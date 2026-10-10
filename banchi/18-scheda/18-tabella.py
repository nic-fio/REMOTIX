#!/usr/bin/env python3
"""18-tabella.py — the old/new table from the outcomes of 18-confronto.sh.

For each test it puts the two versions side by side: ffprobe (profile, level,
size, colour) IDENTICAL or not, the decoded frames, PSNR, SSIM, the bytes
of the stream and of the key frame, the median times per frame.  ⛔ The verdict
«worse» is written with numbers: PSNR lower by 0.5 dB, or bytes more than 10 %
higher, or encoding more than 20 % slower.
"""
import csv, io, json, os, statistics, sys

outcomes = [json.loads(r) for r in open(sys.argv[1]) if r.strip()]
folder = os.path.dirname(os.path.abspath(sys.argv[1]))

def times(prova, version_v):
    p = os.path.join(folder, f"{prova}-{version_v}.csv")
    if not os.path.exists(p):
        return None
    line_list = [r for r in open(p) if r and r[0].isdigit()]
    if not line_list:
        return None
    rdr = csv.DictReader(io.StringIO("n,key_id,byte,convert_us,upload_us,encode_us,reencodes\n" + "".join(line_list)))
    cod, prep, key_byte, delta_byte = [], [], [], []
    for r in rdr:
        if r["key_id"] == "-":
            continue
        cod.append(int(r["encode_us"]))
        prep.append(int(r["convert_us"]) + int(r["upload_us"]))
        (key_byte if r["key_id"] == "1" else delta_byte).append(int(r["byte"]))
    if not cod:
        return None
    return dict(cod=statistics.median(cod), cod_max=max(cod), prep=statistics.median(prep),
                key_id=max(key_byte) if key_byte else 0,
                delta=statistics.median(delta_byte) if delta_byte else 0, n=len(cod))

per_test = {}
for e in outcomes:
    per_test.setdefault(e["prova"], {})[e["version_v"]] = e

def num(x):
    """the PSNR is «y:.. u:.. v:.. average:..»: the average is judged, everything is printed"""
    try:
        if "average:" in str(x):
            x = str(x).split("average:")[1]
        return float(x)
    except Exception:
        return None

print(f"{'prova':38} {'ver':7} {'cod':4} {'dec':>4} {'psnr':>6} {'ssim':>6} {'byte':>9} {'key_id':>8} {'delta':>7} {'cod µs':>7} {'prep µs':>7}  ffprobe · psnr y/u/v")
worse = []
for prova, v in per_test.items():
    for version_v in ("prior", "fresh"):
        e = v.get(version_v)
        if not e:
            print(f"{prova:38} {version_v:7} MISSING"); continue
        t = times(prova, version_v) or {}
        print(f"{prova:38} {version_v:7} {e['code_v']:<4} {e['decoded']:>4} {str(num(e['psnr']) or '')[:6]:>6} {str(e['ssim'])[:6]:>6} "
              f"{e['byte_flusso']:>9} {t.get('key_id',0):>8} {t.get('delta',0):>7.0f} {t.get('cod',0):>7.0f} {t.get('prep',0):>7.0f}  {e['ffprobe']} · {e['psnr']}")
    a, b = v.get("prior"), v.get("fresh")
    if a and b:
        note = []
        if a["ffprobe"] != b["ffprobe"]:
            note.append(f"ffprobe DIFFERENT: «{a['ffprobe']}» → «{b['ffprobe']}»")
        if a["decoded"] != b["decoded"]:
            note.append(f"decoded {a['decoded']} → {b['decoded']}")
        pa, pb = num(a["psnr"]), num(b["psnr"])
        if pa and pb and pb < pa - 0.5:
            note.append(f"PSNR {pa:.2f} → {pb:.2f} dB")
        if a["byte_flusso"] and b["byte_flusso"] > a["byte_flusso"] * 1.10:
            note.append(f"byte +{(b['byte_flusso']/a['byte_flusso']-1)*100:.0f} %")
        ta, tb = times(prova, "prior"), times(prova, "fresh")
        if ta and tb and tb["cod"] > ta["cod"] * 1.20:
            note.append(f"encoding {ta['cod']:.0f} → {tb['cod']:.0f} µs")
        if b["code_v"] != 0 or int(b.get("errori_decodifica", 0)) > 0:
            note.append(f"the NEW one has code {b['code_v']} and {b.get('errori_decodifica')} decoding errors")
        if note:
            worse.append(f"{prova}: " + " · ".join(note))
print()
if worse:
    print("⛔ WHERE THE NEW ONE IS NOT EQUAL OR IS WORSE:")
    for r in worse:
        print("   " + r)
else:
    print("⭐ no test in which the new one is worse than the old (ffprobe, decoding, PSNR, bytes, times)")
