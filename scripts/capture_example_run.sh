#!/usr/bin/env bash
# Capture monitor script outputs into examples/ (sanitized).
# Usage: from repo root → bash scripts/capture_example_run.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$ROOT/a-share-daily-monitor/scripts"
OUT_DIR="$ROOT/examples/_raw"
mkdir -p "$OUT_DIR"
DAY="$(date +%Y-%m-%d)"

sanitize() {
  # drop absolute paths / home dirs
  sed -E \
    -e 's#\[portfolio\] loaded .*/(portfolio\.(example|local)\.json)#\[portfolio\] loaded \1#g' \
    -e "s#$HOME#~#g" \
    -e 's#/Users/[^/]+/#~/ #g'
}

cd "$SCRIPTS"
python3 morning_check.py 2>/dev/null | sanitize > "$OUT_DIR/morning.$DAY.txt" || true
python3 pre_close_check.py 2>/dev/null | sanitize > "$OUT_DIR/pre_close.$DAY.txt" || true
python3 daily_monitor.py 2>/dev/null | sanitize > "$OUT_DIR/daily.$DAY.txt" || true

echo "Wrote:"
ls -la "$OUT_DIR"/*."$DAY".txt 2>/dev/null || echo "(empty — market closed or network fail)"
echo "Paste into examples/scenario-*.zh.md and add Agent interpretation."
