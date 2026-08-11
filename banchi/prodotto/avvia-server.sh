#!/bin/bash
# accende il server nel contenitore e lascia il pid in un file
set -uo pipefail
D=/srv/src/remotix
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7448 \
  --certificati /srv/src/remotix-cert --pagina "$D/pagina.html" \
  --ban /srv/src/remotix-ban > /srv/src/remotix-browser.log 2>&1 &
echo $! > /srv/src/remotix.pid
sleep 2
if [ -d "/proc/$(cat /srv/src/remotix.pid)" ]; then echo "ACCESO pid $(cat /srv/src/remotix.pid)"; else echo "MORTO"; cat /srv/src/remotix-browser.log; exit 2; fi
