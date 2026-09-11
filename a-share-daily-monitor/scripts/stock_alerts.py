#!/usr/bin/env python3
"""
Optional stock watchlist alerts (price tiers).

Reads `watchlist` from portfolio.local.json / portfolio.example.json.
If watchlist is empty, exits quietly (public pack ships with no personal names).

Example portfolio JSON:

  "watchlist": {
    "300073": {
      "name": "示例成长股",
      "sina": "sz300073",
      "alerts": [[45.0, "试探区"], [36.0, "低估区"]]
    }
  }
"""
from __future__ import annotations

import sys
import urllib.request

from portfolio_config import load_portfolio

_PF = load_portfolio()
WATCH = _PF.get("watchlist") or {}


def get_realtime(sina_code: str) -> dict:
    url = f"https://hq.sinajs.cn/list={sina_code}"
    req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode("gbk")
    fields = data.split('"')[1].split(",")
    price = float(fields[3])
    prev = float(fields[2])
    return {
        "name": fields[0],
        "price": price,
        "pre_close": prev,
        "high": float(fields[4]),
        "low": float(fields[5]),
        "chg": (price - prev) / prev * 100 if prev else 0.0,
    }


def main() -> int:
    if not WATCH:
        print("个股挂单预警: 未配置 watchlist，跳过")
        return 0
    print("个股挂单预警")
    for code, meta in WATCH.items():
        sina = meta.get("sina") or (
            "sh" + code if code.startswith("6") else "sz" + code
        )
        name = meta.get("name", code)
        try:
            d = get_realtime(sina)
        except Exception as e:
            print(f"{name}({code}) 获取失败: {e}")
            continue
        print(
            f"{name} 现价:{d['price']:.2f} {d['chg']:+.2f}%  "
            f"高:{d['high']:.2f} 低:{d['low']:.2f}"
        )
        tiers = meta.get("alerts") or []
        triggered = False
        for target, msg in tiers:
            if d["price"] <= float(target):
                print(f"  🔴 触发! ≤{target} → {msg}")
                triggered = True
        if not triggered and tiers:
            dists = [
                f"距{float(t):.0f}还差{(d['price']/float(t)-1)*100:+.1f}%"
                for t, _ in tiers
            ]
            print(f"  未触发 | {' | '.join(dists)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
