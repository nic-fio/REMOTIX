#!/bin/bash
set -u
export XDG_RUNTIME_DIR=/tmp/rt
rm -f /tmp/uscita.wav
setsid nohup pw-record --target uscita --rate 44100 --channels 2 --format s16 \
    /tmp/uscita.wav >/dev/null 2>&1 </dev/null &
echo $! > /tmp/rec.pid
echo "   registrazione avviata"
