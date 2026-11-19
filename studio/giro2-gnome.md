# Giro unione2 - macchina `gnome` (Ubuntu 26.04, GNOME 50, box `rxu-gnome`)

18 nov 2026. Pacchetto `pacchetti/unione2/remotix_1.0.0-1+ubuntu26.04_amd64.deb` (SHA-256 `5bfc4da6...`). Registri: `/media/REMOTIX-UBUNTU/albero/prove/log/unione2-gnome/` (summary.txt scritto alle 21:18). Script e istantanee mie: `/media/REMOTIX-UBUNTU/lavoro/giro2-gnome/` (`g.py`/`g.out` primo tentativo, `g2.py`/`g2.out`, `g3.py`/`g3.out`, `*.png`).

## 1. Esito: 123 PASS su 124 righe, 1 FAIL
Confronto riga per riga con `unione1-gnome` (diff delle due tabelle):

| Riga unione1 | unione1 | unione2 | Chiusa da |
|---|---|---|---|
| input-chrome/mouse-drag, input-firefox/mouse-drag | FAIL | PASS | correzione 3 (rilascio registrato) |
| phone/tap-and-half-drag-select | FAIL | PASS | correzione 3 |
| input-{chrome,firefox}/page-cad-button | FAIL | rinominata `page-cad-hidden`: PASS | correzione 3 (controllo cambiato) |
| input-{chrome,firefox}/page-ctrl-alt-end | FAIL | rinominata `page-ctrl-alt-end-passes`: PASS | correzione 3 |
| desktop/users-shell-and-environment | FAIL | FAIL | non toccata (vedi sotto) |
| tutte le altre 116 righe | PASS | PASS | - |

REGRESSIONI: nessuna (nessuna riga verde in unione1 e non verde in unione2). Righe nuove: nessuna oltre alle due rinominate (3 righe rinominate in tutto: 4 con le due varianti browser).

Unica riga ancora FAIL: `desktop/users-shell-and-environment`. Classe (a), nota e attesa (registro E2, `pkexec`). Evidenza identica a unione1: `pkexec by the plain user made no password window (polkit BeginAuthentication 0 times): The value for the SHELL variable was not found in the /etc/shells file`; il resto della riga e' verde (ptyxis in /usr/bin/bash, `SHELL=` vuota voluta, gruppi = `id -G`, logind `Remote=yes Service=remotix Type=wayland Class=user Active=yes`, sudo chiede la password, nessuna finestra). Lo strumento (`check-desktop.py`, righe 326-327) pretende che l'agente polkit chieda la password, in contrasto con la regola «nessuna finestra di password non richiesta».

## G3 - righe per intero (unione2)
Chrome (`input-chrome.out`):
- PASS mouse-drag - left to right: press at fx 0.010 release at fx 0.990, 13 motion events, selected 'alpha beta gamma'; right to left: press at fx 0.990 release at fx 0.010, 13 motion events, selected 'alpha beta gamma'
- PASS page-cad-hidden - outside diagnostics the page shows no Ctrl+Alt+Del / Ctrl+Alt+End button and no control that opens one (in the page but not displayed: ['shortcuts-open'])
- PASS page-cad-chain - with the page's diagnostics on (service route ?logbook) the Ctrl+Alt+Del button sent the three keys (page dispatched [{'name': 'Ctrl+Alt+Del', 'codes': [29, 56, 111], 'ms': 194434}]); the desktop took the combination for itself, as on a local login: the application saw ['Control_L', 'Alt_L'] and then the desktop reacted (focus lost: True, picture changed: True): its own handler, a dialog
- PASS page-ctrl-alt-end-passes - Ctrl+Alt+End typed on the client keyboard: no confirmation, the session is still on, the desktop application received ['Control_L', 'Alt_L', 'End'], End carrying modifiers ['ctrl', 'alt']

Firefox (`input-firefox.out`):
- PASS mouse-drag - left to right: press at fx 0.009 release at fx 0.990, 37 motion events, selected 'alpha beta gamma'; right to left: press at fx 0.990 release at fx 0.009, 37 motion events, selected 'alpha beta gamma'
- PASS page-cad-hidden - (stessa riga di Chrome: ... in the page but not displayed: ['shortcuts-open'])
- PASS page-cad-chain - ... page dispatched [{'name': 'Ctrl+Alt+Del', 'codes': [29, 56, 111], 'ms': 189077}] ... focus lost: True, picture changed: True): its own handler, a dialog
- PASS page-ctrl-alt-end-passes - (identica a Chrome)

Telefono (`phone.out`):
- PASS tap-and-half-drag-select - tap then, within the half-second, a finger down that dragged right: the tap clicked (press at fx 0.051), the second contact pressed the left button at fx 0.051 and held it while the pointer moved (14 motion events) and released at fx 0.472; the entry selected 'help '

(Le righe `page-cad-hidden` e `page-ctrl-alt-end-passes` di Firefox sono riportate in forma abbreviata solo dove sono identiche a quelle di Chrome; il testo completo e' in `input-firefox.out`.)

## G1 - desktop appena nato, portachiavi (utente nuovo `gw1`, uid 1036)
Istantanee: `g1-10s.png`, `g1-40s.png` (da `rig.login()`, canvas 1344x768).
- A 10 s e a 40 s: desktop Ubuntu normale (barra, dock a sinistra, procione, icona Home). UNICA cosa non prevista: una notifica in alto «System - Screen Lock disabled - Screen Locking requires the GNOME display manager». Le due immagini sono identiche byte per byte (stessa notifica, stesso orologio 20:19), quindi NON so dire se la notifica sia rimasta fino a 40 s o se l'immagine non e' stata ridipinta. Nessuna finestra di errore, di password, di portachiavi, nessun assistente di primo avvio, nessun avviso di crash. Se la stessa notifica compaia su GNOME Debian: non verificato da me (nessun confronto fatto).
- Processi del portachiavi: `/usr/bin/gnome-keyring-daemon --foreground --components=pkcs11,secrets --control-directory=/run/user/1036/keyring` (unita utente `gnome-keyring-daemon.service`, attivata dal socket `gnome-keyring-daemon.socket`, cgroup `user@1036.service/app.slice`), piu' `/usr/libexec/gcr-ssh-agent`. Niente componente `ssh`. Nessun `gcr-prompter`, `seahorse`, `gnome-initial-setup`. In `~/.local/share/keyrings/` nessun portachiavi (cartella vuota).
- Journal utente: `Listening on gnome-keyring-daemon.socket`, `Started gnome-keyring-daemon.service`, `gnome-keyring-daemon[...]: GNOME_KEYRING_CONTROL=/run/user/1036/keyring`, due righe di gnome-session `App gnome-keyring-pkcs11.desktop / gnome-keyring-secrets.desktop sets X-GNOME-Autostart-Phase, but gnome-session no longer manages session services`. Nessuna riga `pam_gnome_keyring` (0 nel journal di sistema).
- PAM: `/etc/pam.d/gdm-*` hanno `pam_gnome_keyring.so auto_start` (accesso locale GDM); `common-password` ha `pam_gnome_keyring` opzionale; lo stack usato da REMOTIX (login remoto) NON ha `pam_gnome_keyring`. Quindi il demone e' avviato dal socket (D-Bus/systemd), non da PAM, e non sblocca nulla con la password.
- `secret-tool store --label=prova servizio prova` DENTRO la sessione (processo spostato nel cgroup `session-cNNNN.scope` della sessione remota, ambiente da `/proc/<gnome-shell>/environ`; installato `libsecret-tools` nel box, poi tolto): il comando RESTA BLOCCATO fino al `timeout 60` (rc=124). Il demone ha cercato di chiedere (journal 60 s dopo: `gnome-keyring-daemon[136326]: prompting failed: The operation was cancelled` due volte). Nelle istantanee (`g1-secret-tool-6s.png`, `g1-secret-tool-16s.png`, identiche tra loro) NON compare alcuna finestra, e a ~16 s non c'era un processo `gcr-prompter`. Limite: le due immagini sono identiche (incluso l'orologio): potrebbe essere un'immagine non aggiornata; non posso escludere che una finestra sia comparsa e non catturata. Fatto sicuro: l'applicazione resta in attesa e dopo un minuto la richiesta fallisce; nessuna finestra osservata. (Il primo tentativo in `g.py` non conta: `secret-tool` non era installato.)
- Differenza rispetto a quanto descrive il codice/le prove per Debian: in `src/` e `debian/` del tree REMOTIX `grep -i keyring` non trova nulla: REMOTIX non fa nulla per il portachiavi, come su Debian. La prova `no-password-windows` (`check-desktop.py` r.194-229) guarda polkit `BeginAuthentication` e, sul bus utente, le chiamate di prompt di keyring/wallet (BeginPrompting/PerformPrompt/PromptReady, Secret Prompt, CreateCollection): sul giro unione2 era PASS, cioe' alla nascita nessuna richiesta, come prevede. Differenza reale Ubuntu/Debian rilevata: su Ubuntu il demone e' attivato da socket con `--components=pkcs11,secrets` e c'e' `gcr-ssh-agent`; se la stessa configurazione sia su Debian 13 non l'ho verificato. La prova non copre il caso «un'applicazione chiede un segreto»: e' quello del test `secret-tool`.

## G2 - snap dall'interno della sessione
Come: comando eseguito dentro il cgroup della sessione logind remota (`/sys/fs/cgroup/user.slice/user-1036.slice/session-c1419.scope`, confermato da `/proc/self/cgroup`), con `runuser -u gw1` e ambiente di gnome-shell.
- `snap list` -> `No snaps are installed yet. Try 'snap install hello-world'.` rc=0. `snap version` -> `snap 2.78+ubuntu26.04, snapd 2.78+ubuntu26.04, series 16, ubuntu 26.04, kernel 7.3, architecture amd64` rc=0.
- `snap install hello-world` (e `gnome-calculator`) FALLISCONO, righe per intero:
```
error: system does not fully support snapd: cannot mount squashfs image using
       "squashfs": mount: /tmp/syscheck-mountpoint-4229283632: failed to setup
       loop device for /tmp/syscheck-squashfs-1650520209.
```
- Journal: `snapd/2.78+ubuntu26.04 (series 16; classic; devmode)`, `main.go:175: system does not fully support snapd: cannot mount squashfs image using "squashfs": mount: ... failed to setup loop device ...`, `backends.go:70: AppArmor status: apparmor not enabled`. Classe (d): limite dell'ambiente (contenitore senza loop device ne' AppArmor), non del prodotto. Nessuno snap e' stato installato: niente da togliere. Non osservato: avvio di un'applicazione snap.
- Nel journal anche: `app-gnome-snap\x2duserd\x2dautostart-126945.scope: No PIDs left to attach to the scope's control group, refusing. ... Failed to start ... Application launched by gnome-session-service` (primo giro, prova g.py): scope fallito, di nuovo contenitore; nel secondo giro lo stesso scope risulta `Started`.

## Modifiche fatte nel box (da dichiarare)
- Utenti `gw1` (creato dai miei script, resta in `/home`), nessun linger. `libsecret-tools` installato per la prova e rimosso (`apt-get remove`; verificato: `dpkg-query: no packages found matching libsecret-tools`). File temporanei `/tmp/gw-*` rimasti nel box. Nessuno snap installato.

## Non possibile
- Se una finestra del portachiavi compaia davvero durante `secret-tool` (istantanee identiche, possibile non ridipintura).
- Confronto della notifica «Screen Lock disabled» con Debian.
- Avvio di applicazioni snap.
