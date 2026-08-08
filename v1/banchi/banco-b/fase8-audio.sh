#!/bin/bash
# L'impianto audio finto del contenitore.  Senza, il client non suona.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
if ! pgrep -x pipewire >/dev/null; then
    setsid nohup pipewire       >/tmp/pw.log 2>&1 </dev/null &
    sleep 1
    setsid nohup wireplumber    >/tmp/wp.log 2>&1 </dev/null &
    setsid nohup pipewire-pulse >/tmp/pp.log 2>&1 </dev/null &
    sleep 2
fi
wpctl status 2>/dev/null | grep -q ' USCITA' || \
    pw-cli create-node adapter '{ factory.name=support.null-audio-sink node.name=uscita node.description=USCITA media.class=Audio/Sink object.linger=true audio.position=[FL,FR] }' >/dev/null 2>&1
sleep 1
wpctl status 2>/dev/null | grep -q ' USCITA' && echo "   impianto audio del contenitore pronto" \
                                             || echo "   impianto audio NON pronto"
