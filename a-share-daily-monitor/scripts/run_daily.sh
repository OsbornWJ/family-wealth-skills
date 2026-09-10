#!/bin/bash
# Run full daily monitor from this scripts/ directory (portable).
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/daily_monitor.py" 2>&1
