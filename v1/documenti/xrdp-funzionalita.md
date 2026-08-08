# xrdp — inventario delle funzionalità supportate

Analisi condotta sul codice sorgente originale:

- `neutrinolabs/xrdp` — versione **0.10.80** (ramo di sviluppo verso 0.11), clonato in `reference/xrdp`
- `neutrinolabs/xorgxrdp` — modulo Xorg complementare, clonato in `reference/xorgxrdp`

Nota: i sottomoduli `librfxcodec`, `libpainter` e `third_party/tomlc99` non sono inclusi nel clone
shallow (sono repo separati); il loro ruolo è comunque documentato più sotto.

---

## 1. Architettura: processi e componenti

| Componente | Eseguibile / libreria | Ruolo |
|---|---|---|
| Server RDP | `xrdp` | Listener, terminazione del protocollo RDP, window manager interno (schermata di login), encoder video |
| Session manager | `xrdp-sesman` | Daemon che gestisce il ciclo di vita delle sessioni, autenticazione, policy |
| Session executor | `xrdp-sesexec` | Un processo per sessione: avvia X server, window manager e chansrv |
| Channel server | `xrdp-chansrv` | Un processo per sessione: clipboard, drive, audio, smartcard, RAIL |
| Backend Xorg | `libxup.so` (+ xorgxrdp) | Sessione su X.Org con moduli `xrdpdev`/`xrdpkeyb`/`xrdpmouse` |
| Backend VNC | `libvnc.so` | Sessione Xvnc oppure proxy verso un server VNC qualsiasi |
| Backend RDP proxy | `libxrdpneutrinordp.so` | Proxy verso un altro server RDP (opzionale, `--enable-neutrinordp`) |
| Media center | `libmc.so` | Modulo dimostrativo/legacy |
| Libreria protocollo | `libxrdp` | Implementazione core di MS-RDPBCGR e canali |

**IPC interni** (`libipm`, socket Unix): SCP (sesman control protocol), EICP, ERCP, CCP.
L'esecuzione di sesman su host separato è stata **rimossa** (era deprecata per motivi di sicurezza):
oggi si usano esclusivamente Unix domain socket locali.

**Utility a corredo:**
`xrdp-keygen` (chiavi RSA), `xrdp-genkeymap` (generazione keymap), `xrdp-sesadmin` (amministrazione
sessioni), `xrdp-sesrun` (avvio sessione da CLI), `xrdp-dis` (disconnessione della propria sessione),
`waitforx` (attesa avvio X server), `xrdp_accel_assist` (encoding hardware), `xrdp-mkfv1`/`xrdp-dumpfv1`
(font FV1), `tcp_proxy`/`gtcp_proxy` (tool di sviluppo), `vrplayer` (player Qt su canale xrdpvr),
`xrdp-ssh-agent` (forwarding agent SSH su canale virtuale).

---

## 2. Trasporto e listener

- **TCP** su porta 3389 (default), con supporto multi-listener (più `port=` contemporanei)
- **IPv4 / IPv6** (`tcp://`, `tcp6://`), con opzione build `--enable-ipv6` / `--enable-ipv6only`
- **Unix domain socket** (`unix://`)
- **AF_VSOCK** (`vsock://<cid>:<port>`) per VM Hyper-V (`--enable-vsock`)
- **Modalità vmconnect**: supporto esteso ai protocolli di sicurezza quando xrdp gira dentro una VM
  Hyper-V raggiunta via `vmconnect`
- Opzioni socket: `tcp_nodelay`, `tcp_keepalive`, dimensione buffer send/recv
- **Fork per connessione** (`fork=true`) e **privilege drop** su `runtime_user`/`runtime_group`

---

## 3. Sicurezza e autenticazione

### 3.1 Livello di sicurezza del protocollo (`libxrdp/xrdp_iso.c`, `xrdp_sec.c`)

- **TLS** (`PROTOCOL_SSL`): versioni configurabili tra `SSLv3, TLSv1, TLSv1.1, TLSv1.2, TLSv1.3`
  (default: TLS 1.2 + 1.3), cipher suite configurabili (`tls_ciphers`), certificato + chiave X.509
- **Standard RDP Encryption** (RC4): livelli `none / low / medium / high / fips`; in modalità FIPS
  si usa 3DES + SHA1 MAC. Implementazione RC4 interna quando si compila con OpenSSL 3
- **Politica**: `security_layer = tls | rdp | negotiate`
- **NLA / CredSSP (`PROTOCOL_HYBRID`, `HYBRID_EX`)**: **non implementato** come autenticazione reale —
  viene selezionato **solo** in modalità `vmconnect` (dove è l'hypervisor a gestirlo). Vedi
  `xrdp_iso.c:121` — *"At present we only support SSL and RDP security"*
- **RDSTLS**: solo riconosciuto nella tabella dei nomi, non negoziabile
- **RemoteGuard**: esplicitamente rifiutato
- Blocco automatico di RDP classico su macchine in FIPS mode
- Debug: log dei TLS pre-master secret (`tls_pms_log_file`) per analisi con Wireshark

### 3.2 Licensing

Implementazione minimale di MS-RDPELE: il server risponde alla richiesta di licenza con un
`ERROR_ALERT / STATUS_VALID_CLIENT` (nessun license server, nessuna CAL).

### 3.3 Autenticazione utente (`sesman/libsesman/`)

- **PAM** (default, `--enable-pam`) con file di configurazione PAM installati per distro
- **BSD auth** (`--enable-bsd`)
- Modulo `authmod`/`authtest` per test dei backend
- **Controllo gruppi**: `TerminalServerUsers` (accesso), `TerminalServerAdmins` (amministrazione),
  `AlwaysGroupCheck`
- `AllowRootLogin`, `MaxLoginRetry`
- **Autologon**: credenziali passate dal client nel `TS_INFO_PACKET` (flag `INFO_AUTOLOGON`),
  sezione `autorun=`
- `require_credentials` — obbliga il passaggio di credenziali da riga di comando client
- `enable_token_login` — autenticazione basata sullo userid già validato (scenari smartcard/token)
- `domain_user_separator` — concatenazione dominio+utente (utile con SSSD)
- `pamerrortxt` — messaggio personalizzato in scenari gateway (es. password scaduta)
- Propagazione errori PAM alla UI (password scaduta, account bloccato, ecc.)
- **Registrazione sessione in `utmp`/`wtmp`/`lastlog`** (`--enable-utmp`)
- Gestione **Xauthority** (opzionalmente in system dir), `XorgNoNewPrivileges` per AppArmor

---

## 4. Protocollo RDP — livello core (`libxrdp/`)

### 4.1 Stack implementato

TPKT/X.224 (`xrdp_iso.c`) → MCS (`xrdp_mcs.c`) → Security (`xrdp_sec.c`) → RDP (`xrdp_rdp.c`)
→ canali virtuali (`xrdp_channel.c`), ordini di disegno (`xrdp_orders.c`), surface commands
(`xrdp_surface.c`), fastpath (`xrdp_fastpath.c`).

Specifiche Microsoft referenziate nel codice (per numero di occorrenze):
**MS-RDPBCGR**, **MS-RDPERP** (RAIL), **MS-RDPEDYC** (canali dinamici), **MS-RDPEFS** (device
redirection), **MS-RDPESC** (smartcard), **MS-RDPECLIP** (clipboard), **MS-RDPEGDI**,
**MS-RDPEDISP** (display control), **MS-FSCC**, **MS-RDPRFX**, **MS-ERREF**, **MS-RDPELE**,
**MS-SMB2**, **MS-RDPEGFX**, **MS-RDPEAI** (audio input), **MS-RDPEPC**, **MS-LCID**.

### 4.2 Capability set negoziati in ingresso (`xrdp_caps.c`)

`GENERAL`, `BITMAP`, `ORDER`, `BITMAPCACHE` (rev1 e rev2), `CACHE_V3_CODEC_ID`, `CONTROL`,
`ACTIVATION`, `POINTER`, `SHARE`, `COLORCACHE`, `SOUND`, `INPUT`, `FONT`, `BRUSH`, `GLYPHCACHE`,
`OFFSCREENCACHE`, `VIRTUALCHANNEL`, `DRAWNINEGRIDCACHE`, `DRAWGDIPLUS`, `RAIL`, `WINDOW`,
`MULTIFRAGMENTUPDATE`, `LARGE_POINTER`, `FRAME_ACKNOWLEDGE`, `SURFACE_COMMANDS`, `BITMAP_CODECS`.

### 4.3 Ordini di disegno supportati (annunciati in Demand Active)

Attivi: `DSTBLT`, `PATBLT`, `SCRBLT`, `MEMBLT`, `LINETO`, `OPAQUE_RECT`, `MULTIOPAQUERECT`,
`GLYPH_INDEX`, `POLYLINE` e relativi.
Non attivi: `MEM3BLT`, `SAVEBITMAP`, `DRAWNINEGRID`, varianti V2, `FAST_INDEX`, testo esteso.

Supportati inoltre: `refreshRectSupport`, `suppressOutputSupport`, **fastpath input e output**
(`use_fastpath = input | output | both | none`).

### 4.4 Caching

Bitmap cache (rev 1 / rev 2 persistente), glyph cache, brush cache, offscreen bitmap cache,
color cache, cache dei puntatori. Compressione bitmap (`xrdp_bitmap_compress.c`, `xrdp_bitmap32_compress.c`)
e compressione bulk MPPC (`xrdp_mppc_enc.c`).

### 4.5 Puntatore del mouse

Cursori monocromatici e a colori (`new_cursors`), cursori a 32 bpp, **large pointer** (96×96),
cache dei cursori.

---

## 5. Pipeline grafica e codec

### 5.1 Codec legacy (surface commands / bitmap update)

- **RemoteFX (RFX)** — via `librfxcodec` (con ottimizzazioni SIMD x86), disattivabile con `--disable-rfxcodec`
- **NSCodec** — riconosciuto in negoziazione
- **JPEG** — `--enable-jpeg` (libjpeg) o `--enable-tjpeg` (libjpeg-turbo)
- **Planar / RAW** bitmap
- `libpainter` — libreria di rasterizzazione software (disattivabile con `--disable-painter`)
- Ottimizzazione regioni via **pixman** (`--enable-pixman`) o implementazione interna inclusa

### 5.2 Pipeline EGFX / MS-RDPEGFX (`xrdp/xrdp_egfx.c`)

Versioni di capability supportate: **8.0, 8.1, 10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7**.

Codec trasportati sulla pipeline EGFX: **H.264 (AVC420)** e **RemoteFX Progressive**
(`WIRETOSURFACE_2` con `RFX_FLAGS_RLGR1 | RFX_FLAGS_PRO1`, encoder in `xrdp_encoder.c:1112`),
con un contesto codec indipendente per ciascuno dei 16 monitor.

Comandi implementati: `CREATESURFACE`, `DELETESURFACE`, `MAPSURFACETOOUTPUT`, `SOLIDFILL`,
`SURFACETOSURFACE`, `STARTFRAME`, `ENDFRAME`, `CAPSCONFIRM`, `WIRETOSURFACE_1/2`, `RESETGRAPHICS`,
più gestione di `FRAMEACKNOWLEDGE`, `CAPSADVERTISE`, `QOEFRAMEACKNOWLEDGE`.
(`CACHEIMPORTOFFER`, `SURFACETOCACHE`, `CACHETOSURFACE`, `MAPSURFACETOWINDOW` e le varianti *scaled*
sono definiti ma non attivi.)

### 5.3 Encoder H.264

- **x264** (`--enable-x264`) e **OpenH264** (`--enable-openh264`), selezionabili a runtime
- **NVENC** (`--enable-nvenc`) tramite il processo `xrdp_accel_assist`, con backend **EGL** e **GLX**,
  shader di conversione colore, pensato per GPU NVIDIA / NVIDIA GRID
  (variabili `XRDP_USE_ACCEL_ASSIST`, `XRDP_NVIDIA_GRID`)
- Configurazione dichiarativa in **`gfx.toml`**: ordine di preferenza codec (`["H.264", "RFX"]`),
  scelta encoder, e profili per tipo di connessione RDP: `lan`, `wan`, `broadband_high`,
  `broadband_low`, `satellite`, `modem` — con preset, tune, profile, bitrate VBV, fps, thread

### 5.4 Frame rate e throttling

Intervalli di cattura configurabili per sessione (`xrdp.ini`, sezione `[Xorg]`):
`h264_frame_interval=16`, `rfx_frame_interval=32`, `normal_frame_interval=40` (ms).
Frame acknowledgement per il controllo di flusso.

### 5.5 Profondità colore

`max_bpp` fino a **32 bpp**; xorgxrdp lavora internamente a 24 bpp e xrdp converte per il client.
Disconnessione/riconnessione alla stessa sessione con profondità colore diverse.

---

## 6. Display: multi-monitor e ridimensionamento

- **Multi-monitor** fino a **16 monitor** (`CLIENT_MONITOR_DATA_MAXIMUM_MONITORS`), abilitabile con
  `allow_multimon`
- **Ridimensionamento alla connessione**: lo schermo viene adattato alla risoluzione del client
- **Ridimensionamento dinamico (on-the-fly)** tramite **MS-RDPEDISP** / canale `Microsoft::Windows::RDS::DisplayControl`:
  gestione di `DISPLAYCONTROL_PDU_TYPE_CAPS` e `MONITOR_LAYOUT`, con macchina a stati dedicata in
  `xrdp_mm.c`
- Riconfigurazione dei monitor lato X tramite **RandR** (`rdpRandR.c`, `rdpLRandR.c` in xorgxrdp)
- **DPI**: `default_dpi`, selezione automatica del font di login in base al DPI del monitor
- Il backend VNC supporta il resize via `SetDesktopSize` / `ExtendedDesktopSize` (con maschera per
  disabilitare encoding su server VNC problematici)

---

## 7. Canali virtuali

### 7.1 Canali statici (abilitabili singolarmente, globalmente e per sessione)

| Canale | Funzione |
|---|---|
| `cliprdr` | Clipboard bidirezionale |
| `rdpdr` | Device redirection (drive, smartcard) |
| `rdpsnd` | Audio in uscita |
| `drdynvc` | Trasporto per canali dinamici |
| `rail` | Remote Applications Integrated Locally |
| `xrdpvr` | Redirezione video/audio proprietaria xrdp (`--enable-xrdpvr`) |

Controllo globale con `allow_channels` e sezione `[Channels]`; override per sessione con
`channel.<nome>=true|false`.

### 7.2 Canali dinamici (MS-RDPEDYC)

Implementazione completa: `CAPABILITY`, `OPEN_CHANNEL`, `CLOSE_CHANNEL`, `DATA_FIRST`, `DATA`,
con de-chunking dei messaggi frammentati. Usato per EGFX, DisplayControl e audio input.

### 7.3 API applicativa

`xrdpapi` espone un'API stile **WTSVirtualChannel** (`WTSVirtualChannelOpen`, `...OpenEx`, `Read`,
`Write`, `Close`, `Query`, `WTSQuerySessionInformation`) per permettere ad applicazioni nella sessione
di parlare direttamente con il client RDP. Esempi inclusi: `simple.c`, `connectmon.c`,
`xrdp-ssh-agent.c`.

---

## 8. Redirezione risorse (`sesman/chansrv/`)

### 8.1 Clipboard (`clipboard.c`, `clipboard_file.c`)

- **Testo** (UTF-8 / `CF_UNICODETEXT`), **immagini** (BMP/`CF_DIB`, PNG, JPEG, TIFF e altri MIME X11),
  **file** (`FileGroupDescriptorW` ↔ `text/uri-list` / `x-special/gnome-copied-files`)
- Bidirezionale, con integrazione X11 (selezione `CLIPBOARD` e `PRIMARY`, TARGETS, MULTIPLE, TIMESTAMP)
- **Restrizioni granulari** per direzione e per tipo:
  `RestrictInboundClipboard` / `RestrictOutboundClipboard` = `none | all | text,file,image`
- Compatibilità con il formato file-list di Nautilus 3 (`UseNautilus3FlistFormat`)

### 8.2 Drive redirection (`chansrv_fuse.c`, `chansrv_xfs.c`, `devredir.c`)

- Mount dei dischi locali del client nella sessione tramite **FUSE** (`--enable-fuse`)
- Filesystem virtuale interno (`xfs`) con gestione inode, path, cache
- Mount point configurabile (`FuseMountName`, con espansione `%u` = uid, `%U` = username),
  `FileUmask`, sostituzione del carattere `:` nei nomi
- Opzioni: `EnableFuseMount`, `FuseDirectIO` (coerenza immediata a scapito di performance),
  `FuseRootReportMaxFree` (workaround "No free space")
- Implementazione IRP asincroni su MS-RDPEFS/MS-FSCC (`irp.c`)

### 8.3 Audio in uscita — rdpsnd (`sound.c`)

Formati supportati (dipendenti dalle opzioni di build):
- **PCM** (sempre)
- **AAC** via FDK-AAC (`--enable-fdkaac`)
- **Opus** (`--enable-opus`)
- **MP3** via LAME (`--enable-mp3lame`)

Sorgente audio: modulo PulseAudio dedicato (`module-xrdp-sink`, da compilare a parte).
Workaround per il rumore in `mstsc.exe`: `SoundNumSilentFramesAAC`, `SoundNumSilentFramesMP3`,
`SoundMsecDoNotSend`.

#### 8.3.1 Come xrdp conduce il ritmo

*Letto in `sesman/chansrv/sound.c` 0.10.1, il 5 agosto 2026, cercando la causa dello scoppiettio.
[R] È la parte che conta di più per REMOTIX, e non stava in questo documento.*

**1. Blocchi di dimensione fissa, mai parziali.** `sound_send_wave_data` non spedisce: **accumula**
in `g_buffer`, e chiama `sound_send_wave_data_chunk` solo quando ha `g_bbuf_size` byte pieni. Quel
che avanza aspetta il prossimo giro.

| Formato | `g_bbuf_size` | a 44,1 kHz stereo |
|---|---|---|
| PCM | 8 192 byte | ≈ 46 ms |
| AAC | 4 096 byte | ≈ 23 ms |
| Opus, MP3 | 11 520 byte | ≈ 65 ms |

Il ritmo con cui PulseAudio consegna i campioni **non arriva mai al filo**: sul filo c'è solo il
ritmo del blocco. È la stessa cosa che fa `SendSamples` di FreeRDP accumulando fino a `latency`
millisecondi — e chi passa a `SendSamples2` la perde, e deve rifarla (`REFERENCE.md` R25).

**2. Un regolatore che guarda i riscontri, non l'orologio.** Ogni `WAVE` porta il proprio istante di
partenza in `g_sent_time[cBlockNo]`; ogni `WaveConfirm` produce un `time_diff`, tenuto in una
finestra mobile di **50 riscontri**. `g_best_time_diff` è la media migliore mai vista — cioè il
viaggio di andata e ritorno quando tutto va bene.

```c
if (g_time_diff > g_best_time_diff + 250)   /* il client è rimasto indietro */
{
    data_bytes = data_bytes / 4;            /* un quarto della lunghezza */
    g_memset(data, 0, data_bytes);          /* e di silenzio */
    g_time_diff = 0;
}
```

Quando il client accumula un quarto di secondo di ritardo, xrdp **butta il passato e manda
silenzio**: un salto breve, udibile, al posto di un ritardo che cresce e non torna più indietro. È
la stessa scelta di REMOTIX quando la coda supera il tetto, con un segnale diverso — xrdp misura il
viaggio, noi misuriamo la coda (i due non sono equivalenti: vedi R25).

**3. I due workaround per `mstsc`, e valgono solo per i formati compressi.** Prima di `SNDC_CLOSE`
xrdp manda `SoundNumSilentFramesAAC`/`MP3` blocchi di silenzio, e poi per `SoundMsecDoNotSend`
millisecondi non manda più niente. Servono a non lasciare il decodificatore di mstsc con mezzo
fotogramma in pancia. Sul **PCM non si applicano** (`g_client_does_fdk_aac || g_client_does_mp3lame`),
quindi non riguardano REMOTIX finché non arriva la voce 3 della fase 8.

### 8.4 Audio in ingresso — microfono (`audin.c`)

Canale dinamico **AUDIO_INPUT** (MS-RDPEAI): `VERSION`, `FORMATS`, `OPEN`, `OPEN_REPLY`,
`DATA_INCOMING`, `DATA`, `FORMATCHANGE`.
Formati riconosciuti: PCM, ADPCM, A-law, μ-law, MP3, Opus, AAC.
Opzione `--enable-rdpsndaudin` per il trasporto su canale rdpsnd.
Richiede il modulo PulseAudio `module-xrdp-source`.

### 8.5 Smartcard (`smartcard.c`, `smartcard_pcsc.c`, `pcsc/`)

Redirezione smartcard MS-RDPESC (`--enable-smartcard`) con un wrapper **PC/SC** che intercetta
`libpcsclite` nella sessione. IOCTL implementati: EstablishContext, ReleaseContext, IsValidContext,
ListReaderGroups, ListReaders (A/W), Introduce/ForgetReader(Group), Add/RemoveReaderFromGroup,
GetStatusChange (A/W), Cancel, Connect (A/W), Reconnect, Disconnect, Begin/EndTransaction, State,
Status (A/W), Transmit, Control, GetAttrib, SetAttrib.

### 8.6 RAIL — RemoteApp (`rail.c`, `libxrdp/xrdp_orders_rail.c`)

Implementazione MS-RDPERP: `HANDSHAKE`, `EXEC`, `EXEC_RESULT`, `ACTIVATE`, `SYSPARAM`, `SYSCOMMAND`,
`NOTIFY_EVENT`, `WINDOWMOVE`, `LOCALMOVESIZE`, `MINMAXINFO`, `CLIENTSTATUS`, `SYSMENU`, `LANGBARINFO`,
`GET_APPID_REQ/RESP`, più gli ordini Window List (`CAPSTYPE_WINDOW`).

### 8.7 Dispositivi NON supportati

`devredir.c:989` — **stampanti, porte seriali e porte parallele vengono rilevate ma esplicitamente
rifiutate** (`STATUS_NOT_SUPPORTED`). Nessuna redirezione USB generica, nessun printer redirection.

---

## 9. Input

- **Tastiera**: scancode set 1 (MS-RDPBCGR `TS_KEYBOARD_EVENT`), gestione `KBDFLAGS_EXTENDED`/`EXTENDED1`,
  conversione RDP scancode ↔ keycode X11 (`common/scancode.c`)
- **Mappature di tastiera**: file `km-XXXXXXXX.toml`/`.ini` per ~25 layout (US, UK, DE, FR, IT, ES, JP,
  KO, RU, PT-BR, SV, TR, PL, CS, ecc.), generabili con `xrdp-genkeymap`
- **Mappatura layout RDP → XKB** dichiarativa in `xrdp_keyboard.toml` (layout, model, variant, options,
  con override per keyboard type/subtype), usata con xorgxrdp
- Override di debug: `override_keyboard_type`, `override_keyboard_subtype`, `override_keylayout`
- Set di keycode `evdev` selezionabile (`keycode_set`)
- **Input Unicode** tramite **IBus** (`--enable-ibus`): engine `XrdpIme` che riceve caratteri Unicode
  dal client e li inietta nella sessione (supporto IME / lingue asiatiche)
- **Mouse**: eventi standard, rotella verticale e orizzontale, pulsanti estesi (via `rdpMouse.c`)
- **Fastpath input** per ridurre la latenza

---

## 10. Backend di sessione

### 10.1 Xorg + xorgxrdp (raccomandato)

Moduli xorgxrdp:
- `xrdpdev` — driver video virtuale, con supporto **DRI2** e **DRI3** e configurazioni dedicate
  (`xorg.conf`, `xorg_nvidia.conf`, `xorg_nvidia_grid.conf`)
- `xrdpkeyb` — driver tastiera
- `xrdpmouse` — driver mouse
- Accelerazione: implementazione delle primitive X (CopyArea, PolyFillRect, Glyphs, Composite,
  Trapezoids, Triangles, PutImage, ecc.), cattura schermo ottimizzata (`rdpCapture.c`) con
  **assembly SIMD x86/amd64**, supporto **EGL** (`rdpEgl.c`) e estensione **Xv** (`rdpXv.c`)
- Ridimensionamento schermo via RandR

### 10.2 Xvnc / VNC generico (`vnc/`)

- Sessioni Xvnc gestite da sesman, connessione via **TCP o Unix domain socket** (consigliato; obbligatorio
  in FIPS mode, dove il formato password VNC classico non è ammesso)
- Encoding RFB gestiti: RAW, CopyRect, Cursor, DesktopSize, **ExtendedDesktopSize**
- Clipboard VNC (`vnc_clip.c`)
- **Proxy VNC generico** (sezione `vnc-any`): connessione a qualsiasi server VNC, con host/porta
  chiesti a runtime, autenticazione PAM opzionale sovrapposta, maschera per disabilitare encoding
  su server buggati

### 10.3 Proxy RDP (`neutrinordp/`)

- Proxy verso un altro server RDP tramite NeutrinoRDP (fork di FreeRDP), opzionale in build
- Autenticazione PAM opzionale davanti al proxy (`pamusername`/`pampassword`)
- Inoltro dei canali `rdpdr`, `rdpsnd`, `cliprdr`, `drdynvc`
- Controllo delle **experience settings**: wallpaper, font smoothing, desktop composition,
  full window drag, menu animations, themes, cursor blink, cursor shadow — o passthrough di quelle
  richieste dal client (`perf.allow_client_experiencesettings`)
- Gestione layout tastiera: uso del layout remoto o propagazione di quello del client
- TLS e RDP security verso l'upstream; NLA disponibile come opzione (`nla_security`)
- Non supporta il resize dinamico

---

## 11. Gestione sessioni (sesman)

- **Riconnessione a sessione esistente** (disconnect/reconnect senza perdere lo stato)
- **Policy di allocazione sessioni** (`Policy=`): combinazione di
  - `U` — separate per utente (sempre attivo)
  - `B` — separate per bits-per-pixel (sempre attivo)
  - `D` — separate per dimensione display iniziale
  - `I` — separate per indirizzo IP del client
  - `N` — separate per **instance name** dell'istanza xrdp
  - `Separate` — ogni connessione crea una sessione nuova
- `MaxSessions`, `X11DisplayOffset`, `MaxDisplayNumber`
- **Timeout**: `KillDisconnected` + `DisconnectedTimeLimit`, `IdleTimeLimit`
- **Script di sessione**: `startwm.sh` (window manager di default), window manager per-utente
  (`EnableUserWindowManager`, `UserWindowManager=~/startwm.sh`), `reconnectwm.sh` eseguito alla
  riconnessione (`ReconnectScript`, `AlwaysRunReconnect`)
- **Alternate shell**: esecuzione di comandi arbitrari richiesti dal client, disabilitata di default
  (`AllowAlternateShell`), oppure passata al WM come variabile d'ambiente (`PassShellAsEnv`)
- **Variabili d'ambiente di sessione** configurabili (`[SessionVariables]`)
- Parametri di avvio X server totalmente configurabili per tipo di sessione (`[Xorg]`, `[Xvnc]`)
- `waitforx` per sincronizzare l'avvio dell'X server
- Amministrazione: `xrdp-sesadmin -c=list` (elenco sessioni; gli admin vedono tutte),
  `kill:<sid>` **non ancora implementato**
- Avvio sessione da CLI con `xrdp-sesrun` (geometria, bpp, tipo sessione, directory, instance name)
- `xrdp-dis` per disconnettere la propria sessione dall'interno
- Permessi della directory socket di sessione (`SessionSockdirGroup`)

---

## 12. Interfaccia utente del server (schermata di login)

Window manager interno minimale (`xrdp_wm.c`, `xrdp_bitmap.c`, `xrdp_painter.c`) con:

- Finestra di login con **combo di selezione della sessione/modulo** e campi dinamici generati in base
  al modulo scelto (username, password, host, porta…)
- Preselezione del modulo tramite il campo *domain* inviato dal client (sintassi `__<indice>`)
- Finestra di **help** e popup di errore/diagnostica; log a video (`hidelogwindow` per nasconderlo)
- **Personalizzazione grafica completa**: titolo, colori (grey, dark_grey, blue, dark_blue, background,
  colore finestra top-level), dimensioni e posizione di ogni elemento (label, input, pulsanti OK/Cancel)
- **Logo** e **immagine di sfondo**: BMP sempre supportato, altri formati (PNG, JPEG…) con **imlib2**;
  trasformazioni `none` / `scale` / `zoom`
- **Font vettoriali FV1** proprietari con selezione automatica in base al DPI (`fv1_select`),
  rendering opzionale con **FreeType2**; utility `xrdp-mkfv1` / `xrdp-dumpfv1`
- Localizzazione parziale dei messaggi (`lang.c`)

---

## 13. Logging e diagnostica

- Log separati per `xrdp`, `xrdp-sesman` e `xrdp-chansrv` (un file per display)
- Livelli: `core, error, warning, info, debug, trace`
- Destinazioni: file, **syslog**, console — ognuna con livello indipendente
- `EnableProcessId`, percorso log configurabile (utile per home NFS)
- **Logging per-logger** (per file sorgente o per funzione) con `--enable-devel-logging`
- Opzioni di build per lo sviluppo: `--enable-devel-debug`, `--enable-devel-streamcheck`,
  `--enable-xrdpdebug`, `--enable-tests` (suite di unit test in `tests/`)
- Modalità debug con connessione diretta a un display già attivo (`port=/tmp/.xrdp/xrdp_display_10`)

---

## 14. Deployment e piattaforme

- **Target primario**: GNU/Linux (x86, x86-64, ARM). Supporto anche **FreeBSD** (BSD auth, UTX)
- Integrazione **systemd** (`xrdp.service`, `xrdp-sesman.service`) e **init.d** / **rc.d**
- File PAM preconfigurati per le principali distribuzioni
- Configurazione PulseAudio di sessione (`instfiles/pulse/default.pa`)
- Build system autotools con ~30 opzioni `--enable-*` / `--with-*`

---

## 15. Sintesi delle lacune (rilevanti per un progetto nuovo)

| Area | Stato in xrdp |
|---|---|
| NLA / CredSSP lato server | Non implementato (solo passthrough vmconnect) |
| RDSTLS | Non implementato |
| RemoteGuard | Rifiutato esplicitamente |
| Redirezione stampanti | Non supportata |
| Redirezione porte seriali/parallele | Non supportata |
| Redirezione USB generica | Non supportata |
| Camera redirection (MS-RDPECAM) | Assente |
| Location/geolocation redirection | Assente |
| Multitransport UDP (MS-RDPEUDP / RDP 8 UDP) | Assente — solo TCP |
| Gateway RDP (MS-TSGU) | Assente |
| `xrdp-sesadmin kill:<sid>` | Non implementato |
| Resize dinamico su proxy NeutrinoRDP | Non supportato |
| Cache surface EGFX (`SURFACETOCACHE`/`CACHETOSURFACE`) | Definite ma non attive |
| Wayland nativo | Assente (solo X11 tramite Xorg/Xvnc) |
