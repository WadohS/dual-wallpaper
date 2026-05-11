# Dual Wallpaper

Local dual-monitor wallpaper rotator for GNOME.

## Goals

- two different wallpapers on two monitors
- one local folder or one folder per monitor
- configurable rotation interval
- atomic wallpaper updates to reduce glitches
- no dependency on Variety

## Usage

Run once:

```bash
./dual_wallpaper.py --apply
```

Run continuously:

```bash
./dual_wallpaper.py --daemon
```

## Config

Default config path:

`~/.config/dual-wallpaper/config.json`

Key settings:

- `mode`: `shared` or `split`
- `primary_folder`
- `secondary_folder`
- `different_images`
- `interval_seconds`
- `recursive`

## Installation

Use `install.sh` to install the script and service locally.

After installation, launch `Dual Wallpaper` from the applications menu to edit the configuration.
