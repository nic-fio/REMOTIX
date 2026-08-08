#!/bin/bash
# Prova a mano degli appunti, nei due versi.
#
# ⚠ Chi mette qualcosa negli appunti RESTA IN VITA a tenerli (wl-copy, xclip):
#   va staccato, o la sessione ssh che lo ha avviato non si chiude piu'.
set -u
BASE=/media/REMOTIX
BANCO=/srv/remotix/tmp/banco-b
vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

echo "== 1. binario nuovo, server e client"
vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BASE/src/remotix-c/build/src/remotix" >/dev/null || exit 1
vm "bash avvia-remotix.sh --aperto" | tail -1
cnt "bash $BANCO/fumo8-client.sh"

echo "== 2. il canale si e' aperto?"
vm "grep -E 'appunti' ~/remotix.log | tail -4"

echo "== 3. LA SESSIONE COPIA, il client incolla"
vm "pkill -x wl-copy 2>/dev/null; printf 'ciao dal desktop remoto' > /tmp/da-copiare.txt; setsid nohup env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wl-copy < /tmp/da-copiare.txt >/dev/null 2>&1 & sleep 3; echo '   copiato nella sessione'"
sleep 2
vm "grep -E 'appunti:' ~/remotix.log | tail -2"
cnt "DISPLAY=:110 timeout 10 xclip -selection clipboard -o 2>&1 | head -2 | sed 's/^/   il client legge: /'"

echo "== 4. IL CLIENT COPIA, la sessione incolla"
cnt "pkill -x xclip 2>/dev/null; printf 'ciao dal client' > /tmp/dal-client.txt; setsid nohup env DISPLAY=:110 xclip -selection clipboard -i /tmp/dal-client.txt >/dev/null 2>&1 & sleep 3; echo '   copiato nel client'"
sleep 2
vm "grep -E 'appunti:' ~/remotix.log | tail -2"
vm "env WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 timeout 10 wl-paste 2>&1 | head -2 | sed 's/^/   la sessione legge: /'"

echo "== 5. registro completo degli appunti"
vm "grep -iE 'appunti' ~/remotix.log | tail -12"
cnt "pkill -x xfreerdp3 2>/dev/null; pkill -x xclip 2>/dev/null; echo '   client chiuso'"
vm "pkill -x wl-copy 2>/dev/null; echo '   sessione sgombrata'"
