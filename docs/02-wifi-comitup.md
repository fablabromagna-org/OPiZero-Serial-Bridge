# Wi-Fi Onboarding with Comitup

Comitup starts a temporary access point when the SBC has no usable Wi-Fi connection. Connect to that access point, open its captive portal, select an SSID, and provide the passphrase. Comitup then stops the access point and connects as a Wi-Fi client.

## Install and Prepare Network Services

Comitup uses NetworkManager. The following commands reflect the reference Armbian setup; review existing network services before disabling them on another distribution.

```bash
apt install comitup dnsmasq
rm /etc/network/interfaces
systemctl disable dnsmasq.service
systemctl disable systemd-resolved.service
systemctl disable dhcpd.service
systemctl disable dhcpcd.service
systemctl disable wpa-supplicant.service
systemctl enable NetworkManager.service
```

## Configure the Access Point

Edit `/etc/comitup.conf` and configure an ASCII-only access-point name:

```yaml
ap_name: opizero
verbose: 1
```

Restart Comitup. With the default configuration, the access point uses `10.41.0.1`; open `http://10.41.0.1` if captive-portal detection does not open the page automatically.

After valid credentials are submitted, Comitup attempts the client connection. If the connection fails, it recreates the access point.

## AP and Client Mode Workaround

Some Wi-Fi drivers cannot scan while operating an access point. For the Orange Pi Zero reference hardware, configure a callback that creates a temporary managed interface only while the hotspot is active.

Add the following settings to `/etc/comitup.conf`:

```yaml
external_callback: /opt/custom-scripts/comitup-callback
primary_wifi_device: wlan0
```

Install the callback from this repository:

```bash
install -d -m 755 /opt/custom-scripts
install -m 755 custom-scripts/comitup-callback /opt/custom-scripts/comitup-callback
systemctl restart comitup
```

The script assumes `phy0` and `wlan0`. Adjust those values for a different wireless driver or interface name.

## Disconnecting from Wi-Fi

Comitup does not provide a connection-disconnect command. Use NetworkManager instead:

```bash
nmcli connection down "<connection-name>"
```

The connection name is saved by the dispatcher documented in [Network Notifications](03-network-notifications.md).
