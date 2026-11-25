# Rapporto di analisi KDE (Plasma/KWin 6.3.6, sddm 0.21) — REMOTIX 1.2.0 per Debian 13

Agente: analisi KDE. VM usata: `kde` (solo `accendi kde virtuale`, due accensioni, spenta alla fine; nessun posto in `turni` preso: la regola è cambiata a metà lavoro). File di misura e diff grezzi in `kde-tmp/` (accanto a questo file).
Convenzione: **[V]** = verificato (codice letto o misura nella VM), **[D]** = dedotto. Righe di codice di `debian13/src` salvo diverso avviso.

## 0. Riepilogo in una pagina

| Voce | Verdetto |
|---|---|
| A6 (forzata su `graphical-session.target`) | PORTABILE COSÌ, ma NON SERVE per il difetto di Fedora: su Plasma 6.3.6 fermare `plasma-workspace.target` o `graphical-session.target` ferma tutto nello stesso tempo (0,37 s contro 0,47 s). Resta innocuo e uniforme. |
| A7 (5 s invece di 10) | PORTABILE COSÌ (scelta di comportamento già decisa dal proprietario; ~6 righe). Su Debian il margine verso i 13 s della parte root è enorme (forzata + 0,46 s). |
| U7 (chiusura KDE «Plasma muore in silenzio») | Va divisa in due. (a) Spostamento del controllo `kwin_closed()` prima del `continue` «nessuno guarda» in `child.c`: vale su qualunque Plasma, PORTABILE COSÌ. (b) Il watch nuovo di `session.c` (rilascio del nome `org.kde.Shutdown` + `isShuttingDown`): nato su Plasma 6.6; su 6.3.6 il segnale vecchio (che Debian ha già) c'è e funziona; la parte nuova è PORTABILE e innocua, ma NON SERVE per un difetto misurato su 6.3.6. |
| U5 (fotogramma perso, `kwin_poke`) | PORTABILE COSÌ (guardia a runtime con interruttore di sicurezza, innocua se non scatta). Resta DA PROVARE COL PRODOTTO se su KWin 6.3.6 scatta mai. Dipende dal «pixel» di `kwin.c`, che Debian ha già. |
| U6 (sidecar `org.freedesktop.ScreenSaver`) | PORTABILE COSÌ; su 6.3.6 il codice di Plasma che lo interroga c'è già (`libkworkspace6` 6.3.6 contiene `GetActive`). Che Ctrl+Alt+Canc sia davvero rotto senza di esso su 6.3.6: DA PROVARE COL PRODOTTO. Innocuo se non serve. |
| D1, D2, D3, D4 | NON PORTABILI, confermato (D2 misurato: KWin 6.3.6 offre `kde_output_management_v2` versione **12**, serve ≥ 22, e NON offre `kde_output_device_registry_v2`). |
| Base giusta per i file KDE di Debian | **Ubuntu** (non Fedora). Il KDE di Fedora ha tolto le chiamate a labwc da `child.c`; Ubuntu no. Con Ubuntu come base si copiano i file e si rimettono a mano 3 punti di `kwin.c` (labwc di distribuzione). |
| E2 (`force_guard_on`) | PORTABILE COSÌ; su Debian oggi l'effetto è praticamente nullo (un solo punto di chiamata più `session_ensure`). |
| B3, A9 | PORTABILI CON ADATTAMENTO: 4 testi runtime + commenti; il rimedio giusto per un `.deb` da file è `apt install --reinstall ./remotix_<versione>_amd64.deb` (verificato con `apt-get -s` nella VM). |
| C7 per sddm | Verificato: sddm, sddm-greeter e sddm-autologin includono tutti `common-session` (una volta); la riga di `pam-auth-update` li copre. |

Scoperte fuori elenco (dettagli nel §7): Debian ha già `session_kde_logout_watch` (vecchia versione) e `force_guard_on`; manca solo il resto. `really_terminate()` di Debian non ha il ramo «nessuna sessione = chiusura riuscita» di Ubuntu/Fedora. Il PATH della sessione locale di Plasma su Debian non è quello fisso del figlio. KWin 6.3.6 non elenca `zkde_screencast_unstable_v1` a un client qualunque (è ristretto): non è un problema nuovo ma è bene saperlo. `labwc` non è installato nella VM: la strada labwc-di-distribuzione NON è stata misurata qui.

---

## 1. A6 e A7 — chiusura forzata di KDE per accesso locale (struttura reale delle unità su Plasma 6.3.6)

### 1.1 Che cos'è
A6: quando l'accesso locale chiede la chiusura completa del desktop remoto e il programma non si chiude da solo, la strada forzata ferma `graphical-session.target` invece di `plasma-workspace.target`. A7: in quella stessa chiusura (solo KDE, solo accesso locale) la chiusura gentile aspetta 5 s invece di 10.

### 1.2 Stato in `debian13/` oggi [V]
- `exit_kde()` `session.c:3646-3668`: forzata = `StopUnit(SESSION_UNIT_PLASMA="plasma-workspace.target","fail")` (riga 3658); ordinata = `org.kde.Shutdown.logout`.
- `really_terminate()` ramo KDE `session.c:4528-4547`: `exit_kde(FALSE) && wait_until_done()` (10 s: `WAIT_EXIT_MS` riga 108, `wait_until_done()` riga 3622), poi `force_refused()`, poi `exit_kde(TRUE)`.
- `session.h:136` definisce solo `SESSION_UNIT_PLASMA`; manca `SESSION_UNIT_GRAPHICAL` (Ubuntu/Fedora lo hanno, `session.h:120` di Fedora).
- La parte root (`rootside.c:2428` `PL_GRACE_MS 13000`) è identica a Ubuntu/Fedora: 13 s dalla richiesta.

### 1.3 Struttura delle unità utente su Plasma 6.3.6 [V] (VM `kde`, sessione Plasma locale di `prova`, `systemctl --user show`/`cat`/`list-dependencies`; file `kde-tmp/m1.out`)
- `plasma-workspace.target`: `Requires=plasma-core.target graphical-session.target`, **`BindsTo=graphical-session.target`**, `StopWhenUnneeded=yes`, `RequiredBy=plasma-workspace-wayland.target`.
- `graphical-session.target`: `RequiredBy`/**`BoundBy=plasma-workspace.target`**, `StopWhenUnneeded=yes`, `RefuseManualStart=yes`, `RefuseManualStop=no` (si può fermare a mano); `ConsistsOf` tutte le unità `plasma-*`, `app-*@autostart`, portali.
- `plasma-workspace-wayland.target`: `Requires=plasma-kwin_wayland.service plasma-workspace.target`, `BindsTo=plasma-kwin_wayland.service`.
- `plasma-kwin_wayland.service`, `plasma-ksmserver.service`, `plasma-plasmashell.service`: **`PartOf=graphical-session.target`**. Le app lanciate da Plasma sono scope `app-org.kde.*.scope` (`KDE_APPLICATIONS_AS_SCOPE=1`).
- `list-dependencies --reverse graphical-session.target`: `plasma-workspace.target` → `plasma-workspace-wayland.target`.

Quindi la costruzione è la stessa di Fedora (kwin/ksmserver/plasmashell `PartOf=graphical-session.target`; `plasma-workspace.target` `BindsTo` lui).

### 1.4 Misure dei tempi [V] (stessa VM, tre accessi locali; `kde-tmp/m2-*.out`, `m7-*.out`)
Sondaggio ogni 50 ms di stato unità e processi (`kwin_wayland`, `plasmashell`, `plasma-shutdown`).

| Caso | Risultato |
|---|---|
| Logout normale (`org.kde.Shutdown.logout`), desktop vuoto | `plasma-workspace.target` va inattivo a ~0,35 s, `graphical-session.target` poco dopo, tutto morto a 0,76 s. Il gestore di Plasma ferma PRIMA `plasma-workspace.target` (segnale vecchio presente). |
| `systemctl --user stop plasma-workspace.target` (quello che fa Debian oggi), desktop vuoto | tutto morto a **0,37 s** |
| `systemctl --user stop graphical-session.target` (quello che fa Fedora), desktop vuoto | tutto morto a **0,47 s** |
| Konsole con `top`, logout normale | si chiude da solo, tutto morto a 0,7 s: su 6.3.6 Konsole+top NON blocca il logout (sulla macchina vera di Fedora con Plasma 6.8 sì) |
| **kwrite con testo non salvato** + logout (blocco vero: `plasma-shutdown` resta vivo, finestra di conferma), forzata dopo 5 s con `plasma-workspace.target` | forzata a 5,15 s, tutto morto **0,46 s** dopo |
| Stesso blocco, forzata dopo 5 s con `graphical-session.target` | forzata a 5,09 s, tutto morto **0,46 s** dopo |

Conclusione [V]: su Plasma 6.3.6 i due modi sono equivalenti nel tempo. Il difetto di F36 (causa 2: `graphical-session.target` che se ne va ~4,5 s dopo `plasma-workspace.target`, oltre la scadenza dei 13 s) **non si riproduce** qui, perché la catena `BindsTo`/`PartOf` si smonta subito. Il ritardo di 4,5 s è quindi un comportamento di Plasma 6.8 (non misurato da me: [D] dal registro F36).

### 1.5 Verdetto
- **A6: PORTABILE COSÌ** (stessa cosa, stessa velocità, e allineata a Fedora/uniformità). **NON SERVE** per correggere un difetto su Debian 13. Costo ~12 righe in `session.c`: aggiungere `#define SESSION_UNIT_GRAPHICAL "graphical-session.target"` a `session.h`, cambiare l'argomento di `StopUnit` in `exit_kde()` (riga 3658), aggiornare il commento e il messaggio di `really_terminate()` (riga ~4540). Dipendenze: nessuna.
- **A7: PORTABILE COSÌ.** Fedora `session.c:109-113` (`#define KDE_PRELOCAL_ORDERLY_MS 5000`), `wait_until_done_ms(gint64 ms)` (Fedora `4561`), `wait_until_done()` la chiama con `WAIT_EXIT_MS`; nel ramo KDE di `really_terminate()` `wait_until_done_ms(force_guard_on ? KDE_PRELOCAL_ORDERLY_MS : WAIT_EXIT_MS)` (Fedora `5639`). ~10 righe. `force_guard_on` è già in Debian (riga 4455). Dipende da E2 (vedi sotto) solo nel senso che la scelta 5 s/10 s legge quella variabile.
- Cambio di comportamento per l'utente (da approvare, ma già deciso per Fedora): su KDE, nella chiusura per accesso locale, una chiusura sana fra 5 e 10 s viene troncata dalla forzata. Su Debian/6.3.6 la forzata costa 0,46 s, quindi l'accesso locale si libera a ~5,5 s invece di ~10,5 s.
- Misurato in VM: tutto quanto sopra. Resta DA PROVARE COL PRODOTTO: (1) la stessa prova con la strada labwc-di-distribuzione (nella VM `labwc` non è installato, quindi KWin non era dentro labwc: il labwc e il ticker vivono nel cgroup di `plasma-kwin_wayland.service`, [D] muoiono con lo stop dell'unità); (2) P7/P8 di `check-prelocal.py` su KDE; (3) la prova «locale chiude il remoto» con programmi aperti, su macchina vera (regola F36).

---

## 2. U7 — chiusura KDE «Plasma muore in silenzio» (PHASE 12, `session_kde_logout_watch`)

### 2.1 Che cos'è
Quando l'utente fa «Log Out» dal menu del desktop remoto, REMOTIX deve accorgersene e chiudere tutto, anche se Plasma si ferma a metà. Due pezzi: (a) in `child.c`, il controllo «KWin è sparito» (`kwin_closed(stage_kwin)`) e quello che ne segue; (b) in `session.c`, `session_kde_logout_watch()`, che vigila il logout e, se Plasma non completa, ferma `graphical-session.target`.

### 2.2 Stato in `debian13/` oggi [V]
- `session.c:4226 void session_kde_logout_watch(void)` (vecchia versione): segnale unico = `plasma-workspace.target` visto attivo e poi non attivo mentre KWin è ancora sulla bus; dopo `KDE_LOGOUT_GRACE_MS`=4000 chiede `StopUnit("graphical-session.target","fail")`, ritenta `KDE_LOGOUT_TRIES` volte, poi rinuncia (returns void). Usa `name_has_owner` a due risposte.
- `child.c:12023-12042`: controllo `stage_kwin && kwin_closed(stage_kwin)` DOPO il `continue` «nessuno guarda il flusso».
- `child.c:10406-10407`: `session_kde_logout_watch();` senza valore di ritorno.

### 2.3 Differenze in Ubuntu [V] (diff `kde-tmp/du-session.diff` righe ~1395-1640, `du-child.diff`)
1. `child.c`: il controllo `kwin_closed()` è spostato PRIMA del `continue` «nessuno guarda» (18 nov, Kubuntu: «Log Out» con il browser chiuso lasciava il figlio vivo per sempre, 11 processi, 2 sessioni logind). È un difetto di LOGICA del figlio, non di Plasma.
2. `session.c`: `session_kde_logout_watch()` diventa `bool`; nuovo segnale (rilascio del nome `org.kde.Shutdown` via `NameOwnerChanged` + risposta di `ksmserver.isShuttingDown()`), perché su Plasma 6.6 `plasma-shutdown` chiede lo stop di `graphical-session.target` e **non ferma mai** `plasma-workspace.target`; dopo `KDE_LOGOUT_TRIES` rifiuti passa a modo `replace`, dopo altrettanti rinuncia e ritorna TRUE; `child.c:10553-10567` (numerazione Ubuntu) in quel caso chiude con la strada del prodotto (`terminate_and_clear()`).
3. `name_owner_three()` (tre risposte) e `session_life()`; `inactive_unit(const char **busy)`.

### 2.4 Che cosa vale su Plasma 6.3.6
- Il segnale NUOVO non serve per un difetto di 6.3.6: **[V]** nella VM, al logout `plasma-workspace.target` si ferma per primo (inattivo a ~0,35 s mentre `graphical-session.target` e KWin sono ancora attivi, poi tutto a 0,7 s): il segnale vecchio che Debian già usa c'è e scatta.
- I pezzi usati dal nuovo watch ESISTONO su 6.3.6 [V]: `org.kde.ksmserver /KSMServer org.kde.KSMServerInterface.isShuttingDown` risponde `(false,)`; il nome `org.kde.Shutdown` è di `plasma-shutdown` (`pshut=1` durante il logout; processo `plasma-shutdown` presente in `/usr/bin`).
- Lo scenario che Ubuntu cura (logout chiesto nei primi secondi del desktop, stop di `graphical-session.target` rifiutato dal manager) non l'ho potuto riprodurre: [D] possibile anche su 6.3.6 (è un comportamento di systemd/job in coda), ma non misurato.

### 2.5 Verdetto
- **(a) spostamento di `kwin_closed()`: PORTABILE COSÌ**, piccolo (~25 righe in `child.c`, prendere il blocco di Ubuntu `child.c:11743-11769` con il commento). Indipendente dalla versione di Plasma. NON cambia il comportamento visibile se la sessione muore con un client collegato; cambia (in meglio) il caso «nessun client».
- **(b) watch nuovo: PORTABILE COSÌ ma NON SERVE** per un difetto misurato su 6.3.6. Se lo si porta (medio: ~100 righe in `session.c` + il cambio di firma in `session.h:561` + ~15 righe in `child.c`) conviene portarlo intero insieme a `name_owner_three`/`session_life` (U3/U9 dipendono da `session_life`). Rischio: nessun cambio di comportamento per l'utente salvo il caso «logout non completato»: dopo ~1 minuto chiude di forza (richiede approvazione). Se il piano è «porta Debian al livello di Ubuntu», va con U3; se il piano è «solo ciò che serve», si può tralasciare e annotare «non provato su Debian».
- Da provare col prodotto: logout dal menu con browser collegato, con browser chiuso (caso Kubuntu), con kwrite non salvato; nessun figlio/sessione logind rimasti.

---

## 3. U5 — fotogramma perso di KWin

### 3.1 Che cos'è
KWin numera ogni buffer che manda a PipeWire; se nella numerazione c'è un buco, un fotogramma si è perso e può essere stato l'ultimo di un'animazione (finestra rimasta a metà). REMOTIX allora «tocca» KWin con il suo pixel trasparente (`kwin_poke`) per far disegnare un fotogramma intero.

### 3.2 Stato in `debian13/` oggi [V]
Assente: `grep capture_watch_sequence|kwin_poke` in `debian13/src` = nessun risultato. Ma esiste già tutto il supporto: in `kwin.c:99-102`, `pixel_surface`/`pixel_buf`/`pixel_configured` e `pixel_configure()` (386-396).

### 3.3 Cosa si porta [V]
- `capture.c`/`capture.h`: copia di Ubuntu (identica a Fedora: `diff` Ubuntu↔Fedora = 0 righe). Diff Debian↔Ubuntu `capture.c` 146 righe, `capture.h` 62: tutto U5 (`seq_watch`, `lost_*`, `capture_watch_sequence`, `capture_frame_lost`, costanti `LOST_QUIET_MS 200`, `LOST_POKES_MAX 10`, `SEQ_WINDOW 600`).
- `kwin.c/kwin.h`: `GMutex pixel_lock` (+init/clear, lock in `pixel_configure`), funzione `kwin_poke()` (`ubuntu26.04/src/kwin.c:586-611`).
- `child.c` (Ubuntu): 2 chiamate `capture_watch_sequence(cat/new_one)` (Ubuntu 9061, 9736), due statiche `lost_said_ms`/`lost_unsent_said` (5896), il blocco nel giro principale (12228-12263).
- Dipendenze: nessuna altra voce. Dimensione: medio (~230 righe, di cui ~190 commenti/capture).

### 3.4 Vale su KWin 6.3.6?
- Misurato solo su KWin 6.6.7 (Kubuntu). Il presupposto è «KWin numera ogni buffer con `seq`» (`screencaststream.cpp`, `addHeader()`): [D] vale anche per 6.3.6 (stessa classe `ScreenCastStream`), non verificato.
- **Innocua se non scatta [V sul codice]:** `lost_need` si attiva solo con un buco nella numerazione; l'interruttore di sicurezza spegne il conteggio se più di metà dei 600 buffer mostrano buchi (una numerazione diversa non può far partire tocchi a raffica); massimo 10 tocchi di fila; `kwin_poke()` fallisce senza effetti se manca pixel/connessione. Nessun input, nessun riavvio del flusso.
- Da provare col prodotto: sessione KDE con animazioni (apertura di finestre/Firefox) su 6.3.6 dentro labwc 0.8.3: contare nel registro le righe «a buffer of KWin never arrived» (se compaiono: serve; se mai: innocuo).
- Verdetto: **PORTABILE COSÌ**, DA PROVARE COL PRODOTTO per sapere se serve. Cambio di comportamento utente: nessuno visibile (solo registro).

---

## 4. U6 — sidecar `org.freedesktop.ScreenSaver` (Ctrl+Alt+Canc)

### 4.1 Che cos'è
Con KWin avviato con `--no-lockscreen` (fatto da REMOTIX: `session.c:2988`, `3039`), nessuno possiede il nome `org.freedesktop.ScreenSaver`; da Plasma 6.4 `requestLogoutPrompt()` lo interroga (`GetActive`) e legge l'errore come «schermo bloccato»: Ctrl+Alt+Canc non apre la schermata di uscita. Un processo satellite risponde «non bloccato» a tutto, e inoltra `Inhibit` a powerdevil (misurato su VLC).

### 4.2 Stato in `debian13/` oggi [V]
Assente (`kwin.c` di Debian non ha `SCREENSAVER_NAME`). Il satellite di Ubuntu (`ubuntu26.04/src/kwin.c:1315-1487` + fork a `1642-1651`) parte solo nella strada labwc (`if (ticker >= 0)` dentro `kwin_nested_alive`); nella strada di ripiego `--virtual` (labwc non installato) NON parte, come in Ubuntu.

### 4.3 Su Plasma 6.3.6 [V]
- In una sessione locale di 6.3.6 il nome `org.freedesktop.ScreenSaver` (e `org.kde.screensaver`) è posseduto da KWin (`GetNameOwner` = `:1.19`, `GetActive` = `(false,)`): è il demone della schermata di blocco dentro KWin.
- `libkworkspace6.so.6` (plasma-workspace 6.3.6) contiene `SessionManagement::requestLogoutPrompt`, `OrgFreedesktopScreenSaverInterface`, `GetActive`, `GetActiveTime`: cioè il codice che interroga ScreenSaver **c'è già in 6.3.6** (lo studio dice «da 6.4»: la stringa c'è, ma non so se la chiamata è nello stesso percorso di `requestLogoutPrompt`; [D]).
- `org.freedesktop.PowerManagement.Inhibit` (powerdevil) c'è su 6.3.6 [V]: l'inoltro di `Inhibit` avrebbe un destinatario.

### 4.4 Verdetto
**PORTABILE COSÌ** (le parti di Ubuntu non dipendono dal labwc; `kwin.c` Ubuntu 1315-1487 + fork). Dimensione medio (~190 righe, solo `kwin.c`). Innocuo se non serve: il satellite prende il nome con `DO_NOT_QUEUE` e si ferma da solo se qualcuno lo possiede. **DA PROVARE COL PRODOTTO:** su 6.3.6, in una sessione REMOTIX senza satellite, Ctrl+Alt+Canc apre o no la schermata di uscita? Se sì già adesso, il satellite non serve (ma resta innocuo; l'unico effetto visibile nuovo: le app che chiamano `Inhibit` su ScreenSaver, es. VLC, avrebbero un'inibizione vera invece di `ServiceUnknown`; l'inoltro è stato misurato su 6.6 e non su 6.3.6). Cambio di comportamento utente: Ctrl+Alt+Canc potrebbe passare da «non fa nulla» a «apre la schermata di uscita» (da approvare).

---

## 5. D1, D2, D3, D4 — conferma «non si portano» e come tenere viva la strada labwc

### 5.1 Misure [V]
- `kwin_wayland --help` (6.3.6): opzioni `--virtual`, `--width/--height/--scale`, `--drm`, `--socket`, `--wayland-fd`, `--xwayland*`, `--no-lockscreen`, `--no-global-shortcuts`, `--exit-with-session`, `--locale1`, `--inputmethod`, `--wayland-display`, `--x11-display`. Nessuna opzione per cambiare la dimensione a caldo. (`kde-tmp/m5.out`)
- Protocolli offerti dal KWin in esecuzione (`wayland-info` sulla sessione locale): `kde_output_management_v2` **versione 12**, `kde_output_device_v2` versione 11, `kde_output_order_v1`; NESSUN `kde_output_device_registry_v2`. Stringhe nel pacchetto `libkwin.so.6.3.6`: `kde_output_management_v2` presente; `add_cvt`, `set_custom_modes`, `kde_mode_list_v2`, `kde_output_device_registry_v2` ASSENTI. (`kde-tmp/m10.out`, `m9.out`). Il codice di Fedora richiede versione ≥ 22 e il registry (`fedora45/src/kwin.c`, `out_global`, `kwin_output_resize`).
- `zkde_screencast_unstable_v1` non appare nell'elenco dei globali visto da un client qualunque (è ristretto ai client autorizzati: `org.kde.remotix.desktop`, `kwin_check_permission` `kwin.c:~760`): niente di nuovo, solo per sapere.

### 5.2 Verdetto per voce
- **D1** (`--kwin-virtual`, `REMOTIX_KDE_HOST=1`, `kdehost.h` di Fedora, `main.c` Fedora 2885-2891): NON PORTABILE. Su Debian `--virtual` è solo il ripiego dichiarato quando labwc manca. Fedora, in più, RIFIUTA la sessione se KWin non offre il protocollo (`kde_refused`): su 6.3.6 la rifiuterebbe sempre.
- **D2** (`kwin_output_resize`, protocolli `kde-output-*.xml`, `Makefile` Fedora 291-298): NON PORTABILE (versione 12 < 22, registry assente). Non copiare i due XML né le righe del `Makefile`.
- **D3** (ciclo nascita/riaggancio KDE di `child.c`): NON PORTABILE. Fedora ha SOSTITUITO `kwin_host_settle()` e `kwin_host_resize()` con `kwin_output_resize()` (Fedora `child.c:9217-9273` e `11663-11678`, `kde_refused`). Debian/Ubuntu: `child.c:8875` e `11183-11185`.
- **D4** (plasmalogin): NON SERVE su Debian 13: sddm. Nella VM `apt-cache policy plasma-login-manager plasmalogin` non trova nulla [V]. Da rivedere con Plasma 6.8 (Debian forky).

### 5.3 Come tenere intatta la strada «KWin dentro labwc di distribuzione»
La strada labwc di Debian = `remotix --kwin-nested W H NODE -- wrapper…` come `ExecStart` di `plasma-kwin_wayland.service` (`session.c:~3030`, `main.c:2839`) → `kwin_nested_alive()` (`kwin.c:1282`): avvia `labwc` da `PATH` (1314-1330, 1377 `execlp("labwc",…)`), ticker (1419-1440), poi esegue il wrapper con `--wayland-display`; senza labwc ripiega su `--virtual` a misura fissa (1316-1330). Il figlio usa `kwin_host_settle()`/`kwin_host_resize()`/`kwin_host_exists()` (`child.c:8875`, `11183`), `kdehost.h` con `KDEHOST_MARK "remotix-kwin-host"` e `KDEHOST_OPTION "--kwin-nested"`.

Regole da rispettare portando il resto:
1. **NON** prendere da Fedora: `kdehost.h` (cambia i segni), `main.c` (rinomina `--kwin-nested` in `--kwin-virtual` e lo rifiuta: Fedora `main.c:2885-2891`), `Makefile` (`kde-output-*`, `-lselinux`), `child.c` blocchi `kde_refused`/`kwin_output_resize`, `session.c` ramo `--kwin-virtual` (Fedora `3930-3956`, `Environment=REMOTIX_KDE_HOST=1`). Tutto quello che Fedora ha di KDE oltre a A6/A7 è D.
2. Da Fedora si porta solo A6/A7 (e i testi B3), in `session.c`.
3. Da Ubuntu `kwin.c`: prendere il file intero MA rimettere i tre punti del labwc di distribuzione (diff Debian↔Ubuntu `kwin.c`: 249 righe, di cui solo ~14 sono labwc):
   - commento e `labwc_path = g_find_program_in_path("labwc");` al posto di `access(REMOTIX_LABWC, X_OK)` (Debian 1314-1318 / Ubuntu 1520-1529);
   - messaggio «⛔ labwc is not installed» (Debian 1325, non «our labwc»);
   - `execlp("labwc", "labwc", "-C", config, NULL)` (Debian 1377) al posto di `execl(labwc_path,…)`.
   Debian NON deve avere `-DREMOTIX_LABWC` nel `Makefile` (Ubuntu `Makefile:128-133`; U12 non si porta).
4. `kdehost.h`, `session.c`'s `write_dropin()` KDE e `main.c:2839` restano come sono: sono identici fra Debian e Ubuntu per la parte KDE [V] (`diff`: `kdehost.h` 0 righe).
5. `child.c` e `session.c` di Ubuntu includono molto altro non-KDE (GNOME 50, dconf, U1-U4): si porta per voce, non a file intero.

### 5.4 Base giusta e differenza Debian↔Ubuntu
**Base = Ubuntu** per i file KDE (kwin.c, capture.c/h, parti KDE di child.c/session.c). Motivo [V]: Fedora ha rimosso dal flusso i punti che Debian usa; Ubuntu ha ancora labwc-per-KDE vivo e il diff Debian↔Ubuntu per KDE è piccolo e chiaro. Differenza fra le due strade labwc: Debian usa il labwc di distribuzione 0.8.3 (wlroots 0.18, `Recommends: labwc`; `apt-cache depends labwc` nella VM: `libwlroots-0.18`); Ubuntu un labwc 0.9.3 + wlroots 0.19.2 PATCHATI e statici, a `/usr/libexec/remotix/labwc`, perché il labwc di Ubuntu con KWin ≥ 6.5 non riporta mai i fotogrammi come presentati (`ubuntu26.04/studio/10-kde-controprova-labwc.md`: 759 `presented` col nostro, 0 con quello di Ubuntu; Firefox fermo). Con KWin 6.3.6 questo difetto non è mai stato visto su Debian [D: l'esperimento è di Ubuntu con 6.6.7]. U12 (labwc nostro) non si porta.

---

## 6. E2, B3, A9

### 6.1 E2 — `force_guard_on`
- Che cos'è: variabile `static bool force_guard_on` (+ `force_guard_ppid`) impostata dal figlio con `session_force_unless_orphaned(ci.a == PRELOCAL)`; se il genitore sparisce durante una chiusura per accesso locale, i passi forzati vengono saltati (`force_refused()`).
- Debian [V]: `session.c:4455-4474`; impostata in un solo punto del figlio `child.c:10968` (stesso valore a ogni chiusura, quindi si riazzera da sola); `session_ensure()` chiama `session_terminate()` a `session.c:7332` senza riazzerare.
- Il «resta acceso» di Fedora: dopo una chiusura PRELOCAL fallita la variabile resta `true`. In Ubuntu/Fedora i punti di chiamata sono tre e quelli aggiunti (scala rifiutata, watch KDE) riazzerano con `session_force_unless_orphaned(false)` (Ubuntu `child.c:10529`, `10562`). In Debian, dove c'è solo il punto di `child.c:10968` e `session_ensure`, un `true` rimasto può influire solo su una chiusura fatta da `session_ensure` (stato «misura sbagliata» nello stesso figlio) e, con A7, sul tempo 5 s/10 s di quella chiusura.
- Verdetto: **PORTABILE COSÌ** (nessuna modifica; si annota il limite come in Fedora). Se si porta U7(b)/U3, copiare i due `session_force_unless_orphaned(false)` di Ubuntu.

### 6.2 B3 — «reinstalla il pacchetto»
Occorrenze in `debian13/src`:
- `kwin.c:779` (RX-KDE-001), `kwin.c:790` (RX-KDE-002), `kwin.c:807` (RX-KDE-003): «Remedy: reinstall the package (apt install --reinstall remotix)» (stringhe a runtime, vanno all'amministratore).
- Commenti: `kwin.c:730` (`packaging/{debian,rpm,arch}`), `kwin.c:741` («`/usr/lib/remotix/remotix` on Arch»); non sono testi visibili.
Verificato nella VM [V] (`apt-get -s`): `apt-get install --reinstall ./tzdata_….deb` dà «1 reinstalled»; `apt-get -s install --reinstall remotix` per un nome senza candidato dà «E: Unable to locate package». [D] per un `.deb` installato da file `apt install --reinstall remotix` non può ricuperare il file (nessun archivio lo offre).
**Testo proposto** (parallelo a Fedora «reinstall the package from its file (sudo dnf reinstall ./remotix-<version>.rpm)»): `Remedy: reinstall the package from its file (sudo apt install --reinstall ./remotix_<version>_amd64.deb)`. Fedora: `kwin.c` 812, 823, 840 (Ubuntu 812 ecc.). Piccolo (3 stringhe + 2 commenti).

### 6.3 A9 — residui «Fedora and Arch» e dintorni (`main.c`)
Tutte le occorrenze in `debian13/src` (grep `Fedora|\.fedora|\.suse|\.arch|openSUSE|Arch`):
- **Runtime (da correggere):** `main.c:469-473`, messaggio «PAM service remotix does not exist»: «on Fedora and Arch it is pam_deny … on Debian the common stacks … Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch.» Testo corretto proposto (come Fedora, adattato): «…will fall back to the «other» service, which is NOT the REMOTIX stack (on Debian it includes the common stacks, without the exclusion of root, and every login of the system would be judged by it). The package installs that file: reinstall the package from its file (sudo apt install --reinstall ./remotix_<version>_amd64.deb).» (La frase su `pam_deny` va tolta: su Debian non vale.)
- **Commenti (consigliato ripulire, non visibili):** `main.c:439` («on Fedora and Arch other is pam_deny»), `main.c:447` («where the openSUSE package puts it»; il secondo percorso `/usr/lib/pam.d/remotix` resta nel codice `main.c:~455`, innocuo), `remotix.pam:6, 30-39` (Fedora/openSUSE/Arch), `kwin.c:730, 741`.
- **Da NON toccare (misure storiche, tracciabilità):** `authentication.c:93-103`, `card_pick.c:17`, `certificates.c:152`, `child.c:9704, 9714, 11527`, `session.c:753, 760, 1595, 3351, 3826, 4829, 5572, 5583, 6408`, `remotix-remote-sessions.rules:15-68` (note `[M]` su altre distribuzioni; come in Ubuntu).
Verdetto: **PORTABILE CON ADATTAMENTO** (solo testo). Piccolo.

---

## 7. Il mio desktop: sddm, `common-session`, PATH, LANG (C7) [V]

- `/etc/pam.d/sddm` (VM `kde`): `@include common-session` UNA volta (dopo `pam_selinux close`, `pam_keyinit`, `pam_limits`, `pam_loginuid`; prima di `pam_selinux open`, `pam_kwallet5`/`gnome_keyring`); poi `@include common-password`; in coda `pam_env` con `/etc/environment` e `envfile=/etc/default/locale user_readenv=1`. Stessa cosa in `/etc/pam.d/sddm-autologin` (con `pam_env envfile=/etc/default/locale`) e in `/etc/pam.d/sddm-greeter` (include `common-session`; lì non c'è `pam_env`). Quindi la riga di `pam-auth-update` (`debian/remotix.pam-config`: `Session-Type: Additional`, `Session-Interactive-Only: yes`, `optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login`) finisce in `common-session` dopo `pam_unix`/`pam_systemd`, e viene eseguita per login, autologin E anche per il greeter (utente `sddm`): il programma deve ignorare chi non ha un desktop remoto (registro A2 di Debian: «esce subito se il servizio è fermo», «provato dal proprietario con le live Debian»). `pam-auth-update` in VM ha profili: fprintd, gnome-keyring, mkhomedir, systemd, unix (nessun conflitto).
- Sessione Plasma locale (sddm, Wayland), `/proc/<plasmashell>/environ` [V]: `LANG=en_US.UTF-8` (da `/etc/default/locale` via `pam_env`; nessun `LC_*`, nessun `LANGUAGE`); `PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games`; `SHELL=/bin/bash`; `XDG_SESSION_TYPE=wayland`, `XDG_CURRENT_DESKTOP=KDE`, `DESKTOP_SESSION=plasma`, `XDG_SESSION_DESKTOP=KDE`, `KDE_FULL_SESSION=true`, `KDE_SESSION_VERSION=6`, `KDE_SESSION_UID`, `KDE_APPLICATIONS_AS_SCOPE=1`, `XDG_CONFIG_DIRS=/home/prova/.config/kdedefaults:/etc/xdg:/usr/share/desktop-base/kf5-settings`; `QT_ACCESSIBILITY=1`, `QT_IM_MODULE=ibus` per KWin.
- Come arriva il PATH [V]: la sessione sddm è `Exec=…/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland` avviata da `/usr/share/sddm/scripts/wayland-session`, che con `SHELL=*/bash` fa `exec $SHELL --login -c 'exec "$@"'`: quindi `/etc/profile` (non-root: `/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games`) e `~/.profile`, che aggiunge `~/bin` e `~/.local/bin` SE le cartelle esistono (nella VM non esistono: `ls` negativo). [D] su una macchina con `~/.local/bin` il PATH locale lo include. Il PATH del gestore utente è lo stesso senza home (`systemctl --user show-environment`).
- Confronto con Debian oggi: il figlio usa `PATH=/usr/local/bin:/usr/bin:/bin` fisso (`child.c:1781`) e `SHELL=` vuoto (`child.c:1782`): mancano i `games` e `~/.local/bin`/`~/bin`, e la shell. La differenza del PATH vale per KDE come per gli altri (voce A3, non solo KDE): per KDE significa che i comandi in `~/.local/bin` non si avviano dal menu e da Konsole del desktop remoto (la `.profile` non viene letta dalla nostra strada). [V per il confronto di valori, D per l'effetto].
- Lingua [V]: la lingua locale di Plasma viene da `/etc/default/locale` (`LANG`) e poi da `~/.config/plasma-localerc` letta da `startplasma`; nessuna scelta AccountsService applicata da sddm. La voce A1 (scelta dell'utente in AccountsService) non è quindi «come in locale» su KDE: su KDE locale vale `plasma-localerc`/`LANG`; da decidere se REMOTIX vuole seguire AccountsService anche su KDE (decisione generale già presa).

---

## 8. Diff completo dei blocchi KDE fra i tre alberi (lo studio non li elenca tutti)

### 8.1 Debian ↔ Ubuntu (file in `kde-tmp/du-*.diff`)
- **`kwin.c` (249 righe di diff) e `kwin.h` (7):** `pixel_lock` + `kwin_poke()` (U5); sidecar ScreenSaver completo (U6); labwc proprio al posto di quello di distribuzione (U12, 14 righe). Lo studio li elenca.
- **`capture.c` (146) e `capture.h` (62):** tutto U5.
- **`kdehost.h`:** identico (0 righe).
- **`main.c` (83 righe):** `session_missing_component()` (U2) solo per XFCE/LXQt; due messaggi di testo. Niente di KDE tranne il ripiego del labwc.
- **`session.c` KDE:** (1) `session_kde_logout_watch` nuova (U7b); (2) `really_terminate()`: ramo «nessuna sessione viva» di Ubuntu/Fedora (`session.c` Ubuntu 5558-5573): se non c'è il nome sulla bus MA unità e processi sono tutti spenti la chiusura è «fatta» (ritorna `true`), altrimenti continua con la strada normale; Debian dice «there was no session to stop» e ritorna `false` (`session.c:4477-4479`): **fuori elenco, riguarda tutti e quattro i desktop** (U3); (3) `inactive_unit(const char **busy)` con messaggio del pezzo non fermo per KDE (`session.c` Ubuntu 4486-4496) e aggiunta di `graphical-session.target` alla guardia SOLO per GNOME 50; (4) `session_life()` a tre risposte (usa `name_owner_three("org.kde.KWin")`); (5) riconoscimento nomi di sessione `kubuntu`/`ubuntu` (inutile su Debian).
- **`child.c` KDE:** spostamento di `kwin_closed()` (U7a); `capture_watch_sequence` e blocco `kwin_poke` (U5); `session_kde_logout_watch()` bool + chiusura di forza (U7b); `session_over_early()` ESCLUDE esplicitamente KDE (`stage_kwin`) e `session_life()`: anche la «fine sessione» anticipata (U3) non cambia nulla per KDE; tre blocchi di U3 su `MSG_STAGE.fatal`/`scale_refused` sono GNOME (scala di mutter) e non toccano KDE.
- **`rootside.c`, `input.c`, `session.h`:** nessuna differenza KDE (solo la firma di `session_kde_logout_watch`).

### 8.2 Ubuntu ↔ Fedora (KDE)
- `kwin.c` (533 righe, quasi tutto AGGIUNTA): i tre messaggi B3; `kwin_virtual_alive()`; tutto il blocco `kwin_output_resize` (≈500 righe). Il codice labwc (`kwin_nested_alive`, `kwin_host_*`, `host_*`) è ancora tutto presente in Fedora ma irraggiungibile (`main.c`: `--kwin-nested` risponde «does not exist»).
- `kdehost.h` (69): segni `--kwin-virtual` + `REMOTIX_KDE_HOST=1`, cancellato `KDEHOST_MARK`.
- `main.c` (28): ramo `--kwin-virtual`; testi A9/B3; «weak dependency».
- `child.c` (370, parte KDE ~110): `kde_refused`, `kwin_output_resize` al posto di `kwin_host_settle`/`kwin_host_resize`; il resto è lingua/SELinux/PATH.
- `session.c` (186, parte KDE ~50): `KDE_PRELOCAL_ORDERLY_MS`, `wait_until_done_ms`, `exit_kde` su `SESSION_UNIT_GRAPHICAL`, ramo di `write_dropin` `--kwin-virtual`; il resto è dconf/SELinux e `LC_*` (A2).
- `capture.c`/`capture.h`: identici a Ubuntu.

---

## 9. Che cosa NON ho potuto verificare
- La strada labwc di distribuzione (labwc 0.8.3 non è installato nella VM e non si installa): tutti i tempi di §1 sono con KWin da solo dentro la sessione locale di Plasma, non dentro la strada del prodotto.
- Il comportamento di `requestLogoutPrompt()` senza proprietario di ScreenSaver (U6) e la numerazione `seq` di KWin 6.3.6 (U5): servono il prodotto installato.
- Il tempo delle forzate con programmi lenti a chiudersi e la «chiusura per abbandono» (non provata nemmeno su Fedora).
- Sorgenti di Plasma 6.3.6 non letti (solo binari: stringhe e proprietà d'unità).

Impronte: nella VM `kde` ho lasciato file di misura in `/tmp` (m*.sh) e `/tmp/dl/tzdata_*.deb`; nella home di `prova` le impostazioni create dai quattro accessi locali (come consentito: kwrite/Konsole usati, finestre di sessione salvate). Nessun pacchetto installato né rimosso.
