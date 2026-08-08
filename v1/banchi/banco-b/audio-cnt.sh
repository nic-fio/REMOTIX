#!/bin/bash
# Accende un impianto audio finto dentro il contenitore, per il banco.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
pkill -x pipewire 2>/dev/null; pkill -x wireplumber 2>/dev/null; pkill -x pipewire-pulse 2>/dev/null
sleep 1
setsid nohup pipewire        >/tmp/pw.log 2>&1 </dev/null &
sleep 1
setsid nohup wireplumber     >/tmp/wp.log 2>&1 </dev/null &
setsid nohup pipewire-pulse  >/tmp/pp.log 2>&1 </dev/null &
sleep 2
pw-cli create-node adapter '{ factory.name=support.null-audio-sink node.name=uscita node.description=USCITA media.class=Audio/Sink object.linger=true audio.position=[FL,FR] }' >/dev/null 2>&1
sleep 2
echo "== grafo del contenitore"
wpctl status 2>&1 | sed -n '/Audio/,/Video/p' | head -20
