#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D.1-septies — il TESTIMONE che mancava.

Il controllo positivo del giro precedente e' fallito: `libx265` con
`temporal-layers=1` ha prodotto `temporal_id` tutti a zero.  ⛔ Finche' non
esiste un flusso con i sotto-livelli DENTRO, lo zero misurato su `EncSliceLP`
puo' essere un lettore rotto.

Qui si prova, in ordine:
  1. `libx265` chiesto in modi diversi, con la sua CONFESSIONE a video
     (`log-level=info`): ha accettato l'opzione o l'ha ignorata?
  2. ⭐ il testimone che non puo' fallire: si prende un nostro flusso e si
     ALZANO A MANO i due bit di `nuh_temporal_id_plus1` su alcune figure.  Se
     il lettore le vede, il lettore funziona; se non le vede, il lettore e'
     rotto e tutte le misure di D.1 vanno buttate.
"""
import os
import re
import subprocess

DIR = "/srv/src/08-D"
FUORI = os.path.join(DIR, "fuori-d1g")
os.makedirs(FUORI, exist_ok=True)
SORGENTE = os.path.join(DIR, "fuori-d1e", "sorgente.nv12")
BASE = os.path.join(DIR, "fuori-d1f", "bf1.h265")
MISURA = "2560x1080"


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


def leggi(percorso):
    d = open(percorso, "rb").read()
    off = nal_offsets(d)
    conto, sub = {}, None
    for inizio, corpo in off:
        b0, b1 = d[corpo], d[corpo + 1]
        tipo = (b0 >> 1) & 0x3F
        tid = (b1 & 0x07) - 1
        if tipo <= 31:
            conto[tid] = conto.get(tid, 0) + 1
        if tipo == 33 and sub is None:
            sub = ((d[corpo + 2] >> 1) & 0x07) + 1
    return conto, sub


print("== 1. libx265: ha accettato `temporal-layers` o l'ha ignorato? ==")
for etichetta, par in [
    ("temporal-layers=1 bframes=4 b-pyramid=1",
     "crf=26:bframes=4:b-pyramid=1:temporal-layers=1:keyint=600:min-keyint=600:"
     "repeat-headers=1:log-level=info"),
    ("temporal-layers=2 bframes=8",
     "crf=26:bframes=8:b-pyramid=1:temporal-layers=2:keyint=600:min-keyint=600:"
     "repeat-headers=1:log-level=info"),
    ("opzione INESISTENTE (controllo)",
     "crf=26:questa-opzione-non-esiste=1:log-level=info"),
]:
    u = os.path.join(FUORI, re.sub(r"\W+", "_", etichetta) + ".h265")
    p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "info", "-y",
                        "-f", "rawvideo", "-pix_fmt", "nv12", "-s", MISURA, "-r", "30",
                        "-i", SORGENTE, "-frames:v", "48", "-c:v", "libx265",
                        "-x265-params", par, "-f", "hevc", u],
                       capture_output=True, text=True)
    s = p.stderr or ""
    conf = [r for r in s.splitlines()
            if "x265" in r and ("Unknown" in r or "unknown" in r or "temporal" in r
                                or "ignoring" in r or "options:" in r)]
    print("\n  %-42s rc=%d" % (etichetta, p.returncode))
    for r in conf[:4]:
        print("     | " + r.strip()[:170])
    if p.returncode == 0 and os.path.exists(u):
        conto, sub = leggi(u)
        print("     ⇒ temporal_id: %s ; sps_max_sub_layers = %s" % (conto, sub))

print("\n== 2. ⭐ IL TESTIMONE CHE NON PUO' FALLIRE: i bit alzati a mano ==")
d = bytearray(open(BASE, "rb").read())
off = nal_offsets(bytes(d))
alzate = 0
for inizio, corpo in off:
    tipo = (d[corpo] >> 1) & 0x3F
    if tipo == 0:                       # TRAIL_N: le figure non di riferimento
        d[corpo + 1] = (d[corpo + 1] & 0xF8) | 2   # nuh_temporal_id_plus1 = 2
        alzate += 1
u = os.path.join(FUORI, "testimone-bit-alzati.h265")
open(u, "wb").write(bytes(d))
conto, sub = leggi(u)
print("  alzate %d intestazioni NAL a `nuh_temporal_id_plus1 = 2`" % alzate)
print("  ⇒ il lettore riporta: temporal_id %s ; sps_max_sub_layers = %s" % (conto, sub))
if 1 in conto and conto[1] == alzate:
    print("  ⇒ ⭐ IL LETTORE VEDE i sotto-livelli quando ci sono, e li conta esatti.")
    print("     ⇒ lo ZERO misurato su EncSliceLP e' del CODIFICATORE, non del banco.")
else:
    print("  ⇒ ⛔ il lettore NON li vede: tutte le misure di D.1 sono da buttare.")

# ⚠ e il controllo dell'altro verso: un flusso cosi' etichettato e' ancora
#   decodificabile?  Serve a dire se l'etichetta da sola basta (non basta:
#   il VPS/SPS continuano a dichiarare UN solo sotto-livello).
p = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", u,
                    "-f", "null", "-"], capture_output=True, text=True)
print("  ⚠ e un flusso con le sole etichette alzate (VPS/SPS invariati) "
      "decodifica: %s" % ((p.stderr or "").strip().splitlines()[0][:110]
                          if (p.stderr or "").strip() else "SI', senza errori"))
