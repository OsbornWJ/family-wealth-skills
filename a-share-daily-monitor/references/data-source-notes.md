# A股数据源有效性记录

## 可用数据源 ✅

### 1. 新浪财经 `hq.sinajs.cn`（实时行情）✅（首选）
最稳定、最快、支持所有A股（个股+ETF+指数）。
- **格式：** `https://hq.sinajs.cn/list=sh512760,sz300308`
- **返回：** `var hq_str_sh512760=\"名称,开盘,昨收,现价,最高,最低,买一,卖一,成交量(手),成交额(元),...\"`
- **编码：** gbk，Python需 `.decode('gbk')`
- **限流：** 连续请求需加 `time.sleep(0.3)`，否则返回空
- **代码前缀：**
  - 上交所 `51/56/58`开头 = `sh`（ETF），`6`开头 = `sh`（主板个股），`688`开头 = `sh`（科创板）
  - 深交所 `15/16`开头 = `sz`（ETF），`0`开头 = `sz`（主板个股），`3`开头 = `sz`（创业板）
  - 个股如：中际旭创300308=sz300308，北方华创002371=sz002371
- **Referer头必须设置**为 `https://finance.sina.com.cn`，否则被拦
- **2026-06-02验证：** 深市个股（300308/002371/300502）全部正常工作

### 1b. 新浪财经 日K线API `money.finance.sina.com.cn` ✅（2026-06-02新增推荐）
当AKShare K线数据失败时，新浪的独立K线API比东财push2更稳定。
- **端点：** `https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData`
- **参数：** `symbol=sh603019&scale=240&datalen=120`
  - `scale=240` = 日K，`scale=60` = 60分钟
  - `datalen=120` = 最多120条
- **字段名：** ⚠️ 注意是`day`不是`date`
  - `day`（日期，字符串如`2026-06-02`）
  - `open`、`close`、`high`、`low`（都是字符串，需float()）
  - `volume`（股数，字符串）
  - 额外带预计算均线：`ma_price5`、`ma_volume5`、`ma_price10`、`ma_volume10`、`ma_price30`、`ma_volume30`
- **Referer头：** 推荐设置 `Referer: https://finance.sina.com.cn`
- **返回格式：** JSON数组，直接从API返回可解析
- **示例：**
  ```python
  url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh603019&scale=240&datalen=120'
  req = urllib.request.Request(url, headers={'Referer': 'https://finance.sina.com.cn'})
  data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
  # data[0] = {'day':'2025-12-01', 'open':'102.300', 'close':'101.130', ...}
  ```
- **2026-06-02验证：** 中科曙光(603019)、长电科技(600584)均正常工作

### 1c. AKShare 业绩快报API `stock_yjbb_em` ✅（2026-06-02验证）
当需要个股年度/季度营收、净利润、EPS等核心指标时可用。利润表明细API `stock_profit_sheet_by_report_em` 返回None。
- `ak.stock_yjbb_em(date='20251231')` — 年报业绩，过滤`股票代码=='603019'`
- `ak.stock_yjbb_em(date='20260331')` — 一季报
- 可用字段：股票代码、股票简称、每股收益、营业总收入、营业总收入-同比增长、净利润-净利润、净利润-同比增长、每股净资产、净资产收益率、销售毛利率
- ⚠️ 利润表/资产负债表API (`stock_profit_sheet_by_report_em`, `stock_balance_sheet_by_report_em`) 返回None，不可用

### 2. AKShare（东财通道 — 偶发RemoteDisconnected）
可用但有间歇性失败
- `fund_open_fund_info_em` — ETF净值历史（可用，收盘后为T-1数据）
- `stock_zh_index_daily` — 指数日K（volume字段=股数非金额）
- `bond_zh_us_rate` — 美债收益率
- `fund_etf_fund_daily_em` — ETF折溢价

### 3. 东方财富 push2 API
AKShare失败时的回退方案
- `https://push2.eastmoney.com/api/qt/stock/kline/get`
- 上交所 secid=`1.`+代码，深交所 secid=`0.`+代码
- 偶尔也失败（和AKShare同一通道），且近期有变慢/无响应趋势

## 不可用数据源 ❌

### 百度财经 `finance.baidu.com`
- 2026-06-02测试：`https://finance.baidu.com/stock/ab-300308` 返回HTTP 403
- 即使加上完整浏览器User-Agent、Accept、Referer头，仍然403
- 疑似WAF拦截非浏览器请求

### 网易 `quotes.money.163.com`
- 2026-06-02测试：`/service/chddata.html?code=0603019` 返回HTTP 502

### AKShare 利润表/资产负债表
- `stock_profit_sheet_by_report_em()` 和 `stock_balance_sheet_by_report_em()` 返回None

## 数据获取优先序

当需要个股K线/基本面数据时：

```
① 新浪实时 hq.sinajs.cn ✓（最快，仅限当日）
② 新浪K线 money.finance.sina.com.cn ✓（日K+均线，推荐）
③ AKShare stock_yjbb_em ✓（年度营收/利润汇总）
④ 东方财富 push2 API ❗（不稳定，回退选项）
```
