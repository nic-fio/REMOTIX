#!/bin/bash
# Mette la connessione sotto monitoraggio, per la prova con mstsc.
#
# Due spie, e servono tutte e due:
#   - il registro di FreeRDP a DEBUG sul nucleo, che scrive OGNI Data PDU
#     ricevuto dal client: e' cosi' che si vede che cosa arriva minimizzando;
#   - lo stato del socket ogni mezzo secondo: se il client smette di leggere,
#     la coda di spedizione cresce e la finestra dell'altro capo va a zero.
#     Il registro da solo non lo direbbe.
set -u
BASE=/media/REMOTIX
vm() { bash "$BASE/vm.sh" ssh "$@" </dev/null; }

vm "sudo tee /etc/default/remotix >/dev/null <<'CONF'
REMOTIX_OPZIONI=--registro diagnostica
WLOG_LEVEL=INFO
WLOG_FILTER=com.freerdp.core.rdp:DEBUG,com.freerdp.core.update:DEBUG,com.freerdp.core.peer:DEBUG
CONF
rm -f ~/remotix.log /tmp/socket.log
sudo systemctl restart remotix.service
sleep 2
systemctl is-active remotix.service"

vm "sudo systemctl stop spia-socket.service 2>/dev/null
sudo systemd-run --unit=spia-socket --collect /bin/bash -c '
  while true; do
    printf \"%s \" \"\$(date +%H:%M:%S.%3N)\" >> /tmp/socket.log
    ss -tinm state established \"( sport = :3389 )\" 2>/dev/null | tr \"\n\" \" \" >> /tmp/socket.log
    echo >> /tmp/socket.log
    sleep 0.5
  done' >/dev/null 2>&1
sleep 1
systemctl is-active spia-socket.service"
