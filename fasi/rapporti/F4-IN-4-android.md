# F4-IN-4 — Android e Samsung DeX, lato piattaforma

*Anello di studio della fase 4, 14 agosto 2026, sera. ⛔ Nessuna riga di `src/` toccata.*
*Mandato: chiudere la `[?]` su `cursor: none`, e rispondere alle otto domande del briefing.*
*⚠ Non ho un DeX: qui non c'è **nessuna** misura nuova sul ferro. Ci sono letture di sorgente
`[R]`, e una pagina di prova pronta da far girare all'utente (§10).*

---

## ⭐⭐⭐ Il verdetto, in tre righe

1. ⛔⭐⭐ **La frase è FALSA, e la causa vera è trovata**: `[R]` alle 15:09 la pagina ascoltava
   **solo `mousemove`** (`0075b4f:src/pagina.html:3909`, nessun `pointermove` — è entrato alle
   17:19), e su Samsung è documentato da quattro progetti che **Chrome consegna i `mousemove` solo
   al clic**. ⇒ *«4 clic e ZERO movimenti»* **è la definizione letterale di quel difetto**, e
   `cursor: none` non c'entra (§2.4, §8.2).
2. ⛔ **E non c'entra nemmeno come meccanismo**: nel framework Android l'icona del puntatore si
   risolve **DOPO** che l'evento è già stato consegnato alla `View` (`ViewRootImpl.java:8118-8119`),
   e nel percorso di consegna **non c'è una sola riga** che guardi l'icona (§1). ⇒ ⭐ **la cura c'è
   già** (`pointermove`, entrato la sera per un'altra ragione), e i «due puntatori sovrapposti» che
   il prodotto sopporta oggi sono un prezzo pagato **per niente**.
3. ⭐ **E la strada di xpra si riapre**, perché la seconda `[M]` che la chiudeva («sul DeX il cursore
   del browser non si veste») ⛔ **misurava codice mai eseguito**: `REMOTIX_PUNTATORE.forma()` non
   ha nessun chiamante (`pagina.html:2983-2989`). ⚠ Nessuna di queste tre righe è una misura sul
   DeX: la misura è scritta e pronta — `banchi/05-dex-cursore.html` (§10).

---

## ⭐⭐ Le due righe che cambiano il prodotto

> **1.** `[R]` **`git show 0075b4f:src/pagina.html`, riga 3909**: la versione in vigore alle 15:09
> registrava `mousemove` e **non** `pointermove` — `pointermove` è entrato alle **17:19**
> (`536e3d2`), cioè **dopo** la misura che ha fatto nascere la `[?]`. ⇒ *«4 clic e ZERO
> movimenti»* è il difetto Samsung documentato (§8.2: *«mousemove only fires on click»*), non
> `cursor: none`. ⭐ **La cura è già dentro il prodotto**, e nessuno sapeva che curava questo.

> **2.** `[R]` **`src/pagina.html:2983-2989`** — `CURSORE_FORMA` viene ricevuto e scartato con un
> `nota()`, e `REMOTIX_PUNTATORE.forma()` non è chiamato da nessuno. ⇒ La riga di xpra
> (`tela.style.cursor = "url(...)"`) **stava dentro `forma()`**: sul DeX non è mai partita. Il
> `[M]` «su Chrome per Android il cursore del browser non si veste» è la misura di un ramo morto,
> e la strada più economica che abbiamo — **una riga di CSS al posto di un fotogramma** — non è
> mai stata provata.

⭐ **Assenza certificata** (regola di `REVIEWER.md`): la ricerca
`grep -n "\.forma(\|CURSORE_FORMA" src/*.c src/*.h src/pagina.html` trova **il messaggio ovunque
nel server** — `rcp.c:3054` (`rcp_cursore_forma`), `webtransport.c:1571` (chi lo spedisce),
`cursore.c:520-533` (i contatori delle forme consegnate) — e **nel client trova solo il `nota()`
che lo butta**. ⇒ lo strumento vede quel che c'è; quel che manca è **il consumatore**.

---

## 1 · ⭐⭐⭐ La frase da refutare, e la catena letta fino in fondo

> **«Su Android/DeX, in Chrome, mettere `cursor: none` su un elemento toglie alla pagina anche gli
> eventi di movimento del puntatore. Quindi sul DeX non si può nascondere il cursore del browser.»**

### 1.1 Il primo tratto: `cursor: none` arriva davvero fino ad Android — ✅ confermato

⚠ Prima di smentire la conseguenza ho verificato la premessa, perché se `cursor: none` fosse un
no-op su Android la frase cadrebbe per un motivo diverso (e più banale). **Non lo è.**

| # | anello | `[R]` file:riga | che cosa fa |
|---|---|---|---|
| 1 | Blink sceglie il cursore | `third_party/blink/renderer/core/input/event_handler.cc:504-532` | `UpdateCursor()` → `SelectCursor()` → `view->SetCursor(...)`. ⛔ **Nessuna guardia `IS_ANDROID` in tutto il file** |
| 2 | il browser lo riceve | `content/browser/renderer_host/render_widget_host_view_android.cc:1374-1379` | `UpdateCursor()` chiama `view_.OnCursorChanged(cursor)` **senza condizioni** |
| 3 | | `content/public/common/content_features.cc:1450` | `BASE_FEATURE(kAndroidDisplayCursor, base::FEATURE_ENABLED_BY_DEFAULT)` — la via è **accesa di serie** |
| 4 | va in Java | `ui/android/view_android.cc:470-490` | `ViewAndroid::OnCursorChanged`: `kCustom` → `onCursorChangedToCustom(bitmap, hotspot)`, altrimenti `onCursorChanged(type)` |
| 5 | diventa un `PointerIcon` | `ui/android/java/src/org/chromium/ui/base/ViewAndroidDelegate.java:326-331` | `case CursorType.NONE: pointerIconType = PointerIcon.TYPE_NULL;` |
| 6 | e finisce sulla `View` | `ViewAndroidDelegate.java:447-451` | `PointerIcon icon = PointerIcon.getSystemIcon(...); containerView.setPointerIcon(icon);` |

⇒ ⭐ **`cursor: none` sul DeX diventa `PointerIcon.TYPE_NULL` sulla `View` di Chrome.** La premessa
della frase è **vera**, ed è l'unica parte che regge.

E `TYPE_NULL` **nasconde davvero** lo sprite: `[R]`
`frameworks/base/services/core/jni/com_android_server_input_InputManagerService.cpp:855-857` —
`if (type == PointerIconStyle::TYPE_NULL) { return PointerIcon(); }` (un'icona **vuota**), caricata
fra le risorse a `:1994-1995`. ⇒ lo sprite si disegna con un bitmap nullo. **Il cursore sparisce.**

### 1.2 ⭐⭐ Il secondo tratto — e qui la frase muore: l'ordine delle righe

`[R]` **AOSP `frameworks/base/core/java/android/view/ViewRootImpl.java`**, classe
`ViewPostImeInputStage`, metodo `processPointerEvent`:

```java
8118    handled = handled || mView.dispatchPointerEvent(event);   // ← l'evento È GIÀ ARRIVATO
8119    maybeUpdatePointerIcon(event);                            // ← l'icona si risolve DOPO
```

⇒ ⛔ **Il verso della causa è l'opposto di quello che dice la frase**: non è l'icona che decide se
l'evento arriva, è **l'arrivo dell'evento** che fa risolvere l'icona. Un'icona nulla è un **effetto**
del movimento, non una sua condizione.

E `maybeUpdatePointerIcon` (`ViewRootImpl.java:8153-8192`) non ha nessuna scorciatoia che possa
retroagire: filtra su `getPointerCount() != 1` e su `!event.isFromSource(SOURCE_MOUSE)`, e per il
resto **si limita a chiamare `updatePointerIcon(event)`**, che a `:8274-8283` fa

```java
if (Objects.equals(mResolvedPointerIcon, pointerIcon)) { return true; }   // ⇒ nessun binder
mResolvedPointerIcon = pointerIcon;
InputManagerGlobal.getInstance().setPointerIcon(pointerIcon, …);
```

⚠ Nota di costo, che vale per la strada di xpra (§6): finché l'icona **non cambia**, quel confronto
taglia via la chiamata a `system_server`. ⇒ tenere `cursor: none` (o un cursore custom **fermo**)
**non costa niente per movimento**.

### 1.3 Il terzo tratto: il percorso dell'evento non guarda mai l'icona

`[R]` **`frameworks/native/services/inputflinger/PointerChoreographer.cpp`** — è il pezzo nuovo di
Android 14/15 che possiede il puntatore, ed è quello che il mandato chiedeva di guardare:

```cpp
173  void PointerChoreographer::notifyMotion(const NotifyMotionArgs& args) {
174      NotifyMotionArgs newArgs = processMotion(args);
175
176      mNextListener.notify(newArgs);          // ← INCONDIZIONATO
177  }
```

`processMotion` → `processMouseEventLocked` (`:232-260`) sposta la posizione del cursore
(`pc.setPosition(...)` / `processPointerDeviceMotionEventLocked`) e **restituisce l'evento**.
⛔ **Non esiste nessun ramo che scarti l'evento**, per nessun valore dell'icona.

E `PointerChoreographer::setPointerIcon` (`:880-930`) tocca **solo** il controller dello sprite
(`setIconForController` → `controller.updatePointerIcon(...)` / `setCustomPointerIcon(...)`,
`:76-85`). ⇒ **l'icona e il flusso degli eventi sono due strade che non si incrociano.**

⭐ **L'assenza, certificata** (`REVIEWER.md`): su
`frameworks/native/services/inputflinger/dispatcher/InputDispatcher.cpp` (7 335 righe)

- controprova che lo strumento vede: `grep -c "ACTION_HOVER_MOVE"` ⇒ **7**;
- ricerca vera: `grep -i "pointericon|PointerIconStyle|sprite|updatePointerIcon"` ⇒ **zero righe**.
  L'unica funzione imparentata è `isPointerInWindow` (`:7310`), che il **setter** dell'icona usa
  per rifiutare una richiesta da una finestra su cui il puntatore non sta
  (`com_android_server_input_InputManagerService.cpp:1608-1620`) — cioè l'icona dipende dagli
  eventi, ancora una volta, e mai il contrario.

Infine il disegno: `[R]` `frameworks/base/libs/input/MouseCursorController.cpp:68-85` —
`move()` aggiorna la posizione **prima e indipendentemente** da qualunque icona o trasparenza; e
`updatePointerLocked()` (`:361-411`) è l'unico punto in cui l'icona tocca qualcosa, e quel qualcosa
è `mLocked.pointerSprite->setIcon(...)`.

### 1.4 ⇒ Il verdetto sulla frase

| tratto | esito |
|---|---|
| `cursor: none` diventa `PointerIcon.TYPE_NULL` su Android | ✅ **vero** `[R]` (§1.1) |
| `TYPE_NULL` nasconde davvero il cursore di sistema | ✅ **vero** `[R]` (§1.1) |
| nasconderlo toglie alla `View` gli `ACTION_HOVER_MOVE` | ⛔ **FALSO** `[R]` (§1.2, §1.3) |
| … e nemmeno sperimentalmente | ⛔ **FALSO** `[R]` (§8.2: riprodotto senza `cursor`, e il cursore visibile non cura) |
| ⇒ «sul DeX non si può nascondere il cursore» | ⛔ **non dimostrato, contraddetto, e senza meccanismo** |

⭐ ⇒ **La strada «il puntatore lo disegniamo noi nella pagina» NON è preclusa**, e l'affermazione
scritta oggi in `src/pagina.html:254-258` va **declassata**: non è una `[?]` con un meccanismo
plausibile, è una `[?]` con un meccanismo **letto e smentito**.

⚠ Quel che resta vero e va tenuto: la **correlazione** è forte e non è spiegata. §2 dice dove
guardare.

---

## 2 · ⚠ La variante alternativa — e sono quattro, non una

*Il mandato chiede di escludere o confermare «qualcos'altro che è cambiato insieme». Ho guardato
il codice vero al commit di quel giorno.*

### 2.1 ⛔ Escluse leggendo

| ipotesi | esito | prova |
|---|---|---|
| **la freccia disegnata copriva il bersaglio** e rubava gli eventi | ⛔ **esclusa** | `[R]` `src/pagina.html:271-272`: `#puntatore { position: fixed; … pointer-events: none; }` — non è mai un bersaglio di hit-test |
| **un `touch-action` cambiato insieme** | ⛔ **esclusa** | `[R]` `touch-action` è messo **solo** dal modo a TOCCO, da JavaScript (`src/pagina.html:5150-5163`), e il DeX è in modo CLASSICO |
| **un `preventDefault()` nuovo** | ⛔ **già esclusa da `F4-AND-1` §3.1** | `[R]` il flag `prevent_mouse_event_for_pointer_type_` si arma **prima** che il `mousedown` esista, e `[S]` PE2 §11: *«Hovering pointers … cannot have their mouse events prevented»* |
| **il fuoco preso da un altro elemento** | ⛔ **esclusa dai fatti della misura stessa** | i **4 clic** sono arrivati, e `cl_su_mousedown` è registrato **sulla tela** (`src/pagina.html:4207`) e comincia con `if (!cl_utilizzabile()) return;` (`:3958`) ⇒ la tela era il bersaglio, il modo era in vigore, il fuoco non c'entra |

### 2.2 ⭐⭐ Quel che invece regge: «ZERO movimenti» **non è** «zero eventi»

⛔ Il numero della misura del 15:09 conta **messaggi arrivati al server**, non eventi del DOM: il
server registra ogni input per tipo (`src/rcp.c:2867` e il `reg()` per `T_PUNTATORE`), e non esiste
nessun contatore di eventi DOM che sia uscito da quella sessione.

Fra l'evento del browser e quel conteggio ci sono **cinque filtri della pagina**, tutti nostri:

| # | `[R]` `src/pagina.html` | che cosa può azzerare il conto |
|---|---|---|
| 1 | `:3900` `if (ev.pointerType === "touch") return;` | un `pointerType` diverso da quel che crediamo |
| 2 | `:3906` `if (!cl_utilizzabile()) return;` | ⛔ escluso: i clic passano dalla stessa guardia |
| 3 | `:3940-3946` `if (!g.vx || !g.vy || !g.sx || !g.sy) { cl_ripiego(…); return; }` | **geometria degenere ⇒ zero messaggi e zero disegno** |
| 4 | `:3947-3950` + `cl_satura()` `:3650-3657` | un `cl_px` calcolato **negativo ovunque** viene saturato a **0** |
| 5 | ⭐ `:3670` `if (x === cl_ux && y === cl_uy) return null;` | **un puntatore che non cambia pixel non spedisce**: con `cl_px` inchiodato a 0, **ogni** movimento è muto |

⚠ ⇒ **Il numero «ZERO» non distingue «l'evento non è arrivato» da «l'evento è arrivato e l'abbiamo
buttato noi».** Il posto giusto dove contare è **il gestore**, e nessuno ci contava. §2.4 dice
quale delle due è, e la prova 1 di §10 lo conferma sul ferro.

⚠ **Un dettaglio che NON so spiegare**, e lo dichiaro: il punto di ripresa dice che *«la freccia è
rimasta piantata nell'angolo dell'immagine»*. `[R]` Se `cl_su_mousemove` non è mai partito,
`cl_noto` resta falso e `cl_disegna()` mette `display: none` (`src/pagina.html:3706`) — cioè la
freccia **non si sarebbe vista affatto**. ⇒ o qualcosa ha chiamato `REMOTIX_PUNTATORE.muovi()`
(il percorso del tocco lo fa), o «piantata nell'angolo» descrive un'altra cosa. **Non lo risolvo da
qui.**

### 2.3 ⚠ E «una variabile sola» non è vero

`[R]` La stessa modifica del 15:07 ha toccato **due** cose, e la seconda è scritta nel codice di
oggi: `src/pagina.html:3716-3719` — *«QUI C'ERA IL NASCONDIGLIO, tolto la sera del 14 agosto dalla
stessa misura che ha rimesso il `cursor: none`»*. Cioè insieme a `cursor: none` è stato **tolto il
ritorno anticipato di `cl_disegna()`**. ⇒ la premessa «una variabile sola cambiata» **non regge
alla lettura del deposito**, e un esperimento a due variabili non attribuisce a nessuna delle due.

⚠ E c'è un terzo motivo per non fidarsi del confronto: fra una sessione e l'altra il server va
riavviato perché **la pagina si legge una volta sola all'avvio** (`pagina.c:627`, citato nel punto
di ripresa) — cioè le «quattro sessioni precedenti» e quella delle 15:09 non sono lo stesso
programma con un CSS diverso: sono cinque avvii.

### 2.4 ⭐⭐⭐ LA CAUSA, e il deposito la conteneva già: **alle 15:09 la pagina non ascoltava `pointermove`**

*Questa è la cosa che vale l'intero rapporto, e si legge in git in trenta secondi.*

`[R]` **Nella versione in vigore alle 15:09 il modo classico ascoltava `mousemove` e basta.**
`git show 0075b4f:src/pagina.html`, righe 3909-3912:

```js
  tela.addEventListener("mousemove", cl_su_mousemove);
  tela.addEventListener("mousedown", cl_su_mousedown);
  tela.addEventListener("wheel", cl_su_wheel, { passive: false });
  tela.addEventListener("contextmenu", cl_su_contextmenu);
```

⛔ **Nessun `pointermove`.** E la datazione è netta:

| commit | ora | `addEventListener("pointermove")` | `cursor: none` sul classico |
|---|---|---|---|
| `dd0b163` | 11:45 | **0** | su **tutto** il modo classico |
| `0075b4f` | 15:34 (ma è lo stato di **prima** delle 15:07) | **0** | ristretto a `[data-agganciato="si"]` |
| `536e3d2` | **17:19** | **1** ⭐ | ristretto |

⇒ ⭐⭐ **`pointermove` è entrato nel prodotto la SERA, DOPO la misura delle 15:09** — e con lui il
commento `[M]` sui «dodici secondi», che infatti compare **solo** in `536e3d2`.

### ⇒ E adesso i due fatti si incastrano

`[R]` §8.2, il difetto documentato di Samsung, con le parole del segnalatore di noVNC #1727:

> *«**`mousemove` only fires on click** indeed. … it seems specific to Chrome on Samsung devices»*

`[M]` La misura delle 15:09: **4 clic** (dal `mousedown`, che funziona) e **ZERO movimenti** (dal
`mousemove`, che su Samsung muore).

⇒ ⭐⭐⭐ **«4 clic e zero movimenti» su una pagina che ascolta SOLO `mousemove`, su un dispositivo
Samsung, è la definizione letterale del difetto Samsung.** Non serve `cursor: none` per spiegarlo,
e `cursor: none` non lo spiegherebbe comunque (§1, §8).

⚠ **E spiega anche perché le quattro sessioni precedenti erano andate**: sono tutte sessioni
`mousemove`-only, e il difetto Samsung è **intermittente** — nella stessa segnalazione l'autore lo
vede sul suo S22 e tre sviluppatori Kasm **non riescono a riprodurlo** su quattro Samsung diversi.
⇒ **165 · 227 · 320 · 200 e poi 0 non è una variabile che cambia: è un difetto che va e viene.**

### ⇒ E la cura c'è già, messa quella sera stessa senza sapere che era questa

`[R]` `536e3d2` aggiunge `tela.addEventListener("pointermove", cl_su_pointermove)`
(`src/pagina.html:4206`), che è l'evento **primario** e non di compatibilità. ⭐ **La cura del
difetto delle 15:09 è entrata due ore dopo, per un'altra ragione, e nessuno ha collegato le due
cose.** ⇒ ⛔ **Il `cursor: none` è stato ristretto per un motivo che non esiste**, e il prezzo che
il prodotto paga oggi — *«due puntatori sovrapposti»*, scritto in `src/pagina.html:260-264` — è un
prezzo pagato **per niente**.

---

## 3 · ⭐ Il cursore di sistema su DeX: chi lo disegna, a che ritmo, e perché *sembra* funzionare

*È la domanda n. 1 del mio mandato, ed è quella che spiega il sintomo dell'utente meglio di
qualunque altra.*

`[R]` **Il cursore del DeX è una superficie di SurfaceFlinger, non un disegno dell'applicazione.**

- `frameworks/base/libs/input/SpriteController.cpp:343-365` — lo sprite è creato con
  `mSurfaceComposerClient->createSurface(String8("Sprite"), …)` e i flag
  `ISurfaceComposerClient::eHidden | ISurfaceComposerClient::eCursorWindow`. ⭐ **`eCursorWindow`**
  è il flag che permette al compositore di metterlo su un piano dedicato del display.
- `frameworks/base/libs/input/MouseCursorController.cpp:361-378` — a ogni movimento si apre una
  `SpriteController` transaction e si fa `pointerSprite->setPosition(x, y)` con
  `setLayer(Sprite::BASE_LAYER_POINTER)` (`SpriteController.h:67`).
- Chi lo muove è `PointerChoreographer::processMouseEventLocked`
  (`services/inputflinger/PointerChoreographer.cpp:232-260`), che sta **prima** di `InputDispatcher`
  nella catena dell'input, cioè **prima** che l'evento parta verso l'applicazione.

⇒ ⭐⭐ **Il cursore di DeX si muove al ritmo del mouse (i rapporti del dispositivo, tipicamente
125 Hz su Bluetooth), su un thread di sistema, e non aspetta né il fotogramma dell'applicazione né
il `Choreographer` dell'applicazione.** È **completamente indipendente** dalla finestra di Chrome.

⭐ **Ed è la risposta a «perché sul DeX il puntatore sembra funzionare mentre il desktop remoto è
fermo»**: l'utente vede una freccia liscia a 125 Hz disegnata dal sistema operativo, sopra
un'immagine che arriva a **1,1 fotogrammi al secondo** `[M]`. La freccia non è una prova che
qualcosa funzioni: è **l'unica cosa nella scena che non passa da noi**.

⚠ Due comportamenti di sistema che vale la pena conoscere, e che nessuno dei rapporti precedenti
nomina:

1. `[R]` `PointerChoreographer.cpp:168-203` `fadeMouseCursorOnKeyPress` — **Android sbiadisce il
   cursore del mouse quando si digita**, ma **solo** se `mPolicy.isInputMethodConnectionActive()`.
   ⇒ su una pagina senza nodo modificabile col fuoco (che è il nostro caso, `F4-AND-2` §1) **non
   scatta**. Un cursore che sparisse mentre l'utente scrive **non** sarebbe questo.
2. `[R]` `PointerChoreographer.cpp:433-445` — toccare lo schermo **sbiadisce il cursore su quel
   display**. Sul DeX col monitor sono display diversi, quindi toccare il telefono non tocca la
   freccia sul monitor; ⚠ ma **se il telefono fa da trackpad** l'evento arriva sul display del
   monitor come touchpad (`processTouchpadEventLocked`, `:265-292`) e il cursore si **riaccende**,
   non si spegne.

---

## 4 · `requestPointerLock` su Android e DeX

### 4.1 Funziona — e la fonte che dice di no è vecchia

`[R]` `content/browser/renderer_host/render_widget_host_view_android.cc:2672-2692`:

```cpp
blink::mojom::PointerLockResult RenderWidgetHostViewAndroid::LockPointer(
    bool request_unadjusted_movement) {
  if (!base::FeatureList::IsEnabled(blink::features::kPointerLockOnAndroid)) {
    NOTIMPLEMENTED();
    return blink::mojom::PointerLockResult::kUnsupportedOptions;
  }
  ui::WindowAndroid* window_android = view_.GetWindowAndroid();
  if (!window_android || !window_android->RequestPointerLock(view_)) {
    return blink::mojom::PointerLockResult::kWrongDocument;
  }
  …
  return blink::mojom::PointerLockResult::kSuccess;
}
```

e `[R]` `third_party/blink/renderer/platform/runtime_enabled_features.json5:4682-4686`:
`name: "PointerLockOnAndroid", status: "stable"` ⇒ **acceso di serie**.

⚠ **E qui due fonti si contraddicono, e lo dichiaro invece di scegliere**: `[S]`
`mdn/browser-compat-data#19829` dice *«Chrome for Android does not support the Pointer Lock API …
seems like essentially a no-op»*. ⛔ È una segnalazione **precedente** al flag che ho appena letto.
⇒ **il sorgente di oggi dice che funziona, la tabella di compatibilità dice di no**, e questa è
esattamente la situazione in cui `F4-AND-2` §—23 avvertiva che *«la tabella di compatibilità non è
una fonte»*. **Si misura** (prova 5 di §10).

`[R]` La catena: `ui/android/window_android.cc:359-373` → `WindowAndroid.java:1696-1728`, con il
commento che chiude la questione — *«Pointer lock API equivalent on Android is called pointer
capture»* — e `view.requestPointerCapture()`. Rilascio a `WindowAndroid.java:1763`.
⚠ `[R]` La cattura **si perde quando la finestra perde il fuoco** (`ViewRootImpl.java:4722-4725`) —
e su DeX, che è un desktop a finestre, il fuoco si perde spesso.

### 4.2 Che cosa succede al cursore di sistema: sparisce, su TUTTI i display

`[R]` `frameworks/native/services/inputflinger/PointerChoreographer.cpp:599-608`,
`notifyPointerCaptureChanged`: se la cattura si accende, per **ogni** controller in
`mMousePointersByDisplay` si fa `fade(Transition::IMMEDIATE)`.
⇒ ⭐ **con Pointer Lock attivo il cursore del DeX sparisce da solo**, senza nessun `cursor: none`.
E `[R]` `CursorInputMapper.cpp:459-474` cambia la sorgente in `AINPUT_SOURCE_MOUSE_RELATIVE`, e
`:479-482` **spegne l'accelerazione** (*«Disable any acceleration or scaling for the pointer when
Pointer Capture is enabled»*).

### 4.3 ⛔⭐ Ma `movementX` su Android è una FINZIONE ricostruita, e va detto

`[R]` `ui/android/java/src/org/chromium/ui/base/PointerLockEventHelper.java:52-108`: Chromium prende
il delta relativo, lo **somma a una posizione che tiene lui**, riscrive la sorgente a
`SOURCE_MOUSE` e manda avanti un normalissimo movimento assoluto:

```java
        float currentPointerPositionX = mLastPointerPositionX + offsetX;
        …
        MotionEvent ret = MotionEvent.obtain(event);
        ret.setSource(InputDevice.SOURCE_MOUSE);
        ret.setLocation(currentPointerPositionX, currentPointerPositionY);
```

⇒ `is_raw_movement_event` resta **falso** (`components/input/web_input_event_builders_android.cc`:
**zero** occorrenze di `movement` in 311 righe, con controprova che lo strumento vede
`AINPUT_SOURCE_MOUSE_RELATIVE` a `:57` e `:259`), e Blink calcola `movementX` **per sottrazione di
`PositionInScreen`, troncata a intero** (`mouse_event_manager.cc:59-75`, `UpdateMouseMovementXY`;
gemello per i `PointerEvent` in `core/events/pointer_event_factory.cc:88-105`).

⭐ **Questo raffina D6 di `F4-AND-1`** (che dava `movementX` in DIP di schermo, «senza dividerlo per
lo zoom»): su Android non è nemmeno un delta del dispositivo, è **la differenza fra due posizioni
di schermo di Blink**, con tre conseguenze `[R]`:

1. **troncamento a intero prima della sottrazione** (`saturated_cast<int>` su tutt'e due i termini):
   i movimenti sotto il pixel si perdono;
2. ⛔ **i micro-movimenti spariscono del tutto**: `EventForwarder.java:873-879` **non inoltra**
   l'evento se la posizione ricostruita coincide con la precedente;
3. la posizione ricostruita **non è ritagliata** ai bordi della `View`
   (`PointerLockEventHelper.java:102-103`) — può uscire indefinitamente.

⇒ ⛔ **`CL_GUADAGNO` tarato su una macchina non si trasporta sul DeX**, e la formula di
`cl_su_mousemove` con la cattura accesa (`src/pagina.html:3925-3926`) tratta `movementX` come pixel
CSS della tela sul vetro: ⚠ sbagliato in linea di principio, **ma per caso quasi giusto su DeX**,
perché lì lo spazio di `PositionInScreen` e quello del vetro differiscono solo per lo zoom di
pagina (1,2) — cioè un errore del **20 %**, non di un fattore.

### 4.4 ⇒ Che cosa ne faccio

⛔ **Non è la cura del mouse.** Tre ragioni, tutte `[R]`: la cattura si perde al cambio di fuoco
(§4.1) — e su un desktop a finestre succede; `movementX` è ricostruito e tronca (§4.3); e ⭐
`SPECIFICHE.md:644` dice che il puntatore è **assoluto ed è l'unico percorso**, cioè i delta non ci
servono. ⚠ E l'utente l'ha già respinta a parole: *«sembra che il puntatore venga catturato dal
desktop virtuale»*.
⭐ **Resta utile per una cosa sola**, ed è già com'è oggi: un'opzione a mano
(`REMOTIX.input_classico.aggancia()`), come in xpra dove la cattura è un bottone `[R]`.

---

## 5 · ⭐⭐ Il ritmo degli eventi del mouse su DeX — e una cosa che nessuno aveva letto

*`F4-AND-1` §3.5 ha già stabilito che `getCoalescedEvents()`, `pointerrawupdate` e
`getPredictedEvents()` **esistono** su Chrome per Android (58 / 77 / 77) e che `pointermove` è
allineato a `requestAnimationFrame`. ⛔ Non lo ripeto. Quel che segue è il tratto **sotto** Blink,
che nessun rapporto aveva guardato.*

### 5.1 Android accorpa anche i movimenti del MOUSE, non solo quelli del dito

⚠ `F4-AND-5` §—15 aveva scritto che Android accorpa *«any MOVE event that has source =
TOUCHSCREEN»*. `[R]` Sul sorgente di oggi **non è più così**:

`frameworks/native/libs/input/InputConsumerNoResampling.cpp:355-358`

```cpp
const bool batchableEvent = (action == AMOTION_EVENT_ACTION_MOVE ||
                             action == AMOTION_EVENT_ACTION_HOVER_MOVE) &&
        (isFromSource(source, AINPUT_SOURCE_CLASS_POINTER) ||
         isFromSource(source, AINPUT_SOURCE_CLASS_JOYSTICK));
```

`AINPUT_SOURCE_MOUSE` **contiene** `AINPUT_SOURCE_CLASS_POINTER`. ⇒ ⭐ **gli `ACTION_HOVER_MOVE` del
mouse vengono messi in un lotto** e consumati al fotogramma del `Choreographer` dell'applicazione —
che su DeX è a **60 Hz** (`F4-AND-3`: il DeX gira a 60 Hz contro i 120 del pannello del telefono).

### 5.2 ⛔⭐ E Chrome BUTTA VIA il contenuto del lotto, per il mouse

`[R]` `ui/android/event_forwarder.cc:178-224`, `EventForwarder::OnMouseEvent`:

```cpp
  auto event = ui::MotionEventAndroidFactory::CreateFromJava(
      …
      /*pointer_count=*/1,
      /*history_size=*/0,          // ← riga 208
      …
```

con il commento, due righe sopra: *«Construct a motion_event object minimally… Since we used only
the cached values at index=0»*.

⚠ **Controprova nello stesso file**: il percorso del **tocco** legge davvero la storia —
`event_forwarder.cc:80-81` `int32_t history_size = Java_MotionEvent_getHistorySize(env,
motion_event);` — e anche il lato Java lo fa solo per il tocco
(`EventForwarder.java:300` `final int historySize = event.getHistorySize();` dentro
`sendTouchEvent`), mentre `sendNativeMouseEvent` (`EventForwarder.java:519-557`) passa **solo**
`event.getX()`/`getEventTimeNanos(event)`. ⇒ **lo strumento vede la storia dove c'è: per il mouse
non c'è perché è stata scartata.**

⇒ ⭐⭐ **Conseguenze, e sono tre, tutte nuove:**

1. **Sul DeX la pagina non può vedere più di ~60 posizioni del mouse al secondo**, qualunque cosa
   faccia. Il tetto **non è** l'allineamento a rAF di Blink: è **due stadi più a monte**, nel
   consumatore di input dell'applicazione.
2. ⛔ **`getCoalescedEvents()` su DeX, con un mouse, restituirà quasi sempre `[1]`**: i campioni
   intermedi che Android aveva accorpato sono già stati buttati da `history_size = 0`. ⇒ la
   conclusione di `F4-AND-1` §3.5 («per noi non serve a niente») resta giusta, **ma per un motivo
   più forte di quello che c'era scritto**: non è che non ci serve, è che **non c'è niente dentro**.
3. ⚠ **`pointerrawupdate` guadagna meno di quel che promette**: `[S]` la spec dice *«as soon as
   possible and as frequently as the JavaScript can handle»*, ma su Android l'evento nasce da un
   `WebMouseEvent` che è già stato consegnato a lotti di 16,7 ms. ⇒ il mezzo fotogramma di latenza
   che si toglie a Blink è vero; i «movimenti in più» **no**.

⭐ **Che cosa vale davvero, allora**: la posizione **assoluta** dell'ultimo evento del lotto è
sempre quella giusta (`getX()` al momento del consumo), e noi mandiamo **una posizione assoluta**.
⇒ **non perdiamo precisione, perdiamo solo campioni intermedi che non ci servono.**
⛔ **Non conviene spendere una riga né su `getCoalescedEvents()` né su `getPredictedEvents()`.**

⚠ `[?]` **Esiste una via d'uscita al tetto dei 60 Hz e non l'ho potuta chiudere**:
`View.requestUnbufferedDispatch()` spegne l'accorpamento. Chromium ha l'impalcatura
(`ui/android/view_android.cc:343-350` → `ViewAndroidDelegate.java:571-590`) ⛔ **ma non ho trovato
il chiamante sul percorso del mouse** (cercato in `render_widget_host_view_android.cc`,
`gesture_listener_manager.cc`, `motion_event_android.cc`: zero). Lo dichiaro `[?]`, non «non
esiste»: non ho certificato lo strumento su tutto l'albero.

---

## 6 · ⭐⭐ Il cursore CSS personalizzato `cursor: url(...)` — la strada di xpra

*Era la domanda n. 4 del mandato, con la nota «se funziona su DeX vale più di tutte le altre».
⭐ **Sul sorgente non c'è NIENTE che la impedisca su Android**, e la `[M]` che la dava per morta
misurava un ramo mai eseguito (§0).*

### 6.1 Il percorso esiste, per intero, e non ha guardie

| anello | `[R]` file:riga | che cosa fa |
|---|---|---|
| Blink | `event_handler.cc:696-762` | accetta/rifiuta il bitmap, calcola il punto attivo |
| `ui::Cursor` | `ui/base/cursor/cursor.cc:47-59` | **ritaglia il punto attivo** dentro il bitmap (`std::clamp`) |
| Android | `ui/android/view_android.cc:475-486` | `kCustom` ⇒ `onCursorChangedToCustom(bitmap, hotspot.x, hotspot.y)` |
| Java | `ViewAndroidDelegate.java:314-322` | `PointerIcon.create(bitmap, hotspotX, hotspotY)` + `setPointerIcon` |
| AOSP | `PointerIcon.java:343-355` | ⛔ **nessun limite di dimensione**: valida **solo** il punto attivo (`:599-611`) |
| sistema | `com_android_server_input_InputManagerService.cpp:2846-2865` | `TYPE_CUSTOM` ⇒ `SpriteIcon` col bitmap copiato ⇒ sprite di SurfaceFlinger |

⭐ **Assenza certificata** (regola di `REVIEWER.md`): in `ViewAndroidDelegate.onCursorChangedToCustom`
non c'è **nessun** `Build.VERSION.SDK_INT`, nessun `@RequiresApi`, nessun controllo di dimensione —
e la controprova è che nello **stesso file** i guard di versione esistono e il grep li trova
(`:580` `SDK_INT <= R`, `:724` `SDK_INT < BAKLAVA`). ⇒ ⭐ **`cursor: url(...)` non ha una versione
minima di Android.**

### 6.2 ⚠ I due limiti di dimensione, e sono di Blink, non di Android

| limite | valore | `[R]` | effetto |
|---|---|---|---|
| **duro** | **128 DIP** | `ui/base/cursor/cursor.cc:93-106`, `AreDimensionsValidForWeb` | oltre, il cursore è **scartato** e resta quello di prima |
| **morbido** | **32 DIP** | `event_handler.cc:260-263`, `kMaximumCursorSizeWithoutFallback` | fra 33 e 128 il cursore vale **solo se sta tutto dentro il visual viewport** (`:726-758`) |

⚠ **Il secondo limite ci riguarda davvero**: un cursore di 48 px vicino al bordo dell'immagine
sparirebbe **a intermittenza**, e sarebbe una cosa che sembra un difetto nostro. ⇒ ⭐ **stare a
≤ 32 px** e ripiegare sulla freccia disegnata quando la forma remota è più grande. `[R]` I cursori
di GNOME sono tipicamente 24 o 32: ci si sta.

⚠ **Un difetto vero, trovato leggendo**: `[R]` `view_android.cc:475-486` passa il bitmap **grezzo** e
⛔ **non legge mai `cursor.image_scale_factor()`** — il fattore di scala calcolato da Blink viene
**buttato al confine JNI**. ⇒ un cursore dichiarato per 2× arriva ad Android come bitmap e basta, e
Android lo disegna 1:1 in pixel del display: su DeX (dpr 1,2) un cursore di 32 px CSS si vede
**26,7 px CSS**. Piccolo, ma da sapere prima di stupirsi.

### 6.3 Il punto attivo è rispettato — e per costruzione non può essere sbagliato

`[R]` `event_handler.cc:707-708` porta il punto attivo da DIP a pixel fisici
(`gfx::ScaleToRoundedPoint(cursor.HotSpot(), scale)`); `cursor.cc:47-59` lo **ritaglia** dentro il
bitmap; `view_android.cc:477` lo passa intero a `PointerIcon.create`; AOSP lo rivalida
(`PointerIcon.java:599-611`, *«x hotspot lies outside of the bitmap area»*). ⇒ ✅ **il punto attivo
arriva, e se fosse fuori il bitmap la creazione tirerebbe un'eccezione invece di sbagliare in
silenzio.** ⭐ È esattamente quel che serve a `CURSORE_FORMA`, che il punto attivo lo porta già
(`RCP.md` §7.2, campi `punto_x`/`punto_y`; il server lo controlla, `rcp.c:3103`).

### 6.4 ⚠ Il costo per movimento: zero, se la forma non cambia

`[R]` `ViewRootImpl.java:8274-8276`: `if (Objects.equals(mResolvedPointerIcon, pointerIcon)) return
true;` ⇒ finché l'icona è la stessa, **nessuna chiamata a `system_server`**.
⚠ Ma `PointerIcon.equals` (`PointerIcon.java:450-461`) confronta il bitmap **per riferimento**
(`mBitmap != otherIcon.mBitmap`), e Chromium crea un `PointerIcon` **nuovo** a ogni cambio di forma
(`ViewAndroidDelegate.java:319`). ⇒ **ogni cambio di forma costa** una conversione JNI del bitmap,
un binder a `system_server` e una transazione di SurfaceFlinger. Su un desktop remoto la forma
cambia a ogni bordo di finestra: ⭐ **si spedisce solo quando cambia davvero** — e `[R]` il server
lo fa già (`cursore.c` conta `uguali` fra i metadati e non le rimanda).

### 6.5 ⇒ La cura, e costa poche righe

1. `[R]` chiamare `REMOTIX_PUNTATORE.forma(...)` da dove oggi c'è il `nota()`
   (`src/pagina.html:2983-2989`): il messaggio arriva, la funzione c'è, **manca il filo fra i due**
   — è la stessa forma di difetto di `F5-desktop-vero.md`, la sesta volta in questa fase;
2. rimettere in `forma()` la riga di xpra `tela.style.cursor = "url(<data>) x y, auto"`
   (`src/pagina.html:3776-3781` dice dov'era), ⚠ **con il ripiego `, auto` in coda** — che non è una
   formalità: se il bitmap supera i limiti di §6.2 il CSS scarta la voce e senza la seconda l'utente
   resta senza cursore;
3. **solo se ≤ 32 px**, altrimenti la freccia disegnata.

⛔ **Ma prima si misura** (prova 3 di §10): tre progetti su cinque `[R]` nascondono il cursore su
Android e nessuno lo veste, e l'unica prova che abbiamo che si vesta è **il sorgente**, non un DeX.

---

## 7 · DeX come piattaforma: che cosa cambia per l'input

*⛔ `F4-AND-3` ha già spiegato l'1,2 (è lo **zoom di pagina** al 120 %, con la densità del DeX a
160 dpi ⇒ fattore di dispositivo 1,0), i 154 px mancanti, e che «schermo intero» su DeX vuol dire
«a tutta finestra», non «a tutto monitor». **Non lo ripeto: lo uso.***

**Per l'input, fra finestra affiancata e schermo intero, dal lato Android non cambia niente**, e la
ragione è nel sorgente:

- `[R]` il puntatore è **per display**, non per finestra: `PointerChoreographer` tiene
  `mMousePointersByDisplay` (`PointerChoreographer.cpp:880-920`), e i limiti del movimento sono
  quelli del **viewport del display** — `MouseCursorController.cpp:95-105` `getBoundsLocked()`
  ritorna `viewport.logicalLeft/Top/Right-1/Bottom-1`. ⇒ **il cursore è ritagliato sul monitor, mai
  sulla finestra**, e lo schermo intero non cambia il suo spazio.
- `[R]` la finestra riceve gli eventi solo mentre il puntatore le sta sopra (l'hit-test di
  `InputDispatcher`), e le coordinate che Chrome usa sono quelle **relative alla finestra**
  (`event_forwarder.cc:193-196` usa `source->GetXPix(0)`, cioè `MotionEvent.getX()`, e calcola lo
  scostamento verso `getRawX()` solo per i campi `raw`). ⇒ **la barra del titolo di DeX non entra
  nelle nostre coordinate**: entra solo nel fatto che la finestra è alta 926 e non 1080.
- ⚠ `[R]` `ViewRootImpl.java:8256-8259`: se il punto è fuori dai limiti della `View`,
  `updatePointerIcon` **rinuncia e lo scrive nel log** (*«updatePointerIcon called with position out
  of bounds»*). È l'unico effetto di bordo della finestra che ho trovato, e riguarda **l'icona**,
  non gli eventi.

⇒ ⭐ **Per l'input, lo schermo intero su DeX non compra niente.** Quel che compra (la vista che
cresce, le bande che si riducono) è tutto geometria, ed è già scritto in `F4-AND-3`.

---

## 8 · ⭐⭐⭐ I difetti aperti a monte — e qui c'è la prova SPERIMENTALE che la frase è falsa

*⚠ `F4-AND-1` §6.3 dichiarava che le pagine di `issues.chromium.org` **non erano leggibili** con gli
strumenti disponibili. ⭐ **Lo sono**: il contenuto della segnalazione è incorporato nell'HTML in
`var defrostedResourcesJspb = [...]`, e si prende con `curl`. ⛔ **I commenti no**: sette punti
d'accesso provati, tutti 404/405/401. ⇒ qui sotto **titolo, stato, date e descrizione** sono letti;
**i commenti no, e non li invento.***

### 8.1 I quattro difetti che `F4-AND-1` citava senza poterli aprire

| id | titolo (letterale) | stato | date | commenti (⛔ non letti) |
|---|---|---|---|---|
| **502461774** | *«Samsung DeX phone-as-trackpad mode not detected by isRealPointerDevice() hover heuristic»* | ⭐ **APERTO** (assegnato) | 14 apr 2026 | 3 |
| **41445959** | *«Some Androids reporting hover: hover»* | **CHIUSO, corretto** | 10 mar 2019 → **17 apr 2026** | 67 |
| **40660627** | *«any-hover:hover evaluates true with paired bluetooth mouse, but doesn't actually :hover / fire JS enter/over/out/leave events»* | **DOPPIONE** di 41445959 | 25 nov 2019 → 7 dic 2023 | 28 |
| **40215797** | *«mousemove events are not fired (bluetooth mouse)»* | **CHIUSO, corretto** | 2012 → 2013 | 13 |

⛔ **Nessuno dei quattro nomina `cursor: none`. Nemmeno una volta.**

E il 41445959 è chiuso da un CL che si legge (`chromium-review` 7594983, **MERGED**), il cui
messaggio è: *«…**Filter virtual/disabled input devices and ignore OEM devices that falsely report
SOURCE_MOUSE alongside SOURCE_TOUCHSCREEN**»* ⇒ ⭐ è la conferma normativa di quel che
`F4-AND-1` §3.4 aveva già letto in `TouchDevice.java`: **su Samsung il touchscreen si dichiara
anche come mouse**, e Chrome ha appena smesso di credergli.

⭐ **Un quinto, che nessuno aveva**: `crbug.com/498987216`, *«[Android][Input][A11y] Validate Samsung
DeX pointer classification for hover capability detection»*, **APERTO** dal 2 aprile 2026, con
un'ammissione che vale oro: *«**No Samsung DeX hardware was available during implementation**, so
the DeX behavior is inferred from API docs and assumptions about built-in pointer reporting.»*
⇒ ⛔ **il comportamento di Chrome su DeX non è stato verificato nemmeno da chi lo ha scritto.**

### 8.2 ⭐⭐ Il difetto vero, documentato da quattro progetti indipendenti

**noVNC #1727** — titolo vero *«Moving hardware mouse without drag ignored on Chrome Android»*
(⚠ non «su DeX»: DeX è nel corpo), chiusa `notourbug` il 12 dic 2022, Galaxy S22 Ultra + Chrome 108:

> *«On Chrome Android, mouse movements are not detected by noVNC, unless mouse buttons are pressed
> (e.g. dragging). However, other browsers (Brave, Kiwi) do detect all mouse movements just fine.»*

⭐⭐ **E il commento successivo del segnalatore è la prova sperimentale che cercavo**: su richiesta
del manutentore prova `domeventviewer.com/mouse-event-viewer.html` —

> *«`mousemove` only fires on click indeed. I've narrowed this down even further — **it seems
> specific to Chrome on Samsung devices** (or at least my S22, with or without DeX). I tried Chrome
> on an old Pixel 4, and it registers `mousemove` just fine.»*

⛔ **Quella pagina di prova è stata scaricata e letta (HTML + i due CSS): la parola `cursor` non
compare nemmeno una volta.** ⇒ ⭐⭐⭐ **il difetto si riproduce su una pagina che non tocca la
proprietà `cursor`.** È la refutazione sperimentale della frase, fatta da un terzo, quattro anni
prima di noi.

**KasmVNC #222**, *«Mouse tracking not working in android chrome»*, **ancora aperta** dal 4 marzo
2024, Galaxy S23 in DeX — stesso sintomo, e un commento che chiude l'altra metà:

> *«Switching Brave to load the Kasm web page in desktop mode helps functionally by **making the
> real pointer actually visible**, but the pointer inside the Workspace window **stays stationary
> until I click somewhere**.»*

⇒ ⛔ **cursore di sistema di nuovo visibile, e i movimenti continuano a non arrivare.** Se la causa
fosse il nascondere il cursore, questo l'avrebbe risolto.

**Kasm workspaces-issues #20** — il supporto suggerisce di spegnere *«Prefer Local Cursor»* (cioè di
smettere di disegnare il cursore lato client e quindi di non mettere `cursor: none`). Risposta del
segnalatore, letterale: **«Nope, didn't help»**.

**Moonlight-android #573** (Galaxy S8+ in DeX, 2018): *«the buttons are functioning properly, but
you cannot move the pointer/cursor»* — ⭐ **applicazione nativa, nessun CSS di mezzo, stesso
sintomo.**

### 8.3 ⭐ E l'argomento che da solo basterebbe: noVNC mette `cursor: none` SEMPRE

`[R]` **noVNC `core/util/cursor.js`**:

- `:9` `const useFallback = !supportsCursorURIs || isTouchDevice;` ⇒ **su Android vale sempre
  `true`**;
- `:109` dentro `clear()`: `this._target.style.cursor = 'none';`
- e nello **stesso ramo** noVNC registra `mousemove` **sul medesimo elemento** per muovere il
  cursore che disegna lui.

⇒ ⛔ **Se `cursor: none` uccidesse i `mousemove` su Android, noVNC sarebbe rotto su ogni dispositivo
tattile, sempre, da anni.** Non lo è — e i suoi utenti Samsung segnalano il difetto **come una
particolarità di Samsung**, non come una particolarità di noVNC.

⚠ E la controprova nell'altro verso: lo sviluppatore di Kasm scrive che **tre sviluppatori su
quattro dispositivi Samsung diversi** (Note 20 Ultra, S23U, S25U, Z Fold 7) hanno montato un DeX e
*«have been unable to replicate it. In all four instances the mouse is tracking exactly as it
should be»*. ⇒ ⭐ **su alcuni DeX funziona, con `cursor: none` acceso.**

### 8.4 ⇒ Che cosa cambia per noi

1. ⛔ **La frase del mandato è falsa anche sperimentalmente**, non solo sul meccanismo (§1).
2. ⭐⭐ **E il difetto che l'ha suggerita è reale, ha un nome, e combacia con la nostra misura**: su
   parecchi dispositivi Samsung Chrome **non consegna i `mousemove` a pulsanti alzati**, comunque
   sia scritto il CSS — e alle 15:09 la nostra pagina ascoltava **solo `mousemove`** (§2.4).
   ⭐ È la stessa `[?]` che `F4-AND-1` §6.2 dichiarava di non saper spiegare (*«non so perché i
   `mousemove` siano mancati per dodici secondi»*): adesso ha **quattro segnalazioni indipendenti,
   una pagina di riproduzione e una spiegazione**. ⛔ E la spiegazione **non è** quella scritta oggi
   in `src/pagina.html:3878-3885` (*«Chrome li sospende quando il tocco e il mouse si contendono lo
   stesso dispositivo»*, che `F4-AND-1` D4 aveva già segnato come deduzione senza fonte): è
   **un difetto del motore su ferro Samsung**, e la fonte è §8.2.
3. ✅ **La nostra cura è già quella giusta**: `pointermove` accanto a `mousemove`
   (`src/pagina.html:4205-4206`), che è l'evento **primario** e non di compatibilità. ⚠ `[?]`
   **quel che nessuna di quelle segnalazioni dice è se muoia anche `pointermove`** — nessuno l'ha
   provato, ⛔ e nemmeno noi: la sessione che l'ha misurato *«senza, i movimenti si spegnevano del
   tutto»* è **precedente** all'aggiunta di `pointermove`. **La prova 1 di §10 lo dice in dieci
   secondi.**
4. ⭐ **E Firefox per Android compare in tutt'e tre le segnalazioni come «funziona»**. Non è una
   cura, ma è un banco di controllo che costa un'installazione.
5. ⭐ **Va aperto un difetto a monte.** `crbug.com/502461774` è aperto, è su DeX, e chi l'ha scritto
   ammette di non avere un DeX (`498987216`). ⇒ **noi ne abbiamo uno**, e le nostre misure sono
   esattamente quelle che a loro mancano.

---

## 9 · Le otto domande del briefing

**1. Quando il mouse si muove e sullo schermo non cambia niente, che cosa viaggia sul filo?**
`[R]` Viaggia **un solo messaggio `PUNTATORE`** (`RCP.md` §7.3) per ogni **pixel di tela**
attraversato — e nemmeno quello se il pixel non cambia (`src/pagina.html:3670`). ⛔ **Indietro non
viaggia niente**, perché Mutter non consegna un fotogramma se non cambia un pixel (`figlio.c`) e il
cursore lo prendiamo come metadato (`mutter.c:503`). Il puntatore si muove sul vetro del client
**senza** un fotogramma nuovo solo perché `cl_su_mousemove` chiama `cl_disegna()` **nello stesso
gestore** (`src/pagina.html:3951`), cioè in locale, alla velocità della mano.
⭐ E su DeX **c'è una terza freccia che si muove senza che nessuno gliela chieda**: quella di
Android, disegnata da SurfaceFlinger (§3). ⇒ **tre puntatori possibili nella stessa scena**: il
nostro disegnato, quello del browser/Android, e quello (invisibile) del desktop remoto.

**2. Chi disegna il puntatore, e che cosa succede quando la forma cambia?**
Oggi, sul DeX: **il sistema operativo** (§3), più la nostra freccia disegnata sopra. `[R]` Il
server manda la forma vera (`CURSORE_FORMA`, `rcp.c:3054`, `webtransport.c:1571`, contatori a
`cursore.c:524-533`) e ⛔ **la pagina la butta** (`src/pagina.html:2983-2989`). ⇒ **quando la forma
cambia, oggi non succede niente.** Le due strade per usarla sono §6 (vestire il cursore del
browser, alla xpra) e la freccia disegnata con `REMOTIX_PUNTATORE.forma()`, che è **già scritta e
non chiamata** (`src/pagina.html:3752-3784`).

**3. Il client chiede la misura del desktop al server?**
⛔ **No**, e non è una domanda di questo rapporto: `F4-AND-4` l'ha già chiusa (quattro progetti su
cinque lo chiedono; noi impaginiamo). ⭐ Quel che aggiungo dal lato piattaforma: **la misura giusta
da chiedere non è `screen`, è la vista** — su DeX `screen.width × devicePixelRatio` = **3072**,
una risoluzione che non esiste (`F4-AND-3`, difetto 1). Se un giorno si chiederà una misura a
Mutter, il numero da mandare è quello di `misura_vista()`, **non quello di `screen`**.

**4. Quanti stadi ha la conversione delle coordinate?**
Tre (vetro→tela, bande, tela→desktop) — già in `F4-AND-1`. ⭐ **Dal lato Android ne scopro un
quarto, invisibile**: `event_forwarder.cc:200` divide per `view_->GetDipScale()`
(`/*pix_to_dip=*/1.f / view_->GetDipScale()`), e `F4-AND-3` ha misurato che su DeX quel fattore
porta dentro **lo zoom di pagina al 120 %**. ⚠ Non è un errore — si cancella nella differenza
`clientX − rect.left` (`F4-AND-1` §2.1) — ma è la ragione per cui **nessun numero letto da
`screen.*` è nella stessa unità dei numeri degli eventi**.

**5. Come si misura e come si limita la latenza dell'input?**
⭐ La risposta nuova è §5: **su DeX il tetto è 60 Hz e non è nostro**, e i campioni intermedi sono
già buttati da Chrome (`event_forwarder.cc:208`). ⇒ non c'è **niente** da guadagnare con
`getCoalescedEvents()`; c'è **mezzo fotogramma** da guadagnare con `pointerrawupdate` — ⚠ a 60 Hz
sono ~8 ms, contro i **12 ms** `[M]` che il comando impiega solo a uscire dal telefono e i **130 ms**
`[M]` di mediana del giro completo. ⇒ **è una cura da fare dopo le altre, non prima.**
⛔ **La coda che scarta ce l'abbiamo noi ed è giusta** (`src/pagina.html:3670`): scarta i movimenti
che non cambiano pixel. ⚠ Ma è anche il motivo per cui **un conteggio fatto sul server non è un
conteggio di eventi** (§2.2), e mezza giornata è stata spesa su quella confusione.

**6. Che cosa c'è di specifico per Android, per il tocco e per DeX?**
§1 (la catena del cursore), §3 (lo sprite di sistema), §5 (l'accorpamento e i campioni buttati),
§7 (il puntatore è per display). ⭐ E la regola che ne esce, da mettere accanto a quella di
`F4-AND-1` §3.4: **su Android il cursore non appartiene alla pagina e nemmeno all'applicazione;
appartiene al display.** Tutto quel che la pagina può fare è **chiedere un'icona**.

**7. Che cosa ruberei, e che cosa NON ruberei.**
⭐ **Ruberei la riga di xpra** (§6): vestire il cursore del browser con la forma remota, **≤ 32 px**
e con il ripiego `, auto` in coda. Costo: una riga in `forma()` **più il chiamante che manca**
(`src/pagina.html:2983-2989`). Guadagno: un puntatore solo, che si muove a 60 Hz senza un solo byte
sul filo e senza un fotogramma. ⚠ Prezzo dichiarato: un binder a `system_server` **per cambio di
forma** (§6.4), e un cursore disegnato il 20 % più piccolo del dovuto perché il fattore di scala si
perde al confine JNI (§6.2).
⛔ **NON ruberei «il cursore dipinto dentro l'immagine»** (strada 5.2 del briefing): `[S]`
`SPECIFICHE.md:532` lo **vieta** — *«il cursore del desktop non deve mai finire nell'immagine
catturata, altrimenti se ne vedono due»*. E costa un fotogramma per movimento, cioè esattamente la
banda che la strada 5.1 vuole risparmiare.
⛔ **NON ruberei Pointer Lock** come strada principale (§4.4): la cattura si perde al cambio di
fuoco, e su DeX il fuoco si perde spesso.
⛔ **NON spenderei una riga su `getCoalescedEvents()` né su `getPredictedEvents()`** (§5.2): sul
mouse, su Android, dentro non c'è niente.

**8. La refutazione del mio mandato.** §1, §2 e §8 — la frase è falsa sul meccanismo, falsa
sperimentalmente, e la causa vera è un'altra.
⭐ **E la domanda giusta non era quella che mi è stata data.** Il mandato mi mandava a leggere
`frameworks/base` e `frameworks/native`, e l'ho fatto — ⛔ **ma la risposta stava in `git log`.**
La `[?]` è nata da un esperimento in cui si credeva di aver cambiato una variabile sola, mentre nel
frattempo la pagina **non aveva ancora** l'ascoltatore che sarebbe arrivato due ore dopo. ⇒ ⭐ **la
prima cosa da fare davanti a una correlazione forte non è cercarne il meccanismo a monte: è
guardare che cos'altro era diverso in quel binario.**
⚠ **Rifiuto comunque metà del mandato**: la conferma non si può dare leggendo. Il conteggio che
serve non esisteva. La misura è scritta (§10) e costa quaranta secondi.

---

## 10 · ⭐ La misura, pronta da far fare — `banchi/05-dex-cursore.html`

*⛔ Non ho un DeX. Questa è la misura che chiude la `[?]`, scritta e verificata sintatticamente
(`node --check`), sul modello di `banchi/04-dex-vista.html` (`F4-AND-3` §9).*

**Che cos'è**: una pagina sola, senza dipendenze, che **non parla con nessun server**. Un riquadro
grigio è l'unico elemento con gli ascoltatori (`pointermove`, `mousemove`, `pointerrawupdate`,
`mousedown`) e l'unico su cui si cambia `cursor`. ⇒ **una variabile sola davvero.**

**Come si serve** (dal portatile, e poi si spegne):

```bash
python3 -m http.server 7912 --bind 0.0.0.0 \
        --directory /home/nicfio/Documenti/REMOTIX_V2/banchi
# dal DeX, in Chrome:  http://192.168.0.3:7912/05-dex-cursore.html
# quando ha finito:    kill %1
```

⚠ **Porta 7912**, dichiarata: sopra la 7900, e fuori da 7448 · 7501 · 7561 · 7571 · 7700 ·
7721-7723 · 7911 (di `04-dex-vista.html`).

**Che cosa deve fare l'utente**: **cinque** prove da dieci secondi, in ordine, muovendo il mouse
**senza fermarsi** dentro il riquadro e senza cliccare, e poi «copia tutto».

| prova | che cosa guardare | che cosa decide |
|---|---|---|
| **1 · cursore normale** | ⭐ `pointermove` al secondo **contro** `mousemove` al secondo | è il **denominatore** di tutto il resto — e insieme è la misura che §8.4 chiede: **se `mousemove` è ~0 e `pointermove` no**, questo DeX ha il difetto Samsung di noVNC #1727 **e la nostra cura lo copre già**. Se sono zero **tutt'e due**, il difetto è più grave di quel che è documentato e va aperto a monte con questa pagina come riproduttore |
| **2 · `cursor: none`** | ⭐⭐ lo stesso numero, ⚠ **guardando `pointermove`** (se `mousemove` era già zero nella prova 1, su `mousemove` non c'è niente da confrontare) | **dello stesso ordine ⇒ la frase è FALSA**, come dicono §1, §2 e §8, e la strada del puntatore disegnato si riapre. **Zero ⇒ è VERA**, e allora abbiamo trovato un difetto del motore che **nessuna fonte descrive e che il sorgente esclude** — con il riproduttore in mano, e va aperto su `crbug.com/502461774` |
| **3 · `cursor: url()` 32×32** | ⭐ **si vede un mirino rosso?** | **sì ⇒ la strada di xpra funziona sul DeX** (§6). **No ⇒ è chiusa davvero**, e questa volta con la prova giusta |
| **4 · `cursor: url()` 96×96** | il mirino grande | se la 3 funziona e la 4 no, il limite è **la dimensione** (§6) |
| **5 · Pointer Lock** | il cursore di sistema **sparisce**? `movementX` è ≠ 0? | §4 |

⭐ **In più, gratis, la pagina misura tre cose che nessun rapporto ha**: `coalesced max` (che
secondo §5.2 deve valere **1**), `pointerrawupdate` al secondo contro `pointermove` al secondo (che
secondo §5.1 devono essere **quasi uguali**, entrambi ~60/s), e il rapporto fra `movementX` sommato
e lo spostamento vero di `clientX` (che dice in che spazio è `movementX` su DeX — la `[?]` di
`F4-AND-1` D6).

⛔ **E due misure che non costano niente e vanno fatte per prime.**

**A · nel registro che abbiamo già.** Nel pannello del tastino `⌨` della sessione del DeX, cercare
la riga *«CURSORE_FORMA ricevuto e non usato»* (`src/pagina.html:2987-2988`). Se c'è, la forma del
cursore remoto **arriva già** e §6.5 costa due righe. Se non c'è, il canale è muto e va guardato il
server (`cursore.c:520-533` stampa i contatori alla chiusura). ⭐ **E c'è anche l'altra riga da
cercare**, quella di `F4-AND-1` M5: *«⚠ la regione … NON e' grande come la tela»* (`src/input.c`).

**B · la pagina di un terzo, trenta secondi.** Aprire sul DeX
<https://domeventviewer.com/mouse-event-viewer.html> — ⛔ **quella pagina non tocca la proprietà
`cursor`** (verificato: HTML e i due CSS scaricati e letti, zero occorrenze) — e muovere il mouse
senza cliccare. Se i `mousemove` non arrivano **lì**, il difetto è di Chrome su Samsung (§8.2), non
nostro, e nessuna riga della nostra pagina lo toglierà. ⭐ È il test con cui il segnalatore di
noVNC #1727 ha isolato il difetto nel 2022, e a noi costa un indirizzo.

---

## 11 · Quel che questo rapporto NON dice

1. ⛔ **Non ho misurato niente su un DeX**, né su nessun Android. **Tutto** quel che c'è qui è
   `[R]` o `[S]`. Non c'è un solo `[M]` mio in questo rapporto: i `[M]` citati sono di altri.
2. ⚠ **La spiegazione di §2.4 è la migliore che ho, non una dimostrazione.** Quel che è
   **dimostrato** è che alle 15:09 la pagina ascoltava solo `mousemove` `[R]` e che su Samsung
   `mousemove` muore `[R]` su quattro segnalazioni. ⛔ **Non è dimostrato che sia successo proprio
   quella volta**: nessuno ha contato gli eventi nel gestore. Lo chiude la prova 1 di §10.
   ⚠ E resta il dettaglio della freccia (§2.2) che non torna.
3. ⚠ **Ho letto AOSP `main` e Chromium `main`, non la build che gira sul telefono dell'utente.**
   Il DeX gira su One UI, cioè su un ramo Samsung: `PointerChoreographer` e
   `MouseCursorController` sono pezzi che Samsung **può** aver toccato, e io non ho modo di
   leggerne il sorgente. ⭐ È la stessa riserva che `F4-AND-1` §3.6 fa per Samsung Internet, e vale
   **anche per il framework**.
4. ⚠ **Non ho verificato quale versione di Android abbia il DeX dell'utente.** `PointerChoreographer`
   è nuovo (Android 14/15) e ha spostato il proprietario del puntatore; su un Android più vecchio la
   catena passa da `PointerController` chiamato dal `NativeInputManager`. ⛔ **In tutt'e due i casi
   l'ordine di `ViewRootImpl` (§1.2) è lo stesso**, e quello è il tratto che decide — ma il resto
   di §3 e §5 potrebbe non applicarsi a una versione più vecchia.
5. `[?]` **Non ho trovato il chiamante di `requestUnbufferedDispatch` sul percorso del mouse** (§5).
   Ho cercato in quattro file; non ho certificato lo strumento su tutto l'albero di Chromium.
6. ⚠ **Non ho ricostruito il codice esatto in vigore alle 15:09.** Quello stato non è mai stato
   messo in git: §2.3 lo deduce dai commenti del commit successivo (`536e3d2`) e dal diff
   `0075b4f..536e3d2`. Se qualcuno ha una copia di quel file, va guardata prima di credermi.
7. ⚠ **Non so se il `[M]` «165 · 227 · 320 · 200» e il `[M]` «4 e 0» siano contati nello stesso
   punto.** Ho argomentato che sono conteggi di messaggi lato server (§2.2) perché è l'unico
   contatore che il deposito produce; ⛔ **non l'ho visto scritto da nessuna parte.**
8. ⛔ **Dei difetti di §8 ho letto titolo, stato, date e descrizione — NON i commenti.** Il payload
   di `issues.chromium.org` è incorporato nell'HTML e si prende, i commenti no (sette punti
   d'accesso provati, tutti respinti). ⇒ dove scrivo «commenti: 67» so **quanti sono**, non **che
   cosa dicono**. E gli stati sono la decodifica di un codice numerico: convalidata su un caso
   (40660627 esce «doppione» e porta davvero a 41445959), non su tutti.
9. ⚠ **Le citazioni di §8.2-8.3 vengono da GitHub, cioè da segnalazioni di utenti**, non da una
   fonte primaria: sono `[R]` sul testo (l'ho letto) ma **non sono misure**. Il valore che hanno è
   che sono **quattro, indipendenti, e concordi** — e che una di esse porta una pagina di
   riproduzione che ho scaricato e verificato io.
10. ⚠ **`requestUnbufferedDispatch` per il mouse resta `[?]`** (§5), e con lei la domanda «si può
    superare il tetto dei 60 Hz?».
11. ⚠ **Non ho verificato se `PointerLockOnAndroid` sia acceso nella Chrome che gira sul DeX
    dell'utente.** Il sorgente dice `status: "stable"`; la tabella di compatibilità dice il
    contrario (§4.1). ⛔ **Due fonti, un conflitto, nessuna misura**: la prova 5 di §10 lo chiude.
12. ⚠ **Non ho guardato Samsung Internet**, e `F4-AND-1` §3.6 spiega perché non ci si possono
    trasportare le conclusioni.

---

## 12 · Le fonti, in un posto solo

*⛔ Ogni file qui è stato **scaricato e letto**, non citato a memoria. Copie di lavoro in
`/tmp/studio-input/android/` (sola lettura, cartella mia).*

**AOSP `[R]`** — via `android.googlesource.com/…?format=TEXT`, ramo `main`, 14 agosto 2026

- `platform/frameworks/base` · `core/java/android/view/ViewRootImpl.java` — `:8118-8119`
  (l'ordine), `:8153-8192` (`maybeUpdatePointerIcon`), `:8247-8283` (`updatePointerIcon`)
- `platform/frameworks/base` · `core/java/android/view/PointerIcon.java` — `:68` (`TYPE_NULL`),
  `:250-272` (`getSystemIcon`), `:289-324` (`getLoadedSystemIcon`), `:440-462` (`equals`),
  `:613-672` (la mappa dei tipi)
- `platform/frameworks/base` · `libs/input/MouseCursorController.cpp` — `:68-85` (`move`),
  `:95-115` (i limiti sul display), `:361-411` (`updatePointerLocked`)
- `platform/frameworks/base` · `libs/input/SpriteController.cpp` — `:343-365` (`eCursorWindow`) ·
  `libs/input/SpriteController.h:67`
- `platform/frameworks/base` · `services/core/jni/com_android_server_input_InputManagerService.cpp`
  — `:850-857` (`TYPE_NULL` ⇒ icona vuota), `:1608-1620` (`isPointerInWindow`), `:1994-1995`,
  `:2846-2865` (`nativeSetPointerIcon`)
- `platform/frameworks/base` · `services/core/java/com/android/server/input/InputManagerService.java:1678-1681`
- `platform/frameworks/native` · `services/inputflinger/PointerChoreographer.cpp` — `:76-85`,
  `:168-203` (`fadeMouseCursorOnKeyPress`), `:173-177` (`notifyMotion`), `:232-292`, `:433-445`,
  `:880-930` (`setPointerIcon`), `:933-955`
- `platform/frameworks/native` · `services/inputflinger/dispatcher/InputDispatcher.cpp` — `:7310`
  (`isPointerInWindow`) e **l'assenza certificata** di ogni logica d'icona
- `platform/frameworks/native` · `libs/input/InputConsumerNoResampling.cpp:349-390`
  (l'accorpamento)

**Chromium `[R]`** — via `raw.githubusercontent.com/chromium/chromium/main`, 14 agosto 2026

- `content/browser/renderer_host/render_widget_host_view_android.cc:1374-1387`
- `content/public/common/content_features.cc:1447-1450` (`kAndroidDisplayCursor`)
- `ui/android/view_android.cc:343-350` (`RequestUnbufferedDispatch`), `:470-490`
  (`OnCursorChanged`)
- `ui/android/java/src/org/chromium/ui/base/ViewAndroidDelegate.java:314-322`
  (`onCursorChangedToCustom`), `:324-452` (`onCursorChanged`), `:571-590`
- `ui/android/java/src/org/chromium/ui/base/EventForwarder.java:295-312` (la storia, nel tocco),
  `:441-490` (`onHoverEvent`), `:516-557` (`sendNativeMouseEvent`)
- `ui/android/event_forwarder.cc:75-95` (la storia, nel tocco), `:178-224` (`OnMouseEvent`,
  `history_size = 0`)
- `third_party/blink/renderer/core/input/event_handler.cc:173-191` (`DetermineHotSpot`), `:260-263`
  (`kMaximumCursorSizeWithoutFallback = 32`), `:501-532`, `:664-762`
- `ui/base/cursor/cursor.cc:47-59` (il punto attivo ritagliato), `:93-106`
  (`AreDimensionsValidForWeb`, **128 DIP**) · `ui/base/cursor/cursor.h:80-83`
- `third_party/blink/renderer/core/frame/local_frame_view.cc:1463-1468` (`ShouldSetCursor`)
- `content/browser/renderer_host/render_widget_host_view_android.cc:2672-2739` (`LockPointer`,
  `ChangePointerLock`, `IsPointerLocked`, `UnlockPointer`)
- `third_party/blink/renderer/platform/runtime_enabled_features.json5:4682-4686`
  (`PointerLockOnAndroid`, `status: "stable"`)
- `ui/android/window_android.cc:359-373` · `WindowAndroid.java:1696-1728`, `:1763`
- `ui/android/java/src/org/chromium/ui/base/PointerLockEventHelper.java:52-108` (⭐ la posizione
  ricostruita) · `EventForwarder.java:844-903`, `:873-879` (i micro-movimenti scartati)
- `components/input/web_input_event_builders_android.cc:169-181` (e **zero** `movement` in 311
  righe) · `third_party/blink/renderer/core/input/mouse_event_manager.cc:59-75`
  (`UpdateMouseMovementXY`) · `third_party/blink/renderer/core/events/pointer_event_factory.cc:88-105`

**AOSP `[R]`, secondo blocco**

- `frameworks/base/core/java/android/view/PointerIcon.java:330-355` (`create`), `:599-611`
  (`validateHotSpot`), `:217-218`
- `frameworks/base/core/java/android/view/ViewRootImpl.java:4722-4725` (la cattura persa col fuoco),
  `:6398-6406` (`handlePointerCaptureChanged`), `:8198-8202`
- `frameworks/native/services/inputflinger/PointerChoreographer.cpp:599-608`
  (`notifyPointerCaptureChanged` ⇒ `fade`)
- `frameworks/native/services/inputflinger/reader/mapper/CursorInputMapper.cpp:294-303`, `:459-474`
  (`AINPUT_SOURCE_MOUSE_RELATIVE`), `:479-482` (accelerazione spenta)

**Difetti e segnalazioni `[S]`/`[R]`** — ⛔ titolo, stato, date e descrizione letti; **commenti no**

- `issues.chromium.org` **502461774** (aperto, DeX-trackpad) · **41445959** (corretto 17 apr 2026) ·
  **40660627** (doppione) · **40215797** (corretto) · **498987216** (aperto, *«No Samsung DeX
  hardware was available during implementation»*)
- `chromium-review.googlesource.com/c/chromium/src/+/7594983` — **MERGED**, il messaggio di commit
  che nomina gli *«OEM devices that falsely report SOURCE_MOUSE alongside SOURCE_TOUCHSCREEN»*
- github.com/novnc/noVNC **#1727** (`notourbug`, con la prova su `domeventviewer.com`) ·
  noVNC `core/util/cursor.js:9`, `:109`
- github.com/kasmtech/KasmVNC **#222** (aperta) · kasmtech/workspaces-issues **#20**
- github.com/moonlight-stream/moonlight-android **#573** ·
  github.com/mdn/browser-compat-data **#19829** (Pointer Lock «no-op», ⚠ vecchia)
- `domeventviewer.com/mouse-event-viewer.html` + i suoi due CSS — **scaricati e letti**: zero
  occorrenze di `cursor`

**Deposito `[R]`**

- `src/pagina.html` — `:190-266` (il foglio di stile e la storia del `cursor: none`), `:271-272`
  (`pointer-events: none`), `:2983-2989` (⭐ `CURSORE_FORMA` scartato), `:3650-3673`
  (`cl_satura`, `cl_manda_puntatore`), `:3704-3725` (`cl_disegna`), `:3752-3784`
  (`REMOTIX_PUNTATORE.forma`), `:3866-3868` (`cl_utilizzabile`), `:3898-3953` (i gestori),
  `:4205-4207` (gli ascoltatori sulla tela), `:5150-5163` (`touch-action`, solo nel tocco)
- `src/rcp.c:2867` (il contatore per tipo), `:3054-3237` (`rcp_cursore_forma`) ·
  `src/cursore.c:520-533` · `src/webtransport.c:1561-1574`
- `SPECIFICHE.md:523-542` (§7.1, ⛔ *«il cursore del desktop non deve mai finire nell'immagine
  catturata»*)
- ⭐ git: `dd0b163` (14/08 11:45) · **`0075b4f` (14/08 15:34) — `src/pagina.html:3909-3912`, gli
  ascoltatori del modo classico alle 15:09: `mousemove`, `mousedown`, `wheel`, `contextmenu`, e
  **nessun `pointermove`** · `536e3d2` (14/08 17:19) — `src/pagina.html:4206`, `pointermove`
  aggiunto. Il conto è verificabile con
  `for c in dd0b163 0075b4f 536e3d2; do git show $c:src/pagina.html | grep -c 'addEventListener("pointermove"'; done`
  ⇒ **0 · 0 · 1**

**Rapporti usati e non ripetuti**: `F4-DEX-punto-di-ripresa.md`, `F4-AND-1-puntatore.md` (§2, §3.1,
§3.4, §3.5, D1, D6), `F4-AND-2-tastiera.md`, `F4-AND-3-dex-vista.md` (l'1,2, i 154 px, lo schermo
intero), `F4-AND-4-come-fanno-gli-altri.md`, `F4-AND-5-latenza.md` (il vsync, l'allineamento a rAF).
