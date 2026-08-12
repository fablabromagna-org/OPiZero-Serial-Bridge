USB_PORT="$1"
BAUD="$2"
exec ser2net -n -d \
  -Y "connection: &esp" \
  -Y "  accepter: telnet(rfc2217),tcp,4000" \
  -Y "  connector: serialdev,${USB_PORT},${BAUD}n81,local"
