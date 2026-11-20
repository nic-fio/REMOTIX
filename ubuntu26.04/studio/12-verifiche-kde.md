# Verifiche su Kubuntu/KDE (box `rxu-kde`, pacchetto unione2, Plasma 6.6.7) — 18 nov 2026, sera

Fatto da un solo agente sul box `kde`. Non è stato cambiato nulla nel prodotto né in `prove/`. Tutti gli script e le uscite
stanno sul server in `/media/REMOTIX-UBUNTU/lavoro/verifiche-kde/` (script: `hold.py`, `b-clean.sh`, `b2.py`, `c-detached.py`,
`d1.py`, `d2`=`m2.py`, `d3.py`, `d3e.py`, `d4.py`, `fakess.py`, `chain*.sh`; uscite: `*.out`). Istantanee in
`/media/REMOTIX-UBUNTU/albero/prove/shots/` (nomi `v-va2-*`, `vb2-*`, `vc-*`, `vd1-*`, `vd3-*`, `ve-e-*`, `desk-canvas-1280x720-kde-2611182228*`).
Versioni: `plasma-workspace 4:6.6.7-0ubuntu0.1`, `libpam-kwallet5 4:6.6.4`, `kwallet6 6.24.0`.
Convenzione: **MISURATO** = visto nel box con comandi e righe di registro; **SUPPOSTO** = ragionamento, non verificato.
Orari del box in UTC (il server è un'ora avanti).

## Riassunto in una tabella

| Compito | Esito |
|---|---|
| A. Ctrl+Alt+Canc su KDE | **DIFETTO, causa provata** (in Plasma ≥ 6.4, per come REMOTIX avvia KWin senza schermata di blocco) + cura proposta |
| B. `canvas-limits` | **Non è il prodotto: è la prova (fotografa troppo presto) con il box carico.** 0 guasti su 6 a vuoto, 2 su 4 sotto carico, riprodotto a volontà con carico forte |
| C. Log Out a sessione staccata | **DIFETTO** (come XFCE): il processo figlio resta vivo ≥ 200 s e un nuovo login è ammesso come «resumed session» senza desktop; causa trovata, cura proposta |
| D1. Salva / Scarta | FUNZIONA |
| D2. Log Out a 2…61 s dalla nascita | FUNZIONA (24 chiusure su 24 complete; ritardi fino a 28-30 s se parte dal secondo 2-5, spiegati) |
| D3. ksmserver che non risponde | **DIFETTO NOTO/ACCETTATO**: se ksmserver è bloccato, REMOTIX non forza nulla e il desktop resta su finché dura il blocco |
| D4. Rientro dopo il Log Out | FUNZIONA (0,3 / 1 / 3 / 10 s: sempre ammesso, nuovo desktop in ~9 s) |
| E. Portafoglio | **FATTO MISURATO**: alla prima richiesta vera di un segreto compare una finestra «KDE Wallet Service» (creazione portafoglio, poi richiesta di password) e l'app resta bloccata |

---

## A. Ctrl+Alt+Canc su KDE — DIFETTO, causa provata

### A.1 Chi ascolta la scorciatoia (MISURATO + codice letto)
- `kglobalshortcutsrc` dell'utente: `[ksmserver] Log Out=Ctrl+Alt+Del,Ctrl+Alt+Del,Show Logout Screen`.
- Il componente D-Bus `ksmserver` di kglobalaccel (`/component/ksmserver`, proprietario sul bus: `kwin_wayland`, kglobalaccel è dentro KWin)
  ha le azioni `Log Out`, `LogOut`, `Shut Down`, `Reboot`, `Log Out Without Confirmation`, `Halt Without Confirmation`, `Reboot Without Confirmation`,
  e `isActive = true`.
- **Chi registra queste azioni NON è il processo `ksmserver`**: è un modulo di kded6, `startkde/session-shortcuts/main.cpp` di plasma-workspace
  (v6.6.7, letto su GitHub `KDE/plasma-workspace`): `Log Out` («Show Logout Screen», Ctrl+Alt+Canc) chiama `SessionManagement::requestLogoutPrompt()`.
  (Il processo `ksmserver` c'è e risponde a `isShuttingDown`, ma non registra la scorciatoia.)
- `requestLogoutPrompt()` in `libkworkspace/sessionmanagement.cpp` **v6.4.0, 6.5.0, 6.6.0, 6.6.7** (righe 144-163):
  ```
  OrgFreedesktopScreenSaverInterface ifaceScreenSaver("org.freedesktop.ScreenSaver", "/ScreenSaver", sessionBus());
  // Do not show Logoup prompt when in the lockscreen / screensaver
  if (!ifaceScreenSaver.GetActive()) {  ... LogoutPromptIface iface; lockQuitUntilFinished(iface.promptAll()); }
  ```
  Nella **v6.3.6** (quella di Debian 13) il controllo non c'è: la funzione chiama direttamente `iface.promptAll()`.

### A.2 Che cosa succede nel box (MISURATO, utente `va2`, sessione di 60 s+)
`busctl --user monitor` mentre il pulsante «Ctrl+Alt+Del» della diagnostica invia i tre tasti:
```
20:53:55.450896 signal  Sender=:1.16  /component/ksmserver  org.kde.kglobalaccel.Component  globalShortcutPressed  ("ksmserver","Log Out",0)
20:53:55.450924 signal  ... globalShortcutReleased  (28 µs dopo)
20:53:57.492054 method_call  Sender=:1.22 (kded6)  Destination=org.freedesktop.ScreenSaver  /ScreenSaver  GetActive
20:53:57.492058 error  ErrorName=org.freedesktop.DBus.Error.ServiceUnknown  "The name org.freedesktop.ScreenSaver was not provided by any .service files"
```
Dopo l'errore **nessuna chiamata a `org.kde.LogoutPrompt`**, nessun processo `ksmserver-logout-greeter`. La finestra di prova vede solo `Control_L, Alt_L`.
(Il ritardo di 2 s tra tasto e `GetActive` nasce dal fatto che kded6 nel box è occupato nei primi ~30 s: nel suo registro
`kf.modemmanagerqt: Failed enumerating MM objects: TimedOut ... service_start_timeout=25000ms`. Non cambia la conclusione.)

### A.3 Perché non c'è il servizio (MISURATO + codice)
`org.freedesktop.ScreenSaver` lo registra il demone di blocco schermo di KWin (`kscreenlocker`, `interface.cpp`: `registerService("org.freedesktop.ScreenSaver")`).
REMOTIX avvia KWin con `--no-lockscreen` (`session.c:3210`, commento 3159 «locking belongs to REMOTIX»); in KWin quell'opzione
spegne il supporto al blocco (`main_wayland.cpp`: `a.setSupportsLockScreen(false)`). Nel box `busctl --user list` non mostra mai
`org.freedesktop.ScreenSaver` e la chiamata a mano dà `ServiceUnknown`.

### A.4 La prova decisiva (MISURATO, stessa sessione `va2`)
1. **Controllo senza servizio**: premuto Ctrl+Alt+Canc → nessun greeter in 5 s (`cad3`).
2. **Servizio finto** `fakess.py` (un programma nostro che, sul bus dell'utente di prova, prende il nome `org.freedesktop.ScreenSaver` e risponde `GetActive = false`):
   premuto Ctrl+Alt+Canc → il processo `ksmserver-logout-greeter` parte in 1 s e la schermata di uscita compare
   (`shots/v-va2-cad-fakess.png`: logo con «va2»; `v-va2-cad-rebound.png` mostra la schermata completa «Logging out in 24 seconds»).
3. Il meccanismo preciso del «sì» sbagliato è **SUPPOSTO** (non letto in Qt): `!GetActive()` su una risposta d'errore di D-Bus si comporta come «blocco schermo attivo»
   (il testo dell'errore, non vuoto, diventa `true`). Il comportamento (servizio assente → niente schermata; servizio presente con `false` → schermata) è invece misurato.

### A.5 Confronto con le altre azioni dello stesso modulo (MISURATO)
- `Log Out Without Confirmation` (`invokeShortcut`): la sessione si chiude, client avvisato dopo 1,6 s (usa `org.kde.Shutdown.logout`, senza `GetActive`).
- `LogOut` («Log Out» con conferma, `promptLogout`): schermata di uscita compare (anche senza servizio ScreenSaver).
- `Shut Down`, `Reboot`: nulla (voluto: `canShutdown()` falso, regola polkit di REMOTIX).
- Ctrl+Alt+L (blocco): tolto dalla regola KIOSK `lock_screen` (non provato di nuovo, nessuna novità).
- Quindi **solo `Log Out`/Ctrl+Alt+Canc** (l'unica che passa da `requestLogoutPrompt()`) è bloccata.

### A.6 Che cosa si aspetta la prova e se l'attesa è giusta
`prove/check-input.py`, `t_cad_chain` (righe 550-582 del server): con `?logbook` clicca il pulsante, poi 9 s a guardare. PASS se la finestra di prova vede
`Control_L, Alt_L, Delete`, **oppure** vede `Control_L, Alt_L` e il desktop reagisce (finestra perde il fuoco o immagine cambia: la schermata di uscita).
L'attesa è giusta anche per Plasma 6.6 (con la scorciatoia funzionante la schermata compare in ~1 s, come misurato col servizio finto). Il FAIL è un difetto vero.
**Debian 6.3 (SUPPOSTO, dal codice v6.3.6; non misurato qui):** lì `requestLogoutPrompt()` non controlla lo ScreenSaver, quindi la schermata dovrebbe comparire. Nel
giro Debian del 17 nov `page-cad-chain` risultava non verde anche su KDE (PIANO.md di Debian: pulsante nascosto, prova da allineare): quel giro è precedente all'allineamento
del 18 nov e non prova nulla né in un senso né nell'altro.

### A.7 Cure proposte (non applicate)
1. **Preferita, la più piccola**: far rispondere `GetActive = false` a un servizio nostro su `org.freedesktop.ScreenSaver` solo quando il blocco di KWin è spento.
   Dove: `session.c`, nel punto in cui si prepara la sessione KDE (vicino a `session_folder_kde()`, riga 1466, e alla riga di avvio 3210), con un piccolo
   «proprietario del nome» nel processo figlio (GDBus `g_bus_own_name`, oggetto `/ScreenSaver` e `/org/freedesktop/ScreenSaver`, metodi `GetActive` → false, `Inhibit`/`UnInhibit`
   con cookie finto, per non rompere chi li usa; `child.c` chiama già le funzioni di sessione a ogni giro). Provata a mano (A.4) solo per `GetActive`.
2. Alternativa: spostare Ctrl+Alt+Canc dall'azione `Log Out` all'azione `LogOut` (che chiama `promptLogout`, senza controllo): scrivere in `kglobalshortcutsrc`
   `Log Out=none,…` e `LogOut=Ctrl+Alt+Del,none,Log Out`. **Misurato** solo a caldo con `org.kde.KGlobalAccel.setForeignShortcut` (schermata comparsa);
   **non provato** che il file nella cartella `XDG_CONFIG_DIRS` di REMOTIX (come `kdeglobals`) venga letto da kglobalaccel. Mostra la schermata «solo uscita» invece di «tutto» (promptAll).
3. Non consigliato: togliere `--no-lockscreen` (il blocco è di REMOTIX, decisione §4.3).

**Conclusione A: DIFETTO** — causa provata, vedi A.2-A.4.

---

## B. `desktop/canvas-limits` — la prova, non il prodotto

### B.1 Esecuzioni (MISURATO) `python3 check-desktop.py --box kde --only canvas-limits --no-cap` (ogni giro ~196 s, utente `dk5`)
| Giri | Condizione | Esito |
|---|---|---|
| 1-6 | box a vuoto | **6 PASS su 6** (tutte e 10 le scene PASS, «edges ok») |
| 7, 8 | 3 sessioni KDE di altri utenti di prova (`va3`,`va4`,`va5`) già aperte | PASS, PASS |
| 9 | stesso (3 sessioni, carico ~4) | **FAIL**, prima scena 1280x720: «quadrants WRONG, edges WRONG» (`shots/desk-canvas-1280x720-kde-261118-222835.png`) |
| 10 | 3 sessioni + 24 cicli a vuoto che occupano la CPU (carico 25-30 su 20 core) | **FAIL**, stessa scena (`…-223158.png`) |
Totale: 2 guasti su 4 sotto carico, 0 su 6 a vuoto. Solo la **prima scena** fallisce (le altre 9 sempre PASS), come nel giro di conferma.

### B.2 Che cosa mostrano le foto (MISURATO)
- Giro 9: la finestra di prova c'è ma è **rimpicciolita (cornice a ~45 px dal bordo) e semitrasparente** (i colori sono mescolati con lo sfondo): è KWin a metà dell'animazione di apertura della finestra. (Nel giro di conferma di prima: cornice a 2-3 px, cioè quasi alla fine della stessa animazione.)
- Giro 10: nella foto c'è ancora **la schermata di avvio di Plasma** («Plasma made by KDE» con i puntini): il desktop non era nemmeno arrivato alla fine dell'avvio.
- Nelle dimensioni la finestra era giusta ovunque (`desktop inside the box (1264, 720)`, `viewer 1264x720`): non c'è mai stato un errore di scala o di bordo.

### B.3 Riproduzione con fotografie ripetute (MISURATO, `b2.py`, 24 cicli a vuoto, 6 esecuzioni)
Stessa scena, ma fotografata ogni ~2 s per 50-60 s dopo l'apertura:
- `vb1`: cornice bianca rientrata di 3 righe/6 colonne per ~11 s (14,0→25,4 s), poi esatta dal campione successivo (27,6 s, subito dopo un tocco del mouse sul desktop: non si distingue il tempo dal tocco).
- `vb2`, `vb3`: esatta subito.
- `vb4`, `vb5`, `vb6`: al primo sguardo (14 s) la finestra non c'era ancora (sfondo/ombre), e si è **corretta da sola** (26-29 s) senza nessun intervento.
Quindi l'immagine sbagliata è uno stato passeggero che finisce da solo: l'ultimo fotogramma arriva sempre.

### B.4 Causa (MISURATO + SUPPOSTO dove detto)
La prova (`prove/check-desktop.py`, `check_canvas`, righe 659-690 del server) apre la finestra con `box.in_session(...)`, aspetta `time.sleep(6)` (673), poi `settle_view` (648: aspetta un fotogramma
dipinto + 3 s) e `time.sleep(4)` (686), e **fotografa**: non verifica che l'avvio del desktop sia finito né che la finestra abbia finito di aprirsi. La prima scena cade quando il desktop ha solo 10-20 s, cioè
mentre `plasmashell` e il resto partono; con il box carico (anche da altre macchine del server) quell'avvio e l'animazione si allungano oltre i 13 s di attesa.
**Classe: della prova (aggiunta ambiente carico). Il prodotto non c'entra** per quanto visto (le dimensioni e i fotogrammi finali sono giusti). **SUPPOSTO**: l'animazione di KWin sia solo in ritardo (non l'ho separata dal ritardo di codifica; il fatto che si corregga da sola senza stimoli lo rende però improbabile come difetto di consegna dell'ultimo fotogramma).

Cura proposta (prova): prima di fotografare aspettare la riga `{"ev":"ready"}` nel registro della finestra (`geom-window.py` riga 88) **e** che la foto resti uguale per ~3 s (`lib.settled`) con un massimo di 30 s, e ripetere la foto una volta prima di dare FAIL; oppure far girare la prima scena a desktop con almeno 40 s di vita. Il resto di `canvas-limits` non va toccato.

---

## C. Log Out dal desktop con sessione staccata — DIFETTO (come XFCE), misurato su KDE

Procedura (`c-detached.py`): login, desktop di 40 s, il browser viene **chiuso** (staccato), 5 s dopo il gesto Log Out (`busctl org.kde.Shutdown logout` come utente), poi sondaggio ogni ~1 s. Un nuovo login dopo il tempo indicato.

| Prova | Login nuovo dopo il gesto | Risultato (MISURATO) |
|---|---|---|
| `c-1` (`vc1`) | 5,6 s | **ammesso come «Admitted, resumed session, canvas 1344×768, desktop kde»**; schermo vuoto (0 fotogrammi); dopo ~12 s la pagina dice «the session has ended: the programs were closed» e torna al modulo |
| `c-2` (`vc2`) | 20,2 s | identico (`resumed session`, poi fine sessione) |
| `c-3` (`vc3`) | 45,7 s | identico |
| `c-4` (`vc4`) | nessuno | per 200 s: KWin e plasmashell spariti da 0,5 s, **ma 11 processi e 2 sessioni logind restano, e il processo figlio `remotix` è vivo** (nessun cambiamento fino alla fine della prova a 201 s, dove lo ha chiuso lo strumento) |

Righe di registro (`c-2`, utente `vc2`, 54:48-54:50 UTC):
```
21:54:48.273 child [vc2] the parent asked for the stage and I have nothing to send again (0)
21:54:49.359 child [vc2] ⚠ KWIN IS GONE: the Plasma session is over (logout, or the compositor died).  Dismantling the stage...
21:54:50.361 session [vc2] no KWin on the bus: the Plasma session is not there
21:54:50.361 child [vc2] ⭐ §7.6: the graphical session WAS THERE and now is NO LONGER — the user logged out from the desktop menu...
21:54:50.421 session [vc2] ⭐ R1/R2 (the session is over (§7.6)) ...   21:54:50.421 child [vc2] ⭐ SIGTERM: the session is over — cleaned up
```
(il gesto era alle 21:54:21,8: il figlio si accorge 27 s dopo, solo perché è arrivato un login.)
Nel caso `c-4` l'ultima riga del figlio dopo la scomparsa di KWin è `capture [vc4] the Wayland connection to KWin has closed: the compositor is gone` (21:58:34,36) e poi **silenzio**.

**Causa (MISURATO il comportamento; codice letto, collegamento SUPPOSTO ma coerente con ogni riga):** in `child.c` il controllo «KWin è sparito» (`stage_kwin && kwin_closed(stage_kwin)`, riga ~12030, messaggio «KWIN IS GONE») sta **dopo**
`if (!requested_codec || !cat) continue;` (riga 11820): senza nessuno collegato (`requested_codec == 0`) il giro non ci arriva mai; il resto del controllo di fine sessione (§7.6, riga ~8650) parte solo quando il genitore chiede «il palcoscenico»,
cioè quando arriva un login. Per questo il nuovo login è ammesso come «resumed» e si accorge della fine solo dopo.
**Cura proposta (non applicata):** in `child.c`, nel giro «senza palcoscenico/senza codec» (vicino a `session_kde_logout_watch()`, riga ~10390), controllare comunque `kwin_closed(stage_kwin)` (o `session_state()==DEAD` con `vista_viva`) e prendere la stessa strada di §7.6 (`MSG_SESSION_FINISHED`, `session_clear_out_*`, `terminate_and_clear()`); così il figlio si chiude da solo pochi secondi dopo il Log Out anche senza client.
**Conclusione C: DIFETTO** — su KDE: figlio vivo ≥ 200 s, login nuovo ammesso come «resumed» a schermo vuoto per ~12 s, poi «sessione terminata», e un secondo login nasce nuovo. Perdita di dati: nessuna.

---

## D. Uscita da KDE, casi rimasti

### D1. «Salva» e «Scarta» con kwrite (testo non salvato) — FUNZIONA (MISURATO, `d1.py`)
(kwrite era già nel box, installato dall'agente precedente.) Gesto Log Out → a 12 s `isShuttingDown = true`, 44 processi, kwrite vivo, finestra «The document "Untitled" has been modified… Salva / Scarta / Annulla» (come `ke-ed61-beforeclick.png`).
- **Scarta** (`vs1`): clic a 13,1 s → client avvisato a **14,7 s**, tutto sparito (processi e sessioni = 0) a **24,6 s**; nessun file.
- **Salva** (`vs4`): clic a 13,6 s → finestra «Save As» → scelta la cartella dell'utente, scritto un nome e Invio a 22,5 s → client avvisato a **25,5 s**, tutto sparito a **34,2 s**; file `/home/vs4/savedbylogout` scritto, contenuto `unsaved work salva` (integro).
- Primo tentativo di «Salva» (`vs3`, errore mio): kwrite era partito con la cartella `/root` e non poteva salvare («could not be saved… /root/savedbylogout»); nessuno ha forzato niente, e a 120 s KWin ha chiuso da solo («Logging out anyway in 2 minutes»), client avvisato a 122,0 s: è il comportamento standard di Plasma, non di REMOTIX.
Nessuna riga «halfway/forzatura» di REMOTIX in nessuna delle prove (`session [..]` solo «logout is under way»/«no KWin on the bus»).

### D2. Log Out a 2, 5, 10, 25, 40, 61 s dalla nascita — FUNZIONA (MISURATO, `m2.py`, 2 ripetizioni, una alla volta)
(nascita = login fatto; «avvisato» = tempo dal gesto alla pagina che torna al modulo; «tutto sparito» = 0 processi e 0 sessioni logind)
| T | Run | Lavori in coda al gesto | KWin sparito | Client avvisato | Tutto sparito |
|---|---|---|---|---|---|
| 2 s | a | `plasma-ksplash start`, `xdg-desktop-portal start` | 26,6 s | **27,6 s** | 38,1 s |
| 2 s | b | stessi | 26,5 s | **28,3 s** | 38,3 s |
| 5 s | a | nessuno | 7,0 s | 8,1 s | 17,8 s |
| 5 s | b | `xdg-desktop-portal start` | 29,6 s | **30,5 s** | 40,9 s |
| 10 s | a / b | nessuno | 7,2 / 6,7 s | 8,2 / 7,7 s | 18,0 / 17,8 s |
| 25 s | a / b | nessuno | 6,6 / 3,7 s | 7,5 / 5,4 s | 18,0 / 15,3 s |
| 40 s | a / b | nessuno | 1,0 / 2,0 s | 2,7 / 2,9 s | 12,8 / 12,6 s |
| 61 s | a / b | nessuno | 1,5 / 0,9 s | 2,8 / 2,5 s | 13,3 / 12,6 s |
- Nessun residuo: tutte e 12 le prove arrivano a 0/0 (al più 41 s dal gesto); le righe tipo «(10 processi, 1 sessione)» tra l'avviso e lo zero sono il gestore utente di systemd che si spegne in ~10 s.
- Nei casi lenti (T=2, T=5b) il journal mostra la riga di systemd «Transaction for graphical-session.target/stop is destructive (xdg-desktop-portal.service has 'start' job queued…)» e REMOTIX ritenta ogni 3 s (`Plasma logout stopped halfway: stop … refused (attempt 3…7, mode fail)`), poi `accepted (attempt 8, mode fail) — the normal end follows` (T=2a: 22:16:59,99; T=5b: tentativo 7, 22:19:13,22) e KWin sparisce ~0,4-5 s dopo. I ~25 s totali sono il **tempo che il portale impiega a finire il suo avvio nel contenitore** (RealtimeKit non parte, scheda B2 del registro dei problemi); su una macchina vera il portale parte in meno di 1 s e il caso lento non dovrebbe vedersi (SUPPOSTO).
- Per T=10 e 25 s i 7-8 s di KWin sono normali (mancano i tentativi: nessun lavoro in coda).

### D3. ksmserver che non risponde — il desktop resta su finché ksmserver è bloccato (MISURATO)
`d3.py`/`d3e.py` mandano `SIGSTOP` al `ksmserver` dell'utente di prova e `SIGCONT` a 100 s.
- **Fermato un attimo prima del gesto** (`vk3` desktop di 16 s con portale in coda; `vk4` desktop di 45 s): `plasma-shutdown` non finisce mai (resta in attesa di ksmserver), quindi non scatta nemmeno la sorveglianza di REMOTIX (`session_kde_logout_watch` agisce solo quando `plasma-shutdown` lascia il nome `org.kde.Shutdown`). **REMOTIX non scrive nessuna riga** tra il gesto e il `SIGCONT`; KWin e plasmashell restano vivi (43 processi) per i 100 s della prova, il client non è avvisato. Dopo il `SIGCONT` (100,5 s) tutto si chiude da solo: client avvisato a 102,3 s, tutto sparito a 112,4 s. Nessun limite di tempo, nessuna forzatura: se ksmserver restasse bloccato per sempre, il desktop resterebbe su per sempre (è la scelta dichiarata in `session.c` ~4404: «a logout that cannot be confirmed is not worth the user's unsaved work»; ma qui anche il caso senza lavoro non salvato resta appeso).
- **Fermato nell'istante in cui `plasma-shutdown` finisce** (`vk5`, desktop di 16,6 s, Log Out buono senza lavori in coda; SIGSTOP alle 22:39:18,94): **non è riuscito a inceppare**: REMOTIX scrive 5,5 s dopo (22:39:24,494) «`plasma-shutdown ended and ksmserver does not say whether a logout is under way (GDBus.Error:…UnknownObject: No such object path '/KSMServer') — nothing is forced`» e subito dopo «`a logout is under way and KWin is still up (the workspace target stopped)… StopUnit(graphical-session.target) accepted (attempt 1)`»: sessione chiusa, client avvisato a 8,5 s, tutto sparito a 17,1 s. Cioè con ksmserver fermo REMOTIX ha atteso ~5,5 s la risposta (SUPPOSTO: la chiamata `isShuttingDown` è bloccante e ha dovuto aspettare la morte di ksmserver, ucciso da systemd alle 22:39:24,49) e poi ha usato un'altra strada. Il caso «`NoReply` a 35 s» visto una volta prima NON l'ho riprodotto.
**Conclusione D3: NON CAPITO fino in fondo** per il caso vero «risposta mai arrivata dopo la fine di `plasma-shutdown`» (non costruibile con `SIGSTOP`, perché systemd uccide ksmserver); **misurato** invece che con ksmserver bloccato PRIMA del gesto REMOTIX non ha alcun limite di tempo e il desktop resta su. Cura proposta: se `plasma-workspace.target` non cambia stato e `org.kde.Shutdown` resta posseduto da `plasma-shutdown` per più di N secondi (es. 150: oltre i 120 s di «Logging out anyway» di Plasma), dichiarare l'uscita bloccata e chiudere con la strada del prodotto (`session.c`, `session_kde_logout_watch`, accanto a `KDE_LOGOUT_TRIES`).

### D4. Rientro dopo il Log Out — FUNZIONA (MISURATO, `d4.py`)
Sessione agganciata di 40 s, gesto Log Out; la pagina è avvisata a ~1,7-1,8 s («the session has ended: the programs were closed») e **il browser rientra dopo 0,3 / 1 / 3 / 10 s dall'avviso**:
| Rientro | Ammesso | Primo desktop | Note |
|---|---|---|---|
| +0,3 s (`vr03`) | sì, subito | desktop pieno (fotogrammi in registro dalle 22:11:59, 4,4 s dopo il gesto); stabile dopo ~9 s | all'avviso restavano 18 processi e 1 sessione (gestore utente che si spegne) |
| +1 s (`vr1`) | sì, subito | stabile in ~9 s | |
| +3 s (`vr3`) | sì, subito | stabile in ~9 s | |
| +10 s (`vr10`) | sì, subito | stabile in ~9 s | |
Mai uno schermo vuoto lungo, mai un rifiuto, mai un secondo tentativo necessario. (Il testo «Admitted, new session» non l'ho letto in questa serie: lo strumento stampava un testo vuoto; che sia nata una sessione nuova lo prova la riga del figlio `FIRST frame encoded … 1344x768` con un `remotix[217503]` nuovo.)
Nota: il caso GNOME con rifiuti ritentati ogni 12 s (SCOPERTA 2) qui non si presenta.

---

## E. Portafoglio (voce 8) — FATTI (MISURATO, utente `ve1`)
Installato `libsecret-tools` per avere `secret-tool` (vedi elenco in fondo). Prima dell'uso: nessuna finestra, `kwalletd6` assente; `ksecretd` parte solo alla prima richiesta sul bus (anche una semplice `busctl status org.freedesktop.secrets` lo risveglia).
1. `secret-tool store --label=rxtest service rxtest` (segreto da stdin), con l'ambiente del bus dell'utente: **compare una finestra «KDE Wallet Service»**: «KDE has requested to create a new wallet named 'Default keyring'… Classic, blowfish encrypted file / Use GPG encryption, for better protection» (`shots/ve-e-2-after-direct.png`).
2. La finestra è di **`ksecretd`** (pid 274332): il suo registro dice `org.freedesktop.impl.portal.desktop.kwallet[274332]: Using kwallet without parent window!`. Non è `kwalletd6` (mai visto in esecuzione).
3. L'app **resta bloccata**: `secret-tool store` non è tornato in 30 s (`timeout 30` → rc=124) finché non si risponde.
4. Scelto «Classic» → Finish → **seconda finestra con richiesta di password**: «KDE has requested to open the wallet. This is used to store sensitive data in a secure fashion. Please enter a password to use with this wallet or click cancel…» con campi «Password» e «Verify» (`shots/ve-e-4-finish.png`). **È proprio una richiesta di password non voluta** (regola della 1.5.3).
5. Dopo «Cancel»: `secret-tool lookup service rxtest` → rc=1 subito, nessuna finestra; `kwallet-query -l kdewallet` → «Wallet kdewallet not found», rc=1. Nessun file creato in `~/.local/share/kwalletd/` (vuota).
6. Un primo tentativo con `box.in_session` (che non imposta l'indirizzo del bus) dà `secret-tool: Could not connect: Permission denied`: è un limite del mio modo di lanciarlo, non del desktop.
7. `src/remotix.pam` non ha righe `pam_kwallet5` (non riletto in questo giro, ripreso dalla SCOPERTA 8 e dal `grep` che mostra nessuna riga «wallet» nei due alberi).
Nessuna cura proposta (regola: come lo stesso desktop su Debian). **Non verificato**: se su Debian 13 la stessa app mostri la stessa finestra (non c'è un box Debian qui); `kwalletd6` (non `ksecretd`) potrebbe esserne il proprietario con KDE 6.3.

---

## Che cosa ho creato / installato nel box
- Installato: `libsecret-tools` 0.21.7-2build1 (`apt-get install -y libsecret-tools`, lasciato). Non toccati: pacchetto REMOTIX, `labwc`, kwrite (già lì).
- File in `/media/REMOTIX-UBUNTU/lavoro/verifiche-kde/` (miei) e nuove istantanee in `prove/shots/` (v-va2-*, vb2-*, vc-*, vd1-*, vd3-*, ve-e-*, desk-canvas-*-261118-22xxxx, ecc.).
- File nel box (`/tmp`): `fakess.py`, `fakess-va2.log`, `mon-A1.txt`, `mon-va2.txt`, `hold-*.{ready,done,cmd.done,out,stop}`, `vs-stop-vk5.txt`, `vc-*.out`, `vd-*.out`, `vm-*.out`, `vs-*.out`, `vd1-*.out`, `e-store.out`, `vb2-*-kwin.png`, `rx-geom-*`.
- Utenti di prova creati (senza processi né sessioni): `va1…va5`, `vb1…vb6`, `vc1…vc4`, `vs1…vs4`, `vk1…vk5`, `vr03 vr1 vr3 vr10`, `vt2a vt2b vt5a vt5b vt10a vt10b vt25a vt25b vt40a vt40b vt61a vt61b`, `ve1`, `vz1`, e `dk5`/`dkf` (creati da `check-desktop.py`).
- Cambiato e rimesso: processi di prova e 24 cicli a vuoto (finiti); nessun file del prodotto, nessuna configurazione di sistema.
- Stato finale: `loginctl list-users` vuoto, nessun processo di utenti di prova, nessun ciclo a vuoto.

## Elenco dei difetti per gravità
1. **C** — figlio vivo e login «resumed» a schermo vuoto dopo il Log Out a sessione staccata (KDE; stessa famiglia di XFCE). Medio: nessuna perdita, ma un giro a vuoto di ~12 s e processi rimasti per sempre.
2. **A** — Ctrl+Alt+Canc non mostra la schermata di uscita (Plasma ≥ 6.4 + `--no-lockscreen`). Medio-basso: l'utente ha comunque il menu «Esci».
3. **E** — finestra di creazione del portafoglio e richiesta di password alla prima richiesta di un segreto. Medio (regola 1.5.3), decisione tua.
4. **D3** — ksmserver bloccato: desktop su finché dura il blocco, nessun tempo massimo. Basso (richiede un blocco vero di ksmserver).
5. **B** — non è il prodotto: da correggere la prova.
