#!/bin/bash
# $1 = codec (AVC420 | RFX)   $2 = nome del registro del client
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb :112' 2>/dev/null; sleep 1
Xvfb :112 -screen 0 3000x1400x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd /srv/remotix/tmp/banco-b || exit 1
rm -f "$2"
#  serve alla sezione 5: senza, trascinare la finestra non
# manda alcun MONITOR_LAYOUT e il ridimensionamento non si puo' nemmeno provare.
# Alle altre sezioni non cambia niente, perche' la finestra non si tocca.
setsid nohup env DISPLAY=:112 xfreerdp3 /v:127.0.0.1:3389 /gfx:$1 \
    /cert:ignore /sec:tls /u:prova /p:prova /size:1600x900 /dynamic-resolution \
    /title:REMOTIXFASE9 /log-level:INFO >"$2" 2>&1 </dev/null &
sleep 8
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato in $1" || echo "   client NON partito"
