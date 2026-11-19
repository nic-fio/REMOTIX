# Studio 10 — Controprova: KWin 6.6.7 su Kubuntu ha bisogno del labwc proprio? (18 nov 2026, agente `kde`)

Esperimento sul box `rxu-kde` (Kubuntu 26.04, KWin 6.6.7, labwc di Ubuntu 0.9.3 / wlroots 0.19.2), pacchetto della copia `kde` installato.
Nessun codice né pacchetto modificato: solo strumenti di prova sul server. File di prova (solo sul server, non nell'albero):
`/media/REMOTIX-UBUNTU/lavoro/kde/prove-ub/kde-live.py`, `kde-exp.py` (+ uscite `lavoro/kde/expB2-ours.out`, `expB2-ubuntu.out`, istantanee in `prove-ub/shots/exp-*`).

## Conclusione (in una riga)
**Il difetto SI RIPRODUCE col labwc di Ubuntu e SPARISCE col nostro: il labwc proprio SERVE su Ubuntu 26.04 con KWin 6.6.7.**
La prova di `konsole --fullscreen` (primo rapporto) non lo vedeva perché konsole aggiunge righe quando arriva output e non si anima sul tempo dei frame callback.

## Come si manifestava il difetto (vecchio albero)
`CHANGES-1.5.md` riga ~46, `DECISIONS.md` §10.43, messaggio del commit `46bb1601`: con KWin >= 6.5 annidato, KWin riceve da labwc solo `wp_presentation_feedback.discarded`,
il suo RenderLoop non avanza, i client ricevono frame callback con tempo 0; **Firefox crede la finestra coperta e smette di dipingere** (28 test KDE bloccati, F-003 ecc.).
Quindi il client del sintomo è un programma che si anima sul tempo dei frame callback (Firefox), non un terminale.

## Misure (stesso box, stessa sessione di prova, un solo cambiamento: il labwc)
Sostituzione solo per la prova: `cp -p /usr/libexec/remotix/labwc /root/labwc.pkg; ln -sf /usr/bin/labwc /usr/libexec/remotix/labwc`; ripristino `rm -f …; cp -p /root/labwc.pkg …; rm -f /root/labwc.pkg`.
SHA-256 prima e dopo ogni prova: `47e54654ab6c3b7307e2c8f2cea53bab544656ee60d9dd7a914941717997dcb4` (= quello del .deb estratto; anche `remotix` = `b75a3c7e…357e` uguale al .deb). Il processo labwc della sessione:
`readlink /proc/<pid>/exe` = `/usr/libexec/remotix/labwc` (nostro) oppure `/usr/bin/labwc` (Ubuntu), letto con `runuser -u bc1`.

### (a) Causa diretta: `wp_presentation_feedback` mandati da labwc a KWin, 30 s, `WAYLAND_DEBUG=1` su KWin e labwc
Strumento: drop-in `/etc/systemd/user/plasma-kwin_wayland.service.d/zz-debug.conf` (`Environment=WAYLAND_DEBUG=1`, `LogRateLimitIntervalSec=0`), tolto dopo la prova; conteggio nel journal dell'utente (pid del labwc e di kwin_wayland).
Client in sessione: konsole + weston-simple-shm.
| labwc | presented | discarded |
|---|---|---|
| nostro (pid 16926 → KWin 16944) | **759** (KWin ne riceve 759) | 1 |
| Ubuntu (pid 18940 → KWin 18959) | **0** | **755** (KWin ne riceve 755) |
La causa dello studio 6 è confermata: col labwc di Ubuntu OGNI feedback torna `discarded`.

### (b) Tempo dei frame callback ricevuti dai client (`WAYLAND_DEBUG=1` sul client; conteggio dei `wl_callback.done` dei soli `wl_surface.frame`, 130 s)
| client | labwc nostro | labwc Ubuntu |
|---|---|---|
| Firefox 160 (tarball Mozilla in `/opt/firefox` del box) | 7799 callback, **0 con tempo 0**, 6085 tempi distinti, il tempo avanza di 135 s | 7976 callback, **TUTTI con tempo 0** (1 solo tempo distinto) |
| weston-simple-shm | 3748 callback, 0 con tempo 0, il tempo avanza di 59,9 s | 3613 callback, **TUTTI con tempo 0** |
I callback arrivano ugualmente (~60/s): è il loro tempo che resta 0, come descrive il commit `46bb1601`.

### (c) Immagine sul client (browser di prova Chrome, istantanee del canvas ogni 3 s, 130 s; finestra Firefox 700×500 NON a tutto schermo con pagina `/opt/clock.html`: orologio JS ogni 50 ms + barra animata CSS; dopo ~44 s una seconda finestra konsole non a tutto schermo; dopo ~72 s weston-simple-shm)
Pixel cambiati fra istantanee consecutive, solo Firefox (t = 6…42 s, 11 intervalli):
- nostro: cambia in 10 intervalli su 11 (568…10 662 pixel ogni 3 s);
- Ubuntu: **9 intervalli su 11 con 0 pixel cambiati** (solo 7 133 a t=16 e 61 a t=35): Firefox resta fermo.
Dopo l'apertura di weston-simple-shm (t ≥ 77 s): nostro ≈ 41 000-46 000 pixel ogni 3 s; Ubuntu ≈ 2 100-2 500 (resta solo konsole, ~800 + il resto fermo): weston fermo.
Konsole (testo che si aggiunge a ogni secondo) si aggiorna con entrambi: ~780-800 pixel per intervallo. Non dipende dal frame clock.
(d) Durata: 130 s (e 2 prove complete per configurazione, risultati uguali): lo stato fermo è costante, non un ritardo che cresce; col nostro labwc l'immagine continua a cambiare fino alla fine.

## Limiti
- Una sola macchina, un solo KWin (6.6.7), una sola versione di Firefox (160, tarball Mozilla, non snap) e di weston.
- Il drop-in `WAYLAND_DEBUG` rallenta KWin: la parte (a) è separata dalle parti (b)/(c) (queste senza drop-in per le immagini; i log dei client hanno `WAYLAND_DEBUG` solo sul client).
- `weston-simple-egl`, app GTK4 e finestra a tutto schermo con Firefox non provate; il caso fullscreen di konsole non mostra il difetto (non si anima sul frame clock).
- Il primo esperimento (solo a) con Firefox aveva un difetto di analisi nei log dei client (formato `#` e `wl_callback` di `wl_display.sync` mescolati): corretto e ripetuto, i numeri sopra sono della ripetizione. Un'altra prova identica ha dato lo stesso esito.

## Pacchetti installati nel box (solo per la prova)
`weston gtk-4-examples libgtk-4-bin curl bzip2 xz-utils libgtk-3-0t64 libdbus-glib-1-2 libasound2t64 libxtst6`; Firefox 160.0.1 in `/opt/firefox`, pagina `/opt/clock.html`. Il labwc di Ubuntu era già installato (Recommends).

## Nota di metodo
`box.sh install` con un .deb della stessa versione non rimpiazza i file già installati: i file del box sono stati confrontati con `sha256sum` con quelli estratti dal .deb (uguali per `labwc` e `remotix`).
