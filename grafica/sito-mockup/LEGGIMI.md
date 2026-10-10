# Il sito remotix.nicfio.it — mockup

Prova di veste, **non il sito**: dati finti (versione, data, impronta del `.run`), nessun collegamento vero. In
inglese (utente, 9 ott). Lo stile è quello della pagina d'accesso del prodotto (`src/pagina.html`, classe
`.accesso`), raccolto in `stile.css`.

✅ **10 ott 2026: REMOTIX è gratuito** (DECISIONI §10.33) ⇒ il sito è solo **file fissi** serviti da Caddy sulla
VPS, come gli altri siti (`~/Documenti/VPS`): niente accesso, area cliente, pannello né prezzi. Tolti
`signin.html`, `account.html`, `console.html` (restano nella storia di git, commit 91b7bc5).
✅ **Il `.run` si scarica dalla VPS** (utente, 10 ott): `remotix.nicfio.it/download/remotix-X.Y.Z-R.run` con
accanto il suo `.sha256`.

✅ **10 ott sera, la forma scelta dall'utente**: un disegno suo (*«questo è quello che volevo, bisogna solo renderla
widescreen»*), costruito in HTML largo (contenuto fino a 1480 px). Corretti rispetto al disegno: «Open source» →
**«Source available»** (§10.33: non è open source per l'OSI); lo schema ha il browser sui dispositivi, non dopo il
server; tolto «files» (niente trasferimento di file); aggiunta AlmaLinux. ⚠ Loghi delle distribuzioni (Simple Icons):
marchi registrati, la politica di ciascuna va letta prima di pubblicare.

| sezione | che cosa c'è |
|---|---|
| apertura | «Connect to your Linux desktop from anywhere», schema dispositivi → cifrato → server REMOTIX ⟷ desktop nel browser, quattro punti |
| Use it anywhere | portatile, tablet e telefono con le schermate vere (`schermate/*.png`, in arrivo dal server) |
| How it works | tre passi: dispositivo con browser → REMOTIX sul server → il tuo desktop |
| Supported distributions | sei loghi e «Get started now» (Download, GitHub) |
| fascia finale | Personal use · Teams · Infrastructure |

⛔ Niente prestazioni nella vetrina: stanno nella documentazione tecnica (utente, 9 ott).

Si apre direttamente dal disco: `xdg-open grafica/sito-mockup/index.html`.

## La pagina in un file solo (10 ott sera)

✅ Utente: *«rendi la landing page autocontenuta (con le immagini incorporate)»*. Il sorgente resta `index.html` +
`stile.css` + `icone/` (Simple Icons 13.21.0, copie locali) + `schermate-vere/`; il file da pubblicare si rigenera con

    python3 grafica/sito-mockup/autocontenuta.py                 # pubblica/index.html, col nastro «Mockup»
    python3 grafica/sito-mockup/autocontenuta.py --senza-nastro  # quella da mettere online

Incorpora CSS, icone (SVG) e schermate (WebP, al massimo 1600 px, qualità 82): **~420 KB, nessuna richiesta a
terzi** (niente CDN né caratteri esterni). Lo script si rifiuta di scrivere se resta un collegamento a un file esterno.

## Online (10 ott 2026, sera)

✅ Utente: *«ormai la homepage di remotix direi che è ok»* ⇒ pubblicata su **https://remotix.nicfio.it** (DNS A su
OVH, blocco Caddy con `~/Documenti/VPS/add-site.sh`, certificato Let's Encrypt). Si ripubblica con

    python3 grafica/sito-mockup/autocontenuta.py --senza-nastro
    scp grafica/sito-mockup/pubblica/index.html progetti@57.131.27.241:/srv/www/remotix.nicfio.it/index.html

Il pulsante che puntava al `.run` è «Coming soon» finché il primo rilascio non sta in `/download/` sulla VPS.
La scheda di REMOTIX («Coming soon · Free») è nella homepage di nicfio.it (`~/Documenti/VPS/sites/nicfio.it/holding`,
`publish.sh`). Contatto: alias Zimbra `remotix@nicfio.it` → nicfio@nicfio.it.
