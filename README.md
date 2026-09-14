# Family Wealth Skills

[中文](#先说人话) · [使用说明](docs/USAGE.zh.md) · [English](#english) · [隐私](PRIVACY.md)

给 Cursor / Claude / Hermes 用的 **家庭理财 + A 股执行** Skill 包。  
装上之后，你跟 Agent 说话，它会先问「这是哪笔钱」，再谈买不买——而不是一上来报代码荐股。

> 行情和产品规则默认服务 **中国 A 股 / 人民币**。IPS、家底表那套想法可以借鉴，美股账户别指望开箱即用。

---

## 先说人话

我自己炒股、也管家里钱，最烦两件事：

1. Agent 一开口就「建议加仓芯片」，根本不问这是吃饭的钱还是闲钱  
2. 每天盯盘要手抄一堆行情，懒得开网页看板

所以这个包干两件事：**出手前先问清楚**，以及 **早盘/尾盘/日报一条命令跑完**。  
没有 Web 仪表盘——就是对话里表格，故意做成「一条命令装上就能聊」。

**适合谁：** 主要玩 A 股 / 场内 ETF / 人民币固收，又愿意让 Agent 帮你盯纪律的人。  
**不适合谁：** 想要持牌投顾、保证收益、全球多券商一键下单的——这里没有。

---

## 三条命令搞定

```bash
# 装上（链到 Cursor / Claude）
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash

# 填砸了？本地数字清回示例（自动备份，技能还在）
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash

# 不想要了？整包卸掉
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash
```

提示输入 `yes` 就行。嫌烦就加：`FAMILY_WEALTH_YES=1`。

要用行情脚本再装依赖（可后装）：

```bash
pip3 install requests pandas akshare baostock
```

装完 **新开一轮对话**，直接说：

> 按 family-wealth-ips，先问清楚能不能买

有空再改 `~/.family-wealth-skills/**/assets/*.local.*` 里的真实数字。  
怎么聊、怎么跑监控：[使用说明](docs/USAGE.zh.md) · [演示对话](examples/demo-conversation.zh.md) · [实跑样例](examples/scenario-monitor-2026-09-11.zh.md) · [发文稿](marketing/)

---

## 里面有啥

| Skill | 干嘛的 |
|-------|--------|
| `family-wealth-ips` | 能不能买：哪笔钱 / 应急金 / 股票会不会买太多 |
| `personal-financial-tracker` | 家底表 |
| `a-share-daily-monitor` | 早盘、尾盘、日报 |
| `a-share-bond-allocation` | 债、储蓄国债、现金停靠 |
| `a-share-dividend-allocation` | 收息怎么选 |
| `a-share-comps-analysis` / `dcf` / `earnings` | 个股研究框架 |
| `a-share-strategy-playbook` | 交易纪律（示例） |
| `akshare-china-finance` | 免费行情，腾讯→新浪→可选 mootdx |

不是投资建议。数据源会挂、会延迟。`*.local.*` 是你的家底，**别推到公开仓库**。

---

## English

AgentSkills pack for **family money rules** + **China A-share helpers**.  
Install, then ask the agent to check “can I buy?” before ticker talk. No web dashboard on purpose.

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash
```

Quotes and products are **A-share / CNY** focused. IPS ideas travel; US brokerage workflows do not.  
Not investment advice. Keep `*.local.*` private. See [USAGE.en.md](docs/USAGE.en.md) · [PRIVACY.md](PRIVACY.md).

## License

[MIT](LICENSE)
