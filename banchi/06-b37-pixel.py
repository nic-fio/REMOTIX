#!/usr/bin/env python3
"""06-b37-pixel.py — ⛔ LA SCALA, LE BANDE E IL MEZZO PIXEL, LETTI SUI PIXEL.

    python3 banchi/06-b37-pixel.py <porta> <display> <pid-browser> <nome> <esiti.jsonl>

⛔ INVARIANTE **I8**: «il metro e' quel che l'utente vede, non il numero che esce
   dal banco».  ⇒ Qui il fotogramma si INIETTA nella pagina, ⚠ ma il verdetto si
   legge **fotografando lo schermo X** e contando i pixel: la scala, le bande e
   il mezzo pixel del `margin: 0 auto` si vedono li', non in `cornice()`.

⛔ CHE COSA E' INIEZIONE, E SI DICHIARA IN OGNI RIGA (`iniezione: si`):
   il fotogramma non arriva dal filo.  Si costruisce una `<canvas>` con un
   disegno noto — righe verticali spesse **UN pixel**, che e' il caso peggiore
   del ricampionamento e insieme il caso vero (un terminale) — e la si consegna
   a `schermo.mostra()`, cioe' la **stessa** funzione che riceve i fotogrammi
   veri.  ⚠ Quel che NON e' provato cosi': la decodifica, il filo, e la misura
   che il server concede davvero.
   ⛔ E la strada si SCEGLIE COME LA SCEGLIE IL PRODOTTO, e si scrive in ogni
      riga (`strada`): fino al 22 agosto 2026 qui c'era `schermo.deposito = c;
      schermo.componi()`, che dal passaggio a `bitmaprenderer` **non dipingeva
      piu' niente** — `[M]` quel giorno, marcatori assenti in 12 fotografie su 12.

⛔ CHE COSA SU QUESTO PALCO NON E' MISURABILE PER COSTRUZIONE:
   · i tempi fra «disegno finito» e «pixel acceso» (`STUDI.md` §web §6.2);
   · il ricampionamento **su GPU vera**: qui rasterizza il software.  ⇒ un
     «grigio» trovato qui e' una prova che l'offset frazionario ARRIVA fino ai
     pixel; un «niente grigio» NON promette che su GPU vera sia lo stesso.
   · il DeX: il telefono ce l'ha l'utente.

═══════════════════════════════════════════════════════════════════════════
⛔ L'ATTESO, DICHIARATO PRIMA

  X1 con la tela della misura della finestra (larghezza PARI) la scala vale
     **1,000**, `image-rendering` e' `pixelated`, e le righe da un pixel escono
     **nette**: nessuna colonna grigia.
  X1-bis ⛔⭐ **AGGIUNTA IL 22 AGOSTO 2026** (`fasi/06` §5.5, primo falso verde):
     il disegno **RIEMPIE** la finestra.  ⚠ «Il disegno misura esattamente il
     fotogramma» e' vero anche quando il fotogramma e' **30 px piu' stretto
     della finestra**, perche' e' il banco stesso a iniettare un fotogramma
     della misura che la pagina ha chiesto.  ⇒ Il disegno si confronta con la
     **vista letta sui PIXEL** (le strisce di `06-b37-comune.py`), che non viene
     ne' dalla pagina ne' dal fotogramma: `W − ceil(dpr) ≤ disegno ≤ W`.
  X2 ⭐ IL MEZZO PIXEL, e qui parto dall'ipotesi che il giudizio «tutto perfetto»
     sia FALSO: con la larghezza della finestra DISPARI la tela perde un pixel
     per la parita' (§4.5), avanza **1 pixel** che `margin: 0 auto` divide in
     **due mezzi** ⇒ il disegno comincia a **x,5** ⇒ mi aspetto colonne GRIGIE.
  X3 le bande stanno FUORI dal buffer: `canvas.width` vale esattamente il
     fotogramma, e i pixel a fianco del disegno sono neri del genitore.
  X4 con tela e vista di forma diversa **si impagina, non si stira**
     (`SPECIFICHE.md` §6.2): il rapporto dei lati MISURATO SUI PIXEL resta
     quello del fotogramma entro lo 0,5 %.
"""
import importlib.util
import math
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

# ---------------------------------------------------------------------------
# ⛔ Il disegno di prova (righe da un pixel + i quattro marcatori) e la strada
#    per metterlo nella pagina stanno in `06-b37-comune.py`: `Banco.mostra()`.
#    ⚠ Qui c'era un `schermo.deposito = c; schermo.componi()` che dal passaggio a
#      `bitmaprenderer` non dipingeva piu' NIENTE.


def trova(img, prova):
    m = prova(img)
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()), int(m.sum())


def rosso(i):
    return (i[:, :, 0] > 170) & (i[:, :, 1] < 90) & (i[:, :, 2] < 90)


def verde(i):
    return (i[:, :, 1] > 170) & (i[:, :, 0] < 90) & (i[:, :, 2] < 90)


def blu(i):
    return (i[:, :, 2] > 170) & (i[:, :, 0] < 90) & (i[:, :, 1] < 90)


def giallo(i):
    return (i[:, :, 0] > 170) & (i[:, :, 1] > 170) & (i[:, :, 2] < 90)


def fotografa(nome_file):
    sch = B.x("xdpyinfo").stdout
    dim = [r for r in sch.splitlines() if "dimensions:" in r]
    l, a = (int(v) for v in dim[0].split()[1].split("x"))
    ok, err = B.fotografa(nome_file, l, a)
    if not ok:
        raise RuntimeError("ffmpeg: " + err[:300])
    d = np.fromfile(nome_file, dtype=np.uint8)
    return d.reshape((a, l, 3))


def misura_scena(etichetta, larghezza_finestra, altezza_finestra, fl, fa,
                 cartella):
    B.ridimensiona(larghezza_finestra, altezza_finestra)
    time.sleep(0.8)
    s = B.js("stato()")
    d = B.mostra(fl, fa, "righe orizzontali")
    time.sleep(0.6)
    # ⛔⭐ LA VISTA VERA, letta sui pixel: e' l'unico numero di questa scena che
    #    non viene ne' dalla pagina ne' dal fotogramma che il banco ha iniettato.
    cal = B.calibra(os.path.join(cartella, "06-b37-cal-%s-%s.rgb24"
                                 % (B.nome, etichetta)))
    percorso = os.path.join(cartella, "06-b37-%s-%s.rgb24" % (B.nome, etichetta))
    img = fotografa(percorso)

    r = trova(img, rosso)
    v = trova(img, verde)
    b = trova(img, blu)
    gi = trova(img, giallo)
    esito = {"tipo": "pixel", "scena": etichetta,
             "finestra_chiesta": [larghezza_finestra, altezza_finestra],
             "fotogramma": [fl, fa], "pagina": d, "cw": s["cw"], "ch": s["ch"],
             "dpr": s["dpr"], "fotografia": B.percorso_foto(percorso),
             "strada": d["strada"],
             "vista_pixel": ([cal["l"], cal["a"]] if cal else None),
             "vista_origine_pixel": ([cal["ox"], cal["oy"]] if cal else None)}

    if not (r and v and b and gi):
        esito["trovato"] = False
        print("        ⛔ i marcatori NON si trovano nella fotografia "
              "(rosso=%s verde=%s blu=%s giallo=%s): niente verdetto"
              % (bool(r), bool(v), bool(b), bool(gi)), flush=True)
        B.scrivi(esito, iniezione="si")
        return esito

    x0, x1 = r[0], v[1]
    y0, y1 = b[2], gi[3]
    larg, alt = x1 - x0 + 1, y1 - y0 + 1
    esito["disegno_pixel"] = [larg, alt]
    esito["origine_pixel"] = [x0, y0]

    # ⛔ Le righe da un pixel: si legge una riga in mezzo al disegno, FRA i
    #    marcatori, e si contano le colonne che non sono ne' nere ne' bianche.
    riga = img[(y0 + y1) // 2, x0 + 6:x1 - 6, :]
    lum = riga.mean(axis=1)
    grigi = int(((lum > 60) & (lum < 195)).sum())
    esito["colonne"] = int(len(lum))
    esito["colonne_grigie"] = grigi
    esito["grigie_per_cento"] = round(100.0 * grigi / max(1, len(lum)), 1)

    # ⛔⭐ LE BANDE, MISURATE DOVE STANNO DAVVERO — e non e' un dettaglio di
    #    comodo: la prima stesura di questo banco guardava SEMPRE a destra e a
    #    sinistra, e su un fotogramma piu' largo che alto li' non c'e' nessuna
    #    banda (il disegno tocca i due bordi).  Leggeva il bordo della finestra
    #    del browser e lo chiamava «banda non nera»: un rosso su codice sano.
    # ⇒ Lo spessore delle quattro bande si prende dalla pagina (tela contro
    #   genitore) e i PIXEL si guardano li' dentro.
    gx, gy, gl, ga = d["genitore"]
    rx, ry, rl, ra = d["rect"]
    dpr = d["dpr"]
    bande = {"sinistra": round((rx - gx) * dpr), "alta": round((ry - gy) * dpr),
             "destra": round((gx + gl - rx - rl) * dpr),
             "bassa": round((gy + ga - ry - ra) * dpr)}
    esito["bande_px"] = bande
    letture = {}
    if bande["sinistra"] >= 4:
        letture["sinistra"] = float(img[y0 + 4:y1 - 4,
                                        max(0, x0 - bande["sinistra"] + 2):x0 - 1,
                                        :].mean())
    if bande["destra"] >= 4:
        letture["destra"] = float(img[y0 + 4:y1 - 4,
                                      x1 + 2:x1 + bande["destra"] - 1, :].mean())
    if bande["alta"] >= 4:
        letture["alta"] = float(img[max(0, y0 - bande["alta"] + 2):y0 - 1,
                                    x0 + 4:x1 - 4, :].mean())
    if bande["bassa"] >= 4:
        letture["bassa"] = float(img[y1 + 2:y1 + bande["bassa"] - 1,
                                     x0 + 4:x1 - 4, :].mean())
    esito["bande_lette"] = {k: round(v, 1) for k, v in letture.items()}
    esito["fuori_media"] = (round(max(letture.values()), 1) if letture else -1)

    rap_dis = larg / float(alt)
    rap_fot = fl / float(fa)
    esito["rapporto_disegno"] = round(rap_dis, 4)
    esito["rapporto_fotogramma"] = round(rap_fot, 4)
    esito["stira_per_cento"] = round(100 * abs(rap_dis - rap_fot) / rap_fot, 2)
    esito["image_rendering"] = d["stile"][2]
    # ⛔⭐ IL LIMITE INFERIORE: il disegno RIEMPIE la finestra?  `W` non viene
    #    dalla pagina, e senza questa riga una tela 30 px piu' stretta era verde.
    if cal:
        esito["avanzo_pixel"] = cal["l"] - larg
        esito["avanzo_minimo"] = cal["l_max"] - larg
        esito["avanzo_massimo"] = int(math.ceil(d["dpr"]))
    esito["rect_sinistro_fisico"] = round(d["rect_fisico"][0], 3)
    esito["mezzo_pixel"] = abs(d["rect_fisico"][0]
                               - round(d["rect_fisico"][0])) > 0.01

    print("        disegno %dx%d px · fotogramma %dx%d · rect.left fisico %.2f"
          " %s · %s · colonne grigie %d/%d (%.1f %%)"
          % (larg, alt, fl, fa, d["rect_fisico"][0],
             "⛔ FRAZIONARIO" if esito["mezzo_pixel"] else "intero",
             d["stile"][2], grigi, len(lum), esito["grigie_per_cento"]),
          flush=True)
    print("        bande %s ⇒ letto %s (0 = nero)"
          % (bande, esito["bande_lette"]), flush=True)
    B.scrivi(esito, iniezione="si")
    return esito


# ---------------------------------------------------------------------------
print("== 06-b37 · %s — i pixel del disegno (iniezione dichiarata)" % B.nome,
      flush=True)
if not B.aspetta_pagina():
    print("    NO  la pagina non si e' mai annunciata", flush=True)
    sys.exit(3)
if not B.trova_finestra():
    print("    NO  nessuna finestra X per il pid %s" % B.pidbr, flush=True)
    sys.exit(3)

if not B.giudica_palco():
    print("    ⇒   nessun verdetto sul prodotto da questo giro", flush=True)
    sys.exit(4)

CARTELLA = os.environ.get("PIXEL_DIR", "/tmp/06-b37-pixel")
os.makedirs(CARTELLA, exist_ok=True)
guasti = 0
scene = []

# ⛔ La larghezza della finestra si sceglie MISURANDO, non calcolando: si cerca
#    una finestra che dia un contenuto PARI e una che lo dia DISPARI, e si dice
#    quale finestra X e' stata.
misure = {}
for L in (1000, 1001, 1002):
    B.ridimensiona(L, 760)
    time.sleep(0.7)
    misure[L] = B.js("stato()")
pari = next((L for L, s in misure.items() if s["cw"] % 2 == 0), None)
dispari = next((L for L, s in misure.items() if s["cw"] % 2 == 1), None)
if pari is None or dispari is None:
    print("    NO  non ho trovato una finestra con contenuto pari E una con "
          "contenuto dispari: %s" % {L: s["cw"] for L, s in misure.items()},
          flush=True)
    sys.exit(3)
print("    --  finestra X %d ⇒ contenuto %d CSS (PARI) · finestra X %d ⇒ "
      "contenuto %d CSS (DISPARI)"
      % (pari, misure[pari]["cw"], dispari, misure[dispari]["cw"]), flush=True)

# --- X1: la tela combacia con la finestra, larghezza PARI ------------------
print("\n    --  X1 · tela = finestra, larghezza PARI (la condizione normale)",
      flush=True)
B.ridimensiona(pari, 760)
time.sleep(0.6)
s = B.js("stato()")
e1 = misura_scena("x1-pari", pari, 760, s["tela"][0], s["tela"][1], CARTELLA)
scene.append(e1)

# --- X2: la tela combacia con la finestra, larghezza DISPARI ---------------
print("\n    --  X2 · tela = finestra, contenuto DISPARI (il mezzo pixel)",
      flush=True)
B.ridimensiona(dispari, 760)
time.sleep(0.6)
s = B.js("stato()")
e2 = misura_scena("x2-dispari", dispari, 760, s["tela"][0], s["tela"][1],
                  CARTELLA)
scene.append(e2)

# --- X3/X4: tela PIU' GRANDE della vista: si impagina, non si stira ---------
print("\n    --  X4 · fotogramma 1400×900 in una finestra piu' piccola "
      "(e' il caso `?adatta=no` e il ripiego di §6.3)", flush=True)
e3 = misura_scena("x4-bande", pari, 760, 1400, 900, CARTELLA)
scene.append(e3)

print("\n    --  X4b · fotogramma 640×480 (piu' PICCOLO della finestra): "
      "si ingrandisce o resta 1:1?", flush=True)
e4 = misura_scena("x4b-piccolo", pari, 760, 640, 480, CARTELLA)
scene.append(e4)

# --- X5: la finestra SOTTO il minimo di §4.5 --------------------------------
print("\n    --  X5 · finestra piu' stretta del minimo di §4.5: la pagina "
      "arrotonda IN SU a 320 e l'avanzo DEVE tornare come banda", flush=True)
B.ridimensiona(250, 760)
time.sleep(0.8)
s5 = B.js("stato()")
e5 = None
if s5["vista"][0] >= 320:
    # ⛔ 3.10: una misura che non si e' potuta fare non e' una misura riuscita.
    print("        ⚠ questo motore NON stringe la finestra sotto il suo minimo "
          "(vista %dx%d): scena NON MISURATA, e si dice"
          % (s5["vista"][0], s5["vista"][1]), flush=True)
else:
    e5 = misura_scena("x5-minimo", 250, 760, s5["tela"][0], s5["tela"][1],
                      CARTELLA)
    scene.append(e5)

# ---------------------------------------------------------------------------
print("\n== 06-b37 · %s — il verdetto sui pixel" % B.nome, flush=True)

for e, nome, atteso_scala1 in ((e1, "X1 pari", True), (e2, "X2 dispari", True)):
    if not e.get("disegno_pixel"):
        guasti += 1
        continue
    larg = e["disegno_pixel"][0]
    fl = e["fotogramma"][0]
    if larg == fl:
        print("    OK  %s: il disegno misura %d px, esattamente il fotogramma "
              "⇒ scala 1,000 SUI PIXEL (strada «%s»)"
              % (nome, larg, e["strada"]), flush=True)
    else:
        print("    NO  %s: disegno %d px contro un fotogramma di %d ⇒ scala %.4f"
              % (nome, larg, fl, larg / float(fl)), flush=True)
        guasti += 1
    # ⛔⭐ X1-bis — E RIEMPIE LA FINESTRA?  Senza questa domanda «il disegno e'
    #    esattamente il fotogramma» resta vero anche con una tela 30 px piu'
    #    stretta della finestra: il fotogramma lo sceglie il banco a partire
    #    dalla tela, quindi combacia sempre con se' stesso.
    if e.get("vista_pixel") is None:
        print("    NO  ⛔ %s: nessuna calibrazione sui pixel ⇒ il limite "
              "INFERIORE non e' stato giudicato, e non e' uno zero" % nome,
              flush=True)
        guasti += 1
    else:
        av, amm = e["avanzo_pixel"], e["avanzo_massimo"]
        if e["avanzo_minimo"] < 0:
            av = e["avanzo_minimo"]     # deborda oltre la maschera permissiva
        if -1 <= av <= amm:
            print("    OK  %s: e RIEMPIE la finestra — vista vera %d px, "
                  "disegno %d px ⇒ avanzo %d px (massimo legale %d)"
                  % (nome, e["vista_pixel"][0], larg, av, amm), flush=True)
        elif av > amm:
            print("    NO  ⛔⛔ %s: BANDA NERA PERMANENTE — vista vera %d px, "
                  "disegno %d px ⇒ %d colonne di desktop che l'utente non vede "
                  "mai (massimo legale %d)"
                  % (nome, e["vista_pixel"][0], larg, av, amm), flush=True)
            guasti += 1
        else:
            print("    NO  ⛔⛔ %s: il disegno DEBORDA dalla finestra — vista "
                  "vera %d px, disegno %d px (%+d)"
                  % (nome, e["vista_pixel"][0], larg, -av), flush=True)
            guasti += 1
    if e["image_rendering"] != "pixelated":
        print("    ⚠   %s: `image-rendering` vale «%s», non «pixelated»"
              % (nome, e["image_rendering"]), flush=True)

# ⭐ IL PUNTO DELLA SCENA: il mezzo pixel si vede o no?
print("    --  X2 · rect.left in pixel fisici: %s (X1) contro %s (X2)"
      % (e1.get("rect_sinistro_fisico"), e2.get("rect_sinistro_fisico")),
      flush=True)
if e2.get("mezzo_pixel"):
    print("    ⛔  X2: il disegno comincia a un OFFSET FRAZIONARIO — il mezzo "
          "pixel di `margin: 0 auto` ESISTE, ed e' misurato", flush=True)
    if e2.get("colonne_grigie", 0) > 0.05 * e2.get("colonne", 1):
        print("    ⛔⛔ e ARRIVA FINO AI PIXEL: %.1f %% di colonne grigie contro "
              "%.1f %% nella scena pari — il testo da un pixel si sfrangia"
              % (e2["grigie_per_cento"], e1.get("grigie_per_cento", -1)),
              flush=True)
    else:
        print("    --  ⚠ ma NON arriva ai pixel su questo rasterizzatore: "
              "%.1f %% di colonne grigie (pari: %.1f %%).  ⛔ Il rasterizzatore "
              "qui e' software: su GPU vera resta `[?]`"
              % (e2["grigie_per_cento"], e1.get("grigie_per_cento", -1)),
              flush=True)
else:
    print("    OK  X2: nessun offset frazionario — il mezzo pixel NON si "
          "presenta a questa misura", flush=True)

# X3 — le bande fuori dal buffer.
for e, nome in ((e3, "X4 bande"), (e4, "X4b piccolo")):
    if not e.get("disegno_pixel"):
        guasti += 1
        continue
    if e["pagina"]["buffer"] == e["fotogramma"]:
        print("    OK  %s: il buffer vale ESATTAMENTE il fotogramma %s — le "
              "bande sono fuori" % (nome, e["fotogramma"]), flush=True)
    else:
        print("    NO  %s: buffer %s ≠ fotogramma %s: le bande sono DENTRO"
              % (nome, e["pagina"]["buffer"], e["fotogramma"]), flush=True)
        guasti += 1
    if not e.get("bande_lette"):
        print("    --  %s: nessuna banda da misurare (il disegno tocca i "
              "quattro bordi)" % nome, flush=True)
    elif e["fuori_media"] > 12:
        print("    NO  %s: una banda NON e' nera: %s"
              % (nome, e["bande_lette"]), flush=True)
        guasti += 1
    else:
        print("    OK  %s: le bande sono NERE e stanno fuori dal buffer: %s px, "
              "letto %s" % (nome, e["bande_px"], e["bande_lette"]), flush=True)
    if e["stira_per_cento"] <= 0.5:
        print("    OK  %s: si impagina, non si stira — rapporto dipinto %.4f "
              "contro %.4f del fotogramma (%.2f %%)"
              % (nome, e["rapporto_disegno"], e["rapporto_fotogramma"],
                 e["stira_per_cento"]), flush=True)
    else:
        print("    NO  %s: il disegno e' STIRATO del %.2f %% (rapporto %.4f "
              "contro %.4f)" % (nome, e["stira_per_cento"],
                                e["rapporto_disegno"],
                                e["rapporto_fotogramma"]), flush=True)
        guasti += 1

if e4.get("disegno_pixel"):
    if e4["disegno_pixel"][0] == 640:
        print("    --  X4b: un fotogramma piu' PICCOLO della finestra resta "
              "1:1 (640 px dipinti su 640) — `cornice()` taglia a 1, ⛔ e il "
              "commento di `src/pagina.html:2004` dice il contrario", flush=True)
    else:
        print("    --  X4b: un fotogramma piu' piccolo della finestra viene "
              "INGRANDITO a %d px" % e4["disegno_pixel"][0], flush=True)

if e5 and e5.get("disegno_pixel"):
    atteso = e5["cw"] * e5["dpr"]
    print("    --  X5: vista %s, tela chiesta %s ⇒ disegno %d px su una "
          "finestra di %.0f fisici: scala %.3f — ⛔ e' l'unico caso in cui la "
          "scala NON puo' valere 1, ed e' DICHIARATO (§4.5)"
          % (s5["vista"], e5["fotogramma"], e5["disegno_pixel"][0], atteso,
             e5["disegno_pixel"][0] / float(e5["fotogramma"][0])), flush=True)
    if e5["stira_per_cento"] > 0.5:
        print("    NO  X5: e sotto il minimo il disegno e' STIRATO del %.2f %%"
              % e5["stira_per_cento"], flush=True)
        guasti += 1
    else:
        print("    OK  X5: anche sotto il minimo si impagina, non si stira "
              "(%.2f %%)" % e5["stira_per_cento"], flush=True)

# ---------------------------------------------------------------------------
# ⛔⭐ IL MEZZO PIXEL, CONTATO — e non solo osservato.  `fasi/06` §5.5: *«il mezzo
#    pixel e' osservato e non incrementa nessun conto»*.  ⇒ Qui i due conti che
#    chiudono (o lasciano aperta) la terza `[?]` di `SPECIFICHE.md` §6.1-bis.
# ⚠ Il conto si fa SOLO sulle scene a scala 1 (`pixelated`): dove la scala non
#   vale 1 il grigio c'e' per il ricampionamento dichiarato — X5, sotto il minimo
#   di §4.5, ne fa 118 su 222 ed e' giusto cosi'.  Mescolarle direbbe «il mezzo
#   pixel arriva ai pixel» a proposito di tutt'altro.
a_uno = [e for e in scene if e.get("disegno_pixel")
         and e.get("image_rendering") == "pixelated"]
mezzi = [e for e in a_uno if e.get("mezzo_pixel")]
arrivati = [e for e in mezzi if e.get("colonne_grigie", 0) > 0]
colonne_tot = sum(e.get("colonne", 0) for e in a_uno)
grigie_tot = sum(e.get("colonne_grigie", 0) for e in a_uno)
print("\n    ⭐ IL MEZZO PIXEL, COL DENOMINATORE (solo le %d scene a scala 1, "
      "`pixelated`): scene con un `rect.left` frazionario **%d** · di queste, "
      "quelle in cui il mezzo pixel ARRIVA ai pixel: **%d** · colonne grigie in "
      "tutto: **%d su %d**"
      % (len(a_uno), len(mezzi), len(arrivati), grigie_tot, colonne_tot),
      flush=True)
print("    ⚠  E QUEL CHE RESTA `[?]`: qui rasterizza il software di Xvfb.  Uno "
      "zero qui NON promette lo stesso su GPU vera ne' su DeX — la `[?]` 3 di "
      "§6.1-bis resta APERTA su quei due terreni, e chiusa su questo",
      flush=True)
B.scrivi({"tipo": "pixel-verdetto", "scene": len(scene), "guasti": guasti,
          "mezzo_pixel_scene": len(mezzi), "mezzo_pixel_ai_pixel": len(arrivati),
          "colonne_grigie": grigie_tot, "colonne": colonne_tot,
          "strada": e1.get("strada")}, iniezione="si")
print("\n    --  le fotografie grezze (rgb24) stanno in %s" % CARTELLA,
      flush=True)
sys.exit(1 if guasti else 0)
