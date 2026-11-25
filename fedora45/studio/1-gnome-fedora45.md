# Studio 1 — GNOME su Fedora 45 (Workstation): come nasce la sessione e che cosa deve cambiare in REMOTIX

21 nov 2026, agente di studio 1 (desktop GNOME, macchina virtuale `gnome`). Solo studio: nessun file del prodotto toccato,
il prodotto non è stato costruito, installato né provato.
Legenda: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione.
Abbreviazioni: `U` = `/home/nicfio/Documenti/REMOTIX/ubuntu26.04` (codice di riferimento); `G` = guest `rx-gnome`
(Fedora 45 Live 45-1.4 installata, SELinux enforcing, kernel 7.2.11-300.fc45); `SRC` = sorgenti dei pacchetti Fedora
scaricati nel guest in `/var/tmp/src/x/<pacchetto>/` (`dnf download --source`).
Studi Ubuntu usati come modello: `U/studio/1-gnome50-avvio.md`, `2-gnome50-chiusura-gdm.md`, `3-sessione-ubuntu.md`, `4-mutter50-cattura-input.md`,
`12-verifiche-gnome.md`; registro `U/docs/REGISTRO-problemi.md`.

---------------------------------------------------------------------------------------------------------------------------------

## 0. In breve

1. **Il codice di avvio GNOME di Ubuntu regge quasi com'è su Fedora 45.** Su Fedora 45 la sessione GNOME è `gnome` (file `gnome.desktop`,
   pacchetto `gnome-session-wayland-session`): la shell è il template `org.gnome.Shell@.service` istanza `@user`, identico alla struttura di
   GNOME 50 di Ubuntu. Provato su Fedora emulando la nascita come fa `child.c` (vedi §3.4): `gnome-shell --headless --no-x11 --mode=user`
   parte, Mutter risponde su D-Bus (`ScreenCast` v4, `RemoteDesktop` v1, `DisplayConfig`: 0 monitor, cioè «sessione viva e nera»), uscita
   in 1,3 s con soli due processi rimasti (leader e gestore utente). [V `G`]
2. **GRANDE — il file PAM `remotix` copiato da sshd (decisione D3) su Fedora NON FA PARTIRE nessun desktop.** Con la riga
   `pam_selinux.so open env_params` (nello stack di sshd di Fedora) il processo `unconfined_service_t` (dominio di un servizio installato da RPM)
   imposta come contesto di exec `unconfined_u:unconfined_r:unconfined_t`, e la `execve` successiva è NEGATA da SELinux
   (`AVC denied { transition } … path="/usr/bin/setsid"`, `execl: Permission denied`). Senza le righe `pam_selinux` il desktop parte. [V `G`, §9.2]
3. **GRANDE — niente H.264/HEVC hardware su Fedora di serie, nemmeno con la Radeon.** Mesa di Fedora è compilata con il valore predefinito
   `video-codecs=all_free`: con la RX 6800, `vainfo` mostra solo MPEG2/JPEG/VP9/AV1 in decodifica, e Vulkan non ha `VK_KHR_video_encode_h264/h265`.
   REMOTIX codifica solo H.264/HEVC in hardware (nessun ripiego software). Con RPM Fusion (`mesa-va-drivers-freeworld` +
   `mesa-vulkan-drivers-freeworld`) compaiono `VAEntrypointEncSlice` per H264/HEVC e le estensioni Vulkan di encode. [V Radeon `G`, §10]
4. **La regola «locale esclude remoto» serve identica anche su Fedora e il problema A1 si riproduce con GDM 51** [V `G`, §5]: con una sessione
   remota orfana in stato `closing`, l'accesso locale fa abortire `gnome-session-init-worker` (`A graphical session is already running!`,
   SIGABRT + core dump) 0,1 s dopo l'apertura. Con la sessione remota ancora attiva GDM 51 mostra «Session Already Running … a remote session
   is already running for prova2».
5. **L'aggancio a PAM per il gancio «locale» è il punto più delicato di Fedora** (authselect, §9.1): le righe messe a mano in `/etc/authselect/*`
   vengono cancellate da `authselect apply-changes`; resistono solo in un profilo `custom/…` che però sostituisce la scelta dell'amministratore.
   I file PAM di GDM stanno in `/usr/lib/pam.d` (non in `/etc/pam.d`) e includono `password-auth` (che porta `pam_systemd`) e poi `postlogin`.
6. **Il portachiavi non è più gnome-keyring: è `oo7-daemon`** (con `pam_oo7`). Nell'accesso locale da GDM la collezione «Login» è sbloccata; in
   una sessione remota nata senza `pam_oo7` è bloccata. [V `G`, §7]
7. **Flatpak funziona nella sessione remota senza nulla di speciale** (provato con gnome-calculator, utente prova2, sessione headless): niente di
   analogo agli snap di Ubuntu. [V `G`, §8]
8. **Il modello dconf di Ubuntu (profilo di runtime + `/etc/dconf/db/remotix`) regge su dconf 51 di Fedora.** Provato con `gsettings` senza
   `DCONF_PROFILE`: valore letto e blocco rispettato. [V `G`, §6] Il profilo di base di Fedora ha 4 righe (user-db + system-db local, site, distro).
9. Fatti utili: `openssl` 4.0.3 (non 3.x), `labwc` 0.20.2 e `wlroots` 0.20.2 nei repository (e `wlroots0.19`), Fedora Workstation ha il firewall con
   **1025-65535 tcp+udp già aperte** (la 7447 è raggiungibile di serie), `pam_faillock` NON attivo di serie, i servizi nuovi nascono disabilitati
   (`99-default-disable.preset`: `disable *`). [V `G`]

---------------------------------------------------------------------------------------------------------------------------------

## 1. Che cosa c'è su Fedora 45 Workstation (installazione dalla ISO Live 45-1.4)

### 1.1 Versioni [V `G`: `rpm -q`, `--version`]

| Componente | Fedora 45 (installato) | Nei repository ora (`dnf download --source`) | Ubuntu 26.04 (da studi `U`) |
|---|---|---|---|
| GNOME Shell | 51.0-1.fc45 | 51.1-1.fc45 | 50.1 |
| Mutter | 51.0-1.fc45 | 51.1-1.fc45 | 50.1 |
| gnome-session | 51.0-1.fc45 (+ `gnome-session-wayland-session`) | 51.0 | 50.1 |
| GDM | 51.0-1.fc45 | 51.1.1-1.fc45 | 50.1 |
| gnome-remote-desktop | 51.0-1.fc45 | 51.0-2 | 50.2 |
| systemd | 262-3.fc45 | 262.1 | 259.9 |
| PipeWire / WirePlumber | 1.6.9 / 0.5.18 | 1.6.11 / 0.5.19 | — |
| Xwayland | 24.1.13 | 24.1.15 | — |
| xdg-desktop-portal (+ `-gnome`) | 1.22.1 (+ 51.0) | — | — |
| dconf / glib2 / gtk4 / libadwaita | 51.0 / 2.90.0 / 4.24.1 / 1.10.0 | — | dconf 0.49 |
| polkit | 127-5 | 127 | — |
| firewalld / authselect | 2.5.2 / 1.8.0 | — | — |
| selinux-policy-targeted | 45.23 | 45.24 | — |
| Mesa | 26.2.3 | 26.2.7 | — |
| libva / vulkan-loader | 2.24.1 / 1.4.350.0 | — | libva 2.23 |
| dbus | **dbus-broker 37** | — | dbus-daemon (broker opzionale) |
| flatpak | 1.18.4 (versione dichiarata `1.19.0^really1.18.4`) | — | — |
| ffmpeg-free / openh264 | 9.0.2 / NON installato | — | — |

Nota: la ISO è «Live 45-1.4», con i pacchetti del giorno della ISO; i repository hanno già versioni successive (51.1 di shell e mutter,
GDM 51.1.1). Il banco di prova ha quindi 51.0; REMOTIX su una Fedora aggiornata girerà su 51.1+. Le differenze 51.0→51.1 non sono state
cercate nei sorgenti, tranne il NEWS di GDM (§5.4).

### 1.2 Sessioni offerte [V `G`]
- `/usr/share/wayland-sessions/`: `gnome.desktop` (`Exec=/usr/bin/gnome-session`, `DesktopNames=GNOME`, `X-GDM-SessionRegisters=true`,
  `X-GDM-CanRunHeadless=true`) e `gnome-classic.desktop` (`Exec=gnome-session --session gnome-classic`, `DesktopNames=GNOME-Classic;GNOME;`).
  Pacchetti: `gnome-session-wayland-session` (la normale) e `gnome-classic-session`. `/usr/share/xsessions/` è **vuota** (nessuna sessione X11).
- `/usr/share/gnome-session/sessions/`: `gnome.session`, `gnome-classic.session`, `gnome-login.session`, `gnome-initial-setup.session`.
- `os-release`: `ID=fedora`, `VERSION="45 (Workstation Edition)"`.
- **Effetto su `gnome_session()` (`U/src/session.c:890`, criterio D8):** i due candidati sono `gnome` e `gnome-classic`; nessuno ha il nome `fedora`,
  quindi la scelta cade sul passo 2 («quello di nome `gnome`», `SESSION_GNOME_FALLBACK`, `session.h:105`). Nessuna modifica necessaria. [S dalla
  lettura del codice: non eseguito]
- `Exec=/usr/bin/gnome-session` senza `--session`: `name_from_exec()` (`session.c:~818`) torna `gnome`. `TryExec=/usr/bin/gnome-session` esiste.
- Sessione accessoria da sapere: `gnome-session-wayland-session` può mancare in un'installazione minima: l'RPM di REMOTIX non deve dipenderne
  (REMOTIX non installa desktop) ma `gnome_session()` ricade nel «fallback dichiarato a `gnome`» e nel registro dirà `DECLARED FALLBACK`.

### 1.3 Servizi e unità di sistema rilevanti [V `G`]
- `gdm.service` abilitato; `graphical.target`; `gnome-remote-desktop.service` (di sistema) **disabilitato**, nessuna porta 3389/3390 in ascolto;
  `firewalld` e `sshd` abilitati; `auditd` attivo (gli AVC sono nel journal).
- Utente del greeter: **dinamico** `gdm-greeter` (uid 60578/60579 alle varie accensioni), sessione logind classe `greeter`, `Service=gdm-launch-environment`.
  Non esiste più l'utente `gdm`. (come GDM 50 di Ubuntu, §4.1 di `U/studio/2-…`).
- Il greeter gira con `gnome-session --session gnome-login`, shell `gnome-shell --mode=gdm`, e un suo user manager (`gdm-greeter`).

---------------------------------------------------------------------------------------------------------------------------------

## 2. L'accesso locale vero, osservato (termine di paragone)

Procedura: ISO installata, schermata di accesso GDM (virtio-vga), utente `prova`, password digitata con i comandi `tasti`/`scrivi` dello script
(la tastiera della VM è solo `us`: limite del banco, non conclusioni su Fedora). [V `G`]

- **Sessione logind** (`loginctl show-session`): `Type=wayland`, `Class=user`, `Seat=seat0`, `VTNr=2`, `TTY=tty2`, `Service=gdm-password`,
  `Remote=no`, `Display=` (vuoto: niente X), `Desktop=` vuoto, `Leader` = `gdm-session-worker [pam/gdm-password]` (processo di dominio `xdm_t`, ppid = gdm).
- **Catena dei processi:** `gdm-session-worker` → `/usr/libexec/gdm-wayland-session /usr/bin/gnome-session` → `gnome-session-init-worker gnome`
  (leader systemd, resta nello scope della sessione). Il resto sta sotto `systemd --user`: `gnome-session-service --session=gnome`,
  `gnome-session-ctl --monitor`, `org.gnome.Shell@user.service` = `/usr/bin/gnome-shell --mode=user`, `oo7-daemon`, `pipewire`, `wireplumber`,
  `pipewire-pulse`, 20 `gsd-*`, `xdg-desktop-portal(-gnome/-gtk)`, `xdg-document-portal`, `xdg-permission-store`, `ibus-daemon --panel disable`,
  `gnome-software --gapplication-service`, `localsearch-3`, `evolution-*`, `goa-daemon`, `gvfsd*`, `at-spi-*`, `uresourced`.
- **Contesti SELinux:** `gdm-session-worker` = `xdm_t`; tutti i processi dell'utente = `unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023`;
  `dbus-broker` utente = `unconfined_dbusd_t`; `(sd-pam)` = `init_t`. Quindi la sessione locale gira non confinata.
- **Ambiente di gnome-shell** (`/proc/<pid>/environ`): `DBUS_SESSION_BUS_ADDRESS`, `DESKTOP_SESSION=gnome`, `GDMSESSION=gnome`, `GDM_LANG`, `HOME`,
  `LANG`, `LOGNAME`, `MAIL`, `PATH=/home/<u>/.local/bin:/home/<u>/bin:/usr/local/bin:/usr/bin`, `QT_IM_MODULE=ibus`, `QT_IM_MODULES=wayland;ibus`,
  `SHELL=/bin/bash`, `SSH_AUTH_SOCK=/run/user/<uid>/gcr/ssh`, `USER`, `XDG_CURRENT_DESKTOP=GNOME`, `XDG_DATA_DIRS=<home>/.local/share/flatpak/exports/share:
  /var/lib/flatpak/exports/share:/usr/local/share/:/usr/share/`, `XDG_MENU_PREFIX=gnome-`, `XDG_RUNTIME_DIR`, `XDG_SESSION_CLASS=user`,
  `XDG_SESSION_DESKTOP=gnome`, **`XDG_SESSION_EXTRA_DEVICE_ACCESS=render:accel`**, `XDG_SESSION_TYPE=wayland`, `XMODIFIERS=@im=ibus`.
- **Ambiente del user manager** (`systemctl --user show-environment`) in aggiunta: `DISPLAY=:0`, `GNOME_SETUP_DISPLAY`, `WAYLAND_DISPLAY=wayland-0`, `XAUTHORITY=
  /run/user/<uid>/.mutter-Xwaylandauth.*` (nel locale c'è Xwayland; REMOTIX usa `--no-x11`).
- **Target attivi:** `gnome-session@gnome.target`, `gnome-session.target`, `gnome-session-initialized.target`, `gnome-session-manager.target`,
  `graphical-session.target` e una ventina di `org.gnome.SettingsDaemon.*.target`.
- **D-Bus:** `org.gnome.Mutter.{RemoteDesktop,ScreenCast,DisplayConfig}` ha come proprietario gnome-shell; `org.freedesktop.secrets` = `oo7-daemon`
  (uid dell'utente); `org.freedesktop.impl.portal.desktop.oo7` = `oo7-portal`; `org.freedesktop.portal.Flatpak` e `org.freedesktop.Flatpak`
  «activatable» (si avviano su richiesta).
- **Primo accesso (Fedora):** compare la finestra «Welcome to Fedora Linux 45 (Workstation Edition)» (gnome-tour); l'utente ha sbloccato la
  collezione `Login` del portachiavi (§7).
- **Variabili `GDM_LANG`/`GDMSESSION`/`DESKTOP_SESSION`** arrivano da GDM (non dalla sessione `.desktop`): REMOTIX non le imposta nel codice
  Ubuntu (`compose_environment()` non le ha); `DESKTOP_SESSION` solo con D-153 (Xsession.d, che qui non esiste: nessuna sessione X11 su Fedora). [S]

---------------------------------------------------------------------------------------------------------------------------------

## 3. Come REMOTIX avvia oggi GNOME (codice `U`) e che cosa regge su Fedora 45

### 3.1 Unità di sessione, GNOME 51 contro GNOME 50 [V `G`, unità lette in `/usr/lib/systemd/user`]
- `org.gnome.Shell@.service`: `Type=notify`, `ExecStart=/usr/bin/gnome-shell --mode=%i`, `AssertEnvironment=XDG_SESSION_TYPE=wayland`,
  `RefuseManualStart=on`, `Requisite=gnome-session-initialized.target`, `OnFailure=… gnome-session-shutdown.target`, `Restart=no`,
  `OOMScoreAdjust=-1000`, `TimeoutStopSec=5`, `ExecStopPost=-systemctl --user unset-environment GNOME_SETUP_DISPLAY WAYLAND_DISPLAY DISPLAY XAUTHORITY`.
  Stessa forma di Ubuntu 50.
- Istanza richiesta dalla sessione `gnome`: `gnome-session@gnome.target.d/gnome.session.conf` ⇒ `Requires=org.gnome.Shell@user.service` (e
  `gnome-session-services.target`). Quindi `--mode=user`. (Ubuntu: `@ubuntu`.)
- `gnome-session-manager@.service`: `Type=notify`, `ExecStart=/usr/libexec/gnome-session-service --session=%i`, `ExecStopPost=-/usr/libexec/gnome-session-ctl
  --shutdown`. `gnome-session-restart-dbus.service`: `ExecStart=/usr/libexec/gnome-session-ctl --restart-dbus`. **I due nomi che `inactive_unit()` aspetta
  (`session.h:121-127`) esistono invariati.**
- Opzioni: `gnome-session [--session=NAME] [--debug] [--version] [--disable-acceleration-check (ignorata)] [--no-reexec]`;
  `gnome-shell [--wayland] [--no-x11] [--wayland-display] [--display-server] [--headless] [--virtual-monitor] [--devkit] [--devkit-args] [--profile]
  [--debug-control] [--mode=MODE] [--list-modes] [--force-animations] [--version]`. `--headless` e `--no-x11` esistono con lo stesso senso;
  `--nested`/`--x11`/`--replace` non ci sono (come in 50). [V `G`: `--help`]
- **`gnome-session-init-worker` rifiuta di partire se `graphical-session.target` è già attivo**: `g_error("A graphical session is already running!")`
  in `gnome-session/leader-systemd.c:309-310` di 51.0 [V SRC]; è il comportamento già noto di 50.1.
- Altre unità utente di GNOME 51 da conoscere: `gnome-remote-desktop{,-headless,-handover}.service` (`WantedBy=gnome-session.target`, ma **non abilitate**
  di serie: `systemctl --user is-enabled` = disabled per tutte e tre), `gnome-initial-setup-first-login.service` (nel `.wants` di `gnome-session.target`),
  `oo7-daemon` (avviato da D-Bus/gnome-session), `uresourced`, `spice-vdagent.service` (nel `.wants` di `graphical-session.target`).

### 3.2 Il drop-in e la scelta dell'unità (`session.c`)
- `unit_shell()` (`U/src/session.c:3771`): legge `Requires` di `gnome-session@<name>.target`. Su Fedora [V `G`]:
  `gnome-session-manager@gnome.service gnome-session.target gnome-session-initialized.target gnome-session-services.target org.gnome.Shell@user.service`
  ⇒ trova `org.gnome.Shell@user.service`. **Regge.**
- Il drop-in (`session.c:~4013`): `ExecStart=` poi `ExecStart=<gnome-shell> --headless --no-x11 --mode=%i`, in
  `$XDG_RUNTIME_DIR/systemd/user.control/org.gnome.Shell@user.service.d/zz-remotix-monitor.conf`. Su Fedora [V `G`]: `systemctl --user show -p ExecStart
  org.gnome.Shell@user.service` mostra `argv[]=/usr/bin/gnome-shell --headless --no-x11 --mode=user` e il processo che nasce ha esattamente quella riga.
- `gnome-shell` si trova in `/usr/bin` (nessun percorso `/usr/lib64` per i binari GNOME; i `libexec` sono in `/usr/libexec` anche su Fedora). [V `G`]

### 3.3 Variabili e ambiente della nascita
- `compose_environment()` blocco GNOME (`session.c:~3619`): `XDG_CURRENT_DESKTOP` da `DesktopNames` = `GNOME`; `XDG_SESSION_DESKTOP` = `gnome`;
  `XDG_SESSION_TYPE=wayland`; `SHELL=` vuoto. Nella prova (§3.4) con esattamente queste variabili [V `G`] il user manager ha ricevuto:
  `WAYLAND_DISPLAY=wayland-0`, `XDG_MENU_PREFIX=gnome-` (messa da gnome-session), `QT_IM_MODULE=ibus`, `QT_IM_MODULES=wayland;ibus`, `XMODIFIERS=@im=ibus`,
  `SSH_AUTH_SOCK=/run/user/<uid>/gcr/ssh`, `PWD=/`, `SHLVL=0`; **niente `DISPLAY`** (`--no-x11`).
  `XDG_DATA_DIRS` nel user manager arriva dal generatore `/usr/lib/systemd/user-environment-generators/60-flatpak` (aggiunge
  `~/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share/`): non va gestito da REMOTIX.
- `SHELL=` vuoto serve a evitare il re-exec in login shell di gnome-session (`maybe_reexec_with_login_shell`, solo se `XDG_SESSION_TYPE=wayland`).
- **Differenza da Ubuntu:** non esiste `XDG_SESSION_EXTRA_DEVICE_ACCESS` nell'ambiente passato da REMOTIX; GDM lo imposta da sé (`render:accel`) e
  con systemd 262 (≥ 260) logind lo onora (con systemd 259.9 di Ubuntu non lo faceva). Vedi §10.3 (nodo render con modo 0666 su Fedora).

### 3.4 Prova di nascita su Fedora, fatta emulando `child.c` [V `G`]
Programma di studio (NON il prodotto; `gcc` e `pam-devel` installati nel guest): come `child.c:1713-1757`, come root `pam_start("rxstudy")`,
`pam_putenv(XDG_SESSION_TYPE=wayland, XDG_SESSION_CLASS=user)`, `PAM_RHOST=192.0.2.7`, `PAM_TTY=remotix`, `pam_open_session`, `pam_end` SENZA
`pam_close_session`, poi `initgroups/setgid/setuid` (utente `prova2`), resta vivo come leader, e lancia `setsid --fork sh -c rxstart.sh` che scrive
il drop-in, fa `daemon-reload`, `exec /usr/bin/gnome-session`. Il binario stava in `/usr/libexec/rxstudy/` (etichetta `bin_t`), l'unità in `/etc/systemd/system/`
(un servizio «di terzi installato da RPM»: gira come `system_u:system_r:unconfined_service_t:s0`). File PAM `rxstudy` = stack di sshd di Fedora.
Risultati:
1. Con lo stack di sshd com'è (`pam_selinux close` + `pam_selinux open env_params`): **`pam_open_session` riesce (0), ma la `execve` di `/usr/bin/setsid` fallisce con
   EACCES.** AVC nel journal (tre volte, una per tentativo):
   `avc: denied { transition } for comm="rxprobe" path="/usr/bin/setsid" scontext=system_u:system_r:unconfined_service_t:s0
   tcontext=unconfined_u:unconfined_r:unconfined_t:s0 tclass=process permissive=0`.
2. Senza le due righe `pam_selinux`: la sessione logind nasce (`Type=wayland`, `Class=user`, `Seat=` vuoto, `Remote=yes`, `Service=rxstudy`, `State=active`,
   Leader = il programma); `gnome-session-init-worker gnome` (contesto `unconfined_service_t`, figlio del leader via `setsid --fork`) avvia
   `gnome-session@gnome.target`; il **user manager** (avviato da logind) gira come `unconfined_t`; tutti i servizi sotto di lui `unconfined_t`
   (dbus-broker `unconfined_dbusd_t`). `gnome-shell --headless --no-x11 --mode=user` parte in ~3 s.
3. `systemctl --user is-active org.gnome.Shell@user.service graphical-session.target gnome-session-initialized.target` = active ×3; `systemctl --user --failed` vuoto.
4. `org.gnome.Mutter.DisplayConfig.GetCurrentState` risponde con **0 monitor** e 0 monitor logici; `ScreenCast.Version` = 4; `RemoteDesktop.Version` = 1.
   Journal della shell: `Running GNOME Shell (using mutter 51.0) as a Wayland display server`, `Added device '/dev/dri/renderD128' (virtio_gpu)`,
   `Failed to initialize accelerated iGPU/dGPU framebuffer sharing: Not hardware accelerated` (virtio senza 3D), `Using Wayland display name 'wayland-0'`,
   **`Error registering session with GDM: GDBus.Error:org.freedesktop.DBus.Error.AccessDenied: No display available`** (messaggio non fatale: il desktop
   resta vivo; è la shell che prova a registrare la sessione presso GDM; nel locale la registrazione riesce), `Will monitor session <n>`,
   `Error looking up permission: … No entry for geolocation` (portale, innocuo). Con la Radeon (§10): `Added device '/dev/dri/renderD128' (amdgpu)`,
   `Created gbm renderer`, `Obtained a high priority EGL context`: Mutter headless usa la scheda vera.
5. Nessun altro AVC oltre a quelli del punto 1 durante tutta la prova.
6. Il giro «Logout» (`org.gnome.SessionManager.Logout(1)`): `gnome-session-manager@gnome.service` e `graphical-session.target` inattivi in 0,2 s, processi
   da 66 a 3 in 1,3 s (restano solo leader `rxprobe`, `systemd --user`, `(sd-pam)`). Nessuna unità fallita. [V]
7. Dopo l'uscita il user manager conserva variabili d'ambiente (le avevano aggiunte le prove locali successive, §5), ma con una nascita pulita le sole
   residue sono quelle del punto 3.3: `WAYLAND_DISPLAY` ecc. le toglie `ExecStopPost` della shell.
**Conseguenza:** nel file PAM di REMOTIX per Fedora le righe `pam_selinux` vanno tolte (o vanno gestite nel codice con `setexeccon(NULL)` dopo `pam_open_session`),
e va deciso che il processo `remotix` giri come `unconfined_service_t` (default di un RPM senza modulo SELinux proprio). Vedi §9.2.

### 3.5 Pezzi di codice Ubuntu che cambiano per Fedora (elenco)
1. `U/src/remotix.pam`: sintassi e contenuto (vedi §9.1/9.2). `@include` non esiste in Linux-PAM di Fedora: si usa `substack`/`include`.
   Lo stack di riferimento di sshd su Fedora è: `auth substack password-auth; auth include postlogin; account required pam_sepermit.so; account required pam_nologin.so;
   account include password-auth; password include password-auth; session required pam_selinux.so close; session required pam_loginuid.so;
   session required pam_selinux.so open env_params; session required pam_namespace.so; session optional pam_keyinit.so force revoke; session optional pam_motd.so;
   session include password-auth; session include postlogin`. [V `G` `/etc/pam.d/sshd`]
2. `debian/remotix.pam-config` (pam-auth-update) non ha equivalente: vedi §9.1.
3. `debian/remotix.service`: `/bin/sh -c 'exec /usr/libexec/remotix/…` va bene (`/usr/libexec` esiste); `After=network.target systemd-logind.service` ok.
4. Il registro `session.c` stampa `«D8: the GNOME session is gnome (gnome.desktop): the only one …»` oppure `…the upstream GDM default`: su Fedora sarà il secondo testo.
5. `session.h:106-116` (commenti) dicono `@ubuntu`; su Fedora `@user`: nessuna costante da cambiare.

---------------------------------------------------------------------------------------------------------------------------------

## 4. Cattura dello schermo e ingresso (Mutter 51)

- `org.gnome.Mutter.ScreenCast` versione **4**, `org.gnome.Mutter.RemoteDesktop` versione **1**, `SupportedDeviceTypes` = 7 (tastiera|puntatore|touch). [V `G`: `busctl --user
  introspect` e `get-property` su una shell headless, §3.4]. **Identici a Mutter 50** (`U/studio/4-mutter50-cattura-input.md` §2: v4 / v1).
- `ScreenCast.CreateSession` espone `a{sv}` → `o` (metodo e proprietà `Version`); i metodi di sessione (`RecordVirtual`, `ConnectToEIS`) non sono stati interrogati
  uno a uno: `busctl introspect` è stato fatto solo sull'oggetto radice. **Non provato:** `RecordVirtual` con `modes`, `ConnectToEIS`, i valori di `cursor-mode`
  su Mutter 51. [S: invariati rispetto a 50, il sorgente di mutter 51.1 è in `SRC/mutter/mutter-51.1` e non è stato diffato]
- `libei` / `libeis` Fedora: 1.6.0 (nei repository; `U/debian/control` chiede `>= 1.3.901`). [V repoquery]
- `DisplayConfig.GetCurrentState` firma `ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv}` (la stessa di `TYPE_STATE` in `session.c:145`) [V `G`:
  la firma stampata da `busctl call`].
- Il monitor virtuale e il suo riconoscimento (`mutter_find_monitor`, prodotto «Virtual remote monitor») non sono stati osservati qui (nessuna cattura).

---------------------------------------------------------------------------------------------------------------------------------

## 5. GDM e la convivenza locale/remoto (voci A1, A2, A3 del registro)

### 5.1 Che cosa fa GDM 51 per un utente con sessione remota [V `G`, schermate e journal]
Procedura: sessione «REMOTIX-like» di `prova2` attiva (leader `rxprobe`, `Remote=yes`, `Class=user`, `Type=wayland`, nessun seat) + accesso locale di
`prova2` dalla schermata di GDM (selezione + password con `tasti`/`scrivi`). Nessun gancio REMOTIX nel PAM.
1. **Sessione remota ATTIVA:** GDM mostra **«Session Already Running — Login is not possible because a remote session is already running for prova2.
   To login, you must log out from the remote session or force stop it.» con «Cancel» e «Force Stop»**. Il codice di `gnome-shell` 51.1
   (`js/gdm/loginDialog.js:1214-1254`, `_findConflictingSession`) è identico per logica a quello di 48/50: per ogni altra sessione dello stesso utente con `Type`
   wayland|x11 e `State` active|online. [V SRC]
2. **«Force Stop»:** GDM 51 (`daemon/gdm-manager.c:1902-1932`, `on_stop_conflicting_session`) chiede a logind le sessioni grafiche dell'utente e fa
   `TerminateSession` su tutte tranne quella aperta. Osservato: `session-54.scope: Killing process 6399 (rxprobe) with signal SIGTERM`, sessione remota rimossa; **però GDM
   ha chiuso anche l'accesso locale appena aperto** (`Gdm: GdmDisplay: Session never registered, failing`, sessione 74 rimossa) e la schermata è tornata all'elenco
   utenti: **il proprietario deve accedere una seconda volta.** Differenza rispetto a quanto previsto per Ubuntu (lì era «da provare»).
3. **Sessione remota ORFANA, stato `closing`** (leader ucciso con SIGKILL, desktop vivo: scenario A1): `loginctl show-session` = `State=closing`, `Active=yes`,
   `Remote=yes`, scope `active (abandoned)`. L'accesso locale **non mostra alcun dialogo** (una sessione `closing` non è conflitto) e **`gnome-session-init-worker`
   muore subito**: journal `A graphical session is already running!`, `ANOM_ABEND … comm="gnome-session-i"`, **SIGABRT con core dump**
   (`coredumpctl`: `/usr/libexec/gnome-session-init-worker`, modulo `gnome-session-51.0-1.fc45`). La schermata di accesso torna all'elenco utenti in pochi
   secondi (non si è visto un blocco permanente come quello di GDM 48 su Debian). **A1 si riproduce su Fedora con GDM 51.**
   Non provato: quante volte può ripetersi prima che GDM si fermi (nel codice di GDM 50 c'è un tetto di 5 fallimenti per display, [S] per 51).
   Effetto collaterale visto: nel user manager condiviso restano variabili dell'accesso locale fallito (`DESKTOP_SESSION`, `GDMSESSION`, `GDM_LANG`, `XMODIFIERS`,
   `SSH_AUTH_SOCK`, `XDG_MENU_PREFIX`, …) e il core dump di gnome-session in `/var/lib/systemd/coredump` (due al termine della prova, uno non spiegato in
   un avvio della sonda: una seconda `gnome-session-init-worker` abortì alle 17:26:19 mentre il manager precedente era ancora in chiusura; la sessione poi
   funzionò e il logout riuscì: causa non accertata).
4. **Il dialogo appare DOPO `pam_open_session`:** il worker di GDM apre la sessione (PAM `session include password-auth` → `pam_systemd`, poi `include postlogin`)
   e solo dopo avvia il greeter che guarda `listSessions()`: l'ordine «prima il gancio PAM chiude il remoto, poi il greeter guarda» regge. [V codice di
   `loginDialog.js` 51.1 + journal: `pam_open_session` alle 17:24:14.242, abort di gnome-session alle 17:24:14.323]
5. Nel journal dell'accesso locale: `Captured PAM_AUTHTOK … Stashed password to try later in open session`, `auto_start argument detected … Successfully sent secret to oo7 daemon`
   (`pam_oo7` con `auto_start` fa parte di `gdm-password`, §7).

### 5.2 GDM 51 rispetto a GDM 50 di Ubuntu (NEWS letto in `SRC/gdm/gdm-51.1.1/NEWS`) [V SRC]
- **51.0/51.rc:** impronta digitale solo per la ri-autenticazione (non per accedere); PAM extensions corrette; «oo7 invece di gnome-keyring nelle regole PAM di Fedora»;
  schermate remote pre-autenticate (Kerberos, per gnome-remote-desktop).
- **51.1:** «Restricted which PAM stacks GDM will run, to defend against malicious greeters»; correzioni del `gnome-headless-session@<utente>.service`;
  `RemoteDisplayFactory` aspetta il `session-id`. **51.1.1:** «Fixed headless user display creation erroring out».
- Il `gnome-headless-session@.service` (unità di SISTEMA in `/usr/lib/systemd/system/`) è la strada di gnome-remote-desktop con GDM; REMOTIX non la usa.
  Il codice di `gdm-display-factory.c` che con quella via termina tutte le sessioni grafiche dell'utente alla distruzione del display resta una cosa da sapere se un
  amministratore usa anche GRD in modalità sistema (non abilitato di serie, §11).
- **Fedora aggiunge patch a GDM** [V SRC `gdm.spec`]: `0001-Add-headless-session-files.patch`, `0001-data-add-system-dconf-databases-to-gdm-profile.patch`
  (il profilo dconf del greeter include `system-db:gdm`, `local`, `site`, `distro`), `0001-Honor-initial-setup-being-disabled-by-distro-installer.patch`.

### 5.3 File PAM di GDM su Fedora [V `G`]
- Stanno in **`/usr/lib/pam.d/`** (`gdm-password`, `gdm-autologin`, `gdm-fingerprint`, `gdm-smartcard`, `gdm-switchable-auth`, `gdm-launch-environment`, `-*-substack`), pacchetto `gdm`,
  non in `/etc/pam.d`. (In Ubuntu sono conffile in `/etc/pam.d`.)
- `gdm-password`: `auth substack gdm-password-auth-substack` / `-auth optional pam_gnome_keyring.so` / `-auth optional pam_oo7.so` / `auth include postlogin`;
  `account … include password-auth`; sessione: `pam_selinux close`, `pam_loginuid`, `pam_selinux open`, `pam_keyinit force revoke`, `pam_namespace`, **`session include password-auth`**
  (qui c'è `pam_systemd`), `-session optional pam_gnome_keyring.so auto_start`, `-session optional pam_oo7.so auto_start`, **`session include postlogin`**.
  `gdm-autologin` usa `system-auth` + `postlogin`. `gdm-launch-environment` (greeter) usa `system-auth` + `postlogin`.
- `postlogin` (authselect, profilo `local`): `pam_umask silent`; `pam_succeed_if service !~ gdm* service !~ su* quiet`; `pam_lastlog2` ×2.
- Il gancio `pam_exec` di REMOTIX potrebbe stare in `postlogin` (è DOPO `pam_systemd` in tutti i servizi che lo includono: GDM, login, su, sshd, cockpit…; i filtri di
  `local_login.c` — `XDG_SEAT` non vuoto, classe `user`, servizio ≠ `remotix` — scartano il resto) oppure in `password-auth`/`system-auth` dopo `pam_systemd`. Vedi §9.1.

---------------------------------------------------------------------------------------------------------------------------------

## 6. dconf: il modello di Ubuntu (profilo di runtime + `/etc/dconf/db/remotix`)

[V `G` salvo dove indicato]
- Fedora: `/etc/dconf/profile/user` contiene **quattro righe**: `user-db:user`, `system-db:local`, `system-db:site`, `system-db:distro`. Esiste anche `/etc/dconf/profile/ibus`
  (`user-db:user`, `system-db:ibus`). Database già compilati in `/etc/dconf/db/`: `distro`, `gdm`, `ibus`, `local`, `site` (con le cartelle `*.d`); `distro.d/20-authselect`
  (blocca le chiavi di login screen per impronta/smartcard) non appartiene a nessun pacchetto (lo scrive authselect).
- Le impostazioni predefinite di Fedora per GNOME arrivano da **gschema override** (`10_org.gnome.desktop.background.fedora.gschema.override`, `org.gnome.shell.gschema.override`,
  `org.gnome.Ptyxis.fedora…`, `org.gnome.software-fedora…`), compilati negli schemi di glib: **arrivano da sole** nella sessione remota, non c'è un profilo da replicare. Lo sfondo, i preferiti
  del dock (Firefox ecc.), ecc. sono di serie.
- Meccanismo di dconf 51: sorgente `SRC/dconf/dconf-51.0/engine/dconf-engine-profile.c` — ordine: 1. profilo obbligatorio `/run/dconf/user/<uid>`, 2. `DCONF_PROFILE`, 3. **profilo di
  runtime `$XDG_RUNTIME_DIR/dconf/profile`**, 4. `user` in `/etc/dconf/profile/` o `XDG_DATA_DIRS/dconf/profile/`, 5. `user-db:user`. Identico a dconf 0.49 di Ubuntu.
  Fedora porta una patch (`dconf-override.patch`) che aggiunge `DCONF_USER_CONFIG_DIR` (usata da Flatpak). [V SRC]
- **Prova del modello (poi tolto tutto):** database `/etc/dconf/db/remotix` creato con `dconf compile` da un file chiave (`enable-animations=false` con blocco,
  `event-sounds=false`), profilo di runtime di `prova2` `user-db:user / system-db:remotix / user-db:remotix / system-db:local / system-db:site / system-db:distro`, **nessun
  `DCONF_PROFILE`**: `gsettings get org.gnome.desktop.interface enable-animations` = `false`, `writable` = `false` (bloccata); `event-sounds` = `false`, writable `true`;
  `color-scheme` = `'default'`. Il modello regge su dconf 51.
- `dconf compile`/`dconf update` stanno nel pacchetto `dconf` (`/usr/bin/dconf`, nessun `dconf-cli` separato). Il pacchetto `dconf` ha scriptlet solo per l'unità utente `dconf.service`;
  **nessun file-trigger** compila automaticamente `*.d` (i database di Fedora sono pronti dalla creazione dell'immagine). Quindi il `%post` di REMOTIX deve fare `dconf compile`
  o `dconf update`, e `%postun` toglierlo (come il postinst/postrm Debian). `dconf` è presente su GNOME; nelle altre edizioni va dichiarato (`Requires`/`Recommends`).
- **Flatpak e dconf** [V SRC `flatpak-1.18.4/common/flatpak-run.c:1280-1345`]: Flatpak legge con `DConfClient` i valori di default e i blocchi SOLO del prefisso dell'app (derivato dall'ID) e dei
  percorsi extra del manifesto, dentro il processo di `flatpak run` (che usa il profilo corrente, quindi anche quello di runtime). Le impostazioni generali (`org.gnome.desktop.*`)
  arrivano alle app Flatpak dal portale Settings (letto dal processo `xdg-desktop-portal`, che deve nascere con lo stesso profilo). [S: non provato che `xdg-desktop-portal` nato PRIMA
  del profilo di runtime lo veda]
- **Non provato su Fedora:** il rilevamento di variazioni a sessione viva con `gsettings monitor` e il servizio `ca.desrt.dconf.Writer/remotix` per `user-db:remotix`
  (`registro C5`): serve una prova con `dconf-service` nato nella sessione. Il punto è lo stesso di Ubuntu (dconf upstream).

---------------------------------------------------------------------------------------------------------------------------------

## 7. Portachiavi: oo7, non gnome-keyring

[V `G`]
- `gnome-keyring` **non è installato** nella Workstation (`rpm -q`: assente). Il servizio Secret è **`oo7-daemon`** (`/usr/libexec/oo7-daemon`, pacchetto `oo7-daemon-0.7.0~beta`),
  portale `oo7-portal` (`org.freedesktop.impl.portal.desktop.oo7`), PAM **`pam_oo7`** (pacchetto `pam_oo7`; nei file PAM di GDM con `-auth optional`, `-password optional … use_authtok`,
  `-session optional … auto_start`). `gcr` 4.4.1 fornisce `gcr/ssh` (`SSH_AUTH_SOCK=/run/user/<uid>/gcr/ssh`). GNOME Shell 51.0 NEWS: «Enabled use of oo7-portal as the implementation of the
  Secret portal» (51.alpha) e «Fixed bug where oo7-daemon.service never starts by default» (51.0). [V SRC `NEWS`]
- **Accesso locale da GDM:** collezioni `/org/freedesktop/secrets/collection/login` («Login», `Locked=false`) e `…/session` (`Locked=false`); alias `default` = `login`.
  Il journal mostra che `gdm-session-worker` ha mandato la password a `oo7-daemon` tramite `/run/user/<uid>/oo7-pam.sock` (processo figlio con l'uid dell'utente).
- **Sessione nata con lo stack di sshd, senza `pam_oo7` (la nostra prova):** `…/collection/login` esiste ma **`Locked=true`**; `session` sbloccata. Quindi un programma che chiede il
  portachiavi (Epiphany, GOA, Chrome via libsecret, ecc.) in una sessione REMOTIX troverebbe la collezione bloccata e chiederebbe la password con un dialogo sullo schermo remoto.
  [V la proprietà, S l'effetto sui singoli programmi]
- **Se si volesse sbloccarla** come fa GDM: `pam_oo7` con `auto_start` in `session` ha bisogno della password in chiaro «rimasta» dall'autenticazione (`pam_set_data`); in REMOTIX
  l'autenticazione (`authentication.c:313`, `pam_start`) e l'apertura di sessione (`child.c:1713`) sono due handle PAM diversi in due processi, quindi **la password non c'è** al momento
  di `pam_open_session`. Stesso limite di gnome-keyring su Ubuntu (`pam_gnome_keyring` è in `common-session` di Ubuntu; nel nostro `remotix.pam` Debian/Ubuntu non c'è). Decisione di
  prodotto, non tecnica (vedi «Decisioni»).
- Il file di dati dei portachiavi non è stato trovato in `~/.local/share/keyrings` né in `~/.local/share/oo7` dopo il primo accesso (percorso non determinato: **[S]** va guardato `oo7-daemon`).

---------------------------------------------------------------------------------------------------------------------------------

## 8. Flatpak nella sessione remota

[V `G`]
- Flatpak 1.18.4 è di serie; remoto `fedora` = **OCI** `oci+https://registry.fedoraproject.org` (non Flathub); nessuna app preinstallata (`flatpak list` vuoto). `flatpak-add-fedora-repos.service` di sistema.
  Servizi utente: `flatpak-portal.service`, `flatpak-session-helper.service`, `flatpak-oci-authenticator.service`; servizio di sistema `flatpak-system-helper.service`; polkit `org.freedesktop.Flatpak.rules`.
  Generatori d'ambiente `60-flatpak` (utente e sistema).
- **Prova:** nella sessione headless di `prova2` (nata come sopra, nessun gancio): `flatpak remote-add --user fedora …`, `flatpak install --user fedora org.gnome.Calculator` (runtime
  `org.fedoraproject.Platform` f45, 540 MB + GL/CL/Locale: ~1,1 GB scaricato, installato in <1 minuto), `flatpak run org.gnome.Calculator` con `WAYLAND_DISPLAY=wayland-0`:
  **il programma parte** (`bwrap … gnome-calculator`, `xdg-dbus-proxy`, `flatpak-session-helper`, `flatpak-portal`, `xdg-document-portal` attivi, tutti `unconfined_t`). Avvisi di Mesa
  («ZINK: failed to choose pdev», `failed to create dri2 screen`) dovuti alla scheda virtuale senza 3D. Nessun AVC. **Non serve nulla di speciale** (a differenza degli snap su Ubuntu, che
  chiedevano un profilo dconf compatibile e AppArmor). [V; non provato con la Radeon né con il flusso video aperto]
- `flatpak install --system` come root senza bus utente fallisce («Cannot autolaunch D-Bus without X11 $DISPLAY»): lo studio ha installato per utente; l'installazione di sistema da un servizio non è un caso REMOTIX.
- Fatto da ricordare: bwrap gira senza problemi in `unconfined_t` (l'utente della sessione); il caso `confinato` (utente SELinux ristretto) non è stato provato.

---------------------------------------------------------------------------------------------------------------------------------

## 9. Sistema Fedora

### 9.1 PAM, authselect, `pam_faillock`
- Profilo attivo: `local` con le funzioni `with-silent-lastlog` e `with-mdns4`. `authselect current` / `check`: valido. **`with-faillock` NON è attivo**: nello stack di sistema
  non c'è `pam_faillock` (la ban table di REMOTIX, `--ban-file`, è l'unica difesa; a Fedora Workstation appena installata anche `ssh` non ha faillock). [V `G`]
- `/etc/pam.d/system-auth`, `password-auth`, `postlogin`, `smartcard-auth`, `fingerprint-auth` sono collegamenti simbolici verso `/etc/authselect/…`, intestati «Generated by authselect — non modificare a mano».
  `/etc/pam.d/sshd`, `login`, `su`, `cockpit` ecc. sono normali conffile. `/usr/lib/pam.d` contiene i file di GDM e `polkit-1`, `systemd-user`, `systemd-run0`.
- **Prova sulla modifica a mano di un file authselect** (`/etc/authselect/postlogin`, riga `session optional pam_exec.so quiet /usr/bin/true` in coda): `authselect check` continua a
  dire «valid», ma **`authselect apply-changes` rigenera il file e cancella la riga** (verificato: 0 righe `pam_exec` dopo). [V `G`]
  Anche l'aggiornamento del pacchetto `authselect` esegue `apply-changes` [S: non provato qui].
- **Prova del profilo personalizzato:** `authselect create-profile remotix-study -b local` (crea `/etc/authselect/custom/remotix-study` con i template), riga aggiunta al suo `postlogin`,
  `authselect select custom/remotix-study with-silent-lastlog with-mdns4 --force`: la riga entra in `/etc/pam.d/postlogin` e **sopravvive** a `apply-changes`. Ripristino: `authselect select
  local with-silent-lastlog with-mdns4 --force` e cancellato `custom/remotix-study`; `diff -r /etc/authselect` con la copia fatta prima: identico. [V `G`]
  **Ma** cambiare profilo sostituisce la scelta dell'amministratore (`sssd`, `winbind`, funzioni attive, profili `custom/` propri): un RPM di terzi non può farlo in silenzio.
- Funzioni di authselect del profilo `local` utili: `with-faillock`, `with-pamaccess`, `with-pwhistory`, `with-mkhomedir`, `with-systemd-homed`… **nessuna funzione generica «aggiungi una riga»**.
  Le funzioni sono nei template dei profili, non estensibili da un pacchetto di terzi. [V `authselect list-features local`]
- **Alternative per il gancio «accesso locale»** (da decidere, §Decisioni): (a) profilo `custom/…` creato dal `%post` solo se l'amministratore non ne ha uno proprio (intrusivo); (b) riga a mano in
  `/etc/authselect/postlogin`/`password-auth` + avviso («fragile: scompare a ogni `apply-changes`») e controllo periodico che la riporti; (c) file PAM propri per i display manager
  (`/etc/pam.d/gdm-password` in `/etc` prevale su `/usr/lib/pam.d`: ma significa copiare e tenere allineato il file di GDM); (d) nessun gancio PAM e un altro meccanismo (osservare logind /
  il display manager); (e) accettare il comportamento di GDM (dialogo + «Force Stop» quando la sessione remota è attiva) e il solo problema dell'orfano `closing` curato con la chiusura
  del remoto alla fermata del servizio (A1), senza gancio. Su GDM 51 la strada (e) copre il caso «attivo» (dialogo) e il caso «orfano» è già curato da A1.
- Lo stack che serve a REMOTIX per `/etc/pam.d/remotix` (service `remotix`, aperto da `child.c`): vedi §3.5 e §9.2; ricordare che `other` su Fedora è `pam_deny`
  (commento di `U/src/remotix.pam`: il sintomo sarebbe «password sbagliata» per tutti) [V: `/etc/pam.d/other` esiste; non letto il contenuto].

### 9.2 SELinux
- `getenforce` = Enforcing, policy `targeted` 45.23, MLS enabled, `deny_unknown allowed`. [V `G`]
- **Dominio di un servizio installato da RPM:** binario in `/usr/libexec/<nome>/` = `bin_t`, unità in `/etc/systemd/system` o `/usr/lib/systemd/system` = `systemd_unit_file_t` ⇒ il servizio gira
  come `system_u:system_r:unconfined_service_t:s0` (osservato sul processo `rxprobe` e sulla sua sessione, §3.4). `unconfined_service_t` è un dominio non confinato: non ha negato bind, D-Bus,
  né l'accesso a logind, né `/proc`, né `setuid`. Un solo AVC osservato in tutta la prova: il passaggio di dominio causato da `pam_selinux open` (§0.2, §3.4.1).
- **Perché fallisce la `execve`:** `pam_selinux.so open env_params` chiama `setexeccon()` con il contesto predefinito dell'utente (`unconfined_u:unconfined_r:unconfined_t`); `unconfined_service_t` non può
  fare la transizione verso `unconfined_t` eseguendo `/usr/bin/setsid` (`bin_t`). Una `execve` di un processo che ha impostato `setexeccon` si rifiuta con EACCES. Le strade:
  togliere `pam_selinux` da `remotix.pam` per Fedora; oppure `setexeccon(NULL)` nel figlio dopo `pam_open_session` (codice); oppure un modulo SELinux di REMOTIX (`remotix_t`, `selinux-policy-devel`
  è nei repository: 45.24) che permetta la transizione verso `unconfined_t`. Nessuna è stata provata oltre la prima.
- **User manager e figli:** logind avvia `user@<uid>.service` con il contesto predefinito dell'utente: `unconfined_t` (visto sia per `prova` locale che per `prova2` remoto); i processi nati dal manager (gnome-shell,
  portali, gsd-*, flatpak) sono `unconfined_t`; solo il **leader** (`gnome-session-init-worker`, il processo REMOTIX figlio) resta `unconfined_service_t`. [V `G`]
- Chi sostituisce AppArmor: nessun profilo da scrivere per forza (dominio non confinato); `walls.c` (landlock) e il resto del prodotto restano. Il profilo AppArmor del lato rete (`debian/remotix_network.apparmor`)
  non ha equivalente automatico: se si vuole un confinamento del lato rete serve un modulo SELinux (non studiato). **[S]**
- File dell'RPM: `/var/lib/remotix` (`var_lib_t`), `/run/remotix` (`var_run_t`), `/etc/remotix` (`etc_t`): non provato che i contesti predefiniti bastino; un servizio non confinato non ne soffre.
- Il core dump di gnome-session e il registro: `coredumpctl` raccoglie (`systemd-coredump`).
- **Porte:** `semanage port -l` non elenca la 7447 (nessuna etichetta); per un dominio non confinato non serve. Se un domani il lato rete fosse confinato (`remotix_network_t`), servirebbe etichettare la porta. [V assenza, S per il resto]

### 9.3 firewalld [V `G`]
- Zona predefinita **`FedoraWorkstation`**, servizi `dhcpv6-client samba-client ssh`, e **porte `1025-65535/udp` e `1025-65535/tcp` aperte**. `firewall-cmd --query-port=7447/tcp` e `/udp` = yes.
  La 7447 è già raggiungibile sulla Workstation: il pacchetto non ha nulla da aprire per far funzionare il servizio, ma nelle altre edizioni (`FedoraServer`: solo ssh/cockpit) e per chi restringe la zona serve un
  file `/usr/lib/firewalld/services/remotix.xml` (266 servizi già lì; paccehtto `firewalld-filesystem` per i macro RPM). Il pacchetto non dovrebbe aprire porte di suo (il servizio nasce disabilitato).
  Il confronto con ufw di Ubuntu (`debian/remotix.ufw`) è: là un profilo, qui un file di servizio. [S sul prodotto, V sui fatti]

### 9.4 polkit e logind [V `G`]
- polkit 127-5; regole del sistema in `/usr/share/polkit-1/rules.d` (`20-gdm.rules`, `50-default.rules`, …); `/etc/polkit-1/rules.d` è leggibile solo da root.
  `20-gdm.rules` dà `YES` all'utente `gdm` (greeter) per `NetworkManager.settings.modify.system`, pcsc, e `gnome-headless-session@…` per le schermate remote.
- **Il gruppo dell'amministratore è `wheel`** (l'utente `prova` è in `wheel`, `uid 1000`); `sudo` chiede la password (ma `echo | sudo -S` col pw funziona qui). La regola
  `remotix-no-poweroff.rules` (`U/src/remotix-no-poweroff.rules`, installata in `/usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules`) è compatibile come percorso.
- **Azioni di logind di systemd 262:** `/usr/share/polkit-1/actions/org.freedesktop.login1.policy` ne ha **37**. Le 19 azioni della regola REMOTIX (`power-off*`, `reboot*`, `halt*`, `suspend*`,
  `hibernate*`, `set-reboot-*` …) **esistono tutte e non ne mancano**; le 18 non nominate sono tutte `inhibit-*`, `attach-device`, `chvt`, `flush-devices`, `lock-sessions`, `manage`,
  `set-self-linger`, `set-user-linger`, `set-wall-message`. Nuove rispetto ai nomi noti: `inhibit-handle-reboot-key`, `inhibit-handle-power-key` e simili (inibitori, non fermano la macchina). [V
  confronto di liste: `U/src/remotix-no-poweroff.rules` contro la policy installata]
  Non eseguito su Fedora: `power-implied` di `prove/check-desktop.py` e `pkcheck` dalla sessione locale (**da fare**, §Prove).
- Altre azioni che toccano energia, non login1: `net.hadess.PowerProfiles.*`, `org.freedesktop.UPower.*`, `udisks2.power-off-drive*` (dischi), `libvirt.api.domain.hibernate/suspend`: non fermano la macchina.
- Il greeter (utente `gdm-greeter`) ha sessione «active locale»: il caso «riavvio dal menu della schermata di accesso» (voce C6) NON è stato misurato su Fedora. **[non provato]** Il menu a tendina con
  l'icona di spegnimento c'è nella schermata di accesso (visto nella schermata).
- logind: `KillUserProcesses` non verificato; `loginctl terminate-user` e `terminate-session` funzionano come sull'altro sistema; sessioni senza seat risultano `Active=yes`.

---------------------------------------------------------------------------------------------------------------------------------

## 10. Video e audio

### 10.1 H.264/HEVC: lo stato di serie e con RPM Fusion [V Radeon `G`, 17:30, un solo periodo di accensione]
- Di serie (Mesa 26.2.3, anche 26.2.7 stock): `vainfo --display drm --device /dev/dri/renderD128` con `LIBVA_DRIVER_NAME=radeonsi` sulla **Radeon RX 6800 (navi21)**: profili
  `MPEG2Simple/Main`, `JPEGBaseline`, `VP9Profile0/2`, `AV1Profile0` (tutti `VAEntrypointVLD`, decodifica), `VideoProc`. **Nessun H264, nessun HEVC, nessun VC1.**
- Vulkan di serie: RADV su Mesa 26.2.x: `VK_KHR_video_decode_av1`, `decode_vp9`, `encode_queue`, `encode_intra_refresh`, `encode_quantization_map`, ma **nessun `encode_h264`/`encode_h265`**.
- Causa [V SRC `mesa.spec` + `meson.options` di mesa 26.2.7]: lo spec non passa `-Dvideo-codecs=…`; il valore predefinito di meson è `all_free` (esclude h264dec/h264enc/h265dec/h265enc/vc1dec, come
  dice la descrizione «Distros might want to consult their legal department»); l'opzione vale «for all video APIs (vaapi, vulkan)». Lo spec ha `with_va 1` (driver VA presente, ma senza i codec).
  `radeonsi_drv_video.so` è dentro `mesa-dri-drivers` (non esiste un pacchetto `mesa-va-drivers` stock in 45; `rpm -q mesa-va-drivers` = assente).
- Con **RPM Fusion Free** abilitato (`rpmfusion-free-release-45`, dichiarato; vedi «Che cosa ho cambiato»): `dnf install mesa-va-drivers-freeworld` (26.2.7) installa
  `/usr/lib64/dri-freeworld/radeonsi_drv_video.so`; libva di Fedora lo cerca prima in `dri-nonfree/`, poi `dri-freeworld/`, poi `dri/`. Risultato: `VAProfileH264ConstrainedBaseline/Main/High`
  e `HEVCMain/Main10` con **`VAEntrypointEncSlice` e `VAEntrypointVLD`**, più VC1. `dnf install mesa-vulkan-drivers-freeworld` (sostituisce `mesa-vulkan-drivers`): `vulkaninfo`
  mostra **`VK_KHR_video_encode_h264` e `VK_KHR_video_encode_h265`** (revisione 14). Aggiornò anche Mesa a 26.2.7 per dipendenza. [V]
- REMOTIX: `encoder.c` «hardware via VA-API, niente ripiego software»; `vulkanvideo.c` richiede `VK_KHR_video_encode_h264/h265`; codec in `child.c:429`: 1 = HEVC, 3 = H.264 (AV1 ritirato).
  La RX 6800 (RDNA2) non ha comunque la codifica AV1 (`av1enc` è «free» ma serve VCN4/RDNA3: **[S]**). ⇒ **su una Fedora senza RPM Fusion REMOTIX non ha nessun codificatore sulla Radeon.**
  Il ripiego software (OpenH264/SVT-AV1, `ripiego.c`) è stato tolto il 1 ott 2026 (`U/src/encoder.c:25`): a Fedora serve per forza una decisione (§Decisioni). `openh264` (Cisco) NON è installato ma il
  repository `fedora-cisco-openh264` è abilitato (solo software, solo H.264, solo decodifica/encodifica lenta); `ffmpeg-free` 9.0.2 è installato (senza libx264/libx265).
- GPU Intel/NVIDIA non provate (la macchina ha solo la Radeon).

### 10.2 GNOME e la GPU [V Radeon]
- Mutter headless con la Radeon: `Added device '/dev/dri/renderD128' (amdgpu) using no mode setting`, `Obtained a high priority EGL context`. Funziona con scheda reale, senza monitor.
  `Boot VGA GPU … selected as primary`.

### 10.3 Nodo di render e permessi [V `G`]
- `/dev/dri/renderD128` = `crw-rw-rw- root render 226,128` (modo **0666**, nessun ACL; con la virtio e con la Radeon). Il gruppo `render` (gid 105) è vuoto; `card0/1` = `crw-rw----+ root video` (con ACL `uaccess`).
  Quindi su Fedora 45 **qualunque utente apre il nodo di render**: `render_grant.c` (ACL su `renderD*`, `GRANTS_DIR /var/lib/remotix`) non ha niente da concedere. **[S: se il codice in presenza di un modo 0666 senza ACL
  lo tratta come «già a posto» o come errore non è stato letto fino in fondo: da controllare]**
- `XDG_SESSION_EXTRA_DEVICE_ACCESS=render:accel`: con logind ≥ 260 dà alla sessione l'ACL sul nodo di render/accel; qui il modo 0666 rende la cosa ininfluente.

### 10.4 Audio (PipeWire) [V `G`]
- PipeWire 1.6.9 e WirePlumber 0.5.18 sono di serie (nell'utente: `pipewire`, `wireplumber`, `pipewire-pulse` sotto il user manager). Nella sessione REMOTIX di prova partono come nel locale
  (`pipewire`, `wireplumber`, `pipewire-pulse`), `gsd-sound`, `uresourced`. Nomi: `pipewire`, `wireplumber`, `pipewire-pulseaudio` (non `pipewire-pulse`), `pipewire-devel`, `opus-devel`.
- Non osservato: cattura dell'audio di REMOTIX e il tempo di 25 s con RealtimeKit (voce B2): su Fedora `rtkit` presente? **[non verificato]**.

---------------------------------------------------------------------------------------------------------------------------------

## 11. gnome-remote-desktop già presente: si pesta i piedi?

[V `G`]
- Pacchetto `gnome-remote-desktop-51.0-1.fc45` installato di serie. Unità di **sistema** `gnome-remote-desktop.service` (disabilitata), `gnome-remote-desktop-configuration.service`,
  `gnome-remote-desktop-pcscd.service`; unità **utente** `gnome-remote-desktop.service`, `-headless.service`, `-handover.service` (`WantedBy=gnome-session.target`, **tutte non abilitate**); GDM porta
  `gnome-headless-session@.service`. Non in ascolto: `ss -ltn` senza 3389/3390; `grdctl status`: RDP e VNC disabled, Unit inactive; D-Bus `org.gnome.RemoteDesktop.*` senza proprietario.
- Quindi **di serie non registra sessioni `org.gnome.Mutter.RemoteDesktop`**: l'interfaccia di Mutter è libera per REMOTIX. Se l'amministratore attiva «Condivisione desktop» (RDP/VNC) o la modalità headless di GRD,
  GRD creerà una propria sessione di RemoteDesktop/ScreenCast per l'utente: convivenza con REMOTIX **non provata** (due sessioni di cattura sullo stesso Mutter sono permesse dall'API: [S]); nella modalità
  headless di sistema GRD usa il display factory di GDM e **termina le altre sessioni grafiche dell'utente** (§5.2: `gdm-display-factory.c`, `gdm_find_graphical_sessions_for_username`).
- Polkit di GRD: `/usr/share/polkit-1/rules.d/20-gnome-remote-desktop.rules` (non letto).
- Differenza da Ubuntu: stessa cosa (anche lì era presente non attivo).

---------------------------------------------------------------------------------------------------------------------------------

## 12. Pacchetto RPM: nomi e regole

### 12.1 Dipendenze: da `U/debian/control` a Fedora 45 [V `G`: `dnf repoquery --available`]
| Debian/Ubuntu | Fedora 45 (versione nel repository) |
|---|---|
| libssl-dev (>= 3.5) | `openssl-devel` **4.0.3** (OpenSSL 4: il codice è stato scritto/provato con 3.5; da provare) |
| libpam0g-dev | `pam-devel` 1.7.2 |
| libglib2.0-dev (>= 2.80) | `glib2-devel` 2.90.1 |
| libpipewire-0.3-dev | `pipewire-devel` 1.6.11 |
| libdrm-dev | `libdrm-devel` 2.4.134 |
| libva-dev | `libva-devel` 2.24.1 |
| libopus-dev | **`opus-devel`** 1.6 (`libopus-devel` non esiste) |
| zlib1g-dev | `zlib-ng-compat-devel` 2.3.3 (fornisce `zlib-devel`) |
| libei-dev (>= 1.3.901) | `libei-devel` 1.6.0 (+ `libeis-devel`) |
| libxkbcommon-dev | `libxkbcommon-devel` 1.13.1 |
| libgbm-dev | `mesa-libgbm-devel` 26.2.7 |
| libwayland-dev | `wayland-devel` 1.26.0 |
| libvulkan-dev (>= 1.3.274) | `vulkan-headers` 1.4.350.0 + `vulkan-loader-devel` |
| meson, patch, hwdata | `meson` 1.12.1, `patch`, `hwdata` 0.413 |
| wayland-protocols | `wayland-protocols-devel` 1.50 |
| libegl-dev / libgles-dev | `mesa-libEGL-devel` 26.2.7; GLES: nome da cercare (`libglvnd-gles`/`mesa-libGLES-devel` non risulta) |
| libinput-dev | `libinput-devel` 1.32.0 |
| libpixman-1-dev | `pixman-devel` 0.46.2 |
| libseat-dev | `libseat-devel` 0.9.3 |
| libudev-dev | `systemd-devel` 262.1 (o `libgudev-devel` 238 per il wrapper GLib) |
| libdisplay-info-dev | `libdisplay-info-devel` 0.3.0 |
| libxml2-dev / libcairo2-dev / libpango1.0-dev / libpng-dev | `libxml2-devel` 2.15.4 / `cairo-devel` 1.18.6 / `pango-devel` 1.58.2 / `libpng-devel` 1.6.59 |
| ngtcp2 / nghttp3 (statici, pinned 1.25.0 / 1.18.0) | repository: `ngtcp2-devel` 1.22.1, `libnghttp3-devel` 1.19.0 (la versione pinned è più nuova di ngtcp2 del repo: si continua a compilare statico come oggi) |
| labwc 0.9.3 / wlroots 0.19.2 (statici) | repository: `labwc` **0.20.2**, `wlroots` **0.20.2**, e il pacchetto compatibile `wlroots0.19` / `wlroots0.19-devel` **0.19.3**; (REMOTIX usa labwc/wlroots propri: tema delle altre agenti) |
| Depends libpam-systemd | integrato in `systemd`/`pam` (modulo `pam_systemd.so` in `systemd-pam`: **[S]** nome del pacchetto da verificare) |
| libpam-runtime / libpam-modules / passwd | `pam`, `shadow-utils` (+ `authselect`) |
| dbus-user-session | di serie: `dbus-broker` + `systemd` (`dbus-broker` 37) |
| pipewire, wireplumber | `pipewire`, `wireplumber` |
| Recommends va-driver-all | `libva` + Mesa (con i codec: **RPM Fusion** `mesa-va-drivers-freeworld`; di serie non codifica) |
| Recommends mesa-vulkan-drivers | `mesa-vulkan-drivers` (stock senza encode H.264/HEVC) / `mesa-vulkan-drivers-freeworld` (RPM Fusion) |
| Recommends labwc, wlr-randr, xwayland, fonts-dejavu-core, dconf-cli | `labwc`, `wlr-randr` 0.5.0, `xorg-x11-server-Xwayland`, `dejavu-sans-fonts` 2.37, `dconf` (contiene `dconf` il comando) |
| (nuovo) | `selinux-policy-devel` 45.24 e `checkpolicy` 3.11 se si fa un modulo SELinux |
Non cercati: `libwebsockets`/`liburing`/`libsodium` ecc. non sono nel `control` e non servono.

### 12.2 Regole RPM che toccano REMOTIX [V `G`/S]
- **Servizio installato disabilitato:** `/usr/lib/systemd/system-preset/99-default-disable.preset` = `disable *`; i preset Fedora abilitano solo i servizi elencati (`90-default.preset`: `enable sshd.service`, `85-display-manager.preset`: gdm…).
  Un servizio di REMOTIX non elencato nasce disabilitato: coincide con «installato disabilitato e non avviato». Le macro `%systemd_post/%systemd_preun/%systemd_postun_with_restart` oggi in Fedora usano `systemd-update-helper`
  (visto negli scriptlet di `dconf`: `systemd-update-helper install-user-units`, `remove-user-units`, `mark-restart-user-units`; per servizi di sistema le macro `%systemd_*`).
- **sysusers/tmpfiles:** `/usr/lib/sysusers.d/` e `/usr/lib/tmpfiles.d/` esistono (visto `gnome-remote-desktop-sysusers.conf`, `gnome-remote-desktop-tmpfiles.conf`): REMOTIX deve consegnare
  `remotix.sysusers` e `remotix.tmpfiles` come file nel pacchetto e dichiarare `%sysusers_create_compat`/`Requires(pre)` secondo la guida Fedora [W, da leggere]. Utente di sistema dedicato (come `gnome-remote-desktop`).
- **File in `/etc`:** `%config(noreplace)` per `/etc/pam.d/remotix`, `/etc/remotix/denied-users`; la regola polkit va in `/usr/share/polkit-1/rules.d` (come oggi); i profili ufw/AppArmor non ci sono.
- **SELinux nel RPM:** modulo `.pp` in `/usr/share/selinux/packages/` con `%selinux_modules_install`/`%selinux_modules_uninstall` (pacchetto `selinux-policy-devel`), oppure nessun modulo: servizio `unconfined_service_t`
  (§9.2). Se si fa il modulo, va provato su enforcing.
- **Licenze dei codec:** Fedora non distribuisce H.264/HEVC (Mesa `all_free`): REMOTIX non li contiene (usa l'hardware della scheda). Il pacchetto non può dipendere da RPM Fusion nei repository ufficiali Fedora: la dipendenza
  da `mesa-va-drivers-freeworld` può essere solo documentata (`Recommends`/`Suggests` impossibili verso un repo non base). Il binario `remotix` non incorpora codec.
- **Aggancio PAM:** nessun equivalente di `pam-auth-update` (§9.1). Il `%post` non dovrebbe toccare authselect senza dirlo.
- **Rimozione pulita** (principio C: «uninstall clean»): `%preun`/`%postun` devono chiudere i desktop remoti, togliere `/etc/dconf/db/remotix`, la riga PAM se messa, `~/.config/dconf/remotix`,
  la regola polkit e lo stato; stesse voci di `postrm` Debian.

---------------------------------------------------------------------------------------------------------------------------------

## Problemi da affrontare

| N | Che cosa | Dove nel codice | Peso | Cura già nota da Ubuntu/Debian |
|---|---|---|---|---|
| 1 | `pam_selinux open` nel file PAM di REMOTIX rende impossibile la `execve` del desktop (AVC `transition`, EACCES) | `U/src/remotix.pam` (copia di sshd), `child.c:1713-1757` | **grande** (nessun desktop su nessun gusto di Fedora con SELinux enforcing) | no: Debian/Ubuntu non hanno SELinux attivo (`module_unknown=ignore`) |
| 2 | Nessun H.264/HEVC hardware di serie (Mesa `all_free`), né VA-API né Vulkan; il ripiego software è stato tolto | `encoder.c`, `vulkanvideo.c`, `vadirect.c`, `child.c:429`, `debian/control` (Recommends) | **grande** (decisione prodotto: RPM Fusion, ripiego software, solo AV1 su GPU nuove) | no |
| 3 | Gancio PAM «locale esclude remoto»: nessun meccanismo pulito di authselect; file GDM in `/usr/lib/pam.d` | `U/debian/remotix.pam-config`, `local_login.c`, `rootside.c:2395-2760` | **grande** | parziale: logica `local_login` valida (Ubuntu); meccanismo diverso |
| 4 | A1 (orfano `closing` + accesso locale → abort di `gnome-session`, core dump) riprodotto su GDM 51 | `rootside.c:1758`, chiusura alla fermata del servizio | medio (cura già nota, da riprovare) | sì: DECISIONS-11 §11.56, registro A1 |
| 5 | «Force Stop» di GDM 51 uccide anche l'accesso locale appena aperto (secondo accesso necessario) e il ramo `sigterm_serve` del figlio non è provato | `child.c` (ramo SIGTERM non del genitore, «1.5.5») | piccolo/medio | no (studio Ubuntu: «da provare») |
| 6 | Portachiavi oo7: collezione «Login» bloccata nella sessione remota; nessuna password al momento di `pam_open_session` | `authentication.c:313`, `child.c:1713` | medio (esperienza utente; scelta di prodotto) | no (stesso limite con gnome-keyring su Ubuntu, mai affrontato) |
| 7 | Mutter 51: `Error registering session with GDM … No display available` e `Will monitor session N` all'avvio della shell headless | log della shell; `session.c` (nessun codice) | piccolo (osservazione: non fatale; chiarire che non cambia il comportamento) | no |
| 8 | Variabili e core dump dopo un accesso locale fallito (A1): `DESKTOP_SESSION`, `GDMSESSION`, `GDM_LANG`, `XMODIFIERS`, `SSH_AUTH_SOCK`… restano nel user manager | `session.c` (`OUR_VARIABLES`, ~3843 in `DEB`; `U` ~) | piccolo | parziale (registro E3) |
| 9 | Nomi dei pacchetti RPM e versioni diverse: `openssl` 4.0.3, `opus-devel`, `libnghttp3-devel`, `labwc`/`wlroots` 0.20.2 (e `wlroots0.19`) | `debian/control`, `build/` | medio (OpenSSL 4 va provato: API) | sì per la lista Debian; da riscrivere |
| 10 | Il profilo AppArmor del lato rete non ha equivalente: il lato rete gira non confinato (`unconfined_service_t`) | `debian/remotix_network.apparmor`, `walls.c` | medio (sicurezza: un secondo muro in meno) | no |
| 11 | `dconf` non è di serie su tutte le edizioni; nessun file-trigger compila `*.d`; `%post` deve fare `dconf compile` | `debian/remotix.postinst`, `session.c` (`--dconf-keyfiles`, ripiego «DECLARED FALLBACK, D-015») | piccolo | sì (C5, Ubuntu) |
| 12 | Il nodo `renderD*` è 0666: verificare che `render_grant.c` non scambi «nessun ACL» per un errore | `render_grant.c` | piccolo | parziale |
| 13 | `pam_faillock` non attivo di serie; la ban table di REMOTIX resta l'unica difesa; `other` = `pam_deny` se il file `remotix` manca | `main.c` (controllo di `/etc/pam.d/remotix`), `authentication.c` | piccolo/medio | sì (D3) |
| 14 | Welcome Tour di Fedora e `gnome-initial-setup-first-login.service` al primo accesso remoto di un utente nuovo: non provato cosa si veda | — | piccolo | no (Ubuntu: voce 4 di §3) |

## Decisioni che spettano al proprietario

1. **Video:** come si ottiene H.264/HEVC su Fedora? (a) documentare RPM Fusion Free (`mesa-va-drivers-freeworld`, `mesa-vulkan-drivers-freeworld`) come requisito; (b) reintrodurre un ripiego software
   (OpenH264 di Cisco è nel repository abilitato; H.264 soltanto); (c) puntare su AV1 per le GPU che lo codificano (non la RX 6800). Nessuna è decisa.
2. **Gancio «accesso locale»** (§9.1): quale meccanismo su Fedora (profilo authselect `custom/` creato dal pacchetto, riga a mano con avviso, file PAM dei display manager in `/etc/pam.d`, o nessun gancio PAM)?
3. **SELinux:** lasciare il servizio non confinato (`unconfined_service_t`, nessun modulo, `pam_selinux` tolto) oppure scrivere un modulo SELinux proprio? Impatta anche cosa sostituisce l'AppArmor del lato rete.
4. **Portachiavi:** va sbloccato il portachiavi (oo7) nella sessione remota? Richiederebbe passare la password al processo che apre la sessione.
5. **«Force Stop» di GDM:** accettare il comportamento osservato (il secondo accesso)?
6. **Welcome Tour/Initial Setup** nella sessione remota: nasconderlo (come Ubuntu per `gnome-initial-setup`)? Non osservato.
7. **OpenSSL 4:** si ricostruisce con OpenSSL 4 di Fedora o si prevede un `openssl3-devel`/compat? (da provare)

## Che cosa non si può sapere senza provare

- Se il prodotto vero (con `child.c`) si comporta come la sonda di studio: ordine esatto dei file di PAM, `pam_loginuid` (la sonda non lo ha in forma identica), mantenimento della sessione logind al `exec`, ritardi.
- Cattura vera: `RecordVirtual`, `ConnectToEIS`, EIS su Mutter 51; il monitor virtuale; la consegna dell'input da tastiera/mouse/touch; HiDPI.
- Video di REMOTIX su Fedora con la Radeon (con i driver freeworld): codifica effettiva, latenza, `VAProfile` scelti, `vulkanvideo` su RADV 26.2.x freeworld.
- Se l'avvio di `gnome-session` da un figlio REMOTIX con `pam_selinux` presente e `setexeccon(NULL)` funziona, o con un modulo SELinux di REMOTIX.
- Il «Force Stop» con il prodotto vero (ramo SIGTERM del figlio, nessuna rinascita, 0x10 ai client, dconf e user manager puliti).
- Quante volte GDM 51 tollera i fallimenti ripetuti di `gnome-session` (A1) prima di fermarsi.
- Il caso «riavvio dal menu della schermata di accesso» su Fedora (voce C6): `pkcheck` dalla sessione del greeter con systemd 262.
- `dconf-service`/`gsettings monitor` con le variazioni a sessione viva; `xdg-desktop-portal` nato prima/dopo il profilo di runtime.
- Differenze fra Mutter/gnome-shell 51.0 (banco) e 51.1 (repository di oggi).
- Utenti SELinux confinati (`user_u`, `staff_u`); installazioni minime senza `gnome-session-wayland-session`; sistemi con `sssd`/`winbind` in authselect.
- Un utente nuovo (senza `~/.config`): primo accesso remoto (tour, initial-setup, collezione `Login` mai creata).
- RealtimeKit e l'attesa audio di 25 s (B2) su Fedora.

## Prove consigliate (le decide il proprietario: nessuna è stata lanciata oltre agli studi sopra)

1. Costruire il pacchetto (RPM o albero di prova) con `remotix.pam` senza `pam_selinux`, installarlo sulla VM `gnome` (snapshot `pulito` come ritorno) e ripetere il giro completo: login, cattura, input, logout, riavvio del servizio con desktop aperto (A1), accesso locale con remoto attivo.
2. Ripetere con `pam_selinux` presente e `setexeccon(NULL)` nel figlio (se si vuole mantenere la riga).
3. Con la Radeon: RPM Fusion freeworld, `remotix` con codifica reale da un browser (misure: fotogrammi, latenza), con e senza i driver freeworld (deve dire chiaro «nessun codificatore»).
4. `check-desktop.py` (`power-implied`, `power-entries-absent`, `power-local-seat`) con systemd 262 e dalla schermata di accesso (C6).
5. A1 completo con il codice nuovo: desktop remoto aperto → `systemctl restart remotix` → accesso locale; poi SIGKILL del servizio e accesso locale (orfano `closing`), controllando i core dump e le variabili.
6. «Force Stop» di GDM con il prodotto vero.
7. dconf: prova con `gsettings monitor` e cambio tastiera a sessione viva (D-bis.2), e con un app Flatpak e snap-equivalenti che leggono il portale Settings.
8. Prova di un utente nuovo (primo accesso).
9. Prova con `with-faillock` attivo in authselect (ban table di REMOTIX + faillock insieme).

## Che cosa ho cambiato nella VM `gnome` (Fedora 45, `rx-gnome`)

- **Pacchetti installati (con `dnf`):** `gcc`, `pam-devel` (e dipendenze) per costruire la sonda di studio; `libva-utils`, `vulkan-tools`, `pciutils`;
  repository **RPM Fusion Free** (`rpmfusion-free-release-45`: installa `rpmfusion-free`, `rpmfusion-free-updates`, chiavi) dichiarato qui; `mesa-va-drivers-freeworld` 26.2.7 e
  `mesa-vulkan-drivers-freeworld` 26.2.7 (quest'ultimo ha sostituito `mesa-vulkan-drivers`); **conseguenza non voluta:** `mesa-dri-drivers`, `mesa-libEGL`, `mesa-libGL`, `mesa-libgbm`, `mesa-filesystem`,
  `mesa-vulkan-drivers` sono passati da 26.2.3 a 26.2.7 (dipendenza di freeworld). Nessun `dnf upgrade` dell'intero sistema.
  Ogni `dnf install` ha stampato «Pending offline transaction has been invalidated»: ha annullato un aggiornamento offline in attesa (se ce n'era uno di GNOME Software).
- **Flatpak:** nell'home di `prova2`: remoto `fedora` (OCI) nella sua installazione utente, `org.gnome.Calculator` + runtime `org.fedoraproject.Platform` f45 (~1,1 GB) in `/home/prova2/.local/share/flatpak`.
- **Sonda di studio** (installata e poi **tolta**): `/usr/libexec/rxstudy/`, `/etc/pam.d/rxstudy`, `/etc/systemd/system/rxstudy.service` (rimossi); `daemon-reload` eseguito.
  Restano in `/var/tmp/probe/` e `/var/tmp/*.sh`, `*.log` i sorgenti e i registri delle prove; `/var/tmp/src/` con i sorgenti scaricati (gdm, gnome-session, gnome-shell, mutter, gnome-remote-desktop, dconf, flatpak, mesa).
- **authselect:** modificata a mano `/etc/authselect/postlogin` (poi rigenerata da `apply-changes`); creato `/etc/authselect/custom/remotix-study` e selezionato, poi rimesso `local with-silent-lastlog with-mdns4`
  e cancellato il profilo; **restano due copie in `/var/lib/authselect/backups/2026-11-21-16-25-22.*` e `…-28.*`**; stato ripristinato (`diff -r /etc/authselect` con la copia: identico). Copia di sicurezza in `/var/tmp/authselect.orig`.
- **dconf:** creato e poi cancellato `/etc/dconf/db/remotix` (+`remotix.d`) e `/run/user/1001/dconf/profile`.
- **Sessioni e utenti:** accesso locale grafico di `prova` (poi terminato), accesso locale di `prova2` tentato due volte dalla schermata di accesso (una chiusa da «Force Stop», una fallita per orfano); sessioni di prova di `prova2` terminate.
  **Core dump** di `gnome-session-init-worker` in `coredumpctl` (due). Il file `~/.config/gnome-initial-setup-done` e dati di GNOME in `/home/prova2` e `/home/prova` creati dai desktop.
- **Radeon:** presa una volta (circa 6 minuti) per `vainfo`, `vulkaninfo` e un avvio headless; rilasciata (`spegni` → `accendi gnome virtuale`). Al termine la VM viene spenta.
- **Un incidente da dichiarare:** nei primi minuti ho messo script di aiuto (`g.sh`, `vm.sh`) in `/tmp/claude-1000/` e poi nel `scratchpad` condivisi con gli altri agenti; sono stati sovrascritti da altri agenti (e un loro `g.sh`
  puntato su `xfce` ha eseguito comandi di sola lettura sulla loro macchina al posto della mia: `loginctl`, `ps` — nessuna modifica). Le mie VM sono sempre state avviate con le porte standard (2351/8851), mai con porte diverse.
  Il fatto che il guest `rx-gnome` abbia risposto al posto di `xfce` è compatibile con lo scambio inverso (un loro comando passato per un mio script): causa non accertata. Da allora uso `scratchpad/gnome-agent/` e controllo `hostname` prima di ogni comando.
