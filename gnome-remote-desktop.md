# gnome-remote-desktop — studio del codice e delle funzionalità

Analisi condotta sul codice sorgente originale, clonato da `gitlab.gnome.org/GNOME/gnome-remote-desktop`:

- **51.alpha** (commit `038caa60`, 9 luglio 2026) — ramo di sviluppo, usato come riferimento principale
- **48.2** — la versione che accompagna GNOME 48, cioè quella di **Debian Trixie**, la piattaforma di
  runtime di REMOTIX. Le differenze rispetto alla 51 sono in §17

Dimensione: **68 730 righe di C** in ~200 file, più gli XML delle interfacce D-Bus e gli shader.

Perché questo documento esiste: la specifica di REMOTIX cita `gnome-remote-desktop` ogni volta che un
problema si è risolto (§5.4, §5.8, §5.10, questione aperta n.9), e ogni volta lo ha consultato a pezzi.
La lezione di metodo scritta in §5.4 — *«studiare il riferimento viene prima di ipotizzare»* — chiede
che il riferimento sia studiato **una volta sola e per intero**. Il §18 raccoglie il conto: cosa
conferma delle decisioni di REMOTIX, cosa le smentisce, e cosa conviene copiare.

> **E dal 3 agosto 2026 conta molto di più.** Con i vincoli posti dall'utente — **linguaggio C** e
> **FreeRDP 3** (§8-bis di `SPECIFICA.md`) — REMOTIX e `gnome-remote-desktop` condividono linguaggio,
> libreria RDP, compositore e client. Quello che segue non è più materiale di confronto: è codice
> leggibile e, dove serve, trasferibile.

---

## 1. Che cos'è

Il server desktop remoto del progetto GNOME. Non è un desktop e non è un compositore: **parla al
compositore**, esattamente come REMOTIX. Due backend di protocollo, **RDP** (predefinito, su FreeRDP 3)
e **VNC** (opzionale, su LibVNCServer, disattivato di default in build).

I mattoni sono gli stessi che REMOTIX ha scelto: **PipeWire** per i pixel, **libei** per l'input,
**API RemoteDesktop di Mutter** per la gestione di alto livello.

Licenza GPL v2 o successiva. Autori principali: Jonas Ådahl (architettura, sessione) e Pascal Nowack
(tutto il grosso del backend RDP).

---

## 2. I quattro modi di funzionamento

Sono la struttura portante di tutto il programma: un solo eseguibile, quattro `GrdRuntimeMode`
(`grd-daemon.c:1198`), ciascuno con la propria classe di daemon e la propria classe di impostazioni.

| Modo | Opzione | Classe | Bus | A cosa serve |
|---|---|---|---|---|
| `SCREEN_SHARE` | *(nessuna)* | `GrdDaemonUser` | sessione | Assistenza remota: ci si attacca alla sessione già attiva di chi è seduto davanti |
| `HEADLESS` | `--headless` | `GrdDaemonUser` | sessione | Utente singolo, sessione grafica senza schermo avviata a parte |
| `SYSTEM` | `--system` | `GrdDaemonSystem` | **sistema** | Accesso remoto multiutente: fa da portiere davanti a GDM |
| `HANDOVER` | `--handover` | `GrdDaemonHandover` | sessione | Il processo che riceve la connessione consegnata dal modo `SYSTEM` |

Unità systemd corrispondenti: `gnome-remote-desktop.service` (utente, per screen share),
`gnome-remote-desktop-headless.service` (utente), `gnome-remote-desktop.service` (sistema).

**Il modo che assomiglia a REMOTIX è `HEADLESS`**: una sola sessione, un solo utente, il server gira
dentro la sessione. Gli altri tre risolvono problemi che REMOTIX ha messo fuori scope (§4.2 della
specifica: multi-tenancy e amministrazione).

### 2.1 Il passaggio di consegne con GDM (`SYSTEM` → `HANDOVER`)

È il meccanismo che la specifica di REMOTIX cita in §5.6 come *«quel passaggio esiste perché
gnome-remote-desktop deve agganciarsi alla schermata di accesso»*. Il codice conferma: sta tutto in
`grd-daemon-system.c` (1520 righe) e `grd-daemon-handover.c` (911 righe), ed è la parte più
complicata dell'intero programma.

Come funziona, in breve:

1. il daemon di sistema gira come utente dedicato `gnome-remote-desktop`, sul **bus di sistema**, e
   ascolta sulla 3389;
2. all'arrivo di una connessione **sbircia i primi byte del socket** (`grd-rdp-routing-token.c`)
   cercando il prefisso `Cookie: msts=` del Routing Token, senza consumarli — con un tetto di 2
   secondi;
3. se il token non c'è, è un client nuovo: si autentica contro una credenziale di sistema, e attraverso
   `org.gnome.DisplayManager.RemoteDisplayFactory` chiede a GDM di creare una sessione di accesso;
4. quella sessione avvia un secondo `gnome-remote-desktop --handover`, che espone
   `org.gnome.RemoteDesktop.Rdp.Handover` sul bus di sessione;
5. il daemon di sistema manda al client una **Server Redirection PDU** (`grd_session_rdp_send_server_redirection`)
   con routing token, credenziali e certificato del bersaglio;
6. il client si ricollega, questa volta col token; il daemon di sistema riconosce il token e **passa
   il socket** al processo handover, che serve la sessione.

Il livello di sicurezza del secondo collegamento è **RDSTLS** (`FreeRDP_RdstlsSecurity = TRUE`,
`grd-session-rdp.c:1547`) — cioè proprio quello che xrdp ha in tabella ma non implementa.

Per REMOTIX questo capitolo è **interamente fuori scope**, ma va letto una volta perché spiega perché
il resto del programma è fatto come è fatto.

---

## 3. Architettura dei processi

Un solo eseguibile principale, `gnome-remote-desktop-daemon` (in `libexecdir`), più tre utilità:

| Binario | Ruolo |
|---|---|
| `gnome-remote-desktop-daemon` | Il server vero, in tutti e quattro i modi |
| `grdctl` | Configurazione da riga di comando (gsettings + credenziali) |
| `gnome-remote-desktop-configuration-daemon` | Espone la configurazione su D-Bus per il pannello Impostazioni |
| `gnome-remote-desktop-enable-service` | Abilita l'unità di sistema passando per polkit |

**Nomi sul bus** (`grd-private.h`): `org.gnome.RemoteDesktop.User`, `.Headless`, `.Handover` sul bus
di sessione; `org.gnome.RemoteDesktop` sul bus di sistema.

**Thread** — sono quattro famiglie, e la divisione conta perché è la stessa che REMOTIX ha dovuto
inventarsi (§5.7 regola 7, §5.8 regola 3):

| Thread | Chi lo crea | Cosa fa |
|---|---|---|
| principale (`GMainContext` di default) | GLib | D-Bus, logind, ciclo di vita delle sessioni, layout manager |
| **socket** (uno per sessione RDP) | `grd_session_rdp_new` | `WaitForMultipleObjects` sugli handle FreeRDP, legge il protocollo |
| **grafica** (uno per sessione) | `grd_rdp_renderer_start` | `GMainContext` privato: codifica, invio dei frame EGFX |
| **EGL** (uno per processo) | `GrdContext` | Tutte le operazioni GL/EGL, che devono stare su un thread solo |
| PipeWire (uno per stream) | `pw_context` | Cattura |

Il thread grafico ha un **`GMainContext` proprio** (`renderer->graphics_context`) e tutte le sorgenti
grafiche vi si attaccano esplicitamente. È l'equivalente disciplinato di ciò che REMOTIX ottiene con
i task Tokio.

---

## 4. Dipendenze

Obbligatorie sempre: glib ≥ 2.75, gio, **libpipewire ≥ 1.2**, **libei ≥ 1.3.901**, cairo, libdrm,
epoxy, xkbcommon ≥ 1.0, libnotify, libsecret, **krb5**, **tss2** (TPM 2.0), libsystemd (opzionale ma
necessaria per `SYSTEM`/`HANDOVER`).

Per il backend RDP: **freerdp3 ≥ 3.22**, winpr3, freerdp-server3, **libva** + libva-drm, **vulkan ≥ 1.2**,
**ffnvcodec ≥ 11.1.5** (NVENC), **fdk-aac**, **opus**, **fuse3 ≥ 3.9.1**, polkit ≥ 122, e in build
`glslc` + `spirv-opt` per gli shader SPIR-V.

Da notare per REMOTIX: **niente ffmpeg**, **niente x264**. La codifica è scritta a mano contro libva e
contro l'API NVENC. Vedi §9.

---

## 5. Il ciclo di vita di una sessione — la sequenza esatta

È la parte di maggior valore immediato per REMOTIX, perché è la stessa danza che §5.8 regola 1 della
specifica ha ricostruito a tentativi. Qui c'è la versione del riferimento, letta in
`grd-session.c`.

```
grd_session_start()
 │
 ├─ 1. org.gnome.Mutter.RemoteDesktop.CreateSession()          → percorso sessione
 │
 ├─ 2. Session.ConnectToEIS(options={})                        → fd
 │      └─ ei_new_sender() + ei_setup_backend_fd(fd)
 │         GSource su ei_get_fd(), ei_configure_name("gnome-remote-desktop")
 │
 ├─ 3. connessione dei segnali: "closed", "selection-owner-changed",
 │      "selection-transfer"
 │
 ├─ 4. org.gnome.Mutter.ScreenCast.CreateSession({
 │        "remote-desktop-session-id": <SessionId del passo 1>,
 │        "disable-animations": true })
 │
 ├─ 5. org.gnome.Mutter.RemoteDesktop.Session.Start()      ← ADESSO, non prima
 │
 └─ 6. ScreenCast.Session.RecordVirtual({cursor-mode, is-platform:true})
        └─ Stream proxy → Stream.Start()                   ← il flusso, non la sessione
```

**I due paletti sono identici a quelli che REMOTIX ha pagato** (§5.8 regola 1): la sessione di cattura
si crea dichiarando `remote-desktop-session-id` *prima* di avviare il controllo, e ciò che si avvia
alla fine è lo **Stream**, non la Session di ScreenCast.

Due dettagli che REMOTIX non ha:

- **`disable-animations: true`** nelle opzioni della sessione di cattura. Le animazioni di GNOME su un
  collegamento remoto costano banda e non aggiungono nulla. Una riga, da copiare.
- **`is-platform: true`** in `RecordVirtual`. Dichiara che il monitor virtuale è «di piattaforma»,
  cioè trattato come uno schermo vero dal punto di vista della configurazione monitor.

**La chiusura** è simmetrica e ha lo stesso vincolo: `grd_session_stop` chiama
`RemoteDesktop.Session.Stop`, e la cattura muore con lui. La sessione di ScreenCast **non** viene
fermata direttamente.

**Come si accorge che la sessione è finita**: segnale `closed` sulla sessione di Mutter
(`on_remote_desktop_session_closed`). Non c'è alcuna registrazione presso `gnome-session`: quella è
un'invenzione di REMOTIX (§5.9 di `SPECIFICA.md`, `uscita.rs`), e — dati i tempi misurati là — è
un'invenzione *migliore*, perché il segnale `closed` di Mutter arriva a smontaggio già avviato.

L'unico punto in cui `gnome-remote-desktop` parla con `gnome-session` è
`grd_session_manager_call_logout_sync()` (`grd-daemon-utils.c:207`), e lo fa nella direzione opposta:
chiama `Logout(NO_CONFIRMATION)` per **chiudere** la sessione greeter quando il client se ne va nel
modo handover.

---

## 6. Il percorso RDP

### 6.1 Cosa il server pretende dal client

In `rdp_peer_capabilities` e `rdp_peer_post_connect` (`grd-session-rdp.c`). Chi non soddisfa una di
queste condizioni **viene disconnesso**:

| Requisito | Riga | Motivo dichiarato nel codice |
|---|---|---|
| **Graphics Pipeline (EGFX)** | 1162 | *"Client did not advertise support for the Graphics Pipeline, closing connection"* |
| **32 bpp** | 1177 | Violazione di protocollo se dichiara codec ma non 32 bit |
| **Desktop resize** | 1193 | *"Client doesn't support desktop resizing"* |
| **Canale DRDYNVC** | 1199 | Senza canali dinamici non c'è EGFX |
| **Pointer cache > 0** | 1286 | *"Client doesn't have a pointer cache"* |
| **Fastpath output** | 1291 | *"Client does not support fastpath output"* |

**Questo è il fatto che più conta per REMOTIX**: il riferimento ha preso *esattamente* la decisione di
§3.7 della specifica — **solo EGFX, nessun ripiego legacy** — e la applica chiudendo la connessione.
La riserva sui client Android («va verificato provandoli») trova qui una risposta indiretta: GNOME
serve gli stessi client Android che REMOTIX ha in elenco, e li serve solo via EGFX.

Due degradazioni interessanti, entrambe sull'audio:

- se il client **non sa fare autodetect di rete**, l'audio in uscita viene **spento**
  (`grd-session-rdp.c:1316`): senza misura della banda, mandare audio peggiora il video;
- se il client è **iOS o Android**, l'audio in uscita viene **spento comunque**
  (`grd-session-rdp.c:1323`), con la motivazione: *«Client cannot handle graphics and audio
  simultaneously»*. Da tenere presente: REMOTIX ha Android fra i client di riferimento **e** l'audio
  AAC in §3.2.

### 6.2 Come il server configura FreeRDP

Estratto significativo di `init_rdp_session` (`grd-session-rdp.c:1539` e seguenti):

```c
RdpSecurity   = FALSE;      TlsSecurity = FALSE;      NlaSecurity = TRUE;
ColorDepth    = 32;
SupportGraphicsPipeline = TRUE;
GfxAVC444v2   = FALSE;   GfxAVC444 = FALSE;   GfxH264 = FALSE;   /* accesi dopo, in CapsAdvertise */
GfxSmallCache = FALSE;   GfxThinClient = FALSE;
RemoteFxCodec = TRUE;    RemoteFxImageCodec = TRUE;   NSCodec = TRUE;
SurfaceFrameMarkerEnabled = TRUE;   FrameMarkerCommandEnabled = TRUE;
PointerCacheSize = 100;
FastPathOutput = TRUE;   NetworkAutoDetect = TRUE;   RefreshRect = FALSE;
SupportMultitransport = FALSE;                       /* niente UDP */
VCFlags = VCCAPS_COMPR_SC;   VCChunkSize = 16256;
HasExtendedMouseEvent = TRUE;  HasHorizontalWheel = TRUE;  HasRelativeMouseEvent = TRUE;
HasQoeEvent = FALSE;           UnicodeInput = TRUE;
AudioCapture = TRUE;   AudioPlayback = TRUE;   RemoteConsoleAudio = TRUE;
OsMajorType = UNIX;    OsMinorType = PSEUDO_XSERVER;
```

**`NlaSecurity = TRUE` con le altre due a `FALSE` significa che NLA è obbligatorio.** È la divergenza
più grossa rispetto a REMOTIX, che ha scelto TLS puro (§3.6). Vedi §7.

### 6.3 Riconoscimento del client

`grd_session_rdp_is_client_mstsc()` (`grd-session-rdp.c:251`) riconosce mstsc guardando
`OsMajorType == WINDOWS && OsMinorType == WINDOWS_NT`. Il riferimento quindi **ammette apertamente che
i client vanno distinti**, ed è la conferma della regola dei tre client di §5.7 di `SPECIFICA.md`.

---

## 7. Autenticazione

### 7.1 NLA obbligatorio, con due meccanismi

`GrdRdpAuthMethods` è un insieme di bandiere (predefinito: `['credentials']`):

- **`credentials`** — NTLM. Il server **fabbrica un file SAM temporaneo** con l'utenza configurata
  (`grd-rdp-sam.c`) e lo passa a FreeRDP come `NtlmSamFile`. Le credenziali non sono quelle di
  sistema: sono una coppia utente/password specifica del desktop remoto, tenuta nel portachiavi;
- **`kerberos`** — richiede un keytab con il principal `TERMSRV`. Dopo l'handshake, `rdp_peer_logon`
  interroga il contesto NLA (`SECPKG_ATTR_AUTH_IDENTITY`), converte il principal in nome locale con
  `krb5_aname_to_localname` e **verifica che l'uid corrisponda a quello del processo**
  (`is_auth_identity_current_user`, `grd-session-rdp.c:991`).

Quest'ultimo controllo è **la stessa regola che REMOTIX ha dovuto scoprire il 3 agosto** — «entra un
solo utente: quello di cui il server serve la sessione», §3.4 di `SPECIFICA.md`. Il riferimento la fa
sull'uid effettivo, esattamente come la nota di REMOTIX prescrive. Con NTLM invece non applica alcuna
politica aggiuntiva (`"Authenticated using NTLM, not applying any additional policy"`) — e non ne ha
bisogno, perché la credenziale NTLM è già specifica di quella sessione.

### 7.2 Dove stanno le credenziali

Tre implementazioni intercambiabili di `GrdCredentials`:

| Backend | File | Uso |
|---|---|---|
| **libsecret** | `grd-credentials-libsecret.c` | Modo utente: portachiavi GNOME |
| **TPM 2.0** | `grd-credentials-tpm.c` + `grd-tpm.c` (809 righe) | Modo sistema: sigilla il segreto nel TPM |
| **file** | `grd-credentials-file.c` | Ripiego quando non c'è TPM |
| **one-time** | `grd-credentials-one-time.c` | Handover: credenziale usa e getta |

La variante TPM è pensata per il servizio di sistema, che gira senza sessione utente e quindi senza
portachiavi sbloccato.

### 7.3 TLS

Certificato e chiave si configurano come **percorsi a file PEM** (`tls-cert`, `tls-key`); il server li
legge e li passa a FreeRDP con `freerdp_certificate_new_from_pem` / `freerdp_key_new_from_pem`.
Nessuna generazione automatica: il README rimanda a `winpr-makecert`, `certtool` o `openssl`.
L'impronta del certificato viene esposta su D-Bus (`tls-fingerprint`) perché il pannello Impostazioni
la mostri.

---

## 8. La pipeline grafica EGFX

`grd-rdp-dvc-graphics-pipeline.c`, 2287 righe. È il file che la specifica di REMOTIX cita in §5.4.

### 8.1 Negoziazione delle capacità

L'elenco delle versioni provate, **in ordine decrescente** (`cap_list`, riga 1567):

```
10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 8.1, 8.0
```

Si sceglie la **prima versione dell'elenco che il client dichiara**, e si conferma quella sola con un
`CapsConfirm`. La versione decide se AVC è disponibile:

| Versione | AVC420 | AVC444 |
|---|---|---|
| 10.0 … 10.7 | sì, salvo `RDPGFX_CAPS_FLAG_AVC_DISABLED` | idem |
| 8.1 | solo se `RDPGFX_CAPS_FLAG_AVC420_ENABLED` | no |
| 8.0 | **no** | no |

**È esattamente il difetto che REMOTIX ha pagato** (§5.4: *«elenco delle versioni EGFX troppo rado:
mancava la famiglia 10.x intermedia, e mstsc si ferma alla 10.6»*). Questa tabella è la versione
autorevole: dieci voci, nessun buco.

Altre regole di protocollo applicate:

- **timeout di 10 secondi** (`PROTOCOL_TIMEOUT_MS`) dall'apertura del canale: se non arriva un
  `CapsAdvertise`, la sessione viene chiusa con `ERRINFO_BAD_CAPABILITIES`;
- un `CapsAdvertise` **ripetuto** è lecito solo se la versione iniziale era ≥ 10.3 (è il *protocol
  reset* previsto dalla specifica Microsoft); altrimenti è violazione;
- un `CapsAdvertise` ripetuto che **spegnerebbe AVC** viene rifiutato con chiusura della sessione;
- `CacheImportOffer` riceve una `CacheImportReply` **vuota** — cioè la cache non viene mai usata, come
  in xrdp;
- `QoeFrameAcknowledge` è accettato e ignorato.

### 8.2 Superfici

`grd_rdp_dvc_graphics_pipeline_acquire_gfx_surface` (riga 439) fa, in quest'ordine:

1. `grd_rdp_gfx_surface_new` → **`CreateSurface`** (formato `GFX_PIXEL_FORMAT_XRGB_8888`);
2. crea il *frame controller*;
3. **`map_surface`** → **`MapSurfaceToOutput`** con `outputOriginX/Y`.

**Le due chiamate sono adiacenti e nessuna delle due è opzionale.** È la conferma diretta della causa
trovata da REMOTIX il 2 agosto (§5.4): creare la superficie e agganciarla all'uscita sono due
operazioni distinte.

L'unico tipo di mappatura implementato è `MAP_TO_OUTPUT`. `MapSurfaceToWindow` e le varianti *scaled*
non esistono, come in xrdp.

**Superficie di rendering separata**: se l'allineamento richiesto dall'encoder non coincide con
l'allineamento a 16, viene creata una *seconda* superficie EGFX, si codifica su quella, e si copia
sulla superficie visibile con `SurfaceToSurface`. È l'unico uso di `SurfaceToSurface` nel programma.

### 8.3 Allineamento e geometrie — le due convenzioni

Nel percorso NVENC (`refresh_gfx_surface_avc420`, riga 1084):

```c
aligned_width  = surface_width  + (surface_width  % 16 ? 16 - surface_width  % 16 : 0);
aligned_height = surface_height + (surface_height % 64 ? 64 - surface_height % 64 : 0);
```

**Larghezza multipla di 16, altezza multipla di 64** — identico a quanto REMOTIX ha accertato in §5.4.

Sulle geometrie il codice usa **due convenzioni diverse, e questo va letto con attenzione** perché la
specifica di REMOTIX ne registra una sola:

| Struttura | Dove | Convenzione |
|---|---|---|
| `RECTANGLE_16` della meta AVC420 | `set_region_rects`, riga 559 | `right = x + width`, `bottom = y + height` → **esclusiva** |
| `RDPGFX_SURFACE_COMMAND` (`cmd.right/bottom`) | riga 686 | `right = extents.x + extents.width` → **esclusiva** |
| `MONITOR_DEF` di `ResetGraphics` | `maybe_reset_graphics`, riga 438 | `right = left + width - 1` → **inclusiva** |

> ⚠ **Da riverificare in REMOTIX.** §5.4 di `SPECIFICA.md` annota *«bordi della regione AVC420
> fuori-di-uno: sono inclusivi»*. Il riferimento fa il contrario sulla regione AVC420 ed è inclusivo
> solo sui `MONITOR_DEF`. Le due cose possono convivere se l'API di IronRDP applica già una
> conversione, ma è un punto dove un errore di ±1 produce esattamente il sintomo descritto
> (rinegoziazione e disconnessione), e va accertato guardando i byte, non il codice Rust.

### 8.4 ResetGraphics

`grd_rdp_dvc_graphics_pipeline_reset_graphics` (riga 462) apre con:

```c
g_assert (g_hash_table_size (graphics_pipeline->surface_table) == 0);
```

**Tutte le superfici devono essere state cancellate prima di ridichiarare la tela.** E l'elenco dei
monitor non è mai vuoto: `maybe_reset_graphics` costruisce l'array dai monitor correnti, con
`g_assert (n_monitors > 0)`. Conferma la quarta correzione di §5.4 di `SPECIFICA.md`.

### 8.5 Invio di un fotogramma

```
StartFrame(frameId, timestamp)      ← timestamp = ora<<22 | min<<16 | sec<<10 | ms
SurfaceCommand(surfaceId, codecId, ...)
[SurfaceToSurface, solo se c'è una superficie di rendering separata]
EndFrame(frameId)
```

Per RemoteFX Progressive esiste la scorciatoia `SurfaceFrameCommand`, che manda i tre PDU insieme.

Il `frameId` viene registrato in `frame_serial_table` insieme al *serial* della superficie, in modo che
un ack in ritardo che si riferisce a una superficie già distrutta non faccia danni: il serial è
contato a parte con `surface_serial_ref` / `unref`. È una raffinatezza che serve solo con
ridimensionamenti frequenti.

---

## 9. Codec ed encoder — la sorpresa

**`gnome-remote-desktop` non ha un encoder H.264 software.** Non usa ffmpeg, non usa x264, non usa
OpenH264. La selezione, in `grd-rdp-render-context.c:561`:

```
il client sa fare AVC (420 o 444)  ∧  c'è VAAPI  →  AVC444v2 se il client lo sa, altrimenti AVC420
altrimenti                                        →  RemoteFX Progressive (software)
```

Più un percorso separato, più vecchio, per **NVENC** (CUDA), che vive dentro la pipeline grafica e
scavalca il resto (`refresh_gfx_surface_avc420`).

| Percorso | File | Note |
|---|---|---|
| **VAAPI** | `grd-encode-session-vaapi.c` (1915 righe) | Scritto **direttamente contro libva**: SPS/PPS/slice generati a mano in `grd-nal-writer.c` (886 righe) |
| **NVENC** | `grd-hwaccel-nvidia.c` + `.cu` | Include due kernel CUDA (`grd-cuda-avc-utils.cu`, `grd-cuda-damage-utils.cu`) |
| **Vulkan** | `grd-hwaccel-vulkan.c` (1022 righe) | **Non è un encoder**: serve per importare i DMA-BUF e convertire il colore. La codifica resta VAAPI |
| **RFX Progressive** | `grd-rdp-sw-encoder-ca.c` | Ripiego software: usa `rfx_encode_message` di FreeRDP e riscrive il messaggio nel formato RDPEGFX |

### 9.1 Controllo del bitrate: non c'è

`grd-encode-session-vaapi.c:1696`:

```c
config_attributes[1].type  = VAConfigAttribRateControl;
config_attributes[1].value = VA_RC_CQP;
```

**Quantizzazione costante, QP 22** (`picture_param->pic_init_qp = 22`, riga 923), profilo **H.264
High**, nessuna misura del bitrate, nessun VBV, nessun target. Anche nel percorso NVENC i valori
dichiarati nella meta sono fissi: `qp = 22`, `qualityVal = 100`.

> **Questo tocca direttamente §3.1 di `SPECIFICA.md`.** La specifica di REMOTIX motiva la scelta di
> `libavcodec` così: *«Vulkan Video consegna il codificatore senza il controllo del bitrate, che
> andrebbe scritto da noi… VA-API e NVENC lo forniscono già messo a punto dal costruttore»*. Il
> riferimento mostra che **VA-API messa a nudo non regala nulla**: il controllo del bitrate è un
> attributo di configurazione che va scelto e alimentato, e GNOME ha scelto di **non usarlo affatto**.
>
> La conclusione non ribalta la decisione di REMOTIX — `libavcodec` la comodità la dà davvero, perché
> incapsula VBV, GOP e preset dietro un'API sola — ma corregge la premessa: il merito è di ffmpeg, non
> di VA-API. E soprattutto: **sul punto di lavoro dei 10 Mbps il riferimento non ha niente da
> insegnare**, perché non ci prova nemmeno. Là REMOTIX è da solo.

### 9.2 Come adatta, allora

Non adattando la qualità, ma **il numero di fotogrammi**. Vedi §10.

### 9.3 AVC444

Implementato davvero, a differenza di xrdp. `prepare_avc444_bitstream` (riga 604) gestisce i tre casi
del campo `LC`: vista doppia (`LC=0`, due flussi), sola luma (`LC=1`), sola croma (`LC=2`). Il
`render_state` decide fotogramma per fotogramma se mandare la vista ausiliaria, ed esiste una logica di
*upgrade* ritardato (`FRAME_UPGRADE_DELAY_US = 60 ms`, `TRANSITION_TIME_US = 200 ms`,
`grd-rdp-surface-renderer.c`): quando il collegamento è tranquillo, il fotogramma «solo luma» già
mandato viene **completato** con la croma poco dopo.

È una risposta concreta alla strategia abbozzata in §5.2 di `SPECIFICA.md` (*«AVC420 come base, AVC444
attivabile su connessioni migliori»*): il riferimento lo fa per fotogramma, non per sessione, e paga
solo la croma quando c'è margine.

---

## 10. Controllo di flusso e adattamento

### 10.1 Misura della rete (`grd-rdp-network-autodetection.c`)

Usa il meccanismo di autodetect di MS-RDPBCGR:

- **RTT**: `RTTMeasureRequest` con numeri di sequenza tracciati. Due cadenze — **70 ms** quando
  qualcuno ha bisogno di RTT preciso (cioè quando la pipeline grafica sta lavorando), **700 ms**
  altrimenti. Media su una finestra di 500 ms;
- **banda**: `BandwidthMeasureStart/Stop`, agganciata all'invio dei fotogrammi. Si misura **solo su
  fotogrammi ≥ 10 KB** (`MIN_BW_MEASURE_SIZE`), per non falsare la misura con pacchetti minuscoli;
- rilevamento di client che non rispondono: se restano più di 16 384 richieste senza risposta, il
  codice scrive *«Protocol violation: Client leaves requests unanswered»* e azzera.

C'è anche una autodetect **al momento della connessione** (`grd-rdp-connect-time-autodetection.c`, 643
righe), attivata dal gancio `OnConnectTimeAutoDetectBegin`.

### 10.2 Il regolatore (`grd-rdp-gfx-frame-controller.c`)

Tre stati: `INACTIVE`, `ACTIVE`, `ACTIVE_LOWERING_LATENCY`. La grandezza regolata è il numero di
**«posti fotogramma»** (`total_frame_slots`) concessi al renderer: `0` significa fermo,
`UINT32_MAX` significa nessun limite.

La soglia di attivazione si ricava **dall'RTT**:

```c
delayed_frames = rtt_us * refresh_rate / 1e6;
activate_throttling_th = MAX (2, MIN (delayed_frames + 2, refresh_rate));
```

Cioè: quanti fotogrammi stanno «in volo» nel tempo di un round trip, più due. Superata quella soglia
di fotogrammi non riscontrati, si smette di produrre; scesi a ≤ 1, si riparte senza limiti. In mezzo,
i posti concessi sono `ack_rate + 1 − enc_rate`, cioè si produce al ritmo con cui il client conferma.

**Non c'è alcun adattamento di risoluzione, né di bitrate, né di frame rate nominale.** Il refresh rate
di riferimento è fisso: `TARGET_SURFACE_REFRESH_RATE = 60` (`grd-rdp-layout-manager.c:36`).

> Per REMOTIX: §3.1 di `SPECIFICA.md` prevede *«adattamento automatico di risoluzione e frame rate alla
> banda»*, riusando la macchina della risoluzione dinamica. Il riferimento **non fa così**: regola solo
> la cadenza di produzione, e lo fa contro il backlog di ack invece che contro la banda misurata (che
> pure misura, e usa solo per informare il client). È una scelta più semplice e più robusta, e vale
> come punto di partenza: la retroazione sugli ack è a costo quasi zero e va comunque implementata,
> l'adattamento di risoluzione è la rete di sicurezza sopra.

### 10.3 Soppressione dell'uscita

`SuppressOutput` (MS-RDPBCGR) è gestito: quando il client minimizza la finestra, il renderer smette e
il consumatore di RTT viene rimosso, così le sonde rallentano da 70 a 700 ms.

---

## 11. Cattura

`grd-rdp-pipewire-stream.c`, 1326 righe.

### 11.1 Il formato proposto

```c
SPA_FORMAT_VIDEO_format      = SPA_VIDEO_FORMAT_BGRx
SPA_FORMAT_VIDEO_size        = rettangolo FISSO (larghezza, altezza del monitor virtuale)
SPA_FORMAT_VIDEO_framerate   = 0/1                    ← «solo quando cambia»
SPA_FORMAT_VIDEO_maxFramerate= intervallo [1/1 … refresh_rate/1]
```

La cadenza dichiarata a zero con un massimo a intervallo è **esattamente** quanto REMOTIX ha accertato
in §5.6 di `SPECIFICA.md`.

> ✅ **La divergenza è chiusa: ha ragione il riferimento.** [M, 4 agosto 2026] Con la catena in C,
> contro Mutter 48.7, il **`SPA_POD_Rectangle` singolo funziona** e negozia esattamente la misura
> chiesta — provato a 1282×802, con `is-platform: true` dichiarato in `RecordVirtual`. Provato anche
> l'intervallo chiuso (min = pref = max): **funziona pure quello**, con lo stesso esito.
>
> Il `no more input formats` misurato da REMOTIX il 2 agosto era quindi un fatto della *sua* catena
> di allora — il pacchetto Rust di PipeWire — o dell'assenza di `is-platform`. Fra le tre
> spiegazioni ipotizzate qui, la versione di Mutter è esclusa (è la stessa); fra le altre due non si
> è discriminato, e non ne vale la pena: la forma pulita funziona e si usa quella. §5.6 di
> `SPECIFICA.md` è stato corretto di conseguenza.
>
> Resta vero che un intervallo **aperto** lascia scegliere a Mutter, che sceglie 1280×720.

### 11.2 DMA-BUF

I modificatori si dichiarano solo se c'è un thread EGL **e non c'è NVENC**, con la proprietà marcata
`MANDATORY | DONT_FIXATE` e chiusa da `DRM_FORMAT_MOD_INVALID`. Quando si dichiarano i modificatori si
aggiunge sempre **un secondo formato di ripiego senza modificatori**, così se la negoziazione DMA-BUF
fallisce resta la memoria condivisa.

Conferma per contrasto la regola di REMOTIX (§5.6): *«per restare in memoria ordinaria non si dichiara
il campo `modifier`»*. Il riferimento fa il contrario perché il DMA-BUF lo vuole; la meccanica è la
stessa.

Tipi di buffer accettati: `MemFd` sempre, `DmaBuf` se c'è EGL. Da 2 a 8 buffer. Con DMA-BUF ed
**explicit sync** disponibile si chiede anche la meta `SPA_META_SyncTimeline`.

Meta richieste sempre: `SPA_META_Header` e **`SPA_META_Cursor`** (fino a 384×384) — il cursore arriva
come metadato e viene reso a parte, non disegnato nell'immagine, salvo in modalità screen-share dove si
usa `CURSOR_MODE_EMBEDDED`.

### 11.3 Il ridimensionamento — la differenza che conta

`grd_rdp_pipewire_stream_resize()` (riga 402) fa **una cosa sola**:

```c
add_format_params (stream, virtual_monitor, ...);   /* con la misura nuova */
pw_stream_update_params (stream->pipewire_stream, params, n);
```

**Nessuna nuova sessione di cattura, nessun nuovo monitor virtuale, nessun nuovo `RecordVirtual`.**
Mutter riconfigura il monitor virtuale e risponde con `on_stream_param_changed`, dove il server
ridimensiona rilevatore di danno e pool di buffer, e emette `video-resized`.

> **È la risposta alla domanda aperta di §5.8 di `SPECIFICA.md`.** REMOTIX oggi rifà la cattura a ogni
> cambio di misura, e siccome una cattura nuova non si registra su un controllo già avviato, **rifà
> anche il controllo** — pagando il prezzo di perdere lo stato dei tasti premuti. La specifica annota
> *«sparirà con la fase 6, se il ridimensionamento smetterà di rifare la cattura»*. Il riferimento
> dimostra che si può, e come: si aggiorna il parametro del flusso PipeWire, e basta.

### 11.4 Lo stride

Il codice calcola `stride = width * 4` in `on_stream_param_changed`, ma è solo per dimensionare il
pool; i dati veri si leggono sempre dal chunk (`grd-rdp-pw-buffer.c`). La regola di REMOTIX — *«lo
stride si legge dal chunk del buffer, mai calcolato»* — resta valida e vale anche qui.

---

## 12. Layout e ridimensionamento

`grd-rdp-layout-manager.c`, 1043 righe. È una macchina a stati esplicita, e merita di essere copiata
quasi così com'è.

```
AWAIT_CONFIG ──(arriva una configurazione monitor)──► inhibit_rendering()
                                                       │
                                              AWAIT_INHIBITION_DONE
                                                       │ (nessun render context in uso)
                                              PREPARE_SURFACES
                                                       │ crea/aggiorna gli stream
                                    ┌──────────────────┴──────────────────┐
                              AWAIT_STREAMS                        AWAIT_VIDEO_SIZES
                                    └──────────────────┬──────────────────┘
                                              START_RENDERING
                                                       │ uninhibit_rendering()
                                                  AWAIT_CONFIG
```

I punti che risolvono problemi noti a REMOTIX:

- **il rendering viene inibito prima di toccare qualunque cosa** e riacceso solo quando *tutti* gli
  stream hanno confermato la misura nuova. È la forma disciplinata della regola 3-bis di §5.7 di
  `SPECIFICA.md` («dopo un cambio di misura si aspetta che il desktop si sia ridisegnato»): invece di
  aspettare un silenzio di 300 ms, si aspetta un **evento**;
- l'inibizione non è un flag ma un **conteggio di risorse in uso**: `inhibition-done` viene emesso
  quando `acquired_render_contexts` è vuoto, cioè quando nessun fotogramma è a metà strada;
- durante `AWAIT_CONFIG` — e solo allora — `grd_rdp_layout_manager_transform_position` accetta le
  coordinate del puntatore. In ogni altro stato **l'input viene scartato**, perché la geometria non è
  stabile;
- una configurazione che arriva mentre se ne sta applicando un'altra **sostituisce** quella in coda
  (`pending_monitor_config`), non si accoda. È la risposta alle raffiche di ridimensionamento che i
  client mandano trascinando il bordo della finestra;
- se uno stream «monitor fisico» si chiude da solo, parte un timer di **50 ms**
  (`LAYOUT_RECREATION_TIMEOUT_MS`) che tenta di ricostruire l'ultima configurazione buona.

### 12.1 Validazione della configurazione monitor

`grd-rdp-monitor-config.c`. Le regole, applicate identiche alle tre sorgenti possibili (Client Core
Data, Client Monitor Data, MS-RDPEDISP):

| Vincolo | Valore |
|---|---|
| Larghezza e altezza | **200 … 8192** |
| Dimensione fisica (mm) | 10 … 10000, altrimenti azzerata |
| Fattore di scala | 100 … 500, altrimenti azzerato |
| Monitor primario | deve stare a **(0, 0)**; se nessuno lo dichiara, se ne elegge uno che ci sta |
| Sovrapposizioni | **vietate** (verifica con `cairo_region`) |
| `DeviceScaleFactor` | **ignorato** — deprecato, solo Windows 8.1 |

Il desktop complessivo è l'estensione dell'unione delle regioni; l'offset del layout serve a
riportare tutto in coordinate non negative.

Su MS-RDPEDISP il server dichiara `MaxMonitorAreaFactorA = MaxMonitorAreaFactorB = 8192` e il numero
massimo di monitor: **16** nei modi headless/sistema, **1** in screen share.

---

## 13. Input

### 13.1 libei, non i metodi `Notify*`

`gnome-remote-desktop` usa `ConnectToEIS` e parla libei, come la specifica di REMOTIX già annota in
§5.8. Vale la pena registrare **cosa se ne ricava**, perché sono cose che i metodi `Notify*` non danno:

| Cosa | Come |
|---|---|
| **La disposizione di tastiera della sessione** | `ei_device_keyboard_get_keymap()` → fd → `xkb_keymap_new_from_string` |
| **Lo stato reale di BlocMaiusc e BlocNum** | evento `EI_EVENT_KEYBOARD_MODIFIERS` |
| **Le regioni degli schermi** | `ei_device_get_region()` con `mapping_id` |
| **Un punto di sincronizzazione** | `ei_ping` / `EI_EVENT_PONG` |

Il primo punto è la **risposta alla questione aperta n.7 di REMOTIX** (§5.8: la disposizione di
tastiera non viene concordata). Il riferimento non impone nulla e non chiede nulla al client: **legge
la keymap dalla sessione**, e per gli eventi Unicode cerca quale tasto fisico produce quel simbolo
nella disposizione corrente, applicando i modificatori di livello:

```c
pick_keycode_for_keysym_in_current_group()   /* scorre keycode × livelli */
apply_level_modifiers()                      /* Shift per il livello 1, ISO_Level3_Shift per il 2 */
ei_device_keyboard_key (evcode, state)
evcode = xkb_keycode - 8                     /* XKB → evdev */
```

Gli eventi di scancode invece passano diretti: scancode RDP → `GetVirtualKeyCodeFromVirtualScanCode`
→ `GetKeycodeFromVirtualKeyCode(..., WINPR_KEYCODE_TYPE_EVDEV)`. Cioè: **le posizioni fisiche restano
posizioni fisiche**, e il simbolo lo decide la sessione — proprio la situazione che REMOTIX descrive.
La differenza è che il riferimento, avendo la keymap in mano, sa tradurre gli eventi Unicode con
precisione, mentre REMOTIX oggi deve dichiarare `REMOTIX_TASTIERA`.

> Nota pratica: con FreeRDP il KLID del client è disponibile (sta in `rdpSettings`), quindi la
> questione n.7 si può chiudere in due modi — dichiarando la disposizione dal KLID, oppure leggendola
> dalla sessione con libei come fa il riferimento. Il secondo è più solido, perché non si fida di come
> il sistema operativo del client descrive la propria tastiera.

### 13.2 Dispositivi e capacità

Alla comparsa del seat: `ei_seat_bind_capabilities(POINTER, KEYBOARD, POINTER_ABSOLUTE, BUTTON,
SCROLL, TOUCH)`. I dispositivi arrivano poi con `EI_EVENT_DEVICE_ADDED`, e su
`EI_EVENT_DEVICE_RESUMED` si chiama `ei_device_start_emulating` con un numero di sequenza crescente.

**Il puntatore assoluto lavora per regioni**: ogni regione ha un `mapping_id`, e il `mapping_id` dello
stream di cattura fa da chiave. `transform_position` (`grd-session.c:703`) riscala le coordinate del
client sulla regione:

```c
scale_x = input_rect_width / ei_region_get_width (region);
x = ei_region_get_x (region) + motion_abs->x / scale_x;
```

È la sostituzione elegante del percorso D-Bus dello stream che REMOTIX passa a
`NotifyPointerMotionAbsolute`.

### 13.3 La rotella

`grd-session-rdp.c:639`:

```c
axis_value = flags & WheelRotationMask;        /* complemento a due se negativo */
axis_step  = -axis_value / 120.0;              /* RDP conta 120 per scatto */
if (flags & PTR_FLAGS_WHEEL_NEGATIVE) axis_step = -axis_step;

verticale:   axis (0,  axis_step * 10.0)
orizzontale: axis (-axis_step * 10.0,  0)
```

`DISCRETE_SCROLL_STEP = 10.0`. **Il verticale è negato, l'orizzontale è negato in senso opposto** —
conferma esatta della regola 6 di §5.8 di `SPECIFICA.md`, compreso il fattore 120 → 10.

C'è anche `grd_session_notify_pointer_axis_discrete`, che rimoltiplica per 120 verso libei.

### 13.4 Il tasto Pausa

Implementato con una macchina a quattro stati (`is_pause_key_sequence`, riga 738): riconosce la
sequenza `Ctrl↓(E1) → NumLock↓ → Ctrl↑(E1) → NumLock↑` e la traduce in `XKB_KEY_Pause` premuto e
rilasciato.

> Per REMOTIX: §5.8 dà il tasto Pausa per perso, perché IronRDP non consegna il flag `KBDFLAGS_EXTENDED1`.
> Il riferimento mostra che **il flag E1 serve solo a disambiguare**: la sequenza è riconoscibile
> anche dal solo susseguirsi di Ctrl e NumLock. Se il flag manca, la macchina a stati funziona
> ugualmente con un rischio di falso positivo trascurabile.

### 13.5 Tasti premuti e tasti a scatto

- due tabelle, `pressed_keys` (per keycode) e `pressed_unicode_keys` (per keysym), che **scartano** la
  pressione ripetuta e il rilascio non appaiato — identico alla regola 4 di REMOTIX;
- alla chiusura della sessione, entrambe vengono svuotate rilasciando tutto, e la coda viene
  **svuotata forzatamente** (`grd_rdp_event_queue_flush`);
- l'evento di sincronizzazione RDP (`rdp_input_synchronize_event`) rilascia tutto e registra lo stato
  atteso di BlocMaiusc/BlocNum;
- la riconciliazione avviene **dopo un ping libei**: si aspetta che l'input in volo sia stato
  digerito (`grd_session_flush_input_async` → `EI_EVENT_PONG`), poi si confronta lo stato atteso con
  quello reale letto da `EI_EVENT_KEYBOARD_MODIFIERS` e, se diverge, si **preme e rilascia il tasto**.

Quest'ultimo punto è la versione fatta bene di ciò che §5.8 di `SPECIFICA.md` descrive come
approssimazione (*«non esiste un modo di imporlo… il conto parte da tutti spenti»*): con libei lo
stato reale si legge, e il ping evita di confrontarlo mentre ci sono eventi ancora in coda.

### 13.6 Coda degli eventi

`grd-rdp-event-queue.c`: gli eventi arrivano dal thread socket e vengono accodati; una `GSource` sul
thread principale li svuota. **Nessuna chiamata bloccante dal ciclo del protocollo** — la regola 3 di
§5.8 di REMOTIX, applicata identica.

### 13.7 Touch e penna (MS-RDPEI)

`grd-rdp-dvc-input.c` (764 righe) implementa il canale `RDPEI`: fino a **256 contatti**, con una
macchina a stati per contatto, più gli eventi penna. I contatti si mappano su `ei_touch` con le stesse
regioni del puntatore assoluto.

> È la **questione aperta n.1 di REMOTIX** (input touch, rilevante avendo Android fra i client). Il
> riferimento la risolve nativamente, non emulando il mouse.

---

## 14. Canali virtuali

| Canale | File | Stato |
|---|---|---|
| **RDPGFX** (EGFX) | `grd-rdp-dvc-graphics-pipeline.c` | Obbligatorio |
| **DISP** (MS-RDPEDISP) | `grd-rdp-dvc-display-control.c` | Solo in modalità `extend` |
| **RDPEI** (touch/penna) | `grd-rdp-dvc-input.c` | Sempre |
| **CLIPRDR** | `grd-clipboard-rdp.c` (2674 righe!) | Se il client si unisce al canale |
| **AUDIO_PLAYBACK** | `grd-rdp-dvc-audio-playback.c` | Se `AudioPlayback` e non `RemoteConsoleAudio` |
| **AUDIO_INPUT** | `grd-rdp-dvc-audio-input.c` | Se `AudioCapture` |
| **RDPECAM** (camera) | `grd-rdp-dvc-camera-*.c` | Sempre (novità della 49+) |
| **TELEMETRY** | `grd-rdp-dvc-telemetry.c` | Sempre |

Tutti derivano da `GrdRdpDvc`, che gestisce apertura, `ChannelIdAssigned`, sottoscrizione allo stato di
creazione e smontaggio. L'inizializzazione avviene nel thread socket quando `DRDYNVC` passa a
`DRDYNVC_STATE_READY`.

### 14.1 Appunti

`grd-clipboard-rdp.c` è il file più grosso del progetto. Copre testo (UTF-8 e UTF-16), HTML,
immagini (BMP, TIFF, GIF, JPEG, PNG) e **file**, questi ultimi tramite un filesystem FUSE
(`grd-rdp-fuse-clipboard.c`, 1591 righe) che espone i file del client dentro la sessione. Formati
dichiarati in `grd-mime-type.c`.

REMOTIX ha la clipboard in §3.5 («bidirezionale», una riga). Il conto vero è questo: **il testo è
poche centinaia di righe, i file sono un progetto a sé**. Vale la pena scriverlo nel piano.

### 14.2 Audio

Uscita: si negozia il formato migliore fra quelli offerti dal client, in ordine **AAC → Opus → PCM**.
Stereo fisso. AAC via fdk-aac, Opus a 48 kHz, PCM 16 bit. `grd-rdp-dsp.c` incapsula i tre encoder e
implementa anche la decodifica A-law per l'ingresso.

Sorgente e destinazione sono **PipeWire** (`grd-rdp-audio-output-stream.c`), non moduli PulseAudio
compilati a parte come in xrdp. È la stessa scelta di §3.2 di `SPECIFICA.md`.

Il volume del client viene applicato lato server moltiplicando i campioni PCM.

### 14.3 Camera

`grd-rdp-dvc-camera-device.c` (1783 righe) + `grd-rdp-camera-stream.c`: redirezione della webcam del
client **dentro** la sessione, esposta come sorgente PipeWire. Supporta H.264 con un decodificatore
software (`grd-decode-session-sw-avc.c`). È fuori scope per REMOTIX, ma è la funzionalità che xrdp non
ha e che GNOME ha aggiunto per prima.

---

## 15. Configurazione

Tutto in GSettings, sotto `org.gnome.desktop.remote-desktop`, con schemi separati per
`rdp`, `rdp.headless`, `vnc`, `vnc.headless`. Le credenziali no: quelle stanno nel portachiavi o nel TPM.

| Chiave RDP | Predefinito | Note |
|---|---|---|
| `port` | 3389 | |
| `negotiate-port` | `true` | Prova i 10 porti successivi se occupato |
| `enable` | `false` | |
| `screen-share-mode` | `mirror-primary` | oppure `extend` (monitor virtuale) |
| `tls-cert`, `tls-key` | `''` | Percorsi a file PEM |
| `view-only` | **`true`** | Predefinito prudente: si guarda e basta |
| `auth-methods` | `['credentials']` | `credentials` (NTLM) e/o `kerberos` |
| `kerberos-keytab` | `''` | |

Opzioni da riga di comando del daemon: `--headless`, `--system`, `--handover`, `--rdp-port`,
`--vnc-port`, `--max-parallel-connections` (predefinito **10**, `0` = illimitate).

`grdctl` ha la forma `grdctl [--system|--headless] rdp <comando>`, con `set-credentials`,
`set-tls-cert`, `set-tls-key`, `enable`/`disable`, `enable-view-only`/`disable-view-only`,
`set-auth-methods`, `set-kerberos-keytab`, `--show-credentials`.

---

## 16. Connessioni concorrenti e limiti

Due meccanismi distinti, e conviene non confonderli.

**Il throttler** (`grd-throttler.c`) agisce *prima* di creare la sessione, contro gli abusi:

| Limite | Predefinito |
|---|---|
| Connessioni per peer | 5 |
| Connessioni in attesa | 5 |
| Tentativi al secondo (per peer) | 10 |
| Connessioni totali | `--max-parallel-connections`, 10 |

Chi supera viene **rifiutato**; chi arriva troppo in fretta viene messo in coda e servito quando il
rateo lo consente.

**La politica sulla seconda sessione** è invece in `on_session_post_connect` (`grd-rdp-server.c:176`):

```c
if (runtime_mode == HANDOVER || runtime_mode == HEADLESS)
  g_list_foreach (rdp_server->sessions, maybe_stop_session, nuova_sessione);
```

Cioè: nei modi a utente singolo, **la connessione nuova soppianta quella vecchia**, e lo fa dopo il
`PostConnect`, cioè dopo che il nuovo client si è autenticato.

> **È la terza opzione della tabella di §5.9 di `SPECIFICA.md`, quella che l'utente ha scartato** il 2
> agosto («soppiantare: comodo per riagganciarsi, ma chiunque si autentichi butta fuori chi sta
> lavorando»). Vale la pena registrare che il riferimento ha scelto diversamente da REMOTIX, e perché
> può permetterselo: le credenziali RDP di `gnome-remote-desktop` sono una coppia dedicata al desktop
> remoto, non le credenziali di sistema, quindi «chiunque si autentichi» è di fatto sempre la stessa
> persona che rientra. In REMOTIX, dove si autentica con PAM contro l'utenza vera, il ragionamento non
> regge allo stesso modo, e il rifiuto resta la scelta giusta.

Da notare anche: **il ciclo di accettazione è un `GSocketService`**, quindi le connessioni si accettano
in parallelo per costruzione. Il difetto di §5.9 di `SPECIFICA.md` — il ciclo sequenziale di
`ironrdp-server` — è specifico di IronRDP e qui non esiste.

### 16.1 Il congedo

`grd_session_rdp_stop` (riga 1847) prima di chiudere imposta l'informazione d'errore RDP:

```c
if (!has_session_close_queued (session_rdp))
  freerdp_set_error_info (peer->context->rdp, ERRINFO_RPC_INITIATED_DISCONNECT);
else if (session_rdp->rdp_error_info)
  freerdp_set_error_info (peer->context->rdp, session_rdp->rdp_error_info);
```

I codici usati altrove: `ERRINFO_BAD_CAPABILITIES`, `ERRINFO_BAD_MONITOR_DATA`,
`ERRINFO_CLOSE_STACK_ON_DRIVER_FAILURE`, `ERRINFO_GRAPHICS_SUBSYSTEM_FAILED`,
`ERRINFO_CB_CONNECTION_CANCELLED`.

> **Era il «congedo dichiarato» che REMOTIX aveva a debito** (§5.9 di `SPECIFICA.md`). Con FreeRDP il
> debito non esiste: `freerdp_set_error_info` è API pubblica. Il riferimento usa
> `RPC_INITIATED_DISCONNECT` per la chiusura ordinata, non `LogoffByUser` — e la scelta è sensata,
> perché descrive chi ha chiuso, non perché.

---

## 17. Che cosa cambia fra la 48 (Debian Trixie) e la 51

L'architettura è la stessa: **la 48 usa già libei**, ha già il layout manager, l'encoder VAAPI, il
frame controller e la pipeline EGFX nella forma descritta qui. Le differenze:

**Aggiunto dopo la 48:**

- redirezione della **camera** (MS-RDPECAM): `grd-rdp-dvc-camera-*`, `grd-rdp-camera-stream`
- **decodifica** H.264 software (serve alla camera): `grd-decode-session-sw-avc`
- il **throttler** delle connessioni: `grd-throttler`
- `grd-frame-clock`, `grd-sample-buffer`, `grd-vk-physical-device`, `grd-vk-sync-file` (explicit sync)
- `grd-settings-headless` come classe a sé
- rinominati con prefisso `dvc`: `grd-rdp-graphics-pipeline` → `grd-rdp-dvc-graphics-pipeline`, e così
  per audio, display control e telemetria; introdotto `grd-rdp-dvc-handler`

**Requisiti diversi:** FreeRDP ≥ 3.1 (48) contro ≥ 3.22 (51); libei ≥ 1.2 contro ≥ 1.3.901.

Per REMOTIX significa che **tutto ciò che è utile qui è già nella 48.x che gira su Trixie**, e che le
misure fatte contro Mutter 48.7 restano confrontabili.

---

## 18. Il conto per REMOTIX

### 18.1 Cosa conferma

| Decisione di REMOTIX | Conferma nel riferimento |
|---|---|
| **Solo EGFX**, nessun ripiego legacy | `rdp_peer_capabilities` chiude la connessione se manca (§6.1) |
| Interfacce dirette di Mutter, non il portale | Idem, e per la stessa ragione |
| `RecordVirtual` invece di `RecordMonitor` | Idem in modalità `extend` |
| `CreateSurface` + `MapSurfaceToOutput` | Adiacenti e obbligatorie (§8.2) |
| Larghezza ×16, altezza ×64 | Identico (§8.3) |
| `ResetGraphics` con la definizione dei monitor | `g_assert (n_monitors > 0)` (§8.4) |
| Cadenza PipeWire dichiarata a 0 + massimo a intervallo | Identico (§11.1) |
| Ultimo fotogramma conservato e rispedito | `invalidate_surface` ripropone `last_buffer` |
| Conteggio dei tasti premuti, rilascio a fine connessione | Identico (§13.5) |
| Rotella: /120 → ×10, verticale negato | Identico (§13.3) |
| Niente D-Bus dentro il ciclo del protocollo | Coda di eventi + `GSource` (§13.6) |
| PipeWire per l'audio | Identico (§14.2) |
| Sessione remota solo per l'utente che la possiede | Controllo sull'uid in `rdp_peer_logon` (§7.1) |
| Il congedo dichiarato serve | `freerdp_set_error_info` prima della chiusura (§16.1) |

### 18.2 Cosa contraddice, o corregge

1. **NLA obbligatorio.** Il riferimento non offre TLS puro: `NlaSecurity = TRUE`, gli altri due a
   `FALSE`. REMOTIX ha scelto TLS + PAM. Non è un errore — è una scelta diversa con conseguenze
   diverse: con NLA le credenziali si verificano *prima* di allocare la sessione, e mstsc mostra la
   finestra di credenziali sua; con TLS puro l'autenticazione avviene dentro il protocollo RDP e il
   difetto trovato il 3 agosto (§3.4: «chi non manda credenziali non viene validato») **non potrebbe
   esistere**. Da mettere agli atti: la guardia che parte da *negato* è il prezzo del TLS puro.

2. **Il controllo del bitrate non lo dà VA-API.** §9.1. La motivazione di §3.1 di `SPECIFICA.md` va
   corretta nella premessa; la conclusione (usare `libavcodec`) regge lo stesso, anzi si rafforza.

3. **Non esiste un encoder H.264 software.** Il ripiego di GNOME è RemoteFX Progressive. REMOTIX
   prevede `libx264` come base sempre disponibile e punto di partenza dello sviluppo: è una scelta
   ragionevole e più semplice, ma va saputo che **il riferimento non la valida** — nessuno ha mai
   provato quella strada con questi client.

4. **La seconda connessione soppianta, non viene rifiutata.** §16. REMOTIX ha deciso diversamente e
   con ragione, ma la ragione va scritta: dipende dal fatto che REMOTIX autentica contro l'utenza vera.

5. **Il ridimensionamento non rifà la cattura.** §11.3. Questa è la correzione più utile: cancella il
   prezzo che §5.8 di `SPECIFICA.md` accetta a malincuore.

6. ~~**Rettangolo PipeWire singolo invece di intervallo chiuso.**~~ §11.1. **CHIUSA il 4 agosto: ha
   ragione il riferimento**, il rettangolo singolo funziona ed è la forma che REMOTIX usa. [M]

7. **Convenzione dei bordi della regione AVC420.** §8.3. Da riverificare sui byte.

### 18.3 Cosa conviene copiare, in ordine di resa

1. **La macchina a stati del layout manager** (§12). Risolve insieme la regola 3-bis, le raffiche di
   ridimensionamento e lo scarto dell'input durante il cambio di geometria. È la cosa più preziosa del
   file.
2. **Il ridimensionamento via `pw_stream_update_params`** (§11.3). Toglie un rifacimento completo di
   cattura e controllo a ogni cambio di misura.
3. **Il regolatore a posti-fotogramma con soglia dall'RTT** (§10.2). Poche decine di righe, e dà
   l'adattamento di base gratis.
4. **L'elenco completo delle versioni EGFX** (§8.1), da tenere allineato.
5. **`disable-animations: true`** nella creazione della sessione di cattura (§5). Una riga.
6. **La validazione della configurazione monitor** (§12.1): limiti, primario a (0,0), niente
   sovrapposizioni.
7. **La riconciliazione dei tasti a scatto dopo un ping** (§13.5), se e quando si passa a libei.

### 18.4 Le questioni aperte di REMOTIX su cui il riferimento dice qualcosa

| Questione | Cosa dice il riferimento |
|---|---|
| **n.1** — input touch | Implementato nativamente via MS-RDPEI + `ei_touch`, 256 contatti (§13.7) |
| **n.6** — bottone centrale e rotella orizzontale | **Caduta**: era un limite di IronRDP. FreeRDP consegna `MouseEvent`, `ExtendedMouseEvent` e `RelMouseEvent` distinti (§6.2, §13.3) |
| **n.7** — disposizione di tastiera | Non si concorda: **si legge dalla sessione** via `ei_device_keyboard_get_keymap` (§13.1). In alternativa il KLID è in `rdpSettings` |
| **n.9** — mstsc, sfondo al 75% dopo cambio di misura | Nessuna corrispondenza diretta, ma §12 suggerisce dove guardare: il riferimento **non manda nulla** fra l'inibizione e la conferma di tutti gli stream. Se REMOTIX manda il fotogramma conservato prima che il palco sia coerente, il sintomo è quello |
| **n.10** — sessione non registrata in logind | Il riferimento usa `sd_session_get_class` e `sd_session_is_remote` (`grd-daemon-utils.c:195`), quindi **assume** che la sessione sia registrata. Nei modi headless è chi avvia la sessione a doverlo garantire, non il server |

---

## 19. Cosa non c'è

Per completezza, e per non cercarlo:

| Funzionalità | Stato |
|---|---|
| Encoder H.264 software | **Assente** — il ripiego è RemoteFX Progressive |
| Controllo del bitrate | **Assente** — CQP fisso, QP 22 |
| Adattamento di risoluzione alla banda | **Assente** — si regola solo la cadenza |
| Multitransport UDP (MS-RDPEUDP) | `SupportMultitransport = FALSE` |
| Gateway RDP (MS-TSGU) | Assente |
| Redirezione dischi del client | Assente (la FUSE serve solo ai file della clipboard) |
| Redirezione stampanti, seriali, USB | Assente |
| RemoteApp (RAIL) | Assente |
| Smartcard | Assente |
| Cache delle superfici EGFX | Dichiarata e sempre rifiutata (`CacheImportReply` vuota) |
| Backend X11 | Assente — solo Wayland, come REMOTIX |
| HEVC, AV1 | Impossibili: non sono in MS-RDPEGFX |
