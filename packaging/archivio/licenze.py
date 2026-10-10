#!/usr/bin/env python3
"""licenze.py — the licence file for REMOTIX's components (DECISIONI §10.22), for the archive.

    licenze.py <archivio> <installatore> [<licenza-di-go>]   > THIRD-PARTY-LICENSES.txt

Called by pubblica.sh rigenera (from the release command). It gathers, with the TEXT of every licence
that asks to accompany the program:
  1. the product (remotix): ngtcp2 and nghttp3 linked STATICALLY, at the version the archive's SBOM
     says is linked (sbom/*.spdx.json); the text (COPYING) is downloaded from the project at the exact tag;
  2. the distribution libraries the product uses (linked dynamically, from the SBOM): they are not
     in our packages, they carry the distribution's licence — they are listed;
  3. the engine (remotix-install, static Go): the Go library (<licenza-di-go>, from the build
     container) and the modules of installatore/vendor/ (modules.txt) with each one's LICENSE;
A component with no licence text found is MARKED («DA VERIFICARE») and the exit code is 1: the file
never says more than it knows.
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
    parti.append(f"== {nome} {versione}\n   licence: {licenza}\n   {dove}\n\n{testo.strip()}\n")


# 1. ngtcp2 and nghttp3 linked into the product (versions from the SBOM: the same for every package)
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
    mancano.append("ngtcp2/nghttp3: no SBOM in the archive")
for lib in sorted(statiche):
    for v in sorted(statiche[lib]):
        url = f"https://raw.githubusercontent.com/ngtcp2/{lib}/v{v}/COPYING"
        try:
            testo = urllib.request.urlopen(url, timeout=30).read().decode()
        except Exception as e:  # without the text we do not publish a file that silently omits it
            mancano.append(f"{lib} {v}: {e}")
            testo = "(text not downloaded: " + url + ")"
        sezione(lib, v, spdx(testo), "linked STATICALLY into the remotix binary (" + url + ")", testo)

# 3. the engine: the Go library and the modules
if licenza_go and os.path.exists(licenza_go):
    t = open(licenza_go).read()
    sezione("Go (standard library and runtime)", "", spdx(t), "inside the static remotix-install binary", t)
else:
    mancano.append("the Go licence (the file from the build container)")
vendor = os.path.join(inst, "vendor")
# modules that carry no LICENSE at the tag used: the licence stated by the project, and the later text
ECCEZIONI = {
    "github.com/mattn/go-localereader": ("MIT", "the README at tag v0.0.1 says «MIT»; the text is the LICENSE the project added later",
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
            testo = "(text not downloaded: " + url + ")"
        sezione(mod, ver, lic, "Go module in the remotix-install binary (" + perche + ": " + url + ")", testo)
        continue
    if not trovato:
        mancano.append(f"{mod} {ver}: no LICENSE in the vendor tree")
        sezione(mod, ver, "DA VERIFICARE", "Go module in the remotix-install binary", "(no licence text in the vendor tree: to be checked on the project)")
        continue
    testo = "\n\n".join(open(x).read() for x in trovato)
    lic = spdx(testo)
    if lic == "DA VERIFICARE":
        mancano.append(f"{mod} {ver}: licence not recognised")
    sezione(mod, ver, lic, "Go module in the remotix-install binary (" + ", ".join(os.path.relpath(x, vendor) for x in trovato) + ")", testo)

# 2. the distribution libraries
elenco = "\n".join("   · " + x for x in sorted(dinamiche)) or "   (none: the SBOM lists none)"
testa = f"""REMOTIX — component licences (generated by packaging/archivio/licenze.py)

REMOTIX's code: PolyForm Noncommercial 1.0.0 (DECISIONI §10.22; the project's LICENSE file).
Below: third-party components that the REMOTIX packages CARRY INSIDE, each with its own
licence and its text.

The DISTRIBUTION libraries that remotix uses (linked dynamically or called at run
time) are not in the REMOTIX packages: the package manager installs them, each with the
licence and text the distribution ships in /usr/share/doc (or /usr/share/licenses). From the SBOM:
{elenco}
⭐ Phase 18 (DECISIONI §10.22, §10.25): REMOTIX no longer links ffmpeg (libavcodec GPL). In its place
libva (MIT) and libopus (BSD-3-Clause). ⛔ Phase 19 (DECISIONI §10.27): no software encoding —
OpenH264 and SVT-AV1 are out. The VA drivers (Mesa MIT, intel-media-driver MIT/BSD) are loaded separately.
"""
print(testa)
for p in parti:
    print(p)
if mancano:
    print("⚠ DA VERIFICARE:\n" + "\n".join("   · " + x for x in mancano))
    print("licenze.py: DA VERIFICARE — " + "; ".join(mancano), file=sys.stderr)
    sys.exit(1)
