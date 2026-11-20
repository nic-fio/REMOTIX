# 16 — Inventario per il manuale tecnico di REMOTIX per Ubuntu 26.04

Data: 20 nov 2026. Albero: ramo `ubuntu-26.04` (commit `50d997b`), confrontato con `main` (REMOTIX 1.0.0 Debian 13).
Base: i 25 capitoli di `manuals/sources/technical-debian13/` (9797 righe), copiati in `manuals/sources/technical-ubuntu26.04/`.
Metodo: cinque letture parallele (una per gruppo di capitoli), ciascuna sul testo del capitolo, sui diff `main..ubuntu-26.04`
(`src/`, `debian/`, `build/`, `prove/`, `server/`, `docs/`), sugli studi 1-15, su `docs/REGISTRO-problemi.md` e `PIANO.md`.
Dove una cosa non e' stata verificata nel codice o su una macchina c'e' scritto «non verificato».
I frammenti per capitolo (parte 1) sono il lavoro dei cinque lettori, riuniti senza riscrittura: ogni gruppo ha in fondo i propri
elenchi (a) cose nuove, (b) cose di Debian da togliere, (c) rif() e stile. Le parti 2-5 sono la sintesi.

## Riepilogo numerico (246 sezioni)

| Gruppo | Capitoli | Sezioni | Vale com'e' | Da correggere | Da riscrivere |
|---|---|---|---|---|---|
| G1 | ch01-ch05 | 56 | 32 | 21 | 3 |
| G2 | ch06-ch11 | 85 | 59 | 24 | 2 |
| G3 | ch12-ch14 | 31 | 15 | 13 | 3 |
| G4 | ch15-ch18 | 36 | 9 | 23 | 4 |
| G5 | ch19-ch25 | 38 | 8 | 24 | 6 |
| Totale | 25 | 246 | 123 | 105 | 18 |

Avvertenze generali emerse:
- Molte cifre del manuale Debian (righe di `child.c`, `session.c`, `registro_dice`, numero di check in `all.sh`, dimensione di `page.html`) erano gia' vecchie rispetto a `main`: vanno RICONTATE sul ramo, non copiate. I comandi di conteggio sono nei frammenti (ch21, ch22).
- I log dei giri Ubuntu stanno sul server (`/media/REMOTIX-UBUNTU/log/`, `.../pacchetti/unione10/controlli.txt`, `lintian.txt`), non nell'albero: nessun lettore li ha visti. Cifre di test di Ubuntu: usare solo quelle di `studio/giro1-*`, `giro2-*`, `PIANO.md`, registro; il resto «non verificato», oppure serve un agente con accesso al server.
- `CLAUDE.md` del ramo dice ancora «Debian trixie only» e `src/remotix.pam` ha ancora l'intestazione «DEBIAN 13 ONLY»; `local_login.c:20` cita «systemd 257». Sono difetti del sorgente, non del manuale: il manuale non li deve ripetere (decisione richiesta: correggere i file o citarli com'e').
- `DECISIONS-11.md` §11.55 (`--session-fd`) e' vero per Debian ma il ramo non lo passa piu' (c'e' una nota di 4 righe nello stesso paragrafo).

---------------------------------------------------------------------------------------------------

# PARTE 1 — Capitolo per capitolo

<!-- ===== frammento g1 ===== -->
# Inventario gruppo 1 — ch01 introduzione, ch02 architettura, ch03 ciclo di vita, ch04 trasporto, ch05 RCP

Albero: `~/Documenti/REMOTIX-UBUNTU`, ramo `ubuntu-26.04` (commit `50d997b`). Confronto: `git diff main..ubuntu-26.04`. Sola lettura.
Nota di processo: per errore ho eseguito una volta `git checkout --detach` (HEAD staccato sullo stesso commit); l'ho subito rimesso con `git checkout ubuntu-26.04`. Nessun file toccato, `git status` identico a prima (solo PIANO.md, build.py, cartella technical-ubuntu26.04 e l'html non tracciati/modificati, già presenti).

Quadro dei diff che toccano la mia area (src/): `session.c` +1889 (modello dconf, GNOME 50, KDE logout, `session_life`, labwc mancante), `child.c` (+443: niente `--session-fd`, PATH da `pam_env`, `fatal` in MSG_STAGE, farewell anticipato), `main.c` (+69), `sentinel.c` (`na`), `webtransport.c/.h` (`wt_dismiss_user_session_over`), `rcp.c/.h` (`rcp_admitted_waiting`), `rootside.c` (+1 riga), `kwin.c`, `mutter.c`, `capture.c`, `input.c`. NON toccati: `transport.c`, `cid.*`, `page.c`, `tls.c`, `certificates.c`, `walls.c`, `helper.c`, `rootside_proto.h`, `rediscover.*`, `hsrate.h`, `resetcap.h`, `msgrate.h`, `debian/remotix.service`, `docs/RCP.md`, `docs/SPECS.md`.

---
## ch01_introduction — «Introduction and concepts» (240 righe, 5 sezioni)

### 1. What REMOTIX is and what it promises — DA CORREGGERE
- Riga 8 (FIG, zona) «The Debian 13 machine» e riga 18 (didascalia) «…on the Debian machine»: diventa Ubuntu 26.04. Riga 14 «GNOME, KDE, XFCE or LXQt»: vale, ma su Ubuntu sono i quattro sapori (Ubuntu/GNOME 50, Kubuntu/Plasma 6.6.7, Xubuntu/XFCE 4.20, Lubuntu/LXQt 2.3; versioni da `studio/giro*-*.md` e `studio/5-sistema-ubuntu.md`).
- Righe 25-27: «built from one codebase for one distribution, Debian 13 (trixie). Each distribution… its own manual»: oggi «Ubuntu 26.04 (resolute)»; il codice di questo ramo serve i quattro sapori Ubuntu, non «una distribuzione» di un solo desktop.
- Riga 35 «Version: from RX_VERSION in build/build-deb.sh»: vale (`RX_VERSION:-1.0.0~dev`, riga 38; la regex di `build.py` prende `1.0.0`). Incompleta: il pacchetto è `1.0.0-1+ubuntu26.04` (`build-deb.sh:55`, era `+deb13`), distribuzione di changelog `resolute`.
- Riga 56 «A single .deb built in a debian:trixie container»: ora `docker.io/library/ubuntu:26.04` (`build/Containerfile`), immagine `localhost/remotix-ubuntu-build`. Il pacchetto include inoltre un secondo programma, `/usr/libexec/remotix/labwc` (labwc 0.9.3 + wlroots 0.19.2 patchato, statico; `debian/rules`, `build/labwc-ospite/`), che ospita il KWin annidato: va aggiunto alla riga «Server» (righe 36-39) accanto a `remotix-local-login`.
- Riga 60 «Licence»: `LICENSE.md` ora dice che il pacchetto Ubuntu porta labwc (GPL-2, due file LGPL-2+) con wlroots (MIT) e una piccola patch nostra, sorgente corrispondente `remotix-<versione>-labwc-source.tar.gz` pubblicato con ogni release (`git diff main..ubuntu-26.04 -- LICENSE.md THIRD-PARTY-LICENSES`). «Not an open-source licence» resta vero per REMOTIX.
- Riga 58 «Size»: conteggio automatico; valori attuali che usciranno: ~105.859 righe C+header (era 103.489 su main) e 14.258 di `page.html` (14.255). Calcolati con `git ls-tree` sul ramo; la cifra esatta la dà il generatore.
- Vale: riga 42 (porta 7447), riga 44-46 (codec, VA-API/Vulkan Video, DECISIONS §10.27), righe 49-52 (cap 10, dichiarato 8 utenti/3K: `RCP_SESSION_CAP 10` in `rcp.h:94`, `RCP_CANVAS_MAX 4096×2304`), riga 53-55 (orologi: `SILENCE 30000` rcp.c:302, `DEFAULT_INACTIVITY` rcp.c:454, `DEFAULT_ABANDON_MS` main.c:1626), righe 63-67 (obiettivi SPECS §3: SPECS non cambia nel diff).

### 2. What was verified and what was not — DA RISCRIVERE
Motivo: tutta la sezione è la verifica di Debian (17 nov, 4 container, 111/118, 112/118, 111/118, 104/118; «real Debian 13 virtual machine»; Samsung DeX su GNOME; AppArmor «complain e enforce senza negazioni»). Su Ubuntu i fatti sono altri:
- Giri automatici del 18 nov nei container `rxu-*` (`studio/giro2-*.md`): GNOME 123/124 (1 FAIL: `desktop/users-shell-and-environment`, pkexec, registro E2); KDE 121/124; LXQt 124/124; XFCE 126/128 (128 righe). Le righe sono 124/128, non 118 (il numero di righe è cambiato: `prove/all.sh` ha ora 15 etichette `LABELS=…package`, diff `prove.diff`).
- Pacchetto finale `unione10` (`PIANO.md`): giro automatico completo su GNOME verde salvo la riga nota; prova a mano del proprietario sulle 4 VM QEMU (Radeon ceduta con vfio, `server/vm-radeon.sh`, `prove/banco-vm`, `RX_BANCO=vm`, `RX_TEMPO=2`) e sulle 4 live vere; su Ubuntu e Kubuntu anche «accesso locale chiude il desktop remoto». I container di prova «non esistono più» (PIANO.md), ma `boxes/*` è ancora nell'albero.
- Difetti trovati solo su macchina vera: C4 (AppArmor: `deny unix addr=@*` vietava ogni socket → accessi tutti rifiutati; profilo ancora `flags=(complain,attach_disconnected)`) e C5 (programmi snap/Flutter e `DCONF_PROFILE`). Aperti non bloccanti: E3, E4 (scatti video su Chrome Android, VM), E1 XFCE sfondo nero, avviso `wireplumber` solo in VM.
- «Non verificato» da dichiarare: ramo «vita SCONOSCIUTA» dell'avvio figlio e ramo «database diverso/più vecchio» della compilazione dconf (REGISTRO C5); AppArmor in `enforce`; NVIDIA; Firefox su Windows/Safari; Samsung DeX NON è stato riprovato su Ubuntu (non verificato: nessuna traccia nel ramo). Riga «Browsers» (Chrome/Firefox Linux): vale per `prove/` (giri), Chrome Android visto dal proprietario solo su GNOME VM (E4).
- Righe 91-98 («Browsers as SPECS §11.5», «What REMOTIX does not do»): vale com'è (SPECS.md non cambia nel diff). Riga 99-104 warn «Documents and code»: vale (Ctrl+Alt+End/Del); aggiungere che il registro B3 allinea le prove: `page-cad-hidden`, `page-ctrl-alt-end-passes` (18 nov).

### 3. Basic vocabulary and the invariants — DA CORREGGERE
- Vale: parole radice/rete/PAM/figlio/stage/canvas/slot/farewell/sentinella/found again/belts/budget (`rootside.c`, `rediscover.c`, `budget.c`, `sentinel.c` esistono; `walls.c` non toccato). Riga 126: stage «belongs to the session» vale (I4: `setsid --fork` in `session.c`).
- Riga 154: I4 «`setsid --fork` in session.c; no line ties a child to a connection» vale; ma la riga di I4 sul legame logind↔figlio è altrove (ch03).
- Riga 160-161 I7: `sentinel_shutdown_forbidden()` ora accetta `no` **o `na`** («not available on this machine»), un errore vale «non sicuro» e il dettaglio nomina chiamata ed errore (`sentinel.c`, diff); da dire nella riga I7.
- Parole nuove mancanti: **our labwc** (host del KWin annidato, percorso fissato a build time `REMOTIX_LABWC`), **profilo dconf di runtime / database di sistema `remotix`** (`session.c`, REGISTRO C5), **session_life** (ALIVE/DEAD/UNKNOWN, `session.h`), **stage refused (fatal)**.

### 4. The repository, folder by folder — DA CORREGGERE
- Riga 167 albero `REMOTIX-DEBIAN/`: la cartella radice è `REMOTIX-UBUNTU/` (CLAUDE.md del ramo ancora intitolato `REMOTIX-DEBIAN`, «Debian 13 (trixie) only»: stantio, riga 200-202 del capitolo lo cita).
- Riga 171 `debian/`: aggiungere `needrestart/remotix.conf` (nuovo, installato in `/etc/needrestart/conf.d`), `remotix.ufw`, `org.kde.remotix.desktop` esistono. Postinst compila `/etc/dconf/db/remotix`, avviso labwc mancante; postrm toglie il database e `~/.config/dconf/remotix`.
- Riga 172 `build/`: aggiungere `labwc-ospite/` (README, VERSIONS, fetch.sh, build.sh, patch `wlroots-0.19.2-remotix-presented-root.patch`). Riga 190-192: «quic-static.sh… because Debian does not ship the versions needed»: su Ubuntu 26.04 le librerie di sistema sono ngtcp2 1.16 / nghttp3 1.12 (`studio/8-pacchetto-e-prove.md:344`), troppo vecchie; la ragione vale, il nome «Debian» va tolto. `debian:trixie` → `ubuntu:26.04`.
- Righe 173-175: `prove/` aggiungere `banco-vm/` (box.sh, fresh-vm.sh); `boxes/` non è più «four containers on the dev server»: il Containerfile costruisce box Ubuntu 26.04 con i metapacchetti `ubuntu-desktop-minimal`, `kubuntu-desktop`, `xubuntu-desktop`, `lubuntu-desktop` (porte 8821-8824), ma i container sono stati sostituiti dalle VM (`PIANO.md`): non verificato se vadano ancora citati come banco.
- Riga 176 `server/`: oggi `vm-radeon*.sh`, `live-installa.sh`, `vm.sh`, `prepara-server.sh`; nuova cartella `studio/` (29 file: studi 1-15, giro1/giro2, regole) non nell'albero del Debian.
- Riga 196-198 `docs/`: `INVENTARIO-non-debian.md` e `PULIZIA-tranche1.md` esistono ancora (`ls docs`).

### 5. The project in numbers — DA CORREGGERE
- Tabella `PARTS` (righe 204-224) è dinamica: i conteggi cambiano da soli (src 105.859+14.258; debian 790→914; build 226→437; prove 8.883→9.171; boxes 586→594; server 229→945 righe, da `git ls-tree` per prefisso).
- La regola `lambda f: f.startswith(("prove/","boxes/","server/"))` va bene; la regola catch-all «Manual sources» (`lambda f: True`) conta anche i sorgenti delle DUE cartelle `technical-debian13` e `technical-ubuntu26.04` (`HERE.rglob`): se resta Debian nel ramo il totale è gonfiato (decisione aperta in PIANO.md). Riga «Build» contiene ora anche `build/labwc-ospite/*`.
- Frase riga 230 «A large share of the C is comment»: vale (non misurato, nessun diff la tocca).

---
## ch02_architecture — «Overall architecture» (452 righe, 11 sezioni)

### 1. The roles of the server executable — DA CORREGGERE
- Tabella ruoli (righe 10-28): manca `--dconf-keyfiles DIR` (`main.c:2864`, solo `argc == 3`, entry point `session_dconf_keyfiles_write()`, usato **a build time** da `debian/rules`: scrive `00-remotix` e `locks/00-remotix` da `DCONF_KEYS`; il postinst li compila).
- Riga 21 `--kwin-nested`: vale (`main.c:2886`), ma ora esegue **il nostro labwc** in `/usr/libexec/remotix/labwc` (`kwin.c:1529`, macro `REMOTIX_LABWC` da `src/Makefile` `LABWC ?=`); se manca ripiega su KWin `--virtual`, dichiarato. In `kwin.c:1562-1644` forka anche un ticker e un sidecar `org.freedesktop.ScreenSaver` (`SCREENSAVER_NAME`, Plasma ≥ 6.4).
- Riga 8-9 `remotix-local-login`: vale (`local_login.c` non toccato; il suo commento cita ancora «systemd 257», stantio su Ubuntu = 259.9).
- Righe 29-36 (riga di comando dell'unit): vale (`debian/remotix.service` non cambia).
- Riga 37-41 nota single-process: vale (nessun diff).

### 2. Process tree and privileges at a glance — VALE COM'È
Verifica: `git diff --stat main..ubuntu-26.04` non tocca `walls.c`, `rootside_proto.h`, `helper.c`, `remotix.service`; la tabella dei processi non ha righe sui nuovi file.

### 3. The root side — DA CORREGGERE
- Tabella «How the root side starts» (righe 100-115): all'inizio di `rootside_main()` ora c'è `session_dconf_system_db_ensure()` (`rootside.c:3344`, «N5, 19 nov»: compila `/etc/dconf/db/remotix` se manca o è diverso, a ogni avvio del servizio; REGISTRO C5), **prima** della sonda della scheda. Aggiungere come passo 0b.
- Il resto (poll 1000 ms, `NET_RESTART_CAP_MS 30000` rootside.c:68, `STOP_WAIT_MS 25000` :73, `KIDS_EOF_GRACE_MS 5000` :82, `STOP_CLOSE_WAIT_MS 15000` main.c:532) verificato con grep: vale.

### 4. The network side and its walls — DA CORREGGERE
- Riga 183-192 riga «AppArmor» e `warn`: «On the real Debian 13 virtual machine it was loaded in complain and in enforce mode with no denial up to the connection; that machine has no graphics card…»: falso per Ubuntu. Fatti: il profilo `remotix_network` resta `flags=(complain,attach_disconnected)` (diff `debian/remotix_network.apparmor`); su Ubuntu 26.04 (kernel 7.0, AppArmor attivo di serie, mediazione dei socket unix) la riga `deny unix addr=@*` vietava **ogni** socket e valeva anche in complain: nessun login funzionava (C4, 19 nov, live Ubuntu 26.04.1). Ora due righe: `deny unix (bind, listen) addr=@**,` e `deny unix (connect, send, receive) peer=(addr=@**),`; limite noto: «autobind» ancora permesso. Percorsi XKB nuovi (`/usr/share/xkeyboard-config-2/**`, `/etc/xkb/**`, `/etc/X11/xkb/**`: xkb-data 2.46), `include if exists <local/remotix_network>`. Il «no capability» va qualificato: `nameservice → nis` porta `capability net_bind_service` (innocuo, set vuoto).
- Verifica Ubuntu: sessione sotto profilo osservata su macchina vera (VM con Radeon + live), «CONNECTED» nel log (C4); `enforce` non provato.
- Resto (walls: PID/mount/net namespace, seccomp, `WALLS_NPROC_MAX 128`, quattro thread): `walls.c`/`walls.h` non toccati: vale.

### 5. The closed list between the two sides — VALE COM'È
Verifica: `rootside_proto.h` e `rootside.c` (solo +1 riga) non toccano regole, grant, limiti, messaggi.

### 6. The PAM helper — VALE COM'È
Verifica: `helper.c` non nel diff; `remotix.pam` cambia solo un commento (la `PATH` viene da `pam_env`, non aggiungere `user_readenv=1`). Numeri `MAX_IN_FLIGHT` ecc. non ricontrollati uno per uno (nessun diff).

### 7. The per-user child — DA CORREGGERE
- Riga 4 tabella «birth» passo 4 (righe 283-287): «The logind session belongs to the process that holds the session's fifo, so the fifo's descriptor is carried across the execve() with `--session-fd` (17 Nov 2026)» è **falso su Ubuntu**: sono stati tolti la ricerca del fifo e l'opzione `--session-fd` (`child.c`, `git diff`; `DECISIONS-11` nota del 18 nov). Dalla v258 logind tiene la sessione con il **pidfd del leader** (`pam_systemd.c:856`, `CreateSessionWithPIDFD`; `logind-session.c:97-107`); il leader è il figlio che ha chiamato `pam_open_session` e conserva il pid attraverso `execve`: nulla da portare. Valido con logind ≥ 258 (Ubuntu 26.04 nasce con 259.9). Resta vero: `pam_end()` senza `pam_close_session()`.
- Passo 6 (righe 290-293): l'ambiente non è più fisso: `PATH` viene da `pam_env` (`/etc/environment` di Ubuntu: `/snap/bin`, sbin, giochi), accettato solo se lista di cartelle assolute senza `..`, caratteri semplici, ≤ 400 (`child_path_ok()`, buffer `e_path[512]`); il valore fisso `/usr/local/bin:/usr/bin:/bin` è solo il ripiego.
- Paragrafo dopo la tabella (righe 295-301): aggiungere che il figlio può dire «sessione finita» **prima** di smontare lo stage (`session_over_early()`, solo su morte certa `session_life()==DEAD`, mai su KDE `stage_kwin`) e che il genitore tiene il figlio «closing» (`closing_asked_ms`; `CLOSING_GRACE_MS 30000` child.c:216).
- Nuovo: `MSG_STAGE` ha il campo `fatal` in coda (`struct body_stage`, `STAGE_MIN`); solo il rifiuto di scala (guard 2) lo mette a 1 → hook `children_hook_stage_refused()` → `stage_refused_by_child()` in `main.c` → 0x0E ai client (`wt_dismiss_user_session_over`) e chiusura della sessione.
- Riga 311-314 tip «Why exec»: vale; riga 306: «fresh image»: vale. Passi 1-3, 5 (usermod, `close_range`, `setgid/setuid`): non toccati.
- Passo 2 «On GNOME and KDE… render_grant_add()»: codice non toccato; effetto su Ubuntu a runtime non verificato.

### 8. The channel between the network side and a child — VALE COM'È (con una nota per ch22)
Verifica: `struct head`, `MAX_PIECE 32768` (child.c:170), `CHILD_VERSION`, kind: nessun nuovo `MSG_*` nel diff. Il corpo di `MSG_STAGE` però è cresciuto (`fatal`, vedi sez. 7): da riportare nell'Appendice A (ch22).

### 9. The logind sentinel — DA CORREGGERE
- Riga «Is power-off really forbidden?» (349-350): «must all say no» → **`no` oppure `na`** («not available here»: VM, server) per tutte e quattro (`CanPowerOff/Reboot/Suspend/Hibernate`); un errore resta «non sicuro» e il dettaglio nomina chiamata ed errore: `ACTIONS[i]=(ERROR: …)`, pezzo da 192 byte, `detail` 384 byte in `child.c` (`sentinel.c`, `sentinel.h`).
- Resto (`sentinel_local3`, `FAIL_CLOSED_WAIT_MS`, ecc.): `sentinel.c` non cambia altro; non ricontrollati i numeri riga per riga.

### 10. Event loops and threads — VALE COM'È
Verifica: tabelle senza nuovi thread con nome; `kwin.c` aggiunge solo un mutex (`pixel_lock`) e il sidecar ScreenSaver è un processo forkato dal ruolo `--kwin-nested`, non un thread del figlio. Il figlio apre il bus utente (GDBus worker) per due LETTURE in `session_dconf_prepare()`: da citare in nota se si vuole, non falsifica la tabella.

### 11. Where state lives, owner by owner — DA CORREGGERE
- Aggiungere righe: database dconf di sistema `/etc/dconf/db/remotix` (postinst + `session_dconf_system_db_ensure`, root, rimosso a `remove|purge`); profilo di runtime `$XDG_RUNTIME_DIR/dconf/profile` (primo rigo `# REMOTIX-RUNTIME-PROFILE`; rimosso o riscritto a fine sessione); `~/.config/dconf/remotix` (tre chiavi tastiera, scritto dal servizio dconf, tolto a `purge`); in ripiego `$XDG_RUNTIME_DIR/remotix/dconf/profile` + `shm/remotix`.
- «Presence table», «found again», cap 10: invariati; `stage_count()` e `RCP_SESSION_CAP` verificati.

---
## ch03_lifecycle — «Startup and life cycle» (489 righe, 11 sezioni)

### 1. Service startup, step by step — DA CORREGGERE
- Riga 12-14: l'elenco root side manca del compilare il database dconf (`session_dconf_system_db_ensure()` all'inizio di `rootside_main`).
- Passo «The desktop» (righe 22-24): `session_desktop_explain()` dice ora anche «labwc is NOT there, and XFCE/LXQt cannot start» (`session.c:583,601`); `kwin_check_permission()` e `debian/org.kde.remotix.desktop`: vale.
- Riga 69 s.: il resto (NET 78, READY_WAIT, ban, tabelle, hook) non è toccato dal diff.

### 1B. The card that arrives late — VALE COM'È
Verifica: `codec_retry()` (rootside.c), `child_video_*` non nel diff. L'ultima frase (preinst rifiuta installazione senza render node) vale: `debian/remotix.preinst` non cambia.

### 2. The systemd unit and its life-cycle settings — VALE COM'È
Verifica: `debian/remotix.service` non cambia nel diff; `debian/rules:122` `dh_installsystemd --no-enable --no-start --restart-after-upgrade`; `LimitRTPRIO 20`, `LimitNICE -11`, `Restart=on-failure`, `RestartSec=2`, `RestartPreventExitStatus=78`, `KillMode=mixed` letti nel file. Il `warn` finale è impreciso (anche su Debian): la parola «engine» sta in `debian/remotix.conf:7`, `remotix-no-suspend.conf:6`, `remotix.tmpfiles:3`, non in testa all'unit; `--without split` è invece in `remotix.service:6`; il commento KillMode «desktops survive» c'è ancora (`:40`). Il `prerm` ha perso solo «and holds its fifo» (commento).

### 3. From password to admission — DA CORREGGERE
- Passo «Admission» (righe 133-137): ordine reale in `delivery_verdict()` (`main.c` ~1120-1200): sessione locale/logind muto (0x05 / 0x0E) → desktop precedente ancora in chiusura (0x0E) → **compositore non installato** (`session_missing_component()`: XFCE/LXQt senza `labwc`, 0x0E con frase «the desktop (X) cannot start: `labwc` is not installed on this server», nessun figlio creato; solo su Ubuntu/qualsiasi distro con `--no-install-recommends`) → stage tutti usati → budget → nascita. Il commento in `main.c` ora parla di «three 0x0E».
- Nota: il 0x10 dato a chi è dentro e il rifiuto dato a chi ancora aspetta PAM non sono più lo stesso invio: `wt_dismiss_user_session_over()` (`webtransport.c`) distingue connessioni loggate (farewell subito), ADMITTED ma ancora nel secondo fisso (`rcp_admitted_waiting()`, farewell trattenuto, parte al posto di ADMITTED), in attesa PAM (saltate).
- Resto (CAP_HELLO 5000, CAP_CREDENTIALS 60000, CAP_ATTACH 10000, FIXED_DELAY, REJECT_FLOOR, VERDICT_CAP, SPAWN_WAIT_MS 15000 child.c:2683, canvas 320×240-4096×2304, grant 30 s): `rcp.c`/`child.c` non toccano; `SPAWN_WAIT_MS` verificato.

### 4. Birth of a graphical session — DA CORREGGERE
- Righe 188-193 «The logind session»: «carries the session's reference fifo across the execve()»: **falso** (vedi ch02 §7): sessione legata al pidfd del leader, nessun descriptor attraversa `execve`.
- Righe 194-196 `note` «GNOME 48»: «On Debian 13 the unit file… `org.gnome.Shell@wayland.service` (`SESSION_UNIT_SHELL_48`)»: da riscrivere per GNOME 50 / Ubuntu: `SESSION_UNIT_SHELL_48` non esiste più; c'è `SESSION_UNIT_SHELL_MODEL "org.gnome.Shell@.service"` (template, `ExecStart=gnome-shell --mode=%i`); l'istanza la sceglie la sessione di gnome-session (`ubuntu` → `@ubuntu`, `gnome` → `@user`); `unit_shell()` la legge da `Requires` di `gnome-session@<sessione>.target`; il drop-in va nella cartella dell'**istanza**, mai in quella del template (`org.gnome.Shell@.service.d/` varrebbe anche per la Shell di GDM). Verificato: `session.c:3759-3793`, `session.h` diff. Resta I7 (drop-in riscritto a ogni nascita e verificato).
- Passo «The desktop» (righe 172-178): aggiungere la scelta della sessione GNOME (D8): `ubuntu` se è l'unica o porta il nome della distribuzione (`ID` di os-release), altrimenti `gnome` (`session.c:775-990`); `XDG_CURRENT_DESKTOP=ubuntu:GNOME`; PATH da `pam_env`; guardia nuova: GNOME 50 rifiuta di avviarsi se `graphical-session.target` è ancora attivo (`inactive_unit()`, `SESSION_UNIT_GRAPHICAL`), quindi una nascita troppo vicina alla fine della sessione precedente «aspetta» o è rifiutata. «`startplasma-wayland`»: la riga di KDE è `remotix --kwin-nested W H nodo -- kwin_wayland_wrapper --xwayland --width W --height H --no-lockscreen` (`session.c:3895-3935`).
- «On Ubuntu» XFCE/LXQt: `xfce4-session`/`lxqt-session` su labwc **di distribuzione** (pacchetto `labwc` solo Recommends; postinst avvisa se manca); KDE usa il labwc **nostro**. Nuove cure dei desktop (picom/compton/xcompmgr non avviati su LXQt, `blueman.desktop` fuori dall'autostart remoto, integrità pannello XFCE): materia di ch12, solo rimando.
- Retries/costanti (`STAGE_BIRTH_RETRY_MS 200` :5566, `BIRTH_REIN_MS 12000` :5533, `STAGE_RETRY_MIN/MAX 1000/30000` :5509-5510, `CANVAS_WAIT_MS 1200` :5729, `WAIT_STARTUP_MS 40000` session.c:68, `SHOW_UP_DEADLINE_MS 15000` :149): verificate, valgono.

### 5. Detach and reattach — VALE COM'È
Verifica: `rcp.c` (SILENCE 30000, DEFAULT_EVICTION = SILENCE/2, DEFAULT_INACTIVITY) e `webtransport.h` (`WT_LM_*`) non cambiano nelle costanti; `prove/check-lifecycle.py` non nel diff funzionale.

### 6. Desktops found again after a restart — DA CORREGGERE
- Riga 239-241: «(it is “closing” as soon as the child that held the session's fifo is gone…)»: su Ubuntu il leader è il pidfd del figlio, non un fifo; riformulare («as soon as the leader, the child, is gone»). Il resto (`rediscover.*`, `LX_EVERY_MS 5000` rootside.c:1767, `MAX_FOUND_AGAIN 256`) non cambia (`rediscover.*` non nel diff).

### 7. The clocks, each one cited from its constant — DA CORREGGERE
- Valori verificati identici: SILENCE, DEFAULT_EVICTION, DEFAULT_INACTIVITY, DEFAULT_ABANDON_MS, SHOW_UP 15 s, WHOAMI 600 s, RECHECK 60 s, CLOSING_GRACE 30 s, CLOSE_ONLY_LIFE 30 s, WAIT_STARTUP 40 s, NET_RESTART_CAP 30 s, KIDS_EOF_GRACE 5 s, STOP_WAIT 25 s, STOP_CLOSE_WAIT 15 s, PL_GRACE 13 s, PL_CEIL 20 s, PL_HOLD 10 s.
- Righe/clock nuovi da aggiungere: `KDE_LOGOUT_GRACE_MS 4000`, `KDE_LOGOUT_RETRY_MS 3000`, `KDE_LOGOUT_TRIES 10` (10 tentativi `fail` poi 10 `replace`, ~1 min, poi chiusura «forzata» del prodotto: `session_kde_logout_watch()` ora restituisce `bool`; `session.c:5170-5174`); `EIS_UNKNOWN_ROUNDS 3` (canale input chiuso + vita «non so»: riprova dopo 1 s, `child.c`); riprova della chiusura per scala ogni 10 s (`scale_close_ms`, `child.c`); `WAIT_EXIT_MS 10000` (session.c:108) già in S8.

### 8. Ending a graphical session — DA CORREGGERE
- Figura EXIT (riga 350) «logind closes the session when the child's fifo closes»: ora «quando il leader (il figlio) esce / il suo pidfd scatta» (`child.c`, commento «the leader's pidfd fires and logind closes the session»).
- Riga 359-361 Log Out: la sequenza è cambiata (19 nov, `[M]` Ubuntu 26.04): il figlio manda `MSG_SESSION_FINISHED` **prima** di smontare lo stage (`session_over_early()`), perché lo smontaggio può aspettare fino a 25 s (`pw_stream_destroy`, RealtimeKit non avviabile in container/macchine «hardened»: la pagina restava 17 s sull'ultima immagine). Solo su morte **certa** (`session_life()==DEAD`: il bus ha risposto e il nome del compositore non ha proprietario); «non so» ≠ morte (3 round da 1 s). **KDE esce**: nessun farewell anticipato (`stage_kwin`), «waits for a proof on a live machine». Il genitore intanto conta il figlio come «closing» (login nel frattempo → 0x0E vero, mai desktop che sta morendo). Il rientro di un login nei 8-10 s non riceve più un falso 0x10 (`wt_dismiss_user_session_over`).
- Riga «The user has a local session» (366-367) e §«light close» (380-384): il messaggio `local_found` al genitore ora parte **prima** della chiusura leggera (`child.c`, `main.c: local_found_by_child`). Vale il resto: dconf neutralizzato, nessun Logout.
- Righe nuove: «Il rifiuto dello stage per la scala»: se la scala dell'utente ≠ 1 su Mutter, un solo tentativo temporaneo di riportare il nostro monitor a 1 (`mutter_scale_to_one()`); se fallisce → 0x0E ai client + chiusura della sessione per la strada del Logout (guard locale prima), riprovata ogni 10 s; nessun processo resta (`child.c`). Causa a monte: `scaling-factor` bloccato a 1 nelle regole dconf (`session.c`).
- Riga «close itself» (373-379): `WAIT_EXIT_MS` 10 s, GNOME `Logout(1)` poi `Logout(2)`, XFCE `org.xfce.Session.Manager.Logout`, LXQt `org.lxqt.session.logout`: verificati (`session.c:4420,4636,4687`). Plasma: oltre a `org.kde.Shutdown.logout` + stop forzato, c'è il **soccorso `session_kde_logout_watch()`** (Kubuntu, Plasma 6.6: `plasma-shutdown` si perde se un servizio sta ancora avviandosi; ripete `StopUnit graphical-session.target` fail→replace; a esaurimento il figlio chiude con la strada del prodotto: log «closing the graphical session by force»; REGISTRO D).
- Riga 394-395: «on KDE a Log Out succeeds even if systemd refuses the stop (session.c)»: vale e va dettagliato come sopra.
- Riga 385-388 (TERMINATE_SESSION senza trigger) e 389-395 (prove): `page.html` cambia solo un commento (sei vie per 0x0E): vale; le prove: i numeri di giro sono quelli di Ubuntu (ch01 §2).

### 9. Stopping the service — DA CORREGGERE
- Procedura e costanti: vale (nessun diff funzionale su `main.c` per STOP, `rootside.c`).
- `tip` finale (righe 442-445): aggiungere che su Ubuntu il pacchetto ora installa `/etc/needrestart/conf.d/remotix.conf` (`$nrconf{override_rc}{qr(^remotix\.service$)} = 0`): `needrestart`/unattended-upgrades non riavviano più il servizio da soli dopo un aggiornamento di libc/openssl/pam (chiuderebbe i desktop); resta «da riavviare a mano».

### 10. The log line that marks each step — VALE COM'È
Verifica: 19 stringhe campione cercate in `src/*.c` (ROOT SIDE on, network side started, walls in force, THIS SERVER CANNOT ENCODE VIDEO, the three clocks in force, ADMINISTRATIVE session cap, FOUND AGAIN the desktop of, AUTH refused BEFORE PAM, NO STAGE at birth, DETACHED for silence, COMES BACK to their desktop, §7.6 «WAS THERE and now is NO LONGER» (spezzata su due righe), ABANDONMENT, farewell 0x0c sent, stopping:, local login of, STILL there after 20 s, ready: https, light close): tutte presenti. Nuove righe da aggiungere in (a).

---
## ch04_transport — «Transport» (571 righe, 14 sezioni)

Diff che tocca l'area: solo `webtransport.c/.h` (+36/+5, `wt_dismiss_user_session_over`). `transport.c`, `cid.*`, `pktinfo.h`, `hsrate.h`, `resetcap.h`, `tls.c`, `certificates.c`, `page.c`, `build/quic-static.sh` NON nel diff.

### 1. The transport stack and the network side — DA CORREGGERE
- Nota «Libraries»: «`debian/control` records them in Static-Built-Using» ora registra anche `labwc (= 0.9.3)` e `wlroots (= 0.19.2)` (diff `debian/control`). «OpenSSL… libssl-dev 3.5 or later»: vale, Ubuntu 26.04 ha 3.5.5-1ubuntu3.7 (`studio/8-pacchetto-e-prove.md:48`); ngtcp2 v1.25.0 / nghttp3 v1.18.0 statici: vale, e su Ubuntu servono perché quelle di sistema sono 1.16/1.12.
- Resto: vale.

### 2. SETTINGS rewrite — VALE COM'È   (`webtransport.c` non cambia `rewrite_settings`; nessun diff in quell'area)
### 3. Listeners, sockets and port 7447 — DA CORREGGERE
- `warn` firewall (righe 114-120): su Ubuntu `ufw` è in `ubuntu-standard` come Recommends e **spento di serie** (`ENABLED=no`, `studio/5-sistema-ubuntu.md:26,164-165`); il profilo `debian/remotix.ufw` (7447/tcp|udp) viene visto da `ufw app list` (misurato, `[V]`). Resta: nulla apre il firewall. La frase «a comment in debian/rules that says an engine does it is stale» non è verificabile: `grep -i engine debian/rules` non trova nulla (neanche su `main`); non verificato dove stia quel commento.
- Resto (porta 7447, `SO_REUSEADDR`, indirizzo 0.0.0.0, IPv6 non esercitato): vale (`debian/remotix.service` invariato).
### 4. QUIC transport parameters — VALE COM'È   (`transport.c` non nel diff)
### 5. Admission of new connections, Retry and Stateless Reset — VALE COM'È   (`transport.c`, `cid.*`, `hsrate.h`, `resetcap.h` non nel diff)
### 6. TLS contexts and the two certificates — VALE COM'È   (`tls.c`, `certificates.c` non nel diff; ML-KEM `X25519MLKEM768` con OpenSSL 3.5.5: non verificato su Ubuntu a runtime, ma il codice ha il ripiego loggato)
### 7. Certificate pinning and the fingerprint endpoint — VALE COM'È   (`page.c`, `page.html` non toccano pinning; diff page.html = un commento)
### 8. The page server on TCP — VALE COM'È   (`page.c` non nel diff)
### 9. The WebTransport layer — VALE COM'È   (il diff di `webtransport.c` aggiunge solo `wt_dismiss_user_session_over()`: nuova funzione, non cambia tabella WIRE né capsule)
### 10. Streams, datagrams and the send queue — VALE COM'È   (nessun diff nei WT_*)
### 11. Idle timeout, keep-alive PINGs and the dead line — VALE COM'È   (nessun diff)
### 12. Congestion, pacing and the video queue — VALE COM'È   (nessun diff)
### 13. One connection from first packet to close — VALE COM'È   (nessun diff; aggiungere solo che i farewell di fine sessione passano da `wt_dismiss_user_session_over`, cfr. ch05)
### 14. What was verified for the transport — DA RISCRIVERE
Motivo: righe 545-554 sono verifiche Debian: «PIANO.md: 34 checks per desktop… run “pulizia1b”… 104 to 112 of 118», «`check-package.py` on the four test containers and a real Debian 13 VM», «AppArmor profile in a session on a machine with a graphics card». Su Ubuntu: giri `unione1/unione2` (18 nov, 124/128 righe) e `unione10` su VM con Radeon (19 nov); AppArmor osservato in sessione su macchina vera (C4); `check-package.py` non fa parte di `all.sh` sulle VM (SKIP «needs box.sh reset») e `package-snap.py` ha elenco snap/cloud-init nuovo. Restano veri: nessun controllo inonda il server, nessuna rotazione di certificato, IPv6 non esercitato (`prove/` non cambia in quei punti). Il giro sulle VM usa `RX_TEMPO=2` (scadenze ×2) e indirizzo 10.0.2.2 per il ban (`check-ban.py`): lo dice la sezione.

---
## ch05_rcp — «The RCP/1 protocol» (404 righe, 14 sezioni)

Diff che tocca l'area: `rcp.c` +8 (`rcp_admitted_waiting()`, stato `S_WAIT_VERDICT && !expected_verdict && cred_good && !held_farewell`), `rcp.h` +2 (prototipo). `docs/RCP.md`, `msgrate.h` e `page.html` (solo commento) non cambiano.

### 1. RCP/1 in one page — VALE COM'È   (grep: «twenty-nine» hook; `rcp.h` aggiunge solo un prototipo, nessun puntatore a funzione in `rcp_hooks`)
### 2. Message map — VALE COM'È   (nessun nuovo tipo di messaggio; `drain_at()` non cambia nel diff)
### 3. Framing and the rigor rule — VALE COM'È   (nessun diff su `accumulate`/`drain_at`/`dismiss`)
### 4. The handshake step by step — VALE COM'È   (costanti CAP_* e stati invariati)
### 5. HELLO, HERE_I_AM — VALE COM'È   (nessun diff)
### 6. CREDENTIALS, the verdict and the fixed second — DA CORREGGERE
- Passo «The answer» (righe 192-194): «A refusal the host decides after a PAM yes (the budget, a local session, the desktop that cannot start) is kept by `rcp_dismiss_login()`…»: vale e si estende: la nuova ragione 0x0E «compositore non installato» (main.c `delivery_verdict()`) passa da qui; in più `rcp_admitted_waiting()` permette di mandare il 0x10/0x0E trattenuto a chi è già ADMITTED ma ancora nel secondo fisso.
- Resto (limiti 5/20/30, LADDER 15 min/1 h/12 h, MAX_ATTEMPTS 256, BAN_QUOTA 160, FIXED_DELAY 1000, REJECT_FLOOR 2500): `rcp.c` non cambia quelle costanti.
### 7. ATTACH and SESSION — VALE COM'È   (nessun diff; canvas 4096×2304 e 320×240 verificati in `rcp.h:1069-1071`)
### 8. Key frames, canvas, view and layout — VALE COM'È
### 9. Input, clipboard and cursor — VALE COM'È   (`input.c` cambia solo `input_dropped()`/commenti dconf, non RCP)
### 10. Rate limits on a connected client — VALE COM'È   (`msgrate.h` non nel diff)
### 11. Clocks of an attached session — VALE COM'È
### 12. FAREWELL, REJECTED and the sixteen reasons — DA CORREGGERE
- Riga 0x0E `SESSION_UNSERVABLE` (337): elenco incompleto. Oggi anche: «compositore non installato» (`delivery_verdict`, 18 nov), «stage rifiutato per la scala» (`stage_refused_by_child`, 19 nov), «ancora in chiusura» (già c'era). La pagina li tratta come generici (`page.html` REASON_TEXT: ora «SIX different routes», prima FIVE).
- Riga 0x10 `SESSION_TERMINATED` (339) «main.c, drain_at()» e frase «The same code is sent to the other clients… (main.c)»: oggi `main.c` lo manda con `wt_dismiss_user_session_over()` (non `wt_dismiss_user()`) in `session_ended_by_child()` e `dismiss_child()`; connessioni ancora in attesa PAM o già rifiutate non lo ricevono. Riga 0x03 via `wt_dismiss_user()`: invariata.
- Riga 0x04 (327) «`main.c`, `wt_watch_locals()`»: il messaggio `local_found` arriva ora PRIMA della chiusura leggera (stessa 0x04).
### 13. Where the code departs from RCP.md — VALE COM'È
Verifica: `RCP.md` e `SPECS.md` non cambiano (diff); tabella: `REJECT_FLOOR`, hook, «PACE off by default», range 0x01-0x0F, PINGs: codice non toccato.
### 14. What was verified about RCP — DA RISCRIVERE
Motivo: righe 376-384 attribuiscono i controlli al «17 November 2026 on the four desktops (PIANO.md)» (Debian). Su Ubuntu i controlli `check-base/lifecycle/multiuser/resilience/ban/input/clipboard` sono quelli dei giri `unione1/2` (18 nov) e `unione10` (19 nov, VM); la tabella «Not verified» resta valida (nessun fuzz, nessun controllo forgia byte). Non stabilito se un controllo provochi 0x04/0x05: ora `prelocal` ci riesce (REGISTRO A, prove prelocal su Ubuntu/Kubuntu a mano); da verificare nel codice di `check-prelocal.py`.

---
# Conteggio (56 sezioni)
- ch01: vale 0 / correggere 4 (§1, §3, §4, §5) / riscrivere 1 (§2).
- ch02: vale 5 (§2, §5, §6, §8, §10) / correggere 6 (§1, §3, §4, §7, §9, §11) / riscrivere 0.
- ch03: vale 4 (§1B, §2, §5, §10) / correggere 7 (§1, §3, §4, §6, §7, §8, §9) / riscrivere 0.
- ch04: vale 11 / correggere 2 (§1, §3) / riscrivere 1 (§14).
- ch05: vale 12 / correggere 2 (§6, §12) / riscrivere 1 (§14).
- Totale: **vale 32, da correggere 21, da riscrivere 3**.

---
## (a) COSE NUOVE di Ubuntu che il gruppo deve contenere e oggi mancano
1. **Modello dconf di GNOME 50** (profilo di runtime `$XDG_RUNTIME_DIR/dconf/profile`, database di sistema `/etc/dconf/db/remotix` compilato dal postinst da keyfile generati in build con `remotix --dconf-keyfiles`, database utente `~/.config/dconf/remotix`, ripiego dichiarato di 1.0.0, motivo = snap/Flutter, REGISTRO C5). Dove: ch02 §1 (ruolo `--dconf-keyfiles`), ch02 §3 (passo di avvio), ch02 §11 (stato), ch03 §4 (birth) — il dettaglio vero in ch12/ch15.
2. **Sessione di Ubuntu = pidfd del leader** (niente `--session-fd`; systemd 259.9): ch02 §7, ch03 §4/§6/§8 (sostituire ogni «fifo»). Aggiungere frase sul requisito logind ≥ 258.
3. **GNOME 50**: template `org.gnome.Shell@.service`, sessione `ubuntu` vs `gnome` (D8), guardia `graphical-session.target`, `XDG_CURRENT_DESKTOP=ubuntu:GNOME`: ch03 §4 (sostituire la nota «GNOME 48»).
4. **Our labwc** (`/usr/libexec/remotix/labwc`, 0.9.3 + wlroots 0.19.2 patchato, statico, GPL-2/MIT, sorgente pubblicato): ch01 §1 (tabella) e §3 (vocabolario), ch01 §4 (build/labwc-ospite), ch02 §1; dettaglio in ch12/ch18/ch15.
5. **Compositore mancante → 0x0E** prima di creare il figlio (`session_missing_component`, avviso del postinst): ch03 §3 e ch05 §12.
6. **Fine sessione sicura rispetto a RealtimeKit**: farewell anticipato (`session_over_early`), `session_life` a tre valori, `finished_told`, `wt_dismiss_user_session_over`, stage rifiutato per la scala con `fatal`: ch03 §8 (nuova sezione consigliata «When the session ends before the stage is gone») e ch05 §12.
7. **KDE**: soccorso del logout (`session_kde_logout_watch`), sidecar ScreenSaver, `capture_watch_sequence`/`kwin_poke` (frame perso): ch03 §8 e riferimenti a ch06/ch12.
8. **`sentinel_shutdown_forbidden` con `na`**: ch02 §9, ch01 invariante I7.
9. **AppArmor su kernel Ubuntu**: righe `deny unix`, percorsi XKB `xkeyboard-config-2`, include `local/`: ch02 §4 (sostituire il warn), ch01 §2.
10. **needrestart**: ch03 §9 tip; **PATH da pam_env**: ch02 §7.
11. **Banco di prova e verifiche Ubuntu** (VM QEMU con Radeon, `RX_BANCO=vm`, `RX_TEMPO`, `--only`, `--clean`, giri unione1/2/10, C4/C5, E3/E4): ch01 §2 (nuova tabella) e ch04 §14, ch05 §14.
12. Nuove righe di log da citare in ch03 §10: «D8: the GNOME session is «…»», «DECLARED FALLBACK, D-015 (19 Nov 2026)», «the desktop cannot be born: … needs `labwc`», «⭐ 19 Nov 2026: the graphical session … is over, CERTAINLY», «Plasma logout stopped halfway…», «the stage was refused for the scale».

## (b) Cose di Debian da TOGLIERE
- ch01: «Debian 13 (trixie)» (riga 25-26, 71, 87), «The Debian 13 machine» (FIG riga 8, 18), `debian:trixie` (56, 190), «real Debian 13 virtual machine» (71, 87), `REMOTIX-DEBIAN/` (167), CLAUDE.md «Debian 13 only» (200-202), cifre 111/118, 112/118, 111/118, 104/118 (riga 76-77), Samsung DeX (80), «Debian does not ship the versions needed» (190-192).
- ch02: warn AppArmor «real Debian 13 VM» (188-192), passo 4 con `--session-fd`/fifo (283-287), `e_path` fisso (290).
- ch03: nota «GNOME 48… `org.gnome.Shell@wayland.service` `SESSION_UNIT_SHELL_48`» (194-196), «reference fifo» (188-190), figura EXIT «child's fifo closes» (350), criterio found again «held the session's fifo» (239-240).
- ch04: righe 545 («PIANO.md: 34 checks… 104 to 112 of 118… “pulizia1b”»), 550 («four test containers and a real Debian 13 VM»); frase «an engine does it» in rules (118-119, non verificata).
- ch05: righe 376-377 («17 November 2026 on the four desktops»).
- Nessuna occorrenza di «GNOME 48», «dconf 0.40», «trixie» nei capitoli 04 e 05 oltre a quelle elencate (grep).

## (c) rif() verso altri gruppi e convenzioni di stile
Titoli citati e presenti altrove (verificati con grep sui `CHAPTER`): «The local-login hold» (ch13), «Security model» (ch14), «Login and its defences» (ch13), «Screen capture» (ch06), «Quality, degradation and budget» (ch08), «The four desktops» (ch12), «Local excludes remote and the session cap» (ch14), «Logging and diagnostics» (ch16), «The package» (ch15), «Build and release» (ch18), «Conventions» (ch21), «Testing» (ch17), «Input» (ch10), «Audio and clipboard» (ch11), «Appendix A — Data structures and messages» (ch22), «Appendix C — Known issues and open points» (ch24). Se un altro gruppo rinomina una di queste sezioni (per es. «The four desktops» per i sapori Ubuntu) i rif() di ch01-ch05 vanno aggiornati: `build.py` li risolve per titolo esatto.
Convenzioni osservate: `CHAPTER = (titolo, [(titolo sezione, html), ...])`; blocchi `p(…, lead=True)`, `table(head, rows, "«TAB» — …")`, `fig("«FIG» — …")`, `note(testo, "titolo breve")`, `warn(…)`, `tip(…)`, `steps([…])`, `seq`, `flow`; `c()` per identificatori, `sysf()` per file di sistema, `rif()` per rimandi; frasi in inglese tecnico, tono asciutto con date (`17 Nov 2026`), riferimenti a `DECISIONS §n`, nome della funzione e costante con il file; le sezioni dichiarano sempre «verified / not verified»; le didascalie iniziano con ««TAB» — » e ««FIG» — ». Le sezioni nuove di Ubuntu dovrebbero citare registro (`REGISTRO C4/C5/D/E`) e data, e dire «not verified» dove il registro lo dice.
Altri elementi da decidere (non miei): se i capitoli `technical-debian13` restano nel ramo (conta doppio in «Manual sources»); `local_login.c:20` cita ancora «systemd 257» (commento stantio); `CLAUDE.md` del ramo ancora «Debian 13 only».


---------------------------------------------------------------------------------------------------

<!-- ===== frammento g2 ===== -->
# Inventario gruppo 2 — ch06 cattura, ch07 codifica, ch08 qualità, ch09 pagina, ch10 input, ch11 audio e appunti

Metodo: ho letto per intero i sei capitoli (testo estratto dai `.py`), `src.diff`, `pacchetto.diff`, `prove.diff`, `docs.diff`, `studio/4`, `6`, `7`, `8`, `10`, `11-riscontro`, `giro1/giro2-*`, `docs/REGISTRO-problemi.md`, `PIANO.md`, e ho ricontrollato nel ramo con `grep` le costanti citate (WAIT_NODE_MS, HOST_MHZ, TICKER_MS, WLR_SLABS, WLR_SLAB_W/H, PROBE_TAIL_US, CAPTURE_DAMAGE_MAX, PIXEL_SCAN_EVERY_MS, MOTION_FPS, WAKEUP_MS, QP_HARDWARE, ENC_RETRY_*, SHAPE_COUNT, CURSOR_MAX_SIDE, UC_*, WHEEL_MAX_UNITS, RCP_CLIPBOARD_CAP, CLIPBOARD_PER_SECOND, MIME_MAX_TYPES, WAIT_TRANSFER_MS, AUDIO_RING_FRAMES): TUTTE uguali a Debian. `src.diff` NON tocca: encoder.c, vadirect.c, vulkanvideo.c, card_pick.c, render_*.c, budget.c, hsrate/msgrate/linebudget/dimcheck, unchanged.h, wlroots.c, wlr_input.c, cursor.c, shape.c, clipboard.c, clipboard_kde.c, sound.c, audio.c, keyboard.c, page.c, opus-wasm/. `page.html` cambia di 3 righe di commento (sei strade dello 0x0E invece di cinque). `webtransport.c` aggiunge solo `wt_dismiss_user_session_over()`.

Cambi di codice di questo ramo che toccano la mia area (tutti in `src.diff`):
- `capture.c/.h`: nuova cura del «fotogramma perso» di KWin (`capture_watch_sequence()`, `capture_frame_lost()`, LOST_QUIET_MS 200, LOST_POKES_MAX 10, SEQ_WINDOW 600).
- `kwin.c/.h`: `kwin_poke()`; labwc ospite = NOSTRO (`REMOTIX_LABWC` = `/usr/libexec/remotix/labwc`, `Makefile` r.128-133), non più quello della distribuzione in `PATH`; sidecar `org.freedesktop.ScreenSaver`.
- `mutter.c/.h`: `mutter_scale_to_one()`; `child.c`: la scala utente diversa da 1 si prova a riportare a 1, altrimenti 0x0E e sessione chiusa (`p.fatal`, `scale_refused`).
- `input.c/.h`: `input_dropped()` risponde anche per wlroots; dconf di sessione = user-db `remotix` (shm solo nel ripiego).
- `child.c`: `session_over_early()` (congedo prima dello smontaggio); `main.c`: 0x0E «compositor non installato» (`session_missing_component()`), `stage_refused_by_child()`.
- `session.c`: chiave `org.gnome.desktop.interface scaling-factor` = 1 bloccata nel dconf di sessione (r.1740); `debian/`: labwc proprio nel `.deb`, postinst che compila `/etc/dconf/db/remotix`.
- `prove/`: banco = macchine virtuali QEMU (`RX_BANCO=vm`), non più contenitori; righe rinominate `page-cad-hidden`, `page-ctrl-alt-end-passes`; `window-input.py` legge il rilascio dagli eventi grezzi (GTK 4.22).

Versioni Ubuntu 26.04 da usare (studio 4 §1, studio 6/7/8, giro1/2): mutter/gnome-shell 50.1, libei/libeis 1.5.0-3, libpipewire/pipewire 1.6.2, wireplumber 0.5.13, libva 2.23, Mesa 26.0.8 (`mesa-libgallium` porta i driver VA; `va-driver-all` è in universe e tira solo Intel), libvulkan-dev 1.4.341, libopus 1.6.1 (studio 4 §1), kwin-wayland/Plasma 6.6.7, labwc 0.9.3-1 e wlr-randr 0.4.1 (universe), xfce4-session 4.20.4 (`libxfce4windowing` 4.20.5 nel box), lxqt 2.3.0, GTK 4.22, systemd 259, dconf 0.49. Browser dei giri: Chrome 156.0.8078.79, Firefox 153.7.0 (giro2-kde) / 160 (studio 10).

---

## ch06_capture.py — «Screen capture» — 572 righe — 11 sezioni

**S0 Capture at a glance: one contract, three compositor families — DA CORREGGERE**
- «On Debian 13 there are three compositor families behind the four desktops»: va detto Ubuntu 26.04 (Ubuntu/GNOME, Kubuntu/KDE, Xubuntu/XFCE, Lubuntu/LXQt).
- NOTE «labwc is a Recommends of the package… KDE still starts with KWin in its --virtual mode… labwc is optional for KDE only»: FALSO su Ubuntu. Il KDE usa il labwc PROPRIO del pacchetto (`kwin.c` `REMOTIX_LABWC`, `debian/rules` r.22-61, `Static-Built-Using: labwc 0.9.3, wlroots 0.19.2`); `labwc` (universe, Recommends) serve solo a XFCE e LXQt. Senza il labwc proprio il KDE ripiega su `--virtual` (dichiarato, K4 verificato).
- Tabella, cella GNOME: la riga di comando reale è `gnome-shell --headless --no-x11 --mode=ubuntu` (giro1-gnome G2, /proc/cmdline); con la modalità `ubuntu` la sessione è quella Ubuntu (dock, Yaru).
- Nuova riga della famiglia KDE: «Compositor ospite = labwc 0.9.3 + wlroots 0.19.2 con patch, statico» (non quello della distribuzione).
- XFCE/LXQt senza `labwc` installato: oggi il server rifiuta l'accesso con 0x0E prima di far nascere il figlio (`main.c:1173`, `session_missing_component()` `session.c:764`, solo XFCE/LXQt).

**S1 The capture contract — VALE COM'È**
Controlli: `capture.h` contratto invariato (diff aggiunge solo la sezione «lost frame»); costanti `PIXEL_SCAN_EVERY_MS` 500 e `CAPTURE_DAMAGE_MAX` 16 verificate nel ramo; `dimcheck.h` non nel diff. Nota: la misura del 12 ago (Mutter 48.7, 410 frame) resta storica; su Mutter 50.1 formati e damage non cambiano nel sorgente (studio 4 §2.2 punti 5 e 8), mai rimisurati a mano.

**S2 GNOME: the Mutter D-Bus sequence — DA CORREGGERE**
- WARN «Scale guard»: «the child refuses the stage when it is not 1.0 and logs the one-line cure» è superato. Oggi: (1) la chiave `scaling-factor` è scritta a 1 e BLOCCATA nel dconf di sessione (`session.c:1740`); (2) se la scala letta è ≠ 1 il figlio prova UNA volta `mutter_scale_to_one()` (`child.c` ~9170; `mutter.c`: `GetCurrentState` + `ApplyMonitorsConfig` metodo 1 = temporaneo, modo corrente mantenuto, `layout-mode` solo se `supports-changing-layout-mode`; solo il caso semplice 1 monitor logico = nostro; ~45 s al peggio = 3 chiamate sincrone da `WAIT_CALL_MS` 15 s); (3) se resta ≠ 1: 0x0E ai client (`stage_refused_by_child`, `main.c:2187`), `p.fatal`, sessione chiusa (ritenta ogni 10 s, `child.c` ~10524). La riga di cura `gsettings set … scaling-factor 0` non c'è più. Righe di registro: «⭐ scale back to 1 (temporary, the user's monitors.xml untouched)…», «⭐ the user's scale %.3f is IGNORED in the remote session».
- Tabella dei dettagli: `cursor-mode` 2, `is-platform`, `mapping-id`, `WAIT_CALL_MS` 15000, `WAIT_NODE_MS` 10000 (grep `mutter.c` 41-44) vale. Mutter 50.1: API ScreenCast v4 e RemoteDesktop v1 invariate, prodotto «Virtual remote monitor» invariato (studio 4 §2.1): non nuovo ma da dire «verificato nel sorgente di 50.1».
- «Mutter … `mapping-id` … ignores it»: studio 4 §2.1 conferma anche per 50.

**S3 KDE: the KWin screencast protocol and the nested KWin — DA CORREGGERE** (la sezione con più falsi)
- «The code was written against KWin 6.3.6»: su Ubuntu KWin/Plasma 6.6.7 (kwin-wayland universe). I commenti di `kwin.c` citano 6.3.6 per le misure vecchie e 6.6.6/6.6.7 per quelle Ubuntu (`kwin.c:962`, `:1316`, `capture.c:1036`).
- «The labwc is the one found in PATH; REMOTIX ships none» e «Without labwc. When labwc is not in PATH…»: FALSI. Oggi `labwc_path = access(REMOTIX_LABWC, X_OK) ? … : NULL` (`kwin.c` ~1360-1390, diff): il pacchetto porta `/usr/libexec/remotix/labwc` (labwc 0.9.3 + wlroots 0.19.2 patchato, LINKATO STATICO; `build/labwc-ospite/`: `VERSIONS`, `fetch.sh`, `build.sh`, patch `wlroots-0.19.2-remotix-presented-root.patch`; sha256 del binario nel .deb provato uguale all'installato, giro2-kde K5). Motivo (studio 10, misurato 18 nov): con KWin ≥ 6.5 il labwc della distribuzione risponde a OGNI `wp_presentation_feedback` con `discarded` (0 presented / 755 discarded in 30 s; col nostro 759 / 1), i client ricevono frame callback con tempo 0 e Firefox smette di dipingere (9 intervalli su 11 senza pixel cambiati). Il ripiego `--virtual` esiste ancora; il messaggio dice «our labwc is not installed».
- «NODE … `pixman` when no card…»: invariato; la build statica ha solo il renderer GLES2 + pixman (`build.sh`: `-Dwlroots:renderers=gles2`), K1/K6 mostrano che KWin nasce.
- Tabella «What REMOTIX sets»: aggiungere il sidecar `org.freedesktop.ScreenSaver` (`kwin.c` ~1316-1470): processo a parte (come il ticker) che possiede il nome sul bus dell'utente e risponde «non bloccato» a tutti i metodi (`GetActive` false, `Lock/Throttle/UnThrottle` = `NotSupported`, `Inhibit` inoltrato a powerdevil). Perché: da Plasma 6.4 Ctrl+Alt+Canc non faceva nulla (`GetActive` falliva con ServiceUnknown, letto come «schermo bloccato»); misurato con un sostituto: la schermata di uscita compare in 1 s. Giro2-kde mostrava `page-cad-chain` rosso su KDE; il sidecar è DOPO quel giro: non verificato in un giro completo.
- «Reattach at another size… `kwin_host_settle()` (3 s)… labwc configures KWin's window more than once»: misure di KWin 6.3.6/labwc 0.8.3 (commento `kwin.c:1178`); su Ubuntu giri verdi (`desktop/reattach-windows-inside` PASS in giro2-kde) ma il testo non va attribuito a Ubuntu.
- «Empty damage… KWin 6.6 is recorded… not measured on Debian 13, whose KWin is 6.3.6»: su Ubuntu KWin è 6.6.7. Aggiungere la misura 19 nov (`capture.h`): 68 poke su desktop fermo = 68 frame interi con damage vuoto.
- NUOVO, manca: «il fotogramma perso» (vedi elenco (a)).
- Tabella `unchanged.h`: valori verificati uguali (grep). La frase «KWin can lose a frame's damage» ora ha la spiegazione (lost frame).
- «The cursor… mode 4», `KWIN_FORCE_SW_CURSOR`, gate `.desktop` `/usr/share/applications/org.kde.remotix.desktop`, codici RX-KDE-00x: nessuna modifica nel diff.

**S4 PipeWire negotiation, resize and wake-up — DA CORREGGERE**
- «Mutter 48.7 offers only BGRx and BGRA… Mutter chooses 1280×720»: per Mutter 50.1 il sorgente dà lo stesso (BGRx/BGRA, `DEFAULT_SIZE` 1280×720; studio 4 §2.2 p.5, §2.5), ma il testo cita 48.7: dire 50.1.
- Differenze reali di Mutter 50 da aggiungere (studio 4 §2.2, [V sorgente], effetto verificato solo dai giri): il flusso virtuale ha `must-drive` FALSE (clock passivo, `node.supports-request`=2) — il nostro consumatore non è mai DRIVER, quindi Mutter resta driver come in 48; a ogni `monitors-changed` Mutter 50 ripubblica i formati (una rinegoziazione in più dopo ogni resize); buffer `2..8` (in 48 `2..16`): le nostre richieste (GPU: 6, min 4, max 8 `capture.c:679-680`; memoria 4) restano nel range ma con margine più stretto. Verifica: righe `reattach/canvas-limits` e `media` PASS su GNOME 50.1 (studio 11 S4.1, S4.2).
- NOTE «NVIDIA with GNOME 50»: era Ubuntu 26.04/GNOME 50.1 (giro NVIDIA 6 ott, vecchio albero): l'etichetta «GNOME 50» è già Ubuntu; su Ubuntu non si sa se Intel/Radeon negoziano DMA-BUF/modificatori come NVIDIA (studio 4 §12): non verificato.
- WARN «Wake-up and held buttons… `viewports-changed`/`remove_viewport_devices`» (misura su Mutter 48): sul sorgente 50 `meta-eis-client.c` ha solo pulizie, `drop_device` e `handle_button` invariati (studio 4 §2.3), ma il bench `06-b33` non è nell'albero Ubuntu: la cura NON è rimisurata su 50.
- Aggiungere: lo smontaggio dello stage (`pw_stream_destroy`) può attendere RealtimeKit fino a 25 s dove `rtkit-daemon` è installato ma non parte (`child.c` box «THE SESSION IS OVER IS SAID BEFORE…»).
- Parametri `proposal()`/`consumer_parameters()`, modificatori LINEAR/INVALID, `generation`, retention: `capture.c` invariato fuori dalla nuova cura.

**S5 XFCE and LXQt: wlroots screencopy — VALE COM'È**
Controlli: `wlroots.c`/`wlr_input.c` assenti da `src.diff`; `grep` delle costanti. Riserva: «the labwc they were written against does not expose ext-image-copy-capture-v1» riguarda labwc 0.8.3; Ubuntu ha labwc 0.9.3-1 (wlroots 0.19): se oggi espone `ext-image-copy-capture-v1` NON è verificato (giro1/giro2 XFCE-LXQt verdi con `zwlr_screencopy` che funziona). Versione di labwc: 0.9.3 su Ubuntu (studio 7).

**S6 Slabs: zero copy on labwc — VALE COM'È**
Controlli: `wlroots.c` non nel diff; `WLR_SLABS` 3, `WLR_CARD_FAILED_MAX` 3, `WLR_SLAB_W/H` 4096×2304, `WLR_SLAB_BIRTH_S` 1.0 (grep). Il WARN sulla GPU AMD dice «not re-measured on Debian 13»: su Ubuntu non è mai stato misurato (la Radeon è passata alle VM, `server/vm-radeon*.sh`; percorso di codifica scelto sulla Radeon: non documentato). Togliere il riferimento a Debian.

**S7 Zero copy and the memory fallback — VALE COM'È**
Controlli: `ZERO_COPY` 1, `MOTION_FPS` 60, `MOTION_WAIT_S` 0.008 (grep `child.c`); `encoder.c`, `child.c` nelle parti citate (`remount_only_capture`, `falls_back_if_refused`) non toccate (il diff di `child.c` aggiunge `capture_watch_sequence()` anche in `remount_only_capture`, r.9733).

**S8 The cursor channel — VALE COM'È**
Controlli: `cursor.c`/`cursor.h` non nel diff; `CURSOR_MAX_SIDE` 256. Mutter 50: bitmap sempre RGBA, `format==0` = «nessuna novità» gestito (studio 4 §2.2 p.7); righe `pointer-shape-text/arrow/edge` PASS sui quattro desktop (giro2).

**S9 The encoded cursor theme — DA CORREGGERE** (solo riferimento)
- WARN «It was not examined on Debian 13 in the 17 Nov 2026 round»: su Ubuntu i controlli `pointer-shape-*` passano, ma «never visible by eye» resta non guardato; togliere il riferimento Debian. `SHAPE_COUNT` 78, `SHAPE_SIZE` 24 verificati. Cursori reali: `REAL_THEMES` = Adwaita poi breeze_cursors; sui tre gusti non-GNOME dipende dai temi installati: non verificato quale tema risolve su Xubuntu/Lubuntu (studio 7 §«nomi dei cursori», `shape.c:131-137` cita labwc 0.8.3).

**S10 Capture constants and what was verified — DA CORREGGERE**
- Tabella costanti: valida; AGGIUNGERE `LOST_QUIET_MS` 200 ms, `LOST_POKES_MAX` 10, `SEQ_WINDOW` 600 (`capture.c`), `REMOTIX_LABWC` `/usr/libexec/remotix/labwc` (`Makefile`).
- «What was verified»: tutti i numeri sono Debian (17 nov: XFCE 111/118, LXQt 112/118, KDE 111/118, GNOME 104/118; DeX su GNOME; «on Debian 13»). Ubuntu: unione1 GNOME 116/124, KDE 111/124, XFCE 117/124, LXQt 117/124; unione2 GNOME 123/124, KDE 121/124 (3 FAIL: `page-cad-chain` ×2, `desktop/canvas-limits` non riprodotto), XFCE 126/128, LXQt 124/124; poi il banco passa alle VM (PIANO: GNOME verde tranne `desktop/users-shell-and-environment`; prova a mano del proprietario sulle quattro VM e sulle quattro live vere, 19 nov). Non verificato su Ubuntu: Radeon/Intel con tutta la suite funzionale (studio 11 «SCOPERTA 17»), KWin senza labwc proprio (`--virtual`) oltre K4, 4096×2304 end to end.

---

## ch07_encoding.py — «Video encoding» — 400 righe — 13 sezioni

**S0 Encoding at a glance — VALE COM'È** (diff non tocca encoder/vadirect/vulkanvideo; `debian/control` Recommends invariati per la parte GPU).
**S1 Codecs and their negotiation — VALE COM'È** (rcp.c/encoder.c non toccati; `rootside.c` cambia di una riga non pertinente: `session_dconf_system_db_ensure()`). Giro: `media/codec` PASS, Chrome 156 e Firefox 153.7 negoziano H.264 `avc1.640033` 8 bit sulle macchine di prova (giro2-kde).
**S2 Choosing the GPU route — VALE COM'È** (nessun diff; costanti `ENC_RETRY_MIN_MS` 500, `ENC_RETRY_MAX_MS` 10000 verificate).
**S3 Choosing the card and granting access to it — VALE COM'È** (`card_pick.c`, `render_grant.c`, `render_node.c` non nel diff; `RENDER_NODE` e `PROBE_SIDE/ROUNDS` verificati). Non verificato su Ubuntu: gruppo `render`/ACL su macchine con linger, NVIDIA.
**S4 The encoding test: remotix --encoding-test — VALE COM'È** (postinst r.57 `timeout 30 … --encoding-test h264`, preinst che rifiuta senza `renderD*`: grep). Aggiungere che il messaggio del postinst cita «Intel/AMD: va-driver-all»: su Ubuntu `va-driver-all` è universe e porta solo Intel; per AMD il VA arriva da `mesa-libgallium` (main) (`debian/control`, studio 8 §1.2).
**S5 VA-API without libavcodec — DA CORREGGERE** (solo riferimenti): «not re-measured for Debian 13» → Ubuntu ha libva 2.23 e Mesa 26.0.8 (le misure AMD/Intel nei commenti sono di Mesa 25.0.7/builds precedenti, mai rifatte); il NOTE «Mesa radeonsi riscrive gli header» non verificato su Mesa 26.
**S6 The Vulkan Video encoder — DA CORREGGERE**
- Tabella «Evidence in this tree»: «Debian 13 ships Mesa; the package Recommends mesa-vulkan-drivers», «SPECS.md §11.4-bis lists AMD on Debian 13…», «not tested on every distribution including Debian 13». Su Ubuntu: Mesa 26.0.8 (`mesa-vulkan-drivers`, main), `libvulkan-dev` 1.4.341 (`debian/control`), `va-driver-all` in universe e solo Intel, `mesa-libgallium` porta VA per AMD/nouveau. Quale rotta (Vulkan o VA-API) sceglie la Radeon su Ubuntu: NON documentato (nessun file/giro cita `h264_vulkan`/`h264_vaapi`/`opened:` per Ubuntu: verificato con grep su studio/, docs/, PIANO.md).
- `encoder.c` cita ancora «RADV Mesa 25.0.7» come misura storica.
**S7 BT.709 colour conversion — VALE COM'È** (colors709.c, shader non nel diff). Nota nuova per Ubuntu (studio 4 §2.2 p.5/§3, [V sorgente, S effetto]): lo stream Mutter 50 dichiara `colorPrimaries=BT709`, `transferFunction=GAMMA22` e compone con gamma 2.2; `colors709.c` ignora il tag di trasferimento. Nessun confronto di immagini Debian/Ubuntu (studio 11 «SCOPERTA 25»).
**S8 Writing the bitstream headers — VALE COM'È** (bit_writer.c non nel diff).
**S9 Bytes, levels and the confession — VALE COM'È** (encoder.c non nel diff).
**S10 Keyframes on demand — VALE COM'È** (nessun diff).
**S11 Resizing the encoder and the frame ceiling — VALE COM'È** (`RCP_CANVAS_MAX_W/H` 4096×2304, limite dichiarato 3K, §11.58 già nel codice: nessun diff).
**S12 Encoder timings, constants and verification status — DA CORREGGERE**
- «Verified (17 Nov 2026, PIANO.md)… on a real Debian 13 VM… check-package 8/8 on each desktop», «Not verified: NVIDIA on Debian 13»: sostituire con l'Ubuntu. `check-package.py` NON gira nel banco a VM (`prove/all.sh`: «SKIP… needs box.sh reset»); installazione/remove/purge provati nei box e nelle VM (giro2-lxqt, studio 12). Il caso «VM senza scheda» per Ubuntu: non verificato. Costanti della tabella: tutte uguali (grep).
- Aggiungere (ottava riga sul rifiuto «nessuna GPU»): invariato.

---

## ch08_quality.py — «Quality, degradation and budget» — 337 righe — 14 sezioni

**S0-S10 — VALE COM'È** (11 sezioni: S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10). Controlli: `budget.c`, `encoder.c`, `hsrate.h`, `msgrate.h`, `linebudget.h`, `dimcheck.h` non nel diff; `webtransport.c` aggiunge solo `wt_dismiss_user_session_over()`; i nomi dei file `debian/remotix.conf`/`debian/remotix.service` esistono. I numeri della tabella delle opzioni (`WT_CLEAR_THRESHOLD_MS` 100, `WT_RATE_SLOTS` 2, `RCP_SESSION_CAP` 10, limite dichiarato 8 utenti) non cambiano. Non rimisurato su Ubuntu: budget acceso, tetto di banda, quality rise, decoder pace (come su Debian).
**S11 Admission: the session cap and the budget — DA CORREGGERE**
- «A child that cannot be born for another reason (a name NSS does not resolve, uid 0, `fork` failing) also ends in 0x0E»: su Ubuntu altre strade dello 0x0E (la pagina dice che sono SEI, `page.html` commento REASON_TEXT): «compositor non installato» (`main.c:1173`: XFCE/LXQt senza `labwc`, il figlio NON viene creato), «scala rifiutata» (`stage_refused_by_child`, `main.c:2187`), «ancora in chiusura» (`delivery_verdict()`), tetto di sessioni. Il congedo di fine sessione usa ora `wt_dismiss_user_session_over()` (`webtransport.c`; un login ancora in attesa di PAM o con il «no» già tenuto non riceve il falso 0x10): il testo di S11 parla di `wt_dismiss_user()` per il rifiuto, che resta corretto (`main.c:1362`).
**S12 Rate and size guards — VALE COM'È** (nessun diff).
**S13 Frames that are not encoded, and what is adapted — DA CORREGGERE**
- Blocco «What was verified» (17 nov, `two-sessions-budget`, 34 controlli per desktop): numeri Debian; Ubuntu 124 righe per desktop (128 su XFCE dopo le righe nuove). La cura del fotogramma perso (ch06) va citata fra i meccanismi che evitano/ripetono fotogrammi su KDE. «The unchanged filter (KDE only)»: `UC_*` verificati uguali.

---

## ch09_page.py — «The browser page» — 674 righe — 17 sezioni

**S0-S13 — VALE COM'È** (14 sezioni). Controlli: `page.html` +3 righe di commento (solo REASON_TEXT 0x0E), `page.c` assente dal diff; `wc`: 14 258 righe, 937 399 byte («about 14 000 lines and 0.9 MB» vale); `debian/remotix.service`/`remotix.install` (percorso `/usr/share/remotix/page.html`) senza diff pertinente; `src/opus-wasm/` non toccato. Le misure storiche su Firefox 140/Chrome 151-154 restano storiche; i giri Ubuntu usano Chrome 156.0.8078.79 e Firefox 153.7.0.
**S14 End of session in the page — DA CORREGGERE**
- «after a logout or a reboot the graphical session is born from scratch, measured 9 s and about 32 s» è una misura Debian. Ubuntu: GNOME primo fotogramma +27,3 s dal clic nel caso di attesa del `graphical-session.target` (giro1-gnome G4), Kubuntu sfondo a 10 s e pannello a 40 s (giro2-kde K4). Il tempo di Log Out riportato al client: 11-14 s (GNOME/KDE).
- FAREWELL 0x10: oggi il figlio lo fa partire PRIMA dello smontaggio dello stage, solo su morte certa (`session_over_early()`, `child.c`; escluso KDE: «KDE waits for a proof on a live machine»). Prima: fino a 17 s di pagina ferma (RealtimeKit). Aggiungere le frasi della pagina per le nuove strade 0x0E (rif. ch05).
**S15 The video worker and the MSE path — VALE COM'È** (nessun diff).
**S16 Browsers supported and untested — DA CORREGGERE**
- Righe «Samsung DeX… tried by the owner on 17 Nov 2026 on GNOME» e «the checks run on the four desktops» riguardano Debian. Ubuntu: stessi controlli sui quattro box, poi prova a mano del proprietario (19 nov) sulle quattro VM e sulle quattro live; Android Chrome: registro E4 (piccoli scatti nel video da Chrome su Android, VM Ubuntu, non distinto telefono/VM/codifica Radeon, non bloccante). `prove/check-phone.py` ancora solo emulazione (giro: 18/19 → PASS in unione2).

---

## ch10_input.py — «Input» — 679 righe — 17 sezioni

**S0 Input at a glance — VALE COM'È** (diff `input.c` irrilevante qui; tabella desktop invariata; «nested KWin in a screenless labwc that REMOTIX starts» è vero, e ora è il labwc proprio).
**S1 The input messages — VALE COM'È** (`rcp.c`, `msgrate.h`, `wheelclamp.h` non nel diff; `WHEEL_MAX_UNITS` 12000 verificato).
**S2 Classic and touch layouts — VALE COM'È** (solo `page.html`, diff = commenti).
**S3 Mouse and pointer in the classic layout — VALE COM'È** (idem).
**S4 Wheel and scrolling — VALE COM'È** (input.c non cambia qui; misura del segno storica su Mutter 48.7/libei 1.3.901; su Ubuntu `mouse-wheel` PASS in unione2 GNOME; segno su libei 1.5.0 + Mutter 50.1 non misurato a parte).
**S5 Keyboard: letters and positions — VALE COM'È** (keyboard.c, page.html senza diff pertinente). In 50 Mutter manda anche i modificatori XKB sul dispositivo tastiera EIS; `input.c` `handle_event` ha `default: break;` (studio 4 §2.3).
**S6 Shortcuts the browser keeps — DA CORREGGERE**
- WARN «the Ctrl+Alt+Del button is not visible… check that fails by design»: i nomi sono cambiati: `page-cad-button` → `page-cad-hidden` (PASS: fuori dalla diagnostica la pagina non mostra il pulsante, `check-input.py`), `page-ctrl-alt-end` → `page-ctrl-alt-end-passes` (PASS: Ctrl+Alt+Fine arriva al desktop). Il pulsante è nascosto per scelta (DECISIONS-11 §11.54); «SPECS §7.3-bis… still to be aligned» va rivisto (registro B3).
- Aggiungere KDE: Ctrl+Alt+Canc non apriva la schermata di uscita da Plasma 6.4 (giro2-kde §2: `kglobalaccel` emette il segnale ma `ksmserver` non apre) → sidecar ScreenSaver (`kwin.c`), misurato con un sostituto, non rigirato.
**S7 Touch gestures — VALE COM'È** (page.html senza diff). **S8 The touch pointer is announced — VALE COM'È** (WARN «one test out of thirteen on GNOME»: registro E2 conferma «primo tocco da telefono su GNOME, saltuario»). **S9 On-screen keyboard — VALE COM'È**. **S10 From a letter to key positions — VALE COM'È** (keyboard.c).
**S11 Keyboard layout negotiation — DA CORREGGERE**
- Riga GNOME: «written only in the session dconf's in-memory layer (`shm`…)» è ora il database UTENTE `remotix` (`~/.config/dconf/remotix`, scrittore `/ca/desrt/dconf/Writer/remotix`, i blocchi in `system-db:remotix` = `/etc/dconf/db/remotix` compilato dal postinst da `/usr/share/remotix/dconf/remotix.d`); `shm/remotix` solo nel ripiego dichiarato («DECLARED FALLBACK, D-015 (19 Nov 2026)»). Prova: `input.c` ~2230-2240 e 2284-2291 (`DCONF_SESSION_OBJECT = session_dconf_object()`, `session.h:547`), registro C5. Un file nostro nella casa dell'utente, tolto da `apt purge` (postrm).
- Riga KDE: «KWin up to 6.3 (the series the comments name for trixie, 6.3.6) … a KWin of the 6.6 series only to the second» → su Ubuntu KWin è 6.6.7: agisce solo `org.kde.kconfig.notify ConfigChanged /kxkbrc` (`kwin.c:962-969`, misura 6 ott su KWin 6.6.6 Ubuntu: senza di esso restava `English (US)`, F-009); entrambi i segnali si mandano. Verificato dai controlli di layout sulle prove KDE.
- Riga XFCE/LXQt «Whether labwc forwards it is not measured»: labwc 0.9.3, `kbd-accents`/`kbd-altgr`/`kbd-text` PASS nei giri XFCE/LXQt (giro2). Aggiungere (studio 4 §2.4): Mutter 50 ha un metodo nuovo `RemoteDesktop.Session.SetKeymap`; il commento di `input.c:2062-2080` «Mutter non offre la leva» è falso su 50, il prodotto resta su dconf (provato). Lo schema e le chiavi `input-sources` esistono in GNOME 50; chi le legge è la Shell, non `gsd-keyboard`.
**S12 Injection through libei — DA CORREGGERE**
- «libei ≥ 1.3.901… always compiled in» e il WARN SIGSEGV «In libei 1.3.901»: su Ubuntu `libei1`/`libeis1` sono 1.5.0-3 (nel sorgente il protocollo cambia solo nei commenti, `ei_touchscreen` v2). Se il difetto di `ei_disconnect()` sul contesto senza handshake esiste ancora in 1.5.0: NON verificato (la cura D4 resta in `input.c`).
- Ricevuta per tasto (`ei_ping`): con libeis 1.5.0 il pong parte quando Mutter rilascia `EIS_EVENT_SYNC` dopo il thread di input (`meta-eis.c`, studio 4 §2.3): più forte, ma dipende dal thread di input del backend nativo in headless; verificato indirettamente (tastiera PASS su GNOME 50.1, studio 11 S4.3).
- «nested KWin host»: la frase «labwc … written by REMOTIX» è vera per il labwc proprio; `kdehost.h`, `HOST_RC` invariati.
**S13 Pressed keys: counting, releasing, healing — DA CORREGGERE**
- La catena di Mutter (misure 16/21 ago, «new in GNOME 48.5») è di Mutter 48: in Mutter 50 `drop_device`/`handle_button` invariati nel diff di studio 4 ma la cura C NON è rimisurata (bench `06-b33` non c'è nell'albero Ubuntu: studio 11 S4.12 «SCOPERTA 14»).
- `heal()`/`input_dropped()`: per wlroots `input_dropped()` ora risponde davvero (`input.c:1504-1513` → `wlr_input_dropped(in->wlr)`; prima restava sempre 0 e il figlio di XFCE non si accorgeva del Log Out: studio 12-verifiche-xfce A). Il figlio la usa solo insieme a `session_life()` (tre esiti: vivo/morto/sconosciuto, 3 giri a 1 s prima di smontare, `child.c`).
**S14 Virtual keyboard and pointer on labwc — DA CORREGGERE**
- «private headless labwc 0.8.3 (the version in trixie)»: misura Debian del 21 set. Ubuntu ha labwc 0.9.3-1 (universe) e wlr-randr 0.4.1; il codice 1.0.0 non è stato provato a parte con 0.9.3 ma i giri XFCE/LXQt (117/124 poi 126/128 e 124/124) comprendono tutti i controlli di input (studio 7 §11.8 «VERIFICATO»). I punti sensibili alla versione (forma di `<keybind>`/`rc.xml`, `SESSION_LABWC_*`, nomi dei cursori) non sono riesaminati in dettaglio.
- Aggiungere `input_dropped()` per wlroots (vedi S13).
**S15 Input decisions — DA CORREGGERE** (una riga): «Layout written in the session's in-memory dconf layer» → user-db `remotix`; «libei 1.3.901 crash» è la ragione storica. Il resto vale.
**S16 What was verified for input and what was not — DA RISCRIVERE**
Motivo: tabella e conteggi sono del 17 nov su Debian (111/118, 112, 111, 104; `page-cad-button` e `page-ctrl-alt-end` come rossi voluti; DeX su GNOME; «KDE a held Delete key»). Su Ubuntu: stessi nomi di controllo salvo le due righe rinominate (verdi), 124 righe per desktop, banco = VM (`RX_BANCO=vm`, `RX_TEMPO=2`; SKIP dichiarati: `prelocal/real-greeter`, `ban/other-addresses`, `package`); i tre rossi di unione1 (`mouse-drag` ×2, `tap-and-half-drag-select`) erano un difetto della finestra di prova (GTK 4.22, registro B3-bis); `page-cad-chain` su KDE rosso in unione2 (Delete preso da KWin); `desktop/canvas-limits` KDE non riprodotto; XFCE unione2 `base-firefox/mouse` e `keyboard` rossi (non spiegati nel mio materiale).

---

## ch11_audio_clipboard.py — «Audio and clipboard» — 451 righe — 13 sezioni

**S0 Audio at a glance — VALE COM'È** (sound.c/audio.c non nel diff). **S1 The audio format and its datagram — VALE COM'È** (rcp.h, webtransport.c senza diff pertinente).
**S2 The session sink and its capture — VALE COM'È** (sound.c non nel diff). Aggiungere versioni: PipeWire 1.6.2, WirePlumber 0.5.13 (PIANO: «avviso `wireplumber` visto solo sulla macchina virtuale», aperto non bloccante, testo non nei miei file); righe `audio` PASS (studio 11 S4.§12.c).
**S3 From samples to datagrams — DA CORREGGERE**
- WARN «Real-time priority is declared, not assumed… CONFIG_RT_GROUP_SCHED… measured 21 Aug» (Debian). Su Ubuntu i box dei giri registrano «FIFO NOT OBTAINED: 3 threads out of 3 of the audio path run at NORMAL policy… RLIMIT_RTPRIO = 0» (giro1-gnome G3, limite del contenitore); sulle VM non documentato. Aggiungere RealtimeKit: `module-rt` dei due contesti PipeWire (`sound.c`, `capture.c`) resta in una chiamata D-Bus fino a 25 s se `rtkit-daemon` non parte (`child.c`, box `session_over_early()`; registro B2).
**S4 The Opus encoder — DA CORREGGERE** (piccolo): «verified identical… (libopus 1.5.2…)»: su Ubuntu il sistema ha libopus 1.6.1 (studio 4 §1); il confronto byte per byte è fatto a 1.5.2 e NON rifatto su 1.6.1. Parametri (`AUDIO_OPUS_BITRATE` 96000, complessità 10, VBR) non nel diff.
**S5 Playing audio in the page — VALE COM'È** (decoder wasm 1.5.2 fisso in `src/opus-wasm/`, sha256 pinned, non nel diff).
**S6 Clipboard at a glance — VALE COM'È.** **S7 The clipboard messages and their limits — VALE COM'È** (`RCP_CLIPBOARD_CAP` 1 000 000, `CLIPBOARD_PER_SECOND` 10: grep).
**S8 Clipboard on GNOME — DA CORREGGERE** (piccolo): «DisableClipboard is one-way (Mutter 48.7)»: interfaccia `Selection*` e `meta-selection*` quasi identiche in 50.1 (studio 4 §4), ma il comportamento di `DisableClipboard` su 50 non è verificato (il codice non lo chiama). Su Ubuntu i controlli `clipboard` passano su GNOME (unione2).
**S9 Clipboard on KDE and labwc — DA CORREGGERE**
- «A KWin of the 6.6 series exposes only the standard one (measured 6 Oct 2026 on another distribution; trixie's KWin is of the 6.3 series…)»: la misura è proprio su Ubuntu 26.04 / KWin 6.6.6 (`clipboard_kde.c:325`); su KWin 6.6.7 `datacontroldevicemanager_v1.cpp` implementa solo `ext_data_control_manager_v1` (studio 6 §6.1). Su Ubuntu il ramo `ext_` è QUELLO USATO, non un'eccezione. Lubuntu: qlipper acceso e `clipboard` PASS nei due versi (giro1-lxqt L4).
**S10 Clipboard in the browser — VALE COM'È** (page.html senza diff pertinente).
**S11 Audio and clipboard decisions — DA CORREGGERE** (una riga): «Never DisableClipboard — One-way in Mutter 48.7» (stessa riserva di S8).
**S12 What was verified for audio and clipboard — DA RISCRIVERE**
Motivo: tabella con stato del 17 nov su Debian (`check-audio.py`, `check-media.py`, `check-clipboard.py`, Firefox open, DeX su GNOME). Su Ubuntu: `audio`, `clipboard`, `input` clipboard-firefox verdi nei giri unione2; su VM `avlib.ensure_pulse` fa SKIP («the private PulseAudio of the lxqt box… does not exist there»: `check-audio.py` usa il PipeWire dell'host). Non verificato: clipboard con manager aperto su Plasma/Klipper oltre il caso qlipper, immagini, microfono, Safari, telefono vero.

---

## (a) COSE NUOVE di Ubuntu che oggi MANCANO (con dove)

1. ch06 — NUOVA sezione dopo S3 (o h4 in S4): «The lost frame (KWin)». Contenuto da `capture.h`/`capture.c`/`child.c`: difetto Kubuntu 26.04, KWin 6.6.7, PipeWire 1.6.2 (finestra aperta ferma a metà animazione per 18-26 s); numeri `spa_meta_header.seq` con buchi 198/200/202 (cursor-only) senza 199/201/203; causa `[R]` (`screencaststream.cpp` timer che rischedula dentro `record()`, driver del grafo, xrun a `tee_process`/`node_ready`: nulla da regolare dal nostro lato); costo (damage perso; se è l'ultimo fotogramma dell'animazione niente dopo); cura in due metà: `capture_watch_sequence()` (conta solo per KWin; buco ⇒ `damage_lost` = prossimo frame «tutto cambiato», `lost_need`), `capture_frame_lost()` (dopo `LOST_QUIET_MS` 200 ms di silenzio, al più 1 poke/200 ms, fino a `LOST_POKES_MAX` 10 poi stop e una riga) e `kwin_poke()` (riattacca, danneggia 1×1 e committa il pixel trasparente sotto mutex `pixel_lock`; nessun riavvio dello stream, nessun input). Interruttore di sicurezza: >300 buchi su 600 buffer (`SEQ_WINDOW`/2) spegne il conteggio (misurato: al più 30 buchi in ~200 buffer a sessione nascente). Misura: 68 poke su desktop fermo = 68 frame interi con damage vuoto, scartati. Righe di registro (area `capture`/`child`): «the buffers' numbers are watched…», «a buffer of KWin never arrived and no picture came after it: pixel on top committed again (so far: N holes…)» (max 1/s), «⚠ %d pokes in a row and no picture from KWin: I stop asking…», «⛔ %u holes in the numbers of the last %u buffers… switched OFF». ATTENZIONE: questa storia è SOLO nei commenti di codice, non in `DECISIONS.md` né in `REGISTRO-problemi.md` (grep): il manuale è la sua unica documentazione; segnalarlo.
2. ch06 S3 — il labwc proprio (build, perché, `VERSIONS`, patch, link statico, licenza GPL-2.0 per labwc con sorgente corrispondente pubblicato; `THIRD-PARTY-LICENSES`); ripiego `--virtual`.
3. ch06 S3 tabella — sidecar `org.freedesktop.ScreenSaver` (e rinvio a ch10 S6).
4. ch06 S2 — `mutter_scale_to_one()` e il blocco `scaling-factor` (vedi S2); stessa cosa citata in ch05/ch12 per lo 0x0E.
5. ch06 S4 — differenze Mutter 50 (clock passivo, rinegoziazione dopo `monitors-changed`, buffer 2..8, tag colore BT709/GAMMA22) con la dicitura «verificato nel sorgente, non misurato a mano».
6. ch10 S11-S15 — modello dconf (user-db `remotix`, `system-db:remotix`, profilo di runtime `$XDG_RUNTIME_DIR/dconf/profile`, ripiego) con rinvio alla sezione del pacchetto; `SetKeymap` di Mutter 50 non usato.
7. ch10 S13/S14 — `input_dropped()` per wlroots e uso con `session_life()` a tre esiti.
8. ch08 S11 / ch09 S14 — nuove strade dello 0x0E e congedo anticipato (`session_over_early()`), con KDE escluso.
9. ch09/ch10/ch11 «What was verified» — il banco a VM e i numeri dei giri Ubuntu (tabella sopra).
10. ch07 S0 — nota di licenza: il pacchetto ora contiene anche un binario GPL-2.0 (labwc statico) accanto al prodotto; «no GPL encoder library» resta vero (non è linkato dal prodotto).

## (b) Cose di Debian da TOGLIERE o riscrivere

- ch06: S0 «On Debian 13…», NOTE «labwc is a Recommends… optional for KDE only»; S3 «KWin 6.3.6» (tre punti), «The labwc is the one found in PATH; REMOTIX ships none», «Without labwc…» (riformulare su `REMOTIX_LABWC`), «not measured on Debian 13, whose KWin is 6.3.6»; S4 «Mutter 48.7»; S6 «not re-measured on Debian 13»; S9 «not examined on Debian 13»; S10 blocco verificato (17 nov).
- ch07: S5 «not re-measured for Debian 13»; S6 tre menzioni di Debian 13 + «Mesa 25.0.7» come unica evidenza; S12 «a real Debian 13 VM», «NVIDIA on Debian 13».
- ch08: S13 blocco «What was verified» (17 nov, 34 controlli).
- ch09: S14 «measured 9 s and about 32 s»; S16 «DeX… 17 Nov on GNOME».
- ch10: S4 «libmutter 48.7, libei 1.3.901» (storico, da qualificare), S11 «the series the comments name for trixie, 6.3.6», S12 «libei ≥ 1.3.901/1.3.901 crash», S13 «new in GNOME 48.5», S14 «labwc 0.8.3 (the version in trixie)», S16 intero.
- ch11: S4 «libopus 1.5.2» come versione del sistema, S8/S11 «Mutter 48.7», S9 «another distribution… trixie 6.3», S12 intero.

## (c) rif() verso altri gruppi, convenzioni di stile

rif() da citare/ricontrollare (titoli di sezione o capitolo di altri gruppi): «Startup and life cycle» (ch06), «The four desktops» (ch06, ch09, ch10), «The package» (ch06, ch07), «Logging and diagnostics» (ch06), «Testing» (ch06), «Overall architecture» e «Transport» (ch08), «Login and its defences» (ch07, ch08, ch09), «Security model» (ch09), «Performance and capacity» (ch07, ch08), «Appendix C — Known issues and open points» (ch07, ch09, ch10), «The RCP/1 protocol» (ovunque; qui andrà l'elenco delle sei strade dello 0x0E). Verso la mia area, da altri gruppi: «Screen capture», «Video encoding», «Audio and clipboard», «Input», «The browser page». I rif() interni ai miei capitoli vanno mantenuti con gli stessi titoli di sezione se aggiungo una sezione («The lost frame (KWin)»): `rif()` risolve per titolo, quindi i titoli delle sezioni esistenti NON vanno cambiati senza aggiornare i richiami (es. «KDE: the KWin screencast protocol and the nested KWin» è citato da ch06 S0).
Stile: `CHAPTER = (titolo, [(titolo sezione, html), ...])`; `from build import arrow, box, c, fig, h4, note, p, path, rif, table, text, tip, ul, warn, zone` (ch07 anche `code`, `flow`; ch10 anche `key`, `seq`, `steps`, `sysf`, `ui`). `p(…, lead=True)` per il paragrafo d'apertura; `table(head, rows, cap, tid)`; `note(t, title)`/`warn(t, title)` con il titolo breve dopo il testo («Scale guard.», «Slabs and the AMD GPU hang.»); `c()` per i nomi di codice, `path()` per i percorsi; `FIG` con didascalia ««FIG» — …»; blocchi `code()` solo per JSON/righe d'esempio (ch07 S4, ch08 S1, S5, S10). Tono: inglese asciutto, ogni numero con il nome della costante e il file; dichiarazioni «Not settled yet / Not verified» e frasi «the comments record…» per ciò che viene dai commenti; ogni sezione chiusa da «What was verified, and what was not» nei capitoli di fine gruppo. Per Ubuntu: distinguere sempre [misurato su Ubuntu] / [dal sorgente] / [storico Debian].

Riga conclusiva richiesta: `/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/e6fe62ae-14ba-4562-b4a7-817b943522ce/scratchpad/inv/g2.md` — 85 sezioni: 59 vale com'è, 24 da correggere, 2 da riscrivere.


---------------------------------------------------------------------------------------------------

<!-- ===== frammento g3 ===== -->
# Frammento g3 — ch12_desktops, ch13_login, ch14_security (manuale tecnico Ubuntu 26.04)

Fonti usate: `src.diff` (session.c/h, child.c, kwin.c, mutter.c, main.c, sentinel.c, remotix.pam, rootside.c), `pacchetto.diff` (control, rules, postinst/postrm, apparmor, needrestart, labwc-ospite), `docs.diff` (registro C4, C5, D, E1-E4, DECISIONS-11 §11.55 nota), studi 2, 3, 5, 6, 7, 8 e i file attuali del ramo. Il diff `main..ubuntu-26.04` su `technical-debian13/ch12_desktops.py` ha 16 righe aggiunte e 3 tolte, tutte su dconf (vedi ch12 §3, §5, §6, §10): sono gia' nel file `technical-ubuntu26.04/ch12_desktops.py` e sono coerenti col codice, ma incomplete (descrivono solo il modello dconf, non il resto). Le versioni di Ubuntu citate vengono dagli studi del ramo (`studio/7`: xfce4-session 4.20.4, libxfce4windowing 4.20.5, lxqt-session 2.3.0, lxqt-panel 2.3.2, labwc 0.9.3, systemd 259.9; `studio/6`: Plasma/KWin 6.6.7; `studio/1`: gnome-shell/mutter/gnome-session 50.1, libei 1.5.0): non le ho ricontrollate su una macchina.

---------------------------------------------------------------------------------------------------

## ch12_desktops — «The four desktops» — 726 righe — 11 sezioni

### 12.1 «The four desktops side by side» (righe 6-60) — DA CORREGGERE
- «Versions» (r. 37-47): tutto il paragrafo e' di Debian 13: «four Debian 13 test containers on 17 Nov 2026», `docs/PULIZIA-tranche1.md`, «GNOME Shell 48.7, KWin 6.3.6 and labwc 0.8.3», unita' `org.gnome.Shell@wayland.service` «as a real file», sessioni «trixie ... gnome, gnome-login, gnome-dummy», XFCE 4.20.2 / LXQt 2.1.1 («read from sources ... not re-verified»). Su Ubuntu (studi): GNOME Shell/Mutter/gnome-session 50.1; l'unita' e' il template `org.gnome.Shell@.service` con istanza per sessione (`@ubuntu`, `@user`) — `session.h` `SESSION_UNIT_SHELL_MODEL`; KWin 6.6.7 (Plasma 6.6.7); xfce4-session 4.20.4 (libxfce4windowing 4.20.5); lxqt-session 2.3.0, lxqt-panel 2.3.2; labwc 0.9.3 della distribuzione (XFCE/LXQt) e labwc 0.9.3 + wlroots 0.19.2 patchato, statico, proprio del pacchetto (KDE: `/usr/libexec/remotix/labwc`, `build/labwc-ospite/VERSIONS`). Il rinvio a `docs/PULIZIA-tranche1.md` va sostituito dai riferimenti agli studi/registro del ramo (esistono in `studio/`).
- «§11.8 names GNOME 46, KDE 6.1, XFCE 4.20, LXQt 2.0 as minimums»: affermazione sui minimi, non cambia nel codice; ma su Ubuntu il dato utile e' che nessun controllo di versione esiste ancora (non verificato diversamente: `grep` di numeri di versione nel diff non trova nulla).
- Riga «Compositor / KDE Plasma»: «KWin, nested in a labwc» vale, ma il labwc e' ora il NOSTRO (`kwin.c`, `REMOTIX_LABWC`, `kwin_nested_alive()`: `access(REMOTIX_LABWC, X_OK)`; mai il labwc della distribuzione). Riga «Started by» KDE: stessa precisazione.
- Riga «Log Out» KDE: ora in piu' c'e' `session_kde_logout_watch()` con `plasma-shutdown` e `ksmserver.isShuttingDown` (vedi 12.5).
- «One desktop per machine»: il testo «with none of the four the server says so (`debian/control`)» resta; da AGGIUNGERE il caso nuovo `session_missing_component()` (session.c, 18 nov): XFCE/LXQt senza `labwc` → il padre rifiuta prima della nascita con 0x0E (`main.c` `delivery_verdict()`), nessun figlio, nessuna sessione logind; il pacchetto lo dichiara anche nel postinst (`pacchetto.diff`, `remotix.postinst`).
- «Whose settings these are» (r. 52-60): la frase «writes nothing permanent in the user's settings» ha ora eccezioni in piu' su GNOME: (a) il file `~/.config/dconf/remotix` (tre chiavi, svuotato a ogni nascita, tolto da `postrm` a purge; registro C5), (b) il file vuoto `~/.local/share/gnome-shell/lock-warning-shown` fatto alla nascita da `session_gnome_lock_warning()` e tolto a fine sessione se lo ha fatto REMOTIX (marchio in `$XDG_RUNTIME_DIR/remotix/lock-warning-made`). «Two exceptions remain» → quattro (le due di XFCE/LXQt piu' queste).

### 12.2 «How the desktop is recognised» (r. 65-103) — DA CORREGGERE
- `desktop_of_session_name()` (r. 88-91, parole `xfce`, `lxqt`, `plasma`/`kde`, `gnome`): ora anche `xubuntu`→XFCE, `lubuntu`→LXQt, `kubuntu`→KDE, e `ubuntu`→GNOME chiesto per ULTIMO perche' xubuntu/lubuntu/kubuntu lo contengono (session.c; limite dichiarato: cattura anche `ubuntustudio`, `ubuntu-budgie`). Senza questa mappa Xubuntu cadeva su GNOME (studio 7 §1, punto 1).
- Tabella «recognition order», riga `gnome-session` e `gnome-shell`: su Ubuntu con i Recommends accesi anche Xubuntu ha ENTRAMBI i marcatori GNOME (gnome-shell 50.1 e gnome-session-bin, studio 7 §3.1) e quindi entra nel ramo «due o piu' desktop» e si decide con la dichiarazione di lightdm (`user-session=xubuntu`, in `/usr/share/lightdm/lightdm.conf.d/60-xubuntu.conf`). Con `--no-install-recommends` il marcatore GNOME non c'e'. Da dire nel testo.
- Elenco «Machines with two or more desktops»: i display manager di Ubuntu: lightdm (Xubuntu), sddm (Lubuntu; Kubuntu: non verificato da me), gdm3 (Ubuntu; ignorato come «another one»). La descrizione di `declared_desktop()`/`active_display_manager()` vale com'e'.
- «Parent and child ... same answer» (r. 66-68): il `PATH` del figlio ora e' quello composto da PAM (`pam_env`, `/etc/environment`: su Ubuntu include `/snap/bin`), non piu' fisso; il commento di `recognize_desktop()` dice che l'accordo regge «as long as the programs are in `/usr/bin`».
- `DesktopSession` valori 0-4 (r. 97-98): non toccati (grep in `session.h`).

### 12.3 «The composed environment» (r. 108-154) — DA CORREGGERE
- Riga `XDG_SESSION_DESKTOP`: aggiunta una regola nuova in `add_session_names()`/`login_session_desktop()`: con sddm vale il `DesktopNames` del file di sessione (Lubuntu → `LXQt`, non `Lubuntu`), con lightdm/gdm il nome della sessione. Il «fallback xfce/lxqt» resta.
- Riga `XDG_DATA_DIRS`: ora puo' contenere anche la cartella «comune» `/usr/share/gnome` (campo `common` di `LocalSession`, da `profile.d/gnome-session_gnomerc.sh`).
- Riga `PATH`: «yes» → ora proviene da PAM (`child_path_ok()`; fallback `/usr/local/bin:/usr/bin:/bin`); su Ubuntu `/etc/environment` aggiunge `/snap/bin` e le cartelle sbin/games. `remotix.pam` ha ora un avviso: NON aggiungere `user_readenv=1` a `pam_env` (il PATH sarebbe scelto dall'utente).
- Riga `DCONF_PROFILE` (gia' modificata nel ramo): corretta («not set»). Manca il caso dell'amministratore (variabile mantenuta e puntata al nostro file: `dconf_admin_profile`) e il ripiego del 1.0.0 (variabile impostata).
- Riga `XDG_CURRENT_DESKTOP` GNOME: `DesktopNames` della sessione scelta, quindi su Ubuntu `ubuntu:GNOME` (la patch `desktop_detect` di Ubuntu lo richiede, studio 1): il testo dice solo «of the chosen session file», vale.
- Paragrafo «The session's own folders» (r. 140-146): FALSO su Ubuntu. Dice che `60x11-common_xdg_path` «does not exist» e che `local_session()` ritorna una struttura vuota. Su Ubuntu 26.04 lo script esiste (x11-common 1:7.7+26ubuntu1, studio 7 §1 punto 2) e `local_session()` ora trova nome, cartella config, cartella dati e cartella comune (`local_session_name_find()`, `local_login_adds_folders()`: `Xsession.d/60x11-common_xdg_path` per sessioni X11 o per lightdm, oppure `/etc/profile.d/xdg_dirs_desktop_session.sh`). La riga di registro «⭐ D-153» ora stampa `config folder`, `data folder`, `common folder`. Citazione `docs/PULIZIA-tranche1.md` item 7: da sostituire.
- «The render node» (r. 147-154): vale com'e' (`card_pick.c` non e' nel diff).
- Da AGGIUNGERE: `OUR_VARIABLES` (usata anche in 12.5) ha quattro voci nuove solo di GNOME 50: `GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULE`, `QT_IM_MODULES`, `XMODIFIERS`.

### 12.4 «How a session is born» (r. 159-241) — DA CORREGGERE
- «The logind session» (r. 174-189): FALSO per Ubuntu. Il testo racconta il fifo `/run/systemd/sessions/<id>.ref`, `--session-fd`, CLOEXEC, «measured on the four boxes». In questo ramo `child.c` non cerca piu' alcun fifo e l'opzione `--session-fd` e' stata tolta: con systemd 259.9 (da v258) logind segue la sessione col PIDFD del leader (`pam_systemd.c:856`, `logind-session.c:97-107`); il leader e' il figlio, che mantiene il pid attraverso `execve`. `pam_end()` senza `pam_close_session()` resta. Prova: diff di `child.c` (righe `-session_fd`, `+THE LOGIND SESSION NEEDS NOTHING TO CROSS THE execve`), `docs/DECISIONS-11.md` §11.55 nota 18 nov, studio 5 §7.1. Resta valida con un logind < 258 ancora in memoria in un aggiornamento (caso escluso su Ubuntu 26.04 nuovo).
- Passo 1 «Clear-out and snapshot»: `dconf_profile_reinstate()` «puts the three dconf layers back» → oggi sul modello nuovo non ci sono tre strati ne' `DCONF_PROFILE` (vedi 12.6). Aggiungere E3 del registro: la «foto» del gestore utente puo' essere vecchia dopo una chiusura fatta dal lato root.
- Passo 2 «The drop-in»: la cartella `.../user.control/<unit>.d/` per GNOME e' ora dell'ISTANZA (`org.gnome.Shell@ubuntu.service.d` o `@user`), mai del template `org.gnome.Shell@.service.d` (si applicherebbe anche alla Shell di GDM); `ExecStart` ora termina con `--mode=%i` (`write_dropin()`).
- Passo 3 «Guards»: `inactive_unit()` ora controlla su GNOME anche `graphical-session.target` (terza unita': `gnome-session-init-worker` abortisce con «A graphical session is already running!», `session.h` `SESSION_UNIT_GRAPHICAL`) e dice QUALE unita' e' occupata (`inactive_unit(const char **busy)`, riga di registro ««%s» is not inactive»).
- Tabella «The command that starts each desktop», riga GNOME: la scelta di `gnome_session()` ha un passo nuovo prima del ripiego `gnome`: la sessione che porta il nome della distribuzione (ID di os-release: `ubuntu`), registrata con «it bears the distribution's name». Quindi su Ubuntu e' `ubuntu`, anche se `gnome` e' installata.
- Da AGGIUNGERE come passo della nascita: `session_missing_component()` in `session_spawn()` («I am not making anything be born: ... needs `labwc`»), prima di `session_state()`.
- «WAIT_STARTUP_MS 40 s», «BIRTH_REIN_MS 12 s», «STAGE_BIRTH_RETRY_MS 200» e le altre costanti citate: non toccate (grep: `session.c:68`, `child.c` 5533, 5566).
- «wlr-randr is a Recommends»: vale (control). 

### 12.5 «Ending a session and tidying up» (r. 246-323) — DA CORREGGERE
- «The user logs out» (r. 250-258): «its lifeline fifo closes and logind closes the session» → ora «the leader's pidfd fires» (commento aggiornato in `child.c`).
- Da AGGIUNGERE (child.c, 19 nov): `session_over_early()`. L'addio `MSG_SESSION_FINISHED` e' mandato PRIMA di smontare lo stage, solo su morte CERTA (`session_life()` == `SESSION_LIFE_DEAD`: il bus ha risposto e il nome del compositore non ha proprietario), mai su KDE (`stage_kwin`). Motivo misurato: lo smontaggio puo' aspettare PipeWire/RealtimeKit fino a 25 s dove `rtkit-daemon` non parte. `session_alive()` e' ora `session_life()==ALIVE`; `SessionLife` ha tre valori (ALIVE 0, DEAD 1, UNKNOWN 2); `EIS_UNKNOWN_ROUNDS` = 3. Anche il padre ora conta il figlio come «closing» da subito (`closing_asked_ms`).
- Tabella «How each desktop is asked to end»: GNOME, colonna «fact that decides»: aggiungere `graphical-session.target` inattivo. `really_terminate()`: «there was no session to stop» ora ritorna TRUE (chiusura fatta) solo se `inactive_unit()` e' vero; altrimenti scrive «⚠ the session name is not on the bus but the desktop's units or processes are still there» e prosegue con la via normale.
- «What is left in the user manager»: la lista `OUR_VARIABLES` ha 4 voci in piu' (vedi 12.3); `clear_out_handler_run()` toglie anche un `DCONF_PROFILE` nostro lasciato da una versione precedente (`dconf_env_is_ours()`). `session_dconf_neutralise()` (gia' corretto nel ramo): oggi il file e' il profilo di runtime, tolto se la base e' quella predefinita. Aggiungere: la neutralizzazione toglie anche `lock-warning-shown` se lo ha fatto REMOTIX.
- Sezione «KDE: a Log Out that stops halfway» (r. 308-323): da RISCRIVERE nella parte del segnale. Il segnale di Debian («`plasma-workspace.target` visto attivo e poi non attivo») resta come seconda via, ma su Plasma 6.6 il target non si ferma mai e il logout si perde (registro D, 18 nov). Prima via nuova: `plasma-shutdown` possiede `org.kde.Shutdown`; il suo rilascio (`NameOwnerChanged`, contesto GLib privato, `shutdown_name_listen()`) + risposta `true` di `ksmserver.isShuttingDown` (`shutdown_released_judge()`); `false` o nessuna risposta = non si forza nulla (lavoro non salvato). Grazia `KDE_LOGOUT_GRACE_MS` 4 s, ripetizione ogni `KDE_LOGOUT_RETRY_MS` 3 s: `KDE_LOGOUT_TRIES` = 10 tentativi in modo `fail`, poi altri 10 in modo `replace`; dopo 20 rifiuti `session_kde_logout_watch()` ritorna `true` (firma cambiata da `void` a `bool`) e il figlio chiude con la strada del prodotto (`terminate_and_clear()`), messaggio «giving up on it». Limiti dichiarati: `logoutAndShutdown/Reboot` (6.6.7) non rilascia il nome; riavvio di KWin durante l'attesa azzera la richiesta. Il vecchio testo «at most 10 times» e' falso.
- `warn` «Scope of the KDE watch»: cita PIANO.md del 17 nov (Debian): su Ubuntu PIANO.md e' un'altra cosa; il caso «XFCE ignora un Log Out chiesto mentre parte» e' confermato anche con xfce4-session 4.20.4 (studio 7 §14 punto 5, sorgente `xfsm-manager.c`), la cura e' la forzatura dopo 10 s (`kill_xfce()`). Aggiornare il rinvio.

### 12.6 «GNOME: headless Shell and session dconf» (r. 328-413) — DA RISCRIVERE
Motivo: il modello dconf e il GNOME 50 cambiano la sezione; il paragrafo aggiunto nel ramo (r. 356-368) dice la cosa giusta ma il resto (r. 369-413) descrive come «il modello» quello che ora e' il «ripiego dichiarato». Da riscrivere con l'ordine: modello nuovo prima, ripiego dopo.
- Passo 1 «Which Shell unit» (r. 332-336): FALSO. `unit_shell()` oggi NON chiede il `FragmentPath` di `org.gnome.Shell@wayland.service`: legge i `Requires` di `gnome-session@<sessione>.target` e prende l'istanza `org.gnome.Shell@<x>.service` diversa dal template (`ubuntu` → `@ubuntu`, `gnome` → `@user`); «On trixie it is a real file ... the template unit of newer GNOME versions is not handled» e' ribaltato (GNOME 50: template; `SESSION_UNIT_SHELL_48` rimosso).
- Passo 2 «The drop-in» (r. 337-340): istanza giusta e `--mode=%i` (vedi 12.4); il `--mode` e' dove vivono dock e colori di Ubuntu.
- Passo 3 «previous session must be over»: tre unita' (aggiunta `graphical-session.target`).
- Passo 4 «Capture and input»: vale l'ordine in `mutter.c` (non toccato in quella parte). Aggiungere Mutter 50: ogni cambio monitor ripubblica i parametri del flusso (rinegoziazione in piu' dopo ogni resize; studio 4 §2, [V codice Mutter; effetto S]); libeis 1.5.0: il `ping` risponde dopo l'input thread (studio 4). Non verificato nel codice del manuale.
- Nuovo: scala. `DCONF_KEYS` ha 2 chiavi nuove (session.c): `org.gnome.desktop.screensaver ubuntu-lock-on-suspend` = false e `org.gnome.desktop.interface scaling-factor` = `uint32 1` (valore + blocco). Rete di sicurezza in `child.c`: se la scala letta non e' 1 il figlio tenta UNA volta `mutter_scale_to_one()` (`ApplyMonitorsConfig` metodo 1 = temporaneo, mai `monitors.xml`; solo caso a un monitor logico, il nostro; tempo massimo ~45 s, 3 chiamate da `WAIT_CALL_MS` 15 s); se fallisce, `MSG_STAGE` porta `fatal = 1`, i client ricevono 0x0E e il figlio chiude la sessione (`scale_refused`, ritentata ogni 10 s). Il testo attuale dice (r. 392-393 del codice) di impostare a mano `scaling-factor 0`: superato.
- Sezione «The session dconf»: la tabella «three layers» (r. 374-382) e il testo sull'`input_layout()` nel database in memoria `service-db:shm/remotix` descrivono il ripiego; il modello nuovo ha profilo `$XDG_RUNTIME_DIR/dconf/profile` = prima riga della base, `system-db:remotix` (blocchi, `/etc/dconf/db/remotix`, compilato dal `postinst` da keyfile generati in costruzione con `remotix --dconf-keyfiles DIR`; il servizio lo ricompila all'avvio se manca o differisce: `session_dconf_system_db_ensure()` chiamata in `rootside_main()`), `user-db:remotix` (`~/.config/dconf/remotix`, scritto dal servizio dconf come `/ca/desrt/dconf/Writer/remotix`), resto della base; nessun `DCONF_PROFILE`. «dconf 0.40» (r. 372): Ubuntu 26.04 ha dconf 0.49 (registro C5); Debian 0.40 «non misurato» con il modello nuovo. Nota: `dconf-cli` resta Recommends (`debian/control`) e senza di esso scatta il ripiego. Motivo del cambio: i programmi Flutter/snap non digeriscono righe `file-db`/`service-db` (registro C5).
- Da AGGIUNGERE: file `lock-warning-shown` (vedi 12.1); `session_life()` tre esiti per il file runtime all'avvio del figlio (SCONOSCIUTO = non tocca nulla); casi non provati sul campo (registro C5: vita sconosciuta, database «diverso/piu' vecchio»); aggiornamento a caldo con desktop nato dal vecchio modello.
- «Inhibition» (r. 411-413): non toccata, vale.
- «Declared fallbacks» (r. 404-410): vale come ripiego; la frase «what the user changes from the remote desktop is lost at the next birth» e' del solo ripiego.

### 12.7 «KDE Plasma: KWin nested in labwc» (r. 431-529) — DA RISCRIVERE
Motivo: con KWin >= 6.5 il labwc della distribuzione non funziona e la sezione assume il labwc di sistema.
- Intro (r. 431-437), tabella «Why KWin runs inside labwc», passo 2 della «start line» (r. 458-461): «It finds `labwc` in `PATH` (the distribution's; there is no REMOTIX-built labwc in this tree)... `labwc` is a Recommends» e' FALSO. Ora `kwin_nested_alive()` esegue il labwc del pacchetto in `/usr/libexec/remotix/labwc` (percorso fissato a costruzione: `src/Makefile` `LABWC ?= ...`, `-DREMOTIX_LABWC`, `debian/rules LABWC_PATH`); senza di esso: ripiego `--virtual` dichiarato con riga «⛔ our labwc is not installed». Causa (labwc-ospite/README): KWin >= 6.5 disegna un pixel nero come radice e mette il contenuto in subsurface; wlroots non lo riporta mai come «presented», KWin da' ai client un orologio fermo, Firefox si crede coperto. Pacchetto: labwc 0.9.3 + wlroots 0.19.2 con la patch `wlroots-0.19.2-remotix-presented-root.patch`, wlroots LINKATO STATICO, sorgenti con sha256 in `VERSIONS`; `control`: Build-Depends meson, patch, hwdata, wayland-protocols, libegl-dev, libgles-dev, libinput-dev, libpixman-1-dev, libseat-dev, libudev-dev, libdisplay-info-dev, libxml2-dev, libcairo2-dev, libpango1.0-dev, libpng-dev; `Static-Built-Using` aggiunge labwc 0.9.3 e wlroots 0.19.2; `copyright` documenta la GPL-2/Expat; il labwc della distribuzione e' usato solo da XFCE e LXQt. Il `labwc` Recommends serve quindi solo a XFCE/LXQt.
- Tabella «Choice / Why» riga «Not `kwin_wayland --virtual`: KWin 6.3.6...»: misura di Debian; su KWin 6.6.7 non e' stata rifatta (non verificato). Tutti i riferimenti a «KWin 6.3.6» da togliere o dichiarare.
- Tabella «Traps»: aggiungere la trappola del 6.5 (sopra). `TICKER_MS` 16, `HOST_MHZ` 240000, `HOST_BIRTH_MS` 10000: confermati (grep in `kwin.c`).
- Nuovi pezzi in `kwin.c` da descrivere: (a) il sidecar `org.freedesktop.ScreenSaver` (`screensaver_alive()`, secondo fork accanto al ticker; Plasma >= 6.4: Ctrl+Alt+Del non apriva il logout perche' `GetActive` falliva con `ServiceUnknown` e veniva letto «schermo bloccato», dato che KWin parte con `--no-lockscreen`); risponde «non bloccato», `Lock/Throttle/UnThrottle` danno `NotSupported`, `Inhibit` e' INOLTRATO a powerdevil `org.freedesktop.PowerManagement.Inhibit` (misurato con VLC) e restituito all'uscita del chiamante; `DO_NOT_QUEUE`; muore con il cgroup dell'unita'. (b) `kwin_poke()` (kwin.h, 19 nov): ricommit con danno del pixel trasparente in alto, per far disegnare a KWin un fotogramma (`capture_frame_lost()`; `GMutex pixel_lock`); `capture_watch_sequence()` conta i buchi nei numeri di buffer di KWin.
- «Capture, input, cursor, clipboard» e nota «Remedy text»: non toccati (`kwin_check_permission()`, RX-KDE-001..003 non sono nel diff): vale. `debian/org.kde.remotix.desktop` esiste ancora nel pacchetto (non verificato su `remotix.install`, ma `debian/` non e' cambiato per quel file).
- Il blocco `code` con `ExecStart=...kwin_wayland_wrapper --xwayland --width ... --no-lockscreen`: coerente con `write_dropin()` (non nel diff); vale.

### 12.8 «XFCE: labwc and a locked xfconf» (r. 534-595) — DA CORREGGERE
- Paragrafo «The panel» (r. 573-581): le plugin `actions` e `whiskermenu` ora sono nei file di blocco come `<property name="plugin-N" type="empty">` (non piu' `type="string" value="actions"/"whiskermenu"`): regola «only the LEAF keys we lock are defined there» (D-X3, `xfce_panel_xml()`); altrimenti `xfconfd` non scrive nel file utente un valore uguale a quello di sistema e, tolto il blocco, il plugin restava senza tipo e spariva. Nuovo `xfce_panel_integrity()` (a ogni nascita, in `xfce_session_xfconf()`): ripara una sola volta i `/plugins/plugin-<id>` senza tipo, dal copy in sospeso o dal `default.xml` ma SOLO per i tipi che blocchiamo (`PLUGIN_ACTIONS`, `PLUGIN_WHISKER`), mai se `xfconfd` ha ancora il blocco in memoria (`xfconfd_holds_lock()`: legge `/proc/<pid>/environ` cercando `/remotix/xdg-xfce`). `xfce_restore_copy()` usa `xfce_copy_group_type()`. Su Xubuntu il pannello non ha il pulsante `actions`, solo whisker (studio 7), quindi il blocco del whisker e' l'unica protezione delle voci di spegnimento.
- Nota «Lock syntax» (r. 591-595): cita xfce4-session 4.20.2 (misura del 13 nov su Debian): su Ubuntu e' 4.20.4; la misura sul blocco `locked="*"` non e' ripetuta (non verificato).
- Da AGGIUNGERE: `session_autostart_cover()` (session.c, 19 nov): voce `blueman.desktop` con `Hidden=true` nella cartella `autostart` di `labwc-xfce` (prima in `XDG_CONFIG_DIRS`) perche' `blueman-applet` crasha (corsa con `obexd`, 5 su 90) e copre lo schermo con la finestra apport; misurato: una voce `Hidden=true` nasconde il nome del file ovunque, quindi nasconde anche `~/.config/autostart/blueman.desktop` visibile dell'utente; il file non si toglie a fine sessione (sparisce con `/run/user/<uid>`). Lista `SESSION_NOT_IN_REMOTE_AUTOSTART`.
- Tabella «How XFCE is kept» e tabella `XFCE_LOCKS`: non toccate nel diff; valgono (grep `XFCE_LOCKS`: nessun hunk). Sfondo nero (registro E1): causa `libxfce4windowing` 4.20.2; Ubuntu ha 4.20.5, atteso risolto, «da verificare con una foto» (studio 7): non verificato.

### 12.9 «LXQt: labwc folder and session commands» (r. 600-638) — DA CORREGGERE
- Prima frase (r. 600-604) «Debian trixie packages no launcher for LXQt on Wayland»: su Ubuntu esiste `lxqt-wayland-session` 0.3.1 ma Lubuntu NON lo installa (studio 7 §3.1); il codice non lo cerca. Riformulare per Ubuntu.
- Riga «The session's commands»: oggi `lxqt_session_commands()` scrive, oltre a `lxqt-leave` e `lxqt-powermanagement`, (a) script no-op per i compositori X11 `picom`, `compton`, `xcompmgr` (`LXQT_X11_COMPOSITORS`: il `picom` di Lubuntu e' un modulo senza `X-LXQt-X11-Only`, muore, lxqt-session lo riavvia fino a `MAX_CRASHES_PER_APP` e mostra «X Compositor crashed too many times»; il no-op esce 0 e un modulo che esce 0 non viene riavviato), (b) `lubuntu-update` (`LXQT_SHARED_SERVER_PROGRAMS`: conta i processi di TUTTI gli utenti, quindi la copia del secondo utente esce 1; il sistema lo nomina per percorso assoluto, percio' una voce di autostart della sessione con lo stesso nome file, `lubuntu-update-autostart.desktop`, NON `Hidden=true`, lo copre e avvia lo script per nome), (c) la copertura `blueman.desktop` (`Hidden=true`, come XFCE). Le pezze sono scritte solo se il programma e la voce di sistema esistono; altrimenti si toglie solo cio' che e' nostro (`X-REMOTIX`). Riga di registro cambiata: «`%d` X11 composition manager(s) and `%d` program(s) that count every user's processes».
- Riga «Menu entries» e «Idleness and lock»: valgono. «Environment»: vedi 12.3 (`XDG_SESSION_DESKTOP`).
- «The one-time restore» e «Exit»: nessun hunk in `restore_user_settings_lxqt()`/`exit_lxqt()`: valgono; il numero «16 volte su 20» e' una misura di Debian (non ripetuta).
- Versioni citate nel codice (lxqt-session 2.1.1, lxqt-panel 2.1.4) sono vecchie: Ubuntu ha 2.3.0/2.3.2 (studio 7 punto 8 chiede di ricontrollare i commenti).

### 12.10 «What the session imposes, desktop by desktop» (r. 643-677) — DA CORREGGERE
- Frase d'apertura: «everything lives under `$XDG_RUNTIME_DIR` ... the two exceptions» → vedi 12.1: quattro eccezioni; elencare `~/.config/dconf/remotix` e `~/.local/share/gnome-shell/lock-warning-shown`.
- Riga GNOME (gia' ritoccata nel ramo): `/etc/dconf/db/remotix` + `$XDG_RUNTIME_DIR/dconf/profile` + `~/.config/dconf/remotix` e' giusto, ma la colonna «Where it lives» tiene ancora `$XDG_RUNTIME_DIR/remotix/dconf/` e «the in-memory dconf layer» come valori principali: sono il ripiego. Aggiungere `--mode=%i`, le due chiavi nuove e il file `lock-warning-shown`.
- Righe XFCE e LXQt: aggiungere le coperture di autostart (`blueman`; LXQt anche `lubuntu-update` e i compositori X11). Riga LXQt «two command scripts»: ora sono piu' script.
- Riga KDE: invariata nel diff (`write_kde_menu_rules()` non toccato); aggiungere (non e' un'impostazione) il sidecar ScreenSaver.
- «KDE's powerdevil inhibition» e «The checks are the log»: valgono (`powerdevil_guard()`, `POWERDEVIL_STEP_US` 2 s, `POWERDEVIL_PATIENCE_S` 120: grep conferma). Il rinvio a `/usr/share/remotix/belts/` e `debian/rules` vale (rules non cambia su quella parte).

### 12.11 «Behaviours of the four desktops worth knowing» (r. 682-712) — DA CORREGGERE
- L'intera sezione cita «PIANO.md status of 17 Nov 2026» (Debian); su questo ramo PIANO.md e' un'altra cosa. Le fonti utili per Ubuntu sono `docs/REGISTRO-problemi.md` D e E. Righe da riportare con fonte nuova: GNOME nasce nella Panoramica (registro D); XFCE ignora un Log Out chiesto mentre parte (confermato su 4.20.4, studio 7); XFCE angolo coperto dal pannello, `pkexec` e primo tocco su GNOME (E2).
- Righe da togliere o dichiarare «non verificato su Ubuntu»: «KDE: Delete key held down» (viene dal PIANO.md di Debian, non e' in registro/E2 di Ubuntu); «All: max canvas 3840x2160 ... test browser's decoder» (idem; vedi anche il «declared limit» 3K in ch14); «GNOME: pkexec ... SHELL empty» resta (E2).
- Riga AppArmor «tried on a real Debian 13 VM only up to the connection»: FALSA per Ubuntu. Registro C4: prima prova del proprietario su live Ubuntu 26.04.1 (kernel 7.0), ogni accesso rifiutato per `deny unix addr=@*`; corretto. Vedi ch14 §4.
- Da AGGIUNGERE: KDE Log Out nei primi secondi su Plasma 6.6 (registro D, lezione sul lavoro non salvato); E3 (foto del gestore utente vecchia; «non ho potuto guardare» trattato come «chiuso» in `session_alive()`/`child.c`: nella preparazione dconf corretto il 19 nov, negli altri due punti no); E4 (scatti video da Chrome su Android, non distinto); E1 sfondo nero XFCE.
- Elenco «Places that differ per desktop»: aggiungere `session_missing_component()`, `session_life()`, `local_session()`, `unit_shell()`, `session_over_early()` (child.c).

---------------------------------------------------------------------------------------------------

## ch13_login — «Login and its defences» — 421 righe — 10 sezioni

Controllo generale: `src/rcp.c` ha nel diff solo la funzione `rcp_admitted_waiting()` (+8 righe); `src/rootside.c` solo la chiamata a `session_dconf_system_db_ensure()` in `rootside_main()`; `authentication.c`, `helper.c`, `rootside.h`, `rootside_proto.h`, `command.c`, `page.c` NON compaiono nel diff `src.diff`. Le costanti (LIMIT/WINDOW/LADDER, 2500/1000/12000 ms, 16/2/8000/20, `RXR_*`) non cambiano. Resta la questione dei tempi di PAM misurati (su Debian): su Ubuntu `pam_sss` e `pam_motd` con `update-motd.d` (studio 5 §3.1: «latenza al login [S] da misurare») possono dare tempi diversi; il pavimento 2500 ms e' una costante, non una misura.

### 13.1 «The path of one login attempt» — VALE COM'E'
Controllo: nomi di funzioni e file (`handle_credentials()` in rcp.c, `handle_auth()` in rootside.c, `dispatcher()`/`grandchild()` in helper.c) assenti dal diff; il codice cambiato in `rootside.c` non e' nel percorso di login.

### 13.2 «The PAM service file remotix.pam» (r. 44-104) — DA CORREGGERE
- «The file mirrors Debian's own `/etc/pam.d/sshd` line by line» (r. 49) e «15 lines equal out of 15 ... 30 Sep 2026» (r. 53): su Ubuntu va detto che `remotix.pam` (esclusa la riga `pam_listfile`) e' uguale riga per riga a `/etc/pam.d/sshd` di Ubuntu 26.04 (openssh-server 1:10.2p1-2ubuntu3.8), 15 su 15, studio 5 §3.1 [V, estratto da pacchetto in contenitore]; il confronto sulle immagini live installate e' rimandato (studio 11, S5.P6 «RIMANDATO»). Intestazione di `src/remotix.pam`: dice ancora «⭐ DEBIAN 13 ONLY» e cita altre famiglie (r. 1-5, 31): testo da correggere nel file sorgente, il manuale non deve ripeterlo.
- Tabella «The four PAM stacks», riga `session`: la lista di moduli e' quella di sshd e resta; la parte «pam_systemd ... inside common-session»: su Ubuntu 26.04 `common-session` ha `pam_umask`, `pam_unix`, `optional pam_sss.so`, `optional pam_systemd.so` (studio 5 §3.1) e la riga `pam_exec` di REMOTIX (Priority -1) va DOPO `pam_systemd` (studio 2 §3.5, 8 §N.3; `S8.11 VERIFICATO: prelocal 6 PASS sui quattro gusti`). `pam_motd motd=/run/motd.dynamic` su Ubuntu esegue `/etc/update-motd.d/*` a ogni apertura: latenza non misurata. Nuovo nel diff: commento in `remotix.pam` sopra `pam_env`: il PATH della sessione viene da quella riga; NON aggiungere `user_readenv=1`.
- Tabella riga `auth`: `common-auth` di Ubuntu con `libpam-sss` ha `pam_unix.so nullok` poi `pam_sss.so use_first_pass` (studio 5 §3.1): conferma che `PAM_DISALLOW_NULL_AUTHTOK` (13.3) e' necessario. `pam_faillock` c'e' ma non e' abilitato di serie su Ubuntu (nessuna riga in common-auth).
- «On Debian `/etc/pam.d/login`...» (r. 84) e warn «on Debian includes the common stacks» (r. 88-92): per Ubuntu `/etc/pam.d/other` = `@include common-*` come Debian (studio 5 §3.1 [V]), quindi il warn vale; il testo «on Debian» va sostituito con «on Debian and Ubuntu».
- Nota «Stale text» (r. 97-104): resta vera, `look_pam_service()` in `main.c` non e' nel diff (stringa «src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch» e «pam_deny on Fedora and Arch»). Il rinvio a `apt install --reinstall remotix` vale.
- Paragrafo `pam_exec` di `common-session` (r. 75-83): vale; `debian/remotix.pam-config` identico (studio 8: «formato pam-auth-update identico»).

### 13.3 «One PAM transaction in authentication.c» — VALE COM'E'
Controllo: `authentication.c` assente dal diff. Il «16 Nov 2026» sulla misura `nullok` e' su Debian; l'effetto vale anche per Ubuntu (common-auth `pam_unix.so nullok`, studio 5).

### 13.4 «The PAM helper: dispatcher and grandchild» — VALE COM'E'
Controllo: `helper.c`/`helper.h` assenti dal diff; costanti `MAX_IN_FLIGHT` ecc. non toccate. I tempi citati («1.0 to 2.2 s», mediane 2123/2198/1086 ms) sono commenti di Debian: «non verificato su Ubuntu».

### 13.5 «The fixed answer time and the floor of a refusal» — VALE COM'E'
Controllo: `FIXED_DELAY`, `REJECT_FLOOR`, `VERDICT_CAP` in rcp.c, nessun hunk. Per Ubuntu: nome inesistente con `sss` in `nsswitch.conf` (`passwd: files systemd sss`): la risposta e' uno 0x07 normale al pavimento perche' l'errore di ricerca NSS e' gia' trattato come rifiuto (`root_user_lookup()`/`user_refused_as()`, studio 5 §3.2 e studio 11 S5.§N.7: riga di `check-ban` VERIFICATA con `sss`, rischio «basso»).

### 13.6 «The three counters and the progressive ban» — VALE COM'E'
Controllo: `LIMIT[]`, `WINDOW_MS[]`, `LADDER_MS[]`, `MAX_ATTEMPTS`, `BAN_QUOTA`, file di ban: nessun hunk in rcp.c su quelle. Nota solo di prova: sulle VM QEMU ogni client appare come `10.0.2.2` (`prove/check-ban.py` `ADDR`), irrilevante per il prodotto.

### 13.7 «The root side's own bounds on logins» — VALE COM'E'
Controllo: `RXR_AUTH_*`, `ROOTSIDE_LOGIN_*`, `RXR_GRANT_LIFE_MS` in `rootside.h`; l'unico hunk di rootside.c e' la chiamata dconf all'avvio.

### 13.8 «No administrator unblock, by design» — VALE COM'E'
Controllo: `command.c`, `check-ban.py` (`unblock-shipped`): unico hunk in check-ban e' `ADDR`/messaggio di pulizia; `debian/remotix.service` non e' nel diff.

### 13.9 «What the login logs and what it never logs» — VALE COM'E'
Controllo: `log_user()`, `rcp_log_tag()`, `name_for_log()` non toccate. Per Ubuntu: anche `pam_sss` (se presente) scrive nel journal con il nome: stessa categoria delle «righe dei moduli PAM» gia' dichiarate (non verificato che lo faccia).

### 13.10 «Login defences against SPECS» — VALE COM'E'
Controllo: tabella di confronto SPECS/codice; nessun numero toccato dal diff.

---------------------------------------------------------------------------------------------------

## ch14_security — «Security model» — 463 righe — 10 sezioni

### 14.1 «Trust boundaries and the processes of the service» — VALE COM'E'
Controllo: `walls.c`, `rootside_proto.h`, `remotix.sysusers`, `remotix.service` non nel diff; processi e permessi invariati. (La riga «AppArmor ... complain mode» e' coerente con `flags=(complain,attach_disconnected)` del profilo del ramo.)

### 14.2 «The closed list between the network side and the root side» — VALE COM'E'
Controllo: `rootside_proto.h` non nel diff; `RXR_VERSION` 3, `RXR_LOCAL_COMING` 110, `RXR_GRANT_LIFE_MS`, `ROOTSIDE_ORPHAN_*` non toccati.

### 14.3 «The walls of the network side» — VALE COM'E' (con riserva di prova)
Controllo: `walls.c` assente dal diff; studio 5 §1.1: `kernel.apparmor_restrict_unprivileged_userns=1` non riguarda REMOTIX (namespace creati da root; il filtro seccomp nega `CLONE_NEWUSER`) [V per il codice, comportamento del kernel Ubuntu 26.04 «S»]. Riserva: «kernel 5.12» e «Landlock ABI 6 (kernel 6.12)» non sono stati ripresi per il kernel Ubuntu 7.0; il login su macchina vera (registro C4) dimostra solo che il lato rete parte, non quale ABI Landlock viene applicata. Il contenitore degli studi gira sul kernel Debian 7.3 del server (studio 5, limite).

### 14.4 «The AppArmor profile and its mode» (r. 147-181) — DA RISCRIVERE
Motivo: la storia verificata e' un'altra (registro C4) e il profilo e' cambiato in tre punti.
- Tabella «Denied: `deny ptrace`, `deny mount`, `deny unix addr=@*`»: FALSO. Ora `deny unix (bind, listen) addr=@**,` e `deny unix (connect, send, receive) peer=(addr=@**),`. Motivo (`debian/remotix_network.apparmor`, registro C4): la riga con `addr=@*` includeva anche `create`, che non ha indirizzo; sul kernel di Ubuntu (che media i socket unix) vietava TUTTI i socket locali, e un `deny` vale anche in complain: niente D-Bus, niente logind, ogni accesso rifiutato (`logind unreachable (Unable to create socket: Permission denied)`). Due asterischi perche' uno si ferma alla `/`. Limite noto: resta permesso l'autobind.
- Tabella «Files»: aggiungere `/usr/share/xkeyboard-config-2/**`, `/usr/share/xkeyboard-config-2.d/**`, `/etc/xkb/**`, `/etc/X11/xkb/**` (xkb-data 2.46: `/usr/share/X11/xkb` e' un symlink, AppArmor giudica il percorso risolto). Aggiunta `include if exists <local/remotix_network>` (file creato vuoto da `dh_apparmor`: l'amministratore puo' aggiungere regole).
- Riga «No capability»: «No `capability` line at all» → il profilo non ne elenca, ma `abstractions/nameservice` → `nis` porta `capability net_bind_service` (innocuo: bounding set vuoto; commento del profilo).
- Paragrafo «What was verified» (r. 168-176) e nota «State of the profile» (r. 177-179): sono di Debian («real Debian 13 virtual machine ... no video card», 17 Nov). Su Ubuntu: il profilo e' in complain; la prima prova su macchina vera (live 26.04.1, kernel 7.0, 19 nov) ha trovato il difetto C4; dopo la correzione misurato: bus di sistema e journal raggiungibili, socket astratti ancora rifiutati, controllo sessioni locali «CONNECTED». Il proprietario ha poi provato a mano le quattro VM e le quattro live (PIANO.md). NON risulta un conteggio documentato di righe DENIED/ALLOWED in complain durante una sessione: «non verificato»; il profilo non e' stato spostato in enforce e la regola «non in enforce senza una sessione osservata» resta (registro C4: «da riguardare quando passera' a enforce»; studio 5 §1.4: restano da verificare le regole `dbus`). Le regole per `/proc` restano «not tried».
- «installed as /etc/apparmor.d/remotix_network ... dh_apparmor» e postrm `.remove`: valgono (`rules`/`postrm` invariati su quel punto). `apparmor` 5.0.2 di Ubuntu parsa il profilo senza avvisi (studio 5 §1.3, `apparmor_parser -QTK -S`).
- `check-package.py` check `apparmor`: «in containers ... answers BLOCKED»: nei contenitori AppArmor non e' in vigore (registro C4); i contenitori non esistono piu' come banco (PIANO.md: banco su VM).

### 14.5 «Local excludes remote and the session cap» (r. 184-233) — DA CORREGGERE
- Il testo dice che `0x0E` copre cinque/diverse strade; ora ce n'e' una sesta: «the desktop's compositor is not installed» (`main.c` `delivery_verdict()`, `session_missing_component()`; `page.html` aggiorna il commento a «SIX routes»). Da aggiungere dove si parla di «cannot verify» e «session cap» come cause di 0x0E; il padre non spawna il figlio, nessun processo, nessuna sessione logind. Il testo della pagina resta generico.
- Seconda causa nuova di 0x0E: il rifiuto dello stage per la scala (`MSG_STAGE` con `fatal`, `stage_refused_by_child()` → `RCP_SESSION_UNSERVABLE`, vedi 12.6).
- Difesa 3 «in the child»: l'ordine cambia: `local_found_by_child()` ora arriva PRIMA della chiusura leggera (avviso ai client 0x04 subito, la chiusura puo' aspettare PipeWire fino a 25 s). `session_ended_by_child()`/`dismiss_child()` usano `wt_dismiss_user_session_over()` (non `wt_dismiss_user()`): un login in attesa di PAM o con «no» trattenuto non riceve il falso 0x10; un login ADMITTED nel secondo fisso riceve 0x10 al posto di ADMITTED (`rcp_admitted_waiting()`).
- Numeri del cap (`RCP_SESSION_CAP` 10, limite dichiarato 8, `0x0F` per il secondo dispositivo): non toccati (rcp.h nel diff aggiunge solo `rcp_admitted_waiting`). Valgono.

### 14.6 «The local-login hold» — VALE COM'E'
Controllo: `local_login.c`, `pl_step()`/`PL_*` in rootside.c e `remotix.pam-config` non nel diff. Per Ubuntu: la riga `pam_exec` finisce dopo `pam_systemd` (studio 2 §3.3-3.5) e il gancio scatta per gdm, sddm, lightdm (tutti includono `common-session`, studio 5 §3.1; `prelocal` 6 PASS su quattro gusti, studio 11 S8.11). Il greeter di sddm/lightdm: «da provare» (S).

### 14.7 «The denied-users list» — VALE COM'E'
Controllo: `user_refused_as()`, `pam_listfile` (remotix.pam diff solo commento), `debian/denied-users` non nel diff.

### 14.8 «Polkit rules, password windows and the power belts» (r. 314-367) — DA CORREGGERE
- `sentinel_shutdown_forbidden()` (non citata nel testo ma legata a «`CanPowerOff` and its siblings answer no»): ora accetta anche `na` («non disponibile qui», VM/server) come sicuro quanto `no`, e un errore resta allarme ma il dettaglio nomina la chiamata e l'errore (`sentinel.c`, `sentinel.h`). Il testo «answer no» → «no (or na)».
- Versioni: polkitd 127-2ubuntu1.1 su Ubuntu (le regole sono state scritte per 126, studio 5 §6); gruppi amministratori: Ubuntu `49-ubuntu-admin.rules` → `sudo` e `admin` (la regola 40 gia' li copre). `polkit.service` identico a Debian (sandbox stretta; l'helper `remotix-polkit-seated` legge solo `/run/systemd/sessions/*`).
- `remotix-polkit-seated`: «reads logind's state files»: con systemd 259 i file di stato mantengono `SERVICE=`, `USER=`, `SEAT=`; il `.ref` che l'helper saltava non esiste piu' (innocuo; studio 5 §7.1.3).
- «`sudo systemctl poweroff` keeps working»: su Ubuntu `sudo` e' sudo-rs 0.2.13; `check-desktop.py` e' stato adattato per i messaggi di sudo-rs («I'm afraid I can't do that», «interactive authentication is required»); l'effetto sulla regola non cambia. Non verificato che `sudo-rs` conservi `CAP_SYS_BOOT` (e' root; logica identica).
- I snap (`io.snapcraft.snapd.*`: `auth_admin`/`auth_admin_keep` anche da seduti) non chiedono finestre non richieste: nessuna estensione della regola 40 (studio 5 §2.2 [V]).
- «The other two belts ... not active»: invariato (`debian/rules` non cambia su quel punto).

### 14.9 «The service unit and why it is not sandboxed» — VALE COM'E'
Controllo: `remotix.service` non e' nel diff. Nuovo (non contraddice nulla): `debian/needrestart/remotix.conf` installato in `/etc/needrestart/conf.d` (`$nrconf{override_rc}{qr(^remotix\.service$)} = 0`): needrestart non riavvia da solo il servizio (riavviare chiude ogni desktop, §11.56). Va nel capitolo sul pacchetto, con rinvio da qui.

### 14.10 «What the security model does not defend» (r. 402-450) — DA CORREGGERE
- Riga «AppArmor in a session»: «never observed during a session» → vedi 14.4 (C4).
- Riga «What the package changes on the machine»: la lista e' incompleta. Da aggiungere: il database di sistema `/etc/dconf/db/remotix` (creato dal postinst, tolto da postrm a remove/purge); il file utente `~/.config/dconf/remotix` (purge come utente, solo quel file regolare); il file `~/.local/share/gnome-shell/lock-warning-shown`; il binario `labwc` proprio in `/usr/libexec/remotix/labwc` (GPL-2, programma separato); la regola needrestart. Le due voci esistenti (riga `pam_exec`, `usermod -aG` con `group-enrollments.jsonl`, ACL `render-grants`) sono nei file non toccati dal diff (`rootside.c`/`child.c` solo hunk non pertinenti): valgono; il gruppo `render` esiste su Ubuntu come su Debian (studio 5 §6, `udev` sysusers).
- Riga «Hardware and clients not tried»: «NVIDIA (deferred) ... Samsung DeX ... 3840x2160 ... declared limit 3K»: fonte Debian (PIANO.md 17 nov); su Ubuntu non verificato (l'unica nota hardware nuova e' la Radeon dei test VM, `server/vm-radeon*.sh`).
- Riga «Kernel facilities»: come 14.3, kernel Ubuntu 7.0: «non verificato».
- Aggiungere: il registro E3 (variabili del gestore utente) come limite noto non bloccante.

---------------------------------------------------------------------------------------------------

## Conteggio

| Capitolo | Sezioni | Vale com'e' | Da correggere | Da riscrivere |
|---|---|---|---|---|
| ch12_desktops | 11 | 0 | 9 | 2 (12.6, 12.7) |
| ch13_login | 10 | 9 | 1 (13.2) | 0 |
| ch14_security | 10 | 6 | 3 (14.5, 14.8, 14.10) | 1 (14.4) |
| Totale | 31 | 15 | 13 | 3 |

---------------------------------------------------------------------------------------------------

## (a) COSE NUOVE di Ubuntu che il gruppo deve contenere e oggi mancano

1. ch12 §6 (riscrittura) o nuova sottosezione «GNOME 50 on Ubuntu»: sessione `ubuntu` scelta per nome os-release, istanze `org.gnome.Shell@ubuntu/@user`, `--mode=%i`, `graphical-session.target` come terza guardia, `AssertEnvironment=XDG_SESSION_TYPE=wayland` (job fallisce e `OnFailure=gnome-session-shutdown.target` ferma tutto), `gnome-session-init-worker`.
2. ch12 §6: modello dconf di runtime (database `/etc/dconf/db/remotix`, profilo `$XDG_RUNTIME_DIR/dconf/profile`, `user-db:remotix`, nessun `DCONF_PROFILE`, ripiego dichiarato, limiti noti del registro C5, `session_dconf_keyfiles_write()`, `session_dconf_system_db_ensure()`), con la tabella in ordine nuovo.
3. ch12 §6: scala forzata a 1 (due chiavi dconf + `mutter_scale_to_one()` + rifiuto fatale 0x0E + chiusura sessione).
4. ch12 §6/§10: file `lock-warning-shown` (marchio, tolto a fine sessione).
5. ch12 §7 (riscrittura): labwc proprio del pacchetto (README, VERSIONS, patch wlroots, costruzione statica, `REMOTIX_LABWC`), sidecar `org.freedesktop.ScreenSaver`, `kwin_poke()`, `capture_watch_sequence()`.
6. ch12 §4/§5: assenza di `--session-fd` (pidfd di systemd 259); `session_life()` a tre esiti; `session_over_early()`; chiusura KDE con `plasma-shutdown`/`isShuttingDown` e 10+10 tentativi `fail`/`replace`.
7. ch12 §2: mappa xubuntu/lubuntu/kubuntu/ubuntu; Xubuntu con entrambi i marcatori GNOME risolta dalla dichiarazione di lightdm.
8. ch12 §3: cartelle di sessione come un login locale (`local_session()` vivo, `profile.d`, cartella comune `/usr/share/gnome`), `XDG_SESSION_DESKTOP` da sddm, `PATH` da PAM.
9. ch12 §8/§9: D-X3 (`xfce_panel_integrity()`, regola «solo chiavi foglia»); coperture di autostart (`blueman`, `lubuntu-update`) e no-op per picom/compton/xcompmgr.
10. ch12 §1/§4 + ch14 §5: `session_missing_component()` (labwc mancante → 0x0E con nome del pacchetto, postinst avvisa).
11. ch14 §4: AppArmor su Ubuntu (C4: sintassi dei `deny unix`, kernel che media unix, percorsi xkb, `local/`, `net_bind_service` da `nis`).
12. ch14 §5: sesta strada di 0x0E, `wt_dismiss_user_session_over()`, `fatal` in `MSG_STAGE`.
13. ch14 §6: `sentinel_shutdown_forbidden()` accetta `na`; sudo-rs; polkitd 127.
14. ch14 §9 / pacchetto: needrestart `override_rc`.
15. ch14 §10: elenco aggiornato dei cambiamenti al sistema (db dconf, file utente, labwc, needrestart).

## (b) Cose di Debian da TOGLIERE

- ch12 §1: tutto il paragrafo «Versions» (Debian 13, GNOME Shell 48.7, KWin 6.3.6, labwc 0.8.3, trixie gnome-session, `docs/PULIZIA-tranche1.md`).
- ch12 §3: paragrafo «On Debian 13 that script does not exist» (r. 142-143) e il rinvio `PULIZIA-tranche1.md` item 7.
- ch12 §4: tutto il racconto del fifo `.ref`, `--session-fd`, CLOEXEC, «measured on the four boxes».
- ch12 §5: «its lifeline fifo closes»; «at most `KDE_LOGOUT_TRIES` = 10 times».
- ch12 §6: «On trixie it is a real file» e `org.gnome.Shell@wayland.service` ovunque (r. 39, 333-336, 338); `dconf 0.40` come stato corrente; tabella «three layers» come modello principale.
- ch12 §7: «the distribution's labwc ... Recommends»; «KWin 6.3.6» come fatto corrente.
- ch12 §9: «Debian trixie packages no launcher for LXQt».
- ch12 §11: fonte «PIANO.md status of 17 Nov», righe Delete key e 3840x2160, riga AppArmor «real Debian 13 VM».
- ch13 §2: «Debian's own sshd», «on Debian», pur tenendo «Debian and Ubuntu» dove il fatto e' provato; ripetere le righe «DEBIAN 13 ONLY» dell'intestazione di `remotix.pam` (da correggere nel file).
- ch14 §4: paragrafo «What was verified» e nota «State of the profile» (Debian 13 VM); `deny unix addr=@*`.
- ch14 §8: «Hardware and clients not tried» come fonte Debian.

## (c) rif() incrociati verso altri gruppi e convenzioni di stile

Rif verso altri capitoli (titoli di sezione citati, da riallineare quando gli altri gruppi rinominano):
- ch12: «Startup and life cycle», «Where the log lines go», «Stopping the service», «Testing», «Security model», «The package», «Screen capture», «Input», «Video encoding», «Logging and diagnostics», «Performance and capacity», «Appendix C — Known issues and open points», «Extending REMOTIX and porting to another distribution» (quest'ultimo parla di porting: il gruppo che lo riscrive deve citare Ubuntu).
- ch13: «Overall architecture», «The RCP/1 protocol», «Security model», «Files the package installs», «The local-login hold», «Appendix C — Known issues and open points», «What the login logs and what it never logs», «Logging and diagnostics».
- ch14: «Overall architecture», «Login and its defences», «The local-login hold», «Files the package installs», «The PAM service file remotix.pam», «Startup and life cycle», «Quality, degradation and budget», «Stopping the service», «Transport», «Logging and diagnostics», «Testing», «Appendix C — Known issues and open points», «What the security model does not defend» (rif interno ch14).
- Il capitolo sull'«Appendix C» dovra' accogliere: E1-E4 del registro, C4/C5 come storia, le limitazioni dichiarate (autobind AppArmor, casi non provati C5).

Convenzioni di stile osservate: `p(..., lead=True)` per il primo paragrafo di sezione; `table(header, rows, "«TAB» — ...")` con titolo che inizia per `«TAB» —` o `«FIG» —` (trattino lungo); `flow([...], "«FIG» — ...")` e `fig(zone/box/arrow)` per le figure; `c()` per codice inline (anche per costanti, file, funzioni con `()`), `sysf()` per percorsi di sistema, `rif("Titolo sezione")` per i rinvii (il titolo deve combaciare con quello nel `CHAPTER`); `note(testo, "Etichetta breve.")` e `warn(...)` con etichetta finale; `ul([...])`, `steps([...])`; blocchi `code(testo, "text", didascalia)`. Tono: inglese asciutto, in prima persona assente, con «the comment records...» per i fatti presi dai commenti, date «17 Nov 2026», dichiarazioni esplicite «not verified here» / «declared fallback»; frasi come «Ubuntu 26.04 tree (19 Nov 2026)» nei paragrafi gia' aggiunti nel ramo. Per Ubuntu: citare studi e registro con `docs/REGISTRO-problemi.md` (voci C4, C5, D, E1-E4) al posto di `docs/PULIZIA-tranche1.md`, e `PIANO.md` solo per lo stato del ramo, non per fatti di Debian.


---------------------------------------------------------------------------------------------------

<!-- ===== frammento g4 ===== -->
# Gruppo g4 — capitoli 15 (Package), 16 (Logging), 17 (Testing), 18 (Build)

Albero: `~/Documenti/REMOTIX-UBUNTU`, ramo `ubuntu-26.04` (commit 50d997b). Fonti lette: i quattro capitoli per intero, `pacchetto.diff`, `prove.diff`,
`docs.diff`, le parti di `src.diff` che toccano log/sessione/main/kwin/rcp, studi 8, 11, 15, `giro2-*.md`, `PIANO.md`, file attuali di
`prove/`, `debian/`, `build/`. Non ho compilato né eseguito nulla. Sigle: «diff X» = file nella cartella `inv/`.

Riepilogo: 36 sezioni = 9 vale com'è, 23 da correggere, 4 da riscrivere.

---------------------------------------------------------------------------------------------------------------------------------------

## ch15_package.py — «The package» (332 righe, 7 sezioni)

### 15.1 «What the package is and how it is built» (S1) — da correggere
- Riga 4: «REMOTIX for Debian 13». Ora: pacchetto per Ubuntu 26.04 (suite `resolute`); `build/build-deb.sh` header (diff pacchetto, `build/build-deb.sh` riga 1).
- Riga 6-7: «in a `debian:trixie` container». Ora: `docker.io/library/ubuntu:26.04` (`build/Containerfile`: «FROM docker.io/library/ubuntu:26.04», universe già attivo nell'immagine base).
- Riga 11-13 elenco di ciò che il pacchetto fa alla macchina: manca che ora installa anche (a) il proprio `labwc` statico in `/usr/libexec/remotix/labwc`, (b) il file needrestart `/etc/needrestart/conf.d/remotix.conf`, (c) il database dconf di sistema `/etc/dconf/db/remotix` (compilato dal postinst, non nella lista dei file). Prove: `debian/rules` (`install -D … $(LABWC_PATH)`), `debian/remotix.install`, `debian/remotix.postinst` (blocco «19 Nov 2026»).
- Riga 21-30 (nota «Stale wording»): i commenti «the desktops survive the stop» valgono ancora nel ramo? Non verificato riga per riga; il diff cambia solo il commento del prerm (tolto «and holds its fifo»), quindi la nota resta, ma va aggiunto che `child.c` non passa più `--session-fd` (DECISIONS-11 §11.55, nota del 18 nov 2026: dal systemd 258 logind tiene la sessione per pidfd del leader).
- Riga 22-23: «the old multi-distribution product… engine/installer»: invariato (grep nei commenti; il diff non li tocca).

### 15.2 «Package metadata: Depends and Recommends» (S2) — da correggere
- Tabella: i nomi dei Depends non cambiano (`debian/control`: diff cambia solo Build-Depends, commenti, Static-Built-Using). Ma riga `Recommends labwc, wlr-randr, xwayland`: «and for KDE (KWin is born nested in a screenless labwc)» è falso. Ora KDE usa il labwc PROPRIO del pacchetto (`/usr/libexec/remotix/labwc`, labwc 0.9.3 + wlroots 0.19.2 patchato e statico); il labwc della distribuzione serve solo a XFCE e LXQt (commento di `debian/control`; `src/kwin.c`: `access(REMOTIX_LABWC, X_OK)`).
- Riga `Recommends dconf-cli`: «GNOME session rules are compiled with `dconf compile`; without it GNOME goes back to a declared fallback in which the user's changes made remotely are not kept». Ora: il postinst compila `/etc/dconf/db/remotix` dai keyfile in `/usr/share/remotix/dconf/remotix.d`; senza `dconf` il postinst avvisa e la sessione GNOME usa il ripiego dichiarato di 1.0.0 (tre strati a runtime, `DCONF_PROFILE`); il servizio, all'avvio, ricompila se il database manca o differisce (`session_dconf_system_db_ensure()`, chiamata in `rootside_main`).
- Riga `Recommends va-driver-all`: il testo regge; aggiungere che su Ubuntu è in `universe` (`libva-dev` pure) e che il driver VA di Mesa sta in `mesa-libgallium`, pacchetto reale che «provides» `mesa-va-drivers` (commento aggiornato in `debian/control`, studio 8 §1.2: `mesa-va-drivers` non esiste come pacchetto).
- Riga 72-75 `Static-Built-Using`: ora `ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0), labwc (= 0.9.3), wlroots (= 0.19.2)` (diff `debian/control`). Il controllo di `debian/rules` («test lines») riguarda ancora solo ngtcp2/nghttp3: labwc/wlroots sono fissati da `build/labwc-ospite/VERSIONS` con sha256.
- Riga 76-81 Build-Depends: aggiungere `meson, patch, hwdata, wayland-protocols, libegl-dev, libgles-dev, libinput-dev, libpixman-1-dev, libseat-dev, libudev-dev, libdisplay-info-dev, libxml2-dev, libcairo2-dev, libpango1.0-dev, libpng-dev` (diff `debian/control`). Il testo dice «There is no ffmpeg»: vale.
- Segnalare: `libva-dev`, `dh-apparmor`, `ninja-build`, `labwc`, `wlr-randr`, `va-driver-all`, `libseat-dev`, `meson` sono in universe su Ubuntu (studio 8 §1.2); su una macchina con solo `main` i Recommends non arrivano.

### 15.3 «The preinst refusals» (S3) — da correggere (solo l'ultimo paragrafo)
- Tabelle e testo delle due negazioni: valgono. Controllo: `debian/remotix.preinst` non è nel diff; `check-package.py` ha ancora il nome `preinst` (riga 38).
- Ultimo paragrafo (riga 107-112), «Verification»: cita «PIANO.md … 17 Nov 2026 … virtual machine… four desktops 8/8». Nel ramo Ubuntu `PIANO.md` contiene il riepilogo del 19 nov, non quei dati: sono storia di Debian. Per Ubuntu: «non verificato» (la VM Ubuntu `vm.sh` ora ha una `virtio-vga` che dà `/dev/dri/renderD128`, quindi la preinst non rifiuta: `server/vm.sh`, commento riga 4).

### 15.4 «The postinst: user, folders and encoding test» (S4) — da correggere
- Riga 120: «measured with debhelper 13.24.2 at compat 13: it installed nothing». Su Ubuntu: debhelper 13.31ubuntu1, `dh_installsysusers` ancora solo da compat 14 (studio 8 §1.2, `root_sequence.pm:51`): il passo manuale resta necessario. Da riscrivere il riferimento di versione.
- L'elenco dell'ordine di esecuzione manca di due blocchi nuovi del postinst (`debian/remotix.postinst`, diff): (1) dopo `systemd-tmpfiles`: «19 Nov 2026», compila `/etc/dconf/db/remotix` con `dconf compile` in un file temporaneo `remotix.new.$$`, `chmod 0644`, `mv -f`; avvisi su `stderr`: «remotix: ⚠ dconf (package dconf-cli) not found: /etc/dconf/db/remotix not made; the GNOME remote session will use its fallback» e «⚠ /etc/dconf/db/remotix could not be compiled…»; mai fa fallire apt. (2) dopo il test di codifica: avviso «remotix: ⚠ the package labwc is not installed (it is only a Recommends)…» emesso solo se `labwc` manca E c'è `xfce4-session` o `lxqt-session` E non c'è `gnome-shell` né `startplasma-wayland`; seconda riga «remotix:   install it: sudo apt install labwc».
- Riga 147-148: «the standard Debian way is `pam-auth-update`»: formula da neutralizzare («standard di Debian e Ubuntu»); «not tried» resta (non verificato su Ubuntu).
- Riga 156: l'avvertenza «the desktops stay alive» resta come nota a parte (vedi 15.1).

### 15.5 «Files the package installs» (S5) — da correggere
- Albero dei file (riga 159-187): aggiungere
  - `/usr/libexec/remotix/labwc` (0755, labwc statico senza libwlroots; `debian/rules`: `install -D -m 0755 debian/labwc-root$(LABWC_PATH) $(B)$(LABWC_PATH)`);
  - `/usr/share/remotix/dconf/remotix.d/` (keyfile generati IN COSTRUZIONE da `src/remotix --dconf-keyfiles`, tabella `DCONF_KEYS` di `session.c`; «una sola lista»);
  - `/etc/needrestart/conf.d/remotix.conf` (da `debian/needrestart/remotix.conf` via `debian/remotix.install`; contiene `$nrconf{override_rc}{qr(^remotix\.service$)} = 0;`; è sotto `/etc` quindi conffile);
  - creati a runtime e non elencati: `/etc/dconf/db/remotix` (postinst, rimosso da postrm a `remove|purge|disappear`).
- `debian/copyright` ha ora una sezione per `usr/libexec/remotix/labwc` («GPL-2 and Expat»); la lista dice «`/usr/share/doc/remotix/THIRD-PARTY-LICENSES`» e basta.
- «The AppArmor profile» (conffile `/etc/apparmor.d/remotix_network`): ora il profilo termina con `include if exists <local/remotix_network>` (diff `debian/remotix_network.apparmor`), quindi il file `/etc/apparmor.d/local/remotix_network` fatto da `dh_apparmor` è davvero incluso; cambiano le regole `deny unix` e i percorsi xkb (vedi cross-reference sotto, capitolo Sicurezza).
- Punto «The unit comes from debhelper» e «No benchmark file»: valgono (`debian/rules` righe BENCH_ON immutate).
- Riga 227-230 (nota Port and profile): non verificato per Ubuntu; il diff non tocca `remotix.service`, `remotix.conf` né `remotix.ufw`: vale.

### 15.6 «Removal: prerm, postrm and purge» (S6) — da correggere
- `postrm` (riga 271-292): a `purge` ora, con lo stesso passaggio `runuser` per ogni account (non più solo se esiste `~/.local/state/remotix`), toglie anche `~/.config/dconf/remotix` (solo se file regolare e non link; cartella `dconf` e file `user` mai toccati; home assenti saltate in silenzio) — `debian/remotix.postrm`, diff. Inoltre, a `remove|purge|disappear`: `rm -f /etc/dconf/db/remotix /etc/dconf/db/remotix.new.*`. L'elenco di purge nel capitolo non li nomina.
- Il blocco di AppArmor `.remove` e l'override lintian: invariati (diff non li tocca).
- `prerm`: il testo regge; il diff cambia solo un commento (tolto «and holds its fifo»).
- Riga 293-298 «Verification»: «real Debian 13 virtual machine… `check-package.py` 8/8 on the four desktops» è storia di Debian. Per Ubuntu: `check-package.py` ha gli stessi nove nomi (riga 38) ma non risulta eseguito su Ubuntu nei registri letti: «non verificato». Nota: nel banco VM il controllo è SKIP (`all.sh`, riga «skip package»: richiede `box.sh reset`).

### 15.7 «Service policy: installed disabled» (S7) — da correggere (incompleta)
- Tabella e `override_dh_installsystemd`: invariati (`debian/rules` non tocca quel passo): valgono.
- Manca la politica needrestart: su Ubuntu `needrestart` riavvierebbe da solo `remotix.service` dopo un aggiornamento di una libreria (libc6, libssl3, libpam…), chiudendo ogni desktop remoto; con `/etc/needrestart/conf.d/remotix.conf` il servizio compare solo sotto «Services to be restarted manually» (commento del file; effetto non osservato dal vero: studio 11 voce P9, «RIMANDATO»). Il testo cita già «Warn the users before upgrading»: va integrato.

---------------------------------------------------------------------------------------------------------------------------------------

## ch16_logging.py — «Logging and diagnostics» (522 righe, 12 sezioni)

Controllo di base: `src/log.c` e `src/log.h` NON sono nel diff `src.diff` (elenco dei file toccati: capture, child, input, kwin, main, mutter, page.html, rcp, remotix.pam, rootside, sentinel, session, webtransport + header).

### 16.1 «The log module» (S1) — vale com'è
Controllo: log.c/log.h assenti dal diff; `log.c:392 char buf[4096]`, `log.c:31 stderr_is_journal` presenti. Il `kwin_nested_alive()` citato come fuori dall'imbuto esiste ancora (`main.c:2887`, `kwin.c` stampa «remotix --kwin-nested: …»).

### 16.2 «Anatomy of a log line» (S2) — vale com'è
Controllo: stesso (nessuna modifica a `line()`); le cifre (23 righe orfane su 28 035, 48 caratteri) sono commenti di `log.c`, invariati.

### 16.3 «Log areas» (S3) — vale com'è
Controllo: nessun nuovo file `.c` nel diff; le aree nuove non compaiono (le righe nuove di `session.c` usano `LOG_SESSION`/`LOG_ROOT`, quelle di `main.c`/`child.c` `LOG_CHILD`/`REG_WT`). Non ho riletto tutte le costanti: «verificato per diff».

### 16.4 «Whose line it is» (S4) — vale com'è
Controllo: `authentication.c`, `helper.c`, `log.c` non nel diff; `rcp.c` ha solo la funzione `rcp_admitted_waiting()` (19 nov).

### 16.5 «Where the log lines go» (S5) — da correggere (lieve)
- Tutto regge (`log_session_path()`, `exec >>FILE 2>&1`: compare solo come contesto nel diff, riga 4306-4402; commento nuovo «fs.protected_regular (on in Debian, Fedora, Arch)» nell'albero Ubuntu). 
- Ultima frase: «The package removes the file when the package is purged (`debian/remotix.postrm`)» è vera ma incompleta: il purge toglie anche `~/.config/dconf/remotix` e `/etc/dconf/db/remotix` (vedi 15.6). Non è un file di registro, ma il manuale parla di «what the package removes».
- Aggiungere: su Ubuntu l'accesso ordinario dei programmi snap/confinati non scrive qui; non verificato.

### 16.6 «The systemd journal output» (S6) — vale com'è
Controllo: `log.c` invariato; il testo non nomina distribuzioni. Nota per l'unione: su Ubuntu 26.04 con AppArmor vero il profilo `remotix_network` vietava ogni socket unix (registro C4): senza `deny` corretto non c'era nemmeno il socket del journal. Ora corretto (`deny unix (bind, listen) addr=@**` e `deny unix (connect, send, receive) peer=(addr=@**)`).

### 16.7 «Journal priorities and the rule of the head mark» (S6B) — vale com'è (con riserva)
Controllo: nessuna modifica alla regola di `line()`; `docs/REGISTRO-priorita.md` esiste ancora e non è nel `docs.diff`. Riserva: i conteggi (31 righe, 33 pattern, ~700 punti ⛔) vengono dal giro di Debian del 17 nov; le molte righe `⛔/⚠` nuove del ramo Ubuntu non sono classificate (non verificato).

### 16.8 «What never enters the log» (S7) — vale com'è
Controllo: `authentication.c`, `helper.c`, `page.c`, `input.c` non nel diff; in `rcp.c` solo `rcp_admitted_waiting()`.

### 16.9 «The startup declarations» (S8) — da correggere
- Tabella: mancano le dichiarazioni nuove di Ubuntu:
  - area `rootside`, all'avvio del lato root (`session_dconf_system_db_ensure()`): `⭐ D-015: /etc/dconf/db/remotix was missing|DIFFERENT from what the package's keyfiles compile to: compiled now from /usr/share/remotix/dconf/remotix.d`; oppure `⚠ D-015: … is missing and /usr/bin/dconf (package dconf-cli) is missing: the GNOME remote sessions use the declared fallback`; oppure `⚠ … could NOT be made|put right (…)`.
  - area `session`: righe «D-015 …» sul profilo runtime (`DECLARED FALLBACK, D-015 (19 Nov 2026)`; esiti vivo/morto/SCONOSCIUTO della vita del desktop al avvio del figlio); non elencate una per una (molte, `session.c`).
  - area `child`, al login: `⛔ «user» passed PAM but the desktop cannot be born: <desktop> needs `labwc` and it is NOT installed on this server — the administrator must install the package `labwc` … ⭐ The child is NOT spawned, it gets 0x0E` (`main.c`, `session_missing_component()`, solo XFCE e LXQt, controllato a ogni login).
  - area `wt`: `⛔ the child of «user» refused the stage (scale): sent away N clients with 0x0E` e (child) `⭐ the user's scale %.3f on «…» is NOT served: I try ONCE to bring our monitor back to 1`.
- Riga della tabella «Which desktop the machine has and why» (`session_desktop_explain()`): ora il riconoscimento include i nomi di sessione dei gusti (`xubuntu`, `lubuntu`, `kubuntu`, `ubuntu`) e sceglie la sessione GNOME «che la schermata di accesso offrirebbe per prima» (`desktop_of_session_name()`, D8 in `session.c`). Spiegazione delle motivazioni da riscrivere.
- «The PAM service file found, or ⛔ the PAM service «remotix» DOES NOT EXIST»: invariato, `look_pam_service()`; non verificato il testo esatto su Ubuntu.

### 16.10 «Lines of the stop, the orphan rule and the local-login hold» (S8B) — da correggere (lieve)
- Le righe citate sono di `rootside.c`/`main.c` e non sono cambiate nel diff, tranne: `main.c`, `local_found_by_child()` ora dice «`its child is doing the light close`» (prima «left after the light close»; il messaggio arriva PRIMA della chiusura, 19 nov). Riga del capitolo che commenta «Light close for that user» regge.
- Aggiungere: `⭐ this end FOLLOWS THE SCALE REFUSAL (our own close), not a logout from the desktop menu` (child) e `⚠ no «stage refused» hook` come righe di `child`.
- «What the page of a client that is refused a birth during the hold shows was not traced»: resta non verificato.

### 16.11 «Environment variables read by the product» (S10) — da correggere
- Elenco completo dei nomi `REMOTIX_`: manca `REMOTIX_LABWC`, **define di compilazione** (`src/Makefile`: `override CFLAGS += -DREMOTIX_LABWC='"$(LABWC)"'`, default `/usr/libexec/remotix/labwc`; letto da `kwin.c:1373` con `access(REMOTIX_LABWC, X_OK)`; `debian/rules` passa `LABWC=$(LABWC_PATH)`). Va nel paragrafo «Other occurrences of the prefix are not variables either».
- Ultimo paragrafo (variabili standard): «`DCONF_PROFILE`» è ancora letto, ma con un ruolo diverso: la sessione non lo riceve più (né nell'ambiente né nel gestore utente); il profilo di base si legge da `DCONF_PROFILE` solo se l'amministratore lo ha messo (`dconf_base_profile(g_getenv("DCONF_PROFILE"))`), e la sessione scrive `$XDG_RUNTIME_DIR/dconf/profile`. Prove: `session.c`, diff righe ~2601-2710; registro C5.
- Aggiungere `XDG_DATA_HOME`, `HOME` (nuove `g_getenv` in `session.c`, diff 2473-2474).

### 16.12 «Diagnostic instruments» (S11) — vale com'è
Controllo: `--encoding-test` ha la stessa risposta (`child.c`: nessuna modifica all'elenco dei campi nel diff); la pagina (`page.html`) ha diff piccolo (non ho letto l'intero: «verificato per diff» del solo `#logbook`? non verificato). Nota: `--dconf-keyfiles DIR` è un nuovo strumento SOLO di costruzione (`main.c`: `argc == 3 && strcmp(argv[1], "--dconf-keyfiles")`, chiamato da `debian/rules`); manca dalla tabella, ma non è una diagnostica.

---------------------------------------------------------------------------------------------------------------------------------------

## ch17_testing.py — «Testing» (484 righe, 9 sezioni)

Debian/«box» da segnalare ovunque: percorsi `/media/REMOTIX-DEBIAN/…` (righe 115, 224-227, 244, 251, 346), «Debian 13» (338, 341, 355), `task-<de>-desktop` (289-292, 303), «box-identity debian 13» (307), `+deb13` (226), porte 8811-8814 (118, 289-292), contenitori `rx-<de>`/`rx/<de>`.

### 17.1 «What a check is and how it decides» (S1) — da correggere (lieve)
- Principi (tre verdetti PASS/FAIL/BLOCKED, nulla condiviso, scadenze, utenti propri): validi (`lib.py`: `Results`, `guard()`).
- «The checks run on the dev server only … `prepara-server.sh` installs them after every reboot»: ora due banchi: (a) contenitori (`boxes/`), (b) macchine virtuali QEMU con `RX_BANCO=vm` (`lib.py`: `BOXES = prove/banco-vm`, porte 8841-8844). Il banco VM aggiunge `RX_TEMPO` (intero ≥ 1, moltiplica ogni scadenza; `guard()` rifiuta altri valori; `all.sh` lo pone a 2 con `RX_BANCO=vm`).
- `all.sh` ha ora righe oltre ai tre verdetti: `SKIP (motivo)` (mai PASS, non fa fallire) e `NOTE` (chiave del banco installata, Welcome Center nascosto). Il testo dice «exits 0 only if every named check is PASS»: per `all.sh` ora anche exit 3 per un giro PARZIALE (`--only`).
- Lista dei prefissi utente: il pattern di `fresh-vm.sh` è `bc|lc|mu|rs|ac|cb|bn|dkf?|md|in|ph|pl`: comprende anche `pl` (check-prelocal), `in`, `ph`, che il capitolo dice «non sono nel pattern di `sweep()`». Il `sweep()` di `lib.py` non è nel diff: la frase resta vera per `all.sh`; ma aggiungere che `fresh-vm.sh` li rimuove tutti.

### 17.2 «The files of prove/» (S2) — da correggere
- Mancano `prove/banco-vm/box.sh` (stessa faccia di `boxes/box.sh`, verbi `ssh`, `rootkey`, `install`, `status`, `reset` → rifiuta) e `prove/banco-vm/fresh-vm.sh` (la «scatola fresca» per una VM che resta accesa); `fresh.sh` fa `exec` di `fresh-vm.sh` se `RX_BANCO=vm`. (`banco-vm/fresh.sh` NON esiste: `ls` mostra solo `box.sh` e `fresh-vm.sh`.)
- `window-input.py`: la descrizione «press / release … with their repeat count» non è più esatta: `release` è letto dagli eventi grezzi con `Gtk.EventControllerLegacy` (GTK 4.22 su Ubuntu: il campo di testo reclama la sequenza e il gesto di cattura non riceve più «released»), non porta `n` (registro B3-bis).
- `package-snap.py`: ignora anche `/var/lib/snapd`, `/run/snapd*`, `/var/lib/cloud`, `/run/cloud-init` (diff).
- `avlib.py`: `ensure_pulse()` ritorna «SKIP on the VMs» (il PulseAudio privato del box lxqt, 127.0.0.1:4713, non esiste in una VM).
- `base-check.py`: porte 8821-8824 (contenitori) / 8841-8844 (VM), `--boxes` verso `banco-vm` se `RX_BANCO=vm`.
- Riga 115: i registri «sono sul server in `/media/REMOTIX-DEBIAN/prove/log/`» → ora `/media/REMOTIX-UBUNTU/prove/log/` (`prepara-server.sh`: `BASE=/media/REMOTIX-UBUNTU`; `server/vm-login-test.py`: `sys.path` verso `/media/REMOTIX-UBUNTU/prove`).

### 17.3 «The checks of all.sh and what each proves» (S3) — da correggere
- Riga 118: «ports 8811 to 8814» → contenitori 8821-8824; VM 8841-8844 (`lib.py`).
- Nomi: `page-cad-button` → `page-cad-hidden` (fuori dalla diagnostica la pagina non mostra alcun pulsante Ctrl+Alt+Canc/Fine; BLOCKED se la diagnostica è accesa o non c'è sessione); `page-ctrl-alt-end` → `page-ctrl-alt-end-passes` (arriva al desktop senza conferma; PASS solo se il desktop riceve `Control_L, Alt_L, End` con ctrl+alt su End). Dal conteggio «24 common» il numero non cambia (rinomina). Prova: `check-input.py` diff, `COMMON` e `LAST`; DECISIONS-11 §11.54.
- «Things to know»: (1) `check-ban.py`: l'indirizzo bannato è `127.0.0.1` nei contenitori, `10.0.2.2` nelle VM (rete utente QEMU: ogni client appare come 10.0.2.2), o `RX_BAN_ADDR`; `all.sh` in VM salta `ban/other-addresses`. (2) `check-desktop.py` su Ubuntu: terminale GNOME `ptyxis` (non `gnome-terminal`); `sudo -n` va riconosciuto anche con sudo-rs (frasi «I'm afraid I can't do that», «interactive authentication is required»); `VOLATILE` esclude `.config/dconf/remotix`; `canvas-limits` aspetta che la finestra dica `ready` (fino a 150 s, misurato fino a ~78 s), aspetta un'immagine ferma (`still_png`), ritenta UNA volta una foto che non si è mai fermata, e il `bbox` ignora pixel sparsi (icona azzurra di KDE). La frase «`canvas-limits` judges … 4096x2304 / page never declares more than 3840x2160» regge: la lista `sizes` e `MEASURE_PROBES` (page.html:1520) sono invariate.
- I limiti di tempo (480, 1650, 960, 2500, 1600, 2700, 480, 480, 1500, 1250, 900, 900): invariati (`all.sh`: `run` righe; somma 17 860 s, calcolata sulle righe `run`); in VM ×2 (`RX_TEMPO`).
- L'affermazione sul docstring di `check-ban.py` («still describes unblock-shipped as…»): non verificata di nuovo.
- «GNOME … users-shell-and-environment (pkexec; the SHELL variable is empty)» resta l'unica riga rossa nota su GNOME (`giro2-gnome.md`).

### 17.4 «Running the suite» (S4) — da riscrivere
Motivo: i comandi, i percorsi e il formato del risultato cambiano.
- Percorsi `/media/REMOTIX-DEBIAN/prove` → `/media/REMOTIX-UBUNTU/prove`; pacchetto `remotix_1.0.0-1+deb13_amd64.deb` → `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (`build-deb.sh`: `VERSION="$VERSION_UP-$REVISION+ubuntu26.04"`); `fresh.sh` cerca in `/media/REMOTIX-UBUNTU/pacchetti` (diff).
- Nuove opzioni di `all.sh`: `--clean` (solo VM: pulizia senza installare), `--only label,label` (elenco `LABELS`: base-chrome base-firefox lifecycle multiuser desktop media resilience audio-chrome audio-firefox clipboard input-chrome input-firefox phone prelocal ban package), `RX_BANCO=vm`, `RX_TEMPO`; senza `--fresh`/`--clean` la VM NON viene pulita. Uscita: 0 giro completo tutto PASS; 3 tutto PASS ma parziale; 1 altrimenti.
- Riepilogo: righe `NOTE`, `SKIP`; riga finale «lines of the checks: N PASS, N FAIL, N BLOCKED/other, N SKIP, N NOTE»; esiti «ALL PASS», «ALL PASS (n SKIP …)», «ALL PASS OF A PARTIAL RUN», «NO CHECK PRODUCED A PASS: nothing proven».
- La «Layout difference» (warn): afferma che `fresh.sh` non troverebbe `box.sh` da un checkout semplice. FALSO per `fresh.sh`: riga 5 ha il ripiego `[ -d "$BOXES" ] || BOXES=$HERE/../boxes`. Vale per il resto? `matrix.sh` non contiene «boxes» (grep): non verificato.
- «The limits … add up to 17 860 s»: vero, ma con `RX_TEMPO=2` raddoppia.

### 17.5 «The package check» (S5) — vale com'è
Controllo: `check-package.py` nel diff ha solo un commento («Docker Ubuntu»); `NAMES` = install, first-start, apparmor, remove, purge, reinstall, preinst, recommends, fresh-end (riga 38); `RECOMMENDS` (riga 42) elenca gli stessi sette pacchetti. Nota: non gira nel banco VM (`all.sh`: SKIP «needs box.sh reset»).

### 17.6 «The four test boxes» (S6) — da riscrivere
Motivo: tabella e descrizione sono quelle di Debian.
- Tabella: contenitori `rxu-<de>`, immagini `rxu/<de>:latest`, ssh 2221-2224, REMOTIX 8821-8824 con ordine gnome=1, kde=2, xfce=3, lxqt=4 (prima xfce, lxqt, gnome, kde); pacchetti `ubuntu-desktop-minimal` (gdm3), `kubuntu-desktop` (sddm), `xubuntu-desktop` (lightdm), `lubuntu-desktop` (sddm) — `boxes/Containerfile`, `boxes/box.sh` (`choose()`).
- `box.sh install` ora fa `apt-get install -y --reinstall` (un pacchetto della stessa versione sostituisce anche i file).
- Nuovi accorgimenti: preferenza apt -1 su `firefox thunderbird chromium-browser` (snap-wrapper; snapd non gira in un box) e, per i gusti non GNOME, su `gnome-shell gdm3 ubuntu-session` (BOX-01: xubuntu-desktop nudo porta gdm3 come predefinito, studio 8 §3.3); l'utente `ubuntu` (uid 1000) dell'immagine base è rimosso e `prova`/`prova2` devono avere uid 1000/1001 (il build fallisce altrimenti); `box-identity ubuntu 26.04 <de> -`.
- Il testo «The desktop as a Debian user installs it … task-<de>-desktop» e «box-identity debian 13» sono falsi qui.
- Importante per l'unione: `PIANO.md` (riepilogo 19 nov) dice «I container di prova non esistono più»; il banco è la VM (`RX_BANCO=vm`). Il manuale deve dichiarare quale dei due descrive (il codice dei contenitori c'è ancora in `boxes/`).
- La nota «Stale comments»: non rinverificata.

### 17.7 «The real-system virtual machine» (S7) — da riscrivere
Motivo: la VM e i suoi limiti sono cambiati.
- `server/vm.sh`: immagine `ubuntu-26.04-server-cloudimg-amd64.img` (non Debian genericcloud); aggiunge `-device virtio-vga` («the package's preinst refuses to install without a render node; VA-API encoding does not work on it»). Resto invariato (4 CPU, 4096 MB, ssh 2301, REMOTIX 8901). Cartella `/media/REMOTIX-UBUNTU/vm`.
- «The VM has no graphics card … a graphical session could not be tried»: ora falso come ritratto: `virtio-vga` dà un nodo render (nessuna codifica); in più `server/vm-radeon.sh` (nuovo, 338 righe) avvia VM con installazione reale da ISO: ubuntu (autoinstall), kubuntu/xubuntu/lubuntu (disco costruito dagli squashfs dell'ISO), UEFI (OVMF), q35, KVM, 8 CPU, 12 G RAM, disco 40 G, la Radeon dell'host ceduta con `vfio-pci` (03:00.0 e 03:00.1; UNA sola VM per volta), porte ssh 2341-2344, REMOTIX 8841-8844; comandi `crea|accendi|spegni|ssh|stato|prova-avvio|istantanea|ripristina`. Script collegati: `vm-radeon-installa.sh` (installa un .deb come l'amministratore, `systemctl enable --now remotix`, istantanea), `vm-radeon-aggiorna.sh` (full-upgrade + snap refresh, istantanea «aggiornato»), `vm-radeon-controllo.sh` (accensione cronometrata, un accesso come `prova2`, foto in `log/consegna/`), `vm-radeon-login-test.py`.
- Nuovo `server/live-installa.sh` (+ studio 15): programma di PROVA per una macchina avviata da una live Ubuntu 26.04: `wget -qO- http://192.168.0.2:8830/installa.sh | sudo bash`; scarica il `.deb` e lo sha256, controlla universe, `apt-get install -y --reinstall`, crea `prova`/`prova2`, `systemctl enable --now remotix`. Non fa parte del prodotto.
- `prepara-server.sh`: ora installa anche `ovmf xorriso gdisk dosfstools rsync` (prima nessun firmware: «SeaBIOS; prepara-server.sh installs no firmware package» è falso); storage podman CONDIVISO con il lavoro Debian sotto `/media/REMOTIX-DEBIAN/podman` (`PODMAN_BASE`), file di config scritti solo se assenti.
- Box VM `prove/banco-vm/box.sh`: ssh come root con la chiave del banco (non sudo, per non scrivere i segreti nel journal della VM), `rootkey` una volta per VM.

### 17.8 «What only a real machine or a real phone can prove» (S8) — da correggere
- Riga «AppArmor during a live session»: ora provato su macchina vera (live Ubuntu 26.04.1, kernel 7.0) il 19 nov: ha trovato il difetto C4 (tutti gli accessi rifiutati) e la correzione è stata misurata («bus di sistema e journal raggiungibili, socket astratti ancora rifiutati»). Il profilo resta in `complain` (`flags=(complain,attach_disconnected)`); «must be observed … before enforce» regge. I contenitori continuano a non provarlo (`check-package.py` BLOCKED).
- Riga «A machine with a real local graphical session»: ora la prova a mano è stata fatta sulle quattro live Ubuntu, Kubuntu, Xubuntu, Lubuntu (PIANO, riepilogo) e, per Ubuntu e Kubuntu, «accesso locale chiude il desktop remoto»; il testo parla di Debian 13 (righe 388-389).
- Riga «NVIDIA»: invariata. Riga «A real phone»: invariata nella sostanza; «Samsung DeX on GNOME 17 Nov» è storia Debian.
- Aggiungere (nuovi limiti da `docs/REGISTRO-problemi.md`): E4 (piccoli scatti del video visto da Chrome su Android, VM Ubuntu, 19 nov, non distinto tra telefono/VM/Radeon); gli snap/Flutter nella sessione remota (C5) non sono nei contenitori (niente snap).

### 17.9 «What was verified on 17 November 2026, and what was not» (S9) — da riscrivere
Motivo: i numeri sono i giri di Debian; per Ubuntu esistono altri.
- Tabella 17 nov 19:40 (118 righe per desktop; XFCE 111 PASS, LXQt 112, KDE 111, GNOME 104): storia Debian, da togliere o mettere in un riquadro «Debian».
- Dati Ubuntu (rapporti `studio/giro1-*.md` e `giro2-*.md`, 18 nov 2026; non rieseguiti da me): unione1 GNOME 116 PASS su 124 (8 non PASS), XFCE 117 su 124 (7 non PASS), KDE (da giro1-kde non letto per riga), LXQt 117 su 124. unione2: GNOME 123 su 124 (1 FAIL: `desktop/users-shell-and-environment`, pkexec); KDE 121 su 124 (3 FAIL, dettaglio non letto); LXQt 124 su 124 (ALL PASS); XFCE 126 su 128 (2 non PASS; perché 128 righe: non verificato). Chiusura 18 nov: `mouse-drag` (Chrome e Firefox) e `tap-and-half-drag-select` (finestra di prova, B3-bis), `page-cad-hidden`, `page-ctrl-alt-end-passes`.
- Ultimo pacchetto: `unione10`, `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (sha256 `07b270e8…63aa`), revisore APPROVATO, giro completo su GNOME verde tranne la riga pkexec (`PIANO.md`, riepilogo del 19 nov). Verifica manuale del proprietario su 4 VM e 4 live (stesso riepilogo).
- Le righe «Open items of PIANO.md», «Without a video card the error repeats…»: storia Debian; non riverificate.

---------------------------------------------------------------------------------------------------------------------------------------

## ch18_build.py — «Build and release» (267 righe, 8 sezioni)

La tabella di `S4` e le liste `SORGENTI`, `PROTOCOLLI`, `MINIMI` sono lette da `src/Makefile` al momento della generazione: il diff del Makefile aggiunge solo `LABWC`, quindi i numeri non cambiano (conteggi non rimisurati da me).

### 18.1 «The build of the .deb in one container» (S1) — da correggere
- Riga 37: «builds a `debian:trixie` image» → `ubuntu:26.04`; figura (riga 24, 26): etichette «debian:trixie + build-deps» e «remotix-debian-build» → `remotix-ubuntu-build` (`IMAGE=${IMAGE:-localhost/remotix-ubuntu-build}` ora sovrascrivibile).
- Riga 42: «Debian 13 image: …». Ora: Ubuntu 26.04 con universe; strato nuovo `labwc` con `meson patch hwdata wayland-protocols libegl-dev libgles-dev libinput-dev libpixman-1-dev libseat-dev libudev-dev libdisplay-info-dev libxml2-dev libcairo2-dev libpango1.0-dev libpng-dev curl`, poi `fetch.sh` che scarica e verifica i due tarball in `/usr/local/src/labwc-sources` (diff `build/Containerfile`).
- Riga 39-40: «the image build clones ngtcp2 and nghttp3 from GitHub»: ora anche scarica labwc (GitHub) e wlroots (gitlab.freedesktop.org), con sha256 (`build/labwc-ospite/VERSIONS`).
- Tabella: aggiungere `build/labwc-ospite/` (`README`, `VERSIONS`, `fetch.sh`, `build.sh`, `wlroots-0.19.2-remotix-presented-root.patch`). Tutto in `build/build-deb.sh`: `cp -a "$HERE/labwc-ospite" "$c/remotix/labwc-ospite"`.

### 18.2 «The build image and the static QUIC libraries» (S2) — da correggere
- Riga 58: «Debian 13 carries ngtcp2 1.11 and nghttp3 1.8 (the comment in `src/Makefile`)». Ubuntu 26.04: `libngtcp2-dev` 1.16.0 e `libnghttp3-dev` 1.12.0, entrambi universe (studio 8 §1.2, `apt-cache`, non rimisurato da me). Il commento di `src/Makefile` non è nel diff: riporta ancora i numeri di Debian. Il fatto «too old: need 1.25 + `ngtcp2_crypto_ossl`, OpenSSL ≥ 3.5» regge: libssl-dev 3.5.5 su Ubuntu.
- «Not pinned by hash» per ngtcp2/nghttp3: vero (`quic-static.sh` non nel diff). NOVITÀ di segno opposto: labwc e wlroots SONO fissati per sha256 (`VERSIONS`: labwc 0.9.3 `38d273fa…`, wlroots 0.19.2 `09a0a8d6…`); `fetch.sh` ricontrolla anche file già presenti, `build.sh` li ricontrolla ancora.
- Warn finale: «Debian mirrors» → archivi Ubuntu e GitHub/gitlab.freedesktop.org.
- «The versions are written in four places»: invariato per ngtcp2/nghttp3; per labwc/wlroots le versioni stanno in `VERSIONS`, `debian/control` (Static-Built-Using) e nel nome della patch.

### 18.3 «What build-deb.sh does, step by step» (S3) — da correggere
- Tabella variabili: `OUTPUT` default `/media/REMOTIX-UBUNTU/pacchetti`; `RX_REVISION` «the Debian revision» → revisione del pacchetto; nuova `IMAGE` (default `localhost/remotix-ubuntu-build`); `SOURCE_DATE_EPOCH` calcolato anche su `build/labwc-ospite`.
- Passi: copia con anche `labwc-ospite/`; `debian/changelog` con «`resolute`; … `* Ubuntu 26.04 build.`» (prima trixie, «Debian 13 build»); nuovo passo dopo i controlli: archivio del sorgente corrispondente di NOSTRO labwc `$OUTPUT/remotix-<versione>-labwc-source.tar.gz` (+ `.sha256`): i due tarball, la patch, la ricetta; archivio deterministico (`tar --sort=name --owner=0 --group=0 --numeric-owner --mode=go-w --mtime=@SDE | gzip -n`), 7 file attesi, controllo con `fetch.sh`; riga `labwc-source SI|NO` in `controlli.txt`; con `TWICE=1` anche la riga `R23 labwc-source-riproducibile`.
- File di uscita: aggiungere il `.tar.gz` e il `.sha256` del sorgente di labwc.
- Uscita: invariata nella sostanza (qualunque ` NO` in `controlli.txt` → exit 1).

### 18.4 «src/Makefile: sources, libraries, minimum versions» (S4) — da correggere (lieve)
- Tutto regge; manca la riga di tabella sulla variabile `LABWC` (`LABWC ?= /usr/libexec/remotix/labwc` e `override CFLAGS += -DREMOTIX_LABWC='"$(LABWC)"'`; «make clean first when it changes»; scelta di costruzione, mai opzione a runtime).
- Il titolo «TWIN=none … plain make fails at fingerprints»: invariato (diff non lo tocca).

### 18.5 «debian/rules: the overrides and the guards» (S5) — da correggere
- Mancano: `LABWC_SOURCES ?= /usr/local/src/labwc-sources`, `LABWC_PATH := /usr/libexec/remotix/labwc`; in `override_dh_auto_clean` ora `rm -rf debian/labwc-build debian/labwc-root`; `override_dh_auto_build` prima costruisce il labwc con `JOBS=… BUILD_DIR=$(CURDIR)/debian/labwc-build labwc-ospite/build.sh $(LABWC_SOURCES) $(CURDIR)/debian/labwc-root` (meson, `--wrap-mode=nodownload`, `-Dwerror=false` perché libinput più nuovo fa un avviso con wlroots 0.19.2, fallisce se il binario ha `libwlroots`) e poi passa `LABWC=$(LABWC_PATH)` a `make`; `override_dh_auto_install` installa labwc (0755) e genera `/usr/share/remotix/dconf/remotix.d` con `src/remotix --dconf-keyfiles`; `debian/remotix.install` mette il file needrestart.
- Riga 162: «gcc 15 would default to gnu23»: Ubuntu 26.04 ha gcc 15.2 (studio 8): regge.
- Riga 174: «restarts it only if it was active or enabled»: formula discutibile ma non toccata dal diff; da lasciare.

### 18.6 «The package checks R4, R13, R14, R23 and R24» (S6) — da correggere
- R4: ora due controlli: `ldd` del binario (nessun «not found», nessun ngtcp2/nghttp3 dinamico) E `R4 ldd-labwc` su `usr/libexec/remotix/labwc` (nessun «not found», nessun `libwlroots`, stampa `labwc --version`; NO se il file manca). Riga 197-198 «32 libraries in the recorded runs»: dato Debian; per Ubuntu non verificato.
- Nuove righe: `labwc-source`, `R23 labwc-source-riproducibile` (vedi 18.3).
- R13, R14, R24: invariati (diff non li tocca).
- «What was recorded»: «lintian 0 E 0 W», «32 libraries», «R23 has no recorded run»: tutti dati di Debian. Ubuntu: studio 11 voce P1 riporta «lintian 0/0, installa sui 4 box» per il primo pacchetto; il pacchetto `unione10` non ha dati di lintian nei file letti (`/media/REMOTIX-UBUNTU/pacchetti` non esiste su questa macchina): «non verificato». Lintian 2.129 (Ubuntu) contro 2.122 (Debian 13): possibili tag nuovi (studio 8, problema 9).

### 18.7 «Version and release» (S7) — da correggere
- Riga 226: `…+deb13` → `…+ubuntu26.04`; esempio `remotix_1.0.0-1+ubuntu26.04_amd64.deb` (nome verificato: `live-installa.sh` riga `PACCHETTO=…`; `build-deb.sh` `VERSION="$VERSION_UP-$REVISION+ubuntu26.04"`).
- Riga 228: «the distribution `trixie` … `Debian 13 build`» → `resolute`, «Ubuntu 26.04 build».
- Riga 232-233 comandi: `OUTPUT=/media/REMOTIX-UBUNTU/pacchetti/1.0.0` (cartelle per versione: `unione10`, ecc.).
- «What "release" means»: resta senza script di rilascio né firma; novità: ogni rilascio deve pubblicare anche `remotix-<versione>-labwc-source.tar.gz` (GPL-2: sorgente corrispondente di labwc, `debian/copyright`, `LICENSE.md` §8). «`manuals/sources/build.py` reads the default of RX_VERSION»: il file risulta modificato nell'albero (`git status`): non verificato.
- «docs/INVENTARIO-non-debian.md» esiste ancora (ls docs).

### 18.8 «Generated and vendored inputs» (S8) — da correggere (incompleta)
- Le tre righe (opus.wasm, `vulkanvideo_rgb_nv12_spv.h`, protocolli) valgono: i file relativi non sono nel diff.
- Manca la quarta fonte esterna vendorizzata: i due tarball (labwc 0.9.3, wlroots 0.19.2) e la patch `build/labwc-ospite/wlroots-0.19.2-remotix-presented-root.patch` (MIT, in `types/scene/surface.c`, `frame_done`: tratta la radice della superficie come «presented» a ogni fotogramma, per KWin ≥ 6.5 annidato); i tarball non sono in git ma nell'immagine di build.

---------------------------------------------------------------------------------------------------------------------------------------

## Conteggio finale (36 sezioni)
- vale com'è: 9 — 16.1, 16.2, 16.3, 16.4, 16.6, 16.7, 16.8, 16.12, 17.5
- da correggere: 23 — 15.1-15.7 (7), 16.5, 16.9, 16.10, 16.11 (4), 17.1, 17.2, 17.3, 17.8 (4), 18.1-18.8 (8)
- da riscrivere: 4 — 17.4, 17.6, 17.7, 17.9

---------------------------------------------------------------------------------------------------------------------------------------

## (a) COSE NUOVE di Ubuntu da aggiungere nel gruppo
1. ch15 S5 (Files) + nuova sezione «Our own labwc (KDE)»: `/usr/libexec/remotix/labwc`, motivo (KWin ≥ 6.5 disegna un pixel nero come radice e wlroots non la riporta «presented», KWin dà ai client un orologio a 0, Firefox si crede coperto e smette di dipingere), versioni, patch, linkaggio statico, licenze, sorgente da pubblicare. Fonti: `build/labwc-ospite/README`, `debian/copyright`.
2. ch15 S4/S5/S6: database dconf di sistema (`/etc/dconf/db/remotix`): generazione in costruzione (`--dconf-keyfiles`), compilazione nel postinst e all'avvio del servizio, rimozione nel postrm, ripiego dichiarato, file utente `~/.config/dconf/remotix` rimosso al purge. Fonte: registro C5.
3. ch15 S7: needrestart (`/etc/needrestart/conf.d/remotix.conf`).
4. ch15 S4: avviso del postinst su `labwc` mancante (solo XFCE/LXQt) e il rifiuto al login con 0x0E (`session_missing_component()`) → ch16 S8 (startup/login lines).
5. ch16 S8/S8B: righe nuove D-015, «cannot be born: needs `labwc`», «refused the stage (scale)», «FOLLOWS THE SCALE REFUSAL».
6. ch17: nuovo capitolo-sezione «Il banco a macchine virtuali»: `RX_BANCO=vm`, `RX_TEMPO`, `banco-vm/box.sh`, `fresh-vm.sh`, `all.sh --clean --only`, SKIP/NOTE, exit 3, porte 8841-8844, `server/vm-radeon*.sh`, `server/live-installa.sh`.
7. ch17 S3/S9: la lezione B3-bis (riga rossa uguale su tutti i desktop: sospettare lo strumento, guardare gli eventi grezzi; GTK 4.22) e C4 (i contenitori non provano AppArmor: serve un accesso su macchina vera).
8. ch18 S3: archivio `remotix-<versione>-labwc-source.tar.gz`, controlli `R4 ldd-labwc`, `labwc-source`, `R23 labwc-source-riproducibile`.
9. ch18 S5: le regole `LABWC_SOURCES`/`LABWC_PATH`, `--dconf-keyfiles`.
10. ch15/ch18: `universe` come requisito del sistema di costruzione e dei Recommends (`labwc`, `wlr-randr`, `va-driver-all`).

## (b) Cose di Debian da TOGLIERE
- «Debian 13», «trixie», `debian:trixie`, `+deb13`, `remotix-debian-build`, `/media/REMOTIX-DEBIAN/…` (ch15 S1; ch17 righe 115, 224-227, 244, 251, 338, 341-355; ch18 S1, S3, S7, figura), `task-<de>-desktop`, `box-identity debian 13`, `rx-<de>`/`rx/<de>`, porte 8811-8814 e ssh 2211-2214.
- ch15: debhelper 13.24.2 (S4), «real Debian 13 virtual machine… 8/8» (S6), «standard Debian way» (S4), «Recommends labwc… and for KDE» (S2).
- ch17 S7: Debian 13 genericcloud, SeaBIOS «prepara-server.sh installs no firmware», «VM without graphics card».
- ch17 S9: la tabella del 17 nov (Debian) e il resto del capitolo storico (check-package 8/8, `pulizia1b`, DeX).
- ch18 S2: «Debian 13 carries ngtcp2 1.11 and nghttp3 1.8»; S6: «32 libraries», «lintian 0E 0W» come fatti di Ubuntu.
- Il warn «Layout difference» di 17.4 (falso per `fresh.sh`).

## (c) rif() incrociati verso altri gruppi e stile
Titoli di sezione citati (da verificare che esistano nei capitoli degli altri gruppi): «Build and release», «Security model», «The local-login hold», «Appendix C — Known issues and open points», «Logging and diagnostics», «Stopping the service», «Startup and life cycle», «Login and its defences», «Environment variables read by the product» (interno), «The RCP/1 protocol», «The browser page», «The package», «Testing», «Where the code is Debian-specific» (ch17 S6 nota: sezione da riscrivere/rinominare per Ubuntu), «Extending REMOTIX and porting to another distribution» (ch18 S8), «Performance and capacity» (ch17 S8). Da aggiungere come rif() da altri gruppi: Sicurezza → AppArmor (`deny unix`, percorsi xkb `/usr/share/xkeyboard-config-2`, registro C4), Sessioni/GNOME → database dconf (registro C5), KDE → «Our own labwc».
Stile osservato: `from build import c, code, note, p, rif, table, tree, ul, warn` (anche `h4`, `steps`, `tip`, `term`, `fig`, `box`, `arrow`, `zone`, `text`, `sysf`, `flow`); ogni capitolo definisce S1…Sn e `CHAPTER = (titolo, [(titolo sezione, html)…])`; tabelle con didascalia che comincia con `«TAB» — …`, figure con `«FIG» — …`; `note(testo, "Titolo breve.")`, `warn(...)` per limiti, `tip(...)` per consigli; `p(..., lead=True)` apre ogni sezione; `c()` per codice inline, `sysf()` per percorsi di sistema; `term("""$ …""")` per comandi; tono: asciutto, in inglese, «non verificato» dichiarato esplicitamente («was not run for this manual»). Il capitolo 18 legge `src/Makefile` a tempo di generazione (`_make_list`): un cambiamento del Makefile cambia i numeri senza toccare il testo.


---------------------------------------------------------------------------------------------------

<!-- ===== frammento g5 ===== -->
# Inventario g5 — ch19 performance, ch20 extending, ch21 conventions, ch22 structures, ch23 map, ch24 problems, ch25 glossary

Albero: `~/Documenti/REMOTIX-UBUNTU`, ramo `ubuntu-26.04` (un solo commit sopra `main`: 50d997b). Sola lettura. Controlli fatti: lettura dei capitoli per intero, `git diff main..ubuntu-26.04` di `src/` (anche degli header uno per uno), `debian/`, `build/`, `boxes/`, `prove/`, `server/`, `docs/REGISTRO-problemi.md`, `PIANO.md`, `studio/5,6,11`, grep mirati nell'albero attuale. Nessuna misura, nessuna compilazione.

Fatti di base che valgono per tutti i capitoli (cosi' non si ripetono): i capitoli di `technical-ubuntu26.04/` sono ancora identici a quelli di Debian (verificato: `ch19..ch25` contengono ancora «Debian 13», «trixie»). Il codice del ramo cambia in `session.c` (+1889 righe nette, il 40% del diff), `child.c`, `kwin.c`, `mutter.c`, `capture.c`, `main.c`, piu' pochi ritocchi (`rcp.c` +8, `webtransport.c` +36, `sentinel.c`, `input.c`, `page.html` solo commenti, `rootside.c` +1). Nessun file nuovo in `src/`; le costanti di protocollo e di limite non cambiano (vedi ch19 sez. «Limits»). Versioni Ubuntu viste negli studi (apt-cache nei contenitori, `[V]`): systemd 259.9, GNOME Shell 50.1 / Mutter 50.1, KWin 6.6.7 (Plasma 6.6.7), PipeWire 1.6.2, WirePlumber 0.5.13, dconf 0.49, labwc 0.9.3 e wlroots 0.19.2 di sistema (XFCE, LXQt), xfce4-session 4.20.4, xfce4-panel 4.20.7, lxqt-session 2.3.0, lxqt-panel 2.3.2, libva 2.23, Vulkan loader 1.4.341, AppArmor 5.0.2, polkit 127, sudo-rs 0.2.13, rust-coreutils 0.10.0, kernel 7.0 (live 26.04.1, registro C4).

---

## ch19_performance — «Performance and capacity» (184 righe, 7 sezioni)

Premessa che vale per l'intero capitolo: i numeri di S1-S4 vengono dai log `prove/log/v160-<de>/*.out` del giro del 17 nov 2026 su Debian 13 (container, server di sviluppo). Nel ramo Ubuntu non esiste nessun log di misura (`prove/log` non e' nell'albero; i log del giro Ubuntu stanno sul server in `/media/REMOTIX-UBUNTU/log/`, che da qui non leggo). `PIANO.md` dice solo: «giro automatico completo su GNOME: verde tranne `desktop/users-shell-and-environment`». Nessuna cifra di prestazione per Ubuntu e' dunque verificabile: va scritto «non verificato» o tolto.

1. **«How to read the numbers of this chapter»** — da correggere.
   - «in the round of 17 November 2026 on the code that became 1.0.0» e «Nothing here was measured while writing the manual»: il giro e' di Debian; per Ubuntu non c'e' una misura citabile. La classificazione Measured / Recorded / Coded resta valida come metodo, ma «Measured now» per Ubuntu e' vuoto (prova: nessun `.out` nell'albero; `PIANO.md`, riepilogo 19 nov).
   - La nota sul browser guidato dal debugger resta vera (strumento invariato: `prove/lib.py` cambia solo per `RX_BANCO`/`RX_TEMPO`).
2. **«The test machine and the conditions of the measurements»** — da riscrivere. Motivo: descrive 4 container systemd su un solo host (carico 3.89-6.21, Chrome 156.0.8078.79, Firefox 153.7.0, 1344x768). Su Ubuntu il banco e' diverso (prove: `server/vm-radeon.sh`, `prove/banco-vm/box.sh`, `prove/lib.py`, `PIANO.md`): 4 macchine virtuali QEMU/KVM con UEFI (`CPUS=8 MEM=12G DISKSZ=40G` in `vm-radeon.sh`), installate davvero dalle ISO 26.04 (Ubuntu, Kubuntu 26.04.1, Xubuntu, Lubuntu), con la Radeon del server passata in `vfio-pci` (GPU `0000:03:00.0`; **una sola VM per volta ha la scheda**); client = il browser del server, rete utente QEMU (ogni client appare come `10.0.2.2`, porte 884x), `RX_TEMPO=2` raddoppia ogni scadenza. Modello della scheda (RX 6800?), browser e dimensione canvas del giro Ubuntu: non verificato (nessun log nell'albero). I container (`boxes/`, porte 8821-8824) esistono nell'albero ma `PIANO.md` dice che non esistono piu'.
3. **«Picture, frame rate and sound measured on 17 November 2026»** — da riscrivere. Tutta la tabella (159/159 valori, 20 ms, 61.7 fps, GNOME 39.3 fps, sfasamento audio 267-305 ms, nitidezza 1.00) e' un risultato Debian: non vale per Ubuntu. Per Ubuntu: non verificato; il codice cambia pero' cio' che e' misurabile: (a) KDE: `capture_watch_sequence()` / `capture_frame_lost()` in `capture.c` (`LOST_QUIET_MS` 200, `LOST_POKES_MAX` 10, `SEQ_WINDOW` 600) e `kwin_poke()`: un buco nella numerazione dei buffer di KWin forza un fotogramma «all changed» e, dopo 200 ms senza immagine, un «poke»; durante un'animazione compare un buffer solo-cursore dopo ogni immagine (commento `capture.h`, misure `[M]` 19 nov su Kubuntu: finestra ferma a meta' animazione 18-26 s; 68 poke su desktop fermo = 68 frame con danno vuoto, non inviati). (b) Il «60 Hz animation» di GNOME 39 fps (Debian) non ha equivalente Ubuntu. (c) `AUDIO_BUFFER_MS = 250` invariato (`page.html:7022`), quindi il vincolo «sound lags by about 250 ms+» resta una proprieta' del codice, non una misura.
4. **«Session and login timings measured on 17 November 2026»** — da riscrivere. Valori Debian (2.64 s di rifiuto, Log Out 0/0/5/4 s, 6 s per tre utenti, 29/89 s dei clocks) non trasferibili. `REJECT_FLOOR = 2500` (`rcp.c:245`) invariato quindi il 2.5 s+ di rifiuto vale per costruzione, non per misura. Cambiano i tempi di chiusura: il figlio dice «la sessione e' finita» PRIMA di smontare lo stage (`session_over_early()` in `child.c`, solo su morte CERTAINTY `session_life()==DEAD`; non su KDE), quindi il «Log Out: client told» di GNOME/XFCE/LXQt non e' piu' quello Debian; il commento citato in `child.c` gia' dice 25 s di attesa RealtimeKit dove non parte. Il banco VM usa `RX_TEMPO=2` e `check-package` e' SKIP: nessun tempo registrato. Non verificato.
5. **«Capacity: the recorded measurements and what they do not cover»** — da correggere.
   - La campagna del 24 ago 2026 (6 sessioni su schermo che cambia tutto, >= 11 su desktop reale, 22.9 ms) e' indipendente dalla distro e dal pacchetto: resta «Recorded», valida com'e'; `budget.h:187` `BUDGET_STRAIN_DELAY_MS 22.9`, `:191` riserva 0.5 verificati.
   - «Measured now: the most users tried at once» (tre utenti, due a 60 Hz, `session-cap` a 2): per Ubuntu non verificato; `all.sh` ora fa SKIP di `ban/other-addresses` e `package` nel banco VM (`all.sh`, `RX_BANCO=vm`).
   - NVIDIA / Intel integrata: il banco Ubuntu ha solo la Radeon; Intel su Ubuntu + GNOME 50 mai provato con la suite funzionale (`studio/11` SCOPERTA 17).
6. **«Limits fixed in the code»** — vale com'e'. Controllo: `grep` delle costanti sull'albero Ubuntu (`RCP_SESSION_CAP 10` rcp.h:94, `RCP_CANVAS_MAX_W/H 4096/2304` rcp.h:1069-1071, `MOTION_FPS 60` child.c:5326, `V_CAP` 16 MiB rcp.c:5276, `REJECT_FLOOR 2500`, `LIMIT {5,20,30}` e `WINDOW_MS {300000,300000,600000}` rcp.c:1338-1339, `AUDIO_BUFFER_MS 250`, `BUDGET_DEFAULT_RESERVE 0.5`); il diff di `src/` non tocca nessuna di queste righe. Dichiarati (8 utenti, 3K) invariati: il ramo non ha decisioni nuove in `DECISIONS-11.md` (solo +4 righe su `--session-fd`).
7. **«Where no measurement exists»** — da correggere.
   - «capacity per number of users on 1.0.0», «real networks», «CPU and memory per session»: ancora vere (nessuna misura nuova nel ramo).
   - «a real phone or tablet as client» — da correggere: il registro E4 (19 nov) riporta una misura sul server di 40 s di video verso un telefono Android (Chrome): 0 pacchetti persi, 1.5-5 Mbit/s, 60 fps in 35 s su 39, ritardo di rete 8 ms (picchi 125 ms; tablet 3.5 ms, picchi 27 ms); causa non distinta (telefono / VM / cadenza / percorso Radeon). Non e' un benchmark: e' un caso aperto non bloccante.
   - «duration of a whole run of all.sh, only the sum of time limits, 17 860 s»: il numero Debian non e' piu' vero; `all.sh` ha 15 `run` (base-chrome 480, base-firefox 480, lifecycle 1650, multiuser 960, desktop 2500, media 1600, resilience 2700, audio-chrome 480, audio-firefox 480, clipboard 480, input-chrome 1500, input-firefox 1500, phone 1250, prelocal 900, ban 900) = 17 860 s: **uguale a Debian** (somma verificata a mano), ma sul banco VM i limiti sono moltiplicati per `RX_TEMPO=2`. Il verdetto «why GNOME paints 39 fps» riguarda Debian.
   - «NVIDIA: no run recorded»: invariato. «a card by vendor»: ora un dato in piu', la Radeon passata alla VM (ma modello non registrato nei log letti).

(a) COSE NUOVE: nuova sezione «Measurements on Ubuntu 26.04» con soli fatti: banco VM con Radeon, `RX_TEMPO=2`, nessun numero di prestazioni registrato, E4; limiti nuovi coded: `LOST_QUIET_MS 200`, `LOST_POKES_MAX 10`, `SEQ_WINDOW 600`, `WAIT_CALL_MS 15000` (3 chiamate = ~45 s al peggio in `mutter_scale_to_one()`, `mutter.h`), attesa RealtimeKit 25 s, `CLOSING_GRACE_MS 30000`. Aggiungere a «Limits fixed in the code».
(b) DA TOGLIERE: le tabelle S3 e S4 con i numeri Debian (o spostarli come «Debian 13, not repeated here»), le condizioni di S2 (4 container, carichi, Chrome 156, Firefox 153), il nome «round of 17 November» e «UHD 730/770» come contesto di misura Ubuntu.
(c) rif(): «Where no measurement exists», «Testing», «The four test boxes», «Quality, degradation and budget». Stile: tabelle con didascalia «TAB» — ..., `warn` per i dati non citabili, `tip` per il suggerimento di misura; ogni numero con la sua fonte.

---

## ch20_extending — «Extending REMOTIX and porting to another distribution» (236 righe, 8 sezioni)

1. **«The one-distribution rule»** — da correggere.
   - «written for one distribution, Debian 13 (trixie)» e «a port is a separate copy of the tree»: questo albero E' la copia separata per Ubuntu 26.04 (4 gusti: Ubuntu/GNOME, Kubuntu/KDE, Xubuntu/XFCE, Lubuntu/LXQt). La regola resta (il codice ha pero' di nuovo logica Ubuntu in `session.c`: nomi di sessione, `local_session()`), ma `CLAUDE.md` del ramo e' ancora quello di Debian («Debian trixie only», `REMOTIX-DEBIAN`; verificato: `CLAUDE.md` non e' nel diff). Decisione per il caposquadra: il manuale cita `CLAUDE.md` com'e' o si aggiorna il file.
   - «docs/PULIZIA-tranche1.md» e `INVENTARIO-non-debian.md` esistono ancora ma descrivono lo stato Debian; il codice rimosso li' e' in parte tornato (S3).
2. **«Where the code is Debian-specific»** — da riscrivere (la tabella ha righe giuste e righe false; cambiano 8 righe su 18). Righe:
   - package format: aggiungere `debian/remotix.install` (installa `debian/needrestart/remotix.conf` in `/etc/needrestart/conf.d`: `override_rc` di `remotix.service` = 0, perche' un riavvio chiude tutti i desktop remoti, DECISIONS-11 §11.56); `postinst` compila `/etc/dconf/db/remotix` con `dconf compile`; `postrm` toglie quel database e, in purge, `~/.config/dconf/remotix`; `rules` usa `src/remotix --dconf-keyfiles` e costruisce il labwc nostro.
   - build image: `docker.io/library/ubuntu:26.04` (resolute, universe) invece di `debian:trixie`; `build-deb.sh` produce `remotix_1.0.0-1+ubuntu26.04_amd64.deb` e `remotix-<ver>-labwc-source.tar.gz` (7 file, sha256 verificato su `VERSIONS`); controlli R4 (ldd del labwc: nessun libwlroots), R23 anche sull'archivio sorgente. Il suffisso e' `+ubuntu26.04` (non `+deb13`).
   - dependency names: `debian/control` Build-Depends cresce di 15 pacchetti (meson, patch, hwdata, wayland-protocols, libegl-dev, libgles-dev, libinput-dev, libpixman-1-dev, libseat-dev, libudev-dev, libdisplay-info-dev, libxml2-dev, libcairo2-dev, libpango1.0-dev, libpng-dev); `Static-Built-Using` aggiunge labwc 0.9.3 e wlroots 0.19.2; Depends/Recommends invariati (prova: diff). `libva-dev` e' in universe; Mesa VA in `mesa-libgallium` (per questo resta `va-driver-all` da solo).
   - install paths: aggiungere `/usr/libexec/remotix/labwc` e `/etc/needrestart/conf.d`; `/etc/ufw/applications.d` vale (ufw `ENABLED=no` su Ubuntu, studio 5).
   - PAM service: invariato nel contenuto; `remotix.pam` ha un commento nuovo (il PATH della sessione viene da `pam_env`/`/etc/environment`; NON aggiungere `user_readenv=1`).
   - who is an administrator: polkit 127 di Ubuntu mette `sudo` e `admin` (`49-ubuntu-admin.rules`); il testo «wheel and admin do not exist on trixie» va riscritto (studio 5 §polkit, `[V]`).
   - mandatory access control: AppArmor in complain, **ma sul kernel di Ubuntu (7.0) il profilo ha tre differenze**: `deny unix (bind, listen) addr=@**` e `deny unix (connect, send, receive) peer=(addr=@**)` al posto di `deny unix addr=@*` (registro C4), cartelle XKB `/usr/share/xkeyboard-config-2*`, `/etc/xkb`, `/etc/X11/xkb`, e `include if exists <local/remotix_network>`.
   - first connection: invariato (`child.c`, `render_grant.c`; gruppo `render` creato da udev su Ubuntu, studio 5).
   - which desktop is installed / display manager readers: aggiungere i nomi di sessione Ubuntu: `desktop_of_session_name()` (session.c:388-400) chiede xubuntu/lubuntu/kubuntu PRIMA di «ubuntu»; `gnome_session()` ha di nuovo il match con `ID` di os-release (session.c:793, 951); lettori lightdm `user-session` (`60-xubuntu.conf`) e sddm `[Autologin] Session` (`20-kubuntu.conf`) servono davvero su Xubuntu/Kubuntu.
   - GNOME session unit: non piu' `org.gnome.Shell@wayland.service` (GNOME 48) ma il template `org.gnome.Shell@.service`, istanza `@ubuntu` o `@user` letta da `Requires` di `gnome-session@<sessione>.target` (`unit_shell()`, session.c:3771; `SESSION_UNIT_SHELL_MODEL`, `SESSION_UNIT_GRAPHICAL` in session.h); drop-in nella cartella dell'ISTANZA, mai in `org.gnome.Shell@.service.d/`.
   - compositor: XFCE e LXQt usano il labwc della distribuzione, 0.9.3 su wlroots 0.19.2 di sistema (non 0.8.3); KDE usa il labwc NOSTRO (`/usr/libexec/remotix/labwc`, labwc 0.9.3 + wlroots 0.19.2 con una patch, collegato in statico; `build/labwc-ospite/`; `LABWC ?= /usr/libexec/remotix/labwc` in `Makefile`, `REMOTIX_LABWC` in `kwin.c`, `access(REMOTIX_LABWC, X_OK)`), perche' quello di Ubuntu lascia KWin >= 6.5 sul primo fotogramma; senza di esso `--virtual` (fallback dichiarato).
   - KWin quirks: KWin 6.6.7 (non 6.3); `kwin_poke()` e `capture_frame_lost()` sono quirk nuovi.
   - boxes: la riga e' falsa su Ubuntu. Container (`boxes/Containerfile`, `box.sh`: nomi `rxu-<de>`, porte ssh 2221-2224, REMOTIX 8821-8824, gnome=Ubuntu, kde=Kubuntu, xfce=Xubuntu, lxqt=Lubuntu; browser snap `firefox`/`thunderbird`/`chromium-browser` esclusi con pin -1; kit `task-<de>-desktop` e `set-dm.sh` non piu' pertinenti: i flavour si installano con i metapacchetti Ubuntu) e banco VM (`prove/banco-vm/box.sh`, `fresh-vm.sh`, porte 8841-8844, ssh 2341-2344).
   - tests: `prove/check-package.py` solo commento; `server/prepara-server.sh` usa `/media/REMOTIX-UBUNTU` e lo storage podman condiviso con Debian (`PODMAN_BASE=/media/REMOTIX-DEBIAN`).
3. **«What the clean-up removed, kept and risked»** — da riscrivere. La tabella «Branches removed in tranche 1» e' una storia Debian e su Ubuntu quasi meta' del codice e' tornata (prove: grep nell'albero Ubuntu):
   - Ubuntu session names in `desktop_of_session_name()`: TORNATI (session.c:388-400).
   - os-release match in `gnome_session()`: TORNATO (session.c:793, 951).
   - GNOME 50 template branch of `unit_shell()`: TORNATO (session.c:3771; `SESSION_UNIT_SHELL_48` sparito).
   - D-153 folder discovery (`local_session()`): TORNATA, con `Xsession.d/60x11-common_xdg_path` (session.c:2906, 2990, 3012) e un campo `LocalSession.common` (`/usr/share/gnome` dallo snippet `profile.d/gnome-session_gnomerc.sh`, solo se GNOME o login X11).
   - the own-labwc build switch (`LABWC=`): TORNATO in forma diversa (percorso fisso di build, non interruttore di run-time).
   - EI-ping fallback: ancora RIMOSSO (`MINIMI` ha `libei-1.0:1.3.901`; Makefile:409).
   - SELinux in `child.c`/`walls.c`: ancora ASSENTE (grep).
   - 90-default-privs branch, 1.0->1.5 upgrade machinery: ancora assenti (diff non li tocca).
   - «What stays and why» e «Risks recorded by tranche 1»: il rischio D-153/x11-common di Debian non c'e' piu' su Ubuntu (lo script esiste in 26.04: `studio/3` §2.3, x11-common 1:7.7+26ubuntu1, `[V]`). «Still to do (tranche 2)» («remaining Ubuntu and Xubuntu detection, Ubuntu emulation of XDG_*») e' ora codice vivo e deve essere descritto, non elencato come lavoro da fare; rimando «Appendix C» ancora valido come titolo.
4. **«A checklist for porting to another distribution»** — da correggere. Punti: (a) `MINIMI` invariati nel Makefile: openssl 3.5.0, ngtcp2/nghttp3 1.25.0/1.18.0, libei 1.3.901, pipewire 0.3.48, gio 2.80, opus 1.3, vulkan 1.3.274; nessun testo fuori posto; (b) «Rewrite the package»: la lista R4/R13/R14/R23 resta, con i controlli nuovi su labwc (`R4 ldd-labwc`, `labwc-source`, `R23 labwc-source-riproducibile`); (c) AppArmor: aggiungere la lezione C4 (il kernel di Ubuntu media i socket `unix`; i container non lo mostrano) e il punto «un `deny` vale anche in complain»; (d) «Make the boxes»: aggiungere che su Ubuntu serve un banco con sistema installato davvero, DM vero, AppArmor e snap (C4, C5, `B1` del registro); `check-package` non e' nel banco VM; (e) dconf: nuovo punto «a porting target with snaps/Flutter needs the locks as a system database». La frase «it has not been exercised, because no second distribution exists yet» e' falsa: questo ramo e' il secondo porting (Ubuntu 26.04) e il manuale puo' dire cosa e' stato davvero incontrato.
5. **«Adding a message to RCP/1»** — vale com'e'. Controllo: `rcp.c` +8 righe nel diff (solo `rcp_admitted_waiting()`), `rcp.h` +2 (dichiarazione), `msgrate.h` non toccato; i tipi `T_*`, `measure_fields()`, `control_class()` invariati. Un solo dettaglio utile: la funzione nuova `wt_dismiss_user_session_over()` (`webtransport.c`) e' un esempio di farewell trattenuto fino al «fixed second» (`rcp_dismiss_login()`).
6. **«Adding a desktop»** — da correggere: (i) il punto «Detection»: oggi i nomi di sessione includono i gusti Ubuntu e `desktop_session()` e' piu' complesso (stesso file, conta ~8800 righe); (ii) «Packaging»: aggiungere `session_missing_component()` (session.h; `labwc` per XFCE/LXQt, ritorna NULL se nulla manca) e che `main.c` risponde 0x0E «the desktop (X) cannot start: `labwc` is not installed on this server» PRIMA di far nascere il figlio; il `postinst` avvisa se XFCE/LXQt sono soli; (iii) «Tests»: dizionari ora con le porte 8821-8824 (container) e 8841-8844 (VM, `RX_BANCO=vm`) in `lib.py`; (iv) `box.sh` e `Containerfile` sono quelli Ubuntu, il banco VM ha il suo `box.sh`. Il passo «enumeration at the END» e «SESSION_DESKTOP_» restano veri (session.h: nessun enum cambiato).
7. **«Adding a video codec»** — vale com'e'. Controllo: `encoder.c`, `vadirect.c`, `vulkanvideo.c`, `rcp.h` codec numbers non toccati dal diff. Il box «State of HEVC» riferisce il giro Debian del 17 nov: per Ubuntu «non verificato» (dire solo che la nota e' di Debian).
8. **«Adding a check to prove/»** — da correggere.
   - «twelve check-*.py files; all.sh runs eleven»: i file sono 13 (`ls prove/check-*.py`, 13 anche su main) e `all.sh` ha 15 righe `run` su 12 file diversi, `check-package.py` a parte (il testo e' gia' vecchio su main: `check-prelocal.py` non era contato).
   - Aggiungere (prova: `prove/all.sh`): `RX_BANCO=vm` (banco VM, `fresh-vm.sh`, porte 884x, `RX_TEMPO=2`), `--clean`, `--only label,label` (esce 3 se verde ma parziale), verdetti `SKIP`/`NOTE` (mai PASS), regola «NO CHECK PRODUCED A PASS»; `lib.sweep()` ha i prefissi `bc|lc|mu|rs|ac|cb|bn|dkf?|md|in|ph|pl`; `check-ban.py` usa `RX_BAN_ADDR`/`10.0.2.2` nelle VM.
   - `prove/check-input.py`: i nomi sono `page-cad-hidden` e `page-ctrl-alt-end-passes` (gia' cosi' su Ubuntu, allineati a DECISIONS-11 §11.54; vedi ch24).

(a) COSE NUOVE: sezione «Porting from Debian to Ubuntu: what changed in practice» (in S2 o come nuova S3-bis): GNOME 50 template, labwc nostro, modello dconf (profilo di runtime, DB di sistema, ripiego), AppArmor 7.0 e socket `unix`, needrestart, snap/Flutter, `session_missing_component`, sudo-rs/uutils nelle prove (`TERMINAL gnome = ptyxis`, messaggi di sudo-rs in `check-desktop.py`), banco VM con vfio. Una voce dedicata a «what a second port found that the first did not» (C4, C5, B1).
(b) DA TOGLIERE: «Debian 13 (trixie)», «labwc 0.8.3», «KWin 6.3 (trixie)», `org.gnome.Shell@wayland.service (GNOME 48)`, `task-<de>-desktop`/`gdm3`/`set-dm.sh` come meccanismo dei box, «no second distribution exists yet», la tabella di S3 nella forma Debian.
(c) rif(): «Where the code is Debian-specific» (citato da ch21), «Appendix C — Known issues and open points», «Testing», «Build and release», «The RCP/1 protocol», «Conventions», «The four desktops», «Video encoding», «The four test boxes». Il titolo della sezione S2 va cambiato in «...Debian-specific» -> es. «Where the code depends on the distribution»; se cambia, aggiornare `rif()` in ch21 S1 e in altri capitoli. Stile: `steps([...])` per le procedure, `warn` per le regole, una tabella per aree.

---

## ch21_conventions — «Conventions» (167 righe, 6 sezioni)

1. **«The written rules and what the tree does with them»** — da correggere. La tabella cita `CLAUDE.md` (invariato nel ramo, dice «Debian trixie only»): riga 1 «Debian trixie only; four desktops; no distribution detection» — su Ubuntu il codice rileva davvero le sessioni Ubuntu (S2/ch20), quindi «no distro detection» e' falso cosi' com'e'; riga 8 «dev server's paths» -> `/media/REMOTIX-UBUNTU` (`build-deb.sh`, `prepara-server.sh`); riga «licences ship in the package» invariata (`debian/copyright` + `THIRD-PARTY-LICENSES`, ora anche labwc/wlroots, `LICENSE.md` §8 riscritto per Ubuntu: «labwc as the separate program `/usr/libexec/remotix/labwc`» e sorgente corrispondente `remotix-<ver>-labwc-source.tar.gz`); «installed disabled, not started»: `--no-enable --no-start` invariato. Le altre righe valgono.
2. **«Names, language and the Italian that remains»** — da correggere.
   - «45 of the 53 headers» / «the other eight»: verificato su Ubuntu e su main con lo stesso grep (45 `REMOTIX_*_H`, 53 con un guard `#ifndef X_H`, 6 senza: `audio.h kwin.h rcp.h vulkanvideo_rgb_nv12_spv.h wlr_input.h wlroots.h`): vale.
   - «registro_dice() ... 1171 uses»: il conteggio non e' riproducibile (`grep -o 'registro_dice(' src/*.c src/*.h` = 1202 su main, 1261 su Ubuntu; righe che lo contengono: 1207 e 1266). Ricontare con un metodo scritto.
   - «The text of the project is English: comments, log lines, messages, documents»: falso per i documenti. `docs/REGISTRO-problemi.md`, `PIANO.md`, `studio/*.md`, `docs/PULIZIA-tranche1.md`, `INVENTARIO-non-debian.md` sono in italiano; non c'erano nuove frasi italiane nei commenti di `src/`, ma i nomi italiani nuovi (tutti da quotare in code): `server/vm-radeon.sh` e fratelli (`crea|accendi|spegni|ssh|stato|istantanea|ripristina|prova-avvio`, `vm-radeon-aggiorna.sh`, `-controllo.sh`, `-installa.sh`), `server/live-installa.sh`, `prove/banco-vm/` , variabili `RX_BANCO`, `RX_TEMPO`, `RX_BAN_ADDR`, `PACCHETTO`, `UTENTI`, il nome del pacchetto di prova `unione10`, cartelle `/media/REMOTIX-UBUNTU/{albero,pacchetti,prove,vm,log,lavoro,vm-radeon}`, `ospite` in `labwc-ospite`. In inglese il manuale deve tradurre il senso («labwc-ospite = guest labwc», `unione` = union, `giro` = round).
   - La lista «Italian that remains in identifiers»: `SORGENTI`, `OGGETTI`, `MINIMI`, ecc. del Makefile restano (Makefile cambia solo +6 righe: `LABWC`, `REMOTIX_LABWC`); `wt_chi`, `codificatore_chiedi_chiave`, `lung`, `tratta_*` invariati.
3. **«Comments, marks and references»** — da correggere solo nei numeri. Prova (`wc -l`, albero Ubuntu): C+H in `src/` 105 799 righe (main: 103 489); `page.html` 14 258 righe (main 14 255; il testo dice 14 255); `child.c` 12 671 (testo: 12 347, main 12 446), `rcp.c` 10 485 (testo 10 466, main 10 477), `webtransport.c` 9 618 (9 582, main 9 582), `session.c` 8 829 (7 374, main 7 404). I valori del testo Debian erano gia' vecchi rispetto a main. La tabella dei segni (stella, divieto, avviso, clessidra, `[M] [R] [S] [?]`) vale: `grep` nei commenti nuovi dello stesso formato (`⭐ 19 Nov 2026`, `[M]`, `[R]`). Citazioni morte (`CODER.md`, `STUDIES.md`, `phases/`, `benches/`) valgono ancora, anzi aumentano (`phases/17-the-installer.md` in `session.c:3755`).
4. **«Errors, fallbacks and invariants»** — vale com'e'. Controlli: `_Static_assert` = 12 anche su Ubuntu; invariante I3 (login fail-closed) confermata dalla nuova regola «an error answer counts as "not safe"» in `sentinel_shutdown_forbidden()`; «a fallback is declared in the log» e' esemplificata dal «DECLARED FALLBACK, D-015 (19 Nov 2026)» nel modello dconf (puo' diventare un esempio in piu'). `78` e `remotix.service`: non toccati.
5. **«Logging conventions for a writer of code»** — vale com'e'. Controllo: `log.c`, `log.h`, `REGISTRO-priorita.md` non sono nel diff; `registro_dice(LOG_CHILD, "⛔ ...")` e' lo stile dei nuovi messaggi (`main.c`, `child.c`). I due esempi nuovi di «what, not error» sono i log di `delivery_verdict` (`labwc` mancante) e `stage_refused_by_child`.
6. **«The layout of the tree and the habits around it»** — da correggere. Tabella: aggiungere `build/labwc-ospite/` (5 file), `studio/` (non coperta dal generatore di mappa: 40 file `.md` in italiano, studi 1-15 e `giro1-2*`), `prove/banco-vm/`, i 5+1 script `server/vm-radeon*`, `server/live-installa.sh`; `server/` ora tiene anche VM e live («paths under `/media/REMOTIX-UBUNTU`»); `boxes/` e' «four test boxes» ma `PIANO.md` dice che i container non esistono piu'. Rimuovere/riscrivere «paths under /media/REMOTIX-DEBIAN» e «the build script sets TMPDIR». Abitudini: «Temporary files never go to /tmp on the dev server» vale ancora (`build-deb.sh`: `TMPDIR=$WORK/tmp`); «Nothing is deleted...» vale (gli script VM dichiarano «Deletes nothing»); «Generated files are marked» invariato.

(a) COSE NUOVE (convenzioni nuove viste): marcatore dei limiti di un test (`SKIP` mai come PASS, `NOTE`); `[M]` datati 18-19 nov 2026 con dispositivo (`Ubuntu 26.04 box`, `rx-kde`); modello «three answers» per vita del desktop (`SESSION_LIFE_ALIVE|DEAD|UNKNOWN`: «non ho potuto guardare non e' chiuso», registro E3); regola «`deny` si scrive con le operazioni» (C4); tag `N5` per i problemi del revisore (session.c). Sezione consigliata «Conventions of the Ubuntu tree» breve.
(b) DA TOGLIERE: «Debian trixie only; four desktops» come prima riga; i conteggi `1171`, `102,000`, `12,347`, `10,466`, `7,374`, `14,255`; «paths under /media/REMOTIX-DEBIAN».
(c) STILE DI SCRITTURA (da dare agli scrittori, osservato in `manuals/sources/build.py` e nei capitoli):
   - Lingua: inglese tecnico, sobrio, frasi corte, nessuna frase italiana (il `--check` fallisce su frasi con >= 2 parole italiane da `ITALIAN_WORDS` fuori da `<code>`, `<pre>`, `<kbd>`; nei diagrammi SVG basta una parola di `ITALIAN_CHART_WORDS`). I nomi italiani reali vanno in `c("...")`, mai tradotti dentro il code.
   - Tono: dichiarativo, impersonale («The table lists...»), niente «we»; ogni affermazione dice la sua fonte (file, funzione, `docs/...` con §); quando non verificato: «not measured», «not verified», «no figure was found». Il codice vince sui commenti; i contrasti vanno in Appendix C.
   - Funzioni: helper `p`, `ul`, `ol`, `steps` (liste di passi), `h4`, `table`, `dl`, `note`, `warn`, `tip` (titolo breve opzionale: `note(txt, "Title.")`), `code`/`term` (blocchi: `term` colora prompt `$ `/`# ` e righe `error`), `tree`, `fig`/`flow`/`seq`, `ui()`, `key()`, `pill()`.
   - `p(..., lead=True)` per il primo paragrafo di ogni sezione (frase di apertura che dice cosa c'e').
   - Didascalie: tabelle e figure usano il segnaposto `«TAB» — Text` / `«FIG» — Text` (la numerazione «Table 19.3» la mette `number()`); la didascalia e' la stringa passata a `table(head, rows, cap)` (terzo argomento). Le tabelle accettano righe-gruppo: una stringa sola = riga a tutta larghezza.
   - `c("x")` per ogni identificatore, file e opzione del repository; `sysf("x")` per file/unita' della macchina non del repo (`/etc/dconf/db/remotix`, `org.gnome.Shell@ubuntu.service`); cio' che non sta nel repository ma deve apparire come codice va in `sysf`, altrimenti `--check` lo cerca in git e fallisce.
   - `--check`: ogni `c("nome()")` esiste nei sorgenti; ogni file citato esiste in git (o e' in `SYSTEM_FILES`: `remotix.conf`, `session.log`, `port.conf`, `60-xubuntu.conf`, `20-kubuntu.conf`, `display-manager.service`); ogni `REMOTIX_*` letto da `getenv` e' documentato e viceversa; ogni `RX-XXX-000` esiste.
   - `rif("Titolo esatto")` collega per titolo di sezione (deve esistere, altrimenti SystemExit): non rinominare una sezione senza cercare i `rif`. Il titolo dei capitoli «Appendix A/B/C» vale come tali.
   - Nomi in codice: file di prove e script (`check-*.py`), costanti in UPPER (`AUDIO_BUFFER_MS`), farewell come `0x04`; i «marchi» di commento (stella, divieto, avviso, clessidra) non vanno copiati nel testo del manuale.
   - Mai emoji. Mai numeri non verificati.

---

## ch22_structures — «Appendix A — Data structures and messages» (279 righe, 6 sezioni)

Verifica campo per campo: il diff `main..ubuntu-26.04` degli header cambia SOLO queste cose rilevanti per l'appendice (`git diff` di `rootside_proto.h`, `rootside.h`, `child.h`, `rcp.h`, `session.h`, `certificates.h`, `transport.h`, `budget.h`, `page.h`: solo `child.h`, `rcp.h`, `session.h` hanno diff):
- `struct body_stage` (child.c): campo nuovo `uint32_t fatal` in coda, `#define STAGE_MIN offsetof(struct body_stage, fatal)`; il genitore accetta il corpo vecchio senza `fatal` (letto come 0).
- `struct children` (child.c): nuovi `ChildStageRefused on_stage_refused` e `void *ctx_stage_refused`; nuovo tipo `ChildStageRefused` e `children_hook_stage_refused()` in `child.h`.
- `session.h`: nuovo `typedef enum { SESSION_LIFE_ALIVE = 0, SESSION_LIFE_DEAD = 1, SESSION_LIFE_UNKNOWN = 2 } SessionLife` e `session_life()`; `SESSION_UNIT_SHELL_48` rimosso, `SESSION_UNIT_SHELL_MODEL "org.gnome.Shell@.service"` e `SESSION_UNIT_GRAPHICAL "graphical-session.target"` aggiunti; `DCONF_SESSION_OBJECT` e' ora `session_dconf_object()` (non piu' una stringa costante); nuove: `session_missing_component()`, `session_dconf_keyfiles_write()`, `session_dconf_system_db_ensure()`; `session_kde_logout_watch()` ritorna `bool`. `DesktopSession`, `SessionState`, `SessionMonitor`: nessuna modifica (enum invariati, verificato nel diff).
- `rcp.h`: nuova `rcp_admitted_waiting()`; `rcp_hooks` invariata (stesso numero di hook: nessun campo aggiunto nel diff).
- `capture.h`, `kwin.h`, `mutter.h`, `input.h`, `sentinel.h`, `webtransport.h`: solo funzioni nuove o semantica (`capture_watch_sequence()`, `capture_frame_lost()`, `kwin_poke()`, `mutter_scale_to_one()`, `input_dropped()` ora vale anche per wlroots, `sentinel` accetta `na` oltre `no`, `wt_dismiss_user_session_over()`).
- Strutture private non elencate nel capitolo (non vanno aggiunte): `LocalSession.common` (session.c), `struct lock_mark`, campi di `Capture`.
- Non cambia: `RXR_VERSION 3`, `CHILD_VERSION 1`, `MAX_PIECE`, `FRAME_MAX`, tutti i tipi RXR e RCP, `RCP_CODEC_VIDEO_MAX`, i codici di farewell (nessuno nuovo in `rcp.h`).

1. **«The main C structures»** — da correggere. Riga `struct children`, `struct child`: citare il nuovo hook `on_stage_refused` (accanto agli hook gia' presenti). Riga `DesktopSession, SessionState, SessionMonitor` (session.h): aggiungere `SessionLife`. Riga `rcp_hooks`: «verify, video, input, canvas, layout, stage size, local session, clipboard, logout» resta vera; `rcp_admitted_waiting()` non e' un hook. Le altre righe: vale (nessun diff sugli struct citati; controllato).
2. **«The root-side protocol, message by message»** — vale com'e'. Controllo: `rootside_proto.h`, `rootside.h` non sono nel diff; `rootside.c` +1 riga (`session_dconf_system_db_ensure()` all'avvio del lato root, non un pacchetto). Il `warn` sui tre commenti in disaccordo vale (header immutati).
3. **«The PAM helper's packets»** — vale com'e'. Controllo: `helper.c`, `helper.h`: non nel diff.
4. **«Messages between the network side and a child»** — da correggere.
   - Riga 11 `MSG_STAGE`/`body_stage`: «bus, session state, capture take, monitors before and after, size, streams, fault text» + `fatal` (u32, 1 = lo stage e' stato rifiutato per la SCALA, guardia 2; nessun retry lo cura; il genitore manda 0x0E ai client e segna l'utente «closing»); corpo minimo `STAGE_MIN`.
   - Riga 15 `MSG_SESSION_FINISHED`: ora puo' arrivare PRIMA dello smontaggio dello stage (`session_over_early()`), solo con `session_life()==DEAD`; il genitore mette subito il figlio «closing» (`closing_asked_ms`).
   - Riga 20 `MSG_LOCAL_FOUND`: il testo «did the light close and is leaving» e' falso; ora arriva PRIMA della chiusura leggera («is going to do the light close», `child.c`, `handle()`).
   - Tabelle di enumerazioni: invariate.
5. **«The unblock command socket»** — vale com'e'. Controllo: `command.c` non nel diff; `prove/check-ban.py` cambia solo l'indirizzo di prova (`10.0.2.2` nelle VM).
6. **«Index of RCP/1 messages and farewell reasons»** — da correggere solo nelle descrizioni di due codici. `0x0E RCP_SESSION_UNSERVABLE` «cap, closing desktop, no stage, unknown layout» + (sei strade, commento aggiornato in `page.html`): il compositor del desktop non e' installato (`main.c` `delivery_verdict`, `session_missing_component()`), e lo stage rifiutato per la scala (`stage_refused_by_child`). `0x10 RCP_SESSION_TERMINATED` e `0x04`: ora via `wt_dismiss_user_session_over()` (una connessione ancora in attesa di PAM non riceve piu' un falso 0x10: `[M]` 18 nov, rientro 8-10.5 s dopo il logout; un login gia' ammesso ma dentro il «fixed second» riceve il farewell al posto di ADMITTED). Tutti i numeri hex della tabella invariati.

(a) COSE NUOVE: nulla di strutturalmente nuovo da aggiungere in tabelle principali; aggiungere una riga `SessionLife` e una nota breve sul campo `fatal` («appended at the end of the struct so that an older body still reads»).
(b) DA TOGLIERE: la descrizione «child did the light close and is leaving» e la dizione 0x0E a quattro cause.
(c) rif(): «Overall architecture», «Login and its defences», «Startup and life cycle», «Transport», «The RCP/1 protocol», «Quality, degradation and budget», «The four desktops», «The local-login hold». Stile: tabelle a gruppi con `"Processes and the closed list"` come riga-gruppo, ogni riga un `c("struct x")`.

---

## ch23_map — «Appendix B — File map» (250 righe, 1 sezione)

1. **«Every file of the tree»** — da correggere. Il generatore e' in regola: `file_map()` fallisce se mancano o eccedono file; ho confrontato `git ls-files src debian build prove boxes server` (al netto di wasm/png/svg/sha256) con i percorsi citati: **nessun file mancante e nessuno in eccesso** (0 differenze). Restano da riempire le righe `TODO(Ubuntu writers)` (15) e da correggere descrizioni di file esistenti. Tabella dei ruoli proposti (letti i file):
   - `debian/remotix.install` — «dh_install list: copies debian/needrestart/remotix.conf to /etc/needrestart/conf.d»
   - `debian/needrestart/remotix.conf` — «needrestart drop-in: remotix.service is never restarted by itself (a restart closes every remote desktop, DECISIONS-11 §11.56); it is only listed for manual restart»
   - `build/labwc-ospite/README` — «why and how of our labwc: hosts the nested KWin >= 6.5; labwc 0.9.3 + wlroots 0.19.2 patched, static, /usr/libexec/remotix/labwc; only KDE uses it»
   - `build/labwc-ospite/VERSIONS` — «pinned names, versions, tarballs, sha256 and URLs of labwc and wlroots»
   - `build/labwc-ospite/build.sh` — «builds our labwc with meson from the two checked tarballs and the patch; fails if the binary links any libwlroots»
   - `build/labwc-ospite/fetch.sh` — «fetches the two upstream tarballs into a folder and verifies them against VERSIONS»
   - `build/labwc-ospite/wlroots-0.19.2-remotix-presented-root.patch` — «our wlroots patch (types/scene/surface.c: the root of a surface on an output counts as presented; MIT)»
   - `server/live-installa.sh` — «test installer for a real machine booted from an Ubuntu 26.04 live image: apt install of the .deb, enable --now remotix, two test users; re-runnable»
   - `server/vm-radeon.sh` — «real-system test VMs (desktop ISOs installed, UEFI, KVM) with the server's Radeon passed through by vfio-pci: crea, accendi, spegni, ssh, stato, istantanea, ripristina, prova-avvio»
   - `server/vm-radeon-aggiorna.sh` — «updates one VM as a user would (apt full-upgrade, snap refresh, reboot) without the Radeon, then snapshot»
   - `server/vm-radeon-controllo.sh` — «short check of one VM with the Radeon: render node, journal, one login, logout check, timed power on/off»
   - `server/vm-radeon-installa.sh` — «installs a .deb in one VM as the administrator would, without opening a session, then snapshot»
   - `server/vm-radeon-login-test.py` — «opens the page in the Radeon VM with lib.py's browser and logs in as the test user; prints facts, exit 0 if a session was reached»
   - `prove/banco-vm/box.sh` — «VM bench: the same commands as boxes/box.sh (ssh as root with the bench key, install, rootkey, status) for the four QEMU VMs; reset is not available»
   - `prove/banco-vm/fresh-vm.sh` — «VM bench: brings a running VM to a clean state (users, drop-ins, ban state, tools) and optionally reinstalls a .deb; the state is checked afterwards»
   Per i ruoli ho letto gli header dei file (non verificato dove non c'e' header).
   - Descrizioni di file esistenti da correggere (verificate nel diff): `build/build-deb.sh` «builds the .deb in a Debian 13 container» -> Ubuntu 26.04 container (e produce l'archivio sorgente di labwc); `build/Containerfile` (ubuntu:26.04 + strumenti labwc); `debian/remotix.postinst` (+ database dconf, avviso labwc), `debian/remotix.postrm` (+ rimuove DB dconf e `~/.config/dconf/remotix`), `debian/control` (Build-Depends labwc), `debian/remotix_network.apparmor` (regole `unix` e XKB), `debian/copyright` (labwc/wlroots), `src/Makefile` («two programs» + `LABWC`/`REMOTIX_LABWC`), `src/capture.c` (+ osservazione della sequenza dei buffer e fotogrammi persi), `src/kwin.c` («screencast through KWin; nested in OUR labwc; kwin_poke»), `src/mutter.c` (+ `mutter_scale_to_one()`), `src/session.c` (+ modello dconf runtime/DB di sistema, GNOME 50, nomi di sessione Ubuntu, pannello XFCE, KDE logout watch, session_life), `src/child.c` (+ scala rifiutata, farewell anticipato, `SESSION_LIFE`), `src/sentinel.c` (accetta `na`), `src/webtransport.c` (`wt_dismiss_user_session_over`), `src/wlroots.c` («labwc di sistema per XFCE e LXQt»), `boxes/*` («Ubuntu 26.04 boxes (rxu-*), browser snap esclusi»), `server/prepara-server.sh` («REMOTIX-UBUNTU, podman condiviso con Debian»), `server/vm.sh`, `prove/lib.py`, `prove/all.sh`, `prove/fresh.sh`, `prove/check-ban.py`, `prove/check-desktop.py`, `prove/check-input.py`, `prove/window-input.py`, `prove/package-snap.py`, `prove/avlib.py`, `prove/base-check.py`, `prove/check-package.py` (ritocchi).
   - Riga finale `Manual sources`: `_manual_rows()` descrive `technical-debian13/` come «chapter of the Debian 13 manual» e `technical-ubuntu26.04/` come «chapter of this manual»: il ramo ha il manuale di Debian ancora nell'albero (`ch12_desktops.py` di Debian e' anche nel diff, +19 righe): decidere se tenerlo nella mappa (`PIANO.md` consiglia di toglierlo).
   - La frase introduttiva citata in `p(...)` («the chapter list at the start of this manual») resta valida.

(a) COSE NUOVE: nessun file nuovo in `src/`; nuove cartelle: `build/labwc-ospite/`, `prove/banco-vm/`, i 6 script `server/`; `studio/` non entra nella mappa (non e' tra le cartelle di `sorgenti()`).
(b) DA TOGLIERE: «Debian 13 container» dal ruolo di `build-deb.sh`; i ruoli generici di `boxes/*` che dicono «four boxes» senza dire che sono container Ubuntu.
(c) rif(): nessuno nel capitolo. Stile: una sola `file_map(MAP, "«TAB» — ...")` con gruppi; descrizioni brevi, minuscole, senza punto finale; ogni gruppo con titolo e cartella tra parentesi.

---

## ch24_problems — «Appendix C — Known issues and open points» (185 righe, 9 sezioni)

Confronto con `docs/REGISTRO-problemi.md` (287 righe nel ramo; voci nuove rispetto a main: B3-bis, C3, C4, C5, D «KDE (Kubuntu 26.04, Plasma 6.6)», E1 riscritta, E3, E4). Confronto con `PIANO.md` (68 righe, riepilogo 19 nov).

1. **«How to read this appendix»** — da correggere. «The package has been run through `prove/all.sh` on four desktops on 17 Nov 2026»: per Ubuntu il giro completo automatico e' registrato solo su GNOME (`PIANO.md`); XFCE/LXQt/KDE: il giro adattato ai VM esiste (`RX_BANCO=vm`) ma l'esito non e' nell'albero; prove a mano del proprietario sulle 4 VM e sulle 4 live, accesso locale solo su Ubuntu e Kubuntu. «1.0.0» come etichetta resta (pacchetto `unione10`, `remotix_1.0.0-1+ubuntu26.04_amd64.deb`).
2. **«What is unverified»** — da correggere.
   - «AppArmor in a session»: su Debian VM senza scheda; su Ubuntu il profilo e' stato osservato in sessioni vere (4 live + 4 VM con Radeon) ma sempre in complain: l'enforce non e' stato provato; limiti noti C4 (autobind permesso) e xkb-data 2.46 (cartella vera diversa dal link). Prova: `debian/remotix_network.apparmor`, registro C4.
   - «A real phone»: aggiungere E4 (Android, Chrome, scatti, non distinto).
   - «GNOME, first tap after login»: invariato, non rimisurato su Mutter 50 (non verificato).
   - «NVIDIA»: invariato. «4096x2304»: invariato; non verificato su Ubuntu. «Capacity»: invariato.
   - «Reproducible build»: il codice `TWICE=1` ora copre anche il sorgente del labwc (`R23 labwc-source-riproducibile`); nessun esito Ubuntu registrato nell'albero: non verificato.
   - «Local-session refusals»: Ubuntu e Kubuntu provati dal proprietario con la schermata di accesso vera (live); le prove automatiche simulano ancora l'accesso (`check-prelocal.py`).
   - «Versions of XFCE and LXQt on trixie»: riscrivere per Ubuntu (xfce4-session 4.20.4, xfce4-panel 4.20.7, lxqt-session 2.3.0, lxqt-panel 2.3.2, labwc 0.9.3: studi, `[V]` nei container); i commenti che citano 2.1.x e labwc 0.8.3 restano nel codice (studio 11 SCOPERTA 21).
   - «Measured figures in comments»: vale; aggiungere le misure nuove nei commenti (`[M]` su KWin 6.6.7, Mutter 50).
3. **«Known limits and what was proven»** — da correggere.
   - XFCE sfondo nero: il registro E1 ora ha la causa (libxfce4windowing 4.20.2 perde il messaggio del compositore se arriva prima che lo schermo sia noto; corretta da 4.20.4); la «unverified hypothesis» e' superata. Versione di libxfce4windowing su Ubuntu 26.04: non verificato.
   - «How the local-login hold was proven»: aggiornare (Ubuntu 26.04: GNOME e KDE provati dal proprietario su live; XFCE/LXQt: VM, non live? PIANO dice «prova accesso locale» su Ubuntu e Kubuntu; XFCE/LXQt non verificato).
   - GNOME `pkexec`: la riga `users-shell-and-environment` resta rossa anche su Ubuntu (PIANO); la causa «SHELL empty by design» vale.
   - RealtimeKit nei container: da riscrivere/spostare (i container non esistono piu'; E2/B2 restano come storia).
   - Nuovi limiti noti da aggiungere: kernel con mediazione `unix` (C4); snap/Flutter e dconf (C5: `~/.config/dconf/remotix`, DB di sistema, ripiego, `Writer/remotix`); la scala dell'utente: il figlio prova UNA volta `mutter_scale_to_one()` (`ApplyMonitorsConfig` temporaneo, 3 chiamate D-Bus di max 15 s l'una) e, se non basta, rifiuta lo stage (0x0E, `fatal`); logout presto su KDE con `plasma-shutdown` rifiutato da systemd (D: ripetizione dello stop dopo 4 s, forzatura dopo circa un minuto).
4. **«Open points in the server»** — da correggere. Vale: `No unblock`, `No firewall` (aggiungere `ufw ENABLED=no` su Ubuntu), `Page certificate name`, `Root-side login pauses`, `Timing tail`, `Faillock`, `Quotas`, `Trust boundaries`, `Power belts`, `TERMINATE_SESSION`, `PACE`, `Single-process mode`, `Clocks`, `Mounts`, `Certificate pins`, `Session id`. Da correggere: «Kernel requirements: Landlock needs kernel 6.12»: il kernel di Ubuntu 26.04 e' 7.0 (registro C4); «Found-again desktop with a local session»: invariato. Nuovi punti: E3 (foto del gestore utente vecchia; «non ho potuto guardare» trattato come «chiuso» in due punti di `session.c`/`child.c`, non corretto, caso forzato); `session_over_early()` non attivo su KDE (aspetta una prova su macchina viva).
5. **«Open points in capture and encoding»** — da correggere.
   - «KDE and labwc: KDE depends on the system labwc... only Plasma 6.3»: FALSO su Ubuntu. KDE usa il labwc nostro (`/usr/libexec/remotix/labwc`), `--virtual` solo se manca; descritto KWin 6.6.7 (il resto del ramo dice «KWin >= 6.5»); il labwc di sistema resta solo per XFCE/LXQt.
   - «Startup codec probe: default renderD128, two cards»: invariato. «No card...»: invariato. «Dead AV1», «Shader header», «Budget...»: invariati (encoder.c, budget.h non nel diff). «HEVC»: giro Debian; Ubuntu non verificato.
   - Nuovo: buffer persi di KWin (`capture.h`): la cura e' un «poke» (`kwin_poke()`) ogni 200 ms al massimo, solo su un buco di numerazione, mai su desktop fermo; la perdita e' di PipeWire/KWin, non sintonizzabile da noi.
6. **«Open points in the page, input, audio and clipboard»** — da correggere. «Ctrl+Alt+Del button ... `page-cad-button` and `page-ctrl-alt-end` fail»: nel ramo Ubuntu i controlli sono gia' stati allineati alla decisione (`page-cad-hidden`, `page-ctrl-alt-end-passes`, `check-input.py`; registro B3): il testo va riscritto (il bottone e' nascosto fuori da `?logbook` per decisione, e le prove lo dicono). Gli altri punti: invariati (diff di `page.html` solo commenti: `0x0E` ora «SIX routes»). In piu': su Ubuntu `window-input.py` legge il rilascio dagli eventi grezzi (B3-bis, GTK 4.22).
7. **«Open points in the desktops and logging»** — da correggere. XFCE: le voci valgono; aggiungere pannello (XFCE panel integrity: `xfce_panel_integrity()`, plugin perso, `studio/9`) e sfondo nero (E1). GNOME: aggiungere l'avviso «Screen Lock disabled» e il file `lock-warning-shown` (sessione, 18-19 nov), e che la scala >1 ora viene prima riportata a 1; «SHELL empty» invariato. KDE: «only KDE has the watch that finishes a Log Out systemd refused»: ora `session_kde_logout_watch()` e' `bool` e Plasma 6.6 non rilascia il nome `org.kde.Shutdown`; vale. LXQt: aggiungere i gestori di composizione X11 (`picom`/`compton`/`xcompmgr`) e `blueman.desktop` nascosto; `lubuntu-update` autostart. «Environment variables REMOTIX_VPP_PADDING...» invariato. «Log priorities: About 700 call sites»: non riverificato.
8. **«Open points in testing and build»** — da riscrivere. «Final round... XFCE 111/118, LXQt 112/118...» e «server logs `prove/log/v100c-<de>.out`» sono Debian: per Ubuntu non verificato (nessun log nel ramo). «Package check ... 8 PASS plus apparmor BLOCKED»: per Ubuntu `check-package` non e' nel banco VM («package ... SKIP»), e non risulta mai eseguito su Ubuntu (`studio/11` S2.7). «Check scripts»: `fresh.sh`/`lib.py` ora cercano `prove/boxes` e, se manca, `../boxes` (vale su main e su Ubuntu), `lib.sweep()` include `in`, `ph`, `pl` (cosi' anche su main: la riga Debian e' gia' stantia), `headless-multi.sh`, `lifecycle-window.py` senza chiamante (non riverificato), `base-check.py` e `check-base.py` duplicati. «Unit tests», «Build» (`make` richiede `TWIN=none`; `debian/rules` lo passa): vale. «Clean-up: tranche 2 open ... A port needs the removed SELinux and Ubuntu code again»: ora il codice Ubuntu c'e'; SELinux ancora no. Nuovo: banco VM e `RX_TEMPO`, SKIP dichiarati, «NO CHECK PRODUCED A PASS», `--only` esce con 3.
9. **«Contradictions between code, comments and documents»** — da correggere. Le righe vere su main restano vere (stessi file, solo numeri di riga spostati). Riscrivere: «Stale installer text main.c:445-473 ...» — il messaggio `PAM service «remotix» DOES NOT EXIST` esiste ancora (`main.c:467`, nomina Fedora/Arch); «Desktops survive the stop» — `main.c:3967-3972` dice ancora «the desktops stay alive» (non corretto sul ramo); «KWin --virtual» — ora e' `REMOTIX_LABWC`, non `labwc in PATH`; «Settings comments: local_session() returns an empty structure on Debian 13» — FALSO su Ubuntu (funzione viva); «Page caps ... the page is 937 155 bytes» — `page.html` e' 937 399 byte nel ramo (937 180 su main); «PIANO.md: 8 utenti vs 10 / check-package 8/8»: il `PIANO.md` del ramo e' un altro testo (68 righe), la riga va tolta. Aggiungere nuove contraddizioni verificate: `DECISIONS-11.md` §11.55 «The logind session is kept alive through `--session-fd`» e' vero per Debian, il ramo non la passa piu' (nota di 4 righe nello stesso §, systemd 258+: logind tiene la sessione con il pidfd del leader); commenti `session.h:216,230,245`, `shape.c:133` con labwc 0.8.3 / lxqt 2.1.1 (studio 11 SCOPERTA 21); `child.c:1674` `ConditionEnvironment` (50 usa `Assert`), `input.c:2059-2084` «Mutter non offre la leva», `rediscover.h:27` `gnome-session-binary`.

(a) COSE NUOVE (voci da aggiungere): C4 (AppArmor `deny unix` e kernel Ubuntu), C5 (dconf/snap/Flutter, ripiego, limiti noti 1-3, «non provato sul campo»: ramo «vita SCONOSCIUTA» e «database diverso»), B3-bis (GTK 4.22 e test window), D KDE/Plasma 6.6 (uscita nei primi secondi), E1 (XFCE sfondo nero: causa e versione), E3, E4, B1/B2 (nessuna schermata di accesso nei container; RealtimeKit 25 s) come storia; PIANO: wireplumber (avviso solo sulla VM, aperto non bloccante); `Aperti`: «`user@UID.service` failed (timeout) dopo il Log Out (mpris-proxy)» non spiegato; `systemd-oomd` non gestito; `pam_motd`/`pam_sss` latenza non misurata; `gnome-remote-desktop` di sistema (studio 11, SCOPERTE 13-27). Proposta: nuove sezioni «Ubuntu: what real machines showed that the boxes did not» (C4, C5, B3-bis) e «Ubuntu: open points» (E3, E4, SCOPERTE ancora aperte, lette dal PIANO e studio 11: segnare «not re-checked» perche' studio 11 e' precedente alle correzioni del 19 nov).
(b) DA TOGLIERE: conteggi del giro 17 nov, «on Debian 13 live systems started on the server», la riga PIANO del 17 nov, «on trixie».
(c) rif(): «Desktops found again after a restart»; il capitolo e' citato da ch05..ch18 come «Appendix C — Known issues and open points» (titolo da non cambiare). Stile: ogni sezione e' `items([[Item, State], ...], "«TAB» — ...")` (due colonne), `<code>` nei testi lunghi, `<b>` per «Unverified hypothesis»; la tabella finale `CONTRA` ha tre colonne (Subject, Where, What disagrees).

---

## ch25_glossary — «Glossary» (29 righe, 1 sezione)

1. **«Terms used in this manual»** — da correggere.
   - «AppArmor … complain mode»: vale (profilo ancora `flags=(complain,...)`).
   - «Compositor ... labwc for XFCE and LXQt, Mutter for GNOME, KWin for KDE»: incompleto: KDE e' KWin NIDIFICATO in un labwc nostro (`/usr/libexec/remotix/labwc`); labwc di distribuzione per XFCE/LXQt.
   - «Found again»: valido (codice rediscover non toccato).
   - «Vulkan Video ... tried first» / «VA-API ... (Intel today)»: `encoder.c` non toccato. Il server di sviluppo ha una Radeon; il testo «(Intel today)» e' un'affermazione sulla scheda: non verificato per Ubuntu (VM con Radeon; Mesa VA in `mesa-libgallium`).
   - Mancano termini (da aggiungere): «Our labwc» / «Hosting labwc» (`build/labwc-ospite/`), «Lost frame / poke», «Session life» (alive/dead/unknown), «Runtime dconf profile», «System dconf database» (`/etc/dconf/db/remotix`), «Declared fallback» (dconf), «Fixed second», «needrestart drop-in», «VM bench» (`RX_BANCO=vm`), «sudo-rs / rust-coreutils» (solo se il manuale li usa), «Snap» e «Flutter program» (C5), «unione» no.
   - Le altre voci (Ban, Child, Detach, HTTP/3, Local excludes remote, Log Out, Network side, No orphan desktops, Opus, PAM, PipeWire, QUIC, RCP/1, Root side, Sentinel, Stage, Walls, WebTransport): valgono; la voce «Sentinel» resta («asks logind...») anche con `na`.

(a) COSE NUOVE: le voci elencate sopra; ordinate alfabeticamente come le attuali; usare `dl(TERMS, "gloss")` invariato.
(b) DA TOGLIERE: nulla di Debian vero e proprio; solo «(Intel today)» se non verificato.
(c) rif(): nessuno nel glossario. Stile: coppie `(term, "<code>...</code> definition")`, una frase.

---

## Riepilogo di consegna

Sezioni per capitolo: ch19 = 1 vale / 3 correggere / 3 riscrivere (7); ch20 = 2 / 4 / 2 (8); ch21 = 2 / 4 / 0 (6); ch22 = 3 / 3 / 0 (6); ch23 = 0 / 1 / 0 (1); ch24 = 0 / 8 / 1 (9); ch25 = 0 / 1 / 0 (1). Totale: 8 vale / 24 correggere / 6 riscrivere, su 38 sezioni.

Cose da sapere e decisioni per il caposquadra: (1) `CLAUDE.md` e `PIANO.md` del ramo: `CLAUDE.md` dice ancora «Debian trixie only»; il manuale lo cita in ch21. (2) La prova dell'esito del giro Ubuntu non e' nell'albero (log su `/media/REMOTIX-UBUNTU/log/` sul server): i capitoli ch19/ch24 vanno scritti senza cifre di test Ubuntu, oppure un agente con accesso al server deve leggerle. (3) Il manuale di Debian e' ancora in `manuals/sources/technical-debian13/` (e `ch12_desktops.py` Debian e' nel diff): decidere se la mappa (`ch23`) lo elenca. (4) Nei capitoli ch21 e ch24 molte cifre del manuale Debian erano gia' stantie rispetto a `main`: ricontare sul ramo Ubuntu con i comandi indicati qui sopra.


---------------------------------------------------------------------------------------------------


# PARTE 2 — Cose NUOVE di Ubuntu e dove metterle

Sintesi degli elenchi (a) dei cinque gruppi; i dettagli e le righe di registro citabili sono nei frammenti. Proposta di posto:

| Novita' | Dove | Fonti |
|---|---|---|
| Sessione `ubuntu` di GNOME 50 (scelta per nome os-release, regola D8), template `org.gnome.Shell@.service` con istanze `@ubuntu`/`@user`, `--mode=%i`, guardia `graphical-session.target`, `gnome-session-init-worker`, estensioni | ch12 §6 (riscrittura), ch03 §4, ch02 §3 | `session.c`, `studio/1`, `2`, `3`, `12-verifiche-gnome` |
| Modello dconf D-015 nuovo: profilo di runtime `$XDG_RUNTIME_DIR/dconf/profile`, `system-db:remotix` (`/etc/dconf/db/remotix`), `user-db:remotix` (`~/.config/dconf/remotix`), `session_dconf_system_db_ensure()`, `session_dconf_keyfiles_write()`, `remotix --dconf-keyfiles`, ripiego dichiarato, casi dell'amministratore, tre esiti di `session_life` (alive/dead/unknown), motivo = snap/Flutter | ch12 §6 (nuova sottosezione), ch15 (file, postinst), ch02 §3/§11, ch03 §4; storia in ch24 | registro C5, E3; `session.c`, `main.c`, `debian/rules`, `debian/remotix.postinst` |
| Scala dell'utente: due chiavi dconf (`scaling-factor`, `ubuntu-lock-on-suspend`), `mutter_scale_to_one()`, rifiuto dello stage (`fatal`, 0x0E) e chiusura sessione | ch12 §6, ch06 §2, ch05 §12, ch14 §5 | `mutter.c`, `child.c`, `webtransport.c` |
| `lock-warning-shown` e avviso «Screen Lock disabled» | ch12 §6/§10, ch24 | `session.c` |
| KDE Plasma 6.6 / KWin 6.6.7 su Ubuntu e labwc «ospite» proprio (`/usr/libexec/remotix/labwc`, labwc 0.9.3 + wlroots 0.19.2 patchato, statico, `REMOTIX_LABWC`, sidecar `org.freedesktop.ScreenSaver`) | ch12 §7 (riscrittura), ch06 §3, ch15 (nuova sezione «Our own labwc»), ch18 §3/§5, ch25 | `build/labwc-ospite/*`, `kwin.c`, `debian/copyright`, studio 6, 10 |
| Fotogramma perso di KWin: `capture_watch_sequence()`, `capture_frame_lost()`, `kwin_poke()` (`LOST_QUIET_MS` 200, `LOST_POKES_MAX` 10, `SEQ_WINDOW` 600). ATTENZIONE: documentato solo nei commenti di codice; il manuale e' la sua unica documentazione | ch06 nuova sezione «The lost frame (KWin)» | `capture.c/.h`, `child.c`, `kwin.c` |
| Chiusura sessione: `session_over_early()` (congedo prima dello stage, solo su morte certa, mai su KDE), `wt_dismiss_user_session_over()`, soccorso del logout KDE (`session_kde_logout_watch()`, `plasma-shutdown`/`isShuttingDown`, 4 s, ripetizione ogni 3 s, 10 `fail` poi 10 `replace`) | ch03 §8 (nuova sezione), ch05 §12, ch12 §4/§5, ch14 §5 | `session.c`, `child.c`, `webtransport.c` |
| Sesta strada dello 0x0E (compositore mancante: `session_missing_component()`, avviso del postinst) | ch05 §12, ch03 §3, ch14 §5, ch12 §1 | `main.c`, `session.c` |
| Niente `--session-fd`/fifo: la sessione logind si regge sul pidfd del leader (systemd 259) | ch02 §7, ch03 §4/§6/§8 (+figura EXIT), ch12 §4 | `child.c`, `session.c`, DECISIONS-11 §11.55 |
| XFCE e LXQt su Ubuntu: mappa xubuntu/lubuntu/kubuntu/ubuntu, Xubuntu con entrambi i marcatori GNOME, `xfce_panel_integrity()` (D-X3), sfondo nero E1, autostart (`blueman`, `lubuntu-update`), compositori X11 no-op (picom/compton/xcompmgr), versioni (xfce4-session 4.20.4, lxqt 2.3.0, labwc 0.9.3) | ch12 §1/§2/§8/§9/§11, ch24 | `session.c`, studio 7, 9, 13, 14, registro E1 |
| AppArmor sul kernel Ubuntu 26.04 (kernel 7.0, mediazione `unix`): righe `deny unix` con le operazioni, percorsi `xkeyboard-config-2`, include `local/`, profilo ancora in complain | ch14 §4 (riscrittura), ch02 §4, ch24 | `debian/remotix_network.apparmor`, registro C4 |
| `sentinel_shutdown_forbidden()` accetta `na`; sudo-rs / rust-coreutils; polkitd 127 | ch14 §6/§8, ch02 §9, ch01 I7 | `sentinel.c`, `sentinel.h` |
| Pacchetto: `debian/control` (Depends/Recommends/universe), `debian/rules` (`--dconf-keyfiles`, `LABWC_*`), `postinst` (compila il db dconf, avviso labwc), `postrm` (purge che pulisce case e file utente), `prerm`, `debian/remotix.install`, needrestart (`/etc/needrestart/conf.d/remotix.conf`, `override_rc`), `PATH` da `pam_env` | ch15 §1-§7 (tutte da correggere), ch14 §9/§10, ch03 §9 | `pacchetto.diff` |
| Polkit: le due regole (nessuno spegne la macchina dal desktop) | nessun file polkit nel diff `main..ubuntu-26.04`; NOTA: l'albero di lavoro ha ora modifiche non committate (non mie) a `src/remotix-no-poweroff.rules`, `src/child.c`, `docs/*`, `prove/check-desktop.py`: da guardare prima di scrivere ch13/ch14 | `git status` |
| Costruzione: archivio `remotix-<versione>-labwc-source.tar.gz`, controlli `R4 ldd-labwc`, `labwc-source`, `R23 labwc-source-riproducibile`, regole Makefile `LABWC_SOURCES`/`LABWC_PATH` | ch18 §3/§5 | `build/build-deb.sh`, `src/Makefile` |
| Banco di prova su macchine virtuali: `server/vm-radeon*.sh`, `server/live-installa.sh`, `prove/banco-vm/box.sh|fresh-vm.sh`, `RX_BANCO=vm`, `RX_TEMPO`, `all.sh --clean --only` (esce con 3), SKIP/NOTE, istantanee, porte 8841-8844, live | ch17 (nuova sezione «VM bench»), ch01 §2, ch04 §14, ch05 §14 | `prove.diff`, studio 8, 15 |
| Lezioni: B3-bis (riga rossa uguale su tutti i desktop = sospettare lo strumento; GTK 4.22), C4 (i container non provano AppArmor) | ch17 §3/§9 | registro |
| Problemi noti: E1-E4, `wireplumber` (solo VM, non bloccante), `pkexec` (riga `users-shell-and-environment`), D (KDE uscita nei primi secondi), `user@UID.service` timeout dopo Log Out (mpris-proxy), `systemd-oomd`, `gnome-remote-desktop` | ch24 (nuove sezioni «Ubuntu: what real machines showed that the boxes did not» e «Ubuntu: open points») | registro, PIANO, studio 11 |
| Glossario: «Our labwc», «Lost frame / poke», «Session life», «Runtime dconf profile», «System dconf database», «Declared fallback», «needrestart drop-in», «VM bench», «Snap», «Flutter program» | ch25 | frammento G5 |

Punti non coperti dal codice del ramo o non verificati: scelta della rotta di codifica (Vulkan/VA-API) sulla Radeon su Ubuntu; difetto libei 1.5.0 e segno della rotella con Mutter 50.1; cura C su Mutter 50 (manca il bench 06-b33 nel ramo); `ext-image-copy-capture-v1` in labwc 0.9.3; libwebkit/Chrome versioni; esito `lintian` e R23 del pacchetto `unione10`; versione di libxfce4windowing su 26.04 (4.20.5 nel box, 4.20.4 corregge E1); XFCE/LXQt sulla prova «accesso locale» (provata su Ubuntu e Kubuntu).

# PARTE 3 — Cose di Debian da TOGLIERE

Elenchi (b) dei gruppi, riassunti; i numeri di riga sono nei frammenti.
- Ogni occorrenza di «Debian 13», «trixie», `debian:trixie`, `+deb13`, `deb13`, `remotix-debian-build`, `/media/REMOTIX-DEBIAN`, `REMOTIX-DEBIAN/`, `task-<de>-desktop`, `box-identity debian 13`, porte 8811-8814 e ssh 2211-2214 (ch01, ch12, ch15, ch17, ch18, ch20, ch24).
- Versioni di Debian come fatto corrente: GNOME Shell 48.7 / Mutter 48.7, KWin 6.3.6, labwc 0.8.3, dconf 0.40, libopus 1.5.2, Mesa 25.0.7, debhelper 13.24.2, ngtcp2 1.11 / nghttp3 1.8 «portati da Debian», «32 librerie», `libei 1.3.901`.
- Unita' e meccanismi inesistenti su Ubuntu: `SESSION_UNIT_SHELL_48` e `org.gnome.Shell@wayland.service`; fifo `.ref`, `--session-fd`, CLOEXEC, «its lifeline fifo closes»; `e_path` fisso; «On Debian 13 that script (`60x11-common_xdg_path`) does not exist» e «`local_session()` returns an empty structure»; «labwc from PATH, REMOTIX ships none» / «labwc optional for KDE»; «Debian trixie packages no launcher for LXQt»; «at most `KDE_LOGOUT_TRIES` = 10».
- Frasi sulla «VM Debian 13 senza scheda video», sul profilo AppArmor `deny unix addr=@*` e sulla «nota State of the profile» (C4 le ha superate); Landlock «kernel 6.12» (Ubuntu ha 7.0).
- Risultati e tabelle del 17 nov 2026: 111/118, 112/118, 104/118, 34 controlli, `pulizia1b`, `check-package` 8/8, Samsung DeX, righe PIANO del 17 nov, «four test containers and a real Debian 13 VM», `prove/log/v100c-<de>.out`; i blocchi «What was verified» di ch08/ch09/ch10/ch11 (citano solo i giri Debian).
- La frase sul «engine» in `debian/rules` (ch04 §3, ch03 §2): non verificabile, la parola non e' in `debian/rules` ne' su `main` ne' su Ubuntu.
- Il manuale di Debian stesso: se resta nel ramo, la riga «Manual sources» (ch01 §5, ch23) conta doppio.

# PARTE 4 — Cosa serve al generatore

Stato lasciato (passi 1-2):
- Cartella creata: `manuals/sources/technical-ubuntu26.04/` (copia dei 25 `chNN_*.py`; non esiste `__pycache__`). Debian invariata.
- `build.py`: nuova voce `MANUALS["tecnico-ubuntu"]` = `dir="technical-ubuntu26.04"`, file `Technical Manual — Ubuntu 26.04.html`, title `Technical Manual — REMOTIX for Ubuntu 26.04`, h1 `Technical Manual — Ubuntu 26.04`. Altre due modifiche minime: il controllo «variabili d'ambiente non documentate» usava `"tecnico" in kinds` (ora `any(k.startswith("tecnico"))`, altrimenti non girava per il nuovo manuale); il messaggio d'errore della mappa citava un file inesistente (`appB_map.py`). Docstring aggiornata.
- Comandi: `python3 manuals/sources/build.py tecnico-ubuntu` (genera), `... --check tecnico-ubuntu` (controlla). Senza argomenti genera tutti i manuali (anche quello di Debian).

Cosa fanno gli strumenti (letto in `build.py`):
- Mappa dei file (`file_map()`, chiamata da `ch23_map.py`): prende i file tracciati da git sotto `src debian build prove boxes server` (esclusi `.wasm .png .svg .sha256 .gitignore`) piu' i sorgenti dei manuali, e FALLISCE (`SystemExit`) se manca un file nella mappa o se la mappa cita un file che non esiste. Quindi la generazione non riesce finche' ogni file nuovo non e' nella mappa: e' successo, con 15 file (`build/labwc-ospite/*`, `debian/needrestart/remotix.conf`, `debian/remotix.install`, `prove/banco-vm/*`, `server/live-installa.sh`, `server/vm-radeon*`). Ho aggiunto le 15 righe nella copia `ch23_map.py` con ruolo «TODO(Ubuntu writers)»: va scritto il ruolo vero (G5 ne propone 15). La mappa elenca anche i sorgenti di TUTTI i manuali (`HERE.rglob`): ho distinto il ruolo di `technical-ubuntu26.04` («chapter of this manual») da `technical-debian13` («chapter of the Debian 13 manual»). Se `technical-debian13` viene tolta dal ramo, la riga sparisce da sola.
- Tabella dei numeri (`numeri()`, in `ch01`): conta le righe dei file per parte secondo regole (lambda); nessun errore se i conti cambiano, ma i numeri del testo scritti a mano vanno allineati; il testo di ch01 §5 li ha in chiaro.
- `--check`: genera il manuale in una cartella temporanea e lo confronta con quello in `manuals/` (fallisce se differisce: va rigenerato dopo ogni modifica); verifica anche stile/script canonici, versione (da `build/build-deb.sh`, `RX_VERSION:-1.0.0`), `lang="en"`, frasi ancora italiane (>= 2 parole italiane fuori da code/pre/kbd; nei diagrammi SVG basta una parola), link interni, `name()` citati in `c()` che devono esistere in `src/ prove/ boxes/ build/ server/` o negli script `debian/remotix.*`, file citati che devono esistere (altrimenti usare `sysf()` o aggiungere a `SYSTEM_FILES`), ogni variabile `REMOTIX_*` letta da `getenv` documentata e viceversa, ogni codice `RX-XXX-000` esistente. NON verifica numeri, versioni, nomi di pacchetti, righe di registro: quelli restano compito degli scrittori e del revisore.
- Esito attuale: generazione OK (1 227 374 byte) dopo l'aggiunta delle righe alla mappa (prima falliva sulla mappa); `--check tecnico-ubuntu`: «manual aligned with the code» (con il testo ancora di Debian: il controllo non vede le falsita' semantiche, vede solo l'esistenza). `--check utente`: allineato. `--check tecnico` (Debian) fallisce, ed e' un fallimento che c'era GIA' prima: la sua mappa non elenca i 9 file nuovi del ramo (fuori dallo scopo toccarla). Nota: `ch12_desktops.py` di Debian e' stato modificato nel commit del ramo (19 righe).
- Cosa andra' aggiornato perche' `--check` passi sul testo definitivo: (1) `ch23_map.py`: i ruoli dei 15 file (e eventuali file nuovi); (2) variabili `REMOTIX_*` nuove nel codice (`REMOTIX_LABWC` ecc.) documentate in ch02/ch15/ch18 («Environment variables read by the product», ch16/ch18; controllare con grep); (3) funzioni nuove citate con `()` esistenti in `src/`; (4) nessuna frase italiana fuori da `c()`/`sysf()` (nomi dei file `vm-radeon-*`, variabili `RX_BANCO`, `unione10`, ecc. vanno in `c()`); (5) i file di sistema (`/etc/dconf/db/remotix`, `org.gnome.Shell@ubuntu.service`, `/etc/needrestart/conf.d/remotix.conf`) in `sysf()`; (6) rigenerare il file HTML in `manuals/` a ogni modifica; (7) versione in copertina: viene da `build-deb.sh`, 1.0.0, nessuna modifica.
- Da decidere: se il manuale di Debian resta in questo ramo (la mappa e `--check tecnico` ne risentono) — PIANO consiglia di toglierlo da qui.

# PARTE 5 — Suddivisione del lavoro di scrittura

Cinque gruppi di file disgiunti (nessuna sovrapposizione di file; i `rif()` collegano per titolo di sezione):

| Gruppo | Capitoli | Peso (sezioni da correggere/riscrivere) | Fonti da leggere (oltre al capitolo) |
|---|---|---|---|
| A | ch01-ch05 (introduzione, architettura, ciclo di vita, trasporto, RCP) | 21 + 3; molta riscrittura in ch02 §7, ch03 §4/§6/§8 | `session.c`, `main.c`, `child.c`, `webtransport.c`, `rcp.c`; `DECISIONS-11` §11.55; registro C4/C5/E3; studi 1, 2, 5; frammento G1 |
| B | ch06-ch11 (cattura, codifica, qualita', pagina, input, audio/appunti) | 24 + 2; nuova sezione «The lost frame (KWin)», ch06 §3 labwc proprio | `capture.c/.h`, `kwin.c`, `mutter.c`, `input.c`, `child.c`; `build/labwc-ospite/README`; studi 4, 6, 10, 11; frammento G2 |
| C | ch12-ch14 (desktop, login, sicurezza) | 13 + 3, ma sezioni lunghe e centrali (ch12 §6, §7, ch14 §4) | `session.c`, `kwin.c`, `mutter.c`, `sentinel.c`, `debian/remotix_network.apparmor`, `src/remotix.pam`; registro C4, C5, D, E1-E4; studi 1, 2, 3, 5, 6, 7, 9, 12-14; frammento G3 |
| D | ch15-ch18 (pacchetto, log, test, costruzione) | 23 + 4; nuova sezione banco VM, labwc nel pacchetto | `pacchetto.diff` (`debian/`, `build/`), `prove.diff`, `server/vm-radeon*`, `prove/all.sh`; studi 8, 11, 15; frammento G4 |
| E | ch19-ch25 (prestazioni, estendere, convenzioni, appendici A-C, glossario) | 24 + 6; ch24 raccoglie la storia dei problemi | `docs/REGISTRO-problemi.md`, `src/*.h`, `session.h`; la mappa dei 15 file nuovi; frammento G5 |

Ordine e dipendenze:
- Tutti i gruppi possono partire insieme. Ultimi da chiudere: ch23 (mappa, dipende dai file), ch01 §5 (tabella dei numeri), ch24 (riassume cio' che A-D hanno scritto: riferisce le sezioni «Ubuntu: …» che devono esistere) e ch25 (glossario: termini introdotti da A-D). Meglio far chiudere E per ultimo, dopo A-D.
- Regola per non rompere i `rif()`: NON rinominare le sezioni esistenti; i titoli nuovi si concordano prima. Titoli proposti: «The lost frame (KWin)» (ch06), «Our own labwc (KDE)» (ch15), «When the session ends before the stage is gone» (ch03), «The VM bench» (ch17), «Ubuntu: what real machines showed that the boxes did not» e «Ubuntu: open points» (ch24). I rif() esterni da altri gruppi verso questi titoli si scrivono solo a lavoro chiuso o con questi titoli esatti. Titoli citati da piu' gruppi (da non cambiare): «The four desktops», «Security model», «Login and its defences», «The local-login hold», «Startup and life cycle», «The package», «Testing», «Logging and diagnostics», «Appendix C — Known issues and open points», «Overall architecture», «The RCP/1 protocol», «Screen capture», «Input», «Audio and clipboard», «Extending REMOTIX and porting to another distribution».
- Dipendenze di contenuto: il modello dconf (C) e' citato da A (ch02/ch03), B (ch10) e D (ch15 file/postinst); la chiusura sessione (A ch03 §8) e' citata da C e dal protocollo (ch05 §12); il labwc proprio e' descritto in D (ch15/ch18), citato da B e C.

Convenzioni di stile (dettaglio nel frammento G5, ch21, e in `build.py`):
- Inglese tecnico asciutto, impersonale, niente «we», frasi corte; nessuna frase italiana fuori da `c()`, `sysf()`, `<pre>`, `<kbd>`; i nomi italiani reali (file, variabili, `unione10`, `labwc-ospite`) sempre in `c()`, e il senso tradotto nel testo («guest labwc», «round»).
- Ogni affermazione con la fonte (file, funzione, `docs/...` §, registro C4/C5/D/E); distinguere [misurato su Ubuntu] / [dal sorgente] / [storico Debian]; dove non verificato: «not verified» / «not measured». Data nel formato «19 Nov 2026».
- Struttura: `CHAPTER = (titolo, [(titolo sezione, html)…])`; primo paragrafo `p(..., lead=True)`; `table(head, rows, "«TAB» — …")`, figure `fig`/`flow`/`seq` con didascalia «FIG» (la numerazione la mettono i segnaposto); note con titolo breve: `note(testo, "Title.")`, `warn`, `tip`; `term("""$ …""")` per comandi, `code(testo, lang, titolo)` per esempi; `c()` per identificatori del repo, `sysf()` per file e unita' della macchina; `rif("Titolo esatto")` per rimandi.
- Il codice vince sui commenti: contrasti fra codice, commenti e documenti vanno in ch24 (tabella `CONTRA`).
- Non copiare i marchi dei commenti (stella, divieto, ecc.) e niente emoji.
- Generare e controllare dopo ogni capitolo: `python3 manuals/sources/build.py tecnico-ubuntu` e `--check tecnico-ubuntu` (sul server se lento; sul tablet dura meno di un secondo ma non compilare nulla). Un solo gruppo alla volta rigenera il file HTML in `manuals/` (e' un solo file): conviene far rigenerare solo al coordinatore, o accettare che il `--check` di confronto con l'HTML pubblicato fallisca finche' non si rigenera alla fine.
