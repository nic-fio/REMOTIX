#!/usr/bin/env python3
"""06-b37-sfora.py — ⛔⛔ LA TELA CHIESTA STA DENTRO LA FINESTRA? — sui pixel.

    FATTORE=1.25 python3 banchi/06-b37-sfora.py <porta> <display> <pid> <nome> <esiti>

⛔ PERCHE' ESISTE, e perche' NON basta l'aritmetica di `06-b37-numeri.py`.

Quel banco confronta la tela chiesta con «la finestra vera», calcolata come
`xwininfo − bordo del motore − barra di scorrimento`.  ⚠ A dpr non intero
quei tre numeri hanno ciascuno un arrotondamento, e il conto balla di ±1 px:
⛔ **il numero che accusa e il numero che assolve distano quanto l'errore dello
strumento**.  Con `FATTORE=1.25` il «bordo» del motore e' uscito 0 nel 48 % delle
righe e −1 nel 48 %: e' lo strumento che vibra, non il motore.

⇒ Qui la domanda si gira in una forma che i pixel sanno chiudere:

   si mette nella pagina un fotogramma **esattamente della misura che la pagina
   ha chiesto**, e si guarda se ci sta.  Se la pagina ha chiesto piu' di quel che
   la finestra ha, succede UNA delle due, e tutt'e due si vedono:

     · compare una barra di scorrimento ORIZZONTALE (`scrollWidth > clientWidth`)
       — e allora la pagina si e' accorta di stare stretta;
     · oppure il disegno viene TAGLIATO, e nella fotografia dello schermo il
       marcatore verde del bordo destro **non c'e' piu'**.

⛔ ATTESO, DICHIARATO PRIMA: a dpr 1 non succede mai; a dpr 1,25 · 1,5 · 2
   succede sulle larghezze in cui `06-b37-numeri.py` accusa lo sforamento, e su
   nessun'altra.  ⭐ Se invece non succede MAI, allora ad avere torto e' il conto
   di A6 — e questo banco serve a dirlo.
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
FATTORE = os.environ.get("FATTORE") or ""

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
  schermo.adatta_vista();
  schermo.componi();
  const el = $("schermo"), d = document.documentElement;
  const r = el.getBoundingClientRect();
  return JSON.stringify({
    dpr: devicePixelRatio, cw: d.clientWidth, scrollW: d.scrollWidth,
    scrollH: d.scrollHeight, ch: d.clientHeight,
    rect: [r.left, r.right, r.width], buffer: [el.width, el.height],
    stile: getComputedStyle(el).imageRendering,
    vista: [schermo.vista_l, schermo.vista_a],
    /* ⛔ la scala che la pagina si e' calcolata DA SE': e' quella che decide
       `pixelated`, e non e' detto che dica la verita' sulla finestra vera */
    scala_pagina: Math.min(schermo.vista_l / L, schermo.vista_a / A, 1)
  });
})(%d, %d)"""


def fotografa(nome_file):
    dim = [r for r in B.x("xdpyinfo").stdout.splitlines() if "dimensions:" in r]
    l, a = (int(v) for v in dim[0].split()[1].split("x"))
    ok, err = B.fotografa(nome_file, l, a)
    if not ok:
        raise RuntimeError("ffmpeg: " + err[:300])
    return np.fromfile(nome_file, dtype=np.uint8).reshape((a, l, 3))


def marcatore(img, quale):
    if quale == "rosso":
        m = (img[:, :, 0] > 170) & (img[:, :, 1] < 90) & (img[:, :, 2] < 90)
    else:
        m = (img[:, :, 1] > 170) & (img[:, :, 0] < 90) & (img[:, :, 2] < 90)
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(xs.max()), int(m.sum())


print("== 06-b37 · %s — la tela chiesta ci sta? (fattore %s)"
      % (B.nome, FATTORE or "1, di suo"), flush=True)
if not B.aspetta_pagina() or not B.trova_finestra():
    print("    NO  pagina o finestra assenti", flush=True)
    sys.exit(3)
if not B.giudica_palco():
    sys.exit(4)

CARTELLA = os.environ.get("PIXEL_DIR", "/tmp/06-b37-pixel")
os.makedirs(CARTELLA, exist_ok=True)

LARGHEZZE = [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010,
             1011]
righe = []
print("    %-7s %-6s %-6s %-11s %-11s %-8s %-9s %s"
      % ("fin.X", "cw", "scrW", "vista", "tela", "scala", "disegno", "esito"),
      flush=True)
for L in LARGHEZZE:
    B.ridimensiona(L, 760)
    time.sleep(0.7)
    s = B.js("stato()")
    tela = s["tela"]
    d = json.loads(B.val(INIETTA % (tela[0], tela[1])))
    time.sleep(0.5)
    f = os.path.join(CARTELLA, "06-b37-sfora-%s-%s-%d.rgb24"
                     % (B.nome, FATTORE or "1", L))
    img = fotografa(f)
    r = marcatore(img, "rosso")
    v = marcatore(img, "verde")
    disegno = (v[1] - r[0] + 1) if (r and v) else None
    barra_h = d["scrollW"] > d["cw"]
    # ⛔ UN pixel basta: su Gecko lo sforamento non fa comparire nessuna barra
    #    (le barre sono sovrapposte) e il sintomo e' UNA COLONNA DEL DESKTOP
    #    INVISIBILE — `[M]` 16 agosto 2026, dpr 1,5, finestre 1001 e 1007.
    #    ⚠ La prima stesura tollerava «tela − 1» e quei due casi passavano.
    tagliato = (v is None) or (disegno is not None and disegno < tela[0])
    esito = []
    if barra_h:
        esito.append("⛔ BARRA ORIZZONTALE (scrollW %d > cw %d)"
                     % (d["scrollW"], d["cw"]))
    if tagliato:
        esito.append("⛔ TAGLIATO (%s px su %d)" % (disegno, tela[0]))
    if d["stile"] != "pixelated":
        esito.append("⚠ image-rendering=%s" % d["stile"])
    riga = {"tipo": "sfora", "fattore": FATTORE or "1", "finestra_x": L,
            "cw": d["cw"], "scrollW": d["scrollW"], "vista": d["vista"],
            "tela": tela, "scala_pagina": d["scala_pagina"],
            "disegno_pixel": disegno, "barra_orizzontale": barra_h,
            "tagliato": bool(tagliato), "image_rendering": d["stile"],
            "fotografia": f}
    righe.append(riga)
    B.scrivi(riga, iniezione="si")
    print("    %-7d %-6d %-6d %-11s %-11s %-8.4f %-9s %s"
          % (L, d["cw"], d["scrollW"], "%dx%d" % tuple(d["vista"]),
             "%dx%d" % tuple(tela), d["scala_pagina"],
             str(disegno), " · ".join(esito) or "sta dentro"), flush=True)

print("\n== 06-b37 · %s — il verdetto" % B.nome, flush=True)
male = [r for r in righe if r["barra_orizzontale"] or r["tagliato"]]
if not male:
    print("    OK  su %d larghezze la tela chiesta ci sta SEMPRE: nessuna barra "
          "orizzontale, nessun taglio" % len(righe), flush=True)
else:
    print("    NO  ⛔⛔ %d larghezze su %d in cui la tela chiesta NON ci sta:"
          % (len(male), len(righe)), flush=True)
    for r in male:
        print("        finestra X %d → tela %s, disegno %s px, barra_h=%s"
              % (r["finestra_x"], r["tela"], r["disegno_pixel"],
                 r["barra_orizzontale"]), flush=True)
inter = [r for r in righe if r["image_rendering"] != "pixelated"]
print("    --  `image-rendering` diverso da `pixelated`: %d righe su %d — ⛔ e' "
      "il NUMERO DI GUARDIA: se cresce, il testo e' tornato interpolato"
      % (len(inter), len(righe)), flush=True)
sys.exit(1 if male else 0)
