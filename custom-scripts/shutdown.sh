#!/bin/bash

# Notify local services before requesting a controlled system shutdown.
STATE_DIR=/run/opizero-serial-bridge
DISPLAY_NOTICE="$STATE_DIR/display-notice"
MESSAGE="System shutdown requested"

mkdir -p "$STATE_DIR"
printf '%s\n' "$MESSAGE" > "$DISPLAY_NOTICE"
logger -t shutdown-script "$MESSAGE"

if command -v telegram-send >/dev/null 2>&1; then
  telegram-send "OPiZero Serial Bridge: $MESSAGE" || \
    logger -t shutdown-script "Telegram notification failed"
fi

# Give the display manager and Telegram client time to handle the notification.
sleep 3
exec /usr/bin/systemctl poweroff
