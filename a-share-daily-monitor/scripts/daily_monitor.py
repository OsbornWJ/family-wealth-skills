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
print(f"[portfolio] loaded {_PF['path']}", flush=True)

SINA_HEADERS = {'Referer': 'https://finance.sina.com.cn'}


# ============================================================
# 1. 大盘环境
# ============================================================
def pull_market():
    """拉取上证指数、科创50、成交额"""
    result = {}
    try:
        df_sh = ak.stock_zh_index_daily(symbol='sh000001')
        sh = df_sh.iloc[-1]
        sh_prev = df_sh.iloc[-2]
        # volume 是成交股数，估算成交额：股数 × 均价(~8元)
        sh_volume_shares = float(sh['volume'])
        sh_amount_est = sh_volume_shares * 8 / 1e8  # 估算亿
        result['上证指数'] = {
            '收盘': round(float(sh['close']), 2),
            '涨跌幅': round((float(sh['close']) / float(sh_prev['close']) - 1) * 100, 2),
            '成交量_亿股': round(sh_volume_shares / 1e8, 1),
            '估算成交额_亿': round(sh_amount_est, 1),
        }
    except Exception as e:
        result['上证指数'] = {'error': str(e)[:100]}

    try:
        df_kc = ak.stock_zh_index_daily(symbol='sh000688')
        kc = df_kc.iloc[-1]
        kc_prev = df_kc.iloc[-2]
        result['科创50'] = {
            '收盘': round(float(kc['close']), 2),
            '涨跌幅': round((float(kc['close']) / float(kc_prev['close']) - 1) * 100, 2),
        }
    except Exception as e:
        result['科创50'] = {'error': str(e)[:100]}

    # 涨跌比估算（从两市成交额推算）
    try:
        df_sz = ak.stock_zh_index_daily(symbol='sz399001')
        sz = df_sz.iloc[-1]
        sz_volume_shares = float(sz['volume'])
        sz_amount_est = sz_volume_shares * 8 / 1e8
        result['深证成指'] = {
            '收盘': round(float(sz['close']), 2),
            '涨跌幅': round((float(sz['close']) / float(df_sz.iloc[-2]['close']) - 1) * 100, 2),
            '成交量_亿股': round(sz_volume_shares / 1e8, 1),
            '估算成交额_亿': round(sz_amount_est, 1),
        }
    except:
        pass

    sh_amt = result.get('上证指数', {}).get('估算成交额_亿', 0)
    sz_amt = result.get('深证成指', {}).get('估算成交额_亿', 0)
    total_vol = sh_amt + sz_amt
    result['全市场估算成交额_万亿'] = round(total_vol / 10000, 2)
    result['成交额达标'] = '✅ ≥2.8万亿' if total_vol >= 28000 else ('🟡 1.5-2.8万亿' if total_vol >= 15000 else f'🔴 仅{total_vol/10000:.2f}万亿')

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
# 4. 建设银行
# ============================================================
def pull_stock_601939():
    """新浪财经实时行情"""
    try:
        url = 'https://hq.sinajs.cn/list=sh601939'
        r = requests.get(url, headers=SINA_HEADERS, timeout=10)
        data = r.text.split('"')[1]
        fields = data.split(',')
        # 0:name, 1:open, 2:prev_close, 3:price, 4:high, 5:low, 6:bid, 7:ask, 8:volume, 9:amount
        price = float(fields[3])
        prev_close = float(fields[2])
        change_pct = round((price / prev_close - 1) * 100, 2)

        return {
            '名称': '建设银行',
            '最新价': price,
            '昨收': prev_close,
            '涨跌幅': change_pct,
            '最高': float(fields[4]),
            '最低': float(fields[5]),
            '成交量_手': int(fields[8]),
            '成本价': STOCK_COST['601939'],
            '成本盈亏_pct': round((price / STOCK_COST['601939'] - 1) * 100, 2),
        }
    except Exception as e:
        return {'error': str(e)[:100]}


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

    # --- 进攻型：移动止盈 ---
    for code in ['515980', '512760']:
        d = etf_data.get(code, {})
        if 'error' in d:
            continue
        peak = PEAK_NAV.get(code, d.get('60日峰值', d.get('单位净值', 0)))
        current = d.get('单位净值', 0)
        drawdown = (1 - current / peak) * 100 if peak > 0 else 0

        if drawdown >= 15:
            alerts.append({
                'level': '🔴 红色',
                '标的': f'{ETF_NAMES[code]}({code})',
                '触发': f'移动止盈：从峰值{peak}回撤{drawdown:.1f}% ≥ 15%',
                '动作': '减仓 1/2',
            })

    # --- 进攻型：硬止损（季报/资本开支）---
    # 这类数据需要人工判断或web search，脚本只做提醒
    # 不自动触发

    # --- 防御型：红利ETF ---
    d_562060 = etf_data.get('562060', {})
    if 'error' not in d_562060:
        # 股息率检查（估算）
        # 红利ETF当前净值约0.64，年化分红约0.025-0.03，估算股息率约4%
        # 这里用粗糙估算，实际应从数据源获取
        nav_562060 = d_562060.get('单位净值', 0)
        if nav_562060:
            # 标普A股红利ETF近12个月分红约0.028，估算股息率
            est_div_yield = round(0.028 / nav_562060 * 100, 2) if nav_562060 > 0 else 0
            if est_div_yield < 3.5:
                alerts.append({
                    'level': '🔴 红色',
                    '标的': f'{ETF_NAMES["562060"]}(562060)',
                    '触发': f'估算股息率{est_div_yield}% < 3.5%',
                    '动作': '需要重新评估（同时检查技术面破位）',
                })
        # MA120破位检查
        ma120_dev = d_562060.get('偏离MA120_pct')
        if ma120_dev is not None and ma120_dev < -3:
            alerts.append({
                'level': '🟡 黄色',
                '标的': f'{ETF_NAMES["562060"]}(562060)',
                '触发': f'偏离MA120 {ma120_dev:.1f}%, 跌破幅度超3%',
                '动作': '进入观察列表，关注股息率是否同步恶化',
            })

    # --- 防御型：建设银行 ---
    if 'error' not in stock_data:
        price_601939 = stock_data.get('最新价', 0)
        # 建行2024年分红约0.40元/股
        div_yield_601939 = round(0.40 / price_601939 * 100, 2) if price_601939 > 0 else 0
        if div_yield_601939 < 4.0:
            alerts.append({
                'level': '🔴 红色',
                '标的': '建设银行(601939)',
                '触发': f'股息率{div_yield_601939}% < 4%',
                '动作': '触发减持条件，建议评估',
            })

    # --- 观察型：军工 ---
    d_512660 = etf_data.get('512660', {})
    if 'error' not in d_512660:
        cost = COST_NAV.get('512660', 0)
        current = d_512660.get('单位净值', 0)
        if current > cost and cost > 0:
            triggers.append({
                'level': '📊 信息',
                '标的': f'{ETF_NAMES["512660"]}(512660)',
                '触发': f'净值{current} > 成本净值{cost}，触发重新评估',
                '动作': '主人请重新评估军工仓位',
            })

    # --- 成交额预警 ---
    total_vol = market_data.get('全市场估算成交额_万亿', 0)
    if total_vol < 1.0:
        alerts.append({
            'level': '🔴 红色',
            '标的': '大盘',
            '触发': f'成交额仅{total_vol}万亿，极度缩量',
            '动作': '注意流动性风险，不宜追高',
        })
    elif total_vol < 1.5:
        alerts.append({
            'level': '🟡 黄色',
            '标的': '大盘',
            '触发': f'成交额{total_vol}万亿，偏冷淡',
            '动作': '控制仓位，等待放量',
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
        lines.append(f"  上证: {sh['收盘']} ({sh['涨跌幅']:+.2f}%) | 成交 {sh.get('估算成交额_亿',0):.0f}亿(估)")
    if 'error' not in kc:
        lines.append(f"  科创50: {kc['收盘']} ({kc['涨跌幅']:+.2f}%)")
    if 'error' not in sz:
        lines.append(f"  深证: {sz['收盘']} ({sz['涨跌幅']:+.2f}%) | 成交 {sz.get('估算成交额_亿',0):.0f}亿(估)")
    lines.append(f"  全市场估算成交额: {market.get('全市场估算成交额_万亿', 'N/A')}万亿 {market.get('成交额达标', '')}")

    # 二、持仓快照
    lines.append("\n二、持仓快照")
    lines.append(f"  {'标的':<16} {'净值':>7} {'日涨跌':>7} {'偏离5MA':>8} {'偏离20MA':>8} {'偏离120MA':>8} {'回撤峰值':>8} {'成本盈亏':>8} {'信号':>4}")
    lines.append("  " + "-" * 83)

    for code in ['515980', '512760', '589720', '562060', '512660']:
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

        lines.append(
            f"  {d['名称']:<16} {d['单位净值']:>7.4f} {d['日涨跌幅']:>+6.2f}% "
            f"{d['偏离MA5_pct']:>+7.2f}% {d['偏离MA20_pct']:>+7.2f}% "
            f"{d.get('偏离MA120_pct', 0):>+7.2f}% "
            f"{d['距峰值回撤_pct']:>+7.1f}% {cost_pnl:>8} {sig_str:<10}"
        )

    # 建设银行
    if 'error' not in stock_data:
        s = stock_data
        lines.append(
            f"  {s['名称']:<16} {s['最新价']:>7.2f} {s['涨跌幅']:>+6.2f}% "
            f"{'--':>8} {'--':>8} {'--':>8} "
            f"{s.get('成本盈亏_pct', 0):>+7.1f}% {'🏦':>4}"
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

    stock_data = pull_stock_601939()
    print("  ✅ 建设银行", file=sys.stderr)

    external = pull_external()
    print("  ✅ 外部变量", file=sys.stderr)

    alerts, triggers = check_triggers(etf_data, stock_data, market, flow_data, external)

    report = format_report(market, etf_data, flow_data, stock_data, external, alerts, triggers)
    return report


if __name__ == '__main__':
    report = main()
    print(report)
