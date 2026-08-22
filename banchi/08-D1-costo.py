#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.1-quinquies — quel che le figure BUTTABILI costano davvero.

Sorgente unica e grezza (NV12, 120 immagini della scena dell'utente a cadenza
fissa): cosi' banda e qualita' si confrontano sullo stesso identico ingresso.

Si misura, per ogni `-bf`:
  - i byte del flusso  (banda);
  - PSNR e SSIM contro la sorgente grezza (qualita');
  - il RIORDINO, in fotogrammi: e' il ritardo che si compra;
  - quante figure sono buttabili e se, buttandole, il resto decodifica.
"""
import os
import re
import subprocess

DIR = "/srv/src/08-D"
SCENA = os.path.join(DIR, "scena-utente.webm")
FUORI = os.path.join(DIR, "fuori-d1e")
os.makedirs(FUORI, exist_ok=True)
INTEL = "/dev/dri/renderD128"
N = 120
MISURA = "2560x1080"
GREZZO = os.path.join(FUORI, "sorgente.nv12")

if not os.path.exists(GREZZO):
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", SCENA,
                    "-frames:v", str(N), "-fps_mode", "cfr", "-r", "30",
                    "-vf", "format=nv12", "-f", "rawvideo", GREZZO], check=True)


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


def sps_max_sub(d, nals):
    for n in nals:
        if n["tipo"] == 33:
            return ((d[n["corpo"] + 2] >> 1) & 0x07) + 1
    return None


def ingresso():
    return ["-f", "rawvideo", "-pix_fmt", "nv12", "-s", MISURA, "-r", "30",
            "-i", GREZZO]


def codifica(bf, depth):
    base = os.path.join(FUORI, "bf%d-d%d" % (bf, depth))
    com = ["-init_hw_device", "vaapi=va:" + INTEL, "-filter_hw_device", "va"] \
        + ingresso() + ["-vf", "format=nv12,hwupload", "-c:v", "hevc_vaapi",
                        "-rc_mode", "CQP", "-qp", "26", "-async_depth", "1",
                        "-idr_interval", "0", "-g", "600", "-profile:v", "1",
                        "-low_power", "1", "-bf", str(bf), "-b_depth", str(depth)]
    for est, arg in ((".h265", ["-f", "hevc"]), (".mkv", [])):
        p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y"] + com
                           + arg + [base + est], capture_output=True, text=True)
        if p.returncode:
            print("FALLITO bf=%d: %s" % (bf, (p.stderr or "")[:150]))
            return None
    return base


def riordino_fotogrammi(mkv):
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                        "-show_entries", "packet=pts_time,dts_time",
                        "-of", "csv=p=0", mkv], capture_output=True, text=True)
    mx = 0.0
    for riga in p.stdout.strip().splitlines():
        c = riga.split(",")
        try:
            mx = max(mx, abs(float(c[0]) - float(c[1])))
        except Exception:
            pass
    return mx


def qualita(h265):
    fuori = {}
    for metrica in ("psnr", "ssim"):
        cmd = ["ffmpeg", "-hide_banner", "-v", "info", "-y",
               "-i", h265] + ingresso() + \
              ["-lavfi", "[0:v][1:v]" + metrica, "-f", "null", "-"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        s = p.stderr or ""
        m = re.search(r"average:([0-9.]+)", s) or re.search(r"All:([0-9.]+)", s)
        fuori[metrica] = m.group(1) if m else "?"
    return fuori


print("== D.1-quinquies — il costo delle figure buttabili, n=%d fotogrammi ==\n" % N)
print("%-9s %8s %6s %11s %9s %10s %9s %s" %
      ("cella", "byte", "sub", "buttabili", "ritardo", "PSNR", "SSIM", "scarto"))
for bf, depth in [(0, 1), (1, 1), (2, 1), (2, 2), (4, 1), (4, 3)]:
    base = codifica(bf, depth)
    if not base:
        continue
    d, nals = scomponi(base + ".h265")
    vcl = [n for n in nals if n["tipo"] <= 31]
    enne = [n for n in vcl if n["tipo"] % 2 == 0 and n["tipo"] <= 14]
    byte = os.path.getsize(base + ".h265")
    rit = riordino_fotogrammi(base + ".mkv")
    q = qualita(base + ".h265")
    esito = "-"
    if enne:
        tenuti = [d[n["inizio"]:n["fine"]] for n in nals
                  if not (n["tipo"] % 2 == 0 and n["tipo"] <= 14)]
        tag = base + ".tagliato.h265"
        open(tag, "wb").write(b"".join(tenuti))
        p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", tag,
                            "-f", "null", "-"], capture_output=True, text=True)
        err = (p.stderr or "").strip()
        esito = "%s, -%.0f%% byte" % ("PULITA" if not err else "ROTTA",
                                      100.0 * (byte - os.path.getsize(tag)) / byte)
    print("%-9s %8d %6s %11s %9s %10s %9s %s" %
          ("bf%d/d%d" % (bf, depth), byte, sps_max_sub(d, nals),
           "%d/%d" % (len(enne), len(vcl)),
           "%.0f ms (%.1f fot.)" % (rit * 1000, rit * 30),
           q["psnr"], q["ssim"], esito))
