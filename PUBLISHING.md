# Publishing checklist

Publish **only** the `public/` tree as the GitHub root (or rsync it to a public repo).

## Docs readers need

| Doc | Purpose |
|-----|---------|
| [README.md](README.md) | Bilingual landing + scope |
| [docs/USAGE.zh.md](docs/USAGE.zh.md) | 中文使用说明 |
| [docs/USAGE.en.md](docs/USAGE.en.md) | Short English usage |
| [examples/demo-conversation.zh.md](examples/demo-conversation.zh.md) | IPS walkthrough + link to live run |
| [examples/scenario-monitor-2026-09-11.zh.md](examples/scenario-monitor-2026-09-11.zh.md) | Real morning/pre-close/daily capture |
| [PRIVACY.md](PRIVACY.md) | What not to commit |
| [CONTRIBUTING.md](CONTRIBUTING.md) | PR rules |

## Before every publish

- [ ] `python3 scripts/ci_check.py` passes
- [ ] No `*.local.md` / `*.local.json` staged
- [ ] README still states China A-share focus for execution
- [ ] Optional: tag `v0.x.y`

## Push

```bash
cd public
git init    # first time only
git add .
git commit -m "Initial public family-wealth skills"
git remote add origin git@github.com:YOU/family-wealth-skills.git
git push -u origin main
```

CI workflow: `.github/workflows/ci.yml`.
