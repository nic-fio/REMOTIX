#!/bin/bash
# ⛔ Il banco si certifica PRIMA della misura: si suona un tono NEL contenitore
#    e lo si registra dallo stesso monitor.  Se esce distorto qui, la colpa non
#    e' di REMOTIX.
set -u
export XDG_RUNTIME_DIR=/tmp/rt
python3 - <<'PY'
import math, struct, wave
w = wave.open('/tmp/tono-cnt.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
w.writeframes(b''.join(struct.pack('<hh', v, v) for v in
    (int(3000*math.sin(2*math.pi*440*i/44100)) for i in range(88200))))
w.close(); print("   tono da 3000 scritto dentro il contenitore")
PY
rm -f /tmp/prova-cnt.wav
setsid nohup pw-record --target uscita --rate 44100 --channels 2 --format s16 /tmp/prova-cnt.wav >/dev/null 2>&1 </dev/null &
echo $! > /tmp/rec3.pid
sleep 1
pw-play /tmp/tono-cnt.wav
sleep 1
kill $(cat /tmp/rec3.pid) 2>/dev/null; sleep 1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/prova-cnt.wav'); d=w.readframes(w.getnframes())
v=struct.unpack('<%dh'%(len(d)//2),d); sx=v[0::2]
forti=[i for i,x in enumerate(sx) if abs(x)>500]
if not forti: print("   niente suono registrato"); raise SystemExit
t=sx[forti[0]:forti[-1]]
print("   dentro il contenitore: picco %d, rms %.0f  (atteso picco 3000, rms 2121)"
      % (max(abs(x) for x in t), (sum(x*x for x in t)/len(t))**0.5))
PY
