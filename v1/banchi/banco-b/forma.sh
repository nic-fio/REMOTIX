python3 - <<'PY'
import wave, struct
w = wave.open('/tmp/uscita.wav'); fr=w.getframerate(); d=w.readframes(w.getnframes())
v = struct.unpack('<%dh'%(len(d)//2), d); sx = v[0::2]
forti=[i for i,x in enumerate(sx) if abs(x)>2000]
a,b=forti[0],forti[-1]; t=sx[a:b]
picco=max(abs(x) for x in t); rms=(sum(x*x for x in t)/len(t))**0.5
fondo=sum(1 for x in t if abs(x)>=32000)
print("   tratto %.2f s  picco %d  rms %.0f  a fondo scala %d su %d (%.1f%%)"
      % (len(t)/fr,picco,rms,fondo,len(t),100.0*fondo/len(t)))
# dove stanno i campioni a fondo scala: sparsi o in gruppi?
gruppi=0; dentro=False
for x in t:
    alto=abs(x)>=32000
    if alto and not dentro: gruppi+=1
    dentro=alto
print("   i campioni a fondo scala stanno in %d gruppi" % gruppi)
print("   trenta campioni dal mezzo del tono:", list(t[len(t)//2:len(t)//2+30]))
PY
