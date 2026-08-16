# F4-IN-9 — KWin sa dare una superficie della misura ESATTA che chiediamo noi?

*Studio di sola lettura, 14 agosto 2026. Nessuna riga di `src/` toccata, nessun commit.*
*Marche: `[M]` misurato · `[R]` letto nel codice con file e riga · `[S]` letto in una specifica · `[?]` ipotizzato · `[I]` informazione da fuori (upstream).*

---

## ⭐ Il verdetto, in tre righe

1. **SÌ** — la misura che chiediamo arriva **esatta**, fino al buffer: nessun arrotondamento, nessun minimo, nessun massimo, nessuna larghezza pari o multipla di 8/16/64. Su Plasma 6.3.6 KWin **non valida proprio nulla**, e il rettangolo che annuncia a PipeWire è **fisso**, non un intervallo — il consumatore non ha modo di riceverne un altro.
2. **NO** — «scelta dal client» e «cambiata a sessione aperta» sono **false su ogni Plasma rilasciato**: il ridimensionamento a caldo è solo su `master` (l'ultimo tag è **v6.7.4** e il ramo `Plasma/6.8` **non esiste ancora**), e la creazione a misura arbitraria richiede il backend `--drm`, che sul nostro banco non parte senza seat.
3. **SÌ MA** — nella configurazione a cui siamo obbligati (`--virtual`) la misura esatta **si ottiene lo stesso**, però si sceglie **all'avvio del compositore** (`--width`/`--height`), non dal client a sessione aperta. ⭐ **È esattamente quel che fa KDE stessa in produzione.**

> **La conseguenza per la decisione di prodotto**: la conversione delle coordinate **può sparire**, ma al prezzo di legare la misura al momento in cui si avvia la sessione, non al momento in cui il client si collega. Se il modello di REMOTIX avvia una sessione per collegamento, la scala 1 è a portata di mano **oggi**. Se la sessione è longeva e i client si alternano, non lo è.

---

## ⭐⭐ La frase da refutare — refutata in due clausole su tre

> «KWin sa creare un'uscita virtuale di misura arbitraria scelta dal client, sa cambiarla a sessione aperta senza rompere il flusso, e non impone né arrotondamenti né limiti che ci obblighino a riscalare.»

| Clausola | Esito |
|---|---|
| «di misura arbitraria **scelta dal client**» | ⛔ **REFUTATA in pratica.** Vera nel protocollo [R], ma la strada richiede `--drm`, che **non parte da una sessione senza seat** [M, STUDI.md §kde M2, 7 ago]. Su `--virtual` la misura la sceglie **la riga di comando di KWin**, non il client. |
| «cambiarla a sessione aperta **senza rompere il flusso**» | ⛔ **REFUTATA due volte.** Non esiste in nessun Plasma rilasciato [R, verificato oggi contro upstream]. E quando arriverà, «senza rompere il flusso» è comunque falso: rifà lo swapchain, rinegozia il formato PipeWire, ridispone le finestre dell'utente. |
| «non impone né arrotondamenti né limiti» | ✅ **CONFERMATA su 6.3.6** — e in modo quasi imbarazzante: non c'è *nessuna* validazione. ⚠ Ma diventa falsa su `master` (limiti **200×200 … 10000×10000**), e **c'è già oggi un arrotondamento silenzioso** in `--virtual`, in un punto che nessuno aveva guardato: vedi la domanda 3, caso (c). |

---

## 1. Il meccanismo

**La richiesta** [R] `reference-kde/plasma-wayland-protocols/src/protocols/zkde-screencast-unstable-v1.xml:42` — `stream_virtual_output(new_id, name, width, height, scale, pointer)`.

Il percorso della misura, passaggio per passaggio, tutto in `reference-kde/kwin/src/` (6.3.6):

| Dove | Che cosa fa alla misura |
|---|---|
| `wayland/screencast_v1.cpp:98-112` | la prende e la rilancia. `width`/`height` sono `int32_t` **con segno** |
| `plugins/screencast/screencastmanager.cpp:56-68` | `createVirtualOutput(name, description, size, scale)` alla riga **63**. Pass-through |
| `core/outputbackend.cpp:80-83` | la base torna **`nullptr`** — nessun backend tranne DRM la ridefinisce |
| `backends/drm/drm_backend.cpp:340-347` | `new DrmVirtualOutput(this, name, description, size, scale)` alla riga **342** |
| `backends/drm/drm_virtual_output.cpp:28-41` | `OutputMode(size, 60000, Preferred)`, `physicalSize = size`, `modes = {mode}`. **Misura tale e quale** |

⛔ **E qui la strada si chiude, per due `[M]` già in casa:**

- `--virtual` **non sa creare uscite virtuali**: `VirtualBackend` non ridefinisce `createVirtualOutput()`, si cade sulla base che torna `nullptr` → `sendFailed("Could not find output")` [R `core/outputbackend.cpp:80-83`]. Confermato sul banco: [M, STUDI.md §kde M7a, 8 ago].
- `--drm` **non parte da una sessione senza seat**: esce con stato 1 su `Activate()` [M, STUDI.md §kde M2, 7 ago]. Averlo vorrebbe dire occupare la console fisica, cioè smettere di essere un servizio remoto che convive con l'utente locale.

### ⭐ Ma la misura esatta si ottiene lo stesso — dalla riga di comando

Il pezzo che `STUDI.md` §kde non aveva seguito fino in fondo. Su `--virtual` le uscite si creano all'avvio, e la misura passa **intatta**:

- `main_wayland.cpp:470-488` — `--width` e `--height` sono letti con un `toInt()` e basta: **nessun controllo oltre «è un intero»**, nessun minimo, nessun massimo, nessuna parità [R];
- `main_wayland.cpp:507-511` — `addOutput({.geometry = QRect(QPoint(), initialWindowSize), .scale = outputScale})` [R];
- `backends/virtual/virtual_backend.cpp:105-107` — `output->init(info.geometry.topLeft(), info.geometry.size() * info.scale, info.scale, info.modes)` [R];
- `backends/virtual/virtual_output.cpp:58-66` — `OutputMode(pixelSize, 60000, Preferred)` [R].

Con `--scale 1`, `2133×772` resta `2133×772`. ⚠ Con una scala frazionaria **no**: vedi la domanda 3, caso (c).

---

## 2. I limiti

**Su Plasma 6.3.6: non ce n'è nessuno.** È un risultato negativo, e va detto per esteso perché l'assenza di controlli è essa stessa la notizia.

- **Nessuna validazione nel protocollo** [R] `wayland/screencast_v1.cpp:98-112`: niente minimo, niente massimo, niente rifiuto dello zero o dei negativi. Il confronto che smaschera l'asimmetria: `stream_region` **viene** validato, un livello più su, da `screencastmanager.cpp:114-117` (`if (!geometry.isValid()) sendFailed(i18n("Invalid region"))`) — e **per l'uscita virtuale quel controllo non esiste**. Nemmeno `scale` è validato: `streamRegion` ha il ripiego `if (scale == 0)` (`:119-121`), `streamVirtualOutput` no.
- **Nessun limite di texture**: `maxTextureSize`, `GL_MAX_TEXTURE_SIZE`, `16384`, `s_maxSize` **non compaiono in tutto `kwin/src/`** [R, ricerca negativa]. `OutputMode` non impone nulla: `core/output.h:107-130`, `m_size` è un `const QSize` in un contenitore senza logica.
- **Larghezza pari o multipla?** ⛔ **KWin non lo chiede.** Il vincolo di parità è **nostro**, del codificatore 4:2:0 — non di KWin (già in `kde.md:1469`).
- **L'unico limite vero è quello del driver**: `core/gbmgraphicsbufferallocator.cpp:159-164`, `gbm_bo_create(device, width, height, format, flags)` con la misura non allineata. Se fallisce, `backends/drm/drm_virtual_egl_layer.cpp:120-121` scrive un `qCWarning` e `doBeginFrame` torna `std::nullopt` (`:57`).

**Su `master` (il futuro) i limiti compaiono**: `plugins/screencast/screencaststream.cpp:779-780` [R, upstream letto oggi]

```cpp
constexpr spa_rectangle streamMinSize = SPA_RECTANGLE(200, 200);
constexpr spa_rectangle streamMaxSize = SPA_RECTANGLE(10000, 10000);
```

⚠ **E il massimo è applicato male**, il che è una curiosità che vale la pena registrare. Il confronto fra rettangoli in SPA (`/usr/include/spa-0.2/spa/pod/compare.h:57-67`) torna `-1` se *la larghezza **oppure** l'altezza* è minore. Il filtro (`/usr/include/spa-0.2/spa/pod/filter.h:251-255`) scarta solo ciò che è `> 0` rispetto al massimo, cioè ciò che supera **entrambi** gli assi: un `20000×500` **passa** il tetto di 10000 di larghezza, perché la sua altezza sta sotto. Il minimo di 200, invece, è applicato correttamente su entrambi gli assi. [R]

---

## 3. ⛔⛔ Errore o arrotondamento SILENZIOSO?

La domanda più pericolosa, e la risposta è **tre risposte diverse**. Una è buona, una è ottima, una è la trappola.

### (a) Oggi, 6.3.6, alla creazione: né errore né arrotondamento — ma un terzo caso

✅ **Nessun arrotondamento è possibile**, e la prova è che il rettangolo annunciato a PipeWire è **fisso**:

[R] `plugins/screencast/screencaststream.cpp:745` e `:766`
```cpp
spa_rectangle resolution = SPA_RECTANGLE(uint32_t(m_resolution.width()), uint32_t(m_resolution.height()));
spa_pod_builder_add(b, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(resolution), 0);
```

È `SPA_POD_Rectangle`, non `SPA_POD_CHOICE_RANGE_Rectangle` — e `SPA_POD_CHOICE_RANGE_Rectangle` **non compare da nessuna parte nel file** [R, ricerca negativa]. Il consumatore o accetta quella misura, o non c'è formato.

Le due cose che *sembrano* arrotondamenti e non lo sono:
- `screencaststream.cpp:157`, `SPA_ROUND_UP_N(m_resolution.width() * bpp, 4)` — allinea i **byte dello stride**, non la larghezza (2133×4 = 8532, già multiplo di 4, invariato). `SPA_PARAM_BUFFERS_align = 16` (`:188`) è l'allineamento del **puntatore in memoria**.
- Il pitch GBM lo decide il driver, ma viene letto e propagato onestamente: `gbm_bo_get_stride_for_plane` → `chunk->stride` in `plugins/screencast/screencastbuffer.cpp:83`. **La larghezza annunciata resta quella chiesta.**

⚠ **Il caso cattivo, qui, è un terzo che non è né errore né conversione**: una misura assurda (`0×0`, `-1×-1`, `100000×100000`) **non viene rifiutata** — l'uscita viene creata, aggiunta al workspace con `addOutput` + `outputsQueried` (`drm_backend.cpp:344-345`, quindi visibile a tutti i client di output-management e capace di ridisporre il desktop), e lo stream **semplicemente non emette mai un fotogramma**, con un solo `qCWarning` nel journal e **nessun `sendFailed()` al client**. Silenzio sì, ma non una conversione nascosta.

### (b) Domani, con la negoziazione: errore rumoroso — **a patto di chiedere un rettangolo FISSO**

[R] `/usr/include/spa-0.2/spa/pod/filter.h:247-262` — produttore `Range` ∩ consumatore `None` (valore fisso): copia il nostro valore **solo se sta dentro**; se non ci sta, `n_copied == 0` → **`return -EINVAL`**, e quel formato cade. ✅ Fallimento rumoroso, nessun arrotondamento.

⛔ **Ma se proponiamo un RANGE, l'arrotondamento silenzioso c'è davvero**, e in tre passi:
1. `filter.h:264-282` — `Range` ∩ `Range` produce l'intersezione, **senza verificare che sia non vuota**;
2. `/usr/include/spa-0.2/spa/pod/iter.h:436-441` e `:430-431` — `spa_pod_fixate` trasforma ogni `Choice` in `None` prendendo il **primo** valore, cioè il minimo dell'intersezione;
3. `plugins/screencast/screencaststream.cpp:237-245` (**master**) — KWin fa `spa_format_video_raw_parse` e poi `m_source->resize(negotiatedSize)` **senza alcun controllo**:
```cpp
spa_format_video_raw_parse(format, &m_videoFormat);
const QSize negotiatedSize(m_videoFormat.size.width, m_videoFormat.size.height);
m_resolution = negotiatedSize;
if (m_source && m_source->followsStreamSize()) {
    m_source->resize(negotiatedSize);
}
```

⭐ **Regola operativa, da scrivere nel nostro codice il giorno che tocchiamo la negoziazione: si propone `SPA_POD_Rectangle`, mai `SPA_POD_CHOICE_RANGE_Rectangle`.** Col rettangolo fisso l'arrotondamento è impossibile per costruzione; con un intervallo si prende il minimo dell'intersezione e nessuno lo dice.

### (c) ⛔ L'arrotondamento silenzioso che ci riguarda **OGGI**

Sta nella riga che abbiamo appena letto per la strada `--virtual`, e non era in `STUDI.md` §kde:

[R] `backends/virtual/virtual_backend.cpp:106`
```cpp
output->init(info.geometry.topLeft(), info.geometry.size() * info.scale, info.scale, info.modes);
```

`QSize * qreal` **arrotonda all'intero più vicino** [S, documentazione Qt: *«Multiplies the given size by the given factor, and returns the result rounded to the nearest integer»*]. Con `--scale 1` non succede niente. Con qualunque scala frazionaria, `--width 2133 --scale 1.5` diventa **3200**, e nessuno lo dice: né un errore, né un avviso.

⭐ **Si passa sempre `--scale 1` e i pixel veri.** È la stessa conclusione di `STUDI.md` §kde §8.4, ma per un meccanismo diverso e su un'altra riga di codice — lì era `chooseScale()` che buttava via la scala del protocollo, qui è una moltiplicazione che arrotonda i pixel.

---

## 4. Il cambio a caldo

### Oggi: impossibile, per quattro barriere e mezza

- `OutputMode::m_size` è **`const`** [R `core/output.h:107-130`];
- `DrmVirtualOutput` non ha `resize`, non ha `setMode`, non ridefinisce `applyChanges` — l'unico setter è `setDpmsMode` [R `backends/drm/drm_virtual_output.h:29-46`]; l'elenco dei modi è scritto **una volta sola**, nel costruttore (`:39`);
- `Output::applyChanges` [R `core/output.cpp:517-543`] copia `enabled`, `transform`, `position`, `scale`, `rgbRange`, `desiredModeSize`… e **non tocca mai** `modes` né `currentMode`. `desiredModeSize` viene salvato, ma per l'uscita virtuale **nessuno lo consuma** (l'unico che fa il modeset è `DrmOutput`, con il proprio override, `backends/drm/drm_output.cpp:476`);
- `.modes = {mode}` è una lista di **un solo elemento**, quindi nemmeno kscreen avrebbe qualcosa da scegliere;
- e sulla nostra configurazione `--virtual` l'uscita virtuale **non esiste affatto**.

**L'unica via oggi è (A), chiudere e rifare lo stream.** Il prezzo, con i numeri che abbiamo: chiudere lo stream **distrugge l'uscita** [R `screencastmanager.cpp:65-67`]; rimettere in piedi il solo flusso costa **65, 65 e 67 ms** su tre giri [M, STUDI.md §kde M7b, 8 ago]; su KDE **non trascina l'input** (EIS è indipendente dallo screencast), che è il vantaggio su GNOME.

### ⭐ Domani: il codice esiste, ma non è in nessun Plasma rilasciato

**Questa è la correzione che questo rapporto porta a `STUDI.md` §kde.** Lo studio dava il ridimensionamento come *«milestone 6.8, cioè ottobre 2026»*. Verificato **oggi** contro `invent.kde.org` [R, upstream]:

| Ramo | `canResize` in `drm_virtual_output.h` |
|---|---|
| `Plasma/6.3` … `Plasma/6.7` | ⛔ **assente in tutti e cinque** |
| `Plasma/6.8` | ⛔ **il ramo non esiste** |
| `master` | ✅ presente |

L'ultimo tag pubblicato è **v6.7.4**. Cioè: il ridimensionamento è **solo su `master`**, la 6.8 **non è ancora stata nemmeno ramificata**, e Trixie è ferma a 6.3.6. La sostanza di `STUDI.md` §kde regge — «non è una funzionalità perduta, è una che arriva» — ma **la data è più lontana di quanto il documento lascia credere**, e nessuna delle versioni che un utente può installare oggi ce l'ha.

Quando arriverà, il meccanismo è quello previsto [R, `master`]:
- `backends/drm/drm_virtual_output.cpp:141-144`, `canResize()` → `true`;
- `:146-154`, `resize()` costruisce un nuovo `OutputMode` con la misura **tale e quale** (nessun arrotondamento), `setState`, poi `Q_EMIT m_backend->outputsQueried()`;
- `plugins/screencast/screencaststream.cpp:783-784`, il rettangolo diventa un `CHOICE_RANGE` **solo** se `m_source->followsStreamSize()`; per un'uscita reale `min = max = default`, cioè nessuna rinegoziazione.

⛔ **E «senza rompere il flusso» resta falso.** `outputsQueried()` fa ripartire la riconfigurazione degli output: è esattamente il ciclo segnalato in revisione [I, Nick Haghiri, 3 luglio 2026, già in `STUDI.md` §kde §8.2-bis], e la guardia è obbligatoria, non un'ottimizzazione — [R] `plugins/screencast/outputscreencastsource.cpp:170-173` (`master`):
```cpp
if (m_output->pixelSize() == size) {
    return;
}
```
Resta poi tutto il prezzo di `STUDI.md` §kde §8.3: le finestre si ridispongono, e il `PlacementTracker` è indicizzato **sulla geometria dell'output**, quindi tornare a una misura già vista teleporta indietro le finestre.

---

## 5. ⭐ Che cosa fa `krdp` quando il client chiede un ridimensionamento

La prova diretta che il mandato cercava. Le due copie in `reference-kde/` **divergono**, e la divergenza è la risposta.

### `krdp-6.3.6` — quello che gira sul Plasma di oggi: **non lo implementa affatto**

- Non esiste `DisplayControl.cpp`, non esiste `disp_server_context_new`, non esiste `#include <freerdp/server/disp.h>` [R, ricerca negativa].
- Il blocco che imposta le settings FreeRDP (`krdp-6.3.6/src/RdpConnection.cpp:303-347`, elencate riga per riga) **non contiene** `SupportDisplayControl` né `SupportMonitorLayoutPdu`: la capability è **semplicemente omessa**, quindi FreeRDP non annuncia il canale `disp` e il client non lo apre.
- `DesktopWidth`/`DesktopHeight` del client: **zero occorrenze** in tutto il sorgente [R, ricerca negativa].
- ⭐ **Anzi, il rovescio esatto**: `krdp-6.3.6/src/RdpConnection.cpp:445` **rifiuta la connessione** del client che non sa accettare un resize *imposto dal server* — `"Client doesn't support resizing, aborting"`. Cioè krdp 6.3.6 **impone la propria misura al client**, e il client deve subirla.
- `SuppressOutput` esiste ma è solo una pausa: il rettangolo del PDU è ignorato, l'handler riceve solo `allow` [R `:480-489`].

### `krdp` master (HEAD `1dd52ba`, 31 luglio 2026) — lo implementa, e lo attua **esattamente come vogliamo noi**

- `krdp/src/DisplayControl.cpp` (78 righe, copyright 2025 David Edmundson), nel build a `src/CMakeLists.txt:21-22`.
- Capability: `krdp/src/RdpConnection.cpp:464-465` — `FreeRDP_SupportMonitorLayoutPdu` e `FreeRDP_SupportDisplayControl` a `true`.
- Limiti annunciati: `DisplayControl.cpp:45-67` — `MaxNumMonitors = 1`, `MaxMonitorAreaFactorA/B = 8192`. Multi-monitor **rifiutato**: `:18-30`, `NumMonitors != 1` → `CHANNEL_RC_BAD_CHANNEL`. `Left`/`Top`/`PhysicalWidth`/`Orientation`/`DesktopScaleFactor` del PDU sono **ignorati**.
- ⭐ **Che cosa ne fa: non riscala.** La catena è `SessionController.cpp:58` → `VideoStream::setRequestedSize` (`VideoStream.cpp:520-529`), che gira la richiesta **a PipeWire** (`setRequestedSize` su `sourceStream` e `encodedStream`), **non** al compositore. Quando la misura del fotogramma cambia (`VideoStream.cpp:937-943`), rifà la superficie GFX: `performReset` → `RDPGFX_RESET_GRAPHICS_PDU` + `CreateSurface` (`:793-817`).
- ⭐ **Nessuna riscalatura lato server, in nessuna delle due versioni**: nessun `sws_scale`, `swscale`, `filter_graph`, `QImage::scaled(`, nessuna VAAPI scale [R, ricerca negativa su `src/` e `server/` di entrambe]. L'unico «scaling» è `FreeRDP_SmartSizing` (`krdp/src/RdpConnection.cpp:444`), che è **lato client** — mstsc adatta la finestra. L'unica conversione è quella delle **coordinate del puntatore** (`PlasmaScreencastV1Session.cpp:229`).
- E anche in master il server **impone** la misura al client: `VideoStream.cpp:780-789` scrive `FreeRDP_DesktopWidth/Height` con `frame.size` e manda `DesktopResize`. Il `DesktopWidth` *del client* non è mai letto, in nessuna delle due versioni.

### ⭐⭐ Le due conclusioni che valgono più del codice

1. **KDE risolve il nostro stesso problema nel modo che vogliamo noi**: misura nativa, **zero conversione lato server**, ridimensionamento delegato al compositore via PipeWire. Non hanno scelto di riscalare: hanno scelto di cambiare la misura della sorgente. La strada c'è, ed è quella.
2. ⛔ **Ma non funziona ancora, nemmeno per loro**: `setRequestedSize` **non esiste** in kpipewire 6.3.6 (zero occorrenze di `equestedSize` in `kpipewire/src/` [R, ricerca negativa]). Il krdp master, messo su un Plasma 6.3.6, risponderebbe al Display Control **senza alcun effetto visibile**. Serve la controparte lato compositore, che è su `master` e basta.
3. E un dettaglio che dice molto: krdp chiede un'uscita virtuale **solo** se glielo si dice da riga di comando, `--virtual-monitor WIDTHxHEIGHT@SCALE` (`krdp/server/main.cpp:48-52`, parsing `:129-140`). **Non esiste un `--resolution`**, il KCM non ha nessuna voce di risoluzione (`src/kcm/krdpserversettings.kcfg:13-42`), e il servizio **non passa mai `--virtual-monitor`**. ⭐ **Cioè krdp, da servizio, cattura lo schermo fisico — e quando usa un'uscita virtuale, ne sceglie la misura all'avvio, non a richiesta.** È la stessa forma a cui `--virtual` costringe noi.

---

## 6. La scala di Plasma: il desktop diventa illeggibile?

### ✅ No, e si dimostra — alla creazione la scala è **1.0 per qualunque misura**

`DrmVirtualOutput` mette `physicalSize = size`, cioè **i pixel al posto dei millimetri** [R `backends/drm/drm_virtual_output.cpp:34`; su `master`, `:35`]. Da lì il conto di `chooseScale` [R, `master`, `src/outputconfigurationstore.cpp:843-905`]:

```cpp
const double dpiX = modeSize.width() / (output->physicalSize().width() / 25.4);
const double scaleX = std::clamp(dpiX / targetDpi, 1.0, maxScaleX);
```

Alla creazione `modeSize == physicalSize`, quindi `dpi` vale **esattamente 25,4** su entrambi gli assi, **qualunque misura chiediamo**. E 25,4 sta sotto entrambi i `targetDpi` possibili — 30,5 per lo schermo grande (`:878-883`) e 96 per il monitor normale (`:886`) — quindi `std::clamp(dpi/targetDpi, 1.0, …)` dà **1.0**. In più `:903-906` riporta a 1.0 tutto ciò che sta sotto 1,20 (*«Low-but-not-1 scale factors look like a blurry mess»*).

⭐ **Una misura strana non fa cambiare il fattore di scala. Il desktop non diventa illeggibile, e non per fortuna: per una proprietà del conto che non dipende dalla misura.** E la scala chiesta nel protocollo viene comunque buttata via e ricalcolata (`outputconfigurationstore.cpp:507`, `607-656`, già in `STUDI.md` §kde §8.4): si passa `scale = 1` e i pixel veri.

### ⚠ Ma il ragionamento vale **solo alla creazione** — e il giorno del ridimensionamento a caldo va rimisurato

`DrmVirtualOutput::resize()` [R `master`, `:146-154`] cambia `modes` e `currentMode` con `setState`, e **non tocca `physicalSize`**, che vive in `Information` e resta quello della creazione. Dopo un ridimensionamento `modeSize != physicalSize`, e `dpi = 25,4 × (nuovo / originale)`: ingrandendo di più di ~1,44× su **entrambi** gli assi si supera la soglia di 1,20 e la scala calcolata **sale**. Con un'uscita creata a 800×600 e portata a 2133×1600, il conto dà **2,0** — cioè un desktop che mostra metà delle cose.

⚠ **Attenuante, non prova**: `outputconfigurationstore.cpp:726` fa `.scaleSetting = existingData.scaleSetting.value_or(chooseScale(output, modeline->size()))` — cioè `chooseScale` **non viene rieseguito** se una scala è già memorizzata per quell'uscita. Alla prima configurazione la 1.0 dovrebbe essere memorizzata e poi conservata. **[?] Non è misurato**, e dipende da come `findOutputIndex` (`:221`) riconosce la *stessa* uscita virtuale fra una configurazione e l'altra. **Va misurato il giorno che il ridimensionamento a caldo diventa disponibile** — non prima, perché prima non è misurabile.

---

## Quel che questo rapporto NON dice

- ⛔ **Nessuna misura nuova. Su `192.168.0.2` gira GNOME, non KDE**: non c'era niente su cui misurare e non ho inventato nulla. Ogni `[M]` citata qui è di `STUDI.md` §kde (banchi del 7 e 8 agosto) ed è **attribuita**. Le domande 3(a), 3(c), 5 e 6 sono **`[R]` pura**.
- **Non risponde alla domanda di prodotto, ma solo a un suo quarto.** La decisione («scala 1 su tutti e quattro i desktop») ha qui la risposta per **KDE soltanto**. GNOME/Mutter, XFCE, LXQt e Cinnamon non li ho guardati. ⛔ La conversione delle coordinate **non sparisce** finché non c'è un sì su tutti e quattro.
- **Non dice se `stream_virtual_output` con `--drm` funzioni davvero** con una misura dispari come 2133×772: è lettura del codice. `--drm` non parte sul nostro banco [M, M2] e la validazione **non è misurabile con `--virtual`** [M, M11] — dove ogni misura, buona o assurda, riceve lo stesso `Could not find output`.
- **Non dice quanto costi davvero un ridimensionamento a caldo** — buco video, fotogrammi persi, input perduto. Il codice non è in nessun Plasma rilasciato, quindi **oggi non è misurabile da nessuna parte**, nemmeno compilando: servirebbe un `master` di kwin *e* di kpipewire.
- **Non ho verificato sul sorgente Qt l'arrotondamento di `QSize::operator*(qreal)`** (le intestazioni Qt non sono installate su questa macchina): è **`[S]`**, dalla documentazione Qt, non `[R]`. È il punto più debole del rapporto ed è quello che innesca la regola `--scale 1`: se qualcuno la vuole come `[R]`, sono due righe di banco.
- **Non ho letto il nostro `src/`** — il mandato lo vietava. La regola «rettangolo fisso, mai un `RANGE`» (domanda 3b) è quindi una raccomandazione **non verificata contro quel che il nostro consumatore fa davvero oggi**.
- **I numeri di riga di `master` invecchiano**: li ho letti da `invent.kde.org` **oggi, 14 agosto 2026**, contro `master` (HEAD `212915b`). Quelli di 6.3.6 sono stabili, perché è un tag.
