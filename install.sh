#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/.local/share/dual-wallpaper"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/dual-wallpaper"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

mkdir -p "$TARGET_DIR" "$BIN_DIR" "$CONFIG_DIR" "$SYSTEMD_USER_DIR"
cp "$ROOT_DIR/dual_wallpaper.py" "$TARGET_DIR/dual_wallpaper.py"
cp "$ROOT_DIR/dual_wallpaper_prefs.py" "$TARGET_DIR/dual_wallpaper_prefs.py"
chmod +x "$TARGET_DIR/dual_wallpaper.py"
chmod +x "$TARGET_DIR/dual_wallpaper_prefs.py"
ln -sf "$TARGET_DIR/dual_wallpaper.py" "$BIN_DIR/dual-wallpaper"
ln -sf "$TARGET_DIR/dual_wallpaper_prefs.py" "$BIN_DIR/dual-wallpaper-prefs"

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

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/dual-wallpaper.desktop" <<'EOF'
[Desktop Entry]
Name=Dual Wallpaper
Comment=Dual monitor wallpaper rotator
Exec=%h/.local/share/dual-wallpaper/dual_wallpaper_prefs.py
Icon=preferences-desktop-wallpaper
Terminal=false
Type=Application
Categories=Utility;GNOME;
Actions=Apply;Restart;EditConfig;

[Desktop Action Apply]
Name=Apply now
Exec=/bin/bash -lc '%h/.local/share/dual-wallpaper/dual_wallpaper.py --apply'

[Desktop Action Restart]
Name=Restart service
Exec=/bin/bash -lc 'systemctl --user restart dual-wallpaper.service'

[Desktop Action EditConfig]
Name=Edit config JSON
Exec=/bin/bash -lc 'gio open %h/.config/dual-wallpaper/config.json'
EOF

printf 'Installed Dual Wallpaper in %s\n' "$TARGET_DIR"
