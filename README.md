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
- `interval_minutes`
- `recursive`

The settings are exposed through the shared `Dual Desktop` extension preferences and the top bar indicator.

## Top Bar Menu

`Dual Wallpaper` installs a tray/appindicator menu in the top bar with:

- `Next`
- `Previous`
- `Refresh Current Pair`
- `Reglages`
- `Redemarrer le service`

## Installation

Use `install.sh` to install the script and service locally.

After installation, open the shared settings from the `Dual Desktop` extension preferences or from the top bar indicator.
