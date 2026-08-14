# F4-AND-5 — La latenza dell'input su Android, e dove si perde

Anello di studio, 14 agosto 2026. Nessun file del deposito toccato tranne questo; nessun `git`;
nessun server sulle porte riservate.

---

## 0. La risposta in tre righe

⭐ **La tesi «è il Wi‑Fi del telefono e il risparmio energetico di Android» NON regge come
spiegazione principale, e si può demolire con una misura che non contiene un solo salto di rete.**
`[S]` Il risparmio energetico 802.11 mette in coda il traffico **in discesa** all'access point, non
quello **in salita** dalla stazione; `[S]` Doze e App Standby si applicano a schermo spento e ad app
in background — su DeX lo schermo è acceso e Chrome è in primo piano; `[S]` e con un video che
scende a 30‑60 fotogrammi al secondo la stazione non entra mai in risparmio.

⭐ **La spiegazione che regge meglio è la nostra**, ed è doppia:
1. `[R]` la pagina, **in via predefinita**, decodifica il video e fa **due `drawImage` a
   fotogramma sul thread principale** (`src/pagina.html:527-529` — l'interruttore `?video=worker` è
   SPENTO), ed è lo **stesso thread** su cui deve arrivare il `keydown` e su cui gira
   `scrittore_input.write()` (`src/pagina.html:2641-2653`, `3340-3359`);
2. `[R]` `scrittore_input.write()` non è atteso e **la contropressione non è mai letta**
   (`src/pagina.html:2648-2652`): su una salita lenta la coda interna del `WritableStream` cresce
   senza limite e ogni battuta aspetta dietro a tutti i movimenti di puntatore già accodati.

⭐ **E la misura che le distingue esiste, costa quattro righe di JavaScript, e la pagina la calcola
già oggi e la butta via** (`src/pagina.html:4763`): `performance.now() − event.timeStamp`.

---

## 1. Dalla pressione del tasto alla chiamata del gestore JavaScript

### 1.1 La catena, tratto per tratto

`[S]` Il percorso ufficiale su Android è: dispositivo → `EventHub` (legge `evdev` dal nucleo) →
`InputReader` (decodifica secondo la classe del dispositivo) → `InputDispatcher` (trova la finestra
a fuoco, aspetta che sia pronta, consegna) → l'applicazione
([source.android.com/docs/core/interaction/input](https://source.android.com/docs/core/interaction/input),
[.../keyboard-devices](https://source.android.com/docs/core/interaction/input/keyboard-devices)).
Poi, dentro Chrome: processo del browser → processo del rendering (mojo) → **coda del thread
principale** → gestore JavaScript.

| tratto | costo | marca e provenienza |
|---|---|---|
| tasto → radio Bluetooth | ~ metà dell'intervallo di connessione, più le ritrasmissioni | vedi §3 |
| radio → `evdev` → `EventHub` → `InputReader` | non trovato pubblicato | `[M]` cercato il 14/8, nessuna misura per tratto |
| `InputDispatcher` → finestra | non trovato pubblicato | `[M]` idem |
| IME per tasti di tastiera **fisica** | `[?]` non verificato: sulla tastiera fisica l'IME è consultato ma di norma non trattiene | non ho trovato una fonte che lo misuri |
| processo browser → processo rendering | non trovato pubblicato | `[M]` idem |
| ⭐ **coda del thread principale del rendering** | **questo sì è misurabile dalla pagina** | §2 |

### 1.2 Misure pubblicate: quel che c'è e quel che non c'è

`[M]` (14 agosto 2026, ricerca in rete) **Non esiste una scomposizione pubblicata, tratto per
tratto, della latenza di tastiera su Chrome per Android.** Quello che esiste è:

- `[R]` Yufeng Shen, lista `input-dev` di Chromium: «*for chrome on android the starting point of
  input event latency is already the timestamp when the input event is received by the android*»
  ([thread](https://groups.google.com/a/chromium.org/g/input-dev/c/ekKmybxFV5M)). ⭐ È la riga che
  rende `event.timeStamp` uno strumento e non un dettaglio.
- `[R]` Rick Byers, stesso thread: la latenza «vera» non è tracciabile via software — il pannello
  aggiunge un ritardo non misurabile; Chromium usa **robot + telecamera ad alta velocità** come
  riferimento, e per il software insegue «*the portion of the latency that we can control*».
- `[R]` Analisi del team di Chrome citata nell'esplicativo delle *scheduling APIs*: su **Chrome per
  Android**, il **18,76 %** delle interazioni lente (> 200 ms) ha un **compito lungo JavaScript
  (> 100 ms) che blocca l'input**
  ([WICG/scheduling-apis](https://github.com/WICG/scheduling-apis/blob/main/explainers/yield-and-continuation.md)).
  ⭐ Un'interazione lenta su cinque, su Android, è la coda del thread principale.
- `[R]` Letteratura: latenza dell'insieme touch su schermi commerciali **50–200 ms**; un
  dispositivo mobile moderno elabora eventi di tocco e Bluetooth «in roughly 20 to 30 ms»
  ([arXiv 1611.08520](https://arxiv.org/pdf/1611.08520)).
- `[S]` Google pubblica il metodo, non i numeri: **WALT** sincronizza un orologio esterno a meno di
  un millisecondo e separa ingresso e uscita
  ([Android Developers Blog, 2016](https://android-developers.googleblog.com/2016/04/a-new-method-to-measure-touch-and-audio-latency.html)).

`[?]` **Stima onesta, dichiarata come ipotesi**: fra la pressione fisica e la chiamata del gestore,
a thread principale **libero**, su un telefono recente: **15–35 ms**, di cui ~5–15 di Bluetooth e il
resto Android + Chrome. A thread principale **occupato**, la coda da sola può valere **quanto un
compito lungo**, cioè anche 50–150 ms. ⛔ Questa riga non è misurata: è esattamente ciò che la
misura di §8 va a prendere.

### 1.3 Un tratto che riguarda DeX e non il portatile

`[R]` Android **accorpa** gli eventi di movimento e li consuma al ritmo del `Choreographer`, cioè al
vsync: «*any MOVE event that has source = TOUCHSCREEN*» viene messo in lotto
([AOSP, batched consumption](https://android.googlesource.com/platform/frameworks/base/+/master/core/jni/android_view_InputEventReceiver.md)).
`[M]` Il documento **non nomina i tasti**: non ho trovato una fonte che dica che i `KeyEvent` siano
accorpati, e l'architettura suggerisce di no. ⇒ `[?]` **l'accorpamento al vsync colpisce il
puntatore, non la tastiera.**

⭐ Ma il vsync su DeX è **più grosso**: un monitor esterno gira quasi sempre a 60 Hz, cioè una
griglia da **16,7 ms**, mentre lo schermo del telefono gira a 120 Hz, griglia da **8,3 ms**. `[?]`
Tutto ciò che è allineato al vsync — consegna dei movimenti (Android), consegna di
`mousemove`/`pointermove`/`wheel` (Chrome, §6), e il **disegno** — su DeX costa il doppio di grana.
È un meccanismo specifico di DeX che **non c'entra niente col Wi‑Fi** e si misura in dieci secondi
(intervallo medio fra due `requestAnimationFrame`).

---

## 2. `event.timeStamp` e l'Event Timing API — ⭐ lo strumento che ci manca

### 2.1 La base di `event.timeStamp`

- `[S]` Da Chrome 49 `Event.timeStamp` è un `DOMHighResTimeStamp` **sulla stessa origine di
  `performance.now()`** — direttamente confrontabile
  ([Chrome for Developers](https://developer.chrome.com/blog/high-res-timestamps),
  [W3C hr-time-2](https://www.w3.org/TR/hr-time-2/)).
- `[R]` Per gli eventi di input Chromium **non** usa l'istante di creazione dell'oggetto DOM: usa il
  **timestamp grezzo del `PlatformEvent`**, generato quando il nucleo riceve l'evento
  ([input-dev](https://groups.google.com/a/chromium.org/g/input-dev/c/1ez9ojul490)).
- `[S]` Su Android quel timestamp è `SystemClock.uptimeMillis` (`MotionEvent.getEventTime()`,
  `KeyEvent.getEventTime()`).
- ⚠ `[R]` **Il caveat, e va scritto**: l'assunzione di Chromium che i timestamp di Android siano
  confrontabili con `base::TimeTicks` «*is based on AOSP implementation, not the Android API
  documentation or CTS*» (stesso thread `input-dev`). Su un dispositivo Samsung con firmware
  proprio, `[?]` non è garantito. ⇒ La difesa è quella che la pagina già fa per il tocco
  (`src/pagina.html:4763`: si accetta `timeStamp` solo se dista meno di 5 s da `performance.now()`),
  ma va **estesa al modo classico**, che oggi la salta (`src/pagina.html:3342`).
- `[S]` Risoluzione: dalla versione 91 Chrome limita i timer espliciti a **100 µs** su tutte le
  piattaforme senza isolamento cross‑origin
  ([Chrome for Developers](https://developer.chrome.com/blog/cross-origin-isolated-hr-timers)).
  Irrilevante su un tetto di 50 ms.

⭐ **Conclusione**: `performance.now() − event.timeStamp`, letto **come prima riga del gestore**,
misura **tutta la catena di §1 fino alla chiamata del gestore**, e **non contiene un solo salto di
rete**. È la lama che taglia il problema in due.

### 2.2 Event Timing API

- `[S]` `PerformanceEventTiming` c'è su **Chrome per Android da 76** (luglio 2019);
  `interactionCount` è in Interop 2025 su tutte le piattaforme Blink, Android compresa
  ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceEventTiming),
  [Intent to Ship](https://groups.google.com/a/chromium.org/g/blink-dev/c/vHyONs6Tr9k)).
- `[S]` Che cosa misura esattamente ([W3C Event Timing](https://www.w3.org/TR/event-timing/)):
  - `startTime` = «*the associated event's `timeStamp` attribute value*» ⇒ **è l'istante hardware**,
    lo stesso di §2.1;
  - `processingStart` = «*captured at the beginning of the event dispatch algorithm… when event
    handlers are about to be executed*»;
  - `processingEnd` = fine dei gestori;
  - `duration` = fino al **prossimo aggiornamento del rendering**, «*rounded to the nearest 8ms*».
  - ⇒ **ritardo d'ingresso = `processingStart − startTime`**; lavoro dei gestori =
    `processingEnd − processingStart`; ritardo di presentazione = il resto di `duration`.
- ⛔ `[S]` **Due trappole da conoscere prima di scrivere il codice**:
  1. la soglia predefinita è **104 ms**: senza `durationThreshold: 16` (il minimo consentito) **non
     si vede quasi nessuna battuta**;
  2. `keydown` e `keyup` sono nell'elenco; `mousemove`, `pointermove`, `touchmove` e `wheel` sono
     **esclusi in quanto continui**. ⇒ per il puntatore l'Event Timing **non serve**, e resta solo
     il conto a mano di §2.1.
- `[S]` INP è il 75° percentile delle interazioni su 28 giorni: è una metrica di campo, non uno
  strumento da banco. Per noi serve la **distribuzione grezza**, non l'INP.

---

## 3. Bluetooth — quanto pesa davvero

- `[S]` Bluetooth LE: fino a Core 6.2 il **minimo intervallo di connessione è 7,5 ms** (133 Hz);
  Core 6.2 introduce *Shorter Connection Intervals* fino a **375 µs**
  ([Bluetooth SIG](https://www.bluetooth.com/blog/how-bluetooth-shorter-connection-intervals-will-impact-the-next-generation-of-wireless-innovations/),
  [SIG, ultra-low latency HID](https://www.bluetooth.com/bluetooth-resources/standardizing-ultra-low-latency-hid-with-bluetooth-technology/)).
  ⇒ `[?]` attesa media ≈ 3,75 ms, coda a ~7,5 ms per ritrasmissione, quindi **4–12 ms** tipici.
- `[R]` Bluetooth **Classic** HID in *sniff mode*: intervallo tipico **15 ms**, in altre
  realizzazioni **50 ms**, e «*although the HID can wake up immediately after an event, it may have
  to wait up to 100 mS to transmit its data to the host*»
  ([US 11849472](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11849472)).
  ⇒ ⚠ **una tastiera Classic in sniff largo può da sola spiegare decine di millisecondi.**
- `[R]` Voce da forum, tenuta per quel che vale: «*Bluetooth HID runs on slotted polling and can add
  10‑30 ms*».

⭐ **Quanto pesa rispetto al resto**: su 139 ms, `[?]` **da 5 a 30 ms**, cioè fra il 4 % e il 22 %.
Non è il colpevole, ma **non è trascurabile e su DeX potrebbe essere peggiore che sul portatile** —
perché sul portatile la tastiera è cablata alla scheda madre e su DeX è Bluetooth.
⭐ **E si distingue gratis**: attaccare la stessa tastiera **via USB** all'hub DeX e rifare la misura
di §8. Se `performance.now() − event.timeStamp` cala, era il Bluetooth; se non cala, non era.
(`[R]` Samsung raccomanda esattamente questo per il DeX senza filo: collegare tastiera e mouse via
USB al monitor invece che al telefono
— [SamMobile](https://www.sammobile.com/news/lower-input-lag-samsung-dex-wirelessly/)).

---

## 4. ⭐ WebTransport su Android, Wi‑Fi del telefono, risparmio energetico

### 4.1 WebTransport: differenze fra Android e desktop

`[M]` (14 agosto 2026, ricerca in rete) **Non esiste un elenco pubblicato di difetti di WebTransport
specifici di Chrome per Android.** Quel che ho trovato:

- `[S]` Chrome supporta WebTransport **dalla 97 su Windows, macOS, Linux, ChromeOS e Android** — la
  stessa versione, senza note di piattaforma
  ([Chromium Blog](https://blog.chromium.org/2021/11/chrome-97-webtransport-new-array-static.html),
  [Chrome for Developers](https://developer.chrome.com/docs/capabilities/web-apis/webtransport)).
- `[R]` Victor Vasiliev (autore della specifica), 4 novembre 2022: «*The Google implementation of
  WebTransport does work on Android (that's what Chromium uses)*»
  ([web-transport-dev](https://groups.google.com/a/chromium.org/g/web-transport-dev/c/rOWUopZVI6E)).
- `[R]` L'unica differenza documentata è **di banco, non di prodotto**: `adb reverse` inoltra solo
  TCP, quindi HTTP/3 (UDP) non passa e i test WPT di web-transport **non girano su Android**
  ([wpt#43291](https://github.com/web-platform-tests/wpt/issues/43291)). ⚠ Conseguenza vera per noi:
  **WebTransport su Android è meno provato in automatico che su desktop**, il che è un motivo per
  misurare, non una prova di difetto.
- `[R]` Sulla pila di rete: Chromium legge i pacchetti UDP su **un solo thread**
  (`Chrome_ChildIOT`), un `recvmsg` per pacchetto
  ([arXiv 2310.09423](https://arxiv.org/html/2310.09423v2)). `[?]` Su un telefono, con la codifica
  video in discesa a piena banda, quel thread è più caricato che su un portatile — ma è **in
  discesa**, cioè tocca il fotogramma, non la battuta.

⇒ `[?]` **Nessuna prova che WebTransport si comporti peggio su Android.** Se ci fosse un difetto,
sarebbe nuovo, e la misura di §8 lo isolerebbe come «tempo fra il `write()` e l'arrivo al server».

### 4.2 Il risparmio energetico di Android — ⭐ dove la tesi dell'utente si rompe

Tre meccanismi diversi, e **nessuno dei tre si applica al caso DeX**:

1. **Doze / App Standby.** `[S]` Doze scatta quando il dispositivo è **fermo, a schermo spento e non
   in carica**; dalla 7.0 c'è un Doze «leggero» che scatta a **schermo spento**. Le app in **primo
   piano** sono esenti da App Standby
   ([developer.android.com](https://developer.android.com/training/monitoring-device-state/doze-standby),
   [source.android.com](https://source.android.com/docs/core/power/platform_mgmt)).
   ⛔ **Su DeX lo schermo è acceso, il telefono è in carica e Chrome è in primo piano: Doze non
   entra mai in gioco.** Questa metà della tesi è **falsificata da specifica**, non da ipotesi.

2. **Risparmio energetico 802.11 (PS‑Poll / U‑APSD).** `[S]` Il meccanismo è che **l'access point
   mette in coda il traffico DIRETTO ALLA STAZIONE** e lo consegna al DTIM o su trigger; il DTIM
   tipico è beacon (≈102,4 ms) × periodo. Le code «*may lead to a couple of hundred milliseconds of
   latency*»
   ([7SIGNAL](https://7signal.com/blog/power-management-in-client-devices/),
   [WMM‑PS](https://wifisharks.com/2020/09/26/wmmps/)).
   ⛔ **Tre ragioni per cui non spiega la tastiera laggata**:
   - `[S]` è **traffico in discesa**: la battuta viaggia **in salita**, e una stazione che ha da
     trasmettere si sveglia e trasmette («*the enhanced timer-based power management scheme wakes up
     the radio transceiver when an outgoing frame is generated by the station so that
     delay-intolerant uplink traffic is transmitted in a timely manner*»);
   - `[S]` con un video che scende a 30‑60 fotogrammi al secondo la stazione **non si riaddormenta
     mai** — «*a station may wake up when delay-sensitive traffic arrives at its buffer and will
     stay awake*»;
   - ⭐ e se davvero fosse il risparmio energetico, **la firma sarebbe riconoscibile**: una
     distribuzione **bimodale** con un pavimento intorno al periodo di beacon (~100 ms), non un
     ritardo diffuso. Si guarda l'istogramma, non la media (§8, misura C).
   ⚠ **Quel che resta in piedi**: `[S]` Android **non** disattiva il risparmio energetico Wi‑Fi da
   solo; lo disattiva solo se un'app prende un `WifiLock` `WIFI_MODE_FULL_HIGH_PERF` o
   `WIFI_MODE_FULL_LOW_LATENCY` — è un obbligo del CDD, e in modalità bassa latenza «*power save is
   explicitly disabled by WifiLockManager*»
   ([AOSP, Wi‑Fi low-latency mode](https://source.android.com/docs/core/connect/wifi-low-latency),
   [CDD 7.4](https://android.googlesource.com/platform/compatibility/cdd/+/refs/heads/master/7_hardware-compatibility/7_4_data-connectivity.md)).
   ⛔ **Chrome non prende quel lock**, e una pagina web **non può chiederlo**: `[?]` è l'unico
   residuo credibile della tesi dell'utente, e riguarda **la discesa del video**, non la salita
   della battuta.

3. **Governatore della CPU / core piccoli / calore.** `[R]` Chrome usa `cpuset`: i thread non
   urgenti finiscono sui **core piccoli**, gli urgenti possono girare ovunque; e «*even if the
   thread runs on a big core, if frequency is reduced due to thermal throttling… its performance
   will decline*»
   ([ChromiumOS kernel scheduler](https://www.chromium.org/chromium-os/developer-library/reference/kernel/kernel-scheduler/),
   [AOSP jank capacity](https://source.android.com/docs/core/tests/debug/jank_capacity),
   [Perfetto CPU](https://androidperformance.com/en/2025/11/12/Android-Perfetto-09-CPU/)).
   ⭐ **Questo sì è un meccanismo di risparmio energetico che colpisce la tastiera** — ma passa per
   **il thread principale del rendering**, cioè per §7, non per la rete. Un telefono che pilota un
   monitor esterno, decodifica 1080p e sta in carica è **caldo**: è lo scenario in cui il tetto
   termico morde di più.

### 4.3 ⛔ La domanda che vale più di dieci misure

⭐ **DeX è collegato col filo (USB‑C → HDMI) o senza filo?**
`[R]` Il DeX **senza filo** usa Wi‑Fi Direct verso il monitor, **sulla stessa radio** che porta il
nostro QUIC, e le segnalazioni parlano di «*input lag… almost half a second*»; il rimedio consigliato
da Samsung è attaccare tastiera e mouse **al monitor**, non al telefono
([SamMobile](https://www.sammobile.com/news/lower-input-lag-samsung-dex-wirelessly/),
[Samsung Community](https://r1.community.samsung.com/t5/samsung-dex/terrible-input-lag-using-dex-wirelessly/td-p/11135006)).
⛔ Se DeX è senza filo, **una parte del ritardo non è né nostra né del risparmio energetico: è il
collegamento del display**, e nessuna ottimizzazione della pagina la toglierà. La domanda costa
zero e va fatta **prima** di misurare.

---

## 5. Messaggi piccoli e frequenti su WebTransport: che cosa dice la documentazione

`[S]` ([Chrome for Developers](https://developer.chrome.com/docs/capabilities/web-apis/webtransport),
[W3C explainer](https://github.com/w3c/webtransport/blob/main/explainer.md)):

| strada | che cosa dice la specifica | giudizio per noi |
|---|---|---|
| **datagrammi** | «*ideal for sending and receiving data that don't need strong delivery guarantees*»; limitati dalla MTU; possono perdersi e arrivare fuori ordine; **niente blocco di testa** | ⭐ giusti per la **posizione del puntatore** (conta l'ultimo valore) |
| **uno stream riusato** | affidabile e **ordinato dentro lo stream**; l'ordine **non** è garantito fra stream diversi | ✅ giusto per **tasti e pulsanti**, dove perdere un `keyup` lascia il tasto premuto |
| **uno stream per messaggio** | «*they can be opened and closed without as much overhead*» — ma restano frame di apertura, un FIN e stato per stream, e **l'ordine fra stream non è garantito** | ⛔ da non fare: ordine perso, byte in più, niente in cambio |

`[M]` **Misure pubblicate**: non ho trovato **nessun confronto rigoroso** stream‑riusato contro
datagrammi per messaggi piccoli. Circola un numero divulgativo — 75 ms (WebSocket) → 49 ms
(datagrammi WebTransport) — che `[?]` **non tratterei come dato**: non ho trovato il banco.

⭐ **Il rilievo che riguarda il nostro codice.** `[R]` Oggi **tutto** l'input — puntatore, pulsanti,
tasti — viaggia su **un solo stream ordinato** (`src/pagina.html:2641-2653`, obbligo di `RCP.md`
§2.5 e §7.3). ⇒ `[S]` Dentro uno stream l'ordine è garantito, quindi **un pacchetto UDP perso che
portava un movimento di puntatore trattiene dietro di sé la battuta successiva** finché non viene
ritrasmesso (un RTT). ⚠ È blocco di testa **dentro** lo stream — proprio quello che i datagrammi
esistono per evitare. `[?]` Su Wi‑Fi con perdita dell'1 % e RTT di 10 ms sono `[?]` ~0,1 ms in
media, trascurabile; su Wi‑Fi con perdita del 5 % e RTT di 40 ms comincia a vedersi. **Da misurare
prima di cambiare il protocollo.**

⭐⛔ **E il rilievo grosso: la contropressione non è letta.**
`[R]` `src/pagina.html:2648-2652`:

```js
manda: (tipo, corpo) => {
  scrittore_input.write(inquadra(tipo, corpo))
    .catch((e) => nota("il canale di input non ha accettato un messaggio: " + e));
},
```

La promessa non è attesa — **ed è giusto così per la latenza** (il commento a `:2637` lo dice, e ha
ragione). ⛔ Ma nessuno guarda mai `scrittore_input.desiredSize`. Se la salita si stringe (Wi‑Fi
debole, DeX senza filo che divide la radio, congestione QUIC), **la coda interna del
`WritableStream` cresce senza limite** e ogni `POSIZIONE_TASTO` parte **dietro a tutti i
`PUNTATORE` già accodati**. `[?]` Questa è un'ipotesi non verificata — ma è **il meccanismo che
spiega meglio di ogni altro «la tastiera è laggata **peggio** che sul portatile»**, perché è
l'unico che **cresce col carico e col numero di movimenti di mouse**, e sul portatile non si vede
mai. Si verifica con **una riga** (§8, misura D).

---

## 6. Throttling di Chrome per Android e `requestAnimationFrame`

- `[S]` **Scheda non in primo piano**: `requestAnimationFrame` **non viene chiamato** su pagina in
  background (dal 2011); i timer sono raggruppati a uno al secondo, e dalla 88 c'è il *throttling
  pesante* dei timer concatenati
  ([Background tabs in Chrome 57](https://developer.chrome.com/blog/background_tabs),
  [Chrome 88](https://developer.chrome.com/blog/timer-throttling-in-chrome-88)).
  ⇒ **Sulla scheda visibile e in primo piano non si applica niente di tutto questo.** ⛔ La tesi
  «il throttling ci rallenta» **non regge** finché la scheda è quella davanti.
- ⚠ **Ma c'è un modo di rompersi che su DeX è realistico**: DeX è un desktop a finestre. Se
  l'utente clicca su un'altra finestra, la scheda può diventare `document.hidden` → rAF si ferma →
  `[R]` **i `mousemove`/`pointermove` allineati a rAF smettono di essere consegnati**
  ([Intent to Ship: rAF Aligned Mouse Input](https://groups.google.com/a/chromium.org/g/blink-dev/c/Y9BrlDeS3x4/m/sYPyPULgBAAJ)).
  `[R]` Il commento a `src/pagina.html:3640-3648` racconta già un incidente di questa famiglia
  (`mousemove` non più consegnati, salvati passando a `pointermove`). ⇒ Vale la pena registrare
  `document.visibilityState` nel registro.
- ⭐ `[R]` **L'allineamento a rAF vale per il puntatore, non per i tasti**: `pointermove`,
  `mousemove`, `wheel` e `scroll` sono consegnati **appena prima di rAF** — fino a **16,7 ms** di
  ritardo aggiunto su un monitor a 60 Hz, e **di più se il thread principale è in ritardo sul
  vsync**. `[S]` E l'Event Timing conferma la stessa divisione dal lato opposto: gli eventi
  «continui» sono **esclusi** dalla specifica.
  ⇒ `[?]` **Sul mouse su DeX, 16,7 ms su 139 (12 %) sono attribuibili solo a questo**, e la cura
  non è nostra.
- `[R]` Il nostro invio **non** è dietro rAF: `src/pagina.html:4366-4381` («⛔ NIENTE ACCORPAMENTO,
  e NIENTE `requestAnimationFrame`»), e la ragione scritta è `[M]` del 13 agosto: su Xvfb rAF non
  gira mai. ✅ **Scelta giusta, e va tenuta.**

---

## 7. `isInputPending()`, `scheduler.yield()`, listener `passive`

| API | stato | serve qui? |
|---|---|---|
| `navigator.scheduling.isInputPending()` | `[R]` **non c'è su Android**: l'implementazione richiede *site-per-process* per attribuire l'input, e su Android non è attivo in via predefinita ([Intent to Experiment](https://groups.google.com/a/chromium.org/g/blink-dev/c/ItkbDBevOrs/m/yFffQlqTBQAJ), [WICG/is-input-pending](https://github.com/WICG/is-input-pending)). `[S]` MDN lo dà per **deprecato**, sostituito da `scheduler.yield()` | ⛔ **No.** Sulla piattaforma che ci fa male non esiste. |
| `scheduler.yield()` | `[S]` c'è; spezza un compito lungo restituendo il controllo al browser ([WICG](https://github.com/WICG/scheduling-apis/blob/main/explainers/yield-and-continuation.md)) | ⚠ **Poco.** Il nostro compito lungo per fotogramma è `decode()` + due `drawImage`: non si può cedere il controllo **in mezzo** a un `drawImage`. Servirebbe solo per spezzare il ciclo di lettura degli stream. |
| listener `passive` | `[S]` `passive` decide se `preventDefault()` funziona; **non** cambia il momento in cui il gestore è chiamato per gli eventi discreti | ⛔ **No, e non si può.** `[R]` `src/pagina.html:3951` (`wheel`) e `:4897-4900` (i quattro `touch*`) sono `{passive:false}` **perché devono chiamare `preventDefault()`**: renderli passivi romperebbe il prodotto. Per `keydown`/`keyup` (`:3956-3957`) la questione non si pone. |

⭐ **Quel che invece serve davvero, ed è già in casa**: `?video=worker`
(`src/pagina.html:527-529`). È l'unica leva che **toglie lavoro al thread principale** invece di
riorganizzarlo.

---

## 8. ⭐ Prova a smentirmi: quale spiegazione regge, e la misura che le distingue

### 8.1 Le prove contro la tesi «è il Wi‑Fi e il risparmio energetico»

| prova | marca |
|---|---|
| Doze e App Standby non si applicano: schermo acceso, in carica, app in primo piano | `[S]` |
| Il risparmio energetico 802.11 accoda il traffico **in discesa**; la battuta va **in salita** e la stazione trasmette appena ha da trasmettere | `[S]` |
| Con 30‑60 fotogrammi al secondo in discesa la stazione **resta sveglia** | `[S]` |
| Se fosse risparmio energetico la firma sarebbe **bimodale a ~100 ms**, non un ritardo diffuso | `[S]` (DTIM = beacon × periodo) |
| Nessun difetto noto di WebTransport su Chrome per Android | `[M]` ricerca senza esito |

### 8.2 Le prove a favore delle spiegazioni alternative

| prova | marca |
|---|---|
| ⭐ La pagina fa **decodifica + due `drawImage` a fotogramma sul thread principale** in via predefinita: `VIDEO_WORKER` è spento | `[R]` `src/pagina.html:527-529`, `1953`, `1491` |
| ⭐ **Lo stesso thread** riceve `keydown` e chiama `scrittore_input.write()` | `[R]` `src/pagina.html:2641-2653`, `3340-3359`, `3956-3957` |
| ⭐ `drawImage(VideoFrame)` **non è una copia**: è conversione di colore e trasferimento — nella catena vera costa **~600 µs a fotogramma** contro i 15 µs del cronometro isolato… **e questo è il numero del PORTATILE** | `[M]` del progetto, 13/8, `src/pagina.html:1235-1240` |
| Su Chrome per **Android**, il **18,76 %** delle interazioni > 200 ms ha un compito lungo JS che blocca l'input | `[R]` WICG |
| ⭐ La **contropressione non è mai letta**: la coda del `WritableStream` può crescere senza limite e mettere ogni battuta dietro ai movimenti già accodati | `[R]` `src/pagina.html:2648-2652` + `[?]` sul comportamento |
| Chrome mette i thread non urgenti sui **core piccoli**; il tetto termico riduce la frequenza — un telefono che pilota un monitor e decodifica 1080p in carica è **caldo** | `[R]` ChromiumOS / AOSP |
| Su DeX il vsync è a **60 Hz** (16,7 ms) contro i 120 Hz del telefono: tutto ciò che è allineato al vsync raddoppia di grana | `[S]` + `[?]` |
| `[M]` del progetto del 13/8 dice che il worker «non toglie ritardo» — ⛔ **ma è misurato SUL PORTATILE**, dove il thread principale non è mai il collo di bottiglia. **Non trasferisce ad Android.** | `[R]` `src/pagina.html:476-481` |

⭐ **Verdetto**: la spiegazione che regge è **«il thread principale della pagina, aggravato su DeX
dal vsync a 60 Hz e dal tetto termico, più — da verificare — una coda di scrittura che cresce»**.
La tesi Wi‑Fi/risparmio energetico regge solo per un residuo: `[?]` la **discesa** del video, dove
Chrome non prende il `WifiLock` a bassa latenza. Non spiega una tastiera laggata.

### 8.3 ⭐ Le misure che le distinguono (in ordine di costo crescente)

**Misura 0 — la domanda, costo zero.** DeX col filo o senza? Se senza, `[R]` il collegamento del
display può da solo valere centinaia di millisecondi, e va tolto di mezzo prima di misurare altro.

**Misura A — il ping nudo, due minuti, nessun browser.** Da Termux sul telefono e dal portatile,
verso lo stesso server, sullo stesso access point: `ping -i 0.2 -c 300`. Si guardano p50, p95 e
**l'istogramma**.
⭐ **Che cosa decide**: se il p95 dal telefono è simile a quello dal portatile, **la tesi della rete
muore qui, in due minuti**, e senza aver toccato una riga di codice. Se invece compare un secondo
picco intorno ai 100 ms, il risparmio energetico c'è e si vede. Complemento: `adb shell iw dev wlan0
get power_save` (o `dumpsys wifi`) per leggere lo stato dichiarato.

**Misura B — ⭐ il ritardo d'ingresso, quattro righe, ZERO salti di rete.**
Prima riga di `cl_su_keydown`, `cl_su_keyup` e — dove è già calcolata e buttata via
(`src/pagina.html:4763`) — di `tocco_quando`:

```js
const dt = performance.now() - ev.timeStamp;   /* Android + Bluetooth + coda del thread */
REMOTIX.ingresso.push(dt);                     /* anello di 512, p50/p95/max nel registro */
```

e in parallelo, per avere la stessa grandezza da una fonte indipendente e la scomposizione in tre
fasi:

```js
new PerformanceObserver((l) => {
  for (const e of l.getEntries()) if (e.name === "keydown")
    REMOTIX.eventtiming.push({
      ingresso: e.processingStart - e.startTime,   /* ⭐ il ritardo d'ingresso */
      gestori:  e.processingEnd   - e.processingStart,
      totale:   e.duration });                     /* ⚠ arrotondato a 8 ms */
}).observe({ type: "event", durationThreshold: 16, buffered: true });
```

⛔ `durationThreshold: 16` **non è facoltativo**: senza, la soglia è 104 ms e non si vede niente
(`[S]` §2.2).

⭐ **Perché è LA misura**: `dt` **non contiene un solo byte di rete**. Se `dt` su DeX è grande, il
ritardo è **prima del gestore** — Android, Bluetooth, o coda del thread principale — e **il Wi‑Fi
non c'entra per definizione**. Se `dt` è piccolo, tutto il ritardo è **dopo**, e solo allora la rete
ha diritto di parola.

**Misura C — le quattro celle, per separare Android dalla nostra coda.** Stessa `dt`, quattro giri:

| | portatile | DeX |
|---|---|---|
| com'è oggi (video sul thread principale) | A1 | **A2** |
| `?video=worker` (decodifica e tela nel worker) | B1 | **B2** |
| sessione **senza video** (server senza `video.codec`, §2.5) | C1 | **C2** |
| tastiera **via USB** invece che Bluetooth | — | **D** |

Lettura:
- **A2 grande, B2 e C2 piccole** ⇒ ⭐ **è il nostro thread principale**: la cura è accendere il
  worker in via predefinita su Android, e il `[M]` del 13 agosto va **rimisurato sul telefono**
  invece che ereditato dal portatile.
- **A2 ≈ B2 ≈ C2, tutte grandi** ⇒ è Android/Bluetooth prima della pagina. Confronto con **D** per
  separare il Bluetooth dal resto.
- **A2 ≈ A1 piccole, ma l'anello resta 139+ ms** ⇒ il ritardo è a valle del gestore: allora, e solo
  allora, misura A e misura D.

**Misura D — la coda di scrittura, una riga.** Dentro `manda`, prima del `write`:

```js
if (scrittore_input.desiredSize <= 0) REMOTIX.contropressione++;
```

⭐ Se il contatore cresce su DeX e resta a zero sul portatile, **la tastiera è in coda dietro al
puntatore ed è colpa nostra**, non del Wi‑Fi. La cura sarebbe scartare i `PUNTATORE` quando
`desiredSize <= 0` (l'ultima posizione basta) e non scartare mai tasti e pulsanti — un `[?]` che
questa misura trasforma in decisione.

**Misura E — l'anello dall'interno, con quel che il protocollo già dà.** `[R]` §7.3 dà a ogni
messaggio un `id` crescente su tutto il canale e §6.2 lo rimanda indietro nel campo `input` del
fotogramma (`src/pagina.html:2629-2633`). ⇒ La pagina può tenere `t_spedito[id] = performance.now()`
e, quando arriva un fotogramma che porta quell'`id`, chiudere l'anello **con un orologio solo**,
senza sincronizzare le macchine. Sommata a `dt` e all'istante di disegno, spacca i 139 ms in
**quattro** tratti misurati anziché due misurati e due `[?]`.

**Misura F — il vsync di DeX, dieci secondi.** Intervallo medio fra due `requestAnimationFrame` sul
portatile e su DeX. `[?]` Se su DeX è 16,7 ms contro 8,3 del telefono, sono ~8 ms di grana in più
sul puntatore e sul disegno, gratis e non riducibili.

---

## 9. Quel che questo rapporto NON ha misurato

⛔ Detto invece che taciuto:
- `[M]` Non ho eseguito **nessuna misura sul dispositivo**: questo è uno studio di fonti e di
  sorgente. Ogni numero attribuito ad Android o al Bluetooth è `[S]`, `[R]` o `[?]`, mai `[M]`.
- `[M]` Non ho trovato **nessuna scomposizione pubblicata per tratto** della latenza di tastiera su
  Chrome per Android, né **nessun elenco di difetti** di WebTransport specifici di Android, né
  **nessun confronto rigoroso** stream contro datagrammi per messaggi piccoli. Le tre assenze sono
  esse stesse un risultato: **quei numeri, se ci servono, ce li dobbiamo prendere noi**.
- `[?]` Non è verificato che Chrome per Android non prenda mai un `WifiLock` a bassa latenza: ho
  trovato che l'API esiste ed è un obbligo del CDD, non l'assenza della chiamata in Chromium.
- `[R]` `[M]` con grep su `src/pagina.html` il 14 agosto 2026: **zero occorrenze** di
  `PerformanceObserver`, di `event-timing` e di qualunque calcolo di
  `performance.now() − event.timeStamp` conservato. La grandezza decisiva **è calcolata a riga
  4763 e scartata nella stessa espressione**.

---

## Fonti

- [Android — Input](https://source.android.com/docs/core/interaction/input) · [Keyboard devices](https://source.android.com/docs/core/interaction/input/keyboard-devices) · [Batched consumption (AOSP)](https://android.googlesource.com/platform/frameworks/base/+/master/core/jni/android_view_InputEventReceiver.md)
- [Android — Doze e App Standby](https://developer.android.com/training/monitoring-device-state/doze-standby) · [Platform power management with Doze](https://source.android.com/docs/core/power/platform_mgmt)
- [Android — Wi‑Fi low-latency mode](https://source.android.com/docs/core/connect/wifi-low-latency) · [CDD 7.4 Data connectivity](https://android.googlesource.com/platform/compatibility/cdd/+/refs/heads/master/7_hardware-compatibility/7_4_data-connectivity.md)
- [Android — jank e capacità CPU](https://source.android.com/docs/core/tests/debug/jank_capacity) · [ChromiumOS kernel scheduler (cpuset, big.LITTLE)](https://www.chromium.org/chromium-os/developer-library/reference/kernel/kernel-scheduler/) · [Perfetto: CPU](https://androidperformance.com/en/2025/11/12/Android-Perfetto-09-CPU/)
- [Android Developers Blog — WALT](https://android-developers.googleblog.com/2016/04/a-new-method-to-measure-touch-and-audio-latency.html)
- [Chromium input-dev — «How to capture real input latency time»](https://groups.google.com/a/chromium.org/g/input-dev/c/ekKmybxFV5M) · [Input Event Timestamps](https://groups.google.com/a/chromium.org/g/input-dev/c/1ez9ojul490) · [Intent to Ship: rAF Aligned Mouse Input](https://groups.google.com/a/chromium.org/g/blink-dev/c/Y9BrlDeS3x4/m/sYPyPULgBAAJ)
- [Chrome — High resolution timestamps for events](https://developer.chrome.com/blog/high-res-timestamps) · [Cross-origin isolated hr timers](https://developer.chrome.com/blog/cross-origin-isolated-hr-timers) · [W3C High Resolution Time L2](https://www.w3.org/TR/hr-time-2/)
- [W3C Event Timing API](https://www.w3.org/TR/event-timing/) · [MDN PerformanceEventTiming](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceEventTiming) · [Intent to Ship: interactionCount](https://groups.google.com/a/chromium.org/g/blink-dev/c/vHyONs6Tr9k) · [web.dev — Optimize input delay](https://web.dev/articles/optimize-input-delay)
- [Chrome — How to use WebTransport](https://developer.chrome.com/docs/capabilities/web-apis/webtransport) · [W3C WebTransport explainer](https://github.com/w3c/webtransport/blob/main/explainer.md) · [Chromium Blog — Chrome 97](https://blog.chromium.org/2021/11/chrome-97-webtransport-new-array-static.html) · [web-transport-dev — WebTransport on Android](https://groups.google.com/a/chromium.org/g/web-transport-dev/c/rOWUopZVI6E) · [wpt#43291 — h3/webtransport su Android](https://github.com/web-platform-tests/wpt/issues/43291)
- [Chrome — Background tabs in Chrome 57](https://developer.chrome.com/blog/background_tabs) · [Heavy throttling of chained JS timers (Chrome 88)](https://developer.chrome.com/blog/timer-throttling-in-chrome-88) · [Nolan Lawson — Browsers, input events, and frame throttling](https://nolanlawson.com/2019/08/14/browsers-input-events-and-frame-throttling/)
- [WICG — yield and continuation](https://github.com/WICG/scheduling-apis/blob/main/explainers/yield-and-continuation.md) · [WICG/is-input-pending](https://github.com/WICG/is-input-pending) · [Intent to Experiment: isInputPending](https://groups.google.com/a/chromium.org/g/blink-dev/c/ItkbDBevOrs/m/yFffQlqTBQAJ) · [MDN Scheduling.isInputPending](https://developer.mozilla.org/en-US/docs/Web/API/Scheduling/isInputPending)
- [Bluetooth SIG — Shorter Connection Intervals](https://www.bluetooth.com/blog/how-bluetooth-shorter-connection-intervals-will-impact-the-next-generation-of-wireless-innovations/) · [SIG — Ultra-low latency HID](https://www.bluetooth.com/bluetooth-resources/standardizing-ultra-low-latency-hid-with-bluetooth-technology/) · [US 11849472 (sniff mode HID)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11849472)
- [7SIGNAL — Power management in client devices](https://7signal.com/blog/power-management-in-client-devices/) · [WMM Power Save](https://wifisharks.com/2020/09/26/wmmps/)
- [arXiv 1611.08520 — End-to-end latency of interactive mobile video](https://arxiv.org/pdf/1611.08520) · [arXiv 2310.09423 — QUIC is not Quick Enough](https://arxiv.org/html/2310.09423v2)
- [SamMobile — input lag del DeX senza filo](https://www.sammobile.com/news/lower-input-lag-samsung-dex-wirelessly/) · [Samsung Community — terrible input lag using DeX wirelessly](https://r1.community.samsung.com/t5/samsung-dex/terrible-input-lag-using-dex-wirelessly/td-p/11135006)
