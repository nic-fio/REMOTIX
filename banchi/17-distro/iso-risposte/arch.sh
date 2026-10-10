#!/bin/bash
# REMOTIX phase 17 — Arch from the official ISO: archinstall with a configuration file.
# The ISO itself launches it ("script=" kernel parameter, on tty1 with automatic
# login). The output also goes to the serial port, which 17-vm.sh writes to console.log.
# Placeholders filled in by 17-vm.sh: @WEB@
exec > >(tee -a /dev/ttyS0 /root/rx-installa.log) 2>&1
echo "RX-ARCH: start $(date)"
archinstall --version 2>/dev/null || pacman -Q archinstall
# the network and the clock, first of all
for i in $(seq 60); do curl -fsS -o /dev/null https://archlinux.org && break; sleep 5; done
timedatectl set-ntp true
archinstall --config-url @WEB@/config.json --creds-url @WEB@/creds.json --silent
rc=$?
echo "RX-ARCH: archinstall rc=$rc"
if [ "$rc" != 0 ]; then
	tail -60 /var/log/archinstall/install.log 2>/dev/null
	echo "RX-ESITO: FALLITA"
else
	echo "RX-ESITO: FATTA"
fi
sync
sleep 3
poweroff
