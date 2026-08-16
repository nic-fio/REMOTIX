#!/usr/bin/env python3
"""03-marca-certifica.py — ⛔ IL BANCO SI CERTIFICA PRIMA DELLA MISURA.

    python3 03-marca-certifica.py --cartella /tmp/remotix-03-scena-7602 \
        --esiti 03-scena-esiti.jsonl --giro c1

===========================================================================
⛔ PERCHE' ESISTE — `LEZIONI.md` §1.2, e non e' una formalita'

*«Si accerta che il banco sappia produrre il risultato atteso PRIMA di
puntarlo sull'incognita.  Altrimenti un esito negativo e' ambiguo fra
"l'incognita non funziona" e "il banco non funzionava".»*

E il rovescio, che e' quello che qui costa di piu' (`STUDI.md` §web §6.3, controllo
**P3**): *«un rilevatore che dice sempre si' misura zero ed e' felice a
torto»*.  ⇒ ogni controllo positivo qui dentro ha il suo gemello negativo, e
un controllo positivo senza gemello NON conta.

===========================================================================
I CONTROLLI, e che cosa dimostra ciascuno

  P1  positivo sintetico     il lettore trova una marca che c'e', e i valori
                             tornano ESATTI (non «simili»)
  P2  negativo per costruzione  su sei scene SENZA marca il lettore dice di no,
                             e la sesta e' un fotogramma vero con il blocco
                             coperto da contenuto qualunque
  P3  ⭐ negativo di massa    N blocchi di rumore casuale: ZERO falsi positivi.
                             E' il controllo che smaschera un rilevatore che
                             dice sempre si'
  P4  ⭐ la codifica          la marca sopravvive a HEVC Main10?  Fino a che QP?
                             ⛔ Non si da' per scontato: si misura, QP per QP
  P5  la marca rotta          invertendo un bit, il lettore deve RIFIUTARE, non
                             leggere un numero sbagliato come se fosse giusto
  P6  ⭐ i due pittori         quel che la C ha dipinto e quel che la Python
                             rilegge devono coincidere.  E' l'unico controllo
                             incrociato fra i due file
  P7  la scena si muove       fotogrammi consecutivi hanno disegni consecutivi e
                             istanti crescenti — cioe' la scena SI MUOVE
                             SEMPRE, misurato invece che promesso
  P8  negativo del conteggio  un blocco condiviso che non c'e' deve dare
                             «non c'e'» con il perche', non «zero disegni»
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys

import numpy as np

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import importlib.util as _iu
_spec = _iu.spec_from_file_location("marca", os.path.join(QUI, "03-marca.py"))
marca = _iu.module_from_spec(_spec)
_spec.loader.exec_module(marca)

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


class Conto:
    def __init__(self):
        self.controlli = []

    def esito(self, nome, passato, dimostra, misura=None):
        self.controlli.append({"nome": nome, "passato": bool(passato),
                               "dimostra": dimostra, "misura": misura})
        c = VERDE + "OK" if passato else ROSSO + "NO"
        print("    %s%s  %-28s %s" % (c, GRIGIO, nome, dimostra))
        if misura is not None:
            print("        %s" % json.dumps(misura, ensure_ascii=False))

    @property
    def passati(self):
        return sum(1 for c in self.controlli if c["passato"])

    @property
    def totali(self):
        return len(self.controlli)


def fondo_sfumato(w, h, seme=0):
    yy = np.linspace(0, 1, h)[:, None]
    xx = np.linspace(0, 1, w)[None, :]
    f = ((yy + xx) / 2 * 200 + 30).astype(np.uint8)
    img = np.repeat(f[:, :, None], 3, axis=2).copy()
    if seme:
        rng = np.random.RandomState(seme)
        img = np.clip(img.astype(np.int32) + rng.randint(-8, 9, img.shape), 0, 255
                      ).astype(np.uint8)
    return img


# ───────────────────────────────────────────────────────────────────────────
def p1_positivo(C, w=1280, h=720):
    print("\n\033[1m== P1 · il controllo POSITIVO — lo strumento sa trovare quel che c'e'\033[0m")
    casi = [
        ("primo disegno",       0,          0,                "g1"),
        ("un disegno qualunque", 4127,      79226085474,      "g1"),
        ("⛔ il massimo",       0xFFFFFFFF, (1 << 48) - 1,    "giro-lunghissimo-per-il-nome"),
        ("un altro giro",       7,          123456789012,     "g2"),
    ]
    tutti = True
    for nome, disegno, istante, giro in casi:
        img = fondo_sfumato(w, h)
        marca.dipingi_marca(img, disegno, istante, marca.fnv1a32(giro))
        r = marca.leggi_marca(img)
        bene = (r["c_e"] and r["disegno"] == disegno and r["istante_us"] == istante
                and r["giro"] == marca.fnv1a32(giro) and r["scorrimento_provato"] == [0, 0])
        tutti = tutti and bene
        C.esito("P1 " + nome, bene,
                "la marca c'e' e i tre campi tornano ESATTI",
                {"atteso": [disegno, istante, marca.fnv1a32(giro)],
                 "letto": [r.get("disegno"), r.get("istante_us"), r.get("giro")],
                 "perche": r.get("perche")})
    # ⛔⭐ LO SCORRIMENTO, E IL CONTROLLO CHE LA PRIMA STESURA AVEVA SCRITTO
    #     SBAGLIATO — trovato girando, 13 agosto 2026.
    #
    #     La prima stesura pretendeva che, su un'immagine spostata di d px, il
    #     lettore dichiarasse `scorrimento == [d, d]`.  ⛔ E' rosso, e aveva
    #     ragione il codice: la cella e' larga 24 px e si legge il quadrato
    #     centrale al 50 %, quindi a scorrimento 0 la finestra di lettura sta
    #     ANCORA dentro la cella giusta — il lettore legge bene alla prima
    #     posizione e non ha nessuna ragione di provarne altre.
    #     ⇒ il campo NON misura di quanto l'immagine e' spostata: dice a quale
    #       posizione la lettura ha funzionato.  Si chiama `scorrimento_provato`
    #       apposta (`LEZIONI.md` §1.13: due grandezze sotto un nome solo).
    #
    # ⇒ Quel che si prova qui e' la proprieta' che serve davvero, ed e' un
    #   NUMERO invece di un si'/no: **fino a quanti pixel di scorrimento la
    #   marca si rilegge ESATTA?**  E' il margine che la fase 3 ha quando la
    #   tela del browser non e' allineata al pixel.
    limite = None
    dettaglio = {}
    for d in range(0, 15):
        img = fondo_sfumato(w, h)
        marca.dipingi_marca(img, 99, 555, marca.fnv1a32("g1"))
        spostata = np.roll(np.roll(img, d, axis=0), d, axis=1)
        r = marca.leggi_marca(spostata)
        esatto = bool(r["c_e"] and r["disegno"] == 99 and r["istante_us"] == 555)
        dettaglio[d] = esatto
        if esatto:
            limite = d
        else:
            break
    bene = limite is not None and limite >= 4
    tutti = tutti and bene
    C.esito("P1 ⭐ margine di scorrimento", bene,
            "la marca si rilegge ESATTA fino a %s px di scorrimento diagonale "
            "(il minimo dichiarato e' 4)" % limite,
            {"limite_px": limite, "provati": dettaglio,
             "nota": "⚠ `scorrimento_provato` NON e' lo scorrimento vero: e' la "
                     "posizione a cui la lettura ha funzionato"})
    return tutti


def p2_negativo(C, w=1280, h=720, vero=None):
    print("\n\033[1m== P2 · il controllo NEGATIVO — la marca non c'e' e NON la trovo\033[0m")
    scene = {
        "nero":     np.zeros((h, w, 3), np.uint8),
        "bianco":   np.full((h, w, 3), 255, np.uint8),
        "sfumatura": fondo_sfumato(w, h),
        "rumore":   np.random.RandomState(11).randint(0, 256, (h, w, 3), dtype=np.uint8),
        "scacchiera": (np.indices((h, w)).sum(0) % 2 * 255).astype(np.uint8)[:, :, None]
                      .repeat(3, axis=2),
    }
    if vero is not None:
        # ⛔ IL NEGATIVO CHE CONTA: un fotogramma VERO della scena, con il
        #    blocco della marca coperto da un pezzo di scena preso altrove.
        #    Le altre cinque sono scene di laboratorio; questa e' la sola che
        #    somiglia a quel che il lettore vedra' quando la marca manca
        #    davvero — un desktop qualunque sotto le celle.
        coperto = vero.copy()
        x0, y0, bw, bh = marca.GEOMETRIA.blocco()
        q = marca.GEOMETRIA.quiete
        sy, sx = y0 + bh + 2 * q + 20, x0
        if sy + bh + 2 * q < coperto.shape[0]:
            coperto[y0 - q:y0 + bh + q, x0 - q:x0 + bw + q] = \
                vero[sy - q:sy + bh + q, sx - q:sx + bw + q]
            scene["⭐ fotogramma vero, marca coperta"] = coperto
    tutti = True
    for nome, img in scene.items():
        r = marca.leggi_marca(img)
        bene = not r["c_e"]
        tutti = tutti and bene
        C.esito("P2 " + nome, bene,
                "il lettore dice di NO, e dice perche'",
                {"c_e": r["c_e"], "perche": (r.get("perche") or "")[:150],
                 "disegno_letto_a_torto": r.get("disegno")})
    # ⛔ E il negativo di forma: un fotogramma troppo piccolo.  «Non ci sta»
    #    non e' «non c'e'», e il lettore lo deve distinguere.
    piccolo = fondo_sfumato(320, 200)
    r = marca.leggi_marca(piccolo)
    bene = (not r["c_e"]) and "GUARDARE" in (r.get("perche") or "")
    tutti = tutti and bene
    C.esito("P2 ⛔ troppo piccolo", bene,
            "«non ho potuto guardare» ≠ «la marca non c'e'» (LEZIONI §1.9)",
            {"perche": (r.get("perche") or "")[:150]})
    return tutti


def p3_massa(C, quanti, w=1280, h=720):
    print("\n\033[1m== P3 · ⭐ il negativo DI MASSA — %d scene di rumore, "
          "zero falsi positivi?\033[0m" % quanti)
    # ⛔ Si genera solo il rettangolo che il lettore guarda, piu' il margine
    #    della ricerca: generare 1280x720 volte 2000 costerebbe minuti e non
    #    aggiungerebbe niente — il lettore non guarda il resto.
    x0, y0, bw, bh = marca.GEOMETRIA.blocco()
    W, H = x0 + bw + 8, y0 + bh + 8
    rng = np.random.RandomState(20260813)
    falsi = []
    for i in range(quanti):
        # tre famiglie di rumore, perche' un rumore solo non e' un campione:
        #  · uniforme pieno       (massimo contrasto, il caso peggiore)
        #  · binario 0/255        (⛔ ha esattamente la statistica della marca)
        #  · a blocchi 24x24      (⛔ ha anche la GEOMETRIA della marca)
        k = i % 3
        if k == 0:
            img = rng.randint(0, 256, (H, W, 3), dtype=np.uint8)
        elif k == 1:
            img = (rng.randint(0, 2, (H, W, 1)) * 255).astype(np.uint8).repeat(3, axis=2)
        else:
            piccola = (rng.randint(0, 2, (H // 24 + 2, W // 24 + 2, 1)) * 255
                       ).astype(np.uint8)
            img = np.kron(piccola, np.ones((24, 24, 3), np.uint8))[:H, :W]
        r = marca.leggi_marca(img)
        if r["c_e"]:
            falsi.append({"i": i, "famiglia": k, "letto": r})
    bene = not falsi
    C.esito("P3 %d scene di rumore" % quanti, bene,
            "⭐ un rilevatore che dice sempre si' qui direbbe si' ~%d volte"
            % quanti,
            {"falsi_positivi": len(falsi),
             "famiglie": ["uniforme", "binario 0/255", "a blocchi 24x24 — "
                          "stessa geometria della marca"],
             "primo_falso": falsi[0] if falsi else None})
    return bene


def _ffmpeg(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def p4_codifica(C, lav, qp_da_provare, w=1280, h=720, vero=None):
    print("\n\033[1m== P4 · ⭐ LA CODIFICA CON PERDITA — la marca sopravvive? "
          "e fino a che QP?\033[0m")
    if not shutil.which("ffmpeg"):
        C.esito("P4 codifica", False, "⛔ NON MISURATO: ffmpeg non c'e'", None)
        return False
    sorgenti = {}
    img = fondo_sfumato(w, h, seme=3)
    marca.dipingi_marca(img, 1234567, 998877665544, marca.fnv1a32("g-codifica"))
    sorgenti["sintetica"] = (img, 1234567, 998877665544, marca.fnv1a32("g-codifica"))
    if vero is not None:
        r = marca.leggi_marca(vero)
        if r["c_e"]:
            sorgenti["⭐ fotogramma VERO della scena"] = (
                vero, r["disegno"], r["istante_us"], r["giro"])

    tutto_bene = True
    riassunto = {}
    for nome, (src, disegno, istante, giro) in sorgenti.items():
        hh, ww = src.shape[:2]
        grezzo = os.path.join(lav, "p4-sorgente.rgb24")
        src.tofile(grezzo)
        esiti_qp = {}
        for qp in qp_da_provare:
            flusso = os.path.join(lav, "p4-%d.hevc" % qp)
            fuori = os.path.join(lav, "p4-%d.rgb24" % qp)
            # ⛔ Main10 e tutto-intra, come F2.3: e' la catena che la fase 2 ha
            #    gia' misurato, e cambiarla qui vorrebbe dire certificare una
            #    codifica che il prodotto non usa.
            e = _ffmpeg(["ffmpeg", "-y", "-loglevel", "error",
                         "-f", "rawvideo", "-pix_fmt", "rgb24",
                         "-s", "%dx%d" % (ww, hh), "-i", grezzo,
                         "-pix_fmt", "yuv420p10le", "-c:v", "libx265",
                         "-x265-params",
                         "qp=%d:keyint=1:log-level=none" % qp,
                         "-f", "hevc", flusso])
            if e.returncode != 0:
                esiti_qp[qp] = {"c_e": None, "perche": "ffmpeg: " + e.stderr[-200:]}
                continue
            e = _ffmpeg(["ffmpeg", "-y", "-loglevel", "error", "-i", flusso,
                         "-pix_fmt", "rgb24", "-f", "rawvideo", fuori])
            if e.returncode != 0:
                esiti_qp[qp] = {"c_e": None, "perche": "decodifica: " + e.stderr[-200:]}
                continue
            dec = np.fromfile(fuori, np.uint8)
            if dec.size < ww * hh * 3:
                esiti_qp[qp] = {"c_e": None, "perche": "decodificato troppo corto"}
                continue
            dec = dec[:ww * hh * 3].reshape(hh, ww, 3)
            r = marca.leggi_marca(dec)
            esiti_qp[qp] = {
                "c_e": r["c_e"],
                "esatto": bool(r["c_e"] and r["disegno"] == disegno
                               and r["istante_us"] == istante and r["giro"] == giro),
                "contrasto": r.get("contrasto"),
                "byte_flusso": os.path.getsize(flusso),
                "perche": (r.get("perche") or "")[:100] if not r["c_e"] else None,
            }
        buoni = [qp for qp, v in esiti_qp.items() if v.get("esatto")]
        massimo = max(buoni) if buoni else None
        bene = massimo is not None and massimo >= 40
        tutto_bene = tutto_bene and bene
        riassunto[nome] = {"qp_provati": list(qp_da_provare),
                           "qp_esatti": buoni, "qp_massimo_esatto": massimo,
                           "dettaglio": esiti_qp}
        C.esito("P4 %s" % nome, bene,
                "rileggibile ed ESATTA fino a QP %s (la soglia dichiarata e' 40; "
                "F2.3 codifica a QP 40)" % massimo,
                {"qp_esatti": buoni,
                 "primo_qp_perso": min([qp for qp, v in esiti_qp.items()
                                        if not v.get("esatto")], default=None)})
    return tutto_bene, riassunto


def p5_rotta(C, w=1280, h=720):
    print("\n\033[1m== P5 · la marca ROTTA — il lettore rifiuta invece di sbagliare\033[0m")
    # ⛔ E' il controllo che distingue «so leggere» da «so anche NON leggere».
    #    Un bit invertito dev'essere preso dal CRC: se passasse, il lettore
    #    restituirebbe un numero di disegno FALSO e nessuno se ne accorgerebbe
    #    — ed e' esattamente il guasto «il fotogramma e' del giro prima»
    #    travestito da fotogramma fresco.
    x0, y0, _, _ = marca.GEOMETRIA.blocco()
    c = marca.GEOMETRIA.cella
    passati = 0
    letti_male = []
    prove = [(0, 3), (2, 7), (5, 11), (7, 17), (4, 0), (1, 1)]
    for r_, k_ in prove:
        img = fondo_sfumato(w, h)
        marca.dipingi_marca(img, 4242, 777777, marca.fnv1a32("g1"))
        cella = img[y0 + r_ * c:y0 + (r_ + 1) * c, x0 + k_ * c:x0 + (k_ + 1) * c]
        cella[:] = 255 - cella          # un bit invertito
        res = marca.leggi_marca(img)
        if not res["c_e"]:
            passati += 1
        else:
            letti_male.append({"cella": [r_, k_], "disegno": res["disegno"]})
    bene = passati == len(prove)
    C.esito("P5 un bit invertito", bene,
            "%d/%d marche rotte RIFIUTATE (il CRC le prende); zero lette a torto"
            % (passati, len(prove)),
            {"lette_a_torto": letti_male})
    return bene


def p6_due_pittori(C, fotogrammi):
    print("\n\033[1m== P6 · ⭐ I DUE PITTORI — la C dipinge, la Python rilegge\033[0m")
    if not fotogrammi:
        C.esito("P6 due pittori", False,
                "⛔ NON MISURATO: non c'e' nessun fotogramma della scena vera", None)
        return False
    bene_tutti = True
    for f in fotogrammi:
        dichiarato = json.load(open(f["json"]))
        img = np.fromfile(f["rgb24"], np.uint8)
        w, h = dichiarato["larghezza"], dichiarato["altezza"]
        img = img[:w * h * 3].reshape(h, w, 3)
        r = marca.leggi_marca(img)
        bene = (r["c_e"] and r["disegno"] == dichiarato["disegno"]
                and r["istante_us"] == dichiarato["istante_us"]
                and r["giro"] == dichiarato["giro_numero"])
        bene_tutti = bene_tutti and bene
        C.esito("P6 disegno %d" % dichiarato["disegno"], bene,
                "quel che 03-scena.c DICHIARA di aver dipinto = quel che "
                "03-marca.py rilegge dai pixel",
                {"dichiarato": [dichiarato["disegno"], dichiarato["istante_us"],
                                dichiarato["giro_numero"]],
                 "riletto": [r.get("disegno"), r.get("istante_us"), r.get("giro")]})
    return bene_tutti


def p7_si_muove(C, fotogrammi):
    print("\n\033[1m== P7 · ⛔ LA SCENA SI MUOVE SEMPRE — misurato, non promesso\033[0m")
    if len(fotogrammi) < 2:
        C.esito("P7 la scena si muove", False,
                "⛔ NON MISURATO: servono almeno due fotogrammi consecutivi", None)
        return False
    letti = []
    for f in fotogrammi:
        d = json.load(open(f["json"]))
        img = np.fromfile(f["rgb24"], np.uint8)[:d["larghezza"] * d["altezza"] * 3]
        img = img.reshape(d["altezza"], d["larghezza"], 3)
        r = marca.leggi_marca(img)
        letti.append((r.get("disegno"), r.get("istante_us"), img))
    letti.sort(key=lambda t: t[0])

    disegni_consecutivi = all(letti[i + 1][0] == letti[i][0] + 1
                              for i in range(len(letti) - 1))
    istanti_crescenti = all(letti[i + 1][1] > letti[i][1] for i in range(len(letti) - 1))
    # ⛔ E i PIXEL devono essere diversi: due fotogrammi con numeri diversi e
    #    pixel identici sarebbero una scena FERMA con un contatore sopra, cioe'
    #    esattamente il verde vuoto che §1.1 vieta.
    diversi = []
    for i in range(len(letti) - 1):
        a, b = letti[i][2].astype(np.int32), letti[i + 1][2].astype(np.int32)
        cambiati = int(np.count_nonzero(np.abs(a - b).max(axis=2) > 8))
        diversi.append(cambiati)
    tot = letti[0][2].shape[0] * letti[0][2].shape[1]
    frazione = [round(c / tot, 5) for c in diversi]
    bene = disegni_consecutivi and istanti_crescenti and all(c > 0 for c in diversi)
    C.esito("P7 la scena si muove", bene,
            "disegni consecutivi, istanti crescenti, e i PIXEL cambiano fra "
            "l'uno e l'altro",
            {"disegni": [l[0] for l in letti],
             "delta_istante_us": [letti[i + 1][1] - letti[i][1]
                                  for i in range(len(letti) - 1)],
             "pixel_cambiati": diversi, "frazione_dello_schermo": frazione})
    return bene


def p8_conteggio_negativo(C):
    print("\n\033[1m== P8 · il negativo del CONTEGGIO — «non c'e'» ≠ «zero disegni»\033[0m")
    r = marca.leggi_conteggio("remotix-scena-che-non-esiste-mai")
    bene = (not r.get("c_e")) and "non esiste" in (r.get("perche") or "")
    C.esito("P8 blocco assente", bene,
            "un blocco che non c'e' da' «non c'e'» con il perche', non zero",
            {"perche": (r.get("perche") or "")[:160]})
    return bene


# ───────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cartella", required=True)
    p.add_argument("--esiti")
    p.add_argument("--giro", default="c1")
    p.add_argument("--rumore", type=int, default=3000,
                   help="quante scene di rumore per il negativo di massa (P3)")
    p.add_argument("--qp", default="20,28,34,40,45,51")
    a = p.parse_args()

    fotogrammi = []
    for f in sorted(os.listdir(a.cartella)):
        if f.startswith("fotogramma-") and f.endswith(".rgb24"):
            j = os.path.join(a.cartella, f[:-6] + ".json")
            if os.path.exists(j):
                fotogrammi.append({"rgb24": os.path.join(a.cartella, f), "json": j})
    vero = None
    if fotogrammi:
        d = json.load(open(fotogrammi[0]["json"]))
        vero = np.fromfile(fotogrammi[0]["rgb24"], np.uint8)
        vero = vero[:d["larghezza"] * d["altezza"] * 3].reshape(
            d["altezza"], d["larghezza"], 3)
        print("⭐ %d fotogrammi VERI della scena, %dx%d"
              % (len(fotogrammi), d["larghezza"], d["altezza"]))
    else:
        print("⚠ nessun fotogramma vero della scena in «%s»: P6 e P7 non si "
              "misurano, e non si fingono misurati" % a.cartella)

    C = Conto()
    p1_positivo(C)
    p2_negativo(C, vero=vero)
    p3_massa(C, a.rumore)
    _, p4 = p4_codifica(C, a.cartella, [int(x) for x in a.qp.split(",")], vero=vero)
    p5_rotta(C)
    p6_due_pittori(C, fotogrammi)
    p7_si_muove(C, fotogrammi)
    p8_conteggio_negativo(C)

    print("\n\033[1m== Il conto\033[0m")
    print("    %d controlli, %d passati, %d falliti"
          % (C.totali, C.passati, C.totali - C.passati))
    for c in C.controlli:
        if not c["passato"]:
            print("    %sNO%s  %s — %s" % (ROSSO, GRIGIO, c["nome"], c["dimostra"]))

    R = {"ora": datetime.datetime.now().isoformat(timespec="seconds"),
         "strumento": "03-marca-certifica.py", "giro": a.giro,
         "fotogrammi_veri": len(fotogrammi),
         "geometria": {"cella": marca.CELLA, "colonne": marca.COLONNE,
                       "righe": marca.RIGHE, "margine": marca.MARGINE,
                       "quiete": marca.QUIETE, "bit": marca.BIT},
         "controlli": C.controlli, "totali": C.totali, "passati": C.passati,
         "codifica": p4}
    if a.esiti:
        with open(a.esiti, "a") as f:
            f.write(json.dumps(R, ensure_ascii=False) + "\n")
        print("    esiti → %s" % a.esiti)
    return 0 if C.passati == C.totali else 1


if __name__ == "__main__":
    sys.exit(main())
