# Usage (English)

For investors who primarily use **China A-shares / CNY** and AgentSkills-capable clients.

**Scope:** This repo is Agent workflows and scripts — **no Web dashboard / HTML UI**. Ask the agent for Markdown tables (IPS, balance sheet, P&amp;L), or wire your own tools to `*.local.*`.

## Setup

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash   # reset local numbers
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash    # remove everything
pip3 install requests pandas akshare baostock   # only if you need quote scripts
```

Install clones to `~/.family-wealth-skills` and symlinks into Cursor / Claude Code.  
Confirm with `yes`, or set `FAMILY_WEALTH_YES=1`. Start a **new** agent session afterward.

## How to talk to the agent

1. **Ask before buying** (`family-wealth-ips`): which money, emergency cash, is stock too heavy?  
2. Refresh the **balance sheet** when discussing net worth.  
3. Then route: bond / dividend / daily-monitor.

Expect a plain line like `能不能买: 可以 / 先少买点 / 先别买`. “先别买” = no order instructions.


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
