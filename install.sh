#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.local/share/dual-wallpaper"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/dual-wallpaper"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

mkdir -p "$TARGET_DIR" "$BIN_DIR" "$CONFIG_DIR" "$SYSTEMD_USER_DIR"
cp "$ROOT_DIR/dual_wallpaper.py" "$TARGET_DIR/dual_wallpaper.py"
chmod +x "$TARGET_DIR/dual_wallpaper.py"
ln -sf "$TARGET_DIR/dual_wallpaper.py" "$BIN_DIR/dual-wallpaper"

cat > "$SYSTEMD_USER_DIR/dual-wallpaper.service" <<'EOF'
[Unit]
Description=Dual Wallpaper background rotator

[Service]
Type=simple
ExecStart=%h/.local/share/dual-wallpaper/dual_wallpaper.py --daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now dual-wallpaper.service

printf 'Installed Dual Wallpaper in %s\n' "$TARGET_DIR"
