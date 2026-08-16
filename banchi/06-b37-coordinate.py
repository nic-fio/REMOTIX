#!/usr/bin/env python3
"""06-b37-coordinate.py — ⛔ IL CLIC FINISCE DOVE PUNTI, QUANDO LA SCALA NON E' 1?

    python3 banchi/06-b37-coordinate.py <porta> <display> <pid> <nome> <esiti>

*Aggiunto al mandato di 6.5 il 16 agosto 2026, quando la sottofase 6.7 e' stata
tolta: il multi-monitor e' fuori scopo, ⭐ ma le COORDINATE con la scala ≠ 1 sono
di questa fase per pieno diritto.*

⛔ PERCHE': e' lo stesso difetto che ha reso il mouse inutilizzabile sul DeX per
   due giorni.  Nasce sempre da una scala data per scontata, e **oggi non si
   vede perche' la scala vale 1 per costruzione** — cioe' e' esattamente il tipo
   di difetto che dorme finche' qualcuno non apre `?adatta=no`, o finche' un
   compositore non risponde `COMPOSITORE_INCAPACE`.

⭐ COME SI CHIUDE IL CERCHIO, e non passa da nessuna variabile della pagina:

   1. si dipinge un fotogramma con quattro marcatori e lo si mette nella pagina;
   2. si FOTOGRAFA lo schermo X e si trova il rettangolo DIPINTO — cioe' dove
      l'immagine sta davvero, bande comprese;
   3. da li' si calcola il punto dello SCHERMO che sta sopra un pixel scelto del
      FOTOGRAMMA (angolo alto-sinistro, centro, angolo basso-destro);
   4. si manda li' un `pointermove` vero, e si legge la coordinata che la pagina
      **spedirebbe sul filo** — `cl_spedisci()` sostituito da una spia.
   5. lo scarto e' la differenza fra il pixel scelto e quello spedito.

⛔ L'ATTESO, DICHIARATO PRIMA: scarto **0 pixel** su tutti i punti quando la
   scala vale 1; e **≤ 1 pixel** quando la scala e' 0,7 e ci sono le bande — un
   pixel e' la larghezza dell'arrotondamento (`Math.floor` in
   `cl_manda_puntatore`), non un errore di origine.  ⭐ Uno scarto che CRESCE con
   la distanza dall'angolo e' un errore di SCALA; uno costante e' un errore di
   ORIGINE — e le bande sono il posto in cui l'origine si nasconde.

⚠ E lo zero si dichiara col denominatore: quanti punti, quante scene.
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

PREPARA = """(function () {
  /* ⛔ LA SPIA sulla coordinata CHE PARTE: `cl_spedisci` e' una funzione
     globale, e qui si sostituisce.  ⚠ Senza un server non c'e' nessun canale su
     cui spedire: senza questa sostituzione la misura non esisterebbe, e con lei
     si legge esattamente il numero che viaggerebbe (§7.3). */
  if (!window.__b37_vero_spedisci) window.__b37_vero_spedisci = cl_spedisci;
  window.__b37_spediti = [];
  cl_spedisci = function (tipo, a, b, ms) {
    window.__b37_spediti.push({ tipo: tipo, x: a, y: b });
    return null;
  };
  cl_entra("banco 06-b37");
  /* ⛔ Senza questa riga `rinegozia_vista()` esce subito (`if (!schermo.sessione)`)
     e la cornice NON si riadatta al ridimensionamento: C4 misurerebbe una
     pagina in cui il cammino che deve provare e' spento.  `[M]` primo giro: il
     disegno restava largo 985 CSS in una finestra da 880, e i marcatori
     finivano fuori dallo schermo. */
  schermo.sessione = true;
  return "pronto";
})()"""

INIETTA = """(function (L, A) {
  const c = document.createElement("canvas");
  c.width = L; c.height = A;
  const g = c.getContext("2d");
  g.fillStyle = "#202020"; g.fillRect(0, 0, L, A);
  g.fillStyle = "#ff0000"; g.fillRect(0, 0, 4, A);
  g.fillStyle = "#00ff00"; g.fillRect(L - 4, 0, 4, A);
  g.fillStyle = "#0000ff"; g.fillRect(0, 0, L, 4);
  g.fillStyle = "#ffff00"; g.fillRect(0, A - 4, L, 4);
  schermo.deposito = c;
  schermo.tela_l = L; schermo.tela_a = A;
  schermo.adatta_vista();
  schermo.componi();
  const el = $("schermo");
  const r = el.getBoundingClientRect();
  return JSON.stringify({ dpr: devicePixelRatio,
                          rect: [r.left, r.top, r.width, r.height],
                          tela: [schermo.tela_l, schermo.tela_a],
                          vista: [schermo.vista_l, schermo.vista_a],
                          stile: getComputedStyle(el).imageRendering });
})(%d, %d)"""

MUOVI = """(function (x, y) {
  window.__b37_spediti = [];
  /* ⛔ Si azzera l'ULTIMO SPEDITO prima di ogni misura, ed e' un'iniezione
     dichiarata: `cl_manda_puntatore()` non spedisce niente se il pixel di tela
     non e' cambiato (ed e' giusto — «un puntatore che non ha cambiato pixel non
     ha niente da dire»).  ⚠ Senza questa riga la seconda misura sullo STESSO
     punto non produce nessun messaggio, e il banco lo confonde con un buco:
     `[M]` e' successo, ed e' costato due giri. */
  cl_ux = -1; cl_uy = -1;
  const el = $("schermo");
  el.dispatchEvent(new PointerEvent("pointermove", {
    clientX: x, clientY: y, bubbles: true, pointerType: "mouse" }));
  return JSON.stringify({ spediti: window.__b37_spediti,
                          grezzo: [cl_grezzo_x, cl_grezzo_y],
                          px: cl_px, py: cl_py });
})(%r, %r)"""


def fotografa(nome):
    dim = [r for r in B.x("xdpyinfo").stdout.splitlines() if "dimensions:" in r]
    l, a = (int(v) for v in dim[0].split()[1].split("x"))
    ok, err = B.fotografa(nome, l, a)
    if not ok:
        raise RuntimeError("ffmpeg: " + err[:300])
    return np.fromfile(nome, dtype=np.uint8).reshape((a, l, 3))


def estremi(img):
    r = (img[:, :, 0] > 170) & (img[:, :, 1] < 90) & (img[:, :, 2] < 90)
    v = (img[:, :, 1] > 170) & (img[:, :, 0] < 90) & (img[:, :, 2] < 90)
    b = (img[:, :, 2] > 170) & (img[:, :, 0] < 90) & (img[:, :, 1] < 90)
    gi = (img[:, :, 0] > 170) & (img[:, :, 1] > 170) & (img[:, :, 2] < 90)
    if not (r.any() and v.any() and b.any() and gi.any()):
        return None
    return (int(np.nonzero(r)[1].min()), int(np.nonzero(v)[1].max()),
            int(np.nonzero(b)[0].min()), int(np.nonzero(gi)[0].max()))


CARTELLA = os.environ.get("PIXEL_DIR", "/tmp/06-b37-pixel")
os.makedirs(CARTELLA, exist_ok=True)


def scena(nome, fl, fa, finestra=(1000, 760)):
    B.ridimensiona(*finestra)
    time.sleep(0.7)
    B.val(PREPARA)
    d = json.loads(B.val(INIETTA % (fl, fa)))
    time.sleep(0.5)
    img = fotografa(os.path.join(CARTELLA, "06-b37-coord-%s-%s.rgb24"
                                 % (B.nome, nome)))
    e = estremi(img)
    if not e:
        print("        ⛔ marcatori non trovati: scena %s NON misurata" % nome,
              flush=True)
        return None
    x0, x1, y0, y1 = e
    ldis, adis = x1 - x0 + 1, y1 - y0 + 1
    scala = ldis / float(fl)
    dpr = d["dpr"]
    # ⛔ Il ponte fra i due sistemi di riferimento: il rettangolo dipinto e' noto
    #    nei pixel dello SCHERMO (fotografia) e nei pixel CSS del DOCUMENTO
    #    (`getBoundingClientRect`).  La differenza e' l'origine del contenuto.
    ox = x0 - d["rect"][0] * dpr
    oy = y0 - d["rect"][1] * dpr
    punti = [("alto-sinistro", 0, 0), ("centro", fl // 2, fa // 2),
             ("basso-destro", fl - 1, fa - 1)]
    righe = []
    print("        disegno %dx%d px su fotogramma %dx%d ⇒ scala %.4f · %s"
          % (ldis, adis, fl, fa, scala, d["stile"]), flush=True)
    for etichetta, fx, fy in punti:
        sx = x0 + (fx + 0.5) * ldis / fl
        sy = y0 + (fy + 0.5) * adis / fa
        cx = (sx - ox) / dpr
        cy = (sy - oy) / dpr
        r = json.loads(B.val(MUOVI % (cx, cy)))
        sp = r["spediti"]
        if not sp:
            print("        %-14s ⛔ NIENTE SPEDITO (grezzo %s, px %.2f) — la "
                  "pagina non ha convertito: non e' uno zero, e' un buco"
                  % (etichetta, r["grezzo"], r["px"]), flush=True)
            righe.append({"punto": etichetta, "atteso": [fx, fy],
                          "spedito": None})
            continue
        ult = sp[-1]
        dx, dy = ult["x"] - fx, ult["y"] - fy
        print("        %-14s atteso (%4d,%4d) → spedito (%4d,%4d)  scarto "
              "(%+d,%+d)" % (etichetta, fx, fy, ult["x"], ult["y"], dx, dy),
              flush=True)
        righe.append({"punto": etichetta, "atteso": [fx, fy],
                      "spedito": [ult["x"], ult["y"]], "scarto": [dx, dy]})
    B.scrivi({"tipo": "coordinate", "scena": nome, "fotogramma": [fl, fa],
              "finestra": list(finestra), "scala_pixel": round(scala, 4),
              "disegno_pixel": [ldis, adis], "image_rendering": d["stile"],
              "vista": d["vista"], "punti": righe}, iniezione="si")
    return righe


print("== 06-b37 · %s — le coordinate quando la scala non vale 1" % B.nome,
      flush=True)
if not B.aspetta_pagina() or not B.trova_finestra():
    print("    NO  pagina o finestra assenti", flush=True)
    sys.exit(3)
if not B.giudica_palco():
    sys.exit(4)

tutte = []
print("\n    --  C1 · la scala vale 1 (tela = finestra): il riferimento",
      flush=True)
B.ridimensiona(1000, 760)
time.sleep(0.7)
s = B.js("stato()")
tutte.append(("C1 scala 1", scena("c1-scala1", s["tela"][0], s["tela"][1])))

print("\n    --  C2 · fotogramma 1400×900 in una finestra piu' piccola: scala "
      "< 1 e bande sopra e sotto", flush=True)
tutte.append(("C2 scala <1", scena("c2-scala-minore", 1400, 900)))

print("\n    --  C3 · fotogramma 640×480 piu' PICCOLO della finestra: bande a "
      "DESTRA e a SINISTRA — e' li' che un errore di origine si nasconde",
      flush=True)
tutte.append(("C3 bande laterali", scena("c3-bande", 640, 480)))

print("\n    --  C4 · la finestra cambia SOTTO il dito: si muove il puntatore "
      "SUBITO dopo il ridimensionamento, senza aspettare il quadro", flush=True)
B.ridimensiona(1000, 760)
time.sleep(0.7)
B.val(PREPARA)
d = json.loads(B.val(INIETTA % (1400, 900)))
time.sleep(0.4)
img = fotografa(os.path.join(CARTELLA, "06-b37-coord-%s-c4.rgb24" % B.nome))
e = estremi(img)
if not e:
    print("        ⛔ marcatori non trovati: C4 NON misurata", flush=True)
else:
    x0, x1, y0, y1 = e
    ldis, adis = x1 - x0 + 1, y1 - y0 + 1
    dpr = d["dpr"]
    ox = x0 - d["rect"][0] * dpr
    oy = y0 - d["rect"][1] * dpr
    fx, fy = 700, 450
    sx = x0 + (fx + 0.5) * ldis / 1400.0
    sy = y0 + (fy + 0.5) * adis / 900.0
    B.ridimensiona(880, 700)          # ⛔ nessuna attesa: e' il punto
    r = json.loads(B.val(MUOVI % ((sx - ox) / dpr, (sy - oy) / dpr)))
    sp = r["spediti"]
    print("        subito dopo il ridimensionamento: spedito %s (atteso "
          "(%d,%d) se la cornice NON e' ancora cambiata)"
          % (sp[-1] if sp else "NIENTE", fx, fy), flush=True)
    # ⛔ Si aspetta che la CORNICE si sia assestata, e lo dice la pagina: una
    #    fotografia scattata mentre il disegno cambia misura non e' una scena.
    prec, fermo = None, 0
    for _ in range(20):
        w = B.js("$('schermo').getBoundingClientRect().width")
        if w == prec:
            fermo += 1
            if fermo >= 3:
                break
        else:
            prec, fermo = w, 0
        time.sleep(0.2)
    img2 = fotografa(os.path.join(CARTELLA,
                                  "06-b37-coord-%s-c4b.rgb24" % B.nome))
    e2 = estremi(img2)
    if not e2:
        print("        ⛔ a cornice assestata i marcatori NON si trovano nella "
              "fotografia (larghezza del disegno %s CSS): la seconda meta' di "
              "C4 e' NON MISURATA, e si dice" % prec, flush=True)
    if e2:
        x0b, x1b, y0b, y1b = e2
        d2 = json.loads(B.val(
            "JSON.stringify({rect: (function(){const r=$('schermo')"
            ".getBoundingClientRect(); return [r.left,r.top,r.width,r.height];"
            "})(), dpr: devicePixelRatio})"))
        ldis2 = x1b - x0b + 1
        adis2 = y1b - y0b + 1
        ox2 = x0b - d2["rect"][0] * d2["dpr"]
        oy2 = y0b - d2["rect"][1] * d2["dpr"]
        sx2 = x0b + (fx + 0.5) * ldis2 / 1400.0
        sy2 = y0b + (fy + 0.5) * adis2 / 900.0
        r2 = json.loads(B.val(MUOVI % ((sx2 - ox2) / d2["dpr"],
                                       (sy2 - oy2) / d2["dpr"])))
        sp2 = r2["spediti"]
        if not sp2:
            print("        ⛔ a cornice assestata non e' partita nessuna "
                  "coordinata: non e' uno zero, e' un buco", flush=True)
        if sp2:
            u = sp2[-1]
            print("        a cornice assestata (disegno %dx%d): spedito "
                  "(%d,%d), atteso (%d,%d) ⇒ scarto (%+d,%+d)"
                  % (ldis2, adis2, u["x"], u["y"], fx, fy, u["x"] - fx,
                     u["y"] - fy), flush=True)
            B.scrivi({"tipo": "coordinate", "scena": "c4-ridimensiona",
                      "prima": sp[-1] if sp else None, "dopo": u,
                      "atteso": [fx, fy],
                      "scarto": [u["x"] - fx, u["y"] - fy]}, iniezione="si")
            tutte.append(("C4 sotto il dito",
                          [{"punto": "centro", "atteso": [fx, fy],
                            "spedito": [u["x"], u["y"]],
                            "scarto": [u["x"] - fx, u["y"] - fy]}]))

# ---------------------------------------------------------------------------
print("\n== 06-b37 · %s — il verdetto sulle coordinate" % B.nome, flush=True)
guasti = 0
punti_totali = 0
for nome, righe in tutte:
    if not righe:
        print("    NO  %s: scena non misurata" % nome, flush=True)
        guasti += 1
        continue
    peggio = 0
    buchi = 0
    for r in righe:
        punti_totali += 1
        if not r.get("spedito"):
            buchi += 1
            continue
        peggio = max(peggio, abs(r["scarto"][0]), abs(r["scarto"][1]))
    if buchi:
        print("    NO  %s: %d punti su %d senza nessuna coordinata spedita"
              % (nome, buchi, len(righe)), flush=True)
        guasti += 1
    elif peggio <= 1:
        print("    OK  %s: scarto peggiore %d px su %d punti"
              % (nome, peggio, len(righe)), flush=True)
    else:
        print("    NO  %s: scarto peggiore %d px su %d punti"
              % (nome, peggio, len(righe)), flush=True)
        guasti += 1
print("    --  punti misurati in tutto: %d (il denominatore dello zero)"
      % punti_totali, flush=True)
sys.exit(1 if guasti else 0)
