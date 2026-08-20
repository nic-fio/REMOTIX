#!/usr/bin/env python3
"""07-b49-occhi-sulla-tela.py — la tela sullo SCHERMO, non riletta.

    python3 banchi/07-b49-occhi-sulla-tela.py            strada normale (GPU)
    python3 banchi/07-b49-occhi-sulla-tela.py --software composizione in software
    python3 banchi/07-b49-occhi-sulla-tela.py --giri 6   quanti giri tenerla su

⛔ PERCHE' ESISTE — 17 agosto 2026, e la ragione è una frase dell'utente:
   *«sto guardando lo svolgimento dei test, e vedo che gli artefatti ancora
   compaiono»* — mentre `07-b48`, sulla STESSA tela e negli STESSI istanti,
   rileggeva `getImageData` e trovava ZERO superblocchi fuori posto.

   ⇒ I pixel dentro la tela sono giusti; è sbagliato quel che di quella tela
     arriva allo schermo.  Il guasto sta DOPO l'ultimo punto che un programma
     sa leggere: nella PRESENTAZIONE — WebRender, Mesa, il pannello.

   ⭐ E lì l'unico strumento che vede è l'occhio dell'utente (I8).  Questo
     banco non misura: tiene la scena in vista, con UNA variabile cambiata, e
     gli chiede di guardare.

⚠ La differenza fra i due giri è un solo interruttore, `gfx.webrender.software`:
  se i blocchi spariscono col software, la colpa è della strada della scheda.
"""
import argparse, importlib.util as iu, os, time

_qui = os.path.dirname(os.path.abspath(__file__))
_sp = iu.spec_from_file_location("m", os.path.join(_qui, "07-b46-marionette.py"))
M = iu.module_from_spec(_sp); _sp.loader.exec_module(M)

a = argparse.ArgumentParser()
a.add_argument("--software", action="store_true",
               help="composizione in software: niente GPU")
a.add_argument("--porta", type=int, default=8099)
a.add_argument("--marionette", type=int, default=2849)
a.add_argument("--giri", type=int, default=4)
a.add_argument("--flusso", default="av1")
# ⭐ Il ritmo è un'ipotesi dell'utente (17 ago 2026): «il terminale viene
#   spostato in modo molto veloce, che sia quella la causa?».  ⛔ Il banco
#   ripassa i 300 fotogrammi a 16 ms l'uno mentre erano stati CATTURATI coi
#   tempi veri di Mutter: il movimento esce compresso, e il carico di
#   composizione è più alto di qualunque sessione vera.  ⇒ Si prova a
#   rallentare, invece di discuterne.
a.add_argument("--disegno", default="2d", choices=["2d", "bitmap"],
               help="2d = `drawImage` su tela 2D · bitmap = `transferFromImageBitmap`")
a.add_argument("--ritmo", type=int, default=16,
               help="ms fra un fotogramma e l'altro (16 ≈ 60/s, 100 ≈ 10/s)")
o = a.parse_args()

prefs = {}
if o.software:
    # ⛔ Tutte e tre, non solo la prima: WebRender ha piu' di una strada verso
    #   la scheda, e spegnerne una sola lascia le altre aperte.
    prefs = {"gfx.webrender.software": True,
             "gfx.webrender.all": False,
             "layers.acceleration.disabled": True}

print("⭐ strada grafica: %s · ritmo %d ms (%.0f fotogrammi al secondo)"
      % ("SOFTWARE (niente GPU)" if o.software else "normale (GPU)",
         o.ritmo, 1000.0 / max(o.ritmo, 1)))
print("   disegno: %s" % ("transferFromImageBitmap (niente tela 2D)"
                          if o.disegno == "bitmap" else "drawImage su tela 2D"))
print("   la finestra resta su per %d giri: GUARDALA e dimmi se i blocchi ci sono." % o.giri)
p, m, prof = M.accendi(porta=o.marionette, headless=False, largo=1900, alto=1100,
                       profilo_prefs=prefs)
try:
    m.sessione()
    for g in range(o.giri):
        m.vai("http://localhost:%d/?flusso=%s&modo=tela&ritmo=%d&vista=1&disegno=%s"
              % (o.porta, o.flusso, o.ritmo, o.disegno))
        for _ in range(120):
            if m.js("return window.RISULTATO ? 1 : 0")["value"]:
                break
            time.sleep(1)
        r = m.js("return window.RISULTATO")["value"]
        print("   giro %d/%d — la tela RILETTA dice: %d superblocchi fuori posto (peggio %.1f)"
              % (g + 1, o.giri, r["tela"]["fuori_posto"], r["tela"]["peggio"]))
finally:
    M.spegni(p, prof)
