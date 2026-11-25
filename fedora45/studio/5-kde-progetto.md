# Progetto KDE su Fedora 45: KWin da solo (`kwin_wayland --virtual`), senza labwc

21 nov 2026. Decisione D2 del proprietario. Solo progetto e prove con sonde fuori dall'albero: **`src/` non è stato toccato**.
Legenda: **[V]** verificato sulla VM `kde` (Plasma 6.8.1, KWin 6.8.1; sorgenti 6.8.3 letti), **[S]** supposizione.
Sonde (mie, NON codice del prodotto): `/media/REMOTIX-FEDORA/tmp/kde-sonde/` sul server (`rxout.c` cambio modo, `rxcast.c` cattura
screencast + metadati, `rxptr.c` puntatore, `rxpix.c` pixel e «poke», script `c*.sh h*.sh g*.sh x1.sh`).
Installato nella VM `kde` per le prove (si perde col ritorno a `codec`): `gcc make wayland-devel plasma-wayland-protocols-devel
pipewire-devel xterm weston-demo xdpyinfo chromium` (+ `wayland-utils`, `pipewire-utils` già presenti).

## 1. Giudizio

**La strada «KWin da solo» regge, con tre accorgimenti obbligatori** (§5): (1) la dimensione di nascita non è garantita (KWin
ricorda l'ultimo modo in `~/.config/kwinoutputconfig.json`), quindi va verificata e corretta alla nascita con la stessa funzione del
cambio a caldo; (2) per le dimensioni dispari serve `add_cvt` (protocollo v22: KWin 6.8; con v<22 niente larghezze non multiple di 8);
(3) lo stream non segue il cambio di modo: il montaggio dopo il cambio, che il codice già fa, resta indispensabile.
Provato con la Radeon, **senza il prodotto**: sessione Plasma vera su `--virtual`, 7 cambi di risoluzione fra 800x600 e 3840x2160 (anche
dispari), flusso 60 fps a ogni dimensione, Firefox, Chromium e programmi X11 vivi, cursore con metadati, uscita pulita in 6 s.
**Non provato** (serve il prodotto): ingresso EIS dopo il cambio, DMA-BUF verso il codificatore, forma del cursore, più GPU (§6).

## 2. Come funziona oggi e che cosa cambia

Oggi (copia di Ubuntu): la riga `ExecStart` del drop-in di `plasma-kwin_wayland.service` avvia `remotix --kwin-nested W H NODO -- kwin_wayland_wrapper …`
(`session.c:3902-3957`), che avvia un labwc nostro senza schermo, un «ticker» e il sidecar `org.freedesktop.ScreenSaver`, poi fa `exec` di KWin
annidato; il cambio di dimensione è `kwin_host_resize()` (cambia l'uscita di labwc).

**Nuovo**: il drop-in diventa `ExecStart=remotix --kwin-virtual W H -- kwin_wayland_wrapper --virtual --xwayland --width W --height H --no-lockscreen`.
`remotix --kwin-virtual` fa solo il sidecar ScreenSaver (doppia `fork`, invariato) e `exec` del wrapper. Provato a mano senza il nostro eseguibile: la
sessione Plasma nasce (ksmserver, kded6, plasmashell, Xwayland `-rootless`, `--socket wayland-N`) [V].

### File per file
- `session.c` `write_dropin()` ramo KDE: nuova riga; via la scelta della scheda per KWin (`card_node()`, `card_say("KDE")`, `node_arg`); `expected` = `--kwin-virtual W H`.
  Resta `XDG_MENU_PREFIX=plasma-`, niente `WAYLAND_DISPLAY`/`DISPLAY`/`XDG_CURRENT_DESKTOP` nell'ambiente (con quelli KWin sceglierebbe il backend annidato).
- `kwin.c`: nuova funzione `kwin_output_resize(W, H, wait_s, GError**)` al posto di `kwin_host_resize()`; `kwin_host_settle()` diventa «misura l'uscita e, se
  diversa dalla voluta, ridimensiona» (stessa funzione). `kwin_open()`, `put_pixel()`/`kwin_poke()`, EIS, `kwin_layout()`, appunti e sidecar ScreenSaver: invariati.
  La modalità `--kwin-nested` si riduce a: sidecar + `exec` (rinominata `--kwin-virtual`).
- `kwin.h`: riscrivere il riquadro «THE NESTED KWIN»; dichiarazioni nuove/tolte.
- `kdehost.h`: `KDEHOST_OPTION` = `--kwin-virtual`. Il segno `remotix-kwin-host` (cartella di labwc nella riga di comando) non c'è più: dopo l'`exec`
  resta il sidecar (stessa riga di comando di prima dell'exec) a identificare «nostro». **Punto fragile**: se il sidecar muore l'unità risulta «estranea» e
  non viene fermata a fine sessione. Cura proposta: secondo segno, `Environment=REMOTIX_KDE_HOST=1` nel drop-in, letto da `/proc/<pid>/environ`
  (root e lo stesso utente possono leggerlo). `rootside.c` e `child.c` usano `kdehost_*` senza cambiare.
- `main.c:2886`: dispatch `--kwin-virtual`. `child.c:8950` (`kwin_host_settle`) e `child.c:11330-11375` (resize) usano le funzioni nuove; l'ordine
  smonta → ridimensiona → rimonta resta (§3, I1). `Makefile`: via `LABWC`/`-DREMOTIX_LABWC`; generare il codice dei due protocolli nuovi.
- `src/protocols/`: aggiungere `kde-output-device-v2.xml` (v26) e `kde-output-management-v2.xml` (v22), presi da plasma-wayland-protocols (master: il pacchetto
  Fedora 1.23.0 non li contiene) [V: il KWin 6.8.1 offre `kde_output_management_v2` v22, `kde_output_device_registry_v2` v26].
- Pacchetto: nessun `labwc` per KDE (resta `Recommends` per XFCE/LXQt); `org.kde.remotix.desktop` si tiene (innocuo, studio 2 §0.3).

### Il cambio di modo (provato con `rxout`)
Client Wayland nel figlio (socket di `kwin_display_open`): lega `kde_output_device_registry_v2` e `kde_output_management_v2`; legge l'unica uscita
(`Virtual-0`, capability `custom_modes` 0x2000); se `current_mode` ≠ voluto: `create_mode_list` → `add_cvt(clock, W, W+48, W+80, W+160, 0, H, H+3, H+8, H+20, 0, 0)`
con `clock = htotal·vtotal·60/1000` → `create_configuration` + `set_custom_modes(uscita, lista)` + `apply` → attesa `applied` →
(il nuovo modo compare nella lista) `mode(uscita, nuovo)` + `apply` → rilettura di `current_mode`. Misurato: ~3 ms per passo. Ogni `set_custom_modes`
**sostituisce** i modi personalizzati precedenti (nessun accumulo). Con `set_resolution/set_refresh_rate` le larghezze non multiple di 8 spariscono in silenzio:
`add_cvt` accetta qualsiasi misura (provati 1367x768, 1365x767, 1001x601, 1919x1079, 320x240, 8192x4320).

## 3. Codice del labwc-per-KDE che su Fedora diventa morto (da NON togliere ancora)
`kwin.c`: parte labwc di `kwin_nested_alive()` (`host_folder`, `HOST_RC`, `host_wanted_*`, `host_ask_size`, `ticker_*`, fork di labwc), `kwin_host_resize/settle/exists/display`,
`mode_*` (lettura wl_output), uso di `wlroots.h`; `kwin.h` (riquadro e 5 funzioni `kwin_host_*`); `kdehost.h` (`KDEHOST_MARK`, `KDEHOST_DROPIN` resta); `Makefile` (`LABWC`);
`session.c` (scelta scheda per KWin; `SESSION` nota «NESTED»); `child.c` (rami `kwin_host_exists()`, messaggi «DECLARED FALLBACK» del `--virtual`).
Restano usati da XFCE/LXQt: `wlroots.c` (`wlr_open_on`, `wlr_ask_size`), `card_pick`, `render_node`.
**Identico**: cattura (`kwin_open`, `capture.c`, danno, cursore a metadati, tema-cursore codificato di `shape.c`), ingresso EIS, tastiera, appunti `ext_data_control`,
pixel e `kwin_poke`, sidecar ScreenSaver, ambiente di sessione, `session_kde_logout_watch`, uscita via `org.kde.Shutdown`, `--xwayland`, `--no-lockscreen`.

## 4. Esito delle incognite (VM `kde`; virtuale = scheda software, Radeon = RX 6800)

| # | Incognita | Prova fatta | Esito |
|---|---|---|---|
| I1 | Cattura dopo il cambio di risoluzione | `rxcast` + `rxout`: stream aperto, uscita cambiata a caldo | **Lo stream NON segue**: resta alla dimensione di apertura (frame 1280x720 a 60 fps mentre l'uscita è 1920x1080/1367x768), nessuna rinegoziazione. Uno stream NUOVO aperto dopo il cambio negozia la dimensione offerta dal consumatore (qualsiasi, anche diversa dall'uscita: KWin ridimensiona). **PASSA** con smonta→cambia→rimonta (come già fa il codice): 7 cicli (1920x1080, 1367x768, 800x600, 1366x769, 2560x1440, 3840x2160, 1280x720) con la Radeon, 60 fps a ogni dimensione. Uscita senza danni: nessun fotogramma (serve il poke). |
| I2 | Cursore | Radeon, flusso con puntatore mosso da `fake_input` | **PASSA** (sonda): metadati `id`, posizione (cambia col puntatore), hotspot, bitmap 24x24 al primo buffer. Con l'offerta «meta a intervallo» come `capture.c`; con dimensione FISSA KWin non manda i metadati. Con il puntatore in moto i buffer sono «solo cursore» (flag CORRUPTED, 22 su 23): è il caso che `capture.c` già scarta. **Da provare col prodotto**: forma (tema codificato), posizione dopo un cambio. |
| I3 | Programmi X11 | `xdpyinfo` e `xterm` su Xwayland durante 6 cambi (virtuale) e 7 (Radeon) | **PASSA**: la radice X segue subito (1920x1080, 1367x768, … 3840x2160); `xterm` vivo. Serve `XAUTHORITY` (quello che KWin passa a Xwayland). |
| I4 | Chrome | Chromium 157 (Wayland, GPU Radeon) animato, 4 cambi inclusi 3840x2160 | **PASSA**: 60 fps a ogni dimensione, nessun core dump. Firefox 158 (Wayland) e `xterm` vivi nei 7 cicli. (Provato Chromium del repository Fedora, non Google Chrome.) |
| I5 | Uscita pulita | sessione Plasma vera su `--virtual` (Radeon), `org.kde.Shutdown.logout` | **PASSA** (una prova): dopo 6 s nessun `kwin_wayland`, `plasmashell`, `ksmserver`, `kded6`, `Xwayland`; `plasma-kwin_wayland.service` e `graphical-session.target` inattivi. Da ripetere con il prodotto (chiusura forzata, orfano A1, stop del servizio). |
| I6 | Dimensione di nascita | due sessioni: A a 1366x768 (poi portata a 1920x1080 e chiusa), B con `--width 1280 --height 720` | **NON PASSA da solo**: B nasce a **1920x1080** (e ci resta): KWin ricorda l'ultimo modo in `~/.config/kwinoutputconfig.json` (`customModes` + modo corrente di `Virtual-0`). `--width/--height` vale solo la prima volta. ⇒ la nascita va verificata e corretta con `kwin_output_resize` (§2). Effetto collaterale: il file di KWin nella casa dell'utente contiene una voce `Virtual-0` (non nostra da cancellare; innocua; da dichiarare nel manuale). |
| I7 | Pixel in cima e «poke» | `rxpix`: layer-shell overlay 1x1 trasparente come `put_pixel()` | **PASSA**: KWin offre `zwlr_layer_shell_v1` v5 e configura il pixel 1x1; desktop fermo = nessun fotogramma; ogni commit con danno = un fotogramma (`kwin_poke` funziona). |
| I8 | Sessione Plasma sul backend virtuale | drop-in + `startplasma-wayland` (Radeon, 1600x900) | **PASSA**: ksmserver, kded6, plasmashell, Xwayland; vivi dopo i cambi (1920x1080, 1366x768, 1600x900). |
| I9 | Protocolli presenti | `wayland-info` | `zkde_screencast_unstable_v1` v6, `ext_data_control_manager_v1` v1 (niente `zwlr_data_control`), `org_kde_kwin_fake_input` v6, `zwlr_layer_shell_v1` v5: come atteso. Il probe lega lo screencast a v5 come `kwin.c`. |
| I10 | Ingresso (EIS) dopo il cambio | non provata | **Da provare col prodotto**: le regioni del dispositivo EIS seguono la nuova uscita? Criterio: clic a (0,3·W; 0,3·H) del canvas arriva alla finestra di prova, prima e dopo 3 cambi. |
| I11 | DMA-BUF verso il codificatore | la sonda negozia memoria condivisa (`memfd`, tipo 2) | **Da provare col prodotto**: modificatori DMA-BUF di KWin su RADV, nodo scelto dal codificatore uguale alla GPU di KWin. |
| I12 | Più di una GPU | non provabile (un solo adattatore) | **Non provata**: il backend virtuale non sceglie la scheda (la dà il nucleo di KWin); REMOTIX sceglie quella di codifica (`card_pick`). Con Intel+dedicata potrebbero divergere. Prova: portatile a due schede, `KWIN_DRM_DEVICES` o nodo di rendering, criterio: stessa scheda, nessuna copia in memoria. |
| I13 | KWin 6.8.3 | non provata (la VM ha 6.8.1; i repository 6.8.3) | **Da ripetere** `rxout`/`rxcast` dopo `dnf upgrade kwin`. |

## 5. Punti in cui la strada potrebbe non reggere
1. **KWin < 6.8** (Ubuntu 26.04 ha 6.6.7): `kde_output_management_v2` v22/`add_cvt` e il ridimensionamento a caldo di `--virtual` non ci sono. Se il codice passerà a Debian/Ubuntu serve il controllo della versione offerta e un ripiego dichiarato (canvas fisso, come il vecchio `--virtual`), oppure tenere il percorso annidato lì. Su Fedora 45 non è un problema.
2. **Persistenza di KWin** (I6): senza la correzione di nascita il desktop nasce a una dimensione sbagliata e il canvas non coincide con la richiesta. La correzione costa un cambio di modo (~6 ms) e va fatta PRIMA di montare lo stream.
3. **Ingresso EIS** (I10) e **più GPU** (I12): non verificabili senza il prodotto o senza un secondo adattatore; se le regioni EIS non seguono, serve riattaccare l'ingresso dopo il cambio (`kwin_eis_reattach`, già esiste).
4. **Segno «nostro» in kdehost** (§2): se il sidecar muore, la sessione non viene fermata alla fine; cura: secondo segno in `environ`.
5. **Rumore di sessione Plasma** (studio 2 §10: Welcome Center, akonadi, kdeconnect…) e **portafoglio** (studio 2 §5): invariati, restano decisioni/passo 6.

## 6. Piano di prova col prodotto (dopo il codice, con la Radeon)
Con `check-base.py --box kde` e i giri del proprietario: (a) accesso, desktop, mouse, tastiera (I10: clic prima/dopo il cambio); (b) ridimensionare la finestra del browser 10 volte,
anche a larghezze dispari: immagine alla misura nuova entro 1 s, nessun errore di codificatore; (c) forma del cursore (I-beam su testo, frecce di ridimensionamento) e posizione dopo un cambio;
(d) `xterm`/un programma X11 e Chromium con video (1440p) durante il cambio; (e) uscita: Log Out, `terminate-session`, `systemctl restart remotix` con desktop aperto, poi accesso locale (A1);
(f) nascita dopo una sessione chiusa a un'altra dimensione (I6) ripetuta tre volte; (g) `ausearch -m avc` vuoto con SELinux attivo.

## 7. plasmalogin e l'aggancio «il locale chiude il remoto» (solo lettura, nulla acceso)
- File PAM del fornitore in `/usr/lib/pam.d/`: `plasmalogin`, `plasmalogin-autologin`, `plasmalogin-greeter` (nessuno in `/etc/pam.d`); sessione come gdm
  (`pam_selinux close`, `pam_loginuid`, `pam_selinux open`, `pam_keyinit`, `pam_namespace`, `include password-auth`, …, `include postlogin`).
- Con `remotix-pam-hook` **così com'è** (prova su una copia con `--test-root`, nessun file di sistema toccato): per `plasmalogin` coprirebbe `plasmalogin` e
  `plasmalogin-autologin` e salterebbe `plasmalogin-greeter` (esclusione `*-greeter`); il blocco entra prima della prima riga `session`. Basterebbe attivarlo con
  `DEFAULT_DMS="gdm plasmalogin"` e il trigger `%triggerin -- plasma-login-manager`.
- **Da provare al suo turno** (come per gdm): che `plasmalogin-helper` metta `XDG_SEAT`/`XDG_SESSION_TYPE` nell'ambiente PAM PRIMA di `pam_selinux open` (se non li mette, la riga
  prima della prima `session` non vede il posto e non fa nulla; la riga dopo `pam_systemd` sbatte contro `pam_selinux`: vedi registro F6). Studio 2 §4.3 ha misurato l'ambiente solo DOPO `pam_systemd`.

## 8. Realizzazione (21 nov 2026, dopo l'approvazione) — che cosa è stato scritto e che cosa è ancora morto
**Scritto** (file toccati: `src/kwin.c`, `src/kwin.h`, `src/kdehost.h`, `src/session.c`, `src/child.c`, `src/main.c`, `src/Makefile`, `src/protocols/kde-output-*.xml` + `README-kde-output.txt`,
`src/remotix-pam-hook`, `rpm/remotix.spec`, `THIRD-PARTY-LICENSES`): drop-in con `remotix --kwin-virtual` e `REMOTIX_KDE_HOST=1`; `kwin_output_resize()` (generico, per nome degli eventi);
la nascita verificata sempre con la stessa funzione; rifiuto pulito se manca il protocollo; segno doppio in `kdehost.h`; plasmalogin nel gancio del locale. XML da plasma-wayland-protocols commit `cd65734cccdf`, licenza MIT-CMU.
**Ancora nel codice ma NON raggiungibile su KDE** (rimozione vera dopo le prove del proprietario): `kwin.c`: `kwin_nested_alive()` (labwc, ticker), `host_*`, `kwin_host_resize/settle/exists/display`, `mode_*`, `ticker_*`;
`kwin.h`: il riquadro «nested» e le dichiarazioni `kwin_host_*`, `kwin_nested_alive`; `child.c`: il ramo «this Plasma session has no host…» dopo il cambio (mai raggiunto); `main.c`: `--kwin-nested` risponde con un errore;
`Makefile`: `LABWC` / `-DREMOTIX_LABWC` (solo una stringa nel codice morto: il pacchetto NON costruisce né installa un labwc statico); `wlroots.c` e `card_pick` restano (XFCE/LXQt).
**Prove col prodotto (VM `kde`, Radeon)**: vedi il rapporto e `docs/REGISTRO-problemi.md`, sezione F (F7-F9).

## 9. Correzioni del revisore (22 nov 2026)
`kwin_output_resize` ora ha una scadenza vera (poll sul descrittore), distingue connessione persa da timeout, libera i proxy e controlla i NULL; limiti scritti nel commento. Errori: uscita esistente ma KWin dice no o tace -> si monta alla misura di KWin (ripiego dichiarato);
senza protocollo -> una riga, 0x0E all'utente e sessione chiusa (strada del rifiuto per la scala; `kde_refused` impedisce di rinascere); non pronto -> si ritenta con una riga ogni 5 s.
Prove: vedi `docs/REGISTRO-problemi.md` F13-F16.
