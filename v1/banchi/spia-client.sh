#!/bin/bash
# Il client di prova dentro il contenitore: apre la sessione e la tiene aperta.
set -u
D=:113
pkill -f "^Xvfb $D" 2>/dev/null; sleep 1
Xvfb $D -screen 0 2200x1400x24 >/dev/null 2>&1 &
sleep 2
cd /srv/remotix/tmp || exit 1
rm -f spia-client.log
setsid nohup env DISPLAY=$D xfreerdp3 /v:127.0.0.1:3392 /gfx:AVC420 \
    /cert:ignore /sec:tls /u:prova /p:prova /size:1280x800 \
    /title:SPIACOPIAZERO /log-level:INFO >spia-client.log 2>&1 </dev/null &
sleep 10
pgrep -x xfreerdp3 >/dev/null && echo "client collegato" || echo "client NON partito"
