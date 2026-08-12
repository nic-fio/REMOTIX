# P2.5 — Il PRODOTTO del quinto anello: la pagina che dipinge il fotogramma

*Scritto il 12 agosto 2026. Mandato: il quinto anello della fase 2, il prodotto.
Il banco di F2.5 sta in [`F2-5-pagina.md`](F2-5-pagina.md); ⛔ **questo giro ha scritto
`src/pagina.html`**, cioè la pagina che l'utente apre.*

> ⭐ **Che cosa è cambiato, in una riga**: `src/pagina.html` non fa più solo la stretta di mano.
> Riceve gli stream video di `RCP.md` §6.2, applica le regole di §5.2 e §6.2, decodifica e
> **dipinge**. E prima di dire al server quale codec sa parlare, **lo prova sul pixel**.

---

## 1. ⛔ Come la pagina sceglie il codec — e perché non lo chiede alle API

### Il fatto che ha deciso la forma

`[M]` 12 agosto 2026, Firefox 140 ESR, su **tutte e sette** le stringhe HEVC (F2.5 §2):

| Chi risponde | Che cosa dice |
|---|---|
| `navigator.mediaCapabilities.decodingInfo()` | `supported` · `smooth` · **`powerEfficient: true`** |
| `video.canPlayType()` | **«probably»** |
| `VideoDecoder.isConfigSupported()` | ⛔ **false** |
| **il pixel** | ⛔ **niente**: `NotSupportedError` a `configure()` |

⇒ ⛔ **Una pagina che scegliesse il codec da `mediaCapabilities` — l'API fatta apposta per quella
domanda — sceglierebbe HEVC su Firefox e non dipingerebbe niente.** In `src/pagina.html`
`mediaCapabilities` e `canPlayType` **non vengono chiamate affatto**: non esiste nessun ramo del file
in cui la loro risposta possa cambiare qualcosa.

### La scelta, in tre tempi

| | |
|---|---|
| **1. il filtro** | `VideoDecoder.isConfigSupported()`. ⛔ Si usa **come filtro, non come verdetto**: quando dice no il pixel non arriva mai (`[M]`, quattro caselle su quattro); quando dice sì **non dice niente** — è la forma **E1**, e `[M]` Chrome accetta `L30` su un flusso di livello 3.0 |
| **2. il pixel** | ⭐ **quattro sonde vivono dentro la pagina**: un fotogramma chiave di 64×48 per codec e per profondità (HEVC 8/10, AV1 8/10). La pagina le decodifica, le dipinge su una tela sua e **rilegge i pixel**. ⛔ Le sonde hanno **due tinte**, metà e metà, e la tela si riempie prima di magenta: con una tinta sola *«ha dipinto»* e *«la tela era già di quel colore»* avrebbero lo stesso aspetto. **1,2 KB in tutto** (114 e 49 byte per flusso) |
| **3. il `CIAO`** | in `video.codec` finiscono **solo i codec che hanno dipinto su questo browser**, nell'ordine `hevc,av1` — ⛔ la scala **non si rovescia** (`DECISIONI.md` §1.13). In `video.profondita` solo le profondità che hanno dipinto |

⭐ **E la stringa che la sonda ha visto dipingere è quella che la sessione userà.** Non se ne compone
un'altra a mano: le stringhe sono una **scala** — prima quella col livello dichiarato da questa
pagina (`hev1.2.4.L153.B0`, `av01.0.13M.10`), poi un ripiego a livello basso — e la sonda dice quale
ha dipinto. ⚠ `seq_level_idx` **non è il livello: è l'indice**, e il conto sta accanto alla tabella
invece che dentro una costante.

⛔ **La `description` non si manda mai**, né per HEVC né per AV1: Annex-B puro
(`fasi/02-primo-fotogramma.md` D1, confermato dal pixel in F2.5 §3).

⚠ **Il sondaggio parte al caricamento della pagina, non alla connessione**: costa qualche decina di
millisecondi dove funziona e fino a dieci secondi dove tutto viene rifiutato con un tempo scaduto.
Quando l'utente preme «Collegati» la risposta c'è già.

### ⛔ E che cosa fa quando **nessuno dei due** arriva al pixel

| | |
|---|---|
| ⛔ **`video.codec` non si manda vuota: si OMETTE** | §4.3: *«un valore vuoto è `ERRORE_PROTOCOLLO`: chi non ha niente da dire non manda la capacità»*. E l'omissione **si scrive nel registro**: una capacità sparita in silenzio e una mai avuta hanno lo stesso aspetto dal lato che riceve |
| **il server congeda con `NIENTE_IN_COMUNE`** | è quel che §4.3 gli **impone** quando l'intersezione di `video.codec` è vuota. ⭐ Non serve nessuna riga nuova di protocollo |
| ⭐ **la frase la scrive la pagina, PRIMA che il server risponda** | *«nessun codec in comune»* non nomina né il browser né la scheda grafica. La causa la sa solo chi ha appena provato a dipingere, e il riquadro la dice: *«Su Linux il decodificatore HEVC di Chrome è quello della scheda grafica, e senza scheda grafica non c'è; Firefox non fa HEVC affatto»* |
| ⚠ **e la parola d'ordine non parte** | il congedo arriva subito dopo il `CIAO`, cioè **due messaggi prima** delle `CREDENZIALI` |
| **il caso simmetrico** | se il server sceglie un codec che questa pagina non dipinge, è **la pagina** a congedare con `NIENTE_IN_COMUNE` (0x09) |

⚠ **Un server che non dichiara `video.codec` affatto non è un server che sbaglia** — alla fase 1 non
ne aveva. Lì la pagina **non congeda**: scrive *«questa sessione non ha video»* e uno stream `0x03`
che arrivasse sarebbe `ERRORE_PROTOCOLLO`. Senza questa distinzione la cura avrebbe rotto la fase 1.

---

## 2. Come dichiara la degradazione — `CODER.md` §4.2

Due posti, e dicono cose diverse:

| Dove | Che cosa |
|---|---|
| **il riquadro `#dichiarazione`**, per l'utente | *«Questo browser non decodifica HEVC: si usa AV1, che è il ripiego previsto. L'immagine c'è; il consumo di banda a parità di qualità può essere diverso.»* — e la variante per quando **non c'è nessun codec**, e quella per quando il server sceglie AV1 su un browser che HEVC ce l'ha. ⚠ Si nasconde da solo quando è vuoto: un riquadro sempre presente e quasi sempre vuoto smette di essere letto |
| **il registro visibile**, per chi diagnostica | una riga per codec e per profondità: `isConfigSupported` di ogni stringa provata, quale ha dipinto, `VideoFrame.format`, e il testo esatto dell'errore quando non dipinge |

⭐ **E il registro dichiara anche quel che NON sa.** Se il decodificatore sia hardware o software **da
JavaScript non è osservabile** (`web.md` §4.1: il dato esiste dentro Chromium, `IsPlatformDecoder()`,
e non compare in nessuna interfaccia). ⛔ Scrivere *«software»* perché `powerEfficient` è falso
sarebbe **inventare**: `[M]` quello stesso campo risponde `true` su Firefox per un codec che il
browser non decodifica affatto. ⇒ La pagina registra `VideoFrame.format` **e non lo interpreta**:
`[M]` `I420`/`I420P10` su Chrome, `BGRX` su Firefox per tutto — la domanda dei 10 bit ha risposta
**motore per motore**.

**Ogni degradazione del percorso video scrive una riga**: un fotogramma tollerato a una misura
vecchia, uno scartato per ordine, uno trattenuto, un buco, una `RICHIEDI_CHIAVE`, una
riconfigurazione. ⛔ È l'invariante **I1** letta da `REVIEWER.md` §3: *«ogni degradazione che avvenga
senza una riga nel registro: una discesa silenziosa e una decisa hanno lo stesso aspetto»*.

---

## 3. L'esito dei due banchi **contro la pagina del prodotto**

### ⚠ La scena, dichiarata — ed è una scelta

⛔ **Xvfb, uno schermo FINTO su un display mio** (`:81`, `:82`, `:84`), **mai il display che l'utente
sta usando** (`CODER.md` §3.2). Ogni riga del registro e ogni riga di esito la porta per esteso
(`xvfb-FINTO-:81-1280x1024`), e tutto quel che si apre si chiude.

⛔ **Il prezzo si dichiara**: su Xvfb non c'è GPU, e su Linux il decodificatore HEVC di Chrome è
quello della **piattaforma** (VA-API). ⇒ Su questa scena **HEVC non arriva al pixel**, ed è
**misurato**, non un difetto del prodotto. Il percorso intero lo prova **AV1**, che `[M]` arriva in
tutte e quattro le caselle *con GPU e senza* — ed è esattamente la ragione per cui AV1 è il ripiego
negoziato.

### Banco 1 — i flussi noti (`BERSAGLIO=prodotto bash banchi/02-pagina-lancia.sh`)

`[M]` 12 agosto 2026, Chrome 151 e Firefox 140 ESR, **banco valido su tutti e due**:

| | Chrome 151 | Firefox 140 ESR |
|---|---|---|
| **AV1 8 bit** (A e B) | ⭐ **8/8** e **8/8** | ⭐ **8/8** e **8/8** |
| **AV1 10 bit veri** | ⭐ **8/8**, `format` = **`I420P10`** | ⭐ **8/8**, `format` = `BGRX` |
| **HEVC** (Main, Main10, 10 bit veri) | ⛔ zero — `OperationError: Unsupported configuration` | ⛔ zero — `NotSupportedError` |
| **P1 · P2 · P3 · P4 · P5 · P6** | verdi | verdi |
| ⭐ **P9** *(nuovo)* | verde | verde |
| **l'intestazione di §6.2** | 30 pezzi, **0 in disaccordo** | 30 pezzi, **0 in disaccordo** |

⭐ **P9 è il controllo che mancava**, e non è un doppione di P4: P4 dice *«questo **motore** porta un
video fino al pixel»* e lo dice decodificando VP9 **nella pagina del banco** — perché `RCP.md` §4.3
porta `vp9` come l'esempio canonico di valore che RCP/1 **deve ignorare**, e il prodotto non lo sa
fare *per decisione*. ⛔ Con P4 verde e HEVC a zero, *«HEVC non arriva su questo motore»* e *«la
catena del **prodotto** non funziona»* avevano ancora lo stesso aspetto. **P9 = AV1 attraverso
`REMOTIX.schermo`**: intestazione di §6.2, regole di §5.2, `VideoDecoder` e tela del prodotto.

⛔ **Certificato**: `bash banchi/02-pagina-prodotto-certifica.sh` — **sano → 4 guasti → risanato,
tutte le pretese onorate**, uscita 0. I guasti: `pixel` (P4 e P9 rossi, **P1 e P2 verdi**),
`lettore` (P2 e P3 rossi), `scambio` (P5 rosso), `muto` (P6 rosso).

### Banco 2 — il cambio di tela (`BERSAGLIO=prodotto bash banchi/02-pagina-tela-lancia.sh`)

⛔ **Misura una cosa diversa da `02-pagina-tela-prova.html`**: quello misura *che cosa fa un
`VideoDecoder`* quando la tela cambia; questo misura **se il prodotto applica le regole**, che sono
del **client** e non del codec. Quindici casi per codec, con l'**atteso scritto prima** in ogni riga
e ⛔ il confronto fatto da un programma **fuori dal browser**.

`[M]` 12 agosto 2026, Chrome e Firefox: **0 casi diversi dall'atteso su 38 eseguiti**, 18 saltati e
dichiarati (i casi HEVC che vogliono un decodificatore vivo: su questa scena non si possono porre).

| Caso | Che regola | Esito |
|---|---|---|
| **T1** | il controllo positivo: chiave + 5 delta alla tela in vigore | ⭐ 8/8 celle |
| **T2** | ⭐ i fotogrammi **in volo** alla misura vecchia sono **accettati e dipinti**, con la riga nel registro (§6.2) | 2 tollerati, 3 dipinti |
| **T3** | ⭐ **il decodificatore si riconfigura sulla prima CHIAVE alla misura nuova, non sul `TELA`** (§5.2, P10) | dopo il `TELA` è ancora a 640×480; dopo la chiave, 320×240, 8/8 |
| **T4** | la tolleranza **finisce** sulla prima chiave alla misura nuova: da lì una misura vecchia è `ERRORE_PROTOCOLLO` | rifiutato, e **dice perché** |
| ⭐ **T5** | ⛔ **l'ordine si applica PRIMA della misura** (§6.2, P14): la chiave grossa alla misura vecchia arriva dopo, col `numero` precedente ⇒ **si scarta per ordine**, e la misura non si guarda nemmeno | 1 scartato per ordine, **0 errori di protocollo** |
| **T7** | ⭐ una misura **mai annunciata** viene **trattenuta**, non uccisa — vedi §5 | 1 trattenuto, poi consegnato al `TELA`, 8/8 |
| **T8** | e la tolleranza ha un fondo: **nove** fotogrammi a una misura mai annunciata chiudono | `ERRORE_PROTOCOLLO` |
| **T9** | uno stream **azzerato** (`RESET_STREAM`) **non si consegna** al decodificatore, ed è un buco (§6.2, forma E8) | 1 azzerato, 1 buco, 1 chiave chiesta |
| **T10** | `FIN` prima dei 28 byte: non è un fotogramma corto, è una lunghezza che non torna | `ERRORE_PROTOCOLLO` |
| **T11** | un **buco** nei `numero`: si chiede una chiave, e fino alla chiave i delta **non si consegnano** (§5.2) | 1 buco, **1** chiave chiesta |
| **T12** | uno stream video **prima di `SESSIONE`** (§2.5, invariante **I3** sul filo) | `ERRORE_PROTOCOLLO` |
| **T13 · T14 · T15** | codec non negoziato · `numero = 0` riservato · `tipo` sconosciuto | `ERRORE_PROTOCOLLO`, ciascuno con la sua frase |

⛔ **Certificato**: `bash banchi/02-pagina-tela-prodotto-certifica.sh` — **sano → 4 guasti →
risanato**, uscita 0. Il guasto `ordine` (in T5 il numero è **maggiore** invece che minore) è quello
che conta: ⭐ **senza, «l'ordine si applica prima della misura» sarebbe verde anche in un prodotto
che guarda solo la misura**, perché il fotogramma verrebbe rifiutato lo stesso — per la ragione
sbagliata.

### Banco 3 — ⭐ e la fase 1 **non è regredita**, contro un server vero

⛔ Una pagina che dipinge e non fa più la stretta di mano non è un anello in più: è un anello rotto.
⇒ Il giro di **P5** è stato rifatto per intero **contro una copia bersaglio mia** — porta **7551**,
prefisso `p25-7551`, cartella `/srv/src/02-p25-copia` — con la pagina nuova accanto al binario, il
browser su CHUWI (Xvfb `:83`) e il server su NIC-OS: **il filo attraversato davvero**.

`[M]` 12 agosto 2026, `p5-20260812-205240-20906`:

| | Chrome 151 | Firefox 140 ESR |
|---|---|---|
| `n2-parola-sbagliata` | ⭐ **CONFORME** — 13 controlli, **0 guasti** | ⭐ **CONFORME** — 13 controlli, **0 guasti** |
| `p-sessione` | ⭐ **CONFORME** — 17 controlli, **0 guasti** | ⭐ **CONFORME** — 17 controlli, **0 guasti** |
| il congedo alla chiusura della scheda | **tutt'e due le strade** (§3.1) | **tutt'e due le strade** |
| il posto | preso e **lasciato** | preso e **lasciato** |
| verdetto per motore | **CONFORME** | **CONFORME** |

⭐⭐ **E il registro del server porta la prova che la scelta del codec arriva sul filo**: nei tre
tratti che usano la pagina del prodotto il server scrive

```
rcp     negoziato video.codec=av1 video.profondita=8 audio.codec=opus
```

⛔ **`av1`, non `hevc,av1`** — perché il browser girava su uno **schermo finto senza GPU**, la sonda
ha misurato che HEVC non arriva al pixel, e la pagina **non l'ha dichiarato**. ⚠ *(La quarta riga del
log dice `hevc`: è il tratto `N1`, che serve `01-b2-sonda.html` dal banco e non la pagina del
prodotto.)* ⇒ La catena *sonda → `CIAO` → scelta del server* è misurata **da capo a fondo**, e il
ripiego negoziato di `DECISIONI.md` §1.13 non è un'intenzione: è quel che il server ha scritto.

⛔ **Il bersaglio è stato spento a fine giro**, e **7448 e 7501 contate prima e dopo**: quattro
ascoltatori, gli stessi. Il prodotto di casa non è stato toccato.

---

## 4. ⛔⭐ Quattro difetti del prodotto trovati **girando**, non rileggendo

Tutti e quattro sono usciti dal banco del cambio di tela alla sua prima esecuzione, e ciascuno è
nel codice con la data accanto.

| # | Il difetto | Come si sarebbe visto |
|---|---|---|
| **1** | ⛔ **Una misura VECCHIA arrivata dopo che la tolleranza si era chiusa finiva nello stesso ramo di una misura MAI ANNUNCIATA**: veniva *trattenuta* invece di chiudere la sessione, e §6.2 dice il contrario | un server che sbaglia la misura **non veniva mai fermato**. Curato con l'insieme delle tele **storiche**: già stata in vigore ⇒ `ERRORE_PROTOCOLLO`; mai in vigore ⇒ si trattiene (caso T4) |
| **2** | ⛔ **Con un buco aperto, ogni delta successivo ne dichiarava un altro** e faceva partire una `RICHIEDI_CHIAVE` per fotogramma | è **la spirale che §5.2 descrive** — *«durante una raffica di perdite le richieste arrivano a decine, e ogni chiave costa dieci volte un delta»*. ⚠ Il server ha il suo smorzatore (200 ms), ma appoggiarsi allo smorzatore dell'altro lato è chiedere all'altro di curare un difetto nostro (caso T11) |
| **3** | ⛔ **Un `VideoDecoder` chiuso da un errore veniva riconfigurato lo stesso**, e ogni `configure()` lanciava `InvalidStateError` | il **primo** errore del decodificatore rendeva la sessione irrecuperabile **in silenzio**: la chiave chiesta a §5.2 arrivava e non poteva più essere consegnata, e il sintomo era *«lo schermo si è fermato e nessuno dice perché»* |
| **4** | ⚠ *(del banco, non del prodotto)* **`A-8bit-annexb` usciva a 8 celle su 8 senza aver dipinto niente**: la tela portava ancora l'immagine del controllo precedente | *«ha dipinto»* e *«la tela era rimasta come prima»* avevano lo stesso aspetto — la forma **E8** dentro il banco. Curato pulendo la tela di magenta prima di ogni sequenza |

> ⭐ **E un quinto, trovato dalla certificazione e non dalla misura.** Il guasto `pixel` sul banco del
> cambio di tela **non faceva virare niente**: gli attesi di T1, T3 e T7 contavano fotogrammi e
> riconfigurazioni e **non guardavano `celle_giuste`**. ⇒ Il *«controllo positivo del percorso
> video»* non guardava il video, e un prodotto che avesse dipinto spazzatura sarebbe passato per T1.
> È `LEZIONI.md` §1.3 nel verso in cui serve.

---

## 5. ⛔⛔ Una regola del cambio di tela che **non regge**, e va portata al coordinatore

*Il mandato chiedeva di fermarsi e scriverlo. È una sola, ed è la stessa famiglia di
**P11 → P13 → P14**, un passo più in là.*

### La riga

`RCP.md` §6.2, campo `largh./altezza`: *«in RCP/1 DEVONO valere la tela in vigore […] e chi ne
riceve altre chiude con `ERRORE_PROTOCOLLO`»*, con la tolleranza che segue scritta **solo per le
misure vecchie** — quelle in volo quando il `TELA` è partito.

### Il caso concreto che non copre

⛔ **Il `TELA` viaggia sul canale di controllo e il fotogramma su uno stream unidirezionale suo: sono
due stream QUIC indipendenti, e niente ne ordina la consegna.** Un fotogramma alla misura **nuova**
può quindi arrivare **prima** del `TELA` che la annuncia — basta un pacchetto perso sul canale di
controllo, o un fotogramma piccolo che passa avanti.

Applicando §6.2 alla lettera, il client **chiude una sessione in cui nessuno ha sbagliato**:

- il server ha risposto ad `ADATTA_TELA` con `TELA(ADATTATA)`, come §7.1 gli **impone**;
- il server ha aperto lo stream del primo fotogramma alla misura nuova, ed è una **chiave vera**,
  come §5.2 gli **impone**;
- il client riceve una misura che non è la tela in vigore e non è fra le tollerate ⇒
  `ERRORE_PROTOCOLLO`.

⚠ **È esattamente il ragionamento di P13**: *«non è solo una sessione sana che cade, è l'invariante
I1 — mai a staccare — rotta perché la linea è lenta»*. Qui non è la linea lenta: è **l'ordine fra due
stream**, che QUIC non promette e che §5.1 fa apposta a non promettere.

⭐ **E la simmetria è visibile nel documento stesso**: §7.1 dà al **server** una tolleranza per le
coordinate di input in volo sulla tela precedente, «perché il cambio di tela è l'unico momento in cui
i due lati hanno legittimamente due verità diverse». §6.2 dà al **client** la tolleranza per le
misure *vecchie*. ⛔ **Nessuna delle due copre il verso «la misura nuova arriva prima del suo
annuncio».**

### Che cosa ho fatto, in attesa che il coordinatore decida

⛔ **Il prodotto non chiude: trattiene.** Un fotogramma a una misura **mai stata in vigore** viene
messo da parte; se il `TELA` che la annuncia arriva subito dopo, viene consegnato e dipinto (caso
T7 del banco, `[M]` 8/8 celle). ⛔ E la tolleranza ha un fondo che è un **fatto osservabile e non un
orologio** — la lezione di P13: **otto fotogrammi**. Più di così non è più una corsa fra due stream,
è un server che manda una misura che non ha mai annunciato, e lì §6.2 ha ragione (caso T8).

⚠ **`RCP.md` non l'ho toccato** (il mandato lo vieta). La riga proposta, se serve:

> ⛔ Un fotogramma la cui misura **non è mai stata in vigore** non è `ERRORE_PROTOCOLLO` **subito**:
> il client lo trattiene, perché il `TELA` che la annuncia può essere ancora in volo su un altro
> stream. Diventa `ERRORE_PROTOCOLLO` quando i fotogrammi trattenuti superano **otto**.

### E due che invece **reggono**, e vanno dette perché sembravano contraddirsi

| | |
|---|---|
| ⭐ **«riconfigura sulla CHIAVE, non sul `TELA`» e «accetta e dipingi i fotogrammi in volo»** | ⛔ **si tengono insieme solo grazie alla prima**: finché non arriva la chiave il decodificatore è ancora configurato alla misura vecchia, quindi i fotogrammi in volo **sono** alla misura per cui è configurato e si dipingono senza nessuna eccezione. Riconfigurando sul `TELA` le due righe comanderebbero il contrario sullo stesso fotogramma. È quel che dice P10, misurato dal prodotto |
| ⭐ **«scarta per ordine prima di guardare la misura»** | regge, e ⛔ **è quel che salva la chiave vecchia in volo**: il suo `numero` è precedente, quindi si scarta per ordine e la misura non si guarda. Senza la precedenza, la regola della misura la ucciderebbe (caso T5) |

### ⚠ E una cosa che `RCP.md` **non dice**, e che ho dovuto decidere

§5.2 impone al client di mandare `RICHIEDI_CHIAVE` *«quando si accorge di un buco»*, e §6.2 dice che
i fotogrammi **possono arrivare fuori ordine**. ⛔ **Non c'è scritto che cosa vuol dire «accorgersi»**,
e le due righe insieme hanno una lettura sola che regge: un fotogramma che arriva dopo uno più
recente **già consegnato** viene scartato per ordine, quindi non arriverà mai al decodificatore ⇒ un
salto nei `numero` **è** un buco. ⭐ Ma solo perché i fotogrammi **trattenuti non fanno avanzare
`ultimo_consegnato`**: un riordino si ricuce da solo, un buco no. Questa distinzione è nel codice e
non nel documento; se il coordinatore la vuole in `RCP.md`, è una riga.

---

## 6. Le righe che servirebbero in `src/pagina.c` — ⛔ non è mio, e non l'ho toccato

`src/pagina.c:590` legge `pagina.html` **una volta sola all'accensione**. Le tre cose che chiedo a
chi lo possiede:

| # | Che cosa | Perché |
|---|---|---|
| **1** | ⛔ **Nessun tetto sulla lunghezza della pagina sotto i ~128 KB**, o va alzato | `pagina.html` è passata da **34 089** a **90 357** byte. `[M]` il server la serve intera (verificato accendendo una copia bersaglio sulla 7551 e confrontando l'impronta SHA-256: identica al file di `src/`), quindi **oggi non c'è un tetto che morda** — ma è una riga che vale la pena di guardare prima che qualcuno la aggiunga |
| **2** | ⚠ **Le quattro sostituzioni (`__IMPRONTA__`, `__AVVISO__`, `__BANNATO__`, `__RESTANO_MS__`) devono restare quelle**, e nessuna sostituzione nuova | ⛔ I quattro flussi di sonda sono **base64**, e contengono lunghe sequenze di lettere e cifre. Una sostituzione fatta su un testo più corto o meno specifico rischierebbe di colpirli. `[M]` con le quattro attuali non succede: la copia sul server ha la **stessa impronta** del file di `src/`, sostituzioni comprese |
| **3** | ⛔ **La pagina va servita con `Cross-Origin-Opener-Policy: same-origin` e `Cross-Origin-Embedder-Policy: require-corp`** (`SPECIFICHE.md` §11.5, rilievo O11) | è già così, e va detto perché adesso la pagina **non ha nessuna sotto-risorsa**: i flussi di sonda sono dentro il file apposta. ⚠ Se un giorno qualcuno li spostasse in un file a parte, quella intestazione li farebbe sparire |

⚠ **E una riga che NON serve**: non serve nessun percorso nuovo, nessun `--pagina`, nessuna opzione.
La pagina resta un file solo accanto al binario.

---

## 7. Che cosa resta `[?]`

| | |
|---|---|
| ⛔ **HEVC attraverso il prodotto, su una GPU** | ⚠ **non misurato di proposito**: HEVC su Chrome/Linux esiste solo via VA-API, e l'unico schermo con GPU di questa macchina è **il display dell'utente**. `CODER.md` §3.2 e la richiesta del coordinatore dicono di non prenderlo. ⇒ Il percorso del prodotto è misurato **su AV1**, e la catena è la stessa: intestazione, regole, `VideoDecoder`, tela. ⭐ Il giorno in cui si vuole il numero, è **un giro solo** con `SCHERMO=:10 SCHERMO_VERO=1`, e va scritto come scelta |
| ⚠ **il ritardo** | questo anello misura **che** il pixel arrivi, non **quando**. La tela desincronizzata di `web.md` §6.1 sta dietro un interruttore **spento** (`?tela=desincronizzata`), perché su una tela desincronizzata `getImageData` legge da un buffer che il compositore può avere già scambiato — cioè rende ambigua la rilettura su cui poggia il metro della fase (I8) |
| ⚠ **il ritmo di AV1 in software** | su 6 fotogrammi a 640×480 non si misura niente di utile, e ⛔ è **la domanda che decide se il ripiego è usabile o solo esistente** (`DECISIONI.md` §1.13) |
| ⚠ **il livello sovradichiarato** | ⭐ `[M]` `hev1.*.L153.B0` e `av01.0.13M.*` su flussi di livello 2.0-3.0 **sono accettati e dipingono** su tutti e due i motori. ⚠ Su un dispositivo che il livello lo fa rispettare davvero non è misurato, ed è per questo che la scala di stringhe ha un secondo gradino |
| ⚠ **un fotogramma chiave grande** | le sequenze stanno sotto i 4 KB. Che il percorso regga un IDR da centinaia di KB, e il tetto dei 16 MiB di §6.2, **non è stato misurato qui** |
| ⚠ **il congedo `NIENTE_IN_COMUNE` sul filo vero** | la strada «nessun codec arriva al pixel» è misurata **dentro la pagina**; che il server risponda come §4.3 gli impone **non è stato provato**, perché su ogni scena provata almeno AV1 arriva. ⭐ Quel che è misurato sul filo vero è il passo prima: la pagina dichiara **`video.codec=av1`** e il server negozia `av1` (§3, banco 3) |
| ⚠ **il fotogramma vero dal server** | il percorso è misurato con flussi **noti**, consegnati a `stream_video()` — cioè dalla porta da cui entrano i fotogrammi quando la sessione è vera. ⛔ Che un fotogramma prodotto da F2.3 e spedito da F2.4 attraversi tutto **non è stato misurato qui**: nessun server della fase 2 lo spedisce ancora |
| ⚠ **appunti e cursore** | riconosciuti, registrati e **non usati**: la fase 2 non li ha. Si dice, invece di saltarli in silenzio |

---

## 8. I file di questo giro

| File | Che cosa |
|---|---|
| **`src/pagina.html`** | ⭐ **il prodotto**: 34 089 → 90 357 byte. `Schermo` (lettore di §6.2, regole di §5.2/§6.2, decodifica, tela), la sonda del codec, il riquadro della degradazione, l'ascolto del canale di controllo dopo `SESSIONE`, gli stream unidirezionali |
| `banchi/02-pagina-sonda-codec.py` | costruisce le quattro sonde da 64×48 e **si certifica**: sano → guasto `una-tinta` → risanato |
| `banchi/02-pagina-prodotto.html` | il banco che guida il prodotto in un iframe con i flussi noti, e ne rilegge i pixel |
| `banchi/02-pagina-prodotto-certifica.sh` | sano → 4 guasti → risanato |
| `banchi/02-pagina-tela-prodotto.html` | i quindici casi del cambio di tela, con l'atteso scritto prima |
| `banchi/02-pagina-tela-prodotto-verdetto.py` | il verdetto, **fuori dal browser** |
| `banchi/02-pagina-tela-prodotto-certifica.sh` | sano → 4 guasti → risanato |
| `banchi/02-pagina-lancia.sh`, `02-pagina-tela-lancia.sh` | `BERSAGLIO=banco\|prodotto`, e la scena per esteso nella riga di esito |
| `banchi/02-pagina-raccogli.py`, `02-pagina-tela-raccogli.py` | servono `src/pagina.html` **dove sta**, senza copiarlo |
| `banchi/02-pagina-verdetto.py` | ⭐ il controllo **P9** |

⛔ **Niente altro in `src/`** è stato toccato. Nessun `git` che scrive. `RCP.md` intatto.
**7448 e 7501 contate prima e dopo: accese tutt'e due, quattro ascoltatori.**

---

## 9. Il giudizio dell'utente

⏳ **Non ancora dato**, e c'è una cosa precisa da fargli guardare: ⭐ **il proprio desktop dentro una
scheda**, che è il metro della fase. Finché il server della fase 2 non spedisce un fotogramma vero,
quel che si può mostrare sono i PNG di `banchi/02-pagina-pixel/` — i pixel **usciti dalla tela del
prodotto**, non da una pagina di prova.
