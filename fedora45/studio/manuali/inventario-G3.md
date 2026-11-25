# Inventario G3 - manuale tecnico Fedora 45, capitoli ch12-ch14, e manuale utente completo (ch01-ch06)

Data: 25 nov 2026. Sola lettura. Albero letto: `fedora45/` (spec ancora `Version: 1.2.0` gia' scritta, `rpm/remotix.spec:25`, `%changelog` 1.2.0-1 del 25 nov).
Base: `ubuntu26.04/manuals/sources/technical-ubuntu26.04/ch12_desktops.py`, `ch13_login.py`, `ch14_security.py` (31 sezioni, 2208 righe) e
`ubuntu26.04/manuals/sources/user-ubuntu26.04/ch01..ch06` (34 sezioni, 1257 righe). Fonti Fedora: `PIANO.md` (D1-D8, giornale, piano manuali),
`docs/REGISTRO-problemi.md` F1-F36, `studio/1..5`, `rpm/`, `selinux/`, `src/` (`diff -rq ../ubuntu26.04/src src` e diff mirati), `src/remotix-pam-hook`,
`src/local_login.c`, `prove/`. Non ho letto i log dei giri (stanno sul server): le cifre di test citate sotto sono quelle scritte in `PIANO.md` e nel registro.
Dove non ho potuto controllare c'e' scritto «non verificato». «da ricontare» = numero che il manuale ricava dal codice: va ricalcolato col comando indicato, non copiato.

## Tabella riassuntiva

| Capitolo | Sezioni | Vale com'e' | Da correggere | Da riscrivere | Da togliere (sezione intera) |
|---|---|---|---|---|---|
| tecnico ch12 The four desktops | 11 | 0 | 9 | 2 | 0 |
| tecnico ch13 Login and its defences | 10 | 4 | 5 | 1 | 0 |
| tecnico ch14 Security model | 10 | 1 | 7 | 2 | 0 |
| **Totale tecnico G3** | **31** | **5** | **21** | **5** | **0** |
| utente ch01 What REMOTIX is | 5 | 0 | 3 | 2 | 0 |
| utente ch02 Installing REMOTIX | 8 | 3 | 1 | 4 | 0 |
| utente ch03 Connecting and using it | 7 | 1 | 6 | 0 | 0 |
| utente ch04 When something does not work | 7 | 3 | 3 | 1 | 0 |
| utente ch05 Looking after an installation | 6 | 2 | 3 | 1 | 0 |
| utente ch06 Glossary | 1 | 0 | 1 | 0 | 0 |
| **Totale utente** | **34** | **9** | **17** | **8** | **0** |
| **Totale G3** | **65** | **14** | **38** | **13** | **0** |

(Dentro le sezioni «da correggere» c'e' spesso un blocco da togliere: e' indicato nella voce. Nessuna sezione intera si toglie, ma molti sottoparagrafi si'.)
«Vale com'e'» comprende le sezioni dove cambiano solo i titoli dei `rif()` (vedi (c) in fondo).

## Fatti-base per tutte le voci (con la prova)

- **Codice quasi identico a Ubuntu.** `diff -rq ubuntu26.04/src fedora45/src`: differiscono `child.c, input.c, kdehost.h, kwin.c, kwin.h, main.c, Makefile, remotix.pam,
  remotix-remote-sessions.rules, session.c, transport.c, walls.c`; nuovi `remotix-pam-hook` e `protocols/kde-output-*`. Identici (quindi ogni frase che li descrive resta vera):
  `rcp.c/.h, rootside.c/.h, rootside_proto.h, webtransport.c, sentinel.c, helper.c, authentication.c, rediscover.c, page.c, page.html, local_login.c` (`diff -q`, nessuna differenza).
  Identici anche `prove/check-ban.py` e `prove/check-package.py` (quest'ultimo e' ancora quello Debian/Ubuntu: apparmor, dpkg; NON prova il muro SELinux). `docs/SPECS.md`, `DECISIONS*.md` identici a Ubuntu:
  le decisioni D1-D8 stanno solo in `fedora45/PIANO.md` (citarle «PIANO.md D3», il registro «REGISTRO F24»).
- **Versioni vere** (`studio/1-gnome-fedora45.md:52-72`, `studio/4-lxqt:15-18`, `studio/2-kde:50`, `studio/3-xfce:68`): GNOME Shell/Mutter/GDM/gnome-session 51.0 (repo 51.1), systemd 262, dconf 51.0, polkit 127,
  PipeWire 1.6.9, Mesa 26.2.3, firewalld 2.5.2, authselect 1.8.0, selinux-policy 45.23, dbus-broker 37; Plasma/KWin 6.8.1 (sorgenti 6.8.3), plasma-login-manager 6.8.1; xfce4-session 4.20.4, lightdm;
  lxqt-session 2.4.0, lxqt-panel 2.4.1, pcmanfm-qt 2.4.1, sddm; labwc 0.20.2 (wlroots 0.20.2). libei: non letto (non verificato).
- **Pacchetto**: `remotix-1.2.0-1.fc45.x86_64.rpm`, `sudo dnf install ./remotix-...rpm`, servizio installato spento (preset Fedora `disable *`), gruppo amministratore `wheel`,
  nessun purge (in RPM `remove` fa tutto cio' che Debian fa in remove+purge: `rpm/remotix.spec` `%postun` r.~385 «an RPM has no purge»).
- **Costanti di tempo/tetto**: identiche a Ubuntu salvo `KDE_PRELOCAL_ORDERLY_MS 5000` (`session.c:113`) e `CHILD_LOCALE_MAX 12` (`child.c`):
  `diff <(grep -h '#define [A-Z_0-9]*_\(MS\|S\|NS\|MAX\|CAP\)\b' ../ubuntu26.04/src/*.[ch] | sort) <(grep -h '#define [A-Z_0-9]*_\(MS\|S\|NS\|MAX\|CAP\)\b' src/*.[ch] | sort)`.
- **Difetti del sorgente da NON ripetere nel manuale** (decisione del proprietario se correggerli o citarli com'e'): `kwin.c:814,825,842` dicono ancora «Remedy: reinstall the package (apt install --reinstall remotix)»;
  `main.c:472` dice ancora «Install the file of the family: src/remotix.pam (Debian/Ubuntu), .fedora, .suse, .arch» e parla di Fedora/Arch con `pam_deny`; `walls.h:43` cita `sudo apt`;
  `src/remotix-remote-sessions.rules` nell'intestazione dice «five actions» ma il codice ne tratta sei (4 refresh + 2 macchina); `selinux`/`session.c` conservano la chiave `ubuntu-lock-on-suspend` (`session.c:1739`).

---------------------------------------------------------------------------------------------------

# PARTE A - Manuale tecnico, ch12 `ch12_desktops.py` - «The four desktops» (11 sezioni)

### 1. The four desktops side by side - DA CORREGGERE
Tabella e testo da rifare (tutta la riga KDE e i nomi dei sapori):
- Intro: «on Ubuntu 26.04 they are the four flavours Ubuntu, Kubuntu, Xubuntu, Lubuntu» -> Fedora 45: GNOME (Workstation), KDE Plasma, XFCE, LXQt (Live 45-1.4, `PIANO.md:7`).
  Togliere «On KDE labwc is also present ... REMOTIX's own build of labwc»: su Fedora NON c'e' (D2, `rpm/remotix.spec:5`, F7).
- Colonna KDE: Compositor = «KWin 6.8 alone, `--virtual`», nessun labwc; Started by = `startplasma-wayland`, unita `plasma-kwin_wayland.service` con ExecStart
  `remotix --kwin-virtual W H -- kwin_wayland_wrapper --virtual --xwayland --width W --height H --no-lockscreen` (`session.c` `write_dropin()`, kwin.c:1702-1727; F7);
  Monitor = «single output Virtual-0 of KWin's virtual backend, resized at run time» (`kwin_output_resize()`, `kde_output_management_v2` >= 22, `kwin.c:2053`); Log Out = `org.kde.Shutdown.logout` poi `StopUnit(graphical-session.target)` (non piu' `plasma-workspace.target`: `session.c:4609`, F36).
- Colonna GNOME: «session `ubuntu`» -> `gnome` (`gnome.desktop`, `Exec=/usr/bin/gnome-session`, `DesktopNames=GNOME`; studio 1:78); unita `org.gnome.Shell@user.service` (non `@ubuntu`).
- Colonne XFCE/LXQt: «the distribution's labwc» resta vero (labwc 0.20.2, `Recommends: labwc`, spec r.~90); LXQt: `lxqt-session` 2.4.0.
- Paragrafo «Versions on Ubuntu 26.04»: riscrivere con la tabella sopra (GNOME 51.0, Plasma/KWin 6.8.1, xfce4-session 4.20.4, lxqt-session 2.4.0, labwc 0.20.2, systemd 262; display manager: gdm, plasmalogin (pacchetto `plasma-login-manager`), lightdm, sddm). Dire che sono le versioni delle VM `gnome/kde/xfce/lxqt` (ISO Live 45-1.4; i repository hanno gia' 51.1 e 6.8.3), non riletti per il manuale. Togliere i riferimenti a `studio/1-gnome50...6-kubuntu...`, REGISTRO C4/C5 e al «catalogue of an earlier multi-distribution product» solo se il testo non vale piu' (il §11.8 di DECISIONS-11 e' identico: la frase sui minimi resta vera; su Fedora tutti i desktop sono sopra i minimi).
- «One desktop per machine»: vale. Il caso «XFCE o LXQt senza il pacchetto labwc» vale (`session_missing_component()`, 0x0E) ma il «postinst also warns» diventa «`%post` of the RPM warns» (spec `%post`, blocco `labwc`); il testo dice `--no-install-recommends` -> `--setopt=install_weak_deps=False`.
- «Whose settings these are»: le quattro eccezioni valgono (file `~/.config/dconf/remotix`, `lock-warning-shown`, copia chiavi XFCE, ripristino una tantum): il codice e' identico (non verificato su Fedora che `lock-warning-shown` serva ancora: `session_gnome_lock_warning()` e' invariata, GNOME 51 non riletto).
- Da ricontare: nessun numero.
Prova: `diff ../ubuntu26.04/src/session.c src/session.c`; PIANO D2; F7; studio/5-kde-progetto.md.

### 2. How the desktop is recognised - DA CORREGGERE
- `/etc/X11/default-display-manager` NON esiste su Fedora: `active_display_manager()` (`session.c:~412-470`) ripiega sul bersaglio di `display-manager.service` (`studio/3-xfce:91`: `display-manager.service -> lightdm.service`; plasmalogin ha `Alias=display-manager.service`, studio 2:156). Riscrivere il paragrafo.
- `declared_desktop()` legge SOLO lightdm (`user-session`) e sddm (`Session` di `[Autologin]`): `session.c:468,478,3028,3098`. Con gdm o plasmalogin attivi i file di lightdm/sddm sono «leftovers» e ignorati (comportamento identico a Ubuntu per gdm3). Su Fedora le edizioni hanno UN desktop ciascuna: i casi a due desktop sono teorici. Il testo deve dire che `plasmalogin` non e' letto (verificato nel sorgente; non provato con due desktop installati).
- Mappa nome -> desktop (`desktop_of_session_name()`, `session.c:393-408`): le parole `xubuntu/lubuntu/kubuntu/ubuntu` restano nel codice ma non servono; i nomi Fedora sono `gnome`, `plasma`, `xfce`, `lxqt-wayland` o `lxqt` (studio 4:11: `strstr(n,"lxqt")` la riconosce). Togliere il paragrafo «Xubuntu has both GNOME markers» (non verificato se la Spin XFCE di Fedora porti `gnome-session`/`gnome-shell`: da `rpm -q` sulla VM xfce) e la nota su `ubuntustudio/ubuntu-budgie`.
- Tabella di riconoscimento e valori di `DesktopSession` (GNOME 0, KDE 1, XFCE 2, none 3, LXQt 4): vale (`session.h`, identico).
- `session_on_wlroots()` e predicati `e_kde()/e_xfce()/e_lxqt()`: valgono.
- Da ricontare: nessun numero.

### 3. The composed environment - DA CORREGGERE
- Tabella: riga `XDG_CURRENT_DESKTOP` GNOME = `GNOME` (non `ubuntu:GNOME`); `XDG_SESSION_DESKTOP` = `gnome` (`studio/1:164`). Riga KDE: `WLR_BACKENDS`, `WLR_RENDER_DRM_DEVICE`, `LABWC_UPDATE_ACTIVATION_ENV` «in KWin's labwc only» -> da togliere per KDE (non c'e' labwc: `kwin.c:1584` e' il ramo nested ormai irraggiungibile, `main.c:2886-2892`); resta `KWIN_FORCE_SW_CURSOR=1` (`kwin.c:1685`) e `XDG_MENU_PREFIX=plasma-`. Per KDE la scheda NON e' scelta da REMOTIX (`session.c` commento D2: «KWin picks its own render device»), quindi il paragrafo «The render node» vale solo per XFCE/LXQt.
- Nuove variabili Fedora: `LANG` dalla scelta dell'utente in AccountsService (`Languages=`/`Language=`, letta da root prima di `setuid()`), poi `LC_*`/`LANGUAGE` di sistema da `/etc/locale.conf` (F34, F35: `child_locale_read()`, `CHILD_LOCALE_MAX 12`, `session.c` nuovo ciclo `LC_`/`LANGUAGE`; OUR_VARIABLES ora include `LANGUAGE, LC_CTYPE ... LC_ALL`). Va detto che senza codifica in AccountsService (es. `it_IT`) il comportamento e' dichiarato aperto (`PIANO.md:458-461`). Aggiungere come NUOVA sezione/paragrafo (vedi (a)).
- «The PATH is the one PAM gives to a login»: su Fedora NON esiste `/etc/environment` (F4, F34); `child_path_ok()` ricade sul fisso `/usr/local/bin:/usr/bin:/bin` (+ `bin-lxqt` su LXQt) e NON ha `~/.local/bin` ne' `~/bin` (differenza dall'accesso locale, dichiarata, decisione del proprietario D3 di F22). Togliere `/snap/bin`, giochi. `src/remotix.pam` ha le DUE righe `pam_env` (`envfile=/etc/locale.conf`).
- «The session's own folders» (D-153, `/etc/X11/Xsession.d/60x11-common_xdg_path`, `/etc/profile.d/xdg_dirs_desktop_session.sh`, `/etc/xdg/xdg-<name>`, `/usr/share/<name>`): su Fedora NON esistono (studio 3:160, studio 4:151, studio 1:128; su Fedora `/etc/X11/Xsession.d/` ha solo `90xbrlapi`). Il paragrafo si riduce a: «`local_session()` non trova nulla e non aggiunge cartelle; i default Fedora arrivano da gschema override e da `/etc/xdg`». Non verificato il log D-153 su Fedora.
- Da ricontare: nessuna cifra (la lista delle variabili si rilegge con `grep -n 'OUR_VARIABLES' -A12 src/session.c`).

### 4. How a session is born - DA CORREGGERE
- «The logind session»: la frase «This tree is born with systemd 259.9» -> systemd 262 (la logica pidfd da 258 resta vera, `child.c`); «freshly installed Ubuntu 26.04» -> Fedora 45. Il `pam_start` col servizio `remotix` ora attraversa lo stack `password-auth`/`postlogin` di Fedora (vedi ch13 S2) e `pam_selinux open env_params`: aggiungere che il contesto d'exec dell'utente e' deciso da `selinux_exec_like_local_login()` e riletto da `selinux_exec_checked()` subito prima dell'`execve`; rifiuti 44-47 «⛔ SELinux ...: the login is REFUSED» (`child.c`, F5/F25). Nuovo paragrafo: vedi (a).
- Passo 2 «Drop-in»: istanza `org.gnome.Shell@user.service.d` (non `@ubuntu`); su KDE «KWin's unit» ha il drop-in con `--kwin-virtual` e `Environment=REMOTIX_KDE_HOST=1` (`session.c` `write_dropin()`).
- Passo 3 «Guards» e `inactive_unit()` per GNOME: tre unita invariate (`gnome-session-manager@<session>.service`, `gnome-session-restart-dbus.service`, `graphical-session.target`); su Fedora `@gnome` (studio 1:3.1). Per KDE `inactive_unit()` controlla ora `graphical-session.target` oltre a `plasma-workspace.target` (`session.c:4491-4557`).
- Tabella «The command that starts each desktop»: GNOME = `/usr/bin/gnome-session` (sessione `gnome`: `gnome_session()` sceglie «the upstream GDM default», non «bears the distribution's name»; il log dice cosi', studio 1 §3.5 punto 4); KDE = `exec startplasma-wayland` (invariato); XFCE `labwc -m --session '<primary>'`; LXQt `labwc -C <folder> -S '<primary>'` (non verificato che la riga Fedora sia identica per LXQt: F22 dice «nessuna opzione da cambiare»).
- «The primary client and the size race» (wlr-randr, 1280x720): vale (labwc 0.20.2: `wlr-randr --custom-mode` funziona, F22). Le cifre «1 birth in 13» sono di Ubuntu e vanno tolte o marcate «misurate su Ubuntu».
- Da ricontare: `BIRTH_REIN_MS`, `STAGE_BIRTH_RETRY_MS`, `WAIT_STARTUP_MS` (costanti invariate: comando sopra).

### 5. Ending a session and tidying up - DA CORREGGERE
- Tabella «How each desktop is asked to end»: GNOME fatto-decisivo `@gnome` (non `@ubuntu`). KDE: forza = `StopUnit(graphical-session.target, "fail")` (non `plasma-workspace.target`) e fatto decisivo `plasma-kwin_wayland.service` + `plasma-workspace.target` + `graphical-session.target` (`session.c:4609`, `4491-4557`; F36).
- Sottosezione «KDE: a Log Out that stops halfway»: riscrivere. Il testo e' misurato su Plasma 6.6 (Kubuntu); su Plasma 6.8 il codice `session_kde_logout_watch()` e le costanti `KDE_LOGOUT_GRACE_MS 4000`, `RETRY 3000`, `TRIES 10` esistono invariate (`session.c:5183-5187`) ma l'effetto «plasma-shutdown non ferma il target» su 6.8 e' NON verificato; il fatto nuovo e' F36 (25 nov): la chiusura forzata ferma `graphical-session.target` perche' kwin, ksmserver, plasmashell sono `PartOf=` esso e `plasma-workspace.target` da solo lo fa sparire ~4,5 s dopo (StopWhenUnneeded), oltre la scadenza del lato root; ora ferma tutto in < 0,6 s. Aggiungere `KDE_PRELOCAL_ORDERLY_MS 5000` (`session.c:113`, usato in `wait_until_done_ms(force_guard_on ? KDE_PRELOCAL_ORDERLY_MS : WAIT_EXIT_MS)`): in una chiusura da «accesso locale in attesa» su KDE il passo ordinato aspetta 5 s invece di 10 (decisione del proprietario, 25 nov, «una prova»). Provato a mano: forzata a 5,04 s, gancio liberato 5,9 s, 0 rifiuti SELinux, 0 core dump (PIANO.md:446-450).
- «The farewell is said before the stage is dismantled», `session_life()` a tre risposte, `EIS_UNKNOWN_ROUNDS 3`: codice invariato, valgono. Il riferimento a «rtkit-daemon ... (Ubuntu 26.04 box, 18 Nov)» e' misura di Ubuntu: marcarla tale.
- «What is left in the user manager»: la lista `OUR_VARIABLES` ha ora anche le variabili di lingua (vedi S3). Le quattro variabili «only with GNOME 50» (`GNOME_DESKTOP_SESSION_ID`, `QT_IM_MODULE`...) sono misure Ubuntu: GNOME 51 non riletto (non verificato).
- F16 (da sapere): alla chiusura forzata da fuori i programmi di sfondo KDE (`kded6, plasmashell, kaccess...`) abortiscono (27 file in 25 s sulla VM kde, `coredumpctl`); con Log Out normale 0. Dopo F36 il quadro e' cambiato: `PIANO.md:458-461` elenca ancora «programmi lenti a chiudersi su KDE». Aggiungere come limite dichiarato (vedi (a)). Il numero 27 e' di una misura precedente a F36: non ricontato.
- «Known limit» E3 (snapshot vecchio, `session_alive` = closed in due punti): vale (codice invariato).
- Da ricontare: `CLEAR_OUT_EXIT_WAIT_MS`, `WAIT_EXIT_MS`, `CHECK_INTERVAL_MS` (comando delle costanti).

### 6. GNOME: headless Shell and session dconf - DA CORREGGERE
- Sottosezione «The session on Ubuntu 26.04» passo 1: sessione `gnome` (`gnome.desktop`, `X-GDM-CanRunHeadless=true`), `XDG_CURRENT_DESKTOP=GNOME`; togliere l'argomento «Ubuntu's defaults are gschema overrides keyed to `ubuntu`»: su Fedora i default arrivano dagli override gschema di Fedora e sono di serie nella sessione remota (studio 1:6, `10_org.gnome.desktop.background.fedora.gschema.override`...). Passo 2: istanza `org.gnome.Shell@user.service` (`gnome-session@gnome.target` la richiede; `unit_shell()` la trova, studio 1:3.2). Passo 3-4: `--mode=%i` = `user`. Passo 5 (Mutter via D-Bus, libei): vale con Mutter 51 (`DisplayConfig.GetCurrentState` stessa firma, studio 1:226).
- «The Ubuntu mode and its extensions» (`ubuntu.json`, dock, ding, snapd-prompting...): DA TOGLIERE. Su Fedora e' il modo `user`, nessuna estensione di Ubuntu. Non verificato quali estensioni di Fedora (nessuna di serie in Workstation 45, da `gnome-extensions list` sulla VM).
- «Leaving and coming back»: le cifre (48/48 tentativi, 1,5-2,9 s) sono di Ubuntu: togliere o attribuirle a Ubuntu. Su Fedora: GNOME chiusura ordinata nel giro finale `h1`, `check-lifecycle` PASS (PIANO.md:316-320); numero di tentativi non verificato.
- «The session is born in the Overview, and without the lock notice»: Overview su GNOME 51: non verificato. `lock-warning-shown`: codice identico, effetto su GNOME 51 non rimisurato.
- «The session's dconf (D-015)»: il modello (tabella `Keyfiles` / `System database` / `Runtime profile` / `Session database`, fallback a due livelli, ripristino una tantum, verifica) VALE: `session.c` identico tranne la compilazione. Correzioni: (1) «Why the model changed ... C5 ... Flutter ... snap» e' storia di Ubuntu (snap e programmi Flutter di Ubuntu): su Fedora non ci sono (non verificato che nessun programma Flutter/snap sia nella Workstation); riscrivere il perche' come «il modello e' quello di Ubuntu, scelto per uniformita', provato su dconf 51 (studio 1 §6)». (2) La riga `System database`: il servizio compila in `/run/remotix/dconf-compile.tmp` (tipo SELinux nostro) e crea in `/etc/dconf/db` solo due nomi fissi `remotix.new` poi `remotix`, con transizione di tipo per nome verso `remotix_dconf_db_t` (`session.c` hunk WORK/NEWDB, `selinux/remotix.fc:8`, F24); NON piu' `remotix.new.<pid>` ne' pulizia dei `remotix.new.*`. (3) «Compiled by the postinst» -> `%post` dell'RPM (compila in `remotix.new.$$` poi `mv`, spec `%post`; rimosso da `%postun`); il comando `dconf` sta nel pacchetto `dconf` (non c'e' `dconf-cli`, studio 1:6; `Recommends: dconf`). (4) «Base profile»: su Fedora `/etc/dconf/profile/user` ha 4 righe `user-db:user, system-db:local, system-db:site, system-db:distro` (studio 1:6), quindi il log NON dira «base profile: user-db:user» alone e il profilo di runtime avra `system-db:remotix`, `user-db:remotix` e poi le tre `system-db` di Fedora. (5) Tabella dei tasti: `ubuntu-lock-on-suspend` e' una chiave di Ubuntu: su Fedora `schema_has_key()` la salta in silenzio (`session.c:5745-5789`), quindi «24 chiavi, 21 con valore» diventa verosimilmente 20 con valore in `session_dconf_verify()` (non verificato: leggere il log «session keys re-read» sulla VM). (6) Commenti con «dconf 0.40/0.49» -> dconf 51.0, stesso meccanismo (studio 1:6, sorgente `dconf-51.0/engine/dconf-engine-profile.c`).
- «Known limits»: valgono; il limite «hot upgrade ... never distributed on Ubuntu» va riscritto («il modello non e' mai stato distribuito su Fedora in altra forma»). La riga sul `purge` diventa «`dnf remove` rimuove `~/.config/dconf/remotix` come l'utente, solo quel file regolare» (spec `%postun`, `runuser`, `rm -f`).
- Scala `scaling-factor`: vale (`mutter_scale_to_one()`, misura `mutter.h` 14 ago); non rimisurata con Mutter 51 (non verificato). Fatto nuovo Fedora (F34): il primo movimento assoluto su GNOME arriva con una coordinata a 0 (bug di mutter 51.0): `input.c` manda il primo movimento due volte (`pointer_primed`); aggiungere in S11 e (a).
- Inhibition: `session_inhibit()` invariato.
- Da ricontare: «24 keys, 21 with value» -> `sed -n '1723,1745p' src/session.c | grep -c '{ "org'` + `grep -c 'switch-to-session' src/session.c` (le 12 chiavi `switch-to-session-N` sono generate a ciclo; non ho un conteggio verificato).

### 7. KDE Plasma: KWin nested in labwc - DA RISCRIVERE
Tutta la sezione descrive l'architettura Ubuntu (KWin annidato in un labwc nostro). Su Fedora (D2, F7, `studio/5-kde-progetto.md`):
- Nuovo titolo suggerito «KDE Plasma: KWin alone». Contenuto vero: il drop-in di `plasma-kwin_wayland.service` esegue `remotix --kwin-virtual W H -- kwin_wayland_wrapper --virtual --xwayland --width W --height H --no-lockscreen`; `remotix --kwin-virtual` (`kwin_virtual_alive()`, `kwin.c:1721`) avvia SOLO il sidecar `org.freedesktop.ScreenSaver` (`screensaver_alive()`, `kwin.c:1481`, doppia fork) e poi fa `exec` del wrapper. `--kwin-nested` risponde errore 2 (`main.c:2886-2892`). `Environment=REMOTIX_KDE_HOST=1` + opzione `--kwin-virtual` sono il doppio segno «questo KWin e' di REMOTIX» (`kdehost.h`).
- Togliere: figura KDE_FIG, «Our own labwc (KDE)», tabella «Why KWin runs inside labwc», «The start line» a 7 passi, tabella «Traps of KWin inside labwc» (ticker 16 ms, 240 Hz, pixel trasparente, `kwin_host_settle` come descritto), regole labwc `rc.xml`. NB: il codice labwc di `kwin.c` (`kwin_nested_alive()`, `kwin_host_*`, `HOST_BIRTH_MS`...) e' ancora presente ma irraggiungibile («da togliere dopo le prove del proprietario», F7): il manuale NON deve descriverlo come funzionante.
- Da dire (vero): il cambio di dimensione e' a caldo nel prodotto: `kwin_output_resize()` (protocollo `kde_output_management_v2` >= 22, modo personalizzato `add_cvt`, ~3 ms, anche misure dispari; F7); se KWin e' piu' vecchio di 6.8 la sessione e' RIFIUTATA con un messaggio chiaro, nessun ripiego silenzioso (F7). Lo stream non segue il cambio: si smonta, si cambia l'uscita, si rimonta (invariato). Ma il manuale di ch03 vale: il prodotto chiede la misura solo alla nascita e al riaggancio, ridimensionare la finestra non cambia il desktop (F14).
- F8: KWin ricorda l'ultimo modo di `Virtual-0` in `~/.config/kwinoutputconfig.json` (file di KWin, mai toccato); `--width/--height` valgono solo la prima volta; il figlio verifica la misura e la corregge prima di montare lo stream.
- F12: piu' schede grafiche con KWin da solo: non provabile sul banco (KWin sceglie da se' il dispositivo): limite dichiarato. F13: KWin non risponde / non accetta la misura (comportamento del prodotto in F13).
- «The ScreenSaver sidecar» (Ctrl+Alt+Del su Plasma >= 6.4): VALE com'e' (`screensaver_alive()` identico; misure su 6.6.7: su 6.8.1 non rimisurato, non verificato). «The lost frame» (`kwin_poke()`, `capture_watch_sequence()`): vale, il rimando a ch06 resta (`kwin.c:595`, `child.c:12562`).
- «Capture, input, cursor and clipboard»: `kwin_check_permission()` e `org.kde.remotix.desktop` (RX-KDE-001/002/003): valgono; il file e' `rpm/org.kde.remotix.desktop` (in `/usr/share/applications`). Nota «Remedy text»: il messaggio dice ancora `apt install --reinstall remotix` (`kwin.c:814,825,842`): difetto del sorgente; il manuale deve dire `sudo dnf reinstall remotix` come azione reale e annotare il testo del messaggio.
- Plasma Setup (wizard del primo avvio, `plasma-setup.service`): non gira in remoto (non verificato) - studio 2:224.
Prova: PIANO D2; REGISTRO F7, F8, F12, F13, F14, F36; `studio/5-kde-progetto.md:1-40`; `diff ../ubuntu26.04/src/kwin.c src/kwin.c`.

### 8. XFCE: labwc and a locked xfconf - DA CORREGGERE
- Intro: «labwc 0.9.3 on Ubuntu 26.04» -> labwc 0.20.2 (wlroots 0.20.2); verificato: `-m`, `-S`, `-C`, `rc.xml` nostro, `wlr-randr --custom-mode` funzionano senza modifiche (F22). «The Xubuntu panel has the whisker menu and no `actions` button (study 7)»: su Fedora XFCE e' un'altra build (pannello con Applications, orologio, utente e un dock in basso, F22); la frase su whisker/actions e' da rifare o dichiarata non verificata (il codice blocca whisker e `actions` solo se presenti: invariato).
- Tabella «How XFCE is kept»: `xfce4-session` 4.20.4: la cintura `XFCE4_SESSION_COMPOSITOR` vale (stessa logica nel sorgente 4.20.4, studio 3:157). «Autostart cover» `blueman.desktop`: su Fedora la lista e' invariata e contiene solo `blueman.desktop` (`session.c:3268`); `abrt-applet`, `dnfdragora-updater`, `nm-applet`, geoclue agent NON sono coperti (F33 punto 2, studio 3:211) e dopo il Log Out nessun processo resta (check-lifecycle/check-exit PASS, F22). Non verificato che `blueman` sia installato su Fedora XFCE (da `rpm -q blueman`).
- Tabella chiavi `XFCE_LOCKS` e sintassi `locked="<user>"`: invariato; il commento «Ubuntu 26.04 has xfce4-session 4.20.4 and the measurement was not repeated» -> Fedora ha 4.20.4-2, misura non ripetuta (non verificato).
- Nota «Black wallpaper» (E1, libxfce4windowing 4.20.2): DA RISCRIVERE come limite dichiarato D7: su Fedora il fondo e' nero pieno e senza icone, causa strutturale «`xfdesktop was not built with Wayland support`» (xfdesktop 4.20.2-2, libxfce4windowing 4.20.7), NON la causa E1; pannello e dock ci sono (F22). Nessun rimedio nel codice (PIANO D7). Altro limite aperto: F30, XFCE con utente SELinux `staff_u`: il pannello non parte (non nostro).
- Il resto (copia e ripristino delle chiavi, `xfce_panel_integrity()`, `xfconfd_holds_lock()`): codice invariato, vale; i file di stato `~/.local/state/remotix/xfce-chiavi` sono rimossi da `%postun` (nome incluso).
- Da ricontare: nessuna cifra.

### 9. LXQt: labwc folder and session commands - DA CORREGGERE
- Intro: «lxqt-wayland-session 0.3.1, Lubuntu does not install it» -> su Fedora `lxqt-session` richiede `lxqt-wayland-session` (hard) con sottopacchetti `lxqt-miriway-session`, `lxqt-labwc-session` ecc. (studio 4:40, F19); REMOTIX NON li usa e avvia labwc da se' come su Ubuntu (`labwc -C <folder> -S`). Versione `lxqt-session` 2.4.0. Il compositor locale e' `miriway` (greeter di sddm), non `labwc`.
- Tabella: «X11 composition managers» (`picom/compton/xcompmgr`) e «Programs that count every user's processes» (`lubuntu-update`) sono cure specifiche di Lubuntu: il codice le conserva, ma su Fedora `picom`/`lubuntu-update` non esistono (non verificato con `rpm -q picom`); riscrivere come «scritte solo se il programma esiste». Aggiungere cio' che su Fedora esiste e NON e' coperto: `dnfdragora-updater`, `nm-applet`, `geoclue demo agent` partono nella sessione remota (studio 4 punti 9-10; F22: spariscono tutti al Log Out; F33: scelta «come Ubuntu», non nascosti).
- «Menu entries», «Idleness», «Environment» (`XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots`), «Exit», «one-time restore»: valgono (codice invariato). `qlipper` non c'e' su Fedora: gli appunti passano per data-control di labwc (`check-clipboard` 2/2, F22).
- Cartelle di sessione (`/etc/xdg/xdg-Lubuntu`...): non esistono (studio 4:96,151); il `panel.conf` di sistema sta in `/etc/xdg/lxqt/panel.conf`, non `/usr/share/lxqt/` (F22: errore del banco corretto; il prodotto usa solo il file dell'utente).
- Chiusura di LXQt: `exit_lxqt()` provata: chiusura ordinata 0,7 s dall'accesso locale (PIANO.md, prove a mano del 25 nov); la misura «Log out ... 16 volte su 20» era di un albero precedente.
- Da ricontare: nessuna cifra.

### 10. What the session imposes, desktop by desktop - DA CORREGGERE
- Riga GNOME: le chiavi (24 totali, 21 con valore) e `ubuntu-lock-on-suspend`: vedi S6 (su Fedora una in meno in vigore, non verificato). Percorsi `/etc/dconf/db/remotix` ecc: validi (tipo SELinux `remotix_dconf_db_t`).
- Riga KDE: invariate le restrizioni KIOSK (`[KDE Action Restrictions][$i]` `session.c:1539`), `--no-lockscreen`, sidecar, inibizione powerdevil; il drop-in e' quello di `--kwin-virtual`.
- Paragrafo «KDE's powerdevil inhibition»: `powerdevil_guard()` invariato; il drop-in `AllowSuspend=no` e' installato spento in `/usr/share/remotix/belts/` (`rpm/remotix-no-suspend.conf`, spec) come su Ubuntu.
- Riga LXQt: cure di Lubuntu (vedi S9). Riga XFCE: valida.
- Da ricontare: «six entries» LXQt (`lxqt_session_commands()`), «n/6 entries hidden»: invariato.

### 11. Behaviours of the four desktops worth knowing - DA RISCRIVERE
La tabella e' tutta del registro D/E di Ubuntu (Kubuntu 18 nov, Xubuntu 17-18 nov, Lubuntu, E1-E4). Per Fedora riscrivere dalle voci F:
- GNOME: primo movimento a coordinata 0 (F34, mutter 51.0; cura: primo movimento inviato due volte, `input.c`, «da togliere quando Mutter sara' corretto»); pkexec dalla sessione remota: `SHELL` vuoto, FAIL noto («gnome 52 PASS (FAIL pkexec noto)», PIANO.md:316) - comune a Ubuntu; `avc { view }` di `xdm_t/gdm-session-worker` su `stratisd_t` (F15, non nostro, non osservato); portachiavi `oo7`: `pam_oo7` non e' nello stack di REMOTIX, la collezione `login` resta bloccata (D6, studio 1 §7) - limite dichiarato.
- KDE: chiusura forzata con programma che non si chiude (F36, risolta); programmi lenti a chiudersi su KDE e chiusura per abbandono su KDE non verificata (PIANO.md:458-461); core dump dei programmi KDE alla chiusura forzata (F16); KWin ricorda `Virtual-0` (F8); piu' schede grafiche (F12).
- XFCE: fondo nero e niente icone (D7, F22); utente `staff_u`: pannello non parte (F30); Log Out nei primi secondi rifiutato da XFCE («must be at rest», E-voce di Ubuntu, stesso codice 4.20.4: vale anche qui, non rimisurato su Fedora - non verificato).
- LXQt: nessuna cosa nota specifica oltre `dnfdragora-updater`/`nm-applet` (S9).
- Tutti: SELinux enforcing, AVC nostri 0 nel giro `h1`; `giro-selinux.sh` nasconde un controllo morto a meta' (`check-kde-exit` «service restart», intermittente: PIANO.md:458-461). E4 (scatti di Chrome su Android) e' di Ubuntu: non rimisurato, togliere o dichiarare «non provato su Fedora».
- Ultimo paragrafo «The AppArmor profile ...» -> «Il modulo SELinux ...» (`rif` da rinominare). L'elenco «Places that differ per desktop» resta valido, con `kwin_virtual_alive()` al posto di `kwin_nested_alive()`.
- Da ricontare: nessun numero (le cifre dei giri vanno prese dal giornale: PIANO.md:316-320, non dai log: non verificato).

---------------------------------------------------------------------------------------------------

# PARTE B - Manuale tecnico, ch13 `ch13_login.py` - «Login and its defences» (10 sezioni)

### 1. The path of one login attempt - DA CORREGGERE
- Riga 5 della tabella (PAM modules): `common-auth`, `common-account`, «`pam_faillock` ... the module is in Ubuntu 26.04's PAM package, but no line enables it in the stock `common-auth`» -> Fedora: stack `password-auth` (link in `/etc/authselect`, riscritto da authselect) e `postlogin`; `pam_faillock` solo se l'amministratore attiva la funzione `with-faillock` del profilo authselect; NON attivo di serie (profilo `local` con `with-silent-lastlog with-mdns4`, studio 1 §9.1; la ban table di REMOTIX e' l'unica difesa).
- Il resto (5 passaggi, invariante I3, `0x05` locale esclude remoto, nota `--split`): vale (codice identico). `rif("The local-login hold")`: titolo da tenere.
- Prova: `src/remotix.pam` (Fedora); studio 1:9.1.

### 2. The PAM service file remotix.pam - DA RISCRIVERE
Il file Fedora e' un'altra cosa (`diff ../ubuntu26.04/src/remotix.pam src/remotix.pam`):
- E' `/etc/pam.d/sshd` di Fedora riga per riga con UNA riga in piu' in testa (root escluso con `pam_listfile ... file=/etc/remotix/denied-users onerr=fail`). Stack veri: `auth substack password-auth` + `auth include postlogin`; `account required pam_sepermit.so`, `required pam_nologin.so`, `include password-auth`; `password include password-auth`; `session required pam_selinux.so close`, `pam_loginuid.so`, `pam_selinux.so open env_params`, `pam_namespace.so`, `optional pam_keyinit.so force revoke`, `optional pam_motd.so`, `include password-auth`, `include postlogin`, e le DUE righe `pam_env` (una senza file, una `envfile=/etc/locale.conf`). NON c'e' `@include` ne' `common-*` (estensione Debian).
- Installato da `%config(noreplace) /etc/pam.d/remotix` (non «dpkg conffile»); `pam_systemd` arriva da `password-auth` (`-session optional pam_systemd.so`). Intestazione del file: «FEDORA 45 ONLY» (corretta, a differenza di Ubuntu che diceva DEBIAN 13).
- Se il file manca: `other` su Fedora = `pam_deny` (ogni password giusta rifiutata): le due protezioni `look_pam_service()` e `why_no()` valgono; il testo runtime di `main.c:472` cita ancora «Install the file of the family ... .fedora, .suse, .arch»: difetto del sorgente (vedi fatti-base); l'azione per l'amministratore Fedora e' `sudo dnf reinstall remotix`.
- SELinux: le due `pam_selinux` funzionano perche' il server gira in `remotix_t` (`selinux/remotix.te`); senza modulo l'exec e' rifiutato (AVC `transition`). Portachiavi: NIENTE `pam_gnome_keyring`/`pam_oo7`/`pam_kwallet` (D6) perche' autenticazione e apertura sessione sono due handle PAM in due processi.
- Il paragrafo «The other PAM line the package adds» (pam-auth-update, `/usr/share/pam-configs/remotix`, `Session-Interactive-Only`): DA TOGLIERE. Sostituire con `remotix-pam-hook` (vedi ch14 S6). Il confronto «15 righe di 15 con sshd» e le misure di Ubuntu: togliere; per Fedora non c'e' un confronto riga-per-riga misurato in questa sede (il file e' scritto copiando `/etc/pam.d/sshd`, F2) - non verificato con `diff` sulla VM.
- «Stale text» nota: riscrivere (il testo stantio e' in `main.c:472` e `kwin.c`).
- `PAM_RHOST`/`PAM_TTY`: vale. Motivo «why not login»: vale (`pam_securetty` ecc.: su Fedora `login` e' lo stack console; non letto il contenuto di `/etc/pam.d/login` Fedora).
Prova: `src/remotix.pam`; F2; studio 1 §3.5 punto 1, §9.1.

### 3. One PAM transaction in authentication.c - DA CORREGGERE
- Codice identico (`authentication.c`): la tabella dei tre valori e la lista dei dettagli valgono. Da toglier/cambiare: «The stock Ubuntu 26.04 `common-auth` with `libpam-sss` has `pam_unix.so nullok` followed by `pam_sss.so use_first_pass`» -> su Fedora `password-auth` generato da authselect: `nullok` e' presente nel profilo `local` standard (non verificato il contenuto di `password-auth`; da `cat /etc/authselect/password-auth` sulla VM); `PAM_DISALLOW_NULL_AUTHTOK` serve comunque. Il confronto col caso `pam_faillock`: la riga «The locked judgement ... FAILLOCK_LOCKED» e' vera solo se l'amministratore abilita `with-faillock` (non di serie, studio 1 §9.1).
- Da ricontare: «more than 16 messages» (costante in `authentication.c`): `grep -n 'RCP_PAM_CONV_MAX\|16' src/authentication.c`.

### 4. The PAM helper: dispatcher and grandchild - DA CORREGGERE
- Codice identico (`helper.c`); tutte le costanti valgono. Correggere solo: «these times were not measured on Ubuntu 26.04, where `pam_sss` and `pam_motd` may add their own» -> «non misurati su Fedora 45» (non verificato; `check-ban.py` identico, tempi su Fedora non registrati nel giornale).
- Da ricontare: `MAX_IN_FLIGHT 16`, `RESERVED_FOR_KNOWN 2`, `EXPIRY_MS 8000`, `GRANDCHILD_ALARM_S 20`, `RESTART_*`: `grep -n 'define MAX_IN_FLIGHT\|RESERVED_FOR_KNOWN\|EXPIRY_MS\|GRANDCHILD_ALARM_S\|RESTART_FIRST_MS\|RESTART_CAP_MS\|STABLE_MS\|LOUD_AFTER' src/helper.c`.

### 5. The fixed answer time and the floor of a refusal - DA CORREGGERE
- Tabella e logica identiche (`rcp.c`: `FIXED_DELAY 1000`, `REJECT_FLOOR 2500`, `VERDICT_CAP 12000`): valgono (da ricontare con `grep -n 'FIXED_DELAY\|REJECT_FLOOR\|VERDICT_CAP' src/rcp.c`).
- Paragrafo «This matters on Ubuntu: `/etc/nsswitch.conf` has `passwd: files systemd sss`»: Ubuntu. Fedora Workstation: `passwd: files systemd` (non verificato; con authselect `sssd` diventa `files sss systemd`). Il comportamento `user_refused_as()` / `RXR_NO` vale sempre.
- «The check check-ban.py ... Its individual times on Ubuntu 26.04 were not read»: riscrivere «non letti su Fedora»; la frase `10.0.2.2` (rete utente QEMU) e' del banco Ubuntu: sul banco Fedora i client appaiono come l'host del bridge (non verificato).
- La misura `pam-tempi` (2,0-2,2 s) e' di Debian: mantenere ma attribuirla a Debian; tempo del PAM Fedora non misurato.

### 6. The three counters and the progressive ban - VALE COM'E'
Codice identico (`rcp.c`, `rcp.h`, `--ban-file /var/lib/remotix/net/ban`, mode 0600, owner `remotix`). Il file di ban e' creato da `remotix.tmpfiles` (`z /var/lib/remotix/net/ban 0600 remotix remotix`) e ha tipo SELinux `remotix_net_state_t` (`selinux/remotix.fc:6`): aggiungere solo se si vuole. Da ricontare: `LIMIT[]`, `WINDOW_MS[]`, `LADDER_MS[]`, `FORGET_MS`, `MAX_ATTEMPTS 256`, `BAN_QUOTA 160`, `UNKNOWN_LIMIT`: `grep -n 'LIMIT\[\]\|WINDOW_MS\[\]\|LADDER_MS\|FORGET_MS\|MAX_ATTEMPTS\|BAN_QUOTA\|UNKNOWN_' src/rcp.c`.

### 7. The root side's own bounds on logins - VALE COM'E'
`rootside.c/.h`, `rootside_proto.h` identici. Da ricontare: `RXR_AUTH_IN_FLIGHT_MAX`, `RXR_AUTH_PER_S`, `RXR_AUTH_BURST`, `ROOTSIDE_LOGIN_*`, `RXR_GRANT_LIFE_MS`: `grep -n 'RXR_AUTH\|ROOTSIDE_LOGIN\|RXR_GRANT_LIFE_MS' src/rootside.h src/rootside_proto.h`. Il testo su `/etc/remotix/denied-users` e `pam_listfile`: vale (`rpm/denied-users` contiene `root`).

### 8. No administrator unblock, by design - VALE COM'E'
`command.c`, `check-ban.py` identici; l'unita Fedora (`rpm/remotix.service`) non passa `--command-socket`; `REMOTIX_OPTIONS` in `/etc/remotix/remotix.conf.d/*.conf` vale (`rpm/remotix.conf`). La nota sul testo di `SPECS.md` che descrive ancora un unblock: vera (SPECS identico). Il `rif("Appendix C")` da tenere.

### 9. What the login logs and what it never logs - DA CORREGGERE
- Tabella e regole: valgono (codice identico). Corregge solo il `warn`: «on Ubuntu with `libpam-sss` `pam_sss` is a second such module» -> su Fedora i moduli che scrivono il nome sono quelli di `password-auth` (`pam_unix`; `pam_sss` solo con authselect `sssd`; `pam_faillock` se abilitato). Non verificato quali righe scriva `pam_unix` nel journal Fedora (`journalctl -b -g 'pam_unix'` sulla VM).

### 10. Login defences against SPECS - VALE COM'E'
Il confronto codice/SPECS dipende da file identici a Ubuntu (`rcp.c`, `rootside.h`, `SPECS.md`, `DECISIONS-11.md`, `check-ban.py`): ogni riga e' ancora vera. Nessun riferimento a Ubuntu. Da ricontare: i numeri della tabella (stesso comando della S6/S7).

---------------------------------------------------------------------------------------------------

# PARTE C - Manuale tecnico, ch14 `ch14_security.py` - «Security model» (10 sezioni)

### 1. Trust boundaries and the processes of the service - DA CORREGGERE
- Figura: la scatola «Walls + AppArmor» -> «Walls + SELinux (remotix_net_t)».
- Tabella «Is confined by»: Network side = walls di `walls.c` + dominio SELinux `remotix_net_t` (non AppArmor, non «complain mode»: SELinux e' enforcing, F24). Root side: NON piu' «Nothing: no profile»: gira nel dominio `remotix_t` (programma di login come sshd, `auth_login_pgm_domain`), non `unconfined`; ogni diritto e' commentato in `selinux/remotix.te`; resta largo (F27: login, transizione verso ogni dominio utente non privilegiato, `sys_admin/net_admin/mount` per le stanze private, faccende nel gestore utente, scrittura `/etc/dconf/db` per due nomi, bind di porte non riservate). Per-user child: domini dell'utente come un accesso locale (`unconfined_t` per utenti normali, `staff_t`/`user_t` per utenti confinati, F25).
- «Runs as: ... `remotix.sysusers`»: vale (`rpm/remotix.sysusers`: `u remotix - "REMOTIX network side" / /usr/sbin/nologin`). L'ultimo paragrafo (`sudo apt install` in un desktop remoto) -> `sudo dnf install` (cosmetico; `walls.h:43` dice ancora `sudo apt`).
- Aggiungere il terzo dominio `remotix_hook_t` (hook del login locale, `selinux/remotix.te:15-16`).
Prova: `selinux/remotix.te:1-30`; F24-F27.

### 2. The closed list between the network side and the root side - VALE COM'E'
`rootside_proto.h`, `rootside.c` identici: messaggi, dimensioni esatte, `SCM_CREDENTIALS`, grant 30 s, limiti di `CLOSE_ORPHAN`. Da ricontare: `RXR_VERSION` (3), `RXR_GRANT_LIFE_MS`, `ROOTSIDE_ORPHAN_*`, il codice 110 di `RXR_LOCAL_COMING`: `grep -n 'RXR_VERSION\|RXR_LOCAL_COMING\|ROOTSIDE_ORPHAN\|RXR_GRANT_LIFE_MS' src/rootside_proto.h src/rootside.h`.

### 3. The walls of the network side - DA CORREGGERE
- Tabella: riga 2 «AppArmor profile, entered ... `/proc/thread-self/attr/apparmor/exec`» -> «SELinux domain: the root side's fork writes `system_u:system_r:remotix_net_t:s0` in `/proc/thread-self/attr/exec` before the `execve` (`selinux_exec_in()`, `walls.c` hunk «Fedora (step 5)»; `WALLS_SELINUX_EXEC`, `WALLS_SELINUX_NET_TYPE`). Stesso comportamento di AppArmor: protezione spenta (`/sys/fs/selinux/enforce` assente) = nota «SELinux: off» e si prosegue; attiva ma root side non in `remotix_t` o dominio non nel criterio (EINVAL) = «⚠» e si prosegue; caricato e scrittura RIFIUTATA = -1, network side non avviata». Nota: il contesto nuovo tiene utente e ruolo del lato root e il livello basso.
- Righe 1,3-9 (pidns, mount read-only, /tmp e /dev privati, netns, capability, `NO_NEW_PRIVS`, Landlock ABI 6, seccomp): valgono (stesso codice). Riga 8: la misura «landlock ABI 8, kernel 7.0.0-44» e' delle VM Ubuntu: kernel e ABI Landlock di Fedora 45 NON verificati (`log` sul server `/media/REMOTIX-FEDORA/...`, non letti).
- Paragrafo «`check-package.py` (first-start) confirms the process layout ...»: `prove/check-package.py` di Fedora e' identico a quello Debian (AppArmor, dpkg): NON e' la prova del muro Fedora. La prova negativa del muro e' `prove/wall-selinux.sh` + `wall-neg-domain.py` (21 tentativi vietati, come root con tutte le capability in `remotix_net_t`; passa solo se rifiuto E AVC dentro la finestra) e `wall-sesearch.sh` (F24, F33 J); da ricontare: «21 tentativi» = `grep -c` nella tabella del probe (non ricontato).
- Paragrafo «What Ubuntu's AppArmor sysctls do not touch» (`apparmor_restrict_unprivileged_userns`): DA TOGLIERE. Su Fedora non c'e'. Il fatto resta: il codice crea namespace come root e il seccomp nega `CLONE_NEWUSER`.
- Nota «Who owns what»: `remotix.tmpfiles` identico in sostanza (`/var/lib/remotix` 0755 root, `net` 0700 remotix, `/run/remotix` 0755 root, `/run/remotix/net` 0700); aggiungere i tipi SELinux dalla `.fc` (`remotix_net_state_t`, `remotix_net_run_t`, `remotix_var_lib_t`...).

### 4. The AppArmor profile and its mode - DA RISCRIVERE (diventa «The SELinux module and its mode»)
Titolo da cambiare (e i `rif("The AppArmor profile and its mode")` di ch12 S11 e ch14 S8). Contenuto vero (`selinux/remotix.{te,fc,if}`, F24-F28, D3):
- Il modulo `remotix` (versione `policy_module(remotix, 1.1.1)`, `remotix.te:1`) e' installato da `%post` (`%selinux_modules_install -s targeted /usr/share/selinux/packages/remotix.pp.bz2`, poi `%selinux_relabel_post`) e tolto da `%postun`; se non entra il `%post` lo dice chiaramente e non fallisce. Gira in enforcing, senza permissive, senza dontaudit nostri, senza audit2allow (intestazione `.te`).
- Tre domini: `remotix_t` (lato root), `remotix_net_t` (rete: tiene i tre descrittori ricevuti; nessun `create/bind/name_bind/name_connect` su socket IP; non esegue nulla; scrive solo `/var/lib/remotix/net` e `/run/remotix/net`), `remotix_hook_t` (hook locale). File e tipi: `/usr/libexec/remotix/remotix` = `remotix_exec_t`; `remotix-local-login` = `remotix_hook_exec_t`; `/run/remotix` = `remotix_var_run_t`; `/run/remotix/prelocal` = `remotix_prelocal_t`; `/run/remotix/net` = `remotix_net_run_t`; `/var/lib/remotix` = `remotix_var_lib_t`; `/var/lib/remotix/net` = `remotix_net_state_t`; `/etc/dconf/db/remotix(.new)` = `remotix_dconf_db_t` (`remotix.fc`).
- Come ci entra: NON per percorso (lo stesso binario e' lato root, rete e figlio utente): il fork scrive il contesto in `attr/exec` (S3). Nessun tipo di porta proprio (valutato: un modulo non porta `portcon`; richiederebbe `semanage port`).
- Verifiche (da PIANO.md/registro, non rilette sui log): giro finale `h1` in enforcing, AVC nostri 0; prova negativa 0 FAIL; rifiuti noti non nostri (F28: `relabelto tmp_t` di systemd utente, `bwrap` in `staff_t/user_t`, `ssh-agent` su XFCE con utenti confinati; F15). Utenti confinati `staff_u`/`user_u`: contesto = quello dell'accesso locale (F25); `sysadm_u` non entra (come ssh e gdm).
- Limiti dichiarati (F27): `remotix_t` resta largo in sei punti; alternativa sul tavolo (far rieseguire le «faccende» come processo utente): decisione del proprietario non presa (non verificato lo stato).
- Rimosso: profilo `.apparmor`, `complain`, le due righe `deny unix` (C4), XKB `xkeyboard-config-2`, `dh_apparmor`, `postrm` `.remove` kernel, lezione C4. «Aggiornamento senza muro»: finestra tra caricamento del modulo e riavvio del servizio (F24).
- `%postun` e `%selinux_relabel_post`: alla rimozione `restorecon -R /var/lib/remotix` se la cartella resta.
Prova: PIANO D3; F24-F28, F31-F33; `selinux/remotix.te`; `rpm/remotix.spec` `%post/%postun`.

### 5. Local excludes remote and the session cap - DA CORREGGERE
- Le quattro difese (`delivery_verdict()`, `local_children_round()`, `local_guard()`, hook): vale (codice identico). Difesa 4: l'hook e' agganciato dallo script `remotix-pam-hook` (S6), non da `pam-auth-update`.
- «Who is told, and when» e «What else answers 0x0E»: valgono; `rif("The four desktops side by side")` resta. Il sesto motivo di 0x0E nuovo su Fedora: KWin piu' vecchio di 6.8 (nessun `kde_output_management_v2` >= 22) rifiuta la sessione con messaggio chiaro (F7), e i rifiuti SELinux 44-47 di `child.c` («the login is REFUSED»): aggiungere.
- «The session cap answers 0x0E»: `RCP_SESSION_CAP 10` (`rcp.h:94`, vero), limite dichiarato 8: valgono.
- Il «live image» test di ch14 S6 e' la sezione dove sta il fatto Ubuntu; qui nulla.

### 6. The local-login hold - DA RISCRIVERE
Il pezzo «PAM line» e il pacchetto cambiano interamente (`src/remotix-pam-hook`, F6, F9, F18, F19, F21, D4):
- L'hook `remotix-local-login` (`local_login.c` identico, 132 righe) e la cartella `/run/remotix/prelocal` (tipo `remotix_prelocal_t`: «the ONLY thing the hook may touch») valgono; cambia COME entra negli stack: NON `pam-auth-update`/`common-session` ma `/usr/libexec/remotix/remotix-pam-hook apply|check|remove|prepare` (335 righe di shell). La riga e' `session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login` messa nella fase `session` SUBITO DOPO la prima `pam_selinux.so close` (cioe' PRIMA di `pam_selinux open`, non dopo `pam_systemd`): (1) il worker del login screen mette gia' `XDG_SEAT/XDG_SESSION_TYPE/XDG_VTNR` nell'ambiente PAM; (2) `pam_selinux open` imposta il contesto d'exec del PROSSIMO exec e una `pam_exec` dopo lo spenderebbe sull'hook (AVC `entrypoint`); (3) non prima di `close` perche' lo stack gira anche a CLOSE_session. Spiegazione completa nel commento di testa dello script.
- Perche' non authselect: `apply-changes` rigenera e cancella le righe a mano (provato, studio 1 §9.1); un profilo `custom/` sostituirebbe la scelta dell'amministratore. Lo script usa i file propri dei login screen: file del fornitore in `/usr/lib/pam.d/<dm>*` -> copia in `/etc/pam.d` con marcatore (rigenerata a ogni `apply`); file in `/etc/pam.d` non nostro -> solo il blocco marcato; sddm: i file `sddm*` stanno in `/etc/pam.d` e sono `%config` del pacchetto sddm: blocco aggiunto SUL POSTO e tolto byte per byte (`rpm -V sddm` segnala «modificato» finche' REMOTIX e' installato, F19). Mai toccati i link di authselect; composizione in file temporaneo, controlli, etichetta SELinux, poi `rename`.
- Login screen attivi: `gdm`, `plasmalogin` (pacchetto `plasma-login-manager`, KDE), `lightdm` (XFCE; `XDG_SESSION_CLASS` vuoto: accettato), `sddm` (LXQt). Mantenuto in vita da: `%post` (apply), trigger `%triggerin/%triggerpostun` per gdm, lightdm, sddm, plasma-login-manager (+ `%triggerprein/%triggerun` per sddm), `ExecStartPre=-remotix-pam-hook check` del servizio, `%preun` (remove, dopo lo stop del servizio). Finestra accettata: pochi secondi durante l'aggiornamento di sddm senza blocco (F21).
- Tabella «real login screens»: riscrivere con le prove di Fedora (PIANO.md:326-329, F9, F18, F19, F22): GNOME: il locale chiude il remoto e arriva al desktop, OK; KDE (plasmalogin): chiusura ordinata, con programma che non si chiude da solo F36: passava col remoto vivo fino alla correzione, ora forzata a 5,04 s, gancio liberato a 5,9 s; XFCE (lightdm): chiusura ordinata 1,7 s; LXQt (sddm): 0,7 s (prove a mano del proprietario con chiavetta il 25 nov); in VM: 1-2 s con remoto aperto, locale attivo -> remoto rifiutato. Le cifre sono quelle del giornale: non verificate sui log. Tutte le prove 1-3 («il remoto si chiude», «orfano A1», «locale attivo -> rifiutato») riuscite su GNOME, KDE (plasmalogin), XFCE e LXQt.
- Comportamenti dei login screen: gdm tratta (dialogo «Session Already Running»), plasmalogin/lightdm/sddm no (voce A2 del registro); «GDM 50.1 ... Force Stop» -> GDM 51 (studio 1 §5.2: letto, non provato su Fedora); non verificato.
- «A real gdm login wipes the screen»... non c'e' altro. «The second rule, no orphan desktops»: vale com'e' (`LX_EVERY_MS 5000`).
- Da ricontare: `PL_GRACE_MS 13000`, `PL_CEIL_MS 20000`, `PL_HOLD_MS 10000`, `PL_MAX 8`, `LOCAL_CEIL_MS 25000`, `LX_EVERY_MS`: `grep -n 'define PL_\|LOCAL_CEIL_MS\|LX_EVERY_MS\|LOCAL_SWEEP_MS' src/rootside.c src/local_login.c src/main.c`.

### 7. The denied-users list - DA CORREGGERE
Il testo vale (rootside e `pam_listfile`). Cambia: «installed from `debian/denied-users` ... a dpkg conffile» -> `rpm/denied-users` -> `/etc/remotix/denied-users` `%config(noreplace)`; un aggiornamento mantiene le modifiche (rpm produce `.rpmnew`) e `%postun` toglie solo `denied-users.rpmsave` per nome (spec).

### 8. Polkit rules, password windows and the power belts - DA CORREGGERE
- Regola `50-remotix-no-poweroff.rules` (19 azioni): identica a Ubuntu (`diff -q` nessuna differenza); le 19 esistono tutte nella policy di systemd 262 (`org.freedesktop.login1.policy` ne ha 37; studio 1:401). Da ricontare: «19» con `grep -c 'org.freedesktop.login1' src/remotix-no-poweroff.rules` (non ricontato). `power-implied` e `power-local-seat` di `prove/check-desktop.py` (file DIVERSO da Ubuntu, `diff -q`): NON eseguiti su Fedora secondo il registro/studio («Non eseguito su Fedora ... da fare», studio 1:401; il giro `h1` riporta `check-desktop` e `power-entries-absent/power-implied/power-local-seat/no-password-windows` PASS su XFCE, F22): marcare il caso del greeter su Fedora «non provato» (studio 1:407, voce C6).
- Regola `40-remotix-remote-sessions.rules`: su Fedora tratta SEI azioni, non cinque: `Flatpak.metadata-update`, `Flatpak.appstream-update`, `packagekit.system-sources-refresh`, `fwupd.refresh-remote` (nuova, F3: GNOME Software la chiede al login e copriva il desktop con una finestra di password), e per la macchina `NetworkManager.network-control`, `Flatpak.modify-repo` (`remotix-remote-sessions.rules:76-84`). Il commento di testa dice ancora «five actions» (difetto del sorgente). Amministratore = `wheel` (gruppo di Fedora), `sudo` o `admin`.
- Togliere: «sudo-rs 0.2.13» (Ubuntu), snap polkit policies, `polkitd 127-2ubuntu1.1`, `49-ubuntu-admin.rules`, i risultati `unione10/unione11` e `/media/REMOTIX-UBUNTU/...`, C6 storia (puo' restare come storia del codice ma con «Debian e Ubuntu»: su Fedora la stessa regola nasce a 19 azioni); polkit 127-5, `20-gdm.rules` ecc. (studio 1:397). Fedora usa `sudo` classico: non verificato il comportamento di `CAP_SYS_BOOT`.
- `remotix-polkit-seated`: identico; nessun D-Bus (stesso motivo).
- «The other two belts»: percorsi invariati `/usr/share/remotix/belts/` (`remotix-power-keys.conf`, `remotix-no-suspend.conf` da `rpm/remotix-no-suspend.conf`), spenti, l'amministratore li copia in `/etc/systemd/logind.conf.d/` e `/etc/systemd/sleep.conf.d/`.

### 9. The service unit and why it is not sandboxed - DA CORREGGERE
- Tabella: il testo vale per `rpm/remotix.service` (stesse opzioni, `KillMode=mixed`, `Restart=on-failure`, `RestartPreventExitStatus=78`, `LimitRTPRIO/LimitNICE`). Aggiunte Fedora: `Environment=MESA_SHADER_CACHE_DISABLE=true` (la sonda codec del lato root apriva la cache Mesa in `/root/.cache`, vietata a `remotix_t`) e `ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check` (rimette la riga del gancio se manca; `-` = mai impedisce l'avvio). `WorkingDirectory=/`. Il commento dell'unita parla ancora di `provision.sh`: ignorabile.
- «`sudo apt install` in a remote desktop» -> `sudo dnf install` (cosmetico). `WantedBy=multi-user.target`: presente, il pacchetto non abilita (`preset` Fedora `disable *`; spec `%post` `%systemd_post`).

### 10. What the security model does not defend - DA CORREGGERE
- Righe valide: man-in-the-middle al primo collegamento, niente secondo fattore, lock schermo spento, utenti l'uno contro l'altro, amministratore, root side compromesso, pause del lato root, NAT, canale temporale, faillock in inglese.
- «Kernel facilities that the walls need»: kernel di Fedora non verificato (Landlock ABI, 5.12/6.12). «AppArmor in a session» -> riga SELinux: enforcing, giro `h1` 0 AVC nostri, ma `remotix_t` e' largo in sei punti (F27); `giro-selinux.sh` nasconde un controllo (PIANO.md:458-461). Righe aperte da aggiungere: `force_guard_on` (`session.c:8770`), `catatonit`, rifiuto `search` su `/proc/sys/dev`, NVIDIA, Safari/Firefox su Windows, IPv6 (PIANO.md:458-461).
- «What the package changes on the machine» da riscrivere: UNA sola modifica di un file di sistema NON e' piu' vera: lo script `remotix-pam-hook` crea/modifica file in `/etc/pam.d` dei login screen (copie marcate per gdm/plasmalogin/lightdm, blocco marcato in `sddm*`) e li ripulisce a `remove`; NON tocca i file di authselect. Il gruppo della scheda (`usermod -aG`, `/var/lib/remotix/group-enrollments.jsonl`, `gpasswd -d`), le ACL su `/dev/dri/renderD*` (`render-grants`, `remotix --drop-render-grants`): invariate (spec `%preun`). Database dconf `/etc/dconf/db/remotix`, file utente `~/.config/dconf/remotix`, `lock-warning-shown`: vale. TOGLIERE «our own labwc». Mantenere la regola needrestart `/etc/needrestart/conf.d/remotix.conf` (il file e' nel pacchetto, ma `needrestart` NON e' installato di serie su Fedora: la riga e' innocua, `%postun` rimuove le cartelle `/etc/needrestart` se `needrestart` non c'e'; non verificato che dnf-automatic lo usi). Aggiungere: modulo SELinux, servizio firewalld `/usr/lib/firewalld/services/remotix.xml` (definisce, non apre), trigger sui pacchetti dei login screen.
- «Hardware and clients not tried»: `NVIDIA (deferred)`, Samsung DeX (solo Debian), canvas > 3840x2160: invariati. La riga sulla Radeon dei test Ubuntu -> la Radeon passata alle VM Fedora (`server/vm-radeon.sh`); percorso di codifica su Fedora: richiede RPM Fusion (D1); VA-API/Vulkan senza H.264 di serie (studio 4 punto 1).

---------------------------------------------------------------------------------------------------

# PARTE D - Manuale utente, `user-ubuntu26.04/` ch01-ch06

Valido per tutto il manuale utente: «Ubuntu 26.04 (Ubuntu, Kubuntu, Xubuntu, Lubuntu)», `apt`, `universe`, `ufw`, AppArmor, `pam-auth-update`, labwc nostro, «live images di Ubuntu/Kubuntu», `1.0.1` e `.deb` da sostituire. In ogni capitolo la voce «Requirements» di D1 (codec da RPM Fusion) va in primo piano (vedi ch01 S2 e (a)).

## ch01_overview - «What REMOTIX is» (5 sezioni)

### 1. REMOTIX in short - DA CORREGGERE
- Quasi tutto vale. Cambiare: «On Ubuntu 26.04 no more than three people were tried together» -> cifra di Fedora non verificata (giro `multiuser` `two-users/three-users` su GNOME e KDE, F28/F27: non c'e' un numero di utenti simultanei in PIANO; marcare «non verificato su Fedora»). Tetto 10 sessioni (`RCP_SESSION_CAP`), supportati 8 persone, 3K: validi (codice identico). Nome della figura «The Linux machine»: va bene.
- Il rif «Leaving and coming back» e «On a phone or a tablet»: titoli da tenere.

### 2. What you need - DA RISCRIVERE
- Riga «The machine»: «Fedora 45 Workstation (GNOME), KDE Plasma, Xfce or LXQt spin», PC `x86_64` (`ExclusiveArch: x86_64 aarch64`, ma aarch64 non provato: non verificato). Togliere `universe`, `amd64`, `deb`. Il desktop e' di serie su ciascuna edizione; REMOTIX non lo installa.
- Riga «The video card» = REQUIREMENTS (D1, `PIANO.md:96-102`): su Fedora H.264/HEVC NON sono di serie (VA-API e Vulkan Video senza H.264/H.265: Mesa di Fedora li ha tolti); l'amministratore abilita RPM Fusion (free) e installa `mesa-va-drivers-freeworld` (AMD/Intel); NVIDIA: driver proprietario. Nessuna codifica software. Il pacchetto non porta i codec come dipendenza. Il test al termine della prima installazione (`%post`, exit 0/3/1) dice cosa fare (`mesa-va-drivers-freeworld`, `remotix --encoding-test h264`). Rifiuto senza nodo DRM `renderD*` (spec `%pre`, r.~168-176). Solo AMD (Radeon passata alle VM) provato; Intel: non provato.
- Riga «NVIDIA cards»: invariata («not yet verified», NVIDIA rimandato).
- Riga «The network»: porta 7447 TCP e UDP; AGGIUNGERE firewalld (F20: `sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload`). Aggiungere SELinux attivo (enforcing) come requisito dichiarato: il pacchetto porta il suo modulo.
- Tabella browser: invariata (`page.html` identico). La frase «On Ubuntu 26.04 the automatic tests used Chrome and Firefox on Linux (four desktops first rounds, GNOME last)» -> riscrivere con i test Fedora (non verificato quale browser: `check-*` usano Chromium/Firefox, F22/F33: «dnf install chromium» per `check-kde-live`; il giro `h1` browser non letto).
- Nuova riga «Requirements» per i limiti dichiarati: portachiavi (D6), sfondo/icone XFCE (D7), nessun spegnimento dal desktop.

### 3. What REMOTIX is not - DA CORREGGERE
- Le prime sette puntate valgono (identiche a Ubuntu). Aggiungere alle cose volutamente assenti: portachiavi di sessione (D6: nessun `pam_oo7`/`pam_kwallet`: un programma che chiede il portachiavi trova la collezione `login` bloccata e chiede la password sullo schermo remoto, studio 1 §7); XFCE senza sfondo e icone (D7).

### 4. The desktops - DA RISCRIVERE
- «four official flavours Ubuntu, Kubuntu, Xubuntu, Lubuntu» -> le quattro edizioni Fedora; login screen: GNOME `gdm`, KDE `plasmalogin` (pacchetto `plasma-login-manager`), XFCE `lightdm`, LXQt `sddm` (non `SDDM` per Kubuntu).
- «GNOME ... XFCE and LXQt run on labwc, the one of Ubuntu, which apt installs ... (universe)» -> labwc 0.20.2 di Fedora, `Recommends: labwc` (dnf lo porta; con `install_weak_deps=False` no). KDE: «runs on KWin alone (6.8), with no second labwc» (D2, F7); TOGLIERE la frase del labwc dentro il pacchetto e Firefox.
- «One desktop per machine»: vale; togliere il caso Xubuntu.
- «XFCE: the wallpaper» -> «XFCE: black background, no desktop icons: declared limit on Fedora» (D7, F22: `xfdesktop was not built with Wayland support`); la voce vecchia (un wallpaper per schermo) NON e' la causa.
- «GNOME: the Overview»: vale se GNOME 51 parte ancora nell'Overview (non verificato).
- `dconf-cli`: su Fedora il comando `dconf` sta nel pacchetto `dconf` (`Recommends: dconf`).
- Nota «Your settings»: invariata.

### 5. The licence - DA CORREGGERE
- «Its full text is in `/usr/share/doc/remotix/copyright`»: su Fedora il pacchetto usa `%license LICENSE.md` (-> `/usr/share/licenses/remotix/LICENSE.md`) e `%doc THIRD-PARTY-LICENSES` (-> `/usr/share/doc/remotix/THIRD-PARTY-LICENSES`, non `.gz`): percorsi da verificare con `rpm -ql remotix` sul pacchetto 1.2.0 (non esiste ancora). `License: LicenseRef-REMOTIX AND MIT` (spec). Difetto del sorgente: `fedora45/LICENSE.md:95-102` e' identico a Ubuntu e parla di labwc/wlroots; decisione richiesta (correggere `LICENSE.md` o non citarlo).

## ch02_installing - «Installing REMOTIX» (8 sezioni)

### 1. The steps - DA RISCRIVERE
- «REMOTIX 1.0.1 is for Ubuntu 26.04» -> `1.2.0` per Fedora 45. Passi: (1) controlla la macchina; (2) abilita RPM Fusion e il driver video (D1) PRIMA di installare; (3) `sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm`; (4) `sudo systemctl enable --now remotix` (servizio installato spento, preset `disable *`); (5) firewalld (non ufw): aprire la porta con `firewall-cmd --add-service=remotix`; (6) prima visita e certificato. Togliere «ufw is installed but off».
- Vale: «any user except those excluded», primo collegamento = gruppo scheda (`render`), invariato.

### 2. Ubuntu 26.04: installing - DA RISCRIVERE (titolo: «Fedora 45: installing»)
- Comandi: `sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm` (non `apt`, `dpkg`), `sudo systemctl enable --now remotix`, `systemctl status remotix`; per reinstallare lo stesso numero `sudo dnf reinstall ./remotix-1.2.0-1.fc45.x86_64.rpm`. `dnf install ./file.rpm` risolve le dipendenze (come `apt install ./`).
- Tabella dei pacchetti: Needed (`Requires` della spec): `pam`, `gawk`, `systemd-pam`, `shadow-utils`, `systemd`, `dbus-broker`, `pipewire`, `wireplumber`, `firewalld-filesystem`, `libselinux` (via binario); Recommended (`Recommends`): `labwc`, `dconf`, `wlr-randr`, `xorg-x11-server-Xwayland`, `dejavu-sans-fonts`. I driver video NON sono nella tabella: sono un requisito dell'amministratore (D1, RPM Fusion `mesa-va-drivers-freeworld`). Togliere `va-driver-all`, `mesa-vulkan-drivers`, `libpam-*`, `universe`. Aggiungere il modulo SELinux (`%selinux_modules_install`) e il servizio firewalld.
- `--no-install-recommends` -> `--setopt=install_weak_deps=False`: il messaggio dice `sudo dnf install labwc`.
- Nota «Power off changes for everybody»: vale (stesse regole polkit).
- Il test della scheda al termine: messaggio vero (spec `%post`): «remotix: ⚠ the video card of this machine did not encode a test frame (H.264) ... on Fedora the H.264 driver is not in the base repositories: enable RPM Fusion (free) and install mesa-va-drivers-freeworld (NVIDIA: its proprietary driver), then: sudo /usr/libexec/remotix/remotix --encoding-test h264». Exit 0/3/1 invariato.

### 3. Ubuntu 26.04: the two refusals - DA CORREGGERE
- Messaggi identici (spec `%pre` r.~168-210: stesso testo con `usermod -l NEWNAME remotix`); «apt then ends with an error» -> `dnf` mostra l'errore dello scriptlet `%pre`. Il controllo vale per una installazione NUOVA (`$1 -eq 1`); aggiornamento mai rifiutato.
- Nota «Not tried on Ubuntu»: riscrivere «non provato su Fedora» (non verificato: tutte le VM avevano nodo DRM).

### 4. Ubuntu 26.04: the firewall - DA RISCRIVERE
- Su Fedora: firewalld, non ufw. Il pacchetto porta il servizio `/usr/lib/firewalld/services/remotix.xml` (`7447/tcp`, `7447/udp`), DEFINITO e non aperto (D5); dopo l'installazione il `%firewalld_reload` lo rende noto. Aprire: `sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload` (zona predefinita; altra zona: `--zone=NOME`); chiudere: `--remove-service=remotix`. Per solo la rete locale: `sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port port="7447" protocol="tcp" accept'` e idem `udp` (non verificato in questo albero: F20 prova solo `--add-service`).
- Togliere: «ufw is installed but switched off», `ufw app info/allow REMOTIX`.
- Stato del firewall di serie su Fedora Workstation (zona `FedoraWorkstation` apre le porte alte): non verificato; F20 dice zona `public` sulle VM. Il manuale non deve promettere che la porta sia chiusa.
- Nota «A different port»: invariata; il file del servizio firewalld dice 7447.

### 5. Ubuntu 26.04: the first visit and the certificate - VALE COM'E'
Codice identico (`certificates.c`, `page.c`); percorsi `/var/lib/remotix/net/certificates/` e comandi (stop, `mv`, `cp`, `chown remotix:remotix`, `chmod 600`) validi; su Fedora il contesto SELinux di quei file e' `remotix_net_state_t`: i file copiati a mano con `cp` ereditano il tipo della cartella (`tmpfiles` `Z` + `restorecon`): non verificato; se serve, aggiungere `sudo restorecon -R /var/lib/remotix/net` dopo la copia (non provato). Solo i `rif()` verso i titoli rinominati.

### 6. Ubuntu 26.04: port, name and other settings - VALE COM'E'
`/usr/share/remotix/remotix.conf` e `/etc/remotix/remotix.conf.d/*.conf` identici (`rpm/remotix.conf`); `REMOTIX_PORT`, `REMOTIX_OPTIONS`. Nota sulla porta: «apri la nuova porta nel firewall» (firewalld: il servizio `remotix` dice sempre 7447; con porta diversa servono `firewall-cmd --add-port=PORT/tcp` e `/udp`; SELinux non ha tipo di porta proprio, D3: non verificato che una porta non riservata funzioni sotto enforcing; il commento di `.te` dice che il lato root lega le porte non riservate e le http). Solo `rif()` da rinominare.

### 7. Ubuntu 26.04: who may connect - VALE COM'E'
`/etc/pam.d/remotix` = stack di sshd di Fedora (`password-auth`): «the same stack that ssh uses» e' vero; `denied-users` con `root`, `/etc/nologin`: invariati. Aggiunta utile: «`pam_faillock` non e' attivo di serie su Fedora (profilo authselect `with-faillock`)». `sudo passwd -l anna` vale. Solo `rif()`.

### 8. Ubuntu 26.04: upgrading and removing - DA RISCRIVERE
- Upgrade: `sudo dnf install ./remotix-NEW.rpm` (o `dnf upgrade` da repository: non c'e'); il servizio e' riavviato SOLO se era in esecuzione (`%systemd_postun_with_restart`); i desktop vengono chiusi dal riavvio. Rimuovere frasi su `apt asks which version to keep`: rpm crea `.rpmnew`/`.rpmsave` per `%config(noreplace)` (`/etc/pam.d/remotix`, `denied-users`, regola needrestart).
- Needrestart: non e' installato di serie su Fedora; il pacchetto porta comunque `/etc/needrestart/conf.d/remotix.conf` (innocuo). Togliere «Ubuntu's own updates ... needrestart ... not seen at work»: non verificato su Fedora.
- Removing: UN solo comando, `sudo dnf remove remotix`, equivale a `remove`+`purge` di Debian (spec `%postun`, commento «an RPM has no purge»): chiude i desktop (SIGTERM, 15 s, poi SIGKILL del solo scope), ferma il servizio, toglie la riga del gancio PAM dai login screen (`remotix-pam-hook remove`; i file `/etc/pam.d/sddm*` tornano byte per byte), toglie i gruppi e le ACL sulla scheda, toglie il modulo SELinux (`%selinux_modules_uninstall`), `firewalld_reload`, elimina `/var/lib/remotix`, `/run/remotix`, il database `/etc/dconf/db/remotix`, i file nelle case degli utenti (`~/.local/state/remotix/`, `~/.config/dconf/remotix`, come l'utente con `runuser`), l'utente di sistema `remotix` se non preesistente. Resta: file di configurazione modificati dall'amministratore (`.rpmsave` per nome tolti), `/etc/remotix/remotix.conf.d` se contiene file propri, una regola firewalld che l'amministratore ha aggiunto (`firewall-cmd --remove-service=remotix` a mano).
- Togliere: AppArmor «its file stays», ufw profile, labwc nostro, `pam-auth-update`, «apt purge», «apt autoremove» -> `sudo dnf autoremove` (lista da leggere prima: i pacchetti arrivati come dipendenze deboli, labwc, wlr-randr, wlroots, swaylock..., se ne vanno con `dnf remove`, F19).
- «What the purge does not reach» (utenti non elencati): vale.
- Nota «Not tried on Ubuntu» -> rimozione e reinstallazione PROVATE sulle VM Fedora (F19: `dnf reinstall sddm`, `dnf remove remotix`: `/etc/pam.d/sddm*` byte per byte uguali; F24: rimozione anche con `/var/lib/remotix` residuo; reinstallazione da zero), ma NON su una macchina fisica diversa dalle VM e col pacchetto 1.2.0 (non esiste ancora: da riprovare, PIANO.md:463+).

## ch03_using - «Connecting and using it» (7 sezioni)

### 1. Signing in - VALE COM'E'
`page.html`, `page.c`, `rcp.c` identici: form, menu Keyboard, tempi 1 s / 2,5 s, messaggi. Da ricontare: «33 layouts» (`page.html`: `grep -c` del catalogo layout: comando non individuato, non ricontato) - il file e' identico a Ubuntu quindi il numero e' lo stesso, ma va verificato col generatore. Solo `rif("...first visit and the certificate")`.

### 2. The desktop in the browser - DA CORREGGERE
- Riga «XFCE: the wallpaper» -> «XFCE: black background and no icons (declared limit, D7)». Riga «GNOME: the Overview»: da riverificare con GNOME 51 (non verificato).
- Nota «Passwords inside the desktop»: pkexec da GNOME: SHELL vuoto, FAIL noto anche su Fedora (PIANO.md:316); «Three requests that a desktop makes on its own at sign-in» -> QUATTRO su Fedora (catalogo programmi Flatpak/PackageKit + `fwupd.refresh-remote`, F3) piu' due per l'amministratore: aggiornare «three».
- Riga «No power buttons»: vale. Resto invariato.

### 3. The keyboard - DA CORREGGERE
- Vale la tabella dei tasti tenuti dal browser («misurata su Debian 13, non ripetuta»): su Fedora ancora non misurata; cambiare «not repeated on Ubuntu (the tests there used newer browsers)» con «non ripetuta su Fedora». Il file `~/.config/dconf/remotix` (GNOME): vale. Menu Keyboard: vale.
- Da ricontare: nessun numero.

### 4. Copy and paste - DA CORREGGERE
- Nota «What was tried»: «On Ubuntu 26.04 the automatic tests checked the clipboard with Chrome and Firefox...» -> Fedora: `check-clipboard` 2/2 su XFCE e LXQt (F22); su GNOME/KDE nel giro `h1` (PIANO.md:316-320: non letti i singoli esiti: non verificato). Il limite 1 000 000 byte e il resto: validi (`clipboard.c` invariato).

### 5. Leaving and coming back - DA CORREGGERE
- Tabella valida salvo l'ultima riga («Somebody signs in at the machine's screen with your user name»): riscrivere con le prove Fedora: provato ai veri login screen di GNOME (gdm), XFCE (lightdm), LXQt (sddm) e KDE (plasmalogin) con chiavetta Live (PIANO.md:326-329, 25 nov): chiusura del desktop remoto in circa 1-2 s su GNOME, 1,7 s su XFCE, 0,7 s su LXQt; su KDE, con un programma che non si chiude da solo il remoto viene forzato dopo 5 s (5,04 s) e l'accesso locale prosegue a ~5,9 s (F36, `KDE_PRELOCAL_ORDERLY_MS`); senza programma bloccante pochi secondi. Cifre del giornale, non lette sui log. Togliere «about eleven seconds» e «not tried at Xubuntu/Lubuntu».
- Resto (tab chiusa, 30 min, 60 min, Log Out, due dispositivi, riavvio): vale (`rcp.c` identico). «On XFCE a Log Out chosen in the first seconds may be ignored»: vale (stesso codice di xfce4-session 4.20.4); non rimisurato su Fedora.

### 6. On a phone or a tablet - DA CORREGGERE
- Nota finale: «on Ubuntu»: gesti non provati uno a uno su telefono reale (valido ancora); la riga sull'Overview e sul primo tap: su Fedora F34 trova che il PRIMO movimento assoluto su GNOME arriva con una coordinata a 0 (mutter 51.0) e `input.c` lo manda due volte (cura attiva, «da togliere quando Mutter sara' corretto»): il manuale deve dire che il primo tocco dopo l'accesso e' protetto da una cura software; efficacia da `check-multiuser one-user` e `check-phone tap-click-portrait` (F34: provate; esito finale non riletto, non verificato).

### 7. Samsung DeX - DA CORREGGERE
- «On Ubuntu 26.04 it was tried by hand once, on GNOME, in a first test environment» -> su Fedora non provato (Samsung DeX provato dal proprietario solo su Debian: `ch14 S10`); marcare «non verificato su Fedora». Il resto (no hover, Super tenuto da Android): vale.

## ch04_problems - «When something does not work» (7 sezioni)

### 1. What the page says when you sign in - DA CORREGGERE
- Righe vere uguali (`page.html`, `rcp.c` identici). Cambiare: riga «the server could not open your session»: cause tra parentesi: «labwc on Xubuntu and Lubuntu» -> «labwc su XFCE e LXQt»; aggiungere: KWin piu' vecchio di 6.8 su KDE (F7), rifiuto SELinux del contesto (child.c 44-47, per utenti confinati particolari), «per i dettagli leggere il journal». Riga «nothing in common to speak»: la cura Ubuntu (`va-driver-all`, `mesa-vulkan-drivers`) -> su Fedora e' D1: «RPM Fusion `mesa-va-drivers-freeworld` (AMD/Intel), driver proprietario (NVIDIA)»; la frase «A virtual machine with only the emulated card cannot encode» vale (F18, F19: «the server and this page have nothing in common to speak» in VM senza Radeon).
- Riga «Cannot connect: ... UDP port 7447 is blocked»: rif a `Fedora 45: the firewall`, comando firewalld.
- Riga «incorrect username or password»: l'amministratore puo' controllare `sudo passwd -S USER`, `denied-users`, `/etc/nologin`: vale; aggiungere `faillock` solo se abilitato.

### 2. The login defences - VALE COM'E'
`rcp.c` identico: tre contatori, scala 15 min / 1 h / 12 h, nessuno sblocco. Da ricontare: 5/20/30 e 5/5/10 minuti (`grep -n 'LIMIT\|WINDOW_MS' src/rcp.c`). L'affermazione «As installed REMOTIX listens on IPv4 only» vale (unita: `--address 0.0.0.0`).

### 3. The three clocks - DA CORREGGERE
- Tabella valida (30 s / 30 min / 60 min, `rcp.c`). Ultima frase: «On Ubuntu 26.04 the 30 and 60 minute clocks were tried only with short values (29 and 90 seconds)» -> per Fedora non verificato: i check `check-lifecycle`/`check-resilience` esistono, i valori non sono letti (giro `h1`: lifecycle PASS, PIANO.md:316).

### 4. How a session ends - VALE COM'E'
Le frasi sono di `page.html`/`rcp.c` (identici). Nessuna dipendenza dalla distribuzione.

### 5. Where the administrator looks - DA CORREGGERE
- Comandi `journalctl -u remotix`, `-t remotix`, `-p warning -b`, `-f`; `~/.local/state/remotix/session.log`; `ss -ltnup`; `remotix --encoding-test h264`: validi (usano `systemd-journald`, presente su Fedora).
- Aggiungere SELinux: rifiuti si vedono con `sudo journalctl -b -g 'avc:'` o `sudo ausearch -m avc -ts recent` (F24: su queste VM `ausearch` non vede nulla anche quando il giornale ha gli AVC: usare `journalctl -b -g avc:`). Stato del muro: la riga del log «SELinux: born in system_u:system_r:remotix_net_t:s0» (`walls.c:340`) e `semodule -l | grep remotix` (il `%post` stampa un avviso se il modulo non e' caricato). Il file `/etc/pam.d/remotix` esiste e `denied-users`: vale. Il messaggio «the PAM service «remotix» DOES NOT EXIST ...» contiene ancora «.fedora, .suse, .arch» (difetto del sorgente).
- Aggiungere: la riga del gancio PAM (`remotix-pam-hook check` scrive una riga di riepilogo a ogni avvio del servizio, visibile con `journalctl -u remotix`).

### 6. What cannot be done, by design - VALE COM'E'
Tutte le puntate valgono su Fedora (stesse regole polkit, nessun unblock, nessun lock, root escluso, un browser per utente, tasti tenuti dal browser, tastiera scelta al login). Eventuale aggiunta: portachiavi non sbloccato (D6).

### 7. Known problems on Ubuntu 26.04 - DA RISCRIVERE (titolo: «Known problems on Fedora 45»)
Tutte le righe sono di Ubuntu (Chrome su Android E4, internal error wireplumber in VM senza scheda audio, Kubuntu 11 s, Xubuntu Log Out/angolo, sfondo XFCE, programmi snap/Flutter, scale GNOME). Per Fedora (registro F, solo cio' che un utente/amministratore incontra):
- Codec: nessuna codifica H.264 senza RPM Fusion (D1) - messaggio e rimedio.
- XFCE: fondo nero e niente icone (D7); pannello non parte con utente SELinux `staff_u` (F30).
- KDE: chiusura forzata dei programmi di sfondo con core dump (F16); desktop lento a chiudersi se un programma chiede «salvare?» (F36: l'accesso locale attende 5 s poi forza); `kwinoutputconfig.json` ricorda la misura (F8: il desktop puo' nascere con l'ultima misura e viene corretto subito); piu' schede grafiche non provato (F12).
- GNOME: pkexec dalla sessione remota (SHELL vuoto): usare `sudo` in un terminale; primo clic a coordinata 0 curato (F34); portachiavi bloccato (D6).
- Tutti: lingua: segue l'utente (AccountsService) o il sistema (`/etc/locale.conf`), F34/F35: con `langpacks-it` il desktop e' in italiano; senza codifica in AccountsService (`it_IT` senza `.UTF-8`) non e' provato (PIANO.md:458-461).
- La riga «The service is killed ... two seconds nobody can close the desktop»: vale (invariato).
- Aperti dichiarati (PIANO.md:458-461): chiusura per abbandono su KDE; programmi lenti a chiudersi su KDE; Safari/Firefox su Windows; IPv6; NVIDIA.

## ch05_looking_after - «Looking after an installation» (6 sezioni)

### 1. The service - VALE COM'E'
`systemctl enable/disable/restart/status remotix`, TCP+UDP 7447, uid `remotix` per la parte di rete, `Restart` dopo 2 s, stato 78: validi (`rpm/remotix.service`, `remotix.sysusers`). Servizio installato spento (preset Fedora `disable *`; spec `%post` commento). Solo i `rif()`.

### 2. What a restart of the service does - DA CORREGGERE
- Resto valido. Correggere: «On Ubuntu (GNOME) it was about one second, on Kubuntu about eleven» -> Fedora (prove del 25 nov): GNOME ~1-2 s, XFCE 1,7 s, LXQt 0,7 s, KDE circa 5-6 s quando un programma non si chiude da solo (forzata a 5,04 s, locale a 5,9 s) - cifre del giornale (PIANO.md:326-329, F36), non lette sui log. «at most about 25 seconds»: `LOCAL_CEIL_MS 25000` vale.
- Needrestart: «Ubuntu's own restarts after a library update (needrestart) do not restart REMOTIX» -> su Fedora needrestart non e' di serie; la regola e' comunque nel pacchetto (non verificato che `dnf-automatic`/`needrestart` la rispetti). Riscrivere o togliere.

### 3. Settings you can change - VALE COM'E'
Tabella (`REMOTIX_PORT`, `--name`, `--session-cap`, `--inactivity-s`, `--abandon-s`): codice identico, default invariati (`rpm/remotix.conf`). Sole modifiche: il rif «Ubuntu 26.04: port, name and other settings» e «Open it in the firewall» (-> firewalld).

### 4. Users, groups and what REMOTIX changes - DA RISCRIVERE
Tabella «What REMOTIX adds to the machine»: sostituire/togliere:
- Valide: utente/gruppo `remotix` (`rpm/remotix.sysusers`, `/usr/sbin/nologin`, home `/`); servizio PAM `/etc/pam.d/remotix` (stack di sshd di Fedora, `%config(noreplace)`); `/etc/remotix/denied-users`; gruppo della scheda (`group-enrollments.jsonl`, `gpasswd -d`); ACL su `/dev/dri/renderD*` (`render-grants`); due regole polkit in `/usr/share/polkit-1/rules.d/` (il testo «three requests» diventa QUATTRO di aggiornamento cataloghi: Flatpak x2, PackageKit, fwupd, piu' due per l'amministratore, `wheel` come gruppo di Fedora: `remotix-remote-sessions.rules:76-84,108`); database dconf `/etc/dconf/db/remotix` (comando `dconf` del pacchetto `dconf`, non `dconf-cli`); regola needrestart (innocua se needrestart non c'e'); permesso KDE `org.kde.remotix.desktop` (`/usr/share/applications/`).
- TOGLIERE: profilo AppArmor, ufw profile, «second compositor» `/usr/libexec/remotix/labwc`, riga in `/etc/pam.d/common-session` da `pam-auth-update`.
- AGGIUNGERE: modulo SELinux `remotix` (tre domini, enforcing, file in `/usr/share/selinux/packages/remotix.pp.bz2`, tipi sui file, F24); servizio firewalld `/usr/lib/firewalld/services/remotix.xml` (definito, non aperto); `remotix-pam-hook` (`/usr/libexec/remotix/remotix-pam-hook`): scrive file/blocchi in `/etc/pam.d` dei login screen (`gdm-*`, `plasmalogin*`, `lightdm*`, `sddm*`), rimessi a ogni avvio del servizio, aggiornamento del pacchetto del login screen e `%preun`; `rpm -V sddm` segnala la modifica finche' REMOTIX e' installato (F19); `/usr/libexec/remotix/remotix-polkit-seated`.
- «Users' own settings» e testo GNOME/XFCE/KDE/LXQt: vale (codice identico), tranne «snap»/«App Center»/«Unknown DConf source» (Ubuntu): togliere; su Fedora le impostazioni arrivano da gschema override. «Without `dconf-cli`» -> «senza il pacchetto `dconf`» (`%post` avvisa: «dconf not found ... the GNOME remote session will use its fallback»).
- Nota nuova da dichiarare: portachiavi (D6).

### 5. Security on a shared server - DA CORREGGERE
- Righe valide: due livelli, primo click, password della macchina, root escluso, macchina condivisa, ban solo col tempo.
- «Do not put it on the open Internet ... On Ubuntu the firewall (ufw) is off by default» -> firewalld: il pacchetto non apre nulla (D5); lo stato di serie di firewalld su Fedora Workstation non e' verificato (F20: zona `public` sulle VM). Non promettere «porta chiusa di serie».
- «pam_faillock in the common PAM stack»: su Fedora si attiva con `authselect enable-feature with-faillock` (feature del profilo; non verificato il comando esatto, studio 1:9.1 elenca le funzioni).
- «Optional protections you can switch on» (belts): comandi invariati (percorsi `/usr/share/remotix/belts/` e `/etc/systemd/logind.conf.d/`, `/etc/systemd/sleep.conf.d/`), spenti.

### 6. Where things are - DA CORREGGERE
Albero da aggiornare:
- `/usr/libexec/remotix/`: `remotix`, `remotix-local-login`, `remotix-pam-hook`, `remotix-polkit-seated` (togliere `labwc`).
- `/usr/share/remotix/`: `page.html`, `remotix.conf`, `linked.json`, `dconf/`, `belts/`.
- `/etc/remotix/`: `denied-users`, `remotix.conf.d/`; `/etc/pam.d/remotix`; `/etc/needrestart/conf.d/remotix.conf`; `/etc/dconf/db/remotix`.
- Togliere: `/usr/share/pam-configs/remotix`, `/etc/ufw/applications.d/remotix`, `/etc/apparmor.d/remotix_network`.
- Aggiungere: `/usr/lib/firewalld/services/remotix.xml`, `/usr/share/selinux/packages/remotix.pp.bz2`, `/usr/share/polkit-1/rules.d/{40,50}-remotix-*.rules`, `/usr/lib/sysusers.d/remotix.conf`, `/usr/lib/tmpfiles.d/remotix.conf`, `/usr/lib/systemd/system/remotix.service`, `/usr/share/applications/org.kde.remotix.desktop`, `/usr/share/licenses/remotix/LICENSE.md`, `/usr/share/doc/remotix/THIRD-PARTY-LICENSES` (percorsi da `rpm -ql`), file di login screen toccati in `/etc/pam.d/`. Per KDE `~/.config/kwinoutputconfig.json` e' di KWin (non di REMOTIX: F8).
- Invariati: `/var/lib/remotix/{net/{certificates/,ban},group-enrollments.jsonl,render-grants}`, `~/.local/state/remotix/`, `~/.config/dconf/remotix`.
- Paragrafo «Certificates»: vale.

## ch06_glossary - «Glossary» (1 sezione)

### 1. Words used in this manual - DA CORREGGERE
Le voci esistenti valgono (Abandonment, Ban, Canvas, Desktop, Detach, Encoding, H.264/HEVC, Inactivity, Log Out, PAM, Port 7447, QUIC/WebTransport, Session, Slot, Touch layout, Wayland). Aggiungere (specifiche Fedora): RPM Fusion, `dnf`, firewalld, SELinux (enforcing, modulo di REMOTIX), `wheel`, authselect, `.rpm`. Togliere nessuna voce. «Encoding ... only on the video card»: vale ma va collegato a D1 (codec da RPM Fusion).

---------------------------------------------------------------------------------------------------

# (a) Cose che esistono SOLO su Fedora e meritano una sezione NUOVA

1. **ch12 (tecnico), nuova sezione dopo «How a session is born» o dentro S4:** «The SELinux context of the user's session» - `selinux_exec_like_local_login()` (chiede alla tabella libselinux col chiamante `xdm_t`), `selinux_exec_checked()` (rilegge `getexeccon()`, rifiuti 44-47 del `child.c`), portachiavi di sessione rifatto solo se diverso dal contesto d'exec (utenti confinati `staff_u/user_u`: F25, F33 H). Prova: F5, F25, F33.
2. **ch12, nuova sezione «Language and locale of the remote session»:** `child_locale_read()` da root prima di `setuid()`, `Languages=`/`Language=` di AccountsService (`/var/lib/AccountsService/users/<name>`, `root:root 0700`), poi `LC_*`/`LANGUAGE` di `/etc/locale.conf`, `CHILD_LOCALE_MAX 12` (F34, F35). Limite: senza codifica `it_IT` non provato.
3. **ch12 S7 (riscritta):** KWin da solo, `kwin_output_resize()`, protocollo `kde_output_management_v2`, rifiuto con KWin < 6.8, F8 (`kwinoutputconfig.json`), F12.
4. **ch13 (o ch14) nuova sezione «The Fedora PAM stack and authselect»:** `password-auth`/`postlogin`, `pam_sepermit`, `pam_selinux open env_params`, `pam_namespace`, perche' non si tocca authselect.
5. **ch14, sostituire S4 con «The SELinux module and its mode»** (vedi sopra) e AGGIUNGERE «The local-login hook: remotix-pam-hook» (S6 riscritta).
6. **ch14 S8 (o ch15):** `firewalld` (servizio `remotix.xml`, D5, F17 file XML non valido corretto, F20 comandi, `%firewalld_reload`), RPM scriptlets e trigger, `%postun` = purge.
7. **ch14 S9:** `MESA_SHADER_CACHE_DISABLE=true` e `ExecStartPre=-... remotix-pam-hook check`.
8. **ch11/ch12 S6 (limiti):** «primo movimento assoluto a 0 su GNOME 51 (F34)».
9. **Manuale utente ch01 S2:** sezione «Requirements» in primo piano (D1: RPM Fusion, `mesa-va-drivers-freeworld`, porta 7447 col comando firewalld di F20, SELinux attivo), con i limiti dichiarati (D6 portachiavi, D7 XFCE, nessuno spegnimento).
10. **Manuale utente ch02:** sezione «Fedora 45: video drivers (RPM Fusion)» - passi: abilitare RPM Fusion free, installare `mesa-va-drivers-freeworld`, `remotix --encoding-test h264`.
11. **Manuale utente ch04 S7:** «Known problems on Fedora 45» (vedi sopra); **ch05 S4:** voci SELinux, firewalld, `remotix-pam-hook`.

# (b) Cose di Ubuntu/Debian da TOGLIERE (nei capitoli del gruppo)

- ch12: labwc nostro (`/usr/libexec/remotix/labwc`, `wlroots-0.19.2-remotix-presented-root.patch`, `build/labwc-ospite/*`), ticker 16 ms, 240 Hz, tabella «Traps of KWin inside labwc», `kwin_nested_alive()`, regole labwc di KWin; modo `ubuntu` e le sue estensioni; «Xubuntu has both GNOME markers»; `/etc/X11/default-display-manager`, `gdm3`, `xubuntu/lubuntu/kubuntu/ubuntu` come parole di sessione; `/snap/bin`, Xsession.d, `xdg_dirs_desktop_session.sh`, D-153, `/etc/xdg/xdg-ubuntu`; `ubuntu-lock-on-suspend` nel testo; cifre dei giri Ubuntu (48/48, 1,5-2,9 s, `rxu-gnome`), `lubuntu-update`/`picom` come cose presenti; modello C5 con snap/Flutter; `dconf-cli`.
- ch13: `common-auth/common-account/common-session`, `libpam-sss`, `pam-auth-update`, `/etc/update-motd.d`, `/etc/nsswitch.conf` di Ubuntu, `dpkg conffile`, `apt install --reinstall remotix`, i test Ubuntu live.
- ch14: AppArmor (profilo, `dh_apparmor`, complain, `deny unix`, XKB `xkeyboard-config-2`, sysctl `apparmor_restrict_*`, C4, `.remove`), `pam-auth-update` e profilo `/usr/share/pam-configs/remotix`, live images Ubuntu/Kubuntu/Xubuntu/Lubuntu, `sudo-rs`, snap polkit, `49-ubuntu-admin.rules`, `debian/needrestart`, labwc nostro tra le cose cambiate sul sistema, `dpkg conffile`, `/media/REMOTIX-UBUNTU/...`.
- Utente: `apt`, `.deb`, `universe`, `ufw`, `va-driver-all`, `mesa-vulkan-drivers`, `libpam-*`, `fonts-dejavu-core`, `dconf-cli`, `xwayland`, AppArmor, labwc nostro, `pam-auth-update`, `apt purge`, `apt autoremove`, Kubuntu/Xubuntu/Lubuntu, GDM/SDDM/LightDM «of the flavours», snap, App Center, «live images of Ubuntu and Kubuntu», cifre 1 s / 11 s di Ubuntu/Kubuntu.

# (c) `rif("...")` che si rompono se un titolo cambia

Titoli del gruppo citati da altri capitoli (da `grep` su `build.py`: il generatore risolve i titoli esatti):
- **«The AppArmor profile and its mode»** (ch14 S4): citato da ch12 S11 (1) e ch14 S3, S8 -> se si rinomina in «The SELinux module and its mode», aggiornare tutti e tre.
- **«The local-login hold»** (ch14 S6): citato da ch01, ch02 (3x), ch03 (4x), ch13 (2x), ch14 (3x), ch15 (3x), ch16, ch17, ch18, ch22 (21 usi): NON cambiare il titolo.
- **«Local excludes remote and the session cap»** (ch14 S5): da ch02, ch12 (3x), ch13 (1x): tenere.
- **«GNOME: headless Shell and session dconf»** (ch12 S6): da ch10, ch12 (4x), ch14 (2x): tenere.
- **«The four desktops side by side»**: ch12 (4x), ch14: tenere.
- **«KDE Plasma: KWin nested in labwc»** (ch12 S7): citato solo in ch12 S1; se il titolo diventa «KDE Plasma: KWin alone» aggiornare quel `rif`.
- **«The PAM service file remotix.pam»**: ch14 S6 (1x); **«What the security model does not defend»**: ch14 S8; **«The walls of the network side»**, **«The closed list between ...»**: solo ch14; **«What the login logs and what it never logs»**: ch13.
- Manuale utente: **«Ubuntu 26.04: installing»** (ch01, ch04, ch05), **«Ubuntu 26.04: the firewall»** (ch04, ch05), **«Ubuntu 26.04: the first visit and the certificate»** (ch02, ch03, ch05 x2), **«Ubuntu 26.04: port, name and other settings»** (ch02 x2, ch05), **«Ubuntu 26.04: who may connect»** (ch05): tutti i titoli «Ubuntu 26.04: ...» di ch02 vanno rinominati «Fedora 45: ...» e i `rif` aggiornati in blocco (in ch05 S_FILES c'e' anche un `rif` spezzato su due righe di codice). **«Users, groups and what REMOTIX changes»** (ch01, ch02 x3, ch03, ch04): tenere. **«Leaving and coming back»** (ch01 x2, ch03, ch05), **«The login defences»** (ch04 x2, ch05), **«Settings you can change»** (ch02, ch04 x2), **«What a restart of the service does»** (ch02, ch05): tenere. **«Known problems on Ubuntu 26.04»**: nessun `rif` verso di esso.
- Dal gruppo verso titoli di altri gruppi che DEVONO restare o aggiornarsi: **«Our own labwc (KDE)»** (ch15, citato da ch12 S7 e ch14 S8: da togliere insieme alla sezione di ch15), **«The lost frame (KWin)»** (ch06), **«Removal: prerm, postrm and purge»** (ch15: su Fedora e' `%preun/%postun`), **«Files the package installs»** (ch15), **«Extending REMOTIX and porting to another distribution»** (ch21/ch20), **«Appendix C — Known issues and open points»**, **«Stopping the service»** (ch03), **«Ending a graphical session»** (ch03), **«Where the log lines go»** (ch16), **«Screen capture»**, **«Input»**, **«Video encoding»**, **«Quality, degradation and budget»**, **«Performance and capacity»**, **«Logging and diagnostics»**, **«Testing»**, **«The package»**, **«Transport»**, **«Overall architecture»**, **«The RCP/1 protocol»**, **«Startup and life cycle»**: titoli degli altri gruppi, devono esistere ancora.

---------------------------------------------------------------------------------------------------

# Punti non verificati (riassunto)

1. Cifre dei giri e dei tempi Fedora (1,7 s, 0,7 s, 5,04 s, 5,9 s, 52/76/60/60 PASS, 39 `all.sh`): prese da `PIANO.md` e registro, non dai log (stanno sul server).
2. Numero di chiavi dconf in vigore su Fedora (verosimilmente 20 con valore: `ubuntu-lock-on-suspend` assente dallo schema Fedora) e contenuto di `password-auth`/`nsswitch.conf`/Landlock ABI/kernel di Fedora 45: non letti.
3. Se Plasma 6.8 ha ancora il difetto «plasma-shutdown non ferma il target» (il codice `session_kde_logout_watch()` e' invariato): non verificato.
4. Se GNOME 51 parte ancora nell'Overview e se `lock-warning-shown` serve ancora: non verificato.
5. Stato di serie del firewall di Fedora Workstation (zona `FedoraWorkstation`): non verificato (F20 solo sulle VM, zona `public`).
6. Percorsi esatti di licenze (`rpm -ql`) e nome/contenuto del pacchetto 1.2.0: il pacchetto non esiste ancora (spec dice 1.2.0, ultimo costruito `i2`, PIANO.md:454-455).
7. `power-implied` e `power-local-seat` su Fedora (caso del greeter): non provati (studio 1:401-407); `blueman`, `picom`, estensioni GNOME, `gnome-session` nella Spin XFCE: non controllati con `rpm -q`.
8. Conteggio «33 layouts» di `page.html` e conteggi `grep -c` delle regole polkit: non ricontati (nessun generatore girato).
9. Esiti dettagliati di `check-multiuser`/`check-phone` su GNOME (F34) e di `check-clipboard` su GNOME/KDE nel giro `h1`: non riletti.
10. Se `needrestart`/`dnf-automatic` rispetta la regola del pacchetto su Fedora; `firewall-cmd --add-rich-rule` (rete locale): non provato in questo albero.
