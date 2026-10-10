#!/usr/bin/env python3
"""19-tabella.py — the VA-API / Vulkan table from the outcomes of 19-confronto.sh (from 18-tabella.py).

For each test it puts the two engines side by side (vaapi = the product, vulkan = the new module): ffprobe (profile, level,
size, colour) IDENTICAL or not, the decoded frames, PSNR, SSIM, the bytes
of the stream and of the key frame, the median times per frame.  ⛔ The verdict
"worse" is written with numbers: PSNR lower by 0.5 dB, or bytes more than 10 %
higher, or encoding more than 20 % slower.
"""
import csv, io, json, os, statistics, sys

esiti = [json.loads(r) for r in open(sys.argv[1]) if r.strip()]
cartella = os.path.dirname(os.path.abspath(sys.argv[1]))

def tempi(prova, versione):
    p = os.path.join(cartella, f"{prova}-{versione}.csv")
    if not os.path.exists(p):
        return None
    righe = [r for r in open(p) if r and r[0].isdigit()]
    if not righe:
        return None
    lett = csv.DictReader(io.StringIO("n,chiave,byte,us_conversione,us_caricamento,us_codifica,ricodifiche\n" + "".join(righe)))
    cod, prep, chiave_byte, delta_byte = [], [], [], []
    for r in lett:
        if r["chiave"] == "-":
            continue
        cod.append(int(r["us_codifica"]))
        prep.append(int(r["us_conversione"]) + int(r["us_caricamento"]))
        (chiave_byte if r["chiave"] == "1" else delta_byte).append(int(r["byte"]))
    if not cod:
        return None
    return dict(cod=statistics.median(cod), cod_max=max(cod), prep=statistics.median(prep),
                chiave=max(chiave_byte) if chiave_byte else 0,
                delta=statistics.median(delta_byte) if delta_byte else 0, n=len(cod))

per_prova = {}
for e in esiti:
    per_prova.setdefault(e["prova"], {})[e["versione"]] = e

def num(x):
    """the PSNR is "y:.. u:.. v:.. average:..": the average is judged, everything is printed"""
    try:
        if "average:" in str(x):
            x = str(x).split("average:")[1]
        return float(x)
    except Exception:
        return None

print(f"{'test':38} {'ver':7} {'code':4} {'dec':>4} {'psnr':>6} {'ssim':>6} {'bytes':>9} {'key':>8} {'delta':>7} {'enc µs':>7} {'prep µs':>7}  ffprobe · psnr y/u/v")
peggio = []
for prova, v in per_prova.items():
    for versione in ("vaapi", "vulkan", "scheda"):
        e = v.get(versione)
        if not e:
            if versione != "scheda":
                print(f"{prova:38} {versione:7} MISSING")
            continue
        t = tempi(prova, versione) or {}
        print(f"{prova:38} {versione:7} {e['codice']:<4} {e['decodificati']:>4} {str(num(e['psnr']) or '')[:6]:>6} {str(e['ssim'])[:6]:>6} "
              f"{e['byte_flusso']:>9} {t.get('chiave',0):>8} {t.get('delta',0):>7.0f} {t.get('cod',0):>7.0f} {t.get('prep',0):>7.0f}  {e['ffprobe']} · {e['psnr']}")
    a, b = v.get("vaapi"), v.get("vulkan")
    if a and b:
        note = []
        if a["ffprobe"] != b["ffprobe"]:
            note.append(f"ffprobe DIFFERENT: «{a['ffprobe']}» → «{b['ffprobe']}»")
        if a["decodificati"] != b["decodificati"]:
            note.append(f"decoded {a['decodificati']} → {b['decodificati']}")
        pa, pb = num(a["psnr"]), num(b["psnr"])
        if pa and pb and pb < pa - 0.5:
            note.append(f"PSNR {pa:.2f} → {pb:.2f} dB")
        if a["byte_flusso"] and b["byte_flusso"] > a["byte_flusso"] * 1.10:
            note.append(f"byte +{(b['byte_flusso']/a['byte_flusso']-1)*100:.0f} %")
        ta, tb = tempi(prova, "vaapi"), tempi(prova, "vulkan")
        if ta and tb and tb["cod"] > ta["cod"] * 1.20:
            note.append(f"encoding {ta['cod']:.0f} → {tb['cod']:.0f} µs")
        if b["codice"] != 0 or int(b.get("errori_decodifica", 0)) > 0:
            note.append(f"VULKAN has code {b['codice']} and {b.get('errori_decodifica')} decoding errors")
        if note:
            peggio.append(f"{prova}: " + " · ".join(note))
    # ⭐ the INTEGRATED product (engine "scheda", since the graft): against VA-API, same rule
    a, s_ = v.get("vaapi"), v.get("scheda")
    if a and s_:
        note = []
        if a["ffprobe"] != s_["ffprobe"]:
            note.append(f"ffprobe DIFFERENT: «{a['ffprobe']}» → «{s_['ffprobe']}»")
        if a["decodificati"] != s_["decodificati"]:
            note.append(f"decoded {a['decodificati']} → {s_['decodificati']}")
        pa, ps = num(a["psnr"]), num(s_["psnr"])
        if pa and ps and ps < pa - 0.5:
            note.append(f"PSNR {pa:.2f} → {ps:.2f} dB")
        if a["byte_flusso"] and s_["byte_flusso"] > a["byte_flusso"] * 1.10:
            note.append(f"byte +{(s_['byte_flusso']/a['byte_flusso']-1)*100:.0f} %")
        ta, ts = tempi(prova, "vaapi"), tempi(prova, "scheda")
        if ta and ts and ts["cod"] > ta["cod"] * 1.20:
            note.append(f"encoding {ta['cod']:.0f} → {ts['cod']:.0f} µs")
        if s_["codice"] != 0 or int(s_.get("errori_decodifica", 0)) > 0:
            note.append(f"the INTEGRATED PRODUCT has code {s_['codice']} and {s_.get('errori_decodifica')} decoding errors")
        if note:
            peggio.append(f"{prova} [integrated product «scheda»]: " + " · ".join(note))
print()
if peggio:
    print("⛔ WHERE VULKAN IS NOT EQUAL TO OR IS WORSE THAN VA-API:")
    for r in peggio:
        print("   " + r)
else:
    print("⭐ no test in which Vulkan is worse than VA-API (ffprobe, decoding, PSNR, bytes, times)")
