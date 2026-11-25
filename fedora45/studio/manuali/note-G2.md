# Note G2 — capitoli ch06–ch11 del manuale tecnico di Fedora 45 (25 nov 2026)

Stato: i sei file compilano; il controllo del generatore, lanciato sui soli capitoli (ch23_map saltato, perché ancora di Ubuntu), non protesta più su nulla dei miei file. `python3 build.py --check` vero si ferma alla mappa dei file (atteso).

## Titoli di sezione cambiati, aggiunti, tolti

- ch06: «KDE: the KWin screencast protocol and the nested KWin» → «KDE: the KWin screencast protocol and KWin alone» (obbligatorio). I tre `rif()` (ch06, ch10 ×2) sono già aggiornati; nessun altro capitolo lo cita oggi (controllato).
- ch06: AGGIUNTA «KWin alone: resizing its output» (subito dopo la sezione KDE). Gli altri capitoli la possono citare con `rif("KWin alone: resizing its output")`; io lo faccio da ch09 e ch10.
- ch07: AGGIUNTA «Requirements: video drivers on Fedora» (seconda sezione, dopo «Encoding at a glance…»; l'ho messa seconda e non prima per non spostare la panoramica). Il manuale utente (altro gruppo) deve dire le stesse cose dei pacchetti RPM Fusion.
- Nessun'altra sezione rinominata né tolta. Il titolo di ch10 «What was verified for input and what was not» è invariato.

## I tre punti più importanti

1. **Conteggio delle strade verso 0x0E**: la pagina (`page.html`, identica a Ubuntu) ne dichiara SEI nel suo commento; fuori da quel conto ora ce ne sono CINQUE (prima quattro): precedente desktop che chiude, logind che non sa dire, nascita fallita, scala diversa da 1 non riparabile, e (nuova, solo KDE) KWin senza `kde_output_management_v2` ≥ 22 (`kde_refused`, che passa dalla strada `scale_refused`). Scritto così in ch08 («Admission») e ch09 («End of session in the page»). Chi scrive ch02/ch05/ch03 e cita «quattro/sei strade» deve allinearsi.
2. **Cifre di prova**: tutte quelle di Ubuntu (116/124, 123/124, `unione*`, Chrome 156, Firefox 153.7…) sono state tolte. Ho usato solo: giro h1 del 23 nov (F35: GNOME 52 PASS con 1 FAIL noto + 39 PASS nel resto di `all.sh`; KDE 76; XFCE 60; LXQt 60; `check-base`+`check-input` 31/0 sui quattro, F34), `check-kde-resize` 10/10, `check-kde-live` 8/8, `check-resize` 10/10, `check-audio` 1/1 e `check-clipboard` 2/2 su XFCE e LXQt (F22), sonda KWin I1–I9 (`studio/5-kde-progetto.md`), prove a mano del proprietario 21–23 nov e le tre prove con chiavetta LIVE del 25 nov. «GNOME 52 PASS» l'ho letto come «52 prove passate»: da confermare con il registro (F35) se si vuole la cifra esatta.
3. **Cose scritte come «non verificato su Fedora»** (elenco sotto): non le ho asserite.

## Punti non verificati dichiarati nei capitoli

- Se il «frame perso» di KWin si presenta ancora con KWin 6.8 `--virtual` e PipeWire 1.6.9 (ch06).
- Diff del sorgente di Mutter 51.1 (formati, `DEFAULT_SIZE`, `SetKeymap`, schema dconf, interfacce D-Bus) (ch06, ch07, ch10).
- Formato di cattura di labwc 0.20.2 (XBGR8888?), sonda del cursore su 0.20.2, scorciatoie di labwc con XFCE completo (ch06, ch10).
- Più schede grafiche con KWin (F12), modificatori DMA-BUF di KWin su RADV, ingresso EIS di KWin dopo il cambio di misura (solo indirettamente), forma del cursore dopo un cambio (ch06).
- Hang amdgpu con slab su Fedora (ch06 «Slabs»).
- Come `render_grant.c` tratta un nodo `renderD*` 0666 senza ACL; rotta VA-API di AMD; Intel col prodotto sulle VM (la chiavetta LIVE ha codificato sulla Intel ma la rotta non è registrata); NVIDIA (ch07).
- Rifiuto dello `%pre` su una macchina senza scheda (non provato su Fedora) (ch07).
- Misura delle sette stringhe HEVC con Firefox 158/Chromium 157; Google Chrome su Fedora; telefono reale; DeX; Safari (ch09, ch10, ch11).
- Tempi di nascita di una sessione grafica e del Log Out su Fedora (le cifre di Ubuntu sono state tolte, ch09).
- Avviso «internal error» di WirePlumber e riga «FIFO NOT OBTAINED» su Fedora; Klipper su Plasma (ch11).
- Ctrl+Alt+Del su KDE provato a mano su Fedora (ch10).

## Difetti o residui del SORGENTE (non toccati, non descritti come funzioni)

- `src/kwin.c` ~riga 588: il commento di `kwin_poke()` cita ancora «the ticker sends to labwc»; il ticker è codice morto.
- `src/kwin.c`: codice labwc-per-KDE ancora presente ma non chiamato (`kwin_nested_alive()`, `kwin_host_*`, `ticker_*`, `HOST_RC`, `HOST_MHZ`, `TICKER_MS`, `HOST_BIRTH_MS`); `src/Makefile` definisce ancora `-DREMOTIX_LABWC`. Nel manuale c'è una sola frase che lo dice (ch06, «KDE…»).
- `src/opus-wasm/build.sh` costruisce il decoder in un contenitore podman (ordine del proprietario: niente podman per il banco). Nel manuale è detto che il pacchetto non lo esegue (il decoder è già dentro `page.html`); la parola «podman» non compare più, resta «container».
- `fedora45/THIRD-PARTY-LICENSES` righe ~1252 e ~1603 citano ancora il labwc nostro (già segnalato dall'inventario).
- Commento sopra `test_exits()` in `child.c` (`hevc_strada`/`h264_strada` contro `hevc_route`/`h264_route`): ereditato, già annotato nel manuale.
- `session.c:688-690` ecc.: il commento di `card_node()` parla ancora di BIOS primary card per labwc; per KDE nessuna scelta (scritto nel manuale).

## Altre note

- I file `__pycache__/` creati da `py_compile` in `fedora45/manuals/sources/technical-fedora45/` sono untracked: li cancella chi vuole (io non cancello nulla).
- Costanti ricontate con `grep` su `fedora45/src/`: tutti i valori delle tabelle di ch06 (costanti di cattura), ch07 (costanti del codificatore) e `unchanged.h` coincidono con il codice; i file `capture.c`, `encoder.c`, `rcp.c`, `hsrate.h`, `msgrate.h`, `linebudget.h`, `dimcheck.h`, `unchanged.h`, `page.c` sono `cmp`-uguali a Ubuntu, `transport.c` ha gli stessi `#define`. Tolte le righe di tabella `HOST_MHZ`, `TICKER_MS`, `HOST_BIRTH_MS`, `REMOTIX_LABWC` (codice morto). `page.html`: 14 326 righe, 941 549 byte (contati).
- ch07 «Choosing the card…»: ho aggiunto un paragrafo «KDE» (nessuna scelta di scheda) e uno «On Fedora 45 there is usually nothing to grant» (nodo 0666, gruppo `render` vuoto).
- Le citazioni a «DECISIONS.md», «SPECS.md», «LESSONS.md», «DECISIONS-11.md» restano come in Ubuntu: i file esistono in `fedora45/docs/` (ereditati), ma il loro contenuto non l'ho riletto per Fedora.
