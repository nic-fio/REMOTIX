#!/usr/bin/env python3
"""licenze.py — il file delle licenze dei componenti di REMOTIX (DECISIONI §10.22), per l'archivio.

    licenze.py <archivio> <installatore> [<licenza-di-go>]   > LICENZE-COMPONENTI.txt

Lo chiama pubblica.sh rigenera (dal comando di rilascio). Mette insieme, con il TESTO di ogni licenza
che chiede di accompagnare il programma:
  1. il prodotto (remotix): ngtcp2 e nghttp3 collegate STATICHE, alla versione che lo SBOM dell'archivio
     dice collegata (sbom/*.spdx.json); il testo (COPYING) si scarica dal progetto al tag esatto;
  2. le librerie della distribuzione che il prodotto usa (collegate dinamiche, dallo SBOM): non stanno
     nei nostri pacchetti, hanno la licenza della distribuzione — si elencano;
  3. il motore (remotix-install, Go statico): la libreria di Go (<licenza-di-go>, dal contenitore di
     costruzione) e i moduli di installatore/vendor/ (modules.txt) col LICENSE di ognuno;
Un componente senza testo di licenza trovato si SEGNA («DA VERIFICARE») e l'uscita è 1: il file non
dice mai più di quel che sa.
"""
import glob, json, os, re, sys, urllib.request

archivio, inst = sys.argv[1], sys.argv[2]
licenza_go = sys.argv[3] if len(sys.argv) > 3 else ""
mancano = []
parti = []


def spdx(testo):
    t = testo.lower()
    if "sil open font license" in t:
        return "OFL-1.1"
    if "unlicense" in t and "mit" in t:
        return "Unlicense OR MIT"
    if "this is free and unencumbered software" in t:
        return "Unlicense"
    if "apache license" in t and "version 2.0" in t:
        return "Apache-2.0"
    if "permission is hereby granted, free of charge" in t:
        return "MIT"
    if "redistribution and use in source and binary forms" in t:
        return "BSD-3-Clause" if "neither the name" in t or "may be used to endorse" in t else "BSD-2-Clause"
    return "DA VERIFICARE"


def sezione(nome, versione, licenza, dove, testo):
    parti.append(f"== {nome} {versione}\n   licenza: {licenza}\n   {dove}\n\n{testo.strip()}\n")


# 1. ngtcp2 e nghttp3 collegate nel prodotto (le versioni dallo SBOM: le stesse per ogni pacchetto)
statiche = {}
dinamiche = set()
for f in sorted(glob.glob(os.path.join(archivio, "sbom", "*.spdx.json"))):
    d = json.load(open(f))
    for p in d.get("packages", []):
        if p.get("name") in ("ngtcp2", "nghttp3"):
            statiche.setdefault(p["name"], set()).add(p["versionInfo"])
        elif p.get("SPDXID", "").startswith("SPDXRef-dip-"):
            dinamiche.add(re.sub(r"\s*\(.*", "", p["name"]).strip())
if not statiche:
    mancano.append("ngtcp2/nghttp3: nessuno SBOM nell'archivio")
for lib in sorted(statiche):
    for v in sorted(statiche[lib]):
        url = f"https://raw.githubusercontent.com/ngtcp2/{lib}/v{v}/COPYING"
        try:
            testo = urllib.request.urlopen(url, timeout=30).read().decode()
        except Exception as e:  # senza il testo non si pubblica un file che lo ometta in silenzio
            mancano.append(f"{lib} {v}: {e}")
            testo = "(testo non scaricato: " + url + ")"
        sezione(lib, v, spdx(testo), "collegata STATICA nel binario di remotix (" + url + ")", testo)

# 3. il motore: la libreria di Go e i moduli
if licenza_go and os.path.exists(licenza_go):
    t = open(licenza_go).read()
    sezione("Go (libreria standard e runtime)", "", spdx(t), "dentro il binario statico di remotix-install", t)
else:
    mancano.append("la licenza di Go (il file dal contenitore di costruzione)")
vendor = os.path.join(inst, "vendor")
# i moduli che al tag usato non portano il LICENSE: la licenza detta dal progetto, e il testo di dopo
ECCEZIONI = {
    "github.com/mattn/go-localereader": ("MIT", "il README al tag v0.0.1 dice «MIT»; il testo è il LICENSE che il progetto ha aggiunto dopo",
                                         "https://raw.githubusercontent.com/mattn/go-localereader/master/LICENSE"),
}
for riga in open(os.path.join(vendor, "modules.txt")):
    m = re.match(r"^# (\S+) (\S+)", riga)
    if not m:
        continue
    mod, ver = m.groups()
    d, trovato = mod, None
    while d and d != ".":
        c = sorted(glob.glob(os.path.join(vendor, d, "LICENSE*")) + glob.glob(os.path.join(vendor, d, "COPYING*")) +
                   glob.glob(os.path.join(vendor, d, "UNLICENSE*")))
        if c:
            trovato = c
            break
        d = os.path.dirname(d)
    if not trovato and mod in ECCEZIONI:
        lic, perche, url = ECCEZIONI[mod]
        try:
            testo = urllib.request.urlopen(url, timeout=30).read().decode()
        except Exception as e:
            mancano.append(f"{mod} {ver}: {e}")
            testo = "(testo non scaricato: " + url + ")"
        sezione(mod, ver, lic, "modulo Go nel binario di remotix-install (" + perche + ": " + url + ")", testo)
        continue
    if not trovato:
        mancano.append(f"{mod} {ver}: nessun LICENSE nel vendor")
        sezione(mod, ver, "DA VERIFICARE", "modulo Go nel binario di remotix-install", "(nessun testo di licenza nel vendor: da verificare sul progetto)")
        continue
    testo = "\n\n".join(open(x).read() for x in trovato)
    lic = spdx(testo)
    if lic == "DA VERIFICARE":
        mancano.append(f"{mod} {ver}: licenza non riconosciuta")
    sezione(mod, ver, lic, "modulo Go nel binario di remotix-install (" + ", ".join(os.path.relpath(x, vendor) for x in trovato) + ")", testo)

# 2. le librerie della distribuzione
elenco = "\n".join("   · " + x for x in sorted(dinamiche)) or "   (nessuna: lo SBOM non ne elenca)"
testa = f"""REMOTIX — le licenze dei componenti (generato da packaging/archivio/licenze.py)

Il codice di REMOTIX: PolyForm Noncommercial 1.0.0 (DECISIONI §10.22; il file LICENSE del progetto).
Qui sotto: i componenti di altri che i pacchetti di REMOTIX PORTANO DENTRO, ognuno con la sua
licenza e il suo testo.

Le librerie della DISTRIBUZIONE che remotix usa (collegate dinamiche o chiamate a tempo di
esecuzione) non stanno nei pacchetti di REMOTIX: le installa il gestore di pacchetti, ognuna con la
licenza e il testo che la distribuzione porta in /usr/share/doc (o /usr/share/licenses). Dallo SBOM:
{elenco}
⭐ Fase 18 (DECISIONI §10.22, §10.25): REMOTIX non collega più ffmpeg (libavcodec GPL). Al suo posto
libva (MIT) e libopus (BSD-3-Clause). ⛔ Fase 19 (DECISIONI §10.27): niente codifica in software —
OpenH264 e SVT-AV1 sono usciti. I driver VA (Mesa MIT, intel-media-driver MIT/BSD) si caricano a parte.
"""
print(testa)
for p in parti:
    print(p)
if mancano:
    print("⚠ DA VERIFICARE:\n" + "\n".join("   · " + x for x in mancano))
    print("licenze.py: DA VERIFICARE — " + "; ".join(mancano), file=sys.stderr)
    sys.exit(1)
