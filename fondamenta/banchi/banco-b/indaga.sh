#!/bin/bash
# Indagine: la raffica innesca un'oscillazione che si autoalimenta?
set -u
BANCO=/srv/remotix/tmp/banco-b
D=:110
ID=$(cat $BANCO/fase6-finestra 2>/dev/null)
echo "finestra $ID"
for m in "1500 860" "1420 820" "1340 780" "1260 740" "1180 700" "1520 880" "1360 800" "1240 720"; do
    set -- $m
    DISPLAY=$D xdotool windowsize $ID $1 $2
    sleep 0.3
done
echo "raffica mandata; da qui in poi NESSUN comando"
for i in $(seq 1 12); do
    sleep 3
    G=$(DISPLAY=$D xdotool getwindowgeometry $ID 2>/dev/null | tr '\n' ' ')
    echo "  t+$((i*3))s  $G"
done
