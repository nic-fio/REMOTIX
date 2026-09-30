#!/usr/bin/env python3
"""18-tabella.py — la tabella vecchio/nuovo dagli esiti di 18-confronto.sh.

Per ogni prova mette in colonna le due versioni: ffprobe (profilo, livello,
misura, colore) IDENTICO o no, i fotogrammi decodificati, PSNR, SSIM, i byte
del flusso e della chiave, i tempi mediani per fotogramma.  ⛔ Il verdetto
«peggio» si scrive coi numeri: PSNR piu' basso di 0,5 dB, o byte oltre il 10 %
in piu', o codifica oltre il 20 % piu' lenta.
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
    """il PSNR e' «y:.. u:.. v:.. average:..»: si giudica la media, si stampa tutto"""
    try:
        if "average:" in str(x):
            x = str(x).split("average:")[1]
        return float(x)
    except Exception:
        return None

print(f"{'prova':38} {'ver':7} {'cod':4} {'dec':>4} {'psnr':>6} {'ssim':>6} {'byte':>9} {'chiave':>8} {'delta':>7} {'cod µs':>7} {'prep µs':>7}  ffprobe · psnr y/u/v")
peggio = []
for prova, v in per_prova.items():
    for versione in ("vecchio", "nuovo"):
        e = v.get(versione)
        if not e:
            print(f"{prova:38} {versione:7} MANCA"); continue
        t = tempi(prova, versione) or {}
        print(f"{prova:38} {versione:7} {e['codice']:<4} {e['decodificati']:>4} {str(num(e['psnr']) or '')[:6]:>6} {str(e['ssim'])[:6]:>6} "
              f"{e['byte_flusso']:>9} {t.get('chiave',0):>8} {t.get('delta',0):>7.0f} {t.get('cod',0):>7.0f} {t.get('prep',0):>7.0f}  {e['ffprobe']} · {e['psnr']}")
    a, b = v.get("vecchio"), v.get("nuovo")
    if a and b:
        note = []
        if a["ffprobe"] != b["ffprobe"]:
            note.append(f"ffprobe DIVERSO: «{a['ffprobe']}» → «{b['ffprobe']}»")
        if a["decodificati"] != b["decodificati"]:
            note.append(f"decodificati {a['decodificati']} → {b['decodificati']}")
        pa, pb = num(a["psnr"]), num(b["psnr"])
        if pa and pb and pb < pa - 0.5:
            note.append(f"PSNR {pa:.2f} → {pb:.2f} dB")
        if a["byte_flusso"] and b["byte_flusso"] > a["byte_flusso"] * 1.10:
            note.append(f"byte +{(b['byte_flusso']/a['byte_flusso']-1)*100:.0f} %")
        ta, tb = tempi(prova, "vecchio"), tempi(prova, "nuovo")
        if ta and tb and tb["cod"] > ta["cod"] * 1.20:
            note.append(f"codifica {ta['cod']:.0f} → {tb['cod']:.0f} µs")
        if b["codice"] != 0 or int(b.get("errori_decodifica", 0)) > 0:
            note.append(f"il NUOVO ha codice {b['codice']} e {b.get('errori_decodifica')} errori di decodifica")
        if note:
            peggio.append(f"{prova}: " + " · ".join(note))
print()
if peggio:
    print("⛔ DOVE IL NUOVO NON E' UGUALE O E' PEGGIO:")
    for r in peggio:
        print("   " + r)
else:
    print("⭐ nessuna prova in cui il nuovo sia peggio del vecchio (ffprobe, decodifica, PSNR, byte, tempi)")
