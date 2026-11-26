# Giro 5, VM xfce (26 nov 2026) - INTERROTTO: il server e' caduto la quarta volta

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
