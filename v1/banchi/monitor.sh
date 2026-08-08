#!/bin/bash
# Campiona il server mentre l'utente guarda: tempo di CPU e fotogrammi spediti,
# una riga al secondo.  Non giudica niente — serve solo ad avere dei numeri
# accanto a un'impressione, che e' l'unica cosa che manca quando il sintomo lo
# vede un occhio e non un contatore.
set -u
DURATA=${1:-900}
for i in $(seq 1 "$DURATA"); do
    P=$(systemctl show -p MainPID --value remotix.service 2>/dev/null)
    [ "${P:-0}" = 0 ] && { echo "$(date +%H:%M:%S) SERVER-GIU"; sleep 1; continue; }
    T=$(awk '{print $14+$15}' "/proc/$P/stat" 2>/dev/null)
    F=$(grep -F 'rete: RTT' ~/remotix.log 2>/dev/null | tail -1 \
        | grep -oE 'spediti [0-9]+' | grep -oE '[0-9]+')
    echo "$(date +%H:%M:%S) tick=${T:-0} spediti=${F:-0}"
    sleep 1
done
