#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.2-quater — la SCALA fra il desktop vero e il rumore, e il tempo del solo
codificatore.

⛔ Nei giri precedenti i «ms per chiave» comprendevano la decodifica del webm,
   la scala, il mosaico e il generatore di rumore — cioe' tutto tranne la
   domanda.  Qui le immagini si preparano PRIMA in un file grezzo NV12, e il
   cronometro parte sul solo `ffmpeg` che codifica da grezzo.

E fra «il desktop vero» e «il rumore uniforme» si mettono due gradini che un
desktop puo' davvero avere: un filmato con la grana.
"""
import os
import subprocess
import time

DIR = "/srv/src/08-D"
SCENA = os.path.join(DIR, "scena-utente.webm")
FUORI = os.path.join(DIR, "fuori-d2d")
os.makedirs(FUORI, exist_ok=True)
INTEL = "/dev/dri/renderD128"
TETTO = 16 * 1024 * 1024
QUANTI = 8


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


def accessi(percorso):
    d = open(percorso, "rb").read()
    tagli = [inizio for inizio, corpo in nal_offsets(d)
             if ((d[corpo] >> 1) & 0x3F) == 32]
    if not tagli:
        return []
    tagli.append(len(d))
    return [tagli[i + 1] - tagli[i] for i in range(len(tagli) - 1)]


def prepara(nome, misura, filtro, ingresso):
    """Scrive QUANTI immagini NV12 grezze: il codificatore poi non aspetta nessuno."""
    grezzo = os.path.join(FUORI, nome + ".nv12")
    if os.path.exists(grezzo):
        return grezzo
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y"] + ingresso + \
          ["-frames:v", str(QUANTI), "-vf", filtro + ",format=nv12",
           "-f", "rawvideo", grezzo]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        print("  prepara %s FALLITO: %s" % (nome, (p.stderr or "")[:200]))
        return None
    return grezzo


def codifica(etichetta, grezzo, misura, qp, profilo=1):
    uscita = os.path.join(FUORI, etichetta.replace(" ", "_") + ".h265")
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y",
           "-init_hw_device", "vaapi=va:" + INTEL, "-filter_hw_device", "va",
           "-f", "rawvideo", "-pix_fmt", "nv12", "-s", misura, "-r", "30",
           "-i", grezzo, "-vf", "format=nv12,hwupload", "-c:v", "hevc_vaapi",
           "-g", "1", "-bf", "0", "-rc_mode", "CQP", "-qp", str(qp),
           "-async_depth", "1", "-idr_interval", "0", "-low_power", "1",
           "-profile:v", str(profilo),
           "-f", "hevc", uscita]
    t0 = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.monotonic() - t0
    if p.returncode:
        print("  %-38s ⛔ FALLITO: %s" % (etichetta, (p.stderr or "").splitlines()[0][:120]))
        return
    v = sorted(accessi(uscita))
    n = len(v)
    sopra = sum(1 for x in v if x > TETTO)
    print("  %-38s n=%d distinte=%d  med %10d  max %10d byte (%7.3f MiB, "
          "%5.1f%% del tetto)  sopra %d/%d  %5.0f ms/chiave"
          % (etichetta, n, len(set(v)), v[n // 2], v[-1], v[-1] / 1048576.0,
             100.0 * v[-1] / TETTO, sopra, n, 1000.0 * dt / max(n, 1)))


SCALA_8K = [
    ("desktop", "scale=2560:1080,tile=3x4", ["-i", SCENA]),
    ("grana10", "scale=2560:1080,tile=3x4,noise=alls=10:allf=t+u", ["-i", SCENA]),
    ("grana30", "scale=2560:1080,tile=3x4,noise=alls=30:allf=t+u", ["-i", SCENA]),
    ("grana60", "scale=2560:1080,tile=3x4,noise=alls=60:allf=t+u", ["-i", SCENA]),
    ("rumore", "null", ["-f", "lavfi", "-i",
                        "nullsrc=s=7680x4320:r=30,geq=random(1)*255:random(2)*255:random(3)*255"]),
]

print("== 7680x4320 — dal desktop vero al rumore, a QP 26 (quello del prodotto) ==")
for nome, filtro, ing in SCALA_8K:
    g = prepara("8k-" + nome, "7680x4320", filtro, ing)
    if g:
        codifica("8K %-8s qp26" % nome, g, "7680x4320", 26)

print("\n== 2560x1080 — la tela dell'utente, stessa scala ==")
SCALA_2K = [
    ("desktop", "null", ["-i", SCENA]),
    ("grana30", "noise=alls=30:allf=t+u", ["-i", SCENA]),
    ("rumore", "null", ["-f", "lavfi", "-i",
                        "nullsrc=s=2560x1080:r=30,geq=random(1)*255:random(2)*255:random(3)*255"]),
]
for nome, filtro, ing in SCALA_2K:
    g = prepara("2k-" + nome, "2560x1080", filtro, ing)
    if g:
        codifica("2560x1080 %-8s qp26" % nome, g, "2560x1080", 26)

print("\n== la scala delle ricodifiche del prodotto sul caso che sfonda ==")
g = prepara("8k-rumore", "7680x4320", "null",
            ["-f", "lavfi", "-i",
             "nullsrc=s=7680x4320:r=30,geq=random(1)*255:random(2)*255:random(3)*255"])
for qp in (26, 32, 38, 44):
    codifica("8K rumore qp%d" % qp, g, "7680x4320", qp)
