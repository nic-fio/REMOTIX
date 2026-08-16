# F4-IN-3 · XPRA, IL SERVER — quando lo schermo è fermo e il mouse si muove

*Studio dell'input, 14 agosto 2026. Bersaglio: il **server** di xpra (Python), ⛔ non il client
HTML5 — quello è già in `STUDI.md` §xpra e in `F4-AND-4-come-fanno-gli-altri.md`.*

| | |
|---|---|
| deposito | `https://github.com/Xpra-org/xpra` — clonato in `/tmp/studio-input/xpra/` |
| commit | **`43ec2ca433f9e08fde0ba0c9d5e80a580a417d48`**, ramo **`master`**, 14 agosto 2026 |
| controllo incrociato | `Xpra-org/xpra-html5` `e06046fb2b02638d172c8a0c71d4ea010488c30a` in `/tmp/studio-input/xpra-html5/` — **usato per una riga sola** (§1.4), non ristudiato |
| porte | nessuna: studio a sola lettura, niente è stato messo in esecuzione |

---

## ⭐⭐⭐ IL VERDETTO, IN TRE RIGHE

1. ⛔ **La frase da refutare è FALSA nella metà che conta.** `[R]` Il server di xpra ha **tre**
   meccanismi che mandano roba al client quando si muove **solo** il puntatore e lo schermo è
   fermo — e uno di essi (`pointer-position`) nasce **esattamente** nel modo di cattura che è il
   nostro: lo *shadow*, cioè «riprendo un desktop che esiste già».
2. ⭐⭐ **La riga che cambia il prodotto**: `[R]` `xpra/server/shadow/shadow_server_base.py:429`
   — **un timer da 20 ms** (`POLL_POINTER`) che **non aspetta nessun fotogramma** e spedisce
   `pointer-position` (`xpra/server/source/pointer.py:82`) su un canale a **priorità più alta di
   quello dei fotogrammi** (`xpra/server/source/client_connection.py:213`). ⇒ **In xpra il
   puntatore non dipende dal fotogramma. Mai. Da nessuna parte.**
3. ⚠ **E la terza parte della frase — «su Wayland non si può ordinare a un compositore di
   ridipingere» — è VERA, e xpra ha esattamente il nostro stesso difetto**: `[R]`
   `xpra/codecs/pipewire/capture.py:143-145`, `refresh()` risponde `False` se PipeWire non ha
   consegnato niente; `[R]` `shadow_server_base.py:310-312` allora **salta il damage**. ⇒ Loro
   non hanno risolto il fotogramma: **hanno tolto il puntatore dal fotogramma.**

> ### ⭐⭐⭐ La riga da portarsi via, in grassetto e con la fonte
>
> **`[R]` `xpra/server/subsystem/pointer.py:357` — il movimento del puntatore NON provoca MAI un
> aggiornamento dello schermo in xpra, in nessun modo di funzionamento.** La verifica è
> esaustiva: `user_event("pointer")` (riga 606) finisce **solo** nel contatore di inattività
> della sessione (`xpra/server/source/idle_mixin.py:76-78`), e non esiste nessun'altra strada
> fra `pointer` e `damage`.
> ⇒ ⛔ **La nostra strada 6.2 «forzare una cattura quando arriva un `PUNTATORE`» non ha nessun
> precedente in xpra.** Loro la stessa domanda l'hanno risolta dall'altra parte: **un pacchetto
> di posizione a sé, su un canale prioritario, a 20 ms.**

---

## 1 · ⭐⭐ Il puntatore quando lo schermo è fermo *(domanda 1 del briefing, e il ⭐⭐ del mandato)*

### 1.1 Che cosa fa il server quando riceve `pointer_position` dal client: **non risponde**

`[R]` `xpra/server/subsystem/pointer.py:614-640` (`_process_pointer_position`, il pacchetto che
manda il client HTML5) e `:581-612` (`_process_pointer_motion`, la forma v5). Il percorso è:

- riga 627-628: **salva** la posizione nella sessione (`ss.mouse_last_position`,
  `ss.mouse_last_relative_position`) — ⭐ il server *sa* dov'è il puntatore, gliel'ha detto il
  client;
- riga 631: `ss.user_event("pointer-position")` — ⇒ **solo** il contatore di inattività;
- riga 638: `process_mouse_common(...)` → sposta il puntatore vero e **basta**.

⛔ **Nessun pacchetto di ritorno.** Ed è una scelta scritta a chiare lettere, `[R]`
`xpra/server/subsystem/pointer.py:357`:

```python
if ALWAYS_NOTIFY_MOTION or self.last_mouse_user is None or self.last_mouse_user != ss.uuid:
    ss.update_mouse(wid, event.x_root, event.y_root, event.x, event.y)
```

⇒ **al client che ha mosso il mouse non si rimanda indietro la sua stessa posizione.** Sarebbe
un giro di rete per dirgli una cosa che sa già. `ALWAYS_NOTIFY_MOTION` esiste
(`pointer.py:22`, `XPRA_ALWAYS_NOTIFY_MOTION`) ma è **spento per difetto**.

### 1.2 ⭐⭐ Il pacchetto di POSIZIONE esiste, è distinto da quello di FORMA, e parte da un timer

`[R]` `xpra/server/source/pointer.py:76-82` — ⭐ **il pezzo centrale di tutto il rapporto**:

```python
def update_mouse(self, wid: int, x: int, y: int, rx: int, ry: int) -> None:
    if self.mouse_last_position != (x, y) or self.mouse_last_relative_position != (rx, ry):
        self.mouse_last_position = (x, y)
        self.mouse_last_position = (rx, ry)          # ⚠ vedi §1.6: è un difetto loro
        self.send_async("pointer-position", wid, x, y, rx, ry)
```

**Chi lo chiama, e quando** — `[R]` `xpra/server/shadow/shadow_server_base.py`:

| riga | che cosa |
|---|---|
| `33` | `POLL_POINTER = envint("XPRA_POLL_POINTER", 20)` — ⭐ **20 millisecondi, 50 volte al secondo** |
| `429` | `self.pointer_poll_timer = self.timeout_add(POLL_POINTER, self.poll_pointer)` |
| `268` | `start_refresh()` chiama `start_poll_pointer()` — ⇒ **si accende insieme alla prima finestra mappata**, non su richiesta |
| `446-451` | legge la posizione e **esce subito se non è cambiata** |
| `457-463` | trova la finestra che contiene il punto e calcola le coordinate relative |
| `469-470` | `for ss in get_sources_by_type(self, PointerSource): ss.update_mouse(...)` |

⛔ **E questo giro non ha NIENTE a che vedere col damage.** `poll_pointer()` (riga 438-444) è un
timer a sé; il timer dei fotogrammi è un altro (`refresh_timer`, riga 270-272). Sono due orologi
separati che girano in parallelo.

⚠ E `update_mouse` **non è protetto** da `pointer_sync`: `[R]` la protezione
(`if ss.pointer_sync and ss is not exclude`) sta in `may_record_pointer_event`
(`xpra/server/subsystem/pointer.py:288-295`), che è un'**altra** strada — quella della
condivisione fra più client. La strada dello shadow chiama `update_mouse` **diretto**. ⇒ **basta
un client solo perché il meccanismo si accenda.**

### 1.3 ⭐ Il canale è PRIORITARIO rispetto ai fotogrammi

`[R]` `xpra/server/source/client_connection.py:212-228`:

```python
def send(self, packet_type: str, *parts, **kwargs) -> None:
    """ This method queues non-damage packets (higher priority) """
```

`update_mouse` usa `send_async` (riga 225-228: `synchronous=False`, `will_have_more=False`);
il cursore usa `send_more` (riga 221-223). ⇒ ⭐ **In xpra il puntatore sorpassa i fotogrammi per
costruzione, non per fortuna.** Da noi il puntatore e il video condividono lo stesso filo.

### 1.4 ⭐⭐ E il client HTML5 lo attua — con una freccia disegnata, **e senza `cursor: none`**

⚠ *Una riga sola dal deposito del client, perché senza di essa il meccanismo di §1.2 sarebbe una
curiosità del server GTK e non una cosa che arriva davvero in un browser.*

`[R]` `xpra-html5/html5/js/Client.js:507` registra il gestore; `:3394-3433`
(`_process_pointer_position`) sposta un elemento `<img id="shadow_pointer">`
(`html5/index.html:180`) mettendogli la **forma e il punto attivo del cursore remoto**
(righe 3414-3419) e sottraendo l'hotspot (3425-3426). `[R]` `html5/css/client.css:443-453`:

```css
#shadow_pointer { position: absolute; z-index: 100000;
                  display: none; pointer-events: none; }
```

⛔⛔ **E il punto che ci riguarda di più**: xpra `[R]` **non mette `cursor: none` da nessuna
parte** — la freccia `#shadow_pointer` **convive** con il cursore vero del browser (che intanto
veste la forma remota via `set_cursor_url`, vedi `STUDI.md` §xpra §2).

⇒ ⭐ **Lo stato che abbiamo consegnato ieri — «due puntatori sovrapposti», descritto in
`F4-DEX-punto-di-ripresa.md` §5 come una resa — è ESATTAMENTE quel che xpra spedisce di
proposito.** Non è un ripiego: è la loro configurazione normale in modo shadow.

⛔ **E una cura che sembrava ovvia è già morta, l'ho verificata**: `pointer-events: none` sulla
freccia disegnata — noi ce l'abbiamo **già** (`[R]` `src/pagina.html:272` e `:4502`). ⇒ **La
regressione dei «4 clic e ZERO movimenti» NON si spiega con quello.** La `[?]` di
`F4-DEX-punto-di-ripresa.md` §5 resta intera, e questo rapporto la restringe: il sospettato è
`cursor: none`, non l'elemento sovrapposto.

### 1.5 ⭐ Il TERZO meccanismo: la forma del cursore parte anche lei senza fotogramma

`[R]` `xpra/server/source/cursor.py:91-109` — `send_cursor()` **non aspetta il damage**, ha il
suo timer:

```python
gbc = self.global_batch_config
if not self.cursor_timer and gbc:
    delay = max(10, int(gbc.delay / 4))          # riga 97
    ...
    self.cursor_timer = GLib.timeout_add(delay, do_send_cursor)   # riga 109
```

⭐ **Un quarto del ritardo di accorpamento dei fotogrammi, con un pavimento a 10 ms.** Il cursore
è dichiarato quattro volte più urgente dell'immagine.

E chi lo sveglia, sul **Wayland** — `[R]` `xpra/wayland/server/subsystem/cursor.py:86-99`: è una
**richiamata dal compositore** (`SeatCursorTracker`, riga 60-62), cioè l'applicazione remota
chiama `wl_pointer.set_cursor` e xpra spedisce **subito**. ⇒ passando col mouse dal fondo di una
finestra al bordo, il client riceve la forma «ridimensiona» **senza un pixel di immagine**.

`[R]` E c'è la protezione contro il doppione, `xpra/server/source/cursor.py:121-124`: se la forma
è identica all'ultima spedita, non parte niente. ⇒ **muovere sopra lo sfondo, in modo seamless,
non manda davvero niente** — ma **non serve**, perché il cursore che si muove è quello del
browser.

⭐ E un quarto, minore ma istruttivo: `[R]` `xpra/server/subsystem/cursor.py:139-158`
(`suspend_cursor`/`restore_cursor`), chiamato da `[R]`
`xpra/server/shadow/pointer.py:21-40` quando il puntatore **esce** dall'area ripresa: il server
manda un `cursor-default` (`source/cursor.py:138-144`). ⇒ **un aggiornamento causato dal solo
movimento**, per dire «qui fuori non comando io».

### 1.6 ⚠ Un difetto loro, che vale la pena di non copiare

`[R]` `xpra/server/source/pointer.py:80-81`:

```python
self.mouse_last_position = (x, y)
self.mouse_last_position = (rx, ry)     # ⛔ doveva essere mouse_last_relative_position
```

⇒ `[?]` la seconda riga sovrascrive la prima: il confronto della riga 79 non fa quel che dice, e
il pacchetto riparte più spesso del necessario. Non l'ho misurato — è lettura.

---

## 2 · ⭐⭐ Il motore di `damage` e il ritardo di accorpamento *(domanda 5 del briefing)*

### 2.1 I numeri di partenza

`[R]` `xpra/server/window/batch_config.py:44-52`:

| costante | valore | che cos'è |
|---|---|---|
| `MIN_DELAY` | **16 ms** | il pavimento (60 al secondo) |
| `START_DELAY` | **50 ms** | da dove si parte |
| `MAX_DELAY` | **500 ms** | il tetto |
| `EXPIRE_DELAY` | **250 ms** | quando scade la regione accumulata |
| `TIMEOUT_DELAY` | **7500 ms** | la resa |
| `MAX_EVENTS` | **50** | quanti eventi di damage si accumulano |
| `ALWAYS` | `0` — ⛔ **ma in shadow è forzato a `True`**, `[R]` `shadow_server_base.py:88` | |

`[R]` `batch_config.py:132-137` — `match_vrefresh()`: **il pavimento sale al ritmo del monitor
dichiarato dal client**. ⇒ il client dice «60 Hz» e il server smette di provare a fare meglio di
16 ms.

### 2.2 Quali grandezze entrano nel conto — **tutte e sei quelle del mandato, e altre**

`[R]` `xpra/server/window/batch_delay_calculator.py:35-79` (`calculate_batch_delay`):

| fattore | dove | che cosa pesa |
|---|---|---|
| **il ritardo di rete del client** | riga 49-51, `get_target_client_latency(min, avg, jitter)` | ⭐ **e il `jitter` è un ingresso a sé** |
| **la coda dei pixel già spediti** | riga 54, 60 — `queue_inspect("damage-packet-queue-pixels", …, div=low_limit, smoothing=sqrt)` | quanti fotogrammi di arretrato |
| **il fuoco** | riga 62 | la finestra col fuoco viene favorita |
| **le regioni scadute** | riga 66, `soft_expired` | *«a strong indicator of problems»* |
| **il limite di banda** | riga 48, passato in `get_factors(bandwidth_limit)` | |
| **le altre finestre** | riga 73-78 | se un'altra è a schermo intero, il pavimento sale a **100 ms**; se questa non ha il fuoco, a **40 ms** |

E il **ritmo di decodifica del client** entra nella *velocità*, non nel ritardo — `[R]`
`batch_delay_calculator.py:216-222`:

```python
min_decode_speed = 1 * 1000 * 1000  # MPixels/s
ads = statistics.avg_decode_speed or 0
if ads > 0:
    dec_lat = min_decode_speed / ads
```

⇒ ⭐ **se il client decodifica piano, il server comprime di meno e più in fretta**, invece di
accodare. Noi questo numero **non ce l'abbiamo affatto**: WebCodecs sa quanto ci mette a
decodificare e non lo dice a nessuno.

`[R]` `batch_delay_calculator.py:82-129` (`update_batch_delay`): il nuovo ritardo è una **media
pesata nel tempo** dei ritardi precedenti (riga 95: peso `0,25` a quelli *tentati*, `0,75` a
quelli *effettivi*) con un decadimento che **rallenta quando già si accorpa molto** (riga 93).
⇒ ⚠ non è un termostato: è un termostato **con memoria**, che si muove piano.

### 2.3 ⭐⭐ E la risposta alla domanda che ci riguarda: **quando la scena è quasi ferma, il ritardo si ANNULLA**

⛔ Questo è il punto in cui mi aspettavo che xpra peggiorasse, e invece no. `[R]`
`xpra/server/window/compress.py:1698-1701`:

```python
elapsed = int(1000*(now-self.batch_config.last_event))
# discount the elapsed time since the last event:
target_delay = delay
delay = max(abs_min_delay, delay-elapsed)
```

⇒ ⭐ **il ritardo di accorpamento si misura dall'ULTIMO EVENTO SPEDITO, non da adesso.**
`last_event` si aggiorna solo quando una regione parte davvero (`[R]` `compress.py:1978`). Se
sono passati 300 ms di quiete e il ritardo calcolato è 50 ms, allora `delay = max(0, 50-300) =
0` ⇒ **il primo fotogramma dopo una pausa parte SUBITO, senza nessun accorpamento.**

⚠ E c'è di più: `[R]` `batch_delay_calculator.py:339-355` — *«raise the quality when there are
not many recent damage events»*: se meno del 50 % dei pixel è cambiato negli ultimi 5 secondi, la
qualità **sale** (riga 352-353), e se negli ultimi 5 secondi si è mosso meno che nei 5 prima,
sale ancora (riga 354-355, `sqrt`).

⇒ ⭐⭐ **Risposta secca alla domanda del mandato: il meccanismo di xpra fa MIGLIORARE la latenza
percepita a scena quasi ferma, non peggiorare** — e lo fa con **una sottrazione di tre righe**
(`delay - elapsed`). ⛔ **È la cosa più economica di tutto questo rapporto, e noi non ce
l'abbiamo**: la nostra latenza a scena ferma non è il ritardo di accorpamento — è l'attesa del
fotogramma. Ma la forma della riga vale lo stesso il giorno in cui accorperemo.

---

## 3 · ⭐ La coda dell'input e la latenza *(domanda 5, seconda metà)*

### 3.1 «L'ultimo vince» esiste, ed è esplicito — **ma sta nel client**

`[R]` `xpra/client/subsystem/pointer.py:133-169` (`send_mouse_position`):

```python
if self.position_timer:
    self.position_pending = packet     # riga 152 — ⭐ SOVRASCRIVE, non accoda
    return
...
delay = self.position_delay - elapsed  # riga 157
if delay > 0:
    self.position_timer = self.timeout_add(delay, self.do_send_mouse_position)
else:
    self.do_send_mouse_position()      # riga 162
```

⭐ **Non c'è nessuna coda: c'è UNA casella**, e il movimento nuovo cancella il vecchio. È «last
wins» alla lettera. Il limite di frequenza è `position_delay`, `[R]`
`xpra/client/subsystem/pointer.py:68-76`:

```python
v = max(60, self.get_subsystem("display").get_vrefresh())
self.position_delay = max(5, 1000 // v // 2 - 5)
```

⇒ a 60 Hz fa **5 ms** (200 posizioni al secondo). ⭐ Ed è **legato al ritmo del monitor**, non a
un numero fisso.

### 3.2 ⭐⭐ Il clic **cancella** la posizione in sospeso e passa avanti

`[R]` `xpra/client/subsystem/pointer.py:115-123` (`send_positional`):

```python
self.client._ordinary_packets.append(packet)
self.position = None
self.position_pending = None
self.cancel_send_mouse_position_timer()
```

⇒ ⭐ **il clic porta con sé la propria posizione e butta via quella in coda.** Non può mai
succedere che un clic arrivi *prima* della posizione che lo riguarda, né che una posizione vecchia
lo segua e sposti il puntatore dopo. ⛔ **Questa è la cura più diretta al sintomo dell'utente
«il mouse ha sempre problemi con le coordinate degli elementi»**, e costa quattro righe.

### 3.3 Lo scarto per numero d'ordine: c'è, e **per i clic è disattivato di proposito**

`[R]` `xpra/server/subsystem/pointer.py:595-600`, sul **movimento**:

```python
if device_id >= 0:
    highest_seq = self.pointer_sequence.get(device_id, 0)
    if INPUT_SEQ_NO and 0 <= seq <= highest_seq:
        log(f"dropped outdated sequence {seq}, latest is {highest_seq}")
        return
```

`[R]` `xpra/server/subsystem/pointer.py:314-319`, sul **bottone** — le stesse righe, **commentate
a mano**:

```python
if device_id >= 0:
    # highest_seq = self.pointer_sequence.get(device_id, 0)
    # if INPUT_SEQ_NO and 0<=seq<=highest_seq:
    #    log(f"dropped outdated sequence {seq}, latest is {highest_seq}")
    #    return
    self.pointer_sequence[device_id] = seq
```

⇒ ⭐⭐ **La regola, letta nel codice: un MOVIMENTO in ritardo si butta, un CLIC in ritardo MAI.**
`INPUT_SEQ_NO` è comunque spento per difetto (`pointer.py:21`, `XPRA_INPUT_SEQ_NO`, `False`),
perché con un client solo e un trasporto ordinato non serve.
⚠ **Per noi cambia**: il nostro «sorpasso del puntatore quando il filo è pieno»
(`F4-DEX-punto-di-ripresa.md` §7) deve fare la stessa distinzione — e va **verificato che non
sorpassi anche i clic**.

### 3.4 Con una connessione a 100 ms

`[?]` **Non misurato** — non ho fatto girare niente. Quel che si legge: `[R]` il ritardo di rete
entra nel conto dell'accorpamento (§2.2) e nella qualità (`batch_delay_calculator.py:296-299`),
`[R]` il puntatore va su un canale prioritario a `send_async` senza attesa di conferma, `[R]` il
limite di frequenza del client (5 ms) è **indipendente** dal ritardo di rete. ⇒ `[?]` a 100 ms
xpra manda **venti posizioni per ogni giro di rete** e non le accorpa mai in salita: la coda è nel
tubo, non nel programma.

---

## 4 · `buffer_refresh` lato server, e il ridisegno differito di qualità *(domanda 4 del mandato)*

### 4.1 Che cosa fa davvero `buffer_refresh` quando arriva

`[R]` `xpra/net/packet_type.py:31` — `buffer-refresh` è **solo il vecchio nome** di
`window-refresh` (`BACKWARDS_COMPATIBLE` è acceso per difetto, `xpra/net/common.py:27`).
Registrato a `[R]` `xpra/server/subsystem/window.py:668`.

La catena, `[R]`:

```
_process_buffer_refresh          subsystem/window.py:410-412   (è un rinvio secco)
 └─ _process_window_refresh      subsystem/window.py:414-444
     ├─ update_batch_config      :436  ← il ramo `batch: {reset: true}`
     └─ _refresh_windows         :441-444, se `refresh-now`
         └─ do_refresh_windows   :460-467
             └─ WindowsConnection.refresh   source/window.py:455-460
```

E il cuore, `[R]` `xpra/server/source/window.py:455-460`:

```python
def refresh(self, wid: int, window, opts) -> None:
    if not self.can_send_window(window):
        return
    self.cancel_damage(wid)                       # ⭐ butta via tutto quel che era in coda
    w, h = window.get_dimensions()
    self.damage(wid, window, 0, 0, w, h, opts)    # ⭐ e chiede la FINESTRA INTERA
```

⭐ **I parametri, decifrati** — `[R]` `subsystem/window.py:414-444`:

| pezzo | significato |
|---|---|
| `wid = 0` | ⭐ **tutte le finestre** (`:426-427`; `-1` è il vecchio sinonimo, `:424-425`) |
| `100` | la **qualità** chiesta (`qual = packet.get_u8(3)`, `:441-444` → `{"quality": qual, "override_options": True}`) |
| `refresh-now: true` | ⛔ è quel che decide se si ridipinge davvero — e **il valore per difetto è `True`** (`:441`) |
| `batch: {reset: true}` | ⭐ **butta via la configurazione di accorpamento tarata finora e la rifà da zero** — `[R]` `source/window.py:462-472`: `ws.batch_config = self.make_batch_config(...)` |

⇒ ⚠ *«can be used for requesting a refresh, or tuning batch config, or both»* — la loro riga di
commento, `[R]` `subsystem/window.py:415`.

### 4.2 ⭐ E rilegge i pixel davvero — non rispedisce una copia

`[R]` `xpra/server/window/compress.py:2168`: `image = self.window.get_image(x, y, w, h)` →
`[R]` `xpra/x11/models/core.py:481-485` → `[R]` `xpra/x11/damage.py:188-221`, che prende il
pixmap composito (`XCompositeNameWindowPixmap`) e ne estrae i pixel con `XShmGetImage`.
⛔ **Nessuna cache: ogni `buffer_refresh` è un giro vero al server X.**

### 4.3 ⭐⭐ Funziona anche se sullo schermo non è cambiato NIENTE — ed è il punto

`[R]` La catena di §4.1 **non passa mai** dall'estensione Damage di X11: `WindowsConnection.refresh`
chiama `self.damage(...)` **incondizionatamente**, e `get_image()` è una lettura sincrona che
risponde comunque, fosse anche con gli stessi identici byte di prima.

⇒ ⭐ **Ecco perché la leva di xpra funziona e la nostra no**: su X11 i pixel **si possono
sempre chiedere**, perché stanno in un pixmap che il server X possiede. Su Wayland col portale i
pixel **te li dà il compositore quando vuole lui** — e infatti xpra, per quella strada, ha lo
stesso identico limite nostro (§5.5).

⛔⛔ **Quindi la terza parte della frase da refutare regge**: `buffer_refresh` **non è una cura
per il difetto del puntatore**, e non lo è nemmeno per xpra. È una cura per **altre due cose**:
il **primo** fotogramma dopo l'accesso (che è il difetto che `STUDI.md` §xpra §1 aveva già colto) e il
ripristino dopo un errore di decodifica.

### 4.4 ⚠ Il ridisegno differito di qualità: c'è, è bello — e in questo commit **non lo chiama nessuno**

Il meccanismo esiste tutto: `[R]` `xpra/server/window/compress.py:2301-2414`
(`do_schedule_auto_refresh`), con il ritardo che **si allunga a ogni nuovo aggiornamento con
perdita** (`refresh_target_time`, `:2390-2414`) ⇒ ⭐ **finché l'utente si muove il fotogramma buono
si rimanda; quando si ferma, parte.** Ritardo di partenza `[R]` **150 ms**
(`xpra/scripts/config.py:1232`, `auto-refresh-delay: 0.15`, mandato dal client in millisecondi,
`xpra/client/subsystem/window/manager.py:196`, letto a `xpra/server/source/encoding.py:391`),
poi ricalcolato su misura della finestra, qualità, congestione e tipo di contenuto
(`compress.py:1520-1568`). La codifica del ridisegno è **sempre a immagine ferma, mai video**:
`[R]` `xpra/codecs/constants.py:45-47` (`webp, avif, jph, png, …`), qualità `AUTO_REFRESH_QUALITY
= 100` (`compress.py:61-63`). Ed è **per regione**, non per finestra intera
(`self.refresh_regions`, `compress.py:489,2416-2426,2472-2481`).

⛔⛔ **MA**: `[R]` in questo commit **`schedule_auto_refresh` non ha nessun chiamante.**

⭐ **Assenza certificata**, come chiede il briefing §8: la stessa ricerca su tutto il deposito
(`grep -rn "schedule_auto_refresh" .`) restituisce **6 righe, tutte definizioni o
sovrascritture** (`compress.py:2288,2299,2301`, `video_compress.py:2273,2303`,
`subsurface_source.py:54`) e **zero invocazioni**; la stessa ricerca su `full_quality_refresh`
**trova invece i chiamanti** (`compress.py:1852`, `compress.py:2789`,
`subsystem/window.py:875`). ⇒ **lo strumento funziona, l'assenza è vera.**

⚠ `[?]` **Non so se sia un residuo di riordino in corso o un difetto vero.** Il mio clone è
superficiale (200 commit) e la storia non basta a dire quando la chiamata è sparita.

⇒ ⭐ **La lezione, e non è tecnica**: stavo per consigliare di rubare un meccanismo che **non
gira**. Se `F4-IN-3` fosse stato scritto sulla documentazione invece che sul codice, il consiglio
sarebbe passato. ⛔ **Quel che resta raccomandabile è la FORMA** — «l'utente si ferma, mandagli
il fotogramma buono; se riprende, rimanda» — **non le righe**, che vanno riprovate da capo.

⭐ Quel che invece è vivo e raggiungibile: `full_quality_refresh` (`compress.py:2494-2519`), coi
suoi tre chiamanti veri — il canale di comando, la scadenza di una regione bloccata
(`compress.py:1852`), e ⭐ **l'errore di decodifica riferito dal client**
(`compress.py:2769-2789`, `decode_error_refresh`). ⇒ ⚠ **quest'ultimo lo vorrei anche io**:
WebCodecs sa quando una `DecoderConfig` fallisce, e oggi da noi quel fallimento **non chiede
niente a nessuno**. E la regione video ha un suo ridisegno a parte, quello sì vivo
(`xpra/server/window/video_subregion.py:186-256`, pavimento a 150 ms alla riga 203).

---

## 5 · Il ridimensionamento, e ⭐⭐ il lato Wayland *(domanda 3 del briefing)*

### 5.1 Che cosa fa il server quando arriva `configure_display`

`[R]` `xpra/server/subsystem/display.py:560-565`: il nome moderno è `display-configure`, con
`configure-display` come alias per i client vecchi — ⭐ **è il pacchetto che manda il client
HTML5**. Il vecchio `desktop_size` viene **normalizzato nella stessa forma** e rilanciato
(`display.py:356-388`).

La catena, `[R]` `xpra/server/subsystem/display.py:404-453` → `:393-402`:

```
_process_display_configure         ss.desktop_size = …            (409-411)
   └─ _apply_desktop_size          self.server.set_screen_size(w,h) (397)
        ├─ calculate_workarea      (401 → 465-493)
        └─ set_desktop_geometry_attributes (402 → 250-259)
```

⭐ E una riga che ci riguarda direttamente, `[R]` `xpra/server/subsystem/display.py:42-53`
(`get_desktop_size_capability`):

```python
w = min(client_w, root_w)
h = min(client_h, root_h)
```

⇒ ⛔ **il MINIMO fra quel che chiede il client e quel che c'è** — l'esatto opposto dello
`std::max` di Chrome Remote Desktop (`F4-AND-4` §Chrome RD). Xpra preferisce **tagliare** che
impaginare.

### 5.2 Su `Xvfb`/`xdummy`: sì, cambia davvero la modalità video — e ne **crea una nuova**

`[R]` `xpra/x11/subsystem/display.py:432-449` (`do_get_best_screen_size`):

```python
if (desired_w, desired_h) in screen_sizes:
    return desired_w, desired_h
if self.randr_exact_size:
    ...
    if RandRBindings().add_screen_size(desired_w, desired_h):
        # we have to wait a little bit ...
        time.sleep(0.5)
        return desired_w, desired_h
```

⭐ `add_screen_size` (`[R]` `xpra/x11/bindings/randr.pyx:853-895`) fabbrica una modalità con
`XRRCreateMode` e la attacca all'uscita con `XRRAddOutputMode`. ⇒ **la misura che chiede il
client non deve esistere: la si inventa.** Tetto: `MAX_NEW_MODES = 32` (`randr.pyx:34`), le
vecchie si buttano. Poi si commuta con `XRRSetScreenConfigAndRate` + `XRRSetScreenSize`
(`x11/subsystem/display.py:551-561`).

C'è anche una strada più nuova: `[R]` `x11/subsystem/display.py:477-488` — con RandR 1.6 e il
driver `dummy` a 16 uscite (`randr.pyx:1006-1042`, `is_dummy16()`), xpra **rispecchia la
disposizione dei monitor del client**, uno per uno (`mirror_client_monitor_layout`, `:608-633`).
⇒ ⭐ **un client con due schermi ottiene due monitor veri sul server.**

### 5.3 Quando non ce la fa, **lo dice** — e questa è la riga che manca a noi

`[R]` `xpra/x11/subsystem/display.py:567-574`:

```python
if root_w != w or root_h != h:
    log.warn("Warning: tried to set resolution to %ix%i", w, h)
    log.warn(" and ended up with %ix%i", root_w, root_h)
```

E soprattutto — `[R]` `xpra/server/subsystem/display.py:300-318` → `xpra/server/source/display.py:171-179`:

```python
if self.desktop_size_server != (root_w, root_h):
    self.desktop_size_server = root_w, root_h
    self.send("desktop_size", root_w, root_h, max_w, max_h)
```

⇒ ⭐⭐ **il server rimanda indietro la misura VERA più il MASSIMO che sa fare**, e lo fa dal
segnale `size-changed` di GDK (`xpra/server/subsystem/gtk.py:132,143-156`), non dalla chiamata.
⛔ **`RCP.md` §4.5 «la tela concessa» non ha questo ritorno**: da noi `[M]` (`STUDI.md` §xpra §3) un
client che chiede 1280×720 riceve la concessione e poi *nessun fotogramma*, «client nero senza
errori». **Il pezzo mancante è tre righe: dire al client che cosa hai potuto fare davvero.**

⭐ E c'è un secondo ritorno, che è una lezione di garbo: `[R]`
`xpra/x11/subsystem/display.py:589-604,635-640` — se il DPI ottenuto si scosta di ≥10 da quello
chiesto, il server manda al client una **notifica visibile** («*you may experience scaling
problems, such as huge or small fonts*»), una volta sola per sessione.

### 5.4 ⭐⭐ Xpra HA un lato Wayland — ma non è il nostro caso, e il confine è netto

`[R]` `/tmp/studio-input/xpra/xpra/wayland/server/` — **44 file**, fra cui `compositor.pyx`,
`output.pyx`, `seamless.py`, `subsystem/{pointer,cursor,keyboard,window,display}.py`. Il
ridimensionamento, `[R]` `xpra/wayland/server/subsystem/display.py:51-67` → `output.pyx:182-195`:

```python
wlr_output_state_set_custom_mode(&state, width, height, refresh)
```

⛔⛔ **E qui il confine va dichiarato prima che lo scopra qualcun altro: xpra, in quel modo, È IL
COMPOSITORE.** È un compositore `wlroots` scritto da loro. Può cambiare la modalità di un'uscita
perché l'uscita è sua. **Noi non siamo il compositore: Mutter lo è.** ⇒ ⛔ **`output.resize()`
non è trasferibile in nessuna forma.** La nostra strada 6.1 (chiedere a Mutter un monitor
virtuale della misura del client) resta l'unica, e questo rapporto **non la conferma né la
smentisce**.

⭐ Ma il pezzo Wayland di xpra ci serve lo stesso, in un altro punto: `[R]`
`xpra/wayland/server/subsystem/pointer.py:15-19`

```python
class WaylandPointerManager(PointerManager):
    # the compositor tracks its own cursor position,
    # and every event needs the `flush()` that comes with a move:
    SKIP_REDUNDANT_MOVES = False
```

⇒ `[R]` sul lato X11 (`xpra/server/subsystem/pointer.py:83,278-282`) xpra **salta** lo
spostamento se il dispositivo è già lì; **su Wayland no, mai**, perché ogni evento deve portarsi
dietro il `flush()`. ⚠ Da verificare se la stessa cosa vale per la nostra iniezione via
`RemoteDesktop`.

### 5.5 ⛔ E il caso che ci somiglia di più: xpra **su PipeWire ha il nostro identico difetto**

`[R]` `xpra/platform/posix/{fd_portal.py,fd_portal_shadow.py,screencast.py,remotedesktop.py}` +
`xpra/codecs/pipewire/capture.py` — xpra sa riprendere un desktop Wayland col portale
`xdg-desktop-portal`, iniettando l'input con `NotifyPointerMotionAbsolute` (`[R]`
`xpra/platform/posix/portal_pointer.py:39-48`). **È la nostra architettura, gemella.**

E allora: `[R]` `xpra/codecs/pipewire/capture.py:143-145`

```python
def refresh(self) -> bool:
    with self._lock:
        return self._image is not None
```

`[R]` `xpra/server/shadow/shadow_server_base.py:307-312`:

```python
updates = [c.refresh() for c in self._captures]
if not any(updates):
    return True          # ⛔ nessun damage, si esce
```

⇒ ⛔⛔ **Se PipeWire non ha consegnato niente, xpra non produce nessun damage. Identico a noi.**
Il loro timer di ripresa gira a **50 Hz** (`[R]` `shadow_server_base.py:65,77-78` +
`xpra/util/parsing.py:29`, `DEFAULT_REFRESH_RATE = 50*1000` millihertz ⇒ 20 ms) ma **interroga**;
non forza il compositore a dipingere. **Non c'è nessuna leva magica.**

⭐ **E questa è la conferma decisiva della tesi di §1**: xpra ha lo stesso limite nostro sul
fotogramma, e il puntatore da loro funziona lo stesso — **perché non passa dal fotogramma.**

---

## 6 · Le misure di latenza *(domanda 6 del mandato)*

### 6.1 Che cosa il server misura — undici numeri, non uno

`[R]`, tutti in `xpra/server/source/source_stats.py` (per client) e
`xpra/server/window/perfstats.py` (per finestra):

| numero | dove sta | dove si aggiorna |
|---|---|---|
| `client_latency` — ⭐ **giro di rete AL NETTO della decodifica del client** | `source_stats.py:66-67` | `source_stats.py:129-141` |
| `client_ping_latency` (giro misurato dal server) | `source_stats.py:68-69` | `xpra/server/source/ping.py:114-119` |
| `server_ping_latency` (giro misurato dal **client** e riferito indietro) | `source_stats.py:70-71` | `ping.py:120-122` |
| `client_decode_time` — ⭐ **quanto ci mette il client a decodificare** | `source_stats.py:64-65`, `perfstats.py:52` | `xpra/server/source/window.py:592-604` |
| `damage_in_latency` (dal damage alla coda d'uscita) | `perfstats.py:57-59` | `compress.py:2554-2555` |
| `damage_out_latency` (dal damage al filo) | `perfstats.py:60-63` | `perfstats.py:102-105` |
| `damage_ack_pending` (le conferme in sospeso, per numero d'ordine) | `perfstats.py:64` | `compress.py:2550`, tolto a `:2713` |
| `frame_total_latency` — ⭐ **il giro completo, damage → conferma** | `source_stats.py:82-84` | `source_stats.py:141` |
| `congestion_send_speed` / `avg_congestion_send_speed` | `source_stats.py:72-75` | `xpra/server/source/window.py:612-624` |
| `tcp_notsent` — ⭐ **la coda del kernel, letta da `TCP_INFO`** | `source_stats.py:76-77` | `source_stats.py:117-127` |
| `congestion_value` | `source_stats.py:86-87` | `source_stats.py:183-192` |

⭐⭐ **Il pezzo che ci manca di più**, `[R]` `source_stats.py:129-141`:

```python
total = now - queued_at
dt = decode_time / 1000.0 / 1000.0     # il client dice quanto ha impiegato
net_total_latency = max(0.0, total - dt)
```

⇒ **il client riferisce il proprio tempo di decodifica, e il server lo SOTTRAE** per isolare la
rete pura. ⛔ Da noi WebCodecs sa esattamente quanto ci mette e **non lo dice a nessuno**: il
nostro `GIRO` mescola rete, decodifica e — per il difetto di §4 di
`F4-DEX-punto-di-ripresa.md` — anche l'attesa del prossimo fotogramma. **Con questa sottrazione
il «peggiore 2161 ms» si sarebbe letto per quel che è in mezza giornata di meno.**

### 6.2 Il `ping`: due direzioni, e porta il carico della macchina

`[R]` `xpra/server/source/ping.py:69-74` — il server manda `ping` con **due** marche temporali
(monotona e da calendario); `[R]` `:92-103` — rispondendo a un `ping` del client, il `ping_echo`
si porta dietro **la media di carico a 1/5/15 minuti** e **l'ultima latenza misurata**; `[R]`
`:106-124` — al ritorno si calcolano e si tengono **entrambe** le direzioni. `[R]` `:24,76-84` —
`PING_TIMEOUT = 60 s`, oltre il quale il client viene **disconnesso**.

### 6.3 ⭐ Come si regola da solo — l'anello è chiuso in quattro punti

`[R]`:

| dal numero | alla decisione | dove |
|---|---|---|
| `min/avg_client_latency` + `jitter` | il **bersaglio** di latenza, che entra nel ritardo di accorpamento | `batch_delay_calculator.py:49-51` |
| `avg_decode_speed` | la **velocità** di codifica (se il client decodifica piano, comprimi meno) | `batch_delay_calculator.py:216-222` |
| `recent_client_latency` | la **qualità** (`latency_q = 3·target/recent`) | `batch_delay_calculator.py:296-299` |
| `avg_congestion_send_speed` | il **tetto di banda**, ridistribuito per finestra a peso di pixel | `xpra/server/source/bandwidth.py:95-136` |

⛔ E la degradazione della rete si legge in un giro solo, `[R]`: conferma in ritardo
(`compress.py:2739-2755`) → `networksend_congestion_event` (`:2636-2681`) →
`record_congestion_event` (`server/source/window.py:612-651`) → sale `congestion_value` → sale il
ritardo di accorpamento (`source_stats.py:239-240`), scendono qualità e velocità
(`batch_delay_calculator.py:210-214,277-278`), scende il tetto di banda.

### 6.4 ⭐⭐ E che cosa VEDE l'utente — la lezione di forma

`[R]` xpra mostra i numeri in **tre** modi, e due sono visibili all'utente finale, non
all'amministratore:

1. `[R]` `xpra/server/source/source_stats.py:255-281` (`get_connection_info`) e `:283-343`
   — `ping_latency` di server e client, `damage.client-latency`, `damage.frame-total-latency`.
   Letti e **disegnati** da `xpra top`: `[R]` `xpra/client/base/top.py:776,785`
   (`"latency: {lcur} ({lavg})"`).
2. ⭐⭐ `[R]` `xpra/server/source/window.py:632-651` — quando la rete peggiora davvero
   (più di `CONGESTION_WARNING_EVENT_COUNT` eventi in 10 secondi), **una notifica sullo schermo
   dell'utente**: *«Network Performance Issue»*, **con dei bottoni** — abbassa la banda / spegni
   l'avviso / ignora. E se preme «abbassa», `[R]` `:653-669`, il tetto di banda **si dimezza
   davvero**.
3. `[R]` `xpra/x11/subsystem/display.py:635-640` — la notifica sul DPI di §5.3.

⇒ ⭐ **Non è «un numero mostrato»: è un numero mostrato CON UN BOTTONE CHE FA QUALCOSA.** Noi il
ritardo lo misuriamo al banco e non lo mostriamo mai (`DECISIONI.md` §2.6); quando l'utente dice
*«mi sembra lento»* non ha un numero, e non ha una leva. ⚠ Il costo è basso e la resa è alta —
ma ⛔ **è una decisione dell'utente**, perché cambia la faccia del prodotto.

---

## 7 · Le otto domande del briefing, in tabella

| # | domanda | risposta per **il server di xpra** |
|---|---|---|
| **1** | quando il mouse si muove e non cambia niente, che cosa viaggia? | ⭐⭐ `[R]` **tre cose, nessuna delle quali è un fotogramma**: `pointer-position` da un timer a **20 ms** (`shadow/shadow_server_base.py:33,429,446-470` → `source/pointer.py:82`); `cursor-data` da un timer a `batch.delay/4` con pavimento **10 ms** (`source/cursor.py:97-109`), su Wayland svegliato dal compositore (`wayland/server/subsystem/cursor.py:86-99`); `cursor-default` quando il puntatore esce dall'area (`subsystem/cursor.py:139-158`). ⛔ Tutte su un canale **a priorità più alta dei fotogrammi** (`source/client_connection.py:213`) |
| **2** | chi disegna il puntatore, e che cosa succede quando la forma cambia? | `[R]` **Nessuno dei tre modelli soli: due insieme.** Il cursore del sistema *veste* la forma remota (`STUDI.md` §xpra §2, `set_cursor_url`), e **in più**, in modo shadow, il client dipinge un `<img id="shadow_pointer">` mosso dal server (`xpra-html5/html5/js/Client.js:3394-3433`, `css/client.css:443-453`). ⛔ **Xpra non mette `cursor: none` da nessuna parte**: i due puntatori convivono di proposito. Quando la forma cambia parte `cursor-data` (`source/cursor.py:116-136`), con protezione contro il doppione (`:121-124`) |
| **3** | il client chiede la misura al server? | ⭐ `[R]` **Sì, e il server la esegue creando una modalità video che non esiste**: `display-configure` → `_apply_desktop_size` → `set_screen_size` → `add_screen_size` con `XRRCreateMode` (`x11/subsystem/display.py:442`, `x11/bindings/randr.pyx:853-895`). Unità: **pixel**, più `desktop-size-unscaled` e un DPI a parte. Se non ce la fa: modalità **più vicina per area** (`x11/subsystem/display.py:456-469`), e ⭐ **rimanda al client la misura vera più il massimo** (`source/display.py:171-179`), oltre a una notifica visibile se il DPI si scosta (`x11/subsystem/display.py:635-640`) |
| **4** | quanti stadi ha la conversione delle coordinate, e dove vive l'offset? | ⭐ `[R]` **Uno solo**, e vive **nel server**: `_adjust_pointer` (`subsystem/pointer.py:235-262`) toglie la differenza fra dov'è la finestra sul server e dove il client l'ha mappata (`ws.mapped_at`); in shadow, `shadow/pointer.py:21-40` somma l'origine della finestra. ⛔ **La pagina non calcola nessun offset** (`F4-AND-4` §3: niente `getBoundingClientRect`). ⇒ i nostri **tre** stadi non hanno riscontro in nessuno dei cinque |
| **5** | come si misura e come si limita la latenza dell'input? | `[R]` **Accorpamento «l'ultimo vince» con UNA casella, non una coda** (`client/subsystem/pointer.py:151-153`), a **5 ms** legati al ritmo del monitor (`:68-76`); ⭐ **il clic cancella la posizione in sospeso** (`:115-123`); scarto per numero d'ordine **sui movimenti sì, sui clic disattivato a mano** (`subsystem/pointer.py:595-600` contro `:314-319`). Sull'uscita: undici numeri (§6.1) e un anello di regolazione chiuso in quattro punti (§6.3) |
| **6** | che cosa c'è per Android, il tocco e DeX? | ⛔ **NIENTE, verificato.** `[R]` la ricerca `-i "touch\|android\|tablet"` su tutto `xpra/server/` trova **solo** `touchpad_device` (`subsystem/pointer.py:164-191`), che è un dispositivo `uinput` per lo scorrimento fine — non il tocco. ⚠ **Lo strumento è certificato**: la stessa ricerca *trova* `touchpad`, quindi non sta guardando nella cartella sbagliata. ⇒ su questa domanda xpra **non ha niente da insegnarci** |
| **7** | che cosa ruberei e che cosa no | vedi §7-bis |
| **8** | la refutazione del mandato | vedi §0 (il verdetto) e §1: ⛔ **la frase è falsa nei due terzi che contano, vera nel terzo che non serve** |

### 7-bis · ⭐⭐ Che cosa ruberei, che cosa no, e quanto costa

| | costo | perché |
|---|---|---|
| ⭐⭐⭐ **Il pacchetto di posizione del cursore, a timer, su canale prioritario** — `POSIZIONE_CURSORE` in `RCP.md`, mandato ogni ~20 ms quando cambia, **indipendente dal fotogramma** | **basso**: un messaggio nuovo e un timer. Da noi è ancora più economico che da loro, perché ⭐ **la posizione ce l'ha già data il client**: non dobbiamo interrogare Mutter | ⛔ È la cura dell'*«è come se si perdessero gli input»*. `[R]` è quel che fa xpra in shadow, ed è **l'unico dei tre meccanismi trasferibile senza attriti**. ⚠ E la pagina lo sa già usare: la freccia disegnata esiste ed è già `pointer-events: none` (`src/pagina.html:272`) |
| ⭐⭐ **Il clic che cancella la posizione in sospeso e porta con sé la propria** — `[R]` `client/subsystem/pointer.py:115-123` | **quattro righe nella pagina** | ⛔ È la cura più diretta di *«il mouse ha sempre problemi con le coordinate degli elementi»*: toglie per costruzione la possibilità che un clic arrivi con la posizione sbagliata |
| ⭐⭐ **Il ritardo che si sconta da sé**: `delay = max(0, delay − elapsed_dall_ultimo_evento)` — `[R]` `window/compress.py:1698-1701` | **tre righe** | Vale il giorno in cui accorperemo. Ora non accorpiamo, quindi ⚠ **non è la cura di oggi** — ma è la riga che impedisce a un accorpamento futuro di rovinare la scena ferma |
| ⭐⭐ **Il tempo di decodifica riferito dal client, e sottratto** — `[R]` `source_stats.py:129-141` | **medio**: un campo nella conferma, e WebCodecs il numero ce l'ha già | ⛔ Senza, il nostro `GIRO` è **inutilizzabile**: mescola rete, decodifica e attesa del fotogramma. `[M]` ha già inquinato mezza giornata (`F4-DEX-punto-di-ripresa.md` §4) |
| ⭐ **Rimandare al client la misura VERA più il massimo** — `[R]` `source/display.py:171-179` | **tre righe** | `RCP.md` §4.5 concede e poi tace: `[M]` «145 fotogrammi prodotti, 0 spediti, client nero senza errori» |
| 🔸 **Un numero di ritardo mostrato con un bottone che fa qualcosa** — `[R]` `server/source/window.py:632-669` | medio | ⛔ **Decisione dell'utente**: cambia la faccia del prodotto |
| ⛔ **NON ruberei: `output.resize()` / `wlr_output_state_set_custom_mode`** (`wayland/server/output.pyx:192`) | — | ⛔ **Xpra lì è il compositore. Noi no.** Non è trasferibile in nessuna forma |
| ⛔ **NON ruberei: `add_screen_size` / `XRRCreateMode`** (`randr.pyx:853-895`) | — | È RandR su X11. Da noi la leva è chiedere a Mutter un monitor virtuale (`mutter.c:502-518`) — **stessa domanda, altro meccanismo** |
| ⛔ **NON ruberei: forzare una cattura sul movimento del puntatore** (la nostra strada 6.2) | — | ⭐ `[R]` **verificato esaustivamente: xpra non lo fa MAI**, in nessun modo di funzionamento (`subsystem/pointer.py:606` → `source/idle_mixin.py:76-78` e basta). Se serve una cattura su movimento, non è xpra che ce lo insegna |
| ⭐ **Il ridisegno chiesto dal client quando la DECODIFICA fallisce** — `[R]` `window/compress.py:2769-2789` (`decode_error_refresh`) | basso | WebCodecs ci dice quando una configurazione o un fotogramma non passa, e oggi da noi quel fallimento **non chiede niente a nessuno** |
| ⛔ **NON ruberei: `buffer_refresh` come cura del difetto di oggi** | — | ⚠ vedi §4.3: è una cura del **primo** fotogramma e della **qualità**, non del puntatore. E ⛔ **funziona da loro perché su X11 i pixel si possono sempre chiedere**; sul portale Wayland xpra ha il nostro identico limite |
| ⛔ **NON ruberei le RIGHE del ridisegno differito di qualità** — solo la forma | — | ⛔ `[R]` **assenza certificata (§4.4): in questo commit `schedule_auto_refresh` non ha nessun chiamante.** Il meccanismo è scritto e non gira |

---

## 8 · ⛔ QUEL CHE QUESTO RAPPORTO NON DICE

⭐ *Obbligatoria, e più utile del resto: qui c'è quel che il prossimo non deve dare per fatto.*

1. ⛔ **Non ho fatto girare xpra. Niente.** Nessun server acceso, nessuna porta occupata, nessun
   pacchetto catturato sul filo. **Tutto quel che c'è qui è `[R]`, letto nel codice.** In
   particolare: `[?]` **non ho la prova che il timer a 20 ms produca davvero 50 pacchetti al
   secondo sul filo** — l'ho letto, non visto.
2. ⛔ **Non so se il meccanismo di §1.2 si accende con un client HTML5 vero.** So `[R]` che il
   server lo manda in modo shadow e `[R]` che il client HTML5 ha il gestore
   (`Client.js:507,3394`). ⚠ **Non ho verificato la stretta di mano**: quale capacità il client
   deve dichiarare perché `PointerConnection` venga costruito (`source/pointer.py:22-26` chiede
   `pointer` o `mouse`), né se il client HTML5 la dichiari. **È il primo controllo da fare.**
3. ⛔ **Non ho verificato che `get_pointer_position()` funzioni sotto Wayland col portale.**
   ⚠ Anzi, la lettura dice il contrario: `[R]` `xpra/platform/posix/pointer.py:8-14` passa da
   `X11CoreBindings().query_pointer()` o dal `get_pointer()` di GDK — **su Wayland puro nessuno
   dei due dà la posizione globale**, e il portale `ScreenCast` non la restituisce. ⇒ `[?]`
   **il polling di §1.2 è probabilmente MORTO sul portale Wayland di xpra.**
   ⭐⭐ **Ma per noi non cambia niente, e conviene dirlo forte: noi la posizione non dobbiamo
   leggerla da nessuna parte — ce l'ha appena data il client** (`subsystem/pointer.py:603` fa
   esattamente questo: la salva). ⇒ **la cura consigliata in §7-bis è più facile per noi che per
   loro.** ⚠ Ma è un `[?]`: non è misurata.
4. ⛔ **Non ho spiegato la regressione dei «4 clic e ZERO movimenti».** Ho ucciso **una**
   ipotesi (`pointer-events: none` manca: falso, `src/pagina.html:272` ce l'ha già) e ho
   ristretto il sospetto a `cursor: none`, `[R]` perché xpra **non lo usa mai**. ⛔ **La `[?]` di
   `F4-DEX-punto-di-ripresa.md` §5 resta aperta.**
5. ⛔ **Non ho letto il compositore `wlroots` di xpra** (`compositor.pyx`, `surface.pyx`,
   `events.pyx`, ~15 file `.pyx`). Ho letto solo i sottosistemi Python che ci stanno sopra. ⚠ Se
   là dentro c'è una risposta migliore alla domanda «quando ridipingere», **non l'ho vista**.
6. ⛔ **Non ho misurato niente sul DeX, né sulla macchina di prova 192.168.0.2.** Questo rapporto
   non contiene un solo `[M]` mio: tutti gli `[M]` citati vengono da
   `F4-DEX-punto-di-ripresa.md`.
7. ⚠ **Non ho confrontato i numeri di xpra coi nostri.** `MIN_DELAY = 16 ms`, `START_DELAY = 50`,
   `MAX_DELAY = 500`, `POLL_POINTER = 20`: sono i loro, tarati su X11 e WebSocket. `[?]` **Che
   20 ms sia il numero giusto per noi non è dimostrato da niente qui dentro.**
8. ⚠ **Il ridimensionamento su Mutter resta intatto.** Questo rapporto **non dice** se
   `RecordVirtual` accetti una misura, né quale; dice solo che xpra risolve la stessa domanda con
   una leva che noi **non abbiamo** (essere il compositore) e con un'altra che noi **non abbiamo**
   (RandR). ⇒ ⛔ **la strada 6.1 va misurata da qualcun altro.**
9. ⚠ `[?]` **Il difetto di §1.6** (`mouse_last_position` scritto due volte) l'ho dedotto
   leggendo. Non ho scritto una prova, non ho aperto una segnalazione, non ne conosco l'effetto
   vero.
10. ⚠ **Il clone è superficiale** (`--depth 200`): `[?]` **non posso dire da quando
    `schedule_auto_refresh` è senza chiamanti** (§4.4), né se in una versione rilasciata lo sia.
    ⛔ Il rapporto vale **per questo commit**, `43ec2ca4` del 14 agosto 2026, non per «xpra».
11. ⚠ **Non ho letto il modo `desktop`/`monitor`** di xpra (`xpra/x11/desktop/`), che è il modo
    più simile al nostro fra quelli su X11. Ho letto lo **shadow** perché è quello che riprende
    un desktop che esiste già, come noi. `[?]` Là dentro potrebbe esserci un'altra risposta.
12. ⛔ **Non ho toccato `src/`.** Nessuna modifica, nessun `git commit`, nessun servizio
    dell'utente fermato o riavviato. Nessuna porta occupata.

---

> ### ⭐⭐ E la riga che non è tecnica
>
> Il mandato mi chiedeva di refutare *«xpra non ha nessun meccanismo per il puntatore a schermo
> fermo»*, e la refutazione è riuscita. ⚠ **Ma la cosa che ho trovato non è quella che cercavo.**
>
> ⛔ **Xpra ha esattamente il nostro stesso difetto** — `[R]` `codecs/pipewire/capture.py:143-145`
> più `shadow/shadow_server_base.py:310-312`: schermo Wayland fermo, PipeWire zitto, nessun
> damage. **Non l'hanno risolto. L'hanno aggirato**, togliendo il puntatore dal fotogramma e
> mettendolo su un canale suo, con un orologio suo, a priorità più alta.
>
> ⇒ ⭐ **Sette volte in questa fase il difetto stava *fra* i pezzi. Questa volta il difetto sta
> nel fatto che due cose viaggiano insieme e dovrebbero viaggiare separate.** Non è un pezzo da
> aggiustare: è una cucitura da tagliare.
