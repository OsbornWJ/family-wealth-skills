# AKShare API 可用性验证（2026-05-20）

## ✅ 已验证可用

| API | 用途 | 备注 |
|-----|------|------|
| `stock_zh_index_daily(symbol='sh000001')` | 上证指数 | volume 是成交股数，非成交额 |
| `stock_zh_index_daily(symbol='sh000688')` | 科创50 | — |
| `stock_zh_index_daily(symbol='sz399001')` | 深证成指 | — |
| `fund_open_fund_info_em(symbol, indicator='单位净值走势')` | ETF净值历史 | 可用于MA计算 |
| `fund_etf_fund_daily_em()` | ETF资金流 | 含当日市价、NAV、折溢价 |
| `bond_zh_us_rate()` | 中美利差 | 含美10Y/中10Y |
| `index_hist_sw(symbol='801xxx', period='day')` | 申万行业指数 | 801950=煤炭, 801180=地产, 801790=非银金融等，日期列需 `pd.to_datetime` 转换 |

## ❌ 不可用（本机连接问题 / API不存在）

| API | 错误 | 替代方案 |
|-----|------|---------|
| `fund_etf_hist_em` | RemoteDisconnected | 用 `fund_open_fund_info_em` 获取净值历史 |
| `stock_zh_a_hist` | RemoteDisconnected | 用新浪 `hq.sinajs.cn` 获取实时行情 |
| `stock_zh_a_spot_em` | RemoteDisconnected | 同上 |
| `index_zh_a_hist` | RemoteDisconnected | 用 `stock_zh_index_daily` |
| `stock_board_industry_summary_em()` | ❌ 本版本不存在此API | 用 `index_hist_sw` 替代 |
| `stock_sector_fund_flow_rank()` | RemoteDisconnected | 行业资金流暂不可用，用ETF净值偏离+指数涨跌替代 |

## 新浪财经实时行情格式

URL: `https://hq.sinajs.cn/list=sh601939`
Headers: `Referer: https://finance.sina.com.cn`

返回字段（逗号分隔）：
```
0:名称, 1:今开, 2:昨收, 3:最新价, 4:最高, 5:最低,
6:买一, 7:卖一, 8:成交量(股), 9:成交额(元), ...
30:日期, 31:时间
```

## 成交额估算

`stock_zh_index_daily` 的 volume 字段为成交股数（非元）。
全市场估算成交额 = (上证成交量 + 深证成交量) × 均价估算(~8元) / 1e8
精确值需从其他数据源获取。
