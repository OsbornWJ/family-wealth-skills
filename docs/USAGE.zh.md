# 使用说明

给谁看：自己管钱、主要玩 **A 股**，又想让 Agent 帮着盯纪律的人。

这不是网页看板。家底、能不能买、盈亏，都在对话里用表格看。嫌麻烦？那正好——装完就能聊。

文风参考过我写过的一篇流水账：[来自 2022 的总结，拖延症害死人](https://juejin.cn/post/7208050893055787063)——能白话就白话，能一条命令就不整七步流程。

---

## 你需要啥

- Python 3.9+（3.10 更香）
- 能上网（腾讯/新浪公开行情，**不用 API Key**）
- Cursor / Claude Code / Hermes / OpenClaw 这类能挂 Skill 的客户端

行情脚本依赖（用到再装）：

```bash
pip3 install requests pandas akshare baostock
# 可选
pip3 install mootdx
```

---

## 装 / 重置 / 卸：各一条

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash
```

装完会放到 `~/.family-wealth-skills`，并链到 Cursor / Claude。  
第一次会从 example 拷一份 local（已有的不覆盖）。  
重置会自动备份；卸载会把目录和链接一起清掉。  
确认时输入 `yes`；或 `FAMILY_WEALTH_YES=1` 直接过。

**重要：** 装完请 **新开一轮对话**，否则旧会话可能还找不到 skill。

自己 `git clone` 也行，但不如上面那条省事。Hermes / OpenClaw 把各 skill 目录链到它们的 skills 根就行。

---

## 本地数字（有空再填）

| 文件 | 填啥 |
|------|------|
| `.../family-wealth-ips/assets/ips.local.md` | 月支出、钱池、配比 |
| `.../personal-financial-tracker/assets/balance-sheet.local.md` | 家底粗表 |
| `.../a-share-daily-monitor/assets/portfolio.local.json` | 持仓、成本、峰值 |

路径前缀都是 `~/.family-wealth-skills/`。

示例组合默认关掉「必须减仓」硬警报，免得演示数据天天吓人。你自己实盘可以把 `enable_hard_sell_alerts` 打开。  
股息阈值写在 JSON 里（`annual_div` 那些），别直接抄别人的数。

监控脚本：有 `portfolio.local.json` 就用它，没有就用 example。

---

## 怎么跟 Agent 说话

别一上来：「帮我看看 515980 加不加。」

建议顺序：

1. **能不能买** — 「按 family-wealth-ips：这是哪笔钱？应急金够吗？股票会不会买太多？」  
2. **家底** — 「根据家底表，净资产和股票类大概占多少」  
3. **再干活**  
   - 保本 / 停靠 → `a-share-bond-allocation`  
   - 收息 → `a-share-dividend-allocation`  
   - 盯盘 → `a-share-daily-monitor`  
   - 研究个股 → comps / dcf / earnings  

Agent 最好甩你一行白话：`能不能买: 可以 / 先少买点 / 先别买`。  
写了「先别买」就别再给下单清单——那叫装瞎。

示例：[演示对话](../examples/demo-conversation.zh.md) · [2026-09-11 实跑](../examples/scenario-monitor-2026-09-11.zh.md)

---

## 日常盯盘

```bash
cd ~/.family-wealth-skills/a-share-daily-monitor   # 或仓库里同名目录
python3 scripts/morning_check.py
python3 scripts/pre_close_check.py
python3 scripts/daily_monitor.py
```

行情链路：腾讯 → 新浪 →（可选）mootdx。东财挂了属正常现象，换网或等会儿再试。

冒烟：

```bash
python3 akshare-china-finance/scripts/quote_providers.py
```

---

## 常见坑

**Agent 找不到 skill？**  
看 symlink、目录名、`SKILL.md` 的 `name`；新开会话。Cursor 别塞进内置的 `skills-cursor` 目录。

**行情空的？**  
免费源就是这样。看返回里的 `source=`，别一挂就怀疑人生。

**能直接管美股吗？**  
家底、能不能买可以借鉴；监控和产品默认只服务 A 股。美股自己接数据。

**「代操作少请示」？**  
个人口癖可以有，**绕过家里保本禁投**不行。

**隐私？**  
别把 `*.local.*` 和券商导出推进公开仓库。见 [PRIVACY.md](../PRIVACY.md)。

---

## 升级

再跑一遍安装命令，或在安装目录 `git pull`。symlink 一般不用动。脚本大改时，对照 `portfolio.example.json` 看看自己的 local 要不要补字段。
