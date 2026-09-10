#!/usr/bin/env python3
"""
Free, no-API-key quote providers for A-shares / ETFs / indices.

Priority (realtime): Tencent qt.gtimg.cn → Sina hq.sinajs.cn → optional mootdx
Priority (daily bars): baostock → optional mootdx → Sina K-line → AKShare last

No tushare / iwencai keys. Soft-deps fail closed (skip).
"""
from __future__ import annotations

import re
import time
from typing import Dict, Iterable, List, Optional

import requests

TENCENT_URL = "http://qt.gtimg.cn/q={codes}"
SINA_URL = "https://hq.sinajs.cn/list={codes}"
SINA_KLINE = (
    "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "CN_MarketData.getKLineData"
)
SINA_HEADERS = {"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}
TENCENT_HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.qq.com"}


def normalize_code(code: str) -> str:
    """Return prefixed code like sh601939 / sz159992."""
    c = code.strip().lower()
    if c.startswith(("sh", "sz", "bj")):
        return c
    if c.startswith(("s_sh", "s_sz")):  # sina index shorthand
        return c
    digits = re.sub(r"\D", "", c)
    if not digits:
        return c
    if digits.startswith(("5", "6", "9")) or digits.startswith("11"):
        return "sh" + digits
    if digits.startswith(("0", "1", "2", "3")):
        return "sz" + digits
    return "sh" + digits


def _tencent_symbol(code: str) -> str:
    c = normalize_code(code)
    if c.startswith("s_"):
        # index: s_sh000001 → sh000001 for tencent
        return c[2:]
    return c


def _empty(error: str) -> dict:
    return {"error": error, "source": None}


def fetch_tencent_batch(codes: Iterable[str]) -> Dict[str, dict]:
    """
    Tencent quote. Field layout (GBK):
    v_sh601939="1~建设银行~601939~price~prev~open~volume~...~date~time~..."
    index 3=price, 4=prev_close, 5=open, 33=high, 34=low (common layout);
    we also parse pct from field 31/32 when present.
    """
    pref = [_tencent_symbol(c) for c in codes]
    key_map = { _tencent_symbol(c): normalize_code(c) for c in codes }
    url = TENCENT_URL.format(codes=",".join(pref))
    out: Dict[str, dict] = {}
    try:
        r = requests.get(url, headers=TENCENT_HEADERS, timeout=10)
        r.encoding = "gbk"
        text = r.text
    except Exception as e:
        return {normalize_code(c): _empty(f"tencent:{e}") for c in codes}

    for chunk in text.strip().split(";"):
        chunk = chunk.strip()
        if not chunk or "=\"" not in chunk:
            continue
        # v_sh601939="..."
        m = re.match(r'v_([^=]+)="(.*)"', chunk)
        if not m:
            continue
        sym, payload = m.group(1), m.group(2)
        if not payload:
            out[key_map.get(sym, sym)] = _empty("tencent:empty")
            continue
        f = payload.split("~")
        try:
            price = float(f[3]) if f[3] else 0.0
            prev = float(f[4]) if f[4] else 0.0
            open_ = float(f[5]) if f[5] else 0.0
            # high/low commonly at 33/34 for stocks; for some ETF shorter — probe
            high = float(f[33]) if len(f) > 33 and f[33] else 0.0
            low = float(f[34]) if len(f) > 34 and f[34] else 0.0
            pct = float(f[32]) if len(f) > 32 and f[32] else (
                ((price / prev) - 1) * 100 if prev else 0.0
            )
            vol = float(f[6]) if len(f) > 6 and f[6] else 0.0
            # 腾讯成交额单位为「万元」
            amount_wan = float(f[37]) if len(f) > 37 and f[37] else 0.0
            amount = amount_wan * 10000.0  # 统一为元
            name = f[1] if len(f) > 1 else sym
            canon = key_map.get(sym, normalize_code(sym))
            out[canon] = {
                "名称": name,
                "今开": open_,
                "昨收": prev,
                "现价": price,
                "最高": high,
                "最低": low,
                "涨跌幅": pct,
                "成交量_手": vol,
                "成交额_万": amount_wan,
                "source": "tencent",
                "price": price,
                "open": open_,
                "prev_close": prev,
                "high": high,
                "low": low,
                "pct": pct,
                "volume": vol,
                "amount": amount,
            }
        except Exception as e:
            out[key_map.get(sym, sym)] = _empty(f"tencent:parse:{e}")
    for c in codes:
        nc = normalize_code(c)
        if nc not in out and _tencent_symbol(c) not in out:
            # try both keys
            if nc not in out:
                out[nc] = _empty("tencent:missing")
    return out


def fetch_sina_batch(codes: Iterable[str]) -> Dict[str, dict]:
    pref = []
    for c in codes:
        nc = normalize_code(c)
        # allow s_sh000001 style for index brief
        if c.strip().lower().startswith("s_"):
            pref.append(c.strip().lower())
        else:
            pref.append(nc)
    url = SINA_URL.format(codes=",".join(pref))
    out: Dict[str, dict] = {}
    try:
        r = requests.get(url, headers=SINA_HEADERS, timeout=10)
        r.encoding = "gbk"
        text = r.text
    except Exception as e:
        return {normalize_code(c): _empty(f"sina:{e}") for c in codes}

    for line in text.splitlines():
        if "=\"" not in line:
            continue
        # hq_str_sh601939="..." or hq_str_s_sh000001="..."
        m = re.search(r'hq_str_([^=]+)="([^"]*)"', line)
        if not m:
            continue
        sym, data = m.group(1), m.group(2)
        if not data:
            out[normalize_code(sym) if not sym.startswith("s_") else sym] = _empty("sina:empty")
            continue
        fields = data.split(",")
        try:
            if sym.startswith("s_"):
                # name, price, change, pct, volume, amount
                name, price, _chg, pct = fields[0], float(fields[1]), fields[2], float(fields[3])
                out[sym] = {
                    "名称": name,
                    "现价": price,
                    "涨跌幅": pct,
                    "昨收": 0.0,
                    "今开": 0.0,
                    "最高": 0.0,
                    "最低": 0.0,
                    "成交量_手": float(fields[4]) if len(fields) > 4 else 0,
                    "成交额_万": float(fields[5]) / 10000 if len(fields) > 5 else 0,
                    "source": "sina",
                    "price": price,
                    "pct": pct,
                    "open": 0.0,
                    "prev_close": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "volume": float(fields[4]) if len(fields) > 4 else 0,
                    "amount": float(fields[5]) if len(fields) > 5 else 0,
                }
            else:
                prev = float(fields[2]) if fields[2] else 0.0
                price = float(fields[3]) if fields[3] else 0.0
                pct = ((price / prev) - 1) * 100 if prev else 0.0
                out[normalize_code(sym)] = {
                    "名称": fields[0],
                    "今开": float(fields[1]) if fields[1] else 0.0,
                    "昨收": prev,
                    "现价": price,
                    "最高": float(fields[4]) if fields[4] else 0.0,
                    "最低": float(fields[5]) if fields[5] else 0.0,
                    "涨跌幅": pct,
                    "成交量_手": int(float(fields[8])) if fields[8] else 0,
                    "成交额_万": float(fields[9]) / 10000 if fields[9] else 0.0,
                    "source": "sina",
                    "price": price,
                    "open": float(fields[1]) if fields[1] else 0.0,
                    "prev_close": prev,
                    "high": float(fields[4]) if fields[4] else 0.0,
                    "low": float(fields[5]) if fields[5] else 0.0,
                    "pct": pct,
                    "volume": float(fields[8]) if fields[8] else 0,
                    "amount": float(fields[9]) if fields[9] else 0,
                }
        except Exception as e:
            out[sym] = _empty(f"sina:parse:{e}")
    time.sleep(0.15)
    return out


def _mootdx_quotes(codes: Iterable[str]) -> Dict[str, dict]:
    try:
        from mootdx.quotes import Quotes  # type: ignore
    except Exception:
        return {}
    out: Dict[str, dict] = {}
    try:
        client = Quotes.factory(market="std")
        for c in codes:
            nc = normalize_code(c)
            digits = re.sub(r"\D", "", nc)
            try:
                df = client.quotes(symbol=digits)
                if df is None or len(df) == 0:
                    continue
                row = df.iloc[0]
                price = float(row.get("price", 0) or 0)
                prev = float(row.get("last_close", 0) or 0)
                out[nc] = {
                    "名称": nc,
                    "现价": price,
                    "昨收": prev,
                    "今开": float(row.get("open", 0) or 0),
                    "最高": float(row.get("high", 0) or 0),
                    "最低": float(row.get("low", 0) or 0),
                    "涨跌幅": ((price / prev) - 1) * 100 if prev else 0.0,
                    "source": "mootdx",
                    "price": price,
                    "prev_close": prev,
                    "open": float(row.get("open", 0) or 0),
                    "high": float(row.get("high", 0) or 0),
                    "low": float(row.get("low", 0) or 0),
                    "pct": ((price / prev) - 1) * 100 if prev else 0.0,
                    "volume": float(row.get("vol", 0) or 0),
                    "amount": float(row.get("amount", 0) or 0),
                    "成交量_手": float(row.get("vol", 0) or 0),
                    "成交额_万": float(row.get("amount", 0) or 0) / 10000,
                }
            except Exception:
                continue
    except Exception:
        return {}
    return out


def get_realtime(codes: Iterable[str]) -> Dict[str, dict]:
    """
    Fetch realtime quotes with failover.
    Returns map keyed by normalize_code (or s_* for index brief codes).
    """
    codes_list = list(codes)
    if not codes_list:
        return {}

    # Split index brief vs normal
    index_brief = [c for c in codes_list if c.strip().lower().startswith("s_")]
    normal = [c for c in codes_list if not c.strip().lower().startswith("s_")]

    result: Dict[str, dict] = {}

    if normal:
        t_map = fetch_tencent_batch(normal)
        need_sina = []
        for c in normal:
            nc = normalize_code(c)
            q = t_map.get(nc) or t_map.get(_tencent_symbol(c))
            if q and not q.get("error") and q.get("现价"):
                result[nc] = q
            else:
                need_sina.append(c)
        if need_sina:
            s_map = fetch_sina_batch(need_sina)
            still = []
            for c in need_sina:
                nc = normalize_code(c)
                q = s_map.get(nc)
                if q and not q.get("error") and q.get("现价"):
                    result[nc] = q
                else:
                    still.append(c)
            if still:
                m_map = _mootdx_quotes(still)
                for c in still:
                    nc = normalize_code(c)
                    if nc in m_map:
                        result[nc] = m_map[nc]
                    else:
                        result[nc] = _empty("all_sources_failed")

    if index_brief:
        # Tencent uses sh000001; sina uses s_sh000001
        t_codes = [c[2:] if c.startswith("s_") else c for c in index_brief]
        t_map = fetch_tencent_batch(t_codes)
        need = []
        for brief, bare in zip(index_brief, t_codes):
            q = t_map.get(normalize_code(bare))
            if q and not q.get("error") and q.get("现价"):
                result[brief] = q
            else:
                need.append(brief)
        if need:
            s_map = fetch_sina_batch(need)
            for brief in need:
                q = s_map.get(brief)
                if q and not q.get("error"):
                    result[brief] = q
                else:
                    result[brief] = _empty("index_failed")
    return result


def get_realtime_one(code: str) -> dict:
    return get_realtime([code]).get(normalize_code(code), _empty("missing"))


def get_daily_bars(code: str, n: int = 120):
    """Return list of dicts {day, open, high, low, close, volume} or []."""
    nc = normalize_code(code)
    digits = re.sub(r"\D", "", nc)

    # 1) baostock
    try:
        import baostock as bs  # type: ignore
        import pandas as pd  # type: ignore

        lg = bs.login()
        if lg.error_code == "0":
            market = "sh" if nc.startswith("sh") else "sz"
            rs = bs.query_history_k_data_plus(
                f"{market}.{digits}",
                "date,open,high,low,close,volume",
                frequency="d",
                adjustflag="3",
            )
            rows = []
            while rs.error_code == "0" and rs.next():
                rows.append(rs.get_row_data())
            bs.logout()
            if rows:
                rows = rows[-n:]
                return [
                    {
                        "day": r[0],
                        "open": float(r[1]),
                        "high": float(r[2]),
                        "low": float(r[3]),
                        "close": float(r[4]),
                        "volume": float(r[5] or 0),
                        "source": "baostock",
                    }
                    for r in rows
                    if r[4]
                ]
    except Exception:
        pass

    # 2) mootdx
    try:
        from mootdx.quotes import Quotes  # type: ignore

        client = Quotes.factory(market="std")
        df = client.bars(symbol=digits, frequency=9, offset=n)
        if df is not None and len(df) > 0:
            out = []
            for _, row in df.tail(n).iterrows():
                out.append(
                    {
                        "day": str(row.get("datetime", row.get("date", ""))),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row.get("vol", row.get("volume", 0)) or 0),
                        "source": "mootdx",
                    }
                )
            if out:
                return out
    except Exception:
        pass

    # 3) sina kline
    try:
        r = requests.get(
            SINA_KLINE,
            params={"symbol": nc, "scale": 240, "datalen": n},
            headers=SINA_HEADERS,
            timeout=15,
        )
        data = r.json()
        if isinstance(data, list) and data:
            return [
                {
                    "day": item.get("day"),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item.get("volume", 0) or 0),
                    "source": "sina",
                }
                for item in data
            ]
    except Exception:
        pass

    # 4) akshare last
    try:
        import akshare as ak  # type: ignore

        df = ak.stock_zh_a_hist(symbol=digits, period="daily", adjust="qfq")
        if df is not None and len(df) > 0:
            df = df.tail(n)
            # columns: 日期 开盘 收盘 最高 最低 成交量 ...
            out = []
            for _, row in df.iterrows():
                out.append(
                    {
                        "day": str(row.iloc[0]),
                        "open": float(row.iloc[1]),
                        "close": float(row.iloc[2]),
                        "high": float(row.iloc[3]),
                        "low": float(row.iloc[4]),
                        "volume": float(row.iloc[5]) if len(row) > 5 else 0,
                        "source": "akshare",
                    }
                )
            return out
    except Exception:
        pass
    return []


if __name__ == "__main__":
    sample = ["sh000001", "sh601939", "sh512760", "sz159992"]
    # also test index brief
    rt = get_realtime(["s_sh000001", "sh601939", "sh512890"])
    for k, v in rt.items():
        if v.get("error"):
            print(k, "FAIL", v.get("error"))
        else:
            print(k, v.get("source"), v.get("名称"), v.get("现价"), v.get("涨跌幅"))
    bars = get_daily_bars("601939", 5)
    print("bars", len(bars), bars[-1] if bars else None)
