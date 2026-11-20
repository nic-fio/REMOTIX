# Studio 5 — Differenze di sistema fra Debian 13 e Ubuntu 26.04 (fuori dai desktop)

Agente di studio 5, 18 nov 2026. Solo studio: nessun file del prodotto toccato, nessuna prova del prodotto.
Argomento: AppArmor, snap, PAM/NSS, strumenti di base, firewall, polkit, systemd, needrestart/unattended-upgrades, gruppi.

Legenda: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione.
Sigle: `DEB` = `/home/nicfio/Documenti/REMOTIX-DEBIAN`, `OLD` = `/home/nicfio/Documenti/REMOTIX` (vecchio albero 1.5.x).
Fonte dei fatti su Ubuntu: contenitore `studio-5` (`docker.io/library/ubuntu:26.04`, 26.04.1) sul server, cartella
`/media/REMOTIX-UBUNTU/studio/5/` (estratti dei `.deb`, sorgenti `snapd 2.78` e `systemd 259.9` scaricati con `apt-get source`).
Limite: il contenitore usa il kernel del server (7.3, Debian), quindi **niente fatti sul kernel Ubuntu 26.04** (AppArmor in kernel,
mediazione `unix`/`dbus`, sysctl `apparmor_restrict_*`): quelli sono [S] fino alla prova su una vera VM Ubuntu.

## 0. Versioni trovate su Ubuntu 26.04 [V: `apt-cache policy`, contenitore]

| Pezzo | Ubuntu 26.04 | Debian 13 (dal codice/commenti, [S] dove non verificato) |
|---|---|---|
| systemd | 259.9-0ubuntu0.1 | 257 (`DEB/src/local_login.c:20` cita «systemd 257») |
| AppArmor (parser, dh-apparmor) | 5.0.2-0ubuntu1~26.04.1 (ABI `3.0 4.0 4.0-ip 5.0` in `/etc/apparmor.d/abi/`) | 4.1.x [S] |
| polkitd | 127-2ubuntu1.1 | 126 (`DEB/src/remotix-no-poweroff.rules`) |
| Linux-PAM (libpam-modules, libpam-runtime) | 1.7.0-5ubuntu3.2 | 1.7.0 [S] |
| coreutils | **rust-coreutils 0.10.0** (uutils) come `/usr/bin/{ls,stat,sort,timeout,install,cut,…}` (pacchetto `coreutils-from-uutils`); GNU 9.7 resta come `gnu-coreutils` | GNU |
| sudo | **sudo-rs 0.2.13** (`/usr/bin/sudo` → alternatives → `/usr/lib/cargo/bin/sudo`) | GNU sudo |
| sed / grep / awk | GNU sed 4.9, GNU grep 3.12, mawk 1.3.4 (gawk se installato) | uguali |
| dbus | dbus-daemon 1.16.2 (+ `dbus-user-session`) | uguale |
| snapd | 2.78+ubuntu26.04 | assente |
| ufw | 0.36.2, **`ENABLED=no`** in `/etc/ufw/ufw.conf` | non installato di serie |
| needrestart / unattended-upgrades | 3.11 / 2.12ubuntu9 | — |
| `/usr/sbin`, `/sbin` | `/sbin → usr/sbin` (symlink), `/usr/sbin` cartella vera | uguale (nessun «sbin merge») |

## 1. AppArmor

### 1.1 Come REMOTIX usa AppArmor (nessuna novità rispetto a Debian)

- Il binario REMOTIX **non usa** `bwrap`, `flatpak`, `unshare` da riga di comando né user namespace per sé: l'unico codice che crea namespace è `DEB/src/walls.c`,
  nel lato rete, **da root**: `clone(CLONE_NEWPID)` (walls.c:109-117), `unshare(CLONE_NEWNS)` (walls.c:696), `unshare(CLONE_NEWNET)` (walls.c:501). [V: grep di `CLONE_NEW|unshare|bwrap|setns|seccomp|userns|flatpak` in `src/`]
  Il filtro seccomp del lato rete (raw BPF, walls.c:82-107, 584-650) **vieta** `CLONE_NEWUSER` (EPERM) e `clone3` (ENOSYS), ma non crea nulla.
- `setns` non è mai usato. Nessun `bwrap`/`flatpak` chiamato dal prodotto o dagli script del pacchetto. [V]
- **Conseguenza: `kernel.apparmor_restrict_unprivileged_userns=1` non tocca REMOTIX.** La restrizione riguarda solo la creazione *non privilegiata* di user namespace;
  REMOTIX crea namespace di altro tipo, da root (CAP_SYS_ADMIN). [V per il codice; il comportamento del kernel Ubuntu è [S] fino alla prova]
- Su Ubuntu 26.04 i sysctl sono in `/usr/lib/sysctl.d/10-apparmor.conf`: `kernel.apparmor_restrict_unprivileged_userns = 1` **e**
  `kernel.apparmor_restrict_unprivileged_unconfined = 1`. [V: file del pacchetto `apparmor`] Nel contenitore non si possono leggere i valori veri del kernel.
- Il lato rete entra nel profilo con `exec remotix_network` scritto in `/proc/thread-self/attr/apparmor/exec` (walls.c:177-258): nessun path di attacco,
  la radice e i desktop restano `unconfined`. Se AppArmor è spento o il profilo non è caricato: nota nel log e si va avanti (walls.c:211-235).

### 1.2 Profili di serie di Ubuntu 26.04 che toccano ciò che avviano le sessioni [V: `/etc/apparmor.d/` del pacchetto `apparmor` 5.0.2]

- Profili `abi <abi/5.0>` per: `firefox` (`flags=(unconfined)`, `userns`), `chrome`, `chromium`, `brave`, `epiphany`, `loupe`, `evolution`, `geary`, `thunderbird`,
  `QtWebEngineProcess`, `flatpak` (unconfined + `userns`), `bwrap-userns-restrict` (`/usr/bin/bwrap`, con sotto-profilo `unpriv_bwrap`: userns consentito, `deny capability`),
  `glycin.bwrap` / `glycin.loaders` (i caricatori immagini di GNOME), `fusermount3`, `podman`, `notify-send`, `plasmashell` (`/usr/bin/plasmashell`: `userns`, `unix`, `dbus`…, figli `pux`),
  `unix-chkpwd`, `Xorg_wrap` (complain), `unprivileged_userns`, e il nostro `remotix_network` quando installato. Totale 154 voci in `/etc/apparmor.d`.
- Nessun profilo di serie per `gnome-shell`, `kwin_wayland`, `labwc`, `xfce4-session`, `lxqt-session`, `pipewire`, `wireplumber`: restano `unconfined`. [V: lista completa letta]
- I profili si attaccano **per percorso dell'eseguibile**, non per chi è il padre: una sessione avviata da REMOTIX e una avviata da GDM/SDDM/LightDM ricevono gli stessi profili.
  Quindi la restrizione userns/unconfined colpisce le app in sessione REMOTIX esattamente come in sessione locale (Chromium non-snap, Electron, app Flatpak, ecc.). [S, conseguenza logica; da vedere con una prova]
- `snap-confine` ha il suo profilo (`/etc/apparmor.d/usr.lib.snapd.snap-confine.real`, pacchetto snapd).

### 1.3 Il nostro profilo `remotix_network` su Ubuntu 26.04

- Installazione: `DEB/debian/rules` (`execute_after_dh_auto_install`: copia in `/etc/apparmor.d/remotix_network` e `dh_apparmor --profile-name=remotix_network -premotix`).
  Lo snippet di `dh-apparmor 5.0.2` che finisce nel postinst [V: `/usr/share/debhelper/autoscripts/postinst-apparmor`]: crea `/etc/apparmor.d/local/remotix_network` vuoto
  con `install --mode 644 /dev/null …` (provato con `install` di uutils: funziona) e, se `aa-enabled --quiet`, `apparmor_parser -r -T -W`.
  Il profilo ha `flags=(complain,attach_disconnected)`: resta in **complain** (nessun rifiuto). Il file **non** contiene `include if exists <local/remotix_network>`:
  il file `local/` creato da dh_apparmor non serve a niente (piccolo, uguale su Debian). [V]
- **Il profilo è identico fra vecchio e nuovo albero** (`diff` delle righe non commento: vuoto) e non è mai stato provato su Ubuntu (assessment: «R-SEC-028 AppArmor… non verificabili nel box»,
  `OLD/assessment/gnome/ubuntu2604.md:39`). Su Debian 13 è stato caricato e provato in complain (0 rifiuti fino alla connessione).
- **Sintassi/ABI [V]**: `apparmor_parser -QTK -S` del profilo con il parser 5.0.2: rc=0, nessun avviso, sia senza riga `abi`, sia con `abi <abi/5.0>` forzata, sia con `abi <abi/4.0>`.
  Il profilo non ha riga `abi`: con il parser nuovo il comportamento di default è quello delle feature del kernel in uso (le classi `userns`, `io_uring`, `mqueue` non elencate saranno
  negate in enforce: voluto, il seccomp le nega già). Fissare `abi <abi/5.0>` sarebbe opzionale (su Debian 13 la 5.0 non c'è).
- `abstractions/nis` (inclusa da `nameservice`) aggiunge `capability net_bind_service`: il profilo la ha, contro il commento «nessuna capability». Innocuo (il processo ha il bounding set vuoto),
  uguale su Debian. [V: `--debug` del parser; `abstractions/nis:16`]
- **Mediazione `unix` di Ubuntu [V sul parser, S sul kernel]**: con ABI 5.0 `network unix stream/dgram` si compila anche in regole `unix` complete: i `connect` verso
  `/run/dbus/system_bus_socket`, il journal, `/var/lib/sss/pipes/nss` restano permessi. `deny unix addr=@*` nega gli abstract socket (nessuno ne serve: il lato rete vive in un netns suo, walls.c:486-497).
  Il kernel Debian 13 (6.12) non media `unix`; quello Ubuntu sì [S]: la differenza si vede solo passando a enforce.
- **Problema vero per l'enforce, trovato nei pacchetti [V]**: su Ubuntu 26.04 `xkb-data 2.46-2` ha i dati in `/usr/share/xkeyboard-config-2/` e `/usr/share/X11/xkb` è un **symlink** a quella cartella
  (`dpkg-deb -c xkb-data`). AppArmor giudica sul percorso risolto, quindi le righe `/usr/share/X11/xkb/ r, /usr/share/X11/xkb/** r` del profilo **non coprono** la vera cartella.
  Inoltre `libxkbcommon0 1.13.1` cerca anche `/etc/xkb`, `/usr/share/xkeyboard-config-2.d` (stringhe della libreria). Il lato rete compila la keymap (`keyboard.c:424`, `wlr_input.c:633` — controllare quale processo la compila).
  In complain: righe ALLOWED nel log; in enforce: tastiera morta. Su Debian 13 (xkb-data 2.42, cartella vera) funzionava [S]. Cura: aggiungere le tre cartelle al profilo.
- Altro da verificare con `aa-status`/log in complain su Ubuntu: letture di `libnss_systemd` (`/run/systemd/userdb/`), `libnss_sss` (`/var/lib/sss/pipes/nss`, già in `nameservice`), `/etc/ssl` (abstraction `crypto`),
  regola `dbus` (il profilo non ha regole `dbus`; `nameservice` ne porta alcune per systemd1/resolve1; Ubuntu **ha** il supporto kernel AppArmor per `dbus` [S] e `dbus-daemon` è compilato con libapparmor [S]: il lato rete parla con logind via bus di sistema — in enforce potrebbe servire una regola `dbus send/receive bus=system`).
- DNS: il lato rete nel suo netns senza interfacce non risolve nomi; il codice usa solo `getnameinfo(NI_NUMERICHOST|NI_NUMERICSERV)` (transport.c:350, page.c:2057) e `getaddrinfo` su indirizzo numerico (page.c:2301, transport.c:2664). Su Ubuntu `systemd-resolved` (127.0.0.53) sarebbe irraggiungibile: non serve. [V grep]

## 2. snap

### 2.1 Che cosa serve a uno snap per partire in una sessione REMOTIX [V: sorgente `snapd 2.78`, `sandbox/cgroup/tracking.go`; `.deb` snapd; Firefox 1:1snap1-0ubuntu9.1]

- `firefox`, `thunderbird`, `chromium-browser` su Ubuntu 26.04 sono pacchetti **transitori** (`Pre-Depends: snapd (>= 2.54)`) che alla prima installazione fanno `snap install firefox` (preinst; salta se non c'è un snapd funzionante, `/run/snapd.socket`).
  `/usr/bin/firefox` è solo uno script che richiede `/snap/bin/firefox` (percorso assoluto) e poi usa `xdg-settings`, `gsettings`, `sed`, `cut`.
- Avvio di uno snap: `snap run` → `snap-confine` (setuid root, `/usr/lib/snapd/snap-confine`, profilo AppArmor suo) → `snap-exec`. Servono:
  1. **setuid effettivo**: il processo utente non deve avere `no_new_privs`. **REMOTIX non lo imposta nei figli dell'utente** (PR_SET_NO_NEW_PRIVS solo nel lato rete, walls.c; grep di `NO_NEW_PRIVS|capset|PR_CAP` in child.c/session.c/rootside.c: nulla). Il servizio non ha `NoNewPrivileges`. [V] Stesso discorso per `sudo`, `pkexec`, `fusermount3`.
  2. **bus di sessione**: `CreateTransientScopeForTracking` crea lo scope `snap.<app>.<app>-<uuid>.scope` via D-Bus verso `systemd --user` (bus di sessione; per uid ≠ 0 non c'è ripiego sul bus di sistema). Se il bus manca l'app parte lo stesso ma senza tracciamento cgroup (errore solo in debug). REMOTIX imposta `XDG_RUNTIME_DIR` e `DBUS_SESSION_BUS_ADDRESS` (child.c:1783-1790; session.c:2442-2461). [V]
  3. **Wayland**: l'interfaccia snap `wayland` consente socket `/run/user/<uid>/wayland-<N>` [S dal profilo generato da snapd]. I socket creati dai compositor REMOTIX sono `wayland-0..9` standard (wlroots.c:2041, kwin.c:331); il nested host di KDE è `…/remotix-kwin-host/wayland-0` ma non è per le app. [V grep]
  4. **`~/snap`** creata da `snap run` nella home: serve una home scrivibile (utenti creati con `useradd -m`/installer di Ubuntu: ok).
  5. **`snapd.session-agent.socket`** (unità utente in `/usr/lib/systemd/user/`, `WantedBy=sockets.target`, abilitata a livello globale dal postinst con `deb-systemd-helper --user enable`): parte con lo user manager, che è quello di logind (`user@UID.service`) e quindi c'è anche in sessione remota. [V file; S effetto]
  6. **`XDG_DATA_DIRS` con `/var/lib/snapd/desktop`** (altrimenti Firefox sparisce dai menu): lo mette `/usr/lib/environment.d/990-snapd.conf` nello **user manager** (`XDG_DATA_DIRS=${XDG_DATA_DIRS:-/usr/local/share/:/usr/share/}:/var/lib/snapd/desktop`, `PATH=$PATH:/snap/bin`). [V]
     REMOTIX compone l'ambiente da zero ma per `XDG_DATA_DIRS` parte dal valore dello user manager: `manager_value()` (session.c:2308-2365) → `session_data_dirs()` (2394-2402) → `add_session_names(…, with_data=TRUE)` (GNOME 2717, KDE 2492, XFCE 2534; LXQt no, `with_data=FALSE` a 2572 ma LXQt compone a 2602). Gli elementi sono accettati solo se assoluti e senza spazi/virgolette (`/usr/local/share/` e `/var/lib/snapd/desktop` passano). Quindi **su Ubuntu con snapd la lista arriva piena** [V codice; S effetto]. Il commento di DECISIONS §10.54 (`OLD/DECISIONS.md:7230`) dice proprio «Firefox as a snap» come caso d'uso.
  7. **Portali** (`xdg-desktop-portal`, `xdg-document-portal` che monta `/run/user/UID/doc` con `fusermount3`, profilo AppArmor `fusermount3` presente): il file chooser, `xdg-open` e l'apertura link di Firefox snap passano dal portale via bus di sessione. Servono nell'ambiente di attivazione `XDG_CURRENT_DESKTOP`, `WAYLAND_DISPLAY` ecc.: **è materia dei desktop** (agenti 1-4, 6, 7), la segnalo come dipendenza.
- **PATH della sessione [V]**: il figlio parte con `PATH=/usr/local/bin:/usr/bin:/bin` fisso (child.c:1786) e i desktop lo ereditano (session.c:2514 «inherits nothing except PATH»). Un login locale Ubuntu avrebbe via `pam_env` (`/etc/environment` di Ubuntu: `PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"`, [V nel contenitore]) anche `/snap/bin`, sbin, games.
  REMOTIX legge dall'ambiente PAM solo `XDG_SESSION_ID` (child.c:1802-1805), quindi **`/snap/bin` non c'è nel PATH del compositore**. Gli avviatori `.desktop` degli snap usano `/snap/bin/…` assoluto, ma un comando `firefox` digitato in un terminale o uno script che chiama `snap` senza percorso dipendono dal PATH finale (che dipende dall'unità `user@` e da cosa il desktop importa: `environment.d` di snapd aggiunge `/snap/bin` al manager). **Da misurare** (vedi prove).
- Fine sessione: gli snap vivono in scope transitori sotto `user@UID.service/app.slice`, non in `session-N.scope`. Come per le app GNOME, restano finché lo user manager non cade; il prerm usa `systemctl --user -M u@ stop graphical-session.target` (debian/remotix.prerm). Un Firefox snap aperto al logout potrebbe restare vivo un po' (prova «chiude e non lascia niente», C7/C24 vecchio albero).
- Tracce nel vecchio albero [V grep]: `OLD/DECISIONS.md:7230` (XDG_DATA_DIRS dal manager «Firefox as a snap»); `OLD/assessment/banchi/suite-2.md:45` («firefox-esr esiste solo su Debian: altrove si chiama firefox, o è uno snap su Ubuntu»);
  `OLD/phases/17-the-installer.md:1170` («firefox/thunderbird tenuti fuori con una preferenza apt, perché snapd non gira in una scatola»). **Non c'è mai stata una prova di Firefox snap dentro una sessione REMOTIX.**
- Per i test: il browser **cliente** dei test (`prove/browserlib.py:99,199`, `prove/lib.py:483,593`) gira sul server Debian (`firefox-esr`, `google-chrome`), non nella macchina Ubuntu: nessun impatto. Il test vecchio C8 (`OLD/benches/11-boxes/11-c8-…py:610`, «il secondo utente apre il browser») lancia `firefox-esr --headless --screenshot` **nella sessione**: su Ubuntu sarebbe lo snap, confinato (non scrive in `/tmp` né nelle cartelle nascoste, profilo in `~/snap/firefox/common/…`): va riscritto per Ubuntu.

### 2.2 Polkit e snap
`io.snapcraft.snapd.{login,manage,manage-interfaces,manage-configuration,manage-fde}`: `allow_any=auth_admin`, `allow_active=auth_admin_keep` [V]. Nessuna finestra non richiesta all'avvio (anche da seduto chiedono la password): non serve estendere la regola 40.

## 3. PAM e NSS

### 3.1 `remotix.pam` contro i `common-*` di Ubuntu 26.04 [V: contenitore con libpam-modules/-runtime 1.7.0-5ubuntu3.2, libpam-systemd 259, libpam-sss, openssh-server 10.2p1-2ubuntu3.8]
- `DEB/src/remotix.pam` (esclusa la riga `pam_listfile` e i commenti) è **riga per riga uguale a `/etc/pam.d/sshd` di Ubuntu 26.04** (estratto da `openssh-server_1:10.2p1-2ubuntu3.8`): 15 righe su 15. Conferma il confronto fatto il 30 set («identici fra loro»). Il file va quindi bene com'è. `pam_listfile.so`, `pam_nologin.so`, `pam_loginuid.so`, `pam_keyinit.so`, `pam_motd.so`, `pam_mail.so`, `pam_limits.so`, `pam_env.so`, `pam_selinux.so` (con `module_unknown=ignore`) esistono tutti.
- `common-*` di Ubuntu **con `libpam-sss` installato** (come Ubuntu Desktop: `ubuntu-desktop(-minimal)` ha `Recommends: libpam-sss`; lo ha anche `gdm3`, e per Kubuntu `libkscreenlocker6` [V `apt-cache rdepends`]):
  - `common-auth`: `[success=2 default=ignore] pam_unix.so nullok` → `[success=1 default=ignore] pam_sss.so use_first_pass` → `requisite pam_deny.so` → `required pam_permit.so`;
  - `common-account`: `[success=1 new_authtok_reqd=done default=ignore] pam_unix.so`, deny, permit, **`sufficient pam_localuser.so`**, `[default=bad success=ok user_unknown=ignore] pam_sss.so`;
  - `common-session`: `pam_permit` (default=1), deny, permit, `pam_umask`, `pam_unix`, `optional pam_sss.so`, `optional pam_systemd.so`;
  - `common-session-noninteractive`: senza `pam_sss` né `pam_systemd`; `common-password`: `pam_pwquality retry=3`, `pam_unix … yescrypt`, `pam_sss.so use_authtok`.
- Moduli in più rispetto a Debian: `pam_sss`, `pam_sss_gss` (da libpam-sss), `pam_localuser`. `pam_faillock` c'è nel pacchetto ma **non** è abilitato di serie (nessuna riga). `pam_lastlog` non esiste più (1.7); `libpam-lastlog2` è un pacchetto a parte e non è nello stack sshd/remotix. `pam_gnome_keyring` e `pam_kwallet5` sono nei file di gdm/lightdm/sddm ma **non** nel nostro stack né in sshd: i portachiavi non si sbloccano con la password REMOTIX (**uguale a Debian**, scelta D3; da sapere: su Ubuntu Desktop/Kubuntu i primi programmi che usano il portachiavi/KWallet chiederanno lo sblocco).
- `/etc/pam.d/other` di Ubuntu = `@include common-*` come Debian (protezione I7 invariata).
- `pam-auth-update` (agganciamento al login locale): provato nel contenitore con `DEB/debian/remotix.pam-config`: `--package` aggiunge `session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login` in `common-session` **dopo `pam_systemd`** (Priority -1) e non in `-noninteractive`; `--remove remotix` la toglie; riaggiungere funziona. [V]
- I PAM di login locale di Ubuntu includono tutti `common-session`: `gdm-password`, `gdm-autologin`, `gdm-fingerprint`, `gdm-smartcard-*`, `sddm`, `sddm-autologin`, `lightdm`, `lightdm-autologin` (esclusi i `*-greeter` / `gdm-launch-environment`). [V file dei pacchetti gdm3 50.1, sddm 0.21, lightdm 1.32] Il gancio `remotix-local-login` (che esce se manca `XDG_SEAT`) quindi scatta su tutti e quattro i gusti. Il greeter di sddm/lightdm passa anche lui da `common-session` ma senza seat utente reale: l'helper già non fa nulla senza seat [S: da provare].
- `pam_motd.so motd=/run/motd.dynamic` nello stack: su Ubuntu esegue ad **ogni** apertura di sessione root-side gli script `/etc/update-motd.d/*` (da `update-notifier-common`: `90-updates-available` che può lanciare `notify-updates-outdated`; `ubuntu-release-upgrader-core`: `91-release-upgrade`; più `95-hwe-eol`, `98-*`, e se presenti `landscape-common`, `motd-news`). Su Debian non ce ne sono. Latenza al login: **[S] da misurare** (potrebbe aggiungere da frazioni di secondo a qualche secondo nella nascita della sessione; la nascita ha un'attesa massima di 15 s, `child.c`).

### 3.2 NSS e il difetto «nome inesistente → 0x0E in 1,2 s invece di 0x07 in 2,7 s»
- Su Ubuntu Desktop `nsswitch.conf` ha `passwd: files systemd sss` (riga di `libnss-sss`: provato, dopo l'installazione di `libnss-sss` nel contenitore `/etc/nsswitch.conf` diventa `passwd/group/shadow: files systemd sss`, `gshadow: files systemd`, `netgroup: nis sss`). [V] `sssd` è `Recommends` di `libpam-sss`/`libnss-sss` ma non gira senza `/etc/sssd/sssd.conf`. Su Ubuntu **Server** non c'è `libpam-sss`; su Xubuntu/Lubuntu non risulta [S].
- **LA CORREZIONE GENERALE APPROVATA IL 16 NOV È GIÀ NEL CODICE DEBIAN ATTUALE — con certezza [V lettura del codice, `DEB/src/rootside.c`]:**
  - `root_user_lookup()` (rootside.c:~660-685) e `user_refused_as()` (688-756): un errore di `getpwnam_r` (`e != 0`) torna **2** (rootside.c:711-718, testo «not verified: lookup error», senza nome), nome assente → 1, uid 0 → 1.
  - `handle_auth()` (rootside.c:1165): il ramo `(r = user_refused_as(...)) != 0 || !rhost_ok(...)` (1195) fa **`out = RXR_NO`** (1210) per **qualsiasi** `r != 0`, quindi anche per l'errore di ricerca (r=2). Commento 1205-1214: «Step 2 (F2, decision 2 of 16 Nov 2026) … Ubuntu Desktop: `sss` in nsswitch.conf and no sssd running … Now it is RXR_NO: 0x07 at the same floor, counted by the network side like a wrong password».
  - Lato rete `helper.c:1009-1025`: `RXR_NO` è un rifiuto normale e conta (`RXR_NOT_CHECKED` resta solo per i limiti del lato root e i guasti nostri); il pavimento dei rifiuti è `REJECT_FLOOR 2500` (`rcp.c:245`, `rcp.c:10307-10319`).
  - Anche il ramo PAUSED (1230-1243) risponde RXR_PAUSED (stesso byte e stesso tempo) per non rivelare nomi.
  - Il vecchio punto «src/rootside.c ~698» era l'antico `0x0E` (`OLD/assessment/RAPPORTO.md` F2); il codice DEB ha già la cura. `DEB/docs/INVENTARIO-non-debian.md:49` lo conferma («the code handles a lookup failure generally; keep»).
  - **Conseguenza per il PIANO Ubuntu: il punto 3.e («Nome utente inesistente: stessa risposta e stesso tempo di una password sbagliata») non richiede codice**: richiede solo una **prova** su Ubuntu GNOME (nome inesistente vs password sbagliata: stesso byte 0x07, stesso tempo ≥ 2,5 s). Questo contraddice il PIANO (`REMOTIX-UBUNTU/PIANO.md`, passo 3e, file `src/rootside.c`).
- Restano punti dove un NSS lento/rotto conta: `child.c:1034` (`name_resolution`, nel figlio), `child.c:1305`, `child.c:2508` (`getpwnam_r` alla nascita: fallimento → «NO child», non è un rifiuto per l'utente), `authentication.c:211` (solo tag di log). Con `sss` non attivo la risposta di `sss` è immediata, ma con `sssd` configurato e irraggiungibile la lookup può bloccare (commento child.c:156-160); invariato rispetto a Debian.
- Una password **sbagliata** di un utente esistente: lo stack Ubuntu (`pam_unix` ignore → `pam_sss` ignore se sssd non risponde → `pam_deny`) rifiuta; già misurato 2,7 s sul vecchio banco G-Ub. [W/V vecchio albero] Da riconfermare.

## 4. Strumenti di base diversi (rust-coreutils, sudo-rs)

Su Ubuntu 26.04 `ls stat sort cut timeout install sleep head cat rm rmdir mkdir echo printf…` sono **uutils 0.10.0**; `sed`, `grep`, `find`, `awk` restano GNU/mawk; `setsid`, `runuser`, `logger`, `getent`, `loginctl`, `systemctl`, `usermod`, `gpasswd`, `userdel`, `groupdel` sono di util-linux/shadow/systemd (uguali a Debian). `/bin/sh` = dash. [V]

### 4.1 Comandi esterni chiamati dal prodotto (da `src/`)
| Comando | Dove | Esito su Ubuntu 26.04 |
|---|---|---|
| `/usr/sbin/usermod -aG <gruppo> <utente>`, ripiego `/sbin/usermod` | child.c:2414-2431 | ok: `/usr/sbin/usermod` esiste (shadow 4.17.4); `/sbin` è symlink |
| `setsid --fork sh -c …` | session.c:3432 | ok (util-linux 2.41.3, non coreutils) |
| `systemctl --user show|daemon-reload|try-restart|is-active|stop|reset-failed|is-system-running` | session.c:2865, 2923, 3534, 3628, 3959, 5354, 6524, 7095, 7164, 7180 | ok (systemd 259) |
| `dconf compile|read` | session.c:1685, 2041 | n/a su Ubuntu minimale: `dconf-cli` va in Depends/Recommends (già in Recommends) |
| `xfconf-query` | session.c:4738… | desktop (agente 7) |
| `labwc`, `wlr-randr`, `kwin_wayland_wrapper`, `gnome-shell`, `startplasma-wayland`, `xfce4-session` | session.c, kwin.c | desktop |
| `loginctl`, `timeout`, `logger` (scritti negli script di sessione LXQt) | session.c:5730-5760 | `timeout` = uutils: provato `timeout 3 sleep 5` → rc 124, `timeout 30 true` → 0 ✓ |
| `sh`, `exec` | session.c | dash ✓ |
| Binario REMOTIX con `--encoding-test`, `--drop-render-grants` | postinst/prerm | proprio |

### 4.2 Comandi esterni degli script del pacchetto (`DEB/debian/*.postinst|prerm|postrm|preinst`, `src/remotix-polkit-seated`)
`systemd-sysusers`, `systemd-tmpfiles`, `pam-auth-update`, `grep -q[xF]`, `command -v`, `timeout 30`, `loginctl list-sessions --no-legend / show-session -p X --value / terminate-session`, `awk '{print $1}'`, `systemctl is-active -q / kill --kill-whom=all --signal=SIGKILL / --user -M u@ stop`, `sleep 1`, `deb-systemd-invoke`, `stat -c %u`, `sed -n 's/…/…/p'`, `sort -u`, `gpasswd -d`, `rm -f/-rf`, `install -d -m 0755`, `getent passwd`, `cut -d: -f3`, `head -n 1`, `runuser -u … -- sh -c`, `userdel`, `groupdel`, `rmdir`, `printf`, `cat`.
Provati nel contenitore Ubuntu [V]: `stat -c %u /etc/passwd` → 0; `sort -u` (con spazi e a capo) ok; `cut -d: -f3` ok; `head -n 1` ok; `install -D -m 0755` e `install -d -m 0755` ok (modo e proprietario corretti);
`sleep 1` ok; `sed -n 's/.*"user":"\([^"]*\)".*"group":"\([^"]*\)".*/\1 \2/p'` ok; `sed -n 's/^UID_MIN…/\1/p' /etc/login.defs | head -n 1` → 1000; `grep -qxF` ok; `awk` (mawk e gawk) legge `<allow_active>` dalle policy polkit (`yes` per le tre azioni provate); `install --mode 644 /dev/null …` (dh_apparmor) ok.
**Nessun comando del prodotto o degli script del pacchetto si comporta in modo diverso con uutils.**
`systemd-sysusers`: il file `remotix.sysusers` (`u remotix - "…" / /usr/sbin/nologin`) crea utente e gruppo senza errori con systemd 259 (`--root`); `systemd-tmpfiles --create remotix.conf` crea `/var/lib/remotix`, `/run/remotix/net` con modo e proprietario voluti. `/usr/sbin/nologin` esiste. `systemd-analyze verify remotix.service`: nessun messaggio. [V]

### 4.3 sudo-rs (solo nei test, non nel prodotto)
- Il prodotto e gli script del pacchetto non chiamano `sudo` (solo un testo di aiuto nel postinst: `sudo /usr/libexec/remotix/remotix --encoding-test h264`, ok con sudo-rs).
- **`prove/check-desktop.py:299-302`** (eseguito *dentro* la sessione dell'utente) lancia `sudo -n true` e considera guasto se l'uscita **non** contiene «password» né «not in the sudoers». Con sudo-rs: utente non in sudoers → `sudo: I'm sorry tu. I'm afraid I can't do that` (rc=1); utente nel gruppo `sudo` → `sudo: interactive authentication is required` (rc=1) — **nessuna delle due frasi attese** ⇒ falso guasto su Ubuntu. [V provato nel contenitore] Cura: controllare `rc != 0` (e/o le due frasi nuove). Piccolo, solo test.
- `prove/check-resilience.py:154`, `boxes/box.sh:29`, `server/prepara-server.sh:17` usano `sudo -S -p ""` sull'**host Debian del server**: invariati. `sudo-rs` accetta comunque `-S -p ""` [V: provato `echo | sudo -S -p "" true` → 0].
- Lo scambio di `su`: `/usr/bin/su` è di util-linux (setuid), non cambiato.

## 5. Firewall
- `ufw` è **raccomandato** (`Recommends: ufw` in `ubuntu-standard`) e di serie **spento** (`ENABLED=no`, `/etc/ufw/ufw.conf`); policy `DEFAULT_INPUT_POLICY="DROP"`, `DEFAULT_APPLICATION_POLICY="SKIP"`; unità `ufw.service` oneshot. [V]
- `debian/remotix.ufw` (`ports=7447/tcp|7447/udp`) copiato in `/etc/ufw/applications.d/remotix`: `ufw app list` lo vede, `ufw app info REMOTIX` mostra 7447/tcp e 7447/udp. [V] Quindi su Ubuntu: nulla da cambiare; se l'utente abilita ufw serve `ufw allow REMOTIX`. Il difetto «porta fissa 7447 se si usa `--port`» (F20 del vecchio rapporto) resta.
- `nftables` è nei Depends di `ubuntu-standard` ma senza regole di serie [V: `apt-cache depends`; regole vere non verificabili].

## 6. polkit
- polkitd 127: gruppi amministratori: `/usr/share/polkit-1/rules.d/49-ubuntu-admin.rules` → `unix-group:sudo` e `unix-group:admin` (pacchetto polkitd); `50-default.rules` → `sudo`. `empower.rules` (gruppo `empower`, dal pacchetto `systemd`: `run0 --empower`, risponde YES a tutto). [V]
- Le nostre regole: `40-remotix-remote-sessions.rules` usa `isInGroup("wheel")||"sudo"||"admin"`: copre Ubuntu (sudo/admin). Le azioni nominate esistono tutte con i valori che il commento si aspetta: `org.freedesktop.packagekit.system-sources-refresh` (any=auth_admin, active=yes), `Flatpak.metadata-update`/`appstream-update`/`modify-repo` (active=yes), `NetworkManager.network-control` (active=yes). L'`awk` dell'helper `remotix-polkit-seated` legge `yes` per tutte. [V: policy estratte da packagekit 1.3.4, flatpak 1.16.6, network-manager 1.54.3]
- `50-remotix-no-poweroff.rules`: le **15** azioni login1 esistono tutte in systemd 259 (`org.freedesktop.login1.policy`: power-off/reboot/halt/suspend/hibernate con `-multiple-sessions` e `-ignore-inhibit`). [V] Altre azioni login1 di 259 non ostili: `set-reboot-to-firmware-setup`, `…boot-loader-menu`, `…boot-loader-entry`, `set-wall-message`, `chvt`, `attach-device`, `flush-devices`, `lock-sessions`, `manage`, `inhibit-*`, `set-self-linger`, `set-user-linger`, `set-reboot-parameter` (come sul 257).
- `polkit.service` di Ubuntu (identico a Debian, pacchetto uguale): `PrivateNetwork=yes`, `ProtectHome=yes`, `ProtectSystem=strict`, `NoNewPrivileges=yes`, `RestrictAddressFamilies=AF_UNIX`; l'helper `polkit.spawn(remotix-polkit-seated)` legge solo `/run/systemd/sessions/*` e `/usr/share/polkit-1/actions/*.policy`: compatibile. Il censimento polkit del 14 nov era già stato fatto anche su Ubuntu 26.04 (commento in `remotix-remote-sessions.rules`), log perduti col server azzerato. [V file; S esito runtime]
- Nuove finestre non richieste potenziali: `io.snapcraft.snapd.*` sono `auth_admin` anche da seduti (nessun trattamento). Nessun altro nuovo azione `allow_active=yes` che un utente remoto veda come finestra è emerso; un censimento su VM vera resta consigliato.

## 7. systemd 259 contro 257

### 7.1 ⚠ SCOPERTA GROSSA: il «filo della sessione» di logind non è più un fifo
- Debian 13 (systemd 257): logind tiene la sessione viva con un **fifo** `/run/systemd/sessions/<id>.ref`. `child.c:1713-1739` lo cerca fra i descrittori aperti (`readlink` → `/run/systemd/sessions/*.ref`), gli toglie il CLOEXEC e lo passa con `--session-fd` al nuovo programma. Fu necessario («misurato 17 nov sulle quattro scatole») perché l'`execve` chiudeva il fifo e la sessione diventava «closing» dopo 0,1 s.
- **Ubuntu 26.04 (systemd 259.9): [V `NEWS` di systemd 259.9, `src/login/pam_systemd.c:1277-1288`, `src/login/logind-session.c:604-607`]** dalla v258 «logind's session tracking, which used to be performed via a FIFO installed in the client, now uses PIDFDs. The file descriptor returned by CreateSession() … is therefore unused. Moreover, **the exit of the session leader process will immediately cause the session to be stopped**». `pam_systemd` riceve un descrittore finto (non un fifo) e non lo conserva (`sd_is_fifo(...) > 0` falso).
- Conseguenze sul codice DEB [V lettura; S effetto]:
  1. `child.c:1720-1735` **non troverà nessun fifo** e scriverà `child: ⚠ the logind session's fifo was not found: the session will close at the exec` — avviso **falso e fuorviante** su 259 (nessun `--session-fd` passato: `child.c:1920`; il ramo è già gestito a -1).
  2. Il «leader» è il processo che chiama `pam_open_session`: nel codice è il figlio che poi fa `execve("remotix-child")` (child.c:1933): **il pid non cambia con l'execve**, quindi la sessione dura quanto `remotix-child`. Se `remotix-child` termina, la sessione si ferma subito, anche se restano processi del desktop. Con il fifo era lo stesso (solo il leader lo teneva), quindi in pratica nessun cambio atteso — ma il caso Debian «closing con leader vivo» (Q7, F9 del vecchio rapporto: «Ubuntu… mostrano `active`») cambia natura.
  3. I file di stato di logind mantengono `SERVICE=`, `USER=`, `SEAT=`, `LEADER=`, `REMOTE_HOST=` (logind-session.c:318-352): `remotix-polkit-seated` e `prerm` (`loginctl … -p Service --value`) continuano a funzionare. Il `.ref` che l'helper salta (`*.ref`) non esiste più (innocuo).
  4. `systemd.session-fd` rimane solo se un logind **più vecchio** della 258 è ancora in esecuzione durante un aggiornamento (commento pam_systemd.c:1277-1279): caso raro, il codice deve restare tollerante.
- **Da provare davvero** (passo 2 del piano): login remoto → sessione `active` stabile; stop del servizio → desktop chiusi (§11.56); riavvio del servizio con desktop vivi → riattacco; uscita (Log Out) → sessione e scope spariscono; `loginctl show-session` mostra `Leader`, `Service=remotix`, `Seat` vuoto.

### 7.2 Altre differenze di systemd 259 rilevanti
- cgroup v2 solo (la 258 ha tolto cgroup v1) [W/NEWS]: nessun uso di cgroup v1 nel prodotto [S].
- `remotix.service`: `systemd-analyze verify` pulito [V]. `KillMode=mixed`, `Restart=on-failure`, `RestartPreventExitStatus=78`, `LimitRTPRIO=20`, `LimitNICE=-11`, `EnvironmentFile=` con `-` e glob: tutte valide.
- `pam_systemd` 259 legge `XDG_SESSION_INCOMPLETE` (nuovo, pam_systemd.c:1795): REMOTIX non lo imposta, nessun effetto.
- `systemd-sysusers`, `systemd-tmpfiles`: provati sopra, ok. La `Z /var/lib/remotix/net` di tmpfiles non segue i symlink (come prima).
- Gruppi/`udev`: `render` creato da `udev` (`/usr/lib/sysusers.d/debian-udev.conf`: `g render -`), regola `SUBSYSTEM=="drm", KERNEL=="renderD*", GROUP="render", MODE="0660"` (`50-udev-default.rules:61`) e `TAG+="uaccess", TAG+="xaccess-render"` (`70-uaccess.rules:48`): come Debian. `video` GID 44, `audio` 29 (`basic.conf`); gruppo `input` non in `basic.conf` ma gestito da udev [S]. `child.c` legge il gruppo dal gid del nodo `/dev/dri/renderD*` (non per nome): indipendente dal nome. [V `usermod -aG` nome gruppo ricavato dal nodo]
- Ubuntu ha `kernel.yama.ptrace_scope=1` (`55-ptrace.conf`/`10-ptrace`) mentre Debian lascia 0 [S per Debian]: REMOTIX non usa ptrace né `pidfd_getfd`/`process_vm_*` (solo li nega: walls.c:622-625) [V grep]; la ricerca dei desktop da ritrovare è fatta da root.
- `systemd-oomd`: `ubuntu-desktop(-minimal)` ha `Recommends: systemd-oomd` (e `gnome-settings-daemon` lo raccomanda); il pacchetto porta `user@.service.d/10-oomd-user-service-defaults.conf` con `ManagedOOMMemoryPressure=kill`, limite 50% (e `oomd.conf.d`: `DefaultMemoryPressureDurationSec=20s`). Può uccidere lo `user@UID.service` (quindi la sessione remota di un utente) sotto pressione di memoria (server con molti utenti): [S] da tenere d'occhio, nessuna cura nota.

## 8. needrestart e unattended-upgrades (chiusura dei desktop, DECISIONS-11 §11.56)

- `unattended-upgrades` 2.12 è installato di serie su Ubuntu Desktop/Server (`APT::Periodic::Unattended-Upgrade "1"` in `20auto-upgrades`) e aggiorna dai canali `-security`/ESM. [V file; presenza di serie sul Desktop: S]
- `needrestart` 3.11 è **di serie su Ubuntu Server** (`ubuntu-server(-minimal)` lo raccomandano/dipendono) e **non** sul Desktop (`ubuntu-desktop` non lo nomina) [V `apt-cache depends`]; ha un hook `DPkg::Post-Invoke` (`/usr/lib/needrestart/apt-pinvoke -m u`).
- Comportamento [V: sorgente `/usr/sbin/needrestart:250-264, 1150-1170`; `needrestart.conf`]: in modalità non interattiva (`unattended-upgrades` / `-m u`) il valore `restart` diventa **`'a'` = riavvia da solo** i servizi con librerie aggiornate, salvo quelli in `$nrconf{override_rc}`. L'elenco di serie esenta (valore 0) `^gdm`, `^sddm`, `^lightdm`, `^xdm`, `^xrdp`, `^user@\d+\.service`, `^dbus`, `^systemd-logind`, `^NetworkManager`, `^getty@…` ecc.: **`remotix.service` non è in elenco** ⇒ dopo un aggiornamento di `libssl3`, `libc6`, `libpam*` ecc. `needrestart` riavvierebbe `remotix.service`, e per §11.56 **chiuderebbe tutti i desktop remoti** senza avviso (stessa cosa dell'`xrdp`, che gli sviluppatori di needrestart hanno infatti esentato).
- Cura (piccola, solo Ubuntu): installare `/etc/needrestart/conf.d/remotix.conf` con `$nrconf{override_rc}{qr(^remotix\.service$)} = 0;` (la cartella `conf.d` è già letta dal conf principale con `eval`). Con questa riga il servizio viene solo elencato fra «Services to be restarted manually». Le librerie più vecchie restano caricate: va dichiarato all'amministratore. Non rilevante su Debian: lì needrestart non è di serie.
- `unattended-upgrades` può anche aggiornare `remotix` stesso (se mai in un repo): `--restart-after-upgrade` nel `debian/rules` (override_dh_installsystemd) chiude i desktop; invariato.
- Le postinst di `libc6`/`libssl3`/`libpam0g` riavviano da sole solo servizi di un elenco noto (ssh, cron, display manager…) [S da conoscenza dei pacchetti; non verificato].

## 9. Utenti, gruppi, home, motd, altri dettagli

- `adduser`/Ubuntu: `UID_MIN 1000`, `UID_MAX 60000`, `USERGROUPS_ENAB yes`, `ENCRYPT_METHOD YESCRYPT` (`/etc/login.defs`) — uguale a Debian; `preinst` usa `UID_MIN` da lì [V].
- `/usr/libexec` esiste ed è usato da altri pacchetti (`polkit-agent-helper-1`, `awk`, `coreutils`, `rust-coreutils`, `dpkg`…): nessun problema per `/usr/libexec/remotix/` [V]. Esiste `/usr/libexec/coreutils` e `/usr/libexec/rust-coreutils` (curiosità: non conflitto).
- `remotix.service` usa `/bin/sh -c 'exec …'`: dash, ok. `%H`: nome macchina.
- `needrestart-session`, `update-notifier`, `apport` e `ubuntu-report` sono nel Desktop: possono avviare programmi nella sessione e mostrare notifiche (reboot-required, aggiornamenti, apport): [S] rumore ma non rotture; l'apport sostituisce `core_pattern` (non toccato dal prodotto).
- `dbus-user-session` (Depends del pacchetto) soddisfatta da `dbus-daemon` (di serie su Ubuntu 26.04: `Depends: dbus-daemon (= …) | dbus-broker`). [V]
- Pacchetti nel `Depends` di `DEB/debian/control` verificati presenti su Ubuntu 26.04: `libpam-systemd`, `libpam-runtime`, `libpam-modules`, `passwd`, `systemd`, `dbus-user-session`, `pipewire`, `wireplumber`; Recommends: `va-driver-all` (universe, vedi commento del control), `mesa-vulkan-drivers`, `labwc`, `dconf-cli`, `wlr-randr`, `xwayland`, `fonts-dejavu-core` [V per i primi; gli altri sono affare dell'agente 8].

## 10. Fatti che contraddicono il piano o gli studi precedenti

1. **PIANO.md, passo 3e e «File interessati: `src/rootside.c` (e)»**: la correzione «nome utente inesistente» **è già nel codice Debian 1.0.0** (rootside.c:1195-1232, helper.c:1009-1025). Serve solo la prova su Ubuntu GNOME, non una modifica. (Se Ubuntu parte da quel codice, il punto e si cancella dal piano.)
2. **Sessione logind su systemd 259**: il fifo `.ref` non esiste più (pidfd). Il codice che lo cerca stampa un avviso falso; l'assunzione «Ubuntu mostra `active`, Debian `closing`» del vecchio rapporto potrebbe avere come causa proprio questa differenza. Non menzionato nel PIANO né (per quanto so) negli studi precedenti.
3. **PIANO «AppArmor su Ubuntu è più severo e mai provato in modalità severa»**: il profilo parsa pulito con 5.0.2; il rischio vero in enforce è nei percorsi (xkb: `/usr/share/xkeyboard-config-2`, symlink) e forse nelle regole `dbus`, non nella sintassi/ABI.
4. **PIANO «Studio del 18 nov: AppArmor resta come su Debian»**: vero per sintassi e installazione; **falso per il contenuto** in enforce (punto sopra). In complain nessun cambiamento.
5. **PAM**: confermato che `remotix.pam` = `sshd` di Ubuntu 26.04: nessuna modifica necessaria.
6. **Test (`prove/check-desktop.py:301`)** presuppone il testo di GNU sudo: fallirà su Ubuntu per sudo-rs.

## Problemi da affrontare

| # | Che cosa | Dove nel codice | Peso | Cura nel vecchio albero |
|---|---|---|---|---|
| 1 | Profilo AppArmor, enforce: aggiungere `/usr/share/xkeyboard-config-2/**`, `/usr/share/xkeyboard-config-2.d/**`, `/etc/xkb/**`, `/etc/X11/xkb/**` (xkb-data 2.46: `/usr/share/X11/xkb` è un symlink) | `debian/remotix_network.apparmor` righe xkb | piccolo (in complain nessun effetto) | no (profilo uguale; non provato su Ubuntu) |
| 2 | Profilo AppArmor, enforce: verificare/aggiungere regole `dbus` (bus di sistema → logind), `/run/systemd/userdb/`, eventuali altre righe viste solo in complain su Ubuntu; poi il giro `complain→enforce` (consigliato dal commento: zero righe inattese) | `debian/remotix_network.apparmor` | medio (richiede giro di prova su VM Ubuntu) | no |
| 3 | `child.c`: avviso «session fifo not found» falso su systemd ≥ 258; capire se il passo `--session-fd` serve ancora (solo per logind < 258 durante un aggiornamento) | `child.c:1713-1739, 1920-1923, 10093` | piccolo | no |
| 4 | Sessione logind con pidfd: verificare chiusura/riattacco/stop servizio/«closing» su 259 | `child.c` (leader), `main.c`/`rootside.c` (chiusure), `remotix.prerm` | medio (solo prove, forse nulla da cambiare) | no |
| 5 | needrestart: `remotix.service` non esentato, riavvio automatico chiude i desktop | nuovo file `debian/remotix.needrestart` → `/etc/needrestart/conf.d/remotix.conf`; `debian/rules` | piccolo | no (su Debian non serve) |
| 6 | PATH della sessione senza `/snap/bin`, sbin, games rispetto a un login locale Ubuntu (e `LANG`/ambiente PAM non applicati: scelta dichiarata in child.c:1806-…) | `child.c:1786` e `session.c` (compose_environment, restore list a 3846) | piccolo-medio (dipende dall'esito della prova; la lista `XDG_DATA_DIRS` è già a posto) | parziale (D-153 per XDG_*; PATH no) |
| 7 | Firefox/Thunderbird/Chromium snap in sessione: mai provato (avvio, finestra su Wayland, portali, chiusura al Log Out, scope fuori da `session-N.scope`) | prove, non codice | medio (incognita) | no |
| 8 | Test `prove/check-desktop.py:299-302` (sudo-rs) e test C8-simili con `firefox-esr` | `prove/`, box | piccolo | n/a |
| 9 | `pam_motd` con gli script di `/etc/update-motd.d` di Ubuntu: latenza alla nascita sessione | `remotix.pam` (decisione D3: mirror di sshd) | piccolo, da misurare | no |
| 10 | `systemd-oomd` può uccidere lo `user@UID.service` dell'utente remoto | nessun codice; nota per l'amministratore o drop-in | piccolo, da decidere | no |
| 11 | Mancano `pam_gnome_keyring`/`pam_kwallet` nello stack (uguale a Debian): finestre di sblocco portachiavi su Ubuntu Desktop/Kubuntu | `remotix.pam` | piccolo, decisione del proprietario (D3 chiuso) | no |
| 12 | `include if exists <local/remotix_network>` mancante nel profilo (il file `local/` esiste ma è inutile) | `debian/remotix_network.apparmor` | minimo (uguale su Debian) | no |
| 13 | Commento di `remotix_network.apparmor` «nessuna capability» vs `abstractions/nis` che dà `net_bind_service` | profilo | minimo | no |

## Che cosa non si può sapere senza provare

- Comportamento del **kernel Ubuntu 26.04** (7.0?): valori reali di `apparmor_restrict_unprivileged_userns/unconfined`, mediazione `unix`/`dbus`, `/proc/thread-self/attr/apparmor/exec`, `features/` — il contenitore usa il kernel 7.3 Debian del server.
- Se in enforce il lato rete ha altri rifiuti (letture di `libnss_systemd`, `dbus`, `xkb`, `cgroup`) oltre a quelli previsti.
- Che cosa succede alle sessioni con pidfd (systemd 259): `active` stabile, stop del servizio, riavvio con desktop vivi, scope che sopravvivono o no.
- Se uno snap (Firefox) parte e funziona in una sessione di ognuno dei quattro gusti; se i portali trovano le variabili giuste; che cosa resta al logout.
- Il PATH reale visto dalle app lanciate in sessione (terminale, `.desktop`, `xdg-open`) su Ubuntu.
- La latenza di `pam_motd` (script `update-motd.d`) e di `pam_sss` con `sssd` assente al login e al rifiuto.
- Il tempo e il byte della risposta per nome inesistente su un vero Ubuntu GNOME con `sss` in nsswitch (il codice è a posto, il misurato manca).
- Se `needrestart` riavvia davvero `remotix.service` su Ubuntu Server dopo un aggiornamento di libreria, e che `override_rc` lo ferma.
- Quali finestre polkit non richieste compaiono su Ubuntu 26.04 in sessione remota (censimento del 14 nov perso).
- Effetto di `systemd-oomd` con più utenti remoti.

## Prove consigliate

1. **VM Ubuntu 26.04 (una per gusto)**: `journalctl -k | grep -i 'apparmor="ALLOWED"\|DENIED'` con `remotix_network` in complain durante il giro completo; poi giro in enforce (come da piano passo 5). Prima aggiungere le righe xkb (problema 1).
2. **Sessione e logind**: login remoto, `loginctl show-session <id> -p Leader -p Service -p State -p Seat`; poi: stop del servizio, restart con desktop vivi, Log Out, kill di `remotix-child`; controllare che l'avviso fifo compaia e non sia dannoso.
3. **Nome inesistente su Ubuntu GNOME** (`sss` in nsswitch, sssd spento): byte 0x07 e tempo ≥ 2,5 s identici a quelli di una password sbagliata; ripetere con sssd configurato e fermo. Nessuna riga di codice da toccare se riesce.
4. **Snap**: nella sessione di ciascun gusto aprire Firefox snap da menu, da terminale (`firefox`), con `xdg-open https://…`; scegliere un file con il file chooser (portale); `echo $PATH` nel terminale e in `systemctl --user show-environment`; Log Out con Firefox aperto → `loginctl list-sessions`, `systemctl --user -M u@ list-units 'snap.*'`, processi rimasti.
5. **needrestart** su Ubuntu Server con `remotix` e un desktop aperto: aggiornare una libreria (es. `libssl3` da `-proposed` o simulare con `needrestart -r a`); con e senza `/etc/needrestart/conf.d/remotix.conf`.
6. **PAM**: confronto riga per riga di `remotix.pam` con `/etc/pam.d/sshd` su ciascuna delle quattro immagini (il confronto di questo studio vale per openssh-server 10.2p1-2ubuntu3.8); misura del tempo di `pam_open_session` con gli script `update-motd.d` presenti (Desktop completo).
7. **Polkit**: censimento (`pkaction`, finestre) con un utente remoto su ciascuna immagine; verificare le tre azioni della regola 40 e i 15 divieti della 50 (`CanPowerOff` ecc. dal figlio, non da root).
8. **Test**: aggiornare il controllo `sudo` di `prove/check-desktop.py` e riscrivere il C8 per Firefox snap prima del giro 2.
9. **Pacchetto**: `apt install ./remotix_*.deb` su Ubuntu Desktop pulita e su Server: postinst (`pam-auth-update`, sysusers, tmpfiles, AppArmor `-r`), prerm/postrm; con `apparmor` assente (Recommends) il profilo deve semplicemente non caricarsi.
