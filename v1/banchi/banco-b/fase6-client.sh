#!/bin/bash
# $1 = porta   $2 = nome del registro del client
set -u
pkill -f '^Xvfb :110' 2>/dev/null; sleep 1
Xvfb :110 -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd /srv/remotix/tmp/banco-b || exit 1
rm -f "$2"
setsid nohup env DISPLAY=:110 xfreerdp3 /v:127.0.0.1:$1 /gfx:AVC420 \
    /cert:ignore /sec:tls /u:prova /p:prova /size:1282x802 /dynamic-resolution \
    /title:REMOTIXFASE6 /log-level:INFO >"$2" 2>&1 </dev/null &
sleep 8
ID=$(DISPLAY=:110 xdotool search --name REMOTIXFASE6 2>/dev/null | head -1)
[ -n "$ID" ] && echo "   finestra del client: $ID" || echo "   NESSUNA finestra trovata"
echo "$ID" > /srv/remotix/tmp/banco-b/fase6-finestra
