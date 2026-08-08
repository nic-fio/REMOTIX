#!/bin/bash
# REMOTIX nel contenitore, scena sintetica.  $1 = opzioni in piu'
set -u
pkill -f "remotix --porta 3390" 2>/dev/null; sleep 1
cd /srv/remotix/tmp/banco-b || exit 1
rm -f fase7-cnt.log
setsid nohup /srv/src/remotix-c/build/src/remotix --porta 3390 --registro traccia \
    --senza-autenticazione --immagine-di-prova $1 >fase7-cnt.log 2>&1 </dev/null &
sleep 2
pgrep -f "remotix --porta 3390" >/dev/null \
    && echo "   REMOTIX avviato sulla 3390 $1" \
    || { echo "   NON avviato"; exit 1; }
