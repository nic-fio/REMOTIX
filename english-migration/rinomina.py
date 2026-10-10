#!/usr/bin/env python3
"""Rinomina meccanica dei nomi italiani di REMOTIX con il vocabolario comune.

  rinomina.py piano  [file...]   calcola la tabella vecchio → nuovo e le collisioni, non scrive
  rinomina.py applica [file...]  riscrive i file (testo) — i percorsi li sposta git mv a parte

Un nome si traduce solo se contiene almeno una parola italiana «forte» (non ambigua con
l'inglese o con le sigle). Le parole deboli si traducono solo in compagnia di una forte.
"""
import json, os, re, subprocess, sys, collections

S = os.path.dirname(os.path.abspath(__file__))
ROOT = "/home/nicfio/Documenti/REMOTIX"

# ── il vocabolario ──────────────────────────────────────────────────────────
VOC = {}
for f in sorted(os.listdir(S)):
    if f.startswith("glossario-") and f.endswith(".tsv"):
        for riga in open(os.path.join(S, f)):
            it, en, nota = (riga.rstrip("\n").split("\t") + ["", ""])[:3]
            if it and en:
                VOC[it] = en
# correzioni a mano, vincono sul vocabolario: parola → inglese
if os.path.exists(os.path.join(S, "voc-correzioni.tsv")):
    for riga in open(os.path.join(S, "voc-correzioni.tsv")):
        if riga.strip() and not riga.startswith("#"):
            it, en = riga.rstrip("\n").split("\t")[:2]
            if en == "=":
                VOC.pop(it, None)
            else:
                VOC[it] = en

# Parole deboli: corte, o anche inglesi, o sigle note. Non bastano da sole.
DEBOLI = set("""
di il la da si va le ha al lo io ne se fa ma ci ed ad po li un su gr
del per via media come note piano solo pure metro regime male cure manifesto diverse confine finale
prime costa concede coincide unite residue confuse mandate morse computer deduce conclude decorative
opera grave tale crude terra alto largo viola nero rossi sole era vale vita otto salvo mira tara viva
sana sane una uno due tre prove mette dire dare stare cade padre eta sta est ore mil pan peg fond cas
tent salt ass imp luc par fam rap tit liv pil dip tel dis cal ric toll cons mis cong cart inn sal punt
rig ins ing fig pun dat mas tut prem flu rin ina tac rim quest prof lung cod tot fab lar det usc ist
camp reg bloc chi con dove vista fine data mente sei comprende darla hai farsi mondo ho ad lui sera
diverse cui mia mani dai sped nato grande fai mano alla dei mai casa ciao vive luc imp ma col cosa
dal viva bene ha primo mio verde dice qui che prima nome serve tutti massimo pronto gia gr sono della
dell ci regime pero sara inn sal dare punt
""".split()) - set("""
nome prima dice qui che primo mio verde tutti massimo pronto gia sono della dell dal col cosa bene
alla dei mai casa grande nato mano fai cui mia mani sera lui pero sara serve
""".split())
# ⇧ le seconde sono italiane anche se compaiono nelle liste inglesi: restano forti.

# Nomi che non si toccano mai (account veri sulle macchine di prova, sigle, terze parti).
INTOCCABILI = set()
if os.path.exists(os.path.join(S, "intoccabili.txt")):
    INTOCCABILI = {l.strip() for l in open(os.path.join(S, "intoccabili.txt")) if l.strip() and not l.startswith("#")}
# Sostituzioni a nome intero, vincono su tutto: vecchio → nuovo
INTERI = {}
if os.path.exists(os.path.join(S, "interi.tsv")):
    for riga in open(os.path.join(S, "interi.tsv")):
        if riga.strip() and not riga.startswith("#"):
            a, b = riga.rstrip("\n").split("\t")[:2]
            INTERI[a] = b

TOKEN = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*(?![A-Za-z0-9_])")
PARTE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+")


def forte(p):
    p = p.lower()
    return p in VOC and VOC[p] != p and p not in DEBOLI


def rendi(en, orig, camel_dopo):
    """La traduzione en (parole unite da _) nella forma della parte orig."""
    parole = en.split("_")
    if orig.isupper() and len(orig) > 1:
        return [w.upper() for w in parole], "_"
    if orig[0].isupper():
        return ["".join(w.capitalize() for w in parole)], ""
    if camel_dopo:
        return [parole[0] + "".join(w.capitalize() for w in parole[1:])], ""
    return parole, None


def traduci(tok):
    if tok in INTERI:
        return INTERI[tok]
    if tok in INTOCCABILI:
        return tok
    segmenti = re.split(r"([_-]+)", tok)
    parti = [PARTE.findall(s) for s in segmenti[::2]]
    if not any(forte(p) for ps in parti for p in ps):
        return tok
    out = []
    for i, s in enumerate(segmenti):
        if i % 2:
            out.append(s)
            continue
        ps = PARTE.findall(s)
        if "".join(ps) != s:          # caratteri strani: non ci si prova
            out.append(s)
            continue
        sep_ctx = "-" if "-" in tok and "_" not in tok else "_"
        nuovo = []
        for j, p in enumerate(ps):
            low = p.lower()
            if low in VOC and VOC[low] != low:
                en = VOC[low]
                if en == "-":
                    continue
                camel = len(ps) > 1 and not (p.isupper() and len(p) > 1)
                parole, giunto = rendi(en, p, camel and j > 0 or (camel and len(ps) > 1 and p[0].islower()))
                if giunto is None:
                    nuovo.append(sep_ctx.join(parole))
                elif giunto == "_":
                    nuovo.append((sep_ctx if sep_ctx == "-" else "_").join(parole))
                else:
                    nuovo.append(parole[0])
            else:
                nuovo.append(p)
        # tra parti MAIUSCOLE di un segmento serve il separatore (prima erano una parola sola)
        out.append("".join(nuovo))
    r = "".join(out)
    r = re.sub(r"([_-])\1+", r"\1", r)          # parti tolte lasciano separatori doppi
    r = re.sub(r"^[_-]+|[_-]+$", "", r) if not tok.startswith("_") else r
    if tok.startswith("_") and not r.startswith("_"):
        r = "_" + r
    if not r or r[0].isdigit():
        return tok
    # la prima lettera mantiene il caso dell'originale (Go: esportato o no)
    if tok[0].isupper() and r[0].islower():
        r = r[0].upper() + r[1:]
    if tok[0].islower() and r[0].isupper() and not r.isupper():
        r = r[0].lower() + r[1:]
    return r


def file_in_scope():
    tutti = subprocess.check_output(["git", "-C", ROOT, "ls-files"]).decode().split("\n")
    out = []
    for f in tutti:
        if not f or "/vendor/" in f or f.startswith(("misure/", "licenze/", "anteprime/", "memoria/")):
            continue
        if re.search(r"\.(png|jpg|jpeg|gif|webp|ico|wasm|gz|zst|pdf|xz|bin|ttf|woff2?|sha256)$", f):
            continue
        if f.startswith("src/protocolli/") or f.endswith("_spv.h") or f.endswith("go.sum"):
            continue
        out.append(f)
    return out


def main():
    cmd = sys.argv[1]
    files = sys.argv[2:] or file_in_scope()
    tabella = collections.Counter()
    esistenti = collections.Counter()
    for f in files:
        try:
            t = open(os.path.join(ROOT, f), encoding="utf-8").read()
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
        cambi = {}
        for m in TOKEN.finditer(t):
            tok = m.group(0)
            esistenti[tok] += 1
            n = traduci(tok)
            if n != tok:
                tabella[(tok, n)] += 1
                cambi[tok] = n
        if cmd == "applica" and cambi:
            t2 = TOKEN.sub(lambda m: cambi.get(m.group(0), m.group(0)), t)
            open(os.path.join(ROOT, f), "w", encoding="utf-8").write(t2)
    # collisioni
    verso = collections.defaultdict(set)
    for (a, b) in tabella:
        verso[b].add(a)
    rinominati = {a for a, _ in tabella}
    coll = {b: sorted(a) for b, a in verso.items() if len(a) > 1}
    contro = {b: sorted(verso[b]) for b in verso if b in esistenti and b not in rinominati}
    json.dump({"tabella": sorted([a, b, n] for (a, b), n in tabella.items()),
               "collisioni": coll, "contro_esistenti": contro},
              open(os.path.join(S, "piano.json"), "w"), ensure_ascii=False, indent=0)
    print(f"nomi da cambiare: {len(tabella)}  collisioni: {len(coll)}  contro nomi esistenti: {len(contro)}")


if __name__ == "__main__":
    main()
