#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.1-sexies — ⭐ PROVA A SMENTIRTI.

Due verdi del giro precedente, e tutt'e due hanno un guasto innestato che li
deve far diventare rossi.  Se non diventano rossi, la misura non vale.

⛔ GUASTO 1 — «il resto decodifica SENZA errori» non prova NIENTE.
   `RCP.md` §5.2 lo dice testualmente: *a un delta mancante il decodificatore
   non solleva nessun errore, si limita a produrre immagini via via piu'
   sfasciate*.  ⇒ Un banco che guarda i messaggi d'errore misura il silenzio
   del decodificatore, non la salute dell'immagine.
   La prova vera: si confrontano i PIXEL.  Ogni immagine che esce dal flusso
   tagliato deve essere IDENTICA, byte per byte, a una che esce dal flusso
   intero.  E il controllo negativo e' buttare una figura DI RIFERIMENTO
   (TRAIL_R) invece di una buttabile: li' le identita' devono CROLLARE.

⛔ GUASTO 2 — «nessun `temporal_id` > 0 e `sps_max_sub_layers` = 1» potrebbe
   essere un lettore rotto invece di un codificatore muto.
   Controllo positivo: `libx265 --temporal-layers`, che i sotto-livelli li
   produce davvero.  Se il lettore li vede LI', il «no» su `EncSliceLP` e' del
   codificatore.
"""
import hashlib
import os
import subprocess

DIR = "/srv/src/08-D"
FUORI = os.path.join(DIR, "fuori-d1f")
os.makedirs(FUORI, exist_ok=True)
SORGENTE = os.path.join(DIR, "fuori-d1e", "sorgente.nv12")
INTEL = "/dev/dri/renderD128"
MISURA = "2560x1080"
N = 120
BYTE_IMMAGINE = 2560 * 1080 * 3 // 2


def nal_offsets(d):
    out, i, n = [], 0, len(d)
    while i + 3 < n:
        if d[i] == 0 and d[i + 1] == 0:
            if d[i + 2] == 1:
                out.append((i, i + 3)); i += 3; continue
            if d[i + 2] == 0 and d[i + 3] == 1:
                out.append((i, i + 4)); i += 4; continue
        i += 1
    return out


def scomponi(percorso):
    d = open(percorso, "rb").read()
    off = nal_offsets(d)
    nals = []
    for k, (inizio, corpo) in enumerate(off):
        fine = off[k + 1][0] if k + 1 < len(off) else len(d)
        b0, b1 = d[corpo], d[corpo + 1]
        nals.append({"inizio": inizio, "fine": fine, "corpo": corpo,
                     "tipo": (b0 >> 1) & 0x3F, "tid": (b1 & 0x07) - 1})
    return d, nals


def decodifica(h265, grezzo):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", h265,
                        "-pix_fmt", "nv12", "-f", "rawvideo", grezzo],
                       capture_output=True, text=True)
    return (p.stderr or "").strip()


def impronte(grezzo):
    fuori = []
    with open(grezzo, "rb") as f:
        while True:
            b = f.read(BYTE_IMMAGINE)
            if len(b) < BYTE_IMMAGINE:
                break
            fuori.append(hashlib.sha256(b).hexdigest())
    return fuori


def taglia(nome, h265, quali):
    d, nals = scomponi(h265)
    da_togliere = [n for n in nals if quali(n)]
    tenuti = [d[n["inizio"]:n["fine"]] for n in nals if not quali(n)]
    fuori = os.path.join(FUORI, nome + ".h265")
    open(fuori, "wb").write(b"".join(tenuti))
    return fuori, len(da_togliere)


BUTTABILE = lambda n: n["tipo"] % 2 == 0 and n["tipo"] <= 14        # TRAIL_N & c.
DI_RIFERIMENTO = lambda n: n["tipo"] == 1                            # TRAIL_R


def una_su_n(f, ogni):
    stato = {"k": 0}

    def g(n):
        if not f(n):
            return False
        stato["k"] += 1
        return stato["k"] % ogni == 0
    return g


print("=" * 78)
print("GUASTO 1 — i pixel, non i messaggi d'errore")
print("=" * 78)

base = os.path.join(FUORI, "bf1")
if not os.path.exists(base + ".h265"):
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y",
                    "-init_hw_device", "vaapi=va:" + INTEL, "-filter_hw_device", "va",
                    "-f", "rawvideo", "-pix_fmt", "nv12", "-s", MISURA, "-r", "30",
                    "-i", SORGENTE, "-vf", "format=nv12,hwupload", "-c:v", "hevc_vaapi",
                    "-rc_mode", "CQP", "-qp", "26", "-async_depth", "1",
                    "-idr_interval", "0", "-g", "600", "-profile:v", "1",
                    "-low_power", "1", "-bf", "1", "-b_depth", "1",
                    "-f", "hevc", base + ".h265"], check=True)

intero = os.path.join(FUORI, "intero.nv12")
err_intero = decodifica(base + ".h265", intero)
imp_intero = set(impronte(intero))
print("flusso intero: %d immagini decodificate, errori: %s"
      % (len(imp_intero), err_intero or "nessuno"))

CASI = [
    ("A-buttate-le-TRAIL_N",   BUTTABILE,                     "il verde da smentire"),
    ("B-buttata-1-TRAIL_R-su-10", una_su_n(DI_RIFERIMENTO, 10), "⭐ GUASTO INNESTATO"),
    ("C-buttate-le-TRAIL_R",   DI_RIFERIMENTO,                "⭐ GUASTO PESANTE"),
]

for nome, quale, che_cosa in CASI:
    tag, quante = taglia(nome, base + ".h265", quale)
    grezzo = os.path.join(FUORI, nome + ".nv12")
    err = decodifica(tag, grezzo)
    imp = impronte(grezzo)
    identiche = sum(1 for h in imp if h in imp_intero)
    print("\n%-28s (%s)" % (nome, che_cosa))
    print("   figure tolte: %d ; immagini decodificate: %d" % (quante, len(imp)))
    print("   messaggi d'errore del decodificatore: %s" % (err.splitlines()[0][:90] if err else "NESSUNO"))
    print("   ⇒ immagini IDENTICHE a una del flusso intero: %d/%d (%.1f%%)"
          % (identiche, len(imp), 100.0 * identiche / max(len(imp), 1)))
    os.remove(grezzo)

os.remove(intero)

print("\n" + "=" * 78)
print("GUASTO 2 — il lettore di `temporal_id` sa vederli, quando ci sono?")
print("=" * 78)

x265 = os.path.join(FUORI, "x265-temporal-layers.h265")
p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y",
                    "-f", "rawvideo", "-pix_fmt", "nv12", "-s", MISURA, "-r", "30",
                    "-i", SORGENTE, "-frames:v", "48", "-c:v", "libx265",
                    "-x265-params",
                    "crf=26:bframes=4:b-pyramid=1:temporal-layers=1:keyint=600:"
                    "min-keyint=600:repeat-headers=1:log-level=error",
                    "-f", "hevc", x265], capture_output=True, text=True)
if p.returncode:
    print("⛔ libx265 con --temporal-layers non e' partito: %s"
          % (p.stderr or "").splitlines()[-1][:160])
else:
    d, nals = scomponi(x265)
    conto = {}
    for n in nals:
        if n["tipo"] <= 31:
            conto[n["tid"]] = conto.get(n["tid"], 0) + 1
    sub = None
    for n in nals:
        if n["tipo"] == 33:
            sub = ((d[n["corpo"] + 2] >> 1) & 0x07) + 1
            break
    print("libx265 `temporal-layers=1`: NAL VCL per temporal_id = %s ; "
          "sps_max_sub_layers = %s" % (conto, sub))
    if max(conto) > 0:
        print("⇒ ⭐ IL LETTORE VEDE i sotto-livelli quando ci sono: "
              "lo ZERO su EncSliceLP e' del codificatore, non del banco.")
    else:
        print("⇒ ⛔ nemmeno qui: il controllo positivo NON tiene, "
              "la misura su EncSliceLP resta senza testimone.")
