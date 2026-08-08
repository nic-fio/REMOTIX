#!/bin/bash
# ⛔ La certificazione che mancava: il client suona attraverso PULSE, non
#    attraverso PipeWire nativo.  Se lo strato pulse del banco distorce, la
#    misura di ieri accusava REMOTIX di un difetto del banco.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
rm -f /tmp/pulse-prova.wav
setsid nohup pw-record --target uscita --rate 44100 --channels 2 --format s16 /tmp/pulse-prova.wav >/dev/null 2>&1 </dev/null &
echo $! > /tmp/rec4.pid
sleep 1
paplay /tmp/tono-cnt.wav 2>&1 | tail -2
sleep 1
kill $(cat /tmp/rec4.pid) 2>/dev/null; sleep 1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/pulse-prova.wav'); d=w.readframes(w.getnframes())
v=struct.unpack('<%dh'%(len(d)//2),d); sx=v[0::2]
forti=[i for i,x in enumerate(sx) if abs(x)>500]
if not forti:
    print("   niente suono: paplay non ha suonato")
else:
    t=sx[forti[0]:forti[-1]]
    print("   attraverso PULSE: picco %d, rms %.0f   (atteso 3000 / 2121)"
          % (max(abs(x) for x in t), (sum(x*x for x in t)/len(t))**0.5))
PY
