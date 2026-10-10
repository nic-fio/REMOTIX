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

HERE = Path(__file__).resolve().parent
PAGES = ["index.html", "performance.html"]   # each becomes pubblica/<same name>
MAX_WIDTH = 1600     # the widest screen on the page is ~1000 CSS px: 1600 covers a 1.6x display
WEBP_QUALITY = 82


def svg_data(fpath):
    body_text = (HERE / fpath).read_text()
    return "data:image/svg+xml;base64," + base64.b64encode(body_text.encode()).decode()


def webp_data(fpath):
    im = Image.open(HERE / fpath).convert("RGB")
    if im.width > MAX_WIDTH:
        im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=WEBP_QUALITY, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def build(label_name):
    OUTPUT = HERE / "pubblica" / label_name
    page_v = (HERE / label_name).read_text()
    style = (HERE / "stile.css").read_text()
    page_v = page_v.replace('<link rel="stylesheet" href="stile.css">', "<style>\n" + style + "</style>")

    # the same image used twice is encoded once per use: the screens are few, simplicity wins
    cache = {}
    def replace(m):
        p = m.group(1)
        if p not in cache:
            cache[p] = svg_data(p) if p.endswith(".svg") else webp_data(p)
        return cache[p]
    page_v = re.sub(r"(?<=src=\")((?:schermate-vere|icons)/[^\"]+)(?=\")", replace, page_v)
    page_v = re.sub(r"(?<=url\()((?:schermate-vere|icons)/[^)]+)(?=\))", replace, page_v)

    page_v = page_v.replace('href="index.html"', 'href="/"')   # the logo goes home, wherever the file is served
    page_v = page_v.replace('href="index.html#', 'href="/#').replace('href="performance.html"', 'href="/performance.html"')

    if "--senza-nastro" in sys.argv:
        page_v = page_v.replace('<div class="nastro">Mockup</div>\n', "")

    remaining = re.findall(r"(?:src=\"|url\(|href=\")(?!data:|#|%23|/\"|/#|/performance\.html|https://github\.com|mailto:|download/)([^\"')]+)", page_v)
    remaining = [r for r in remaining if not r.startswith("https://github.com")]
    if remaining:
        sys.exit("still pointing outside the file: " + ", ".join(sorted(set(remaining))))

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(page_v)
    print(f"{OUTPUT.relative_to(HERE.parent.parent)}: {OUTPUT.stat().st_size / 1024:.0f} KB, "
          f"{len(cache)} files inlined")


def main():
    for label_name in PAGES:
        build(label_name)


if __name__ == "__main__":
    main()
