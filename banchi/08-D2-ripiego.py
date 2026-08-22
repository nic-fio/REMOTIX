#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.2-quinquies — il RIPIEGO in software contro lo stesso tetto.

Serve perche' oltre i 4096 px `h264_vaapi` non c'e' (misurato in D.2-ter): a
quelle misure il prodotto scende su `libx264`/`libx265`, e li' la scala delle
qualita' parte da CRF 20 (`figlio.c:4065`), non da QP 26.
"""
import os
import subprocess
import time

DIR = "/srv/src/08-D"
D2D = os.path.join(DIR, "fuori-d2d")
FUORI = os.path.join(DIR, "fuori-d2e")
os.makedirs(FUORI, exist_ok=True)
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


def accessi(percorso, hevc):
    d = open(percorso, "rb").read()
    tagli = [i for i, c in nal_offsets(d)
             if (((d[c] >> 1) & 0x3F) == 32 if hevc else (d[c] & 0x1F) == 7)]
    if not tagli:
        return []
    tagli.append(len(d))
    return [tagli[i + 1] - tagli[i] for i in range(len(tagli) - 1)]


def gira(etichetta, grezzo, misura, comp, crf):
    hevc = comp == "libx265"
    u = os.path.join(FUORI, etichetta.replace(" ", "_") + (".h265" if hevc else ".h264"))
    par = ("crf=%d:bframes=0:open-gop=0:repeat-headers=1:rc-lookahead=0:"
           "frame-threads=1:keyint=1:min-keyint=1:info=1:log-level=error" % crf) if hevc \
        else ("crf=%d:bframes=0:open-gop=0:repeat-headers=1:rc-lookahead=0:"
              "threads=1:sliced-threads=0:keyint=1:min-keyint=1:log-level=error" % crf)
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "nv12", "-s", misura, "-r", "30",
           "-i", grezzo, "-vf", "format=yuv420p", "-c:v", comp,
           "-" + ("x265" if hevc else "x264") + "-params", par,
           "-g", "1", "-bf", "0", "-f", "hevc" if hevc else "h264", u]
    t0 = time.monotonic()
    p = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.monotonic() - t0
    if p.returncode:
        print("  %-40s ⛔ FALLITO: %s" % (etichetta, (p.stderr or "").splitlines()[0][:110]))
        return
    v = sorted(accessi(u, hevc))
    if not v:
        print("  %-40s ⛔ nessun accesso" % etichetta)
        return
    n = len(v)
    sopra = sum(1 for x in v if x > TETTO)
    print("  %-40s n=%d  med %10d  max %10d byte (%7.3f MiB, %5.1f%% del tetto)  "
          "sopra %d/%d  %6.0f ms/chiave"
          % (etichetta, n, v[n // 2], v[-1], v[-1] / 1048576.0,
             100.0 * v[-1] / TETTO, sopra, n, 1000.0 * dt / n))


print("== il ripiego in software, 2560x1080 ==")
for scena in ("desktop", "grana30", "rumore"):
    g = os.path.join(D2D, "2k-" + scena + ".nv12")
    if os.path.exists(g):
        gira("2560x1080 %-8s libx265 crf20" % scena, g, "2560x1080", "libx265", 20)
        gira("2560x1080 %-8s libx264 crf20" % scena, g, "2560x1080", "libx264", 20)

print("\n== il ripiego in software, 7680x4320 (li' l'hardware H.264 NON c'e') ==")
for scena in ("desktop", "grana30", "grana60", "rumore"):
    g = os.path.join(D2D, "8k-" + scena + ".nv12")
    if os.path.exists(g):
        gira("7680x4320 %-8s libx264 crf20" % scena, g, "7680x4320", "libx264", 20)

print("\n== e la scala del ripiego sul caso che sfonda ==")
g = os.path.join(D2D, "8k-rumore.nv12")
for crf in (20, 26, 32, 38, 44, 51):
    gira("7680x4320 rumore libx264 crf%d" % crf, g, "7680x4320", "libx264", crf)
