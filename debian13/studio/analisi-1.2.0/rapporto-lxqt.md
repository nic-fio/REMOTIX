# Rapporto LXQt (+ voci generali A5, U2, U3, U9, quadro dei file, prove/) — REMOTIX 1.2.0 per Debian 13

Autore: agente di analisi `lxqt`. Solo lettura e misure sulla VM `lxqt` (accesa `virtuale`, spenta alla fine; nessun posto-turno preso).
Legenda: [V] verificato sul codice o sulla VM, [D] dedotto.

## 0. Scoperte più importanti (fuori elenco)

1. **`debian13/src` non è «Ubuntu vecchio»: è Ubuntu POTATO.** `docs/PULIZIA-tranche1.md` (17 nov) ha tolto da Debian 12 gruppi di codice
   morto su trixie (SELinux/dlopen, nomi Ubuntu, ramo GNOME 50, scoperta cartelle di sessione, `REMOTIX_LABWC`, `REMOTIX_EI_PING`, ecc.).
   Prendere un file di Ubuntu o di Fedora per intero RIPORTA quel codice e rompe cose di Debian (vedi §6 «da preservare»).
2. **`child.c` di Debian ha il «filo di vita» della sessione logind (`--session-fd`, fifo `/run/systemd/sessions/<id>.ref`)** (`child.c`: 10 occorrenze;
   Ubuntu e Fedora 0). Ubuntu/Fedora hanno systemd ≥ 259 (logind segue il pidfd del capo-sessione, dal v258); Debian 13 ha systemd 257.13 [V: `systemctl --version`
   nella VM] e il fifo serve ancora. **Se `child.c` di Ubuntu/Fedora entrasse in Debian, la sessione logind si chiuderebbe 0,1 s dopo l'accesso** (è proprio il guasto
   misurato il 17 nov). Rischio numero uno dell'allineamento.
3. **Sessione LXQt locale di Debian = X11 + xfwm4, non Wayland, non labwc** [V]. `/usr/share/xsessions/lxqt.desktop` (`Exec=startlxqt`), nessun
   `/usr/share/wayland-sessions`, `lxqt-wayland-session` non esiste nel repository (`apt-cache policy`: nessun candidato). Nella sessione locale `XDG_SESSION_TYPE=x11`,
   `DISPLAY=:0`, WM `xfwm4` (con compositing), Xorg avviato da sddm. Il WM viene da `~/.config/lxqt/session.conf` (`window_manager=xfwm4`), perché il metapacchetto `lxqt`
   dipende da `xfwm4` [V `apt-cache depends lxqt`: `Depends: xfwm4`]; `lxqt-core` non dipende da nessun WM. REMOTIX invece crea un LXQt Wayland dentro `labwc` (`labwc -C … -S lxqt-session`).
   Conseguenza buona: il `kill_xfce()` (SIGTERM a ogni processo `labwc` dell'utente) nella chiusura forzata non può colpire il desktop locale, che su Debian non ha labwc.
4. Gli strumenti di prova di Fedora per l'accesso locale su LXQt (`banco-vm/autologin-sddm.sh`) sono **scritti per `Session=lxqt-wayland` e `hostname = rx-lxqt`**:
   su Debian servono `Session=lxqt` (X11) e `rx-deb-lxqt`; e in P7 `COMPOSITOR["lxqt"] = ("labwc",)` va in `("xfwm4","labwc")` come già fa `xfce`.
5. `coredumpctl` e `ausearch` **non esistono** nella VM Debian [V]. In P7/P8 di Fedora la riga dei core dump è `coredumpctl … | grep -vi 'no coredumps'; true`: con il comando mancante
   uscirebbe «command not found» e verrebbe letto come «core dump trovato» (falso FAIL). Va protetta (`command -v coredumpctl`). `ausearch` mancante invece non dà falsi allarmi (il `grep type=AVC` resta vuoto).
6. `prove/check-desktop.py` di Fedora per LXQt usa `ls /usr/share/lxqt/panel.conf /etc/xdg/lxqt/panel.conf | head -1`; `ls` ordina e prende **`/etc/xdg/lxqt/panel.conf`** (file di
   `lxqt-branding-debian`, [V] diverso da quello di `lxqt-panel`: ha `[General] iconTheme=Papirus-Dark`, `[mainmenu]`, niente `panels=panel1`). Su Debian va tenuta la riga di Debian
   (`/usr/share/lxqt/panel.conf`) o scelta con attenzione.
7. U9 ha un effetto reale su Debian: nella VM `CanHibernate = "na"` (anche `CanSuspendThenHibernate`, `CanHybridSleep`) [V `busctl`]. Con la regola polkit del pacchetto
   `CanPowerOff/Reboot/Suspend` diventano `no`, ma `CanHibernate` resta `na` su macchine senza swap/resume: il codice di Debian (`sentinel.c:896-905`) lo conta come «non sicuro» e dà l'allarme
   (da provare col prodotto; [D]).

## 1. LXQt — U8 (autostart, compositor), E1 (chiusura per accesso locale), `common-session`

### 1.1 Autostart reali di Debian LXQt [V, VM `lxqt`]
`/etc/xdg/autostart` (22 file, tutti da pacchetti Debian). Sessione locale vera (accesso grafico di `prova` da sddm): processi vivi dopo il login: `lxqt-session`, `xfwm4`, `pcmanfm-qt --desktop`,
`lxqt-globalkeysd`, `lxqt-notificationd`, `lxqt-panel`, `lxqt-policykit-agent`, `lxqt-runner`, `xscreensaver`, `system-config-printer applet`, `lxqt-powermanagement`, `qlipper`, `nm-tray`,
`geoclue demo agent`, `at-spi`, `ibus-*`, `xdg-desktop-portal-lxqt`, `pulseaudio`, `gnome-keyring-daemon`.

| Entry | Pacchetto | Chiave | Su remoto (Wayland, labwc) |
|---|---|---|---|
| lxqt-globalkeyshortcuts, lxqt-xscreensaver | lxqt-globalkeys, lxqt-session | `X-LXQt-X11-Only=true` | saltati da lxqt-session (marcati) |
| lxqt-powermanagement | lxqt-powermanagement | `X-LXQt-Module` | già gestito da REMOTIX (script `lxqt-powermanagement` nel PATH di sessione) |
| nm-tray | nm-tray | `NotShowIn=KDE;GNOME` | **parte** (icona di rete NetworkManager nella sessione remota): da provare |
| print-applet | system-config-printer | `NotShowIn=KDE;GNOME;Cinnamon;LXDE;Unity` | **parte**: da provare |
| lxqt-qlipper | qlipper | `OnlyShowIn=LXQt` | parte (clipboard manager: da provare con la clipboard di REMOTIX; il commento di `session.c:2613` già lo segnala «[?]») |
| spice-vdagent | spice-vdagent | nessuna | solo VM |
| pulseaudio (`start-pulseaudio-x11`), im-launch, at-spi, geoclue-demo-agent, xdg-user-dirs(-kde) | vari | nessuna | partono; da provare |

Non ci sono `picom`, `compton`, `xcompmgr`, `lubuntu-update`, `blueman` in Debian LXQt [V `dpkg -l` e elenco autostart]. La composizione X11 in locale la fa `xfwm4` (non è un autostart).

### 1.2 U8 per la parte LXQt — che cosa è di Lubuntu e che cosa è generale
Nel diff `session.c` Debian↔Ubuntu le parti LXQt di Ubuntu sono (righe del diff, tutte in `ubuntu26.04/src/session.c`):
- `LXQT_X11_COMPOSITORS` {picom, compton, xcompmgr} + script-sostituto nel PATH di sessione (picom di Lubuntu è un modulo senza `X-LXQt-X11-Only`, `lxqt-session` lo rilancia 5 volte: «X Compositor crashed too many times»).
  **Di Lubuntu nel sintomo, generale nel meccanismo** (qualsiasi compositore X11 installato dall'utente, anche su Debian: `apt install picom`). Se il programma non è installato il codice non scrive nulla ed elimina i residui.
- `LXQT_SHARED_SERVER_PROGRAMS` = {`lubuntu-update` / `lubuntu-update-autostart.desktop`}: **solo Lubuntu** (programma e voce non esistono su Debian). Il meccanismo (script + voce di autostart di copertura) è generico ma con un solo elemento, di Lubuntu: su Debian sarebbe codice morto.
- `SESSION_NOT_IN_REMOTE_AUTOSTART` = {`blueman.desktop`} + `session_autostart_cover()` (XFCE e LXQt): **generale** (blueman-applet su Debian non è installato di serie in nessuno dei due; se l'amministratore lo installa si applica). Dipende da `system_autostart_exists()` e da `session_config_dirs_strv()` (cartelle di config della sessione: in Debian `local_session()` è stata semplificata, vedi sotto).
- `desktop_of_session_name()`: `lubuntu`/`xubuntu`/`kubuntu`/`ubuntu` — **specifico Ubuntu, tolto apposta da Debian** (PULIZIA voce 4): NON portare.
- `local_session_name_find()`, `local_login_adds_folders()`, `login_session_desktop()` (`xdg-Lubuntu`, `/usr/share/<nome>`): **specifico Ubuntu** (`x11-common` di Ubuntu ha `60x11-common_xdg_path`, quello di Debian no; PULIZIA voce 7): NON portare.
- messaggi finali di `lxqt_session_commands()`: solo testo che conta compositori/programmi condivisi.

**Verdetto U8-LXQt: NON SERVE su Debian 13 come installato (nessuno dei programmi c'è); PORTABILE CON ADATTAMENTO se si vuole la protezione generale** (compositori X11 + blueman): ~100 righe, da `ubuntu26.04/src/session.c`
(`lxqt_session_commands`, `LXQT_X11_COMPOSITORS`, `session_autostart_cover`, `system_autostart_exists`) senza `LXQT_SHARED_SERVER_PROGRAMS`/`lubuntu-update`. Dipende da: nulla (se si toglie `lubuntu-update`). Da decidere (cambio per il proprietario: nessun cambio visibile oggi su Debian).
Resta da provare col prodotto: che `nm-tray`, `print-applet`, `qlipper`, `pulseaudio` nella sessione remota non diano finestre/errori (nessun precedente nel registro Debian: `grep` in `src` e `docs/REGISTRO-problemi.md` non trova nulla).

### 1.3 Compositor di LXQt: locale e remoto, nei tre alberi [V]
- **Locale Debian**: X11, `xfwm4` 4.20 (§0.3). **Locale Ubuntu/Fedora**: sessione Wayland con il loro labwc (Fedora: `Session=lxqt-wayland` negli script di prova). 
- **REMOTIX, nei tre alberi** (stesso codice per LXQt: `session.c`, `exec labwc -C '<cartella>' -S lxqt-session`, `SESSION_PROCESS_XFCE "labwc"`, `write_config_labwc_lxqt()`, `session.h:190-227`): il comando `labwc` si cerca per **nome nel PATH** in tutti e tre
  (Debian `session.c:3464`, Ubuntu e Fedora idem). **Il labwc nostro 0.9.3 di Ubuntu (`/usr/libexec/remotix/labwc`, `REMOTIX_LABWC`) serve solo a KDE (KWin ospite), non a LXQt/XFCE.** Quindi su Ubuntu LXQt usa il labwc di Ubuntu; su Fedora quello di Fedora.
- **labwc 0.8.3 di Debian basta per LXQt?** Sì per quanto risulta: tutto il codice LXQt/XFCE è nato e misurato su labwc 0.8.3 di trixie (commenti `session.h:208-266`: «labwc 0.8.3 `src/common/dir.c`», «0.8.3 non annida If/ForEach», `wlr_input.h:62`, `input.c:2855`, `shape.c:133`; `DECISIONS.md:6922` confronta 0.8.3 e 0.9.8). `apt-cache`: labwc 0.8.3-1, dipende da wlroots 0.18 e da `xwayland` [V]. Non provato in questa analisi (niente prodotto): DA PROVARE nel giro.
- **LXQt su Wayland in trixie**: `lxqt-session` 2.1.1 dipende da `liblayershellqtinterface6` [V `apt-cache depends`], `lxqt-wayland-session` non esiste: REMOTIX scrive il lanciatore (`session.h:194-213`); coerente.

### 1.4 Chiusura LXQt per accesso locale (E1 estesa a LXQt)
Com'è fatta oggi, uguale nei tre alberi (Ubuntu e Fedora non hanno blocchi LXQt diversi: `diff` Ubuntu↔Fedora di `session.c` ha **0** righe con «lxqt») [V]:
- Lato root: `local_login.c` (aggancio PAM) + `rootside.c` «PL» (cartella `/run/remotix/prelocal`, tetto 20 s; `local_login.c` aspetta fino a 25 s). `local_login.c` e `rootside.c` identici fra Debian e Ubuntu (diff 0 / 2 righe) e uguali a Fedora [V].
- Lato figlio (`session.c:4504-4529`, `really_terminate()` ramo `e_lxqt()`): chiusura gentile `org.lxqt.session.logout()` (D-Bus `NO_REPLY_EXPECTED`, `Q_NOREPLY`), `wait_until_done()` = 10 s (`WAIT_EXIT_MS`); se non basta, **forzata** = SIGTERM a tutti i `labwc` dell'utente (`kill_xfce()`, 3708) e altri 10 s; `force_refused()` salta la forzata se il padre è sparito (`force_guard_on`, 4455).
- Differenze con KDE di Fedora (A6/A7): niente `graphical-session.target`, niente 5 s (`KDE_PRELOCAL_ORDERLY_MS`): LXQt resta a 10 s + forzata SIGTERM a labwc. Nessuna «ultima difesa» lato root (E1): vale per LXQt come per XFCE e GNOME.
- Come aggiunge **sddm** `common-session` [V `/etc/pam.d/sddm`, `sddm-greeter`, `sddm-autologin` nella VM]: tutti e tre hanno `@include common-session` (sddm e sddm-autologin anche `pam_selinux close/open`, innocue). `common-session` (gestito da `pam-auth-update`) ha `pam_umask`, `pam_unix`, `pam_systemd` e, col pacchetto, la riga
  `session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login` (`debian/remotix.pam-config`: `Priority: -1`, `Session-Interactive-Only: yes`; identico in Ubuntu). Il greeter (`sddm-greeter`) include la stessa pila ma `local_login.c` ignora le sessioni di classe diversa da `user` (riga «greeter, background, manager»): quindi il greeter non scatta [V sul codice, la sessione greeter non è stata osservata].
  Il PAM di sddm in Debian non ha `pam_env … user_readenv` per l'utente remoto: non c'entra.
- Sessione locale Debian = X11/`xfwm4`: dopo il login locale non c'è nessun `labwc` locale; il test «dopo la chiusura nessun processo remoto» in P7 deve cercare `xfwm4` come compositor locale (§0.4) — XFCE già lo fa.

Verdetto E1-LXQt: **PORTABILE COSÌ** (nessun codice da cambiare) **+ DA PROVARE COL PRODOTTO**: P1-P6 (già in Debian) e P7 con qterminal+`top` su sddm/LXQt (con gli adattamenti del §7); P8 su LXQt = BLOCKED (come Fedora: niente editor con testo non salvato senza interazione; `featherpad` è installato nella VM, mousepad no, ma il suo stdin non è noto).
Rischio/cambio comportamento: nessuno oggi; se la chiusura gentile di LXQt (`logout()`) lascia aperto un programma che chiede «salva?», la forzata scatta dopo 10 s e il desktop remoto viene chiuso con SIGTERM a labwc: è già il comportamento attuale, da misurare per tempi e assenza di core dump.

### 1.5 Diff dei blocchi LXQt di `session.c` e affini [V]
- Debian↔Ubuntu: 52 righe di diff che citano LXQt; le sostanziali sono: (a) `desktop_of_session_name` (Debian senza nomi Ubuntu, voluto); (b) `session_missing_component()` (Ubuntu, +21 righe, nuova); (c) `session_life()` a tre risposte al posto di `session_alive()` (ramo LXQt: `name_owner_three(bus, "org.lxqt.session")`; Debian 1026 `name_has_owner`); (d) compositori X11 + programmi condivisi + copertura blueman in `lxqt_session_commands()` e messaggio finale; (e) cartelle di sessione tipo `/etc/xdg/xdg-Lubuntu` (Ubuntu) contro `local_session()` semplificata di Debian («sempre vuota»); (f) `LXQT_SCRIPT_HEAD` commento («two scripts» → «session's scripts»).
- Ubuntu↔Fedora: nessuna differenza nei blocchi LXQt di `session.c`; le altre differenze di `session.c` (186 righe) sono KDE-`--virtual`, lingua/LC_*, dconf in `/run/remotix` (SELinux), chiusura KDE 5 s.
- Altri file con LXQt: `main.c:3458` (`wt_desktop("lxqt")`, identico), `child.c:8790-8854` (rinascita LXQt/XFCE, identico nei tre alberi nella parte LXQt), `input.c` (`input_dropped`: Ubuntu corregge il caso wlroots = XFCE/LXQt, vedi U3), `wlroots.c`, `shape.c`, `capture.h` (tutti identici).

## 2. A5 — «chi ha chiuso la connessione QUIC e perché» (`transport.c`)
1. Una riga di registro in più alla chiusura di una connessione QUIC: chi ha chiuso (il peer, noi, silenzio/idle, o «lasciata cadere»), il codice (alert TLS con nome, es. `42 bad_certificate`), e se l'handshake TLS era completo.
2. Debian: `debian13/src/transport.c` è **identico a Ubuntu** (0 righe di diff) [V]; non ha `close_why()`: righe di chiusura a `transport.c:963-976` senza il suffisso.
3. Diff Ubuntu(=Debian)↔Fedora: **164 righe, tutte aggiunte** (nessuna riga tolta tranne le 3 `registro_dice/log_detail` riscritte): `tls_alert_name()`, `transport_error_name()`, `close_why()` (+126 righe a Fedora 955-1080), le tre chiamate alla chiusura (1090-1105) e due `ngtcp2_ccerr_set_liberr(&c->last_error, rv, NULL, 0)` per la chiusura per silenzio (2187-2189, 2597-2600).
4. API ngtcp2 usate: `ngtcp2_conn_get_ccerr2`, `ngtcp2_conn_in_draining_period2`, `ngtcp2_conn_in_closing_period2`, `ngtcp2_conn_get_handshake_completed2`, `ngtcp2_ccerr_set_liberr`, `NGTCP2_CCERR_TYPE_*`, `NGTCP2_CRYPTO_ERROR`, `NGTCP2_ERR_IDLE_CLOSE`. Debian già usa le varianti `…2` (`in_draining_period2` ×2, `in_closing_period2` ×1, `get_tls_alert2` ×2, `ngtcp2_ccerr_set_liberr` ×2) [V `grep`]. Debian costruisce con **ngtcp2 1.25.0 e nghttp3 1.18.0 statici** (`build/quic-static.sh:20-21` `NGHTTP3_VER=v1.18.0`, `NGTCP2_VER=v1.25.0`; `debian/rules:36-37` controlla `pkg-config` = 1.25.0/1.18.0; `debian/control:104` `Static-Built-Using`); `quic-static.sh` è identico a Ubuntu (Fedora lo ha riscritto, stesse versioni). Fedora ha compilato `close_why()` proprio con 1.25.0 [D: dal PIANO Fedora; la versione di ngtcp2 vera nella VM Fedora non l'ho guardata]. Un'intestazione 1.26.0 trovata sul tablet (overlay di un contenitore) ha tutti questi simboli [V], non è la 1.25.0 di costruzione.
5. **Verdetto: PORTABILE COSÌ.** Come: applicare a `debian13/src/transport.c` il diff Ubuntu→Fedora (`diff ubuntu26.04/src/transport.c fedora45/src/transport.c`) — oppure copiare `fedora45/src/transport.c` per intero: i due file Debian e Ubuntu sono identici e quello di Fedora li estende soltanto (la differenza 164 righe è tutta A5). Dimensione: piccolo (~165 righe, un solo file). Dipende da nulla.
6. Rischio: nessun cambio di comportamento (solo testo del registro; la riga ha il testo del peer, solo ASCII, max 60 caratteri). Da provare: compilazione con ngtcp2 1.25.0 nella VM di costruzione; riga vista con un client che rifiuta il certificato.

## 3. U2 — «il compositor non è installato» (codice 0x0E)
1. Dire chiaro all'utente (0x0E) che il desktop non può nascere perché manca `labwc`, invece di ammetterlo e mostrare un canvas nero.
2. Debian oggi: `session_missing_component` **non esiste** (`grep`: 0 occorrenze in `debian13/src`); `labwc` è solo `Recommends` (`debian/control:99`, `apt install --no-install-recommends` lo lascia fuori). `recognize_desktop()` (`session.c:540-596`) già registra «labwc is NOT» nella descrizione, ma il login viene ammesso. Per desktop [V sul codice]:
   - **XFCE e LXQt**: utente ammesso, figlio nato, `exec labwc` fallisce (`exec: labwc: not found` solo in `session.log`), l'utente vede un canvas vuoto senza spiegazione.
   - **KDE**: nessun guasto: `kwin.c:1315-1327` (`--kwin-nested`) ripiega dichiarato su KWin `--virtual` a misura fissa («DECLARED FALLBACK»), il desktop nasce ma non si ridimensiona alla riattivazione. Ubuntu non ha questo ripiego (usa il suo labwc) e `session_missing_component()` ritorna NULL per KDE; lo stesso va bene per Debian.
   - **GNOME**: nessun compositor esterno: nessun problema.
3. Verdetto: **PORTABILE CON ADATTAMENTO.** Si prende da Ubuntu (identico in Fedora tranne il testo «weak dependency»/`dnf`): `session.c` `session_missing_component()` (+21 righe a 754-774), dichiarazione in `session.h`, ramo in `main.c` (1172-1194, +22), seconda guardia in `session.c` (Fedora 8462, Ubuntu `session.c` 2 occorrenze), nota in `page.html` («SIX» invece di «FIVE» nel commento, solo commento). Il testo è già Debian (`--no-install-recommends`, «package `labwc`»). Dimensione: piccolo (~60 righe).
4. Dipende da: `only_this_login`/codice 0x0E già esistenti in Debian; nessuna dipendenza da U3. Cambio visibile all'utente: sì, positivo (messaggio al posto del canvas nero) → approvazione del proprietario. Alternativa da proporre al proprietario (non è nel perimetro del codice): mettere `labwc` in `Depends` (decisione di pacchetto).
5. Misurato: `apt-cache policy labwc` = candidato 0.8.3-1, non installato nella VM; `apt-cache depends labwc`: `Depends: xwayland` (non solo `wlr-randr`, che non c'entra col rifiuto). Da provare col prodotto: `apt --no-install-recommends` su VM `lxqt` e `xfce`, un login: deve arrivare 0x0E con la frase e nessun processo del figlio.

## 4. U3 — «la sessione è finita» detta prima di smontare lo stage
1. Il figlio dice «sessione finita» al padre PRIMA di smontare lo stage (smontare può attendere RealtimeKit fino a 25 s), il padre chiama il cliente con 0x04/0x10 giusto, e un login che nel frattempo arriva non si attacca a un desktop che sta morendo. In più: scala GNOME rifiutata → 0x0E invece di pagina nera.
2. Stato in Debian [V diff]: non c'è nulla di tutto questo: `child.c` senza `session_over_early`, `finished_told`, `scale_refused`, `fatal`/`STAGE_MIN`, `closing_asked_ms` anticipato; `webtransport.c/h` senza `wt_dismiss_user_session_over`; `rcp.c/h` senza `rcp_admitted_waiting`; `main.c` senza `stage_refused_by_child` e senza `children_hook_stage_refused`.
3. **Pezzi e da dove prenderli** (diff Debian↔Ubuntu: `child.c` 518 righe, `child.h` 8, `webtransport.c` 37, `webtransport.h` 6, `rcp.c` 9, `rcp.h` 3, `main.c` 83, `session.h` 86; Ubuntu↔Fedora per questi pezzi: 0 righe):
   - `rcp.c/h` (+8/+2 righe) e `webtransport.c/h` (+36/+5): **prendere da Ubuntu per intero** (diff solo additivo; `webtransport.c` ha 0 righe tolte). Piccoli, indipendenti.
   - `child.h` (+7: `ChildStageRefused`, `children_hook_stage_refused`): da Ubuntu.
   - `child.c`: **NON il file intero.** Prendere a mano (hunk) da Ubuntu: `struct body_stage.fatal` + `STAGE_MIN`; `closing_asked_ms` anticipato (3378); messaggio «finished» prima della chiusura leggera (3394, 10514-10517 `local_light_close`); `p.fatal` + `on_stage_refused` (3435-3448, 4367-4374); `finished_told`, `session_over_early()` (9789-9824) e le sue chiamate (11728-11735, 12309-12311); `session_life()` nella porta «input channel closed» (11707-11728, `EIS_UNKNOWN_ROUNDS`); parte `scale_refused` (9168-9222, 10520-10539) **solo se si porta U4/GNOME scale** (`mutter_scale_to_one` in `mutter.c`).
   - `main.c`: `stage_refused_by_child()` (+17), `wt_dismiss_user_session_over` ai due posti (2146-2152, 2349), commento 0x04, `children_hook_stage_refused(...)` (3922). Il resto del diff di `main.c` è U2 e U1 (`--dconf-keyfiles`).
   - `session.c`/`session.h`: **`session_life()`** (tre risposte) al posto di `session_alive()`: fa parte del lotto (+`name_owner_three`, `SessionLife`), serve a U3. Per LXQt: ramo `SESSION_BUS_LXQT` identico. `session_kde_logout_watch()` che ritorna `bool` (U7) è nell'hunk a 10553-10567 di `child.c`: si porta solo con U7.
   - `input.c` (24 righe): `input_dropped()` per wlroots (`wlr_input_dropped`): **corretta in Ubuntu un bug del vecchio ramo `!in->wlr && in->dropped`, sempre 0 su XFCE/LXQt**; `input.h` commento. Piccolo, ma cambia quando U3 vede finire la sessione su XFCE/LXQt (usata solo insieme a `session_life()`).
4. **Che cosa di Debian va preservato in `child.c`** (non esiste in Ubuntu/Fedora): `--session-fd`/fifo (`child.c` `become_and_exec` ~1709-1737, `a_sfd`, `argv[26]` «+2», ricezione ~10090-10108); PATH fisso `/usr/local/bin:/usr/bin:/bin` (1781: Ubuntu prende il PATH da PAM con `child_path_ok()`: è la voce A3, portabile e collegata alla riga di `remotix.pam` «`pam_env` … Do NOT add `user_readenv=1`», che manca in Debian di 2 righe). Tolte da Debian apposta: SELinux, `dlfcn.h`.
5. Verdetto: **PORTABILE CON ADATTAMENTO**, dimensione **media/grande** (~330 righe di `child.c` a mano, ~110 altrove). È la voce più intrecciata: mescola U3 + U4 (scala, solo GNOME) + U5 (`capture_watch_sequence`, solo KDE) + U7 (`session_kde_logout_watch`) + U1 (dconf) nello stesso `child.c`. Ordine proposto: (1) `session_life()`/`name_owner_three` in `session.c`; (2) rcp/webtransport/child.h/main.c; (3) hunk di `child.c` di U3 senza scala; (4) scala (con U4) in un secondo tempo.
6. Rischi/cambi per l'utente: la pagina del client dice «sessione finita» fino a ~17-25 s prima in caso di Log Out; su KDE l'avviso anticipato **non scatta** (esplicito: `stage_kwin` escluso). Cambio da approvare. Da provare: Log Out dal desktop su GNOME 48, XFCE, LXQt con client aperto e con rientro entro 10 s (login subito dopo il logout); sessione bus che sparisce («UNKNOWN») su GNOME; KDE senza avviso anticipato.
7. Misurato in VM: nulla di specifico (richiede il prodotto).

## 5. U9 — sentinella: errori di logind leggibili (`sentinel.c/h`)
1. Se una chiamata a logind (`CanPowerOff/Reboot/Suspend/Hibernate`) fallisce, la riga dice quale chiamata e perché; e «na» (non disponibile) vale come «no».
2. Debian: `sentinel.c:889-908` usa il `call()` generico e scrive «(no answer)»; accetta solo `no` (`sentinel.c:903-905`); `piece[64]`.
3. Ubuntu (= Fedora): `g_dbus_connection_call_sync` con `GError`, `piece[192]`, `na` accettato. Diff `sentinel.c` 35 righe, `sentinel.h` 7 (solo commento).
4. **PORTABILE COSÌ**: copiare `sentinel.c/h` di Ubuntu (diff piccolo, nessuna dipendenza). Piccolo (~20 righe).
5. Cambio comportamentale: con `CanHibernate=na` (nessuna swap/resume, o VM) l'allarme «shutdown non vietato» **non scatta più** (oggi scatta): è la ragione della modifica. Da approvare. Misurato nella VM Debian: `CanPowerOff/Reboot/Suspend/Halt = challenge`, `CanHibernate/CanSuspendThenHibernate/CanHybridSleep = na` (senza regola polkit del pacchetto, e come utente `prova`). Da provare col prodotto: con la regola polkit installata, le quattro risposte devono essere `no`/`na` e nessun allarme.

## 6. Quadro d'insieme dei file di `debian13/src`

Conteggi `diff | wc -l`. Su 109 file (compresi `protocols/` e `opus-wasm/`: identici fra i tre alberi tranne `protocols/kde-output-*.xml` e README, solo in Fedora) **81 sono identici ai due**, 28 differiscono da almeno uno. Fedora ha in più `remotix-pam-hook` (C7, non serve a Debian: c'è `pam-auth-update`).
Colonne: D-U = Debian↔Ubuntu, D-F = Debian↔Fedora, U-F = Ubuntu↔Fedora. «+N/-M» = righe che Ubuntu/Fedora ha in più / che Debian ha di suo.

| File | D-U | D-F | U-F | Proposta |
|---|---:|---:|---:|---|
| `capture.c`/`capture.h` | 146/62 | 146/62 | 0 | Prendere da Ubuntu (U5: `capture_watch_sequence`, `capture_frame_lost`; solo aggiunte, -1 riga). Innocuo se non scatta. Insieme a `kwin.c/h`. |
| `child.c` | 518 | 880 | 370 | **Tenere Debian e applicare a mano** (§4): hunk di U3 da Ubuntu; A1/A2/A3 da Fedora (`child_locale_*`, PATH) senza SELinux; preservare `--session-fd`. Mai il file intero. |
| `child.h` | 8 | 8 | 0 | Da Ubuntu (U3). |
| `input.c` | 24 | 41 | 17 | Tenere Debian, applicare `input_dropped` wlroots (Ubuntu), commenti dconf solo con U1; A4 (primo movimento puntatore) da Fedora (17 righe di Fedora vs Ubuntu: `input.c` 257, 1330, 1937-1952), da provare su GNOME 48. |
| `input.h` | 9 | 9 | 0 | Da Ubuntu (commento). |
| `kdehost.h` | 0 | 69 | 69 | Tenere (=Ubuntu). Fedora: solo KWin `--virtual` (D1): non portare. |
| `kwin.c` | 249 | 782 | 533 | **Tenere Debian** (labwc di distribuzione da PATH + ripiego `--virtual`, voluto) e applicare da Ubuntu SOLO U5 `kwin_poke` e simili (U6 sidecar ScreenSaver da verificare su Plasma 6.3.6). Non prendere il file di Ubuntu: ha `REMOTIX_LABWC` (tolto da Debian, PULIZIA 9). Fedora: non portare (D1-D3). |
| `kwin.h` | 7 | 25 | 18 | Da Ubuntu `kwin_poke` (+6 righe). Fedora: no. |
| `main.c` | 83 | 105 | 28 | **Tenere Debian e applicare a mano** da Ubuntu: U2 (+22), U3 (`stage_refused_by_child` +17, `wt_dismiss_user_session_over` ×2), U1 (`--dconf-keyfiles`, solo con U1). Da Fedora: A9 (testo PAM riscritto, 2 righe; per Debian il rimedio va scritto «reinstall … `.deb`», B3), niente `--kwin-virtual`. Debian ha di suo: `kwin_nested_alive` (non perdere). |
| `Makefile` | 7 | 19 | 12 | Tenere Debian. Ubuntu aggiunge `LABWC`/`REMOTIX_LABWC` (non portare); Fedora `-lselinux` ecc. (non portare). |
| `mutter.c`/`mutter.h` | 139/14 | idem | 0 | Da Ubuntu (U4: `mutter_scale_to_one`, GNOME 50): 133 righe aggiunte, 3 tolte; guardia a runtime: proporre di portarla e dichiararla «non provata su GNOME 48». Serve a `scale_refused` di U3. |
| `page.html` | 15 | 15 | 0 | Da Ubuntu (solo commenti 0x0E «SIX»; 3 righe Debian tolte sono commento). |
| `rcp.c`/`rcp.h` | 9/3 | 9/3 | 0 | Da Ubuntu. |
| `remotix.pam` | 3 | 179 | 181 | Debian = Ubuntu + 2 righe di commento (`user_readenv`): prendere la riga da Ubuntu (A3). **Non** Fedora. |
| `remotix-remote-sessions.rules` | 0 | 7 | 7 | Applicare da Fedora la regola fwupd (A8, 4 righe); da verificare su GNOME 48 di Debian. |
| `rootside.c` | 2 | 2 | 0 | Da Ubuntu: 1 riga `session_dconf_system_db_ensure()` — solo con U1. |
| `sentinel.c`/`sentinel.h` | 35/7 | idem | 0 | Da Ubuntu (U9, §5). |
| `session.c` | 2177 | 2299 | 186 | **Tenere Debian e applicare a mano** da Ubuntu, per blocchi: `session_life`+`name_owner_three`, `session_missing_component`, U1 (dconf, ~1000 righe, grande), U7 (watch KDE), U8-LXQT/XFCE (compositori X11, blueman, §1.2), A1/A2 da Fedora (`LC_*` in `OUR_VARIABLES` e `session.c:3711-3716`), A6/A7 da Fedora (3 righe: `SESSION_UNIT_GRAPHICAL`, `wait_until_done_ms`). **NON** portare: nomi Ubuntu, `local_session_name_find` e simili, ramo GNOME 50 (`SESSION_UNIT_SHELL_MODEL`, ma Debian ha `SESSION_UNIT_SHELL_48`), `--kwin-virtual`/`REMOTIX_KDE_HOST` (D1), dconf in `/run/remotix` (C5), SELinux. |
| `session.h` | 86 | 86 | 0 | Da Ubuntu le dichiarazioni nuove (`session_missing_component`, `SessionLife`, dconf se U1); non il ramo `SESSION_UNIT_SHELL_MODEL`. |
| `transport.c` | 0 | 164 | 164 | Da Fedora (A5, §2). |
| `walls.c` | 0 | 102 | 102 | Tenere (=Ubuntu, senza SELinux). Fedora: SELinux (C2): non portare. |
| `webtransport.c`/`.h` | 37/6 | idem | 0 | Da Ubuntu (U3). |
| tutti gli altri (81 file, fra cui `local_login.c`, `rediscover.c`, `walls.h`, `tls.c`, `wlroots.c`, `shape.c`, `wlr_input.c`, `clipboard*.c`, `encoder.c`, `vadirect.c`, i `.h`) | 0 | 0 | 0 | Identici: nulla da fare. |

**Che cosa Debian ha di SUO e non deve perdersi** (diff in verso opposto, `docs/PULIZIA-tranche1.md` + diff):
1. `child.c`: `--session-fd` e il fifo di logind (systemd 257), PATH fisso, niente SELinux/`dlfcn`; richiede che `main.c` di Debian accetti `--session-fd` (nel codice è in `child.c` `10090`: già in sede).
2. `kwin.c`/`main.c`: KWin nato dentro il `labwc` di distribuzione (`g_find_program_in_path("labwc")`, `execlp("labwc")`, ripiego `--virtual`); `--kwin-nested` in `main.c` (Ubuntu e Debian) — Fedora l'ha tolto.
3. `session.c`: `SESSION_UNIT_SHELL_48` (`org.gnome.Shell@wayland.service`), `local_session()` semplificata, `desktop_of_session_name()` senza nomi Ubuntu, nessun test sul `ID` di os-release, `unit_shell()` senza ramo GNOME 50.
4. `input.c`: `REMOTIX_EI_PING` senza `#ifdef`; `Makefile` senza `LABWC`, `-ldl`, target bench; `remotix-polkit-seated` senza ramo `90-default-privs`.
5. `debian/`: niente `remotix-net-move`; `debian/remotix.pam-config`; `Recommends: labwc` (non `Depends`).
Se un file di Ubuntu/Fedora viene preso intero, questi punti ritornano o spariscono: per `child.c`, `kwin.c`, `main.c`, `session.c`, `session.h`, `Makefile`, `input.c` **si lavora a hunk sul file di Debian**.

## 7. Strumenti di prova `prove/`
Debian vs Ubuntu / Fedora (righe di diff): `all.sh` 91/91, `avlib.py` 3/3, `base-check.py` 10/10, `check-ban.py` 8/8, `check-desktop.py` 86/103, `check-input.py` 64/64, `check-package.py` 4/4, `check-prelocal.py` **0**/330, `fresh.sh` 9/9, `lib.py` 14/14, `package-snap.py` 2/2, `window-input.py` 26/26. Ubuntu↔Fedora: tutti 0 tranne `check-desktop.py` 17, `check-prelocal.py` 330, `lib.py` 4. Solo in Ubuntu e Fedora: `banco-vm/` (`box.sh`, `fresh-vm.sh`, 86 righe ciascuno; Fedora in più `autologin-lightdm.sh`, `autologin-sddm.sh`). Solo in Fedora: `check-exit.py`, `check-resize.py`, `hold.py`, `hold-user.py`, `prelocal.sh`, `check-kde-*.py` (4), `giro-*-radeon.sh`, `giro-selinux.sh`, `wall-*`.
Debian oggi prova su **contenitori** (`boxes/`, porte 8811-8814); Ubuntu e Fedora su VM con `RX_BANCO=vm`.

Che cosa serve per provare la 1.2.0 sulle quattro VM Debian (ssh 2361-2364, REMOTIX 8861-8864; VM chiamate `gnome`, `kde`, `xfce`, `lxqt`, hostname `rx-deb-<nome>`, radice `/media/REMOTIX-DEBIAN/vm-radeon`):
1. `lib.py`: aggiungere il blocco `RX_BANCO=vm` (Ubuntu: `BOXES=banco-vm`, `PORTS`) con `PORTS = {gnome:8861, kde:8862, xfce:8863, lxqt:8864}` e `RX_TEMPO` (fattore di tempo): **diff Ubuntu 14 righe**, copiabili cambiando le porte. Debian ha 8811-8814 (contenitori).
2. `banco-vm/box.sh` e `fresh-vm.sh`: copiare da Ubuntu e cambiare `VM_ROOT=/media/REMOTIX-DEBIAN/vm-radeon`, `choose()` (nomi `gnome|kde|xfce|lxqt`, porte 2361-2364 / 8861-8864), `install` (stesso `apt-get install --reinstall`, giusto per `.deb`); in `fresh-vm.sh` il controllo di identità (`ubuntu 26.04` → `debian 13`; `WANT` dei display manager: `gdm3`, `sddm`, `lightdm`, `sddm`: giusto come in Ubuntu) e l'elenco dei pacchetti extra («pcmanfm-qt su lxqt», ecc.). `rootkey` presuppone `prova` con sudo e `vmkey` (VM-BANCO.md: c'è) e `PermitRootLogin` che accetti la chiave (trixie: `prohibit-password` di default, [D]).
3. `all.sh`, `fresh.sh`, `avlib.py`, `base-check.py`, `check-ban.py`, `check-input.py`, `check-package.py`, `package-snap.py`, `window-input.py`: Debian = versione precedente di Ubuntu; i file di Ubuntu cambiano i percorsi `/media/REMOTIX-UBUNTU/…` (da sostituire con `…DEBIAN`), aggiungono `RX_BANCO`, `--clean`, `--only`, skip. Ubuntu-specifico da NON portare: `sudo-rs` (`check-desktop.py` 309: messaggi di sudo-rs; Debian ha sudo GNU), `ptyxis` (Fedora; Debian ha `gnome-terminal`), `.config/dconf/remotix$` nella lista (è di U1).
4. `check-prelocal.py` P7/P8 (330 righe, solo Fedora): copiare da Fedora con questi adattamenti [V sul codice e sulla VM]: `DM` = `gdm3`/`sddm`/`lightdm`/`sddm` (non `gdm`, non `plasmalogin`); `AUTO_ON/OFF` GNOME: file `/etc/gdm3/daemon.conf` (sezione `[daemon]`), non `/etc/gdm/custom.conf`; KDE su sddm: serve uno script tipo `autologin-sddm.sh` con `Session=plasma` (Fedora usava `plasmalogin.conf.d`); XFCE: `autologin-lightdm.sh` (6 righe, controllo `hostname = rx-deb-xfce`); LXQt: `autologin-sddm.sh` con **`Session=lxqt`** (X11) e `hostname = rx-deb-lxqt` (non `rx-lxqt`); `COMPOSITOR["lxqt"] = ("xfwm4","labwc")` e `COMPOSITOR["xfce"]` come già; `TERMINALS`: `gnome-terminal` (non `ptyxis`; confermare `gnome-terminal -- top`), `konsole -e top`, `xfce4-terminal -x top`, `qterminal -e top` (presente nella VM); `EDITORS`: `kwrite`/`mousepad` come Fedora [da verificare cosa sia installato nelle VM `kde`/`xfce`]; LXQt e GNOME restano BLOCKED. Togliere/proteggere le righe SELinux (`ausearch`, assente) e `coredumpctl` (assente: serve `command -v`, o installare `systemd-coredump` — decisione del proprietario). `p6_fedora()` non serve: Debian ha `common-session` (P6 di Debian lo controlla già). `UNIT_IDS` ok (`systemd --user`).
5. `prelocal.sh`, `check-exit.py`, `check-resize.py`, `hold.py`, `hold-user.py`: generici, percorsi `/media/REMOTIX-FEDORA/…` e nomi di processo (`labwc` per remoto, `lxqt-panel`, `xfce4-panel`) da cambiare; `check-kde-exit.py` forse riusabile per A6/A7 (KWin 6.3.6 da misurare). Non portare: `giro-selinux.sh`, `wall-*`, `check-kde-birth/live/resize.py` (D).
6. Nessun `coredumpctl`/`auditd` nelle VM Debian: se le prove vogliono i core dump, `systemd-coredump` va installato o la riga tolta.
Dimensione: medio (3 file da copiare e ritoccare, ~15 righe di porte e percorsi; P7/P8 ~330 righe con ~10 ritocchi).

## 8. Misure sulla VM `lxqt` (comandi e risultato essenziale)
- `vm-radeon.sh accendi lxqt virtuale` → `up, virtual video (ssh -p 2364 …)`; spenta con `spegni lxqt` → `stopped`; nessun posto-turno preso né da liberare (regola cambiata dal coordinatore).
- `ls /etc/xdg/autostart` + `grep` delle chiavi + `dpkg -S`: 22 voci, tutte da pacchetti Debian (§1.1).
- `cat /usr/share/xsessions/lxqt.desktop` (`Exec=startlxqt`), `ls /usr/share/wayland-sessions` → non esiste; `apt-cache policy lxqt-wayland-session` → nessun candidato.
- `apt-cache depends lxqt`: `Depends: xfwm4`; `lxqt-session 2.1.1-1` Depends `liblayershellqtinterface6`; `labwc 0.8.3-1` Depends `xwayland`, `libwlroots-0.18`.
- Accesso grafico di `prova` da sddm (`scrivi prova2026` + `tasti kp_enter`): `loginctl` session 10 `Seat=seat0 Service=sddm Type=x11 Class=user Desktop=LXQt`; `lxqt-session` ambiente: `XDG_CURRENT_DESKTOP=LXQt`, `XDG_SESSION_TYPE=x11`, `DISPLAY=:0`, `PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games`, `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share`, `QT_QPA_PLATFORMTHEME=lxqt`; processi vivi (elenco §1.1); `~/.config/lxqt/session.conf`: `window_manager=xfwm4`.
- `/etc/pam.d/sddm`, `sddm-greeter`, `sddm-autologin`: `@include common-session` in tutti e tre; `/etc/pam.d/common-session`: `pam_umask`, `pam_unix`, `pam_systemd` (nessuna riga REMOTIX, pacchetto non installato).
- `busctl call … CanPowerOff|Reboot|Suspend|Halt` = `challenge`; `CanHibernate|SuspendThenHibernate|HybridSleep` = `na`. `systemctl --version`: systemd 257 (257.13-1~deb13u1).
- `command -v`: `qterminal`, `top`, `python3` presenti; `coredumpctl`, `ausearch`, `mousepad`, `kwrite` assenti; `featherpad 1.6.1` presente.
- `/etc/xdg/lxqt/panel.conf` (pacchetto `lxqt-branding-debian`) ≠ `/usr/share/lxqt/panel.conf` (`lxqt-panel`).
- Nota: ho scritto un file di schermata temporaneo `/tmp/lxqt-s1.png` sul server (ora cancellato) per leggere il greeter; nient'altro oltre allo script. Nella home di `prova` della VM restano le impostazioni del login (ammesso).

## 9. Da provare col prodotto (non fatto, non possibile in questa fase)
labwc 0.8.3 con `lxqt-session` 2.1.1 remoto (compreso `nm-tray`, `print-applet`, `qlipper`, `pulseaudio`); P1-P7 su sddm/LXQt (tempi, nessun core dump); log-out dal menu LXQt con U3; `--no-install-recommends` con XFCE/LXQt (U2); riga A5 con client che rifiuta il certificato; sentinella con la regola polkit installata e `CanHibernate=na`; compilazione di A5 con ngtcp2 1.25.0 nella VM di costruzione.
