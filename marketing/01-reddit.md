# Reddit · ready to paste

**Image:** `images/fw-cover-1x1-reddit-og.png`  
**Not a tip sheet.** No “buy this ticker” content.

**Title options:**
1. I open-sourced AgentSkills that make the AI ask “whose money is this?” before A-share talk  
2. Family Wealth Skills — household rules + China A-share monitor scripts (one-command install)  
3. Cursor/Claude skills for family money gates + local A-share helpers (MIT, no dashboard)

---

## Body

I got tired of two things:

1. Agents that jump straight to “add more tech ETFs” without asking if it’s rent money or play money  
2. Re-typing the same portfolio checklist every session

So I packaged what I actually use: **Family Wealth Skills** ([AgentSkills](https://agentskills.io) for Cursor / Claude Code / Hermes / OpenClaw).

Repo: https://github.com/OsbornWJ/family-wealth-skills · MIT  
Public export is sanitized — no live personal book.

### What you get

- **Ask-before-acting rules** (`family-wealth-ips`) — whose money, emergency cash, equity budget  
- **Balance-sheet template** — local Markdown, tables in chat  
- **China A-share helpers** — morning / pre-close / daily scripts; bond & dividend *workflows*; research frameworks  
- **Free quotes** — Tencent → Sina → optional mootdx (can lag; no API key)

### What you don’t get

- Licensed advice / tip spam / return promises  
- A web dashboard (on purpose — chat tables only)  
- Drop-in US/EU brokerage automation (CN / CNY focused)

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
pip3 install requests pandas akshare baostock   # if you run monitors
```

Reset / uninstall one-liners are in the README. **Start a new agent chat** after install.

### Talk order

1. “Run `family-wealth-ips`: whose money, emergency cash, equity share?”  
2. Balance sheet if needed  
3. Then bond / dividend / monitor / research  

Expect a plain line like `能不能买: 可以 / 先少买点 / 先别买` (can / size down / don’t). On “don’t”, no order list.

```bash
cd ~/.family-wealth-skills/a-share-daily-monitor
python3 scripts/morning_check.py
python3 scripts/daily_monitor.py
```

Not investment advice. Issues about skill design welcome; “what should I buy today” is out of scope here.
