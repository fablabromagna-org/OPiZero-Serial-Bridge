#!/usr/bin/env python3

#######################################################################
#
# Display IP and WiFi SSID to a SPI TFT Display 
# 
#######################################################################



import subprocess
import os
import signal
import time

import OPi.GPIO as GPIO

from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont


# Display and network configuration
ETH_IFACE = "end0"
WLAN_IFACE = "wlan0"
RFC2217_PROCESS = "esp_rfc2217_server"
DISPLAY_EVENT_FILE = "/run/sbc-serial-bridge/display-event"

NETWORK_UPDATE_INTERVAL = 5.0
DISPLAY_UPDATE_INTERVAL = 0.05
DISPLAY_EVENT_UPDATE_INTERVAL = 0.2

SCROLL_SPEED = 1
SCROLL_GAP = 25

DISPLAY_EVENTS = {
    "SHUTDOWN_PROGRESS": {
        "lines": (
            "SYSTEM SHUTDOWN",
            "IN PROGRESS...",
        ),
        "timeout": 0,
    },
    "WIFI_RESET": {
        "lines": (
            "Reset WiFi",
            "Activate AP mode",
        ),
        "timeout": 3,
    },
    "DUMMY": {
        "lines": (
            "Dummy command",
            "just for test",
        ),
        "timeout": 3,
    },

}


# GPIO / display setup
GPIO.setmode(GPIO.BOARD)

serial = spi(
    port=1,
    device=0,
    gpio_DC=15,
    gpio_RST=22,
    gpio=GPIO,
    bus_speed_hz=8000000
)

device = st7735(
    serial,
    width=160,
    height=128,
    rotate=0,
    bgr=True,
    gpio=GPIO,
    gpio_LIGHT=26,
    active_low=True
)

font = ImageFont.load_default()


def get_ip(interface):
    """Return the interface IPv4 address, or 'n/a' if unavailable."""

    try:
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show", "dev", interface],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            return "n/a"

        for line in result.stdout.splitlines():
            parts = line.split()

            if "inet" in parts:
                index = parts.index("inet")
                return parts[index + 1].split("/")[0]

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "n/a"


def get_essid(interface):
    """Return the Wi-Fi SSID, or 'n/a' if not associated."""

    try:
        result = subprocess.run(
            ["iw", "dev", interface, "link"],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            return "n/a"

        for line in result.stdout.splitlines():
            line = line.strip()

            if line.startswith("SSID:"):
                essid = line.split(":", 1)[1].strip()

                if essid:
                    return essid

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return "n/a"


def is_process_running(process_name):
    """Return True if the process command line contains process_name."""

    try:
        result = subprocess.run(
            ["pgrep", "-f", process_name],
            capture_output=True,
            text=True,
            timeout=2
        )

        return result.returncode == 0

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False



def get_text_width(draw, text):
    """Return text width in pixels."""

    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def get_display_event():
    """Return the current event ID and the file modification time."""

    try:
        event_stat = os.stat(DISPLAY_EVENT_FILE)

        with open(DISPLAY_EVENT_FILE, encoding="ascii") as event_file:
            return event_file.read().strip(), event_stat.st_mtime

    except OSError:
        return "", 0


def is_display_event_active(event_id, event_mtime):
    """Return True if the configured display event has not expired."""

    event = DISPLAY_EVENTS.get(event_id)

    if not event:
        return False

    timeout = event["timeout"]
    return timeout == 0 or time.time() - event_mtime < timeout


def terminate(signum, frame):
    """Exit through the cleanup path when systemd stops the service."""

    raise SystemExit(0)


eth_ip = "n/a"
wlan_ip = "n/a"
essid = "n/a"
rfc2217_running = False

scroll_x = 0
last_network_update = 0
display_event_id = ""
display_event_mtime = 0
last_display_event_update = 0

signal.signal(signal.SIGTERM, terminate)


try:
    while True:

        now = time.monotonic()

        if now - last_display_event_update >= DISPLAY_EVENT_UPDATE_INTERVAL:
            display_event_id, display_event_mtime = get_display_event()
            last_display_event_update = now

        # Refresh network information at a lower rate than the display.
        if now - last_network_update >= NETWORK_UPDATE_INTERVAL:

            new_eth_ip = get_ip(ETH_IFACE)
            new_wlan_ip = get_ip(WLAN_IFACE)
            new_essid = get_essid(WLAN_IFACE)
            new_rfc2217_running = is_process_running(RFC2217_PROCESS)

            if new_essid != essid:
                scroll_x = 0

            eth_ip = new_eth_ip
            wlan_ip = new_wlan_ip
            essid = new_essid
            rfc2217_running = new_rfc2217_running

            last_network_update = now

        image = Image.new(
            "RGB",
            (device.width, device.height),
            "black"
        )

        draw = ImageDraw.Draw(image)

        draw.rectangle(
            (0, 0, device.width - 1, device.height - 1),
            outline="white"
        )

        if is_display_event_active(display_event_id, display_event_mtime):
            event_lines = DISPLAY_EVENTS[display_event_id]["lines"]
            text_height = 12
            first_line_y = (device.height - len(event_lines) * text_height) // 2

            for index, line in enumerate(event_lines):
                line_x = (device.width - get_text_width(draw, line)) // 2
                line_y = first_line_y + index * text_height
                draw.text((line_x, line_y), line, fill="white", font=font)

            device.display(image)
            time.sleep(DISPLAY_UPDATE_INTERVAL)
            continue

        draw.text(
            (5, 5),
            "OPiZero Active",
            fill="white",
            font=font
        )

        draw.text(
            (5, 30),
            "ETH:",
            fill="white",
            font=font
        )

        draw.text(
            (40, 30),
            eth_ip,
            fill="white",
            font=font
        )

        draw.text(
            (5, 50),
            "WLAN:",
            fill="white",
            font=font
        )

        draw.text(
            (40, 50),
            wlan_ip,
            fill="white",
            font=font
        )

        label_x = 5
        text_x = 40
        text_y = 70

        draw.text(
            (label_x, text_y),
            "SSID:",
            fill="white",
            font=font
        )

        right_margin = 5
        viewport_width = device.width - text_x - right_margin
        viewport_height = 12

        essid_width = get_text_width(draw, essid)

        if essid_width <= viewport_width:

            draw.text(
                (text_x, text_y),
                essid,
                fill="white",
                font=font
            )

            scroll_x = 0

        else:

            # Draw the scrolling text into a separate image so it is
            # clipped to the SSID area and cannot overlap the label.
            viewport = Image.new(
                "RGB",
                (viewport_width, viewport_height),
                "black"
            )

            viewport_draw = ImageDraw.Draw(viewport)

            viewport_draw.text(
                (-scroll_x, 0),
                essid,
                fill="white",
                font=font
            )

            # Draw a second copy to create seamless circular scrolling.
            viewport_draw.text(
                (
                    -scroll_x + essid_width + SCROLL_GAP,
                    0
                ),
                essid,
                fill="white",
                font=font
            )

            image.paste(
                viewport,
                (text_x, text_y)
            )

            scroll_x += SCROLL_SPEED

            if scroll_x >= essid_width + SCROLL_GAP:
                scroll_x = 0

        draw.text(
            (5, 90),
            "RFC2217:",
            fill="white",
            font=font
        )

        draw.text(
            (55, 90),
            "ON" if rfc2217_running else "OFF",
            fill="white",
            font=font
        )

        device.display(image)

        time.sleep(DISPLAY_UPDATE_INTERVAL)


except KeyboardInterrupt:
    pass

finally:
    try:
        device.clear()
    except Exception:
        pass

    try:
        device.backlight(False)
        device.cleanup()
    except Exception:
        pass

    GPIO.cleanup()
