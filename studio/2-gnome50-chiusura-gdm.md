# Studio 2 — Fine della sessione GNOME 50 e convivenza con l'accesso locale (GDM) su Ubuntu 26.04

Agente di studio n. 2, 18 nov 2026. Solo studio: nessun codice del prodotto toccato, nessuna prova del prodotto.
Legenda: **[V]** verificato (dove), **[W]** dal web (dichiarato), **[S]** supposizione.
Percorsi: `D/` = `/home/nicfio/Documenti/REMOTIX-DEBIAN/`, `O/` = `/home/nicfio/Documenti/REMOTIX/` (vecchio albero),
`S/` = `/media/REMOTIX-UBUNTU/studio/2/` sul server (contenitore `studio-2`, immagine `ubuntu:26.04`, abilitato `deb-src`).

## 0. Riassunto per chi ha fretta

1. **La struttura della chiusura GNOME non è cambiata fra 48 e 50.** Logout D-Bus → fasi di `gnome-session-service` →
   `ExecStopPost=gnome-session-ctl --shutdown` → `gnome-session-shutdown.target` → `gnome-session-restart-dbus.service`.
   Le unità `gnome-session-shutdown.target`, `gnome-session-restart-dbus.service`, `gnome-session-monitor.service` sono **identiche byte per byte**
   fra gnome-session 48.0 e 50.1; `gnome-session-manager@.service` cambia solo il nome dell'eseguibile. Le due unità che il codice REMOTIX guarda
   (`gnome-session-manager@<sessione>.service`, `gnome-session-restart-dbus.service`) esistono in 50.1 [V]. **Il codice di chiusura di Debian dovrebbe
   funzionare com'è su Ubuntu 26.04**, salvo i punti 2-4.
2. **Cambia sotto, in systemd 259.9 (Debian 13 ha 257.13): la sessione logind è tenuta dal pidfd del leader, non più dal fifo `.ref`.**
   Il meccanismo `--session-fd` della correzione del 17 nov (`child.c:1700-1740`) non trova nulla da passare e stampa un avviso falso
   («the session will close at the exec»). La sessione resta viva lo stesso, perché il leader (stesso pid dopo l'`execve`) è vivo. Peso piccolo.
3. **GDM 50 tratta ancora chi ha già una sessione grafica, con lo stesso dialogo di gnome-shell 48** («Session Already Running»; codice del
   greeter identico [V]). **Novità reale in gdm 50.1:** il pulsante «Force Stop» ora interroga logind e fa `TerminateSession` su **tutte** le sessioni
   grafiche in stato active/online dell'utente, anche quelle non di GDM, quindi anche la sessione REMOTIX; in gdm 48 «Force Stop» non faceva nulla
   per una sessione estranea (`find_session_for_user()` conosce solo le proprie).
4. **Il dialogo del greeter compare DOPO `pam_open_session`**, cioè dopo il nostro gancio `pam_exec`: l'ordine «prima chiudo il remoto, poi il greeter
   guarda» regge anche su GDM 50. Il worker di GDM aspetta senza limite (`g_dbus_proxy_set_default_timeout(..., G_MAXINT)`), quindi i 25 s del gancio non
   sono tagliati da GDM [V].
5. **`pam-auth-update` su Ubuntu ordina come su Debian: la riga `pam_exec` finisce DOPO `pam_systemd`**, provato in un contenitore con i pacchetti PAM
   di un desktop Ubuntu (`pam_sss` 128, `pam_wtmpdb` 0, `pam_systemd` 0, `pam_lastlog2` 0, poi la nostra a -1) [V]. Il `pam-auth-update` di Ubuntu è
   identico a quello di Debian 13 salvo le liste di md5sum.
6. **Fatto fuori argomento ma da segnalare:** Ubuntu 26.04 ha **uutils coreutils (Rust)** al posto di GNU (`stat`, `readlink` sono link a
   `/usr/lib/cargo/bin/coreutils/...`) [V]. Gli script `postinst`, `prerm`, `remotix-polkit-seated`, le prove `prove/*` usano comandi coreutils: vanno riletti.

## 1. Come REMOTIX chiude oggi una sessione GNOME su Debian 13 (codice 1.0.0)

### 1.1 Le cinque cause di chiusura e chi le avvia
| Causa | Chi la decide | Come arriva al figlio | Chiusura |
|---|---|---|---|
| Log Out dell'utente dal menu del desktop | il desktop | il compositore sparisce | via «§7.6» (1.3) |
| TERMINATE_SESSION del client (`CHILDREN_INPUT_TERMINATE`, `ci.a` = causa) | il client | messaggio al figlio | `terminate_and_clear()` (1.2) |
| ABANDON (soffitto di tempo) | `main.c:1979-2041` | `CHILDREN_EXIT_ABANDON` | come sopra, o leggera se c'è sessione locale |
| STOP del servizio | `main.c:4308-4404`, `children_wait_closed()` fino a `STOP_CLOSE_WAIT_MS` (child.c:4375) | `CHILDREN_EXIT_STOP` | come sopra (§11.56) |
| «Un login locale sta arrivando» | `rootside.c` PL_*, `main.c:909-924` `local_coming_event()` | `CHILDREN_EXIT_PRELOCAL` | chiusura PIENA, guardia saltata (§11.57) |

La causa è scritta in `child.c:10919-10945` (sei righe di log diverse). Con sessione locale viva (o dubbio) tutte le cause tranne PRELOCAL
cadono sulla **chiusura leggera** `local_light_close()` (`child.c:9921`, cinque passi, mai Logout, mai stop di unità): guardia `local_guard()`
(`child.c:5581`, sentinella fail-closed, una seconda domanda dopo ~1 s se la risposta è «non so»).

### 1.2 `terminate_and_clear()` → `session_terminate()` → `really_terminate()`
- `child.c:9894` `terminate_and_clear()` = `session_terminate()` + `kdehost_stop()`.
- `session.c:4441` `session_terminate()`: se `really_terminate()` riesce, `session_clear_out_scope()` (SIGTERM a ciò che resta nello scope REMOTIX,
  2 s, poi SIGKILL; `session.c:4390`) e `session_clear_out_handler()` (R1/R2: toglie drop-in e variabili con il nostro marchio dallo user manager).
- `session.c:4474` `really_terminate()`, ramo GNOME (ultimo, `session.c:4549-4569`): `exit_gnome(1)` = `org.gnome.SessionManager.Logout(1)`
  (nessuna conferma; `session.c:3508`) poi `wait_until_done()` (10 s, `WAIT_EXIT_MS`; `session.c:3621`); se non basta, `exit_gnome(2)` (forzato) e altra attesa.
  `force_refused()` (`session.c:4454-4470`) salta i passi forzati se il genitore è sparito durante una chiusura PRELOCAL.
- `wait_until_done()` considera finita la sessione quando `!session_alive()` (GetCurrentState di Mutter senza risposta; `session.c:993`; usa prima
  `name_has_owner`, mai auto-start) **e** `inactive_unit()` (`session.c:3544`): `gnome-session-manager@<nome>.service` **e**
  `gnome-session-restart-dbus.service` inattivi (la seconda esiste perché a fine sessione GNOME riavvia il bus di sessione: «nacque su un bus che sta
  per essere sostituito»). `unit_stopped()` accetta `inactive`/`failed`/`unknown`.
- `<nome>` viene da `gnome_session()` (`session.c:859`): sulla Debian l'unico file `wayland-sessions/gnome.desktop`; su Ubuntu ci saranno `ubuntu` e
  `gnome` (vedi agente 3: non è qui).

### 1.3 Il Log Out fatto dall'utente dentro il desktop (strada «§7.6»)
1. Il compositore sparisce. Sul canale EIS (`input_dropped()`) il figlio guarda ogni secondo `session_alive()` (`child.c:11520-11560`, `EIS_GONE_LOOK_MS`).
2. Al rimontaggio dello stage `session_state()` dice DEAD mentre `vista_viva` è vero → **`child.c:8656-8700`**: log «the user logged out», `MSG_SESSION_FINISHED`
   al genitore (i client ricevono 0x10), `session_clear_out_scope()`, `session_dconf_neutralise()`, `session_clear_out_handler_due()`, e — **correzione del 17 nov**
   — **`raise(SIGTERM)` su se stesso**: `sigterm_serve()` (`child.c:9792`) vede `session_closed_by_user`, il figlio muore del segnale, **muore il leader della sessione logind,
   e logind chiude la sessione**. Prima lo faceva solo GNOME «per caso» (vedi 1.4); su KDE/XFCE/LXQt il figlio restava vivo e il login successivo era «RIPRESO».
3. Il rientro successivo nasce NUOVO.

### 1.4 SIGTERM «guarda, poi esci» (`child.c:9685-9890`)
`term_signal()` (`child.c:9754`) registra soltanto (due `sig_atomic_t`, un byte in pipe); `sigterm_serve()` decide:
- sessione finita (vista viva e ora non risponde; attesa fino a `SIGTERM_WAIT_MS` = 2 s; 0 s se il segnale viene dal genitore) → pulizia (dconf, user manager) e il figlio muore dello stesso segnale;
- sessione che risponde (rete caduta o figlio ucciso da fuori) → **non si tocca nulla**, il desktop resta per il riattacco (I4);
- mai vista viva / figlio close-only → niente;
- **SIGTERM che non viene dal genitore e la sessione era viva** (ramo «1.5.5», `child.c:9830-9860`): è logind che termina la sessione (`loginctl terminate-session`,
  oppure — su GDM 50.1 — «Force Stop» del greeter): `kdehost_stop()` (solo KDE) e poi lo stesso controllo.
- **Su GNOME il SIGTERM se lo manda il figlio da solo**: il thread «dconf worker» → `libdconfsettings` → `GDBusConnection` `exit-on-close` della connessione condivisa al bus di sessione →
  `raise(SIGTERM)`. È l'esito di `gnome-session-restart-dbus` (`StopUnit("dbus.service")`, `gnome-session-ctl.c:130-133`). Prova gdb su **Ubuntu 26.04 GNOME** del 14 nov nel
  vecchio albero (`child.c:9690-9712`, percorso del banco `/media/REMOTIX-16/misure/ubuntu-153/chi-manda-153/gpn-linger.gdb.txt`, ormai non più su questa macchina) [V da commento; non rivisto].
  Le connessioni nostre sono aperte con `sess_bus()` con exit-on-close spento (`session.c`, `session.h:496-512`).

### 1.5 «Nessun desktop orfano» (DECISIONS-11 §11.56) e «locale esclude remoto» periodico (rootside.c)
- Allo STOP del servizio: il lato rete chiede a ogni figlio la chiusura (`CHILDREN_EXIT_STOP`, leggera se c'è sessione locale), aspetta fino a 15 s; poi il lato root chiude ciò che
  resta in uno scope REMOTIX (`lx_stop_begin`, `rootside.c:2351`).
- Durante il servizio: una sessione logind seatless `SERVICE=remotix` con processi vivi e **nessun figlio nostro**, vista in due scansioni di fila, viene chiusa dal lato root (`lx_scan` `rootside.c:1901`,
  `lx_end_begin` `rootside.c:2066`: SIGTERM ai processi del `session-N.scope`, SIGKILL dopo `LX_TERM_MS`; poi `lx_clean_begin` pulisce lo user manager come l'utente).
- Il lato root legge `/run/systemd/sessions/<id>` (chiavi `UID`, `USER`, `SEAT`, `SERVICE`, `STATE`, `SCOPE`; `rootside.c:1830-1875`, `rediscover.c:638-651`, `render_grant.c:801-813`):
  **tutte presenti nel file di stato di logind 259** (`logind-session.c:360-399` [V]); il formato non è cambiato in modo che li rompa.
- Perché SIGTERM allo scope basta su GNOME: lo scope contiene solo il figlio e il leader `gnome-session` (init-worker); **il compositore e le app stanno nello user manager** (`org.gnome.Shell@.service` ha `Slice=session.slice`,
  [V] `S/x/gnome-shell-common/usr/lib/systemd/user/org.gnome.Shell@.service`). Il leader che riceve SIGTERM avvia `gnome-session-shutdown.target` (`leader-systemd.c`, `leader_term_or_int_signal_cb`); se muore a SIGKILL,
  il monitor vede HUP sul fifo e avvia comunque lo shutdown. Identico in gnome-session 48 (`deb13/gnome-session-48.0/gnome-session/main.c:284-291, 480-481` [W: sorgente scaricato da deb.debian.org]).

## 2. La regola «locale esclude remoto» (§11.57)

- `D/src/local_login.c` (132 righe): programma lanciato da `pam_exec` per ogni apertura di sessione; esce a 0 sempre. Filtri: `PAM_TYPE=open_session`, `PAM_USER` non vuoto, **`XDG_SEAT` non vuoto**,
  servizio ≠ `remotix`, **`XDG_SESSION_CLASS` vuota o `user`**, `XDG_SESSION_TYPE` vuota o wayland/x11/mir, uid ≠ 0. Se `/run/remotix/prelocal` (di root, 0700) esiste e il lato root tiene `flock` su `.lock`,
  lascia `/run/remotix/prelocal/<uid>` e aspetta (tetto 25 s) che il lato root lo tolga.
- Lato root: `rootside.c:2395-2760` (PL_GRACE_MS 13 s, PL_CEIL_MS 20 s, PL_HOLD_MS 10 s, PL_MAX 8); `main.c:909-924` `local_coming_event()`. Misurato su GNOME (tablet, 18 nov): chiusura piena 0,7 s (commento `rootside.c:2428`).
- Pacchetto: `D/debian/remotix.pam-config` (Priority **-1**, `Session-Interactive-Only: yes`, `Session-Type: Additional`, `optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login`),
  `postinst:22-31` (`pam-auth-update --package` + controllo `grep remotix-local-login`), `prerm:60-61` (`--remove remotix` solo su `remove`).
- Registro problemi: A1 (orfano dopo riavvio del servizio), A2 (SDDM/LightDM non trattengono), A3 (provare su tutti i desktop), C1 (agganciarsi a PAM col meccanismo della distro), D (comportamenti dei desktop;
  «la sessione logind deve restare attiva... e l'uscita deve chiuderla davvero»).

### 2.1 Fatti sulla variabili che il gancio legge (systemd 259.9, `src/login/pam_systemd.c`) [V]
- `update_environment()` (`:544`) mette in ambiente PAM `XDG_SESSION_ID`, `XDG_SESSION_TYPE`, **`XDG_SESSION_CLASS`**, `XDG_SESSION_DESKTOP`, `XDG_SESSION_EXTRA_DEVICE_ACCESS`, **`XDG_SEAT`**, `XDG_VTNR` (`:1306-1346`).
  `pam_exec` 1.7.0 passa al programma l'ambiente PAM più `PAM_TYPE` ecc. (`pam_exec.c:446-477`). Vale quindi ancora ciò che dice il commento di `local_login.c`.
- GDM mette per conto suo `XDG_SEAT` (se c'è un seat), `XDG_SESSION_TYPE=wayland` (sempre; `gdm-session.c:2893`), e **`XDG_SESSION_CLASS=greeter` per ogni sessione del servizio `gdm-launch-environment`**
  (greeter **e** gnome-initial-setup; `gdm-session-worker.c:1253-1255`). La sessione utente non ha classe in ambiente: la sceglie `pam_systemd` («user» per tipo grafico, `:985-990`), **prima** del nostro gancio. ⇒ il filtro regge.
- Classi nuove in logind 259: `user-light`, `user-early`, `user-early-light`, `user-incomplete` (`logind-session.c:1708-1711`). Per un utente regolare con sessione grafica resta `user`; la sentinella (`sentinel.c:352`) e il gancio accettano solo `user` ⇒ una
  sessione `user-incomplete` (XDG_SESSION_INCOMPLETE, usata da remote-desktop di sistema) non conterebbe come locale [S: non risulta usata da GDM].
- Una sessione senza seat è sempre `active` (`session_is_active()`, `logind-session.c:1113-1120`) ⇒ la sessione REMOTIX è «active» e il greeter la vede come conflitto finché non è «closing» (1.5 e 4.2).

## 3. Ubuntu 26.04 vero

### 3.1 Versioni (da `apt-cache policy`, contenitore `studio-2`, 18 nov 2026; suite `resolute`, `resolute-updates`, `resolute-security`) [V]
| Pacchetto | Ubuntu 26.04 | Debian 13 |
|---|---|---|
| gdm3 | 50.1-0ubuntu0.1 (50.0-0ubuntu1 alla uscita, dal changelog) | 48.0-2 [W] |
| gnome-session (e -bin, -common) | 50.1-0ubuntu0.1 | 48.0 [W, orig.tar.xz] |
| ubuntu-session | 50.1-0ubuntu0.1 | — |
| gnome-shell | 50.1-0ubuntu1.5 | 48.7 [commento D/docs/PULIZIA-tranche1.md; W] |
| mutter | 50.1-0ubuntu2.5 | 48.x |
| systemd / libpam-systemd | **259.9-0ubuntu0.1** (`KillUserProcesses=no`, `debian/rules:77`) | 257.13-1~deb13u1 [W] |
| libpam-runtime / libpam-modules | 1.7.0-5ubuntu3.2 | 1.7.0-5 [W] |
| dbus-daemon | 1.16.2-2ubuntu4 (`dbus-broker` è in universe, opzionale) | dbus-daemon |
| localsearch | 3.11.0-1ubuntu1.1 | — |
| coreutils | **uutils (Rust) 0.10.0** | GNU |
| gnome-remote-desktop | 50.2-0ubuntu0.1 | — |

### 3.2 I file PAM di gdm3 50.1 (`S/x/gdm3/etc/pam.d/`) [V]
`gdm-password`, `gdm-autologin`, `gdm-fingerprint`, `gdm-launch-environment`, `gdm-smartcard-pkcs11-exclusive`, `gdm-smartcard-sssd-exclusive`, `gdm-smartcard-sssd-or-password`:
**tutti hanno `@include common-session`** (nell'ordine: `pam_selinux close`, `pam_loginuid`, `pam_selinux open`, `pam_keyinit`, `pam_limits`, `pam_env` ×2, poi `common-session`, poi `pam_gnome_keyring auto_start`).
`gdm-launch-environment` è l'unico senza selinux/loginuid. Ne segue che il nostro gancio in `common-session` scatta per ogni modo di entrare (password, autologin, impronta, smartcard, e anche greeter, che il filtro scarta).
I file di GDM stanno in `/etc/pam.d` (conffile di gdm3) e non sono toccati da `pam-auth-update`. `gdm.service` non ha sandbox (`ProtectSystem`, `PrivateTmp`…): il gancio può leggere `/run/remotix` [V `data/gdm.service.in`].

### 3.3 `common-session` e dove sta `pam_systemd` [V]
Generato da `pam-auth-update` (template in `libpam-runtime`, `usr/share/pam/common-session`): blocco «Primary» (`[default=1] pam_permit`), `pam_deny`, `pam_permit`, **`pam_umask`**, blocco «Additional».
`pam_systemd.so` arriva dal profilo `/usr/share/pam-configs/systemd` di `libpam-systemd` (`Priority: 0`, `Session-Interactive-Only: yes`, Additional) — **identico a quello di Debian 13** (257.13) [V+W].
Priorità degli altri profili `pam-configs` di Ubuntu (da `apt-file` + estrazione): `unix` 256; `sss` 128; `adsys` 120; `libpam-mount` 128; `authd` 1050; `pwquality` 1024 (password); tutti gli altri di sessione **0**: `systemd`, `lastlog2`, `wtmpdb`, `gnome-keyring`, `tmpdir`, `ecryptfs-utils`, `capability`, `malcontent`, `mkhomedir`. **Nessun profilo ha priorità negativa.**
Regola di ordinamento (`pam-auth-update:129`): priorità decrescente, a parità **nome in ordine inverso** (`$b cmp $a`).

### 3.4 Prova: il risultato vero (contenitore, pacchetti da desktop Ubuntu: `libpam-systemd libpam-gnome-keyring libpam-lastlog2 libpam-wtmpdb libpam-sss libpam-fprintd`, poi il file `remotix.pam-config` copiato in `/usr/share/pam-configs/remotix`)
```
session [default=1] pam_permit.so
session requisite   pam_deny.so
session required    pam_permit.so
session optional    pam_umask.so
session required    pam_unix.so
session optional    pam_sss.so
session optional    pam_wtmpdb.so
session optional    pam_systemd.so
session optional    pam_lastlog2.so
session optional    pam_exec.so quiet /usr/libexec/remotix/remotix-local-login     <- nostra, ultima
```
`common-session-noninteractive` NON la contiene (Session-Interactive-Only). Dopo `pam-auth-update --package --remove remotix` la riga sparisce (`grep -c pam_exec` = 0). `pam_exec` fa parte di `libpam-modules` 1.7.0. `/usr/lib/pam.d` contiene `polkit-1` e `systemd-user` (come su Debian).
Nota di metodo: ho copiato nel contenitore solo il file di profilo per vedere l'ordine; non ho avviato nulla di REMOTIX.

### 3.5 `pam-auth-update` Debian 13 contro Ubuntu 26.04 [V, confronto file con `libpam-runtime_1.7.0-5_all.deb` scaricato da deb.debian.org]
Script `pam-auth-update`: **identico salvo la lista degli md5sum** (Ubuntu ne ha una in più, per i `common-*` delle sue vecchie versioni). Profilo `unix` identico. Template `common-session{,-noninteractive}`: cambia solo un commento (`# reset the umask…` / `pam_umask`). Le patch Ubuntu di `pam` (`debian/patches/series`) non toccano `pam-auth-update`. ⇒ il comportamento del nostro `postinst`/`prerm` è lo stesso.

## 4. GDM 50 contro GDM 48

### 4.1 Che cosa dice il NEWS (`S/src/gdm3-50.1/NEWS`) [V]
- **49.beta:** utenti dinamici per il greeter (`gdm-greeter`, niente più utente `gdm`), sessioni di greeter gestite da systemd, niente dipendenza da dbus-daemon, gnome-session 49 richiesto.
- **49.rc/49.0:** X11 riabilitato di default; **50.alpha:** X11 rimosso del tutto (restano solo le sessioni X11 di altri desktop con X per utente); sessioni speciali (greeter, initial-setup) caricate da `.desktop`;
  nuovo `gnome-headless-session@<utente>.service` (sessione grafica senza testa per RDP); unione di registrazione display e sessione (poi in parte tolta in 50.beta); niente più utente `gdm`/`gdm3`.
- **50.0:** con systemd ≥260 le sessioni remote senza seat ottengono accesso alla GPU (`XDG_SESSION_EXTRA_DEVICE_ACCESS=render:accel`, impostata già da `gdm-session-worker.c:1247`; **systemd 259.9 di Ubuntu è < 260**, quindi sulla 26.04 la funzione non c'è) — interessa l'agente 1/GPU, non qui.
- **50.1:** «GDM non riusciva a terminare le sessioni grafiche in conflitto avviate fuori da GDM (ThinLinc, TigerVNC). Ora interroga logind e le termina tutte».
- Il NEWS **non cita** una «nuova gestione dei seat»: nessun cambiamento dichiarato; non ho visto nei sorgenti nulla che cambi come REMOTIX (sessione seatless) viene trattata, a parte i punti 4.2-4.3.
- Ubuntu aggiunge: `Depends libsystemd >= 259`, patch `start-after-cloudinit`, `prefer_ubuntu_session_fallback`, `dont_set_language_env`, `config_error_dialog`, `revert_override_LANG_with_accountservices` (nessuna riguarda sessioni in conflitto) [V `debian/patches/series`, `debian/changelog`].
  Il changelog 50~beta cita «Fix PAM Worker crash breaks further logins (LP: #2117248)» e «Fix GNOME login screen stops responding (LP: #2125720)»: **possibili parenti del «fermo» di GNOME 48**, non provato [S].

### 4.2 Che cosa fa il greeter quando l'utente ha già una sessione grafica [V, `gnome-shell-50.1/js/gdm/loginDialog.js` e `deb13/gnome-shell-48.7/js/gdm/loginDialog.js`]
`_onSessionOpened(client, serviceName, sessionId)` → `_findConflictingSession()`: `listSessions()` di logind; per ogni altra sessione dello **stesso utente** con `Type` ∈ {wayland, x11} e `State` ∈ {active, online} → dialogo
**«Session Already Running»** con «Cancel» / «Force Stop», 60 s di tempo (`_CONFLICTING_SESSION_DIALOG_TIMEOUT`), testo diverso se la sessione in conflitto è `Remote` («...a remote session is already running for %s...»).
**Le due funzioni sono identiche in 48.7 e 50.1** (confronto riga per riga). Una sessione «closing» non è conflitto (come dice §11.56).
Il dialogo parte dall'evento «session opened», cioè **dopo `pam_open_session`** ⇒ dopo il nostro gancio (ordine in `gdm-session-worker.c:2250-2290`: `pam_open_session` → `XDG_SESSION_ID` → poi il greeter).
Il worker è chiamato con `g_dbus_proxy_set_default_timeout(…, G_MAXINT)` (`gdm-session.c:1273`): nessun timeout di GDM sull'apertura.

### 4.3 «Force Stop»: la differenza 48 → 50.1 [V]
- gdm 48.0 (`deb13/gdm-48.0/daemon/gdm-manager.c`, `on_stop_conflicting_session`): cerca tra le **sessioni di GDM** (`find_session_for_user`), se non c'è scrive «Couldn't find session for user» e **non fa nulla**.
- gdm 50.1 (`daemon/gdm-manager.c:1884-1914`): `gdm_find_graphical_sessions_for_username()` (logind, `sd_uid_get_sessions(..., GDM_SYSTEMD_SESSION_REQUIRE_ONLINE)`, solo grafiche e `active|online`, `common/gdm-common.c:789`)
  e `gdm_terminate_session_by_id()` = `org.freedesktop.login1.Manager.TerminateSession` per ognuna tranne la nuova.
- Conseguenza per REMOTIX: se l'utente preme «Force Stop» con un desktop REMOTIX vivo, logind manda SIGTERM allo scope (figlio + leader gnome-session). Il leader avvia lo shutdown pulito; il figlio entra nel ramo «1.5.5» di `sigterm_serve()` (SIGTERM non del genitore, sessione viva).
  Prima (GDM 48) il pulsante era inutile e l'utente restava bloccato; ora la sessione REMOTIX si chiude «a modo di logind». **Da provare** che il ramo regga (nessuna rinascita, 0x10 ai client, dconf e user manager puliti).
- `gdm-display-factory.c:249-310` (percorso `CreateRemoteDisplay`/display utente headless di gnome-remote-desktop di sistema): termina **tutte** le sessioni grafiche dell'utente quando quel display viene distrutto. Non è la nostra strada; da sapere se un amministratore usa anche GRD in modalità sistema [S].

### 4.4 Il «fermo» di GNOME 48 e cosa diventa in 50
Sequenza Debian (§11.56): sessione REMOTIX «closing» senza figlio → nessun conflitto per il greeter → parte il desktop locale → `gnome-session` trova ancora attiva l'unità della sessione remota nello user manager → «Session manager already running!», exit 1 → GDM resta con un login che rifiuta ogni password finché non si riavvia.
- **gnome-session 48.0** (`main.c:640-690`): controlla `gnome-session-wayland@<sessione>.target` attivo → `g_warning` + `exit(1)`.
- **gnome-session 50.1** (`gnome-session/leader-systemd.c:307-312`): controlla **`graphical-session.target`** attivo (qualunque sessione grafica dell'utente, non solo GNOME: «Improved safety check that enforces only one active graphical session per user», NEWS 50.alpha) → **`g_error("A graphical session is already running!")`**, cioè abort (SIGTRAP) del leader.
- Che cosa fa GDM 50 dopo la morte rapida del desktop locale non è provato: nel codice (`gdm-local-display-factory.c:256-318`) un display finito riporta il greeter solo a certe condizioni sul seat attivo, e un display «failed» conta fino a 5 fallimenti. **[S]** Il «fermo» potrebbe ripresentarsi o no; la cura REMOTIX (chiudere prima, §11.56/§11.57) resta quella giusta in entrambi i casi.
- Caso residuo: servizio caduto con SIGKILL, desktop orfano in stato **active** (leader ancora vivo), login locale con il gancio che trova il lucchetto libero e passa: su GDM 50 compare il dialogo e «Force Stop» (4.3) risolve; su GDM 48 no. Un orfano già «closing» resta il caso cattivo (nessun dialogo, abort del leader).

## 5. gnome-session 50: come avviene il logout [V, `S/src/gnome-session-50.1`]

### 5.1 Struttura
- `gnome-session` (`leader-main.c`): rilancia se stesso con la **shell di login** dell'utente (`maybe_reexec_with_login_shell`, solo se `XDG_SESSION_TYPE=wayland` e classe ≠ greeter; opzione `--no-reexec`), esporta l'ambiente, poi fa `execl(gnome-session-init-worker, <nome>)`.
- `gnome-session-init-worker` (`leader-systemd.c`, ex `systemd_leader_run`) = **leader**: l'unico processo non gestito dallo user manager, resta nello scope della sessione logind. Controlla `graphical-session.target` (vedi 4.4), esegue `ResetFailed`, avvia `gnome-session@<nome>.target` (modo `fail`), apre il fifo `$XDG_RUNTIME_DIR/gnome-session-leader-fifo`.
  SIGTERM/SIGHUP/SIGINT → `StartUnit gnome-session-shutdown.target` (`replace-irreversibly`) + un byte sul fifo.
- `gnome-session-monitor.service` (`gnome-session-ctl --monitor`) tiene l'altro capo del fifo, `PartOf=gnome-session-pre.target`.
- `gnome-session-manager@<nome>.service` (`ExecStart=gnome-session-service`, `Type=notify`, `OnFailure=gnome-session-shutdown.target`, `ExecStopPost=gnome-session-ctl --shutdown`) ospita `org.gnome.SessionManager` sul bus.
- Il compositore è `org.gnome.Shell@<modo>.service` (template `org.gnome.Shell@.service` con `ExecStart=gnome-shell --mode=%i`, `Slice=session.slice`, `Restart=no`, `OnFailure=gnome-session-shutdown.target`, `AssertEnvironment=XDG_SESSION_TYPE=wayland`); la sessione `gnome` chiede `@user`, la sessione `ubuntu` chiede `@ubuntu`
  (`gnome-session@ubuntu.target.d/ubuntu.session.conf`: `Requires=org.gnome.Shell@ubuntu.service`) [V].

### 5.2 Il Logout
`org.gnome.SessionManager.Logout(u mode)` (0 normale, 1 senza conferma, 2 forzato; `gsm-manager-logout-mode.h`; API invariata, `gnome-session-quit --logout [--no-prompt|--force]` la chiama) → `gsm_manager_logout()`:
errore `NOT_IN_RUNNING` se la fase è < RUNNING («Logout interface is only available after the Running phase starts»: **identico in 48.0** `gsm-manager.c:2930`), errore `LOCKED_DOWN` se `disable-log-out` → fasi QUERY_END_SESSION (1 s di attesa clienti; in modo NORMAL/NO_CONFIRMATION se un'app ha un inibitore di logout
si apre il dialogo di fine sessione della shell) → END_SESSION → EXIT → `gsm_quit()` → il servizio esce → `ExecStopPost` → `gnome-session-ctl --shutdown` → **`gnome-session-shutdown.target`**: `Conflicts` con `graphical-session.target`, `gnome-session*.target`; `Wants/Before=gnome-session-restart-dbus.service` che fa `StopUnit("dbus.service")` (riavvio del bus di sessione).
Il leader, avvisato dal monitor (HUP sul fifo), aspetta che `graphical-session-pre.target` diventi inattivo ed esce; GDM (o, da noi, il figlio) vede uscire il leader.
**Differenze rispetto a 48.0:** eseguibile `gnome-session-binary` → `gnome-session-service` (+ `gnome-session-init-worker`); tolti `gnome-session-failed.target` e il «fail whale» (49), tolti i target `gnome-session-wayland@` e `-x11` (sostituiti da `gnome-session@.target` solo Wayland), tolto il gestore di servizi interno (49),
`gnome-session` non è più uno script (49). Nuovi (50): `CanReboot`, `CanSuspend`, `Suspend`, `CanShutdown` ridefinita, inibitore di sleep da `block` a `block-weak`. Patch Ubuntu su gnome-session: solo sessioni `ubuntu`, alias `RequestShutdown/RequestReboot`, `ignore_gsettings_region` (nessuna sul Logout).
Ubuntu in `10_ubuntu-settings.gschema.override` ha `always-show-log-out = true` (come il nostro dconf di sessione); nessun override di `disable-log-out`/`logout-prompt` [V].

### 5.3 Cosa resta vivo dopo il Log Out
- **Nello scope della sessione logind** dopo un Log Out completo restano: il figlio (leader logind) finché non gli si manda SIGTERM (vedi 1.3), e il leader `gnome-session-init-worker` finché `graphical-session-pre.target` non è inattivo. Il vecchio banco su **Ubuntu 26.04 GNOME** diceva «scope chiuso» per S5 (`O/assessment/gnome/ubuntu2604.md`). [V da documento; non rivisto sul campo]
- **Nello user manager** (non nello scope): servizi come `localsearch-3.service` (`After=gnome-session.target`, `Slice=background.slice`, **senza `PartOf=graphical-session.target`**) [V unit file], `localsearch-writeback-3`, `gcr-ssh-agent` (`WantedBy=graphical-session-pre.target`), i `app-*@autostart.service` generati da `systemd-xdg-autostart-generator`.
  Senza linger l'intero user manager muore con l'ultima sessione (dopo `UserStopDelaySec=10` s, `logind.conf.in:26`); **con linger o con una sessione locale resta**, e con lui `localsearch-3` & C. (comportamento normale della sessione locale, non un difetto nostro; il pulitore R1/R2 toglie solo le nostre variabili e drop-in).
  I «`localsearch-3` e un `agent`» visti nel vecchio banco erano su **XFCE** (nello scope, perché avviati dall'autostart XDG di XFCE; `O/assessment/xfce/ubuntu2604.md`, D-X8, R-SESS-053; `O/phases/19-nvidia.md:478`): su GNOME 50 non nascono nello scope.
- **Arch GNOME** (`O/assessment/gnome/arch.md`, `difformita.md` n. 14; vale anche Leap e Tumbleweed): dopo Log Out il figlio e la sessione logind restavano (`State=active Leader=<figlio>`, «⏳ without a stage and WAITING») perché lì non arrivava il SIGTERM da GIO. Sul solo Ubuntu/Debian/Fedora/Alma il figlio moriva «per caso».
  **Il 17 nov Debian ha sistemato per tutti** con `raise(SIGTERM)` (1.3): su Ubuntu è quindi coperto in due modi (GIO e raise); da riprovare con una prova esplicita.

## 6. systemd 259.9 di Ubuntu e logind [V, `S/src/systemd-259.9`]

- **Tracciamento della sessione per pidfd (da 258)** (`NEWS`, CHANGES WITH 258): «logind's session tracking, which used to be performed via a FIFO installed in the client, now uses PIDFDs. The file descriptor returned by CreateSession() … is therefore unused.
  Moreover, the exit of the session leader process will immediately cause the session to be stopped.» Codice: `pam_systemd.c:842-890` (`CreateSessionWithPIDFD` con `pidfd_open(getpid())`), `pam_systemd.c:1282-1295` (il fd è «dummy», si tiene solo se è ancora un fifo di un logind <258),
  `logind-session.c:97-129` (`session_dispatch_leader_pidfd` → `session_stop(false)` subito), `logind-session.c:676-679` (il vecchio fifo, se c'è, viene tolto).
  **Per REMOTIX:** (a) il figlio resta il leader (stesso pid dopo `execve`, il pidfd non cambia); (b) il «fifo `.ref`» non esiste più su Ubuntu: `child.c:1720-1736` non trova nulla e scrive «⚠ the logind session's fifo was not found: the session will close at the exec» **anche se non è vero**;
  (c) `--session-fd` non viene passato; (d) tutto ciò che nel codice o nei documenti dice «il figlio tiene il fifo» (`prerm`, `DECISIONS-11 §11.55`) va letto «il figlio è il leader». I file `.ref` che `rediscover.c:621`, `render_grant.c:774`, `rootside.c:1917` e `remotix-polkit-seated:24` saltano per nome non compaiono più (nessun danno).
- **Stati:** `session_get_state()` (`logind-session.c:1368-1383`): `closing` se `stopping` o timer di rilascio; `opening` se c'è un job di scope o manca il leader; `active` se `session_is_active` (senza seat sempre vero); altrimenti `online`.
  `session_stop_scope()` (`:960-1000`): abbandona sempre lo scope; **uccide ciò che resta solo se** `force` o `kill_processes`/`KillUserProcesses` — **in Ubuntu 26.04 `KillUserProcesses=no`** (`debian/rules:77`, `logind.conf.in:22`), come in Debian ⇒ una sessione senza leader resta `closing` finché lo scope ha processi: è lo scenario A1.
  `TerminateSession` (usata da GDM 50.1 e da `loginctl terminate-session`, `prerm`) = `session_stop(force=true)` → `StopUnit(scope, "replace")` (SIGTERM a tutto lo scope, 90 s di attesa poi SIGKILL).
- **Classi** (`NEWS` 258, `logind-session.c:1708`): `user-light`, `user-early`, `user-early-light`, `user-incomplete`, `background-light`, `manager`. Per utenti regolari e sessioni grafiche resta `user` (`pam_systemd.c:1027-1040`: la «classe automatica» cambia solo per utenti di sistema o con «area»). Le sessioni REMOTIX impostano `XDG_SESSION_CLASS=user` e type wayland (`child.c:1672-1680`, `pam_putenv`).
- **Tty «remotix»:** `pam_systemd.c:972-974` lo accetta (`skip_dev_prefix`), come in 257 [V]; da confermare con una vera apertura di sessione (agente 1).
- **File di stato** `/run/systemd/sessions/<id>`: chiavi usate da REMOTIX presenti (2.1/1.5). `LEADER_PIDFDID` e `LEADER_FD_SAVED` sono nuove e ignorate.
- **user@.service:** `UserStopDelaySec=10` (default), PAM `systemd-user` (`/usr/lib/pam.d`) usa `common-session-noninteractive` + `pam_systemd` ⇒ il nostro gancio **non** scatta per lo user manager (non è in quel blocco).
- Altro NEWS 258 che non ci riguarda: le sessioni di utenti di sistema senza TTY e senza grafica diventano `user-light`/`background-light` (non toccano utenti regolari né sessioni grafiche).

## 7. Decisioni e lezioni già scritte nel vecchio albero e in quello Debian sul tema

- `D/docs/DECISIONS-11.md` **§11.55** (`:2040-2057`): il limite «sessione logind tenuta viva con `--session-fd`, Log Out termina il figlio (strada §7.6) su ogni desktop; KDE con il suo guardiano»; «nessun percorso di aggiornamento».
- **§11.56** (`:2059-2082`): desktop chiusi allo stop del servizio, nessun desktop orfano; scartato: reagire a `SessionNew`, dare un figlio a ogni desktop ritrovato all'avvio, tenere «active» dopo l'uscita del figlio.
- **§11.57** (`:2084-2113`): il gancio PAM, FULL e non leggero, guardia saltata, «ALWAYS exits 0»; **«Non coperto»: servizio giù; la parte che le prove automatiche non esercitano** (`local_guard()` saltata, interazione con gli sweep) → provata solo con login vero (GNOME sul tablet; KDE, XFCE, LXQt dal proprietario su live Debian).
- `D/docs/REGISTRO-problemi.md` A1-A3, B1-B2 (nei contenitori il figlio non esce prima di ~25 s dall'audio: la prova aspetta 31 s), C1, D.
- `D/docs/PULIZIA-tranche1.md`, voce 6: **tolto il ramo GNOME 50 di `unit_shell()`** (template `org.gnome.Shell@.service`, istanze `@user`/`@ubuntu`, `--mode=%i`, guardia della cartella del template nel clear-out) e voce 7 (scoperta D-153 della sessione «come un login locale»);
  entrambi servono di nuovo qui, ma sono **avvio**, non chiusura (agenti 1 e 3). Per la chiusura conta solo che il clear-out cerca i drop-in `org.gnome.Shell@*.service.d` per prefisso (`D/src/session.c:3989-4010`, ancora presente) e salta la cartella del template.
- Vecchio albero: `O/src/session.c:4100-4160` (clear-out con istanze `@wayland/@user/@ubuntu`), `O/src/child.c:9690-9712` (la prova gdb su Ubuntu 26.04: SIGTERM da GIO), `O/CHANGES-1.5.md:304, 349` (pulizia anche quando il sistema chiude REMOTIX al Log Out; il «raro difetto» 1 su 53: profilo dconf legato all'utente per colpa del linger, ora tolto sempre),
  `O/assessment/gnome/ubuntu2604.md` (112 controlli: 100 verdi; S5 Logout/rientro NEW verde; rosso nuovo R-LOGIN-010/013 «oracolo utente» per `getpwnam_r`, **non di questo argomento**), `arch.md`, `difformita.md` n. 14, `fase3-gnome.md:30-32`.
- Principio del 15 nov (memoria): «un utente con sessione grafica locale attiva ⇒ remoto rifiutato, niente di vivo, tutti i DE/distro» (incidente 1.5.4).

## 8. Problemi da affrontare

| # | Che cosa | Dove nel codice | Peso | Cura nota nel vecchio albero? |
|---|---|---|---|---|
| 1 | Con systemd ≥258 non esiste più il fifo `.ref`: la ricerca di `--session-fd` fallisce e stampa un avviso falso; la correzione del 17 nov serve solo a Debian 13 (257). Rendere l'avviso condizionale (o spostarlo nel log come «pidfd, nessun fifo») e riscrivere i commenti/§11.55 («il leader è il figlio») | `D/src/child.c:1700-1740`, `:10093-10105`; `D/docs/DECISIONS-11.md:2055`; `D/debian/remotix.prerm:9-12` (commento) | piccolo | no: il vecchio albero non aveva il fifo e andava (verde sul banco Ubuntu) |
| 2 | **Il gancio PAM su GDM 50:** ordine «gancio → dialogo del greeter» da confermare con un login vero; misurare il tempo di chiusura piena su Ubuntu 26.04 GNOME; verificare che al ritorno del gancio `graphical-session.target` sia già inattivo (altrimenti il leader del desktop locale abortisce con «A graphical session is already running!»), soprattutto nel percorso forzato del lato root (SIGTERM allo scope, shutdown asincrono) | `D/src/rootside.c:2395-2760`, `D/src/local_login.c`, `D/src/child.c:10957-10968` | medio (prova su live, nessun codice previsto) | no (il gancio nasce il 18 nov) |
| 3 | **«Force Stop» di GDM 50.1** termina la sessione REMOTIX con `TerminateSession`: provare che il ramo «1.5.5» di `sigterm_serve()` e la pulizia (dconf, user manager, 0x10 ai client, nessuna rinascita) reggano su GNOME 50; aggiornare le descrizioni del comportamento (manuali, §11.57) | `D/src/child.c:9792-9890` | piccolo-medio (prova) | no |
| 4 | **Guardia di nascita dopo il logout:** `inactive_unit()` guarda `gnome-session-manager@<nome>.service` e `restart-dbus`. In 50 il leader abortisce se `graphical-session.target` è attivo. Per l'ordine delle unità (shutdown target `Before=` restart-dbus) il guard attuale dovrebbe bastare; misurare un rientro immediato (<1 s) dopo il Log Out su Ubuntu; se serve, aggiungere `graphical-session.target` | `D/src/session.c:3544-3619` | piccolo (misura) | no (S5 verde sul banco, ma senza rientri a ~0 s) |
| 5 | **Assenza di prove su GDM+greeter reale in contenitore:** le prove automatiche (`prove/check-prelocal.py`) chiamano il gancio a mano; GDM 50, il dialogo e il leader che abortisce si vedono solo su live Ubuntu 26.04 vera (passo 5 del piano). Preparare la live (pacchetto, script, istruzioni, salvataggio del registro) | `D/prove/check-prelocal.py`, `D/boxes/` | medio | no |
| 6 | **Test «chi resta vivo dopo il Log Out» su GNOME 50:** vecchio banco verde per Ubuntu; ricostruire con la nuova strada (`raise(SIGTERM)`) e con linger acceso; cercare processi `localsearch-3`, `gcr-ssh-agent`, `app-*@autostart` nello user manager e decidere se è «nostro» (finché c'è una sessione locale non si toccano) | `D/src/session.c:4390-4470` (clear-out), `prove/check-lifecycle.py` | piccolo-medio | sì per lo scope (R-SESS-053 su XFCE, `O/phases/19-nvidia.md:478`), no per lo user manager |
| 7 | **Ubuntu 26.04 ha uutils coreutils (Rust):** riguardare gli script che chiudono sessioni e quelli del pacchetto (`prerm`, `postinst`, `remotix-polkit-seated`, `prove/*`) per opzioni GNU (`stat -c`, `readlink -f`, `date -d`, `sort -V`…) e `awk` (Ubuntu usa `mawk`?) | `D/debian/remotix.prerm`, `remotix.postinst`, `D/src/remotix-polkit-seated`, `D/prove/*.sh` | piccolo-medio | no |
| 8 | **Dopo il Log Out con linger o sessione locale** lo user manager resta con i servizi dell'utente (normale) ma il pulitore R1/R2 deve togliere le nostre variabili anche quando manca il SIGTERM (su 26.04 arriva da GIO e da `raise`); verificare con linger acceso (`loginctl enable-linger`) che `DCONF_PROFILE` e le altre variabili tornino come prima | `D/src/session.c:3841-3861`, `child.c:9894` | piccolo | sì (1.5.3, `O/CHANGES-1.5.md:349`) |
| 9 | **gnome-initial-setup / autologin:** il gancio scatta anche per `gnome-initial-setup` e l'autologin; con il filtro per classe `greeter`/`user` e il lucchetto del servizio non dovrebbe far danni; verificare sul primo avvio e con autologin attivo che non si aspetti mai | `D/src/local_login.c:96-117` | piccolo | no |
| 10 | **`gdm-display-factory` / gnome-remote-desktop di sistema** può terminare sessioni grafiche dell'utente (percorso RDP headless): non è la nostra strada, ma va scritto nei manuali come incompatibilità di fatto se GRD è in modalità sistema | manuali | piccolo | no |
| 11 | **Mutter 50 e `GetCurrentState`/`session_alive()`:** verificare che non sia diventato attivabile; nei pacchetti Ubuntu `mutter-common` e `gnome-shell` non c'è un servizio D-Bus per `org.gnome.Mutter.DisplayConfig` né per `org.gnome.Shell` [V `S/x/*/usr/share/dbus-1/services`], quindi `name_has_owner` + chiamata senza auto-start resta valido | `D/src/session.c:251-276, 993-1040` | piccolo (conferma) | n/a |

## 9. Che cosa non si può sapere senza provare

1. Se, con GDM 50.1 e gnome-session 50.1 reali, il login locale con un desktop REMOTIX «closing» orfano si blocca come in 48 («login che rifiuta ogni password») o si riprende; il comportamento dopo l'abort del leader (`g_error`) e le correzioni upstream di GDM («PAM worker crash», «login screen stops responding») non sono verificabili dai sorgenti.
2. Il tempo reale (a) del gancio PAM con chiusura piena su Ubuntu 26.04 GNOME (Debian: 0,7 s), (b) fra «gancio tornato» e `graphical-session.target` inattivo nel percorso forzato.
3. Se il dialogo «Session Already Running» si vede davvero (e per quanto) quando il gancio non c'è o scade (servizio fermo, orfano «active»), e se «Force Stop» chiude la sessione REMOTIX in modo pulito.
4. Se `pam_open_session` di REMOTIX (tty «remotix», classe user, tipo wayland, senza seat, PAM_RHOST) funziona con `CreateSessionWithPIDFD` di systemd 259 senza avvisi nuovi nel journal (letto nei sorgenti: sì; non provato).
5. Se su Ubuntu l'estensione «ubuntu-dock» o altre app impongono inibitori di logout tali da far passare `Logout(1)` al ramo forzato (`Logout(2)` dopo 10 s): impatto sul tempo di chiusura.
6. Comportamento di `localsearch-3` e dei servizi `app-*@autostart` con linger acceso, e se qualche processo della sessione REMOTIX finisce nello scope (la shell di login rilanciata da `gnome-session` esegue `~/.profile`: un utente che avvia demoni lì li lascerebbe nello scope).
7. Se gdm 50 + dbus-daemon producono ancora il `raise(SIGTERM)` da GIO (la prova gdb è su Ubuntu 26.04 con le versioni di ottobre-novembre; gnome-session non è cambiata, ma l'ha verificato solo un gdb).

## 10. Prove consigliate (decide il proprietario: nessuna è stata lanciata)

1. **Live Ubuntu 26.04 (desktop GNOME) con REMOTIX installato**, in sequenza: (a) desktop remoto aperto → login locale con GDM (password) → il login deve riuscire al primo tentativo; registro: gancio, 0x04 al client, tempo della chiusura piena, nessun dialogo. (b) stessa cosa con autologin. (c) servizio fermo con desktop remoto (processi uccisi a mano) → login locale: osservare il dialogo «Session Already Running», premere «Force Stop», vedere la fine pulita della sessione REMOTIX.
2. **Orfano «closing»**: ricreare A1 su GNOME 50 (riavvio del servizio senza §11.56, oppure uccisione del figlio) e vedere se GDM 50 «si blocca»; è per sapere quanto vale la difesa e per dirlo nel registro.
3. **Misura di rientro dopo Log Out:** Log Out dal menu, rientro dopo 0,3 / 1 / 3 / 10 s, con e senza linger; registro: `SESSION: state=1` e nessun «A graphical session is already running».
4. **Log Out con linger acceso**: processi rimasti, variabili dello user manager, drop-in, profilo dconf, 0x10; confronto con senza linger.
5. **TerminateSession dall'esterno** (`loginctl terminate-session`) e dal «Force Stop»: 0x10, nessuna rinascita, pulizia.
6. **Journal** di una nascita su Ubuntu 26.04: nessun avviso di `pam_systemd` / logind su `tty=remotix`; verifica che `session.state` mostri `LEADER_PIDFDID`.
7. **Controllo grep** delle sorgenti di script e prove per opzioni GNU incompatibili con uutils (problema 7), anche solo con `shellcheck`/esecuzione di `postinst` e `prerm` in un contenitore Ubuntu usa-e-getta (senza avviare il servizio).

## Appendice: che cosa ho fatto, dove sta, che cosa ho tolto

- Contenitore `studio-2` (podman, `ubuntu:26.04`) con `deb-src` abilitato; pacchetti installati solo per leggerne i file (`libpam-systemd libpam-gnome-keyring libpam-lastlog2 libpam-wtmpdb libpam-sss libpam-fprintd`, `dpkg-dev`, `apt-file`, `curl`); copiato nel contenitore (solo per la prova di ordinamento) il file di profilo `remotix.pam-config`; scaricato (ripiego **[W]**, dichiarato) da `deb.debian.org` i sorgenti `gdm3 48.0`, `gnome-shell 48.7`, `gnome-session 48.0` e i `.deb` `libpam-runtime 1.7.0-5`, `libpam-systemd 257.13-1~deb13u1`.
- Cartella lasciata: `/media/REMOTIX-UBUNTU/studio/2/` (`x/` pacchetti estratti, `src/` sorgenti Ubuntu: gdm3, gnome-session, gnome-shell, pam, systemd; `deb13/` sorgenti Debian; `debs/`; `s*.out`). Nulla di REMOTIX avviato, nessun sudo, `/media/REMOTIX-DEBIAN` non toccato.
