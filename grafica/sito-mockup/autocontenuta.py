#!/usr/bin/env python3
"""Builds the site as self-contained files in pubblica/: the pages and a copy of the manuals.

    python3 grafica/sito-mockup/autocontenuta.py

From each page (index.html, performance.html, docs.html: the editable sources) it inlines stile.css,
the icons in icone/ (SVG as data URIs) and the screenshots in schermate-vere/ (converted to WebP,
resized to what the page shows). The result makes no request to anyone: no CDN, no fonts, nothing but
the file itself. Links between pages stay links, to the site's own paths (/, /performance.html, ...).

The manuals made by docs/sources/build.py (already self-contained) are copied to pubblica/docs/ under
the names the site serves; the versions shown on docs.html are read from them.

Before writing anything it checks every link inside the site: each one must reach a page or manual that
is being published, and an anchor must exist in it. It refuses to write if a link to an external file
remains, or if a link leads nowhere.
"""
import base64, io, re, sys
from pathlib import Path
from PIL import Image

QUI = Path(__file__).resolve().parent
RADICE = QUI.parent.parent
PUBBLICA = QUI / "pubblica"
PAGINE = ["index.html", "performance.html", "docs.html"]   # each becomes pubblica/<same name>
# the manuals: file in docs/ -> name served at /docs/
MANUALI = {"User Manual.html": "user-manual.html", "Technical Manual.html": "technical-manual.html"}
# the chapters the pages point to by number: if build.py renumbers them, the link must not silently go elsewhere
CAPITOLI = {("user-manual.html", "ch2"): "Installing the server",
            ("technical-manual.html", "ch18"): "Performance and capacity"}
MAX_WIDTH = 1600     # the widest screen on the page is ~1000 CSS px: 1600 covers a 1.6x display
WEBP_QUALITY = 82


def svg_data(percorso):
    testo = (QUI / percorso).read_text()
    return "data:image/svg+xml;base64," + base64.b64encode(testo.encode()).decode()


def webp_data(percorso):
    im = Image.open(QUI / percorso).convert("RGB")
    if im.width > MAX_WIDTH:
        im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=WEBP_QUALITY, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def versione(testo):
    m = re.search(r"Version</span><b>([^<]+)</b>", testo)
    return m.group(1) if m else sys.exit("no version in a manual: was it made by docs/sources/build.py?")


def costruisci(nome, manuali):
    pagina = (QUI / nome).read_text()
    stile = (QUI / "stile.css").read_text()
    pagina = pagina.replace('<link rel="stylesheet" href="stile.css">', "<style>\n" + stile + "</style>")

    # the same image used twice is encoded once per use: the screens are few, simplicity wins
    cache = {}
    def sostituisci(m):
        p = m.group(1)
        if p not in cache:
            cache[p] = svg_data(p) if p.endswith(".svg") else webp_data(p)
        return cache[p]
    pagina = re.sub(r"(?<=src=\")((?:schermate-vere|icone)/[^\"]+)(?=\")", sostituisci, pagina)
    pagina = re.sub(r"(?<=url\()((?:schermate-vere|icone)/[^)]+)(?=\))", sostituisci, pagina)

    # the sources link each other as files on disk; online they are the site's paths
    pagina = pagina.replace('href="index.html"', 'href="/"')   # the logo goes home, wherever the file is served
    pagina = pagina.replace('href="index.html#', 'href="/#')
    for p in PAGINE[1:]:
        pagina = pagina.replace(f'href="{p}', f'href="/{p}')
    for sorgente, servito in MANUALI.items():
        pagina = pagina.replace('href="../../docs/' + sorgente.replace(" ", "%20"), f'href="/docs/{servito}')
    # docs.html shows each manual's version as written in the manual itself
    pagina = re.sub(r'(<b data-versione="(\w+)">)[^<]*(</b>)',
                    lambda m: m.group(1) + manuali[m.group(2) + "-manual.html"][1] + m.group(3), pagina)

    rimasti = re.findall(r"(?:src=\"|url\(|href=\")(?!data:|#|%23|/\"|/#|/[\w-]+\.html|/docs/[\w-]+\.html|https://github\.com/|mailto:|download/)([^\"')]+)", pagina)
    if rimasti:
        sys.exit(f"{nome}: still pointing outside the file: " + ", ".join(sorted(set(rimasti))))
    return pagina, len(cache)


def controlla_link(sito):
    """sito: served path -> text. Every href inside the site must reach a file of `sito` and an id in it."""
    ids = {p: set(re.findall(r'\bid="([^"]+)"', t)) for p, t in sito.items()}
    errori = []
    for p, t in sito.items():
        if p.startswith("docs/"):
            continue   # the manuals' own links are checked by build.py --check
        for href in re.findall(r'href="([^"]*)"', t):
            if re.match(r"(https://|mailto:|data:|download/)", href):
                continue
            percorso, _, ancora = href.partition("#")
            if href == "#" or (not percorso and not ancora):
                errori.append(f"{p}: empty link «{href}»")
                continue
            dest = p if not percorso else ("index.html" if percorso == "/" else percorso.lstrip("/"))
            if dest not in sito:
                errori.append(f"{p}: {href} → no such page")
            elif ancora and ancora not in ids[dest]:
                errori.append(f"{p}: {href} → no id «{ancora}» in {dest}")
    for (servito, ancora), titolo in CAPITOLI.items():
        if not re.search(rf'id="{ancora}"><div class="ch-head"><span class="ch-kick">[^<]*</span><h2 class="h-ch">{re.escape(titolo)}<', sito["docs/" + servito]):
            errori.append(f"docs/{servito}#{ancora} is no longer «{titolo}»: update the links and CAPITOLI")
    if errori:
        sys.exit("broken links, nothing written:\n  " + "\n  ".join(errori))
    return sum(len(re.findall(r'href="', t)) for p, t in sito.items() if not p.startswith("docs/"))


def main():
    manuali = {}
    for sorgente, servito in MANUALI.items():
        testo = (RADICE / "docs" / sorgente).read_text()
        if re.search(r'(?:src="|url\(["\']?|<link[^>]*href=")(?:https?:)?//', testo):
            sys.exit(f"docs/{sorgente} loads an external file: it is no longer self-contained")
        manuali[servito] = (testo, versione(testo))
    sito = {"docs/" + s: t for s, (t, _) in manuali.items()}
    inline = {}
    for nome in PAGINE:
        sito[nome], inline[nome] = costruisci(nome, manuali)
    n = controlla_link(sito)

    (PUBBLICA / "docs").mkdir(parents=True, exist_ok=True)
    for percorso, testo in sito.items():
        uscita = PUBBLICA / percorso
        uscita.write_text(testo)
        extra = f", {inline[percorso]} files inlined" if percorso in inline else ""
        print(f"{uscita.relative_to(RADICE)}: {uscita.stat().st_size / 1024:.0f} KB{extra}")
    print(f"{n} links checked, all reach a page and an anchor")


if __name__ == "__main__":
    main()
