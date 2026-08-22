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
> ⇒ ⭐⭐ **337 contro 360: si accordano entro il 7 %**, per due strade che non si sono mai parlate —
> un occhio su un desktop e un cronometro su un banco. ⛔ **E non è una coincidenza fortunata: è la
> prova che l'elastico di §1.2 è il modello giusto.** `distacco = velocità × ritardo` regge sui
> numeri veri.
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

*(il resto si riempie quando avrà qualcosa da guardare)*
