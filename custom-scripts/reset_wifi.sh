#!/bin/bash

nmcli connection delete $(cat /run/network-state/connection 2>/dev/null)
