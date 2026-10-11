# The site remotix.nicfio.it — mockup

A trial of the look, **not the site**: fake data (version, date, fingerprint of the `.run`), no real links. In
English (user, 9 Oct). The style is that of the product's sign-in page (`src/page.html`, class
`.accesso`), collected in `style.css`.

✅ **10 Oct 2026: REMOTIX is free of charge** (DECISIONI §10.33) ⇒ the site is only **static files** served by Caddy on the
VPS, like the other sites (`~/Documenti/VPS`): no sign-in, customer area, panel or prices. Removed
`signin.html`, `account.html`, `console.html` (they remain in git history, commit 91b7bc5).
✅ **The `.run` is downloaded from the VPS** (user, 10 Oct): `remotix.nicfio.it/download/remotix-X.Y.Z-R.run` with
its `.sha256` beside it.

✅ **10 Oct evening, the form chosen by the user**: a drawing of his own (*«questo è quello che volevo, bisogna solo renderla
widescreen»*), built in wide HTML (content up to 1480 px). Corrected with respect to the drawing: «Open source» →
**«Source available»** (§10.33: it is not open source by the OSI's definition); the diagram has the browser on the devices, not after the
server; removed «files» (no file transfer); added AlmaLinux. ⚠ Distribution logos (Simple Icons):
registered trademarks, each one's policy must be read before publishing.

| section | what is there |
|---|---|
| opening | «Connect to your Linux desktop from anywhere», diagram devices → encrypted → REMOTIX server ⟷ desktop in the browser, four points |
| Use it anywhere | laptop, tablet and phone with the real screenshots (`schermate/*.png`, coming from the server) |
| How it works | three steps: device with browser → REMOTIX on the server → your desktop |
| Supported distributions | six logos and «Get started now» (Download, GitHub) |
| final band | Personal use · Teams · Infrastructure |

⛔ No performance in the showcase: it belongs in the technical documentation (user, 9 Oct).

It opens directly from disk: `xdg-open design/site-mockup/index.html`.

## The page in a single file (10 Oct evening)

✅ User: *«rendi la landing page autocontenuta (con le immagini incorporate)»*. The source stays `index.html` +
`style.css` + `icons/` (Simple Icons 13.21.0, local copies) + `screenshots/`; the files to publish are regenerated with

    python3 design/site-mockup/standalone.py

(11 Oct: the red «Mockup» ribbon and the `--no-ribbon` option are gone — the user removed it from the published pages.) It inlines CSS, icons (SVG) and screenshots (WebP, at most 1600 px, quality 82): **~420 KB, no requests to
third parties** (no CDN or external fonts). The script refuses to write if a link to an external file remains, and if a link inside the site does not reach an
existing page and anchor (`href="#"` included).

## Online (10 Oct 2026, evening)

✅ User: *«ormai la homepage di remotix direi che è ok»* ⇒ published at **https://remotix.nicfio.it** (DNS A at
OVH, Caddy block with `~/Documenti/VPS/add-site.sh`, Let's Encrypt certificate). It is republished, with the release, with the commands in «Republishing» below.

The button that pointed to the `.run` was «Coming soon» until the first release; since 1.0.0 (11 Oct 2026) it is
«Download 1.0.0» → `download/remotix-1.0.0-1.run`, with «SHA-256» → `download/remotix-1.0.0-1.run.sha256` beside it
(relative links: `standalone.py` lets `download/` through without looking for it). At every release: change the two
names in `index.html`, and copy the `.run` and its `.sha256` to `/srv/www/remotix.nicfio.it/download/`.
REMOTIX's card («Coming soon · Free») is on the nicfio.it homepage (`~/Documenti/VPS/sites/nicfio.it/holding`,
`publish.sh`). Contact: Zimbra alias `remotix@nicfio.it` → nicfio@nicfio.it.

## The manuals on the site (11 Oct 2026)

The «Docs» link leads to **`docs.html`**: a light page, the same style as `performance.html`, with the two manuals —
the **User Manual** first (what REMOTIX is, how to install it), then the **Technical Manual** (how it works inside), each
with one line and the version, read from the manual itself at generation. The manuals are the self-contained files made
by `docs/sources/build.py`; `standalone.py` copies them to `public/docs/` with the names the site serves:

| in the repository | on the site |
|---|---|
| `docs/User Manual.html` | `/docs/user-manual.html` |
| `docs/Technical Manual.html` | `/docs/technical-manual.html` |

The copies are not in git (`.gitignore`): they are byte-for-byte the manuals, remade at every run. Other links: on the
home page «Get started now» has «Installation guide» → `/docs/user-manual.html#ch2`; on `performance.html` «the
technical manual, chapter Performance and capacity» → `/docs/technical-manual.html#ch18`; the footers have «Docs». The
chapters are linked by number: if `build.py` renumbers them, `standalone.py` stops (table `CAPITOLI`). The «FAQ»
entry was removed: there is no FAQ content.

## Republishing

Commands only, to be run with the release (the manuals first, so that the site copies the new ones):

    python3 docs/sources/build.py
    python3 design/site-mockup/standalone.py
    ssh progetti@57.131.27.241 mkdir -p /srv/www/remotix.nicfio.it/docs
    scp design/site-mockup/public/index.html design/site-mockup/public/performance.html \
        design/site-mockup/public/docs.html progetti@57.131.27.241:/srv/www/remotix.nicfio.it/
    scp design/site-mockup/public/docs/user-manual.html design/site-mockup/public/docs/technical-manual.html \
        progetti@57.131.27.241:/srv/www/remotix.nicfio.it/docs/
    ssh progetti@57.131.27.241 mkdir -p /srv/www/remotix.nicfio.it/download
    scp costruzione-uscita/rilasci/remotix-1.0.0-1.run costruzione-uscita/rilasci/remotix-1.0.0-1.run.sha256 \
        costruzione-uscita/rilasci/remotix-1.0.0-1-labwc-source.tar.gz \
        costruzione-uscita/rilasci/remotix-1.0.0-1-labwc-source.tar.gz.sha256 \
        progetti@57.131.27.241:/srv/www/remotix.nicfio.it/download/
