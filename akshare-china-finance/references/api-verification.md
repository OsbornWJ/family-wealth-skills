# AKShare API Availability Verification (2026-05-20)

**Origin**: Absorbed from `a-share-daily-monitor` skill `references/api-verification.md`.

Original audit log of which AKShare APIs work in this environment. The definitive list lives in the parent `akshare-china-finance` SKILL.md — this file preserves the original audit details.

## ✅ Verified Working

| API | Purpose | Notes |
|-----|---------|-------|
| `stock_zh_index_daily(symbol='sh000001')` | 上证指数 | volume is shares, not yuan |
| `stock_zh_index_daily(symbol='sh000688')` | 科创50 | |
| `stock_zh_index_daily(symbol='sz399001')` | 深证成指 | |
| `fund_open_fund_info_em(symbol, indicator='单位净值走势')` | ETF NAV history | For MA calculations |
| `fund_etf_fund_daily_em()` | ETF fund flow | Current price, NAV, premium/discount |
| `bond_zh_us_rate()` | China–US bond spread | US 10Y / China 10Y |
| `index_hist_sw(symbol='801xxx', period='day')` | 申万行业指数 | Date column needs `pd.to_datetime` conversion |
| `futures_foreign_hist(symbol)` | International futures | GC, XAU, ZSD, XAG |
| `spot_golden_benchmark_sge()` | SGE gold benchmark | |
| `macro_china_fx_gold()` | China gold reserves | |
| `macro_china_au_report()` | SGE Au99.99 | |

## ❌ Unavailable / Blocked

| API | Error | Workaround |
|-----|-------|------------|
| `fund_etf_hist_em` | RemoteDisconnected | `fund_open_fund_info_em` for NAV history |
| `stock_zh_a_hist` | RemoteDisconnected | Sina `hq.sinajs.cn` for real-time |
| `stock_zh_a_spot_em` | RemoteDisconnected | Same |
| `index_zh_a_hist` | RemoteDisconnected | `stock_zh_index_daily` |
| `stock_board_industry_summary_em()` | ❌ Does not exist | `index_hist_sw` |
| `stock_sector_fund_flow_rank()` | RemoteDisconnected | ETF NAV divergence + index trend |

## Sina Real-time Format (Preserved Reference)

```
URL: https://hq.sinajs.cn/list=sh601939
Headers: Referer: https://finance.sina.com.cn

Fields comma-separated:
  0: name          1: open         2: prev_close   3: current
  4: high          5: low          6: bid          7: ask
  8: volume(shares) 9: amount(yuan) ... 30: date    31: time
```

## Turnover Estimation

`stock_zh_index_daily` volume = shares, not yuan.
Estimated total = (SH volume + SZ volume) × ~8 yuan avg / 1e8.
