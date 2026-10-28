#!/usr/bin/python3
"""Install or remove GNOME shortcuts for DDC monitor brightness."""
import sys
from gi.repository import Gio

MEDIA = 'org.gnome.settings-daemon.plugins.media-keys'
CUSTOM = MEDIA + '.custom-keybinding'
ROOT = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/'
SHORTCUTS = (
    ('ddc-brightness-up/', 'Monitor brightness up', 'XF86MonBrightnessUp', '+'),
    ('ddc-brightness-down/', 'Monitor brightness down', 'XF86MonBrightnessDown', '-'),
)


def main():
    if sys.argv[1:] not in ([], ['--undo']):
        raise SystemExit('Usage: setup.py [--undo]')
    undo = '--undo' in sys.argv
    settings = Gio.Settings.new(MEDIA)
    paths = list(settings.get_strv('custom-keybindings'))
    for suffix, name, key, direction in SHORTCUTS:
        path = ROOT + suffix
        shortcut = Gio.Settings.new_with_path(CUSTOM, path)
        if undo:
            paths = [item for item in paths if item != path]
            for field in ('name', 'command', 'binding'):
                shortcut.reset(field)
        else:
            shortcut.set_string('name', name)
            shortcut.set_string('command',
                '/usr/bin/flock -w 2 /run/user/1000/ddc-brightness.lock '
                '/usr/bin/ddcutil --display 1 setvcp 10 ' + direction + ' 5')
            shortcut.set_string('binding', key)
            if path not in paths:
                paths.append(path)
    if not settings.set_strv('custom-keybindings', paths):
        raise SystemExit('Could not save shortcuts.')
    Gio.Settings.sync()
    print('Brightness shortcuts removed.' if undo else
          'Brightness shortcuts installed. Try the brightness keys (or Fn + those keys).')


if __name__ == '__main__':
    main()
