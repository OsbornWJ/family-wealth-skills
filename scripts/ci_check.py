#!/usr/bin/env python3
"""CI checks for the public skill pack."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_NAME_PARTS = (
    ".local.md",
    ".local.json",
    "session-lessons",
    "user-fund-account",
    "cost-records.md",
)

FORBIDDEN_CONTENT = re.compile(
    r"wenjie\.liao|Osbornjie@|@163\.com|老婆的钱",
    re.I,
)

# Embedded secrets / anti-patterns in published tree
EMBEDDED_SECRET = re.compile(
    r"b64decode\(\s*['\"][A-Za-z0-9+/=]{16,}['\"]\s*\)|SMTP_PASSWORD\s*=\s*['\"][^'\"]+['\"]",
)
MISLEADING_FUND_FLOW = re.compile(r"三、主力资金信号")

# Real-looking cost literals that should not appear as hardcoded dicts in scripts
HARDCODED_COST = re.compile(
    r"COST_PRICE\s*=\s*\{[^}]*0\.\d{3,}",
    re.S,
)


def main() -> int:
    errors: list[str] = []
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    # skip .git if present
    files = [p for p in files if ".git" not in p.parts]

    for p in files:
        rel = str(p.relative_to(ROOT))
        for part in FORBIDDEN_NAME_PARTS:
            if part in p.name or part in rel.replace("\\", "/"):
                # allow mentions in docs
                if p.suffix in {".md"} and part in (
                    ".local.md",
                    ".local.json",
                    "session-lessons",
                    "user-fund-account",
                    "cost-records.md",
                ):
                    if p.name in {
                        "PRIVACY.md",
                        "CONTRIBUTING.md",
                        "README.md",
                        "USAGE.zh.md",
                        "USAGE.en.md",
                        "PUBLISHING.md",
                    } or "docs/" in rel or "examples/" in rel:
                        continue
                    if "example" in p.name:
                        continue
                if "example" in p.name:
                    continue
                if p.suffix == ".md" and any(
                    x in rel for x in ("PRIVACY", "CONTRIBUTING", "README", "USAGE", "demo-")
                ):
                    continue
                # actual forbidden artifacts
                if part in p.name:
                    errors.append(f"forbidden file name: {rel}")

        if p.suffix.lower() not in {".md", ".py", ".json", ".sh", ".yml", ".yaml"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            errors.append(f"read fail {rel}: {e}")
            continue

        if FORBIDDEN_CONTENT.search(text) and "PRIVACY" not in p.name and "ci_check" not in p.name:
            errors.append(f"forbidden content pattern in {rel}")

        if EMBEDDED_SECRET.search(text):
            errors.append(f"possible embedded secret in {rel}")

        if MISLEADING_FUND_FLOW.search(text) and (
            rel.endswith("output-formats.md") or p.suffix == ".py"
        ):
            errors.append(f"outdated section title 主力资金信号 in {rel}")

        if p.suffix == ".py" and "portfolio_config" not in p.name:
            if HARDCODED_COST.search(text) and "example" not in text.lower():
                # allow if loads from portfolio_config nearby
                if "load_portfolio" not in text and "COST_PRICE = _PF" not in text:
                    errors.append(f"possible hardcoded COST_PRICE in {rel}")

    # example portfolio must parse
    example = ROOT / "a-share-daily-monitor" / "assets" / "portfolio.example.json"
    if not example.exists():
        errors.append("missing portfolio.example.json")
    else:
        try:
            data = json.loads(example.read_text(encoding="utf-8"))
            assert "etf" in data and "stocks" in data
            # costs should look like real A-share levels (not placeholder 1.0 across the board)
            costs = [float(v["cost"]) for v in data["etf"].values() if "cost" in v]
            if costs and max(costs) / max(min(costs), 1e-9) < 1.01 and all(abs(c - 1.0) < 1e-6 for c in costs):
                errors.append("portfolio.example.json ETF costs look like placeholders (all ~1.0)")
            settings = data.get("settings") or {}
            if settings.get("enable_hard_sell_alerts") is not False and data.get("settings", {}).get("example_mode"):
                # prefer soft alerts for public example
                pass
        except Exception as e:
            errors.append(f"portfolio.example.json invalid: {e}")

    # skill folders need SKILL.md with name+description
    for d in ROOT.iterdir():
        if not d.is_dir() or d.name.startswith(".") or d.name in {"docs", "examples", "scripts"}:
            continue
        skill = d / "SKILL.md"
        if not skill.exists():
            errors.append(f"missing SKILL.md in {d.name}")
            continue
        head = skill.read_text(encoding="utf-8", errors="ignore")[:2000]
        if "name:" not in head or "description:" not in head:
            errors.append(f"SKILL.md frontmatter incomplete: {d.name}")

    # portfolio_config import smoke (no network)
    sys.path.insert(0, str(ROOT / "a-share-daily-monitor" / "scripts"))
    try:
        from portfolio_config import load_portfolio  # type: ignore

        pf = load_portfolio()
        if not pf.get("cost_price"):
            errors.append("load_portfolio returned empty cost_price")
        if not pf.get("is_example"):
            errors.append("example portfolio should set is_example=True in CI")
        if pf.get("settings", {}).get("enable_hard_sell_alerts") is not False:
            errors.append("example pack should disable hard sell alerts by default")
        if pf.get("settings", {}).get("enable_observe_over_cost_alert") is not False:
            errors.append("example pack should disable observe-over-cost alerts by default")
        if "stock_meta" not in pf:
            errors.append("load_portfolio missing stock_meta")

        # format_report must tolerate None MA fields
        import daily_monitor as dm  # type: ignore

        etf = {
            c: {
                "名称": pf["etf_names"].get(c, c),
                "单位净值": 1.0,
                "日涨跌幅": 0.0,
                "偏离MA5_pct": 0.0,
                "偏离MA20_pct": 0.0,
                "偏离MA120_pct": None,
                "距峰值回撤_pct": 0.0,
                "成本盈亏_pct": 0.0,
            }
            for c in pf["cost_price"]
        }
        try:
            dm.format_report(
                {
                    "上证指数": {"error": "skip"},
                    "成交额来源": "none",
                    "全市场估算成交额_万亿": 0,
                    "成交额达标": "",
                },
                etf,
                {},
                {},
                {"error": "skip"},
                [],
                [],
            )
        except Exception as e:
            errors.append(f"format_report None-MA crash: {e}")
    except Exception as e:
        errors.append(f"portfolio_config import failed: {e}")

    if errors:
        print("CI FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print("CI OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
