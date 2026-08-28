#!/bin/bash
# $1 = codec (AVC420 | RFX)   $2 = nome del registro del client
set -u
pkill -f '^Xvfb :112' 2>/dev/null; sleep 1
Xvfb :112 -screen 0 3000x1400x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd /srv/remotix/tmp/banco-b || exit 1
rm -f "$2"
setsid nohup env DISPLAY=:112 xfreerdp3 /v:127.0.0.1:3389 /gfx:$1 \
    /cert:ignore /sec:tls /u:prova /p:prova /size:2560x984 \
    /title:REMOTIXFASE9 /log-level:INFO >"$2" 2>&1 </dev/null &
sleep 5
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato in $1" || echo "   client NON partito"
