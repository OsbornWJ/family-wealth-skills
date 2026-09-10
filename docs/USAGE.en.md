# Usage (English)

For investors who primarily use **China A-shares / CNY** and AgentSkills-capable clients.

## Setup

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
pip3 install requests pandas akshare baostock   # only if you need quote scripts
```

This clones to `~/.family-wealth-skills` and symlinks into Cursor / Claude Code.  
Start a **new** agent session afterward. Edit `*.local.*` under that folder when ready (never commit them).

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
