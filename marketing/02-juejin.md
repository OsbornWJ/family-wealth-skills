# 掘金稿 · 可直接发

**封面：** `images/fw-cover-16x9-cn-title.png`  
**插图顺序：** 安装 → 出手前先问 →（可选）监控竖图  
**标签：** AI、Cursor、Agent、开源、个人理财  

**标题选一：**
1. 我给 Cursor 装了一套「先问哪笔钱」的理财 Skill，不是荐股机器人  
2. 开源 Family Wealth Skills：一条命令安装，家庭约定 + A 股盯盘脚本  
3. 拖延症患者自用：Agent 出手前先问清楚，家底和日报都在对话里

> 文风参考过我之前一篇流水账：[来自 2022 的总结，拖延症害死人](https://juejin.cn/post/7208050893055787063)。能白话就白话。  
> **本文不荐股。** 不讨论买什么票。

---

## 正文

### 先吐槽两句

自己炒点 A 股，也管家里钱。最烦 AI 两件事：

1. 一开口就「建议加仓某某」，根本不问这是吃饭的钱还是闲钱  
2. 每天盯盘要手抄行情，懒得再开一个网页看板

所以我把平时用的流程收成一套开源 Skill：**Family Wealth Skills**。  
装进 Cursor / Claude / Hermes 这类能挂 Skill 的客户端，跟它说话时，它会先问「这是哪笔钱」，再谈别的。

仓库：https://github.com/OsbornWJ/family-wealth-skills · MIT

### 它干啥 / 不干啥

干三件事：

1. **出手前先问清楚** — 哪笔钱、应急金够不够、股票会不会买太多  
2. **家底表** — 本地 Markdown 记资产负债，对话里表格看  
3. **A 股助手** — 早盘 / 尾盘 / 日报脚本，固收、收息、研究流程（数字你自己填）

不干这些：

- 不当持牌投顾，不荐股，不保证收益，不替你下单  
- 不做 Web 仪表盘（故意的，保持「一条命令装上就能聊」）  
- 行情和产品默认服务 **A 股 / 人民币**；美股账户别指望开箱即用  

![安装](images/fw-spot-install.png)

### 里面有啥（扫一眼就行）

| Skill | 干嘛的 |
|------|--------|
| `family-wealth-ips` | 能不能买：哪笔钱 / 应急金 / 仓位 |
| `personal-financial-tracker` | 家底表 |
| `a-share-daily-monitor` | 早盘、尾盘、日报 |
| `a-share-bond-allocation` | 债、储蓄国债、现金停靠 |
| `a-share-dividend-allocation` | 收息怎么选（规则，不是喊单） |
| comps / dcf / earnings | 研究框架 |
| `akshare-china-finance` | 免费行情：腾讯 → 新浪 → 可选 mootdx |

### 三条命令

```bash
# 装上
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash

# 填砸了，本地数字清回示例（自动备份）
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash

# 不想要了
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash
```

要用监控脚本再装：

```bash
pip3 install requests pandas akshare baostock
```

装完 **新开一轮对话**，直接说：

> 按 family-wealth-ips，先问清楚能不能买

提示输入 `yes`；嫌烦就加 `FAMILY_WEALTH_YES=1`。

![出手前先问](images/fw-spot-ips-gate.png)

### 有空再填的三个文件

都在 `~/.family-wealth-skills/` 下面：

- `family-wealth-ips/assets/ips.local.md` — 月支出、钱池、配比  
- `personal-financial-tracker/assets/balance-sheet.local.md` — 家底  
- `a-share-daily-monitor/assets/portfolio.local.json` — 持仓和成本  

这些是你家底，**别推进公开仓库**。没有 local 时，监控会先用 example，跑得通，但别当真。

### 跟 AI 怎么说话

别一上来：「515980 加不加。」

可以照着说：

1. 「按 family-wealth-ips：这是哪笔钱？应急金够吗？股票会不会买太多？」  
2. 「根据家底表，净资产和股票类大概占多少」  
3. 再按需：保本 → bond；收息 → dividend；盯盘 → monitor  

它最好回你一行：`能不能买: 可以 / 先少买点 / 先别买`。  
写了「先别买」还甩下单清单——那叫装瞎。

### 盯盘三条

```bash
cd ~/.family-wealth-skills/a-share-daily-monitor
python3 scripts/morning_check.py
python3 scripts/pre_close_check.py
python3 scripts/daily_monitor.py
```

东财挂了属正常，看返回里的 `source=`，换网或等会儿。

更细的说明、演示对话、实跑样例在仓库 `docs/USAGE.zh.md` 和 `examples/`。

### 写在最后

不构成投资建议。数据会延迟、会挂。  
行动力往往比嘴上功夫重要——想到要装，把上面那条 `curl` 跑了就行。
