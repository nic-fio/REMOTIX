#!/bin/bash
# Che cosa consegniamo davvero al canale?  Si scrive su disco e si guarda.
set -u
BASE=/media/REMOTIX
BANCO=/srv/remotix/tmp/banco-b
vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
bash "$BASE/vm.sh" copia "$BASE/src/remotix-c/build/src/remotix" >/dev/null || exit 1
vm "rm -f /tmp/copia.pcm ~/remotix.log; printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione\nREMOTIX_SUONO_COPIA=/tmp/copia.pcm\n' | sudo tee /etc/default/remotix >/dev/null; sudo systemctl restart remotix.service; sleep 2; systemctl is-active remotix.service"

cnt "bash $BANCO/fumo8-client.sh" >/dev/null
vm "pw-play /tmp/piano.wav; sleep 1; echo '   tono da 3000 suonato'"
sleep 2
vm "ls -l /tmp/copia.pcm; python3 - <<'PY'
import struct
d=open('/tmp/copia.pcm','rb').read()
v=struct.unpack('<%dh'%(len(d)//2), d); sx=v[0::2]
forti=[i for i,x in enumerate(sx) if abs(x)>500]
if not forti:
    print('   nessun suono nella copia')
else:
    t=sx[forti[0]:forti[-1]]
    print('   quel che consegniamo al canale: picco %d, rms %.0f  (atteso 3000 / 2121)'
          % (max(abs(x) for x in t), (sum(x*x for x in t)/len(t))**0.5))
    print('   trenta campioni:', list(t[len(t)//2:len(t)//2+30]))
PY"
cnt "pkill -x xfreerdp3 2>/dev/null; echo '   client chiuso'"
