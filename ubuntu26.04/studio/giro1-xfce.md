# Giro «unione1» — macchina xfce (Xubuntu 26.04, XFCE 4.20, box `rxu-xfce`, porta 8823)

Data: 18 nov 2026. Pacchetto `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (SHA-256 `2c473ac9…`). Box: `labwc 0.9.3-1`, `libxfce4windowing 4.20.5-1`,
`xfce4-panel 4.20.7-1`, `xfconf 4.20.0-1build1`. Registri del giro: `/media/REMOTIX-UBUNTU/albero/prove/log/unione1-xfce/`. Misura: nulla è stato corretto.
Orario del box: UTC (il server è CET, un'ora avanti).

## 1. Esito del giro: 117 PASS su 124 righe, 7 non PASS

Tutte le righe PASS tranne queste sette (tabella completa in `summary.txt` del giro). `fresh`, base (Chrome e Firefox), lifecycle (4), multiuser (3),
desktop (7), media (4), resilience (5), audio (2), clipboard (2), phone (18 su 19), prelocal (6), ban (8): PASS. Uscita di `input-chrome`, `input-firefox`
e `phone`: exit=1 (per le righe qui sotto); tutti gli altri controlli exit=0.

| Riga | Classe | Prova |
|---|---|---|
| `input-chrome/page-cad-button` e `input-firefox/page-cad-button` | (a) nota e attesa, e (b) della prova | Registro E2 «Pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine (prove da allineare, vedi B3)». La prova stessa lo dice: «the little ⌨ control … exists (True) but is not displayed (display none, 0 px) because page.html's stylesheet hides #shortcuts … unless diagnostics are on (?logbook), a change made on 16 Aug 2026». La prova (`check-input.py`, `t_cad`) esige ancora ciò che la pagina ha tolto per decisione. |
| `input-chrome/page-ctrl-alt-end` e `input-firefox/page-ctrl-alt-end` | (a) e (b), come sopra | «no confirmation appeared … the desktop application RECEIVED the combination [Control_L, Alt_L, End]»; la pagina ha tolto la scorciatoia il 17 ago (commento in page.html), la prova (`check-input.py`, `t_ctrl_alt_end`, in `LAST`) la pretende ancora. |
| `input-chrome/mouse-drag` e `input-firefox/mouse-drag` | (b) della prova, PROBABILE ma non provata; non in E2 | `left to right: WRONG press at fx 0.010 release at fx -1.000, 13 motion events, selected 'alpha beta gamma'` (Firefox 37 motion). Il prodotto ha portato il trascinamento: pressione al punto giusto, tutti i movimenti, e il testo risulta TUTTO selezionato. Manca solo l'evento `release` nel registro della finestra di prova (`rl` vuoto ⇒ `fx=-1`, `check-input.py` righe 148-157). La finestra (`window-input.py` righe 73-76) registra `release` con un `Gtk.GestureClick` in fase CAPTURE su tutta la finestra; un trascinamento dentro una `GtkEntry` che seleziona testo fa prendere alla casella il «sequence» e l'altro gesto riceve annullamento, non `released`: spiegazione plausibile, NON verificata da me. `edge-drag` (trascinamento sul bordo, fuori dalla casella) PASSA con il rilascio visto. LXQt ha le STESSE sette righe nel suo giro (`unione1-lxqt/summary.txt`). |
| `phone/tap-and-half-drag-select` | (b) probabile, stessa famiglia, non provata | `desktop window got 2 left press(es) …, 0 release(s) at fx [], 14 motion events, selection ['help ']`: di nuovo selezione nella casella e nessun `release` registrato. Uguale su LXQt. |

Difetti veri del prodotto nelle righe non PASS: nessuno dimostrato. Il caso del trascinamento (mouse e dito) andrebbe chiuso con una prova che distingua
(per esempio registrare l'evento a livello compositore, non nella casella) prima di dirlo solo della prova.

## 2. Verifiche in più (sulla macchina xfce, utenti di prova `xz1` e `xz2`, miei)

Strumenti miei, fuori dall'albero: `/media/REMOTIX-UBUNTU/lavoro/giro-xfce/` (`xl.py`, `phase1.py`…`phase4.py`, `seat.py`, uscite `phase*.out`, istantanee `*.png`, copie
del file del pannello `xz1-panel-*.xml`). Prodotto e prove non toccati.

### X1 — Ambiente di xfce4-session, xfce4-panel, labwc (sessione remota di `xz1`, utente nuovo)
Per xfce4-session (pid 127775), xfce4-panel (127823) e labwc (127764), valori IDENTICI:
- `DESKTOP_SESSION=xubuntu`, `XDG_SESSION_DESKTOP=xubuntu`, `XDG_CURRENT_DESKTOP=XFCE`, `XDG_SESSION_TYPE=wayland`
- `XDG_CONFIG_DIRS=/run/user/1036/remotix/labwc-xfce:/etc/xdg/xdg-xubuntu:/etc/xdg`
- `XDG_DATA_DIRS=/usr/share/xubuntu:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop`
- `PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin`
- xfconfd (pid 127671, nel gestore dell'utente): `XDG_CONFIG_DIRS=/run/user/1036/remotix/xdg-xfce:/etc/xdg/xdg-xubuntu:/etc/xdg`, `XDG_DATA_DIRS=/usr/local/share/:/usr/share/:/var/lib/snapd/desktop`.
  (La cartella del blocco `xdg-xfce` è dunque solo nell'ambiente di xfconfd, non in quello di sessione/pannello.)
- Journal dell'utente: `⭐ D-153: the session as a local login gives it — session «xubuntu» (declared by the display manager): config folder /etc/xdg/xdg-xubuntu, data folder /usr/share/xubuntu, common folder none`.
- labwc: `readlink /proc/127764/exe` (come utente) = `/usr/bin/labwc` (quello di Ubuntu; riga di comando `labwc -m --session sh -c '…wlr-randr…'`). xfce4-session `/usr/bin/xfce4-session`, xfce4-panel `/usr/bin/xfce4-panel`. NESSUN `/usr/libexec/remotix/labwc`. **OK.**

### X2 — Punto a: utente nuovo, prima sessione remota — OK
- Istantanea del desktop (`xz1-desktop-15s.png`): pannello in alto con il menu whisker (icona Xubuntu a sinistra), orologio e vassoio a destra; NESSUNA finestra «could not be loaded». Nel journal l'unica riga con «could not be loaded» è di wireplumber (libcamera), non del pannello.
- Dopo 15 s, `grep -n -A8 'name="plugin-1"'` sul file utente: `<property name="plugin-1" type="string" value="whiskermenu">` con sei figli `show-command-{lockscreen,switchuser,suspend,hibernate,restart,shutdown}` tutti `type="empty"` (senza valore). Il tipo c'è. `plugin-ids` contiene 1…9.
- `xfconf-query -c xfce4-panel -p /plugins/plugin-1` = `whiskermenu`; `/plugins/plugin-1/show-command-shutdown` = `false` (così pure gli altri cinque).
- `… show-command-shutdown -s true`: codice di uscita 0 (non rifiutato) ma riletto = `false`: il valore NON cambia.
- File di blocco `/run/user/1036/remotix/xdg-xfce/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml`: `<property name="plugin-1" type="empty">` con i sei `show-command-* type="bool" value="false" locked="xz1"`.

### X3 — Punto b: chiusura leggera e nuova nascita — RIPRODOTTO, OK
Nel box non c'è schermata di accesso. L'accesso locale di `check-prelocal.py` (chiama a mano `remotix-local-login` con `PAM_SERVICE=prova-dm`, ecc.) fa la chiusura PIENA: in `child.c` ~10935-10945 il caso `CHILDREN_EXIT_PRELOCAL` salta la «difesa 3» («defence 3 bypassed … FULL close, not the light one»). La chiusura LEGGERA (`local_light_close`, `session.c:4215-4226` «light mode … XFCE keys are NOT restored») avviene invece quando il bambino o il genitore trovano una sessione logind locale (`Remote=no`, tipo grafico `wayland`/`x11`, classe `user`, con seat: `sentinel.c` `kind_if_graphical`) senza passare dal gancio PRELOCAL. Per riprodurla ho:
1. creato un servizio PAM mio `/etc/pam.d/xz-seat` (solo `pam_systemd.so`, SENZA il gancio) e uno script `/tmp/xz-seat.py` (libpam via ctypes) avviati con `systemd-run` fuori dalla sessione ssh, con `XDG_SEAT=seat0 XDG_VTNR=0 XDG_SESSION_TYPE=wayland XDG_SESSION_CLASS=user`: logind crea `c1319 … Seat=seat0 Remote=no Service=xz-seat Type=wayland Class=user` (con `XDG_VTNR=1` o 7 logind rifiuta, `InvalidParameter`: seat0 del contenitore non ha VT);
2. attivato `loginctl enable-linger xz1` (per tenere vivo il gestore dell'utente dopo la fine della sessione locale, come con un desktop locale vero).
Sequenza e osservazioni:
- R1 (remota, desktop su), 33 s dopo: xfconfd pid 132885 con blocco in memoria; file utente `plugin-1 type="string" value="whiskermenu"`, `plugin-ids` 1…9.
- Avvio della sessione locale seated: dopo 7 s `light close (asked by the parent) 1/5 … 5/5 … finished, the local desktop untouched`; `light mode — drop-in removed and daemon-reload done, but NO try-restart of xfconfd`; `light mode — the XFCE keys are NOT restored`; la pagina riceve «the local session on that machine took precedence». Dopo la chiusura leggera: xfconfd stesso pid 132885, ancora con `XDG_CONFIG_DIRS=…xdg-xfce…`; `xfconf-query plugin-1` = `whiskermenu`, shutdown `false`; file utente: `plugin-1 type="string" value="whiskermenu"`, `plugin-ids` 1…9.
- Fine della sessione locale, 14 s di attesa, R2 (nuova remota): ammessa al primo tentativo, desktop con sfondo (`xz1-R2-after-light-close.png`, 0 finestre «could not be loaded»). Journal della nascita: sedici righe `⛔ XFCE: … NOT put back as the user had it — it stays pending` (sei `show-command-*` del pannello più le altre chiavi), `2 keys out of 18 put back — only the 16 that did NOT go back stay pending`, poi (xfconfd fermato e riavviato dal prodotto alla nascita, `Stopping/Started xfconfd.service`, pid 136168) `the user's 16 locked keys put back`. NESSUNA riga «no `actions` nor `whiskermenu`». Dopo R2: file utente `plugin-1 type="string" value="whiskermenu"`, `plugin-ids` 1…9.
- Nota: xfconfd NON è sopravvissuto a R2 (pid cambiato): lo riavvia il prodotto alla nascita, non io; il difetto antico (perdita del plugin) NON si è presentato in questa sequenza. Non ho potuto provare la variante «H1b» (riavviare xfconfd a mano a sessione locale in corso).
- Rimesso a posto: linger disabilitato (`/var/lib/systemd/linger` vuota), sessioni di `xz1` chiuse, `/etc/pam.d/xz-seat` e `/tmp/xz-seat.py` rimossi (verificato).

### X4 — Punto c: Log Out pulito — OK
- Utente nuovo (`xz1`): dopo il Log Out (`xfce4-session-logout --logout`, pagina avvisata subito: «the session has ended: the programs were closed») il file utente ha `plugin-1 type="string" value="whiskermenu"/` (senza figli), nessun `show-command` nei file dell'utente; copia `xfce-chiavi` con `absent=true` per tutte le chiavi, `/plugins/plugin-1 kind=plugin plugin=whiskermenu`; journal: `the user's 18 locked keys put back — their EFFECTIVE values are as they were`.
- Utente con valori propri (`phase4.py`, scritti a mano nel file: `show-command-shutdown=true`, `show-command-lockscreen=true`): in sessione i valori effettivi sono `false` (blocco), file utente intatto; dopo il Log Out il file ha di nuovo `plugin-1 type="string" value="whiskermenu"` con `show-command-shutdown true` e `show-command-lockscreen true` (valori di prima); journal `18 locked keys put back`. **OK.**

### X5 — Punto d: utente danneggiato ad arte — OK
A sessione chiusa e xfconfd fermo tolgo dal file utente la riga `plugin-1` (`sed`, copia `xz1-panel-before-damage.xml` e `xz1-panel-damaged.xml`; `grep -c plugin-1` = 0, `plugin-ids` 1…9 intatto). Nuova sessione remota: journal `⭐ XFCE: /plugins/plugin-1 had no type: put back as «whiskermenu»` (tipo GIUSTO, non `applicationsmenu`); file utente dopo: `plugin-1 type="string" value="whiskermenu"`; effettivo `whiskermenu`; menu presente nell'istantanea (`xz1-X5-damaged-user.png`), nessuna finestra di errore. Dopo il Log Out il nodo c'è ancora.

### X6 — Punto e: «lock is still in xfconfd's memory … not repaired now» — NON compare
Journal di tutti gli utenti di prova (uid ≥ 1000) al momento del conteggio: 40 nascite XFCE (righe `D-153`/`D-017` in 31 utenti), riga «lock is still in xfconfd's memory» = 0, «had no type but the lock is still» = 0, «NOT put back» = 0, «no `actions` nor `whiskermenu`» = 0. (Poi, nelle mie prove: «NOT put back» solo nella nascita R2 dopo chiusura leggera, X3.) La lettura di `/proc/<pid>/environ` di xfconfd funziona (l'ho fatta da root; il prodotto la fa come utente, stesso uid): la riparazione non è bloccata. Non ho però osservato la riga «not repaired now» perché non ho prodotto il caso (nodo senza tipo E blocco ancora in memoria).

### X7 — Punto f: tempo di nascita e sfondo
- Registri del giro: `base-chrome` e `base-firefox` «shell up 0 s and picture settled 6 s after the first frame» (1344×768 e 1392×800); `prelocal/P2` «shell up 0 s» e immagine assestata; `lifecycle.out` non riporta i due tempi (riga `setup` e PASS senza tempo).
- Mia misura (`xz1`, utente nuovo, 1344×768): login accettato dopo 5,8 s (include la pagina), primo fotogramma 0,8 s dopo l'accettazione (nero al 100%, il desktop non è ancora su), pannello su subito dopo, immagine assestata e non uniforme 5 s dopo il primo fotogramma.
- Sfondo: NON nero. `xz1-desktop-settled.png` e `xz1-desktop-15s.png`: sfondo Xubuntu (paesaggio al tramonto con colline scure e un albero, riflesso nell'acqua), icone Home e Trash a sinistra, pannello in alto. Colori: 17180 distinti, il più frequente esatto rgb(24,11,29) al 4,1% (il «dominante 13,8%» dello strumento è un raggruppamento), pixel quasi neri 0,0%. Il difetto E1 di Debian (`libxfce4windowing` 4.20.2) qui non c'è: nel box la libreria è 4.20.5-1.
- Resta vero (E1): XFCE tiene lo sfondo per ogni schermo; qui l'utente era nuovo e ha avuto lo sfondo predefinito.

### X8 — Residui dopo il Log Out (`xz1`, campioni dal momento in cui la pagina è avvertita)
- +5 s: 26 processi dell'utente, tutti di servizio e NESSUNO del desktop: `systemd --user`, `(sd-pam)`, 2 `dbus-daemon`, 3 pipewire (+wireplumber, pipewire-pulse), `mpris-proxy`, `at-spi-bus-launcher`/`at-spi2-registryd`, `gvfsd` + `gvfsd-metadata`, `gvfsd-trash`, 5 volume monitor gvfs, `gnome-keyring-d`, `dconf-service`, `tumblerd`, `xfconfd` (pid nuovo, 5 s: riavviato dal ripristino). `loginctl`: sessione `manager` c1235 e utente in stato `closing`; `user@1036` attivo.
- +15 s e +30 s: NESSUN processo dell'utente, nessuna sessione logind, nessun utente in `loginctl`.
- `ssh-agent`, `gpg-agent`, `xiccd`, `localsearch-3`: mai visti nei campioni (di gpg-agent ci sono solo i socket di sistema `gpg-agent*.socket`); non ho elencato i processi DURANTE la sessione, quindi non so se sono mai nati.
- Ambiente (classe d): `user@1036.service` è finito `failed (Result: timeout)`: «User job mpris-proxy.service/stop running … State 'stop-sigterm' timed out. Killing», SIGKILL al gestore dopo ~40 s dalla chiusura. Lo stesso risulta per `user@1006`, `1007`, `1010`, `1019` (utenti di altri controlli). Non è del prodotto (è il fermo del gestore utente di systemd in un contenitore, un servizio `mpris-proxy` che non si ferma); non influisce sul criterio «nulla resta».

## 3. Che cosa NON è stato possibile vedere
- Il rilascio del pulsante nei due casi di trascinamento (mouse-drag, tap-and-half-drag-select): la causa «finestra di prova» è solo ipotesi.
- Il caso con xfconfd riavviato a mano durante la sessione locale (H1b) e il caso «nodo senza tipo con blocco ancora in memoria» (riga «not repaired now»): non prodotti.
- Un vero accesso locale con lightdm (nei box non esiste): sostituito da una sessione logind con seat creata da un mio servizio PAM; la chiusura leggera risulta quella del codice (`light close … finished`).
- Residui durante la sessione (per sapere se `ssh-agent`, `gpg-agent`, `xiccd`, `localsearch-3` nascono), non solo dopo.

## 4. Modifiche lasciate nel box
- Utenti nuovi `xz1` e `xz2` (con le loro cartelle; non cancellati). Il file del pannello di `xz1` è stato modificato da me (X4 variante, X5) e da REMOTIX. `/etc/pam.d/xz-seat`, `/tmp/xz-seat.py`, linger: rimossi. Nulla altrove.
