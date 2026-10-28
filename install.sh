#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
sudo apt-get install -y python3-evdev
sudo install -D -o root -g root -m 644 listener.py /usr/local/libexec/ddc-brightness-keys.py
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
python3 setup.py --undo
sudo systemctl daemon-reload
sudo systemctl enable --now ddc-brightness-keys.service
sudo systemctl restart ddc-brightness-keys.service
sudo systemctl --no-pager status ddc-brightness-keys.service
