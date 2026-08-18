#!/bin/bash

STATE_DIR=/run/sbc-serial-bridge
CONNECTION_FILE="$STATE_DIR/network-state/connection"
DISPLAY_EVENT="$STATE_DIR/display-event"

mkdir -p "$STATE_DIR"
printf '%s\n' "WIFI_RESET" > "$DISPLAY_EVENT.$$"
mv -f "$DISPLAY_EVENT.$$" "$DISPLAY_EVENT"

connection=$(cat "$CONNECTION_FILE" 2>/dev/null)

if [ -n "$connection" ]; then
  nmcli connection delete "$connection"
fi
