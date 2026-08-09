# S3 — La tastiera e gli appunti nel browser: che cosa si perde, motore per motore

*Rapporto della sonda del browser, misura **S3** (`PIANO.md` §1.2). Scritto il 9 agosto 2026.
Risponde a `SPECIFICHE.md` §7.3-bis e §9, e alle `[?]` che lì restavano aperte.*

⛔ **Questo rapporto non contiene nessuna `[M]`.** È fatto di specifiche lette (`[S]`), di codice
di riferimento letto (`[R]`) e di ipotesi dichiarate (`[?]`). Le misure sul ferro sono il §4.

---

## 1. La risposta in cinque righe

1. ⭐ **Il 2026 ha cambiato la risposta a metà domanda.** La Keyboard Lock non è più «solo Chrome»:
   `requestFullscreen({keyboardLock:"browser"})` è entrato nel **Fullscreen Standard del WHATWG
   l'8 maggio 2026**, l'ha spedito **Safari 26.4** (marzo) e **Firefox 151** (19 maggio) — e
   `SPECIFICHE.md` §7.3-bis va corretta di conseguenza.
2. ⭐ **E ha cambiato anche l'altra metà**: l'evento **`clipboardchange`** è in Chrome dal **13
   gennaio 2026** e la sua motivazione dichiarata è *«remote desktop applications»* — cioè si può
   sorvegliare gli appunti del dispositivo, **su Chromium, e solo mentre la pagina ha il fuoco**.
   Su Firefox e Safari **no**, ed è verificato, non dedotto.
3. ⛔ **Quel che resta perso è perso davvero e non si recupera**: `Ctrl+Alt+Canc`, l'uscita da
   schermo intero (`F11`, `⌘⌃F`, Esc tenuto premuto), **tutta la keyboard lock fuori da schermo
   intero**, **tutta la keyboard lock su mobile — DeX compreso** — e quel che il compositore Wayland
   *locale* si tiene prima ancora che il browser lo veda. ⭐ **Il canale delle posizioni invece è
   sano**: `code` → evdev copre **senza un buco** l'intera tastiera a 105 tasti (`evdev 1…94`).
4. ⛔ **Il difetto più grave non sono le scorciatoie: è il modificatore rimasto giù.** La specifica
   **non garantisce** il `keyup` alla perdita del fuoco, su macOS con `Cmd` premuto non arriva mai,
   su iOS non arriva mai — e da noi la sessione remota **sopravvive alla connessione**: un `Ctrl`
   incollato rende il desktop inservibile e non si ripara riconnettendosi.
5. ⛔ **Quel che la pagina deve dichiarare spento** è nella tabella del §2, ed è **una tabella per
   motore *e per sistema***, non per motore: quel che si perde su Chrome/Linux non è quel che si
   perde su Chrome/DeX.

---

## 2. ⛔ La tabella di quel che si perde — «dichiarato spento»

*Questa è la tabella che finisce in `SPECIFICHE.md`. Ogni riga è una cosa che la pagina **deve
dire all'utente** invece di far finta che funzioni. ⚠ Le celle marcate `[?]` sono quel che il banco
del §4 deve chiudere: **fino ad allora si dichiarano spente**, perché dichiarare spento qualcosa che
funziona costa un avviso di troppo, mentre il contrario è una bugia.*

### 2.1 Le capacità, motore per motore e sistema per sistema

| Capacità | Chrome/Edge desktop | Firefox desktop | Safari macOS | **Chrome su DeX** | Safari iPadOS |
|---|---|---|---|---|---|
| **schermo intero** avviato da JS | ✅ | ✅ | ✅ | ✅ | ⚠ **parziale** `[S]` |
| **keyboard lock** — quale API | `navigator.keyboard.lock()` **68+** `[S]` | `requestFullscreen({keyboardLock})` **151+** `[S]` — ⛔ **spenta su Android** | idem, **26.4+** `[S]` | ⛔ **`[?]` da misurare: dichiarata *«a no-op on mobile platforms»* all'atto dell'implementazione** `[S]` | ⚠ `[?]` — Safari 26.4 l'ha aggiunta, ma la Fullscreen API su iOS/iPadOS è a **supporto parziale**: senza schermo intero non c'è lock |
| lock **con elenco di tasti** | ✅ | ⛔ tutto-o-niente | ⛔ tutto-o-niente | ⛔ | ⛔ |
| lock **fuori** da schermo intero | ⛔ **mai** `[S]` | ⛔ **mai** `[S]` | ⛔ **mai** `[S]` | ⛔ | ⛔ |
| lock con schermo intero da **`F11`** | ⛔ **mai** — *«During F11 fullscreen, no Keyboard Lock processing […] will take place»* `[S]` | ⛔ | ⛔ | — | — |
| lock dentro un **`<iframe>`** | ⛔ `InvalidStateError` `[S]` | ⛔ | ⛔ | ⛔ | ⛔ |
| **`Ctrl+Alt+Canc`** | ⛔ **mai, in nessun caso** `[S]` | ⛔ | — | — | — |
| **uscita da schermo intero** (`F11`, `⌘⌃F`) | ⛔ mai annullabile `[S]` | ⛔ mai `[S]` | ⛔ mai `[S]` | — | — |
| **Esc** a schermo intero con lock | consegnato; uscita tenendo **2 s** `[S]` | consegnato; uscita con pressione lunga `[S]` | consegnato; uscita tenendo **1,5 s** `[S]` | ⛔ | ⛔ |
| **`getLayoutMap()`** (etichette dei tasti) | ✅ Chrome 69+ `[S]` | ⛔ | ⛔ | ✅ `[?]` | ⛔ |
| appunti: permesso **persistente** | ✅ `clipboard-read`/`clipboard-write` `[S]` | ⛔ **non esistono e non sono previsti** `[S]` | ⛔ **idem** `[S]` | ✅ | ⛔ |
| appunti: lettura **senza interfaccia** | ✅ col permesso concesso `[S]` | ⛔ **menu «Incolla» a ogni lettura**, attivo dopo **1 s** `[S]` | ⛔ **idem** `[S]` | ✅ | ⛔ |
| **`clipboardchange`** | ✅ **144+**, dal 13 gen 2026 `[S]` | ⛔ **no** `[S]` | ⛔ **no** `[S]` | ✅ **144+** `[S]` | ⛔ **no** `[S]` |
| appunti **senza il fuoco** | ⛔ mai | ⛔ mai | ⛔ mai | ⛔ mai | ⛔ mai |
| appunti: **immagini e file** | fuori disegno (`DECISIONI.md` §5-ter.1) | idem | idem | idem | idem |

### 2.2 Le sei righe che valgono su **tutti** i motori, e che vanno dichiarate una volta sola

| Che cosa si perde | Perché | Marca |
|---|---|---|
| ⛔ **`Ctrl+Alt+Canc`** | è la *secure attention sequence* di Windows; la specifica la esclude per nome | `[S]` |
| ⛔ **la via d'uscita da schermo intero** | la specifica **obbliga** l'implementazione a tenersene una: *«User agents should reserve an additional input for the purposes of exiting fullscreen»* | `[S]` |
| ⛔ **tutto, quando non si è a schermo intero** | la lock non esiste a finestra, su nessun motore. ⚠ **E su DeX la finestra ridimensionabile è proprio il modo d'uso** (`DECISIONI.md` §5-bis.0) | `[S]` |
| ⛔ **quel che il sistema si tiene prima del browser** | su Linux/Wayland il compositore locale *«is under no obligation to disable all of its shortcuts»*; su Android/DeX **`F1` apre il pannello scorciatoie di DeX comunque**; su iPadOS `⌘` tenuto premuto apre il foglio di sistema | `[S]` |
| ⛔ **la lettura degli appunti mentre la pagina non ha il fuoco** | nessuna API la concede, nemmeno `clipboardchange`, che al ritorno del fuoco consegna **un evento solo** senza storico | `[S]` |
| ⛔ **i tasti-funzione dei portatili moderni** — retroilluminazione tastiera, mute microfono, luminosità min/max/auto, privacy screen, dettatura, emoji, accessibilità, non disturbare | **44 codici evdev che Chromium riconosce e lascia senza nome `code`**: la pagina non può nemmeno sapere che sono stati premuti. ⚠ Non è un limite del nostro protocollo, è il confine di JavaScript | `[R]` §3.A.3 |

### 2.3 Come si legge questa tabella nel prodotto

⛔ **La pagina non dichiara «le scorciatoie»: dichiara *questa riga di questa tabella*.** Il testo
che l'utente vede si compone da tre dati che la pagina conosce a runtime — **motore, sistema,
stato dello schermo intero** — e cambia quando cambia il terzo. Il dettaglio in §5.3.

---

## 3. Il dettaglio

### 3.A La tastiera

#### 3.A.1 ⭐ La Keyboard Lock nel 2026 — la cosa più importante di questo rapporto

`SPECIFICHE.md` §7.3-bis dà la keyboard lock per «solo Chrome ed Edge». **Nei dodici mesi fra
l'aprile 2025 e il maggio 2026 la faccenda si è ribaltata**, e va scritto con le date perché è la
riga che cambia quali browser conviene consigliare.

| Data | Che cosa è successo | Marca |
|---|---|---|
| 2018 | Chrome 68 spedisce `navigator.keyboard.lock()`, specifica WICG. *«While in fullscreen, this API allows apps to receive keys normally handled by the system or the browser like Cmd/Alt-Tab, or Esc»* | `[S]` chromestatus 5642959835889664 |
| lug 2019 | ⛔ Mozilla dichiara posizione **negativa** su Keyboard Lock | `[S]` standards-positions #196 |
| 19 apr 2025 | **WebKit** propone una versione diversa, agganciata alla Fullscreen API | `[S]` WebKit/standards-positions #481 |
| 7 apr 2026 | Mozilla dichiara posizione **positiva** sulla nuova | `[S]` mozilla/standards-positions #1385 |
| 15 apr 2026 | Mozilla **chiude** la vecchia issue, confermando il negativo su quella | `[S]` #196 |
| 17 apr 2026 | Mozilla annuncia *Intent to prototype **& ship*** | `[S]` dev-platform |
| **8 mag 2026** | ⭐ **`keyboardLock` entra nel Fullscreen Standard del WHATWG** | `[S]` whatwg/fullscreen#232, *merged* |
| **19 mag 2026** | ⭐ **Firefox 151** lo spedisce, **solo desktop** (`dom.fullscreen.keyboard_lock.enabled`) | `[S]` note di rilascio + bug 2032302 |
| mar 2026 | ⭐ **Safari 26.4** lo spedisce | `[S]` webkit.org/blog/17862 |
| 17 mar 2026 | ⛔ Chrome **rinuncia** al permesso per keyboard lock e pointer lock introdotto nella 131: *«We have decided not to launch the Keyboard Lock and Pointer Lock permissions»* — i dati mostravano confusione sui siti legittimi e nessun beneficio su quelli truffaldini | `[S]` blog Chrome |

**Le due API, oggi, in concreto** `[S]`:

| | `navigator.keyboard.lock()` | `requestFullscreen({keyboardLock:"browser"})` |
|---|---|---|
| specifica | WICG, ferma al 6 ottobre 2021 | ⭐ **WHATWG Fullscreen**, viva |
| Chrome / Edge | ✅ **68+** | `[?]` — vedi §6.4 |
| Firefox | ⛔ no | ✅ **151+**, ⛔ **solo desktop, spento su Android** |
| Safari | ⛔ no | ✅ **26.4+** |
| granularità | elenco di `code`, o tutti | tutto o niente (`"browser"` / `"none"`) |
| valori dell'enum | — | `"browser"`, `"none"`. ⚠ Era stato proposto anche `"system"`, **tolto prima del merge** |
| uscita di sicurezza | Esc tenuto **2 s** (Chrome) | Esc tenuto **1,5 s** (Safari); su Firefox un avviso compare al triplo clic rapido o alla pressione lunga |
| rilascio | `unlock()`, o l'uscita da schermo intero | automatico all'uscita da schermo intero **o al cambio di scheda** |

**Che cosa la lock consegna e che cosa non consegna mai.** La specifica WHATWG è deliberatamente
vaga — *«Key events that would normally trigger user agent or system-level actions are instead
redirected to the web application in fullscreen»* `[S]` — e la vecchia WICG è esplicita
sull'incertezza:

> *«This API operates on a "best effort" basis. It is not required that a conforming implementation
> be able to override the OS default behaviour for every possible key combination.»* `[S]`

⛔ **I quattro limiti duri, che nessuna lock supera, su nessun motore:**

1. **`Ctrl+Alt+Canc` su Windows** — è la *secure attention sequence*, non è intercettabile `[S]`
   (WICG explainer; ripetuto da MDN);
2. **l'uscita da schermo intero** — «Esc tenuto premuto» su Chrome/Safari, e in più «i tasti del
   browser che fanno uscire da schermo intero, come **F11** o **⌘⌃F** su Mac, **non sono mai
   annullabili**» `[S]` (intent Mozilla). La specifica lo rende obbligatorio: *«User agents should
   reserve an additional input for the purposes of exiting fullscreen»* `[S]`;
3. ⛔ **la lock richiede uno schermo intero avviato da JavaScript.** La vecchia specifica è netta:
   *«During F11 fullscreen, no Keyboard Lock processing of keyboard events will take place»* `[S]`.
   Un utente che va a schermo intero con `F11` **non ha la lock**, e non se ne accorge;
4. **quel che il sistema si tiene prima del browser.** ⭐ **E su Linux questo è nostro pane**: il
   protocollo Wayland che serve a chiedere al compositore di lasciar passare tutto —
   `keyboard-shortcuts-inhibit-unstable-v1` — dice `[S]`:
   > *«The Wayland compositor is however under no obligation to disable all of its shortcuts, and
   > may keep some special key combo for its own use, including but not limited to one allowing the
   > user to forcibly restore normal keyboard events routing»*

   ⛔ **Quindi sul nostro sistema di casa la catena ha tre anelli, non due**: compositore locale →
   browser → pagina. La keyboard lock agisce sul secondo. `Super` e `Alt+Tab` del *desktop locale*
   possono sparire prima che il browser li veda, e nessuna API del browser li recupera.

**Altri requisiti, e le trappole** `[S]`:

- **contesto sicuro** (HTTPS) — entrambe le API. ⚠ Si lega a **S1**: il certificato accettato con
  un'eccezione fa contesto sicuro, ma è da confermare;
- **transient user activation** per `lock()` (MDN); e `requestFullscreen` la richiede comunque;
- **contesto di navigazione di primo livello**: `lock()` rigetta con `InvalidStateError` se non è
  *«in the currently active top-level browsing context»* `[S]`. ⛔ **La pagina non può stare in un
  `<iframe>`**;
- ⚠ **il permesso che non c'è più**: Chrome 131 aveva introdotto una richiesta di permesso, **e
  Chrome l'ha ritirata il 17 marzo 2026** `[S]`. ⛔ **Chi scrive il codice guardando un articolo del
  2024 o del 2025 troverà una richiesta di permesso che oggi non esiste.**

#### 3.A.2 Le scorciatoie che il browser si tiene

Vedi **la tabella del §2**, che è la consegna vera di questo rapporto. Qui restano tre cose che la
tabella non contiene.

**La distinzione che conta, e che non è «arriva / non arriva»**, ma **tre** stati:

| Stato | Che cosa vuol dire | Che cosa possiamo farci |
|---|---|---|
| **A — annullabile** | l'evento arriva alla pagina e `preventDefault()` ferma l'azione del browser | ⭐ **niente da fare: funziona già** |
| **B — consegnata ma riservata** | l'evento arriva, ma il browser esegue lo stesso la sua azione | ⛔ **il peggiore**: la sessione remota riceve la battuta **e** la scheda si chiude. La pagina la vede e non la può fermare |
| **C — non consegnata** | non arriva nessun evento | recuperabile solo con la lock |

⛔ **Lo stato B è quello che il banco deve saper distinguere**, e nessun articolo lo distingue: è
il motivo per cui il §4.5 mette due colonne diverse per «non c'è la riga» e «c'è la riga e la
scheda si chiude lo stesso».

**Il fatto meno noto e più utile**: ⭐ **in Chromium alcune scorciatoie del browser risultano
consegnate alla pagina quando è a schermo intero, senza nessuna lock.** L'*intent* che lo introdusse
lo dice esplicitamente `[S]`
([blink-dev, *Browser Shortcuts in Fullscreen*](https://groups.google.com/a/chromium.org/g/blink-dev/c/wlRDnLbyVlk)):

> «Ctrl/Cmd + (T | W | N) […] Ctrl/Cmd + Shift + (T | W | N) […] and the mouse forward and back
> buttons» sarebbero inviati all'applicazione web a schermo intero, con l'eccezione: «**Escape and
> F11 remain reserved to the browser**».

⚠ `[?]` **Ma quell'*intent* è del gennaio 2017 e non ho trovato conferma che il comportamento sia
ancora quello nel 2026.** ⛔ È una riga del banco, non una riga della specifica: si prova
`Ctrl+W` a schermo intero **senza** lock, e si guarda se la scheda si chiude. **Se questo è ancora
vero, metà del prezzo di `SPECIFICHE.md` §7.3-bis si paga solo a finestra, non a schermo intero.**

**E il ripiego che tutti hanno accettato**: bottoni nella pagina. noVNC ha una barra con
Ctrl/Alt/Windows/Tab/Esc/Ctrl-Alt-Canc come *interruttori* di modificatore (`app/ui.js:1766-1832`,
`core/rfb.js:449-456` `[R]`); Guacamole ha una tastiera a schermo la cui descrizione dichiara il
motivo `[R]` (`translations/en.json`): *«The on-screen keyboard allows typing of key combinations
that may otherwise be impossible (such as Ctrl-Alt-Del)»*. ⭐ **Tre prodotti maturi su tre: quel che
il browser non lascia passare, lo si fa cliccare.** È un requisito, non un ripiego di fortuna.

#### 3.A.3 ⭐ `KeyboardEvent.code` → evdev: completo dove serve, vuoto in periferia

*Domanda 3. È la metà «posizioni» di `DECISIONI.md` §5-bis.6, e la conclusione è buona — con tre
sorprese.*

⛔ **Prima sorpresa: la corrispondenza non sta nella specifica.** Il documento
[uievents-code](https://w3c.github.io/uievents-code/) è **Working Draft del 9 maggio 2023**, fermo
da tre anni, e ⛔ **non contiene alcuna colonna evdev, né Linux, né USB HID**: le sue tabelle hanno
tre colonne sole (`code`, *Required*, *Notes*). Verificato sul testo estratto: `evdev` → **0
occorrenze**, `linux` → **0 occorrenze**, mentre `scancode` e `USB HID` compaiono — cioè
**l'estrazione funzionava** `[S]`.

⭐ **La tabella canonica è di Chromium**, e si copia invece di riscriverla: `[R]`
`ui/events/keycodes/dom/dom_code_data.inc`, che ha **due colonne distinte** — intestazione verbatim
(riga 88):

```
  //            USB     evdev    XKB     Win     Mac   Code
```

e la riga che ci riguarda (riga 142):

```c
DOM_CODE(0x070004, 0x001e, 0x0026, 0x001e, 0x0000, "KeyA", US_A), // aA
```

→ **evdev `0x1e` = 30 = `KEY_A`**, che è esattamente il numero che passiamo a libei. ⭐ **Esiste già
anche la funzione inversa**: `KeycodeConverter::DomCodeToEvdevCode(DomCode)`,
`keycode_converter.cc:214-218` `[R]`.

⚠ **XKB non è evdev**: nel file sono due colonne, e vale `XKB == evdev + 8` — verificato su **tutte
le 246 righe attive, zero violazioni** `[R]`, con la costante dichiarata in
`keycode_converter.cc:72-73`: `// The offset between XKB Keycode and evdev code.` +
`constexpr int kXkbKeycodeOffset = 8;`. ⛔ **E la colonna usata cambia per piattaforma**
(`keycode_converter.cc:28-40` `[R]`): **XKB** su Linux desktop, **evdev grezzo** su Android.

**Il verdetto sulla copertura** `[R]`, contato meccanicamente:

| | |
|---|---|
| valori `code` nella specifica | **172** |
| di cui con un evdev in Chromium | **151 (88 %)** |
| ⭐ **Writing System · Functional · Control Pad · Arrow Pad · Media** | ⭐ **100 % — 105 su 105, senza un buco** |
| Numpad | 21 su 31 |
| Legacy/non standard | 8 su 18 |
| ⭐ **il codice evdev non raggiungibile più basso** | ⭐ **95** (`KEY_KPJPCOMMA`) |

⭐ **Quest'ultima riga è la risposta breve alla domanda 3: `evdev 1…94` — l'intera tastiera PC a 105
tasti, numpad, modificatori, `KEY_102ND`, `KEY_RO`, `KEY_YEN`, i tasti giapponesi — è coperta senza
buchi.** Per un desktop remoto la corrispondenza è completa.

**Seconda sorpresa: 333 dei 515 `KEY_*` di Linux (65 %) non sono nominabili da JavaScript** `[R]`
(confronto con `include/uapi/linux/input-event-codes.h`). ⛔ **E 44 di questi sono tasti che
Chromium *riconosce* e sceglie di non nominare** — ha la riga, sa il codice evdev, ha l'enum
`DomCode::`, e il campo `code` è `NULL`:

| Gruppo | Esempi (con evdev) |
|---|---|
| retroilluminazione tastiera | `KEY_KBDILLUMTOGGLE` 228, `KEY_KBDILLUMDOWN` 229, `KEY_KBDILLUMUP` 230 |
| microfono e camera | `KEY_MICMUTE` 248, `KEY_CAMERA_ACCESS_TOGGLE` 589 |
| luminosità | `KEY_BRIGHTNESS_AUTO` 244, `KEY_BRIGHTNESS_MIN` 592, `KEY_BRIGHTNESS_MAX` 593 |
| moderni | `KEY_EMOJI_PICKER` 585, `KEY_DICTATE` 586, `KEY_ACCESSIBILITY` 590, `KEY_DO_NOT_DISTURB` 591, `KEY_PRIVACY_SCREEN_TOGGLE` 633 |
| classici | `KEY_MENU` 139, `KEY_PROPS` 130, `KEY_WWW` 150, `KEY_SAVE` 234, `KEY_PRINT` 210, `KEY_ZOOMIN` 418 |

⛔ **Quindi: se l'utente preme il tasto «mute microfono» del suo portatile, la pagina non ha modo di
saperlo.** Non è recuperabile con nessuna API. È una riga da dichiarare spenta.

⚠ E una trappola di andata-e-ritorno: `keycode_converter.cc:97-105` `[R]` schiaccia
`KEY_PLAYCD` (200) su `KEY_PLAY` (207) — `code:"MediaPlay"` torna sempre 207, mai 200.

**Terza sorpresa, e la più costosa per noi: ⛔ non esiste «il browser», esistono tre tabelle
diverse su Linux.**

| | Chromium | Firefox (Gecko) | WebKitGTK |
|---|---|---|---|
| nomi `code` | **197** | **159** | **156** |
| codici evdev nominati | **181** | 156 | 156 |
| volume | `AudioVolumeUp/Down/Mute` | ⛔ `VolumeUp/Down/Mute` | — |
| tasto Windows/Super | `MetaLeft`/`MetaRight` | `MetaLeft`/`MetaRight` | ⛔ **`OSLeft`/`OSRight`** (legacy) |
| `KEY_PROPS` (130) | ⛔ **non nominato** | ✅ `"Props"` | ✅ `"Props"` |
| `Lang3`,`Lang4`,`Lang5`, `Power`, `Sleep`, `NumpadParenLeft/Right` | ✅ | ⛔ `"Unidentified"` | ⛔ |
| **tasto ignoto** | ⛔ **`""`** (stringa vuota) | ✅ `"Unidentified"` | ✅ `"Unidentified"` |

⛔ **L'ultima riga è una violazione di specifica da parte di Chromium**, che è normativa `[S]`:
*«Conforming implementations MUST only use `"Unidentified"` as a key code when there is no way for
the implementation to determine the key code»*.

⭐ **Le tre conseguenze dirette sul nostro dizionario `code` → evdev, lato server:**

1. **si copia la colonna `evdev` di `dom_code_data.inc`**, non si riscrive a mano;
2. ⛔ **deve accettare gli alias**: `VolumeUp` **e** `AudioVolumeUp`; `OSLeft` **e** `MetaLeft`;
   `LaunchMediaPlayer` **e** `MediaSelect`;
3. ⛔ **`""` e `"Unidentified"` sono lo stesso caso**, e vanno nel registro come «posizione non
   determinabile», mai indovinati.

**Le trappole, con la prova:**

| Trappola | Che cosa succede | Marca |
|---|---|---|
| ⭐ **tastiere non-QWERTY** | ✅ **`code` è la posizione fisica con nomi QWERTY**, ed è confermato tre volte. La specifica: *«The value is not affected by the current keyboard layout or modifier state»*; e nelle note: `"KeyQ"` — *«q on a US keyboard. **Labelled a on an AZERTY (e.g., French) keyboard**»*. ⭐ **E la specifica cita il nostro caso d'uso per nome**: *«trapping all keys (e.g., in a remote desktop client to send all keys to the remote host)»* | `[S]` |
| **Windows con disposizione non-QWERTY** | ✅ nessun problema: Chromium legge lo **scan code** da `lParam` (`events_win_utils.cc:369-371` `[R]`), e Microsoft lo definisce *«a value that identifies the key pressed **regardless of the active keyboard layout**»* | `[S]`+`[R]` |
| ⛔ **i coreani `Lang1`/`Lang2` su Windows** | **lo scan code è emesso solo sull'evento di rilascio** (nota 6 della tabella Microsoft). Chi aspetta un `keydown` non lo vedrà **mai**. E Chrome non li mappa affatto (`""`), mentre Firefox dà `"Lang1"`/`"Lang2"` | `[S]` |
| ⛔ **`Alt+Stamp` (SysRq) su Chrome/Windows** | `code` **vuoto**; su Firefox `"PrintScreen"` | `[S]` |
| **Stamp e Pausa su Linux** | ✅ mappati senza problemi: `"PrintScreen"` ← evdev 99 (`KEY_SYSRQ`), `"Pause"` ← evdev 119 | `[R]` |
| ⛔ **BlocMaiusc su macOS** | ⛔ **tre comportamenti incompatibili sullo stesso tasto**: Chrome/Safari fanno `keydown` all'accensione e `keyup` allo spegnimento; **Firefox fa solo `keydown`, mai `keyup`**. Motivo dichiarato da uno sviluppatore Mozilla: *«On Mac, the Cocoa event model doesn't notify physical keyup event for CapsLock key. Therefore, we don't dispatch it»* (bug 712535, **WONTFIX**). Chromium stesso ha il TODO: `// TODO(garykac): CapsLock requires special handling for each platform` (`dom_code_data.inc:209` `[R]`) | `[S]`+`[R]` |
| **`Fn` su macOS** | il nome c'è ma **nessun evento viene generato** | `[S]` |
| ⛔ **`repeat` sbagliato su X11** | *«Before Chrome 139, on Linux under X11, if multiple keys are held down, a `keydown` event for the most recently pressed key will trigger with `repeat` incorrectly set to `false`»*. ⚠ **Ci riguarda direttamente**: se filtriamo su `repeat` (§5.4), su X11 con Chrome < 139 iniettiamo pressioni fantasma | `[S]` BCD |
| **tasti multimediali** | arrivano **se l'OS non se li mangia prima**. `[?]` **Quale desktop Linux intercetti quali, non è documentato da nessuna parte**: è una riga del banco | `[?]` |
| ⛔ **`code` su Android** | BCD dice, per Chrome Android **e** Firefox Android, `partial_implementation` con la nota **«The value is always empty»**. ⚠ Ma il sorgente dice altro: `code` viene dallo **`scanCode`** di `android.view.KeyEvent`, e c'è la guardia `if (scancode)` — con `scanCode == 0` (tastiere software) il `code` resta vuoto (`web_input_event_builders_android.cc:137-146` `[R]`). ⭐ **Quindi da DeX con tastiera fisica dovrebbe arrivare la numerazione evdev identica a quella di libei, senza offset.** `[?]` **È la riga 4 del banco, ed è quella che decide se su DeX le posizioni funzionano** | `[R]`+`[S]` |

⚠ **E un bonus che tocca il mouse, non la tastiera**: Linux ha **otto** pulsanti
(`BTN_LEFT` 0x110 … `BTN_TASK` 279), UI Events ne definisce **cinque** (`button` 0-4). ⛔ **`BTN_TASK`
non ha equivalente JavaScript**, e la corrispondenza di `BTN_SIDE`/`BTN_EXTRA`/`BTN_FORWARD`/
`BTN_BACK` è **convenzionale, non normata** `[R]`+`[S]`. Va verificata a parte, in fase 4.

#### 3.A.4 Le lettere: come si ottiene davvero il carattere

*Domanda 4. È la metà «lettere» di `DECISIONI.md` §5-bis.6, ed è la parte dove i tre riferimenti
si dividono di più.*

**Il caso semplice**: per un tasto stampabile, `keydown.key` **è già il carattere** prodotto dal
sistema del client con la sua disposizione — `"a"`, `"A"`, `"à"`, `"€"`. È esattamente il modello
che ci serve: *«la disposizione del client la applica il sistema del client»* (§5-bis.6). Ed è
quello che noVNC usa: `core/input/util.js:68-108` `getKey()` prende `evt.key`, e
`core/input/keysymdef.js:672-687` lo converte in keysym con la scala Latin-1 → tabella →
`0x01000000|codepoint` `[R]`.

⛔ **Ma `keydown` da solo non basta, e Guacamole lo dimostra scrivendo una macchina a stati intera
per aggirarlo.** La citazione è la prova `[R]` (`Keyboard.js:183-191`):

```
        /**
         * Whether this event has been initially processed but deferred
         * (pending further events). An event may need to be deferred if its
         * details are ambiguous without context from events that have not yet
         * fired.
         */
```

Guacamole accoda ogni evento in un `eventLog` e lo interpreta al giro successivo del ciclo eventi
(`setTimeout(interpret_events, 0)`, `Keyboard.js:1132-1139`), con tre regole `[R]`
(`Keyboard.js:1236-1254`): *«If event itself is reliable, no need to wait» / «If keydown is
immediately followed by a keypress, use the indicated character» / «If keydown is immediately
followed by anything else, then no keypress can possibly occur to clarify this event»*. ⛔ **Il
carattere vero lo dice il `keypress` che *forse* seguirà.**

**I tre percorsi, e quando ciascuno vale:**

| Percorso | Quando è affidabile | Quando mente |
|---|---|---|
| `keydown.key` | tasto stampabile semplice, tastiera fisica | ⛔ **tasto morto** (`key === "Dead"`), **IME in corso** (`keyCode === 229`, `key === "Process"`/`"Unidentified"`) |
| `keypress` | il carattere effettivo, storico | è **deprecato** in UI Events, e non scatta sui tasti non stampabili |
| `beforeinput` / `input` | ⭐ **l'unico che vede il testo composto**: accenti, IME, correzione | richiede un elemento **modificabile con il fuoco**; e `insertCompositionText` **non è annullabile** `[S]` |

**I tasti morti.** `keydown.key` vale `"Dead"`, che non è un carattere. noVNC **non li gestisce
affatto**: `core/input/domkeytable.js:128` `[R]` ha la riga `// - Dead` — cioè *deliberatamente non
mappato* — e `getKeysym()` restituisce `null` perché `"Dead".length !== 1`
(`util.js:180-183` `[R]`). ⛔ **Su noVNC, in un browser, `^` + `e` non produce `ê` per la via delle
lettere.** Il carattere esce solo dal percorso `input`, che noVNC usa **solo** sulla textarea
mobile. Xpra ci prova con `getLayoutMap()` (`Client.js:1008-1012` `[R]`) ma la lettura è sbagliata
— usa `keyboardLayoutMap[key]` su un oggetto *maplike*, dove serve `.get(key)` — **quindi la mappa
resta vuota e il ramo non scatta quasi mai**.

⭐ **Per noi la conclusione è netta, ed è una decisione di disegno**: le lettere devono uscire da
**`beforeinput`** (o `compositionend`), non da `keydown`, se vogliamo accenti e tasti morti. E
questo obbliga la pagina ad avere **un elemento modificabile con il fuoco** anche sul desktop, non
solo su Android — che è esattamente quel che fa Guacamole con il suo `InputSink` `[R]`
(`InputSink.js:22-28`): *«A hidden input field which attempts to keep itself focused at all times
[…] may be used as a reliable source of keyboard-related events, particularly composition and input
events which may require a focused input field to be dispatched at all»*.

#### 3.A.5 ⭐ «Sta scrivendo» contro «sta premendo una scorciatoia»

*È la regola che decide come viaggia la battuta (`DECISIONI.md` §5-bis.6), e va scritta come
codice, non come intenzione.*

```
è un comando  ⇔  event.ctrlKey || event.altKey || event.metaKey
```

⚠ **Con quattro correzioni che vengono tutte dal codice letto, e nessuna è facoltativa:**

1. ⛔ **`event.altKey` è vero anche con AltGr su Windows**, perché Windows realizza AltGr come
   `Ctrl+Alt` sintetico. Preso alla lettera, **`AltGr+e` verrebbe mandato come posizione** invece
   di produrre `€`. Le due cure lette:
   - noVNC ritarda il `ControlLeft` di **100 ms** e lo fonde con l'`AltRight` se arriva entro
     **50 ms**, `core/input/keyboard.js:99-121` `[R]`, con un FIXME che dichiara il residuo:
     *«We fail to detect this if either Ctrl key is first manually pressed as Windows then no
     longer sends the fake Ctrl down event»*;
   - Guacamole va al contrario e **scioglie** Ctrl+Alt quando arriva un carattere stampabile che
     non sia `[A-Za-z]`, `Keyboard.js:1151-1181` `[R]`.

   ⭐ **La seconda è più semplice e non costa latenza. È quella da copiare.**
2. **`AltGraph` va escluso esplicitamente**: `getModifierState("AltGraph")` esiste, e il `key` vale
   `"AltGraph"`. `SPECIFICHE.md` §7.3 dice già che AltGr non conta;
3. ⛔ **su macOS il modificatore di comando è `metaKey`, non `ctrlKey`.** E noVNC rimescola i
   modificatori interi perché *«Alt behaves more like AltGraph on macOS»*
   (`core/input/keyboard.js:138-157` `[R]`, che dichiara di seguire RealVNC e TigerVNC);
4. **AltGr fisico su Linux manda `ControlLeft` senza il flag `ctrl`** — Guacamole lo scarta a mano
   `[R]` (`Keyboard.js:1231-1234`): *«On AltGr hold, ControlLeft is sent without Ctrl modifier and
   could be misinterpreted as Ctrl press»*.

⚠ **E una conseguenza che va scritta in `RCP.md`**: quando la battuta viaggia **come posizione**,
il server deve premere *anche i modificatori*, e la posizione dev'essere quella **fisica**. Se il
client ha una tastiera tedesca, `Ctrl+Z` sta dove da noi sta `Ctrl+Y`: è la seconda ragione di
`DECISIONI.md` §5-bis.7 (rinegoziare la disposizione), e questa lettura la conferma.

#### 3.A.6 Android e la tastiera a schermo

*Domanda 5. ⚠ Su DeX questo capitolo quasi non si usa (`DECISIONI.md` §5-bis.0): serve al telefono
in mano, che è il ripiego. **Ma il ripiego deve funzionare.***

**Il fatto di partenza** `[S]`: un IME in un browser **non produce tasti, produce testo**. Le
battute danno `keydown` con `keyCode: 229` e `code` vuoto — *«a keyCode value of 229 is returned
when keystrokes are typed but composition is not yet complete»*. Tutti e tre i riferimenti hanno
esattamente la stessa riga di difesa `[R]`:

- noVNC, `core/input/keyboard.js:65-67`: `// 229 is used for composition events` → il `code` resta
  `Unidentified`;
- Guacamole, `Keyboard.js:1415-1419`: *«Ignore (but do not prevent) the event if explicitly marked
  as composing, or when the "composition" keycode sent by some browsers when an IME is in use»* →
  `if (e.isComposing || keydownEvent.keyCode === 229) return;`;
- Xpra, `Client.js:981-984`: `//this usually fires when we have received the event via "oninput"
  already`.

**Come si fa comparire la tastiera senza un campo di testo visibile**: ⛔ **non si può.** L'unica
API dedicata, `navigator.virtualKeyboard.show()`, **richiede comunque** che l'elemento col fuoco sia
un controllo di modulo o un *editing host* `[S]`
([Chrome, VirtualKeyboard API](https://developer.chrome.com/docs/web-platform/virtual-keyboard)).
Quindi il **campo nascosto** non è un trucco: è l'unica strada. E i tre riferimenti lo confermano,
con tre varianti e tre difetti diversi:

| | Come | Il difetto, dal codice |
|---|---|---|
| **noVNC** | `<textarea>` fuori schermo pre-riempita con **99 underscore**, e si ricostruisce quel che l'utente ha scritto **per differenza fra il vecchio e il nuovo valore** (`app/ui.js:1673-1732` `[R]`) | ⛔ paga **un Backspace remoto per ogni correzione**. E `vnc.html:420-423` `[R]` ammette: *«Note that Google Chrome on Android doesn't respect any of these html attributes which attempt to disable text suggestions on the on-screen keyboard»*. Più il ricircolo: `blur()` + `setTimeout(focus)`, *«This sometimes causes the keyboard to disappear for a second but it is required for the android keyboard to recognize that text has been added»* |
| **Guacamole** | `InputSink`: `<textarea>` invisibile che **si riprende il fuoco a ogni keydown**, più un metodo «Text input» separato con una textarea **imbottita di 4+4 caratteri a larghezza zero** (`U+200B`) per poter dedurre Backspace e Canc dalla posizione del cursore (`guacTextInput.js:283-287` `[R]`) | il fuoco va difeso a mano; e mentre quel modo è attivo **la tastiera fisica viene filtrata** a una lista bianca di tasti (`guacTextInput.js:57-91` `[R]`) |
| **Xpra** | disegna **una tastiera propria** in pagina (`simple-keyboard`) e sintetizza eventi finti | ⛔ quegli eventi hanno `which: 0, keyCode: 0` e nessun `getModifierState`: **da quella tastiera i modificatori non passano mai**. E il percorso IME vero esiste (`index.html:1028`) ma la textarea è dichiarata **`readonly`** e non viene mai smarcata — cioè **è codice morto** |

⛔ **Le tre trappole da portarsi via**, tutte `[R]`:

1. **l'autocorrezione non è un carattere in più**: sostituisce parole intere. Su Android il
   `beforeinput` che ne esce è di tipo **`insertCompositionText`**, e per la specifica **non è
   annullabile** `[S]`. Chi conta i caratteri sbaglia; bisogna **diffare**;
2. **fuori dal BMP si rompe tutto per costruzione**: Xpra usa `String.fromCharCode` e
   `str.charCodeAt(0)` (`Keycodes.js:1630`, `index.html:1036` `[R]`) — **ogni emoji è rotta**.
   ⭐ Per noi non è un difetto ma una conferma: `SPECIFICHE.md` §7.3 dice già che quel che non è
   scrivibile **si dichiara**, e un'emoji non è scrivibile su nessuna disposizione;
3. **il campo nascosto ruba il fuoco**, e va difeso con codice sporco in tutti e tre.

#### 3.A.7 La ripetizione, e ⛔ il modificatore rimasto giù

*Domanda 6. Per noi il secondo punto è il più grave del rapporto, perché la sessione remota
sopravvive alla connessione.*

**Chi ripete**: ⛔ **il sistema, non il browser.** UI Events è normativo `[S]`:

> *«Holding down a key MUST result in the repeating the events `keydown`, `beforeinput`, `input` in
> this order, at a rate determined by the system configuration.»*

Quindi arriva **una raffica di `keydown` con `repeat: true` e un solo `keyup`**. I tre riferimenti
fanno tre cose diverse `[R]`: Xpra e noVNC inoltrano la raffica (noVNC tenendo fermo il keysym,
`keyboard.js:159-163`); **Guacamole scarta i `keydown` ripetuti e genera lui la ripetizione** a
500 ms + 50 ms, mai per modificatori e lock (`Keyboard.js:839-851`, `1769-1771`).
⭐ **Conseguenza per noi in §5.4.**

**Il modificatore rimasto giù.** La specifica **non garantisce** il `keyup` quando la pagina perde
il fuoco `[S]`: UI Events §3.5.6.2 dice solo *quando* il `keyup` arriva, non *che* arrivi. Le cause
lette nel codice sono cinque, e sono tutte reali:

| Causa | Chi l'ha documentata nel codice |
|---|---|
| la pagina perde il fuoco con un modificatore giù | tutti e tre |
| ⛔ **su macOS, con `Cmd` premuto, il `keyup` degli altri tasti non arriva mai** | Guacamole `Keyboard.js:244-251` `[R]`: *«the keyup will never be sent in Chrome (bug #108404)»*; noVNC `keyboard.js:165-173` `[R]` |
| su iOS **tutti** i `keyup` sono inaffidabili | Guacamole `Keyboard.js:1615` `[R]`: `// All keyup events are unreliable on iOS (sadly)` |
| su Windows, Maiusc destro e sinistro insieme: manca un `keyup` | noVNC `keyboard.js:232-245` `[R]` |
| BlocMaiusc/BlocNum su macOS: **cambio di stato, non pressione** | Guacamole `Keyboard.js:1565-1572` `[R]`; noVNC `keyboard.js:175-184` `[R]` |

**Le cure, in ordine di qualità** (e la migliore è di Guacamole):

1. `reset()` su `blur` — ce l'hanno tutti e tre, ma ⛔ **Xpra rilascia un solo tasto**:
   `index.html:1636-1648` `[R]` sotto il commento `// Prevent stuck keys.` manda il rilascio del
   **solo `last_key_packet`**. Con `Ctrl+Alt` tenuti e la finestra che perde il fuoco, **i
   modificatori restano incollati lato server**;
2. **premi-e-rilascia atomico** quando si sa che il `keyup` non arriverà (Cmd su macOS, iOS,
   BlocMaiusc);
3. ⭐ **risincronizzare i modificatori dai flag degli eventi del mouse** — è la sola cura che
   ripara uno stato già andato alla deriva, e la sola che funziona quando il modificatore era già
   premuto *prima* che la pagina prendesse il fuoco. Guacamole `Keyboard.js:944-953` `[R]`;
4. ⭐ **il tri-stato**: `null` = «non lo so», distinto da `false` = «non è premuto». Guacamole
   `Keyboard.js:1918-1920` `[R]`; noVNC lo usa per NumLock su macOS, dove `getModifierState`
   *«is not supported on mac and ios and always returns false»* (`keyboard.js:90-97` `[R]`).

⚠ **Un fatto che ci riguarda direttamente**: noVNC **risincronizza BlocMaiusc con lo stato del
LED riportato dal server** (`core/rfb.js:1028-1058`, `2891-2904` `[R]`). ⭐ **La stessa cosa la
possiamo fare noi, e meglio**: il server è nostro, sa lo stato vero della sessione, e può
**rimandarlo indietro**. Un `Ctrl` rimasto giù lo sappiamo *da questa parte*, non lo dobbiamo
indovinare da quella.

---

### 3.B Gli appunti

#### 3.B.1 Che cosa dice la specifica, e che cosa fanno davvero i tre motori

La Clipboard API `[S]` ([w3c.github.io/clipboard-apis](https://w3c.github.io/clipboard-apis/)) è
la sola specifica in gioco. Il testo normativo chiede, **per leggere**, il risultato positivo di
*check clipboard read permission*: il documento deve avere **sticky activation** *oppure* il
permesso `clipboard-read`; in mancanza, `read()`/`readText()` **rigettano con
`NotAllowedError`** `[S]`. Per **scrivere**, il positivo di *check clipboard write permission*
`[S]`.

⛔ **Ma i tre motori hanno divergito dalla specifica, e la divergenza è il fatto che ci
riguarda.** MDN la riassume, ed è la fonte più precisa che esista sulla differenza `[S]`
([Clipboard API › Security considerations](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API#security_considerations)):

> *Chromium browsers:* «If a read isn't allowed by the spec **and the document has focus**, it
> triggers a request to use permission `clipboard-read`, and succeeds if the permission is granted
> […]. Writing requires either the `clipboard-write` permission **or transient activation**. If the
> permission is granted, **it persists**, and further transient activation is not required.»
>
> *Firefox & Safari:* «If a read isn't allowed by the spec but transient user activation is still
> met, it triggers a user prompt in the form of an **ephemeral context menu with a single "Paste"
> option (which becomes enabled after 1 second)** and succeeds if the user chooses the option. […]
> **The `clipboard-read` and `clipboard-write` permissions are not supported (and not planned to be
> supported) by Firefox or Safari.**»

Le versioni, da `browser-compat-data` `[S]`
([mdn/browser-compat-data › api/Clipboard.json](https://github.com/mdn/browser-compat-data/blob/main/api/Clipboard.json)):

| | `readText()` | `read()` | `writeText()` | `write()` |
|---|---|---|---|---|
| Chrome / Edge | 66 | 76 | 66 | 76 |
| Firefox | **125** | **127** | 63 | 127 |
| Safari | 13.1 | 13.1 | 13.1 | 13.1 |

Note BCD verbatim `[S]`: per Chrome «*The user must grant the `clipboard-read` permission*» e «*From
version 107, this method must be called within user gesture event handlers, or the user must grant
the `clipboard-write` permission*»; per Firefox «*This method must be called within user gesture
event handlers*» e «*A paste prompt is displayed when the clipboard is read. **If the clipboard
contains same-origin content, the prompt is suppressed***».

Il caso WebKit, che è il più restrittivo e il meglio documentato dagli autori stessi `[S]`
([webkit.org/blog/10855](https://webkit.org/blog/10855/async-clipboard-api/)): la finestra di
conferma **non** appare in due casi soli — se l'utente sta *esplicitamente* incollando durante il
gesto (⌘V su macOS, «Incolla» sulla barra di richiamo su iOS), oppure se il contenuto degli
appunti è stato scritto da una pagina **della stessa origine**. Fuori di lì compare un elemento
d'interfaccia nativo (voce di menu contestuale su macOS, barra di richiamo su iOS) e *«qualsiasi
azione diversa — cliccare altrove, cambiare scheda, chiudere Safari — rigetta la promessa»*.

⚠ **Il requisito del fuoco è di Chromium, non della specifica.** In Chromium la lettura fallisce
se il documento non ha il fuoco `[S]` (MDN, riquadro sopra: *«and the document has focus»*). È il
motivo per cui **tutti e tre i riferimenti leggono gli appunti proprio sull'evento `focus`** — non
è un'astuzia, è l'unico istante in cui la lettura è lecita e i dati sono freschi.

#### 3.B.2 A schermo intero e senza fuoco

| Situazione | Che cosa succede | Marca |
|---|---|---|
| pagina a schermo intero, Chrome, permesso `clipboard-read` **già concesso** | la lettura riesce senza interfaccia: il permesso persiste | `[S]` MDN |
| pagina a schermo intero, Chrome, permesso **da chiedere** | compare la richiesta di permesso. ⚠ In Chromium la richiesta **non esce da schermo intero**, e ci sono segnalazioni di richieste **non cliccabili** sopra una pagina a schermo intero con puntatore bloccato | `[?]` — vedi il caso opposto sotto |
| pagina a schermo intero, **Firefox** | ⛔ Firefox **esce da schermo intero** quando mostra una richiesta di permesso, dal Firefox 70, e vieta di rientrarci finché la richiesta è aperta — *«Force-exit fullscreen and disallow re-entering while a permission prompt is shown»* | `[S]` [bug 1522120](https://bugzilla.mozilla.org/show_bug.cgi?id=1522120) |
| pagina a schermo intero, Firefox, **il menu «Incolla»** | `[?]` **non è una richiesta di permesso ma un menu contestuale effimero**: non è detto che faccia scattare l'uscita da schermo intero. **Va misurato**, ed è il punto più delicato del §4 | `[?]` |
| pagina **senza fuoco** | Chromium: la lettura rigetta. Firefox/Safari: senza *transient activation* non c'è nemmeno il menu, quindi rigetta | `[S]` |

⛔ **Il caso opposto, scritto prima** (`LEZIONI.md` §1.11). L'affermazione «su Firefox il menu
«Incolla» non fa cadere lo schermo intero» sarebbe **falsa** se, premendo `Ctrl+V` dentro la
pagina a schermo intero con `keyboardLock`, si vedesse la pagina tornare a finestra prima che il
menu compaia. Se invece il menu compare **sopra** la pagina ancora a schermo intero e, scelto
«Incolla», lo schermo intero è ancora attivo e la `keyboardLock` ancora in piedi, l'affermazione è
vera. **Sono due schermate diverse: la prova distingue.**

#### 3.B.3 ⭐ Sorvegliare gli appunti del dispositivo — la risposta è cambiata nel 2026

`SPECIFICHE.md` §9 sospettava di no, «in nessun browser». **Il sospetto era giusto fino al gennaio
2026 e da allora non lo è più su Chromium.**

L'evento **`clipboardchange`** è entrato nella specifica W3C `[S]`
([w3c.github.io/clipboard-apis](https://w3c.github.io/clipboard-apis/), §5.2.1: *«The
clipboardchange event fires whenever the contents of the system clipboard are changed»*, PR
[w3c/clipboard-apis#239](https://github.com/w3c/clipboard-apis/pull/239)) ed è **spedito in Chrome
144 il 13 gennaio 2026** `[S]`
([note di rilascio Chrome 144](https://developer.chrome.com/release-notes/144)), con la
motivazione dichiarata nell'*intent to ship* `[S]`
([blink-dev](https://groups.google.com/a/chromium.org/g/blink-dev/c/UgYnldQ0-VY)):

> «a web-app can monitor the system clipboard by polling and reading the clipboard through async
> clipboard API at regular intervals. **Remote desktop applications like Chrome Remote Desktop**
> exemplify this problem, checking for changes on every page focus event unnecessarily.»

⭐ **È scritto per noi.** È esattamente il verso «dispositivo → sessione remota» di `DECISIONI.md`
§5-ter.1, quello che si usa di più.

**Che cosa consegna e a che prezzo** `[S]`:

| | |
|---|---|
| che cosa porta l'evento | ⛔ **solo i tipi MIME** (`event.types`), **non il contenuto**. Per avere il testo serve comunque una `readText()`, con le sue regole |
| requisiti | **sticky activation** *oppure* permesso `clipboard-read` concesso — è nella spec: *«The `clipboardchange` event is only fired with sticky activation or after the `clipboard-read` permission is granted»* `[S]` (MDN, §Security considerations) |
| fuoco | l'evento scatta solo se il documento ha il **fuoco di sistema**; se il cambio avviene mentre la pagina non ce l'ha, si accende un *pending flag* e **un solo evento** viene emesso al ritorno del fuoco. ⛔ **Nessuno storico**: dieci copie fuori fuoco diventano un evento solo `[S]` |
| altri motori | ⛔ **Firefox, Firefox Android, Safari e Safari iOS non lo hanno.** Posizione dichiarata sia da Mozilla sia da WebKit al momento dell'*intent*: **«No signal»** `[S]` |

⛔ **Conclusione, e va scritta come sta**: **sorvegliare gli appunti del dispositivo si può, su
Chromium, dal gennaio 2026, e solo mentre la pagina ha il fuoco.** Su Firefox e Safari **no**, e
non è «non l'ho trovato»: è **verificato che non c'è**, perché la voce esiste nella specifica, ha
una tabella di compatibilità, e quella tabella dice `false` per Gecko e WebKit.

⚠ **E resta un limite che nessuna API toglie**: mentre la pagina non ha il fuoco — cioè mentre
l'utente sta copiando un indirizzo in *un'altra applicazione* del telefono — **non arriva niente**.
Il guadagno vero di `clipboardchange` non è «sorvegliare in background»: è **non dover interrogare
gli appunti a ogni ritorno di fuoco**, che è ciò che oggi fanno tutti e tre i riferimenti.

#### 3.B.4 ⭐ Come lo risolvono i tre riferimenti — letto nel codice

*Tre cloni, tre commit, tre strategie diverse per lo stesso problema. Questa è la parte del
rapporto che vale più di tutto il resto, ed è tutta `[R]`.*

| | noVNC | Guacamole | Xpra html5 |
|---|---|---|---|
| commit letto | `7c36fabe`, 6 giu 2026, `package.json` v**1.7.0** | `7fcdce8c`, 6 ago 2026, v**1.6.1**-SNAPSHOT | `3ecf4f2a`, 6 ago 2026, v**22** in sviluppo (ultima release 21.0, 11 mag 2026) |
| dispositivo → remoto, innesco | **`focus` sul canvas** → `navigator.clipboard.readText()` | **`load`, `copy`, `cut`, `focus` della finestra** → `readText()`, ripiego `execCommand('paste')` | **`paste`, clic, `contextmenu`, `focus`, bottone** → `readText()` |
| polling a intervallo | ⛔ **no** (`grep readText` → 2 occorrenze, nessun `setInterval`) | ⛔ **no** (un solo ritardo di 100 ms *una tantum*) | ⛔ **no** (`grep setInterval` → solo ping e info) |
| ascolto dell'evento `paste` | ⛔ **no** — verificato con grep vuoto | ⛔ **no** — le uniche occorrenze di `'paste'` sono la textarea nascosta e `execCommand('paste')` | ✅ **sì**, `Client.js:1955` — ma dentro `paste` preferisce comunque `readText()` a `clipboardData.getData()` |
| interroga i permessi | ✅ `navigator.permissions.query({name:'clipboard-read'})` — di fatto un test *«sei Chromium?»* | ⛔ **no** — `grep navigator.permissions` vuoto | ⛔ **no** — `grep` trova solo le notifiche |
| ripiego se il browser nega | **pannello «Clipboard»** con `<textarea>` ed evento `change` | **degrado silenzioso** su un clipboard interno di scheda + **pannello manuale** nel menu | **`execCommand('copy')`** su una `<textarea>` fuori schermo, al prossimo clic |
| lo dice all'utente? | ⚠ no: con permesso `denied` **nasconde il pannello** e l'utente resta senza appunti | ⛔ no: log e via | ⛔ no: log di debug e via |

**Le tre citazioni che contano, verbatim.**

Xpra, `html5/js/Client.js:4247-4253` `[R]` — l'ammissione più onesta dei tre:

```
    // if we have navigator.clipboard support in the browser,
    // we can just set the clipboard value here,
    // otherwise we don't actually set anything
    // because we can't (the browser security won't let us)
    // we just record the value and actually set the clipboard
    // when we get a click, control-C or control-X event
    // (when access to the clipboard is allowed)
```

Xpra, `html5/index.html:678-686` `[R]` — ⛔ **la lettura degli appunti è spenta per difetto su
Firefox e su Safari-in-HTTPS**, per non far comparire le finestrelle:

```
        // Some browsers trigger ugly popups if we try to read the clipboard
        // Safari: https://github.com/Xpra-org/xpra-html5/issues/226
        // Firefox: https://github.com/Xpra-org/xpra-html5/issues/301
        const clipboard = getboolparam("clipboard", true);
        let cpoll = !Utilities.isFirefox();
        if (Utilities.isSafari()) {
          cpoll = !ssl;
        }
```

Guacamole, `indexController.js:299-309` `[R]` — i quattro inneschi, e nient'altro:

```
    // Attempt to read the clipboard if it may have changed
    $window.addEventListener('load',  clipboardService.resyncClipboard, true);
    $window.addEventListener('copy',  clipboardService.resyncClipboard);
    $window.addEventListener('cut',   clipboardService.resyncClipboard);
    $window.addEventListener('focus', function focusGained(e) {
        // Only recheck clipboard if it's the window itself that gained focus
        if (e.target === $window)
            clipboardService.resyncClipboard();
    }, true);
```

⭐ **La scoperta che cambia il disegno.** In tutti e tre i prodotti **`Ctrl+V` dentro la pagina
non incolla**: viene inviato al server come normale battuta, e quel che il desktop remoto incolla
è ciò che il client gli aveva **già** trasferito. Da qui la corsa che tutti e tre devono
disinnescare a mano:

- Guacamole, `guacClient.js:255-258` `[R]`: *«Wait for any in-progress clipboard synchronization to
  complete. This avoids the pasting of outdated clipboard content when guacamole window regains
  focus»*, con attesa a passi di 10 ms e il commento *«Synchronization can take 8-10ms»*
  (`guacClient.js:287-288`);
- Xpra, `Client.js:18` `const CLIPBOARD_EVENT_DELAY = 100;` e `Client.js:1139-1141` `[R]`: *«if
  there is a chance that we're in the process of handling a clipboard event (a click or control-v)
  then we send with a slight delay»* — ⛔ **cento millisecondi di ritardo su ogni battuta** quando
  gli appunti sono in ballo;
- Xpra, `Client.js:2134-2135` `[R]`: *«warning: this can take a while, so we may send the click
  before the clipboard contents...»*.

⛔ **È il difetto di forma da non ereditare**: se il testo viaggia *dopo* il `Ctrl+V`, il desktop
remoto incolla la roba di prima. Chi lo cura col ritardo paga latenza su ogni tasto.

**Il compromesso che tutti e tre hanno accettato**: una **finestra «appunti» separata**, dove
l'utente incolla a mano. Guacamole la mette nel menu con questo testo `[R]`
(`translations/en.json:128`): *«Text copied/cut within Guacamole will appear here. Changes to the
text below will affect the remote clipboard»*, e la textarea è pure **oscurata** finché non ci si
clicca sopra (`ACTION_SHOW_CLIPBOARD`: *«Click to view clipboard contents.»*). noVNC ha lo stesso
pannello con *«Edit clipboard content in the textbox below»* (`vnc.html:180-188`). Xpra ha un
bottone nella barra (`index.html:1554`) più una pagina diagnostica dedicata,
`html5/clipboard.html`.

#### 3.B.5 Che cosa costa all'utente, in gesti

Con `clipboardchange` (Chromium ≥ 144) e permesso concesso:

| Verso | Gesti | Marca |
|---|---|---|
| **dispositivo → remoto** (il verso che si usa di più) | copio nel telefono; **torno nella pagina** (un tocco); il testo è già di là. **Un gesto**, che l'utente farebbe comunque | `[?]` — dipende dal permesso concesso una volta sola |
| **remoto → dispositivo** | copio nel desktop remoto; il server manda; `writeText()` scrive — ⚠ ma in Chromium serve `clipboard-write` o *transient activation*: senza permesso, il testo resta in sospeso finché l'utente non tocca la pagina | `[S]` |

Senza permesso, su Firefox e Safari:

| Verso | Gesti | Marca |
|---|---|---|
| **dispositivo → remoto** | copio; torno nella pagina; `Ctrl+V` (o tocco un bottone); **compare il menu «Incolla»**; aspetto **1 secondo** che si abiliti; lo scelgo. ⛔ **Tre gesti e un secondo di attesa, ogni volta** | `[S]` |
| **remoto → dispositivo** | serve *transient activation*: un tocco qualunque sulla pagina | `[S]` |

#### 3.B.6 Il caso Safari e iOS

| | |
|---|---|
| `read`/`write` | Safari 13.1+, ma **mai senza interfaccia**, salvo i due casi del §3.B.1 `[S]` |
| permessi `clipboard-read`/`clipboard-write` | ⛔ **non esistono e non sono previsti** `[S]` (MDN) |
| `clipboardchange` | ⛔ **non c'è** `[S]` |
| l'interfaccia su iOS | barra di richiamo con la sola voce «Incolla» `[S]` |
| lo schermo intero su iPhone | ⚠ **supporto parziale** della Fullscreen API su Safari iOS in tutte le versioni da 12 a 26.5 `[S]` ([caniuse › fullscreen](https://caniuse.com/fullscreen)) — storicamente il solo `<video>`. ⛔ Senza schermo intero **non c'è keyboard lock**, quindi su iPhone si perde tutto il §3.A insieme |
| l'ammissione di noVNC | `app/ui.js:153-156` `[R]`: il bottone «schermo intero» **non viene nemmeno mostrato** su Safari — *«Safari doesn't support alphanumerical input while in fullscreen»* |

⛔ Quest'ultima riga è la più pesante del rapporto per Safari, e viene dal codice di un prodotto
che quel caso l'ha pagato: **il commento di noVNC dice che su Safari, a schermo intero, non si
scrive.** ⚠ È datato e potrebbe essere superato da Safari 26.4, che la keyboard lock a schermo
intero l'ha appena aggiunta. **Va misurato**, ed è nel §4.

---

## 4. ⛔ Il banco: come si misura S3

*Il banco si scrive **prima** del prodotto (`PIANO.md` §0.4) e si certifica **prima** della misura
(`LEZIONI.md` §1.2). Quello che segue è una pagina sola, servita in HTTPS, che non ha bisogno di
niente del resto di REMOTIX.*

### 4.1 Che cos'è lo strumento

Una pagina sola — `banchi/banco-s3.html`, servita in HTTPS dalla macchina di prova — con quattro
riquadri e **un registro che si può copiare via**:

1. **il registro delle battute** — per ogni evento: `type`, `code`, `key`, `keyCode`, `location`,
   `repeat`, `isComposing`, `getModifierState()` dei sei modificatori, e `event.defaultPrevented`
   dopo il nostro `preventDefault()`. Con marca temporale al microsecondo (`event.timeStamp`);
2. **il registro dei tasti giù** — l'insieme dei `code` che il banco crede premuti, **sempre
   visibile**, perché è quello che smaschera il modificatore rimasto giù;
3. **i comandi dello schermo intero**: entra senza lock, entra con `navigator.keyboard.lock()`,
   entra con `requestFullscreen({keyboardLock:"browser"})`, e la stessa cosa con l'elenco esplicito
   di `code`;
4. **il riquadro appunti**: leggi, scrivi, e un contatore di `clipboardchange`.

⛔ **Il registro non conta, ascolta** (`LEZIONI.md` §2.3). Non si scrive «sono arrivate 12
scorciatoie su 20»: si scrive, per ogni combinazione provata, **che cosa è arrivato e che cosa ha
fatto il browser**. Un banco che conta non distingue «non è arrivata» da «è arrivata ma il browser
l'ha eseguita lo stesso».

### 4.2 ⛔ Il controllo positivo — prima di ogni sessione di misura

*Costa dieci secondi e impedisce la riga sbagliata (`LEZIONI.md` §1.9 regola 2).*

| Controllo | Che cosa dimostra | Se fallisce |
|---|---|---|
| **premo `KeyA`** e il registro scrive `code:"KeyA" key:"a"` | ⛔ **il banco riceve le battute.** Senza questo, ogni «non è arrivata» è ambiguo fra «il browser se l'è tenuta» e «il banco era sordo» | il banco è rotto, non il browser: fuoco perso, `preventDefault` sbagliato, listener sull'elemento sbagliato |
| **premo `Ctrl+Maiusc+KeyA`** (combinazione che nessun browser rivendica) e il registro la scrive intera, con i due modificatori | il banco sa vedere **una combinazione con modificatori**, non solo un tasto nudo | idem |
| **scrivo `ciao` nel riquadro appunti, premo «scrivi»**, e lo ritrovo incollando in un editor locale | il canale appunti **in uscita** funziona su questo motore | tutto il §3.B è da rifare qui |
| **entro a schermo intero e il registro scrive `fullscreenchange`** | la pagina è davvero a schermo intero **avviato da JavaScript** — ⛔ non da `F11`, che per la specifica **non attiva** la keyboard lock | le prove di lock che seguono non valgono niente |

⛔ **E il controllo positivo del terzo riquadro va rifatto a ogni motore**, non una volta sola: è
il motore che cambia, ed è lui l'incognita.

### 4.3 I tasti, in quest'ordine

**Gruppo A — le battute normali** (servono a provare la regola di `DECISIONI.md` §5-bis.6):

1. `a`, `A` (con Maiusc), `à` — che `key` esce, e con quale `code`;
2. **il tasto morto**: `^` poi `e` → deve uscire `ê`. Si guarda che cosa dà `keydown.key` (atteso
   `"Dead"`), e da dove esce davvero il carattere (`compositionend`? `beforeinput`?);
3. **AltGr**: `AltGr+e` su disposizione italiana → `€`. Su Windows si guarda se arriva
   `Ctrl`+`Alt` invece di `AltGraph`;
4. `Maiusc+2` → `"` su italiana. Si verifica che `code` resti `Digit2`.

**Gruppo B — le scorciatoie, dalla meno rischiosa alla più rischiosa.** ⛔ **In quest'ordine, e
una per volta**, perché quelle in fondo chiudono la scheda e portano via il registro:

1. `Ctrl+C`, `Ctrl+V`, `Ctrl+X`, `Ctrl+Z`, `Ctrl+A` — le annullabili, che devono arrivare **come
   posizione** (`code`) e non come lettera;
2. `Ctrl+P`, `Ctrl+S`, `Ctrl+F`, `Ctrl+G`, `Ctrl+O`, `Ctrl+U`, `Ctrl+D`, `Ctrl+H`, `Ctrl+J`,
   `Ctrl+L`, `Ctrl+K`, `Ctrl+E`, `Ctrl+R`, `Ctrl++`, `Ctrl+-`, `Ctrl+0`;
3. `F1`…`F12`, e in particolare **`F11`**, **`F12`**, **`F3`**, **`F5`**, **`F6`**;
4. `Ctrl+Maiusc+I`, `Ctrl+Maiusc+J`, `Ctrl+Maiusc+C`, `Ctrl+Maiusc+K`, `Ctrl+Maiusc+E`,
   `Ctrl+Maiusc+M`, `Ctrl+Maiusc+P`, `Ctrl+Maiusc+N`, `Ctrl+Maiusc+T`, `Ctrl+Maiusc+W`,
   `Ctrl+Maiusc+Q`;
5. `Alt+Freccia sinistra`, `Alt+Freccia destra`, `Alt+Home`, `Alt+D`, `Alt+E`, `Alt+F`;
6. **`Escape`** — da solo, e **tenuto premuto** (si cronometra: 1,5 s su Safari, 2 s su Chrome);
7. `Ctrl+Tab`, `Ctrl+Maiusc+Tab`, `Ctrl+1`…`Ctrl+9`;
8. ⛔ **le tre che chiudono**: `Ctrl+T`, `Ctrl+N`, **`Ctrl+W`** — **ultime**, e con il registro già
   copiato fuori;
9. **quelle del sistema**: `Super`, `Super+D`, `Alt+Tab`, `Alt+F4`, `Stamp`, `Pausa`,
   `Ctrl+Alt+Canc` — che non è recuperabile in nessun caso e serve solo a scriverlo nero su bianco;
10. su macOS, tutto il gruppo con `Cmd` al posto di `Ctrl`, più `Cmd+Tab`, `Cmd+Q`, `Cmd+H`,
    `Cmd+Spazio`, `Cmd+Ctrl+F`;
11. su iPadOS, `Cmd+H`, `Cmd+Spazio`, `Cmd+Tab`, e **`Cmd` tenuto premuto**, che apre il foglio
    delle scorciatoie di sistema.

**Ogni combinazione va provata in tre stati**, ed è la sola forma che dà una risposta utile:

| Stato | Che cosa si scrive nella tabella |
|---|---|
| **a finestra**, senza schermo intero | arriva? il `preventDefault()` ferma l'azione del browser? |
| **a schermo intero**, senza lock | cambia qualcosa? (⚠ Chromium consegna in schermo intero alcune scorciatoie che a finestra si tiene) |
| **a schermo intero, con la lock** del motore | arriva? |

**Gruppo C — la ripetizione e il modificatore rimasto giù** (per noi è il gruppo più grave, perché
la sessione remota sopravvive alla connessione):

1. tengo premuto `KeyA` tre secondi: quanti `keydown` con `repeat:true`, a che ritmo, e **un solo
   `keyup`**;
2. tengo premuto `Ctrl` e **cambio scheda** con il mouse: arriva il `keyup` di `Ctrl`? Arriva il
   `blur`?
3. tengo premuto `Ctrl` e premo `Alt+Tab` (cambio finestra di sistema): stessa domanda;
4. tengo premuto `Ctrl` ed **esco da schermo intero** con `Escape`: stessa domanda;
5. tengo premuto `Ctrl` e la macchina **va in sospensione**;
6. ⛔ **su macOS**: tengo `Cmd` e premo `KeyA` — arriva il `keyup` di `KeyA`? (Guacamole e noVNC
   dicono di no, e lo aggirano premendo-e-rilasciando subito: `Keyboard.js:244-251` `[R]`,
   `keyboard.js:165-173` `[R]`);
7. **Maiusc destro e sinistro insieme**, rilasciandone uno solo — su Windows manca un `keyup`
   (noVNC `keyboard.js:232-245` `[R]`);
8. `BlocMaiusc` e `BlocNum`: quanti eventi per una pressione, su ciascun sistema.

**Gruppo D — Android e la tastiera a schermo:**

1. su **DeX con tastiera fisica**: tutto il gruppo B, più `Super`, `Alt+Tab`, **`F1`** (che apre il
   pannello scorciatoie di DeX `[S]`), e la verifica che `code` arrivi valorizzato;
2. con la **tastiera a schermo**: scrivo `ciao` — quanti `keydown` con `keyCode:229`, quanti
   `beforeinput` e di che `inputType`, quanti `compositionstart`/`compositionend`;
3. **l'autocorrezione**: scrivo `perchd` e lascio che il correttore lo cambi in `perché` — si conta
   quanti `deleteContentBackward` e quanti `insertText`/`insertCompositionText` escono, e si
   verifica se il `beforeinput` è **annullabile** (per `insertCompositionText` la specifica dice
   **no** `[S]`);
4. il predittivo che sostituisce **una parola intera** già scritta.

**Gruppo E — gli appunti**, nell'ordine:

1. copio del testo in **un'altra applicazione**, torno alla pagina: scatta `clipboardchange`? Con
   quale ritardo dal ritorno del fuoco?
2. copio **due volte** mentre la pagina non ha il fuoco, poi torno: ⛔ quanti eventi arrivano?
   (atteso: **uno solo** `[S]`);
3. `readText()` **con la pagina a schermo intero e la keyboard lock attiva**: riesce? Compare
   un'interfaccia? ⛔ **Lo schermo intero sopravvive alla comparsa dell'interfaccia?** — è la
   domanda del §3.B.2, e su Firefox è quella che decide;
4. `readText()` **senza fuoco** (con la finestra dietro un'altra);
5. `writeText()` senza gesto recente;
6. testo con **accenti, emoji e newline**, per verificare che non si perda niente nel passaggio.

### 4.4 Su quali motori, e su che cosa

⛔ **Non «due motori»: sei combinazioni motore-sistema**, perché quel che si perde dipende da
entrambi.

| # | Motore | Sistema | Perché è in elenco |
|---|---|---|---|
| 1 | **Chrome** stabile (≈ 151/152 ad agosto 2026) | **Linux/Wayland** | è il caso di casa, ed è l'unico dove il **compositore locale** può mangiare i tasti prima del browser |
| 2 | **Firefox** stabile (≥ **151**) | **Linux/Wayland** | ⛔ il motore con la keyboard lock **nuova**: quel che si perde qui non è quel che si perde su Chrome |
| 3 | **Chrome** | **Windows** | il posto da cui l'utente si collega, e dove vive il falso AltGr `Ctrl+Alt` |
| 4 | ⭐ **Chrome su Samsung DeX** | **Android** | ⛔ **l'uso primario dichiarato** (`DECISIONI.md` §5-bis.0). Sul telefono vero, mai sull'emulatore (§5-bis.0-ter) |
| 5 | **Safari ≥ 26.4** | **macOS** | il motore più restrittivo, e quello che ha appena aggiunto la lock |
| 6 | **Safari** | **iPadOS**, con tastiera fisica | il caso peggiore: `Cmd` è del sistema e lo schermo intero è parziale |

⚠ **Chrome per Android e Firefox per Android hanno un motore uguale al desktop ma un sistema che
non è quello**: la riga 4 non si deduce dalla riga 1. È la forma d'errore **E10** (`DECISIONI.md`
§5-bis.0-ter).

### 4.5 ⛔ Il caso opposto, scritto prima

*Per ogni prova indiretta di questo banco, che aspetto avrebbe il contrario (`LEZIONI.md` §1.11).*

| L'affermazione | Se è **vera** si vede così | Se è **falsa** si vede così |
|---|---|---|
| «con la lock, `Ctrl+W` arriva alla pagina» | il registro scrive `keydown code:"KeyW" ctrlKey:true`, **e la scheda è ancora aperta** | o non c'è nessuna riga, **o** c'è la riga e la scheda si chiude lo stesso (⛔ **due difetti diversi**: consegnato-ma-non-annullabile contro non-consegnato) |
| «il modificatore non resta giù quando si perde il fuoco» | al ritorno il registro dei tasti giù è **vuoto**, e c'è un `keyup` di `Ctrl` (o un `blur` che lo ha ripulito) | il registro dei tasti giù mostra ancora `ControlLeft` **e non c'è nessun `keyup`** |
| «su Firefox il menu «Incolla» non fa cadere lo schermo intero» | dopo aver scelto «Incolla», `document.fullscreenElement` è ancora l'elemento nostro | c'è un `fullscreenchange` **prima** che il menu compaia, e la pagina torna a finestra |
| «la tastiera a schermo di Android non manda posizioni» | ogni battuta è un `keydown` con `code:""` e `keyCode:229`, e il testo esce da `beforeinput` | arrivano `code` valorizzati — allora la strada delle posizioni è aperta anche là, e §5-bis.6 va rivista |
| «il compositore Wayland locale si tiene `Super`» | il registro non ha nessuna riga per `Super`, **e** il menu del desktop locale si apre | il registro scrive `MetaLeft`, e il menu locale **non** si apre |

⛔ **E la trappola di banco che abbiamo già pagato tre volte** (`LEZIONI.md` §2.3-bis): quando un
controllo è rosso e la cosa che misura *sembra* funzionare, **il primo sospetto è il controllo**.
Qui il candidato è il fuoco: una pagina che ha perso il fuoco non riceve niente e **sembra** un
browser che si tiene tutto.

### 4.6 Il banco va eseguito due volte di fila

`LEZIONI.md` §2.3-ter. ⛔ **In particolare il permesso `clipboard-read`**: la prima esecuzione
mostra la richiesta, la seconda no — e i due esiti sono **diversi**. Il banco deve dire quale dei
due sta misurando, e deve saper ripartire da permesso revocato.

---

## 5. Che cosa decide, per il prodotto

### 5.1 ⭐ La riga di `SPECIFICHE.md` §7.3-bis va riscritta

Oggi dice:

> | **la leva che esiste** | la **Keyboard Lock** […] `[S]` **solo su Chrome ed Edge, e solo a schermo intero** |

⛔ **Non è più vero dal 2026.** La leva esiste su **tutti e tre i motori**, ma **con due API
diverse**, e la pagina deve saperle **entrambe**:

```
// 1) lo standard WHATWG — Firefox 151+, Safari 26.4+
await elem.requestFullscreen({ keyboardLock: "browser" });

// 2) il predecessore Chromium — Chrome/Edge 68+
await elem.requestFullscreen();
if (navigator.keyboard?.lock) await navigator.keyboard.lock();
```

⚠ **E il rilevamento va fatto sulla *funzione*, non sul nome del browser.** `requestFullscreen`
ignora in silenzio le opzioni che non conosce: chiamarlo con `{keyboardLock}` su Chrome **non
fallisce**, semplicemente non blocca niente. ⛔ **Il banco deve provare l'effetto, non
l'esistenza** — è la stessa lezione di `KWIN_COMPOSE=O2`, l'interruttore inerte (`LEZIONI.md`
§1.11).

### 5.2 Quali browser conviene consigliare

| Posto | Consigliato | Perché |
|---|---|---|
| **Linux, Windows, macOS** | ⭐ **Chrome o Edge** | sono i soli con **`clipboardchange`** e con il permesso `clipboard-read` **che persiste**: è il solo modo di rendere invisibile il verso «dispositivo → sessione», che `DECISIONI.md` §5-ter.1 dichiara il più usato. La keyboard lock ce l'hanno da otto anni |
| **Linux, Windows, macOS** — alternativa vera | **Firefox ≥ 151** / **Safari ≥ 26.4** | ⭐ **da quest'anno sono un'alternativa, non un ripiego**, per la tastiera. ⛔ Restano indietro **solo** sugli appunti, e in un punto solo: il menu «Incolla» a ogni lettura |
| **Samsung DeX** | ⭐ **Chrome per Android** | ⚠ ma con l'avvertenza del §3.A: sui sistemi mobili la keyboard lock di Chromium era dichiarata *«a no-op on mobile platforms»* `[S]` all'atto dell'implementazione, e Firefox 151 la disabilita esplicitamente su Android `[S]`. ⛔ **Su DeX il prezzo va misurato, non dedotto**: è la riga 4 del §4.4 |
| **iPhone / iPad** | ⚠ **si serve, ma si dichiara** | Safari non ha `clipboardchange`, non ha i permessi degli appunti, e su iPhone lo schermo intero è parziale `[S]`. È il posto dove il §5.3 si vede di più |

⛔ **Consigliare non è escludere.** `SPECIFICHE.md` §7.3-bis dice *«si dichiara»*, non *«si
blocca»*: la pagina serve tutti e tre i motori e dice, su ciascuno, che cosa non può fare.

### 5.3 ⛔ Che cosa la pagina deve dire all'utente

*È il punto in cui questo rapporto diventa un requisito. La regola è quella di sempre: **si
dichiara quel che non si può fare, non si fa finta**.*

**Quando**: alla connessione, una volta, in un riquadro che si chiude — **non** un avviso che
riappare. E una voce nel menu, sempre raggiungibile, che dice lo stesso in dettaglio.

**Che cosa**, in tre righe e nella lingua dell'utente:

1. ⛔ **«Su questo browser queste scorciatoie restano al browser e non arrivano al desktop
   remoto: …»** — con **l'elenco vero di questo motore**, riempito dalla tabella del §2, non un
   generico «alcune». ⭐ **E l'elenco cambia quando si entra a schermo intero**: la stessa voce di
   menu deve dirlo aggiornato;
2. **«Per averle tutte: schermo intero»** — con il bottone lì. ⚠ E la contropartita scritta
   accanto: **«per uscire, tieni premuto Esc»** (1,5 s su Safari, 2 s su Chrome `[S]`). Un utente
   che non lo sa e preme Esc una volta si ritrova fuori dalla sessione senza capire perché;
3. **«Gli appunti: …»** — e qui tre testi diversi, uno per stato:
   - permesso concesso: **niente**. Se funziona non si dice nulla;
   - permesso da chiedere: *«per incollare dal telefono al desktop remoto serve un permesso —
     concedilo una volta e non te lo chiede più»*;
   - motore senza permessi (Firefox, Safari): *«ogni volta che incolli dal dispositivo, il browser
     ti chiede conferma. Non possiamo toglierlo»*.

⛔ **E la cosa che la pagina NON deve fare**, ed è il difetto che tutti e tre i riferimenti hanno:
**fallire in silenzio**. noVNC con permesso negato **nasconde il pannello degli appunti**
(`app/ui.js:1864-1887` `[R]`); Guacamole degrada su un clipboard interno senza dire niente
(`clipboardService.js:579-581` `[R]`); Xpra scrive nel registro di debug e va avanti
(`Client.js:1976` `[R]`). ⭐ **Sono tre prodotti maturi che hanno fatto la stessa scelta sbagliata:
per noi è la conferma che è una trappola facile, non che sia giusta.**

### 5.4 Le quattro conseguenze sul disegno, che nascono dal codice letto

1. ⛔ **`Ctrl+V` dentro la pagina non deve incollare, e va detto nel protocollo.** Tutti e tre i
   riferimenti mandano `Ctrl+V` al server come battuta, e il testo deve essere **già** di là:
   Guacamole aspetta la sincronizzazione a passi di 10 ms, Xpra ritarda **ogni battuta di 100 ms**
   quando gli appunti sono in ballo `[R]`. ⭐ **Con `clipboardchange` il ritardo si può togliere**,
   perché il testo arriva quando cambia e non quando si incolla — ma sul filo RCP serve
   comunque **un ordine garantito fra il canale appunti e il canale input**, o si incolla la roba
   di prima. **Va scritto in `RCP.md`.**
2. **Il rilascio dei tasti sul `blur` è un requisito, non un'accortezza.** La sessione remota
   sopravvive alla connessione (`SPECIFICHE.md` §8.3): un `Ctrl` rimasto premuto la rende
   inservibile **e non si ripara riconnettendosi**, perché al riattacco nessuno manda il rilascio.
   ⭐ **Guacamole ha la cura più completa dei tre e va copiata**: non solo `reset()` su
   `window.onblur`, ma **la risincronizzazione dei modificatori dai flag degli eventi del mouse**
   — `Keyboard.js:944-953` `[R]`: *«Mouse and touch events provide an opportunity to resync
   modifier state that has drifted via key events that could not be received, such as lock keys
   toggled while the window lacked keyboard focus»*. ⛔ **E il tri-stato**: un modificatore che non
   si sa vale `null`, non `false` (`Keyboard.js:1918-1920` `[R]`) — rilasciare quel che non si sa è
   esso stesso un difetto.
3. ⚠ **La ripetizione: decidere, non ereditare.** I tre riferimenti fanno tre cose diverse — Xpra
   inoltra la raffica dell'OS locale, noVNC pure (ma tiene fermo il keysym), Guacamole **la genera
   lui** a 500 ms + 50 ms e non ripete mai modificatori e lock (`Keyboard.js:839-851` `[R]`).
   `DECISIONI.md` §5-bis.6 dice già *«la ripetizione non è nostra: a ripetere è l'applicazione»* —
   ⭐ **allora la scelta giusta è filtrare `event.repeat === true` e non mandarlo**, che è la sola
   che non raddoppia con quella del desktop remoto. ⛔ **Ma con una guardia**: BCD documenta che
   **prima di Chrome 139, su Linux sotto X11 e con più tasti premuti insieme, `repeat` è
   sbagliato** `[S]`. Chi filtra su `repeat` là inietta pressioni fantasma. `[?]` **Da confermare
   col gruppo C del banco.**
4. ⛔ **Il dizionario `code` → evdev del server va copiato da Chromium, non scritto a mano — e deve
   accettare gli alias.** La specifica non ha la tabella (§3.A.3); i tre motori usano nomi diversi
   per lo stesso tasto (`VolumeUp` contro `AudioVolumeUp`, `OSLeft` contro `MetaLeft`); e ⛔ **`""`
   e `"Unidentified"` sono lo stesso caso**, che va nel registro come «posizione non determinabile»
   — mai indovinata. ⭐ È la stessa regola di `SPECIFICHE.md` §7.3: *«mai una lettera diversa, mai
   un silenzio»*, applicata alle posizioni invece che alle lettere.

---

### 5.5 ⛔ Le righe dei documenti che questo rapporto obbliga a correggere

*`README.md`: «quando una misura contraddice un documento, lo si aggiorna nello stesso momento».
⚠ Qui non è una misura ma una lettura di specifiche — vale lo stesso, e le correzioni sono quattro.*

| Documento | Che cosa dice oggi | Che cosa va scritto | Fonte |
|---|---|---|---|
| `SPECIFICHE.md` §7.3-bis | *«la Keyboard Lock […] `[S]` solo su Chrome ed Edge»* | ⛔ **falso dal 2026**: c'è su tutti e tre, con **due API diverse** — §3.A.1, §5.1 | `[S]` |
| `SPECIFICHE.md` §9 | *«non si può sorvegliare la clipboard in silenzio»* + la `[?]` sul verso dispositivo → sessione | ⭐ **si può, su Chromium, dal gennaio 2026**, con `clipboardchange` — e **solo mentre la pagina ha il fuoco**. Su Firefox/Safari resta vero — §3.B.3 | `[S]` |
| `SPECIFICHE.md` §7.3-bis | la `[?]` *«quante e quali si perdano davvero su ciascun motore non l'ha misurato nessuno»* | ⚠ **resta aperta**, ma si restringe: la tabella del §2 dice **le capacità**; l'elenco tasto-per-tasto è un esito del banco §4, non della lettura | `[?]` |
| `PIANO.md` §1.2, misura S3 | *«quante scorciatoie si perdono, motore per motore»* | ⛔ **la domanda va riformulata**: non «quante», ma **in quale dei tre stati A/B/C** cade ciascuna, e **in quale dei tre modi** (finestra / schermo intero / schermo intero con lock) — §3.A.2 | `[S]` |

⚠ **E una `[?]` nuova, che prima non c'era**: se su **DeX** la keyboard lock sia davvero un no-op.
Se lo è, ⛔ **l'uso primario dichiarato dall'utente è anche il posto dove si perde di più** — e
`DECISIONI.md` §5-bis.0 dice che *«le scorciatoie sono metà del lavoro»*. È la riga più importante
del banco.

---

## 6. Le fonti

### 6.1 Specifiche `[S]`

| Che cosa | URL | Stato al 9 ago 2026 |
|---|---|---|
| **Fullscreen API Standard** — è qui che vive `keyboardLock` | https://fullscreen.spec.whatwg.org/ | Living Standard, aggiornato **17 luglio 2026** |
| la PR che ha aggiunto `keyboardLock` | https://github.com/whatwg/fullscreen/pull/232 | **merged l'8 maggio 2026** |
| la discussione originaria | https://github.com/whatwg/fullscreen/issues/231 | aperta dal proponente di WebKit |
| **Keyboard Lock** (la vecchia, WICG) | https://wicg.github.io/keyboard-lock/ | Draft Community Group Report, **6 ottobre 2021** — fermo |
| l'*explainer* della vecchia | https://github.com/WICG/keyboard-lock/blob/gh-pages/explainer.md | |
| **Clipboard API and events** | https://w3c.github.io/clipboard-apis/ | contiene `clipboardchange` §5.2.1 |
| la PR di `clipboardchange` | https://github.com/w3c/clipboard-apis/pull/239 | |
| **UI Events** | https://w3c.github.io/uievents/ | `repeat`, `isComposing`, ordine degli eventi |
| **UI Events KeyboardEvent code Values** | https://w3c.github.io/uievents-code/ | ⛔ **Working Draft del 9 maggio 2023**, e **non contiene** la corrispondenza con evdev — vedi §3.A.3 |
| **Keyboard Map** — l'algoritmo di `getLayoutMap()` | https://wicg.github.io/keyboard-map/ | Draft CG Report, 17 giugno 2022. ⚠ Copre **solo le 50 Writing System Keys**, e vuole il permesso `keyboard-map` |
| **Input Events Level 2** | https://w3c.github.io/input-events/ | ⛔ `insertCompositionText` **non è annullabile** |
| **Wayland `keyboard-shortcuts-inhibit-unstable-v1`** | https://wayland.app/protocols/keyboard-shortcuts-inhibit-unstable-v1 | *«The Wayland compositor is however under no obligation to disable all of its shortcuts»* |

### 6.2 Note di rilascio e annunci `[S]`

| Che cosa | URL | Data |
|---|---|---|
| **Safari 26.4** — la keyboard lock, con l'Esc a 1,5 s | https://webkit.org/blog/17862/webkit-features-for-safari-26-4/ | marzo 2026 |
| **Firefox 151** — `options.keyboardLock` | https://developer.mozilla.org/en-US/docs/Mozilla/Firefox/Releases/151 | **19 maggio 2026** |
| Firefox, *Ship Fullscreen keyboard lock to Desktop* | https://bugzilla.mozilla.org/show_bug.cgi?id=2032302 | RESOLVED FIXED, ramo 151, `dom.fullscreen.keyboard_lock.enabled` |
| Firefox, *Intent to prototype & ship* | http://www.mail-archive.com/dev-platform@mozilla.org/msg01767.html | **17 aprile 2026** |
| **Chrome 144** — `clipboardchange` | https://developer.chrome.com/release-notes/144 | **13 gennaio 2026** |
| `clipboardchange`, *Intent to Ship* | https://groups.google.com/a/chromium.org/g/blink-dev/c/UgYnldQ0-VY | Mozilla e WebKit: **«No signal»** |
| `clipboardchange`, la guida Chrome | https://developer.chrome.com/blog/clipboardchange | |
| Chrome, keyboard lock e i permessi | https://developer.chrome.com/blog/keyboard-lock-pointer-lock-permission | ⛔ aggiornato **17 marzo 2026**: *«We have decided not to launch the Keyboard Lock and Pointer Lock permissions»* |
| Chrome, la guida alla keyboard lock | https://developer.chrome.com/docs/capabilities/web-apis/keyboard-lock | l'Esc a 2 s |
| Chrome Platform Status, *Keyboard Lock* | https://chromestatus.com/feature/5642959835889664 | Chrome **68**, *«While in fullscreen, this API allows apps to receive keys normally handled by the system or the browser like Cmd/Alt-Tab, or Esc»* |
| Chromium, *Browser Shortcuts in Fullscreen* | https://groups.google.com/a/chromium.org/g/blink-dev/c/wlRDnLbyVlk | `Ctrl/Cmd+(T\|W\|N)` in schermo intero; **Esc e F11 restano al browser** |
| Firefox esce da schermo intero sulle richieste di permesso | https://bugzilla.mozilla.org/show_bug.cgi?id=1522120 | RESOLVED FIXED in **Firefox 70** |
| **Async Clipboard API** su WebKit | https://webkit.org/blog/10855/async-clipboard-api/ | le due sole eccezioni alla conferma |

### 6.3 Posizioni degli altri motori `[S]`

| Chi | Su che cosa | Posizione | Data |
|---|---|---|---|
| Mozilla | **Keyboard Lock** (WICG, `navigator.keyboard.lock`) | ⛔ **negativa** — *concerns: API design* | issue [#196](https://github.com/mozilla/standards-positions/issues/196), chiusa il **15 aprile 2026** |
| Mozilla | **Fullscreen keyboard lock** (WHATWG) | ⭐ **positiva** | issue [#1385](https://github.com/mozilla/standards-positions/issues/1385), **7-23 aprile 2026** |
| WebKit | **Full Screen based Keyboard Lock API** | proposta da WebKit stesso, poi **spedita in Safari 26.4** | issue [#481](https://github.com/WebKit/standards-positions/issues/481), aperta il 19 aprile 2025 |

⭐ **Queste tre righe raccontano la storia**: la vecchia API era Chrome-e-basta e gli altri due la
rifiutavano; quella nuova è nata in WebKit, è passata dal WHATWG, e in dodici mesi l'hanno spedita
sia Safari sia Firefox. **Nel 2026 la tastiera nel browser è diventata un problema meno grave di
quanto `SPECIFICHE.md` §7.3-bis dia per scontato.**

### 6.4 Tabelle di compatibilità `[S]`

- MDN `browser-compat-data`: [`api/Keyboard.json`](https://github.com/mdn/browser-compat-data/blob/main/api/Keyboard.json),
  [`api/Clipboard.json`](https://github.com/mdn/browser-compat-data/blob/main/api/Clipboard.json)
- MDN: [Keyboard: lock()](https://developer.mozilla.org/en-US/docs/Web/API/Keyboard/lock),
  [Element.requestFullscreen()](https://developer.mozilla.org/en-US/docs/Web/API/Element/requestFullscreen),
  [Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API)
- caniuse: [fullscreen](https://caniuse.com/fullscreen) — Safari iOS **supporto parziale** da 12 a 26.5

⚠ **Un limite di questa ricerca, dichiarato**: ⛔ **non sono riuscito a stabilire da fonte diretta
se Chrome supporti oggi `requestFullscreen({keyboardLock:"browser"})`.** `browser-compat-data` non
ha ancora una voce per quel parametro (verificato: la chiave `requestFullscreen` in
`api/Element.json` ha il solo `__compat`, nessuna sottochiave di opzioni); `chromestatus` ha solo la
voce del 2018 per `navigator.keyboard.lock()`. L'unico indizio è l'*intent* di Mozilla del 17 aprile
2026, che scrive *«Chromium: ha implementato un'API diversa dalla versione 68»* `[S]` — cioè al
netto di novità recenti **Chrome sta ancora sulla sua**. **È `[?]`, ed è una riga del banco** (§4.1
punto 3): si chiamano tutte e due e si guarda quale delle due blocca davvero.

### 6.4-bis Le tabelle `code` → evdev, lette nel sorgente dei motori `[R]`

*Sono la fonte del §3.A.3, e sono la tabella che il server dovrà contenere.*

| Che cosa | URL |
|---|---|
| ⭐ **Chromium, la tabella canonica** | https://raw.githubusercontent.com/chromium/chromium/main/ui/events/keycodes/dom/dom_code_data.inc |
| Chromium, la conversione e l'offset XKB | https://raw.githubusercontent.com/chromium/chromium/main/ui/events/keycodes/dom/keycode_converter.cc |
| Chromium, Windows (scan code da `lParam`) | https://raw.githubusercontent.com/chromium/chromium/main/ui/events/win/events_win_utils.cc |
| Chromium, Android (`code` dallo `scanCode`) | https://raw.githubusercontent.com/chromium/chromium/main/components/input/web_input_event_builders_android.cc |
| Chromium, Wayland | https://raw.githubusercontent.com/chromium/chromium/main/ui/ozone/platform/wayland/host/wayland_keyboard.cc |
| **Gecko** | https://raw.githubusercontent.com/mozilla/gecko-dev/master/widget/NativeKeyToDOMCodeName.h |
| **WebKitGTK** — il WebKit che gira su Linux | https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebKit/Shared/gtk/WebKeyboardEventGtk.cpp |
| WebKit su macOS | https://raw.githubusercontent.com/WebKit/WebKit/main/Source/WebCore/platform/mac/PlatformEventFactoryMac.mm |
| ⭐ **il kernel** — l'elenco vero dei `KEY_*` | https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/input-event-codes.h |
| MDN, `KeyboardEvent` | https://github.com/mdn/browser-compat-data/blob/main/api/KeyboardEvent.json · https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_code_values |
| Microsoft, gli scan code | https://learn.microsoft.com/en-us/windows/win32/inputdev/about-keyboard-input |
| BlocMaiusc su macOS, **WONTFIX** | https://bugzilla.mozilla.org/show_bug.cgi?id=712535 |

### 6.5 Codice di riferimento letto `[R]`

*I tre cloni stanno fuori dal repository, come da `README.md` («`reference-*/` — non versionati»).
Ogni citazione di questo rapporto porta `file:riga` relativa alla radice del clone.*

| Progetto | Origine | Commit letto | Data | Versione |
|---|---|---|---|---|
| **noVNC** | `https://github.com/novnc/noVNC` | `7c36fabe599e053c5a81e98e091ac636f6c1e174` | 6 giu 2026 | 1.7.0 + master |
| **Apache Guacamole** | `https://github.com/apache/guacamole-client` | `7fcdce8cb4fc670af3864d19b0967dd721acb4c3` | 6 ago 2026 | 1.6.1-SNAPSHOT |
| **Xpra html5** | `https://github.com/Xpra-org/xpra-html5` | `3ecf4f2a175c2a95090591020a9a1e9be979dc8d` | 6 ago 2026 | 22 in sviluppo (release 21.0 dell'11 mag 2026) |

I file che contano, per chi vorrà rileggerli:

- noVNC: `core/input/keyboard.js`, `core/input/util.js`, `core/input/domkeytable.js`,
  `core/input/keysymdef.js`, `core/input/xtscancodes.js`, `core/clipboard.js`,
  `core/util/browser.js`, `core/rfb.js`, `app/ui.js`, `vnc.html`;
- Guacamole: `guacamole-common-js/src/main/webapp/modules/Keyboard.js` (1975 righe),
  `.../InputSink.js`, `guacamole/src/main/frontend/src/app/clipboard/services/clipboardService.js`,
  `.../app/client/services/guacFullscreen.js`, `.../app/index/controllers/indexController.js`,
  `.../app/textInput/directives/guacTextInput.js`;
- Xpra: `html5/js/Keycodes.js`, `html5/js/Client.js`, `html5/js/Utilities.js`, `html5/index.html`,
  `html5/clipboard.html`.

### 6.6 ⛔ «Non l'ho trovato» contro «ho verificato che non c'è»

*`LEZIONI.md` §1.9. Le righe che seguono sono **verifiche negative con controllo positivo**, non
assenze di risultati.*

| Affermazione negativa | Come è stata verificata | Controllo positivo |
|---|---|---|
| **noVNC non usa la Keyboard Lock** | `grep -rn "navigator\.keyboard\|keyboard\.lock\|getLayoutMap\|keyboardLock" .` → **zero righe, uscita 1** | la stessa grep su `requestFullscreen` trova `app/ui.js:1421-1428`: **lo strumento sa trovare quel che c'è** |
| **noVNC non ascolta `paste`/`copy`/`cut`/`beforeinput`/composizione** | `grep -rn "addEventListener(['\"](paste\|copy\|cut\|beforeinput\|composition…)" core/ app/` → zero righe | la stessa forma trova `'blur'` in `keyboard.js:277` e `'input'` in `app/ui.js:273` |
| **Guacamole non usa `event.code`** | `grep -n "\.code\b" Keyboard.js` → zero righe; su tutti i moduli le sole occorrenze sono `Status.js:50` e `Tunnel.js:1005` | quelle due occorrenze **sono** il controllo positivo: la grep funziona |
| **Guacamole non interroga i permessi** | `grep -rn "navigator.permissions\|clipboard-read\|clipboard-write"` → zero righe | la stessa grep su `navigator.clipboard` trova le 4 occorrenze di `clipboardService.js` |
| **Guacamole non ha nulla di specifico per Android** | `grep -rni "android"` su `guacamole-common-js/src` e sul frontend → zero righe | la stessa grep su `ipad|iphone|ipod` trova `Keyboard.js:1616`, e su `^mac` trova `Keyboard.js:1624` |
| **Xpra non gestisce la ripetizione** | `grep -rni "repeat"` su `Client.js`, `Keycodes.js`, `index.html` → zero righe | la stessa grep su `setInterval` trova `Client.js:2643` e `:3021` |
| **Xpra non usa composizione né `beforeinput`** | `grep -rni "inputmode\|contenteditable\|beforeinput\|compositionstart\|compositionend\|isComposing"` su `html5/js/*.js` e `html5/*.html` → zero righe | la stessa grep trova `oninput`/`"input"` in `index.html:1028` |
| ⛔ **la specifica `uievents-code` NON contiene la corrispondenza evdev** | estratto tutto il testo del documento (152 967 byte) e cercato: `evdev` → **0**, `linux` → **0** | ⭐ **il controllo positivo è nella stessa ricerca**: `scancode` dà 2 occorrenze e `USB HID` ne dà 3 — **lo strumento sa trovare quel che c'è**, quindi lo zero è uno zero vero |
| **`XKB == evdev + 8` senza eccezioni in Chromium** | confrontate **tutte le 246 righe attive** di `dom_code_data.inc`: **0 violazioni** | il caso opposto sarebbe stato **almeno una riga** con `xkb ≠ evdev+8`, o una tabella di eccezioni. Non c'è, e la costante `kXkbKeycodeOffset = 8` è dichiarata nel sorgente |
| **`getLayoutMap()` e `keyboard.lock()` non esistono fuori da Chromium** | `browser-compat-data` dice **`false`** per `firefox` e `safari` — ⛔ che in BCD significa *«verificato non supportato»*, **non** `null` = «sconosciuto» | la stessa fonte dà `68`/`69` per Chrome |
| **Firefox e Safari non hanno `clipboardchange`** | ⛔ **non è una grep**: la voce **esiste** nella specifica e in `browser-compat-data`, e la tabella dice `false` per Gecko e WebKit; l'*intent to ship* registra **«No signal»** da entrambi | la stessa tabella dà `144` per Chrome: **la fonte sa dire di sì quando è sì** |
| **Firefox e Safari non hanno i permessi `clipboard-read`/`clipboard-write`** | MDN lo scrive in forma positiva: *«not supported (and not planned to be supported) by Firefox or Safari»* — è **una dichiarazione**, non un'assenza | la stessa pagina elenca i permessi che Chromium **ha** |
