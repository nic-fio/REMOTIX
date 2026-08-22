#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.1-ter — la STRUTTURA che esce da EncSliceLP, figura per figura.

Domande, e ognuna ha una colonna:
  - compaiono figure NON DI RIFERIMENTO (TRAIL_N)?  con quale `-bf`?
  - portano un `temporal_id` > 0 (sotto-livelli veri) o restano tutte a 0?
  - lo `sps_max_sub_layers_minus1` del flusso dichiara piu' di un sotto-livello?
  - quanto costa in RITARDO: quante figure il codificatore trattiene?
  - quanto costa in BANDA e in QUALITA' (PSNR/SSIM contro la sorgente)?
"""
import os
import re
import subprocess

DIR = "/srv/src/08-D"
SCENA = os.path.join(DIR, "scena-utente.webm")
FUORI = os.path.join(DIR, "fuori2")
os.makedirs(FUORI, exist_ok=True)
INTEL = "/dev/dri/renderD128"
N = 120

TIPO = {0: "TRAIL_N", 1: "TRAIL_R", 2: "TSA_N", 3: "TSA_R", 4: "STSA_N",
        5: "STSA_R", 19: "IDR_W_RADL", 20: "IDR_N_LP", 21: "CRA"}


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


def sps_sub_layers(d, nals):
    """Legge `sps_max_sub_layers_minus1` dal primo SPS (HEVC, 33)."""
    for n in nals:
        if n["tipo"] == 33:
            b = d[n["corpo"] + 2]          # primo byte del payload SPS
            vps_id = b >> 4
            max_sub = (b >> 1) & 0x07
            return vps_id, max_sub + 1
    return None, None


def vps_sub_layers(d, nals):
    for n in nals:
        if n["tipo"] == 32:
            b = d[n["corpo"] + 3]          # terzo byte: max_sub_layers_minus1 nei bit 3..1
            return ((b >> 1) & 0x07) + 1
    return None


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


def pacchetti(percorso):
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                        "-show_entries", "packet=pts,dts,size,flags",
                        "-of", "csv=p=0", percorso], capture_output=True, text=True)
    r = []
    for riga in p.stdout.strip().splitlines():
        c = riga.split(",")
        r.append(c)
    return r


def cella(bf, depth, low_power=1):
    nome = "bf%d-d%d-lp%d" % (bf, depth, low_power)
    uscita = os.path.join(FUORI, nome + ".h265")
    cmd = ["ffmpeg", "-hide_banner", "-v", "verbose", "-y",
           "-init_hw_device", "vaapi=va:" + INTEL, "-filter_hw_device", "va",
           "-i", SCENA, "-frames:v", str(N),
           "-vf", "format=nv12,hwupload", "-c:v", "hevc_vaapi",
           "-rc_mode", "CQP", "-qp", "26", "-async_depth", "1",
           "-idr_interval", "0", "-g", "600", "-profile:v", "1",
           "-low_power", str(low_power), "-bf", str(bf), "-b_depth", str(depth),
           "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-color_range", "tv",
           "-f", "hevc", uscita]
    p = subprocess.run(cmd, capture_output=True, text=True)
    log = p.stderr or ""
    ep = "?"
    m = re.search(r"Using VAAPI entrypoint (\S+)", log)
    if m:
        ep = m.group(1)
    if p.returncode != 0:
        print("%-14s FALLITO rc=%d  %s" % (nome, p.returncode,
              [x for x in log.splitlines() if "rror" in x][:1]))
        return
    d, nals = scomponi(uscita)
    vcl = [n for n in nals if n["tipo"] <= 31]
    conto = {}
    for n in vcl:
        k = "%s/tid%d" % (TIPO.get(n["tipo"], n["tipo"]), n["tid"])
        conto[k] = conto.get(k, 0) + 1
    _, sps_sub = sps_sub_layers(d, nals)
    vps_sub = vps_sub_layers(d, nals)
    pk = pacchetti(uscita)
    sfasati = sum(1 for c in pk if c[0] != c[1])
    byte = os.path.getsize(uscita)
    print("%-14s ep=%-22s VCL=%3d  byte=%9d  sps_max_sub_layers=%s vps=%s "
          "pacchetti pts!=dts=%d/%d\n               %s"
          % (nome, ep, len(vcl), byte, sps_sub, vps_sub, sfasati, len(pk), conto))
    return uscita, vcl, d, byte


print("== D.1-ter — struttura di quel che esce da EncSliceLP, %d fotogrammi ==" % N)
esiti = {}
for bf, depth in [(0, 1), (1, 1), (2, 1), (2, 2), (4, 1), (4, 3), (8, 4)]:
    r = cella(bf, depth)
    if r:
        esiti["bf%d-d%d" % (bf, depth)] = r

# ⭐ la prova di scarto sulle celle che hanno prodotto TRAIL_N
print("\n== ⭐ PROVA DI SCARTO — si buttano le figure «_N» e si decodifica ==")
for nome, (uscita, vcl, d, byte) in esiti.items():
    enne = [n for n in vcl if n["tipo"] % 2 == 0 and n["tipo"] <= 14]
    if not enne:
        print("%-10s nessuna figura «_N»: niente da buttare" % nome)
        continue
    tenuti = [d[n["inizio"]:n["fine"]] for n in
              [x for x in scomponi(uscita)[1]] if not (x["tipo"] % 2 == 0 and x["tipo"] <= 14)]
    tag = uscita + ".tagliato.h265"
    open(tag, "wb").write(b"".join(tenuti))
    p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", tag,
                        "-f", "null", "-"], capture_output=True, text=True)
    err = (p.stderr or "").strip()
    print("%-10s buttate %d/%d figure; risparmio %d byte su %d (%.1f%%); "
          "decodifica: %s"
          % (nome, len(enne), len(vcl), byte - os.path.getsize(tag), byte,
             100.0 * (byte - os.path.getsize(tag)) / byte,
             "SENZA errori" if not err else "CON errori: " + err.splitlines()[0]))
