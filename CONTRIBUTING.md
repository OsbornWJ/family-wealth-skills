# Contributing

Thanks for helping improve this AgentSkills pack.

## Ground rules

1. **No real money data** — never commit `*.local.*`, live `COST_PRICE`, session diaries, or broker exports. See [PRIVACY.md](PRIVACY.md).
2. **China A-share scope** — execution/data changes should stay honest about CNY/A-share focus; IPS/core docs may stay locale-neutral.
3. **Not investment advice** — docs and skills are process templates; avoid “guaranteed return” language.
4. **AgentSkills shape** — each skill is a folder with `SKILL.md` (`name` + `description`); keep `description` trigger-focused (`Use when …`).

## How to contribute

1. Fork / branch from the public tree.
2. Prefer small PRs: one skill or one doc area.
3. Run checks locally:

```bash
python3 scripts/ci_check.py
```

4. Open a PR describing **why** (user pain), not only what.

## Doc language

- User-facing guides: Chinese (`docs/USAGE.zh.md`) + short English (`docs/USAGE.en.md`) is ideal.
- Code comments: English or Chinese both OK; be consistent within a file.

## Feature ideas that fit

- Better quote failover / tests (still no API-key-required defaults)
- Clearer IPS templates
- Extra fictional demos
- Hermes / OpenClaw install notes

## Feature ideas that need discussion first

- US/EU broker adapters
- Anything that stores credentials
- Auto-trading / order placement against a live broker API
