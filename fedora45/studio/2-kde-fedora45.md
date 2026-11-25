# Studio 2 — KDE Plasma su Fedora 45 (KDE Plasma Desktop Live 45-1.4)

Agente di studio 2, 21 nov 2026. Solo studio: nessun codice del prodotto scritto, REMOTIX non costruito né installato.
Legenda: **[V]** verificato (dove), **[W]** dal web, **[S]** supposizione/ragionamento.
Macchina: VM `kde` (hostname `rx-kde`), Fedora 45 installata dalla ISO «KDE-Desktop-Live-45-1.4», SELinux enforcing.
Sorgenti letti in `/var/tmp/st/x/` del guest (`dnf download --source`): sono la versione **6.8.3** (repo `updates`), mentre la
macchina ha installato la **6.8.1** (immagine live). Dove conta, ho provato sul binario installato (6.8.1) e letto il sorgente 6.8.3:
nei punti citati il codice 6.8.3 è quello che 6.8.1 mostra a runtime. I repository `updates` hanno già 6.8.3: la versione
«vera» di Fedora 45 al rilascio dell'aggiornamento è 6.8.3 [V `dnf repoquery`].
Percorsi: `U:` = `/home/nicfio/Documenti/REMOTIX/ubuntu26.04`.

## 0. Risposta breve alle domande chiave

1. **Il difetto di KWin nel labwc della distribuzione c'è ancora, identico, su Fedora 45** [V, prova con la Radeon]:
   KWin 6.8.1 annidato nel `labwc 0.20.2` di Fedora (wlroots 0.20.2) riceve **2457 `discarded` e 0 `presented`**,
   i client ricevono frame callback con tempo 0 (weston-simple-shm 601 su 601 col tempo 0), Firefox 158 **non dipinge più**
   (0 `attach` ogni 4 s). Con un labwc 0.20.2 + wlroots 0.20.2 **con la nostra patch portata a 0.20** (3 righe, in `handle_scene_buffer_frame_done`):
   **2867 `presented`**, tempo dei callback che avanza, Firefox 249 `attach` ogni 4 s (≈60 al secondo). Quindi, se KDE resta «KWin dentro labwc»,
   serve ancora un labwc nostro (da impacchettare); il difetto è nel `types/scene/surface.c` di wlroots, uguale in 0.20.2.
2. **Ma KWin 6.8 sa fare da sé: `kwin_wayland --virtual` ora cambia la dimensione dello schermo a caldo** [V]. Con `kscreen-doctor`
   (`output.1.addCustomMode.W.H.60000.full`, poi `output.Virtual-0.mode.WxH@60`) l'uscita virtuale `Virtual-0` è passata
   1280x720 → 1920x1080 → 1366x768 senza riavviare KWin; Firefox ha continuato a dipingere uguale (240 `attach`/4 s prima e dopo
   ogni cambio). Il motivo per cui REMOTIX annida KWin in labwc (`kwin.h`: «`--virtual` non può cambiare dimensione») **non vale più su 6.8**.
   Con la Radeon, KWin `--virtual` non ha il difetto delle presentazioni: callback con tempo vero (599 distinti su 600), Firefox 241 `attach`/4 s.
   Nessun labwc nostro, nessuna patch, nessun «ticker», nessuno scambio di copie statiche di wlroots. Va però scritta la parte nuova (protocollo
   `kde_output_management_v2`, disponibile v22 [V `wayland-info`]) al posto di `kwin_host_resize()`, e provato con il flusso `zkde_screencast`
   e con il client vero (non fatto: vedi §10).
3. **Il «permesso» `org.kde.remotix.desktop` non serve più** [V]: nel sorgente 6.8.3 `wayland_server.cpp:132-165` le interfacce «riservate»
   (`zkde_screencast_unstable_v1`, `ext_data_control_manager_v1`, `org_kde_kwin_fake_input`, `org_kde_plasma_window_management`…) sono negate **solo ai client
   «sandboxed»**; e `wayland-info` da una shell normale, senza alcun `.desktop`, vede `zkde_screencast_unstable_v1` v6, `ext_data_control_manager_v1`,
   `org_kde_kwin_fake_input`. Tenere il file è innocuo.
4. **plasmalogin non trattiene chi ha già un desktop remoto vivo: la voce A2 del registro si ripete, in forma ancora peggiore** [V]: l'accesso locale parte
   (password accettata, sessione logind creata), ma `startplasma-wayland` resta fermo (`plasma_waitforname org.kde.KSplash`: «Service was not registered within timeout»),
   il greeter resta congelato sullo schermo, nessun desktop locale. Ripetuto con un desktop Plasma rimasto vivo sul bus dell'utente.
5. **Il KDE di Fedora 45 non ha sddm ma `plasmalogin`** (Plasma Login Manager 6.8): PAM, nomi, file e config diversi (§4). Il codice di REMOTIX
   non lo conosce (`session.c:458` legge solo sddm e lightdm).
6. **H.264 su AMD (Radeon RX 6800) non c'è di serie su Fedora 45** [V]: `vainfo` con il Mesa 26.2.7 di Fedora elenca solo MPEG2/JPEG/VP9/AV1 in decodifica,
   **nessun profilo H.264/HEVC**; RADV espone solo `VK_KHR_video_decode_av1` e `VK_KHR_video_encode_queue`, **non** `video_encode_h264/h265`.
   REMOTIX richiede `h264_vaapi` o `h264_vulkan` e non ha ripiego software: senza RPM Fusion (Mesa «freeworld») su AMD non codifica niente. Vale per ogni desktop.
7. `openssl-devel` in Fedora 45 è **4.0.3** (il `Build-Depends` Ubuntu chiede `libssl-dev >= 3.5`): da verificare con ngtcp2/nghttp3 statici (non KDE, vale per tutti).

## 1. Che cosa c'è (versioni vere) [V tutto dalla VM, `rpm -q` / `dnf repoquery`]

| Componente | Installato (live) | Nei repository `updates` |
|---|---|---|
| Fedora / kernel | Fedora 45, 7.2.11-300.fc45 | |
| plasma-workspace / plasma-desktop / kwin | 6.8.1-3 / 6.8.1-1 / 6.8.1-2 | 6.8.3-1 |
| Qt (qt6-qtbase) | 6.11.2-3 | |
| KDE Frameworks (kf6-kcoreaddons) | 6.31.0 | |
| display manager | **plasma-login-manager 6.8.1-1** (`plasmalogin.service`, alias `display-manager`) | 6.8.3-1; **sddm non è installato né è il default** |
| systemd | 262-3 | |
| PipeWire / WirePlumber | 1.6.9 / 0.5.18 | |
| Xwayland | 24.1.13-2 | |
| xdg-desktop-portal / `-kde` | 1.22.1 / 6.8.1 | |
| labwc / wlroots | **non installati** di serie; nei repo: `labwc 0.20.2-2`, `wlroots 0.20.2-2`, `wlroots0.19 0.19.3-2`, `wlroots0.18 0.18.3-6` | |
| kwin-x11 | non installato (esiste 6.7.5) | |
| kscreen / libkscreen | 6.8.1 | |
| pam-kwallet, kf6-kwallet | 6.8.1 / 6.31.0 (con `ksecretd`) | |
| firefox | 158.0.1 | |
| flatpak / plasma-discover(+flatpak) | 1.18.4 / 6.8.1 | |
| authselect / firewalld / polkit / pam | 1.8.0 / 2.5.2 / 127 / 1.7.2 | |

- Sessioni offerte: **solo** `/usr/share/wayland-sessions/plasma.desktop` (`Name=Plasma`, `DesktopNames=KDE`,
  `Exec=/usr/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland`, `TryExec=/usr/bin/startplasma-wayland`); `xsessions/` **vuota** [V].
  La sessione locale è quindi **Wayland** e non c'è alternativa X11.
- Percorsi: `/usr/bin/kwin_wayland` (file capability `cap_sys_nice=ep` [V `getcap`]), `/usr/bin/kwin_wayland_wrapper`, `/usr/bin/startplasma-wayland`,
  `/usr/libexec/` (non `/usr/lib/x86_64-linux-gnu/libexec`) per `plasma-dbus-run-session-if-needed`, `pam_kwallet_init`, `plasma-login-greeter`, `plasmalogin-helper`.
- Unità utente di Plasma [V `rpm -ql kwin plasma-workspace`]: `plasma-kwin_wayland.service` (nel pacchetto **kwin**, non in plasma-workspace):
  `ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland`, `BusName=org.kde.KWinWrapper`, `Slice=session.slice`; `plasma-workspace.target`
  (`RefuseManualStart=yes`, `StopWhenUnneeded=true`, `BindsTo=graphical-session.target`), `plasma-workspace-wayland.target`
  (`Requires/BindsTo=plasma-kwin_wayland.service`), `plasma-core.target`, `plasma-plasmashell.service`, `plasma-kded6.service`,
  `plasma-ksmserver.service`, `plasma-kwallet-pam.service`… **Stessi nomi che usa il codice** (`session.h:143-144`: `SESSION_UNIT_KWIN`, `SESSION_UNIT_PLASMA`).

## 2. Accesso locale vero, osservato [V: VM virtuale, accesso dalla schermata di accesso con `tasti`/`scrivi`]

- Il greeter è il «Plasma Login» (clock, avatar di `prova` e `prova2`, campo password, Sleep/Restart/Shut Down/Other…); **nessun selettore di sessione** (una sola sessione).
  Gira come utente di sistema `plasmalogin` (uid 981): sessione logind `c1` **class `greeter`**, seat0, tty1, più una `manager-early`; il suo
  compositore è un **proprio** `kwin_wayland` (`plasma-login-kwin_wayland.service`: `kwin_wayland --no-lockscreen --no-global-shortcuts --no-kactivities --inputmethod plasma-keyboard --locale1`,
  `BusName=org.kde.KWin`, `KWIN_USE_OVERLAYS=0`) con il greeter `/usr/libexec/plasma-login-greeter` [V unità e processi].
- Dopo l'accesso di `prova`: sessione logind **`Type=wayland`, `Class=user`, `Seat=seat0`, `VTNr` nuovo (2, poi 3, 4, 5 a ogni accesso), `Service=plasmalogin`, `Desktop=KDE`**.
  Per ogni accesso `plasmalogin` apre un **nuovo VT** (il greeter resta sul VT1 finché vive).
- Ordine di avvio: `plasmalogin-helper` (root) → PAM (`plasmalogin`) → `/etc/plasmalogin/wayland-session` (script come sddm: fa fare la shell di login, legge `/etc/profile`
  e `~/.profile`, poi `exec`) → `/usr/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland` → `startplasma` avvia
  `plasma-workspace-wayland.target` nel **user manager** → `plasma-kwin_wayland.service` (`kwin_wayland_wrapper --xwayland` → `kwin_wayland --wayland-fd 7 --socket wayland-1 --xwayland-fd… --xwayland`),
  plasmashell, kded6, ksmserver, ecc. [V `ps`, `systemctl --user`].
- Processi/unità osservati subito dopo l'accesso (rumorosi per una sessione REMOTIX): `akonadi_*` + `mysqld`, `kdeconnectd`, `kalendarac`, `DiscoverNotifier`, `abrt-applet`,
  `geoclue demo agent`, `xwaylandvideobridge`, **`plasma-welcome` (Welcome Center, finestra al primo accesso di ogni utente)**, `drkonqi-coredump-pickup`,
  `ssh-agent.service`, `xdg-desktop-portal(-kde/-gtk)`.
- Variabili della sessione (plasmashell, [V `/proc/<pid>/environ`]): `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `XDG_SEAT=seat0`, `XDG_VTNR`, `XDG_SESSION_DESKTOP=KDE`,
  `XDG_CURRENT_DESKTOP=KDE`, `DESKTOP_SESSION=/usr/share/wayland-sessions/plasma.desktop` (percorso intero, non il nome), `WAYLAND_DISPLAY=wayland-1` (in quel caso `wayland-0` era occupato da un residuo; non da generalizzare),
  `DISPLAY=:0`, `KDE_FULL_SESSION=true`, `KDE_SESSION_VERSION=6`, `XDG_MENU_PREFIX=plasma-`, `PAM_KWALLET5_LOGIN=/run/user/1000/kwallet5.socket`,
  `SSH_AUTH_SOCK=/run/user/1000/ssh-agent.socket`, `SSH_ASKPASS=/usr/bin/ksshaskpass`, `XDG_CONFIG_DIRS=~/.config/kdedefaults:/etc/xdg:/usr/share/kde-settings/kde-profile/default/xdg`
  (la cartella `kde-settings` è di Fedora), `PATH=~/.local/bin:~/bin:/usr/local/bin:/usr/bin:/bin`, `KDE_APPLICATIONS_AS_SCOPE=1`, `QT_WAYLAND_RECONNECT=1`.
- **Logout locale** (`org.kde.Shutdown.logout`, Plasma 6.8.1, user manager mantenuto vivo da una sessione ssh): dopo 30 s `plasma-workspace.target` e `graphical-session.target` inattivi,
  nessun processo di kwin/plasmashell/ksmserver/ksecretd rimasto, greeter di nuovo su [V una prova]. L'anomalia dello studio Ubuntu 6 §8 («plasma-shutdown ignora il rifiuto e il desktop resta su»)
  **non si è presentata**; una sola prova, non esclude che con altre unità in coda ricapiti [S].
- **Chiusura forzata della sessione logind** (`loginctl terminate-session`) con il user manager vivo: il desktop Plasma (kwin_wayland, plasmashell, ksmserver, plasma-welcome…) **resta vivo**:
  le unità sono del user manager, non dello scope della sessione [V]. È proprio la situazione «desktop orfano» del registro A1.

## 3. KWin 6.8 e il difetto del labwc: prove

### 3.1 Perché Ubuntu ha richiesto il labwc proprio (da `U:studio/6`, `10`, e codice)
- `U:src/kwin.c:1520-1545`: KWin non parte direttamente; il drop-in `plasma-kwin_wayland.service.d/zz-remotix-monitor.conf` (`U:src/session.c:3904-3956`, `write_dropin()`) sostituisce
  `ExecStart` con `remotix --kwin-nested W H NODE -- kwin_wayland_wrapper --xwayland --width W --height H --no-lockscreen`; il binario fa nascere un labwc headless
  (`WLR_BACKENDS=headless`, `WLR_RENDER_DRM_DEVICE=<nodo>` o `WLR_RENDERER=pixman`, `XDG_RUNTIME_DIR` proprio) con un `rc.xml` proprio e un «ticker» layer-shell 1x1, poi fa `exec` di KWin con `--wayland-display`.
  `REMOTIX_LABWC` (`/usr/libexec/remotix/labwc`) è il labwc nostro statico (labwc 0.9.3 + wlroots 0.19.2 con `wlroots-0.19.2-remotix-presented-root.patch`); se manca, ripiego dichiarato su `--virtual`.
- Il difetto (`U:studio/6` §2, confermato in `U:studio/10`): dal 6.5 il backend Wayland annidato di KWin mette un pixel nero come radice e il contenuto in subsurface; wlroots non campiona mai la radice coperta,
  quindi ogni `wp_presentation_feedback` torna `discarded` e il RenderLoop di KWin non avanza.

### 3.2 Il sorgente di Fedora 45 [V, letto]
- `kwin-6.8.3/src/backends/wayland/wayland_output.cpp:297-345`: **identico nella sostanza**: radice con `wp_single_pixel_buffer_manager_v1_create_u32_rgba_buffer(0,0,0,0xFFFFFFFF)`,
  `wp_presentation_feedback(…, *m_surface)` sulla radice, `frameDiscarded()` fa solo `m_frames.pop_front()`.
- `wlroots-0.20.2/types/scene/surface.c:182-192`: `handle_scene_buffer_frame_done()` è ancora solo `wlr_surface_send_frame_done()` dopo il controllo del frame pacing output: **nessuna correzione upstream** in 0.20.2.
- Il pacchetto Fedora `wlroots` ha solo una patch (`Revert-layer-shell-error-on-0-dimension-without-anch.patch`), irrilevante.

### 3.3 Prova (VM con la Radeon, ≈5 minuti, rilasciata; `/var/tmp/st/t2.sh` nel guest) [V]
Banco: KWin 6.8.1 (`--wayland-display` di un labwc headless in `XDG_RUNTIME_DIR` proprio, `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128`, `KWIN_FORCE_SW_CURSOR=1`),
client `weston-simple-shm` (10 s) e Firefox 158 su una pagina con `requestAnimationFrame` e animazione CSS (25 s di attesa, poi tre finestre da 4 s di conteggio degli `attach`); `WAYLAND_DEBUG=1`.
Senza ticker e senza il resto di REMOTIX (il ticker non è servito: il difetto si vede comunque).

| Caso | feedback verso KWin | weston: callback totali / col tempo 0 / tempi distinti | Firefox `attach` per 4 s | Firefox callback totali / tempo 0 |
|---|---|---|---|---|
| `kwin --virtual` (nessun labwc) | (non applicabile) | 600 / 2 / 599 | 241, 241, 241 | 4342 / 0 |
| KWin nel **labwc 0.20.2 di Fedora** | **0 presented, 2457 discarded** | **601 / 601 / 1** | **0, 0, 0** | 2202 / 2192 |
| KWin nel **labwc 0.20.2 + wlroots 0.20.2 patchato** (statico) | **2867 presented**, 0 discarded | 620 / 3 / 618 | 249, 249, 249 | 4541 / 0 |

La patch usata (solo per la prova, nel guest) è quella di `U:build/labwc-ospite/wlroots-0.19.2-remotix-presented-root.patch` portata a 0.20: nel handler `frame_done`, dopo il controllo del pacing output e prima di
`wlr_surface_send_frame_done()`, `if (surface->buffer->primary_output != NULL) wlr_presentation_surface_textured_on_output(wlr_surface_get_root_surface(surface->surface), event->output->output);`.
Si applica con fuzz 1 (contesto di riga diverso: la funzione in 0.20 ha `struct wlr_scene_frame_done_event *event`). Costruzione nel guest con le opzioni di `U:build/labwc-ospite/build.sh`
cambiando `wlroots-0.19` in `wlroots-0.20` nel wrap: riuscita, `labwc 0.20.2 (-xwayland -nls -rsvg -libsfdo) wlroots-0.20.2`, 2,1 MB, `ldd` senza libwlroots [V].
Occorre `-Dwerror=false`? non necessario: non ho verificato se il build regge con `-Werror` (ho passato `werror=false` come in build.sh) [S].
**Avvertenza di prova**: nella VM in modo virtuale (senza Radeon) né labwc né KWin trovano EGL (`DRI2: failed to create screen` su virtio-vga senza 3D; con `LIBGL_ALWAYS_SOFTWARE=1`
`KWin --virtual` parte ma i callback hanno tempo 0 e Firefox non dipinge: **è un effetto del rendering software della VM, non di KWin**: con la Radeon lo stesso KWin `--virtual` è sano).
La prova del difetto va quindi fatta **solo con la GPU** (come in Ubuntu).

### 3.4 `--virtual` ridimensionabile [V Radeon e VM virtuale]
- `kscreen-doctor -o` su `kwin_wayland --virtual` mostra `Virtual-0` con un solo modo (`1280x720@60.00*!`); `output.Virtual-0.mode.1024x600@60` → «mode not found»;
  `kscreen-doctor output.1.addCustomMode.1024.600.60000.full` aggiunge il modo (`2:1024x600@59.85`) e `…mode.1024x600@60` lo imposta: Geometry 1024x600. Ripetuto con la Radeon
  fino a 1920x1080 e 1366x768 con Firefox aperto: KWin vivo, finestra di Firefox continua a dipingere 60 fps, nessun riavvio.
- Sorgente: `src/backends/virtual/virtual_output.cpp:80-137` (`applyChanges`: `customModes`, `currentMode`), `virtual_backend.cpp:54` (`.capabilities = BackendOutput::Capability::CustomModes`), `virtual_output.cpp:142-153` (`canResize()` vero).
  Il protocollo usato dal client è `kde_output_management_v2` (v22) / `kde_output_device_v2`: presenti in KWin [V `wayland-info`: `kde_output_management_v2` v22, `kde_output_device_registry_v2` v26, `kde_output_order_v1`].
- Limiti non provati: (a) il flusso `zkde_screencast_unstable_v1` (nodo PipeWire) segue il cambio di modo? (b) il comando può essere mandato anche con un client nostro invece di `kscreen-doctor`; (c) un modo personalizzato dev'essere accettato con le dimensioni dispari/grandi (4K) del client;
  (d) il cursore e Xwayland dopo il cambio; (e) lo stato resta nel `kwinoutputconfig.json` della cartella di configurazione (REMOTIX usa una cartella di sessione propria: vedi `kwin.c`); (f) la frequenza risulta 59.96/59.80 Hz, non 60.
- Il ripiego dichiarato di Ubuntu («KWin `--virtual`: il desktop mantiene la dimensione di nascita») non è più un declassamento su 6.8.

### 3.5 Le altre cure KDE del codice (clipboard, layout tastiera, danno) su Fedora [V sorgente 6.8.3 + `wayland-info`]
1. **Appunti**: `src/wayland/datacontroldevicemanager_v1.cpp` implementa solo `ext_data_control_manager_v1` (versione 1, presente in `wayland-info`; niente `zwlr_data_control`). `U:src/clipboard_kde.c` (`bind_ext_if_needed`) lo gestisce: cura intatta [V lettura].
2. **Layout tastiera**: `keyboard_layout.cpp:29,59,101` usa `KConfigWatcher` e `handleXkbConfigChanged`; nessun `reloadConfig` su `org.kde.keyboard`. `kwin_layout()` (`kwin.c ~900-960`) manda anche il segnale di `kconfig.notify`: cura intatta [V lettura, S funzionamento].
3. **Danno della cattura** (`capture.c damage_classify`): dipende da come KWin riempie `SPA_META_VideoDamage`: **non verificato** su 6.8 [S].
4. **Screencast**: `screencast_v1.cpp` è versione **6** (`s_version = 6`), ha `stream_output`, `stream_window`, `stream_virtual_output(_with_description)`, `stream_region`; il codice di REMOTIX parla della v5: verificare che la v6 non cambi il comportamento di `cursor mode`/`POINTER_METADATA` [S].
5. **EIS**: `src/plugins/eis/eisbackend.cpp` contiene `connectToEIS`: la strada input resta; versione libei 1.6.0 in Fedora (`libei-devel 1.6.0`) [V].

## 4. plasmalogin (il display manager di KDE su Fedora 45)

### 4.1 Che cos'è [V pacchetto e sorgente 6.8.3]
- «Plasma Login Manager», **fork di SDDM** con un greeter nuovo in QML (README: «forked from SDDM… systemd è un requisito duro»). Servizio `plasmalogin.service` (`Alias=display-manager.service`, `Conflicts=getty@tty1 kmsconvt@tty1`, `Restart=always`,
  `StartLimitBurst=2`), eseguibile `/usr/bin/plasmalogin`, helper `/usr/libexec/plasmalogin-helper`, utente `plasmalogin` (sysusers: uid 981, home `/var/lib/plasmalogin`, stato in `state.conf`).
- Configurazione: **`/etc/plasmalogin.conf`** (tutto commentato di serie: `[Autologin] Relogin Session User`, `[General] Namespaces`, `[Users] DefaultPath RememberLastSession RememberLastUser ReuseSession`, `[Wayland] SessionLogFile`, `[X11]`),
  `/etc/plasmalogin.conf.d/` (vuota), `/usr/lib/plasmalogin/plasmalogin.conf.d/` (vuota); il README dice che i valori di distribuzione stanno in `/usr/lib/plasmalogin/defaults.conf`.
  Sono i file che oggi `U:session.c:296-299, 454-458` (`declared_sessions()`) legge per sddm (`[Autologin] Session`, `/etc/sddm.conf.d`) e **non** per plasmalogin: con più desktop installati la scelta «dichiarata dal sistema» non funzionerebbe; con il solo Plasma non serve [S].
- Preset: `85-display-manager.preset` abilita `plasmalogin` (la VM: `enabled`).

### 4.2 PAM [V file `/usr/lib/pam.d/plasmalogin`, `-autologin`, `-greeter`; **vendor dir `/usr/lib/pam.d`, non `/etc/pam.d`**]
- `plasmalogin`: `auth [success=done…] pam_selinux_permit.so`, `auth substack password-auth`, `-auth optional pam_gnome_keyring.so`, `-auth optional pam_kwallet5.so`, `-auth optional pam_kwallet.so`, `-auth optional pam_oo7.so`, `auth include postlogin`;
  `account pam_nologin + password-auth`; **`session`: `pam_selinux.so close`, `pam_loginuid.so`, `-pam_ck_connector`, `pam_selinux.so open`, `pam_keyinit force revoke`, `pam_namespace`, `include password-auth` (porta `pam_systemd` e `pam_limits`), `-pam_gnome_keyring auto_start`, `-pam_kwallet5 auto_start`, `-pam_kwallet auto_start`, `-pam_oo7 auto_start`, `include postlogin`**.
- `plasmalogin-greeter`: `pam_permit`, `session pam_unix + pam_systemd` (nessuna password). `plasmalogin-autologin`: `pam_permit`, include `system-auth`.
- Le tre includono i file di **authselect** (`password-auth`, `system-auth`, `postlogin`, symlink a `/etc/authselect/…`, «Generated by authselect… will be overwritten»).
- In `/etc/pam.d/` non c'è alcun `plasmalogin`: un file con quel nome in `/etc/pam.d` **sostituirebbe** quello del fornitore (Linux-PAM 1.7.2 prima cerca `/etc/pam.d`, poi `/usr/lib/pam.d`) [V il file di fornitore è usato; S la precedenza, supportata dal fatto che ho creato `/etc/pam.d/plasmalogin` per la prova e il login l'ha usato (la riga `pam_exec` ha girato)].
- **Pam di kscreenlocker**: `/etc/pam.d/kde` (+ `kde-fingerprint`, `kde-smartcard`, `kcheckpass`, `kscreensaver`): `auth substack password-auth`, `account…`, `session … pam_selinux open/close, pam_loginuid, pam_namespace, include password-auth, include postlogin`.

### 4.3 Che cosa vede un aggancio PAM di REMOTIX in plasmalogin [V prova]
Per sapere se la riga `pam_exec` di `remotix-local-login` (`U:debian/remotix.pam-config`, `U:src/local_login.c`) funzionerebbe, ho messo **temporaneamente** `/etc/pam.d/plasmalogin` (copia del fornitore con una riga
`session optional pam_exec.so quiet /usr/local/bin/rxenv.sh` subito prima di `session include postlogin`, cioè **dopo** `pam_systemd` di `password-auth`) e ho fatto un accesso locale. Ambiente che l'hook vede (`PAM_TYPE=open_session`, `PAM_SERVICE=plasmalogin`, `PAM_USER=prova`, `PAM_TTY=/dev/tty5`):
`XDG_SEAT=seat0`, **`XDG_SESSION_CLASS=user`**, **`XDG_SESSION_TYPE=wayland`**, `XDG_SESSION_ID=123`, `XDG_VTNR=5`, `XDG_SESSION_DESKTOP=KDE`, `XDG_RUNTIME_DIR=/run/user/1000`, e il contesto SELinux `unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023`.
Sono le variabili su cui `local_login.c` decide «accesso grafico locale» (nessun `XDG_SEAT` ⇒ niente). **Quindi il programma, con la riga nel posto giusto, riceverebbe quel che si aspetta.** File di prova rimossi (verificato).
Il greeter stesso apre una sessione (class `greeter`, utente `plasmalogin`, uid 981 < 1000): non è una sessione «user» e non si confonde con un utente vero [V `loginctl`].

### 4.4 Come si aggiunge un modulo a PAM su Fedora (authselect) [V file; S la scelta]
- Profilo corrente: `local` con le feature `with-silent-lastlog`, `with-mdns4` [V `authselect current`]. I file generati (`/etc/authselect/{system-auth,password-auth,postlogin,…}`) dicono di non essere modificati a mano: `authselect apply-changes`/`select` li riscrive; `authselect check` segnala la modifica.
  **Non esiste** per authselect un meccanismo di «drop-in» o «pam-auth-update»: i modi sono (a) un **profilo personalizzato** (`authselect create-profile remotix -b <profilo>`) che incorpora la riga, ma ne serve uno per ogni profilo base (`local`, `sssd`, `winbind`) e l'amministratore deve selezionarlo; (b) aggiungere la riga ai **file PAM di ciascun display manager** in `/etc/pam.d/` (`plasmalogin`, `gdm-password`, `lightdm`, `sddm`…), dove una copia in `/etc` copre il file del fornitore ma poi non segue gli aggiornamenti del pacchetto del DM;
  (c) `postlogin` (incluso da `login`, `sshd`, `kde`, `su`, `plasmalogin`, `gdm*`…): riscritto da authselect; (d) niente PAM: osservare logind/il DM da servizio (stessa regola «una sola per tutti» ma con altro meccanismo). **Decisione al proprietario** (§8).
- `password-auth` ha `-session optional pam_systemd.so`, **`pam_limits`**, **nessun `pam_faillock`** nel profilo `local` con queste feature (non c'è `with-faillock`) [V]; `postlogin`: `pam_umask`, `pam_lastlog2` (non `pam_lastlog`).
- Il servizio PAM `remotix` di Debian (`U:src/remotix.pam`) usa `@include common-auth` ecc.: **su Fedora va riscritto** sul modello di `/etc/pam.d/sshd` [V il testo di sshd di Fedora]:
  `auth substack password-auth`, `auth include postlogin`, `account required pam_sepermit.so`, `account required pam_nologin.so`, `account include password-auth`, `password include password-auth`, `session required pam_selinux.so close`, `session required pam_loginuid.so`,
  `session required pam_selinux.so open env_params`, `session required pam_namespace.so`, `session optional pam_keyinit.so force revoke`, `session optional pam_motd.so`, `session include password-auth`, `session include postlogin` (+ la riga `pam_listfile … /etc/remotix/denied-users` per escludere root).
  Con `@include` (che è un'estensione Debian) non funziona; in Fedora è `substack`/`include`. Se manca il file, PAM cade su `other` = `pam_deny` (`/etc/pam.d/other` 154 byte) e **ogni** password giusta è rifiutata (già documentato nel commento di `U:src/remotix.pam`).

### 4.5 Che cosa succede a un accesso locale quando lo stesso utente ha un desktop già vivo (voce A2) [V due prove]
Scenario: l'utente `prova` ha una sessione logind e il suo user manager vivo (tenuto da una sessione ssh) con un desktop Plasma attivo sul bus (`org.kde.KWin`, `org.kde.KWinWrapper`, plasmashell, ksmserver). Accesso dal greeter con la password giusta:
- plasmalogin **non trattiene** nulla: autentica, apre la sessione (`Class=user`, `seat0`, VT nuovo), lancia `startplasma-wayland`;
- `startplasma-wayland` (pid rimasto vivo) aspetta `org.kde.KSplash` (`plasma_waitforname`): **«WaitForName: Service was not registered within timeout»** dopo 30 s; il greeter rimane congelato (immagine sfocata, campo password con i puntini, pulsanti spenti) per più di un minuto; **non arriva nessun desktop locale** né si torna alla schermata d'accesso;
  le unità del vecchio desktop (`plasma-kwin_wayland.service` ecc.) sono già attive e non vengono riavviate [V `journalctl --user`, screenshot `/media/REMOTIX-FEDORA/studio/kde/a2b.png`, `a2c.png`; processi `startplasma-wayland` pid 9750 + `plasma_waitforname`].
- **Differenza con Ubuntu/sddm** (studio 6: «KDE e XFCE rimandano alla schermata di accesso»): qui il greeter resta appeso, non c'è rimando. La cura di REMOTIX (PAM che chiude il desktop remoto prima di lasciar proseguire) resta quella giusta, ma il fallimento senza cura è più brutto.
- plasmalogin ha una funzione **`ReuseSession`** (`src/daemon/Seat.cpp:95-113`, `Display.cpp:251-308`): se lo stesso utente ha già una sessione `Service=plasmalogin` in stato `online`, la riattiva (`UnlockSession` + `ActivateSession`) invece di crearne una nuova.
  Si applica **solo alle sessioni aperte da plasmalogin** (`session.service() == "plasmalogin"`), mai a una sessione REMOTIX (servizio PAM `remotix`) [V lettura]. Non serve a REMOTIX. Impostazione `ReuseSession=true` di serie.

### 4.6 Blocco schermo
KWin del greeter parte con `--no-lockscreen`; la sessione dell'utente ha il blocco schermo (`kscreenlocker`, PAM `kde`). REMOTIX avvia KWin con `--no-lockscreen` (`U:src/session.c:3951-3953`): flag ancora presente in `kwin_wayland --help` 6.8.1 [V].

## 5. Portafoglio (KWallet / ksecretd) e `pam_kwallet`

- Fedora 45 con Plasma 6.8: il portafoglio è servito da **`ksecretd`** (`/usr/bin/ksecretd` in `kf6-kwallet 6.31`): sul bus ci sono `org.freedesktop.secrets`, `org.kde.ksecretd`, `org.freedesktop.impl.portal.desktop.kwallet`, `org.kde.secretservicecompat` [V `busctl --user list`]; `kwalletd6` è su richiesta (`org.kde.kwalletd5/6` non attivi). `ksecretd` è partito **dentro lo scope della sessione di accesso** (PID 1 padre, `session-85.scope`) perché `pam_kwallet5` lo avvia in `open_session` (`pam_kwallet5: final socket path: /run/user/1000/kwallet5.socket`).
- Dopo l'accesso locale esistono `~/.local/share/kwalletd/kdewallet.kwl` e `kdewallet.salt`; nessun `~/.config/kwalletrc` [V]. Il portafoglio viene creato e sbloccato con la **password digitata** (`PAM_KWALLET5_LOGIN` nell'ambiente; `plasma-kwallet-pam.service` + `/usr/libexec/pam_kwallet_init`).
- `pam_kwallet5.so` è in `/usr/lib64/security/` (pacchetto `pam-kwallet`, installato sulla live KDE); **è referenziato da plasmalogin, da `-autologin` e (con `-`) da nessun altro file di sistema**; il servizio PAM `remotix` non lo ha ⇒ **in una sessione remota il portafoglio non viene creato né sbloccato** [S dal confronto; non provato con REMOTIX]: la prima app che chiede un segreto (Firefox/Chrome con password, NetworkManager, KDE Connect, Discover) mostrerà la finestra di creazione/apertura portafoglio con richiesta di password, contro la regola «nessuna finestra di password non richiesta» della 1.5.3 (stessa analisi di `U:studio/6` §8). Cura candidata: nel servizio PAM `remotix` `-auth optional pam_kwallet5.so` e `-session optional pam_kwallet5.so auto_start` (con gnome-keyring per GNOME). **Decisione e prova**.
- `gnome-keyring` **non** è installato sulla variante KDE; `pam_gnome_keyring.so` e `pam_oo7.so` sono messi con `-` (ignorati se mancano).

## 6. Come REMOTIX avvia e chiude oggi KDE e che cosa su Fedora 45 non regge

| Punto del codice (`U:`) | Oggi | Su Fedora 45 |
|---|---|---|
| `src/session.h:142-144` | `exec startplasma-wayland`, unità `plasma-kwin_wayland.service`, `plasma-workspace.target` | **regge** [V nomi e percorsi] |
| `src/session.c:3904-3956` (drop-in `ExecStart`) | `kwin_wayland_wrapper` da `PATH` (ripiego `/usr/bin/kwin_wayland_wrapper`) | **regge**: `/usr/bin/kwin_wayland_wrapper` esiste; stessa opzioni `--xwayland --width --height --no-lockscreen` accettate da `kwin_wayland` 6.8.1 (`--help`) [V] |
| `src/kwin.c:1520-1545` (labwc nostro `REMOTIX_LABWC=/usr/libexec/remotix/labwc`, `-C`, `rc.xml`, ticker) | labwc nostro statico 0.9.3 + wlroots 0.19.2 patchato | **va rifatto per wlroots 0.20** se si resta nell'annidamento (patch portata, provata) **oppure sostituito** con `--virtual` + ridimensionamento via `kde_output_management_v2` (§3.4) |
| `src/kwin.c` `kwin_open()`: `zkde_screencast_unstable_v1` su `WL-0` (annidato) | output `WL-0` | con `--virtual` l'uscita si chiama **`Virtual-0`** (come fino alla 1.0 su Debian); il nome va letto, non assunto |
| `src/kwin.c` `kwin_check_permission()` + `debian/org.kde.remotix.desktop` | gate sul `.desktop` | **non serve più** (§0.3) ma innocuo; `kwin_check_permission()` non deve fallire se il file manca |
| `src/kwin.c` `kwin_eis_fd()`: `org.kde.KWin.EIS.RemoteDesktop.connectToEIS(7)` | EIS | codice `plugins/eis/eisbackend.cpp` presente in 6.8.3 [V sorgente]; non provato a runtime |
| `src/session.c:458` `sddm_dirs`, `lightdm_dirs` | legge sddm e lightdm | **manca plasmalogin** (`/etc/plasmalogin.conf`, `.conf.d`, `/usr/lib/plasmalogin/…`, `/var/lib/plasmalogin/state.conf`): serve solo per scegliere fra più desktop installati |
| `src/session.c:4179-4300` `session_kde_logout_watch()` (Log Out che si ferma a metà) | cura del 17 nov per KWin 6.3/6.6 | su 6.8.1 un Log Out ha chiuso tutto in 30 s senza la cura (una prova): la cura è innocua; da riprovare con il codice vero |
| `src/session.c:5127-5372`, `3641-3666` (`org.kde.Shutdown.logout()`, `StopUnit("plasma-workspace.target","fail")`) | `plasma-shutdown` | metodi presenti: `logout`, `logoutAndReboot`, `logoutAndShutdown`, `saveSession` [V `busctl introspect org.kde.Shutdown`] — NOTA 25 nov 2026: la chiusura forzata del prodotto ora ferma `graphical-session.target` (vedi `exit_kde()` e PIANO.md) |
| `src/session.c:1534-1580` KIOSK (`[KDE Action Restrictions]`, `kwinrc` di sessione) e `3369-3386` (`XDG_MENU_PREFIX=plasma-`) | file di configurazione dell'utente | `XDG_MENU_PREFIX=plasma-` è quello che la sessione vera esporta [V]; `XDG_CONFIG_DIRS` della sessione vera include `/usr/share/kde-settings/kde-profile/default/xdg` (profilo Fedora): se REMOTIX ricostruisce `XDG_CONFIG_DIRS` a mano, va tenuto [S] |
| `debian/remotix.pam-config` / `src/remotix.pam` | `pam-auth-update`, `@include common-*` | **da riscrivere** per authselect/`substack` (§4.4) |
| `debian/control` `Recommends: labwc, wlr-randr, xwayland, mesa-vulkan-drivers, va-driver-all` | | nomi Fedora al §7 |

- **Plasma Setup (wizard del primo avvio)** [V sorgente 6.8.3 e unità]: `plasma-setup.service` (`WantedBy=multi-user.target`, `Before=display-manager.service`, `ConditionPathExists=!/etc/plasma-setup-done`, non gira in live) lancia `plasma-setup-bootutil`;
  senza il file-bandiera parte un wizard **prima** del display manager: crea il **primo utente** (gruppo `wheel` da `/etc/xdg/plasmasetuprc`, `UserGroups=wheel`), lingua, tastiera, fuso orario, hostname, rete; usa un utente `plasma-setup` con una regola polkit (`plasma-setup-polkit.rules`, solo per quell'utente);
  scrive un **autologin temporaneo** in `/etc/plasmalogin.conf.d/99-plasma-setup.conf` (`Relogin=true`) per il primo accesso e lo toglie con un file di autostart dell'utente (`remove-autologin.desktop`). **Non tocca REMOTIX** (che si installa dopo e non c'è al primo avvio); l'unico effetto: all'installazione di REMOTIX su una macchina appena finita ci potrebbe essere ancora l'autologin temporaneo (accesso locale automatico: stessa regola «locale esclude remoto»). Nella VM `/etc/plasma-setup-done` esiste (creato prima dello studio) e il wizard non gira.

## 7. Pacchetto: nomi Fedora (parte KDE e comune) [V `dnf repoquery`]

Mappatura di `U:debian/control` (Build-Depends → pacchetti `-devel`): `libssl-dev` → `openssl-devel` (**4.0.3**, vedi 0.7), `libpam0g-dev` → `pam-devel` 1.7.2, `libglib2.0-dev` → `glib2-devel` 2.90.x,
`libpipewire-0.3-dev` → `pipewire-devel` 1.6.9/1.6.11, `libdrm-dev` → `libdrm-devel` 2.4.134, `libva-dev` → `libva-devel` 2.24.1, `libopus-dev` → `opus-devel` 1.6, `zlib1g-dev` → `zlib-ng-compat-devel` 2.3.3 (o `zlib-devel`),
`libei-dev` → `libei-devel` 1.6.0, `libxkbcommon-dev` → `libxkbcommon-devel` 1.13.1, `libgbm-dev` → `mesa-libgbm-devel` 26.2.x, `libwayland-dev` → `wayland-devel` 1.26.0, `libvulkan-dev` → `vulkan-loader-devel` 1.4.350 (+ `vulkan-headers`),
`libegl-dev`/`libgles-dev` → `mesa-libEGL-devel`/`mesa-libGLES-devel`, `libinput-dev` → `libinput-devel` 1.32.0, `libpixman-1-dev` → `pixman-devel` 0.46.2, `libseat-dev` → `libseat-devel` 0.9.3, `libudev-dev` → `systemd-devel` 262,
`libdisplay-info-dev` → `libdisplay-info-devel` 0.3.0, `libxml2-dev` → `libxml2-devel` 2.15.4, `libcairo2-dev` → `cairo-devel` 1.18.6, `libpango1.0-dev` → `pango-devel` 1.58.2, `libpng-dev` → `libpng-devel` 1.6.59, `meson`, `patch`, `hwdata` 0.413, `wayland-protocols-devel` 1.50. Tutti esistono.
Dipendenze d'uso: `pipewire`, `wireplumber`, `systemd`, `pam`, `dbus-broker` (equivalente di `dbus-user-session`: il bus utente c'è di serie), `dconf` per GNOME. Per KDE se resta il labwc nostro: `labwc`/`wlroots` di Fedora **non** servono a KWin (restano per XFCE/LXQt); con `--virtual` per KDE il labwc non serve più.
- **Pacchetto del labwc nostro, se lo si tiene**: i sorgenti Fedora sono `labwc-0.20.2-2.fc45.src.rpm` e `wlroots-0.20.2-2.fc45.src.rpm`; REMOTIX dovrebbe portarsi labwc 0.20.2 + wlroots 0.20.2 + la patch, costruiti statici (Fedora vieta le librerie incorporate: `bundled()` provides da dichiarare, **[W/S]**); labwc è GPL-2.0, wlroots MIT: restano gli obblighi di sorgente corrispondente del §7 di `U:studio/6`.
  Anche la politica Fedora di non fare linking statico di librerie di sistema andrebbe verificata con il proprietario/rilascio: REMOTIX non è nei repository ufficiali, quindi non si applica automaticamente [S].
- **Video** [V Radeon]: Mesa 26.2.7; `mesa-dri-drivers` contiene `radeonsi_drv_video.so` ma `vainfo` su RX 6800 non mostra H.264/HEVC; `mesa-vulkan-drivers` ha RADV 26.2.7 senza `VK_KHR_video_encode_h264/h265`;
  non esistono `mesa-va-drivers` né `mesa-va-drivers-freeworld` nei repository Fedora (il driver cerca `/usr/lib64/dri-freeworld/` e `/usr/lib64/dri-nonfree/`, che in Fedora esiste solo con RPM Fusion [W/S]); sulla live ci sono `libva-intel-media-driver` 26.2.4 (Intel: H.264 ok [S]) e `noopenh264` (stub).
  `ffmpeg-free 9.0.2` elenca `h264_vaapi`, `libopenh264`, `h264_nvenc`, `h264_amf`… ma H.264 hardware via Mesa AMD no.
- **Regole RPM** (comuni): `99-default-disable.preset` ⇒ i servizi nuovi sono **disabilitati** di serie (coerente con «installato disabilitato»); `%systemd_post` non li abilita; usare `%sysusers_create_compat`/`sysusers.d`, `tmpfiles.d`; SELinux nel §9.

## 8. Sistema Fedora per KDE: SELinux, firewall, polkit

- **SELinux** [V]: enforcing, policy `targeted`, 437 moduli. `plasmalogin` e il suo helper girano in **`xdm_t`**; kwin del greeter e la sessione dell'utente in `unconfined_t` (`unconfined_u:unconfined_r:unconfined_t:s0-s0:c0.c1023`). Nessuna negazione AVC oggi (`ausearch -m avc,user_avc -ts today`: «no matches») durante gli accessi, il logout e l'uso di Firefox/KWin.
  Un servizio di terzi da RPM, eseguibile in `/usr/libexec/<nome>/` (tipo `bin_t`), lanciato da systemd come root gira in **`unconfined_service_t`** (provato con una copia di `sleep`: sia come root sia con `--uid=1000`); è senza vincoli: **nessun modulo SELinux è necessario**.
  Quel che sarebbe da provare (non fatto, REMOTIX non è installato): che `pam_selinux.so open` nel `child.c` faccia nascere il desktop in `unconfined_t` e non resti in `unconfined_service_t` (il servizio `remotix` dovrebbe avere le righe `pam_selinux close/open` come `sshd`).
  Il booleano `selinuxuser_direct_dri_enabled` è `on`. Sostituisce il profilo AppArmor di Ubuntu (`remotix_network.apparmor`): sul lato rete non c'è nulla di equivalente se non si scrive una politica propria [S].
- **firewalld** [V]: attivo, zona `FedoraWorkstation` (predefinita, anche sul gusto KDE): `services: dhcpv6-client samba-client ssh`, **`ports: 1025-65535/udp 1025-65535/tcp`** (aperte di serie): la porta 7447 tcp+udp è **già raggiungibile** senza fare nulla sulla variante desktop; su una zona diversa (`public`, Server) no.
  Un pacchetto corretto dovrebbe aggiungere un servizio firewalld (`/usr/lib/firewalld/services/remotix.xml`, 7447 tcp+udp) senza abilitarlo da sé (decisione dell'amministratore, come oggi con ufw `U:debian/remotix.ufw`).
- **polkit** [V]: `/usr/share/polkit-1/rules.d/` contiene `11-fedora-kde-policy.rules`, `50-default.rules`, `plasma-setup-polkit.rules`, `org.freedesktop.Flatpak.rules` ecc.; `/etc/polkit-1/rules.d/` solo `49-polkit-pkla-compat.rules`. Gruppo amministrativo: `wheel`. Le regole `remotix-*.rules` (spegnimento) vanno in `/usr/share/polkit-1/rules.d/` o `/etc/polkit-1/rules.d/`; da verificare con `11-fedora-kde-policy.rules` che non conceda spegnimento ai locali in modo che prevalga [S, non letta a fondo].
- **PAM/faillock**: nel profilo `local` senza `with-faillock` non c'è `pam_faillock` [V `password-auth`].

## 9. Flatpak e Discover [V]
`flatpak 1.18.4` e `plasma-discover-flatpak 6.8.1` installati; `flatpak remotes` mostra solo `fedora` (`system,oci`); Flathub non abilitato di serie (filtro «third party» di Fedora). Discover parte in autostart come `DiscoverNotifier` nella sessione.
Rilevante per REMOTIX: browser/app Flatpak in sessione remota usano `xdg-document-portal` e `xdg-desktop-portal-kde`, nessuna interazione con il portafoglio salvo `org.freedesktop.secrets`. KWin considera «sandboxed» i client Flatpak (`isSandboxed()`): **non** vedono `zkde_screencast`, `ext_data_control`, `fake_input` (non rilevante: sono i client di REMOTIX a usarli, non sandboxed) [V sorgente].

## Problemi da affrontare

1. **Come ospitare KWin su Fedora 45**: (a) annidato in labwc 0.20.2 con labwc+wlroots 0.20.2 **patchati e statici** (difetto dimostrato; patch portata, funziona); oppure (b) **`--virtual` + ridimensionamento via `kde_output_management_v2`** (nessun labwc nostro; ridimensionamento provato con `kscreen-doctor`; flusso `zkde_screencast`, cursore, Xwayland non provati).
   Dove: `U:src/kwin.c:1296-1720` (`kwin_nested_alive`, `host_rc`, ticker, `kwin_host_resize/settle`), `src/session.c:3904-3956`, `src/kdehost.h`, `src/Makefile:132-133` (`LABWC`), `debian/rules:26-61`. Peso: **grande** per (a) se serve di nuovo tutta la catena di build/licenze (cura nota sì, Ubuntu: `U:build/labwc-ospite/`, `U:studio/6` §5, §7); **medio** per (b) (codice nuovo: client di `kde_output_management_v2`; cura nota **no** per la parte nuova, sì per il resto).
2. **H.264 su AMD non esiste di serie**: servirebbe RPM Fusion (Mesa freeworld) o una decisione diversa (AV1 non basta: la RX 6800 decodifica AV1 ma non lo codifica; `av1_vaapi` non esiste lì). Dove: `U:src/encoder.c:1529-1530, 1795-1830`, `debian/postinst` (messaggio sul test di codifica), `debian/control` (Recommends). Peso: **grande** (per ogni desktop); cura nota **no**.
3. **Aggancio PAM su Fedora**: il file `remotix.pam` (`@include`) non vale; il profilo `pam-auth-update` non esiste; authselect non ha drop-in. Va deciso dove mettere `pam_exec remotix-local-login` (profilo authselect personalizzato / file PAM per DM / altro) e come toglierlo alla rimozione; la riga deve stare **dopo** `pam_systemd` (nel file `plasmalogin` è dentro `password-auth`). Dove: `U:debian/remotix.pam-config`, `remotix.postinst:42-52`, `remotix.postrm`, `src/remotix.pam`, `src/local_login.c`. Peso: **grande**; cura nota **parziale** (Debian `pam-auth-update`).
4. **Accesso locale appeso con un desktop remoto vivo** su plasmalogin (A2 confermata, forma peggiore): serve l'aggancio del punto 3 anche per `plasmalogin` (che non è il PAM di sddm/gdm). Peso: **grande** finché non c'è il 3; cura nota **sì** (§11.57, Debian).
5. **Nuovo display manager non riconosciuto**: `declared_sessions()` non legge plasmalogin (`/etc/plasmalogin.conf`, `.conf.d`, `/usr/lib/plasmalogin`, `/var/lib/plasmalogin/state.conf`). Peso: **piccolo** (solo con più desktop installati); cura nota **sì** (stessa logica sddm).
6. **Servizio PAM `remotix` su Fedora**: riscrittura con `substack/include`, `pam_sepermit`, `pam_selinux close/open env_params`, `pam_loginuid`, `pam_namespace`, `pam_keyinit`, `pam_motd`, `postlogin`, `pam_listfile` per root. Peso: **medio**; cura nota **sì** (modello Debian/sshd).
7. **Portafoglio nelle sessioni remote**: `ksecretd`/`pam_kwallet5` non attivati da PAM `remotix`; rischio di finestra password non voluta. Dove: `U:src/remotix.pam`. Peso: **medio**; cura nota **no** (Ubuntu: «decisione necessaria»).
8. **OpenSSL 4.0 in Fedora 45** contro ngtcp2/nghttp3 statici e `libssl-dev >= 3.5`: compatibilità API da verificare (comune). Peso: **grande se non compila**; cura nota no.
9. **Pacchetto RPM**: spec nuova (macro systemd, sysusers, tmpfiles, `bundled()` per i sorgenti incorporati), servizio disabilitato (preset `99-default-disable`), servizio firewalld, regola polkit, niente `dh-apparmor`; modulo/etichette SELinux non necessari ma da provare dopo l'installazione. Peso: **medio**; cura nota **sì** (Debian) ma tutta da riscrivere.
10. **Il «Welcome Center» e i servizi di sfondo di una sessione Plasma Fedora** (akonadi+mysqld, kdeconnect, kalendarac, abrt, geoclue demo agent) pesano in una sessione remota: finestra «Welcome» al primo accesso di ogni utente. Valutare di ridurli (KIOSK/autostart) come per `plasma-fallback-session-restore` (`U:src/session.c:1582-1590`). Peso: **piccolo-medio**; cura nota **parziale**.
11. **Desktop orfano dopo `loginctl terminate-session`** (A1) su Plasma: confermato [V]; la regola «nessun desktop orfano» deve funzionare con le unità di Fedora. Peso: **medio**; cura nota **sì** (`U:session.c`, §11.56).
12. **Logout KDE** (`session_kde_logout_watch`): una prova ha chiuso tutto senza la cura; ripetere con il codice vero. Peso: **piccolo**; cura nota **sì**.
13. **File di prova nelle `licenses`**: se si tiene il labwc nostro, `THIRD-PARTY-LICENSES` e `LICENSE.md:95-101` vanno rifatti per Fedora (come in `U:studio/6` §7). Peso: **piccolo-medio**; cura nota **sì**.
14. **R-SEC-035 / D10** (falso allarme `CanPowerOff … (no answer)` su Fedora): non provato qui; nota da `U:studio/6` p.13 [S].

## Decisioni che spettano al proprietario

1. **Strada per KDE**: (a) labwc+wlroots 0.20 patchati e statici impacchettati da REMOTIX (strada già percorsa su Ubuntu, con manutenzione di sicurezza e obblighi di licenza GPL/MIT) oppure (b) `--virtual` con ridimensionamento via protocollo KWin (meno pezzi, ma da provare a fondo con cattura/cursore/Xwayland) — e se il codice Fedora/Ubuntu 26.04 debba seguire la stessa strada (Ubuntu ha KWin 6.6.7: lì (b) non è provata; il «ridimensionamento a caldo» di `--virtual` va controllato su 6.6).
2. **Dove agganciare PAM** (profilo authselect proprio, file PAM per ciascun DM, osservazione di logind senza PAM) e come dirlo all'amministratore (avviso all'installazione, come `pam-auth-update`).
3. **H.264 su AMD**: dichiarare RPM Fusion come requisito/raccomandazione, accettare «niente video senza», o cercare un'altra strada (AV1/software: oggi escluse dal prodotto).
4. **Portafoglio**: aggiungere `pam_kwallet5` (e keyring) al servizio PAM `remotix`, o accettare la finestra.
5. **Welcome Center / servizi di sfondo** nella sessione remota Fedora: lasciarli o spegnerli.
6. Se `plasmalogin` debba entrare nelle prove di accettazione come DM del gusto KDE (è il default Fedora): sì, perché è diverso da sddm (nuovo, non coperto dalle prove di Ubuntu).

## Che cosa non si può sapere senza provare

- Se con `--virtual` il flusso `zkde_screencast_unstable_v1` (`stream_output` su `Virtual-0`) **segue il cambio di modo** senza rinegoziare male, e che cosa fa il cursore (`POINTER_METADATA`) con `KWIN_FORCE_SW_CURSOR`; e Xwayland (`--xwayland`) al cambio di dimensione.
- Se REMOTIX, con il codice vero, parte su Fedora 45: compilazione con OpenSSL 4, `pam_selinux open` nel `child.c`, `unconfined_service_t` come dominio del servizio e `unconfined_t` per i desktop, `pam_exec` della regola A2 in `plasmalogin`, firewall.
- Se `pam_kwallet5` nel servizio `remotix` crea/sblocca davvero il portafoglio senza finestre.
- Se Plasma 6.8.3 (aggiornamento) cambia qualcosa su `--virtual`, `kde_output_management_v2` o sul gate (ho letto 6.8.3 e provato 6.8.1: coerenti nei punti toccati).
- Il comportamento dello stesso difetto con **Chrome** (provato solo Firefox 158 e weston) e con KWin 6.8.3.
- Il logout con più unità in coda (la cura del 17 nov).
- La tastiera in sessione: **la VM ha solo `KEYMAP=us`** (limite del banco avvisato dal coordinatore): nulla da concludere su `kxkbrc`/layout.

## Prove consigliate

1. **Annidato + patch (strada a)**: `labwc` patchato 0.20.2 + KWin 6.8 con Firefox **e Chrome** sulla Radeon, con il ticker e `rc.xml` veri; contare `presented/discarded` (script `/var/tmp/st/t2.sh nested-patched` nel guest, riproducibile). Verificare `readelf`/`strings` per il renderer pixman e `ldd` senza wlroots.
2. **`--virtual` + resize (strada b)**: con la Radeon e il prodotto vero (o un client di prova che chieda `stream_output`), cambiare modo a caldo durante la cattura; verificare la rinegoziazione del nodo PipeWire, il cursore, Xwayland; provare anche 2560x1080 e 3840x2160.
3. **A2 con REMOTIX**: aggancio PAM scelto in `plasmalogin` → desktop remoto aperto → accesso locale: desktop remoto chiuso e desktop locale in cima senza appendersi (come i desktop di Debian/Ubuntu).
4. **A1**: desktop remoto aperto → `systemctl restart remotix` → accesso locale; nessun desktop orfano.
5. **Portafoglio**: sessione remota con e senza `pam_kwallet5` nel servizio PAM, aprire Firefox con una password salvata e Discover.
6. **SELinux**: dopo l'installazione, `ausearch -m avc` durante una sessione remota completa; `ps -eZ` del servizio e dei desktop nati da `child.c`.
7. **Logout** (Log Out da Plasma remoto, attendere 30 s) con kwin 6.8.3 e con l'aggiornamento di sistema applicato.
8. **Video**: `vainfo`/`vulkaninfo` dopo avere abilitato RPM Fusion sulla stessa Radeon per vedere se compare H.264 (non fatto: nessun repository di terzi abilitato).
9. Confronto con Plasma 6.8.3: ripetere `t2.sh` dopo `dnf upgrade kwin kwin-libs kwin-common` (non fatto: la regola vieta l'aggiornamento completo).

## Che cosa ho cambiato nella VM `kde` (hostname `rx-kde`)

- Pacchetti installati con dnf (tutti dal repository Fedora): `labwc`, `wlroots`, `wlr-randr` (+ dipendenze: `libseat`, `libliftoff`, `libsfdo`, `aml`, `neatvnc`, `grim`, `slurp`, `xdg-desktop-portal-wlr`, `labwc-menu-generator`…), `weston`, `weston-libs`, `weston-demo` (i client `weston-simple-*`), `patch`, e i pacchetti di `dnf builddep labwc-0.20.2-2.fc45.src.rpm wlroots-0.20.2-2.fc45.src.rpm` (tanti `-devel`, `meson`, `gcc`…).
- `/var/tmp/st/` nel guest: sorgenti scaricati (`*.src.rpm` di kwin, plasma-workspace, plasma-login-manager, plasma-setup, labwc, wlroots), `x/` sorgenti estratti, `bld/` albero di costruzione, `labwc-patched` (binario labwc+wlroots 0.20.2 patchato), `wl020.patch`, script `t1.sh`, `t2.sh`, `clock.html`, profilo Firefox `ffprof/`, log `r2-*.{fb,wcb,ff,labwc}`.
- Dati di `prova` creati dagli accessi: `~prova/.local/share/kwalletd/` (portafoglio), configurazioni Plasma/akonadi, ecc. Un accesso con password sbagliata (una riga di fallimento nel journal).
- File di prova messi e **rimossi**: `/etc/pam.d/plasmalogin`, `/usr/local/bin/rxenv.sh`, `/var/tmp/hook-*`, `/usr/libexec/rxtest/` e unità transitorie `rxtest1/2` (verificato che non esistono più).
- Non toccati: `/etc/plasma-setup-done` (già presente), firewall, SELinux, authselect, utenti, `/etc/pam.d` (stato originale ripristinato), nessun repository abilitato, nessun `dnf upgrade`.
- Screenshot sul server: `/media/REMOTIX-FEDORA/studio/kde/*.png`.
- La VM è **spenta**; la Radeon è stata usata una sola volta, circa 5 minuti (17:37-17:42), ed è **libera** (`stato`: «Radeon held by VM: none», `03:00.1 snd_hda_intel`).
- Nota sul banco: nessun comando ssh ha risposto da un altro guest (ho controllato `hostname == rx-kde` prima dei comandi di modifica dopo l'avviso del coordinatore); prima dell'avviso i comandi `dnf` e la compilazione erano su `rx-kde` (verificato dopo con `rpm -q labwc weston patch`). Lo script `accendi` in modo virtuale ha risposto «another vm-radeon.sh holds the lock» per qualche decina di secondi più volte (altri agenti), poi è passato.
