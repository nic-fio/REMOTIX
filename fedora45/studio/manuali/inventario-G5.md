# Inventario G5 — manuale tecnico Fedora 45, capitoli ch19–ch25

Data: 25 nov 2026. Sola lettura. Base: i capitoli di `ubuntu26.04/manuals/sources/technical-ubuntu26.04/ch19..ch25` (gia' riscritti per Ubuntu, 1669 righe), confrontati con `fedora45/` (`diff -rq ubuntu26.04/src fedora45/src`, `PIANO.md` fino al 25 nov, registro F1–F36, `rpm/`, `selinux/`, `build/build-rpm.sh`, `prove/`, `server/`).
Fonti citate come `file:riga` o «F<n>» (registro `docs/REGISTRO-problemi.md`) o «D<n>» (decisioni di `PIANO.md`). Dove non ho potuto verificare c'e' scritto «non verificato». Nessuna cifra del manuale e' copiata: dove il manuale conta dal codice c'e' «da ricontare» + comando.

## Tabella riassuntiva

| Capitolo | Sezioni | Vale com'e' | Da correggere | Da riscrivere | Da togliere |
|---|---|---|---|---|---|
| ch19 performance | 7 | 0 | 3 | 4 | 0 |
| ch20 extending | 9 | 1 | 5 | 3 | 0 |
| ch21 conventions | 7 | 1 | 5 | 1 | 0 |
| ch22 structures | 6 | 6 | 0 | 0 | 0 |
| ch23 map | 1 | 0 | 0 | 1 | 0 |
| ch24 problems | 11 | 0 | 5 | 5 | 1 |
| ch25 glossary | 1 | 0 | 1 | 0 | 0 |
| **Totale** | **42** | **8** | **19** | **14** | **1** |

## Fatti di base (valgono per tutti i capitoli; non ripetuti sotto)

- Diff `src/` Ubuntu → Fedora: differiscono SOLO `child.c`, `input.c`, `kdehost.h`, `kwin.c`, `kwin.h`, `main.c`, `Makefile`, `remotix.pam`, `remotix-remote-sessions.rules`, `session.c`, `transport.c`, `walls.c`; nuovi `remotix-pam-hook`, `protocols/kde-output-device-v2.xml`, `protocols/kde-output-management-v2.xml`, `protocols/README-kde-output.txt`. IDENTICI (diff vuoto, controllato): `rcp.c`, `rcp.h`, `budget.h`, `mutter.h`, `capture.c`, `rootside*.{c,h}`, `child.h`, `session.h`, `helper.*`, `command.*`, `page.html`, `webtransport.c`, `msgrate.h`, `local_login.c`, `encoder.c`, `log.*`. Quindi costanti di protocollo/limite e strutture dei ch19-ch22 non cambiano. Ricontrollo: `diff -rq ubuntu26.04/src fedora45/src | grep -v pycache`.
- Cambiamenti del codice che toccano i miei capitoli: KDE = KWin da solo (`--kwin-virtual`, `kwin_virtual_alive()` `kwin.c`, `kwin_output_resize()`, `kde_output_management_v2`; niente labwc ospite: F7, D2); SELinux (`child.c:1144-1147` uscite 44/45/46/47, `selinux_exec_like_local_login()`, `walls.c:260-348` `remotix_net_t`, `session.c` compilazione dconf in `/run/remotix/dconf-compile.tmp`: F24/F25/F32/F33); lingua e PATH (`child.c` `child_locale_read()`, `LC_*`/`LANGUAGE`: F34/F35); primo movimento puntatore GNOME (`input.c`, F34); chiusura forzata KDE (`session.c` `exit_kde(TRUE)` → `graphical-session.target`, `KDE_PRELOCAL_ORDERLY_MS 5000` a `session.c:113`: F36); `transport.c` `close_why()` (F23/F31).
- Pacchetto: `rpm/remotix.spec` (Version 1.2.0, `ExclusiveArch: x86_64 aarch64`), `%pre` rifiuta senza render node (spec:168-), `%post` modulo SELinux + sysusers + tmpfiles + compilazione dconf + `remotix-pam-hook apply` + `--encoding-test h264` + `%firewalld_reload` (spec:217-279); trigger su gdm, lightdm, sddm, plasma-login-manager (spec:433-463); file di servizio in `rpm/`: `remotix.service`, `remotix.sysusers`, `remotix.tmpfiles`, `remotix.conf`, `remotix.firewalld.xml`, `denied-users`, `needrestart.conf`, `remotix-no-suspend.conf`, `org.kde.remotix.desktop`. Nessun `debian/`, nessun `boxes/`, nessun `build/labwc-ospite/`, nessun AppArmor.
- Banco: solo VM con la Radeon passata (`server/vm-radeon.sh`, `prepara-server.sh`, `live-installa.sh`), ssh 2351-2354, REMOTIX 8851-8854 (`prove/lib.py:40`), cartella server `/media/REMOTIX-FEDORA`, VM `costruzione` per il pacchetto (`build/build-rpm.sh`), niente contenitori.
- Registro: le voci A–E di `docs/REGISTRO-problemi.md` in `fedora45/` sono EREDITATE da Ubuntu (non provate su Fedora); quelle di Fedora sono F1–F36 (r.366 in poi).
- I log dei giri Fedora stanno sul server (`prove-sel/log-final/`, `/media/REMOTIX-FEDORA/pacchetti/*`) e sul tablet (`~/remotix-prove-live/…`), non nell'albero: nessuna cifra misurata (fps, ms, latenze) e' leggibile dall'albero Fedora, salvo quelle scritte nel registro/PIANO (citate sotto).
- `fedora45/` non e' ancora in git (`git status`: `?? fedora45/`): `build.py` di Fedora usa `git ls-files --cached --others --exclude-standard src rpm selinux build prove server` (`manuals/sources/build.py:351`), quindi conta anche i file non tracciati.

---

# ch19_performance — «Performance and capacity» (7 sezioni)

### 19.1 «How to read the numbers of this chapter» — DA CORREGGERE
- L'impianto (tre sorta di numeri: misurato / registrato / codificato) vale. Cambiano i riferimenti: «round of 19 November 2026», `vm-gnome-unione10`, «package unione10», «Kubuntu, Xubuntu, Lubuntu», «measured on Debian 13 only» → giro Fedora: pacchetti `h1` (GNOME, XFCE, LXQt) e `i2` (KDE, candidato 1.2.0) in enforcing, log in `prove-sel/log-final/h1/` sul server (F35, `PIANO.md` 23-25 nov). Non verificato: se qualcuno di quei log contenga le cifre di `check-media` (fps, sync audio): non nell'albero.
- Dichiarare cosa e' stato provato per desktop: GNOME 52 PASS (+1 FAIL pkexec) + `all.sh` 39 PASS; KDE 76 PASS; XFCE 60; LXQt 60 (F35). Tutti e quattro provati a mano dal proprietario (23 nov) e da chiavetta live (25 nov).
- `rif("Testing")`, `rif("Where no measurement exists")`: restano validi se i titoli non cambiano.

### 19.2 «The test machine and the conditions of the measurements» — DA RISCRIVERE
- Macchina: VM QEMU/KVM con UEFI, Fedora 45 installata dal contenuto della ISO Live, SELinux enforcing, firewall di serie, `CPUS=4 MEM=5G DISKSZ=40G` (`server/vm-radeon.sh:30`; la VM di build `costruzione` 8 CPU, 6G, `vm-radeon.sh:41`); una sola Radeon (vfio), una VM alla volta; slot `vm-radeon.sh` per ISO «Fedora-*-Live-45-1.4». Stesse parole «Radeon passed through» valgono; il modello della scheda: non verificato.
- Interruttori del banco: `RX_BANCO=vm`, `RX_TEMPO`: `prove/lib.py:37-40` (porte 8851-8854); `RX_TEMPO=2` di default su Fedora: non verificato (`grep -n RX_TEMPO prove/*.sh prove/lib.py`).
- Client: versioni di Chrome/Firefox del banco Fedora: non verificato (il testo cita Chrome 156.0.8078.79, Firefox 153.7.0 di Ubuntu). Chromium nella VM kde: installato a mano (F33 punto 1).
- Codec: su Fedora H.264 richiede RPM Fusion (`mesa-va-drivers-freeworld`, D1; macchine di prova da istantanea `codec`); percorso video: `--encoding-test h264` hardware via `h264_vulkan` sulla Radeon (F35, macchine di consegna); sulla macchina vera da chiavetta: codifica riuscita anche sulla Intel (`PIANO.md` 25 nov). HEVC nel browser: non verificato su Fedora.
- Eliminare il «Debian vs Ubuntu» (container bench). Aggiungere: SELinux enforcing, nessun `permissive`, `dontaudit` di serie (F33), tempo di accensione/spegnimento VM e' proprieta' del banco.

### 19.3 «Picture, frame rate and sound measured on 19 November 2026» — DA RISCRIVERE
- Tutta la tabella (160/160, 33 ms, 60.0 fps, sync 294 ms, 2 sessioni a 60 fps, nitidezza 1.00…) e' di Ubuntu: NON copiabile. Per Fedora: non verificato (nessun log di `check-media` nell'albero; chiedere/leggere `prove-sel/log-final/h1/` sul server oppure dichiarare «non misurato»).
- Da togliere il punto «Debian 13 only» (39 vs 60 fps dei container Debian) e i riferimenti a Kubuntu/`docs/STORIA-ubuntu-26.04.md`.
- Costanti citate nei punti che restano vere: `AUDIO_BUFFER_MS = 250` (`page.html` identico, da ricontare: `grep -n "AUDIO_BUFFER_MS" src/page.html`), `--budget-mpixel-s 0.0 --session-cap 10 --reserve 0.50` (`rcp.h`, `budget.h` identici).
- Sottosezione «KDE: the lost frame»: `capture_watch_sequence()`/`capture_frame_lost()`/`LOST_QUIET_MS 200`/`LOST_POKES_MAX 10`/`SEQ_WINDOW 600` sono in `capture.c` (identico); `kwin_poke()` esiste in `kwin.c:595` (modalita' KWin da solo). I numeri citati nei commenti (18-26 s, 68 poke) sono stati misurati su Kubuntu con KWin 6.6 dentro il labwc nostro: con KWin 6.8 `--virtual` non e' misurato, quindi riscrivere come «limite di codice, non misurato su Fedora». Non verificato se la sorgente di buffer di KWin 6.8 perde ancora frame.

### 19.4 «Session and login timings measured on 19 November 2026» — DA RISCRIVERE
- La tabella (2.65 s rifiuto, 29 s/90 s orologi, 11 s network-drop, 6 s due utenti) e' di Ubuntu/GNOME: per Fedora non verificato. `REJECT_FLOOR = 2500` e' identico (`rcp.c`) ma la cifra misurata no.
- Tempi Fedora documentati (da citare con la fonte): chiusura ordinata del remoto con gancio locale: GNOME 1-2 s (F6), XFCE 1,7 s e LXQt 0,7 s da chiavetta (`PIANO.md` 25 nov), KDE: senza programmi 2,9 s; con Konsole+top+kwrite non salvato forzata a 5,03 s (i2), tutto fermo 0,54-0,56 s dopo, gancio liberato a 5,9 s; con i1 forzata a 10,05 s e gancio a 10,9 s (F36).
- Punto «session_over_early()» (`child.c:10130`, «mai su KDE» `child.c:12085`): vale. Punto RealtimeKit 25 s: era artefatto dei contenitori (B2): non verificato su Fedora, da togliere dal testo.
- Paragrafo «Local login on KDE (hand test)»: riscrivere con F36 e i 5 s di `KDE_PRELOCAL_ORDERLY_MS` (`session.c:113`, applicato in `session.c:5639` solo se `force_guard_on`); compromesso dichiarato: una chiusura sana fra 5 e 10 s viene troncata (`PIANO.md` 25 nov).
- «Restart del servizio chiude i desktop» (§11.56): vale; cfr. contraddizione nel commento di `rpm/remotix.spec:220` (vedi ch24 §11).

### 19.5 «Capacity: the recorded measurements and what they do not cover» — DA CORREGGERE
- Vale: campagna registrata di agosto 2026 (`docs/DECISIONS.md` §4.6-septies r.2583, §4.6-nonies r.2654 esistono in `fedora45/docs/`), `BUDGET_STRAIN_DELAY_MS` (`budget.h` identico), `RCP_SESSION_CAP = 10`. Il testo dice «not repeated on Ubuntu 26.04»: sostituire con «non ripetuta su Fedora 45».
- Cambia «Measured on Ubuntu: the most users tried at once»: su Fedora `two-users`/`three-users` e `tap-click-portrait` erano FAIL nel giro f1 e sono PASS dopo la cura del primo movimento (F34, g6: `two-users`, `three-users`, `same-user`, tutto `check-phone` PASS); `all.sh` GNOME con h1: 39 PASS (F35). `session-cap` con tetto 2: non verificato su Fedora. Altri tre desktop: «Base+input 31/0» (F34), `check-multiuser` non su KDE/XFCE/LXQt: non verificato.

### 19.6 «Limits fixed in the code» — DA CORREGGERE
- Le 12 prime righe valgono (costanti in `rcp.h`, `budget.h`, `rootside.c`, `child.c`; tutti identici a Ubuntu). Verifica fatta: `child.c:170` `FRAME_MAX 16 MiB`, `child.c:220` `CLOSING_GRACE_MS 30000`, `child.c:5578` `MOTION_FPS 60`.
- Frase finale «same as on Debian 13 (diff of rcp.h and budget.h…)» → «same as Ubuntu 26.04: diff vuoto».
- Righe «Added or relevant on Ubuntu»: `WAIT_CALL_MS`/`mutter_scale_to_one()` valide (`mutter.c`/`mutter.h` identici; GNOME 51 invece di 50: non riprovato); attesa RealtimeKit 25 s: contenitori, togliere o marcare «non verificato su Fedora»; lost-frame: vedi 19.3.
- Aggiungere righe NUOVE Fedora: `KDE_PRELOCAL_ORDERLY_MS` 5000 (`session.c:113`) contro `WAIT_EXIT_MS` 10000 (`session.c:108`); scadenza lato root `PL_GRACE_MS` 13000, `PL_CEIL_MS` 20000, `PL_HOLD_MS` 10000 (`rootside.c:2428-2432`); `KDEHOST_SWEEP_MS` 45000 (`rootside.c:1676`). Da ricontare con `grep -n "define PL_\|define KDE_PRELOCAL\|define WAIT_EXIT_MS" src/*.c`.
- Limiti dichiarati (8 utenti, 3K) invariati: `docs/DECISIONS-11.md` §11.51 (presente in fedora45/docs).

### 19.7 «Where no measurement exists» — DA RISCRIVERE
- Righe da rifare per Fedora: «timings on Kubuntu/Xubuntu/Lubuntu» → su Fedora tutti e quattro i desktop hanno giri in enforcing ma senza cifre di prestazione nell'albero; «a card by vendor and model»: la Radeon (VM e, sulla macchina vera, Intel + Radeon da chiavetta); NVIDIA: nessuna prova; «Intel with GNOME»: solo `--encoding-test` riuscito sulla Intel il 25 nov, suite funzionale non eseguita sulla Intel (non verificato); «after the bench entered as root»: togliere (fatto Ubuntu); «duration of all.sh» (47 min Ubuntu): non verificato su Fedora; «4096x2304 canvas-limits»: non verificato su Fedora.
- Sottosezione E4 (stutter Chrome su Android, VM Ubuntu): e' dell'Ubuntu e non e' stata riprodotta su Fedora (proprietario da Android su GNOME il 21 nov: «video 1440p fluidissimo», `PIANO.md`): togliere la tabella o dichiararla «solo Ubuntu, non osservato su Fedora». `rif("Ubuntu: open points")` si rompe se si rinomina ch24 §10.
- Altre note: CPU/memoria per sessione: non verificato (come Ubuntu).

---

# ch20_extending — «Extending REMOTIX and porting to another distribution» (9 sezioni)

### 20.1 «The one-distribution rule» — DA CORREGGERE
- «exists twice … Debian 13 and Ubuntu 26.04» → tre alberi (`debian13/`, `ubuntu26.04/`, `fedora45/`), Fedora e' il terzo porting; `fedora45/CLAUDE.md` (19 righe) dice «Fedora 45 only … no distro detection … never touch ../debian13 ../ubuntu26.04». Versione 1.2.0 (spec:24). I 4 desktop: GNOME 51 (gdm), Plasma 6.8 (plasmalogin), XFCE 4.20 (lightdm), LXQt 2.4 (sddm) (`PIANO.md` riscontro, r.62).
- «about fifty source files» differenza Debian→Ubuntu: per Fedora da ricontare: `diff -rq ubuntu26.04/src fedora45/src | wc -l` (12 file differenti + 4 nuovi, ma solo in `src/`).
- Il warn «Removed code comes back» e' vero ancora, anzi: il codice SELinux (rimosso su Debian) e' tornato (vedi 20.3).
- Note «Where the history is»: `docs/INVENTARIO-non-debian.md` e `docs/PULIZIA-tranche1.md` sono ancora in `fedora45/docs/` (descrivono l'albero Debian).

### 20.2 «Where the code depends on the distribution» — DA RISCRIVERE
Tabella a due colonne (Debian/Ubuntu): va riscritta con la colonna Fedora; righe, in ordine:
- formato pacchetto: `.rpm` da `rpm/remotix.spec` (macro `%selinux_*`, `%systemd_*`, `%firewalld_reload`), scriptlet `%pre`/`%post`/`%preun`/`%postun`/trigger (spec:168-463); sysusers non automatico (`%global __sysusers_path ^$`, spec:17-20) e `systemd-sysusers remotix.conf` nello `%post` (spec:230); niente `deb-systemd-invoke`, `dh_*`, `needrestart` come Build; `rpm/needrestart.conf` → `/etc/needrestart/conf.d/remotix.conf` (spec:165-166, «se mai installato»).
- nomi delle dipendenze: Requires `pam gawk systemd-pam shadow-utils systemd dbus-broker pipewire wireplumber`; Recommends `labwc dconf wlr-randr xorg-x11-server-Xwayland dejavu-sans-fonts` (spec:70-94); BuildRequires `openssl-devel pam-devel libselinux-devel glib2-devel>=2.80 pipewire-devel libdrm-devel libva-devel opus-devel libei-devel>=1.3.901 libxkbcommon-devel mesa-libgbm-devel wayland-devel vulkan-headers vulkan-loader-devel systemd-rpm-macros firewalld-filesystem …` (spec:44-65,101). Nessun Recommends `va-driver-all`: i codec sono requisito dell'amministratore (RPM Fusion `mesa-va-drivers-freeworld`, D1, spec:description). OpenSSL di Fedora 4.0 (D8; `build-rpm.sh` header: nessun ripiego su openssl3).
- immagine di build: nessun container; VM `costruzione` + `build/build-rpm.sh`; librerie QUIC statiche `ngtcp2 1.25.0`/`nghttp3 1.18.0` da `build/quic-static.sh` (Provides `bundled(...)`, spec:95-98); controlli R13/R4 in `build-rpm.sh`. R23 (riproducibilita') e lintian: non presenti in `build-rpm.sh` (non verificato).
- nome/archivi: `remotix-1.2.0-1.fc45.x86_64.rpm`; nessun archivio sorgente di labwc (non lo include).
- percorsi: `/usr/libexec/remotix/remotix`, `/usr/lib/firewalld/services/remotix.xml` (spec:151), `/etc/remotix/denied-users`, `/usr/share/remotix/belts/` (cinghie spente, spec:159-162), `/usr/share/selinux/packages/remotix.pp.bz2`.
- servizio: installato spento (preset Fedora `disable *`, spec:218); `ExecStartPre=-…remotix-pam-hook check` (`rpm/remotix.service:42`), `Environment=MESA_SHADER_CACHE_DISABLE=true` (:39), `Restart=on-failure RestartSec=2 RestartPreventExitStatus=78`.
- PAM: file = `/etc/pam.d/sshd` di Fedora riga per riga + esclusione di root (`src/remotix.pam`): `auth substack password-auth`, `include postlogin`, `pam_sepermit`, `pam_selinux close/open env_params`, `pam_namespace`, DUE `pam_env` con `/etc/locale.conf`; authselect riscrive `system-auth/password-auth`: per questo l'aggancio «il locale chiude il remoto» NON va in `common-session` ma nei file delle schermate (`src/remotix-pam-hook`, `DEFAULT_DMS="gdm plasmalogin lightdm sddm"`, hook:51; F6, F9, F18, F19, F21).
- PATH: Fedora non ha `/etc/environment`; ripiego del figlio `~/.local/bin:~/bin:/usr/local/bin:/usr/bin` (F34). Lingua: dall'utente (AccountsService) o sistema, `LC_*`/`LANGUAGE` passati (F35).
- amministratore: regola polkit con `sudo`/`wheel`/`admin`: su Fedora vale `wheel` (D8 del banco: utente `prova` wheel). Azioni logind vietate: la regola e' identica a Ubuntu (23 occorrenze `org.freedesktop` in `src/remotix-no-poweroff.rules`; 19 azioni da ricontare: `grep -c '"org.freedesktop.login1' src/remotix-no-poweroff.rules`); la check `power-implied` PASS su XFCE (F33 punto 4) con systemd 262; su GNOME/KDE/LXQt: non verificato. Regola `remotix-remote-sessions.rules` ha UNA azione in piu': `org.freedesktop.fwupd.refresh-remote` (F3).
- accesso: la regola «nessuno spegne» deve ordinare prima di `lightdm.rules` (provato F33 p.4).
- MAC: SELinux enforcing con il modulo del pacchetto: `selinux/remotix.te` (381 righe, da ricontare), tipi `remotix_t`, `remotix_net_t`, `remotix_hook_t`, `remotix_exec_t`, `remotix_dconf_db_t`, `remotix_prelocal_t`; `walls.c:260-348` scrive `/proc/thread-self/attr/exec` per `remotix_net_t`; protezione spenta = nota e si prosegue, caricata-e-negata = la parte di rete non parte (F24, uguale all'AppArmor). Niente piu' «SELinux still absent».
- firewall: servizio firewalld `remotix` (7447 tcp+udp), definito mai aperto (D5, F17, F20): `sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload`.
- prima connessione (render group): `child.c`/`render_grant.c` identici; gruppo `render` su Fedora: non verificato.
- «which desktop is installed»: marcatori e `desktop_of_session_name()` identici; sessioni Fedora (`plasma`, `xfce`, `LXQt`, `gnome`): non verificato in dettaglio (`session.c:405` accetta `plasma`/`kde`/`kubuntu`). Lettori del display manager: `session.c:308,412` conoscono lightdm, sddm, `gdm3`; il DM di Fedora e' `gdm` e `plasmalogin`: non verificato come vengono trattati (lightdm e sddm: usati per XFCE e LXQt).
- unita' sessione GNOME: GNOME 51: stessa forma di GNOME 50 (`PIANO.md` r.66); non verificato oltre.
- compositor XFCE/LXQt: labwc 0.20.2 di Fedora (era 0.9.3); `rc.xml` invariato; `wlr-randr 0.5.0`; avviso lxqt-panel con wlroots < 0.20.2 (F33 p.8).
- compositor KDE: KWin 6.8.3 da solo `--virtual`, nessun labwc nostro (D2, F7); marchio «KWin di REMOTIX»: `--kwin-virtual` + `REMOTIX_KDE_HOST=1` (`kdehost.h`); rifiuto pulito se manca `kde_output_management_v2` ≥ 22 (F7); KWin ricorda `Virtual-0` in `~/.config/kwinoutputconfig.json` (F8).
- componente mancante: `session_missing_component()` nomina `labwc` per XFCE/LXQt (`session.c`, immutato): `%post` avvisa se manca (spec:262-270).
- impostazioni di programmi che leggono dconf da soli: nessun snap/Flutter su Fedora; Flatpak parte senza nulla di speciale (`PIANO.md` r.67; non provato dal proprietario). Modello dconf: stesso, ma compilato dallo `%post`/dal servizio in `/run/remotix/dconf-compile.tmp` con nomi fissi (F24, `session.c`).
- banco: nessun `boxes/`, nessun `rxu-<de>`; 4 VM + VM di build; porte 8851-8854; `prove/banco-vm/box.sh`, `fresh-vm.sh`, `autologin-lightdm.sh`, `autologin-sddm.sh`; `server/prepara-server.sh` usa `/media/REMOTIX-FEDORA`.
- Per ogni riga la colonna «Where» deve citare `rpm/…` invece di `debian/…`. Colonna Debian: potrebbe restare «Debian 13» o sparire (decidere).

### 20.3 «What the clean-up removed, kept and risked» — DA RISCRIVERE
- Tabella «removed on Debian / on the Ubuntu tree»: aggiungere la colonna Fedora. Righe che cambiano: «SELinux handling in child.c and walls.c» → TORNATO per Fedora (`child.c:1144-1147`, `selinux_exec_like_local_login()`, `selinux_exec_checked()`; `walls.c:260-348`), con `-lselinux` nel Makefile e `libselinux-devel` (spec:49); «own-labwc build switch / LABWC=» → morto: `REMOTIX_LABWC` resta come stringa nel Makefile (`Makefile:132-133`) e il codice labwc-per-KDE di `kwin.c`/`kwin.h`/`child.c`/`main.c` e' irraggiungibile (F7, da togliere dopo le prove: `studio/5-kde-progetto.md` §8); «Ubuntu session names», «GNOME 50 template branch», «D-153 folder discovery»: restano vivi (codice identico).
- «Risks recorded by tranche 1»: «SELinux handling absent on either tree» → falso su Fedora; «apt remove … net/»: non verificato su `dnf remove` (`%postun` spec:380-430 rimuove `/etc/dconf/db/remotix`, file nelle home, `*.rpmsave`).
- Elenco «What stays and why»: «The pam_selinux lines of remotix.pam … mirror sshd» ora e' funzionale (F2). `--no-split`/`TWIN`: il spec passa `TWIN=none` (spec:117-133).

### 20.4 «Porting from Debian to Ubuntu: what changed in practice» — DA RISCRIVERE
- Il titolo e il contenuto sono Ubuntu (GNOME 50, AppArmor C4, dconf C5, polkit C6, needrestart). Riscrivere come «Porting to Fedora: what changed in practice» (le righe Ubuntu si possono riassumere in una riga). Tabella «Subject / What changed / Register», righe da citare con la voce: GNOME 51 e dconf (F34/F35); KDE KWin da solo (F7, F8, F13, F14); SELinux al posto di AppArmor (F2, F5/F25, F10/F26, F24, F27, F28-F33); aggancio «locale chiude remoto» sulle quattro schermate (F6, F9, F18, F19, F21, F36); firewalld (F17, F20); pacchetto RPM (F1, F21, F24); lingua/PATH (F4, F34, F35); XFCE sfondo (F22, D7); portachiavi (D6, `remotix.pam`: nessun `pam_gnome_keyring/oo7/kwallet`).
- «Lessons of the second port» → lezioni del terzo, con fonti: (1) provare su macchina vera/chiavetta: KDE passava in VM e falliva dal vero (F36: la prova automatica apriva un desktop vuoto); (2) prima di accendere una schermata di accesso provarla: la riga PAM deve stare PRIMA della prima riga `session` (F6, `pam_selinux open` consuma l'exec); (3) `.xml` di firewalld non valido (F17); (4) l'orologio del client (notBefore = adesso − 3600 s `certificates.c:143`, F23); (5) una cura nata su Fedora che vale per tutti non si applica senza piano (nota `PIANO.md` 23 nov, lingua/primo clic); (6) una regola SELinux si prova in enforcing, non in `permissive -DB` (F28).
- Il warning E «A class of programs» (Flutter/snap) → su Fedora non applicabile; sostituire con Flatpak (non provato).

### 20.5 «A checklist for porting to another distribution» — DA CORREGGERE
Passi generici validi (copia, minimi librerie, pacchetto, PAM, polkit, DM, MAC, compositor, banco, check-package, manuale). Correggere:
- passo 2: `MINIMI` del Makefile (immutato) + OpenSSL 4.0 di Fedora (D8). Passo 3: guardie `R13`/`R24` ora in `rpm/remotix.spec:%build` e `build-rpm.sh` (R4/R13), non `debian/rules`/`build-deb.sh`.
- passo 4 (PAM): su Fedora authselect (F6): mai toccare i link; nuovo passo «aggancio sulle schermate» con `remotix-pam-hook`.
- passo 5 (polkit): il «19 azioni derivata di nuovo» ha una riga Fedora (nessuna prova di `power-implied` oltre XFCE: non verificato altrove); nota sul 19-azioni di debian13/ da riverificare (testo cita il pacchetto Debian «not yet published»: stantio).
- passo 7 (MAC): SELinux = modulo del pacchetto, prova negativa (`prove/wall-selinux.sh`, `wall-neg-domain.py`, `wall-sesearch.sh`), `ausearch` poco affidabile sulle VM (usare `journalctl -b -g avc:`, F24). Il manuale dice «enforce mode not proven»: su Fedora SELinux e' SEMPRE enforcing.
- passo «bench»: VM, non container; «tre domande sul mondo vero» di F36 (programmi aperti nel remoto; `systemctl --user show -p PartOf`; etichetta SELinux dei file di unita' da fermare).

### 20.6 «Adding a message to RCP/1» — VALE COM'E'
- `rcp.c`, `rcp.h`, `msgrate.h`, `webtransport.c` (`wt_dismiss_user_session_over`), `page.html` identici a Ubuntu (diff vuoto): tutti i nomi (`measure_fields()`, `control_class()`, `lww_index()`, `T_TERMINATE_SESSION = 0x0011`) restano. Ricontrollo a campione: `grep -n "measure_fields\|rcp_admitted_waiting" src/rcp.c`.
- `rif("Build and release")`, `rif("The RCP/1 protocol")`: titoli di altri gruppi.

### 20.7 «Adding a desktop» — DA CORREGGERE
- «KDE uses KWin nested in our own labwc» (passo 1) → KWin da solo con `--kwin-virtual` (`session.c` riga `ExecStart=… --kwin-virtual %u %u -- %s --virtual --xwayland …`; `kwin_output_resize()`); XFCE e LXQt: labwc di Fedora.
- passo 6 (packaging): `Recommends` in `rpm/remotix.spec`; `session_missing_component()` + avviso nello `%post` (spec:262-270); nuovo: trigger RPM del display manager e voce in `DEFAULT_DMS` di `remotix-pam-hook` (il desktop nuovo ha una sua schermata di accesso da provare: F6) + regole SELinux per le unita' da fermare (F36: `allow remotix_t xdm_unit_file_t:service { stop status }`, `selinux/remotix.te`).
- passi 7-8 (banco/test): `PORTS` in `lib.py:40` = 8851-8854; niente `boxes/Containerfile`/`box.sh` dei contenitori; VM in `server/vm-radeon.sh`; `prove/banco-vm/box.sh`; dizionari `PANEL`, `LOGOUT` (`deskkit.py`), `SHELL_UP`, `TERMINAL`/`FILEMGR` (`check-desktop.py`): terminale GNOME su Fedora non verificato (il testo dice `ptyxis` per Ubuntu).
- `all.sh` e `matrix.sh`: l'elenco desktop identico; nuovi check per desktop (`check-kde-*`, `check-resize`, `check-exit`): vedi 20.9.

### 20.8 «Adding a video codec» — DA CORREGGERE
- La catena (capacita' scheda, `h264_card`/`hevc_card` in `encoder.c`, numeri RCP, tabelle della pagina) vale (`encoder.c`, `page.html`, `rcp.h` identici).
- Correggere la nota «State of HEVC»: round Ubuntu del 19 nov → Fedora: HEVC al browser non verificato; H.264 e' l'unico codec provato; su Fedora il driver H.264 viene da RPM Fusion (D1) e `--encoding-test h264` e' hardware `h264_vulkan` su Radeon (F35), riuscito anche su Intel dalla chiavetta (25 nov); riga «HEVC: yes via vaapi» e' dell'Ubuntu (`docs/STORIA-ubuntu-26.04.md`): togliere.

### 20.9 «Adding a check to prove/» — DA CORREGGERE
- Conteggi «thirteen check-*.py files; all.sh runs fifteen steps»: da ricontare su Fedora: `ls prove/check-*.py | wc -l` (ci sono in piu' `check-exit.py`, `check-kde-birth.py`, `check-kde-exit.py`, `check-kde-live.py`, `check-kde-resize.py`, `check-resize.py`) e `grep -n '^LABELS' prove/all.sh` (15 etichette, identiche a Ubuntu: `prove/all.sh:19`).
- Il resto (kit `lib.py`, FAIL/BLOCKED/SKIP/NOTE, `--only`, `sweep`) vale: `all.sh` identico. Pattern di `lib.sweep()`: aggiungere i prefissi dei check nuovi (non verificato: `grep -n "def sweep" -A8 prove/lib.py`).
- Aggiungere strumenti nuovi di Fedora: `prove/giro-selinux.sh` (nasconde un controllo morto a meta', aperto), `giro-xfce-radeon.sh`, `giro-lxqt-radeon.sh`, `prelocal.sh`, `hold.py`/`hold-user.py` (senza `RX_KEEP` chiude TUTTE le sessioni dell'utente: F22), `wall-selinux.sh`, `wall-neg-domain.py`, `wall-sesearch.sh`; `check-prelocal.py` P1–P8 (P6 controlla la riga PRIMA di `pam_selinux open`; P7 terminale, P8 editor non salvato: F33/F36).

---

# ch21_conventions — «Conventions» (7 sezioni)

### 21.1 «The written rules and what the tree does with them» — DA CORREGGERE
- `CLAUDE.md` di Fedora e' diverso da quello Debian/Ubuntu: 19 righe, «Fedora 45 only», «never touch ../debian13 ../ubuntu26.04», «SELinux stays enforcing; the package ships its own policy module. Service installed disabled», «NO containers, no podman», «Code comments in English», «Every closed or postponed problem gets a register entry». Riscrivere la tabella sulle regole VERE di `fedora45/CLAUDE.md`; sono stantie due frasi: «RPM packaging goes in rpm/ (to be written)» e «the Debian packaging to translate is ../ubuntu26.04/debian/» (il pacchetto esiste: `rpm/`).
- riga «service installed disabled»: `%systemd_post` + preset Fedora (spec:218), non `dh_installsystemd`.
- riga «licences ship in the package»: `LICENSE.md` e `THIRD-PARTY-LICENSES` di `fedora45/` descrivono ANCORA il labwc proprio (`LICENSE.md:95-102`, `THIRD-PARTY-LICENSES:9,24-25,1174`): non e' vero per Fedora (nessun labwc nel pacchetto). Decisione richiesta: correggere i file o citarli come stantii; il manuale non deve ripetere «our labwc».
- Non verificato: se lo spec installi `LICENSE.md`/`THIRD-PARTY-LICENSES` (`grep -n "LICENSE\|THIRD" rpm/remotix.spec`).

### 21.2 «Names, language and the Italian that remains» — DA CORREGGERE
- Da ricontare (cifre del manuale): occorrenze `registro_dice(`: `grep -o 'registro_dice(' src/*.c src/*.h | wc -l`; header guard: `grep -L pragma src/*.h` + `grep -c '#ifndef REMOTIX_'` (il manuale dice 45/53/59/5: ricontare, `src/` Fedora ha 5 header in piu'? no, ha lo stesso numero di `.h` ma verificare `ls src/*.h | wc -l`).
- Italiano in identificatori: `registro_dice`, `SORGENTI`, `OGGETTI`, `PROTOCOLLI`, … del `Makefile` restano (Makefile quasi identico; `grep -n "^SORGENTI\|^GEMELLATI\|^MINIMI" src/Makefile`).
- Elenco script/cartelle italiane: sostituire i VM-script di Ubuntu (`vm-radeon-aggiorna.sh`, `-controllo.sh`, `-installa.sh`, `vm.sh`, `vm-login-test.py`, `build/labwc-ospite/`) — non esistono in Fedora (`ls server/`: `live-installa.sh`, `prepara-server.sh`, `vm-radeon.sh`). Nomi italiani di Fedora da citare: comandi di `vm-radeon.sh` (`crea`, `accendi`, `spegni`, `ssh`, `istantanea`, `ripristina`, ecc.: elenco esatto non verificato: leggere l'intestazione dello script), `prove/giro-selinux.sh`, `giro-xfce-radeon.sh`, `giro-lxqt-radeon.sh`, VM `costruzione`, istantanee `pulito`, `codec`, `consegna-finale-<de>`, cartella `/media/REMOTIX-FEDORA/{pacchetti,vm-radeon,studio}`; nomi dei pacchetti di prova: `p4f`, `k4b`, `l6`, `s13`, `f1`, `g6`, `h1`, `i1`, `i2` (un nome breve + numero), non `unioneN`. Variabili del banco: `RX_BANCO`, `RX_TEMPO`, `RX_KEEP` (`hold.py`).
- «document headings: DECISIONI/SPECIFICHE»: `docs/DECISIONS.md` ecc. identici (copiati).

### 21.3 «Comments, marks and references» — DA CORREGGERE
- Cifre da ricontare: righe di C+header e di `page.html` («105,799 … 14,258»; `child.c` 12,671, `rcp.c` 10,485, `webtransport.c` 9,618, `session.c` 8,829): `wc -l src/*.c src/*.h | tail -1`, `wc -l src/page.html src/child.c src/rcp.c src/webtransport.c src/session.c`. (`child.c`, `session.c`, `kwin.c`, `main.c`, `walls.c` sono cambiati: le loro righe sono diverse da Ubuntu; `rcp.c`, `webtransport.c`, `page.html` uguali.)
- Marchi `[M] [R] [S] [?]`: validi. Gli `[M]` di Fedora citano macchine «VM `kde`», «macchina vera da chiavetta»; il manuale dice «rx-kde» (Ubuntu): sostituire.
- Il testo sui «dead references» (`CODER.md`, `REVIEWER.md`, `phases/`, `benches/`) vale ancora (commenti ereditati).

### 21.4 «Errors, fallbacks and invariants» — DA CORREGGERE
- Vale l'impianto (I1–I7 ecc.). Esempi da aggiornare: «DECLARED FALLBACK, D-015» (dconf) resta nel codice (`session.c`, verificare con `grep -n "DECLARED FALLBACK" src/session.c`); `_Static_assert (12 in the tree)`: da ricontare `grep -c _Static_assert src/*.c src/*.h | grep -v ':0'`.
- Aggiungere esempi Fedora di «fail closed»: SELinux acceso + errore = login RIFIUTATO (uscite 44/45/46/47, `child.c:1144-1147`; F31, F25), «un `.rpmnew` si adotta solo se provato che e' di questa transazione» (`remotix-pam-hook`, F21), «se il blocco PAM non torna non tocca nulla e avvisa» (hook, F6), `onerr=fail` di `pam_listfile` (`remotix.pam`).
- `exit 78` nel servizio: `rpm/remotix.service:54` (`RestartPreventExitStatus=78`).

### 21.5 «Logging conventions for a writer of code» — VALE COM'E'
- `log.c`/`log.h` identici; `docs/REGISTRO-priorita.md` presente. Cifra «33 patterns, 5 info, 24 warning, 4 errors»: storica, vale com'e' (non ricontata).
- Possibile aggiunta (a): `close_why()` di `transport.c` (F23/F31) come esempio «say what, not error» (chi ha chiuso, alert TLS con nome, «idle timeout» da `last_error`).

### 21.6 «The layout of the tree and the habits around it» — DA RISCRIVERE
Tabella cartelle di Fedora: `src/` (anche `remotix-pam-hook`, `protocols/kde-output-*`), `rpm/` (spec, servizio, firewalld, sysusers, tmpfiles, conf, denied-users, needrestart, no-suspend, `org.kde.remotix.desktop`), `selinux/` (`remotix.te`, `.fc`, `.if`), `build/` (`build-rpm.sh`, `quic-static.sh`: niente `labwc-ospite/`), `prove/` (+ `banco-vm/` 4 script), `server/` (3 script), `studio/` (studi 1-5 + `manuali/`), `docs/` (anche `STORIA-ubuntu-26.04.md`, ereditato), `manuals/`, `licenses/how-it-works.html`, `LICENSE.md`, `THIRD-PARTY-LICENSES`. Niente `debian/`, `boxes/`.
- punti elenco: «temporary files never in /tmp on the dev server» (RAM): vale per `build-rpm.sh`? non verificato; «nothing deleted without request»: vale; `build.py --check` vale (`manuals/sources/build.py`).
- `licenses/how-it-works.html`: nessuno spec lo copia? non verificato (`grep -n how-it-works rpm/remotix.spec`).

### 21.7 «Conventions of the Ubuntu tree» — DA CORREGGERE
Riscrivere come «Conventions of the Fedora tree» con righe vere:
- SKIP/NOTE/PARTIAL RUN: vale (`prove/all.sh` identico). `session_life()` 3 risposte: vale (`session.h` identico).
- riga AppArmor `deny` → regole SELinux scritte una per una con la ragione nel `.te` («ogni diritto e' in `selinux/remotix.te`, con la ragione», F27) e verificate in enforcing, mai con `-DB`/permissive (F28); prova negativa con `remotix_net_t` come root con tutte le capability (F24).
- «declared fallback»: vale (dconf; anche KWin: «DECLARED FALLBACK» F13).
- tag del revisore (N5, …): su Fedora lettere K, L, M, N, O (F34/F35).
- banco con nome: `RX_BANCO=vm`: vale; nome dei pacchetti di prova: parola breve + numero (`h1`, `i2`), cartella `/media/REMOTIX-FEDORA/pacchetti/<nome>/`.
- NUOVE convenzioni Fedora (a): una voce di registro per ogni problema chiuso o rimandato (`fedora45/CLAUDE.md`); «uniformita'»: il comportamento e' uno solo (Fedora = Debian = Ubuntu): una differenza di Fedora va elencata e portata, non lasciata (`PIANO.md` 22-23 nov); «provare il locale-chiude-remoto sempre con programmi aperti nel remoto» (F36).

---

# ch22_structures — «Appendix A — Data structures and messages» (6 sezioni)

Verificato: `rootside_proto.h`, `rootside.h`, `child.h`, `helper.h`, `command.h`, `rcp.h`, `session.h`, `budget.h`, `certificates.h`, `page.h` identici a Ubuntu (diff vuoto). Il capitolo non cita KWin, labwc, AppArmor, Debian o Ubuntu in modo fattuale, salvo il rimando alla «Debian tree» (S5) e `session_over_early()`/«never on KDE» (S4).

### 22.1 «The main C structures» — VALE COM'E'
- Strutture e costanti (`ROOTSIDE_GRANTS_MAX = 32`, `ROOTSIDE_LOGIN_USERS 1024`, …) invariate. «Covered in» → `rif(…)` verso titoli di altri gruppi: non toccare quei titoli.

### 22.2 «The root-side protocol, message by message» — VALE COM'E'
- Header identico: `RXR_VERSION = 3`, dimensioni: valide (stessa sorgente). Ricontrollo facoltativo: compilare `rootside_proto.h` da solo con gcc (leggero) e confrontare le dimensioni.
- (a) Possibile aggiunta: nello `RXR_CHILD_EXITED` (stato di `waitpid`) citare i NUOVI codici di uscita del figlio, solo Fedora: 44 nessun contesto SELinux «come un login locale», 45 `setexeccon` fallito, 46 la prossima exec non lascia `remotix_t`, 47 portachiavi di sessione (`child.c:1144-1147`; rifiuti provati: F31, F32). Il capitolo Ubuntu non elenca i codici 40-43.

### 22.3 «The PAM helper's packets» — VALE COM'E'
- `helper.h`, `helper.c` identici.

### 22.4 «Messages between the network side and a child» — VALE COM'E'
- `MSG_*` 1-20 e `CHILDREN_EXIT_*` (`child.h` identico). «Never on KDE» di `MSG_SESSION_FINISHED`: ancora vero (`child.c:12085`). `CLOSING_GRACE_MS = 30000`: `child.c:220`. `MSG_STAGE` con `fatal`: uguale.
- (a) Nota possibile: `CHILDREN_EXIT_*` 4 «un login locale e' tenuto in PAM» e' esattamente il caso di F36 su KDE (forzata a 5 s in Fedora).

### 22.5 «The unblock command socket» — VALE COM'E'
- `command.c` identico. «With the network side behind its walls the socket would live in /run/remotix/net»: coerente con SELinux (`remotix_net_t` scrive solo `/var/lib/remotix/net` e `/run/remotix/net`, F24). Facoltativo: aggiungere «AppArmor o SELinux» dove dice «walls».

### 22.6 «Index of RCP/1 messages and farewell reasons» — VALE COM'E'
- `rcp.h`/`rcp.c` identici; tutte le righe valgono.

Elenchi del gruppo (ch22): (a) nuove sezioni: nessuna obbligatoria; opzionale i codici 44-47 in 22.2. (b) Da togliere: la parentesi «the plan of the Debian tree» in 22.5 (storia). (c) `rif()`: nessuno si rompe se i titoli restano.

---

# ch23_map — «Appendix B — File map» (1 sezione)

### 23.1 «Every file of the tree» — DA RISCRIVERE
Il generatore FALLISCE se la mappa non coincide con l'albero (`build.py:file_map`). Fedora usa `git ls-files --cached --others --exclude-standard src rpm selinux build prove server` (`build.py:351`: nessuna cartella `debian`, `boxes`). Differenze controllate (script di confronto sulla mappa Ubuntu):
- MANCANO nella mappa (esistono in Fedora, esclusi `.wasm`/`.sha256`): `src/remotix-pam-hook`, `src/protocols/kde-output-device-v2.xml`, `src/protocols/kde-output-management-v2.xml`, `src/protocols/README-kde-output.txt`; `rpm/remotix.spec`, `rpm/remotix.service`, `rpm/remotix.sysusers`, `rpm/remotix.tmpfiles`, `rpm/remotix.conf`, `rpm/remotix.firewalld.xml`, `rpm/denied-users`, `rpm/needrestart.conf`, `rpm/remotix-no-suspend.conf`, `rpm/org.kde.remotix.desktop`; `selinux/remotix.te`, `selinux/remotix.fc`, `selinux/remotix.if`; `build/build-rpm.sh`; `prove/check-exit.py`, `check-kde-birth.py`, `check-kde-exit.py`, `check-kde-live.py`, `check-kde-resize.py`, `check-resize.py`, `giro-selinux.sh`, `giro-xfce-radeon.sh`, `giro-lxqt-radeon.sh`, `hold.py`, `hold-user.py`, `prelocal.sh`, `wall-selinux.sh`, `wall-neg-domain.py`, `wall-sesearch.sh`, `prove/banco-vm/autologin-lightdm.sh`, `prove/banco-vm/autologin-sddm.sh`.
- CITATI ma inesistenti in Fedora (da togliere): tutto `boxes/*` (6 file), `build/Containerfile`, `build/build-deb.sh`, `build/labwc-ospite/*` (5), tutto `debian/*` (18 voci), `server/vm.sh`, `server/vm-login-test.py`, `server/vm-radeon-aggiorna.sh`, `-controllo.sh`, `-installa.sh`, `server/vm-radeon-login-test.py`. (Sono i 40 «citati che non esistono» di `studio/manuali/check-iniziale.md`.)
- Descrizioni da riscrivere per file che esistono: `src/kwin.c` (KWin da solo `--virtual`, `kwin_output_resize`, sidecar ScreenSaver, poke), `src/kwin.h`, `src/kdehost.h` (doppio marchio `--kwin-virtual`/`REMOTIX_KDE_HOST=1`), `src/walls.c` (+ gemello SELinux `remotix_net_t`), `src/child.c` (contesto SELinux, lingua), `src/main.c` (`--kwin-virtual`), `src/Makefile` («with the path of our labwc, LABWC» e' falso; `-lselinux`, protocolli `kde-output-*`), `src/remotix.pam` (stack sshd di Fedora/authselect, `/etc/locale.conf`), `src/remotix-remote-sessions.rules` (+ `fwupd.refresh-remote`), `src/local_login.c` (invariato), `src/transport.c` (`close_why`), `src/input.c` (primo movimento doppio), `src/remotix-pam-hook` (aggancio sulle 4 schermate), `src/card_pick.c` («which card the desktop draws on»: su KDE non piu' usato, F7), `src/clipboard_kde.c` («also bound on labwc» vale per XFCE/LXQt).
- Gruppo «Test containers (boxes/)» → togliere. Gruppo «Build (build/) and dev server (server/)» → ridisegnare (3 script `server/`, `build-rpm.sh`, `quic-static.sh`). Gruppo «Package (debian/)» → «Package (rpm/) and SELinux (selinux/)».
- Righe da ricontare (generate dal generatore: nessuna cifra a mano). `_manual_rows()` testa la stringa `technical-ubuntu26.04` → deve diventare `technical-fedora45` (`grep -n "technical-" manuals/sources/technical-fedora45/ch23_map.py`).
- (b) Ubuntu-only da togliere: vedi sopra. (c) `rif()`: la sezione ha un solo rimando testuale («the chapter list at the start of this manual»); nessun `rif()`.

---

# ch24_problems — «Appendix C — Known issues and open points» (11 sezioni)

Nota generale: le voci A–E del registro in `fedora45/docs/` sono ereditate da Ubuntu; i fatti Fedora sono F1–F36. Molte celle di questo capitolo vanno riscritte da F1–F36 e dal `PIANO.md`.

### 24.1 «How to read this appendix» — DA RISCRIVERE
- «REMOTIX 1.0.1 for Ubuntu 26.04», «1.0.1 non ha avuto un giro completo», nota «unione10 … 120 PASS, 2 FAIL, 1 BLOCKED, 3 SKIP» e «polkit rule of 15 vs 19 (unione11)» sono Ubuntu. Fedora: versione 1.2.0; pacchetto candidato `i2` (sha256 `172d4e89…6393930b`, `PIANO.md` r.454); h1 approvato e provato sui 4 desktop; i2 differisce da h1 solo per la chiusura KDE e la regola SELinux e NON e' stato rieseguito sugli altri tre (decisione del proprietario). Giro finale h1: GNOME 52 PASS + FAIL pkexec noto + `all.sh` 39 PASS; KDE 76; XFCE 60; LXQt 60; prova negativa del muro 0 FAIL; perdite audit 0 (F35). Prove su macchina vera da chiavetta (25 nov): GNOME, XFCE, LXQt OK con h1; KDE NON superata con h1 (F36), OK con i1 e i2.
- «Two sections specific to this tree» → «Fedora: what real machines showed…» e «Fedora: open points».

### 24.2 «What is unverified» — DA RISCRIVERE
Riga per riga:
- «AppArmor in a session» → SELinux: enforcing sempre, 0 AVC nostri sui 4 desktop (F24, F33, F35); resta largo `remotix_t` lato root (F27); `ausearch` non vede nulla sulle VM anche con AVC (usare `journalctl -b -g avc:`, F24). Non provato: accesso locale vero con il muro su gdm/plasmalogin prima del 25 nov (poi provato da chiavetta); riavvio VM col modulo: provato (F24).
- «A real phone»: Fedora: proprietario da Android (video 1440p fluido), Windows e Linux (21-22 nov, `PIANO.md`); due utenti, telefono, Flatpak non provati da lui; Samsung DeX: non verificato su Fedora.
- «GNOME, first tap after login»: sostituire con F34 (mutter 51.0: primo movimento assoluto con una coordinata a 0; cura `input.c`, campo `pointer_primed`, «TO BE REMOVED WHEN MUTTER IS FIXED»; su Ubuntu e' E2 «probabilmente lo stesso», non provato).
- «NVIDIA»: nessuna prova (come Ubuntu); Intel: codifica provata sulla macchina da chiavetta, suite no.
- «4096×2304»: `canvas-limits` su Fedora: non verificato.
- «Capacity»: come Ubuntu; due/tre utenti PASS su GNOME dopo g6 (F34).
- «Reproducible build»: Fedora ha solo R13/R4 in `build-rpm.sh` e `%build` (R24 per i `bundled()`); riproducibilita' e lintian: non verificato/assenti. Non citare `controlli.txt`/`R23`.
- «Local-session refusals»: Fedora: provato da chiavetta su tutte e quattro (gdm OK, lightdm OK 1,7 s, sddm OK 0,7 s, plasmalogin OK solo con i1/i2); `check-prelocal.py` P1–P8 PASS su KDE (F36), P1–P5 su VM pulita; caso residuo: lightdm come server XDMCP/VNC (non provato, F21(b)); finestra di pochi secondi durante l'aggiornamento di sddm (F21). Nessun check automatico copre il motivo 0x05: non verificato su Fedora.
- «Network hardening»: unita' con `--address 0.0.0.0` (`rpm/remotix.service:45`): solo IPv4; nessun check di flood: come Ubuntu.
- «Versions of XFCE and LXQt»: Fedora 45: xfce 4.20 (xfdesktop 4.20.2-2, libxfce4windowing 4.20.7), LXQt 2.4 (sessione locale Wayland su miriway), labwc 0.20.2, GNOME 51 (mutter 51.0, gdm 51.0→51.1.1), Plasma 6.8 (KWin 6.8.3), systemd 262, wlr-randr 0.5.0 (fonti: `PIANO.md` r.62-63, F22, F33, F34, F6). Commenti di `session.h` citano ancora labwc 0.8.3 / lxqt-session 2.1.1 (codice giusto).
- «Settings model, branches tried only by reading»: `session.c` e' CAMBIATO (compilazione in `/run/remotix/dconf-compile.tmp`); F24 dice «Provato: database mancante e database diverso, etichetta giusta, 0 AVC»; il ramo «vita SCONOSCIUTA» resta non provato (non verificato); `dconf` assente: ripiego dichiarato, non provato su Fedora.
- «Measured figures in comments»: vale com'e' (stessi commenti).
- «Package check»: `check-package.py` non e' stato eseguito su Fedora (non verificato); l'installazione/rimozione `dnf` e' provata a mano (F6 p.5, F19, F21, F24: «rimozione … lascia il sistema pulito»). Da riscrivere con fonti.
- Nuove righe (a): enforcing con SELinux utenti confinati: provato `staff_u`/`user_u` su 4 desktop (F25), XFCE+`staff_u` pannello non parte (F30, non nostro); multi-GPU non provabile (F12); incognite KDE I11/I2/I13 (F11); KWin lento oltre 3 s → ripiego dichiarato (F13); lingua senza codifica (`it_IT`) e `FormatsLocale`/`LANGUAGE` non provati (F34/F35).

### 24.3 «Known limits and what was proven» — DA RISCRIVERE
- Valgono: «Declared limits» (8 utenti, 3K), «Service killed and not yet restarted» (`RestartSec=2`, `rpm/remotix.service:55`), «Scale of the user» (`mutter.c` identico; GNOME 51 non riprovato).
- «XFCE black background»: Fedora: D7, limite DICHIARATO; `xfdesktop 4.20.2-2` compilato senza Wayland («xfdesktop was not built with Wayland support», F22), fondo nero senza icone, pannello e dock presenti; non e' la causa E1 di Debian (libxfce4windowing 4.20.2 — qui 4.20.7); la prova breve di un rimedio non e' riuscita (F33 p.8).
- «How the local-login hold was proven»: sostituire con F6, F9, F18, F19, F22 e le prove da chiavetta del 25 nov (`PIANO.md` r.343-366), poi F36 (KDE: tre cause, correzione `exit_kde(TRUE)`, regola SELinux, 5 s).
- «GNOME pkexec»: vale (FAIL `users-shell-and-environment`, SHELL vuoto, comune a Ubuntu: `PIANO.md` r.299); `sudo-rs`→ su Fedora `sudo` classico: non verificato; terminale `ptyxis` su GNOME Fedora: non verificato.
- «Kernel with mediation of unix sockets / AppArmor»: DA TOGLIERE (Fedora usa SELinux; equivalente: F24, F27).
- «Programs with their own settings reader» (snap/Flutter): togliere; Flatpak «partono senza nulla di speciale» (`PIANO.md` r.67, non provato dal proprietario). «One small file stays until apt purge» → `dnf remove`: `%postun` toglie `~/.config/dconf/remotix` e `~/.local/state/remotix/*` per nome, come l'utente (spec:400-406) e `/etc/dconf/db/remotix` (spec:421-422).
- «RealtimeKit in the containers (history)»: togliere.
- Nuove righe (a): portachiavi (D6: nessun `pam_gnome_keyring`/`oo7`/`kwallet`, GNOME `oo7` bloccato nella sessione remota, KDE `ksecretd`); KWin ricorda l'ultima misura di `Virtual-0` in `~/.config/kwinoutputconfig.json` (F8); ridimensionamento a caldo inesistente su ogni desktop (F14, DECISIONS §5.1-bis); orologio del dispositivo client giusto (notBefore = −3600 s, `certificates.c:143`, F23); codec da RPM Fusion (D1) e porta nel firewall a carico dell'amministratore (D5, F20).

### 24.4 «Ubuntu: what real machines showed that the boxes did not» — DA RISCRIVERE
Titolo → «Fedora: what real machines showed that the VMs did not». Contenuto Ubuntu da togliere o ridurre a una riga storica: C4 (AppArmor `deny unix`), C5 (snap/Flutter dconf), B3-bis (GTK 4.22: non verificato su Fedora), D (Plasma 6.6 `plasma-shutdown`), C6 (polkit implications: la regola Fedora e' identica, `power-implied` PASS su XFCE, F33). Voci Fedora da scrivere (fonte):
- F36 KDE: con un programma che non si chiude da solo l'accesso locale passava col remoto vivo (3 cause: `Shutdown.logout` senza limite; forzata su `plasma-workspace.target` invece di `graphical-session.target`; `stop` negato a `remotix_t` su `xdm_unit_file_t`); soluzione `session.c` + `selinux/remotix.te`; prove: forzata 5,04 s, tutto fermo 0,56 s dopo, 0 rifiuti, 0 core dump (`PIANO.md` r.435-453).
- F2 login con `pam_selinux open` negato; F6 la riga PAM va PRIMA della prima `session` (consumo dell'exec); F21 sddm con file `%config` del pacchetto (`.rpmnew`/`.rpmsave`, adozione `prepare`/`apply`); F17 firewalld XML non valido; F20 `INVALID_SERVICE` fino al reload (ora `%firewalld_reload`); F23 «Opening handshake failed» da orologio sballato; F34 coordinata 0; F35 lingua; «tastiera del proprietario collegata al tablet» (non del prodotto, 25 nov).
- `[M]` Il giro di prove automatico e la macchina vera dicono cose diverse: A3/F36 («provare su un solo desktop nasconde difetti»).

### 24.5 «Open points in the server» — DA CORREGGERE
- «No unblock» e «Page certificate name», «Root-side login pauses», «Timing tail», «Faillock detection» (inglese: su Fedora `pam_faillock` viene dal profilo authselect `with-faillock`, `remotix.pam`), «Quotas», «TERMINATE_SESSION», «PACE», «Single-process mode», «Clocks», «Mounts after start», «Pins», «Session id»: valgono (codice identico).
- «No firewall rule opened»: `ufw` → servizio firewalld `remotix` definito e mai aperto (D5, F20, `rpm/remotix.firewalld.xml`); zona predefinita `public` chiusa su XFCE/LXQt, aperta da 1025 su GNOME/KDE (zona Workstation, `PIANO.md` r.90-91): la porta 7447 e' sotto 1025? 7447 > 1025: aperta di fatto su Workstation: non verificato — da controllare prima di scrivere.
- «Kernel requirements»: Landlock 6.12, `mount_setattr` 5.12: kernel di Fedora 45 non verificato.
- «Trust boundaries»: «root side is root and unconfined» → `remotix_t` confinato ma largo (F27: diritti di login program, passaggio verso ogni dominio utente, `sys_admin`/`net_admin`/`setpcap`, le «faccende» nel gestore utente, scrittura in `/etc/dconf/db` a nomi fissi, `domain_kill_all_domains`).
- «Power belts shipped off»: file in `/usr/share/remotix/belts/` (spec:159-162), regola polkit unica cinghia attiva.
- «Needrestart»: `rpm/needrestart.conf` installato in `/etc/needrestart/conf.d/` (spec:165-166); `needrestart` non e' di serie su Fedora: nota «se mai installato».
- «Closing a session before the stage is gone»: vale (KDE no: `child.c:12085`); aggiungere F36.
- (a) Nuove: nessuna rete di sicurezza comune: GNOME ha la stessa costruzione di KDE e nessuna «ultima difesa» (non provato); `force_guard_on` resta acceso dopo una chiusura per accesso locale fallita (`session.c:5549`/`5560`, il PIANO cita `session.c:8770`: riga da ricontare con `grep -n force_guard_on src/session.c`).

### 24.6 «Open points in capture and encoding» — DA CORREGGERE
- «KDE and our labwc» → riscrivere: KWin 6.8 da solo, `--virtual`, `kwin_output_resize()` (`kde_output_management_v2` ≥ 22, `add_cvt`, qualsiasi misura); se manca il protocollo: sessione RIFIUTATA con messaggio (F7); KWin non risponde: ripiego «DECLARED FALLBACK» (F13); incognite aperte F11 (I11 DMA-BUF, I2 cursore, I13 sonde); scelta della scheda non provabile con una sola Radeon (F12); codice labwc-per-KDE morto da togliere (F7).
- «Lost frames of KWin»: il meccanismo e' di `capture.c` (identico); non misurato con KWin 6.8: non verificato.
- «HEVC»: → Fedora: H.264 e' l'unico provato (D1); riga «HEVC: yes via vaapi / Vulkan nelle VM» dell'Ubuntu: rifare con F35 (h264_vulkan Radeon).
- «No card or card that does not encode»: `%pre` rifiuta senza render node (spec:168-179); `%post` avvisa se la scheda non codifica e dice di installare RPM Fusion `mesa-va-drivers-freeworld` (spec:258-263 circa).
- Valgono: «Dead AV1 code», «Shader header», «Budget…», «Startup codec probe», «Encoded cursor theme».

### 24.7 «Open points in the page, input, audio and clipboard» — DA CORREGGERE
- `page.html` identico: righe «Ctrl+Alt+Del», «Firefox», «Keyboard layout», «Test switches», «Opus decoder», «Audio and clipboard» valgono.
- «KDE: held Delete, Klipper»: non verificato con Plasma 6.8 (`clipboard_kde.c` identico).
- «Window test and GTK 4.22 (B3-bis)»: la versione di GTK su Fedora 45 non e' verificata; la riga e' Ubuntu: togliere o marcare.
- (a) Nuova: primo movimento del puntatore su GNOME (F34), cura in `input.c` solo su mutter (su wlroots non passa).

### 24.8 «Open points in the desktops and logging» — DA CORREGGERE
- «XFCE»: aggiungere D7/F22 (sfondo nero, nessuna icona) e F30 (`staff_u`: pannello non parte, non nostro); i tre programmi che sopravvivono all'uscita (abrt-applet, geoclue agent, localsearch) non contati (F22).
- «GNOME»: `lock-warning-shown` (avviso «Screen Lock disabled» di Ubuntu): non verificato su GNOME 51 di Fedora; pkexec: vedi 24.3; Overview all'avvio: non verificato; scala utente: vedi sopra.
- «KDE»: `session_kde_logout_watch()` esiste (`session.c:5300`, usato `child.c:10873`); la ragione citata («Plasma 6.6 non rilascia il nome») e' di Ubuntu: su Plasma 6.8 la forzata ora ferma `graphical-session.target` (F36); F16: programmi di sfondo KDE in SIGABRT se la sessione viene chiusa «da fuori» (27 file in 25 s con `terminate-session`; 0 core dump nel caso reale simulato col gancio, F33 p.7).
- «LXQt»: `blueman.desktop` nascosto: vale (elenco di Ubuntu, F33 p.2); `lubuntu-update`: non esiste su Fedora; LXQt 2.4 senza `qlipper` (appunti via data-control di labwc, F22); X11 composition managers: invariato.
- «Settings left behind»: `apt purge` → `dnf remove` (`%postun`, spec:400-422); marcatori `gnome-ripristinato`, `lxqt-restored`, `xfce-vecchi-ripristinati`: spec:406 li toglie.
- «Environment variables», «Log priorities»: valgono.
- (a) Nuove: programmi avviati di serie (dnfdragora-updater, abrt, geoclue, nm-applet, Welcome Center) non nascosti (F33 p.2, solo `blueman.desktop`).

### 24.9 «Open points in testing and build» — DA RISCRIVERE
- «Rounds of 19 Nov 2026»/«Virtual-machine bench» → giri Fedora: pacchetti `s8`→`s13`→`s15`→`f1`→`g6`→`h1` (F24, F32-F35) e `i1`/`i2` per KDE; banco VM con Radeon, SELinux enforcing, prova negativa `wall-selinux.sh` 25/25 (F24, F31) e 0 FAIL con h1 (F35); `check-kde-exit` «service restart» a volte esce senza risultato (intermittente, causa non trovata, `PIANO.md` r.322-325); `giro-selinux.sh` nasconde un controllo morto a meta' (aperto prima di pubblicare).
- «Package check»: vedi 24.2.
- «Check scripts»: `prove/fresh.sh`/`lib.py` cercano `prove/boxes` o `../boxes`: su Fedora non esistono (non verificato il comportamento: `grep -n boxes prove/lib.py prove/fresh.sh`); `lib.sweep()` prefissi: ricontare; `check-base.py`/`base-check.py` doppioni: invariato.
- «Build»: `make` con `TWIN=none` passato dallo spec (spec:117-133), `SOURCE_DATE_EPOCH`: non verificato (Fedora RPM ha sue regole di `source_date_epoch_from_changelog`); `build/build-deb.sh` → `build/build-rpm.sh` (VM `costruzione`, ssh 2355).
- «Clean-up»: «a port to a distribution with SELinux needs the removed SELinux code again» → FATTO su Fedora. Aggiungere: D8 OpenSSL 4.0, `ExclusiveArch x86_64 aarch64`.

### 24.10 «Ubuntu: open points» — DA TOGLIERE
- E3 (foto dell'ambiente), E4 (stutter Android), wireplumber, autobind AppArmor, tempo KDE 10.9 s su Kubuntu, rami dconf non provati, limiti C5, «what was not proven on Ubuntu», «from the studies, not re-checked»: sono Ubuntu. E3 e i limiti del modello dconf riguardano codice che Fedora condivide (`session.c`): se si vuole tenerli, rifarli come «ereditati da Ubuntu, non provati su Fedora». Il titolo di sezione e' citato da `ch19 S7` e `ch21 S7`, `ch24` stesso: aggiornare i `rif()` insieme (vedi sotto).
- (a) NUOVA sezione consigliata «Fedora: open points» (in questo capitolo, dopo 24.9), contenuto: KDE forzata troncata a 5 s (programmi lenti a chiudersi non provati; chiusura per abbandono non provata); GNOME senza ultima difesa; Debian/Ubuntu col codice di forzata invariato (le cure nate su Fedora vanno portate: `PIANO-1.0.2-debian-ubuntu.md`); `catatonit` (aiutante podman) resta nel gestore utente dopo l'accesso locale; rifiuto `search` su `/proc/sys/dev`; `force_guard_on`; F28 rifiuti SELinux non nostri (`relabelto` su `tmp_t`, `map` su `hwdb.bin`, `bwrap` in `staff_t`); F15 AVC `xdm_t`→`stratisd_t` `{ view }` di gdm (non nostro); F27 `remotix_t` largo; F30; `giro-selinux.sh`; commento `child.c:1636` da allineare; lingua `it_IT` senza codifica; `LANGUAGE`/`FormatsLocale` non provati; XFCE sfondo (D7).

### 24.11 «Contradictions between code, comments and documents» — DA CORREGGERE
- Numeri di riga (main.c, child.c, session.c, walls.c, transport.c, rcp.c…): da ricontare TUTTI, `main.c`/`child.c`/`session.c`/`walls.c`/`transport.c` sono cambiati (es. `main.c` ha 7 righe in piu' dopo la 2886; `child.c` ~370 righe di diff). Comando: `grep -n "<testo>" src/<file>`; per `rcp.c`, `webtransport.c`, `rootside*.h`, `page.html` (identici) le righe di Ubuntu valgono ancora.
- Righe che restano vere (codice/commenti ereditati): «Fixed answer time», «Paused AUTH», «fds crossing», «PAM_RHOST», «Process limit», «/proc», «Hooks (27)», «Pending caps», «Page caps», «Keepalive», «Client close codes», «Shutdown wait», «PACE», «Encoder header», «NVIDIA», «Bandwidth floor», «Names», «Logging», «Test windows»… (nessuno di quei file cambia).
- DA TOGLIERE: «AppArmor» (profilo assente), «PIANO.md» (il file Fedora e' un piano con diario fino al 25 nov: riscrivere la riga), «Licences: CLAUDE.md…» (il CLAUDE.md di Fedora non lo dice).
- DA CORREGGERE: «Stale installer text»: `main.c:467-473` (nome del file verificato) dice ancora «Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch» e `rpm/remotix.service:6` ha `--without split`/REMOTIX_SPLIT (letto); «Desktops survive the stop»: `main.c:3972-3977` «the desktops stay alive» e, NUOVO, `rpm/remotix.spec:220` («the desktops stay alive» all'aggiornamento) contraddicono §11.56; «Debian-only wording»: `remotix.pam` ora dice «FEDORA 45 ONLY» (corretto), `local_login.c:20` cita ancora «systemd 257» (file immutato), `CLAUDE.md` e' Fedora; «--session-fd»: invariato (non verificato se Fedora lo passi: `grep -n session-fd src/child.c src/session.c`); «Paths»: `debian/control` → `rpm/remotix.spec`.
- NUOVE (a) per Fedora: `LICENSE.md:95-102` e `THIRD-PARTY-LICENSES:9,24-25,1174` descrivono il labwc nel pacchetto (falso per Fedora); `CLAUDE.md` «RPM packaging … (to be written)»; `Makefile:132-133` `LABWC ?= /usr/libexec/remotix/labwc` e `-DREMOTIX_LABWC` (stringa orfana, F1/F7); `kwin.h` «nested box above is DEAD»; codice labwc-per-KDE irraggiungibile in `kwin.c`/`child.c`/`main.c` (F7); `prove/lib.py:37` commento «boxes/box.sh header» (le porte 8821-8824 non servono a Fedora); commento `child.c:1636` da allineare (`PIANO.md` r.324); `docs/STORIA-ubuntu-26.04.md`, `INVENTARIO-non-debian.md`, `PULIZIA-tranche1.md` ereditati e non di Fedora; `session.c:300,801,3014` citano `xubuntu`, `kubuntu`, «Prefer ubuntu session», `gdm3`.

Elenchi del gruppo (ch24): (a) nuove sezioni: «Fedora: what real machines showed…» (sostituisce 24.4), «Fedora: open points» (sostituisce 24.10). (b) Da togliere: tutto AppArmor/snap/Flutter/ufw/RealtimeKit-container/unione10/C4/C5/B3-bis. (c) `rif()` che si rompono se si cambiano i titoli: «Ubuntu: open points» (da ch19 S1/S7, ch21 S7, ch24 S_INTRO/S_REAL/S_CONTRA), «Ubuntu: what real machines showed that the boxes did not» (da ch20 S4, ch24 S_LIMITS/S_OPEN), «What is unverified» (da ch20 S4), «Appendix C — Known issues and open points» (titolo di CAPITOLO, citato da ch01, ch04, ch07, ch09, ch10, ch13, ch14, ch15, ch17, ch19, ch20, ch21).

---

# ch25_glossary — «Glossary» (1 sezione)

### 25.1 «Terms used in this manual» — DA CORREGGERE
Voci da TOGLIERE: «Our labwc (guest labwc)» (non c'e' in Fedora), «Flutter program», «Snap», «sudo-rs, rust-coreutils» (su Fedora: non verificato che servano; `sudo` classico), «Unione» (nomi dei pacchetti di prova Ubuntu).
Voci da RISCRIVERE:
- «AppArmor» → «SELinux»: modulo `remotix` dentro il pacchetto (`selinux/remotix.te`, `.fc`, `.if`), tipi `remotix_t` (lato root), `remotix_net_t` (parte di rete), `remotix_hook_t` (aggancio PAM), `remotix_exec_t`, `remotix_dconf_db_t`, `remotix_prelocal_t`; sempre enforcing (D3, F24).
- «Compositor»: XFCE/LXQt labwc di Fedora (0.20.2); GNOME Mutter; KDE KWin da solo (`--virtual`).
- «VM bench»: 4 VM Fedora 45 + VM di build, Radeon con vfio, `server/vm-radeon.sh`, `prove/banco-vm/`, `RX_BANCO=vm`.
- «Walls»: aggiungere l'equivalente SELinux in `walls.c` (`remotix_net_t`).
- «System dconf database»: compilato dallo `%post` dello spec e dal servizio (non da `postinst`), `/etc/dconf/db/remotix`.
- «Needrestart drop-in»: vero solo «se needrestart e' installato» (spec:165-166).
- «Lost frame, poke»: valido, annotare «non misurato con KWin 6.8».
- «Local-login hold»: oggi anche `remotix-pam-hook` per gdm/plasmalogin/lightdm/sddm.
Voci che VALGONO: Ban, Child, Declared fallback, Detach/reattach, Fixed second, Found again, HTTP/3, Local excludes remote, Log Out, Network side, No orphan desktops, Opus, PAM, PipeWire, QUIC, RCP/1, Root side, Runtime dconf profile, Sentinel, Session life, Stage, Vulkan Video, VA-API, WebTransport.
(a) NUOVE voci consigliate: SELinux/domain/AVC, authselect, `remotix-pam-hook`, firewalld service, RPM Fusion (`mesa-va-drivers-freeworld`), plasmalogin, «KWin alone» (`--kwin-virtual`, `kwin_output_resize`, `kde_output_management_v2`), `wheel`, `graphical-session.target` (F36), «forzata» (forced close), «giro» (round), «banco».
(b) Ubuntu/Debian-only da togliere: vedi sopra.
(c) `rif()`: nessuno nel glossario (usa `dl()`); le definizioni possono essere citate da altri capitoli per nome: non verificato (`grep -n "Glossary" manuals/sources/technical-fedora45/ch*.py`).

---

# Elenchi di sintesi del gruppo

## (a) Cose solo Fedora che meritano una sezione NUOVA
1. ch19: «Closing time of a local login, per desktop» (tempi da F6, `PIANO.md` 25 nov, F36) — o inglobata in 19.4.
2. ch20: «Porting to Fedora: what changed in practice» (sostituisce 20.4) + nuova riga della checklist su authselect/SELinux/firewalld.
3. ch21: «Conventions of the Fedora tree» (sostituisce 21.7).
4. ch22: facoltativo, codici di uscita 44-47 del figlio (in 22.2).
5. ch24: «Fedora: what real machines showed that the VMs did not» (F36 ecc.) e «Fedora: open points».
6. ch25: SELinux, `remotix-pam-hook`, firewalld, RPM Fusion, KWin alone, plasmalogin.

## (b) Da togliere (Ubuntu/Debian-only)
`our labwc` e `build/labwc-ospite/` (ch20, ch21, ch23, ch24, ch25); AppArmor (profilo, C4, `deny unix`, autobind); ufw; snap e Flutter (C5); sudo-rs/rust-coreutils; `needrestart` come fatto Ubuntu; `debian/*`, `boxes/*`, `server/vm*.sh` di Ubuntu; «unione10»; E3/E4/wireplumber/KDE 10.9 s; round del 19 nov e tutte le cifre di `check-media`/timing di Ubuntu; il giro `RX_TEMPO` di Ubuntu; riferimenti a Kubuntu/Xubuntu/Lubuntu; RealtimeKit B2; commenti «Debian only».

## (c) `rif("…")` che si rompono se si cambia un titolo
- Titoli di SEZIONE del gruppo citati altrove: «Where no measurement exists» (ch19 stesso), «What the clean-up removed, kept and risked», «A checklist for porting to another distribution», «Where the code depends on the distribution», «The one-distribution rule» (ch20/ch21), «Ubuntu: open points», «Ubuntu: what real machines showed that the boxes did not», «What is unverified» (ch19, ch20, ch21, ch24).
- Titoli di CAPITOLO del gruppo citati da altri gruppi: «Performance and capacity» (ch07, ch08, ch12, ch17), «Extending REMOTIX and porting to another distribution» (ch12, ch18), «Conventions» (ch01, ch20), «Appendix A — Data structures and messages» (ch02), «Appendix C — Known issues and open points» (ch01, ch04, ch07, ch09, ch10, ch13, ch14, ch15, ch17, ch19, ch20, ch21). Non rinominare i capitoli.
- `rif()` dal mio gruppo verso titoli di altri gruppi (devono esistere ancora): «Testing», «The VM bench», «The lost frame (KWin)», «Quality, degradation and budget», «The four desktops», «The RCP/1 protocol», «Build and release», «Video encoding», «Startup and life cycle», «Logging and diagnostics», «The package», «Overall architecture», «Login and its defences», «Transport», «The local-login hold», «Desktops found again after a restart» (tutti presenti ora nei sorgenti Fedora: nessun `NOT FOUND` nel controllo).
