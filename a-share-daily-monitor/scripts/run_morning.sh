#!/bin/bash
# Run morning check from this scripts/ directory (portable).
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 "$ROOT/morning_check.py" 2>&1
