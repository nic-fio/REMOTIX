# Giro 2 - KDE (VM `kde`, ssh 2362, REMOTIX 8862) - 26 nov 2026

Pacchetto: `remotix_1.2.0-1+deb13_amd64.deb` (giro2). Il giro e' stato fatto in tre tempi perche' il server e' caduto due volte (vedi sotto).
Registri sul server: `/media/REMOTIX-DEBIAN/tmp/prove-run/prove/log/kde-giro1/`, `kde-giro2/` (voci fino a `phone`), `kde-giro2b/` (`ban`, `apparmor`);
`/media/REMOTIX-DEBIAN/log/giro2/kde/` (kde-exit.out, hold1-3.out). Procedura: `COME-SI-LANCIA.md`.

## Esito per voce (conteggio delle righe PASS/FAIL/BLOCKED)
| Voce | giro1 | giro2 | Note |
|---|---|---|---|
| base (Chrome, Firefox) | 5+5 PASS | 5+5 PASS | |
| lifecycle, multiuser, resilience | 4, 3, 5 PASS | 4, 3, 5 PASS | |
| desktop | 9 PASS | 8 PASS, 1 BLOCKED | `power-local-seat` BLOCKED: «no ACTIVE session on seat0» (sddm col solo greeter, nessuna sessione locale: limite del banco, non del prodotto) |
| media | 3 PASS, 1 FAIL | 3 PASS, 1 FAIL | `screen-updates`, vedi sotto |
| audio (Chrome, Firefox), clipboard | PASS | PASS | |
| input Chrome | 26 PASS | 26 PASS | Ctrl+Alt+Canc: `page-cad-hidden`, `page-cad-chain`, `page-ctrl-alt-end-passes` PASS in entrambi i giri |
| input Firefox | 26 PASS, 1 FAIL (`kbd-not-producible`) | 27 PASS | il FAIL del giro1 non si e' ripresentato col pacchetto giro2 (giro1 aveva il pacchetto vecchio) |
| phone | 19 PASS | 19 PASS | |
| prelocal P1-P6 | 6 PASS | 6 PASS | P7/P8 NON eseguiti (vietati, vedi sotto) |
| ban (rifatto in kde-giro2b) | - | 7 PASS (+ cleanup PASS), 1 SKIP previsto | tutte PASS: wrong-password, same-answer, typed-names-not-logged, ban-after-limit, ban-survives-restart, unblock, unblock-shipped, cleanup |
| apparmor | - | FAIL (vedi sotto) | difetto del PRODOTTO (profilo incompleto) |

### media/screen-updates (FAIL, confronto con GNOME)
KDE giro2: ritardo costante 1,03-1,06 s (mediana primo avvistamento 1129 ms, eta' immagine mediana 1109 ms, fine raffica 1051/1061 ms), 160 su 161 valori visti,
0 passi indietro, animazione 57,8 fotogrammi/s. Soglia dello strumento 1,0 s. Su GNOME 1,05-1,2 s: stesso ordine di grandezza, quindi il ritardo NON e' di
un desktop in particolare (VM senza monitor / strumento / carico 1,29 del server). Nel giro1 KDE il ritardo era 1,82-1,87 s (pacchetto e condizioni diversi).
Causa non stabilita; soglia non allargata.

### apparmor
Il profilo `remotix_network` e' in complain. `check-apparmor.py --box kde` sull'avvio corrente: FAIL, 4 righe ALLOWED, 0 DENIED, tutte uguali:
`operation="open" profile="remotix_network" name="/usr/share/applications/org.kde.remotix.desktop" comm="exe" requested_mask="r" fsuid=986` (fsuid 986 = utente `remotix`).
Il journal della VM E' persistente: stesse righe negli avvii dei giri gia' fatti (`journalctl -k -b -N`): avvio -1 (giro2, 07:38-08:26): 10 righe ALLOWED, tutte la stessa
(07:39:31 ... 08:25:05); avvio -2 (giro1, 00:25-01:12): 8 righe, tutte la stessa (00:26:28 ... 01:11:58). Nessuna riga DENIED, nessun'altra risorsa. Gli avvii -3 e -4 (prove precedenti): 0.
Difetto del PRODOTTO: il profilo non consente la lettura di `/usr/share/applications/org.kde.remotix.desktop` (il file del permesso di cattura per KWin, controllato all'avvio
del servizio: «the capture permission for KWin: ... checked»). In enforce sarebbe un DENIED. Da aggiungere al profilo (`r` su quel percorso).

## Uscita da KDE (nessun riavvio di sddm: `check-kde-exit.py` letto prima, non lo fa)
`check-kde-exit.py`: RESULT PASS.
- 1 terminate-session: desktop sparito in 1 s, 0 processi, 0 sessioni logind REMOTIX.
- 2 riavvio del servizio: desktop sparito in 0 s.
- 3 chiusura del browser e attesa 20 s: 6 processi ancora vivi (il desktop sopravvive al client), nuovo accesso: «Admitted, resumed session»; poi Log Out (org.kde.Shutdown) fatto dallo strumento: sparito in 2 s.
`check-exit.py` non vale per KDE (solo xfce/lxqt).
Uscita dal menu (Log Out = `org.kde.Shutdown /Shutdown logout` dell'utente remoto kd1), a mano:
- CON browser collegato: dopo 2 s nessun `labwc`/`kwin_wayland`/`plasmashell`; dopo ~10 s figlio del servizio finito, 0 sessioni logind; registro: «§7.6 the graphical session of kd1 IS OVER (... logged out from the desktop menu)», `farewell reason=0x10`, «closed the WebTransport session, code 0x10», «the child ... is leaving: Connection reset by peer». PASS.
- SENZA browser (finestra chiusa 10 s prima): tutto sparito in 2 s (figlio, labwc, kwin, plasmashell); registro «IS OVER ... logged out from the desktop menu», «child ... is leaving: closed the socket (or died)». PASS.
Nessun processo dell'utente remoto rimasto in nessun caso.

## Voci specifiche di KDE (sessione aperta con `hold.py`, utente `kd1`)
- Il desktop nasce dentro `labwc` 0.8.3: processi `kwin_wayland_wrapper` > `labwc -C /run/user/1005/remotix-kwin-host/labwc` > `kwin_wayland --wayland-fd ... --socket wayland-0 --xwayland` + `plasmashell` dell'utente + due `remotix --kwin-nested 1344 768 ...`. Nel registro nessuna riga di ripiego `--virtual` (0 in tutti e tre gli avvii della VM).
- `kwin_poke` / `frame lost`: il prodotto non scrive righe con questi testi. Le righe vere (`src/capture.c`) sono «N holes in the numbers of the last M buffers» e «N pokes in a row and no picture from KWin»: 0 e 0 in tutti e tre gli avvii (-2 = giro1 67.405 righe di registro, -1 = giro2 63.229, 0 = oggi).
- Ctrl+Alt+Canc dalla pagina: coperto da `check-input.py`, PASS (vedi sopra).
- Ambiente del desktop remoto (plasmashell, kwin_wayland, gestore utente): `LANG=en_US.UTF-8` (lingua di sistema), nessun `LC_*`, `PATH=/home/kd1/.local/bin:/home/kd1/bin:/usr/local/bin:/usr/bin`. PASS.
- Lingua dell'utente con AccountsService: generato `it_IT.UTF-8` (`/etc/locale.gen` decommentata, resta nella VM), `SetLanguage s it_IT.UTF-8` (file `/var/lib/AccountsService/users/kd1`: `Languages=it_IT.UTF-8;`),
  nuova sessione remota. RISULTATO: **FAIL su KDE, difetto del PRODOTTO (da confermare)**. Il processo `remotix-child kd1` ha `LANG=it_IT.UTF-8` (la lettura di AccountsService funziona),
  ma il gestore utente `systemd --user`, `labwc`, `kwin_wayland`, `plasmashell` e gli altri `remotix` del desktop hanno `LANG=en_US.UTF-8`: l'ambiente scelto non arriva a Plasma
  (su GNOME arrivava a gnome-shell e al gestore utente). Il desktop KDE parte dall'unita' utente `plasma-kwin_wayland.service`, che eredita l'ambiente del gestore utente (preso da `/etc/default/locale`), non quello del figlio.
  Lingua rimessa a `""` (il file ora contiene `Languages=;`).
- Riga di registro sulla chiusura della connessione: presente (`the client said farewell ...`, `closed the WebTransport session, code 0x01/0x10`, `child ... is leaving`; senza saluto: `dropped without a CONNECTION_CLOSE: idle timeout (silence)`).
- Autologin di sddm: all'avvio controllato SUBITO: nessun file in `/etc/sddm.conf.d/` (la cartella e' vuota, modificata alle 08:26) e nessuna riga `Autologin` in `/etc/sddm.conf*`: niente da togliere, nessun riavvio di sddm.
- Stato iniziale della VM sana: `systemctl --failed` vuoto, `dpkg --audit` vuoto, `is-system-running` = running, servizio attivo, `remotix_network` caricato.

## Rimozione e reinstallazione
`apt purge remotix`: nessun file di REMOTIX in `/etc /usr /var /root /opt /lib /run /srv /home` (nome o contenuto), utente/gruppo `remotix` tolti, riga PAM tolta, profilo AppArmor scaricato,
nessun `~/.local/state/remotix` negli utenti. Restano solo i soliti `/etc/passwd-`, `shadow-`, `group-`, `gshadow-` (copie di Debian) e `/root/.cache/mesa_shader_cache*` del 25 nov 20:28
(precedente al pacchetto, non suo). Reinstallato giro2 (`box.sh install`), utente `remotix` ricreato (UID 986), servizio abilitato e attivo (il pacchetto lo lascia `disabled`: l'ho abilitato io),
riga «hook ... in place in /etc/pam.d/common-session», `remotix_network` caricato. VM SPENTA, istantanea `giro2` creata (`qemu-img snapshot -l`: pulito, giro2), Radeon libera.

## Caduta del server
Il server e' caduto due volte, nello stesso passo: `check-prelocal.py`, P1-P6 PASS, poi P7 (vero accesso locale: autologin di sddm e `systemctl restart sddm` dentro la VM con la Radeon passata).
| | giro1 | giro2 |
|---|---|---|
| ultima scrittura di `prelocal.out` | 01:12:59 | 08:26:05 |
| fine dell'avvio della VM nel journal | 01:12:33 | 08:26:10 |
| server non piu' raggiungibile (dal brief) | 01:17 | 08:26 |
| ultima riga di `prelocal.out` | `PASS P6-pam-line-order - pam_systemd line 26, pam_exec remotix-local-login line 27 (after it)` (poi righe vuote: il file ha 8 righe e NUL finali) | `terminal: remote desktop of pl3 up, konsole running (top on pts/1); 49 process(es) (22 not helpers), 22 desktop unit(s)` (seguita da una riga `unit-detail` di un'unita' di pl3 della sessione, 08:25:17) |
Che cosa stava facendo P7 secondo il codice di `check-prelocal.py` (`kind == "terminal"`, utente `pl3`): aperto il desktop remoto di pl3 e lanciato `top` dentro Konsole; subito dopo la riga
«remote desktop of pl3 up ...» il codice fa `autologin(box, "kde", "pl3", True)` (scrive `/etc/sddm.conf.d/99-remotix-bench.conf` con `Autologin User=pl3 Session=plasma`) e `dm_restart(box, "kde")`
(`systemctl restart sddm`), poi attende il desktop locale (fino a `LOCAL_CAP`) per vedere che il gancio PAM chiude il desktop remoto. Nel giro2 l'ultima riga e' quella di prima del riavvio (le 08:25:05 hanno
l'ultimo ALLOWED di AppArmor, le 08:25:17 il `gnome-keyring-daemon` di pl3); nel giro1 P6 era l'ultimo caso e P7 non ha fatto in tempo a scrivere nulla. In entrambi i casi il riavvio di sddm con la Radeon
passata e' il passo che precede la caduta. Nessuno dei due e' stato rifatto: ora `COME-SI-LANCIA.md` ha il divieto in testa.

## Per chi viene dopo
- Dopo un riavvio del server: `prepara-server-vm.sh` va copiato dal repository e lanciato (la copia rimasta puo' essere vecchia: stavolta `python3`, `chromium`, `firefox-esr`, `labwc` mancavano pur con «ALL OK» dichiarato prima; rilanciato dal repository ora e' ALL OK).
- Il registratore della memoria va avviato con `setsid nohup sh -c '...' </dev/null &` (registro: `/media/REMOTIX-DEBIAN/log/memoria-kde.log`, fermato a fine lavoro).
- Strumenti: nessuna correzione necessaria in questo giro (`debian13/prove/` copiato sul server senza toccare `log/`).
- Da decidere/correggere nel prodotto: (1) il profilo AppArmor non copre `/usr/share/applications/org.kde.remotix.desktop`; (2) su KDE la lingua di AccountsService non arriva a Plasma.

## Riprova con giro5 (lingua, AppArmor)
26 nov 2026, 09:2x-09:40. Pacchetto giro5 (md5 `37d30533...2a37`) installato sopra il precedente, `remotix` riavviato (attivo; «the local-login hook is in place»); poi VM spenta e riaccesa (avvio nuovo, solo dopo l'installazione). Utente `kd1`, sessioni aperte e chiuse con `hold.py` (chiusura normale).
- 3a (nessuna scelta): `remotix-child`, `labwc`, `kwin_wayland`, `plasmashell` e gestore utente tutti `LANG=en_US.UTF-8`, nessun `LC_*`. PASS.
- 3b (`SetLanguage it_IT.UTF-8`, nuova sessione): `remotix-child` `LANG=it_IT.UTF-8`, MA `labwc`, `kwin_wayland`, `plasmashell` e `systemctl --user show-environment` restano `LANG=en_US.UTF-8`. **FAIL**: la correzione non ha effetto su KDE. Nel registro di `remotix` dall'inizio della prova nessuna riga «language is NOT put into the user manager» (e nessuna riga sulla lingua). Il registro di sessione/servizio non dice che cosa e' successo.
- 3c: dopo la chiusura normale il gestore utente e' sparito (`user@1005` inactive); `show-environment` rilanciato dopo, `LANG=en_US.UTF-8`, nessun `LC_*`/`LANGUAGE`. Esito valido (niente da ripristinare, ma 3b non ha messo nulla).
- 3d: lingua rimessa vuota (`Languages=;`).
- 4 `check-apparmor.py --box kde` (tutto l'avvio, successivo all'installazione): PASS, nessuna riga ALLOWED/DENIED di `remotix_network` (quindi nessuna per `org.kde.remotix.desktop`).
- Chiusura: VM spenta, Radeon libera, `pgrep -c qemu` = 0, istantanea `giro5` creata. Prima dell'inizio il server mancava di `python3` (script di preparazione lanciato dal proprietario).
