#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.2-ter — ⛔ IL DENOMINATORE ERA FINTO, E LO DICO IO.

Nel giro precedente le 33 chiavi a 7680x4320 uscivano tutte di **243 497 byte
esatti**: impossibile su 33 immagini diverse.  La causa: `-fps_mode cfr -r 30`
sta DOPO il filtro `tile=3x4`, che consegna 2,5 immagini al secondo — la
conversione a 30/s le **duplica dodici volte**.  ⇒ Le immagini distinte erano
tre, non trentatre.

Qui il mosaico si costruisce senza conversione di cadenza, e il numero di
chiavi distinte si CONTA guardando quante misure diverse escono.

E si misura anche il TEMPO di codifica per chiave, perche' la scala delle
ricodifiche (QP 26 → 32 → 38) lo paga tre volte.
"""
import os
import subprocess
import time

DIR = "/srv/src/08-D"
SCENA = os.path.join(DIR, "scena-utente.webm")
FUORI = os.path.join(DIR, "fuori-d2c")
os.makedirs(FUORI, exist_ok=True)
INTEL = "/dev/dri/renderD128"
TETTO = 16 * 1024 * 1024


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


def accessi(percorso, hevc=True):
    d = open(percorso, "rb").read()
    tagli = []
    for inizio, corpo in nal_offsets(d):
        tipo = ((d[corpo] >> 1) & 0x3F) if hevc else (d[corpo] & 0x1F)
        if (hevc and tipo == 32) or ((not hevc) and tipo == 7):
            tagli.append(inizio)
    if not tagli:
        return []
    tagli.append(len(d))
    return [tagli[i + 1] - tagli[i] for i in range(len(tagli) - 1)]


def gira(etichetta, ingresso, vf, comp, extra, quanti, hevc=True):
    uscita = os.path.join(FUORI, etichetta.replace(" ", "_").replace("/", "-")
                          + ("." + ("h265" if hevc else "h264")))
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y",
           "-init_hw_device", "vaapi=va:" + INTEL, "-filter_hw_device", "va"] \
        + ingresso + ["-frames:v", str(quanti), "-vf", vf, "-c:v", comp,
                      "-g", "1", "-bf", "0", "-rc_mode", "CQP",
                      "-async_depth", "1", "-idr_interval", "0", "-low_power", "1",
                      "-colorspace", "bt709", "-color_primaries", "bt709",
                      "-color_trc", "bt709", "-color_range", "tv"] + extra \
        + ["-f", "hevc" if hevc else "h264", uscita]
    t0 = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.monotonic() - t0
    if p.returncode != 0:
        righe = [x for x in (p.stderr or "").splitlines() if x.strip()]
        print("  %-44s ⛔ FALLITO rc=%d" % (etichetta, p.returncode))
        for r in righe[:3]:
            print("       | " + r[:150])
        return
    v = accessi(uscita, hevc)
    distinte = len(set(v))
    v2 = sorted(v)
    n = len(v2)
    sopra = sum(1 for x in v2 if x > TETTO)
    print("  %-44s n=%3d (misure distinte %2d)  min %9d  med %9d  max %9d byte "
          "(%6.3f MiB)  sopra il tetto %d/%d  %5.0f ms/chiave (tutto il tubo)"
          % (etichetta, n, distinte, v2[0], v2[n // 2], v2[-1],
             v2[-1] / 1048576.0, sopra, n, 1000.0 * dt / max(n, 1)))


print("== 1. il mosaico 8K, con la cadenza NON convertita ==")
gira("7680x4320 mosaico desktop qp26", ["-i", SCENA],
     "scale=2560:1080,tile=3x4,format=nv12,hwupload", "hevc_vaapi",
     ["-qp", "26", "-profile:v", "1"], 33)
gira("7680x4320 mosaico desktop qp26 m10", ["-i", SCENA],
     "scale=2560:1080,tile=3x4,format=p010le,hwupload", "hevc_vaapi",
     ["-qp", "26", "-profile:v", "2"], 33)

print("\n== 2. controllo: la stessa scena 2560x1080 senza conversione ==")
gira("2560x1080 desktop utente qp26", ["-i", SCENA],
     "format=nv12,hwupload", "hevc_vaapi", ["-qp", "26", "-profile:v", "1"], 404)

print("\n== 3. h264_vaapi: dove si ferma davvero ==")
for l, a in ((3840, 2160), (4096, 2160), (4098, 2160), (7680, 4320)):
    gira("%dx%d h264 LP qp26" % (l, a), ["-i", SCENA],
         "scale=%d:%d,format=nv12,hwupload" % (l, a), "h264_vaapi",
         ["-qp", "26"], 10, hevc=False)

print("\n== 4. hevc_vaapi: dove si ferma davvero ==")
for l, a in ((7680, 4320), (8192, 4320), (16384, 4320)):
    gira("%dx%d hevc LP qp26" % (l, a), ["-i", SCENA],
         "scale=%d:%d,format=nv12,hwupload" % (l, a), "hevc_vaapi",
         ["-qp", "26", "-profile:v", "1"], 6)

print("\n== 5. il tempo di UNA chiave 8K, che la scala delle ricodifiche paga 3 volte ==")
for qp in (26, 32, 38):
    gira("7680x4320 RUMORE qp%d" % qp,
         ["-f", "lavfi", "-i",
          "nullsrc=s=7680x4320:r=30,geq=random(1)*255:random(2)*255:random(3)*255"],
         "format=nv12,hwupload", "hevc_vaapi", ["-qp", str(qp), "-profile:v", "1"], 6)
