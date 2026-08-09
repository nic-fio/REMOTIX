# S4 — Quanto costa dipingere: dal fotogramma decodificato al pixel acceso

*Studio del 9 agosto 2026. Risponde alla domanda **S4** di `PIANO.md` §1.2. Fonti aggiornate al
2026, con le versioni.*

⛔ **Nessuna misura in questo documento.** Qui non c'è nemmeno una marca `[M]`: chi scrive non ha
un browser sotto mano e non ne ha lanciato uno. Tutto è `[S]` (letto in una specifica o in una
documentazione, con l'URL), `[R]` (letto nel codice di un progetto, con il file) o `[?]`
(ipotizzato). ⚠ **Le decisioni che poggiano su `[?]` vanno scritte provvisorie**
(`README.md`, le convenzioni).

⛔ **E una diffida che vale per tutto il documento**: i numeri di ritardo trovati negli articoli
quasi mai dichiarano la scena né dove comincia e dove finisce la misura. Ogni volta che ne cito
uno, scrivo **che cosa misurava**; e quando la fonte non lo dice, lo scrivo pure.

---

## 1. La risposta in cinque righe

1. ⭐ **Si dipinge con `drawImage(videoFrame)` su un canvas 2D creato `{desynchronized: true, alpha: false}`, dentro la callback `output` del decodificatore — non su `requestAnimationFrame`** — con tutto il percorso (WebTransport, `VideoDecoder`, `OffscreenCanvas`) dentro **un worker dedicato**.
2. Costo: **zero copie CPU** quando il fotogramma è NV12 a 8 bit su *shared image*, **una conversione YUV→RGB in GPU** per il canvas, e poi il compositore.
3. ⛔ **Il compositore è il pezzo caro e non è nostro**: a 60 Hz sono **due o tre passaggi di vsync fra il `drawImage` e il pixel**, cioè `[?]` **~16–40 ms** — da un terzo all'intero tetto dei 50 ms, prima ancora che il fotogramma esca dal decodificatore.
4. Sotto interruttore, e solo dove esistono: **WebGPU `importExternalTexture`** (l'unico zero-copy vero, ma solo Chrome/Safari e solo NV12 8 bit) e **`<video>` alimentato da `VideoTrackGenerator`** (l'unica strada che può finire su un piano overlay e saltare il compositore).
5. ⛔ **E i 10 bit qui prendono la seconda bastonata**: in Chromium la condizione di zero-copy di WebGPU è letteralmente `format == PIXEL_FORMAT_NV12` `[R]` — **P010 non passa**. Dopo l'indizio Android di `DECISIONI.md` §2.3-bis, questo è il secondo.

---

## 2. La tabella delle strade di disegno

Le colonne «copie» contano **dal fotogramma decodificato al buffer che il compositore legge**. «C»
= copia che passa dalla CPU (cara), «G» = copia GPU→GPU (molto meno cara), «0» = nessuna.

| # | Strada | Copie (8 bit NV12 hw) | Il fotogramma resta in GPU? | Latenza aggiunta `[?]` | Chrome | Firefox | Safari |
|---|---|---|---|---|---|---|---|
| **A** | canvas 2D `drawImage(frame)` | **1 G** (YUV→RGB in GPU) `[R]` | sì, se `HasSharedImage()` `[R]` | disegno quasi gratis; il costo è il compositore | ✅ | ✅ ⚠ lento | ✅ |
| **A′** | come A ma `{desynchronized: true}` | 1 G | sì | ⭐ salta la coda del compositore del renderer `[S]` | ✅ (⛔ rotto su macOS `[S]`) | ❌ `[S]` | ❌ `[S]` |
| **B** | `createImageBitmap(frame)` + `transferFromImageBitmap` | **1 G** + trasferimento a zero copie `[S]` | sì | ⚠ `createImageBitmap` è **asincrona**: un salto di task in più `[S]` | ✅ | ✅ ⭐ la cura per Firefox | ✅ |
| **C** | WebGL `texImage2D(frame)` | **1 G** — l'API di Chromium si chiama `Copy…ToGLTexture` `[R]` | sì | come A | ✅ | ✅ | ✅ |
| **D** | ⭐ WebGPU `importExternalTexture` | **0** `[R]` | sì | il minimo possibile lato disegno | ✅ | ⛔ **non implementato** `[S]` | ✅ (26+) `[S]` |
| **D′** | WebGPU `copyExternalImageToTexture` | 1 G `[S]` | sì | ripiego di D | ✅ | ✅ | ✅ |
| **E** | `<video>` + **MSE** | dipende dal decoder | sì | ⛔ **3 fotogrammi di cuscinetto** per difetto in Chromium `[S]`, 1 in «low delay» `[R]` — e non lo chiedi tu | ✅ | ✅ ⚠ | ✅ |
| **F** | ⭐ `<video>` + **`VideoTrackGenerator`** (WebCodecs → traccia) | 0 o 1 G `[?]` | sì | ⭐ **può diventare overlay e saltare il compositore** `[S]` | ✅ (nome vecchio `MediaStreamTrackGenerator`, solo main thread) `[S]` | ⏳ previsto 2026-06 `[S]` | ✅ (18 TP+) `[S]` |
| **G** | `frame.copyTo()` + `putImageData` | ⛔ **1 C + 1 C** | ⛔ **no** | ⛔ inaccettabile | — | — | — |

⛔ **La riga G non è un'opzione**: `copyTo()` su un fotogramma GPU fa un *readback* verso la CPU
(`ReadbackTextureBackedFrameToBuffer`, con ripiego sincrono `ReadbackTexturePlaneToMemorySync`)
`[R]`. Sta in tabella solo perché il **banco** di §4 ne ha bisogno, in dose omeopatica.

⚠ **I numeri di throughput che girano**, e cosa misurano davvero. `webcodecsfundamentals.org`
pubblica fotogrammi al secondo per ciascuna strada su *Big Buck Bunny* 1080p: `drawImage` Firefox
**70**, Chrome **960**, Safari **230**; `bitmaprenderer` porta Firefox a **230**; WebGPU
`importExternalTexture` Firefox **430**, Chrome **1230**, Safari **610** `[S]`. ⛔ **Non sono
latenze**: sono ritmi sostenuti su una scena video, e **la fonte non dichiara la macchina, la GPU,
né la versione dei browser**. Servono a una cosa sola, ed è già molta: **70 fps su Firefox
significa ~14 ms per fotogramma solo per il `drawImage`**, cioè oltre un quarto del tetto — e
questo sì che sarebbe un difetto da vedere subito nel banco.

---

## 3. Il dettaglio, domanda per domanda

### 3.1 Le strade, confrontate

**`VideoFrame` è una sorgente legittima per `drawImage`** `[S]`: il typedef `CanvasImageSource`
della spec HTML è
`(HTMLOrSVGImageElement or HTMLVideoElement or HTMLCanvasElement or ImageBitmap or OffscreenCanvas or VideoFrame)`
— <https://html.spec.whatwg.org/multipage/canvas.html#canvasimagesource>. Non serve nessun
passaggio intermedio.

**Che cosa fa Chromium dietro un `drawImage`.** `media/renderers/paint_canvas_video_renderer.cc`
biforca su `video_frame->HasSharedImage()`: se sì costruisce una `SkImage` dalla shared image e fa
`drawImageRect`; se no chiama `ConvertVideoFrameToRGBPixels(...)` **sulla CPU** `[R]`. Esiste anche
il ripiego dichiarato nel commento: *«If skia couldn't do the YUV conversion on GPU, we will on
CPU»*, via `GetSkImageViaReadback()` `[R]`. ⚠ **Quindi anche il ramo buono non è zero-copy**: è una
conversione YUV→RGB dentro una texture intermedia, cioè una copia GPU→GPU.
<https://chromium.googlesource.com/chromium/src/+/main/media/renderers/paint_canvas_video_renderer.cc>

**`desynchronized`.** La spec HTML dice che con l'attributo a `true` l'agente utente *«può
ottimizzare il rendering della canvas per ridurre la latenza desincronizzandolo dal ciclo di
eventi, scavalcando l'algoritmo di rendering ordinario, o entrambi»* `[S]`. La documentazione di
Chrome è più concreta: *«tells the underlying system to skip as much compositing as it is able and
in some cases, the canvas's underlying buffer is sent directly to the screen's display
controller»*, il che *«eliminates the latency that would be caused by using the renderer
compositor queue»* `[S]` — <https://developer.chrome.com/blog/desynchronized>.

⛔ **Ma leggere l'Intent to Ship cambia il quadro**: *«All platforms support the desynchronization
between input events and compositor frame, **CrOs supports also front-buffer rendering**»* `[S]` —
<https://groups.google.com/a/chromium.org/g/blink-dev/c/nxjWgMIeC1Q/m/GfwjbzeVAwAJ>. Cioè: **solo
su ChromeOS il buffer va davvero allo schermo**; altrove è «solo» la desincronizzazione dalla coda.
E su macOS la modalità è **rotta**: nel thread `graphics-dev` del 2025 si legge che la modalità
`SingleBuffer` di `CanvasResourceProvider` non funziona su Mac perché `IOSurfaceImageBacking` sotto
Metal *«doesn't support concurrent read/write»* `[S]` —
<https://groups.google.com/a/chromium.org/g/graphics-dev/c/20qDm3ZD2f8>.
Firefox e Safari **non lo implementano** `[S]`
(<https://bugzilla.mozilla.org/show_bug.cgi?id=1536809>,
<https://web-platform-dx.github.io/web-features-explorer/features/canvas-2d-desynchronized/>).

⚠ **E si rileva, non si assume**: `ctx.getContextAttributes().desynchronized` `[S]`.

**WebGL.** L'header `paint_canvas_video_renderer.h` documenta le sue funzioni come
`CopyVideoFrameYUVDataToGLTexture` — *«Copy the CPU-side YUV contents of |video_frame| to texture
|texture|»* — e `TexImage2D` `[R]`. ⚠ **Il vocabolario è *copy*, non *bind***: in WebGL non esiste
un oggetto che campioni i piani del decodificatore in loco. **Il caso opposto**: se WebGL fosse
zero-copy, in quell'header troveremmo un'API tipo «BindVideoFrameToTexture» con `EGLImage` o
`GL_TEXTURE_EXTERNAL_OES`. Non c'è.

**WebGPU.** Qui lo zero-copy è vero, e la condizione è scritta nel codice
(`third_party/blink/renderer/modules/webgpu/external_texture_helper.cc`) `[R]`:

```cpp
const bool zero_copy =
    (media_video_frame->HasSharedImage() &&
     (media_video_frame->format() == media::PIXEL_FORMAT_NV12) &&
     device_support_zero_copy &&
     media_video_frame->metadata().is_webgpu_compatible &&
     DstColorSpaceSupportedByZeroCopy(dst_predefined_color_space));
```

Il ripiego è commentato nel sorgente stesso: *«Using CopyVideoFrameToSharedImage() is an optional
one copy upload path. However, the formats this path supports are quite limited»* `[R]`. E c'è un
diagnostico ufficiale non standard: `GPUExternalTexture.isZeroCopy`, dietro
`chrome://flags/#enable-webgpu-developer-features`, che dice *«whether the video imported with
importExternalTexture() was directly accessed by the GPU without the need for an intermediate
copy»* `[S]` — <https://developer.chrome.com/docs/web-platform/webgpu/developer-features>.
⭐ **Quel flag è uno strumento di misura regalato**, e va usato nel banco.

⛔ **I limiti di `importExternalTexture` sono seri, e si progettano prima**: la texture *«is only
valid until you exit the current JavaScript task»*, quindi **va rifatto il bind group a ogni
fotogramma**; nello shader si usa `texture_external` e `textureSampleBaseClampToEdge`, non
`texture_2d<f32>` né `textureSample`; niente mipmap `[S]` —
<https://webgpufundamentals.org/webgpu/lessons/webgpu-textures-external-video.html>.
E ⛔ **Firefox non ce l'ha**: è ancora tracciato come mancante nel meta bug 1827116 `[S]`.

**La strada `<video>`.** Due varianti, e vanno tenute distinte.
- ⛔ **Con MSE** si paga un cuscinetto che **non si chiede**: l'explainer WICG `media-latency-hint`
  dice *«Chromium defaults to require 200 milliseconds of decoded audio and 3 decoded video
  frames»* `[S]` — e nel thread originale Chris Cunningham precisa che i 200 ms vengono dal buffer
  audio, mentre *«the video frame buffer is ~3 frames»* `[S]`
  (<https://github.com/WICG/media-latency-hint>). **Che cosa misura quel numero**: il riempimento
  del buffer di rendering prima che la riproduzione parta, mantenuto poi come cuscinetto — **non è
  un glass-to-glass**. Nel codice: `low_delay_ = stream->liveness() == StreamLiveness::kLive;` e
  allora `min_buffered_frames_ = 1` `[R]`
  (`media/renderers/video_renderer_impl.cc`); e fuori da low-delay, in underflow,
  `min_buffered_frames_++` — ⛔ **il cuscinetto cresce da solo e non torna indietro**. Peggio: la
  modalità low-delay **si attiva per euristica** (durata assente nei metadati), non con un'API
  `[S]`. L'explainer di WebCodecs lo dice senza giri: *«The way to trigger 'low-latency mode' is
  implicit, not standardized, and not supported by all major browsers»* `[S]` —
  <https://github.com/w3c/webcodecs/blob/main/explainer.md>.
- ⭐ **Con `VideoTrackGenerator`** invece i `VideoFrame` che escono da `VideoDecoder` si scrivono
  direttamente in una traccia, e la traccia si appende al `<video>` con `srcObject`. Si tiene
  WebCodecs (quindi `optimizeForLatency`, e la coda la governiamo noi) **e** si guadagna il
  percorso overlay. È worker-only nella spec `[S]`
  (<https://www.w3.org/TR/mediacapture-transform>); Chrome espone il nome vecchio
  `MediaStreamTrackGenerator` solo sul thread principale `[S]`; Firefox lo ha pianificato per
  2026-06 `[S]` (<https://bugzilla.mozilla.org/show_bug.cgi?id=1749532>).

⛔ **`ManagedMediaSource` non serve alla latenza.** La MSE v2 (W3C Working Draft del **7 agosto
2026**) lo introduce per *«power-efficient streaming and active buffered media cleanup by the user
agent»*, e **la parola *latency* non compare** `[S]` — <https://www.w3.org/TR/media-source-2/>.
WebKit lo presenta come *«a power-efficient, low-level toolkit»* `[S]`. ⚠ E per noi è un
**rischio**: l'agente utente può **espellere** dati dai buffer quando vuole, e decide lui quando
chiedere i dati.

### 3.2 Zero-copy: quando c'è, e che cosa lo rompe

**Il veicolo.** La documentazione Chromium VideoNG dice che i fotogrammi decodificati in hardware
vivono in buffer GPU opachi — **DXGI** su Windows, **IOSurface** su macOS, **AHardwareBuffer** su
Android, **DMA buffer** su Linux — e che *«high bandwidth video data never actually leaves the
GPU»* `[S]` — <https://developer.chrome.com/docs/chromium/videong>.

**La catena intatta**, oggi, è una sola: **WebGPU `importExternalTexture` su NV12 a 8 bit**, con
`is_webgpu_compatible`, la feature Dawn `DawnMultiPlanarFormats`, e lo spazio colore di
destinazione fra `srgb` e `display-p3` `[R]`.

**Che cosa la rompe** — la lista operativa:

| Azione | Effetto | Marca |
|---|---|---|
| `frame.copyTo()` su fotogramma GPU | ⛔ readback GPU→CPU | `[R]` `video_frame.cc` |
| `frame.copyTo()` con `format` RGB | ⛔ conversione + readback | `[R]` |
| `frame.allocationSize()` | **innocuo**: chiama solo `ParseCopyToOptions()` | `[R]` |
| `new VideoFrame(frame, {visibleRect, displayWidth})` | non copia (`WrapVideoFrame()`)… | `[R]` |
| …ma poi `importExternalTexture` su quel fotogramma | ⛔ **cade a one-copy** se `visible_rect.size() != natural_size` | `[R]` |
| `createImageBitmap(frame)` | riusa `sk_image()` se c'è, altrimenti `CreateImageFromVideoFrame()` | `[R]` |
| `getImageData()` / `toDataURL()` / `readPixels()` | ⛔ readback sincrono | `[S]` |
| canvas 2D con `willReadFrequently: true` | ⛔ **disattiva l'accelerazione**: il fotogramma *deve* scendere in CPU | `[S]` |
| formato ≠ NV12 — **P010 compreso** | ⛔ one-copy | `[R]` |
| BT.2020 / PQ / HLG | ⛔ one-copy | `[R]` |

⭐ **Il ridimensionamento è nella lista**, ed è il dettaglio che il progetto rischiava di scoprire
tardi: se costruisci un `VideoFrame` ritagliato o riscalato, `importExternalTexture` **abbandona lo
zero-copy** `[R]`. La riscalatura si fa **dopo**, nello shader o nel `drawImage` — mai
riconfezionando il fotogramma.

**⛔ I 10 bit — la risposta secca.** No: **le strade zero-copy documentate per l'8 bit non valgono
per il 10.**

1. Il cancello di WebGPU è `format == media::PIXEL_FORMAT_NV12` `[R]`. **P010 non passa.** *Caso
   opposto*: se passasse, quella condizione conterrebbe un `|| PIXEL_FORMAT_P010LE` e Dawn
   esporrebbe un formato multipiano a 10 bit. Non c'è.
2. Lato decodifica su Linux/VA-API la storia è in movimento ma non arriva fin qui: il commit
   `f346a2f` (luglio 2024) abilita HEVC Main 10 e VP9 Profile 2 introducendo un **VPP** di
   conversione **P010→NV12 (Vulkan)** e **P010→AR24 (OpenGL)**, con la nota *«should be optimized
   for zero-copy in the future»* `[R]`; il commit `882f184` (settembre 2024) toglie la conversione
   ma **solo sul percorso Vulkan** `[R]`. ⚠ Su OpenGL il 10 bit finisce in **AR24, cioè 8 bit**.
3. Quando un fotogramma a 10 bit arriva sul canvas 2D, Chromium ha i casi
   `PIXEL_FORMAT_YUV420P10` (`libyuv::I010ToARGBMatrixFilter`) e `PIXEL_FORMAT_P010LE`, e un helper
   che si chiama `DownShiftHighbitVideoFrame` `[R]`. ⛔ **Il nome dice tutto: si scende a 8 bit.**
4. Lato JavaScript il 10 bit è quasi invisibile: l'enum `VideoPixelFormat` **non contiene P010**
   `[S]`. Nella discussione w3c/webcodecs #631 Dale Curtis (Chrome) dice che i casi
   **hardware-decoded richiederanno più tempo perché mancano i percorsi di readback ad alta
   profondità** `[S]` — <https://github.com/w3c/webcodecs/discussions/631>.

⛔ **Questo è il secondo indizio contro i 10 bit**, dopo quello Android di `DECISIONI.md` §2.3-bis,
e arriva da una direzione diversa: non «il telefono riporta a 8 bit», ma «**il browser perde lo
zero-copy**». `DECISIONI.md` §2.2 va riletta con questo in mano.

**Lo spazio colore.** `GPUExternalTextureDescriptor.colorSpace` ammette **solo** `"srgb"` e
`"display-p3"` `[S]`; e in Chromium `DstColorSpaceSupportedByZeroCopy` ritorna vero solo per quei
due, con il TODO esplicito *«Support HDR color space and color range in generated wgsl shader to
enable all color space for zero-copy path»* `[R]`. In gpuweb #4384 si legge che con HDR10 (BT.2020
+ PQ) il percorso a una copia **converte 10→8 bit** e vira verso BT.709, con risultato slavato
`[S]`. ⭐ **Conclusione per il prodotto: si codifica in BT.709 full/limited a 8 bit, e HDR non si
promette.**

**Firefox e Safari.** Firefox: WebCodecs desktop dalla 130 `[S]`; ma `[?]` **non ho trovato un bug
che dimostri un percorso zero-copy `VideoFrame`→WebGL** — *il caso opposto* sarebbe un bug RESOLVED
FIXED che collega `WebCodecsVideoFrame` a DMABUF/`SurfaceTexture` dentro `texImage2D`. Safari: il
veicolo è `CVPixelBuffer` su **IOSurface**, e il disegno passa da `VideoFrame::paintInContext`
`[R]`; `[?]` zero-copy *dentro* la famiglia IOSurface, ma non un binding diretto a texture WebGL
garantito.

**Android.** Gli `AHardwareBuffer` sono zero-copy per costruzione `[S]`, e Chromium decodifica con
`AImageReader` su `MediaCodec` `[R]`. ⚠ Ma `[?]` **non ho trovato la prova che quei fotogrammi
portino `is_webgpu_compatible = true`**: *il caso opposto* sarebbe un commit che imposta quel
metadato nel percorso Android, come è stato fatto per la fotocamera. **Da verificare sul
dispositivo vero** (`DECISIONI.md` §5-bis.0-ter: mai su un browser di comodo).

### 3.3 La cadenza di presentazione

⛔ **`requestVideoFrameCallback` non è disponibile per noi.** È definito **solo su
`HTMLVideoElement`** `[S]` — <https://wicg.github.io/video-rvfc/>. Su un canvas alimentato da
WebCodecs **non esiste**. Questo taglia fuori l'unica API che porti con sé un tempo di
presentazione, e ha una conseguenza pesante sul banco (§4).

Restano due candidati:

| | `requestAnimationFrame` | ⭐ dipingere subito nella callback `output` |
|---|---|---|
| quando gira | a una *rendering opportunity*, cioè al vsync `[S]` | appena il decodificatore consegna |
| il fotogramma arrivato **subito dopo** il rAF | ⛔ aspetta **un intervallo intero** prima di essere anche solo disegnato | è disegnato subito, pronto per la prossima opportunità |
| attesa media prima del disegno | ⛔ ~T/2, e il disegno è *dentro* il cammino critico | ~0 |
| tearing | no | possibile con `desynchronized` |

`[?]` **A 60 Hz T = 16,7 ms**: aspettare il rAF per *poi* disegnare regala in media 8 ms e nel caso
peggiore 16,7 — cioè **fino a un terzo del tetto**, buttati per niente. La logica è la stessa che
il progetto applica alle memorie intermedie: compra fluidità, vende risposta.

⭐ **E chi lo fa davvero è d'accordo.** In `moonlight-web-stream` c'è un interruttore con questo
commento verbatim: *«When true: enable desynchronized in the context creation options (lower
latency), draw in submitFrame (low latency). When false: draw only on rAF (VSync-like, may reduce
tearing)»* `[R]` —
<https://raw.githubusercontent.com/MrCreativ3001/moonlight-web-stream/master/web/stream/video/pipeline.ts>.
Il commento dice **esattamente lo scambio**, e da che parte sta chi punta alla latenza.

⚠ **Non aspettare il vsync non significa non pagarlo.** Il pannello si accende quando si accende:
`desynchronized` toglie la **coda**, non lo **scanout**. `[?]` Il guadagno è al più un intervallo,
non tutto il ritardo di visualizzazione.

**`optimizeForLatency`.** Va acceso: è *«a hint that the selected decoder should be optimized to
minimize the number of `EncodedVideoChunk` objects that have to be decoded before a `VideoFrame` is
output»* `[S]`. ⭐ **È l'unico posto dove la profondità della coda del decodificatore è scritta
nella nostra API invece che in un'euristica del browser** — la ragione principale per cui
WebCodecs batte MSE per questo prodotto. E lo accendono tutti: Xpra `[R]`, noVNC `[R]`, Selkies
`[R]`.

### 3.4 Il compositore del browser

**Le fasi.** Il documento `life_of_a_frame.md` di Chromium elenca il cammino: BeginFrame →
BeginMainFrame → Commit → Activate → **SubmitCompositorFrame** → AggregateSurfaces (nel processo
**Viz**, che è un altro processo) → Draw → RequestSwap → GPU Draw & Swap → **Presentation** `[S]` —
<https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/life_of_a_frame.md>.
La documentazione RenderingNG conferma i tre processi e il fatto che il *display compositor* di Viz
aggrega le superfici di più processi in **un solo compositor frame** `[S]` —
<https://developer.chrome.com/docs/chromium/renderingng-architecture>.

⚠ **Quanti quadri, in numero.** ⛔ **Nessuna delle due pagine dà una cifra.** Dicono che il pipeline
tiene più fotogrammi in volo e che esiste una *high latency mode* quando il thread principale non
risponde in tempo `[S]`. `[?]` **La mia stima, dichiarata come tale**: fra il `drawImage` e il
pixel ci sono **una attesa della prossima rendering opportunity (0…T)**, **almeno un intervallo di
compositore (T)** e **lo scanout (fino a T)** — cioè `[?]` **1,5–2,5 T**, che a 60 Hz fa **25–42
ms** e a 120 Hz **12–21 ms**. *Il caso opposto*, cioè la prova che mi sbaglio, sarebbe un
`PresentationFeedback` che risulta costantemente a meno di un intervallo dal `drawImage`: è
osservabile in `chrome://tracing`/Perfetto, **non dalla pagina**.

⭐ **Il percorso overlay esiste, e per il `<video>` è documentato.** VideoNG: *«Platform level
decoders often only provide opaque buffers that Chromium passes through to the platform level
compositing system in the form of overlays»*, e dal punto di vista del compositore principale *«video
is just a fixed-size hole with opacity»* `[S]`. Le primitive: **Direct Composition** (Windows),
**CoreAnimation Layers** (macOS), **SurfaceView** (Android), **VASurfaces/VA-API** (Linux) `[S]`.
Il riassunto Khronos del livello di presentazione dice che quel percorso *«bypasses the GPU
compositor entirely»* `[S]` —
<https://www.khronos.org/vulkan/chrome-video/chromium_presentation_layer.html>.

⛔ **Ma attenzione a come è giustificato**: la documentazione ufficiale motiva gli overlay con **il
consumo**, non con la latenza — *«when Chromium enabled overlays on macOS, power consumption during
fullscreen video playback was halved»* `[S]`. `[?]` Il guadagno di latenza plausibile è **al più un
quadro di compositore**, e **non ho trovato una fonte Chromium che lo quantifichi**.

**Le condizioni di promozione**, lette nel codice
(`components/viz/service/display/overlay_processor_win.cc`) `[R]`: fallisce con
`kCompositedCopyRequest` se c'è una copy request o una cattura schermo in corso;
`kCompositedTooManyQuads` sopra 2048 quad; l'ottimizzazione a schermo intero salta se il candidato
ha **rotazione o flip**; e il piano primario si può togliere solo se il video **occlude
completamente** — *«If the video is underneath e.g. controls or captions, we cannot remove the
primary plane»* `[R]`. ⛔ **Tradotto per noi: qualunque decorazione sopra il video — una barra, un
cursore disegnato in DOM, un indicatore di stato — può far cadere l'overlay.**

⚠ **E il canvas non è del tutto tagliato fuori**: `desynchronized` è la sua contromossa, e su
ChromeOS arriva al front buffer `[S]`. `[?]` **La differenza vera fra `<video>` promosso a overlay
e canvas desincronizzato è uno o zero quadri: va misurata, non dedotta.**

### 3.5 `OffscreenCanvas` in un worker

⭐ **Aiuta, e la ragione è scritta nell'explainer**: segnalare al worker dal thread principale
*«potrebbe aggiungere latenza indebita, specialmente quando l'event loop del contesto di
navigazione è occupato, il che distrugge completamente uno dei vantaggi chiave dell'uso di
OffscreenCanvas in un worker»* — perciò il worker ha il **suo** `requestAnimationFrame`,
sincronizzato con lo stesso dispositivo di visualizzazione `[S]` —
<https://github.com/junov/OffscreenCanvasAnimation/blob/master/OffscreenCanvasAnimation.md>.

⚠ **`commit()` è morto**: MDN lo dà **deprecato**, e *«calling commit() inside a
requestAnimationFrame() is unsupported and unnecessary»* `[S]`. Non lo si usa.

**Dove mettere la decodifica: nel worker, insieme a tutto il resto.** Il motivo è che **WebTransport
è disponibile nei worker** `[S]` (<https://developer.mozilla.org/en-US/docs/Web/API/WebTransport>),
quindi si può tenere l'intera catena — filo → `VideoDecoder` → `drawImage` su `OffscreenCanvas` —
**dentro un solo thread, senza un solo `postMessage` sul cammino del fotogramma**. Il thread
principale resta con l'input e l'interfaccia, e manda al worker solo eventi piccoli.

⚠ Il canvas visibile si consegna con `transferControlToOffscreen()`. ⛔ **Da verificare**: `[?]`
che `{desynchronized: true}` sia onorato su un `OffscreenCanvas` trasferito — il thread
`graphics-dev` dice che la modalità funziona *«on main threads and dedicated workers»* `[S]`, ma
sulle piattaforme che contano per noi non l'ho visto confermato.

⭐ **E chi lo fa già lo fa così**: Xpra decodifica in un worker (`OffscreenDecodeWorker.js`, con
`new OffscreenCanvas(...)`) e trasferisce il canvas visibile con `transferControlToOffscreen()`
`[R]`; Selkies ha un percorso «OffscreenCanvas worker» come ripiego universale `[R]`.

### 3.6 La riscalatura

⛔ **Non si riscala mai riconfezionando il `VideoFrame`.** Un `new VideoFrame(frame, {visibleRect,
displayWidth})` non copia `[R]`, ma fa **cadere lo zero-copy** al passaggio successivo `[R]`
(§3.2).

⭐ **La riscalatura si fa nel disegno, ed è essenzialmente gratis**: `drawImage(frame, 0, 0, w, h)`
scala in GPU dentro la stessa operazione che stava già facendo; in WebGPU la fa il campionamento
dello shader.

**Dimensionare il canvas o usare il CSS?** ⭐ **Tutt'e due, con ruoli diversi.**
- Il **buffer** del canvas (`canvas.width/height`) si mette alla **misura codificata** e si tocca
  **solo quando il server cambia risoluzione** — cambiarlo riallochia il buffer e partecipa al
  layout `[S]`.
- La **misura a schermo** si dà in CSS. Le trasformazioni non partecipano al layout e la scalatura
  la fa la GPU `[S]` — <https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Optimizing_canvas>.

`[?]` **Questo si sposa esattamente col disegno del prodotto**: il server codifica alla misura della
tela e non la cambia, quindi durante il trascinamento della finestra il CSS copre il transitorio
gratis, e la riconfigurazione del flusso (con la riallocazione del buffer) avviene **una volta
sola**, quando il ridimensionamento si ferma. ⚠ **Ma va scritto un debounce**, altrimenti si
riallochia a ogni pixel di trascinamento.

⛔ **Una cautela sul CSS**: `[?]` una trasformazione o un `border-radius` sul canvas potrebbero far
cadere il percorso desincronizzato/overlay — su Windows il codice degli overlay rifiuta i candidati
con rotazione o flip `[R]`. **Si usa larghezza/altezza in CSS, non `transform`, e niente angoli
arrotondati sulla tela.**

### 3.7 Come si misura dentro una pagina

**`performance.now()` è più grezzo di quanto si creda**, e per motivi di sicurezza:

| Motore | Granularità normale | Con `crossOriginIsolated` | Fonte |
|---|---|---|---|
| spec `hr-time` | **100 µs** | **5 µs** | `[S]` <https://w3c.github.io/hr-time/> |
| Chrome (da M91) | 100 µs | 5 µs | `[S]` <https://developer.chrome.com/blog/cross-origin-isolated-hr-timers> |
| Firefox | ⛔ **1 ms** (`reduceTimerPrecision.microseconds` = 1000) | **20 µs** (`RFP_TIMER_UNCONDITIONAL_VALUE`) | `[R]` `nsRFPService.cpp` |
| Safari/WebKit | ⛔ **1 ms** (`static Seconds timePrecision { 1_ms }`) | alta precisione via COOP+COEP | `[R]` `Source/WebCore/page/Performance.cpp` |

⭐ **Decisione che discende da qui: la pagina si serve *cross-origin isolated* (COOP `same-origin` +
COEP `require-corp`).** Senza, su Firefox e Safari misuriamo con una grana di **1 ms** su un tetto
di **50 ms**. E la spec **permette il jitter** oltre all'arrotondamento `[S]`: ⛔ **una misura
singola non vale nulla, si lavora a distribuzioni.**

**Che cosa portano i `VideoFrame`.** ⛔ **Niente di utile per il ritardo.** `VideoFrame.timestamp` è
un intero in **microsecondi** che viene dall'`EncodedVideoChunk` `[S]`: è un tempo **di media**, non
d'orologio. ⛔ **Non si confronta con `performance.now()`** — ed è esattamente la stessa trappola
che `RCP.md` §6.2 già dichiara per il campo `istante`. L'unico tempo d'orologio disponibile è
**quello che leggiamo noi all'ingresso della callback `output`**.

**`requestVideoFrameCallback`**, se e solo se si prova il percorso `<video>`: `presentationTime` è
*«The time at which the user agent submitted the frame for composition»* — cioè **la consegna al
compositore, non il pixel** — ed `expectedDisplayTime` è *«The time at which the user agent
**expects** the frame to be visible»* `[S]`. ⛔ **È una previsione**, e la spec avverte che *«there
are no strict timing guarantees»* e che una callback può arrivare **un vsync in ritardo** `[S]`.
⚠ E anche questi campi sono arrotondati per motivi di sicurezza: la spec propone **100 µs** per
`processingDuration` `[S]`.

**Il resto, e perché non basta:**

| API | Che cosa dà | Perché non chiude S4 |
|---|---|---|
| `PerformanceEventTiming` | `duration` include i passi di rendering | ⛔ **arrotondata a 8 ms** `[S]`, e si ferma alla fine dei passi, non alla presentazione |
| Element Timing / LCP | in Chromium riporta il **presentation timestamp** `[S]` | ⛔ **una volta sola per elemento**, non per fotogramma |
| `PerformanceFrameTiming` | — | ⛔ **mai spedita** `[S]` |
| Long Animation Frames | `duration` | ⛔ dichiarata *«not including presentation time»* `[S]` |
| `requestPostAnimationFrame` | — | ⛔ non spedita; e comunque gira **prima** della presentazione `[S]` |
| `getVideoPlaybackQuality()` | `droppedVideoFrames`, `totalVideoFrames` | contatori, **non tempi** `[S]` |
| WebRTC `getStats()` | `jitterBufferDelay`, `totalDecodeTime`, `totalProcessingDelay` | ⛔ si fermano **alla decodifica** `[S]`; e comunque non siamo su WebRTC |

⛔ **E la risposta secca alla domanda vera: non esiste in JavaScript alcun modo di sapere quando il
pixel si è acceso.** `[?]` Il confronto più istruttivo è **WebXR**, che è la piattaforma web più
vicina all'hardware di visualizzazione: anche lì `XRFrame.predictedDisplayTime` è *«the
DOMHighResTimeStamp corresponding to the **average point in time** the XRFrame is **expected** to
be displayed»*, e la spec avverte che *«is not intended to be used to infer how much time the
application has for rendering, as the XR Compositor typically has to do extra processing after the
frame is submitted»* `[S]` — <https://www.w3.org/TR/webxr/>. **Previsione, mai conferma.**

### 3.8 Il banco ad anello chiuso

→ **§4**, che è la parte lunga: come si costruisce dentro la pagina, i sette controlli, e il pezzo
cieco che nessuna misura in JavaScript può vedere.

### 3.9 La prassi di chi già lo fa

| Progetto | Che strada di disegno | Numeri dichiarati |
|---|---|---|
| ⭐ **Selkies** | ordine di preferenza scritto nei commenti: *«worker-side VideoTrackGenerator (standard) > main-thread MediaStreamTrackGenerator (Chromium) > OffscreenCanvas worker»*, perché i track generator *«present decoded VideoFrames to a `<video>` element (GPU-composited, no per-frame 2D-canvas draw)»* `[R]` | il percorso WebRTC stima `rtt + jitterBufferDelay/emittedCount` `[R]` — ⛔ **solo rete + jitter buffer**, non cattura, non encoder, non presentazione |
| ⭐ **moonlight-web-stream** | stessa gerarchia: WebCodecs + `MediaStreamTrackGenerator` → `<video>`; poi canvas; poi canvas in worker; poi WASM; **MSE per ultimo** `[R]` | nessuno; il README dice solo che senza `VideoDecoder` si cade su un'API più vecchia *«which may introduce noticeable latency»* `[S]` |
| **Xpra html5** | ⛔ **canvas 2D e basta**: `putImageData` sul backbuffer + `drawImage(this.draw_canvas, 0, 0)`; `VideoDecoder` con `optimizeForLatency: true` `[R]` | **nessuno trovato** |
| **noVNC** | canvas 2D con damage tracking: `putImageData` sul backbuffer, `drawImage` sul visibile; anche il decoder H.264 WebCodecs finisce in `drawImage` `[R]` | — |
| **Parsec (browser)** | `<video>` + MSE sfruttando la modalità *low delay* di Chrome — *«a push model for video frames rather than the traditional buffered pull model»* `[?]` (blog del progetto); **solo Chrome** | nessun numero |
| **Xbox Cloud Gaming** | WebRTC | Direct Capture *«reduces input latency by 16-72ms depending on the game»* `[S]` — ⛔ è un **risparmio lato server**, non un end-to-end |
| **Stadia** | WebRTC; il percorso di disegno non è documentato | «100–200 ms»: ⛔ fonte terza, **non dice da dove a dove** |
| **GeForce NOW** | — | ⛔ il «30 ms click-to-photon» che circola **non l'ho verificato in una fonte primaria**: non si cita |
| ⭐ **Hopp** (LiveKit) | `<video>` | **98 ms a 1080p**, 126 a 1440p, 159 in rete degradata `[S]` — ⭐ **e dichiara il metodo**: watermark nel canale Y, andata e ritorno completo input→encode→SFU→decode→rilevamento. È l'unico numero ben definito che ho trovato, ed è **lo stesso schema del nostro banco** |

⭐ **La lezione che esce dalla colonna di sinistra**: **i due progetti che hanno ragionato di più
sulla latenza non dipingono su canvas** — mandano i `VideoFrame` a un `<video>` per prendere
l'overlay. Xpra e noVNC restano sul canvas, e **nessuno dei due dichiara un numero di ritardo**.

---

## 4. ⛔ Il banco: come si misura S4

### 4.1 L'anello chiuso, dentro la pagina

Riprende `DECISIONI.md` §2.6 e lo rende eseguibile. Tutto dentro il worker, dove vive la sessione.

1. **La marca.** Il server disegna un rettangolo di **16×16** in un angolo fisso (angolo in alto a
   sinistra, coordinate note al client), e ne cambia il colore fra due valori molto distanti
   (p.es. nero pieno e bianco pieno), **su comando**. ⚠ In due valori, non uno: così il banco può
   ripetere l'andata e il ritorno senza rimettere a posto niente.
2. **`t0`** = `performance.now()` letto **subito prima** della `write()` sul filo dell'evento di
   input che ordina il cambio.
3. Il server inietta, il compositore ridisegna, la cattura prende, il codificatore codifica, il
   filo porta.
4. **`t1`** = `performance.now()` letto **come primissima riga della callback `output`** del
   `VideoDecoder`, **prima di qualunque altra cosa**.
5. **Poi**, e solo poi: si disegna; e **dopo il disegno** si legge la marca con
   `frame.copyTo(buf, {rect: {x:0, y:0, width:16, height:16}, format:'RGBX'})` `[S]`.
6. Se la marca ha il colore nuovo, il campione è **`t1 − t0`**. Altrimenti si aspetta il fotogramma
   dopo.

⭐ **Perché l'ordine dei passi 4-5-6 è vincolante.** `copyTo()` su un fotogramma GPU è un
**readback** `[R]`: è la cosa più perturbante che possiamo fare al percorso che stiamo misurando.
Mettendolo **dopo** la lettura di `t1` e **dopo** il disegno, il readback non può gonfiare il
campione: può solo disturbare i fotogrammi successivi. ⚠ E si legge un rettangolo di 16×16, non
l'immagine: `[?]` il costo di un readback è dominato dalla sincronizzazione, non dai byte, quindi
piccolo non vuol dire gratis — **e va misurato il disturbo**, accendendo e spegnendo il rilevatore
su una serie lunga.

⛔ **Non si usa `getImageData()` sul canvas per leggere la marca**, e nemmeno
`willReadFrequently: true`: il secondo **disattiva l'accelerazione del canvas** `[S]`, cioè
trasforma il banco in una misura di una strada che non è quella del prodotto. È la forma d'errore
di v1: *misurare una cosa e credere di misurarne un'altra*.

### 4.2 I controlli — senza questi il banco non vale

| # | Controllo | Che cosa dimostra | Come si vede se fallisce |
|---|---|---|---|
| **P1** | ⭐ **Il ritardo iniettato.** Il server aspetta **N ms noti** (0, 20, 50, 100) fra l'input e il cambio di colore | che il banco **misura quello che crediamo**: la mediana deve salire di **esattamente N** | se la mediana non si muove, il banco sta misurando altro (p.es. il periodo dei fotogrammi) |
| **P2** | **Il rilevatore trova il colore che c'è.** Si dà al rilevatore un fotogramma in cui la marca è **certamente** già nuova | che sa dire «sì» | — |
| **P3** | ⛔ **Il rilevatore NON trova il colore che non c'è.** Si campiona nei fotogrammi **prima** dell'input | che sa dire «no» | se dice sempre sì, si sta misurando zero e si è felici a torto |
| **P4** | **L'anello locale.** La pagina codifica e decodifica da sé, senza rete e senza server | isola **la metà cliente** del ritardo | — |
| **P5** | ⚠ **Il fuori ordine.** Con `numero` dei fotogrammi fuori sequenza (`RCP.md` §6.2) | che un fotogramma vecchio non venga scambiato per la risposta | un campione **negativo** o assurdamente breve |
| **P6** | **La grana dell'orologio.** Si stampa la distribuzione dei `t1 − t0`: se i valori sono multipli di 1 ms, la pagina **non è cross-origin isolated** | che i timer siano quelli buoni `[S]` | ⛔ tutti i campioni cadono su una griglia |
| **P7** | ⭐ **Il ritmo, come controllo del percorso.** Si conta anche `output` al secondo e occupazione CPU | che il decodificatore sia hardware davvero (`PIANO.md` §1.2) | il ritmo crolla e la CPU sale: software |

⚠ **E si dichiara la scena**, sempre: risoluzione, ritmo, codec, profilo, se il decodificatore è
hardware, il browser con la versione, la macchina, la frequenza del pannello. Un numero di ritardo
senza questa riga è un numero che non si può difendere.

### 4.3 ⛔ Il pezzo cieco — quello che questa misura NON vede

⛔ **La misura finisce alla callback `output`. Il pixel si accende dopo.** Fra `t1` e la luce c'è un
tratto che **nessun JavaScript può leggere** (§3.7), e questo banco lo **salta per intero**.

Il tratto cieco, in ordine:

| Pezzo | Chi lo fa | `[?]` Quanto vale a 60 Hz | Si vede da JS? |
|---|---|---|---|
| `drawImage` / caricamento GPU | il motore | frazioni di ms su Chrome; ⚠ **fino a ~14 ms su Firefox** se vale il rapporto 70 fps `[S]` | no |
| attesa della prossima *rendering opportunity* | il motore | 0…16,7 ms (media ~8) | no |
| compositore del renderer + Viz + swap | il browser | ≥ 1 intervallo | no |
| scanout del pannello | il monitor | fino a 16,7 ms | ⛔ mai |
| elaborazione interna e risposta del pannello | il monitor | dipende dal pannello | ⛔ mai |
| **totale** | | `[?]` **~16–40 ms** | ⛔ **invisibile** |

⛔ **Cioè il pezzo cieco può valere quanto tutto il resto del tetto.** Il tetto dei 50 ms
«per il pezzo che è nostro» resta legittimo, ma ⚠ **l'utente sente la somma**, e la somma a 60 Hz
può stare fra 55 e 90 ms anche con il nostro pezzo perfetto.

**E c'è un secondo cieco, dal lato opposto**: `t0` è preso **dentro JavaScript**. Un utente vero
prima muove un dito. Restano fuori: il polling del dispositivo (`[?]` 1–8 ms a 125–1000 Hz), la
consegna dell'evento dal sistema operativo, l'accodamento nel browser. `[?]` **Il banco misura da
JS a JS: non è un click-to-photon, ed è più corto su tutt'e due i capi.**

**Come si stima il pezzo cieco, senza telecamere** — tre strade, tutte parziali, e vanno dichiarate
tali:

1. ⭐ **Il periodo del pannello, dalla pagina.** Si misurano le differenze fra timestamp
   consecutivi di `requestAnimationFrame` e se ne prende la mediana: dà **T**, cioè l'unità in cui
   il pezzo cieco si conta. `[?]` Poi il pezzo cieco si dichiara come **1,5–2,5 T**, con la stima
   scritta come stima.
2. ⭐ **Il controllo positivo del cieco: lo stesso anello su un `<video>`.** Si costruisce una
   seconda variante del banco che manda i `VideoFrame` a un `<video>` con `VideoTrackGenerator`, e
   lì `requestVideoFrameCallback` **esiste**: la differenza
   `expectedDisplayTime − t1` è **la stima che il browser stesso fa** del tratto dal decodificatore
   al visibile `[S]`. ⛔ **Resta una previsione, non una conferma** — la spec lo dice — e non
   include lo scanout né il pannello. Ma trasforma un segmento **completamente cieco** in un
   segmento **stimato dal motore**, e lo fa **dentro la stessa pagina**, sullo stesso ferro. `[?]`
   E dà in regalo il confronto della §3.4: `<video>` overlay contro canvas desincronizzato.
3. **Il flag di Chrome.** `GPUExternalTexture.isZeroCopy` dietro
   `chrome://flags/#enable-webgpu-developer-features` `[S]`: non misura tempo, ma dice **se la
   strada zero-copy è viva** — cioè se stiamo misurando la strada che crediamo.

⛔ **E la strada che chiuderebbe il cieco davvero è una sola: un fotodiodo o una telecamera ad alta
velocità puntata sullo schermo.** Il progetto l'ha esclusa (`DECISIONI.md` §2.6), e la scelta è
sana — ma allora ⛔ **il pezzo cieco va scritto come costante dichiarata accanto a ogni numero di
S4**, non taciuto. Un numero di ritardo di REMOTIX che non porta accanto «più 16–40 ms che non
vediamo» è un numero che mente per omissione, ed è **esattamente** la forma di errore che
`LEZIONI.md` §1.7 è costata tre fasi a scoprire.

---

## 5. Che cosa decide per il prodotto

### 5.1 La strada di disegno da scrivere per prima

⭐ **Una sola, e semplice**, perché è l'unica che funziona su tutti e tre i motori:

```
worker dedicato
  ├─ WebTransport                       [S] disponibile nei worker
  ├─ VideoDecoder { optimizeForLatency: true, hardwareAcceleration: 'prefer-hardware' }
  └─ OffscreenCanvas (transferControlToOffscreen)
       ctx = getContext('2d', { desynchronized: true, alpha: false })
       nella callback output:  t = now();  ctx.drawImage(frame, 0, 0, w, h);  frame.close();
```

Le regole che vanno con essa:

| ⛔ | Regola | Perché |
|---|---|---|
| 1 | **si dipinge nella callback `output`, non su rAF** | fino a 16,7 ms regalati a 60 Hz (§3.3) |
| 2 | **`frame.close()` subito dopo il disegno** | *«failing to release them… can cause decoding to stall»* `[S]` |
| 3 | **mai `willReadFrequently`, mai `getImageData` sul percorso caldo** | disattiva l'accelerazione `[S]` |
| 4 | **mai riconfezionare il `VideoFrame` per riscalare** | fa cadere lo zero-copy `[R]` |
| 5 | **buffer del canvas = misura codificata; scala in CSS; debounce sul ridimensionamento** | §3.6 |
| 6 | **niente `transform`, niente `border-radius`, niente elementi sopra la tela** | può far cadere desincronizzato/overlay `[S]` `[R]` |
| 7 | ⭐ **la pagina si serve cross-origin isolated (COOP+COEP)** | senza, i timer di Firefox e Safari hanno grana **1 ms** `[R]` |
| 8 | **`ctx.getContextAttributes().desynchronized` si legge e si dichiara** | è una richiesta, non una garanzia `[S]` |

### 5.2 Che cosa va sotto un interruttore

⚠ **Sotto interruttore, e con il ripiego dichiarato — mai silenzioso** (`CODER.md` §4.2):

| Interruttore | Dove serve | Rischio |
|---|---|---|
| **WebGPU `importExternalTexture`** | Chrome e Safari: unico zero-copy vero `[R]` | ⛔ Firefox non ce l'ha `[S]`; bind group da rifare a ogni fotogramma `[S]`; cade a one-copy se non è NV12 8 bit `[R]` |
| **`<video>` + `VideoTrackGenerator`** | la sola strada che può prendere l'overlay `[S]` | ⛔ worker-only nella spec, nome diverso in Chrome, Firefox previsto 2026-06 `[S]`; si perde il controllo del momento di presentazione `[S]` |
| **`bitmaprenderer`** (`createImageBitmap` + `transferFromImageBitmap`) | ⭐ **la cura per Firefox**, se il `drawImage` là è davvero lento `[S]` | ⚠ `createImageBitmap` è asincrona: un salto di task in più `[?]` |
| **disegno su rAF invece che su `output`** | se il tearing risultasse intollerabile | compra fluidità, vende risposta: **da tenere spento** |
| **`desynchronized`** | acceso di norma | ⛔ **rotto su macOS** `[S]`: serve un interruttore per spegnerlo |

### 5.3 Le decisioni che questo studio tocca

1. ⛔ **`DECISIONI.md` §2.2 (desiderato a 10 bit) — secondo indizio contrario, e da direzione
   nuova.** Non è più solo «il telefono riporta a 8 bit» (§2.3-bis): è che **il cancello di
   zero-copy di WebGPU è `PIXEL_FORMAT_NV12`** `[R]`, che il canvas 2D ha un helper che si chiama
   `DownShiftHighbitVideoFrame` `[R]`, e che `VideoPixelFormat` **non espone P010** `[S]`.
   `[?]` Il 10 bit oggi, in un browser, **costa almeno una copia in più e spesso finisce a 8 bit
   comunque**. La decisione va riscritta come **provvisoria** in attesa della sonda.
2. ⚠ **HDR non si promette.** BT.2020/PQ fa cadere lo zero-copy e il percorso a una copia converte
   verso BT.709 con risultato slavato `[S]`. **Si codifica BT.709.**
3. ⚠ **Il tetto dei 50 ms va accompagnato da una riga sul pezzo cieco.** `SPECIFICHE.md` e
   `PIANO.md` dicono «solo per il pezzo che è nostro»: giusto, ma `[?]` **il pezzo non nostro vale
   16–40 ms a 60 Hz** e l'utente sente la somma. La riga va scritta accanto al tetto, non in fondo.
4. ⭐ **La sonda del browser guadagna una domanda.** Oltre a S4 «quanto costa dipingere», serve
   sapere **quale strada è viva** su ciascun motore: `desynchronized` onorato? `importExternalTexture`
   c'è? `isZeroCopy` dice sì? `VideoTrackGenerator` esiste? Sono quattro righe di rilevamento, e
   decidono che codice si scrive.
5. ⚠ **RCP: la marca del banco è un'estensione di protocollo.** Il rettangolo di 16×16 e il comando
   che lo cambia (con il ritardo `N` iniettabile del controllo P1) vanno scritti in `RCP.md` come
   **funzione di banco**, non improvvisati nel codice di prova.

---

## 6. Le fonti

**Specifiche**
- HTML Standard — `CanvasImageSource`, `desynchronized` — <https://html.spec.whatwg.org/multipage/canvas.html#canvasimagesource>
- HTML Standard — *run the animation frame callbacks* — <https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#run-the-animation-frame-callbacks>
- W3C WebCodecs — <https://www.w3.org/TR/webcodecs/> · <https://w3c.github.io/webcodecs/>
- WebCodecs explainer (limiti di MSE) — <https://github.com/w3c/webcodecs/blob/main/explainer.md>
- w3c/webcodecs discussion #631 — formati YUV a 10 bit — <https://github.com/w3c/webcodecs/discussions/631>
- W3C WebGPU (14 luglio 2026) — <https://www.w3.org/TR/webgpu/> · <https://gpuweb.github.io/gpuweb/>
- gpuweb discussion #4384 — HDR in WebGPU & WebCodecs — <https://github.com/gpuweb/gpuweb/discussions/4384>
- WICG `requestVideoFrameCallback` — <https://wicg.github.io/video-rvfc/>
- W3C High Resolution Time — <https://w3c.github.io/hr-time/>
- W3C Media Source Extensions — <https://w3c.github.io/media-source/> · MSE v2 (7 ago 2026) <https://www.w3.org/TR/media-source-2/>
- W3C MediaStreamTrack Insertable Media Processing — <https://www.w3.org/TR/mediacapture-transform>
- W3C Event Timing — <https://w3c.github.io/event-timing/> · Media Playback Quality — <https://w3c.github.io/media-playback-quality/> · WebRTC Stats — <https://w3c.github.io/webrtc-stats/>
- W3C WebXR Device API — <https://www.w3.org/TR/webxr/>
- WICG `media-latency-hint` — <https://github.com/WICG/media-latency-hint>
- WICG `requestPostAnimationFrame` — <https://github.com/WICG/request-post-animation-frame/blob/main/explainer.md>

**Documentazione dei motori**
- Chromium VideoNG (overlay, buffer opachi) — <https://developer.chrome.com/docs/chromium/videong>
- Chromium *Life of a frame* — <https://chromium.googlesource.com/chromium/src/+/refs/heads/main/docs/life_of_a_frame.md>
- Chromium RenderingNG — <https://developer.chrome.com/docs/chromium/renderingng-architecture>
- Chrome — *Low-latency rendering with the desynchronized hint* — <https://developer.chrome.com/blog/desynchronized>
- Chrome — Intent to Ship `desynchronized` — <https://groups.google.com/a/chromium.org/g/blink-dev/c/nxjWgMIeC1Q/m/GfwjbzeVAwAJ>
- Chromium `graphics-dev` — low-latency canvas su Mac (2025) — <https://groups.google.com/a/chromium.org/g/graphics-dev/c/20qDm3ZD2f8>
- Chrome — WebGPU developer features (`isZeroCopy`) — <https://developer.chrome.com/docs/web-platform/webgpu/developer-features>
- Chrome — timer e cross-origin isolation — <https://developer.chrome.com/blog/cross-origin-isolated-hr-timers>
- Khronos — Chromium presentation layer — <https://www.khronos.org/vulkan/chrome-video/chromium_presentation_layer.html>
- Explainer `OffscreenCanvasAnimation` — <https://github.com/junov/OffscreenCanvasAnimation/blob/master/OffscreenCanvasAnimation.md>
- WebKit — MMS in Safari 17.1 — <https://webkit.org/blog/14735/webkit-features-in-safari-17-1/>
- Bugzilla — `desynchronized` (1536809) — <https://bugzilla.mozilla.org/show_bug.cgi?id=1536809> · WebCodecs meta (1746557) — <https://bugzilla.mozilla.org/show_bug.cgi?id=1746557> · WebGPU meta (1827116) — <https://bugzilla.mozilla.org/show_bug.cgi?id=1827116> · `MediaStreamTrackProcessor` (1749532) — <https://bugzilla.mozilla.org/show_bug.cgi?id=1749532>

**Codice sorgente letto**
- Chromium `media/renderers/paint_canvas_video_renderer.cc` / `.h` — <https://chromium.googlesource.com/chromium/src/+/main/media/renderers/paint_canvas_video_renderer.cc>
- Chromium `media/renderers/video_renderer_impl.{cc,h}` (`low_delay_`, `min_buffered_frames_`) — <https://chromium.googlesource.com/chromium/src/+/refs/heads/main/media/renderers/video_renderer_impl.h>
- Chromium `third_party/blink/renderer/modules/webgpu/external_texture_helper.cc` (il cancello `zero_copy`) — <https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/modules/webgpu/external_texture_helper.cc>
- Chromium `third_party/blink/renderer/modules/webcodecs/video_frame.cc` — <https://chromium.googlesource.com/chromium/src/+/main/third_party/blink/renderer/modules/webcodecs/video_frame.cc>
- Chromium `components/viz/service/display/overlay_processor_win.cc` — <https://raw.githubusercontent.com/chromium/chromium/main/components/viz/service/display/overlay_processor_win.cc>
- Chromium commit `f346a2f` (P010 via VPP, VA-API) — <https://chromium.googlesource.com/chromium/src/+/f346a2f7518133c1df1d777a1870852cde918238>
- Chromium commit `882f184` (P010 zero-copy, solo Vulkan) — <https://chromium.googlesource.com/chromium/src/+/882f184c471fc8e5c59ead4e4c8eaf06dc7f89da%5E%21/>
- Firefox `toolkit/components/resistfingerprinting/nsRFPService.cpp` — <https://searchfox.org/firefox-main/source/toolkit/components/resistfingerprinting/nsRFPService.cpp>
- WebKit `Source/WebCore/page/Performance.cpp` — <https://github.com/WebKit/WebKit/blob/main/Source/WebCore/page/Performance.cpp>
- Selkies `selkies-ws-core.js` — <https://raw.githubusercontent.com/selkies-project/selkies/main/addons/selkies-web-core/selkies-ws-core.js>
- moonlight-web-stream `web/stream/video/pipeline.ts` — <https://raw.githubusercontent.com/MrCreativ3001/moonlight-web-stream/master/web/stream/video/pipeline.ts>
- Xpra html5 `Window.js`, `OffscreenDecodeWorker.js`, `VideoDecoder.js` — <https://raw.githubusercontent.com/Xpra-org/xpra-html5/master/html5/js/VideoDecoder.js>
- noVNC `core/display.js`, `core/decoders/h264.js` — <https://raw.githubusercontent.com/novnc/noVNC/master/core/display.js>

**Misure di terzi (con la scena, quando la dichiarano)**
- webcodecsfundamentals.org — *Rendering* (fps per strada, Big Buck Bunny 1080p; ⛔ **macchina non dichiarata**) — <https://webcodecsfundamentals.org/basics/rendering/>
- webrtcHacks — video frame processing (copie CPU↔GPU) — <https://webrtchacks.com/video-frame-processing-on-the-web-webassembly-webgpu-webgl-webcodecs-webnn-and-webtransport/>
- Hopp — *Latency exploration* (98/126/159 ms, ⭐ **metodo dichiarato**: watermark nel canale Y, andata e ritorno) — <https://www.gethopp.app/blog/latency-exploration>
- Microsoft — GDC 2025, Xbox Cloud Gaming (⛔ risparmio lato server, non end-to-end) — <https://developer.microsoft.com/en-us/games/articles/2025/03/gdc-2025-xbox-cloud-gaming-beta-expanding-your-reach-enhancing-your-game/>
