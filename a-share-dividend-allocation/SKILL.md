---
name: a-share-dividend-allocation
description: Use when 用户问股息率、银行/红利ETF对比、收息层配置或清仓后现金怎么分。四标准筛选+分散配置+大跌触发买入。
license: MIT
compatibility: Requires Python 3, requests, akshare; network for Tencent/Sina quotes.
metadata:
  author: stunner
  version: "1.1.0"
  tags: "a-share,dividend,income,allocation,bank,etf"
  hermes_related: "family-wealth-ips,a-share-daily-monitor,a-share-bond-allocation,a-share-stock-fundamental-analysis"
  openclaw: '{"requires":{"bins":["python3"]}}'
---

# A股收息资产选择与配置

**IPS：** 清仓后现金分配、加大收息层前，先问 `family-wealth-ips`（哪笔钱 + 应急金 + 目标配比）。本 skill 只解决「收息层买什么」。

## When to Use

- 用户问「XX股息率多少」「每年分红稳定吗」「哪个银行性价比高」
- 清仓后问「现金怎么分配/配置」「红利出来了钱放哪」
- 想加收息仓（银行 / 红利ETF / 收息个股）
- 明确说「不想都放一个银行股」

**Don't use for:** 纯债/债基/储蓄国债 → `a-share-bond-allocation`；日常持仓监控 → `a-share-daily-monitor`。

## 用户偏好（硬约束）

- 拒绝高一手门槛个股收息（美的/伊利等默认不推）
- **一手 <¥1,100 + 单日波动 <±1.5% + 股息率 >4% + 分红连续**
- 分散：不把红利清仓款全押一个银行
- 优先：红利低波 ETF > 银行股 > 收息个股（个股仅用户主动要弹性时）
- 等一次大跌一次性买入，不追反弹高位

## 筛选四标准

| 标准 | 阈值 | 说明 |
|:---|:---|:---|
| 一手成本 | <¥1,100 | 心理+资金利用率 |
| 单日波动 | <±1.5% | 求稳 |
| 股息率 | >4% | 收息目的 |
| 分红连续性 | 上市至今不断 | 用数据验证，不凭印象 |

## 数据获取

实时价（优先腾讯，失败再新浪；见 `akshare-china-finance`）：

```python
# 腾讯: http://qt.gtimg.cn/q=sh601939
# 新浪: https://hq.sinajs.cn/list=sh601939  (Referer: https://finance.sina.com.cn)
```

分红历史：

```python
import akshare as ak
df = ak.stock_history_dividend_detail(symbol='601939', indicator='分红')
# 派息字段单位=每10股 → 每股年分红需 /10
```

ETF 分红：`ak.fund_fh_em(year='2025')`（按年拉取，慢，加 timeout）。

## 银行股息率速查（表内价格会过期——出口前必须拉实时价）

| 银行 | 参考股息率区间 | 一手量级 | 分红连续 | 默认 |
|:---|:---:|:---:|:---:|:---|
| 招商银行 | 高 | 一手偏贵 | 长 | 常因一手否决 |
| 工商银行 | ~4%+ | 低 | 长 | 优先 |
| 中国银行 | ~4% | 低 | 长 | 可选 |
| 建设银行 | ~4% | ~千元 | 长 | 常已有底仓 |
| 农业银行 | ~4% | 低 | 长 | 可选 |

## 红利 ETF

| ETF | 角色 | 注意 |
|:---|:---|:---|
| **512890 红利低波** | 主力收息工具 | 一手便宜、波动低 |
| 562060 标普红利 | 旧仓/对比 | 分红曾大幅缩水；勿与 512890 混码 |

**代码雷区：** 512890（价量级 ~1.x）vs 562060（~0.6x）名称都含「红利」。报价格前必须实时核实。

## 配置框架（全仓视角示例）

| 层级 | 占比量级 | 说明 |
|:---|:---:|:---|
| 进攻（芯片+AI） | ~25% | 弹性 |
| 收息（银行+红利低波） | ~25% | 年分红目标 ~4%+ |
| 观察（军工等） | ~5% | 纪律减仓/观察 |
| 现金安全垫 | ~35% | 等宏观确认 |
| 场外收息 | ~10% | 债基等 → bond skill |

收息层金额示例见 `references/dividend-asset-selection.md`；个股尽调见 `references/stock-due-diligence-2026-08.md`。

## 大跌触发买入（4 信号任一 + 价格到位）

| 信号 | 典型触发 |
|:---|:---|
| 上证单日暴跌 | <-2% |
| CPI 等宏观超预期差 | 以当日日历为准，先 `date` 确认 |
| 建行跌破约定买点 | 股息率抬升区 |
| 科创 50 二次探底 | 风险偏好冰点 |

**兜底：** 长期无大跌则设截止日期手动建仓，防无限等待。触发前资金趴现金。

建行 MA60 回测买点、长江电力等进攻型收息补充 → `references/dividend-asset-selection.md`。

## 执行纪律

1. 不追现价；宏观事件前可挂 -1~2%
2. 个股收息除非用户主动要弹性，否则推 ETF/银行
3. 涉及挂单价/股息率：**先拉实时价再出口**
4. 宏观事件日期用系统日期确认，不靠记忆

## 输出格式

银行对比：

```
| 银行 | 股价 | 年分红/股 | 股息率 | 一手 | 分红连续性 |
```

换仓：给多标的分配比例 + 加权股息率 + 年分红金额，不要只给二选一。

## 陷阱

1. akshare「派息」= 每 10 股，算股息率必须 /10
2. 东财通道易挂 → 转腾讯/新浪实时，AKShare 重试 ≤2 次
3. 「稳定分红」= 年年有 **且** 金额不大幅缩水
4. 512890 / 562060 混码会直接污染挂单
5. 不 all-in 单一银行
