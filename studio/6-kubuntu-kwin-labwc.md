# Studio 6 — Kubuntu 26.04: KWin recente dentro labwc, e il «labwc proprio» della 1.5

Agente di studio 6, 18 nov 2026. Solo studio: nessun codice scritto, nessuna prova del prodotto.
Legenda: **[V]** verificato (dove), **[W]** dal web (dichiarato), **[S]** supposizione/ragionamento.
Fatti su Ubuntu 26.04 («resolute») presi in un contenitore usa-e-getta `studio-6` sul server (immagine `ubuntu:26.04`,
`deb-src` abilitato, `apt-get source` di kwin 4:6.6.7, wlroots 0.19.2-1, labwc 0.9.3-1; pacchetti scaricati e aperti con
`dpkg-deb -x`). I file grezzi stanno in `/media/REMOTIX-UBUNTU/studio/6/` (src/, dl/x/, up/, s1.out, s2.out).
Percorsi: `D:` = `/home/nicfio/Documenti/REMOTIX-DEBIAN`, `V:` = `/home/nicfio/Documenti/REMOTIX` (vecchio albero 1.5.x).

## 0. Risposta breve alla domanda chiave

**Il labwc di Ubuntu 26.04 NON basta: serve di nuovo il labwc proprio (con wlroots 0.19.2 corretto dalla patch).**
Grado di certezza: **alto (circa 90-95 %)**. Motivi, tutti verificati:

1. Il labwc di Ubuntu è **0.9.3-1** e usa la **libwlroots-0.19 di sistema, 0.19.2-1** [V `apt-cache`, `labwc.dsc`: Depends `libwlroots-0.19`;
   `meson.build:53` `dependency('wlroots-0.19')`]: sono **le stesse identiche versioni** che la 1.5 compilava (labwc 0.9.3 + wlroots 0.19.2),
   ma senza la patch e in dinamico.
2. Il sorgente wlroots di Ubuntu **non contiene la correzione**: `types/scene/surface.c` di Ubuntu è **byte per byte uguale** a quello del
   tarball upstream 0.19.2 (`diff` vuoto, [V]); l'unica patch Debian/Ubuntu è `Revert-layer-shell-error-on-0-dimension-without-anchors`
   (tocca solo `types/wlr_layer_shell_v1.c`, irrilevante: il nostro layer ha dimensione 1x1) [V `debian/patches/series`].
   La patch REMOTIX per 0.19.2 si applica pulita al sorgente Ubuntu (`patch --dry-run`: «checking file types/scene/surface.c», nessun rifiuto) [V].
3. **Upstream non l'ha corretto**: `types/scene/surface.c` di wlroots **master** e **0.20.0** ha ancora `handle_scene_buffer_frame_done` senza
   alcuna chiamata di presentation (scaricato oggi da gitlab.freedesktop.org, [V] file in `up/surface-master.c`); `wlr_presentation_time.c`
   cambia solo nel campo `refresh`. Il difetto lato KWin è in `master`, `Plasma/6.7` e `Plasma/6.6`: `frameDiscarded()` fa solo
   `m_frames.pop_front()` [V `up/kwin-wo-*.cpp`]. Segnalazioni wlroots aperte e correlate: #4003 «Firefox under nested kwin_wayland causes screen
   updates to block» (aperta da luglio 2025) e #4133 «scene: no frame callbacks for a surface covered by its own subsurface» (aperta il 22 ott 2026,
   stesso tipo di causa: radice 1x1 coperta da subsurface) [W/V via API gitlab]. Nessuna MR di correzione trovata.
4. Il sintomo fu **osservato in banco proprio su Ubuntu 26.04 con il labwc della distribuzione**: `V:CHANGES-1.5.md:46` «On Ubuntu 26.04, Fedora 44,
   RHEL/Alma 10, Tumbleweed and Arch the windows of a KDE session stayed on their first frame (28 tests blocked) and the picture came 1-3 s late».
   Ubuntu 26.04 ha ancora il labwc 0.9.3 e il wlroots 0.19.2 di allora e kwin è passato da 6.6.6 a 6.6.7 (stessa struttura del backend).

Cosa resta incerto (5-10 %): la **catena causale esatta** è ricostruita dalla lettura del codice (sezione 2), non osservata con un tracciamento nuovo;
e nessuno ha provato 6.6.7 col labwc di Ubuntu da quando esce 6.6.7. **Prova che la confermerebbe** (non eseguita: le regole vietano di lanciare prove):
dentro un contenitore/VM con GPU o llvmpipe, avviare `labwc` di Ubuntu in headless e `kwin_wayland --wayland-display …` annidato con
`WAYLAND_DEBUG=1` sul lato KWin, e contare gli eventi `wp_presentation_feedback.presented` contro `.discarded`: col labwc di Ubuntu ci si aspetta
quasi solo `discarded` (e frame callback ai client con tempo 0); col labwc proprio ci si aspetta `presented` a ogni frame. Poi Firefox/Chrome dentro la sessione.

## 1. Come REMOTIX fa girare KDE oggi (Debian 13, 1.0.0) — architettura

[V] da `D:src/kwin.h` (intestazione), `D:src/kwin.c`, `D:src/session.c`, `D:debian/*`. Il codice KDE è **identico** a quello del vecchio albero
(vedi sezione 6), tranne il percorso labwc.

**Chi cattura che cosa, da quale compositore, con quale protocollo**

| Funzione | Compositore | Protocollo / canale | Dove |
|---|---|---|---|
| Schermo | KWin (annidato) | `zkde_screencast_unstable_v1` (Wayland) sull'uscita `WL-0` (annidato; `Virtual-0` con `--virtual`) → risposta: numero di nodo PipeWire → `capture_start(node)` (da qui la strada è quella di GNOME) | `kwin.c` `kwin_open()`, `kwin.h` |
| Cursore | KWin | modo `POINTER_METADATA=4` (cursore come metadato, lo disegna la pagina) | `kwin.c:~44` |
| Tastiera/mouse (input) | KWin | `org.kde.KWin.EIS.RemoteDesktop.connectToEIS(7)` → descriptor libei (come Mutter) | `kwin.c` `kwin_eis_fd()` |
| Appunti | KWin | `ext_data_control_manager_v1` (o `zwlr_data_control_manager_v1` se c'è) sul socket `wayland-N` di KWin | `clipboard_kde.c` |
| Dimensione del desktop al reattach | **labwc (host)** | `zwlr_output_manager_v1` cambia l'uscita di labwc → la finestra a tutto schermo di KWin si ridimensiona → `WaylandOutput::resize()` di KWin | `kwin.c` `kwin_host_resize()`, `kwin_host_settle()` |
| Layout tastiera | KWin | `kxkbrc` nella cartella di sessione + segnali D-Bus `org.kde.keyboard /Layouts reloadConfig` e `org.kde.kconfig.notify ConfigChanged /kxkbrc` | `kwin.c:~900-960` `kwin_layout()` |
| Permesso | — | `/usr/share/applications/org.kde.remotix.desktop` con `Exec=/usr/libexec/remotix/remotix` e `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1`: KWin annuncia il global screencast solo a un client il cui `/proc/<pid>/exe` è nell'`Exec=` di un `.desktop` che lo dichiara | `D:debian/org.kde.remotix.desktop`, `kwin_check_permission()` |

**Perché KWin è annidato in labwc.** KWin `--virtual` (fino a 6.7) non può cambiare la dimensione dell'uscita né crearne una seconda, e riavviare KWin
uccide i programmi non-Qt (`kwin.h`, §10.40 di DECISIONS). Quindi KWin nasce **annidato** (`--wayland-display`) come finestra a tutto schermo dentro un
labwc **senza schermo** (backend `headless`) in una cartella propria; cambiare la dimensione dell'uscita di labwc ridimensiona il desktop senza riavviare nulla.

**Come parte.** Il drop-in `plasma-kwin_wayland.service.d/zz-remotix-monitor.conf` (`session.c:2909 write_dropin()`, `kdehost.h`) sostituisce l'`ExecStart` di
`/usr/lib/systemd/user/plasma-kwin_wayland.service` (di Ubuntu: `ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland`, `BusName=org.kde.KWinWrapper`
[V dal pacchetto kwin-wayland 6.6.7]) con `remotix --kwin-nested W H NODE -- kwin_wayland_wrapper …` (`kwin.c:1295-1450 kwin_nested_alive()`):
1. sceglie il labwc: **oggi** `g_find_program_in_path("labwc")` (`D:kwin.c:1314-1318`); se non c'è, ripiega su KWin `--virtual` dichiarato;
2. scrive un `rc.xml` proprio (`HOST_RC`: ogni finestra a tutto schermo con regola sul **titolo**, nessuna decorazione, **zero binding** di tasti/mouse: un binding con azione `None`
   per tipo; senza questo labwc carica quelli predefiniti che avviano programmi, §10.43) e lo passa con `-C`;
3. fork/exec di labwc con `XDG_RUNTIME_DIR=<runtime>/remotix-kwin-host`, `WLR_BACKENDS=headless`, `WLR_LIBINPUT_NO_DEVICES=1`, `LABWC_UPDATE_ACTIVATION_ENV=0`,
   `WLR_RENDERER=pixman` o `WLR_RENDER_DRM_DEVICE=<nodo>`; frequenza dell'uscita 240 Hz (`HOST_MHZ`, per non perdere fotogrammi con KWin a 60);
4. un «ticker»: processo a parte (doppio fork) che tiene su labwc una superficie layer-shell 1x1 trasparente e fa commit a orologio (`TICKER_MS`), perché labwc ridisegna solo
   se c'è danno e KWin disegna solo quando labwc ha ridisegnato (`kwin.c:~1170-1260`);
5. fa `execvp` del wrapper di KWin con `--wayland-display <socket host>`.

Il guscio del servizio è fermato da `kdehost.h` (riconosce il processo dalla riga di comando `remotix-kwin-host`/`--kwin-nested`, mai per nome).
`debian/control` D: `Recommends: …, labwc, wlr-randr, xwayland, fonts-dejavu-core` (riga 99; labwc anche per KDE, commento righe 82-86).
Non c'è nulla di `kwin_x11`: REMOTIX usa solo `startplasma-wayland`.

## 2. Il guaio storico con KWin ≥ 6.5 e la causa esatta

**Sintomo** [V `V:CHANGES-1.5.md:46`, `V:DECISIONS.md:6862` §10.43 (testata aggiornata), `V:packaging/labwc-ospite/README`]: con KWin ≥ 6.5 le finestre di una sessione KDE
restano al primo fotogramma, l'immagine arriva con 1-3 s di ritardo, Firefox crede la finestra coperta e smette di dipingere; 28 test bloccati. Debian 13 (KWin 6.3.6) e Leap 16 (KWin 6.4.2) non ne soffrono.

**Causa, ricostruita sul codice vero (kwin 6.6.7 di Ubuntu, wlroots 0.19.2 di Ubuntu, labwc 0.9.3 di Ubuntu)**

*Lato KWin* — `src/backends/wayland/wayland_output.cpp` [V]:
- Dal 6.5 il backend Wayland annidato di KWin cambiò struttura (commit «backends/wayland: make the primary layer a subsurface», 5 ago 2025 [V API invent.kde.org]):
  la superficie radice `m_surface` della finestra di KWin riceve **un solo pixel nero** (`wp_single_pixel_buffer_manager_v1_create_u32_rgba_buffer(0,0,0,0xFFFFFFFF)`, righe 309-312; scalato con viewport
  alla dimensione dell'uscita) e il contenuto vero sta in **subsurface** (`WaylandLayer`) sopra di essa. In 6.3/6.4 non c'era `singlePixel` [V `up/kwo-Plasma_6.3/6.4.cpp`: 0 occorrenze; 6.5: 1].
- In `present()` (righe 297-336) KWin chiede **il feedback di presentazione sulla radice**: `wp_presentation_feedback(presentationTime, *m_surface)` e `wl_surface_frame(*m_surface)`, poi fa commit della radice.
- `handlePresented` → `framePresented()` → `frame.outputFrame->presented(timestamp)`: **solo qui** il `RenderLoop` di KWin avanza (`lastPresentationTimestamp`, `notifyFrameCompleted`, `renderloop.cpp:130-172`) e KWin consegna ai suoi client i frame callback con quel tempo
  (`workspacescene.cpp:508` `frameTime = renderLoop()->lastPresentationTimestamp()`).
- `handleDiscarded` → `frameDiscarded()` fa **soltanto `m_frames.pop_front()`**: nessun `presented`. Con il feedback sempre scartato il tempo dei client resta a 0 e il ciclo di render non avanza correttamente.

*Lato wlroots* — `types/wlr_presentation_time.c`, `types/scene/surface.c`, `types/scene/wlr_scene.c` 0.19.2 [V]:
- Il feedback di una superficie vive in `p_surface->current.feedback` (preso a ogni commit). Passa «in coda» sull'uscita **solo** quando qualcuno chiama
  `wlr_presentation_surface_textured_on_output()` / `…scanned_out_on_output()` → `presentation_surface_queued_on_output()`, che lo prende con `wlr_presentation_surface_sampled()`, lo lega
  agli eventi commit/present/destroy dell'uscita e, al `present` successivo con lo stesso `commit_seq`, manda `presented`. Se invece il feedback resta lì e arriva un nuovo commit, o
  la superficie muore, `wlr_presentation_feedback_destroy()` manda **`discarded`**.
- In `wlr_scene` quella chiamata è fatta **solo** da `handle_scene_buffer_output_sample` (`surface.c:49-61`), cioè quando il nodo buffer viene **davvero campionato** nel render pass
  (`wlr_scene.c:1453-1457` render; `1981-1985` scanout). Un nodo la cui regione `visible` è vuota perché coperto da subsurface opache viene saltato (culling, `wlr_scene.c:~2260`) e **non genera `output_sample`**.
- La radice 1x1 nera di KWin è interamente coperta dalle subsurface opache ⇒ mai campionata ⇒ il suo feedback non entra mai in coda ⇒ **ogni feedback di KWin torna `discarded`**. (`[S]`: la copertura totale è
  dedotta dalla struttura di KWin 6.5+ e dal fatto che la patch, che non la tocca, la cura; non è stata osservata con un log.)
- Effetto collaterale analogo (nota, non toccato dalla patch): `wlr_scene_buffer_send_frame_done()` non emette nulla per un nodo con `visible` vuoto (`wlr_scene.c:1073-1076`) e la radice coperta non ha `primary_output`
  (`update_node_update_outputs`, `wlr_scene.c:~423-500`) ⇒ il `wl_surface_frame` della radice di KWin non scatta mai. In KWin serve solo a stimare il margine di sicurezza (`frameCallbackTime`), per questo non blocca. È lo stesso difetto dell'issue wlroots #4133 (Chromium).
- In **labwc 0.9.3** non c'è codice che interferisca: `src/output.c:160-162` fa `lab_wlr_scene_output_commit()` e **poi** `wlr_scene_output_send_frame_done()`; `presentation` compare solo in `server.c:641` (creazione) e `tearing.c` [V].

**Perché Firefox si ferma:** KWin consegna a Firefox frame callback col tempo 0 / non avanzato; Firefox lo interpreta come finestra occlusa e smette di dipingere (descrizione in commento della patch; `[W-interno]` dal vecchio albero; coerente con l'issue #4003).

### La patch, riga per riga (`V:packaging/labwc-ospite/wlroots-0.19.2-remotix-presented-root.patch`)

File `types/scene/surface.c`, funzione `handle_scene_buffer_frame_done(listener, data)` (listener `frame_done` di ogni `wlr_scene_surface`, invocato da `wlr_scene_output_send_frame_done()` per ogni nodo buffer
con `primary_output == questa uscita` e `visible` non vuota, cioè per **ogni subsurface visibile** di KWin). Prima: solo `wlr_surface_send_frame_done(surface->surface, now)`. La patch aggiunge, prima di quella riga:

```c
if (surface->buffer->primary_output != NULL) {
    wlr_presentation_surface_textured_on_output(
        wlr_surface_get_root_surface(surface->surface),
        surface->buffer->primary_output->output);
}
```
- `surface->buffer->primary_output != NULL`: guardia (per costruzione è vero quando questo handler scatta; serve per poter dereferenziare `->output`).
- `wlr_surface_get_root_surface(surface->surface)`: risale dalla subsurface alla **superficie radice** (quella di KWin, per cui KWin ha chiesto il feedback).
- `wlr_presentation_surface_textured_on_output(radice, uscita)`: mette in coda il feedback **corrente della radice** sull'uscita, come se la radice fosse stata campionata. Alla prima subsurface del frame prende il feedback;
  alle successive `wlr_presentation_surface_sampled()` restituisce NULL (già preso) e non fa nulla. Per superfici normali già campionate è un no-op.
- Poi, come prima, `wlr_surface_send_frame_done(...)`.
- Il feedback così accodato viene legato al **commit successivo** dell'uscita (`feedback_handle_output_commit`: `output_committed` si imposta al prossimo commit): infatti labwc fa commit e *poi* `send_frame_done`, quindi la patch riporta un `presented` con un frame di ritardo; con host a 240 Hz è trascurabile. `[S]`
- Versioni: 0.18 e 0.20 hanno patch gemelle in `patches-upstream/` (in 0.20 l'handler riceve `event->output` e la chiamata è `wlr_presentation_surface_textured_on_output(wlr_surface_get_root_surface(surface->surface), event->output->output)` dopo il controllo del *frame pacing output*).

### Perché la cura fu un labwc proprio statico (`V:packaging/labwc-ospite/README`, `VERSIONS`, `build.sh`)
Il difetto è in **wlroots**, non in labwc e non in KWin; wlroots è una libreria di sistema con ABI diversa a ogni serie (0.18/0.19/0.20) e le distribuzioni non applicano la patch. Per non dipendere dal wlroots di ogni distro la 1.5 compilava
**labwc 0.9.3 + wlroots 0.19.2 patchato, collegato staticamente** (`subprojects/wlroots`, `-Dwlroots:default_library=static`), installato come `/usr/lib/remotix/labwc`, usato **solo** per KDE (`make LABWC=/usr/lib/remotix/labwc` → `-DREMOTIX_LABWC`);
XFCE e LXQt tengono il labwc della distribuzione. Prima (11 ott 2026, §10.43) c'era un labwc 0.8.4 **non** patchato per Alma 10 (non servì: fu sostituito il 28 ott).

## 3. Ubuntu 26.04 vero: i pacchetti [V tutto da `apt-cache`/`apt-get` nel contenitore]

| Pacchetto | Versione in 26.04 (resolute) | Note |
|---|---|---|
| `kwin-wayland` | **4:6.6.7-0ubuntu0.1** (resolute-updates; 6.6.4-0ubuntu1 in release) | Depends `xwayland`, `libcap2-bin`; postinst fa `setcap CAP_SYS_NICE=+ep` su `kwin_wayland`; unità `plasma-kwin_wayland.service` |
| `kwin-x11` | 4:6.6.4-0ubuntu1 | esiste ma **non** è nelle dipendenze di `kubuntu-desktop` |
| `plasma-workspace` | 4:6.6.7-0ubuntu0.1 | porta `plasma-workspace.target`, `plasma-ksmserver.service`, … |
| `plasma-desktop` / `-data` | 4:6.6.7-0ubuntu0.1 | |
| `plasma-session-wayland` | (6.6.x) | **`/usr/share/wayland-sessions/plasma.desktop`**: `Exec=/usr/lib/x86_64-linux-gnu/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland`, `DesktopNames=KDE`, `Name=Plasma (Wayland)` |
| `plasma-session-x11` | esiste in archivio, **non** installato da `kubuntu-desktop` | quindi su Kubuntu predefinita non c'è `xsessions/plasma.desktop`; X11 resta come opzione, Wayland è la sessione di default |
| `labwc` | **0.9.3-1** (universe) | Depends `libwlroots-0.19`, `xwayland`, librsvg, libsfdo, … |
| `libwlroots-0.19` | **0.19.2-1** (sorgente `wlroots`), **nessun `libwlroots-0.20`** in archivio | solo la serie 0.19 |
| `sddm` | **0.21.0+git20250502.4fe234b-2ubuntu3** | `kubuntu-desktop` Depends `sddm`; **`plasma-login-manager` non esiste in archivio** (`apt-cache` vuoto) |
| `kubuntu-desktop` | 1.496 | Depends `kwin-wayland`, `plasma-desktop`, `plasma-workspace`, `plasma-session-wayland`, `sddm`, `kubuntu-settings-desktop`, `xdg-desktop-portal-kde`, `pipewire`, … (**non** `labwc`, **non** `kwin-x11`) |
| `kubuntu-settings-desktop` | 1:26.04.13 | vedi sotto |
| `libpam-kwallet5` / `-common` | 4:6.6.4-0ubuntu1 | `pam_kwallet5.so`; `plasma-kwallet-pam.service` |

**sddm e sessione predefinita** [V file del pacchetto]: `/etc/sddm.conf.d/10-wayland.conf` (`DisplayServer=wayland`, `CompositorCommand=kwin_wayland --drm --no-lockscreen --no-global-shortcuts --locale1`, `GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell`) e
`/etc/sddm.conf.d/20-kubuntu.conf` (`[Autologin] Session=plasma`, `Relogin=false`, tema `kubuntu`, `MinimumUid=1000`). **Nota:** sono in `/etc/sddm.conf.d`, non in `/usr/lib/sddm/sddm.conf.d` (la cartella di `/usr/lib` del brief non esiste in questo pacchetto);
il lettore `declared_sessions()` di `D:session.c` legge entrambe le cartelle (`sddm_dirs`), quindi vale (serve solo se più desktop sono installati). Il greeter di sddm gira come utente `sddm` con un **proprio** `kwin_wayland --drm` (bus e uid diversi dall'utente remoto).
`/usr/share/sddm/scripts/wayland-session` (lancio locale, solo `$SHELL --login`/`/etc/profile`, **non** esegue `Xsession.d`) [V].

X11 presente? Xwayland sì (dipendenza di kwin-wayland e di labwc); sessione X11 di Plasma solo se si installa `plasma-session-x11`.

## 4. Sviluppo parallelo di versioni (utile a capire «quanto dura» il problema)
Plasma upstream oggi: 6.8.3 (10 nov 2026), 6.7.6, … [W API invent]. Ubuntu 26.04 resta su 6.6.x con SRU. `frameDiscarded` è uguale in 6.6, 6.7 e master [V]: il problema **non sparirà con un KWin più nuovo**; l'unica cura robusta è lato compositore host.

## 5. Che cosa richiede costruire il labwc proprio su Ubuntu 26.04 (solo i requisiti; il resto è dell'agente 8)

Dal vecchio albero [V `V:packaging/labwc-ospite/{VERSIONS,fetch.sh,build.sh}`, `V:packaging/debian/rules:25-90`, `V:src/build-targets/build-deb.sh:60-80`]:
- Sorgenti fissati con sha256 in `VERSIONS`: `labwc-0.9.3.tar.gz` (archivio GitHub del tag, `38d273fa…126`; non c'è tarball firmato), `wlroots-0.19.2.tar.gz` (rilascio ufficiale gitlab, `09a0a8d6…267`). `fetch.sh` li scarica e li verifica; `build.sh` li ricontrolla.
  Il pacchetto non può scaricare durante la costruzione: i tarball vanno messi in `labwc-ospite/sources` dal costruttore (`build-deb.sh`).
- `build.sh`: toglie i `.wrap` upstream, scrive un wrap proprio (`wlroots-0.19` → cartella `subprojects/wlroots`), applica la patch, meson con
  `-Dxwayland=disabled -Dsvg=disabled -Dicon=disabled -Dnls=disabled -Dman-pages=disabled -Dwlroots:default_library=static -Dwlroots:backends=drm,libinput -Dwlroots:renderers=gles2 -Dwlroots:allocators=gbm -Dwlroots:session=enabled -Dwlroots:libliftoff=disabled -Dwlroots:color-management=disabled -Dwerror=false -Dwlroots:werror=false`.
  `werror=false` serve davvero su 26.04: libinput nuovo (`LIBINPUT_SWITCH_KEYPAD_SLIDE` non gestito) fermerebbe wlroots 0.19.2 compilato con `-Werror`. `[S]`: il renderer pixman è sempre incluso in wlroots (kwin.c usa `WLR_RENDERER=pixman` per `node=pixman`); da verificare nel binario.
- Il controllo finale: `ldd labwc` non deve nominare nessuna libwlroots (mai il wlroots di sistema).
- Build-Depends aggiunti per ubuntu2604 (verificati allora): `meson, patch, hwdata, wayland-protocols, libegl-dev, libgles-dev, libinput-dev, libpixman-1-dev, libseat-dev, libudev-dev, libdisplay-info-dev, libxml2-dev, libcairo2-dev, libpango1.0-dev, libpng-dev` (più quelli già di REMOTIX: libdrm, libgbm, vulkan…).
  Confronto con i veri `Build-Depends` del `.dsc` di Ubuntu (labwc: cmake gettext libcairo2-dev libdrm-dev libglib2.0-dev libinput-dev liblzma-dev libpango1.0-dev libpng-dev librsvg2-dev libsfdo-dev libxkbcommon-dev libxml2-dev meson scdoc wayland-protocols xwayland; wlroots: glslang-tools hwdata libcap-dev libdisplay-info-dev libegl-dev libgbm-dev libgles2-mesa-dev libliftoff-dev liblcms2-dev libseat-dev libsystemd-dev libvulkan-dev libx11-xcb-dev libxcb-* … ) [V `.dsc`]:
  `[S]` Per la build con `-Dsvg/icon/nls/man-pages=disabled` probabilmente servono meno pacchetti di quelli dell'elenco Ubuntu (niente `librsvg`, `libsfdo`, `scdoc`, `gettext`); la lista minima va ricalcolata provando su 26.04 (`libglib2.0-dev` e `libxkbcommon-dev` servono comunque a labwc).
- `debian/rules` (vecchio): variabile `REMOTIX_LABWC_OSPITE` decisa da `dpkg-vendor --is Ubuntu` e `VERSION_ID >= 26.04` (override da ambiente); se 1 → esegue `build.sh` con `BUILD_DIR=debian/labwc-build`, poi `make -C src all … LABWC=/usr/lib/remotix/labwc`, poi installa `debian/labwc-root/usr/lib/remotix/labwc` in `/usr/lib/remotix/labwc`.
- `Makefile`: `LABWC ?=`; `ifneq ($(LABWC),)` → `override CFLAGS += -DREMOTIX_LABWC='"$(LABWC)"'` (`V:src/Makefile:127-135`; ricordare `make clean`).
- `kwin.c`: i due `#ifdef REMOTIX_LABWC` (percorso scelto con `access(X_OK)`; `execl(labwc_path,…)`); se il file manca ripiega su `--virtual` dichiarato **senza** ricadere sul labwc di sistema (giusto: quello ricadrebbe nel difetto).
- Il pacchetto binario risultò (banco) con `/usr/lib/remotix/labwc` di 1 456 680 byte; le dipendenze di libreria le calcola `dh_shlibdeps`.
- Il pacchetto Ubuntu **continua a raccomandare `labwc`** (serve a XFCE/LXQt e al ripiego su un solo pacchetto): su Kubuntu resterà installato ma **non usato** (così nel banco: «labwc 0.9.3 della distro installato ma non usato», `V:assessment/kde/ubuntu2604.md`, R-DE-038).

**Alternativa non provata [S]:** invece del labwc statico, ricompilare solo la libwlroots 0.19.2 (dal sorgente Ubuntu + patch) in una cartella privata e avviare il labwc di Ubuntu con `LD_LIBRARY_PATH` (stesso ABI, stesso SONAME). Evita di compilare labwc ma richiede che il labwc di distro e la libreria restino in ABI-sync a ogni aggiornamento Ubuntu, e `LD_LIBRARY_PATH` nell'ambiente dell'exec. La strada statica è invece **già provata su 26.04** (banco 1.5.5): consiglio di riusarla.

## 6. Gli altri tre difetti KDE di KWin 6.6 e se la cura c'è ancora

Confronto con `diff` tra `V:src/` e `D:src/` sulle zone KDE [V]:

| File | Differenze |
|---|---|
| `kdehost.h` | **0** righe |
| `clipboard_kde.c` | **0** righe |
| `capture.c`, `capture.h` | **0** righe |
| `kwin.c` | 36 righe: (a) tolti i due `#ifdef REMOTIX_LABWC` e il commento (righe 1314-1324, 1385-1387 vecchie); (b) tre messaggi `RX-KDE-001` «reinstall REMOTIX with the installer» → «reinstall the package (apt install --reinstall remotix)»; (c) un `⛔` → `⚠` in un messaggio (riga 1639). Nient'altro |
| `Makefile` | tolto il pezzo `LABWC` (e i target bench) |
| `session.c` | 367 righe: tolti nomi Ubuntu/Kubuntu in `desktop_of_session_name()` (`strstr(n,"kubuntu")`, `xubuntu`, `lubuntu`, `ubuntu`), `local_session_name_find()`/`xsession_d_applies()`/`session_folder_there()` (D-153), ramo GNOME 50; **aggiunto** il 17 nov `session_kde_logout_watch()` (vedi 8). Nessuna parte KDE di avvio è stata tolta |
| `child.c` | solo commenti/glifi e la chiamata a `session_kde_logout_watch()` (aggiunta 17 nov) |

1. **Appunti `ext_data_control`** — cura presente: `D:clipboard_kde.c:~325` `bind_ext_if_needed()` + `on_global` (righe ~300-330): se `zwlr_data_control_manager_v1` manca lega `ext_data_control_manager_v1` (versione 1) e lo pilota con le funzioni zwlr (stessi opcode e firme; i figli nascono da `new_id`). È una **sonda a runtime** senza test di versione.
   Verificato su KWin 6.6.7 di Ubuntu: `src/wayland/datacontroldevicemanager_v1.cpp:18` implementa solo `ext_data_control_manager_v1` (nessun `zwlr`) [V]. Cura intatta.
2. **Layout di tastiera F-009** — cura presente: `D:kwin.c:~900-960` `kwin_layout()` scrive `kxkbrc` e manda **due** segnali: `org.kde.keyboard /Layouts reloadConfig` (KWin ≤ 6.3) e `org.kde.kconfig.notify ConfigChanged` su `/kxkbrc` con gruppo `Layout` e chiavi `LayoutList`/`VariantList` (KWin ≥ 6.6).
   Verificato in 6.6.7: `src/keyboard_layout.cpp:29,63,105-107` usa `KConfigWatcher` e `handleXkbConfigChanged` per il gruppo `Layout`; `reloadConfig` su `org.kde.keyboard` non compare in KWin 6.6.7 [V]. Cura intatta.
3. **Frame vuoti saltati nella cattura** — cura presente: `D:capture.c:888-1082` `damage_classify()` (`SPA_META_VideoDamage` presente ma vuoto = «nessun cambiamento», righe 946-958 `tally.empty_damage`) e la saltata a 1072-1082 salvo `deliver_next` / `damage_lost`. Il danno richiesto a PipeWire è alla riga 671. 5 fotogrammi/s invece di 53 su schermo fermo. `capture.c` è identico al vecchio [V].
   Questa non è specifica di Ubuntu né di KDE come distribuzione: dipende da come KWin ≥ 6.6 riempie il metadato.

**Conclusione:** dopo la pulizia del 17 nov la cura dei tre difetti c'è **tutta**; è stato tolto soltanto il labwc proprio (e le stringhe Ubuntu di `session.c`, irrilevanti qui perché la sessione Kubuntu si chiama `plasma`, non `kubuntu`). `INVENTARIO-non-debian.md:36` e `PULIZIA-tranche1.md:52` confermano: le sonde sono volutamente senza test di versione.

## 7. Licenza: che cosa comporta allegare labwc e wlroots

Come la dichiarava la 1.5 [V `V:THIRD-PARTY-LICENSES:1237-1262`, `1605`, `V:LICENSE.md:93-101`, `V:packaging/labwc-ospite/README`, `V:packaging/release.sh:170-180`]:
- **labwc**: GPL-2.0-only (due file LGPL-2.0-or-later: `src/img/img-xpm.c`, `src/common/xcolor-table.h`). **wlroots**: MIT (la patch REMOTIX è sua modifica MIT). Il binario li contiene entrambi (wlroots statico).
- labwc è un **programma separato**, non collegato a REMOTIX (REMOTIX lo avvia con exec): la licenza di REMOTIX (LICENSE.md, che vieta modifica e ridistribuzione, §3) **non si applica** al labwc; chi lo riceve ha i diritti GPL-2.0.
- Obblighi pratici: testo completo GPL-2.0 (e LGPL-2.1 per i due file, già nel file come testo delle proiezioni dei protocolli) in `THIRD-PARTY-LICENSES` (installato in `/usr/share/doc/remotix/`); testo MIT di wlroots; **sorgente corrispondente completo**: i due tarball upstream non modificati, la patch e la ricetta (`labwc-ospite/`) pubblicati con ogni rilascio, dentro il `.run` (`source/labwc/`) e accanto (`remotix-<versione>-labwc-source.tar.gz` + sha256). Nel pacchetto `.deb` per un'archivio Ubuntu/Debian il sorgente accompagna il pacchetto sorgente.
- Stato nel **nuovo albero Debian** `D:`: `THIRD-PARTY-LICENSES` contiene ancora (identico) l'elenco e il testo «Ubuntu 26.04 / Fedora 44 / Alma 10 / Tumbleweed / Arch» per labwc 0.9.3 e wlroots 0.19.2 (il file non è stato ripulito) — quindi i testi sono **già pronti**, ma il file dice «Fedora/Alma/…» e va riscritto per la sola Ubuntu.
  `D:LICENSE.md:95-101` è **sbagliato/obsoleto**: parla del «pacchetto per RHEL / AlmaLinux 10» e dice che il sorgente è «the upstream release tarball, **unmodified**» — falso con la patch (e già incoerente con `THIRD-PARTY-LICENSES:1245`, che dice «labwc … unmodified (its wlroots carries a small patch of ours)»). Da correggere: «Ubuntu 26.04 (Kubuntu)», patch inclusa, nominare wlroots MIT.
  `D:debian/copyright` rimanda a `THIRD-PARTY-LICENSES` e aggiunge `LICENSE.md` in coda (la build lo fa in `build-deb.sh`); occorrerà un paragrafo per labwc/wlroots (DEP-5).
- Se un giorno il pacchetto andasse in un archivio ufficiale Ubuntu: la patch e un labwc incluso statico si scontrerebbero con la politica di non incorporare librerie di sistema (copie «embedded»); non è lo scenario attuale.
- Dovere di manutenzione (regola §10.43, punto 3): un avviso di sicurezza serio su labwc o wlroots 0.19 obbliga a un rilascio straordinario; **Ubuntu non lo corregge più nella copia statica**. L'esposizione è limitata: labwc gira headless, senza rete (`V:DECISIONS.md` §10.43: nessun AF_INET, nessun dlopen, nessun setuid, non scrive su disco), ma gli input arrivano dal protocollo Wayland dal solo utente.

## 8. Logout KDE, kwallet, plasmalogin

- **Logout** (`D:session.c:4179-4300`, correzione del 17 nov, **assente nel vecchio albero**): `plasma-shutdown` (`org.kde.Shutdown`, quello che chiama «Log Out») ferma `plasma-workspace.target` e poi chiede a systemd utente di fermare `graphical-session.target`;
  se un'unità ha un job di avvio in coda («Transaction … is destructive») plasma-shutdown ignora il rifiuto ed esce, e KWin/plasmashell restano su. La cura: `session_kde_logout_watch()` vede `plasma-workspace.target` prima attivo poi non attivo mentre `org.kde.KWin` è ancora sul bus; dopo `KDE_LOGOUT_GRACE_MS=4000` richiede
  `StopUnit(graphical-session.target, "fail")` ogni `KDE_LOGOUT_RETRY_MS=3000`, al più 10 volte; poi segue la strada normale §7.6. Il logout ordinato usa `org.kde.Shutdown.logout()` e il forzato `StopUnit("plasma-workspace.target","fail")` (`session.c:3641-3666`).
  Il vecchio banco su Ubuntu 26.04 aveva **la stessa anomalia di Debian**: `R-DE-051 DA DECIDERE` — Log Out → 0x10, dopo 20 s restano 11 processi di prova e `/run/user/1001` (`V:assessment/kde/ubuntu2604.md`); la cura del 17 nov nasce su Debian: **da riprovare su Kubuntu** (systemd e plasma-workspace diversi).
  Nota: l'unità di Ubuntu `plasma-workspace.target` e `plasma-kwin_wayland.service` hanno gli stessi nomi usati dal codice (`SESSION_UNIT_PLASMA`) [V: file dei pacchetti 6.6.7].
- **kwallet** [V]: `/etc/pam.d/sddm` di Ubuntu ha `-auth optional pam_kwallet5.so` e `-session optional pam_kwallet5.so auto_start` (e gnome-keyring). Il servizio PAM **`remotix`** (`D:src/remotix.pam`) **non** li ha: né `common-auth` li include (solo `pam-auth-update` profili), quindi
  al login remoto il portafoglio **non viene sbloccato**: `plasma-kwallet-pam.service` (`Wants` di `plasma-workspace.target`, `After=plasma-kwin_wayland.service`, esegue `/usr/share/libpam-kwallet-common/pam_kwallet_init`, `libpam-kwallet-common`) parte ma non trova il socket/ambiente PAM `[S]`; la prima app che chiede il portafoglio (browser, Discover, NetworkManager, KDE Connect) vedrà la **finestra «crea/apri portafoglio»** con richiesta di password — in conflitto con la regola della 1.5.3 «nessuna finestra di password non richiesta nelle sessioni remote».
  Nel vecchio albero e in `D:` non c'è né gestione né decisione su kwallet o gnome-keyring (un solo riferimento a «gnome-keyring .scope falliti» in `REGISTRO-priorita.md:58`). **Decisione necessaria** (comportamento uniforme: «remoto = login locale meno i danni del server condiviso»): aggiungere a `/etc/pam.d/remotix` le righe `-auth optional pam_kwallet5.so` / `-session optional pam_kwallet5.so auto_start` (con gnome-keyring per GNOME)? Sbloccherebbe il portafoglio con la password digitata nel browser.
  Il pacchetto `libpam-kwallet5` non è dipendenza di `kubuntu-desktop` (`apt-cache depends`: non compare; `kubuntu-desktop` ha in Recommends altri pezzi) `[V per Depends, S per Recommends]`.
- **plasmalogin**: `plasma-login-manager` (nuovo gestore di accesso KDE) **non è nell'archivio di Ubuntu 26.04** [V]; Kubuntu 26.04 usa **sddm 0.21.0**. Niente da fare ora; guardare Plasma 6.7/6.8 e Ubuntu 26.10.
- **sddm accanto al remoto**: principio «sessione grafica locale attiva ⇒ remoto rifiutato»: il greeter di sddm gira su seat0 come utente `sddm` con un proprio `kwin_wayland`; verificare che non venga scambiato per un desktop di un utente reale (rilevazione tramite logind/uid). `[S]`
- Il `.desktop` di permesso (`org.kde.remotix.desktop`, `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1`) vale ancora in KWin 6.6.7: `src/wayland/screencast_v1.cpp` e `wayland_server.cpp` ne fanno ancora uso [V grep].

## 9. Risultati del vecchio banco su Ubuntu 26.04 KDE (`V:assessment/kde/ubuntu2604.md`, `difformita.md`)
Box `ubuntu2604-kde` (scheda Intel vera), `remotix-1.5.5-0.run` installato come un cliente, deb 1.5.5-0+ubuntu26.04 con unità split, KWin 6.6 annidato nel labwc proprio. Quasi tutto VERDE «come Debian». Righe significative:
- R-DE-038 VERDE: `/usr/lib/remotix/labwc` (1 456 680 byte) è il labwc che ospita KWin (`/proc/<labwc>/maps`); labwc 0.9.3 di distro installato ma non usato.
- R-SESS-069 VERDE: FIT_CANVAS 1280x800 in 297 ms; kwin e plasmashell restano; ritorno 1920x1080 in 83 ms. R-SESS-074 VERDE (`wanted 1280 800`, «by resizing KWin's host (41 ms)»).
- R-CLIP-004/027 VERDE (accenti, €; sessione→client OK).
- R-SESS-058 VERDE: `State=active` (l'anomalia «closing» di Debian/Alma/Leap non si vede su Ubuntu).
- R-DE-051 DA DECIDERE (logout: processi residui, come Debian) — oggi curato su Debian (17 nov), da riprovare.
- R-SEC-035 ROSSO (falso allarme `CanPowerOff=no … (no answer)` per attesa di 300 ms, D10; la protezione vera funziona: pkcheck «Not authorized»). R-SEC-032 VERDE (Ubuntu ha anche `49-ubuntu-admin.rules`, `com.ubuntu.desktop.rules`: non decidono le azioni di spegnimento).
- R-LOGIN-022, R-LOGIN-037 ROSSO (come Debian, generici). R-LIC-006 NON VERIFICATO (sorgente del labwc nel `.run`/accanto non controllato nel box). R-LOGIN-012 DA DECIDERE (rifiuto a 2503 ms).
- Misure del 28-29 ott (server affittato NVIDIA, **non** Intel/Ubuntu): suite KDE Chrome 22/22, Firefox 21/22 (F-013 limite della macchina di prova); suite completa a casa 29 ott: nessuna regressione contro 1.0, 5 migliorate (`CHANGES-1.5.md:46`).
- Difformità: D10 sopra; nessuna difformità KDE-specifica di Ubuntu oltre a quelle.

## Problemi da affrontare

1. **Rimettere il labwc proprio per Kubuntu 26.04** (KWin ≥ 6.5): ripristinare i due `#ifdef REMOTIX_LABWC` in `D:src/kwin.c:1314-1324,1385-1387`, il knob `LABWC` in `D:src/Makefile`, e la cartella `labwc-ospite/` (VERSIONS, fetch.sh, build.sh, patch 0.19.2) — **peso medio**; cura nota **sì**: `V:src/kwin.c`, `V:src/Makefile:127-135`, `V:packaging/labwc-ospite/*`, `V:packaging/debian/rules:25-90`, `V:src/build-targets/build-deb.sh:60-80`.
2. **Costruzione condizionale**: il labwc proprio solo su Ubuntu ≥ 26.04 (criterio `dpkg-vendor` + `VERSION_ID`, override da ambiente); Debian 13 (KWin 6.3) resta com'è; due pacchetti dallo stesso albero — **medio** (agente 8); cura nota **sì**: `REMOTIX_LABWC_OSPITE` nel vecchio `debian/rules`.
3. **Build di labwc+wlroots nel `.deb`**: tarball pinnati e verificati forniti dal costruttore (niente download in `dpkg-buildpackage`), Build-Depends aggiuntivi, `werror=false`, controllo «nessuna libwlroots in `ldd`», dipendenze di libreria calcolate da `dh_shlibdeps` — **medio**; cura nota **sì** (`build.sh`, vedi 5), ma la lista dei Build-Depends va ricontrollata su 26.04.1 con 6.6.7.
4. **Documenti di licenza**: riscrivere `D:LICENSE.md:95-101` (oggi «RHEL/Alma», «unmodified»), rifare l'elenco in `D:THIRD-PARTY-LICENSES` per la sola Ubuntu, paragrafo DEP-5 in `D:debian/copyright`, pubblicare i sorgenti corrispondenti (tarball + patch + ricetta) con ogni rilascio — **piccolo-medio**; cura nota **sì** (`V:LICENSE.md`, `V:THIRD-PARTY-LICENSES`, `V:packaging/release.sh:170-180`).
5. **Manutenzione di sicurezza della copia statica** (regola §10.43 p.3: avviso grave su labwc/wlroots ⇒ rilascio straordinario; rivedere il diff a ogni aggiornamento) — **piccolo** (processo); cura nota **sì** (regola scritta in DECISIONS §10.43). Considerare di segnalare la patch a wlroots (esiste in `patches-upstream/` per 0.18/0.19/0.20; non risulta mai inviata) — decisione dell'utente.
6. **Ritrovare la prova che con il labwc di Ubuntu il difetto c'è e con il proprio no, su KWin 6.6.7** (e con Chrome e Firefox) — **piccolo** ma necessario; cura nota **sì** (banco 1.5.5 su 6.6.6).
7. **Ripiego senza labwc proprio**: se il file `/usr/lib/remotix/labwc` manca il codice va su `--virtual` (desktop senza ridimensionamento al reattach); su Kubuntu è un declassamento ma **non** ricade nel difetto — confermare che sia la scelta voluta — **piccolo**; cura nota **sì**.
8. **Logout KDE su Ubuntu**: la cura del 17 nov (`session_kde_logout_watch`) nasce su Debian/KWin 6.3; sul vecchio banco Ubuntu il logout lasciava 11 processi e `/run/user/…` (R-DE-051) — da riprovare con 6.6.7 e il systemd di 26.04 — **medio**; cura nota **parziale** (solo Debian).
9. **kwallet/gnome-keyring**: il servizio PAM `remotix` non sblocca il portafoglio; comparsa di finestre «portafoglio» in sessione remota — decisione di comportamento uniforme (da portare all'utente) — **medio**; cura nota **no**.
10. **Rilevazione desktop con più desktop installati e nomi di sessione**: la pulizia del 17 nov tolse `kubuntu` da `desktop_of_session_name()`; su Kubuntu il file è `plasma.desktop` quindi basta, ma `declared_sessions()` deve ancora leggere `/etc/sddm.conf.d/20-kubuntu.conf` (lo fa) — **piccolo**; cura nota **sì** (c'è già).
11. **sddm/greeter e «locale esclude remoto»**: verificare che il greeter (utente `sddm`, proprio `kwin_wayland --drm`) non confonda i controlli — **piccolo**; cura nota **no** (non testato).
12. **Capability di KWin** (`setcap CAP_SYS_NICE` dal postinst di `kwin-wayland`): nei contenitori di prova rootless serve `--cap-add=SYS_NICE` (già annotato in DECISIONS §10.43) — **piccolo**.
13. **R-SEC-035 falso allarme (D10)** dell'attesa di 300 ms su Ubuntu e Fedora — non specifico di KDE, già nel registro difformità — **piccolo**; cura nota **no** nel vecchio albero (aperto); verificare se `D:` l'ha ripreso.

## Che cosa non si può sapere senza provare

- Se col labwc di Ubuntu 26.04 e KWin 6.6.7 le finestre restano davvero al primo fotogramma oggi (la causa è letta nel codice; il sintomo fu osservato con 6.6.6).
- Se la copertura totale della radice 1x1 sia davvero la ragione del mancato `output_sample` (conteggio `presented`/`discarded` con `WAYLAND_DEBUG`).
- Se wlroots/labwc di Ubuntu verrà aggiornato (SRU) a una serie che include una cura: oggi non c'è `libwlroots-0.20` e master non ha la correzione.
- Se il pixman renderer è presente nella build statica `-Dwlroots:renderers=gles2` (kwin.c lo usa per `node=pixman`).
- Il comportamento di `pam_kwallet5`/`plasma-kwallet-pam.service` con il servizio PAM `remotix` (e se le finestre del portafoglio compaiono davvero).
- Logout KDE con la cura del 17 nov su systemd 26.04.
- Il ritardo di un frame del `presented` (patch) e l'effetto sulla fluidità a 4K con GPU reali (vecchio banco a 240 Hz: nessun problema notato).

## Prove consigliate

1. **Confronto presentation feedback** (VM o macchina con GPU, 15 min): `labwc` di Ubuntu headless + `kwin_wayland --wayland-display …` annidato con `WAYLAND_DEBUG=1`; contare `presented` vs `discarded`; poi stessa cosa con `/usr/lib/remotix/labwc`. Proverebbe la causa.
2. **Sessione KDE completa su Kubuntu 26.04 (VM)** con il `.deb`: Firefox e Chrome si aggiornano; suite F-003/F-016/F-018 dei vecchi banchi (la sola F-013 è limite della macchina).
3. Costruire il labwc proprio in un contenitore pulito 26.04 con i soli Build-Depends: `ldd`, dimensioni (~1,4 MB), `labwc --version`; `readelf` per i simboli pixman.
4. **Logout**: Log Out da Plasma remoto, attendere 30 s: nessun processo e `/run/user/<uid>` pulito.
5. **kwallet**: avviare un'app che apre il portafoglio dentro la sessione remota, con e senza le righe `pam_kwallet5` in `/etc/pam.d/remotix`.
6. **sddm presente**: sessione remota mentre il greeter è acceso e mentre c'è una sessione locale attiva.
7. Rifare `diff` dei percorsi di sorgente wlroots/kwin se Ubuntu rilascia nuove SRU prima dell'uscita.
