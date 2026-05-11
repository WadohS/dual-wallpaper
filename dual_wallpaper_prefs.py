#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gio, Gtk  # noqa: E402


HOME = Path.home()
CONFIG_DIR = HOME / '.config' / 'dual-wallpaper'
CONFIG_PATH = CONFIG_DIR / 'config.json'


DEFAULT_CONFIG = {
    'mode': 'shared',
    'primary_folder': str(HOME / 'Téléchargements' / 'ColorWall'),
    'secondary_folder': str(HOME / 'Téléchargements' / 'ColorWall'),
    'different_images': True,
    'recursive': False,
    'interval_minutes': 20,
    'output_file': str(HOME / '.local' / 'share' / 'dual-wallpaper' / 'wallpaper-composite.jpg'),
    'fill_color': 'black',
}


def ensure_config() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding='utf-8')
        return DEFAULT_CONFIG.copy()

    config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    if 'interval_minutes' not in config:
        seconds = int(config.pop('interval_seconds', 1200))
        config['interval_minutes'] = max(1, seconds // 60)
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')
    return config


class DualWallpaperPrefs(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id='com.wadohs.DualWallpaperPrefs')
        self._config = ensure_config()

    def do_activate(self) -> None:
        window = self.props.active_window
        if window:
            window.present()
            return

        window = Gtk.ApplicationWindow(application=self)
        window.set_title('Dual Wallpaper')
        window.set_default_size(640, 420)

        grid = Gtk.Grid(
            column_spacing=12,
            row_spacing=12,
            margin_top=12,
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
        )

        row = 0

        title = Gtk.Label(label='<b>Dual Wallpaper</b>', use_markup=True, halign=Gtk.Align.START)
        grid.attach(title, 0, row, 3, 1)
        row += 1

        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append('shared', 'Un seul dossier pour les 2 ecrans')
        self.mode_combo.append('split', 'Un dossier par ecran')
        self.mode_combo.set_active_id(self._config.get('mode', 'shared'))
        self.mode_combo.connect('changed', self._sync_visibility)
        grid.attach(Gtk.Label(label='Mode', halign=Gtk.Align.START), 0, row, 1, 1)
        grid.attach(self.mode_combo, 1, row, 2, 1)
        row += 1

        self.primary_entry = Gtk.Entry(text=self._config.get('primary_folder', ''))
        self.secondary_entry = Gtk.Entry(text=self._config.get('secondary_folder', ''))
        self.output_entry = Gtk.Entry(text=self._config.get('output_file', ''))
        self.fill_combo = Gtk.ComboBoxText()
        for color in ('black', 'white', 'gray20'):
            self.fill_combo.append(color, color)
        self.fill_combo.set_active_id(self._config.get('fill_color', 'black'))

        self.primary_label = Gtk.Label(label='Dossier ecran 1', halign=Gtk.Align.START)
        self.secondary_label = Gtk.Label(label='Dossier ecran 2', halign=Gtk.Align.START)
        self.output_label = Gtk.Label(label='Fichier de sortie', halign=Gtk.Align.START)

        primary_button = Gtk.Button(label='Choisir...')
        primary_button.connect('clicked', self._choose_folder, self.primary_entry)
        grid.attach(self.primary_label, 0, row, 1, 1)
        grid.attach(self.primary_entry, 1, row, 1, 1)
        grid.attach(primary_button, 2, row, 1, 1)
        row += 1

        secondary_button = Gtk.Button(label='Choisir...')
        secondary_button.connect('clicked', self._choose_folder, self.secondary_entry)
        grid.attach(self.secondary_label, 0, row, 1, 1)
        grid.attach(self.secondary_entry, 1, row, 1, 1)
        grid.attach(secondary_button, 2, row, 1, 1)
        row += 1

        self.different_switch = Gtk.Switch(active=self._config.get('different_images', True))
        grid.attach(Gtk.Label(label='Forcer 2 images differentes', halign=Gtk.Align.START), 0, row, 1, 1)
        grid.attach(self.different_switch, 1, row, 1, 1)
        row += 1

        self.recursive_switch = Gtk.Switch(active=self._config.get('recursive', False))
        grid.attach(Gtk.Label(label='Recherche recursive', halign=Gtk.Align.START), 0, row, 1, 1)
        grid.attach(self.recursive_switch, 1, row, 1, 1)
        row += 1

        self.interval_spin = Gtk.SpinButton.new_with_range(1, 1440, 1)
        self.interval_spin.set_value(self._config.get('interval_minutes', 20))
        grid.attach(Gtk.Label(label='Intervalle (minutes)', halign=Gtk.Align.START), 0, row, 1, 1)
        grid.attach(self.interval_spin, 1, row, 1, 1)
        row += 1

        grid.attach(Gtk.Label(label='Couleur de fond de remplissage', halign=Gtk.Align.START), 0, row, 1, 1)
        grid.attach(self.fill_combo, 1, row, 1, 1)
        row += 1

        grid.attach(self.output_label, 0, row, 1, 1)
        grid.attach(self.output_entry, 1, row, 2, 1)
        row += 1

        button_box = Gtk.Box(spacing=12)
        save_button = Gtk.Button(label='Enregistrer')
        save_button.connect('clicked', self._save)
        apply_button = Gtk.Button(label='Appliquer maintenant')
        apply_button.connect('clicked', self._apply_now)
        next_button = Gtk.Button(label='Suivant')
        next_button.connect('clicked', self._next_wallpaper)
        previous_button = Gtk.Button(label='Precedent')
        previous_button.connect('clicked', self._previous_wallpaper)
        restart_button = Gtk.Button(label='Redemarrer le service')
        restart_button.connect('clicked', self._restart_service)
        open_button = Gtk.Button(label='Ouvrir le JSON')
        open_button.connect('clicked', self._open_config)
        button_box.append(save_button)
        button_box.append(apply_button)
        button_box.append(previous_button)
        button_box.append(next_button)
        button_box.append(restart_button)
        button_box.append(open_button)
        grid.attach(button_box, 0, row, 3, 1)

        self.status = Gtk.Label(label='', halign=Gtk.Align.START)
        row += 1
        grid.attach(self.status, 0, row, 3, 1)

        self._sync_visibility()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(grid)
        window.set_child(scrolled)
        window.present()

    def _sync_visibility(self, *_args) -> None:
        split = self.mode_combo.get_active_id() == 'split'
        self.secondary_label.set_visible(split)
        self.secondary_entry.set_visible(split)

    def _choose_folder(self, _button: Gtk.Button, entry: Gtk.Entry) -> None:
        dialog = Gtk.FileChooserNative(
            title='Choisir un dossier',
            transient_for=self.props.active_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
            accept_label='Choisir',
            cancel_label='Annuler',
        )
        dialog.connect('response', self._on_choose_folder_response, entry)
        dialog.show()

    def _on_choose_folder_response(self, dialog: Gtk.FileChooserNative, response: int, entry: Gtk.Entry) -> None:
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file and file.get_path():
                entry.set_text(file.get_path())
        dialog.destroy()

    def _collect(self) -> dict:
        return {
            'mode': self.mode_combo.get_active_id() or 'shared',
            'primary_folder': self.primary_entry.get_text(),
            'secondary_folder': self.secondary_entry.get_text() or self.primary_entry.get_text(),
            'different_images': self.different_switch.get_active(),
            'recursive': self.recursive_switch.get_active(),
            'interval_minutes': self.interval_spin.get_value_as_int(),
            'output_file': self.output_entry.get_text(),
            'fill_color': self.fill_combo.get_active_id() or 'black',
        }

    def _save(self, *_args) -> None:
        self._config = self._collect()
        CONFIG_PATH.write_text(json.dumps(self._config, indent=2), encoding='utf-8')
        self.status.set_text('Configuration enregistree.')

    def _run(self, command: list[str]) -> tuple[bool, str]:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, result.stdout.strip() or result.stderr.strip() or 'OK'
        except subprocess.CalledProcessError as err:
            return False, err.stderr.strip() or err.stdout.strip() or str(err)

    def _apply_now(self, *_args) -> None:
        self._save()
        ok, msg = self._run([str(HOME / '.local' / 'share' / 'dual-wallpaper' / 'dual_wallpaper.py'), '--apply'])
        self.status.set_text('Fond applique.' if ok else f'Erreur: {msg}')

    def _next_wallpaper(self, *_args) -> None:
        self._save()
        ok, msg = self._run([str(HOME / '.local' / 'share' / 'dual-wallpaper' / 'dual_wallpaper.py'), '--apply'])
        self.status.set_text('Couple suivant applique.' if ok else f'Erreur: {msg}')

    def _previous_wallpaper(self, *_args) -> None:
        self._save()
        ok, msg = self._run([str(HOME / '.local' / 'share' / 'dual-wallpaper' / 'dual_wallpaper.py'), '--previous'])
        self.status.set_text('Couple precedent applique.' if ok else f'Erreur: {msg}')

    def _restart_service(self, *_args) -> None:
        self._save()
        ok, msg = self._run(['systemctl', '--user', 'restart', 'dual-wallpaper.service'])
        self.status.set_text('Service redemarre.' if ok else f'Erreur: {msg}')

    def _open_config(self, *_args) -> None:
        Gio.AppInfo.launch_default_for_uri(f'file://{CONFIG_PATH}', None)


def main() -> int:
    app = DualWallpaperPrefs()
    return app.run(None)


if __name__ == '__main__':
    raise SystemExit(main())
