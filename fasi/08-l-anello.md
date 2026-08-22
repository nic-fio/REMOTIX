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

⭐⭐ **E xrdp girava a MENO di ~2000 px di larghezza**, contro i **2560** nostri — precisato
dall'utente subito dopo. ⇒ Due effetti, e vanno dichiarati tutt'e due perché tirano in versi opposti:

| | |
|---|---|
| ⭐ **a favore nostro, e pesa** | xrdp aveva **al più il 78 % dei nostri pixel** da catturare, codificare e spedire — meno lavoro per fotogramma, quindi un anello che *dovrebbe* essere più corto. **Ed era comunque indietro.** ⇒ Il divario vero è **più largo** di quello che si è visto |
| ⚠ **contro, ed è perché l'unità era quella giusta** | il distacco è `velocità × ritardo`, e su uno schermo più piccolo la stessa mano copre **meno pixel al secondo** ⇒ il distacco di xrdp in *pixel* sarebbe uscito più piccolo comunque. ⭐ **Ma il giudizio era in frazioni di barra del titolo**, che scala con lo schermo: l'unità scelta ha normalizzato da sé la differenza di risoluzione |

⇒ ⭐ **L'unità dell'utente ha retto a una variabile che nessuno aveva previsto.** È la ragione per
cui §2.2 punto 4 la pretende: i pixel si confrontano solo a schermo uguale, le frazioni di barra no.

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

## 4-F2 · ⭐⭐⭐ AGENTE F2 — **l'occhio dell'utente aveva ragione**, e i due banchi non litigavano · *22 agosto 2026, sera*

> ### ⭐⭐⭐ LO SCARTO È SPIEGATO **SENZA** USARE «L'UTENTE SI SARÀ SBAGLIATO»
>
> Tre candidate abbattute con la misura: ⛔ **i pixel** (`[M]` **0,301 · 0,294 · 0,301 barre** a
> 1560 · 1920 · 2560 — **il doppio dei pixel, ZERO pendenza**), ⛔ **la mano** (3 169-3 358 px/s
> contro 3 400: normalizzata non muove niente), ⛔ **la barra** (`barra_px = 720` in tutti e quindici
> i verbali: è la finestra dell'utente).
>
> ⭐ Restava la quarta, quella che dà sempre ragione a chi misura. **Non è servita:**
>
> ```
> 70,3 [M]  +  11,6 [M]  +  [?] 4-12  +  [?] 16-40  =  102-134 ms  ⇒  0,48-0,63 barre
>              ↑ la coda eventi del browser: nel banco vale 0,165 ms
>                perché la mano è SINTETICA
> ```
>
> ⇒ ⭐⭐ **L'utente ne riferiva 0,50: il bordo basso dell'intervallo.** ⛔ **Il banco non sbagliava:
> guardava un pezzo più corto dell'anello vero**, e il pezzo mancante era invisibile **proprio
> perché la sua mano è finta**. Una mano sintetica non fa la fila nella coda eventi del browser.
>
> ### ⭐⭐ E i due banchi non litigavano: **misurano due grandezze diverse**
>
> | | | |
> |---|---|---|
> | `04-b30` | ⭐ **la RISPOSTA** | contiene **l'attesa** che un fotogramma venga prodotto |
> | `08-b67` | ⭐ **la VECCHIAIA** di quel che è sullo schermo | non la contiene |
>
> `[M]` Stessa macchina, stesso giorno: tratto 1a **11,55** contro **0,165 ms**; tratto 3 **28,74**
> contro **6,3-10,4** ⇒ **−30…−34 ms strutturali**, residuo `[?]` 6-10.
>
> ⛔ **E la moltiplicazione di §4-A tornava per COMPENSAZIONE**: accostava il ritardo di una
> grandezza alla velocità dell'altra, e due errori si annullavano. 📖 `LEZIONI.md` §1.28.
>
> ### ⛔⛔ E DUE COSE CHE IL DIRETTORE AVEVA SCRITTO SONO SMENTITE
>
> 1. ⛔ **«I 17,48 ms erano contesa»** — `[M]` sul palco di F2, **a macchina scarica**, il tratto 9
>    misura **17,64 ms** (n=241); **a macchina carica 15,37**. ⇒ **La contesa lo ABBASSAVA.** Il
>    numero non era contesa: era **un'attesa** che l'altro banco non contiene (vedi sopra). ⚠ La
>    contesa **esiste** ed è misurata (§4-F1, 8-17 ms sullo stesso anello) — **ma non era lei**;
> 2. ⛔ **«Tutta la prima ondata è contaminata»** — `[M]` **falso**: sul banco del distacco il carico
>    non gonfia niente (**70,7** carico contro **70,3** scarico). Crederlo farebbe **buttare misure
>    buone**.
>
> ### ⭐ E lo stato alla risoluzione VERA dell'utente
>
> `[M]` 2560×1080, portatile scarico (carico 0,33, 0 Xvfb altrui), n=905/926, tutti i controlli
> verdi, 13 guasti su 13 ricertificati: **70,5 · 70,0 ms · 214 · 213 px · 0,30 barre**.
> Il **locale alla stessa tela**: **30,05 ms = 0,142 barre**, n=254 (B ne aveva 29). ⇒ **2,3 ×**.
>
> ### ⭐⭐⭐ E una previsione FALSIFICABILE, che tocca all'utente
>
> `[M]` Dopo la copia zero il banco dà **0,16 barre** ⇒ sullo schermo dell'utente la previsione è
> **0,31-0,46 barre**. ⛔ **Se l'utente dicesse ancora «metà barra», questa spiegazione è sbagliata**
> — e sta scritto qui perché si possa dirlo.
>
> ### ⚠ E i sei buchi non ricompaiono
> `[M]` **3 in 244,6 s** a 2560 (uno ogni **82 s**) contro **uno ogni 2,9 s** dell'utente. ⇒ Resta la
> **rete**: p99 **27,9-35,4 ms** ⇒ **+95…+120 px** che si aprono di colpo.

> ### ⭐⭐⭐ TRE COSE, E LA PRIMA È CHE **L'OCCHIO DELL'UTENTE AVEVA RAGIONE**
>
> **1. `[M]` Alla tela vera dell'utente (2560×1080), a portatile scarico, il banco dà 0,30 barre —
> e la risoluzione NON c'entra niente.** Girato a tre tele con **due volte** i pixel in mezzo, il
> numero non si muove: **0,300 · 0,294 · 0,301 barre** a 1560×888, 1920×1080 e 2560×1080. ⛔ Per
> arrivare da 0,28 a 0,50 servirebbe **+79 %**: la risoluzione ne dà **+0 %**.
>
> **2. ⭐⭐ Lo scarto sta tutto in quel che il banco NON misura**, e adesso è un conto:
>
> | | ms | ⇒ barre a 3 400 px/s |
> |---|---|---|
> | `[M]` il banco, 2560×1080, macchina scarica | **70,0 – 70,5** | **0,30** |
> | `[M]` + la coda degli eventi del browser (tratto 1a, mouse **vero**) | + 11,6 | + 0,05 |
> | `[?]` + il pezzo cieco in **ingresso** (mano → `event.timeStamp`) | + 4 … 12 | + 0,02 … 0,06 |
> | `[?]` + il pezzo cieco in **uscita** (disegno finito → pixel acceso) | + 16 … 40 | + 0,08 … 0,19 |
> | ⇒ **quel che l'utente guarda** | **102 … 134 ms** | ⭐⭐ **0,48 … 0,63 barre** |
>
> ⇒ ⭐⭐ **0,50 sta dentro l'intervallo che il banco stesso dichiara, sul bordo basso.** Non c'era
> nessuno scarto: c'erano **due grandezze diverse chiamate con lo stesso nome**. ⛔ E la candidata
> «l'utente ha stimato male» si chiude **senza usarla**: il suo occhio è stato lo strumento più
> preciso dei tre di questa fase.
>
> **3. ⛔⛔ E i due banchi nostri non litigano: misurano due cose diverse, e la differenza è
> misurata, non supposta.** A misura la **RISPOSTA** («ho mosso, quando lo vedo?»), B/F2 misura la
> **VECCHIAIA** di quel che è sullo schermo durante un trascinamento continuo. `[M]` I due tratti
> che li separano valgono **−30 … −34 ms**, e sono stati presi **oggi, sulla stessa macchina,
> nella stessa ora**.
>
> ⚠ **E una smentita che riguarda una correzione già in corso**: `[M]` sul mio palco, a portatile
> **scarico**, il tratto 9 di A misura **17,64 ms** — cioè **esattamente i 17,5 ms** che F3 dà per
> gonfiati dalla contesa. ⇒ ⛔ Sul mio banco **quel numero non è contesa**, e la correzione di
> −15 ms va rimessa in discussione prima di entrare in un documento.

*Da inserire in `fasi/08-l-anello.md` §4 (misure), §5 (non ha funzionato) e §7 (resta `[?]`).
⛔ Non è stata toccata una riga di `src/`, e nemmeno una dei banchi.*

---

## F2.0 · Le risorse, il palco e ⛔ **il carico, accanto a ogni numero**

⭐ **Mie, tutte separate**: porta **7765** (prodotto) · **7766** (ponte) · **7767** (ancora) ·
utente **`provaf8`** (uid 1044, nel gruppo `render`: verificato) · albero
`/media/REMOTIX/src/08-f-src` · lavoro `/media/REMOTIX/tmp/08-f` (ban-file e socket propri) ·
scena `/dev/shm/remotix-08-f` · schermo Xvfb `:92` (e `:94` per il banco di A).
⛔ **7730 e 7731 — i due server dell'utente — non sono mai state toccate**, e la 7765 è stata
**contata libera con `ss -tulnp` prima** di prenderla.

**Palco**: server `192.168.0.2`, sessione GNOME headless, monitor virtuale letto **dal
compositore** (`«Meta-0» 2560x1080 @ 60.000 Hz`), scena `04-b30-scena.c` a schermo intero,
formato **BGRx 8 bit**. Client: Chrome su Xvfb **sul portatile**, strada **`bitmaprenderer`**
(quella vera), rete **WiFi** (`wlo1`) in mezzo. ⛔ Prestazioni **su Intel UHD 730 integrata**.

⛔⛔ **IL CARICO DEL PORTATILE VA ACCANTO AL NUMERO** — `LEZIONI.md` §2.0. ⚠ Il portatile ha
**4 nuclei** ed è il **CLIENT**: è lì che gli agenti si pestano. Il server ne ha 20 e ha avuto
`load 0,08` tutto il giorno.

| | `load` (1 min) | Xvfb altrui | Chrome altrui |
|---|---|---|---|
| ⛔ **prima ondata** (i giri di F2.1 «carico») | **2,4 – 3,2** | 1 – 5 | fino a 56 |
| ⭐ **finestra tranquilla** (i giri «PULITO») | **0,27 – 0,84** prima del giro | **0** | **0** |

⇒ ⭐⭐ **E il risultato più utile di tutta la giornata sul carico è questo**: `[M]` a 2560×1080 il
banco dell'elastico dà **70,5 · 71,2 · 71,7 · 70,7 · 70,7** a macchina carica e **70,5 · 70,0** a
macchina scarica. ⛔ **La contesa NON gonfia questo banco.** Quel che gonfiava, se gonfiava, era
un altro strumento — e va detto, perché «tutti i numeri della prima ondata sono contaminati» è
falso e farebbe buttare misure buone.

⭐⭐ **E la copia zero NON era accesa in nessuno dei miei giri**, verificato in due modi:
`[M]` il mio albero è antecedente alla fusione (`src/codificatore.c` ha **2** occorrenze di
«copia zero», quello fuso ne ha **10**), e `[M]` il registro del mio server ha **0** righe che
nominino copia zero / DMA-BUF / ripiego. ⇒ ⭐ **I miei numeri sono sul codice ESATTO che l'utente
guardava quando ha detto «mezza barra».** È la condizione perché la spiegazione valga.

---

## F2.1 · ⭐⭐ IL NUMERO ALLA TELA DELL'UTENTE — `[M]` 2560×1080, macchina scarica

| | giro q1 | giro q3 |
|---|---|---|
| campioni | **905** su 941 fotogrammi | **926** su 963 |
| ⏱ **ritardo, confine SCOMODO** (input → **disegno finito**) | **70,5 ms** | **70,0** |
| ⏱ ritardo, confine COMODO (fotogramma *arrivato*, §6.2) | 37,6 | 36,9 |
| ⭐ quanto si regala il comodo | 32,9 | 33,1 |
| 📏 **distacco** | **214 px** (p95 600, max 1 149) | **213** (p95 600) |
| ⭐ **distacco in barre del titolo** | **0,30** | **0,30** |
| 🖐 la mano | 3 358 px/s | 3 356 |
| 🌐 rete misurata **nello stesso giro** | 2,8 ms (4,0 %) | 2,8 (4,0 %) |
| ⭐ **il pezzo NOSTRO** | **67,7 ms** | **67,2** |
| carico prima del giro | load 0,33 · 0 Xvfb altrui | 0,84 · 0 |

⇒ ⭐ Tutti i controlli verdi (Q0…Q13), **13 guasti su 13** alla ricertificazione fatta oggi sul
mio portatile prima di cominciare.

### ⭐⭐ Il termine di paragone LOCALE, rifatto alla stessa tela — con un denominatore vero

| | n | la scena | il compositore | ⭐⭐ **l'anello locale** | ⇒ barre |
|---|---|---|---|---|---|
| `[M]` **2560×1080**, oggi | **254** | 10,43 ms | 20,52 | **30,05 ms** (p95 32,5) | **0,142** |
| `[M]` 1560×888, agente B, 22 ago | 29 | 7,29 | 20,01 | 27,58 | 0,130 |

⇒ ⭐ **Il pavimento si muove poco** (+9 % raddoppiando i pixel, con n che passa da 29 a 254), e il
rapporto REMOTIX/locale resta **2,3×** — praticamente il 2,4× che B aveva trovato a 1560. ⛔ Il
mandato della fase non cambia con la risoluzione: restano **~40 ms** da prendere sopra il
compositore.

⛔ **Un difetto vero, trovato e curato**: la copia di `08-b67-locale.py` **sulla macchina di prova
era VECCHIA** (md5 `fe9ebcb…` contro `78ffc5a…` del deposito), cioè quella di *prima* della cura
del setaccio unico che l'agente B descrive al suo §6 punto 4. `[M]` Con quella copia il primo
giro ha detto **anello 13,51 ms con parti 10,92 + 20,68** — un totale **più piccolo delle sue
parti**, che è impossibile: lo stesso rosso che B aveva già pagato, ricomparso perché la cura non
era mai arrivata sulla macchina dove il banco gira. ⇒ **Una cura vale solo dove il banco gira.**

---

## F2.2 · ⭐⭐ LO SCARTO, CANDIDATA PER CANDIDATA — tre cadono con la misura, la quarta non serve

### 1. ⛔⛔ **I PIXEL: refutata.** A macchina scarica il ritardo è **piatto**

`[M]` Stesso banco, stessa scena, stesso palco, stessa ora, **macchina scarica**:

| tela | Mpx | passo (byte) | `[M]` ritardo | distacco | barre | ⭐ **barre @ 3 400 px/s** |
|---|---|---|---|---|---|---|
| **1560 × 888** | 1,39 | 6 240 (**%64 = 32**) | **70,1 · 70,1 ms** | 203 · 201 px | 0,28 | **0,301 · 0,300** |
| **1920 × 1080** | 2,07 | 7 680 (%64 = 0) | **69,4 ms** | 201 px | 0,28 | **0,294** |
| **2560 × 1080** ⭐ *(l'utente)* | 2,76 | 10 240 (%64 = 0) | **70,5 · 70,0 ms** | 214 · 213 px | 0,30 | **0,301 · 0,300** |

⇒ ⛔⛔ **Raddoppiando i pixel il numero non si muove di un centesimo di barra.** Nessuno dei due
confini scala coi pixel, né lo scomodo né il comodo (35,4 – 37,6 ms su tutte e tre le tele).
⭐ È la risposta diretta alla `[?]` che l'agente A aveva lasciato aperta («quanto dei 41 ms è
prodotto e quanto sono pixel in meno»): **dei pixel non è quasi niente**.

⚠ **E il contrario si dichiara**: nella **prima ondata**, a macchina carica, gli stessi giri
davano una pendenza apparente (0,266 a 1560 contro 0,308 a 2560, **+16 %**). ⛔ **Quella pendenza
non c'è**: era dispersione fra sessioni, e a macchina scarica sparisce. ⇒ Un banco che avesse
girato una volta sola per tela avrebbe consegnato una legge dei pixel **che non esiste**.

⭐ **E la trappola del passo di F4 è stata guardata**: la sola tela con passo non multiplo di 64 è
la **1560×888** — ⛔ **ed è quella che va uguale alle altre**. Se il passo storto costasse
qualcosa, si vedrebbe lì. E su tutte le tele la marca si legge `[M]` **al 100 %** (Q3) con
**contrasto 1,0** e **scorrimento [0,0]**, e le coordinate si ritrovano **esatte al 100 %** (Q5).
⚠ Nota di metodo, perché F4 avverte giustamente: **`08-b67` non guarda nessuna media**. Il lettore
è quello certificato di `03-marca.py` (CRC, sync, contrasto), il controllo JS-contro-numpy è un
**massimo per cella** (`0,000 su 255` in ogni giro) e Q5 pretende **le coordinate identiche**, non
vicine. ⇒ Un'immagine inclinata farebbe saltare il CRC e il banco direbbe «0 eco letti», non un
verde.

### 2. ⛔ **LA VELOCITÀ DELLA MANO: refutata**, e togliendola il numero non si muove

`[M]` La mano sintetica ha fatto **3 169 … 3 358 px/s** mediani nei giri puliti, contro i **3 400**
dell'utente: **−7 % … −1 %**, dentro la dispersione della sua stessa mano (p90/mediana = 1,85).
⭐ E il conto si può togliere del tutto: normalizzando ogni giro a **3 400 px/s esatti** si ottiene
la colonna «barre @ 3 400» della tabella qui sopra — **0,294 … 0,301**, cioè la stessa cosa.

⭐ **E c'è un fatto nuovo che nessuno cercava**, e va nel verso scomodo per noi: il distacco
**misurato nei pixel** è `[M]` **0,90 – 0,94 volte** il prodotto `velocità × ritardo`, su tutti e
quindici i giri. `[R]` La causa è la traiettoria del banco: il serpentino **rimbalza** a ogni riga,
e attorno a un rimbalzo l'elastico si richiude perché la mano inverte. ⇒ Su un trascinamento
**vero**, che non inverte, il fattore è **1,0**: ⛔ **il banco misura un elastico un po' più corto
di quello dell'utente**, non più lungo.

### 3. ⛔⛔ **LA BARRA DEL TITOLO: la più stupida e la più letale — controllata per prima, ed è a posto**

`[M]` Letto nel verbale di **tutti e quindici i giri**: `barra_px = 720`, che è esattamente la
larghezza della finestra dell'utente misurata sul suo video
(`SCENA_UTENTE.finestra = [720, 433]`, «barra del titolo larga quanto la finestra»).
⇒ **Il banco divide per la barra DELL'UTENTE**, non per una sua, e non c'è nessun fattore 1,8
nascosto lì dentro.

⭐ **E adesso l'unità è pulita anche nel secondo senso**: l'agente B girava a **1560 px** di
larghezza dividendo per una barra di **720** misurata su uno schermo da **2560** — due schermi
diversi sotto la stessa frazione. Alla tela dell'utente quel dubbio **non esiste più**: mano,
barra e schermo sono i suoi tre. ⛔ E il numero **non cambia**: 0,30 di qua e 0,30 di là.

### 4. ⭐⭐ **LA STIMA A OCCHIO: NON serve, e non si conclude per esclusione**

⛔ Il mandato diceva: *«non si conclude questo per esclusione»*. **Non ce n'è stato bisogno**,
perché il conto chiude da solo. Quel che il banco misura è **`t0` nella pagina → disegno finito**;
quel che l'utente guarda ha **tre pezzi in più**:

| | quanto | come si sa |
|---|---|---|
| ⭐ **la coda degli eventi del browser** (tratto 1a) | `[M]` **11,55 ms** mediani (p75 21,4) | misurato **oggi, sulla stessa macchina, a portatile scarico**, dal banco di A. ⛔ Nel banco dell'elastico vale `[M]` **0,165 ms**, perché la mano è **sintetica**: l'evento nasce già dentro il gestore, e la coda del browser non c'è |
| `[?]` **il pezzo cieco in ingresso** | 4 – 12 ms | mano → `event.timeStamp`: dispositivo, nucleo e compositore **del client**. Nessuna API della pagina lo vede |
| `[?]` **il pezzo cieco in uscita** | 16 – 40 ms | disegno finito → pixel acceso, `STUDI.md` §web §6.2. ⛔ E per l'utente **ci sono davvero**: sul suo schermo un compositore c'è |

⇒ `[M]` 70,3 + `[M]` 11,6 + `[?]` 4-12 + `[?]` 16-40 = **102 – 134 ms** ⇒ a 3 400 px/s, col
fattore **1,0** di un trascinamento che non inverte, **347 – 456 px** ⇒ ⭐⭐ **0,48 – 0,63 barre**.

⇒ ⭐⭐ **L'utente ne riferisce 0,50: il bordo basso dell'intervallo che il banco stesso dichiara.**
⛔ Non era un occhio impreciso: era un banco che si ferma **tre pezzi prima del vetro** e chiama
«l'anello» quel che è la parte in mezzo.

⚠ **E il pezzo che regge meno si dichiara**: anche mettendo il tratto 1a a **zero**, l'intervallo
resta **0,43 – 0,58 barre** e **0,50 ci sta lo stesso**. La conclusione non dipende da quel numero.

### 5. ⛔ **La quinta candidata, il CARICO: guardata, e su questo banco non morde**

Vedi F2.0: `[M]` 70,7 ms mediani a macchina carica, 70,3 a macchina scarica. ⇒ ⛔ **Il banco
`08-b67` è insensibile alla contesa**, e i suoi numeri della prima ondata **non vanno buttati**.
`[R]` La ragione plausibile è che il grosso dell'anello sta **sul server** (che era scarico) e
che il pezzo di client è dominato da attese, non da CPU. ⚠ È una spiegazione, non una misura.

---

## F2.3 · ⭐⭐ I DUE BANCHI NOSTRI — non è un disaccordo: sono **due grandezze**

⛔ Il fatto duro del mandato: A dice **99,07 ms** (⇒ 0,47 barre), B dice **69,8** (⇒ 0,28).
Rifatti **oggi, sulla stessa macchina, nella stessa ora, sullo stesso palco, a portatile scarico**:

| | banco | tela | strada | `[M]` mediana | n | carico |
|---|---|---|---|---|---|---|
| **A** | `04-b30-anello-input.py` | 1460×888 | `?tela=2d` | **109,9 ms** | 241 | load 1,27 · 0 altrui |
| **A** (macchina carica) | idem | 1460×888 | `?tela=2d` | 111,2 | 198 | load ~2,5 |
| **F2** | `08-b67-elastico.py` | 1560×888 | `bitmaprenderer` | **70,1 ms** | 777 · 791 | load 0,66 · 0 altrui |

⇒ ⛔ **Il disaccordo si riproduce, e a macchina scarica è persino più largo (40 ms).** E la tela di
A è **più piccola**, quindi i pixel tirano nel verso sbagliato. ⭐⭐ **I due pezzi che lo spiegano
sono misurati oggi, e sono tutti e due nella scomposizione di A:**

| | A, oggi, pulito | F2, oggi, pulito | Δ |
|---|---|---|---|
| **tratto 1a** — `event.timeStamp` → i byte escono | `[M]` **11,55 ms** | `[M]` **0,165 ms** (`riassunto.tratto_1a_ms`) | **−11,4** |
| **tratto 3** — la scena riceve → la scena **DISEGNA** | `[M]` **28,74 ms** | `[M]` **6,3 – 10,4 ms** (banco locale, stesso campo `eco_us → eco_disegnato_us`) | **−18,3 … −22,4** |
| | | ⇒ **somma** | **−30 … −34 ms** |
| | | ⇒ **residuo non spiegato** | `[?]` **6 – 10 ms** (strada 2D contro `bitmaprenderer`, e 100 px di tela) |

⇒ ⭐⭐ **I due banchi misurano due cose diverse, e tutte e due sono vere:**

- **A misura la RISPOSTA**: da *quell'* evento al primo fotogramma che lo mostra. Paga la coda del
  browser **e** l'attesa intera del quadro della scena. È il numero giusto per *«ho cliccato,
  quando lo vedo?»*.
- ⭐ **F2/B misura la VECCHIAIA di quel che è sullo schermo** durante un trascinamento continuo:
  `04-b30-scena.c` dipinge **l'ULTIMO input ricevuto**, quindi l'eco nomina sempre l'evento **più
  fresco** e l'attesa del quadro **non la paga**. ⛔ **Ed è questa la grandezza che governa il
  distacco**: la finestra che l'utente vede sta dove la mano era `vecchiaia` fa, non dove era
  quando è partito un evento particolare.

⇒ ⛔ **Nessuno dei due numeri va chiamato «l'anello di REMOTIX» senza dire quale dei due è.**
`fasi/08-l-anello.md` §1.4 li mette in colonna come se fossero la stessa cosa: **non lo sono**, e
la differenza è `[M]` **~30-34 ms**, cioè il 30 % del più grande.

⚠ **E la moltiplicazione di §4-A va corretta**: `99,07 × 3 400 = 337 px = 0,47 barre` accostava un
numero di **risposta** a un distacco di **vecchiaia**. ⭐ Che desse quasi il numero giusto è una
**coincidenza**: i ~30 ms di troppo del confine di A compensavano i tre pezzi mancanti in coda.
⛔ Due errori in versi opposti non fanno una prova, e §4-A la chiamava *«la prova che l'elastico è
il modello giusto»*. **Il modello è giusto lo stesso** — lo dimostrano i quindici giri di qui —
ma non per quella ragione.

### ⛔⛔ E una smentita che riguarda una correzione già in corso: **il tratto 9 di A non è contesa**

`[M]` F3 dà il tratto 9 di A (17,58 ms) per gonfiato dalla contesa e lo rimisura a **0,39 – 2,80 ms**.
⛔ **Sul mio palco, a portatile scarico (load 0,37 all'inizio, 0 Xvfb e 0 Chrome altrui), il
tratto 9 misura 17,64 ms** (n=241, min 10,98, p25 16,2, p75 19,x) — cioè **esattamente il numero
di A**. E a macchina carica misurava **15,37**: ⛔ **la contesa lo abbassava, non lo alzava.**

⇒ `[?]` **Le due misure non sono riconciliate**, e la spiegazione più economica è che non misurino
la stessa cosa: il tratto 9 di A è *«richiamo del decodificatore → il fotogramma è PRONTO»*, cioè
un'**attesa** (il primo `drawImage` di un `VideoFrame` blocca finché la GPU non l'ha consegnato) —
`04-b30` lo dice già di suo: *«il tratto 9 non è il disegno, è l'attesa»*. ⛔ Un banco che misuri
il **disegno** troverà 0,4-2,8 ms e avrà ragione; uno che misuri l'**attesa** troverà 17 e avrà
ragione anche lui. ⇒ **Prima di togliere 15 ms da un numero della fase, va scritto quale delle due
il numero conteneva.**

---

## F2.4 · I SEI BUCHI — `[M]` alla sua risoluzione **NON ricompaiono**

| tela | secondi di trascinamento | buchi | uno ogni |
|---|---|---|---|
| 1280×720 | 25,0 | 0 | — |
| 1560×888 | 111,5 | 0 | — |
| 1920×1080 | 75,0 | 1 | 75 s |
| ⭐ **2560×1080** | **244,6** | **3** | **82 s** |
| *(l'utente)* | *17,5* | *6* | ⛔ *2,9 s* |

⇒ ⛔ **La risoluzione non li fa ricomparire: sono 28 volte più radi dei suoi.** E il rilevatore
funziona — G11 lo prova su un buco innestato, e qui ne ha trovati tre veri con la loro descrizione
(*«5 disegni della scena NON sono arrivati al vetro: il buco è a VALLE di lei»*).

⭐ **Resta la rete**, e nei miei giri è viva: `[M]` il `ping` che corre **nello stesso giro** ha
p99 fra **27,9 e 35,4 ms** e il **3,8 – 4,1 %** dei colpi sopra 15 ms ⇒ `[M]` **+95 … +120 px di
distacco che si aprono di colpo**, cioè un sesto di barra in più su un colpo su venticinque.

⇒ `[?]` **I sei buchi dell'utente non sono né della risoluzione né della nostra scena.** Restano
tre strade, nessuna chiusa: il **suo** momento di WiFi, il **suo desktop vero** (una scena di prova
non ha né finestre, né ombre, né altre applicazioni), o il **registratore di GNOME** (§2.6: gira a
30 fotogrammi al secondo e satura).

---

## F2.5 · ⭐ CHE COSA QUESTO DICE DELLA COPIA ZERO — una previsione che l'utente può smentire

`[M]` F4 misura, **col mio stesso banco**, 0,27/0,26 barre prima e **0,16/0,16** dopo. ⛔ Quei
numeri sono presi **allo stesso confine del mio**, quindi hanno **gli stessi tre pezzi mancanti**.
⇒ Applicando lo stesso conto di F2.2 punto 4:

| | barre |
|---|---|
| il banco, dopo la copia zero | **0,16** |
| ⇒ **quel che l'utente vedrà**, con i tre pezzi rimessi | ⭐ **0,31 – 0,46** |

⇒ ⭐⭐ **Previsione falsificabile, e la può falsificare lui guardando**: dove prima diceva «metà
della barra del titolo», dovrebbe adesso dire **«un terzo, o poco meno»**. ⛔ Se dicesse ancora
«metà», allora **la spiegazione di F2.2 è sbagliata** e va rifatta. È il modo giusto di chiudere
questa fase: non con un numero nostro, ma con una previsione che il suo occhio può smentire.

---

## ⛔ CHE COSA NON HA FUNZIONATO

1. ⛔⛔ **`--window-size` di Chrome NON è rispettato, e per tre giri ho misurato una tela sbagliata
   credendola quella giusta.** `[M]` Chiedendo 2600×1192 la tela usciva **2544×960**; chiedendone
   2616×1312 usciva **la stessa**. `[R]` La causa, letta nel profilo e non dedotta: Chrome salva in
   `Preferences → browser.window_placement` una collocazione **`maximized: true`** con
   `work_area 2560×1080`, e su Xvfb — **senza gestore di finestre** — si riapre massimizzato a
   quell'area ignorando la bandiera. ⛔ **Il banco la bandiera la dichiarava** (`--window-size=2600,1192`
   sta nel verbale) **ma nessuno la confrontava con la tela ottenuta**: è la forma di `LEZIONI.md`
   §2.0 in persona — *un palco dichiarato e non verificato*.
   ⇒ **Cura**: un pezzo a parte (`forza.py`) che dal di fuori chiama `Browser.setWindowBounds` via
   CDP appena Chrome apre la porta di diagnosi, **rilegge i limiti ottenuti** e li stampa. E il
   controllo vero è nel banco: la riga `tela 2560x1080` si legge **prima** di prendere il numero,
   e i giri con la tela sbagliata **si buttano**. ⚠ Ne ho buttati tre.
   ⭐ **Va messo dentro `08-b67`**: oggi il rimedio è nella testa di chi lancia.

2. ⛔ **Il banco locale sulla macchina era una copia vecchia**, e diceva un totale più piccolo delle
   sue parti (vedi F2.1). ⚠ Non l'ho preso per buono perché il conto non tornava — ma un lettore
   distratto avrebbe scritto «l'anello locale è 13,5 ms» in un documento.

3. ⛔ **L'anello locale a 1560×888 NON è uscito**: `[M]` **n = 12**, poi **1**, poi **1** su tre
   tentativi. `[R]` La causa è la sincronia: il banco locale campiona `/dev/shm` **da fuori** e vede
   l'eco cambiare solo mentre la mano si muove; farli partire a mano con uno `sleep` è un
   accoppiamento fragile, e due volte su tre la finestra è caduta **prima** che la mano partisse
   (l'ingresso e la misura dello scorrimento costano ~35 s). ⇒ **Il numero locale a 1560 in questo
   rapporto (26,40 ms) ha n = 12 e si legge come indicazione, non come misura.** La cura è che il
   banco locale lo lanci **il banco dell'elastico**, non l'agente.

4. ⛔ **Cinque giri persi per uno `/tmp/.X11-unix/X92` orfano.** Quando un giro muore male il socket
   dell'Xvfb resta, e il giro dopo si rifiuta di partire — giustamente (`03-b17` non condivide uno
   schermo), ma **il rimedio (`rm -f`) è nella testa di chi lancia**, non nel banco.

5. ⛔ **Il banco di A non si può girare alla tela dell'utente**, quindi il confronto A↔F2 è a
   **1460/1560**, non a 2560. `[R]` `04-b30-anello-input.py:3381` costruisce il palco con
   `finestra=(1500, 1000)` **scritto nel sorgente**, e l'Xvfb nasce di conseguenza a 1600×1200: una
   finestra da 2600 non ci sta e `forza.py` non può allargare uno schermo. ⇒ `[?]` **Il numero di A
   a 2560×1080 non esiste** — e visto che i pixel non contano (F2.2 punto 1) sarebbe **~110 ms**,
   ma è una stima.
   ⚠ **E lo stesso banco chiama il terreno SENZA ambiente** (`_sudo("bash %s scena-avvia")`): coi
   difetti avvia la scena di `provao2`. Ho dovuto scrivergli attorno un terreno mio
   (`/media/REMOTIX/src/08-f-terreno.sh`) che è solo `04-b32-terreno.sh` con le mie variabili.

6. ⛔ **Due giri di A sono usciti ROSSI per un difetto del banco, non del prodotto**: `[M]` *«il
   seqlock non si è fermato (seq 47482 e 47484)»* e Q4(a) senza fotogrammi da mostrare ⇒ verdetto
   NON CONFORME **mentre la scomposizione dei tempi era completa e sana** (n = 241, somma dei tratti
   108,9 contro T 109,9). ⇒ ⚠ **I numeri di A che cito vengono da un giro il cui verdetto è rosso**,
   e lo dico invece di nasconderlo: sono buoni per il **confronto fra tratti**, non per essere
   consegnati come «l'anello».

7. ⚠ **Il costo del banco è dentro ogni numero**: `[M]` la lettura delle due marche costa
   **7,5 – 10,5 ms mediani per fotogramma**, sul **filo principale**, cioè quello che decodifica e
   dipinge. ⛔ È un errore sistematico che **allunga** i miei tempi (quindi non gonfia il nostro
   vantaggio) e **cresce con la tela** (7,5 a 1560, 8,5 a 1920, 9,5-10,5 a 2560): ⇒ ⭐ la pendenza
   vera dei pixel è **ancora più piatta** di quella che ho scritto — cioè **negativa** se si
   togliesse il costo del banco.

8. ⛔ **Ho scritto sul registro comune dei giri**: `banchi/08-b67-esiti.jsonl` ha i miei quindici
   giri accanto a quelli di B. Si distinguono dal nome (`f2-*`), ⚠ ma **il nome del giro non è una
   regola** — è lo stesso rilievo che l'agente A si era già fatto.

9. ⛔ **Il mio albero è stato RICOSTRUITO alle 18:44 mentre lavoravo** (md5 diverso da quello di
   partenza, `.o` nuovi), quasi certamente dal banco di A. ⇒ ⚠ **I giri prima e dopo le 18:44 non
   girano sullo stesso binario.** Ho verificato che **le sorgenti sono le stesse** e che la copia
   zero non c'è in nessuno dei due, e i numeri prima e dopo coincidono (70,7 contro 70,3) — ma
   **la verifica l'ho fatta dopo, e poteva andare diversamente.**

---

## `[?]` CHE COSA RESTA APERTO

| | |
|---|---|
| ⏳⏳ **il pezzo cieco in USCITA è la metà del mio intervallo** | `[?]` 16-40 ms è una **forbice di 24 ms** presa da `STUDI.md` §web §6.2, e da sola muove il risultato da 0,48 a 0,63 barre. ⛔ Finché non è misurata, «0,50» e «0,60» sono indistinguibili **per noi** e non per l'utente. ⭐ È la `[?]` che vale di più di tutta la fase |
| ⏳ **il tratto 1a con un mouse VERO** | `[M]` 11,55 ms, ma è preso dal banco di A con la sua mano da 70 ms. ⭐ La strada `--mano cdp` di `08-b67` (eventi *fidati* consegnati da Chrome) è prevista e **non è ancora stata girata**: è la misura giusta, e chiuderebbe il pezzo più grosso che resta `[?]` nel mio conto |
| ⏳ **il tratto 9 di A: 17,6 o 2,8 ms?** | ⛔ le due misure non sono riconciliate (F2.3). Prima di correggere un numero della fase va scritto **quale delle due** conteneva |
| ⏳ **l'anello locale a 1560×888** | n = 12: da rifare col banco locale lanciato **dal** banco dell'elastico |
| ⏳ **i sei buchi** | non sono della risoluzione. Restano il suo WiFi, il suo desktop vero, o il suo registratore |
| ⏳⏳ **il desktop VERO contro la scena di prova** | ⛔ nessun banco di questa fase misura un desktop con finestre, ombre e compositing: misurano **una scena sola a schermo intero**. È l'ultima differenza fra il banco e l'utente che **non** è stata quantificata, e tira nel verso scomodo |
| `[?]` **il codificatore** | `08-b67` **non** verifica che la codifica sia in hardware. `provaf8` è nel gruppo `render` (verificato: `groups=1044(provaf8),44(video),991(render)`), ⛔ ma «ha aperto un render node» non prova niente (`LEZIONI.md` §1.11) |

---

## Come si rigira

```bash
# sul portatile, dalla radice del deposito
python3 banchi/08-b67-elastico.py --certifica          # 13 guasti su 13 (rifatto oggi)
bash <scratch>/fase8/f2.sh utente ; sessione ; accendi ; ponte ; parola
(python3 <scratch>/fase8/forza.py 2600 1192 9645 60 &)  # ⛔ senza, la tela esce 2544x960
bash <scratch>/fase8/f2.sh scena-avvia
bash <scratch>/fase8/f2.sh misura 2600 1192 25 nome     # ⛔ e si VERIFICA la riga «tela 2560x1080»
bash <scratch>/fase8/carico.sh                          # ⛔ prima e dopo ogni giro
```

⚠ **Lasciato acceso sulla macchina**: prodotto sulla **7765**, ponte sulla **7766**, scena, e la
sessione GNOME di `provaf8`. Si spengono con `f2.sh spegni` — ⛔ che tocca **solo** le mie cose.
⚠ **Nel deposito** restano modificati `banchi/08-b67-esiti.jsonl` e `banchi/04-b30-esiti.jsonl`
(i registri dei giri) e **niente altro**: `src/` non è stato toccato.


---

## 4-F4 · ⭐⭐⭐ AGENTE F4 — **LA COPIA ZERO È FATTA**, e siamo a 1,23 volte il locale · *22 agosto 2026, sera*

> ### ⭐⭐⭐ IL NUMERO CHE CHIUDE IL MANDATO, NELL'UNITÀ DELL'UTENTE
>
> | | barre del titolo | |
> |---|---|---|
> | il **locale** — il pavimento, misurato da B | **0,13** | |
> | ⭐ **REMOTIX, dopo la copia zero** | **0,16 · 0,16** | **1,23 × il locale** |
> | REMOTIX, prima | 0,27 · 0,26 | 2,1 × il locale |
>
> ⇒ ⭐⭐ **Da 2,1 volte il locale a 1,23.** La specifica dell'utente era *«il più vicino possibile a
> una situazione locale, ma non identica: quello è impossibile»* (§1.1): **il divario si è chiuso
> per due terzi.**
>
> ⛔⭐ **E la regola che poteva far cadere tutto è rispettata**: `LEZIONI.md` §6.2 dice che un
> guadagno di millisecondi che non diventa fotogrammi **non è un guadagno**, e in questa stessa fase
> era già successo due volte (C tolse 7,28 ms senza far salire i fotogrammi). ⇒ `[M]` **I fotogrammi
> DIPINTI dalla pagina salgono: 834 → 942 e 870 → 926, il +9 %.** Non è una vittoria di millisecondi.
>
> ### Il tratto, e i sotto-tratti affiancati
>
> `[M]` `cattura → byte fuori`: **22,82 → 6,41 ms**, il **−72 %**. Tre giri **alternati** (A-B-A-B
> sullo stesso albero), md5 verificati diversi, tela 1920×1080, **copia zero verificata accesa a
> ogni giro**. Macchina: 20 nuclei, carico 1,31-1,65, 0 Chrome, 0 Xvfb — **il carico è dichiarato**,
> come §4-F1 pretende.
>
> | | prima | dopo |
> |---|---|---|
> | la copia | 2,11 | **0,00** |
> | la conversione (`sws_scale`) | 11,23 | **2,98** |
> | il caricamento sulla GPU | 1,24 | **0,00** |
> | ⭐ **il produttore** | 5,44 | **0,64** |
>
> ### ⭐⭐ E i «5,79 ms di Mutter» erano quasi tutti NOSTRI — smentito C
>
> §4-C aveva scritto: *«5,79 ms sono di Mutter: più di un terzo del margine non è nostro»*. ⛔ `[M]`
> **Il produttore cala di 4,80 ms** togliendo **il nostro lavoro** dal thread di tempo reale di
> PipeWire. ⇒ Non era il compositore: **eravamo noi, dentro casa sua.**
>
> ### ⛔⛔ E il difetto vero trovato **coi millisecondi già perfetti**
>
> `[M]` Il driver **iHD non onora un passo che non sia multiplo di 64 byte**: legge le righe a passo
> suo e il desktop esce **inclinato di qualche pixel per riga, senza nessun errore**.
>
> | tela | passo | %64 | marca |
> |---|---|---|---|
> | 1920×1080 | 7680 | 0 | ⭐ letta, contrasto 1,000 |
> | 1552×888 | 6208 | 0 | ⭐ letta, contrasto 1,000 |
> | 1544×888 | 6176 | 32 | ⛔ **NON letta** |
> | 1560×888 | 6240 | 32 | ⛔ **NON letta** |
>
> ⛔ **1552 e 1544 distano otto pixel e danno verdetti opposti.**
>
> ### ⭐⭐⭐ E la cosa da mettere in `LEZIONI.md`: **il controllo sul colore è CIECO a questo difetto**
>
> `[M]` Le medie per canale dei due flussi combaciano entro **0,17 livelli su 255** mentre la marca
> **non si legge su 0 fotogrammi di 903**. Controllo negativo (R↔B scambiati): scarto **33**, cioè
> lo strumento funziona.
>
> ⇒ ⛔⛔ **Un banco che guarda le medie dice VERDE su un'immagine sbagliata.** È la forma di
> `LEZIONI.md` §1.20 applicata ai **pixel** invece che ai giudizi: *la misura è buona e non guarda
> la cosa che conta*.
>
> **La cura**: il passo si guarda **misurato**, mai calcolato, prima di comprimere; se non è
> importabile il palco si rimonta sulla memoria **dichiarandolo**; al cambio di tela la copia zero si
> riprova da sé. `[M]` Stessa tela 1560: **0 eco su 903 → 831 su 831**.
>
> ### ⭐ E il rilascio: la cura è attuata, **ma il guasto innestato NON l'ha confermata**
>
> La ritenuta del `pw_buffer` è in vigore (6 buffer contro 4, **0 sostituiti su 1 800**). ⛔ Ma il
> controllo positivo **non ha riprodotto il danno**: 10 marche su 10 anche **senza** attesa GPU.
> ⇒ ⚠ **Resta prudenza, non necessità misurata**, e sta scritto così.
>
> ⭐ **Il guasto è servito lo stesso**: senza `vaSyncSurface` la conversione scende 2,86 → 0,38 e la
> codifica sale 2,43 → 4,67, totale 6,19 → 6,05. ⇒ **L'attesa costa zero** e dice dov'è il punto di
> rilascio giusto.

> ### ⭐⭐ IL RISULTATO IN DUE RIGHE, e la seconda vale più della prima
>
> `[M]` Il tratto `cattura → primo byte` passa da **22,82 a 6,41 ms (−72 %)**, tre giri
> **alternati**, e ⭐ **stavolta i fotogrammi SALGONO anche al metro dell'utente**: il distacco
> misurato col banco di B va da **0,27 a 0,16 barre del titolo**, con **834→942** fotogrammi
> dipinti in 25 s.  Il pavimento locale misurato da B è **0,13**: eravamo a **2,1 volte** il locale,
> siamo a **1,23**.
>
> ⛔⛔ **E il difetto vero l'ho trovato dopo aver visto quei numeri.** La copia zero funzionava, il
> tratto era sceso del 72 %, e **il desktop usciva inclinato di qualche pixel per riga** — senza
> nessun errore, su nessuna riga di registro. Il driver iHD, importando il DMA-BUF, **non onora un
> passo che non sia multiplo di 64 byte**.
>
> ⭐⭐⭐ **E la parte che è metodo, non aneddoto**: `[M]` il controllo sul COLORE **non lo vede**.
> Le medie per canale dei due flussi combaciavano entro **0,17 livelli su 255** — R 96,90 contro
> 96,97, B 130,11 contro 130,17 — mentre il lettore certificato della marca leggeva **0 marche su
> 903**. ⇒ *Un banco che guarda le medie dice verde su un'immagine sbagliata.* Il numero che
> discrimina è la **struttura**, non l'intensità.

*22 agosto 2026. Macchina di prova NIC-OS (Intel i5-13500T, **iGPU Intel UHD 730 integrata** su
`/dev/dri/renderD128`, iHD 25.2.3), utente `provaf48` (uid 1046), porta **7775**, albero
`/media/REMOTIX/src/08-f4-src`, lavoro `/media/REMOTIX/tmp/08-f4`.*

> ### ⛔ E LA PRIMA COSA È LA PORTA, di nuovo — «08-f» non era libero
>
> `[M]` `pgrep -ax remotix` prima di toccare qualunque cosa: un **altro agente della fase 8** girava
> in quel momento con utente **`provaf8`**, albero `/media/REMOTIX/src/08-f-src`, lavoro
> `/media/REMOTIX/tmp/08-f` e porta **7765**. ⇒ Il mio si chiama **`08-f4`** dappertutto, l'utente è
> **`provaf48`** (uid 1046), e le porte **7775 · 7776 · 7777** sono state **contate con `ss`** prima
> di prenderle. ⛔ 7730 e 7731 — i server dell'utente — non sono mai state toccate, e si contano
> prima e dopo ogni passo.

---

## F4.1 · Che cosa è stato cambiato, e perché

| file | che cosa |
|---|---|
| `src/cattura.h` · `src/cattura.c` | ⭐ la **ritenuta** del `pw_buffer`, il descrittore DMA-BUF dentro `CatturaFermo`, la **generazione** dei buffer, la misura dei pixel del primo fotogramma via `mmap` |
| `src/codificatore.h` · `src/codificatore.c` | ⭐ l'importazione del DMA-BUF come superficie VA-API, la **conversione sulla GPU** (VPP) al posto di `sws_scale` + `av_hwframe_transfer_data`, la cache delle importazioni, ⛔ **la guardia sul passo** |
| `src/figlio.c` | ⭐ la strada si chiede **SCHEDA**, e si retrocede sulla **MEMORIA dichiarandolo** quando il fotogramma non è usabile |

⛔ **Non è stata toccata una riga** di `src/pagina.html` né dei banchi `04-b30-*` e `08-b67-*`.

### Che cosa fa la copia zero, in una riga

Il fotogramma **non esce più dalla GPU**. Il DMA-BUF che Mutter consegna si importa come superficie
VA-API (`vaCreateSurfaces` con `VA_SURFACE_ATTRIB_MEM_TYPE_DRM_PRIME_2`) e si converte in NV12 con
la **VPP della scheda** (`VAEntrypointVideoProc`), direttamente dentro la superficie che il
codificatore consuma.

⚠ **E quel che NON toglie, ed è la metà che nessuno si aspetta**: la conversione di colore **va
fatta lo stesso**. Mutter consegna BGRx, `hevc_vaapi` vuole NV12. ⇒ Non è «non si converte»: è
**chi converte** — la GPU invece della CPU, sulla memoria che ha già sotto invece che su otto
megabyte fatti passare due volte per il bus. Per questo il suo costo resta nella voce
`conversione`, sotto la **stessa etichetta di prima**: metterlo in una voce nuova avrebbe reso
impossibile il confronto col «prima». ⛔ `caricamento` invece va a **0**, e lì lo zero vuol dire
**«questo tratto non c'è più»**, non «è gratis».

---

## F4.2 · ⛔⛔ IL DIFETTO VERO — il passo del DMA-BUF, e otto pixel che cambiano verdetto

`[R]` Il driver iHD, importando un DMA-BUF, **non onora un passo che non sia multiplo di 64 byte**:
legge le righe a un passo suo, e l'immagine esce **inclinata di qualche pixel per riga**.

⭐ **Quattro tele scelte apposta dalle due parti della soglia**, lette col **lettore certificato**
della marca (`banchi/03-marca.py`, controllo negativo `[M]` 0 falsi su 3 000 sonde di rumore):

| tela | passo | passo % 64 | la marca si legge? | contrasto |
|---|---|---|---|---|
| 1920×1080 | 7680 | **0** | ⭐ SÌ (disegno 65) | **1,000** |
| 1552×888 | 6208 | **0** | ⭐ SÌ (disegno 70) | **1,000** |
| 1544×888 | 6176 | 32 | ⛔ **NO** | 0,617 |
| 1560×888 | 6240 | 32 | ⛔ **NO** | 0,510 |

⭐ **1552 e 1544 distano OTTO pixel e danno verdetti opposti**: non è una soglia scelta dopo aver
visto il risultato, è un confine al pixel. ⚠ E il passo è `larghezza × 4` esatto in tutte e quattro,
modificatore **LINEAR**, **letto dal chunk** e mai calcolato.

### ⭐⭐⭐ E la cosa che va in `LEZIONI.md`, non in nota a piè di pagina

⛔ **Il controllo sul colore non vede questo difetto.** Sullo stesso paio di flussi, 40 fotogrammi
ciascuno, 2 241 760 campioni:

| | media R | media G | media B | min/max | a zero | a 255 |
|---|---|---|---|---|---|---|
| memoria (`sws_scale`) | 96,902 | 114,055 | 130,110 | 0 / 255 | 6,39 % | 1,98 % |
| scheda (GPU, VPP) | 96,969 | 113,891 | 130,170 | 0 / 255 | 6,41 % | 1,79 % |
| **scarto** | **0,067** | **0,165** | **0,061** | — | — | — |

⭐ E il **controllo negativo** dello stesso banco — lo stesso flusso con R e B **scambiati a mano** —
dà scarti di **33,27 e 33,14**: il banco *sa* dire di no, e quel verde non è per costruzione.

⇒ ⛔⛔ **Le medie combaciavano entro 0,17 livelli su 255 mentre la marca non si leggeva su 0
fotogrammi di 903.** Uno strumento che guarda le intensità è cieco a un difetto **geometrico**.
⭐ Chi certifica una catena di immagini deve avere almeno un controllo che guardi la **struttura**.

### La cura, e perché è questa

⛔ **Il passo si guarda MISURATO, mai calcolato** (`cattura.h` regola 1), **prima di comprimere**. Se
non è multiplo di 64 il fotogramma **non si spedisce** e il palco si **rimonta sulla MEMORIA
dichiarandolo**; al cambio di tela la copia zero **si riprova da sé**, perché una sola tela storta
non deve spegnerla per tutta la sessione.

`[M]` La cura provata dal vivo, e **il verdetto lo dà il banco, non l'occhio**: stessa tela **1560**,
stesso binario «scheda», **prima** della cura **0 eco letti su 903** — **dopo** la cura **831 su 831
(100 %)**, perché ripiega sulla memoria e l'immagine è giusta. La riga di registro dice quale dei
due casi è.

⚠ **E la cura piena NON è mia da fare**: il passo lo decide il produttore e lo fa uguale a
`larghezza × 4` `[M]`. ⇒ Una tela **multipla di 16** avrebbe sempre il passo buono, ma la regola
della tela vive in `rcp_misura_ammessa()` (oggi: solo «pari»), che è **normativa** in `RCP.md` §4.5
e non è di questo file. 🔸 **Girata al direttore per l'utente**, non curata di nascosto.

---

## F4.3 · La cura del RILASCIO, e ⛔ **il guasto innestato NON l'ha confermata**

⭐ **Attuata quella decisa da C**: si **trattiene il `pw_buffer`** fino a lettura finita, e **non**
si chiede `SPA_META_SyncTimeline`. La ritenuta è **nostra** e vale su ogni produttore; la timeline
dipende da quel che il produttore offre, e quando non c'è **non c'è nessun errore** — c'è la
schermata che si alterna (`LEZIONI.md` §8, §1.25).

**Come è fatta**: `cattura_fermo_libera()` **è** il rilascio; il buffer torna a PipeWire solo lì.
Il momento in cui «la GPU ha finito» è la `vaSyncSurface()` dentro la conversione: quando
`codificatore_comprimi_scheda()` torna, la scheda ha **finito di leggere**, e solo allora
`figlio.c` rende il buffer. ⛔ E due cose che il riquadro impone: il buffer che era nel posto si
rende **prima** di sovrascriverlo, e un buffer che PipeWire ha **tolto** (`remove_buffer`) non si
rende affatto — il `CatturaFermo` porta la **generazione** con cui è nato e il confronto decide.

**Il prezzo, contato**: `[M]` sulla strada della scheda si chiedono **sei** buffer invece di
quattro, perché ne tratteniamo al più due (uno nel posto, uno in mano a chi legge). Mutter li
concede: `[M]` **«6 buffer distinti»** contro **«4»** sulla memoria, e **«sostituiti nel posto 0»**
su 1 800 fotogrammi ⇒ la ritenuta non affama il produttore.

### ⛔ IL GUASTO INNESTATO, e il risultato è un NO

Tolta **la sola riga dell'attesa** (`vaSyncSurface`) lasciando tutto il resto — il buffer torna a
Mutter mentre VA-API lo sta ancora leggendo, che è **esattamente** il meccanismo di §8. Binari
verificati diversi per md5.

⭐ **Il guasto è stato davvero percorso, e lo dicono i tratti**:

| | conversione | codifica | totale |
|---|---|---|---|
| sano (con l'attesa) | **2,86 ms** | 2,43 | 6,19 |
| guasto (senza l'attesa) | **0,38 ms** | **4,67** | 6,05 |

⇒ ⭐⭐ **Togliere l'attesa non compra niente**: il tempo si sposta da `conversione` a `codifica`,
perché il codificatore aspetta lo stesso la VPP da cui dipende. **6,19 → 6,05 ms**, dentro la
dispersione. ⇒ La sincronizzazione esplicita **costa zero** e in cambio dà il punto di rilascio
giusto: è una riga che si tiene senza pagarla.

⛔ **Ma la corruzione NON si è presentata**: `[M]` **10 marche lette su 10** col guasto addosso,
contrasto **1,000** su tutti e dieci, contro **10 su 10** del sano. ⇒ **Su questa scena e su questa
macchina la ritenuta non è dimostrata necessaria.** Il meccanismo di §8 resta `[R]` (letto in
Mutter), non `[M]`. ⚠ La spiegazione plausibile è che con sei buffer riciclati la finestra non si
apre mai: la VPP finisce in ~3 ms e un buffer torna in giro dopo ~100 ms. ⇒ La ritenuta resta
**prudenza con un meccanismo documentato e un prezzo misurato (due buffer)**, non una cura con una
misura sotto. **Va detto così.**

⛔ E **non** è stata rifatta la superficie di accumulo: il DMA-BUF di Mutter non è un diff.

---

## F4.4 · ⭐⭐ IL PRIMA E IL DOPO — tre giri **ALTERNATI**, i tratti affiancati, i fotogrammi accanto

⛔ **Il palco, accanto al numero** (`LEZIONI.md` §2.0), e oggi vale doppio: `[M]` un tratto dato a
17,48 ms si è rivelato fra 0,39 e 2,80 quando la macchina non era martellata da altri banchi.

*Macchina di prova, **20 nuclei**, carico **1,31-1,65**, **17** processi `remotix` e **5**
`gnome-shell` di altri banchi vivi, **0** Chrome e **0** Xvfb. Tela **1920×1080** — ⭐ **passo 7680,
multiplo di 64: la copia zero era DAVVERO accesa**, e la riga di registro «il palco si monta sulla
strada SCHEDA» è stata verificata a ogni giro. Codec **HEVC in hardware** — `[M]` dal registro:
«hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD 25.2.3 · ⚠ EncSliceLP, bassa potenza)»,
chiesto al **componente** (`componente_e_hardware()`: accetta un formato di superficie) e
l'entrypoint **letto dal driver**, non da ffmpeg.*

⛔ **Alternati e non in fila** (A-B-A-B sullo stesso albero): i due binari nascono dallo **stesso
sorgente**, cambia **una costante** (`COPIA_ZERO`), e il banco **verifica che gli md5 differiscano**
prima di misurare.

| tratto | **prima** *(memoria)* | **dopo** *(scheda)* | Δ |
|---|---|---|---|
| ⛔ **produttore** *(pts di Mutter → la nostra richiamata)* | **5,44** | **0,64** | ⭐ **−4,80** |
| allocazione | 0,00 | 0,00 | — |
| ⭐ **copia** | **2,11** | **0,00** | **−2,11** |
| nel posto | 0,09 | 0,08 | −0,01 |
| misura | 0,00 | 0,00 | — |
| ⭐ **conversione** | **11,23** | **2,98** | **−8,25** |
| ⭐ **caricamento** | **1,24** | **0,00** | **−1,24** |
| codifica | 2,21 | 2,47 | +0,26 |
| spedizione | 0,02 | 0,05 | +0,03 |
| resto | 0,05 | 0,17 | +0,12 |
| **TOTALE** | **22,82** | **6,41** | ⭐⭐ **−16,41 ms (−72 %)** |
| **fotogrammi in 45 s** | 1 487 · 1 468 · 1 521 | 1 519 · 1 506 · 1 454 | ⚠ **fermi** |

*(mediana dei tre giri per riga; i tre concordano — `conversione` 11,23/12,06/10,72 prima,
2,91/2,99/2,98 dopo; `totale` 22,82/23,46/22,52 prima, 6,34/6,48/6,41 dopo.)*

### ⛔ Che cosa questa tabella dice, e che cosa NON dice

1. ⭐⭐ **I 5,79 ms «di Mutter» non erano tutti di Mutter.** C aveva scritto *«più di un terzo del
   margine non è nostro: non c'è niente da limare, è il compositore»*. `[M]` La voce `produttore`
   passa da **5,44 a 0,64 ms** togliendo **il nostro** lavoro dal thread di tempo reale e dalla
   banda di memoria. ⇒ **Erano nostri quasi tutti**, ed è la smentita più grossa di oggi;
2. ⛔ **I fotogrammi consegnati dal figlio NON sono saliti** (1 487 → 1 506, dentro la dispersione):
   a **33/s** su una scena che ne disegna 61 il collo di bottiglia non è la nostra CPU. È la forma
   mite di `LEZIONI.md` §6.2, e va detta;
3. ⛔ **Il budget di C — 10,96 ms — è stato superato, e non perché la stima fosse timida**: le tre
   voci previste ne valgono 11,60, ma il totale scende di **16,41** perché ne è caduta una quarta
   che nessuno contava (`produttore`). ⇒ **In questo tratto le voci non sono indipendenti in
   tutt'e due i versi**: si passano la cache (C), e si passano il thread di tempo reale (io).

---

## F4.5 · ⭐⭐⭐ IL METRO DELL'UTENTE — il distacco in barre del titolo

⛔ Il banco è **quello di B** (`banchi/08-b67-elastico.py`, **13 guasti innestati su 13 accusati**,
ricertificato oggi prima dell'uso): non ne è stato inventato un altro e non ne è stata toccata una
riga.

*Portatile **4 nuclei**, carico **0,21-0,76**, **0 Xvfb** e **1** Chrome di altri (finestra
tranquilla concessa dal direttore). Macchina di prova 20 nuclei. Rete **WiFi vera** in mezzo.
⭐ Finestra **1608** ⇒ tela **1568×888**, **passo 6272, multiplo di 64: la copia zero era accesa in
tutt'e due i giri «scheda»**, verificato sul registro giro per giro.*

| | **prima** *(memoria)* | **dopo** *(scheda)* |
|---|---|---|
| ⏱ ritardo, confine SCOMODO | **68,2** · **64,1** ms | **39,0** · **38,7** ms |
| 📏 distacco | 195 · 188 px | 117 · 116 px |
| ⭐⭐ **distacco in barre del titolo** | **0,27 · 0,26** | ⭐ **0,16 · 0,16** |
| 🖼 **fotogrammi dipinti in 25 s** | 834 · 870 | ⭐ **942 · 926** |
| eco letti (Q3) | 834/834 · 870/870 (100 %) | 942/942 · 926/926 (100 %) |
| verdetto del banco | CONFORME | CONFORME |

⇒ ⭐⭐ **E QUI I FOTOGRAMMI SALGONO INSIEME AI MILLISECONDI** (+9 %, 834→942 e 870→926): per la
regola di §2.2 punto 1 **questa è una vittoria vera**, e non lo era quella di C.

### ⭐⭐ La riga che conta, in una unità sola

| | barre del titolo | ms |
|---|---|---|
| **locale** (lo stesso compositore, senza di noi — misurato da B) | **0,13** | 27,6 |
| REMOTIX **prima** della copia zero | **0,27** | 68,2 |
| ⭐ REMOTIX **dopo** | **0,16** | 39,0 |
| *(l'utente, a occhio, sulla sua sessione)* | *0,50* | — |

⇒ ⭐⭐ **Da 2,1 volte il locale a 1,23 volte.** Dei **42 ms** che B aveva misurato come «quel che
aggiungiamo noi sopra al compositore», ne restano **~11**.

⚠ **E il confronto col giudizio dell'utente NON si fa da qui**: lui guarda a **2560** px e su un
desktop vero, il banco a **1568** e su una scena. Lo scarto 0,27 contro 0,50 resta la `[?]` che B ha
aperto.

### ⛔ E su una tela «storta» il dopo È IL PRIMA — dichiarato, non nascosto

`[M]` Stesso banco, finestra **1600** ⇒ tela **1560×888** (passo 6240, **non** multiplo di 64):
il registro scrive la riga del rifiuto e il palco si rimonta sulla **MEMORIA**. ⇒ Su quella tela il
«dopo» **è il vecchio percorso**, e chi confrontasse i due numeri confronterebbe due volte la stessa
cosa. ⭐ L'immagine però è **giusta** (831 eco su 831, 100 %), che è precisamente quel che la cura
esiste per garantire.

---

## ⛔ Che cosa NON ha funzionato

1. ⛔⛔ **La copia zero ha prodotto un'immagine sbagliata per tre giri di banco, e i millisecondi
   erano perfetti.** Il passo non allineato a 64. Trovato solo perché il banco di B legge una marca
   **strutturata**: il mio banco del colore diceva verde.
2. ⛔ **La mia prima diagnosi di quel difetto era sbagliata.** Avevo incolpato le regioni della VPP
   lasciate a `NULL` (che scalano da 1080 a 1088 righe). Le ho fissate — ed era una cura giusta e
   necessaria — **ma il rosso è rimasto identico**. La causa era un'altra.
3. ⛔ **E prima ancora avevo sospettato l'ORDINE dei giri** (la scheda girava sempre per seconda).
   `[M]` Rifatto con la scheda per prima: stesso rosso. ⇒ Un confondente escluso con una misura
   invece che con un ragionamento — ed era escludibile in tre minuti.
4. ⛔ **Il guasto innestato sul rilascio non ha riprodotto il difetto di §8**: 10 marche su 10 lette
   anche senza aspettare la GPU. La ritenuta resta prudenza, non necessità misurata. Vedi F4.3.
5. ⚠ **La diagnosi del «fotogramma NERO» è più povera sulla strada della scheda.** In memoria si
   guardava a cadenza (500 ms); sulla scheda si guarda **una volta sola**, mappando il DMA-BUF —
   `[M]` **4,76 ms** il primo fotogramma. ⛔ Un desktop che diventasse nero a metà sessione, su
   questa strada, **non ha più chi lo dica**. È dichiarato nel codice e qui, non scoperto dopo.
6. ⚠ **Non ero solo sulla macchina** in nessun giro (17 `remotix` e 5 `gnome-shell` di altri
   banchi). ⇒ ⛔ **I valori assoluti vanno letti come un tetto.** Il prima/dopo regge perché è
   **alternato**, e il carico è dichiarato accanto a ogni giro.
7. ⚠ **`banchi/08-b67-esiti.jsonl` si è allungato con i miei verbali**: è il banco di B che ci
   scrive da sé a ogni giro. Non ho toccato il file a mano; lo dico perché il proprietario non lo
   scopra da un `git status`.

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⏳⏳ **la tela multipla di 16** | ⛔ È una **modifica del protocollo** (`RCP.md` §4.5 dichiara normativo «pari»), quindi è dell'utente. Finché non c'è, la copia zero **non vale su tutte le tele** — e una delle tele scoperte è proprio la **1560** del banco di B |
| ⏳ **la ritenuta serve davvero?** | `[R]` il meccanismo di §8 è letto in Mutter; `[M]` il guasto innestato **non lo riproduce** su questa scena. Servirebbe una scena che tenga la GPU occupata più a lungo dei sei buffer |
| `[?]` **i 0,64 ms di `produttore`** | quel che resta dopo aver tolto il nostro lavoro dal thread di tempo reale. **Quello** sì che sembra di Mutter, ma è dieci volte meno di quanto si credeva |
| `[?]` **i fotogrammi del figlio fermi a 33/s** | la scena ne disegna 61. Con il tratto a 6,41 ms il collo non è più la nostra CPU: `[?]` è la cadenza di Mutter, o il ciclo del figlio (`MOVIMENTO_ATTESA_S`) |
| `[?]` **altri driver e altri compositori** | il vincolo dei 64 byte è `[M]` **su iHD**. Su AMD (radeonsi, `renderD129`) e su KWin/wlroots **non è stato guardato**. ⚠ La guardia però è sul **passo misurato**, quindi non è una regola su iHD: è una regola sul passo |
| `[?]` **i 10 bit** | ⛔ non tornano da questa porta e non erano di questa fase: Mutter consegna BGRx sulla scheda come in memoria |

---

## Come si rifà

Tutto in `/media/REMOTIX/src/`, e il server è rimasto **acceso sulla 7775** col binario sano
(`remotix-scheda`, md5 `c11d200f…`) perché il coordinatore possa rigirare.

| | |
|---|---|
| `08-f4-derivami.sh` | il terreno **derivato** da quello di C, non riscritto — porte, utente e albero miei |
| `08-f4-due-binari.sh` | i due binari dallo **stesso albero**, con la verifica che gli md5 differiscano |
| `08-f4-ab.sh` | ⭐ il prima/dopo **alternato** dei tratti |
| `08-f4-elastico.sh` *(sul portatile)* | ⭐ il metro dell'utente, alternato, che **guida** il banco di B senza toccarlo |
| `08-f4-misure.sh` | ⭐ le quattro tele dalle due parti della soglia dei 64 byte |
| `08-f4-colore.sh` · `08-f4-colore.py` | il confronto di colore, **col controllo negativo R↔B** |
| `08-f4-guasto-rilascio.sh` · `08-f4-prova-guasto.sh` | ⭐ il guasto innestato sul rilascio |

⚠ Le copie stanno anche in `…/scratchpad/`. ⛔ Nessuno sta in `banchi/`: sono banchi di questo
punto, e i rapporti degli agenti non si conservano — se il coordinatore li vuole, il posto è
`banchi/` con un nome `08-…`.


---

## 4-F1 · ⭐⭐⭐ AGENTE F1 — **l'anello intero: 89,86 → 55,20 ms**, appaiato · *22 agosto 2026, notte*

> ### ⭐⭐⭐ IL NUMERO CHE MANCAVA A TUTTA LA FASE
>
> `[M]` **`input → vetro` = 55,20 ms** con la copia zero accesa, contro **89,86** senza:
> **−34,66 ms, il 39 %.**
>
> ⭐⭐ **Due giri di seguito che condividono TUTTO tranne il binario** — stessa tela 1456×888, stesso
> passo 5824, stessa finestra, stessa scena, e `macchina carica: false` **scritto dal banco** in
> tutt'e due (carico 1,10 e 0,40 su 4 nuclei, un solo banco `b30`). Md5 letti a mano da
> `/proc/PID/exe`: `f45e9f78…` contro `73ce3a1f…`.
>
> ⭐ **Ed era accesa davvero**: il prodotto dichiara **«strada scheda»** oggi e **«strada memoria»**
> ieri, **col passo identico** ⇒ si ribalta perché cambia il **binario**, non la tela.
>
> | | il tratto | ieri | ⭐ **oggi** | Δ |
> |---|---|---|---|---|
> | **E** | codifica e ritorno | 26,56 | **10,27** | **−16,30** |
> | **C** | l'attesa del quadro nella scena | 27,67 | **11,78** | **−15,89** |
> | **D** | il quadro di Mutter | 16,33 | 16,01 | −0,32 |
> | | **T — l'anello intero** | **89,86** | **55,20** | **−34,66** |
> | | p95 · n | 157,25 · 476/476 | **122,50** · 721/727 | −34,75 |
>
> ### ⭐⭐⭐ E la cosa che nessuno aveva previsto: **la cura rende dove non è sua**
>
> ⛔ **Metà del guadagno — 15,89 dei 34,66 — sta nel tratto C**, che è **sul server** e che la copia
> zero **non attraversa**. ⇒ `[?]` L'ipotesi economica è la smentita di F4 a §4-C: **il produttore
> tolto dal thread di tempo reale** di PipeWire. ⚠ **Dichiarata, non misurata**, e sta scritta così.
>
> ⭐⭐ **E il conto torna con F4 per un'altra strada**: `[M]` tratto 5 **−62 %** (26,27 → 9,89);
> F4, senza browser e su un altro palco, **−72 %**. Due banchi, due palchi, **stessa forma**.
>
> ⭐ **Ed è il primo giro interamente verde** che questo banco abbia mai prodotto: **12 su 12, Q5 e
> Q6 compresi** — i due che il 14 agosto erano **rossi tutti e due** quando fu consegnato il 139,40,
> e nessun documento lo diceva.
>
> ### ⛔ I limiti, scritti accanto al numero
> - ⛔ **NON si sottrae il 55,20 dai 74-76 ms**: altra tela (dove la copia zero **non si accende
>   nemmeno**) e carico `[R]` invece che `[M]`. **Il «prima» buono è quello appaiato di stanotte**;
> - ⚠ **Un giro per parte**, e sullo stesso binario di ieri ci sono `[M]` **74,08 · 75,81 · 89,86**
>   ⇒ **~15 ms di dispersione**. ⇒ ⭐ **A reggere l'attribuzione non è il totale: sono i tratti.**
>
> ### ⛔⛔ E la lezione della sera: **quattro falsi rossi, e accusavano tutti lo stato NORMALE**
>
> Il confine vecchio · il disaccordo passo/strada · il tratto 1a in Q11 · `None == None` nello script
> di confronto. **Ogni volta il banco accusava il giro di controllo.**
>
> ⇒ ⭐ **Un falso rosso costa quanto un falso verde**: tutt'e due scollegano il colore dal fatto. La
> domanda gemella di `LEZIONI.md` §1.20 è *«e quando è NORMALE che quel confronto non torni?»*.
> ⚠ E uno dei quattro è stato curato **dopo** aver visto il rosso: l'agente lo **dichiara**, e dice
> che la ragione fisica era già scritta prima e che ha escluso **un tratto solo e nominato**.
>
> ⛔ **E due difetti veri, suoi**: ha **rotto il banco con una sua cura** (una variabile che
> ombreggiava un modulo — un giro intero perso), e il pid raccolto dalle cifre dell'indirizzo IP.
> ⭐ **In tutt'e due i casi il banco è MORTO o ha detto «non ho potuto guardare»** invece di
> consegnare numeri falsi.

> ### ⭐⭐⭐ IL NUMERO CHE MANCAVA: `input → vetro` = `[M]` **55,20 ms**, contro **89,86** senza la copia zero
>
> **−34,66 ms, il 39 %**, su due giri di seguito nella stessa mezz'ora tranquilla che condividono
> **tutto** tranne il binario: stessa tela (1456×888), stesso passo (5824), stessa finestra, stessa
> scena, stesso utente, e `macchina carica: false` **scritto dal banco** in tutt'e due.
> ⭐ E la copia zero **era accesa davvero**: il prodotto dichiara «strada **scheda**» oggi e «strada
> **memoria**» ieri, **col passo identico** — la strada si ribalta perché cambia il binario, non la
> tela.
>
> | | il tratto | IERI | ⭐ OGGI | Δ |
> |---|---|---|---|---|
> | **E** | ⭐⭐ codifica e ritorno | 26,56 | **10,27** | **−16,30** |
> | **C** | l'attesa del quadro nella scena | 27,67 | **11,78** | **−15,89** |
> | **D** | il quadro di Mutter | 16,33 | 16,01 | −0,32 |
> | | **T — l'anello intero** | **89,86** | ⭐ **55,20** | ⭐⭐⭐ **−34,66** |
>
> ⭐⭐ **E il conto torna con quello di F4 per un'altra strada**: il tratto 5 fa `[M]` **−62 %**
> (26,27 → 9,89); lui, sul suo tratto e **senza browser**, aveva `[M]` −72 %. Due banchi, due
> palchi, la stessa forma.
>
> ⭐⭐⭐ **E rende anche dove non è suo**: metà del guadagno — **15,89 dei 34,66 ms** — sta nel tratto
> **3**, che è **sul server** e che la copia zero non attraversa nemmeno. `[?]` La spiegazione più
> economica è la smentita di F4 a §4-C: il produttore tolto dal thread di tempo reale di PipeWire
> (`[M]` 5,44 → 0,64 ms). **Ipotesi dichiarata, non misurata.**
>
> ⭐ **E il giro di oggi è il primo interamente verde che questo banco abbia mai prodotto**: 12
> controlli su 12, **Q5 e Q6 compresi**.
>
> ⚠ **Il resto del rapporto (F1.1-F1.4) resta com'è scritto** e dice altre due cose che non vanno
> confuse con questa: come il banco è arrivato a leggere la strada vera, e **quanto la contesa
> sposta un anello**. ⛔ I 74-76 ms che ci si trovano **non sono il «prima» della copia zero** —
> vedi l'avvertenza in F1.5.

### ⭐⭐ E LA SECONDA COSA CHE HO TROVATO STASERA — arrivandoci per un'altra strada che F3

> ### ⛔⛔⛔ **Il «prima» di A non è un termine di paragone**, e il perché è il carico
>
> Il mio mandato era rifare `input → vetro` sulla strada vera e affiancarlo ai **99,07 ms** di A.
> ⛔ **L'affiancamento non si può fare**, e non perché il banco non ci arrivi: perché il numero di A
> **porta dentro la contesa**. F3 l'ha dimostrato con tre banchi; io ci sono arrivato senza cercarlo,
> e le due strade si incontrano sullo stesso numero.
>
> `[M]` **Il tratto 9 — «l'attesa che il fotogramma sia utilizzabile», i 17,48 ms su cui §A.2 punto 2
> fonda la sua conclusione più citata — vale 0,71 ms.** E non lo dico solo io:
>
> | chi lo misura | quanto | come |
> |---|---|---|
> | il **banco** (il mio prologo) | **0,715** e **0,835 ms** | dal richiamo del decodificatore alla risoluzione di `createImageBitmap` |
> | ⭐⭐ il **PRODOTTO**, da sé | **0,710** e **0,830 ms** | `src/pagina.html`, `bmp_ms` — un lettore scritto da un'altra persona, in un altro posto, che non sa che il banco esiste |
> | F3, tre banchi indipendenti | **0,39 – 1,18 ms** | fra cui **sulla stessa strada 2D di A** |
>
> ⇒ ⭐⭐⭐ **Scarto fra il banco e il prodotto: `[M]` +0,005 ms. Due giri, due volte lo stesso scarto.**
>
> ⛔ **E la mia misura dice anche PERCHÉ, senza che io lo cercassi.** Quattro giri, stesso banco,
> stesso palco, stessa sera, stessa scena, stesso binario del prodotto:
>
> | giro | `input → vetro` | `[R]` sul portatile c'era anche… |
> |---|---|---|
> | `08f1-strada-vera-prova` | **74,08 ms** | solo il mio banco |
> | `08f1-fase-del-quadro` | **75,81 ms** | solo il mio banco |
> | `08f1-strada-vera-4` | **84,22 ms** | ⛔ **il banco di un altro agente** (porte 7765-67) |
> | `08f1-strada-vera-3` | **90,87 ms** | ⛔ **il banco di un altro agente** |
>
> ⇒ ⛔⛔ **Da 8 a 17 ms di differenza sullo stesso anello, e a cambiare non era il prodotto: era chi
> altro girava sul portatile.** ⚠ È `[R]` e non `[M]`, perché il banco quel carico **non lo scriveva
> da nessuna parte** — ed è esattamente il difetto che ho poi curato.
>
> ⭐ **Quel che invece regge intero è il BANCO**: da oggi legge la strada che il prodotto usa davvero,
> e il suo confine di chiusura **non è più una promessa** (F1.2).

### ⛔⛔ E la lezione che porto io è diversa da quella di F3

F3 dice: *il numero era la contesa*. ⭐ Io aggiungo la cosa che l'ha resa invisibile, e che è del
banco, non della macchina:

> **Il banco dichiarava NOVE voci di palco — codec, profondità, GPU, tela, monitor, WebCodecs,
> isolamento, scena, `wl_surface.enter` — e NON UNA sul carico.**

⇒ `LEZIONI.md` §2.0 lo chiedeva già: *il palco si dichiara accanto al numero*. ⛔ Ma un palco
descritto voce per voce e un carico mai nominato fanno un numero che **sembra** completamente
dichiarato. È `LEZIONI.md` §1.20 dalla parte di chi legge: nove numeri stampati fanno credere che il
decimo sia stato guardato.

⇒ ⭐ **Curato, e sta nel banco**: `carico_della_macchina()` legge ai **due capi** (il portatile, dove
stanno Chrome e il banco; il server, dove sta il prodotto), **due volte** — prima e dopo il giro — e
scrive nuclei, carico, processi Chrome, Xvfb, **quanti altri banchi `04-b30` stanno girando e su
quali porte**. Se non è scarica **lo dice in rosso**, con la misura che lo giustifica accanto, e la
riga finisce nell'`esiti.jsonl`.

⛔ **E la soglia guarda il carico DEGLI ALTRI, non il mio**, perché `[M]` un giro solo di questo banco
tiene già **~3,7 nuclei su 4 e ~29 processi Chrome**: una soglia sul carico assoluto sarebbe rossa
sempre, e una bandiera sempre rossa non la guarda più nessuno. ⇒ Si accusa quel che non è mio: un
secondo banco, un secondo Xvfb, o un numero di Chrome che un banco solo non può spiegare — soglia
**40**, e ⚠ `[M]` quando A misurava ce n'erano **56**, con **5 Xvfb**.

---

## F1.0 ⭐ Il banco si è ricertificato, e la certificazione è cresciuta

`[M]` `--certifica` ⇒ **PROMOSSO, 57 controlli su 57, 18 guasti innestati accusati su 18**
(A ne aveva 53 e 16). I controlli e i due guasti nuovi sono tutti di **Q11**, il controllo del
confine.

⭐ E prima di quello, una prova che il banco non aveva mai avuto: **il prologo provato senza
browser**. Il prologo è una stringa che vive dentro Chrome e non si può esercitare a pezzi; l'ho
estratto e fatto girare in `node` contro un finto browser che imita la pagina vera —
`createImageBitmap` asincrona, `ImageBitmapRenderingContext`, `VideoDecoder`, una tela:
`[M]` **16 controlli su 16** (`f1-prova-prologo.js`). ⛔ E il quarto blocco pretende che **la strada
2D non si sia rotta**: 5 fotogrammi, 2 `drawImage` ciascuno, `t_dip == t_dip_vecchio`.

---

## F1.1 ⭐⭐ COME IL BANCO LEGGE LA STRADA VERA

⛔ Il difetto di §A.4 punto 1 era **doppio**, e le due metà si curano insieme o non si curano:

| | il difetto | la cura, e dov'è |
|---|---|---|
| **1** | il prologo legge i pixel dal **deposito 2D**, che su `bitmaprenderer` **non esiste** ⇒ `[M]` 0 marche lette su 304 | ⭐ **si leggono dal VETRO**. Il contesto `bitmaprenderer` non ha `getImageData` — non dà nessun accesso ai pixel — ⛔ **ma la tela sì**: un `<canvas>` è una sorgente valida per `drawImage` qualunque sia il contesto che lo dipinge. ⇒ Il banco ricopia la **sola regione della marca** (480×240) su una tela di servizio 2D e la rilegge di lì (prologo §6, `leggi_marca_vetro`) |
| **2** | ⛔⛔ `createImageBitmap` è **asincrona**: il richiamo del prodotto **ritorna prima** che sia stato dipinto qualunque cosa ⇒ il confine «scomodo» era diventato **più comodo del comodo**, e nessuno l'aveva deciso | ⭐ il campione **non si chiude più nel richiamo del decodificatore**: si apre lì e si chiude in **`transferFromImageBitmap`**, cioè quando lo schermo cambia |

⭐ **Funziona, e il denominatore lo dice**: `[M]` **555 sonde chiuse su 555** al primo giro sulla
strada vera (A ne aveva chiuse **0 su 304**), **1424 marche lette su 1424 guardate** (Q3), e Q4(a)
`[M]` **251 fotogrammi guardati dove la marca dell'eco non c'è → 0 falsi positivi**: la lettura dal
vetro **discrimina**, non dice sempre sì.

### ⭐ I tre dettagli che fanno la differenza fra una cura e un'approssimazione

1. ⛔ **`createImageBitmap` si avvolge SENZA incatenare.** Il banco registra il proprio gestore sulla
   promessa e restituisce **quella originale**, non `p.then(...)`: incatenarla infilerebbe un
   microtask del banco fra la risoluzione e il gestore del prodotto — cioè **il banco ritarderebbe
   quel che misura**.
2. ⛔ **L'immagine si lega al fotogramma col `pts` ANNUNCIATO**, non con l'ordine di risoluzione:
   l'ordine è una grandezza sostitutiva (`LEZIONI.md` §1.13), e `createImageBitmap` non promette di
   risolvere in ordine — è la ragione per cui il prodotto stesso conta le `tardive`.
3. ⛔ **I pixel si leggono DOPO il trasferimento**, non dall'`ImageBitmap` prima: leggere prima
   vorrebbe dire leggere qualcosa che sullo schermo non c'è ancora — e per giunta ritardarlo.

### ⭐ E la strada non si dichiara: si DEDUCE

Ogni campione porta un campo `strada`, riempito da quel che è **successo**. `coda_url` è
l'intenzione, `strade` è il fatto — e adesso stanno **tutt'e due nella riga depositata** in
`04-b30-esiti.jsonl` (era il difetto minore n. 5 di §A.4: `[M]` tutte le 11 righe depositate prima di
oggi, comprese le cinque di A, hanno `coda_url: null`).

⛔ **E la prima stesura di quel campo aveva un difetto che ho trovato e curato**: marcavo «2d» ogni
fotogramma su cui non avevo visto una chiamata a `createImageBitmap`. `[M]` In un giro ne sono usciti
**235 su 2022** — con la strada 2D mai usata. ⇒ Erano fotogrammi che il prodotto ha **decodificato e
mai dipinto** (scartati perché tardivi). ⚠ **Non sporcano nessun numero** — l'ho verificato: zero
`drawImage`, zero celle, e **nessuno di loro ha chiuso una sonda** — ⛔ ma chiamarli «2d» era
scambiare *«non è successo»* con *«è successa l'altra cosa»*, la stessa forma di «non arrivato» ≠
«non guardato». ⇒ Adesso lo stato è **terzo e si chiama `non dipinto`**, e contato per quel che è
dice una cosa del prodotto: `[M]` **l'11,6 % dei fotogrammi decodificati non è arrivato al vetro**
in quel giro.

---

## F1.2 ⭐⭐⭐ IL CONTROLLO POSITIVO — e ha corretto ME

⛔ **Un banco riadattato che dà un numero plausibile non è un banco che funziona.** Il banco innesta
`--ritardo-vetro N`: N ms **dentro la pagina**, fra «il fotogramma è pronto» e «il fotogramma è al
vetro». Se il confine si chiudesse prima del disegno, quel ritardo sarebbe **invisibile**.

### ⛔⛔ La prima stesura del controllo era SBAGLIATA, e a bocciarla è stata la misura

Avevo scritto la pretesa così: *«il confine VECCHIO — il ritorno del richiamo — NON deve salire»*.
⛔ **È falsa, e il mondo vero l'ha rifiutata al primo giro**: `[M]` con 8 ms innestati il confine
vecchio è salito di **6,82 ms** e il totale di **14,81** invece che di 8.

`[R]` **E la ragione è fisica, non è un difetto del metro**: il ritardo si innesta **occupando il
filo della pagina** — che è quel che fa un disegno costoso — e quel tempo ritarda anche la consegna
degli **eventi di input**, che stanno sullo stesso filo. ⇒ Si sposta tutto il condotto, e su una
mediana sola quello spostamento è **indistinguibile** dal ritardo innestato.

⇒ ⭐⭐ **La grandezza giusta è APPAIATA**: la distanza fra il confine vero e quello sbagliato presa
**sulla stessa sonda, sullo stesso fotogramma**. Lo spostamento del condotto colpisce i due capi in
modo identico e **si elide**; resta solo il ritardo innestato.

### ⭐⭐⭐ E il numero, ripetuto TRE volte in tre giri diversi

| giro | distanza a ritardo 0 | col ritardo di **8,000** | **salita** | ⛔ **il MINIMO** | sonde |
|---|---|---|---|---|---|
| `08f1-fase-del-quadro` | 0,085 ms | 8,090 | **+8,005** | **8,045** | 476 |
| `08f1-strada-vera-3` | 0,080 | 8,095 | **+8,015** | **8,045** | 470 |
| `08f1-strada-vera-4` | 0,100 | 8,095 | **+7,995** | **8,040** | 833 |

⇒ ⭐⭐⭐ **Scarto massimo dal ritardo innestato: 0,015 ms.** E il **minimo** della distribuzione è
sopra 8,04 in tutt'e tre: su **1 779 sonde su 1 779** non ce n'è **una sola** che non veda il
ritardo. ⛔ Un banco che chiudesse al ritorno del richiamo darebbe **0,09 in ogni riga**, e la sua
mediana salirebbe lo stesso: è per questo che la riga appaiata è la prova e la mediana no.

⭐ E le altre due pretese reggono da sole: `[M]` la salita sta **nel tratto 10 (+7,995 / +8,005 /
+8,015 su 8,0) e in nessun altro tratto** (`e_anche_altrove: []`), e il totale sale **di almeno N**.

### ⛔⛔ E LA COSA CHE VA DETTA CONTRO ME STESSO: la catastrofe che A temeva **non c'era**

`[M]` Sulla strada vera i due confini distano **0,08 – 0,10 ms**. `createImageBitmap` risolve in
`[M]` **0,71 ms** e `transferFromImageBitmap` costa `[M]` **0,06**. ⇒ Il banco vecchio, se avesse
potuto leggere i pixel, avrebbe consegnato un numero **più corto di un decimo di millisecondo**, non
di venti.

⇒ ⭐ **La seconda metà del difetto di §A.4 era vera come MECCANISMO e piccola come QUANTITÀ**, e le
due cose si dicono insieme: il meccanismo è dimostrato (gli 8 ms innestati stanno per intero dentro
quel divario, e il confine sbagliato ne perde 8 su 8); la quantità su *questo* palco è 0,09 ms.
⛔ Non è una ragione per lasciare il confine dov'era — è la ragione per cui **si misura invece di
stimare**. E nessuno dei due numeri era deducibile prima.

### ⭐⭐ IL CONTROLLO INCROCIATO — e porta un avvertimento per tutti

Il prodotto misura da sé le stesse due grandezze dei tratti 9 e 10 (`bmp_ms`, `vetro_ms`). Il banco
adesso le porta fuori accanto alle proprie:

| | il PRODOTTO | il BANCO | |
|---|---|---|---|
| **tratto 9** (`createImageBitmap`) | **0,710** · **0,830** ms | **0,715** · **0,835** | ⭐⭐ scarto **+0,005** due volte su due |
| tratto 10 (`transferFromImageBitmap`) | 8,04 · 9,86 ms | 0,05 · 0,065 | ⛔ **NON è un disaccordo** |

⛔⛔ **E il tratto 10 è la scoperta involontaria più importante che lascio.** `vetro_ms` del prodotto
cronometra `this.bm.transferFromImageBitmap(bmp)` — ma **il banco avvolge proprio quel metodo**, e
dentro l'involucro legge i pixel. ⇒ Il cronometro del prodotto **contiene il banco**.

⇒ ⛔⛔ **Finché questo banco è attaccato, il campo `vetro` del blocco diagnostico di `pagina.html`
non è il prodotto: è il prodotto più il banco.** Chi lo leggesse in un altro rapporto scriverebbe
`[M]` 8-10 ms per un trasferimento che ne costa 0,06. ⭐ Il banco adesso lo dichiara invece di
giudicarlo, e la differenza (**7,99** e **9,80**) è un **terzo parere sul costo del banco**, preso
dal prodotto e accostato a Q9 (**7,61** e **8,79**).

---

## F1.3 ⭐⭐ IL NUMERO DELLA STRADA VERA, E I SEI TRATTI AFFIANCATI A QUELLI DI A

⛔⛔ **Si legge con l'avvertenza in testa, non dopo**: la colonna di A **non è un «prima»
affidabile** (F3, e i miei quattro giri). Le due colonne stanno accanto perché il mandato le chiede
e perché il **profilo** — dove sta il tempo — è quel che serve a chi cura; ⛔ **le differenze non si
attribuiscono al prodotto.**

| | il tratto | A · 2D (5 giri) | ⭐ F1 · `bitmaprenderer` (4 giri) | Δ |
|---|---|---|---|---|
| **A** | **la pagina** — `event.timeStamp` → i byte escono | 7,65 ms | **5,14 ms** | −2,51 |
| **B** | **l'andata** — byte usciti → la scena riceve l'input | 7,25 ms | **8,58 ms** | +1,33 |
| **C** | **l'attesa del quadro nella scena** | 23,25 ms | **20,57 ms** | −2,67 |
| **D** | **il quadro di Mutter** | 16,36 ms | **16,40 ms** | **+0,04** |
| **E** | **codifica e ritorno** | 24,45 ms | **22,58 ms** | −1,86 |
| **F** | ⛔ **il cliente** — `decode()` → disegno finito | **18,83 ms** | ⭐ **2,43 ms** | ⛔ **−16,40** |
| | somma delle mediane | 97,79 | **75,71** | |
| | **T, mediana delle mediane** | **99,07** | **80,02** | −19,05 |

| tratto | A · 2D [min–max] | ⭐ F1 · `bitmaprenderer` [min–max] |
|---|---|---|
| 1a evento → il prodotto lo vede | 7,53 [7,04 – 15,04] | **4,95** [4,83 – 6,33] |
| 1b il prodotto lo vede → i byte escono | 0,12 | **0,19** |
| 2 byte usciti → la scena riceve | 7,25 [6,84 – 7,93] | **8,58** [8,16 – 8,90] |
| 3 la scena riceve → la scena disegna | 23,25 [13,86 – 28,28] | **20,57** [13,57 – 23,98] |
| 4 la scena disegna → cattura | 16,36 [16,23 – 16,39] | **16,40** [16,37 – 16,45] |
| 5 cattura → primo byte in pagina | 24,19 [20,05 – 26,17] | **22,25** [19,03 – 26,44] |
| 6 primo byte → ultimo byte | 0,24 | **0,34** |
| 7 stream completo → `decode()` | 0,10 | **0,15** |
| 8 `decode()` → richiamo del decodificatore | 1,09 | **1,53** |
| 9 ⛔ richiamo → **il fotogramma è pronto** | **17,48** [14,90 – 18,72] | ⭐ **0,71** [0,69 – 0,83] |
| 10 pronto → **il disegno è finito** | 0,10 | **0,06** |

### ⛔ Le quattro cose che questa tabella dice

1. ⛔⛔ **Il tratto 9 non è un bersaglio: `[M]` vale 0,71 ms**, e la conclusione di §A.2 punto 2 —
   *«il 1° `drawImage` costa 17,48 ms e il 2° 0,10: 163 volte»* — **va ritirata**. ⇒ **Chi stava per
   curare il tratto F stava per curare un tratto che pesa `[M]` 2,43 ms su ~80**, cioè il 3 %.
   ⭐ §A.5 lo temeva con parole sue: *«se il numero cambia, lo deve sapere prima di curarlo»*.
2. ⭐ **Il tratto D non si è mosso di quattro centesimi** (16,36 → 16,40), con la dispersione più
   stretta di tutte [16,37 – 16,45]. ⇒ Un tratto che resta identico quando cambia tutto il resto è
   la prova che la scomposizione separa cose diverse davvero — **e resta il muro**: un quadro di
   compositore esatto, `[M]` il 20 % dell'anello.
3. ⛔ **Le altre cinque differenze NON si attribuiscono**: stanno dentro la dispersione che A stesso
   aveva misurato (C fra 13,86 e 28,28) e dentro quella che la contesa produce sui miei stessi giri
   (8-17 ms sul totale). `[?]`
4. ⭐ **Il denominatore è migliore del suo**: `[M]` 463-829 sonde chiuse per giro contro 224-417, e
   la chiusura è del 99-100 % in tutti e quattro.

### ⛔ Il numero, e va letto col carico accanto

| | |
|---|---|
| ⭐ i due giri in cui `[R]` **ero solo sul portatile** | **74,08** e **75,81 ms** |
| ⛔ i due giri con il banco di un altro agente sopra | **84,22** e **90,87 ms** |
| ⛔⛔ **il numero che consegno** | `[M]` **74-76 ms** a macchina scarica, `[?]` **da riconfermare con il carico SCRITTO nel verbale**: la lettura del carico è entrata nel banco **dopo** questi quattro giri |
| contro `SPECIFICHE.md` §3.2 | **SFORA** i 50 ms e i 40, alla mediana e al p95 |

### ⚠ E il palco, accanto al numero

`[M]` codec **HEVC** `hev1.1.6.L120.B0`, **8 bit**, promozione 8→10 no · codifica **IN HARDWARE**
(`hevc_vaapi`, `/dev/dri/renderD128`, ⚠ **EncSliceLP**, confermato oggi) · tela **1460 × 888** ·
GPU della pagina `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` · WebCodecs sì · pagina isolata sì ·
scena su **Meta-0**, confermato da `wl_surface.enter`.
⇒ **È il palco di §A.1 voce per voce**, ed è voluto: stesso albero del prodotto
(`/media/REMOTIX/src/08-a-src`, `md5sum` di `pagina.html` verificato), **stesso binario della scena**
(`md5sum` identico), stesso utente. ⛔ Non ho ricostruito niente: ricostruire avrebbe cambiato un
capo del confronto senza dirlo.
⚠ ⭐ **E quindi il mio albero NON ha `REMOTIX.tratti()` di F3**, che è arrivato dopo (`md5sum` di
`src/pagina.html` a HEAD: `d387c166…`, il mio: `2fdf13a9…`). ⇒ Chi rifà questi giri col prodotto di
oggi ha uno strumento migliore del mio prologo, e deve saperlo.

### ⛔ I due pezzi ciechi

`[?]` **4-12 ms** in ingresso (mano → `event.timeStamp`) · `[?]` **16-40 ms** in uscita (disegno
finito → pixel acceso). ⛔ **E quelli in uscita ci sono**: `clienti_sull_xvfb: 0` ⇒ il browser sta sul
desktop vero del portatile, dove un compositore c'è. ⇒ Sullo schermo di un utente:
`[M]` 74-76 + `[?]` 20-52 = **94-128 ms**, **più la rete**.

### ⭐⭐ E il conto dell'elastico di §1.2 va rifatto

Il riquadro di §4-A moltiplicava `99,07 × 3 400 px/s = 337 px` contro i **360** che l'utente vede,
«entro il 7 %». ⛔ Col numero della strada vera quel prodotto fa **74,9 × 3 400 = 255 px**: **lontano
dai 360**. ⇒ ⭐ **Non è un difetto: è un'informazione.** O il distacco che l'utente vede contiene i
pezzi ciechi e la rete — e allora il conto giusto è `94-128 ms × 3 400 = 320-435 px`, che sui 360
torna — oppure guardava più veloce della sua mediana.
⛔⛔ **E l'accordo «entro il 7 %» di §4-A era un accordo con un numero gonfiato dalla contesa: va
tolto dal riquadro**, o resta a certificare il modello con la misura sbagliata.

---

## F1.4 ⭐⭐ I DUE DIFETTI CHE A HA LASCIATO SCRITTI

### 1. ⭐⭐ Q5 e Q6: **è curabile, e la cura è nella SCELTA DEL RITARDO** — non nel metro

§A.4 punto 2 dava l'ipotesi `[?]`: *«ritardare l'input ne cambia la FASE rispetto al quadro del
compositore»*, e chiudeva: *«chi la vuole `[M]` la prova innestando ritardi non multipli di 16,7»*.

⭐ L'ho provata **al contrario**, che è più forte: ritardi **multipli esatti** del quadro. Se
l'ipotesi è giusta la fase non cambia, e il tratto 3 **non si deve muovere**.

`[M]` **Stesso banco, stesso palco, stessa sera:**

| ritardo innestato | Q5 | Q6 | ⭐ dove va il surplus | ⛔ e il **tratto 3**? |
|---|---|---|---|---|
| **25 / 30 ms** (non multipli del quadro) | **rosso** | **rosso** | tratto 5: **+23,12** su 25 · tratto 2: **+29,62** su 30 | ⛔ **−6,18** e **−5,66 ms** |
| ⭐ **33,4 / 33,4** (= **due quadri esatti**) | rosso di **0,22** | ⭐ **VERDE** | tratto 5: **+32,94** su 33,4 · tratto 2: **+33,34** su 33,4 | ⭐ **non si muove**: `e_anche_altrove: []` |

⇒ ⭐⭐⭐ **L'ipotesi di A è confermata e diventa `[M]`.** Il tratto 3 **si compensa** quando il
ritardo sposta la fase dell'input rispetto al quadro: non è contaminazione del metro, è il condotto
che si comporta davvero diversamente. E il surplus **sta nel tratto giusto in tutt'e quattro i casi,
entro 0,46 ms**.

⇒ ⭐ **La cura**: i ritardi da innestare vanno messi a **multipli del quadro** (16,7 ms).
⛔ **Non ho cambiato i valori di partenza del banco**, e la ragione è che **un altro agente aveva un
giro in volo su questo stesso file**: cambiargli sotto una taratura a metà esperimento gli avrebbe
cambiato il verdetto senza che lo sapesse. ⇒ **È una riga sola, e la passo al direttore.**

### 2. ⛔⛔ Il fatto sul 139,40 — riletto dalla FONTE, e ne esce di più

§A.4 punto 2 lo dichiarava. Io l'ho riletto da `04-b30-esiti.jsonl` (campo `controlli`) e ne esce
**il MODO del rosso**, che cambia la lettura:

| giro | Q5 | Q6 | ⛔ **come** falliva |
|---|---|---|---|
| 14 ago `b30-o2-finale` — ⛔ **il 139,40** | **rosso** | **rosso** | Q5: salita **15,79 su 25** (−9,21) e **il tratto 2 va −14,19**; Q6: tratto giusto, totale +6,29 |
| 14 ago `b30-o2-finale2` — il 141,60 | **rosso** | verde | salita 20,78 su 25, tratto 2 **−7,17** |
| 22 ago `08a-tela2d-adattano-1` | verde | verde | ⭐ l'unico con tutt'e due verdi |
| 22 ago `08a-tela2d-5` — **il 99,07** | **rosso** | verde | tratto giusto, salita 30,59 su 25 |

⇒ ⛔⛔ **Il 139,40 non è solo «consegnato con due tarature rosse»: è consegnato da un giro in cui il
tratto 2 si muoveva di −14,19 ms sotto un ritardo iniettato altrove.** Su 139 è il 10 %.
⚠ Il totale resta quel che è — misurato ai due capi con lo stesso orologio — ⛔ ma **la sua
scomposizione del 14 agosto va letta con questo accanto**, e nessun documento lo diceva.

### 3. ⚠ I tre difetti minori di §A.4 punto 5 — **curati, tutt'e tre**

| | |
|---|---|
| ⭐ **`coda_url` non arrivava nell'`esiti.jsonl`** | curato, e con **due** campi: `coda_url` (l'intenzione) e `strade` (il **fatto**). ⛔ Verificato che il difetto c'era: `[M]` tutte le 11 righe depositate prima di oggi hanno `coda_url: null` |
| ⭐ **`scena-costruisci` di `04-b30-lancia.sh` rotto** | curato: la costruzione sta in un **file** (`banchi/04-b30-scena-costruisci.sh`), non in una riga che attraversa `ssh → enter.sh → bash -c`. ⭐ La regola era **già scritta** nell'intestazione dello stesso file — *«un file non ha livelli di virgolette»* — solo che il codice non la seguiva. Il file nuovo verifica anche che il binario non sia vuoto prima di rinominarlo |
| ⭐ **la scena vecchia non lascia il fuoco** | curato **dentro il banco**: `giro_vero()` chiama `scena-ferma` **prima** di `scena-avvia`. ⚠ Prima il rimedio stava «nella testa di chi lo lancia», ed è così che A ha perso il suo primo giro |

### 4. ⭐ E un contributo a `LEZIONI.md` §1.24, che F3 ha pagato oggi

Ho verificato le mie risorse su **ogni** asse, non solo la porta:

| | mie | altrui, contate |
|---|---|---|
| porte | **7760 · 7761 · 7762** | 7730/7731 (l'utente) · 7746 · 7752 · 7765-67 |
| utente / uid | **provaa8 / 1041** | provaf8/1044 · provaf48/1046 · provaf3/1047 · provac8 · provab8 |
| shm | **remotix-08-f1** | remotix-08-f · -08-f3 · -08-f4 · -08-a/b/c |
| dir di lavoro | **/media/REMOTIX/tmp/08-f1** | 08-f · 08-f4 · 08-a/b/c |
| Xvfb / CDP | **:96 / 9660** | l'unico Xvfb vivo era il mio |

⛔ **E ne è uscita una forma che la lezione non copre ancora**: `08-f1` e `08-f` sono nomi diversi,
⛔ **ma uno è PREFISSO dell'altro**. Un `rm -rf /media/REMOTIX/src/08-f*` di chi possiede `08-f`
porterebbe via anche i miei, e nessuno dei due avrebbe sbagliato niente.
⇒ ⭐ **Non basta che i nomi siano diversi: devono essere non-prefissi l'uno dell'altro.** È una riga
per §1.24.
⚠ **E una sovrapposizione vera la dichiaro**: uso `provaa8`, l'utente di **A**, apposta — è l'unico
modo di avere il suo stesso palco. A è rientrato, quindi nessuno lo contende; ⛔ ma se qualcuno ne
riavviasse la sessione mentre misuro, la mia scena morirebbe. ⭐ Il banco lo direbbe («la scena non
prende il fuoco») invece di produrre un numero falso — l'ho verificato leggendo quel ramo.

---

## F1.5 ⭐⭐⭐ L'ANELLO INTERO CON LA COPIA ZERO — il prima/dopo **appaiato**

> ### ⭐⭐⭐ `input → vetro` passa da `[M]` **89,86 ms** a `[M]` **55,20 ms** — **−34,66 ms, il 39 %**
>
> Due giri di seguito, nella stessa mezz'ora tranquilla, che condividono **tutto** tranne il binario.

### ⛔ Prima del numero: era la copia zero, ed era accesa?

⛔⛔ La trappola peggiore sarebbe misurare il codice nuovo mentre percorre la strada vecchia, e non è
teorica: `[M]` (F4) il driver iHD **non onora un passo che non sia multiplo di 64 byte**. Il passo è
`larghezza × 4`, quindi la condizione è **larghezza multipla di 16 px**:

| tela | passo | resto su 64 | |
|---|---|---|---|
| **1460×888** — ⛔ il palco di **tutti** i giri precedenti | 5840 | **16** | ⛔ copia zero **spenta** |
| 1544×888 · 1560×888 (le tele storte di F4) | 6176 · 6240 | 32 · 32 | ⛔ spenta |
| ⭐ **1456×888** — il palco di stasera | **5824** | **0** | ⭐ **accesa** |
| 1920×1080 | 7680 | 0 | ⭐ accesa |

⇒ ⭐⭐ **1456 e non 1920, e la ragione è il confronto**: è il multiplo di 16 più vicino a 1460, cioè
**quattro pixel** dal palco di sempre invece dei **+63 % di pixel** che 1920×1080 avrebbe portato
dentro. ⭐ E il conto riproduce i casi che F4 ha misurato: 1544 e 1560 → resto 32 (storte), 1920 → 0
(buona). Due strade, stesso risultato.
⭐ La leva è **la finestra del browser** (`--finestra 1496x1000`, argomento nuovo): la pagina chiede
al server una tela grande quanto la sua vista.

### ⭐ E che i due giri siano confrontabili non si spera: **il banco lo verifica**

| | **IERI** (senza) | ⭐ **OGGI** (copia zero) |
|---|---|---|
| albero | `/media/REMOTIX/src/08-a-src/src/remotix` | `/media/REMOTIX/src/08-f1-src/src/remotix` |
| **md5 del binario CHE GIRA** (da `/proc/PID/exe`) | **`73ce3a1f19028c8e7436db9d2125ded2`** | **`f45e9f789782e316da6efc7e409e4625`** |
| sorgenti | il tronco del 22 agosto mattina | HEAD `6f5f418`, `cattura.c` `c17a7838…` verificato |
| **copia zero**, letta dal registro del PRODOTTO | ⛔ **SPENTA** — «strada **memoria**» | ⭐ **ACCESA** — «strada **scheda**» |
| tela · passo · resto su 64 | 1456×888 · 5824 · **0** | **identici** |
| finestra | 1496×1000 | **identica** |
| carico del portatile, `[M]` **nel verbale** | carico **0,40** · Chrome 13 · Xvfb 1 · **un solo banco** | carico **1,10** · Chrome 13 · Xvfb 1 · **un solo banco** |
| `macchina carica` | **false** | **false** |

⇒ ⭐⭐ **Il passo è identico e buono in tutt'e due**: la strada si ribalta da `memoria` a `scheda`
**perché cambia il binario**, non perché cambi la tela. È il controllo più pulito che potessi
costruire.
⚠ **L'impronta l'ho letta a mano** (`sudo md5sum /proc/PID/exe`): nel verbale non c'è, perché la
lettura automatica si è rotta due volte stasera (F1.6). ⇒ `[M]` ma per mano mia, non per mano del
banco — e la distinzione la scrivo invece di nasconderla.

### ⭐⭐ I SEI TRATTI AFFIANCATI — è la sola cosa che dice **quale pezzo ha reso**

| | il tratto | IERI (senza) | ⭐ OGGI (copia zero) | Δ |
|---|---|---|---|---|
| **A** | la pagina — `event.timeStamp` → i byte escono | 2,08 ms | 5,68 ms | ⚠ **+3,60** |
| **B** | l'andata — byte usciti → la scena riceve | 9,19 ms | 6,68 ms | −2,51 |
| **C** | l'attesa del quadro nella scena | 27,67 ms | **11,78 ms** | ⭐ **−15,89** |
| **D** | il quadro di Mutter | 16,33 ms | 16,01 ms | **−0,32** |
| **E** | ⭐⭐ **codifica e ritorno** | 26,56 ms | **10,27 ms** | ⭐⭐ **−16,30** |
| **F** | il cliente | 2,11 ms | 2,48 ms | +0,38 |
| | **T — L'ANELLO INTERO** | **89,86 ms** | ⭐ **55,20 ms** | ⭐⭐⭐ **−34,66** |
| | **p95** | 157,25 | **122,50** | **−34,75** |
| | n (sonde chiuse / tentate) | **476 / 476** | **721 / 727** | |

| tratto | IERI | OGGI | Δ |
|---|---|---|---|
| 1a evento → il prodotto lo vede | 1,90 | 5,53 | ⚠ +3,63 |
| 1b · 6 · 7 · 8 · 9 · 10 | 0,19 · 0,29 · 0,12 · 1,31 · 0,62 · 0,05 | 0,15 · 0,38 · 0,16 · 1,55 · 0,72 · 0,06 | ≈ 0 |
| 2 byte usciti → la scena riceve | 9,19 | 6,68 | −2,51 |
| 3 la scena riceve → la scena disegna | 27,67 | **11,78** | ⭐ **−15,89** |
| 4 la scena disegna → cattura | 16,33 | 16,01 | −0,32 |
| **5 cattura → PRIMO byte in pagina** | **26,27** | ⭐⭐ **9,89** | ⭐⭐ **−16,38** |

### ⭐⭐⭐ Le quattro cose che questa tabella dice

1. ⭐⭐ **Il tratto 5 è la firma della copia zero, e il conto torna con quello di F4.**
   `[M]` **26,27 → 9,89 ms, −62 %**. F4, sul suo tratto `cattura → byte fuori` e senza browser,
   aveva `[M]` **22,82 → 6,41, −72 %**. ⇒ **Due banchi diversi, due palchi diversi, la stessa cura,
   la stessa forma.** È la conferma incrociata che al numero di F4 mancava.
2. ⭐⭐⭐ **E rende ANCHE nel tratto 3, che non è suo** — `[M]` **27,67 → 11,78, −15,89 ms**. Il
   tratto 3 è *«la scena riceve l'input → la scena disegna»*, cioè **l'attesa del quadro sul
   server**: la copia zero non ci passa nemmeno. ⇒ `[?]` **La spiegazione più economica è la
   smentita di F4 a §4-C**: togliendo il nostro lavoro dal thread di **tempo reale di PipeWire** il
   produttore cala `[M]` 5,44 → 0,64 ms, e il compositore torna a servire la scena in tempo. ⛔ È
   un'**ipotesi**, non una misura: la prova sarebbe rifarlo con la copia zero accesa e il produttore
   riportato a mano sul thread di tempo reale. **Non l'ho fatto.**
   ⚠ E metà del guadagno dell'anello sta lì: **15,89 dei 34,66 ms**.
3. ⭐ **Il tratto D non si muove** (16,33 → 16,01, −0,32): il quadro del compositore resta il muro, e
   un tratto che non cambia quando tutto il resto cambia è la prova che la scomposizione separa cose
   diverse davvero.
4. ⚠ **Il tratto 1a peggiora di 3,6 ms**, ed è l'unico. `[?]` Il giro di oggi aveva il carico a
   **1,10** contro **0,40** di ieri — il tratto 1a è la consegna degli eventi sul filo della pagina,
   ed è il primo a soffrire il carico. ⛔ Non lo attribuisco alla copia zero e non lo nascondo.

### ⛔⛔ COME SI LEGGE QUESTO CONFRONTO, E COME NON SI LEGGE

⚠ **Il confronto buono è questo, e solo questo.** ⛔ **NON si sottrae il 55,20 dai 74-76 ms** dei miei
giri precedenti, e la tentazione è forte perché i numeri stanno nello stesso documento. Quei giri
erano su un'**altra tela** (1460×888, dove la copia zero **non si accende nemmeno**), col carico
`[R]` invece che `[M]`, e due dei quattro sotto la contesa di un altro banco.
⇒ ⭐ **Il «prima» buono è `08f1-copiazero-IERI-2`, non i 74-76.** Quelli restano scritti perché
dicono un'altra cosa — quanto la contesa sposta un anello — e quella la dicono bene.

⛔⛔ **E c'è un limite del mio stesso confronto che va detto**: `[M]` sullo **stesso** binario di ieri
ho tre giri — **74,08 · 75,81 · 89,86** — cioè **~15 ms di dispersione da giro a giro**. ⇒ Con
**un solo giro per parte**, i −34,66 ms sono più grandi della dispersione ma **non di un fattore
comodo**. ⭐ **A rendere credibile l'attribuzione non è il totale: sono i tratti.** Il tratto 5 cala
del 62 % e concorda con F4 misurato per un'altra strada; gli altri nove non si muovono. ⛔ Chi vuole
il totale `[M]` con la dispersione dentro deve fare **tre giri per parte, alternati**, ed è mezz'ora.

⚠ E oltre a questo: `[?]` non ho fatto una prova che la copia zero **spenta sulla stessa tela storta**
desse il numero di ieri — cioè la controprova del meccanismo dal lato del driver.

---

## F1.6 ⛔⛔⭐ QUATTRO FALSI ROSSI IN UNA SERA — e **un falso rosso costa quanto un falso verde**

⭐ Il pezzo di questa serata che vale più del numero, e non è un aneddoto: **quattro volte** ho
scritto un controllo che accusava uno **stato normale**, e ogni volta la cura è stata la stessa —
distinguere *«non è successo»* da *«è successo il contrario»*, e *«non ho guardato»* da *«ho
guardato e va male»*.

| | il controllo | perché accusava lo stato NORMALE | la cura |
|---|---|---|---|
| **1** | Q11: *«il confine vecchio non deve salire»* | il ritardo si innesta **occupando il filo della pagina**, quindi sposta **tutto** il condotto: `[M]` +6,82 ms sul confine vecchio | la grandezza giusta è **appaiata** (distanza fra i due confini sulla **stessa sonda**): lo spostamento comune si elide |
| **2** | passo/strada: *«copia zero spenta con passo buono = disaccordo»* | il passo multiplo di 64 è **necessario e non sufficiente** — serve anche il codice. ⇒ «passo buono + strada memoria» è lo stato **corretto** del binario di prima della cura, cioè **del giro di controllo** | si accusa **un verso solo**, quello impossibile (strada «scheda» con passo storto); l'altro si **dichiara** con una nota |
| **3** | Q11: *«la salita sta nel tratto 10 e in nessun altro»* | `[M]` il tratto **1a** sale di **5,60 ms**, perché 1a è la consegna degli eventi **sullo stesso filo** in cui innesto il ritardo | si esclude **un tratto solo, nominato, per la ragione detta** — e la ricaduta si **conta e si consegna**, non sparisce |
| **4** | il mio script di confronto: *«stesso md5 ⇒ nessun prima/dopo»* | `None == None` è vero: con l'impronta non letta diceva **«stesso binario»** invece di **«non ho potuto guardare»** | «non l'ho letta» diventa un `⚠` distinto dal rosso |

⇒ ⭐⭐ **Il danno non è che sbagliano: è che accusano il caso che deve andare bene.** Il giro di
controllo — quello che *deve* uscire senza copia zero, perché è il termine di paragone — sarebbe
uscito rosso ogni volta. ⛔ **E un rosso che compare quando tutto va come deve è il modo più rapido
di insegnare a chi legge che i rossi di questo banco si ignorano.**

⇒ ⛔⛔ **Un falso rosso costa esattamente quanto un falso verde, e per la stessa via**: tutt'e due
scollegano il colore dal fatto. `LEZIONI.md` §1.20 chiede *«per ogni numero che il banco stampa:
quale riga lo confronta?»* — ⭐ **e la domanda gemella, che stasera mi è costata quattro volte, è
«e quando è NORMALE che quel confronto non torni?»**.

⚠ **E il numero 3 l'ho curato DOPO aver visto il rosso**, che è il momento più pericoloso per
toccare un criterio. ⇒ Lo dichiaro: la ragione fisica era scritta in questo stesso file **prima**
che il rosso comparisse (F1.2, sul totale), e ho escluso **un tratto solo e nominato**, non «i
tratti che davano fastidio». Tutti gli altri restano accusabili: se il surplus finisse nel 2, nel 3
o nel 5, Q11 diventa rosso.

### ⛔ E due difetti veri del banco, trovati mentre lo curavo

1. ⛔⛔ **Ho rotto il banco con una mia stessa cura, e mi è costato un giro intero.** Curando la
   lettura dell'`md5` ho scritto `p = x.split()` — e in quella funzione **`p` è già il modulo del
   ponte**. Sette passi più giù `p.orologio_chiedi(...)` trovava una lista, e il giro moriva **ad
   ancora chiusa, dopo aver misurato tutto**.
   ⭐ E il difetto era **invisibile** nel giro precedente, perché lì la lettura dell'`md5` falliva e
   il ciclo non girava mai: **una riga curata ne ha rotta un'altra a distanza**.
   ⚠ L'unica cosa che ha funzionato come doveva: il banco è **morto** invece di consegnare un numero.
2. ⛔ **`"".join(c for c in stdout if c.isdigit())`** per prendere il `pid`: nello `stdout` di `sshpw`
   c'è anche *«nicfio@**192.168.0.2**'s password:»*, e il pid usciva `1921680`+quello vero.
   ⭐ Anche qui il banco ha detto **«NON HO POTUTO GUARDARE: "non lo so" non è "è quello giusto"»**
   invece di inventare un'impronta — ed è l'unica ragione per cui il difetto è costato una riga e non
   un numero falso in un documento.
   ⚠ ⛔ **È la terza volta in una sera** che un comando muore attraversando `ssh → sudo → pipe`: la
   regola di casa *«un file non ha livelli di virgolette»* vale anche per le righe brevi.

---

## F1.7 ⛔⛔ CHE COSA NON HA FUNZIONATO (il resto)

### 1. ⛔⛔ La prima stesura di Q11 era SBAGLIATA, e a bocciarla è stata la misura
⚠ **E il finto non l'avrebbe mai bocciata**: nel finto il ritardo al vetro non occupa nessun filo,
quindi il condotto non si sposta. ⇒ Un banco consegnato dopo la sola certificazione sarebbe uscito
**verde sul finto e falso sul mondo**. È la ragione per cui la certificazione non basta.

### 2. ⛔ Il banco costa **5,5 volte più di prima**
`[M]` la lettura dei pixel: **1,59 ms** dal deposito 2D (giro di A) contro **7,61 – 8,79 ms** dal
vetro. ⇒ Leggere dal vetro è una **lettura dalla GPU**, e si paga.
⭐ Q9 resta verde e non è una concessione: `[M]` il ritmo **non cala** (29,88 senza contro 30,46 con;
A: 30,67 contro 30,25) ⇒ il filo non è saturo a 30 fps. ⛔ Ma «non satura» non è «gratis»: resta in
F1.8.
⭐ **E la cura per chi viene dopo è trovata e non applicata, apposta**: le due marche stanno **una
sopra l'altra**, quindi si leggerebbero con **una sola** `drawImage` sul riquadro che le contiene
tutt'e due. ⛔ Non l'ho fatto perché i giri erano cominciati: **cambiare il metro a metà della
misura** è il difetto che questa fase sta curando.

### 3. ⛔ La TASTIERA non chiude **niente**
`[M]` **276 messaggi sul filo, 276 sonde, 0 CHIUSE.** §A.4 punto 3 dava 0/208 · 0/212 · 8/196 ·
5/202 · 16/198. ⇒ Sulla strada vera è **0 su 276**. ⛔ **Nessun documento deve citare un ritardo di
tastiera preso da questo banco.** `[?]` Se sia la scena, l'eco o la finestra di 500 ms **non l'ho
aperto**.

### 4. ⛔ Q5 resta rosso anche coi ritardi a quadro intero, di **0,22 ms**
La diagnosi è giusta (il surplus è nel tratto 5, +32,94 su 33,4, e in nessun altro); è la mediana del
**totale** a salire di 37,62. `[?]` Non ho separato rumore e contesa.

### 5. ⛔ Il palco NON era isolato, e va detto perché è il cuore di tutto
⚠ **E c'è una conseguenza che non è solo rumore**: le mie modifiche a `04-b30-anello-input.py` sono
entrate in vigore **mentre un giro di un altro agente era in volo** — in particolare
`--ritardo-vetro`, che aggiunge una **quarta condizione** a ogni giro. ⇒ Il suo giro è durato un
quarto in più di quel che si aspettava, e il suo Q11 può comparire in un verbale che non lo
prevedeva. **La colpa è mia e la dichiaro**; il file del banco è di tutti e non c'era modo di curarlo
senza toccarlo.

### 6. ⛔ Un solo valore di ritardo al vetro, non due
Ho provato **8 ms**, tre volte in tre giri (scarto 0,005 · 0,015 · 0,005). ⛔ **Non ho fatto la
linearità** con un secondo valore. ⚠ Sopra ~16 ms il filo si satura e i fotogrammi si **buttano**
invece di ritardare — cioè si misurerebbe un'altra cosa. `[?]` Fra 4 e 12 ms lo spazio c'era.

### 7. ⛔ Il quinto giro **l'ho ammazzato io, a metà**
Su richiesta del direttore, per liberare il portatile a F4. ⇒ Ho quattro giri e non cinque, e i due a
macchina scarica sono **due**. ⭐ È la scelta giusta — un giro in più preso sotto contesa avrebbe
peggiorato la mediana invece di migliorarla — ⛔ ma il denominatore è quello che è.

---

## F1.8 ⛔ Che cosa resta `[?]` dopo di me

| | |
|---|---|
| ✅ ~~**il numero a macchina scarica, col carico SCRITTO**~~ | **FATTO** (F1.5): i due giri appaiati di stasera hanno `macchina carica: false` **scritto dal banco**, carico 0,40 e 1,10 su 4 nuclei, un solo banco b30. ⚠ **E la voce vecchia resta vera com'era scritta**: i quattro giri da 74-91 ms sono anteriori alla cura, il loro numero è `[M]` e il loro carico `[R]` |
| ⏳ ⛔ **quanto del numero è il banco stesso** | `[M]` **7,6-8,8 ms per fotogramma** di lettura. Il ritmo non cala (Q9) ⇒ il filo non è saturo, **ma su ~75 ms non è trascurabile**. ⚠ E non si separa con la fetta «senza lettura» di Q9: senza pixel **nessuna sonda chiude**. ⇒ Serve un giro con la lettura **dimezzata** (una `drawImage` sola): se `T` non cambia, il costo non entra |
| ⏳ ⭐⭐ **il conto dell'elastico** | 255 px contro i 360 che l'utente vede. Si decide **rimisurando il distacco oggi**, col video, sulla strada vera. ⛔ E intanto **l'accordo «entro il 7 %» di §4-A va tolto** |
| ⏳ **la TASTIERA** | 0 su 276 |
| ⏳ **Q5 a 0,22 ms dalla tolleranza** · **la linearità del confine** | F1.7 punti 4 e 6 |
| ⏳ `[?]` **i valori di partenza dei ritardi** | vanno messi a **multipli del quadro**: una riga, passata al direttore |
| ⏳ ⭐⭐ **il tratto 3, metà del guadagno, non è attribuito** | `[M]` −15,89 ms su un tratto che sta **sul server** e che la copia zero non attraversa. `[?]` L'ipotesi (il produttore fuori dal thread di tempo reale di PipeWire, F4) è plausibile e **non misurata**. ⇒ Si prova rimettendo il produttore a mano su quel thread con la copia zero accesa |
| ⏳ ⛔ **un solo giro per parte** | sullo stesso binario di ieri ho `[M]` 74,08 · 75,81 · 89,86 ⇒ **~15 ms di dispersione**. I −34,66 sono più grandi, ma **non di un fattore comodo**. ⇒ Tre giri per parte, alternati: mezz'ora |
| ⏳ **la controprova dal lato del driver** | `[?]` non ho provato che il binario NUOVO su una tela **storta** (1460×888) dia il numero di ieri — sarebbe la conferma del meccanismo del passo |
| ⏳ **l'impronta del binario nel verbale** | l'ho letta **a mano**; la lettura automatica è stata curata **dopo** i due giri, quindi nei loro verbali `md5` è `null` |
| ⏳ **`EncSliceLP`** | `[M]` il codificatore dichiara ancora **bassa potenza**: confermato oggi sul mio giro |

---

## F1.9 Che cosa ho lasciato sulla macchina

⭐ Porte **7760 · 7761 · 7762**, utente **`provaa8`** (quello di A), directory
**`/media/REMOTIX/tmp/08-f1`**, shm `/dev/shm/remotix-08-f1`, scena
`/media/REMOTIX/src/08-f1-scena-lav/08-f1-scena` (copia bit per bit di quella di A), terreno
`/media/REMOTIX/src/08-f1-terreno.sh`, ponte `/media/REMOTIX/src/08-f1-ponte.py`.
⛔ **Le porte 7730 e 7731 e le directory dell'utente non sono mai state toccate.**
⛔ **E non ho toccato nessun file di `src/`.**
⭐ **Il portatile è libero**: Xvfb e Chrome miei spenti, scena ferma.

⭐ **E l'albero del prodotto di oggi resta**: `/media/REMOTIX/src/08-f1-src` (HEAD `6f5f418`,
binario `f45e9f78…`), accanto a quello di ieri `08-a-src` (`73ce3a1f…`) che **non ho toccato**.
⇒ Chiunque può rifare il prima/dopo senza ricostruire niente, e i due terreni ci sono già:
`08-f1-terreno-OGGI.sh` e `08-f1-terreno-IERI.sh`.

I file del banco che ho cambiato, tutti in `banchi/`:
- `04-b30-anello-input.py` — il prologo §4-bis (`createImageBitmap` + `transferFromImageBitmap`) e
  §6 (`leggi_marca_vetro`), **Q11** e i suoi due guasti, `--ritardo-vetro`,
  **`carico_della_macchina()`** ai due capi e due volte, il controllo incrociato col prodotto,
  `scena-ferma` prima di `scena-avvia`, `coda_url` + `strade` + il carico nella riga depositata,
  ⭐ **`--finestra`** (la misura della finestra comanda la tela, e la tela comanda se la copia zero
  si accende), ⭐ **`strada_di_cattura()`** (la copia zero letta dal registro del PRODOTTO, col conto
  del passo accanto), ⭐ **l'impronta del binario** letta da `/proc/PID/exe`;
- `04-b30-lancia.sh` — `scena-costruisci`;
- **nuovo** `04-b30-scena-costruisci.sh`.


---

## 4-F3 · ⛔⛔⭐ AGENTE F3 — **i diciassette millisecondi non esistono**, e a mentire era la macchina · *22 agosto 2026*

> ### ⛔⛔⛔ E IL COLPEVOLE È IL DIRETTORE, NON IL PRODOTTO
>
> Il tratto 9 dell'agente A — *«richiamo del decodificatore → 1° `drawImage`»* — valeva `[M]`
> **17,48 ms**, il **19 %** dell'anello, ed era stato promosso a bersaglio della fase con un agente
> dedicato. ⭐ **Quell'agente è tornato dicendo che non c'era niente da curare.**
>
> `[M]` Lo stesso tratto, tre banchi indipendenti:
>
> | come | ms |
> |---|---|
> | strada **vera** (`bitmaprenderer`), sessione vera, HEVC in hardware, n=200 ×2 | **1,18** e **0,49** |
> | ⛔ **la stessa strada `?tela=2d` di A** | **0,39** e **0,97** |
> | senza server né rete, stream HEVC vero a 60/s | **1,00** (2D) · **2,80** (`bitmaprenderer`) |
>
> ⇒ **Da 15 a 45 volte meno, e su tutt'e due le strade** ⇒ ⛔ **la strada di disegno non era la
> spiegazione**: quella non c'entrava niente.
>
> ⭐⭐ **La causa, misurata**: `[M]` il portatile ha **4 nuclei**, e mentre A misurava ci giravano
> sopra **56 processi Chrome e 5 Xvfb** — perché **tre o quattro agenti facevano banchi da browser
> nello stesso momento**. ⇒ **Li avevo lanciati in parallelo io.**
>
> ⛔ **Che cosa cade con quel numero**: il tratto F non vale 18,83 ms (19 %) ma **~3,5 (3,5 %)**; il
> **99,07 ms** di §4-A **sovrastima di ~15 ms**; e la frase *«quattro tratti su sei fanno l'83 %»*
> va rifatta. ⚠ **E il sospetto si estende a tutta la prima ondata**, B compreso: i suoi 0,28 barre
> sono stati presi nelle stesse condizioni, solo in un verso che nessuno conosce.
>
> ⭐ **La lezione, e non è «misurate meglio»**: `LEZIONI.md` §1.24 diceva *due banchi sulla stessa
> porta si ammazzano in silenzio*. ⛔ **È più larga di così**: due banchi sulla stessa **macchina**
> si falsano in silenzio — e il secondo caso non dà nessun rosso, dà un **numero plausibile**.
> ⇒ **Il carico va dichiarato accanto a ogni numero**, come il palco (§2.0).
>
> ### ⭐ E l'agente ha consegnato uno strumento invece di una cura
>
> **`REMOTIX.tratti()`, dentro `src/pagina.html`**: il prodotto **dichiara da sé** i quattro tratti
> del cliente, **con gli stessi nomi su tutte e tre le strade di disegno**, a `[M]` ~4 µs per
> fotogramma. ⇒ ⛔ **Non serve più riscrivere il prologo di un banco ogni volta che la pagina cambia
> modo di dipingere** — che è esattamente il difetto che aveva bloccato A (0 sonde su 304).
>
> ⚠ **E due numeri del documento vanno buttati**: `[M]` `createImageBitmap` costa **1,05 / 0,41 ms**,
> non i **3,8** di §7.1; e il tratto F vale ~3,5 ms, non 18,83.

> ### ⭐⭐⭐ IL PUNTO STA IN DUE NUMERI PRESI SULLA **STESSA** STRADA CHE HA DATO IL PRIMO
>
> L'agente A, sulla strada `?tela=2d`: `[M]` il tratto *«richiamo del decodificatore → 1°
> `drawImage` finito»* vale **17,48 ms**, contro **0,10** del disegno vero. ⇒ *«il collo di
> bottiglia è il disegno»* è falso — e su questo non c'è niente da correggere: è giusto.
>
> ⛔⛔ **Ma il tratto stesso non c'è.** Rimisurato oggi, in una sessione vera, sulla **stessa
> strada `?tela=2d`**, con lo stesso ferro e lo stesso codec:
>
> | | `richiamo → vetro` (i tratti 9+10 di A) | fotogrammi dipinti |
> |---|---|---|
> | `[M]` **A, 22 agosto, `?tela=2d`** | **17,58 ms** | — |
> | `[M]` **F3, `?tela=2d`** — la strada di A · giro 1 · giro 2 | ⭐ **0,39** · **0,97 ms** (n=200 ×2) | 33,7 · 39,9/s |
> | `[M]` **F3, la strada VERA (`bitmaprenderer`)** · giro 1 · giro 2 | ⭐⭐ **1,18** · **0,49 ms** (n=200 ×2) | 34,0 · 34,7/s |
>
> ⇒ ⭐⭐ **Da quindici a quarantacinque volte meno, sulla strada identica**, e **quattro giri su
> quattro** in **due sessioni indipendenti** stanno fra **0,39 e 1,18 ms**. E non è solo la
> sessione: un
> secondo banco, **senza server e senza rete**, che decodifica in hardware uno stream HEVC vero
> di 1460×888 a 60/s sullo stesso portatile, trova `[M]` **1,00 ms** sulla strada 2D e **2,80**
> su `bitmaprenderer`. ⛔ **I 17,48 ms non si riproducono da nessuna delle due parti.**
>
> ⇒ ⛔⛔ **Non c'è nessuna cura da fare nel disegno del cliente, perché non c'è niente da
> curare.** Il mandato diceva *«prima capire, poi curare»*: capito, e la risposta è che il
> bersaglio non esiste. ⭐ **Il risultato di questo giro è una riga cancellata, non una riga
> aggiunta** — ed è il genere di esito per cui si strumenta prima.
>
> ⚠ **E la conseguenza è più grossa del tratto**: se il tratto 9 vale 0,39 e non 17,48, allora
> il tratto **F, «il cliente»** non vale **18,83 ms (il 19 % dell'anello)** ma `[M]` **~3,5 ms
> (il 3,5 %)** — e i **~15 ms** di differenza **erano nell'anello di A per davvero** (la somma
> dei suoi tratti chiude con il suo totale entro 0,002 ms). ⇒ Sono **dello strumento**, non del
> prodotto, e il **99,07 ms** di §4-A **sovrastima l'anello vero di circa quel tanto**.

*Agente F3. Risorse tutte mie: porta **7770** · utente **`provaf3`** (uid 1047) · albero
`/media/REMOTIX/src/08-f-src` · lavoro `/media/REMOTIX/tmp/08-f` · scena
`/dev/shm/remotix-08-f3`. ⛔ Le porte **7730 e 7731** dell'utente non sono mai state toccate, e la
7770 è stata **contata** con `ss -tulnp` prima di prenderla.*

---

## F3.1 · Che cosa è stato costruito

| file | che cos'è |
|---|---|
| `src/pagina.html` | ⭐⭐ **i quattro tratti del cliente li dichiara il PRODOTTO**: `REMOTIX.tratti()` |
| `banchi/08-f3-quanto-aspetta.html` | ⭐⭐ il banco **senza server**: la stessa catena `decode() → richiamo → immagine → vetro` su uno stream vero, con i controlli che separano le tre ipotesi |
| `banchi/08-f3-lancia.py` | il lanciatore del banco: lo stream con `ffmpeg`, i quattordici giri, i confronti |
| `banchi/08-f3-tratti.py` | ⭐ legge `REMOTIX.tratti()` da una **sessione vera**, su tutt'e due le strade nella stessa seduta |
| `banchi/08-f3-sessione.sh` | il terreno mio (porta, utente, albero, scena) |
| `banchi/08-f3-esiti.json` · `08-f3-esiti.jsonl` | i verbali |

⛔ **Non è stata toccata una riga di `src/*.c`, né un banco di un altro agente.**

### ⭐⭐ E la cosa che vale più del banco: **adesso i tratti li dichiara il prodotto**

⛔ **La ragione è il difetto che ha generato questo giro.** Il numero di A è della strada `?tela=2d`
perché il prologo di `04-b30` **legge i pixel dal deposito**, e dal 20 agosto il deposito non
esiste (`DECISIONI.md` §5.4). ⇒ Il numero della strada **viva** non era misurabile da nessuno senza
riscrivere il prologo di un banco — «mezza giornata», dice §A.4.

⇒ ⭐ `src/pagina.html` misura da sé i quattro tratti che gli appartengono e li espone:

```
REMOTIX.tratti()  →  strada · tela · dipinti · saltati_coda · tardive
                     8_decode_richiamo · 9a_richiamo_chiamata · 9b_conversione
                     10_vetro · 9_10_richiamo_vetro · 11_vetro_prossimo_quadro
```

⭐ **Gli stessi nomi su tutt'e tre le strade** (`bitmaprenderer`, `?tela=2d`, il ripiego): un banco
li legge con una riga e non deve più sapere come è fatto il disegno di dentro.
⛔ **E non è un interruttore** (invariante I6): non c'è niente lì dentro che possa cambiare quel che
la pagina fa.

**Il costo, dichiarato**: due `performance.now()` in più per fotogramma (~4 µs a 60/s, `[M]` sotto
il passo dell'orologio del browser, che è 100 µs) più una voce di mappa che si cancella nel
richiamo — e la mappa ha un **tetto di 240**, perché un decodificatore che smettesse di consegnare
farebbe crescere la pagina per sempre.

---

## F3.2 · ⛔ CHE COSA SONO, QUEI MILLISECONDI — e la risposta è «non ci sono»

**Le tre ipotesi del mandato, e come apparirebbe ciascuna** (`LEZIONI.md` §1.11 regola 1: per ogni
prova indiretta si scrive prima come apparirebbe il caso opposto):

| | l'ipotesi | come apparirebbe |
|---|---|---|
| **a** | il **decodificatore hardware** macina | l'attesa sta dentro la conversione del fotogramma **e solo lì**; i gemelli (microtask, macrotask, immagine piccola) restano a ~0 |
| **b** | si aspetta un **quadro del browser** (16,7 ms a 60 Hz — un numero sospettosamente vicino) | ⛔ **è il muro**: l'attesa è incollata al quadro, e **sparisce dove non c'è scanout** |
| **c** | la **promessa si risolve tardi** perché il thread è occupato | i gemelli salgono **insieme** all'attesa, e in assoluto |

### ⭐ E il banco ha risposto a una domanda che veniva prima: **si aspetta?**

`[M]` **Banco senza server**, portatile, Chrome, GPU `ANGLE (Intel, Mesa Intel(R) Graphics
(ADL-N))`, HEVC **in hardware** (⚠ `[M]` Chrome **rifiuta** `prefer-software` su HEVC: su questo
motore HEVC è **solo** hardware), stream vero 1460×888 consegnato a 60/s, 400 fotogrammi per giro:

| giro | tratto 9 | 9+10 | contro i 17,58 di A |
|---|---|---|---|
| `2d-hw-pulito` — la strada di A, **senza strumento addosso** | **0,80 ms** | **1,00** | **−94 %** |
| `bitmap-hw-pulito` — la strada vera | **2,70** | **2,80** | **−84 %** |
| `2d-hw-letto` — **con la lettura dei pixel dentro il richiamo, come fa il banco di A** | **2,40** | 2,60 | −85 % |
| `2d-h264-hw` (hardware) | 2,80 | 3,00 | −83 % |
| `2d-h264-sw` (**software**) | 1,50 | 1,60 | −91 % |

⇒ ⭐⭐ **Sotto i 5 ms non c'è nessuna attesa da diagnosticare**, e il banco lo dice con un verdetto
invece di scegliere una delle tre ipotesi sul rumore. ⛔ **Un banco che partisse dalle tre ipotesi
ne sceglierebbe una anche su mezzo millisecondo.**

⇒ E le tre ipotesi restano **tutte e tre smentite come spiegazione dei 17 ms**:
- **(a) il decodificatore**: lo stesso stream in **software** costa **meno** (1,50 contro 2,80). Il
  decodificatore hardware non sta facendo aspettare nessuno;
- **(c) la coda**: `[M]` la **netta** — quel che il fotogramma aggiunge sopra a una continuazione
  qualunque dello stesso richiamo — vale **0,00 ms**. Tutto quel che si misura è il confine del
  compito, e il confine del compito è ~1 ms;
- **(b) il quadro**: ⛔ **non provato né escluso su quel palco**, e si dichiara: `[M]` il ritmo di
  `requestAnimationFrame` su questo Xvfb passa da **1 a 434 quadri** fra un giro e l'altro
  (`STUDI.md` §web §6.2 lo diceva già: senza scanout rAF non gira). ⇒ Il controllo positivo di (b)
  **non è eseguibile lì**, e il banco lo scrive invece di contarlo verde.
  ⭐ Ma in **sessione vera** la domanda è chiusa lo stesso: il tratto vale **1,18 ms**, cioè meno di
  un decimo di quadro. Nessun quadro ci sta dentro.

### ⭐ E la sessione vera, che è quella che conta

`[M]` 22 agosto 2026, server **7770** sul mio albero, utente `provaf3`, GNOME headless, monitor
virtuale **1520 × 868 @ 60 Hz**, scena `04-b30-scena` a 60 disegni/s, codec **HEVC**
`hev1.1.6.L153.B0` **in hardware**, `VideoFrame.format` **BGRX**, GPU della pagina `ANGLE (Intel,
Mesa Intel(R) Graphics (ADL-N))`, rete WiFi vera in mezzo, **nessun errore**:

| tratto | **strada VERA** g1 · g2 | strada `?tela=2d` g1 · g2 |
|---|---|---|
| 8 · `decode()` → richiamo | **2,20** · **0,79 ms** | 0,74 · 1,82 |
| 9a · richiamo → chiamata | **0,04** · **0,02** | — |
| 9b · la conversione (`createImageBitmap`) | **1,05** · **0,41** | — |
| 10 · il vetro (`transferFromImageBitmap`) | **0,04** · **0,02** | — |
| ⭐ **9+10 · richiamo → VETRO** | ⭐⭐ **1,18** · **0,49 ms** | ⭐ **0,39** · **0,97 ms** |
| ⭐ 11 · vetro → prossimo quadro | — · **1,67** [p95 14,53] n=55 | — |
| ⭐ **fotogrammi dipinti** | **34,0** · **34,7/s** | **33,7** · **39,9/s** |
| saltati in coda · tardive | **0 · 0** | 0 · 0 |

⭐ **Il tratto 11 è il primo numero che quel pezzo cieco abbia mai avuto**: `[M]` **1,67 ms**
mediani fra il vetro cambiato e il quadro successivo del browser (p95 **14,53**, max **18,16**,
n=55). ⛔ **Non è «il pixel acceso»** — è il **primo istante in cui può accendersi**, cioè il
limite **inferiore** dei `[?]` 16-40 ms di `STUDI.md` §web §6.2, e il p95 dice che ogni tanto ci
sta dentro un quadro intero. ⚠ Un giro su quattro l'ha consegnato: sugli altri tre
`requestAnimationFrame` non è mai scattato (§F3.4 punto 2).

⭐ **`9a` vale 0,04 ms**, ed è un controllo, non un dato di colore: se un giorno non valesse ~zero
vorrebbe dire che fra il richiamo e la conversione qualcuno ha infilato del lavoro, e oggi nessun
conto lo vedrebbe.

⚠ **`createImageBitmap` costa 1,05 e 0,41 ms qui**, non i **3,8** di `SPECIFICHE.md`/§7.1. ⇒ Quel
numero va rimisurato prima di essere citato ancora; non è sbagliato, è di un altro palco.

### ⭐ E un controllo che ha lavorato subito

`[M]` Un giro è stato **rifiutato dal banco stesso**: *«la pagina dipinge 0,0 fotogrammi/s: il
PALCO è fermo (la scena non è sul monitor di questa sessione). ⇒ NON misuro»*. ⛔ Senza quella
riga il verbale avrebbe detto **«non misurato»** su tutti i tratti, e chi lo rilegge avrebbe letto
*«lo strumento ha guardato e non ha visto»* invece di *«lo strumento non ha potuto guardare»* —
`LEZIONI.md` §1.21. ⚠ E la riga esiste perché il **primo** giro di oggi era esattamente così:
`[M]` **2 fotogrammi dipinti in 30 secondi**, e il banco allora **non se n'era accorto**.

---

## F3.3 · ⛔ Dove sono finiti, allora, quei 17 ms

`[R]` Il prologo di `04-b30-anello-input.py` fa **due cose dentro lo stesso richiamo del
decodificatore**, e la seconda è quella che pesa:

1. avvolge `CanvasRenderingContext2D.prototype.drawImage` e ne misura la durata (`t_dip_a =
   t1 + disegni[0]` ⇒ **il tratto 9 È la durata del primo `drawImage`**);
2. ⛔ subito dopo **rilegge i pixel dal deposito con `getImageData`**, due finestrelle, **a ogni
   fotogramma**.

⇒ ⭐ **Una tela 2D da cui si rilegge viene retrocessa a tela di CPU**, e da quel momento ogni
`drawImage` di un `VideoFrame` che sta in GPU non è un disegno: è una **rilettura dalla GPU**.

⚠ **E qui la mia stessa prova mi smentisce a metà, e si scrive**: rifacendo *esattamente* quello nel
banco isolato, il disegno passa da **0,80 a 2,40 ms** — `[M]` **+1,60**, non +17. Con
`willReadFrequently` acceso: **2,70**, cioè **nessuna differenza**.

⇒ `[?]` **Il meccanismo è plausibile e la sua taglia non torna.** Quel che è `[M]` e non dipende
dall'ipotesi:

- sulla **stessa strada**, con **strumento** (A) **17,58 ms**, senza (F3) **0,39 ms**;
- il banco di A misura **4,12 – 4,86 ms** di sola lettura delle marche, e lo dichiara (Q12);
- ⛔ e il **palco era condiviso in un modo che nessuno ha scritto**: `[M]` mentre giravano queste
  misure il portatile — **4 nuclei** — aveva **56 processi di Chrome** e **5 `Xvfb`** vivi
  contemporaneamente, cioè tre o quattro agenti della fase 8 che facevano banchi da browser sulla
  stessa macchina. ⇒ ⭐ **È la spiegazione più economica**, e vale anche per A.

---

## F3.4 · ⛔⛔ CHE COSA NON HA FUNZIONATO

### 1. ⛔ `08-b67-elastico.py` sul mio terreno NON dà un numero, e non lo si cita

`[M]` giro `f3-dopo-strumentata`: **527,7 ms** di ritardo, **0 px** di distacco, **Q1 rosso**.
`[R]` La causa sta nel verbale: il banco ha generato **3 125 movimenti** e ne sono **usciti 30**.
⇒ ⛔ **Non è «l'anello è lungo», è «la mano non è partita»**: `Input.dispatchMouseEvent` via CDP ha
impiegato `[M]` **~5 secondi per evento** su questo palco, e il banco stesso lo dice — *«3 intervalli
di movimento: troppo pochi per dire che velocità aveva la mano. ⚠ Non è "la mano era lenta"»*.

⚠ **La causa è il palco condiviso di §F3.3**, non il banco di B: con 56 Chrome su 4 nuclei il canale
di diagnosi si accoda. ⭐ **Il banco di B ha rifiutato correttamente di consegnare un numero**, ed è
esattamente il comportamento che gli si chiede.

⇒ ⛔ **Il «dopo» in barre del titolo NON c'è**, e non si prende da un'altra seduta. Il mio prima/dopo
è quello di §F3.2, **coi fotogrammi accanto ai millisecondi**: `[M]` **34,0 · 34,7 · 33,7 ·
39,9 fotogrammi/s** su quattro giri, con **0 saltati in coda e 0 tardive** su tutti e quattro.
⇒ Il prodotto strumentato dipinge come prima, e **non è un'impressione: è il denominatore**.
⚠ E il confronto regge perché **la cura è misurazione e basta**: non c'è nessuna riga che cambi
quel che la pagina fa. ⛔ Se ci fosse stata, questo «dopo» non sarebbe bastato.

### 2. ⚠ Il tratto 11 esce **un giro su quattro**, e il denominatore va detto

Il prodotto lo campiona uno ogni 16 fotogrammi. `[M]` Su quattro giri ne ha consegnati **55
campioni in uno solo**; negli altri tre `requestAnimationFrame` **non è mai scattato**. `[R]` È la
stessa cosa di `STUDI.md` §web §6.2 — dove non c'è scanout rAF non gira — e sul banco senza server
`[M]` il ritmo dei quadri passa da **1 a 434** fra un giro e l'altro sulla stessa macchina.
⇒ ⛔ **Il numero c'è ma il denominatore è di un giro solo**: `1,67 ms` mediani va letto come un
**primo** numero, non come il numero. ⭐ Il codice per prenderlo bene c'è ed è gratis: basta un
palco con scanout vero.

### 3. ⛔⛔ Ho toccato l'utente di un altro agente, e va detto

`[M]` Il mio terreno chiedeva l'utente **`provaf8`**; `04-b32-terreno.sh` ha risposto *«c'è già —
non lo rifaccio»* e **poi gli ha riposto la parola d'ordine** e ha scritto il drop-in di systemd in
`/home/provaf8/.config`. ⛔ **`provaf8` (uid 1044) è di un altro agente della fase**, che l'aveva
creato pochi minuti prima. ⇒ Ho cambiato subito utente (**`provaf3`**, uid **1047**) e ho lasciato
`provaf8` in pace da quel momento.

⚠ **Il danno possibile e il suo limite**: la parola che ho posto è `provaf8-2026`, cioè la
convenzione del progetto; se quell'agente usa la stessa convenzione **non è cambiato niente**, se ne
usa un'altra **la sua sessione non entra più**. ⛔ **Non è verificabile da qui.**
⭐ **E la lezione è del processo, non mia**: `LEZIONI.md` §1.24 dice di contare le **porte** prima di
prenderle. `[M]` Oggi le porte le ho contate e andava bene; **quel che ha morso è l'UTENTE**, e
nessuna regola diceva di contarlo. ⇒ La regola va estesa: **utente, uid, porta, ban-file, socket e
nome dello shm si contano tutti prima**. Lo stesso è successo con lo shm: `/dev/shm/remotix-08-f`
era già di `provaf8`, e la scena moriva con `Permission denied` — quello **l'ho visto subito**
perché fallisce rumorosamente, mentre l'utente ha fallito **in silenzio**.

### 4. ⚠ Tre difetti dello strumento, trovati dallo strumento stesso

- ⛔ **il primo `bmp_ms` che ho letto era il costo del banco**: `[M]` `createImageBitmap` **0,90 ms**
  e il microtask di controllo **0,90** — identici, perché i controlli stanno dentro tutt'e due.
  ⇒ Curato con la **netta** (si sottrae il gemello) e con i giri **puliti** (i controlli spenti);
- ⛔ **il verdetto della coda era verde sempre**: il rapporto `controlli/attesa` vale ~1,0 anche su
  un thread libero. È `LEZIONI.md` §1.20 in persona — *«esiste un caso in cui vale zero e il banco
  resta verde?»*. ⇒ Curato con una soglia **assoluta** accanto al rapporto;
- ⛔ **il controllo positivo del fotogramma era cieco**: chiedere a `createImageBitmap` un
  riscalamento a 3840×2160 lascia la netta a **0,00** — ⭐ e quello è un **fatto**, non un difetto:
  quella promessa si risolve al confine del compito, non al termine del lavoro. ⇒ Il controllo si è
  spostato sulla strada 2D, dove il disegno è sincrono, e lì `[M]` otto disegni fanno salire il
  tratto 9 di **+11,50 ms** e i gemelli di **+11,60**, cioè **di quel tanto e non di più**: il banco
  attribuisce.

**La certificazione del banco senza server**: `[M]` taratura verde (20 ms bruciati escono
**+20,00 ms** nel tratto giusto), controllo positivo (c) verde, controllo positivo (a) verde,
controllo (b) **dichiarato non eseguibile**. ⇒ **rossi: 0.**

---

## F3.5 · ⛔ Che cosa resta `[?]` dopo di me

| | |
|---|---|
| ⏳ **perché A ha visto 17,48 ms** | il meccanismo (la tela retrocessa a CPU dalla rilettura) spiega `[M]` **+1,60 ms** su quattordici. Il resto è `[?]`, e il candidato migliore è il **palco condiviso** — ⛔ ma non l'ho isolato |
| ⛔ **l'anello di §4-A va rimisurato** | se il tratto 9 vale 0,39 e non 17,48, i **99,07 ms** sovrastimano. ⚠ Non basta sottrarre 17: il numero va **ripreso**, con lo strumento che oggi sta nel prodotto invece che nel prologo |
| ⏳ **il tratto 11 e i `[?]` 16-40 ms** | il codice c'è, il palco no: serve un browser con scanout vero |
| ⏳ **il «dopo» in barre del titolo** | `08-b67-elastico.py` va rigirato **su un portatile scarico** |
| ⚠ **`createImageBitmap` = 3,8 ms** | `[M]` oggi ne vale **1,05**. Il numero di §7.1 è di un altro palco e non si cita più senza rifarlo |
| ⚠ **il tratto 8 cambia con la strada** | `[M]` **2,20 ms** su `bitmaprenderer` contro **0,74** su `?tela=2d`, stessa sessione. ⛔ `decode()` → richiamo **non dovrebbe** dipendere da come si dipinge: o è la contesa, o è una coda che si sposta. Non l'ho aperto |

---

## F3.6 · Che cosa ho lasciato sulla macchina

Utente **`provaf3`** (uid 1047) con sessione GNOME, albero `/media/REMOTIX/src/08-f-src`
(**compilato da me**, non copiato), scena `/media/REMOTIX/src/08-f-scena-lav/04-b30-scena`,
lavoro `/media/REMOTIX/tmp/08-f`, blocco condiviso `/dev/shm/remotix-08-f3`.
⭐ **Prodotto, ponte e scena SPENTI**, e il conteggio dei vicini lo dichiara in ogni riga di
registro. ⛔ **Le porte 7730 e 7731 non sono mai state toccate**, e la 7770 è tornata libera.
⚠ Sul portatile ho lasciato pulito: nessun `Xvfb` mio, nessun socket X mio.

---

## F3.7 · ⭐ E la riga che questa fase può portarsi via

⛔ **Il tratto F non è un bersaglio.** L'anello dell'utente è lungo perché sono lunghi **C**
(l'attesa del quadro nella scena), **D** (il quadro di Mutter, un muro a 16,36 ms) ed **E**
(codifica e ritorno). ⇒ ⭐ **Chi apre la fase 8 dopo di me non spenda un'ora sul cliente**: `[M]`
il cliente costa **1,18 ms su ~100**, cioè **l'1 %**, e i tre quarti di quell'1 % sono il
decodificatore che consegna (tratto 8), non noi.

⭐⭐ **E il metodo ha retto una seconda volta oggi**: l'agente C credeva di sapere dove stavano i
suoi 16 ms e lo strumento gli ha risposto **0,08**; io sono andato a curare 17 ms e lo strumento ha
risposto che **non ci sono**. ⇒ *Strumentare prima e lasciare che lo strumento smentisca* ha
prodotto, in una giornata, **due bersagli cancellati** — che è lavoro risparmiato, non lavoro perso.


---

## 4-A · ⭐⭐⭐ AGENTE A — il «prima» dell'anello · **rientrato il 22 agosto 2026**

> ### ⭐⭐⭐ E LA COSA PIÙ IMPORTANTE STA IN UNA MOLTIPLICAZIONE: **l'occhio dell'utente e lo strumento dicono la stessa cosa**
>
> L'utente, guardando lo schermo e senza strumenti: il distacco fra la freccia e la finestra è
> **«metà della barra del titolo»** ⇒ ≈ **360 px**. Il suo trascinamento, misurato dal video, ha
> velocità mediana **3 400 px/s**.
>
> Il banco, che non sa niente di tutto questo: `input → vetro` = **99,07 ms**.
>
> ```
> 99,07 ms × 3 400 px/s  =  337 px
> ```
>
> ⛔⛔ **QUESTO ACCORDO È STATO RITIRATO IL 22 AGOSTO, LA SERA — 📖 §4-F1.** I 99,07 ms erano
> gonfiati dalla contesa fra i miei stessi agenti: `[M]` a macchina scarica l'anello vale **74,9 ms**,
> che a 3 400 px/s fanno **255 px**, non 337. ⇒ **255 contro 360 non è un accordo entro il 7 %: è uno
> scarto del 30 %, e nel verso sbagliato** — l'utente vede **più** distacco di quanto lo strumento
> ne misuri.
>
> ⚠ **Quel che resta in piedi**, e non è poco: l'elastico di §1.2 — `distacco = velocità × ritardo` —
> **non è smentito**, è la sua taratura che era falsa. Ma ⛔ **l'accordo fra l'occhio e lo strumento
> era la riga più citata di questo documento, ed era un artefatto della mia orchestrazione.** Resta
> scritta com'era, sbarrata, perché la forma dell'errore vale più della conclusione.
>
> ⭐ **E dice anche a quale velocità l'utente guardava**: alla sua **mediana**, non ai picchi. ⇒ Il
> bersaglio della fase è il trascinamento **normale**, non quello estremo.
>
> ⚠ **Il conto non chiude del tutto, e si dichiara**: 99,07 è il **pezzo nostro**; sullo schermo
> vero ci vanno sopra i due pezzi ciechi (`[?]` 4-12 ms in ingresso, 16-40 in uscita) e la rete
> (2,85 ms mediani) ⇒ **119-151 ms**, che a 3 400 px/s farebbero 405-513 px. L'utente ne vede 360.
> `[?]` O guarda un po' più veloce della sua mediana, o i pezzi ciechi stanno al minimo. **Non è
> risolto, ed è il genere di scarto che si scrive invece di limarlo a parole.**

*Agente A. Banco `banchi/04-b30-anello-input.py`, risorse tutte mie: porte **7740** (ponte) ·
**7741** (prodotto) · **7742** (ancora), utente **`provaa8`** (uid 1041), `/media/REMOTIX/tmp/08-a`,
`/dev/shm/remotix-08-a`, ban-file e socket dentro la mia directory. ⛔ Le due porte dell'utente —
**7730** e **7731** — non sono state toccate, e il conteggio dei vicini lo dichiara a ogni passo.*

---

## A.0 ⭐ Il banco si è ricertificato, e la certificazione conta i guasti

`[M]` `python3 banchi/04-b30-anello-input.py --certifica` ⇒ **PROMOSSO, 53 controlli su 53, e 16
guasti innestati accusati su 16.** Rifatto due volte: prima di toccare il file e dopo (§A.4).
⇒ Il banco sa come fallire.

---

## A.1 ⭐⭐ IL NUMERO DI OGGI

`[M]` **22 agosto 2026** — `input → vetro`, confine **scomodo** ai due capi
(`event.timeStamp` in fase di cattura → **disegno finito**), **cinque giri**:

| | |
|---|---|
| **la mediana delle cinque mediane** | `[M]` **99,07 ms** |
| le cinque mediane | **88,39** · **96,68** · **99,07** · **109,07** · **111,03** ms |
| **n** (sonde CHIUSE, il denominatore vero) | **228** · **234** · **224** · **413** · **417** — ⭐ e le sonde *tentate* erano 228/234/224/417/418: **nessun giro sotto il 99 % di chiusura** |
| il confine **comodo** (per confronto, NON è il numero) | mediana delle mediane **70,15 ms** ⇒ il comodo si regala `[M]` **30,89 ms** |
| contro `SPECIFICHE.md` §3.2 | **SFORA** i 50 ms e i 40, alla mediana e al p95 |

### ⛔ E i DUE pezzi ciechi, che l'intestazione pretende accanto al numero

| | |
|---|---|
| **in INGRESSO** | `[?]` **4-12 ms**: mano → `event.timeStamp` — dispositivo, nucleo e compositore **del client**. Nessuna API della pagina lo vede: `event.timeStamp` è già il dopo |
| **in USCITA** | `[?]` **16-40 ms**: disegno finito → pixel acceso (`STUDI.md` §web §6.2). ⛔ **E qui ci sono davvero**: il banco ha letto `clienti_sull_xvfb: 0` ⇒ il browser misurato **non sta sull'Xvfb del banco** ma sul desktop vero del portatile, dove un compositore c'è |

⇒ ⛔ **Sullo schermo di un utente**: `[M]` 99,1 + `[?]` 4-12 + `[?]` 16-40 = **119,1 - 151,1 ms**,
**più la rete**. `SPECIFICHE.md` §3.2 misura «solo il pezzo che è nostro»: i pezzi ciechi si
**dichiarano**, non si promettono.

### ⛔ Il palco, accanto al numero (`LEZIONI.md` §2.0)

`[M]` codec negoziato **HEVC** · stringa `hev1.1.6.L120.B0`, **8 bit**, promozione 8→10 **no** ·
codifica **IN HARDWARE** (`hevc_vaapi`, `/dev/dri/renderD128`, iHD 25.2.3, ⚠ **EncSliceLP**, bassa
potenza — non è la codifica piena) · tela **1460 × 888** · GPU della pagina
`ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` · WebCodecs sì · pagina isolata sì ·
scena sul monitor **Meta-0**, confermato da `wl_surface.enter`, cioè **dal compositore**.
⚠ E sulla macchina giravano contemporaneamente i **due server dell'utente** (7730, 7731): è un
palco condiviso, e la dispersione di §A.4 lo riflette.

---

## A.2 ⭐⭐ LA SCOMPOSIZIONE — e i tratti sono SEI davvero

Il banco produce **11 tratti misurati** (più T, T-comodo, Δ e i due pezzi ciechi = i «16 tratti» che
la certificazione conta). ⭐ **Raggruppati per anello fisico sono esattamente SEI**, ed è la tabella
che la fase 4 aveva promesso senza scriverla:

| | il tratto | 14 ago | **22 ago** | Δ |
|---|---|---|---|---|
| **A** | **la pagina** — `event.timeStamp` → i byte escono (1a + 1b) | 12,75 ms (9,1 %) | **7,65 ms (7,7 %)** | −5,10 |
| **B** | **l'andata** — byte usciti → la scena riceve l'input (filo + server + `libei` + compositore) (2) | 25,35 ms (18,0 %) | **7,25 ms (7,3 %)** | **−18,09** |
| **C** | **l'attesa del quadro nella scena** — la scena riceve → la scena disegna (3) | 26,51 ms (18,9 %) | **23,25 ms (23,5 %)** | −3,27 |
| **D** | **il quadro di Mutter** — la scena disegna → cattura (`pts`) (4) | 16,23 ms (11,5 %) | **16,36 ms (16,5 %)** | +0,13 |
| **E** | **codifica e ritorno** — cattura → ultimo byte in pagina (5 + 6) | 31,06 ms (22,1 %) | **24,45 ms (24,7 %)** | −6,61 |
| **F** | **il cliente** — `decode()` → disegno finito (7 + 8 + 9 + 10) | 27,25 ms (19,4 %) | **18,83 ms (19,0 %)** | −8,42 |
| | **somma delle mediane** | 139,14 | **97,79** | |
| | **T, mediana del totale** | **140,50** | **99,07** | −41,43 |

⭐ **I tratti non perdono niente per strada**, e non è un'impressione: sulle **medie** (che sono
additive, a differenza delle mediane) la somma dei tratti 1a…10 contro la media di T fa
`[M]` 141,718 contro 141,719 · 142,726 contro 142,725 · 115,769 contro 115,769 · 110,142 contro
110,140. **Scarto ≤ 0,002 ms su quattro giri.**

### I sotto-tratti, quando servono a chi deve curare

| tratto | 14 ago | **22 ago** (mediana di 5 giri, [min-max]) |
|---|---|---|
| 1a evento → il prodotto lo vede (fase di cattura) | 12,68 | **7,53** [7,04 – 15,04] |
| 1b il prodotto lo vede → i byte escono | 0,07 | **0,12** |
| 2 byte usciti → la scena riceve l'input | 25,35 | **7,25** [6,84 – 7,93] |
| 3 la scena riceve → la scena DISEGNA | 26,51 | **23,25** [13,86 – 28,28] |
| 4 la scena disegna → cattura (`pts` di Mutter) | 16,23 | **16,36** [16,23 – 16,39] |
| 5 cattura → PRIMO byte in pagina | 30,87 | **24,19** [20,05 – 26,17] |
| 6 primo byte → ULTIMO byte (lo stream sul filo) | 0,20 | **0,24** |
| 7 stream completo → richiamo di `decode()` | 0,09 | **0,10** |
| 8 `decode()` → richiamo del decodificatore | 0,75 | **1,09** |
| 9 ⭐ richiamo → **1° `drawImage`** (l'ATTESA del fotogramma) | 26,34 | **17,48** [14,90 – 18,72] |
| 10 ⭐ 1° → 2° `drawImage` (**il disegno VERO**) | 0,08 | **0,10** |

### ⭐⭐ Le tre cose che questa tabella dice, e che nessun documento diceva

1. ⛔⛔ **«sei tratti da ~25 ms, nessuno dominante» NON è più vero.** Oggi i sei valgono
   **7,7 / 7,3 / 23,5 / 16,5 / 24,7 / 19,0** ms. ⇒ **Quattro tratti su sei** (C, D, E, F) fanno
   **83 %** dell'anello; i due dell'andata (A e B) ne fanno **15 %** insieme. La fase 8 ha
   **quattro** bersagli, non sei.
2. ⭐ **Q8 conferma di nuovo, e più forte di prima**: `[M]` il **1° `drawImage` costa 17,48 ms e il
   2° ne costa 0,10 — 163 volte**. ⇒ Il tratto 9 **non è il disegno**: è l'**attesa** che il
   fotogramma decodificato sia utilizzabile. La riga «il collo di bottiglia è il disegno» resta
   falsa, e adesso lo è con `[M]`.
3. ⛔ **Il tratto D è un muro, non un margine**: 16,36 ms con dispersione [16,23 – 16,39] su cinque
   giri — è **un quadro a 60 Hz**, esatto. Non si lima: si toglie solo cambiando il modo in cui
   Mutter consegna. ⇒ **Un sesto dell'anello è il ritmo del compositore.**

### ⭐ Quanto AGGIUNGE il canale di input (la sola cosa nuova che questo banco sa dire)

`[M]` i tratti che il metro della fase 3 non attraversava (A + B + C) valgono **41,74 ms**
(mediana dei cinque giri; 14 agosto: **64,6**). ⛔ E i due numeri **non si sommano e non si
sottraggono**: `input → vetro` **contiene** `disegno della scena → vetro`.

---

## A.3 ⛔⛔ IL CONFRONTO COL 139,40 — regge in parte, e la parte che NON regge va detta per prima

### Il file del banco: sì, è lo stesso

`[M]` `git log -- banchi/04-b30-anello-input.py`: l'ultima modifica al banco è del **16 agosto**
(`0c85e5c`), ed è la **rinomina dei documenti** (`web.md` → `STUDI.md` §web) — si vede confrontando
il verbale del 14 agosto, che cita `web.md §6.2`, con quello di oggi, che cita `STUDI.md §web §6.2`.
⇒ **Nessuna modifica al metro fra le due date.** L'unica modifica *mia* è §A.4, additiva, e il banco
è stato ricertificato dopo.

### ⛔ Ma il palco è cambiato in DUE modi, e tutt'e due tirano dalla nostra parte

| | 14 agosto | 22 agosto | che effetto ha |
|---|---|---|---|
| ⛔⛔ **la tela** | **1920 × 1080** = 2 073 600 px | **1460 × 888** = 1 296 480 px | **il 62,5 % dei pixel**: meno da convertire, codificare, spedire, decodificare e disegnare ⇒ tira giù **E** e **F**, e forse **D** |
| ⛔ **la profondità** | `hev1.**2.4**` — HEVC **10 bit**, promozione 8→10 **dichiarata** (conversione 6214 µs + caricamento 2916 + codifica 5187 = **14,3 ms**) | `hev1.**1.6**` — HEVC **8 bit**, nessuna promozione (2735 + 1606 + 7199 = **11,5 ms**) | tira giù **E** |

⚠ **Ho provato a rimettere la tela di allora e NON ci sono riuscito**: `?adatta=no` è la leva
dichiarata («la pagina di prima del 15 agosto»), il giro con quella coda ha girato, ⛔ **e la tela è
rimasta 1460 × 888**. `[R]` Il registro del server dice perché: `cattura formato negoziato:
1460x888` e `input regione 0: 0,0 1460x888` — **il monitor virtuale NASCE a quella misura**, quindi
`ADATTA_TELA` non c'entra e dall'indirizzo non si torna indietro. ⇒ **Resta `[?]`** quanto dei 41 ms
sia prodotto e quanto siano pixel in meno.

### ⭐ Quel che regge lo stesso, e regge bene

1. ⭐⭐ **Il miglioramento è più grande della dispersione, e di molto.** Il **peggiore** dei cinque
   giri di oggi (**111,03**) è **28,4 ms sotto il migliore** dei due del 14 agosto (**139,40**). Non
   c'è sovrapposizione fra i due gruppi.
2. ⭐⭐ **Il tratto B non può essere spiegato dai pixel**: `25,35 → 7,25 ms`, **−18,1 ms**, ed è il
   tratto dell'**input che va verso il desktop** — dove non passa nessun fotogramma. ⇒ Quei 18 ms
   sono **prodotto**, e sono la firma della cura del clic delle fasi 6 e 7.
   ⭐ E l'attribuzione non è un'opinione: **Q6** innesta 30 ms sul ramo d'andata e il banco li ritrova
   `[M]` **+31,57 · +31,68 · +32,36 ms proprio nel tratto 2** su tre giri su tre.
3. ⭐ **Il tratto D non si è mosso**: 16,23 → 16,36 ms. Un tratto che *non* cambia quando cambiano
   tela, codec e prodotto è la prova che la scomposizione sta separando cose diverse davvero.
4. ⛔ **E i due numeri sono presi allo stesso confine**: la strada di disegno di oggi è la stessa del
   14 agosto (§A.4), non quella nuova.

⇒ ⭐ **Conclusione onesta**: l'anello è passato da `[M]` **139,40 / 141,60** a `[M]` **88,4 – 111,0**
(mediana **99,07**). Di questi ~41 ms, **almeno 18 sono prodotto e dimostrati** (tratto B);
il resto è **`[?]` fra prodotto e una tela più piccola del 37,5 %**.

---

## A.4 ⛔⛔ CHE COSA NON HA FUNZIONATO

### 1. ⛔⛔ Il banco NON misura la strada di disegno che il prodotto usa oggi — ed è il difetto più grosso

`[M]` **Giro `08a-strada-normale-bitmaprenderer`, 22 agosto, senza coda d'indirizzo:**
**304 input spediti**, **1249 eventi ricevuti dalla scena**, **0 sonde CHIUSE su 304** ⇒ **codice
d'uscita 3**, «non ho niente da giudicare». Q2, Q3, Q4, Q5, Q6, Q7, Q8 tutti **NON ESEGUITI**.
Il resto della catena era sano: codifica in hardware, scena su `Meta-0`, input arrivato al desktop.

`[R]` **La causa, letta nel codice e non dedotta.** Dal 20 agosto (`DECISIONI.md` §5.4,
`src/pagina.html:2432`) la strada normale è `bitmaprenderer` + `createImageBitmap`. Su quella strada:

- **il deposito 2D non esiste** (`src/pagina.html:2518`: `this.deposito = null; this.deposito_p =
  null;`), e il prologo del banco legge i pixel **esattamente da lì** ⇒ zero marche lette;
- **`drawImage` non viene mai chiamato** ⇒ i tratti 9 e 10 non esistono e Q8 non gira;
- ⛔⛔ **e c'è di peggio, ed è la trappola vera**: il banco prende `t_dip` — il confine **scomodo**,
  «disegno finito» — subito dopo aver chiamato il richiamo del prodotto. Ma `createImageBitmap(f)`
  è **asincrona**: quel richiamo ritorna **prima** che qualcosa sia dipinto. ⇒ Se il deposito ci
  fosse, il banco consegnerebbe un numero **più basso del vero** chiamandolo «scomodo». È la forma
  di `LEZIONI.md` §1.20 in persona.

**La cura che ho applicato (l'unica modifica al banco):** `--coda-url`, un argomento nuovo che
appende una coda all'indirizzo. Con `--coda-url "?tela=2d"` la pagina prende la strada 2D — che è
**esattamente quella del 14 agosto** — e il banco misura di nuovo. Il banco è stato **ricertificato
dopo**: `[M]` 53 su 53, 16 guasti su 16. E la coda finisce nel verbale (`coda_url`).

⛔ **Che cosa questo NON risolve, e va scritto in fase 8**: il numero di §A.1 è **la strada 2D**, non
la strada che l'utente usa. `[?]` La differenza fra le due non è deducibile dai numeri che ci sono:
`SPECIFICHE.md`/§7.1 dice `createImageBitmap` **3,8 ms** mediani, ma il tratto 9 di questo banco
(17,48 ms) **non è il disegno**, è l'attesa del fotogramma — le due grandezze non si sottraggono.
⇒ **Chi vuole il numero della strada vera deve prima rifare il prologo del banco** (chiudere su
`transferFromImageBitmap` invece che su `drawImage`, e leggere i pixel dalla tela invece che dal
deposito). **È lavoro di mezza giornata, e senza di lui la fase 8 misura una strada morta.**

### 2. ⛔ Q5 e Q6 non stanno verdi insieme, e già il 14 agosto non ci stavano

| giro | Q5 (ritardo al ritorno) | Q6 (ritardo all'andata) |
|---|---|---|
| 14 ago `b30-o2-finale` (**il 139,40**) | **rosso** | **rosso** |
| 14 ago `b30-o2-finale2` (**il 141,60**) | **rosso** | verde |
| 22 ago `-2` | verde | **rosso** |
| 22 ago `-3` | **rosso** | verde |
| 22 ago `-adattano-1`, `-4`, `-5` | verde | verde |

⇒ ⛔ **Il 139,40 della fase 4 è stato consegnato da un giro con TUTT'E DUE le tarature rosse.**
Non lo dice nessun documento. Oggi le tarature stanno verdi **3 giri su 5**, cioè meglio di allora,
ma non sempre.
`[R]` **Il modo in cui falliscono è sempre lo stesso e non è casuale**: il surplus finisce nel
tratto giusto (`il_surplus_sta_in` lo nomina, `nel_tratto_giusto` a parte), **ma se ne vede un pezzo
anche altrove** — quasi sempre nel tratto 3, «l'attesa del quadro». ⚠ Ha una spiegazione fisica
plausibile: ritardare l'input ne cambia la **fase** rispetto al quadro del compositore, quindi
l'attesa del quadro cambia per costruzione. `[?]` **Ipotesi, non misura** — chi la vuole `[M]` la
prova innestando ritardi non multipli di 16,7 ms.

### 3. ⛔ La TASTIERA non chiude quasi mai — e non era buona nemmeno prima

`[M]` sonde di tastiera chiuse: oggi **0 su 208** · **0 su 212** · **8 su 196** · **5 su 202** ·
**16 su 198**. Il 14 agosto: **27 su ~486** · **35 su ~744**, con mediane di **1007 ms** e **152 ms**
— cioè numeri che non vogliono dire niente.
⇒ ⛔ **Nessun documento deve citare un ritardo di tastiera preso da questo banco**, né oggi né dal
14 agosto. `[?]` Se sia la scena, l'eco o il prodotto **non l'ho aperto**: è fuori dal mio punto.

### 4. ⛔ La scena vecchia non lascia il posto, e il primo giro l'ho perso così

`[M]` primo tentativo con `?tela=2d`: **«la scena non prende il fuoco del puntatore»**, sei
tentativi, e il banco ha rifiutato di misurare — correttamente: un numero preso lì sarebbe preso su
una **miniatura dentro la Panoramica di GNOME**, scala 0,79, senza CRC e senza eco.
`[R]` La causa: `scena-avvia` dice «la scena è già viva» e riusa quella del giro precedente, che il
fuoco l'ha perso. ⇒ **Rimedio: `scena-ferma` fra un giro e l'altro.** Fatto per tutti i giri
successivi. ⚠ Va scritto nel banco: oggi il rimedio è nella testa di chi lo lancia.

### 5. ⚠ Due difetti minori, dichiarati e non curati

- ⛔ **`coda_url` non arriva nell'`esiti.jsonl`**: sta nel verbale su disco ma non nella riga
  depositata. ⇒ Chi rilegge `04-b30-esiti.jsonl` **non può sapere su quale strada di disegno** è
  stato preso un numero. Il mio l'ho messo nel nome del giro (`08a-tela2d-*`); non basta come regola.
- ⛔ **`scena-costruisci` di `04-b30-lancia.sh` non funziona**: `ssh → enter.sh → bash -c` ha tre
  livelli di virgolette e `$L`/`$P` si perdono per strada ⇒ `gcc -o /scena.nuovo`. `[M]` visto oggi.
  Rimedio: la costruzione sta in un **file** (`08-a-scena-costruisci.sh`), non in una riga.

---

## A.5 ⛔ Che cosa resta `[?]` dopo di me

| | |
|---|---|
| ⏳ **quanto dei 41 ms è prodotto** | la tela è passata da 1920×1080 a 1460×888 (**62,5 % dei pixel**) e il flusso da 10 a 8 bit, e non ho trovato il modo di rimettere la tela di allora (`?adatta=no` non basta: il monitor virtuale nasce già a quella misura). **Almeno 18 ms sono prodotto** (tratto B, dimostrato da Q6); il resto è aperto |
| ⏳ **la strada `bitmaprenderer`** | il numero che l'utente vive **non è mai stato misurato da questo banco**. Serve il prologo rifatto (§A.4 punto 1) |
| ⏳ **il tratto C, 23,25 ms e la dispersione più larga di tutte** ([13,86 – 28,28]) | è «la scena riceve l'input → la scena disegna». ⚠ È in parte **la scena del banco**, non il prodotto: prima di curarlo bisogna sapere quanto sia suo |
| ⏳ **i ~16 ms non spiegati dentro il tratto 5** | oggi il tratto 5 vale 24,19 e il primo fotogramma dichiara conversione 2,7 + caricamento 1,6 + codifica 7,2 = **11,5 ms** ⇒ ne restano **~12,7** che nessuno dei tre spiega. Il margine c'è ancora, ed è più piccolo di prima |
| ⏳ **i sei buchi del video dell'utente** | ⛔ **non li ho separati**: il mio giro non ha una traccia di rete abbastanza fine per attribuirli. Resta il punto §2.4 della fase |
| `[?]` **`EncSliceLP`** | `[M]` il codificatore dichiara ancora **bassa potenza, non la codifica piena** — riga letta oggi, e la fase 9 la deve sapere |
| ⚠ **il palco era condiviso** | i due server dell'utente (7730, 7731) giravano durante tutti i giri. È la spiegazione più economica della dispersione 88 – 111 ms, e non l'ho isolata |

---

## A.6 Che cosa ho lasciato sulla macchina

⭐ Utente **`provaa8`** (uid 1041) con sessione GNOME, albero `/media/REMOTIX/src/08-a-src`, scena
`/media/REMOTIX/src/08-a-scena-lav/08-a-scena`, terreno `/media/REMOTIX/src/08-a-terreno.sh`,
directory di lavoro `/media/REMOTIX/tmp/08-a`. Prodotto, ponte e scena **spenti**; si riaccendono
con `08-a-lancia.sh accendi`. ⛔ **Le porte 7730 e 7731 e le directory dell'utente non sono mai state
toccate**, e il conteggio dei vicini lo dichiara in ogni riga di registro del terreno.


---

## 4-C · ⭐⛔ AGENTE C — i ~16 ms hanno un nome, **e la copia zero NON è stata fatta** · *22 agosto 2026*

> ### ⛔⛔ QUEL CHE MANCA SI DICE PRIMA DI QUEL CHE C'È — e la colpa è del direttore, non dell'agente
>
> **La copia zero — il titolo storico di questa fase — non è entrata.** Il tempo è andato nello
> **strumentare**, che era l'ordine che gli ho dato io: *«prima si strumenta, poi si cura; una cura
> misurata con uno strumento che non c'era prima non ha un prima»*. L'ordine era giusto e lo
> rifarei; ⛔ **la stima del tempo era mia ed era sbagliata.**
>
> ⇒ Resta il budget `[M]`, **da misurare col banco e non da sottrarre a tavolino**: copia 1,65 +
> conversione 8,15 + caricamento 1,16 = **10,96 ms su 18,86, il 58 % del tratto**.
>
> ### ⭐⭐ E i ~16 ms hanno un nome — due, e nessuno dei due era quello che cercavamo
>
> `[M]` Strumentato **dentro il prodotto**, dieci voci in fila, mediane su 512 fotogrammi, **resto
> 0,02 ms** — la scomposizione non ha buchi. 1920×1080, HEVC in hardware, 2 450 fotogrammi:
>
> | voce | ms |
> |---|---|
> | ⛔ **il produttore (Mutter)** — dal suo `pts` alla nostra richiamata | **5,79** |
> | ⛔ **`misura_i_pixel()`** — la diagnostica | **5,34** |
> | la conversione (`sws_scale`) | 5,39 |
> | la copia | 1,30 |
> | la codifica, in hardware | 2,18 |
> | il caricamento sulla GPU | 0,98 |
> | il fotogramma che aspetta nel posto | **0,08** |
> | **totale** | **21,61** |
>
> 1. ⛔ **5,79 ms sono di Mutter**: più di un terzo del margine **non è nostro**;
> 2. ⛔⛔ **5,34 ms sono DIAGNOSTICA**: `misura_i_pixel()` legge **ogni pixel di ogni fotogramma**
>    per riempire **una riga di registro che si scrive una volta sola**;
> 3. ⭐⭐ **e l'ipotesi del coordinatore era sbagliata**, refutata dallo strumento costruito *prima*
>    della cura: credevo fosse il fotogramma che invecchia nel posto, ⇒ `[M]` **0,08 ms**.
>
> ### ⛔⛔ E la cura non ha reso quel che aveva tolto — **i tratti non si sommano**
>
> Il giro sui pixel è passato a cadenza (500 ms). Prima/dopo **alternato**, tre giri, stesso albero,
> md5 verificati diversi: `[M]` **21,19 → 18,86 ms (−11 %)**.
>
> ⛔ **Ma ha tolto 7,28 e guadagnato 2,33**: `sws_scale` si è ripreso **+3,84 ms** (3 giri su 3, in
> tutt'e due i versi) perché la scansione dei pixel **gli scaldava la cache**.
> ⛔⛔ **E i fotogrammi consegnati NON sono saliti**: 1 271 → 1 242.
>
> ⇒ ⭐ **Per la regola di §2.2 punto 1, questa non è ancora una vittoria** — «si contano i
> fotogrammi che la pagina dipinge, non i millisecondi». La cura resta (una diagnostica che costa il
> 25 % del tratto va tolta comunque), ma **il guadagno va rimisurato col banco di B**, sulla scena
> vera, contando i fotogrammi.

*22 agosto 2026. Macchina di prova NIC-OS (Intel i5-13500T, iGPU su `/dev/dri/renderD128`),
utente `provac8`, porta **7752**, albero `/media/REMOTIX/src/08-c-src`, lavoro
`/media/REMOTIX/tmp/08-c`.*

> ### ⛔ E LA PRIMA COSA E' LA PORTA, perche' era assegnata a due
>
> Il mandato mi dava la **7742**. `[M]` La 7742 e' gia' l'**ancora dell'orologio del banco A**
> (`/media/REMOTIX/src/08-a-terreno.sh`, `PORTA_ANCORA=${PORTA_ANCORA:-7742}`), e mentre A girava
> `ss` la contava **occupata**. ⇒ Ho preso **7750 · 7752 · 7753** e l'ho scritto, invece di far
> fallire il ponte di un altro banco a meta' misura (`LEZIONI.md` §1.24: *il ban di uno ferma
> tutti*). ⚠ Chi assegna le porte alla prossima fase legga `08-a-terreno.sh` prima.

---

## C.1 · ⭐⭐ I ~16 ms hanno un nome — e **cinque non erano nostri**

### Che cosa e' stato costruito

`src/cattura.h` · `src/cattura.c` · `src/figlio.c`. Il tratto `cattura → primo byte` adesso si
scompone **dentro il prodotto**, e la riga esce nel registro **una volta al secondo**:

```
⭐ TRATTO cattura → byte fuori: mediana 21.61 ms (max 32.87) su 512 fotogrammi del campione,
   2450 in tutto — produttore 5.79 · allocazione 0.00 · copia 1.30 · nel posto 0.08 ·
   misura 5.34 · conversione 5.39 · caricamento 0.98 · codifica 2.18 · spedizione 0.01 · resto 0.02
```

Dieci voci **disgiunte e in fila**, **mediane** (non medie) su un anello di 512 fotogrammi, col
**massimo** accanto. ⭐ L'ultima voce e' il **`resto`**: quel che il totale ha in piu' della somma
delle altre. `[M]` vale **0,02 ms** ⇒ **la scomposizione non ha buchi**, ed e' la stessa proprieta'
che rendeva credibile quella della fase 4 (scarto 0,32 su 139).

⚠ **Il confine si dichiara**: qui il tratto finisce **quando i byte partono verso il padre**, non
quando arrivano in pagina. Il 30,37 ms della fase 4 e' misurato dal client; questo e' **il pezzo di
quello che sta dentro il figlio**, ed e' l'unico che questo processo puo' vedere senza dedurre.
⇒ ⛔ I due numeri **non si sottraggono fra loro**.

### Il banco, e perche' **senza browser**

`08-c-giro.sh` sulla macchina di prova: attacca `banchi/04-b31-cliente.py` (cliente RCP in Python,
dentro il contenitore), aspetta il palco, **legge dal registro** su quale monitor sta — non lo
indovina — e accende li' sopra la scena di `banchi/04-b30-scena.c`, pretendendo che il conto dei
disegni **cresca** («vivo» non e' «disegna»).
⭐ Cliente e prodotto stanno **sulla stessa macchina** ⇒ il `pts` di Mutter e il `time.monotonic()`
del cliente sono lo **stesso `CLOCK_MONOTONIC`**: niente ancora d'orologio, niente Xvfb, niente CDP.

### ⭐⭐ IL NUMERO — `[M]` 1920×1080, HEVC in hardware, 2 450 fotogrammi

| voce | mediana | max | di chi e' |
|---|---|---|---|
| **produttore** *(pts di Mutter → la nostra richiamata)* | **5,79 ms** | 11,48 | ⛔ **di Mutter, non nostro** |
| allocazione *(la `g_malloc` del posto)* | 0,00 | 0,02 | nostro — e non costa: il buffer si riusa |
| **copia** *(la `memcpy` nella richiamata di tempo reale)* | **1,30** | 2,26 | nostro |
| **nel posto** *(il fotogramma che invecchia aspettando)* | **0,08** | 6,52 | nostro |
| **misura** *(`misura_i_pixel()`)* | **5,34** | 13,91 | ⛔ **nostro, e DIAGNOSTICA** |
| conversione *(`sws_scale`)* | 5,39 | 7,89 | nostro |
| caricamento *(→ GPU)* | 0,98 | 1,75 | nostro |
| codifica | 2,18 | 2,65 | nostro |
| spedizione | 0,01 | 0,03 | nostro |
| **resto** | **0,02** | 1,41 | ⭐ **niente buchi** |
| **TOTALE** | **21,61** | 32,87 | |

### ⇒ Le due risposte, e la seconda e' una **smentita mia**

1. ⛔⛔ **`5,79 ms su ~16 sono di Mutter.** E' il tempo fra l'istante che Mutter stesso timbra sul
   fotogramma e l'istante in cui la nostra richiamata lo riceve. Non c'e' niente da limare: e' il
   compositore. ⇒ **Piu' di un terzo del margine piu' grosso della fase non e' nostro.**
2. ⛔ **`5,34 ms sono una diagnostica.** `misura_i_pixel()` legge **ogni pixel** di ogni fotogramma
   per dire tre cose — il range, «e' nero», «e' uniforme». ⭐ E contando riga per riga chi le
   consuma: nel prodotto finiscono in **UNA** riga di registro, scritta **UNA VOLTA**, al montaggio
   del palco. ⇒ **Trenta-sessanta scansioni al secondo da 5,34 ms per una riga sola.**

⭐ **E la mia ipotesi di partenza era un'altra, ed e' stata REFUTATA dal primo giro.** Credevo che i
~16 ms fossero il fotogramma che **invecchia nel posto** aspettando che il ciclo tornasse a
chiederlo — la fase 4 aveva scritto *«attese a vuoto 0,00/s: ce n'era sempre uno pronto»*, che letto
al contrario suonava «allora aspettava noi». `[M]` **`nel posto` vale 0,08 ms**: il fotogramma **non
invecchia**. L'ipotesi era verosimile e sbagliata, e a dirlo e' stato lo strumento che era stato
costruito **prima** della cura.

### ⚠ Il costo su CPU pura, che dice come cresce

`[M]` banco `08-c-scansione.c`, CPU sola, un processo solo, mediana di 80 giri:

| | 1920×1080 | 2560×1080 | 2560×1440 |
|---|---|---|---|
| **la scansione intera** | **5,36 ms** | 6,78 | **8,89** |
| la stessa a campione 1/8 | 0,10 | 0,12 | 0,17 |
| la `memcpy` del posto | 0,65 | 0,82 | 0,63 |
| `malloc`+tocco+`free` (se il posto non si riusasse) | 0,48 | 0,60 | 0,32 |

⇒ **Cresce coi pixel**: su una tela grande sarebbe **peggio**, non uguale.

> #### ⛔ E LO STRUMENTO HA MENTITO AL PRIMO GIRO, nella direzione comoda
> Il primo `08-c-scansione` diceva **0,000 ms** per una scansione di 14 MB. ⛔ Non era una scoperta:
> il risultato non usciva dalla funzione e **`-O2` aveva cancellato l'intero ciclo**. E' `LEZIONI.md`
> §1.21 dentro lo strumento — *uno strumento che si rompe sotto carico mente quando serve* — e
> mentiva dicendo *«la scansione non costa niente»*, cioe' esattamente quel che avrebbe chiuso la
> caccia. ⇒ Adesso c'e' una **sentinella `volatile`**, e il commento dice perche'.

---

## C.1-bis · La cura, e ⛔ **il conto NON torna come sperava**

`src/cattura.c`: il giro sui pixel si fa sul **primo** fotogramma e poi **al piu' ogni 500 ms**
(`MISURA_PIXEL_OGNI_MS`). La risposta resta **esatta** — cambia solo ogni quanto si da'.

⛔ **E `nero == FALSE` adesso puo' voler dire «non ho guardato».** Per questo `CatturaConsegna` ha un
campo nuovo, **`pixel_misurati`**, e chi legge `nero`/`uniforme` deve guardare prima quello —
esattamente come `stride_letto` sta accanto a `stride` (`LEZIONI.md` §1.9). Sui fotogrammi saltati
**non si copia il valore di prima**: sarebbe due misure sotto la stessa etichetta.

⛔ **Quel che NON ho fatto, e la ragione**: guardare **un pixel ogni otto** costerebbe `[M]` 0,10 ms
invece di 5,36 — meglio ancora. Scartata: cambierebbe il **significato**. Un fotogramma nero tranne
una regione saltata verrebbe dichiarato **NERO**, e una riga che accusa il nero quando il nero non
c'e' manda la caccia dalla parte sbagliata — che costa molto piu' di 5 ms.

### ⭐⭐ IL PRIMA E IL DOPO — tre giri **ALTERNATI**, stesso banco, stessa scena, stessa compagnia

*⛔ Alternati e non in fila: `banchi/03-solo.py` dice che un banco che misura un tempo deve essere
solo, e **non lo ero** (due sessioni GNOME, nove processi `remotix`, carico 1,25-2,09). Alternare e'
l'unico modo onesto di misurare su questa macchina oggi. I due binari nascono dallo **stesso
albero**, cambia **una costante**, e il banco **verifica che gli md5 siano diversi** prima di
misurare.*

| tratto | **prima** *(scansione su ogni fotogramma)* | **dopo** *(a cadenza)* | Δ |
|---|---|---|---|
| produttore | 4,45 | 5,14 | +0,69 |
| allocazione | 0,00 | 0,00 | — |
| copia | 1,30 | 1,65 | +0,35 |
| nel posto | 0,08 | 0,08 | — |
| ⭐ **misura** | **7,28** | **0,00** | **−7,28** |
| ⛔ **conversione** | **4,31** | **8,15** | **+3,84** |
| caricamento | 0,90 | 1,16 | +0,26 |
| codifica | 2,18 | 2,08 | −0,10 |
| spedizione | 0,01 | 0,02 | — |
| resto | 0,03 | 0,04 | — |
| **TOTALE** | **21,19** | **18,86** | ⭐ **−2,33 ms (−11 %)** |
| **fotogrammi in 40 s** | 1 268 · 1 271 · 1 276 | 1 240 · 1 242 · 1 340 | ⚠ **fermi** |

*(mediana dei tre giri per riga; i tre giri concordano — `misura` 6,48/7,79/7,28 prima, 0,00 sempre
dopo; `conversione` 4,17/4,18/4,31 prima, 8,40/7,95/8,15 dopo.)*

### ⛔⛔ E QUI STA LA COSA CHE VA DETTA PRIMA DEL GUADAGNO

**Ho tolto 7,28 ms e ne ho guadagnati 2,33.** Gli altri **~4 ms li ha ripresi `sws_scale`**, che nei
tre giri passa da 4,3 a 8,2 — **in tutti e tre, in tutt'e due i versi**. Non e' rumore.

⭐ **E il meccanismo si spiega, ed e' istruttivo**: la scansione leggeva gli **8 MB del fotogramma
subito prima** che `sws_scale` leggesse gli stessi 8 MB. **Scaldava la cache per lui.** Tolta la
scansione, il traffico verso la memoria lo paga swscale. ⇒ *Una parte di quei 5,34 ms non era spreco:
era prefetch fatto per sbaglio.*

⛔ **E i fotogrammi consegnati NON sono saliti** (1 271 → 1 242 di mediana, dentro la dispersione dei
giri). ⇒ La cura **non compra fluidita'**: compra **2,33 ms di ritardo** e basta. Alla velocita'
mediana dell'utente (3 400 px/s) valgono **−8 px** di distacco; ai suoi picchi (12 400 px/s),
**−29 px** su ~360. ⚠ **E' una limatura vera e piccola, e va chiamata cosi'.**

⭐ **Ma la lezione vale piu' del guadagno**: ⛔ **non si sommeranno mai i tratti tolti sperando che
si sottraggano dal totale.** In questo tratto le voci **non sono indipendenti**: si passano la cache.
Chi togliera' `conversione` e `caricamento` con la copia zero deve **rimisurare il totale**, non
sottrarre 9,3.

---

## C.2 · ⛔ **LA COPIA ZERO NON E' STATA FATTA** — e questo e' il buco piu' grosso che lascio

Non ho toccato `CATTURA_STRADA_SCHEDA` ne' l'importazione del DMA-BUF come superficie VA-API.
`src/figlio.c` chiede ancora `CATTURA_STRADA_MEMORIA`.

⛔ **La ragione e' il tempo, non un ostacolo tecnico**, e va detta cosi'. Il mandato metteva
l'ordine — *«prima si strumenta, poi si cura»* — e strumentare e' costato: costruire il banco
server-side, l'utente, la sessione, la scena, il cliente senza browser, e poi tre giri alternati per
non consegnare un numero contaminato. ⇒ Ho consegnato **la misura** e **la cura piu' piccola**, e la
copia zero resta intera per chi viene dopo.

⭐ **E gli lascio il budget misurato**, che prima non c'era:

| che cosa la copia zero cancella | `[M]` oggi |
|---|---|
| `copia` (la `memcpy` nel posto) | **1,65 ms** |
| `conversione` (`sws_scale`) | **8,15 ms** |
| `caricamento` (memoria → GPU) | **1,16 ms** |
| **in tutto** | **10,96 ms su 18,86 — il 58 % del tratto** |

⚠ **E il numero da NON credere e' proprio quello**: vedi C.1-bis. Le voci si passano la cache, e
9,3 tolti hanno reso 2,3. ⇒ **La copia zero va misurata col banco, non stimata dalla tabella.**
⭐ Il banco per farlo c'e' ed e' quello di qui: `08-c-giro.sh` + `08-c-ab.sh` (due binari dallo
stesso albero, alternati, md5 verificati diversi).

⭐ **E resta vero che e' la strada giusta**: la copia zero non **sposta** il traffico di memoria come
ha fatto la mia cura — lo **toglie**. Il fotogramma non esce piu' dalla GPU.

### ⏳ La cura del RILASCIO — la scelta, con la ragione

⛔ Non l'ho scritta (non c'e' la copia zero da rilasciare), ma il mandato chiedeva **quale** e
**perche'**, e la risposta la lascio decisa: **trattenere il `pw_buffer` fino a lettura finita**, non
chiedere `SPA_META_SyncTimeline`.

| | |
|---|---|
| ⭐ **trattenere il buffer** | e' **nostro** e vale su **ogni** produttore. `can_reuse_pw_buffer` si arrende quando la timeline manca, e allora Mutter riusa il buffer mentre VA-API legge `[R]`: trattenendolo il caso non esiste, qualunque cosa il produttore offra. ⚠ Il prezzo e' **un buffer in meno** dei quattro che Mutter ricicla (`DECISIONI.md` §2.3-ter), ed e' un prezzo che si conta |
| ⛔ **chiedere la timeline** | dipende da **quel che il produttore offre**, ed e' la forma che questa fase ha gia' pagato: quando non c'e', non c'e' nessun errore — c'e' **la schermata che si alterna**, che e' il difetto da cui la caccia era partita dalla parte sbagliata (`LEZIONI.md` §8). ⇒ Una cura che sparisce in silenzio su un compositore che non la offre e' precisamente `LEZIONI.md` §1.8 |

⭐ E c'e' un terzo argomento che decide: `LEZIONI.md` §1.25 — *una cura si cerca dovunque valga*.
Trattenere il buffer vale su Mutter, su KWin e su wlroots senza chiedere niente a nessuno; la
timeline va richiesta a ognuno e verificata su ognuno.

⛔ **E non si rifa' la superficie di accumulo**: il DMA-BUF di Mutter **non e' un diff** — c'e'
scritto in testa a `cattura.h`, `[M]` 12 agosto, danno parziale su **410 fotogrammi su 410** e le
barre SMPTE **intere** nel buffer.

---

## C.3 · ⭐ La scheda del codificatore — **e c'era gia' quasi tutto**

⛔ **Il timore del mandato — *«se il codificatore cercasse la discreta ripiegherebbe in CPU senza un
errore»* — NON si applica**, e vale la pena scriverlo invece di curare due volte:

| | |
|---|---|
| il nodo | ⭐ **dichiarato**, non scelto: `figlio.c` `NODO_RENDERING "/dev/dri/renderD128"`, passato a `av_hwdevice_ctx_create` |
| il fornitore | ⭐ **letto** con `vaQueryVendorString` e messo **dentro il nome** del codificatore |
| l'entrypoint | ⭐ **letto dal driver** con `vaQueryConfigEntrypoints` **prima** di aprire, e ⛔ **non si ripiega sull'altro** |
| «e' in hardware?» | ⭐ **chiesto al componente** (`componente_e_hardware()`: accetta un formato di *superficie*), non letto nel nome |
| il ripiego in software | ⭐ **dichiarato** nel registro |

⇒ ⭐ `[M]` dal registro di oggi: *«HEVC 8 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 ·
Intel iHD driver for Intel(R) Gen Graphics - 25.2.3 · ⚠ EncSliceLP, bassa potenza — NON e' la
codifica piena)»*.

### Che cosa ho aggiunto

**1. ⛔ La riga del ripiego nominava il codificatore SBAGLIATO** — difetto vero, trovato refutando.
`figlio.c` scriveva **«hevc_vaapi»** e **«libx265»** dentro le virgolette; ⛔ ma dal 20 agosto quel
ramo serve **anche H.264**, e quando a non aprirsi era `h264_vaapi` il registro accusava un
codificatore che nessuno aveva chiesto e nominava un ripiego che non sarebbe stato usato. ⇒ *Il
numero giusto e la parola sbagliata accanto* (`LEZIONI.md` §1.20). Adesso i due nomi si **stampano**,
e il ripiego viene da **un posto solo** — `codificatore_ripiego_software()`, nuovo in
`codificatore.h`, perche' averlo in due posti sarebbe peggio di tutt'e due.

**2. ⭐⭐ La misura massima si chiede AL DRIVER, prima di aprire** — ed e' anche il punto 4 di D.
`codificatore.c`, `vaGetConfigAttributes(VAConfigAttribMaxPictureWidth/Height)`. **Tre esiti e non
due**: se il driver non risponde o non dichiara l'attributo, **non si conclude niente** e lo si
scrive — non e' «non c'e' limite», e' «non ho guardato». ⇒ `[M]` dal registro di oggi:
*«⭐ il driver dichiara al massimo 16384x12288 per «hevc_vaapi» su /dev/dri/renderD128, e 1920x1080
ci sta — CHIESTO al driver, non dedotto dal nome»*.

### ⭐ E il guasto innestato che rende quel verde credibile

`[M]` banco `08-c-scheda.c`, che chiede al driver e **prova una misura oltre il limite**:

| profilo | entrypoint | massimo dichiarato | 4096×2160 | **4112×2160** | 7680×4320 |
|---|---|---|---|---|---|
| H.264 High | EncSliceLP | **4096 × 4096** | si | ⛔ **NO** | ⛔ NO |
| H.264 High | EncSlice *(piena)* | ⚠ il driver non risponde (13) — **non e' «nessun limite»** | | | |
| HEVC Main | EncSliceLP | **16384 × 12288** | si | si | ⭐ si |
| HEVC Main | EncSlice *(piena)* | ⚠ il driver non risponde (13) | | | |
| HEVC Main10 | EncSliceLP | 16384 × 12288 | si | si | si |

⇒ ⭐ **Il numero di D e' confermato al pixel**: 4096 si', 4112 no. E il controllo **sa dire di no** —
la riga dei 4112 px cambia verdetto, quindi non e' verde per costruzione.
⭐ **Due fatti in piu' che D non aveva**: il massimo di HEVC e' **16384 × 12288** (non 4320), e
l'entrypoint **pieno non esiste affatto** su questa scheda per nessuno dei due codec — che e' la
conferma indipendente del perche' `POTENZA_RENDERING` e' BASSA.

⛔ **E la verifica NON passa da ffmpeg**, che e' il punto 5 di D: `[M]` `-low_power 0` sull'Intel
apre lo stesso `EncSliceLP` **senza fallire**. Qui si parla al driver.

---

## I quattro punti dell'agente D

| | che cosa ho fatto |
|---|---|
| **1 · ⛔ ci si arrende su una CHIAVE** | ⭐ **CURATO e PROVATO COL GUASTO.** Su una chiave non ci si arrende piu': si scende la scala finche' ha scalini, e la riga lo **dichiara** («l'immagine uscira' piu' brutta»). Il conto dei tentativi vale **solo per i delta**. L'unico caso in cui una chiave non parte e' il **fondo della scala**, e la riga dice **quale dei due** e' — «non c'e' piu' niente da abbassare» ≠ «mi sono arreso» |
| **2 · ⛔ la scala e' corta di uno scalino** | ⭐ **CURATO**: `CRF_PASSO` 6 → **9** ⇒ 26 → 35 → 44 → 51, e comprende il QP 44 che `[M]` ce la faceva (11,056 MiB). ⭐ Alzato il **passo** e non i tentativi, con la ragione di D accanto: un tentativo a 8K costa 91-108 ms. ⚠ **Il valore esatto NON e' deciso qui**: c'e' scritto nel commento che il punto di lavoro fra qualita' e banda e' della **fase 9** |
| **3 · ⭐ `max_b_frames = 0`** | ⭐ **NON TOCCATO**, e adesso il commento porta il numero: **59 figure buttabili su 120** e **−16 % di banda** (PSNR −0,065 dB) **contro +67 ms di riordino**, che da soli sfondano i 50 ms dati a *tutto* il pezzo nostro. ⇒ Comprerebbe banda vendendo risposta — lo stesso commercio per cui §6.1 ha chiuso l'anello in parallelo |
| **4 · ⚠ i 4096 px di `h264_vaapi`** | ⭐ **CURATO**, e sta qui sopra in C.3: si chiede al driver **prima di aprire**, e il numero di D e' confermato al pixel |
| **5 · ⚠ i due vicoli ciechi** | ⭐ **Rispettati**: non ho toccato `-max_frame_size` (`[M]` rifiutato in CQP), e la verifica dell'entrypoint **non passa da ffmpeg** |

### ⭐⭐ Il guasto innestato del punto 1, perche' quel ramo non si percorre mai da solo

⛔ Il tetto e' 16 MiB e `[M]` alla tela di prova la chiave piu' grossa vale ~21 KB — lo **0,13 %**.
⇒ Sul banco quel ramo **non si tocca mai**, e una cura che non si percorre e' **verde per
costruzione**. ⭐ Ho abbassato il **tetto** (`TETTO_FOTOGRAMMA` a **6000 byte**), non alzato il
contenuto, e ricostruito un binario apposta.

`[M]` 22 agosto 2026, con il guasto addosso:

```
⚠ CHIAVE sopra il tetto: scendo a QP 35 e RIPROVO (tentativo 2).  ⛔ Una chiave non si abbandona (§5.2)…
⚠ CHIAVE sopra il tetto: scendo a QP 44 e RIPROVO (tentativo 3).  …
```

⭐⭐ **E la prova vera non e' il registro, e' il fotogramma**: `fotogramma 91 · t = 4,002 s · chiave ·
4 728 byte · 1920×1080` — **sotto il tetto falso**, e **994 fotogrammi completi con 2 chiavi** nel
giro. ⛔ Prima della cura quel giro avrebbe scritto *«nemmeno dopo 3 ricodifiche… il fotogramma NON
parte»* e **nessuna chiave sarebbe uscita**.

⚠ **Quel che il guasto NON ha esercitato**: il ramo «delta abbandonato» — a 1920×1080 i delta stanno
sotto i 6 000 byte da soli. `[?]` Resta non percorso.

---

## ⛔ Che cosa NON ha funzionato

1. ⛔⛔ **La mia ipotesi sui ~16 ms era sbagliata.** Credevo fosse il fotogramma che invecchia nel
   posto: `[M]` **0,08 ms**. Refutata dal primo giro dello strumento.
2. ⛔ **La cura ha reso un terzo di quel che toglieva** — 7,28 ms tolti, **2,33** guadagnati, perche'
   `sws_scale` si e' ripreso ~4 ms che la scansione gli scaldava in cache. ⇒ ⛔ **In questo tratto le
   voci non sono indipendenti**, e i tratti tolti **non si sommano**.
3. ⛔ **I fotogrammi consegnati non sono saliti** (1 271 → 1 242 di mediana, dentro la dispersione).
   La cura compra ritardo, non fluidita'. E' la forma mite di `LEZIONI.md` §6.2, e va detta.
4. ⛔ **Il banco della scansione mentiva**: `-O2` aveva cancellato il ciclo e il banco diceva
   **0,000 ms** — nella direzione che avrebbe chiuso la caccia.
5. ⛔ **Il primo tentativo di costruire i due binari e' uscito con lo STESSO md5**:
   `costruisci.sh:110` fa `rm -f remotix *.o`, quindi la `cattura.o` compilata col `-D` spariva.
   ⚠ Senza il controllo degli md5 il confronto avrebbe detto *«la cura non cambia niente»* misurando
   **due volte la stessa cosa**. ⇒ Il controllo resta nel banco.
6. ⛔ **La copia zero non e' stata fatta.** Vedi C.2.
7. ⚠ **Non ero solo sulla macchina** (`banchi/03-solo.py`): due sessioni GNOME, nove `remotix`,
   carico 1,25-2,09. ⇒ ⛔ **I valori assoluti di questo rapporto vanno letti come un tetto.** Il
   prima/dopo regge perche' e' **alternato**; i totali singoli no. Nell'ultimo giro della giornata,
   con la macchina piu' carica, la stessa `conversione` e' salita da 8,15 a **11,9** senza che nulla
   cambiasse nel codice — ed e' la misura di quanto la compagnia sposti i numeri.

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **la copia zero** | non fatta. Budget `[M]` **10,96 ms su 18,86 (58 %)** — ⛔ da **misurare**, non da sottrarre |
| ⏳ **i 5,79 ms del produttore** | `[M]` sono di Mutter. `[?]` Non so **di che cosa siano fatti** (composizione? il ciclo di PipeWire? la cadenza del compositore?) e non e' detto che si possa sapere da qui |
| ⏳ **`conversione` che si prende la cache** | `[M]` +3,84 ms quando la scansione sparisce. `[?]` Se `sws_scale` acceda alla memoria in modo migliorabile (piu' thread, flag diversi) non e' stato guardato — ⚠ e la copia zero lo cancella comunque |
| `[?]` **il ramo «delta abbandonato»** | non percorso nemmeno col guasto innestato |
| `[?]` **`banchi/02-cattura-prodotto.c` legge `nero`/`uniforme` senza `pixel_misurati`** | ⛔ **non e' mio e non l'ho toccato.** Prende pochi fotogrammi e il primo si misura sempre, quindi oggi non sbaglia; ma la riga giusta e' stamparlo. **Una riga, per chi lo possiede** |
| `[?]` **il valore di `CRF_PASSO`** | 9 e' *sufficiente*, non *giusto*: il punto di lavoro e' della **fase 9** |
| `[?]` **il distacco in pixel** | ⛔ non l'ho misurato: e' l'anello intero, ed e' del punto A |

---

## Come si rifa'

Tutto sulla macchina di prova, `/media/REMOTIX/src/`:

| | |
|---|---|
| `08-c-terreno.sh` | utente `provac8`, sessione GNOME **senza** `--virtual-monitor`, prodotto sulla **7752** — derivato da quello di A con `08-c-derivami.sh`, **non ricopiato** |
| `08-c-giro.sh` | un giro: cliente senza browser + scena sul monitor **letto dal registro**, e le righe `⭐ TRATTO` |
| `08-c-ab.sh` | ⭐ il prima/dopo **alternato** |
| `08-c-due-binari.sh` | i due binari dallo stesso albero, **con la verifica che gli md5 differiscano** |
| `08-c-scansione.c` | il costo del giro sui pixel, CPU pura, con la sentinella `volatile` |
| `08-c-scheda.c` | i limiti chiesti al driver, **con la misura oltre il limite** |
| `08-c-guasto-chiave.sh` · `08-c-prova-guasto.sh` | il guasto innestato di §5.2 |

⚠ Le copie di questi file stanno anche in
`…/scratchpad/fase8/`. ⛔ Nessuno di loro sta in `banchi/`: sono banchi di questo punto, e
`documenti-si-accorpano` dice che i rapporti degli agenti non si conservano — se il coordinatore li
vuole conservare, il posto e' `banchi/` con un nome `08-…`.


---

## 4-B · ⭐⭐⭐ AGENTE B — il banco del trascinamento, e **il locale ha un numero** · *22 agosto 2026*

> ### ⭐⭐⭐ LA SPECIFICA DELL'UTENTE SMETTE DI ESSERE UN DESIDERIO: adesso il «locale» è misurato
>
> *«La mia specifica è avere un'esperienza utente il più vicina possibile a una situazione locale,
> ma non identica: quello è impossibile.»* — §1.1. ⛔ **Finché il locale non aveva un numero, quella
> frase non era collaudabile da nessuno.** Adesso ce l'ha.
>
> | | ritardo | distacco | **in barre del titolo** |
> |---|---|---|---|
> | ⭐ **il locale**, stesso banco stessa scena | **27,58 ms** | 94 px | **0,13** |
> | **REMOTIX**, tre giri concordi entro l'1 % | **69,8 · 70,2 · 67,1 ms** | 201 · 206 · 194 px | **0,28 · 0,29 · 0,27** |
> | *(l'utente, a occhio, sul suo 2560)* | *~106 ms* | *~360 px* | *0,50* |
>
> ⇒ ⭐⭐ **Siamo a 2,4 volte il locale, e i 42 ms di differenza sono esattamente quel che aggiungiamo
> noi sopra al compositore.** Il mandato della fase si riscrive in una riga: **accorciare quei 42.**
>
> ⭐ **E l'utente aveva ragione anche sul limite**: il locale **non è zero** — è 27,58 ms, perché
> anche lì c'è un compositore e uno schermo. *«Ma non identica: quello è impossibile»* è confermato
> dalla misura, non concesso per cortesia.
>
> ⚠ **E lo scarto fra 0,28 e 0,50 si dichiara invece di limarlo a parole**: il banco gira a
> **1560 px** di larghezza, l'utente a **2560** — più pixel, più lavoro per fotogramma. `[?]` La
> differenza non è spiegata, ed è la prima cosa da rifare alla sua misura.

*22 agosto 2026. Da inserire in `fasi/08-l-anello.md` §3 (sviluppo), §4 (misure), §5 (non ha
funzionato) e §7 (resta `[?]`).*

---

## 1 · Che cosa è stato costruito

| file | che cos'è |
|---|---|
| `banchi/08-b67-elastico.py` | ⭐⭐ **il banco**: la mano dell'utente, la lettura dell'eco nei pixel, le tre unità, la separazione della rete, i buchi, i tredici guasti innestati |
| `banchi/08-b67-lancia.sh` | il lanciatore: porte, albero, contenitore, terreno, scena, misura |
| `banchi/08-b67-locale.py` | ⭐⭐ **il termine di paragone locale**, misurato sul ferro dal blocco condiviso della scena |
| `banchi/08-b67-esiti.jsonl` | i verbali dei giri |

⛔ **Non è stata toccata una riga di `src/`.**

⭐ **E niente è stato ricopiato che si potesse importare**: il palco, la distribuzione, il regime e
il **lettore certificato della marca** vengono da `03-b17-ritardo.py`; l'eco e il lettore del blocco
condiviso da `04-b30-anello-input.py`; **la scena è `04-b30-scena.c` senza una riga cambiata**; il
terreno è `04-b32-terreno.sh` **guidato dall'ambiente**, non una sua copia. L'unico pezzo ricopiato
è `batti()` (il `thisisunsafe`), e la ragione sta scritta accanto: il modulo che lo contiene fa
`argparse` a livello di modulo, e importarlo lancerebbe un altro banco.

---

## 2 · ⛔⛔ La porta 7741 **non era libera**, ed era di un altro agente della fase

`[M]` `ss -tulnp` prima di toccarla:

```
udp 0.0.0.0:7741  users:(("remotix",pid=3446627))
    /media/REMOTIX/src/08-a-src/src/remotix --porta 7741
      --ban-file /media/REMOTIX/tmp/08-a/ban-7741
udp 0.0.0.0:7740 / 7742  ("python3")  → il PONTE di 08-a
```

⇒ ⛔ **Il mandato mi assegnava una porta che l'agente A stava già usando.** Non l'ho presa e non
l'ho spenta: `LEZIONI.md` §1.24 — *due banchi sulla stessa porta si ammazzano in silenzio, e il
rosso compare sul terzo* — e il ban-file era il suo, quindi un mio errore avrebbe bannato lui.

⭐ **Il mio terreno, tutto separato**: porta **7746** · utente **`provab8`** (uid 1043) · albero
`/media/REMOTIX/src/08-b-src` · lavoro `/media/REMOTIX/tmp/08-b` (ban-file e socket propri) ·
scena `/dev/shm/remotix-08-b`. ⛔ **7730 e 7731 — i due server dell'utente — non sono mai state
toccate**, e si contano prima e dopo ogni passo.

⚠ **Per il coordinatore**: se il piano assegnava 7741 a due agenti, la tabella delle porte della
fase 8 va corretta prima del prossimo giro.

---

## 3 · Che cosa misura, e come si chiude l'anello

**La grandezza è il distacco fra la freccia e la finestra che la insegue**, e non è un ritardo:

```
distacco = velocità della mano × ritardo dell'anello
```

`[R]` La freccia la muove il **browser**, alla velocità della mano (`pagina.html`: il cursore di
sistema *e* la freccia disegnata, tutt'e due locali). La finestra insegue con **tutto** il ritardo.
⇒ Il distacco si apre quando la mano accelera e si richiude quando rallenta.

### L'anello si chiude **due volte**, e le due si guardano in faccia

1. ⭐⭐ **L'ECO NEI PIXEL** — `04-b30-scena.c` dipinge in una seconda marca **le coordinate stesse
   dell'evento che il compositore le ha consegnato**. Il banco legge quella marca **dalla tela
   dipinta** e sa *dove sta la finestra che l'utente vede in questo istante*. È il confine
   **SCOMODO**, ed è **l'unico dei due che sa dare i pixel**: l'eco *è* una posizione.
2. **IL CAMPO `input` DEI 28 BYTE** — `RCP.md` §6.2, che la pagina raccoglie già in `REMOTIX.giro`.
   Il banco avvolge `GIRO.torna`. È il confine **COMODO**: il fotogramma è *arrivato*, non ancora
   decodificato né dipinto.

⭐ **L'accoppiamento è per COORDINATE**, non per tempo: la traiettoria non ripassa mai sullo stesso
pixel, quindi un eco individua **un** evento. ⛔ E quando non lo individua (mano ripassata, evento
mai partito) il campione **si butta e si conta**.

### ⛔ Il prologo è nuovo, e la ragione è una misura

Quello di A10 legge i pixel dal **deposito**. `[R]` Dal 21 agosto la strada del disegno è
`bitmaprenderer` (`DECISIONI.md` §5.4) e **il deposito non esiste più** (`this.deposito = null`).
Un prologo copiato avrebbe letto `null` a ogni fotogramma. ⇒ Qui i pixel si leggono dalla **vista**,
e il confine del disegno è l'avvolgimento di **`transferFromImageBitmap`** — non di
`VideoDecoder.output`, che su questa strada ritorna **prima** che la tela sia cambiata (il
`createImageBitmap` è asincrono) e regalerebbe un fotogramma intero.

### Le TRE unità, e nessuna esce da sola (Q6)

millisecondi (per noi) · **pixel di distacco** (per l'utente) · ⭐⭐ **frazioni della barra del
titolo** (invariante di scala — è l'unità che ha già retto al confronto con xrdp a risoluzione
diversa).

---

## 4 · ⭐⭐ I PRIMI NUMERI — `[M]` 22 agosto 2026

**Palco dichiarato**: server `192.168.0.2:7746`, utente `provab8`, sessione GNOME headless, monitor
virtuale **1560 × 888 @ 60 Hz**, scena `04-b30-scena.c` a schermo intero. Client: Chrome su Xvfb
**sul portatile**, `bitmaprenderer`, formato **BGRX**. Rete **WiFi vera** (`wlo1`) in mezzo.
⛔ Prestazioni **su Intel UHD 730 integrata**, non su una scheda potente.

**Tre giri indipendenti, e concordano entro l'1 %:**

| | giro 1 | giro 2 | giro 3 |
|---|---|---|---|
| campioni | 793 su 829 fotogrammi | 776 | 818 |
| ⏱ **ritardo, confine SCOMODO** (input → **disegno finito**) | **69,8 ms** | **70,2** | **67,1** |
| ⏱ ritardo, confine COMODO (fotogramma *arrivato*, §6.2) | 35,7 | 36,0 | 35,0 |
| ⭐ **quanto si regala il comodo** | **34,1 ms** | 34,2 | 32,1 |
| 📏 **distacco** | **201 px** (p95 497, max 838) | 206 | 194 |
| ⭐ **distacco in barre del titolo** | **0,28** | 0,29 | 0,27 |
| 🌐 rete misurata **nello stesso giro** | 2,7 ms (3,9 %) | 2,8 (3,9 %) | 2,7 (4,1 %) |
| ⭐ **il pezzo NOSTRO** | **67,0 ms** | 67,5 | 64,3 |
| la mano | 3 185 px/s | 3 178 | 3 226 |
| ritmo dei fotogrammi visti | 33,2 ms fra due (≈ **30/s**) | 33,3 | 33,3 |

### ⭐⭐ E il termine di paragone locale, misurato — non supposto

`[M]` `08-b67-locale.py`, **la stessa scena, sulla stessa macchina, senza di noi**, letto dal blocco
condiviso col seqlock verificato:

| tratto | mediana | p95 |
|---|---|---|
| 1. la **scena** (eco ricevuto → dipinto) | 7,29 ms | 16,00 |
| 2. il **compositore** (dipinto → **presentato**, `wp_presentation`) | 20,01 ms | 25,07 |
| 3. ⭐⭐ **L'ANELLO LOCALE** (eco → sullo schermo) | **27,58 ms** | 32,30 |

⇒ 📏 alla mediana dell'utente (3 400 px/s): **94 px**, cioè **0,13 barre del titolo**.
⚠ `n = 29` su 83 chiusi (54 buttati dal setaccio): **è un primo numero con un denominatore
piccolo**, e va rifatto più lungo.

### ⭐⭐ La riga che conta, e sta in una unità sola

| | barre del titolo | ms |
|---|---|---|
| **locale** (lo stesso compositore, senza di noi) | **0,13** | 27,6 |
| **REMOTIX**, banco, monitor 1560 | **0,28** | 69,8 |
| **REMOTIX**, giudizio dell'utente sulla sua sessione | **0,50** | — |

⇒ ⭐ **Siamo a ~2,4 volte il locale, non a dieci.** E la differenza `69,8 − 27,6 = 42 ms` è
**quel che aggiungiamo noi** sopra al compositore: è il pezzo su cui questa fase può lavorare.

⚠ **E lo scarto fra 0,28 (banco) e 0,50 (utente) NON si spiega da qui**, ed è una `[?]` aperta:
il banco gira a **1560 px**, l'utente a **2560** — più pixel da catturare, codificare e spedire per
ogni fotogramma — e la sua sessione ha un desktop vero addosso invece di una scena.

### ⭐ E un fatto che nessuno cercava: **il confine comodo si regala metà del numero**

`[M]` 35,7 ms contro 69,8. ⇒ ⛔ Chi misurasse l'anello col solo campo `input` dei 28 byte —
cioè con `REMOTIX.giro`, che è quel che la pagina mostra all'utente in diagnostica —
**direbbe la metà del vero**. Il numero della pagina è un limite inferiore, ed è dichiarato tale
nel suo commento; ma ora c'è la misura di **quanto** vale quel limite.

---

## 5 · La certificazione: **13 guasti innestati su 13 accusati**

`python3 banchi/08-b67-elastico.py --certifica` — gira sul portatile, senza rete e senza server,
e finisce **0**. Ogni verde è messo alla prova con un guasto che **deve** far diventare rosso il
banco:

| | guasto innestato | preso da |
|---|---|---|
| G1 | l'eco è **fermo** (la finestra non insegue) | Q4 |
| G2 | l'eco è **illeggibile** (rumore nei pixel) | Q0, Q3 |
| G3 | ⛔ **niente da giudicare** (zero marche) | Q0, Q3 → **uscita 3** |
| G4 | la mano è **lenta** (300 px/s invece di 3 400) | Q1 |
| G5 | le due marche sono di **due fotogrammi diversi** | Q2 |
| G6 | le celle in 0-1 invece che 0-255 (il difetto del 13 agosto) | Q13 |
| G7 | ⛔ la **rete non è misurata** in questo giro | Q9 |
| G8 | ritardo **negativo** (fotogramma prima dell'evento) | Q0 |
| G9 | ⛔ il server **trasforma** le coordinate (§7.3 violata) | Q0, Q5 |
| G10 | la traiettoria **ripassa** sugli stessi pixel (accoppiamento ambiguo) | Q0, Q5 |
| G11 | ⭐ un **buco di 300 ms** innestato nel mezzo | il rilevatore dei buchi lo trova |
| G12 | il **costo del banco** non è misurato | Q12 |
| G13 | si consegnano **solo i millisecondi** | Q6 |

### ⭐⭐ E la taratura è **doppia**, ed è il pezzo che vale di più

Si innesta un ritardo **noto** e si pretende che salgano **tutt'e due** le unità:

| innesto | il **tempo** sale di | atteso | il **distacco** sale di | atteso |
|---|---|---|---|---|
| +30 ms | 30,0 ms | 30 | 94 px | 96 |
| +60 ms | 60,0 ms | 60 | 164 px | 192 |

⛔ **Perché conta**: se il banco ricavasse il distacco dividendo il ritardo per una costante, questa
prova passerebbe **per costruzione**. Qui il distacco viene dai **pixel** (l'eco) e il ritardo dai
**tempi**: le due si muovono insieme nel rapporto della velocità **solo se tutt'e due sono vere**.

### ⭐ Il controllo positivo, e ha corretto **me**

Su una traccia in cui la finestra insegue la mano **senza nessun ritardo** il banco trova
**0 px** e **4,0 ms**. ⛔ La prima stesura di Q11 pretendeva 0,0 ms e **si accusava da sola**:
i 4 ms sono **la grana della mano** (un evento ogni 8 ms, i fotogrammi cadono in mezzo ⇒ mezzo
passo), e nemmeno un anello perfetto potrebbe scendere sotto. ⇒ La soglia è **un passo della mano**,
ed è scritta col perché.

⛔ **Il controllo negativo**: 3 000 sonde di rumore attraverso il lettore certificato → **0 falsi su
3 000**.

---

## 6 · ⛔ Che cosa NON ha funzionato — quattro rossi, tutti del banco

⭐ **Nessuno dei quattro era del prodotto**, e tutti e quattro sono stati trovati dal banco stesso.

1. ⛔⛔ **`[M]` 0 eco su 826 — e la causa era la PANORAMICA di GNOME.**
   Quando la sessione si apre senza finestre, GNOME mostra «Activities» e la scena ci compare dentro
   come **miniatura ridotta e spostata**: la marca c'è nei pixel ma non è né a (0,0) né in scala
   1:1, e ogni CRC salta. ⭐ **L'ho vista solo fotografando la tela** — un contrasto di 0,65 con
   sync 0x00 non lo dice. ⇒ Cura: il banco **batte `Escape` sul desktop remoto** e riprova, fino a
   tre volte; e il verde arriva solo quando la marca si legge con `scorrimento [0,0]` e
   `contrasto 1,0`.
   ⚠ **E prima ancora avevo saltato il passo dello SCORRIMENTO**, che `04-b30` documenta come
   costato *«0 marche su 966»*. Ho ripreso lo stesso rosso pari pari credendolo un dettaglio di
   A10: **la lezione di un altro banco vale solo se la si esegue.**

2. ⛔ **`[M]` un picco di 531 079 px/s** — cioè una mano che non è di nessuno.
   Il pilota consegnava **tutti** i punti scaduti nello stesso giro: quando il filo principale era
   occupato a decodificare restava indietro e poi sparava cinque movimenti nello stesso
   millisecondo. ⇒ Cura: **un solo movimento per giro**, i vecchi si saltano e **si contano** —
   che è quel che fa un mouse vero quando il browser fonde gli eventi.

3. ⛔ **`[M]` 450 000 px/s e poi 26 132 px/s** — due gradini nella traiettoria.
   La serpentina **ripartiva dall'alto** arrivata in fondo (un teletrasporto), e poi **scendeva a
   scalini** di una riga intera al rimbalzo (245 px in 8 ms su uno schermo largo). ⇒ Cura: si
   rimbalza sfasando di mezza riga, e **la discesa è continua** (una diagonale). `[M]` Verificato:
   0 punti ripetuti su 3 125, mediana 3 500 px/s, p90 7 250, picco 13 500.

4. ⛔ **`[M]` l'anello locale diceva 11,71 ms mentre le sue due parti facevano 7,29 + 20,01 = 27,3**
   — cioè un totale **più piccolo delle sue parti**, che è impossibile.
   Il setaccio («un disegno non può precedere l'evento che lo causa») era applicato **solo al primo
   tratto**: tre denominatori diversi sotto la stessa tabella. ⇒ Cura: un setaccio solo, applicato
   una volta, e i buttati si contano (54 su 83). Il numero vero è **27,58 ms**.

⚠ **E una cosa che non ho fatto**: il costo della lettura dei pixel è `[M]` **7,6 ms mediani per
fotogramma** (Q12), sul **filo principale**, cioè lo stesso che decodifica e dipinge. L'ho dimezzato
(una sola riconsegna dalla GPU invece di due) **ma non tolto**: è un errore sistematico dentro ogni
numero di questo banco, e sta dichiarato invece che sperato piccolo.

---

## 7 · Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **lo scarto 0,28 contro 0,50** | il banco misura **meno** elastico di quel che l'utente riferisce. Candidati: la **risoluzione** (1560 contro 2560 — più pixel per fotogramma), il **desktop vero** contro una scena sola, e la velocità a cui lui guarda. ⛔ Non è deducibile: si rifà il giro a 2560 |
| ⏳ **i sei buchi** | `[M]` **0 buchi in 24,9 s** su tre giri, contro i **6 in 17,5 s** dell'utente. ⛔ Il rilevatore FUNZIONA (G11 lo prova su un buco innestato), quindi *su questa scena e su questa rete i buchi non ci sono*. ⇒ Sono della sua scena, della sua risoluzione, o del suo momento di WiFi — e restano `[?]` |
| ⏳ **la mano è SINTETICA** | i `PointerEvent` nascono dentro la pagina: ⛔ il pezzo cieco in ingresso **non c'è affatto**, e per questo non si somma. ⚠ E gli eventi non vengono **fusi** dal browser come quelli veri. La strada `--mano cdp` (eventi *fidati*, consegnati da Chrome) è prevista e **non è ancora stata girata** |
| ⏳ **l'anello locale ha n = 29** | il numero c'è, il denominatore è piccolo: va rifatto su un giro lungo |
| ⏳ **il ritmo è 30/s, non 60** | `[M]` 33,3 ms fra due fotogrammi visti, con una scena che ne disegna 61/s. ⇒ **metà si perdono per strada**, e questo banco lo *vede* ma non lo *spiega* |
| ⏳ **la taratura sul FERRO** | Q7/Q8 girano sul sintetico. Il ponte di A10 (`04-b30-ponte.py`) sa innestare un ritardo noto sul filo vero, e il terreno lo prevede: **non è stato girato** |
| `[?]` **il codificatore e la sua scheda** | il banco **non** verifica che la codifica sia in hardware. `provab8` è nel gruppo `render` (verificato), ma «ha aperto un render node» non prova niente (`LEZIONI.md` §1.11) |
| ⏳⏳ **69,8 contro i 99,07 ms dell'agente A** | ⛔ **I due numeri vanno riconciliati prima che uno dei due entri in un documento come «l'anello».** Non si sommano e non si sottraggono finché non è scritto, per ciascuno, *quale confine* e *quale scena*: il mio chiude al **disegno finito** su una scena di prova a **1560 px**, e la sua mano è **sintetica**. ⚠ Finché la riconciliazione non c'è, il mio numero vale come **misura dell'elastico su questa scena**, non come «l'anello di REMOTIX» |

---

## 8 · Come si rigira

```bash
bash banchi/08-b67-lancia.sh certifica          # qui, senza server: 13 guasti su 13
bash banchi/08-b67-lancia.sh porta costruisci   # albero e contenitore
bash banchi/08-b67-lancia.sh scena-costruisci
bash banchi/08-b67-lancia.sh terreno accendi
bash banchi/08-b67-lancia.sh aggancia           # il monitor virtuale nasce col figlio
bash banchi/08-b67-lancia.sh scena-avvia
bash banchi/08-b67-lancia.sh misura 25
```

⚠ **Il server sulla 7746 e la scena sono rimasti ACCESI**, così il coordinatore può rigirare senza
rimontare il terreno. Si spengono con `bash banchi/08-b67-lancia.sh spegni` — ⛔ che tocca **solo**
le mie cose.


---

## 4-D · ⭐⭐ AGENTE D — `EncSliceLP` e il peso delle chiavi · **rientrato il 22 agosto 2026**

*Due `[?]` che stavano nei documenti da settimane, chiuse tutte e due con la misura. ⛔ E due
difetti veri trovati in `codificatore.c`, girati al suo proprietario invece che curati di nascosto.*

*Misurato il 22 agosto 2026 sulla macchina di prova (`192.168.0.2`), dentro il contenitore
(`enter.sh`). Ferro: **Intel UHD 730 integrata** — `/dev/dri/renderD128`, driver **iHD 25.2.3**,
VA-API 1.22 — e, come solo controllo, la **Radeon RX 6800** su `renderD129` (Mesa 25.0.7,
radeonsi navi21). ffmpeg 7.1.5, libavcodec 61.19.101.
⛔ Nessuno dei due server dell'utente (7730, 7731) è stato toccato: questi banchi non aprono
nessuna porta, sono codifiche fuori linea.*

---

## D.1 · ⛔ `EncSliceLP` **NON** sa produrre i sotto-livelli temporali

⭐ **La risposta è NO, ed è misurata a tre porte diverse — che si chiudono tutte.**

`RCP.md` §5.2 diceva: *«se `EncSliceLP` dell'Intel li sappia produrre non lo sa nessuno, ed è una
misura della fase 8»*. Adesso lo si sa.

### D.1.1 La prima porta: il driver **non li dichiara** — e i due controlli positivi lo inchiodano

`[M]` `vaGetConfigAttributes` su `renderD128`, attributo `VAConfigAttribEncRateControlExt` (è quello
che porta `max_num_temporal_layers_minus1`), banco `banchi/08-D1-attributi-va.c`:

| profilo, entrypoint | nodo | `EncRateControlExt` | sotto-livelli |
|---|---|---|---|
| H264 ConstrainedBaseline · Main · High, **`EncSliceLP`** | Intel | ⛔ **NON SUPPORTATO** | — |
| HEVC Main · Main10 · Main444 · Main444_10, **`EncSliceLP`** | Intel | ⛔ **NON SUPPORTATO** | — |
| ⭐ **VP9** Profile0/1/2/3, **`EncSliceLP`** | Intel | `0x00000107` | **8** |
| ⭐ H264 ×3 e HEVC Main/Main10, `EncSlice` | AMD | `0x00000103` | **4** |

⛔ **7 profili su 7** dicono no sul percorso che ci riguarda. ⭐ **E i due controlli positivi sono
la parte che vale**:

- **stesso nodo, stesso driver, stesso entrypoint `EncSliceLP`**: su VP9 i sotto-livelli ci sono, e
  sono otto ⇒ il «no» **non è del percorso a bassa potenza in quanto tale**, ed è del binomio
  (codec, entrypoint);
- **stessa libva, stesso banco, altro nodo**: su AMD `EncSlice` ci sono per H.264 *e* per HEVC ⇒ il
  «no» **non è del codec in astratto**, e **non è della mia sonda**.

⚠ Questa è la porta che si legge nel driver, e da sola non basterebbe: il mandato chiedeva una
misura, non la documentazione. Le altre due sono nei byte.

### D.1.2 La seconda porta: **nei byte che escono non c'è nessun sotto-livello**

`[M]` `banchi/08-D1-struttura.py` e `08-D1-costo.py`. Sei configurazioni su `EncSliceLP`
(`-bf` 0, 1, 2/d1, 2/d2, 4/d1, 4/d3), 120 fotogrammi della **scena vera dell'utente** ciascuna,
QP 26 come il prodotto. Si legge `nuh_temporal_id_plus1` in **ogni** intestazione NAL e
`sps_max_sub_layers_minus1` nell'SPS:

⇒ ⛔ **6 celle su 6: `sps_max_sub_layers = 1`, e il 100 % dei NAL VCL porta `temporal_id = 0`.**
E la stessa cosa sul controllo AMD `EncSlice` (1 cella su 1): **ffmpeg non li produce nemmeno dove
l'hardware li dichiara**, perché nell'elenco completo delle opzioni di `hevc_vaapi` e `h264_vaapi`
**non esiste nessuna opzione per chiederli** `[R]` (c'è `b_depth`, e basta).

⇒ ⛔ **Le porte chiuse sono due e indipendenti**: il chip non li dichiara, e la nostra unica strada
verso il chip non saprebbe chiederli comunque.

### D.1.3 ⭐⭐ La terza porta: **prova a smentirti** — il lettore, e il guasto innestato

⛔ *«Non ho visto sotto-livelli»* può voler dire *«il mio lettore è rotto»*. Due testimoni,
`banchi/08-D1-testimone.py`:

| testimone | `[M]` |
|---|---|
| **`libx265` con `temporal-layers=2:bframes=8`**, 48 fotogrammi | `temporal_id` **{0: 25, 1: 23}**, `sps_max_sub_layers = **2**` ⇒ ⭐ **il lettore li vede quando ci sono** |
| **i bit alzati a mano** su un nostro flusso (59 intestazioni portate a `nuh_temporal_id_plus1 = 2`) | il lettore ne conta **59 su 59**, esatte |

⭐ **E `LEZIONI.md` §1.8 si è presentata da sola, dalla parte buona**: chiesto
`temporal-layers=**1**`, x265 **rifiuta a voce alta** — *«No support for temporal sublayers less
than 2; Disabling temporal layers»* — e produce `temporal_id` tutti a zero. ⇒ Al primo giro il mio
controllo positivo **è fallito**, e per un giro la misura è rimasta senza testimone (§«che cosa non
ha funzionato», punto 4). Un banco che avesse guardato solo il codice di uscita avrebbe scritto
«x265 non li fa» ed è **falso**.

⇒ ⛔ **Lo zero su `EncSliceLP` è del codificatore, non del banco.**

### D.1.4 ⭐ Però una **parte** di quel che i sotto-livelli servivano a fare si ottiene già oggi

I sotto-livelli servivano a *«buttare certi fotogrammi senza rompere niente»*. **Quel risultato lì
`EncSliceLP` lo dà**, per un'altra strada: le **figure non di riferimento** — in HEVC i NAL di tipo
`TRAIL_N` — che compaiono appena si chiede `-bf ≥ 1` (nel prodotto è `c->ctx->max_b_frames`,
`codificatore.c:1377`, oggi **0**).

`[M]` `banchi/08-D1-costo.py`, sorgente **grezza NV12 a cadenza fissa**, 120 fotogrammi
2560×1080 della scena dell'utente, `hevc_vaapi` `EncSliceLP` QP 26 (`entrypoint` **confessato da
libavcodec**, non dedotto):

| cella | byte (120 fot.) | buttabili | **ritardo di riordino** | PSNR | SSIM | buttandole |
|---|---|---|---|---|---|---|
| `-bf 0` — **il prodotto oggi** | 89 457 | **0**/120 | **0 ms** | 52,973 | 0,998174 | — |
| `-bf 1` | 75 119 | 59/120 | **67 ms (2 fot.)** | 52,908 | 0,998155 | PULITA, −12 % byte |
| `-bf 2 -b_depth 1` | 66 445 | 79/120 | 100 ms (3 fot.) | 52,852 | 0,998135 | PULITA, −21 % |
| `-bf 2 -b_depth 2` | 66 683 | 39/120 | 133 ms (4 fot.) | 52,853 | 0,998135 | PULITA, −10 % |
| `-bf 4 -b_depth 1` | 66 255 | 95/120 | 167 ms (5 fot.) | 52,796 | 0,998110 | PULITA, −36 % |
| `-bf 4 -b_depth 3` | 62 055 | 23/120 | 234 ms (7 fot.) | 52,797 | 0,998109 | PULITA, −7 % |

**Come si chiedono**: `-bf N` (in C: `ctx->max_b_frames = N`), niente altro. `-b_depth` sposta
**quante** figure sono buttabili, non **se** lo sono.

**Che cosa costano in qualità**: `[M]` **niente di misurabile** — da `-bf 0` a `-bf 1` il PSNR
scende di **0,065 dB** e lo SSIM di **0,00002**.
**Che cosa costano in banda**: `[M]` **la fanno risparmiare**: −16 % a `-bf 1`, fino a −31 %.
⛔ **Che cosa costano davvero**: **il riordino**. Già `-bf 1` mette **due fotogrammi** fra la
cattura e l'uscita — `[M]` **67 ms** a 30/s — cioè **da solo sfonda i 50 ms** che `DECISIONI.md`
§2.4 dà a **tutto** il pezzo nostro.

⇒ ⛔ **Su questo ferro non esiste un modo a ritardo zero di avere fotogrammi buttabili.**
⇒ ⭐ **La riga di `RCP.md` §5.2 — «ogni abbandono costa una chiave» — resta in vigore, e adesso ha
una misura sotto invece di una `[?]`.**

⚠ *E il prodotto è già protetto se qualcuno provasse a toccare quel numero*: `codificatore.c:2182`
guarda `dts ≠ pts` e **scrive nel registro** che il codificatore riordina. La riga
`max_b_frames = 0` è giusta com'è: ⛔ **non si tocca.**

### D.1.5 ⭐⭐ E il verde più importante di D.1 è stato **smentito su richiesta**

⛔ *«Il flusso tagliato decodifica senza errori»* **non prova niente**, e §5.2 lo dice testualmente:
a un delta mancante il decodificatore **non solleva nessun errore**. ⇒ La prova sono i **pixel**.
`banchi/08-D1-smentita.py`, flusso `-bf 1`, 120 fotogrammi, impronta SHA-256 di **ogni** immagine
decodificata, confrontata con le immagini del flusso **intero**:

| | figure tolte | immagini | errori del decodificatore | **identiche al flusso intero** |
|---|---|---|---|---|
| **il verde**: buttate tutte le `TRAIL_N` | 59 | 61 | nessuno | ⭐ **61/61 — 100,0 %** |
| ⭐ **guasto innestato**: buttata **1 `TRAIL_R` su 10** | 6 | 114 | *«Could not find ref with POC 20»* | ⛔ **19/114 — 16,7 %** |
| ⭐ **guasto pesante**: buttate **tutte** le `TRAIL_R` | 60 | 60 | *«Could not find ref with POC 2»* | ⛔ **1/60 — 1,7 %** |

⇒ Il verde **diventa rosso** quando si butta la cosa sbagliata, e di quanto: **100 % → 16,7 %**
togliendo **sei** figure su 120. Il banco distingue.

---

## D.2 · Quanto pesa una chiave, contro il tetto dei 16 MiB

**Il tetto è 16 777 216 byte** (`RCP.md` §6.2). Metodo: **ogni** fotogramma è una chiave (`-g 1`,
`idr_interval 0`), e si misura l'**accesso intero** — VPS+SPS+PPS+SEI+IDR — cioè quel che il
protocollo mette in un chunk `key`, non il solo slice. Regime del prodotto: `EncSliceLP`,
`rc_mode=CQP`, **QP 26** (`figlio.c:3978`); ripiego in software **CRF 20** (`figlio.c:4065`).

⛔ **I 10 bit qui sono OTTO PROMOSSI, e si dichiara**: `DECISIONI.md` §2.3-ter ha misurato che dalla
cattura di Mutter i 10 bit veri non escono per nessuna strada. Le righe `main10` qui sotto misurano
l'**etichetta**, non il contenuto — e infatti `[M]` a 8K costano **meno** di `main` (250 355 contro
251 288 byte): la profondità dichiarata non porta informazione che non ci sia.

### D.2.1 ⭐ Alla tela dell'utente il tetto **non si può sfondare**

`[M]` `banchi/08-D2-misure.py`, il video vero girato dall'utente il 22 agosto (2560×1080, 404
fotogrammi), **ogni fotogramma una chiave**:

| | n | min | **mediana** | p90 | **massimo** | quota del tetto |
|---|---|---|---|---|---|---|
| `hevc_vaapi` `EncSliceLP` QP 26 | **404** | 20 328 | **20 817** | 21 070 | **21 433 byte** | **0,13 %** |
| `h264_vaapi` `EncSliceLP` QP 26 | **404** | 24 160 | **24 956** | 25 282 | **25 621 byte** | **0,15 %** |

⇒ ⭐ **Il margine è 782×.** E il tetto lì non si raggiunge **nemmeno di proposito**
(`banchi/08-D2-scala.py`, n=8 per riga, sorgente grezza, codificatore isolato):

| scena, 2560×1080 | massimo | quota |
|---|---|---|
| il desktop vero | 20 259 byte | 0,1 % |
| il desktop + **grana forte** (`noise=alls=30`) | 758 513 byte | 4,5 % |
| ⛔ **rumore uniforme** — il caso peggiore che esista | **2 529 464 byte (2,412 MiB)** | **15,1 %** |
| ripiego `libx265` CRF 20 sul rumore | 3 065 178 byte | 18,3 % |
| ripiego `libx264` CRF 20 sul rumore | 2 812 378 byte | 16,8 % |

⇒ ⛔⭐ **Alla tela di 2560×1080 il difetto di forma di §6.2 è irraggiungibile**: perfino il rumore
puro sta **6,6 volte** sotto.

### D.2.2 ⛔ A 7680×4320 il tetto **si sfonda davvero**

La scena 8K non si inventa e non si ingrandisce: ⛔ **ingrandire cancella il dettaglio e
sottostima**. Si prende il desktop vero e lo si **affianca 3×4** — dodici immagini diverse — così la
densità di dettaglio per pixel resta quella vera. `[M]` `banchi/08-D2-misure.py` e `08-D2-scala.py`,
`hevc_vaapi` `EncSliceLP` QP 26:

| scena, 7680×4320 | n | massimo | quota del tetto |
|---|---|---|---|
| ⚠ *il desktop **ingrandito** invece che affiancato — il caso comodo* | 6 | *76 520 byte* | *0,5 %* |
| **il desktop affiancato** (dettaglio nativo) | 33 (27 distinte) | **251 288 byte (0,240 MiB)** | **1,5 %** |
| lo stesso, etichetta `main10` (8 bit promossi) | 33 | 250 355 byte | 1,5 % |
| il desktop + grana `alls=10` | 8 | 660 939 byte | 3,9 % |
| il desktop + grana `alls=30` | 8 | 9 136 749 byte (8,713 MiB) | **54,5 %** |
| il desktop + grana `alls=60` | 8 | 15 926 065 byte (15,188 MiB) | ⚠ **94,9 %** |
| ⛔ **rumore uniforme** | 8 | **30 319 727 byte (28,915 MiB)** | ⛔ **180,7 % — sfonda 8/8** |

⚠ **E l'ingrandimento sottostima di 3,3 volte**: è la ragione per cui il mosaico esiste.

⇒ ⛔ **Risposta alla `[?]` di `RCP.md` §6.2: sì, il tetto si sfonda**, alla misura massima che §4.5
dichiara legale, con contenuto quasi incomprimibile. **Ma con un desktop vero, no** — nemmeno a 8K,
dove sta al **1,5 %**.

### D.2.3 ⛔⛔ E il ripiego in software sfonda **prima**, con contenuto **plausibile**

⛔ **`h264_vaapi` su questo chip si ferma a 4096 px per lato** — `[M]` *«Hardware does not support
encoding at size 4112x2160 (constraints: width 32-4096 height 32-4096)»*, mentre 4096×2160 passa
(41 566 byte, n=10). ⇒ **Oltre i 4096 px l'H.264 in hardware NON C'È**, e la tela legale arriva a
7680: là si scende su `libx264`. `[M]` `hevc_vaapi` invece regge 7680×4320, 8192×4320 e perfino
16384×4320 (6 chiavi su 6 ciascuno).

`[M]` `banchi/08-D2-ripiego.py`, `libx264` **CRF 20**, 7680×4320, n=8:

| scena | mediana | massimo | sopra il tetto |
|---|---|---|---|
| il desktop affiancato | 331 979 | 398 054 byte (0,380 MiB) | 0/8 |
| + grana `alls=30` | 9 182 880 | **19 642 719 byte (18,733 MiB)** | ⛔ **1/8** |
| + grana `alls=60` | 11 653 811 | **23 820 270 byte (22,717 MiB)** | ⛔ **1/8** |
| rumore uniforme | 18 729 154 | 33 710 537 byte (32,149 MiB) | ⛔ 8/8 |

⇒ ⛔ **Un filmato molto granuloso a schermo intero su una tela 8K è già oltre il tetto**, e non è
rumore di laboratorio.

### D.2.4 ⛔⛔ E qui c'è il difetto vero: **la scala delle ricodifiche è corta di UNO scalino**

`[R]` `codificatore.c:41` `RICODIFICHE_MASSIME 3`, `:46` `CRF_PASSO 6`, `:2061` `abbassa_qualita()`.
La scala è dunque **QP 26 → 32 → 38** (hardware) e **CRF 20 → 26 → 32** (software), e dopo il terzo
tentativo `:2203` **restituisce `false`: il fotogramma NON parte.**

`[M]` sul caso che sfonda, 7680×4320, n=8 per riga:

| tentativo | hardware `hevc_vaapi` LP | esito | software `libx264` | esito |
|---|---|---|---|---|
| 0 | QP 26 → 28,915 MiB | ⛔ sopra 8/8 | CRF 20 → 32,149 MiB | ⛔ sopra 8/8 |
| 1 | QP 32 → 22,442 MiB | ⛔ sopra 8/8 | CRF 26 → 25,602 MiB | ⛔ sopra 1/8 |
| 2 | QP 38 → **16,654 MiB** | ⛔ **sopra 8/8** | CRF 32 → **19,895 MiB** | ⛔ **sopra 1/8** |
| **3 — che non c'è** | *QP 44 → 11,056 MiB* | *0/8, ce l'avrebbe fatta* | *CRF 38 → 14,280 MiB* | *0/8, ce l'avrebbe fatta* |

⇒ ⛔⛔ **Manca uno scalino solo**, su tutt'e due i percorsi, e il tentativo che manca è quello che
sarebbe bastato. **QP 38 sta al 104,1 % del tetto**: si perde per il **4 %**.

⛔ **E la conseguenza è quella che `RCP.md` §5.2 esiste per non avere.** Se il fotogramma che «non
parte» è una **chiave**, §5.2 dice *«il server NON DEVE abbandonare un fotogramma chiave»*: il
client resta rotto, manda `RICHIEDI_CHIAVE`, e ogni richiesta fa rifare **tre** ricodifiche che non
producono niente. `[M]` **Ogni tentativo a 8K costa 91-108 ms in hardware e 1,8-3,3 s in
software** ⇒ **~300 ms** ovvero **~7,8 s** buttati per fotogramma, a ripetizione. **È la spirale.**

⚠ **Quanto è raggiungibile**: serve una tela vicina agli 8K **e** contenuto quasi incomprimibile.
Alla tela dell'utente, mai (§D.2.1). ⇒ È un difetto **vero e dimostrato**, non **urgente**.

---

## ⛔ Che cosa NON ha funzionato — e sette cose sbagliate le ho fatte io

1. ⛔⛔ **Il denominatore era finto, e me ne sono accorto perché era troppo bello.** Le prime 33
   chiavi a 8K uscivano **tutte di 243 497 byte esatti**: impossibile su 33 immagini diverse. Causa:
   `-fps_mode cfr -r 30` sta **dopo** il filtro `tile=3x4`, che consegna 2,5 immagini al secondo ⇒
   la conversione di cadenza le **duplicava dodici volte**. Le immagini distinte erano **tre**, non
   trentatré. ⇒ Rifatto senza conversione: **27 distinte su 33**, e le misure vanno da 243 496 a
   251 288. ⭐ *La regola che ha salvato il numero: un massimo uguale alla mediana è un allarme, non
   un bel risultato.*
2. ⛔ **La prima misura di qualità era priva di senso** — PSNR **16,47 dB** in tutte le celle, e
   identico a cinque decimali. Non era una qualità: era un **disallineamento**, perché confrontavo
   una codifica a cadenza fissa con la sorgente **a cadenza variabile** del video dell'utente. Rifatto
   da una sorgente **grezza NV12 già a cadenza fissa**: **52,9 dB**.
3. ⛔ **`-max_frame_size` non è una via d'uscita**: `[M]` `hevc_vaapi` lo **rifiuta** in CQP, 3
   tentativi su 3 — *«Max frame size is invalid in CQP rate control mode»*. Era il candidato più
   comodo per il tetto e non esiste.
4. ⛔ **Il mio primo controllo positivo è fallito**: `libx265` con `temporal-layers=**1**` non
   produce sotto-livelli e **lo dichiara** (*«No support for temporal sublayers less than 2»*).
   Per un giro la misura di D.1 è rimasta senza testimone. Con `=2` funziona.
5. ⛔⛔ **`-low_power 0` sull'Intel apre lo stesso `VAEntrypointEncSliceLP`** `[M]`, e ffmpeg **non
   fallisce**: prende quel che c'è. ⇒ Chiunque misuri «LP contro entrypoint pieno» su questo chip
   passando da ffmpeg produce **due misure sotto la stessa etichetta**, che è `LEZIONI.md` §1.8 in
   piena regola. ⚠ **Riga da consegnare alla fase 9**, che quella domanda ce l'ha in carico: sul
   ferro di casa il confronto **non si può fare**, perché l'entrypoint pieno non c'è — si fa
   sull'AMD, e allora cambiano insieme chip e driver.
6. ⛔ Le opzioni di colore passate come opzioni **di uscita** su un ingresso grezzo fanno inserire a
   ffmpeg un `auto_scale` che la catena VA-API rifiuta (*«Impossible to convert between the formats
   supported by the filter Parsed_hwupload»*). Un giro perso; nei banchi definitivi il colore si
   dichiara alla sorgente o non si dichiara, e **le misure di D.2 non ne dipendono**.
7. ⚠ **La scena 8K non è un desktop 8K vero**, ed è dichiarato: è il desktop 2560×1080 dell'utente
   affiancato 3×4. Nessuno ha un desktop 8K da fotografare.

---

## `[?]` Che cosa resta aperto

1. `[?]` ⭐ **Un programma che facesse la codifica VA-API da sé — senza ffmpeg — potrebbe
   costruire i sotto-livelli su `EncSliceLP`?** Non è escluso, e l'indizio è misurato:
   `[M]` `VAConfigAttribEncPackedHeaders = 0x1f` su `EncSliceLP` vuol dire che **è l'applicazione a
   impacchettare VPS/SPS/PPS e le intestazioni di slice** ⇒ `nuh_temporal_id_plus1` **lo scrive il
   software, non il chip**; e `EncMaxRefFrames` dà **L0 = 3** riferimenti, cioè lo spazio per una
   piramide di **P** (che **non riordina**, quindi **non costa ritardo**). ⛔ Nessuno l'ha provato.
   Chiuderla vuol dire scrivere un codificatore VA-API nostro: giorni di lavoro, e la decisione è di
   chi possiede `codificatore.c`. ⚠ Finché è aperta, `RCP.md` §5.2 **non cambia**.
2. `[?]` **I 10 bit veri** restano non misurabili da qui: `DECISIONI.md` §2.3-ter, Mutter dà BGRx.
   Tutto quel che qui porta l'etichetta `main10` è **otto bit promossi**, e alle 8K costa `[M]`
   **933 byte in meno** di `main` — cioè l'etichetta non porta informazione.
3. `[?]` **Se un desktop 8K vero somigli al mosaico o alla grana.** Il mosaico è un surrogato
   dichiarato.
4. `[?]` **Il regime senza perdita** (`CODIFICATORE_QUALITA_LOSSLESS`) non è nel percorso di
   `figlio.c` e non l'ho misurato; a 8K un fotogramma senza perdita a 8 bit vale **47 MiB** di soli
   pixel grezzi, quindi sfonderebbe per costruzione. Se un giorno si accende, va misurato.

---

## ⚠ Da girare al proprietario di `src/codificatore.c` — io **non l'ho toccato**

| # | dove | che cosa, e perché |
|---|---|---|
| **1** | `codificatore.c:41` `#define RICODIFICHE_MASSIME 3` **oppure** `:46` `#define CRF_PASSO 6` | ⛔ **La scala è corta di uno scalino**, misurato su tutt'e due i percorsi (§D.2.4): l'ultimo tentativo lascia **16,654 MiB** in hardware e **19,895 MiB** in software, e il quarto ce l'avrebbe fatta. ⭐ **Meglio alzare il PASSO che il numero di tentativi**: `[M]` ogni tentativo a 8K costa **91-108 ms** in hardware e **1,8-3,3 s** in software, quindi un passo da **9** costa un terzo di un tentativo in più. ⚠ Il numero esatto è un punto di lavoro fra qualità e banda ⇒ **è della fase 9**: io porto solo la prova che **3×6 non basta** |
| **2** | `codificatore.c:2203-2207` — la resa | ⛔⛔ Quando si arrende restituisce `false` **anche per una CHIAVE**, e `RCP.md` §5.2 vieta di abbandonare le chiavi. ⇒ Per una chiave non ci si può arrendere: si continua a scendere finché entra — `[M]` **QP 51 dà 1,771 MiB a 8K**, quindi entra **sempre** — e si scrive nel registro che l'immagine è uscita brutta. Abbandonarla lascia il client rotto **per sempre**, e ogni `RICHIEDI_CHIAVE` che segue costa tre ricodifiche **che non producono niente**: è la spirale di §5.2 |
| **3** | `codificatore.c:1377` `c->ctx->max_b_frames = 0` | ⛔ **Non si tocca, e adesso c'è il numero accanto**: metterlo a 1 darebbe `[M]` 59 figure buttabili su 120 e −16 % di banda a qualità invariata, **ma 67 ms di riordino** — da solo oltre i 50 ms di `DECISIONI.md` §2.4. ⭐ Il commento «deciso, non ereditato» merita la misura sotto |
| **4** | *nessuna riga: è una cosa che non esiste* | ⚠ `-max_frame_size` **non** è utilizzabile come tetto: `[M]` `hevc_vaapi` lo rifiuta in CQP, 3/3. Se qualcuno ci pensasse, è già misurato che non c'è |
| **5** | ⚠ **fuori da `codificatore.c`** — riguarda `figlio.c` / la trattativa della tela | `[M]` `h264_vaapi` su `EncSliceLP` accetta **32-4096 px per lato**: **4096×2160 sì, 4112×2160 no**. La tela legale di `RCP.md` §4.5 arriva a **7680×4320** ⇒ oltre i 4096 il ripiego `libx264` non è un'eventualità, è **la regola**, e a 8K costa `[M]` **309 ms** per chiave sul desktop e **1,2-3,3 s** sul granuloso. `hevc_vaapi` invece regge fino a 16384×4320 `[M]`. ⇒ Vale la pena leggerlo dal driver invece di scoprirlo al primo fotogramma |

---

## I banchi

Copiati nel worktree, ⚠ **con il prefisso `08-D` per non pestare i nomi degli altri agenti** — il
coordinatore li rinumeri come vuole:

| banco | che cosa risponde |
|---|---|
| `banchi/08-D1-attributi-va.c` | che cosa dichiara il driver su ogni (profilo, entrypoint) dei due nodi |
| `banchi/08-D1-struttura.py` | `temporal_id` e `sps_max_sub_layers` nei byte che escono |
| `banchi/08-D1-costo.py` | banda, PSNR/SSIM, riordino e figure buttabili per ogni `-bf` |
| `banchi/08-D1-smentita.py` | ⭐ la prova a pixel + i due guasti innestati |
| `banchi/08-D1-testimone.py` | ⭐ i due controlli positivi del lettore di `temporal_id` |
| `banchi/08-D2-misure.py` | le chiavi in byte, con il denominatore vero |
| `banchi/08-D2-scala.py` | dal desktop vero al rumore, codificatore isolato |
| `banchi/08-D2-ripiego.py` | lo stesso in software, e la scala delle ricodifiche |

Si girano sulla macchina di prova dentro il contenitore, da `/srv/src/08-D`, dove sta anche la
scena (`scena-utente.webm`, il video del 22 agosto).


---

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
| ✅ ~~**il puntatore doppio**~~ | **SMENTITO dall'utente il 22 agosto 2026**: *«non ci sono doppi puntatori»*. 📖 §7.3 |

### 7.1 ⭐ Le due strade già provate — non si rifanno

- `createImageBitmap`: **3,8 ms** mediani per fotogramma, l'8 % del tetto di 50, e già **nove volte
  meglio** del disegno 2D di prima;
- ⛔ **`?video=worker` funziona e NON rende**: abbassa il tetto del **19 %**. Chi apre questa fase
  non la rifaccia.

### 7.3 · ⛔⭐ **Il «puntatore doppio» non esiste** — e a smentirlo è stato l'occhio dell'utente

*22 agosto 2026. Il punto era stato aperto e un agente ci stava già lavorando: **fermato dopo pochi
minuti**, su una frase sola.*

⛔ **Il codice lo dichiara come un difetto vivo.** `src/pagina.html`, nel commento del 14 agosto:
*«Il cursore del browser resta VISIBILE, e la freccia la disegniamo lo stesso. ⚠ Se ne vedono **due
sovrapposti** — brutto, e §7.1 lo chiama un difetto»*. Ed è la ragione per cui esiste l'interruttore
`data-puntatore` a tre condizioni, con `due` come valore per difetto **chiamato «il DIFETTO» dal
codice stesso**.

⭐⭐ **E l'utente, guardando lo schermo vero, dice che non c'è**, due volte e la seconda più netta:
*«non ci sono doppi puntatori»* e poi **«io vedo solo un puntatore»** — dopo aver già confermato,
poche ore prima, che *«sì, la freccia si vede»*. ⇒ **Uno, e si vede.**

⇒ ⛔ **Il difetto è dichiarato dal codice e non si manifesta.** È la forma di `LEZIONI.md` §1.20
rovesciata: lì il giudizio era staccato dalla misura, qui **un commento è staccato dal prodotto** —
e ha resistito otto giorni perché nessuno aveva chiesto all'unico arbitro che poteva vederlo.

⚠ **Che cosa NON si conclude da qui**, e va scritto o la prossima lettura sbaglia: *«ne vedo uno»*
non dice **quale**. Restano due mondi possibili — le due frecce **coincidono** esattamente (quindi
sono indistinguibili e il difetto è cosmetico e nullo), **oppure la seconda non viene disegnata
affatto** (e allora sul DeX potrebbe mancare proprio quella che serve). `[?]` La distinzione costa
poco e **non è stata fatta**: l'utente ha chiuso il punto, e un punto chiuso dall'arbitro non si
riapre per curiosità.

⚠ **E l'una vale l'altra per il prodotto sul desktop**, che è quel che l'utente giudica. ⛔ Non
sarebbe più vero sul **DeX**, dove la freccia disegnata esiste per una ragione misurata — a 1,1
fotogrammi al secondo il desktop sembra morto se non la disegna il client. ⇒ Chi un giorno tocca il
DeX **riapra la domanda lì**, non qui.

⇒ ⭐ **Il commento del codice va corretto**, perché oggi manda a cercare un difetto che non c'è. ⏳
Lo farà chi tocca quel file per un'altra ragione — **non si apre un giro per questo**.

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

### 8.3 ⭐⭐⭐ **«È ok»** — 22 agosto 2026, sera, sul prodotto con la copia zero accesa

*Il server della porta **7790**, ramo `fase-1` con tutto il lavoro della giornata dentro, tela
2560×1080 (passo 10240, multiplo di 64 ⇒ **la copia zero è accesa**, non ripiega). L'utente si
collega, trascina una finestra veloce come nel suo video del mattino, e giudica:*

> ### ⭐⭐⭐ *«è ok»*

⇒ ⭐ **È il mandato della fase, chiuso dall'unico giudizio che lo poteva chiudere.** Il mandato era
suo — *«l'unico piccolo appunto è un'ottimizzazione sulle performance grafiche»* (§8.1) — e la
specifica pure: *«un'esperienza utente il più vicina possibile a una situazione locale»* (§1.1).

**Il cammino della giornata, nella sua unità:**

| | barre del titolo | |
|---|---|---|
| il **locale** — il pavimento, misurato (n=254, alla sua tela) | **0,142** | |
| REMOTIX **al mattino** | 0,27 · 0,26 | 2,1 × il locale |
| ⭐ REMOTIX **a sera** | **0,16 · 0,16** | **1,23 × il locale** |
| *quel che l'utente riferiva a occhio, al mattino* | *0,50* | |

⚠ **Che cosa questo giudizio dice e che cosa NON dice**, e la distinzione va tenuta:
- ⭐ **dice** che la cura ha funzionato dove conta — sull'occhio dell'utente, sul suo ferro, sulla
  sua scena;
- ⛔ **non dice** se la **previsione falsificabile** di §4-F2 abbia retto. Quella prevedeva
  **0,31-0,46 barre** sul suo schermo, e *«è ok»* è un'accettazione, **non una frazione**. ⏳ Finché
  non c'è la frazione, la spiegazione dello scarto resta **plausibile e non confermata**.

⛔ **E non si scriva che la previsione è confermata**: sarebbe la forma di `LEZIONI.md` §1.20 — *il
giudizio staccato dalla misura* — con l'aggravante di farlo nel documento che quella lezione la
cita.
