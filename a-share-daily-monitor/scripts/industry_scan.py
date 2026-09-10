#!/usr/bin/env python3
"""全自动行业低估扫描 — 申万指数+ETF净值"""
import warnings
warnings.filterwarnings('ignore')
import akshare as ak
import pandas as pd
from datetime import date, timedelta

today = date.today()
cutoff_60 = today - timedelta(days=90)
cutoff_ytd = date(today.year, 1, 1)

SW_INDICES = {
    '煤炭': '801950', '房地产': '801180', '通信': '801770',
    '银行': '801780', '医药生物': '801150', '食品饮料': '801120',
    '电力设备': '801730', '农林牧渔': '801010', '非银金融': '801790',
    '国防军工': '801740', '电子': '801080', '计算机': '801750',
    '传媒': '801760', '机械设备': '801890', '基础化工': '801030',
    '家用电器': '801110', '汽车': '801880', '建筑装饰': '801720',
    '公用事业': '801160', '有色金属': '801050',
}

LOGIC = {
    '煤炭': '能源回落+高股息安全垫，等煤价企稳',
    '房地产': '政策底但基本面磨底，左侧风险大',
    '通信': 'AI主升浪过，光通信/卫星互联网有二次催化',
    '银行': '高股息(5%+)护城河，适合防御底仓',
    '医药生物': '集采减弱+创新药出海，已有反弹迹象',
    '食品饮料': '消费复苏不确定，龙头估值回落合理区间',
    '电力设备': '产能过剩消化中，关注出海和新技术',
    '农林牧渔': '猪周期底部，等拐点确认',
    '非银金融': '成交额放大直接受益，牛市弹性最大',
    '国防军工': '订单驱动，关注十四五中期调整',
    '电子': '芯片周期上行，高景气但估值已高',
    '计算机': '信创+AI应用，等订单落地信号',
    '传媒': 'AI退潮缺催化，游戏/广告复苏不确定',
    '机械设备': '制造升级+出海，景气度较高',
    '基础化工': 'PPI低迷，新材料国产替代逻辑',
    '家用电器': '出口+内需，估值合理弹性有限',
    '汽车': '价格战压利润，关注智能化增量',
    '建筑装饰': '基建加码+低估值央企重估',
    '公用事业': '电力改革+绿电，防御但弹性不足',
    '有色金属': '全球大宗定价，关注美元和美联储',
}

SH_BENCHMARK = 8.0

results = []
print("拉取申万行业指数...")
for name, code in SW_INDICES.items():
    try:
        df = ak.index_hist_sw(symbol=code, period='day')
        if df is None or len(df) == 0:
            continue
        df['日期_d'] = pd.to_datetime(df['日期']).dt.date
        latest = df.iloc[-1]
        close_now = float(latest['收盘'])
        df_60 = df[df['日期_d'] >= cutoff_60]
        chg_60d = round((close_now/float(df_60.iloc[0]['收盘'])-1)*100,2) if len(df_60)>=2 else None
        df_ytd = df[df['日期_d'] >= cutoff_ytd]
        chg_ytd = round((close_now/float(df_ytd.iloc[0]['收盘'])-1)*100,2) if len(df_ytd)>=2 else None
        results.append({'行业':name,'指数':close_now,'近60日':chg_60d,'YTD':chg_ytd})
        print(f"  {name:<8} {close_now:>10.2f}  近60日{chg_60d:+.1f}%  YTD{chg_ytd:+.1f}%")
    except Exception as e:
        print(f"  {name:<8} FAIL: {str(e)[:60]}")

print(f"\n{'='*70}")
print(f"近60日排名 (vs上证+{SH_BENCHMARK}%)")
print(f"{'='*70}")
valid = sorted([r for r in results if r['近60日'] is not None], key=lambda x: x['近60日'])
for r in valid:
    gap = r['近60日'] - SH_BENCHMARK
    label = 'RUN' if gap < -8 else ('LAG' if gap < 0 else 'WIN')
    print(f"  [{label}] {r['行业']:<8} {r['近60日']:>+6.1f}% (gap{gap:+.0f}pp)")

print(f"\n{'='*70}")
print("跑输候选分析")
print(f"{'='*70}")
laggards = sorted([r for r in valid if r['近60日'] < SH_BENCHMARK], key=lambda x: x['近60日'])
for r in laggards:
    print(f"  {r['行业']}  60d{r['近60日']:+.1f}%  YTD{r.get('YTD',0):+.1f}%  {LOGIC.get(r['行业'],'?')}")

print(f"\nYTD排名")
ytd_v = sorted([r for r in results if r['YTD'] is not None], key=lambda x: x['YTD'])
for r in ytd_v:
    print(f"  {r['行业']:<8} {r['YTD']:>+6.1f}%")
print("\nDone.")
