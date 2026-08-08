python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/uscita.wav'); n=w.getnframes(); fr=w.getframerate(); d=w.readframes(n)
v = struct.unpack('<%dh'%(len(d)//2), d)
sx = v[0::2]
# la parte sonora: il piu' lungo tratto con ampiezza alta
forti = [i for i,x in enumerate(sx) if abs(x)>2000]
a,b = forti[0], forti[-1]
tratto = sx[a:b]
picco = max(abs(x) for x in tratto)
rms = (sum(x*x for x in tratto)/len(tratto))**0.5
incroci = sum(1 for i in range(1,len(tratto)) if (tratto[i-1]<0)<=(tratto[i]>=0) and tratto[i-1]*tratto[i]<0)
hz = incroci/2/(len(tratto)/fr)
sopra = sum(1 for x in tratto if abs(x)>=32767)
print("   tratto sonoro: %.2f s, picco %d, rms %.0f, frequenza stimata %.1f Hz, campioni a fondo scala %d"
      % (len(tratto)/fr, picco, rms, hz, sopra))
PY
