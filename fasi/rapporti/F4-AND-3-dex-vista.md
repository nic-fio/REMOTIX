# F4-AND-3 — La vista, la densità e la finestra su Samsung DeX

*Anello di studio, 14 agosto 2026. Mandato: «prova a smentirmi» su
`vista = 2560×926`.*

---

## 0. Il verdetto, in tre righe

| L'affermazione del mandato | Verdetto | La prova |
|---|---|---|
| «**2560×926 è una misura corretta** di una finestra Chrome su DeX» | ✅ **REGGE** — e si riproduce al pixel | `[M]` 13 ago 2026, impronta verbatim del DeX dell'utente: `finestra 772` CSS × `dpr 1,2000000476837158` = **926,4 → 926** |
| «le **bande nere laterali sono giuste**» | ✅ **REGGE**, ed era già misurato | `componi()` dà scala 0,857 · dipinto 1646×926 · **914 px di nero**. `fasi/02-primo-fotogramma.md` riga 281 aveva già scritto *«912 px di nero, tela dipinta all'86 %»* per la stessa finestra |
| ⛔ «su un **monitor 2560×1440**, e i **514 px mancanti** in altezza» | ⛔ **CADE** | Il monitor del DeX è **2560×1080**, 21:9. I px mancanti sono **154 fisici** (128 CSS), non 514 |

⭐ **E ci sono due numeri da portarsi via, che il mandato non chiedeva.**

1. A **2560×926** il desktop remoto 1920×1080 viene **rimpicciolito all'85,7 %**:
   **non è 1:1**, e non lo diventa allargando la finestra — mancano 154 px in
   **altezza**, e in larghezza ne avanzano 640. Diventerebbe 1:1 esatto a
   2560×**1080**. ⚠ Che lo schermo intero su DeX ce li dia tutti e 154 è `[?]`,
   e §3.5 dà motivo di dubitarne. **Vedi §7.**
2. ⛔ **La formula che produce quel 2560×926 è giusta per fortuna, non per
   costruzione.** `[R]` `clientWidth × devicePixelRatio` è il **viewport di
   layout** in pixel fisici, non il vetro: coincidono solo se il meta viewport è
   in vigore. `[M]` **Sullo stesso telefono, nove minuti dopo, fuori dal dock,
   la stessa formula dà 2754 px su un vetro che ne ha 1080** — ⭐ **× 2,55**.
   **Vedi §2.**

---

## 1. ⭐ La prova: l'impronta verbatim del DeX, e la catena aritmetica che chiude

⛔ **Non l'ho dedotta: era già nel deposito, e nessuno l'aveva letta per questa
domanda.** `banchi/02-giudizio-dispositivo.py` righe 766-814 conserva **verbatim**
due impronte raccolte dall'utente il 13 agosto 2026, a nove minuti di distanza,
**dallo stesso telefono** — la prima **in DeX**, la seconda **tolta dal dock**.

```
IMPRONTA_DEX_VERA          2026-08-13T05:42:51.934Z          [R] riga 769-788
  ua_stringa          "Mozilla/5.0 (X11; Linux x86_64) … Chrome/151.0.0.0 …"
  piattaforma_legacy  "Linux armv81"
  gpu.resa            "ANGLE (Qualcomm, Adreno (TM) 740, OpenGL ES 3.2)"
  schermo   l 2560 · a 1080 · dpr 1.2000000476837158 · disponibile 2560×1080
  finestra  l 2133 · a  772

IMPRONTA_MANO_TRAVESTITA   2026-08-13T05:51:44.515Z          [R] riga 795-814
  (stesso silicio, stesso UA, «richiedi sito desktop» ancora acceso)
  schermo   l  384 · a  832 · dpr 3.375000238418579
  finestra  l  816 · a 1476
```

### 1.1 Il conto che riproduce 2560×926 al pixel

`misura_vista()` (`src/pagina.html` righe 1152-1161) è
`[round(clientWidth·dpr), round(clientHeight·dpr)]`. Sull'impronta DeX:

```
2133 × 1,2000000476837158 = 2559,600…  → round → 2560   `[M]`
 772 × 1,2000000476837158 =  926,400…  → round →  926   `[M]`
```

⭐ **926 non è un numero da spiegare: è `772 × 1,2` arrotondato.** La misura del
14 agosto è la stessa finestra di quella del 13 agosto, e la sua altezza è
`innerHeight = 772` pixel CSS.

⚠ **Una precisazione che rende la prova più forte, non più debole.** La sonda del
13 agosto registra `innerWidth/innerHeight`; `misura_vista()` legge
`clientWidth/clientHeight`. Su Chrome per Android **le due NON coincidono in
generale** — `[R]` `innerHeight` esce da `MainFrameSize()`, cioè dal viewport
**grande** («come se la barra degli indirizzi fosse sempre nascosta»), mentre
`clientHeight` esce da `GetPageScaleConstraintsSet().GetLayoutSize()`, cioè dal
**riquadro contenitore iniziale decurtato dell'altezza dei browser controls**
(`WebViewImpl::UpdateICBAndResizeViewport()`,
`third_party/blink/renderer/core/exported/web_view_impl.cc`), e `[S]` Chrome lo
documenta: *«the ICB will not resize when the URL bar is hidden […] as if the URL
bar were always showing»* (<https://developer.chrome.com/blog/url-bar-resizing>).

⇒ ⭐ **E il fatto che `innerHeight × dpr` dia ESATTAMENTE il numero che
`misura_vista()` ha prodotto (926) è esso stesso una misura**: dice che su DeX
`clientHeight == innerHeight`, cioè che **in una finestra DeX la barra degli
indirizzi non si ritrae** e i browser controls non decurtano niente. ⚠ Su un
telefono in mano le due divergono, e lì `misura_vista()` prenderebbe la più
piccola.

⚠ **Stessa cosa in larghezza, e chiude un altro dubbio.** `clientWidth` esclude
la barra di scorrimento, `innerWidth` la include: se su DeX la barra occupasse
spazio, `clientWidth` varrebbe 2118 e la vista **2542**, non 2560. `[M]` La
vista misurata è **2560** ⇒ **su Android la barra di scorrimento è in
sovrimpressione e non toglie larghezza**. ⭐ Conseguenza per il prodotto: la riga
`html { overflow-y: scroll }` di `src/pagina.html` riga 94 — la cura del difetto
dei 15 px del 13 agosto — **su DeX non fa nulla, e non serve**. Non è un difetto;
è una cura che vale su un solo palco, e vale saperlo.

### 1.2 ⭐ Da dove viene l'1,2 — e non è la densità dello schermo

Sull'impronta **del telefono in mano** il `dpr` vale `3,375000238418579`. Due
conti, e tutt'e due danno **numeri interi esatti**:

```
384 × 2,8125 = 1080     832 × 2,8125 = 2340     ⇐ il pannello di un Galaxy S23
                                                   (Adreno 740 = Snapdragon 8 Gen 2)
3,375000238418579 ÷ 2,8125 = 1,2000000847…      ⇐ ⭐ LO STESSO 1,2 DEL DeX
```

`[S]` 2,8125 = **450 dpi ÷ 160**, cioè la densità di serie di quel telefono; e
`[S]` **DeX gira a 160 dpi (mdpi)** — Samsung lo documenta: *«160 dpi (mdpi)»*
per Samsung DeX contro *«640dpi (xxhdpi)»* in Phone Mode
(<https://developer.samsung.com/samsung-dex/how-it-works.html>), e la FAQ
ripete *«Support Multi Density for xxxhdpi (640 dpi) and mdpi (160 dpi)»*
(<https://developer.samsung.com/samsung-dex/faq.html>). 160 dpi ⇒ fattore di
scala del dispositivo **1,0**.

⇒ **La stessa costante 1,2 compare su due configurazioni con densità di
sistema diversissime (1,0 e 2,8125).** Non può essere la densità. È lo **zoom di
pagina di Chrome**, e vale **120 %**.

⭐⭐ **E che lo zoom di pagina MOLTIPLICHI `devicePixelRatio` non è un'ipotesi: è
scritto nel sorgente di Blink.** `[R]`
`third_party/blink/renderer/core/frame/local_frame.cc`, `LocalFrame::DevicePixelRatio()`:

```cpp
double ratio = page_->InspectorDeviceScaleFactorOverride();
ratio *= LayoutZoomFactor();
return ratio;
```

e `[R]` `third_party/blink/renderer/core/frame/web_frame_widget_impl.cc`,
`SetZoomInternal()`:

```cpp
float layout_zoom_factor = device_scale_factor
        * ZoomLevelToZoomFactor(zoom_level) * css_zoom_factor;
local_frame->SetLayoutZoomFactor(layout_zoom_factor);
```

⇒ `[R]` **`devicePixelRatio = densità × zoom_di_pagina × css_zoom`**, dove la
densità su Android è `DisplayMetrics.density = densityDpi / 160` — `[R]` AOSP
`core/java/android/view/DisplayInfo.java` con `DENSITY_DEFAULT = 160`, e `[R]`
Chromium `PhysicalDisplayAndroid.updateFromConfiguration()` passa quel valore
**tale e quale** a `DisplayAndroid.mDipScale` → `set_device_scale_factor()`
(`ui/android/display_android_manager.cc`).

⚠ E `[R]` **su Android non c'è nessun arrotondamento del fattore**: l'unico
`round to nearest 20` in `ui/android/.../DisplayUtil.java` è dentro il ramo
`isAutomotive()`, e `Display::SetScale()` forza la scala intera **solo su Apple**
(`#if BUILDFLAG(IS_APPLE)`) — percorso che Android non tocca. ⇒ Il `dpr` su
Android è **frazionario qualunque**, a passi di `1/160 = 0,00625`: 2,625 (420
dpi), 2,8125 (450 dpi), 3,5 (560 dpi), **1,0 (160 dpi = DeX)**.

**Terza conferma, indipendente.** `[S]` Chrome documenta che in modalità
desktop su Android il viewport, invece del *«default fixed virtual viewport of
980px»*, *«matches the window width»*
(<https://developer.chrome.com/blog/desktop-mode>). Il telefono in mano era
**fuori** dalla modalità desktop-per-finestra (è un telefono, non un tablet
premium): prende il **980 fisso**. E allora:

```
980 ÷ 1,2 = 816,67 → 816    ⇐ ⭐ ESATTAMENTE l'`innerWidth` misurato in mano
2560 ÷ 1,2 = 2133,3 → 2133  ⇐ ⭐ ESATTAMENTE l'`innerWidth` misurato in DeX
```

⛔ **Tre catene indipendenti, tre numeri interi esatti.** La lettura è chiusa:

| grandezza | che cos'è **davvero** su DeX | unità |
|---|---|---|
| densità del monitor esterno | **160 dpi** ⇒ fattore di dispositivo **1,0** | `[S]` Samsung |
| zoom di pagina di Chrome | **120 %** — un'impostazione **dell'utente** | `[M]` dedotto sopra |
| `devicePixelRatio` | `1,0 × 1,2` = **1,2** | fisici ÷ CSS |
| `screen.width/height` | **2560×1080** = i pixel **fisici** del monitor, perché il fattore di dispositivo è 1 | pixel CSS **a zoom 100 %** ⚠ |
| `innerWidth/clientWidth` | **2133** = larghezza della finestra ÷ 1,2 | pixel CSS **allo zoom corrente** ⚠ |
| `innerHeight/clientHeight` | **772** | idem |
| `misura_vista()` | **2560×926** ✅ i pixel fisici veri | fisici |

⚠ **`screen.*` e `inner*` NON sono nella stessa unità**, e questa è la radice di
tutto quel che segue.

### 1.3 ⛔ E il monitor non è 2560×1440

`[M]` `screen 2560×1080`, e `screen.availWidth/availHeight` **2560×1080**: il
DeX ha dato al monitor un modo **21:9**. È lo stesso monitor che il deposito
nomina dappertutto come schermo dell'utente — `xpra.md` riga 122 *«il suo è
**21:9** (2560×1080)»*, `README.md` righe 531 e 599, `fasi/rapporti/F4-A2` riga
58, `fasi/rapporti/F4-A9` riga 173.

⚠ E `[S]` Samsung documenta per DeX solo modi **16:9** — *«FHD(1920x1080, 16:9),
HD+(1600x900, 16:9), and WQHD(2560x1440, 16:9)»*
(<https://developer.samsung.com/samsung-dex/how-it-works.html>). ⭐ **Il misurato
batte il documentato**: il DeX dell'utente ha prodotto 2560×1080, che in
quell'elenco non c'è. È un fatto in più, non un dubbio in meno.

⇒ **I 514 px mancanti non esistono.** Mancano **1080 − 926 = 154 px fisici**,
cioè **154 ÷ 1,2 = 128,3 px CSS**. E a 160 dpi 1 px CSS a zoom 100 % = 1 dp, per
cui i 154 fisici sono **154 dp** di decorazione: `[?]` la ripartizione fra
barra delle applicazioni di DeX (~48 dp), barra del titolo della finestra
(~32-40 dp) e la doppia barra di Chrome in modalità desktop (schede ~40 dp +
indirizzi ~40 dp) **non è misurata** — la somma torna, la ripartizione no, e la
pagina di prova di §9 la separa.

---

## 2. ⛔⭐ Il colpo vero: la formula è giusta **su DeX**, ed è sbagliata di 2,55 volte **sullo stesso telefono in mano**

Il mandato chiedeva di smentire. La smentita non è su 2560×926 — è sulla
**generalità** della formula, e la prova è nel deposito da ieri.

Applico `misura_vista()` alla seconda impronta, quella del telefono tolto dal
dock:

```
innerWidth 816 × dpr 3,375 = 2754 pixel «fisici»   su un vetro che ne ha 1080
                                                    ⇒ ⛔ ERRORE × 2,55
```

⛔ **La pagina dichiarerebbe al server una vista di 2754×4982 su un telefono
1080×2340.**

### 2.1 ⭐ E il meccanismo non è un mistero: è una riga di sorgente

`[R]` La catena, tutta da Blink:

```
clientWidth = layout_size_blink / (DSF × zoom)    element.cc:2552 + adjust_for_absolute_zoom.h:53
devicePixelRatio = DSF × zoom                      local_frame.cc:1921 + web_frame_widget_impl.cc:2532
──────────────────────────────────────────────────────────────────────────────
clientWidth × devicePixelRatio  =  layout_size_blink
```

⇒ ⛔⭐ **Il prodotto non dà «i pixel del vetro»: dà il VIEWPORT DI LAYOUT in
pixel fisici.** Che sia anche il vetro è una **coincidenza fortunata**, non una
proprietà. ⭐ Ed è anche la ragione per cui lo zoom di pagina si cancella
esattamente — `[R]` il commento in `web_view_impl.h:182-197` lo dice: *«We use
only the device scale factor, rather than the full zoom factor which includes
browser zoom, since […] The device's screen size, as measured in physical
pixels, does not change with browser zoom.»* `clientWidth` e `dpr` variano in
modo **reciproco** e il prodotto si conserva.

### 2.2 ⛔⭐ Quando la coincidenza si rompe — e sul telefono dell'utente era **già rotta**

`[R]` `content/browser/web_contents/web_contents_impl.cc:3947-3963`:

```cpp
// Only ignore viewport meta tag when Request Desktop Site is used …
is_request_android_desktop_site = … && !ua_metadata_override->mobile;
prefs.viewport_meta_enabled = !is_request_android_desktop_site;
```

⇒ ⛔⛔ **«Richiedi sito desktop» SPEGNE il meta viewport.** Il
`width=device-width` della pagina viene **buttato**, e resta solo il foglio di
stile dello UA, che `[R]`
(`third_party/blink/renderer/core/css/resolver/viewport_style_resolver.cc:70-91`)
per `ViewportStyle::kMobile` dice:

```cpp
description.min_width = ViewportLength::Fixed(980 * DeviceScaleZoom());
```

**Il conto, sui numeri veri del telefono dell'utente:**

```
layout_size_blink = 980 × DSF = 980 × 2,8125 = 2756,25 pixel fisici
misurato:  innerWidth 816 × dpr 3,375        = 2754      ✓ (a meno dell'arrotondamento)
```

⭐ **Combacia.** Non è «il fattore di pagina misterioso»: è **il 980 del foglio
di stile mobile**, moltiplicato per la densità del telefono. Il vetro c'entra
solo perché Chrome poi **rimpicciolisce** tutto per farcelo stare — `[R]`
`page_scale_constraints.cc:76-97`, `FitToContentsWidth()`:
`minimum_scale = max(minimum_scale, view_width / contents_width)` = `1080/2756`
= **0,392**, e `[R]` `ResolveAutoInitialScale()` mette la scala iniziale uguale
alla minima. **È lo «shrink to fit», acceso di serie su Android** — `[R]`
`web_preferences.h:46-49`, `kShrinksViewportContentsToFit = true`.

⇒ ⭐ **La guardia giusta è quindi `visualViewport.scale`**, e il conto torna al
pixel:

```
clientWidth × devicePixelRatio × visualViewport.scale
   = 2756 × 0,392 = 1080     ⇐ ⭐ la larghezza vera del vetro
```

⚠ `[?]` **Che su Chrome `visualViewport.scale` a riposo valga davvero 0,392 e non
1 non l'ho misurato** — `[S]` la specifica CSSOM View §12 dice *«the visual
viewport's scale factor»* (assoluto) e `[R]` Blink lo prende da
`VisualViewport::Scale()`, che è il page scale factor assoluto; ma MDN lo
descrive come *«relativo alla scala iniziale»*, e le due letture danno 0,392 e
1. ⇒ **La pagina di §9 lo stampa, ed è la riga che decide come si scrive la
cura.**

### 2.3 Perché su DeX la coincidenza invece regge

`[M]` Su DeX il meta viewport **non è spento** (Chrome è in modalità desktop di
sua iniziativa, non perché l'utente abbia spuntato «richiedi sito desktop»), e
allora `[R]` `viewport_description.cc:74-75`:

```cpp
if (length.IsDeviceWidth())
  return initial_viewport_size.width();   // = icb_size_ = la dimensione del WIDGET
```

⭐ **`device-width` è la larghezza della FINESTRA, non dello schermo** — e `[S]`
la specifica del 2016 lo dice per scritto: *«we translate to 100vw/100vh which
are the **window** dimensions. The rationale is that the device dimensions would
not be what the author intended for UAs where the window is resizable or does
not fill the screen»*
(<https://www.w3.org/TR/2016/WD-css-device-adapt-1-20160329/> §9.4).

⇒ `width = MAX(980×1,0, larghezza finestra 2560) = 2560` fisici, e con
`shrink to fit` che non ha niente da stringere (il contenuto ci sta),
`minimum_scale = 1` ⇒ `visualViewport.scale = 1` ⇒ **la formula azzecca**.

⛔ **Quindi la formula del prodotto è corretta su DeX per una catena di tre
condizioni** — meta viewport acceso, finestra più larga di 980, contenuto che ci
sta — **nessuna delle quali è controllata dal codice**. ⚠ E
`SPECIFICHE.md` riga 453 dichiara *«il telefono in mano, in verticale»* come
**ripiego d'emergenza §7.2**: cioè il caso in cui la catena si spezza **è un caso
previsto del prodotto**.

⛔ **La guardia manca in `src/pagina.html`**: `misura_vista()` (righe 1152-1161)
non legge `visualViewport.scale`, non lo nomina, e il commento che la precede —
tre `⚠` sulla barra di scorrimento e sul fattore di scala — **non nomina né il
fattore di pagina né il 980**. ⇒ È un E5 al rovescio: la cura c'è per il rischio
piccolo (15 px di barra, che oltretutto su Android non esiste, §1.1) e manca per
il rischio grosso (× 2,55).

---

## 3. Le sette domande del mandato, con le marche

### 3.1 Che cosa valgono davvero le grandezze su DeX

| grandezza | valore `[M]` 13 ago 2026 | unità | rapporto col monitor vero |
|---|---|---|---|
| `devicePixelRatio` | **1,2000000476837158** | fisici ÷ CSS-correnti | = densità (1,0 a 160 dpi `[S]`) × zoom di pagina (1,2) |
| `screen.width/height` | **2560×1080** | ⚠ pixel CSS **a zoom 100 %** — che a 160 dpi coincidono coi **fisici** | = la risoluzione vera del monitor esterno ✅ |
| `screen.availWidth/Height` | **2560×1080** | idem | ⛔ **non sottrae la barra delle applicazioni di DeX** |
| `window.innerWidth/Height` | **2133×772** | pixel CSS **correnti** (zoom compreso) | finestra ÷ 1,2; ⚠ include la barra di scorrimento |
| `documentElement.clientWidth/Height` | **2133×772** — ⭐ dedotto per aritmetica in §1.1: se divergesse da `inner*`, la vista non farebbe 2560×926 | pixel CSS correnti; `[R]` esce da `layout_size_`, che è **un altro campo** rispetto a quello di `inner*` | è il numero su cui si disegna |
| `misura_vista()` | **2560×926** | **fisici** ✅ | 2560 = tutta la larghezza del monitor ⇒ la finestra era **piena in larghezza** |

⭐⭐ **E che `screen.*` NON senta lo zoom di pagina è anch'esso nel sorgente,
non dedotto.** `[R]` `third_party/blink/renderer/core/frame/screen.cc`,
`Screen::GetRect()`:

```cpp
const display::ScreenInfo& screen_info = GetScreenInfo();
gfx::Rect rect = available ? screen_info.available_rect : screen_info.rect;
if (frame->GetSettings()->GetReportScreenSizeInPhysicalPixelsQuirk())
  return gfx::ScaleToRoundedRect(rect, screen_info.device_scale_factor);
...
return rect;
```

⇒ `screen.width/height` esce da **`ScreenInfo`**, cioè da `display.bounds()`, che
`[R]` nasce in Java come
`DisplayUtil.scaleToEnclosingRect(boundsInPixels, 1.0f / displayMetrics.density)`
(`PhysicalDisplayAndroid.java`): **pixel fisici ÷ densità**, e **`LayoutZoomFactor`
non compare da nessuna parte in quel percorso**. ⛔ Mentre `innerWidth` e
`clientWidth` escono dall'impaginazione, che per `LayoutZoomFactor` ci passa.
**È T2, dimostrata: due unità diverse, e la differenza è esattamente lo zoom.**

⚠ Il quirk `report_screen_size_in_physical_pixels_quirk` — l'unica via per cui
`screen.*` tornerebbe in pixel fisici — `[R]` ha default `false`
(`third_party/blink/public/common/web_preferences/web_preferences.h`) ed è acceso
**solo dalla WebView di Android per le app legacy**
(`android_webview/browser/aw_settings.cc`). ⇒ In Chrome per Android **non è mai
acceso**, DeX compreso.

⭐ **E si spiega anche il `disponibile 2560×1080`**, cioè una `availHeight` che
**non toglie la barra delle applicazioni di DeX**: `[R]` `availWidth/Height` esce
da `display.work_area()`, e il calcolo corretto del work area su Android sta
dietro il flag `kAndroidUseCorrectDisplayWorkArea` — **spento, `work_area =
bounds`** (`ui/android/display_android_manager.cc`, `DoUpdateDisplay`). ⇒ ⛔ **Su
DeX `screen.availHeight` non è utilizzabile per sapere quanta altezza c'è
davvero**: mente di tutta la barra delle applicazioni.

⚠ **La sonda del 13 agosto registra `innerWidth`, non `clientWidth`**, e le due
su Chrome Android sono `[R]` **due campi diversi di `LocalFrameView`** —
`innerWidth` da `View()->Size()` (= `size_ / MinimumPageScaleFactor()`),
`clientWidth` da `GetLayoutSize()`. §1.1 mostra per aritmetica che **su DeX
coincidono**; ⭐ la pagina di prova di §9 le stampa tutt'e due, e quella riga
trasforma l'aritmetica in misura.

### 3.2 2560×926 è plausibile? E che cosa occupa i px mancanti

✅ Non solo plausibile: **riprodotto al pixel** (§1.1). ⛔ Ma **non** su
2560×1440 e **non** con 514 px di decorazione: su **2560×1080**, con **154 px
fisici** (128 CSS) di decorazione. `[?]` La ripartizione fra barra delle
applicazioni, barra del titolo e barre di Chrome non è misurata (§1.3).

⛔ **E i numeri NON tradiscono un errore di unità *in* `misura_vista()`** — ne
tradiscono **due altrove**, §4.

### 3.3 `<meta name="viewport" content="width=device-width, initial-scale=1">` su DeX

`[S]` Chrome in modalità desktop su Android **non usa più il viewport virtuale
fisso da 980 px**: *«Rather than using a default fixed virtual viewport of
980px, the viewport now matches the window width»*
(<https://developer.chrome.com/blog/desktop-mode>). E `[M]` su DeX Chrome **è**
in modalità desktop: manda `Mozilla/5.0 (X11; Linux x86_64) … Chrome/151` —
`[R]` `banchi/02-giudizio-dispositivo.py` riga 771 — che `[S]` è esattamente la
stringa che quel documento chiama «desktop»; e `[S]` Samsung documenta lo stesso
travestimento per DeX (<https://developer.samsung.com/internet/android/web-development-guide-for-dex.html>).

⇒ ⭐ **Su DeX il viewport di layout è la larghezza della finestra**: 2133 px CSS
= 2560 fisici ÷ 1,2.

⛔⭐ **E `width=device-width` NON è inutile: è quel che tiene in piedi la
misura.** `[R]` L'algoritmo è `width = MAX(min-width, MIN(max-width,
initial-width))` (`[S]` CSS Device Adaptation 2016, §6.2), dove per DeX
`min-width` viene dal foglio dello UA — `980 × DSF` in `ViewportStyle::kMobile`,
oppure `DeviceWidth()` in `kDefault` `[R]`
(`viewport_style_resolver.cc:70-91`) — e `initial-width` viene dal meta. **Senza
il meta, `width=device-width` non c'è e resta il 980**: `[R]` il ramo
`kMobile` mette `min_width = 980 × DeviceScaleZoom()` e basta. ⇒ Su DeX il 980
non morde comunque (2560 > 980), ma **sul telefono sì**, ed è §2.2.

⭐⭐ **E c'è una soglia che decide quale dei due fogli si usa, con un difetto
noto proprio per DeX.** `[R]` `web_contents_impl.cc:3930-3945`:

```cpp
display::Display display = display::Screen::Get()->GetPrimaryDisplay();
int min_width_in_dp = min_width / display.device_scale_factor();
if (prefs.viewport_enabled && (… min_width_in_dp >= kAndroidMinimumTabletWidthDp …))
  prefs.viewport_style = blink::mojom::ViewportStyle::kDefault;
```

con `[R]` `kAndroidMinimumTabletWidthDp = 600` (`content/public/common/content_constants.cc:66`).
⛔ **Quella riga guarda `GetPrimaryDisplay()`, cioè lo schermo del TELEFONO, non
il monitor DeX** — e nel file c'è il `TODO` che lo ammette: *«GetPrimaryDisplay()
won't be correct for externally connected displays»*
(<https://issues.chromium.org/issues/40925473>).

⇒ `[?]` **Su DeX il telefono misura 1080/2,8125 = 384 dp < 600 ⇒ Chrome resta su
`ViewportStyle::kMobile` anche mentre disegna su un monitor da 2560.** Non fa
danno **solo perché** il meta `width=device-width` c'è e 2560 > 980. ⛔ **Togli
il meta, e la stessa pagina su DeX impagina a 980 px fisici invece che a 2560.**
Questa è la ragione tecnica per cui quella riga di `src/pagina.html` (riga 82)
**non si tocca**.

⚠ **La «scala minima» / «shrink to fit»** è accesa di serie su Android — `[R]`
`web_preferences.h:46-49`: `kDefaultMinimumPageScaleFactor = 0.25f`,
`kShrinksViewportContentsToFit = true` (su desktop sono `1.0f` e `false`). ⚠ Il
flag che la spegnerebbe sugli schermi grandi,
`[R]` `blink::features::kAndroidDesktopWebPrefsLargeDisplays`, è **spento di
serie**. ⇒ Su DeX non morde perché il contenuto ci sta; sul telefono in mano
morde, ed è §2.2.

`[?]` Che `initial-scale=1` sia rispettato o clampato su DeX **non è misurato**;
`[R]` l'unico percorso trovato è il clamp a `[min-zoom, max-zoom]`
(`viewport_description.cc:124-127`), e il quirk `ClobberUserAgentInitialScaleQuirk`
è spento in Chrome.

### 3.4 `window.visualViewport`

⚠ **Non è più una specifica a sé: è dentro CSSOM View §12** —
<https://drafts.csswg.org/cssom-view/#the-visualviewport-interface>. `[S]` Le
definizioni, verbatim:

| campo | definizione `[S]` |
|---|---|
| `offsetLeft/Top` | *«the offset of the left/top edge of the visual viewport from the […] edge of the **layout viewport**»* |
| `pageLeft/Top` | l'offset dal bordo del **blocco contenitore iniziale** del documento |
| `width/height` | *«the width of the visual viewport **excluding** […] any rendered vertical classic scrollbar»* |
| `scale` | *«the visual viewport's **scale factor**»* |

`[S]` E l'unità, che è la nota che serve a noi: *«Since this value is returned in
**CSS pixels**, the value will decrease in magnitude if either **page zoom** or
the **scale factor** is increased.»*

`[R]` E l'implementazione conferma che sono **già normalizzate due volte** —
`third_party/blink/renderer/core/frame/visual_viewport.cc`:

```cpp
visible_size.Enlarge(0, browser_controls_adjustment_);   // la barra che si ritrae
visible_size.Scale(1 / scale_);                          // il pinch / lo shrink-to-fit
…
Width()  → VisibleRect().width()  / LocalMainFrame().LayoutZoomFactor();   // lo zoom
```

⇒ ⭐ **`visualViewport.width/height` è l'unica grandezza che segue davvero quel
che si vede**: `clientHeight` e `innerHeight` sono tutt'e due **stabili** e
tutt'e due **diverse fra loro** su Chrome Android (§1.1), e nessuna delle due
segue la barra.

**Quando divergono dal viewport di layout** `[S]`: pinch-zoom; tastiera a schermo;
barra degli indirizzi che si ritrae. ⚠ E da **Chrome 108** il valore di serie di
`interactive-widget` è **`resizes-visual`** — `[S]`
<https://developer.chrome.com/blog/viewport-resize-behavior> — cioè la tastiera
**non** tocca più `clientHeight` né `innerHeight`, tocca solo
`visualViewport.height`. ⛔ Per il ripiego «telefono in mano» di §7.2 questo vuol
dire che **la pagina non si accorgerebbe della tastiera**: la vista dichiarata
resterebbe quella intera.

`[?]` **Non ho nessuna misura di `visualViewport.*` su DeX**: la sonda del 13
agosto non lo raccoglieva, e **non lo deduco** — `scale` è definito relativo alla
scala iniziale, e non è ovvio che con lo «shrink to fit» a riposo valga 0,392
invece di 1. ⇒ È **la prima riga** che la pagina di §9 misura.

**Gli eventi, e quello che manca al prodotto.**

- `src/pagina.html` riga 2115 ascolta **solo** `resize` di `window`. ⛔ Mancano
  `visualViewport.addEventListener('resize'|'scroll')`.
- `[S]` CSSOM View §13.1: `resize` su `Window` scatta anche **al cambio di zoom
  di pagina**, e `resize` su `VisualViewport` scatta se cambiano *«scale, width,
  or height»*.
- ⚠ `[R]` **`window.resize` su Chrome Android può scattare anche quando
  `innerWidth/innerHeight` NON sono cambiati**: `WebViewImpl::ResizeWithBrowserControls()`
  chiama sempre `SendResizeEventForMainFrame()`, e c'è il `TODO` degli
  sviluppatori che lo dice (crbug 1353728). ⇒ **Si confrontano i valori, non si
  contano gli eventi** — e la pagina lo fa già, perché `vista()` esce subito se i
  numeri non sono cambiati (`[R]` riga 1400).
- `[?]` Trascinando il bordo della finestra DeX: `window.resize` **sì** e
  `visualViewport.resize` **sì** (la catena è `[R]`: l'activity di Chrome dichiara
  `resizeableActivity="true"` e `configChanges` che include `screenSize|density`,
  quindi gestisce il resize senza essere ricreata); `screen.orientation.change`
  **no** — `[S]` Samsung dichiara i display DeX sempre *landscape*.
- ⭐ Il cambio di `devicePixelRatio` **a finestra ferma** non ha nessun evento
  dedicato: `[S]` MDN, *«Monitoring screen resolution or zoom level changes»*,
  dà come unica via una `matchMedia("(resolution: N dppx)")` **da ricreare a ogni
  cambio**. È la `[?]` che `src/pagina.html` righe 2145-2154 dichiara già aperta,
  ed è scritta nella pagina di prova di §9. ⚠ Serve **davvero** su DeX: fra
  pannello del telefono (640 dpi ⇒ ~4) e monitor DeX (160 dpi ⇒ 1) il salto è di
  quattro volte.

### 3.5 ⛔ Schermo intero su DeX — e qui la mia prima risposta era sbagliata

⚠ **Avevo scritto che lo schermo intero è «il modo giusto per avere 1:1». Le
fonti dicono che probabilmente NON basta**, e la correzione vale più della
risposta.

`[S]` **La regola che conta è di Android, non del browser** — *Window
management*, Android Developers,
<https://developer.android.com/topic/arc/window-management>:

> «If the window is **not covering the full screen**, requests for full
> screening (hiding all system UI elements) **are ignored**.»
> «When the app is **maximized** the normal fullscreen methods […] are
> performed. This hides the system UI elements.»

`[R]` E Chrome per Android lo asseconda —
`chrome/android/java/src/org/chromium/chrome/browser/fullscreen/FullscreenHtmlApiHandlerBase.java`:
in `enterFullScreen()` la barra di stato **non** viene resa translucida se
`mIsInMultiWindowMode`, e
`FullscreenMultiWindowModeObserver.onMultiWindowModeChanged()` chiama
`onExitFullscreen(mTab)` — cioè **quando la finestra entra in multi-window Chrome
ESCE dallo schermo intero**.

⇒ ⭐ **Il modello attendibile per DeX** — `[R]`+`[S]`, `[?]` per la conferma sul
ferro:

| che cosa | in una finestra DeX |
|---|---|
| la promessa di `requestFullscreen()` | si risolve, `fullscreenchange` scatta, `:fullscreen` si applica `[?]` |
| i controlli di Chrome (schede + indirizzi) | **spariscono** ⇒ `clientHeight` cresce `[?]` |
| la finestra DeX | **NON** si ingrandisce sul monitor `[S]` |
| barra del titolo della finestra e barra delle applicazioni di DeX | **restano** `[S]` |

⇒ ⛔ **Lo schermo intero in DeX è «a tutta finestra», non «a tutto monitor»** —
salvo che la finestra sia **già massimizzata**, e `[M]` quella dell'utente lo era
almeno in larghezza (2560 = tutto il monitor). ⚠ **Se anche in altezza fosse
massimizzata, i 154 px mancanti sarebbero già solo i controlli di Chrome**, e lo
schermo intero li recupererebbe tutti: allora **sì**, 1080 e scala 1,000.
`[?]` **È esattamente la domanda che la pagina di §9 chiude in dieci secondi.**

- `[?]` Se `devicePixelRatio` cambi passando a schermo intero: **no** —
  `[R]` dipende dal `device_scale_factor` dello `ScreenInfo` del display, che il
  fullscreen non tocca. Idem `screen.width/height` `[R]` (`Screen::GetRect()`
  legge il display, non la finestra). Cambia solo `inner*`/`client*`.
- ⛔ `src/pagina.html` riga 5273 dichiara già `[?]` *«blink su Android / DeX —
  nessun telefono e nessun DeX collegati»*, e c'è un difetto **certo** nel
  riconoscimento, §4.2.
- ⛔ **`screen.orientation.lock()` su DeX: consideralo NON disponibile.** `[R]`
  `ScreenOrientationDelegateAndroid::FullScreenRequired()` ritorna sempre `true`,
  e `ScreenOrientationProviderSupported()` ritorna **falso** per i form factor
  non-telefono con la feature `kRestrictOrientationLockToPhones` — e un display
  DeX è `[S]` «xLarge» a 160 dpi, cioè ben oltre i 600 dp di `isTablet()`. In più
  `[R]` il lock si implementa con `activity.setRequestedOrientation()`, che
  Android **ignora** per un'activity in freeform.

### 3.6 PWA installata su DeX

`[S]` Samsung documenta che su DeX una PWA *«can be launched in a standalone,
resizable window, without the URL bar»*
(<https://developer.samsung.com/internet/android/web-development-guide-for-dex.html>),
e la stessa cosa dice l'articolo degli sviluppatori di Samsung Internet
(<https://samsunginternet.github.io/Samsung-DeX-brings-a-new-Dimension-to-the-Mobile-Web/>):
*«their own window which is fully resizable like all DeX mode compatible apps»*.

`[R]` E Chrome soddisfa il requisito Samsung anche per le PWA:
`chrome/android/java/AndroidManifest.xml` applica `resizeableActivity="true"` e
la lista `configChanges` a `WebappActivity` e `SameTaskWebApkActivity`.

⇒ ⭐ **Sulle misure cambia una cosa, e in meglio.** `[R]` Senza barra degli
indirizzi i browser controls hanno altezza zero ⇒ in
`WebViewImpl::UpdateICBAndResizeViewport()` la decurtazione dell'ICB non si
applica ⇒ **`clientHeight`, `innerHeight` e `visualViewport.height` convergono
sullo stesso numero e diventano stabili**, e `100vh == 100svh == 100lvh ==
100dvh`. ⛔ È **la configurazione con la geometria più semplice da governare**, ed
è quella in cui la divergenza di §1.1 fra `clientHeight` e `innerHeight` sparisce
per costruzione. ⚠ Di quanti pixel cresca la vista è `[?]`.

⛔ Non cambia né la densità né lo zoom, quindi `devicePixelRatio` resta 1,2 `[?]`.

⭐ E c'è un modo **portabile e già scritto** di sapere in che modo si è, che non
guarda la geometria: `matchMedia("(display-mode: standalone|fullscreen|browser)")`
`[S]` (<https://developer.mozilla.org/en-US/docs/Web/CSS/@media/display-mode>).
È in §4.2 e nella pagina di §9.

⚠ **E una cosa su cui NON contare su Android**: `screen.isExtended` e
`window.getScreenDetails()` (Window Management API) esistono `[S]` su Chrome
Android da 100 — l'IDL non ha nessun gate di piattaforma `[R]` — ma `[R]`
`DisplayAndroidManager.java` registra **tutti** i display solo se la feature
`AndroidUseDisplayTopology` è attiva (flag Chromium **e** flag aconfig di
sistema); altrimenti registra **solo il display di default** ⇒
`screen.isExtended === false` e `getScreenDetails().screens` ha **un solo
elemento**, anche con il monitor DeX collegato. `[?]` Non verificato sul ferro.

### 3.7 ⭐ La formula giusta per «un pixel del buffer = un pixel del vetro», e le trappole

**La formula, e le condizioni senza cui non vale.**

```
fisici_larghezza = documentElement.clientWidth  × devicePixelRatio × visualViewport.scale
fisici_altezza   = documentElement.clientHeight × devicePixelRatio × visualViewport.scale
canvas.width       = Math.floor(fisici_larghezza)   (il buffer)
canvas.style.width = clientWidth + "px"             (la cornice — ⚠ NON fisici/dpr, §7.3)
```

⛔ **Le condizioni, tutte `[R]`, e nessuna delle tre è controllata dal codice:**

1. `<meta name="viewport" content="width=device-width, initial-scale=1">` **deve
   esserci e deve essere in vigore** — «richiedi sito desktop» lo spegne (§2.2);
2. la finestra deve essere **più larga di `980 × DSF`**, o il foglio dello UA
   `kMobile` vince;
3. il contenuto deve **starci dentro**, o `shrinks_viewport_contents_to_fit`
   abbassa la scala minima.

⭐ E `visualViewport.scale` è **esattamente** il numero che dice se 2 e 3 hanno
morso: è per questo che va nella formula invece di essere dedotto.

**Le trappole, in ordine di quanto costano.**

| # | trappola | costo misurato |
|---|---|---|
| **T0** | ⛔⭐ **`clientWidth × dpr` è il VIEWPORT DI LAYOUT in pixel fisici, non il vetro** `[R]` — coincidono solo se il meta viewport è in vigore e la finestra è più larga di 980 | tutto il resto discende da qui |
| **T1** | ⛔ **spegnere il meta viewport («richiedi sito desktop») porta il layout a `980 × DSF`**, e il fattore di pagina che rimpicciolisce **non è in `devicePixelRatio`** | **× 2,55** `[M]`, §2.2 |
| **T2** | ⛔ **`screen.*` è in px CSS a zoom 100 %, `inner*`/`client*` allo zoom corrente**: mescolarli sbaglia del fattore di zoom | **× 1,2** `[M]` su DeX, §4.1 e §4.2 |
| **T2-bis** | ⛔ **`innerWidth` non è `clientWidth`** su Chrome Android: `[R]` `innerWidth = size_ / MinimumPageScaleFactor`, `clientWidth = layout_size_`. Sono **due campi diversi** di `LocalFrameView`, e divergono se c'è un elemento più largo dell'ICB (<https://issues.chromium.org/issues/41239283>) | fino a × 1/minScale |
| **T2-ter** | ⛔ **sull'ALTEZZA `clientHeight × dpr` non è mai l'altezza del monitor**: `[R]` l'ICB è decurtato dei browser controls, e `innerHeight` no ⇒ le due misure differiscono dell'altezza della barra degli indirizzi | l'altezza della barra |
| **T3** | ⚠ **`clientWidth` è un intero, il viewport vero no**: a dpr 1,2 il viewport è 2133,33 px CSS e `clientWidth` dà 2133 | ≤ 1 px fisico |
| **T4** | ⛔ **l'andata e ritorno `round(l·r)` poi `l/r` SBORDA**: `round(2133×1,2)=2560`, e `2560/1,2 = 2133,33 px CSS` — **0,33 px CSS più larghi di `clientWidth`** ⇒ candidato a far comparire la barra orizzontale | 1/3 px CSS, §7.3 |
| **T5** | ⚠ `clientWidth` **esclude** la barra di scorrimento, `innerWidth` **la include** `[S]` — ⭐ ma **su Android la barra è in sovrimpressione e non toglie niente** (§1.1): la cura `html{overflow-y:scroll}` serve sul portatile, **non** su DeX | 15 px CSS sul portatile, **0 su DeX** `[M]` |
| **T6** | ⚠ con dpr **frazionario** non esiste nessuna coppia esatta a meno che `clientHeight × dpr` sia intero: **926,4 non è intero**, e qualunque arrotondamento costa ≤ 1 px | ≤ 1 px |
| **T7** | ⚠ il compositore **aggancia la cornice CSS alla griglia dei pixel fisici** con la SUA regola, che non è `Math.round` | ≤ 1 px, `[?]` |

⇒ ⭐ **La cura per T4/T6 è una riga**: prendere il buffer col **pavimento** e la
cornice dalla **misura CSS**, non dal buffer:

```js
const l = d.clientWidth, a = d.clientHeight, r = devicePixelRatio || 1;
tela.width  = Math.max(1, Math.floor(l * r));   // ⇐ floor, non round
tela.style.width  = l + "px";                    // ⇐ il numero misurato, non l/r
```

Così `buffer ÷ r ≤ clientWidth` **sempre**, la barra orizzontale non può nascere
da un arrotondamento, e l'errore di scala resta sotto il pixel fisico.

---

## 4. ⛔ I due difetti **certi** che questa misura scopre in `src/pagina.html`

⚠ Non li ho curati — non è il mio mandato. Li dichiaro con riga e conto.

### 4.1 Riga 1030-1031 — `screen.width × devicePixelRatio`, e su DeX stampa un monitor che non esiste

```js
+ "che vale " + Math.max(1, Math.floor(screen.width  * devicePixelRatio))
+ "x"        + Math.max(1, Math.floor(screen.height * devicePixelRatio))
+ " e viaggia in ATTACCA come «vista»"
```

`[M]` Sui numeri del DeX: `2560 × 1,2 = 3072` e `1080 × 1,2 = 1296`. ⛔ **La
pagina scrive nel registro dell'utente «lo schermo vale 3072×1296»** — una
risoluzione che quel monitor non ha e non può avere. È **T2**, ed è **esattamente
il rilievo S5** (`DECISIONI.md` §5.0-ter, riquadro del 10 agosto): *«su Chrome
`screen.width` NON cala con lo zoom di pagina, mentre `devicePixelRatio` sale»*.

⚠ E la riga dice *«e viaggia in ATTACCA come vista»*: **è falso oggi** — in
`ATTACCA` viaggia `misura_vista()` (riga 2576), che è giusta. ⇒ Il difetto è
**doppio**: un numero sbagliato e una frase che lo attribuisce al posto sbagliato.

### 4.2 ⛔⭐ Riga 5301 — il riconoscimento dello schermo intero **non può scattare su DeX**

```js
const pieno = (innerWidth >= screen.width - 2 && innerHeight >= screen.height - 2);
```

`[M]` Sui numeri del DeX, **anche a schermo intero perfetto**:

```
innerWidth  = 2560 ÷ 1,2 = 2133      screen.width  = 2560     2133 ≥ 2558 ?  ⛔ NO
innerHeight = 1080 ÷ 1,2 =  900      screen.height = 1080       900 ≥ 1078 ?  ⛔ NO
```

⛔ **`pieno` vale `false` per costruzione, per qualunque geometria, finché lo
zoom di pagina non è 100 %.** È T2 di nuovo: si confronta un numero in px CSS
**correnti** con uno in px CSS **a zoom 100 %**. ⇒ La *«trappola O10, prima
metà»* — lo schermo intero entrato da `F11` che non accende
`document.fullscreenElement` — **resta scoperta su DeX**, cioè sull'uso primario
dichiarato (`DECISIONI.md` §5-bis.0). La stessa forma è alla riga 5834-5835
(`schermo_intero_geometria`).

⭐ **La cura non è aggiustare la soglia: è smettere di guardare la geometria.**
Esiste una media query fatta apposta, che prende **anche** l'`F11`:

```js
const pieno = matchMedia("(display-mode: fullscreen)").matches;
```

⚠ `[?]` Che Chrome per Android la accenda anche in DeX **non è misurato**: la
pagina di §9 la stampa accanto a `document.fullscreenElement`, e le due righe
insieme dicono se la cura regge.

### 4.3 ⭐ E la `[?]` di `DECISIONI.md` §5.0-ter **si può chiudere adesso**

Quel riquadro finisce così (riga 1839-1840):

> ⚠ **E metà di S5 non è misurata**: il **DeX** non c'era. […] **la seconda
> delle tre `[?]` resta intera.**

⇒ ⭐ **La seconda `[?]` — *«che cosa risponde DeX»* — è chiusa dai numeri del 13
agosto, e la risposta è quella cattiva**: su DeX Chrome si comporta **come
Chrome sul portatile, non come Firefox**. `screen.width` resta 2560 mentre
`devicePixelRatio` sale a 1,2, e il prodotto **non resta**: dà 3072, cioè
**+20 %**. ⛔ La formula di `SPECIFICHE.md` §6.1-bis è rotta su DeX **esattamente
come su Chrome desktop**, e su DeX il difetto è **acceso adesso**, perché lo zoom
al 120 % è l'impostazione **che l'utente ha davvero**.

---

## 5. Che cosa regge del mandato, e con quale prova

| affermazione | verdetto | prova |
|---|---|---|
| «2560×926 è una misura corretta» | ✅ **REGGE** | `[M]` 772 × 1,2 = 926,4 → 926, riprodotto dall'impronta verbatim |
| «mescola pixel CSS e fisici» | ❌ **smentita** — `misura_vista()` moltiplica una volta sola, e la moltiplica **giusta** | `[R]` righe 1152-1161 |
| «su DeX `devicePixelRatio` non significa quel che crediamo» | ⚠ **mezza vera, e la metà vera è quella che costa** | ⛔ **significa quel che crediamo** (fisici ÷ CSS) e la vista è giusta; ⛔ **ma non è la densità dello schermo**: `[R]` è `DSF × zoom_di_pagina × css_zoom`, qui `1,0 × 1,2`, e chi lo usa insieme a `screen.*` sbaglia del 20 % (§4.1, §4.2) |
| «monitor 2560×1440, 514 px mancanti» | ⛔ **CADE** | `[M]` monitor **2560×1080**, mancano **154** px |
| «le bande nere laterali sono giuste» | ✅ **REGGE** | `componi()` `[R]` righe 1476-1500: scala 0,857, nero 914 px. Già misurato come *«912 px di nero»* |
| ⭐ **la formula è corretta in generale** | ⛔ **CADE** | `[M]` sullo **stesso telefono** in mano: `816 × 3,375 = 2754` su un vetro da 1080 — **× 2,55**, e `[R]` il meccanismo è il 980 del foglio dello UA con «richiedi sito desktop» acceso (§2.2) |
| ⭐ **«a schermo intero torna 1:1»** (`SPECIFICHE.md` §6.1-bis) | ⚠ **`[?]`, e il dubbio è nuovo** | `[S]` Android: *«If the window is not covering the full screen, requests for full screening are ignored»* ⇒ in una finestra DeX lo schermo intero toglie i controlli di Chrome ma **non** la barra del titolo né quella delle applicazioni (§3.5, §7) |

---

## 6. ⚠ La `[?]` che resta appesa a tutto il resto

⛔ **Il `dpr = 1,2` è dedotto essere zoom di pagina, non misurato come tale.**
Le tre catene di §1.2 (il 2,8125 esatto del pannello, l'1,2 identico su due
densità diverse, il 980 ÷ 1,2 = 816 esatto) sono forti, e non conosco nessuna
lettura alternativa che le regga tutte e tre. ⚠ Ma resta il fatto che
**JavaScript non espone lo zoom di pagina in modo portabile** — lo dice già
`DECISIONI.md` riga 1836 — e quindi la conferma diretta è una cosa sola:
**l'utente apre la pagina di §9, guarda `zoom_stimato` a finestra piena, poi
rimette lo zoom di Chrome al 100 % e riguarda.** Se `zoom_stimato` passa da 1,2 a
1,0 e `devicePixelRatio` da 1,2 a 1,0, la deduzione è chiusa in trenta secondi.

⭐ **E la cosa da notare è che la vista NON cambierà**: a zoom 100 % `clientWidth`
diventa 2560 e `dpr` 1,0, e `2560 × 1,0 = 2560`. **`misura_vista()` è invariante
allo zoom** — è la sua proprietà migliore, ed è quel che la salva mentre
`screen.width × dpr` affonda.

---

## 7. ⭐ Il numero che il mandato non chiedeva: a 2560×926 il desktop **non è 1:1**

`componi()` (`[R]` righe 1476-1500) impagina con `s = min(cl/fl, ca/fa)`.

| vista | scala | dipinto sul vetro | nero | 1:1? |
|---|---|---|---|---|
| **2560×926** (la finestra di oggi) | **0,857** | 1646×926 | 914 px (457/lato) | ⛔ **no — il 1920×1080 è rimpicciolito al 85,7 %** |
| 2560×857 (13 ago, `[R]` riga 153) | 0,794 | 1524×857 | 1036 px | ⛔ no |
| ⭐ **2560×1080** (schermo intero) | **1,000** | **1920×1080** | 640 px (320/lato) | ✅ **sì, esatto** |

⛔ **Il vincolo è l'ALTEZZA, non la larghezza.** In larghezza avanzano 640 px
(2560 contro 1920); in altezza ne mancano 154, e quei 154 costano **tutto**: il
14,3 % di rimpicciolimento in **tutt'e due** le direzioni, e con esso la
nitidezza del testo del desktop remoto. `SPECIFICHE.md` §6.1-bis promette
*«appena vai a schermo intero torna 1:1 e nitido»*.

⚠⚠ **E qui la mia prima stesura era troppo generosa.** La promessa è
aritmeticamente esatta **soltanto se lo schermo intero recupera tutti e 154 i
pixel**, e §3.5 dice che su DeX probabilmente ne recupera solo una parte:

| che cosa mangia i 154 px | lo schermo intero lo recupera? |
|---|---|
| barra delle schede + barra degli indirizzi di Chrome | ✅ **sì** `[?]` |
| barra del titolo della finestra DeX | ⛔ **no** se la finestra resta una finestra `[S]` |
| barra delle applicazioni di DeX | ⛔ **no**, idem `[S]` |

⇒ ⛔ **La domanda «1:1 sì o no» si riduce a una sola misura**: dopo aver premuto
il bottone «schermo intero», `clientHeight × dpr` vale **1080** oppure meno? ⭐ Se
vale 1080, la scala è 1,000 e la promessa di §6.1-bis è mantenuta. Se vale, per
dire, 1022, la scala è 0,946 e **il testo del desktop remoto resta sfocato anche
a schermo intero**. ⚠ **Non lo so, e non lo deduco.** È la quarta riga della
pagina di §9.

⇒ ⭐ **Le tre strade, in ordine di quanto sono sicure:**

1. **Massimizzare la finestra DeX, poi schermo intero.** `[S]` La regola Android
   è *«when the app is maximized the normal fullscreen methods […] are
   performed»*: è **l'unica** condizione in cui Android concede di nascondere la
   UI di sistema. ⚠ Dipende dai `[?]` di §3.5 e dal difetto di §4.2.
2. **PWA installata con `display: fullscreen`.** `[S]` web.dev: *«A fullscreen
   experience […] is currently only available on Android devices, and it hides
   the status bar and the navigation bar, giving your PWA 100% of the screen»*.
   ⭐ E `[R]` è anche la configurazione in cui `clientHeight`, `innerHeight` e
   `visualViewport.height` **convergono** (§3.6): meno numeri, meno modi di
   sbagliare.
3. **`ADATTA_TELA` alla vista che c'è.** Toglie il nero **e** non rimpicciolisce
   niente, ma cambia la forma del desktop remoto. È una decisione dell'utente
   (`SPECIFICHE.md` §6.4), e `DECISIONI.md` §5.0-quinquies ha già deciso
   **1920×1080** col prezzo scritto accanto. ⛔ Sarebbe un **terzo** numero da
   decidere, non questo rapporto.

### 7.3 ⚠ E la cornice, oggi, sborda di un terzo di pixel

`[R]` Righe 1407-1409: `this.tela.style.width = (l / r) + "px"` con `l` = buffer.
`[M]` Sui numeri del DeX: `l = 2560`, `r = 1,2` ⇒ `style.width = 2133,3332px`,
mentre `clientWidth` vale **2133**. ⇒ **la cornice è 0,33 px CSS più larga della
vista in cui deve stare** (trappola T4). ⚠ Non l'ho vista comparire — è sotto il
pixel e il compositore probabilmente la aggancia — ma è **la stessa famiglia** del
difetto del 13 agosto che costò 15 px alla vista (`[R]` righe 1425-1443), e a
dpr 1 **non poteva esistere**: nasce col dpr frazionario, cioè **nasce su DeX**.

---

## 8. Le fonti, e che cosa ciascuna dà

| fonte | che cosa dà | marca |
|---|---|---|
| `banchi/02-giudizio-dispositivo.py` righe 766-814 | ⭐ **le due impronte verbatim del 13 agosto**: tutta l'aritmetica di §1 | `[R]` di una misura `[M]` dell'utente |
| Samsung, *How Samsung DeX works* — <https://developer.samsung.com/samsung-dex/how-it-works.html> | **«160 dpi (mdpi)»** per DeX contro «640dpi (xxhdpi)» in Phone Mode; i modi esterni documentati «FHD(1920x1080, 16:9), HD+(1600x900, 16:9), and WQHD(2560x1440, 16:9)» | `[S]` |
| Samsung, *DeX FAQ* — <https://developer.samsung.com/samsung-dex/faq.html> | «Support Multi Density for xxxhdpi (640 dpi) and mdpi (160 dpi)» | `[S]` |
| Chrome for Developers, *Desktop mode* — <https://developer.chrome.com/blog/desktop-mode> | ⭐ «Rather than using a default fixed virtual viewport of 980px, the viewport now matches the window width»; UA da `Linux; Android` a `X11; Linux x86_64`; `SEC-CH-UA-PLATFORM` da `Android` a `Linux` | `[S]` |
| Samsung, *Web Development Guide for DeX* — <https://developer.samsung.com/internet/android/web-development-guide-for-dex.html> | l'UA `X11; Linux x86_64` in DeX; PWA «launched in a standalone, resizable window, without the URL bar» | `[S]` |
| Samsung Internet, *DeX brings a new Dimension to the Mobile Web* — <https://samsunginternet.github.io/Samsung-DeX-brings-a-new-Dimension-to-the-Mobile-Web/> | «their own window which is fully resizable like all DeX mode compatible apps» | `[S]` |
| Chromium, `core/dom/element.cc` (`Element::clientWidth`), `core/frame/local_dom_window.cc`, `core/frame/local_frame.cc`, `core/frame/web_frame_widget_impl.cc`, `core/exported/web_view_impl.cc`, `core/frame/screen.cc`, `core/frame/visual_viewport.cc`, `core/css/resolver/viewport_style_resolver.cc`, `core/page/viewport_description.cc`, `core/frame/page_scale_constraints_set.cc`, `blink/public/common/web_preferences/web_preferences.h`, `content/browser/web_contents/web_contents_impl.cc`, `ui/android/display_android_manager.cc`, `ui/android/.../PhysicalDisplayAndroid.java`, `DisplayAndroidManager.java`, `DisplayUtil.java`, `ui/display/display.cc`, `ui/display/display_util.cc` — <https://source.chromium.org/chromium/chromium/src> | ⭐ **la catena intera**: `dpr = DSF × zoom`, `clientWidth × dpr = layout_size_blink`, `screen.*` da `display.bounds()` in DIP, il 980 di `kMobile`, il meta spento da «richiedi sito desktop», lo shrink-to-fit, i browser controls che decurtano l'ICB | `[R]` |
| AOSP, `core/java/android/view/DisplayInfo.java`, `core/java/android/util/DisplayMetrics.java`, `services/.../LocalDisplayAdapter.java`, `services/.../DisplayContent.java` — <https://android.googlesource.com/platform/frameworks/base> | `density = densityDpi / 160`, esatto e senza arrotondamenti | `[R]` |
| W3C, **CSSOM View Module Level 1** — <https://drafts.csswg.org/cssom-view-1/> | §2.1 *«All coordinates and dimensions […] are in CSS pixels»*; §6 `clientWidth` = *«the viewport width excluding the size of a rendered scroll bar»*; §4 `innerWidth` = *«including the size of a rendered scroll bar»*; §2.3 ⚠ **`screen.*` può legalmente restituire il viewport invece dello schermo**; `devicePixelRatio` = *«the size of a CSS pixel at the current page zoom and using a scale factor of 1.0»* ⇒ **lo zoom di pagina entra, il pinch no**; §12 `VisualViewport`; §13.1 gli eventi `resize` | `[S]` |
| W3C, **CSS Device Adaptation 2016** — <https://www.w3.org/TR/2016/WD-css-device-adapt-1-20160329/> | §6.2 `width = MAX(min-width, MIN(max-width, initial-width))`; §9.4 ⭐ *«device-width […] translate to 100vw […] which are the **window** dimensions»*; §11.2 l'origine del 980. ⚠ La spec attuale (CSS Viewport L1) ha §3 vuota: *«Specify me»* | `[S]` |
| Chrome for Developers — <https://developer.chrome.com/blog/url-bar-resizing> e <https://developer.chrome.com/blog/viewport-resize-behavior> | *«the ICB will not resize when the URL bar is hidden […] as if the URL bar were always showing»*; da Chrome 108 `interactive-widget: resizes-visual` di serie | `[S]` |
| Android Developers, *Window management* — <https://developer.android.com/topic/arc/window-management> | ⭐ *«If the window is not covering the full screen, requests for full screening […] are ignored»* | `[S]` |
| MDN, `Window.devicePixelRatio` — <https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio> | *«Page zooming affects the value […] Pinch-zooming does not»*; il modello `matchMedia("(resolution: N dppx)")` da ricreare | `[S]` |
| `src/pagina.html` righe 82, 94, 1030-1031, 1152-1161, 1399-1418, 1476-1500, 2115, 2145-2154, 5301, 5834 | il codice che misura, impagina, e i due difetti di §4 | `[R]` |
| `DECISIONI.md` §5.0-ter (righe 1803-1841) | il rilievo **S5** e la `[?]` sul DeX che §4.3 chiude | `[R]` |
| `PIANO.md` righe 290-293 | Samsung documenta l'emulatore DeX «alla densità e risoluzione equivalenti a DeX (**160 dpi**, 1080×1920)» | `[R]` di un `[S]` |
| `xpra.md` riga 122, `README.md` 531/599 | il monitor dell'utente è **21:9, 2560×1080** | `[R]` |

⚠ **Nessuna misura di questo rapporto è stata fatta su un DeX da me: il
dispositivo non c'è.** Tutto quel che è `[M]` viene da misure che **l'utente** ha
fatto col telefono in mano il 13 agosto e che erano già nel deposito. ⛔ Quel che
ho aggiunto è l'**aritmetica** e le **fonti**, e l'aritmetica su numeri veri non
è una deduzione: è un conto che chiunque può rifare.

---

## 9. ⭐ La pagina di prova — `banchi/04-dex-vista.html`

Scritta, sintassi verificata con `node --check`, **eseguita** `[M]` 14 agosto
2026 in Chrome headless a 1400×900: stampa la tabella, e la prima cosa che ha
detto è stata `innerWidth 1400` contro `clientWidth 1385` — ⭐ **i 15 px della
barra di scorrimento, misurati invece che citati** (T5).

**Che cosa misura**, in una tabella sola e in un riquadro grande:
`devicePixelRatio` · `visualViewport.{scale,width,height,offsetLeft,offsetTop,pageLeft,pageTop}` ·
`clientWidth/Height` · `innerWidth/Height` · `outerWidth/Height` ·
`screen.{width,height,availWidth,availHeight,orientation}` ·
`misura_vista()` verbatim dal prodotto · **la stessa corretta col fattore di
pagina** · `screen.width × dpr` (la formula S5, per confronto) ·
`document.fullscreenElement` **accanto a** `matchMedia("(display-mode: …)")` ·
`(resolution: N dppx)` · `screen.isExtended` · `980 ÷ dpr` (il 980 del foglio
dello UA, per riconoscere a occhio il caso di §2.2) · puntatore, sorvolo, tocco,
UA.
Si rimisura da sola su `resize`, su `visualViewport.resize/scroll`, su
`fullscreenchange` e sul cambio di risoluzione (media query riarmata).
C'è un bottone **schermo intero** e un bottone **copia**.

**Come si apre dal DeX** (⚠ porta 7911, sopra la 7900; non tocca 7448 / 7501 /
7561 / 7571 / 7700):

```bash
python3 -m http.server 7911 --bind 0.0.0.0 \
        --directory /home/nicfio/Documenti/REMOTIX_V2/banchi
# dal DeX, in Chrome:  http://192.168.0.2:7911/04-dex-vista.html
# poi: «copia tutto» e si incolla qui
# ⛔ e si spegne:  kill %1
```

⭐ **Le cinque righe da guardare, in quest'ordine:**

| riga | che cosa chiude |
|---|---|
| ⭐ **la vista dopo il bottone «schermo intero»** | ⛔ **la domanda che vale di più**: se `misura_vista()` arriva a **2560×1080**, la promessa *«a schermo intero torna 1:1»* di `SPECIFICHE.md` §6.1-bis è **mantenuta** su DeX e la scala è 1,000. Se si ferma sotto, §3.5 aveva ragione e la promessa va riscritta |
| `zoom_stimato` (a finestra **piena**) | la `[?]` di §6: se vale 1,2, l'1,2 è zoom di pagina e §4.3 è chiusa per sempre |
| `vv_scale` | la guardia di §2: se non vale 1, `misura_vista()` va corretta **anche su DeX** |
| `clientWidth` contro `innerWidth` | se su DeX la barra di scorrimento occupa spazio (§1.1 dice di no, per aritmetica) e se i browser controls decurtano l'altezza (§1.1, `[?]`) |
| `dm_fullscreen` contro `fullscreenElement` | se la cura di §4.2 — la media query al posto della geometria — regge su DeX |

⚠ **E un secondo giro che costa trenta secondi e chiude §6 da solo**: si rimette
lo zoom di Chrome al **100 %** e si riguarda. `dpr` deve passare da 1,2 a 1,0,
`clientWidth` da 2133 a 2560, e ⭐ **la vista deve restare 2560×926**. Se resta,
`misura_vista()` è invariante allo zoom sul ferro vero e non solo sulla carta.

⛔ **Il server sulla 7911 è stato acceso, verificato (`HTTP 200`) e spento**:
`ss -ltn` non lo trova più.

---

## 10. Che cosa direi al prossimo che legge

1. ⭐ **La misura 2560×926 è giusta e si riproduce al pixel** — l'unica cosa
   sbagliata del mandato era il **monitor**, ed era 2560×**1080**, 21:9.
2. ⛔ **La formula però è giusta per fortuna, non per costruzione.** `[R]`
   `clientWidth × dpr` è il **viewport di layout** in pixel fisici; che sia anche
   il vetro dipende da tre condizioni che il codice non controlla. Sullo **stesso
   telefono in mano** — il ripiego §7.2, dichiarato — sbaglia di **2,55 volte**,
   e la prova era già nel deposito da ieri.
3. ⛔ **Due difetti certi da curare**, righe 1030-1031 e 5301: tutt'e due sono la
   stessa cosa, cioè `screen.*` mescolato con `inner*`, e tutt'e due si vedono
   **solo** quando lo zoom di pagina non è 100 % — ⭐ **cioè solo sul dispositivo
   dell'utente**. E il secondo rende **impossibile** accorgersi dello schermo
   intero su DeX, cioè proprio dove serve.
4. ⭐ **Una `[?]` di `DECISIONI.md` §5.0-ter si chiude oggi** (§4.3): *«che cosa
   risponde DeX»* — risponde **come Chrome desktop, non come Firefox**, e la
   formula di `SPECIFICHE.md` §6.1-bis è rotta su DeX del **+20 %**.
5. ⚠ **E una `[?]` nuova si apre, che vale più di quella chiusa**: `[S]` in una
   finestra DeX Android **ignora** la richiesta di schermo intero se la finestra
   non copre già tutto. ⇒ **La promessa *«a schermo intero torna 1:1 e nitido»*
   di `SPECIFICHE.md` §6.1-bis è a rischio proprio sull'uso primario dichiarato**,
   e si chiude con **una misura di dieci secondi** — la pagina di §9, il bottone
   «schermo intero», e si legge se `clientHeight × dpr` arriva a 1080.
