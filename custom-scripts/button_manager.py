#!/usr/bin/env python3

import logging
import subprocess
import threading
from datetime import timedelta

import gpiod
from gpiod.line import Bias, Direction, Edge


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

GPIO_CHIP = "/dev/gpiochip0"

# GPIO line offsets - CHANGE THESE
BUTTON_P1 = 18
BUTTON_P2 = 19

LONG_PRESS_TIME = 5.0

# External commands
P1_LONG_COMMAND = ["/opt/custom-scripts/reset-wifi.sh"]
P2_LONG_COMMAND = ["/opt/custom-scripts/shutdown.sh"]

P1_SHORT_COMMAND = ["/opt/custom-scripts/reset-esp32.sh"]
P2_SHORT_COMMAND = ["/opt/custom-scripts/custom-action.sh"]


# ----------------------------------------------------------------------
# Logging
# ------------:----------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

log = logging.getLogger("button-manager")


# ----------------------------------------------------------------------
# Button state
# ----------------------------------------------------------------------

timers = {}
long_press_triggered = {}
state_lock = threading.Lock()


# ----------------------------------------------------------------------
# Command execution
# ----------------------------------------------------------------------


def run_command(command):
    """Run an external command without blocking GPIO event processing."""

    try:
        log.info("Executing: %s", " ".join(command))

        subprocess.Popen(
            command,
            start_new_session=True,
        )

    except Exception:
        log.exception("Unable to execute command")


# ----------------------------------------------------------------------
# Button actions
# ----------------------------------------------------------------------


def short_press(button):
    if button == BUTTON_P1:
        log.info("P1: short press")
        run_command(P1_SHORT_COMMAND)

    elif button == BUTTON_P2:
        log.info("P2: short press")
        run_command(P2_SHORT_COMMAND)


def long_press(button):
    with state_lock:
        long_press_triggered[button] = True

    if button == BUTTON_P1:
        log.info("P1: long press")
        run_command(P1_LONG_COMMAND)

    elif button == BUTTON_P2:
        log.info("P2: long press")
        run_command(P2_LONG_COMMAND)


# ----------------------------------------------------------------------
# GPIO event handling
# ----------------------------------------------------------------------


def button_pressed(button):
    """Called on falling edge."""

    log.debug("GPIO %d pressed", button)

    with state_lock:
        # Defensive cleanup in case an old timer still exists
        old_timer = timers.pop(button, None)

        if old_timer:
            old_timer.cancel()

        long_press_triggered[button] = False

        timer = threading.Timer(
            LONG_PRESS_TIME,
            long_press,
            args=(button,),
        )

        timer.daemon = True

        timers[button] = timer
        timer.start()


def button_released(button):
    """Called on rising edge."""

    log.debug("GPIO %d released", button)

    with state_lock:
        timer = timers.pop(button, None)

        if timer:
            timer.cancel()

        was_long_press = long_press_triggered.pop(button, False)

    # If the long press timer did not expire, this is a short press
    if not was_long_press:
        short_press(button)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main():
    buttons = (BUTTON_P1, BUTTON_P2)

    settings = gpiod.LineSettings(
        direction=Direction.INPUT,
        edge_detection=Edge.BOTH,
        bias=Bias.PULL_UP,
        debounce_period=timedelta(milliseconds=30),
    )

    log.info("Starting button manager")
    log.info("GPIO chip: %s", GPIO_CHIP)
    log.info("P1 GPIO offset: %d", BUTTON_P1)
    log.info("P2 GPIO offset: %d", BUTTON_P2)
    log.info("Long press time: %.1f seconds", LONG_PRESS_TIME)

    with gpiod.request_lines(
        GPIO_CHIP,
        consumer="button-manager",
        config={
            buttons: settings,
        },
    ) as request:
        log.info("GPIO lines configured")

        while True:
            # Blocking call:
            # the process sleeps here until a GPIO edge occurs.
            events = request.read_edge_events()

            for event in events:
                button = event.line_offset

                if event.event_type is event.Type.FALLING_EDGE:
                    button_pressed(button)

                elif event.event_type is event.Type.RISING_EDGE:
                    button_released(button)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        log.info("Stopped by user")

    except Exception:
        log.exception("Fatal error")
        raise
