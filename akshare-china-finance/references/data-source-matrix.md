# 免费无 Key 行情源矩阵与降级

默认路径**不需要 API Key**。禁止把 tushare / 问财等需 Key 的源写成默认依赖。

## 实时价优先级

| 优先级 | 源 | 端点 / 方式 | 用途 |
|:---:|:---|:---|:---|
| 1 | 腾讯财经 | `http://qt.gtimg.cn/q=sh601939` | 个股/ETF/指数实时 |
| 2 | 新浪财经 | `https://hq.sinajs.cn/list=sh601939`（需 Referer） | 兼容备胎；批量加 sleep |
| 3 | mootdx（可选） | 通达信 TCP 7709 | 未安装则跳过 |
| 末位 | 东财 / AKShare | 各 hist / push2 | 仅独有数据；易 RemoteDisconnected |

统一入口：`scripts/quote_providers.py` → `get_realtime(codes)`，返回字段含 `source`。

## 日 K / 历史

| 优先级 | 源 | 说明 |
|:---:|:---|:---|
| 1 | baostock | 免费登录协议，无个人 Key；`pip install baostock` |
| 2 | mootdx | 可选 |
| 3 | 新浪 K 线 | `money.finance.sina.com.cn/.../getKLineData`（字段名 `day`） |
| 4 | AKShare | `stock_zh_a_hist` 等，东财挂了即放弃 |

入口：`get_daily_bars(code, n)`。

## 东财 / AKShare 仍可用的独有类

- 分红明细 `stock_history_dividend_detail`（注意派息÷10）
- 部分资金流 / 北向 / 申万行业（失败则注明缺失，不编造）

## 降级铁律

1. 实时价：**腾讯优先，失败再新浪**；不要「必须用新浪」。
2. AKShare / 东财重试 ≤2 次，然后换源。
3. 输出报告时标注或可追溯 `source=`，便于排障。
4. 永不默认依赖需 Key 的商业源。

## 冒烟

```bash
python3 scripts/quote_providers.py
# 期望：建行/ETF/上证 打出 tencent 或 sina 非空现价
```
