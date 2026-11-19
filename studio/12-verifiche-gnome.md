# 12 - Verifiche mirate su GNOME 50 (box `rxu-gnome`, Ubuntu 26.04)

18 nov 2026, sera. Pacchetto installato: unione2 (sorgente: `/media/REMOTIX-UBUNTU/unione2/albero/src/`). Un solo agente sul box `gnome`;
sullo stesso server giravano in parallelo i lavori dell'agente XFCE (processi `runB.sh`/`xb.py` in `lavoro/verifiche-xfce`): può aver
caricato un po' la macchina, non ho notato effetti sui tempi.

Materiale grezzo (tutto sul server): `/media/REMOTIX-UBUNTU/lavoro/verifiche-gnome/`
- strumenti miei: `vg.py` (libreria sopra `prove/lib.py`), `vg-mon.sh` (monitor del box ogni 0,2 s), `runA.py`, `runB.py`, `runX.py` (C e rientro con
  sopravvivenza), `runD.py`, `runE.py`, `runG.py`, `runK.py`, `runK2.py`, `runF.py`, `runM.py`, `stall.py`, e gli aggregatori `agg*.py`, `sum.py`, `gap*.py`, `jf.py`;
- risultati: `res-A-*.jsonl`, `res-B-b1.jsonl`, `res-C-c1.jsonl`, `res-S-s*.jsonl`, `run-*.out`;
- journal completo di ogni prova: `j-<etichetta>.txt` (sezioni: journal utente, `====REMOTIX` servizio, `====USERAT` user@, `====LOGIND`);
- istantanee `*.png`, istantanee di ambiente `E-*.txt`.

## 0. Premessa: l'istantanea è affidabile? (la domanda lasciata dal giro)

MISURATO. `Rig.canvas_png()` fa `Page.captureScreenshot` di Chrome sul canvas: è un fotogramma nuovo ogni volta. Prova (utente nuovo `vgdn35964`,
`runD.py`, hash md5 abbreviato):
- sessione 1: +4 s `69563f94`, +8 s `ef90634c`, +16 s `db06eb50`, +30 s `db06eb50`, dopo un movimento del mouse `5df487a3`;
- sessione 2 (stesso utente): +4 s `800c335a`, +8 s `800c335a`, +16 s `800c335a`, +30 s `460e991f` (cambio di minuto dell'orologio), dopo il mouse `d21cf585`.
Le immagini cambiano quando lo schermo cambia (nuovi elementi, orologio, mouse) e sono uguali quando lo schermo è fermo: due istantanee identiche
(orologio compreso) a pochi secondi di distanza NON sono segno di un'immagine non aggiornata, se nello stesso minuto lo schermo è davvero fermo.
Il pezzo di prova finora ambiguo (notifica «Screen Lock disabled» identica a 10 e 40 s) è spiegato in D: la notifica resta ferma finché l'utente non fa nulla.
In più ho letto il contatore `painted`/`delivered` della pagina insieme al fotogramma (fermo anche lui quando lo schermo è fermo).

## A) Log Out nei primi secondi (voce 1) - FUNZIONA; sorpresa sul tempo di chiusura

### Come ho provato
Per ogni prova: utente (nuovo = creato apposta; usato = stesso utente già con sessioni, `vgubu`/`vguqu`), login dalla pagina, t0 = istante in cui sono veri
insieme «gnome-shell esiste» e «la pagina ha dipinto il primo fotogramma» (misurato a ~0,1 s), Log Out a t0+1, +2, +4, +8 s, 3 ripetizioni per tempo.
Un monitor nel box (`vg-mon.sh`) scrive ogni 0,2 s: sessioni logind dell'utente, processi, `gnome-shell`, stato di `user@UID.service`, stato di
`graphical-session.target` / `org.gnome.Shell@ubuntu.service` / `gnome-session-manager@ubuntu.service` nel gestore utente (letti con `setpriv`, senza
PAM, senza svegliare nessun gestore), esistenza di `/run/user/UID/remotix`. Due vie di Log Out:
1. «dal pulsante della pagina»: la pagina NON ha un pulsante visibile (il tasto di scelta rapida è stato tolto, `page.html:10250-10400`); ho chiamato
   dal browser la funzione `run_logout()` della pagina, che manda `TERMINATE_SESSION` (0x11) - è esattamente quello che farebbe il pulsante;
2. «dal desktop»: `gnome-session-quit --logout --no-prompt` eseguito come l'utente con il bus di sessione (=`org.gnome.SessionManager.Logout`).
Totale 48 prove (2 vie x 2 tipi di utente x 4 tempi x 3 ripetizioni), tutte in `res-A-*.jsonl`; tempi in secondi dal gesto.

| via | utente | desktop pronto -> gesto | pagina avvisata | `gnome-shell` sparito | TUTTO sparito (sessioni, processi, user@, `/run/user/UID/remotix`) |
|---|---|---|---|---|---|
| pulsante | nuovo | +1 | 0,2 | 5,5-5,9 | 16,1-31,5 |
| pulsante | nuovo | +2 | 0,1-0,2 | 5,4-6,1 | 28,9-30,3 |
| pulsante | nuovo | +4 | 0,2 | 5,4-5,9 | 27,6-28,1 |
| pulsante | nuovo | +8 | 0,2 | 0,8-5,5 | 11,9-24,9 |
| pulsante | usato | +1 | 0,2-0,6 | 5,5-5,7 | 30,6-31,4 |
| pulsante | usato | +2 | 0,2-0,3 | 5,6-5,9 | 29,7-30,5 |
| pulsante | usato | +4 | 0,2-0,3 | 5,5-6,0 | 16,0-28,7 |
| pulsante | usato | +8 | 0,2 | 5,5-5,6 | 23,7-24,8 |
| desktop | nuovo | +1 | 6,3-22,1 | 5,6-5,9 | 16,4-32,0 |
| desktop | nuovo | +2 | 18,5-20,1 | 5,5-5,9 | 28,8-30,2 |
| desktop | nuovo | +4 | 18,0-18,8 | 5,7-6,2 | 27,9-28,6 |
| desktop | nuovo | +8 | 1,6-14,4 | 1,1-5,5 | 11,4-24,4 |
| desktop | usato | +1 | 7,5-21,3 | 5,5-6,0 | 17,3-31,5 |
| desktop | usato | +2 | 7,1-20,4 | 5,8-6,0 | 17,2-30,5 |
| desktop | usato | +4 | 7,6-18,4 | 5,6-5,8 | 17,5-28,8 |
| desktop | usato | +8 | 14,0-14,8 | 5,6-5,9 | 24,0-25,0 |

Dal menu di sistema (una prova, `runM.py`): clic sul riquadro in alto a destra (1290,15) -> pulsante di spegnimento (1299,76) -> «Log Out…» (1013,211) ->
finestra «Log Out vgm1 / vgm1 will be logged out automatically in 60 seconds / Cancel - Log Out» (istantanea `M-step2.png`) -> clic su «Log Out» (762,431).
Conferma data a t0+10,9 s: pagina avvisata dopo 13,0 s («the session has ended: the programs were closed»), tutto sparito dopo 23,5 s. Funziona.
OSSERVAZIONE (non indagata, non cliccata): lo stesso menu (`M-step1.png`) mostra anche la voce «Power Off» sopra «Log Out…». Il registro di nascita di ogni
sessione dice: `child [..] ⛔⛔ FROM THIS SESSION THE MACHINE CAN BE POWERED OFF OR SUSPENDED (CanPowerOff=no CanReboot=no CanSuspend=(no answer) CanHibernate=(no answer) ): §4.7 says nobody must be able to do it ...` (child.c:9452).
Va guardato su una macchina vera (nel contenitore logind non risponde a `CanSuspend`).

### Fatti
- Si chiude SEMPRE, a qualunque tempo da 1 a 8 s: 48 prove su 48 con «nessuna sessione, nessun processo, `user@UID` inattivo, nessun `/run/user/UID/remotix`»
  (sonda diretta `loginctl`/`pgrep`/`systemctl is-active` a fine prova: `quiet_ok=True` in tutte). Nessun residuo, nessuna sessione `closing` rimasta,
  nessun «FOUND AGAIN», nessun «resumed session» nei journal di queste prove (`grep` su tutti i `j-*.txt`).
- `graphical-session.target` risulta inattivo 0,2-0,7 s dopo il gesto (letto dal monitor); `org.gnome.Shell@ubuntu.service` è fermo quando `gnome-shell` sparisce.
- `gnome-shell` NON esce da solo entro 5 s nel 46/48 dei casi: systemd lo uccide. Righe (prova `t1`, utente `vgn1`, journal utente):
  `Nov 18 20:43:33.427989 NIC-OS systemd[146880]: Stopping org.gnome.Shell@ubuntu.service - GNOME Shell...`
  `Nov 18 20:43:33.428186 NIC-OS gnome-shell[147197]: Shutting down GNOME Shell`
  `Nov 18 20:43:33.453027 NIC-OS gnome-shell[147197]: Launching DING process` (la shell rilancia l'estensione icone-sul-desktop mentre sta chiudendo)
  `Nov 18 20:43:38.610747 NIC-OS systemd[146880]: org.gnome.Shell@ubuntu.service: State 'stop-sigterm' timed out. Killing.`
  `Nov 18 20:43:38.610785 NIC-OS systemd[146880]: org.gnome.Shell@ubuntu.service: Killing process 147197 (gnome-shell) with signal SIGKILL.`
  `Nov 18 20:43:38.610980 NIC-OS systemd[146880]: org.gnome.Shell@ubuntu.service: Killing process 148723 (gjs) with signal SIGKILL.`
  (`Failed with result 'timeout'`). Nei 2 casi in cui esce subito (0,8-1,1 s) la chiusura totale è ~11-12 s. È rumore ma non guasto: la sessione si chiude comunque.
  Causa: SUPPOSTA (processo `gjs` di DING che non muore al SIGTERM); non ho verificato se succede su una sessione GNOME locale normale.
- La chiusura TOTALE ha tre pezzi (tutti misurati nel journal utente di `A-bn-new-d1-r1`, utente `vgnbn1`):
  1. `session [vgnbn1] asking the graphical session to exit (Logout 1)` 20:45:24.430 -> `the graphical session has exited` 20:45:25.358 -> `scope leftovers after the exit: SIGTERM to 1 processes (gnome-session-i)` 20:45:27.360 -> `R1/R2 ... the user manager goes back to how it was` 20:45:27.835 -> `child [vgnbn1] the input channel closes` 20:45:27.837;
  2. POI IL FIGLIO RESTA MUTO per 17 s: la riga successiva è `child [vgnbn1] audio turns OFF: 0 blocks sent, 0 lost, 205632 frames overflowed` 20:45:45.132 e `the child of «vgnbn1» has dismantled the stage and is exiting` 20:45:45.143;
  3. 10 s dopo l'uscita del figlio il gestore utente si ferma (`Activating special unit exit.target` 20:44:04.82 nella prova `t1`, dopo `the child ... is exiting` 20:43:54.815): è il `UserStopDelaySec=10` di logind (`/etc/systemd/logind.conf:26` commentato = default 10 s). Normale.

### Il silenzio del figlio (punto 2): misurato, causa NON provata
- Misurato su 24 prove `pulsante`: il figlio esce a **21,3-22,4 s dal primo fotogramma del desktop** in 19 prove su 24, indipendentemente da quando si è premuto Log Out (1, 2, 4 o 8 s: in secondi dal gesto sono 20,9 / 19,3 / 17,3 / 14,4 ...) (`gap2.py`). Nelle altre 5 esce 5,5-9,5 s dopo il gesto. Con Log Out a 30 s dal desktop (prove S, sotto) il figlio esce entro ~1-6 s: niente silenzio.
- Durante il silenzio i fili del figlio (`/proc/<pid>/task/*/comm`, `stall.py`, 2 s di passo): dopo ~3,6 s dal gesto i fili `remotix-cattura` e `remotix-appunti` spariscono (= `unmount_stage` finito), restano `remotix-suono` (thread loop di PipeWire), `data-loop.0`, `module-rt`, `gdbus`, `gmain`, `dconf worker`; il figlio muore tutto in una volta a ~t0+22.
- Il silenzio finisce nel punto del codice `child.c:12430` `audio_rule_child(0)` -> `sound_listen_stop()` (`sound.c`, righe ~450-520: `wait_callback` (max 2 s), `pw_thread_loop_lock`, `pw_stream_destroy`): la riga `audio capture stopped` (che sta dopo `pw_stream_destroy`) esce nello stesso istante di `audio turns OFF`. Quindi il blocco è lì o appena prima: SUPPOSTO fra i tre, non ho potuto fissarlo (nel box mancano `gdb`/`strace` e CAP_SYS_PTRACE; sull'host non sono root).
- Perché «t0+22 s»? Ipotesi di lavoro: una chiamata D-Bus bloccante con timeout di 25 s (default) fatta dal thread audio all'avvio (RealtimeKit: nel box `rtkit-daemon` è `failed` ed è un limite noto dei contenitori, vedi la riga `P1-hook-closes-desktop` di `prelocal.out` dei giri precedenti: «RealtimeKit cannot start in a container and holds a young child's exit for 25 s»). NON provata: nel journal di `rtkit-daemon` fra 20:43 e 20:46 non c'è nessuna riga. (Nota: per prova ho fatto `systemctl start rtkit-daemon`: ha fallito di nuovo, `Main process exited, code=exited, status=1/FAILURE`, l'unità era già `failed`.)
- Conseguenza per l'utente, MISURATA: se si esce dal DESKTOP (menu di sistema, o `gnome-session-quit`) nei primi ~20 s, il client resta davanti all'ULTIMA IMMAGINE DEL DESKTOP congelata, senza alcun messaggio, finché il figlio non esce:
  `runF.py` (Log Out a t0+3): fotogramma con lo stesso hash `169c9dd9` a +2, +5, +8, +12, +16 s (`painted=7 delivered=7` fermi), a +20 s `form=True`, `outcome='the session has ended: the programs were closed'`. (Le immagini `F-quit-*.png`.) Con il pulsante della pagina il client è avvisato dopo 0,2 s (il saluto 0x10 parte prima). Il registro del servizio lo dice a modo suo: `Nov 18 20:45:29.875943 ... input [vgnqn1] ⚠ the compositor CLOSED the input channel` -> `child [vgnqn1] ⚠ THE COMPOSITOR CLOSED THE INPUT CHANNEL AND THE SESSION NO LONGER ANSWERS ... Dismantling the stage` (29,876) -> nessuna riga per 15,3 s -> `⭐ 1.5.5: SIGTERM from pid 154435, not our parent` (45,132).
- Su una macchina vera, se `rtkit` funziona, il silenzio probabilmente non c'è (SUPPOSTO: nelle 5 prove su 24 senza silenzio e nelle prove a +30 s il figlio esce in 1-6 s). Va rimisurato fuori dal contenitore.

### Conclusione A
**FUNZIONA** (chiusura completa e senza residui in 48/48). **Difetto d'esperienza a livello ambiente-sospetto (NON CAPITO nel dettaglio):** il figlio non esce prima di ~22 s dal desktop; dal desktop il client vede l'ultima immagine congelata fino a ~20 s senza messaggio; dal pulsante no.
Cura proposta (non applicata): (1) per ora nessuna sulla chiusura; (2) se si conferma anche fuori dal box, nel ramo di `child.c:11540-11560` (finestra «THE COMPOSITOR CLOSED THE INPUT CHANNEL ... Dismantling the stage») avvisare subito il genitore/client che la sessione è finita (come fa già `session_ended_by_child`, `main.c:2108`, ma quando il figlio ESCE), invece di aspettare l'uscita; (3) per trovare la riga bloccata: provare `strace -f -p <figlio>` / `gdb -batch -ex 'thread apply all bt'` su un box con `--cap-add SYS_PTRACE`, durante il silenzio (dura ~15-20 s a ogni prova).

## B) Rientro subito dopo il Log Out (voce 2) - FUNZIONA, con un messaggio sbagliato in un caso

Guardia `inactive_unit()` (`session.c:3716-3790`): su GNOME controlla tre unità del gestore utente (`gnome-session-manager@ubuntu.service`, `gnome-session-restart-dbus.service`, `graphical-session.target`) con `unit_stopped()`; se una non è ferma, risponde «occupato» e il chiamante (`session.c:7688`) rifiuta la nascita e la ritenta (`BIRTH_REIN_MS` 12 s, `child.c:5495`). In TUTTI i miei journal (≈100 prove) la riga `the PREVIOUS graphical session has not ended yet` e `the user manager is SHUTTING DOWN` NON compaiono mai (0 file su tutti i `j-*.txt`): la guardia non è mai scattata. Il rientro è già fermato PRIMA da un'altra regola: `main.c:1161-1175`: finché il figlio dell'utente non è uscito (`closing`), il nuovo login è accettato da PAM ma riceve `0x0E`.

### Prove `B-b1` (utente `vgrb1`, sessione vissuta ~12 s, Log Out dal pulsante, poi login dopo 0,3/1/3/10 s dal momento in cui la pagina mostra «ended»; tempi reali 1,8 / 2,5 / 4,5 / 11,5 s perché la pagina va riaperta e il login dura 1,2 s) - `aggb.py`
| gap | r1 | r2 | r3 |
|---|---|---|---|
| 0,3 (reale 1,8 s) | ammesso, desktop dopo 2,2 s | RIFIUTATO | RIFIUTATO |
| 1 (2,5 s) | RIFIUTATO | RIFIUTATO | ammesso, 2,2 s |
| 3 (4,5 s) | ammesso, 2,2 s | RIFIUTATO (testo: «the session has ended») | RIFIUTATO |
| 10 (11,5 s) | ammesso, 1,5 s | ammesso, 2,9 s | ammesso, 2,9 s |
- «Ammesso» = `Admitted, new session, canvas 1344×768, desktop gnome` e desktop vero dopo 1,5-2,9 s dall'ammissione: NESSUNO schermo vuoto di 27 s in nessuna prova (campioni a 0,7 s con giudizio sull'immagine, `samples` in `res-B-b1.jsonl`).
- «RIFIUTATO» = testo mostrato all'utente: `the server could not open your session, and it is not your mistake: try again in a moment, and if it happens again ask whoever administers the server - the precise reason is in its log`. Quindi NON schermo vuoto: un messaggio, ma generico (non dice «il desktop precedente si sta chiudendo»; il motivo preciso è solo nel registro). Righe del servizio (`j-B-b1-button-g1-r1.txt`, utente `vgrb1`):
  `Nov 18 20:51:17.848751 ... rcp [vgrb1] ⭐ §7.6: vgrb1 asked to LEAVE ...`
  `Nov 18 20:51:20.458213 NIC-OS remotix[125606]: rootside ⭐ PAM said YES to «vgrb1»: a grant is minted - single use, 30 s, bound to «vgrb1» from «127.0.0.1»`
  `Nov 18 20:51:20.458658 NIC-OS remotix[125616]: child ⛔ «vgrb1» is ADMITTED while its desktop is closing: the previous desktop of «vgrb1» is still closing: retry in a few seconds.  ⭐ It gets 0x0E`
  `Nov 18 20:51:20.458745 ... wt ⛔ sent away 1 clients of «vgrb1» with 0x0e: the previous desktop ... ⚠ If here you read ZERO, the no reached NOBODY and the user is in front of a black page`  (qui: 1 client, quindi il «no» è arrivato)
  `Nov 18 20:51:27.396895 ... child the child of «vgrb1» (uid 1054, pid 258262, serial 29) is leaving: Connection reset by peer` (il figlio vecchio esce 7 s dopo il rifiuto).
- Quando è ammesso, il figlio vecchio era già uscito (riga `has been REAPED` prima di `PAM said YES`) nei casi che ho letto: l'ammissione è legata all'uscita del figlio, non alle unità.
- Finestra di rifiuto = tempo di uscita del figlio vecchio. Con sessione giovane (<22 s dal desktop) è quella di A (fino a ~22 s dal desktop). Con sessione vecchia è breve: vedi sotto.

### Prove `S` (sessione vissuta 30 s, poi Log Out, login dopo 0,3/1/3/10 s (pulsante) e 0,3/3 s (desktop), poi 33 s di osservazione, 3+2 ripetizioni) - 16 prove su 16
`aggs.py`/`res-S-s1.jsonl`, `res-S-s2.jsonl`: TUTTE ammesse come `new session`, desktop dopo 2,1 s, e per 33 s dopo: sessione ancora attiva, `gnome-shell` presente (1), 2 sessioni logind, `user@UID` attivo, immagine non uniforme. Cioè il nuovo desktop NON viene ucciso quando il vecchio gestore utente arriva ai suoi 10 s di chiusura (misurato con rientro a 0,3 s). Via desktop: pagina avvisata dopo 0,7-1,2 s (nessun silenzio a quell'età).

### Un messaggio sbagliato (difetto piccolo, provato)
Prova `B-b1-button-g3-r2`: login a 4,5 s -> rifiutato con `0x0E` (20:55:39.120), poi 1 s dopo lo STESSO client riceve un secondo saluto con un altro motivo, e la pagina mostra «the session has ended: the programs were closed», che è falso (il suo login non ha mai avuto una sessione):
  `Nov 18 20:55:40.150496 ... child the child of «vgrb1» (uid 1054, pid 323054, serial 44) is leaving: Connection reset by peer`
  `Nov 18 20:55:40.150526 ... rcp [vgrb1] farewell reason=0x10 detail=the graphical session has ended state=wait-verdict`
Causa provata nel codice: quando il figlio vecchio esce, `main.c:2300-2310` (e `session_ended_by_child` `main.c:2108-2127`) chiamano `wt_dismiss_user(user, RCP_SESSION_TERMINATED, "the graphical session has ended")` su TUTTI i client di quell'utente, compreso il nuovo login già rifiutato in attesa del verdetto (`state=wait-verdict`).
Cura proposta: far partire il saluto 0x10 solo per i client collegati al figlio che esce (numero di serie del figlio, `serial 44` nella riga) e non per quelli in `wait-verdict`; oppure lasciare che quest'ultimo tenga il suo 0x0E. File: `src/main.c` funzione che gestisce l'uscita del figlio (righe 2285-2315) e `wt_dismiss_user`.

### Conclusione B
**FUNZIONA** per sessioni di almeno 30 s (rientri a 0,3-10 s sempre ammessi e sani). **Difetto lieve** per sessioni giovani (<22 s): rifiuto con messaggio generico; e un messaggio sbagliato nel caso 3 s/r2. Lo «schermo vuoto fino a 27 s senza messaggio» di G4 NON è riprodotto con rientri veri: G4 forzava a mano il bersaglio.

## C) Log Out dal desktop con sessione STACCATA - su GNOME NON succede

Procedura (`detached_logout` in `vg.py`, `res-C-c1.jsonl`): login, 12 s di quiete, chiusura del browser (la sessione resta, nessun client), 3 s, `gnome-session-quit` dal box; poi login nuovo (a) appena `gnome-shell` è sparito +1 s ("shellgone") oppure (b) a chiusura completa ("quiet"). 3 ripetizioni per tipo.
| prova | `gnome-shell` sparito | figlio vivo al login | login dopo | esito per l'utente |
|---|---|---|---|---|
| shellgone r1 | 5,9 s | 0 | 7,2 s | `Admitted, new session`, desktop dopo 2,1 s |
| quiet r1 | 1,07 | 0 | 11,6 | `Admitted, new session`, 2,1 s |
| shellgone r2 | 1,07 | 0 | 2,2 | `Admitted, new session`, 3,1 s |
| quiet r2 | 1,16 | 0 | 11,8 | `Admitted, new session`, 2,1 s |
| shellgone r3 | 5,74 | 1 (uscì subito dopo) | 6,9 | `Admitted, new session`, 2,1 s |
| quiet r3 | 1,09 | 0 | 11,6 | `Admitted, new session`, 2,1 s |
Dopo ogni nuovo login: `shell=1`, `child=1`, `graphical-session.target` attivo, 2 sessioni logind (la `manager` e la `user` remotix). Nessun «resumed session» senza desktop, nessun figlio rimasto vivo per minuti.
Spiegazione (misurata): con la sessione staccata l'audio è già spento, quindi il silenzio di ~22 s di A non c'è; il figlio esce entro ~1-6 s.
**FUNZIONA.** (La variante XFCE «figlio vivo + resumed senza desktop» non si riproduce su GNOME.)

## D) Notifica «Screen Lock disabled» - causa trovata, cura proposta

### Chi la emette e quando: MISURATO + LETTO NEL CODICE
- La emette `gnome-shell` stesso, funzione `_handleLockScreenWarning()` di `js/ui/main.js` (estratta con `gresource extract /usr/lib/gnome-shell/libshell-18.so /org/gnome/shell/ui/main.js`, righe 421-445 e 386):
  ```
  async function _handleLockScreenWarning() {
      const path = `${global.userdatadir}/lock-warning-shown`;
      const file = Gio.File.new_for_path(path);
      const hasLockScreen = screenShield !== null;
      if (hasLockScreen) { ... file.delete_async ... }
      else {
          try { if (!await file.touch_async()) return; } catch (e) { logError(e); }
          notify(_('Screen Lock disabled'), _('Screen Locking requires the GNOME display manager'));
      }
  }
  ```
  chiamata all'avvio della shell se `sessionMode.currentMode !== 'gdm' && !== 'initial-setup'` (riga ~386). `screenShield` esiste solo se `LoginManager.canLock()` (riga 252), che chiede sul bus di sistema `org.gnome.DisplayManager` `Version >= 3.5.91` (`misc/loginManager.js`): nei nostri desktop remoti GDM non c'è, quindi `screenShield === null` sempre.
- NON dipende da nessuna chiave dconf: il codice non legge `disable-lock-screen`, `lock-enabled`, `ubuntu-lock-on-suspend`, `DCONF_KEYS` (`session.c:1635-1657`) non c'entra (letto, non provato togliendole).
- Compare SOLO la prima volta di ogni utente, perché `file.touch_async()` (`Shell.util_touch_file_async`) restituisce `true` solo se crea il file `~/.local/share/gnome-shell/lock-warning-shown`; già esistente -> `return` senza notifica. Provato: utente nuovo `vgdn35964` sessione 1: istantanea a +8 s CON la banda «System - Just now - Screen Lock disabled - Screen Locking requires the GNOME display manager» (`D-s1-08s.png`, `D-s1-16s.png`, `D-s1-30s.png` stesso hash a 16 e 30 s); file creato `2026-11-18 21:06:14` e mai più toccato; sessione 2 dello stesso utente: nessuna banda a +8 s (`D-s2-08s.png`). I file `lock-warning-shown` esistono (0 byte) nelle home di tutti i miei utenti.
- La banda resta ferma per più di 30 s finché l'utente non fa qualcosa (la shell la tiene finché c'è un'attività): è la spiegazione delle due immagini identiche del giro precedente. Dopo un movimento del mouse l'immagine cambia (`D-s1-after-move.png`) ma nell'istantanea la banda è ancora lì (30+ s).

### Debian (SOLA LETTURA)
`/home/nicfio/Documenti/REMOTIX-DEBIAN/src/session.c`: stesse chiavi (`disable-lock-screen`, `lock-enabled` righe 1642-1649; non c'è `ubuntu-lock-on-suspend`, che è solo di Ubuntu); nessun trattamento della notifica (`grep -i "lock-warning\|Screen Lock disabled"` non trova nulla né in Debian né nel mio albero). Quindi GNOME 48 su Debian era trattato come Ubuntu. Se Debian la mostrasse davvero: NON verificato (nessun box Debian), ma il percorso di codice è lo stesso della shell (SUPPOSTO per GNOME 48).

### Cura proposta (NON applicata)
- Strada pulita e nello stile del codice (come per LXQt/XFCE che scrivono nella home, `session.c:6512`, `6653`, e come i segni `~/.local/state/remotix/...`): in nascita, per GNOME, se manca, creare il file vuoto `~/.local/share/gnome-shell/lock-warning-shown` (cartella `~/.local/share/gnome-shell` con modo 0700) PRIMA di lanciare `gnome-session`. Effetto: `touch_async()` -> false -> nessuna notifica. Costa 5 righe in `session.c` nel ramo GNOME della preparazione della sessione; il file è identico a quello che la shell avrebbe creato da sé.
- Strade scartate: (a) chiave dconf: non esiste; (b) `org.gnome.desktop.notifications show-banners=false`: spegnerebbe TUTTI i banner (compresi quelli utili); (c) fingere `org.gnome.DisplayManager` sul bus di sistema: troppo pesante e rischioso per la regola «nessun blocco schermo».
- Costo/rischio: basso; verificare con `runD.py` (utente nuovo, istantanea a +8 s senza banda).

## E) Linger acceso (voce 9) - variabili e processi RIMASTI (difetto lieve), seconda sessione pulita

Prova `runE.py` (utente nuovo `vgl36106`, `loginctl enable-linger`, 2 sessioni remote con Log Out dal pulsante e 45 s di attesa dopo ciascuna; istantanee dell'ambiente in `E-*.txt`; alla fine `disable-linger`, il gestore si ferma `Deactivated successfully`, `/var/lib/systemd/linger` vuoto).
- Base (gestore utente senza sessione): 13 variabili (`DBUS_SESSION_BUS_ADDRESS GPG_AGENT_INFO GTK_MODULES HOME LANG LOGNAME PATH QT_ACCESSIBILITY SHELL SSH_AUTH_SOCK USER XDG_DATA_DIRS XDG_RUNTIME_DIR`).
- Durante la sessione si aggiungono: `DCONF_PROFILE DESKTOP_SESSION GNOME_DESKTOP_SESSION_ID=this-is-deprecated PWD QT_IM_MODULE=ibus QT_IM_MODULES=$'wayland;ibus' WAYLAND_DISPLAY=wayland-0 XDG_CURRENT_DESKTOP=ubuntu:GNOME XDG_MENU_PREFIX=gnome- XDG_SESSION_DESKTOP=ubuntu XDG_SESSION_TYPE=wayland XMODIFIERS=@im=ibus`, e `SHELL=` vuota, `XDG_DATA_DIRS` allungata, `PATH` senza il doppio `/snap/bin`.
- DOPO il Log Out (45 s) restano nel gestore utente rispetto alla base: `GNOME_DESKTOP_SESSION_ID=this-is-deprecated`, `QT_IM_MODULE=ibus`, `QT_IM_MODULES=$'wayland;ibus'`, `XMODIFIERS=@im=ibus`, `PWD=/home/<utente>` (cinque). REMOTIX ripulisce `DCONF_PROFILE, DESKTOP_SESSION, XDG_*, WAYLAND_DISPLAY`, ripristina `SHELL`/`PATH`/`XDG_DATA_DIRS` (riga `R1/R2 ... org.gnome.Shell@ubuntu.service.d/zz-remotix-monitor.conf -DCONF_PROFILE -XDG_MENU_PREFIX -DESKTOP_SESSION -XDG_CURRENT_DESKTOP -XDG_SESSION_DESKTOP -XDG_SESSION_TYPE -WAYLAND_DISPLAY ~XDG_DATA_DIRS ~SHELL ~PATH`) ma non conosce le quattro di GNOME 50 (`GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULE`, `QT_IM_MODULES`, `XMODIFIERS`): coincide con la previsione della voce 9. Dopo la seconda sessione l'elenco è IDENTICO (non si accumula).
- Processi rimasti: `systemd --user`, `(sd-pam)`, `dbus-daemon`, `ssh-agent`, `gcr-ssh-agent` (unità `ssh-agent.service`, `gcr-ssh-agent.service` attive) e le slice `app-gnome\x2dsession\x2dmanager.slice`, `background.slice`; fermati e NON rimessi: `pipewire`, `wireplumber`, `pipewire-pulse`, `filter-chain`, `mpris-proxy` (i socket `pipewire*.socket` tornano `listening`). Rimasta `/run/user/UID/remotix/dconf` (profilo neutralizzato, cartelle `gnome-shell`, `at-spi`, `gvfs`...). `user.control` è vuota (drop-in tolti).
- Seconda sessione remota: parte pulita (`Admitted, new session`, desktop normale `E-s2-desktop.png`, ambiente durante la sessione identico a quello della prima: `diff` vuoto), `gnome-shell` e tutti i servizi della sessione ripartiti.
- Ricaduta (SUPPOSTA, non provata): una sessione locale successiva dello stesso utente con linger erediterebbe `QT_IM_MODULE(S)`, `XMODIFIERS`, `GNOME_DESKTOP_SESSION_ID` (uguali a quelle che una sessione GNOME locale imposta comunque: effetto probabilmente nullo su GNOME; su XFCE/KDE locale sarebbe una variabile in più).
Conclusione E: **DIFETTO LIEVE**, causa provata: la lista da ripulire (`OUR_VARIABLES`, `session.c:4041-4060`) non contiene le quattro variabili che il leader 50 immette. Cura proposta: aggiungere `GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULE`, `QT_IM_MODULES`, `XMODIFIERS` (e `PWD` se si vuole) alla lista di `unset-environment` fatta alla chiusura (stessa funzione che oggi toglie `WAYLAND_DISPLAY`...). Controllare prima che l'accesso locale non le imposti da sé (se sì, meglio RIPRISTINARE il valore di base che toglierle).

## F) `user@UID` che fallisce per `mpris-proxy` (voce 19) - su GNOME NON si riproduce dopo il Log Out; causa vera trovata per un altro caso

Misurato:
- In tutte le chiusure dopo Log Out (62 `j-*.txt` con la sezione `====USERAT`): `systemd[1]: user@UID.service: Deactivated successfully.` Nessun `timed out` di `user@`. `mpris-proxy` termina da solo e subito con `mpris-proxy.service: Main process exited, code=exited, status=1/FAILURE` / `Failed with result 'exit-code'` (128 righe uguali), nello stesso istante in cui `gnome-session-restart-dbus.service` ferma `dbus.service` (`Nov 18 20:43:38.701378 ... Stopping dbus.service`; `20:43:38.702441 ... mpris-proxy.service: Main process exited, code=exited, status=1/FAILURE`): `mpris-proxy` perde il bus di sessione e esce, non si blocca. Quindi su GNOME dopo il Log Out: nessun ritardo dovuto a `mpris-proxy`.
- Quello che invece produce `user@UID.service: Failed with result 'timeout'` è un gestore utente fermato mentre ha ancora vivo il bus e i servizi audio: riprodotto con un utente nuovo `vgf6419` (linger, 5 s, `disable-linger`; script `vg-f.sh`):
  `Nov 18 21:13:45.011763 NIC-OS systemd[1]: Stopping user@1072.service - User Manager for UID 1072...`
  `Nov 18 21:13:45.012504 NIC-OS systemd[628701]: Stopping filter-chain.service - PipeWire filter chain daemon...`
  `Nov 18 21:13:45.012575 NIC-OS systemd[628701]: Stopping mpris-proxy.service - Bluetooth mpris proxy...`
  `Nov 18 21:13:45.012636 NIC-OS systemd[628701]: Stopping pipewire-pulse.service - PipeWire PulseAudio...`
  `Nov 18 21:13:45.026610 NIC-OS systemd[628701]: Stopped mpris-proxy.service - Bluetooth mpris proxy.`   (14 ms!)
  `Nov 18 21:13:50.098514 NIC-OS systemd[1]: user@1072.service: State 'stop-sigterm' timed out. Killing.`
  `... Killing process 628701 (systemd) / 628727 (pipewire) / 628728 (pipewire-pulse) / 628726 (wireplumber) / 628724 (pipewire) / 628723 (dbus-daemon) with signal SIGKILL`
  `Nov 18 21:13:50.139062 NIC-OS systemd[1]: user@1072.service: Failed with result 'timeout'.`
  Cioè: `mpris-proxy` si ferma in 14 ms e NON è lui a bloccare; a non fermarsi in 5 s sono `filter-chain` e `pipewire-pulse` (mai un «Stopped» per loro). Il limite di 5 s è `TimeoutStopSec=5` messo da Ubuntu in `/usr/lib/systemd/system/user@.service.d/timeout.conf` («Avoid long hangs during shutdown if user services fail/hang due to X.org going away too early»; `dpkg -S`: pacchetto `systemd`). Il testo della nota di XFCE («User job mpris-proxy.service/stop running») è il modo in cui systemd elenca i lavori ancora in corso: `mpris-proxy` può comparire senza essere la causa. Perché `pipewire-pulse`/`filter-chain` non si fermano nel contenitore: NON capito (ipotesi: stesso problema RT/rtkit di A; non provata).
- Allunga il tempo prima del rientro? NO, misurato: il rientro è fermato dal figlio (B), non da `user@`; il nuovo desktop nasce mentre il vecchio `user@` finisce i suoi 10 s (prove S: rientro a 0,3 s, 33 s di vita sana).
Conclusione F: **NON È UN DIFETTO DEL PRODOTTO su GNOME**; la voce 19 va riscritta: «`user@UID` va in timeout dopo 5 s solo se si ferma il gestore con pipewire-pulse/filter-chain ancora vivi (contenitore); `mpris-proxy` è innocente». Rimane da vedere su macchina vera.

## G) Se restava tempo

### G1 - tasto tenuto premuto (voce 14): FUNZIONA (quanto provato)
`runG.py` (utente `vgk36311`, finestra di prova `window.py` in sessione, tasto `x` con Chrome DevTools):
- una sola pressione di 3 s: nella finestra arriva 1 solo carattere (nessuna ripetizione remota da una pressione singola: la ripetizione la fa il browser);
- pressione + 74 ripetizioni automatiche (`autoRepeat`, ogni 33 ms per 2,5 s) + rilascio: `HOLD ... x typed during=75, right after release=75, 2.5 s later=75 (growth after release: 0)`: 75 caratteri per 75 pressioni, niente cresce dopo il rilascio;
- tasto `y` tenuto premuto (41 pressioni) e browser chiuso senza rilascio: 2 s e 5 s dopo il distacco il conteggio resta 41 (niente tasto rimasto premuto); riattacco `Admitted, resumed session`, ancora 41 dopo altri 6 s. Il registro mostra `release at detach` nel distacco.
NON provato: il caso «Mutter rifà i dispositivi con il tasto già premuto» (voce 14 vera): serve il banco `06-b33` che non c'è nell'albero Ubuntu.

### G2 - `scaling-factor=2` e `text-scaling-factor` (voce 26)
- `text-scaling-factor 1.5` (impostato con `gsettings` nella sessione): il desktop si ingrandisce (barra più alta, icona accessibilità; `K-1-text15.png`), sessione e ingresso normali. FUNZIONA.
- `scaling-factor 2` impostato a sessione già avviata (`gsettings`): nessun effetto visibile (Mutter 50 su Wayland non lo applica al monitor virtuale; immagini `K-2-scale2-*.png` identiche a quella con testo 1,5) e il prodotto non dice niente (la guardia 2 legge la scala SOLO quando monta il palco).
- `scaling-factor 2` presente PRIMA della nascita (scritto con `dconf write` nel file dell'utente, `runK2.py`): la guardia rifiuta di prendere il palco, come su Debian (stesso codice `child.c:9070-9130`). Righe (servizio e utente):
  `capture [vgs1] ⛔ SCALE 2.000 instead of 1.0 - the input coordinate space does NOT match the stream's pixels, and the pointer will go elsewhere with nothing saying so.  Cure: gsettings set org.gnome.desktop.interface scaling-factor 0 (DECISIONS.md §5.0-sexies)`
  `child [vgs1] ⛔⛔ SCALE 2.000 on OUR monitor «Meta-0» instead of 1.0 ... ⇒ I am NOT taking the stage (guard 2 of DECISIONS.md §5.0-sexies)`
  Ma per l'utente: ammesso come `Admitted, new session, canvas 1344x768` e poi NESSUN fotogramma per più di 40 s (`painted=0 delivered=0` a +10, +16, +26, +41 s): schermo vuoto senza testo (il motivo c'è solo nel registro del server). **DIFETTO d'esperienza (medio-basso)** sia su Debian sia su Ubuntu (stesso codice); su Ubuntu è più probabile perché l'installer può impostare la scala 2 su schermi ad alta risoluzione. Cura proposta: quando la guardia 2 rifiuta, mandare al client un motivo leggibile (un codice di saluto già esistente o una scritta nel canvas) invece del silenzio; file `child.c` ramo di `child.c:9110-9128` (campo `p.fault`) e `rcp.c`.

## Riepilogo delle conclusioni
| compito | esito |
|---|---|
| A Log Out presto | FUNZIONA (48/48 chiusure complete, nessun residuo); la chiusura totale dura 11-32 s; dal desktop nei primi ~20 s il client vede l'ultima immagine congelata senza messaggio (silenzio del figlio ~22 s dal desktop; causa NON provata, sospetto ambiente/RealtimeKit) |
| B rientro | FUNZIONA con sessioni >=30 s (rientro 0,3-10 s sempre sano); con sessioni <22 s rifiuto con messaggio generico fino a ~22 s; un messaggio falso «session has ended» (`main.c:2300-2310`); schermo vuoto 27 s NON riprodotto |
| C staccata | FUNZIONA (6/6 nuovo login = sessione nuova con desktop; figlio sparisce in 1-6 s) |
| D notifica | DIFETTO lieve, causa provata (shell: `canLock()` falso senza GDM, solo al primo avvio dell'utente); cura: creare `~/.local/share/gnome-shell/lock-warning-shown` |
| E linger | DIFETTO lieve, causa provata (4 variabili non in `OUR_VARIABLES`); la seconda sessione parte pulita |
| F mpris-proxy | NON riprodotto dopo Log Out; riprodotto altrove: i colpevoli sono `pipewire-pulse`/`filter-chain` col limite di 5 s di Ubuntu; non allunga il rientro |
| G tasto / scala | tasto FUNZIONA; `scaling-factor` prima della nascita: rifiuto giusto ma schermo vuoto senza messaggio |

## Che cosa NON è stato possibile vedere
- La riga esatta che blocca il figlio ~22 s (A): niente `gdb`/`strace`/CAP_SYS_PTRACE nel box.
- Se il silenzio di ~22 s c'è anche fuori dal contenitore (con `rtkit` funzionante).
- Se Debian GNOME 48 mostra la stessa notifica (nessun box Debian).
- Il caso «Mutter rifà i dispositivi con tasto premuto»; la voce «Power Off» del menu non è stata cliccata.
- Nessuna prova ha usato un secondo client contemporaneo (le prove sono a client unico).

## Che cosa ho creato / cambiato nel box (e com'è finito)
- Utenti di prova (restano in `/home`, senza sessioni, senza processi, senza linger): `vgn1`, `vgn{bn,qn}1..12`, `vgubu`, `vguqu`, `vgrb1`, `vgxs1`, `vgxs2`, `vgxc1`, `vgstall`, `vgdn35964`, `vgl36106`, `vgk36214`, `vgk36311`, `vgf6419`, `vgm1`, `vgs1`, `vgq1`. In `vgs1`: `scaling-factor` riportato a 0 e `text-scaling-factor` ripristinato al valore di fabbrica (`dconf reset`).
- File nel box (`/tmp`): `vg-mon.sh`, `vg-mon-*.txt`, `vg-keep-*.txt`, `vg-dump.sh`, `vg-f.sh`, `vgs-env.sh`, `vgs-mk.py`, `vg-quit.out`, la cartella `vg-res/` (estratto dei JS di gnome-shell per la lettura). Sull'host del server: `/tmp/vg-x.sh`, `/tmp/vg-f.sh`.
- Stato di sistema toccato: `loginctl enable-linger`/`disable-linger` per `vgl36106`, `vgf6419`, `vgs1` (tutti tolti: `/var/lib/systemd/linger` vuoto); un `systemctl start rtkit-daemon` (fallito, l'unità era già `failed`).
- Un tentativo di login con nome utente inesistente `vgdummy` (errore mio nel primo `runK2.py`, esito «incorrect username or password»): UN errore di password da 127.0.0.1, poi decine di login giusti; nessun blocco scattato.
- Nessun pacchetto installato/rimosso. Nessun file del prodotto o di `prove/` modificato. Nessun commit.
- Stato finale verificato: `loginctl list-sessions` = solo sessioni root; `loginctl list-users` = solo root; nessun processo di utenti `vg*`; nessun linger.
