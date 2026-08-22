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

═══════════════════════════════════════════════════════════════════════════
⛔⭐⭐ E DAL 22 AGOSTO 2026 LA DOMANDA HA ANCHE L'ALTRO VERSO — `fasi/06` §5.5,
   primo falso verde: *«nessuna scena ha un limite INFERIORE sulla tela»*.

   «Ci sta» era una domanda sola: la tela e' piu' GRANDE della finestra?  ⇒ Una
   tela **30 px piu' stretta** della finestra — banda nera permanente su tutta
   l'altezza dello schermo, 30 colonne di desktop che l'utente non vede mai —
   passava questo banco **su dodici larghezze su dodici**, perche' il fotogramma
   iniettato e' della misura che la pagina ha chiesto e quindi ci sta sempre.

⇒ Adesso il disegno si confronta con la **VISTA LETTA SUI PIXEL** (le strisce di
  calibrazione di `06-b37-comune.py`), che non viene ne' dalla pagina ne' dal
  fotogramma iniettato, e il confine e' DERIVATO:

      W − ceil(dpr) ≤ disegno ≤ W

  ⚠ `ceil(dpr)` e non un numero scelto: `clientWidth` e' un intero di pixel CSS
    (fino a `dpr` pixel del dispositivo di troncatura) e la parita' di §4.5 ne
    toglie al massimo un altro — ma i due si sovrappongono, e il conto stretto e'
    quello di `06-b37-numeri.py` A6.
"""
import importlib.util
import math
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

# ⛔ Il fotogramma lo mette `Banco.mostra()`, per la STRADA DEL PRODOTTO
#    (`schermo.mostra()` su `bitmaprenderer`).  ⚠ Qui c'era un `schermo.deposito
#    = c; schermo.componi()` che dal passaggio a `bitmaprenderer` non dipingeva
#    piu' NIENTE — vedi il cappello di `06-b37-comune.py`.


def fotografa(nome_file):
    """⛔ I pixel, dalla PIPE: il file si scrive solo con `B37_FOTO=tieni`
       (`06-b37-comune.py` `_grezza`).  ⚠ Un giro intero scriveva 1,5 GB di
       fotogrammi grezzi in un `/tmp` condiviso con altri otto agenti."""
    return B.immagine(nome_file)


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
print("    %-7s %-6s %-6s %-11s %-11s %-8s %-9s %-9s %s"
      % ("fin.X", "cw", "scrW", "vista", "tela", "scala", "disegno",
         "VISTA_px", "esito"), flush=True)
for L in LARGHEZZE:
    B.ridimensiona(L, 760)
    time.sleep(0.7)
    s = B.js("stato()")
    tela = s["tela"]
    d = B.mostra(tela[0], tela[1], "righe")
    time.sleep(0.5)
    # ⛔ La calibrazione si fa DOPO l'iniezione e PRIMA della fotografia dei
    #    marcatori: se il fotogramma ha fatto comparire una barra, la vista vera
    #    e' quella di adesso, non quella di prima.  ⚠ E sono due fotografie
    #    distinte apposta: le strisce partono da `left: 0`, cioe' proprio dove
    #    puo' cadere il marcatore rosso del disegno.
    cal = B.calibra(os.path.join(CARTELLA, "06-b37-sfora-cal-%s-%s-%d.rgb24"
                                 % (B.nome, FATTORE or "1", L)))
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
    # ⛔⭐ IL LIMITE INFERIORE, e la verita' non e' la tela: e' la VISTA sui pixel.
    amm = int(math.ceil(d["dpr"]))
    avanzo = None
    banda = False
    if cal and disegno is not None:
        # ⚠ Il pavimento viene dalla maschera STRETTA (il piu' piccolo che la
        #   vista possa essere): un pixel di bordo mescolato col fondo non
        #   diventa un'accusa.
        avanzo = cal["l"] - disegno
        banda = avanzo > amm
    esito = []
    if barra_h:
        esito.append("⛔ BARRA ORIZZONTALE (scrollW %d > cw %d)"
                     % (d["scrollW"], d["cw"]))
    if tagliato:
        esito.append("⛔ TAGLIATO (%s px su %d)" % (disegno, tela[0]))
    if banda:
        esito.append("⛔ BANDA NERA di %d px (massimo legale %d)"
                     % (avanzo, amm))
    if cal is None:
        esito.append("⛔ NESSUNA calibrazione: il limite inferiore non si "
                     "giudica")
    if d["image_rendering"] != "pixelated":
        esito.append("⚠ image-rendering=%s" % d["image_rendering"])
    riga = {"tipo": "sfora", "fattore": FATTORE or "1", "finestra_x": L,
            "cw": d["cw"], "scrollW": d["scrollW"], "vista": d["vista"],
            "tela": tela, "scala_pagina": d["scala_pagina"],
            "disegno_pixel": disegno, "barra_orizzontale": barra_h,
            "tagliato": bool(tagliato), "image_rendering": d["image_rendering"], "strada": d["strada"],
            "vista_pixel": ([cal["l"], cal["a"]] if cal else None),
            "avanzo_pixel": avanzo, "avanzo_massimo": amm,
            "banda_nera": bool(banda), "senza_calibrazione": cal is None,
            "fotografia": B.percorso_foto(f)}
    righe.append(riga)
    B.scrivi(riga, iniezione="si")
    print("    %-7d %-6d %-6d %-11s %-11s %-8.4f %-9s %-9s %s"
          % (L, d["cw"], d["scrollW"], "%dx%d" % tuple(d["vista"]),
             "%dx%d" % tuple(tela), d["scala_pagina"],
             str(disegno), ("%dx%d" % (cal["l"], cal["a"])) if cal else "⛔ -",
             " · ".join(esito) or "sta dentro, e la riempie"), flush=True)

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
# ⛔⭐ L'ALTRO VERSO, e senza di lui questo banco era verde su una tela 30 px
#    piu' stretta della finestra (`fasi/06` §5.5, primo falso verde).
buchi = [r for r in righe
         if r["senza_calibrazione"] or r["avanzo_pixel"] is None]
strette = [r for r in righe if r["banda_nera"]]
if buchi:
    print("    NO  ⛔ %d larghezze su %d SENZA la lettura sui pixel: il limite "
          "inferiore non e' stato giudicato, e non e' uno zero"
          % (len(buchi), len(righe)), flush=True)
if not strette and not buchi:
    peggio = max((r["avanzo_pixel"] for r in righe
                  if r["avanzo_pixel"] is not None), default=0)
    print("    OK  e la RIEMPIE: su %d larghezze il disegno arriva a %d px "
          "dalla vista vera al massimo (massimo legale ceil(dpr)) — nessuna "
          "banda nera permanente" % (len(righe), peggio), flush=True)
elif strette:
    print("    NO  ⛔⛔ %d larghezze su %d in cui la tela chiesta e' PIU' "
          "STRETTA della finestra: banda nera permanente e colonne di desktop "
          "che l'utente non vede mai:" % (len(strette), len(righe)), flush=True)
    for r in strette:
        print("        finestra X %d → vista sui PIXEL %s, tela %s, disegno %s "
              "px ⇒ avanzo %d px (massimo legale %d)"
              % (r["finestra_x"], r["vista_pixel"], r["tela"],
                 r["disegno_pixel"], r["avanzo_pixel"], r["avanzo_massimo"]),
              flush=True)
inter = [r for r in righe if r["image_rendering"] != "pixelated"]
print("    --  `image-rendering` diverso da `pixelated`: %d righe su %d — ⛔ e' "
      "il NUMERO DI GUARDIA: se cresce, il testo e' tornato interpolato"
      % (len(inter), len(righe)), flush=True)
B.scrivi({"tipo": "sfora-verdetto", "righe": len(righe),
          "non_ci_stanno": len(male), "banda_nera": len(strette),
          "senza_calibrazione": len(buchi),
          "non_pixelated": len(inter)}, iniezione="si")
sys.exit(1 if (male or strette or buchi) else 0)
