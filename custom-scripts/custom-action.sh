#!/bin/bash

STATE_DIR=/run/sbc-serial-bridge
DISPLAY_EVENT="$STATE_DIR/display-event"

mkdir -p "$STATE_DIR"
printf '%s\n' "DUMMY" > "$DISPLAY_EVENT.$$"
mv -f "$DISPLAY_EVENT.$$" "$DISPLAY_EVENT"

echo "Custom action"
