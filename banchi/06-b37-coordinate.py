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

   1. si dipinge un fotogramma con quattro marcatori e lo si mette nella pagina
      per la STRADA DEL PRODOTTO (`schermo.mostra()`);
   2. si CALIBRA la vista sui pixel: dove sta il pixel CSS (0,0) sullo schermo X,
      e quanto e' grande la vista.  ⛔ E non lo si chiede alla tela;
   3. si FOTOGRAFA lo schermo X e si trova il rettangolo DIPINTO — cioe' dove
      l'immagine sta davvero, bande comprese;
   4. da li' si calcola il punto dello SCHERMO che sta sopra un pixel scelto del
      FOTOGRAMMA (angolo alto-sinistro, centro, angolo basso-destro);
   5. si manda li' un `pointermove` vero, e si legge la coordinata che la pagina
      **spedirebbe sul filo** — `cl_spedisci()` sostituito da una spia.
   6. lo scarto e' la differenza fra il pixel scelto e quello spedito.

═══════════════════════════════════════════════════════════════════════════
⛔⛔⭐ 22 AGOSTO 2026 — L'ORIGINE NON SI SOTTRAE PIU', E PRIMA SI SOTTRAEVA.

   `fasi/06` §5.5, quarto falso verde.  Il passo 4 si faceva cosi':

       ox = x0 − rect.left · dpr        ← lo scostamento fra DOVE L'IMMAGINE STA
                                          e DOVE LA PAGINA CREDE CHE STIA
       cx = (sx − ox) / dpr

   ⛔ Ma `sx = x0 + …`: `x0` si semplifica, e quel che resta e'
   `cx = rect.left + …`, cioe' un'algebra fra `rect.left` e la conversione della
   pagina, **con l'origine vera cancellata**.  ⇒ Una tela dipinta 50 px fuori
   posto — il difetto del DeX, quello che questa scena nomina come propria
   ragione d'essere — dava **scarto 0 su 20 punti su due motori**.

⇒ Adesso `ox`/`oy` vengono dalla CALIBRAZIONE (l'origine della VISTA, che non
  dipende dalla tela), e c'e' una verifica in piu' che prima non esisteva:

   ⭐ **C0 · L'ORIGINE**: il bordo sinistro DIPINTO deve cadere dove
     `getBoundingClientRect()` dice, cioe' `ox + rect.left · dpr`, entro 1 px.
     ⛔ Se non ci cade, la pagina crede che l'immagine sia altrove, e ogni clic
     e' spostato di quella distanza — anche se il resto dei conti torna.

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

# ⛔ Il fotogramma lo mette `Banco.mostra()`, per la strada del prodotto.
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


def fotografa(nome_file):
    """⛔ I pixel, dalla PIPE: il file si scrive solo con `B37_FOTO=tieni`
       (`06-b37-comune.py` `_grezza`).  ⚠ Un giro intero scriveva 1,5 GB di
       fotogrammi grezzi in un `/tmp` condiviso con altri otto agenti."""
    return B.immagine(nome_file)


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
    d = B.mostra(fl, fa, "grigio orizzontali")
    time.sleep(0.4)
    # ⛔⭐ L'ORIGINE DELLA VISTA, letta sui pixel e INDIPENDENTE dalla tela.
    cal = B.calibra(os.path.join(CARTELLA, "06-b37-coord-cal-%s-%s.rgb24"
                                 % (B.nome, nome)))
    if not cal:
        print("        ⛔ calibrazione fallita: scena %s NON misurata" % nome,
              flush=True)
        return None
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
    # ⛔⭐⭐ L'ORIGINE NON SI SOTTRAE: viene dalla calibrazione.  ⚠ Prima qui
    #    c'era `ox = x0 − rect.left·dpr`, cioe' proprio lo scostamento che
    #    questa scena deve trovare, e sottrarlo lo cancellava.
    ox, oy = cal["ox"], cal["oy"]
    # ⭐ C0 — L'ORIGINE: dove la pagina crede che stia l'immagine, e dove sta.
    atteso_x0 = ox + d["rect"][0] * dpr
    atteso_y0 = oy + d["rect"][1] * dpr
    origine = [round(x0 - atteso_x0, 2), round(y0 - atteso_y0, 2)]
    punti = [("alto-sinistro", 0, 0), ("centro", fl // 2, fa // 2),
             ("basso-destro", fl - 1, fa - 1)]
    righe = []
    print("        disegno %dx%d px su fotogramma %dx%d ⇒ scala %.4f · %s · "
          "strada «%s»" % (ldis, adis, fl, fa, scala, d["image_rendering"],
                           d["strada"]), flush=True)
    print("        C0 origine: dipinta a x=%d,y=%d · la pagina la dichiara a "
          "x=%.1f,y=%.1f ⇒ scarto (%+.1f,%+.1f) %s"
          % (x0, y0, atteso_x0, atteso_y0, origine[0], origine[1],
             "" if max(abs(v) for v in origine) <= 1
             else "⛔⛔ L'IMMAGINE NON STA DOVE LA PAGINA CREDE"), flush=True)
    # ⛔⭐ LA CONTROPROVA, e sta qui apposta: `ox_v` e' la formula di PRIMA del 22
    #    agosto 2026 (`ox = x0 − rect.left·dpr`).  Ogni punto si misura DUE
    #    volte, con l'origine vera e con quella vecchia, e i due scarti si
    #    stampano accanto.  ⇒ Quando c'e' un errore di origine si vede in una
    #    riga sola che il metodo vecchio lo cancellava; quando non c'e', i due
    #    numeri coincidono e la controprova non costa niente.
    ox_v = x0 - d["rect"][0] * dpr
    oy_v = y0 - d["rect"][1] * dpr
    for etichetta, fx, fy in punti:
        sx = x0 + (fx + 0.5) * ldis / fl
        sy = y0 + (fy + 0.5) * adis / fa
        cx = (sx - ox) / dpr
        cy = (sy - oy) / dpr
        rv = json.loads(B.val(MUOVI % ((sx - ox_v) / dpr, (sy - oy_v) / dpr)))
        spv = rv["spediti"]
        vecchio = ([spv[-1]["x"] - fx, spv[-1]["y"] - fy] if spv else None)
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
              "(%+d,%+d)   [col metodo vecchio, che sottraeva l'origine: %s]"
              % (etichetta, fx, fy, ult["x"], ult["y"], dx, dy,
                 ("(%+d,%+d)" % tuple(vecchio)) if vecchio else "niente"),
              flush=True)
        righe.append({"punto": etichetta, "atteso": [fx, fy],
                      "spedito": [ult["x"], ult["y"]], "scarto": [dx, dy],
                      "scarto_metodo_vecchio": vecchio})
    B.scrivi({"tipo": "coordinate", "scena": nome, "fotogramma": [fl, fa],
              "finestra": list(finestra), "scala_pixel": round(scala, 4),
              "disegno_pixel": [ldis, adis],
              "image_rendering": d["image_rendering"], "strada": d["strada"],
              "vista": d["vista"], "vista_pixel": [cal["l"], cal["a"]],
              "origine_vista_pixel": [ox, oy],
              "origine_disegno_pixel": [x0, y0],
              "origine_dichiarata": [round(atteso_x0, 2), round(atteso_y0, 2)],
              "scarto_origine": origine,
              "punti": righe}, iniezione="si")
    return {"punti": righe, "origine": origine}


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
d = B.mostra(1400, 900, "grigio orizzontali")
time.sleep(0.4)
cal4 = B.calibra(os.path.join(CARTELLA, "06-b37-coord-cal-%s-c4.rgb24" % B.nome))
img = fotografa(os.path.join(CARTELLA, "06-b37-coord-%s-c4.rgb24" % B.nome))
e = estremi(img)
if not e or not cal4:
    print("        ⛔ marcatori o calibrazione assenti: C4 NON misurata",
          flush=True)
else:
    x0, x1, y0, y1 = e
    ldis, adis = x1 - x0 + 1, y1 - y0 + 1
    dpr = d["dpr"]
    # ⛔ L'origine viene dalla CALIBRAZIONE, non dal disegno: vedi il cappello.
    ox, oy = cal4["ox"], cal4["oy"]
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
    cal4b = B.calibra(os.path.join(CARTELLA,
                                   "06-b37-coord-cal-%s-c4b.rgb24" % B.nome))
    img2 = fotografa(os.path.join(CARTELLA,
                                  "06-b37-coord-%s-c4b.rgb24" % B.nome))
    e2 = estremi(img2)
    if not e2 or not cal4b:
        print("        ⛔ a cornice assestata i marcatori o la calibrazione NON "
              "si trovano (larghezza del disegno %s CSS): la seconda meta' di "
              "C4 e' NON MISURATA, e si dice" % prec, flush=True)
    if e2 and cal4b:
        x0b, x1b, y0b, y1b = e2
        d2 = json.loads(B.val(
            "JSON.stringify({rect: (function(){const r=$('schermo')"
            ".getBoundingClientRect(); return [r.left,r.top,r.width,r.height];"
            "})(), dpr: devicePixelRatio})"))
        ldis2 = x1b - x0b + 1
        adis2 = y1b - y0b + 1
        ox2, oy2 = cal4b["ox"], cal4b["oy"]
        # ⭐ C0 anche qui: dopo un ridimensionamento l'origine e' il posto in cui
        #    la cornice puo' restare indietro senza che nessun conto se ne accorga.
        orig4 = [round(x0b - (ox2 + d2["rect"][0] * d2["dpr"]), 2),
                 round(y0b - (oy2 + d2["rect"][1] * d2["dpr"]), 2)]
        print("        C0 a cornice assestata: dipinta a x=%d · dichiarata a "
              "%.1f ⇒ scarto (%+.1f,%+.1f)"
              % (x0b, ox2 + d2["rect"][0] * d2["dpr"], orig4[0], orig4[1]),
              flush=True)
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
                      "atteso": [fx, fy], "scarto_origine": orig4,
                      "origine_vista_pixel": [ox2, oy2],
                      "scarto": [u["x"] - fx, u["y"] - fy]}, iniezione="si")
            tutte.append(("C4 sotto il dito",
                          {"origine": orig4,
                           "punti": [{"punto": "centro", "atteso": [fx, fy],
                                      "spedito": [u["x"], u["y"]],
                                      "scarto": [u["x"] - fx,
                                                 u["y"] - fy]}]}))

# ---------------------------------------------------------------------------
print("\n== 06-b37 · %s — il verdetto sulle coordinate" % B.nome, flush=True)
guasti = 0
punti_totali = 0
origini = []
for nome, d_sc in tutte:
    if not d_sc or not d_sc.get("punti"):
        print("    NO  %s: scena non misurata" % nome, flush=True)
        guasti += 1
        continue
    righe = d_sc["punti"]
    # ⛔⭐ C0 — L'ORIGINE, e si giudica PRIMA degli scarti: se l'immagine non sta
    #    dove la pagina crede, gli scarti dei punti possono tornare a zero lo
    #    stesso (e per due giorni sono tornati a zero: `fasi/06` §5.5).
    org = d_sc.get("origine")
    origini.append((nome, org))
    if org is None:
        print("    NO  %s: l'origine non e' stata misurata" % nome, flush=True)
        guasti += 1
    elif max(abs(v) for v in org) <= 1:
        print("    OK  %s · C0: l'immagine sta dove `getBoundingClientRect()` "
              "dice, scarto (%+.1f,%+.1f) px" % (nome, org[0], org[1]),
              flush=True)
    else:
        print("    NO  %s · C0: ⛔⛔ L'IMMAGINE NON STA DOVE LA PAGINA CREDE — "
              "scarto (%+.1f,%+.1f) px.  E' il difetto del DeX: ogni clic "
              "finisce spostato di tanto, e nessuno scarto sui punti se ne "
              "accorge se l'origine viene sottratta"
              % (nome, org[0], org[1]), flush=True)
        guasti += 1
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
print("    --  punti misurati in tutto: %d su %d scene (il denominatore dello "
      "zero) · origini misurate: %s"
      % (punti_totali, len(tutte), [(n, o) for n, o in origini]), flush=True)
B.scrivi({"tipo": "coordinate-verdetto", "scene": len(tutte),
          "punti": punti_totali, "guasti": guasti,
          "origini": [{"scena": n, "scarto": o} for n, o in origini]},
         iniezione="si")
sys.exit(1 if guasti else 0)
