# OliveTin Dashboard

[OliveTin](https://github.com/OliveTin/OliveTin) provides a web UI to run controlled administrative actions on the SBC. In this project it starts and stops the RFC2217 server, lists USB serial ports, disconnects Wi-Fi, and provides basic network and storage diagnostics. It avoids keeping the RFC2217 service permanently active and is an alternative to SSH for routine operations.

## Install OliveTin

Download the release package that matches the SBC architecture. The Orange Pi Zero reference platform requires the ARMv7 package.

```bash
wget https://github.com/OliveTin/OliveTin/releases/latest/download/OliveTin_linux_armv7.deb
dpkg -i OliveTin_linux_armv7.deb
```

If `dpkg` reports unresolved package dependencies, repair them with:

```bash
apt --fix-broken install
```

Enable and start the service:

```bash
systemctl enable --now OliveTin
systemctl status OliveTin
```

Open `http://<sbc-ip>:1337/` to verify the installation. The NetworkManager dispatcher described in [Network Notifications](03-network-notifications.md) sends this address by Telegram after a successful Wi-Fi connection.

## Install Custom Icons

The reference configuration uses custom action icons. Create the destination directory and copy the corresponding PNG files before enabling the related actions:

```bash
install -d -m 755 /etc/OliveTin/custom-webui/icons
```

The configuration refers to the following icon files:

```text
custom-webui/icons/wifi_disconnect.png
custom-webui/icons/connected.png
custom-webui/icons/disconnected.png
custom-webui/icons/usb.png
```

Either provide these files under OliveTin's custom web UI directory or replace the `icon` values with built-in OliveTin icon names.

## Configure OliveTin

Back up the generated configuration before replacing it:

```bash
cp /etc/OliveTin/config.yaml /etc/OliveTin/config.yaml.bak
editor /etc/OliveTin/config.yaml
```

The following is the current reference configuration. It listens on port `1337`, uses the Catppuccin theme, and groups serial actions in the `Espressif` dashboard.

```yaml
listenAddressSingleHTTPFrontend: 0.0.0.0:1337
logLevel: "INFO"
themeName: catppuccin-mocha-olivetin
pageTitle: OrangePi-Zero

actions:
  - title: Disconnect WiFi
    id: wifi_disconnect
    shell: nmcli connection down $(cat /run/network-state/connection 2>/dev/null)
    icon: '<img src="custom-webui/icons/wifi_disconnect.png" />'
    onclick: execution-dialog

  - title: Disconnect and forget WiFi
    id: wifi_delete
    shell: nmcli connection delete $(cat /run/network-state/connection 2>/dev/null)
    icon: '<img src="custom-webui/icons/wifi_disconnect.png" />'
    justification: " "
    arguments:
      - type: confirmation
        title: Are you sure?!
    onclick: execution-dialog

  - title: Check disk space
    icon: disk
    shell: df -h /
    onclick: execution-dialog

  - title: Ping the Internet
    shell: ping -c 3 1.1.1.1
    icon: ping
    onclick: execution-dialog
    execOnStartup: true

  - title: Ping host
    id: ping_host
    shell: ping {{ host }} -c {{ count }}
    icon: ping
    timeout: 100
    onclick: history
    execOnWebhook:
      - matchHeaders:
          X-OliveTin-Demo: ping-host
    arguments:
      - name: host
        title: Host
        type: ascii_identifier
        default: example.com
        description: The host to ping
      - name: count
        title: Count
        type: int
        default: 3
        description: Number of packets to send

  - title: Setup easy SSH
    icon: ssh
    shell: olivetin-setup-easy-ssh
    onclick: execution-dialog
    execOnWebhook:
      - matchQuery:
          demo: setup-ssh

  - title: Start RFC2217 Server
    id: rfc2217_start
    shell: nohup /opt/custom-env/bin/esp_rfc2217_server -p 4000 /dev/{{ port }} > /var/log/esp_rfc2217.log 2>&1 &
    arguments:
      - name: port
        description: Select the USB port to use
        choices:
          - title: ttyUSB0
            value: ttyUSB0
          - title: ttyUSB1
            value: ttyUSB1
          - title: ttyUSB2
            value: ttyUSB2
          - title: ttyACM0
            value: ttyACM0
          - title: ttyACM1
            value: ttyACM1
          - title: ttyACM2
            value: ttyACM2
    timeout: 10
    icon: '<img src="custom-webui/icons/connected.png" />'
    onclick: execution-dialog

  - title: Stop RFC2217 Server
    id: rfc2217_stop
    shell: killall esp_rfc2217_server
    icon: '<img src="custom-webui/icons/disconnected.png" />'

  - title: List USB ports
    icon: '<img src="custom-webui/icons/usb.png" />'
    shell: ls -l /dev/tty[AU]*
    onclick: execution-dialog

dashboards:
  - title: Espressif
    category: mcu
    contents:
      - title: Start RFC2217 Server
      - title: Stop RFC2217 Server
      - title: List USB ports

authRequireGuestsToLogin: false
authLocalUsers:
  enabled: true

defaultPolicy:
  showDiagnostics: true
  showLogList: true

defaultPermissions:
  view: true
  exec: true
  logs: true

accessControlLists:
  - name: admin_acl
    matchUsergroups: ["admins"]
    policy:
      showDiagnostics: true
    permissions:
      view: true
      exec: true
      logs: true
```

Reload the configuration after every change:

```bash
systemctl restart OliveTin
systemctl status OliveTin
journalctl -u OliveTin -n 50 --no-pager
```

## Action Dependencies

`Disconnect WiFi` and `Disconnect and forget WiFi` require `/run/network-state/connection`, created by the NetworkManager dispatcher after a successful connection. The runtime directory is cleared at boot, so these actions are unavailable until NetworkManager raises a subsequent `up` event.

`Start RFC2217 Server` requires `esptool` to be installed in `/opt/custom-env`; follow [RFC2217 Serial Service](05-rfc2217.md). The selectable values are limited to known `ttyUSB` and `ttyACM` device names., avoiding arbitrary device-path input. Add or remove choices to match the SBC hardware.

The server output is written to `/var/log/esp_rfc2217.log`. The stop action terminates every `esp_rfc2217_server` process on the SBC; this is appropriate for the single-server reference setup.

## Security

The reference configuration has `authRequireGuestsToLogin: false`. Therefore anyone who can reach port `1337` can execute the exposed actions, including Wi-Fi disconnection and serial-server control. This setting is acceptable only on a restricted, trusted network.

Before exposing OliveTin beyond a trusted LAN, require login, define at least one local user with an Argon2id password hash, and limit the dashboard through a firewall, VPN, HTTPS reverse proxy, or equivalent access controls. Review webhook-triggered actions as well: they permit remote action execution when their match conditions are satisfied.



## TODO

- Better actions to start/stop RFC2217 Server
- Look for a way to display service status in dashboard
- Add login auth 
- Start RFC2217 server only on available USB port
