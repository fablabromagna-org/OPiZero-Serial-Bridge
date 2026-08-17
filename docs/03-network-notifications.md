# Network Notifications

A NetworkManager dispatcher can notify a Telegram chat when an interface comes up or goes down. It also stores runtime connection information for the OliveTin Wi-Fi disconnect action.

## Configure Telegram

Create a bot token through [BotFather](https://telegram.me/BotFather), then configure `telegram-send` interactively for the destination chat.

```bash
apt install telegram-send
telegram-send --configure
telegram-send --format markdown "Only the *bold* use _italics_"
```

Do not commit the generated Telegram configuration or bot token to this repository.

## Install the Dispatcher

The repository provides the dispatcher as `custom-scripts/90-telegram-network`. Install it in the directory monitored by NetworkManager:

```bash
install -m 700 custom-scripts/90-telegram-network \
  /etc/NetworkManager/dispatcher.d/90-telegram-network
chown root:root /etc/NetworkManager/dispatcher.d/90-telegram-network
```

The installed script contains the following configuration:

```bash
#!/bin/bash

INTERFACE="$1"
EVENT="$2"
STATE_DIR=/run/sbc-serial-bridge/network-state

case "$EVENT" in
  up)
    IP=$(printf '%s\n' "$IP4_ADDRESS_0" | cut -d' ' -f1 | cut -d'/' -f1)

    mkdir -p "$STATE_DIR"
    printf '%s\n' "$IP" > "$STATE_DIR/ip"
    printf '%s\n' "$INTERFACE" > "$STATE_DIR/interface"
    printf '%s\n' "${CONNECTION_ID:-n/a}" > "$STATE_DIR/connection"
    date -Iseconds > "$STATE_DIR/timestamp"

    telegram-send "Network updated
Host: $(hostname)
Interface: $INTERFACE
Event: $EVENT
Wi-Fi: ${CONNECTION_ID:-n/a}

Dashboard: http://$IP:1337"
    ;;
  down)
    telegram-send "Interface disconnected
Host: $(hostname)
Interface: $INTERFACE"
    ;;
esac
```

The script is intentionally installed in NetworkManager's dispatcher directory rather than `custom-scripts/`, because NetworkManager executes dispatchers only from this path.

## Notes

The dispatcher receives events only for interfaces managed by NetworkManager. In the reference system, it manages Wi-Fi but not Ethernet. The `/run/sbc-serial-bridge/network-state` directory is volatile and is recreated after each boot or successful `up` event.

The dashboard URL uses HTTP in this example. Enable HTTPS or restrict network access before using it beyond a trusted LAN.
