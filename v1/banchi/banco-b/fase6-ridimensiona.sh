#!/bin/bash
# $1 = larghezza   $2 = altezza   $3 = secondi di attesa dopo
set -u
ID=$(cat /srv/remotix/tmp/banco-b/fase6-finestra 2>/dev/null)
[ -n "$ID" ] || { echo "   nessuna finestra da ridimensionare"; exit 1; }
# ⚠ Il client di FreeRDP non manda piu' di un layout ogni 200 ms
# (RESIZE_MIN_DELAY): una raffica piu' fitta di cosi' la accorpa LUI, e la
# prova misurerebbe il client invece del server.
DISPLAY=:110 xdotool windowsize $ID $1 $2
sleep $3
echo "   finestra portata a $1x$2"
