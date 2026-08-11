# Fase 1 — Il filo nudo

Aperta il **9 agosto 2026** · **Riscritta la sera del 9 agosto**, dopo due revisioni avversariali ·
⭐ **Chiusa l'11 agosto 2026**, sul giudizio dell'utente — la frase, con la scena e il registro, sta
in fondo a questo documento

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

**Che cosa vede l'utente, e giudica**: apre `https://192.168.0.2:7448` nel browser, digita utente e
password, e la pagina dice *«ammesso, sessione nuova, tela 1920×1080, **desktop sconosciuto**»*.
Oppure dice **perché no**, con una frase comprensibile e non un numero (`RCP.md` §8.2).

> ⚠ *Questa riga diceva* «`…:7447` … **desktop GNOME**» *— e il giro dell'utente dell'11 agosto 2026
> l'ha smentita in tutt'e due i punti, con il prodotto acceso davanti.* ⛔ **La 7447 è dell'innesto**:
> il prodotto sta sulla **7448**, e chi eseguiva questa riga alla lettera giudicava il banco invece
> del prodotto. ⛔ **E «GNOME» è una parola che la fase 1 non può dire senza inventarla**: la sessione
> grafica nasce alla fase 2, non c'è nessun compositore a cui chiedere, e `src/rcp.c` lo dichiara per
> iscritto — `SESSIONE` porta `desktop=sconosciuto`. ⇒ **A cambiare è l'atteso, non il codice**:
> era stato scritto prima che il prodotto esistesse. Prova e scena in
> [`rapporti/GIUDIZIO-11-agosto.md`](rapporti/GIUDIZIO-11-agosto.md).

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
| ⛔ **S3a su Firefox** | **Firefox ≥ 151**: `requestFullscreen({keyboardLock})` è entrato nello standard l'8 maggio 2026 e Gecko l'ha spedito **nella 151** `[S]` | ⛔ **no**: il Firefox della macchina da cui si prova è la **140.0** `[M]` 9 ago. ⭐ *Trovato dalla regola B0.6 — annotare la versione esatta — al primo giro in cui è servita: `web.md` §2 dichiara di aver letto Gecko **151-153**, e su questa macchina c'è tre versioni indietro. Chi misurasse S3a qui misurerebbe **l'assenza della lock**, e la scambierebbe per scorciatoie perdute* |
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
| **0.2** | ⛔ **e lo stato che sopravvive è più di uno**: l'eccezione concessa sul certificato della pagina *(che S1a e S1b **misurano**)*, il certificato di sessione già ruotato da B3, **la sessione creata al giro prima** *(che a meno di 30 s fa dare `GIA_ATTIVA_REMOTA` alla prima connessione del giro nuovo — rosso su codice giusto)*, il permesso `clipboard-read`, e ⛔ **il ban di §4.4-bis, che dal 10 agosto 2026 sta su file e quindi sopravvive anche al riavvio del server** — cioè lo stato che sopravvive di più fra tutti | R3.16 |
| **0.3** | ⛔ **l'isolamento fra banchi, e dal 10 agosto 2026 è il vincolo più duro del capitolo**: il conto dei tentativi è **per indirizzo**, e tutti i banchi partono dallo stesso indirizzo. B7 fallisce un tentativo, B8 ne fallisce tre, **e da lì in poi ogni banco di quella macchina è fuori per dodici ore** — compresi B10, B11 e chi sta sviluppando. ⚠ *La riga vecchia diceva «i contatori sono per nome e per indirizzo … si cura cambiando indirizzo o **dichiarando l'attesa**»: con il ban di `DECISIONI.md` §1.9 l'attesa è mezza giornata, e quella cura è morta.* ⛔ **La cura è il comando di sblocco** (§4.4-bis), chiamato fra un banco e l'altro — ⛔ **mai dentro il giro di B8**, o B8 non prova più niente. E ogni banco che lo chiama **lo dichiara**, o «il ban non è scattato» e «qualcuno l'ha tolto» hanno lo stesso aspetto. ⭐ **Lo strumento è `banchi/01-b8-sblocca.py`** — non è un pezzo di B8 — e parla un **socket Unix `0600`**: `SBLOCCA <indirizzo>` → `TOLTO` / `NON-BANNATO`, `PING` → `PONG`. ⛔ Il `PING` **è il denominatore di questa regola**: senza, «il ban non è scattato» e «lo sblocco non è mai arrivato a nessuno» hanno di nuovo lo stesso aspetto. ⚠ *Dalla notte del 10 agosto 2026 **i due server parlano lo stesso protocollo**: prima il prodotto aveva un'opzione `remotix --sblocca IND`, cioè un secondo processo che riscriveva il file mentre il ban vive nella memoria di chi serve — **usciva con 0 dicendo di aver funzionato**, e al primo ban successivo di chiunque altro il ban tolto **tornava anche su disco** (rilievo **R12.1** di `fasi/rapporti/R12-D-cuciture.md`, e l'analisi era scritta per esteso in `01-b3-rcp-innesta.py` da mesi prima che il difetto nascesse). Curato nel codice la stessa notte: `src/comando.c`.* ⛔ **E resta da fare la metà che nessuno ha fatto**: puntare `01-b8-sblocca.py` al prodotto, che oggi non è mai stato provato | R3.8 |
| **0.4** | ⛔ **l'atteso lo confronta il banco, non chi legge**: si stampa *e* si confronta, e lo stato d'uscita è quello del **confronto**. ⚠ E attenzione al punto contro la virgola: `"60"` contro `"60,0"` dà rosso su codice giusto, ed è il difetto ancora aperto di `00-c1-kwin.sh` | R3.18, R3.23 |
| **0.5** | ⛔ **dopo ogni prova che deve far cadere la connessione, il server deve essere ancora lì**: una connessione nuova che arriva fino a `SESSIONE`. «Cade sempre» è soddisfatto anche da un server **ucciso dal nucleo** | R3.3 |
| **0.6** | ⛔ **la versione esatta del browser si annota**, ogni volta. *«Un risultato senza versione, fra sei mesi, non vale niente»* (S1 §4.5) — e questo è il capitolo che invecchia in mesi | R3.16 |
| **0.7** | ⛔ **i due lati si sincronizzano con marcatori, non con `sleep`** — e il precedente in casa **non** è un esempio da copiare: `banco.sh` della fase 0 ha ancora il suo `sleep 2.5` | R3-§4.9 |

---

## Gruppo 1 — Le cinque misure indipendenti dal filo

⛔ **Tutte sul dispositivo vero, mai su un browser di comodo** (`DECISIONI.md` §5-bis.0-ter).
⭐ **E ogni riga porta il rimando puntuale al posto dove vive la procedura** — ⛔ **che per tre di
loro non è un rapporto, e va detto**: `S1a`, `S1b`, `S2`, `S3a`, `S3b` e `S4` sono nate in `web.md`
§7 e **non compaiono in nessuno dei quattro rapporti**, dove le prove si chiamano in quattro modi
incompatibili e due rapporti usano `P1…Pn` per cose di natura opposta (R3.28). ⛔ **`S5`, `S6` e
`S7` invece non sono nate lì**: `[M]` 11 agosto 2026, `grep -cE '\bS5\b|\bS6\b|\bS7\b' web.md` →
**0**, con il controllo positivo accanto (le altre sei etichette compaiono **24** volte nello stesso
file). Sono nate **in questo documento**, dalle domande di `SPECIFICHE.md` §6.1-bis (S5),
`RCP.md` §5.3 (S6) e `RCP.md` §7.3 (S7), e rimandano **lì** perché non esiste un rapporto che le
contenga.

> ⚠ *Questa riga diceva* «le etichette `S1a…S7` **sono nate in `web.md` §7**» *— e §7 di `web.md` ne
> elenca **sei**, non nove. ⛔ Era la riga che **stabilisce la convenzione dei rimandi**, e le due
> righe che la seguono in questo stesso capitolo ne erano la smentita: S5 rimanda a
> `SPECIFICHE.md §6.1-bis`, S7 a `RCP.md §7.3` — cioè non a un rapporto. Corretta l'11 agosto 2026,
> rilievo **R12C.10**. ⭐ E costa poco e vale: tre misure su cinque del Gruppo 1 adesso hanno una
> provenienza, cioè chi le esegue sa da quale lettura sono nate e quale domanda chiudono.*

⛔ **E dalla notte del 10 agosto gli esiti hanno un posto solo dove vivono**:
[`web/rapporti/S-esiti-sonda.md`](../web/rapporti/S-esiti-sonda.md) — la scena, l'ora in UTC, i
registri, e **la ricontata dell'11 agosto che dice quali numeri hanno una provenienza su disco e
quali no**. ⚠ *Fino all'11 agosto quel rapporto non era nominato da **nessuno** dei dieci documenti
(rilievo **R12C.15**): l'unico posto in cui i numeri di quella notte vivevano non era raggiungibile
da nessuna strada di lettura, e la sola via per sapere che esisteva era aprire a caso una cartella di
rapporti.*

### S1b — quanto dura l'eccezione su Chrome  ·  ⏳ **AVVIATA il 10 agosto 2026** · `banchi/01-s1b-eccezione.sh`

> ⚠ *Questa riga rimandava a* `S1 §4.2 P5`. ⛔ **P5 non è questa prova**: è la prova del *contesto
> sicuro* (Service Worker, keyboard lock, appunti, pointer lock, `isSecureContext`), e **in S1 non
> esiste nessuna prova di banco sulla durata** — i sette giorni sono **solo sorgente letto** (S1
> §3.1), e la sola persistenza messa a banco è quella di Safari (S1 §4.3). ⇒ *Non c'era una
> procedura da seguire: ce n'era una da scrivere.* Chi apriva S1 §4.2 P5 per eseguire S1b trovava
> cinque chiamate di API e nessuna procedura, e la spiegazione più naturale è *«ho sbagliato io a
> leggere»*. Corretto l'11 agosto 2026, rilievo **R12C.9** — ed è il terzo rimando di questa forma
> che il progetto paga (R11.2, R11.18).

| | |
|---|---|
| **si misura** | dopo quanti giorni l'avviso ricompare sulla pagina |
| **atteso** | **7 giorni** — `[S]`→`[R]` da `kCertErrorBypassExpirationInSeconds = 604800`. ⚠ **La promozione di marca è dichiarata qui**: `web.md` §8 la teneva ancora `[?]`, e le due righe di `web.md` si contraddicevano (R4.14) |
| ⛔ **il controllo** | **l'impronta del certificato DELLA PAGINA, letta all'inizio e alla fine, deve essere la stessa.** Senza, un certificato rigenerato da un riavvio fa scrivere «l'eccezione è durata quattro giorni» e la frase che si dirà all'utente nasce sbagliata (R3.15) |
| ⚠ **il calendario** | è l'unica misura che richiede **sette giorni di tempo reale**, e la fase non si chiude prima. Se si accelera spostando l'orologio della macchina, ⭐ il controllo diventa *«a sei giorni l'eccezione c'è ancora»* — che è un controllo vero |
| ⏳ **giorno 0 preso, l'orologio è in moto** | `[M]` **2026-08-10T21:10:01Z** — **Chrome 151.0.7922.108**, profilo persistente in `~/.remotix-s1b/profilo`, schermo finto `Xvfb :77 1280x1024x24`, sito `https://192.168.0.2:7452`, certificato **ECDSA P-256 a 3650 giorni** con SAN `IP Address:192.168.0.2` (⛔ **non** `localhost`, che in Chrome ha una corsia riservata, e ⛔ **non** in navigazione privata). Registro `banchi/01-s1b-stato.jsonl`. **Il verdetto è del 17-18 agosto 2026** |
| ⛔ **e un numero che NON regge** | Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z** (`[M]` sul valore grezzo `13431474587889370` µs dal 1601, che è su disco; la conversione è ricalcolata a mano e **dichiarata** tale). ⚠ *Il rapporto scriveva «cioè **604 800 s esatti** dalla concessione», due volte: fra i due numeri che pubblicava ci sono **604 786,889 s**. Mancavano **13,111 s**, e «esatti» era falso in tutt'e due i punti — rilievi **A26** e **R12.6**.* ⛔ **Non si arrotonda e non si rimisura** (rifare il giro «avvia» azzererebbe l'orologio dei sette giorni): che siano 604 800 s dal **clic** è tornata `[?]`, perché **l'istante del clic non l'ha registrato nessuno** |
| ⭐ **quattro controlli, e il quarto è nato dopo** | l'impronta letta **dal filo** dev'essere quella del giorno 0 · un profilo **nuovo** deve vedere l'avviso · il sito dev'essere vivo · ⭐ **il canale di lettura dev'essere certificato** (rilievo **A27**, 11 agosto): il verdetto poggiava su `ssh` + un `grep` che, se rotti, rispondevano **NO** — e il controllo che dice *no* leggeva **lo stesso canale**, quindi si dichiarava passato da sé. Il giro che ne usciva stampava *«a N giorni l'eccezione NON c'è più: è questo il numero di S1b»* — ⛔ **il numero della misura, in verde, da uno strumento muto**, e su un orologio da sette giorni se ne sarebbe accorto qualcuno **fra una settimana** |
| ⛔ **che cosa può rompere l'orologio** | rigenerare `/media/REMOTIX/s1b-certificato/s1b-pagina.pem`, cancellare `~/.remotix-s1b/`, o far cadere la data del server. I primi due li vede il controllo dell'impronta; ⚠ **il terzo no** |

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
| ⛔ **il controllo di prima era rosso sul codice giusto** | diceva *«i due numeri devono differire»*. Ma la tela **giusta** è lo schermo in pixel fisici, e la ragione scritta qui era: *«`screen.width` cala di un terzo, `devicePixelRatio` sale di un mezzo, **il prodotto resta**»*. Una pagina scritta bene dava **1920 e 1920** ⇒ rosso, e chi lo leggeva sarebbe andato a rompere la pagina finché il numero non si muoveva — cioè a **scrivere** il difetto che `DECISIONI.md` §5.0-quater voleva evitare (R3.10) |
| ⭐ **il controllo giusto** | la tela dichiarata a 100 % e a 150 % **deve essere la stessa**, e **deve coincidere con la risoluzione fisica letta fuori dal browser**, nelle impostazioni del dispositivo. Due strumenti diversi sullo stesso fatto |
| ⛔⛔ **MISURATO, e la ragione qui sopra è FALSA su Chrome** | `[M]` **10 agosto 2026**, registro `banchi/01-s5-esiti.jsonl` (due giri identici, 23:13 e 23:14), schermo **Xvfb 1920×1080×24** con `xdpyinfo` a confermarlo da fuori. **Chrome 151.0.7922.108** a zoom 150 %: `screen` resta **1920×1080** e `dpr` sale a 1,5 ⇒ tela **2880×1620**, del **50 % più grande** di quella che esiste. **Firefox 140.13.0esr** a 150 %: `screen` cala a **1280×720** ⇒ tela **1920×1080**, invariante. ⛔ *«Il prodotto resta»* **resta su un motore su due**, e la formula di `SPECIFICHE.md` §6.1-bis non regge su Chrome. ⚠ Corretto l'11 agosto 2026, rilievo **R12C.8** — e il difetto è **di prodotto, non di banco** |
| ⭐ **ed è il controllo giusto che l'ha trovato** | il controllo vecchio (*«i due numeri devono differire»*) sarebbe stato **verde su Chrome e rosso su Firefox**: avrebbe premiato il motore rotto. È la dimostrazione, su un caso vero, che la cura di R3.10 valeva |
| ⚠ **e metà di S5 non è misurata** | il **DeX** non c'era. *«Il Chrome del portatile lo fa»* non dice niente del Chrome del telefono — forma **E10**. La pagina è la stessa (`01-s5-pagina.html`): il giorno che il DeX c'è, si apre quell'indirizzo e si legge la riga |
| ⛔ **e la terza domanda non è chiudibile con una misura** | *«l'arrotondamento può produrre un numero dispari?»* — su un dispositivo si osserva un numero; se è pari **non se ne ricava che i dispari non esistano** (`LEZIONI.md` §1.3). La protezione va **nel programma**, dove **I7** la vuole: la pagina arrotonda al pari per difetto. La misura può solo trovare un positivo |

### S7 — da che parte gira la rotella  ·  `RCP.md §7.3`

| | |
|---|---|
| **si misura** | si inietta `+120` con `libei` in una sessione GNOME (`banchi/00-sessione-gnome.sh`) e si guarda da che parte va la pagina |
| ⭐ **il controllo** | si inietta anche **`-120`**: se la pagina va dalla stessa parte, non si sta misurando il segno. ⭐ *È il controllo meglio scritto della prima stesura, e resta* |
| ⛔ **il controllo che mancava** | si rifà **con `natural-scroll` nei due stati**: se il segno cambia, il numero che finirebbe in `RCP.md` §7.3 è **il segno di una gsetting della sessione di prova**, e il sintomo per l'utente è *«la rotella va al contrario»* su metà delle installazioni. Forma **E11** (R3.25) |
| ⭐⭐ **MISURATA — e il server deve INVERTIRE l'asse verticale** | `[M]` **10 agosto 2026, 20:59:27→20:59:57 UTC**. `ei_device_scroll_discrete(0, **+120**)` → l'evento `wheel` porta **`deltaY = +114`** e la pagina **scende**, cioè va verso la fine del documento; con **−120**, `−114` e sale. `RCP.md` §7.3 fissa l'altra metà — *il client manda `+120` perché l'utente ha girato **in su*** — quindi ⛔ **le due convenzioni sono opposte e il server inverte il segno**. Iniettando il valore com'è, lo schermo remoto scorrerebbe al contrario per **ogni** utente. ⇒ **`RCP.md` §7.3 è chiusa l'11 agosto 2026**, rilievo **R12C.7** |
| **la scena, per intero** | macchina di prova **192.168.0.2**; sessione GNOME senza monitor (`banchi/00-sessione-gnome.sh`), `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; la pagina in **Firefox 140.13.0esr** in `--kiosk`, `dpr` 1, documento posizionato a 8 000 px dal bordo. Registro: `banchi/01-s7-esiti.jsonl`, due giri (`7sd0u7jv`, `oq7jqrdv`) |
| ⚠ **e i controlli non valgono tutti uguale** | `[M]` **nel registro**: il segno opposto, e i due strumenti che concordano (`deltaY` e `scrollY`). ⚠ **A metà**: `natural-scroll` nei due stati — i due giri ci sono e danno lo stesso segno, ⛔ **ma quale giro fosse quale stato non è nel registro**, l'etichetta stava solo a schermo. ⛔ **Non ritrovabile**: che `ei_device_scroll_delta` abbia lo stesso verso — visto, non consegnato |
| `[?]` **e la domanda che resta** | §7.3 vincola **cinque** desktop e la misura è su **Mutter**. Se `libei` normalizza, il numero vale ovunque; se normalizza il compositore, la fase 10 troverà un segno diverso su KWin e non saprà se correggere il protocollo o il server. ⛔ *«Non chiusa»* e *«non misurata»* sono due stati diversi, e questo è il primo: il banco è **rieseguibile su KWin senza cambiare una riga della pagina**. ⚠ La fase 0 ha misurato **tre** famiglie in un pomeriggio: qui la stessa domanda ha una risposta sola |
| ⚠ **e un numero che NON va nel protocollo** | uno scatto (120 unità) vale **114 pixel** su Firefox+Mutter, cioè tre righe. È il fattore di conversione di **quella coppia**, non una costante di RCP: si annota e non si mette in nessuna formula |
| ⚠ **e la lezione citata era quella sbagliata** | il banco della rotella di v1 è costato **una stringa di registro cercata male** (`LEZIONI.md` §2.3), non una tabella col segno sbagliato. Citando la lezione sbagliata **la si perde nel punto in cui si applicherebbe** (R4.15) — la frase è di `RCP.md` §7.3, ed è corretta lì |

---

## Gruppo 2 — B2, il banco della libreria: quale QUIC arriva fino a WebTransport

⛔ **Viene prima di S1a e S6, ed è la cosa che chiude `DECISIONI.md` §6.4** — con un banco davanti,
non su carta. Il criterio è cambiato il 9 agosto: non basta che la libreria parli QUIC, deve
portare **HTTP/3 e WebTransport lato server**, più un ascoltatore **TCP** per la pagina.

**La prova**: un server minimo — cinquanta righe, che si buttano — che accetta una sessione
WebTransport su `/rcp/1`, aperta da **un browser vero**, con l'impronta pubblicata nella pagina.

> ### ⭐ Il censimento del 9 agosto notte, prima di scrivere una riga
>
> *Punto 0 della ricetta, e ha cambiato la domanda.* ⛔ **Nessuna delle due candidate originali
> porta WebTransport lato server**: danno le fondamenta — extended CONNECT, datagram, capsule — e
> non lo strato di sopra. ⭐ **E sono spuntate due candidate che non erano nell'elenco**, una delle
> quali (`lsquic`, in C) **ha WebTransport server dietro un flag di compilazione**.
>
> Il censimento completo, con le marche, sta in `DECISIONI.md` §6.4 — qui non si copia.
> ⛔ **Ed è tutto `[S]` e `[R]`: letto, non misurato.** Serve solo a decidere **a chi vale la pena
> scrivere le cinquanta righe**.

| Candidata | Sul ferro | Che cosa si prova |
|---|---|---|
| ⭐ **`ngtcp2` + `nghttp3`** (MIT, C) | ✅ **costruite dai sorgenti** — `ngtcp2` 16.11.0, `nghttp3` 1.18.90, sullo stesso BoringSSL `[M]`, **e il loro `bsslserver` gira** | ⭐ **passa il criterio dell'SNI** `[M]` 10 ago. Resta da misurare quanto pesa lo strato WebTransport sopra |
| ⭐ **`quiche`** (BSD-2, API C) | ✅ **costruita**, ma alla **0.28.0**: la 0.29.3 pretende `rustc` **1.88** e Trixie ne ha **1.85** `[M]` | ⭐ **passa il criterio dell'SNI** `[M]` 10 ago. ⚠ Porta un costo di **catena di strumenti**, non di QUIC — `DECISIONI.md` §6.4 |
| ⛔ **`lsquic`** (C) | ✅ compilato, **e il collante scritto** (333 righe) `[M]` | ⛔ **ELIMINATA**: in modalità HTTP/3 pretende **SNI** per trovare il certificato, e chi si collega a un **indirizzo IP** non lo manda. È il caso primario del prodotto — `DECISIONI.md` §6.4 |
| ⚠ **`libwtf`** (C su MsQuic) | ⛔ niente | *ultima della fila*: porta dentro una seconda pila QUIC, e ha una **licenza che si contraddice** |

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
| ⭐ **apertura del CANALE DI CONTROLLO** (non «TLS finito», e non l'apertura della sessione — vedi sotto) | `CIAO` | **5 s**, poi `TEMPO_SCADUTO` `0x0D` |
| `ECCOMI` | `CREDENZIALI` | **60 s** |
| `AMMESSO` | `ATTACCA` | **10 s** |

⛔ **Il controllo che distingue i due guasti, ed è il meglio costruito del documento**: se il server
non tiene viva la connessione coi **PING del trasporto**, al trentesimo secondo scatta il tempo di
inattività di QUIC. **Si guarda il motivo**: `TEMPO_SCADUTO` a 60 s è il server che fa il suo
mestiere; una morte a 30 s **senza motivo** è il PING che manca. *R3 ha cercato un terzo caso che
producesse una morte a 30 s con motivo e non l'ha trovato: §3.1 vieta il codice 0 e obbliga il
motivo su ogni chiusura.*

> ### ⭐ R3.27 è CHIUSA, e B6 ha dato DUE risposte — 10-11 agosto 2026
>
> ⚠ *Questo riquadro diceva* «`[?]` … *Da misurare; se confermato, `RCP.md` §4.6 cambia di una
> parola»* — *e la misura era stata presa mentre il riquadro restava `[?]`. La cella «Misurato» di
> B6 in fondo a questo documento era vuota, e i tre numeri vivevano soltanto nel `README.md`, che
> per convenzione riassume e non decide. Chiuso l'11 agosto 2026, rilievi **R12C.11** e
> **R12-A.25**.*
>
> **La domanda era**: *«stretta di mano TLS finita» non è un istante che i due lati condividono.* In
> WebTransport la connessione HTTP/3 e la **sessione** sono due cose separate, e fra i due istanti
> passa almeno un giro di rete — il browser può aver stabilito la connessione molto prima che la
> pagina chiami l'API. ⛔ E il caso peggiore: una seconda sessione su una connessione riusata
> partirebbe **col budget già consumato**.
>
> ⭐ **PRIMA RISPOSTA — il cronometro parte dall'apertura del CANALE DI CONTROLLO**, e non sono due
> parole per la stessa cosa: né la fine del TLS né l'apertura della **sessione**. È l'istante che il
> server osserva davvero, ed è quel che il codice fa (la sessione RCP nasce quando il canale si apre,
> e il tetto si conta da lì). ⇒ **`RCP.md` §4.6 riga 1 è cambiata di una parola**, l'11 agosto 2026.
> B6 lo dice con due casi costruiti apposta — `ciao-senza-controllo` e `ciao-sessione-tardiva` — e
> **non** lo consegna come un rosso del server: ha un esito suo, il **3**, che vuol dire *«il filo si
> comporta come il codice dice, e il documento dice un'altra cosa»*.
>
> ⛔ **SECONDA RISPOSTA — e curare la parola NON BASTA.** Se il cronometro parte dall'apertura del
> canale, chi apre la **sessione** WebTransport e **non apre mai il canale** non ha addosso **nessun
> tetto**: resta lì, viva e senza scadenza. È esattamente la connessione che *«tiene un posto e non
> lo dichiara a nessuno»*, cioè la prima riga di §4.6 — **sopravvissuta alla cura**. §4.6 non ha una
> riga per quello stato: la tabella comincia da *«`CIAO` ricevuto»*, e prima del `CIAO` c'è uno stato
> in cui il server non conta niente.
> ⚠ Lo copre solo il tempo di inattività di QUIC — **30 secondi di silenzio** — e chi tiene aperta la
> sessione scrivendo su un altro stream non è silenzioso, quindi non scade **mai**.
> ⛔ **Che tetto darle, e da che istante, è una domanda aperta e non una svista**: `DECISIONI.md`
> §7.17, ❓, con le due letture e il caso concreto. Un banco che avesse stampato **una riga sola**
> per le due risposte avrebbe consegnato la metà facile.
>
> ⚠ **E i tre numeri di B6 — 5,0 · 60,1 · 10,0 s — non hanno un registro.** Girano, e l'uscita è a
> schermo: non esiste nessun `.jsonl` di B6, quindi la scena di quel giro non è ricostruibile e i
> numeri non sono riverificabili. Stanno in fondo a questo documento con quel che se ne sa
> **e con quel che non se ne sa**.

### B7 — il congedo, verificato dal lato che riceve

⛔ **Mai dal registro di chi lo manda**: in v1, per **tre fasi**, il server scriveva «congedo il
client» mentre il client scriveva «errore di rete» (`LEZIONI.md` §1.7).

⛔ **Il denominatore è quindici, e i provocabili in questa fase sono SETTE** — `CHIUSO_DALL_UTENTE`,
`VERSIONE_INCOMPATIBILE`, `NIENTE_IN_COMUNE`, `ERRORE_PROTOCOLLO`, `TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`. Per ciascuno si verifica il `CONGEDO` **e** il codice
nella chiusura.

> ⚠ *Questa riga diceva* «Per ciascuno degli **otto** motivi che questa fase sa produrre … `SERVER_IN_CHIUSURA`»
> *e più sotto «le **otto** frasi devono essere distinte». ⛔ Era falsa in tutt'e due i sensi, e il
> banco lo aveva **misurato e scritto** — `banchi/01-b7-congedo.py`, tabella `ESCLUSI`, voce `0x0C`:*
> «il server della fase 1 non ha un percorso di spegnimento: `RCP_SERVER_IN_CHIUSURA` è dichiarato in
> `rcp.h` e non compare in nessuna riga di `rcp.c`. ⚠ MISURATO col grep, non supposto — **e
> contraddice `fasi/01-filo-nudo.md` B7**». *Corretta l'11 agosto 2026, rilievo **R12C.6**.*
>
> ⛔ **E il denominatore vero è QUINDICI, non otto**: §8.2 ha quindici motivi. Scrivere «8 su 8»
> scegliendo gli otto che si sanno provocare è vero **per costruzione**, ed è la forma di verde più
> vuota che ci sia. Gli **otto esclusi** stanno in `ESCLUSI` con la ragione di ciascuno, e
> `certifica_denominatore()` verifica che 7 + 8 = 15 invece di fidarsi: `0x02` e `0x03` sono orologi
> della sessione (fase 5) · `0x04` e `0x05` vogliono una sessione grafica locale (fase 2) · `0x06`
> vuole la capacità di codifica (fase 3) · `0x07` e `0x08` **non viaggiano in un `CONGEDO`** ma in
> `RESPINTO` (§4.4), e provocare `0x08` bannerebbe l'indirizzo del banco (B0.3) · `0x0C` per il
> percorso di spegnimento che manca.
>
> ⭐ **E `0x0C` è cambiato di soggetto la notte del 10 agosto, ed è il primo posto in cui i due
> server divergono in modo visibile**: **il prodotto** un percorso di spegnimento adesso ce l'ha —
> `src/main.c` congeda tutti con `SERVER_IN_CHIUSURA` prima di uscire — mentre **l'innesto**, che è
> quello che B7 accende, no (`grep`: zero occorrenze in `01-b3-rcp-innesta.py`). ⛔ Quindi i
> provocabili restano **sette contro il bersaglio che B7 misura**, e diventano **otto il giorno in
> cui B7 sarà puntato al prodotto**. Il numero da scrivere accanto a un esito è quello del bersaglio
> che si è acceso.

| | |
|---|---|
| ⛔ **«tante su tante» non basta, e la prima stesura si fermava lì** | una `switch` col ramo predefinito — `mostra("Errore " + codice)` — dà una stringa non vuota per **ogni** motivo, e quindi il conto torna sempre. L'utente legge *«Errore 14»* per `SESSIONE_NON_SERVIBILE`, che §8.2 vieta con un ⛔ e un esempio quasi identico (R3.20) |
| ⭐ **i due criteri che rendono la riga misurabile** | le frasi devono essere **distinte fra loro** — ⛔ **tutte e quindici**, non solo le sette provocabili: la frase la costruisce il client dal codice, quindi si legge senza provocare il motivo — e ⛔ **nessuna deve contenere il numero del motivo** né «errore» seguito da una cifra. Un `grep` di due righe |
| ⚠ **e «il banco guarda lo schermo» non è eseguibile** | o si legge il DOM — l'unica cosa che una prova automatica può fare — **oppure è l'utente** (I8), e allora la riga va nel **giudizio**, non in una tabella con un «tante su tante». Dichiarato, così che nessuno la legga come già coperta |
| ⚠ **i due motivi che NON viaggiano in un `CONGEDO`** | `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` stanno in `RESPINTO` (§4.4, rilievo R1.18): un banco che li cercasse in un `CONGEDO` **fallirebbe per costruzione** |
| ⛔ **il `dettaglio` non si mostra** | è per il registro (§8.2) |

### B8 — il secondo fisso, e il ban dell'indirizzo

> ⛔ **Riscritto il 10 agosto 2026, dopo che l'utente ha sostituito la forma della limitazione**
> (`DECISIONI.md` §1.9): tre autenticazioni fallite dallo stesso indirizzo ⛔ **dentro una finestra
> di 5 minuti**, e quell'indirizzo è fuori per **12 ore**. Cadono con la regola vecchia il raddoppio della finestra, la
> scadenza a 30 minuti di quiete e **il contatore per nome utente**; ⭐ **e cade il controllo che
> teneva fermo questo banco** — *«quattro falliti · uno riuscito · altri quattro»* non è più
> eseguibile, perché dopo il terzo fallito non esiste nessun quinto tentativo.
>
> ⚠ *E il rosso del 10 agosto va riletto con la regola nuova prima di indagarlo: il quinto tentativo
> — quello con le credenziali buone — aveva ricevuto `CREDENZIALI_ERRATE` `0x07` e **non**
> `TROPPI_TENTATIVI` `0x08`. §4.4-bis rifiuta **senza interrogare PAM**, quindi non ha modo di dire
> «errate»: il motivo sul filo accusa **la gamba del banco**, non il limitatore. Il controllo si
> riscrive comunque da capo, e la mezz'ora si spende su quello nuovo.*

⭐ **È un banco che vede due proprietà che nessun altro vede**, e una regressione che le togliesse non
farebbe fallire niente.

**Il secondo fisso** — invariato, la regola non l'ha toccato:

| | |
|---|---|
| ⛔ **il criterio NON è «≥ 1 s», ed è la cura più importante di questo banco** | `pam_authenticate(); sleep(1); rispondi();` dà **1,001 · 1,050 · 1,300 s** nei tre casi: **tre righe verdi**, e la distinzione che §4.4 vieta di scrivere nel motivo si legge col cronometro **esattamente come prima**. Il banco che si dichiara *«l'unico che vede questa proprietà»* non la vedeva (R3.2) |
| ⭐ **il criterio giusto è di forma diversa, non di soglia diversa** | ⛔ **le mediane dei tre casi differiscono meno del rumore della misura** — molti campioni per caso, non uno. Con un campione i cinquanta millisecondi che separano «utente inesistente» da «password sbagliata» non sono nemmeno visibili. **Atteso: ≥ 1 s in ogni campione, e le tre mediane indistinguibili** |
| ⛔ **e i campioni adesso costano** | tre per indirizzo, poi il ban. Le mediane vogliono **molti** campioni per caso, quindi il banco deve **variare l'indirizzo di provenienza** o sbloccare fra un blocco e l'altro — ⛔ **e dichiarare quale delle due fa**, perché cambiano quel che la misura sta misurando |
| ⚠ **e il `[?]` che questo banco ha già trovato** | `[M]` 10 agosto: mediana **2636 ms** sui respinti, dove §4.4-bis vuole ~1000. ⛔ **A governare i tempi è PAM, non noi**, e finché quel ritardo non è costante il secondo fisso non nasconde quel che dichiara di nascondere. Il ban **non** chiude questa `[?]` |

**Il ban** — nuovo, e sostituisce tutte le righe del limitatore:

> ⛔ **LA FINESTRA DI CINQUE MINUTI, che questa sezione non nominava.**
>
> ⚠ *Il riquadro qui sopra e la tabella che segue dicevano* «tre autenticazioni fallite
> **consecutive** dallo stesso indirizzo», *senza finestra — e «consecutive» era la **prima**
> formulazione dell'utente, stretta lo stesso giorno da una **terza** frase:* «i 3 tentativi falliti
> devono avvenire **entro i 5 minuti** per far scattare il ban» *(`DECISIONI.md` §1.9). La finestra
> era in `DECISIONI.md`, in `RCP.md` §4.4-bis, in `SPECIFICHE.md` §4.2 e nel codice
> (`#define FINESTRA 300000u`) — e mancava nei **due** documenti da cui si scrive il banco.
> Corretto l'11 agosto 2026, rilievo **R12C.5**.*
>
> ⛔ **Perché morde sul banco e non sulla carta**: le due regole danno **esiti opposti sullo stesso
> ingresso**. Tre fallimenti alle 0:00, 4:00 e 8:00 sono *consecutivi* ⇒ bannati secondo la riga
> vecchia, e **fuori finestra** ⇒ non bannati secondo il codice. Un banco scritto da qui che spaziasse
> i tre tentativi darebbe **rosso sul codice giusto**, che è la forma di `LEZIONI.md` §2.3.
> ⚠ E la ragione per cui è successo è quella che il `README.md` vieta: la decisione era **copiata** in
> quattro documenti invece che rimandata, e le quattro copie non erano uguali.
>
> ⚠ **La finestra è scorrevole**: si guarda l'ora degli **ultimi tre** fallimenti, non si riparte dal
> primo. Ancorandola al primo, tre fallimenti a 0:00 · 4:59 · 5:01 farebbero ripartire il conto da
> uno, e chi prova a un ritmo appena più lento della finestra non verrebbe **mai** fermato.
> ⇒ **La decisione sta in `DECISIONI.md` §1.9 e qui non si copia**: questa è la sua conseguenza sul
> banco.

| | Atteso |
|---|---|
| ⛔ tre autenticazioni fallite dallo stesso indirizzo, **dentro 5 minuti** | le prime tre rispondono `RESPINTO(CREDENZIALI_ERRATE)`, ciascuna **non prima di un secondo** |
| ⭐ **il quarto controllo che dice *no*, ed è nuovo: FUORI dalla finestra il ban NON scatta** | tre fallimenti spaziati di più di 5 minuti ⇒ **nessun ban**, e il quarto tentativo con la parola giusta **entra**. ⛔ Senza, «il ban scatta al quarto» è compatibile con un server che non guarda l'orologio, e la riga di `DECISIONI.md` §1.9 che protegge *«chi sbaglia a digitare ogni tanto»* non è provata da nessuno |
| ⛔ **il quarto tentativo, con la parola d'ordine GIUSTA** | ⛔ **rifiutato lo stesso**, e la pagina lo **dice**: `TROPPI_TENTATIVI`. ⭐ *È la riga che distingue un ban da un contatore, ed è anche il sintomo che l'utente vedrà — «l'ho scritta giusta e non mi fa entrare» — quindi è voluto e va provato, non evitato* |
| ⛔ **e i tre nomi utente DEVONO essere diversi** | ⚠ Con lo stesso nome tre volte, un server che avesse ancora il contatore **per nome** della forma vecchia darebbe verde: il banco proverebbe la regola sbagliata. È la stessa forma con cui **B5** ha trovato il contatore chiavato sulla porta |
| ⭐ **il controllo che dice *no*, primo**: un **altro** indirizzo | entra **subito**, con le credenziali buone. Senza, «il quarto è rifiutato» è compatibile con un server che ha smesso di funzionare |
| ⭐ **il controllo che dice *no*, secondo**: l'azzeramento | **due** falliti · **uno riuscito** · **due** falliti ⇒ il terzo fallito **non** banna. Se il successo non azzerasse, il secondo blocco sarebbe già scattato. ⚠ *È il controllo di R3.9 nella forma che la regola nuova rende eseguibile: prima serviva un quinto tentativo che non esiste più* |
| ⭐ **il controllo che dice *no*, terzo**: la persistenza | si banna, **si riavvia il server**, e l'indirizzo **è ancora bannato**. ⛔ Senza, il ban vive in memoria e un aggiornamento del pacchetto regala tre tentativi a chiunque — è l'invariante **I7** |
| **quel che l'utente vede** | ⛔ la **pagina si carica** e dice che i tentativi sono esauriti (§4.4-bis). Si legge il DOM, come per le otto frasi di B7: un banco non guarda uno schermo |
| **e la scheda già aperta** | la sessione WebTransport si rifiuta con `TROPPI_TENTATIVI` nel codice della chiusura, verificato **dal lato che riceve** |
| **lo sblocco** | il comando toglie il ban, **lo scrive nel registro**, e l'indirizzo rientra. ⛔ **Questa riga si prova in fondo**, non all'inizio: uno sblocco chiamato dentro il giro fa passare tutto il resto per costruzione (B0.3) |

⛔ **E `TROPPI_TENTATIVI` non viaggia in un `CONGEDO`, viaggia in `RESPINTO`** (§4.4, rilievo R1.18):
un banco che lo cercasse in un congedo fallirebbe per costruzione, e chi lo scrive penserebbe di
aver sbagliato lui.

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

> ### ⭐⭐ IL BANCO ESISTE DALL'11 AGOSTO 2026, SERA — e si è certificato nello stesso giro
>
> *Era l'unico dei dodici **mai provato**, e il motivo era che non c'era: `banchi/01-b10-secondo-utente.py`
> e `banchi/01-b10-lancia.sh`. ⭐ Il banco **importa** `01-b3-cliente.py` come modulo invece di
> copiarlo: misura RCP col secondo lettore, e la parola non passa da nessun `argv`.*
>
> | | |
> |---|---|
> | ⭐ **l'atteso è misurato** | **`prova2`** — dal provisioning, non a mano — arriva a `SESSIONE` sul **PRODOTTO**: `AMMESSO` a **1001-1059 ms** (il secondo fisso di §4.4-bis), stretta intera **1213-1261 ms**. `[M]` **11 agosto 2026, 13:08 UTC**, NIC-OS, porta **7491**, binario md5 `9dcb9657…`. Registro `banchi/b10-esiti-prodotto.jsonl` |
> | ⛔ **chi possiede il processo è DICHIARATO** | **`root`, uid effettivo 0** — letto da `/proc/<pid>/status`, non supposto — cioè **di sistema**, come §5.5 vuole. ⭐ E il banco verifica di **non essere vacuo**: se il server girasse come l'utente della prova esce **2**, *«non ho potuto misurare»*, invece di stampare un verde che non significa niente |
> | ⛔ **le quattro cause si distinguono, e con tre osservazioni** | *(1)* **la guardia** — il server rifiuta **e nel suo registro non c'è nessuna riga di `autenticazione.c`**: PAM non è stata nemmeno interrogata; *(2)* **il contatore per indirizzo** — il motivo sul filo è `TROPPI_TENTATIVI` `0x08`, e allora il banco **sblocca dichiarandolo e riprova**, o (2) coprirebbe (1); *(3)* **la pila PAM** — `pamtester` fallisce con la stessa parola; *(4)* **l'utente** — `getent passwd` e `getent shadow` |
> | ⭐ **il controllo che costa dieci secondi, e il suo negativo** | `pamtester remotix prova2 authenticate` **riesce** — ⛔ sul servizio **`remotix`**, non `login` — e con la parola sbagliata **fallisce**: senza il secondo, il primo non varrebbe niente |
> | ⭐⭐ **e la `[?]` R3.26 è MISURATA** | da un utente **non privilegiato** la verifica della parola di **un altro** utente **fallisce**; da **root riesce**. ⇒ **la pila PAM giudica un altro utente solo se il processo è privilegiato**. Il server oggi è di root e ci riesce; ⛔ un servizio di sistema che **lasciasse i privilegi** vedrebbe la causa (3), e il sintomo sarebbe di nuovo *«credenziali errate»* — è la domanda che la fase 2 si porta dietro |
> | ⭐ **due utenti, non uno** | dopo il respinto, **`prova`** arriva a `SESSIONE`: è insieme **B0.5** (il server è ancora lì) e §5.5 (due utenti diversi, **nessuno dei due** proprietario del processo) |
> | ⛔ **la parola generata non passa da nessuna riga di comando** | il compromesso che il `README.md` dichiarava **non accettato** è chiuso: la parola si legge da `credenziali-banchi`, si scrive con un **builtin** in un file `0600`, arriva come `--parola-file`, e una `trap` la cancella. ⚠ Resta una copia su disco per la durata del giro, ed è dichiarata |
>
> ⭐ **CERTIFICATO — `0 → 1 → 0`** `[M]` 11 agosto, **15:09 UTC**. Il guasto **rimette la guardia di
> v1** — `getpwuid(geteuid())` e il confronto col nome, **prima** di `pam_start` — su una **copia
> intera** dell'albero del prodotto, ⛔ **mai su `src/remotix`**: gli altri banchi lo stavano
> misurando in quegli stessi minuti, e per un quarto d'ora avrebbero avuto sotto i piedi un server
> bugiardo. Marca **`CAUSA-1-GUARDIA-PRE-PAM`: 2 nel giro guasto, 0 nei due giri sani**.
>
> ⛔ **E il guasto in catalogo non guastava niente.** L'appiglio `autenticazione_utente_atteso` era
> puntato su un file dove compare **solo dentro un commento**: il sostituto ci appiccicava accanto la
> marca e il codice compilato restava **identico byte per byte**. ⚠ **È la terza volta in un giorno**
> che un appiglio di commento fa credere di aver guastato qualcosa — dopo B5 e B3 — ed è la forma che
> costa di più, perché il giro *sembra* una certificazione riuscita.
>
> ⚠ **B10 non passa da `01-b12-lancia.sh`**: il suo guasto si ricostruisce con
> `GEMELLO=nessuno <copia>/costruisci.sh`, mentre `attrezzi-misura-marca.sh` sa fare solo
> `ninja … bsslserver`, cioè **l'innesto**. Finché `gira()` non impara a costruire il **prodotto**,
> la certificazione si fa dal lanciatore del banco — ed è la stessa lacuna del punto 4 dell'elenco.
>
> ⛔ **E quel che B10 NON prova**: il caso dell'utente **proprietario** del processo. `root` non ha
> una parola d'ordine nota nel contenitore, quindi *«con la guardia rimessa entra solo root»* è
> **dedotto, non misurato**. ⚠ E B10 è provato solo contro il **prodotto**, mai contro l'innesto.

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

> ### ⭐ IL GIRO DELL'11 AGOSTO, POMERIGGIO — e la prima cosa da dire è che il conto di stamattina era già scaduto
>
> ⛔ **Nessuno dei tre certificati valeva più.** Il registro porta, accanto a ogni certificazione,
> l'impronta di `rcp.c` con cui è stata fatta: **`d839839f…`**. Oggi `rcp.c` è **`cb7af778…`** —
> l'hanno cambiato le cure del 10-11 agosto. ⇒ *«3 su 12»* era **3 su 12 su un codice che non esiste
> più**, ed è esattamente ciò che il registro dice quando lo si legge invece di leggerne il totale.
>
> ⚠ ⛔ **E la prova qui sopra è scritta in due alfabeti, cioè non si rifà** — trovato la sera dell'11
> agosto. `d839839f…` è un **sha256 troncato** (il registro lo scrive per esteso); `cb7af778…` è un
> **md5**. Il `sha256` di `rcp.c` oggi è **`84411b9c…`**. ⇒ La **conclusione regge** — il codice è
> cambiato davvero, `d839839f…` → `84411b9c…` — ma **il confronto stampato mette a paragone due
> funzioni diverse**, e chi lo rifacesse domani troverebbe due numeri che non c'entrano niente e non
> saprebbe se ha sbagliato lui. ⭐ *Un'impronta senza il nome della funzione è la stessa cosa di un
> numero senza unità di misura.*
>
> | Banco | Oggi | Come |
> |---|---|---|
> | **B4** | ⭐ **certificato** | `0 → 1 → 0`, marca «⛔ atteso il byte» |
> | **C2** | ⭐ **certificato** | `0 → 1 → 0`, marca «IRRAGGIUNGIBILE» |
> | **B9** | ⭐ **certificato** | `0 → 3 → 0`, marca «il testo è cambiato sotto il banco». ⭐ **Ma prima ha trovato un difetto vero, e nostro**: il giro sano usciva **3**, perché la voce **L6** citava la vecchia riga 1 di `RCP.md` §4.6 — quella che partiva dalla fine del TLS — e **l'abbiamo corretta noi** l'11 agosto sulla misura di B6. ⛔ Nessun altro banco se ne sarebbe accorto: gli altri sarebbero diventati **più verdi**, non meno. La `[?]` R3.27 è ora registrata come **DECISA**, che non è «sparita» |
> | **B7** | ⭐ **certificato** | `0 → 1 → 0`, marca «il motivo nel `CONGEDO` sul canale: assente» — ⛔ e la riserva del 10 agosto (*«marca non discriminante, 37 occorrenze»*) **è chiusa**: la marca di oggi nel giro sano non compare |
> | **B6** | ⭐ **certificato — e non era mai stato provato** | `0 → 1 → 0`, marca «⭐ nessuna caduta», cioè la riga che solo un caso `-presto` **caduto** può produrre. Il guasto porta `TETTO_CIAO` da 5000 a 500 ms: ⭐ *la metà del requisito che nessuno scrive è «non prima»* |
> | ⭐ **B5** | ⭐ **certificato — e non era mai stato provato** | `0 → 1 → 0`, marca «§3.1 punto 3 su «capacita-ripetuta»». ⛔ Il guasto in catalogo **non rompeva niente**: l'appiglio era una stringa di *commento* e il sostituto ci appiccicava accanto la marca — il codice compilato restava identico byte per byte. Rifatto sul **ramo**: `if (ripetuto)` spento, `congeda()` mai chiamato |
> | ⛔ **B8** | ⛔ **provato e NON certificato**, e il motivo è cambiato — *poi **certificato la sera dello stesso giorno**, vedi in fondo alla sezione* | vedi il riquadro qui sotto |
> | ⭐ **B3** | ⭐ **certificato — e non era mai stato provato** | `0 → 2 → 0`, marca «`CONGEDO invece di SESSIONE: motivo 0x0f = GIA_ATTIVA_REMOTA`». ⛔ L'appiglio in catalogo aveva **due** spazi di rientro dove il file ne ha **quattro**: compariva **zero** volte, e il guasto non si sarebbe innestato. ⭐ Il sintomo col guasto è quello di v1 alla lettera: la prima connessione passa, la seconda si vede rifiutare perché il posto della prima non si è liberato |
> | ⭐ **B2** | ⭐ **certificato — e ha trovato un difetto vero prima di lasciarsi certificare** | `0 → 1 → 0`, marca «`- credito uni DISPONIBILE a RCP all'apertura`». Vedi il riquadro |
> | ⭐ **B11** | ⭐ **certificato dal PROPRIO giro** | **CONFORME, 0 punti** contro il server guasto; **NON-CONFORME, 9 punti** contro quello sano — il controllo che dice *no*. ⚠ Riserva scritta: **un motore solo**. Vedi il riquadro |
> | **B13** | ⛔ **non certificabile, e il motivo ha un nome** | vedi il riquadro qui sotto |
>
> ⇒ ⭐ **9 certificati su 12 sul codice di oggi**, contro **3 su 12 su un codice che non c'è più**.
> ⚠ Restano **due provati e non certificati** — **B8** e **B13**, tutt'e due su lacune con un nome,
> non su capricci dello strumento — e **uno mai provato**, **B10**. ⛔ Nessuno dei tre è «pulito».
>
> ⛔ **E questa riga ha portato «5» per mezza giornata mentre il registro diceva 8** — R12-A.49.
> Due aggiornamenti di questo file erano andati a vuoto **in silenzio**, perché una sostituzione di
> testo non protesta quando non trova, e lo script diceva «fatto» lo stesso. ⭐ È la forma «il
> denominatore non lo guarda nessuno», applicata a un documento invece che a un banco: adesso ogni
> sostituzione si verifica, e chi non trova l'ancora **si ferma**.
>
> ⚠ **E il numero dipende da dove lo si chiede — R12-A.36.** Il registro viveva in **due copie**,
> una per macchina, e nessuna delle due sapeva dell'altra: il server dava «B9 NON certificato»
> mentre sul portatile B9 era certificato da un'ora. ⭐ Unite (il file è quello versionato,
> `banchi/01-b12-registro.jsonl`, e la copia del server ne è ora un riflesso). ⛔ Ma anche unite, il
> server dice **4 su 12** e il portatile **5 su 12**, e ⭐ **hanno ragione tutt'e due**: sul server
> `RCP.md` non c'è, quindi la certificazione di B9 non si può *riverificare* lì — e lo strumento
> scrive *«non si può dire se valga oggi»* invece di arrotondarlo a «certificato». ⇒ Il numero è
> **5**, e va detto **dove** si legge.
> ⚠ E i due che restano provabili subito sono **B5** e **B8**, tutt'e due fermi sulla **marca
> mancante**; **B2** costa una ricostruzione intera; **B3** e **B11** la marca non ce l'hanno;
> **B10** non ha nemmeno il banco.
>
> #### ⭐⭐ `01-b0-terreno.sh` — il controllo che guarda SOTTO i banchi
>
> *Nato l'11 agosto 2026, rilievo **R12-A.46**. Non muove il conto di un punto, e protegge tutti.*
>
> ⛔ **Due volte nello stesso giorno un banco è stato verde su un terreno che non era quello che
> credevamo**, e in tutt'e due i casi il banco non aveva nessun motivo di accorgersene: l'innesto
> RCP sparito da `examples/` (**R12-A.45**) e l'utente `prova` che non lo creava nessuno
> (**R12-A.44**). ⚠ Nel primo caso **la certificazione di B2 è passata lo stesso** — la sua sonda
> legge i parametri QUIC e di RCP non sa niente. ⭐ **L'ho preso per caso**, mentre provavo un'altra
> cosa: senza quella coincidenza starebbe nel registro, datato, e sbagliato in un modo che nessuno
> ritrova.
>
> ⇒ Gira **prima** di ogni giro di certificazione e guarda **14 cose**: i due innesti al loro posto
> in tutt'e due i file che se li contendono · i tre file che B3 copia dentro `examples/` · che
> `examples/rcp.c` sia **identico** a `rcp/rcp.c` · che nessun guasto di B12 o di B11 sia rimasto
> addosso · ⭐ e che **il binario sia più nuovo di tutti i sorgenti che dichiara**. Se non regge, B12
> **non certifica e non scrive nel registro**.
>
> ⭐ **E si è fatto dire di no tre volte prima di essere creduto**: con un guasto di B12 lasciato
> addosso → rosso; con un pezzo dell'innesto tolto → rosso; e ⭐ **la terza non l'avevo preparata** —
> il mio stesso giro di prova aveva lasciato `rcp.c` più nuovo del binario, cioè *sorgente sano e
> binario vecchio*, la trappola **R12-A.6** in persona. Il controllo l'ha trovata da solo.
>
> ⚠ **Che cosa non dimostra**: che il server sia *corretto*. Dimostra che è **quello dichiarato** —
> cioè che i banchi cerchino nel posto giusto. Un server può passare tutti e 14 ed essere pieno di
> difetti: quelli sono il mestiere dei banchi.
>
> ⛔ E la prima stesura sbagliava **nella stessa forma curata quella mattina su S1b** (A31): `grep
> -c` esce **1** quando non trova niente — che è la risposta «zero», non un errore — e il `|| printf
> '?'` ci appiccicava un `?` dopo lo zero già stampato. **Cinque falsi rossi in un colpo, dentro il
> file che esiste per impedirli.**

> #### ⛔⭐ Tre falsi rossi, tutti prodotti da B12 stesso — e sono la parte che vale
>
> **R12-A.31 — B12 certificava dove non poteva.** Il lanciatore avvertiva *«B9 e B4 si certificano
> dove stanno i loro file»* e poi li lanciava lo stesso. `[M]`: sul server **`RCP.md` non esiste** —
> lì arrivano i banchi, non i documenti — B9 è uscito **4** e il registro ha scritto **«B9 NON
> certificato»**. ⛔ È **la forma opposta del falso verde**, e costa uguale: un banco sano marchiato
> rosso manda a cercare un difetto che non c'è, e il registro se lo porta dietro con una data.
> ⭐ Cura: `--provabile` guarda se i file su cui la certificazione poggia ci sono, e il lanciatore si
> **rifiuta** invece di misurare. *«Non posso provarlo qui»* e *«l'ho provato e non passa»* sono due
> fatti.
>
> **R12-A.32 — B6 era certificabile, e l'obiezione in catalogo non reggeva.** Diceva che il guasto
> non si può innestare perché *«`01-b6-lancia.sh` ricopia il sorgente a ogni giro»*. ⭐ Tutt'e due le
> metà dell'obiezione parlano del **lanciatore**, e **B12 non lo usa**: chiama il programma del
> banco. Aggiunta la riga di comando, coi tetti **letti** dal sorgente compilato invece che scritti a
> mano. ⚠ E va detto che cosa questa certificazione **non** copre: certifica `01-b6-tetti.py`, non il
> confronto sorgente/binario che sta nel lanciatore.
>
> **R12-A.33 — `--bersaglio` è diventato obbligatorio e i chiamanti sono rimasti indietro. Tre volte
> in due giorni.** Il 10 agosto su `01-b6-lancia.sh` e `01-b3-quarto-giro.sh`; oggi su
> `01-b12-lancia.sh`, che chiamava B7 **senza `--bersaglio`** e con un `--sorgente` che non esiste
> più: il giro ha scritto **«B7 NON certificato»** su un banco sano.
>
> ⭐ **Da cui un banco nuovo: `banchi/01-b0-chiamate.py`** — *chi chiama un banco gli passa quel che
> il banco pretende?* Legge gli `add_argument` con l'AST, scioglie le variabili di shell definite nel
> file, e distingue **tre** esiti: approvata · rotta · **IGNOTA** (una variabile che potrebbe
> nascondere il nome di un'opzione). Ha subito trovato **R12-A.33-bis**: `01-b8-lancia.sh` chiamava
> il cronometro senza `--bersaglio` né `--porta`, quindi il passo *«che cosa mi aspetto, prima di
> misurare»* stampava da giorni **un messaggio d'uso di argparse** — e non faceva fallire niente.
>
> ⛔ **E scriverlo ha insegnato quattro cose, tutte misurate, tutte sullo stesso tema:**
> · accusava **21** righe di *esempio* dentro le spiegazioni. ⭐ Un controllo che grida sul falso non
>   viene ignorato meno di uno che tace: viene ignorato **insieme ai suoi veri**;
> · un filtro troppo stretto ha fatto sparire le chiamate `python3 -u` **in silenzio** — le viste
>   sono passate da **83 a 22** e il conto sembrava soltanto più pulito. ⛔ Una copertura che cala
>   senza dirlo è un banco che smette di guardare, e si vede **solo dal denominatore**;
> · *«c'è un `$` ⇒ ignota»* rendeva ignote **26 righe su 34**, ⛔ compresa quella che aveva appena
>   rotto B7. La domanda giusta non è «c'è una variabile», è **«quella variabile può nascondere il
>   nome di un'opzione?»**;
> · ⭐⭐ e il più istruttivo: unendo le opzioni del modulo condiviso avevo preso quelle **ammesse** e
>   non quelle **pretese**. Risultato: la riga per B6 che avevo appena scritto — **senza
>   `--bersaglio`** — il controllo l'ha dichiarata **approvata**, e il giro di certificazione ha
>   scritto «B6 NON certificato» su un errore mio che lo strumento nato per trovarlo aveva guardato e
>   promosso. ⛔ **Allargare le maglie per far tacere i falsi si porta via i veri nella stessa
>   mossa**, e non si vede, perché il conto dei rossi scende — che è precisamente l'aspetto di un
>   progresso.
>
> ⚠ E le tre accuse superstiti **le ho lanciate davvero** invece di dedurle: due erano false (B7 ha
> una scorciatoia `--elenco` prima di `parse_args`) e una vera. Curarle tutt'e tre avrebbe rotto due
> chiamate funzionanti per far tacere il mio stesso strumento.
>
> #### ⭐⭐ B11: certificato — e il difetto era una CORSA, non una divergenza
>
> ⚠ Non era «mai provato»: era **mai lanciato**. E va lanciato **dalla macchina di chi guarda**, non
> dal server — `01-b11-lancia.sh` cerca `v1/strumenti/sshpw.py`, che sul server non c'è. Lanciato di
> là muore prima di applicare qualsiasi guasto (verificato: zero marche nei sorgenti e nel binario,
> porta 7447 libera).
>
> ⛔ **Al primo giro un punto solo non passava**: contro il server guasto, `respinto-non-riprovare`
> restituiva **`canale-rotto`** dove l'atteso dice **`muta`**. ⭐ **E la pagina aveva ragione**:
> distinguere un `FIN` da un `RESET_STREAM` è la cura del rilievo R6.12, e il server in quel caso
> **non manda nessun `FIN`** — chiude la *sessione* con `CLOSE_WEBTRANSPORT_SESSION`.
>
> ⭐⭐ **Ma la causa vera era un'altra, e allargando l'atteso non l'avrei mai trovata.** La pagina
> non arrivava nemmeno al ramo del `RESPINTO`: il server manda `RESPINTO` e **chiude subito
> dietro**, e la chiusura **corre** contro il lettore della pagina. ⇒ Il verdetto dipendeva da chi
> vinceva la corsa.
>
> ⛔ **E la cura era già scritta nel file, per il caso gemello.** `respinto-poi-congedo` porta
> questo commento: *«La chiusura di §3.1 partirebbe subito dietro al messaggio, e correrebbe contro
> la risposta della pagina… un banco che cambia verdetto fra due giri identici non misura la pagina:
> misura il carico della macchina»*. ⇒ Stessa cura, stesso posto: dopo `RESPINTO` il server guasto
> **tace**, e chi chiude sarà la pagina.
>
> ⚠ **E non è allargare l'atteso**: l'atteso resta `muta`, e il caso può ancora dire di no — se la
> pagina riprovasse, i byte in più li vedrebbe il **registro del server**, che è il testimone che
> quel caso dichiara da sempre (§8.1).
>
> ⭐ **Esito**: **CONFORME, 0 punti** contro il server guasto; **NON-CONFORME, 9 punti** contro
> quello sano, in 35 secondi. ⚠ Riserva scritta nel registro: **un motore solo** — Chrome non l'ha
> guardato, e con un motore solo la seconda strada di §3.1 non si vede.
>
> ⭐ **E B12 ha imparato a giudicarlo — R12-A.48.** Il modello sano/guasto/risano non gli si
> applica: il suo giro «sano» **dev'essere rosso**, perché è il controllo che dice *no*. `giudica()`
> ha ora un passo **`proprio-giro`** che pretende **tutt'e due le metà, esplicite** — ⛔ un giro che
> portasse solo *«il guasto è verde»* non certifica niente, perché sarebbe compatibile con una
> pagina che dichiara conforme qualunque cosa.

> #### ⛔⭐ B13: la parola d'ordine in un indirizzo — e il banco aveva ragione da ieri
>
> B13 non si certifica perché **il suo soggetto è davvero rotto**, ed è la regola giusta: si lascia
> NON CERTIFICATO invece di allargare l'atteso finché torna. Oggi il difetto ha un nome — **rilievo
> R12-A.34**.
>
> `B13.2` — *«la parola d'ordine compare in 1 registri su 1288»* — indicava
> `sonda/racc.log`. ⛔ Non era un registro stantio da cancellare: **`sonda/lancia.sh` passava le
> credenziali nella query dell'indirizzo** (`&utente=prova&parola=…`), e la query fa parte della
> **riga di richiesta HTTP**, che ogni server registra per mestiere.
>
> ⚠ E la stessa pagina, venti righe più sotto, stampava *«CREDENZIALI mandate (la parola non compare
> in nessun registro)»*: una frase che si smentiva da sola nel file accanto.
>
> ⛔ **E il difetto era più largo del registro**: la parola stava anche nella sessione salvata di
> **due profili Firefox** (`prof-ammesso`, `prof-respinto`), perché l'indirizzo è passato dalla
> cronologia.
>
> ⭐ **Cura**: le credenziali passano nel **frammento** (`#`), che il browser **non manda al
> server** — quindi non entra in nessun registro HTTP, né nostro né di un proxy in mezzo. ⛔ E la
> seconda metà, che da sola avrebbe reso la cura una finzione: `lancia.sh` **stampava l'indirizzo**
> sul terminale, e il terminale di un giro finisce in un file come tutto il resto — adesso lo stampa
> mascherato.
>
> ⚠ **Che cosa la cura non chiude, detto qui e non altrove**: il frammento resta nella **cronologia**
> del browser. Per un banco con una parola di prova va bene; ⛔ **una pagina di prodotto non deve
> prendere la parola d'ordine da nessun pezzo dell'indirizzo**.
>
> ⛔ **E i registri sporchi NON sono stati cancellati**: farlo prima di aver verificato la cura
> sarebbe rendere B13 verde **buttando la prova**. Si buttano il giorno in cui un giro nuovo della
> sonda ne produce di puliti. ⚠ Resta inoltre aperta `B13.4` (*«qualcuno ascolta in TCP ma la pagina
> non si carica»*): B13 non si certifica finché non passano tutt'e due.
>
> #### ⭐⭐ LA SERA DELL'11 AGOSTO: la cura regge, i registri sono buttati, e **B13 è certificato**
>
> ⭐ **Il giro nuovo della sonda l'ha verificata** `[M]` **11 agosto 2026, 12:54:33Z-12:54:53Z**, su
> **NIC-OS**, contro il **PRODOTTO** su `192.168.0.2:7481` (raccoglitore su `127.0.0.1:7482`,
> **Firefox 140.13.0esr**): `AMMESSO` e `RIFIUTATO`, **8 file prodotti**, ⛔ **zero registri con la
> parola dentro**. A contenerla restano i soli due **sorgenti** — ed è quel che `B13.2` dichiara di
> non chiamare rosso.
>
> ⛔ **E il giro nuovo ha trovato che la cura era scritta e non fatta.** `sonda-rcp.html` prometteva
> *«il profilo lo si butta a fine giro (`lancia.sh`)»*, e `lancia.sh` lo buttava all'**inizio**:
> quello dell'ultimo giro restava sul disco. ⚠ **E le prime due cure non hanno tenuto, ed è
> misurato**: profilo cancellato alle **12:49:54**, `recovery.jsonlz4` ricomparso alle **12:50:10**
> (2223 byte, la parola dentro) — Firefox era ancora vivo; poi, con `setsid` + `kill -- -$p`,
> ricomparso alle **12:51:31**, perché *«il gruppo è morto»* rispondeva **subito**: ⛔ **il controllo
> era muto, e un controllo muto ha la stessa faccia di un controllo che passa**. ⭐ Adesso si guarda
> in `/proc` **chi ha ancora quel profilo fra i propri argomenti** — mai `pkill -f` — e la
> cancellazione **si riverifica cinque secondi dopo**.
>
> ⭐ **Poi i registri sporchi sono stati buttati, e non prima**: `sonda/racc.log` e i **due profili
> Firefox interi**, **33 file**, di cui **5** contenevano la parola. ⛔ La traccia — nome, byte,
> `sha256`, data, e **se** la contenevano ma non **quale** — sta in `banchi/01-b13-buttati.jsonl`:
> buttare una prova senza lasciarne il conto è la seconda metà dello stesso difetto.
> ⇒ ⭐ **`B13.2` è verde**: *«la parola non compare in nessuno dei **1368** registri»*, denominatore
> **22 461 file**, **zero illeggibili**, col controllo positivo accanto.
>
> ⭐⭐ **`B13.4` si chiude, perché contro il prodotto ha finalmente un imputato**: la pagina si carica
> (**200, 31 083 byte**), porta l'**impronta corrente**, e **`/impronta` risponde**. **4 su 4**.
> ⚠ Contro l'**innesto** resterà `[?]` per sempre: lì nessuno ascolta in TCP.
>
> ⭐⭐ **E B13 è certificato** `[M]` **11 agosto 2026, 15:19**, NIC-OS: **sano 3 → guasto 1 → risanato
> 3**, col guasto di B12 (`pagina.pem` sostituito da `sessione.pem`) e la marca *«LE IMPRONTE
> COMBACIANO»* **nel suo punto** — più i **14 guasti costruiti a mano** di `--certifica`: **14 su
> 14** ⚠ **da utente normale**, e **13 su 14 da root**, perché i permessi `0000` non fermano root e
> ⛔ **un guasto saltato non è un guasto passato**. ⚠ **Tre deviazioni da B12, scritte dentro la riga
> di registro**: porta **7481** invece della 7447 · bersaglio il **prodotto** e non l'innesto · il
> ciclo condotto da uno script suo, perché `01-b12-lancia.sh` **scrive `PORTA=7447` in chiaro** e non
> si può puntare altrove.
>
> ⛔ **Che cosa resta aperto, e sono due**: **`B13.3`** — c'è un imputato (`src/certificati.c`, **45
> righe**) e questo banco **non lo interroga**: serve un banco che *installi* un certificato
> d'autorità e guardi che cosa il server presenta sul filo dopo · **`B13.5`** — **non misurata**: il
> credito letto dal pari è **19** (§2.3 ne vuole almeno 16), ma `aioquic` concede **tutti** i 23
> stream chiesti, quindi lo strumento non sa dire *no* e il suo *sì* non vale. ⚠ È un difetto del
> **banco**, non del server.
>
> ⛔⭐ **E la prima riga di registro di B13 non contava, e ci sono volute due letture per accorgersene.**
> Il banco era certificato e il rapporto lo diceva; ⚠ ma `01-b12-guasti.py --registro` classificava
> B13 fra le certificazioni **NON RIVERIFICABILI**, cioè **non lo contava**. ⛔ E il motivo non era
> *«mancano le impronte»*: le impronte c'erano, **sotto nomi che il catalogo non conosce**
> (`01-b13-sera-certifica.sh`, `src/rcp.c`, `src/pagina.c`). `FILE_CHE_CONTANO["B13"]` ne nomina
> **due** — `01-b13-proprieta.py` e `rcp/rcp.c` — e `confronta_impronte()` scorre le chiavi vecchie
> con un `get`: ⛔ **una sola chiave fuori catalogo manda l'intera riga in *«non si sa»***.
> ⭐ **Lo strumento aveva ragione, e per la ragione giusta**: *«non so se valga oggi»* non si
> arrotonda a *«certificato»* (`LEZIONI.md` §1.9).
> ⭐ **E la correzione è una riga NUOVA, non una riga riscritta**: quella delle 15:07 resta dov'è, e
> quella delle 15:19 dice perché esiste. ⚠ *E si è visto perché serviva anche l'altra metà della
> cura: fra un `--put` dell'intero registro e il successivo, il server aveva guadagnato **una riga
> di un altro agente** — che un `--put` avrebbe cancellato in silenzio.*
>
> ⚠ **E la riga porta scritta dentro una riserva che altrimenti non si vedrebbe**:
> `FILE_CHE_CONTANO["B13"]` nomina `rcp/rcp.c`, la copia dei **banchi**, mentre il ciclo ha misurato
> il **prodotto**. Oggi le due copie sono identiche byte per byte (`84411b9c…`) — ⛔ **per
> combinazione, non per costruzione**: il giorno in cui divergono, quella riga riverificherà il file
> sbagliato e continuerà a dire di sì.
>
> ⭐ **E la cartella `sonda/` non era nel deposito**: come i quattordici file del 10 agosto, viveva
> solo sul server. Adesso sta in `banchi/sonda/`.
>
> ---
>
> ### ⛔ Che cosa B12 ha certificato DAVVERO: **3 su 12** — all'11 agosto 2026, *mattina*
>
> ⚠ *Il riquadro qui sotto è lo stato di stamattina, ed è tenuto perché spiega da dove si partiva.
> Il conto di oggi sta nel riquadro qui sopra.*
>
> *Scritto qui perché è la domanda che vale doppio, e la risposta non stava in nessun documento: il
> `README.md` diceva «sei verdi» nello stesso momento in cui il registro di B12 ne certificava due.
> ⛔ **«Verde» e «certificato» sono due cose diverse** — verde vuol dire che il banco ha girato e non
> ha trovato niente; certificato vuol dire che qualcuno **gli ha rotto sotto il codice** e il banco è
> diventato rosso, e sulla marca giusta. È la seconda che dice se la prima valga qualcosa. Rilievo
> **R12C.16**, e il conto viene da `banchi/01-b12-registro.jsonl` letto riga per riga l'11 agosto.*
>
> ⛔ **E le parole sono quattro, non due**, perché quattro sono gli stati:
>
> | Banco | Stato | Quando, e su che cosa |
> |---|---|---|
> | **B4** | ⭐ **certificato** | 11 ago 00:27, macchina `CHUWI`, con le impronte dei **tre file che partecipano** (`01-b4-lancia.py`, `01-b4-validatore.py`, `01-b4-registrazioni.py`) |
> | **B9** | ⭐ **certificato**, ⚠ **con una riserva scritta** | 11 ago 00:27, `CHUWI`, impronte di `01-b9-letture.py`, `01-b3-cliente.py` e di `RCP.md`. ⚠ Il guasto costruito per lui **cancella una citazione** del documento: quel che dimostra è che B9 sa vedere **un testo cambiato**, che è la cosa che B9 dichiara apertamente di saper fare — **non** che sappia vedere il secondo lettore allinearsi al primo (rilievo **A8**) |
> | **C2** | ⭐ **certificato** | 10 ago 22:32, macchina `NIC-OS`, con una marca **discriminante** — cioè che nel giro sano **non compare** |
> | **B13** | ⛔ **provato e NON certificato** | 10 ago 22:24 e 22:25, due volte. ⛔ E il motivo è del **guasto, non del banco**: è di tipo «riga di comando» e l'orchestratore non lo sa innestare; e anche innestandolo a mano costruirebbe un difetto che **B13.1 non guarda** (rilievi **A1**, **A2**) |
> | **B7** | ⚠ **certificato e NON riverificabile** | 10 ago 21:19. ⛔ La marca pretesa era la parola `CONGEDO`, che `01-b7-congedo.py` stampa **37 volte** e anche nel giro **sano**: *«una marca che compare in tutt'e due i giri non è una marca, è un modo di certificare senza guardare»* (rilievo **A3**). E quel giro non ha lasciato le impronte per banco |
> | **B2 · B3 · B5 · B6 · B8 · B10 · B11** | ⛔ **mai provati** — sette | nessun giro di B12 li ha toccati |
>
> ⛔ **Il conto onesto: 3 certificati su 12**, uno provato e non riuscito, uno non riverificabile,
> sette mai provati. ⚠ **Non si arrotonda a «quattro»** (il numero che il registro ha dichiarato alle
> 21:19) **né a «sei»** (i verdi del README): *«provato e non riuscito»* e *«mai provato»* hanno due
> cure diverse, e un registro che le fonde le fonde sempre **nella più innocente**.
>
> ⚠ **E il denominatore va dichiarato, o è un conteggio senza denominatore**: i dodici di questa
> tabella sono **il catalogo di B12**, che comprende **B10** — il quale non ha uno script suo — ed
> esclude **B12**, che non certifica sé stesso. ⛔ **Non sono gli stessi dodici** dei banchi scritti
> (i prefissi in `banchi/`, che comprendono B12 e non B10): due insiemi di dodici che si somigliano
> e non coincidono, ed è precisamente il modo in cui un conteggio smette di essere una misura.
>
> ⭐ **E due difetti del registro stesso sono stati curati la notte del 10, e vanno detti perché
> spiegano perché il conto di ieri non tornava**:
> · il campo si chiamava **`mai_provati`** ed era *«mai provati **in questo giro**»*: B7 e C2,
>   certificati alle 21:19, alle 23:01 comparivano come **mai provati**, e B13 passava da *«provato e
>   non riuscito»* a *«mai provato»* — con la **stessa** impronta del codice (rilievo **A4**). Adesso
>   il campo si chiama `non_provati_in_questo_giro`;
> · l'impronta annotata era quella di `banchi/rcp/rcp.c` **anche per i banchi in cui `rcp.c` non
>   entra affatto** (B4, B9, C2): un denominatore che promette una cosa e ne misura un'altra, cioè
>   **peggio di nessuna impronta**, perché dà alla riga l'aria di essere già stata controllata
>   (rilievo **A5**). Adesso ogni riga porta le impronte **dei file che partecipano davvero**.

> ### ⭐ P1 e P5 entrano nel catalogo, e il denominatore cambia — la sera dell'11 agosto 2026
>
> Il `README.md` lo diceva con un numero: *«P1 e P5 non sono nel catalogo di B12: i banchi sono 14,
> le voci 12»*. ⛔ E quei due non erano «puliti»: erano **due banchi mai diventati rossi**, cioè la
> definizione di NON CERTIFICATO — ⛔ **e sono i due che guardano il PRODOTTO**, l'unica cosa di
> questa fase che un utente vedrebbe.
>
> ⛔ **Il denominatore vero, contato e non ricordato** (`ls banchi/`): **22** prefissi `01-`, che non
> sono 22 banchi — **14 banchi** (B2 B3 B4 B5 B6 B7 B8 B9 B11 **B12** B13 C2 **P1 P5**), **1
> attrezzeria** (`01-b0-*`) e **7 sonde del Gruppo 1** (S1b S2 S3a S5 S6 S7 S-telefono), che sono
> misure e non banchi che si certificano. Le voci del catalogo passano da **12 a 14**.
> ⚠ ⭐ **E non sono gli stessi quattordici**: il catalogo comprende **B10** ed esclude **B12**, che
> non certifica sé stesso. ⇒ I banchi che il catalogo può certificare sono **13**, e le voci che
> hanno un banco dietro sono **13**: due insiemi che adesso **coincidono**, mentre prima di stasera
> erano dodici e dodici **diversi** — cioè il conto tornava e contava cose che non erano le stesse.
>
> | | |
> |---|---|
> | ⭐⭐ **P1 è CERTIFICATO** | `[M]` NIC-OS, porta **7501**, tre giri alle **12:56:20 · 12:56:56 · 12:57:24 UTC**: **0 → 1 → 0**, VERDE 34/34 → ROSSO 33/34 → VERDE 34/34. Guasto: `Cross-Origin-Opener-Policy` da `same-origin` a **`unsafe-none`**. Marca `MANCA: Cross-Origin-Opener-Policy: same-origin`, misurata **0 · 2 · 0** |
> | ⭐ **e il rosso è di UN controllo solo** | `costruzione.esito` resta **0** e `binario.marche` resta **8/8**: il guasto **non** è passato per una compilazione fallita, che renderebbe rosso qualunque banco e certificherebbe **zero** |
> | ⛔ **e la prima stesura del guasto sarebbe stata proprio quella** | toglieva **l'intestazione**. ⚠ Ma `src/costruisci.sh` **cerca `Cross-Origin-Opener-Policy` dentro il binario e si ferma se non la trova**, e la cerca anche P1 fra le sue otto marche. ⭐ Preso **leggendo `costruisci.sh` prima di innestare**, e la cura è nella forma del guasto: **si cambia il valore, si lascia il nome** |
> | ⛔ **P5 è PROVATO e NON CERTIFICATO** | e non *«non provabile»*, che è l'altra cosa. ⭐ Ma il suo conto è cambiato due volte in un'ora, e la seconda in meglio |
> | ⛔⛔ **ATTENZIONE: le due righe qui sotto sono state SMENTITE la sera stessa** | ⭐ Il banco aveva davvero un difetto — `ctrl+w` sul display sbagliato, ed è vero — ⛔ **ma l'assoluzione che ne è seguita era falsa**: l'arbitrato contava una chiusura **senza guardarne il motivo**. Il difetto del prodotto **c'è, su tutt'e due i motori**. Si leggano queste righe **fino in fondo al riquadro**, dove la misura le corregge |
> | ⭐⭐ **e l'accusa al PRODOTTO era del BANCO** *(riga smentita — vedi sotto)* | ⛔ P5 scriveva *«nessun congedo, per nessuna delle due strade di §3.1»* — cioè accusava la pagina di violare §8.1 **per un gesto mai fatto**: `01-p5-lancia.sh` batteva `xdotool key ctrl+w` **senza la funzione `X`**, su un `DISPLAY` che non è lo schermo finto. Il tasto non arrivava, `pagehide` non scattava. ⭐ **L'arbitrato è `banchi/01-p5-congedo.sh`** `[M]` **13:26 UTC**: si va via in **due modi** — navigando via, dove `pagehide` scatta di sicuro, e con `ctrl+w`, dove scatta solo se il tasto arriva — e ⭐ **da tutt'e due il congedo ESCE** (strada 2 di §3.1, posto `LASCIATO`, **zero** `STACCATO per silenzio`, e il gesto verificato dalle finestre **1 → 0**). ⇒ **La pagina fa quel che §8.1 le impone.** ⚠ È `LEZIONI.md` §1.9 di nuovo, e **la seconda volta in questa fase dopo B3**: il rosso puntato sull'imputato sbagliato |
> | ⭐ **e il testimone è stato scelto bene** | il registro **del server**, letto a **+8 s** — prima che il tetto dei 30 secondi possa liberare il posto: senza quella finestra, *«si è congedato»* e *«staccato per silenzio»* arrivano con la stessa faccia. ⚠ *E il primo giro dell'arbitrato ha sbagliato lui: il segmento si chiudeva sul marcatore di fine, mentre `pagehide` scatta **mentre quella richiesta è in volo**, e la riga del congedo cadeva fuori. Uno zero da segmento sbagliato ha la stessa faccia di uno zero vero — vale il **secondo** giro* |
> | ⭐ **curato il pilota, i numeri si muovono** | `X` davanti al `ctrl+w`, e `fuoco` portato **fuori dal ramo di N2** — con lo sblocco che non risponde quel ramo si saltava, e si arrivava alla gamba `P` **senza aver mai dato il fuoco a nessuna finestra**. `[M]` giro sano **13:29:41 UTC**: ⭐ **Chrome passa a CONFORME**, e ⭐ **Firefox adesso MISURA** — arriva a `SESSIONE`, **14 su 15**, secondo fisso **1069 ms** — dove prima non aveva denominatore |
> | ⛔ **e resta UN punto, che questa volta NON è del banco** | su **Firefox** il congedo non esce lo stesso: dal registro del server il client chiude con un **`FIN` nudo sul canale di controllo**, il posto è `LASCIATO` **in modo ordinato** e `STACCATO per silenzio` vale **0**. ⇒ **Il gesto è arrivato, la sessione si è chiusa bene, e il client non ha detto perché** — dove §8.1 lo impone senza condizioni. ⚠ **I due imputati residui non si distinguono da questa parte**: *«la pagina non spedisce»* e *«Firefox butta via quel che la pagina spedisce dentro `pagehide`»* arrivano identici al server, e a separarli serve il registro **del browser**. ⭐ E si noti che la pagina prevede il caso **opposto** — *«Chrome butta un messaggio spedito subito prima di chiudere, quindi la strada che regge è il codice di chiusura»* — mentre su Firefox non regge **nessuna** delle due: è la differenza fra motori per cui P5 esiste, ⛔ **e è comparsa solo DOPO aver curato il pilota**, che è la prova che le due colonne servono |
> | ⭐ **e il guasto di P5 è misurato lo stesso** | la marca `sono due impronte diverse per lo stesso certificato di sessione` compare **1** volta nel giro rosso e **0** nel sano: il banco **vede** il proprio guasto. ⇒ P5 non si certifica perché **il suo giro sano non è verde** — la stessa forma di B8 — **non** perché sia cieco |
>
> #### ⛔⛔ E POI LA MISURA HA SMENTITO L'ASSOLUZIONE: **il congedo non esce, ed è della PAGINA**
>
> *`[M]` 11 agosto 2026, sera, `banchi/01-p5-ff-*`. ⛔ Due giri identici per motore, su una **copia
> strumentata** di `src/pagina.html` servita da un server a parte — il prodotto non è stato toccato.
> Il tracciatore è `navigator.sendBeacon`, cioè **un portatore che non passa da WebTransport**: se
> passasse di lì condividerebbe il destino della cosa che si misura.*
>
> ⛔ **L'imputato è la pagina, e Gecko è scagionato per misura.** Chiudendo la scheda con `ctrl+w`
> **a browser vivo**, su Firefox 140.13.0esr `pagehide` **scatta** — e la traccia della pagina dice
> `congeda_corrente NULLA`. ⇒ Il gestore di `src/pagina.html:331` è **codice morto**: il `finally`
> del gestore di `submit` (riga **620**) azzera `congeda_corrente` **un millisecondo dopo
> `SESSIONE`**, perché `collega()` ritorna lì. Il posto se ne va dopo `STACCATO per silenzio:
> 30060 ms`.
>
> | variante, stesso motore e stessa scena | `pagehide` | `congeda()` chiamata | che cosa arriva al SERVER |
> |---|---|---|---|
> | **fedele** — il prodotto com'è | ⭐ **1** | **0** | ⛔ **niente** |
> | **tenace** — la *stessa* `congeda()`, riferimento non azzerato | 1 | 1 | ⭐ **`CONGEDO` sul canale + codice `0x01`** |
> | **codice** — solo `wt.close(0x01)` | 1 | — | ⭐ codice `0x01` |
> | **vivo** — la stessa `congeda()`, scheda **viva** | — | 1 | ⭐ `CONGEDO` + codice `0x01` |
>
> ⇒ ⭐ **Firefox non butta via niente**: dentro `pagehide` funzionano **tutt'e due** le strade di
> §3.1. **Manca solo chi le imbocchi.**
>
> ⛔⛔ **E il ⭐ di Chrome era un FALSO VERDE — è il rilievo che vale di più.** Nella stessa scena,
> su Chrome, la pagina non spedisce niente e al server arriva **lo smontaggio di Chrome**:
>
> ```
> ⛔ VIOLAZIONE §3.1 — la pagina ha chiuso la sessione col codice 0x0 … A verbale va ERRORE_PROTOCOLLO
> la pagina ha chiuso la sessione, motivo 0x0b
> ```
>
> ⛔ `01-p5-congedo.sh:318` conta la riga *«la pagina ha chiuso la sessione, motivo»* **senza
> guardare il motivo**: ha contato **una violazione di §3.1 come un congedo**, e ha stampato
> *«⭐⭐ LA PAGINA FA QUEL CHE §8.1 LE IMPONE»*. ⇒ ⭐⭐ **I due motori non erano opposti: mostravano
> lo STESSO difetto della pagina attraverso due smontaggi diversi**, e su uno dei due il banco è
> inciampato nel proprio contatore. ⚠ *E il server lo diceva*: la riga di violazione la scrive lui,
> ed era nel registro.
>
> ⭐ **La cura è di tre righe, ed è DESCRITTA E NON APPLICATA** — la fase era chiusa da un'ora, e una
> cura di prodotto infilata dopo la chiusura non è una cura, è un cambiamento non dichiarato.
> L'ancora di `congeda_corrente` è sbagliata: non è *«il tentativo è finito»*, è ⭐ ***«la sessione è
> finita»***. ⇒ togliere l'azzeramento dal `finally` (riga 620) · azzerarlo dentro
> `wt.closed.then(…)` di `collega()`, l'unico punto che sa quando la sessione non c'è più · lasciare
> quello a inizio gestore (riga 606), perché un tentativo nuovo deve buttare il riferimento vecchio.
>
> ⚠ **E due rilievi per i banchi, che valgono oltre questo caso**: *(a)* si conta **`motivo 0x01`**,
> non *«una chiusura qualunque»* — un contatore che non legge il motivo trasforma una violazione in
> un verde; *(b)* ⛔ **`ctrl+w` sull'unica scheda fa USCIRE Firefox**, e in quella scena non esce
> niente per **nessuna** via, nemmeno per le varianti che scavalcano il difetto: **la scena va fatta
> con due schede**, o si misura l'uscita del programma invece della chiusura di una scheda. *Era la
> scena di P5.*
>
> ⛔ **E tutt'e due i guasti si innestano su una COPIA INTERA del prodotto**, mai su
> `/media/REMOTIX/src/remotix/`. ⚠ La ragione **non** è quella dei guasti in Python degli altri
> banchi: è che **P1 ricostruisce il binario come primo passo del proprio giro**, e guastare il
> prodotto di casa lascerebbe, per i minuti del passo di mezzo, **un binario bugiardo sotto i piedi
> di chiunque altro lo riaccendesse**. *La sera dell'11 agosto sulla macchina di prova c'era un
> `remotix` vivo sulla 7448 e cinque agenti al lavoro insieme.*
>
> ⭐ **E `01-p1-prodotto.sh` e `01-p1-dentro.sh` accettano da stasera `PORTA`, `PORTA_MORTA`, `SORG`
> e `PREFISSO_TMP`**, coi predefiniti di prima: chi lancia a mano misura quel che misurava.
>
> ### ⭐⭐ B8 CERTIFICATO — e la cura non è stata completare la copia, è stata TOGLIERE la copia
>
> | | |
> |---|---|
> | ⭐ **B8** | **certificato, e non lo era mai stato**: `[M]` 11 agosto 2026, **13:46 UTC**, NIC-OS, innesto, porta **7471** — **`5 → 1 → 5`**, marca *«N risposte sotto il secondo»*, vista **solo** nel rosso |
> | ⛔ **e l'atteso sano è 5, non 0** | ⭐ **scritto nel catalogo prima del giro, non allargato dopo**: è il quinto esito di B8 — *«il ban passa per intero, ma le mediane si separano»* — e si concede **solo** perché l'imputato è **misurato** ed è **PAM**. ⭐ Il giorno in cui quel `[?]` si chiudesse, il sano diventerà **0** e **quella riga del catalogo diventerà rossa da sé**: è il modo giusto di accorgersene |
> | ⭐ **il guasto dà un rosso pieno** | `RITARDO_FISSO` da 1000 a **0**: `[M]` **17 risposte sotto il secondo**, la più veloce **49,7 ms**, e la mediana del caso «parola giusta» da **1085,9** a **56,3 ms** |
> | ⭐ **e il giro copre finalmente la sequenza intera** | **due vite del server** — la seconda accensione dichiara *«ban caricati: 1»*, cioè il ban torna **dal disco** e non dalla memoria (**I7**) · **la pagina** (HTTP **200**, `bannato=True`, *«tentativi esauriti»*, **12h 0m**, col controllo che dice no a 594 byte) · **lo sblocco su un ban vero** (`TOLTO` → poi `NON-BANNATO` → e l'indirizzo **rientra**) |
> | ⭐ **il segreto NON trapela** | mediane `[M]`: **inesistente 2123,2 · sbagliata 2198,1 · giusta 1085,9 ms**; la coppia che §4.4 protegge — *«inesistente − sbagliata»* — vale **−74,8 ms**, intervallo **[−509,3; +255,7]** ⇒ ⛔ **non si separa**. E l'imputato del resto è misurato: il server ha atteso **+1034 ms** oltre il secondo fisso sui respinti e **+84 ms** sugli ammessi — la firma di `pam_faildelay` |
> | ⚠ **e i due denominatori accanto** | la certificazione **fuori dal filo** 33 su 33, e il **giudice** di B8 15 su 15 guasti a mano, in tutt'e tre i passi |
>
> ⭐⭐ **E la cura strutturale è il punto 4 dell'elenco, fatto dove mordeva.** `01-b12-lancia.sh`
> **riscriveva a mano** la sequenza di B8, e la copia era incompleta in tre punti: il giro sano
> usciva rosso su **otto** punti che parlavano **dell'orchestratore, non del banco**. ⇒ Adesso
> `gira()` **chiama `01-b8-lancia.sh`** — come faceva da sempre con C2, quindi è un precedente in
> casa e non una deroga inventata — e la marca la legge dal file che il verdetto di B8 scrive da sé.
> ⚠ **E si è fermato lì apposta**: estendere la cosa agli altri banchi stasera avrebbe cambiato il
> modo di lanciare banchi **certificati oggi**, cioè invalidato nove certificazioni per rifarle in un
> tempo che non c'era.
>
> ⛔ **Che cosa questa certificazione NON copre**, e va detto: B8 è certificato **contro l'innesto**.
> Sul **prodotto** i tre appigli della pagina del ban esistono, ⚠ ma il giro non è stato fatto lì; e
> **la pagina la legge un socket, non un browser**, mentre questa sezione ne chiede il DOM *«come per
> le otto frasi di B7»*.
>
> ⚠ **E la certificazione di P1 non si riverifica da CHUWI**: la sua riga elenca `remotix/pagina.c`,
> che da `banchi/` esiste **solo sul server** — qui il prodotto sta in `../src/`. ⛔ Quindi
> `--registro` la classifica *«non si può dire se valga oggi»*, ed è **la scena di B9 al contrario**
> (là mancava `RCP.md` sul server). ⭐ *«Non riverificabile da questa macchina»* non è
> *«non certificato»*, e lo strumento fa bene a non fonderli — ma il conto **dipende ancora da dove
> lo si chiede**, ed è la stessa `[?]` del pomeriggio, non curata.

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

> ⚠ **Questo capitolo si apriva con** *«Nessuna riga di **prodotto** scritta. Quel che c'è è
> banco.»* — ⛔ **ed era falso dalla notte del 10 agosto 2026**, quando `src/` è nato: venti file,
> poi ventidue. Nessuno dei dieci documenti del progetto nominava quella cartella, e `PIANO.md` §0.2
> assegna proprio a questo capitolo il compito di dire che cosa la fase ha prodotto. ⛔ **Il costo
> era concreto**: chi riprendeva la fase leggeva *«nessuna riga di prodotto»* e **riscriveva da zero
> un server che esiste** — oppure lo trovava per caso con un `ls` e non sapeva se fosse prodotto,
> scarto o l'esperimento di qualcuno. Riscritto l'11 agosto 2026, rilievo **R12C.1**.
>
> ⛔ **E c'è una seconda cosa che quella riga faceva, meno visibile**: da quando `src/` esiste, ogni
> frase che dice *«il server»* ha **due soggetti** — il prodotto e l'innesto di
> `banchi/01-b3-rcp-innesta.py` dentro `bsslserver`. In questo documento, da qui in poi, *«il
> prodotto»* è `src/` e *«l'innesto»* è l'altro, **e i banchi misurano l'innesto**.

## ⭐⭐ Il prodotto — `src/`, il server della fase 1 in C

`[M]` **11 agosto 2026** (`wc -l` e `grep -cvE` su questo albero, codice fermo alle 00:36):
**22 file**, **9.647 righe**, di cui **5.248 di codice** nei `.c`/`.h`.

⭐ **Che cosa fa, in una riga**: un browser vero apre `https://192.168.0.2:7447`, l'utente digita
nome e parola d'ordine, e **la stretta di mano di RCP/1 arriva fino a `SESSIONE`** — con i due
certificati, la pagina servita dal server stesso, e il ban di `RCP.md` §4.4-bis. ⛔ **Niente video,
niente audio, niente input**: quelle sono le fasi da 2 in poi.

| | |
|---|---|
| `src/main.c` | ⛔ **i due ascoltatori sulla stessa porta 7447** (`RCP.md` §2.4): UDP per HTTP/3 e WebTransport, TCP per il primo caricamento della pagina — e sono **indipendenti**, WebTransport non passa da `Alt-Svc`. Un ciclo `poll` solo. ⭐ All'avvio **guarda che `/etc/pam.d/remotix` ci sia** e lo scrive: senza, Linux-PAM ripiega su `other` (che su Debian è `pam_deny`) e **ogni parola giusta viene rifiutata**, con una diagnosi che punta sulla parola d'ordine mentre il difetto è un file mancante. ⭐ E alla chiusura **congeda tutti** con `SERVER_IN_CHIUSURA` (§8.2 `0x0C`) invece di sparire |
| `src/trasporto.c` | QUIC su **ngtcp2**: `max_idle_timeout` 30 s imposto dal server, datagram annunciati, **19** stream unidirezionali concessi (§2.3 ne vuole 16 *disponibili* e HTTP/3 se ne prende 3 — il numero si dichiara invece di essere sottratto in silenzio), migrazione non disabilitata. ⭐ I datagram che arrivano si **contano e si scartano scrivendolo nel registro** (§6.3), invece di sparire in un callback che non c'è |
| `src/webtransport.c` | HTTP/3 e WebTransport: la `CONNECT` estesa **solo** su `/rcp/1` (404 altrove, §2.2), le capsule, la chiusura col codice del motivo. ⭐ E i **PING del trasporto** mentre il server aspetta le credenziali — senza, al trentesimo secondo la connessione muore in silenzio e i 60 s di §4.6 non scadono mai (§4.6, rilievo R1.8) |
| ⭐⭐ `src/rcp.c` + `rcp.h` | **RCP/1**, la stretta di mano e il ban. ⛔ **Identici byte per byte a `banchi/rcp/`** — `[M]` 11 agosto 2026, `md5sum`: `cb7af778…` (`rcp.c`), `0458f154…` (`rcp.h`). ⚠ **Identici per fortuna, non per costruzione**: nessuno script confronta le due copie a ogni giro, e da stanotte hanno **due storie diverse** (una in git, una no). `src/costruisci.sh` accetta `GEMELLO=` per dichiarare il confronto |
| `src/autenticazione.c` + `remotix.pam` | PAM, ⭐ **servizio `remotix`** come vuole `SPECIFICHE.md` §4.2 — con il file del servizio nella cartella, non in una nota d'installazione. ⚠ *Il 10 agosto notte diceva `pam_start("login")`, cioè la pila della **console locale** con `pam_securetty`, `pam_lastlog`, `pam_limits`: rilievo **B-11** di `fasi/rapporti/R12-B-prodotto.md`, curato nel codice la stessa notte* |
| `src/certificati.c` | i **due** certificati di §4.1-bis, con il rifiuto di partire se le due impronte coincidono, il breve a 13 giorni che ruota quando ne restano due, e `/impronta` servito con `no-store` |
| `src/tls.c` | TLS per l'ascoltatore TCP. ⭐ **0-RTT spento a livello di contesto**, dove nessuna sessione lo può riaccendere (§2.3) |
| `src/pagina.c` + `pagina.html` | la pagina servita dal server: l'impronta corrente, la stretta di mano dal lato del browser, e l'avviso di chi è bannato con **le ore che mancano** (§4.4-bis). ⭐ Il server **si rifiuta di partire** se la pagina non contiene i segni da sostituire, o se ne contiene due — una sostituzione che «riesce senza fare niente» servirebbe per sempre una pagina senza impronta |
| ⭐ `src/comando.c` + `comando.h` | **il comando di sblocco di §4.4-bis**, su un **socket Unix `0600`**: `SBLOCCA <indirizzo>` → `TOLTO` / `NON-BANNATO`, `PING` → `PONG`. ⛔ È lo stesso protocollo, byte per byte, che parla `banchi/01-b8-sblocca.py`, cioè lo strumento della regola **B0.3** |
| `src/registro.c` | riusato da v1, con l'obbligo di **B13.2**: la parola d'ordine non compare in nessun registro |
| `src/Makefile` + `costruisci.sh` | ⭐ **butta il binario prima di ricostruire** (così *«c'è»* vuol dire *«è di adesso»*) e **controlla cinque marche dentro il binario prodotto**, con il controllo positivo dello strumento. È la ottava veste di `LEZIONI.md` §1.9 curata prima di pagarla |

### ⛔ Che cosa di `src/` NON è provato

*Elencato riga per riga, perché è la metà che non si vede. Le prime due voci vengono da
`fasi/rapporti/R12-B-prodotto.md` §0; le altre le ho misurate io l'11 agosto 2026, e dove ho
misurato lo dico.*

| | |
|---|---|
| ⛔ **il server intero non è mai stato eseguito da un revisore** | sulla macchina del revisore mancano `ngtcp2`, `nghttp3`, `libssl-dev` e `libpam0g-dev` (`make dipendenze` dà **cinque NO**). ⇒ tutto quel che riguarda `trasporto.c`, `webtransport.c`, `pagina.c`, `certificati.c` è **letto, non misurato**. ⭐ L'unica esecuzione è `src/rcp.c` **compilato isolato** con `-Wall -Wextra` — **zero avvisi** — contro un driver del revisore, sei ingressi byte per byte |
| ⛔ **UN SOLO MOTORE** | l'unica traccia di un giro con un **browser vero** contro questo server è un commento dentro `src/pagina.html`: `[M]` 10 agosto notte, **Firefox** — e quel giro ha trovato un difetto vero (la pagina mandava `disposizione = en`, che **non è** un nome XKB, e il server congedava con `SESSIONE_NON_SERVIBILE` facendo esattamente il suo mestiere). ⛔ **Di Chrome contro questo server non c'è nessuna traccia**, e il criterio di B2 vuole **due motori su due** |
| ⛔ **e quel giro non è riverificabile da questa parte** | `[M]` 11 agosto 2026, **mattina**: in `src/` non c'è né il binario `remotix` né un `.o`; nessun `.jsonl`; `git status` dà `src/` **untracked**, mai committata. E **nessuno dei 14 script `01-*-lancia.sh` accende il prodotto**: `bsslserver` compare in **11** di loro, il binario `remotix` in **zero** (l'unica occorrenza della parola è `remotix.prova`, un nome SNI in `01-b2-lancia-sni.sh`). ⚠ ⛔ **E questa riga è SCADUTA la sera dello stesso giorno, e va letta con la data addosso**: `[M]` 11 agosto **sera** — `git ls-files src/` dà **22 file** (commit `ffeb341`), gli script di lancio sono **16** e **11 di loro sanno puntare al `BERSAGLIO=prodotto`**, tre accendono il binario per nome. ⭐ *Una riga che dichiara un'assenza invecchia nel verso peggiore: resta vera nell'aspetto e falsa nei fatti, e chi la legge non ha nessun motivo di sospettarla* |
| ⛔ **le proprietà di trasporto non sono state rimisurate contro questo server** | le sei di B2 — tetto 30 s · datagram · credito uni · migrazione · niente 0-RTT · `allowPooling` — sono `[M]` **sull'innesto**, letto dal pari. `src/trasporto.c` oggi dichiara **19** stream uni dove la misura di B2 ne leggeva 16: è un numero diverso, ed è **la sonda `01-b2-sonda-trasporto.py` puntata al prodotto** che lo direbbe |
| `[?]` **il rinnovo del credito degli stream** | il prodotto lo dichiara **di suo** (`src/trasporto.c`): ngtcp2 non alza il tetto da sé *«tranne quando uno stream si chiude senza che `stream_open` sia stato chiamato»*, e questo codice cade **probabilmente** in quell'eccezione. Nessuno l'ha misurato. ⛔ Si misura alla **fase 4**, quando gli appunti apriranno uno stream per trasferimento: prima di allora nessun client ne apre più di quattro, e una misura senza il carico che la provoca non è una misura |
| ⚠ **la pagina del prodotto e quella dell'innesto sono due documenti diversi** | e **B8 misura i marcatori che solo l'innesto produceva**. Curato nel prodotto la notte del 10 (`data-bannato` e `data-restano-ms` ci sono, in una sola occorrenza ciascuno, e il server rifiuta di partire se ce ne fossero due) — ⛔ **ma nessuno ha puntato B8 al prodotto per verificarlo**: finché non lo si fa, «curato» è letto e non misurato |

### ⛔ I ripieghi di fase — due che pesano e uno minore, dichiarati qui e non solo in un commento

> ## ⭐ E i due che pesano hanno una SCADENZA, decisa dall'utente alla chiusura della fase
>
> *11 agosto 2026, sera. ⛔ Le decisioni stanno in `DECISIONI.md` e qui si rimanda: sotto c'è la
> conseguenza sulla fase, non la decisione.*
>
> | | |
> |---|---|
> | **il filo** | **`DECISIONI.md` §1.10** — ⛔ **si cura PRIMA della fase 2**, e con un **processo aiutante** (PAM non è affidabilmente rientrante). ⭐ A spostare la scadenza dalla fase 5 alla 2 è stato **un numero di B8**: il blocco è di **1,0-2,2 s** a tentativo, ⛔ **e a metterlo è PAM**. Fino alla fase 1 il sintomo è *«l'ultimo dei dieci aspetta»*; **dalla fase 2 in poi è lo schermo di chi sta già lavorando che si pianta quando entra qualcun altro**, e chi lo vede lo attribuisce al video. ⛔ **E la proprietà da provare non è «PAM funziona ancora»**: è *«mentre uno si autentica, gli altri non se ne accorgono»* — e **quel banco oggi non esiste** |
> | **il tetto** | **`DECISIONI.md` §1.11** — ⛔ **resta 16 fisso fino alla fase 3**, di proposito: `SPECIFICHE.md` §5.5 dice di sé che *«il limite vero non è un conteggio, è un budget di pixel al secondo»*, quindi qualunque numero di oggi è un segnaposto. ⚠ **Il prezzo dichiarato**: per due fasi il codice dice **16** e la specifica dice **dieci**. ⛔ E vale per qualunque numero: **nessun banco ha mai visto quel tetto mordere** — riempirlo vuole dieci utenti **diversi** (I2), e il motivo del rifiuto è di fase 3 |

*Rilievo **R12C.17**: stavano scritti in `src/main.c` e `src/rcp.c`, cioè dove non li legge nessuno
che non stia leggendo quel file — mentre `SPECIFICHE.md` §5.5 e `DECISIONI.md` §4.6 promettono dieci
sessioni insieme senza una riga che dica il contrario. ⚠ Un ripiego di fase dichiarato nel codice non
è una promessa rotta: è una promessa **non ancora dovuta**. Ma il posto in cui si scrive è dove la
fase dichiara i propri confini.*

| | |
|---|---|
| ⛔ **un solo filo, e la verifica PAM lo BLOCCA** | tutto gira in un ciclo `poll` solo, e `pam_authenticate` è sincrona: la stretta di mano di un utente **ritarda i pacchetti di chiunque altro**. ⛔ E il secondo fisso di §4.4-bis lo rende misurabile: con dieci utenti che entrano insieme, l'ultimo aspetta **dieci secondi** — e il sintomo, *«il server è lento quando c'è gente»*, non nomina né PAM né il filo. **Prima della fase 5 la verifica va su un filo a parte** |
| ⚠ **sedici sessioni attaccate, in compilazione** | `src/rcp.c`: `#define MAX_ATTACCATE 16`, col commento *«un server vero lo sostituirà con la sua tabella delle sessioni»*. `SPECIFICHE.md` §5.5 dice **dieci, configurabile**: qui è sedici e fisso |
| ⚠ **e un terzo, minore, che vale la pena di nominare adesso** | l'interruttore della funzione di banco di `RCP.md` §7.5 è `#define BANCO_ACCESO 0`. L'invariante **I6** è rispettata — è spenta di suo — ⛔ ma §7.5 la vuole accendibile **nella configurazione del server**, e oggi accenderla richiede di **ricompilare**. Il giorno in cui la configurazione ci sarà, questa è la riga da cambiare |

## I banchi

| | |
|---|---|
| ⭐ `banchi/01-b2-costruisci.sh` | **nuovo**: costruisce BoringSSL e `lsquic` con `-DLSQUIC_WEBTRANSPORT=ON`, e ⛔ **verifica che il flag abbia prodotto i simboli** — non che compili |
| ⭐ `banchi/01-b2-certificati.sh` | **nuovo**: i **due** certificati di `RCP.md` §4.1-bis con quattro controlli — curva, `subjectAltName`, durata sotto i 14 giorni, e ⛔ **che i due siano davvero due** (il difetto di B13.1, colto alla nascita invece che due settimane dopo) |
| ⭐ `banchi/01-b2-controllo-aioquic.py` | **nuovo**: ⛔ **il controllo positivo di B2** — una sessione WebTransport che *deve* riuscire. Senza, «la candidata non apre la sessione» e «il banco non sa aprirne nessuna» hanno lo stesso aspetto (R3.17) |
| ⭐ `banchi/01-b2-cliente-aioquic.py` | **nuovo**: il germe del **cliente di prova** (B9), e il controllo d'ambiente che separa «il server non regge» da «il browser non accetta» |
| ⭐ `banchi/01-b2-sonda.html` | **nuovo**: la pagina, ⛔ **servita da `localhost`** — contesto sicuro senza avvisi, così quel che si misura è **la sessione** e non il clic dell'utente |
| ⭐ `banchi/01-b2-sni-ngtcp2.sh` | **nuovo, 10 agosto**: costruisce `bsslserver`, il server d'esempio di `ngtcp2`, che è il bersaglio della prova SNI. ⛔ **Non guarda l'uscita di `ninja`: guarda se il binario c'è** — `examples/CMakeLists.txt` costruisce quel blocco solo `if(LIBEV_FOUND AND HAVE_BORINGSSL AND LIBNGHTTP3_FOUND)`, e se una manca cmake **salta in silenzio** |
| ⭐ `banchi/01-b2-sonda-sni.py` | **nuovo, 10 agosto**: la sonda del criterio nuovo di `DECISIONI.md` §6.4. Due gambe (senza SNI · con SNI), e ⛔ **due gradini per gamba**: la stretta di mano riesce **e** l'impronta del certificato ricevuto combacia con quella del file |
| ⭐ `banchi/01-b2-sni-quiche.sh` | **nuovo, 10 agosto**: la terza candidata. ⛔ **Due azioni separate — `leggi` e `costruisci`** — perché se leggere e misurare stanno nello stesso comando la previsione la si scrive **dopo** aver visto il risultato, cioè non la si scrive. ⭐ E **sceglie la versione**: confronta il `rust-version` di ogni etichetta col compilatore presente, e dice quale e perché |
| ⭐⭐ `banchi/rcp/rcp.c` + `rcp.h` | **nuovo, 10 agosto**: ⭐ **la stretta di mano di RCP/1 E IL BAN DELL'INDIRIZZO, in C** — `[M]` **11 agosto 2026** (`wc -l` su questo albero, codice fermo alle 00:36): `rcp.c` **2.566 righe / 1.418 di codice**, `rcp.h` **197 / 54**. ⚠ *Diceva «**1292 righe / 875 di codice**, `rcp.h` **131 / 49**», `[M]` delle **ore 16:30 del 10 agosto**, e alle 23:48 il file ne misurava già 2.339: lo scarto era dell'**81 %** — rilievo **R12C.12**. E prima ancora diceva «807 righe, 662 di codice», il conto della mattina. ⛔ **La cura era già in questa tabella, tre righe più giù**, applicata a un numero della stessa natura (la riga del collante di B2, che porta «alle 08:00 la stessa misura dava 456/329»): una cura applicata in un posto solo, dentro la stessa tabella.* ⛔ **E la riga non nominava il ban**, che è il lavoro della notte del 10 — `FINESTRA` di 5 minuti, `BAN_DURATA` di 12 ore, `salva_ban`, `rcp_ban_carica`, `rcp_sblocca`, `rcp_bannato`, la tabella da 256 posti con lo sfratto che non butta mai una voce bannata — cioè la decisione dell'utente del giorno (`DECISIONI.md` §1.9). ⛔ **E questo numero non c'entra con quello dello strato WebTransport**: il protocollo **non dipende da ngtcp2** — riceve byte, restituisce byte, e non entra in nessuna delle misure di collante di B2. ⛔ **Non sa che sotto c'è QUIC**: riceve byte, restituisce byte, e il tempo glielo passa chi lo ospita. È la ragione per cui potrà passare al server vero senza riscritture, e per cui §6.4 — se si riaprisse — non porterebbe via il protocollo |
| ⭐ `banchi/rcp/autenticazione.c` | **nuovo, 10 agosto**: `[M]` **99 righe / 52 di codice** (ore 16:30) — PAM, derivato da `v1/remotix-c/src/autenticazione.c` con ⛔ **la cura di B10** — è caduto il confronto con l'utente del processo, che contraddiceva il multi-tenant di `SPECIFICHE.md` §5.5 |
| ⭐ `banchi/01-b3-rcp-innesta.py` | **nuovo, 10 agosto**: ⛔ **un innesto SEPARATO da quello di B2**, perché quel numero misura WebTransport e farlo crescere con RCP dentro renderebbe due misure diverse sotto la stessa etichetta (E2) |
| ⭐ `banchi/01-b3-cliente.py` | **nuovo, 10 agosto**: **il cliente di prova** — la stretta di mano scritta una seconda volta, in un linguaggio diverso, e **registra** nel formato di §11.1 con la parola d'ordine oscurata |
| ⭐ `banchi/01-b3-lancia.sh` + `01-b3-terzo-giro.sh` | **nuovi, 10 agosto**: le tre connessioni di B3, e ⛔ **ogni traccia passa dal validatore di B4** — non si collauda il server contro il client |
| ⭐⭐ `banchi/01-b3-quarto-giro.sh` | **nuovo, 10 agosto**: l'**orologio del silenzio** — 35 s a `max_idle_timeout` 120, con il controllo a +6 s che dice **no**. ⛔ Senza quel primo tempo, «dopo 35 s la seconda entra» è compatibile con «la seconda entra sempre» |
| ⭐⭐ `banchi/01-b3-quinto-giro.sh` | **nuovo, 10 agosto**: ⚠ **gira da questa parte del filo** — ruota il certificato, riavvia, e prova che la pagina ritira l'**impronta corrente**. ⛔ E che con la **vecchia** non si apre: senza quel controllo, «funziona con la nuova» è compatibile con un browser che l'impronta non la guarda |
| ⭐⭐ `banchi/01-b4-validatore.py` | **nuovo, 10 agosto**: ⭐ **il validatore del filo** — un terzo programma che legge una registrazione e dice **quale byte** non è conforme a `RCP.md`. ⛔ Scritto leggendo **solo la specifica**, prima che esistesse un byte di server. Ha **tre** esiti, non due: conforme · non conforme · ⚠ *registrazione malformata*, perché «il file è rotto» e «il filo non era conforme» sono due fatti con due cure |
| ⭐ `banchi/01-b4-registrazioni.py` + `01-b4-lancia.py` | **nuovi, 10 agosto**: le **sette** registrazioni, ciascuna col **byte offensivo dichiarato in anticipo** in un manifesto — e il confronto lo fa il banco, non chi guarda |
| ⭐ `banchi/01-b2-sonda-trasporto.py` + `01-b2-lancia-trasporto.sh` | **nuovi, 10 agosto**: le sei proprietà, lette **dal pari** con una spia dichiarata su `pull_quic_transport_parameters` di `aioquic`. ⛔ Hanno trovato due difetti che nessun banco funzionale vedeva, e il secondo giro (`--timeout=10s`) misura la proprietà che serve a **B3** |
| ⭐ `banchi/01-b2-sonda-impostazioni.py` | **nuovo, 10 agosto**: legge **sul filo** quali impostazioni un server HTTP/3 dichiara (`received_settings` di `aioquic`), e dice se c'è WebTransport. ⛔ È la prova che ha chiuso §6.4, e stampa **tutte** le impostazioni: un elenco vuoto e uno senza le due che interessano sono due fatti diversi |
| `banchi/01-b2-quiche-wt-innesta.py` + `01-b2-lancia-impostazioni.sh` | **nuovi, 10 agosto**: accendono su `quiche` tutto quel che la sua API C permette (3 righe di codice), e conducono il confronto con `ngtcp2` come **controllo positivo** |
| ⭐⭐ `banchi/01-b2-ngtcp2-wt-innesta.py` | **nuovo, 10 agosto**: ⭐ **il server minimo** — innesta lo strato WebTransport nel server d'esempio di `ngtcp2`. ⛔ Ogni innesto ha un **appiglio che deve comparire una volta sola**: zero o due, e lo script si ferma dicendo quante ne ha trovate. E **conta le righe nostre** da `git diff`, che è il dato di §6.4 |
| ⭐ `banchi/01-b2-lancia-wt.sh` | **nuovo, 10 agosto**: misura il server minimo col cliente di prova, ⛔ **e col controllo che dice no** — `/rcp/9` deve essere rifiutato (`RCP.md` §2.2). `accendi`/`spegni` servono alla misura col browser |
| ⭐ `banchi/01-b2-lancia-sonda.sh` | **nuovo, 10 agosto**: ⚠ **gira sulla macchina di chi guarda, non sul server** — i browser stanno lì. Accende il server dall'altra parte, serve la pagina da `127.0.0.1`, lancia i due motori sotto `xvfb` e aspetta che il **registro cresca**, non un tempo fisso |
| `banchi/01-b2-sonda.html` | **corretto**: `?avvia=1` fa partire la prova da sé. ⛔ Un banco che ha bisogno di una mano **non si può rifare uguale**, e rifarlo uguale è l'unico modo di sapere se una misura è cambiata perché è cambiato il server |
| `banchi/01-b2-raccogli.py` | **corretto**: registra **ogni richiesta**. Prima taceva, «il rumore non serve» — ed è quel silenzio che ha reso indistinguibili «il browser non ha caricato la pagina» e «l'ha caricata e la prova è fallita» |
| ⭐ `banchi/01-b2-lancia-sni.sh` | **nuovo, 10 agosto**: conduce la prova sui **tre** bersagli — `ngtcp2`, `quiche`, e `lsquic` come **controllo negativo** in coda, che a ogni esecuzione ridimostra che la sonda sa vedere un rifiuto. ⛔ Verifica che le porte siano libere **prima**, che i server ascoltino davvero (`ss`, non solo «il processo è vivo»), e li ferma **per PID** |
| `v1/banco/provision.sh` | **corretto**: `libev-dev` fra i pacchetti — è quel che serve agli esempi di `ngtcp2`, ed è **un'altra libreria** da `libevent-dev` che c'era già. ⚠ Senza, cmake mette `LIBEV_LIBRARY-NOTFOUND` e **salta gli esempi senza dire niente** |
| `v1/banco/provision.sh` | **corretto**: `golang-go` fra i pacchetti del contenitore. Serve a compilare BoringSSL, che è la sola pila TLS con cui `lsquic` e `quiche` parlano QUIC. ⛔ Nel provisioning, non a mano (`LEZIONI.md` §2.5-bis) |

> ### ⛔ E i banchi che questa tabella non nominava — undici, contati
>
> *Rilievo **R12C.13**. Questa tabella si fermava a B5 e agli innesti di B2, mentre il README
> dichiarava chiusi B6, B7, B8 e B11 e la notte del 10 ne ha fatti nascere altri quattro. ⛔ La
> regola con cui **R11.21** era stato chiuso sta nel `README.md` e vale identica qui: «un banco che
> non è nominato dove si dice come rimettere in piedi i banchi **non si può rifare uguale**», e
> rifarlo uguale è l'unico modo di sapere se una misura è cambiata perché è cambiato il server.
> Aggiunti l'11 agosto 2026.*
>
> | | |
> |---|---|
> | `banchi/01-b6-lancia.sh` + `01-b6-tetti.py` | **B6**, i tre tetti di §4.6. ⭐ Legge i `#define TETTO_*` **da tutt'e due** le copie del sorgente — quella dei banchi e quella compilata — e pretende che combacino, «perché una copia stantia darebbe un numero che nel binario non c'è». ⭐ E ha **tre esiti separati**: il server sbaglia · il **documento** sbaglia · non ho saputo classificare |
> | `banchi/01-b7-lancia.sh` + `01-b7-congedo.py` | **B7**, il congedo dal lato che riceve. ⛔ Dichiara il **denominatore vero**: §8.2 ha **quindici** motivi, i provocabili in questa fase sono **sette**, e gli altri otto stanno in una tabella `ESCLUSI` con la ragione di ciascuno |
> | `banchi/01-b8-lancia.sh` + `01-b8-cronometro.py` + `01-b8-prova-ban.c` + ⭐ `01-b8-sblocca.py` | **B8**, il secondo fisso e il ban. ⭐ `01-b8-sblocca.py` **non è un pezzo di B8**: è lo strumento della regola **B0.3**, e parla il socket di comando di §4.4-bis con tre esiti distinti (`TOLTO` · `NON-BANNATO` · «non ho parlato con nessuno», che esce **3**) |
> | ⭐ `banchi/01-b9-letture.py` | **B9**, il secondo lettore messo a confronto con l'arbitro: **dodici** punti in cui `RCP.md` ammette due letture, ciascuno con **i byte che cambiano sul filo**. L'elenco sta in «Che cosa NON ha funzionato» |
> | `banchi/01-b11-lancia.sh` + `01-b11-pagina.html` + `01-b11-guasto.sh` + `01-b11-guasto-innesta.py` | **B11**, le violazioni verso la **pagina**, col server guasto di proposito e `ricostruisci()` che rimette quello sano nei due `--togli` nell'ordine |
> | `banchi/01-b12-guasti.py` + `01-b12-lancia.sh` + `01-b12-copie/` + `01-b12-registro.jsonl` | **B12**, il banco che certifica gli altri: un guasto costruito a mano per ogni banco, e il registro delle certificazioni con la data e le impronte. ⛔ Quel che ha certificato davvero sta più sotto, ed è **3 su 12** |
> | `banchi/01-b13-lancia.sh` + `01-b13-proprieta.py` | **B13**, le sei cose che nessun altro banco guardava |
> | `banchi/01-c2-lancia.sh` + `01-c2-diagnosi.py` | **C2**, le tre diagnosi del collegamento guasto — nessuno in ascolto · UDP filtrato col TCP che risponde · impronta non corrente |
> | ⭐ **le sette pagine della sonda** | `01-s1b-eccezione.sh` + `01-s1b-pagina.html` + `01-s1b-sito.sh` + `01-s1b-servi.py` (**S1b**, l'orologio dei sette giorni) · `01-s2-pagina.html` (**S2**) · `01-s3a-pagina.html` (**S3a**) · `01-s5-tela.sh` + `01-s5-pagina.html` + `01-s5-raccogli.py` (**S5**) · `01-s6-pagina.html` (**S6**) · `01-s7-rotella.sh` + `01-s7-rotella.c` + `01-s7-pagina.html` + `01-s7-raccogli.py` (**S7**) · `01-s-telefono.sh` (le procedure che aspettano un dispositivo) |
>
> ⚠ **E i registri che quei banchi lasciano**, perché un banco senza il suo registro non è
> riverificabile: `banchi/01-s7-esiti.jsonl` · `01-s5-esiti.jsonl` · `01-s1b-stato.jsonl` ·
> `01-b12-registro.jsonl` · `b2-esiti.jsonl`. ⛔ **B6, B7, B8, B11, B13 e C2 non ne hanno nessuno**:
> i loro numeri vivono nell'uscita a schermo del giro, e quando la scena è smontata non ci si torna.

**Si riusa** (`PIANO.md` fase 1): `autenticazione.c` di v1 (144 righe) — ⛔ **con la cura di B10**,
e quel che ne è uscito misura **99 righe / 52 di codice** `[M]` — e `registro.c` (140) — ⚠ **con
l'obbligo di B13.2**.

---

# Le misure

*⛔ Con la scena, il dispositivo e la **versione** dichiarati accanto a ogni numero (B0.6).*

### La sonda

⛔ **Gli esiti per esteso, con i registri e la ricontata dei numeri, stanno in
[`web/rapporti/S-esiti-sonda.md`](../web/rapporti/S-esiti-sonda.md)** — qui c'è il numero con la
data, come vuole B0.6. ⚠ *Fino all'11 agosto 2026 queste sei celle erano **vuote** mentre tre delle
misure erano state prese la notte del 10: chi leggeva questo documento credeva che la misura non ci
fosse (rilievi **R12.7** e **R12C.7**, e la sonda lo aveva scritto di suo — voce S.6 del suo §9).*

| # | Che cosa | Dispositivo · versione | Atteso | Misurato | Data |
|---|---|---|---|---|---|
| S1b | durata dell'eccezione su Chrome | **Chrome 151.0.7922.108**, profilo persistente, `Xvfb :77 1280x1024x24` | **7 giorni** `[R]` | ⏳ **AVVIATA — giorno 0 preso.** Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z** `[M]` (grezzo su disco, conversione dichiarata). ⚠ `[?]` **che siano 604 800 s esatti dal clic**: l'istante del clic non l'ha registrato nessuno. Il numero sul campo si legge **il 17-18 agosto** | **10 ago**, 21:10:01Z |
| S2 | HEVC Main10 **in hardware** | ✅ telefono + PC per `chrome://inspect` | `[?]` — ⛔ *non «sì da Chrome 108»* | ⛔ **non eseguita**: manca il telefono, manca il PC per il controllo C, e le cinque sequenze dipendono dal codificatore della **fase 2**. ⭐ Banco pronto: `01-s2-pagina.html`, e finché A e B non passano **non pubblica verdetti** | |
| S3a | tastiera, nei tre stati di O8 | ✅ DeX — ⚠ `[?]` **verificare che sia ≥ Android 16 QPR1** | `[?]` | ⛔ **non eseguita**: manca il DeX. ⚠ E una riga di S3 §4.4 non è eseguibile **nemmeno col DeX**: `requestFullscreen({keyboardLock})` vuole **Firefox ≥ 151** e questa macchina ha la **140.13.0esr** — chi provasse qui misurerebbe l'assenza della lock e la scambierebbe per scorciatoie perdute | |
| S5 | tela dichiarata, zoom 100 %/150 % | **Chrome 151.0.7922.108** e **Firefox 140.13.0esr** su `Xvfb 1920×1080×24` (⛔ il **DeX** manca) | **uguale nei due**, e = risoluzione fisica | ⛔ **I DUE MOTORI NON CONCORDANO.** Firefox: `screen` 1280×720 a 150 % ⇒ tela **1920×1080**, invariante ✅. Chrome: `screen` resta 1920×1080 ⇒ tela **2880×1620**, del **50 % più grande** ⛔. `[M]`, due giri identici, `01-s5-esiti.jsonl`. ⇒ la formula di `SPECIFICHE.md` §6.1-bis **non regge su Chrome** | **10 ago**, 23:13-23:14 |
| S7 | segno della rotella, `natural-scroll` nei due stati | **server 192.168.0.2**, GNOME headless, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**, **Firefox 140.13.0esr** in `--kiosk` | `[?]`, e **non deve cambiare** con la gsetting | ⭐ **`+120` → `deltaY +114`, la pagina SCENDE** ⇒ ⛔ **il server inverte l'asse verticale**. `[M]`, due giri, `01-s7-esiti.jsonl`. Il segno **non cambia** fra i due giri ⚠ (`[?]` che fossero i due stati di `natural-scroll`: l'etichetta non è nel registro). ⛔ Misurata **su Mutter**: per gli altri quattro desktop resta `[?]` | **10 ago**, 20:59 UTC |
| S6 | carico utile di un datagram, **sul percorso peggiore** | ✅ telefono su LTE | ≥ **972 byte** | ⛔ **non eseguita**: manca una LTE vera e manca la metà di server che faccia l'**eco** dei datagram. ⭐ Banco pronto: `01-s6-pagina.html`, che **si rifiuta di misurare senza `?percorso=`** | |
| ⛔ S1a | eccezione ⇒ WebTransport su Safari | ⛔ **niente Mac** | *fuori dalla fase, resta `[?]`* | | |
| ⏳ S3b | PWA su Chrome per Android | ⛔ + certificato vero | *rimandata* | | |
| ⏳ S4 | anello del ritardo del disegno | | *→ fase 3* | | |

### Il filo

⚠ *Tre `[M]` di **B3** — la 2ª mentre la 1ª è viva, l'orologio del silenzio, la 3ª col certificato
ruotato — stavano in questa tabella **senza la cella della data**, in un capitolo che apre
imponendola: rilievo **R11.17**. La data c'è dal 10 agosto 2026, e la cella mancante non era
formalismo — `[M]` è definito come «misurato da noi, sul ferro, **con la data**» (`README.md`), e
la riga della 3ª è quella che dichiara un esito su **due browser**, cioè quella che B0.6 nomina per
prima.*
⚠ *E la stessa cura è dovuta tornare l'11 agosto 2026, tre righe sotto quel riquadro: la riga di
**B8** portava il suo `[M]` nella colonna dell'**atteso**, con «Misurato» e «Data» vuote e il «10
ago» dentro il testo invece che nella cella — rilievo **R12C.14**. ⛔ Il controllo meccanico che
aveva trovato R11.17 (contare le `|`) qui **non vede niente**: le celle sono cinque su tutte le
righe, e il difetto è nel loro **ordine**. Cioè la cura era stata applicata alla forma che il rilievo
descriveva e non alla proprietà che il rilievo proteggeva — che è, di nuovo, «una cura applicata in
un posto solo».*

⛔ **E la scena, che B0.6 pretende accanto a ogni numero**: i giri **1-4** di B3 li fa il cliente
`banchi/01-b3-cliente.py` contro il server minimo su `ngtcp2`, sulla macchina di prova — **nessun
browser**, quindi nessuna versione di browser da annotare; il **quinto** (certificato ruotato) è
l'unico coi browser veri, e le loro versioni sono dentro la riga.

| Che cosa | Atteso | Misurato | Data |
|---|---|---|---|
| **B2** — BoringSSL compila nel `devroot` | sì | ✅ **sì** — ramo predefinito, `libssl.a` e `libcrypto.a` | 9 ago |
| **B2** — `lsquic` compila con `-DLSQUIC_WEBTRANSPORT=ON` | sì | ✅ **sì**, v4.9.3, e la define è nei `FLAGS` di `build.ninja` | 9 ago |
| ⛔ **B2** — **il flag ha prodotto i simboli?** | **4 su 4** | ⭐ **4 su 4** `[M]` — dopo aver curato il banco, vedi sotto | 9 ago |
| **B9** — `aioquic` porta WebTransport? | `[?]` | ⭐ **sì** `[M]` 1.2.0: 29 occorrenze nel modulo h3, l'evento e `create_webtransport_stream`. *Era la `[?]` di R3.21: se fosse stata «no», cadeva l'arbitro* | 9 ago |
| **B2** — i due certificati, quattro controlli | 4 su 4 | ✅ **4 su 4** — e i due sono davvero due | 9 ago |
| ⭐ **B2** — **il controllo positivo d'ambiente** (senza browser) | sessione accettata **e** byte che tornano | ⭐ **`:status = 200`, `b'ciao'` torna identico** `[M]` | 9 ago |
| ⭐ **B2** — **la sessione si apre da un BROWSER VERO** | si apre, e i byte tornano | ⭐ **APERTA in 30,2 ms** su **Chrome 151.0.0.0** (X11, Linux), `"ciao"` torna identico `[M]` | 9 ago |
| ⭐ **B2** — lo stesso su **Firefox** | si apre | ⭐ **APERTA in 52,0 ms** su **Firefox 140.0**, `"ciao"` torna identico `[M]` | 9 ago |
| ⭐ **B2** — ⛔ **`ngtcp2` serve il certificato SENZA SNI?** | **sì** (previsione scritta prima: zero ricerche per nome in 109+18 file) | ⭐ **sì** `[M]` — sessione stabilita, e **l'impronta del certificato ricevuto combacia** con quella del file | 10 ago |
| **B2** — lo stesso con SNI, il controllo | sì | ✅ **sì** — `remotix.prova` | 10 ago |
| ⭐ **B2** — ⛔ **`quiche` serve il certificato SENZA SNI?** | **sì** (previsione scritta prima: l'unico punto che nomina l'SNI è un **lettore**, `tls/mod.rs:510`) | ⭐ **sì** `[M]` su **`quiche` 0.28.0** — sessione stabilita, **impronta combaciante** | 10 ago |
| **B2** — lo stesso con SNI, il controllo | sì | ✅ **sì** | 10 ago |
| ⛔ **B2** — quale `quiche` si costruisce con `rustc` di Trixie? | *non era una domanda* | ⛔ **la 0.28.0**: la **0.29.3 pretende rustc 1.88**, Trixie ha **1.85** `[M]` | 10 ago |
| ⭐ **B2** — il **controllo negativo**: `lsquic` senza SNI | **fallisce** | ⭐ **fallisce** `[M]`, e il suo registro dice **perché**: `SNI is not set … fail certificate lookup` | 10 ago |
| ⭐ **B2** — `lsquic` **con** SNI: trova il certificato? | sì — *la metà che mancava alla diagnosi del 9* | ⭐ **sì** `[M]`: `looked up cert for remotix.prova`. ⚠ poi cade su ALPN (avviso 120), **causa non indagata** | 10 ago |
| ⭐⭐ **B2** — **la sessione si apre da un BROWSER VERO, su `ngtcp2`** | 2 motori su 2 | ⭐ **2 su 2** `[M]`: **Chrome 151.0.0.0** (118,6 ms) e **Firefox 140.0** (140,0 ms), impronta pubblicata, nessun avviso, `"ciao"` torna identico | 10 ago |
| ⛔ **B2** — e il percorso **sbagliato** si rifiuta? | non 200 | ⭐ **404** su `/rcp/9` `[M]`, come impone §2.2 (R1.24) | 10 ago |
| ⭐ **B2** — le sei proprietà della libreria | 6 su 6 | ⭐ **6 su 6** `[M]`, e **lette dal pari, non dal registro del server**: `max_idle_timeout` 30 000 ms · datagram 65 536 · credito uni **16** · migrazione **non** disabilitata · **niente 0-RTT** · `allowPooling: false` | 10 ago |
| ⛔ **B2** — e il tetto d'inattività si può **cambiare**? (serve a B3) | il pari vede il valore nuovo | ⭐ **sì** `[M]`: con `--timeout=10s` il pari legge **10 000 ms**. B3 potrà distinguere il tetto del protocollo da quello del trasporto | 10 ago |
| ⛔ **B2** — ⭐ **due difetti trovati proprio da queste misure** | *nessuno era atteso* | ⛔ il server offriva **0-RTT** (2 biglietti, `max_early_data_size` 0xffffffff) e concedeva **3** stream unidirezionali invece di 16. **Nessuno dei due ha un sintomo funzionale**: la sessione si apriva uguale | 10 ago |
| ⛔⭐ **B2** — **`quiche` riesce a dichiarare WebTransport dal C?** | **no** (previsione scritta prima: `set_additional_settings` esiste in Rust, **non nell'FFI**) | ⛔ **no** `[M]`: 4 impostazioni sul filo, **nessuna** delle due di WebTransport. Il controllo positivo (`ngtcp2`) ne dichiara 7 | 10 ago |
| **B2** — la sessione si apre, **per candidata** | 2 motori su 2, **e le sei proprietà** | ⭐ **fatto su `ngtcp2`**; su `quiche` **non si arriva a provarlo**: cade al cancello prima | 10 ago |
| ⭐ **B2** — righe di collante **per lo strato WebTransport** | *si conta, non si stima* | ⭐ **`ngtcp2`, lo strato di B2 da solo: 553 righe aggiunte — 373 di CODICE, 134 di commento, 46 vuote** `[M]` **ore 16:30**, su albero pulito dopo i due `--togli` e riapplicando il solo innesto di B2. ⚠ *Alle 08:00 la stessa misura dava **456 / 329**: la lettura della capsula di chiusura è cresciuta lì dentro. La successione sta in `DECISIONI.md` §6.4, non qui.* ⛔ **I 972 / 618 dei due innesti insieme non vanno in questa riga.** ⚠ Su `quiche` il numero **non esiste e non esisterà**: la candidata cade prima, ed è il lavoro che non abbiamo speso | 10 ago |
| **B2** — quanto pesa il loro esempio (il punto di partenza) | *si conta* | `ngtcp2` **7.041 righe** (HTTP/3 completo, C++, 13 file) · `quiche` **614** (esempio minimo, C, 1 file) `[M]`. ⛔ Due etichette diverse: non si sottraggono | 10 ago |
| ⭐ **B3** — la **1ª** connessione, fino a `SESSIONE` | passa | ⭐ **passa** `[M]` 10 ago: `CIAO`→`ECCOMI`→`CREDENZIALI`(PAM)→`AMMESSO`→`ATTACCA`→`SESSIONE`, e ⛔ **la traccia è dichiarata CONFORME dal validatore di B4** | 10 ago |
| ⭐ **B3** — la **2ª dopo la chiusura della 1ª** | **identica alla prima** | ⭐ **passa** `[M]`, e anche la sua traccia è conforme. ⛔ **Non lo era al primo giro**: vedi il difetto qui sotto | 10 ago |
| ⭐ **B3** — la **2ª mentre la 1ª è viva** | `CONGEDO(0x0F)` a chi arriva, e la 1ª sopravvive | ⭐ **passa** `[M]`: la seconda riceve `GIA_ATTIVA_REMOTA` **per tutt'e due le strade di §3.1** — `CONGEDO` sul controllo *e* codice `0x0f` nella chiusura della sessione — e la prima sopravvive. ⚠ *Era rossa al primo giro, e il difetto era del banco* | 10 ago |
| ⭐⭐ **B3** — la 2ª **dopo il silenzio** della 1ª, 35 s a `max_idle_timeout` **120** | **entra** | ⭐ **entra** `[M]`, e ⛔ **con il controllo che dice no**: a **+6 s** la seconda è **rifiutata** con `0x0F`, a **+35 s** la terza **entra**. Il registro: `STACCATO per silenzio: 30072 ms`. ⭐ E la connessione della prima è **ancora viva**: a liberare il posto è stato **il server**, non QUIC | 10 ago |
| ⭐ **B3** — la 3ª con il certificato **ruotato a mano** | passa | ⭐ **PASSA, pieno** `[M]` **2026-08-10 sera**: rotazione (impronta nuova ≠ vecchia, quattro controlli sui certificati su quattro), la pagina ritira la nuova e apre su Chrome 151 e Firefox 140, **e il server risponde `ECCOMI` al `CIAO` della sonda** — la seconda metà del criterio di B2 è soddisfatta —, e con la vecchia **tutt'e due rifiutano**. ⛔ Il rosso del mattino era della SONDA, non del certificato: mandava `ciao` e aspettava l'eco di B2, che con RCP innestato non esiste più. ⚠ Resta `[?]` che a rifiutare sia il confronto dell'impronta e non una delle altre due cause con lo stesso aspetto.<br><br>*Quel che diceva prima* `[M]` **2026-08-10 09:36**, Chrome **151.0.0.0** e Firefox **140.0**: con l'impronta corrente (`5o99/7rSTJER…`) la **sessione si apre** su tutt'e due — 149,0 ms Firefox, 180,0 ms Chrome — ⛔ **ma lo stream non ha funzionato in nessuno dei due** (`remote WebTransport close` · `The session is closed.`), e il criterio di B2 vuole *«la sessione si apre su Chrome e Firefox, **e la pagina riceve un byte dal server**»*. ⚠ Con l'impronta vecchia (`35wqjGTOmKSj…`) **tutt'e due rifiutano** — Firefox `WebTransport connection rejected`, ⚠ Chrome `Opening handshake failed.`, *due frasi diverse* — ma `[?]` **che a rifiutare sia il confronto dell'impronta non è dimostrato**: l'esito registrato dichiara di suo **tre cause con lo stesso aspetto** (UDP filtrato · impronta non del certificato servito · certificato oltre i 14 giorni), e nessuno le ha distinte. È la forma **E1**, e il banco l'aveva già dichiarata | 10 ago |
| ⭐ **B3** — il **secondo fisso** di §4.4-bis, cronometrato | ≥ 1000 ms **anche su `AMMESSO`** | ⭐ **1074–1085 ms** `[M]` su tre connessioni. È una proprietà che nessun altro banco vede | 10 ago |
| ⭐ **B10** — PAM, con `pamtester` come controllo | entra | ⭐ **entra** `[M]`: `pamtester login prova authenticate` riesce, e il server ammette lo stesso utente | 10 ago |
| ⭐ **B4** — sette guaste, quattro rotte, una conforme, una senza niente da giudicare | i **quattro esiti** coperti, byte esatto | ⭐ **13 su 13** `[M]` 10 ago sera: ciascuna guasta accusata sul **byte dichiarato in anticipo**, e i quattro codici d'uscita del validatore tutti esercitati (0 conforme · 1 non conforme · 2 registrazione rotta · 3 niente da giudicare). Il validatore è **certificato** | 10 ago |
| ⭐⭐ **B4** — e ha trovato una contraddizione in `RCP.md` | *non era un atteso* | ⛔ §4.3 vietava il trattino basso nei nomi di capacità **e ne definisce uno che ce l'ha** (`video.misura_massima`). Curato in `RCP.md` §4.3 | 10 ago |
| ⭐⭐ **B5** — le violazioni, e il server vivo dopo ciascuna | motivo giusto sempre, **server vivo sempre** | ⭐ **36 violazioni su 36 + 8 verdi attesi su 8** `[M]` 10 ago sera, e per **tutt'e due le strade di §3.1** ogni volta — ⛔ **36 su 36 anche sul punto 3**, che nessuno aveva mai contato: `CONGEDO` sul controllo *e* il codice del motivo nella chiusura della sessione. ⛔ E dopo **ciascuna** una connessione nuova arriva a `ECCOMI`: il server è sempre lì | 10 ago |
| ⭐ **B5** — i cinque casi che **devono passare** | *nessuna caduta* | ⭐ **5 su 5** `[M]`: `hevc,vp9` sceglie `hevc` e scrive lo scarto · **vista 300×801** e **1×1** passano (§7.1, R4.10) · `BANCO_MARCA` a funzione spenta risponde `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` e **la sessione regge** · `ritardo_ms = 20000` → `RITARDO_FUORI_LIMITI`, **non** `ERRORE_PROTOCOLLO`. ⛔ Senza di loro «il server chiude su tutto» darebbe 44 verdi su 44 | 10 ago |
| ⭐⭐ **B5** — e ha trovato **un difetto che nessun altro banco vedeva** | *non era un atteso* | ⛔ il contatore **per indirizzo** di §4.4-bis era chiavato sulla `provenienza`, che contiene **la porta**: con un solo tentativo per connessione (§4.4) la porta cambia ogni volta, e quel contatore **valeva sempre 1**. Codice presente, che sembrava giusto, e che non faceva niente. Curato, e ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — anche per la parola d'ordine **giusta**. ⚠ *Il **sesto** è della regola di quel giorno; dal 10 agosto sera la regola è il **ban al quarto** (`DECISIONI.md` §1.9), e questa riga resta com'è perché una misura porta la data della regola che misurava* | 10 ago |
| ⭐ **B5** — e una **seconda contraddizione in `RCP.md`** | *non era un atteso* | ⛔ §2.2 dice che un `CIAO(2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`; §9 dice che il server sceglie *«la più alta che non superi quella del `CIAO`»*, cioè `ECCOMI(1)`. **Byte diversi sul filo per lo stesso ingresso**, e nessuna delle due cita l'altra. Vince §2.2 (la più specifica); `RCP.md` §9 curata. ⚠ *La cura citava **§2.4**, che è «La porta»: numero corretto lo stesso giorno, rilievo **R11.2*** | 10 ago |
| ⭐⭐ **B11** — le violazioni verso la pagina | 13 su 13 | ⭐ **13 su 13 su TUTT'E DUE i motori** `[M]` 10 ago sera — Firefox **140.0** e Chrome **151.0.0.0**, `CONFORME` con **0 guasti** — **più le due proprietà negative** (`desktop` non cambia i byte usciti · nessun battito applicativo). ⭐ **E ripetuto**: due giri completi conformi, `15:51:54`+`15:52:28` e `15:54:51`+`15:55:24`. ⚠ *Alle 11 questa riga diceva «12 su 12 su Firefox, 9 su 12 su Chrome»: i tre rossi di Chrome sono stati chiusi la sera stessa, e questo documento era rimasto indietro fino al rilievo **R11.4** del 10 agosto* | 10 ago |
| ⛔ **B11** — e il controllo che dice **no** | la pagina contro un server **SANO** deve dire NON-CONFORME | ⭐ **NON-CONFORME** `[M]`, **9 casi su 13** falliti. Senza, «tredici verdi» sarebbe compatibile con una pagina che approva qualunque cosa. ⚠ `[?]` **gira su un motore solo** (Firefox), e il banco lo dichiara di suo — **rilievo R11.24**. ⭐ *Dalla notte del 10 agosto 2026 lo dichiara anche il `README.md`, che prima lo elencava dentro «su tutt'e due i motori»: resta da **eseguirlo anche su Chrome**, e la differenza morde proprio qui, perché i tre casi rossi di stasera vivevano **nella differenza fra i due motori*** | 10 ago |
| **B6** — i tre tetti | 5 s · 60 s · 10 s, **col motivo giusto** | ⚠ **5,0 · 60,1 · 10,0 s**, e ⭐ **il cronometro parte dall'apertura del CANALE DI CONTROLLO** — R3.27 chiusa, `RCP.md` §4.6 riga 1 cambiata di una parola. ⛔ **E una seconda risposta**: la sessione che il canale non lo apre mai **non ha addosso nessun tetto** (`DECISIONI.md` §7.17). ⛔ **Questi tre numeri non hanno un registro**: non esiste nessun `.jsonl` di B6, la scena di quel giro non è dichiarata da nessuna parte e **non sono riverificabili** — si rifanno col registro, o restano tre numeri di cui si sa solo l'ordine di grandezza | **10 ago**, ora non registrata |
| **B7** — i motivi dal lato che riceve, frasi distinte, nessun numero | ⛔ **7 provocabili su 15 dichiarati** + **15 frasi distinte** | ⭐ **7 su 7 + 15 su 15**, con gli **otto esclusi** e la ragione di ciascuno. ⚠ *L'atteso di questa riga diceva «**8 su 8** + 8 frasi distinte», e l'ottavo — `SERVER_IN_CHIUSURA` — è quello che il banco **misura** di non poter produrre sull'innesto* | **10 ago** |
| **B8** — ≥ 1 s per campione, **e le tre mediane indistinguibili** | ≥ 1 s in **ogni** campione, e le tre mediane **indistinguibili** fra loro | ⚠ **parziale**: **2636 ms** di mediana sui **42** tentativi respinti, dove §4.4-bis vuole ~1000 ⇒ ⛔ **a governare i tempi è PAM, non il nostro ritardo fisso**. Le tre mediane **restano da confrontare**. ⚠ E il numero è la mediana **del servizio `login`**: il prodotto usa `remotix`, quindi con lui **la misura va rifatta** | **10 ago** |
| ⛔ **B8** — il ban: tre falliti con **tre nomi diversi**, poi il quarto con la parola **giusta** | il quarto **rifiutato** con `TROPPI_TENTATIVI`, e la pagina lo dice | | |
| ⭐ **B8** — i tre controlli che dicono *no* | un **altro** indirizzo entra · **2 falliti · 1 riuscito · 2 falliti** non banna · il ban **sopravvive al riavvio** | | |
| **B8** — lo sblocco, in fondo al giro | l'indirizzo rientra, e lo sblocco è **nel registro** | | |
| **B9** — `aioquic` porta WebTransport; la stretta di mano completa | sì; e **l'elenco delle ambiguità trovate** | ⭐ **12 punti su 12**, ciascuno con le due letture, la lettura che il secondo lettore ha scelto, **i byte che cambiano sul filo** e il caso concreto in cui la differenza morde. L'elenco sta in «Che cosa NON ha funzionato» — ⛔ **sono difetti del documento, non del banco** | **10 ago** |
| **B10** — l'utente `prova` entra, con `pamtester` come controllo | entra | ⭐ **entra** — vedi la riga di B10 qui sopra | **10 ago** |
| **B13** — le sei cose | 6 su 6 | ⛔ **non certificato**: il guasto costruito per lui **non è quello giusto** (accende il server con l'altro certificato, che B13.1 non guarda perché legge le impronte dei **file su disco**), e l'orchestratore non lo sa nemmeno innestare. `[M]` B12, 10 ago 22:24 e 22:25 | **10 ago** |
| **C1** — dodici guasti costruiti a mano | **12 rossi su 12** | ⛔ **3 su 12**, e le parole giuste per gli altri: vedi il riquadro «Che cosa B12 ha certificato davvero» | **10-11 ago** |
| **C2** — tre modi di fallire | **tre diagnosi diverse** | ⭐ **certificato** `[M]` 10 ago 22:32 (macchina `NIC-OS`), con una marca **discriminante**. ⚠ Un giro precedente (22:28) lo dava **non certificato**: fra i due è cambiato il file, non il verdetto — l'impronta di `01-c2-diagnosi.py` è diversa nelle due righe | **10 ago** |

---

# ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura* (`PIANO.md` §0.3 regola 2). ⭐ **E qui va ogni punto
in cui `RCP.md` ha ammesso due letture**: sono difetti del documento, e questa è la fase in cui
costano meno.

## ⭐⭐ I dodici punti in cui `RCP.md` ammette due letture — B9, 10 agosto 2026

*È **l'esito più prezioso di B9**, e questa sezione lo dichiarava in anticipo: «l'esito più prezioso
non è "passa": è ogni punto in cui chi lo scrive ha dovuto scegliere perché `RCP.md` ammetteva due
letture». `banchi/01-b9-letture.py` li ha trovati e li tiene con **gli appigli citati alla lettera**
— una citazione che non si trova più è una voce che parla di un altro documento — e con **i byte che
cambiano sul filo** fra l'una e l'altra. ⛔ Portati qui l'11 agosto 2026: finché stavano solo nel
banco, erano dodici difetti del documento che il documento non sapeva di avere.*

⛔ **Perché la colonna dei byte è quella che conta**: due letture che producono gli stessi byte sono
una questione di gusto. Queste **producono byte diversi per lo stesso ingresso**, cioè due
implementazioni conformi a `RCP.md` divergono senza che nessuna delle due abbia torto — che è
esattamente ciò che §0 esiste per impedire.

| # | Dove | La domanda | Che cosa ha scelto il secondo lettore | ⛔ Il byte che cambia |
|---|---|---|---|---|
| **L1** | §4.3 | `ECCOMI` porta **l'elenco** dei codec del server o **la scelta**? | ⚠ nessuna delle due: legge i due byte della versione e **butta il resto** — la lettura A **per omissione**, cioè la scelta fatta senza accorgersi di sceglierla | il valore di `video.codec`: `0008 «hevc,av1»` contro `0004 «hevc»`, e con lui la `lunghezza` u32 |
| **L2** | §3.1 punto 3 | il codice d'errore della chiusura: il motivo **nudo** nei 32 bit, o **mappato** come vuole HTTP/3? | A — e ⛔ **in più tronca**: legge l'**ultimo dei quattro byte**, quindi un codice sopra 255 gli arriverebbe come **un altro motivo**, senza una riga che lo dica | `00 00 00 0D` contro otto byte di un valore mappato — e la capsula cambia lunghezza. ⚠ `RCP.md` **non dichiara la larghezza del campo in nessun punto** |
| **L3** | §3.1 p. 2 contro §4.2 | dopo il `CONGEDO`, il canale si chiude **con un FIN** o si chiude solo la sessione? | B — non manda mai il FIN; e dal lato che riceve chiama il FIN *«il canale si è chiuso»*, che è un esito **diverso** da «sessione chiusa dal server» | il **bit FIN** del frame STREAM che porta il `CONGEDO`: gli stessi byte di carico, un bit di trasporto in più |
| **L4** | §6.1 | byte in più in coda al corpo, con la `lunghezza` che li conta: **violazione** o **riserva** per il futuro? | ⛔ **i nostri due lettori hanno scelto DIVERSAMENTE**: il cliente di prova legge `lunghezza` byte e passa il corpo così com'è (B, tollerante); il **validatore di B4** ha una registrazione apposta per bocciarlo (A) | quattro byte in coda e la `lunghezza`: `0000002A` contro `0000002E`. ⛔ È il difetto che B9 esiste per trovare: **l'arbitro e il secondo lettore non leggono la stessa specifica** |
| **L5** | §4.3 | una capacità **assente** è un elenco **vuoto** (⇒ `NIENTE_IN_COMUNE`) o una cosa **non negoziata**? | ⚠ **la domanda l'ha evitata**: dichiara sempre tutte e otto le capacità, quindi nessuna sua esecuzione la farà mai emergere | il campo `quante`: `0003` contro `0002`, e ventidue byte in meno |
| **L6** | §4.6 riga 1 | da quale istante parte il primo tetto? | ⛔ **ha scelto B6**, che lo fa partire dall'apertura del canale — ed è una scelta **del banco**, non del documento | ⛔ **nessuno, e va detto invece di inventarne uno**: le due letture mandano lo stesso `CIAO`. Cambia **quando** arriva il `CONGEDO(TEMPO_SCADUTO)` — e nel caso della sessione senza canale, **se** arriva. ⇒ `DECISIONI.md` §7.17 |
| **L7** | §2.2 | la `CONNECT` estesa deve portare un `origin`? | A — **lo manda**, copiando il browser. ⚠ È prudente e ha un prezzo: mandandolo, **non può più scoprire** se il server lo pretenda — l'arbitro si è adattato all'imputato | il campo `origin` nell'intestazione della `CONNECT`: una riga in più, compressa da QPACK |
| **L8** | §4.5 | un `desktop` fuori dai sei nomi: **campo fuori intervallo** (§3) o **stringa di diagnosi** da non guardare? | B — lo stampa e non lo controlla | la stringa in fondo a `SESSIONE`: `0005 «gnome»` contro `0007 «plasma6»` — e la connessione che sopravvive o cade. ⚠ **Le due letture stanno in sei righe, una sotto l'altra, e sono opposte** |
| **L9** | §11.1 contro §6.0 | nella registrazione, che cosa si scrive in `stream` quando l'identificatore non si conosce? | ⛔ **sempre zero** — ma §6.0 vieta i valori sentinella impliciti, e **zero è un identificatore di stream legale** (è quello della `CONNECT`) | gli otto byte di `stream`: `…04` contro `…00`. ⚠ E il validatore **non se ne può accorgere**: un campo sempre zero e un campo assente hanno lo stesso aspetto — forma **E8** |
| **L10** | §8.1 contro §4.4 | il client, dopo un `RESPINTO`, deve mandare `CONGEDO`? | ⚠ **una terza cosa**: non manda mai un `CONGEDO`, in nessun caso — cioè **non esercita mai** l'obbligo che §8.1 mette su chi chiude | un'inquadratura di **undici byte** contro **il silenzio**. ⛔ Il caso è già costato un rosso: il server contava come «byte dopo la fine» anche il congedo **conforme** della pagina |
| **L11** | §9 contro §2.2 | che versione mette nel `CIAO` un client che ne sa parlare **due**, su `/rcp/1`? | ⚠ scrive `1` a mano perché ne sa parlare una sola: **la domanda non gli si è posta**, e non se la porrà finché RCP/2 non esisterà | i due byte di `versione`: `0002` contro `0001` — e una connessione che vive o muore |
| **L12** | §4.5 contro §7.1 | i limiti 320×240-7680×4320 e la parità valgono anche per `vista_*` dentro `ATTACCA`? | ⚠ manda **vista = tela**: ancora una volta la domanda evitata, non risposta | `vista_larghezza`/`vista_altezza`: `00000780 00000438` contro `0000012C 00000321` (sotto il minimo e dispari). ⭐ **La risposta esiste ed è B**, ma sta in **§7.1** — chi implementa `ATTACCA` leggendo §4.5 non ha nessun motivo di andarci |

⛔ **Che cosa se ne fa**, e non è «si sistemano tutte adesso»: **tre** di queste dodici sono già
domande aperte dove le decisioni stanno — L3 in `DECISIONI.md` §7.14, L10 in §7.15, L6 in §7.17. Le
altre nove sono **difetti di scrittura di `RCP.md`**, e il posto in cui si curano è `RCP.md`, una
riga per volta, ⛔ **senza aggiungere tipi di messaggio**: la clausola di §9 è consumata dal 10
agosto.

⚠ **E una cosa che B9 dice di sé, e va letta**: `01-b9-letture.py` verifica che le due letture di
ogni voce producano **byte diversi**, e una voce «UGUALI» è **un rosso di B9**. Cioè l'elenco non
può crescere di voci inventate per far tornare la colonna — e L6, che byte non ne cambia, lo
**dichiara** invece di fabbricarne uno.

## ⛔ Tre trappole in un giro solo, e la terza non era nei banchi — 11 agosto 2026, sera

*Dal giro che ha certificato **B8**. ⭐ Le prime due sono difetti che il progetto aveva già scritto,
e la terza spiega perché le prime due erano rimaste invisibili.*

- ⛔ **La pagina del ban era illeggibile sull'innesto, e nessuno lo sapeva.** `leggi_pagina()`
  incartava **sempre** in TLS — `[M]` `SSLError: WRONG_VERSION_NUMBER` da tutt'e due gli indirizzi —
  perché l'innesto la serve **in chiaro**. ⇒ Il banco scriveva *«la pagina non si è caricata»*, cioè
  **il silenzio che §4.4-bis vieta al ban**, su un server che la pagina la serve. ⚠ **Ed era la cura
  del giorno prima ad averlo spostato**: era stata scritta per il **prodotto**, che vuole HTTPS. Due
  rossi opposti a un giorno di distanza, e in tutt'e due i casi **il server faceva la cosa giusta**.
  ⭐ Ora il dialetto lo **dichiara il bersaglio**, e se quello dichiarato tace si prova l'altro:
  *«il dialetto è l'altro»* è un fatto, *«non ho parlato con nessuno»* è un altro fatto.
- ⛔ **Due redirezioni ATTORNO a `enter.sh` — dentro i due file che quella trappola la descrivono in
  testa.** La richiesta di `sudo` esce su **stderr**: buttandola via, **nessuno può rispondere**.
  `[M]` `ps` sul server: `sudo -v -S -p Password` fermo, ⛔ **col guasto ancora addosso al codice**,
  che è il peggior punto in cui fermarsi. ⚠ Da un terminale interattivo è **invisibile** finché il
  credito di `sudo` regge: morde solo sui giri lunghi, cioè quelli che costano di più da rifare.
  ⇒ È la **quinta veste** della regola pagata il 10 agosto, e stavolta dentro i suoi stessi guardiani.
- ⛔⭐ **E la causa vera stava nello strumento, non nei banchi**: `v1/strumenti/sshpw.py` rispondeva
  ad al massimo **64** richieste di parola d'ordine, e un giro di certificazione di B8 — **tre**
  esecuzioni del banco, una sessantina di ingressi nel contenitore ciascuna — ne chiede **oltre
  200**. Il giro si fermava a metà del passo «guasto», ⚠ **e il sintomo era di nuovo quello che
  inganna: non un errore, una prova «lenta»**. Chi guardava il registro vedeva l'ultimo blocco
  stampato e credeva che stesse ancora misurando. ⚠ Il tetto era **già stato alzato una volta**, da 8
  a 64, per la stessa ragione: **è la terza**. ⭐ Il numero giusto non è *«quante ne servono oggi»*:
  a proteggere non è il tetto, è **l'ancora** che spedisce la parola d'ordine solo a chi la sta
  chiedendo **in quell'istante**.

## I difetti pagati, uno per uno

| | |
|---|---|
| ⛔ **la prima stesura del banco, 9 agosto** | 44 rilievi su due revisioni. La forma che si ripete: **cadeva sempre il controllo che dice *no***, e in tre casi era già stato scritto da chi ci era passato prima. ⚠ *Due delle tre amputazioni erano state bocciate da `R2` poche ore prima, con l'istruzione «curare prima di scrivere una riga di banco»: il documento che le doveva ereditare curate le ha ereditate intatte* |

### ⛔ Tre difetti di banco pagati in un'ora, sul primo banco eseguito — 9 agosto 2026

*E il terzo è il più istruttivo del progetto finora, perché **stava per cancellare la candidata
migliore** con un `[M]` falso contro un `[R]`.*

| # | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | `git clone -b master` di BoringSSL: *«Remote branch master not found»*. Google l'ha rinominato | ⚠ **un ramo scritto a mano è una dipendenza dal nome di qualcun altro**. Tolto: si prende il predefinito |
| **2** | ⛔ il fallimento è arrivato **con «uscita 0»** a chi guardava, perché avevo messo `\| tail` in coda al comando remoto: lo stato d'uscita era quello di `tail` | `LEZIONI.md` §1.9 — *zero e fallimento con la stessa faccia* — **presa nell'invocazione invece che nello script**. Il banco era innocente; chi lo lanciava no |
| **3** | ⛔⭐ il banco ha dichiarato **«0 simboli su 4»** stampando **i quattro simboli tre righe sopra** | vedi il riquadro |

> #### ⛔ Il terzo: `set -o pipefail` più `grep -q`, cioè un falso rosso garantito
>
> Il controllo era `nm -g --defined-only "$LIB" \| grep -q " $s$"`. **`grep -q` esce al primo
> riscontro** e chiude il tubo; `nm` sta ancora scrivendo, prende `SIGPIPE`, muore con **141**; e
> `set -o pipefail`, in cima allo script, fa valere **quel 141** come esito della pipeline.
>
> ⛔ **Il riscontro riuscito veniva letto come fallimento** — e la perversione è che *più il simbolo
> era facile da trovare, prima `grep` usciva, più sicuro era il falso rosso.*
>
> ⚠ **Che cosa avrebbe prodotto se nessuno avesse guardato**: la riga *«il flag di `lsquic` non
> produce niente»* in `DECISIONI.md` §6.4 — cioè **la candidata con più WebTransport dentro,
> cancellata da un difetto del banco**, con un `[M]` falso che avrebbe battuto un `[R]` letto nel
> codice. È `LEZIONI.md` §2.3 (*una prova che boccia il codice giusto costa quanto una che promuove
> quello sbagliato*) e `CODER.md` §3.11 (*quando codice letto e misura si contraddicono, il sospetto
> va prima sulla misura*) nello stesso difetto.
>
> ⭐ **Che cosa l'ha fatto emergere**: non l'intuito — **tre righe di strumentazione nel banco**, che
> dichiarano su quale archivio si sta guardando e quanti simboli si vedono *prima* di dire quali
> mancano. Ora sono permanenti: erano la differenza fra «chi dei due mente» e mezza giornata di
> supposizioni.
>
> ⚠ **E una quarta, che non è un difetto ma un'abitudine da prendere**: la diagnosi a mano era
> passata attraverso **tre shell annidate** (locale → ssh → `enter.sh` → chroot) e si è rotta sulle
> virgolette, restituendo `grep: ...: No such file or directory`. La regola della fase 0 vale qui:
> **le righe di comando si mettono in un file, non si ricordano**.

### ⛔ E il terzo difetto della stessa famiglia, che ha stampato un VERDE

*9 agosto, banco di `ngtcp2`.* Il controllo diceva **«nessuna traccia di `SETTINGS_WT_MAX_SESSIONS`:
la previsione regge»** — ⛔ **da una ricerca mai eseguita**. I due alberi erano passati a `grep` come
**una stringa sola**, quindi cercava in un percorso con uno spazio dentro che non esiste; e
`2>/dev/null` nascondeva il «No such file or directory» che l'avrebbe detto subito.

⛔ **È il peggiore dei tre, perché gli altri due davano rosso e questo ha dato verde** — e un verde
non lo si va a verificare. A insospettirmi non è stato il banco: è stato **un numero impossibile**
nella riga accanto — «extended CONNECT in 0 file» su una libreria che implementa RFC 9220.

⭐ **La cura è diventata una regola generale**, ed è entrata in `LEZIONI.md` §1.9 come **quarta
regola**: *una misura deve dichiarare su che cosa ha guardato — il denominatore, non solo il
risultato*. Adesso il banco stampa «dentro 447 file di 2 alberi» e **cerca una cosa che deve
esserci** (`nghttp3`, trovata in 110 file) prima di credere a uno zero.

### ⚠ `aioquic` sa creare uno stream WebTransport e non sa riconoscerlo quando risponde

*Trovato costruendo il controllo positivo, 9 agosto 2026, ed è del **cliente di prova** — quindi
tornerà a mordere a ogni fase in cui quello cresce.*

Il primo giro andava in **timeout aspettando il ritorno**, mentre il server dichiarava di averlo
spedito. `[R]` `H3Connection.create_webtransport_stream` di aioquic 1.2 scrive l'intestazione dello
stream e **non registra lo stream in ricezione**: i byte tornano — si vedono a livello QUIC — e il
livello H3 non emette nessun `WebTransportStreamDataReceived`.

⛔ **Che cosa l'ha distinto**: due righe che stampano gli eventi **a tutt'e due i livelli**. Senza,
*«i byte non arrivano»* e *«i byte arrivano e nessuno li riconosce»* sono lo stesso rosso — e sono
due difetti in due posti diversi. È la seconda volta in un'ora che la strumentazione batte
l'intuito.

⚠ **La cura è dichiarata, non nascosta**: il ritorno si legge a livello QUIC, **scrivendo perché**.
Fingere che l'abbia riconosciuto il livello H3 sarebbe stato comodo e falso.

### ⛔ Sei difetti di banco per una prova che dura due secondi — 10 agosto 2026

*La prova SNI di B2 è **una connessione**. Ci sono volute **sei esecuzioni** per arrivarci, e
nessuno dei sei difetti era della libreria che si stava misurando.*

| # | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | ⛔ **Due server della sessione del 9 agosto erano ancora vivi**, otto ore dopo, e tenevano le porte 7447 e 7448. `bsslserver` ha scritto *«Could not bind»* ed è morto | ⚠ Il rootfs del server è in RAM e **non si riavvia mai**: *«l'avevo fermato»* non è un'informazione. ⛔ E il rosso non sarebbe stato «il banco non parte», sarebbe stato **«`ngtcp2` rifiuta»** — un rosso attribuito alla libreria. Ora la porta si controlla **prima** |
| **2** | La sessione remota è rimasta **appesa senza stampare nulla** | `>/dev/null 2>&1` su una chiamata a `enter.sh`: era la prima della sessione, `sudo` chiedeva la parola d'ordine, e **la domanda finiva nel nulla**. ⛔ È il `2>/dev/null` del 9 agosto in una veste peggiore: un errore nascosto fa sbagliare diagnosi, **una domanda nascosta ferma la macchina** |
| **3** | ⛔ E non si vedeva **dove** si fermasse, perché avevo messo `\| tail` in coda al comando remoto | ⚠ **Identico al difetto n. 2 del 9 agosto**, commesso di nuovo dalla stessa mano il giorno dopo: `tail` non stampa niente finché il flusso non finisce. La cura non è ricordarsene — è **scrivere su un file e leggerlo** |
| **4** | Il banco ha dichiarato **MORTI due server che stavano ascoltando** | `setsid` **forca**: `$!` era il PID di `setsid`, che esce subito, non quello del server. ⭐ E `lsquic` lo smentiva **tre righe sotto**, con un *«in ascolto»* stampato nel suo stesso registro |
| **5** | E l'ha rifatto dopo la cura | `kill -0` da utente normale su un processo di **root** risponde *«operazione non permessa»* — cioè **un errore**, non *«non esiste»*. ⛔ **Vuoto e proibito con la stessa faccia**, `LEZIONI.md` §1.9 regola 1, su un controllo di sanità. Cura: `[ -d /proc/<pid> ]` |
| **6** | Il collegamento è caduto su `cannot find -lngtcp2`, e ⛔ **il banco ha dato la diagnosi opposta** — *«cmake ha saltato gli esempi in silenzio»* | Cmake li aveva configurati benissimo: mancava la libreria **condivisa** (`ENABLE_SHARED_LIB=OFF`), che è il bersaglio che gli esempi chiedono. ⚠ Un messaggio d'errore che indovina la causa **manda a cercare nel posto sbagliato**: ora il banco distingue «ninja è fallito» da «ninja è riuscito e il file non c'è» |

> #### ⛔⭐ E il settimo, che è il più grave del progetto finora: **la sonda dichiarava un denominatore falso**
>
> La quarta regola di `LEZIONI.md` §1.9 era **applicata**: la sonda stampava, a ogni gamba, che cosa
> avesse messo nel campo `server_name`. Diceva `'192.168.0.2'` — **e sul filo non andava niente.**
>
> Due righe di `aioquic`, in due file diversi: `asyncio/client.py:66` riempie il campo con l'ospite
> **anche se è un indirizzo IP**; `tls.py:1551` poi, scrivendo il ClientHello, **butta gli indirizzi
> IP**. La sonda leggeva la prima e credeva di descrivere la seconda.
>
> ⛔ **Conseguenza: la gamba «con SNI» mandava esattamente quel che mandava la gamba «senza SNI».**
> Le due gambe misuravano **la stessa cosa** mentre la sonda dichiarava che erano opposte — cioè il
> controllo che doveva distinguere «la libreria pretende l'SNI» da «il banco è rotto» **non
> distingueva niente**.
>
> ⚠ **E il verde di `ngtcp2` era già stampato quando me ne sono accorto.** Era vero — la misura
> rifatta lo conferma — ma era vero **per caso**: nessuna delle due gambe stava provando quel che
> diceva di provare.
>
> ⭐ **Che cosa l'ha fatto emergere**: non un sospetto, la riga stessa. `server_name spedito:
> '192.168.0.2'` in **tutt'e due** le gambe è un'impossibilità visibile — e l'ha resa visibile
> proprio la regola che stava sbagliando. Un denominatore falso si scopre solo se lo si stampa.
>
> ⛔ **La cura, in tre pezzi**: la sonda stampa il valore configurato **e** quel che finisce sul
> filo, con la riga di codice che li separa; la gamba di controllo usa un **nome** (`remotix.prova`)
> invece dell'indirizzo, perché è l'unico modo di far comparire l'estensione davvero; e ⭐ **il
> testimone finale non è nostro** — il registro di `lsquic`, che scrive *«SNI is not set»* guardando
> lo stesso filo dall'altro capo. È entrata in `LEZIONI.md` §1.9 come **corollario della quarta
> regola**: *un denominatore si legge dove la cosa succede*.

### ⚠ E su `quiche`, quattro intoppi e **una trappola vera** — 10 agosto 2026

*I primi tre sono cronaca di costruzione, e stanno qui perché costano tempo a chi li rifà. Il
quarto è un fatto per `DECISIONI.md` §6.4. **La trappola è il quinto**, e sarebbe stata il terzo
falso rosso attribuito a una libreria in due giorni.*

| | Che cosa è successo | |
|---|---|---|
| **1** | `cargo`/`rustc` **non erano nel contenitore** | ⚠ Il `[M]` del 9 agosto diceva che *Trixie li offre* (1.85.0) — ed era vero. **«Disponibile come pacchetto» e «installato» sono due cose diverse**, e la seconda ora sta in `provision.sh` |
| **2** | Gli esempi in C stanno in `quiche/examples`, non in `examples` | Il deposito ha una cassetta per ogni pezzo e una si chiama come il deposito. ⭐ **Il banco l'ha detto** invece di contare zero: era la quarta regola che funzionava |
| **3** | Il loro esempio non compilava: manca `uthash.h` | Nel `provision.sh`, come le altre. È una dipendenza del **banco** di `quiche`, non del prodotto |
| **4** | ⛔ `cargo` si è fermato: **`quiche` 0.29.3 pretende `rustc` 1.88**, Trixie ne ha **1.85** | ⭐ **Non è un intoppo, è un dato della decisione.** Il banco adesso sceglie da sé la versione più recente che il compilatore presente sa costruire — la **0.28.0** — e stampa quale e perché. ⚠ E nemmeno quella basta da sola: il loro `workspace` tira dentro `tonic`, `icu`, `image`; si costruisce `-p quiche`, il solo pacchetto che useremmo |

> #### ⛔ La trappola: il loro esempio **non controlla** di aver caricato il certificato
>
> `[R]` `quiche/examples/http3-server.c:564-565`: legge `./cert.crt` e `./cert.key` **dalla
> cartella corrente**, e ⛔ **ignora l'esito** di `quiche_config_load_cert_chain_from_pem_file`.
>
> ⚠ Con i due file assenti **il server parte lo stesso**, ascolta, e ogni stretta di mano
> fallisce — che alla sonda ha esattamente l'aspetto di *«`quiche` pretende l'SNI»*. Sarebbe stato
> il **terzo falso rosso attribuito a una libreria in due giorni**, dopo il `0 su 4` di `lsquic` e i
> due server dichiarati morti.
>
> ⭐ **La cura sta nel conduttore, non nella speranza**: mette i due file con i nomi che l'esempio
> pretende e **controlla che ci siano** prima di avviare. ⚠ E il controllo usa `case`, non
> `grep -q` in un tubo: con `pipefail`, `grep -q` esce al primo riscontro e il **riscontro riuscito**
> diventa un errore — il difetto del 9 agosto, che qui non si è ripetuto perché era scritto.

### ⛔ E la misura col browser: **quattro silenzi**, e un verde su zero misure

*Il server minimo ha funzionato al primo colpo col cliente di prova. La misura col **browser** — che
è il criterio vero di B2 — ha richiesto cinque giri, e nessuno dei difetti era del server.*

| | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | ⛔ **L'impronta del certificato arrivava tagliata della prima cifra** | Il banco la estraeva con `[A-Za-z0-9+/]{42}=`, e un SHA-256 in base64 è **43** cifre più il riempimento. ⚠ Il sintomo sarebbe stato *«i browser non aprono la sessione con `ngtcp2`»* — cioè **una candidata bocciata per una lettera**. Ora il banco **conta i caratteri** invece di fidarsi dell'espressione |
| **2** | Firefox non chiedeva nemmeno la pagina, e **non lo diceva** | La cartella del profilo non esisteva: con `--profile` su una cartella assente, Firefox si ferma sul suo gestore dei profili. ⛔ **Silenzio su tutt'e due i lati** — zero richieste al raccoglitore, registro del browser vuoto — per una cartella mancante |
| **3** | ⛔ E non c'era modo di saperlo, perché il raccoglitore **taceva le richieste** | `log_message` era `pass`, con scritto accanto *«il rumore delle richieste non serve: serve l'esito»*. È falso: la richiesta **è il denominatore dell'esito**. Senza, *«il browser non è partito»* e *«è partito e la prova è fallita»* sono lo stesso silenzio |
| **4** | E il primo tentativo di denominatore **contava sé stesso** | Cercavo `01-b2-sonda.html` nel registro del raccoglitore, e quel nome compare anche nel suo **banner d'avvio**: ha stampato *«richieste: 1»* quando erano **zero**. ⚠ Terzo falso denominatore in due giorni, e stavolta l'ho scritto io mentre curavo il secondo |

> #### ⛔ E il peggiore, che non è un difetto di diagnosi ma di giudizio: **OK su zero motori**
>
> Un giro ha stampato `OK — i motori provati hanno registrato il loro esito`, e i motori provati
> erano **zero**: il controllo di presenza guardava `xvfb-run -a`, cioè verificava che esistesse un
> programma chiamato `-a`, e saltava tutt'e due i browser dicendolo in una riga di avviso che
> l'esito finale contraddiceva.
>
> ⛔ *«Tutti quelli provati sono andati bene»* **è vero anche quando i provati sono zero**, ed è la
> forma di verde più vuota che ci sia — perché non ha nemmeno bisogno che qualcosa vada storto.
> ⭐ Ora il banco conta i motori provati, li stampa, e **si rifiuta di dare un esito se sono zero**.
>
> ⚠ *E vale la pena dire come si è visto: non da un sospetto, ma perché il numero dei motori è stato
> messo accanto al verdetto. È la quarta regola di `LEZIONI.md` §1.9 applicata al **verdetto**
> invece che alla misura — il denominatore di un'approvazione è quante cose ha approvato.*

### ⭐⛔ Le sei proprietà: due difetti veri, e nessuno dei due aveva un sintomo

*E il difetto peggiore era in una misura **nostra**, dichiarata verde poche ore prima.*

> #### ⛔ La misura che non misurava: il server che si dà ragione da solo
>
> Il 10 agosto il server minimo stampava all'avvio
> `REMOTIX B2: max_idle_timeout=30000ms max_datagram_frame_size=65536`, e quella riga è finita nei
> documenti come una misura di `RCP.md` §2.2. ⛔ **Ma è la sua configurazione, non il filo**: dice
> che cosa il server ha *chiesto* a ngtcp2, non che cosa è *arrivato* al pari.
>
> ⚠ È **esattamente** il corollario di `LEZIONI.md` §1.9 nato quella stessa mattina — *un
> denominatore si legge dove la cosa succede* — e l'ho violato io, quel pomeriggio, su una misura
> mia. La regola scritta contro `aioquic` non mi ha protetto dal commetterla contro me stesso.
>
> ⭐ La cura è `01-b2-sonda-trasporto.py`, che legge i parametri **dal pari**. E leggendoli da lì ha
> trovato subito due cose che nessuno aveva chiesto:

| | Che cosa si è visto | Perché nessun banco lo vedeva |
|---|---|---|
| ⛔ **il server offriva 0-RTT** | due biglietti di sessione con `max_early_data_size` = `0xffffffff`. `RCP.md` §2.3 lo **vieta**: i dati 0-RTT si possono ripetere, e il secondo messaggio di RCP è `CREDENZIALI` | ⭐ **Il documento l'aveva previsto**: *«il sintomo di 0-RTT acceso non esiste… le librerie QUIC lo offrono per impostazione predefinita»*. La sessione si apre uguale, i byte tornano uguali |
| ⛔ **concedeva 3 stream unidirezionali su 16** | `initial_max_streams_uni = 3` — quanti ne vuole HTTP/3 per il controllo e QPACK. §2.3 ne impone **almeno 16** «in ogni momento» | Il client di prova non ne apre nessuno. Il sintomo sarebbe comparso **nella fase 3**, come *«il desktop non risponde»* — e nessuno l'avrebbe collegato al credito |
| ⚠ **e la pagina non passava `allowPooling: false`** | §4.1-bis lo mette fra i vincoli, accanto al certificato di 14 giorni e alla chiave P-256 | Mettendolo a `true` la sessione si aprirebbe **uguale**: è un vincolo senza sintomo, e i due browser avevano già dato verde senza di lui |

⭐ **E il 0-RTT ha avuto il suo controllo positivo per caso, dal bersaglio stesso**: la sonda ha
*visto* un 0-RTT acceso prima di vederne uno spento. Il verde che è seguito è un verde dopo una
cura, non un verde da uno strumento cieco — che è la differenza fra i due che conta.

⚠ **E un colpo a vuoto, mio, che vale come regola**: curando la pagina ho sostituito una riga con
`str.replace` in Python su un appiglio con l'indentazione sbagliata. ⛔ **Python non protesta**:
restituisce la stringa intatta. La proprietà era nel codice ma non nell'esito registrato — cioè
affermata dal sorgente e non vista da nessuno. `01-b2-ngtcp2-wt-innesta.py` questo controllo ce
l'ha (l'appiglio dev'essere **uno**); le modifiche fatte a mano no, finché non l'ho aggiunto.

### ⭐⛔ B3: due difetti veri, e il primo è **esattamente** quello che B3 esiste per trovare

> #### ⛔ La stretta di mano funzionava **una volta sola**
>
> Al primo giro di B3 la **prima** connessione veniva rifiutata con
> `GIA_ATTIVA_REMOTA` — cioè il server diceva *«c'è già qualcuno»* a un client che era solo.
>
> La causa: `rcp_libera()`, che libera il posto nel registro delle sessioni, **non la chiamava
> nessuno**. Ogni connessione occupava un posto per sempre; dopo la prima riuscita, il server
> rispondeva `0x0F` a chiunque, per sempre.
>
> ⭐ **È la forma di `LEZIONI.md` §2.1 alla lettera**: *in v1 un certificato condiviso uccideva il
> server alla seconda connessione, e una prova a collegamento singolo resta verde per sempre*. Il
> banco che B3 impone — **due, mai una** — l'ha preso al primo giro. Una prova a connessione
> singola sarebbe stata verde e sarebbe rimasta verde fino alla fase 5.
>
> ⚠ E si noti dove **non** si sarebbe visto: la traccia della prima connessione è *conforme* a
> `RCP.md`. Il validatore non poteva dire niente — il difetto non è nei byte, è nello stato del
> server fra una connessione e l'altra.

> #### ⭐⛔ Il secondo: il banco accusava il server, e il colpevole era il buffer di Python
>
> Il terzo giro dava **rosso sul server**: la seconda connessione, che arriva mentre la prima è
> attaccata, veniva **accettata** invece che rifiutata con `0x0F`. Sembrava una violazione
> dell'invariante **I2** — *«la seconda connessione è rifiutata con messaggio esplicito»*.
>
> ⛔ **Non lo era. Il server aveva ragione dal primo istante.**
>
> La diagnosi, e sono state due righe di strumentazione — *chi prende il posto, chi lo lascia, e
> quanti ne restano occupati*:
>
> ```
> posto PRESO da prova via [..]:39390 (occupati adesso: 1)
> sessione aperta utente=prova via=[..]:39390
> posto LASCIATO da prova via [..]:39390 (occupati adesso: 0)   ← prima che la 2ª arrivi
> ```
>
> E i **timestamp** di ngtcp2 hanno chiuso il caso: la prima connessione si chiude a **t≈13,1 s**
> con `CONNECTION_CLOSE 0x0` — cioè ha retto i suoi dodici secondi — e la seconda arriva **dopo**.
> Le due non erano mai state contemporanee.
>
> ⭐ **La causa**: il banco aspettava la parola `SESSIONE` nel registro della prima connessione, e
> **Python bufferizza lo stdout quando è rediretto su un file**. Quella riga compariva solo
> all'uscita del processo — cioè **nell'istante esatto in cui il client si staccava**. Il controllo
> stampava `OK la prima è attaccata` leggendo una verità appena scaduta, e la seconda trovava
> sempre il posto libero.
>
> ⛔ **È la forma peggiore di difetto di banco**: non un rosso su un verde, ma **un rosso puntato
> sull'imputato sbagliato**. Il server rispettava §3.1 alla lettera — manda `CONGEDO(0x0F)` sul
> canale di controllo *e* chiude la sessione col codice `0x0f` — e il banco lo dichiarava in
> violazione di un'invariante.
>
> ⭐ **La cura, e la regola che ne esce**: il client scrive un **file** quando la sessione è aperta,
> e il banco aspetta quel file. *Un file scritto e chiuso è un fatto; una riga stampata è una
> speranza sul momento in cui qualcuno la vedrà.* (E `python3 -u`, che toglie l'altra metà della
> causa.)
>
> ⚠ E vale la pena dire **come non si è visto prima**: il controllo «la prima è attaccata» c'era, ed
> era proprio quello che doveva impedire questo errore. Era scritto giusto e misurava l'istante
> sbagliato.

### ⛔ E due difetti di banco degli ultimi due giri, uno dei quali ha dato un VERDE

| | Che cosa è successo | |
|---|---|---|
| **1** | ⛔ Il validatore ha dichiarato **«conforme»** una registrazione mentre il cliente di *quel* giro non si era nemmeno collegato | Stava giudicando il **file rimasto dal giro precedente**. ⚠ Un verde da un file stantio: la registrazione ora si **butta prima**, e se manca il banco dice *«non ho niente da giudicare»* — che non è «conforme» |
| **2** | Il cliente «non si collegava», e il colpevole ero io | `shift 3` con **meno di tre argomenti non sposta niente e non fallisce**: `$*` restava `accendi`, il server riceveva il nome dell'azione come opzione e moriva con *«port: invalid port number»*. ⛔ **Di nuovo il rosso sull'imputato sbagliato**, e stavolta a una manciata d'ore dalla lezione che l'aveva appena nominato |

> ⚠ **E una scelta di documento, dichiarata invece che nascosta**: `SPECIFICHE.md` §5.3 dice che un
> client silenzioso da trenta secondi «si considera staccato», e **non dice che cosa succede alla
> sua connessione**. Qui si è scelto di **lasciarla aperta** e liberare solo il posto: chiuderla
> sarebbe un congedo, e §8.2 non ha un motivo che voglia dire *«taci da un po'»*. È uno dei punti
> in cui `RCP.md` ammette due letture, ed è quel che questa sezione esiste per raccogliere.
>
> ⚠ **E un filo dell'ospite, non del protocollo**: per valutare l'orologio mentre il client tace, il
> server accende il **keep-alive di QUIC a 5 s** — è un battito del *trasporto*, che §2.2 non
> vieta, ma un server vero armerà un proprio timer e non metterà niente sul filo.

### ⛔ E tre trappole di shell in una sera, tutte la stessa

Il terzo giro di B3 si è impiccato **tre volte**, e ogni volta per lo stesso motivo in una veste
diversa: una **sottoshell in secondo piano**, una **sostituzione di comando**, e un
**`nohup ... &` con le virgolette annidate** — tutt'e tre attorno a `enter.sh`, e tutt'e tre si
portano via la richiesta di password di `sudo`. Lo script resta ad aspettare una domanda che
nessuno vede.

⭐ **La cura è la regola che il progetto aveva già**: le righe di comando si mettono in un file. Il
terzo giro adesso è `01-b3-terzo-giro.sh`, e gira **dentro** il contenitore, dove non c'è nessun
`sudo` e nessuna shell annidata.

⚠ **E un'ultima, a mio carico**: fermando i banchi ho scritto `pkill -f "01-b2-raccogli.py"`, e il
comando **ha ucciso la shell che lo eseguiva** — il modello compariva nella sua stessa riga di
comando. È la trappola del 9 agosto, scritta nel README di questo progetto, ripetuta il giorno dopo
da chi l'aveva appena documentata. Si ferma **per PID**.

⛔ **E la quarta veste, la sera dopo, su `01-b5-lancia.sh`**: `bash enter.sh --root "ninja …" > log
2>&1`. Nessuna sottoshell, nessun `&`, nessuna virgoletta annidata — **solo una redirezione**, e
`sudo` si è fermato lo stesso. Sei minuti a guardare un processo senza figli e un registro vuoto.
⭐ **La regola è più larga di come era stata scritta**: *non è `>/dev/null`, è **qualunque
redirezione attorno a `enter.sh`***. Dentro le virgolette invece è del comando remoto, e la
richiesta resta sul filo dove qualcuno la vede.

### ⭐⛔ B5: quarantaquattro violazioni, e **un difetto che nessun altro banco poteva vedere**

*Il banco è passato al primo giro su tutte le violazioni. Il rosso è arrivato da un **controllo**,
ed era stato **previsto per iscritto dentro il banco prima di misurare**.*

⛔ **Il contatore per indirizzo di §4.4-bis non ha mai bloccato nessuno.** La chiave era
`s->provenienza`, cioè `192.168.0.2:44661` — **con la porta**. E §4.4 ammette **un solo tentativo
per connessione**: la porta cambia ogni volta, quindi quel contatore valeva **sempre 1**.

⚠ **È la forma peggiore**: il codice c'era, si leggeva bene, sembrava giusto, e **non faceva
niente**. Nessun registro lo nominava; il sintomo — *«si può provare una parola d'ordine
all'infinito»* — non arriva mai da solo.

⭐ **E il controllo che l'ha trovato è preciso**: sette tentativi falliti con **sette nomi diversi**
dallo stesso indirizzo. Con lo stesso nome, il contatore **per nome** copriva il buco e il banco
sarebbe stato verde. Curato; ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — ⛔ **anche per
la parola d'ordine giusta**, che è il secondo controllo, quello che distingue un contatore da un
blocco.

⚠ **E un ordine che è una misura**: il giro completo buono si esegue **prima** del limitatore. Dopo,
l'indirizzo è bloccato per trenta secondi, e un banco che mettesse la stretta di mano in coda
leggerebbe quel rifiuto come *«il server è rotto»* — cioè darebbe rosso **proprio quando la regola
funziona**.

### ⭐⛔ B11: il difetto che serviva **un browser vero** per esistere

*E che B3 non poteva vedere, per cinque giri, con nessun cliente di prova.*

⛔ **Il posto nel registro delle sessioni si liberava solo alla morte della CONNESSIONE.**
`rcp_libera()` stava in `~ProtoCodec`. Con `aioquic` i due istanti coincidono — il cliente di prova
chiude tutto — e B3 è rimasto verde. ⭐ **Un browser no**: chiude la *sessione* e **tiene viva la
connessione**, e da quel momento il posto resta occupato da una sessione che non esiste più.
Con Chrome: **sette `posto NEGATO` su nove tentativi**, e alla pagina arrivava solo silenzio.

⚠ È **la stessa forma** del difetto che B3 aveva trovato il giorno prima — il posto che non si
libera — in un altro punto. ⛔ *Il difetto viveva nella differenza fra i due client, quindi nessuna
prova con un client solo poteva trovarlo.* È `LEZIONI.md` §2.1, la regola dei tre client, applicata
a una cosa che sembrava già provata.

⛔ **E il secondo, che riguarda §3.1 alla lettera.** `respingi()` manda `RESPINTO` sul canale di
controllo e chiude la sessione **nella riga dopo**: i due finivano nello stesso volo di pacchetti, e
il browser processa la capsula `CLOSE_WEBTRANSPORT_SESSION` **prima** dei byte dello stream, che a
quel punto butta. ⛔ **La pagina non ha mai visto `RESPINTO`: ha visto silenzio.**

⭐ **Ed è la dimostrazione che il punto 3 di §3.1 non è ridondanza**: il motivo è arrivato comunque,
dentro il codice d'errore della chiusura. *«Se il congedo non arriva — perché lo stream era rotto,
perché il messaggio era illeggibile — il motivo viaggia comunque»* è vero alla lettera, e questo è
il caso che lo prova. ⚠ Curato lo stesso da tutt'e due i lati: il server **rimanda** la capsula
finché la coda d'uscita non è vuota, e la pagina **legge `wt.closed`**.

⛔ **E il terzo, che è della PAGINA e lo ha reso visibile la differenza fra due motori.** La pagina
**chiudeva senza congedarsi**: chiamava `close()` e basta. Ma §8.1 dice che chi chiude *DEVE*
mandare `CONGEDO` con un motivo **prima** di chiudere — e vale anche per una chiusura volontaria
(`CHIUSO_DALL_UTENTE`). ⚠ Con Firefox non si vedeva: il trasporto chiudeva gli stream in tempo e il
posto si liberava lo stesso. ⛔ Con **Chrome** no, e otto casi su dodici ricevevano
`GIA_ATTIVA_REMOTA`. ⭐ *Non è una cura per Chrome: è §8.1 applicata, e la pagina non se ne era
accorta perché nessuno gliel'aveva chiesto.* Aggiunta: i falliti su Chrome sono passati **da 8 a 4**.

⛔ **E il quarto, che è stato l'ultimo a cadere.** Su Chrome, dopo il caso in cui è il **server** a
chiudere il canale di controllo con un `FIN`, il posto restava occupato: da lì in poi non arrivava
più un byte che potesse liberarlo, e la pagina non poteva rimediare. ⭐ **Il difetto viveva nella
differenza fra i due motori** — su Firefox il trasporto chiudeva lo stream in tempo e il posto se ne
andava lo stesso, quindi con un motore solo non esisteva. ⭐ **Curato la sera del 10 agosto: il
server libera il posto anche quando a chiudere è lui**, ed è quello che ha chiuso i tre casi rossi
di Chrome. Da lì Firefox 140 e Chrome 151 fanno **13 su 13** tutt'e due, `CONFORME` con zero
guasti, e il giro è stato **ripetuto**.

⚠ *Fino al rilievo **R11.4** del 10 agosto questo paragrafo diceva «quella riga non c'è ancora», e
la tabella delle misure «12 su 12 su Firefox, 9 su 12 su Chrome»: il commit che ha chiuso B11 ha
toccato `README.md`, `RCP.md`, cinque file di banco e `b2-esiti.jsonl`, e **non questo documento** —
che è quello che `PIANO.md` §0.1 fa leggere per primo alla ripresa. Chi riprendeva domani
riscopriva come aperto un difetto curato, e cercava una riga che c'è.*

⚠ **E la giustificazione che si dava a quel rosso è a sua volta `[?]`**: si diceva che la pagina non
poteva mandare il congedo perché *«§4.2 le vieta di spedire ancora»*. §4.2 vieta di continuare a
spedire **sugli altri canali**, e su uno stream bidirezionale il `FIN` del server non chiude il
verso della pagina — che quindi **potrebbe** mandare il `CONGEDO` che §8.1 le impone. Le due letture
danno byte diversi, il banco ha scelto il silenzio, e `RCP.md` **non dice quale sia giusta**:
rilievo aperto **R11.22**. ⛔ **La domanda sta in `DECISIONI.md` §7.14** — le due letture, i nove
byte di `CONGEDO` contro il silenzio, e il prezzo di ciascuna — e ci è arrivata la notte del 10
agosto 2026: era nominata qui, nel `README.md` e nel rapporto, e **in nessun posto dove si
decide**. ⚠ *E `RCP.md` §4.2 adesso lo dice di suo, invece di lasciar credere a chi implementa che
stia obbedendo mentre sta scegliendo.*

⛔ **E un difetto di banco che avrebbe accusato la pagina**: il confronto *«`desktop` non cambia
niente»* metteva a paragone **tutti** i byte usciti nei due giri — compreso il `CIAO`, che porta
`banco.guasto=…kde` contro `…gnome`, due stringhe di lunghezza diversa. Il denominatore conteneva
**il byte che il banco stesso aveva cambiato**, e avrebbe detto «DIVERSI» anche su una pagina
perfetta.

---

# Le decisioni prodotte

*Rimandi, non copie (`PIANO.md` §0.3 regola 1). ⚠ La prima stesura copiava tre passaggi da `RCP.md`
§4.1-bis e da `PIANO.md`, e uno aveva perso il rimando dell'originale (R4.12).*

| | |
|---|---|
| ⭐ `DECISIONI.md` §6.4 | 🔸 **CHIUSA il 10 agosto 2026, con un banco**: **`ngtcp2`+`nghttp3`**. `lsquic` fuori sull'SNI, `quiche` fuori perché **dal C non riesce a dichiarare WebTransport**, `ngtcp2` dentro perché **due browser veri aprono la sessione**. ⚠ Il prezzo — **373 righe di codice** `[M]` ore 16:30, di cui la riscrittura del SETTINGS di nghttp3 — è scritto accanto alla scelta |
| ✅ `DECISIONI.md` §1.8 | ⭐ **Apple è un di più, non un obiettivo** — 9 agosto 2026, dall'utente: S1a esce dalla fase, e la libreria si sceglie su due motori su tre |
| ⭐ ✅ `DECISIONI.md` §1.9 | **Il ban dell'indirizzo** — 10 agosto 2026, dall'utente: **tre autenticazioni fallite, dodici ore**, con un contatore solo e senza quello per nome utente. Riscrive `RCP.md` §4.4-bis — che da 🔸 diventa ✅ — `SPECIFICHE.md` §4.2, la regola **B0.3** e il banco **B8** per intero. ⛔ Nessun tipo nuovo sul filo: `TROPPI_TENTATIVI` c'era già |
| ⏳ `DECISIONI.md` §1.7 | resta aperta solo la comodità su Safari, e nessuno la misurerà per ora |
| ✅ `DECISIONI.md` §7.14 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: dopo un `FIN` sul canale di controllo **chi lo riceve tace** — cioè la lettura che **B11** aveva scelto da sé. ⚠ *Questa riga l'ha data **aperta** per mezza giornata dopo che era stata decisa (commit `ea35b5a`), e il documento di chiusura della fase **sottostimava quel che la fase aveva prodotto**: quattro decisioni contate come domande* |
| ✅ `DECISIONI.md` §7.15 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: il congedo di §8.1 vale **se il canale è ancora utilizzabile** — vince la condizione di §3.1 punto 2, e **B5 e B11 applicavano già quella** |
| ✅ `DECISIONI.md` §7.16 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: la funzione di banco resta 🔸 — ⭐ **e fuori dal prodotto consegnato** |
| ⛔ `DECISIONI.md` §5.0-quater | **S5 ha risposto, e la risposta smentisce la ragione scritta accanto alla decisione**: la tela resta lo schermo in pixel fisici, ⛔ **ma la formula con cui il client lo legge non regge su Chrome** — `screen.width × devicePixelRatio` dà `risoluzione × zoom`. `[M]` 10 agosto 2026. ⚠ La decisione **resta 🔸** e non è ripensata: cade la formula, non l'oggetto. La cura è di `SPECIFICHE.md` §6.1-bis e **non c'è ancora** |
| ⭐ `RCP.md` §7.3 | ⭐ **CHIUSA su Mutter l'11 agosto 2026**: S7 ha misurato il segno, e il server **inverte l'asse verticale**. ⛔ Resta `[?]` per gli altri quattro desktop, e *«non chiusa»* e *«non misurata»* sono due stati diversi |
| ✅ `DECISIONI.md` §7.17 | ⭐ **CHIUSA dall'utente l'11 agosto 2026: cinque secondi.** L'ha **prodotta una misura** — B6, chiudendo R3.27, ha trovato che una sessione che **non apre mai il canale di controllo** non aveva addosso nessun tetto — e l'ha chiusa l'utente dandogliene uno. ⭐ È il giro intero: una misura apre una domanda, la domanda va dove si decide, e la decisione torna nel protocollo |
| ⏳ `RCP.md` §5.3 | S6 dice se i 5 ms del PCM reggono |
| 🔸 `RCP.md` §7.5 | ⭐ **chiusa la notte del 9 agosto**: la funzione di banco — `BANCO_MARCA` e `BANCO_ESITO` — è entrata **prima del primo byte**, sotto la clausola di §9. ⚠ La usa la fase 3; qui se ne prova solo il **rifiuto a funzione spenta** (B5). ⚠ *Era marcata ✅, cioè «deciso dall'utente» (`README.md`), e non risulta presa dall'utente: §7.5 dichiara di venire dal **rilievo R3.4** e la motivazione da `web/rapporti/S4-ritardo-disegno.md` §5.3 — non c'è né frase né voce, come invece l'hanno §1.6 e §1.8. Corretta il 10 agosto 2026, rilievo **R11.15**, e **registrata dove le decisioni stanno**: `DECISIONI.md` §1.5 riga 26.* ⛔ **E la domanda «era sua?» è aperta, e sta in `DECISIONI.md` §7.16**: si chiude con una parola, e conta perché quei due tipi hanno consumato la clausola di §9 che `RCP.md` §12 dichiara essere stata *«l'ultima occasione»* |
| ⭐ `RCP.md` §4.6 | ⭐ **CHIUSA l'11 agosto 2026**: il cronometro parte dall'**apertura del canale di controllo**, e la riga 1 è cambiata di una parola (B6, R3.27). ⛔ Con la seconda risposta che apre `DECISIONI.md` §7.17 |
| ⭐ `SPECIFICHE.md` §11.5 | ⭐ **MISURATA l'11 agosto 2026, sera**, e da fuori: `curl -skI https://192.168.0.2:7448/` sul **prodotto** risponde **200, 31 840 byte**, con `Cross-Origin-Opener-Policy: same-origin` · `Cross-Origin-Embedder-Policy: require-corp` · `Cross-Origin-Resource-Policy: same-origin` · `Cache-Control: no-store`. ⇒ l'isolamento fra origini **c'è sulla pagina che il prodotto serve**, e non è più *«un vincolo da rispettare»* letto in un documento. ⚠ È `[M]` sulle **intestazioni**, non sul comportamento del browser sotto attacco |

---

# Che cosa resta `[?]`

| | |
|---|---|
| quanti **stream al secondo** regga ciascun browser | `RCP.md` §2.3 — banco della **fase 3** |
| **Safari su HTTP/2 e TCP** | l'unico motore che ci ripiega, e il nostro server non lo parla: ⏳ **va deciso** se implementarlo o dichiarare Safari fuori dal ripiego (`web.md` §3.2, O5) |
| ⭐ **S1a — l'eccezione su Safari e su iOS** | ✅ **resta `[?]` per decisione**, non per dimenticanza (`DECISIONI.md` §1.8). ⛔ E finché è `[?]`, *«funziona su iPhone»* **non si scrive nella documentazione del prodotto** |
| i **10 bit** fino allo schermo | tre indizi contrari, nessuno è una misura (`web.md` §1.2 A). Verifica alla **fase 2**, e la prova finale è **guardare una sfumatura** |
| il **pezzo cieco** di S4 | 16-40 ms fra il disegno e il pixel acceso, e nessuna API JavaScript lo vede: la stima **si dichiara accanto a ogni numero** |
| ⚠ **che a rifiutare l'impronta vecchia sia il CONFRONTO dell'impronta** | il terzo giro di B3 lo dava per dimostrato, e non lo è: l'esito registrato dichiara **tre cause con lo stesso aspetto** — UDP filtrato, impronta non del certificato servito, certificato oltre i 14 giorni — e nessuno le ha distinte. ⛔ Si chiude con un controllo che le separi, non con la frase *«il browser confronta davvero»* (R11.3) |
| ⭐ **~~e la seconda metà del criterio di B2 sul terzo giro~~ — CHIUSA** | il giro è stato **rifatto la sera del 10 agosto**, su decisione dell'utente, e adesso passa pieno: la sonda manda un `CIAO` conforme e accetta `ECCOMI`, invece dell'eco di B2 che il server non fa più. ⭐ E registra **sempre** un esito, anche quando il server tace: prima restava appesa, e «il browser non è partito», «la sessione non si è aperta» e «il server non ha risposto» avevano lo stesso aspetto (R11.3) |
| ⚠ **il segno della rotella su più di un compositore** | R3.25 — ⭐ **misurato su Mutter** il 10 agosto 2026 (`+120` ⇒ il server inverte), ⛔ **e §7.3 vincola cinque desktop**: se a normalizzare è `libei` il numero vale ovunque, se normalizza il compositore KWin darà un segno diverso. Il banco è rieseguibile su KWin senza cambiare una riga |
| ~~**l'istante da cui parte il primo tetto**~~ — **CHIUSA** | R3.27, chiusa da **B6** l'11 agosto 2026: si parte dall'apertura del **canale di controllo**. ⛔ E la seconda risposta di B6 ha aperto `DECISIONI.md` §7.17 — **la sessione senza canale non ha nessun tetto** |
| ⭐ ~~**la pila PAM per un utente diverso dal proprietario del processo**~~ — **CHIUSA** | R3.26, chiusa da **B10** l'11 agosto 2026 **con una misura**, sul servizio **`remotix`**: la pila PAM verifica la parola di un utente **diverso dal proprietario del processo** ⛔ **solo se il processo è privilegiato** — da `root` riesce, da un utente normale no. Il server oggi è di root. ⚠ **Resta la domanda della fase 2**: un servizio di sistema che **lascia i privilegi** vedrebbe quella causa, e il sintomo sarebbe *«credenziali errate»* |
| ⛔ **il secondo fisso di §4.4-bis, e l'imputato adesso ha un nome** | ⭐ **Rimisurato la sera dell'11 agosto 2026** dal giro di certificazione di B8: mediane **2123,2 · 2198,1 · 1085,9 ms** — ⛔ *e quindi i «1984 ms» del `README` e i «2636 ms» qui sotto sono **due fotografie di giri diversi**, non un numero corretto due volte*. ⭐ **Quel che è cambiato non è il numero, è che l'imputato è misurato**: il server attende **+1034 ms** oltre il secondo fisso sui respinti e **+84 ms** sugli ammessi — la firma di `pam_faildelay`, cioè **PAM e non il nostro codice**. ⚠ E la `[?]` resta aperta lo stesso, perché finché quel ritardo non è costante il secondo fisso **non nasconde quel che dichiara di nascondere** |
| ⛔ **il secondo fisso di §4.4-bis contro il servizio `remotix`** | i **2636 ms** di B8 sono la mediana **di `login`**. Il prodotto ha il suo servizio PAM, quindi *«a governare i tempi è PAM»* va rimisurato prima di credergli, e il `[?]` sul secondo fisso **non lo chiude quella misura** |
| ⛔ **la formula della tela, dopo S5** | `screen.width × devicePixelRatio` non è invariante allo zoom su Chrome 151, e lo zoom di pagina **non è leggibile da JavaScript in modo portabile**. Non è una `[?]` da misurare: è una **cura da trovare**, in `SPECIFICHE.md` §6.1-bis |
| ⛔ **S5 su DeX, e S2, S3a, S6** | quattro misure che aspettano un **dispositivo**, non un'idea: il telefono Android, il DeX, una rete LTE vera. ⭐ I banchi sono pronti e girano il giorno che il ferro c'è (`web/rapporti/S-esiti-sonda.md` §4-§6) |
| ⏳ **il numero di S1b** | l'orologio è in moto dal 10 agosto 21:10 UTC: il verdetto è il **17-18 agosto 2026**. Fino ad allora S1b dice *«a N giorni l'eccezione c'è ancora»*, e il `[R]` dei sette giorni **non è confermato dal comportamento** — solo dalla contabilità di Chrome |
| ⛔⛔ ~~**il congedo di §8.1 su FIREFOX**~~ — **NON È PIÙ UNA `[?]`: È UN DIFETTO DI PRODOTTO, CON UN NOME** | ⭐ **Attribuito la sera stessa** (`banchi/01-p5-ff-*`, due giri per motore): **è della PAGINA**, e su **tutt'e due i motori**. `src/pagina.html:620` azzera `congeda_corrente` un millisecondo dopo `SESSIONE`, e il gestore di `pagehide` (riga 331) è **codice morto**. ⇒ Chiudendo la scheda, il client **non manda nessun congedo** dove §8.1 lo impone senza condizioni, e il posto se ne va per il tetto dei 30 s. ⛔ **Gecko è scagionato per misura**: la stessa `congeda()` chiamata da dentro `pagehide` consegna **tutt'e due** le strade di §3.1. ⛔ E su Chrome quel che sembrava un congedo era **lo smontaggio col codice `0x0`, che §3.1 vieta** — il banco lo contava senza leggere il motivo. ⭐ **La cura è di tre righe ed è scritta**, nel riquadro di P5: non applicata, perché la fase era già chiusa |
| ⛔ **il prodotto contro i banchi** | nessun banco ha mai acceso `src/`. Finché non lo fa, *«il server fa X»* è vero **dell'innesto**, e di `src/` è **letto** |
| `[?]` **il rinnovo del credito degli stream unidirezionali** | dichiarato dal prodotto stesso; si misura alla **fase 4**, col carico che lo provoca |
| ⚠ **perché `lsquic` con l'SNI cada su ALPN** | `[M]` 10 agosto: avviso TLS **120**, `no suitable application protocol`, **dopo** che il certificato è stato trovato. ⛔ **Non indagato di proposito**: `lsquic` è fuori per un motivo che non dipende da questo, e la riga esiste perché nessuno lo riscopra credendolo nuovo |
| ⚠ **la previsione sulla bozza 02 di `lsquic`** | ⛔ **ancora aperta dopo due misure**: nemmeno con l'SNI si arriva alle impostazioni HTTP/3. Non è stata né confermata né smentita |

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

**E quelle dell'11 agosto 2026**, uscite dalla revisione avversariale della notte
(`fasi/rapporti/R12-A/B/C/D`) e dalle misure della sonda. ⛔ *Ogni riga dice **dove** la cura è
andata: quando si cura una riga si cercano tutti gli altri posti che dicevano la stessa cosa, ed è
la forma di difetto che questo progetto paga più spesso.*

| | |
|---|---|
| `RCP.md` §0-bis · §9 · §7.5 · §8.2 · `DECISIONI.md` §1.5 | ⛔ **cinque punti dicevano «oggi non esiste nessuna implementazione»**, al presente, mentre ne esistono tre: la finestra di §9 era dichiarata **aperta** dall'arbitro. Chiusa in tutti e cinque, con la data del primo byte (R12C.2) — ⭐ **e §9 adesso conta QUATTRO tipi entrati sotto la clausola, non due** (R12C.3) |
| `RCP.md` §7.3 | il segno della rotella: da `[?]` a **misurato**, con la scena, la data, i quattro controlli e quel che di ciascuno è nel registro (R12C.7) |
| `RCP.md` §4.6 | la riga 1 cambia di una parola, ⛔ **e la tabella guadagna la riga dello stato che non aveva** (R12C.11) |
| `RCP.md` §4.4-bis | il comando di sblocco **non è di RCP e non sta sul filo**: dichiarato, con la forma che non funziona e perché (R12C.4, R12.1) |
| `SPECIFICHE.md` §6.1-bis | *«va misurato quanto e su quali motori»* → **è misurato**, e la formula non regge su Chrome (R12C.8) |
| `SPECIFICHE.md` §5.5 | ⛔ prometteva dieci sessioni insieme mentre la fase 1 gira su **un filo solo con PAM sincrona**: il ripiego era dichiarato **solo in un commento di `src/main.c`** (R12C.17) |
| `DECISIONI.md` §5.0-quater | la `[?]` su cui poggiava è misurata, e va **nell'altro verso** — `LEZIONI.md` §2.3-quater preso in flagrante (R12C.8) |
| `DECISIONI.md` §7.17 | ❓ **nuova**, aperta da una misura di B6 e non da una lettura |
| `web.md` §7 · §8 | le etichette della sonda, e S1b che non è più *«da avviare»* |

---

# ⛔ Un verdetto che la regola dell'utente ha cambiato: **R9.10**

*Scritto qui la notte del 10 agosto 2026, e non nel rapporto: ⛔ **`fasi/rapporti/R9-prodotto-rcp.md`
porta la sua data e non si riscrive**. Chi lo legge domani deve poter sapere, da qualche parte, che
una sua metà è decaduta e l'altra è peggiorata — e da quando.*

Il rilievo diceva due cose sul limitatore di `banchi/rcp/rcp.c` (*«il blocco per indirizzo non
scade mai, e raddoppia fra prove separate da settimane»*).

| | |
|---|---|
| ⭐ **la prima metà è DECADUTA** | il blocco che raddoppiava — 30 s, poi 60, poi 120, fino a 15 minuti, e `blocco_corrente` che nessuna strada riportava a zero — **descriveva la forma 🔸 che non esiste più**. `DECISIONI.md` §1.9, la sera dello stesso giorno, l'ha sostituita per intero: niente finestra che raddoppia, niente contatore per nome utente, **un ban di dodici ore con una scadenza scritta su file**. ⛔ La cura non è più *«far scadere il contatore»*, è che il ban abbia **una scadenza e un comando di sblocco** (`RCP.md` §4.4-bis) |
| ⛔ **la seconda metà è PEGGIORATA** | *«due giri identici, due verdetti diversi, e la causa non è nel banco»*: l'indirizzo del banco resta bloccato dal giro prima, e nel secondo ogni caso che passa da `fino_ad_ammesso()` riceve `TROPPI_TENTATIVI` invece di `AMMESSO`. ⛔ **Adesso quel blocco dura 12 ore invece di 15 minuti, e sta su file**: sopravvive anche al riavvio del server, quindi «si aspetta» e «si riavvia» non sono più cure. E non tocca solo B5: **B7 fallisce un tentativo, B8 ne fallisce tre**, e da lì in poi B10, B11 e chi sta sviluppando sono fuori da quella macchina per mezza giornata |

⛔ **La cura è la regola B0.3 di questo documento**, e va letta prima di lanciare qualunque banco: il
**comando di sblocco** fra un banco e l'altro — ⛔ **mai dentro il giro di B8**, o B8 non prova più
niente — e **ogni banco che lo chiama lo dichiara**, o *«il ban non è scattato»* e *«qualcuno l'ha
tolto»* hanno lo stesso aspetto.

⚠ E la parte del rilievo che **non** cambia: era, ed è, il **difetto noto n. 6** del mandato del 10
agosto — *«B11 ha dato verdetti diversi fra giri identici»* — con l'imputato fuori dal banco.

---

# Il giudizio dell'utente

*La frase vera, con la data. La fase si chiude qui, non quando questo documento è pieno.*

> ## ✅ **«Va bene, la stretta di mano funziona: fase 1 approvata.»**
>
> — l'utente, **11 agosto 2026**, dopo aver aperto `https://192.168.0.2:7448` **dal portatile**, in
> **Chrome**, digitato `prova` e la parola d'ordine, e aver letto sulla pagina *«Ammesso, sessione
> nuova, tela 1920×1080, desktop sconosciuto»*.

⭐ **La misura che chiude la fase ha una provenienza su disco**, e non è un ricordo:
[`rapporti/GIUDIZIO-11-agosto.md`](rapporti/GIUDIZIO-11-agosto.md) — la scena, le impronte, il
registro del server verbatim (`GET /` alle **12:45:44 UTC**, la stretta di mano alle
**12:48:55-12:48:56 UTC**) e quel che la pagina ha mostrato.

⛔ **E quel giro ha chiuso da solo le due cose che il `README.md` di quella mattina dichiarava non
misurate**: che **la pagina l'abbia servita il prodotto** (`GET /` era a **zero**) e che un giro
**abbia attraversato la rete** (le 19 connessioni del 10 agosto venivano **dal server stesso**). Su
**Chrome**, di cui contro questo server non c'era nessuna traccia.

⚠ **Che cosa il giudizio NON è**: un banco. Non ha un atteso confrontato da una macchina (**B0.4**),
non ha un controllo che dica *no*, non è rieseguibile senza una persona, e ⛔ **la versione esatta di
Chrome non è annotata** (regola **B0.6** mancata). È **I8**, e vale per quello che è — che è
esattamente ciò che `PIANO.md` §0.2 regola 3 chiede per chiudere una fase: *una misura giudicata
dall'utente, non un documento completo*.

⛔ **E la fase si chiude con del lavoro dichiarato aperto**, che è la forma onesta: le certificazioni
mancanti e i `[?]` qui sopra non si cancellano perché il giudizio è arrivato — si portano in fase 2
scritti, o la prossima fase comincia credendo a misure che nessuno ha fatto certificare.
