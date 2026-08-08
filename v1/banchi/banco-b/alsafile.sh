#!/bin/bash
# Che cosa il CLIENT consegna al proprio dispositivo audio: si dirotta ALSA su
# un file e lo si guarda.  E' l'ultimo punto in cui il sospetto e' ancora
# diviso fra «arriva storto» e «lo suona storto».
set -u
export XDG_RUNTIME_DIR=/tmp/rt
cat > "$HOME/.asoundrc" <<'RC'
pcm.spia {
    type file
    slave.pcm "null"
    file "/tmp/dal-client.raw"
    format raw
}
RC
echo "   asoundrc in $HOME"
rm -f /tmp/dal-client.raw
pkill -x xfreerdp3 2>/dev/null; sleep 1
cd /srv/remotix/tmp/banco-b || exit 1
setsid nohup env DISPLAY=:110 XDG_RUNTIME_DIR=/tmp/rt xfreerdp3 \
    /v:127.0.0.1:3389 /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \
    /size:1280x800 /sound:sys:alsa,dev:spia /log-level:WARN >alsa.log 2>&1 </dev/null &
sleep 8
pgrep -x xfreerdp3 >/dev/null && echo "   client su ALSA-file avviato" || { echo "   NON partito"; tail -3 alsa.log; }
