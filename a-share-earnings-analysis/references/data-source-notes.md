# A股数据源有效性速查

本文件与 `a-share-daily-monitor/references/data-source-notes.md` 内容一致。核心要点：

## ✅ 可用
- **新浪实时行情** — `hq.sinajs.cn/list=sh600584`，批量50只，间隔0.3秒
- **新浪日K线** — `CN_MarketData.getKLineData?symbol=sh600584&scale=240&datalen=120`，字段: `day`, `open`, `high`, `low`, `close`, `volume`
- **AKShare财务摘要** — `stock_yjbb_em(date='20260331')`，列名全中文，需先`.columns.tolist()`
- **东方财富基金净值** — `fund_open_fund_info_em(symbol, indicator='单位净值走势')`，注意日期是字符串

## ❌ 不稳定/不可用
- **利润表/资产负债表API** — `*_by_report_em()` 全系列返回None，回退用 `stock_yjbb_em` 摘要+行业均值估算
- **东方财富ETF日K** — `fund_etf_hist_em` 可能 `RemoteDisconnected`，回退用新浪日K线
- **东方财富全市场行情** — `stock_zh_a_spot_em` 可能连接断开

## ⚠️ 陷阱
- 新浪K线字段名 `day` 不是 `date`
- 沪深代码前缀：6xx/688→sh, 0xx/3xx→sz
- Q1 EPS年化需×4, 强季节性行业偏差大
