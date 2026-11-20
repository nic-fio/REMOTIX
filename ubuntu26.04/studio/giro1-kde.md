# Giro unione1 su `kde` (Kubuntu 26.04, KWin/Plasma 6.6.7, box `rxu-kde`, porta 8822) — 18 nov 2026

Pacchetto: `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (SHA-256 `2c473ac9…81cb3d`). Giro: `all.sh kde --fresh`, registri in
`/media/REMOTIX-UBUNTU/albero/prove/log/unione1-kde/`. Nulla di prodotto o prove è stato corretto. Script miei (solo sul server, non nell'albero):
`/media/REMOTIX-UBUNTU/lavoro/giro-kde/` (`k156.py`, `k63.py`, `k6.py`, `k2.py`, `k2b.py`, `k4.py`, `k5b.py`, `anim.py` + uscite `*.out`).
Istantanee in `/media/REMOTIX-UBUNTU/albero/prove/shots/` (`gk-*.png`, `gk10-k5-*.png`, `gk2-k3-*.png`, `gk6-k6-*.png`).

## 1. Risultato del giro: 111 PASS su 124 righe, 13 non PASS (tutte FAIL; nessun BLOCKED)
Confronto con le altre macchine dello stesso giro: gnome 116 PASS / 8 FAIL, xfce 117 / 7, lxqt 117 / 7. Le 9 righe dei pulsanti Ctrl+Alt (6), mouse-drag (2) e tap-and-half-drag (1) falliscono con gli stessi numeri anche sulle altre macchine che le hanno non verdi (cad e ctrl-alt-end e mouse-drag e half-drag: verificato nei `.out` di gnome, xfce, lxqt per mouse-drag e half-drag; cad/ctrl-alt-end per le altre tre solo da `summary.txt`): non sono di KDE. Solo 4 righe sono proprie di KDE: logout, settings-intact, reattach-windows-inside, codec.

| Riga | Esito | Classe | Prova |
|---|---|---|---|
| lifecycle/logout | FAIL | (c) prodotto su Ubuntu, in parte (d) | vedi 3 (K2) |
| desktop/settings-intact | FAIL | (c)/(e): stesso gesto, stesso sintomo del precedente | «Log Out of the second session did not end it in 72 s»; non ho letto il journal di quell'utente a parte |
| desktop/reattach-windows-inside | FAIL | (b) della prova | vedi sotto |
| media/codec (solo Firefox) | FAIL | (e) non capita | vedi sotto |
| input-chrome e input-firefox/mouse-drag | FAIL | (b) della prova (probabile), comune a 4 macchine | vedi sotto |
| phone/tap-and-half-drag-select | FAIL | (b) della prova (probabile), comune a 4 macchine | vedi sotto |
| input-*/page-cad-button, page-cad-chain, page-ctrl-alt-end (6 righe) | FAIL | (a) nota e attesa | `docs/REGISTRO-problemi.md` voce E2 (+ B3); uguali su tutte e 4 le macchine |

Dettagli:
- **reattach-windows-inside** (`check-desktop.py:745-794`, riga 793). La finestra era 2567x1553 in un canvas 3824x2160; dopo il riaggancio a 2544x1440 è 2295x1021 a (236,398): interamente visibile (236+2295=2531 < 2544; distanza dal bordo 12/20 px). Il controllo pretende «stessa dimensione ±3%», ma la finestra era più larga del nuovo canvas (2567 > 2544): non può restare uguale. KWin la rimpicciolisce per farla stare (comportamento normale di Plasma). Su GNOME, XFCE e LXQt la riga è PASS. Foto: `shots/desk-reattach-2-2560-kde-261118-172628.png` (finestra intera, sopra il pannello). Non provata la stessa prova con una finestra che entrerebbe.
- **media/codec, Firefox 153.7**: «edge 10-90% rise 130 px, contrast 1px 0.79»; Chrome sulla stessa macchina PASS (rise 0 px); su gnome, xfce, lxqt anche Firefox PASS (rise 0). Guardando la foto (`shots/media-codec-firefox-kde-261118-173618.png`) il bordo nero/bianco è netto a occhio e il resto dei motivi c'è; il numero 130 px lo ha dato la misura. Non so se sia una misura presa a metà di un cambio di immagine o un difetto reale. Non l'ho rieseguita (non era fra le verifiche richieste). Classe (e).
- **mouse-drag / tap-and-half-drag**: il testo viene selezionato correttamente ('alpha beta gamma') ma la finestra di prova non registra l'evento `release` (`release at fx -1.000` = nessun evento); stessa riga, stessi numeri, su tutte e quattro le macchine (anche gnome, xfce, lxqt). Probabile effetto del GestureClick di GTK4 in `window-input.py:76` (il gesto viene annullato quando la selezione del campo di testo prende la sequenza): è la prova, non il desktop. Non verificato con un altro strumento; sul banco Debian non ho potuto confrontare (registri non presenti). Resta una riga che nessuna macchina Ubuntu passa.

## 2. K1 — labwc proprio, ambiente, D-153 (utente nuovo `gk1`, sessione remota viva; uscita in `k156.out`)
- processo `labwc` pid 88230, `runuser -u gk1 -- readlink /proc/88230/exe` = **`/usr/libexec/remotix/labwc`** (nostro). Riga di comando: `labwc -C /run/user/1036/remotix-kwin-host/labwc`; `kwin_wayland --wayland-fd 7 --socket wayland-0 … --width 1344 --height 768`, lanciato da `remotix --kwin-nested 1344 768 /dev/dri/renderD128`.
- `sha256sum /usr/libexec/remotix/labwc` nel box = `47e54654ab6c3b7307e2c8f2cea53bab544656ee60d9dd7a914941717997dcb4` = quello estratto dal `.deb` (`dpkg-deb -x` in `lavoro/giro-kde/deb/`; stesso valore; anche `remotix` = `1283976e…d2ef` uguale al .deb).
- Ambiente di **plasmashell** (pid 88389) e di **kwin_wayland** (pid 88251), identici fra loro, valori per intero:
  `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`
  `XDG_DATA_DIRS=/usr/local/share/:/usr/share/:/var/lib/snapd/desktop`
  `XDG_CONFIG_DIRS=/home/gk1/.config/kdedefaults:/run/user/1036/remotix/xdg:/etc/xdg`
  `XDG_CURRENT_DESKTOP=KDE`, `XDG_MENU_PREFIX=plasma-`
  `DESKTOP_SESSION`: **non impostata** (differenza nota). `XDG_SESSION_DESKTOP`: **non impostata** nemmeno (il mio filtro la cercava: non è comparsa in nessuno dei due processi).
- Journal dell'utente: `session [gk1] ⭐ D-153: the session as a local login gives it — session «(none)» (its local login adds no session folders, or no session is known): config folder none, data folder none, common folder none` = come atteso (nessuna cartella di sessione, common folder none).

## 3. K2 — uscita da KDE (gesto del check: `busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout`)
**Due casi osservati.**
**K2a** (utente `gk4`, gesto 16 s dopo la nascita, appena finito il controllo «idle» del check; `k2.out`): dopo 5, 15, 30, 45, 60, 90 e 120 s il desktop **non esce**: 47 processi prima, 42 dopo (restano `startplasma-way`, `kwin_wayland_wr`, `labwc`, `kwin_wayland`, `ksmserver`, `plasmashell`, `kded6`, `Xwayland`…), sessioni logind `c1432 user` e `c1433 manager` attive, il client non viene avvisato (`form=False`, esito «Admitted, new session…»). `plasma-shutdown` ha finito subito (`rc=0` dopo 36 ms). Journal dell'utente:
`17:22:47.250 Activating service name='org.kde.Shutdown'` → `17:22:47.291 systemd[97723]: Requested transaction contradicts existing jobs: Transaction for graphical-session.target/stop is destructive (xdg-desktop-portal.service has 'start' job queued, but 'stop' is included in transaction).`
`xdg-desktop-portal` parte davvero solo alle 17:22:56 (prima `Failed to create RealtimeKit proxy … timed out`), ma nessuno ripete lo stop. Nel journal del servizio **non** compare alcuna riga della «cura» `session_kde_logout_watch` («Plasma: plasma-workspace.target is … while KWin is still up»). Inoltre nessuna forzatura dopo 10 s (nessuna riga). Ho lasciato il desktop vivo 120 s poi fatto chiudere dagli strumenti.
Perché la cura non scatta: `session.c:4424-4500` aspetta di vedere `plasma-workspace.target` prima attivo e poi non attivo; qui `plasma-shutdown` 6.6.7 ha chiesto subito lo stop di `graphical-session.target`, rifiutato, e `plasma-workspace.target` è rimasto attivo (nessuna riga «Stopped target plasma-workspace.target» fino alla fine forzata). Il segnale su cui poggia la cura (commento a `session.c:4375-4394`) non c'è su Plasma 6.6.7. È solo un'ipotesi dal codice e dal journal: non ho modificato né provato nulla.
Nel giro, `lifecycle/logout` (utente `lc2`, gesto 2 min dopo la nascita) ha mostrato un'altra variante: nessun «destructive» al gesto; `ksmserver` non risponde (`org.kde.plasma.shutdown: ksmserver failed to complete logout with error "org.freedesktop.DBus.Error.NoReply"`, `KWin failed to complete logout`, 35 s) e il desktop è sceso solo alle 16:24:26, quando la pulizia di fine prova ha ucciso la sessione (`session-c89.scope: Killing process 6869 (remotix) with signal SIGTERM`). Con il giro che girava in parallelo su 4 macchine. Non so spiegare perché `ksmserver` non rispondesse.
**K2b** (utente `gk7`, gesto dopo 61 s, `systemctl --user list-jobs` vuoto, `k2b.out`): **funziona**: il client viene avvisato dopo 5,5 s («the session has ended: the programs were closed», form di accesso di nuovo visibile); a 5 s restano 10 processi (infrastruttura: remotix, systemd, dbus, pipewire…), a 15 s **0 processi e nessuna sessione logind**, e così a 30, 45, 60, 90, 120 s. Nessun `labwc`, `kwin_wayland`, `plasmashell` residuo. Nessuna forzatura: l'uscita è ordinata (`Stopped plasma-kwin_wayland.service` alle 17:26:51; `Reached target shutdown.target` 17:27:02).
Sintesi: l'uscita da KDE su Ubuntu 26.04 funziona se il desktop ha almeno ~1 minuto e nessun job in coda; nei primi secondi (portale in avvio, qui rallentato da `RealtimeKit … timed out` 25 s dentro il contenitore) il Log Out viene perso e la cura non lo ripesca (K2a). Il vecchio banco lasciava 11 processi: qui, nel caso che funziona, 0.

## 4. K3 — ridimensionamento al riaggancio (utente `gk2`, `k63.out`; browser Chrome di dimensioni diverse con `Rig.new_browser(size)`)
Prima: browser 1400x900, canvas 1344x768, finestra fullscreen nel box 1344x768. Dopo, riaggancio («resumed»):
- browser 1000x640 → canvas/immagine **944x496**, finestra nel box (nuova, a tutto schermo) **944x496**;
- browser 1700x1000 → **1584x864**, finestra nel box **1584x864**;
- browser 800x500 → **752x368**, finestra nel box **752x368**.
(L'esito mostrato dalla pagina dice la dimensione precedente: «resumed session, canvas 1344×768» ecc., mentre l'immagine e il desktop hanno già la nuova.) Anche il giro: `lifecycle/reattach-other-size` PASS (944x496), `desktop/canvas-limits` PASS (limiti 320x240…3840x2160).

## 5. K4 — ripiego dichiarato (`k4.out`)
Solo dentro il box: `chmod a-x /usr/libexec/remotix/labwc` (era 755 root:root, 1456680 byte, mtime 2026-11-18 15:39:08).
Sessione nuova `gk8` con il labwc non eseguibile: **ammessa** («Admitted, new session, canvas 1344×768, desktop kde»), desktop arrivato (1344x768, 501 colori; foto `shots/gk-k4-gk8.png`: solo lo sfondo, senza pannello al momento della foto). Processi: `kwin_wayland_wrapper … --virtual`, `kwin_wayland … --virtual`, plasmashell; **nessun processo labwc**. Registro: `remotix --kwin-nested: ⛔ our labwc is not installed: KWin --virtual, and the desktop will NOT take the window's size at reattach (DECLARED FALLBACK)`; `capture [gk8] ⭐ KWin: zkde_screencast v5 on socket «wayland-0», output «Virtual-0» 1344x768`. Il client vede un desktop normale ma, come dichiara il registro, il riaggancio con altra dimensione non adatterebbe il desktop (non provato).
Ripristino: `chmod 755`; dopo: SHA-256 `47e54654…dcb4` **uguale**, `stat` = `755 root:root 1456680 2026-11-18 15:39:08` **identico** a prima. Sessione nuova `gk9`: labwc pid 106677 con `readlink /proc/106677/exe` = `/usr/libexec/remotix/labwc` (nostro), riga `labwc (pid 106677 …) at 1344x768 … now KWin, nested in it`. Stato finale riverificato: 755, stesso hash.
Nota: la riga «pointer hiding will NOT be delivered any more: KWin --virtual…» compare anche nella sessione col nostro labwc (gk9), quindi non è del ripiego.

## 6. K5 — portafoglio delle password (OSSERVAZIONE, nessun giudizio)
Utenti nuovi `gk1` (`k156.out`) e `gk10` (`k5b.out`), prima sessione remota; foto a 5, 30 (gk1, gk10) e 60, 90 s (gk10).
- Nessuna finestra di KWallet né richiesta di password in nessuna delle foto di gk10 a 30 s e a 90 s (desktop Kubuntu: icone «HOW-TO Guides» e «Kubuntu Website», pannello in basso, orologio; `gk10-k5-30s.png`, `gk10-k5-90s.png`). Le foto di gk1 a 5 s e 30 s mostrano solo lo sfondo (nessun pannello ancora, macchina carica dal giro): nessuna finestra neppure lì.
- Processi: `kwalletd6` **mai visto**; `ksecretd` compare fra 5 e 30 s (a 5 s no, a 30 s sì, pid 88891 in gk1; anche in gk10) e resta; `polkit-kde-auth` presente da subito.
- Journal (`grep wallet|ksecret|kwallet`): `Started plasma-kwallet-pam.service - Unlock kwallet from pam credentials.`; `Activating service name='org.freedesktop.impl.portal.desktop.kwallet' requested by xdg-desktop-portal` → `Successfully activated`. Nessun `~/.config/kwalletrc`; `~/.local/share/kwalletd` esiste, vuota.
- Il controllo del giro `desktop/no-password-windows` PASS (0 chiamate polkit BeginAuthentication; 0 richieste di prompt di keyring/wallet sul bus dell'utente).

## 7. K6 — una finestra che cambia si aggiorna sul client (60 s, pacchetto del giro, labwc proprio; `k6.out`, utente `gk6`)
Firefox e `weston-simple-shm` non ci sono più nel box e non li ho installati. Programma animato usato (dichiarato): finestra GTK4 non a tutto schermo (`anim.py`) con un contatore grande aggiornato ogni 16 ms (timer; la pittura è comunque pilotata dai frame callback Wayland); heartbeat: 4196 passi in circa 70 s. Pixel cambiati fra istantanee del canvas ogni ~3 s, 19 intervalli in 61 s: **0 intervalli su 19 senza cambiamenti**; valori da 1 826 a 5 255 pixel (bbox sulla finestra, 553-792 x 354-433), più un intervallo a 69 521 pixel (apertura della finestra). Quindi la finestra animata arriva al client per tutta la durata. NON è la stessa prova di Firefox (che dipende dal tempo dei frame callback); non ho misurato il tempo dei `wl_callback.done` (non fatto). Due tentativi precedenti sono falliti per un mio errore (il file `/tmp/rx-anim.err` creato da un altro utente non era scrivibile): non contano.

## Che cosa NON ho potuto vedere / limiti
- Firefox non snap e `weston` assenti nel box: K6 fatto con un altro programma, e senza misura dei frame callback.
- media/codec Firefox: non rieseguito, causa non chiarita. settings-intact: journal non letto.
- Riaggancio con altra dimensione nel ripiego `--virtual` (K4): non provato.
- Il difetto del Log Out l'ho riprodotto una volta (K2a) e visto funzionare una volta (K2b); non so quanto sia frequente né quanti secondi di vita servano esattamente (fra 16 e 61 s).
- Stato lasciato nel box: utenti di prova `gk1…gk10` (creati da me, senza processi né sessioni), file `/tmp/rx-anim-gk6.*`, `/tmp/k2-logout.out`, `/tmp/rx-gk*`. Nessun file del pacchetto cambiato (labwc: stesso hash, stesso modo e mtime; nessun drop-in lasciato).
