#!/usr/bin/env python3
"""Load portfolio config for monitor scripts (public pack)."""
from __future__ import annotations

import json
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_LOCAL = _ASSETS / "portfolio.local.json"
_EXAMPLE = _ASSETS / "portfolio.example.json"

_DEFAULT_SETTINGS = {
    "example_mode": False,
    "enable_hard_sell_alerts": True,
    "enable_observe_over_cost_alert": True,
    "drawdown_watch_pct": 8.0,
    "drawdown_alert_pct": 15.0,
    "volume_cold_trillion": 1.5,
    "volume_dry_trillion": 1.0,
}


def load_portfolio() -> dict:
    path = _LOCAL if _LOCAL.exists() else _EXAMPLE
    data = json.loads(path.read_text(encoding="utf-8"))
    etf = data.get("etf") or {}
    stocks = data.get("stocks") or {}
    sina_map = data.get("sina_map") or {
        code: ("sh" + code if code.startswith(("5", "6")) else "sz" + code)
        for code in etf
    }
    settings = {**_DEFAULT_SETTINGS, **(data.get("settings") or {})}
    # Example file always demos quietly unless user overrides
    if path.name.endswith("example.json"):
        settings["example_mode"] = True
        if "enable_hard_sell_alerts" not in (data.get("settings") or {}):
            settings["enable_hard_sell_alerts"] = False

    stock_sina = {}
    stock_meta = {}
    for code, v in stocks.items():
        stock_sina[code] = (
            "sh" + code if code.startswith("6") else "sz" + code
        )
        stock_meta[code] = {
            "name": v.get("name", code),
            "annual_div": float(v["annual_div"]) if v.get("annual_div") is not None else None,
            "min_yield_pct": float(v.get("min_yield_pct", 4.0)),
            "alert_on_low_yield": bool(v.get("alert_on_low_yield", True)),
        }

    return {
        "path": str(path),
        "is_example": path.name.endswith("example.json") or bool(settings.get("example_mode")),
        "settings": settings,
        "etf_names": {c: v.get("name", c) for c, v in etf.items()},
        "etf_type": {c: v.get("type", "观察") for c, v in etf.items()},
        "cost_price": {c: float(v["cost"]) for c, v in etf.items() if "cost" in v},
        "peak_price": {
            c: float(v["peak"]) for c, v in etf.items() if v.get("peak") is not None
        },
        "stock_cost": {c: float(v["cost"]) for c, v in stocks.items() if "cost" in v},
        "stock_sina": stock_sina,
        "stock_meta": stock_meta,
        "watchlist": data.get("watchlist") or {},
        "sina_map": sina_map,
    }
