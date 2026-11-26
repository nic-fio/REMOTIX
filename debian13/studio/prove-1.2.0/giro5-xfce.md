# Giro 5, VM xfce (26 nov 2026) - parte 1 INTERROTTA (quarta caduta); parte 2 COMPLETATA (sezione in fondo, con `amdgpu.runpm=0`)

## Cronologia (ore del server)
- 09:49 server su da 30 min, `pgrep -c qemu`=0, Radeon libera. 09:50 `xfce` accesa con la Radeon. Registratore: `log/memoria-xfce2.log`.
- 09:5x passo 3 (utente `xl1`, pacchetto giro2 senza correzione, `hold.py`): fatto, chiusura normale.
- ~09:57 passo 4: `box.sh install xfce .../giro5/remotix_1.2.0-1+deb13_amd64.deb` (`apt-get install -y --reinstall`). Il comando e' rimasto
  senza risposta oltre 180 s; alla verifica successiva il server non rispondeva piu' (`No route to host`), dalle ~09:58.
  Ultima riga di `passi-xfce.log` (scritta prima del comando): `passo4a installa giro5`. Nessuna altra attivita' sul server: una sola VM (`xfce`), nessuna costruzione.
- Atteso fino alle 10:18 (oltre 20 minuti, ping ogni minuto circa): il server non e' tornato. Il lavoro si e' fermato qui; passi 4 (misura), 5, 6, 7 NON eseguiti.
  La VM `xfce` e' rimasta accesa con la Radeon (da spegnere/ripristinare a mano dopo il ripristino del server); `xl1` ha ancora `Languages=it_IT.UTF-8;`.

## Passo 1
`systemctl --failed` vuoto, `dpkg --audit` vuoto, `is-system-running` running, `remotix` attivo (1.2.0-1+deb13, giro2). `debian13/prove/` ricopiata senza `log/`.

## Passo 2: voci del giro interrotto (`log/xfce-giro2/`)
| voce | esito |
|---|---|
| base-chrome | PASS page, login, desktop; **FAIL mouse** (1 movimento, nessun clic arrivato alla finestra) e **FAIL keyboard** (finestra vuota) |
| base-firefox | stesso: PASS page/login/desktop; **FAIL mouse**, **FAIL keyboard** |
| lifecycle | PASS detach-reattach, kill-reattach, reattach-other-size, logout |
| multiuser | PASS two-users, three-users, same-user |
| desktop (parziale) | PASS power-entries-absent; **FAIL no-password-windows**; PASS users-shell-and-environment (il resto non scritto) |
(base-*: le due FAIL mouse/keyboard sono nel registro; la consegna le dava per "passate": vanno guardate.)

`no-password-windows`: una chiamata `BeginAuthentication`, mittente `:1.4` (polkitd) verso `:1.834`, percorso `/org/mate/PolicyKit1/AuthenticationAgent`,
08:12:22.875 UTC = 09:12:22 ora locale. Nel registro persistente della VM (`journalctl -b -1`):
`09:12:22.851 polkitd[747]: Registered Authentication Agent for unix-session:265 (system bus name :1.834 [/usr/libexec/polkit-mate-authentication-agent-1], object path /org/mate/PolicyKit1/AuthenticationAgent, locale en_US.UTF-8)`
cioe' l'agente e' `polkit-mate-authentication-agent-1` (di `mate-polkit`, avviato da XFCE per `dk1`, sessione 265) e la chiamata arriva 24 ms DOPO la sua registrazione.
polkitd NON scrive l'azione richiesta e il registro dell'avvio -1 non contiene altro su polkit/pkexec dopo quell'istante (l'avvio finisce alle 09:13:32);
l'identificativo `org.freedesktop.*` non e' ricavabile da qui (il testo della prova e' troncato prima del campo azione; `/tmp/rx-sysbus.txt` era nella VM, perso al riavvio).
Il `pkexec` della prova `users-shell-and-environment` viene dopo (stesso utente, ordine nel codice), quindi non e' dimostrato che sia lui.

## Passo 3: lingua con giro2 (senza correzione), utente nuovo `xl1`
`it_IT.UTF-8` generato (`/etc/locale.gen`, resta nella VM); AccountsService presente: `SetLanguage` (file `Languages=it_IT.UTF-8;`) PRIMA del primo accesso; home appena creata da `useradd`.
| processo | LANG |
|---|---|
| remotix (child) | it_IT.UTF-8 |
| labwc | it_IT.UTF-8 |
| xfce4-session | it_IT.UTF-8 |
| xfce4-panel | it_IT.UTF-8 |
| xfdesktop | it_IT.UTF-8 |
| xfconfd | **en_US.UTF-8** |
| `systemctl --user show-environment` (gestore utente) | **en_US.UTF-8** |
Nessun `LANGUAGE`/`LC_*`. Nessun processo `light-locker` nella lista dei processi di `xl1`. Chiusura normale (`hold.py` stopped).

---
# PARTE 2 (10:34-11:14, server su da 12 minuti, rimedio `amdgpu.runpm=0` attivo): pacchetto giro5, giro completo
Passo 0: `/proc/cmdline` con `amdgpu.runpm=0`, `runpm`=0, "SMU is resuming" = 0 (e restato 0 fino alla fine, ricontrollato dopo ogni voce), `pgrep -c qemu`=1, registratore `memoria-xfce3.log`,
orari in `passi-xfce.log`. Passo 1: giro5 installato (`dpkg --audit` vuoto), servizio attivo, `remotix-pam-hook ... in place in /etc/pam.d/common-session`.

## Lingua (giro5, utente nuovo `xl2`, `it_IT.UTF-8` in AccountsService prima del primo accesso)
| processo | LANG |
|---|---|
| remotix (child), labwc, xfce4-session, xfce4-panel, xfdesktop | it_IT.UTF-8 |
| gestore utente (`systemctl --user show-environment`) | **it_IT.UTF-8** (con giro2: en_US) |
| xfconfd (pid 2612, nato PRIMA di labwc) | **en_US.UTF-8** (ancora; con giro5 non e' cambiato) |
Nessun LANGUAGE/LC_*. Dopo la chiusura normale il gestore e' sparito; `show-environment` lo riavvia e da' `en_US.UTF-8` (com'era). Lingue di `xl1` e `xl2` rimesse vuote (`Languages=;`).

## Voci di `all.sh` (TAG `xfce-giro5-<voce>`, log in `prove-run/prove/log/`)
| voce | esito |
|---|---|
| base-chrome / base-firefox | page, login, desktop PASS; **FAIL mouse, FAIL keyboard** (vedi sotto: causa = finestra di password) |
| media | PASS (screen-updates, video, codec, two-sessions-budget) |
| resilience | PASS service-restart, network-drop, simultaneous-first-login, login-after-other-logout; **FAIL clocks** ("base failed: typed idle, the window holds empty": stessa causa) |
| audio-chrome, audio-firefox | PASS |
| clipboard | PASS (due direzioni) |
| input-chrome (25 PASS) / input-firefox (26 PASS) | tutto PASS (clic, doppio clic, rotella, trascinamento, tastiera completa) tranne **FAIL mouse-coordinates** (angolo in alto a destra: sotto c'e' il pannello XFCE, vedi sotto) |
| phone | PASS (tutte) |
| ban | PASS (tutte) |
| apparmor | PASS |
| check-prelocal P1-P6 | PASS tutti |
Non lanciate (vietate/escluse): desktop, lifecycle, multiuser, prelocal di `all.sh`, package, P7/P8.

## Mouse e tastiera: PRODOTTO o STRUMENTO? Causa trovata
La foto della pagina (`shots/base-xfce-chrome-20261126-103938-page.png`) mostra al posto della finestra di prova una finestra «Authenticate - Authentication is required to create a color managed device»
con il campo password GIA' riempito con 8 puntini (= "remotix2" scritto dalla prova): tastiera e mouse arrivano al desktop, ma vanno alla finestra di password che ha preso il fuoco.
Dal registro della VM: `10:35:32 dbus-daemon: Activating ... org.freedesktop.ColorManager ... requested by :1.176 (uid=1010 comm="xiccd")` poi
`polkitd: Operator of unix-session:35 FAILED to authenticate to gain authorization for action org.freedesktop.color-manager.create-device ... (owned by unix-user:xl2)` (alla chiusura, 10:38:02; stesso per `bc1`, sessione 68).
Quindi la finestra c'e' in OGNI sessione remota XFCE (anche quella di `xl2`). Quando la finestra di prova viene creata, la finestra di password ha il fuoco. In `input-*`/`clipboard`/`multiuser` passano perche' le loro finestre nascono dopo/riprendono il fuoco.
Verdetto: ne' bug dello strumento ne' trasporto input rotto (`input-chrome` lo prova a fondo): e' un difetto del PRODOTTO nel senso del `40-remotix-remote-sessions.rules`
(sessione remota senza seat => `allow_any` = `auth_admin` per `org.freedesktop.color-manager.create-device`, chiesta da sola da `xiccd`, autostart di Debian `/etc/xdg/autostart/xiccd.desktop`, pacchetto xiccd).
La regola polkit del pacchetto non copre questa azione (copre solo catalogo software, rete KDE, repository). Non toccato (decisione del proprietario).

## Finestra di password (passo 4)
Azione: `org.freedesktop.color-manager.create-device`; programma: `xiccd` (colord); agente: `polkit-mate-authentication-agent-1` (autostart XFCE); si VEDE nel desktop remoto (foto sopra, centrata, in primo piano, con la barra «Authenticate» nel pannello).
(La voce `desktop` NON e' stata lanciata, ma `no-password-windows` fallito nel giro interrotto era certamente questa.) `busctl monitor` con filtro sull'interfaccia dell'agente non ha catturato nulla
(le chiamate `BeginAuthentication` non sono passate dal bus di sistema visibile in 40 s); il nome dell'azione viene dal registro di polkitd. In un utente nuovo con sessione di soli 15 s (`xl3`) la finestra non era ancora comparsa.

## Pannello (passo 5)
`xfce4-panel.xml` di `xl2` e `bc1`: nessun `plugin-N` con `type="empty"` (le uniche righe `empty` sono i contenitori `plugins`, `items`, `panel-1`, `panel-2`, normali). `xfce_panel_integrity` (src/session.c:5927) non scrive righe nel registro del servizio.

## mouse-coordinates (input-*)
`top-right`: `[1339,3]`, il puntatore e' fuori dalla finestra applicativa: nell'angolo in alto a destra c'e' il plugin utente («in1») del pannello XFCE, sopra la finestra a tutto schermo. Altri quattro punti esatti (0-0,9 px). Limite della prova su XFCE (pannello sempre in primo piano), non del trasporto.

## Chiusura
`apt purge remotix`: pacchetto `no packages found`, nessun file in `/etc /usr /var /root /home /opt /run` con nome remotix, nessun utente `remotix`, nessun riferimento in `pam.d`/`apparmor.d`/`polkit-1`. Reinstallato giro5, servizio abilitato e attivo.
VM spenta (11:14), Radeon libera ("Radeon held by VM: none"), `pgrep -c qemu`=0, istantanea `giro5` creata, registratore fermo. "SMU is resuming" = 0 per tutta la durata.
