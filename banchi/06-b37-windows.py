#!/usr/bin/env python3
"""06-b37-windows.py — ⭐ LA CONFIGURAZIONE DELL'UTENTE SU WINDOWS, RIPRODOTTA.

    FATTORE=1.25 TELA_X=2600x1000x24 \\
    bash banchi/06-b37-lancia.sh chrome windows

`[M]` 16 agosto 2026, ore 20:43 (orologio della macchina di prova, indietro di
due ore).  L'utente si collega al prodotto vivo sulla 7700 **da Windows con lo
schermo scalato al 125 %**, e giudica: *«funziona tutto e con performance
eccellenti»*, poi *«il test su Windows lo dichiaro superato al 100 %»*.  Il
registro del server:

    tela=2540x868 vista=2541x869 disposizione=it
    3829 fotogrammi consegnati (10 chiavi), 0 guasti

⇒ ⛔ **La sua finestra era DISPARI su tutt'e due i lati**, e la tela e' stata
  troncata di un pixel per lato.  E' esattamente il caso delle `[?]` 2 e 3 di
  `SPECIFICHE.md` §6.1-bis, capitato su un utente vero.

⭐ CHE COSA MISURA QUESTO BANCO, E PERCHE' NON E' UNA CONFERMA DI COMODO.
   L'invariante **I8** dice che a giudicare e' l'utente, e lui ha gia' giudicato:
   ⛔ quel che manca non e' un verdetto, e' **il numero di guardia** — la
   grandezza che, se un giorno cambia, dice che il testo e' tornato interpolato.
   Qui si misura quella, e si misura SUI PIXEL.

⛔ L'ATTESO, DICHIARATO PRIMA (derivazione del coordinatore, da smentire):
   con `dpr 1,25` e finestra 2541×869 la tela chiesta e' **2540×868**, e la
   scala vale **esattamente 1** perche' nel `Math.min` di `cornice()` vince il
   terzo termine (il tappo a 1), non i rapporti 2541/2540 e 869/868.
   ⇒ `image-rendering: pixelated`, disegno largo **2540 px esatti**, righe da un
   pixel NETTE.  ⚠ E il residuo del centraggio e' 0,4 px CSS per lato = **mezzo
   pixel fisico**: se il motore non aggancia il canvas alla griglia, si vede li'.
"""
import importlib.util
import json
import os
import sys
import time

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location("b37comune",
                                            os.path.join(QUI, "06-b37-comune.py"))
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)

B = _m.Banco(*sys.argv[1:6])
BERSAGLIO_TELA = (2540, 868)
BERSAGLIO_VISTA = (2541, 869)

INIETTA = """(function (L, A) {
  const c = document.createElement("canvas");
  c.width = L; c.height = A;
  const g = c.getContext("2d");
  g.fillStyle = "#000"; g.fillRect(0, 0, L, A);
  g.fillStyle = "#fff";
  for (let xx = 0; xx < L; xx += 2) g.fillRect(xx, 0, 1, A);
  g.fillStyle = "#ff0000"; g.fillRect(0, 0, 4, A);
  g.fillStyle = "#00ff00"; g.fillRect(L - 4, 0, 4, A);
  schermo.deposito = c;
  schermo.tela_l = L; schermo.tela_a = A;
  schermo.sessione = true;
  schermo.adatta_vista();
  schermo.componi();
  const el = $("schermo"), r = el.getBoundingClientRect();
  return JSON.stringify({
    dpr: devicePixelRatio, rect: [r.left, r.top, r.width, r.height],
    rect_fisico: [r.left * devicePixelRatio, r.width * devicePixelRatio],
    stile: getComputedStyle(el).imageRendering,
    stile_larghezza: getComputedStyle(el).width,
    vista: [schermo.vista_l, schermo.vista_a],
    scala: Math.min(schermo.vista_l / L, schermo.vista_a / A, 1),
    buffer: [el.width, el.height]
  });
})(%d, %d)"""


def fotografa(nome):
    dim = [r for r in B.x("xdpyinfo").stdout.splitlines() if "dimensions:" in r]
    l, a = (int(v) for v in dim[0].split()[1].split("x"))
    ok, err = B.fotografa(nome, l, a)
    if not ok:
        raise RuntimeError("ffmpeg: " + err[:300])
    return np.fromfile(nome, dtype=np.uint8).reshape((a, l, 3))


print("== 06-b37 · %s — la finestra 2541×869 a dpr 1,25 (il caso dell'utente)"
      % B.nome, flush=True)
if not B.aspetta_pagina() or not B.trova_finestra():
    print("    NO  pagina o finestra assenti", flush=True)
    sys.exit(3)

dim = [r for r in B.x("xdpyinfo").stdout.splitlines() if "dimensions:" in r]
sl, sa = (int(v) for v in dim[0].split()[1].split("x"))
if sl < 2600:
    print("    NO  lo schermo finto e' largo %d: non ci sta una finestra da "
          "2541 px di contenuto.  ⛔ Scena NON MISURATA (serve "
          "TELA_X=2600x1000x24), e non si estrapola" % sl, flush=True)
    sys.exit(3)
if not B.giudica_palco():
    sys.exit(4)

# ⛔ La finestra si CERCA, non si calcola: il bordo del motore e la barra di
#    scorrimento sono due numeri che nessuno di noi conosce con certezza a dpr
#    1,25 (e' quello che ha fatto vibrare A6).  Si prova, si legge, si corregge.
L, A = 2560, 980
trovata = None
# ⛔ Prima la LARGHEZZA, poi l'ALTEZZA, e ciascuna con una spazzata: a dpr 1,25
#    un pixel X vale 0,8 px CSS, e una ricerca che corregge di «quanto manca»
#    rimbalza fra due valori senza mai toccare quello in mezzo — `[M]` il primo
#    giro ha oscillato fra 867 e 870 sette volte, saltando 868.
cand_l = []
for prova_l in range(2550, 2578):
    B.ridimensiona(prova_l, A)
    time.sleep(0.5)
    s = B.js("stato()")
    if s["tela"][0] == BERSAGLIO_TELA[0]:
        cand_l.append((prova_l, s))
        # ⛔ Fra le larghezze che danno la tela giusta si vuole quella che da'
        #    anche la VISTA DISPARI dell'utente (2541): e' l'unica in cui avanza
        #    un pixel, cioe' l'unica in cui il mezzo pixel del centraggio esiste.
        if s["vista"][0] == BERSAGLIO_VISTA[0]:
            break
if cand_l:
    L = next((l for l, x in cand_l if x["vista"][0] == BERSAGLIO_VISTA[0]),
             cand_l[0][0])
    print("    --  larghezze che danno la tela giusta: %s"
          % [(l, x["vista"][0]) for l, x in cand_l], flush=True)

candidate = []
for prova_a in range(966, 996):
    B.ridimensiona(L, prova_a)
    time.sleep(0.5)
    s = B.js("stato()")
    if s["tela"][1] == BERSAGLIO_TELA[1]:
        candidate.append((prova_a, s))
        # ⛔ Fra tutte le altezze che danno la stessa TELA si prende quella che
        #    riproduce anche la VISTA dell'utente (2541×869): altrimenti si
        #    misurerebbe un caso equivalente ma NON il suo — e il residuo del
        #    centraggio, che e' proprio quel che si cerca, sarebbe zero.
        if tuple(s["vista"]) == BERSAGLIO_VISTA:
            break
if candidate:
    for prova_a, s in candidate:
        if tuple(s["vista"]) == BERSAGLIO_VISTA:
            A, trovata = prova_a, (L, prova_a, s)
            break
    else:
        A, s = candidate[0]
        trovata = (L, A, s)
    B.ridimensiona(L, A)
    time.sleep(0.6)
    print("    --  altezze che danno la tela giusta: %s"
          % [(a, tuple(x["vista"])) for a, x in candidate], flush=True)

if not trovata:
    print("    NO  non sono riuscito a portare la tela a %dx%d: scena NON "
          "MISURATA" % BERSAGLIO_TELA, flush=True)
    sys.exit(1)

L, A, s = trovata
print("    OK  riprodotta: finestra X %dx%d ⇒ vista %s ⇒ tela %s"
      % (L, A, s["vista"], s["tela"]), flush=True)
if tuple(s["vista"]) != BERSAGLIO_VISTA:
    print("    ⚠   la VISTA e' %s e non %s: la tela concessa e' la stessa, ma "
          "la vista dichiarata al server differisce di %+d,%+d — si dice"
          % (s["vista"], list(BERSAGLIO_VISTA),
             s["vista"][0] - BERSAGLIO_VISTA[0],
             s["vista"][1] - BERSAGLIO_VISTA[1]), flush=True)

d = json.loads(B.val(INIETTA % tuple(BERSAGLIO_TELA)))
time.sleep(0.8)
CARTELLA = os.environ.get("PIXEL_DIR", "/tmp/06-b37-pixel")
os.makedirs(CARTELLA, exist_ok=True)
f = os.path.join(CARTELLA, "06-b37-windows-%s.rgb24" % B.nome)
img = fotografa(f)
r = (img[:, :, 0] > 170) & (img[:, :, 1] < 90) & (img[:, :, 2] < 90)
v = (img[:, :, 1] > 170) & (img[:, :, 0] < 90) & (img[:, :, 2] < 90)
if not (r.any() and v.any()):
    print("    NO  i marcatori non si trovano: niente verdetto", flush=True)
    sys.exit(1)
x0 = int(np.nonzero(r)[1].min())
x1 = int(np.nonzero(v)[1].max())
y = int(np.nonzero(r)[0][len(np.nonzero(r)[0]) // 2])
larg = x1 - x0 + 1
riga = img[y, x0 + 8:x1 - 8, :].mean(axis=1)
grigi = int(((riga > 60) & (riga < 195)).sum())
frazione = abs(d["rect_fisico"][0] - round(d["rect_fisico"][0]))

print("\n    --  scala che la pagina si e' calcolata: %.6f · image-rendering "
      "«%s» · style.width «%s»" % (d["scala"], d["stile"], d["stile_larghezza"]),
      flush=True)
print("    --  `getBoundingClientRect().left` in pixel fisici: %.3f ⇒ %s"
      % (d["rect_fisico"][0],
         "⛔ MEZZO PIXEL" if frazione > 0.01 else "sulla griglia"), flush=True)
print("    --  disegno misurato SUI PIXEL: %d px (tela %d) · colonne grigie "
      "%d su %d" % (larg, BERSAGLIO_TELA[0], grigi, len(riga)), flush=True)

B.scrivi({"tipo": "windows", "finestra_x": [L, A], "vista": s["vista"],
          "tela": s["tela"], "scala_pagina": d["scala"],
          "image_rendering": d["stile"], "rect_sinistro_fisico":
          round(d["rect_fisico"][0], 3), "mezzo_pixel": frazione > 0.01,
          "disegno_pixel": larg, "colonne": len(riga), "colonne_grigie": grigi,
          "fotografia": f}, iniezione="si")

guasti = 0
if abs(d["scala"] - 1.0) < 1e-9:
    print("    OK  la scala vale ESATTAMENTE 1: nel Math.min vince il tappo, "
          "non i rapporti %.6f e %.6f — la derivazione REGGE"
          % (s["vista"][0] / float(BERSAGLIO_TELA[0]),
             s["vista"][1] / float(BERSAGLIO_TELA[1])), flush=True)
else:
    print("    NO  la scala vale %.6f e non 1: la derivazione NON regge"
          % d["scala"], flush=True)
    guasti += 1
if larg == BERSAGLIO_TELA[0]:
    print("    OK  e sui PIXEL il disegno e' largo %d, cioe' la tela esatta: "
          "nessun ricampionamento" % larg, flush=True)
else:
    print("    NO  sui pixel il disegno e' largo %d invece di %d"
          % (larg, BERSAGLIO_TELA[0]), flush=True)
    guasti += 1
if grigi == 0:
    print("    OK  ⭐ zero colonne grigie su %d: le righe da UN pixel arrivano "
          "intatte fino al vetro, mezzo pixel di centraggio compreso"
          % len(riga), flush=True)
else:
    print("    NO  %d colonne grigie su %d: il mezzo pixel ARRIVA ai pixel"
          % (grigi, len(riga)), flush=True)
    guasti += 1
print("\n    ⭐ IL NUMERO DI GUARDIA: `image-rendering` deve leggersi "
      "«pixelated» e la scala deve valere 1,000000.  Se `vista < tela` anche "
      "di UN pixel, il tappo del Math.min non serve piu' e si passa a «auto»: "
      "e' li' che il testo torna interpolato.", flush=True)
sys.exit(1 if guasti else 0)
