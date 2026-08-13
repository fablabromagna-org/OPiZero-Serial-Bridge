#!/bin/bash

sleep 0.3

OUT="/etc/OliveTin/entities/serial_ports.yaml"

content=""

for dev in /dev/ttyUSB* /dev/ttyACM*; do
    [ -e "$dev" ] || continue

    name=$(basename "$dev")

    printf -v entry -- '- name: %s\n  device: %s\n' "$name" "$dev"
    content+="$entry"
done

printf '%s' "$content" > "$OUT"
