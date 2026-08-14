# XPRA — lo studio, fatto il 14 agosto 2026

*Il settimo studio del progetto. ⛔ Era previsto da `PIANO.md` §1.3 **prima di scrivere la pagina**
e non è mai stato fatto: si scrive adesso, a pagina scritta, ed è tardi — ⭐ ma non troppo, perché
metà di quel che c'è qui dentro ha cambiato il prodotto **oggi stesso**.*

> ## ⭐⭐⭐ Perché questo studio esiste, e chi l'ha chiesto
>
> **L'ha chiesto l'utente, due volte.** La prima il 9 agosto, ed è l'origine di tutto il binario
> web: *«ti spiego perché mi è venuto in mente il discorso WEB: in passato ho avuto modo di usare
> XPRA, e devo dire di essere rimasto molto sorpreso»* (`DECISIONI.md` §1.6).
>
> La seconda **il 14 agosto**, davanti al prodotto che finalmente si usava, e con un difetto in
> mano: *«un piccolo difetto è la cattura del puntatore del mouse… per questa funzionalità puoi
> studiare la soluzione che ha adottato il progetto XPRA»*.
>
> ⇒ ⛔ **E aveva ragione in mezz'ora**: la soluzione di Xpra al puntatore ha smontato una riga delle
> nostre specifiche che ne contraddiceva un'altra. È `LEZIONI.md` §9 punto 0 — *«cercare chi l'ha
> già fatto»* — per la terza volta, e per la terza volta a chiederlo è stato l'utente.

## Come è stato fatto, e che cosa vale

⛔ **Letto nel codice**, non nella documentazione: `Xpra-org/xpra-html5`, i file `html5/js/Client.js`
e `html5/js/Window.js`, più `docs/Usage/Encodings.md` del server. ⇒ Quel che segue è `[R]`, salvo
dove è scritto `[S]`.

⚠ **E il confine si dichiara**: Xpra è su **WebSocket** e noi su **WebTransport**; il suo server è
nato attorno al modello di *damage* di X11 e il nostro parla con un compositore Wayland. ⛔ **Il
trasporto non si eredita, e nemmeno il modello di aggiornamento.** Quel che si eredita è la **forma
delle domande** che il client fa al server — ed è lì che siamo indietro.

⚠ **E una cosa che NON ho potuto misurare**: il `README` non elenca i limiti del client HTML5
(appunti, audio, disposizioni di tastiera, IME, schermo intero). ⇒ `[?]` — non li deduco dal codice
letto a campione.

---

## ⭐⭐⭐ 1. La cosa che vale di più, e ci serviva OGGI: **il primo fotogramma si CHIEDE**

```javascript
request_refresh(wid) {
  this.send([PACKET_TYPES.buffer_refresh, wid, 0, 100,
            {"refresh-now": true, batch: {reset: true}}, {}]);
}
```

⛔⛔ **Il client di Xpra non ASPETTA che lo schermo cambi: dice al server «ridipingi adesso».**

⇒ E questo è **esattamente** il difetto che l'utente ha sentito oggi come *«il tempo fra il login e
la comparsa del desktop è troppo lungo»*: `[M]` 14 agosto 2026, dal registro della sua sessione
vera, fra il canale video acceso e il primo pixel passano **4,10 secondi su 5,21**, e il registro
dice il perché — *«scena ferma: Mutter consegna solo quando qualcosa cambia»*.

| | |
|---|---|
| ⛔ **quel che ci manca** | in `RCP.md` **non esiste un messaggio che chieda l'immagine**. C'è `RICHIEDI_CHIAVE` (§7.1), ma chiede una **chiave** di quel che è già stato catturato: se non arriva niente dal compositore, non produce niente |
| ⚠ **e non si copia alla lettera** | il `buffer_refresh` di Xpra costa poco perché il loro server possiede il modello di damage di X11. ⛔ Su Wayland **non si può ordinare a Mutter di ridipingere**: la leva equivalente è **riavviare il flusso**, che consegna un buffer — `[M]` è così che nasce il nostro fotogramma del `+325 ms` |
| ⇒ ⭐ **quel che si eredita** | **la forma**: il client deve poter dire «dammi lo schermo adesso», e il server deve avere *una* strada per obbedire. Chi la attua è affare nostro |

---

## ⭐⭐ 2. Il cursore: **lo disegna il browser, non la pagina** — e niente cattura

```javascript
function set_cursor_url(url, x, y, w, h) {
  window_element.css("cursor", `url('${url}') ${x} ${y}, auto`);
}
```

⭐ **Il cursore del browser INDOSSA la forma di quello remoto**, punto attivo compreso, da una
`data:image/png;base64`. ⛔ **Nessun elemento disegnato sopra la tela, nessun `cursor: none`.** E la
scala la fa lui quando `devicePixelRatio ≠ 1`, aggiustando anche il punto attivo.

**E la cattura del puntatore?** C'è, ⛔ **ma è un'opzione dell'utente**, non un automatismo:

```javascript
if (window.cursor_lock && win.canvas) { win.canvas.requestPointerLock(); }
```

⇒ un bottone (`#cursor-lock-button`) che si preme. Le coordinate sono **assolute per difetto**; con
la lock accesa passano agli spostamenti (`e.movementX`).

> ### ⛔⛔ E qui lo studio ha smontato una nostra riga con un'altra nostra riga
>
> | dove | che cosa diceva |
> |---|---|
> | `SPECIFICHE.md` §7.1 | *«il mouse fisico arriva da **Pointer Lock**… senza, se ne vedrebbero due»* |
> | `SPECIFICHE.md` §7.5 | *«puntatore **assoluto** — è l'**unico** percorso del puntatore»* |
>
> ⇒ La lock serve a dare gli **spostamenti relativi**. Noi mandiamo **posizioni assolute**. ⛔ Non
> comprava niente, e costava il sequestro del puntatore — che è precisamente quel che l'utente ha
> visto.
> ⭐ **E il motivo per cui era stata messa** — *«altrimenti se ne vedono due»* — si risolve meglio
> nell'altro modo, **con il pezzo che avevamo costruito la mattina stessa e non stavamo usando**:
> `CURSORE_FORMA` (`RCP.md` §7.2).
>
> ✅ **Adottato il 14 agosto 2026**: il cursore del browser veste la forma remota, la freccia
> disegnata si toglie di mezzo nel modo classico, la cattura resta accendibile a mano. Il modo a
> **tocco** tiene il puntatore disegnato, e deve: ⭐ **il dito non ha un cursore da vestire.**

---

## ⭐⭐ 3. La misura della finestra: **il client la dice, il server la esegue**

```javascript
_screen_resized(event) {
  const packet = [PACKET_TYPES.configure_display,
                  {"desktop-size": [this.desktop_width, this.desktop_height],
                   "monitors": this._get_monitors(), …}];
  this.send(packet);
}
```

⭐ **Il client comunica la propria misura e il server RIDIMENSIONA il desktop.** Lo scalamento CSS
locale (`transform: scale(1/scale)`) resta come ripiego, non come strada principale.

⇒ ⛔ **È la nostra `RCP.md` §4.5, «la tela concessa» — e oggi nessuno la mantiene**: `[M]` 14 agosto
(anello A1), un client che chiede **1280×720** ottiene la concessione, ma il palco cattura
**1920×1080** (costante di compilazione) e `rcp` rifiuta **ogni** fotogramma: *145 prodotti, 0
spediti, client nero senza errori*.

⚠ **E il prezzo si vede sullo schermo dell'utente**: il suo è **21:9** (2560×1080), il desktop
remoto **16:9** ⇒ `[M]` dal suo video, **il 36 % dei pixel è banda nera**.

---

## 4. Come dipinge — e qui **noi siamo avanti**

| Xpra HTML5 `[R]` | noi |
|---|---|
| **canvas 2D** con un *offscreen canvas* e `swap_buffers()` | canvas + **WebCodecs** |
| codifiche accettate: `rgb32`, `rgb24`, `jpeg`, `png`, `webp`, `scroll`, `void` | **HEVC/AV1 in hardware** |
| ⛔ `h264` **rifiutato nel percorso principale**: *«h264 decoding is only supported via the decode workers»* | il video è la strada normale, non l'eccezione |

⇒ ⭐ **La loro strada di riferimento è ancora a immagini** (jpeg/png/webp) con il video come caso
speciale in un worker. La nostra nasce sul video. ⚠ E questo spiega la frase dello studio del web:
*«Xpra e noVNC restano sul canvas, e **nessuno dei due dichiara un numero di ritardo**»* (`web.md`).

### ⭐ Una cosa che loro hanno e noi no: la codifica `scroll`

`[S]` *«tries harder to send screen updates using motion vectors»* — invece dei pixel si manda
**«questa zona si è spostata di N»**. È il caso di chi scorre una pagina o un terminale, cioè
**quel che l'utente fa tutto il giorno**.
⚠ **Non è una cosa da prendere adesso**: con HEVC in hardware i vettori di moto li trova il
codificatore, ed è il suo mestiere. ⭐ Ma la riga va tenuta per il giorno in cui la banda stringe:
`SPECIFICHE.md` §8.

---

## 5. La tastiera: **loro mandano posizioni, noi lettere** — e la differenza è voluta

```javascript
[PACKET_TYPES.key_action, wid, keyname, pressed, modifiers, keyval, keystring, keycode, group]
```

⛔ Xpra manda **il codice e il nome del tasto**, più `keyval`, `keystring` e il `group`. ⇒ È la
strada che `SPECIFICHE.md` §7.3 ha scartato **con una ragione scritta**: *«un client con tastiera
americana attaccato a una sessione italiana produrrebbe le lettere sbagliate»*, e su Android una
tastiera **non ha posizioni affatto**.

⭐ **E i tasti morti loro li trattano, noi no** — esplicitamente:

```javascript
const dead = keystring.toLowerCase() === "dead";
if (dead && ((this.last_keycode_pressed !== keycode && !pressed) || pressed)) { … }
```

⇒ ✅ **Ed è coerente con la decisione presa dall'utente oggi** (`DECISIONI.md` §5-bis.6-bis): i
tasti morti e l'IME restano **fuori, dichiarati**. ⚠ Lo studio conferma che il prezzo esiste — Xpra
lo paga con codice apposta — e che **la nostra strada è un'altra scelta, non una dimenticanza**.
`[?]` E l'**IME** non compare nemmeno da loro: chi scrive in cinese dentro un browser, in Xpra,
`[?]` non l'ho trovato servito.

---

## 6. Il ritardo: **lo misurano, e noi no**

```javascript
this.server_ping_latency = 0;
this.client_ping_latency = 0;
PING_FREQUENCY = 5000;   // ms
```

⭐ Un `ping` ogni cinque secondi, e **due** numeri distinti: quanto ci mette il server e quanto il
client. ⇒ ⛔ Noi il ritardo lo misuriamo **al banco** (`DECISIONI.md` §2.6) e **non lo mostriamo mai
all'utente**: quando dice *«mi sembra lento»* non ha un numero da darci, e noi non abbiamo il suo.

⚠ **Non è la stessa misura del nostro tetto di 50 ms** — il loro è il giro di rete, il nostro è
input → vetro. ⭐ Ma la lezione è di forma: **un numero che l'utente vede è un numero che l'utente
può contestare**, ed è più utile di dieci nei nostri file di esiti.

---

## ⛔ Che cosa NON si prende da Xpra

| | perché |
|---|---|
| il **trasporto** (WebSocket) | `DECISIONI.md` §6.4: noi su WebTransport, e quel pezzo non si eredita |
| la **strada a immagini** (jpeg/png/webp con il video in un worker) | è il contrario del nostro punto di partenza: `SPECIFICHE.md` §3.1 vuole 4K a 60 con la codifica in hardware |
| le **posizioni di tasto** come strada principale | §7.3, con la ragione già scritta e già pagata in v1 |
| il modello di **damage di X11** | il nostro compositore è Wayland: la stessa domanda si fa, la risposta la dà un altro meccanismo |

---

## ⭐ Che cosa questo studio ha già cambiato, e che cosa apre

| | stato |
|---|---|
| ⭐ **il cursore vestito dal browser, e niente cattura** | ✅ **fatto il 14 agosto 2026** |
| ⛔ **il client deve poter chiedere l'immagine** («ridipingi adesso») | ⏳ **aperto** — ed è il lavoro sul tempo di apparizione del desktop |
| ⛔ **la tela alla misura del client** | ⏳ **aperto**: `RCP.md` §4.5 esiste e non è mantenuta. Sul 21:9 dell'utente il **36 %** dello schermo è nero |
| ⚠ **un numero di ritardo mostrato all'utente** | 🔸 da valutare: costa poco e cambia il modo in cui i giudizi tornano indietro |
| la codifica `scroll` | 📖 tenuta da parte per quando la banda stringe |

> ### ⭐⭐ E la riga da portarsi via, che non è tecnica
>
> Lo studio era previsto **prima** di scrivere la pagina, ed è stato fatto **dopo**. ⛔ Nel mezzo
> abbiamo scritto una specifica che si contraddiceva (§7.1 contro §7.5), l'abbiamo attuata, e il
> difetto l'ha trovato **l'utente in trenta secondi d'uso** — indicandoci anche dove guardare.
>
> ⇒ ⚠ *Il costo di saltare il punto 0 di `LEZIONI.md` §9 non è il tempo dello studio: è il codice
> scritto nel frattempo, e la fiducia spesa a difenderlo.*
