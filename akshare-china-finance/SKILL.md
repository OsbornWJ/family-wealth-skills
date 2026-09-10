---
name: akshare-china-finance
description: Use when 拉取中国财经数据或行情源失败需降级。免费无 Key 多源矩阵。
license: MIT
compatibility: Requires Python 3, requests, pandas; akshare/baostock recommended; mootdx optional. No API keys.
metadata:
  author: stunner
  version: "1.2.0"
  tags: "akshare,china-finance,shanghai-stock,shenzhen-stock,financial-data,API"
  hermes_related: "a-share-daily-monitor,a-share-stock-fundamental-analysis"
  openclaw: '{"requires":{"bins":["python3"]}}'
---

# China Finance Data — Shared Knowledge Base

Class-level skill for China (A-share) market data. **Default path is free and needs no API key.**

## Quote failover (read this first)

See [`references/data-source-matrix.md`](references/data-source-matrix.md).

```bash
pip3 install requests pandas akshare baostock
# optional: pip3 install mootdx
python3 scripts/quote_providers.py   # smoke: Tencent → Sina → …
```

```python
from quote_providers import get_realtime, get_daily_bars
q = get_realtime(["sh601939", "s_sh000001"])
bars = get_daily_bars("601939", 120)
```

Realtime priority: **Tencent → Sina → mootdx(optional)**. Daily bars: **baostock → mootdx → Sina K → AKShare last**.

## Environment Setup

```bash
pip3 install akshare pandas requests baostock
```

**⚠️ AKShare import is slow** — first `import akshare` takes 5–10 seconds. Always pull ALL needed data in a single Python script, never multiple scripts or repeated module imports.

## Verified API Status (this environment)

### ✅ Working data sources

| API | Data | Notes |
|-----|------|-------|
| `ak.index_hist_sw(symbol, period='day')` | 申万一级行业指数 (20 sectors) | Codes: 801010–801950. Returns columns: `['代码','日期','收盘','开盘','最高','最低']` |
| `ak.stock_zh_index_daily(symbol)` | Broad market indices | `sh000001` (上证), `sh000688` (科创50), `sz399001` (深成指). **volume is shares, not yuan** |
| `ak.fund_open_fund_info_em(symbol, indicator='单位净值走势')` | ETF Net Asset Value history | Chinese column names: `净值日期`, `单位净值`, `日增长率`. **Date column is string type** |
| `ak.fund_etf_fund_daily_em()` | ETF daily fund flows | Price, NAV, premium/discount |
| `ak.bond_zh_us_rate()` | China–US bond yields | Chinese column names may vary (`利率名称` / `指标名称`) |
| `ak.futures_foreign_hist(symbol)` | International futures/forex | `GC` (COMEX gold), `XAU` (spot gold), `ZSD` (dollar index proxy), `XAG` (silver) |
| `ak.spot_golden_benchmark_sge()` | Shanghai Gold Exchange benchmark | |
| `ak.macro_china_fx_gold()` | China gold reserves | |
| `ak.macro_china_au_report()` | SGE Au99.99 details | |
| `ak.stock_yjbb_em(date='YYYYMMDD')` | Quarterly financial summary (~5801 stocks) | Columns: 股票代码, 股票简称, 每股收益, 营业总收入-同比增长, 净利润-同比增长, 每股净资产, 净资产收益率, 销售毛利率, 所处行业. **Q1 EPS must be annualized (×4) for PE calc** |
| `ak.stock_index_pe_lg(symbol="沪深300")` | CSI 300 PE history (2005~now) | Returns 5160+ rows: 日期, 指数, 滚动市盈率, 静态市盈率, 等权滚动市盈率. **Works reliably.** For percentile analysis: `(series < current_val).sum() / len(series) * 100` |
| `ak.stock_index_pb_lg(symbol="沪深300")` | CSI 300 PB history (2005~now) | Same structure as PE. Key frame: PB 1.43 @28%分位 vs PE 13.59 @64%分位 → 结构性分化判断 |
| `ak.stock_zh_index_value_csindex(symbol="000300")` | CSIndex official PE/PB (weekly-ish) | Columns: 日期, 指数代码, 市盈率1(static), 市盈率2(TTM), 股息率1, 股息率2. **Use as cross-check** for PE_lg/pb_lg data |
| Sina Finance `hq.sinajs.cn` | Real-time quotes | Header: `Referer: https://finance.sina.com.cn`. Fields: name, open, prev close, current, high, low, bid, ask, volume(shares), amount(yuan), date, time. Rate-limit: `time.sleep(0.3)` between batches. **Batch 50 stocks per request** using comma-separated list |
| Sina K-line `money.finance.sina.com.cn/.../getKLineData` | Historical K-line | URL: `https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh603019&scale=240&datalen=120`. **Field name is `day` not `date`** |

### ❌ Unavailable / blocked APIs

| API | Error | Fallback |
|-----|-------|----------|
| `ak.fund_etf_hist_em` | Intermittent — may work or fail | Try first; if `RemoteDisconnected`, fallback to `fund_open_fund_info_em` + Sina real-time. **科创板ETF (5xxxxx codes)**: `fund_etf_hist_em` often works even when push2.eastmoney.com returns empty |
| `ak.stock_zh_a_hist` | `RemoteDisconnected` | Sina `hq.sinajs.cn` |
| `ak.stock_zh_a_spot_em` | `RemoteDisconnected` | Same |
| `ak.index_zh_a_hist` | `RemoteDisconnected` | Use `stock_zh_index_daily` |
| `ak.stock_board_industry_summary_em()` | **Does not exist in this version** | Use `index_hist_sw` |
| `ak.stock_sector_fund_flow_rank()` | `RemoteDisconnected` | Use ETF NAV divergence + index trends instead |
| `ak.stock_profit_sheet_by_report_em()` | Returns `None` | Use `stock_yjbb_em` summary + industry mean estimates |
| `ak.stock_balance_sheet_by_report_em()` | Returns `None` | Industry mean estimates for debt ratios |
| `ak.stock_cash_flow_sheet_by_report_em()` | Returns `None` | Use `stock_yjbb_em` 每股经营现金流量 field |
| `ak.stock_individual_info_em()` | `RemoteDisconnected` | Use Sina quotes for price, `stock_yjbb_em` for earnings |
| East Money `push2.eastmoney.com` | `RemoteDisconnected` | **All** push2 endpoints blocked; use Sina throughout |
| `money.163.com` (网易财经) | `502 Bad Gateway` | Historical CSV via `chddata.html` endpoint unreliable; use Sina K-line `getKLineData` instead |

## Critical Pitfalls

### 1. Volume is shares, not yuan
`stock_zh_index_daily` returns volume in shares (股), not amount (元). Estimated market turnover ≈ (SH volume + SZ volume) × ~8 yuan/share ÷ 1e8 for 亿元. This is an approximation only.

### 2. Chinese column names
AKShare APIs from East Money return Chinese column names. Always inspect `.columns.tolist()` first before referencing columns. Common examples:
- `fund_open_fund_info_em`: `净值日期`, `单位净值`, `日增长率`
- `bond_zh_us_rate`: column names may vary (`利率名称` vs `指标名称`)
- `index_hist_sw`: `['代码','日期','收盘','开盘','最高','最低']`

### 3. Date columns are strings
`pd.to_datetime(df['日期']).dt.date` (or equivalent) is required before date comparisons. Never assume datetime type.

### 4. T-1 data after market close
`stock_zh_index_daily` does NOT update immediately at 15:00 close — data is typically T-1 until evening batch. For same-day close prices, use Sina `hq.sinajs.cn` real-time API instead.

### 5. execute_code sandbox vs terminal

`execute_code` runs in a sandbox environment that may not have `akshare` installed (even if the system Python does). Always use `terminal()` to run Python scripts that import akshare. Alternative: run scripts directly via `/path/to/python3 /tmp/script.py` in terminal.

### 6. Sina batch query method

For querying 50–200 stocks at once, comma-separate in a single URL:

```python
sina_codes = [f"{'sh' if c.startswith('6') else 'sz'}{c}" for c in codes]
url = f'https://hq.sinajs.cn/list={",".join(sina_codes)}'
```

**Response format** — one line per stock:
```
var hq_str_s_sh601939="建设银行,10.060,-0.120,-1.18,1038261,104015";
var hq_str_s_sz300573="兴齐眼药,37.81,-0.140,-0.37,257841,9716267";
```

Fields: name, open, prev_close, current, high, low, bid, ask, volume(shares), amount(yuan), ...

**Prefix rules**: `6xxx`/`688xxx` → `sh` | `0xxx`/`3xxx` → `sz`

### 7. PE calculation from stock_yjbb_em data

`stock_yjbb_em` returns **quarterly** EPS. For annualized PE:

```python
# Q1 EPS → annualized × 4
annualized_eps = eps_q1 * 4
pe_ttm_est = current_price / annualized_eps
```

This is an estimate, not true TTM PE (which uses trailing 4 quarters). But Q1×4 is a reasonable proxy for screening purposes.
Burst requests to `hq.sinajs.cn` return empty data. Add `time.sleep(0.3)` between sequential requests, or batch in groups of 5–8 with `time.sleep(0.5)` between groups.

### 8. Script execution from profile scripts directory

When running analysis scripts, **always use the Hermes profile's scripts directory** (`~/.hermes/profiles/stunner/scripts/`), not arbitrary project directories like `other-project`. The profile scripts are maintained and versioned as part of the skill library. Running scripts from other-project or other project dirs was explicitly corrected by the user.

If a morning_check.py or similar script exists in the profile scripts dir, run it directly:
```bash
python3 ~/.hermes/profiles/stunner/scripts/morning_check.py
```
Not via a project directory's path.

### 10. 科创板ETF (5xxxxx codes) — EastMoney push2 API returns empty

科创板ETF codes (5xxxxx, e.g. 589720) have a unique quirk: the EastMoney `push2.eastmoney.com/api/qt/stock/kline/get?secid=1.589720` endpoint returns `{"data":{}}` (empty), even though it works for other codes (6xxxxx, 0xxxxx). However, `ak.fund_etf_hist_em(symbol="589720", period="daily", adjust="qfq")` does work for these codes.

When historical K-line data for a 科创板ETF returns nothing from push2:
1. Try `ak.fund_etf_hist_em` first (it often works)
2. If that also fails, use `fund_open_fund_info_em` for NAV history
3. Last resort: Sina `hq.sinajs.cn` real-time + manually track from session data

**Note**: The Sina K-line API (`getKLineData`) does NOT support 科创板ETF codes (5xxxxx). It returns an empty array for these codes. So for historical daily data on 科创板ETF, AKShare's `fund_etf_hist_em` is the only viable programmatic source.
APIs hitting `api-fund.eastmoney.com` and `push2his.eastmoney.com` (e.g. `fund_etf_hist_em`, `stock_zh_a_hist`) are unreliable from this environment. Prefer `fund_open_fund_info_em` (which hits a different endpoint) and Sina real-time for price data.

## Sina K-line API — Detailed Usage

The Sina K-line endpoint is the **most reliable source** for historical price data when EM/163 endpoints fail:

```python
import requests, json

url = ('https://money.finance.sina.com.cn/quotes_service/api/json_v2.php'
       '/CN_MarketData.getKLineData'
       '?symbol=sh600584&scale=240&ma=no&datalen=120')

headers = {'Referer': 'https://finance.sina.com.cn'}
r = requests.get(url, headers=headers, timeout=10)
data = json.loads(r.text)  # list of dicts
```

### Parameters

| Param | Values | Description |
|-------|--------|-------------|
| `symbol` | `sh600584`, `sz300573` | Prefix: `sh` for 6xx/688xx, `sz` for 0xx/3xx |
| `scale` | `240` (daily), `60` (60min), `30` (30min), `15` (15min), `5` (5min) | K-line period |
| `datalen` | Integer, e.g. `30`, `60`, `120` | Number of candles to return |
| `ma` | `no` (default) | Moving average overlay (not needed — calculate yourself) |

### Response Fields

| Field | Type | Example |
|-------|------|---------|
| `day` | str (YYYY-MM-DD) | `2026-06-11` |
| `open` | str (float) | `72.600` |
| `high` | str (float) | `74.260` |
| `low` | str (float) | `71.000` |
| `close` | str (float) | `71.950` |
| `volume` | str (int) | `55975440` (in 手, or shares depending on instrument) |
| `ma_priceXX` | str (float, only when ma param set) | — |

**⚠️ Field names are lowercase English** (`day` not `date`, `close` not `收盘`). This differs from AKShare's Chinese column names.

### Common Analysis Patterns

**Moving averages:**
```python
closes = [float(d['close']) for d in data]
ma5  = sum(closes[-5:]) / 5
ma10 = sum(closes[-10:]) / 10
ma20 = sum(closes[-20:]) / 20
```

**Support/resistance (N-day range):**
```python
low_n  = min(float(d['low'])  for d in data[-N:])
high_n = max(float(d['high']) for d in data[-N:])
dist_from_low  = (curr / low_n  - 1) * 100
dist_from_high = (curr / high_n - 1) * 100
```

**Amplitude (volatility):**
```python
amp = (high - low) / prev_close * 100  # single day
avg_amp_5 = sum(amp_n for n in last_5) / 5  # 5-day avg
```

**Volume ratio (relative to 20-day average):**
```python
vol5  = sum(int(d['volume']) for d in data[-5:]) / 5
vol20 = sum(int(d['volume']) for d in data[-20:]) / 20
ratio = vol5 / vol20  # >1.3 = elevated, <0.7 = quiet
```

**3-day momentum:**
```python
last3_chg = [(closes[-i] - closes[-i-1]) / closes[-i-1] * 100 for i in range(1, 4)]
```

### Rate Limiting

The Sina K-line API is generous — no rate limiting observed even with 10+ parallel requests. The real-time quote API (`hq.sinajs.cn`) is slightly more restrictive; batch 50 codes per request and add `time.sleep(0.3)` between batches.

### Intraday (tick-by-tick) alternative — unreliable

The 163.com intraday API (`quotes.money.163.com/cjmx/2026/1/0603588.json`) frequently returns `502 Bad Gateway`. **Do not rely on it for production analysis.** Use the Sina real-time API for current price and the Sina K-line API for historical trends.

---

## Sina Real-time Quote Format

```
URL: https://hq.sinajs.cn/list=sh601939
Header: Referer: https://finance.sina.com.cn
Fields (comma-separated): name, open, prev_close, current, high, low,
  bid, ask, volume(shares), amount(yuan), ..., date, time
```

## Reference Files

- `references/gold-analysis.md` — Gold/precious metals analysis methodology (absorbed from `akshare-gold-analysis`)
- `references/api-verification.md` — Original API verification log (from `a-share-daily-monitor`)

## Related Skills

- `a-share-daily-monitor` — Portfolio monitoring pipeline (holdings, cron jobs, stop-loss rules). Uses the APIs documented here.
