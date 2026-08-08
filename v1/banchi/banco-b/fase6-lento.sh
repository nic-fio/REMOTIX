#!/bin/bash
# Tre trascinamenti BEN DISTANZIATI: tre secondi l'uno dall'altro, cioe' molto
# piu' del mezzo secondo che il server impiega ad applicare.  E' il modo in cui
# si ridimensiona davvero — si trascina, ci si ferma, si guarda — e qui la
# misura finale dev'essere ESATTAMENTE l'ultima chiesta.
set -u
ID=$(cat /srv/remotix/tmp/banco-b/fase6-finestra 2>/dev/null)
[ -n "$ID" ] || { echo "   nessuna finestra da ridimensionare"; exit 1; }
for m in "1500 860" "1300 760" "1420 820"; do
    set -- $m
    DISPLAY=:110 xdotool windowsize $ID $1 $2
    sleep 3
done
echo "   tre trascinamenti distanziati, ultimo 1420 x 820"
