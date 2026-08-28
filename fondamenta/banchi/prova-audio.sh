#!/bin/bash
# Prova: un'applicazione suona sul sink virtuale, e il monitor si cattura.
set -u
echo "== strumenti"; which pw-play pw-record pw-cat python3 2>&1
python3 - <<'PY'
import math, struct, wave
w = wave.open('/tmp/tono.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(44100)
d = b''.join(struct.pack('<hh', v, v) for v in
             (int(12000*math.sin(2*math.pi*440*i/44100)) for i in range(44100)))
w.writeframes(d); w.close()
print("tono.wav scritto")
PY
ID=$(wpctl status | sed -n 's/.*\*\? *\([0-9]*\)\. REMOTIX .*/\1/p' | head -1)
echo "== sink virtuale: id=$ID"
rm -f /tmp/cattura.wav
pw-record --target "$ID" --rate 44100 --channels 2 --format s16 /tmp/cattura.wav &
REC=$!
sleep 1
pw-play /tmp/tono.wav
sleep 1
kill $REC 2>/dev/null; wait $REC 2>/dev/null
ls -l /tmp/cattura.wav
python3 - <<'PY'
import wave, struct
try:
    w = wave.open('/tmp/cattura.wav')
    n = w.getnframes(); d = w.readframes(n)
    picco = max(abs(v) for v in struct.unpack('<%dh' % (len(d)//2), d)) if d else 0
    print("catturati %d fotogrammi, %d Hz, %d canali, picco %d"
          % (n, w.getframerate(), w.getnchannels(), picco))
except Exception as e:
    print("errore:", e)
PY
