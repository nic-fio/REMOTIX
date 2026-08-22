# Fase 8 — L'anello più corto

> ⚠ **Nel piano questa fase si chiama ancora «La copia zero».** Il titolo è di quando la fase era
> quel solo tratto. ⛔ **Il mandato del 22 agosto 2026 è più largo**, e il documento porta il nome
> del mandato: la copia zero è **un tratto su sei**. Se il piano vada rinominato lo decide l'utente.

*Aperta il 22 agosto 2026. Le fasi 6 e 7 si chiudono senza nessun difetto vero aperto.*

---

## 1 · Che cosa deve produrre

### 1.1 ⭐⭐ La specifica, dettata dall'utente — `SPECIFICHE.md` §3.2-bis

> *«Non pretendo un comportamento allineato al nanosecondo rispetto a una situazione locale, ma che
> gli si avvicini molto. La mia specifica è avere un'esperienza utente **il più vicina possibile a
> una situazione locale, ma non identica**: quello è impossibile.»*

⭐ **E il sintomo l'ha nominato lui, due volte, e la seconda con un numero**:

1. *«quando la finestra di un'app sul desktop remoto viene spostata velocemente, l'effetto visivo è
   **leggermente meno fluido** di quando la stessa azione viene svolta in locale»*;
2. e alla domanda diretta: la distanza fra la freccia del mouse e la finestra che la insegue è
   **«la metà della larghezza della barra del titolo»** ⇒ su una finestra di 720 px, **≈ 360 px**.

⚠ **E ha tarato lui il registro del lavoro**, che è un dato di progetto quanto il resto:
*«è questione di micro-secondi, non di secondi, ecco perché parlavo di ottimizzazione e non di
debug»*. ⇒ ⛔ **Non c'è nessun difetto aperto in questa fase.** C'è un tetto da alzare.

### 1.2 ⭐⭐ E la causa ha un nome: **è un elastico**, non un ritardo

`[R]` Nel modo classico la freccia la muove **il browser**, alla velocità della mano — il cursore di
sistema *e* la freccia che disegniamo noi, sovrapposti, **tutt'e due locali** (`pagina.html`, la
strada di Xpra e la sua ritirata del 14 agosto). La finestra invece la insegue con **tutto** il
ritardo dell'anello. ⇒

```
distacco = velocità della mano × ritardo dell'anello
```

⛔ **Il distacco non è costante: si apre quando la mano accelera, si richiude quando rallenta.** In
locale è **zero a qualunque velocità**. ⇒ La finestra *nuota* rispetto alla mano.

⭐⭐ **È la ragione per cui l'utente ha detto «meno fluido» e non «lento»**, e l'ha detto **prima**
che qualcuno ne conoscesse la causa. ⇒ Chi legge «fluidità» e va a cercare fotogrammi al secondo
cerca nel posto sbagliato: **il piatto è l'elastico**, i fotogrammi sono il contorno.

### 1.3 ⛔ Che cosa NON si può promettere, e va detto adesso

Un anello di rete **non può avere distacco zero**: c'è un fotogramma del compositore, uno della
pagina, e il filo in mezzo. ⇒ **Il distacco si dimezza o meglio, non si toglie.** ⭐ E questa parte
l'ha messa nella specifica l'utente stesso — *«ma non identica: quello è impossibile»* — quindi non
è una scusa preparata: è il confine dichiarato prima di cominciare.

### 1.4 Il conto che apre la fase

| | |
|---|---|
| l'anello **input → vetro**, ultima misura | `[M]` **139,40 ms** (n=326) e **141,60** (n=322), fase 4, 14 agosto — ⚠ **otto giorni e due fasi di cure fa** |
| il tetto di `SPECIFICHE.md` §3.2 (solo il pezzo nostro) | **50 ms**, traguardo **40** |
| che cosa dice l'occhio dell'utente | 360 px ⇒ **106 ms** se guarda alla sua velocità mediana, **57** al p90, **29** ai picchi |
| ⛔ e come è fatto quel numero | **sei tratti da ~25 ms, nessuno dominante** — scritto dalla fase 4 chiudendo: *«nessuna cura singola porta 140 a 50: è lavoro della fase 8»* |

⇒ ⛔⛔ **La copia zero toglie 8,5 ms su ~139: il 6 %.** Da sola **non è la cura di quel che l'utente
vede**. Questa fase deve aprire **tutti e sei** i tratti.

---

## 2 · Il banco — *scritto PRIMA di sviluppare*

### 2.1 ⭐ La scena non si inventa: è quella dell'utente, misurata

`[M]` 22 agosto 2026, dal video girato dall'utente (`~/Video/Screencasts/`, 404 fotogrammi,
registratore di GNOME, 17,5 s), spogliato fotogramma per fotogramma:

| | |
|---|---|
| la finestra | **720 × 433** px (un terminale), barra del titolo larga quanto la finestra |
| velocità del trascinamento | **mediana 3 400 px/s** · p90 **6 300** · **picchi 12 400** |
| intervalli in trascinamento | 350 su 403 |

⛔ **Il banco riproduce QUESTA**, non una scena comoda. Un trascinamento lento non mostra l'elastico,
perché l'elastico è proporzionale alla velocità.

### 2.2 ⛔ Le quattro regole, e tre sono costate sangue

1. ⛔ **Si contano i fotogrammi che la pagina DIPINGE, non i millisecondi di CPU.** La fase 9 di v1
   portò il costo per fotogramma da 41 ms a 6 mentre i fotogrammi consegnati **scendevano** da 29 a
   22,7 (`LEZIONI.md` §6.2). ⛔⛔ E qui morde due volte: la fase 4 ha trovato la coda che cresce —
   server **39,6/s**, pagina **34,7/s**;
2. ⛔ **Si chiede il codificatore per nome e si verifica che abbia obbedito.** Uno che ripiega in CPU
   credendosi in GPU produce due misure sotto la stessa etichetta (`LEZIONI.md` §1.8). ⭐ Il modo
   giusto è già nel prodotto: `componente_e_hardware()` **chiede al componente** quali formati
   accetta — una superficie, non dei pixel. ⚠ E «ha aperto un render node ⇒ rende in GPU» **non
   prova niente** (§1.11);
3. ⛔ **Il prima e il dopo si fanno con lo STESSO banco e la STESSA scena** (`03-b17-ritardo.py`), o
   non si sottraggono. ⚠ E non basta il totale: si affiancano **i tratti**, perché la domanda è
   *«tolto un tratto, gli altri restano dove sono?»*;
4. ⭐⭐ **E il banco misura in DUE unità**: i millisecondi per noi, e **i pixel di distacco per
   l'utente**. Il secondo è l'unico che lui può giudicare senza strumenti, ed è quello in cui ha
   dettato la specifica. `distacco = velocità × ritardo`: si dichiarano tutt'e due, mai uno solo.

### 2.3 ⭐⭐ Il primo numero, e non è un tratto

**`input → vetro`, rimisurato sulla scena vera**, con la parte della rete tolta di mezzo.

⛔ **Finché non c'è, ogni altra misura di questa fase nasce senza un «prima».**

### 2.4 ⭐ La rete si separa, perché non è nostra — ed è già misurata

`[M]` 22 agosto 2026, 400 colpi dal portatile (`wlo1`, **WiFi**) verso il server `192.168.0.2`:

| | andata+ritorno | un verso |
|---|---|---|
| minimo | 1,49 ms | 0,74 |
| **mediana** | **2,85 ms** | 1,43 |
| p90 | 3,94 ms | 1,97 |
| **p99** | **33,60 ms** | 16,80 |
| massimo | 37,60 ms | 18,80 |

⭐ **Il 97 % sotto i 4 ms**: per un WiFi è eccellente, ed è la risposta al rilievo dell'utente
*«c'è pur sempre la latenza di rete in mezzo»*.

⇒ ⛔ **Ma la rete NON spiega il distacco**: 2,85 ms su ~106 è **meno del 3 %**. Il 97 % dell'anello
è nostro. ⭐ *E questa è la buona notizia*: se fosse stato della rete, non ci sarebbe niente da
prendere.

⚠ **Dove il WiFi morde invece davvero**: il **3,2 %** dei colpi schizza a ~35 ms ⇒ **+128 px** di
distacco che si aprono di colpo. `[?]` E nel video dell'utente ci sono **sei buchi in 17,5 s** —
uno ogni tre secondi, **stesso ordine di grandezza**. Non è una prova, è un candidato **e non è
nostro**. ⛔ Il banco li separa, o si cura una cosa che non c'è.

### 2.5 ⭐ Il metro esterno: **xrdp**, e va misurato invece che creduto

*L'utente: «di sicuro siamo avanti a xrdp».* ⛔ `[R]` **Nessuno l'ha mai misurato.** xrdp è studiato
a fondo (`STUDI.md` §12.3 e §gnome) ma **solo come architettura**; un confronto di ritardo non
esiste in nessun documento.

⭐ **E si può fare**, perché xrdp c'è già su questa macchina — `LEZIONI.md` §2.7 lo racconta: fino al
17 agosto la sessione del portatile *era* xrdp (`Xorg :10`, `got RFX capture`), ed è l'anello che
per due giorni nessuno aveva contato.

⇒ Lo stesso trascinamento, la stessa finestra, la stessa unità: **quanti pixel di distacco fa xrdp?**
⭐ È l'unico numero di questa fase che l'utente può giudicare **guardando**, senza fidarsi di me.

#### ⭐⭐ FATTO, dall'utente, il 22 agosto 2026 — e REMOTIX è avanti

> *«Confermo: siamo avanti, e di non poco. Non posso darti i numeri ma già si vede molto bene
> ad occhio.»*

⚠ **È un giudizio, non una misura**, e sta scritto così di proposito: l'utente ha dichiarato lui
stesso di non avere numeri. ⛔ Non si citi come `[M]`.

⭐ **E risponde di rimbalzo alla domanda che gli era stata posta e che non ha avuto bisogno di
rispondere**: *«su xrdp la freccia ti risponde istantanea o un filo indietro?»* — la domanda serviva
a sapere se xrdp disegna il puntatore in locale (come noi) o dentro l'immagine. ⇒ **Se lo disegnasse
dentro l'immagine il suo distacco sarebbe ZERO per costruzione, e avrebbe vinto lui.** Essendo
indietro, lo disegna in locale: **il confronto era alla pari.**

⛔⛔ **E adesso la trappola, perché questo risultato è il tipo di cosa che ferma le
ottimizzazioni.** «Siamo avanti al concorrente» **non è la specifica**. La specifica di §1.1 è *«il
più vicino possibile a una situazione locale»*, e il termine di paragone che l'utente ha nominato
per primo è **il locale**, non xrdp. ⇒ Il mandato resta quello che ha dato aprendo: *«se possiamo
limare ancora qualcosa allora ok»*.

### 2.6 ⛔ Lo strumento del 22 agosto NON basta, e va detto perché

Il registratore di GNOME gira a **30 fotogrammi al secondo** e **non riprende il puntatore**
(cercato a macchina su tutti e 404 i fotogrammi: gli unici oggetti piccoli in movimento sono
l'indicatore di registrazione e il cursore di testo del terminale).

⇒ ⛔ **Due difetti dello strumento, non del prodotto**:
- **satura**: il fenomeno sta fra 30 e 60 fotogrammi al secondo, e un tetto a 30 non li distingue —
  la forma di `LEZIONI.md` §1.21, *uno strumento che si rompe sotto carico mente quando serve*;
- **perde il puntatore**, che è l'unica cosa da cui si legge il distacco. ⭐ *E l'ironia è
  istruttiva*: lo perde per lo **stesso meccanismo** che usiamo noi — il cursore preso come
  metadato, fuori dai pixel.

⭐ **Quel che il video ha comunque dato, ed è molto**: la scena vera di §2.1, e i sei buchi di §2.4.

---

## 3 · Che cosa è stato sviluppato

*(vuoto — la fase si apre oggi)*

## 4 · Le misure

*(si riempie strada facendo. ⛔ La prima riga è §2.3, e finché non c'è le altre non hanno un «prima».)*

## 5 · ⛔ Che cosa NON ha funzionato

*(vuoto)*

## 6 · Le decisioni prodotte

### 6.1 ⛔ CHIUSA PRIMA DI APRIRSI: l'anello in parallelo — 22 agosto 2026

Mettere l'anello in pipeline — codificare l'N mentre si cattura l'N+1 — alzerebbe i fotogrammi al
secondo pagandoli con **un fotogramma di ritardo in più**.

⛔ **Su questa scena è il peggiore degli scambi**: ai picchi dell'utente (12 400 px/s) un fotogramma
in più vale **da 200 a 350 pixel** di distacco — **mezza finestra**. ⇒ Comprerebbe il contorno
vendendo il piatto.

⭐⭐ **E non serviva una misura nuova per saperlo**: `SPECIFICHE.md` §3.2 lo vietava già —
*«ogni memoria intermedia compra fluidità e vende risposta»*, *«una scelta che alza il ritmo
peggiorando il ritardo non si fa»*. ⇒ La riga era scritta **prima** che il difetto avesse un nome, e
questa fase è la prova che serviva.

### 6.2 ⏳ Sul tavolo, NON decisa: ritardare la freccia per chiudere l'elastico

Se la freccia venisse disegnata **in ritardo**, alla posizione che il fotogramma sta portando invece
che a quella della mano, il distacco **sparirebbe** — freccia e finestra si muoverebbero insieme.

⛔ **Il prezzo è il puntatore che risponde in ritardo**, e va contro una decisione già presa: la
freccia è locale **apposta**, perché sul DeX a 1,1 fotogrammi al secondo *«è come se si perdessero
gli input»* — non se ne perdeva nessuno, non si **vedeva** che arrivavano (`pagina.html`, 14 agosto).

⇒ 🔸 **È una decisione di prodotto, e la prende l'utente — con i numeri in mano, non adesso.**

---

## 7 · Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **a quale velocità guarda l'utente** | 360 px danno 106 ms alla mediana, 57 al p90, 29 ai picchi. ⛔ **Non è deducibile**: si misura l'anello, non si chiede a lui |
| ⏳ **i ~16 ms non spiegati** | dentro `cattura → primo byte` (30,37 ms) stanno 5,6 di conversione, 2,9 di caricamento, 5,3 di codifica — e **~16 che nessuno dei tre spiega**. ⚠ Un margine, non un difetto |
| ⏳ **gli altri cinque tratti** | la fase 4 dice «sei da ~25 ms». ⛔ **Questo documento ne ha nominato uno solo.** Gli altri cinque vanno aperti |
| ⏳ **i sei buchi** | del WiFi (§2.4) o nostri? Il banco li separa |
| `[?]` **il codificatore e la sua scheda** | VA-API sceglie da sé; se cercasse la discreta — chiusa da udev — ripiegherebbe in CPU **in silenzio** (`DECISIONI.md` §4.6-ter) |
| `[?]` **`EncSliceLP` e i sotto-livelli temporali** | senza, ogni fotogramma abbandonato costa una chiave intera (`RCP.md` §5.2) |
| `[?]` **quanto pesa una chiave 8K** | contro il tetto dei 16 MiB di `RCP.md` |
| ⛔ **il puntatore doppio** | oggi se ne disegnano **due sovrapposti**, e il codice stesso lo chiama *«il DIFETTO»*. Fuori mandato qui, ma è nella stessa riga di codice che questa fase tocca |

### 7.1 ⭐ Le due strade già provate — non si rifanno

- `createImageBitmap`: **3,8 ms** mediani per fotogramma, l'8 % del tetto di 50, e già **nove volte
  meglio** del disegno 2D di prima;
- ⛔ **`?video=worker` funziona e NON rende**: abbassa il tetto del **19 %**. Chi apre questa fase
  non la rifaccia.

### 7.2 ⛔ Che cosa NON è di questa fase

i **10 bit veri** → il muro è nella cattura, non nella codifica (Mutter dà BGRx da ogni strada) · la
**rete stretta** e il **punto di lavoro fra qualità e banda** → fase 9 · la **qualità di
`EncSliceLP` contro l'entrypoint pieno** → fase 9 · il **ridimensionamento dinamico** → fuori dal
progetto · il **multi-tenant** → fase 10, ⚠ ma aspetta il numero vero che esce da qui.

---

## 8 · Il giudizio dell'utente

### 8.1 ⭐ L'apertura — 22 agosto 2026

> *«Di sicuro siamo avanti a xrdp, ma se possiamo limare ancora qualcosa allora ok.»*

⇒ ⭐ **Il via libera, e il metro**: non «raggiungere un numero», ma **limare**.

### 8.2 ⭐⭐ E il confronto con xrdp l'ha fatto lui, subito — 22 agosto 2026

*Si è collegato dal notebook al tablet con l'altro utente e ha rifatto la stessa prova.*

> *«Confermo: siamo avanti, e di non poco. Non posso darti i numeri ma già si vede molto bene
> ad occhio.»*

⚠ Giudizio, **non misura** — e §2.5 spiega perché vale lo stesso, e perché **non chiude la fase**.

*(il resto si riempie quando avrà qualcosa da guardare)*
