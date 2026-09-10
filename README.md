# Family Wealth Skills

[中文说明](#中文) · [Usage (使用说明)](docs/USAGE.zh.md) · [English usage](docs/USAGE.en.md) · [Privacy](PRIVACY.md) · [Contributing](CONTRIBUTING.md)

**AgentSkills** pack for **family wealth governance** + **China A-share execution helpers**.

> **Scope:** IPS / balance-sheet frameworks are general. Market data, products, and trading rules are **China A-share (CNY) focused**. Not a drop-in toolkit for US/EU brokerage workflows.

This is a **sanitized public export** — no live portfolios, session diaries, or personal account snapshots.

---

## 中文

### 这是什么 / 不是什么

| 是 | 不是 |
|----|------|
| 给 AI Agent 用的流程与脚本（[AgentSkills](https://agentskills.io)） | 持牌投顾、荐股软件 |
| 家庭 IPS 闸门 + 资产负债表模板 | 保证收益或代客理财 |
| A 股监控 / 收息 / 固收 **执行助手**（需你自己填本地配置） | 全球多市场一体化交易系统 |
| 对话里用 Markdown 表看资产盘 / 闸门结果 | **Web 看板 / HTML 仪表盘**（本仓库不提供） |

资产视图请在对话中让 Agent 按 IPS / 资产负债表输出表格；或自行用 `*.local.*` 对接其它工具。本仓库**故意不做**图形化网页，以保持一条命令安装的 Skill 定位。

### 谁适合用

- 主要投资 **中国 A 股 / 场内 ETF / 人民币固收**，并用 Cursor、Claude Code、Hermes、OpenClaw 等支持 Skill 的 Agent
- 希望 Agent **先问钱池与风险预算，再谈标的**

海外用户可借鉴 IPS 与资产负债表；行情脚本与产品规则默认只服务中国市场。

### 安装（一条命令）

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
```

会克隆到 `~/.family-wealth-skills`，并自动链到 Cursor / Claude Code。然后：

```bash
pip3 install requests pandas akshare baostock   # 要用行情脚本时再装
```

**新开一轮对话**，直接说：「按 family-wealth-ips 过闸」。

可选：改 `~/.family-wealth-skills/**/assets/*.local.*` 填自己的钱池/持仓。  
完整说明：[docs/USAGE.zh.md](docs/USAGE.zh.md) · 演示：[examples/demo-conversation.zh.md](examples/demo-conversation.zh.md)

### Skill 地图

| Skill | 用途 |
|-------|------|
| `family-wealth-ips` | **总闸门**：钱池 / 应急金 / 风险预算 |
| `personal-financial-tracker` | 家庭资产负债表 |
| `a-share-daily-monitor` | 早盘/盘中/尾盘/日报 |
| `a-share-bond-allocation` | 债 / 储蓄国债 / 现金停靠 |
| `a-share-dividend-allocation` | 收息层筛选 |
| `a-share-comps-analysis` / `dcf` / `earnings` | 研究框架 |
| `a-share-strategy-playbook` | 交易纪律（示例） |
| `a-share-active-disclosure` | 重大事件主动披露 |
| `akshare-china-finance` | 免费无 Key 行情源与降级 |

### 免责声明

不构成投资建议。数据源可能延迟或失败。本地 `*.local.*` 含个人财务信息，**不要推送到公开仓库**（见 [PRIVACY.md](PRIVACY.md)）。

---

## English

### What this is / is not

| Is | Is not |
|----|--------|
| [AgentSkills](https://agentskills.io) workflows + scripts | Licensed financial advice |
| Family IPS gate + balance-sheet templates | Return guarantee |
| **China A-share** monitor / dividend / bond helpers | Global multi-broker trading suite |
| Portfolio views as Markdown tables in chat | **Web dashboard / HTML UI** (not shipped) |

Ask the agent for IPS / balance-sheet tables in conversation, or wire your own tools to `*.local.*`. This repo intentionally has **no** graphical web UI.

### Audience

Users who invest mainly in **China A-shares / CNY fixed income** and run skill-capable agents (Cursor, Claude Code, Hermes, OpenClaw, …).

IPS ideas travel; quote APIs and product rules do **not** auto-work for US/EU accounts.

### Install (one liner)

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
pip3 install requests pandas akshare baostock   # only if you need quote scripts
```

Start a **new** agent chat. Full guide: [docs/USAGE.en.md](docs/USAGE.en.md).

### Disclaimer

Not investment advice. Keep `*.local.*` private. See [PRIVACY.md](PRIVACY.md).

## License

[MIT](LICENSE)
