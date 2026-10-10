#!/usr/bin/env python3
"""sbom.py — the SBOM of every product package in the REMOTIX archive (R24, fasi/17 §6.5 p.11).

    sbom.py <cartella-dati> <cartella-uscita>

For every package, pubblica.sh has left in <cartella-dati>:
  <nome>.nv          package name and version
  <nome>.file        the file in the archive
  <nome>.incorporate the package's usr/share/remotix/incorporate.json: the versions of ngtcp2 and
                     nghttp3 LINKED into the binary (pkg-config in the build container)
  <nome>.bundled     what the package DECLARES (Static-Built-Using of the .deb, bundled() of the .rpm;
                     Arch has no field: empty)
  <nome>.richieste   the declared dependencies (the distribution libraries, linked dynamically)

⛔ R24 red if the linked version is missing or differs from the declared one: the SBOM is not written
and the exit code is 1. ⚠ «The version in the binary»: static ngtcp2 and nghttp3 leave no version
string in the binary (ngtcp2_version() is not called, the linker drops it). The source is the pkg-config
of the linked .a files, read in the same container that links the binary; reading it FROM the binary
would need a line in the product (ngtcp2_version() in the startup log: a request to REMOTIX,
§6.5-bis, not made).
"""
import hashlib, json, os, re, sys, uuid

dati, uscita = sys.argv[1], sys.argv[2]
os.makedirs(uscita, exist_ok=True)
FONTI = {
    "ngtcp2": "https://github.com/ngtcp2/ngtcp2/releases/download/v{v}/ngtcp2-{v}.tar.xz",
    "nghttp3": "https://github.com/ngtcp2/nghttp3/releases/download/v{v}/nghttp3-{v}.tar.xz",
}
rosso = 0
nomi = sorted({f.rsplit(".", 1)[0] for f in os.listdir(dati) if f.endswith(".nv")})
for b in nomi:
    leggi = lambda est: open(os.path.join(dati, b + "." + est)).read() if os.path.exists(os.path.join(dati, b + "." + est)) else ""
    nv = leggi("nv").split()
    pk, ver = nv[0], nv[1]
    f = leggi("file").strip()
    inc_t = leggi("incorporate").strip()
    if not inc_t:
        print(f"   SBOM {b}: SKIPPED — the package has no incorporate.json (built before T8)")
        continue
    inc = json.loads(inc_t)
    dich = {}
    for m in re.finditer(r"(ngtcp2|nghttp3)\)?\s*\(?\s*=\s*([0-9][0-9.]*)", leggi("bundled")):
        dich[m.group(1)] = m.group(2)
    esito = []
    for lib in ("ngtcp2", "nghttp3"):
        v = inc.get(lib)
        if not v:
            esito.append(f"{lib}: linked version MISSING"); rosso = 1
        elif lib in dich and dich[lib] != v:
            esito.append(f"{lib}: linked {v}, declared {dich[lib]}"); rosso = 1
    if esito:
        print(f"   ⛔ R24 {b}: " + "; ".join(esito))
        continue
    sha = hashlib.sha256(open(f, "rb").read()).hexdigest() if f and os.path.exists(f) else ""
    pacchetti = [{
        "SPDXID": "SPDXRef-remotix", "name": pk, "versionInfo": ver, "supplier": "Organization: REMOTIX",
        "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
        "checksums": [{"algorithm": "SHA256", "checksumValue": sha}] if sha else [],
        "packageFileName": os.path.basename(f),
    }]
    rel = [{"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": "SPDXRef-remotix"}]
    for lib in ("ngtcp2", "nghttp3"):
        v = inc[lib]
        pacchetti.append({
            "SPDXID": f"SPDXRef-{lib}", "name": lib, "versionInfo": v, "supplier": "Organization: ngtcp2 project",
            "downloadLocation": FONTI[lib].format(v=v), "filesAnalyzed": False, "licenseDeclared": "MIT",
            "externalRefs": [{"referenceCategory": "PACKAGE-MANAGER", "referenceType": "purl",
                              "referenceLocator": f"pkg:github/ngtcp2/{lib}@v{v}"}],
            "comment": "linked STATICALLY into the binary (" + inc.get("fonte", "") + ")" +
                       (f"; declared by the package: {dich[lib]}" if lib in dich else ""),
        })
        rel.append({"spdxElementId": "SPDXRef-remotix", "relationshipType": "STATIC_LINK", "relatedSpdxElement": f"SPDXRef-{lib}"})
    for i, d in enumerate(x.strip() for x in re.split(r"[,\n]", leggi("richieste")) if x.strip()):
        if d.startswith("rpmlib(") or d.startswith("/"):
            continue
        pacchetti.append({"SPDXID": f"SPDXRef-dip-{i}", "name": d, "versionInfo": "NOASSERTION",
                          "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
                          "comment": "distribution dependency, linked dynamically or used at run time"})
        rel.append({"spdxElementId": "SPDXRef-remotix", "relationshipType": "DEPENDS_ON", "relatedSpdxElement": f"SPDXRef-dip-{i}"})
    doc = {
        "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{pk}-{ver}", "documentNamespace": f"https://remotix.invalid/sbom/{b}-{uuid.uuid5(uuid.NAMESPACE_URL, b + sha)}",
        "creationInfo": {"created": os.environ.get("SBOM_DATA", "") or __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         "creators": ["Tool: REMOTIX packaging/archivio/sbom.py"]},
        "packages": pacchetti, "relationships": rel,
    }
    with open(os.path.join(uscita, b + ".spdx.json"), "w") as o:
        json.dump(doc, o, indent=2, ensure_ascii=False)
    print(f"   SBOM {b}: ngtcp2 {inc['ngtcp2']}, nghttp3 {inc['nghttp3']} (declared: {dich or 'no field'})")
sys.exit(rosso)
