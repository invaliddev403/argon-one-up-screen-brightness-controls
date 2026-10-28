#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
sudo apt-get install -y python3-evdev
sudo install -D -o root -g root -m 644 listener.py /usr/local/libexec/ddc-brightness-keys.py
sudo install -o root -g root -m 644 ddc-brightness-keys.service /etc/systemd/system/ddc-brightness-keys.service
python3 setup.py --undo
sudo systemctl daemon-reload
sudo systemctl enable --now ddc-brightness-keys.service
sudo systemctl restart ddc-brightness-keys.service
sudo systemctl --no-pager status ddc-brightness-keys.service
