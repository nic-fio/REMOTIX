# Verifiche sul box XFCE (Xubuntu 26.04, `rxu-xfce`, REMOTIX porta 8823) — 18 nov 2026, sera

Pacchetto in prova: `unione2`. Sorgente corrispondente: `/media/REMOTIX-UBUNTU/unione2/albero/src/`. Albero locale `src/` (stesso codice dei file letti).
Orari: UTC (il box). Misura e diagnosi: **nulla è stato corretto** (né prodotto né `prove/`). Strumenti miei: `/media/REMOTIX-UBUNTU/lavoro/verifiche-xfce/` (server).
Convenzione: «MISURATO» = visto dal vivo con i numeri; «LETTO» = letto nel codice; «SUPPOSTO» = ragionamento non provato.

## Riassunto in una pagina

| Compito | Esito |
|---|---|
| A. Log Out a sessione staccata: figlio rimasto vivo | **DIFETTO, DUE CAUSE PROVATE** (riprodotto 3 volte su 3): (1) `input_dropped()` sempre falso su wlroots, così il figlio non si accorge che il desktop è finito; (2) quando poi l'abbandono (60 min) o un login locale chiede di chiudere, `terminate_and_clear()` dice «niente da chiudere = fallito» e il figlio non esce. Lo stato dura senza limite (62 min misurati) finché non torna un cliente (che lo sana, spendendo un login). Stesso codice nell'albero Debian |
| B1. Log Out nei primi secondi (menu XFCE) | **DIFETTO MINORE, NON DEL PRODOTTO** (supposto): fino a 7 s dal desktop il Log Out del menu viene ignorato da XFCE, senza avviso; da 8 s funziona; premendo di nuovo funziona |
| B2. Rientro dopo il Log Out | **FUNZIONA** (a 0,3 s il primo accesso riceve «sessione finita», poi si rientra; da 1 s in poi si rientra subito; nessuno schermo vuoto oltre ~6 s) |
| C. Finestra apport per `blueman-applet` | **CAUSA PROVATA**, non è del prodotto (catena completa nel journal); vale anche per un accesso locale (inferito dai pacchetti) |
| D. Allarme «CAN BE POWERED OFF…» | **ALLARME FALSO nel box** (causa provata); su macchina vera può essere falso o vero (condizioni indicate) |
| E. Pannello XFCE, tre strade non provate | **FUNZIONA** (nessuna perdita del plugin in nessuna delle tre); la riga «not repaired now» non si può produrre per questa via (spiegato) |
| F. Chiusura leggera e `survivor()` | **FUNZIONA** quanto osservabile; il salto di `survivor()` è reale ma qui innocuo; l'accesso locale vero NON è osservabile nel box |

---------------------------------------------------------------------------------------------------

## A. Log Out dal menu con la sessione STACCATA (nessun browser)

### A.1 Riproduzione (MISURATO, 3 volte)
Metodo (`xa.py`, usa `prove/lib.py`): utente nuovo, login con Chrome, desktop assestato, +5 s, chiudo il browser (sessione staccata), +4 s,
poi `xfce4-session-logout --logout` come utente. Ogni secondo-due controllo `labwc`, figlio `remotix`, sessioni logind, numero processi.

| Prova | Log Out chiesto alle | `labwc` sparito dopo | Figlio `remotix` | Sessioni logind | Processi dell'utente |
|---|---|---|---|---|---|
| va1 | 20:32:06 (epoca 1795033926) | 0,8 s | **ancora vivo a 92 s (fine dello script), poi controllato: 20:37, 20:50, 21:07, 21:18, 21:33 (61 minuti); fine: vedi A.5** | 2 (`c1375` user, `c1376` manager) | 27 (25 più tardi) |
| va2 | 20:34:28 (1795034068) | 0,65 s | **vivo per tutti i 100 s** e fino al mio rientro delle 20:40:18 (350 s) | 2 | 27 |
| va3 | 20:36:13 (1795034173) | 0,84 s | **vivo per tutti i 100 s** e fino al mio rientro (~20:43) | 2 | 27 |

Ultima riga di va1 nello script: `t=92 labwc=- remotix=141077 logind=2 nproc=27`; elenco rimasti: `pipewire x2, dbus-daemon x2, xiccd, xfconfd, wireplumber, tumblerd, systemd, remotix, pipewire-pulse, mpris-proxy, gvfsd*, gnome-keyring-d, dconf-service, ayatana-indicat, at-spi*, applet.py, (sd-pam)`: il desktop non c'è più, il figlio e il gestore dell'utente sì.

Journal dell'utente va1 (l'unico del figlio dopo il Log Out; per intero, in 5 minuti non c'è altro dal figlio):
```
Nov 18 20:32:06.778070 NIC-OS remotix[141077]: input   [va1] ⛔ wlroots: the input connection has DROPPED (read_events: Broken pipe) — the compositor has gone away or closed the socket
Nov 18 20:32:06.784492 NIC-OS remotix[141077]: input   [va1] ⛔ wlroots: the input connection has DROPPED (read_events: Connection reset by peer) — the compositor has gone away or closed the socket
Nov 18 20:32:06.784521 NIC-OS remotix[141077]: input   [va1] ⛔ wlroots: the input reattach does not succeed (the compositor did not answer the list of globals within 2 s) — retrying every second, and this line does not repeat.  ⚠ Meanwhile the desktop can be SEEN and not CONTROLLED
```
La riga «THE COMPOSITOR CLOSED THE INPUT CHANNEL AND THE SESSION NO LONGER ANSWERS» (child.c:11551) compare **0 volte** nel journal di va1.

### A.2 Che cosa succede a un nuovo login in quello stato (MISURATO)
- va2 (rientro 20:40:18, script `xr.py`): «Admitted, **resumed session**, canvas 1344×768, desktop xfce» a +1 s; poi il giornale del figlio:
```
20:40:19.815456 child [va2] ⚠ THE STAGE HAS GONE FROM UNDER OUR FEET (grab 2: the wire to the compositor dropped (flush): Broken pipe)…
20:40:20.819932 session [va2] no org.xfce.SessionManager on the bus: the XFCE session is not there
20:40:20.819952 child [va2] ⭐ §7.6: the graphical session WAS THERE and now is NO LONGER — the user logged out from the desktop menu.  ⛔ I am NOT making it be born again … Warning the parent, which gives whoever is watching the farewell 0x10
20:40:20.920518 session [va2] ⭐ scope leftovers after the exit: SIGTERM to 3 processes (applet.py xiccd ayatana-indicat)
20:40:21.505201 child [va2] ⭐ SIGTERM: the session is over — cleaned up
```
  Nella pagina: `painted=1`, rettangolo `[0,0,0,0]` (canvas largo 0), messaggio «the session has ended: the programs were closed»; figlio sparito a +8 s. Quindi lo stato sbagliato dura **fino al primo cliente che torna**: il primo login è ammesso «resumed», dopo 1-2 s la pagina viene avvisata e il figlio muore.
- va3 (script `xr2.py`): login «resumed» a +1,2 s; «ended» a +2,2 s con il modulo di accesso di nuovo visibile; processi 22, sessione logind 1; **secondo login: «Admitted, new session»**, desktop assestato dopo 8,5 s, pannello presente (`va3-2nd-login.png`).
- Quindi: la cura «chiudere e ripartire puliti» il prodotto la fa già, ma **solo dopo aver sprecato un login** (l'utente vede «sessione finita» al primo tentativo e deve riaccedere).

### A.3 CAUSA (LETTO + MISURATO)
1. Con nessun cliente collegato il ciclo del figlio non cattura: `child.c:11820` `if (!requested_codec || !cat) continue;` (il «prima» del `continue` è tutto ciò che c'è). Il solo posto che scopre «lo stage è sparito» da lì in poi è la cattura (`child.c:12016-12060`, «THE STAGE HAS GONE FROM UNDER OUR FEET» → `unmount_stage` → rimontaggio → `take_stage` legge `session_state()==DEAD` con `vista_viva` → §7.6 → `raise(SIGTERM)`, `child.c:8640-8700`). A sessione staccata quella strada **non gira mai**.
2. Esiste una seconda strada indipendente dalla cattura, pensata proprio per questo («THE INPUT CHANNEL CLOSED BY THE COMPOSITOR, AND THE SESSION NO LONGER ANSWERS», `child.c:11545`): `if (cat && !stage_kwin && input_dropped(stage_input)) { …ogni 1 s… if (!session_alive()) { unmount_stage… } }`.
3. **Quella strada su XFCE/LXQt (wlroots) non scatta mai**, perché `input_dropped()` (`input.c:1505`) è
   `return in && !in->wlr && in->dropped;`
   e per il backend wlroots `in->wlr` resta **non nullo** (è l'oggetto `WlrInput` caduto, `input.c:2700`; viene sostituito solo da un reattacco riuscito, `:2930`), mentre il flag `in->dropped` viene messo a TRUE soltanto nel ramo libei/GNOME (`input.c:1358, 1714, 1732, 1748`). Il flag giusto per wlroots è `wlr_input_dropped(in->wlr)` (`wlr_input.c:752`, messo a true da `mark_drop`, `wlr_input.c:149`), ed è proprio quello che il journal mostra («the input connection has DROPPED»). Il controllo c'era, scritto per GNOME; su wlroots la condizione è sempre falsa. Prova dal vivo: in 62 minuti la riga del punto 2 non compare mai.
4. Neanche altro chiude il figlio: il Log Out dell'utente non passa dal figlio (§7.6 vale solo se il figlio lo scopre).

### A.4 Cura minima proposta (NON applicata)
`src/input.c`, funzione `input_dropped()` (riga 1505):
```c
int input_dropped(const Input *in)
{
	if (!in) return 0;
	if (in->wlr) return wlr_input_dropped(in->wlr);   /* wlroots: il flag è nell'oggetto wlr */
	return in->dropped;                                /* libei */
}
```
Effetto: dal secondo successivo al Log Out `child.c:11545` chiama `session_alive()` (una chiamata D-Bus al secondo, già limitata da `EIS_GONE_LOOK_MS`); su XFCE `session_alive()` = «nome `org.xfce.SessionManager` sul bus» (`session.c:1004`), assente dopo il Log Out; il figlio smonta lo stage e il rimontaggio porta a §7.6 (`raise(SIGTERM)`, pulizia, logind chiude la sessione). Con la sessione viva e solo il filo caduto il controllo non fa nulla (il reattacco c'è già, `input.c:2870`). **Da provare nel box prima di approvare** (un reattacco in corso può far chiamare `session_alive()` più volte, innocuo). Se si vuole una cintura in più: anche nel ramo «senza cliente» fare ogni 1-2 s la stessa domanda `session_alive()` quando `cat` è montato.
Vale per LXQt (stesso backend wlroots, non misurato: macchina di altri). Per KDE c'è già `kwin_closed()`.

### A.5 Quanto dura al massimo lo stato sbagliato (LETTO + MISURATO) — **non ha un limite: l'orologio di abbandono scatta e non fa nulla**
- Il figlio non ha nessun timeout proprio. Il parent ha l'orologio di abbandono `DEFAULT_ABANDON_MS = 3600000` (60 minuti, `main.c:1604`), **contato dalla nascita della sessione** (non dal Log Out) e rinnovato solo da input vero (`main.c:1252-1270`).
- MISURATO su va1 (nascita 20:31:47, Log Out 20:32:06): alle **21:31:47** l'orologio scatta, per intero:
```
21:31:47.854182 remotix[125480]: startup ⭐ §5.3 — ABANDONMENT: «va1» has touched nothing for 3600326 ms (ceiling 3600000).  ⛔ I CLOSE the graphical session, and with it its programs …
21:31:47.865158 remotix[141077]: child   [va1] ⭐ §5.3: the session is ABANDONED — closing the graphical session and with it its programs.  ⚠ Nobody asked for it: the ceiling expired, and the number is in the parent's line
21:31:47.866707 remotix[141077]: session [va1] there was no session to stop
21:31:47.867037 remotix[141077]: child   [va1] ⛔ the graphical session did NOT end: the user asked to log out and the desktop is still there.  ⚠ The client has already been given the farewell 0x10, so now the two truths do not match — and this line is the only place where it shows
```
  e **il figlio è rimasto vivo** (controllato 21:33:52 e 21:34:18: 25 processi, 1 sessione utente + manager). **Causa (LETTO)**: `child.c:10969` `if (!terminate_and_clear()) { …"did NOT end"…; continue; }`: `terminate_and_clear()` → `session_terminate()` → `really_terminate()` (`session.c:4801`) che, se il desktop non c'è più (`!session_alive()`), scrive «there was no session to stop» e **ritorna false**; il figlio lo prende per un fallimento e torna nel ciclo invece di uscire (il ramo di successo, «I am exiting too», `child.c:10985`, non viene mai raggiunto).
- Quindi lo stato sbagliato dura **finché non arriva un cliente** (che lo sana in 1-2 s, A.2), **oppure finché qualcuno uccide il figlio da fuori**: non c'è nessun limite di tempo. MISURATO: alle 21:34:18 ho simulato un login locale di va1 con il gancio PAM del prodotto (`env -i PAM_TYPE=open_session PAM_SERVICE=prova-dm PAM_USER=va1 XDG_SEAT=seat0 XDG_SESSION_CLASS=user XDG_SESSION_TYPE=wayland /usr/libexec/remotix/remotix-local-login`, come fa `check-prelocal.py`): il gancio è tornato `rc=0` dopo **16,3 s** (il figlio non si chiudeva da solo; il lato radice lo ha ucciso con SIGTERM alle 21:34:34, riga `⛔ local excludes remote: session-c1375.scope of «va1» is gone` e `its REMOTIX session is gone (16300 ms, scope ended by the root side…) — the login goes on`). Cioè un accesso locale di quell'utente è stato **ritardato di 16 s** (il P1 di `check-prelocal` chiede «entro 15 s»), ma non bloccato. Una sola misura, con un solo gancio simulato.
- Costo dello stato sbagliato: 25-27 processi e un gestore utente per utente (la stima del codice è ~477 MB per sessione abbandonata, `main.c:1590`, non misurata da me); va1 è rimasto così 62 minuti.
- **Seconda cura minima (NON applicata)**, in aggiunta alla prima: `child.c`, ramo `if (!terminate_and_clear())` (riga ~10969): se `!session_alive()` (non c'era niente da chiudere: desktop già finito) trattare come chiuso — scrivere la riga «the graphical session was already gone: I am exiting» e fare `fine = true; break;` come nel ramo di successo, senza il messaggio «did NOT end». Così abbandono, arresto del servizio e login locale (PRELOCAL) chiudono davvero il figlio anche in questo stato. Con la cura A.4 lo stato non nasce più; questa è la cintura per tutti gli altri modi in cui il desktop può sparire senza che il figlio se ne accorga.

### A.6 Stesso codice nell'albero Debian rilasciato? (LETTO, sola lettura)
`/home/nicfio/Documenti/REMOTIX-DEBIAN/src/child.c` contro quello di unione2: le sole differenze sono righe 1565-1930 (PATH/ambiente del figlio, `--session-fd`), 8704, 10095, 10393 (gancio KDE «session_kde_logout_watch»); **le righe 11545 e 11820 non sono in nessuna differenza** → identiche. `input.c` e `wlr_input.c` di Debian e di Ubuntu sono **identici** (`diff` vuoto). Quindi il difetto è presente anche nel codice Debian per XFCE/LXQt. Non misurato su Debian (non c'è un box Debian in questo giro).

**va1 (esito finale):** figlio vivo dal Log Out delle 20:32:06 fino al mio login locale simulato delle 21:34:18 (**62 minuti**), morto alle 21:34:34/21:34:38 per SIGTERM del lato radice (monitor: `va1 child gone 21:34:38 after 3752 s from logout`); l'abbandono delle 21:31:47 non lo ha chiuso (A.5). Poi ho chiuso io l'utente (`end_users`).

---------------------------------------------------------------------------------------------------

## B. Log Out nei primi secondi

### B.0 Che cosa ho provato (MISURATO)
Tempo zero = primo fotogramma del desktop nella pagina (in ogni prova arriva 0,8-1,6 s dopo l'accettazione del login, con pannello e `xfce4-session` già presenti). Utenti nuovi `bnDR`; la prova 1 su ciascuno è «utente nuovo», la 2 «già usato» (stesso utente, seconda sessione), la 3 «già usato» dal pulsante della pagina. Tre ripetizioni per tempo (`bn11..bn83`, 3 sessioni in parallelo alla volta). Script `xb.py`, `runB.sh`.
- **Pulsante della pagina: non esiste più per l'utente.** `src/page.html:10250-10300` (la scorciatoia è stata tolta il 17 ago: «Log Out dal menu del desktop remoto»); resta nel documento solo il pulsante nascosto `confirm-yes` che invia `TERMINATE_SESSION`. Ho emulato il gesto cliccando quello (via CDP). Non è un percorso dell'utente.
- Menu XFCE: `xfce4-session-logout --logout` lanciato come utente nell'ambiente della sessione.

### B.1 Esiti
| Log Out dopo (dal 1° fotogramma) | Dal menu, utente nuovo | Dal menu, già usato | Dal pulsante della pagina (già usato) |
|---|---|---|---|
| **1 s** | **3/3 IGNORATO**: desktop vivo (40 processi) per tutti i 60 s osservati; il comando resta appeso (`rc=124`, ucciso dal mio `timeout 60`), nessun messaggio | 3/3 ignorato | 3/3 chiude: desktop sparito e pagina avvisata ≤1 s; figlio sparito a 22-23 s; logind a 33 s (con 3 sessioni in parallelo) |
| **2 s** | 3/3 ignorato | 3/3 ignorato | 3/3 chiude (figlio 21-22 s, logind 31-32 s) |
| **4 s** | 3/3 ignorato | 3/3 ignorato | 3/3 chiude (figlio 20 s, logind 30 s) |
| **5 s, 6 s, 7 s** (solo nuovi, 2 prove ciascuno, `bt51..bt72`) | 6/6 ignorato | – | – |
| **8 s** | **3/3 chiude**: `labwc` ≤0,2 s, pagina avvisata a 1,3-1,4 s, figlio sparito a 2,5-2,6 s, logind a 12-16 s | 3/3 chiude (figlio 2,5-2,6 s, logind 12-18 s) | 3/3 chiude (figlio 11-17 s, logind 22-27 s) |

(Risoluzione dei tempi: ~1 s, il primo controllo parte dopo la chiamata ssh.)
- Nuovo o già usato: **nessuna differenza**.
- Soglia: tra 7 s (ignorato 2/2) e 8 s (chiude 6/6) dal primo fotogramma, cioè circa 8-10 s dal login.
- Il Log Out ignorato **non resta in coda**: nella prova `xs.py` (utente bs1, Log Out a 2 s) il comando è rimasto appeso per tutti i 163 s e il desktop è rimasto su; il comando non ha stampato nulla. Un **secondo** Log Out premuto a 20 s dal primo (`xb.py … menu2`, `bt31`, `bt32`) chiude subito: `labwc` sparito a 20,2 s, pagina avvisata 21,4 s, figlio 22,6 s, logind 32,4 s.
- A 5-6 s dal login `xfce4-session` sta ancora avviando la seconda fase (processi `polkit-mate-authentication-agent-1`, `applet.py`, `xiccd`, `xfce4-power-manager`, `nm-applet`, `blueman-applet`, `update-notifier` compaiono con età 00:06 sotto `xfce4-session`: output `ps` di `xs.py`).
- Residui dopo un Log Out riuscito (8 s e prova `bq*`): 0 processi dell'utente, 0 sessioni logind (dopo 12-18 s: la sessione resta «closing» qualche secondo), `/run/user/<uid>/remotix` **assente**.
- Residui dopo un Log Out ignorato: tutto è ancora in piedi (nessun danno, nessun residuo: è un desktop normale).

### B.2 Conclusione B1
**Ignorato da XFCE, non perso dal prodotto** (SUPPOSTO per la causa, MISURATO per l'effetto): lo studio 7 §6.6 documenta che `xfce4-session` accetta il Log Out solo a stato «idle» (`xfsm_manager_signal_startup_done`) e il prodotto lo sa; qui l'idle arriva circa 8 s dopo il primo fotogramma (sono i `STARTUP_TIMEOUT_WAYLAND` di 8 s per gruppo, dello studio, non provati da me uno per uno). In un accesso locale XFCE si comporterebbe uguale (stesso `xfce4-session`), ma lì l'utente non ha il desktop davanti prima: SUPPOSTO, non osservabile qui. Effetto per l'utente: il primo Log Out premuto nei primi 8 s non fa niente e non dà nessun avviso; premendo di nuovo funziona. **Cura proposta**: nessuna sul prodotto (non può né vedere il clic né cambiare `xfce4-session`); eventualmente scriverlo nel manuale. Se invece si volesse: il figlio potrebbe interrogare l'`org.xfce.SessionManager` per sapere se è `idle` prima di mostrare il primo fotogramma (aumenta il tempo di avvio: non consigliato).
Nota correlata (MISURATO): dal pulsante nascosto della pagina il figlio impiega 11-23 s a sparire contro 2,5 s dal menu: la strada `TERMINATE_SESSION` aspetta più a lungo; non raggiungibile dall'utente, annotata.

### B.3 Rientro immediato dopo il Log Out (MISURATO)
Metodo (`xb.py … menu 12 <ritardo>`, utenti `bq*`): utente nuovo, Log Out dal menu a 12 s; **un secondo Chrome già aperto sul modulo di accesso** (per non misurare l'avvio del browser), la pagina vecchia viene abbandonata (`about:blank`) e il login parte dopo 0,3 / 1 / 3 / 10 s dal gesto. Due ripetizioni per tempo (`out-B3-*.txt`; la prima tornata, con l'avvio del browser dentro il tempo, è invalida e messa in `invalid-first-reentry/`).

| Rientro a | Primo tentativo | Ammesso a (dal Log Out) | Primo fotogramma | Desktop assestato (pannello su) |
|---|---|---|---|---|
| 0,3 s (2/2) | **rifiutato**: «the session has ended: the programs were closed» (il login ha raggiunto la sessione che stava morendo) | secondo tentativo a **+5,9 s**: «Admitted, new session» | +0,8 s dopo l'ammissione | +5,8 s dopo l'ammissione |
| 1 s (2/2) | ammesso «new session» in 2,7 s | +3,7 s | +0,8 / 1,2 s | +5,8 / 6,2 s |
| 3 s (2/2) | ammesso «new session» in 2,7 s | +5,7 s | +0,8 s | +5,8 s |
| 10 s (2/2) | ammesso «new session» in 2,7 s | +12,7 s | +0,8 s | +5,8 / 6,2 s |

In tutti i casi la nascita ha scritto `⚠ NO STAGE at birth … I do NOT exit` e poi `RESTARTING THE CAPTURE: the stage came back after 200 ms` (la guardia attende che la sessione grafica precedente sia chiusa); non c'è schermo nero più lungo di ~6 s, uguale a una nascita normale. Istantanee `bq*-re*.png` (pannello presente). Nessun processo residuo a fine prova.
**FUNZIONA.** Solo a 0,3 s l'utente vede un rifiuto «sessione finita» e deve riprovare (il testo è fedele: è la sessione appena chiusa).

---------------------------------------------------------------------------------------------------

## C. Finestra apport per `blueman-applet`

### C.1 Fatti (MISURATO)
- `/var/crash`: 5 file `_usr_bin_blueman-applet.*.crash` (utenti bc1 19:33:44, lc2 19:36:56, rs10 19:54:01, bn21 20:49:04, bre031 21:06:14). Traceback identico in tutti: `blueman/plugins/applet/TransferService.py:235 _on_dbus_name_appeared → Manager() → bluez/obex/Manager.py:29 Gio.DBusObjectManagerClient.new_for_bus_sync → GDBus.Error:org.freedesktop.DBus.Error.NoReply: Message recipient disconnected from message bus without replying`.
- Il box non ha Bluetooth (`/sys/class/bluetooth` assente, `bluetooth.service` inattivo).
- **Chi lo avvia**: `/etc/xdg/autostart/blueman.desktop` (`Exec=blueman-applet`), pacchetto `blueman` (`Recommends` di `xubuntu-desktop`).
- **Catena completa dal journal dell'utente bc1, 19:33:44** (stessa sequenza in tutte le 90 sessioni):
```
19:33:44.062052 dbus-daemon: Activating via systemd: service name='org.bluez.obex' unit='obex.service' requested by ':1.100' (uid=1002 pid=4880 comm="/usr/bin/python3 /usr/bin/blueman-applet")
19:33:44.085360 obexd[5116]: OBEX daemon 5.85
19:33:44.085870 dbus-daemon: Successfully activated service 'org.bluez.obex'
19:33:44.088488 obexd[5116]: Unable to acquire registry: Error calling StartServiceByName for org.gnome.evolution.dataserver.Sources5: Unit evolution-source-registry.service not found.
19:33:44.089161 obexd[5116]: obex_server_init failed
19:33:44.089630 systemd[3626]: obex.service: Main process exited, code=exited, status=1/FAILURE
```
  Cioè: blueman chiede il nome D-Bus `org.bluez.obex`; il bus lo attiva avviando `obexd` (`/usr/share/dbus-1/services/org.bluez.obex.service`, `obex.service` senza condizione sulla presenza di hardware Bluetooth); `obexd` prende il nome e **muore dopo ~25 ms** (`obex_server_init failed`, manca il servizio di Evolution: `apt-cache depends bluez-obexd` mostra `Suggests: evolution-data-server` soltanto; nel box c'è solo `evolution-data-server-common`); blueman, appena il nome appare, fa una chiamata sincrona e se `obexd` è già sparito riceve `NoReply` → eccezione non gestita → crash → apport → `update-notifier` (in sessione, osservato in `ps`) mostra la finestra «Sorry, Ubuntu 26.04 has experienced an internal error».
- Frequenza (MISURATO sul journal di tutto il box): **90 attivazioni di `org.bluez.obex` per 98 nascite XFCE, 90 «obex_server_init failed», 5 crash** → circa 5-6% delle sessioni. Il crash è la gara tra la sparizione di `obexd` (25 ms) e la chiamata di blueman; negli altri 85 casi la chiamata arriva in tempo o il nome è già sparito.
- **Dipende dal numero di sessioni insieme?** Non risulta (MISURATO, poche unità): sessioni con altre nascite entro 15 s: 1 sola → 3 crash su 47; 2 → 0/7; 3 → 3/28 (qualche doppio conteggio); 4+ → 0/8. Nessun andamento chiaro.
- Alla stessa maniera, MISURATO, `blueman-applet` NON parte e non c'è nessuna attivazione di `obexd` (0) se per l'utente esiste `~/.config/autostart/blueman.desktop` con `Hidden=true` (utente `bh1`, `xh.py`); gli altri autostart (`nm-applet`, `polkit-mate`, `update-notifier`, `xfce4-power-manager`) partono lo stesso.

### C.2 Su una macchina vera senza Bluetooth, o in un accesso locale?
INFERITO dai pacchetti (non osservabile nel box): la catena non passa né per il remoto né per l'hardware: dipende da `blueman` che parte all'avvio, da `bluez-obexd` che parte e fallisce senza `evolution-data-server`. Un Xubuntu locale con installazione di serie (stessi pacchetti `xubuntu-desktop`) ha le stesse condizioni → stesso crash casuale (~5% dei login), con o senza Bluetooth. Con `evolution-data-server` installato `obexd` non dovrebbe fallire: non provato. Nel codice Debian per XFCE non c'è nulla su blueman/Bluetooth (grep su `src/*.c`, `manuals`), né in quello Ubuntu.

### C.3 Come tratta il prodotto gli autostart? (LETTO)
XFCE: **nessun trattamento** degli autostart nella sessione remota (`session.c` ha solo le chiavi xfconf, il pannello e i blocchi). LXQt sì: elenco `LXQT_X11_COMPOSITORS` (picom, compton, xcompmgr) con cartella `bin-lxqt` e voci `Hidden=true` (`session.c:6064-6095, 6228-6240, 6717-6800`). Per KDE/GNOME/XFCE non esiste un elenco di autostart da non avviare.

### C.4 Proposta (NON applicata) — decisione del proprietario
- **Opzione 1 (coerente con «remoto = accesso locale»):** non toccare nulla; è un difetto dei pacchetti Ubuntu (`blueman` + `bluez-obexd` senza EDS), uguale in locale; riferire a Ubuntu/Launchpad; scrivere nel manuale che una finestra apport su `blueman-applet` è nota.
- **Opzione 2 (il Bluetooth è un dispositivo della macchina, non dell'utente remoto, e un utente remoto su server condiviso non deve gestirlo):** nella funzione che prepara la sessione XFCE (`session.c`, dove si scrivono `xdg-xfce`/`labwc-xfce` per XFCE, vicino a `xfce_session_xfconf`) scrivere in `$XDG_RUNTIME_DIR/remotix/labwc-xfce/autostart/blueman.desktop` un file con `[Desktop Entry]`, `Type=Application`, `Name=Blueman Applet`, `Hidden=true` (stesso meccanismo del LXQt). Il meccanismo `Hidden=true` per nome è provato a livello utente (C.1); che funzioni dalla cartella `XDG_CONFIG_DIRS` di REMOTIX (prima voce) **non l'ho provato**.
Raccomandazione: opzione 1, perché per la regola uniforme un elenco di autostart per distro è proprio la «pezza per distro»; l'opzione 2 è difendibile solo con l'argomento «dispositivo fisico della macchina».

---------------------------------------------------------------------------------------------------

## D. La riga «⛔⛔ FROM THIS SESSION THE MACHINE CAN BE POWERED OFF OR SUSPENDED…»

### D.1 Codice (LETTO)
Scritta in `child.c:9445-9462` una volta per sessione, dopo `sentinel_shutdown_forbidden()` (`sentinel.c:880-905`): per ciascuna azione `CanPowerOff`, `CanReboot`, `CanSuspend`, `CanHibernate` chiede a logind (`org.freedesktop.login1`, **dal figlio, cioè come utente**: root riceverebbe sempre «yes») e **l'allarme scatta se anche una sola risposta non è esattamente `no`**: una risposta mancante (`(no answer)`) vale «non sicuro» (`all_no = false`), come `na`, `challenge` o `yes`. Il testo dice sempre «POWERED OFF OR SUSPENDED… the polkit rule is missing, or it does not cover all twelve actions», qualunque sia la risposta che ha fatto scattare; i valori stanno nella riga.

### D.2 Dal vivo dentro una sessione remota XFCE (MISURATO, utente `bd1`, `xd.py`, `busctl --system call …` come utente)
```
CanPowerOff  -> s "no"
CanReboot    -> s "no"
CanSuspend   -> Call failed: Read-only file system   (rc=1)
CanHibernate -> Call failed: Read-only file system   (rc=1)
CanSuspendThenHibernate / CanHybridSleep -> Call failed: Read-only file system
CanHalt      -> s "no"
```
Riga di journal: `⛔⛔ FROM THIS SESSION THE MACHINE CAN BE POWERED OFF OR SUSPENDED (CanPowerOff=no CanReboot=no CanSuspend=(no answer) CanHibernate=(no answer) ): §4.7 says nobody must be able to do it, and the machine belongs to several people.  ⇒ The polkit rule is missing, or it does not cover all twelve actions`.
Regola polkit del prodotto presente: `/usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules`.

### D.3 Conclusione
- **Nel box l'allarme è FALSO** (CAUSA PROVATA): spegnimento, riavvio e halt sono «no» (la protezione c'è); le due risposte mancanti sono un errore D-Bus `Read-only file system` perché nel contenitore `/sys/power` è di sola lettura e logind non sa dire «sospendi sì/no».
- **Su una macchina vera**: sarebbe VERO solo se una delle quattro risposte è `yes` o `challenge` (regola polkit mancante o incompleta). Sarebbe **falso** anche con `na` (sospensione non supportata dal kernel/hardware: tipico di una VM o di un server) — SUPPOSTO dal codice, non osservato — e con qualsiasi errore di logind.
- **Cura proposta** (non applicata): `src/sentinel.c`, `sentinel_shutdown_forbidden()`: accettare come sicuro anche `na` e un errore D-Bus su `CanSuspend`/`CanHibernate` (non su `CanPowerOff`/`CanReboot`), oppure scrivere nella riga quale azione non è «no» e non dire «can be powered off» se la risposta è `na`/errore.

### D.4 Il menu di uscita di XFCE (MISURATO, istantanea `bd1-logout-dialog.png`)
`xfce4-session-logout` senza `--logout`: finestra «Log out bd1» con **Log Out attivo, Restart e Shut Down presenti ma GRIGI (disattivati)**, nessun Suspend/Hibernate, nessun Lock screen, e il pulsante Cancel. Chiavi del pannello: `show-command-{lockscreen,switchuser,suspend,hibernate,restart,shutdown}` tutte `false` (bloccate); `xfce4-session`: `ShowSuspend/ShowHibernate/ShowHybridSleep=false`, `ShowSwitchUser=false`.

---------------------------------------------------------------------------------------------------

## E. Pannello XFCE, le tre strade non provate

Metodo (`xe.py`): utente nuovo, sessione remota 1 (15 s: file del pannello e blocco in memoria controllati), poi **accesso locale simulato** come nello studio X3 (servizio PAM mio `xz-seat` con solo `pam_systemd`, `XDG_SEAT=seat0`, linger acceso; tutto rimosso a fine prova): chiusura leggera, poi la manipolazione, poi **nuova sessione remota** con journal e istantanea.
Premessa MISURATA comune: nel file utente dopo 15 s `plugin-1` ha il tipo vero: `<property name="plugin-1" type="string" value="whiskermenu">` con sei figli `show-command-* type="empty"`; xfconfd con il blocco in memoria (`remotix/xdg-xfce` nell'ambiente) e `plugin-1 = whiskermenu`, `show-command-shutdown = false`. Chiusura leggera dal journal: `light close (asked by the parent) 3/5 … 4/5 … R1/R2 (light close: the user has a local session): light mode — drop-in removed and daemon-reload done, but NO try-restart of xfconfd: it is the one of the user's LOCAL desktop` e `light mode — the XFCE keys are NOT restored (they would be written into the local desktop's xfconfd)`; dopo di essa xfconfd stesso pid con il blocco ancora in memoria.

| Strada | Come costruita | Che cosa ha fatto il prodotto | Esito |
|---|---|---|---|
| **E1 (H1b)**: xfconfd riavviato a mano con la sessione locale viva (`be1`) | dopo la chiusura leggera `systemctl --user restart xfconfd` come utente | file utente dopo il riavvio: `plugin-1 type="string" value="whiskermenu"` **intatto** (il tipo NON è `empty`: il pannello lo scrive come valore dell'utente); `xfconf-query` dà `whiskermenu`; seconda nascita: `⭐ XFCE: the user's 18 locked keys put back`, nessun «NOT put back», nessuna finestra «could not be loaded»; istantanea `be1-E1-panel.png`: pannello con menu whisker (icona in alto a sinistra) | **FUNZIONA, nessuna perdita**. H1b come descritta (tipo `empty`) non si verifica con questo codice |
| **E2**: nodo senza tipo con il blocco ancora in memoria («not repaired now») (`be2`) | dopo la chiusura leggera `xfconf-query -c xfce4-panel -p /plugins/plugin-1 -r` (non ricorsivo): in memoria il padre rimane **senza tipo** (l'elenco mostra solo i sei figli) | seconda nascita con xfconfd ancora con il blocco: 16 righe `⛔ XFCE: … NOT put back as the user had it — it stays pending in the copy` (come X3) e `2 keys out of 18 put back — only the 16 that did NOT go back stay pending`; **nessuna** riga «has no type» né «not repaired now»; file e pannello a posto (`be2-E2-panel.png`) | **FUNZIONA**; la riga «not repaired now» non compare |
| **E3**: figlio non bloccato sotto `plugin-1` (`favorites`) + padre senza tipo (`be3`) | aggiunto `favorites` (due voci) sotto `plugin-1` durante la prima sessione; dopo la chiusura leggera xfconfd fermato e tolto dal file il tipo del padre (`type="empty"` con i figli e `favorites`) | seconda nascita: `18 locked keys put back`; file finale: `plugin-1 type="string" value="whiskermenu"` **con** `favorites` (`exo-terminal-emulator.desktop`, `thunar.desktop`) intatto; nessuna finestra; pannello normale (`be3-E3-panel.png`) | **FUNZIONA** |

Perché «not repaired now» non compare (LETTO + MISURATO): `xfce_panel_integrity()` (`session.c:5904-5967`) scrive «lock is still in xfconfd's memory — not repaired now» solo se `xfconfd_holds_lock()` è vero **dopo** `xfce_restore_keys()` (`session.c:7053-7100`); ma `xfce_restore_copy()` (`session.c:5723`) fa a sua volta `try-restart xfconfd` e ripristina il tipo del plugin dalla copia (gruppo `kind=plugin`, `session.c:5750-5760`), e solo dopo l'integrità legge il canale. In E2 il riavvio fa sparire lo stato «senza tipo» (era solo in memoria), in E3 la copia rimette il tipo. La riga resterebbe raggiungibile solo se il riavvio di xfconfd fallisse e la copia non avesse il plugin: NON costruita (non so come far fallire `systemctl --user try-restart` senza toccare altro). Non mi risulta nessuna strada che porti oggi alla perdita del menu del pannello.

Limiti: l'accesso locale è simulato (nessun desktop vero sulla sessione locale: nel box non c'è schermata di accesso); la sequenza «pannello vero che parte con `/plugins/plugin-1` NULL» (finestra «could not be loaded») non è stata prodotta perché il prodotto ha sempre rimesso il tipo prima della partenza del pannello.

---------------------------------------------------------------------------------------------------

## F. Chiusura leggera (voce 5) e `survivor()` (voce 6)

### F.1 Chiusura leggera (voce 5)
- MISURATO (E1/E2/E3, sopra): dopo `light close` xfconfd locale resta con il blocco in memoria (`show-command-shutdown=false`, `NOT restored` nel journal) — è il comportamento previsto dal codice (`session.c:4215-4226`, `child.c:9921`). Nel box **non è osservabile l'effetto sul menu del desktop locale** (nessun desktop locale); la sola prova di effetto è che `xfconf-query` come utente dà ancora `false` dopo la chiusura leggera (E1, E2).
- Come si esce da quello stato (MISURATO): (a) riavvio manuale di xfconfd (E1: dopo il riavvio la nascita seguente rimette tutte e 18 le chiavi: `18 locked keys put back`); (b) la nascita remota successiva (E2: 16 chiavi «NOT put back… pending» perché il blocco c'è ancora, poi riavvio del prodotto a fine sessione; X3 del giro 1 lo aveva già mostrato); (c) la fine del gestore utente quando non c'è linger (E3: xfconfd con pid nuovo). L'utente locale che resta con «Spegni/Riavvia» nascosti ha come uscita il riavvio di xfconfd/del gestore: SUPPOSTO per il suo desktop (non osservabile).

### F.2 `survivor()` e agenti (voce 6)
- Durante la sessione remota (MISURATO, `bf1`, `xf.py`): **non esiste nessun `ssh-agent` né `gpg-agent`** (`xfce4-session` qui non li avvia: nessuna chiave `/startup/ssh-agent/*` nel canale, `SSH_AUTH_SOCK`/`GPG_AGENT_INFO` assenti nell'ambiente di `xfce4-session`); c'è `xfconfd` (pid 381266). Restano da elencare i processi del gestore utente quando si usa un browser/applicazione che avvia un agente: non provato.
- Per provare il salto ho creato io un `ssh-agent` (non-dumpable) e l'ho messo **dentro lo scope della sessione** (`/user.slice/user-1062.slice/session-c4210.scope/cgroup.procs`): `stat -c %U /proc/<pid>/comm` = **root** (MISURATO), cioè `survivor()` (`session.c:4691`: `st.st_uid != getuid()` sul file `comm`) lo scarta: è vero che i processi non-dumpable vengono saltati.
- Dopo il Log Out (menu, sessione attaccata): journal `⭐ scope leftovers after the exit: SIGTERM to 3 processes (applet.py xiccd ayatana-indicat)` (l'ssh-agent **non** è nell'elenco, come previsto), ma:
```
21:04:18.099785 systemd-logind: Session c4210 logged out. Waiting for processes to exit.
21:04:24.105890 ssh-agent[382735]: exiting on signal 15
21:04:24.106237 systemd: session-c4210.scope: Deactivated successfully.
21:04:24.106947 systemd-logind: Removed session c4210.
```
  cioè l'agente è morto per SIGTERM 6 s dopo l'uscita del figlio (da chi lo ha mandato non lo so: **NON CAPITO**; non è `survivor()`), lo scope si è chiuso, la sessione logind è sparita (`logind=1`→`0` in 20 s, 0 processi dell'utente), e il login seguente è stato **«Admitted, new session»**, desktop assestato (`bf1-next.png`), senza «FOUND AGAIN».
- Effetto su un accesso successivo: **nessuno osservato** (solo remoto). Con `KillUserProcesses=no` di default (`/etc/systemd/logind.conf`) un processo che non muore da solo resterebbe nello scope: il caso reale che ha motivato `survivor()` (6 ott, NVIDIA: `localsearch-3`, `agent`) riguardava processi dumpable. Un agente non-dumpable che ignora SIGTERM e arriva da un'app dell'utente: NON provato.
- **Conclusione**: salto di `survivor()` reale ma innocuo nel caso provato; cura proposta di 3 righe come nello studio (leggere `Uid:` da `/proc/<pid>/status` invece del proprietario di `/proc/<pid>/comm`, `session.c:4689-4703`) resta valida e senza rischi: la propongo come prudenza, non come difetto visto.
- **Accesso locale**: non osservabile nel box (nessun desktop locale). Dichiaro che gli effetti su un accesso locale successivo (variabili ereditate, voci Spegni/Riavvia, `xfconfd` rimasto) sono solo SUPPOSTI.

### F.3 Residui dopo la chiusura della sessione remota (MISURATO)
In tutte le prove con Log Out riuscito: 0 processi dell'utente (incluso `xfconfd`, che finisce con il gestore utente 10-18 s dopo), 0 sessioni logind, nessuna cartella `/run/user/<uid>/remotix`. Nessun `ssh-agent`/`gpg-agent` residuo.

---------------------------------------------------------------------------------------------------

## Altre osservazioni (non richieste)
1. Riga nel journal del figlio dopo il Log Out, 10 s più tardi, dal processo helper della radice: `R1/R2 (no orphan desktops: the root side ended the user's REMOTIX session): light mode — the XFCE keys are NOT restored (they would be written into the local desktop's xfconfd)` (visto per bf1 alle 21:04:28, ben dopo che il figlio aveva già rimesso le 18 chiavi alle 21:04:18). È la strada «la sessione dell'utente è finita sul lato radice» e dichiara modalità leggera anche senza sessione locale: forse un messaggio fuorviante, nessun effetto visto. Non indagato.
2. La finestra di prova gira in un browser sul server: la distanza «login accettato → primo fotogramma» è 0,8-1,6 s in tutte le prove.

## Che cosa ho creato nel box (e come l'ho lasciato)
- **Utenti di prova** (con la loro cartella, NON cancellati, senza processi né sessioni a fine lavoro): `va1 va2 va3`, `bn11…bn83` (12), `bt31 bt32 bt51 bt52 bt61 bt62 bt71 bt72`, `bre031 bre032 bre11 bre31 bre101` (tornata invalida), `bq031 bq032 bq11 bq12 bq31 bq32 bq101 bq102`, `bs1 bd1 bf1 be1 be2 be3 bh1`. Password di prova comune dello strumento (`xl.py`).
- `bh1` ha `~/.config/autostart/blueman.desktop` con `Hidden=true` (prova C).
- **File nel box** (in `/tmp`, contenitore): `xa-*.out`, `xb-*.out`, `xb2-*.out`, `xs-*.out`, `xd-*.out`, `xf-*.out`, `xf-agent-*.sock/.env`, `xe-be3-before.xml`, `jall.txt`. `/root/mon-va1.out` (monitor di va1).
- **Cose di sistema create e RIMOSSE**: `/etc/pam.d/xz-seat`, `/tmp/xz-seat.py`, file `/tmp/xz-seat-hold-*`, unità transitorie `xzseat-*`, linger (spento, `/var/lib/systemd/linger` vuota).
- **Lasciato in `/var/crash`**: 5 file `.crash` di `blueman-applet` (3 del giro, 2 miei: `bn21`, `bre031`).
- Sul server, mia cartella `/media/REMOTIX-UBUNTU/lavoro/verifiche-xfce/`: script (`xa.py xr.py xr2.py xb.py xs.py xd.py xf.py xe.py xh.py conc.py runB*.sh`), uscite `out-B*-*.txt`, `xa-*.out`, `xe-E*.out`, `xf-bf1.out`, `xs-bs1.out`, `xr-va2.out`, `jall.txt` (copia del journal del box), istantanee `*.png` (`bd1-logout-dialog.png`, `be1/2/3-E*-panel.png`, `bq*-re*.png`, `bf1-next.png`, `va3-2nd-login.png`), cartella `invalid-first-reentry/` con la prima tornata invalida (spostata da me, mia).
- Un login locale **simulato** (gancio PAM del prodotto lanciato a mano, utente va1) alle 21:34:18, e per E la sessione PAM simulata `xz-seat` (rimossa).
- Stato finale del box (21:35): 0 processi e 0 sessioni logind di utenti di prova, linger vuota, `/etc/pam.d/xz-seat` assente.
- Nessuna modifica a pacchetto, prodotto, `prove/`, altre macchine, `/media/REMOTIX-DEBIAN`; nessun commit.

## Che cosa NON ho potuto vedere
- Un accesso locale vero (nessun desktop locale nel box): effetti di chiusura leggera, crash di blueman in locale, `survivor()` su accesso locale successivo.
- Il comportamento del difetto A su Debian e su LXQt (letto soltanto).
- Se il crash di blueman e la finestra apport esistono su una macchina Xubuntu vera con Bluetooth (inferito dal pacchetto).
- Perché `xfce4-session-logout` resta appeso nei primi 8 s (non ho letto i sorgenti di `xfce4-session`; l'ipotesi dello stato non-idle è dello studio 7).
- La cura A non è stata provata.
