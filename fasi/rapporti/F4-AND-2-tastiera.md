# La tastiera fisica su Android e DeX, nel browser — e perché «è laggata»

*Anello di studio F4-AND-2, 14 agosto 2026. Mandato: «prova a smentirmi».
L'ipotesi da smentire era: **«il ritardo della tastiera su DeX viene dall'IME di Android che
intercetta le battute»**.*

**Sorgenti letti oggi, e dove stanno** (scaricati nello scratchpad, niente nel deposito):
Chromium `main` — `ImeAdapterImpl.java`, `web_input_event_builders_android.cc`,
`key_event_utils.cc`, `keyboard_lock_service_impl.cc`, `render_widget_host_view_android.cc`,
`render_widget_host_view_base.cc`, `WindowAndroid.java`, `keyboard.idl`;
noVNC `7c36fab` (6 giu 2026); kasmtech/noVNC `3c418e6` (12 ago 2026);
`apache/guacamole-client`; `Xpra-org/xpra-html5`.

---

## ⭐⭐⭐ In una riga

**L'ipotesi non regge, e si smentisce con una riga del sorgente di Chrome e con la misura che
l'utente ha già in mano.** Su Chrome per Android l'IME sta nel percorso **solo se il fuoco è su un
elemento modificabile**; la nostra pagina non ne ha uno col fuoco — ⛔ **tranne subito dopo
l'accesso, e quello è un difetto vero** — e infatti le 13 lettere sono arrivate con `ev.key` vero,
cosa che con l'IME nel mezzo **non sarebbe potuta succedere**.
⇒ Il candidato che regge è un altro: ⭐ **il thread principale della pagina è occupato a dipingere
il video, e i `keydown` aspettano in coda dietro un blocco da ~34 ms per fotogramma.**

---

## 1. ⭐⭐ LA REFUTAZIONE, in tre prove

### Prova A — il sorgente di Chrome: senza nodo modificabile, l'IME non c'è

`[R]` `content/public/android/java/src/org/chromium/content/browser/input/ImeAdapterImpl.java:569-573`
(Chromium `main`, scaricato il 14 ago 2026):

```java
// Without this line, some third-party IMEs will try to compose text even when
// not on an editable node. Even when we return null here, key events can still go
// through ImeAdapter#dispatchKeyEvent().
if (!focusedNodeEditable()) {
    setInputConnection(null);
```

`[R]` e `ImeAdapterImpl.java:1116-1125`, che è **il bivio**:

```java
public boolean dispatchKeyEvent(KeyEvent event) {
    ...
    if (mInputConnection != null) return mInputConnection.sendKeyEventOnUiThread(event);
    return sendKeyEvent(event);
}
```

⇒ **`mInputConnection == null` ⟺ nessun nodo modificabile col fuoco ⟺ la battuta salta l'IME.**
`[R]` `focusedNodeEditable()` è `mTextInputType != TextInputType.NONE`
(`ImeAdapterImpl.java:492-495`).

⚠ E il commento è prezioso per un'altra ragione: dice che **alcuni IME di terze parti
proverebbero a comporre anche su un nodo non modificabile**, e che Chrome tappa quel buco lui.
⇒ La differenza fra Gboard e la Samsung Keyboard, che era la domanda, **è resa irrilevante da questa
riga**: nessuno dei due riceve una `InputConnection`.

### Prova B — la misura che l'utente ha già fatto

`[M]` (dall'utente, 14 ago 2026, DeX): **13 LETTERA e 28 POSIZIONE_TASTO sono arrivate.**

⛔ Con l'IME nel percorso, `cl_su_keydown` (`src/pagina.html:3842-3847`) avrebbe **scartato tutto**:
il ramo `keyCode === 229` è un `return` senza spedizione. Zero lettere, non 13.
⇒ **Le battute misurate sono la prova che l'IME non era nel percorso.**

⚠ **Ma la misura è cieca su un punto, e va detto**: `cl_ripiego` dichiara ogni ripiego **una volta
sola** (`[R]` `src/pagina.html:3297-3301`, `if (CL_RIPIEGHI.indexOf(nome) >= 0) return;`).
⇒ `REMOTIX.input_classico.ripieghi` dice **se** «composizione» è scattato, non **quante volte**.
La prova B regge se in quell'elenco «composizione» **non c'è**; se c'è, non sappiamo se è scattato
una volta o cinquecento. ⭐ **È la prima cosa da guardare nel registro della sessione DeX, e costa
zero.**

### Prova C — la firma dell'evento sintetico dell'IME, e perché la nostra pagina non la vede

`[R]` `components/input/web_input_event_builders_android.cc:137-148`:

```cpp
ui::DomCode dom_code = ui::DomCode::NONE;
if (scancode)
  dom_code = ui::KeycodeConverter::NativeKeycodeToDomCode(scancode);
...
result.dom_key = GetDomKeyFromEvent(env, android_key_event, keycode, modifiers, unicode_character);
```

`[R]` e `GetDomKeyFromEvent`, righe 82-90 dello stesso file:

```cpp
// Synthetic key event, not enough information to get DomKey.
if (android_key_event.is_null() && !unicode_character)
  return ui::DomKey::UNIDENTIFIED;
```

`[R]` `ImeAdapterImpl.java:1388-1396` chiama il lato nativo con `null` come evento, `COMPOSITION_KEY_CODE`
(= 229), **scancode 0**.

⇒ ⭐ **La firma completa di una battuta sintetizzata dall'IME è una TERNA, non un numero:**

| | evento dell'IME | tastiera FISICA |
|---|---|---|
| `ev.keyCode` | **229** | il codice vero |
| `ev.code` | **`""`** (scancode 0 ⇒ `DomCode::NONE`) | pieno (`"KeyA"`, `"Enter"`, …) |
| `ev.key` | **`"Unidentified"`** | la lettera / il nome |

⭐ **`ev.code !== ""` è il discriminante «tastiera fisica» che il nostro codice non usa e potrebbe
usare subito**: viene dallo **scancode** dell'evento Android (`[R]` `ImeAdapterImpl.java:1433-1437`
passa `event.getScanCode()`), e una tastiera a schermo non ne ha uno.
⚠ Nota che il nostro ramo comando (`src/pagina.html:3855`) **già** dipende da `ev.code`: se `code`
fosse vuoto la posizione non sarebbe in tabella e la battuta si perderebbe con una `nota`. Le 28
posizioni arrivate dicono `[M]` che **su DeX `ev.code` è pieno** — un'altra conferma della prova A.

### ⛔⛔ E dove l'ipotesi dell'utente HA ragione: il modulo che non se ne va

`[R]` `src/pagina.html:240-246` — il modulo di accesso, con
`<input id="parola" type="password">`, **resta nel documento e resta focalizzabile** quando lo
schermo si accende: `[R]` il foglio di stile (`:184-190`) cambia solo l'impaginazione
(`padding:0`, `display:block`, la tela a `order:-1`), **non nasconde il modulo**.

⇒ ⭐⭐ **Nell'istante subito dopo «Collegati», il fuoco è dentro un `<input type="password">.**
E allora, tutto insieme:
1. `[R]` `ImeAdapterImpl.java:576-590` costruisce la `InputConnection` ⇒ **ogni battuta passa
   dall'IME** (bivio della prova A);
2. `[R]` e con la tastiera FISICA Chrome dichiara il difetto nel proprio codice —
   `ImeAdapterImpl.java:1298-1303`:

   ```java
   // HACK: When the user types text using a physical keyboard, Gboard consumes key down events
   // and commits the typed characters even if there is no conversion happening. This doesn't
   // work well with web apps expecting keypress DOM events. b/416494348
   // Ideally Gboard should be fixed to send the consumed key events back to chrome using the
   // sendKeyEvent() API, but as a workaround here we send the corresponding key down event
   // captured in onKeyPreIme() if any.
   ```

   ⚠ Il rimedio è **condizionato**: `[R]` `ImeAdapterImpl.java:466-467` lo accende solo se la
   funzionalità `ANDROID_CAPTURE_KEY_EVENTS` è attiva **e** `Build.VERSION.SDK_INT <= 38`.
3. ⛔ E il nostro `cl_nel_modulo(ev)` (`[R]` `src/pagina.html:3628-3632`) **scarta comunque tutto**
   in silenzio finché il fuoco è lì dentro.

⇒ **Lo stato è bistabile**: prima del primo clic sulla tela **nessuna battuta arriva**; dopo, tutte.
⚠ E il rimedio che il codice crede di avere **non c'è**: `[R]` `src/pagina.html:5628` e `:5780`
chiamano `tela.focus()` con il commento *«Il fuoco torna alla tela»*, ma `[R]` `<canvas id="schermo">`
(`:250`) **non ha `tabindex`** ⇒ non è focalizzabile ⇒ **`focus()` è un colpo a vuoto**.
`[R]` noVNC fa esattamente la riga che ci manca: `this._canvas.tabIndex = -1;` (`core/rfb.js:233`).

⭐ Questo **non spiega la lentezza** (spiega battute perdute, non ritardate), ma è un difetto vero,
trovato leggendo, ed è **la sola parte dell'ipotesi dell'utente che sopravvive**.

---

## 2. Le proprietà di `KeyboardEvent` su Android — quali reggono

| proprietà | su Android, tastiera FISICA | da dove viene | marca |
|---|---|---|---|
| `key` | **affidabile** (lettera vera, nome vero) | `GetDomKeyFromAndroidEvent(keycode, unicode_character)` | `[R]` `web_input_event_builders_android.cc:107-110` |
| `code` | **affidabile e non vuoto** | `NativeKeycodeToDomCode(scancode)`, e lo scancode c'è | `[R]` idem `:137-139`; `[R]` `ImeAdapterImpl.java:1437` |
| `keyCode` | affidabile (mai 229 senza IME) | `LocatedToNonLocatedKeyboardCode(KeyboardCodeFromAndroidKeyCode(...))` | `[R]` idem `:143-145` |
| `getModifierState()` | ⚠ **AltGr NON esiste** | `getModifiers(event.getMetaState())` | `[R]` `web_input_event_builders_android.cc:93-96`: *«Android doesn't have AltGr key and ImeAdapter::getModifiers won't pass it either»* |
| `timeStamp` | ⭐ **è l'orologio dell'EVENTO DI SISTEMA**, non l'istante della consegna | `event.getEventTime()` (uptimeMillis) | `[R]` `ImeAdapterImpl.java:1433-1437` |

⛔ **La conseguenza su `AltGr` tocca il nostro codice adesso**: `cl_comando()`
(`src/pagina.html:3808-3811`) e `cl_sincronizza_modificatori()` (`:3828-3831`) si reggono su
`getModifierState("AltGraph")`. `[R]` Su Android quel modificatore **non arriva mai**.
⇒ Su DeX, `AltGr+e` per fare `€` verrebbe letto come `Alt+e`, cioè come **un comando**, e
spedito come `POSIZIONE_TASTO` invece che come `LETTERA`. `[?]` Non è misurato — è dedotto dal
sorgente — ma è una `[?]` con un indirizzo preciso e si prova in trenta secondi su DeX.

⚠ **Su DeX non cambia niente di tutto questo**: DeX è la stessa Chrome per Android nella stessa
`WebContents`; non c'è un ramo DeX in nessuno dei file letti. Quel che cambia è la
`Configuration.keyboard` (tastiera attaccata) — vedi §4.

---

## 3. La strada `beforeinput`/`input`/`composition*` — **NON serve su Android, e costa cara**

### 3.1 Non serve, se il fuoco non è su un elemento modificabile

`[R]` prova A + `[M]` le 13 lettere: con la tastiera fisica e il fuoco fuori dai campi, la lettera
**arriva in `keydown`**. La strada dell'elemento nascosto serve alla tastiera **A SCHERMO**, che è
un altro problema.

### 3.2 ⛔⛔ E il costo peggiore è che ACCENDE il difetto che oggi non c'è

Mettere un `contenteditable`/`<textarea>` nascosto **col fuoco** significa, per costruzione:
`mInputConnection != null` ⇒ **tutte** le battute passano dall'IME (`[R]` `:1116-1125`) ⇒ si entra
esattamente nel caso della «HACK» di `:1298-1303`.
⇒ ⭐ **Il ramo `keyCode === 229` della nostra pagina oggi è codice morto su DeX; quella strada lo
farebbe diventare il ramo principale.**

### 3.3 ⛔⛔ E la tastiera a schermo si apre LO STESSO — `inputmode="none"` non basta

`[R]` `ImeAdapterImpl.java:1040-1050`, e il commento dice il perché:

```java
} else if (focusedNodeEditable()) {
    // The focused node is editable but disllows the virtual keyboard. We may need to
    // show soft keyboard (for IME composition window only) if a hardware keyboard is
    // present.
    restartInput();
    if (!isHardwareKeyboardAttached()) {
        hideKeyboard();
    } else {
        showSoftKeyboard();
    }
}
```

⇒ **Con una tastiera fisica attaccata, Chrome chiama `showSoftKeyboard()` di proposito**, anche su
un elemento con `inputmode="none"`, per avere la finestrella di composizione dell'IME.
`[R]` La stessa asimmetria a `:794`: `hide = textInputMode == WebTextInputMode.NONE && !isHardwareKeyboardAttached();`
⇒ **`inputmode="none"` nasconde la tastiera SOLO SE non c'è una tastiera fisica**, cioè
**esattamente nel caso opposto al nostro**.
`[R]` `isHardwareKeyboardAttached()` è `mCurrentConfig.keyboard != Configuration.KEYBOARD_NOKEYS`
(`:499-501`) — su DeX con la Bluetooth attaccata è vero.

⚠ Il ramo è dentro `onKeyboardConfigurationChanged`, cioè scatta quando la tastiera viene
attaccata/staccata o si entra/esce dal DeX. `[?]` Che succeda **anche a ogni cambio di fuoco** non
l'ho letto: è la `[?]` che resta su questo punto.

### 3.4 Le altre voci del prezzo, lette nei client veri

| costo | prova |
|---|---|
| il campo deve stare **nell'impaginazione**, non `display:none`, o il popup dell'IME non si àncora | `[R]` Guacamole `InputSink.js:48-60` (0×0 in basso a sinistra) + commit `4b933476` *«Hide input sink field in bottom-left corner for sake of input method dialogs»* |
| il campo deve essere **scrivibile**: `readonly` uccide la strada | `[R]` xpra `html5/index.html:269` `<textarea id="pasteboard" readonly …>` — e il commento del suo `return` sul 229 (`Client.js:1001`, *«we have received the event via "oninput" already"»*) **oggi è falso**, perché il commit `378e9dc4` (issue #147, «prevent keyboard popping up on mobile») ha aggiunto `readonly` all'unico campo che avrebbe dovuto riceverlo |
| il fuoco va **ripreso di continuo**, con `setTimeout(…,0)` e `click()+select()` | `[R]` Guacamole `InputSink.js:82-97`, commit `9f6b2fad`: *«Do not rely on autofocus, which may result in the field being partly focused … but not receiving any actual text input»* |
| ⛔ e il `preventDefault` sul 229 **rompe la composizione** | `[R]` Guacamole `Keyboard.js:1413-1419` fa `return` **senza** `preventDefault` («*Ignore (but do not prevent)*»); `[R]` xpra `Client.js:1001` fa `return undefined` e il chiamante (`:859-862`) chiama `preventDefault()`. ⭐ **Il nostro `cl_su_keydown:3842-3847` fa come Guacamole (nessun `preventDefault`), ed è la scelta giusta** |

---

## 4. ⭐⭐⭐ LA LATENZA — le sorgenti, messe in ordine di grandezza

### Il candidato n. 1, e ha già un numero misurato dal progetto: **il thread principale**

`[R]` `src/pagina.html:1902-1907` (misura `[M]` del progetto, 14 ago 2026, anello O2):

> *il primo `drawImage` — quello che porta il `VideoFrame` nel deposito — costa **34,03 ms** di
> mediana, e il secondo (`componi`, deposito → tela visibile) **0,08 ms** […] a 34 ms per
> fotogramma questa pagina non può superare i 29/s.*

`[R]` E il worker che toglierebbe quel lavoro dal thread principale **è spento per difetto**:
`src/pagina.html:527-529`, si accende solo con `?video=worker`.

⇒ ⭐ **Ogni `keydown` cade su un thread che sta già dentro un blocco da ~34 ms.** Chrome consegna gli
eventi tastiera al thread principale del renderer, e un evento che arriva a metà di un blocco
aspetta la fine del blocco.
⇒ Ritardo **medio ~17 ms, di picco ~34 ms, e VARIABILE** — ⭐ e la variabilità è precisamente il
sintomo che l'utente ha descritto: **«a scatti»**, non «in ritardo costante».
⛔ **L'IME, se ci fosse, farebbe l'opposto: battute perse o alterate, non battute a scatti.**

⚠ E c'è un sospetto sul PERCHÉ quei 34 ms: `[R]` `src/pagina.html:1177-1179` la tela **visibile** è
creata con `willReadFrequently: true`. `[S]` La specifica Canvas2D e la documentazione di Chrome
dicono che quell'attributo **spegne l'accelerazione GPU della tela** («*this is a hint to the
browser … which essentially means "do not use the GPU"*»). ⇒ Un `VideoFrame` decodificato in
hardware che finisce su una tela in CPU paga un trasferimento GPU→CPU **a ogni fotogramma**.
`[?]` Che sia questa la causa dei 34 ms **non è misurato** — è una lettura, e va misurata togliendo
`willReadFrequently` e rifacendo il numero.
⚠ E il numero dei 34 ms è preso **sulla macchina di sviluppo**, non su DeX: `[?]` su DeX potrebbe
essere peggio o meglio, e nessuno l'ha guardato.

### Il candidato n. 2: **quel che l'utente giudica non è la tastiera, è il VIDEO**

`[R]` `src/pagina.html:1887-1900`, misura `[M]` del progetto del 14 ago 2026, prima della cura:

> il ritardo fra `decode()` e il richiamo del decodificatore saliva di **~108 ms al secondo**:
> 31,6 ms dopo 1 s · 1 461 ms dopo 11 s · **4 650 ms dopo 43 s**.

⇒ Un utente che batte un tasto **giudica dal desktop che vede**. Con quel ritardo, una tastiera
istantanea **sembra laggata**, e nessun conto sulla tastiera lo direbbe.
⚠ La cura c'è (`decodeQueueSize > 2` ⇒ si salta il disegno, `:1924-1928`), ma `[?]` **non è
misurata su DeX**, dove il ritmo è un altro.

⭐⭐ **E lo strumento per separare le due cose ESISTE GIÀ NEL PROTOCOLLO E NON LO USA NESSUNO**:
`[R]` `RCP.md` §6.2 mette nell'intestazione di ogni fotogramma l'`id` dell'ultimo input applicato, e
`[R]` `src/pagina.html:1568` **lo legge** (`input: v.getUint32(24)`) — e `[R]` cercando `.input` in
tutta la pagina **non c'è nessun consumatore**. ⇒ Il ritardo battuta→pixel si misurerebbe
sottraendo l'istante di quell'`id` in `CL_SPEDITI` dall'istante del fotogramma. **Una decina di
righe, e chiude la domanda.**

### Il candidato n. 3: **il DeX stesso** (e non è nostro)

`[?]` Comunità Samsung e stampa, non misurato da me: con **DeX senza filo** gli utenti riportano
*«300-500 ms di latenza dei tocchi»* e *«quasi mezzo secondo per registrare un input»*, e il
rimedio consigliato è attaccare mouse e tastiera **al monitor**, non al telefono
([Samsung Members](https://r1.community.samsung.com/t5/samsung-dex/terrible-input-lag-using-dex-wirelessly/td-p/11135006),
[SamMobile](https://www.sammobile.com/news/lower-input-lag-samsung-dex-wirelessly/)).
⇒ ⭐ **Discriminante da un minuto**: scrivere nella barra degli indirizzi di Chrome, o in un campo di
testo qualunque, **sullo stesso DeX**. Se lagga anche lì, non è REMOTIX.

### Il candidato n. 4: **il filo, e la sua è una latenza A SCATTI per costruzione**

`[R]` `src/pagina.html:2641-2652`: l'input viaggia su **uno stream unidirezionale** di WebTransport.
`[S]` W3C WebTransport §3.2: *«A WebTransport stream is a concept for a **reliable in-order** stream
of bytes on a WebTransport session»*.
⇒ ⛔ **Affidabile e ordinato vuol dire blocco in testa alla coda**: un pacchetto perso ferma **tutte**
le battute successive finché non è ritrasmesso, e poi arrivano **insieme**. Su Wi-Fi/DeX è
esattamente la forma «a scatti».
⚠ `[?]` Non misurato, e non è un difetto: §2.5 concede uno stream solo e l'ordine ci serve. Ma è la
seconda spiegazione possibile dello **scatto**, e va separata dalla prima con la misura di §6.

### Quel che **NON** è la causa — refutato

| teoria | verdetto |
|---|---|
| «i listener `passive` ritardano i tasti» | ⛔ **falso.** `[S]` DOM Standard, *default passive value*: vale solo per `touchstart`, `touchmove`, `wheel`, `mousewheel`. **`keydown` non è nell'elenco** e non è mai passivo per difetto |
| «il nostro incolonnamento accorpa le battute» | ⛔ **falso.** `[R]` `src/pagina.html:3340-3358`: `cl_spedisci` codifica e chiama `manda()` **dentro il gestore**, e `[R]` `:2648-2652` scrive subito sullo stream. Nessun `requestAnimationFrame`, nessun `setTimeout`, nessuna soglia. ⭐ È la scelta giusta, ed è **l'opposto** di quel che fa KasmVNC (§5) |
| «la scheda è strozzata» | ⛔ non si applica: la pagina è in primo piano e `visibilityState` è `visible` (e `cl_rilascia_tutto` scatta proprio quando non lo è, `:3933-3936`) |
| «è il Bluetooth» | ⚠ improbabile: `[?]` intervallo di connessione BLE minimo su Android **7,5 ms**, tipico per una tastiera **11,25-15 ms** ([Punch Through](https://punchthrough.com/ble-connection-interval-throughput/)). È un ordine di grandezza sotto il sintomo |

### ⚠ E una sorgente di «scatto» che è tutta nostra, e che nessuno ha nominato: **due ritmi di ripetizione**

`[R]` `src/pagina.html:3863-3865`: sul percorso `POSIZIONE_TASTO` la ripetizione automatica
**non si rimanda** — la fa il desktop remoto. `[R]` Sul percorso `LETTERA` (`:3877-3883`) **non c'è
nessun controllo su `ev.repeat`** ⇒ le ripetizioni **locali** partono tutte.
⇒ ⭐ **Tenere premuta una lettera ripete al ritmo di Android; tenere premuto Backspace ripete al
ritmo di GNOME.** Due ritmi diversi nella stessa tastiera. `[?]` Non misurato, ma è precisamente il
tipo di cosa che un utente chiama «va a scatti», e si vede solo usando.

---

## 5. Che cosa fanno i client veri — e nessuno dei quattro ci aiuta come si spera

### La riga che conta: **nessuno legge la lettera dal `keydown` su Android; tutti la scartano**

| | trattamento del 229 | `preventDefault`? | da dove recupera la lettera |
|---|---|---|---|
| **noVNC** | `[R]` `core/input/keyboard.js:63-68`, commento `// 229 is used for composition events` — non inventa un codice fittizio come per gli altri | ⛔ **sì**, `stopEvent(e)` a `:134` | `[R]` `<textarea>` nascosta + **differenza di stringhe su 99 underscore** nell'evento `input`, `app/ui.js:1669-1732` |
| **KasmVNC** | `[R]` `core/input/keyboard.js:260-266`, `if (e.isComposing \|\| e.keyCode === 229) { … return; }` — **identico al nostro** | ✅ **no**, di proposito, per lasciar proseguire l'IME | `[R]` `compositionupdate`/`input` con `e.data`, `keyboard.js:192-253`; textarea tenuta **vuota** |
| **Guacamole** | `[R]` `Keyboard.js:1413-1419`, `229` letterale, commento *«Ignore (but do not prevent) the event»* | ✅ **no** | `[R]` `Guacamole.InputSink` — `<textarea>` 0×0 **nel layout**, `input` + `compositionstart`/`compositionend` |
| **xpra** | `[R]` `html5/js/Client.js:999-1005`, `if (keycode === 229) { return; }` | ⛔ **sì** (il `return undefined` fa scattare `preventDefault()` a `:859-862`) | ⛔ **rotta**: `[R]` `index.html:269` il `#pasteboard` è **`readonly`** |

⭐ **Il nostro `src/pagina.html:3842-3847` è letteralmente la riga di KasmVNC**, `preventDefault`
compreso (cioè: senza). Su questo punto siamo allineati al fork più recente dei quattro.

### ⛔⛔ E il fatto che smentisce l'idea che ci sia una ricetta da copiare

**`isAndroid()` NON tocca la tastiera in nessuno dei quattro.**
- `[R]` noVNC: `isAndroid()` esiste (`core/util/browser.js:215-218`) ed è usata **una volta sola**,
  in `app/ui.js:1484`, **per le barre di scorrimento**. Tutte le pezze di `keyboard.js` sono
  `isMac()`/`isIOS()`/`isWindows()`.
- `[R]` KasmVNC: `isAndroid()` **non esiste proprio** nel suo `browser.js`.
- `[R]` Guacamole: `detectQuirks()` (`Keyboard.js:1608-1632`) guarda **solo** `ipad|iphone|ipod` e `^mac`.
- `[R]` xpra: `getOS()` finisce in una *capability* verso il server; `isMobile()` decide solo se
  mostrare la sua tastiera JS.

⇒ ⭐ **La distinzione fisica/a schermo, in tutti e quattro, è IMPLICITA e passa da un bit solo: il 229.**
Nessuno ha un ramo per la tastiera fisica su Android. **Non c'è precedente da copiare: va inventato.**

### ⛔ Sulla LATENZA, il fork più recente va nella direzione OPPOSTA alla nostra

`[R]` KasmVNC `core/input/keyboard.js:19` `const thresholdTime = 16;` e `:118-154`: i tasti finiscono
in `_rfbKeyQueue` e partono dentro un `requestAnimationFrame`, **solo se sono passati > 16 ms**
dall'ultimo invio. ⇒ **Aggiunge da 1 a 2 quadri (≈16-33 ms) prima dell'invio.** Introdotto dalla PR
kasmtech/noVNC **#137** «Bugfix/vnc 130 ime race condition» (commit `009bd472`, 18 lug 2025):
`[?]` l'intento sembra serializzare press/release rispetto agli eventi IME, **non** ridurre il ritardo.

`[R]` noVNC invece manda **sincrono**: `sendKey` → `RFB.messages.keyEvent` → `sock.flush()`
(`core/rfb.js:472-497`, `:3092-3101`, `core/websock.js:221-226`). Il suo unico accorpamento è sul
**mouse** (`const MOUSE_MOVE_DELAY = 17;`, `core/rfb.js:47`).
`[R]` Guacamole manda sincrono sul WebSocket (`Tunnel.js:948-960`), **ma** rimanda di un giro del
loop ogni keydown giudicato «inaffidabile» (`Keyboard.js:1132-1139`, `setTimeout(interpret_events, 0)`).
`[R]` xpra manda con `setTimeout(…, delay)` e `delay` è 0 salvo sospetto di Ctrl+V (`Client.js:1152-1174`).

⇒ ⭐ **La nostra scelta (spedire dentro il gestore, senza coda) è la migliore delle quattro per il
ritardo, e non va toccata.** `CODER.md` §1-bis è dalla parte giusta.

### ⭐ Una cosa da rubare a KasmVNC: il misuratore

`[R]` KasmVNC `core/rfb.js:1052-1054` (`this._trackInputEvent('keydown', 0, 0)`) e `:2551-2585`:
statistiche di latenza input lato client, evento `inputlatency` con **p50/p95/p99** e le medie di
rete e di disegno separate. Introdotto dalla PR #203 (ago 2026). ⇒ È la forma dello strumento che
ci manca (§6), fatta da qualcuno che non ci conosce.

### Le issue che valgono, e quel che NON esiste

- `[R]` noVNC **#275** «Keyboard input does not work in Chrome on Android», chiusa — *la* issue del
  229 (*«Key event (keyCode = 229) not found on keyDownList»*); conclusione dei manutentori:
  «*The problem might not be in noVNC but rather in Chrome on Android*».
- `[R]` noVNC **PR #301** (4 ott 2013), merged — l'origine della textarea nascosta.
- `[R]` noVNC **#1727** — Samsung DeX, Galaxy S22 Ultra + Chrome 108: **i movimenti del mouse non
  arrivano** senza pulsante premuto. Chiusa `notourbug`. ⚠ **È lo stesso difetto che il nostro
  commento a `src/pagina.html:3636-3649` ha già misurato `[M]` e curato con `pointermove`** — e noi
  l'abbiamo curato, loro no. ⭐ È l'unica issue DeX esistente in tutti e quattro i progetti.
- `[R]` Guacamole **GUACAMOLE-621** (aperta): Gboard inserisce caratteri di controllo in più —
  è il difetto della deduzione backspace/delete da lunghezza+cursore; **GUACAMOLE-1423** (aperta):
  il backspace cancella 8, poi 67, poi 345 caratteri; **GUACAMOLE-380** «Automatically select text
  input on mobile» è **«In Progress» da anni**.
- ⛔ **Nessuna issue «keyboard lag Android», «hardware keyboard Android» o «Samsung DeX» in nessuno
  dei quattro progetti.** ⇒ `[?]` O nessuno usa una tastiera fisica su Android con questi client,
  o quando la usa **funziona** — che è la lettura coerente con la prova A.

---

## 6. `navigator.keyboard` su Chrome per Android e DeX — ⭐ e una `[?]` del progetto si CHIUDE

### La Keyboard Lock **esiste** su Android, e **solo da Android 16 QPR1**

`[R]` `content/browser/renderer_host/render_widget_host_view_android.cc:2745-2762`:

```cpp
bool RenderWidgetHostViewAndroid::LockKeyboard(
    std::optional<base::flat_set<ui::DomCode>> codes) {
  ...
  if (!window_android->SetHasKeyboardCapture(true)) {
    return false;
  }
  keyboard_locked_ = true;
```

`[R]` e il lato Java, `ui/android/java/src/org/chromium/ui/base/WindowAndroid.java:1803-1815`:

```java
private boolean setHasKeyboardCapture(boolean hasCapture) {
    Window window = getWindow();
    if (window == null) return false;
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.BAKLAVA
            && Build.VERSION.SDK_INT_FULL >= Build.VERSION_CODES_FULL.BAKLAVA_1) {
        WindowManager.LayoutParams params = window.getAttributes();
        params.setKeyboardCaptureEnabled(hasCapture);
        window.setAttributes(params);
        return true;
    }
    return false;
}
```

⇒ ⭐⭐ **`BAKLAVA` è Android 16 e `SDK_INT_FULL >= BAKLAVA_1` è Android 16 QPR1.** La deduzione che
`fasi/rapporti/F4-A9-scorciatoie.md:301` teneva come `[?]` — *«la lock esiste solo da lì»* — **ora è
letta nel sorgente**: `[R]`, con file e riga. ⛔ Sotto Android 16 QPR1 `setHasKeyboardCapture`
ritorna `false` ⇒ `LockKeyboard` ritorna `false` ⇒ **la promessa di `keyboard.lock()` fallisce**, e
la pagina lo saprà.
⚠ Resta `[?]` **sul dispositivo**: che sul DeX vero la cattura arrivi davvero fino a `keydown` è una
misura, non una lettura.

### ⛔⛔ `getLayoutMap()` su Android **risponde, e risponde VUOTO** — la trappola

`[R]` `third_party/blink/renderer/modules/keyboard/keyboard.idl` — nessun `[RuntimeEnabled]`, nessuna
esclusione Android ⇒ **`navigator.keyboard` esiste** su Chrome per Android.
`[R]` La catena: `keyboard_lock_service_impl.cc:137-155` → `PageImpl::GetKeyboardLayoutMap`
(`page_impl.cc:366-368`) → `RenderWidgetHostImpl::GetKeyboardLayoutMap`
(`render_widget_host_impl.cc:3656-3661`) → `view_->GetKeyboardLayoutMap()`.
`[R]` E `render_widget_host_view_android.cc` **non ridefinisce `GetKeyboardLayoutMap`** (cercato
`LayoutMap` in tutto il file: zero occorrenze) ⇒ vale la base,
`render_widget_host_view_base.cc:464-467`:

```cpp
RenderWidgetHostViewBase::GetKeyboardLayoutMap() {
  NOTIMPLEMENTED_LOG_ONCE();
  return base::flat_map<std::string, std::string>();
}
```

⇒ ⭐⭐ **Su Chrome per Android la promessa si RISOLVE con successo e la mappa è VUOTA.**
`[R]` E il servizio marca `status = kSuccess` comunque (`keyboard_lock_service_impl.cc:152`).
⛔ **Non lancia, non rifiuta, non dice niente.** Chi scrivesse `if (navigator.keyboard) { … }` per
decidere la disposizione della tastiera **su DeX prenderebbe una mappa vuota per «tastiera
americana»**. È la forma E2 di `REVIEWER.md` — un ripiego in silenzio — e sta nel motore, non da noi.

⚠ `[S]` MDN dà `chrome_android: "mirror"` per `Keyboard`, `lock`, `unlock` e `getLayoutMap`
(`mdn/browser-compat-data`, `api/Keyboard.json`, letto oggi): **«mirror» vuol dire "copiato dal
desktop", non "verificato su Android"**. ⇒ La tabella di compatibilità **non è una fonte** su questo
punto; il sorgente sì.

⚠ `[R]` KasmVNC usa `navigator.keyboard.getLayoutMap()` per rimappare `Ctrl+lettera`
(`core/rfb.js:323`, `core/input/keyboard.js:34-41`, `:273-283`). `[?]` Su Android quella rimappatura
lavorerebbe su una mappa vuota.

---

## 7. ⭐ LE MISURE CHE DECIDONO — quattro, e tre costano meno di dieci righe

*In ordine: prima si guarda, poi si cambia.*

| # | che cosa | come | che cosa separa |
|---|---|---|---|
| **1** | ⭐ **c'è «composizione» in `REMOTIX.input_classico.ripieghi`?** | si legge il registro della sessione DeX già fatta — **costo zero, e si fa adesso** | se **non** c'è, l'ipotesi dell'IME è **morta** (e la prova B è completa). Se c'è, si torna a leggere §1 |
| **2** | ⭐⭐ **`performance.now() - ev.timeStamp`** dentro `cl_su_keydown` | una riga. `[R]` `ev.timeStamp` è `event.getEventTime()` di Android, cioè **l'istante dell'evento di sistema** | ⇒ **il ritardo PRIMA di JavaScript**. Grande (> 50 ms) = Bluetooth + IME + DeX + coda del thread principale. Piccolo (< 5 ms) = il ritardo è **dopo**: rete, server, iniezione, video |
| **3** | ⭐⭐ **il campo `input` dei fotogrammi**, che oggi si legge e si butta | `[R]` `src/pagina.html:1568`; l'`id` sta già in `CL_SPEDITI` con il suo istante | ⇒ **il ritardo battuta→pixel**, cioè quel che l'utente giudica davvero. Separa «la tastiera è lenta» da «il video è vecchio» |
| **4** | **scrivere nella barra degli indirizzi di Chrome sullo stesso DeX** | un minuto, nessun codice | se lagga anche lì, `[?]` **non è REMOTIX**: è il DeX |

⚠ E una misura di controllo che vale la pena: **rifare la sessione DeX con `?video=worker`**
(`[R]` `src/pagina.html:527-529`). Se la tastiera smette di andare a scatti con il disegno spostato
fuori dal thread principale, il candidato n. 1 è **provato**. `[R]` Sul palco di sviluppo il worker
non tolse ritardo *al video* (`[M]` 13 ago, banco `03-b17`) — ⭐ ma **nessuno guardò la tastiera**, e
la tastiera è l'unica cosa che quel worker può salvare **anche senza velocizzare un fotogramma**.

---

## 8. Le riscritture che questo studio giustifica (nell'ordine, e non prima delle misure)

| | dove | che cosa | perché |
|---|---|---|---|
| **1** | `src/pagina.html:250` | dare `tabindex="-1"` alla tela | `[R]` `focus()` su un canvas senza tabindex è un colpo a vuoto: `:5628` e `:5780` non fanno quel che dichiarano. `[R]` noVNC ha la riga (`core/rfb.js:233`) |
| **2** | `src/pagina.html:240-246` / il foglio a `:184-190` | togliere il modulo dal giro del fuoco quando lo schermo è acceso | `[R]` §1, il fuoco resta nel campo della parola d'ordine ⇒ **IME acceso e battute scartate da `cl_nel_modulo`** finché non si clicca |
| **3** | `src/pagina.html:3808-3811` e `:3828-3831` | dire che `AltGraph` **non esiste su Android** | `[R]` `web_input_event_builders_android.cc:93-96`. Oggi `AltGr+e` su DeX diventerebbe un comando |
| **4** | `src/pagina.html:3842-3847` | aggiungere `ev.code === ""` alla firma, e **contare** invece di dichiarare una volta | `[R]` la firma vera è una terna (§1, prova C); `[R]` `cl_ripiego:3297` rende la misura cieca sul numero |
| **5** | `src/pagina.html:3877-3883` | ⚠ decidere il ritmo di ripetizione delle **lettere** | `[R]` oggi le lettere ripetono al ritmo di Android e le posizioni al ritmo di GNOME: due ritmi in una tastiera |
| **6** | `src/pagina.html:1177-1179` | ⚠ **misurare** `willReadFrequently: true` prima di toglierlo | `[S]` spegne la GPU sulla tela; `[?]` che sia la causa dei 34 ms è una lettura, non una misura |

⛔ **Quel che NON va fatto**: mettere un elemento nascosto modificabile col fuoco per «avere le
lettere». §3 dice che non serve (le lettere arrivano già), che accenderebbe il ramo 229 che oggi è
morto, e che `[R]` **la tastiera a schermo si aprirebbe lo stesso**, perché con una tastiera fisica
attaccata Chrome la mostra di proposito.

---

## 9. Le `[?]` che restano, dichiarate

1. `[?]` **I 34 ms del disegno su DeX** — il numero è della macchina di sviluppo. Su un telefono
   nessuno l'ha guardato, e tutto il candidato n. 1 poggia lì.
2. `[?]` **Il blocco in testa alla coda sullo stream di input** — `[S]` la proprietà dello stream è
   certa, che sul filo dell'utente ci sia perdita **non è misurato**.
3. `[?]` **`showSoftKeyboard()` con tastiera fisica** — letto in `onKeyboardConfigurationChanged`;
   che valga **anche a ogni cambio di fuoco** non l'ho letto.
4. `[?]` **La Keyboard Lock sul DeX vero** — il sorgente dice che c'è da Android 16 QPR1; che
   arrivi fino a `keydown` è una misura mai fatta (ed era già la `[?]` di `F4-A9-scorciatoie.md:301`).
5. `[?]` **`AltGr` su DeX** — dedotto dal sorgente di Chrome, non provato sul dispositivo.
6. `[?]` **Il rimedio `ANDROID_CAPTURE_KEY_EVENTS`** — `[R]` è dietro una `ContentFeatureMap` e
   `SDK_INT <= 38`; se sia acceso nella Chrome di quel telefono non si legge dal sorgente.

---

## ⭐ E la riga da portarsi via

**L'ipotesi guardava il pezzo giusto della catena e il posto sbagliato dentro il pezzo.**
L'IME di Android c'entra con questa pagina — ma c'entra **dove il fuoco è rimasto nel modulo di
accesso**, che è un difetto di quattro caratteri di `tabindex`, non una latenza. Il ritardo che
l'utente sente ha sotto un numero che il progetto **aveva già misurato e attribuito al video**: 34
millisecondi per fotogramma su un thread che è **anche** quello che consegna i tasti.

⇒ Non è una teoria nuova: è **la stessa misura, letta da un'altra parte della catena**. E la
conferma o la smentita costa **una sottrazione** — `performance.now() - ev.timeStamp` — che questa
pagina può fare stasera.

---

## Fonti in rete

- [Chromium `ImeAdapterImpl.java`](https://github.com/chromium/chromium/blob/master/content/public/android/java/src/org/chromium/content/browser/input/ImeAdapterImpl.java)
- [WHATWG DOM Standard — default passive value](https://dom.spec.whatwg.org/#default-passive-value)
- [W3C WebTransport](https://www.w3.org/TR/webtransport/)
- [Chrome for Developers — `willReadFrequently` / Canvas2D](https://developer.chrome.com/blog/canvas2d) · [spec `will-read-frequently`](https://github.com/fserb/canvas2D/blob/master/spec/will-read-frequently.md)
- [MDN — `KeyboardEvent.code`](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code) · [MDN — Keyboard API](https://developer.mozilla.org/en-US/docs/Web/API/Keyboard_API) · [MDN — VirtualKeyboard.hide()](https://developer.mozilla.org/en-US/docs/Web/API/VirtualKeyboard/hide)
- [Chrome for Developers — VirtualKeyboard API](https://developer.chrome.com/docs/web-platform/virtual-keyboard) · [Keyboard Lock API](https://developer.chrome.com/docs/capabilities/web-apis/keyboard-lock)
- [Android — Keyboard devices (dispatch pre-IME)](https://source.android.com/docs/core/interaction/input/keyboard-devices) · [InputEventReceiver, batched consumption](https://android.googlesource.com/platform/frameworks/base/+/540219174d49/core/jni/android_view_InputEventReceiver.md)
- [noVNC #275](https://github.com/novnc/noVNC/issues/275) · [noVNC PR #301](https://github.com/novnc/noVNC/pull/301) · [noVNC #1727 (DeX)](https://github.com/novnc/noVNC/issues/1727)
- [kasmtech/noVNC PR #137](https://github.com/kasmtech/noVNC/pull/137)
- [Guacamole commit `fb610813` (GUAC-685, ignora 229)](https://github.com/apache/guacamole-client/commit/fb610813bf08c8fa93c3adcb659d73456ae0dd34) · [GUACAMOLE-621](https://issues.apache.org/jira/browse/GUACAMOLE-621) · [GUACAMOLE-1423](https://issues.apache.org/jira/browse/GUACAMOLE-1423)
- [xpra-html5 commit `078a9b13` (ignora 229 + oninput)](https://github.com/Xpra-org/xpra-html5/commit/078a9b1350370246c800c39e9bd5d90083001495) · [commit `378e9dc4` (`readonly`)](https://github.com/Xpra-org/xpra-html5/commit/378e9dc4d8a5f5b165ca171659283a7e808d95a8) · [xpra-html5 #147](https://github.com/Xpra-org/xpra-html5/issues/147)
- [Samsung Members — input lag su DeX senza filo](https://r1.community.samsung.com/t5/samsung-dex/terrible-input-lag-using-dex-wirelessly/td-p/11135006) · [SamMobile](https://www.sammobile.com/news/lower-input-lag-samsung-dex-wirelessly/)
- [Punch Through — BLE connection interval](https://punchthrough.com/ble-connection-interval-throughput/)
- [web.dev — Optimize input delay](https://web.dev/articles/optimize-input-delay)
