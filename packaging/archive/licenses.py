#!/usr/bin/env python3
"""licenses.py — the licence file for REMOTIX's components (DECISIONI §10.22), for the archive.

    licenses.py <archivio> <installatore> [<licenza-di-go>]   > THIRD-PARTY-LICENSES.txt

Called by pubblica.sh rigenera (from the release command). It gathers, with the TEXT of every licence
that asks to accompany the program:
  1. the product (remotix): ngtcp2 and nghttp3 linked STATICALLY, at the version the archive's SBOM
     says is linked (sbom/*.spdx.json); the text (COPYING) is downloaded from the project at the exact tag;
  2. the distribution libraries the product uses (linked dynamically, from the SBOM): they are not
     in our packages, they carry the distribution's licence — they are listed;
  3. the engine (remotix-install, static Go): the Go library (<licenza-di-go>, from the build
     container) and the modules of installer/vendor/ (modules.txt) with each one's LICENSE;
A component with no licence text found is MARKED («TO BE CHECKED») and the exit code is 1: the file
never says more than it knows.
"""
import glob, json, os, re, sys, urllib.request

archive, inst = sys.argv[1], sys.argv[2]
go_license = sys.argv[3] if len(sys.argv) > 3 else ""
missing = []
parts = []


def spdx(text):
    t = text.lower()
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
    return "TO BE CHECKED"


def section(name, version, licence, dove, text):
    parts.append(f"== {name} {version}\n   licence: {licence}\n   {dove}\n\n{text.strip()}\n")


# 1. ngtcp2 and nghttp3 linked into the product (versions from the SBOM: the same for every package)
static = {}
dynamic = set()
for f in sorted(glob.glob(os.path.join(archive, "sbom", "*.spdx.json"))):
    d = json.load(open(f))
    for p in d.get("packages", []):
        if p.get("name") in ("ngtcp2", "nghttp3"):
            static.setdefault(p["name"], set()).add(p["versionInfo"])
        elif p.get("SPDXID", "").startswith("SPDXRef-dip-"):
            dynamic.add(re.sub(r"\s*\(.*", "", p["name"]).strip())
if not static:
    missing.append("ngtcp2/nghttp3: no SBOM in the archive")
for lib in sorted(static):
    for v in sorted(static[lib]):
        url = f"https://raw.githubusercontent.com/ngtcp2/{lib}/v{v}/COPYING"
        try:
            text = urllib.request.urlopen(url, timeout=30).read().decode()
        except Exception as e:  # without the text we do not publish a file that silently omits it
            missing.append(f"{lib} {v}: {e}")
            text = "(text not downloaded: " + url + ")"
        section(lib, v, spdx(text), "linked STATICALLY into the remotix binary (" + url + ")", text)

# 3. the engine: the Go library and the modules
if go_license and os.path.exists(go_license):
    t = open(go_license).read()
    section("Go (standard library and runtime)", "", spdx(t), "inside the static remotix-install binary", t)
else:
    missing.append("the Go licence (the file from the build container)")
vendor = os.path.join(inst, "vendor")
# modules that carry no LICENSE at the tag used: the licence stated by the project, and the later text
EXCEPTIONS = {
    "github.com/mattn/go-localereader": ("MIT", "the README at tag v0.0.1 says «MIT»; the text is the LICENSE the project added later",
                                         "https://raw.githubusercontent.com/mattn/go-localereader/master/LICENSE"),
}
for line in open(os.path.join(vendor, "modules.txt")):
    m = re.match(r"^# (\S+) (\S+)", line)
    if not m:
        continue
    mod, ver = m.groups()
    d, found = mod, None
    while d and d != ".":
        c = sorted(glob.glob(os.path.join(vendor, d, "LICENSE*")) + glob.glob(os.path.join(vendor, d, "COPYING*")) +
                   glob.glob(os.path.join(vendor, d, "UNLICENSE*")))
        if c:
            found = c
            break
        d = os.path.dirname(d)
    if not found and mod in EXCEPTIONS:
        lic, why, url = EXCEPTIONS[mod]
        try:
            text = urllib.request.urlopen(url, timeout=30).read().decode()
        except Exception as e:
            missing.append(f"{mod} {ver}: {e}")
            text = "(text not downloaded: " + url + ")"
        section(mod, ver, lic, "Go module in the remotix-install binary (" + why + ": " + url + ")", text)
        continue
    if not found:
        missing.append(f"{mod} {ver}: no LICENSE in the vendor tree")
        section(mod, ver, "TO BE CHECKED", "Go module in the remotix-install binary", "(no licence text in the vendor tree: to be checked on the project)")
        continue
    text = "\n\n".join(open(x).read() for x in found)
    lic = spdx(text)
    if lic == "TO BE CHECKED":
        missing.append(f"{mod} {ver}: licence not recognised")
    section(mod, ver, lic, "Go module in the remotix-install binary (" + ", ".join(os.path.relpath(x, vendor) for x in found) + ")", text)

# 2. the distribution libraries
listing = "\n".join("   · " + x for x in sorted(dynamic)) or "   (none: the SBOM lists none)"
head = f"""REMOTIX — component licences (generated by packaging/archive/licenses.py)

REMOTIX's code: its own licence, LICENSE.md (DECISIONI §10.39).
Below: third-party components that the REMOTIX packages CARRY INSIDE, each with its own
licence and its text.

The DISTRIBUTION libraries that remotix uses (linked dynamically or called at run
time) are not in the REMOTIX packages: the package manager installs them, each with the
licence and text the distribution ships in /usr/share/doc (or /usr/share/licenses). From the SBOM:
{listing}
⭐ Phase 18 (DECISIONI §10.22, §10.25): REMOTIX no longer links ffmpeg (libavcodec GPL). In its place
libva (MIT) and libopus (BSD-3-Clause). ⛔ Phase 19 (DECISIONI §10.27): no software encoding —
OpenH264 and SVT-AV1 are out. The VA drivers (Mesa MIT, intel-media-driver MIT/BSD) are loaded separately.
"""
print(head)
for p in parts:
    print(p)
if missing:
    print("⚠ TO BE CHECKED:\n" + "\n".join("   · " + x for x in missing))
    print("licenses.py: TO BE CHECKED — " + "; ".join(missing), file=sys.stderr)
    sys.exit(1)
