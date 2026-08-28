#!/bin/bash
# $1 = quante raffiche
#
# ⛔ IL FUOCO SI DA' CON `windowfocus`, NON CON `windowactivate`.
#
#    `windowactivate` parla al gestore di finestre via EWMH, e qui un gestore
#    di finestre non c'e': fallisce in silenzio, i tasti vanno al fuoco corrente
#    — che dopo un `windowsize` non e' piu' la nostra finestra — e la scena non
#    si muove.  Il banco allora conta zero fotogrammi e accusa il prodotto di
#    avere lo schermo fermo.  Costato un controllo rosso il 6 agosto, con il
#    codice giusto.  `windowfocus` usa `XSetInputFocus` e non chiede permesso
#    a nessuno; il puntatore dentro la finestra chiude il caso.
set -u
export DISPLAY=:112
ID=$(xdotool search --name REMOTIXFASE9 | head -1)
if [ -z "$ID" ]; then
    echo "   NESSUNA FINESTRA: la scena non si muovera'"
    exit 1
fi
xdotool windowfocus --sync "$ID" 2>/dev/null
xdotool mousemove --window "$ID" 60 60 2>/dev/null
xdotool key super; sleep 1
for i in $(seq 1 $1); do
    xdotool type --delay 25 'remotix fase nove'
    xdotool key BackSpace BackSpace BackSpace BackSpace
done
echo "   scena mossa ($1 raffiche)"
