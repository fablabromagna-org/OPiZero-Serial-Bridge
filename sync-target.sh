#!/bin/bash

################################################################
# SYNC scripts, services and configuration file to SBC
################################################################

set -euo pipefail

TARGET="${1:-root@192.168.10.54}"
SSH_OPTIONS=(-o BatchMode=yes -o ConnectTimeout=10)

for command in rsync ssh; do
  command -v "$command" >/dev/null 2>&1 || {
    printf 'Required command not found: %s\n' "$command" >&2
    exit 1
  }
done

ssh "${SSH_OPTIONS[@]}" "$TARGET" \
  'install -d -m 755 /opt/custom-scripts /etc/systemd/system /etc/OliveTin /etc/NetworkManager/dispatcher.d'

rsync -a --chown=root:root --chmod=D755,F755 \
  --exclude='__pycache__/' --exclude='*.pyc' \
  -e "ssh ${SSH_OPTIONS[*]}" \
  custom-scripts/ "$TARGET:/opt/custom-scripts/"

rsync -a --chown=root:root --chmod=D755,F644 \
  -e "ssh ${SSH_OPTIONS[*]}" \
  systemd_scripts/system/ "$TARGET:/etc/systemd/system/"

rsync -a --chown=root:root --chmod=F644 \
  -e "ssh ${SSH_OPTIONS[*]}" \
  OliveTinConfig/config.yaml "$TARGET:/etc/OliveTin/config.yaml"

rsync -a --chown=root:root --chmod=F700 \
  -e "ssh ${SSH_OPTIONS[*]}" \
  custom-scripts/90-telegram-network \
  "$TARGET:/etc/NetworkManager/dispatcher.d/90-telegram-network"

read -r -p "Reload services? [y/N] " answer || answer=""

case "$answer" in
  [Yy]|[Yy][Ee][Ss])
    ssh "${SSH_OPTIONS[@]}" "$TARGET" '
      systemctl daemon-reload
      systemctl try-restart tft-display-manager.service
      systemctl try-restart button-manager.service
      systemctl try-restart OliveTin
    '
    ;;
  *)
    printf 'Service reload skipped.\n'
    ;;
esac

printf 'Deployment completed: %s\n' "$TARGET"
