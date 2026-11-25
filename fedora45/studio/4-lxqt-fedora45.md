# 4 - LXQt su Fedora 45 (LXQt Spin, Live 45-1.4)

Studio del 21 nov 2026, agente 4, macchina virtuale `lxqt` (porta ssh 2354). Solo osservazione: il prodotto non è stato
costruito né installato. Legenda: **[V]** verificato (dove), **[W]** dal web / dai sorgenti letti, **[S]** supposizione.
Il banco ha un limite dichiarato dal revisore: la tastiera della VM è solo `KEYMAP=us` in `/etc/vconsole.conf`, senza
disposizione grafica; non se ne traggono conclusioni su Fedora.

Letti prima: `ubuntu26.04/docs/REGISTRO-problemi.md`, `studio/7-xubuntu-lubuntu.md`, `studio/13-riunito-xfce-lxqt.md`,
`src/session.c`/`session.h` (rami LXQt), `src/remotix.pam`, `debian/remotix.pam-config`, `debian/control`, `src/local_login.c`.

## 1. Che cosa c'è (versioni vere)

| Componente | Fedora 45 (VM) | Ubuntu 26.04 (studio 7) |
|---|---|---|
| lxqt-session | 2.4.0-3.fc45 [V `rpm -q`] | 2.3.0 |
| lxqt-panel | 2.4.1-2.fc45 [V] | 2.3.2 |
| lxqt-wayland-session | 0.4.1-2.fc45, **installato di serie** [V] | 0.3.1, non installato |
| pcmanfm-qt | 2.4.1-1.fc45 [V] | - |
| Qt | qt6-qtbase 6.11.2-3.fc45 [V]; il plugin `libqwayland.so` sta dentro `qt6-qtbase-gui` (nessun `qt6-qtwayland` separato); **nessun Qt5** installato [V] | Qt6 + qlipper (Qt5) |
| sddm | 0.21.0-16.fc45 [V] | 0.21.0 |
| systemd | 262-3.fc45 [V] | 257 |
| PipeWire / WirePlumber | 1.6.9 / 0.5.18 [V] | - |
| Xwayland | 24.1.13 (ISO), 24.1.15 negli updates [V] | - |
| **labwc** | **NON installato di serie**; nel repository `fedora`: **0.20.2-2.fc45** [V `dnf repoquery`, installato e provato] | 0.9.3 |
| **wlroots** | non installato di serie; 0.20.2-2.fc45 (arriva come dipendenza di labwc) [V] | 0.19.2 |
| wlr-randr | non installato di serie; 0.5.0-4.fc45 [V] | - |
| miriway (Mir) | **installato di serie**, 26.08-1.fc45 [V] | - |
| openbox | 3.6.1-32.fc45 (sessione X11 `openbox.desktop`) [V] | - |
| xdg-desktop-portal | 1.22.1 + `xdg-desktop-portal-gtk` 1.15.3; **nessun `xdg-desktop-portal-lxqt`** [V] | - |
| lxqt-policykit | 2.4.0-2.fc45 [V] | - |
| qlipper, blueman, picom | **assenti** [V `rpm -q`] | qlipper e picom presenti |
| SELinux | `selinux-policy-targeted 45.23`, enforcing [V] | AppArmor |
| firewalld | 2.5.2, attivo [V] | ufw |
| polkit | 127-5.fc45 [V] | - |

Sessioni offerte [V `ls`]: `wayland-sessions/lxqt-wayland.desktop` (`Exec=startlxqtwayland`, pacchetto `lxqt-wayland-session`),
`xsessions/lxqt.desktop` (`Exec=startlxqt`), `xsessions/openbox.desktop`. Xorg c'è (`xorg-x11-server-Xorg 21.1.24`),
quindi la sessione X11 esiste ancora.

`lxqt-session` ha come `Requires` **`lxqt-wayland-session`** (hard); questo ha i sottopacchetti `lxqt-miriway-session`,
`lxqt-labwc-session`, `-niri-`, `-river-`, `-sway-`, `-wayfire-`, `-x11-session` e
`lxqt-wayland-session-default-compositor-miriway` (porta il file `/usr/share/lxqt/wayland/default-compositor` = `miriway`)
[V `rpm -qR`, `dnf repoquery`]. `lxqt-labwc-session` **non** è installato; non serve a REMOTIX (vedi §3).

## 2. L'accesso locale vero (termine di paragone)

### 2.1 Schermata di accesso: sddm con greeter **Wayland su miriway**
- Il pacchetto `sddm-wayland-miriway-26.08-1.fc45` porta `/usr/lib/sddm/sddm.conf.d/miriway.conf` con `DisplayServer=wayland`,
  `CompositorCommand=/usr/bin/miriway --add-wayland-extensions=zwlr_layer_shell_v1`, `GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell`
  [V `rpm -ql`, `cat`]. `/etc/sddm.conf` è quasi vuoto (solo intestazioni di sezione); `/etc/sddm.conf.d/` vuota. Il greeter gira come
  utente `sddm` (uid 984), sessione logind `c1` classe `greeter`, `seat0`, `tty1` [V `loginctl`].
- Messaggio nel journal: `The configured theme "01-breeze-fedora" doesn't exist, using the embedded theme instead` [V]: tema greeter di serie
  mancante nella VM (nessun effetto sul resto). Foto della schermata: `/media/REMOTIX-FEDORA/studio/lxqt/greeter.png` (menu «Session: LXQt (Wayland)»,
  pulsanti riavvio e spegnimento in alto a destra) [V].
- sddm `RememberLastSession=true`, `ReuseSession=true` (default dell'esempio di configurazione) [V `sddm --example-config`]. «ReuseSession»
  è per l'accesso con un'altra sessione sddm; non è un controllo «stesso utente con altra sessione grafica».

### 2.2 Quale sessione parte in un accesso locale: **LXQt (Wayland) dentro miriway**, non labwc, non X11
Osservato [V]: dalla schermata di accesso, `prova` / `prova2026` → sessione logind **15: `Type=wayland`, `Class=user`, `Desktop=LXQt`, `Seat=seat0`,
`VTNr=2`, `Service=sddm`, `State=active`**. Albero dei processi: `/usr/bin/sh /usr/bin/startlxqtwayland` → `miriway-shell` (Mir, con Xwayland
attivabile) + `lxqt-session` e i moduli. Il compositor viene scelto da `compositor=miriway` in `/etc/lxqt/session.conf` (pacchetto `lxqt-session`;
stesso valore in `/usr/share/lxqt/session.conf`) [V]. `startlxqtwayland` (script upstream 0.4.1, letto per intero) cerca la chiave
`compositor=` in `$XDG_CONFIG_HOME/lxqt/session.conf`, poi in `$XDG_CONFIG_DIRS/lxqt/session.conf`; Con `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share` (valore osservato) il file trovato è `/etc/lxqt/session.conf` (`/etc` + `lxqt/session.conf`) [V: la sessione è partita con miriway]. Il valore
`XDG_CURRENT_DESKTOP=LXQt:miriway:mir` [V]. Il file `~/.config/lxqt/session.conf` creato al primo accesso contiene solo `[General] __userfile__=true` [V].
Sul ramo labwc lo script usa `labwc -C ~/.config/lxqt/labwc -S lxqt-session` e `LABWC_CONFIG_DIR` (letto) [V lettura, non eseguito da sddm].

Se invece `compositor=` fosse vuoto: ramo «firstrun» con labwc e un avviso «No compositor is selected» [V lettura].

Il comportamento di sessione sotto miriway: `lxqt-wrapper` (`/usr/share/lxqt/wayland/miriway/lxqt-miriway-wrapper`) avvia `miriway-shell` con `MIR_SERVER_ENABLE_X11=1`,
`MIRIWAY_DECORATIONS=prefer-ssd`, `MIRIWAY_CONFIG_DIR=lxqt`, poi `lxqt-session`; quando lxqt-session esce, uccide miriway [V lettura].

### 2.3 Ambiente della sessione locale (da `/proc/<lxqt-session>/environ`) [V]
`DESKTOP_SESSION=lxqt-wayland`, `XDG_CURRENT_DESKTOP=LXQt:miriway:mir`, `XDG_SESSION_DESKTOP=LXQt`, `XDG_SESSION_TYPE=wayland`,
`XDG_SESSION_CLASS=user`, `XDG_SESSION_ID=15`, `XDG_SEAT=seat0`, `XDG_SEAT_PATH`, `XDG_SESSION_PATH`, `XDG_VTNR=2`, `WAYLAND_DISPLAY=wayland-0`,
`DISPLAY=:0` (Xwayland di Mir), `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`, `XDG_MENU_PREFIX=lxqt-`,
`QT_QPA_PLATFORMTHEME=lxqt`, `QT_PLATFORM_PLUGIN=lxqt`, `QT_ACCESSIBILITY=1`, `QT_AUTO_SCREEN_SCALE_FACTOR=0`, `QT_EXCLUDE_GENERIC_BEARER=1`,
**`QT_QPA_PLATFORM` non impostata** (Qt sceglie wayland da solo), `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share`,
`XDG_DATA_DIRS=~/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share:/usr/share`, `SSH_ASKPASS=/usr/libexec/openssh/lxqt-openssh-askpass`,
`EDITOR=/usr/bin/nano`, `DEBUGINFOD_*`, `LANG=en_US.UTF-8`, `PATH=~/.local/bin:~/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin`.
Dal journal sddm: `Starting Wayland user session: "/etc/sddm/wayland-session" "startlxqtwayland"`: lo script `/etc/sddm/wayland-session` rilancia la shell dell'utente
**come login shell** (`--login`) per bash, quindi `/etc/profile` e `/etc/profile.d/*` girano: da lì vengono `EDITOR`, `SSH_ASKPASS` (profile.d `lxqt-openssh-askpass.sh`),
`DEBUGINFOD_URLS`, la lingua da `/etc/locale.conf`, `PATH`. Il gestore utente systemd ha un ambiente diverso: `PATH=/usr/local/bin:/usr/bin` e `LANG`, `XDG_DATA_DIRS` con flatpak
(generatore `60-flatpak`) [V `systemctl --user show-environment`].
Il file `/etc/environment` non esiste su Fedora, `pam_env` non porta PATH [V]: vedi problema 8.

### 2.4 Processi della sessione locale (utente `prova`, SELinux `unconfined_u:unconfined_r:unconfined_t`) [V]
Sotto `lxqt-session`: `geoclue-2.0/demos/agent`, `pcmanfm-qt --desktop --profile=lxqt`, `lxqt-notificationd`, `lxqt-panel`, `lxqt-policykit-agent` (da `/usr/libexec`),
`lxqt-runner`, `nm-applet`, **`dnfdragora-updater`** (python3), `lxqt-powermanagement` (partito dopo). Nel gestore utente: `dbus-broker`, `gvfsd`, `gvfsd-trash`,
`gvfs-udisks2-volume-monitor`, `gvfsd-metadata`, `at-spi-bus-launcher`, `at-spi2-registryd`, `pipewire`, `wireplumber`, `pipewire-pulse`.
**Non** partono: qlipper, blueman, picom, xscreensaver (l'autostart `lxqt-xscreensaver-autostart.desktop` ha `X-LXQt-X11-Only=true`; `xscreensaver-autostart.desktop` ha
`OnlyShowIn=X-NODEFAULT;`), orca (`OnlyShowIn=GNOME;MATE;...`), `localsearch-3` (non LXQt), `lxqt-globalkeyshortcuts` [V elenco `ps`/`/etc/xdg/autostart`].
Elenco `/etc/xdg/autostart` [V]: at-spi-dbus-bus, geoclue-demo-agent, `liveinst-setup` (residuo della live: `anaconda-live`, probabile artefatto della costruzione della VM [S]),
localsearch-3, lxqt-desktop, lxqt-globalkeyshortcuts, lxqt-notifications, lxqt-panel, lxqt-policykit-agent, lxqt-powermanagement, lxqt-runner, lxqt-xscreensaver-autostart,
nm-applet (`NotShowIn=KDE;GNOME`), orca-autostart, `org.mageia.dnfdragora-updater`, spice-vdagent, vboxclient, vmware-user, xdg-user-dirs, xscreensaver-autostart.
`/etc/xdg/` ha anche `xdg-miriway/` e `lxqt/panel.conf` (pannello: `fancymenu,desktopswitch,quicklaunch,taskbar,statusnotifier,tray,mount,volume,worldclock,showdesktop`) [V].
**Non** esiste una cartella `/etc/xdg/xdg-<Nome>` stile Lubuntu: `lxqt-themes-fedora 2.4.0` è un pacchetto **senza file** (solo `Requires: breeze-cursor-theme, breeze-icon-theme,
fedora-logos, lxqt-themes`) [V `rpm -ql`/`rpm -qR`]; le impostazioni Fedora stanno in `/etc/lxqt/{session,lxqt,notifications}.conf` (`lxqt-session`: tema `Clearlooks`, icone `breeze`, cursore
`breeze_cursors`, `leave_confirmation=true`, `window_manager=openbox`) [V `cat`].

### 2.5 Stato di logind, D-Bus e systemd-utente nell'accesso locale [V]
- `org.lxqt.session` sul bus utente, proprietario `lxqt-session`; interfaccia `org.lxqt.session` con `canLogout/canPowerOff/canReboot/execDesktopFile/listModules/logout/powerOff/reboot`
  (`logout` e `powerOff`/`reboot` sono `no-reply`) [V `busctl introspect`]. Il gestore utente è un servizio separato (sessione `manager`).
- **`graphical-session.target` è `inactive`** durante tutta la sessione LXQt locale: `lxqt-session` e miriway non lo avviano. Conseguenza osservata: `xdg-desktop-portal.service`
  (`Requisite=graphical-session.target`) non parte (journal utente: `Dependency failed for xdg-desktop-portal.service`) e Qt scrive in `~/.cache/wayland-errors`:
  `qt.qpa.services: Failed to register with host portal ... startup job failed`. È lo stato normale dell'accesso locale: **la sessione remota non perde nulla** a non avviare il portale.
- Altri messaggi in `~/.cache/wayland-errors` (errore locale, innocui): `Currently tray plugin supports X11 only` / `Can't load plugin "tray"` (il plugin `tray` del pannello è solo X11; resta `statusnotifier`),
  `kf.idletime: Could not find any system poller plugin`, `nm-applet Gtk-CRITICAL`, avvisi miriway su flatpak e AppArmor.
- **Spegnimento/riavvio dal posto locale**: `CanPowerOff`/`CanReboot`/`CanSuspend`/`CanHalt` rispondono `challenge`, `CanHibernate` `na` (per la sessione `user` attiva); `pkcheck --action-id
  org.freedesktop.login1.reboot` e `.power-off` da un processo di `lxqt-session` → **autorizzati (rc=0)** [V]. È lo stesso caso C6 del registro: senza la regola REMOTIX l'utente seduto può riavviare.
- Voci di spegnimento: `lxqt-leave` (`/usr/bin/lxqt-leave`, `OnlyShowIn=LXQt;`, `Categories=System;X-Leave`) e `lxqt-{shutdown,reboot,suspend,hibernate,lockscreen,logout}.desktop` in
  `/usr/share/applications` (pacchetto `lxqt-session`), stessi nomi di Debian/Ubuntu: la tecnica di `settings_lxqt()` (`Hidden=true` in `data-lxqt`) vale invariata [V elenco file; il resto S].
  `/usr/share/lxqt/globalkeyshortcuts.conf` (Ctrl+Alt+T qterminal, luminosità) non ha scorciatoie di spegnimento [V `head`].
- **Uscita** `busctl --user call org.lxqt.session /LXQtSession org.lxqt.session logout`: la sessione 15 sparisce, nessun processo `lxqt-session/miriway/startlxqtwayland/Xwayland` resta,
  nel gestore utente restano solo i soliti servizi (pipewire, gvfs, at-spi, dbus-broker; l'utente era tenuto vivo anche da ssh); sddm riapre il greeter (`c2`); journal: `pam_unix(sddm:session): session closed for user prova`.
  [V; il tempo preciso non l'ho misurato, ma tutto era concluso entro la prima osservazione a 1 s e confermato a 25 s].

### 2.6 PAM dell'accesso locale [V]
`/etc/pam.d/sddm` (pacchetto `sddm`, **non** generato da authselect): `auth substack password-auth` + `pam_gnome_keyring/kwallet5/kwallet/oo7` facoltativi (con trattino davanti) + `include postlogin`;
`account required pam_nologin.so`, `include password-auth`; sessione: `pam_selinux.so close`, `pam_loginuid`, `pam_ck_connector` (facoltativo), `pam_selinux.so open`, `pam_keyinit`, `pam_namespace`,
**`session include password-auth`** (qui c'è `pam_systemd.so`, riga `-session optional pam_systemd.so`), poi `-session optional pam_gnome_keyring.so auto_start` e simili, poi `include postlogin`.
`sddm-greeter`: `pam_permit` (nessuna autenticazione). `/etc/pam.d/sddm-autologin` simile. Non ci sono `gnome-keyring`, `kwallet-pam` né `oo7`/`pam_oo7` installati nel Spin LXQt: **nessun portachiavi** in LXQt Spin [V `rpm -q`].
`pam_faillock` **non** è nello stack (authselect `local`, funzioni attive `with-silent-lastlog`, `with-mdns4`) [V `cat /etc/authselect/password-auth`; `authselect current`]: un tentativo errato (battuta sbagliata) ha dato solo
`Login failed` nella schermata, senza blocco.

## 3. Come REMOTIX avvia LXQt oggi, e che cosa regge su Fedora 45

Oggi (codice Ubuntu, identico per Debian) [V lettura]: `labwc -C $XDG_RUNTIME_DIR/remotix/labwc-lxqt -S "<sh -c wlr-randr ...; exec lxqt-session>"` con `WLR_BACKENDS=headless`, `WLR_LIBINPUT_NO_DEVICES=1`,
`WLR_RENDER_DRM_DEVICE=<nodo>` (o `WLR_RENDERER=pixman` senza scheda) (`session.c:3519-3565`, `session.h:219-227`, `session.c:4130-4200`, `measured_primary()` `session.c:4237`); ambiente `XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots`,
`QT_QPA_PLATFORM=wayland`, `QT_QPA_PLATFORMTHEME=lxqt`, `XDG_MENU_PREFIX=lxqt-`, `XDG_CONFIG_DIRS=<xdg-lxqt>:...:/etc/xdg:/usr/share` (`session.c:3470-3525`); «viva» = nome `org.lxqt.session` sul bus utente (`session.c:1063-1072, 1332`);
uscita `org.lxqt.session.logout()` (`session.c:~3750`); voci pericolose `Hidden=true` (`session.c:6155-6290`, `5719-5850`). Marcatore: `lxqt-session` nel PATH (`SESSION_MARKER_LXQT`). Il labwc è quello **di sistema** (cercato nel PATH), non quello
patchato per KDE.

### 3.1 Prova diretta su Fedora 45 [V, nella VM, utente `prova`, senza sessione grafica, via ssh]
Dopo `dnf install labwc wlr-randr` (nessun altro pacchetto è stato necessario per LXQt) ho rifatto l'avvio nella forma di REMOTIX (cartella di configurazione vuota con `rc.xml` e `autostart` come nostri, `HOME` pulita):
1. **`labwc 0.20.2` + `wlroots 0.20.2` headless funzionano**: `wlr-randr` elenca `HEADLESS-1` 1280x720; `wlr-randr --output HEADLESS-1 --custom-mode 1344x768` → rc=0 e la modalità cambia; `grim` (screencopy) scatta lo schermo.
2. **Protocolli annunciati** (da `wayland-info`) [V]: `zwlr_screencopy_manager_v1 v3`, `ext_image_copy_capture_manager_v1`, `zwlr_export_dmabuf_manager_v1`, `zwlr_virtual_pointer_manager_v2`, `zwp_virtual_keyboard_manager_v1`, `zwlr_data_control_manager_v1 v2`,
   `ext_data_control_manager_v1`, `zwlr_layer_shell_v1 v4`, `zwlr_output_manager_v1 v4`, `ext_workspace_manager_v1`, `zwlr_foreign_toplevel_manager_v1`, `xdg_wm_base v6`, `zwp_pointer_constraints_v1`, `zwp_relative_pointer_manager_v1`,
   `zwp_text_input_manager_v3`, `zwp_input_method_manager_v2`; con la Radeon anche `zwp_linux_dmabuf_v1 v4`. Sono tutti i protocolli che `src/protocols/` e `wlr_input.c` usano (screencopy, virtual-pointer, virtual-keyboard, data-control, layer-shell, output-management, dmabuf).
3. **LXQt intera dentro labwc headless parte** (`lxqt-session` come `-S`): partono `pcmanfm-qt --desktop`, `lxqt-notificationd`, `lxqt-panel`, `lxqt-policykit-agent`, `lxqt-runner`, `nm-applet`, `dnfdragora-updater`, `lxqt-powermanagement`, `geoclue demo agent`; `org.lxqt.session`
   sul bus; `grim` dà un'immagine 1344x768 con sfondo, icone sul desktop, pannello in basso (menu, pagers, area di stato, orologio) (immagine vista sul tablet, copia solo nella cartella di lavoro temporanea, non nel repository) [V]. Xwayland parte su richiesta dentro labwc (`DISPLAY=:1` nell'ambiente dei figli; nm-applet è GTK/X; messaggio `Xwayland glamor: GBM Wayland interfaces not available ... falling back to sw` con `pixman`).
   Ho eseguito l'avvio con `QT_QPA_PLATFORM=wayland` bare **senza qlipper** (non c'è): nessun programma Qt5, quindi il vecchio dubbio «qlipper muore con wayland nudo» (§6.5 studio 7) non si pone su Fedora.
4. **Con la Radeon vera** (RX 6800, Navi 21, kernel 7.2.11, amdgpu, nodo `/dev/dri/renderD128` mode 0666 gruppo `render`): `labwc -d` con `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128` crea il **renderer GLES2 su Mesa 26.2.3 «AMD Radeon RX 6800 (radeonsi, navi21, ACO)»**,
   allocatore GBM sul nodo, `zwp_linux_dmabuf_v1 v4`, `grim` rc=0; la sessione intera LXQt parte con lo stesso renderer; senza avvisi seri nel log salvo `MESA-EGL: failed to open /dev/dri/card1: Permission denied` (innocuo, prova da utente senza seat) [V].
5. Nessun conflitto con la sessione locale quando l'utente è lo stesso solo se **non** convivono (vedi §4).

### 3.2 Che cosa cambia rispetto a Ubuntu/Debian
- **labwc 0.20.2 contro 0.9.3 (e wlroots 0.20.2 contro 0.19.2)**: il numero di versione salta molto. La prova sopra dice che le basi (headless, `wlr-randr --custom-mode`, screencopy, virtual pointer/keyboard, data-control) reggono. **Non provato**: input vero dal browser (puntatore assoluto, rotella, tastiera), clipboard, cursore, `-C` con `rc.xml` nostro (i tasti per riportare dentro le finestre, `SESSION_LABWC_KEY`, D-007), `-m` merge, la regola «finestre dentro quando lo schermo si restringe». Le opzioni di `rc.xml` possono essere cambiate da 0.9 a 0.20 [S]. Nessun `Static-Built-Using: labwc` serve per LXQt.
- `labwc` **non** è installato di serie sul Spin LXQt (come su Lubuntu) → REMOTIX deve chiederlo; su Fedora `labwc` ha `Requires: xdg-desktop-portal-wlr` e porta grim [V `rpm -q --requires`, `dnf install` ha tirato dentro `xdg-desktop-portal-wlr`, `grim`, `libseat`, `libliftoff`, `libsfdo`, `xcb-util-errors`, `wlroots`]. Installare `xdg-desktop-portal-wlr` aggiunge un backend di portale; da guardare se in una sessione remota (dove `graphical-session.target` dovrebbe comunque restare spento) diventa un problema [S].
- **Il compositor locale non è labwc ma miriway** (Mir): nessun dato sul suo comportamento deve essere copiato per labwc. Ma questo è un vantaggio: REMOTIX, che gira in un labwc suo, è **indipendente da ciò che parte in locale** (nessuna interferenza); non c'è motivo di usare miriway.
- **REMOTIX non deve usare la sessione `lxqt-wayland`/`startlxqtwayland`**: sceglierebbe miriway (`/etc/lxqt/session.conf`), che non ha `wlr-screencopy`/`wlr-virtual-pointer` garantiti [S: con `--add-wayland-extensions=all` Mir potrebbe offrirli, non verificato]. Resta la forma di oggi (`labwc -C ... -S lxqt-session`). Va solo tenuto conto che la variabile `XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots` coincide con la forma che `startlxqtwayland` darebbe a chi sceglie labwc [V lettura].
- **Cartelle Fedora**: non c'è `/etc/xdg/xdg-<nome>` né `/usr/share/<Nome>`; il codice D-153 (nome di sessione e cartelle proprie di Lubuntu: oggi azzerato in `local_session()`) **non serve** su Fedora; i default Fedora stanno in `/etc/lxqt/*.conf` e `/usr/share/lxqt/*.conf`.
  **Attenzione al ramo LXQt** (`session.c:3495-3510`): la catena `XDG_CONFIG_DIRS=<xdg-lxqt>:<sessione>/etc:/etc/xdg:/usr/share`. Su Fedora `lxqt-session` cerca i default in `/etc/lxqt/` (nel codice upstream «di sistema» `LXQT_...`/`XdgDirs::configDirs()` con `/etc` davanti: la mia sessione di prova con `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share` ha riconosciuto `/etc/lxqt/session.conf`, `/etc/lxqt/lxqt.conf` e il tema, come nella foto) — se REMOTIX togliesse `/etc` dalla catena, perderebbe il tema Fedora [S + V parziale]. Va tenuto `/etc` in testa come oggi (la forma `/etc:/etc/xdg:/usr/share` è proprio quella già usata).
- `lxqt-session` 2.4.0 avvia il window manager X11 (`window_manager=openbox` in `/etc/lxqt/session.conf`) solo se la piattaforma è `xcb` [S: confermato per 2.3.0 in studio 7, non riletto per 2.4.0]; con `QT_QPA_PLATFORM=wayland` è ignorato. La finestra «X Compositor crashed too many times» di Lubuntu veniva da `picom`: su Fedora `picom` e `compton` non esistono nei pacchetti installati [V `rpm -q`] e nessun autostart lancia un compositore X: **il problema non dovrebbe presentarsi** [V assenza, S esito].
- `dnfdragora-updater` (autostart `org.mageia.dnfdragora-updater.desktop`, nessun filtro `OnlyShowIn`) parte in ogni sessione LXQt e **scarica i metadati dei repository all'accesso** (eventi `OnDownloadStart/Progress` nel log; ~6 MB dagli «updates», 38 MB da «fedora») [V: `~/.cache/wayland-errors`]. In una macchina con tanti utenti remoti, ognuno lo lancia: equivalente del «Lubuntu Update» (R-DE-?, `lubuntu-update` contava i processi di tutti gli utenti). Decisione/misura da prendere (§Decisioni).
- `nm-applet` parte (su Lubuntu era `Hidden=true`); `geoclue` demo agent parte; `spice-vdagent`, `vboxclient`, `vmware-user` partono se il modulo c'è e si trovano nella VM [V: errore `vmware-user: could not open /proc/fs/vmblock/dev`]; non ci sono su una macchina vera.
- **`qlipper` assente**: la decisione 16 nov «si lascia» non riguarda Fedora. Non c'è un gestore degli appunti: la clipboard del browser passa dal protocollo data-control di labwc [V protocolli annunciati; non provata con il browser].
- **Tray**: il plugin `tray` del pannello è solo X11 («Can't load plugin tray» anche in locale); nei pannelli di REMOTIX resta `statusnotifier` [V].

## 4. Convivenza con sddm e locale/remoto (voce A2 del registro)

### 4.1 Prova della voce A2 su sddm Fedora [V, riprodotta]
Per simulare «desktop remoto vivo dello stesso utente» ho lasciato girare, come `prova`, la sessione LXQt dentro labwc headless (il mio test, `lxqt-session` con `org.lxqt.session` sul bus `/run/user/1000/bus`), poi ho fatto l'accesso locale con la schermata sddm:
- sddm accetta la password e apre la sessione logind (`session opened for user prova`, sessione 43, Wayland), avvia `startlxqtwayland`, miriway parte (`Mir is starting up` alle 17:16:07.256) e **`Mir is shutting down` alle 17:16:07.472**, sessione chiusa (`session closed for user prova`) e il greeter si ripresenta: **la sessione locale muore in ~0,3 secondi e si torna alla schermata di accesso** (`/media/REMOTIX-FEDORA/studio/lxqt/l4.png`; journal `sddm-helper`, `~/.cache/wayland-errors`).
- La causa più probabile è che `lxqt-session` del locale non riesce a prendere il nome `org.lxqt.session` (già usato dalla sessione dell'altro desktop sullo stesso bus utente) e esce, e il wrapper uccide miriway [S: coerente con l'orario e con lo studio 7; non ho letto il motivo dell'uscita di lxqt-session]. Il controllo senza altra sessione (accesso locale pulito) era riuscito prima.
- Quindi, su Fedora, **sddm non trattiene l'utente** come previsto dal registro (A2): il difetto c'è come per KDE/XFCE (qui non «LXQt senza sfondo» ma ritorno al greeter, perché miriway muore insieme a lxqt-session).
- Il sistema è rimasto sano: nessun processo orfano dopo il ritorno al greeter (la sessione di prova di labwc è rimasta viva fino al suo timeout), nessun blocco.

### 4.2 Il gancio PAM (`remotix-local-login`, §11.57) su Fedora: due ostacoli veri
1. **Dove agganciarlo**. Su Debian è `pam-auth-update` + `/usr/share/pam-configs/remotix` → `common-session`. Su Fedora **non c'è** un equivalente a drop-in: i file sono
   `/etc/pam.d/sddm` (di proprietà del pacchetto `sddm`, `%config`), e `password-auth`/`system-auth`/`postlogin` sono **link a `/etc/authselect/*`, riscritti da authselect** [V `ls -l`, `rpm -qf`]: una riga aggiunta lì viene cancellata al prossimo `authselect select/apply-changes/enable-feature`.
   `authselect` non ha un modo di aggiungere una riga a un profilo vendor: l'unica strada «legale» è un **profilo personalizzato** (`authselect create-profile`, in `/etc/authselect/custom/`) basato su `local` con un file `postlogin` o `system-auth` modificato, e poi `authselect select custom/remotix` — cambia la configurazione globale dell'autenticazione e va fatto/ripristinato con cura [S, da `authselect` 1.8.0 man; non provato].
   Alternative: (a) riga `pam_exec` messa direttamente in `/etc/pam.d/sddm` (e `sddm-autologin`, `lightdm`, `gdm-password`, `plasmalogin` per gli altri gusti) dallo scriptlet: `rpm -V` e gli aggiornamenti di `sddm` genererebbero `.rpmnew`; (b) profilo authselect personalizzato (tocca TUTTI i servizi); (c) niente gancio, solo i controlli periodici del servizio (come dice il registro, «dirlo all'installazione»). **Decisione del proprietario.**
   `pam_systemd.so` sta in `password-auth` (inclusa da sddm): la riga REMOTIX deve venire **dopo** `include password-auth` in `/etc/pam.d/sddm` (e dopo il blocco `pam_gnome_keyring ... auto_start`, indifferente) [V ordine].
2. **SELinux blocca il gancio in silenzio** [V policy `selinux-policy-targeted 45.23`, `sesearch`, non provato dal vero con un pacchetto]: `sddm-helper` gira in **`xdm_t`** (confinato) [V `ps -eZ`: `system_u:system_r:xdm_t:s0-s0:c0.c1023`]; `pam_exec` esegue il programma di REMOTIX (etichetta `bin_t` di default per `/usr/libexec(/.*)?` [V `semanage fcontext -l`]) **dentro lo stesso dominio `xdm_t`** (nessuna transizione: `xdm_t` può eseguire `bin_t` senza cambiare dominio [V `allow login_pgm base_ro_file_type:file { execute execute_no_trans }`]).
   Ora `/run/remotix/prelocal/` e il file `.lock` sarebbero creati dal servizio (dominio `unconfined_service_t`, vedi §5) con l'etichetta di default **`var_run_t`** [V `semanage fcontext`: `/run/.* → var_run_t`]; e `sesearch -A -s xdm_t -t var_run_t -c file` **non dà alcun permesso** `create/write/open/unlink/lock/getattr/read` per `xdm_t` su file `var_run_t` (cartelle: sì `add_name/remove_name/write` per `login_pgm`; file: **0 regole**) [V]. Quindi `remotix-local-login` non potrebbe aprire il `.lock` né creare la richiesta `/run/remotix/prelocal/<uid>`: il programma non fa mai fallire un accesso (resta `optional`, esce 0), ma **la protezione A2 non funzionerebbe** e nel `journal` comparirebbero AVC `denied` (provenienza `sddm-helper`/`remotix-local-login`).
   Rimedio da progettare: un piccolo **modulo SELinux** nel pacchetto (nuovo tipo `remotix_var_run_t` per `/run/remotix(/.*)?` con regole per `xdm_t`, `lightdm_t`, `plasmalogin_t`/`xdm_t`, `gdm_t` e per `unconfined_service_t`, installato con `semodule` in `%post`, rimosso in `%postun`; per la costruzione serve `selinux-policy-devel 45.24` [V repo]) oppure un'etichetta esistente già scrivibile da `xdm_t` (es. `xdm_var_run_t`, `allow xdm_t xdm_var_run_t:file { create ... }` [V]) assegnata con `semanage fcontext` — meno pulito. **Non so dire** quale sia meglio senza provare; da provare il gancio vero (§Prove).
   Non verificato: se `pam_exec` con l'ambiente PAM porta `XDG_SEAT` anche con sddm Wayland (in sessione 15 logind ha `Seat=seat0`; nel journal `pam_systemd` è in `password-auth`) [V per la sessione, S per l'ambiente passato a `pam_exec`].

## 5. Sistema Fedora per il servizio e il pacchetto (parte comune, vista da LXQt)

- **authselect** `local` (versione 1.8.0), nessun `faillock` [V]: `/etc/pam.d/remotix` va scritto come copia dello `sshd` di Fedora (letto sopra, §2.6/`/etc/pam.d/sshd`): `auth substack password-auth` + `include postlogin`, `account required pam_sepermit.so`, `pam_nologin`, `include password-auth`, `session`: `pam_selinux close`, `pam_loginuid`, **`pam_selinux open env_params`**, `pam_namespace`, `pam_keyinit force revoke`, `pam_motd`, `include password-auth`, `include postlogin` [V `cat /etc/pam.d/sshd`]. `@include common-*` non esiste su Fedora (`@include` è un'estensione Debian: il nostro file attuale non vale). La riga `pam_listfile` di REMOTIX (root escluso) va **prima** di `auth substack password-auth` come oggi. Il file `/etc/pam.d/remotix` è un file di pacchetto (`%config(noreplace)`), non gestito da authselect; **non va in una sua configurazione**; se manca, PAM usa `other` che su Fedora è `pam_deny` [V `/etc/pam.d/other` dalla riga `other` presente, contenuto non riletto: S dalla `main.c`/`remotix.pam` del repo].
- **Il file locale `LANG`** su Fedora è `/etc/locale.conf` (`LANG=en_US.UTF-8`) [V]; non c'è `/etc/default/locale` né `/etc/environment`: la riga Ubuntu `pam_env envfile=/etc/default/locale` non serve e `child.c` (PATH da `pam_env`) dà solo il ripiego `/usr/local/bin:/usr/bin:/bin` (mancano `~/.local/bin`, `~/bin`, `sbin`) [V assenza del file, S effetto].
- **SELinux**: `enforcing`, `targeted`. Un servizio installato da RPM con eseguibile in `/usr/libexec/remotix/` (`bin_t`) avviato da systemd entra in **`unconfined_service_t`** (`type_transition init_t bin_t:process unconfined_service_t`, e `systemd-run /usr/bin/sleep` di prova: `ps -eZ` → `system_u:system_r:unconfined_service_t:s0`) [V]. `unconfined_service_t` ha l'attributo `unconfined_domain_type`, `corenet_unconfined_type` (può usare qualunque porta: la 7447 non ha etichetta `semanage port` [V], quindi `unreserved_port_t`, bind permesso `allow corenet_unconfined_type port_type:udp_socket { name_bind ... }`), `can_read_shadow_passwords`, `dbusd_unconfined`, `devices_unconfined_type` [V `seinfo`]. Quindi, **come processo unconfined, il servizio non incontra negazioni** — a differenza di AppArmor su Ubuntu (voce C4): niente profilo da scrivere per far funzionare il prodotto. **Che cosa prende il posto del profilo AppArmor**: nulla di serie; `remotix_network.apparmor` (il muro del lato rete) non ha un equivalente automatico: servirebbe un modulo SELinux che confini il lato rete in un dominio proprio (`remotix_net_t`) — lavoro grosso, **decisione del proprietario** (restare `unconfined_service_t` e basta o confinare).
  `pam_selinux open` nella sessione dei figli: un servizio `unconfined_service_t` può dare il contesto utente `unconfined_u:unconfined_r:unconfined_t` ai figli (`selinux_unconfined_type`), [S, da provare]; l'utente `prova` ha infatti `unconfined_t` [V `id -Z`].
  Nessuna negazione AVC trovata nei miei accessi locali e nelle prove (`ausearch -m avc`: 0 righe) [V].
- **firewalld**: attivo, zona `public` (default) per `enp0s1`, servizi `dhcpv6-client mdns ssh`, nessuna porta aperta [V `firewall-cmd --list-all`]: **7447 tcp+udp è chiusa di serie** (nota: il Spin LXQt ha `public`; la Workstation ha un'altra zona più permissiva: da confrontare con l'agente 1). Un pacchetto la apre in modo corretto con un file di servizio `/usr/lib/firewalld/services/remotix.xml` (porte `7447/tcp` e `7447/udp`) e **non** abilitato di default (decisione dell'amministratore, come oggi con ufw `debian/remotix.ufw`); il pacchetto `firewalld-filesystem` fornisce le macro RPM `%firewalld_reload` [V `rpm -q firewalld-filesystem`; l'uso delle macro: W].
- **polkit 127**: `50-default.rules` assegna agli amministratori il gruppo **`wheel`** (`polkit.addAdminRule → unix-group:wheel`) [V]; esiste anche una regola `empower.rules` (gruppo `empower`, tutto permesso) [V]. Le regole di REMOTIX vanno in `/etc/polkit-1/rules.d/` (cartella leggibile solo da root/polkitd) o `/usr/share/polkit-1/rules.d/` (lì stanno quelle di sistema) [V `ls`; mia scelta S].
  **Le 19 azioni vietate dalla regola attuale esistono tutte in `org.freedesktop.login1.policy` di systemd 262**; l'unica riga «in regola e non in policy» è il nome del file stesso (falso allarme del confronto): ho confrontato `src/remotix-no-poweroff.rules` con le `<action id>` Fedora [V `comm`]. Le implicazioni di systemd 262 sono quelle di C6: `set-reboot-parameter`, `set-reboot-to-firmware-setup`, `set-reboot-to-boot-loader-menu`, `set-reboot-to-boot-loader-entry` implicano `reboot` con `allow_active=yes`; `power-off`, `reboot`, `suspend`, `hibernate` hanno `allow_active=yes` e `halt` `auth_admin_keep` [V `python3` sul `.policy`]. Non compaiono azioni nuove di spegnimento. Il nuovo controllo `power-implied` va rilanciato su Fedora.
- **systemd**: preset di sistema `99-default-disable.preset` = `disable *` [V]: un servizio installato da RPM nasce **disabilitato** senza fare nulla; lo scriptlet standard è `%systemd_post/%systemd_preun/%systemd_postun_with_restart`; NON mettere `enable` in un preset proprio. `systemd-sysusers`/`systemd-tmpfiles` con i file `remotix.sysusers`/`remotix.tmpfiles` come oggi (macro `%sysusers_create_compat`, `%tmpfiles_create` [W, prassi Fedora]).
- **Kernel/rete**: `net.core.rmem_max = wmem_max = 4194304`, `fs.protected_regular=1`, `inotify max_user_watches` 40430 [V]. Utente `prova` in gruppo `wheel` ma non in `video`/`render`; `/dev/dri/renderD128` è `crw-rw-rw-` gruppo `render` (mode 0666): un utente senza seat usa il nodo di rendering senza gruppi [V ls + prova].
- **Video H.264/HEVC — il problema più grosso (comune ai quattro gusti)** [V con la Radeon, 5 minuti di scheda]:
  - `vainfo --device /dev/dri/renderD128` con `LIBVA_DRIVER_NAME=radeonsi`: driver *Mesa Gallium 26.2.3 for AMD Radeon RX 6800 (radeonsi, navi21, ACO, DRM 3.64, 7.2.11)*; profili: **MPEG2, JPEG, VP9 (VLD), AV1 (VLD)** e `VideoProc`: **nessun H.264, nessun HEVC, nessun entrypoint di codifica (EncSlice)**. libva cerca anche `/usr/lib64/dri-freeworld/` e `/usr/lib64/dri-nonfree/` (percorsi dei pacchetti RPM Fusion/terze parti).
  - `vulkaninfo`: GPU0 `AMD Radeon RX 6800 (RADV NAVI21)` Vulkan 1.4.354; estensioni video presenti: `video_queue`, `video_decode_queue`, `video_decode_av1`, `video_decode_vp9`, `video_encode_queue`, `video_encode_intra_refresh`, `video_encode_quantization_map`, `video_maintenance1/2` — **mancano `VK_KHR_video_encode_h264`, `VK_KHR_video_encode_h265` e anche i decode h264/h265** [V]. `vulkanvideo.c:758-760` rifiuta il dispositivo senza queste estensioni.
  - Quindi **su Fedora 45 di serie REMOTIX non può codificare** (il codice non ha più ripiego software: OpenH264/SVT-AV1 tolti, `encoder.c:25`, `child.c:7067`): il prodotto mostrerebbe «no desktop» finché non c'è un codec. La Radeon non codifica AV1 (Navi 21: nessun `EncSlice` AV1, [V vainfo]).
  - **RPM Fusion** (dichiarato: ho solo *interrogato* i repository `rpmfusion free fedora 45` e `updates/45` senza abilitarli) offre `mesa-va-drivers-freeworld-26.2.3/26.2.7-1.fc45` e `mesa-vulkan-drivers-freeworld-26.2.3/26.2.7-1.fc45` [V `dnf repoquery --repofrompath`, sito `mirror.netsite.dk`]: sono i pacchetti che rimettono H.264/HEVC. **Non provati** (non installati). Nel repository Fedora c'è `openh264-2.6.0-3.fc45` (repo `fedora-cisco-openh264`, abilitato; `mozilla-openh264`, `gstreamer1-plugin-openh264` 1.28.x): è il **codec software di Cisco**, usabile solo come decodificatore/codificatore software, non risolve da solo l'accelerazione hardware; REMOTIX non lo usa più [V repoquery].
  - `libavcodec-free 9.0.2` c'è (solo codec liberi) [V]; `ffmpeg-free` non installato.
- **Nomi dei pacchetti Fedora per `debian/control`** [V `dnf repoquery --whatprovides`]: `openssl-devel 4.0.3` (⚠ OpenSSL **4.0** nel repo; `openssl3-devel 3.5.9` come compatibilità: REMOTIX chiede ≥ 3.5 e ngtcp2 statico; ngtcp2 di Fedora è `ngtcp2-devel 1.22.1`, `libnghttp3-devel 1.19.0` — il pacchetto Debian incorpora ngtcp2 1.25.0 statico), `pam-devel`, `glib2-devel 2.90.1`, `pipewire-devel 1.6.11`, `libdrm-devel`, `libva-devel 2.24.1`, `opus-devel`, `zlib-ng-compat-devel`, `libei-devel 1.6.0`, `libxkbcommon-devel`, `mesa-libgbm-devel`, `wayland-devel`, `vulkan-loader-devel`, `meson`, `patch`, `hwdata`, `wayland-protocols-devel`, `libglvnd-devel` (EGL+GLES), `libinput-devel`, `pixman-devel`, `libseat-devel`, `systemd-devel` (libudev), `libdisplay-info-devel 0.3.0`, `libxml2-devel`, `cairo-devel`, `pango-devel`, `libpng-devel`; strumenti: `selinux-policy-devel 45.24`. Dipendenze d'uso: `pam`, `systemd`, `pipewire`, `wireplumber`, `dbus-broker` (la sessione utente su Fedora ha `dbus-broker`, non `dbus-daemon`; non esiste `dbus-user-session`), `labwc` (0.20.2), `wlr-randr`, `xorg-x11-server-Xwayland`, `dconf` (`dconf 51.0`; non `dconf-cli`), `mesa-dri-drivers` (contiene `radeonsi_drv_video.so`; non esiste un pacchetto separato `mesa-va-drivers` tra i miei risultati, il nome `mesa-va-drivers` viene risolto in `mesa-dri-drivers`), `mesa-vulkan-drivers`, `libva-intel-media-driver 26.3.5` (Intel, in repo), caratteri `dejavu-sans-fonts` (⚠ `google-dejavu-sans-fonts` non esiste). Non ho verificato le dipendenze di `rpm` (nomi `libssl.so.4`?) né la costruzione.
- **Regole RPM che toccano REMOTIX** [S, prassi Fedora]: file in `/etc` come `%config(noreplace)` (`/etc/pam.d/remotix`, `/etc/remotix/denied-users`); licenza `%license LICENSE.md`; macro `%systemd_*`; modulo SELinux nel pacchetto principale o in un sottopacchetto `remotix-selinux` (prassi); i codec non si portano nel pacchetto (`mesa-*-freeworld` è terza parte). Non provati.

## 6. Altri punti richiesti

- **Portachiavi/kwallet**: nessuno installato nel Spin LXQt (`gnome-keyring`, `kwallet`, `kwallet-pam`, `oo7`, `pam_oo7` assenti) [V `rpm -q`]; le righe `-auth optional pam_gnome_keyring.so` ecc. in `sddm` sono ignorate. Nessun «sblocco del portachiavi» da fare, né con nm-applet (i segreti Wi-Fi vanno nei file di NetworkManager). [V]
- **Agente polkit**: `lxqt-policykit-agent` (da `/usr/libexec/`, autostart `lxqt-policykit-agent.desktop`) parte come modulo di `lxqt-session` nella sessione locale e nella mia sessione tipo-REMOTIX [V].
- **Idle/blocco schermo**: `lxqt-powermanagement` parte; miriway ha `idle-timeout=600` nel suo file di configurazione LXQt (`miriway-shell.config`), ma è del compositor locale; sotto labwc non vale. Con la sessione di prova di 45 s non ho potuto misurare l'inattività di 15 minuti: [S] come su Lubuntu (nessuna azione di inattività in `/usr/share/lxqt/power.conf`: **non letto**).
- **X11 e Xwayland**: l'`Xwayland` di Fedora (24.1.13) lavora sotto labwc (nm-applet parte, `DISPLAY` impostato) [V].
- **Registro `~/.cache/wayland-errors`** nel locale ha tutto l'avvio di miriway/lxqt (file 4,9 KB per sessione, perso a ogni accesso). In REMOTIX il registro è `~/.local/state/remotix/session.log` come oggi.

## Problemi da affrontare

1. **Video: nessuna codifica H.264/HEVC su Fedora 45 di serie** (VA-API e Vulkan Video senza H.264/H.265, verificato con la Radeon): `src/vadirect.c`, `src/vulkanvideo.c:358-390,758-760`, `child.c:7067`, `debian/control` Recommends. Peso **GRANDE** (blocca il prodotto). Cura nota: parziale/no — su Ubuntu/Debian il driver Mesa ha i codec; qui servono `mesa-*-freeworld` di RPM Fusion (esistono per fc45) o un'altra via (nessun ripiego software esiste più). Decisione del proprietario.
2. **Il gancio PAM locale non funziona con SELinux**: `xdm_t` non può scrivere nei file `var_run_t` di `/run/remotix/prelocal` (`src/local_login.c`, `src/rootside.c` PL_DIR, `debian/remotix.pam-config`). Peso **MEDIO-GRANDE** (richiede un modulo SELinux nel pacchetto). Cura nota: no (su Ubuntu AppArmor non lo copre; su Debian SELinux assente).
3. **Dove agganciare il gancio PAM su Fedora**: non esiste un meccanismo come `pam-auth-update` (`/etc/pam.d/sddm` è del pacchetto sddm, `authselect` riscrive il resto) (`debian/remotix.postinst:36-46`, `debian/remotix.pam-config`). Peso **MEDIO**. Cura nota: no per Fedora (voce C1 del registro la menziona senza risolverla). Decisione del proprietario.
4. **Voce A2 confermata su Fedora/sddm**: sddm non trattiene; con un desktop remoto vivo l'accesso locale torna al greeter in ~0,3 s (`/media/REMOTIX-FEDORA/studio/lxqt/l4.png`). Peso **MEDIO** (dipende dal punto 3). Cura nota: sì, il gancio `remotix-local-login` (DECISIONS-11 §11.57), da portare su Fedora.
5. **labwc 0.20.2 / wlroots 0.20.2 (Ubuntu: 0.9.3 / 0.19.2)**: salto di versione grande; le basi (headless, screencopy, virtual input, dmabuf) funzionano, ma input/cursore/clipboard/`rc.xml`/finestre dentro (`session.c:3519-3565, 4130-4260`, `SESSION_LABWC_KEYBOARD`, `shape.c`, `wlr_input.c`) non sono stati provati. Peso **MEDIO** (da provare). Cura nota: no (nessuno studio sulla 0.20).
6. **`labwc`, `wlr-randr` assenti di serie nel Spin LXQt** (`xorg-x11-server-Xwayland` c'è) (`debian/control` Recommends → su Fedora `Requires`/`Recommends` RPM; `session.c:535,769`). Peso **PICCOLO**. Cura nota: sì, come Lubuntu (messaggio postinst e al login, voce 18 nov; per RPM lo scriptlet `%post` può dire lo stesso).
7. **`pam.d/remotix` per Fedora** non può usare `@include common-*` (estensione Debian): va riscritto sul modello di `/etc/pam.d/sshd` Fedora (`password-auth`, `postlogin`, `pam_sepermit`, `pam_selinux open env_params`) (`src/remotix.pam`). Peso **PICCOLO-MEDIO**. Cura nota: la nota del file stesso già dice «`other` su Fedora è `pam_deny`».
8. **PATH e lingua** della sessione remota: su Fedora non ci sono `/etc/environment` né `/etc/default/locale`; il PATH ripiego è `/usr/local/bin:/usr/bin:/bin` (`child.c:1573-1600, 1791-1800`); la lingua viene da `/etc/locale.conf`. Peso **PICCOLO**. Cura nota: no.
9. **`dnfdragora-updater` per ogni utente remoto** (scarica metadati all'accesso, un processo per utente) (nessun codice; `src/session.c:3240-3300` ha l'elenco dei programmi dell'autostart di sistema da non avviare). Peso **PICCOLO-MEDIO** (rete e CPU ad ogni accesso; con molti utenti). Cura nota: sì per l'analogo `lubuntu-update` (shim «not started in the remote session»); qui la forma è da decidere.
10. **`nm-applet`, `geoclue demo agent` partono** nella sessione remota. Peso **PICCOLO** (decisione 16 nov e «filtri autostart» di `session.c:3240-3300` vanno estesi se si vuole toglierli). Cura nota: sì (stessa tecnica, `Hidden=true`).
11. **Mappa nome-sessione → desktop** (`session.c:388-399`): su Fedora la sessione dichiarata da sddm per LXQt è `lxqt-wayland` o `lxqt` (`DesktopNames=LXQt`; `DESKTOP_SESSION=lxqt-wayland` [V]): `strstr(n,"lxqt")` la riconosce già. Peso **PICCOLO** (controllare il riconoscimento con la dichiarazione di sddm; manca `plasmalogin`/altri DM da vedere con gli altri agenti). Cura nota: sì.
12. **SELinux, confinamento del lato rete**: nessun equivalente automatico di `remotix_network.apparmor` (il servizio resta `unconfined_service_t`). Peso **GRANDE** se si vuole lo stesso livello di protezione, **PICCOLO** se si accetta «non confinato». Cura nota: no (AppArmor di Ubuntu/Debian non si traduce). Decisione del proprietario.
13. **openssl 4.0 e ngtcp2 su Fedora**: `openssl-devel` è 4.0.3, e ngtcp2 di Fedora è 1.22.1 (REMOTIX usa 1.25.0 statico, `quic-static.sh`): la compilazione statica va rifatta con la libreria TLS scelta (`openssl3-devel` 3.5.9 o 4.0). Peso **MEDIO** (comune ai gusti). Cura nota: sì, la costruzione statica esiste, da riprovare sul contenitore Fedora (non sul tablet, e niente podman: da vedere come, regola 21 nov).
14. **Aggiornamento di commenti/riferimenti di versione** nel codice (`session.c:3749-3760, 6180-6190`, `session.h:~190`: lxqt-session 2.1.1, wayland-session 0.1.1): oggi 2.4.0 e 0.4.1. Peso **PICCOLO**. Cura nota: sì (voce 8 dello studio 7).

## Decisioni che spettano al proprietario

1. **Codec video su Fedora**: accettare di far dipendere REMOTIX da RPM Fusion (`mesa-va-drivers-freeworld`/`mesa-vulkan-drivers-freeworld`) con avviso chiaro all'installazione, oppure Fedora «senza video» fino a nuovo ordine, oppure altra via (ripiego software tolto il 1 ott 2026, ripristinarlo?).
2. **Gancio PAM locale**: (a) riga in `/etc/pam.d/sddm` e simili dallo scriptlet (con avviso se modificato a mano), (b) profilo `authselect` personalizzato, (c) nessun gancio. E, sotto SELinux, nuovo tipo + modulo oppure etichetta esistente.
3. **Confinamento SELinux**: restare `unconfined_service_t` o scrivere un modulo che confini almeno il lato rete.
4. **`dnfdragora-updater`, `nm-applet`, geoclue agent** nella sessione remota LXQt: lasciare, nascondere (`Hidden=true` in `xdg-lxqt/autostart`).
5. **LXQt Wayland locale = miriway**: confermare che REMOTIX non lo usa e continua con `labwc -S lxqt-session` (nessun cambio di approccio).
6. **Dipendenza da `labwc` (0.20.2)**: `Requires` o `Recommends` nel RPM (su Fedora il Spin LXQt non lo porta).
7. Se il proprietario vuole un `Requires`/`Recommends` anche per `xdg-desktop-portal-wlr` (lo porta labwc comunque).

## Che cosa non si può sapere senza provare

- Il comportamento **di REMOTIX stesso** (pacchetto, servizio, `child.c`, cattura, tastiera dal browser) su Fedora: non è stato installato né costruito.
- Se **labwc 0.20.2** accetta le opzioni di `rc.xml` e le scorciatoie di REMOTIX (D-007), il `-m` merge, e come si comporta il puntatore assoluto/rotella/touch (virtual pointer v2) e il cursore.
- Se la **clipboard** (data-control v2 e ext) arriva al browser senza qlipper.
- La causa esatta dell'uscita immediata di `lxqt-session` locale con un altro `lxqt-session` sullo stesso bus (A2): ho visto la morte, non il motivo.
- Il comportamento del **gancio PAM sotto SELinux** reale (AVC) con sddm Wayland; i nomi dei domini nei DM degli altri gusti (`lightdm_t`, `plasmalogin_t`, `gdm_t`).
- `pam_selinux open` per i figli di un servizio `unconfined_service_t` (contesto dei processi dell'utente nella sessione remota) e le regole di `unconfined_service_t` verso D-Bus/logind in presenza di sessioni confinate.
- L'**idle > 15 min** con LXQt (nessuna azione di spegnimento schermo) e la finestra di crash «X Compositor» (non c'è nessun compositore X: non osservata, ma non provata a lungo).
- L'uscita con **lavoro non salvato** (regola della voce D del registro): non ho aperto applicazioni; ho provato solo `logout()` a desktop vuoto.
- Il tempo di chiusura/uscita ordinata e il suo comportamento con `lxqt-leave` (con `leave_confirmation=true` in `/etc/lxqt/session.conf`, come Debian/Ubuntu: `lxqt-leave --logout` chiede conferma, REMOTIX usa `org.lxqt.session logout`).
- Il comportamento del Spin **installato dall'installatore vero** (la VM è costruita dalla ISO: `liveinst-setup.desktop` e `vmware-user` ecc. possono essere artefatti) e con la tastiera vera (limite del banco).
- `mesa-*-freeworld` di RPM Fusion: se davvero rimettono H.264/HEVC (encode) sulla Radeon con Vulkan Video e VA-API.

## Prove consigliate

1. Su VM `lxqt` con Radeon: installare `mesa-va-drivers-freeworld`/`mesa-vulkan-drivers-freeworld` da RPM Fusion e rifare `vainfo` e `vulkaninfo` (H.264/HEVC encode) + `remotix --encoding-test h264`.
2. Costruire il pacchetto RPM (non sul tablet, non con podman) e installarlo nella VM; poi: servizio disabilitato dopo `dnf install`, avviarlo, accesso dal browser, sessione LXQt dentro labwc 0.20.2, input da mouse/tastiera/tocco, clipboard, audio, chiusura (Log Out) a sessione attaccata e staccata, i cicli distacco/riattacco, lancio di `check-lifecycle`/`check-prelocal` adattati.
3. Rifare la prova A2 **con REMOTIX vero** e il gancio PAM nelle due varianti SELinux (con e senza modulo) e leggere `ausearch -m avc,user_avc` + `journalctl`.
4. Controllare `pkcheck` e `power-implied` di REMOTIX con le regole installate, dalla sessione locale (seduta) e dal greeter, su polkit 127/systemd 262.
5. Accesso locale pulito dopo l'uscita remota (A1: riavvio servizio con desktop aperto → accesso locale).
6. SELinux in `permissive` solo per la diagnosi (mai nel prodotto): contare gli AVC del servizio e dei figli.
7. L'uscita con lavoro non salvato e con la finestra «Log Out» annullata; idle > 15 min.
8. Prova con un secondo utente e con tre utenti insieme (dnfdragora-updater e tray).

## Che cosa ho cambiato nella VM `lxqt`

- Pacchetti installati con `dnf install` (repo Fedora, senza `dnf upgrade`): `labwc 0.20.2` e le sue dipendenze `wlroots 0.20.2`, `libseat`, `libliftoff`, `libsfdo`, `xcb-util-errors`, `xdg-desktop-portal-wlr`, `grim`; `wlr-randr 0.5.0`; `wayland-utils 1.3.0`; `libva-utils`, `vulkan-tools`, `mesa-demos`, `pciutils`; `setools-console 4.7.1` (con dipendenze); chiave GPG Fedora 45 importata dal programma.
- Nessun repository abilitato: RPM Fusion solo **interrogato** con `--repofrompath` (temporaneo, cache di `dnf`), niente installato.
- File miei nella casa di `prova` (`~/t1 ... ~/t4`, `t*.sh`, `se*.sh`, `inst*.log`) e `/root/setools.log`; la prima volta che `prova` ha fatto l'accesso locale sono nate `~/.config/lxqt/*`, `~/.config/miriway-shell.*`, `~/.cache/*` e le cartelle `Desktop`, `Documents`, ecc.; una sessione di prova di LXQt in labwc headless ha scritto in `~/t2/home`, `~/t3/home`.
- Piccoli cambiamenti di stato: due tentativi di accesso falliti all'inizio (battuta sbagliata); sessioni locali di `prova` aperte e chiuse; un transient `rxtest.service` (systemd-run, fermato) per l'etichetta SELinux; una cartella `/run/rxtest` creata e tolta (la mia).
- Sul server, cartella propria `/media/REMOTIX-FEDORA/studio/lxqt/`: `greeter.png`, `l1.png ... l4.png`, `t1.sh`.
- La VM è stata accesa in modo virtuale, poi per ~6 minuti con la Radeon (spenta e di nuovo virtuale), e infine **spenta**; la Radeon è libera. Non ho ripristinato l'istantanea `pulito`.
