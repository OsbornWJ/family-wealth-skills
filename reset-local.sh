#!/usr/bin/env bash
# 一键重置本地用户数据（IPS / 家底表 / 持仓），技能本身保留
# 会先自动备份到 ~/.family-wealth-skills-backup-时间戳，再把 example 拷回 *.local.*
#
#   curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash
#
# 不想确认时：
#   FAMILY_WEALTH_YES=1 curl -fsSL .../reset-local.sh | bash
set -euo pipefail

INSTALL_DIR="${FAMILY_WEALTH_HOME:-$HOME/.family-wealth-skills}"

_confirm() {
  if [ "${FAMILY_WEALTH_YES:-}" = "1" ] || [ "${FAMILY_WEALTH_YES:-}" = "yes" ]; then
    return 0
  fi
  if [ ! -r /dev/tty ]; then
    echo "无法交互确认。请改用："
    echo "  FAMILY_WEALTH_YES=1 curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/reset-local.sh | bash"
    exit 1
  fi
  echo
  echo "将用示例配置覆盖这些本地文件（会自动备份）："
  echo "  - family-wealth-ips/assets/ips.local.md"
  echo "  - personal-financial-tracker/assets/balance-sheet.local.md"
  echo "  - a-share-daily-monitor/assets/portfolio.local.json"
  echo
  printf "确认重置？输入 yes 继续: " > /dev/tty
  read -r ans < /dev/tty
  case "$ans" in
    yes|YES|y|Y) ;;
    *) echo "已取消"; exit 0 ;;
  esac
}

if [ ! -d "$INSTALL_DIR" ]; then
  echo "还没安装。请先："
  echo "  curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash"
  exit 1
fi

_confirm
echo "==> 重置本地用户数据"

stamp="$(date +%Y%m%d-%H%M%S)"
backup="$HOME/.family-wealth-skills-backup-$stamp"
mkdir -p "$backup"

copy_pair() {
  local example="$1" localf="$2" label="$3"
  if [ -f "$localf" ]; then
    mkdir -p "$backup/$(dirname "$label")"
    cp "$localf" "$backup/$label"
    echo "  已备份: $label"
  fi
  if [ -f "$example" ]; then
    mkdir -p "$(dirname "$localf")"
    cp "$example" "$localf"
    echo "  已重置: $label"
  else
    echo "  缺少示例，跳过: $example"
  fi
}

copy_pair \
  "$INSTALL_DIR/family-wealth-ips/assets/ips.example.md" \
  "$INSTALL_DIR/family-wealth-ips/assets/ips.local.md" \
  "family-wealth-ips/assets/ips.local.md"

copy_pair \
  "$INSTALL_DIR/personal-financial-tracker/assets/balance-sheet.example.md" \
  "$INSTALL_DIR/personal-financial-tracker/assets/balance-sheet.local.md" \
  "personal-financial-tracker/assets/balance-sheet.local.md"

copy_pair \
  "$INSTALL_DIR/a-share-daily-monitor/assets/portfolio.example.json" \
  "$INSTALL_DIR/a-share-daily-monitor/assets/portfolio.local.json" \
  "a-share-daily-monitor/assets/portfolio.local.json"

echo
echo "OK: 本地数据已恢复成示例。"
echo "备份在: $backup"
echo "技能仍在: $INSTALL_DIR（未卸载）"
