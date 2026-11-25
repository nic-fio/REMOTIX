# 3 - XFCE su Fedora 45 (Xfce Spin): studio per portare REMOTIX 1.0.1

Data: 21 nov 2026. Agente di studio 3. Solo studio: nessun codice del prodotto toccato, prodotto non costruito né installato.
Macchina: VM `xfce` (Fedora 45 Live "Xfce" 45-1.4 installata, kernel 7.2.11-300.fc45, SELinux enforcing, firewall di serie),
sempre in modo `virtuale`: la Radeon non è mai stata usata.

Convenzioni: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione.
Sigle: `U:` = `/home/nicfio/Documenti/REMOTIX/ubuntu26.04/`. Le cartelle di lavoro sul server sono in
`/media/REMOTIX-FEDORA/studio/xfce/` (solo le foto `s1..s7.png` della schermata di accesso).

Come ho osservato: (a) accesso locale vero dalla schermata di lightdm come `prova` e come `prova2`; (b) un'**emulazione** di
come REMOTIX avvia XFCE, fatta a mano come utente `prova2` in una sessione ssh: stesso ambiente di `session.c`
(`XDG_CURRENT_DESKTOP=XFCE`, `XDG_SESSION_TYPE=wayland`, `GDK_BACKEND=wayland`, `WLR_BACKENDS=headless`,
`WLR_RENDERER=pixman`, `XFCE4_SESSION_COMPOSITOR="labwc -m --session xfce4-session"`) e stessa riga di avvio
(`labwc -m --session sh -c "wlr-randr … --custom-mode 1344x768; exec xfce4-session"`). **Non** è l'ambiente costruito da zero di
`compose_environment()` (la sessione ssh ci ha lasciato qualche variabile): vale per capire cosa regge, non per misurare.

---------------------------------------------------------------------------------------------------

## 1. Riassunto (le dieci cose che contano)

1. **labwc, wlroots, wlr-randr NON sono installati di serie** sullo Spin Xfce, ma sono nei repository: `labwc 0.20.2`
   (wlroots 0.20.2), `wlr-randr 0.5.0`, `wlroots 0.20.2`. Xwayland 24.1.13 è già installato. Con `dnf install labwc wlr-randr`
   arrivano anche `xdg-desktop-portal-wlr` (Requires di labwc), `grim`, `slurp`, `labwc-menu-generator`, `libsfdo`, `libliftoff`,
   `xcb-util-errors` [V].
2. **labwc è passato da 0.9.3 (Ubuntu) a 0.20.2**: il numero è stato riallineato a quello di wlroots (NEWS: "sudden jump from
   0.9.7 to 0.20.0"). Le opzioni usate da REMOTIX (`-m`, `-S/--session`, `-C`, `-d`) ci sono ancora; il file `rc.xml` di REMOTIX
   (tasto «riporta dentro» con `ForEach`, `query`, `SetDecorations forceSSD`, `WarpCursor`, `AutoPlace`) viene letto senza
   avvisi (`read config file /tmp/rxcfg/labwc/rc.xml`, `-m`) [V]. L'azione del tasto non è stata fatta scattare [non provato].
3. **Il desktop XFCE nasce e regge dentro labwc 0.20.2 + Xwayland** con la ricetta di REMOTIX: pannello alto, dock in basso,
   `xfce4-session`, `xfwm4` non c'è (lo fa labwc), orologio, systray [V: foto `grim`, 1344x768]. Globali Wayland offerti da labwc
   0.20.2 e usati da REMOTIX: `zwlr_screencopy_manager_v1` v3, `zwlr_virtual_pointer_manager_v1` v2,
   `zwp_virtual_keyboard_manager_v1`, `zwlr_output_manager_v1` v4, `zwlr_data_control_manager_v1` v2, `ext_data_control_manager_v1`,
   `zwlr_layer_shell_v1` v4 [V]. (Con `WLR_RENDERER=pixman` non c'è `zwp_linux_dmabuf_v1`: con la scheda vera da verificare.)
4. **Lo sfondo nero (E1) su Fedora ha una causa DIVERSA e più grave**: `libxfce4windowing` è 4.20.7 (>= 4.20.4, quindi il
   difetto del registro non c'è), ma **`xfdesktop 4.20.2` di Fedora è compilato senza supporto Wayland**: in sessione Wayland
   scrive `CRITICAL: xfdesktop was not built with Wayland support` ed esce. Risultato: **nessun sfondo e nessuna icona del
   desktop** (nero pieno; il pannello c'è) [V: foto]. In locale (X11) xfdesktop gira. Nessun aggiornamento di libreria lo cura.
5. **Il desktop locale è X11, non Wayland**: l'unica sessione è `xsessions/xfce.desktop`; `wayland-sessions/` è vuota
   (`xfce4-session-wayland-session` esiste ma non è installato) [V]. Sessione logind locale: `Type=x11, Class=user, Seat=seat0,
   VTNr=7, Service=lightdm, Desktop=xfce` [V].
6. **Il problema A2 (lightdm non trattiene) si riproduce identico su Fedora**: con un desktop "remoto" vivo, l'accesso locale
   dello stesso utente dura 1 secondo e torna alla schermata di accesso [V]. E l'aggancio previsto (`pam_exec` dopo `pam_systemd`)
   **funziona su lightdm Fedora**, con l'ambiente giusto (§7) [V]. Il punto aperto è **come mettere la riga in PAM su Fedora**
   (authselect, §8.1).
7. **BLOCCO SELinux (nuovo, specifico di Fedora, grave)**: un servizio installato da RPM in `/usr/libexec` gira nel dominio
   `unconfined_service_t`. Se la sua pila PAM contiene `pam_selinux` (come `/etc/pam.d/sshd`, di cui il file `remotix` è copia),
   `pam_open_session` riesce, ma il successivo `execve` del desktop dell'utente è **negato**
   (`avc: denied { transition } … scontext=unconfined_service_t tcontext=unconfined_t`) [V]. Senza `pam_selinux` nella pila
   il desktop parte (ma i processi dell'utente restano `unconfined_service_t`). Va deciso (§9, decisione D1).
8. **Le regole polkit di REMOTIX reggono su Fedora/polkit 127 senza modifiche**: con `50-remotix-no-poweroff.rules` in
   `/usr/share/polkit-1/rules.d/` le 19 azioni diventano tutte "no" sia per l'utente seduto sia per il greeter di lightdm [V]. Su
   Fedora c'è però una regola della distribuzione che da sola concederebbe TUTTO al greeter (`lightdm.rules`): la nostra vince
   solo grazie al nome `50-…` (ordine alfabetico, §6) [V].
9. **Pannello predefinito dello Spin = quello di Debian**: ha il pulsante `actions` (`plugin-10`), il menu è `applicationsmenu`
   (non whisker menu; il pacchetto `xfce4-whiskermenu-plugin 2.10.1` è installato ma non usato). Quindi la protezione delle voci di
   spegnimento passa dal blocco di `items` dell'`actions`, come su Debian, non dal whisker come su Xubuntu [V].
10. **Tutto il resto del contorno è come altrove**, con tre differenze Fedora: `/etc/environment` è VUOTO (il PATH remoto cade sul
    ripiego fisso), il portachiavi di serie (`oo7`) non è attivabile (nessuno risponde a `org.freedesktop.secrets`), e un Log Out
    locale o remoto lascia vivi tre programmi (`abrt-applet`, `geoclue demo agent`, `localsearch-3`) [V].

---------------------------------------------------------------------------------------------------

## 2. Che cosa c'è (versioni vere) [V: `rpm -qa` nella VM]

| Pezzo | Fedora 45 Xfce Spin | Ubuntu 26.04 (studio 7) |
|---|---|---|
| xfce4-session | 4.20.4-2 (+ `xfce4-session-wayland-session`: NON installato) | 4.20.4 |
| xfce4-panel | 4.20.8-4 | 4.20.7 |
| xfdesktop | **4.20.2-2, senza Wayland** | 4.20.1 |
| xfwm4 | 4.20.0-5 (solo X11) | - |
| libxfce4windowing | **4.20.7-1** | 4.20.5 |
| xfce4-whiskermenu-plugin | 2.10.1-9 (installato, non nel pannello) | 2.10.1 |
| xfconf / xfce4-settings / power-manager / screensaver | 4.20.0 / 4.20.5 / 4.20.1 / 4.20.2 | - |
| polkit agent | `xfce-polkit 0.3-18` (autostart `OnlyShowIn=XFCE`) | - |
| lightdm / greeter | 1.33.1-7 / `lightdm-gtk 2.0.8` (greeter-session `lightdm-gtk-greeter`) | 1.32.0 |
| labwc / wlroots / wlr-randr | **0.20.2 / 0.20.2 / 0.5.0 (nei repo, non installati)** | 0.9.3 / 0.19 / 0.4.1 |
| Xwayland | 24.1.13-2 (installato) | 24.1.10 |
| systemd | 262-3 | 259.9 |
| polkit | 127-5 (+ `polkit-pkla-compat`) | - |
| PipeWire / WirePlumber | 1.6.9 / 0.5.18 | - |
| portali | xdg-desktop-portal 1.22.1, `-gtk` 1.15.3 (+ `xfce-portals.conf` di xfce4-session) | - |
| dbus | **dbus-broker 37** (bus utente) + dbus-daemon 1.16.2 (per `dbus-run-session`, `dbus-launch`) | dbus-daemon |
| authselect / SELinux | 1.8.0 (profilo `local`) / selinux-policy-targeted 45.23, enforcing | - |
| firewalld | 2.5.2, zona `public` | - |
| Mesa | 26.2.3 (`mesa-dri-drivers` contiene `radeonsi_drv_video.so`); NON esiste `mesa-va-drivers` nel repo | - |
| H.264 | `openh264` nel repo (2.6.0), `gstreamer1-plugin-openh264` e `ffmpeg-free 9.0.2` installati; niente `x264` | - |
| dconf | 51.0 (comando `dconf` installato) | - |

Sessioni offerte [V]: `/usr/share/xsessions/xfce.desktop` (`Exec=startxfce4`); `wayland-sessions/` vuota. Display manager:
`display-manager.service -> lightdm.service`; `/etc/lightdm/lightdm.conf` è vuoto di opzioni (nessun `user-session`: niente da
"dichiarare"); `50-session-wrapper.conf: session-wrapper=/etc/X11/xinit/Xsession`; `60-lightdm-gtk-greeter.conf`;
guest disabilitato. Marcatori di desktop: c'è solo `xfce4-session` (no `gnome-session`, `gnome-shell`, `lxqt-session`,
`startplasma-wayland`) [V: `which`]: il riconoscimento `recognize_desktop()` (`U:src/session.c:534-620`) darebbe XFCE senza
ambiguità. `desktop_of_session_name("xfce")` → XFCE (`U:src/session.c:388-397`).

---------------------------------------------------------------------------------------------------

## 3. Accesso locale vero, osservato (termine di paragone)

### 3.1 Processi e sessione logind [V]
Dopo l'accesso di `prova` da lightdm: sessione `11`, `Type=x11`, `Class=user`, `Seat=seat0`, `VTNr=7`, `Display=:0`,
`Service=lightdm`, `Desktop=xfce`; più `manager` (`systemd --user`) e il greeter `c1` (utente `lightdm`).
Albero in `session-11.scope`: `xfce4-session` (figlio di lightdm, via `Xsession` → `ssh-agent /bin/sh -c exec -l /bin/bash -c "startxfce4"`),
con figli `xfwm4`, `xfsettingsd`, `xfce4-panel` (+ `wrapper-2.0` per `systray` e `actions`), `Thunar --daemon`, `xfdesktop`,
`abrt-applet`, `blueman-applet`, `geoclue-2.0/demos/agent`, `localsearch-3`, `nm-applet`, `dnfdragora-updater`, `xfce-polkit`,
`xfce4-power-manager`, `xfce4-screensaver`; in `/usr/lib/systemd/user`-unità del manager: `xfconfd`, `xfce4-notifyd`, gvfs*, `tumblerd`,
`imsettings-daemon`, pipewire/wireplumber/pipewire-pulse, `obexd`. Fuori dallo scope di sessione: `oo7-daemon-login` (aiuto PAM) e
`gpg-agent`.

### 3.2 Ambiente della sessione locale (`/proc/<xfce4-session>/environ`) [V]
`DESKTOP_SESSION=xfce`, `GDMSESSION=xfce`, `XDG_SESSION_DESKTOP=xfce`, `XDG_CURRENT_DESKTOP=XFCE`, `XDG_MENU_PREFIX=xfce-`,
`XDG_SESSION_TYPE=x11`, `XDG_SESSION_CLASS=user`, `XDG_SESSION_ID`, `XDG_SEAT=seat0`, `XDG_SEAT_PATH`, `XDG_SESSION_PATH`, `XDG_VTNR=7`,
`XDG_GREETER_DATA_DIR`, `DISPLAY=:0`, `XAUTHORITY=/run/lightdm/<utente>/xauthority`, `XDG_CONFIG_DIRS=/etc/xdg` (**nessuna cartella
`xdg-<sessione>`**), `XDG_DATA_DIRS=~/.local/share/flatpak/exports/share:/var/lib/flatpak/exports/share:/usr/local/share:/usr/share`,
`PATH=~/.local/bin:~/bin:/usr/local/bin:/usr/bin`, `LANG`, `EDITOR=/usr/bin/nano`, `SSH_AUTH_SOCK`/`SSH_AGENT_PID` (`ssh-agent` messo da `Xsession`),
`IMSETTINGS_*`, `HISTSIZE`, `MAIL`, `DEBUGINFOD_*`, `SSH_ASKPASS`. `SESSION_MANAGER` lo ha `xfce4-session` per i figli.
Le variabili del manager utente (`systemctl --user show-environment`) coincidono quasi del tutto (anche `DISPLAY`, `XAUTHORITY`,
`XDG_*`): le mette `xfce4/xinitrc` con `dbus-update-activation-environment --systemd`.

### 3.3 File di avvio letti da un accesso locale [V]
- lightdm → `session-wrapper=/etc/X11/xinit/Xsession` (**non** `/etc/X11/Xsession.d`: su Fedora `/etc/X11/Xsession.d/` esiste ma contiene solo `90xbrlapi`).
  `Xsession` (se `GDMSESSION` non c'è) ridirige l'uscita su `~/.xsession-errors`, fa `. /etc/X11/xinit/xinitrc-common`, poi per il
  nome `startxfce4` esegue `exec $CK_XINIT_SESSION $SSH_AGENT /bin/sh -c "exec -l $SHELL -c startxfce4"`: **shell di login**, quindi
  `/etc/profile`, `/etc/profile.d/*` (lang, flatpak, nano-default-editor, debuginfod, gnupg2, vte…), `~/.bash_profile`.
- `xinitrc-common`: `lang.sh`, `~/.profile`, `xrdb`, `Xmodmap`, `Xkbmap`, poi tutti gli `xinitrc.d/*`:
  `00-start-message-bus.sh` (dbus-launch solo se manca il bus), `10-qt6-check-opengl2.sh`, `50-systemd-user.sh`
  (`systemctl --user import-environment DISPLAY XAUTHORITY`), `50-xinput.sh`, `98vboxadd-xclient.sh`, `localuser.sh` (`xhost +si:localuser:<utente>`).
- `startxfce4` → `/etc/xdg/xfce4/xinitrc`: `xdg-user-dirs-update`, Xft.xrdb, Xcursor, `dbus-update-activation-environment`, poi `exec xfce4-session`
  (con attesa che la VT sia attiva: workaround lightdm #63).
- PAM `lightdm` (`/usr/lib/pam.d/lightdm`, vedi §8): `pam_selinux`, `pam_loginuid`, `pam_namespace`, `system-auth` (con `pam_systemd`),
  `pam_gnome_keyring` / `pam_kwallet5` / `pam_kwallet` / `pam_oo7` (tutti con `-`: ignorati se assenti), `pam_lastlog2`, `postlogin`.
- Portachiavi: `pam_oo7.so auto_start` ha "mandato il segreto" al demone `oo7` (riga di lightdm nel journal) **ma** `oo7-daemon` non ha un file di
  attivazione D-Bus (`/usr/share/dbus-1/services/` non ha `org.freedesktop.secrets*`): `secret-tool store` risponde «The name is not activatable»
  e `busctl --user list` non lo elenca [V]. Quindi sullo Spin Xfce **non c'è un servizio di portachiavi attivo**, né in locale né in remoto
  (gnome-keyring non è installato; `gcr3`, `libsecret`, `oo7-portal` sì). Nessuna differenza locale/remoto da curare [S: i browser
  ripiegano su archivio non cifrato].

### 3.4 Uscita locale e processi rimasti [V]
`xfce4-session-logout --logout` (locale) e `Logout(false,false)` (come REMOTIX, `U:src/session.c:4627`): la sessione `11` passa a
`State=closing`, `Active=no`, lo scope diventa "active (abandoned)" e **restano vivi tre processi** figli di PID 1 dentro lo scope:
`abrt-applet --gapplication-service`, `/usr/libexec/geoclue-2.0/demos/agent`, `/usr/libexec/localsearch-3`. Lo stesso identico trio
resta dopo l'uscita della sessione "remota" emulata. `blueman-applet`, `nm-applet`, `dnfdragora-updater` escono da soli.
Per REMOTIX: `survivor()`/`session_clear_out_scope()` (`U:src/session.c:4359 e segg.`) li deve chiudere (SIGTERM poi SIGKILL): su Fedora il caso è certo, non raro.
`TimeoutStopFailureMode=abort` (Fedora, `service.d/10-timeout-abort.conf`) vale per le unità di servizio, non per gli scope: nessuna osservazione di core dump.

---------------------------------------------------------------------------------------------------

## 4. Come REMOTIX avvia XFCE oggi, e che cosa su Fedora 45 non regge (o regge)

Riferimento: `U:src/session.c` (8829 righe), `U:src/session.h:180-195`, `U:debian/control`, `U:studio/7`, `9`, `13`, `14`.

| Punto | Codice | Fedora 45 |
|---|---|---|
| Riga di avvio `labwc -m --session xfce4-session` (con `wlr-randr --output $u --custom-mode WxH` prima di `exec xfce4-session`) | `session.h:180-182`, `session.c:4243-4247, 4353-4380` | opzioni presenti in labwc 0.20.2 [V `labwc --help`]. `wlr-randr 0.5.0`: elenco senza argomenti, prima parola della prima riga = `HEADLESS-1`, `--custom-mode` accettato: l'emulazione ha dato `OUT=HEADLESS-1` e uscita 1344x768 [V] |
| Compositore headless | `WLR_BACKENDS=headless`, `WLR_LIBINPUT_NO_DEVICES=1`, `WLR_RENDER_DRM_DEVICE` o `WLR_RENDERER=pixman` | provato solo con `pixman` (VM): funziona. Con scheda vera [non provato]. NEWS 0.20.2: «force the initial modeset commit … QEMU/virtio-gpu» |
| `XFCE4_SESSION_COMPOSITOR` come "cintura" del logout | `session.c:3589-3597` | il sorgente di `xfce4-session 4.20.4` di Fedora (`main.c:263`) ha la stessa logica: se non trova `labwc` **e** `--session` esegue `loginctl terminate-session ''` [V: `main.c`]. Nessuna patch Fedora al punto (la sola patch è `startxfce4` con `vt${tty_num}`) |
| Logout `org.xfce.Session.Manager.Logout(false,false)` | `session.c:4627-4650` | stesso nome sul bus, stesso metodo [V: `busctl introspect`] |
| XFCE rifiuta il Logout durante l'avvio | registro D | **confermato**: il nome sul bus appare a +119 ms; `Logout` risponde «Session manager must be in idle state when requesting a shutdown» per 8 tentativi a 1 s di distanza e riesce al nono (+8,2 s, VM 4 vCPU, `pixman`); dopo la riuscita `labwc` e `xfce4-session` sono spariti (0 processi) [V]. La cura esistente (forzare con SIGTERM a labwc dopo il tempo concesso) resta necessaria |
| Cartelle di sessione come un accesso locale (D-153) | `session.c:2930-3140` (`local_session()`) | su Fedora **non esistono** `/etc/xdg/xdg-xfce` né `/usr/share/xfce`; non c'è `60x11-common_xdg_path`; non c'è dichiarazione `user-session`. `local_session()` darebbe "nessuna sessione" e il log "its local login adds no session folders": **corretto**, il locale ha `XDG_CONFIG_DIRS=/etc/xdg`. Il pannello dello Spin sta in `/etc/xdg/xfce4/panel/default.xml` (pacchetto `xfce4-panel`) e i valori di sistema in `/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/` (quattro file: `xfce4-keyboard-shortcuts`, `xfce4-power-manager`, `xfce4-session`, `xsettings`): vengono trovati lungo `XDG_CONFIG_DIRS` normalmente [V] |
| `DESKTOP_SESSION` / `XDG_SESSION_DESKTOP` | `add_session_names(.., "xfce", TRUE)` | locale: entrambi `xfce`. Con nome non trovato il codice usa il ripiego `xfce`: coincide [V] |
| Variabili di lightdm/Xsession che la sessione remota non ha | - | `GDMSESSION=xfce`, `XDG_SEAT/_PATH`, `XDG_SESSION_PATH`, `XDG_VTNR`, `XDG_GREETER_DATA_DIR`, `XAUTHORITY`, `DISPLAY` (reale :0), `SSH_AUTH_SOCK` (ssh-agent di `Xsession`), `IMSETTINGS_*`, `EDITOR` (profile.d), `PATH` con `~/.local/bin` e `~/bin`, `HISTSIZE`, `MAIL`. Non c'è `56xubuntu-session`-equivalente. Quelle di seat/VT sono volutamente assenti (sessione senza seat). Da decidere: `PATH` (§9 D3) |
| PATH remoto | `child.c:1573-1807` (da `pam_env`/`/etc/environment`, ripiego `/usr/local/bin:/usr/bin:/bin`) | **`/etc/environment` è un file vuoto (0 byte)** [V]: `pam_env` non dà `PATH`; il ripiego fisso vale. Locale: `~/.local/bin:~/bin:/usr/local/bin:/usr/bin` (da `/etc/skel/.bash_profile`). Differenza piccola (script personali in `~/bin`) |
| `LANG` | `session.c:3699` `local_utf8()` | `/etc/locale.conf` ha `LANG=en_US.UTF-8`; il manager utente lo ha. Nessun `pam_env envfile=/etc/default/locale` su Fedora (il file `remotix` di Debian lo cita: **non esiste su Fedora**) |
| `SHELL` | `session.c:3689-3697` (XFCE: shell di passwd) | ok |
| Pulsante `actions`, blocco di `items` | `session.c:6100-6330`, `7739` (`XFCE_LOCKS`) | stesse chiavi su Fedora 4.20.8: il plugin `libactions.so` c'è (`plugin-10`), i canali di sistema `xfce4-session`, `xfce4-power-manager` esistono come file di sistema, con valori diversi dall'Ubuntu: `xfce4-session.xml` ha `LockCommand=""`, `power-button-action=3` (chiedi), `logind-handle-lid-switch=false` [V]. Il blocco via drop-in di `xfconfd.service` funziona se l'unità esiste: **c'è** (`/usr/lib/systemd/user/xfconfd.service`, `Type=dbus`), come su Debian [V] |
| Voci di avvio automatico da non far partire | `SESSION_NOT_IN_REMOTE_AUTOSTART` = solo `blueman.desktop` (`session.c:3240-3270`) | su Fedora `blueman.desktop` c'è (pacchetto `blueman`, senza `OnlyShowIn`): ok. Ma ci sono altre voci (§5) |
| Fine sessione, "cintura" xfconf | `session.c:5810-6100` | non provata (nessun REMOTIX); le chiavi e il canale sono quelli Debian |

### 4.1 Dipendenze di avvio su Fedora
- **labwc**: pacchetto `labwc` 0.20.2, **non installato di serie**: va nel `Requires`/`Recommends` del nostro RPM. `labwc` richiede a sua volta
  `xdg-desktop-portal-wlr` e `mesa-dri-drivers` [V: `rpm -qp --requires`]; in sessione, con `XDG_CURRENT_DESKTOP=XFCE` e `xfce-portals.conf`
  il portale usato resta `gtk` [S] (il portale wlr è attivabile ma non scelto).
- **wlr-randr**: pacchetto `wlr-randr`, non installato; **Xwayland**: `xorg-x11-server-Xwayland`, già installato; senza di esso labwc 0.20 parte lo stesso
  ("gracefully handle missing XWayland", NEWS 0.20.0) ma `xfce4-screensaver`, `vmware-user`, `blueman`… che usano X11 non andrebbero.
- Nell'emulazione Xwayland è partito da solo (`DISPLAY=:1`) con `Xwayland glamor: GBM Wayland interfaces not available … falling back to sw` e
  `MESA-EGL: failed to open /dev/dri/card1: Permission denied` (sotto `pixman`, VM): rumore, non errore.
- `xfce4-session-wayland-session` (sessione `xfce-wayland` ufficiale: `startxfce4 --wayland`, usa `~/.config/xfce4/labwc/` con `--config-dir`): **non serve** a REMOTIX,
  che usa la propria riga di avvio. Non installarlo né dipenderne.

### 4.2 Che cosa non regge
- (grave) **xfdesktop senza Wayland**: sfondo/icone assenti (§1.4). Dato che la sessione "regge" ma ha uno schermo nero, va deciso se dichiararlo limite noto o dare un rimedio
  (§9 D2). Non esiste rimedio di versione.
- (grave) **SELinux e `pam_selinux`** (§8.3).
- (medio) **labwc 0.20.x**: i punti sensibili alla versione sono quelli già elencati nello studio 7 (§7, ultima riga): forma di `rc.xml`/`<keybind>` (letto
  senza errori), nomi dei cursori in `shape.c:131-137`, `wlr-randr` 0.5.0 (testato). Nuove cose di 0.20: `labwc-session.target` (unità systemd utente installata dal pacchetto
  quando c'è systemd) [S: da guardare che non interferisca con la nostra gestione unità]; `<core><errorCommand>` e `labnag` per gli errori di configurazione; le note di wlroots 0.20
  (`wl_output` senza make/model; «auto-hide lxqt-panel con wlroots < 0.20.2» — Fedora ha 0.20.2: non vale).
- (piccolo) la sessione remota ha `Workspace 1` nel pannello al posto del pager (labwc non associa finestre e aree di lavoro: `libxfce4windowing-Message: Window<->Workspace association is not available on your compositor`) — come su Ubuntu.

---------------------------------------------------------------------------------------------------

## 5. Programmi avviati di serie nella sessione (autostart) [V: `/etc/xdg/autostart`, `rpm -qf`]

Visti nell'albero locale e (tranne i marcati) anche nell'emulazione "remota". Candidati a stare **fuori** da una sessione su macchina condivisa, oltre al solo `blueman` già coperto:

| Voce (pacchetto) | Che cosa fa | Commento |
|---|---|---|
| `blueman.desktop` (blueman) | applet Bluetooth; nell'emulazione: `Failed to start plugin GameControllerWakelock: Only X11 platform is supported`, nessun crash visto | già coperto (`SESSION_NOT_IN_REMOTE_AUTOSTART`) |
| `org.freedesktop.problems.applet.desktop` (abrt-gui) | `abrt-applet`: segnalazione crash (ABRT); **resta vivo dopo l'uscita** | segnalazioni "di macchina", non dell'utente remoto; in locale è di serie. Candidato |
| `org.mageia.dnfdragora-updater.desktop` (dnfdragora-updater) | avvisi aggiornamenti dnf, in sessione locale | su server condiviso inutile/fuorviante; in locale di serie. Candidato |
| `geoclue-demo-agent.desktop` (geoclue2, `NotShowIn=GNOME`) | agente di posizione; **resta vivo dopo l'uscita** | candidato |
| `localsearch-3.desktop` (localsearch, `OnlyShowIn=GNOME;KDE;XFCE;…`) | indicizzatore file (ex tracker-miner); **resta vivo dopo l'uscita**, spawna `localsearch-extractor-3` | pesante in più utenti; candidato |
| `nm-applet.desktop` (network-manager-applet) | icona di rete | in remoto: rete della macchina; probabilmente innocuo |
| `xfce4-power-manager.desktop`, `xfce4-screensaver.desktop` | gestione energia / salvaschermo (su Wayland: «Unsupported windowing environment») | già gestiti da chiavi bloccate (§4) |
| `liveinst-setup.desktop` (anaconda-live) | crea il lanciatore dell'installatore **solo se** `/dev/mapper/live-base` esiste (script letto) | innocuo su disco installato; sulla live potrebbe agire |
| `spice-vdagent`, `vboxclient`, `vmware-user` | strumenti per macchine virtuali, presenti perché l'immagine è quella della live | sul tablet/server vero non ci saranno o saranno inerti; **sono loro a far partire Xwayland nell'emulazione** [S] |
| `xfsettingsd`, `xfce4-notifyd`, `xfce-polkit`, `imsettings-start`, `xdg-user-dirs*`, `user-dirs-update-gtk` | necessari (polkit agent, notifiche, impostazioni) | `xfce-polkit` parte in remoto e fa da agente polkit della sessione remota [V: processo vivo] |
| `xfce4-clipman-plugin-autostart`, `org.xfce.xfdashboard-autostart` | `Hidden=true` | non partono |

Il meccanismo di copertura (`Hidden=true` in una cartella `autostart` in testa a `XDG_CONFIG_DIRS`) vale uguale su Fedora (garcon/xfce4-session leggono `XDG_CONFIG_DIRS` come altrove [S: stessi sorgenti 4.20.4]; la prova che un `Hidden=true` nasconde anche la voce utente è dei studi Ubuntu).
Decisione di prodotto da chiedere (§9 D4): quali di queste voci togliere.

---------------------------------------------------------------------------------------------------

## 6. Voci di spegnimento / polkit / logind [V: pkcheck dalla VM]

- Lo Spin ha `systemd 262`: **37** azioni `org.freedesktop.login1.*`. Le 19 azioni del file `U:src/remotix-no-poweroff.rules` esistono tutte (nessuna mancante),
  e **nessuna altra azione di nessun pacchetto ne implica una vietata** (controllo equivalente a `power-implied` fatto con uno script sui `.policy`).
  Le `set-reboot-*` implicano `reboot`, `halt`/`power-off` implicano `set-wall-message` (non vietata, `auth_admin_keep`: innocua).
- Altre azioni "di spegnimento" fuori elenco: `org.xfce.session.xfsm-shutdown-helper` (`allow_active=yes`, `allow_any=auth_admin`): usata da
  `xfce4-session` solo come ripiego quando logind non risponde (`xfsm-shutdown-fallback.c`; ordine: logind/systemd → ConsoleKit → ripiego); e
  `org.freedesktop.udisks2.power-off-drive*` (spegne un disco esterno, non la macchina).
- **Base locale (senza regola nostra)**, utente `prova2` seduto in sessione locale attiva: `pkcheck` dà "sì" (rc 0) a `power-off`, `reboot`, `halt`(no: `auth_admin`), `suspend`,
  `hibernate`, `set-reboot-*`, le `*-multiple-sessions`; e `xfce4-session` risponde `CanShutdown=true, CanRestart=true, CanSuspend=true, CanHibernate=false`
  (`org.xfce.Session.Manager`).
- **Con `50-remotix-no-poweroff.rules` copiata in `/usr/share/polkit-1/rules.d/`** (messa e tolta, vedi §15): le 19 azioni tutte "no" (rc 1) per l'utente seduto; `chvt`
  resta "sì" (taratura); `set-wall-message` resta `auth_admin_keep`. La cartella `/usr/share/polkit-1/rules.d` è letta da polkit 127 di Fedora [V].
- **Greeter di lightdm**: pacchetto `lightdm` porta `/usr/share/polkit-1/rules.d/lightdm.rules`: *per l'utente `lightdm` risponde YES a ogni azione `login1.*`,
  `consolekit.system.*` e `upower.*`*. Misurato da un processo del greeter (`lightdm-gtk-greeter`, dominio `xdm_t`): **senza la nostra regola** `power-off`, `reboot`,
  `halt`, `suspend`, `hibernate`, `set-reboot-parameter` = sì (rc 0); **con** la nostra regola tutti = no (rc 1) [V]. Funziona perché polkit ordina i file per nome e
  `50-remotix-…` viene prima di `lightdm.rules` (cifra < lettera). ⚠ Se mai il file si chiamasse con un prefisso alfabetico o `9x-`, la regola di lightdm vincerebbe.
  Il greeter ha l'icona di spegnimento in alto a destra (foto `s1.png`): con la regola il menu non può spegnere [mai premuto davvero: non provato fino al clic].
- Spegnimento hardware: il drop-in `remotix-power-keys.conf` (`/etc/systemd/logind.conf.d/`) vale com'è (non provato su Fedora, nessun `HandlePowerKey` fissato nel file di sistema [V: `power-button-action=3` è di xfce4-power-manager]).
- `polkit-pkla-compat` è installato: le regole `.pkla` esistono ancora come meccanismo vecchio; non servono.
- `/etc/polkit-1/rules.d` non è leggibile all'utente `prova` (permessi 700 root:polkitd): le regole dell'amministratore non le ho potute elencare [limite].

---------------------------------------------------------------------------------------------------

## 7. lightdm su Fedora e l'accesso locale con il remoto vivo (voce A2)

### 7.1 Che cosa fa lightdm [V]
Greeter `lightdm-gtk-greeter` (utente `lightdm`, uid 979, sessione logind `c<N>` classe `greeter`, dominio `xdm_t`); il demone usa il servizio PAM
`lightdm` (`/usr/lib/pam.d/lightdm`, installato dal pacchetto in `/usr/lib/pam.d`, non in `/etc/pam.d`) e `lightdm-greeter`, `lightdm-autologin`. Per ogni
tentativo lightdm riavvia il greeter (sessioni `c1`, `c2`… in aumento). Niente "attesa dell'altra sessione": nessuna logica di trattenere.

### 7.2 Prova: desktop "remoto" vivo, poi accesso locale dello stesso utente [V]
Emulazione viva per `prova2` (labwc + xfce4-session, `org.xfce.SessionManager` sul bus utente). Accesso locale di `prova2` dalla schermata: 
journal lightdm `17:14:56 … session opened for user prova2`, `17:14:57 … session closed for user prova2`: **1 secondo**, poi nuovo greeter. `~/.xsession-errors`:
`xfce4-session-Message: SSH authentication agent is already running` e basta (la sessione locale muore: il nome `org.xfce.SessionManager` è già preso dalla remota).
**Esito: la schermata di accesso di lightdm non trattiene, identico a Ubuntu/Debian (A2).** La stessa prova fu fatta due volte (secondo e terzo tentativo con l'aggancio, §7.3).

### 7.3 Prova: l'aggancio `pam_exec` che chiude il desktop remoto prima [V]
Ho copiato `/usr/lib/pam.d/lightdm` in `/etc/pam.d/lightdm` con una riga in più subito dopo `session include system-auth` (cioè **dopo** `pam_systemd`):
`session optional pam_exec.so quiet /usr/local/sbin/hook-test.sh`. Lo script registrava l'ambiente, scriveva in una cartella root-only in `/run`, mandava
SIGTERM a `labwc` di quell'utente e aspettava che `xfce4-session` sparisse. Esito (2 prove riuscite su 3, vedi sotto): accesso locale riuscito (sessione `seat0` classe `user`
`Type=x11`, `xfce4-session`, `xfwm4`, `xfce4-panel`, `xfdesktop` vivi); il gancio è rimasto in attesa ~1 s (`waited i=2`).
Ambiente visto dal gancio al momento della chiamata: `PAM_SERVICE=lightdm`, `PAM_TYPE=open_session`, `PAM_USER`, `PAM_TTY=:0`, **`XDG_SEAT=seat0`**,
**`XDG_SESSION_CLASS=user`**, **`XDG_SESSION_TYPE=x11`**, `XDG_SESSION_ID=<n>` (già assegnato: `pam_systemd` aveva già girato), `XDG_VTNR=7`, `DISPLAY=:0`,
`DESKTOP_SESSION=xfce`, `XDG_CURRENT_DESKTOP=XFCE`, `XDG_RUNTIME_DIR`. È ciò che `U:src/local_login.c:19-23` si aspetta [V]. Contesto SELinux del gancio:
`unconfined_u:unconfined_r:unconfined_t` (non `xdm_t`: `pam_selinux open` aveva già messo il contesto di esecuzione dell'utente).
- **Anomalia non spiegata**: il PRIMO tentativo con l'aggancio (riga in `/etc/pam.d/lightdm` appena creata) **non ha lasciato nessuna traccia** (`/tmp/hook.log`
  assente, nessun AVC) e il login è tornato al greeter in 1 s; il secondo e il terzo hanno funzionato. Nel frattempo avevo eseguito `semodule -DB` (tolto `dontaudit`).
  Da riprovare su una macchina pulita prima di fidarsi: potrebbe essere una corsa o un file di prova non ancora pronto [S].
- **`pam_exec` + SELinux**: dopo `pam_selinux open`, ogni `execve` fatto da quel processo passa al contesto dell'utente (`unconfined_t`). Se il dominio chiamante non
  può transitare lì, il gancio **non parte e non lo dice** (riga `optional`). Visto: chiamante `xdm_t` (lightdm) → transizione consentita (solo AVC `siginh` innocui); chiamante
  `initrc_t` o `unconfined_service_t` → `denied { transition }`, `execve … failed: Permission denied`. Per l'aggancio dentro `lightdm`/`sddm`/`gdm` vale il primo caso.

### 7.4 Che cosa vuol dire per il codice
- La logica A2 (`local_login.c` + `rootside.c`) serve identica; non cambia niente nel programma se la pila di lightdm porta la riga dopo `pam_systemd`.
- `rootside.c` deve poter leggere/scrivere `/run/remotix/prelocal/<uid>` da un processo il cui contesto, in accesso locale, è `unconfined_t` (sotto SELinux standard
  `unconfined_t` può farlo se la directory ha un'etichetta comune: la mia prova ha scritto un file in `/run/testhook` (`var_run_t`) senza AVC). Un utente confinato (`staff_u`, `user_u`) non è
  stato provato [non provato].

---------------------------------------------------------------------------------------------------

## 8. Sistema Fedora: PAM, SELinux, firewall

### 8.1 PAM e authselect [V]
- Profilo attivo `local` (non `sssd`), funzioni `with-silent-lastlog`, `with-mdns4`. **`with-faillock` NON è attivo**: `pam_faillock.so` esiste (`/usr/lib64/security/`) ma
  non è nella pila di `system-auth`/`password-auth` (a differenza di molte altre installazioni Fedora): REMOTIX "ha il suo conteggio" (ban dell'indirizzo, SPECS §4.2), quindi niente di rotto.
- I file `/etc/pam.d/{system-auth,password-auth,postlogin,fingerprint-auth,smartcard-auth}` sono **link a `/etc/authselect/…`**, intestati «Do not modify this file manually … Any user changes will be overwritten».
  `/etc/authselect/custom/` è vuota.
- `/etc/pam.d/sshd` (modello del nostro `remotix.pam`): `auth substack password-auth`, `auth include postlogin`, `account pam_sepermit/pam_nologin`, `account/password include password-auth`,
  `session pam_selinux close; pam_loginuid; pam_selinux open env_params; pam_namespace; pam_keyinit force revoke; pam_motd; include password-auth; include postlogin`.
  `pam_systemd` sta in `password-auth`/`system-auth` come `-session optional pam_systemd.so` (dopo `pam_limits`, prima di `pam_unix`). `pam_oo7`, `pam_gnome_keyring` ecc. sono nelle pile
  di lightdm/gdm, **non** in `password-auth`: la sessione REMOTIX non sblocca nessun portachiavi (innocuo, §3.3).
- **Il nostro file `src/remotix.pam` (Debian) non vale su Fedora**: usa `@include common-auth` (non esiste), `pam_listfile`, `pam_motd motd=/run/motd.dynamic`, `pam_env envfile=/etc/default/locale`
  (non esiste). Va riscritto sul modello di `/etc/pam.d/sshd` di Fedora (`substack password-auth`, `include postlogin`); si installa in `/usr/lib/pam.d/remotix` o `/etc/pam.d/remotix`. `U:src/main.c`
  cerca già il file in `/etc/pam.d` **e** `/usr/lib/pam.d` (`remotix.pam:36-37`).
- **Aggancio A2 su Fedora**: non esiste `pam-auth-update`. La riga `pam_exec` deve stare nella pila di sessione di ogni accesso locale dopo `pam_systemd`:
  - non si può modificare `system-auth`/`postlogin` (sovrascritti da authselect);
  - lightdm usa `/usr/lib/pam.d/lightdm` (vendor, del pacchetto lightdm: non si modifica; un file in `/etc/pam.d/lightdm` lo oscura intero, e la copia va tenuta allineata a ogni aggiornamento);
  - i modi di authselect: `authselect create-profile remotix --base-on local` (profilo personalizzato con la riga) e `authselect select custom/remotix` (cambia il profilo del sistema: invasivo, e
    se l'amministratore ha già un profilo suo non lo si sostituisce), oppure funzioni di authselect esistenti (`with-pamaccess`, `with-pwhistory`…): nessuna fa `pam_exec`.
  Va deciso (§9 D5). Nota: ogni DM ha il suo file (`lightdm`, `sddm`, `gdm-password`, `plasmalogin`…): un file per DM, oppure `postlogin` via profilo authselect (tutti gli accessi, compreso ssh: il gancio esce subito senza `XDG_SEAT`).

### 8.2 pam_faillock, logind, polkit gruppo wheel
`wheel` è il gruppo amministrativo (`polkit.addAdminRule` → `unix-group:wheel` in `50-default.rules`): `prova` (wheel) è amministratore per polkit. Non c'è un gruppo `sudo`. logind di serie: sessione utente `Class=user`; nessun
`HandlePowerKey` in `logind.conf` (le azioni dei tasti sono quelle di xfce4-power-manager/logind predefinite).

### 8.3 SELinux (enforcing) [V]
- **Dominio di un servizio RPM**: un'unità in `/usr/lib/systemd/system` con `ExecStart=/usr/libexec/<x>/<prog>` (etichetta del file `bin_t`, di serie per `/usr/libexec`)
  gira in `system_u:system_r:unconfined_service_t:s0`. Dentro: bind tcp+udp 7447 riuscito, lettura di `/etc/shadow` e della casa di un utente riuscita, lettura di
  `/proc/<pid utente>/environ` riuscita, connessione al bus di sistema e al socket del bus utente riuscita; **nessun AVC**. La porta 7447 non appartiene a nessun tipo `semanage port`: nessuna negazione.
- **Il problema**: stessa unità, pila PAM `rxtest` = copia di `/etc/pam.d/sshd` (con `pam_selinux close/open env_params`), programma in Python che fa `pam_start/pam_open_session`
  (come `child.c`), poi `fork`, `setgid/setuid` e `execve`: `pam_open_session` → 0; `attr/exec` del processo = `unconfined_u:unconfined_r:unconfined_t:s0`; **il `execve` del figlio fallisce**:
  `avc: denied { transition } for comm="probe3" path="/usr/bin/id" scontext=unconfined_service_t tcontext=unconfined_t tclass=process`. Il `pam_selinux` con il contesto di partenza
  `unconfined_service_t` sceglie `unconfined_u:unconfined_r:unconfined_t` (`default_contexts` non ha una riga per `unconfined_service_t`; ha righe per `xdm_t`, `sshd_t`, `sshd_session_t`,
  `remote_login_t`, `local_login_t`, `crond_t`) ma il servizio non ha il permesso di transitarci. Con la pila **senza** `pam_selinux` (`rxtest2`): `pam_open_session` → 0, `attr/exec` vuoto, `execve` riuscito, e `id -Z` dà
  `system_u:system_r:unconfined_service_t:s0` (i processi dell'utente restano in quel dominio).
- Possibili cure (da scegliere, §9 D1): (a) pila PAM di REMOTIX **senza** `pam_selinux` e processi utente in `unconfined_service_t` (funziona, rompe la separazione di dominio utente [S: dbus-broker e polkit non hanno
  mostrato AVC nelle prove, ma non ho avviato un desktop intero in quel dominio con scheda e SELinux]); (b) modulo di policy SELinux nell'RPM (`selinux-policy-devel` è nei repo, 45.24): un dominio
  `remotix_t` con la transizione verso `unconfined_t`/`user_t`; (c) `semanage`/etichetta del binario con un tipo di un dominio che ha già la riga in `default_contexts` (hack, non consigliato).
- Che cosa prende il posto del profilo AppArmor (`remotix_network.apparmor`: nega socket astratti, ecc.): su Fedora il servizio è `unconfined_service_t`, cioè **senza alcun muro** da MAC; per avere un muro equivalente
  serve una policy SELinux scritta (lavoro non piccolo). `landlock` (il "secondo muro" del codice) è del kernel [S: disponibile].
- AVC visti solo di tipo `siginh`, `noatsecure`, `rlimitinh` (sshd e xdm con `dontaudit` spento): rumore normale, non negazioni utili.

### 8.4 Firewall
`firewalld 2.5.2`, **zona `public` (default, attiva su `enp0s1`)**, servizi `dhcpv6-client mdns ssh`, nessuna porta: **7447 tcp+udp è chiusa di serie** [V] (la zona `FedoraWorkstation` è di Workstation, qui non c'è).
Un RPM la apre correttamente con un file di servizio `/usr/lib/firewalld/services/remotix.xml` (porte tcp+udp 7447) e `%post` `firewall-cmd --permanent --add-service=remotix` solo se firewalld è attivo [W, prassi RPM; non provato qui].
Il pacchetto Debian usa `remotix.ufw`: non c'è ufw su Fedora. Decisione: aprire o no al momento dell'installazione (§9 D6).

---------------------------------------------------------------------------------------------------

## 9. Pacchetto RPM (per XFCE; le parti comuni sono degli altri studi)

Nomi Fedora 45 per `U:debian/control` [V: `dnf repoquery`]:
- Build: `openssl-devel` è la **4.0.3** (esiste anche `openssl3-devel` 3.5.8/3.5.9: il codice chiede libssl >= 3.5: da decidere se OpenSSL 4 va bene o si usa `openssl3-devel`), `pam-devel` 1.7.2, `glib2-devel` 2.90.1, `pipewire-devel` 1.6.11,
  `libdrm-devel` 2.4.134, `libva-devel` 2.24.1, `opus-devel` 1.6, `zlib-ng-compat-devel` (`zlib-devel` non esiste: è `zlib-ng-compat-devel`), `libei-devel` 1.6.0, `libxkbcommon-devel`, `mesa-libgbm-devel`, `wayland-devel` 1.26.0,
  `vulkan-headers` + `vulkan-loader-devel` 1.4.350, `meson` 1.12.1, `patch`, `hwdata`, `wayland-protocols-devel` 1.50, `mesa-libEGL-devel`, **`mesa-libGLES-devel` non esiste** (il pacchetto probabile è `libglvnd-devel` [S]), `libinput-devel` 1.32,
  `pixman-devel`, `libseat-devel` 0.9.3, `systemd-devel` 262 (libudev), `libdisplay-info-devel` 0.3.0, `libxml2-devel` 2.15.4, `cairo-devel`, `pango-devel`, `libpng-devel`, `ngtcp2-devel` 1.22.1, **`nghttp3-devel` assente** (il pacchetto Debian li lega già staticamente), `selinux-policy-devel` 45.24.
- Uso: `systemd` (262), `pam`, `pipewire`, `wireplumber`, `dbus-broker` (bus utente; **non** `dbus-user-session`), `dconf` (comando `dconf` presente di serie: il postinst che compila `/etc/dconf/db/remotix` per GNOME/KDE vale),
  `labwc`, `wlr-randr`, `xorg-x11-server-Xwayland`, `mesa-vulkan-drivers` e `libva`/Mesa video: la voce Debian `va-driver-all` non ha un nome Fedora (i driver sono in `mesa-dri-drivers`, che c'è; `mesa-va-drivers` non esiste nel repo). Font: `dejavu-sans-fonts` [S].
- XFCE-specifico: `xfce4-session` (marcatore), `xfdesktop` (**senza Wayland**), `xfce4-panel`, `xfconf`, `libxfce4windowing`, `gtk-layer-shell` (presente 0.10.1).
- Codec: `openh264` nei repo (2.6.0; il pacchetto `gstreamer1-plugin-openh264` e `ffmpeg-free` sono già installati sullo Spin), nessun `x264`; HEVC/H.264 hardware con la scheda: `vainfo`/Radeon [non provato qui: tocca allo studio video].
- Regole RPM che toccano REMOTIX: preset: `/usr/lib/systemd/system-preset/99-default-disable.preset` finisce con `disable *` [V]: un servizio di terzi **non** parte da solo, quindi «installato spento» è il comportamento di serie (basta
  `%systemd_post`/`%systemd_preun`/`%systemd_postun_with_restart` standard senza preset). File in `/etc` = `%config(noreplace)`; regole polkit in `/usr/share/polkit-1/rules.d` (come oggi); modulo SELinux nel RPM [da decidere].
  Licenze: `LICENSE.md` come `%license`.

---------------------------------------------------------------------------------------------------

## 10. Video e audio (per quanto riguarda XFCE)
PipeWire 1.6.9 + WirePlumber 0.5.18 + `pipewire-pulse`: avviati come unità del manager utente nella sessione locale (`pipewire.service`, `wireplumber.service`, `pipewire-pulse.service`) [V]; nella sessione remota emulata
pipewire/wireplumber/pipewire-pulse sono partiti da soli (attivati da socket). Il codice che parla con `pipewire` è uguale. La parte H.264/VA-API/Vulkan con la Radeon: non guardata (non serviva la scheda per XFCE).
Cattura: `zwlr_screencopy_manager_v1` v3 è offerto (lo ha usato `grim` con successo: 1344x768, PNG). `ext_image_copy_capture_manager_v1` è offerto da labwc 0.20.2 [V]: alternativa futura al screencopy wlr.

---------------------------------------------------------------------------------------------------

## 11. Problemi da affrontare

| # | Che cosa | Dove nel codice | Peso | Cura già nota da Ubuntu/Debian? |
|---|---|---|---|---|
| 1 | **SELinux: il `execve` del desktop negato** con `pam_selinux` nella pila PAM di un servizio `unconfined_service_t` (§8.3) | `U:src/remotix.pam` (da riscrivere), `U:src/child.c` (pam_open_session + exec) | **grande** | no (Debian/Ubuntu non hanno SELinux) |
| 2 | **xfdesktop senza Wayland**: nessuno sfondo/icone, schermo nero (§1.4) | `U:src/session.c` (nessun rimedio; registro E1) | medio (estetico, ma vistoso; peso reale lo decide il proprietario) | no (E1 nasceva da altra causa; qui non si cura con la versione) |
| 3 | Aggancio A2 (pam_exec) su Fedora: dove mettere la riga con authselect, senza farsela cancellare e senza invadere il profilo del sistema (§8.1); anomalia del primo tentativo (§7.3) | `U:debian/remotix.pam-config`, `remotix.postinst/prerm`, `U:src/local_login.c` | grande | parziale (idea e codice sì; il modo di agganciare no) |
| 4 | `remotix.pam` Debian da riscrivere per Fedora (`@include common-*`, `/etc/default/locale`, `pam_motd` dynamic non esistono) | `U:src/remotix.pam` | medio | no |
| 5 | `labwc` 0.20.2 (e wlroots 0.20) al posto di 0.9.3: provare a fondo (tasto «riporta dentro», cursori, `labwc-session.target`, errori di config in `labnag`) | `U:src/session.h:306-345`, `session.c:2864`, `shape.c:131-137` | medio | in parte (studio 7: stessi punti sensibili) |
| 6 | labwc/wlr-randr non installati di serie: dipendenze dell'RPM, avviso chiaro se mancano (`labwc_missing`) | `U:src/session.c:755-772`, `debian/control` | piccolo | sì (Recommends; qui servirà `Requires` o un messaggio) |
| 7 | Tre programmi sopravvivono all'uscita (`abrt-applet`, `geoclue agent`, `localsearch-3`) | `U:src/session.c:4359` (`survivor()`) | piccolo | sì (D-X8 / pulizia dello scope) |
| 8 | Voci di autostart da non far partire in remoto (abrt, dnfdragora-updater, geoclue demo agent, localsearch) oltre a blueman | `U:src/session.c:3240-3270` | piccolo | sì (stesso meccanismo `Hidden=true`) |
| 9 | Regole polkit: ordine dei nomi rispetto a `lightdm.rules` (vince grazie a `50-`); documentare il vincolo e aggiungere al giro di prove il controllo dal greeter (`power-local-seat` con processo del greeter) | `U:src/remotix-no-poweroff.rules`, `prove/check-desktop.py` | piccolo | sì (C6) |
| 10 | PATH remoto: `/etc/environment` vuoto → ripiego fisso, senza `~/.local/bin` e `~/bin` | `U:src/child.c:1573-1807` | piccolo | no |
| 11 | Firewall: porta 7447 chiusa di serie, serve un file di servizio firewalld e una scelta all'installazione | `U:debian/remotix.ufw` (equivalente) | piccolo-medio | no (ufw) |
| 12 | Nessun muro MAC al posto di AppArmor (servizio `unconfined_service_t`) | `U:debian/remotix_network.apparmor` | medio (dipende da D1) | no |
| 13 | Nomi dei pacchetti di costruzione: `openssl-devel` è OpenSSL 4.0 (il codice chiede >= 3.5); `zlib-devel`→`zlib-ng-compat-devel`; `mesa-libGLES-devel` assente; `nghttp3-devel` assente | `U:debian/control`, `build/` | medio | no |
| 14 | `dbus-broker` come bus utente: il codice usa `dbus-run-session`/`sess_bus()` e `org.freedesktop.DBus` (nessuna differenza vista nelle prove; da riprovare a fondo con `StartServiceByName`) | `U:src/session.c` (`sess_bus`, `name_has_owner`) | piccolo | [non provato a fondo] |
| 15 | `xfce4-session-wayland-session` non va installato né richiesto (cartella `~/.config/xfce4/labwc` e `--config-dir` sono altro) | - | piccolo | - |

---------------------------------------------------------------------------------------------------

## 12. Decisioni che spettano al proprietario
- **D1 (SELinux)**: come far partire il desktop dell'utente sotto SELinux enforcing: pila senza `pam_selinux` con processi in `unconfined_service_t`; oppure un piccolo modulo di policy SELinux dentro l'RPM; oppure altro (§8.3).
  È il punto che decide se REMOTIX su Fedora parte o no.
- **D2 (sfondo nero)**: su Fedora lo sfondo nero e l'assenza di icone non sono più un «difetto di versione» ma strutturali (xfdesktop senza Wayland): lo si dichiara (come E1) o si dà un rimedio (es. lo sfondo disegnato da labwc? non esiste in labwc; un client che disegna lo sfondo: lavoro nuovo)?
- **D3 (variabili dell'accesso locale)**: si vogliono nella sessione remota `~/.local/bin` e `~/bin` nel PATH, `EDITOR` e simili che vengono dai `profile.d` della shell di login (REMOTIX oggi non usa una shell di login)?
- **D4 (autostart)**: quali voci togliere in remoto oltre a blueman (§5).
- **D5 (PAM e authselect)**: come agganciare il gancio dell'accesso locale: profilo authselect personalizzato (invasivo), file per display manager in `/etc/pam.d`, o altro; e cosa fare se l'amministratore ha un profilo suo (avviso all'installazione come per Debian, C1).
- **D6 (firewall)**: aprire la 7447 in firewalld all'installazione o lasciare all'amministratore (il servizio resta comunque spento).
- **D7 (OpenSSL)**: OpenSSL 4.0 di Fedora 45 oppure `openssl3-devel` (3.5.x) per la costruzione.

---------------------------------------------------------------------------------------------------

## 13. Che cosa non si può sapere senza provare
1. Il comportamento di XFCE dentro labwc con **scheda vera** (renderer GLES/Vulkan, `WLR_RENDER_DRM_DEVICE`, `zwp_linux_dmabuf_v1`): tutto qui è con `pixman` in VM.
2. Con REMOTIX vero installato: il giro completo (login PAM, `compose_environment()`, cintura xfconf, blocco di `items` con `actions`, chiusura leggera, `survivor()`), anche sotto SELinux dopo la cura scelta per D1.
3. L'azione del tasto `W-C-A-S-F12` (riporta dentro) con labwc 0.20.2: la configurazione si legge, il gesto non è stato fatto.
4. Il primo tentativo del gancio A2 che non ha lasciato traccia (§7.3): riproducibilità.
5. Utenti SELinux confinati (`staff_u`, `user_u`): gancio e sessione.
6. `labwc-session.target` e `blueman.service`/altre unità utente: interazione con la nostra gestione delle unità.
7. Lo spegnimento dal greeter con la regola in vigore: provato con `pkcheck`, non cliccando il pulsante.
8. Che cosa fa `localsearch-3`/`abrt-applet` per ogni utente remoto in termini di carico: non misurato.
9. La tastiera: la VM ha solo `KEYMAP=us` in `vconsole.conf` (limite del banco, segnalato dal coordinatore): nessuna conclusione sulla disposizione di tastiera.

## 14. Prove consigliate
1. (prima di tutto) Un servizio di prova in `/usr/libexec/remotix/` con la **stessa pila PAM** del prodotto e `child.c` vero, in enforcing, per D1: login → desktop in vita → `ausearch -m avc`. Ripetere con ciascuna cura.
2. Il giro `lifecycle` e `prelocal` (studio 13 di Ubuntu) con l'RPM su questa VM, dopo D1 e D5.
3. Provare accesso locale con REMOTIX vivo su lightdm Fedora **più volte** (almeno 5) per vedere se l'aggancio ha mai silenzio.
4. `power-implied` + controllo dal greeter con `pkcheck` su un processo di `lightdm-gtk-greeter` (non di root).
5. Una foto della sessione remota con scheda vera per confermare lo sfondo nero e la grafica con GLES.
6. Un giro di 10 minuti con tre utenti remoti per vedere il carico di `localsearch-3`, `abrt-applet`, `dnfdragora-updater`.
7. Verificare il tasto «riporta dentro» con labwc 0.20.2 su una sessione con finestre massimizzate.

## 15. Che cosa ho cambiato nella VM `xfce` (stato finale)
Acceso solo in modo `virtuale` (due volte); la Radeon non è stata toccata; la VM è SPENTA; istantanea non ripristinata.
- **Installati (dnf, repository Fedora, nessun repository aggiunto)**: `labwc 0.20.2`, `wlroots 0.20.2`, `wlr-randr 0.5.0`, `grim`, `slurp`, `xdg-desktop-portal-wlr`, `labwc-menu-generator`, `libsfdo`, `libliftoff`, `xcb-util-errors`. **Restano installati.**
  Installato e poi **rimosso**: `pamtester`.
- Importata la chiave GPG di Fedora 45 (fatto da dnf).
- Utenti: `prova` e `prova2` hanno fatto accessi locali (creati i soliti file della casa: `.config`, `.cache`, cartelle `Desktop` ecc.; `prova2`: `.gnupg`); sessioni ssh di prova.
- File di prova creati e **tolti**: `/etc/pam.d/lightdm` (copia con riga `pam_exec`), `/etc/pam.d/rxtest*`, `/usr/local/sbin/hook-test.sh`, `/usr/local/sbin/ctx-print.sh`, `/usr/libexec/rxprobe/`, `/etc/systemd/system/rxprobe.service`,
  `/usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules` (copia del file del repository, messa e tolta due volte), `/run/testhook`, chiave ssh `selfkey` e `/home/prova2/.ssh`, `/tmp/*` di prova.
- `semodule -DB` (tolto `dontaudit`) e poi `semodule -B` (ripristinato): policy come all'inizio.
- Tentativo Ubuntu `ssh xfce` che per un istante ha risposto `rx-gnome` (porta 2353 collegata al guest di gnome per alcuni secondi, mentre l'altro agente accendeva): ho solo letto (`ls`, `cat`); da allora ogni mio comando controlla `hostname = rx-xfce` prima di agire.
- Foto della schermata di accesso e dell'accesso sul server: `/media/REMOTIX-FEDORA/studio/xfce/s1.png … s7.png`.
