#!/bin/bash
# starts the server in the container and leaves the pid in a file
set -uo pipefail
D=/srv/src/remotix
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7448 \
  --certificati /srv/src/remotix-cert --pagina "$D/pagina.html" \
  --ban /srv/src/remotix-ban > /srv/src/remotix-browser.log 2>&1 &
echo $! > /srv/src/remotix.pid
sleep 2
if [ -d "/proc/$(cat /srv/src/remotix.pid)" ]; then echo "RUNNING pid $(cat /srv/src/remotix.pid)"; else echo "DEAD"; cat /srv/src/remotix-browser.log; exit 2; fi
