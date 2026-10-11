# The 20 «premium» proposals for the sign-in page — the common contract

Direction chosen by the user (4 Oct 2026): **premium product** — the register of a polished commercial
product (Linear, Tailscale, Vercel), the real logo in evidence, a sober sign-in card.

Each proposal is ONE self-contained file `NN-nome.html` in this folder, and complies with:

1. **No external resources** (the server may be without Internet): no Google Fonts, no CDN,
   no external images. Fonts: `system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",Cantarell,Ubuntu,sans-serif`
   (monospace: `ui-monospace,"JetBrains Mono","DejaVu Sans Mono",monospace`).
2. **The logo** is `logo.svg` from this folder, copied INLINE (not `<img>`), with `currentColor`
   for «EMO» (white on the dark background, near-black `#0b1430` on the light one). The R mark alone
   (the three `<path>`, viewBox `0 0 442 356`) may be used as a graphic element. If the logo appears twice,
   the gradient ids must be made unique. Do not redraw it, do not change its colours.
3. **The IDs and the words stay those of the product**: `<form id="modulo">`, `<input id="utente">`
   (label «User», `autocomplete="username"`), `<input id="parola" type="password">`
   (label «Password», `autocomplete="current-password"`), `<button id="vai">Connect</button>`,
   `<div id="esito" role="status" aria-live="polite">`, `<div id="avviso">`, `<div id="dichiarazione">`.
   Motto (it may be shortened but not change meaning): «Your Linux desktop, from any browser».
   Footer: encrypted connection and the server's name (use `alfa.lan` as an example).
4. **The error state must be visible**: a small script does `preventDefault` on submit and
   shows in `#esito` «Invalid user or password.» in error style; opening the file with
   `?stato=errore` the error is already visible on opening.
5. **From the phone to 4K**: no horizontal scrolling at 360 px; at 3840×2160 the card grows
   (sizes in `em`, `font-size: clamp(16px, 0.42vw + 10px, 26px)` like the current page).
6. **Modest hardware** (integrated Intel UHD 730, and Android phones): animations ONLY on
   `transform`/`opacity`, slow and few; no canvas, WebGL or JavaScript loops; `backdrop-filter`
   only on small surfaces; `prefers-reduced-motion` turns everything off.
7. **Accessible**: text contrast ≥ 4.5:1, focus visible from the keyboard, `lang="en"`.
8. At the top of the file a comment like the old proposals:
   `<!-- Style: «Name» — one line on what you see. Idea: one line on why. -->`
9. `<title>REMOTIX — Sign in</title>`.

**Before delivering, look at it**: for each file
`firefox --headless --window-size 1600,900 --screenshot /percorso/NN.png file:///percorso/NN-nome.html`
and also at `390,844` (phone); open the images and fix what is wrong. The test images
do NOT stay in the folder (delete them, or put them in your temporary folder).
