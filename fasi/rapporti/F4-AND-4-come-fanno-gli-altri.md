# F4-AND-4 — Come fanno gli altri: il mouse su schermi che non combaciano

Anello di studio, 14 agosto 2026. Marche: `[M]` misurato, `[R]` letto in un sorgente
altrui, `[S]` letto in una specifica, `[?]` ipotesi non verificata.

## Depositi letti (cloni in `/tmp/studio-f4/`, sola lettura)

| Progetto | Indirizzo | Commit letto |
|---|---|---|
| noVNC | `https://github.com/novnc/noVNC` | `7c36fabe599e053c5a81e98e091ac636f6c1e174` (6 giu 2026) `[R]` |
| Apache Guacamole | `https://github.com/apache/guacamole-client` | `5be18be1eeadc4cc544c737c54bd761261d2ad65` (10 ago 2026) `[R]` |
| xpra-html5 | `https://github.com/Xpra-org/xpra-html5` | `e06046fb2b02638d172c8a0c71d4ea010488c30a` (10 ago 2026) `[R]` |
| KasmVNC (client web) | `https://github.com/kasmtech/KasmVNC` → sottomodulo `https://github.com/kasmtech/noVNC` | `3c418e68e40f31508bf0b598499e6a3af9481d2c` (12 ago 2026) `[R]` |
| Chrome Remote Desktop | `https://chromium.googlesource.com/chromium/src` | `remoting/client/**` al tag `100.0.4896.60`; `remoting/proto`, `remoting/host` a `db27dca3` `[R]` |

Nota su Chrome Remote Desktop: il client **web** moderno non e' pubblico `[R]`
(`remoting/webapp/` non esiste piu' nell'albero attuale di Chromium: `git
sparse-checkout set remoting` a `db27dca3` mostra solo `base client codec host proto
protocol resources scripts signaling test tools`). E' pubblico invece il client
**nativo** Android/iOS (`remoting/client/ui/`, `remoting/client/input/`) fino a
Chromium 100, ed e' esattamente il codice che risolve il nostro problema su tablet.

---

## ⭐ La risposta corta

**La tua tesi va rovesciata.** Nessuno dei cinque progetti considera l'impaginazione
con le bande la strada *giusta*: e' la strada di *ripiego*. E — punto ancora piu'
importante — **nessuno dei tre grandi client web tiene conto delle bande facendo
aritmetica sull'offset.** Le bande esistono, ma stanno **fuori dall'elemento contro
cui si misura il mouse**, e quindi l'offset lo calcola il browser dentro
`getBoundingClientRect()` / `offsetLeft`. La formula di conversione resta a **un solo
stadio**: `(client − bordo_elemento) / scala`.

Le due strategie vere, in ordine di preferenza dei progetti:

1. **Chiedere al server di cambiare la misura del desktop remoto** perche' combaci con
   la finestra. E' il default di Guacamole `[R]`, di KasmVNC `[R]`, di xpra `[R]` e di
   Chrome Remote Desktop `[R]`. In questa strada **le bande spariscono del tutto** e la
   classe di difetti «puntatore altrove» sparisce con loro.
2. Se il server non sa ridimensionare: **scalare il disegno in CSS e lasciare che il
   contenitore centri l'elemento**, misurando il mouse contro l'elemento disegnato, mai
   contro il contenitore. Le bande sono lo sfondo del *genitore*, non pixel del disegno.

Chrome Remote Desktop fa una terza cosa, ancora piu' netta: **non impagina affatto**,
riempie (`max`, non `min`) e fa scorrere `[R]`.

---

## 1. noVNC

### La formula esatta

Due sole righe, in due file.

**`core/util/element.js:13-32`** `[R]` — da coordinate di finestra a coordinate
dell'elemento, con ritaglio ai bordi:

```js
export function clientToElement(x, y, elem) {
    const bounds = elem.getBoundingClientRect();
    ...
    pos.x = x - bounds.left;     // riga 22
    ...
}
```

**`core/display.js:175-187`** `[R]` — da coordinate dell'elemento a coordinate del
framebuffer:

```js
absX(x) { ... return toSigned32bit(x / this._scale + this._viewportLoc.x); }   // riga 179
absY(y) { ... return toSigned32bit(y / this._scale + this._viewportLoc.y); }   // riga 186
```

E il chiamante, **`core/rfb.js:1116`** e **`core/rfb.js:1225-1229`** `[R]`:

```js
let pos = clientToElement(ev.clientX, ev.clientY, this._canvas);   // riga 1116
...
RFB.messages.pointerEvent(this._sock, this._display.absX(x), this._display.absY(y), mask);  // riga 1228
```

Formula completa:

```
x_remoto = (ev.clientX − canvas.getBoundingClientRect().left) / scala + viewport.x
```

**Un solo stadio.** Nessun offset di bande, nessun `devicePixelRatio`.

### Dove finiscono le bande

⭐ **Non esistono dentro la tela.** `core/rfb.js:221-234` `[R]`:

```js
this._screen = document.createElement('div');
this._screen.style.display = 'flex';     // riga 222
this._screen.style.width = '100%';       // riga 223
this._screen.style.height = '100%';      // riga 224
this._screen.style.background = DEFAULT_BACKGROUND;   // riga 226
this._canvas = document.createElement('canvas');
this._canvas.style.margin = 'auto';      // riga 228
this._screen.appendChild(this._canvas);  // riga 234
```

La tela e' figlia flex con `margin: auto`; le bande sono lo **sfondo del div genitore**.
La tela ha esattamente la misura dell'immagine, perche' `_rescale` tocca **solo** lo
stile CSS, non il buffer — `core/display.js:456-472` `[R]`:

```js
_rescale(factor) {
    this._scale = factor;
    const vp = this._viewportLoc;
    const width  = factor * vp.w + 'px';   // riga 464
    const height = factor * vp.h + 'px';   // riga 465
    this._target.style.width  = width;
    this._target.style.height = height;
}
```

mentre il buffer resta `canvas.width = vp.w` (`core/display.js:161-162`) `[R]`.

Quindi `getBoundingClientRect().left` **contiene gia' l'offset della banda sinistra**:
il browser lo calcola, noVNC non lo scrive da nessuna parte.

La scala e' il classico «contain» — `core/display.js:432-452` `[R]`:

```js
const targetAspectRatio = containerWidth / containerHeight;
const fbAspectRatio = vp.w / vp.h;
if (fbAspectRatio >= targetAspectRatio) scaleRatio = containerWidth / vp.w;    // riga 445
else                                    scaleRatio = containerHeight / vp.h;  // riga 447
```

### `devicePixelRatio`

⭐ **Non entra mai nella conversione.** In tutto `core/` compare in **una sola riga**,
`core/util/browser.js:62` `[R]`:

```js
export let dragThreshold = 10 * (window.devicePixelRatio || 1);
```

cioe' solo per una soglia di trascinamento in pixel fisici. Motivo `[?]`: il buffer
della tela e' in pixel di framebuffer, lo stile e' in pixel CSS,
`getBoundingClientRect()` e' in pixel CSS — il rapporto si semplifica da solo.

### Android e tablet

`core/rfb.js:589-610` `[R]`: si registra **solo** su `mousedown`, `mouseup`,
`mousemove`, `click`, `contextmenu`, `wheel` e sui propri eventi sintetici
`gesturestart`/`gesturemove`/`gestureend`. **Nessun `pointerdown`, nessun
`pointerType`** — verificato con grep su tutto `core/`.

Il tocco passa da `core/input/gesturehandler.js`, che ascolta
`touchstart/touchmove/touchend/touchcancel` (righe 58-64) e fa **`e.preventDefault()`
su ogni evento** (riga 91) `[R]`. E' quello che impedisce ad Android di generare i
falsi `mousedown/mousemove` sintetici dopo il tocco. Il CSS mette `touch-action: none`
(`app/styles/base.css:45`) `[R]`.

Gli eventi sintetici portano `clientX/clientY` e finiscono nella **stessa**
`clientToElement` (`core/rfb.js:1296`, `1329`) `[R]` — una sola conversione per tutto.

### Ridimensionano il desktop remoto?

Si', e' una delle tre modalita'. `app/ui.js:187` `[R]`: `UI.initSetting('resize',
'off')` — il default di noVNC e' *non fare niente*. Le altre due, `app/ui.js:1180-1181`
`[R]`:

```js
UI.rfb.scaleViewport = UI.getSetting('resize') === 'scale';
UI.rfb.resizeSession = UI.getSetting('resize') === 'remote';
```

Sono **alternative**, mai insieme. In `remote`, `core/rfb.js:795-835` `[R]` manda
`setDesktopSize` con la misura del contenitore in **pixel CSS** (`_screenSize()` =
`this._screen.getBoundingClientRect()`, righe 838-841) — **senza** moltiplicare per
`devicePixelRatio`:

```js
const size = this._screenSize();
if (size.w === this._fbWidth && size.h === this._fbHeight) return;   // riga 823
RFB.messages.setDesktopSize(this._sock, Math.floor(size.w), Math.floor(size.h), ...);  // riga 829
```

Con `resize=remote` **le bande non ci sono**, perche' il desktop remoto ha esattamente
il rapporto della finestra.

---

## 2. Apache Guacamole

### La formula esatta

**`guacamole-common-js/.../Position.js:66-90`** `[R]`:

```js
this.fromClientPosition = function fromClientPosition(element, clientX, clientY) {
    this.x = clientX - element.offsetLeft;        // riga 68
    this.y = clientY - element.offsetTop;         // riga 69
    var parent = element.offsetParent;
    while (parent && !(parent === document.body)) {
        this.x -= parent.offsetLeft - parent.scrollLeft;   // riga 74
        this.y -= parent.offsetTop  - parent.scrollTop;    // riga 75
        parent = parent.offsetParent;
    }
    ...
};
```

⭐ Guacamole **non usa `getBoundingClientRect()`**: risale a mano la catena
`offsetParent`, sottraendo anche gli **scroll** dei genitori. Poi la scala si toglie in
**`Client.js:386-417`** `[R]`:

```js
this.sendMouseState = function sendMouseState(mouseState, applyDisplayScale) {
    var x = mouseState.x;  var y = mouseState.y;
    if (applyDisplayScale) {
        x /= display.getScale();     // riga 397
        y /= display.getScale();     // riga 398
    }
    ...
    tunnel.sendMessage("mouse", Math.floor(x), Math.floor(y), buttonMask);   // riga 416
};
```

e il chiamante passa sempre `true` — `guacamole/src/main/frontend/src/app/client/directives/guacClient.js:262` e `:326` `[R]`: `client.sendMouseState(event.state, true);`

Formula completa:

```
x_remoto = (clientX − offsetLeft_cumulativo + scrollLeft_cumulativo) / display.getScale()
```

Di nuovo: **un solo stadio, nessun offset di bande scritto a mano.**

### Dove finiscono le bande

Stessa architettura di noVNC, con tecnica piu' vecchia (tabella invece di flex) —
`guacamole/src/main/frontend/src/app/client/styles/display.css:38-57` `[R]`:

```css
div.displayOuter  { height: 100%; width: 100%; position: absolute; display: table; }
div.displayMiddle { width: 100%; height: 100%; display: table-cell;
                    vertical-align: middle; text-align: center; }
div.display       { display: inline-block; }
```

`div.display` e' **`inline-block`**: si stringe attorno al contenuto, cioe' al `bounds`
che Guacamole dimensiona a `displayWidth*displayScale` — `Display.js:1653-1655` `[R]`:

```js
bounds.style.width  = (displayWidth*displayScale) + "px";
bounds.style.height = (displayHeight*displayScale) + "px";
```

La scala e' una `transform: scale()` con **origine 0,0** — `Display.js:49-55` e
`:1641-1651` `[R]`:

```js
display.style.transformOrigin = "0 0";        // righe 50-55
display.style.transform = "scale(" + scale + "," + scale + ")";   // righe 1643-1649
```

L'origine a `0 0` e' cio' che rende **legittimo** usare `offsetLeft` (che ignora le
trasformate): con origine in alto a sinistra la posizione visiva del vertice coincide
con quella di impaginazione. Le bande le fanno `text-align: center` +
`vertical-align: middle`, cioe' **il contenitore**, e finiscono dentro `offsetLeft`.

### `devicePixelRatio`

⭐ Qui c'e' la differenza sostanziale con noVNC: Guacamole **usa il DPR, ma dall'altra
parte** — non per convertire il mouse, ma per **chiedere un desktop remoto piu' fitto**.

`ManagedClient.js:333-347` `[R]`, alla connessione:

```js
const pixel_density = $window.devicePixelRatio || 1;
const optimal_dpi    = pixel_density * 96;
const optimal_width  = width  * pixel_density;
const optimal_height = height * pixel_density;
...
+ "&GUAC_WIDTH="  + Math.floor(optimal_width)
+ "&GUAC_HEIGHT=" + Math.floor(optimal_height)
+ "&GUAC_DPI="    + Math.floor(optimal_dpi)
```

`guacClient.js:504-523` `[R]`, ad ogni ridimensionamento:

```js
const pixelDensity = $window.devicePixelRatio || 1;
const width  = main.offsetWidth  * pixelDensity;    // riga 513
const height = main.offsetHeight * pixelDensity;    // riga 514
if (display.getWidth() !== width || display.getHeight() !== height)
    client.sendSize(width, height);                 // riga 517
```

Conseguenza aritmetica `[?]` (mia deduzione dal codice, non misurata): il desktop
remoto diventa `W·dpr × H·dpr`, e la scala di adattamento e'
`minScale = min(main.offsetWidth/display.getWidth(), main.offsetHeight/display.getHeight())`
(`guacClient.js:151-154`) `[R]` `= 1/dpr` in entrambe le dimensioni. Rapporti identici
→ **`minScale` uguale nei due assi → nessuna banda**. Il `/getScale()` del mouse
rimoltiplica per `dpr` e riporta ai pixel veri del desktop. Il cerchio si chiude.

### Android e tablet

Nessun `pointerType`, nessun `PointerEvent` in tutto `guacamole-common-js` — verificato
con grep. Il mouse ascolta `contextmenu`, `mousemove`, `mousedown`, `mouseup`,
`mouseout`, `selectstart` (`Mouse.js:122-193`) `[R]`; il tocco ha oggetti dedicati
(`Guacamole.Touch` su `touchstart/touchmove/touchend`, `Touch.js:164-224`;
`Guacamole.Mouse.Touchscreen` e `Guacamole.Mouse.Touchpad`) `[R]`.

⭐ La distinzione mouse/dito e' fatta con un **contatore di eventi da ignorare**, non
con `pointerType` — `Mouse.js:195-200` `[R]`:

```js
// Ignore all pending mouse events when touch events are the apparent source
function ignorePendingMouseEvents() { ignore_mouse = guac_mouse.touchMouseThreshold; }
element.addEventListener("touchmove",  ignorePendingMouseEvents, false);
element.addEventListener("touchstart", ignorePendingMouseEvents, false);
element.addEventListener("touchend",   ignorePendingMouseEvents, false);
```

con `this.touchMouseThreshold = 3` (`Mouse.js:65`) `[R]`: dopo un tocco, i **tre**
eventi mouse successivi vengono scartati come sintetici.

La scelta fra tocco diretto, mouse assoluto emulato e touchpad relativo e' in
`guacClient.js:440-463` `[R]`, ed e' una preferenza dell'utente, non del dispositivo.

`DEFAULT_CONTACT_RADIUS = Math.floor(16 * window.devicePixelRatio)` (`Touch.js:70`) `[R]`
— DPR di nuovo solo per una soglia fisica.

### Ridimensionano il desktop remoto?

⭐ **Si', ed e' la strada principale, non un'opzione.** Guacamole manda la misura
**prima ancora di connettersi** (`GUAC_WIDTH`/`GUAC_HEIGHT` nella stringa di
connessione, `ManagedClient.js:345-346`) `[R]` e poi ad ogni resize
(`client.sendSize`, `guacClient.js:517`) `[R]`. La `scale()` di `Guacamole.Display`
serve allo **zoom** dell'utente (`minScale`/`maxScale`, `maxScale` fino a 3×,
`guacClient.js:157`) `[R]`, con barre di scorrimento quando si supera il minimo
(`guacClient.js:472-478`) `[R]`. Non e' un meccanismo di impaginazione.

---

## 3. xpra (client HTML5)

xpra e' il caso piu' istruttivo perche' e' quello che **rifiuta esplicitamente** sia le
bande sia la scalatura.

### La formula esatta

**`html5/js/Client.js:1651-1705`** `[R]`:

```js
getMouse(e) {
    const windowIsLocked = Boolean(document.pointerLockElement);
    let mx = e.clientX + jQuery(document).scrollLeft();   // riga 1655
    let my = e.clientY + jQuery(document).scrollTop();    // riga 1656
    if (windowIsLocked) { mx = e.movementX; my = e.movementY; }
    if (this.scale !== 1) {
        mx = Math.round(mx * this.scale);                 // riga 1664
        my = Math.round(my * this.scale);                 // riga 1665
    }
    ...
}
```

⭐ **Coordinate di pagina, non di elemento.** Non c'e' nessun
`getBoundingClientRect()`, nessun `offsetLeft`, nessuna sottrazione del contenitore.
Funziona perche' **la pagina *e'* lo schermo remoto**: `index.html:179` `[R]`

```html
<div id="screen" style="width: 100%; height: 100%">
```

dentro un `body` con `margin: 0; padding: 0; overflow: hidden`
(`html5/css/client.css:1-8`) `[R]`. Il `<div id="screen">` sta a (0,0) di pagina.

L'offset della finestra remota si toglie **dopo**, e solo come *coordinate relative
aggiuntive* — `Client.js:1742-1750` `[R]`:

```js
if (win) {
    wid = win.wid;
    const pos = win.get_internal_geometry();
    coords.push(Math.round(mouse.x - pos.x));   // riga 1746
    coords.push(Math.round(mouse.y - pos.y));   // riga 1747
    e.preventDefault();
}
this.send([PACKET_TYPES.pointer_position, wid, coords, modifiers, buttons]);   // riga 1750
```

xpra manda **quattro** numeri: assoluti *e* relativi. E `pos.x/pos.y` sono la stessa
geometria che il client ha gia' **dichiarato al server** con `geometry_cb`
(`Window.js:1050`) `[R]`. Non e' aritmetica sulle bande: e' la posizione della finestra
sullo schermo virtuale, nota a entrambe le parti.

### Bande: quando ci sono e come le gestiscono

xpra impagina davvero, in modalita' `server_is_desktop`, e lo fa **spostando la
finestra**, non ritagliando il disegno — `Window.js:1039-1057` `[R]`:

```js
recenter(force_update_geometry) {
    x = Math.round((this.client.desktop_width  - this.w) / 2);   // riga 1043
    y = Math.round((this.client.desktop_height - this.h) / 2);   // riga 1044
    ...
    this.updateCSSGeometry();
    this.geometry_cb(this);      // riga 1050 — il server viene AVVISATO
}
```

E c'e' un avviso esplicito quando l'impaginazione fallisce (`Window.js:1054-1056`) `[R]`:

```js
if (this.x < 0 || this.y < 0) {
    this.warn("window does not fit in canvas, offsets: ", x, y);
}
```

Ma la prima scelta e' un'altra — `Window.js:1059-1106` `[R]`:

```js
match_screen_size() {
    const maxw = this.client.desktop_width;
    const maxh = this.client.desktop_height;
    if (this.client.server_resize_exact) {
        neww = maxw;  newh = maxh;
        this.log("resizing to exact size:", neww, newh);      // righe 1064-1067
    } else {
        // scegli fra i modi disponibili il piu' grande che CI STA
        if (w <= maxw && h <= maxh && w * h > best) { ... }   // riga 1082
    }
    this.w = neww;  this.h = newh;
    this.recenter(true);   // riga 1105
}
```

Cioe': **se il server sa ridimensionare all'esatto, si prende tutta la finestra e le
bande non nascono**. Le bande esistono solo quando il server ha un elenco fisso di
modi video.

E il server viene informato ad ogni resize del browser — `Client.js:762-781` `[R]`:

```js
this.desktop_width  = this.container.clientWidth;    // riga 771
this.desktop_height = this.container.clientHeight;   // riga 772
const packet = [PACKET_TYPES.configure_display, {
    "desktop-size": [this.desktop_width, this.desktop_height],
    "monitors": this._get_monitors(),
    "dpi": {"x": dpi, "y": dpi},
    ...
}];
this.send(packet);
```

### `devicePixelRatio`

⭐ **Non lo usano per le coordinate, e lo dicono nel codice.** `Client.js:776` `[R]`,
riga commentata di proposito:

```js
// "desktop-size-unscaled": [this.desktop_width, this.desktop_height],  - we don't do desktop scaling
```

Tutto e' in pixel CSS: `canvas.width = this.w` (`Window.js:515-519`) `[R]` con `this.w`
preso da `container.clientWidth`. Il DPR compare in due punti soli:

- `Window.js:428` `[R]`: `const mult = 20 * (window.devicePixelRatio || 1);` — moltiplicatore di scorrimento;
- `Window.js:1249-1256` `[R]`: `canvas.width = Math.round(w * window.devicePixelRatio)` — **solo** per l'immagine del cursore.

Il DPI mandato al server viene misurato con un **div di prova nella pagina**, non da
`devicePixelRatio` — `Client.js:1212-1214` `[R]`:

```js
const dpi_div = document.querySelector("#dpi");
if (dpi_div && dpi_div.offsetWidth > 0 && dpi_div.offsetHeight > 0)
    return Math.round((dpi_div.offsetWidth + dpi_div.offsetHeight) / 2);
```

`this.scale` (`Client.js:138`, default `1`) e' uno zoom dell'utente, applicato con
`transform: scale(1/scale)` sul contenitore ingrandito (`Client.js:467-472`) `[R]` — e
per questo la formula del mouse lo rimoltiplica.

### Android e tablet

⭐ xpra e' **l'unico dei tre** che tocca `pointerType`, e lo fa **solo per
riconoscere il gesto, mai per le coordinate** — `Window.js:408-437` `[R]`:

```js
register_canvas_pointer_events(canvas) {
    if (!window.PointerEvent) return;                       // riga 409
    canvas.addEventListener("pointerdown", (event_) => {
        if (event_.pointerType === "touch") {               // riga 414
            this.pointer_down = event_.pointerId;
            this.pointer_last_x = event_.offsetX;
            this.pointer_last_y = event_.offsetY;
        }
    });
    canvas.addEventListener("mousemove", (event_) => {
        if (this.pointer_down === event_.pointerId) {
            const dx = event_.offsetX - this.pointer_last_x;
            ...
            const mult = 20 * (window.devicePixelRatio || 1);
            event_.wheelDeltaX = Math.round(dx * mult);
            return this.mouse_scroll_cb(event_, this);       // riga 431
        }
    });
```

Cioe': `pointerType === "touch"` serve a trasformare il **trascinamento col dito in
rotellina di scorrimento**. Le coordinate continuano a passare dai `mousedown /
mouseup / mousemove` di jQuery (`Window.js:395-406`) `[R]`, cioe' dagli **eventi mouse
sintetici che Android genera dal tocco**.

---

## 4. KasmVNC — la prova piu' vicina al nostro caso

KasmVNC e' una biforcazione di noVNC (`kasmweb` e' un sottomodulo verso
`github.com/kasmtech/noVNC`) `[R]`. La `clientToElement` e' identica
(`core/util/element.js:13-30`) `[R]`, piu' una correzione per gli schermi multipli
(righe 32-42).

### Il default e' il ridimensionamento remoto

`app/ui.js:367` e `:377` `[R]`:

```js
UI.initSetting('resize', 'off');      // riga 367 — dentro Kasm Workspaces (VDI)
...
UI.initSetting('resize', 'remote');   // riga 377 — uso autonomo
```

⭐ Il noVNC originale ha `off` come unico default (`app/ui.js:187`) `[R]`. **Kasm lo ha
cambiato in `remote`**: quando il client web viene usato da solo, la prima mossa e'
chiedere al server un desktop della misura della finestra.

### E se il rapporto non combacia lo stesso

`core/display.js:287-358` `[R]`, `getScreenSize()`:

```js
let parentNodeSize = this._target.parentNode.getBoundingClientRect();       // riga 298
this._screens[i].containerHeight = Math.floor(parentNodeSize.height / 2) * 2;  // riga 300
this._screens[i].containerWidth  = Math.floor(parentNodeSize.width  / 2) * 2;  // riga 301
this._screens[i].pixelRatio = window.devicePixelRatio;                      // riga 302
...
else if (hiDpi) {
    width  = Math.floor(width  * this._screens[i].pixelRatio);   // riga 334
    height = Math.floor(height * this._screens[i].pixelRatio);   // riga 335
    scale  = 1 / this._screens[i].pixelRatio;                    // riga 336
}
...
let clientServerRatioH = this._screens[i].containerHeight / height;   // riga 351
let clientServerRatioW = this._screens[i].containerWidth  / width;    // riga 352
...
this._screens[i].scale = Math.min(clientServerRatioH, clientServerRatioW);   // riga 358
```

Tre cose da notare:

1. La misura chiesta al server e' **arrotondata a numero pari** (`Math.floor(x/2)*2`,
   righe 300-301) — `[?]` verosimilmente per i codificatori video che vogliono
   dimensioni pari. E' un vincolo che *da solo* puo' produrre uno scarto di 1 pixel: e'
   il motivo per cui una scala residua serve comunque.
2. `hiDpi` (righe 333-337) e' il trattamento esplicito del DPR: si chiede al server un
   desktop `dpr` volte piu' fitto e si ricompensa con `scale = 1/dpr`. **Stessa idea di
   Guacamole.**
3. La scala residua e' `min(...)` — il classico «contain», con bande — ed entra in
   `absX/absY` esattamente come in noVNC, `core/display.js:605-617` `[R]`:
   `return toSigned32bit(x / this._scale + this._screens[0].x);`

`_screens[0].x` qui e' l'origine dello schermo nello **spazio del desktop remoto**
(multi-monitor), non un offset di bande sul vetro.

### Android

`core/rfb.js:1389-1391` `[R]`: solo `mousedown/mouseup/mousemove`. `pointerlockchange`
e `pointerlockerror` (righe 1400-1401) riguardano il blocco del cursore, non
`PointerEvent`. **Nessun `pointerType` in tutto `core/rfb.js`** — verificato con grep.

---

## 5. Chrome Remote Desktop

Il client web moderno non e' pubblico `[R]`. Il client nativo Android/iOS lo e', e fa
la cosa piu' radicale di tutte.

### ⭐ Non impagina: riempie

`remoting/client/ui/desktop_viewport.cc:125-155` (tag `100.0.4896.60`) `[R]`:

```cpp
void DesktopViewport::ResizeToFit() {
  ...
  // resize the desktop such that it fits the viewport in one dimension.
  ViewMatrix::Vector2D safe_area_size = GetSurfaceSafeAreaSize();
  float scale = std::max(safe_area_size.x / desktop_size_.x,
                         safe_area_size.y / desktop_size_.y);      // righe 149-150
  desktop_to_surface_transform_.SetScale(scale);
  desktop_to_surface_transform_.SetOffset({safe_insets_.left, safe_insets_.top});
  UpdateViewport();
}
```

`std::max`, non `std::min`. E' **«cover», non «contain»**: il desktop remoto trabocca in
una dimensione e l'utente fa scorrere. **Le bande non nascono mai.** Il commento a
disegni sopra (righe 130-146) lo dice a lettere: «resize the desktop such that it fits
the viewport in **one** dimension».

Il `min` esiste, ma solo come rete di sicurezza quando il desktop e' piu' piccolo del
riquadro in **entrambe** le direzioni — `desktop_viewport.cc:176-194` `[R]`:

```cpp
if (desktop_size_on_surface_.x < safe_area_size.x &&
    desktop_size_on_surface_.y < safe_area_size.y) {
  float scale = std::min(safe_area_size.x / desktop_size_.x,
                         safe_area_size.y / desktop_size_.y);      // righe 191-192
  desktop_to_surface_transform_.SetScale(scale);
}
```

### La formula esatta

Una trasformazione affine **con offset**, e la sua inversa. `remoting/client/ui/view_matrix.cc:16-20` e `:57-60` `[R]`:

```cpp
ViewMatrix::Point ViewMatrix::MapPoint(const Point& point) const {
  float x = scale_ * point.x + offset_.x;
  float y = scale_ * point.y + offset_.y;
  return {x, y};
}
...
ViewMatrix ViewMatrix::Invert() const {
  return ViewMatrix(1.f / scale_, {-offset_.x / scale_, -offset_.y / scale_});
}
```

e l'uso, `remoting/client/input/direct_touch_input_strategy.cc:46-56` `[R]`:

```cpp
bool DirectTouchInputStrategy::TrackTouchInput(
    const ViewMatrix::Point& touch_point, const DesktopViewport& viewport) {
  ViewMatrix::Point new_position =
      viewport.GetTransformation().Invert().MapPoint(touch_point);   // riga 50
  if (!viewport.IsPointWithinDesktopBounds(new_position)) return false;
  cursor_position_ = new_position;
  return true;
}
```

Formula:

```
x_remoto = (x_superficie − offset.x) / scala
```

⭐ Questo e' **l'unico dei cinque progetti che tiene l'offset in una variabile propria**
— e non e' un offset di bande: e' la posizione di scorrimento del riquadro (piu' le
`safe_insets` di tacca/barra di stato). L'offset e' centrato in `UpdateViewport()`
(`desktop_viewport.cc:196-235`, con `GetViewportCenterBounds()` alle righe 237-265) `[R]`,
non calcolato come `(contenitore − immagine)/2`.

### E chiede comunque al server di cambiare misura

`remoting/proto/control.proto:21-38` `[R]`:

```protobuf
message ClientResolution {
  // Width and height of the client in device pixels.
  optional int32 width_pixels = 1;
  optional int32 height_pixels = 2;
  ...
  // Horizontal and vertical DPI of the screen. If either of these is zero or
  // unset, the corresponding DPI should be assumed to be 96 (Windows' default)
  optional int32 x_dpi = 5;
  optional int32 y_dpi = 6;
  ...
}
```

⭐ «**in device pixels**» e un **DPI esplicito**: identico a `GUAC_WIDTH`/`GUAC_DPI` di
Guacamole. Lato host, `remoting/host/resizing_host_observer.cc:33-75` `[R]` sceglie il
modo video migliore pesando **anche il rapporto d'aspetto**:

```cpp
float preferred_aspect_ratio = ... ;                     // righe 65-67
if (candidate_aspect_ratio > preferred_aspect_ratio)
  aspect_ratio_goodness_ = preferred_aspect_ratio / candidate_aspect_ratio;   // riga 69
else
  aspect_ratio_goodness_ = candidate_aspect_ratio / preferred_aspect_ratio;   // riga 71
```

cioe' l'host **cerca attivamente di far combaciare i rapporti** per non lasciare bande.

---

## ⭐ Tabella di confronto

| | noVNC | Guacamole | xpra | KasmVNC | Chrome RD |
|---|---|---|---|---|---|
| Elemento contro cui si misura | la **tela** | il **div display** | la **pagina** | la **tela** | la superficie |
| Come si trova il bordo | `getBoundingClientRect()` | catena `offsetParent` | (0,0) di pagina | `getBoundingClientRect()` | offset nella matrice |
| Stadi di conversione | **1** | **1** | **1** | **1** | **1** |
| Offset delle bande scritto a mano | **no** | **no** | **no** (posizione finestra) | **no** | **no** (scorrimento) |
| DPR nelle coordinate | **no** | **no** | **no** | **no** | (pixel dispositivo nativi) |
| DPR per chiedere il desktop | no | **si', ×dpr + DPI** | no (DPI misurato) | **si', `hiDpi`** | **si', `width_pixels`+`x_dpi`** |
| Chiede il resize al server | opzione, default off | **sempre, anche pre-connessione** | **sempre** | **default `remote`** | **sempre** |
| Impaginazione con bande | ripiego (`min`) | zoom manuale | ripiego, con avviso | ripiego (`min`) | **mai** (`max` + scorrimento) |
| Eventi Android | `mouse*` + `touch*` propri | `mouse*` + `touch*` propri | `mouse*` (+`pointer*` per il gesto) | `mouse*` + `touch*` propri | tocco nativo |
| `pointerType` | **mai** | **mai** | **solo per il gesto** | **mai** | — |

---

## ⭐ Che cosa consiglio a noi

Ho guardato la nostra conversione. `src/pagina.html:3705` `[R]`
(`/home/nicfio/Documenti/REMOTIX_V2/src/pagina.html`):

```js
cl_px = ((ev.clientX - g.r.left) / g.vx - g.bx0) / g.sx;
```

con, da `src/pagina.html:3379-3386` `[R]`:

```js
let bx0 = 0, by0 = 0, sx = tela.width / t[0], sy = tela.height / t[1];
if (...) { bx0 = d.x; by0 = d.y; sx = d.l / d.fotogramma[0]; ... }
const vx = tela.width ? r.width / tela.width : 0;
```

Sono **tre stadi in cascata**: vetro→tela (`vx`), bande **dentro** la tela (`bx0`),
tela→desktop (`sx`). Nessuno dei cinque progetti ne ha piu' di uno. `bx0` esiste perche'
noi **disegniamo le bande dentro il buffer della tela**: e' quello il difetto di
progetto, non la formula.

Tre mosse, in ordine di resa.

**1. Togliere le bande dal buffer della tela.** E' la mossa che elimina `bx0` e `vx`
insieme. La tela va dimensionata *esattamente* come l'immagine del desktop
(`canvas.width = fb.w`), la scala va messa **solo in CSS**
(`tela.style.width = scala*fb.w + 'px'`, noVNC `core/display.js:464-470` `[R]`), e le
bande devono diventare **lo sfondo del genitore**, con la tela centrata da
`display:flex` + `margin:auto` (noVNC `core/rfb.js:222-228` `[R]`) o da `inline-block`
+ `text-align:center` (Guacamole `display.css:47-57` `[R]`). Allora
`tela.getBoundingClientRect().left` **contiene gia'** l'offset della banda, e la formula
si riduce a:

```
x_remoto = (ev.clientX − tela.getBoundingClientRect().left) / scala
```

Costo `[?]`: bisogna verificare come il nostro riquadro video/tela viene riempito dal
decodificatore — se il flusso arriva gia' impaginato dal server, il problema non e' in
pagina ma nel produttore.

**2. Chiedere al server la misura giusta — e' la strada che *evita la classe di
difetti*, e la tua tesi qui va rovesciata.** Quattro progetti su cinque lo fanno di
default, non come opzione: Guacamole prima ancora di connettersi
(`ManagedClient.js:345-346`) `[R]`, KasmVNC come default fuori dal VDI (`app/ui.js:377`)
`[R]`, xpra ad ogni resize (`Client.js:774-781`) `[R]`, Chrome RD nel protocollo stesso
(`control.proto:21-24`) `[R]`. Se REMOTIX parla con `gnome-remote-desktop`/Mutter, la
domanda concreta e' se possiamo cambiare la modalita' del monitor virtuale a
2560×926 — allora bande zero, scala 1, e la formula diventa una sottrazione. Chi sceglie
il modo dovrebbe pesare **il rapporto d'aspetto**, come fa
`resizing_host_observer.cc:65-71` `[R]`, non solo l'area.

**3. `devicePixelRatio`: toglilo dalla conversione, mettilo nella richiesta.** ⭐ E'
l'insegnamento piu' netto e piu' controintuitivo. Nessuno dei cinque moltiplica le
coordinate del mouse per il DPR — noVNC lo usa in **una riga sola** in tutto `core/`
(`core/util/browser.js:62`, per una soglia) `[R]`, xpra in due (rotellina e cursore)
`[R]`. Chi lo usa davvero (Guacamole `guacClient.js:512-514`, KasmVNC
`core/display.js:333-337`, Chrome RD `control.proto:22-23`) `[R]` lo usa **per chiedere
un desktop remoto piu' fitto**, e poi lo ricompensa con `scale = 1/dpr` — cosicche'
nella conversione il DPR si semplifica di nuovo e non compare. Se nella nostra pagina il
DPR compare nella catena delle coordinate, e' un sospettato immediato: su DeX
`devicePixelRatio` non e' intero e non e' stabile fra finestra affiancata e schermo
intero `[?]`.

**4. Se le bande devono restare** (per esempio perche' il flusso arriva gia' impaginato):
allora la lezione di xpra e di Chrome RD e' che l'offset **non va ricalcolato in pagina**
come `(contenitore − immagine)/2`, ma **tenuto in una sola variabile, prodotta dallo
stesso codice che disegna**, e usata invertendo la stessa affine
(`ViewMatrix::Invert()`, `view_matrix.cc:57-60`) `[R]`. Due formule scritte in due punti
diversi — una per disegnare, una per convertire — sono la definizione del difetto
«puntatore altrove»: basta che una arrotondi diversamente. Con `Math.floor(x/2)*2` di
Kasm (`core/display.js:300-301`) `[R]` a ricordarci che gli arrotondamenti esistono.

**5. Android: non passare a `pointer*` per le coordinate.** Quattro progetti su cinque
non toccano `PointerEvent`. xpra lo usa **solo** per `pointerType === "touch"` e **solo**
per classificare un gesto (`Window.js:412-431`) `[R]`. La disciplina che conta e' un'altra:
`touch-action: none` in CSS (noVNC `app/styles/base.css:45`) `[R]` piu'
`preventDefault()` su **ogni** evento di tocco (noVNC `gesturehandler.js:91`) `[R]`,
oppure il contatore di Guacamole che scarta i 3 eventi mouse sintetici successivi a un
tocco (`Mouse.js:65`, `:195-200`) `[R]`. Su DeX c'e' un puntatore vero **e** un dito: e'
esattamente il caso in cui `pointerType` **potrebbe** valere la pena `[?]` — ma per
scegliere il *comportamento*, non per calcolare le coordinate.

---

## Che cosa **non** ho verificato

- Non ho misurato nulla su DeX ne' fatto girare i client studiati: tutte le affermazioni
  su di loro sono `[R]` da codice, non `[M]`.
- Il client **web** di Chrome Remote Desktop resta chiuso: quanto detto vale per il
  client nativo Android/iOS e per il protocollo `[R]`.
- La catena aritmetica di Guacamole (`scale = 1/dpr` → nessuna banda) e' una mia
  deduzione dal codice, marcata `[?]`: non l'ho eseguita.
- Non ho letto il lato server di REMOTIX per sapere **se** possiamo chiedere a Mutter un
  monitor virtuale 2560×926. E' la domanda che decide fra la mossa 1 e la mossa 2, e va
  posta a chi conosce `mutter.c`.
