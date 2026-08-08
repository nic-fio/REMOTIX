#!/bin/bash
# Un giro di caccia al flash: si registra lo schermo del client mentre la scena
# si muove, e si contano i fotogrammi che se ne vanno e tornano.
#
# $1 = 0|1 (copia zero)   $2 = etichetta
set -u
BASE=/media/REMOTIX
DISP=:114
MIS=1024x768
DUR=12

vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

DMA="$1"; ETI="$2"

vm "printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione\nREMOTIX_DMABUF=$DMA\n' \
    | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log 2>/dev/null; \
    sudo systemctl restart remotix.service; sleep 4; systemctl is-active remotix.service"

cnt "pkill -x xfreerdp3 2>/dev/null; pkill -f '^Xvfb $DISP' 2>/dev/null; pkill -x ffmpeg 2>/dev/null; sleep 1;
     Xvfb $DISP -screen 0 ${MIS}x24 -nolisten tcp >/dev/null 2>&1 &
     sleep 2
     setsid nohup env DISPLAY=$DISP xfreerdp3 /v:127.0.0.1:3389 /gfx:AVC420 /cert:ignore /sec:tls \
        /u:prova /p:prova /size:$MIS /title:CACCIA /log-level:WARN >/tmp/cli-$ETI.log 2>&1 </dev/null &
     sleep 10
     pgrep -x xfreerdp3 >/dev/null && echo '   client collegato' || echo '   client NON partito'"

# La registrazione parte PRIMA dei tasti: un flash che capitasse durante
# l'avvio della scena non deve cadere fuori dalla finestra di misura.
cnt "export DISPLAY=$DISP
     setsid nohup ffmpeg -loglevel error -f x11grab -framerate 30 -video_size $MIS -i $DISP \
        -vf scale=160:120,format=gray -f rawvideo -t $DUR -y /tmp/grezzo-$ETI.raw \
        >/tmp/ff-$ETI.log 2>&1 </dev/null &
     sleep 1
     xdotool search --name CACCIA windowactivate --sync 2>/dev/null
     xdotool key super; sleep 1
     for i in \$(seq 1 12); do
        xdotool type --delay 25 'remotix caccia al flash'
        xdotool key BackSpace BackSpace BackSpace BackSpace
     done
     sleep 3
     echo '   registrazione finita'"

cnt "python3 /srv/remotix/tmp/banco-b/flash.py /tmp/grezzo-$ETI.raw 160 120"
cnt "pkill -x xfreerdp3 2>/dev/null; pkill -f '^Xvfb $DISP' 2>/dev/null; true"
