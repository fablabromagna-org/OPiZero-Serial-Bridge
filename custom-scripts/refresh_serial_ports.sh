#!/bin/bash

sleep 0.5

OUT="/etc/OliveTin/entities/serial_ports.yaml"
TMP="${OUT}.tmp"

{
    for dev in /dev/ttyUSB* /dev/ttyACM*; do
        [ -e "$dev" ] || continue

        name=$(basename "$dev")

        echo "- name: $name"
        echo "  device: $dev"
    done
} > "$TMP"

mv "$TMP" "$OUT"
