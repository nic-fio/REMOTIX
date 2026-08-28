#!/bin/bash
# Tre trascinamenti BEN DISTANZIATI: 3 s fra l'uno e l'altro, cioe' molto piu'
# del mezzo secondo che il server impiega ad applicare.  Se il ping-pong non
# compare qui, il fattore che lo innesca e' l'arrivo di una richiesta MENTRE un
# ridimensionamento e' in volo.
set -u
BANCO=/srv/remotix/tmp/banco-b
D=:110
ID=$(cat $BANCO/fase6-finestra)
for m in "1500 860" "1300 760" "1420 820"; do
    set -- $m
    DISPLAY=$D xdotool windowsize $ID $1 $2
    sleep 3
done
echo "tre trascinamenti distanziati mandati"
for i in 1 2 3 4 5 6; do
    sleep 3
    echo "  t+$((i*3))s  $(DISPLAY=$D xdotool getwindowgeometry $ID 2>/dev/null | grep Geometry)"
done
