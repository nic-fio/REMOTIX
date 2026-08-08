#!/bin/bash
set -u
export DISPLAY=:113
D=/srv/remotix/tmp/schermo-client
rm -rf $D; mkdir -p $D
for i in $(seq -w 1 70); do
    xwd -root -silent > $D/$i.xwd 2>/dev/null
    sleep 0.07
done
echo "70 istantanee"
