#!/bin/bash
# Lo stesso giro, ma con un tono PIANO: distingue un guadagno costante da una
# normalizzazione, e dice se a distorcere siamo noi.
set -u
BASE=/media/REMOTIX
BANCO=/srv/remotix/tmp/banco-b
vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

vm "python3 - <<'PY'
import math, struct, wave
w = wave.open('/tmp/piano.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
w.writeframes(b''.join(struct.pack('<hh', v, v) for v in
    (int(3000*math.sin(2*math.pi*440*i/44100)) for i in range(88200))))
w.close(); print('   tono piano scritto: ampiezza 3000')
PY"

echo "== quel che ESCE dalla sessione (misurato sul monitor del nostro sink)"
vm "rm -f /tmp/controllo.wav; (setsid pw-record --target remotix --rate 44100 --channels 2 --format s16 /tmp/controllo.wav >/dev/null 2>&1 & echo \$! > /tmp/rec2.pid); sleep 1; pw-play /tmp/piano.wav; sleep 1; kill \$(cat /tmp/rec2.pid) 2>/dev/null; sleep 1; python3 - <<'PY'
import wave,struct
w=wave.open('/tmp/controllo.wav'); d=w.readframes(w.getnframes()); v=struct.unpack('<%dh'%(len(d)//2),d)
print('   picco alla sorgente: %d' % max(abs(x) for x in v))
PY"

echo "== e quel che ESCE dal client, con lo stesso tono piano"
cnt "bash $BANCO/fumo8-client.sh" >/dev/null
cnt "bash $BANCO/fumo8-registra.sh" >/dev/null
vm "pw-play /tmp/piano.wav; echo '   suonato'"
sleep 2
cnt "bash $BANCO/fumo8-esamina.sh"
cnt "XDG_RUNTIME_DIR=/tmp/rt wpctl get-volume 46 2>&1; XDG_RUNTIME_DIR=/tmp/rt wpctl status | sed -n '/Streams:/,/^\$/p'"
cnt "pkill -x xfreerdp3; echo chiuso" >/dev/null
