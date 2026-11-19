# 13 - Pacchetto riunito (unione3a) su xfce e lxqt

Pacchetto: `/media/REMOTIX-UBUNTU/pacchetti/unione3a/remotix_1.0.0-1+ubuntu26.04_amd64.deb` (sha256 .deb `f7ff0294...`).
Binario dentro il .deb: `/usr/libexec/remotix/remotix` sha256 `20e77abd79eb2199e382269e885f4af839a5c2a0f2aeb81db907267f676b9c53`.
Installato con `box.sh install` su xfce e lxqt, poi `systemctl restart remotix`; `/proc/<MainPID>/exe` ha lo stesso sha256 su entrambi (xfce pid 683833, lxqt pid 4774).
Tutti i file di prova sono sul server in `/media/REMOTIX-UBUNTU/lavoro/riunito-xl/` (script: `sc.py`, `sc2.py` = copia con elenco processi/sessioni al ritorno dell'hook, `t1b.py`, `nl.py`, `drv-*.sh`, `suite.sh`; output grezzo in `out/`). Nessun codice del prodotto o degli strumenti originali e' stato toccato.

## Riepilogo: nessun FAIL

| Prova | Esito |
|---|---|
| 1 XFCE labwc assente, poi reinstallato | PASS |
| 2 LXQt hook PRELOCAL a desktop vivo e a desktop appena uscito | PASS |
| 3 LXQt tre utenti, nessun Lubuntu Update; Log Out a sessione staccata | PASS |
| 4 XFCE Log Out staccata x2, distacco/riattacco x2 | PASS |
| 5 lifecycle + prelocal su xfce (4+6) e lxqt (4+6) | PASS (20/20 righe) |

## Prova 1 - XFCE, labwc assente (`out/p1-nolabwc.txt`, `out/p1-reinstall.txt`, `out/p1-normal-attlogout.txt`)
- `apt-get remove -y labwc` nel box xfce (versione 0.9.3-1; solo labwc rimosso). Login di `rx1`: PASS.
- Pagina: «the server could not open your session, and it is not your mistake: try again in a moment, and if it happens again ask whoever administers the server - the precise reason is in its log» (frase generica).
- Dopo 4 s: sessioni logind 0, processi 0, `/run/user/1109` assente, cartella `~/.local/state/remotix` assente.
- Journal: «child  «rx1» passed PAM but the desktop cannot be born: XFCE needs `labwc` and it is NOT installed on this server - the administrator must install the package `labwc` ...  The child is NOT spawned, it gets 0x0E»; «farewell reason=0x0e ... detail=the desktop (XFCE) cannot start: `labwc` is not installed on this server».
- `apt-get install -y labwc`: versione 0.9.3-1, installato, `/usr/bin/labwc`.
- Login normale (`rxa`): «Admitted, new session, canvas 1344x768, desktop xfce»; Log Out attaccato: labwc via a 0.5 s, figlio via a 2.2 s, pagina «the session has ended: the programs were closed», 0 processi / 0 sessioni a 13.6 s.

## Prova 2 - LXQt, hook PRELOCAL (`out/p2-*.txt` primo lancio, `out/p2b-*.txt` con elenco di processi e sessioni al ritorno)
Hook = `/usr/libexec/remotix/remotix-local-login` con ambiente PAM simulato (come `check-prelocal.py`).
| Caso | hook | al ritorno dell'hook | a zero |
|---|---|---|---|
| desktop vivo, staccata (`p2b-alive-det`) | rc=0 in 8.9 s | nessun processo del desktop; sessioni logind: solo `Class=manager` (`Service=systemd-user`) | 0/0 a 25.6 s |
| desktop vivo, attaccata (`p2b-alive-att`) | rc=0 in 16.6 s | idem | 0/0 a 25.7 s |
| corsa Log Out + hook a 0.0 s (`p2b-race-0.0`) | rc=0 in 16.8 s | idem | 0/0 a 24.8 s |
| a 0.5 s (`p2b-race-0.5`) | rc=0 in 14.0 s | idem | 0/0 a 24.5 s |
| a 1.0 s (`p2b-race-1.0`) | rc=0 in 1.5 s | idem | 0/0 a 12.4 s |
- Journal a 0.0 e 0.5 s: «session [rls] there was no session to stop: no session name on the bus and no unit or process of the desktop left - the desktop is already gone, the close is done» seguito da «child [rls] the graphical session is closed: I am exiting too - the next attach will have a NEW child and desktop» (`out/p2-race-0.0.txt`, `out/p2-race-0.5.txt`).
- Nota onesta': i 9-17 s dell'hook sono la ritenzione di un figlio giovane da parte di RealtimeKit nel contenitore (noto, come nel rapporto staccata-uscita). Al ritorno dell'hook restano alcuni processi dell'infrastruttura dell'utente (at-spi, gvfs*, dbus-daemon, pipewire, mpris-proxy: il gestore utente systemd, non il desktop); nessun labwc/lxqt-*/panel/pcmanfm.

## Prova 3 - LXQt, tre utenti insieme (`out/p3-t1b.txt`, `out/p3-detlogout3.txt`, screenshot `out/t1-*.png`)
- `t1b.py` (utenti rl1, rl2, rl3; il primo staccato quando entra il secondo): in tutti i controlli a +10/+20/+40 s la lista dei processi `lubuntu-update` e' vuota; 0 occorrenze di "crashed" nell'output; riga nel journal: «lubuntu-update: not started in the remote session (it counts the processes of ALL users)». Fuori dalla sessione remota lo shim esegue il programma vero («+ exec /usr/bin/lubuntu-update --version»), `dpkg -V lubuntu-update-notifier` rc=0. Stesso utente di nuovo: «Admitted, resumed session»; utenti gia' usati: «new session». Nessun residuo in `/run/user/<uid>` dopo il Log Out; sessioni finali 0.
- NOTA: gli screenshot sono stati scattati, ma non li ho guardati uno a uno (finestre di crash: verificato solo con l'elenco processi e i log).
- Log Out dal menu (comando `org.lxqt.session logout` come l'azione del menu) a sessione STACCATA, utente `rlq`, x3: figlio via a 1.5, 1.3, 1.5 s (labwc a 0.5, 0.4, 0.4 s); 0 processi / 0 sessioni a 11.9, 12.3, 12.2 s; il login seguente e' ogni volta «Admitted, new session, canvas 1344x768, desktop lxqt» al primo colpo. Journal: «THE COMPOSITOR CLOSED THE INPUT CHANNEL AND THE SESSION NO LONGER ANSWERS» e «SIGTERM: the session is over - cleaned up».

## Prova 4 - XFCE (`out/p4-detlogout2.txt`, `out/p4-cycles2.txt`)
- Log Out a sessione staccata x2 (`rxb`): figlio via a 3.3 e 1.9 s (labwc 0.5 e 0.4 s); 0/0 a 13.5 e 12.6 s; il secondo login «new session». Journal: «§7.6: the session of «rxb» was ended from the desktop - sent away 1 clients with 0x10».
- Distacco/riattacco x2 + sosta staccata 60 s (`rxc`): 2/2 «Admitted, resumed session», stesso figlio (693109) e stesso labwc (693498) ad ogni giro e dopo la sosta; riattacco dopo la sosta «resumed», desktop assestato; nessuna riga ENDED / COMPOSITOR CLOSED / §7.6 / SIGTERM / no session to stop nel journal: nessun falso positivo.

## Prova 5 - suite, una alla volta (`out/suite-<de>-lifecycle.out`, `out/suite-<de>-prelocal.out`)
Lanciate con `check-lifecycle.py --box <de>` e `check-prelocal.py --box <de>` (xfce e lxqt in parallelo tra loro, mai due sullo stesso box).
- xfce lifecycle: PASS detach-reattach, kill-reattach, reattach-other-size, logout. xfce prelocal: PASS P1..P6.
- lxqt lifecycle: PASS detach-reattach, kill-reattach, reattach-other-size, logout. lxqt prelocal: PASS P1..P6.
- Il controllo `all.sh` conferma il comando `python3 check-<nome>.py --box <de>`; non ho usato `all.sh`.

## Stato finale dei due box
Pacchetto unione3a installato e servizio riavviato (sha binario verificato), `labwc` 0.9.3-1 presente su entrambi, nessuna sessione viva (solo quelle root dell'ssh), nessun drop-in di prova (resta `10-box-port.conf`). Utenti di prova (rx*, rl*, rm*) chiusi con `end_users`/Log Out. Creato da me anche `/tmp/xdeb-riu` nel server (estratto del .deb per lo sha). I box gnome e kde non sono stati toccati.
