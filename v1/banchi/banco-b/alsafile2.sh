#!/bin/bash
set -u
python3 - <<'PY'
import struct, os
p='/tmp/dal-client.raw'
if not os.path.exists(p) or os.path.getsize(p)==0:
    print("   il client non ha scritto niente sul dispositivo"); raise SystemExit
d=open(p,'rb').read()
v=struct.unpack('<%dh'%(len(d)//2), d); sx=v[0::2]
forti=[i for i,x in enumerate(sx) if abs(x)>500]
if not forti:
    print("   il client ha scritto %d byte, tutti silenzio" % len(d)); raise SystemExit
t=sx[forti[0]:forti[-1]]
print("   quel che il CLIENT consegna al suo dispositivo: picco %d, rms %.0f  (atteso 3000 / 2121)"
      % (max(abs(x) for x in t), (sum(x*x for x in t)/len(t))**0.5))
print("   venti campioni:", list(t[len(t)//2:len(t)//2+20]))
PY
