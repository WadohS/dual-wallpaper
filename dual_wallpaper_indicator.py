#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from pathlib import Path

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import AyatanaAppIndicator3, Gtk  # noqa: E402


HOME = Path.home()
APP_DIR = HOME / '.local' / 'share' / 'dual-wallpaper'
CLI = str(APP_DIR / 'dual_wallpaper.py')


def run_command(command: list[str]) -> None:
    subprocess.Popen(command)


def build_menu() -> Gtk.Menu:
    menu = Gtk.Menu()

    def add_item(label: str, callback) -> None:
        item = Gtk.MenuItem(label=label)
        item.connect('activate', callback)
        item.show()
        menu.append(item)

    add_item('Next', lambda *_args: run_command([CLI, '--apply']))
    add_item('Previous', lambda *_args: run_command([CLI, '--previous']))
    add_item('Refresh Current Pair', lambda *_args: run_command([CLI, '--refresh']))

    separator = Gtk.SeparatorMenuItem()
    separator.show()
    menu.append(separator)

    add_item('Settings', lambda *_args: run_command(['gnome-extensions', 'prefs', 'dual-clock@wadohs']))
    add_item('Restart Service', lambda *_args: run_command(['systemctl', '--user', 'restart', 'dual-wallpaper.service']))

    separator2 = Gtk.SeparatorMenuItem()
    separator2.show()
    menu.append(separator2)

    add_item('Quit Menu', lambda *_args: Gtk.main_quit())

    return menu


def main() -> int:
    indicator = AyatanaAppIndicator3.Indicator.new(
        'dual-wallpaper-indicator',
        'preferences-desktop-wallpaper',
        AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_title('Dual Wallpaper')
    indicator.set_menu(build_menu())
    Gtk.main()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
