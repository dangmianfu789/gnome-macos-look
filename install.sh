#!/usr/bin/env bash
# ============================================================
#  GNOME macOS Look —— 一键安装
#  全部改动都在用户态完成，不需要 sudo，随时可一键还原
# ============================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_DIR="$HOME/.config/macos-look"
PY_SRC="$REPO_DIR/macos-look.py"
PY="$CONF_DIR/macos-look.py"

echo "=============================================="
echo "  GNOME macOS Look · 一键安装"
echo "=============================================="
echo

# ---------- 1. 依赖检查 ----------
echo "[1/6] 检查系统与依赖"
echo "----------------------------------------------"
if ! python3 "$PY_SRC" deps; then
    echo
    echo "!! 缺少必需依赖，请按上面的提示补齐后重跑本脚本。"
    exit 1
fi
echo

# ---------- 2. 部署脚本 ----------
echo "[2/6] 部署脚本到 $CONF_DIR"
mkdir -p "$CONF_DIR"
cp -f "$PY_SRC" "$PY"
cp -f "$REPO_DIR/README.md" "$CONF_DIR/" 2>/dev/null || true
echo "  ✓ 完成"
echo

# ---------- 3. 备份当前设置（仅首次） ----------
echo "[3/6] 备份当前桌面设置"
if [ -f "$CONF_DIR/backup.json" ]; then
    echo "  ✓ 已存在原始备份，跳过（这是还原用的原始值，不要删除）"
else
    python3 "$PY" backup
fi
echo

# ---------- 4. 下载用户态资源 ----------
echo "[4/6] 下载用户态资源（字体 / 图标 / 光标 / 壁纸）"
echo "  首次运行需要下载约 180MB，请耐心等待"
echo "----------------------------------------------"
python3 "$PY" assets
echo

# ---------- 5. 安装 GNOME 扩展 ----------
echo "[5/6] 下载并安装 GNOME 扩展"
echo "----------------------------------------------"
python3 "$PY" install-ext
python3 "$PY" patch-ext
echo

# ---------- 6. 应用配置 ----------
echo "[6/6] 应用配置"
echo "----------------------------------------------"
python3 "$PY" apply
python3 "$PY" prepare
echo

cat <<'EOF'
==============================================
  安装完成 —— 还剩两步收尾
==============================================

【必做】注销并重新登录一次
  Wayland 下 GNOME 无法热加载新装的扩展，必须重新登录。
  登录后执行这一条把扩展全部启用：

      python3 ~/.config/macos-look/macos-look.py enable-ext

【可选】补齐推荐软件包（需要 sudo）

      sudo apt install -y gnome-sushi gnome-tweaks

      gnome-sushi    文件管理器里按空格快速预览（= macOS Quick Look）
      gnome-tweaks   图形化调参面板，以后不用记命令

【还原】任何一步不满意，随时一键还原

      python3 ~/.config/macos-look/macos-look.py revert

==============================================
EOF
