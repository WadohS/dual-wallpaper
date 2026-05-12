#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.local/share/dual-wallpaper"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/dual-wallpaper"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
ICONS_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

mkdir -p "$TARGET_DIR" "$BIN_DIR" "$CONFIG_DIR" "$SYSTEMD_USER_DIR" "$ICONS_DIR"
cp "$ROOT_DIR/dual_wallpaper.py" "$TARGET_DIR/dual_wallpaper.py"
cp "$ROOT_DIR/dual_wallpaper_indicator.py" "$TARGET_DIR/dual_wallpaper_indicator.py"
cp "$ROOT_DIR/assets/dual-desktop.svg" "$ICONS_DIR/dual-desktop.svg"
chmod +x "$TARGET_DIR/dual_wallpaper.py"
chmod +x "$TARGET_DIR/dual_wallpaper_indicator.py"
ln -sf "$TARGET_DIR/dual_wallpaper.py" "$BIN_DIR/dual-wallpaper"
ln -sf "$TARGET_DIR/dual_wallpaper_indicator.py" "$BIN_DIR/dual-wallpaper-indicator"

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

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/dual-wallpaper-indicator.desktop" <<'EOF'
[Desktop Entry]
Name=Dual Wallpaper Indicator
Comment=Top bar menu for Dual Wallpaper
Exec=/home/wadohs/.local/share/dual-wallpaper/dual_wallpaper_indicator.py
Icon=dual-desktop
Terminal=false
Type=Application
Categories=Utility;GNOME;
X-GNOME-Autostart-Delay=10
EOF

printf 'Installed Dual Wallpaper in %s\n' "$TARGET_DIR"
