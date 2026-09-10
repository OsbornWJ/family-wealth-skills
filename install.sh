#!/usr/bin/env bash
# One-shot install for Family Wealth Skills (Cursor + Claude Code).
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash
set -euo pipefail

REPO_URL="${FAMILY_WEALTH_REPO:-https://github.com/OsbornWJ/family-wealth-skills.git}"
INSTALL_DIR="${FAMILY_WEALTH_HOME:-$HOME/.family-wealth-skills}"
BRANCH="${FAMILY_WEALTH_BRANCH:-main}"

echo "==> Install dir: $INSTALL_DIR"

if command -v git >/dev/null 2>&1; then
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "==> Updating existing clone..."
    git -C "$INSTALL_DIR" fetch --depth 1 origin "$BRANCH"
    git -C "$INSTALL_DIR" checkout "$BRANCH"
    git -C "$INSTALL_DIR" reset --hard "origin/$BRANCH"
  else
    rm -rf "$INSTALL_DIR"
    git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
  fi
else
  echo "git not found; downloading zip..."
  tmp="$(mktemp -d)"
  zip="$tmp/repo.zip"
  curl -fsSL "https://github.com/OsbornWJ/family-wealth-skills/archive/refs/heads/${BRANCH}.zip" -o "$zip"
  unzip -q "$zip" -d "$tmp"
  rm -rf "$INSTALL_DIR"
  mv "$tmp/family-wealth-skills-${BRANCH}" "$INSTALL_DIR"
  rm -rf "$tmp"
fi

mkdir -p "$HOME/.cursor/skills" "$HOME/.claude/skills"

linked=0
for d in "$INSTALL_DIR"/*/ ; do
  [ -f "$d/SKILL.md" ] || continue
  name="$(basename "$d")"
  ln -sfn "$d" "$HOME/.cursor/skills/$name"
  ln -sfn "$d" "$HOME/.claude/skills/$name"
  linked=$((linked + 1))
done

# Seed local configs once (do not overwrite)
if [ ! -f "$INSTALL_DIR/family-wealth-ips/assets/ips.local.md" ]; then
  cp "$INSTALL_DIR/family-wealth-ips/assets/ips.example.md" \
     "$INSTALL_DIR/family-wealth-ips/assets/ips.local.md" 2>/dev/null || true
fi
if [ ! -f "$INSTALL_DIR/personal-financial-tracker/assets/balance-sheet.local.md" ]; then
  cp "$INSTALL_DIR/personal-financial-tracker/assets/balance-sheet.example.md" \
     "$INSTALL_DIR/personal-financial-tracker/assets/balance-sheet.local.md" 2>/dev/null || true
fi
if [ ! -f "$INSTALL_DIR/a-share-daily-monitor/assets/portfolio.local.json" ]; then
  cp "$INSTALL_DIR/a-share-daily-monitor/assets/portfolio.example.json" \
     "$INSTALL_DIR/a-share-daily-monitor/assets/portfolio.local.json" 2>/dev/null || true
fi

echo
echo "OK: linked $linked skills → ~/.cursor/skills and ~/.claude/skills"
echo "Optional Python deps:"
echo "  pip3 install requests pandas akshare baostock"
echo "Edit your numbers (optional):"
echo "  $INSTALL_DIR/family-wealth-ips/assets/ips.local.md"
echo "  $INSTALL_DIR/a-share-daily-monitor/assets/portfolio.local.json"
echo "Then start a NEW agent chat and try: 先问清楚能不能买（family-wealth-ips）"
