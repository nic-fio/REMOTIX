# Giro «unione2» — macchina xfce (Xubuntu 26.04, XFCE 4.20, box `rxu-xfce`, porta 8823)

Data: 18 nov 2026. Pacchetto `unione2` (SHA-256 `5bfc4da6…`). Registri: `/media/REMOTIX-UBUNTU/albero/prove/log/unione2-xfce/` (server). Misura: nulla corretto.
Mie cose (server): `/media/REMOTIX-UBUNTU/lavoro/giro2-xfce/` (`x23.py`, `x23.out`, `x4.py`, `x4.out`, `rerun-base-firefox.out`, istantanee `yz1-*.png`, copie degli ambienti `yz1-env-*.txt`).
Orario del box: UTC (il server è CET, un'ora avanti).

## 1. Esito: 126 PASS su 128 righe, 2 non PASS (unione1: 117 su 124, 7 non PASS)

Uscite: tutti i controlli exit=0 tranne `base-firefox` (exit=1). Le righe sono 128 contro 124: quattro in più per le rinominate/nuove (vedi tabella).

### Confronto riga per riga con unione1

| Riga unione1 | unione1 | unione2 | Esito del confronto |
|---|---|---|---|
| tutte le altre 117 righe in comune (fresh, base-chrome, lifecycle, multiuser, desktop, media, resilience, audio, clipboard, input, phone, prelocal, ban) | PASS | PASS | verde → verde |
| `input-chrome/mouse-drag` | FAIL | PASS | chiusa dalla correzione (3): il rilascio ora registrato (`release at fx 0.990`) |
| `input-firefox/mouse-drag` | FAIL | PASS | idem |
| `phone/tap-and-half-drag-select` | FAIL | PASS | idem (`released at fx 0.472`) |
| `input-{chrome,firefox}/page-cad-button` | FAIL | (tolta) | sostituita da `page-cad-hidden`: PASS |
| `input-{chrome,firefox}/page-ctrl-alt-end` | FAIL | (tolta) | sostituita da `page-ctrl-alt-end-passes`: PASS |
| NUOVE: `page-cad-hidden`, `page-ctrl-alt-end-passes` (x2 browser) | – | PASS | righe nuove/rinominate; `page-cad-chain` presente in tutte e due le tornate |
| **`base-firefox/mouse`** | **PASS** | **FAIL** | **REGRESSIONE APPARENTE, poi spiegata: vedi sotto (classe d/e, non riprodotta)** |
| **`base-firefox/keyboard`** | **PASS** | **FAIL** | idem |

### La regressione apparente: `base-firefox/mouse` e `keyboard`
Uscita del controllo (`base-firefox.out`, 18 nov 19:33 UTC):
`FAIL mouse - click sent 9 times in 20 s at (0.60,0.50), 2 motion events and NO click reached the window in the box`
`FAIL keyboard - typed "remotix2" in the browser, the window in the box holds nothing`
(page, login, desktop PASS). Nello stesso giro `input-firefox` (24 righe sul mouse e la tastiera con Firefox) è tutto PASS, e `base-chrome` PASS.

Che cosa si vede:
- Il prodotto ha RICEVUTO e inoltrato l'input: journal del servizio `remotix`, utente bc1, 9 coppie `BUTTON evdev code 272 pressed/released` (id 3,4,7,8,…,35,36) e poi `LETTER «a character»` (id 37…). I movimenti arrivano (`POINTER (417,239)` / `(835,399)`), e il cursore cambia forma tra `text` e `default`: il compositore li ha ricevuti.
- La finestra di prova nel box ha registrato solo `ready` e 2 `motion` (`/tmp/rx-bc1-base.log`), nessun `click`, nessun testo.
- L'istantanea della pagina client alla fine del controllo (`prove/shots/base-xfce-firefox-20261118-203329-page.png`) mostra sopra la finestra di prova una finestra di **apport-gtk**: «Sorry, Ubuntu 26.04 has experienced an internal error. Send problem report to the developers?» con la voce `Ubuntu` nella barra dei task. La finestra ha preso il fuoco e coperto la finestra di prova: ecco perché clic e tasti non le arrivavano.
- Causa della finestra: `/var/crash/_usr_bin_blueman-applet.1002.crash` (19:33:44): `blueman-applet` (autostart di Xubuntu) è andato in crash in `blueman/plugins/applet/TransferService.py` `_on_dbus_name_appeared` → `Gio.DBusObjectManagerClient.new_for_bus_sync(...)`: `GDBus.Error:org.freedesktop.DBus.Error.NoReply: Message recipient disconnected from message bus without replying`. Nel box non c'è Bluetooth (`/sys/class/bluetooth` assente, `bluetooth.service` inattivo). Altri due crash identici nello stesso giro: `.1004` (lc2, 19:36:56) e `.1019` (rs10, 19:54:01): 3 volte su una trentina di sessioni nuove.
- Rieseguito `check-base.py --box xfce --browser firefox` tre volte dopo il giro (`rerun-base-firefox.out`): 3 volte PASS su mouse e tastiera (`attempt 1, 3 s`).

Classificazione: **(d) ambiente, con un risvolto sul prodotto da decidere**: la corsa è di `blueman-applet` all'avvio (nome D-Bus di bluez obex che appare e scompare in un contenitore senza Bluetooth), non del trasporto di input di REMOTIX; non riprodotta in 3 su 3. Non sono in grado di dire se in unione1 ci fu lo stesso crash (il box era fresco e i registri `/var/crash` di allora non esistono più); è plausibile che unione1 abbia solo avuto fortuna. NON è un difetto dell'input del prodotto, ma un utente reale con un avvio così vedrebbe la finestra apport sul suo desktop (vedi X2). Dato certo: la finestra comparve, nessuno la chiuse, e coprì la finestra di prova.

Righe di unione2 non PASS: solo queste due. Nessuna riga che era verde e resta rossa per colpa del prodotto.

## 2. X1 — le righe corrette per intero (unione2-xfce, `input-chrome.out`, `input-firefox.out`, `phone.out`)

Chrome:
- `PASS mouse-drag - left to right: press at fx 0.010 release at fx 0.990, 13 motion events, selected 'alpha beta gamma'; right to left: press at fx 0.990 release at fx 0.010, 13 motion events, selected 'alpha beta gamma'`
- `PASS page-cad-hidden - outside diagnostics the page shows no Ctrl+Alt+Del / Ctrl+Alt+End button and no control that opens one (in the page but not displayed: ['shortcuts-open'])`
- `PASS page-cad-chain - with the page's diagnostics on (service route ?logbook) the Ctrl+Alt+Del button sends the three keys: the application saw ['Control_L', 'Alt_L', 'Delete']; page dispatched [{'name': 'Ctrl+Alt+Del', 'codes': [29, 56, 111], 'ms': 180743}]`
- `PASS page-ctrl-alt-end-passes - Ctrl+Alt+End typed on the client keyboard: no confirmation, the session is still on, the desktop application received ['Control_L', 'Alt_L', 'End'], End carrying modifiers ['ctrl', 'alt']`

Firefox:
- `PASS mouse-drag - left to right: press at fx 0.009 release at fx 0.990, 36 motion events, selected 'alpha beta gamma'; right to left: press at fx 0.990 release at fx 0.009, 37 motion events, selected 'alpha beta gamma'`
- `PASS page-cad-hidden - …` (stesso testo di Chrome)
- `PASS page-cad-chain - … the application saw ['Control_L', 'Alt_L', 'Delete']; page dispatched [{'name': 'Ctrl+Alt+Del', 'codes': [29, 56, 111], 'ms': 177378}]`
- `PASS page-ctrl-alt-end-passes - … the desktop application received ['Control_L', 'Alt_L', 'End'], End carrying modifiers ['ctrl', 'alt']`

Telefono:
- `PASS tap-and-half-drag-select - tap then, within the half-second, a finger down that dragged right: the tap clicked (press at fx 0.051), the second contact pressed the left button at fx 0.051 and held it while the pointer moved (14 motion events) and released at fx 0.472; the entry selected 'help '`

Conclusione: la causa nel giro 1 era dunque dello strumento (la finestra non vedeva il rilascio), come ipotizzato; ora il rilascio è registrato in tutti e tre i casi.

## 3. X2 — desktop appena nato di un utente nuovo (`yz1`, 1344×768)

Istantanee (server): `yz1-birth-10s.png` (10 s dopo l'accettazione del login, 8,9 s dopo il primo fotogramma) e `yz1-birth-40s.png` (40 s dopo il login). Primo fotogramma 1,2 s dopo il login.
- Pannello in alto con il menu whisker (icona Xubuntu a sinistra), a destra rete, notifiche, batteria/alimentazione, microfono, volume, orologio. Icone Home e Cestino a sinistra. Nessuna finestra, né di errore né di richiesta, a 10 s né a 40 s: nessuna password, nessun portachiavi/portafoglio, nessun assistente di primo avvio, nessun avviso di crash.
- Sfondo: Xubuntu (paesaggio al tramonto, colline scure, albero, uccelli), NON nero: 17318 colori distinti (10 s) e 17327 (40 s), il più frequente rgb(24,11,29) al 4,1%, pixel quasi neri 0,0%.
- Nella sessione di `yz1` `blueman-applet` NON è andato in crash; è vivo a 49 s (nessun file `.crash` per l'uid 1036). Il caso crash di sezione 1 non si è dunque ripresentato in questa nascita: 3 crash su una trentina di nascite osservate (non per colpa dell'utente nuovo: avviene a caso).
- Journal dell'utente: le uniche righe «could not be loaded» sono di wireplumber (libcamera); errori RTKit di pipewire (`org.freedesktop.DBus.Error.NoReply`); riga di REMOTIX `⛔⛔ FROM THIS SESSION THE MACHINE CAN BE POWERED OFF OR SUSPENDED (CanPowerOff=no CanReboot=no CanSuspend=(no answer) CanHibernate=(no answer))` (testo di avviso generico con valori «no»: non l'ho indagata, la riporto perché è una riga di allarme; non produce finestre).

## 4. X3 — variabili di `Xsession.d` che un accesso locale darebbe e la sessione remota non ha (solo tabella)

Nel box gli script di `/etc/X11/Xsession.d` che esportano variabili, e il confronto con l'ambiente reale di `xfce4-session` (pid 135722, utente `yz1`, `/proc/<pid>/environ`; copie in `yz1-env-*.txt`):

| Script | Variabile | Condizione nello script | In xfce4-session remoto |
|---|---|---|---|
| `56xubuntu-session` | `GTK_OVERLAY_SCROLLING=0` | `DESKTOP_SESSION = xubuntu` | assente |
| `56xubuntu-session` | `QT_QPA_PLATFORMTHEME=gtk2` | idem | assente |
| `56xubuntu-session` | `CLUTTER_BACKEND=x11` | idem | assente |
| `90qt-a11y` | `QT_ACCESSIBILITY=1` (e `dbus-update-activation-environment --systemd`) | sempre | assente in xfce4-session, ma PRESENTE nell'ambiente di `systemctl --user` (`QT_ACCESSIBILITY=1`) |
| `90gpg-agent` | `GPG_AGENT_INFO`, `SSH_AUTH_SOCK` | se gpg-agent/ssh è abilitato | assenti in xfce4-session; nel `systemctl --user` ci sono (`GPG_AGENT_INFO=/run/user/1036/gnupg/S.gpg-agent:0:1`, `SSH_AUTH_SOCK=/run/user/1036/gcr/ssh`) |
| `70im-config_launch` | `IM_CONFIG_ENTRY=xsession` (e avvio di `im-launch`) | sempre | assente; nessun `im-launch` in esecuzione |
| `55numlockx` | `NUMLOCK=auto` (variabile di script, non esportata) | – | assente (ininfluente) |
| `55xfce4-session` | `XDG_DATA_DIRS` con `/usr/share/xfce4` davanti | solo se `STARTUP` è xfce4-session | NON c'è `/usr/share/xfce4`; il remoto ha `XDG_DATA_DIRS=/usr/share/xubuntu:/usr/local/share/:/usr/share/:/var/lib/snapd/desktop` |
| `60x11-common_xdg_path` | `XDG_CONFIG_DIRS`, `XDG_DATA_DIRS` di base | – | presenti (con le cartelle xubuntu e quella di REMOTIX davanti) |
| `20dbus_xdg-runtime` | `DBUS_SESSION_BUS_ADDRESS` | – | presente (`unix:path=/run/user/1036/bus`) |
| `75dbus_dbus-launch`, `90x11-common_ssh-agent`, `90xbrlapi` | nessuna variabile propria rilevante | – | – |

Ambiente remoto comune (xfce4-session): `DESKTOP_SESSION=xubuntu`, `XDG_SESSION_DESKTOP=xubuntu`, `XDG_CURRENT_DESKTOP=XFCE`, `XDG_CONFIG_DIRS=/run/user/1036/remotix/labwc-xfce:/etc/xdg/xdg-xubuntu:/etc/xdg`. Nel box NON ci sono programmi Qt (nessuna `libQt*`, nessun pacchetto `qt` secondo dpkg): la differenza `QT_QPA_PLATFORMTHEME` non avrebbe comunque effetto visibile qui. Come da decisione del proprietario, nessuna prova visiva e nessuna istantanea di confronto.
Mancano quindi nel remoto: `GTK_OVERLAY_SCROLLING=0`, `QT_QPA_PLATFORMTHEME=gtk2`, `CLUTTER_BACKEND=x11` (le tre di `56xubuntu-session`), `IM_CONFIG_ENTRY` con `im-launch`, e il prefisso `/usr/share/xfce4` in `XDG_DATA_DIRS`.

## 5. X4 — residui a fine giro

- A giro finito (prima delle mie prove): `ps` per gli uid ≥ 1000 nel box: solo processi dell'utente `yz1` (mio, 40 processi, sessione staccata); `loginctl list-sessions`: solo `yz1` più root. Nessun utente di prova del giro con processi (il registro `sweep.out` dice «34 test user(s) ended»).
- Dopo le mie prove: 0 processi per uid ≥ 1000, nessuna sessione di `yz1`, linger vuota. L'utente `yz1` (mio, con la cartella) NON è stato cancellato. Restano in `/var/crash` i tre `.crash` di blueman-applet (dei controlli del giro).

Osservazione fuori elenco (non è una riga del giro): ho fatto il Log Out di `yz1` con la sessione staccata (nessun browser). Il desktop si chiude (`labwc` scompare, 20:23:56) ma il processo figlio `remotix` e il gestore dell'utente restano vivi (27 processi, sessione logind `c1302` ancora attiva) per più di 3 minuti, con la riga `⛔ wlroots: the input connection has DROPPED … retrying every second`. Un nuovo login lo ammette come «resumed session» (`SESSION … RESUMED (the stage was already there)`) ma senza desktop: `frames painted=1`, pannello non su, canvas di larghezza 0. Quando il browser lascia, la sessione morta viene poi eliminata (0 processi). Il giro 1 verificava il Log Out solo con il browser collegato (lì il figlio finisce in 15-30 s). È un caso limite (uscita dal desktop mentre nessuno guarda); l'ho solo osservato, non indagato nel codice.

## 6. Che cosa NON è stato possibile vedere
- Se il crash di `blueman-applet` e la finestra apport comparvero anche in unione1 (box ricreato, nessun `/var/crash` di allora).
- Il caso del Log Out a sessione staccata: non capisco se è voluto (la sessione sopravvive finché qualcuno non torna) o un difetto; non è stato indagato.
- Qualunque effetto visibile di Qt/GTK (X3 ridotto a tabella per decisione del proprietario).

## 7. Modifiche lasciate nel box
- Utente `yz1` (creato da me per X2/X3/X4, con la cartella; senza sessioni). Nel suo `$HOME` (non toccato dopo: lo script `rx-launch.sh` e `long.txt` non sono stati creati perché X3 è stato ridotto). Nient'altro: nessun pacchetto, nessun file PAM, nessun linger.
- Il controllo `base-firefox` rieseguito 3 volte ha riutilizzato l'utente `bc1` del giro (già esistente).
