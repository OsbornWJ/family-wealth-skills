#!/usr/bin/env python3
"""
A股持仓每日监控脚本
运行时间: 每个交易日 15:45 CST
监控4类数据 + 检查全部触发条件
"""

import json, sys, warnings
from datetime import date, datetime, timedelta
import akshare as ak
import pandas as pd
import requests
import numpy as np
warnings.filterwarnings('ignore')

# ============================================================
# 配置（来自 assets/portfolio.local.json 或 portfolio.example.json）
# ============================================================
from portfolio_config import load_portfolio
_PF = load_portfolio()
ETF_CODES = list(_PF["sina_map"].keys())
ETF_NAMES = _PF["etf_names"]
ETF_TYPE = _PF["etf_type"]
COST_NAV = _PF["cost_price"]
STOCK_COST = _PF["stock_cost"]
PEAK_NAV = _PF["peak_price"]
STOCK_SINA = _PF["stock_sina"]
STOCK_META = _PF["stock_meta"]
SETTINGS = _PF["settings"]
IS_EXAMPLE = _PF["is_example"]
HARD_SELL = bool(SETTINGS.get("enable_hard_sell_alerts", True))
print(f"[portfolio] loaded {_PF['path']} (example={IS_EXAMPLE})", flush=True)

SINA_HEADERS = {'Referer': 'https://finance.sina.com.cn'}

try:
    from quote_providers import get_realtime
except ImportError:
    get_realtime = None


def _index_amount_yi(quote: dict) -> float:
    """成交额 → 亿元。优先 amount(元) / 成交额_万。"""
    if not quote or quote.get("error"):
        return 0.0
    amount = quote.get("amount")
    if amount and float(amount) > 0:
        return float(amount) / 1e8
    wan = quote.get("成交额_万")
    if wan and float(wan) > 0:
        return float(wan) / 1e4
    return 0.0


# ============================================================
# 1. 大盘环境
# ============================================================
def pull_market():
    """拉取上证指数、科创50、两市成交额（优先实时行情字段，避免 volume×均价误报）"""
    result = {}
    amount_source = "none"

    # 实时：沪深指数成交额（元）≈ 两市成交额
    if get_realtime is not None:
        try:
            rt = get_realtime(["sh000001", "sz399001", "sh000688"])
            sh_q = rt.get("sh000001") or {}
            sz_q = rt.get("sz399001") or {}
            kc_q = rt.get("sh000688") or {}
            if sh_q.get("现价") and not sh_q.get("error"):
                result["上证指数"] = {
                    "收盘": round(float(sh_q["现价"]), 2),
                    "涨跌幅": round(float(sh_q.get("涨跌幅") or 0), 2),
                    "成交额_亿": round(_index_amount_yi(sh_q), 1),
                }
            if sz_q.get("现价") and not sz_q.get("error"):
                result["深证成指"] = {
                    "收盘": round(float(sz_q["现价"]), 2),
                    "涨跌幅": round(float(sz_q.get("涨跌幅") or 0), 2),
                    "成交额_亿": round(_index_amount_yi(sz_q), 1),
                }
            if kc_q.get("现价") and not kc_q.get("error"):
                result["科创50"] = {
                    "收盘": round(float(kc_q["现价"]), 2),
                    "涨跌幅": round(float(kc_q.get("涨跌幅") or 0), 2),
                }
            sh_amt = result.get("上证指数", {}).get("成交额_亿", 0)
            sz_amt = result.get("深证成指", {}).get("成交额_亿", 0)
            if sh_amt + sz_amt > 100:  # 正常交易日两市合计远大于百亿
                amount_source = "realtime"
        except Exception as e:
            result["_rt_error"] = str(e)[:80]

    # 回退：日线收盘价；成交额仍尽量不用 volume×均价
    if "上证指数" not in result or "error" in result.get("上证指数", {}):
        try:
            df_sh = ak.stock_zh_index_daily(symbol="sh000001")
            sh = df_sh.iloc[-1]
            sh_prev = df_sh.iloc[-2]
            result["上证指数"] = {
                "收盘": round(float(sh["close"]), 2),
                "涨跌幅": round((float(sh["close"]) / float(sh_prev["close"]) - 1) * 100, 2),
            }
        except Exception as e:
            result["上证指数"] = {"error": str(e)[:100]}

    if "科创50" not in result:
        try:
            df_kc = ak.stock_zh_index_daily(symbol="sh000688")
            kc = df_kc.iloc[-1]
            kc_prev = df_kc.iloc[-2]
            result["科创50"] = {
                "收盘": round(float(kc["close"]), 2),
                "涨跌幅": round((float(kc["close"]) / float(kc_prev["close"]) - 1) * 100, 2),
            }
        except Exception as e:
            result["科创50"] = {"error": str(e)[:100]}

    if "深证成指" not in result:
        try:
            df_sz = ak.stock_zh_index_daily(symbol="sz399001")
            sz = df_sz.iloc[-1]
            result["深证成指"] = {
                "收盘": round(float(sz["close"]), 2),
                "涨跌幅": round((float(sz["close"]) / float(df_sz.iloc[-2]["close"]) - 1) * 100, 2),
            }
        except Exception:
            pass

    sh_amt = float(result.get("上证指数", {}).get("成交额_亿") or 0)
    sz_amt = float(result.get("深证成指", {}).get("成交额_亿") or 0)
    # 兼容旧字段名
    if sh_amt and "估算成交额_亿" not in result.get("上证指数", {}):
        result["上证指数"]["估算成交额_亿"] = sh_amt
    if sz_amt and "估算成交额_亿" not in result.get("深证成指", {}):
        result["深证成指"]["估算成交额_亿"] = sz_amt

    total_yi = sh_amt + sz_amt
    total_wan = round(total_yi / 10000, 2) if total_yi else 0
    result["成交额来源"] = amount_source
    result["全市场估算成交额_万亿"] = total_wan
    if amount_source != "realtime" or total_yi <= 0:
        result["成交额达标"] = "⚪ 成交额暂不可靠（未用实时字段）"
    elif total_yi >= 28000:
        result["成交额达标"] = "✅ ≥2.8万亿"
    elif total_yi >= 15000:
        result["成交额达标"] = "🟡 1.5-2.8万亿"
    else:
        result["成交额达标"] = f"🔴 仅{total_wan:.2f}万亿"

    return result


# ============================================================
# 2. ETF 净值 + MA偏离
# ============================================================
def pull_etf_data():
    """拉取所有ETF的净值历史和当日市价"""
    results = {}
    today_str = str(date.today())

    for code in ETF_CODES:
        try:
            # NAV 历史
            df_nav = ak.fund_open_fund_info_em(symbol=code, indicator='单位净值走势')
            df_nav['净值日期'] = pd.to_datetime(df_nav['净值日期'])
            df_nav = df_nav.sort_values('净值日期')

            nav_series = df_nav['单位净值'].astype(float)
            latest = df_nav.iloc[-1]
            latest_date = str(latest['净值日期'])[:10]

            # MA 计算
            nav_5 = nav_series.tail(5).mean()
            nav_20 = nav_series.tail(20).mean()
            nav_60 = nav_series.tail(60).mean() if len(nav_series) >= 60 else None
            nav_120 = nav_series.tail(120).mean() if len(nav_series) >= 120 else None
            nav_peak_60d = nav_series.tail(60).max()

            current_nav = float(latest['单位净值'])
            daily_change = float(latest['日增长率'])

            results[code] = {
                '名称': ETF_NAMES[code],
                '类型': ETF_TYPE[code],
                '数据日期': latest_date,
                '单位净值': current_nav,
                '日涨跌幅': daily_change,
                'MA5': round(nav_5, 4),
                'MA20': round(nav_20, 4),
                'MA60': round(nav_60, 4) if nav_60 else None,
                'MA120': round(nav_120, 4) if nav_120 else None,
                '偏离MA5_pct': round((current_nav / nav_5 - 1) * 100, 2),
                '偏离MA20_pct': round((current_nav / nav_20 - 1) * 100, 2),
                '偏离MA60_pct': round((current_nav / nav_60 - 1) * 100, 2) if nav_60 else None,
                '偏离MA120_pct': round((current_nav / nav_120 - 1) * 100, 2) if nav_120 else None,
                '60日峰值': round(nav_peak_60d, 4),
                '距峰值回撤_pct': round((1 - current_nav / nav_peak_60d) * 100, 2),
                '成本净值': COST_NAV.get(code),
                '成本盈亏_pct': round((current_nav / COST_NAV[code] - 1) * 100, 2) if code in COST_NAV else None,
            }
        except Exception as e:
            results[code] = {'名称': ETF_NAMES[code], 'error': str(e)[:100]}

    return results


# ============================================================
# 3. ETF 资金流向
# ============================================================
def pull_fund_flow():
    """拉取ETF资金流数据"""
    results = {}
    try:
        df = ak.fund_etf_fund_daily_em()
        today_str = str(date.today())
        yesterday_str = str(date.today() - timedelta(days=1))

        for code in ETF_CODES:
            row = df[df['基金代码'] == code]
            if row.empty:
                results[code] = {'error': '未找到'}
                continue

            r = row.iloc[0]
            # 提取今日和昨日净值
            nav_today_key = f'{today_str}-单位净值'
            nav_yday_key = f'{yesterday_str}-单位净值'

            results[code] = {
                '今日市价': float(r.get('市价', 0)),
                '今日NAV': float(r.get(nav_today_key, r.get(f'{yesterday_str}-单位净值', 0))),
                '昨日NAV': float(r.get(nav_yday_key, 0)),
                '折溢价率': str(r.get('折价率', 'N/A')),
            }
    except Exception as e:
        results['_error'] = str(e)[:100]

    return results


# ============================================================
# 4. 个股（组合配置）
# ============================================================
def pull_stocks():
    """拉取组合内个股实时行情，返回 {code: {...}}"""
    out = {}
    if not STOCK_SINA:
        return out
    codes = list(STOCK_SINA.values())
    batch = {}
    if get_realtime is not None:
        try:
            batch = get_realtime(codes)
        except Exception:
            batch = {}
    for code, sina in STOCK_SINA.items():
        meta = STOCK_META.get(code) or {}
        q = batch.get(sina) or batch.get(code) or {}
        if (not q or q.get("error") or not q.get("现价")) and get_realtime is not None:
            try:
                q = get_realtime([sina]).get(sina) or {}
            except Exception as e:
                out[code] = {"error": str(e)[:100]}
                continue
        if not q or q.get("error") or not q.get("现价"):
            # 最后回退新浪直连
            try:
                r = requests.get(
                    f"https://hq.sinajs.cn/list={sina}",
                    headers=SINA_HEADERS,
                    timeout=10,
                )
                r.encoding = "gbk"
                fields = r.text.split('"')[1].split(",")
                price = float(fields[3])
                prev = float(fields[2])
                q = {
                    "名称": fields[0],
                    "现价": price,
                    "昨收": prev,
                    "涨跌幅": round((price / prev - 1) * 100, 2) if prev else 0,
                    "最高": float(fields[4]),
                    "最低": float(fields[5]),
                    "成交量_手": int(float(fields[8])) if fields[8] else 0,
                }
            except Exception as e:
                out[code] = {"error": str(e)[:100]}
                continue
        price = float(q.get("现价") or 0)
        cost = STOCK_COST.get(code)
        out[code] = {
            "名称": meta.get("name") or q.get("名称") or code,
            "最新价": price,
            "昨收": float(q.get("昨收") or 0),
            "涨跌幅": float(q.get("涨跌幅") or 0),
            "最高": float(q.get("最高") or 0),
            "最低": float(q.get("最低") or 0),
            "成交量_手": int(q.get("成交量_手") or 0),
            "成本价": cost,
            "成本盈亏_pct": round((price / cost - 1) * 100, 2) if cost and cost > 0 else None,
        }
    return out


# 兼容旧调用：单票结构
def pull_stock_601939():
    stocks = pull_stocks()
    if not stocks:
        return {"error": "no stocks in portfolio"}
    code = next(iter(stocks))
    d = dict(stocks[code])
    d["_code"] = code
    return d

# ============================================================
# 5. 外部变量
# ============================================================
def pull_external():
    """美债收益率 + 简要外部信息"""
    result = {}
    try:
        df = ak.bond_zh_us_rate()
        latest = df.iloc[-1]
        result['美10年期国债'] = float(latest['美国国债收益率10年'])
        result['中10年期国债'] = float(latest['中国国债收益率10年'])
        result['中美利差_bp'] = round((result['中10年期国债'] - result['美10年期国债']) * 100, 1)
        result['数据日期'] = str(latest['日期'])[:10]
    except Exception as e:
        result['error'] = str(e)[:100]

    return result


# ============================================================
# 6. 触发条件检查
# ============================================================
def check_triggers(etf_data, stock_data, market_data, flow_data, external):
    """逐条检查所有规则"""
    triggers = []
    alerts = []
    alert_pct = float(SETTINGS.get("drawdown_alert_pct", 15))
    watch_pct = float(SETTINGS.get("drawdown_watch_pct", 8))
    dry_t = float(SETTINGS.get("volume_dry_trillion", 1.0))
    cold_t = float(SETTINGS.get("volume_cold_trillion", 1.5))

    def _sell_alert(item):
        """示例包默认只记信息，不抛硬卖出警报。"""
        if HARD_SELL:
            alerts.append(item)
        else:
            soft = dict(item)
            soft["level"] = "📊 信息"
            soft["动作"] = f"（示例模式未启用硬减仓）{item.get('动作', '')}"
            triggers.append(soft)

    # --- 进攻型：移动止盈 ---
    for code in [c for c in ETF_CODES if ETF_TYPE.get(c) == "进攻" or c in PEAK_NAV]:
        d = etf_data.get(code, {})
        if "error" in d:
            continue
        peak = PEAK_NAV.get(code, d.get("60日峰值", d.get("单位净值", 0)))
        current = d.get("单位净值", 0)
        drawdown = (1 - current / peak) * 100 if peak > 0 else 0

        if drawdown >= alert_pct:
            _sell_alert({
                "level": "🔴 红色",
                "标的": f"{ETF_NAMES.get(code, code)}({code})",
                "触发": f"移动止盈：从峰值{peak}回撤{drawdown:.1f}% ≥ {alert_pct}%",
                "动作": "减仓 1/2",
            })
        elif drawdown >= watch_pct:
            triggers.append({
                "level": "📊 信息",
                "标的": f"{ETF_NAMES.get(code, code)}({code})",
                "触发": f"回撤{drawdown:.1f}%，接近观察线{watch_pct}%",
                "动作": "继续监控，暂不操作",
            })

    # --- 防御型：持仓中 type=防御 的 ETF，仅做 MA120 观察 ---
    for code in [c for c in ETF_CODES if ETF_TYPE.get(c) == "防御"]:
        d = etf_data.get(code, {})
        if "error" in d:
            continue
        ma120_dev = d.get("偏离MA120_pct")
        if ma120_dev is not None and ma120_dev < -3:
            alerts.append({
                "level": "🟡 黄色",
                "标的": f"{ETF_NAMES.get(code, code)}({code})",
                "触发": f"偏离MA120 {ma120_dev:.1f}%, 跌破幅度超3%",
                "动作": "进入观察列表",
            })

    # --- 个股股息率（阈值来自 portfolio，不再写死建行）---
    # stock_data 可能是单票 dict（兼容旧结构）或 {code: {...}}
    stock_map = stock_data if isinstance(stock_data, dict) and any(
        k in STOCK_META for k in stock_data
    ) else {"_single": stock_data} if stock_data else {}

    if "_single" in stock_map and STOCK_META:
        # 旧 pull_stock 只返回一只；按第一只配置映射
        code0 = next(iter(STOCK_META))
        stock_map = {code0: stock_map["_single"]}

    for code, meta in STOCK_META.items():
        d = stock_map.get(code) or {}
        if not d or d.get("error"):
            continue
        if not meta.get("alert_on_low_yield"):
            continue
        annual = meta.get("annual_div")
        if annual is None:
            continue
        price = float(d.get("最新价") or d.get("现价") or 0)
        if price <= 0:
            continue
        min_y = float(meta.get("min_yield_pct") or 4.0)
        y = round(annual / price * 100, 2)
        if y < min_y:
            name = meta.get("name") or STOCK_COST and code
            _sell_alert({
                "level": "🔴 红色",
                "标的": f"{meta.get('name', code)}({code})",
                "触发": f"估算股息率{y}% < {min_y}%（年化分红假设{annual}元）",
                "动作": "触发减持条件，建议评估",
            })

    # --- 观察型：净值回到成本上方 ---
    for code in [c for c in ETF_CODES if ETF_TYPE.get(c) == "观察"]:
        d = etf_data.get(code, {})
        if "error" in d:
            continue
        cost = COST_NAV.get(code, 0)
        current = d.get("单位净值", 0)
        if current > cost and cost > 0:
            triggers.append({
                "level": "📊 信息",
                "标的": f"{ETF_NAMES.get(code, code)}({code})",
                "触发": f"净值{current} > 成本净值{cost}，触发重新评估",
                "动作": "请重新评估该观察仓位",
            })

    # --- 成交额预警（仅实时可靠来源才告警）---
    if market_data.get("成交额来源") == "realtime":
        total_vol = float(market_data.get("全市场估算成交额_万亿") or 0)
        if total_vol > 0 and total_vol < dry_t:
            alerts.append({
                "level": "🔴 红色",
                "标的": "大盘",
                "触发": f"两市成交额约{total_vol}万亿，极度缩量",
                "动作": "注意流动性风险，不宜追高",
            })
        elif total_vol > 0 and total_vol < cold_t:
            alerts.append({
                "level": "🟡 黄色",
                "标的": "大盘",
                "触发": f"两市成交额约{total_vol}万亿，偏冷淡",
                "动作": "控制仓位，等待放量",
            })

    return alerts, triggers


# ============================================================
# 7. 格式化报告
# ============================================================
def format_report(market, etf_data, flow_data, stock_data, external, alerts, triggers):
    today_str = str(date.today())
    lines = []
    lines.append(f"📊 A股持仓监控日报 | {today_str} 15:45 CST")
    lines.append("=" * 55)

    # 一、大盘环境
    lines.append("\n一、大盘环境")
    sh = market.get('上证指数', {})
    kc = market.get('科创50', {})
    sz = market.get('深证成指', {})
    if 'error' not in sh:
        amt = sh.get('成交额_亿', sh.get('估算成交额_亿', 0)) or 0
        lines.append(f"  上证: {sh['收盘']} ({sh['涨跌幅']:+.2f}%) | 成交 {amt:.0f}亿")
    if 'error' not in kc:
        lines.append(f"  科创50: {kc['收盘']} ({kc['涨跌幅']:+.2f}%)")
    if 'error' not in sz:
        amt = sz.get('成交额_亿', sz.get('估算成交额_亿', 0)) or 0
        lines.append(f"  深证: {sz['收盘']} ({sz['涨跌幅']:+.2f}%) | 成交 {amt:.0f}亿")
    src = market.get("成交额来源", "unknown")
    lines.append(
        f"  两市成交额: {market.get('全市场估算成交额_万亿', 'N/A')}万亿 "
        f"{market.get('成交额达标', '')} [来源:{src}]"
    )

    # 二、持仓快照
    lines.append("\n二、持仓快照")
    lines.append(f"  {'标的':<16} {'净值':>7} {'日涨跌':>7} {'偏离5MA':>8} {'偏离20MA':>8} {'偏离120MA':>8} {'回撤峰值':>8} {'成本盈亏':>8} {'信号':>4}")
    lines.append("  " + "-" * 83)

    for code in list(ETF_CODES):
        d = etf_data.get(code, {})
        if 'error' in d:
            lines.append(f"  {ETF_NAMES[code]:<16} ⚠️ 数据获取失败")
            continue
        # 信号判断
        signals = []
        if d.get('偏离MA5_pct', 0) > 5:
            signals.append('超5MA')
        if d.get('偏离MA5_pct', 0) < -3:
            signals.append('破5MA')
        if d.get('偏离MA20_pct', 0) < 0:
            signals.append('破20MA')
        if d.get('距峰值回撤_pct', 0) > 10:
            signals.append('⚠️深回撤')
        sig_str = ','.join(signals) if signals else '✅'

        cost_pnl = f"{d.get('成本盈亏_pct', 0):+.1f}%" if d.get('成本盈亏_pct') is not None else 'N/A'

        if not d.get('名称') and not d.get('单位净值'):
            lines.append(f"  {ETF_NAMES.get(code, code):<16} ⚠️ 数据不完整")
            continue
        lines.append(
            f"  {d.get('名称', ETF_NAMES.get(code, code)):<16} {d.get('单位净值', 0):>7.4f} {d.get('日涨跌幅', 0):>+6.2f}% "
            f"{d.get('偏离MA5_pct', 0):>+7.2f}% {d.get('偏离MA20_pct', 0):>+7.2f}% "
            f"{d.get('偏离MA120_pct', 0):>+7.2f}% "
            f"{d.get('距峰值回撤_pct', 0):>+7.1f}% {cost_pnl:>8} {sig_str:<10}"
        )

    # 个股
    stock_rows = (
        stock_data
        if isinstance(stock_data, dict) and any(k in STOCK_META for k in stock_data)
        else None
    )
    if stock_rows is None and isinstance(stock_data, dict) and "error" not in stock_data and stock_data.get("最新价"):
        stock_rows = {stock_data.get("_code") or next(iter(STOCK_META), "?"): stock_data}
    if stock_rows:
        for code, s in stock_rows.items():
            if not s or s.get("error"):
                continue
            pnl = s.get("成本盈亏_pct")
            pnl_s = f"{pnl:+.1f}%" if pnl is not None else "N/A"
            lines.append(
                f"  {s.get('名称', code):<16} {s.get('最新价', 0):>7.2f} {s.get('涨跌幅', 0):>+6.2f}% "
                f"{'--':>8} {'--':>8} {'--':>8} "
                f"{pnl_s:>8} {'🏦':>4}"
            )

    # 三、资金信号
    lines.append("\n三、主力资金信号")
    if flow_data and '_error' not in flow_data:
        for code in ETF_CODES:
            f = flow_data.get(code, {})
            if 'error' in f:
                continue
            lines.append(
                f"  {ETF_NAMES[code]:<16} 市价:{f.get('今日市价', 0):.4f}  "
                f"NAV:{f.get('今日NAV', 0):.4f}  折溢价:{f.get('折溢价率', 'N/A')}"
            )
    else:
        lines.append("  ⚠️ 资金流数据暂不可用")

    # 四、触发警报
    lines.append("\n四、触发条件检查")
    if alerts:
        lines.append("  ╔═══ 警报 ═══╗")
        for a in alerts:
            lines.append(f"  {a['level']} {a['标的']}")
            lines.append(f"     触发: {a['触发']}")
            lines.append(f"     动作: {a['动作']}")
    if triggers:
        for t in triggers:
            lines.append(f"  {t['level']} {t['标的']}: {t['触发']} → {t['动作']}")
    if not alerts and not triggers:
        lines.append("  🟢 今日无触发，所有规则正常")

    # 五、外部变量
    lines.append("\n五、外部变量")
    if 'error' not in external:
        lines.append(f"  美10年期国债: {external['美10年期国债']:.2f}%")
        lines.append(f"  中10年期国债: {external['中10年期国债']:.2f}%")
        lines.append(f"  中美利差: {external['中美利差_bp']:.1f}bp")
        lines.append(f"  数据日期: {external.get('数据日期', 'N/A')}")
    else:
        lines.append(f"  ⚠️ {external.get('error', '数据不可用')}")

    # 六、需要决策
    if alerts:
        lines.append("\n六、⚠️ 需要主人决策")
        for a in alerts:
            lines.append(f"  → {a['标的']}: {a['动作']}")

    lines.append("\n" + "=" * 55)
    lines.append("以上数据来自 AKShare + 新浪财经，仅供决策参考。")
    return "\n".join(lines)


# ============================================================
# 主函数
# ============================================================
def is_trading_day():
    """检查今天是否为A股交易日"""
    try:
        import akshare as ak
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
        return ""  # 空输出 = 静默，不会推送通知

    print("⏳ 正在拉取数据...", file=sys.stderr)

    market = pull_market()
    print("  ✅ 大盘数据", file=sys.stderr)

    etf_data = pull_etf_data()
    print("  ✅ ETF净值", file=sys.stderr)

    flow_data = pull_fund_flow()
    print("  ✅ 资金流向", file=sys.stderr)

    stock_data = pull_stocks()
    print(f"  ✅ 个股 {list(stock_data.keys()) or '无'}", file=sys.stderr)

    external = pull_external()
    print("  ✅ 外部变量", file=sys.stderr)

    alerts, triggers = check_triggers(etf_data, stock_data, market, flow_data, external)

    report = format_report(market, etf_data, flow_data, stock_data, external, alerts, triggers)
    return report


if __name__ == '__main__':
    report = main()
    print(report)
