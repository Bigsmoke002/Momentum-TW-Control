# Momentum-TW-Control

A Linux desktop control panel for the **Sennheiser MOMENTUM True Wireless 5** earbuds,
written in Python with PyQt6. It talks to the earbuds directly over Bluetooth (BlueZ via
D-Bus, Qualcomm GAIA v3 and Google Fast Pair over RFCOMM) – no smartphone app needed.

> This is an **unofficial** community project. It is not affiliated with, endorsed by or
> supported by Sennheiser / Sonova. "Sennheiser" and "MOMENTUM" are trademarks of their
> respective owners. Use at your own risk.

> Note: the user interface is in **German**.

## Features

- **Dashboard** – connection status, battery of both earbuds and the case (live via
  Fast Pair), audio codec and sample rate, volume
- **ANC** – noise cancellation, transparency mode and related settings
- **Sound** – equalizer with presets, bass boost
- **Smart features** – device settings exposed via GAIA (e.g. battery protection, timers)
- **Spatial audio / DSP** – presets for [EasyEffects](https://github.com/wwmm/easyeffects)
  (created automatically in `~/.local/share/easyeffects/output`)
- **Telemetry** – live log of GAIA events and notifications
- **Settings** – Bluetooth status and diagnostics, reconnect/disconnect, autostart,
  start minimised to the system tray

## Requirements

- Linux with **BlueZ** and **PipeWire** (`pactl`, `wpctl`, `pw-play`)
- Python 3.10+ with **PyQt6** and **dbus-python**
- Optional: EasyEffects (spatial audio / DSP), `blueman-manager` or
  `gnome-control-center` (opening the Bluetooth settings)
- The earbuds must be **paired** with the computer once (e.g. via your desktop's
  Bluetooth settings)

Arch / CachyOS:

```bash
sudo pacman -S python-pyqt6 python-dbus
```

or with pip:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 app.py          # open the window
python3 app.py --tray   # start minimised to the system tray
```

The earbuds are detected automatically by their Bluetooth name (`MOMENTUM TW …`).
If you have several devices with that name, set the address explicitly:

```bash
MOMENTUM_TW_MAC=XX:XX:XX:XX:XX:XX python3 app.py
```

Autostart can be enabled in the settings view; it writes
`~/.config/autostart/momentum-tw-control.desktop` pointing to this folder.

## Project structure

```
app.py                  # main window, tray, wiring
backend/
  bluez_monitor.py      # connection state via BlueZ / D-Bus
  gaia_client.py        # Qualcomm GAIA v3 (RFCOMM channel 12): ANC, EQ, settings
  fastpair_client.py    # Google Fast Pair battery stream (RFCOMM channel 22)
audio/
  spatial_audio.py      # codec info, volume, EasyEffects presets
ui/                     # theme, sidebar and views
resources/icons/        # app icon
```

## Status

Actively developed. Tested on CachyOS (KDE Plasma, PipeWire) with a MOMENTUM True
Wireless 5. Other MOMENTUM models may partially work, but are untested.

## Contributing

Please read [AGENTS.md](AGENTS.md) (also applies to humans). In short: never commit
private data such as device MAC addresses, home paths, IPs or tokens. After cloning, run
`scripts/install-hooks.sh` once – the hooks check every commit and push with
`scripts/check-private.sh`.

## License

[MIT](LICENSE)
