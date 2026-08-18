# Optional SPI TFT Display

The optional 1.8-inch ST7735 SPI display shows Ethernet and Wi-Fi IPv4 addresses, the associated SSID, and whether `esp_rfc2217_server` is running.

## Wiring

The reference display is a 128x160 ST7735 module wired to the Orange Pi Zero as follows:

| Display pin | Orange Pi pin | GPIO |
| --- | --- | --- |
| BL | 26 | PA10 through BC557B |
| CS | 24 | PA13 |
| DC | 15 | PA3 |
| RESET | 22 | PA2 |
| SDA/MOSI | 19 | PA15 |
| CLK | 23 | PA14 |
| VCC | 17 | 3V3 |
| GND | 20 or 25 | GND |

Use 3.3 V logic and power. Verify the pinout for the specific SBC revision before connecting hardware.

## Backlight Control

The backlight is controlled through PA10 on physical pin 26. Do not connect `BL` directly to the GPIO: use a BC557B PNP transistor as a high-side switch.

See KiCAD directory for schema.

The display manager uses `GPIO.BOARD` numbering and initializes pin 26 as an active-low backlight output. The backlight turns on when PA10 is low and turns off when PA10 is high or released.


## Enable SPI

On the reference Armbian Debian Trixie system, add the SPI overlay settings to `/boot/armbianEnv.txt`:

```text
overlays=... spi-spidev
param_spidev_spi_bus=1
param_spidev_spi_cs=0
param_spidev_max_freq=32000000
```

Reboot and verify that `/dev/spidev1.0` exists:

```bash
ls -l /dev/spidev*
```

## Install Dependencies and Script

Activate the shared virtual environment and install the display dependencies:

```bash
apt install python3-pil
source /opt/custom-env/bin/activate
pip install luma.lcd spidev gpiod OPi.GPIO
```

Install the display script:

```bash
install -d -m 755 /opt/custom-scripts
install -m 755 custom-scripts/display_manager.py /opt/custom-scripts/display_manager.py
```

Before starting it, edit `/opt/custom-scripts/display_manager.py` if interface names, SPI bus, chip-select, GPIO pins, or display orientation differ from the reference hardware.

## Display Events

Local scripts can show a temporary or persistent message by writing an event ID to `/run/sbc-serial-bridge/display-event`. The display manager polls this file every 200 ms and renders known events as a full-screen overlay.

Events are configured in the `DISPLAY_EVENTS` dictionary. Each event defines display lines and a timeout in seconds. A timeout of `0` remains active until the event file is removed or replaced; a positive timeout returns to the normal status screen after it expires.

The current event is `SHUTDOWN_PROGRESS`, which is written by `shutdown.sh` before system shutdown. The manager intercepts `SIGTERM`, clears the display, and turns off the PA10-controlled backlight during service shutdown.

## systemd Service

Create `/etc/systemd/system/tft-display-manager.service`:

```ini
[Unit]
Description=SBC Display Manager
After=network.target
Wants=network.target

[Service]
Type=simple
WorkingDirectory=/opt/custom-scripts
ExecStart=/opt/custom-env/bin/python3 /opt/custom-scripts/display_manager.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable --now tft-display-manager.service
systemctl status tft-display-manager.service
```
