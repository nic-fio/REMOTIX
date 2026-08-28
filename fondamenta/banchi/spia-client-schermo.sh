#!/bin/bash
# Fotografa quel che il CLIENT mostra: 40 istantanee a ~10/s dello schermo
# dell'Xvfb in cui gira xfreerdp3.  E' l'altro capo del filo.
set -u
export DISPLAY=:113
D=/srv/remotix/tmp/schermo-client
rm -rf $D; mkdir -p $D
for i in $(seq -w 1 40); do
    import -window root -silent $D/$i.png 2>/dev/null || xwd -root -silent > $D/$i.xwd 2>/dev/null
    sleep 0.1
done
ls $D | wc -l
