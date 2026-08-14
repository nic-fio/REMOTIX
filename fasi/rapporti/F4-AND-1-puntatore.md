# F4-AND-1 — Il puntatore su Android e Samsung DeX, nel browser

*Anello di studio della fase 4. Scritto il 14 agosto 2026, a codice fermo.*
*Mandato: rispondere a sei domande sul puntatore su Chrome per Android/DeX, e **provare a smentire**
l'ipotesi corrente sull'errore di coordinate.*
*⛔ Nessuna riga di prodotto toccata: questo anello legge, misura sulla carta e cita.*

---

## ⭐⭐⭐ In una riga

**L'ipotesi delle bande nere descrive con precisione al pixel il RAMO DI RIPIEGO di
`cl_geometria()` — non il ramo normale, che le bande le sottrae già.** ⇒ non è «la mappatura è
sbagliata»: è **«quel ramo è stato preso»**, e la domanda vera diventa *perché `schermo.dipinta`
non c'era*. ⛔ E la spiegazione alternativa — «è un fatto di Android: unità, viewport, DPR» — la
**smentisco con il sorgente**: `clientX` e `getBoundingClientRect()` escono dalle **stesse due
divisioni** in Blink, quindi pizzico, barra dell'URL e scorrimento **si cancellano** nella
sottrazione; e su DeX `devicePixelRatio` vale 1, perché DeX gira a 160 dpi.

⭐ **E la cosa che questo anello ha imparato smentendo SE STESSO**: avevo trovato una spiegazione
elegante del sintomo A — *«è il nostro `preventDefault()` che chiede a Chrome di spegnere i
`mouse*`»* — e **l'ordine delle righe in `pointer_event_manager.cc` la uccide** (§3.1). ⇒ **il
sintomo A resta senza causa dimostrata**, e la ragione oggi scritta nel codice non ha nessuna
fonte (D4).

---

## 1. Il verdetto sull'ipotesi, con l'aritmetica

### 1.1 Che cosa dice il codice, riga per riga

`[R]` `src/pagina.html`, `cl_geometria()` — e il gemello `tocco_geometria()`:

```js
let bx0 = 0, by0 = 0, sx = tela.width / t[0], sy = tela.height / t[1];   /* ← RIPIEGO */
if (d && d.fotogramma && d.fotogramma[0] > 0) {                          /* ← NORMALE */
  bx0 = d.x; by0 = d.y;
  sx = d.l / d.fotogramma[0]; sy = d.a / d.fotogramma[1];
}
```

`d` è `schermo.dipinta`, che `componi()` riempie a ogni fotogramma `[R]` (`this.dipinta = { l, a,
x, y, vista, fotogramma, scala }`) con **esattamente** l'origine e la misura del rettangolo
dipinto, bande comprese.

⇒ ⭐ **Il ramo normale sottrae le bande.** L'ipotesi «la nostra mappatura ignora le bande» è
**falsa come descrizione del codice scritto**.

### 1.2 Ma è vera come descrizione del ramo di ripiego — e l'aritmetica combacia al pixel

`[M]` 14 agosto 2026, conto fatto con i numeri del mandato (vista/buffer `2560×926`, fotogramma
`1920×1080`), programma di tre righe in `python3`:

| | |
|---|---|
| scala d'impaginazione | `min(2560/1920, 926/1080)` = **0,857407** |
| rettangolo dipinto | **1646×926** in **(457, 0)** |

⇒ le bande sono **457 px a sinistra e 457 a destra**, e **zero sopra e sotto**. Il numero
dell'ipotesi è giusto.

| `x` nel buffer | ramo NORMALE | ramo di RIPIEGO | errore |
|---:|---:|---:|---:|
| 457 (bordo sinistro dell'immagine) | 0,0 | 342,8 | **+342,8** |
| 868 | 479,4 | 651,0 | +171,6 |
| 1280 (centro) | 960,0 | 960,0 | **0,0** |
| 1691 | 1439,4 | 1268,2 | −171,2 |
| 2102 (bordo destro) | 1918,8 | 1576,5 | **−342,3** |

### 1.3 ⭐⭐ E QUESTA È LA FIRMA CHE DECIDE

Il ripiego ha **tre** proprietà insieme, e tutt'e tre si vedono in trenta secondi:

1. l'errore è **zero al centro** dell'immagine;
2. cresce **linearmente** verso i bordi, fino a **±343 px di tela**;
3. ⛔ **è SOLO ORIZZONTALE.** `by0 = 0` e `sy` corretto anche nel ripiego, perché in verticale
   l'immagine riempie tutto (926 su 926): **nel ripiego l'errore verticale è esattamente zero.**

⇒ ⭐ **Se l'utente vede il puntatore remoto spostato anche IN ALTO o IN BASSO, l'ipotesi delle
bande è morta**, e non c'è bisogno di nessun'altra prova. Se invece l'errore è puramente
orizzontale e nullo al centro, l'ipotesi regge — ma allora la domanda non è «la formula è
sbagliata», è **«perché `schermo.dipinta` era assente»**, che è un'altra riga e un'altra cura.

---

## 2. La spiegazione «è Android» — e perché la smentisco

*Il mandato chiede di cercare prove che l'errore venga dalle unità, dal viewport o dal DPR. Le ho
cercate — spec, sorgente Blink, bug tracker. ⛔ Non reggono, e le ragioni si leggono nel codice del
motore, non in un blog. Il dettaglio con le citazioni sta in §3.2 e §3.3; qui c'è il verdetto.*

### 2.1 `clientX` e `getBoundingClientRect()` sono nello STESSO spazio ⇒ si cancellano

`[S]` **WICG, spiegazione ufficiale della Visual Viewport API**
(<https://github.com/WICG/visual-viewport>), che è il documento che stabilisce quale API sta in
quale viewport:

> *«all other coordinates are generally relative to the layout viewport (e.g.
> getBoundingClientRects, elementFromPoint, **event coordinates**, etc.)»*

e sul pizzico:

> *«the visual viewport shrinks but the layout viewport is unchanged»*

⇒ ⛔ **Il pinch-zoom, la barra dell'URL, la tastiera a schermo e lo scorrimento non possono
produrre l'errore**: la nostra formula usa `ev.clientX - r.left`, cioè una **differenza fra due
numeri dello stesso spazio**, e qualunque traslazione o scala del viewport visuale entra in
tutt'e due e sparisce. Lo stesso vale per lo `scale` CSS del pizzico interno (`tocco_ingrandisci`):
`getBoundingClientRect()` lo contiene già `[S]`, e `vx = r.width / tela.width` lo assorbe.

### 2.2 Su DeX `devicePixelRatio` vale 1 ⇒ niente DPR frazionario

`[S]` **Samsung Developer, *Samsung DeX app testing guide***
(<https://developer.samsung.com/samsung-dex/testing.html>): per riprodurre DeX si dà

> `wm density 160, wm size 1080x1920` — *«to test the app in the same density and resolution as
> Samsung DeX Desktop Mode»*

160 dpi è **mdpi**, cioè il fattore di riferimento di Android: **`devicePixelRatio = 1`**.

`[M]` E il numero del mandato lo conferma da solo: `documentElement.clientWidth × dpr` = **2560**.
Con il 2,625 tipico dei telefoni Samsung servirebbe `clientWidth = 975,2` — e `clientWidth` è un
intero, `975 × 2,625 = 2559,4 → 2559`, **non 2560**. Con `dpr = 1` invece `clientWidth = 2560`
esatto, e `926 = 1080 − 154` è il monitor 2560×1080 dell'utente meno la barra del titolo e la
barra delle applicazioni di DeX.

⚠ **E qui c'è una cosa che avrei sbagliato a dare per scontata**: `[R]` `devicePixelRatio` in
Blink **non è** il fattore del dispositivo, è `DeviceScaleFactor × LayoutZoomFactor` — cioè ci sta
dentro anche **lo zoom di pagina** (§3.4). ⇒ su DeX può valere 1,5 senza che nessuno abbia toccato
un monitor. ⭐ **Ma non cambia il verdetto**: `clientWidth` si restringe esattamente di quanto
`dpr` cresce, e `vx = r.width / tela.width` è **misurato dal vivo** dal DOM. Lo zoom di pagina
sposta *quanti pixel si dipingono*, **non** *dove va il puntatore*.

⇒ ⛔ **Tutta la famiglia «DPR non intero, arrotondamenti, sub-pixel» è fuori causa in questo
caso.** E anche se ci fosse: `[R]` l'errore massimo del `LayoutUnit` di Blink è **1/64 di pixel
CSS** (`layout_unit.h`, *«storing multiples of 1/64 of a pixel»*), cioè **0,0156 px** — non 343.

### 2.3 ⇒ La graduatoria

| spiegazione | regge? | prova |
|---|---|---|
| le bande ignorate — **ramo normale** | ⛔ **no** | `[R]` `cl_geometria()` le sottrae |
| le bande ignorate — **ramo di ripiego** | ✅ **sì, al pixel** | `[M]` tabella §1.2; firma §1.3 |
| unità/viewport/pizzico di Android | ⛔ **no** | `[S]`+`[R]` stesso viewport, si cancellano |
| barra dell'URL che compare/sparisce | ⛔ **no** | `[R]` `browser_controls_adjustment_` cambia **solo l'altezza** di `VisibleRect`, non l'origine |
| DPR frazionario di Samsung | ⛔ **no** | `[S]` DeX = 160 dpi ⇒ dpr 1; `[M]` 2560 è esatto |
| `clientX` troncato sui `MouseEvent` | ⚠ **sì, ma vale ~1 px** | `[R]` `mouse_event.h`: `std::floor(client_x_)` |
| **`?video=worker`** (vedi §4, D1) | ✅ **sì, e peggio** | `[S]`+`[R]`: `tela.width` resta **16** |
| coordinate di FOTOGRAMMA spedite come TELA (§4, D2) | `[?]` solo se fotogramma ≠ tela | `[R]` |

---

## 3. Le sei domande

### 3.1 Quando e perché Chrome per Android sopprime i `mouse*`

**La regola normativa.** `[S]` **W3C Pointer Events Level 2, §11** *Compatibility mapping with
mouse events* (<https://www.w3.org/TR/pointerevents2/#compatibility-mapping-with-mouse-events>) —
i passi normativi di §11.2, per un dispositivo che sa fare hover, sono:

1. *«If the `isPrimary` property … is false then dispatch the pointer event and terminate these
   steps»* ⇒ **pointer non primario ⇒ nessun evento di mouse**;
2. *«If the pointer event dispatched was `pointerdown` and the event was **canceled**, then set
   the PREVENT MOUSE EVENT flag for this `pointerType`»*;
3. *«If the PREVENT MOUSE EVENT flag is not set … `pointermove` → fire a `mousemove`»*;
4. *«If the pointer event dispatched was `pointerup` or `pointercancel`, **clear** the PREVENT
   MOUSE EVENT flag»*.

⛔⭐ **E la nota che chiude la questione**, sempre §11:

> *«Mouse events can only be prevented **when the pointer is down**. **Hovering pointers (e.g. a
> mouse with no buttons pressed) cannot have their mouse events prevented.**»*

⇒ ⭐⭐ **Secondo la specifica, quel che abbiamo visto sul DeX NON PUÒ SUCCEDERE**: il `mousemove`
di un mouse che passeggia senza pulsanti premuti **non è sopprimibile**. Il sintomo A non è
comportamento previsto: o è un difetto del motore, o è un secondo meccanismo.

⚠ E c'è una nota che invece riguarda il **dito**, non il mouse — `[S]` PE2 §11.3: *«If the user
agent supports both Touch Events and Pointer Events, the user agent SHOULD NOT generate
compatibility mouse events as described in this section»*. `[R]` Su Chrome per Android infatti i
`mouse*` del **dito** non nascono qui: nascono dai *gesture events*
(`gesture_manager.cc`, `suppress_mouse_events_from_gestures_`). ⇒ ⛔ **è vero che su Android il
tocco e il mouse hanno due strade diverse — ma non è la strada del mouse che si chiude.**

**Il meccanismo, nel motore.** `[R]` Chromium `main`, letto il 14 agosto 2026,
`third_party/blink/renderer/core/input/pointer_event_manager.cc`,
`PointerEventManager::SendMousePointerEvent`. `prevent_mouse_event_for_pointer_type_` è un array
**indicizzato per `pointerType`** (non per `pointerId`):

| | |
|---|---|
| **armato** | `if (result != kNotHandled && type == kPointerdown && isPrimary())` — dove `result` è l'esito del **`pointerdown`**, non del `mousedown` |
| **letto** | `send_compat_mouse = isPrimary() && !prevent_mouse_event_for_pointer_type_[…]` |
| **azzerato** | su `pointerup`/`pointercancel` primario; ⭐ **su qualunque `pointermove` a pulsanti alzati** (`event_type == kPointerMove && !pointer_event->buttons()`); in `SendMouseAndPointerBoundaryEvents` con `buttons()==0`; in `Clear()` |

### ⛔⭐⭐ E QUI SMENTISCO ME STESSO — un'ipotesi mia, uccisa dal sorgente

Leggendo per la prima volta avevo visto la riga
`result = event_handling_util::MergeEventResult(result, dispatch_result.second)` — che fonde nel
`result` **anche l'esito del `mousedown` di compatibilità** — e ne avevo tratto una tesi elegante:
*«è il nostro `ev.preventDefault()` dentro `cl_su_mousedown` che chiede a Chrome di spegnere i
`mouse*`: il sintomo A ce lo siamo dato da soli»*.

`[R]` **È FALSA, e l'ordine delle righe lo dimostra.** Nella funzione l'ordine è:

```
DispatchPointerEvent(...)                        →  result
if (result != kNotHandled && kPointerdown …)     →  ARMA il flag      ← QUI
send_compat_mouse = …                            →  legge il flag
mouse_event_manager_->DispatchMouseEvent(...)    →  il `mousedown` arriva alla pagina  ← DOPO
result = MergeEventResult(result, …)             →  serve solo al VALORE DI RITORNO
```

⇒ **il flag è armato PRIMA che il `mousedown` esista**: un `preventDefault()` su `mousedown` non
può armarlo. E anche se potesse, `[R]` **il flag si azzera al primo `pointermove` a pulsanti
alzati** — cioè al primo movimento dopo il rilascio.

⭐ **Questo è il risultato che vale di più di tutta la sezione**: la spiegazione più comoda del
sintomo A — «colpa nostra, una riga» — **non regge**, e nemmeno quella scritta oggi nel codice
(vedi D4). **Il sintomo A resta senza causa dimostrata `[?]`**, ed è un buco da chiudere con una
misura (M3), non con una deduzione.

**Le piste che restano, tutte `[R]` o `[S]`, nessuna dimostrata qui:**

1. `[R]` **la strada dell'hover su Android è un'altra**: un mouse **senza pulsanti** passa da
   `EventForwarder.onHoverEvent()` (`ACTION_HOVER_MOVE` → `kMouseMove`), un mouse **con un
   pulsante giù** da `onTouchEvent()`. Sono due percorsi Android distinti, e solo il primo muove
   il puntatore in hover.
2. `[R]` **la soppressione da trascinamento**: quando parte un drag nativo Blink emette
   `pointercancel` e *«suppress the pointer event stream for the corresponding pointer»*
   (`mouse_event_manager.cc`; flag `SuppressPointerStreamAfterDrag`, **stable**).
3. `[S]` **esistono situazioni riconosciute in cui l'hover cambia senza nessun evento di
   movimento** — Mustaq Ahmed (Chromium) sulla lista `public-pointer-events`, dicembre 2024:
   *«After a short delay, Chrome fires pointer/mouse over/out events and **no move event**, and
   shows hover effect»* (spec issue w3c/pointerevents#529).
4. `[S]` **storicamente su Android + mouse l'hover non produceva NIENTE** — la matrice di prova di
   Patrick H. Lauke (<https://patrickhlauke.github.io/touch/tests/results/>), riga *Android 10 /
   Chrome 77 + mouse*: colonna hover = **`none`**, e la nota *«Chromium-based browsers all don't
   fire any events when mouse pointer is moved over the button»*.
   ⚠ Ma allora sarebbero morti **tutt'e due**, `pointermove` compreso — e non è il nostro caso.

**`pointermove` è sempre affidabile con un mouse Bluetooth?**

- ✅ `[R]` **rispetto a questo filtro sì**: `prevent_mouse_event_for_pointer_type_` è letto solo
  per decidere `send_compat_mouse`. `pointermove` è l'evento primario e non ci passa.
- ⚠ `[R]` **`pointerType` non è garantito «mouse»**: `EventForwarder.java` distingue
  `SOURCE_MOUSE + TOOL_TYPE_MOUSE` (mouse vero) da `SOURCE_MOUSE + TOOL_TYPE_FINGER`
  (**touchpad**), e il secondo diventa «mouse» solo se
  `isTrackpadToMouseEventConversionEnabled()`. ⛔ **Il nostro filtro
  `if (ev.pointerType === "touch") return;` è quindi già la scelta giusta** (nega il tocco invece
  di pretendere il mouse): un touchpad DeX che si dichiarasse diversamente passerebbe lo stesso.
- ⚠ `[R]`+`[S]` **è allineato a `requestAnimationFrame`**: `main_thread_event_queue.cc`,
  `IsRafAlignedEvent()` include `kMouseMove`/`kTouchMove`/`kMouseWheel`; e
  <https://developer.chrome.com/blog/aligning-input-events> lo dichiara dal **Chrome 60**:
  *«the input pipeline will delay dispatching continuous events (wheel, mousewheel, touchmove,
  pointermove, mousemove) and dispatch them right before the requestAnimationFrame() callback»*.
  ⇒ ⭐ **il puntatore non può muoversi più spesso di un fotogramma di schermo**, qualunque cosa
  faccia il mouse. Vedi §3.5.

---

### 3.2 Che cosa valgono `clientX`, `offsetX`, `pageX`, `screenX` su Android/DeX

`[S]` **CSSOM View Module §10** (<https://drafts.csswg.org/cssom-view/>) per le definizioni, `[S]`
**Blink Coordinate Spaces** (<https://www.chromium.org/developers/design-documents/blink-coordinate-spaces/>)
per lo spazio che Chrome usa davvero:

| attributo | definizione `[S]` | spazio in Chrome | serve a noi? |
|---|---|---|---|
| `clientX/Y` | *«relative to the origin of the **viewport**»* | ⭐ **frame / layout viewport, in pixel CSS** (*«In web APIs this is referred to as "client coordinates"»*) | ✅ **è quello giusto** |
| `pageX/Y` | `clientX` + scorrimento del layout viewport | documento, pixel CSS | ⛔ no: `getBoundingClientRect()` è già in spazio *client* |
| `screenX/Y` | *«relative to the origin of the Web-exposed screen area»* — che la spec dice **in pixel CSS** | ⛔ **in Chrome sono DIP**, e `[R]` `mouse_event.cc` **non** li divide per lo zoom | ⛔ **mai**: su DeX ci sono dentro anche la posizione della finestra sul desktop |
| `offsetX/Y` | *«relative to the padding edge of the **target node**, **ignoring the transforms**»* | pixel CSS dell'elemento | ⛔ **due trappole**: il `target` non è garantito essere la tela, e `[R]` `offsetX` usa `std::round` mentre `clientX` usa `std::floor` — **due regole di arrotondamento nello stesso evento** |
| `movementX/Y` | `[S]` Pointer Lock: *«movementX = eNow.screenX − ePrevious.screenX»* | ⛔ **spazio SCHERMO, interi**, non scalati per il pizzico | solo con lock; `[R]` noi in `cl_agganciato` |

⭐ **E il punto che chiude la questione «è Android»**, con tre fonti che dicono la stessa cosa:

1. `[S]` **WICG visual-viewport**: *«all other coordinates are generally relative to the layout
   viewport (e.g. getBoundingClientRects, elementFromPoint, **event coordinates**, etc.)»*
2. `[S]` **blink-dev, Intent to Ship**: *«Pinch zoom affects some window APIs like
   innerWidth/Height and scrollX/Y while not others (like **event coordinates and
   getBoundingClientRect**)»* (<https://groups.google.com/a/chromium.org/g/blink-dev/c/A12B1S4eGxY>)
3. `[R]` **il sorgente**, catena completa:
   `WebMouseEvent::PositionInRootFrame() = position_in_widget_ / frame_scale_ + frame_translate_`
   con `frame_scale_ = VisualViewport().Scale()`, poi
   `client_point = frame_point × (1 / LayoutZoomFactor())`.
   ⇒ **il `pageScale` del pizzico è diviso via**, e `getBoundingClientRect()` passa dalle **stesse
   due operazioni** (`AdjustRectForScrollAndAbsoluteZoom`), **senza** aggiustamento per il visual
   viewport.

⇒ ⛔ **Pizzico, barra dell'URL, tastiera a schermo e scorrimento si cancellano nella differenza
`clientX − rect.left`.** Non ci serve `visualViewport`, non ci serve `devicePixelRatio` nella
mappatura. `[R]` La pagina non li usa — **e fa bene**.

⚠ ⭐ **UNA COSA VERA E NUOVA, però, e ci riguarda**: `[R]` `mouse_event.h`

```cpp
virtual double clientX() const { return std::floor(client_x_); }
```

⇒ **sui `MouseEvent` `clientX` è troncato all'intero**; `[R]` sui `PointerEvent` è **frazionario**
(`pointer_event.cc`, tranne `click`/`auxclick`/`contextmenu`, dove `[S]` la spec **impone** il
`Math.floor`). ⭐ **Un secondo motivo, indipendente dal sintomo A, per stare su `pointermove`**: il
troncamento costa fino a 1 px CSS, che diviso per `vx·sx` diventa **~1,2 px di tela** su DeX — e su
un telefono con `dpr` alto e la tela rimpicciolita, molto di più.

---

### 3.3 `getBoundingClientRect()` su Android

- `[S]`+`[R]` **stesse unità e stesso spazio di `clientX`** (vedi §3.2). ⇒ la differenza è pulita.
- ⚠ **`rect.left` è il bordo della BORDER box**, non della content box (`[S]` CSSOM View §6:
  `getClientRects()` restituisce *«its border area»*). ⇒ un `border` o un `padding` sulla tela
  sposterebbe lo zero. `[R]` **Noi non ne abbiamo** (`#schermo { display; background;
  image-rendering; margin: 0 }`) — ma è un errore che nasce dal foglio di stile, non dal
  JavaScript, e vale la pena saperlo.
- ⭐⭐ **La barra dell'URL NON sposta né `clientX` né `getBoundingClientRect()`.** `[R]`
  `visual_viewport.cc`:
  ```cpp
  visible_size.Enlarge(0, browser_controls_adjustment_);   // ← solo l'ALTEZZA
  return gfx::RectF(ScrollPosition(), visible_size);       // ← origine invariata
  ```
  e `FrameTranslation()` usa **solo** `VisibleRect().origin()`, che quell'aggiustamento non tocca.
  ⇒ ⛔ **anche durante la transizione della barra la formula resta valida.**
  `[S]` E l'ICB non cambia affatto: *«The ICB will not change height in response to the URL bar»*
  (<https://github.com/bokand/URLBarSizing>, documento di David Bokan/Chrome). Cambia
  `innerHeight` *«in real-time»* `[S]` (<https://developer.chrome.com/blog/url-bar-resizing>), e
  arriva un `resize` **al `touchend`** — che `[R]` la pagina raccoglie
  (`addEventListener("resize", rinegozia_vista)`).
- **Arrotondamenti con DPR frazionario.** `[R]` `getBoundingClientRect()` lavora in `gfx::RectF` e
  **non arrotonda**; la precisione interna è `LayoutUnit` = **1/64 di pixel CSS**
  (`layout_unit.h`, *«storing multiples of 1/64 of a pixel»*) ⇒ errore massimo **0,0156 px**.
  `[M]` Quattro ordini di grandezza sotto i 343 px del sintomo: **fuori causa**.
- ⛔⭐ **Ma `clientWidth` sì che arrotonda** — `[S]` l'IDL è `readonly attribute **long**
  clientWidth`, e `[R]` Blink fa `.Round()` (arrotondamento al più vicino, non troncamento).
  ⇒ vedi **D5**: la nostra `misura_vista()` fa `clientWidth × devicePixelRatio`, cioè
  **arrotonda e poi moltiplica**. Su DeX (dpr = 1) non costa niente; su un telefono a 2,625 costa
  fino a ~1,3 pixel fisici. `[S]` La strada giusta la documenta Chrome stesso:
  `ResizeObserver` con **`devicePixelContentBox`** (<https://web.dev/articles/device-pixel-content-box>),
  che dà *«an element's content box in device pixel (i.e. physical pixel) units»*.

---

### 3.4 `devicePixelRatio` su DeX

**Quanto vale.**

- `[S]` Samsung Developer, *DeX app testing guide*
  (<https://developer.samsung.com/samsung-dex/testing.html>): DeX Desktop Mode gira a
  **`wm density 160`**.
- `[S]` AOSP `DisplayMetrics`: *«one DIP is one pixel on an approximately 160 dpi screen… Thus on
  a 160 dpi screen this density value will be 1»*.
- `[R]` La catena è verificata e **senza arrotondamenti**:
  `PhysicalDisplayAndroid.updateFromDisplay()` legge `displayMetrics.density` →
  `display_android_manager.cc`: `display->set_device_scale_factor(dip_scale)`.

⇒ ⭐ **il fattore del dispositivo su DeX è 1.**

⛔⭐ **MA `devicePixelRatio` NON È IL FATTORE DEL DISPOSITIVO.** `[R]` `local_frame.cc`:

```cpp
double LocalFrame::DevicePixelRatio() const {
  double ratio = page_->InspectorDeviceScaleFactorOverride();
  ratio *= LayoutZoomFactor();          // ← ci sta dentro lo ZOOM DI PAGINA
  return ratio;
}
```

⇒ **lo zoom di pagina di Chrome per Android** (Impostazioni → Accessibilità → Zoom pagina, e lo
zoom per-sito) **si moltiplica dentro `devicePixelRatio`**. Su DeX il numero può quindi valere
1,5 o 2 con l'utente che non ha toccato nessun monitor.

⭐ **E questo deposito ha già pagato quella lezione**: `DECISIONI.md` §5.0 registra la misura del
10 agosto — *«Su Chrome `screen.width` NON cala con lo zoom di pagina, mentre `devicePixelRatio`
sale»*. ⚠ **Ma per la mappatura del puntatore non fa danno**, e vale la pena dirlo perché è
controintuitivo: `clientWidth` si restringe esattamente di quanto `dpr` cresce, `misura_vista()`
resta la misura fisica, e `vx = r.width / tela.width` viene **misurato dal vivo** ⇒ la
conversione regge. Lo zoom di pagina sposta *quanti pixel si dipingono*, non *dove va il
puntatore*.

`[M]` E i numeri del mandato dicono che oggi lo zoom è al 100 %: `clientWidth × dpr = 2560`
**esatto** vuole `dpr = 1` e `clientWidth = 2560`. E `926 = 1080 − 154` è il monitor 2560×1080
dell'utente meno la barra del titolo e quella delle applicazioni di DeX.

**Cambia quando il telefono si aggancia al monitor?**

- `[R]` **Chrome NON ricrea la scheda**: `chrome/android/java/AndroidManifest.xml` dichiara
  `android:configChanges="…|screenSize|smallestScreenSize|uiMode|**density**|touchscreen|…"` ⇒
  Android chiama `onConfigurationChanged()` e non distrugge l'Activity.
- `[R]` La catena a caldo esiste: `DisplayManager.DisplayListener.onDisplayChanged` →
  `PhysicalDisplayAndroid.updateFromDisplay` (rilegge `density`) → `DisplayAndroid.update` →
  `onDIPScaleChanged` + JNI `updateDisplay(..., dipScale, ...)`.
- ⚠ `[?]` **L'ultimo anello — browser → renderer — non è verificato.**
- ⛔⭐ **E c'è una segnalazione che dice che quell'anello si rompe davvero**: forum Samsung,
  *«Chrome scaling issue after reconnecting to DeX (Galaxy Z Fold6, One UI 8)»* — le schede Chrome
  restano *«massively zoomed in as if displayed on a phone screen»* dopo un distacco e riattacco,
  mentre **Samsung Internet e Firefox non sono colpiti**
  (<https://eu.community.samsung.com/t5/galaxy-z-fold-z-flip/chrome-scaling-issue-after-reconnecting-to-dex-galaxy-z-fold6/td-p/13584915>).
  ⚠ **Fonte debole** (forum, non riproducibile da qui) — ma è **esattamente la forma** che il
  nostro `[?]` aperto prevedeva, e sarebbe la spiegazione di *«l'immagine è della misura
  sbagliata»*, non di *«il puntatore va altrove»*.

**Come accorgersene.** `matchMedia("(resolution: " + devicePixelRatio + "dppx)")` con il suo
evento `change`, riarmato a ogni scatto. ⛔ `[R]` **la pagina non ne installa nessuno**, e lo
dichiara già come `[?]` aperto: *«il cambio di `devicePixelRatio` a finestra ferma… sotto
`Emulation.setDeviceMetricsOverride` non arriva NIENTE»*.
⇒ ⭐ **Il DeX è il banco vero che quel commento chiedeva**: agganciare e sganciare il monitor a
pagina aperta è la misura che l'emulazione non sapeva fare (M4).

**E una conferma per il codice che c'è già** — `[R]` Chromium, `TouchDevice.java`, commit `d99d448`
del 17 aprile 2026 (`Bug: 41445959`, *«Fix hover media query reporting hover:hover on touch-only
Android devices»*):

> *«On desktop-like Android sessions, built-in SOURCE_MOUSE devices are real and should be counted
> (for example Android Desktop and **Samsung DeX**).»*
> *«**Known gap: Samsung DeX mode where the phone acts as a trackpad (tested on S24 Ultra) reports
> both `isExternal()=false` and `UI_MODE_TYPE_DESK=false`, so `isRealPointerDevice()` returns
> false.** See crbug.com/502461774.»*

⇒ ⛔ **Su Android `hover: hover` è deliberatamente `none`** su qualunque dispositivo con
touchscreen che non sia in sessione desktop-like, e su DeX-trackpad **fallisce anche
`any-hover`**. ⭐✅ **La pagina sceglie la disposizione con `(any-pointer: fine)`** `[R]`
(`tocco_interroga("(any-pointer: fine)")`) — **che è la query giusta**, l'unica che resta vera in
tutti gli scenari della tabella di Chromium. ⚠ Ma la regola vale la pena scriverla accanto:
**su Android, per sapere se c'è un mouse ci si fida di `event.pointerType`, poi di
`any-pointer: fine`, MAI di `hover: hover`.**

---

### 3.5 `pointerrawupdate` e `getCoalescedEvents()`

**Esistono su Chrome per Android?** ✅ Sì, tutt'e tre, e da parecchio `[S]` (chromestatus):

| API | desktop | **Android** | WebView |
|---|---|---|---|
| `getCoalescedEvents()` | 58 | **58** | — |
| `pointerrawupdate` | 77 | **77** | 77 |
| `getPredictedEvents()` | 77 | **77** | 77 |
| `getCoalescedEvents()` tolto dai contesti insicuri | 129 | **129** | 129 |
| `pointerrawupdate` solo in secure context (interop) | 142 | **142** | 142 |

`[S]` L'*Intent to Ship* di `pointerrawupdate` si impegna esplicitamente su *«all six Blink
platforms (Windows, Mac, Linux, Chrome OS, **Android**, and Android WebView)»*
(<https://groups.google.com/a/chromium.org/g/blink-dev/c/mUW58VMIrTM/m/gIotA4HwBAAJ>).

**Vincoli.**

- ⛔ `[S]` PE3 §4.2.5: *«The user agent MUST fire a pointer event named `pointerrawupdate`, and
  **only do so within a secure context**»*; `getCoalescedEvents()` è `[SecureContext]` (§4.1).
  ⭐ **REMOTIX è su HTTPS: il vincolo è già soddisfatto.**
- ⭐⭐ `[R]` **si generano SOLO se c'è già un ascoltatore registrato**, e non è un dettaglio di
  consegna: è generazione a monte. `main_thread_event_queue.cc`:
  ```cpp
  if (has_pointerrawupdate_handlers_.load(std::memory_order_relaxed)) {
    if (event->Event().GetType() == WebInputEvent::Type::kMouseMove) { … kPointerRawUpdate … }
  }
  ```
  Il flag viene da `EventHandlerRegistry` (`cc::EventListenerClass::kPointerRawUpdate`). ⇒
  **finché nessuno ascolta, l'evento non viene nemmeno creato** — il costo di non usarli è zero,
  e il costo di usarli è reale.
- ⚠ `[S]` PE3 mette l'avvertimento in norma: *«Adding listeners for the `pointerrawupdate` event
  might negatively impact performance»*.

**Frequenza.** `[S]` PE3 §4.2.5: *«In contrast with `pointermove`, user agents SHOULD dispatch
`pointerrawupdate` events **as soon as possible and as frequently as the JavaScript can handle**»*,
e *«the user agent MUST dispatch the `pointerrawupdate` event **before** the corresponding
`pointermove`»*. `[R]` `IsRafAlignedEvent()` **non** include `kPointerRawUpdate`.
⚠ Ma il coalescing resta permesso `[S]`, e `[R]` è implementato
(`AreCoalescablePointerRawUpdateEvents()`).

**Servono a ridurre la latenza?**

- ⭐ **`pointerrawupdate`: sì, e la cifra è ufficiale.** `[S]` chromestatus (riassunto letterale):
  `pointermove` è rAF-allineato e *«may add **half a frame of latency on average** from when they
  happened until they are delivered to the javascript»* ⇒ **~8 ms a 60 Hz, ~4 ms a 120 Hz**.
- **`getCoalescedEvents()`: no, non toglie latenza** — `[S]` PE3 §10.1 dice che serve alla
  *fedeltà*: *«the un-coalesced events can be used to draw smoother curves»*. ⛔ Per noi, che
  mandiamo **una posizione assoluta** e non una traccia, **non serve a niente**: `[R]`
  `cl_manda_puntatore()` scarta già tutto ciò che non ha cambiato pixel.
- **`getPredictedEvents()`: riduce la latenza *percepita*** disegnando in avanti `[S]` (PE3 §10).
  ⛔ **Da non usare qui**: predire dove va il mouse e **mandarlo al desktop remoto** vuol dire
  iniettare un movimento che l'utente non ha fatto.

⚠ **Per REMOTIX il guadagno è da misurare, non da dedurre** `[?]`: 8 ms su un anello mano →
server → codifica → rete → decodifica → vetro potrebbero non vedersi. ⭐ Ma il posto giusto dove
metterlo è **`pointerrawupdate` che spedisce, `pointermove` che disegna**: il filo non deve
aspettare il fotogramma, il disegno sì.

⛔ **E nessuna delle tre c'entra col sintomo B**: cambiano *quando* arriva una posizione, non
*quale*.

---

### 3.6 Chrome per Android contro Samsung Internet

- `[S]` Samsung Internet è **Chromium**: la versione per Windows **30.0.0.95** (25 marzo 2026)
  dichiara il motore **M143** (<https://developer.samsung.com/internet/release-note/windows-release-note.html>).
  ⇒ ⭐ **Samsung Internet è indietro di parecchie versioni** rispetto al Chrome stabile — il banco
  di questo deposito ha misurato **Chrome 151** il 13 agosto 2026 `[M]`. Sono ~8 versioni maggiori,
  cioè mesi.
- ⚠ **Conseguenza pratica**, e vale più di qualunque elenco di differenze: tutto quel che è §3.1
  (il filtro dei `mouse*`) e §3.5 (`pointerrawupdate`) va **rimisurato su Samsung Internet**, non
  dedotto da Chrome. Un motore di otto versioni più vecchio ha *quel* `pointer_event_manager.cc`,
  non questo.
- `[?]` **Differenze specifiche documentate su questi punti: non ne ho trovate.** Samsung dichiara
  il supporto a DeX da Samsung Internet 5.2 e raccomanda il *responsive design*
  (<https://developer.samsung.com/internet/android/web-development-guide-for-dex.html>), ma quella
  pagina **non parla** né di `devicePixelRatio`, né di viewport, né di eventi di puntatore.
- ⭐ **L'unica differenza segnalata è proprio sul nostro terreno**, e viene da un forum, non da una
  fonte primaria: nella segnalazione di §3.4 sullo scaling di Chrome dopo il riaggancio del DeX,
  **Samsung Internet e Firefox non sono colpiti** — solo Chrome. ⚠ `[?]` Non riproducibile da qui,
  ma dice dove guardare se l'immagine dovesse tornare della misura sbagliata.
- ⇒ ⭐ **La regola pratica**: quel che questo rapporto dice di **Chromium `main`** vale per Chrome
  per Android **oggi**; su Samsung Internet va **rimisurato**, non dedotto. In particolare il
  commit `d99d448` (aprile 2026) che riscrive le media query `hover` **e nomina DeX** non è
  ancora in un Samsung Internet stabile.

---

## 4. I difetti trovati leggendo il codice

*Tutti `[R]` su `src/pagina.html` al 14 agosto 2026 (il file è in lavorazione: i numeri di riga
scivolano, i nomi delle funzioni no).*

### D1 ⛔⭐ Con `?video=worker` la geometria è rotta di fabbrica — e il puntatore va a (0,0)

| | |
|---|---|
| `[R]` | `<canvas id="schermo" width="16" height="16">` — il buffer nasce a **16×16** |
| `[R]` | `accendi_worker()` fa `$("schermo").transferControlToOffscreen()`; da lì in poi è il **worker** a fare `oc.width = l` |
| `[S]` | **HTML Standard §4.12.5**: *«When setting the value of the `width` or `height` attribute, if the context mode of the `canvas` element is set to **placeholder**, the user agent must throw an `InvalidStateError`»* — e **nessun meccanismo** riporta la misura della `OffscreenCanvas` sull'elemento segnaposto |
| ⇒ | `[R]` `cl_geometria()` legge `tela.width`, che **resta 16 per sempre** ⇒ `vx = r.width / 16` invece di `r.width / 2560` |

`[M]` Conto: con `r.width ≈ 2560` CSS, `vx = 160` invece di 1; `((clientX − left)/160 − 457)/0,857`
è **negativo ovunque** ⇒ `cl_satura()` lo porta a 0. **Il puntatore remoto resterebbe inchiodato
nell'angolo in alto a sinistra.**

⚠ ⭐ **E `schermo.dipinta` invece arriva giusto** (lo specchia `specchia()` ogni 100 ms): è la
forma esatta di `F5-desktop-vero.md` — *il difetto non è DENTRO un pezzo, è **FRA** due pezzi
ciascuno corretto per conto suo*. Il rapporto `F4-A7` §9 aveva già scritto la metà della frase
(*«con `?video=worker` la pagina non sa che tela ha»*): questa è l'altra metà, con la citazione
normativa che la chiude.

⇒ **La cura è una riga**: in `cl_geometria()` e `tocco_geometria()` la misura del buffer va presa
da `schermo.dipinta.vista` (che il worker manda già) e **non** da `tela.width`. ⛔ Oppure: rifiutare
di comandare quando le due divergono, e **dirlo**.

### D2 ⚠ `cl_px` è in coordinate di FOTOGRAMMA, ma viene saturato e spedito come coordinata di TELA

`[R]` `sx = d.l / d.fotogramma[0]` porta il punto in **pixel del fotogramma decodificato**; poi
`cl_satura()` lo ritaglia su `cl_tela()` = `schermo.tela_l × tela_a` e `cl_manda_puntatore()` lo
spedisce come `PUNTATORE`, che `[S]` `RCP.md` §7.3 definisce **sulla tela**:

> *«Le coordinate sono sulla tela, e sono indici di pixel: `0 ≤ x < tela_larghezza`»*

⭐ **Oggi combacia**, perché `[R]` la pagina chiede una tela **fissa** `1920×1080`
(`const tela_l = pari(1920, …)`) e il fotogramma arriva a quella misura.
⛔ **Ma `RCP.md` §6.2 impone di accettare e dipingere i fotogrammi in volo alla misura
PRECEDENTE** durante un `ADATTA_TELA`: in quella finestra `cl_px` è in un'unità e il messaggio ne
dichiara un'altra, **senza nessun errore da nessuna parte**. È la stessa famiglia di D1.

### D3 — ⛔ *(RITIRATO)* Il `preventDefault()` su `mousedown` **non** è la causa del sintomo A

*Lo lascio scritto perché è la tesi che avevo, ed era sbagliata:* vedi §3.1. `[R]` Il flag si arma
**prima** che il `mousedown` di compatibilità venga consegnato alla pagina, e si azzera al primo
`pointermove` a pulsanti alzati. ⇒ **niente da correggere in `cl_su_mousedown`.**

⭐ Quel che resta di vero: `[S]` la spec vuole che si annulli su **`pointerdown`**, non su
`mousedown` (§11.2 passo 2). Spostare gli ascoltatori del modo classico su
`pointerdown`/`pointerup`/`pointermove` — una famiglia sola, quella primaria — toglierebbe la
dipendenza da eventi che il motore considera **facoltativi** `[S]` (*«The compatibility mapping
with mouse events are an OPTIONAL feature of this specification»*, PE2 §11). ⚠ È una semplificazione
con un prezzo: `ev.button` ha valori diversi fra i due (`[S]` PE3 §11, nota sul drag).

### D4 ⛔ La ragione scritta accanto alla cura del sintomo A è una `[?]` travestita da fatto

`[R]` `src/pagina.html`, ancora `F4-INPUT-CLASSICO`:

> *«su Android gli eventi `mouse*` sono di COMPATIBILITA'… e Chrome li sospende quando il tocco e
> il mouse si contendono lo stesso dispositivo — e il DeX e' esattamente quel caso, perche' lo
> schermo del telefono resta tattile»*

⛔ **Questa frase non ha nessuna fonte**, e §3.1 mostra che è **contraddetta** dalla spec: *«Hovering
pointers … cannot have their mouse events prevented»*. È la forma **E5** di `REVIEWER.md` — una
deduzione scritta come fatto. ⭐ **La cura non cambia** (`pointermove` serve, ed è misurato che
serve): cambia la ragione, che va riscritta come *«il motore ha smesso di consegnarli e non
sappiamo perché — `pointermove` è l'evento primario e non dipende da quella scelta»*.

### D5 ⚠ `misura_vista()` arrotonda e poi moltiplica

`[R]` `misura_vista()` fa `Math.round(documentElement.clientWidth × devicePixelRatio)`.
⛔ `[S]` `clientWidth` è dichiarato `readonly attribute **long**` (CSSOM View §6) e `[R]` Blink lo
**arrotonda al più vicino** (`AdjustLayoutUnit(...).Round()`). ⇒ si perde fino a **0,5 px CSS
prima** di moltiplicare — su DeX (dpr = 1) niente, su un telefono a 2,625 fino a ~1,3 pixel
fisici, e su un DeX con lo zoom di pagina al 150 % (§3.4) ancora di più.

⭐ `[S]` La strada giusta la documenta Chrome stesso: `ResizeObserver` con
**`devicePixelContentBox`** (<https://web.dev/articles/device-pixel-content-box>), che dà
*«an element's content box in device pixel (i.e. physical pixel) units»* ed è consegnato *«just
before they are being painted»*. ⚠ **Non è il difetto di oggi** (vale 1 px, non 343): è un
`[?]` che diventa vero il giorno in cui qualcuno userà REMOTIX dallo schermo del telefono.

### D6 ⚠ `movementX` non è nello spazio che `cl_agganciato` gli attribuisce

`[R]` `cl_su_mousemove()` con la cattura accesa fa
`cl_px += ev.movementX * CL_GUADAGNO / (g.vx * g.sx)` — cioè tratta `movementX` come **pixel CSS
della tela sul vetro**. ⛔ `[S]` Pointer Lock lo definisce invece come
*«movementX = eNow.screenX − ePrevious.screenX»*, e `[R]` Blink lo calcola in **coordinate
schermo (DIP), troncate a intero**, senza dividerlo né per lo zoom né per il page-scale
(`mouse_event_manager.cc`; e il commit **`66ad18c093eb`**, 18 feb 2022, *«ZoomForDSF: Don't
adjust movementX/Y by the device scale factor»*, `Bug: 1297149, 907309`, ha cambiato proprio
quella convenzione).
⚠ **Oggi non fa danno** — la cattura è spenta per difetto e su DeX zoom e dpr valgono 1 — ma il
`CL_GUADAGNO` misurato su una macchina non si trasporta su un'altra. `[S]` E l'interoperabilità
è dichiarata rotta: w3c/pointerlock#42 — Chrome in pixel fisici scalati, Firefox in CSS px,
Safari in DIP, **e nessun browser scala per il pinch-zoom**.

### D7 ⚠ Nessun osservatore di `devicePixelRatio`, e il DeX è il banco che lo misurerebbe

Vedi §3.4. `[R]` la pagina lo dichiara già come `[?]` aperto e spiega perché non l'ha scritto
(*«da una prova indiretta che non prova niente non si scrive una cura»*, `LEZIONI.md` §1.11) —
⭐ **ma adesso la prova diretta esiste: è un cavo HDMI.**

### D8 ⚠ `REMOTIX.input_classico.stato()` non espone quel che serve a distinguere le ipotesi

`[R]` espone `puntatore`, `ultimo_spedito`, `tela`, `tela_di_comodo` — e da lì **non si può dire**
se il ramo normale o il ramo di ripiego di `cl_geometria()` sia stato preso. ⇒ ⭐ **due chiavi in
più chiudono la domanda di questo rapporto** (vedi M1).

---

## 5. Le misure che chiudono la domanda

*Nessuna richiede di modificare il prodotto tranne M1, che aggiunge due chiavi a un oggetto di sola
lettura.*

### M1 — ⭐ La misura che decide fra le due ipotesi (due righe)

In `REMOTIX.input_classico.stato()` aggiungere:

```js
      geometria: cl_geometria(),
      dipinta: schermo.dipinta,
```

Poi, sul DeX, in console:

```js
REMOTIX.input_classico.stato()
```

| che cosa si legge | che cosa vuol dire |
|---|---|
| `dipinta: null` **oppure** `geometria.bx0 === 0` con la tela 16:9 in una finestra più larga | ⭐ **l'ipotesi delle bande VINCE** — si è preso il ramo di ripiego, e la cura è capire perché `dipinta` non c'era |
| `geometria.bx0 === 457` | ⛔ **l'ipotesi delle bande PERDE**: le bande sono sottratte, l'errore viene da altrove |
| `geometria.vx` molto diverso da `1/devicePixelRatio` | ⛔ **D1**: `tela.width` è vecchio (worker) |

### M2 — ⭐ La firma dell'errore, senza toccare niente (trenta secondi)

Sul DeX, mettere il puntatore su **tre** punti e guardare dove finisce quello remoto:

1. al **centro** dell'immagine;
2. sul **bordo sinistro** dell'immagine;
3. su un punto **in basso al centro**.

| esito | verdetto |
|---|---|
| errore **zero al centro**, ±343 ai lati, **nessun errore verticale** | ✅ ipotesi delle bande (ramo di ripiego) |
| errore **anche verticale** | ⛔ **ipotesi morta** — vedi D1, D2 |
| errore **anche al centro** | ⛔ ipotesi morta: è un'origine sbagliata, non una scala |

### M3 — ⭐ La `[?]` che resta aperta: **perché** i `mousemove` erano morti

*§3.1 ha ucciso la spiegazione comoda. Questa misura dice quale delle piste rimaste è quella
giusta, e la pagina la registra già a metà (`cl_visti_mouse` / `cl_visti_pointer`).*

Sul DeX, in console:

```js
let m = 0, p = 0, ultimo = "";
addEventListener("mousemove",   e => { m++; }, true);
addEventListener("pointermove", e => { p++; ultimo = e.pointerType + " b=" + e.buttons; }, true);
setInterval(() => console.log("mouse", m, "pointer", p, ultimo), 1000);
```

Poi: **muovere senza cliccare** (30 s) → **cliccare 5 volte** → **muovere ancora**.

| esito | verdetto |
|---|---|
| `mouse` fermo e `pointer` che sale **anche senza mai cliccare** | ⛔ non è nessun meccanismo documentato: **è un bug del motore**, e va aperto a monte con questa traccia |
| `mouse` si ferma **solo dopo un clic** e riparte al movimento successivo | è il flag di §3.1, e si comporta **come la spec vuole** |
| `mouse` si ferma dopo un clic e **non riparte più** | ⛔ l'azzeramento su `pointermove` a pulsanti alzati non funziona: bug, con riproduttore |
| `ultimo` non dice `mouse` | ⭐ è il caso «DeX trackpad» del commento in `TouchDevice.java` (§3.4) |

### M4 — `devicePixelRatio` all'aggancio del monitor

Aprire la pagina **sullo schermo del telefono**, leggere `devicePixelRatio` e
`documentElement.clientWidth`, agganciare il monitor DeX, rileggerli. E guardare se è arrivato un
`resize`. ⇒ chiude la `[?]` di §3.4 e **D7**, e mette alla prova la segnalazione dello scaling
rotto dopo il riaggancio.

### M4-bis — Lo zoom di pagina, che nessuno guarda

Leggere `devicePixelRatio` sul DeX **con lo zoom di pagina al 100 %** e poi con lo zoom cambiato
(Impostazioni → Accessibilità → Zoom pagina). `[R]` §3.4 dice che il numero cambia; ⇒ verificare
che `misura_vista()` e `getBoundingClientRect()` restino coerenti, cioè che **l'immagine cambi
misura e il puntatore no**.

### M5 — Il lato server, con una riga di registro che già esiste

`[R]` `src/input.c`, `input_puntatore()`: se la regione di `libei` non è grande come la tela, il
server **lo scrive**:

> *«⚠ la regione (%.0fx%.0f) NON e' grande come la tela (%ux%u): scalo le coordinate»*

⇒ ⭐ **cercare quella riga nel registro della sessione del DeX.** Se c'è, l'errore è a valle di
tutto quel che dice questo rapporto e nessuna cura nella pagina lo toglierebbe. Se non c'è, il
server sta facendo una somma e il difetto è **nella pagina** — che è dove l'ho cercato.

---

## 6. Che cosa questo rapporto NON dice

1. ⛔ `[?]` **Non ho misurato niente su un DeX vero**: non ne ho uno. Tutto ciò che è marcato `[M]`
   qui è **aritmetica sui numeri del mandato**, non una lettura da un dispositivo. ⇒ **questo
   rapporto non chiude il sintomo B: dice dove guardare e con quale prova**, e le prove sono §5.
2. ⛔ `[?]` **Non so perché i `mousemove` siano mancati per dodici secondi** con trentacinque clic
   in mezzo. ⭐ E questa è la cosa che ho *scoperto di non sapere*: avevo una spiegazione, §3.1 la
   smentisce, e **nessuna fonte ne offre un'altra** — anzi `[S]` la spec dice che quel che è
   successo *non dovrebbe poter succedere* (*«Hovering pointers … cannot have their mouse events
   prevented»*). M3 lo chiude.
3. ⚠ **Le pagine di `issues.chromium.org` non sono leggibili** dagli strumenti che ho: ogni numero
   di bug qui è citato **come compare in una fonte che ho letto davvero** (un commento nel
   sorgente, un messaggio di commit, una issue W3C, un thread blink-dev), **non** perché ne abbia
   aperto la pagina. In particolare **non ho letto** lo stato di 40215797, 40660627, 41445959,
   502461774.
4. `[?]` **Non ho verificato l'ultimo anello del cambio di densità**, browser → renderer: la
   catena Android → `set_device_scale_factor` è letta `[R]`, il *push* al renderer no. La
   segnalazione del forum Samsung sullo scaling rotto dopo il riaggancio è **una fonte debole** e
   la marco così.
5. `[?]` **Non so come si comporti `offsetX` sotto la `transform: scale()`** della tela nel modo a
   tocco. Non serve oggi (usiamo `clientX`), e §3.2 dà due ragioni indipendenti per non passarci
   mai — ma se qualcuno fosse tentato di semplificare, quella è la domanda da fare prima.
6. ⚠ **Non ho misurato niente su Samsung Internet.** §3.6 dice solo di quanto è indietro il motore
   e perché questo basta a **non** trasportarci le conclusioni.
7. ⚠ **Un dettaglio sub-pixel che ho trovato e non ho approfondito**: `[R]` `FrameTranslation()`
   applica `gfx::ToFlooredPoint` all'origine del visual viewport ⇒ con pizzico **e** trascinamento
   insieme resta un errore intrinseco inferiore a 1 px CSS nelle coordinate degli eventi. Non
   c'entra col sintomo B (vale 1 px, non 343) e non ho trovato un bug che lo tracci.

---

## 7. Le fonti, in un posto solo

*⛔ Ogni riga qui è stata **letta**, non citata a memoria. Le date sono del 14 agosto 2026.*

**Specifiche `[S]`**

- W3C **Pointer Events Level 2**, §11 *Compatibility mapping with mouse events* —
  <https://www.w3.org/TR/pointerevents2/#compatibility-mapping-with-mouse-events>
- W3C **Pointer Events Level 3**, §4.1, §4.2.5, §10, §11 — <https://www.w3.org/TR/pointerevents3/>
- W3C **Pointer Lock**, *Extensions to the MouseEvent Interface* —
  <https://w3c.github.io/pointerlock/#extensions-to-the-mouseevent-interface>
- CSSOM View Module §2, §6, §10, §12.1, §13.1 — <https://drafts.csswg.org/cssom-view/>
- CSS Values 4 §6.1.2.1, *large / small / dynamic viewport* —
  <https://drafts.csswg.org/css-values-4/#viewport-relative-lengths>
- HTML Standard §4.12.5, `canvas` in *placeholder* mode —
  <https://html.spec.whatwg.org/multipage/canvas.html#the-canvas-element>
- WICG **visual-viewport** (explainer di David Bokan, Chrome) — <https://github.com/WICG/visual-viewport>
- **bokand/URLBarSizing** — <https://github.com/bokand/URLBarSizing>
- **Blink Coordinate Spaces** — <https://www.chromium.org/developers/design-documents/blink-coordinate-spaces/>
- Chrome for Developers, *Aligned input events* (Chrome 60) — <https://developer.chrome.com/blog/aligning-input-events>
- Chrome for Developers, *URL bar resizing* (Chrome 56) — <https://developer.chrome.com/blog/url-bar-resizing>
- web.dev, *device-pixel-content-box* — <https://web.dev/articles/device-pixel-content-box>
- Samsung Developer, *DeX app testing guide* (`wm density 160`) — <https://developer.samsung.com/samsung-dex/testing.html>
- Samsung Developer, *Web Development Guide for DeX* — <https://developer.samsung.com/internet/android/web-development-guide-for-dex.html>
- chromestatus: `pointerrawupdate` <https://chromestatus.com/feature/6041426311774208> ·
  `getCoalescedEvents` <https://chromestatus.com/feature/5853451217010688> ·
  `getPredictedEvents` <https://chromestatus.com/feature/5765569655603200>
- blink-dev: *Intent to Ship: pointerrawupdate*
  <https://groups.google.com/a/chromium.org/g/blink-dev/c/mUW58VMIrTM/m/gIotA4HwBAAJ> ·
  *Visual Viewport / pinch zoom e le API*
  <https://groups.google.com/a/chromium.org/g/blink-dev/c/A12B1S4eGxY> ·
  *mouse on Android stops firing TouchEvents from M56*
  <https://groups.google.com/a/chromium.org/g/blink-dev/c/cNaFvMaYtNA>
- `public-pointer-events`, Mustaq Ahmed sull'hover senza evento di movimento (dic. 2024) —
  <https://lists.w3.org/Archives/Public/public-pointer-events/2024OctDec/0070.html>
- Matrice di prova di **Patrick H. Lauke** — <https://patrickhlauke.github.io/touch/tests/results/>

**Sorgente Chromium `[R]`** (branch `main`, via `raw.githubusercontent.com` e `chromium.googlesource.com`)

- `third_party/blink/renderer/core/input/pointer_event_manager.cc` — `SendMousePointerEvent`,
  `prevent_mouse_event_for_pointer_type_`, `SendMouseAndPointerBoundaryEvents`
- `third_party/blink/renderer/core/input/gesture_manager.cc` — `suppress_mouse_events_from_gestures_`
- `third_party/blink/renderer/core/input/mouse_event_manager.cc` — `movementX/Y`, soppressione da drag
- `third_party/blink/renderer/core/events/mouse_event.{h,cc}` — `std::floor(client_x_)`,
  `std::round(offset_x_)`, `ComputeRelativePosition` (`crbug.com/570666`)
- `third_party/blink/renderer/core/events/pointer_event.{h,cc}` — coordinate frazionarie
- `third_party/blink/renderer/core/frame/local_frame.cc` — `DevicePixelRatio() = DSF × LayoutZoomFactor`
- `third_party/blink/renderer/core/frame/visual_viewport.cc` — `browser_controls_adjustment_`
- `third_party/blink/renderer/core/dom/element.cc` — `GetBoundingClientRect`, `clientWidth`
- `third_party/blink/renderer/platform/geometry/layout_unit.h` — 1/64 px
- `third_party/blink/renderer/platform/widget/input/main_thread_event_queue.cc` —
  `IsRafAlignedEvent`, `has_pointerrawupdate_handlers_`
- `ui/android/java/src/org/chromium/ui/base/EventForwarder.java` — `onHoverEvent`, tool type
- `ui/android/java/src/org/chromium/ui/base/TouchDevice.java` — ⭐ *«Known gap: Samsung DeX …
  `isRealPointerDevice()` returns false»*, `crbug.com/502461774`
- `ui/base/pointer/pointer_device_android.cc` — `GetPrimaryHoverType()`
- `ui/android/java/src/org/chromium/ui/display/PhysicalDisplayAndroid.java` — `displayMetrics.density`
- `chrome/android/java/AndroidManifest.xml` — `android:configChanges=… density …`
- commit **`66ad18c093eb`** (18 feb 2022) — *«ZoomForDSF: Don't adjust movementX/Y by the device
  scale factor»*, `Bug: 1297149, 907309`
- commit **`d99d448`** (17 apr 2026) — *«Fix hover media query reporting hover:hover on touch-only
  Android devices»*, `Bug: 41445959`

**Deposito `[R]`**

- `src/pagina.html` — ancora `F4-INPUT-CLASSICO` (`cl_geometria`, `cl_su_mousemove`,
  `cl_su_mousedown`, `cl_manda_puntatore`), classe `Schermo` (`vista`, `componi`, `dipinta`),
  `misura_vista`, `accendi_worker`, ancora `F4-TOCCO` (`tocco_geometria`, `tocco_ingrandisci`)
- `src/input.c` — `input_puntatore()`, la riga di registro sulla regione ≠ tela
- `RCP.md` §7.3 (coordinate sulla tela), §6.2 (i fotogrammi in volo), §4.5 (la tela concessa)
- `DECISIONI.md` §5.0 (lo zoom e `devicePixelRatio`), §5-bis.0 (DeX è l'uso primario)
- `fasi/rapporti/F4-A7-pagina-classico.md` §9 · `fasi/rapporti/F5-desktop-vero.md`
