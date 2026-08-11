# Base System and Prerequisites

These instructions assume an Orange Pi Zero running Armbian or another Debian-derived distribution.  Run the commands as `root` or prefix them with `sudo`.

> The current reference system is `Armbian 26.8.0-trunk.11 trixie`.


## System Packages

Update the package metadata and install the Python tools used by the optional display and RFC2217 components.

```bash
apt update
apt install python3-pip python3-venv
```

## Python Environment

Create one virtual environment for Python packages that are unavailable or outdated in the distribution repositories.

```bash
python3 -m venv  --system-site-packages  /opt/custom-env
source /opt/custom-env/bin/activate
```


## Optional mDNS Hostname Resolution

Avahi makes the SBC reachable by hostname, for example `opizero.local`, on networks that support multicast DNS.

```bash
apt install avahi-daemon avahi-utils libnss-mdns
```

Allow the `.local` domain and ensure that mDNS is listed in the host lookup order.

```bash
tee /etc/mdns.allow > /dev/null <<'EOF'
.local
.local.
EOF

sed -i 's/^hosts:.*/hosts: files mdns4 [NOTFOUND=return] dns myhostname/' /etc/nsswitch.conf
systemctl restart avahi-daemon avahi-daemon.socket
```

Verify resolution from another host on the same LAN:

```bash
getent hosts opizero.local
ping -c 3 opizero.local
```

mDNS is a convenience feature only. The Telegram notification described in [Network Notifications](03-network-notifications.md) provides the assigned IP address when mDNS is unavailable.
