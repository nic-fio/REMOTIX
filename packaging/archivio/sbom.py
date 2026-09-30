#!/usr/bin/env python3
"""sbom.py — lo SBOM di ogni pacchetto del prodotto nell'archivio di REMOTIX (R24, fasi/17 §6.5 p.11).

    sbom.py <cartella-dati> <cartella-uscita>

Per ogni pacchetto, pubblica.sh ha lasciato in <cartella-dati>:
  <nome>.nv          nome e versione del pacchetto
  <nome>.file        il file nell'archivio
  <nome>.incorporate usr/share/remotix/incorporate.json del pacchetto: le versioni di ngtcp2 e
                     nghttp3 COLLEGATE nel binario (pkg-config nel contenitore di costruzione)
  <nome>.bundled     quel che il pacchetto DICHIARA (Static-Built-Using del .deb, bundled() del .rpm;
                     Arch non ha un campo: vuoto)
  <nome>.richieste   le dipendenze dichiarate (le librerie della distribuzione, collegate dinamiche)

⛔ R24 rosso se la versione collegata manca o è diversa da quella dichiarata: lo SBOM non si scrive
e l'uscita è 1. ⚠ «La versione nel binario»: ngtcp2 e nghttp3 statiche non lasciano una stringa di
versione nel binario (ngtcp2_version() non è chiamata, il linker la toglie). La fonte è il pkg-config
delle .a collegate, letto nello stesso contenitore che collega il binario; leggerla DAL binario
chiederebbe una riga nel prodotto (ngtcp2_version() nel registro d'avvio: una richiesta a REMOTIX,
§6.5-bis, non fatta).
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
        print(f"   SBOM {b}: SALTATO — il pacchetto non ha incorporate.json (costruito prima di T8)")
        continue
    inc = json.loads(inc_t)
    dich = {}
    for m in re.finditer(r"(ngtcp2|nghttp3)\)?\s*\(?\s*=\s*([0-9][0-9.]*)", leggi("bundled")):
        dich[m.group(1)] = m.group(2)
    esito = []
    for lib in ("ngtcp2", "nghttp3"):
        v = inc.get(lib)
        if not v:
            esito.append(f"{lib}: versione collegata ASSENTE"); rosso = 1
        elif lib in dich and dich[lib] != v:
            esito.append(f"{lib}: collegata {v}, dichiarata {dich[lib]}"); rosso = 1
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
            "comment": "collegata STATICA nel binario (" + inc.get("fonte", "") + ")" +
                       (f"; dichiarata dal pacchetto: {dich[lib]}" if lib in dich else ""),
        })
        rel.append({"spdxElementId": "SPDXRef-remotix", "relationshipType": "STATIC_LINK", "relatedSpdxElement": f"SPDXRef-{lib}"})
    for i, d in enumerate(x.strip() for x in re.split(r"[,\n]", leggi("richieste")) if x.strip()):
        if d.startswith("rpmlib(") or d.startswith("/"):
            continue
        pacchetti.append({"SPDXID": f"SPDXRef-dip-{i}", "name": d, "versionInfo": "NOASSERTION",
                          "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
                          "comment": "dipendenza della distribuzione, collegata dinamica o usata a tempo di esecuzione"})
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
    print(f"   SBOM {b}: ngtcp2 {inc['ngtcp2']}, nghttp3 {inc['nghttp3']} (dichiarate: {dich or 'nessun campo'})")
sys.exit(rosso)
