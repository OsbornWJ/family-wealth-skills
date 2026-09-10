# 使用说明（中文）

面向：把本仓库当作 **Agent Skill 包** 使用的个人投资者（中国 A 股为主）。

**产品边界：** 本仓库是 Agent 流程与脚本，**不提供 Web 看板 / HTML 仪表盘**。家底、「能不能买」结论、持仓盈亏请在对话里用 Markdown 表查看；或自行用 `*.local.*` 对接其它工具。

## 1. 环境要求

- Python 3.9+（推荐 3.10+）
- 网络（访问腾讯 / 新浪等公开行情；无需 API Key）
- 支持 AgentSkills 的客户端之一：
  - [Cursor](https://cursor.com)（`~/.cursor/skills`）
  - Claude Code（`~/.claude/skills`）
  - Hermes / OpenClaw（把各 skill 目录链到其 skills 根目录）

依赖安装：

```bash
pip3 install requests pandas akshare baostock
# 可选：通达信 TCP
pip3 install mootdx
```

## 2. 安装 Skill（推荐：一条命令）

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
```

脚本会：

1. 克隆/更新到 `~/.family-wealth-skills`
2. 自动 symlink 到 `~/.cursor/skills` 与 `~/.claude/skills`
3. 若还没有 local 配置，从 example 复制一份（不覆盖已有）

**新开一轮对话** 后再用（多数运行时只在会话开始时加载 skill）。

### 手动安装（可选）

若你更想自己 clone：

```bash
git clone https://github.com/OsbornWJ/family-wealth-skills.git ~/.family-wealth-skills
# 然后对每个含 SKILL.md 的目录 ln -sfn 到 ~/.cursor/skills 与 ~/.claude/skills
# 或再次运行上面的 install.sh
```

Hermes / OpenClaw：把 `~/.family-wealth-skills` 下各 skill 目录链到对应 skills 根即可。

## 3. 本地配置（可后补）

安装脚本已生成空白/示例 `*.local.*`。有空再改真实数字即可（**不要推到公开仓库**）：

| 文件 | 填什么 |
|------|--------|
| `~/.family-wealth-skills/family-wealth-ips/assets/ips.local.md` | 月支出、钱池、目标配比 |
| `.../personal-financial-tracker/assets/balance-sheet.local.md` | 资产负债粗表 |
| `.../a-share-daily-monitor/assets/portfolio.local.json` | 监控标的、成本/峰值、股息假设 |

复制 `portfolio.example.json` 为 `portfolio.local.json` 后改真实数字。`settings.enable_hard_sell_alerts` 在 example 中默认关闭，避免演示组合误报「必须减仓」；本地实盘可设为 `true`。个股股息告警用 `annual_div` / `min_yield_pct` / `alert_on_low_yield`，勿把别人的阈值当自己的。

监控脚本优先读 `portfolio.local.json`，没有则用 example。

## 4. 推荐对话顺序（先问清 → 再执行）

1. **能不能买** — 「按 family-wealth-ips：这是哪笔钱？应急金够吗？股票会不会买太多？」
2. **家底** — 「根据家底表算净资产和股票类大概占多少」
3. **再分派**  
   - 家里保本 / 停靠 → `a-share-bond-allocation`  
   - 收息 → `a-share-dividend-allocation`  
   - 盘中买卖 / 日报 → `a-share-daily-monitor`  
   - 个股研究 → comps / dcf / earnings  

Agent 输出里应出现白话一行：`能不能买: 可以 / 先少买点 / 先别买`。「先别买」时不要给下单指令。

虚构完整对话：[examples/demo-conversation.zh.md](../examples/demo-conversation.zh.md)  
**真实脚本实跑**（2026-09-10 示例组合）：[examples/scenario-monitor-2026-09-10.zh.md](../examples/scenario-monitor-2026-09-10.zh.md)

重新抓取报告（会写到 `examples/_raw/`，勿提交含本机路径的原文）：

```bash
bash scripts/capture_example_run.sh
```

## 5. 日常监控命令

在 `a-share-daily-monitor` 目录下：

```bash
python3 scripts/morning_check.py      # 早盘
python3 scripts/pre_close_check.py    # 尾盘/盘中触发
python3 scripts/daily_monitor.py      # 日报
# 或
bash scripts/run_morning.sh
```

行情统一走 `akshare-china-finance/scripts/quote_providers.py`：  
**腾讯 → 新浪 →（可选）mootdx**；日 K：**baostock → … → AKShare 末位**。

冒烟：

```bash
python3 akshare-china-finance/scripts/quote_providers.py
```

## 6. 常见问题

**Q: Agent 找不到 skill？**  
A: 确认 symlink、目录名与 `SKILL.md` 里 `name` 一致；新开会话；Cursor 勿装到 `skills-cursor` 内置目录。

**Q: 行情报错 / 空数据？**  
A: 东财系常挂，属预期。看返回里的 `source=`；换网络或稍后重试。见 `akshare-china-finance/references/data-source-matrix.md`。

**Q: 能直接用于美股账户吗？**  
A: IPS/资产负债表可以借鉴；监控与产品 skill **默认只服务 A 股/人民币**。美股需自备数据源，不在本包范围。

**Q: 「代操作 / 少请示」？**  
A: 发布版把个人口癖收成可选偏好；**不能**绕过家庭固定资本禁投与 IPS 红灯。

**Q: 会不会泄露隐私？**  
A: 只要不把 `*.local.*` 和券商导出推进公开仓库即可。见 [PRIVACY.md](../PRIVACY.md)。

## 7. 升级

```bash
git pull
# 若用 symlink，一般无需重装；若脚本有 breaking change，对照 portfolio.example.json 更新 local
```

## 8. 卸载

删除 `~/.cursor/skills/<name>`、`~/.claude/skills/<name>` 的对应 symlink（不要删错其它 skill）。
