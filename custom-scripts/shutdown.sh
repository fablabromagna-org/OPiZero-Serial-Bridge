#!/bin/bash

# Notify local services before requesting a controlled system shutdown.
STATE_DIR=/run/sbc-serial-bridge
DISPLAY_EVENT="$STATE_DIR/display-event"
EVENT_ID=SHUTDOWN_PROGRESS
MESSAGE="System shutdown in progress"

mkdir -p "$STATE_DIR"
printf '%s\n' "$EVENT_ID" > "$DISPLAY_EVENT.$$"
mv -f "$DISPLAY_EVENT.$$" "$DISPLAY_EVENT"
logger -t shutdown-script "$MESSAGE"

if command -v telegram-send >/dev/null 2>&1; then
  telegram-send "OPiZero Serial Bridge: $MESSAGE" || \
    logger -t shutdown-script "Telegram notification failed"
fi

# Give the display manager and Telegram client time to handle the notification.
sleep 3
exec /usr/bin/systemctl poweroff
