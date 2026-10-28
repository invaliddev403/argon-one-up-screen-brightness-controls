# Argon One Up screen brightness controls

Control a DDC/CI monitor with the keyboard brightness keys and show Ubuntu's native brightness overlay with a percentage and bar. The working setup uses a system service for key events and a GNOME Shell extension for the overlay.

This folder is standalone; it is not part of the adjacent `letsGO` Go installer repository. Run installation scripts from your normal desktop terminal as your own user, not with `sudo bash`. The scripts request sudo for system installation steps themselves.

Clone the project:

```bash
git clone https://github.com/invaliddev403/argon-one-up-screen-brightness-controls.git
cd argon-one-up-screen-brightness-controls
```

Before installing, follow the new adopter instructions below, especially the username, monitor bus, and GNOME version settings. The current defaults reflect the original working setup.

## Confirmed environment

Working configuration confirmed by the adopter on October 27, 2026:

| Component | Observed value |
| --- | --- |
| OS | Ubuntu 26.04.1 LTS (Resolute), arm64 |
| Desktop | Ubuntu GNOME, Wayland |
| GNOME Shell | 50.1 |
| ddcutil / libddcutil5 | 2.2.5-1 from Ubuntu resolute/universe |
| ddcui | 0.6.0-6 from Ubuntu resolute/universe |
| ddcui build/runtime libraries | libddcutil 2.2.1 / 2.2.5; Qt 5.15.17 / 5.15.18 |
| Monitor EDID | BOE, product 2187 (`0x088b`), manufactured week 16 of 2019; no model or serial reported |
| Working monitor connection | `/dev/i2c-14`, `card1-HDMI-A-2`, VCP 2.1 |
| Brightness feature | VCP `0x10`, range 0–100 |
| Keyboard events | `KEY_BRIGHTNESSUP` (225), `KEY_BRIGHTNESSDOWN` (224) |
| Input devices discovered | AMIRA-KEYBOAR USB KEYBOARD Consumer Control; Logitech USB Receiver Consumer Control |

Input event numbers such as `event18` and `event7` are observations, not configuration: the listener discovers compatible devices at runtime and rescans every three seconds. Other distributions, architectures, GNOME versions, and multiple-monitor arrangements have not been validated here.

## How it works

1. `listener.py` opens input devices that advertise either brightness key. It does not grab the devices, so GNOME can still receive their events.
2. Presses and held-key repeats enqueue changes of five units. A single worker serializes DDC operations and combines queued changes to avoid concurrent writes.
3. The worker calls `ddcutil --bus 14 --skip-ddc-checks --noverify setvcp 10 + 5` (or `- 5`). Each combined change is capped at 100 units.
4. After a successful command, it waits 150 ms and reads `getvcp 10 --terse`. The overlay uses the returned current/max ratio, not an assumed brightness value.
5. It calls the extension's `local.argononeup.DdcBrightness.Show` method on the user's session bus. The extension displays a brightness icon, percentage label, and native GNOME OSD bar on all monitors.

The overlay is transient. This does not add a permanent panel indicator or connect Ubuntu's Quick Settings brightness slider to DDC. Readback can lag on some monitors; the 150 ms delay is a local choice, not a universal guarantee.

## New adopter installation

### 1. Confirm monitor control first

Enable DDC/CI in the monitor's own settings if it has that option. Install dependencies:

```bash
sudo apt install ddcutil i2c-tools python3-evdev python3-gi libglib2.0-bin
ddcutil detect
```

If device access fails, inspect permissions and group membership:

```bash
id
getent group i2c
ls -l /dev/i2c-*
```

On the confirmed system, the `i2c` group and a udev rule assigning I²C devices to that group already existed. Adding the user resolved the permission errors:

```bash
sudo usermod -aG i2c "$USER"
```

Log out of the desktop completely and back in after changing membership. Do not make all I²C devices world writable. If your distribution lacks the group or device rule, follow the upstream permissions documentation linked below rather than assuming this command alone is enough.

Record your display's bus from `ddcutil detect`. Test a deliberate brightness change, substituting that bus number:

```bash
ddcutil --bus 14 setvcp 10 50
sleep 2
ddcutil --bus 14 getvcp 10
```

Confirm both the physical brightness change and the returned value. The original successful test used `--display 1` and returned 50/100. A working read alone does not establish that writes work.

### 2. Adapt the local settings before installing

The supplied files currently contain the working adopter's settings. The installers detect your username; monitor selection remains manual.

| File | Setting to check |
| --- | --- |
| `ddc-brightness-keys.service` | The installer sets the service user to your current account; verify `input` and `i2c` groups exist. |
| `listener.py` | Replace bus `14` in **both** DDC commands; five-unit increments are in `directions`. |
| `osd-extension/metadata.json` | Declares support for GNOME Shell 50 only. Other versions require compatibility review and testing. |
| `setup.py` | Legacy shortcut code uses the current UID and display 1; it is no longer the working key-control path. |

The listener derives the session-bus UID from its running user; there is no UID setting needed for the overlay. Keep the fixed monitor bus synchronized between the write and read commands. Port or hardware changes can renumber it.

Check your desktop with:

```bash
echo "$XDG_CURRENT_DESKTOP / $XDG_SESSION_TYPE"
gnome-shell --version
getent group input i2c
```

### 3. Install keys and overlay

From this folder, as your regular desktop user:

```bash
bash install.sh
bash install-osd.sh
```

The first script installs `python3-evdev`, copies the listener and service to system locations, removes the abandoned custom shortcuts, and enables and restarts the service. The second installs the extension in your account, refreshes the service files, restarts the service, and attempts to enable the extension.

A newly installed extension may not be discoverable until you **log out and back in** on Wayland. Then run:

```bash
gnome-extensions enable ddc-brightness-osd@argon-one-up.local
gnome-extensions info ddc-brightness-osd@argon-one-up.local
```

Expect `Enabled: Yes` and `State: ACTIVE`. Press a brightness key, with Fn if needed. Confirm the screen changes and the percentage/bar appears. Close `ddcui` during testing to avoid competing changes.

### 4. Verify persistence

```bash
systemctl is-enabled ddc-brightness-keys
systemctl is-active ddc-brightness-keys
gnome-extensions info ddc-brightness-osd@argon-one-up.local
```

The service is enabled under `multi-user.target`, so it starts at boot. Extension enablement persists for the account and GNOME loads it on login. A reboot test remains a useful adoption check; persistence is configured, but no reboot test was recorded in the original session. The service controls keys; it does not restore a saved brightness value at boot.

## Troubleshooting

### Keys do nothing

```bash
sudo journalctl -u ddc-brightness-keys -n 30 --no-pager
sudo apt install libinput-tools
sudo libinput debug-events --show-keycodes
```

Press only the brightness keys, try Fn if needed, then Ctrl+C. Expect codes 225 and 224. The diagnostic prints keyboard events, so avoid typing unrelated text while it runs. No input-listening message suggests missing device permissions, a stopped service, or a device without the advertised key capabilities.

`Brightness adjusted by 5` means the DDC subprocess exited successfully. Since immediate verification is disabled, it is not proof of the physical change; check the screen and `getvcp` if needed.

### Brightness works but overlay does not

```bash
gnome-extensions info ddc-brightness-osd@argon-one-up.local
sudo journalctl -u ddc-brightness-keys -n 20 --no-pager
```

Test just the extension from your normal desktop terminal (this displays 50% without changing the monitor):

```bash
gdbus call --session --dest org.gnome.Shell \
  --object-path /local/argononeup/DdcBrightness \
  --method local.argononeup.DdcBrightness.Show 50
```

- `Permission denied` connecting to the bus: check the installed service with `systemctl cat ddc-brightness-keys`. The working configuration uses **`ProtectHome=read-only`**. `ProtectHome=true` hid `/run/user`; exposing the socket alone with a bind mount also failed because its parent remained inaccessible.
- Unknown object or method: the extension may not be loaded. Enable it after logging out/in and check its state.
- Readback/parser error: run `ddcutil --bus 14 --skip-ddc-checks --terse getvcp 10`. The listener expects a continuous-feature line such as `VCP 10 C 50 100`.
- Extension error: inspect `journalctl --user -b` and `journalctl -b _COMM=gnome-shell` for `DdcBrightness` or the extension UUID. After changing extension JavaScript, log out/in to ensure fresh code is loaded.

### Slow changes, probe retries, or cache errors

The original service spent several seconds testing unsupported features `0xdd` and `0x41` on every invocation. Direct bus selection and `--skip-ddc-checks` removed these startup probes. `--noverify` avoids an immediate post-write verification; a separate delayed read supplies the overlay value. These choices were made after confirming feature `0x10` worked on this monitor.

`Error opening $HOME/.cache/ddcutil/dsa: Permission denied` was caused by service isolation, not by missing monitor permissions. The working unit provides:

```ini
CacheDirectory=ddc-brightness-keys
Environment=XDG_CACHE_HOME=/var/cache/ddc-brightness-keys
ProtectHome=read-only
```

Keep these when updating the service. If the monitor stops responding after cable changes, rerun `ddcutil detect`, update both bus settings, and reinstall/restart. Multi-monitor selection is not implemented.

## Findings and approaches that did not solve it

- Initial `ddcui` errors were `EACCES(-13)` opening `/dev/i2c-13` and `/dev/i2c-14`. Group access resolved the permission problem; display detection then found the working monitor on bus 14.
- `ddcui` subsequently emitted `corrupted size vs. prev_size while consolidating`. The heap-corruption cause remains unresolved. An upstream issue reports similar corruption on closing the Features view, but was not confirmed to be the same bug.
- `ddcui` showed “Expected value: 50; Reported value: 60” for brightness. A command-line write followed by a two-second delayed read returned 50. This suggests a possible timing issue but does not prove its cause.
- The `QSocketNotifier` warning was observed; its relationship to either error was not established.
- Installed packages matched Ubuntu repository candidates at the time; build/runtime library version differences alone did not demonstrate incompatibility.
- The captured GDB trace showed `QDialog::exec()` after Ctrl+C, consistent with waiting in the popup. It did not capture the heap-corruption crash. To investigate that crash, allow GDB to stop on the actual failure rather than interrupting a live dialog.
- `setup.py` installed custom GNOME shortcuts for `XF86MonBrightnessUp/Down`. They saved successfully but did not control brightness. Raw input monitoring confirmed standard brightness key events. GNOME interception was suspected, not independently proven. The direct input service works and the installers remove those legacy shortcuts.
- GNOME 50 restricts native `ShowOSD` calls to selected desktop components. The local extension supplies a separate method that invokes the native OSD manager. No unsafe Shell mode is needed.
- After the final `ProtectHome=read-only` change, the adopter confirmed the overlay works.

## Files, permissions, and lifecycle

| Location | Purpose |
| --- | --- |
| `/usr/local/libexec/ddc-brightness-keys.py` | Root-owned installed listener; runs as the service's configured user. |
| `/etc/systemd/system/ddc-brightness-keys.service` | System service definition. |
| `/var/cache/ddc-brightness-keys` | Writable service cache managed by systemd. |
| `~/.local/share/gnome-shell/extensions/ddc-brightness-osd@argon-one-up.local/` | Per-user overlay extension. |

The service receives supplementary `input` and `i2c` groups without adding your account permanently to `input`. Input-group access permits reading input devices; the implementation filters for brightness-capable devices, ignores other key events, and logs no ordinary keystrokes. It opens those devices without grabbing them. GNOME may still display its own response to the same keys. The service runs even outside a logged-in desktop session; overlay calls can fail harmlessly when GNOME is absent.

The extension exports its method on the session bus and allows session clients to request an overlay percentage. It does not change monitor brightness itself. The system service has `NoNewPrivileges=true`, a read-only system/home view, and a private temporary directory. Home files are readable according to the user's normal permissions; `ProtectHome=read-only` does not hide them.

Installers copy files: editing a source file here does not update the running installation. Rerun `install.sh` for listener/service changes or `install-osd.sh` for overlay/service changes. Reinstalling is intended to be repeatable. The latter prints an enablement message if the enable command succeeds; check `gnome-extensions info` for actual ACTIVE state.

If upgrading from the initial prototype, the extension UUID and D-Bus interface have changed to project identifiers. In GNOME's Extensions application, disable the previous **DDC Brightness Overlay** instance before running `install-osd.sh`. Log out/in if necessary, then enable `ddc-brightness-osd@argon-one-up.local`. Update the listener and extension together so their interface names match. The service name is unchanged.

## Disable or remove

Stop key control and disable the overlay:

```bash
sudo systemctl disable --now ddc-brightness-keys
gnome-extensions disable ddc-brightness-osd@argon-one-up.local
```

For full removal, run from this source folder as your desktop user:

```bash
python3 setup.py --undo
sudo rm -f /etc/systemd/system/ddc-brightness-keys.service
sudo rm -f /usr/local/libexec/ddc-brightness-keys.py
sudo systemctl daemon-reload
gnome-extensions uninstall ddc-brightness-osd@argon-one-up.local
sudo rm -rf /var/cache/ddc-brightness-keys
```

Stop/disable first. Installed dependency packages and any manually added `i2c` membership remain; other monitor tools may use them.

## References

- [ddcutil device permissions](https://www.ddcutil.com/i2c_permissions/)
- [Group-based I²C access](https://www.ddcutil.com/i2c_permissions_using_group_i2c/)
- [Relative brightness writes with setvcp](https://www.ddcutil.com/command_setvcp/)
- [ddcutil performance and tuning](https://www.ddcutil.com/performance_options/)
- [ddcutil release notes, including skip-ddc-checks](https://www.ddcutil.com/release_notes/)
- [Similar ddcui heap-corruption report, issue 74](https://github.com/rockowitz/ddcui/issues/74)
- [GNOME Shell D-Bus implementation and sender restrictions](https://github.com/GNOME/gnome-shell/blob/main/js/ui/shellDBus.js)
- [systemd service execution and isolation settings](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)

The source files passed Python compilation, shell syntax, and metadata JSON checks during setup. Hardware behavior and final overlay success were confirmed interactively by the adopter. Automated hardware tests, other GNOME versions, and reboot behavior were not validated in this session.
