---
name: personal-financial-tracker
description: Use when 用户要家庭总资产、资产负债表、净资产、应急金月数，或场外基金/积存金/现金记账。
license: MIT
compatibility: Requires Python 3, requests, akshare for fund/gold marks. No API keys.
metadata:
  author: stunner
  version: "1.1.0"
  tags: "personal-finance,family-balance-sheet,fund-account,gold,wealth-management"
  hermes_related: "family-wealth-ips,a-share-daily-monitor,a-share-bond-allocation"
  openclaw: '{"requires":{"bins":["python3"]}}'
---

# 家庭资产负债表与个人金融资产追踪

在 `family-wealth-ips` 之下提供**全账户净值视图**。A 股场内持仓数据来自 `a-share-daily-monitor`；本 skill 负责场外+现金+黄金+固收+（可选）房产/负债登记，并合并出家庭金融净资产。

**权威快照：** [`assets/balance-sheet.local.md`](assets/balance-sheet.local.md)（与 IPS 的 `assets/ips.local.md` 配合使用）。

## When to Use

- 「总资产」「家底」「净资产」「应急金够不够」
- 更新场外基金 / 积存金 / 理财 / 现金
- 「能不能买」检查需要占比、应急金月数时

## 工作流（先表后建议）

1. 读 `assets/balance-sheet.local.md` + IPS `assets/ips.local.md`
2. 拉场外净值 / 金价（API 见下）；场内市值问用户或从 monitor 脚本成本+现价估算
3. 输出「家庭资产负债表」模板（见下）→ 算出金融净资产、层级占比、应急金月数
4. **任何买卖建议** → 交回 `family-wealth-ips` 先问清能不能买，本 skill 不单独下单

完成标准：表内资产合计 − 负债 = 净资产；应急金月数有数；与 IPS 目标配对比有一句偏离说明。

## 家庭资产负债表模板

```
=== 家庭资产负债表（日期）===

【流动安全垫】
现金/活期/货基          … 元
短债/可快赎固收         … 元
小计 / 月支出 = 应急金 X 个月（目标 6）

【家庭固定资本】（保本池，分列）
储蓄国债/定存/配偶本金   … 元

【蓄水池固收】
债基等（存量）           … 元

【收息层】
银行股/红利低波等        … 元（可与 A 股合并注明）

【进攻/权益】
A股 ETF/个股（场内）     … 元  ← 来自 daily-monitor
偏股/QDII 场外           … 元

【其它】
积存金/黄金              … 元
观察仓/其它              … 元

【负债】（若有）
房贷/消费贷/其它         … 元

金融净资产 = 资产合计 − 负债
层级占比：进攻 a% | 收息 b% | 固收+现金 c% | 其它 d%
vs IPS：偏离 … → 再平衡建议交回理财约定 skill
```

房产等非金融不动产：可单列「参考项」，**默认不计入**金融净资产占比（除非用户要求「总家产」口径并注明）。

## 场外资产数据源

| 类型 | 示例 | 来源 |
|------|------|------|
| 场外基金 / QDII | 中欧红利、中概联接 | `ak.fund_open_fund_info_em(代码, '单位净值走势')` |
| 积存金 | 克数×金价 | `ak.spot_golden_benchmark_sge()`（元/克，常 T-1） |
| 养老理财等 | | 手动录入 |
| 现金 | | 手动录入 |
| A 股场内 | ETF/个股 | `a-share-daily-monitor`（勿混进该 skill 日报正文） |

反算：`成本 = 市值 − 盈亏`；积存金成本/克 = `(市值 + 亏损) / 克数`。

### 账户总览（子集报表）

```
=== 账户总览 ===
名称                         市值         盈亏        收益率
------------------------------------------------------------
…
合计                         …元         …元         …%
```

问「总资产」时：合并 A 股部分 + 本表部分，标注来源，防现金重复计算。

## 已知基金代码

| 基金名称 | 代码 | 类型 |
|---------|------|------|
| 中欧红利优享灵活配置混合C | 012248 | 场外红利 |
| 易方达中概互联网ETF联接C | 006328 | QDII |
| 易方达中概互联网ETF联接A | 006327 | QDII |
| 招商双债增强C | 161716 | 家庭固收蓄水池 |
| 平安6个月瑞尚 | 005750 | 短债蓄水池 |

## 蓄水池债基策略

| 产品 | 策略 |
|:----|:-----|
| 招商双债 / 平安瑞尚 | 存量不动收息；增量要不要进股票 **先问清能不能买** |

利率地板位时长久期加仓见 `a-share-bond-allocation`，且家庭固定资本优先储蓄国债。

## 积存金与计价

详见 `references/gold-conversion.md`。用户说「黄金 X」先确认 **$/oz 还是 元/g**。

```
市值 = 克数 × 上海金基准价(元/克)
RMB/g ≈ USD/oz ÷ 31.1035 × 汇率
```

仓位占比过高（如黄金 > 金融净资产 30%）→ 建议减至合理，而不是亏损中加仓。

## 家人/配偶持仓

| 维度 | 自有组合 | 家人持仓 |
|:----|:---------|:---------|
| 决策权 | 自决 | 建议权 |
| 心理 | 纪律 | 亏损影响关系 |
| 场外 | 可条件单（场内） | 常无条件单，T+2 |

输出用「家人持仓分析」格式；补仓默认定投方案；**必须标明：这是家人名下的钱**。

## 陷阱

1. 基金/金价列名中文；净值常 T-1。
2. 现金与 A 股可用资金重复计入。
3. 「总资产」未扣负债、未分钱池 → 占比失真。
4. 未更新 `balance-sheet.local.md` 就报精确净资产。
5. 本 skill 不问清楚就直接下单。

## 相关技能

- `family-wealth-ips` — 出手前先问清楚
- `a-share-daily-monitor` — 场内监控
- `a-share-bond-allocation` / `a-share-dividend-allocation` — 固收与收息产品

## 参考

- `assets/balance-sheet.local.md` — 本地资产负债快照
- `references/gold-conversion.md` — 黄金换算
