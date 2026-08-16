# F2.5 — La pagina: dal byte al pixel dipinto

*Sotto-fase 5 della fase 2 «Il primo fotogramma». Scritta il 12 agosto 2026.
Mandato: `fasi/rapporti/MANDATO-12-agosto-fase2.md`. Porta **7515**.*

> ⛔ **Questo giro non ha scritto prodotto.** `src/pagina.html` è stata **letta** e non toccata:
> `PIANO.md` §0.4 momento 1 — *il revisore interviene appena il banco esiste, prima che il prodotto
> sia scritto*. Quel che segue è **il banco**, e lo studio che dice al prodotto che forma deve avere.

---

## Che cosa deve produrre

**Che un byte HEVC arrivato sul filo diventi un pixel acceso nella scheda del browser — e che
qualcuno lo possa verificare guardando i pixel, non i numeri del decodificatore.**

L'utente vede il proprio desktop dentro una scheda. Il banco misura **i pixel riletti dalla tela**,
non «`configure()` non ha lanciato». È l'invariante **I8** di `CODER.md` §2: *il metro è quel che
l'utente vede, non il numero che esce dal banco*.

---

## ⛔ Il banco — scritto prima del prodotto

### La scena, dichiarata

| | |
|---|---|
| **dove gira** | CHUWI (i browser stanno qui, non su NIC-OS). ⛔ Su NIC-OS non è stato toccato niente: 7448 e 7501 sono rimaste accese |
| **porta** | **7515**, su `127.0.0.1`, quella assegnata dal mandato §2 |
| **schermo finto** | Xvfb `:75` a 1280×1024×24 — ⛔ **non** `:78` (di S5) né `:10`/`:1024`/`:1025` (in uso) |
| **schermo vero** | `:10`, che è il display di GNOME di questa macchina. ⚠ **`:0` non esiste qui** |
| **il flusso** | un file, costruito da noi con `libx265`, identico a ogni giro |
| **motori** | Chrome **151.0.7922.108** · Firefox **140.13.0esr** |

⛔ **E la scena non si muove, di proposito** — ed è l'unica volta in cui va bene. `LEZIONI.md` §1.1
vuole una scena in movimento perché *un compositore manda un fotogramma solo quando qualcosa
cambia*: qui non c'è nessun compositore da misurare. Il flusso è un file, e **è la sua immobilità a
rendere leggibile la differenza fra un giro e l'altro**.

⛔ **La scena viaggia in ogni riga del registro**, e non è una formalità: vedi §«Le misure», dove lo
stesso browser dà **due risposte opposte** sulle due scene.

### Che cosa si conta

Il flusso noto porta **otto tinte piatte in una griglia 4×2**, distanti fra loro oltre 100 in RGB.
La pagina decodifica, dipinge su una tela 2D, **rilegge i pixel con `getImageData`** e classifica
ogni cella sulla tinta più vicina.

⭐ **La classificazione è immune alla resa del colore e non all'immagine sbagliata**, che è
esattamente la distinzione che serve: la conversione YUV→RGB, il flag di intervallo, la gamma e la
perdita di x265 spostano un canale di qualche decina — non di cento. `[M]` gli scarti misurati vanno
da −20 a +27 per canale, e le celle si classificano lo stesso 8 su 8.

Per ogni prova escono **i denominatori**, non solo il risultato:
`pezzi_attesi · pezzi_dati · fotogrammi_usciti · disegni · celle_lette · celle_giuste · errori`.

### I sei controlli, e perché quattro non bastavano

| | Che cosa chiede | Che difetto impedisce |
|---|---|---|
| **P1** | il lettore trova 8/8 tinte dipinte a mano con `fillRect` | se cade, non manca il decodificatore: manca `getImageData` |
| **P2** | su una tela grigia piatta il lettore **non** trova 8/8 | ⛔ un classificatore che risponde sempre «giusto» passerebbe P1 e ogni sequenza: il banco sarebbe **verde su un difetto vivo** |
| **P3** | i pixel di un pattern non si classificano **anche** sull'altro | un banco che ridipinge sempre la stessa cosa dà la stessa risposta sui due |
| **P4** | ⭐ **VP9 arriva al pixel** | ⛔ se HEVC cade **e** VP9 riesce, il «no» è di HEVC; se cadono tutti e due il «no» è della pagina, e **su HEVC non si scrive niente** |
| **P5** | l'immagine dipinta è più vicina al pattern **chiesto** che all'altro | il flusso arrivato non è quello che il banco crede di aver dato |
| **P6** | ogni sequenza che non dipinge **dice perché** | «zero» e «sono fallito» con lo stesso aspetto (`REVIEWER.md` §1 punto 4) |

> ### ⭐ P5 e P6 sono nati **certificando**, e questa è la parte utile
>
> La prima stesura aveva quattro controlli. Poi due guasti innestati apposta **non hanno fatto
> virare niente**:
>
> | | |
> |---|---|
> | `scambio` — dare al decodificatore i byte del pattern **B** dicendo di aver chiesto **A** | nessun controllo virava. P3 chiede se il *classificatore* distingue; nessuno chiedeva se il *flusso arrivato* fosse quello chiesto ⇒ **P5** |
> | `muto` — buttare i testi degli errori | nessun controllo virava. La regola *«una misura che può dire zero deve poter dire sono fallito»* era **scritta nel banco e non provata dal banco** ⇒ **P6** |
>
> ⛔ È `LEZIONI.md` §1.3 nel verso in cui serve: un controllo che non controlla si dichiara solo
> innestando il difetto che dovrebbe vedere.

### ⛔ Il controllo positivo, e perché non è solo in coda

Il mandato §3.2 chiede *«un controllo positivo in coda a ogni esecuzione»*. Ce n'è uno in coda —
il registro ha righe di **questo** giro, il raccoglitore ha servito N richieste, e i due numeri sono
stampati — **e uno prima della misura, che è quello che conta**: il flusso **VP9** (P4).

⚠ Senza P4, un rosso su Firefox sarebbe indistinguibile fra «Firefox non fa HEVC» e «il banco non
funziona su Firefox»: la forma **E10** vista dall'altra parte, e la stessa che `STUDI.md` §web §3.3 racconta
come il rilievo più grave della revisione R2 — *«il controllo positivo era cieco, e la sua
conclusione era la conclusione sbagliata su un dato mancante»*.

### Il caso opposto, scritto prima — i 10 bit

`DECISIONI.md` §2.3-bis: se il decodificatore torna a 8 bit senza dirlo, i pixel vengono bene lo
stesso e nessuno se ne accorge. Scritto **prima del giro**:

| Che cosa si osserverebbe | Che cosa vorrebbe dire |
|---|---|
| `VideoFrame.format` = `I420P10` | ⭐ i 10 bit sono arrivati **fino al fotogramma**. ⚠ Non fino allo schermo |
| `format` = `I420` su un flusso **Main10** | ⛔ uscita riportata a 8 bit senza dirlo: l'indizio di §2.3-bis, misurato |
| `format` = `null` | ⛔ **non si conclude niente** (`STUDI.md` §web §1.2 A): nullo è «non lo dico», non «8 bit» |

⛔ **E la tela 2D non può rispondere, per costruzione**: `getImageData` restituisce 8 bit per canale.
Qualunque numero letto di lì è a 8 bit anche se il fotogramma ne aveva 10. Questo era scritto prima
del giro, e il giro l'ha confermato in un modo che nessuna delle tre righe prevedeva: `format` non è
`null` né `I420P10` — è **`BGRA`**.

> ⛔⭐ **E poi una cucitura di F2.2 ha cambiato quale domanda stavo facendo.** La sorgente dà **8
> bit**: il pattern di questo banco nasceva in RGB24, quindi le sequenze `*-10bit-*` erano **Main10
> con dentro 8 bit promossi**, e con quelle la domanda non era ponibile. ⇒ Sono state costruite due
> sequenze **lossless** — 220 livelli contro 573 — come **caso di banco**. Il conto per esteso è in
> §«Le misure» 6, e ⛔ **le due domande vanno tenute separate**: *«il browser decodifica un Main10?»*
> ha risposta **sì**; *«conserva i 10 bit?»* **non ha risposta da JavaScript**.

### Come questo banco si certifica — sano N → guasto M → risanato N

⛔ **Gli attesi sono stati scritti prima del giro**, e uno è stato **smentito**. Sono in testa a
`banchi/02-pagina-certifica.sh` come tabella, non come commento.

| Giro | Atteso, scritto prima | Misurato |
|---|---|---|
| **sano** | P1..P6 verdi, `HEVC=arriva` | ✅ come atteso |
| **guasto `pixel`** — dipinge un grigio invece del fotogramma | **P4 rosso**, e P1, P2 **verdi** | ✅ come atteso |
| **guasto `lettore`** — il classificatore risponde sempre giusto | **P2 rosso** e **P3 rosso** | ✅ come atteso |
| **guasto `scambio`** — i byte dell'altro pattern | **P5 rosso** | ✅ come atteso |
| **guasto `muto`** — gli errori buttati | **P6 rosso**, P1 e P4 verdi | ✅ come atteso |
| **`livello`** — codec con livello più basso del vero | `HEVC=non-arriva` (`RCP.md` §4.3, **O12**) | ⛔ **SMENTITO**: `HEVC=arriva` |
| **risanato** | P1..P6 verdi, `HEVC=arriva` | ✅ come atteso |

⭐ **Che P1 e P2 restino verdi sotto il guasto `pixel` fa parte dell'atteso**, e non è un dettaglio:
è quel che dice a chi legge che il rosso è del percorso del video e non del lettore. Un guasto che
facesse virare tutto insegnerebbe solo che qualcosa c'è.

`[M]` 12 agosto 2026 — l'ultima esecuzione: **sano → 5 guasti → risanato, tutte le pretese onorate**,
uscita 0.

---

## Che cosa si riusa da v1

⛔ **Niente, e la riga va scritta così invece di essere lasciata vuota.** `PIANO.md` fase 2 elenca
`cattura.c`, `mutter.c`, `superficie.c`, `immagine.c`, `codificatore.c`, `palco.c`: sono tutti del
**lato server**, e appartengono a F2.1–F2.3. v1 **non aveva un client web** — la decisione di non
avere client dedicati è del 9 agosto 2026 (`DECISIONI.md` §1.6), cioè posteriore a tutto v1.

Quel che si riusa è **di V2, della fase 1**, e contato sul file vero:

| File | Righe vere | Che cosa se ne è preso |
|---|---|---|
| `banchi/01-s2-pagina.html` | **442** | la forma della pagina di sonda, il richiamo `output` che chiude ogni fotogramma, e ⭐ **l'idea del controllo VP9** che rende valido il banco (S2 §4.4) |
| `banchi/01-s5-tela.sh` | **310** | la struttura del lanciatore: Xvfb, raccoglitore, `prova_motore`, il verdetto calcolato **fuori** dal browser |
| `banchi/01-s5-raccogli.py` | **72** | il raccoglitore con il **denominatore** delle richieste su stderr |
| `banchi/01-s5-pagina.html` | **85** | la convenzione del `?giro=` e della riga per giro |
| `src/pagina.html` | **662** | ⛔ **letta, non toccata**: la forma di `Scrittore`/`Lettore`/`Canale`, e la cura del congedo dell'11 agosto |

⚠ **Una differenza dichiarata rispetto a `01-s2-pagina.html`**: lì il controllo VP9 se lo costruisce
la pagina con `VideoEncoder`. Qui arriva da `ffmpeg`. ⛔ Un controllo che dipende da una **seconda**
API del browser sparisce proprio sul motore dove serve di più — quello che di WebCodecs ha poco.

---

## ⛔ Le trappole già pagate che mordono qui

| Trappola | Dove sta scritta | Come morde in F2.5, e che cosa si è fatto |
|---|---|---|
| **E1 — necessario preso per sufficiente** | `REVIEWER.md` §2, `STUDI.md` §web §4.1 e §9.1, `LEZIONI.md` §1.11 | ⛔ `isConfigSupported()` vero è compatibile con **una tela nera**. Qui si chiama, si **registra** in una casella chiamata «che cosa avrebbe detto l'API», e **non entra in nessun verdetto**. ⭐ E il giro l'ha pagata sul serio: vedi la contraddizione fra API su Firefox |
| **E10 — la prova verde sul client sbagliato** | `REVIEWER.md` §2, `STUDI.md` §web §7 | vista **dall'altra parte**: un rosso su un motore dove il banco non funziona. Curata con P4 (VP9) |
| **il controllo positivo cieco** | `STUDI.md` §web §3.3 (rilievo R1 di R2) | *«con la porta chiusa la prova fallisce su tutti e due, il controllo è verde, e la conclusione è quella sbagliata su un dato mancante»*. Qui il controllo è **sullo stesso motore, nella stessa pagina, nello stesso giro** |
| **zero e fallimento** | `LEZIONI.md` §1.9, `REVIEWER.md` §1 punto 4 | «nessun fotogramma» ha almeno cinque cause con lo stesso aspetto. Curata con i denominatori e **certificata** dal guasto `muto` (P6) |
| **il denominatore** | `LEZIONI.md` §1.9 quarta regola | ⭐ **ha pagato subito**: Firefox non partiva e il banco ha scritto *«ZERO richieste: il browser non ha nemmeno aperto la pagina»* invece di «Firefox non decodifica niente» |
| **E2 — due comportamenti sotto la stessa etichetta** | `REVIEWER.md` §2 | lo stesso Chrome dà **due risposte opposte** su Xvfb e su schermo vero. Curata portando **la scena in ogni riga** del registro |
| **la trappola dell'`hvcC`** | `STUDI.md` §web §4.2 | *«Chromium riparsa l'SPS e rifiuta la configurazione se i byte di prevenzione dell'emulazione cadono nel campo sbagliato»*. ⭐ **Ci è caduto il nostro generatore**, da un'altra porta: vedi sotto |
| **O12 — il livello dichiarato** | `RCP.md` §4.3 | *«un livello troppo basso non dà un errore di rete: fa rifiutare la configurazione dal decodificatore»*. Innestato apposta — e **smentito su Chrome** |
| **il tracciatore cieco dentro `pagehide`** | `fasi/01-filo-nudo.md`, banco P5 | *«né `sendBeacon` né la XHR sincrona escono: sei giri, zero tracce»*. ⛔ Questa pagina **non spedisce niente dentro `pagehide`**: ogni esito parte con un `fetch` **atteso** mentre la scheda è viva, e il banco chiude il browser solo dopo aver letto la riga `FINITO` |
| **`LEZIONI.md` §1.8 — il componente che decide da sé** | | x265, lasciato scegliere, emetteva un profilo **che non avevamo chiesto**. Curata chiedendo il profilo per nome **e verificando che abbia obbedito** |
| **§2.4 — il metro è quel che si vede** | `LEZIONI.md` | i 10 bit **non sono leggibili da JavaScript**: la striscia di sfumatura è nel pattern per il giorno in cui la guarderà l'utente |

> ### ⛔⭐ Due difetti che questo banco ha trovato **in sé stesso**, il 12 agosto
>
> Sono nel codice con la data accanto, perché sono i due che avrebbero avvelenato tutto il resto.
>
> **1. Il lettore dell'SPS non sgusciava i byte di prevenzione dell'emulazione.** La stringa di codec
> usciva `hev1.4.C0000010.L0.00.9D…` — profilo 4, **livello 0**. L'SPS di x265 contiene `00 00 03 00`
> proprio dentro i flag di compatibilità, e leggerlo così com'è sposta di uno tutto ciò che segue,
> **livello compreso**. ⚠ E un livello a 0 non dà un errore di rete: è **O12**, e il sintomo sarebbe
> stato *«Chrome non apre il flusso»* — cioè un `[M]` falso contro il browser. ⭐ È letteralmente la
> trappola che `STUDI.md` §web §4.2 attribuisce all'`hvcC`, solo che a caderci era **il nostro lettore**.
>
> **2. La profondità di bit nell'`hvcC` era scritta agli indici sbagliati** (19 e 20, che sono
> `avgFrameRate`, invece di 17 e 18). Un flusso a 10 bit portava una descrizione che ne dichiarava 8.
> ⚠ Un decodificatore indulgente non se ne accorge — i bit veri stanno nell'SPS — e il banco avrebbe
> misurato i 10 bit con una descrizione che ne dichiara 8: **E2 dentro il banco**.

---

## Le misure

⛔ **Tutte con la scena accanto**, perché è la scena a decidere una delle due risposte.
Registro: `banchi/02-pagina-esiti.jsonl`. Giri di riferimento del 12 agosto 2026, con **tutte e 16
le sequenze**:

| | schermo **vero** `:10` | **Xvfb** `:75` |
|---|---|---|
| **Chrome 151** | `f25-chrome-1786536911` | `f25-chrome-1786537126` |
| **Firefox 140 ESR** | `f25-firefox-1786536915` | `f25-firefox-1786537130` |

Si rileggono con `python3 banchi/02-pagina-verdetto.py <giro>`.

### 1. ⭐ Il fatto che conta più di tutti: HEVC arriva al pixel su Chrome — **ma solo con la GPU**

| Motore | Scena | `isConfigSupported` HEVC | Pixel dipinti | Marca |
|---|---|---|---|---|
| **Chrome 151** | schermo **vero** `:10` (GPU Intel UHD, VA-API) | **true** | ⭐ **8/8 celle giuste**, 6 fotogrammi su 6, Main **e** Main10, Annex-B **e** hvcC | `[M]` 12 ago 2026 |
| **Chrome 151** | **Xvfb** `:75` (nessuna GPU) | ⛔ **false su tutte e 7 le stringhe** | ⛔ **zero**, `OperationError: Unsupported configuration` | `[M]` 12 ago 2026 |
| **Firefox 140 ESR** | schermo **vero** `:10` | ⛔ **false** | ⛔ **zero**, `NotSupportedError: Operation is not supported` | `[M]` 12 ago 2026 |
| **Firefox 140 ESR** | **Xvfb** `:75` | ⛔ **false** | ⛔ **zero**, stesso errore | `[M]` 12 ago 2026 |

⛔ **In tutti e quattro i casi il controllo VP9 (P4) è verde, 8/8**: la catena
decodifica→tela→rilettura esiste su tutti e due i motori e su tutte e due le scene. **Il «no» è di
HEVC, non del banco.**

**La causa, e non è dedotta:** sullo stesso giro, `hardwareAcceleration: "prefer-software"` su Chrome
schermo vero dà `OperationError: Unsupported configuration` mentre `prefer-hardware` e
`no-preference` dipingono 8/8. ⇒ `[M]` **Chrome su Linux non impacchetta un decodificatore HEVC
software**: HEVC esiste solo attraverso la piattaforma (VA-API), e senza GPU sparisce.
⚠ `vainfo` su questa macchina dichiara `VAProfileHEVCMain` e `VAProfileHEVCMain10` con
`VAEntrypointVLD` `[M]` — il ferro c'è, ed è quel che Chrome usa.

> ⭐ **E questo è il complemento esatto di `STUDI.md` §web §4.1**, che dice il contrario per Android: *«su
> desktop `prefer-hardware` è una prova vera: il broker butta via del tutto la fabbrica dei
> decodificatori software»* `[R]`. Misurato: su Linux **non c'è proprio nessuna fabbrica software per
> HEVC**, quindi su questa piattaforma HEVC riuscito **implica** hardware. ⛔ Ma vale **qui**, non su
> Android, dove §4.1 dice che Chromium ne sceglie uno software di proposito.

### 2. ⭐⭐ La contraddizione fra API su Firefox — **la misura più importante del giro**

`[M]` 12 agosto 2026, Firefox 140.13.0esr, schermo vero, **su tutte e 7 le stringhe HEVC**:

| Chi risponde | Che cosa dice |
|---|---|
| `navigator.mediaCapabilities.decodingInfo()` | `supported: true` · `smooth: true` · **`powerEfficient: true`** |
| `video.canPlayType()` | **`"probably"`** |
| `VideoDecoder.isConfigSupported()` | ⛔ **`false`** |
| **il pixel** | ⛔ **niente**: `NotSupportedError` a `configure()` |

⛔ **Tre testimoni concordi, e sbagliati.** Una pagina che scegliesse il codec chiedendo a
`mediaCapabilities` — che è l'API *fatta apposta* per quella domanda — sceglierebbe HEVC su Firefox
e **non dipingerebbe niente**. È la forma **E1** con la sua veste più convincente: non un'API
indulgente, ma **due** che si confermano a vicenda.

⚠ E `powerEfficient: true` su un codec che il browser non decodifica affatto è la riga che chiude il
discorso su quanto valga quel campo: `STUDI.md` §web §4.1 lo trattava già come non-prova per l'hardware;
`[M]` **non è nemmeno una prova del supporto**.

### 3. ⭐ La `[?]` di F2.3 sui prefissi, chiusa

F2.3 consegna la stringa come `hev1.…` e dichiara aperta: *«non è verificato che Chromium accetti il
prefisso `hev1.` in Annex-B»*.

`[M]` 12 agosto 2026, Chrome 151, schermo vero, **stesso flusso Annex-B senza `description`**:

| Stringa | Pixel |
|---|---|
| `hev1.2.4.L90.90` | ⭐ **8/8** |
| `hvc1.2.4.L90.90` | ⭐ **8/8** |

⇒ **Tutti e due i prefissi vanno**, in Annex-B puro. Chromium decide la forma del flusso dalla
**presenza della `description`**, non dal prefisso. ⭐ La scelta di F2.3 è confermata dal pixel, e la
`[?]` si chiude.

### 4. ⛔ Le due forme non sono intercambiabili — e i due errori sono asimmetrici

`[M]` 12 agosto 2026, Chrome 151, schermo vero:

| Che cosa si è fatto | Che cosa succede |
|---|---|
| byte **hvcC** (lunghezze davanti) con configurazione **senza** `description` | ⭐ `DataError` **alla prima `decode()`**, e il messaggio nomina la cura: *«A key frame is required after configure() or flush(). **If you're using HEVC formatted H.265 you must fill out the description field in the VideoDecoderConfig**»* |
| byte **Annex-B** con configurazione **con** `description` | ⛔ `configure()` **passa**, e poi `EncodingError: Decoder error.` — **e non nomina la `description`** |

⛔ **L'asimmetria è la parte che serve a F2.3**: sbagliare in un verso ti dà il nome della cura,
sbagliare nell'altro ti dà un errore generico a decodifica avviata. ⇒ La strada scelta da F2.3
(Annex-B senza `description`) è anche quella in cui **l'errore opposto si diagnostica da solo**.

### 5. ⛔ L'atteso su O12 è stato **smentito**, e la conseguenza non è rassicurante

Innestato apposta il guasto `livello`: stringa `hev1.2.4.**L30**.90` — livello 1.0 — su un flusso
640×480 il cui livello vero è **3.0** (letto nell'SPS **e** confermato da `ffprobe`: 90).

Atteso, scritto prima, da `RCP.md` §4.3 rilievo **O12**: *«fa rifiutare la configurazione dal
decodificatore»* ⇒ `HEVC=non-arriva`.

`[M]` **Misurato**: `isConfigSupported` → **true**, `configure()` passa, **8 celle su 8 dipinte**.
⛔ Il guasto **era entrato in vigore** — `codec_chiesto` nel registro dice `hev1.2.4.L30.90` — quindi
non è «il guasto non si è innestato»: è che **Chrome 151 su Linux non fa rispettare il livello
dichiarato**.

⚠ **E va letto nel verso giusto**: un livello sbagliato che *non* viene rifiutato è **peggio** di uno
rifiutato, perché toglie il sintomo che lo diagnosticava. Il conto lo pagherà il dispositivo che il
livello lo fa rispettare davvero — e lì il sintomo comparirà **altrove**, lontano dalla causa.

### 6. ⛔ I 10 bit — e F2.2 ha cambiato **quale domanda** stavo misurando

> ⛔⭐ **Questa sezione è stata riscritta dopo la cucitura di F2.2, e la prima stesura aveva un
> difetto mio.** F2.2 ha misurato che **la sorgente dà otto bit**: Mutter consegna solo BGRx/BGRA,
> 8 bit per canale `[M]`. ⇒ In fase 2 il flusso che arriva alla pagina è **Main10 con dentro 8 bit
> promossi**.
>
> ⛔ E lo stesso valeva per le sequenze di questo banco: il pattern nasceva in **RGB24**. Quindi la
> mia riga *«il flusso Main10 e quello Main dipingono pixel identici ⇒ i pixel non distinguono
> 10 bit da 8»* **non dimostrava quel che dicevo**: dimostrava che **la mia sorgente era già a
> 8 bit**. Due cause diverse con lo stesso aspetto — la forma **E1** applicata a me.

⇒ Sono state costruite due sequenze nuove, **caso di banco e non catena vera**, per porre la domanda
che la catena vera non può porre: stesso pattern, stessa codifica **senza perdita**, stesso
contenitore Main10, e dentro contenuti diversi.

**Che cosa c'è nei flussi**, misurato `[M]` 12 agosto 2026 sulla striscia di sfumatura, con un
contatore scritto in `02-pagina-sequenze.py` — ⚠ **non importato da F2.3**: due letture indipendenti
della stessa grandezza valgono più di una riusata due volte.

| Sequenza | Sorgente: livelli · ×4 | Flusso ridecodificato: livelli · ×4 |
|---|---|---|
| `A-10bit-lossless` — 8 bit **promossi** | **220** · **1,000** | **220** · 0,2531 |
| `A-10bitvero-lossless` — **10 bit veri** | **640** · 0,2547 | **573** · 0,2469 |

⭐ **Il conteggio dei livelli distingue i due flussi (220 contro 573); la frazione di multipli di 4
no.** ⛔ E la ragione è che la firma «tutti i campioni sono `v8 << 2`» **non sopravvive alla
conversione RGB→YUV**, che è un'altra trasformazione con arrotondamento — nemmeno con `lossless=1`,
che è lossless *in YUV*, non da RGB. ⚠ Con la codifica a **CRF 16** si perde anche il conteggio:
0,2488 contro 0,2524 e 411 contro 616, cioè due numeri che non separano.

⇒ ⛔ **A valle della codifica nessuno può sapere se il contenuto fosse a 8 o a 10 bit** — né il
browser, né F2.6, né noi. Quel che F2.2 ha misurato **alla sorgente** resta l'unica risposta.

**E che cosa arriva alla tela**, `[M]` Chrome 151, schermo vero:

| Sequenza | Livelli nel flusso | ⛔ Livelli **dipinti sulla tela** |
|---|---|---|
| `A-10bit-lossless` (8 bit promossi) | 220 | **233** |
| `A-10bitvero-lossless` (10 bit veri) | **573** | **236** |

⛔ **Due flussi che differiscono di 220 contro 573 livelli dipingono 233 contro 236.** La tela non li
distingue — e non per un difetto del browser: `getImageData` è a **8 bit per canale**, tetto 256, per
costruzione. ⭐ Questa volta è una **misura**, non un argomento.

**E il formato del fotogramma non aiuta.** `[M]` Chrome 151/Linux, decodifica hardware:
`VideoFrame.format` è **`"BGRA"`** — non `null`, e non `I420P10`. `copyTo()` restituisce **un solo
piano di 1 228 800 byte**, cioè 640 × 480 × 4. Su Firefox il controllo VP9 dà **`"BGRX"`**.

| | |
|---|---|
| ⛔ **quel che NON si può concludere** | che i 10 bit siano persi. `BGRA` è come Chrome **presenta** una tessitura di GPU, non necessariamente come la tiene |
| ⛔ **quel che si può concludere** | **da JavaScript i 10 bit non sono osservabili**, né dal formato, né dai piani, né dalla tela — e adesso con un flusso a 10 bit veri sotto, non solo per argomento |
| ⭐ **quel che si è misurato lo stesso** | Chrome **decodifica e dipinge correttamente** un Main10 a 10 bit veri: 8/8 celle. La domanda «lo decodifica?» ha risposta **sì**; quella «li conserva?» non ha risposta da qui |

⇒ ⚠ **`STUDI.md` §web §1.2 A va aggiornata su due punti**: l'indizio `[S]` del 2023 («`format` è `null`») è
superato da una misura (**è `BGRA`**), e la frase *«dal browser i 10 bit non sono leggibili»* passa da
`[?]` a **`[M]`**, con il flusso a 10 bit veri come prova.

### 7. La fedeltà del colore — i numeri, per F2.6

`[M]` scarti per canale fra il pixel dipinto e il colore d'origine, Chrome 151, schermo vero,
flusso Main10 Annex-B, prime tre celle:

| Cella | Atteso | Letto | Scarto |
|---|---|---|---|
| rosso | 220, 32, 32 | 204, 12, 34 | −16, −20, +2 |
| verde | 32, 200, 64 | 46, 227, 68 | +14, +27, +4 |
| blu | 48, 64, 220 | 51, 55, 214 | +3, −9, −6 |

Il fotogramma dichiara `primaries: bt709 · transfer: bt709 · matrix: bt709 · **fullRange: false**`.
⚠ Gli scarti sono compatibili con un giro completo pieno→limitato→pieno più la perdita di x265 a
CRF 16. ⛔ **F2.5 non giudica la fedeltà**: la misura è consegnata a F2.6, che è la sotto-fase del
giudizio.

---

## ⛔ Che cosa NON ha funzionato

1. ⛔ **Il primo giro ha dato un rosso su Chrome che avrei potuto attribuire male.** Otto sequenze su
   otto rifiutate, `Unsupported configuration`. Le letture possibili erano tre — Chrome non ha HEVC ·
   Chrome non ha HEVC **su questa scena** · la nostra stringa è storta — e **hanno lo stesso
   aspetto**. Curato con il **sondaggio delle stringhe** (le nostre, le canoniche, `hvc1`, e tre
   controlli non-HEVC) e con il giro sulla **seconda scena**. Senza, il rapporto avrebbe scritto
   `[M] Chrome non decodifica HEVC`, che è **falso per metà degli utenti**.
2. ⛔ **`keyint=1` era la scelta sbagliata, e sembrava la più fedele.** Tutto-intra pareva la forma
   giusta per «un'immagine ferma», ma x265 in tutto-intra emette il profilo **`Main 10 Intra`**, che
   nel flusso è `profile_idc = 4` (**Rext**) e non 2: la domanda al browser sarebbe stata posta su un
   profilo che né `SPECIFICHE.md` né `RCP.md` nominano.
3. ⛔ **Il lettore dell'SPS non sgusciava i byte di prevenzione dell'emulazione** — livello letto 0
   invece di 90. Vedi il riquadro sopra.
4. ⛔ **La profondità di bit nell'`hvcC` scritta agli indici sbagliati.** Vedi il riquadro sopra.
5. ⛔ **Firefox non partiva con `--width` e `--height`**, e il banco ha registrato «ZERO richieste al
   raccoglitore». ⭐ Il denominatore ha fatto esattamente il suo mestiere: senza, quel giro sarebbe
   stato letto come «Firefox non decodifica niente».
6. ⛔ **Una sostituzione di testo ha rotto una stringa in `02-pagina-verdetto.py`**, e la
   certificazione è andata **tutta rossa**. ⭐ Anche questo è il comportamento giusto: uno strumento
   di verdetto che non parte deve far fallire ogni pretesa, non passarle in silenzio.
7. ⛔⭐ **Il mio confronto sui 10 bit non dimostrava quel che dicevo**, e l'ha trovato una cucitura
   di **F2.2**, non io. Le sequenze `*-10bit-*` nascono da un pattern **RGB24**: sono Main10 con
   dentro 8 bit promossi. *«I pixel non distinguono 10 bit da 8»* era vero e **non per la ragione che
   avevo scritto**. Curato costruendo un flusso a 10 bit veri, e la conclusione ora regge su una
   misura invece che su una coincidenza (§6).
8. ⚠ **Il `[?]` sui 10 bit non si è chiuso**, e non era realistico che si chiudesse: non è una
   mancanza del giro, è una proprietà del browser (§6).

---

## Le decisioni prodotte

⛔ Nessuna decisione nuova da scrivere in `DECISIONI.md` da parte di F2.5: questo giro **misura** e
**consegna**. Le decisioni che tocca, e che il coordinatore dovrà valutare:

- `DECISIONI.md` §2.3-bis (i 10 bit) — la misura dice che **da JavaScript la domanda non è ponibile**;
- `DECISIONI.md` §2.7 (il massimo lo offre il server, l'altezza la mette il client) — ⭐ **applicata
  alla lettera**: Firefox senza HEVC non è un difetto di REMOTIX, è un fatto da dichiarare;
- `RCP.md` §4.3 rilievo **O12** — smentito su Chrome/Linux (§5);
- `STUDI.md` §web §1.2 A — l'indizio `[S]` del 2023 superato da una misura (§6);
- `STUDI.md` §web §4.1 — il complemento per Linux desktop: nessuna fabbrica software per HEVC (§1).

⭐ **Due decisioni piccole prese da me, e dichiarate:**

1. **La tela del banco non è desincronizzata**, mentre `STUDI.md` §web §6.1 la vuole così per il *prodotto*.
   Ragione: qui la misura **è la rilettura**, e su una tela desincronizzata `getImageData` legge da un
   buffer che il compositore può avere già scambiato. Un'ambiguità nel punto in cui sta la misura
   vale meno di un millisecondo di ritardo in un banco. ⚠ Va detto perché nessuno legga questo file
   come «la forma che il prodotto avrà».
   > ⛔ *13 agosto 2026 — e la seconda metà di questa riga è caduta: **nemmeno il prodotto ha la tela
   > desincronizzata.** `src/pagina.html:407` ha `desynchronized` **spento** `[R]`, e la strada per
   > accenderlo (`?tela=desincronizzata`) **non è mai stata raggiungibile**: `src/pagina.c:243` manda
   > in **404** qualunque percorso con un `?`. ⇒ ⛔ Non è «un interruttore spento», è **un interruttore
   > che non c'è**, e la differenza conta: un interruttore spento si accende per misurare, uno che non
   > esiste no. ⚠ Non visto da nessuno perché i banchi servono la pagina da un `http.server` di
   > Python, che il `?` lo ignora. ⇒ Il guadagno della tela desincronizzata resta `[?]`: **non è mai
   > stato misurato**.*
2. **Le sequenze hanno 6 fotogrammi (1 chiave + 5 delta)** mentre la fase 2 ne consegna **uno**.
   Ragione: cinque delta in più distinguono «ha decodificato» da «ha decodificato il primo e si è
   fermato», e `bframes=0` perché un fotogramma B uscirebbe in un ordine diverso da quello di
   presentazione. ⚠ Dichiarata come **differenza voluta** dal flusso della fase 2.

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⛔ `[?]` **i 10 bit fino allo schermo** | ⭐ e adesso non è più un'ipotesi che non si chiuda da qui: è **misurato**. Due flussi con **220** e **573** livelli dipingono **233** e **236** — `getImageData` è a 8 bit, tetto 256. La prova resta **guardare la sfumatura** (`LEZIONI.md` §2.4), e i PNG sono su disco |
| ⛔ `[?]` **i 10 bit servono a qualcosa, in fase 2?** | ⚠ **no, e non per colpa del browser**: F2.2 misura la sorgente a **8 bit** (Mutter dà BGRx/BGRA). In fase 2 il Main10 porta 8 bit promossi. La domanda diventa di F2.2 e della cattura, non della pagina |
| ⛔ `[?]` **HEVC su Chrome per Android / DeX** | ⛔ **non misurato, e non è una dimenticanza**: vuole il dispositivo. *«Il Chrome del portatile lo fa»* non dice niente del Chrome del telefono — forma **E10** (`DECISIONI.md` §5-bis.0-ter). Il banco è lo stesso e la pagina è la stessa: il giorno che il dispositivo c'è, si apre quell'indirizzo |
| ⛔ `[?]` **Safari / WebKit** | nessun dispositivo Apple. `STUDI.md` §web §2 dà `VideoDecoder` da Safari 26 e HEVC pieno dalla 26.0 `[S]`, mai misurato da noi |
| `[?]` **Firefox con `media.hevc.enabled`** | ⛔ **non provato di proposito**: si è misurato il Firefox **che l'utente ha**, senza toccare preferenze. Un flag che accende una strada che il browser di serie non ha produce un `[M]` che non vale per nessun utente (**E10**) |
| `[?]` **un fotogramma chiave grande** | F2.3 misura IDR da **96 237 byte** lossless e **21 569** a CRF 20; le sequenze di questo banco stanno sotto i 4 KB. ⚠ Che il percorso regga un IDR da centinaia di KB **non è stato misurato qui** |
| `[?]` **il ritardo** | F2.5 misura **che** il pixel arrivi, non **quando**. L'anello di `DECISIONI.md` §2.6 e i 16-40 ms del compositore (`STUDI.md` §web §6.2) restano di S4 |
| `[?]` **AV1** | `isConfigSupported` vero su tutti e due i motori, `powerEfficient: false` su tutti e due. Nessuna sequenza AV1 costruita: `STUDI.md` §web **O2** lo dichiara vicolo cieco da entrambi i lati |
| `[?]` **`av01`/`hev1` su altre GPU** | la misura di §1 è su **Intel UHD 730 / iHD**. Su AMD e NVIDIA il risultato può cambiare, e cambierebbe **per la stessa ragione** (il decodificatore è della piattaforma) |

---

## Le cuciture

### ⛔ Che cosa F2.5 **pretende** da F2.3 (la codifica)

Le prime tre sono **confermate dal pixel**, non richieste: F2.3 aveva già deciso così, e questo banco
lo ha misurato.

1. ⭐ **Annex-B puro, nessuna `description`** — confermato: 8/8 celle su Chrome. E la scelta è anche
   quella in cui **l'errore opposto si diagnostica da solo** (§4).
2. ⭐ **`[00 00 00 01]` davanti a ogni NALU, VPS·SPS·PPS·SEI·IDR, primo fotogramma sempre chiave** —
   è esattamente la forma che le sequenze di questo banco portano, e che Chrome accetta.
3. ⭐ **La `[?]` sul prefisso è chiusa**: `hev1.` **e** `hvc1.` vanno tutti e due in Annex-B (§3).
   ⇒ F2.3 può tenere `hev1.` senza riserve.
4. ⛔ **La stringa di codec va composta dai byte del flusso, non a memoria** — e **sgusciando** le
   NALU prima di leggere il `profile_tier_level`. È il difetto che questo banco ha pagato in proprio,
   e il sintomo sarebbe stato «il browser non apre il flusso», che non nomina la causa.
5. ⛔ **Il profilo si chiede per nome e si verifica che sia stato dato.** `libx265` in tutto-intra
   emette **Rext**, non Main10.
6. ⚠ **Il livello dichiarato non è protetto da Chrome** (§5): un valore sbagliato **non** verrà
   rifiutato lì, quindi il controllo deve stare **dal lato del server**, non essere atteso dal browser.
7. `[?]` **Un IDR da 96 KB non è passato per questo banco.** Se F2.3 lo consegna, vale la pena
   ripassarlo di qui: è una riga di `02-pagina-sequenze.py`.

### ⛔ Che cosa F2.5 **pretende** da F2.4 (il filo)

1. ✅ **L'intestazione di 28 byte di `RCP.md` §6.2 è già letta da questo banco**, con un lettore
   scritto **qui, dalla specifica**. `[M]` 6 pezzi su 6, **0 in disaccordo** con quel che il nostro
   scrittore ci aveva messo.
2. ⛔ **E il divieto è stato rispettato alla lettera**: `banchi/02-filo-fotogramma.py` **non è stato
   letto, importato né ricopiato**. Lo scrittore in `02-pagina-sequenze.py` (`intestazione_rcp()`) e
   il lettore in `02-pagina-prova.html` (`leggi_intestazione()`) vengono dalla tabella di `RCP.md`
   §6.2 e da nient'altro. ⭐ ⇒ **Ci sono davvero due implementazioni indipendenti**, ed è il pezzo di
   arbitro che `PIANO.md` §0.4 dice di aver comprato buttando mstsc. Se un giorno non andranno
   d'accordo, **quel disaccordo è il regalo**.
3. ⛔ **`FIN` ⇒ completo, `RESET` ⇒ si butta e non si consegna al decodificatore** — accettato, e
   ⚠ **non è misurato da questo banco**: qui il filo non c'è, i pezzi arrivano da un file. Il giorno
   in cui la pagina consumerà il filo, quel ramo va misurato **dal lato della pagina**, perché
   consegnare mezzo fotogramma al decodificatore è la forma **E8** (`RCP.md` §6.2).
4. ⚠ **Un avvertimento che vale per il canale**: `scambio-annexb-con-descrizione` mostra che byte
   validi con una configurazione sbagliata danno `EncodingError: Decoder error.` **e basta**. Se un
   giorno il filo consegnasse byte troncati, il sintomo sarebbe **lo stesso**. ⇒ Il buco va
   riconosciuto **prima** del decodificatore, dal `numero` e dal `RESET`, non dopo.

### ⭐ Che cosa F2.5 **consegna** a F2.6 (il giudizio)

⛔ **Pixel leggibili, in tre forme, e nessuna delle tre è il nostro verdetto.**

| Che cosa | Dove | A che serve |
|---|---|---|
| **PNG a piena risoluzione** del fotogramma dipinto, 640×480 | `banchi/02-pagina-pixel/<giro>-<prova>.png` | ⭐ **il confronto vero**: è l'immagine come è uscita dalla tela del browser |
| **miniatura 32×24 in RGB**, base64, dentro il registro | campo `miniatura_rgb32x24` di ogni riga `SEQUENZA` | si rilegge fra sei mesi **senza avere più i file accanto** |
| **le otto celle**, con colore letto, colore atteso e scarto per canale | campo `letture` di ogni riga `SEQUENZA` | i numeri della fedeltà, già estratti |

Accanto, per ogni riga: **la scena**, il motore con la versione esatta, la stringa di codec chiesta,
i denominatori, e `contro_pattern` (quanto quell'immagine somiglia all'**altro** pattern).

⛔ **Tre cose che F2.6 deve sapere prima di giudicare:**

1. **F2.5 non giudica la fedeltà del colore**, di proposito. Il criterio di F2.5 è la
   classificazione su otto tinte lontane — robusta e grossolana apposta. Gli scarti misurati arrivano
   a **27 su un canale** e sono compatibili con il giro pieno→limitato→pieno: se F2.6 usasse una
   soglia stretta senza tenerne conto, boccerebbe codice giusto (`LEZIONI.md` §2.3).
2. **Il fotogramma dichiara `fullRange: false`**: il confronto col fotogramma catturato deve dire
   **quale delle due convenzioni** applica, o misurerà lo scarto di conversione invece della qualità.
3. ⛔ **Sui 10 bit F2.6 non troverà niente nei pixel**: il flusso Main10 e quello Main dipingono
   pixel identici a meno di 1. ⇒ Il giudizio sui 10 bit **è dell'utente, sulla sfumatura**
   (`LEZIONI.md` §2.4), non del confronto numerico.

### ⛔ Che cosa F2.5 ha **preso** da F2.2, e che cosa le rimanda

**Preso, e ha corretto un difetto mio**: la sorgente dà **8 bit** `[M]`, quindi in fase 2 il Main10
porta 8 bit promossi, e la domanda *«il decodificatore torna a 8 bit senza dirlo?»* con quel flusso
**non è ponibile**. ⇒ Costruite due sequenze a **10 bit veri** come **caso di banco**, e riscritta
la §6 dicendo **quale delle due domande** si sta misurando (§6).

**Rimandato a F2.2 e a F2.3, ed è la parte che le riguarda:**

1. ⛔ **La firma dei «multipli di 4» non sopravvive alla codifica**, e nemmeno a `lossless=1` — perché
   si perde già nella conversione **RGB→YUV**, non in x265. `[M]` sorgente 1,000 → flusso 0,2531.
   ⇒ Se F2.3 volesse verificare a valle che il contenuto sia a 10 bit veri, **quella metrica non
   serve lì**: il discriminante che sopravvive è il **conteggio dei livelli distinti** (220 contro
   573 senza perdita), e a CRF 16 **non sopravvive nemmeno quello** (411 contro 616).
2. ⚠ ⇒ **La misura dei bit veri si fa alla sorgente o non si fa.** Quel che F2.2 ha contato su
   Mutter è l'unico posto dove la domanda ha una risposta pulita, e va tenuto lì.
3. ⚠ **Un avvertimento sul livello**: le sequenze **lossless** escono con livello `L255` (8,5) — il
   flusso senza perdita fa dichiarare a x265 un livello altissimo. `[M]` Chrome le decodifica lo
   stesso. Se F2.3 usasse mai una codifica lossless, quella stringa va guardata.

### Che cosa F2.5 **dichiara** a F2.1 e F2.2

⚠ Una riga, e riguarda la scena: ⛔ **un banco che guida un browser vero su uno schermo finto misura
un browser senza GPU**, e su Chrome/Linux quello cambia la risposta su HEVC. Se F2.1 o F2.2 avessero
bisogno di far girare un browser, la scena va dichiarata accanto al numero — non è una formalità, è
la differenza fra `arriva` e `non-arriva`.

---

## La riga per il catalogo delle certificazioni

*Nella forma di `banchi/01-b12-guasti.py`. ⛔ L'atteso è scritto **prima** del giro; la riga
`livello` porta l'atteso originale **e** la smentita, invece di essere riscritta.*

| nome | comando | atteso sano | guasto da innestare | atteso guasto |
|---|---|---|---|---|
| `f25-pixel` | `SCHERMO=:10 SCHERMO_VERO=1 GUASTO=pixel bash banchi/02-pagina-lancia.sh` | `P4=verde` (VP9 8/8 celle) | la pagina dipinge `#808080` invece di `drawImage(frame)` | ⛔ `P4=rosso`, **e `P1=verde`, `P2=verde`** — il rosso è del percorso video, non del lettore |
| `f25-lettore` | `… GUASTO=lettore …` | `P2=verde` (1/8 su tela grigia), `P3=verde` | il classificatore risponde sempre «la tinta attesa» | ⛔ `P2=rosso` **e** `P3=rosso` |
| `f25-scambio` | `… GUASTO=scambio …` | `P5=verde` (12 sequenze) | al decodificatore vanno i byte del pattern **opposto** | ⛔ `P5=rosso` |
| `f25-muto` | `… GUASTO=muto …` | `P6=verde` (3 zeri, tutti con causa) | i testi di `errore_configure` e `errori_decode` vengono buttati | ⛔ `P6=rosso`, `P1=verde`, `P4=verde` |
| `f25-livello` | `… GUASTO=livello …` | `HEVC=arriva` | la stringa di codec dichiara `L30` (livello 1.0) su un flusso di livello 3.0 | ⚠ atteso scritto prima: `HEVC=non-arriva` (`RCP.md` §4.3 **O12**) — ⛔ **SMENTITO** `[M]` 12 ago 2026: Chrome 151/Linux **non fa rispettare il livello** e dipinge 8/8. L'atteso corrente è `HEVC=arriva`, e la smentita è §5 di questo rapporto |
| `f25-10bit` | `python3 banchi/02-pagina-sequenze.py` | la coppia lossless esce con **220** livelli (8 bit promossi) e **573** (10 bit veri), e le due stringhe di codec Main10 e Main sono **diverse** | costruire il pattern in `rgb24` invece che in `rgb48le` | ⛔ le due sequenze escono **entrambe a 220 livelli**: il flusso «a 10 bit veri» non li contiene, e la domanda sui 10 bit non è più ponibile |
| `f25-intero` | `bash banchi/02-pagina-certifica.sh` | sano → 5 guasti → risanato, tutte le pretese onorate, uscita **0** | — | — |

---

## Il giudizio dell'utente

⏳ **Non ancora dato.** ⛔ E c'è una cosa precisa da fargli guardare, che nessun numero di questo
rapporto può sostituire: **la striscia di sfumatura in fondo al pattern**, dipinta dal flusso Main10
e da quello Main, una accanto all'altra. È la sola prova sui 10 bit che questo lato del progetto può
produrre (`LEZIONI.md` §2.4, `STUDI.md` §web §1.2 A), e i PNG sono già su disco.

---

## I file di questa sotto-fase

| File | Righe **vere**, contate il 12 ago 2026 | Che cosa fa |
|---|---|---|
| `banchi/02-pagina-sequenze.py` | **1219** | costruisce le **19 sequenze** note con `libx265`: 2 pattern × (Main10, Main) × (Annex-B, hvcC), la coppia **lossless a 10 bit veri / 8 bit promossi**, le **3 di AV1** (il ripiego) e 2 di controllo **VP9**. Legge profilo e livello **dal flusso**, conta i livelli veri, e scrive i 28 byte di `RCP.md` §6.2 |
| `banchi/02-pagina-prova.html` | **1131** | ⭐ **la pagina di prova**: decodifica, dipinge, **rilegge i pixel**, classifica, e li porta fuori. Non è il prodotto |
| `banchi/02-pagina-raccogli.py` | **169** | serve la pagina sulla **7515**, registra gli esiti e scrive i **PNG dei pixel** |
| `banchi/02-pagina-verdetto.py` | **482** | ⛔ calcola il verdetto **fuori dal browser**, e tiene separate le due domande: «il banco funziona?» e «HEVC arriva al pixel?» |
| `banchi/02-pagina-lancia.sh` | **374** | guida Chrome e Firefox su schermo finto o vero, con i denominatori |
| `banchi/02-pagina-certifica.sh` | **210** | sano → 5 guasti → risanato, con gli attesi scritti prima |
| `banchi/02-pagina-esiti.jsonl` | — | il registro, una riga per prova |
| `banchi/02-pagina-pixel/` | — | ⭐ i PNG dei pixel dipinti: **la consegna a F2.6** |

---

# ⭐ Aggiunta del 12 agosto 2026 — AV1 come **ripiego negoziato**

*F2.5 riaperta dal coordinatore per **una misura sola**. La ragione: l'utente ha deciso HEVC **con un
ripiego negoziato**, invece di dichiarare un requisito «Chrome con VA-API» — e la decisione è
inciampata nel protocollo.*

## ⛔ Perché AV1 e non il VP9 che questo banco aveva già in mano

Il VP9 di questo banco era il candidato naturale: **8 celle su 8 in tutte e quattro le caselle**, ed
era già lì come controllo positivo. ⛔ Ma è **`RCP.md` a decidere**, non la comodità del banco:

| | |
|---|---|
| `RCP.md` §4.3 | i valori ammessi di `video.codec` in RCP/1 sono **`hevc` e `av1`** |
| ⛔ e `vp9` compare **come esempio del contrario** | è il valore canonico che un'implementazione RCP/1 **deve ignorare**: *«un `video.codec` che vale `hevc,vp9` si legge come `hevc`»* |
| `RCP.md` §9 | la finestra dei valori nuovi è **chiusa dal 10 agosto** |
| `RCP.md` §6.2 | AV1 ha **già il suo `codec = 2`** nell'intestazione del fotogramma |

⇒ **VP9 in RCP/1 vorrebbe dire aprire RCP/2 o dichiarare un'eccezione a §9. AV1 non costa niente.**
⇒ La domanda da misurare non era più «quale codec regge», ma **«AV1 regge?»**.

> ⚠ **E `STUDI.md` §web O2 diceva che AV1 è «un vicolo cieco da entrambi i lati»** — il nostro ferro non lo
> codifica in hardware `[M]`, e in decodifica non aggiunge niente che HEVC non dia. ⛔ Quella riga
> vale per il codec **principale**, e resta vera. Qui si misura **il ramo che non era stato
> percorso**: non «AV1 al posto di HEVC», ma **«AV1 dove HEVC non c'è»**. Un vicolo cieco resta tale
> finché nessuno guarda l'altro ramo.

## Le quattro caselle — ⭐ AV1 arriva al pixel **dappertutto**

`[M]` 12 agosto 2026. Giri: `f25-chrome-1786539457` e `f25-firefox-1786539464` (schermo vero `:10`),
`f25-chrome-1786539477` e `f25-firefox-1786539480` (Xvfb `:75`).
⛔ **In tutti e quattro i giri i sei controlli del banco sono verdi**: i numeri qui sotto sono stati
prodotti da un banco valido.

| Sequenza | Chrome 151 vero `:10` | Firefox 140 ESR vero `:10` | Chrome Xvfb | Firefox Xvfb |
|---|---|---|---|---|
| **AV1 8 bit** (`av01.0.04M.08`) | ⭐ **8/8** | ⭐ **8/8** | ⭐ **8/8** | ⭐ **8/8** |
| **AV1 10 bit** (`av01.0.04M.10`) | ⭐ **8/8** | ⭐ **8/8** | ⭐ **8/8** | ⭐ **8/8** |
| *(per confronto)* HEVC Main10 | 8/8 | ⛔ zero | ⛔ zero | ⛔ zero |
| *(controllo)* VP9 | 8/8 | 8/8 | 8/8 | 8/8 |

⭐ **AV1 riempie esattamente le tre caselle che HEVC lascia vuote.** È la sola riga che serviva.

## ⭐ Regge in software — ed è la domanda che aveva smascherato HEVC

⛔ *Un ripiego che esiste solo con la GPU non è un ripiego*, perché mancherebbe esattamente dove
serve. È la prova che su HEVC aveva rivelato la dipendenza da VA-API.

| `hardwareAcceleration` | Chrome vero | Firefox vero | Chrome Xvfb | Firefox Xvfb |
|---|---|---|---|---|
| `no-preference` | 8/8 | 8/8 | 8/8 | 8/8 |
| ⭐ **`prefer-software`** | ⭐ **8/8** | ⭐ **8/8** | ⭐ **8/8** | ⭐ **8/8** |
| `prefer-hardware` | ⛔ zero | 8/8 | ⛔ zero | 8/8 |

⭐ **`prefer-software` dipinge 8/8 in tutte e quattro le caselle, a 8 bit e a 10 bit.** AV1 non
dipende dalla GPU: **è un ripiego vero.**

⚠ **E il `prefer-hardware` va letto al contrario di come sembra.** `vainfo` su questa macchina non
elenca **nessun** entrypoint di decodifica AV1 `[M]` — c'è solo `av1_vaapi` in *codifica*. Quindi
**Chrome ha ragione a rifiutare**: dice la verità, non c'è un decodificatore AV1 hardware.
⛔ **Firefox invece accetta `prefer-hardware` e dipinge**, sulla stessa macchina. `[?]` **Delle due
l'una**: o Firefox ha una strada hardware che VA-API non dichiara, o **ignora il suggerimento e
ripiega in software senza dirlo** — che è la forma **E2**, un componente che decide da sé. ⚠ Non è
misurato quale delle due, e non va scritto come se lo fosse.

## ⭐⭐ I 10 bit: AV1 li conserva, **e sono osservabili** — il caso positivo che mancava

`[M]` 12 agosto 2026, Chrome 151, flusso `A-av1-10bitvero` (sorgente a **10 bit veri**, 640 livelli):

| Che cosa | AV1 8 bit | ⭐ AV1 10 bit |
|---|---|---|
| `VideoFrame.format` | `I420` | ⭐ **`I420P10`** |
| `copyTo()` | 460 800 byte, 3 piani | ⭐ **921 600 byte**, 3 piani — cioè campioni a **16 bit** |
| massimo del luma | — | ⭐ **870** |

⛔ **870 è la prova, e non è un'opinione: a 8 bit un campione non può superare 255.** I 10 bit
arrivano al fotogramma **e si vedono da JavaScript**.

⭐ **È il caso positivo che la tabella del «caso opposto» di §6 non aveva mai potuto riempire.** Su
HEVC in hardware il formato era `BGRA` e la domanda restava senza risposta; qui il formato è
`I420P10`, e la stessa domanda ha **risposta sì**. ⇒ La riga *«dal browser i 10 bit non sono
leggibili»* di `STUDI.md` §web §1.2 A **non vale per AV1 su Chrome**: lì lo sono.

⚠ **Su Firefox no**: il formato è `BGRX` a 1 228 800 byte in un piano solo, per **tutte** le
sequenze. I 10 bit **arrivano** (la sfumatura dipinta ha 210 livelli distinti) ma **non sono
osservabili**. ⇒ La domanda dei 10 bit ha risposta **motore per motore**, non una volta sola.

## Le stringhe esatte, composte dai numeri letti nel flusso

⛔ Come per HEVC: `ffprobe` legge profilo e livello **dal flusso appena prodotto**, e la stringa si
compone da lì.

| | |
|---|---|
| **8 bit** | **`av01.0.04M.08`** |
| ⭐ **10 bit** | **`av01.0.04M.10`** |
| forma | `av01.<profilo>.<seq_level_idx a 2 cifre><tier>.<profondità a 2 cifre>` |
| letti nel flusso | profilo `Main` ⇒ **0** · livello **4** · tier `M` (main) |

⚠ **`seq_level_idx = 4` non è «livello 4»: è il livello 3.0.** Nella stringa va **l'indice**, non il
livello in chiaro — ed è il tipo di campo su cui si sbaglia in silenzio. ⭐ Tutt'e due le stringhe
sono accettate e dipingono su **tutti e quattro** i giri; nessuna delle alternative di riserva
(`av01.0.08M.*`, `av01.0.00M.*`) è servita.

⛔ **Nessuna `description`**: AV1 in WebCodecs prende le unità temporali di OBU così come sono. ⇒ Per
il ripiego **non esiste** la coppia hvcC/Annex-B che complica HEVC — una cucitura in meno con F2.3.

## Il controllo positivo e negativo, come nel giro di prima

⛔ Senza, un «no» su AV1 non si distinguerebbe da un banco che ha smesso di funzionare.

| | |
|---|---|
| **P1** il lettore dice sì · **P2** dice no · **P3** distingue · **P4** VP9 arriva · **P5** dipinge quel che ha chiesto · **P6** gli zeri hanno una causa | ⭐ **verdi in tutti e quattro i giri** |
| **il controllo negativo su AV1 stesso** | `av1-B-8bit` — il pattern **B** in AV1: dipinge **8/8 sul suo pattern**, e `contro_pattern` non lo confonde con A. ⇒ il banco non sta dicendo «8/8» a prescindere |
| **e il rosso che c'è nello stesso giro** | HEVC su Firefox e su Xvfb resta a **zero**, nello **stesso registro e nello stesso giro**. ⛔ Un banco che dicesse 8/8 a tutto non potrebbe produrre quei tre zeri |

⭐ Quest'ultima riga è la più forte: **il verde su AV1 e il rosso su HEVC convivono nello stesso giro,
sullo stesso motore, con lo stesso codice di misura.**

## Che cosa questo cambia, e che cosa no

| | |
|---|---|
| ⭐ **AV1 regge come ripiego** | quattro caselle su quattro, a 8 **e** a 10 bit, **in software**. Non serve RCP/2, non serve un'eccezione a §9: `av1` è già normativo in §4.3 e ha già `codec = 2` in §6.2 |
| ⭐ **e non perde i 10 bit** | anzi, su Chrome è **l'unico** percorso di questo banco in cui i 10 bit si vedono da JavaScript |
| ⚠ **il prezzo non è misurato qui** | ⛔ questo giro dice **che** AV1 arriva al pixel, **non a che ritmo**. `STUDI.md` §web O2 e `DECISIONI.md` restano in piedi su tutto il resto: la codifica AV1 sul nostro ferro è **software** `[M]` 9 ago, e a 4K60 il costo non è stato misurato da nessuno |
| ⛔ **e la scala di preferenza non si rovescia** | `hevc,av1` resta l'ordine: HEVC dove c'è, AV1 dove HEVC non c'è. Questa misura riempie il **secondo** posto, non il primo |

## Le `[?]` che questa aggiunta lascia aperte

| | |
|---|---|
| `[?]` **il ritmo di AV1 in software** | a 640×480 su 6 fotogrammi non si misura niente di utile. Il costo a 1080p e a 4K è **da misurare**, ed è la domanda che decide se il ripiego è usabile o solo esistente |
| `[?]` **perché Firefox accetta `prefer-hardware`** | strada hardware non dichiarata da VA-API, oppure ripiego silenzioso (**E2**). Non misurato |
| `[?]` **AV1 su Chrome per Android e DeX** | ⛔ non misurato: manca il dispositivo. Vale la forma **E10** — «il Chrome del portatile lo fa» non dice niente del Chrome del telefono |
| `[?]` **AV1 su Safari** | nessun dispositivo Apple |
| `[?]` **il costo in banda** | a parità di qualità AV1 e HEVC non sono lo stesso flusso, e nessuno ha confrontato i due sul nostro contenuto |

## La riga per il catalogo

| nome | comando | atteso sano | guasto da innestare | atteso guasto |
|---|---|---|---|---|
| `f25-av1` | `SCHERMO=:10 SCHERMO_VERO=1 MOTORI="chrome firefox" bash banchi/02-pagina-lancia.sh` | `A-av1-8bit`, `A-av1-10bitvero` e `av1-*-prefer-software` a **8/8 celle** su tutti e quattro i giri, con P1..P6 verdi | `GUASTO=scambio` | ⛔ **P5 rosso**, e `A-av1-8bit` scende a **0/8 sul suo pattern e 8/8 sull'altro** `[M]` — il banco distingue anche su AV1, non solo su HEVC e VP9. ⚠ `A-av1-10bitvero` **non ha gemello** e lo dichiara (`scambio: NON APPLICABILE`) |

> ### ⛔⭐ E questa riga ha trovato un difetto **mentre veniva verificata**, il 12 agosto
>
> L'avevo scritta come atteso e sono andato a **provarla** invece di lasciarla scritta. Il guasto
> `scambio` cercava il pattern gemello con `carica()` **senza protezione**: le sequenze che il
> gemello non ce l'hanno — le `*-lossless-*`, `A-10bitvero-*`, `A-av1-10bitvero` — facevano lanciare
> l'eccezione, che saliva fino a `giro()` e **chiudeva la corsa a metà**. ⛔ Le sequenze **AV1, che
> vengono dopo, non venivano eseguite affatto**.
>
> ⚠ **E la certificazione passava lo stesso**, perché P5 virava al rosso sulle prime otto sequenze.
> Un guasto che vira per la ragione giusta su metà della corsa e ferma l'altra metà **non ha
> certificato quel che credevo**: è `LEZIONI.md` §1.3 un piano più in su — non «il banco non
> riproduce il difetto», ma «il banco riproduce il difetto **su un campione che non è quello che
> credo**».
>
> ⭐ Curato: il gemello mancante si **dichiara** nel campo `scambio` e si prosegue. Dopo la cura il
> giro arriva in fondo (`FINITO: COMPLETO`, **29 prove**) e le sequenze AV1 virano davvero.
