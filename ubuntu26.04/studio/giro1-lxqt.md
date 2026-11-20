# Giro unione1 su `lxqt` (Lubuntu 26.04, LXQt 2.3, box `rxu-lxqt`, porta 8824) — 18 nov 2026

Pacchetto: `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (fresh box, riga `fresh | PASS`). Registri: `/media/REMOTIX-UBUNTU/albero/prove/log/unione1-lxqt/`
(`summary.txt`, `<controllo>.out`). Verifiche in più: script e uscite in `/media/REMOTIX-UBUNTU/lavoro/giro-lxqt/`
(`phase_a.py/.out`, `phase_b.py/.out`, `phase_c.py/.out`, `clip.out`, `clip-poll.out`, `desktop-lxqt.png`, `page-lxqt.png`).
Nota: l'orologio del box è un'ora indietro rispetto al server (journal del box 17:02 = server 18:02).

## 1. Esito del giro: 117 PASS su 124 righe, 7 non PASS

Tutti i controlli hanno dato verdetto (nessun BLOCKED, nessun timeout, `sweep` pulito). Le 7 righe non PASS:

| Riga | Classe | Prova / motivo |
|---|---|---|
| `input-chrome/page-cad-button` | (a) nota e attesa | Registro E2 / B3 («Pulsanti Ctrl+Alt+Canc e Ctrl+Alt+Fine, prove da allineare»). Il `.out`: `#shortcuts-open` esiste ma è `display:none` perché `page.html` lo nasconde senza `?logbook` (modifica del 16 ago). Identica su tutte e quattro le macchine. |
| `input-firefox/page-cad-button` | (a) | idem |
| `input-chrome/page-ctrl-alt-end` | (a) | E2 / B3. Nessuna conferma, la sessione resta, il desktop RICEVE Ctrl+Alt+End; la pagina dichiara di aver tolto la scorciatoia il 17 ago. |
| `input-firefox/page-ctrl-alt-end` | (a) | idem |
| `input-chrome/mouse-drag` | (b) della prova, probabile, NON dimostrata | `FAIL mouse-drag - … press at fx 0.010 release at fx -1.000, 13 motion events, selected 'alpha beta gamma'`. Il testo viene selezionato, il press arriva, manca solo l'evento `release` nel registro della finestra di prova. `window-input.py:75-76` registra `press`/`release` con `Gtk.GestureClick`; sospetto (non verificato) che su un `GtkEntry` il trascinamento con selezione faccia terminare la gesture di click con `stopped` invece di `released`. I tasti del mouse dopo il drag funzionano (`mouse-buttons`, `mouse-doubleclick`, `edge-drag` PASS), quindi un tasto rimasto premuto è improbabile. **Stessa riga, stesso valore (`release at fx -1.000`), su gnome, kde, xfce**: non dipende dal desktop. Non in E2: riga nuova rispetto al registro. |
| `input-firefox/mouse-drag` | (b) probabile | idem (37 motion events) |
| `phone/tap-and-half-drag-select` | (b) probabile, stessa firma | `2 left press(es) … 0 release(s) at fx [], 14 motion events, selection ['help ']`: di nuovo nessun `release` registrato dalla stessa finestra di prova; identica su gnome, kde, xfce. Non in E2. |

Nessuna riga rimasta in (c) o (e) tra le righe del giro. Non ho dimostrato la causa del «release mancante»: per farlo servirebbe loggare gli eventi grezzi del compositor durante un drag.

## 2. Verifiche in più

### L1 — ambiente della sessione remota (utente `lx1`, sessione nata 17:02 ora del box): ATTESO, tutto confermato
Identico per `lxqt-session` (pid 54800), `lxqt-panel` (54865), `labwc` (54786), `qlipper`, `pcmanfm-qt`:
```
DESKTOP_SESSION=Lubuntu
XDG_SESSION_DESKTOP=LXQt
XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots
XDG_SESSION_TYPE=wayland   XDG_MENU_PREFIX=lxqt-   QT_QPA_PLATFORM=wayland   QT_QPA_PLATFORMTHEME=lxqt
XDG_CONFIG_DIRS=/run/user/1036/remotix/xdg-lxqt:/etc/xdg/xdg-Lubuntu:/etc:/etc/xdg:/usr/share
XDG_DATA_DIRS=/run/user/1036/remotix/data-lxqt:/usr/share/Lubuntu:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop
PATH=/run/user/1036/remotix/bin-lxqt:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
```
Journal dell'utente: `session [lx1] ⭐ D-153: the session as a local login gives it — session «Lubuntu» (a session file with its own folders): config folder /etc/xdg/xdg-Lubuntu, data folder /usr/share/Lubuntu, common folder none`.
`runuser -u lx1 -- readlink /proc/54786/exe` = `/usr/bin/labwc` (quello di Ubuntu, non il nostro). Osservazione: `/etc/xdg/xdg-Lubuntu` sta DOPO `xdg-lxqt` di REMOTIX e prima di `/etc:/etc/xdg:/usr/share` (il resto della lista è quello del codice, invariato). `QT_QPA_PLATFORMTHEME=lxqt`, non quello di un accesso locale che non ho misurato (non c'è accesso locale nel box).

### L2 — aspetto: è il desktop di Lubuntu, non un LXQt nudo (`desktop-lxqt.png`, 1344x768)
Visto: sfondo blu notte Lubuntu (albero con stella), icone sul desktop «Computer», «Lubuntu Manual», cartella `lx1`, «Network», «Trash» (pcmanfm-qt `--profile=lxqt`), pannello in basso con menu a icona Lubuntu (fancymenu), commutatore «1», lanciatori, taskbar, area di notifica (vassoio, volume, qlipper, nm-tray) e orologio; icone Papirus; finestre con tema chiaro in stile Arc/Kvantum (`/etc/xdg/xdg-Lubuntu/lxqt/lxqt.conf`: `theme=Lubuntu Arc`, `icon_theme=Papirus`, `style=kvantum`, `panel1 plugins=fancymenu, desktopswitch, quicklaunch, showdesktop, taskbar, mount, volume, tray, statusnotifier, worldclock`). Notifica in alto a destra «lubuntu-update: Updates available!».
**DIFETTO VISIBILE (classe c): una finestra «Crash Report» al centro dello schermo: «X Compositor crashed too many times. Its autorestart has been disabled until next login.»** Causa (prove): `/etc/xdg/xdg-Lubuntu/autostart/picom.desktop` (`Exec=picom`, `X-LXQt-Module=true`, NESSUN `X-LXQt-X11-Only`) e anche `/etc/xdg/autostart/picom.desktop`; su Wayland `picom` non può partire (nessun X), `lxqt-session` lo rilancia fino al limite e mostra la finestra. Era previsto nello studio 7 (§7: «picom.desktop di Lubuntu non ha X-LXQt-X11-Only … può apparire nel log»): in realtà appare sul desktop dell'utente, a ogni sessione nuova (mostrata nella foto della prima sessione di `lx1`, 17 s dopo la nascita). Zona probabile della cura (non corretta): `src/session.c` `settings_lxqt()` (~righe 6155-6290 nel codice 1.0.0), dove già si scrivono `.desktop` `Hidden=true` in `data-lxqt`/`xdg-lxqt` per le voci pericolose: aggiungerne uno `autostart/picom.desktop` `Hidden=true` (stessa tecnica proposta nello studio 7 per qlipper). Nessuna riga del giro lo ha rilevato: i controlli non guardano le finestre di errore.

### L3 — sessione logind: ATTESO
Durante la sessione (`lx2`, `lx3`): `loginctl show-session` della sessione remota = `Service=remotix Leader=<pid del figlio> Type=wayland Class=user State=active` (anche `Active=yes`, `Remote=yes`; per `lx1` c1225); accanto la sessione `Class=manager Service=systemd-user State=active`. Nel journal di sistema del box: 0 righe «close at the exec» (controllo ripetuto a 3 e 14 min). Dopo il Log Out (`busctl --user … org.lxqt.session logout`): il client è avvisato dopo 1,4 s («the session has ended: the programs were closed», maschera di login tornata); la sessione remota sparisce da logind prima di +5,3 s (a +5,3 s resta solo la sessione `manager`), logind e processi dell'utente a zero a +11,7 s (+12,1 s e +11,9 s nelle altre due misure). `check-lifecycle/logout` (PASS) lo copre una volta con rientro `Admitted, new session`. **Rientro immediato provato 5 volte** (`phase_b.out`): 5 rientri su 5 ammessi al primo tentativo (`tries=1`), ciascuno una sessione NUOVA (journal: 6 `admitted user=lx2` + 6 `SESSION to lx2: NEW`, nessun rifiuto) e con sessione logind nuova (leader 57500, 57948, 58236, 58523, 58811). La pausa fra il Log Out e il rientro era di circa 4-5 s (4 s di attesa fissa + avviso). Il primo rientro NON è respinto, a differenza del vecchio banco.
Limite: nei rientri la riga di esito della pagina era vuota (`outcome=''`, `0.0 s`): `try_login` ha restituito subito «ammesso» perché lo stato della pagina precedente era ancora «sessione + good»; la prova che sia davvero un rientro nuovo sono il journal e gli identificativi logind, non l'esito della pagina.

### L4 — appunti con qlipper: PASS e qlipper acceso
`clipboard.out` (giro, righe riportate dal giro): `PASS clipboard-session-to-browser … attempt 1`, `PASS clipboard-browser-to-session … attempt 1` (nel giro non c'era un controllo che qlipper fosse acceso, quindi l'ho rifatto). Rifatto con `check-clipboard.py --box lxqt` (`clip.out`) mentre una sonda ogni 2 s guardava `pgrep -u cb1 qlipper`: qlipper pid 63095 acceso e invariato da 18:07:30 fino a 18:07:57 (la sonda non ha mai visto uno spegnimento), con entrambe le righe PASS («copied1g25kg in the desktop» sessione→browser; «Ciao dal browser è € 5a3f7f» browser→sessione, entrambe al primo tentativo). Anche in `lx1`/`lx2`/`lx3` qlipper era in esecuzione (pid 55116, 56665, 60334) e partito dall'autostart di `xdg-Lubuntu` (`lxqt-qlipper-autostart.desktop`). Pacchetto `qlipper 1:5.1.2-2ubuntu3`.

### L5 — residui dopo il Log Out: nessuno oltre il gestore utente
Misura (`phase_c.out`, `lx3`): a +5,3 s: logind = solo la sessione `manager` (c1333); processi: soltanto il `systemd --user` con i suoi servizi (`(sd-pam)`, `dbus-daemon`, `pipewire`, `wireplumber`, `pipewire-pulse`, `mpris-proxy`, `xdg-desktop-por`, `xdg-permission-`, `at-spi-bus-laun`, `at-spi2-registr`, `gvfsd*`), nessun processo del desktop (niente `labwc`, `lxqt-*`, `qlipper`, `pcmanfm-qt`, `picom`, `geoclue agent`). A +15,3 s e +30,1 s: nessuna sessione e nessun processo (`procs: none`, `loginctl=[]`). Stesso risultato per `lx2` dopo il quinto Log Out (+15 s, +30 s: vuoto) e per `lx2` dopo il primo (misura grezza: vuoto a +12,1 s). Il `+5 s` di `phase_b` non è valido (misurato dopo l'attesa di 12 s): vale `phase_c`.

### L6 — aggiornamenti automatici
`/etc/needrestart/conf.d/remotix.conf` c'è (667 byte, 18 nov 14:48) ed è quello del pacchetto: `dpkg -S` = `remotix: /etc/needrestart/conf.d/remotix.conf`; il `.deb` contiene lo stesso file (667 byte); contenuto: `$nrconf{override_rc}{qr(^remotix\.service$)} = 0;`. `dpkg --verify remotix` dà una sola riga: `missing /usr/share/doc/remotix/THIRD-PARTY-LICENSES.gz` — è dell'ambiente (classe d): il box ha `path-exclude=/usr/share/doc/*` in `/etc/dpkg/dpkg.cfg.d/excludes` (la cartella contiene solo `changelog.Debian.gz` e `copyright`), mentre il `.deb` il file lo contiene (25149 byte). **`needrestart` NON è installato nel box** (`dpkg -l`: assente; candidato `3.11-1ubuntu2.26.04.1` disponibile, non installato da me): non ho potuto vedere se elenchi `remotix.service` fra i servizi da riavviare. Il file di configurazione c'è, l'effetto non è osservato.

## 3. Che cosa NON è stato visto
- La causa del «release mancante» nelle 3 righe `mouse-drag`/`tap-and-half` (solo la firma identica sui quattro desktop).
- Il comportamento di `needrestart` (non installato).
- Un accesso locale vero (SDDM) di Lubuntu per confrontare variabili e aspetto: nel box non c'è.
- Se il «Crash Report» di picom compare anche senza utente nuovo (visto sulla prima sessione di `lx1`; in `lx2`/`lx3` non ho scattato la foto del desktop).
- Il filtro di `Hidden=true` per picom non è stato provato (nessuna correzione: è una misura).

## 4. Cambiamenti nel box per le verifiche (da dichiarare)
Creati dagli strumenti di `prove/` (`ensure_user`) gli utenti `lx1`, `lx2`, `lx3`, `cb1` con le loro home; sessioni terminate a fine prova (`loginctl list-sessions` vuoto, nessun processo). Nient'altro: pacchetto non reinstallato, nessun `box.sh reset`, nessun file di sistema toccato, `needrestart` non installato.
