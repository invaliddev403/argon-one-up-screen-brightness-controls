#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
extension_dir="$HOME/.local/share/gnome-shell/extensions/ddc-brightness-osd@redwood.local"
mkdir -p -- "$extension_dir"
install -m 644 osd-extension/metadata.json osd-extension/extension.js "$extension_dir/"
sudo install -o root -g root -m 644 listener.py /usr/local/libexec/ddc-brightness-keys.py
sudo install -o root -g root -m 644 ddc-brightness-keys.service /etc/systemd/system/ddc-brightness-keys.service
sudo systemctl daemon-reload
sudo systemctl restart ddc-brightness-keys.service
if gnome-extensions enable ddc-brightness-osd@redwood.local; then
    echo 'Overlay enabled. Try the brightness keys.'
else
    echo 'Log out and back in, then run: gnome-extensions enable ddc-brightness-osd@redwood.local'
fi
