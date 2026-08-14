# Punto fermo — la sera del 14 agosto 2026, dopo quattro cure fallite

⛔ **Scritto a richiesta dell'utente** (*«credo che sia il caso di raccogliere le idee»*), a
difetto **aperto** e dopo **quattro** correzioni che hanno tolto quattro difetti **veri e
misurati** senza cambiare il sintomo di una virgola.

⚠ Questo documento **supera** `F4-IN-0-sintesi.md` §2 e §7, che restano con la loro data.

---

## 1 · ⭐⭐⭐ IL SINTOMO VERO, che si è saputo solo alle 19

Per due giorni il difetto si è chiamato *«il mouse è inutilizzabile»*. ⛔ Non era una descrizione,
era un giudizio — e sotto c'era un fatto **preciso**, arrivato solo stasera, con le parole
dell'utente:

> *«Per attivare il puntatore del desktop devo premere il tasto sinistro del mouse. Se muovo il
> mouse il puntatore del server non si muove; se invece muovo il mouse **con il tasto sinistro
> premuto** allora il puntatore si muove.»*

⭐ **Questo ha un nome, un numero e quattro anni di età**: **noVNC #1727**, titolo testuale
*«Moving hardware mouse without drag ignored on Chrome Android»*, chiusa `notourbug` il 12
dicembre 2022. `[S]` Confermata da **KasmVNC #222** (aperta), **Kasm workspaces-issues #20** e
⭐ **moonlight-android #573 — che è un'applicazione NATIVA**, senza CSS e senza browser di mezzo.

⛔ **La lezione di metodo, e costa due giorni**: un giudizio (*«è inutilizzabile»*) non è un
sintomo. Nessuna delle otto ipotesi smentite, nessuno dei cinque studi e nessuna delle quattro
cure sarebbe stata necessaria se la prima domanda fosse stata *«che cosa vedi esattamente
succedere?»* invece di *«quanto è lento?»*.

---

## 2 · ⛔⛔ LA CONTRADDIZIONE, ed è il centro di tutto

Due fatti, tutti e due `[M]`, che **non possono essere veri insieme**:

| | |
|---|---|
| **A** | L'utente dice che **senza tasto premuto il puntatore del server non si muove** |
| **B** | Il registro del server registra `[M]` **213 messaggi `PUNTATORE`** in una sessione, con coordinate sensate e istanti unici — e prima della cura ne registrava 403 |

⇒ **Una delle due misure non misura quel che crediamo.** Le sole spiegazioni che reggono:

1. **I 213 erano tutti movimenti a tasto premuto** — cioè l'utente stava trascinando, e la
   sessione non contiene nemmeno un movimento libero. ⚠ Plausibile: stava provando i bottoni del
   pannello. **Non verificato.**
2. **I messaggi arrivano ma l'iniezione non li applica** — il server riceve e non muove nulla.
   ⛔ Contro: il registro mostra `CURSORE_FORMA` che **cambia forma** (punto attivo da `(3,1)` a
   `(13,6)`), il che vuol dire che il cursore del server **si muove sopra cose diverse**.
3. **Il puntatore del server si muove davvero, e l'utente guarda un'immagine ferma** — cioè il
   movimento c'è ma non si **vede**. ⚠ A 8 fotogrammi al secondo con il cursore fuori
   dall'immagine, muovere il puntatore sopra lo sfondo **non cambia un pixel**.

⭐⭐ **La 3 spiegherebbe TUTTO, compreso «col tasto premuto funziona»**: premere e trascinare
**cambia i pixel** (una finestra si sposta, un testo si seleziona, un pulsante si illumina) ⇒
arriva un fotogramma ⇒ si **vede**. Muovere a vuoto non cambia niente ⇒ nessun fotogramma ⇒
**sembra che il mouse non funzioni, mentre funziona.**

⛔ E se è la 3, **tutte e quattro le cure di stasera erano fuori bersaglio per costruzione**, e la
diagnosi originale del punto di ripresa era **giusta** — solo che nessuno l'ha creduta abbastanza
da attaccarla per prima.

---

## 3 · Le quattro cure di stasera, e che cosa hanno lasciato

| # | cura | il difetto era vero? | ha cambiato il sintomo? |
|---|---|---|---|
| 1 | `CURSORE_FORMA` cucita a `forma()` (era ricevuta e buttata) | ✅ sì, `[R]` verificato | ⛔ no |
| 2 | i tre modi del puntatore (`due`/`sistema`/`disegnata`) | — è un banco, non una cura | ⛔ no: **tutti e tre uguali** |
| 3 | una porta sola per i movimenti | ✅ sì: `[M]` **84 % dei movimenti spediti DUE volte**, un pixel di scarto | ⛔ no |
| 4 | la cattura del puntatore rimessa come interruttore | ⚠ da verificare | ⛔ **peggio** |

⭐ **Il numero 3 resta un guadagno vero** anche se non è la cura: metà del traffico di input e
metà delle iniezioni erano sprecate, e la doppia spinta a un pixel di distanza era comunque
sbagliata.

⚠ **E la 4 che peggiora è un dato, non un fallimento**: `[R]` su Android `movementX` è
**ricostruito** da Chromium e i micro-movimenti sono **scartati** — con la cattura accesa il
puntatore si muove per differenze inaffidabili invece che per posizioni assolute. ⇒ Combacia.

---

## 4 · ⭐ Quel che sappiamo con certezza, e va smesso di rimettere in discussione

| `[M]`/`[R]` | |
|---|---|
| `[M]` | l'input **arriva** al server: 213 messaggi, coordinate in campo, istanti unici |
| `[M]` | i fotogrammi **escono**: 541 in 59 s = **8/s**, zero abbandonati, zero rifiutati |
| `[M]` | il tratto «prima di noi» è **9-12 ms**: nessun salto di rete dentro |
| `[M]` | la coda del filo non si è **mai** riempita |
| `[M]` | la conversione delle coordinate **torna al pixel** |
| `[M]` | i tre modi di disegno del puntatore sono **indistinguibili** all'uso ⇒ il disegno non è la causa |
| `[R]` | `cursor: none` **non** toglie i movimenti su Android: il meccanismo ipotizzato non esiste |
| `[S]` | il difetto «niente movimenti senza tasto» è **documentato, specifico di Samsung**, e colpisce anche un'app nativa |

---

## 5 · ⛔ Le due misure che decidono, e NESSUNA delle due tocca il nostro codice

⭐ È il punto in cui questo documento serve a qualcosa: le prossime due domande si rispondono
**senza scrivere una riga**, e ciascuna costa trenta secondi.

### 5.1 La pagina di un terzo, sul DeX, in Chrome

`domeventviewer.com/mouse-event-viewer.html` — e si muove il mouse **senza premere niente**.

`[R]` Quella pagina è stata scaricata e letta: **la parola `cursor` non vi compare nemmeno una
volta**, e non c'è nessun REMOTIX di mezzo.

| esito | che cosa significa |
|---|---|
| **`mousemove` non scatta** | ⛔ il difetto è **interamente fuori dal nostro codice**. Nessuna nostra cura può funzionare, e la strada diventa un'altra (§5.2 o §6) |
| **`mousemove` scatta** | ⛔ allora il difetto è **nostro**, e le quattro cure hanno cercato nel posto sbagliato: si riparte da §2 punto 3 |

### 5.2 La nostra pagina, sul DeX, in un browser diverso

`[S]` Il segnalatore di noVNC #1727, testuale: *«other browsers (**Brave, Kiwi**) do detect all
mouse movements just fine»*.

⇒ Se in Brave il puntatore funziona, **abbiamo un rimedio oggi**, senza scrivere niente: si
dichiara il browser.

---

## 6 · ❓ E la decisione di prodotto che si profila, se la 5.1 dice «non scatta»

⛔ Allora **un client dentro un browser non può funzionare su questo dispositivo**, e non per
colpa nostra. Le strade, tutte dell'utente:

1. **dichiarare il browser** (Brave/Kiwi su Samsung) — costa zero, ed è brutto ma onesto;
2. **un client nativo Android** — è quel che fa RDM, ed è la ragione per cui RDM funziona;
3. **accettare** che sul DeX si usi col tasto premuto — ⛔ da escludere, l'utente ha già
   giudicato;
4. ⭐ **verificare prima l'ipotesi 3 del §2**: se il puntatore del server si muove davvero e
   manca solo il *riscontro visivo*, allora la cura non è sull'input ma sui **fotogrammi** —
   e cambia tutto.

---

## 7 · ⭐⭐ La riga da portarsi via, e non è tecnica

> Per due giorni abbiamo curato **un giudizio** invece di **un sintomo**.

`[M]` Il fatto decisivo — *«si muove solo col tasto premuto»* — è arrivato dopo cinque studi,
quattro cure, otto ipotesi smentite e due giorni di misure. ⛔ Era a una domanda di distanza, e la
domanda era: **«che cosa vedi esattamente succedere?»**

⚠ E la seconda riga, che vale quanto la prima: la contraddizione del §2 era **visibile da ore**
nel registro, e le ho passate sopra quattro volte perché avevo una cura pronta da provare. *Una
cura pronta è il modo più efficace di non guardare una contraddizione.*
