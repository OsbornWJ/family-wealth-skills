#!/usr/bin/env python3
"""
A股早盘分析脚本
运行时间: 每个交易日 10:30 CST
开盘一小时快照：大盘走势、持仓表现、开盘形态、资金信号
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
STOCK_COST = _PF["stock_cost"]
print(f"[portfolio] loaded {_PF['path']}", flush=True)

SINA_HEADERS = {'Referer': 'https://finance.sina.com.cn'}

try:
    from quote_providers import get_realtime
except ImportError:
    get_realtime = None


def fetch_sina_quote(sina_code):
    """实时行情：腾讯 → 新浪 → mootdx（见 quote_providers）"""
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
            '成交额_万': float(fields[9]) / 10000 if fields[9] else 0,
            'source': 'sina',
        }
    except Exception as e:
        return {'error': str(e)[:80]}


def fetch_index():
    """大盘实时快照（上证、科创50、深证成指）— 多源"""
    result = {}
    indices = {'上证': 's_sh000001', '科创50': 's_sh000688', '深证': 's_sz399001'}
    if get_realtime is not None:
        batch = get_realtime(list(indices.values()))
        for name, code in indices.items():
            q = batch.get(code) or {}
            if q and not q.get('error') and q.get('现价') is not None:
                pct = q.get('涨跌幅') or q.get('pct') or 0
                price = q.get('现价')
                prev = q.get('昨收') or 0
                chg = round(price - prev, 2) if prev else round(price * pct / 100, 2) if pct else 0
                result[name] = {
                    '现价': round(float(price), 2),
                    '涨跌额': chg,
                    '涨跌幅': round(float(pct), 2),
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
                    '涨跌额': round(float(f[2]), 2),
                    '涨跌幅': round(float(f[3]), 2),
                    'source': 'sina',
                }
        except Exception:
            result[name] = {'error': '获取失败'}
    return result


def fetch_stock():
    """建设银行实时行情"""
    return fetch_sina_quote('sh601939')

def fetch_north_flow():
    """拉取北向资金当日实时流向（沪股通+深股通）"""
    try:
        df = ak.stock_hsgt_hist_em(symbol='北向资金')
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            # 尝试多个可能的列名
            net_val = None
            for col in ['当日成交净买额', '净买额', '净流入']:
                if col in latest.index:
                    raw = latest[col]
                    try:
                        net_val = float(raw)
                        if str(net_val) != 'nan':
                            break
                    except:
                        continue
            if net_val is not None and str(net_val) != 'nan':
                return {
                    '日期': str(latest['日期'])[:10],
                    '当日净流入_亿': round(net_val / 1e8, 2),
                }
    except:
        pass
    return None


def analyze_opening(quotes):
    """分析开盘形态：高开/低开/平开 + 日内走势方向"""
    analysis = {}
    for code, q in quotes.items():
        if not q or 'error' in q:
            continue
        open_p = q.get('今开', 0)
        prev = q.get('昨收', 0)
        current = q.get('现价', 0)
        high = q.get('最高', 0)
        low = q.get('最低', 0)

        if prev <= 0:
            continue

        gap = round((open_p / prev - 1) * 100, 2)
        intra_day = round((current / open_p - 1) * 100, 2) if open_p > 0 else 0

        # 开盘分类
        if gap >= 1:
            open_type = '🔺高开'
        elif gap <= -1:
            open_type = '🔻低开'
        else:
            open_type = '➖平开'

        # 日内走势
        if intra_day >= 1:
            trend = '📈走强'
        elif intra_day <= -1:
            trend = '📉走弱'
        else:
            trend = '➡️横盘'

        # 振幅
        amplitude = round((high - low) / prev * 100, 2) if prev > 0 and high > 0 and low > 0 else 0

        analysis[code] = {
            '名称': ETF_NAMES.get(code, code),
            '开盘': open_type,
            '开盘gap%': gap,
            '日内方向': trend,
            '日内涨跌%': intra_day,
            '振幅%': amplitude,
            '现价': current,
            '涨跌幅': round((current / prev - 1) * 100, 2),
        }

    return analysis


def check_morning_alerts(etf_quotes, stock_quote, index_data, opening):
    """早盘特定触发条件"""
    alerts = []

    # --- 高开低走预警 ---
    for code, o in opening.items():
        if not o:
            continue
        gap = o.get('开盘gap%', 0)
        intra = o.get('日内涨跌%', 0)
        if gap >= 1.5 and intra <= -1:
            alerts.append({
                'level': '🟡',
                '标的': f'{ETF_NAMES.get(code, code)}({code})',
                '内容': f'高开{gap:+.1f}%后低走{intra:+.1f}%，警惕获利盘出逃',
                '动作': '观察午后能否收复，若持续走弱尾盘考虑减仓',
            })

    # --- 低开高走（正向信号）---
    for code, o in opening.items():
        if not o:
            continue
        gap = o.get('开盘gap%', 0)
        intra = o.get('日内涨跌%', 0)
        if gap <= -1.5 and intra >= 1:
            alerts.append({
                'level': '🟢',
                '标的': f'{ETF_NAMES.get(code, code)}({code})',
                '内容': f'低开{gap:+.1f}%后走高{intra:+.1f}%，抄底资金进场',
                '动作': '正向信号，继续持有观察',
            })

    # --- 单日涨跌幅过大 ---
    for code, q in etf_quotes.items():
        if not q or 'error' in q:
            continue
        prev = q.get('昨收', 0)
        current = q.get('现价', 0)
        change = round((current / prev - 1) * 100, 2) if prev > 0 else 0
        if change >= 5:
            alerts.append({
                'level': '🟢',
                '标的': f'{ETF_NAMES.get(code, code)}({code})',
                '内容': f'+{change}%，早盘强势拉升',
                '动作': '关注是否放量，午后可能继续冲高',
            })
        elif change <= -4:
            alerts.append({
                'level': '🔴',
                '标的': f'{ETF_NAMES.get(code, code)}({code})',
                '内容': f'{change}%，早盘急跌',
                '动作': '检查是否有板块利空，考虑是否减仓',
            })

    # --- 大盘环境 ---
    sh = index_data.get('上证', {})
    kc = index_data.get('科创50', {})
    if 'error' not in sh:
        sh_change = sh.get('涨跌幅', 0)
        if sh_change <= -2:
            alerts.append({
                'level': '🔴',
                '标的': '大盘',
                '内容': f'上证早盘跌{sh_change}%，系统性风险信号',
                '动作': '整体仓位不宜增加，等企稳信号',
            })
    if 'error' not in kc:
        kc_change = kc.get('涨跌幅', 0)
        if kc_change <= -3:
            alerts.append({
                'level': '🔴',
                '标的': '科创50',
                '内容': f'科创早盘跌{kc_change}%，科技成长承压',
                '动作': '进攻型ETF(515980/512760)需重点监控',
            })

    # --- 建设银行 ---
    if stock_quote and 'error' not in stock_quote:
        price = stock_quote.get('现价', 0)
        div_yield = round(0.40 / price * 100, 2) if price > 0 else 0
        if div_yield < 4.0:
            alerts.append({
                'level': '🟡',
                '标的': '建设银行(601939)',
                '内容': f'股息率{div_yield}%，低于4%阈值',
                '动作': '持续监控，尾盘确认',
            })

    return alerts


def estimate_market_volume(etf_quotes, index_data):
    """粗略估算早盘成交额（基于指数+ETF成交量推算）"""
    total_vol = 0
    for code, q in etf_quotes.items():
        if q and 'error' not in q:
            total_vol += q.get('成交额_万', 0)
    # 仅持仓ETF的成交额，非常粗略，但可参考相对水平
    return round(total_vol / 10000, 2)  # 亿


def format_report(index_data, etf_quotes, stock_quote, opening, alerts, north_flow):
    now_str = datetime.now().strftime('%H:%M')
    today_str = str(date.today())
    lines = []
    lines.append(f"🌅 A股早盘分析 | {today_str} {now_str} CST")
    lines.append("=" * 55)

    # 一、大盘环境
    lines.append("\n一、大盘环境")
    for name in ['上证', '科创50', '深证']:
        d = index_data.get(name, {})
        icon = '📈' if d.get('涨跌幅', 0) > 0 else ('📉' if d.get('涨跌幅', 0) < 0 else '➡️')
        if 'error' not in d:
            lines.append(f"  {icon} {name}: {d['现价']} ({d['涨跌幅']:+.2f}%)")
        else:
            lines.append(f"  {name}: --")

    # 北向资金
    if north_flow:
        nf = north_flow
        nf_val = nf.get('当日净流入_亿')
        if nf_val is not None:
            nf_icon = '🔴流出' if nf_val < 0 else '🟢流入'
            lines.append(f"\n  北向资金: {nf_icon} {nf_val:+.1f}亿 (数据日期: {nf.get('日期', 'N/A')})")

    # 二、持仓早盘快照
    lines.append("\n二、持仓早盘快照")
    lines.append(f"  {'标的':<16} {'现价':>7} {'涨跌':>7} {'开盘':>6} {'日内方向':>8} {'振幅':>6} {'成交额':>8}")
    lines.append("  " + "-" * 70)

    for code in list(ETF_SINA_MAP.keys()):
        q = etf_quotes.get(code) or {}
        o = opening.get(code) or {}
        if 'error' in q:
            lines.append(f"  {ETF_NAMES.get(code, code):<16} ⚠️ 获取失败")
            continue
        price = q.get('现价', 0)
        prev = q.get('昨收', 0)
        change = round((price / prev - 1) * 100, 2) if prev > 0 else 0
        vol = q.get('成交额_万', 0) / 10000  # 亿
        lines.append(
            f"  {ETF_NAMES.get(code, code):<16} {price:>7.4f} {change:>+6.2f}% "
            f"{o.get('开盘', '--'):>6} {o.get('日内方向', '--'):>8} "
            f"{o.get('振幅%', 0):>5.1f}% {vol:>7.2f}亿"
        )

    # 建设银行
    if stock_quote and 'error' not in stock_quote:
        s = stock_quote
        change = round((s['现价'] / s['昨收'] - 1) * 100, 2) if s.get('昨收', 0) > 0 else 0
        cost_pnl = round((s['现价'] / STOCK_COST.get('601939') or list(STOCK_COST.values())[0] if STOCK_COST else 1 - 1) * 100, 2)
        lines.append(f"  建设银行            {s['现价']:>7.2f} {change:>+6.2f}% {'--':>6} {'--':>8} {'--':>6} {'--':>8} 成本盈亏{cost_pnl:+.1f}%")

    # 三、开盘形态分析
    lines.append("\n三、开盘形态解读")
    for code in list(ETF_SINA_MAP.keys()):
        o = opening.get(code) or {}
        if not o:
            continue
        lines.append(
            f"  {o['名称']:<16} {o.get('开盘', '--')} ({o.get('开盘gap%', 0):+.1f}%) → "
            f"{o.get('日内方向', '--')} ({o.get('日内涨跌%', 0):+.1f}%)  |  振幅 {o.get('振幅%', 0):.1f}%"
        )

    # 四、触发信号
    lines.append(f"\n四、触发信号 ({len(alerts)}条)")
    if alerts:
        for a in alerts:
            lines.append(f"  {a['level']} {a['标的']}")
            lines.append(f"     {a['内容']}")
            lines.append(f"     → {a['动作']}")
    else:
        lines.append("  🟢 早盘无异常触发")

    # 五、今日关注要点
    lines.append("\n五、今日关注")
    sh = index_data.get('上证', {})
    kc = index_data.get('科创50', {})
    sh_change = sh.get('涨跌幅', 0)
    kc_change = kc.get('涨跌幅', 0)

    if sh_change > 1:
        lines.append("  ✅ 大盘偏强，进攻型可适度积极")
    elif sh_change < -1:
        lines.append("  ⚠️ 大盘偏弱，防御为主，不宜追高")
    else:
        lines.append("  ➡️ 大盘震荡，按兵不动等待方向")

    if kc_change > sh_change + 0.5:
        lines.append("  💡 科创强于主板，科技成长风格占优")

    lines.append(f"  🕐 下一个节点: 14:35 尾盘预警 → 15:45 完整日报")
    lines.append("\n" + "=" * 55)
    lines.append("早盘快照 · 数据来源: 新浪财经 + AKShare")
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

    print("⏳ 拉取早盘数据...", file=sys.stderr)

    # 并行拉取
    etf_quotes = {}
    for code, sina_code in ETF_SINA_MAP.items():
        etf_quotes[code] = fetch_sina_quote(sina_code)
    print("  ✅ ETF行情", file=sys.stderr)

    index_data = fetch_index()
    print("  ✅ 大盘指数", file=sys.stderr)

    stock_quote = fetch_stock()
    print("  ✅ 建设银行", file=sys.stderr)

    # 开盘形态分析
    opening = analyze_opening(etf_quotes)

    # 北向资金
    north_flow = fetch_north_flow()
    if north_flow:
        print(f"  ✅ 北向资金: {north_flow.get('当日净流入_亿', 'N/A')}亿", file=sys.stderr)

    # 触发检查
    alerts = check_morning_alerts(etf_quotes, stock_quote, index_data, opening)
    print(f"  ✅ 触发检查: {len(alerts)}条", file=sys.stderr)

    print("✅ 早盘分析完成", file=sys.stderr)
    return format_report(index_data, etf_quotes, stock_quote, opening, alerts, north_flow)


if __name__ == '__main__':
    report = main()
    if report:
        print(report)
