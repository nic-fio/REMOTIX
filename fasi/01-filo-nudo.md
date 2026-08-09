# Fase 1 — Il filo nudo

Aperta il **9 agosto 2026** · **Riscritta la sera del 9 agosto**, dopo due revisioni avversariali ·
Chiusa il **—**

> ⛔ **Questo documento si apre prima di sviluppare, e contiene i banchi** (`PIANO.md` §0.1). Le
> tabelle delle misure sono **vuote per costruzione**: si riempiono strada facendo, una riga alla
> volta, con la data e la scena. Un documento scritto dopo è un resoconto, e in un resoconto le
> misure si *ricordano* invece di essere *registrate*.

> ## ⛔ La prima stesura è stata revisionata prima di produrre un numero, e non ha retto
>
> Due revisioni avversariali con due lenti diverse — `fasi/rapporti/R3-revisione-banco-01.md` (il
> banco come strumento, **28 rilievi**) e `R4-revisione-banco-01.md` (la coerenza con quel che è
> già scritto, **16**). **44 rilievi: 38 `[R]`, 6 `[?]`, nessun `[M]`.** Nessuna delle due è verde.
>
> ⭐ **È il primo dei tre momenti di `PIANO.md` §0.4 che fa il suo mestiere**: il banco è il primo
> imputato, e questo è costato una riscrittura invece di tre fasi di misure avvelenate.
>
> **Le sei cure che hanno cambiato la forma del documento, non il dettaglio:**
>
> | | |
> |---|---|
> | **l'ordine era circolare** | tre misure della sonda pretendevano il server che il banco della libreria deve ancora scegliere. ⭐ **B2 adesso viene prima**, e la sonda si divide in *prima del filo* e *sopra il filo* — R3.4, R4.3 |
> | **cadeva sempre il controllo che dice *no*** | delle **undici** prove di controllo che i rapporti prescrivono per S1a, S2 e S4 ne erano sopravvissute **tre**, ed erano tutte del tipo che dice *sì*. Due erano già state bocciate da `R2` con l'istruzione *«curare prima di scrivere una riga di banco»* — R3.1 |
> | **il rigore puntava in un verso solo** | dodici violazioni verso il server, **nessuna verso la pagina**, mentre `RCP.md` §3 è scritta su *«un'implementazione RCP»*. ⭐ Nasce **B11** — R4.1 |
> | **i dispositivi non esistevano** | sei misure su nove pretendono ferro che nessun documento dichiara. ⭐ Nasce il capitolo delle **dipendenze**, prima dei banchi — R3.14 |
> | **la certificazione copriva 4 banchi su 12** | e i due scoperti — B3 e B7 — sono i banchi dei due difetti più cari di v1 — R3.7, R4.6 |
> | **sei cose prodotte non le guardava nessuno** | fra cui che **i due certificati siano due**, e che la parola d'ordine non finisca in un registro. ⭐ Nasce **B13** — R3.24 |
>
> ⚠ **E tre cure sono cadute fuori da questo file**, perché la stonatura era altrove: `RCP.md`
> §4.1-bis e §7.3, i controlli negativi nei banchi di `web.md`, e la riga della fase 0 che manda la
> sonda alla fase 2. Sono elencate in fondo, sotto «Le cure fuori da questo documento».

---

## Che cosa deve produrre

La **stretta di mano di RCP su WebTransport**, dai due lati: il server in C e la pagina servita dal
server stesso. Niente video, niente audio, niente input.

**Che cosa vede l'utente, e giudica**: apre `https://192.168.0.2:7447` nel browser, digita utente e
password, e la pagina dice *«ammesso, sessione nuova, tela 1920×1080, desktop GNOME»*. Oppure dice
**perché no**, con una frase comprensibile e non un numero (`RCP.md` §8.2).

### ⛔ Il confine della fase, e le quattro cose che produce senza sembrare

*Riscritto dopo R4.2, R4.5, R4.8 e R4.11: la prima stesura ne dichiarava una sola, e le altre tre
sarebbero nate senza banco.*

| | |
|---|---|
| **`SESSIONE`** | `stato` vale **sempre `NUOVA`**. La sessione grafica vera nasce alla fase 2, la sua vita e i tre orologi alla fase 5. ⛔ **E «sempre» si verifica** (B13): un ramo `RIPRESA` scritto per prudenza e mai provato è precisamente quel che questo riquadro esiste per impedire |
| ⛔ **la tela concessa** | **non** è «quella chiesta»: è quella chiesta **capata a `video.misura_massima`** se il client l'ha dichiarata, e comunque dentro i limiti e la parità di `RCP.md` §4.5. *Correzione R4.2: la riga precedente contraddiceva un DEVE, e il difetto sarebbe nato invisibile qui per presentarsi alla fase 2 come «il browser non apre il flusso» — cioè il sintomo di un'altra causa* |
| ⭐ **l'occupazione della sessione** | ⛔ la fase 1 produce **metà dell'invariante I2**, e va detto: per rispondere `GIA_ATTIVA_REMOTA` il server deve sapere che esiste una sessione di quell'utente con un client **vivo** attaccato. Quel che resta alla fase 5 sono **i tre orologi** (`DECISIONI.md` §4.5), non l'occupazione. *Senza questa riga B3 provava una cosa che nessuna fase dichiarava di produrre — R4.5* |
| ⭐ **le capacità che il server dichiara in `ECCOMI`** | `RCP.md` §4.3 le rende **normative**: chi non dichiara `pcm` e `8` si congeda con `NIENTE_IN_COMUNE`. Il server della fase 1 dichiara **`video.codec=hevc` · `video.profondita=8,10` · `audio.codec=pcm,opus` · `appunti.testo=si`** — cioè quel che il prodotto avrà, non quel che la fase 1 sa già fare. ⚠ **È una dichiarazione d'intenti, ed è onesta solo se qualcuno la verifica**: la fase 2 deve provare che il codec negoziato sia davvero quello prodotto, o la negoziazione mente da qui in avanti. *Senza questa riga il cliente di prova sarebbe diventato rosso applicando §4.3 alla lettera, e chi l'ha scritto avrebbe pensato di aver sbagliato lui — R4.8* |
| ⛔ **la pagina servita isolata fra origini** | `SPECIFICHE.md` §11.5: **è un vincolo di prodotto**, non una taratura del banco — cambia come il server serve **ogni** risorsa, e deciderlo dopo significa riconfezionare la pagina. La fase 1 è l'unica in cui il server acquista il mestiere di servirla. *Mancava del tutto — R4.11* |

---

# ⛔ Le dipendenze: che cosa serve, e che cosa oggi non c'è

*Capitolo nuovo, dal rilievo **R3.14**. La prima stesura scriveva nove righe di sonda dando per
esistenti dispositivi che nessun documento del progetto nomina — e `fasi/00-ambiente.md` dichiara
quell'ambiente **non toccato**. Una dipendenza non dichiarata è una misura che non si fa, e questo
progetto l'ha già pagata due volte in un giorno (`weston` e i gruppi `adm`/`systemd-journal`).*

*Censito con l'utente la notte del 9 agosto 2026: **il telefono Android e il DeX ci sono, il mondo
Apple no**.*

| Serve a | Che cosa | C'è? |
|---|---|---|
| S2, S5, S3a | ⭐ **il telefono Android** con Chrome | ✅ **sì** — e non va configurato: si apre un indirizzo |
| S3a, S5 | ⭐ un dispositivo **DeX** (la lock esiste solo da **Android 16 QPR1**) | ✅ **sì** — ⚠ `[?]` **da verificare che sia almeno Android 16 QPR1**, o S3a misura l'assenza della lock e la scambia per una perdita di scorciatoie |
| S2 | un **PC collegato** per `chrome://inspect` — il controllo C, l'unico canale che risponde davvero | ✅ sì |
| S7 | sessione GNOME e `libei` | ✅ `banchi/00-sessione-gnome.sh`, `libei1` 1.3.901 `[M]` |
| tutti | il `devroot`, la macchina di prova, la cache dei pacchetti | ✅ fase 0 |
| B9 | `python3-aioquic` 1.2 | ⚠ `[M]` c'è, ma **che porti WebTransport lato client non è `[M]` da nessuna parte** (R3.21) |
| B10 | un **secondo utente** sul server, con parola d'ordine, che PAM sappia autenticare | ⛔ **no** — e ⛔ **va in `provision-server.sh`, non creato a mano**, o in un giorno è invisibile (`LEZIONI.md` §2.5-bis) |
| S2 | **cinque sequenze di prova** da `hevc_vaapi` (S2 §4.1), fra cui la rampa di grigio per i 10 bit | ⛔ no — dipendono dal codificatore, che è della fase 2 |
| ⛔ **S1a, B2** | un **Mac** con Safari 26.4, e un **iPhone/iPad collegato al Mac** col Web Inspector — su Safari non esiste `net-export` (S1 §4.3) | ⛔ **NO, e non si aggira** |
| ⏳ S3b | un **certificato vero con un dominio**: dietro l'eccezione il Service Worker non si installa `[R]`, quindi **la PWA non esiste** (R3.12) | ⛔ no — *rimandata* |

> ## ⭐ Safari non si misura in questa fase, ed è una decisione — non una mancanza
>
> **`DECISIONI.md` §1.8**, dall'utente il 9 agosto 2026: *Apple è un di più, non un obiettivo*.
> Non si procura un Mac, non si affittano dispositivi, non si monta un tunnel. **S1a esce dalla
> fase 1 e resta `[?]`.**
>
> ⛔ **E non è «Safari non è supportato»**: il codice è lo stesso per tutti e tre i motori, e la
> strada su Safari 26.4 è la stessa degli altri due. Non si spende per **verificarlo**.
>
> Le tre conseguenze, e nessuna si cura scrivendo codice:
>
> | | |
> |---|---|
> | **B2 perde un terzo del suo criterio** | *«tutti e tre i motori aprono la sessione»* diventa **due su tre**, e la libreria QUIC si sceglie **sapendo di Chrome e Firefox**. ⚠ Va scritto accanto alla scelta, o fra sei mesi sembrerà una scelta informata |
> | ⭐ **ma non blocca niente** | `serverCertificateHashes` è spedito in **Safari 26.4** `[R]`: iPhone e iPad hanno **la stessa strada** degli altri due. S1a decideva **una comodità** — se lì l'impronta si possa risparmiare — non se una piattaforma sia servibile (`RCP.md` §4.1-bis) |
> | ⛔ **e quel che resta scoperto va detto a chi installa** | finché nessuno prova su Safari, *«funziona su iPhone»* è **una deduzione, non una misura**. È la forma **E5**, e il posto dove non deve comparire è la documentazione del prodotto |
>
> ⚠ **Il giorno in cui un Mac ci fosse**, S1a si fa in un pomeriggio: i tre controlli sono già
> scritti qui sopra, e la pagina sonda è la stessa.

⚠ **E `fasi/00-ambiente.md` e `PIANO.md` §1.2 non concordavano** su dove viva la sonda: la fase 0 la
mandava alla fase 2, il piano la mette *«prima di tutto»* nella fase 1. Chiarito con una nota datata
nel documento della fase 0.

---

# Il banco

⛔ **Scritto prima di sviluppare, e revisionato prima del prodotto** — `PIANO.md` §0.4.

## ⭐ L'ordine, e perché è quello

*Corretto da R3.4 e R4.3: l'ordine dichiarato era **circolare**. S1a, S6 e S4 pretendono un server
che parli WebTransport, cioè la cosa che B2 costruisce; e B2 pretende di sapere che Safari sappia
aprire la sessione, cioè la domanda di S1a. Chi eseguiva il documento nell'ordine scritto si
fermava alla prima riga della prima misura.*

| Quando | Che cosa | Perché lì |
|---|---|---|
| **1** | **le cinque misure indipendenti dal filo**: S1b · S2 · S3a · S5 · S7 | non toccano il server: si fanno subito, e S1b **va fatta per prima perché dura sette giorni** |
| **2** | ⭐ **B2 — il banco della libreria** | produce il **server minimo da cinquanta righe** su cui tutto il resto poggia, e chiude `DECISIONI.md` §6.4 |
| **3** | **le due misure che vivono sopra il server minimo**: S1a · S6 | ⚠ e se la candidata poi cambia, **si rifanno**: un controllo positivo fatto su un motore diverso da quello del prodotto è la forma **E10** |
| **4** | i banchi del filo: **B3-B13** | provano il prodotto contro `RCP.md`, mai contro sé stesso |
| ⏳ **rimandate** | **S4** → fase 3 · **S3b** → dove arriverà il suo certificato vero | S4 non è «senza prodotto»: vuole codifica, trasporto e decodifica — ⛔ **e una riga di protocollo, da decidere adesso** (vedi sotto) |

> ### ⛔ La riga di protocollo che S4 pretende, e la finestra che si chiude
>
> S4 §5.3 lo dichiara: la marca del banco — **il rettangolo 16×16 e il comando che lo cambia, con
> il ritardo `N` iniettabile del controllo decisivo** — è *«un'estensione di protocollo … va
> scritta in `RCP.md` come **funzione di banco**, non improvvisata nel codice di prova»*.
>
> ⛔ **E `RCP.md` §9 chiude la finestra dei tipi nuovi «dal primo byte scritto in poi».** Se quel
> messaggio non entra **prima** che il server esista, entrerà come deroga a una regola che protegge
> le implementazioni — cioè come il primo strappo, fatto da noi, alla regola che abbiamo scritto
> ieri. **Aperta in `RCP.md` §12, da chiudere prima del primo byte** (R3.4).

## B0 — Le regole che valgono per tutti i banchi

*Sezione nuova: cinque rilievi diversi (R3.3, R3.8, R3.16, R3.17, R3.18, R3.23) dicevano la stessa
cosa in cinque posti — che il banco non dichiara da che stato parte, e che quel che sopravvive fra
una prova e l'altra falsa la prova successiva.*

| # | La regola | Da dove viene |
|---|---|---|
| **0.1** | ⛔ **ogni banco dichiara e VERIFICA il proprio stato iniziale** prima di partire, come `00-c1-kwin.sh` verifica che il socket di KWin non ci sia più. Un banco che non sa da che stato parte **misura la storia della macchina** | R3.16 |
| **0.2** | ⛔ **e lo stato che sopravvive è più di uno**: l'eccezione concessa sul certificato della pagina *(che S1a e S1b **misurano**)*, il certificato di sessione già ruotato da B3, **la sessione creata al giro prima** *(che a meno di 30 s fa dare `GIA_ATTIVA_REMOTA` alla prima connessione del giro nuovo — rosso su codice giusto)*, il permesso `clipboard-read`, e i due contatori di §4.4-bis | R3.16 |
| **0.3** | ⛔ **l'isolamento fra banchi**: i contatori dei tentativi sono **per nome e per indirizzo**, e tutti i banchi partono dallo stesso indirizzo. B7 fallisce un tentativo, B8 ne fallisce cinque, **e B10 arriva dentro la finestra e legge «il secondo utente non entra»** — cioè un falso rosso che *conferma* il difetto che B10 cerca. ⚠ E non si cura azzerando i contatori fra un banco e l'altro, o **B8 non prova più niente**: si cura **cambiando indirizzo di provenienza** o dichiarando l'attesa | R3.8 |
| **0.4** | ⛔ **l'atteso lo confronta il banco, non chi legge**: si stampa *e* si confronta, e lo stato d'uscita è quello del **confronto**. ⚠ E attenzione al punto contro la virgola: `"60"` contro `"60,0"` dà rosso su codice giusto, ed è il difetto ancora aperto di `00-c1-kwin.sh` | R3.18, R3.23 |
| **0.5** | ⛔ **dopo ogni prova che deve far cadere la connessione, il server deve essere ancora lì**: una connessione nuova che arriva fino a `SESSIONE`. «Cade sempre» è soddisfatto anche da un server **ucciso dal nucleo** | R3.3 |
| **0.6** | ⛔ **la versione esatta del browser si annota**, ogni volta. *«Un risultato senza versione, fra sei mesi, non vale niente»* (S1 §4.5) — e questo è il capitolo che invecchia in mesi | R3.16 |
| **0.7** | ⛔ **i due lati si sincronizzano con marcatori, non con `sleep`** — e il precedente in casa **non** è un esempio da copiare: `banco.sh` della fase 0 ha ancora il suo `sleep 2.5` | R3-§4.9 |

---

## Gruppo 1 — Le cinque misure indipendenti dal filo

⛔ **Tutte sul dispositivo vero, mai su un browser di comodo** (`DECISIONI.md` §5-bis.0-ter).
⭐ **E ogni riga porta il rimando puntuale al rapporto dove vive la procedura**: le etichette
`S1a…S7` sono nate in `web.md` §7 e **non compaiono in nessuno dei quattro rapporti**, dove le
prove si chiamano in quattro modi incompatibili — e due rapporti usano `P1…Pn` per cose di natura
opposta (R3.28).

### S1b — quanto dura l'eccezione su Chrome  ·  `S1 §4.2 P5`

| | |
|---|---|
| **si misura** | dopo quanti giorni l'avviso ricompare sulla pagina |
| **atteso** | **7 giorni** — `[S]`→`[R]` da `kCertErrorBypassExpirationInSeconds = 604800`. ⚠ **La promozione di marca è dichiarata qui**: `web.md` §8 la teneva ancora `[?]`, e le due righe di `web.md` si contraddicevano (R4.14) |
| ⛔ **il controllo** | **l'impronta del certificato DELLA PAGINA, letta all'inizio e alla fine, deve essere la stessa.** Senza, un certificato rigenerato da un riavvio fa scrivere «l'eccezione è durata quattro giorni» e la frase che si dirà all'utente nasce sbagliata (R3.15) |
| ⚠ **il calendario** | è l'unica misura che richiede **sette giorni di tempo reale**, e la fase non si chiude prima. Se si accelera spostando l'orologio della macchina, ⭐ il controllo diventa *«a sei giorni l'eccezione c'è ancora»* — che è un controllo vero |

### S2 — HEVC Main10 in hardware, sul telefono vero  ·  `S2 §4.2 misure 1,2,4 · §4.4 controlli A,B,C`

| | |
|---|---|
| **si misura** | portata a saturazione (4K60 Main10), **canarina di CPU** in un worker, **decadimento su dieci minuti** |
| ⛔ **l'atteso NON è «`[S]` sì da Chrome 108»** | quel `[S]` riguarda il **supporto in WebCodecs**, non l'hardware: scriverlo come atteso di una misura di *hardware* mette **E1 nella casella dell'aspettativa**, e le prove indirette si leggono con indulgenza quando l'atteso è già scritto. **L'atteso è `[?]`** (R3.13, R4.13) |
| ⛔ **i tre controlli, non uno** | **A**: VP9 `prefer-software` **dev'essere dichiarato software** · **B**: VP9 `prefer-hardware` **dev'essere dichiarato hardware** — *era caduto, ed è quello che dice no* · **C**: ⭐ **`is_software_codec` letto via `chrome://inspect`** |
| ⭐ **e il canale diretto esiste** | su Android, `media_codec_video_decoder.cc` registra `is_software_codec` col nome che arriva da `MediaCodec.getName()`. **Il browser sa e non risponde *da JavaScript*** — ma il banco non è JavaScript: il banco è chi guarda (`LEZIONI.md` §1.11 regola 2). Rinunciarci per tre prove indirette, sull'uso primario, era una scelta non dichiarata (R3.13) |
| ⛔ **gli esiti sono tre** | ≥ 90 fps ⇒ hardware · ≤ 30 ⇒ software · **in mezzo: verdetto sospeso**. La prima stesura ne aveva due, dove il rapporto ne prevede tre |
| ⚠ | su iPhone il canale diretto non esiste, e lì le tre indirette restano l'unica strada |

### S3a — la tastiera, nei tre stati  ·  `S3 §4.2 (quattro controlli) · §4.3 (gruppi A-E) · §4.4`

⛔ **La domanda non è «arriva?» ma «arriva *e basta*?»** — gli stati sono tre: *consegnata* ·
**consegnata *e* riservata** · *non consegnata*. Il secondo è il peggiore (`SPECIFICHE.md` §7.3-bis,
O8).

| | |
|---|---|
| ⛔ **il difetto che invertiva la misura** | `Ctrl+W` su DeX: la pagina riceve il `keydown` **e** il browser chiude la scheda. Se il registro vive nella pagina, **la chiusura porta via il registro**: il banco scrive «non consegnata», cioè **lo stato opposto** — e dichiara innocuo il caso pericoloso (R3.11) |
| ⛔ **la cura, già scritta nel rapporto** | S3 §4.3 ordina le undici combinazioni **dalla meno rischiosa alla più rischiosa, una per volta**, con `Ctrl+T`, `Ctrl+N` e `Ctrl+W` **ultime e col registro già copiato fuori dal dispositivo**. Era caduta la sola riga che rende la misura possibile |
| ⛔ **i quattro controlli, prima di ogni sessione e a ogni motore** | che una battuta **nuda** arrivi *(senza, ogni «non è arrivata» è ambiguo fra «il browser se l'è tenuta» e «il banco era sordo»)*; che arrivi una combinazione **con modificatori**; che gli **appunti in uscita** funzionino; ⛔ e che lo schermo intero **non** sia entrato con `F11` — perché con `F11` **la lock non esiste e non lo dice**, e tutte le prove che seguono non valgono niente |
| ⚠ **e «la sessione»** | alla fase 1 **non c'è canale di input**: qui il ricevente è **la pagina**. La formulazione precedente mandava chi scrive il banco a cercare qualcosa che non esiste |

### S5 — la tela che il client dichiara  ·  `SPECIFICHE.md §6.1-bis · DECISIONI.md §5.0-quater`

| | |
|---|---|
| **si misura** | il numero che la pagina dichiarerebbe in `ATTACCA`, a zoom **100 %** e **150 %**; e che cosa risponde `screen` **su DeX** |
| ⛔ **il controllo di prima era rosso sul codice giusto** | diceva *«i due numeri devono differire»*. Ma la tela **giusta** è lo schermo in pixel fisici, che **con lo zoom non cambia**: `screen.width` cala di un terzo, `devicePixelRatio` sale di un mezzo, il prodotto resta. Una pagina scritta bene dava **1920 e 1920** ⇒ rosso, e chi lo leggeva sarebbe andato a rompere la pagina finché il numero non si muoveva — cioè a **scrivere** il difetto che `DECISIONI.md` §5.0-quater voleva evitare (R3.10) |
| ⭐ **il controllo giusto** | la tela dichiarata a 100 % e a 150 % **deve essere la stessa**, e **deve coincidere con la risoluzione fisica letta fuori dal browser**, nelle impostazioni del dispositivo. Due strumenti diversi sullo stesso fatto |
| ⛔ **e la terza domanda non è chiudibile con una misura** | *«l'arrotondamento può produrre un numero dispari?»* — su un dispositivo si osserva un numero; se è pari **non se ne ricava che i dispari non esistano** (`LEZIONI.md` §1.3). La protezione va **nel programma**, dove **I7** la vuole: la pagina arrotonda al pari per difetto. La misura può solo trovare un positivo |

### S7 — da che parte gira la rotella  ·  `RCP.md §7.3`

| | |
|---|---|
| **si misura** | si inietta `+120` con `libei` in una sessione GNOME (`banchi/00-sessione-gnome.sh`) e si guarda da che parte va la pagina |
| ⭐ **il controllo** | si inietta anche **`-120`**: se la pagina va dalla stessa parte, non si sta misurando il segno. ⭐ *È il controllo meglio scritto della prima stesura, e resta* |
| ⛔ **il controllo che mancava** | si rifà **con `natural-scroll` nei due stati**: se il segno cambia, il numero che finirebbe in `RCP.md` §7.3 è **il segno di una gsetting della sessione di prova**, e il sintomo per l'utente è *«la rotella va al contrario»* su metà delle installazioni. Forma **E11** (R3.25) |
| `[?]` **e una domanda che resta** | §7.3 vincola **cinque** desktop e la misura è su **Mutter**. Se `libei` normalizza, il numero vale ovunque; se normalizza il compositore, la fase 10 troverà un segno diverso su KWin e non saprà se correggere il protocollo o il server. ⚠ La fase 0 ha misurato **tre** famiglie in un pomeriggio: qui la stessa domanda ha una risposta sola |
| ⚠ **e la lezione citata era quella sbagliata** | il banco della rotella di v1 è costato **una stringa di registro cercata male** (`LEZIONI.md` §2.3), non una tabella col segno sbagliato. Citando la lezione sbagliata **la si perde nel punto in cui si applicherebbe** (R4.15) — la frase è di `RCP.md` §7.3, ed è corretta lì |

---

## Gruppo 2 — B2, il banco della libreria: quale QUIC arriva fino a WebTransport

⛔ **Viene prima di S1a e S6, ed è la cosa che chiude `DECISIONI.md` §6.4** — con un banco davanti,
non su carta. Il criterio è cambiato il 9 agosto: non basta che la libreria parli QUIC, deve
portare **HTTP/3 e WebTransport lato server**, più un ascoltatore **TCP** per la pagina.

**La prova**: un server minimo — cinquanta righe, che si buttano — che accetta una sessione
WebTransport su `/rcp/1`, aperta da **un browser vero**, con l'impronta pubblicata nella pagina.

| Candidata | Sul ferro `[M]` 9 ago | Da provare |
|---|---|---|
| **`quiche`** (BSD-2, API C) | `cargo`/`rustc` 1.85 | `[?]` fino a dove arriva **lato server**: HTTP/3 sì, WebTransport da verificare |
| **`ngtcp2` + `nghttp3`** (MIT) | `libngtcp2-dev` 1.11, `libnghttp3-dev` 1.8 | `[?]` quanto collante resta a noi, e il TLS da montare |

**L'atteso, che la prima stesura lasciava vuoto** (R3.23):

| | |
|---|---|
| **passa** | la sessione si apre su **Chrome e Firefox**, e la pagina riceve un byte dal server. ⛔ **Erano tre motori**, e Safari esce perché non c'è un Mac (vedi «Le dipendenze»): la scelta della libreria si fa **sapendo di due su tre**, e questa riga esiste perché fra sei mesi non sembri una scelta informata |
| ⛔ **e cinque proprietà si verificano qui**, perché sono della libreria e nessun altro banco le guarda | **datagram abilitati** sulla connessione HTTP/3 (§2.2) · **niente 0-RTT** (§2.3) · **migrazione non disabilitata** (§2.3) · **`max_idle_timeout` = 30 s imposto dal server** (§2.2) · **`allowPooling` a `false`** (§4.1-bis) |
| ⛔ **e una che serve a B3** | che il banco **possa cambiare `max_idle_timeout`**: senza, la riga dei 30 secondi di B3 non è distinguibile dal trasporto (R3.19). È il tipo di cosa da decidere **scegliendo la libreria**, non scrivendo B3 |
| **il criterio di scelta** | ⚠ *«il numero di righe che restano a noi»* non è un atteso: si conta il **collante misurato**, candidata per candidata, e il numero si scrive. Senza, la scelta si fa a giudizio |

⛔ **Il sintomo di 0-RTT acceso non esiste**: `CREDENZIALI` si può ripetere, e nessun banco
funzionale lo vede mai. Le librerie QUIC lo offrono **per impostazione predefinita**.

---

## Gruppo 3 — Le due misure che vivono sopra il server minimo

### S1a — l'eccezione su Safari copre WebTransport?  ·  `S1 §4.2 P1, controlli P2-P4`

| | |
|---|---|
| **si misura** | su **Safari macOS e iOS separati**: una sessione WebTransport dietro la sola eccezione del certificato |
| ⛔ **i tre controlli, non uno** | **P2** la connessione **con l'impronta pubblicata deve riuscire** — *stesso browser, stessa pagina, stesso giro* · **P3** ⛔ **con l'impronta sbagliata di un byte deve FALLIRE** · **P4** con un certificato a **30 giorni** deve fallire **per durata** |
| ⛔ **perché P3 è quello che mancava** | senza, una pagina che guarda **la promessa sbagliata** — considera «riuscita» la costruzione dell'oggetto invece di attendere `ready` — fa riuscire **anche** la prova con l'impronta storpiata, e il banco scrive un `[M]` falso *«su Safari l'eccezione copre WebTransport»* **contro due `[R]` letti nel codice di Chromium e di Gecko** (R3.1). S1 §4.4: *«solo con P2 verde e **P3 rosso** il risultato di P1 significa qualcosa»* |
| ⚠ **che cosa decide** | **una comodità, non una piattaforma**: `serverCertificateHashes` è spedito anche in **Safari 26.4** (`web.md` §3.1) — *la prima stesura citava `RCP.md` §4.1-bis a sostegno, e §4.1-bis diceva il contrario perché non era stata aggiornata. Curata (R4.4)* |

### S6 — quanto porta davvero un datagram  ·  `RCP.md §5.3`

| | |
|---|---|
| ⛔ **non è una grandezza del motore** | lo decide **il cammino** — la MTU più piccola fra i due estremi meno le intestazioni — non il browser. Il motore decide solo che cosa **dichiara** l'API, che è la cosa che la riga stessa diceva di non credere: attribuirlo al motore è **E2**, due misure diverse sotto la stessa etichetta (R3.22) |
| ⛔ **quindi si dichiara il percorso accanto al numero** | come la fase 0 dichiara la scena accanto a ogni fotogramma al secondo. E si misura sul percorso **peggiore che si intende servire** — LTE, o una VPN a MTU 1400 — **non su quello comodo** |
| **il controllo** | si spedisce un datagram di quella misura esatta e **si verifica che arrivi dall'altra parte**, non che l'API lo accetti |
| ⭐ **e se il numero deve essere un tetto di protocollo, non si misura affatto** | si prende il **minimo garantito da QUIC**, che è quel che i **972 byte** del PCM già fanno. Misurare in LAN e alzare il tetto significa spedire audio che l'utente vero non riceve — ⛔ e il PCM è **il controllo positivo di Opus**: si ripiegherebbe su una strada che non esiste |

---

## I banchi del filo

### B3 — la stretta di mano su DUE connessioni, e una terza con la chiave cambiata

⛔ In v1 un certificato condiviso uccideva il server **alla seconda** connessione, e una prova a
collegamento singolo **resta verde per sempre** (`LEZIONI.md` §2.1).

| | Atteso |
|---|---|
| **1ª connessione** | stretta di mano completa fino a `SESSIONE` |
| **2ª dopo la chiusura della prima** | ⛔ **identica alla prima.** Se il server muore, o se la seconda fallisce dove la prima è passata, il difetto è **suo** |
| **2ª mentre la prima è viva** | `CONGEDO(GIA_ATTIVA_REMOTA = 0x0F)` verso **chi arriva**, verificato **dal lato che riceve**, e ⛔ **si controlla quale delle due sopravvive** |
| **la 2ª dopo il silenzio della 1ª** | ⛔ **35 secondi con `max_idle_timeout` alzato a 120** — *non 30 secondi a timeout predefinito*: così com'era, un server **senza nessuna nozione di sessione staccata** restava verde, perché QUIC chiudeva la prima da sé e la struttura legata alla connessione si liberava. Cioè il banco benediceva **la violazione di I4** (R3.19) |
| **3ª con il certificato di sessione ruotato a mano** | la pagina **ritira l'impronta corrente dal server** e riesce (`RCP.md` §4.1-bis) |
| ⚠ **e quel che questo NON prova** | la **rotazione automatica** a quattordici giorni. Cambiare la chiave a mano prova che la pagina sa ritirare l'impronta; che il server rigeneri **prima della scadenza** resta senza banco, e il suo sintomo — *«non si collega più e non dice perché»* — arriva due settimane dopo la consegna |

### B4 — il validatore del filo

Un **terzo programma** che legge una registrazione e dice **quale byte** non è conforme a `RCP.md`
§6. L'unico arbitro meccanico che avremo.

| | |
|---|---|
| **le sei registrazioni guaste** | lunghezza incoerente col tipo (§6.1) · UTF-8 non valido (§6.0) · nome di capacità ripetuto (§4.3) · byte alto fuori dai cinque canali (§2.5) · messaggio nello stato sbagliato — `ATTACCA` prima di `CREDENZIALI` (§1) · ⭐ **corpo giusto ma allineato**, il byte di riempimento che «fa tornare i conti» (§6.0) |
| ⛔ **la settima, che mancava: una registrazione CONFORME, che il validatore DEVE accettare** | senza, «6 su 6» è compatibile con un validatore che **boccia tutto**: basta leggere `lunghezza` come `u16` invece di `u32` — due caratteri — e da quel momento l'arbitro dichiara non conforme **ogni** traccia, con la diagnosi che punta su `RCP.md` §6.1 mentre il difetto è nello strumento (R3.5) |
| ⛔ **e si verifica QUALE byte, non solo che sia rosso** | sulla registrazione col riempimento, un validatore che non conosce §6.0 non vede il byte in più: legge di traverso il **messaggio successivo** e dichiara non conforme **quello**. Rosso giusto, byte sbagliato — e su una traccia vera manda la diagnosi a leggere il messaggio sbagliato |

> ### ⛔ Il formato della registrazione va deciso **prima** di scrivere il registratore
>
> *Rilievo R3.6, e la prima stesura vedeva il problema senza scegliere: due regole a
> contraddirsi, e nessuna che dicesse quale vince.*
>
> | Che cosa fa il registratore | Che cosa succede |
> |---|---|
> | registra i byte **come sono passati** | ⛔ la parola d'ordine in chiaro in un file, vietato da `RCP.md` §4.4 *«a nessun livello»* |
> | **sostituisce** la parola e lascia la `lunghezza` | il corpo non ha più la lunghezza dichiarata ⇒ **falso rosso perpetuo** su ogni traccia con una stretta di mano riuscita |
> | sostituisce **e riscrive la lunghezza** | la registrazione non è più i byte passati: il validatore convalida un documento che il banco ha riscritto — **non è più un arbitro** |
>
> ⭐ **La quarta strada, che si sceglie adesso**: si registra **la lunghezza vera** e **un'impronta**
> del corpo per i soli campi segreti, e il **formato della registrazione dichiara che quel corpo è
> oscurato**. La lunghezza torna, il validatore sa che non deve guardarci dentro, la parola non c'è.
>
> ⛔ **E il formato è uno solo, scritto una volta**: due registratori — uno nel C, uno nella pagina
> — che scrivono lo stesso fatto in due modi sono esattamente il difetto muto contro cui `RCP.md`
> §0 è stato scritto.

### B5 — le prove di violazione: il rigore verso il server

⛔ La connessione **deve cadere ogni volta**, col motivo giusto, verificato dal lato che riceve —
⛔ **e il server deve essere ancora lì dopo** (B0.5).

| Che cosa si manda | Atteso |
|---|---|
| un tipo di messaggio sconosciuto | `ERRORE_PROTOCOLLO` `0x0B` |
| una lunghezza incoerente col tipo (in più e in meno) | `ERRORE_PROTOCOLLO` |
| ⛔ **una `lunghezza` annunciata di 4 GiB** | `ERRORE_PROTOCOLLO` **e il server vivo**: §6.1 vieta di allocare prima di controllare, e un server ucciso dal nucleo *«fa cadere la connessione» lo stesso* — portandosi via **tutte le sessioni degli altri utenti** (R3.3) |
| ⛔ un messaggio che **annuncia più di 1 MiB** (§6.1) | `ERRORE_PROTOCOLLO` |
| `CREDENZIALI` con utente **vuoto**, e con parola **vuota** | `ERRORE_PROTOCOLLO`, ⛔ e **nessuno dei due contatori** di §4.4-bis si muove |
| utente da 257 byte, parola da 1025 | `ERRORE_PROTOCOLLO` (§4.4) |
| `CIAO(versione = 2)` su `/rcp/1` | `VERSIONE_INCOMPATIBILE` `0x0A` |
| una sessione WebTransport su un percorso diverso | **404** |
| uno stream **bidirezionale** oltre il primo, dal client | `ERRORE_PROTOCOLLO` |
| `0x00` (controllo) su uno stream **unidirezionale**; `0x04` (audio) su uno **stream** | `ERRORE_PROTOCOLLO` (§2.5) |
| un canale nel **verso sbagliato** — `0x03` dal client | `ERRORE_PROTOCOLLO` |
| un nome di capacità con **maiuscole**, o da 65 byte; un **valore vuoto**; un valore da 257 byte | `ERRORE_PROTOCOLLO` (§4.3) |
| `video.misura_massima` dichiarata **dal server** | `ERRORE_PROTOCOLLO` |
| `video.codec = vp9` e basta | `NIENTE_IN_COMUNE` `0x09` — *non ha sbagliato a scrivere, non ha di che parlare* |
| `video.codec = hevc,vp9` | ⭐ **si legge `hevc` e si prosegue**, e lo scarto **si scrive nel registro** |
| un `CIAO` **senza `pcm`**, e uno **senza `8`** | `NIENTE_IN_COMUNE` (§4.3) |
| tela `1921×1080`, `319×240`, `7682×4320` | `ERRORE_PROTOCOLLO` (§4.5) |
| ⛔ **vista `300×801`, e vista `1×1`** | ⛔ **DEVONO PASSARE**: §7.1 dice che la vista non ha i vincoli della tela — *«qualunque misura da 1×1 in su è legale, dispari compresa»*. Chi scrive `ATTACCA` in C scrive **una** `valida_misura()` e la chiama quattro volte: è la cosa naturale da fare, e produce un server che chiude la sessione perché l'utente ha stretto la finestra. Su un telefono a fattore 2,75 la vista è **dispari quasi sempre** (R4.10) |
| `disposizione` malformata / ben formata ma sconosciuta | ⛔ **due guasti diversi**: `ERRORE_PROTOCOLLO` · `SESSIONE_NON_SERVIBILE` `0x0E` ⛔ **col dettaglio nel corpo** (§8.2) |
| ⭐ **`BANCO_MARCA` a funzione spenta** | ⛔ **`BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — non un silenzio, non una chiusura** (§7.5). ⚠ È lo stato **predefinito** di ogni server, quindi si prova qui anche se la marca la userà la fase 3: un silenzio lascerebbe il banco della fase 3 ad aspettare per sempre, e il sintomo sarebbe «il banco si è piantato» |
| **`BANCO_MARCA` con `ritardo_ms = 20000`** | `BANCO_ESITO(RIFIUTATA, RITARDO_FUORI_LIMITI)` — ⛔ **non** `ERRORE_PROTOCOLLO`: far cadere la sessione al banco che si sta tarando è la cattiva idea che §7.1 evita per le misure fuori limite |
| ⚠ **e la scelta del codec** | `RCP.md` §4.3 la rende **obbligatoria nel registro del server**: si verifica che ci sia |

⚠ **La chiusura si verifica nei tre punti di §3.1** — registro, `CONGEDO`, codice della sessione —
⛔ **col secondo condizionale**: §3.1 dice *«se il canale di controllo è ancora utilizzabile»*, e un
banco che pretende tutt'e tre sempre **dà rosso sul codice giusto** quando la violazione arriva su
uno stream unidirezionale (R3.3).

### B11 — ⭐ le prove di violazione verso la PAGINA

*Banco nuovo, dal rilievo **R4.1**, ed è il buco più grande della prima stesura: dodici violazioni
verso il server e **nessuna** verso il client. `RCP.md` §3 è scritta su «un'implementazione RCP», e
§9 ha un **DEVE esplicito del client**. In un progetto che ha perso `mstsc` e scrive `RCP.md`
proprio per non fidarsi di due programmi della stessa mano, **un client mai messo alla prova è il
buco al posto dell'arbitro**.*

Un server **guasto di proposito** — poche righe, che si buttano — manda alla pagina:

| Che cosa manda il server guasto | Che cosa DEVE fare la pagina |
|---|---|
| ⛔ `ECCOMI(versione = 2)` a un `CIAO(versione = 1)` | `CONGEDO(VERSIONE_INCOMPATIBILE)` — §9 lo impone al **client** con un DEVE, e accettarla in silenzio è *«l'indulgenza che §3 vieta»* |
| un `SESSIONE` con tela **dispari**, o fuori dai limiti | rifiuta invece di adattarsi |
| un `CONGEDO` con motivo **`0x00`** | `ERRORE_PROTOCOLLO`: §3.1 vieta il codice zero |
| uno **stream bidirezionale aperto dal server** | `ERRORE_PROTOCOLLO` (§2.5) |
| un tipo di messaggio sconosciuto sul canale di controllo | `ERRORE_PROTOCOLLO` |
| una capacità **sconosciuta** in `ECCOMI` | ⛔ **si ignora e si prosegue** — è l'eccezione 1 di §3, ⛔ **e si scrive nel registro** |
| `video.misura_massima` in `ECCOMI` (lato sbagliato) | `ERRORE_PROTOCOLLO` |
| un `FIN` sul canale di controllo | ⛔ la sessione **è finita**: la pagina non spedisce più su nessun canale (§4.2) |
| `RESPINTO` **seguito da** `CONGEDO` | ⛔ il secondo è una violazione (§4.4) |
| dopo `RESPINTO`, la pagina **non deve riprovare** sulla stessa connessione | §4.4 |
| un `SESSIONE` con `desktop = kde` mentre il ferro è GNOME | ⛔ la pagina **non cambia comportamento**: §4.5 lo vieta, e il campo è per la diagnosi |
| ⚠ **e un battito applicativo** | §2.2 lo **vieta**: si verifica che la pagina non ne mandi uno, e che non ne aspetti uno |

⛔ **E la pagina, quando chiude, chiude come dice §3.1**: registro, `CONGEDO`, **e il codice
d'errore applicativo nella chiusura della sessione WebTransport** — che è il punto che
un'implementazione può lasciare indietro restando conforme alla lettera di una versione precedente
del testo.

### B6 — i tempi della stretta di mano

Si apre una connessione e **si tace**, per ciascuno dei tre tetti di `RCP.md` §4.6.

| Da | A | Atteso |
|---|---|---|
| `[?]` **apertura della SESSIONE** (non «TLS finito» — vedi sotto) | `CIAO` | **5 s**, poi `TEMPO_SCADUTO` `0x0D` |
| `ECCOMI` | `CREDENZIALI` | **60 s** |
| `AMMESSO` | `ATTACCA` | **10 s** |

⛔ **Il controllo che distingue i due guasti, ed è il meglio costruito del documento**: se il server
non tiene viva la connessione coi **PING del trasporto**, al trentesimo secondo scatta il tempo di
inattività di QUIC. **Si guarda il motivo**: `TEMPO_SCADUTO` a 60 s è il server che fa il suo
mestiere; una morte a 30 s **senza motivo** è il PING che manca. *R3 ha cercato un terzo caso che
producesse una morte a 30 s con motivo e non l'ha trovato: §3.1 vieta il codice 0 e obbliga il
motivo su ogni chiusura.*

> `[?]` ⚠ **«Stretta di mano TLS finita» non è un istante che i due lati condividono** (R3.27). In
> WebTransport la connessione HTTP/3 e la **sessione** sono due cose separate, e fra i due istanti
> passa almeno un giro di rete — il browser può aver stabilito la connessione molto prima che la
> pagina chiami l'API. Il server farebbe partire il cronometro alla fine del TLS, il banco
> all'apertura della sessione, e la differenza si legge come un tetto sbagliato. ⛔ **E il caso
> peggiore**: una seconda sessione su una connessione riusata partirebbe **col budget già
> consumato**. Da misurare; se confermato, `RCP.md` §4.6 cambia di una parola.

### B7 — il congedo, verificato dal lato che riceve

⛔ **Mai dal registro di chi lo manda**: in v1, per **tre fasi**, il server scriveva «congedo il
client» mentre il client scriveva «errore di rete» (`LEZIONI.md` §1.7).

Per ciascuno degli otto motivi che questa fase sa produrre — `CHIUSO_DALL_UTENTE`,
`VERSIONE_INCOMPATIBILE`, `NIENTE_IN_COMUNE`, `ERRORE_PROTOCOLLO`, `TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`, `SERVER_IN_CHIUSURA` — si verifica il `CONGEDO`
**e** il codice nella chiusura.

| | |
|---|---|
| ⛔ **«8 su 8» non basta, e la prima stesura si fermava lì** | una `switch` col ramo predefinito — `mostra("Errore " + codice)` — dà otto stringhe non vuote e **otto su otto**. L'utente legge *«Errore 14»* per `SESSIONE_NON_SERVIBILE`, che §8.2 vieta con un ⛔ e un esempio quasi identico (R3.20) |
| ⭐ **i due criteri che rendono la riga misurabile** | le otto frasi devono essere **distinte fra loro**, e ⛔ **nessuna deve contenere il numero del motivo** né «errore» seguito da una cifra. Un `grep` di due righe |
| ⚠ **e «il banco guarda lo schermo» non è eseguibile** | o si legge il DOM — l'unica cosa che una prova automatica può fare — **oppure è l'utente** (I8), e allora la riga va nel **giudizio**, non in una tabella con «8 su 8». Dichiarato, così che nessuno la legga come già coperta |
| ⚠ **i due motivi che NON viaggiano in un `CONGEDO`** | `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` stanno in `RESPINTO` (§4.4, rilievo R1.18): un banco che li cercasse in un `CONGEDO` **fallirebbe per costruzione** |
| ⛔ **il `dettaglio` non si mostra** | è per il registro (§8.2) |

### B8 — il secondo fisso, e il limitatore

⭐ **È una proprietà di sicurezza che nessun altro banco vede**, e una regressione che la togliesse
non farebbe fallire niente.

| | |
|---|---|
| ⛔ **il criterio NON è «≥ 1 s», ed è la cura più importante di questo banco** | `pam_authenticate(); sleep(1); rispondi();` dà **1,001 · 1,050 · 1,300 s** nei tre casi: **tre righe verdi**, e la distinzione che §4.4 vieta di scrivere nel motivo si legge col cronometro **esattamente come prima**. Il banco che si dichiara *«l'unico che vede questa proprietà»* non la vedeva (R3.2) |
| ⭐ **il criterio giusto è di forma diversa, non di soglia diversa** | ⛔ **le mediane dei tre casi differiscono meno del rumore della misura** — molti campioni per caso, non uno. Con un campione i cinquanta millisecondi che separano «utente inesistente» da «password sbagliata» non sono nemmeno visibili. **Atteso: ≥ 1 s in ogni campione, e le tre mediane indistinguibili** |
| ⛔ **il controllo del limitatore, che prima era cieco** | *«un'autenticazione riuscita azzera»* non è eseguibile dentro la finestra — §4.4-bis rifiuta **senza interrogare PAM** — quindi la sola sequenza possibile era *cinque rossi, attesa, verde*, che **dà lo stesso esito su un server senza azzeramento** (R3.9) |
| ⭐ **il controllo che distingue** | **quattro** fallimenti (sotto soglia), **un successo**, **altri quattro**: si verifica che l'ottavo **non** sia bloccato. Se il successo ha azzerato, il nono è il quinto; se no, il blocco è già scattato |
| ⛔ **e «subito» vale un secondo** | il ritardo fisso vale *«anche quando la risposta è `AMMESSO`»*, quindi a maggior ragione sui rifiuti: chi cronometra «subito» e si aspetta zero **dà rosso sul codice giusto**. È la forma del rilievo R1.13 di `RCP.md` |
| **il contatore per indirizzo** | soglia, raddoppio fino a 15 minuti, **e la scadenza a 30 minuti di quiete** — ⚠ che è anche la ragione per cui B0.3 esiste |

### B9 — il cliente di prova: il secondo lettore

⭐ Poche centinaia di righe, **in un linguaggio diverso dal server e dalla pagina**, scritte
leggendo `RCP.md`.

| | |
|---|---|
| ⛔ **la separazione dev'essere un MECCANISMO, non una regola** | la prima stesura scriveva *«chi lo scrive non guarda il C né la pagina»*, cioè affidava **l'unico arbitro esterno rimasto** a una memoria. È **I7 al contrario**, ed è la forma che questo progetto ha pagato tre giorni fa: *«la lezione era già scritta, la cura è rimasta una nota in un documento»* (R3.21) |
| ⭐ **il meccanismo, e costa poco** | chi scrive il cliente di prova **riceve `RCP.md` e i suoi riferimenti, e non l'albero del server e della pagina**. E la cosa si **dichiara qui**, così che il giorno in cui il cliente di prova concorderà col server si sappia se quella concordanza vale qualcosa |
| ⛔ **una dipendenza da verificare prima**, ed è il criterio di B2 non riapplicato | che **`python3-aioquic` 1.2 porti WebTransport lato client non è `[M]` da nessuna parte**. Se non lo porta, il cliente di prova non esiste — cioè cade l'arbitro — e ce ne accorgeremmo dopo aver scritto il server |
| ⚠ **l'esito più prezioso non è «passa»** | è **ogni punto in cui chi lo scrive ha dovuto scegliere** perché `RCP.md` ammetteva due letture. Quei punti vanno in «che cosa NON ha funzionato», e sono difetti **del documento** |

### B10 — il secondo utente: il difetto ereditato da `autenticazione.c`

⛔ Il banco autentica un utente **diverso** da quello che possiede il processo del server.
`autenticazione_utente_atteso()` rifiuta chiunque non sia il proprietario del processo: era giusto
in v1, **contraddice il multi-tenant** di `SPECIFICHE.md` §5.5.

| | |
|---|---|
| ⛔ **«non entra» ha quattro cause, e il banco ne nominava una** | *(1)* la guardia è ancora lì — **il difetto**; *(2)* il contatore per indirizzo è nella sua finestra (B0.3); *(3)* la pila PAM non consente al processo di verificare la parola di **un altro** utente; *(4)* il secondo utente non esiste o non ha parola d'ordine. Chi legge quel rosso credendo alla riga vecchia va a cercare nel posto sbagliato — `LEZIONI.md` §1.6 (R3.26) |
| ⛔ **chi possiede il processo va dichiarato** | il banco si definiva *«un utente diverso da quello che possiede il processo»* **senza dire chi sia**, mentre `SPECIFICHE.md` §5.5 lo vuole **di sistema** |
| ⭐ **il controllo che costa dieci secondi** | prima di credere al rosso, si verifica che la stessa parola **funzioni fuori dal server**: `pamtester` sullo stesso servizio PAM. Se fallisce anche lì, **non si sta misurando il server** |
| **atteso** | l'utente `prova` — creato dal provisioning, non a mano — completa la stretta di mano fino a `SESSIONE` |

### B12 — la certificazione: come questi banchi si fanno credere

⛔ `PIANO.md` §0.3 regola 4. *La prima stesura costruiva **quattro** guasti per **dodici** banchi, e
i due scoperti erano i banchi dei due difetti più cari di v1 (R3.7, R4.6).*

| # | La prova | Che cosa dimostra |
|---|---|---|
| **C1** | ⛔ **un guasto costruito a mano PER OGNI BANCO**, e sono dodici | il banco **deve diventare rosso**. Fra i nuovi: **B3** — non si libera la struttura per connessione (il difetto di v1); **B7** — ⛔ **si toglie la spedizione del `CONGEDO` e si lascia il codice nella chiusura**: se B7 resta verde sta facendo una `\|\|` dove serve una `&&`, e **il banco è nato per non accorgersene**; **B4** — il validatore che legge `lunghezza` come `u16`; **B9** — il cliente di prova che ha letto il C |
| **C2** | ⛔ **si guasta il collegamento in TRE modi e si pretendono TRE diagnosi diverse**: nessuno in ascolto · **UDP 7447 filtrato col TCP che risponde** · impronta non corrente. *La prima stesura provava solo il primo — e il secondo è il caso concreto con cui `R2` ha dimostrato che il primo controllo positivo del progetto era cieco* (R3.17) | un banco che le confonde dirà «il server non risponde» il giorno in cui il certificato è scaduto |
| **C3** | si esegue tutto **due volte di fila**, senza rimettere niente | ⚠ e quel che sopravvive è **cinque cose, non una**: vedi B0.2 |
| **C4** | i due lati si sincronizzano con **marcatori** | `LEZIONI.md` §2.3-quinquies |
| **C5** | ⛔ **ogni banco confronta il proprio atteso**, e lo stato d'uscita è quello del confronto | ⚠ *La prima stesura citava `00-c1-kwin.sh` come modello: quel file **stampa e non confronta**, ed è un difetto dichiarato aperto nella fase 0. Citato adesso come **il difetto da non ripetere*** (R3.18) |

### B13 — ⭐ Sei cose che la fase produce e che nessun banco guardava

*Rilievo **R3.24**. Tre hanno un ⛔ scritto in `RCP.md`.*

| # | Che cosa si verifica | Quando morderebbe |
|---|---|---|
| **1** | ⛔ **che i due certificati siano DUE** (§4.1-bis): impronte diverse, scadenze diverse | un server che ne genera uno solo a scadenza breve **passa tutti i banchi** — e l'avviso ricompare **quattordici giorni dopo**, quando *«nessuno collegherebbe le due cose»* |
| **2** | ⛔ **che la parola d'ordine non sia in nessun registro**: un `grep` della parola di prova su **tutti** i file prodotti dal giro — registro del server, registro della pagina, registrazione del validatore | la fase riusa `registro.c`, che in v1 è *«un registratore di battitura»*, e aggiunge un registratore di byte decifrati |
| **3** | **la chiave privata a `0600`**, il `subjectAltName` che combacia, e ⛔ **che un certificato d'autorità installato venga usato senza rigenerare il proprio** (§4.1) | nessuna fase lo dichiarava |
| **4** | **la pagina servita in TCP**: che si carichi, che pubblichi l'impronta **corrente**, e che **l'endpoint da cui si ritira l'impronta aggiornata esista** (§4.1-bis) | è il secondo mestiere che il server acquista qui, e B3 lo presupponeva in una riga |
| **5** | **il credito di almeno 16 stream unidirezionali** concessi al client (§2.3) | se finisse, *«l'input non partirebbe affatto»* e il sintomo sarebbe «il desktop non risponde» — alla fase 4, lontano da qui |
| **6** | ⛔ **che `stato` valga SEMPRE `NUOVA`**, cioè che nessuno abbia scritto per prudenza un ramo `RIPRESA` che nessuno proverà fino alla fase 5 | un `[?]` implementato a metà e non provato è quel che il confine dichiara di voler evitare |

### B14 — che cosa di `RCP.md` §11 questa fase NON prende, e dove va

| Banco di §11 | Dove |
|---|---|
| ⛔ **il rilascio dei tasti al distacco** | **fase 5**, non fase 4 — *corretto da R4.7*: §11 ne scrive la procedura come *«si stacca una connessione con un tasto premuto **e si riattacca**»*, e alla fase 4 non esiste una sessione a cui riattaccarsi. Alla fase 4 la sessione **muore con la connessione**, quindi il banco o non si scrive o **si scrive verde per costruzione** |
| l'audio ascoltato, il formato del PCM | **fase 7** — ⚠ ma **S6** è qui, perché decide i 5 ms |
| gli appunti, i tre messaggi, i due trasferimenti insieme | **fase 7** |
| l'anello del ritardo | **fase 3**, ⛔ **e S4 con lui** (vedi «L'ordine») |
| il fotogramma abbandonato e la chiave che segue | **fase 3** |
| il credito degli stream oltre i 256 fotogrammi | **fase 3** — ⚠ il **credito concesso al client** invece è qui (B13.5): sono due versi diversi dello stesso obbligo |
| ⏳ **`GIA_ATTIVA_LOCALE` `0x05`** | ⛔ **non era di nessuna fase** *(R4.16)*: nasce all'attacco, cioè nel messaggio che questa fase scrive, e la riga di `SPECIFICHE.md` §5.1 che lo impone è la stessa che genera `GIA_ATTIVA_REMOTA`. ⚠ **Va alla fase 5**, con i tre orologi e la sessione locale — ma **dichiarato qui**, o cadeva fra le fasi |

---

# Che cosa è stato sviluppato

*Vuoto: nessuna riga di prodotto scritta.*

**Si riusa** (`PIANO.md` fase 1): `autenticazione.c` (144 righe, PAM) — ⛔ **con la cura di B10** — e
`registro.c` (140) — ⚠ **con l'obbligo di B13.2**.

---

# Le misure

*⛔ Con la scena, il dispositivo e la **versione** dichiarati accanto a ogni numero (B0.6).*

### La sonda

| # | Che cosa | Dispositivo · versione | Atteso | Misurato | Data |
|---|---|---|---|---|---|
| S1b | durata dell'eccezione su Chrome | ✅ Chrome, versione da annotare | **7 giorni** `[R]` | | |
| S2 | HEVC Main10 **in hardware** | ✅ telefono + PC per `chrome://inspect` | `[?]` — ⛔ *non «sì da Chrome 108»* | | |
| S3a | tastiera, nei tre stati di O8 | ✅ DeX — ⚠ `[?]` **verificare che sia ≥ Android 16 QPR1** | `[?]` | | |
| S5 | tela dichiarata, zoom 100 %/150 % | ✅ telefono + DeX | **uguale nei due**, e = risoluzione fisica | | |
| S7 | segno della rotella, `natural-scroll` nei due stati | ✅ server | `[?]`, e **non deve cambiare** con la gsetting | | |
| S6 | carico utile di un datagram, **sul percorso peggiore** | ✅ telefono su LTE | ≥ **972 byte** | | |
| ⛔ S1a | eccezione ⇒ WebTransport su Safari | ⛔ **niente Mac** | *fuori dalla fase, resta `[?]`* | | |
| ⏳ S3b | PWA su Chrome per Android | ⛔ + certificato vero | *rimandata* | | |
| ⏳ S4 | anello del ritardo del disegno | | *→ fase 3* | | |

### Il filo

| Che cosa | Atteso | Misurato | Data |
|---|---|---|---|
| **B2** — la sessione si apre sui tre motori, per candidata | 3 motori su 3, **e le sei proprietà** | | |
| **B2** — righe di collante, per candidata | *si conta, non si stima* | | |
| **B3** — 1ª · 2ª · 2ª in parallelo · 35 s a timeout 120 · 3ª con chiave ruotata | passa · passa · **rifiutata `0x0F`** · **entra** · passa | | |
| **B4** — sei guaste **+ una conforme**, e il byte giusto | **6 rosse, 1 verde**, byte esatto | | |
| **B5** — le violazioni, e il server vivo dopo ciascuna | motivo giusto sempre, **server vivo sempre** | | |
| **B11** — le violazioni verso la pagina | 12 su 12 | | |
| **B6** — i tre tetti | 5 s · 60 s · 10 s, **col motivo giusto** | | |
| **B7** — otto motivi dal lato che riceve, frasi distinte, nessun numero | 8 su 8 **+ 8 frasi distinte** | | |
| **B8** — ≥ 1 s per campione, **e le tre mediane indistinguibili** | | | |
| **B8** — il controllo 4 · successo · 4 | l'ottavo **non** bloccato | | |
| **B9** — `aioquic` porta WebTransport; la stretta di mano completa | sì; e **l'elenco delle ambiguità trovate** | | |
| **B10** — l'utente `prova` entra, con `pamtester` come controllo | entra | | |
| **B13** — le sei cose | 6 su 6 | | |
| **C1** — dodici guasti costruiti a mano | **12 rossi su 12** | | |
| **C2** — tre modi di fallire | **tre diagnosi diverse** | | |

---

# ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura* (`PIANO.md` §0.3 regola 2). ⭐ **E qui va ogni punto
in cui `RCP.md` ha ammesso due letture**: sono difetti del documento, e questa è la fase in cui
costano meno.

| | |
|---|---|
| ⛔ **la prima stesura del banco, 9 agosto** | 44 rilievi su due revisioni. La forma che si ripete: **cadeva sempre il controllo che dice *no***, e in tre casi era già stato scritto da chi ci era passato prima. ⚠ *Due delle tre amputazioni erano state bocciate da `R2` poche ore prima, con l'istruzione «curare prima di scrivere una riga di banco»: il documento che le doveva ereditare curate le ha ereditate intatte* |

---

# Le decisioni prodotte

*Rimandi, non copie (`PIANO.md` §0.3 regola 1). ⚠ La prima stesura copiava tre passaggi da `RCP.md`
§4.1-bis e da `PIANO.md`, e uno aveva perso il rimando dell'originale (R4.12).*

| | |
|---|---|
| ⏳ `DECISIONI.md` §6.4 | ❓ **aperta**, la chiude **B2** |
| ✅ `DECISIONI.md` §1.8 | ⭐ **Apple è un di più, non un obiettivo** — 9 agosto 2026, dall'utente: S1a esce dalla fase, e la libreria si sceglie su due motori su tre |
| ⏳ `DECISIONI.md` §1.7 | resta aperta solo la comodità su Safari, e nessuno la misurerà per ora |
| ⏳ `DECISIONI.md` §5.0-quater | S5 dice se il numero dichiarato è quello vero |
| ⏳ `RCP.md` §7.3 | S7 toglie il segno dalla rotella dal `[?]` |
| ⏳ `RCP.md` §5.3 | S6 dice se i 5 ms del PCM reggono |
| ✅ `RCP.md` §7.5 | ⭐ **chiusa la notte del 9 agosto**: la funzione di banco — `BANCO_MARCA` e `BANCO_ESITO` — è entrata **prima del primo byte**, sotto la clausola di §9. ⚠ La usa la fase 3; qui se ne prova solo il **rifiuto a funzione spenta** (B5) |
| ⏳ `RCP.md` §4.6 | `[?]` se il tetto parta dal TLS o dall'apertura della sessione (B6) |
| ⏳ `SPECIFICHE.md` §11.5 | l'isolamento fra origini: è un vincolo che questa fase deve rispettare |

---

# Che cosa resta `[?]`

| | |
|---|---|
| quanti **stream al secondo** regga ciascun browser | `RCP.md` §2.3 — banco della **fase 3** |
| **Safari su HTTP/2 e TCP** | l'unico motore che ci ripiega, e il nostro server non lo parla: ⏳ **va deciso** se implementarlo o dichiarare Safari fuori dal ripiego (`web.md` §3.2, O5) |
| ⭐ **S1a — l'eccezione su Safari e su iOS** | ✅ **resta `[?]` per decisione**, non per dimenticanza (`DECISIONI.md` §1.8). ⛔ E finché è `[?]`, *«funziona su iPhone»* **non si scrive nella documentazione del prodotto** |
| i **10 bit** fino allo schermo | tre indizi contrari, nessuno è una misura (`web.md` §1.2 A). Verifica alla **fase 2**, e la prova finale è **guardare una sfumatura** |
| il **pezzo cieco** di S4 | 16-40 ms fra il disegno e il pixel acceso, e nessuna API JavaScript lo vede: la stima **si dichiara accanto a ogni numero** |
| ⭐ **il segno della rotella su più di un compositore** | R3.25: §7.3 vincola cinque desktop, la misura è su Mutter |
| ⭐ **l'istante da cui parte il primo tetto** | R3.27 |
| ⭐ **la pila PAM per un utente diverso dal proprietario del processo** | R3.26 |

---

# Le cure fuori da questo documento

*Tre stonature che le revisioni hanno trovato guardando questo banco, e che stavano altrove. ⛔
Curate lo stesso giorno, o sarebbero rimaste note in un documento.*

| | |
|---|---|
| `RCP.md` §4.1-bis | diceva ancora *«`[S]` WebKit non lo implementa»*, mentre `web.md` §3.1 e `DECISIONI.md` §1.7 erano stati corretti il 9 agosto. ⛔ **È l'arbitro**: chi lo leggeva alla lettera scriveva il ramo sbagliato **restando conforme** (R4.4) |
| `RCP.md` §7.3 | attribuiva al banco della rotella di v1 una tabella di conversione: `LEZIONI.md` §2.3 dice che è costato **una stringa di registro cercata male** (R4.15) |
| `web.md` §3.3, §4.3, §6.3 | i **controlli negativi** che i rapporti prescrivono e che la sintesi aveva perso — è la cura che `R2` aveva ordinato *«prima di scrivere una riga di banco»* (R3.1) |
| `web.md` §8 | la durata dell'eccezione su Chrome era `[?]` in §8 e `[R]` in §3.2, **nello stesso documento** (R4.14) |
| `fasi/00-ambiente.md` | dichiara che l'ambiente della sonda serve *«alla fase 2, non prima»*, mentre `PIANO.md` §1.2 la mette prima di tutto nella fase 1 (R3.14) |
| `PIANO.md` §1.2 | la sonda era di quattro misure e **S4 non è eseguibile in questa fase** |

---

# Il giudizio dell'utente

*La frase vera, con la data. La fase si chiude qui, non quando questo documento è pieno.*

*(la fase è aperta)*
