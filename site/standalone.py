#!/usr/bin/env python3
"""Builds the site as self-contained files in out/: the pages and a copy of the manuals.

    python3 site/standalone.py

Every *.html in this folder is a page (editable source): index.html is the home, docs.html the manuals, and one
page per distribution (debian13.html and ubuntu2604.html today). From each page it inlines style.css, the icons in icons/ (SVG as data
URIs) and the screenshots in screenshots/ (converted to WebP). The result makes no request to anyone.

Links between pages are RELATIVE (index.html, debian13.html, docs/user-manual-debian13.html): the output opens from
disk and works the same when served. The manuals (one User Manual and one Technical Manual for each distribution,
made elsewhere and read-only here) are copied to out/docs/ under the names in MANUALI. Each distribution's manuals are
read from its own folder: "manuals_dir" in distributions.json (relative to this folder), by default ../manuals.
The old address docs/user-manual.html (the single User Manual) is kept as a small page that points to docs.html.

ADDING A DISTRIBUTION = (1) a new page <slug>.html (copy debian13.html), (2) one entry in distributions.json (name,
icon, colour, its two manuals and, if they are not in ../manuals, "manuals_dir"). The card in index.html, the footer
links and the pair of manuals in docs.html are generated from that entry. Nothing else, no other page changes.

Before writing anything it checks every link inside the site (page and anchor) and refuses to write if a link to an
external file remains. The one exception: a plain link (href, never src or url) to the project on GitHub,
https://github.com/nic-fio/REMOTIX/… — a link the reader may click, not a request the page makes.
"""
import base64, html, io, json, re, sys
from pathlib import Path
from PIL import Image

QUI = Path(__file__).resolve().parent
RADICE = QUI.parent
USCITA = QUI / "out"
PAGINE = sorted(p.name for p in QUI.glob("*.html"))
# THE single list of available distributions: distributions.json. Cards, home text, footers and the documentation page
# are all generated from it, so they can never disagree. Only distributions that exist are listed there.
DISTRIBUZIONI = json.loads((QUI / "distributions.json").read_text())
# served name -> file to read; each manual comes from the "manuals_dir" of its distribution
MANUALI = {}
for d in DISTRIBUZIONI:
    cartella = (QUI / d.get("manuals_dir", "../manuals")).resolve()
    MANUALI["docs/" + d["user_manual_served"]] = cartella / d["user_manual"]
    MANUALI["docs/" + d["technical_manual_served"]] = cartella / d["technical_manual"]
# the old single User Manual address: a small self-contained page
VECCHIO_MANUALE = "docs/user-manual.html"
PAGINA_VECCHIA = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>REMOTIX — User Manuals</title></head>
<body style="font-family:system-ui,sans-serif;max-width:40em;margin:3rem auto;padding:0 1.2rem;line-height:1.6">
<h1>The User Manuals are now one for each distribution</h1>
<p>REMOTIX is made separately for each distribution, so each one has its own User Manual and its own Technical Manual.</p>
<p><a href="../docs.html">Choose the manuals of your distribution</a></p>
</body></html>
"""
MAX_WIDTH = 1600
WEBP_QUALITY = 82


def svg_data(percorso):
    return "data:image/svg+xml;base64," + base64.b64encode((QUI / percorso).read_bytes()).decode()


def webp_data(percorso):
    im = Image.open(QUI / percorso).convert("RGB")
    if im.width > MAX_WIDTH:
        im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=WEBP_QUALITY, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def elenco(nomi):
    return nomi[0] if len(nomi) == 1 else ", ".join(nomi[:-1]) + " and " + nomi[-1]


def segnaposto():
    nomi = [d["short"] for d in DISTRIBUZIONI]
    carte = "\n".join(
        f'''        <a class="distro-scheda" href="{d["slug"]}.html">
          <i class="d-logo" style="--c:{d["color"]};--m:url({d["icon"]})"></i>
          <div><h3>{html.escape(d["name"])}</h3>
            <p>REMOTIX {d["version"]} · {html.escape(d["how"])}</p>
            <p class="d-de">{html.escape(d["desktops"])}</p></div>
          <span class="pulsante primario">Open the {html.escape(d["short"])} page</span>
        </a>''' for d in DISTRIBUZIONI)
    coppie = "\n".join(
        f'''      <div class="distro-m" id="manuals-{d["slug"]}">
        <h2 class="titolo-d">{html.escape(d["name"])} · REMOTIX {d["version"]}</h2>
        <div class="manuali">
          <article class="manuale">
            <p class="occhiello">For everyone</p>
            <h2>User Manual — {html.escape(d["short"])}</h2>
            <p>What REMOTIX is, how to install it on {html.escape(d["short"])}, how to connect and how to use it.</p>
            <div class="dati"><a class="pulsante primario" href="docs/{d["user_manual_served"]}">Read the User Manual</a></div>
          </article>
          <article class="manuale">
            <p class="occhiello">For the curious and the technical</p>
            <h2>Technical Manual — {html.escape(d["short"])}</h2>
            <p>How REMOTIX works inside on {html.escape(d["short"])}: architecture, transport, encoding, security.</p>
            <div class="dati"><a class="pulsante secondario" href="docs/{d["technical_manual_served"]}">Read the Technical Manual</a></div>
          </article>
        </div>
      </div>''' for d in DISTRIBUZIONI)
    return {"{{AVAILABLE}}": f"REMOTIX is available for {elenco(nomi)}.", "{{NAMES}}": elenco(nomi),
            "{{CARDS}}": carte, "{{MANUAL_PAIRS}}": coppie,
            "{{FOOTER_LINKS}}": "".join(f'<a href="{d["slug"]}.html">{html.escape(d["short"])}</a>' for d in DISTRIBUZIONI)}


def costruisci(nome):
    pagina = (QUI / nome).read_text()
    for k, v in segnaposto().items():
        pagina = pagina.replace(k, v)
    assert "{{" not in pagina, f"{nome}: unresolved placeholder"
    stile = (QUI / "style.css").read_text()
    pagina = pagina.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + stile + "</style>")
    cache = {}
    def sostituisci(m):
        p = m.group(1)
        if p not in cache:
            cache[p] = svg_data(p) if p.endswith(".svg") else webp_data(p)
        return cache[p]
    pagina = re.sub(r"(?<=src=\")((?:screenshots|icons)/[^\"]+)(?=\")", sostituisci, pagina)
    pagina = re.sub(r"(?<=url\()((?:screenshots|icons)/[^)]+)(?=\))", sostituisci, pagina)
    rimasti = re.findall(r"(?:src=\"|url\(|href=\"(?!https://github\.com/nic-fio/REMOTIX/))(?!data:|#|%23|[\w-]+\.html|docs/[\w-]+\.html|mailto:|download/)([^\"')]+)", pagina)
    if rimasti:
        sys.exit(f"{nome}: still pointing outside the file: " + ", ".join(sorted(set(rimasti))))
    return pagina


def controlla_link(sito):
    ids = {p: set(re.findall(r'\bid="([^"]+)"', t)) for p, t in sito.items()}
    errori = []
    for p, t in sito.items():
        if p.startswith("docs/"):
            continue
        for href in re.findall(r'href="([^"]*)"', t):
            if re.match(r"(https://|mailto:|data:|download/)", href):
                continue
            percorso, _, ancora = href.partition("#")
            if href == "#" or (not percorso and not ancora):
                errori.append(f"{p}: empty link «{href}»")
                continue
            dest = p if not percorso else percorso
            if dest not in sito:
                errori.append(f"{p}: {href} → no such page")
            elif ancora and ancora not in ids[dest]:
                errori.append(f"{p}: {href} → no id «{ancora}» in {dest}")
    if errori:
        sys.exit("broken links, nothing written:\n  " + "\n  ".join(errori))
    return sum(len(re.findall(r'href="', t)) for p, t in sito.items() if not p.startswith("docs/"))


def main():
    sito = {}
    for servito, f in MANUALI.items():
        if not f.exists():
            sys.exit(f"manual missing: {f}")
        testo = f.read_text()
        if re.search(r'(?:src="|url\(["\']?|<link[^>]*href=")(?:https?:)?//', testo):
            print(f"WARNING: {f.name} loads an external file: not self-contained")
        sito[servito] = testo
    sito[VECCHIO_MANUALE] = PAGINA_VECCHIA
    for nome in PAGINE:
        sito[nome] = costruisci(nome)
    n = controlla_link(sito)
    (USCITA / "docs").mkdir(parents=True, exist_ok=True)
    for percorso, testo in sito.items():
        u = USCITA / percorso
        u.write_text(testo)
        print(f"{u.relative_to(RADICE)}: {u.stat().st_size / 1024:.0f} KB")
    print(f"{n} links checked, all reach a page and an anchor")


if __name__ == "__main__":
    main()
