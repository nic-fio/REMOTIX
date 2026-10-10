# Il sito remotix.nicfio.it — mockup

Prova di veste, **non il sito**: dati finti (versione, data, impronta del `.run`), nessun collegamento vero. In
inglese (utente, 9 ott). Lo stile è quello della pagina d'accesso del prodotto (`src/pagina.html`, classe
`.accesso`), raccolto in `stile.css`.

✅ **10 ott 2026: REMOTIX è gratuito** (DECISIONI §10.33) ⇒ il sito è solo **file fissi** serviti da Caddy sulla
VPS, come gli altri siti (`~/Documenti/VPS`): niente accesso, area cliente, pannello né prezzi. Tolti
`signin.html`, `account.html`, `console.html` (restano nella storia di git, commit 91b7bc5).
✅ **Il `.run` si scarica dalla VPS** (utente, 10 ott): `remotix.nicfio.it/download/remotix-X.Y.Z-R.run` con
accanto il suo `.sha256`; il deposito GitHub resta privato.

| sezione di `index.html` | che cosa c'è |
|---|---|
| apertura | il desktop nel browser, «Free, for everyone», pulsante **Download** |
| How it works · Why | invariate dal 9 ott |
| Requirements | server: le sette distribuzioni dei pacchetti; chi si collega: il browser |
| **Download** | il `.run`, i due comandi (`check` e `sudo sh … .run`), l'impronta, le distribuzioni, i desktop |
| **License** | gratis per tutti, aziende comprese; cosa si può e cosa va chiesto (da `LICENSE.md`, ⏳ non ancora approvata) |
| FAQ | gratis anche per un'azienda? open source? chiama casa? cambia il sistema? |

⛔ Niente prestazioni nella vetrina: stanno nella documentazione tecnica (utente, 9 ott).

Si apre direttamente dal disco: `xdg-open grafica/sito-mockup/index.html`.
