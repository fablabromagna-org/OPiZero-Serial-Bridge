#!/bin/bash

nmcli connection delete $(cat /run/sbc-serial-bridge/network-state/connection 2>/dev/null)
