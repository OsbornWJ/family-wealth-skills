---
name: a-share-daily-monitor
description: Use when 用户要早盘/盘中/尾盘/日报、大盘分析或问今天有没有操作。A股持仓四节点监控与触发检查。
license: MIT
compatibility: Requires Python 3, requests, akshare; network for Tencent/Sina quotes.
metadata:
  author: stunner
  version: "1.37.0"
  tags: "a-share,monitoring,etf,portfolio,akshare"
  hermes_related: "family-wealth-ips,a-share-stock-fundamental-analysis,a-share-dividend-allocation,a-share-active-disclosure"
  openclaw: '{"requires":{"bins":["python3"]}}'
---

# A股每日监控

**定位：** 交易弹药层的执行与监控。配置建议、动用家庭固定资本/配偶本金、提高权益占比 → 必须先用 `family-wealth-ips` 问清楚能不能买（输出「可以/先少买点/先别买」）。先别买时只出监控数据，**不下单指令**。

四节点监控管线（交易日）。OpenClaw 用 `{baseDir}`；其它运行时用本 skill 目录绝对路径。
| 时间 | 节点 | 脚本 | 聚焦 |
|:----|------|------|------|
| 10:30 | 早盘 | `scripts/morning_check.py` | 开盘形态、北向、早盘触发 |
| 盘中 | 盘中 | 手动：合并 morning + pre_close | 全持仓+触发+午后预警 |
| 14:35 | 尾盘 | `scripts/pre_close_check.py` | 止盈逼近、单日暴跌 |
| 15:45 | 日报 | `scripts/daily_monitor.py` | 全量（AKShare 日线可能 T-1，实时源兜底） |
| 盘中 | 大盘 | 见 `references/output-formats.md` | 六大指数+申万 Top5+风格轮动 |

## 运行方式

```bash
# 从本 skill 目录：
python3 scripts/morning_check.py
python3 scripts/pre_close_check.py
python3 scripts/daily_monitor.py
# 或 scripts/run_morning.sh | run_mid.sh | run_daily.sh
```

持仓成本从 `assets/portfolio.local.json`（若无则用 `portfolio.example.json`）加载；勿把实盘成本写进仓库。Hermes cron 同步见 `references/runtime-hermes.md`（私有部署说明）。

## 响应铁律

0. **买卖前先问清（涉及操作时）**：标明钱池=交易弹药（默认）；若用户指向家庭/配偶钱 → 停，转 `family-wealth-ips`。授权执行**不能**绕过家庭固定资本禁投。加仓后须自检股票类占比不超过约定上限（见 `family-wealth-ips/assets/ips.local.md`）。
1. **报告直接贴在对话里**，禁止只说「报告已生成」。
2. 「早盘分析」→ 直接跑 `morning_check.py` 输出，不改 cwd、不绕到其它项目。
3. 「盘中分析」→ 合并 `morning_check.py` + `pre_close_check.py` 输出。
4. 「日报/盘后」→ `daily_monitor.py`；指数/现价用**实时源**校验（腾讯优先，失败新浪；见 `akshare-china-finance`）。
5. **纠正后翻篇**：承认一次 → 修正数据 → 停止道歉循环。
6. **授权执行**（「请直接决策」「授权全权执行（可选偏好）」）→ 给单一完整方案，只问「要调吗？」；授权执行则连确认也不问——但仍受铁律 0 约束。
7. **输出前验证清单**：大盘/ETF/个股现价用实时源；持仓浮盈用确认价+成本重算；不盲信脚本内 T-1 指数。
8. **单字/晚安**：用户连续 2 轮极简/晚安后第 3 轮起零输出。
9. **快速轮动**：「XX呢」模式 → 每标的 1 行数据 + 1 句判断。
10. **只问一次**：关键数字问一次无答 → 给公式/通用方案翻篇。

## 数据采集（4 步）

1. **大盘** — 实时源指数（上证/科创50/深证）；勿把成交量股数当成交额。
2. **持仓价与 MA** — ETF 净值/日线 + 实时价；算 MA 偏离与峰值回撤。
3. **资金/折溢价** — 可用则拉；东财挂了就跳过并注明。
4. **外部变量** — 美债利率、宏观日历（日期用系统 `date` 确认）。

### 「今天有需要操作的吗」

按 🟢不操作 / 🟡可观察 / 🔴建议行动 分组；每项含成本、浮盈%、距触发%。末尾一句话策略。FOMO（「心疼/踏空」）用数据消解，不情感安慰。细则与早盘「今日可操作一览」见历史会话模式；场景库 `references/scenarios.md`。

## 场景索引（按需读 references/scenarios.md）

| 场景 | 触发 |
|:---|:---|
| L 大跌定投 | 中等跌幅补条件单盲区 |
| M / H3 下跌诊断 | 用户质疑「为什么跌」 |
| N 操作信号 | 「有机会吗」「需要操作吗」 |
| P 复盘 | 月度/当日操作复盘 |
| I/J/K/O | 加仓诊断、大反弹、底部抬升、恐慌信号 |
| A–G / E专项 | 急跌、ASCO、核心卫星、高浮盈加仓、板块雷达等 |

## 参考文件

- `references/scenarios.md` — 场景全文
- `references/traps.md` — 陷阱全文（持仓名单语义、T-1、限流等）
- `references/output-formats.md` — 日报/尾盘/大盘/盘中格式
- `references/runtime-hermes.md` — Hermes cron / 禁邮件
- `assets/portfolio.local.md` — 标的快照（会过期）
- `references/portfolio-scoring-framework.md` — 持仓评分
- `references/mid-session-template.md` — 盘中模板
- `references/dip-dca-*.md` / `tiered-buy-point-framework.md` 等 — 定投与买点
- 同目录其它 `references/*.md` — 宏观、轮动、锁利等

## 相关技能

- `family-wealth-ips` — 家庭理财约定（买卖前先问清能不能买）
- `personal-financial-tracker` — 家庭资产负债表 / 应急金
- `a-share-stock-fundamental-analysis` — 个股研究
- `a-share-dividend-allocation` — 收息层配置
- `a-share-active-disclosure` — 重大事件主动说
- `` — 会话纠正档案
- `akshare-china-finance` — 行情源与降级

## 陷阱（摘要）

完整列表：`references/traps.md`。

- 「之前止盈」≠ 已清仓；以脚本 `COST_PRICE` 为活跃持仓真相源。
- 东财/AKShare 易断 → 腾讯/新浪实时，重试 ≤2。
- 新浪批量限流 → `sleep`；优先腾讯批量。
- 实时价不得用记忆替代。
