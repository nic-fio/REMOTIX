#!/bin/bash
set -u
BASE=/media/REMOTIX
BANCO=/srv/remotix/tmp/banco-b
vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BASE/src/remotix-c/build/src/remotix" >/dev/null || exit 1
vm "bash avvia-remotix.sh --aperto" | tail -1
cnt "bash $BANCO/fumo8-client.sh"
cnt "bash $BANCO/fumo8-registra.sh"
vm "pw-play /tmp/piano.wav; echo '   tono da 3000 suonato'"
sleep 2
cnt "bash $BANCO/fumo8-esamina.sh"
cnt "bash $BANCO/forma.sh"
cnt "pkill -x xfreerdp3 2>/dev/null; echo '   client chiuso'"
