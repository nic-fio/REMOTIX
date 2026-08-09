# SPECIFICHE — che cosa è REMOTIX_V2, e che cosa promette

*Riscritta il 9 agosto 2026, incorporando le 44 decisioni prese l'8 e il 9 agosto.*

> **Come si legge questo documento.** Qui c'è **che cosa** il prodotto fa. Il **perché** di ogni
> scelta, con la data e chi l'ha presa, sta in [`DECISIONI.md`](DECISIONI.md), e ogni paragrafo
> rimanda alla voce corrispondente. Il **come si misura** sta in [`LEZIONI.md`](LEZIONI.md); le
> regole di chi scrive e di chi revisiona in [`CODER.md`](CODER.md) e [`REVIEWER.md`](REVIEWER.md).
>
> Le marche sono quelle di `CODER.md` §5: `[M]` misurato da noi, `[R]` letto nel codice,
> `[S]` letto in una specifica, `[?]` ipotizzato e non ancora verificato. **Una riga senza marca
> è una decisione di prodotto, non un fatto tecnico.**

---

## 1. Che cos'è

REMOTIX_V2 è un sistema di **desktop remoto per Linux**, composto da un server e da **una pagina
web**, che parlano un protocollo nostro chiamato **RCP** — *Remotix Control Protocol*.

| | |
|---|---|
| **server** | esclusivamente Linux |
| **client** | ⭐ **nessuno da installare: un browser moderno**. Il server serve la pagina, la pagina parla RCP su **WebTransport** |
| **Windows come server** | ⛔ **fuori**, ed è la leva di §1.1 |
| **Windows come posto da cui ci si collega** | ✅ **dentro, e gratis**: un browser su Windows non è codice nostro. Vale per macOS, iPhone, iPad, Chromebook e qualunque altra cosa abbia un browser |

⭐ **Niente client dedicati** *(deciso il 9 agosto 2026, `DECISIONI.md` §1.6)*. Sparisce il client
Android — con esso cinque fasi di piano — e sparisce il client Linux. Restano **un server e una
pagina**.

⚠ **E il protocollo non è cambiato di una riga.** WebTransport porta a un browser esattamente i
mattoni su cui RCP era stato disegnato: stream QUIC indipendenti, l'abbandono di un fotogramma,
i datagram per l'audio. Se il filo fosse stato progettato su TCP, questa decisione sarebbe costata
il protocollo intero.

È l'evoluzione di REMOTIX v1, che si è fermato alla fase 11 dopo aver servito GNOME e KDE
parlando RDP. Il patrimonio di v1 — 17.481 righe di C, 4.563 righe di banchi, cinque studi dei
desktop e il registro delle lezioni — sta sotto `v1/` ed è la base su cui V2 poggia
(`DECISIONI.md` §6).

### 1.1 Perché RDP muore, in una riga

I tre muri contro cui v1 si è fermato — il tetto a H.264, il client Android che decodificava in
software, il colore pieno irraggiungibile — **erano tutti e tre di RDP, non del problema**. La
riga «niente Windows» è la leva che li toglie insieme. Il prezzo, accettato: il protocollo va
progettato oltre che scritto, e i client vanno scritti da zero. (`DECISIONI.md` §1.1)

⭐ **E metà di quel prezzo è stato restituito il 9 agosto 2026**: i client da scrivere non sono più
due, è **una pagina sola** (§1). Resta intero il primo pezzo — il protocollo va progettato — ed è
il motivo per cui `RCP.md` esiste prima del codice.

---

## 2. I principi guida

1. **Rilevare le capacità, non la distribuzione.** All'avvio si verifica cosa c'è, si sceglie il
   percorso migliore e si **dichiara** cosa manca.
2. **Degradare, non fallire.** Ogni dipendenza mancante ha un ripiego. Il servizio funziona
   comunque, con meno — ma il ripiego si dichiara nel registro: uno silenzioso produce due
   comportamenti sotto la stessa etichetta.
3. **Dipendere, non riscrivere.** Ogni componente che scriviamo è un componente da mantenere per
   sempre.
4. ⭐ **Si dipende dal compositore, non dal suo contorno.** Il compositore si insegue per forza:
   solo lui consegna i fotogrammi e accetta l'input. Blocca-schermo, demoni di inattività,
   gestori dell'energia e display manager fanno la stessa cosa in quattro modi diversi, con
   quattro configurazioni che si riscrivono da sole: quelli **non** si inseguono.
   (`DECISIONI.md` §0.1 — è il principio che ha prodotto diverse delle scelte che seguono)
5. **Parlare direttamente al compositore**, mai attraverso portali che chiedano autorizzazione a
   video: un servizio non presidiato non ha nessuno che clicchi.

---

## 3. I tre numeri

Sono i numeri che l'utente pone e a cui la tecnica si adegua, non il contrario. Ogni scelta
tecnica si giustifica mostrando che avvicina uno di questi. (`CODER.md` §1 e §1-bis)

⭐ **E tutti e tre misurano il pezzo che è nostro** *(`DECISIONI.md` §2.7, 9 agosto 2026)*: REMOTIX
promette quel che **produce e consegna sulla linea**. Che cosa il dispositivo dall'altra parte
riesca a decodificare e dipingere **si misura e si dichiara, non si promette** — non è codice
nostro. ⚠ Con un confine: un client che non tiene il minimo va **detto**, con la ragione. Un
ripiego silenzioso resta vietato anche quando la colpa non è nostra.

### 3.1 Qualità dell'immagine

| | |
|---|---|
| **MINIMO** | 480p · 25 fps · 24 bit |
| **DESIDERATO** | 4K · 60 fps · **10 bit per canale** |

⭐ **Il minimo è una garanzia, non un traguardo.** Non è un'asticella da inseguire — v1 la
superava già `[M]` — ma **il livello sotto cui non si scende e non si stacca**, per quanto brutta
sia la linea. Nasce dal caso della rete mobile (§8), non da una rinuncia sulla qualità.
(`DECISIONI.md` §2.1)

**Il desiderato è a 10 bit, non a «32 bit».** Trentadue bit non sono una grandezza esistente: sono
24 di colore più 8 di trasparenza, e la trasparenza non si trasmette. Dietro l'intenzione
«massima qualità» stavano due leve distinte, e ne è stata scelta una:

| Leva | Cura | Prezzo |
|---|---|---|
| **10 bit per canale** ✅ | le strisce sulle sfumature | quasi nulla, e in hardware ovunque — decoder Android compreso |
| 4:4:4 `[?]` | il testo colorato sfrangiato `[M]` v1 | ~50 % di banda, e **nessun decoder Android in hardware** |

Il 4:4:4 resta una `[?]` da misurare, non una promessa: sarebbe un'opzione per il solo client
Linux su GPU capaci, e nessuno ha ancora misurato quanto si veda la differenza.
(`DECISIONI.md` §2.2-2.3)

### 3.2 Il ritardo

| | Dall'input che arriva al fotogramma che parte |
|---|---|
| **TETTO** | 50 ms |
| **TRAGUARDO** | 40 ms |

⛔ **Si misura solo il pezzo che è nostro.** La rete non è nostra e cambia da un minuto all'altro:
un requisito «100 ms end-to-end» si fallirebbe stando fermi, per colpa di una galleria — e un
requisito che si può fallire senza aver sbagliato niente **non viene misurato da nessuno**. Il
totale che l'utente sente è questo più la rete: si **dichiara**, non si promette.

⚠ **Il ritardo pesa più dei fotogrammi**: 30 al secondo con 40 ms si usano benissimo, 60 con
200 ms sono insopportabili. Una scelta che alza il ritmo peggiorando il ritardo non si fa — ed è
uno scambio che si presenta di continuo, perché **ogni memoria intermedia compra fluidità e vende
risposta**. (`DECISIONI.md` §2.4)

`[?]` Il traguardo dei 40 ms probabilmente **non è raggiungibile su GNOME**, per lo stesso muro
dei 60 fotogrammi: Mutter ne consegna 37 al secondo. Stima, non misura. (`DECISIONI.md` §2.5)

⭐ **Ma «nessuna leva nostra lo sposta» non si può più scrivere** *(9 agosto 2026)*: `gnome.md`
§8.2 dà la causa del muro `[R]` — un solo numero che fa da freno alla cattura **e** da frequenza
al monitor virtuale — e con essa un candidato di cura che costa zero righe di prodotto. Va
provato prima di dare il muro per acquisito (`LEZIONI.md` §3, il riquadro dei sei decimi).

---

## 4. Il protocollo RCP

```
librcp.so
rcp_frame_t · rcp_connect() · rcp_session_t
stretta di mano:  RCP/1
```

Il nome dice *Control*, non *Display*: il protocollo non porta solo pixel — porta input, appunti,
geometria, congedo e stato della sessione, e il video è **uno** dei suoi canali.

| | |
|---|---|
| **trasporto** | **WebTransport su HTTP/3**, cioè QUIC con TLS 1.3 obbligatorio — **porta 7447** di serie, configurabile |
| **codec video** | HEVC, con AV1 dove l'hardware lo codifica |
| **audio** | Opus, con PCM come base sempre disponibile |
| **canali** | video · audio · input · cursore · appunti · controllo |

⚠ **Il server ascolta su due porte con lo stesso numero**: **TCP** per consegnare la pagina, **UDP**
per HTTP/3 e WebTransport. ⭐ *Corretto il 9 agosto 2026 dalla misura S1*: le due cose sono
**indipendenti** — WebTransport non passa da `Alt-Svc`, apre la sua connessione da sé — e questo
toglie di mezzo il ripiego silenzioso su TCP che avevo dichiarato come pericolo.

⚠ **Il protocollo non è un dettaglio implementativo: è l'arbitro.** In v1 l'oracolo era `mstsc` —
se disegnava, era giusto. In V2 client e server sono nostri, e **due programmi scritti dalla
stessa mano che vanno d'accordo non confermano niente**: ripetono lo stesso presupposto. Da cui
tre obblighi: `RCP.md` si scrive **prima** del codice e abbastanza preciso da poter dare torto a
qualcuno; client e server si collaudano **contro la specifica**, non l'uno contro l'altro; e dove
si può, serve un validatore che legga il filo.

### 4.1 La fiducia — due livelli, e non di più

*Posti dall'utente il 9 agosto 2026: «Abbiamo 2 livelli per la sicurezza: il trasporto e l'accesso».*

| Livello | Che cos'è | Come si risolve |
|---|---|---|
| **il trasporto** | che nessuno legga o riscriva quel che passa | **TLS**, sempre e senza alternative. Il certificato **se lo fa il server**, e la pagina passa al browser la sua impronta |
| **l'accesso** | chi è ammesso a quella macchina | **indirizzo, porta, utente e password**. Niente altro — §4.2 |

⛔ **Non c'è un terzo livello, ed è una decisione**: niente autorità da installare, niente impronte
da confrontare a mano, niente servizio nostro in mezzo. Le strade che aggiungevano un livello sono
state guardate e **scartate**, con le ragioni in `DECISIONI.md` §1.7.

**Che cosa vede l'utente**: apre `https://indirizzo:7447`, **clicca l'avviso la prima volta su
quel dispositivo**, digita utente e password. ⭐ Tutto il resto — rigenerare il certificato prima
che scada, pubblicarne l'impronta nella pagina — sta **dentro il server** e non si vede.

⚠ **Il clic resta, ed è il prezzo dichiarato di non avere un dominio.** Chi ne ha uno mette un
**certificato vero** — una riga di configurazione, non una strada diversa — e l'avviso non compare
mai, iPhone compreso.

**La password non parte prima** che il server abbia dimostrato di essere quello di ieri —
l'invariante I3 applicata all'ordine della stretta di mano.

⚠ La prima connessione **su ogni dispositivo** resta scoperta a un uomo-in-mezzo. **Rischio
valutato e accettato** per lo scenario previsto: server proprio, rete propria o VPN. ⛔ E con il
client web la **conseguenza** di quel rischio è più grossa — chi si mette in mezzo non intercetta
la pagina, **la riscrive**. (`DECISIONI.md` §1.3 e §1.7)

⏳ **Rinviato per decisione dell'utente**: la messa in sicurezza vera — MFA e quel che la tecnologia
offre — è **un'evoluzione da fare a progetto completato**, non un pezzo di questo. Sta in evidenza
in `DECISIONI.md` §1.7, con le tre voci da rileggere quel giorno.

### 4.2 L'autenticazione

**PAM locale**, servizio `remotix`, con limitazione della frequenza dei tentativi.

✅ **La forma della limitazione è decisa** *(9 agosto 2026, `RCP.md` §4.4-bis e `DECISIONI.md`
§1.5)*: cinque tentativi falliti in cinque minuti, poi un'attesa che parte da 30 secondi e
raddoppia fino a un tetto di 15 minuti, con due contatori — uno per nome utente e uno per
indirizzo — e l'azzeramento su un accesso riuscito.

⭐ **E un secondo fisso di ritardo su ogni risposta, anche quando è «ammesso».** Non serve a
rallentare chi indovina: serve a togliere il **tempismo** come canale. Senza, «utente inesistente»
risponde in un millisecondo e «password sbagliata» in cinquanta — e la distinzione che il
protocollo vieta di scrivere nel motivo la si legge col cronometro.

---

## 5. La sessione

### 5.1 Una sola sessione grafica per utente

Un utente può avere **innumerevoli** sessioni testuali (ssh, tty) contemporaneamente, ma **una
sola** grafica — locale o remota. Testuali e grafiche convivono.

| Situazione | Esito |
|---|---|
| ha una sessione grafica **locale** attiva e apre una remota | ⛔ la remota è **rifiutata**, con messaggio esplicito |
| ha una sessione grafica **remota** attiva e ne apre una locale | ⛔ **la locale vince**: la remota viene chiusa |
| ⭐ ha una remota **attiva e viva** e si collega da un **secondo dispositivo** | ⛔ **la seconda connessione è rifiutata** *(deciso il 9 agosto 2026)* — è l'invariante I2, e il motivo è `GIA_ATTIVA_REMOTA` |
| ha una remota il cui client **tace da 30 secondi** | quel client è **staccato** (§5.3): non tiene il posto, e il nuovo dispositivo **entra** |

⚠ **Le ultime due righe non si contraddicono, e il discrimine è l'orologio del silenzio**: un client
vivo occupa, un client muto no. ⛔ Il prezzo, dichiarato: se il portatile si spegne di colpo senza
congedarsi, dal telefono si entra **dopo trenta secondi**, non subito.

### 5.2 La sessione sopravvive al client

Il palco — cattura, controllo e schermo virtuale — **appartiene alla sessione, non alla
connessione**. Si chiude il client e la sessione resta viva; ci si ricollega, anche da un altro
dispositivo, e si ritrova tutto. È l'invariante I4, ed è il difetto che in v1 rendeva la sessione
inutilizzabile dopo il primo distacco. (`DECISIONI.md` §4.1)

### 5.3 I tre orologi

| Orologio | Quanto | Che cosa scatta |
|---|---|---|
| **silenzio del client** | 30 secondi | il client si considera **staccato**, e il codificatore si libera |
| **inattività dell'utente** | 30 minuti senza input | REMOTIX **stacca** il client: per rientrare servono utente e password |
| **abbandono della sessione** | 6 ore senza alcun attacco | la sessione si chiude, **con congedo pulito** |

Sono in scala: secondi, minuti, ore. Il secondo e il terzo sono **configurabili**, con quei
valori come predefiniti.

⭐ **Un client che tace è un client che si è staccato**, e nessuna connessione «tiene il posto».
Chi arriva entra, senza timeout da aspettare: sparisce il caso «il telefono è morto in galleria e
ora non posso rientrare nella mia sessione». (`DECISIONI.md` §4.4)

⚠ Con QUIC il passaggio WiFi → LTE **non** conta come silenzio: la connessione si porta dietro il
cambio di indirizzo. I 30 secondi coprono solo le interruzioni vere.

⚠ «Input» è quel che l'utente manda, non quel che guarda: chi resta mezz'ora a guardare un video
senza toccare nulla viene staccato. Il costo è piccolo — riattaccarsi è rapido.

### 5.4 Il blocco è di REMOTIX, non del desktop

⛔ **Il blocca-schermo dei desktop resta spento**, com'era in v1. Non è una svista ereditata: è
una dipendenza, e ha una ragione misurata. Bloccando davvero, su GNOME Mutter **revoca** cattura
e input `[R]`; su KDE si apre la catena che spegne lo schermo e monta un output fittizio **con un
filtro che inghiotte tutto l'input** `[R]`; su XFCE e LXQt le cure sarebbero righe di
configurazione, e su LXQt il demone ne riscrive una da sé.

La sicurezza è la stessa: l'unica strada per quel desktop passa da RCP, e RCP passa da PAM.
(`DECISIONI.md` §4.3)

⏳ **Con una scadenza dichiarata**: quel ragionamento regge **finché la password è l'unica
chiave**. Chi un giorno aggiungesse un'autenticazione più forte deve rileggere questa scelta,
perché allora il blocco del desktop tornerebbe a difendere qualcosa.

### 5.5 Multi-tenant

Più utenti possono avere ciascuno la propria sessione grafica remota, indipendenti.

**Tetto predefinito: 10 sessioni**, configurabile. ⛔ Ma il limite vero non è un conteggio: è un
**budget** di pixel al secondo, e lo pone il codificatore. Con lo stesso ferro le stesse dieci
sessioni sono facilissime o impossibili secondo la qualità che ciascuna chiede.

Sul ferro di riferimento — i5-13500T, 31 GB, Intel UHD 730 `[M]` — la sola integrata regge
`[?]` una cinquantina di sessioni al minimo, **8-10 a 1080p30**, **una sola a 4K60**.

**Quando il budget è pieno si rifiuta, dichiarando il motivo.** Non si fa degradare chi sta già
lavorando per far entrare chi arriva: sarebbe una discesa non nata da una misura della linea,
cioè ciò che I1 vieta. (`DECISIONI.md` §4.6)

---

## 6. La geometria: la tela e la vista

Sono due cose distinte, ed è la separazione che tiene in piedi sia il riaggancio da dispositivi
diversi sia il futuro multi-monitor.

| | Di chi è | Quanto cambia |
|---|---|---|
| **la tela** — la misura del desktop, quella che le finestre vedono | della **sessione** | si fissa a ogni attacco, e non si muove finché il client resta |
| **la vista** — che cosa di quella tela vede questo client, e quanto grande | della **connessione** | liberamente |

### 6.1 Il modello

| Momento | Chi decide la misura |
|---|---|
| **attacco** | il client: la sessione legge la sua risoluzione e usa quella. È 1:1 |
| **durante la sessione** | nessuno: se l'utente ridimensiona la finestra, **il client riscala l'immagine** |
| **riattacco** da un altro dispositivo | il nuovo client, con la sua risoluzione |

⭐ Il caso mobile viene giusto da solo: il telefono si attacca e la tela nasce della forma del
telefono — pixel veri, niente bande, niente scalatura.

**Ridimensionare la finestra del client non tocca mai il desktop**, su nessuno dei quattro
compositori. Le ragioni, in ordine di peso: su KDE 6.3.6 — cioè Debian stabile — **non si può**
`[M]`; la correzione a monte esiste ma Debian non aggiorna Plasma; e ⛔ **anche dove funziona fa
una cosa peggiore**, perché ridimensionare un output **ridispone le finestre dell'utente** `[R]`.
La versione «giusta» scompiglia il lavoro, quella «rotta» lo lascia fermo. (`DECISIONI.md` §5.1)

### 6.2 Le proporzioni

**Si impagina, non si stira.** Se la finestra ha proporzioni diverse dalla tela si conservano le
proporzioni e si mettono le bande: allungare deforma il testo e lo rende illeggibile.

Il caso è raro per costruzione — all'attacco le proporzioni **combaciano sempre** — e resta solo
durante il ridimensionamento e nel ripiego di §6.3. Sul telefono in verticale la banda sarebbe
enorme: lì serve lo zoom con scorrimento, che è nel ventaglio dei gesti (§7.2).

### 6.3 Il ripiego su KDE, dichiarato

Al riattacco a misura diversa su KWin < 6.8 la tela **non può** cambiare. Si tiene quella vecchia
e riscala il client — e non costa una riga in più, perché è lo stesso codice del punto
«durante la sessione». **Il ripiego si dichiara nel registro.**

### 6.4 «Adatta il desktop a questa finestra»

Il ridimensionamento vero della tela resta come **scelta esplicita dell'utente**, mai come
automatismo. Dove il compositore non lo sa fare la voce è **spenta, con la ragione dichiarata**.
Quando si scriverà, si scriverà nella forma della **negoziazione PipeWire** — una strada sola per
GNOME, wlroots e KDE ≥ 6.8, che su KDE si accende da sé all'aggiornamento.

### 6.5 Multi-monitor

**Fuori scope come funzione**, ma l'implementazione resta parametrica su N: una tela più grande di
quel che un singolo schermo mostra **è già** la forma del multi-monitor — due viste sulla stessa
tela invece di una.

---

## 7. L'input

### 7.1 Il puntatore lo disegna il client

Il dito trascina un puntatore **disegnato dal client**. Non è il tocco diretto, dove il dito è il
puntatore: è il trackpad, e si vede dove si sta per cliccare **prima** di cliccare.

Tre problemi chiusi insieme: ⭐ **la latenza percepita** — il puntatore si muove alla velocità del
dito, non della rete; **le scie e le posizioni vecchie**, che nascono dal puntatore che viaggia
dentro il video; e **la precisione**, perché un dito è largo ~10 mm e i bersagli ~4.

⛔ **Da cui un obbligo**: il cursore del desktop **non deve mai finire nell'immagine catturata**,
altrimenti se ne vedono due. Su GNOME è già escluso; su KDE e wlroots ci finisce `[M]`, e la cura
è un tema con un cursore 1×1 a trasparenza piena.

⚠ **E va verificata, non sperata**: su wlroots un tema che carica **zero** cursori fa ripiegare la
libreria su uno **incorporato e visibile** `[R]`. L'esito si controlla dopo l'avvio della
sessione. (`DECISIONI.md` §5-bis.1-2)

**Nella pagina**: il puntatore è disegnato sopra il video, quello del browser si nasconde
(`cursor: none`), e il mouse fisico arriva da **Pointer Lock** — che è l'equivalente esatto del
*Pointer Capture* di Android e ha lo stesso motivo: senza, se ne vedrebbero **due**.

### 7.2 I gesti — per il telefono in mano

⚠ **Su Android l'uso primario è Samsung DeX**, con mouse e tastiera veri: là vale §7.4, e questi
gesti non si usano. Servono al telefono in mano, che è il ripiego d'emergenza.

| Gesto | Effetto |
|---|---|
| 1 dito trascina | muove il puntatore |
| 1 dito tap | clic sinistro |
| 2 dita tap | clic destro |
| 2 dita trascina | rotella / scorrimento |
| tap-e-mezzo | trascinamento e selezione |
| 3 dita tap | clic centrale |
| pizzico | ingrandisce la **vista** del client |

⭐ **È un punto di partenza dichiarato, non un impegno.** I gesti si giudicano usandoli, non
leggendoli: chi trova questa tabella diversa fra sei mesi non ha trovato un difetto.

### 7.3 La tastiera

**Le lettere viaggiano come lettere; i tasti che lettere non sono viaggiano come posizioni.**

| Che cosa | Come |
|---|---|
| lettere, numeri, segni | **come lettere** |
| Invio, Tab, Esc, frecce, F1-F12, Ctrl, Alt, Maiusc, Super | **come posizioni** — stanno nello stesso posto su ogni tastiera |

Il motivo: una tastiera fisica non manda lettere, manda **posizioni**, ed è il desktop a decidere
che lettera sia. Se sul filo viaggiassero le posizioni, un client con tastiera americana attaccato
a una sessione italiana produrrebbe **le lettere sbagliate**. E su Android una tastiera non ha
posizioni affatto: è un metodo di inserimento che produce testo.

⛔ **Con una precisazione**: `Ctrl+C` non è testo, è un comando. Una battuta viaggia come lettera
quando **scrive del testo**; quando è premuto un modificatore di comando — Ctrl, Alt, Super —
viaggia come posizione. Maiusc e AltGr non contano: servono a *fare* la lettera.

**La disposizione della sessione si rinegozia a ogni attacco e riattacco**, come la risoluzione —
e serve a due cose: rendere *raggiungibili* i caratteri, e far combaciare le posizioni delle
scorciatoie (su una tastiera tedesca la Z sta dove da noi sta la Y).

⚠ **Quel che non è scrivibile viene dichiarato, non falsificato.** Se un carattere non esiste su
nessun tasto della disposizione — un'emoji, un alfabeto diverso — non esce **niente**, e il server
lo scrive nel registro: mai una lettera diversa, mai un silenzio. (`DECISIONI.md` §5-bis.6-7)

### 7.3-bis Le scorciatoie che il browser si tiene — molto meno di quanto sembrava

> ⛔ **Riscritta la sera del 9 agosto 2026 dalla misura S3** (`web.md` §5). Questa sezione diceva
> che la Keyboard Lock esiste *«solo su Chrome ed Edge»* e che `F11` e `Ctrl+Shift+I` sono perduti.
> **Era sbagliata su tre punti**, e in meglio.

| | |
|---|---|
| **la leva** | ⭐ **non è più solo di Chrome**: `keyboardLock` è entrato nello standard WHATWG l'**8 maggio 2026** e l'hanno spedito Safari 26.4 e Firefox 151 `[S]`. Chrome ed Edge restano sulla forma vecchia — ⚠ **la pagina deve saperle entrambe** |
| **quanto si perde** | `[R]` la lista riservata di Chrome è di **dodici** comandi; **a schermo intero scende a due** — `F11` e l'uscita — **senza chiamare nessuna API**. Firefox ne ha **sei**, Safari **zero** |
| ⭐ **e in una PWA installata è vuota** | tutte le scorciatoie arrivano alla sessione. ⛔ **Ma una PWA vuole un certificato fidato**: dietro l'eccezione di §4.1 il Service Worker non si installa `[R]`. **Chi ha un dominio non compra solo l'assenza dell'avviso: compra la tastiera intera** (`web.md` §1.2 B) |

**Quel che si perde davvero, e non si recupera:**

| | |
|---|---|
| `Ctrl+Alt+Canc` · l'uscita da schermo intero | ovunque, per costruzione |
| ⛔ **su macOS, tutte le scorciatoie di sistema** | non esiste un aggancio: la funzione che dovrebbe fornirlo **restituisce `nullptr`** `[R]` |
| ⛔ **su Android e DeX, ogni combinazione con Meta** | per regola AOSP — ⚠ e DeX è l'uso primario (`DECISIONI.md` §5-bis.0) |

⛔ **Che cosa si fa**: la pagina **dichiara** quali scorciatoie non può consegnare su quel browser.
NON si finge che funzionino, e non si inventa una scorciatoia sostitutiva senza dirlo.

`[?]` **Restano due domande, e sono le due che pesano di più**: se la Keyboard Lock funzioni su
**DeX**, e se la PWA valga anche su **Chrome per Android**.

### 7.4 Mouse e tastiera fisici — su Android è la strada principale

Il mouse passa da *Pointer Capture*: il cursore di Android sparisce — altrimenti se ne vedrebbero
due — e i suoi spostamenti muovono **lo stesso puntatore che muove il dito**. Una freccia sola,
due modi di spingerla. L'accelerazione la applica il **client**: applicata da entrambi si
sommerebbe.

### 7.5 Che cosa porta il canale di input

| | |
|---|---|
| puntatore **assoluto** | sì — è l'unico percorso del puntatore |
| **posizioni** di tasto | sì |
| **lettere** | sì, ed è la strada principale |
| tocco multi-dito | **posto riservato**, non implementato `[?]` |
| stilo (pressione, inclinazione) | fuori |

---

## 8. La rete e la degradazione

### 8.1 Gli scenari da servire

Il requisito è **l'adattamento**, non una soglia di banda:

| Collegamento | Banda | Ritardo e perdita | Che cosa fa il server |
|---|---|---|---|
| fisso buono | 30+ Mbps | bassi | punta al desiderato |
| fisso modesto, WiFi | 5–15 Mbps | medi | **spende tutto quel che c'è** |
| **mobile critico** | sotto i 2 Mbps, variabile | alti, con perdita | tiene il minimo, **e non stacca** |

### 8.2 La regola dell'adattamento — invariante I1

> **Il ritmo non cala mai per prudenza, per risparmio o perché la scena è ferma. Cala solo quando
> la misura dimostra che la linea non porta, e ogni discesa è dichiarata nel registro.**

Vietata l'euristica prudente, obbligatorio l'adattamento misurato. Il risparmio di banda **non è
un obiettivo di questo prodotto**: la banda non spesa non torna utile a nessuno, e la qualità
persa si vede.

### 8.3 Sotto il minimo

**Si calano i fotogrammi. Mai sgranare l'immagine, mai staccare.**

Su un desktop degradare nel tempo è meglio che degradare nello spazio: a pochi fotogrammi al
secondo ognuno resta nitido e il testo si legge — è lento ma ci si lavora. Sgranando, il testo
diventa illeggibile. E a ritmo basso si possono spendere più bit su ciascun fotogramma.

⭐ È l'utente a decidere quando chiudere il client; la sessione resta e si riprende quando la
linea migliora.

### 8.4 QUIC

Oltre alla cifratura, due cose che il trasporto regala e che vanno sfruttate: la **misura
continua** di quanto porta la linea, che in v1 andava ricavata a mano; e la **migrazione della
connessione**, che tiene viva la sessione quando il telefono passa da WiFi a rete mobile.

---

## 9. Gli appunti

**Solo testo, nei due versi.** Si copia sul desktop remoto e si incolla sul dispositivo in mano, e
viceversa — ed è il secondo verso quello che si usa di più.

Niente immagini, niente file, niente formati ricchi: il testo copre quasi tutti gli usi, costa
pochi byte e non ha negoziazione, mentre le immagini aprono la questione dei formati e soprattutto
di **chi paga la banda** quando si copia una schermata da 8 MB su un collegamento che stiamo
faticando a tenere al minimo. (`DECISIONI.md` §5-ter)

**Dalla parte del browser gli appunti non sono nostri**, il che tocca proprio il verso più usato —
ma meno di quanto si temeva *(misura S3, 9 agosto 2026, `web.md` §5.3)*:

| | |
|---|---|
| ⭐ **si può sorvegliare, su Chrome** | l'evento `clipboardchange` è arrivato con **Chrome 144**, il 13 gennaio 2026 — e la motivazione scritta nella proposta sono **i client di desktop remoto** `[S]`. Porta i soli tipi MIME, e vuole il fuoco |
| ⛔ **su Firefox e Safari no** | verificato, non dedotto. Là ogni lettura costa il menu «Incolla», con un secondo di attesa |

⚠ E una trappola che **tutti e tre** i riferimenti letti disinnescano a mano: la corsa fra `Ctrl+V`
e la lettura degli appunti. Xpra la risolve ritardando **ogni battuta di 100 ms** `[R]` — ⛔ per noi
sono **due volte il tetto del ritardo**: quella cura non si copia, si sostituisce.

La regola resta quella di sempre: **si dichiara quel che non si può fare**, non si fa finta.

⚠ **Su tutti e tre gli stack gli appunti appartengono al compositore**, e ci sono anche senza di
noi. Su GNOME la sessione remota non li possiede: possiede solo **la porta** per raggiungerli
(`EnableClipboard`). *Corretto il 9 agosto 2026 da `gnome.md` §10 `[R]`; questa riga diceva il
contrario, ed è la stessa correzione di `DECISIONI.md` §5-ter.3 e `LEZIONI.md` §3 domanda 14.*

---

## 10. L'audio

| | |
|---|---|
| **uscita** | **Opus**, con **PCM** come base sempre disponibile |
| **microfono** | dal client alla sessione — **non urgente**, e può slittare |
| sorgente e destinazione | **PipeWire** |

⚠ Invariante I5: **il volume appartiene alla sessione.** Chi si collega trova il livello al
massimo; un cursore lasciato in basso non sopravvive alla riconnessione.

⚠ E una trappola misurata da v1: un nodo audio applica il volume **a valle della presa del
monitor**, quindi chi cattura il monitor riceve il segnale a fondo scala qualunque cosa dica il
cursore, **muto compreso**. La proprietà che sposta la presa esiste ma è spenta di suo.

---

## 11. I desktop e il sistema

### 11.1 Wayland, e le applicazioni X11

**Solo sessioni Wayland.** Le applicazioni scritte per X11 restano supportate **via XWayland**.
I desktop X11 come tipo di sessione sono fuori scope.

### 11.2 I desktop supportati, in ordine

| | Stato |
|---|---|
| **GNOME** | servito in v1 `[M]` |
| **KDE Plasma** | servito in v1 `[M]` |
| **XFCE** (labwc) | studiato, non ancora servito |
| **LXQt** (labwc) | studiato, non ancora servito |
| **Cinnamon** | 📖 **studiato il 9 agosto, ultimo della fila** — vedi [`cinnamon.md`](cinnamon.md) |

⛔ **Su Cinnamon tre cose non esistono a monte**: `RecordVirtual`, libei, e **gli appunti** — né la
via di GNOME né quella di wlroots. La fattibilità dipende da una misura sola, e la decisione
«dentro o fuori» si prende su quella, non sullo studio. (`DECISIONI.md` §7.13)

### 11.3 Il sistema attorno

| | |
|---|---|
| **init** | systemd |
| **distribuzioni** | rilevamento delle capacità e degradazione dichiarata; **Debian e Ubuntu** come riferimento |
| **spegnimento, riavvio, sospensione** | **tolti** alla sessione remota |
| **GPU** | scelta per **id PCI** con una regola udev. ⚠ Negare il nodo lo nega a **tutta la sessione dell'utente**: chi usa l'altra scheda per altro va messo nel gruppo della regola |

### 11.4 L'accelerazione hardware

**L'astrazione è `libavcodec`**, non le API dei costruttori: si sceglie il codificatore **per
nome, a runtime**, in base a cosa si trova. Un solo percorso di codice, nessuna riga specifica per
costruttore. La scala di preferenza:

1. `hevc_vaapi` · `hevc_qsv` · `hevc_nvenc` — la strada normale
2. `av1_*` dove c'è — Intel Arc/Xe2, AMD RDNA3+, NVIDIA Ada+
3. ripiego software: **SVT-AV1** (BSD-3) — ⛔ **mai x265**, che è GPL-only e incatenerebbe tutto
   il server

⚠ Sul ferro di riferimento **nessuna delle due schede codifica AV1** `[M]` 9 agosto: il desiderato
a 10 bit passa da **HEVC Main10**, che tutt'e due codificano in hardware.

⛔ **E la parentesi «RDNA2 e Alder Lake lo decodificano soltanto» era sbagliata a metà**, corretta
lo stesso giorno con `vainfo` sui due nodi: la Radeon RX 6800 decodifica AV1 (`AV1Profile0`,
`VLD`), **l'Intel UHD 730 non espone alcun profilo AV1 — nemmeno in decodifica**. Il dettaglio
delle capacità delle due schede sta in `DECISIONI.md` §4.6.

`[?]` Vulkan Video resta una delle opzioni fra cui `libavcodec` può scegliere. Non è la prima
perché non porta il controllo del bitrate — che è precisamente la parte che decide se i Mbps
risultino guardabili.

### 11.5 I browser serviti, e perché vanno dichiarati

⭐ **La regola dei tre client non decade con il client unico: cambia forma** (`LEZIONI.md` §2.1).
Una pagina gira su **tre motori scritti da tre squadre che non ci conoscono** — Blink (Chrome,
Edge, Samsung Internet), WebKit (Safari), Gecko (Firefox) — e questo ci restituisce un pezzo
dell'arbitro esterno perso con `mstsc`: quando due sono d'accordo e il terzo no, il difetto si
dichiara da solo.

| | |
|---|---|
| **il minimo tecnico** | WebTransport **e** WebCodecs. `[S]` Entrambi presenti su Chrome/Edge, Firefox e Safari 26+ — WebTransport è Baseline da marzo 2026 |
| **si collauda su** | ⛔ **almeno due motori diversi**, sempre. Un solo motore è un client solo, cioè il caso che questa regola vieta |
| **si dichiara** | quali browser sono serviti, e **che cosa si perde su ciascuno** — le scorciatoie (§7.3-bis), gli appunti (§9), il certificato su Safari (`DECISIONI.md` §1.7) |

⚠ **E le versioni contano più che sui desktop**: qui il pavimento non lo pone Debian, lo pone il
dispositivo dell'utente. Un telefono fermo a una versione vecchia di Chrome non ha WebCodecs, e
il sintomo va detto in una frase — non «non funziona».

---

## 12. Fuori scope

Il paragrafo che protegge il progetto dallo scivolamento. Ciascuna riga è **esclusa
deliberatamente**, non dimenticata.

| Che cosa | Perché |
|---|---|
| **Windows come server** | è la leva di §1.1. ⚠ *Corretta il 9 agosto 2026*: questa riga diceva «come server **e come client**», e la seconda metà è decaduta con §1.6 — non scriviamo un client per Windows, ma **chi ha Windows si collega dal suo browser**, e non ci costa niente |
| **applicazioni da installare**, su qualunque sistema | §1: il client è la pagina. Un'applicazione nativa sarebbe un secondo prodotto da mantenere per sempre, per guadagnare quel che il browser già dà |
| **desktop X11** come tipo di sessione | le applicazioni X11 restano, via XWayland |
| **redirezione di dischi, stampanti, porte seriali, smart card** | non serve al mestiere di questo prodotto |
| **trasferimento file** | idem — e la clipboard testuale copre il caso frequente |
| **immagini e file negli appunti** | §9 |
| **multi-monitor** come funzione | §6.5: predisposizione sì, funzione no |
| **stilo** con pressione e inclinazione | §7.5 |
| **tocco nativo multi-dito** | posto riservato nel protocollo, non implementato |
| **registrazione della sessione** su file | mai chiesto |
| **compatibilità con client RDP, VNC o SPICE** | è il contrario di §1.1 |

---

## 13. Le questioni aperte

Quel che **non** è deciso, elencato perché non si perda. Il dettaglio e lo stato stanno in
`DECISIONI.md` §7.

| | |
|---|---|
| ⏳ **la licenza** | rinviata a fine progetto. Fino ad allora vale il solo vincolo di §11.4: niente x265 |
| 📖 **Cinnamon** | studiato, da misurare — §11.2 |
| `[?]` **il 4:4:4** | §3.1 |
| ✅ ~~la forma della limitazione dei tentativi PAM~~ | **chiusa il 9 agosto**, §4.2 |
| `[?]` **il tocco nativo multi-dito** | §7.5 |
| `[?]` **il puntatore relativo** per le applicazioni che catturano il puntatore | segnalato dal server, non dal client |
| `[?]` **l'eccezione del certificato copre WebTransport?** | §4.1 — è la misura che decide se il predefinito «un clic» funziona ovunque o solo su Chrome e Firefox |
| `[?]` **quanto si perde delle scorciatoie**, motore per motore | §7.3-bis |
| `[?]` **gli appunti nel verso dispositivo → sessione** senza gesto dell'utente | §9 |
| `[?]` **HEVC Main10 in hardware nel browser del telefono** | `[S]` documentato da Chrome 108; da misurare sul dispositivo vero — e con §3 non è più un muro, è una cosa da dichiarare |
| ⏳ **la sicurezza forte (MFA)** | rinviata a progetto completato, per decisione dell'utente — `DECISIONI.md` §1.7 |
| `[?]` **codificare più piccolo quando la finestra è piccola** | oggi il server codifica la **tela** e il client riscala. Ridurre anche la misura codificata è `DECISIONI.md` §5.0-ter, volutamente fuori dal modello finché nessuno ha misurato quanto pesa |

---

## 14. Il modo di lavorare

Lo sviluppo è portato avanti da due tipi di agenti, con le regole scritte nei loro documenti:

| | |
|---|---|
| [`CODER.md`](CODER.md) | che cosa costruire e come — con i tre numeri, gli invarianti e le regole di misura |
| [`REVIEWER.md`](REVIEWER.md) | come si cercano le **contraddizioni**. Il verdetto è sempre «questo contraddice X», mai «questo è giusto» |
| [`LEZIONI.md`](LEZIONI.md) | il fondamento condiviso: come si misura, come si prova, come si impara. **Si legge prima di tutto** |
| [`DECISIONI.md`](DECISIONI.md) | che cosa è stato deciso, quando, da chi, e con che grado di certezza |

⛔ **E la regola che tiene insieme tutto**: quando una misura contraddice questo documento, lo si
aggiorna **nello stesso momento**, con la data e la marca della fonte. Un riferimento che
invecchia in silenzio è peggio di nessun riferimento.
