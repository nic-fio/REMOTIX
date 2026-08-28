#!/bin/bash
set -u
export XDG_RUNTIME_DIR=/tmp/rt
pkill -x xfreerdp3 2>/dev/null; sleep 1
cd /srv/remotix/tmp/banco-b || exit 1
rm -f spia.log
setsid nohup env DISPLAY=:110 XDG_RUNTIME_DIR=/tmp/rt xfreerdp3 \
    /v:127.0.0.1:3389 /gfx:AVC420 /cert:ignore /sec:tls /u:prova /p:prova \
    /size:1280x800 /sound /log-level:WARN \
    /log-filters:com.freerdp.channels.rdpsnd.client:TRACE >spia.log 2>&1 </dev/null &
sleep 8
echo "   client con spia avviato"
