#!/usr/bin/python3
"""React only to brightness keys, without grabbing keyboard devices."""
import queue
import os
import re
import selectors
import subprocess
import threading
import time
from evdev import InputDevice, ecodes, list_devices

changes = queue.Queue(maxsize=20)


def show_brightness():
    time.sleep(0.15)
    reading = subprocess.run(
        ['/usr/bin/ddcutil', '--bus', '14', '--skip-ddc-checks',
         '--terse', 'getvcp', '10'], capture_output=True, text=True, timeout=10)
    match = re.search(r'^VCP\s+10\s+C\s+(\d+)\s+(\d+)', reading.stdout, re.MULTILINE)
    if reading.returncode or not match or int(match[2]) == 0:
        print('Could not read brightness for overlay:', reading.stdout, reading.stderr, flush=True)
        return
    percent = max(0, min(100, round(int(match[1]) * 100 / int(match[2]))))
    result = subprocess.run(
        ['/usr/bin/gdbus', 'call', '--address',
         f'unix:path=/run/user/{os.getuid()}/bus', '--dest', 'org.gnome.Shell',
         '--object-path', '/local/redwood/DdcBrightness',
         '--method', 'local.redwood.DdcBrightness.Show', str(percent)],
        capture_output=True, text=True, timeout=3)
    if result.returncode:
        print('Brightness overlay unavailable (enable extension):', result.stderr.strip(), flush=True)


def worker():
    while True:
        delta = changes.get()
        # Combine repeats that arrived while the previous DDC request ran.
        while True:
            try:
                delta += changes.get_nowait()
            except queue.Empty:
                break
        if not delta:
            continue
        try:
            result = subprocess.run(
                ['/usr/bin/ddcutil', '--bus', '14', '--skip-ddc-checks',
                 '--noverify', 'setvcp', '10',
                 '+' if delta > 0 else '-', str(min(abs(delta), 100))],
                capture_output=True, text=True, timeout=15)
            if result.returncode:
                print('Brightness update failed:', result.stderr, result.stdout, flush=True)
            else:
                print('Brightness adjusted by', delta, flush=True)
                show_brightness()
        except subprocess.TimeoutExpired:
            print('Brightness update timed out', flush=True)


def main():
    threading.Thread(target=worker, daemon=True).start()
    selector = selectors.DefaultSelector()
    devices = {}
    next_scan = 0
    directions = {ecodes.KEY_BRIGHTNESSUP: 5, ecodes.KEY_BRIGHTNESSDOWN: -5}
    while True:
        if time.monotonic() >= next_scan:
            for path in list_devices():
                if path in devices:
                    continue
                try:
                    device = InputDevice(path)
                    if not set(directions).intersection(device.capabilities().get(ecodes.EV_KEY, [])):
                        device.close()
                        continue
                    selector.register(device, selectors.EVENT_READ)
                    devices[path] = device
                    print('Listening for brightness keys:', device.name, path, flush=True)
                except OSError as error:
                    print('Input device unavailable:', path, error, flush=True)
            next_scan = time.monotonic() + 3
        for key, _ in selector.select(timeout=1):
            device = key.fileobj
            try:
                for event in device.read():
                    if event.type == ecodes.EV_KEY and event.code in directions and event.value in (1, 2):
                        try:
                            changes.put_nowait(directions[event.code])
                        except queue.Full:
                            pass
            except OSError:
                selector.unregister(device)
                devices.pop(device.path, None)
                device.close()


if __name__ == '__main__':
    main()
