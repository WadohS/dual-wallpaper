#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


HOME = Path.home()
CONFIG_DIR = HOME / '.config' / 'dual-wallpaper'
DATA_DIR = HOME / '.local' / 'share' / 'dual-wallpaper'
CONFIG_PATH = CONFIG_DIR / 'config.json'
STATE_PATH = DATA_DIR / 'state.json'
OUTPUT_PATH = DATA_DIR / 'wallpaper-composite.jpg'
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
VARIETY_CONFIG = HOME / '.config' / 'variety' / 'variety.conf'


def read_variety_defaults() -> tuple[Path, int]:
    folder = HOME / 'Téléchargements' / 'ColorWall'
    interval = 1200

    if not VARIETY_CONFIG.exists():
        return folder, interval

    values: dict[str, str] = {}
    sources: list[str] = []
    current_section = None
    for raw_line in VARIETY_CONFIG.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            current_section = line[1:-1]
            continue
        if '=' not in line:
            continue
        key, value = [part.strip() for part in line.split('=', 1)]
        if current_section == 'sources' and key.startswith('src'):
            sources.append(value)
        else:
            values[key] = value

    interval = int(values.get('change_interval', interval))
    for source in sources:
        enabled, source_type, location = source.split('|', 2)
        if enabled == 'True' and source_type == 'folder':
            folder = Path(location).expanduser()
            break

    return folder, interval


def default_config() -> dict:
    folder, interval = read_variety_defaults()
    return {
        'mode': 'shared',
        'primary_folder': str(folder),
        'secondary_folder': str(folder),
        'different_images': True,
        'recursive': False,
        'interval_seconds': interval,
        'output_file': str(OUTPUT_PATH),
        'fill_color': 'black',
    }


def ensure_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():
        cfg = default_config()
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
        return cfg

    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding='utf-8'))


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding='utf-8')


def list_images(folder: Path, recursive: bool) -> list[Path]:
    if not folder.exists():
        return []

    iterator = folder.rglob('*') if recursive else folder.glob('*')
    images = [p for p in iterator if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(images)


def choose_image(candidates: list[Path], avoid: set[str]) -> Path | None:
    available = [p for p in candidates if str(p) not in avoid]
    pool = available if available else candidates
    if not pool:
        return None
    return random.choice(pool)


def parse_monitor_geometry() -> list[dict]:
    result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, check=True)
    monitors = []
    for line in result.stdout.splitlines():
        if ' connected' not in line:
            continue
        parts = line.split()
        name = parts[0]
        geom = next((part for part in parts if 'x' in part and '+' in part), None)
        if not geom:
            continue
        width, rest = geom.split('x', 1)
        height, xpos, ypos = rest.split('+', 2)
        monitors.append({
            'name': name,
            'width': int(width),
            'height': int(height),
            'x': int(xpos),
            'y': int(ypos),
        })
    monitors.sort(key=lambda m: (m['x'], m['y']))
    return monitors


def compose_wallpaper(primary: Path, secondary: Path, output_file: Path, fill_color: str) -> None:
    monitors = parse_monitor_geometry()
    if len(monitors) < 2:
        raise RuntimeError('Dual Wallpaper requires at least two connected monitors.')

    left, right = monitors[:2]
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        left_tmp = Path(tmp_dir) / 'left.jpg'
        right_tmp = Path(tmp_dir) / 'right.jpg'
        out_tmp = Path(tmp_dir) / 'composite.jpg'

        subprocess.run([
            'magick', str(primary),
            '-resize', f"{left['width']}x{left['height']}^",
            '-gravity', 'center',
            '-extent', f"{left['width']}x{left['height']}",
            str(left_tmp),
        ], check=True)
        subprocess.run([
            'magick', str(secondary),
            '-resize', f"{right['width']}x{right['height']}^",
            '-gravity', 'center',
            '-extent', f"{right['width']}x{right['height']}",
            str(right_tmp),
        ], check=True)

        total_w = max(left['x'] + left['width'], right['x'] + right['width'])
        total_h = max(left['y'] + left['height'], right['y'] + right['height'])

        subprocess.run([
            'magick',
            '-size', f'{total_w}x{total_h}', f'xc:{fill_color}',
            str(left_tmp), '-geometry', f"+{left['x']}+{left['y']}", '-composite',
            str(right_tmp), '-geometry', f"+{right['x']}+{right['y']}", '-composite',
            str(out_tmp),
        ], check=True)

        shutil.move(out_tmp, output_file)


def apply_gnome_wallpaper(output_file: Path) -> None:
    uri = f'file://{output_file}'
    current = subprocess.run(
        ['gsettings', 'get', 'org.gnome.desktop.background', 'picture-uri'],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    if current != f"'{uri}'":
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', uri], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri-dark', uri], check=True)
        subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-options', 'spanned'], check=True)


def next_pair(config: dict, state: dict) -> tuple[Path, Path]:
    primary_folder = Path(config['primary_folder']).expanduser()
    secondary_folder = Path(config['secondary_folder']).expanduser()
    recursive = bool(config.get('recursive', False))
    shared = config.get('mode', 'shared') == 'shared'
    different = bool(config.get('different_images', True))

    primary_candidates = list_images(primary_folder, recursive)
    secondary_candidates = primary_candidates if shared else list_images(secondary_folder, recursive)
    if not primary_candidates or not secondary_candidates:
        raise RuntimeError('No wallpapers found in the configured folder(s).')

    last_primary = state.get('current_primary')
    last_secondary = state.get('current_secondary')

    primary = choose_image(primary_candidates, {last_primary} if last_primary else set())
    avoid_secondary = {last_secondary} if last_secondary else set()
    if different and primary:
        avoid_secondary.add(str(primary))
    secondary = choose_image(secondary_candidates, avoid_secondary)

    if primary is None or secondary is None:
        raise RuntimeError('Unable to select wallpapers.')

    return primary, secondary


def apply(config: dict, refresh: bool = False) -> None:
    state = load_state()
    output_file = Path(config.get('output_file', str(OUTPUT_PATH))).expanduser()

    if refresh and state.get('current_primary') and state.get('current_secondary'):
        primary = Path(state['current_primary'])
        secondary = Path(state['current_secondary'])
    else:
        primary, secondary = next_pair(config, state)
        state['current_primary'] = str(primary)
        state['current_secondary'] = str(secondary)
        save_state(state)

    compose_wallpaper(primary, secondary, output_file, config.get('fill_color', 'black'))
    apply_gnome_wallpaper(output_file)


def daemon_loop(config_path: Path) -> None:
    while True:
        config = ensure_config() if config_path == CONFIG_PATH else json.loads(config_path.read_text(encoding='utf-8'))
        apply(config)
        time.sleep(max(5, int(config.get('interval_seconds', 1200))))


def main() -> int:
    parser = argparse.ArgumentParser(description='Dual monitor wallpaper rotator for GNOME')
    parser.add_argument('--config', default=str(CONFIG_PATH))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--daemon', action='store_true')
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    config = ensure_config() if config_path == CONFIG_PATH else json.loads(config_path.read_text(encoding='utf-8'))

    if args.daemon:
        daemon_loop(config_path)
        return 0

    apply(config, refresh=args.refresh)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f'dual-wallpaper error: {err}', file=sys.stderr)
        raise SystemExit(1)
