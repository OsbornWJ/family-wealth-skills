#!/bin/bash
# Run mid-session / pre-close checks from this scripts/ directory (portable).
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/pre_close_check.py" 2>&1
if [ -f "$ROOT/stock_alerts.py" ]; then
  python3 "$ROOT/stock_alerts.py" 2>&1
fi
