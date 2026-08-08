import struct, sys, os
# Cerca le DISCONTINUITA' in una registrazione di un seno noto.
#
# Un seno di 440 Hz ad ampiezza A campionato a 44100 non puo' saltare piu' di
# A*2*pi*440/44100 fra due campioni consecutivi: ~188 per A=3000.  Tutto quel
# che salta di piu' e' uno strappo — un blocco perso, un blocco doppio, o una
# giuntura fra due invii che non si allacciano.  Nessun contatore di fotogrammi
# puo' vederlo; l'orecchio lo sente come scoppiettio.
p = sys.argv[1]
if not os.path.exists(p) or os.path.getsize(p) < 4:
    print("VUOTO"); raise SystemExit
d = open(p, "rb").read()
v = struct.unpack("<%dh" % (len(d) // 2), d)
sx = v[0::2]
forti = [i for i, x in enumerate(sx) if abs(x) > 500]
if not forti:
    print("SILENZIO"); raise SystemExit
a, b = forti[0], forti[-1] + 1
t = sx[a:b]
picco = max(abs(x) for x in t)
limite = int(picco * 2 * 3.14159 * 440 / 44100 * 1.5)  # meta' di margine
salti = [i for i in range(1, len(t)) if abs(t[i] - t[i - 1]) > limite]
# I buchi: tratti di silenzio DENTRO il suono, cioe' quel che si sente come
# interruzione invece che come scoppiettio.
buchi, corrente = [], 0
for x in t:
    if abs(x) < 50:
        corrente += 1
    else:
        if corrente > 441:  # oltre 10 ms
            buchi.append(corrente)
        corrente = 0
if corrente > 441:
    buchi.append(corrente)
print("campioni %d (%.1f s)  picco %d  limite di salto %d" % (len(t), len(t) / 44100.0, picco, limite))
print("STRAPPI %d  (%.1f al secondo)" % (len(salti), len(salti) / (len(t) / 44100.0)))
if salti:
    print("  i primi, in millisecondi dall'inizio del suono: %s" %
          ", ".join("%.0f" % (i / 44.1) for i in salti[:12]))
    print("  distanza fra strappi consecutivi, in ms: %s" %
          ", ".join("%.0f" % ((salti[i] - salti[i - 1]) / 44.1) for i in range(1, min(13, len(salti)))))
print("BUCHI  %d  (durate in ms: %s)" % (len(buchi), ", ".join("%.0f" % (n / 44.1) for n in buchi[:12])))
