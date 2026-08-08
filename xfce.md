# XFCE, labwc e wlroots — studio del codice, per la fase 11

*Scritto l'8 agosto 2026, aprendo il terzo desktop, con dieci ricerche parallele sui sorgenti clonati
alle versioni di Debian Trixie. È il sesto studio del progetto, dopo `protocollo-rdp.md`,
`gnome-remote-desktop.md`, `client-android.md`, `xrdp-funzionalita.md` e `kde.md`.*

> **Come si legge questo documento.** Ogni affermazione porta una marca, e la marca conta più della
> frase:
>
> | | |
> |---|---|
> | **[R]** | letto nel codice, con `file:riga`. **Non è una misura**: dice che cosa il programma *può* fare, non che cosa *fa* sulla nostra macchina |
> | **[M]** | misurato. Dove c'è, è detto su quale macchina e quando |
> | **[?]** | deduzione o ipotesi. Da trattare come una domanda aperta, non come un fatto |
> | **[✗]** | verificata **assente**, dicendo come è stata cercata e con quale controllo positivo |
>
> Il dettaglio con i `file:riga` sta nei **dieci rapporti** in `reference-xfce/rapporti/`
> (~9 000 righe). Qui c'è quel che serve per decidere e per scrivere.

---

## 1. In due minuti

**XFCE non ha un compositore proprio.** Su Wayland avvia **labwc**, e labwc è **wlroots** — la terza e
ultima famiglia del panorama. Serviti GNOME (Mutter) e KDE (KWin), questa chiude il giro.

**La differenza che cambia la forma del codice**, e che era già scritta in `LEZIONI.md` §3: wlroots
**fa tirare** i fotogrammi invece di spingerli. Non c'è PipeWire in mezzo, non c'è D-Bus: c'è un
protocollo Wayland, `zwlr_screencopy_manager_v1`, e per ogni fotogramma si fa
`capture_output → frame → copy → ready`. Il flusso non si «monta»: si chiede, uno per volta.

**Le sei risposte che contano, tutte migliori che su KDE:**

| | |
|---|---|
| **Il permesso della cattura** | ✅ **non esiste**. [M, portatile, 8 ago] Un client nudo (`env -i`, sole `XDG_RUNTIME_DIR` e `WAYLAND_DISPLAY`) vede 45 global e cattura al primo colpo. Nessun `.desktop`, nessun dialogo, nessun portale. L'unico cancello è l'UID: `/run/user/1000` è `drwx------` |
| **Il seat** | ✅ **non serve**. Con `WLR_BACKENDS=headless` non si crea mai una `wlr_session` e libseat non viene sfiorato: il muro su cui `kwin_wayland --drm` moriva **qui non esiste** |
| **La GPU** | ✅ **una variabile**: `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128`. Niente regola udev, niente permessi di nodo negati a tutta la sessione dell'utente |
| **Il ridimensionamento a caldo** | ✅ **sì**: `set_custom_mode` su un output headless non ha alcun tetto. Il ripiego «misura fissa alla connessione» che KDE ci ha imposto **non serve** |
| **La cadenza** | ⭐ **è un parametro nostro**: su headless il refresh dell'output *è* il periodo del timer dei fotogrammi |
| **Gli appunti** | ✅ **`appunti_wlr.c` funziona così com'è**: è scritto contro un protocollo di wlroots, e qui siamo in casa sua |

**E le cinque che costano:**

| | |
|---|---|
| ⛔ **Nessun protocollo crea un output** | `wlr-virtual-output` **non esiste** [✗]. Un output headless nasce **1280×720 cablati**, e labwc non ha né IPC né `<output>` in configurazione: la misura si dà **solo** col protocollo, **dopo** l'avvio |
| ⛔ **Il cursore è sempre dentro l'immagine** | il backend headless non ha `set_cursor`, quindi non esiste cursore hardware; e `overlay_cursor` **non lo toglie** — lo *forza* software. È la stessa forma di `KWIN_COMPOSE=O2`: una leva che sembra esserci e non fa niente |
| ⛔ **libei non esiste su wlroots** | [✗] cercato in wlroots, labwc, sway, wayfire, weston, xdpw, wayvnc: zero. `input.c` **diventa un client Wayland**: si riusano le tabelle, non il trasporto |
| ⛔ **`xfce4-power-manager` ci spegne l'output** | parla Wayland nativo e dopo **10 minuti** su rete elettrica manda `zwlr_output_power_v1(OFF)`; output spento ⇒ nessun fotogramma ⇒ `failed` sulla cattura |
| ⛔ **Al logout XFCE può ammazzare la nostra sessione** | se la riga del compositore non contiene *sia* `labwc` *sia* `--session`, `xfce4-session` esegue `loginctl terminate-session ''` |

**E il passo zero — *«chi, al mondo, fa questa cosa su questo desktop?»* — ha una risposta che va
detta per intera**: **nessuno fa RDP su wlroots senza monitor**. Un solo server RDP al mondo parla
con wlroots (Rust, licenza BSL) e **dichiara di richiedere un desktop già acceso**; `xrdp` non ha
Wayland dal 2017; `freerdp-shadow` non ha un backend Wayland e i manutentori hanno scritto che è
improbabile che arrivi; e chi passa dal portale su wlroots è **video-only**, perché
`xdg-desktop-portal-wlr` non implementa `RemoteDesktop`.

> ⭐ **Ma un precedente c'è, ed è dalla nostra parte.** wlroots un backend RDP **ce l'aveva**, ed è
> stato rimosso nella 0.10 *«interamente in favore di wayvnc»* dopo cinque issue di crash. La
> comunità ha già deliberato che il posto giusto per questa cosa è **un client esterno del
> compositore** — cioè esattamente dove siamo. E labwc **cita wayvnc alla lettera nella propria
> documentazione**, prevedendo l'output virtuale ridimensionabile dal client remoto.

---

## 2. La mappa: dove sta ciascuna cosa

| Che cosa | Dove | Versione Trixie |
|---|---|---|
| il compositore | `reference-xfce/labwc/` | **0.8.3** |
| la libreria del compositore | `reference-xfce/wlroots/` | **0.18.2** |
| i protocolli di wlroots | `reference-xfce/wlr-protocols/` | (screencopy, data-control, virtual-pointer, output-management…) |
| i protocolli standard | `reference-xfce/wayland-protocols/` | **1.38** |
| la sessione | `reference-xfce/xfce4-session/` | **4.20.2** |
| pannello, scrivania, impostazioni | `xfce4-panel/` 4.20.4, `xfdesktop/` 4.20.1, `xfce4-settings/` 4.20.1 | |
| l'astrazione X11/Wayland di XFCE | `libxfce4windowing/` | **4.20.2** |
| le librerie comuni | `libxfce4ui/` 4.20.1, `libxfce4util/` 4.20.1, `xfconf/` 4.20.0, `garcon/` 4.20.0 | |
| energia e blocco | `xfce4-power-manager/` 4.20.0, `xfce4-screensaver/` 4.18.4 | |
| **chi lo fa già** | `wayvnc/` 0.9.1 + `neatvnc/` 0.9.1, `weston/` 14.0.2 (backend RDP), `xdg-desktop-portal-wlr/` 0.7.1 | |
| i termini di paragone | `sway/` 1.10.1, `wayfire/` 0.9.0 | |

⚠ **Le versioni installate sul server coincidono esattamente con quelle clonate** [M, 8 ago]: labwc
0.8.3-1, xfce4-session 4.20.2-2, xfce4-panel 4.20.4-1, xfdesktop4 4.20.1-1, xfce4-settings 4.20.1-1,
sway 1.10.1-2, weston 14.0.2-1. Lo studio e il banco parlano della stessa macchina.

⚠ **Wayfire non è nella stessa famiglia di codice**: `meson.build:45,49` chiede wlroots
`>=0.17.0, <0.18.0` e lo vendorizza. Tutto quel che segue vale per **labwc** (il nostro bersaglio) e
per **sway** (il termine di paragone). Wayfire va riletto sulla 0.17 se e quando servirà.

---

## 3. ✅ Il cancello che non c'è

Su KWin questa sezione è la più lunga del documento e ha richiesto cinque prove di banco. Qui si
chiude in tre righe, ed è **misurata** [M, portatile con labwc 0.8.3, 8 agosto 2026] prima ancora che
dedotta.

| | |
|---|---|
| **Che cosa vede un client nudo** | 45 global, fra cui `zwlr_screencopy_manager_v1` **v3**, `zwlr_virtual_pointer_manager_v1` **v2**, `zwp_virtual_keyboard_manager_v1` **v1**, `zwlr_data_control_manager_v1` **v2**, `zwlr_layer_shell_v1` v4 |
| **Che cosa serve nell'ambiente** | `XDG_RUNTIME_DIR` e `WAYLAND_DISPLAY`. Nient'altro: la cattura è riuscita al primo colpo (`buffer(1280×720, stride 5120)` → `copy()` → `ready`, checksum non nullo) |
| **Il codice che lo spiega** | `labwc/src/server.c:344` — `return true` per ogni client **senza** security context; `wlroots/types/wlr_security_context_v1.c:435-437` — chi entra dal socket normale non ha contesto |

**[✗] wlroots 0.18.2 non filtra nulla**: zero chiamate a `wl_display_set_global_filter` in tutto
l'albero. Il filtro che labwc e sway hanno scatta **solo** sui client entrati da un `listen_fd`
altrui, cioè Flatpak e bwrap — e noi non ci saremo mai. Wayfire non filtra affatto.

⛔ **E non esiste il verso opposto**: `rc.xml` di labwc **non ha alcun interruttore di protocollo**
[✗], su nessuno dei tre compositori. Un amministratore che volesse *chiudere* la cattura non ha una
leva di configurazione — informazione che ci riguarda perché significa che **nessuno può chiuderci la
porta per errore**.

### 3.1 ⚠ Dove sta il rischio, invece: la diagnosi

Il permesso non è il pericolo; il pericolo è **non vedere perché una cosa fallisce**.

| | |
|---|---|
| ⛔ **labwc non logga** | né la connessione né il `bind`, nemmeno con `-d`. Su richiesta illegale scrive solo `error in client communication (pid N)`, a livello **INFO** (invisibile senza `-V`): il PID, non l'interfaccia né il codice |
| ⛔ **`WLR_DEBUG` non esiste** [✗] | `wlroots/util/log.c` non ha un solo `getenv`. Il livello lo decide il compositore, con `-d`/`-V` sulla riga di comando |
| ✅ **La diagnosi si fa dal lato client, ed è ottima** | libwayland stampa da sé su stderr `zwlr_screencopy_frame_v1#3: error 1: invalid buffer dimensions`, e `wl_display_get_protocol_error()` restituisce **interfaccia e codice**. `WAYLAND_DEBUG=1` dà la traccia completa |

⭐ **Da cui una regola per il nostro codice**: dopo *ogni* fallimento, chiamare
`wl_display_get_protocol_error()` e scriverne l'esito. È l'equivalente della lezione §1.10 — *prima di
provare varianti, farsi dire la causa* — con la differenza che qui il componente che nega non parla, e
il nostro cliente sì.

### 3.2 ⛔ Un errore di protocollo uccide la connessione

Non è un fotogramma perso: è la connessione. [M] `roundtrip = -1`, `EPROTO`, nessuna ripresa — va
rifatto tutto da `wl_display_connect`.

**Le tre regole che ne discendono, e che valgono per tutto il codice nuovo:**

1. **Formato, dimensioni e stride si copiano *esattamente* dall'evento `buffer`.** Nessun allineamento
   nostro (`wlroots/types/wlr_screencopy_v1.c:384-432`);
2. **un solo `copy()` per frame**, poi un `capture_output()` nuovo (`:391`);
3. **la keymap prima del primo tasto**, o `no_keymap` (`wlroots/types/wlr_virtual_keyboard_v1.c:84,107`).

---

## 4. La cattura: `zwlr_screencopy_manager_v1`

*Dettaglio: `reference-xfce/rapporti/01-cattura-screencopy.md`.*

### 4.1 ✅ Fotogrammi interi, sempre — e il difetto di GNOME non si ripresenta

`frame_shm_copy`/`frame_dma_copy` usano `frame->box`, cioè **l'output intero**, e non consultano mai
il danno (`wlr_screencopy_v1.c:214-219`, `:255-268`). Il buffer sorgente è a sua volta completo grazie
al *buffer age* del damage ring (`types/scene/wlr_scene.c:1910-1911`).

⭐ **Cioè la trappola che su GNOME tiene spenta la copia zero — il buffer che è un «diff» su quattro
buffer riciclati, R29 — qui non esiste.** Un pool di buffer riusati va bene senza precauzioni, e la
superficie di accumulo non serve.

### 4.2 ⛔ Il modello a tiro, e le sue due trappole

| | |
|---|---|
| **`copy_with_damage` a schermo fermo** | ⛔ **`ready` non arriva mai**, e non c'è alcun timeout: il listener resta agganciato (`:297-303`). Serve **un timer nostro** che, scaduto, distrugga il frame e riapra con `copy` semplice |
| **`copy` semplice** | ⛔ chiama `wlr_output_update_needs_frame()` (`:448`), cioè **forza il rendering** anche a schermo immobile. Un ciclo ingenuo a 30 fps fa rendere al compositore 30 fotogrammi al secondo di nulla |

⭐ **La forma giusta la mostra wayvnc**, ed è la correzione strutturale al problema dei 18 fps del
7 agosto: `copy_with_damage` di regola, `copy` intero solo quando serve un fotogramma subito (primo
client, cambio output, cambio misura, riaccensione) — e **la cadenza sottrae la latenza misurata del
compositore**: `time_left = 1/rate − dt − delay`, con `delay` misurato a ogni `ready` e filtrato
passa-basso a 0,5 s (`wayvnc/src/screencopy.c:308`, `:214-215`).

### 4.3 ⭐ Il libro doppio del danno — obbligatorio, non un'ottimizzazione

Ogni buffer porta **due** danni: `frame_damage` (che va al codificatore) e `buffer_damage` (che va al
compositore). Quando un fotogramma è pronto con danno D, D si somma al `buffer_damage` di **tutti** i
buffer del pool (`wayvnc/src/buffer.c:693-704`).

⛔ **Senza, si mandano fotogrammi con pezzi vecchi, e nessuna misura di fotogrammi al secondo lo
rivela** — è il difetto di R29 in forma generale, e la ragione per cui va scritto ora e non poi.

⚠ E il danno di wlroots è **un solo rettangolo** (gli extents, con un `// TODO` esplicito a
`:168-178`), in coordinate pixel dell'output, **non** traslato per `capture_output_region`. Va
**ritagliato** al rettangolo del buffer prima di fidarsene, come fa wayvnc (`main.c:1145-1146`).

### 4.4 La copia zero: possibile, e in una forma migliore di quella di Mutter

| Strada | Che cosa consegna | Verdetto |
|---|---|---|
| **`copy` su buffer DMA-BUF** | un **blit GPU** dentro un buffer **di proprietà del client** (`wlr_renderer_begin_buffer_pass` + `add_texture` + `submit`, `wlr_screencopy_v1.c:249-270`) | ✅ **la nostra strada**: niente lettura CPU, buffer stabile, formato per VA-API |
| `copy` su buffer shm | `glFinish()` + `glReadPixels` (`render/gles2/texture.c:206,218`) | ⛔ **blocca il ciclo principale del compositore** |
| `zwlr_export_dmabuf_v1` | il buffer *del compositore*, ma con flag **TRANSIENT** sempre alzato (`wlr_export_dmabuf_v1.c:75`) | ⛔ è la trappola di GNOME in forma pura. Da scartare |

⚠ **Non è copia zero in senso stretto** — c'è un blit — ma è **una copia sola, sulla scheda**, e il
buffer è nostro: è precisamente la forma che le fasi 8 e 9 hanno imparato a consumare.

⚠ **La sincronizzazione**: con GLES2 il ramo DMA-BUF fa solo `glFlush()` (`render/gles2/pass.c:39`),
**nessuna fence esplicita**: si dipende dal sync implicito. Il renderer Vulkan invece importa
correttamente una sync file nel DMA-BUF (`render/vulkan/renderer.c:1025-1029`) — ma in `auto` Vulkan
**non è mai tentato** in 0.18.2 (`wlr_renderer.c:244`). È lo stesso punto che su Mutter è costato la
fase 9, e va **misurato** prima di crederci.

⚠ **I modifier non vengono dall'evento `linux_dmabuf`**, che porta solo format/width/height
(xml:214-223) e non è controllato da wlroots: vanno presi dal feedback di `zwp_linux_dmabuf_v1`, come
fanno wayvnc e il portale.

### 4.5 Formati e profondità

Il formato shm lo sceglie il renderer via `GL_IMPLEMENTATION_COLOR_READ_FORMAT` e **non è
richiedibile**; il campo va trattato come **fourcc**, non come enum (`render/pixel_format.c:215-224`).
`BGR888` a 24 bit esiste in tabella ma **[?]** non uscirà mai dalla query GL: si riceve 32 bit e si
converte a valle — come su Mutter, dove R32 aveva già stabilito che un percorso a 24 bit impacchettati
non esiste.

### 4.6 Il successore, e perché il codice va scritto con due implementazioni

**[✗] `ext-image-copy-capture-v1` non esiste** in wlroots 0.18.2, labwc 0.8.3, wayfire 0.9.0 né sway
1.10.1 (grep a zero su tutti e quattro, con controllo positivo su `screencopy`). Su Trixie **l'unica
via è `zwlr_screencopy`**.

Ma **wayvnc 0.9.1 lo parla già**, e sceglie a runtime in dodici righe
(`wayvnc/src/screencopy-interface.c:29-45`), con le capacità diverse in una maschera di bit e **un
solo punto** in cui il codice si dirama. ⭐ **È la forma da copiare**, perché il protocollo nuovo
porta due cose che ci servono: i **modifier**, e una **sessione cursore** con posizione e hotspot —
cioè la cura definitiva al doppio puntatore.

⚠ E porta anche un cambio di modello da sapere adesso: **il nuovo protocollo è a diff** («at least
the union of the region passed by the client and the region advertised by `damage`»), con danno pieno
solo al primo fotogramma. Chi lo scriverà senza sapere questo ripaga R29 una terza volta.

---

## 5. Senza monitor: headless, GPU, cadenza

*Dettaglio: `reference-xfce/rapporti/03-output-headless-gpu.md`.*

### 5.1 ✅ Nessun seat, nessun libseat

`grep session|libseat|drm backend/headless/` → **vuoto** [✗]. Con `WLR_BACKENDS=headless` non si crea
mai una `wlr_session` (`backend/backend.c:308-316`). Il muro su cui `kwin_wayland --drm` usciva con
stato 1 da una shell SSH **qui non esiste**, e non serve alcun `Activate()` di logind.

### 5.2 ⭐ La GPU si sceglie con una variabile — e il ripiego è la trappola

| | |
|---|---|
| **Come si sceglie** | `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128` (`render/wlr_renderer.c:147-158`, accetta solo `renderD*`) |
| **Il default** | il **primo** render node di `drmGetDevices2()`, con `break` immediato |
| ⛔ **Il ripiego** | **non esiste**: se l'`open` fallisce, wlroots **non prova l'altra scheda** — cade in **pixman**, cioè in software, senza errore |

⭐ **Da cui: la regola udev di KDE non serve, e negare un nodo sarebbe controproducente.** Su KWin
negare il nodo era l'unico modo di scegliere la scheda, e il prezzo era negarlo a tutta la sessione
dell'utente. Qui basta una variabile d'ambiente.

⚠ **E la lezione §1.11 vale identica**: «render node aperto» non prova la GPU nemmeno qui, e
«DMA-BUF offerto» prova **l'allocatore**, non il disegno. **[✗] Non esiste API né IPC per chiedere il
renderer** in 0.18.2 (`struct wlr_renderer` non ha `name`): niente di equivalente a
`supportInformation` di KWin. Restano due strade, entrambe da usare: **`-V` all'avvio del
compositore** (labwc e sway partono a `WLR_ERROR` e non stampano `GL renderer:` senza), e il
**controllo positivo obbligatorio** — rifare la misura con `WLR_RENDERER=pixman` e vedere che
**cambia**.

Con headless e default: **GLES2 + allocatore GBM** (`allocator.c:101-103`), quindi la copia zero è
disponibile. Con pixman l'allocatore è shm e screencopy **non offre affatto** il formato DMA-BUF
(`wlr_screencopy_v1.c:574-577`) — il che, notato di passaggio, è una prova *negativa* utile: se il
DMA-BUF non viene offerto, siamo in software.

### 5.3 ⭐ La cadenza è un parametro nostro

Su un output headless `frame_delay = 1 000 000 / refresh_mHz` ms (`backend/headless/output.c:25-32`):
**il terzo argomento di `set_custom_mode` diventa il periodo del timer dei fotogrammi.**

| refresh dichiarato | periodo | tetto |
|---|---|---|
| 60 Hz | 16 ms | **62,5 fps** |
| 30 Hz | 33 ms | 30 fps |

Nessun altro compositore ci ha mai dato questa leva: su Mutter la cadenza si dichiarava a PipeWire e
se ne ottenevano sei decimi; su KWin il tetto era `maxFramerate` e lo onorava il server. ⚠ wayvnc lo
lascia a 0 con un TODO, quindi qui **non abbiamo un precedente da copiare**.

⛔ **E i fotogrammi si tirano davvero**: niente danno ⇒ niente commit
(`types/scene/wlr_scene.c:1705-1709`) ⇒ il timer non si riarma (`headless/output.c:76`). A riaccendere
è la cattura stessa, con `wlr_output_update_needs_frame()` dentro `copy`.

### 5.4 ⛔ Due silenzi da conoscere prima di scrivere

1. **Mai toccare l'adaptive sync**: `ADAPTIVE_SYNC_ENABLED` è **fuori** dalla maschera headless
   (`headless/output.c:10-14`) e fa fallire **l'intero** commit con `Unsupported output state fields:
   0x40` — che sembra un rifiuto della misura. `false` invece è un no-op silenzioso;
2. **Chiedere la misura che l'output ha già** non produce un modeset: `output_compare_state` toglie il
   campo `MODE` e il commit riesce **senza fare niente** (labwc lo aggira alzando la larghezza di 1,
   `labwc/src/output.c:1084-1104`).

E una terza, sul protocollo di configurazione: **serial vecchio ⇒ `cancelled`, non `failed`**
(`wlr_output_management_v1.c:446-455`). Chi ascolta solo `succeeded`/`failed` resta appeso per sempre.

---

## 6. ✅ Il ridimensionamento a caldo: si può — e il ripiego di KDE non serve

*È la domanda 13 di `LEZIONI.md` §3, quella che su KWin ha deciso metà del piano.*

`zwlr_output_configuration_head_v1::set_custom_mode` ridimensiona un output headless a caldo.
**L'unica validazione in tutto il percorso** è `width<=0 || height<=0 || refresh<0`
(`wlr_output_management_v1.c:216-241`) più `pending_width==0` (`types/output/output.c:593-596`).
**[✗] Nessun tetto**, cercato con grep su wlroots e sui tre compositori.

**Il precedente esiste e non è nostro**: wayvnc ridimensiona l'output alla risoluzione del client
(`wayvnc/src/main.c:802-826` → `output-management.c:230-287`), e da lì si copia anche la disciplina —
**enumerare tutte le head** con enable/disable, o wayfire rifiuta.

### 6.1 ⛔ Ma l'output NON si crea, e non si distrugge

| | |
|---|---|
| **[✗] `wlr-virtual-output` non esiste** | dieci protocolli in `wlr-protocols/unstable/`, nessuno crea output. `wlr-output-management` li *configura*: *«Heads cannot be created nor destroyed by the client»* |
| **[✗] Nessuna variabile dà la misura iniziale** | ⚠ *precisato l'8 agosto, studiando LXQt*: le misure cablate sono **due, diverse secondo la via** — `WLR_HEADLESS_OUTPUTS` crea output **1280×720** (`wlroots/backend/backend.c:237`), mentre gli output virtuali **di labwc** nascono **1920×1080** (`labwc/src/output-virtual.c:52-53`). Nessuna delle due porta la misura: `WLR_HEADLESS_OUTPUTS` porta solo il **numero** |
| **[✗] labwc non ha IPC** | `grep -rli ipc labwc/src` → nulla, e `rc.xml` non ha alcun `<output>`. `VirtualOutputAdd` accetta il **nome** ma non la misura ed è raggiungibile **solo da keybind**. ⚠ Esiste però **`LABWC_FALLBACK_OUTPUT`** (`output-virtual.c:109-135`): a layout **vuoto** labwc crea da sé un output virtuale col nome dato — ed è il meccanismo che upstream documenta perché un nome `NOOP-…` faccia riconoscere a wayvnc un output ridimensionabile. Scatta **solo** a layout vuoto, quindi vuole `WLR_HEADLESS_OUTPUTS=0` [?, da provare] |

⭐ **Da cui la forma obbligata**: si avvia il compositore headless, ci si collega, e **si ridimensiona
l'output esistente**. Non «si crea l'output della misura chiesta», che è quel che facevamo su KWin con
`--virtual --width/--height`.

⛔ **E distruggere e ricreare è vietato da tre parti diverse**, tutte in XFCE:

| | |
|---|---|
| `xfsettingsd` | se compare un output **nuovo** lo **disabilita** e lancia `xfce4-display-settings` (`displays-wayland.c:524-528`, `:541-546`). ⚠ E attenzione al verso: `action <= SHOW_DIALOG` significa che **anche `/Notify=0` disabilita** — servono 2 o 3 |
| `xfce4-panel` | esce senza far niente se `n_monitors == 0` (`panel-window.c:2640-2642`, commento «temporary state on Wayland») |
| `xfdesktop` | perde le impostazioni dello sfondo se cambia il nome del connector: **la chiave xfconf *è* il connector** (`xfdesktop-backdrop-manager.c:169`) |

⚠ E un dettaglio da tenere per il banco: il pannello **non usa** l'API monitor di
`libxfce4windowing` [✗], ascolta `GdkScreen::monitors-changed`. Quel che dobbiamo far scattare è GDK.

---

## 7. L'input: `input.c` diventa un client Wayland

*Dettaglio: `reference-xfce/rapporti/04-input.md`.*

**[✗] libei non esiste su wlroots** — cercato `libei|EIS|ei_device|ei_seat|ei_new` in wlroots, labwc,
sway, wayfire, weston, xdg-desktop-portal-wlr e wayvnc: zero, con controllo positivo su
`virtual_keyboard` che dà 67/15/16/10 righe. E **[✗] `xdg-desktop-portal-wlr` non ha `RemoteDesktop`**
(`wlr.portal:3`: solo Screenshot e ScreenCast).

Quindi: `zwp_virtual_keyboard_manager_v1` **v1** e `zwlr_virtual_pointer_manager_v1` **v2**, senza
alcun permesso (wlroots non filtra; labwc e sway filtrano solo i client in sandbox).

### 7.1 Che cosa si riusa, e che cosa si riscrive

| | |
|---|---|
| ✅ **si riusa** | le tabelle scancode set 1 → VK → evdev, la mappa dei pulsanti, la macchina a stati del tasto Pausa, la logica di sessione. L'offset evdev↔X11 è **8** in entrambe le direzioni |
| ⛔ **si riscrive** | il trasporto (D-Bus/EIS → `wl_registry`) e **tutta la gestione dei modificatori**, che con libei non esisteva |

**[?] Circa metà del file.** ⚠ E una decisione da prendere **prima** di scrivere: se anche la cattura
è un protocollo Wayland, **una sola connessione `wl_display` serve entrambi**.

### 7.2 ⛔ Le cinque trappole silenziose

| # | | |
|---|---|---|
| 1 | **La rotella vuole scatti da ±1**, non ±120 | `axis_discrete(t, axis, value, discrete)` con `discrete` **in scatti interi**; wlroots moltiplica **lui** per 120 (`wlr_virtual_pointer_v1.c:183-184`). La convenzione di KWin qui darebbe **120 scatti** |
| 2 | **`value` non deve mai essere 0** | con `value == 0` parte un `axis_stop` e lo scatto sparisce (`wlr_seat_pointer.c:369-391`). wayvnc usa **15.0**, «valore magico misurato con `wev`» |
| 3 | **Senza `frame` non arriva niente** | gli assi restano nel buffer (`wlr_virtual_pointer_v1.c:109-122`), e `frame` serve a **tutti** gli eventi, non solo alla rotella |
| 4 | **I modificatori li mandiamo noi, sempre** | wlroots costruisce l'evento con `update_state = false` (`:92`) e non aggiorna `xkb_state`: **senza `modifiers`, Shift+A dà `a`**. Serve un `xkb_state` nostro |
| 5 | **`wlr_pointer_finish()` non rilascia i pulsanti** (`types/wlr_pointer.c:38-42`) | alla disconnessione dobbiamo mandare noi `button(release)` + `frame` prima di `destroy`, o **il desktop resta col tasto sinistro premuto**. La tastiera invece li rilascia da sola |

⚠ **Il verso della rotella**: verticale **invertito** rispetto a Wayland, orizzontale no — e **nessuno
lo corregge per noi**, perché su un device virtuale labwc salta libinput (`scroll_factor = 1.0`,
niente natural scrolling né accelerazione). Su sway e wayfire invece `scroll_factor` **si applica
anche a noi**. Weston conferma la conversione riga per riga, ed è il pezzo più prezioso del suo
backend RDP: valore negli 8 bit bassi dei flag, negativo = `(0xff - v) * -1`, **due accumulatori per
asse** (`≥ 12` passo fluido, `/120` scatto discreto, con `%=` che conserva il resto).

### 7.3 ⭐ I lucchetti si leggono — ma solo perché il compositore è labwc

wlroots manda `wl_keyboard.modifiers` **solo al client con il fuoco**
(`seat/wlr_seat_keyboard.c:191-213`). Noi non abbiamo una surface, quindi non dovremmo vedere niente.

**Ma labwc lo trasmette a tutti, senza surface** (`input/keyboard.c:106-133`, chiamato a `:186-193`),
con un commento che dice che **sway lo faceva e ha smesso**. Quindi `mods_locked` dà BlocMaiusc e
BlocNum **veri**, e `group` dà il layout.

| | |
|---|---|
| ✅ | su KDE questa risposta era costata un protocollo dedicato (`org_kde_kwin_keystate`) |
| ⚠ | **è comportamento di labwc, non di protocollo**: su sway la stessa lettura è `[✗]` |
| ⚠ | **lo stato iniziale non arriva mai** — si conosce il primo cambiamento, non la situazione di partenza |
| ⚠ | attenzione all'**anello di retroazione** coi nostri stessi `modifiers` |

### 7.4 La keymap: presentarla noi, ma copiata dal filo

Obbligatoria prima di ogni `key` (`no_keymap`, `wlr_virtual_keyboard_v1.c:83-88`). ⭐ **La forma
giusta**: fare `wl_seat.get_keyboard` — wlroots manda `keymap` subito, senza fuoco
(`seat/wlr_seat_keyboard.c:412-417`) — e **rigirare quel contenuto**. È meglio di wayvnc, che la
genera da configurazione, e c'è una ragione forte: su labwc **ogni tasto** fa
`wlr_seat_set_keyboard`, che **rimanda la keymap a tutti i client**.

✅ **La ripetizione non la facciamo noi**: nessuno ripete lato compositore, i `key down` ripetuti di
RDP sono comunque **scartati** da wlroots (`wlr_keyboard.c:68-83`), e la ripetizione la fa
l'applicazione via `repeat_info`.

### 7.5 ⚠ Le nostre scorciatoie le mangia labwc

`match_keybinding(..., is_virtual)` salta il confronto per keycode ma **applica comunque le
scorciatoie** (`input/keyboard.c:225-228`, `:548-560`), e le mousebind di scorrimento ingoiano lo
scatto usando anche **i nostri** modificatori (`keyboard_get_all_modifiers`, `:57-79` — con un
commento che nomina wayvnc). Da mettere in conto: parte di quel che mandiamo non arriva alle
applicazioni.

### 7.6 Il seat: si inietta in quello esistente

**[✗] labwc non crea `ext_transient_seat_v1`** (sway sì, wlroots ce l'ha). Su XFCE **non c'è scelta**:
si inietta nel seat dell'utente. ⭐ E dato che REMOTIX gira **senza utente presente**, è anche il caso
migliore — è precisamente ciò che ci regala la lettura dei lucchetti veri di §7.3.

---

## 8. ✅ Gli appunti: `appunti_wlr.c` funziona così com'è

*Dettaglio: `reference-xfce/rapporti/05-appunti.md`.*

`zwlr_data_control_manager_v1` **v2** su tutti e tre i compositori, senza permessi. Il file l'abbiamo
scritto per KWin ma **contro il protocollo di wlroots**: qui siamo in casa sua.

**Le due lezioni pagate su KWin reggono, e per lo stesso motivo meccanico:**

| | |
|---|---|
| **L'eco è certa, non probabile** | ogni device si iscrive a `seat->events.set_selection` **senza filtro sull'originatore** (`wlr_data_control_v1.c:620-622`) |
| **`cancelled` precede `selection`** | e più solidamente che su KWin: sta tutto dentro `wlr_seat_set_selection` — riga 196 distrugge la vecchia source, riga 211 emette il segnale. **Due righe della stessa funzione, nessun rientro asincrono in mezzo.** La guardia di stato **non va rivista** |
| **`POLLHUP` vale come «pronto»** | `client_source_send` fa `close(fd)` subito dopo l'evento (`:131`): con dati corti la `poll` torna con solo `POLLHUP` |

**Le tre riserve, tutte nostre e tutte piccole:**

1. **[?] `kwin_display_apri`** (`appunti_wlr.c:441`): se filtra il socket per nome, su labwc non si
   apre nulla. È l'unica cosa che può impedire al file di funzionare;
2. **wlroots scarta i MIME duplicati in silenzio** (`:47-54`) e la nostra `tipi_uguali` boccia su
   lunghezza diversa: un duplicato nell'elenco del client ⇒ guardia saltata ⇒ **ciclo infinito**;
3. lo scavalco `onlyReplaceEmpty` è inutile qui: **[✗]** assente da tutto l'albero.

⭐ **E c'è una guardia migliore della nostra, da valutare**: wayvnc offre un **secondo MIME sintetico**
`x-wayvnc-client-%08x` e, se lo rivede in un'offerta, sa che è sua e la ignora
(`wayvnc/src/data-control.c:196-199`). È più solido di un confronto sui tipi, e in RDP il problema è
identico.

**Il resto, in breve**: **[✗] `ext-data-control-v1` non esiste** né in wlroots 0.18.2 né in
wayland-protocols 1.38 — su Trixie `zwlr` è l'unica porta, benché a monte sia già marcato deprecato.
Il ponte Xwayland funziona **in entrambe le direzioni gratis**, passando dallo stesso stato del seat.
La clipboard **non sopravvive alla morte di chi ha copiato**, e in XFCE su Wayland **non c'è nessun
gestore** (`xfsettingsd` lo avvia solo sotto X11): cioè il coinquilino che su KDE era klipper qui non
c'è.

---

## 9. La sessione XFCE senza monitor

*Dettaglio: `reference-xfce/rapporti/06-sessione-xfce.md`.*

### 9.1 Il compositore è cablato in uno script

`default_compositor="labwc"` in `xfce4-session/scripts/startxfce4.in:121` — **non è una
configurazione, è una riga di script**. Si sostituisce solo passando la riga di comando a
`startxfce4 --wayland <cmd>` (`:37-40`, `:164`), oppure con `XFCE4_SESSION_COMPOSITOR`, che viene
`exec`-ato tal quale (`xinitrc.in:147`).

⭐ **La riga da copiare**: `labwc --config-dir … --config … --session xfce4-session`. Il `--session`
rende `xfce4-session` il *primary client*: quando esce, **labwc termina**
(`labwc/src/main.c:43`, `:96-104`; `server.c:167-170`). Il logout viene gratis.

### 9.2 ⛔ La trappola che può ammazzare la nostra sessione

Se `XFCE4_SESSION_COMPOSITOR` non contiene **sia** `labwc` **sia** `--session`, al logout
`xfce4-session` esegue **`loginctl terminate-session ''`** (`xfce4-session/main.c:257-273`) — cioè la
sessione logind di REMOTIX.

**Doppia difesa**, e vanno messe tutte e due: xfconf `xfce4-session` `/general/WaylandLogoutCommand`
= `/bin/true` (ha la precedenza, `:259`) **più** la variabile d'ambiente scritta come si deve.

⚠ **È la prima cosa da provare sul banco**, e mai sull'utente (`LEZIONI.md` §2.6).

### 9.3 L'ambiente: che cosa mettere e che cosa togliere

| Mettere | Perché |
|---|---|
| `XDG_RUNTIME_DIR` | labwc esce senza (`main.c:201-204`) |
| `XDG_CURRENT_DESKTOP=XFCE` | **prima** di labwc, che altrimenti la mette a `labwc:wlroots` con `overwrite=0` (`config/session.c:249`) |
| `XDG_MENU_PREFIX=xfce-` | ⚠ **non perché manchi** — garcon ripiega su `xfce-` da sé (`garcon-private.h:37-39`, con un commento che dice espressamente «so garcon doesn't break when xfce is not started with startxfce4»). Il pericolo è **ereditarne una sbagliata** (`plasma-`, `gnome-`) **o vuota**: il test è `prefix != NULL`, non `*prefix`, e allora `garcon_menu_load()` fallisce con `G_FILE_ERROR_NOENT` **senza alcun ripiego**. È la lezione §1.10 in forma rovesciata: non «metti la variabile», ma **«componi l'ambiente da zero, o ti porti dietro quella di un altro desktop»** |
| `WLR_BACKENDS=headless` | e `WLR_LIBINPUT_NO_DEVICES=1`, che è la ricetta dichiarata da wayvnc (`FAQ.md:3-8`) e **[M]** provata sul portatile |
| `WLR_RENDER_DRM_DEVICE` | la scheda, §5.2 |
| `LABWC_UPDATE_ACTIVATION_ENV=1` | ⚠ **obbligatoria**: labwc propaga `WAYLAND_DISPLAY` al bus e a systemd **solo se il backend è DRM** (`config/session.c:186-207`). Su headless non lo fa, **in silenzio** |
| `XCURSOR_THEME` (+ `XCURSOR_SIZE`) | §10.1 |

| Togliere | Perché |
|---|---|
| `WAYLAND_DISPLAY`, `WAYLAND_SOCKET` | backend annidato (`wlroots/backend/backend.c:375-402`) |
| `DISPLAY` | backend X11 — e su GTK fa ripiegare su X11 **in silenzio**, riaccendendo XSETTINGS, grab della tastiera e systray XEmbed: **due comportamenti sotto la stessa etichetta**, cioè la lezione §1.8 |
| `SESSION_MANAGER` | `xfce4-session` esce (`main.c:97-102`) |
| `GDK_BACKEND` | va messo a **`wayland` secco**, non `wayland,x11` |

⚠ **`~/.ICEauthority` deve essere scrivibile**: `xfce4-session` esce anche su Wayland se non riesce ad
aprirlo (`main.c:114-127`).

### 9.4 ⚠ Otto secondi per gruppo di priorità, e sono strutturali

Su Wayland **nessun client si registra al gestore di sessione**, quindi ogni gruppo di priorità si
sblocca **a timeout**: `STARTUP_TIMEOUT_WAYLAND = 8000` (`xfsm-manager.h:43`).

E la ragione è definitiva, non un caso limite: `xfce-sm-client.c` è compilato **solo dentro
`if ENABLE_X11`** (`libxfce4ui/Makefile.am:73-82`), `configure` forza `enable_libsm=no` senza X11, la
connessione è XSMP puro e richiede `$SESSION_MANAGER`, che `xfce4-session` esporta solo nello strato
X11. **[✗] Nessuno può registrarsi su Wayland, e nessuna chiave xfconf accorcia il timeout** — le
costanti sono cablate.

⭐ **Da cui: il timeout di REMOTIX per «il desktop è su» va tarato ≥ 8 s**, e una sessione salvata con
priorità diverse lo moltiplica.

### 9.5 Il logout: sorveglianza passiva, come su KDE

| | |
|---|---|
| **bus** | `org.xfce.SessionManager` |
| **path** | `/org/xfce/SessionManager` |
| **interfaccia** | `org.xfce.Session.Manager` ⚠ **nome ≠ interfaccia**, attenzione al punto |
| **segnale** | `StateChanged(u old, u new)` — 0 Startup, 1 Idle, 2 Checkpoint, 3 Shutdown, 4 Phase2 |
| **«il desktop è su»** | `StateChanged(old=0, new=1)` (`xfsm-manager.c:861-867`). ⚠ Usare `old==0`: il Checkpoint produce 1→2→1 |

✅ **Non registrarsi e non inibire**: `Logout` **non consulta l'inibitore**
(`xfsm-manager.c:2409-2431`), e un `RegisterClient` ci farebbe aspettare fino a `DIE_TIMEOUT` — lo
stesso errore che su KDE avrebbe frenato il logout di quindici secondi.

### 9.6 ⚠ La sessione salvata è legata al nome del socket

`~/.cache/sessions/xfce4-session-<display>` con `display` = `wayland-0`… Un socket diverso è una
sessione diversa, e **una sessione salvata sbagliata risorge con priorità e geometrie di un altro
schermo**. `SaveOnExit` è già `false` di default, ma la cache va **cancellata a ogni avvio**.

È la stessa forma del difetto di KDE, dove plasmashell scriveva `SceneGraphBackend=software` in modo
persistente: **una sessione avviata male lascia un segno nella casa dell'utente**.

### 9.7 Il bus di sessione — una decisione da prendere

`startxfce4 --wayland` usa **`dbus-run-session`**: bus privato che nasce col compositore e muore col
logout. ⚠ Se lo usiamo, **il sorvegliante di REMOTIX non vede `StateChanged`**.

Su Trixie `dbus-user-session` è installato, quindi **[?] la strada raccomandata è il bus d'utente di
systemd** (`$XDG_RUNTIME_DIR/bus`) senza `dbus-run-session`. È una scelta di progetto, da provare.

---

## 10. Il sistema attorno: cursore, energia, voci di menu

*Dettaglio: `reference-xfce/rapporti/07-componenti-xfce.md` e `06-sessione-xfce.md` §13.*

### 10.1 ⭐ Il cursore: la cura di KDE si trasporta, con un vincolo in meno

**Il fatto**: su output headless il cursore è **sempre** dentro l'immagine catturata. Il backend
headless non implementa `set_cursor` [✗], quindi non esiste cursore hardware, quindi la scena lo
dipinge nel framebuffer (`types/output/cursor.c:285-289`, `types/scene/wlr_scene.c:1998`). E
`overlay_cursor` **non toglie niente**: *forza* i cursori software (`wlr_screencopy_v1.c:451-454`).

⭐ **La cura è la stessa di KDE — rendere il cursore invisibile, non nasconderlo**: un tema
`XCURSOR_THEME` con un cursore 1×1 ad alfa zero, e il puntatore torna a essere quello del client.

| | |
|---|---|
| ✅ **un vincolo in meno** | su labwc il tema arriva da `XCURSOR_THEME`/`XCURSOR_SIZE` **dell'ambiente** (`labwc/src/input/cursor.c:1405-1414`), e **`XCURSOR_SIZE` non è obbligatoria** (default 24 nella riga stessa) — a differenza di KWin, che il tema lo guardava solo se c'era anche la misura |
| ⛔ **la stessa trappola** | se il tema carica **zero** cursori, wlroots ripiega su un tema **incorporato e visibile** (`wlr_xcursor.c:219-221`). Serve almeno un cursore valido, `index.theme` **senza `Inherits=`**, e i dieci nomi che labwc chiede (`cursor.c:39-64`) |
| ⚠ **due leve, non una** | l'ambiente copre il compositore e i client non-GTK; i client **GTK3** usano il proprio tema, che su Wayland arriva da xfconf `xsettings /Gtk/CursorThemeName` via un **modulo GTK annunciato su D-Bus** (`org.gtk.Settings`), non più via XSETTINGS |
| ✅ **il punto d'inserimento c'è già** | XFCE spedisce `xfce4-session/labwc/labwc-environment:7` con `XCURSOR_THEME=Adwaita`, e `startxfce4.in:141-146` lo copia **solo se manca** |

### 10.2 ⛔ `xfce4-power-manager` spegne l'output, e va inibito

Parla Wayland nativo: `zwlr_output_power_v1_set_mode(OFF)` (`xfpm-dpms-wayland.c:233`), con default
`DPMS_ENABLED TRUE` e **10 minuti su rete elettrica** (`common/xfpm-config.h:50-60`). labwc espone il
protocollo (`server.c:683-688`) e su `MODE_OFF` **disabilita l'output** (`output.c:1063-1078`) ⇒
timer mai riarmato ⇒ **`failed` sulla cattura**.

| Via | Come |
|---|---|
| **D-Bus** | `org.freedesktop.PowerManagement.Inhibit` su `/org/freedesktop/PowerManagement/Inhibit`, firma `(ss)→u` (`xfpm-inhibit.c:349-353`). Copre DPMS + idle + screensaver in un colpo. ⚠ **Precondizione**: xfce4-power-manager **non ha attivazione D-Bus** [✗] — se non gira, la chiamata fallisce (è la forma del difetto di powerdevil su KDE, dove l'errore era `ServiceUnknown`) |
| **xfconf** | `dpms-enabled=false`, `inactivity-on-{ac,battery}=0`, `presentation-mode=true` |
| ⭐ **la cura di wayvnc** | `set_mode(MODE_ON)` **prima** di catturare, più ritento a 100 ms (`wayvnc/src/main.c:1022-1045`, `:1055-1063`) — cioè non fidarsi dell'inibizione, ma **riaccendere** |

✅ **`xfce4-screensaver` invece non è un rischio**: è X11 puro e esce con `EXIT_FAILURE` se il display
GDK non è X11. ⚠ Ma con `GDK_BACKEND=wayland,x11` potrebbe risorgere su Xwayland: **`wayland` secco**.

### 10.3 ⭐ Il blocco schermo si spegne con una chiave sola

Su KDE questa parte è stata KIOSK; qui la leva è più semplice e più forte: xfconf canale
`xfce4-session`, chiave **`/general/LockCommand`**. Se è impostata, `xfce_screensaver_lock()` la
esegue e **ritorna il suo esito senza provare nient'altro** — niente D-Bus, niente `xdg-screensaver`,
niente ripieghi (`libxfce4ui/xfce-screensaver.c:570-596`).

Impostandola a `/bin/false` si neutralizzano **in un colpo** `xflock4`, il metodo D-Bus
`org.xfce.Session.Manager.Lock` e ogni pulsante del pannello.

⚠ **La stringa vuota conta come «non impostata»** (`:299-305`): il default Debian `LockCommand=""` è
normalizzato a NULL, quindi oggi la catena D-Bus prosegue. Va scritto un valore **vero**.

⚠ E due dettagli che spiegano perché conviene: la catena D-Bus può **attivare** `xfce4-screensaver`
(che su Wayland esce subito), e i tre ripieghi sono `g_spawn_command_line_sync`, cioè **bloccano il
ciclo principale di `xfce4-session`**.

### 10.4 ⛔ In XFCE non esiste un KIOSK — e le voci vanno tolte, non bloccate

Confermato in modo definitivo: in tutto l'albero clonato, librerie comprese, `xfce_kiosk_query`
compare **solo** in `xfsm-shutdown.c:137-138`, con due sole capacità: **`Shutdown`** e
**`SaveSession`**. [✗] Nessun uso in pannello, scrivania, impostazioni, energia, salvaschermo,
libxfce4ui. **KIOSK non può togliere il blocco schermo né toccare il pannello.**

| | |
|---|---|
| **Il blocco xfconf** | impedisce di **cambiare** una voce, **non la rimuove** |
| **La leva vera** | plugin `actions` del pannello: `xfce4-panel /plugins/plugin-<N>/items`, **array di stringhe** con prefisso `+`/`-`; il `-` fa `continue`, cioè **la voce non viene creata** (`actions.c:1318`, `:1518`). Una voce `+` non permessa resta invece **visibile e grigia** |
| ⚠ **due insidie** | i nomi `logout`/`logout-dialog` sono **invertiti** rispetto agli enum; e il default di serie ha già `+lock-screen` e `+switch-user` |
| ⛔ **togliere `xflock4` non basta** | il plugin ripiega su `loginctl lock-session`, `dm-tool`, `gdmflexiserver`, `shutdown`, `systemctl` (`actions.c:1049-1085`) |
| **[✗] il dialogo di logout** | nessuna chiave toglie «Log Out/Restart/Shut Down»: restano solo polkit e logind |

⭐ **Il modo di preimpostare il pannello**: `xfce4/panel/default.xml` cercato lungo `XDG_CONFIG_DIRS`
(`migrate/main.c:36-37`, `:63-101`), applicato **in silenzio** se non è quello di serie. Per gli altri
canali i default di sistema stanno in `/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/<canale>.xml`.

### 10.6 xfconf: il lock, e la scrittura che riesce senza riuscire

| | |
|---|---|
| **Il lock è un attributo XML**, non un file a parte | `locked="utente"` (o `unlocked=`) su `<channel>` o `<property>` (`xfconf/docs/spec/perchannel-xml.txt:44-53`). Ammesso **solo nei file di sistema**: in un file d'utente è un **errore di parsing** |
| ⭐ **Col canale bloccato il file dell'utente non viene nemmeno letto** | (`xfconf-backend-perchannel-xml.c:1710`) — è la forma più forte, ed è quella che ci serve |
| ⛔ **Due trappole del lock** | **`locked="*"` non blocca nessuno** (nessun jolly: solo `strcmp`), e **`@gruppo` guarda solo `gr_mem[]`**, quindi **ignora il gruppo primario** — su Debian `@<nomeutente>` non funziona. Si scrive **il nome utente secco** |

⛔ **E il punto che cambia il modo di scrivere il provisioning**: **una scrittura su proprietà bloccata
non dà errore a chi scrive.** Il demone rifiuta con `XFCONF_ERROR_PERMISSION_DENIED`, ma
`xfconf_channel_set_property()` è **asincrona**: aggiorna la cache locale, emette `property-changed`,
**ritorna TRUE**; alla risposta il valore viene ripristinato e resta un `g_warning` su stderr. ⇒
**`xfconf-query` esce con `EXIT_SUCCESS`.**

⭐ **Da cui la regola, che è `LEZIONI.md` §1.9 applicata alla configurazione: dopo aver scritto un
valore, lo si rilegge.** Un banco che si accontenta dello stato d'uscita di `xfconf-query` è verde su
una configurazione che non è stata applicata.

⚠ E tre dettagli del demone: `xfconfd` **ha** attivazione D-Bus e i canali si caricano pigramente
(quindi scrivere i default *prima* che parta funziona); ma **[✗] non ha alcun `GFileMonitor`** — un
canale già caricato **non rilegge** un file cambiato sotto; e la scrittura su disco è **ritardata di
5 secondi**, con flush ordinato su `SIGTERM` e **perso** su `SIGKILL`.

⛔ **Correzione a quel che si poteva sperare**: i default di sistema evitano di *scrivere* nella casa
dell'utente, **non** che vi resti traccia. `xfconfd` **crea sempre**
`~/.config/xfce4/xfconf/xfce-perchannel-xml/` all'avvio — e **non parte** se non ci riesce — e alla
prima scrittura vi riversa **l'intero albero del canale**. **[?] L'unica via per non lasciare traccia
è un `XDG_CONFIG_HOME` effimero**, che è una decisione di progetto, non un dettaglio.

### 10.7 ✅ Il menu: garcon non ha la trappola di KDE

**[✗] garcon non costruisce alcun indice su disco** (grep su `g_file_set_contents|fopen|g_mkdir…` →
zero, con controllo positivo): la cache è **solo in memoria**. Cioè il difetto che su KDE ci ha
negato un permesso — *un indice costruito vuoto che resta vuoto* — **qui non può succedere sul
disco**.

⛔ **Ma la stessa forma esiste in memoria**: `garcon_menu_start_monitoring()` è chiamata **dopo** il
caricamento riuscito (`garcon-menu.c:817-819`). Se il primo caricamento fallisce, **non esiste alcun
monitor**, quindi `reload-required` non arriva mai e il menu resta vuoto **per la vita del
processo** — e il fallimento è **una finestra modale in faccia all'utente remoto**. Su XFCE non si
cancella un file: **si riavvia il processo**.

⚠ E `XDG_CURRENT_DESKTOP` va **`XFCE` secco, maiuscolo, senza suffissi**: per i sottomenu garcon
**non spezza sui `:`** (mentre per le voci sì), quindi con `XFCE:qualcosa` le directory
`OnlyShowIn=XFCE;` **spariscono**. Con la variabile *vuota* il filtro si spegne e si vede **di più**,
non di meno.

✅ Infine, letto nel menu spedito: **«Esci» è una voce del file**, mentre **«Blocca schermo» e «Cambia
utente» non sono voci di menu** [✗] — vivono solo nel pannello (§10.4).

### 10.5 I requisiti duri di XFCE sul compositore

| Protocollo | Chi lo pretende | Che cosa succede senza |
|---|---|---|
| `zwlr_layer_shell_v1` | xfdesktop, xfce4-panel | ⛔ **xfdesktop esce con `exit(1)`** (`xfdesktop-application.c:1017-1027`); il pannello degrada e non carica plugin esterni |
| `zxdg_output_manager_v1` | libxfce4windowing | la geometria **logica** viene solo da lì: senza, resta `{0,0,0,0}` e con essa il workarea |
| `wl_output` **v4** | libxfce4windowing | il `name` è l'identificatore |
| `ext_workspace_manager_v1` | il pager | ✅ labwc ce l'ha; **[✗]** sway e wayfire no |

✅ Tutti presenti in labwc 0.8.3. ⚠ E `xfsettingsd` su Wayland **non registra alcuna scorciatoia**
(sei moduli dietro `#ifdef ENABLE_X11`): il canale `xfce4-keyboard-shortcuts` è **inerte**, e nessuna
combinazione può lanciare `xflock4`. Effetto collaterale: XSettings non propagato, quindi temi e font
diversi da quelli attesi.

---

## 11. Chi lo fa già, e che cosa gli si ruba

*Dettaglio: `reference-xfce/rapporti/08-wayvnc.md`, `09-weston-rdp.md`, `10-portale-e-chi-lo-fa.md`.*

### 11.1 wayvnc — il riferimento pratico della famiglia

**Le cinque cose da copiare:**

1. ⭐ **la cadenza che sottrae la latenza del compositore** (§4.2): è la correzione strutturale al
   problema dei 18 fps;
2. ⭐ **il libro doppio del danno** (§4.3): obbligatorio, non un'ottimizzazione;
3. ⭐ **l'interfaccia astratta con due implementazioni di cattura** e le capacità in una maschera di
   bit, con **un solo punto** di diramazione;
4. **il MIME-marchio anti-eco** sulla clipboard (§8);
5. **`--show-performance`**: fotogrammi al secondo **e percentuale media di area danneggiata**, ogni
   secondo. Il secondo numero è quello che i nostri banchi non hanno mai avuto.

**Le tre da non copiare:** DMA-BUF **spento di default** (`--gpu`); nessuno scaler per client — chi
non sa ridimensionarsi **viene disconnesso**, e col nostro requisito 4K/60 non regge; e la creazione
dell'output **delegata a `swaymsg`**, che su labwc non esiste.

⚠ E due suoi difetti utili come avvertimento: il regolatore di banda **è volontario** (se il client
non annuncia `FENCE` il freno non si arma mai — il nostro deve restare obbligatorio), e il cursore
viene **solo** dal protocollo nuovo: con il solo `wlr-screencopy` wayvnc **non manda alcun cursore**.

### 11.2 Weston — il backend RDP più vecchio del mondo Wayland

**Il suo video è arretrato e non c'è niente da copiare lì**: [✗] niente MS-RDPEGFX, niente H.264,
niente GPU (anche col renderer GL il buffer viene riletto in RAM e compresso dalla CPU), il danno
diventa un bounding box, e **[✗] il regolatore di flusso non esiste** — annuncia
`SurfaceFrameMarkerEnabled=TRUE` e poi non ascolta gli ack. **La nostra formula è più avanzata del
progetto di riferimento.**

**Ma tre cose valgono, e sono tutte accessibili a noi:**

| | |
|---|---|
| ⭐ **la rotella RDP→Wayland** | riga per riga (§7.2) |
| ⭐ **il ponte thread → ciclo eventi** | `eventfd(EFD_SEMAPHORE)` + lista con mutex + `assert_compositor_thread()` in cima a ogni callback (`rdputil.c:79-226`). Serve subito: anche il nostro `cliprdr` gira su un thread di FreeRDP |
| ⭐ **il certificato per peer, mai condiviso** | il backend tiene solo i **percorsi**; ogni peer fa `freerdp_certificate_new_from_file()` e cede la proprietà a FreeRDP (`rdp.c:1755-1764`). **È l'antidoto diretto al difetto che su KDE uccideva il server alla seconda connessione** |

E due regali per la conversione dell'input: la catena
`GetVirtualKeyCodeFromVirtualScanCode → KBDEXT → GetKeycodeFromVirtualKeyCode(XKB) → scan_code - 8`
(nessuna tabella a mano: si delega a WinPR), e ⚠ **la trappola di FreeRDP 3**: `KBD_FLAGS_DOWN` non è
mai settato — **l'assenza di `KBD_FLAGS_RELEASE` *è* la pressione**.

⚠ **E una lezione §1.11 in forma pura**: i lucchetti di Weston **non funzionano**, e non lo dichiara
nessuno. `weston_keyboard_set_locks()` esce con `-1` alla prima riga se `!seat->led_update`, e il
seat RDP non lo imposta mai. L'idea è giusta, l'attuazione è morta: **va verificato il primo `return`
di ogni API che chiamiamo**.

Del ridimensionamento: **[✗] MS-RDPEDISP non c'è**, ma c'è una cosa da rubare — alla nuova misura
Weston **copia il vecchio contenuto nel nuovo buffer** (`PIXMAN_OP_SRC`) per non mostrare nero al
primo fotogramma.

### 11.3 Il ponte PipeWire: gratis sulle copie, caro su tutto il resto

`xdg-desktop-portal-wlr` alloca i buffer lui e **passa lo stesso `wl_buffer` a screencopy**: DMA-BUF =
**un blit GPU**, che è la copia intrinseca del protocollo e ci sarebbe identica parlando screencopy
da soli. **Sulle copie il ponte non costa niente.**

**Il prezzo è altrove, e sono quattro fatti strutturali:**

| | |
|---|---|
| ⛔ **non possiamo chiedere un fotogramma** | nessun `.process`, nessun `PW_STREAM_FLAG_DRIVER`, e **sempre `copy_with_damage`** — a schermo fermo `ready` non arriva |
| ⛔ **non possiamo negoziare la misura** | [✗] `SPA_POD_CHOICE_RANGE_Rectangle` non esiste: la misura è un `SPA_POD_Rectangle` fisso. Il ridimensionamento passa da un protocollo **separato** |
| ⛔ **niente cursore separato** | `METADATA` è rifiutato, `SPA_META_Cursor` mai citato. RDP vuole il *Pointer Update* a parte |
| ⚠ **quattro processi, ≥3 salti IPC** | su un budget di **16,6 ms** per fotogramma |

**Il conto opposto**: parlare screencopy direttamente costa **[R] ≈1 200 righe nuove** — ma il
DMA-BUF resta un `gbm_bo` allocato da noi, quindi **l'importazione e l'attesa della fence delle fasi
8 e 9 si riusano intere**: si perde solo lo strato `pw_stream`.

---

## 12. Le quattordici domande di `LEZIONI.md` §3, con la colonna wlroots riempita

*Tutte **[R]** salvo dove segnato: è una lettura di codice, non una misura, e §14 dice quali vanno
misurate per prime.*

| # | La domanda | wlroots 0.18.2 / labwc 0.8.3 |
|---|---|---|
| 1 | **Come si chiede la cattura senza portale?** | `zwlr_screencopy_manager_v1` **v3**, protocollo Wayland diretto |
| 2 | **Spinge o fa tirare?** | ⛔ **fa tirare**: `capture_output → frame → copy → ready`, uno per fotogramma |
| 3 | **È dietro un permesso?** | ✅ **no** [M]. Nessun filtro, nessun `.desktop`, nessun dialogo |
| 4 | **Senza monitor disegna sulla GPU?** | ✅ **sì** con headless + default (GLES2 + GBM). ⚠ ma il ripiego in pixman è **silenzioso**, e non c'è modo di chiedere al compositore che renderer usa [✗] |
| 5 | **Si può chiedere uno schermo virtuale della misura voluta?** | ⛔ **non all'avvio** (1280×720 cablati), ✅ **sì dopo**, con `set_custom_mode` |
| 6 | **Quanto consegna?** | **61** a 1080p e 1440p, **40,3** a 4K [M, 7 ago, sway, `wl_shm`] — a 4K il costo è la copia in memoria |
| 7 | **La cadenza dichiarata come si comporta?** | ⭐ **non esiste una cadenza da dichiarare**: il refresh dell'output headless *è* il periodo del timer, e il ritmo lo detta il nostro ciclo |
| 8 | **Interi o «diff»?** | ✅ **interi, sempre** — il danno non è mai consultato nella copia |
| 9 | **Il buffer arriva già disegnato?** | ⚠ **[?]**: GLES2 fa solo `glFlush()`, nessuna fence esplicita. **Da misurare** |
| 10 | **Che cosa costa la risoluzione?** | a 4K **sì** in memoria (61 → 40); **[?]** in DMA-BUF, da misurare |
| 11 | **Che cosa costa la profondità di colore?** | niente; nessun percorso a 24 bit impacchettati |
| 12 | **Si può cambiare misura a cattura viva?** | ✅ **sì** — ma **[?]** che cosa succede alla cattura in corso va misurato |
| **12-bis** | ⭐ **Il cursore è dentro l'immagine?** | ⛔ **sì, sempre**, su headless. E `overlay_cursor` non lo toglie |
| **13** | ⭐ **Uno schermo virtuale si ridimensiona a caldo?** | ✅ **sì, senza tetto** — la risposta migliore delle tre famiglie |
| **14** | ⭐ **La clipboard di chi è?** | **del compositore**, `zwlr_data_control_manager_v1` v2, nessun permesso — e **nessun gestore di appunti** in XFCE su Wayland |

⭐ **E la quindicesima, che questo desktop aggiunge alla lista per il prossimo**: **«chi possiede il
ciclo dei fotogrammi?»** Su Mutter e KWin lo possiede il compositore e noi consumiamo; qui lo
possediamo **noi**, e con esso il ritmo, il costo e la responsabilità di non far rendere il
compositore a vuoto. È la domanda 2 portata alle sue conseguenze, e va posta **prima** della 6:
perché su un compositore a tiro, *«quanto eroga»* non è una proprietà del compositore — **è una
proprietà del nostro ciclo**.

---

## 13. Le scelte da mettere davanti all'utente

| # | La scelta | I termini |
|---|---|---|
| **1** | **Screencopy diretto o ponte PipeWire?** | diretto: ~1 200 righe nuove, ma controllo del ritmo, del cursore e della misura, e riuso intero del consumatore DMA-BUF delle fasi 8-9. Ponte: meno righe, ma ⛔ nessuna delle tre cose sopra, e quattro processi sul budget di 16,6 ms |
| **2** | **Il ridimensionamento a caldo si accende subito?** | su KDE si era scelta la misura fissa **perché KWin non sapeva fare altro**. Qui **si può**, e il precedente (wayvnc) esiste. Resta da decidere se farlo nella fase 11 o dopo |
| **3** | **Il cursore: dentro l'immagine o sul canale RDP?** | oggi il tema trasparente è la cura pronta (§10.1). Il cursore *vero* — forma e hotspot sul canale puntatore di RDP — arriva **solo col protocollo nuovo**, che su Trixie non c'è: sarebbe lavoro che oggi non si può nemmeno provare |
| **4** | **Il bus di sessione: privato o d'utente?** | `dbus-run-session` è quel che XFCE fa di suo, ma **ci nasconde `StateChanged`**. Il bus d'utente di systemd è la strada raccomandata **[?]**, e va provata |
| **5** | **Le voci pericolose: quante ne togliamo?** | «Blocca schermo» ha una cura netta (§10.3). «Cambia utente» e lo spegnimento chiedono di riscrivere la disposizione del pannello — che è una modifica alla casa dell'utente, e il suo prezzo lo paga lui |

---

## 14. Il piano di misure che apre la fase

*Nell'ordine, e ogni misura ha un controllo positivo, perché «zero» e «proibito» hanno lo stesso
aspetto (`LEZIONI.md` §1.9).*

| # | La misura | Perché è lì |
|---|---|---|
| **M1** | i due global dell'input compaiono davvero da una **shell SSH**, e i device si creano | è la premessa di tutto il capitolo 7. Il permesso della cattura è già misurato, quello dell'input no |
| **M2** | ⛔ **`WaylandLogoutCommand` impedisce `loginctl terminate-session ''`** | è l'unica misura che, sbagliata, **ammazza la sessione di chi la esegue**. Sul banco, mai sull'utente |
| **M3** | screencopy su **DMA-BUF**: il buffer è intero? la fence è pronta o va aspettata? | sono le domande 8 e 9, e decidono se la copia zero nasce accesa come su KDE |
| **M4** | la **cadenza a 1080p e 4K** con la scena dichiarata, contando anche quanto disegna il client | R32 rifatta per questa famiglia — e qui il numero dipende **dal nostro ciclo**, non dal compositore |
| **M5** | GPU o pixman: **controllo positivo** con `WLR_RENDERER=pixman` e con la scheda sbagliata | §5.2. Il ripiego è silenzioso per costruzione |
| **M6** | `set_custom_mode` a cattura viva: la cattura sopravvive? il pannello si ridispone? | §6, e il verso di `xfsettingsd` che disabilita gli output nuovi |
| **M7** | la sessione XFCE completa parte headless, e in quanti secondi | §9.4: gli otto secondi per gruppo di priorità sono strutturali |
| **M8** | l'inibizione del DPMS regge dieci minuti | §10.2, e la precondizione che xfce4-power-manager sia vivo |
| **M9** | il tema del cursore trasparente **non fa ripiegare** wlroots sul tema visibile | §10.1, ed è la trappola già pagata su KDE |
| **M10** | `appunti_wlr.c` così com'è, contro labwc | §8, e le tre riserve |
| **M11** | ogni valore xfconf scritto dal provisioning **si rilegge** | §10.6: la scrittura riuscita non prova niente, ed è un verde che costa un pomeriggio |

---

## 15. Le lezioni che questo studio aggiunge, prima ancora di misurare

1. ⭐ **Su un compositore a tiro, «quanto eroga» non è una domanda sul compositore.** Le tabelle di
   R32 per Mutter e KWin misuravano *loro*; qui misureranno **il nostro ciclo**. Chi citerà il numero
   deve citare anche la cadenza che gli abbiamo chiesto e il modo in cui gliel'abbiamo chiesta.
2. ⭐ **La leva che sembra esserci e non fa niente si ripresenta, con un altro nome.** Su KWin era
   `KWIN_COMPOSE=O2`; qui è `overlay_cursor`, che *forza* i cursori software invece di togliere il
   cursore. **Per ogni interruttore che troviamo, va scritto che cosa mostrerebbe il caso opposto**
   (§1.11) — e questa volta lo sappiamo prima di misurare, non dopo.
3. ⭐ **Il precedente più utile può essere una rimozione.** wlroots ha *tolto* il proprio backend RDP
   in favore di un client esterno: è la conferma più forte che l'architettura di REMOTIX sia quella
   giusta, e non l'avremmo trovata leggendo il codice presente — solo cercando **chi lo fa, e chi ha
   smesso**.
4. ⚠ **Legarsi ai protocolli, non alla libreria.** XFCE sta scrivendo un compositore proprio in Rust
   su smithay, non su wlroots. Tutto ciò che scriviamo contro `zwlr_screencopy`,
   `zwlr_virtual_pointer` e `zwlr_data_control` sopravvive a quel cambio; tutto ciò che assume
   *wlroots* no.
5. ⭐ **Una scrittura che riesce non è una configurazione applicata.** `xfconf-query` esce con zero
   anche quando il demone ha rifiutato e ripristinato il valore, perché l'API è asincrona e la cache
   locale risponde prima. È `LEZIONI.md` §1.9 spostata dalla misura alla configurazione: **una
   scrittura che può essere rifiutata dev'essere riletta**, e vale per ogni valore che il
   provisioning imposta.
6. ⚠ **Le variabili d'ambiente pericolose non sono quelle che mancano, ma quelle che si ereditano.**
   Garcon ha un ripiego per `XDG_MENU_PREFIX` assente, e nessuno per una sbagliata; `XDG_CURRENT_DESKTOP`
   con un suffisso fa sparire i sottomenu; `DISPLAY` fa ripiegare GTK su X11 in silenzio. È la lezione
   §5 di `LEZIONI.md` — *chi avvia una sessione le regala tutto il proprio ambiente* — e su questo
   desktop morde in tre punti diversi.
