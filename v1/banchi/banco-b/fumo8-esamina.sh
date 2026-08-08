#!/bin/bash
set -u
kill $(cat /tmp/rec.pid) 2>/dev/null; sleep 1
python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/uscita.wav'); n = w.getnframes(); d = w.readframes(n)
v = struct.unpack('<%dh' % (len(d)//2), d) if d else ()
picco = max(abs(x) for x in v) if v else 0
sopra = sum(1 for x in v if abs(x) > 1000)
print("   il client ha suonato %d fotogrammi, picco %d, campioni non silenziosi %d"
      % (n, picco, sopra))
PY
