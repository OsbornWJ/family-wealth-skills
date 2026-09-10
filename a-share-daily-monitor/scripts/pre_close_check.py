#!/usr/bin/env python3
"""
A股持仓尾盘预警脚本
运行时间: 每个交易日 14:35 CST
仅检查实时价格 + 盘中触发条件，轻量快速
"""

import json, sys, warnings
from datetime import date, datetime
import requests
import akshare as ak
warnings.filterwarnings('ignore')

# ============================================================
# 配置（来自 assets/portfolio.local.json 或 portfolio.example.json）
# ============================================================
from portfolio_config import load_portfolio
_PF = load_portfolio()
ETF_SINA_MAP = _PF["sina_map"]
ETF_NAMES = _PF["etf_names"]
ETF_TYPE = _PF["etf_type"]
PEAK_PRICE = _PF["peak_price"]
COST_PRICE = _PF["cost_price"]
STOCK_SINA = _PF["stock_sina"]
STOCK_META = _PF["stock_meta"]
SETTINGS = _PF["settings"]
HARD_SELL = bool(SETTINGS.get("enable_hard_sell_alerts", True))
print(f"[portfolio] loaded {_PF['path']} (example={_PF['is_example']})", flush=True)

SINA_HEADERS = {'Referer': 'https://finance.sina.com.cn'}


try:
    from quote_providers import get_realtime
except ImportError:
    get_realtime = None


def fetch_sina_quote(sina_code):
    """实时行情：腾讯 → 新浪 → mootdx"""
    if get_realtime is not None:
        batch = get_realtime([sina_code])
        q = batch.get(sina_code) or next(iter(batch.values()), None)
        if q and not q.get('error') and q.get('现价') is not None:
            return q
    try:
        url = f'https://hq.sinajs.cn/list={sina_code}'
        r = requests.get(url, headers=SINA_HEADERS, timeout=10)
        data = r.text.split('"')[1]
        if not data:
            return {'error': 'empty response'}
        fields = data.split(',')
        return {
            '名称': fields[0],
            '今开': float(fields[1]) if fields[1] else 0,
            '昨收': float(fields[2]) if fields[2] else 0,
            '现价': float(fields[3]) if fields[3] else 0,
            '最高': float(fields[4]) if fields[4] else 0,
            '最低': float(fields[5]) if fields[5] else 0,
            '成交量_手': int(fields[8]) if fields[8] else 0,
            'source': 'sina',
        }
    except Exception as e:
        return {'error': str(e)[:80]}


def fetch_index():
    """大盘实时快照 — 多源"""
    result = {}
    indices = {'上证': 's_sh000001', '科创50': 's_sh000688'}
    if get_realtime is not None:
        batch = get_realtime(list(indices.values()))
        for name, code in indices.items():
            q = batch.get(code) or {}
            if q and not q.get('error') and q.get('现价') is not None:
                result[name] = {
                    '现价': round(float(q['现价']), 2),
                    '涨跌幅': round(float(q.get('涨跌幅') or q.get('pct') or 0), 2),
                    'source': q.get('source'),
                }
            else:
                result[name] = {'error': '获取失败'}
        return result
    for name, code in indices.items():
        try:
            url = f'https://hq.sinajs.cn/list={code}'
            r = requests.get(url, headers=SINA_HEADERS, timeout=10)
            data = r.text.split('"')[1]
            if data:
                f = data.split(',')
                result[name] = {
                    '现价': round(float(f[1]), 2),
                    '涨跌幅': round(float(f[3]), 2),
                    'source': 'sina',
                }
        except Exception:
            result[name] = {'error': '获取失败'}
    return result


def fetch_stock():
    """组合内第一只个股实时行情（无个股则返回 None）"""
    if not STOCK_SINA:
        return None
    code = next(iter(STOCK_SINA))
    q = fetch_sina_quote(STOCK_SINA[code])
    if isinstance(q, dict):
        q = dict(q)
        q["_code"] = code
    return q


def check_alerts(etf_quotes, stock_quote, index_data):
    """检查所有盘中触发条件"""
    alerts = []
    alert_pct = float(SETTINGS.get("drawdown_alert_pct", 15))
    watch_pct = float(SETTINGS.get("drawdown_watch_pct", 8))
    # 尾盘：逼近线略低于正式止盈线
    near_pct = max(watch_pct, alert_pct - 3)

    def _maybe_hard(item):
        if HARD_SELL or item.get("level") in ("🟡", "📊", "🟢"):
            alerts.append(item)
        else:
            soft = dict(item)
            soft["level"] = "📊"
            soft["动作"] = f"（示例模式）{item.get('动作', '')}"
            alerts.append(soft)

    # --- 进攻型移动止盈检查 ---
    for code in [c for c in ETF_SINA_MAP if ETF_TYPE.get(c) == "进攻" or c in PEAK_PRICE]:
        q = etf_quotes.get(code) or {}
        if "error" in q:
            continue
        price = q.get("现价", 0)
        peak = PEAK_PRICE.get(code, price)
        if peak > 0 and price > 0:
            drawdown = round((1 - price / peak) * 100, 1)
            if drawdown >= near_pct:
                _maybe_hard({
                    "level": "🔴",
                    "标的": f"{ETF_NAMES.get(code, code)}({code})",
                    "内容": f"回撤{drawdown}%，逼近{alert_pct}%止盈线！现价{price}，峰值{peak}",
                    "动作": "如14:55前未回升，收盘前执行减仓1/2",
                })
            elif drawdown >= watch_pct:
                alerts.append({
                    "level": "🟡",
                    "标的": f"{ETF_NAMES.get(code, code)}({code})",
                    "内容": f"回撤{drawdown}%，注意观察",
                    "动作": "继续监控，暂不操作",
                })

    # --- 观察型：现价回到成本上方 ---
    for code in [c for c in ETF_SINA_MAP if ETF_TYPE.get(c) == "观察"]:
        q = etf_quotes.get(code) or {}
        if "error" in q:
            continue
        price = q.get("现价", 0)
        cost = COST_PRICE.get(code, 0)
        if price > cost and cost > 0:
            alerts.append({
                "level": "📊",
                "标的": f"{ETF_NAMES.get(code, code)}({code})",
                "内容": f"现价{price} > 成本{cost}，触发重新评估",
                "动作": "收盘后请重新评估该观察仓位",
            })

    # --- 个股股息率 ---
    if stock_quote and not stock_quote.get("error"):
        code = stock_quote.get("_code") or (next(iter(STOCK_META), None) if STOCK_META else None)
        meta = STOCK_META.get(code or "", {})
        if meta.get("alert_on_low_yield") and meta.get("annual_div") is not None:
            price = float(stock_quote.get("现价") or 0)
            annual = float(meta["annual_div"])
            min_y = float(meta.get("min_yield_pct") or 4.0)
            if price > 0:
                y = round(annual / price * 100, 2)
                if y < min_y:
                    _maybe_hard({
                        "level": "🟡",
                        "标的": f"{meta.get('name', code)}({code})",
                        "内容": f"估算股息率{y}% < {min_y}%",
                        "动作": "触发减持条件",
                    })

    # --- 单日大跌预警 ---
    for code, q in etf_quotes.items():
        if not q or "error" in q:
            continue
        change = (
            round((q.get("现价", 0) / q.get("昨收", 1) - 1) * 100, 2)
            if q.get("昨收", 0) > 0
            else 0
        )
        if change <= -5:
            alerts.append({
                "level": "🔴",
                "标的": f"{ETF_NAMES.get(code, code)}({code})",
                "内容": f"单日暴跌{change}%",
                "动作": "检查是否有突发利空，考虑尾盘减仓",
            })

    return alerts

def format_report(index_data, etf_quotes, stock_quote, alerts):
    now_str = datetime.now().strftime('%H:%M')
    today_str = str(date.today())
    lines = []
    lines.append(f"⚡ A股尾盘预警 | {today_str} {now_str} CST")
    lines.append("=" * 45)

    # 大盘
    lines.append("\n【大盘实时】")
    for name in ['上证', '科创50']:
        d = index_data.get(name, {})
        if 'error' not in d:
            lines.append(f"  {name}: {d['现价']} ({d['涨跌幅']:+.2f}%)")
        else:
            lines.append(f"  {name}: --")

    # 持仓速览
    lines.append("\n【持仓盘中】")
    lines.append(f"  {'标的':<16} {'现价':>7} {'涨跌':>7} {'距峰值':>8} {'状态':>6}")
    lines.append("  " + "-" * 50)

    for code in list(ETF_SINA_MAP.keys()):
        q = etf_quotes.get(code) or {}
        if 'error' in q:
            lines.append(f"  {ETF_NAMES.get(code, code):<16} ⚠️ 获取失败")
            continue
        price = q.get('现价', 0)
        prev = q.get('昨收', 0)
        change = round((price / prev - 1) * 100, 2) if prev > 0 else 0
        peak = PEAK_PRICE.get(code)
        if peak:
            from_peak = round((1 - price / peak) * 100, 1)
            peak_str = f"-{from_peak}%"
        else:
            peak_str = "--"

        # 状态
        if change >= 2:
            status = '🔥强势'
        elif change <= -3:
            status = '❄️走弱'
        else:
            status = '➡️平稳'

        lines.append(f"  {ETF_NAMES.get(code, code):<16} {price:>7.4f} {change:>+6.2f}% {peak_str:>8} {status:>6}")

    # 个股
    if stock_quote and "error" not in stock_quote:
        s = stock_quote
        code = s.get("_code") or (next(iter(STOCK_META), None) if STOCK_META else None)
        name = (STOCK_META.get(code) or {}).get("name", code or "个股") if code else "个股"
        change = round((s["现价"] / s["昨收"] - 1) * 100, 2) if s.get("昨收", 0) > 0 else 0
        lines.append(f"  {name:<16} {s['现价']:>7.2f} {change:>+6.2f}% {'--':>8} {'🏦':>6}")

    # 警报
    lines.append(f"\n【触发警报】({len(alerts)}条)")
    if alerts:
        for a in alerts:
            lines.append(f"  {a['level']} {a['标的']}")
            lines.append(f"     {a['内容']}")
            lines.append(f"     → {a['动作']}")
    else:
        lines.append("  🟢 无触发，一切正常")

    lines.append("\n" + "=" * 45)
    lines.append("盘中快照 · 15:45将发送完整日报")
    return "\n".join(lines)


def is_trading_day():
    """检查今天是否为A股交易日"""
    try:
        today = date.today().strftime('%Y-%m-%d')
        df = ak.tool_trade_date_hist_sina()
        trade_dates = set(df['trade_date'].astype(str).values)
        return today in trade_dates
    except:
        wd = date.today().weekday()
        return wd < 5


def main():
    if not is_trading_day():
        print("休市", file=sys.stderr)
        return ""
    print("⏳ 拉取盘中数据...", file=sys.stderr)

    # 并行李拉取（顺序即可，Sina很快）
    etf_quotes = {}
    for code, sina_code in ETF_SINA_MAP.items():
        etf_quotes[code] = fetch_sina_quote(sina_code)

    index_data = fetch_index()
    stock_quote = fetch_stock()
    alerts = check_alerts(etf_quotes, stock_quote, index_data)

    print("✅ 完成", file=sys.stderr)
    return format_report(index_data, etf_quotes, stock_quote, alerts)


if __name__ == '__main__':
    report = main()
    print(report)
