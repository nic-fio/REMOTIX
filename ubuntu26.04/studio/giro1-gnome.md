# Giro unione1 - macchina `gnome` (Ubuntu 26.04, GNOME 50, box `rxu-gnome`, porta 8821)

18 nov 2026. Pacchetto `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (installato da `fresh.sh`, box nuovo). Registri: `/media/REMOTIX-UBUNTU/albero/prove/log/unione1-gnome/`.
Script e istantanee delle verifiche in più: `/media/REMOTIX-UBUNTU/lavoro/giro-gnome/` (`g1.py`/`g1.out`, `g4.py`/`g4b.py`/`g4b.out`, `desktop-g2*.png`).

## 1. Esito: 116 PASS su 124 righe, 8 non PASS

| Riga | Classe | Prova |
|---|---|---|
| desktop/users-shell-and-environment | (a) nota e attesa (registro E2: «un controllo su GNOME voluto così (`pkexec`)») | `pkexec` dell'utente semplice non apre alcuna finestra password (BeginAuthentication 0 volte): `pkexec` risponde «The value for the SHELL variable was not found in the /etc/shells file». Succede perché REMOTIX imposta `SHELL=` vuoto (`SHELL=` anche nell'ambiente di `gnome-shell`, vedi G1). Il resto della riga è verde: terminale ptyxis in bash, gruppi uguali a `id -G` locale, logind `Remote=yes Service=remotix Type=wayland Class=user Active=yes`, sudo chiede la password, nessuna finestra. Il controllo di `check-desktop.py` (righe 326-327) pretende che l'agente chieda: contraddice la scelta 1.5.3 «niente finestre password non richieste» |
| input-chrome/mouse-drag, input-firefox/mouse-drag | (b) della prova | `press at fx 0.010 release at fx -1.000 ... selected 'alpha beta gamma'`: il trascinamento SELEZIONA tutto il testo (quindi il prodotto lo ha eseguito), ma la finestra di prova non registra l'evento `release`. In `window-input.py:76` il `release` viene da `Gtk.GestureClick "released"`, che in GTK4 non scatta quando il campo di testo ha preso la sequenza per la selezione; `check-input.py:155` richiede però un `release`. Identica riga FAIL anche su `lxqt` e `xfce` (summary): non è di GNOME |
| input-chrome/page-cad-button, input-firefox/page-cad-button | (a) nota (registro E2: «Pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine, prove da allineare, vedi B3») | `#shortcuts`/`#shortcuts-open` esistono ma sono `display none` per il foglio di stile di `page.html` (16 ago 2026) |
| input-chrome/page-ctrl-alt-end, input-firefox/page-ctrl-alt-end | (a) nota (E2, stessa voce) | nessuna conferma «end the session?»; l'applicazione ha ricevuto `Control_L, Alt_L, End`; il commento di `page.html` dice che la scorciatoia è stata tolta il 17 ago 2026 |
| phone/tap-and-half-drag-select | (b) probabile, non provato fino in fondo | `2 left press(es) at fx [0.0515, 0.0515], 0 release(s), 14 motion events, selection ['help ']`: ancora zero `release` (stessa lacuna di `window-input.py:76` di cui sopra); il gesto «tocco e mezzo + trascinamento» è arrivato (14 motion), ma il testo selezionato è solo `help `, non l'intera selezione voluta. Stessa riga FAIL anche su `lxqt` e `xfce`. Non è la voce «primo tocco da telefono su GNOME, saltuario» di E2 (qui non è il primo tocco). Non ho capito se anche la selezione parziale è effetto della prova: lo lascio come (e) |

Nessun difetto del prodotto su Ubuntu emerso dalle righe non verdi. Note a margine lette nei `.out`: ptyxis non mostra `XDG_SESSION_ID`/`XDG_SESSION_CLASS` (nota della prova, non difetto).

## 2. Verifiche in più

Sessione di prova: utente `gv1` (G1-G3, G5), `gv2` (G4), creati da me nel box (restano in `/home`; `gv2` aveva il linger attivo, TOLTO alla fine, `/var/lib/systemd/linger` vuota).

### G1 - ambiente (valori per intero, sessione remota viva, uid 1036)
Identici in `gnome-shell` (pid 126889), nell'applicazione ptyxis (avviata per attivazione D-Bus, pid 128651), nel manager (`systemctl --user show-environment`) e in `gsd-media-keys`:
```
DESKTOP_SESSION=ubuntu
XDG_SESSION_DESKTOP=ubuntu
XDG_CURRENT_DESKTOP=ubuntu:GNOME
XDG_DATA_DIRS=/usr/share/ubuntu:/usr/share/gnome:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop
XDG_MENU_PREFIX=gnome-
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
SHELL=            (vuota, voluto)
XDG_SESSION_TYPE=wayland
```
- `XDG_CONFIG_DIRS`: NON impostata (in nessuno dei quattro ambienti). La riga D-153 dice «config folder none» (non esiste `/etc/xdg/xdg-ubuntu`), coerente con lo studio 3; in un accesso locale lo script `profile.d` la imposterebbe a `/etc/xdg/xdg-ubuntu:/etc/xdg`. Differenza dichiarata, senza effetto pratico (cartella inesistente).
- `GNOME_SHELL_SESSION_MODE`: NON impostata (come previsto nello studio 3: la modalità arriva dall'istanza `org.gnome.Shell@ubuntu`).
- Tutti gli attesi sono confermati (`ubuntu`, `ubuntu`, `ubuntu:GNOME`, `XDG_DATA_DIRS` identico al valore atteso, `/snap/bin` nel `PATH`).
- Journal dell'utente (righe per intero più sotto in forma abbreviata):
  - `D8: the GNOME session is «ubuntu» (ubuntu.desktop): the only one the machine offers.  Candidates: ubuntu (ubuntu).  Line: exec '/usr/bin/gnome-session' '--session=ubuntu' · XDG_CURRENT_DESKTOP=ubuntu:GNOME`
  - `D-153: the session as a local login gives it - session «ubuntu» (the GNOME session REMOTIX starts): config folder none, data folder /usr/share/ubuntu, common folder /usr/share/gnome`
  - `D-015: session keys re-read: 20 in force, 0 NOT (value + lock)` (zero «NOT in force»).
- Non verificato: i valori di `gsettings` letti da un'app. Il mio tentativo (`runuser` senza `XDG_CURRENT_DESKTOP`) ha dato `Adwaita`/`BOTTOM`: NON è una misura valida (la prova non aveva l'ambiente della sessione). Il tema Yaru si vede però nell'istantanea (G2).

### G2 - modalità e istantanea
- `/proc/126889/cmdline`: `/usr/bin/gnome-shell --headless --no-x11 --mode=ubuntu`.
- Istantanea `/media/REMOTIX-UBUNTU/lavoro/giro-gnome/desktop-g2.png` (1344x768): desktop di Ubuntu, non GNOME puro. Barra superiore scura con Activities a pillola, orologio «Nov 18 17:05» al centro (l'ora del box è in UTC+1 diversa dal server, non importa), indicatori a destra (condivisione/registrazione arancione, rete, audio, spegnimento); dock a SINISTRA con Files, Help (punto interrogativo blu), Cestino e il pulsante Ubuntu in basso; sfondo viola 26.04 con logo del procione (Resolute Raccoon); icona Home arancione (ding) in basso a destra; stile Yaru. Le tre istantanee `desktop-g2*.png` sono identiche (la finestra del terminale ptyxis non è comparsa nell'immagine: non so perché, non indagato).
- «Welcome to Ubuntu» / `gnome-initial-setup`: NON è comparso, nessun processo `gnome-initial-setup` (`ps -u gv1`). Osservato su un utente nuovo, un solo accesso.

### G3 - logind
Durante la sessione (utente `gv1`):
```
c1366  Remote=yes Service=remotix Desktop= Scope=session-c1366.scope Leader=126706 Type=wayland Class=user State=active Active=yes
c1367  Remote=no  Service=systemd-user Scope= Leader=126709 Type=unspecified Class=manager State=active
```
- Nel journal non compare «the session will close at the exec». La parola «fifo» compare UNA volta, ma è altro: `child [gv1] FIFO **NOT** OBTAINED: 3 threads out of 3 of the audio path run at NORMAL policy ... RLIMIT_RTPRIO = 0` (priorità in tempo reale dell'audio negata: limite del contenitore/kernel, classe (d), non attinente alla sessione logind).
- Log Out (`busctl ... SessionManager Logout u 1`): la sessione logind è sparita dopo 11,4 s; allo stesso istante `pgrep -u` = 0 processi; il client ha letto «the session has ended: the programs were closed». Dopo: `user@1036.service` inattivo, `/run/user/1036/systemd` non esiste più. Nessun processo rimasto nello scope.

### G4 - rifiuto, attesa, nascita buona (utente `gv2`, linger attivo per tenere vivo il manager utente)
Senza linger il manager utente sparisce con la sessione, quindi il target non si può tenere: ho acceso il linger (poi tolto).
1. Dopo il Log Out `graphical-session.target` è `inactive`.
2. `systemctl --user start graphical-session.target` FALLISCE sempre: «Operation refused, unit graphical-session.target may be requested by dependency only (it is configured to refuse manual start/stop)», rc=4, il target resta `inactive`. Dunque il tentativo manuale non lo attiva (in questo box non ho riprodotto la nota dell'agente: il target risulta attivo solo tramite l'unità transitoria).
3. `systemd-run --user --unit=tieni --property=Wants=graphical-session.target sleep 20` → il target diventa `active` insieme a `tieni.service`.
4. Subito nuovo accesso (17:11:34,6). Registro:
   - 17:11:35,861 `session [gv2] ⛔ the PREVIOUS graphical session has not ended yet («graphical-session.target» is not inactive): I do not make a second one be born now ... ⭐ Retrying shortly` e `child [gv2] ⛔ the graphical session of «gv2» did not start`: la riga di rifiuto nomina `graphical-session.target`.
   - ritentativo 17:11:47,964: stesso rifiuto (intervallo circa 12,1 s).
   - il target è tornato `inactive` circa a 17:11:50 (campione a +15,7 s dal clic; `tieni` finito).
   - 17:12:00,021 terzo tentativo: `D-015: session keys re-read: 20 in force, 0 NOT`, `D-153 ...`, `starting the graphical session: exec '/usr/bin/gnome-session' '--session=ubuntu'`; `org.gnome.Shell@ubuntu.service` avviato 17:12:00,771.
   - Nascita buona SENZA nuovo accesso manuale.
   Visto dal client: «Admitted, new session, canvas 1344×768, desktop gnome» a +1,2 s dal clic, poi schermo senza immagine; primo fotogramma dipinto a +27,3 s dal clic (+27 s; ~10 s dopo che il target è libero, per il passo di 12 s fra i ritentativi). Nessun messaggio di errore al client durante l'attesa.
   - La prima prova (`g4.out`) è stata interrotta dalla mia stessa logica troppo presto (rilevato come «nato» un fotogramma vecchio): scartata, la seconda (`g4b.out`) è quella valida. In `g4.out` il rifiuto compare allo stesso modo (+1,3 s dal clic).
   - Dopo la prova: `loginctl disable-linger gv2`, `terminate-user gv2`: 0 processi, 0 sessioni. `g4-born.png` non esiste utilizzabile (screenshot 0x0 nella prima prova); nella seconda non ho salvato l'istantanea, ma `gnome-shell` era vivo (pid 140114).

### G5 - `user.control`
Durante la sessione: `/run/user/1036/systemd/user.control/org.gnome.Shell@ubuntu.service.d` esiste (drop-in `zz-remotix-monitor.conf`). Dopo il Log Out l'intera `/run/user/1036/systemd/` non esiste più: `org.gnome.Shell@ubuntu.service.d` NON resta. Verificato solo nel caso di utente senza linger; con linger (gv2) non ho guardato la cartella.

### G6 - snap
`snap` è nel PATH della sessione (`/usr/bin/snap`, `/snap/bin` in `PATH`). Atteso: non funziona. Osservato: `snap list` risponde «No snaps are installed yet. Try 'snap install hello-world'.» (rc 0). Nel box `snapd.service` è `inactive` ma `snapd.socket` è `active` e `enabled`: il socket avvia il demone alla prima richiesta. Quindi in questo box il comando funziona (non su uno snap installato: non ne c'è nessuno). Non ho provato ad avviare applicazioni snap. La prova di `snap list` è stata lanciata con `runuser` e l'ambiente D-Bus dell'utente, non da un terminale nella sessione.

## 3. Che cosa NON è stato possibile vedere
- gsettings (tema Yaru, posizione del dock) dall'interno di un'app della sessione (vedi G1).
- La finestra del terminale ptyxis nell'istantanea; l'assistente di primo avvio con un secondo accesso o con `gnome-initial-setup` forzato.
- G5 con linger attivo; G4 senza linger (il manager sparisce).
- La causa della selezione parziale `help ` nel test del telefono.
- L'ambiente di un accesso GDM locale vero su Ubuntu 26.04 (nessun confronto riga per riga, solo i valori attesi dagli studi).
