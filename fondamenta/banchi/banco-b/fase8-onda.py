import struct, sys, os
p = sys.argv[1]
if not os.path.exists(p) or os.path.getsize(p) < 4:
    print("VUOTO"); raise SystemExit
d = open(p, "rb").read()
v = struct.unpack("<%dh" % (len(d) // 2), d)
sx = v[0::2]
forti = [i for i, x in enumerate(sx) if abs(x) > 500]
if not forti:
    print("SILENZIO"); raise SystemExit
t = sx[forti[0]:forti[-1] + 1]
picco = max(abs(x) for x in t)
rms = (sum(x * x for x in t) / len(t)) ** 0.5
# La percentuale di campioni vicini al fondo scala e' il discriminante che
# nessun contatore dava: un seno di ampiezza 3000 non ne ha nemmeno uno, un
# segnale col segno ribaltato li ha TUTTI.
fondo = sum(1 for x in t if abs(x) > 10000)
print("ONDA %d %d %d" % (picco, rms, round(100.0 * fondo / len(t))))
