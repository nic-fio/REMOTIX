#!/bin/bash
# Muove la scena: apre e chiude la panoramica di GNOME, che e' il cambio di
# schermata piu' grande che si possa provocare senza aprire applicazioni.
set -u
export DISPLAY=:113
W=$(xdotool search --name SPIACOPIAZERO 2>/dev/null | head -1)
[ -n "$W" ] || { echo "finestra del client non trovata"; exit 1; }
xdotool windowactivate --sync "$W" 2>/dev/null
sleep 1
for i in 1 2 3 4 5 6 7 8; do
    xdotool key super;   sleep 0.6
    xdotool key Escape;  sleep 0.6
done
echo "otto aperture/chiusure della panoramica"
