# 使用说明（中文）

面向：把本仓库当作 **Agent Skill 包** 使用的个人投资者（中国 A 股为主）。

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

## 2. 安装 Skill

在仓库根目录（本 `public` 包根）执行：

```bash
SRC="$(pwd)"
mkdir -p "$HOME/.cursor/skills" "$HOME/.claude/skills"
for d in "$SRC"/*/ ; do
  [[ -f "$d/SKILL.md" ]] || continue
  name=$(basename "$d")
  ln -sfn "$d" "$HOME/.cursor/skills/$name"
  ln -sfn "$d" "$HOME/.claude/skills/$name"
  echo "linked $name"
done
```

Hermes：将本包放到 profile 的 `skills/<category>/` 下，或对各 skill 目录做同样的 symlink。  
OpenClaw：链到 workspace 的 `skills/`；正文里可用 `{baseDir}` 指 skill 目录。

**新开一轮对话** 后再试（多数运行时在会话开始时加载 skill 列表）。

## 3. 必做：本地配置（私有）

示例文件可以提交；**填了真实数字的 local 文件不要提交**。

```bash
cp family-wealth-ips/assets/ips.example.md \
   family-wealth-ips/assets/ips.local.md

cp personal-financial-tracker/assets/balance-sheet.example.md \
   personal-financial-tracker/assets/balance-sheet.local.md

cp a-share-daily-monitor/assets/portfolio.example.json \
   a-share-daily-monitor/assets/portfolio.local.json
```

请至少填写：

| 文件 | 填什么 |
|------|--------|
| `ips.local.md` | 月支出、各钱池金额、目标配比、禁投约定 |
| `balance-sheet.local.md` | 现金/固收/权益/负债粗表 |
| `portfolio.local.json` | 你监控的 ETF/个股代码、成本、峰值（止盈用） |

监控脚本优先读 `portfolio.local.json`，没有则回退 `portfolio.example.json`。

## 4. 推荐对话顺序（规划 → 执行）

1. **总闸门** — 「按 family-wealth-ips 检查：这笔钱是哪个钱池？应急金够吗？」
2. **家底** — 「根据 balance-sheet 算金融净资产和进攻占比」
3. **再分派**  
   - 家庭固定资本 / 停靠 → `a-share-bond-allocation`  
   - 收息层 → `a-share-dividend-allocation`  
   - 盘中买卖 / 日报 → `a-share-daily-monitor`  
   - 个股研究 → comps / dcf / earnings  

Agent 输出里应出现类似：`IPS闸门: 绿|黄|红`。红灯时不应给下单指令。

虚构完整对话：[examples/demo-conversation.zh.md](../examples/demo-conversation.zh.md)

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
