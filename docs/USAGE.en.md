# Usage (English)

For investors who primarily use **China A-shares / CNY** and AgentSkills-capable clients.

## Setup

```bash
pip3 install requests pandas akshare baostock

SRC="$(pwd)"   # repo root
mkdir -p "$HOME/.cursor/skills" "$HOME/.claude/skills"
for d in "$SRC"/*/ ; do
  [[ -f "$d/SKILL.md" ]] || continue
  ln -sfn "$d" "$HOME/.cursor/skills/$(basename "$d")"
  ln -sfn "$d" "$HOME/.claude/skills/$(basename "$d")"
done

cp family-wealth-ips/assets/ips.example.md family-wealth-ips/assets/ips.local.md
cp personal-financial-tracker/assets/balance-sheet.example.md \
   personal-financial-tracker/assets/balance-sheet.local.md
cp a-share-daily-monitor/assets/portfolio.example.json \
   a-share-daily-monitor/assets/portfolio.local.json
# Edit *.local.* — never commit them to a public repo
```

Start a **new** agent session after linking.

## How to talk to the agent

1. Run the **IPS gate** (`family-wealth-ips`) before any buy/sell advice.  
2. Refresh the **balance sheet** when discussing net worth or risk %.  
3. Route execution: bond / dividend / daily-monitor skills.

Expect a line like `IPS闸门: 绿|黄|红` (green / yellow / red). Red = no order instructions.

Fictional walkthrough (Chinese): [examples/demo-conversation.zh.md](../examples/demo-conversation.zh.md).

## Scripts

```bash
python3 akshare-china-finance/scripts/quote_providers.py
python3 a-share-daily-monitor/scripts/morning_check.py
```

Quotes: Tencent → Sina → optional mootdx. No API keys on the default path.

## Audience note

IPS templates are portable. **Execution skills and data sources are China-only.** US/EU brokers need your own data layer.

## More

- [USAGE.zh.md](USAGE.zh.md) — fuller Chinese guide  
- [PRIVACY.md](../PRIVACY.md) · [CONTRIBUTING.md](../CONTRIBUTING.md)
