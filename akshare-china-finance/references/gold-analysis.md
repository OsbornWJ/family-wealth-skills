# Gold & Precious Metals Analysis via AKShare

**Origin**: Absorbed from `akshare-gold-analysis` skill.

Domain-specific guide for analyzing gold (XAU/USD), COMEX gold futures (GC), silver (XAG), and the Shanghai Gold Exchange (SGE) market using AKShare. All shared AKShare environment knowledge (import speed, API availability, fallbacks) lives in the parent `akshare-china-finance` SKILL.md — this file focuses on gold-specific methodology.

## Data Collection Pipeline

### Step 1: Core Gold Data (AKShare primary)

Run a single Python script to collect ALL core data in one go:

```python
import akshare as ak
import pandas as pd
import json

results = {}

# 1.1 COMEX gold futures daily (symbol="GC")
df = ak.futures_foreign_hist(symbol="GC").dropna(subset=['close'])
results['comex_gold'] = {
    'rows': len(df),
    'latest_close': float(df['close'].iloc[-1]),
    'latest_date': str(df['date'].iloc[-1])[:10],
    'ma50': round(float(df['close'].tail(50).mean()), 2),
    'ma200': round(float(df['close'].tail(200).mean()), 2),
    'high_20d': round(float(df['high'].tail(20).max()), 2),
    'low_20d': round(float(df['low'].tail(20).min()), 2),
    'high_52w': round(float(df['high'].tail(252).max()), 2),
    'low_52w': round(float(df['low'].tail(252).min()), 2),
}
# RSI(14)
delta = df['close'].diff()
gain = delta.clip(lower=0).tail(14).mean()
loss = -delta.clip(upper=0).tail(14).mean()
if loss > 0:
    results['comex_gold']['rsi14'] = round(float(100 - 100/(1 + gain/loss)), 1)

# 1.2 XAU/USD spot historical (symbol="XAU")
df_xau = ak.futures_foreign_hist(symbol="XAU").dropna(subset=['close'])
results['xau_usd'] = {
    'latest_close': float(df_xau['close'].iloc[-1]),
    'latest_date': str(df_xau['date'].iloc[-1])[:10],
}

# 1.3 Dollar index proxy (symbol="ZSD")
df_zsd = ak.futures_foreign_hist(symbol="ZSD").dropna(subset=['close'])
results['dxy_proxy'] = {
    'latest': float(df_zsd['close'].iloc[-1]),
    'trend_5d': 'up' if df_zsd['close'].iloc[-1] > df_zsd['close'].iloc[-5] else 'down',
}

print(json.dumps(results, indent=2, default=str))
```

### Step 2: China Domestic Gold & Macro Data

```python
# 2.1 Shanghai Gold Benchmark
df = ak.spot_golden_benchmark_sge()
results['sge_benchmark'] = {
    'latest_date': str(df['交易时间'].iloc[-1])[:10],
    'latest_morning': float(df['早盘价'].iloc[-1]),
    'latest_evening': float(df['晚盘价'].iloc[-1]),
}

# 2.2 China gold reserves
df = ak.macro_china_fx_gold()
results['china_gold_reserves'] = {
    'latest_month': str(df['月份'].iloc[-1]),
    'gold_tons': float(df['黄金储备-数值'].iloc[-1]),
    'gold_yoy_pct': float(df['黄金储备-同比'].iloc[-1]),
    'fx_reserves_bn': float(df['国家外汇储备-数值'].iloc[-1]),
}

# 2.3 China-US bond spread (for macro context)
df = ak.bond_zh_us_rate()
latest = df.iloc[-1]
results['bond_spread'] = {
    'date': str(latest['日期'])[:10],
    'cn_10y': float(latest['中国国债收益率10年']),
    'us_10y': float(latest['美国国债收益率10年']),
    'spread_bp': round((float(latest['中国国债收益率10年']) - float(latest['美国国债收益率10年'])) * 100, 1),
}

# 2.4 SGE Au99.99 detail
df = ak.macro_china_au_report()
au = df[df['商品'] == 'Au99.99'].iloc[-1]
results['sge_au9999'] = {
    'date': str(au['日期'])[:10],
    'close': float(au['收盘价']),
    'volume_kg': float(au['成交量']),
    'amount_bn': round(float(au['成交金额']) / 1e8, 2),
}
```

### Step 3: Fallback (when AKShare fails)

| Data | AKShare API | Sina fallback |
|------|-------------|---------------|
| XAU/USD spot | `futures_foreign_hist("XAU")` | `hq.sinajs.cn/list=hf_XAU` |
| COMEX gold | `futures_foreign_hist("GC")` | `hq.sinajs.cn/list=hf_GC` |
| Dollar index | `futures_foreign_hist("ZSD")` | `hq.sinajs.cn/list=hf_DINIW` |
| Silver | `futures_foreign_hist("XAG")` | `hq.sinajs.cn/list=hf_XAG` |

Sina fallback (real-time snapshot only, no history):
```bash
curl -sL "https://hq.sinajs.cn/list=hf_XAU,hf_GC,hf_XAG,hf_DINIW" -H "Referer: https://finance.sina.com.cn"
```

## Technical Indicators

| Indicator | Formula | Meaning |
|-----------|---------|---------|
| MA50 | `close.tail(50).mean()` | Medium-term trend |
| MA200 | `close.tail(200).mean()` | Long-term bull/bear boundary |
| RSI(14) | Wilder's standard formula | Overbought >70, oversold <30 |
| Support S1 | 20-day low | First support level |
| Resistance R1 | 20-day high | First resistance level |
| 52-week percentile | `(close - low52w) / (high52w - low52w)` | Year-to-date position |
| China-US spread | CN10Y - US10Y | Negative widening → gold bullish |

## Output Requirements

Every gold analysis report must include:
1. Data source annotation (AKShare vs fallback)
2. Full provenance chain: raw data → calculation → conclusion
3. Risk warnings before profit projections
4. Currency units on all prices (USD / RMB)

## Unit Conversion

- SGE prices are in RMB/gram
- International prices are in USD/oz
- Conversion: 1 troy ounce = 31.1035 grams
- Spot conversion: XAU/USD ÷ 31.1035 × USD/CNY rate = RMB/gram

## Pitfalls Specific to Gold Analysis

- `futures_foreign_hist` volume/position fields may be 0 for some symbols; price data is always valid
- ZSD is a dollar index proxy (not standard DXY=100 scale); use for trend direction only, not absolute level
- Sina fallback provides **same-day snapshot only** — no historical data
- East Money APIs (`bond_zh_us_rate`, `macro_china_*`) are distinct from the unreliable East Money endpoints; they generally work
- Gold-specific APIs (`spot_golden_benchmark_sge`, `macro_china_fx_gold`) hit Shanghai Gold Exchange endpoints, not East Money — they are reliable
