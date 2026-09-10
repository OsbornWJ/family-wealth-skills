#!/usr/bin/env python3
"""Load portfolio config for monitor scripts (public pack)."""
from __future__ import annotations

import json
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_LOCAL = _ASSETS / "portfolio.local.json"
_EXAMPLE = _ASSETS / "portfolio.example.json"


def load_portfolio() -> dict:
    path = _LOCAL if _LOCAL.exists() else _EXAMPLE
    data = json.loads(path.read_text(encoding="utf-8"))
    etf = data.get("etf") or {}
    stocks = data.get("stocks") or {}
    sina_map = data.get("sina_map") or {
        code: ("sh" + code if code.startswith(("5", "6")) else "sz" + code)
        for code in etf
    }
    return {
        "path": str(path),
        "etf_names": {c: v.get("name", c) for c, v in etf.items()},
        "etf_type": {c: v.get("type", "观察") for c, v in etf.items()},
        "cost_price": {c: float(v["cost"]) for c, v in etf.items() if "cost" in v},
        "peak_price": {
            c: float(v["peak"]) for c, v in etf.items() if v.get("peak") is not None
        },
        "stock_cost": {c: float(v["cost"]) for c, v in stocks.items() if "cost" in v},
        "sina_map": sina_map,
    }
