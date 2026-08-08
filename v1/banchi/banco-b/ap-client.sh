#!/bin/bash
# Avvia il client.  Senza argomenti riusa l'Xvfb che c'e' gia'.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
pkill -x xfreerdp3 2>/dev/null
pgrep -f '^Xvfb :110' >/dev/null || {
    Xvfb :110 -screen 0 2400x1600x24 -nolisten tcp >/dev/null 2>&1 &
    sleep 2
}
cd /srv/remotix/tmp/banco-b || exit 1
setsid nohup env DISPLAY=:110 XDG_RUNTIME_DIR=/tmp/rt xfreerdp3 \
    /v:127.0.0.1:3389 /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \
    /size:1280x800 /clipboard /log-level:WARN >ap-client.log 2>&1 </dev/null &
sleep 7
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato" || echo "   client NON partito"
