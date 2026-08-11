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

Create `/etc/NetworkManager/dispatcher.d/90-telegram-network` with the following content:

```bash
#!/bin/bash

INTERFACE="$1"
EVENT="$2"

case "$EVENT" in
  up)
    IP=$(printf '%s\n' "$IP4_ADDRESS_0" | cut -d' ' -f1 | cut -d'/' -f1)

    mkdir -p /run/network-state
    printf '%s\n' "$IP" > /run/network-state/ip
    printf '%s\n' "$INTERFACE" > /run/network-state/interface
    printf '%s\n' "${CONNECTION_ID:-n/a}" > /run/network-state/connection
    date -Iseconds > /run/network-state/timestamp

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

Set restrictive ownership and permissions:

```bash
chmod 700 /etc/NetworkManager/dispatcher.d/90-telegram-network
chown root:root /etc/NetworkManager/dispatcher.d/90-telegram-network
```

The script is intentionally installed in NetworkManager's dispatcher directory rather than `custom-scripts/`, because NetworkManager executes dispatchers only from this path.

## Notes

The dispatcher receives events only for interfaces managed by NetworkManager. In the reference system, it manages Wi-Fi but not Ethernet. The `/run/network-state` directory is volatile and is recreated after each boot or successful `up` event.

The dashboard URL uses HTTP in this example. Enable HTTPS or restrict network access before using it beyond a trusted LAN.
