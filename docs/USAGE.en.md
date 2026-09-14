# Usage (English)

For people who mostly trade **China A-shares / CNY** and want an agent that asks about money pools before tickers.

No web dashboard—Markdown tables in chat on purpose. Chinese docs are the primary voice; this page stays short.

## Commands

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash
pip3 install requests pandas akshare baostock   # if you need quotes
```

Confirm with `yes`, or set `FAMILY_WEALTH_YES=1`. Start a **new** chat after install.

Full Chinese walkthrough (tone + examples): [USAGE.zh.md](USAGE.zh.md).

## Talk order

1. `family-wealth-ips` — which money, emergency cash, stock overweight?  
2. Balance sheet if needed  
3. Then bond / dividend / daily-monitor / research skills  

Expect a plain line like `能不能买: 可以 / 先少买点 / 先别买`. If it’s 先别买, no order list.

Demos: [demo-conversation.zh.md](../examples/demo-conversation.zh.md) · [scenario-monitor-2026-09-11.zh.md](../examples/scenario-monitor-2026-09-11.zh.md)

## Notes

- Quotes: Tencent → Sina → optional mootdx. Free sources flake; retry.  
- Keep `*.local.*` private. See [PRIVACY.md](../PRIVACY.md).  
- Not investment advice. A-share focused.
