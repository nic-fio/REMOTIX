#!/bin/bash
# REMOTIX fase 17 — Arch dall'ISO ufficiale: archinstall con file di configurazione.
# Lo lancia l'ISO stessa (parametro «script=» del kernel, sulla tty1 in accesso
# automatico). L'uscita va anche sulla seriale, che 17-vm.sh scrive in console.log.
# Segnaposti riempiti da 17-vm.sh: @WEB@
exec > >(tee -a /dev/ttyS0 /root/rx-installa.log) 2>&1
echo "RX-ARCH: inizio $(date)"
archinstall --version 2>/dev/null || pacman -Q archinstall
# la rete e l'orologio, prima di tutto
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
