# Privacy

## What this repo should contain

- Skill workflows, example configs (`*.example.md` / `portfolio.example.json`)
- Scripts that read **local** portfolio files
- Fictional demos

## What you must keep private

| Item | Why |
|------|-----|
| `*.local.md` / `*.local.json` | Your net worth, costs, holdings |
| Broker exports, screenshots of positions | Identifiable financial data |
| Session diaries / chat logs with real P&amp;L | Personal trading history |
| Email, phone, ID, bank account numbers | PII |

Do **not** open a PR or push a branch that adds these files.

## Recommended local git hygiene

If you fork and also keep a private overlay:

```gitignore
**/*.local.md
**/*.local.json
**/portfolio.local.*
```

## Data sent to third parties

Quote scripts call **public** HTTP endpoints (e.g. Tencent / Sina).  
No API key is required on the default path. Your broker credentials should never be placed in this repo.

## Security contact

If you find a personal data leak in a published commit, open a private security advisory (or email the maintainer) rather than posting holdings in a public issue.
