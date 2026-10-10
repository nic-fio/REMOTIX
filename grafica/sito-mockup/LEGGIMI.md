# The site remotix.nicfio.it — mockup

A trial of the look, **not the site**: fake data (version, date, fingerprint of the `.run`), no real links. In
English (user, 9 Oct). The style is that of the product's sign-in page (`src/pagina.html`, class
`.accesso`), collected in `stile.css`.

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

It opens directly from disk: `xdg-open grafica/sito-mockup/index.html`.

## The page in a single file (10 Oct evening)

✅ User: *«rendi la landing page autocontenuta (con le immagini incorporate)»*. The source stays `index.html` +
`stile.css` + `icone/` (Simple Icons 13.21.0, local copies) + `schermate-vere/`; the file to publish is regenerated with

    python3 grafica/sito-mockup/autocontenuta.py                 # pubblica/index.html, with the «Mockup» ribbon
    python3 grafica/sito-mockup/autocontenuta.py --senza-nastro  # the one to put online

It inlines CSS, icons (SVG) and screenshots (WebP, at most 1600 px, quality 82): **~420 KB, no requests to
third parties** (no CDN or external fonts). The script refuses to write if a link to an external file remains.

## Online (10 Oct 2026, evening)

✅ User: *«ormai la homepage di remotix direi che è ok»* ⇒ published at **https://remotix.nicfio.it** (DNS A at
OVH, Caddy block with `~/Documenti/VPS/add-site.sh`, Let's Encrypt certificate). It is republished with

    python3 grafica/sito-mockup/autocontenuta.py --senza-nastro
    scp grafica/sito-mockup/pubblica/index.html progetti@57.131.27.241:/srv/www/remotix.nicfio.it/index.html

The button that pointed to the `.run` is «Coming soon» until the first release is in `/download/` on the VPS.
REMOTIX's card («Coming soon · Free») is on the nicfio.it homepage (`~/Documenti/VPS/sites/nicfio.it/holding`,
`publish.sh`). Contact: Zimbra alias `remotix@nicfio.it` → nicfio@nicfio.it.
