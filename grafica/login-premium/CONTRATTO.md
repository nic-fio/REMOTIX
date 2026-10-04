# Le 20 proposte «premium» della pagina d'accesso — il contratto comune

Direzione scelta dall'utente (4 ott 2026): **prodotto premium** — il registro di un prodotto
commerciale curato (Linear, Tailscale, Vercel), il logo vero in evidenza, scheda d'accesso sobria.

Ogni proposta è UN file `NN-nome.html` autonomo in questa cartella, e rispetta:

1. **Niente risorse esterne** (il server può essere senza Internet): niente Google Fonts, niente CDN,
   niente immagini esterne. Caratteri: `system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",Cantarell,Ubuntu,sans-serif`
   (monospace: `ui-monospace,"JetBrains Mono","DejaVu Sans Mono",monospace`).
2. **Il logo** è `logo.svg` di questa cartella, copiato INLINE (non `<img>`), con `currentColor`
   per «EMO» (bianco sul fondo scuro, quasi nero `#0b1430` sul chiaro). Si può usare il solo segno
   della R (i tre `<path>`, viewBox `0 0 442 356`) come elemento grafico. Se il logo compare due
   volte, gli id dei gradienti vanno resi unici. Non ridisegnarlo, non cambiarne i colori.
3. **Gli ID e le parole restano quelli del prodotto**: `<form id="modulo">`, `<input id="utente">`
   (etichetta «Utente», `autocomplete="username"`), `<input id="parola" type="password">`
   (etichetta «Parola d'ordine», `autocomplete="current-password"`), `<button id="vai">Collegati</button>`,
   `<div id="esito" role="status" aria-live="polite">`, `<div id="avviso">`, `<div id="dichiarazione">`.
   Motto (si può accorciare ma non cambiare senso): «Il tuo desktop Linux, da qualunque browser».
   Piede: connessione cifrata e il nome del server (usa `alfa.lan` come esempio).
4. **Lo stato d'errore si deve vedere**: un piccolo script fa `preventDefault` sull'invio e
   mostra in `#esito` «Utente o parola d'ordine non validi.» in stile errore; aprendo il file con
   `?stato=errore` l'errore è già visibile all'apertura.
5. **Dal telefono al 4K**: nessuno scorrimento orizzontale a 360 px; a 3840×2160 la scheda cresce
   (misure in `em`, `font-size: clamp(16px, 0.42vw + 10px, 26px)` come la pagina attuale).
6. **Ferro modesto** (Intel UHD 730 integrata, e telefoni Android): animazioni SOLO su
   `transform`/`opacity`, lente e poche; niente canvas, WebGL o cicli JavaScript; `backdrop-filter`
   solo su superfici piccole; `prefers-reduced-motion` spegne tutto.
7. **Accessibile**: contrasto del testo ≥ 4.5:1, fuoco visibile da tastiera, `lang="it"`.
8. In testa al file un commento come le vecchie proposte:
   `<!-- Stile: «Nome» — una riga su cosa si vede. Idea: una riga sul perché. -->`
9. `<title>REMOTIX — Accesso</title>`.

**Prima di consegnare, guardala**: per ogni file
`firefox --headless --window-size 1600,900 --screenshot /percorso/NN.png file:///percorso/NN-nome.html`
e anche a `390,844` (telefono); apri le immagini e correggi quel che non va. Le immagini di prova
NON restano nella cartella (cancellale, o mettile nella tua cartella temporanea).
