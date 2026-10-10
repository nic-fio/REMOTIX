#!/usr/bin/env python3
"""Builds the landing page as ONE self-contained file: pubblica/index.html.

    python3 grafica/sito-mockup/autocontenuta.py [--senza-nastro]

From index.html (the editable source) it inlines stile.css, the icons in icone/ (SVG as data URIs)
and the screenshots in schermate-vere/ (converted to WebP, resized to what the page shows).
The result makes no request to anyone: no CDN, no fonts, nothing but the file itself.
--senza-nastro drops the red «Mockup» ribbon, for the published version.
"""
import base64, io, re, sys
from pathlib import Path
from PIL import Image

QUI = Path(__file__).resolve().parent
USCITA = QUI / "pubblica" / "index.html"
LARGHEZZA_MAX = 1600     # the widest screen on the page is ~1000 CSS px: 1600 covers a 1.6x display
QUALITA_WEBP = 82


def svg_data(percorso):
    testo = (QUI / percorso).read_text()
    return "data:image/svg+xml;base64," + base64.b64encode(testo.encode()).decode()


def webp_data(percorso):
    im = Image.open(QUI / percorso).convert("RGB")
    if im.width > LARGHEZZA_MAX:
        im = im.resize((LARGHEZZA_MAX, round(im.height * LARGHEZZA_MAX / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=QUALITA_WEBP, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    pagina = (QUI / "index.html").read_text()
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

    pagina = pagina.replace('href="index.html"', 'href="/"')   # the logo goes home, wherever the file is served

    if "--senza-nastro" in sys.argv:
        pagina = pagina.replace('<div class="nastro">Mockup</div>\n', "")

    rimasti = re.findall(r"(?:src=\"|url\(|href=\")(?!data:|#|%23|/\"|https://github\.com|mailto:|download/)([^\"')]+)", pagina)
    rimasti = [r for r in rimasti if not r.startswith("https://github.com")]
    if rimasti:
        sys.exit("still pointing outside the file: " + ", ".join(sorted(set(rimasti))))

    USCITA.parent.mkdir(exist_ok=True)
    USCITA.write_text(pagina)
    print(f"{USCITA.relative_to(QUI.parent.parent)}: {USCITA.stat().st_size / 1024:.0f} KB, "
          f"{len(cache)} files inlined")


if __name__ == "__main__":
    main()
