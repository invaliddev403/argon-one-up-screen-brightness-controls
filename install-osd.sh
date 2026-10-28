#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
extension_dir="$HOME/.local/share/gnome-shell/extensions/ddc-brightness-osd@argon-one-up.local"
mkdir -p -- "$extension_dir"
install -m 644 osd-extension/metadata.json osd-extension/extension.js "$extension_dir/"
sudo install -o root -g root -m 644 listener.py /usr/local/libexec/ddc-brightness-keys.py
service_user="$(id -un)"
if [[ "$service_user" == root ]]; then
    echo 'Run this script as your desktop user, without sudo.' >&2
    exit 1
fi
unit_file="$(mktemp)"
trap 'rm -f -- "$unit_file"' EXIT
SERVICE_USER="$service_user" python3 - <<'PYUNIT' > "$unit_file"
import os
from pathlib import Path
print(Path('ddc-brightness-keys.service').read_text().replace(
    '@SERVICE_USER@', os.environ['SERVICE_USER']), end='')
PYUNIT
sudo install -o root -g root -m 644 "$unit_file" /etc/systemd/system/ddc-brightness-keys.service
sudo systemctl daemon-reload
sudo systemctl restart ddc-brightness-keys.service
if gnome-extensions enable ddc-brightness-osd@argon-one-up.local; then
    echo 'Overlay enabled. Try the brightness keys.'
else
    echo 'Log out and back in, then run: gnome-extensions enable ddc-brightness-osd@argon-one-up.local'
fi
