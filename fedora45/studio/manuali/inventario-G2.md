# Inventario G2 — manuale tecnico per Fedora 45, capitoli ch06–ch11 (cattura, codifica, qualità, pagina, input, audio e appunti)

Data: 25 nov 2026. Sola lettura. Base: `ubuntu26.04/manuals/sources/technical-ubuntu26.04/ch06_*.py … ch11_*.py` (già adattati a Ubuntu), confrontati con `fedora45/`.
Metodo: testo di ogni sezione estratto dal `CHAPTER` (tag HTML tolti) e cercato per parole che dipendono dalla distribuzione; `diff -rq ubuntu26.04/src fedora45/src`; diff mirati; `PIANO.md`, `docs/REGISTRO-problemi.md` (F1–F36), `studio/1…5`, `rpm/remotix.spec`.
Numerazione delle sezioni = ordine nel `CHAPTER` (la variabile Python, es. `S4B`, non conta). «Ubuntu» = il manuale Ubuntu attuale.

## Tabella riassuntiva

| Capitolo | Sezioni | Vale com'è | Da correggere | Da riscrivere | Da togliere |
|---|---|---|---|---|---|
| ch06 Screen capture | 12 | 3 | 8 | 1 | 0 |
| ch07 Video encoding | 13 | 6 | 7 | 0 | 0 |
| ch08 Quality, degradation and budget | 14 | 12 | 2 | 0 | 0 |
| ch09 The browser page | 17 | 10 | 7 | 0 | 0 |
| ch10 Input | 17 | 7 | 9 | 1 | 0 |
| ch11 Audio and clipboard | 13 | 7 | 5 | 1 | 0 |
| **Totale G2** | **86** | **45** | **38** | **3** | **0** |

(Ubuntu contava 85 sezioni per G2: qui 86, contando anche la sezione «The lost frame (KWin)» come voce propria. Nessuna sezione intera da togliere: le parti da togliere sono paragrafi, righe di tabella e riquadri dentro sezioni da correggere o da riscrivere.)

## Fatto di base che spiega quasi tutto

`diff -rq ubuntu26.04/src fedora45/src` dice che i file DIVERSI sono soltanto: `child.c`, `input.c`, `kdehost.h`, `kwin.c`, `kwin.h`, `main.c`, `Makefile`, `remotix.pam`, `remotix-remote-sessions.rules`, `session.c`, `transport.c`, `walls.c` (più i nuovi `remotix-pam-hook` e `protocols/kde-output-*`). Sono IDENTICI a Ubuntu: `capture.c`, `mutter.c`, `wlroots.c`, `encoder.c`, `vadirect.c`, `vulkanvideo.c`, `audio.c`, `sound.c`, `clipboard*.c`, `wlr_input.c`, `rcp.c`, `page.c`, `page.html` (`cmp` uguale), `hsrate.h`, `msgrate.h`, `shape.c`, `render_grant.c`, `card_pick.c`. Quindi per ch07–ch11 il codice descritto vale com'è; cambiano versioni, pacchetti, scriptlet, prove e (per KDE) tutto ciò che riguarda l'avvio di KWin. Le differenze di codice che toccano G2:

- **KDE = KWin da solo** (D2, F7, F8, F13, F14): `kwin.c:1696-2212` (nuovo: `kwin_virtual_alive()` riga 1713, `kwin_output_resize()` riga 2053, protocolli `kde_output_device_v2` / `kde_output_management_v2`), `kwin.h:139-155`, `kdehost.h:50-61` (segni `--kwin-virtual` e `REMOTIX_KDE_HOST=1`), `main.c:2886-2892` (`--kwin-virtual`; `--kwin-nested` ora risponde con errore), `session.c:3930-3956` (drop-in `zz-remotix-monitor.conf`: `ExecStart=remotix --kwin-virtual W H -- wrapper --virtual --xwayland --width W --height H …` + `Environment=REMOTIX_KDE_HOST=1`; nessuna scelta di scheda), `child.c` (rifiuto `kde_refused`, riga 5886 di session.c e 8997/9035 di child.c; montaggio dello stage con `kwin_output_resize()`). Codice labwc-per-KDE ancora presente ma morto: `kwin_nested_alive()`, `kwin_host_*`, `ticker_*`, `HOST_RC` (kwin.c:1043-1700, 2256-2404; F7).
- **Chiusura KDE** (F36, 25 nov): `session.c:4590-4609` forzata = `StopUnit("graphical-session.target","fail")`; `session.c:113` `KDE_PRELOCAL_ORDERLY_MS 5000` (solo KDE, solo chiusura per accesso locale; riga 5639); regola SELinux `allow remotix_t xdm_unit_file_t:service { stop status }` in `selinux/remotix.te`.
- **GNOME**: `input.c:257,1330,1940-1951` doppio invio del primo movimento assoluto (`pointer_primed`, F34, mutter 51); `session.c:1843-1906` compilazione del database dconf in `/run/remotix/dconf-compile.tmp` e `/etc/dconf/db/remotix.new` (nomi fissi per SELinux).
- **Lingua/PATH/SELinux del figlio**: `child.c:1590-1720` (`child_locale_read()`, LANG da AccountsService, LC_*, PATH di ripiego con `~/.local/bin`), `child.c:1726-1790` (contesto SELinux dell'accesso locale, uscite 44–47; portachiavi di sessione), `session.c:3711-3715` (LC_*/LANGUAGE nell'ambiente).
- **Registro di chiusura delle connessioni** (F23): `transport.c:955-1080` `close_why()`.
- **Muro SELinux** `walls.c:260-348` (parte di rete in `remotix_net_t`).

Versioni vere di Fedora 45 (tutte con la fonte): GNOME Shell/Mutter 51.0 sul banco, 51.1 nel repository (`studio/1:191`, `studio/1:559`); Plasma e KWin 6.8.1 sul banco, 6.8.3 nel repository (`studio/5` I13); XFCE 4.20, LXQt 2.4 (`PIANO.md:62`); PipeWire 1.6.9, WirePlumber 0.5.18 (`studio/3:344`); libei 1.6.0 (`studio/2:151`); labwc 0.20.2, wlroots 0.20.2, wlr-randr 0.5.0 (`studio/3:22-23`); Mesa 26.2.7, libva 2.24.1, opus 1.6 (`studio/2:231,238`); systemd 262; OpenSSL 4.0.3. Browser dei banchi: Chromium 157 del repository Fedora (NON Google Chrome) e Firefox 158 (`studio/5` I4).

Prove di Fedora da usare al posto di quelle Ubuntu (tutte dal registro): h1 (23 nov, F35) — gnome 52 PASS (1 FAIL noto: `users-shell-and-environment`, pkexec/SHELL vuoto) + resto di `all.sh` 39 PASS; kde 76 PASS; xfce 60; lxqt 60; `check-base`+`check-input` 31/0 su tutti e quattro (F34); f1 (F33): kde 78/0. Per KDE: `check-kde-resize.py` 10/10, `check-kde-live.py` 8/8 (F14), `check-prelocal.py` P1–P8 (F36). Il banco di Fedora è fatto di VM (non container) con la Radeon RX 6800 passata; in più tre prove a mano del proprietario da macchina vera con la chiavetta LIVE il 25 nov (PIANO.md:343-369, 435-448).

---------------------------------------------------------------------------------------------------

# ch06_capture — «Screen capture» (12 sezioni)

### 1. Capture at a glance: one contract, three compositor families — DA CORREGGERE
- Il testo cita «Ubuntu 26.04 … Ubuntu GNOME 50, Kubuntu Plasma 6.6, Xubuntu, Lubuntu»: su Fedora sono Workstation/GNOME 51, Plasma 6.8 (KWin 6.8.1 sul banco), XFCE 4.20, LXQt 2.4 (`PIANO.md:62`). Le TRE famiglie restano tre (Mutter, KWin, labwc): il titolo regge.
- Figura FIG: la casella «KWin (KDE Plasma) — nested in a screenless labwc» diventa «KWin alone, `--virtual`»; riga «rif» del KDE cambia titolo (vedi (c)). Fonte: `kwin.h:139-155`, `session.c:3930-3956`, F7.
- Tabella «The capture, desktop by desktop»: KWin «Virtual output: KWin's only output, the size of the labwc output that hosts it» → output virtuale `Virtual-0` di KWin, cambiata con `kde_output_management_v2` (`kwin.c:2053`); riga «Resize: stage dismantled, labwc's output is resized, KWin's output follows, remounted» → «stage smontato, `kwin_output_resize()`, rimontato» (`child.c`, F7: «lo stream non segue»); gate «None beyond the user's own D-Bus»: invariato.
- Riquadro «i Two labwc programs»: da TOGLIERE. Su Fedora il labwc è uno solo, quello della distribuzione (0.20.2-2.fc45), `Recommends: labwc` (`rpm/remotix.spec:90`), serve solo a XFCE e LXQt; il pacchetto non porta `/usr/libexec/remotix/labwc` (`remotix.spec:5`; `build/` non ha `labwc-ospite`). Via anche «if that file is missing KDE still starts, with KWin in `--virtual` as declared fallback»: ora è l'unica strada.
- Versione di labwc «0.9.3-1 in Ubuntu's universe» → 0.20.2 (wlroots 0.20.2), nei repository ma NON installato di serie (`studio/3:22`).

### 2. The capture contract — VALE COM'È
- `capture.c`/`capture.h` identici a Ubuntu. La misura citata (12 ago 2026, Mutter 48.7 su Debian) è storica e dichiarata come tale. Nessun cambiamento. Numeri: nessuno contato dal codice.

### 3. GNOME: the Mutter D-Bus sequence — DA CORREGGERE (poco)
- «GNOME 50» → GNOME 51 (Mutter 51.0 banco, 51.1 repository). Interfacce `RemoteDesktop`/`ScreenCast`: «identiche a Mutter 50 (v4/v1)» è solo `[S]` (`studio/1:221-224`: sorgente 51.1 non confrontato) → scrivere «non verificato il diff del sorgente»; verificato invece che la cattura vera funziona (prove del proprietario 21 nov su GNOME, F35 giro h1).
- `session.c` scrive `scaling-factor = 1` nel database dconf di sistema `remotix`: ora compilato dallo scriptlet `%post` (`remotix.spec:235-246`) e ricompilato da `session.c:1843-1906` in `/run/remotix/dconf-compile.tmp` + `/etc/dconf/db/remotix.new` (nomi fissi, SELinux). Se la sezione cita «postinst»: diventa «`%post`».
- Rumore nuovo di Mutter 51 nel log della shell headless: «Error registering session with GDM … No display available» (`studio/1`, tabella riga 7; innocuo, non verificato oltre).

### 4. KDE: the KWin screencast protocol and the nested KWin — DA RISCRIVERE
Titolo da cambiare (es. «KDE: the KWin screencast protocol and KWin alone»); `rif()` che puntano qui: ch06:64, ch10:312, ch10:534.
- **Resta vero** (codice identico o confermato su Fedora): `kwin_open()` e il protocollo `zkde_screencast_unstable_v1` (v6 offerto, `wayland-info`, `studio/5` I9); il permesso `org.kde.remotix.desktop` — ora sorgente `rpm/org.kde.remotix.desktop`, installato in `/usr/share/applications/` da `remotix.spec:152` (non più `debian/…`); `kwin_check_permission()` (`kwin.c:800`); il filtro dei frame uguali (`capture_skip_unchanged`, `child.c:9380`); `kwin_poke()` e il pixel 1×1 in cima (provato su KWin 6.8: layer-shell v5, un commit con danno = un frame, `studio/5` I7); il sidecar `org.freedesktop.ScreenSaver` (`screensaver_alive()`, `kwin.c:1481`, ora avviato da `kwin_virtual_alive()`); cursore con metadati modo 4 (`studio/5` I2: passa; con dimensione FISSA KWin non manda i metadati).
- **Da togliere**: «On Kubuntu 26.04 KWin and Plasma are 6.6.7 (universe)» → 6.8.1/6.8.3; tutto il blocco «KWin nested in labwc» (KWin non può ridimensionare `--virtual` fino a 6.7: falso per 6.8, `kwin.c:1696-1712`); `remotix --kwin-nested W H NODE`; `$XDG_RUNTIME_DIR/remotix-kwin-host`; nodo di render scelto da `card_pick_desktop()` per KWin (su Fedora NESSUNA scelta di scheda per KWin: `session.c:3939-3944`, F12); labwc nostro `/usr/libexec/remotix/labwc` e `-DREMOTIX_LABWC`; misura del 18 nov (0 presented / 755 discarded, `studio/10-kde-controprova-labwc.md`) — è di Ubuntu; `build/labwc-ospite/`, patch wlroots, archivio `remotix-<version>-labwc-source.tar.gz`, licenze GPL/MIT del labwc; tabella «The nested KWin»: `HOST_RC`, `LABWC_UPDATE_ACTIVATION_ENV=0`, refresh 240 Hz, ticker `TICKER_MS=16`, `KWIN_FORCE_SW_CURSOR=1` (impostato solo da `kwin_nested_alive()`, `kwin.c:1685`); `kwin_host_resize()`, `kwin_host_settle()`, `kwin_host_exists()`; «Without our labwc … declared fallback `--virtual`».
- **Da scrivere** (con prova): drop-in `zz-remotix-monitor.conf` di `plasma-kwin_wayland.service` con `ExecStart=remotix --kwin-virtual W H -- kwin_wayland_wrapper --virtual --xwayland --width W --height H --no-lockscreen` e `Environment=REMOTIX_KDE_HOST=1` (`session.c:3930-3956`; ordine esatto degli argomenti da rileggere). `kwin_virtual_alive()` fa un doppio fork per il sidecar ScreenSaver e poi `exec` del wrapper (`kwin.c:1713-1750`). `kwin_output_resize()` (`kwin.c:2053`): `kde_output_management_v2` ≥ 22 e capacità `custom_modes` (0x2000); modo personalizzato con `add_cvt` (qualsiasi misura, anche dispari; con `set_resolution` KWin scarta larghezze non multiple di 8: `[M]` 1367x768, 1365x767, 1001x601, 1919x1079); ogni `set_custom_modes` SOSTITUISCE i modi; ~3 ms; massimo 4 uscite e 64 modi (`OUT_MAX_MODES`); poi RILETTURA dal compositore. Nascita: KWin ricorda l'ultimo modo di `Virtual-0` in `~/.config/kwinoutputconfig.json` (F8, I6): `--width/--height` valgono solo la prima volta, quindi il figlio verifica e corregge PRIMA di montare lo stream; il file non si tocca e resta nella casa dell'utente (dichiararlo). Errori e comportamento (F13): `NOT_SUPPORTED` (KWin < 6.8) = sessione RIFIUTATA con una riga e messaggio 0x0E, nessun ripiego (`child.c`, `kde_refused`); uscita non ancora pronta = ritenta, una riga ogni 5 s; uscita presente ma KWin dice no o tace = ripiego DICHIARATO, si monta alla misura che KWin ha, la pagina riscala. Limite noto (F13): KWin lento oltre 3 s alla nascita fa partire il ripiego.
- **Prova**: I1–I9 di `studio/5` (7 cambi 800x600…3840x2160 anche dispari, 60 fps a ogni misura, Firefox 158/Chromium 157/xterm vivi); `check-kde-resize.py` 10/10 e 6/6, `check-kde-live.py` 8/8 (F14); giro h1 kde 76 PASS (F35).
- **Non verificato / limiti da dire**: più schede grafiche (`studio/5` I12, F12), KWin 6.8.3 (I13), ingresso EIS dopo il cambio (I10: `studio/5` lo dà «da provare col prodotto»; `check-kde-resize` lo copre solo indirettamente), forma del cursore dopo un cambio.
- Numeri «da ricontare»: «about 50 buffers a second for five real changes (3776×2016)», «59 frames/s against 52–55» sono misure di Ubuntu, non copiabili: togliere o ripetere. Su KWin 6.8 `--virtual`: 60 fps a ogni misura (`studio/5` I1, I4).

### 5. The lost frame (KWin) — DA CORREGGERE
- Il meccanismo (`damage_lost`, `capture_frame_lost()` dopo 200 ms, `kwin_poke()`) è in codice identico (`capture.c`) o presente (`kwin.c:595`). Il sintomo (finestra a metà animazione 18–26 s) era misurato con KWin 6.6.7 «nested in labwc», PipeWire 1.6.2: sostituire con KWin 6.8.1 alone, PipeWire 1.6.9. Che il difetto si presenti ancora con `--virtual` e KWin 6.8: **non verificato** (`studio/5` misura 60 fps e poke ok, non l'evento raro).
- Figura: «KWin (nested in labwc)» → «KWin». Il commento di `kwin.c:588` ancora cita «the ticker sends to labwc»: il pixel 1×1 in cima resta, il ticker no.

### 6. PipeWire negotiation, resize and wake-up — DA CORREGGERE
- «Mutter 50.1» (sorgente letto) → Mutter 51: stesse note `[S]` (`studio/1:221-224`): formati BGRx/BGRA, `DEFAULT_SIZE` 1280×720, colorPrimaries/gamma 2.2 NON riverificati su 51.
- Riga KDE: la dimensione di KWin segue ora `kwin_output_resize()`; lo stream aperto NON segue il cambio (`studio/5` I1: resta 1280×720 mentre l'uscita cambia): smontare e rimontare (`child.c`). KWin dà metadati del cursore solo con offerta «a intervallo» (I2).
- DMA-BUF: «NVIDIA with GNOME 50 on Ubuntu» resta storico; Radeon/Intel su Fedora: `studio/5` I11 «modificatori DMA-BUF di KWin su RADV: da provare col prodotto»; sulla Radeon di Fedora la rotta è Vulkan (F35: `--encoding-test h264` = `h264_vulkan`).
- Frase «Since 17 Nov 2026 the package refuses a new installation with no DRM render node» vale anche su Fedora (`%pre`, `remotix.spec:173-183`), rimando a «The package» (nome del capitolo di G4).

### 7. XFCE and LXQt: wlroots screencopy — DA CORREGGERE
- «Ubuntu 26.04 has labwc 0.9.3» → labwc 0.20.2 + wlroots 0.20.2 (nei repository, non di serie, `Recommends`). `zwlr_screencopy_manager_v1` v3 offerto (`grim` riuscito 1344×768, `studio/3:346`); `ext_image_copy_capture_manager_v1` c'è ma il prodotto non lo usa.
- Formati: «labwc offre solo XBGR8888 in memoria» (commento di 0.8.3/0.9.3) → su 0.20.2 **non verificato** il formato esatto; verificato che cattura, input e ridimensionamento passano: XFCE 60 PASS e LXQt 60 PASS (F22, F35), `check-resize.py` 10/10.
- Ambiente `WLR_BACKENDS=headless`, `WLR_LIBINPUT_NO_DEVICES=1`, `LABWC_UPDATE_ACTIVATION_ENV=1`, `WLR_RENDER_DRM_DEVICE`: `session.c` per questi desktop non cambia; con la Radeon vera `labwc -d` crea il renderer GLES2 su Mesa 26.2.x (`studio/4:142`).
- Al titolo «labwc 0.9.3 vs 0.20.2»: nessuna opzione o `rc.xml` da cambiare (F22; F33 punto 8: tasti di serie cambiati — `W-<freccia>`, terminale `lab-sensible-terminal`, `A-<freccia>` deprecato; regressione nota di lxqt-panel con wlroots < 0.20.2).

### 8. Slabs: zero copy on labwc — DA CORREGGERE (poco)
- Codice identico (`wlroots.c`). Cambiare solo i riferimenti: «Which route a Radeon takes on Ubuntu 26.04» → su Fedora la Radeon prende la rotta Vulkan SOLO con `mesa-vulkan-drivers-freeworld` (RPM Fusion); «never re-measured on Ubuntu» → non rimisurato nemmeno su Fedora (il rischio hang amdgpu con slab non è stato provato: **non verificato**). `113 MB per session` = 3 × 4096 × 2304 × 4: aritmetica, resta.

### 9. Zero copy and the memory fallback — VALE COM'È
- Codice identico; il contenuto (stride a 64 byte, iHD, ripiego in memoria) è generico. Nessun riferimento Ubuntu.

### 10. The cursor channel — VALE COM'È
- Identico. Riga KDE «KWin's metadata (mode 4)»: confermata dalla sonda su Fedora (`studio/5` I2), forma del cursore col prodotto «da provare» ma i `pointer-shape-*` passano (vedi 11).

### 11. The encoded cursor theme — DA CORREGGERE (poco)
- «The pointer-shape-* checks pass on the four desktops in the Ubuntu rounds» → Fedora: `pointer-shape-text|arrow|edge` stanno in `prove/check-input.py:28-29`; passano nel giro h1 (gnome 52, kde 76, xfce 60, lxqt 60: F35).
- `KWIN_FORCE_SW_CURSOR=1` esce dalla storia di KDE (era solo nel ramo annidato, `kwin.c:1685`); resta il tema `remotix-invisible` con `XCURSOR_THEME`+`XCURSOR_SIZE` insieme (`session.c:3406-3412`, 3615). «The labwc probe»: non rifatta su 0.20.2 (**non verificato**; i `pointer-shape` passano).
- `FILE_MAX = 8 MiB` ecc.: da ricontare (comando sotto).

### 12. Capture constants and what was verified — DA CORREGGERE
- Tabella costanti (`MOTION_FPS`, `WAKEUP_MS`, `WAIT_LATCH_MS`, …): file identici a Ubuntu → valgono quanto valgono su Ubuntu; **da ricontare** con `grep -nE 'define (MOTION_FPS|MOTION_WAIT_S|WAKEUP_MS|WAIT_LATCH_MS|ZERO_COPY)' fedora45/src/child.c fedora45/src/capture.c`.
- Metà «What was verified»: da RISCRIVERE. Togliere i round Ubuntu del 18 nov (container, Chrome 156.0.8078.79, Firefox 153.7.0, «GNOME 116/124 … 123/124», `RX_BANCO=vm`). Mettere i dati di Fedora (sopra): VM + Radeon; giro h1 enforcing; Chromium 157/Firefox 158; chiavetta LIVE a mano il 25 nov (cattura/accesso locale; codifica riuscita sulla scheda Intel, PIANO.md:344-345).
- «Not verified» di Fedora: più schede (F12), Intel/NVIDIA col prodotto sulle VM (solo Radeon), KWin 6.8.3, Mutter 51.1, Google Chrome (si è provato Chromium).

---------------------------------------------------------------------------------------------------

# ch07_encoding — «Video encoding» (13 sezioni)

### 1. Encoding at a glance: one front, two GPU routes — DA CORREGGERE
- Togliere «On Ubuntu 26.04 the package also contains a GPL-2.0 program, the labwc that hosts KWin»: il pacchetto Fedora non ha alcun programma GPL (`remotix.spec:5`, `remotix.spec:111-112`: «Video is encoded only on the video card»). Il resto (due rotte, niente software, niente libavcodec) vale: `encoder.c`, `vadirect.c`, `vulkanvideo.c` identici; D1: nessuna codifica software.
- Tabella dei file: invariata (`render_grant.c` esiste: vedi 4).

### 2. Codecs and their negotiation — VALE COM'È
- RCP/1 e `rcp.c` identici; codec 1 = HEVC, 3 = H.264 (`child.c`, `studio/1:429` in forma di riga `child.c:429`). Nessun riferimento di distribuzione.

### 3. Choosing the GPU route — VALE COM'È
- Regola «Vulkan se `vulkan_fit()`, altrimenti VA-API» identica. Su Fedora, con la Radeon e i driver freeworld, esce `h264_vulkan` (F35). Numeri da codice: nessuno.

### 4. Choosing the card and granting access to it — DA CORREGGERE
- Riga «Which card does labwc (XFCE, LXQt) or KWin's host (KDE) draw on? `card_pick_desktop()`»: per KDE su Fedora NESSUNA scelta di scheda (KWin `--virtual` sceglie da sé, `session.c:3939-3944`; non provabile con una sola GPU, F12, `studio/5` I12). Resta per labwc.
- Gruppo e «render grant»: su Fedora il nodo `/dev/dri/renderD128` è `crw-rw-rw- root render` (0666, nessuna ACL), il gruppo `render` (gid 105) è vuoto (`studio/1:437`) → `render_grant.c` non ha niente da concedere. Come il codice tratta un modo 0666 senza ACL: **non verificato** (`studio/1:438`, tabella 12 «parziale»). Con logind ≥ 260 (systemd 262 su Fedora) `XDG_SESSION_EXTRA_DEVICE_ACCESS=render:accel` dà ACL alla sessione (`studio/1:172`).
- «debian/remotix.prerm» → `%preun` di `remotix.spec:367-373` (`remotix --drop-render-grants`); il registro `/var/lib/remotix/render-grants` si cancella in `%postun` (righe 393-398). `usermod -aG` ora su Fedora, sempre «gruppo che possiede i renderD*» (qui `render`).
- Nota NVIDIA (`/dev/nvidia*`): invariata; **non verificato** su Fedora.

### 5. The encoding test: remotix --encoding-test — DA CORREGGERE
- `debian/remotix.preinst` → `%pre` (`remotix.spec:168-183`: rifiuto della PRIMA installazione senza `/sys/class/drm/renderD*`, `exit 1`); `debian/remotix.postinst` → `%post` (righe ~255-262: `timeout 30 remotix --encoding-test h264`, solo `$1 -eq 1`, avviso a video, non fa mai fallire `dnf`). «It never makes apt fail» → «dnf».
- Togliere la discussione `va-driver-all` / `mesa-libgallium` (Ubuntu). Su Fedora i driver NON sono dipendenze (D1, `remotix.spec:14,86-87`): il messaggio dello scriptlet dice di abilitare RPM Fusion (free) e installare `mesa-va-drivers-freeworld` (NVIDIA: driver proprietario). Pacchetti veri (`studio/1:420-425`, `live-installa.sh:130-167`): `rpmfusion-free-release-45`, `mesa-va-drivers-freeworld` (da `/usr/lib64/dri-freeworld/radeonsi_drv_video.so`), `mesa-vulkan-drivers-freeworld` (sostituisce `mesa-vulkan-drivers`), per Intel `intel-media-driver` da RPM Fusion nonfree (il messaggio dello scriptlet NON lo nomina).
- Formato JSON del test: invariato (codice identico).

### 6. VA-API without libavcodec — DA CORREGGERE (poco)
- «libva 2.23 and Mesa 26.0.8» → libva 2.24.1, Mesa 26.2.7 (`studio/2:231,238`). I commenti di Mesa 25.0.7 (driver riscrive gli header, layer di padding) restano storici: su Fedora la rotta VA-API di AMD **non è stata provata** (la Radeon prende Vulkan, F35). `libva` cerca i driver in `dri-nonfree/`, `dri-freeworld/`, poi `dri/` (`studio/1:422`).

### 7. The Vulkan Video encoder — DA CORREGGERE (la tabella dei costruttori va riscritta)
- Il codice vale. Tabella «Vendor / Route / Evidence»: AMD RADV — Fedora di serie NON ha `VK_KHR_video_encode_h264/h265` (Mesa 26.2.x, `-Dvideo-codecs` = `all_free`, `studio/1:418-419`), compaiono con `mesa-vulkan-drivers-freeworld` (`studio/1:424`); misurato: `--encoding-test h264` hardware `h264_vulkan` sulla Radeon, VM di consegna (F35) e giro h1. Togliere le prove Ubuntu («unione10», 19 nov, Kubuntu 26.04.1 live). Intel: rotta VA-API con `intel-media-driver`; su chiavetta LIVE con scheda Intel+Radeon il 25 nov «codifica riuscita sulla Intel» (PIANO.md:344-345): la rotta non è registrata, **non verificato** che fosse VA-API. NVIDIA: invariato, **non verificato** su Fedora.
- Togliere «The package Recommends mesa-vulkan-drivers (Mesa 26.0.8, main)» e «va-driver-all is a Recommends, in universe»: su Fedora nessun Recommends per i driver video.
- Riquadro «at startup of the VMs the card's driver is still loading … THIS SERVER CANNOT ENCODE VIDEO»: era osservazione Ubuntu; su Fedora **non verificato**.

### 8. BT.709 colour conversion — DA CORREGGERE (poco)
- Riquadro «Gamma 2.2 on GNOME 50» → Mutter 51: non riverificato (`studio/1:221-224` `[S]`). Resto identico (colors709.c, shader). «Radeon VPP loses on chroma»: storico, ripetuto solo con Mesa 25.

### 9. Writing the bitstream headers — VALE COM'È
- `bit_writer.c`, `vadirect.c`, `vulkanvideo.c` identici; la nota HEVC 2544×1344→2560×1344 su radeonsi è storica.

### 10. Bytes, levels and the confession — VALE COM'È
- Identico.

### 11. Keyframes on demand — VALE COM'È
- Identico.

### 12. Resizing the encoder and the frame ceiling — VALE COM'È
- Identico. La frase sugli slab di labwc è generica.

### 13. Encoder timings, constants and verification status — DA CORREGGERE
- Costanti/contatori: file identici → **da ricontare**: `grep -nE '#define +(ENCODER_|RENDER_|CODIFICATORE_|BANDWIDTH_WINDOW_US)' fedora45/src/encoder.c fedora45/src/child.c`.
- «Verified (Ubuntu 26.04, 18-19 Nov 2026)»: da riscrivere con Fedora: `avc1.640033` negoziato con Chromium 157/Firefox 158 (non Chrome 156); `--encoding-test h264` hardware su Radeon con freeworld (F35); chiavetta con Intel. «Not verified»: rotta VA-API di AMD, NVIDIA, VM senza scheda (il rifiuto è nello `%pre`, non provato in Fedora: `remotix.spec:173`), gruppo/ACL render con utenti «lingering» (qui nodo 0666).

---------------------------------------------------------------------------------------------------

# ch08_quality — «Quality, degradation and budget» (14 sezioni)

Codice quasi tutto identico (`encoder.c`, `rcp.c`, `hsrate.h`, `msgrate.h`, `transport.c` salvo `close_why`). Costanti e tabelle numeriche di questo capitolo (soglie, tetti, 16 MiB, `WT_CLEAR_THRESHOLD_MS`, limiti hsrate/msgrate): **da ricontare** con `grep -nE 'define' fedora45/src/hsrate.h fedora45/src/msgrate.h` e `grep -nE 'WT_CLEAR_THRESHOLD_MS|BANDWIDTH_WINDOW_US|CANVAS_W|CANVAS_H' fedora45/src/*.c fedora45/src/*.h`.

### 1. The quality contract — VALE COM'È
### 2. Where quality is decided — VALE COM'È
### 3. Encoder rate control — VALE COM'È
- Misure su Intel iHD (macchina Ubuntu di prova): storiche, dichiarate tali.
### 4. The 16 MiB frame cap and the quality ladder — VALE COM'È
### 5. Quality recovery after the cap — VALE COM'È
### 6. The video queue threshold — VALE COM'È
### 7. The rate regulator — VALE COM'È
### 8. Keyframe request pacing — VALE COM'È
### 9. The dead line — VALE COM'È
- La riga «Stall … N ms» e le altre soglie: valgono; la chiusura per silenzio dopo la riga di registro `close_why` (F23) dice «idle timeout (silence)» (`transport.c:1021-1080`): se la sezione descrive la riga di log, aggiungere il testo («connection with … closed (N left) — …»).
### 10. Ghost eviction and audio silence — VALE COM'È
### 11. The composition budget — VALE COM'È
- Cifre dell'Intel UHD 770 (1,86 / 0,97 Gpixel/s): misure storiche della macchina di prova; restano come tali.

### 12. Admission: the session cap and the budget — DA CORREGGERE
- Le strade verso 0x0E: su Fedora ce n'è UNA in più: «this KDE session cannot be used: KWin does not offer kde_output_management_v2 version 22 or newer» (`child.c`, `kde_refused`/`scale_refused`, F13; messaggio 0x0E). Contare di nuovo le strade («six roads» → sette, **da ricontare** guardando `child.c`/`rcp.c`). Fonte: F13, `kwin.c:2130-2150`.
- La strada «the desktop's compositor is not installed (XFCE or LXQt without labwc)» ora è più probabile: su Fedora labwc è solo `Recommends` (`remotix.spec:90`); lo scriptlet avvisa (`remotix.spec:265-272`).

### 13. Rate and size guards: hsrate, msgrate, linebudget, dimcheck — VALE COM'È
- Tabelle di limiti (pointer 2000/4000, …): file identici; ricontare con il comando in testa al capitolo.

### 14. Frames that are not encoded, and what is adapted — DA CORREGGERE
- Sezioni «What was verified / Not verified on Ubuntu»: riscrivere per Fedora (giro h1, F35; NVIDIA non provato). Il resto (`--decoder-pace`, `video.pace`) vale.

---------------------------------------------------------------------------------------------------

# ch09_page — «The browser page» (17 sezioni)

`page.html` identico a Ubuntu (`cmp` uguale), `page.c` identico.

### 1. How the page is served — VALE COM'È
- Limiti di connessione (128 / 32 / 64) da costanti (`PAGE_MAX_CLIENTS`, …): identici; ricontare con `grep -nE 'PAGE_(MAX_CLIENTS|PER_ADDRESS|PER_48)' fedora45/src/page.c`.

### 2. Structure of page.html — DA CORREGGERE
- «about 14 000 lines and 0.9 MB (14 258 lines and 937 399 bytes on the Ubuntu tree)»: **da ricontare**: `wc -lc fedora45/src/page.html` (oggi 14326 righe, 941549 byte, uguale a `ubuntu26.04/src/page.html`; il testo Ubuntu è già vecchio).

### 3. Layouts and the states of the document — VALE COM'È
### 4. The connection sequence — DA CORREGGERE
- Aggiungere: il motivo di chiusura nel registro (F23, `transport.c:1021-1100`: chi ha chiuso, errore QUIC, alert TLS 42/45/46/48 con nome, «TLS handshake COMPLETED / NOT completed»); e l'avvertenza sul client: orologio del dispositivo sbagliato di oltre un'ora ⇒ «Opening handshake failed», perché il certificato di sessione nasce con `notBefore` = adesso − 3600 s (`certificates.c:143`; F23 esito 22 nov; da dire anche nei «Requisiti»). Il resto della sequenza è identico.

### 5. Capabilities declared by the page — VALE COM'È
### 6. Choosing the codec on the pixel — DA CORREGGERE (una frase)
- «Firefox 140 ESR … the Ubuntu rounds ran Firefox 153.7.0 and Chrome 156» → Fedora: Firefox 158 e Chromium 157; la misura sulle sette stringhe HEVC NON è stata ripetuta su Fedora (**non verificato**).

### 7. Measuring the decoder ceiling — DA CORREGGERE (poco)
- «a canvas of 4096×2304 end to end has not been verified on Ubuntu» → su Fedora vale uguale (KDE: Chromium a 3840×2160 con 60 fps, `studio/5` I4; 4096×2304 **non verificato**).

### 8. Canvas and view — DA CORREGGERE
- «On KDE the compositor (KWin) runs nested inside a screenless labwc … at reattach REMOTIX resizes labwc's output, which KWin follows (§10.40)» → KWin da solo: al riaggancio con un'altra misura `kwin_output_resize()` (F7, F14); NIENTE ridimensionamento a caldo su nessun desktop (F14: con la sessione viva la finestra del browser non cambia il desktop, la pagina riscala; decisione del 17 ago 2026, DECISIONS.md §5.1-bis). Provato: `check-kde-live.py` 8/8, `check-kde-resize.py` 10/10, `check-resize.py` 10/10 su XFCE e LXQt.
- Riferimenti storici a Firefox 140/Chrome 154: restano storici.

### 9. Asking for the canvas with FIT_CANVAS — VALE COM'È
### 10. Receiving video frames — VALE COM'È
### 11. Decoding with WebCodecs — VALE COM'È
### 12. Drawing paths: WebGL2, bitmaprenderer, 2D canvas — VALE COM'È
- Misure su Chrome/Firefox con date (24 ott, 26 set): storiche.
### 13. Measurements and the diagnostics mode — VALE COM'È
### 14. What the page stores and what it declares — VALE COM'È

### 15. End of session in the page — DA CORREGGERE
- «Measured on Ubuntu 26.04 (round 1, 18 Nov 2026) … 17 s» → cifre di Fedora o toglierle (**non verificato**: non misurato su Fedora). «Six roads to that reason» → sette (nuova: sessione KDE rifiutata, F13; **da ricontare** nel codice). Chiusura KDE con accesso locale: sul lato pagina nessun cambiamento (F36 è lato root).

### 16. The video worker and the MSE path — VALE COM'È
- Resta la nota sul commento «PROPOSAL … NOT decided» in `page.html` (difetto del sorgente, identico).

### 17. Browsers supported and untested — DA CORREGGERE
- Sostituire i paragrafi Ubuntu («Chrome 156.0.8078.79 … 18 Nov», «unione10», «Samsung DeX on unione5») con quelli di Fedora: prove a mano del proprietario 21–23 nov — GNOME: portatile Windows e PC Linux (stacco/riaggancio, appunti, audio e video «tutto ok»), da Android video 1440p «fluidissimo» (assenti gli scatti E4 visti su Ubuntu in VM); KDE e XFCE e LXQt: «OK», KDE con dispositivi di risoluzione diversa; notebook Windows con orologio sballato (F23). Browser dei banchi: Chromium 157 + Firefox 158 su Linux (non Google Chrome: **non verificato** su Fedora). Telefono reale, DeX, Safari: **non verificati** (come Ubuntu).
- Tabella dei browser: invariata (decisioni del proprietario).

---------------------------------------------------------------------------------------------------

# ch10_input — «Input» (17 sezioni)

### 1. Input at a glance — DA CORREGGERE
- «On KDE, KWin runs nested inside a screenless labwc that REMOTIX starts only to host it; input still goes to KWin through libei» → KWin da solo; input comunque via libei (`input.c` identico a parte `pointer_primed`).

### 2. The input messages — VALE COM'È
### 3. Classic and touch layouts in the page — VALE COM'È

### 4. Mouse and pointer in the classic layout — DA CORREGGERE (paragrafo nuovo)
- Aggiungere il difetto di Mutter 51 (F34): il PRIMO movimento assoluto dopo l'avvio del dispositivo puntatore arriva con una coordinata a 0 (misurato con un utente solo e con telefono, `check-multiuser`, `check-phone tap-click-portrait`); cura: `input.c:257,1330,1940-1951`, campo `pointer_primed`, il primo movimento inviato DUE volte, «TO BE REMOVED WHEN MUTTER IS FIXED»; solo percorso libei (GNOME), non wlroots. Su Ubuntu stesso codice e stesso difetto probabile (E2), non provato.
- Il resto (DeX, noVNC #1727, regola dei sub-pixel) vale.

### 5. Wheel and scrolling — DA CORREGGERE (poco)
- «Ubuntu 26.04 has Mutter 50.1 and libei 1.5.0, the sign was not measured again» → Fedora: Mutter 51, libei 1.6.0, segno non rimisurato; `mouse-wheel` passa (`check-input.py:28`, F35).

### 6. Keyboard: letters and positions — VALE COM'È

### 7. Shortcuts the browser keeps — DA CORREGGERE
- Il sidecar `org.freedesktop.ScreenSaver` (Plasma ≥ 6.4, Ctrl+Alt+Del): vale su KWin 6.8; ora nasce in `kwin_virtual_alive()` e il rif punta alla sezione rinominata (ch10:312). Ctrl+Alt+Del su KDE non ripetuto a mano su Fedora: **non verificato** oltre le prove automatiche.

### 8. Touch gestures — VALE COM'È
### 9. The touch pointer is announced to the server — VALE COM'È
### 10. The on-screen keyboard on a phone — VALE COM'È
### 11. From a letter to key positions — VALE COM'È

### 12. Keyboard layout negotiation — DA CORREGGERE
- GNOME: «the package compiles in its postinst» → `%post` (`remotix.spec:235-246`) e `session.c:1843-1906`; «removed by apt purge» → `%preun` (`remotix.spec:400-406`, cancella `~/.config/dconf/remotix` per nome, come l'utente). Schema `org.gnome.desktop.input-sources` su GNOME 51: stessa riga, **non verificato** il diff dello schema; `RemoteDesktop.Session.SetKeymap` su Mutter 51: non guardato.
- KDE: «kxkbrc … KWin 6.6.6 on Ubuntu» → KWin 6.8.1; `kwin_layout()` non è cambiata; `kbd-text`, `kbd-accents`, `kbd-altgr` in `check-input.py` passano su KDE (F35: kde 76). XFCE/LXQt: «labwc 0.9.3» → 0.20.2; i test passano (60/60).

### 13. Injection through libei — DA CORREGGERE
- «Ubuntu 26.04 has 1.5.0» → libei 1.6.0 (Fedora; `BuildRequires: libei-devel >= 1.3.901`, `remotix.spec:56`). Il difetto di libei 1.3.901 resta storico (1.6.0 **non verificato**).
- Paragrafo KDE: «that KWin is the nested one … ExecStart replaced by `remotix --kwin-nested` … `HOST_RC` … `KDEHOST_MARK` = remotix-kwin-host» → `remotix --kwin-virtual`, segni `KDEHOST_OPTION` (`--kwin-virtual`) e `KDEHOST_ENV` (`REMOTIX_KDE_HOST=1` nell'ambiente dell'unità, riconosciuto da `/proc/<pid>/environ`) (`kdehost.h:50-61`, `118-142`; il segno non sceglie né utente né unità: contano cgroup e proprietario del pid). Il file del drop-in resta `zz-remotix-monitor.conf` (`session.c:3904,4821`).
- Regole su `ei_device_frame()`, `ei_ping()`, `0x300`: invariate (`input.c` identico tranne il campo).

### 14. Pressed keys: counting, releasing, healing — DA CORREGGERE (poco)
- «before `kwin_host_resize()` resizes the labwc that hosts KWin» → `kwin_output_resize()` (`child.c` ~11662, `kwin.h:150`). La misura «Mutter 48.7» e «Mutter 50.1 non rimisurata» → Mutter 51: **non verificato**. `heal()` e `session_life()` invariati.

### 15. Virtual keyboard and pointer on labwc — DA CORREGGERE
- «Ubuntu 26.04 has labwc 0.9.3-1 and wlr-randr 0.4.1 (universe)» → labwc 0.20.2, wlr-randr 0.5.0 (`studio/3:22-23`). Le cinque trappole di wlroots sono misure su 0.19/0.9.3 (21 set): su 0.20.2 le basi funzionano (virtual pointer/keyboard, `wlr-randr --custom-mode`, `studio/4:135`), il tasto «riporta dentro» `W-C-A-S-F12`: configurazione letta, gesto non fatto a mano (`studio/3:387`); `check-resize.py` 10/10 con terminale aperto (F22). Tasti di serie cambiati in labwc 0.20 (F33 punto 8).

### 16. Input decisions — DA CORREGGERE (una riga)
- «libei 1.5.0 not checked» → 1.6.0 non verificato.

### 17. What was verified for input and what was not — DA RISCRIVERE
- Tutto il resoconto è Ubuntu (container per sapore, round del 18 nov, `RX_BANCO=vm`, `unione3/5/10`, Kubuntu `page-cad-chain`). Per Fedora: `check-input.py` COMMON (`prove/check-input.py:28`) e righe per desktop; esiti: h1 gnome 52 PASS (FAIL noto pkexec) e 39 di `all.sh`; kde 76; xfce 60; lxqt 60; `check-base`+`check-input` 31/0 sui quattro (F34); `two-users`, `three-users`, `same-user`, `check-phone` (incl. `tap-click-portrait` due volte) PASS con la cura `pointer_primed`. Da non dire: telefono reale, tastiera Android, Safari, tastiera fisica non-US (**non verificati**). Prove a mano: sezione 17 di ch09.

---------------------------------------------------------------------------------------------------

# ch11_audio_clipboard — «Audio and clipboard» (13 sezioni)

### 1. Audio at a glance — VALE COM'È
### 2. The audio format and its datagram — VALE COM'È
- Misure di datagramma del 17 ago (Chrome 151, Firefox 140): storiche.

### 3. The session sink and its capture — DA CORREGGERE
- «PipeWire 1.6.2 with WirePlumber 0.5.13» → PipeWire 1.6.9 e WirePlumber 0.5.18 (`studio/3:344`); pacchetto: `Requires: pipewire`, `wireplumber` (`remotix.spec:76-77`), `BuildRequires: pipewire-devel` (1.6.9-1.6.11). `sound.c` identico. Riquadro «WirePlumber on the VMs … Ubuntu internal error notice»: è di Ubuntu; su Fedora **non verificato** (togliere o dire «non osservato»).
- Su Fedora PipeWire/WirePlumber partono come unità del gestore utente (`studio/3:344`): nella sessione remota REMOTIX li avvia come su Ubuntu (da `session.c`, non cambiato).

### 4. From samples to datagrams — DA CORREGGERE (una riga)
- «On Ubuntu the checks' machines record «FIFO NOT OBTAINED»»: su Fedora **non verificato**; togliere o riscrivere dopo aver guardato il journal di una VM Fedora.

### 5. The Opus encoder — DA CORREGGERE
- «Ubuntu 26.04 has libopus 1.6.1, comparison not repeated» → Fedora `opus-devel` 1.6 (`studio/2:231`, `BuildRequires: opus-devel`, `remotix.spec:54`), confronto con libavcodec non ripetuto. Parametri (`AUDIO_OPUS_SPACE`, `AUDIO_OUT_MAX = 1200`): `audio.c` identico, da ricontare con `grep -nE 'AUDIO_(OPUS_SPACE|OUT_MAX|BLOCK)' fedora45/src/audio.c`.

### 6. Playing audio in the page — VALE COM'È
- Decoder Opus WebAssembly (libopus 1.5.2 fissata, `src/opus-wasm/build.sh`) identico; attenzione: lo script costruisce «in a podman container» — è lo script del prodotto, non del banco, ma l'ordine del proprietario («niente podman» per Fedora, CLAUDE.md) vale per le prove: citare solo che il decoder è già incorporato in `page.html`.

### 7. Clipboard at a glance — VALE COM'È
### 8. The clipboard messages and their limits — VALE COM'È

### 9. Clipboard on GNOME — DA CORREGGERE (poco)
- «behaviour on Mutter 50 was not checked» → Mutter 51; provato a mano dal proprietario su GNOME 21 nov (appunti, stacco/riaggancio, «tutto ok», PIANO.md:200-202) e `check-clipboard` (1 riga/2 righe per desktop, F22).

### 10. Clipboard on KDE and labwc — DA CORREGGERE
- Togliere la frase sulla cartella runtime `remotix-kwin-host` del labwc che ospita KWin (non esiste più). «On Ubuntu 26.04 this is the branch in use: KWin 6.6 only exposes ext_data_control…» → Fedora: KWin 6.8.1 offre `ext_data_control_manager_v1` v1 e NON `zwlr_data_control` (`wayland-info`, `studio/5` I9): stessa conclusione, nuova fonte. LXQt senza `qlipper` (non c'è su Fedora): gli appunti passano per data-control di labwc, `check-clipboard` 2/2 (F22). Klipper su Plasma: **non verificato** (come Ubuntu).

### 11. Clipboard in the browser — VALE COM'È
### 12. Audio and clipboard decisions — VALE COM'È

### 13. What was verified for audio and clipboard — DA RISCRIVERE
- Ubuntu: `vm-gnome-unione10`, Chrome/Firefox, DeX `unione5`. Fedora: `check-audio` 1/1 e `check-clipboard` 2/2 su XFCE e LXQt (F22), PASS nei giri h1 per GNOME e KDE (F35); a mano 21–23 nov su tutti e quattro i desktop (audio, appunti «ok»); chiavetta LIVE 25 nov. **Non verificati**: Firefox con prove di audio su Fedora oltre ai banchi, Safari, telefono reale, gestori di appunti (Klipper).

---------------------------------------------------------------------------------------------------

# (a) Cose che esistono solo su Fedora e meritano una SEZIONE NUOVA (nel gruppo G2)

1. **ch06**, dopo la sezione KDE riscritta (o come sua parte): «KWin alone: resizing its output with kde_output_management_v2» — `kwin_output_resize()`, `add_cvt`, perché non `set_resolution`, rilettura dal compositore, memoria di KWin in `~/.config/kwinoutputconfig.json` (F8), il rifiuto pulito (F13), «lo stream non segue» (F7, I1). Prova: `studio/5` I1/I6, `check-kde-resize.py` 10/10.
2. **ch07**, sezione in primo piano «Requirements: video drivers on Fedora» (D1; piano: manuale con «Requirements» in primo piano, PIANO.md:101): RPM Fusion free (`rpmfusion-free-release-45`), `mesa-va-drivers-freeworld`, `mesa-vulkan-drivers-freeworld` (sostituisce `mesa-vulkan-drivers`), Intel `intel-media-driver` (nonfree), NVIDIA proprietario; perché il Mesa di Fedora non ha H.264/HEVC (`-Dvideo-codecs=all_free`, `studio/1:419`); cosa fa il pacchetto (nessuna dipendenza; avviso in `%post`). Nodo 0666 e gruppo `render` vuoto.
3. **ch09** (sezione «The connection sequence» o nuova): il motivo di chiusura nel registro (`close_why()`, F23) e l'orologio del client (F23 esito).
4. **ch10**, in «Mouse and pointer»: la cura Mutter 51 `pointer_primed` (F34).
5. **ch10** o ch06: la chiusura di KDE per accesso locale (F36: forzata = `graphical-session.target`, regola SELinux `xdm_unit_file_t`, 5 s di attesa) è materia di ch03/ch13; per G2 basta il rimando dal capitolo della cattura/input (KWin vivo = stage vivo).
6. **ch08** «Admission»: la nuova strada 0x0E «KDE session cannot be used» (F13).
7. **ch11**: nessuna novità Fedora oltre le versioni.

# (b) Cose di Debian/Ubuntu da TOGLIERE o sostituire nel gruppo G2

- Tutto il KWin «annidato» in labwc: `--kwin-nested`, `remotix-kwin-host`, `HOST_RC`, ticker, `KWIN_FORCE_SW_CURSOR`, labwc nostro `/usr/libexec/remotix/labwc` e `-DREMOTIX_LABWC`, `build/labwc-ospite/`, patch `wlroots-0.19.2-remotix-presented-root.patch`, archivio `remotix-<version>-labwc-source.tar.gz`, licenze GPL-2.0/MIT di quel labwc (ch06 S1, S4, S5, ch07 S1, ch10 S1, S7, S13, S14, ch11 S10, ch09 S8). Nota fuori G2: `fedora45/THIRD-PARTY-LICENSES:1252,1603` cita ancora il labwc nostro.
- «universe», `va-driver-all`, `mesa-libgallium`, `apt`, `debian/*` (`remotix.preinst`, `postinst`, `prerm`, `control`), «apt purge» → `rpm/remotix.spec` (`%pre`, `%post`, `%preun`, `%postun`), `dnf`.
- Versioni Ubuntu: GNOME/Mutter 50.1, KWin 6.6.6/6.6.7, PipeWire 1.6.2, WirePlumber 0.5.13, libei 1.5.0, libva 2.23, Mesa 26.0.8, libopus 1.6.1, labwc 0.9.3-1, wlr-randr 0.4.1.
- Banco e prove Ubuntu: container, `unione3/5/10`, `RX_BANCO=vm`, `RX_TEMPO=2`, Chrome 156.0.8078.79, Firefox 153.7.0/160, cifre 116/124, 123/124, 111/124, 117/124 → ricavare le cifre di Fedora dai giri h1/f1 (F33, F35); strumenti nuovi: `check-kde-resize.py`, `check-kde-live.py`, `check-kde-exit.py`, `check-prelocal.py`, `check-exit.py`, `check-resize.py`.

# (c) `rif("…")` che si rompono se il titolo di una sezione cambia

Verificato con uno script che cerca ogni `rif("…")` di tutti i 25 capitoli tecnici (nessun rif orfano oggi).

- **Titolo da cambiare obbligatoriamente**: ch06 S4 «KDE: the KWin screencast protocol and the nested KWin» ← `ch06_capture.py:64`, `ch10_input.py:312`, `ch10_input.py:534`.
- **Sezioni G2 puntate da altri capitoli o dentro G2** (da NON rinominare, o da aggiornare tutti i punti):
  «The lost frame (KWin)» ← ch08:308, ch12:843, ch19:87; «PipeWire negotiation, resize and wake-up» ← ch07:297; «The encoded cursor theme» ← ch06:327; «Capture constants and what was verified» ← ch08:326 (il titolo contiene «what was verified»: se si riscrive la metà verificata il titolo regge); «Codecs and their negotiation» ← ch07:267,403; «Choosing the GPU route» ← ch06:585; «BT.709 colour conversion» ← ch06:461; «Bytes, levels and the confession» ← ch07:74,207,225; «Admission: the session cap and the budget» ← ch09:613; «The connection sequence» ← ch09:70; «Capabilities declared by the page» ← ch09:171,569; «Choosing the codec on the pixel» ← ch09:68,566,660; «Measuring the decoder ceiling» ← ch09:208,348; «Canvas and view» ← ch09:292; «Receiving video frames» ← ch09:69; «Measurements and the diagnostics mode» ← ch09:66,414, ch10:177,303; «What the page stores and what it declares» ← ch09:198, ch10:430; «End of session in the page» ← ch09:74,129, ch10:588, ch11:141; «The video worker and the MSE path» ← ch09:73,95,542; «Mouse and pointer in the classic layout» ← ch09:119,512,672; «Shortcuts the browser keeps» ← ch06:280, ch09:132,547; «The touch pointer is announced to the server» ← ch10:660; «The on-screen keyboard on a phone» ← ch11:400; «Keyboard layout negotiation» ← ch09:193, ch10:93; **«What was verified for input and what was not» ← ch10:9** (se la sezione si rinomina, cambiare ch10:9); «Clipboard in the browser» ← ch10:252, ch11:281.
- **Titoli di altri gruppi usati da G2**, da non rompere nel lavoro di G1/G3/G4: «Startup and life cycle», «Overall architecture», «The RCP/1 protocol», «Transport», «Input», «Audio and clipboard», «Video encoding», «Screen capture», «Quality, degradation and budget», «The browser page», «Performance and capacity», «Security model», «Login and its defences», «The package», «Testing», «Logging and diagnostics», «The four desktops», «GNOME: headless Shell and session dconf» (ch10:462), «When the session ends before the stage is gone» (ch06:498, ch09:609), «Appendix C — Known issues and open points».

# Numeri «da ricontare» (non copiare)

- `page.html`: `wc -lc fedora45/src/page.html` (ch09 S2).
- Costanti di cattura/codifica/qualità (ch06 S11-S12, ch07 S13, ch08 S13, ch11 S5, ch09 S1): comandi `grep` indicati nelle voci; i file sono identici a Ubuntu.
- Numero delle strade verso 0x0E (ch08 S12, ch09 S15): contarle nel codice dopo `kde_refused` (`child.c`), non sommare «uno» a occhio.
- Cifre di prova (116/124, 123/124 …): sostituite con quelle di Fedora (F33, F35), non copiate.

# Punti NON verificati (sintesi)

1. Se il difetto del «frame perso» di KWin si presenta ancora con KWin 6.8 `--virtual` (ch06 S5).
2. Formati di cattura di labwc 0.20.2 (XBGR8888?), sonda cursore su 0.20.2, diff del sorgente di Mutter 51.1 (formati, `DEFAULT_SIZE`, `SetKeymap`, schema dconf) (ch06 S6-S7, S11; ch10 S12).
3. Che cosa fa `render_grant.c` con un nodo `renderD*` 0666 senza ACL; rotta VA-API di AMD, Intel col prodotto sulle VM, NVIDIA (ch07 S4, S6, S7, S13).
4. Più schede grafiche con KWin (F12) e DMA-BUF di KWin su RADV (`studio/5` I11, I12); ingresso EIS di KWin dopo il cambio (I10) provato solo indirettamente.
5. Slab a 4096×2304 e hang amdgpu su Fedora (ch06 S8); canvas 4096×2304 dal capo al capo (ch09 S7).
6. Misura sulle stringhe HEVC con Firefox 158/Chromium 157, Google Chrome su Fedora, telefono reale, DeX, Safari (ch09 S6, S17).
7. Avviso WirePlumber e riga «FIFO NOT OBTAINED» su Fedora (ch11 S3, S4); Klipper (ch11 S10).
8. Nome esatto degli argomenti dell'`ExecStart` del drop-in KDE e comportamento di `remotix --kwin-virtual` con un KWin senza `kde_output_management_v2` ≥ 22 (letti nel codice, non eseguiti).
9. Non ho letto i registri dei giri su server (log `log-final/`, `~/remotix-prove-live/`): le cifre di prova sono quelle scritte in `PIANO.md` e nel registro.
10. Non ho eseguito alcun comando di conteggio sui file `*.c` (solo `wc` su `page.html`): le costanti sono marcate «da ricontare».
