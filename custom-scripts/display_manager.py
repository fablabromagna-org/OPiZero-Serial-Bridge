#!/usr/bin/env python3

"""Display network and RFC2217 status on an ST7735 SPI TFT display."""

import subprocess
import time

import OPi.GPIO as GPIO
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont


# Display and network configuration.
ETH_IFACE = "end0"
WLAN_IFACE = "wlan0"
RFC2217_PROCESS = "esp_rfc2217_server"

NETWORK_UPDATE_INTERVAL = 5.0
DISPLAY_UPDATE_INTERVAL = 0.05

SCROLL_SPEED = 1
SCROLL_GAP = 25


# GPIO and display setup.
GPIO.setmode(GPIO.BOARD)

serial = spi(
    port=1,
    device=0,
    gpio_DC=15,
    gpio_RST=22,
    gpio=GPIO,
    bus_speed_hz=8000000,
)

device = st7735(
    serial,
    width=160,
    height=128,
    rotate=0,
    bgr=True,
    gpio=GPIO,
    backlight=None,
)

font = ImageFont.load_default()


def get_ip(interface):
    """Return the interface IPv4 address, or 'n/a' if unavailable."""
    try:
        result = subprocess.run(
            ["ip", "-4", "-o", "addr", "show", "dev", interface],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode != 0:
            return "n/a"

        for line in result.stdout.splitlines():
            parts = line.split()
            if "inet" in parts:
                return parts[parts.index("inet") + 1].split("/")[0]
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
            timeout=2,
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
    """Return True when a process command line contains process_name."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", process_name],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_text_width(draw, text):
    """Return text width in pixels."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


eth_ip = "n/a"
wlan_ip = "n/a"
essid = "n/a"
rfc2217_running = False
scroll_x = 0
last_network_update = 0

try:
    while True:
        now = time.monotonic()

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

        image = Image.new("RGB", (device.width, device.height), "black")
        draw = ImageDraw.Draw(image)
        draw.rectangle(
            (0, 0, device.width - 1, device.height - 1), outline="white"
        )
        draw.text((5, 5), "OPiZero Active", fill="white", font=font)
        draw.text((5, 30), "ETH:", fill="white", font=font)
        draw.text((40, 30), eth_ip, fill="white", font=font)
        draw.text((5, 50), "WLAN:", fill="white", font=font)
        draw.text((40, 50), wlan_ip, fill="white", font=font)

        label_x = 5
        text_x = 40
        text_y = 70
        draw.text((label_x, text_y), "SSID:", fill="white", font=font)

        right_margin = 5
        viewport_width = device.width - text_x - right_margin
        viewport_height = 12
        essid_width = get_text_width(draw, essid)

        if essid_width <= viewport_width:
            draw.text((text_x, text_y), essid, fill="white", font=font)
            scroll_x = 0
        else:
            # Render into a separate viewport to avoid overwriting the label.
            viewport = Image.new("RGB", (viewport_width, viewport_height), "black")
            viewport_draw = ImageDraw.Draw(viewport)
            viewport_draw.text((-scroll_x, 0), essid, fill="white", font=font)
            viewport_draw.text(
                (-scroll_x + essid_width + SCROLL_GAP, 0),
                essid,
                fill="white",
                font=font,
            )
            image.paste(viewport, (text_x, text_y))
            scroll_x += SCROLL_SPEED

            if scroll_x >= essid_width + SCROLL_GAP:
                scroll_x = 0

        draw.text((5, 90), "RFC2217:", fill="white", font=font)
        draw.text(
            (55, 90), "ON" if rfc2217_running else "OFF", fill="white", font=font
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

    GPIO.cleanup()
