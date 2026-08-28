#!/bin/bash
set -u
BANCO=/srv/remotix/tmp/banco-b
DISPLAY_CLI=:110
mkdir -p $BANCO; cd $BANCO || exit 1
pkill -f "remotix --porta 3390" 2>/dev/null
pkill -x xfreerdp3 2>/dev/null
pkill -f "^Xvfb $DISPLAY_CLI" 2>/dev/null; sleep 1
rm -f f7-srv.log f7-cli.log
setsid nohup /srv/src/remotix-c/build/src/remotix --porta 3390 --registro traccia \
    --senza-autenticazione --immagine-di-prova >f7-srv.log 2>&1 </dev/null &
sleep 2
Xvfb $DISPLAY_CLI -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:3390 /gfx:AVC420 \
    /cert:ignore /sec:tls /u:prova /p:prova /size:1282x802 \
    /title:F7 /log-level:INFO >f7-cli.log 2>&1 </dev/null &
sleep 10
echo "=== registro del server ==="
grep -E "misura della rete|rete: RTT|strozzo|riprendo|sospende|banda misurata|misura di banda avviata" f7-srv.log | head -30
echo "=== quante righe di rete ==="
grep -c "rete: RTT" f7-srv.log
pkill -x xfreerdp3 2>/dev/null
pkill -f "remotix --porta 3390" 2>/dev/null
pkill -f "^Xvfb $DISPLAY_CLI" 2>/dev/null
