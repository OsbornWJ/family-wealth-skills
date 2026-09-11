#!/usr/bin/env bash
# 一键卸载 Family Wealth Skills（技能目录 + 快捷链接 + 本地配置一并删除）
#
#   curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash
#
# 不想确认时：
#   FAMILY_WEALTH_YES=1 curl -fsSL .../uninstall.sh | bash
set -euo pipefail

INSTALL_DIR="${FAMILY_WEALTH_HOME:-$HOME/.family-wealth-skills}"

_confirm() {
  if [ "${FAMILY_WEALTH_YES:-}" = "1" ] || [ "${FAMILY_WEALTH_YES:-}" = "yes" ]; then
    return 0
  fi
  if [ ! -r /dev/tty ]; then
    echo "无法交互确认。请改用："
    echo "  FAMILY_WEALTH_YES=1 curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/uninstall.sh | bash"
    exit 1
  fi
  echo
  echo "将删除："
  echo "  - $INSTALL_DIR（含你填的 *.local.*）"
  echo "  - ~/.cursor/skills 与 ~/.claude/skills 里指向上述目录的链接"
  echo
  printf "确认卸载？输入 yes 继续: " > /dev/tty
  read -r ans < /dev/tty
  case "$ans" in
    yes|YES|y|Y) ;;
    *) echo "已取消"; exit 0 ;;
  esac
}

_unlink_skills() {
  local base name target
  for base in "$HOME/.cursor/skills" "$HOME/.claude/skills"; do
    [ -d "$base" ] || continue
    for link in "$base"/*; do
      [ -L "$link" ] || continue
      target="$(readlink "$link" 2>/dev/null || true)"
      case "$target" in
        "$INSTALL_DIR"/*|"$INSTALL_DIR")
          name="$(basename "$link")"
          rm -f "$link"
          echo "  已去掉链接: $base/$name"
          ;;
      esac
    done
  done
}

_confirm
echo "==> 卸载 Family Wealth Skills"

_unlink_skills

if [ -d "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  echo "  已删除: $INSTALL_DIR"
else
  echo "  安装目录不存在，跳过: $INSTALL_DIR"
fi

echo
echo "OK: 已卸载。需要再用时重新安装："
echo "  curl -fsSL https://raw.githubusercontent.com/OsbornWJ/family-wealth-skills/main/install.sh | bash"
