# SPECIFICHE — che cosa è REMOTIX, e che cosa promette

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

REMOTIX è un sistema di **desktop remoto per Linux**, composto da un server e da **una pagina
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
desktop e il registro delle lezioni — sta sotto `fondamenta/` ed è la base su cui V2 poggia
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
6. ⭐ ⛔ **Sullo schermo dell'utente c'è il suo desktop e nient'altro.** *«Come se fosse davanti al
   monitor del PC»* — nessun artefatto, nessuna marca, nessun riquadro di servizio. ⛔ E non nella
   forma *«spento per predefinito»*: quel che serve a noi per misurare **non entra nel binario che
   si installa** (`DECISIONI.md` §7.16, dall'utente l'11 agosto 2026; la pulizia si fa e **si
   misura** alla fase 13). ⚠ *Aggiunto quando la prima funzione di banco ha chiesto il permesso di
   dipingere: il principio non c'era, e la risposta è stata più larga della domanda.*

---

## 3. I tre numeri

Sono i numeri che l'utente pone e a cui la tecnica si adegua, non il contrario. Ogni scelta
tecnica si giustifica mostrando che avvicina uno di questi. (`CODER.md` §1 e §1-bis)

⚠ **Obiettivi di progetto, non promesse misurate** *(decisione dell'utente, 30 set 2026)*: le prove di
prestazione sono state tolte (troppo dipendenti dall'hardware) e le misure con loro; le soglie di questo
capitolo — e le altre del documento — restano come **direzione** delle scelte tecniche, non come garanzia.
I parametri che il prodotto usa davvero (banda minima, tetto delle sessioni, orologi, ban) sono
configurazione e valgono come scritti.

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
| 4:4:4 `[?]` | il testo colorato sfrangiato `[M]` v1 | molta più banda, e **nessun decoder Android in hardware** |

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

### 3.2-bis ⭐⭐ LA SPECIFICA DELL'ESPERIENZA — dettata dall'utente il 22 agosto 2026

> *«Non pretendo un comportamento allineato al nanosecondo rispetto a una situazione locale, ma che
> gli si avvicini molto. La mia specifica è avere un'esperienza utente il più vicina possibile a una
> situazione locale, ma non identica: quello è impossibile.»*

⭐ **È il metro della fase 8**, e differisce dai tre numeri di §3 in una cosa sola ma decisiva: §3.2
promette **il pezzo che è nostro** (input → fotogramma che parte), questa dice **che cosa deve
sentire l'utente**. Le due non si sostituiscono: la prima è collaudabile da un banco, la seconda è
il giudizio a cui la prima serve.

#### ⭐ La scena su cui è stata dettata, e il numero che l'utente ha prodotto con l'occhio

22 agosto 2026, dal video dell'utente: una finestra di terminale trascinata a mano dentro la
sessione.

⭐ **E l'utente ha misurato a occhio la cosa che conta**: la distanza fra la freccia del mouse e la
finestra che la insegue è **«la metà della larghezza della barra del titolo»**. ⇒ Le velocità della
mano e i conti su quella scena stanno in `fasi/08-l-anello.md`.

#### ⛔ Perché è un ELASTICO, e perché l'utente lo chiama «fluidità» invece che «ritardo»

`[R]` Nel modo classico la freccia la muove **il browser**, alla velocità della mano (§7.1 e
`pagina.html`: il cursore di sistema *e* la freccia disegnata, sovrapposti, tutt'e due locali). La
finestra invece la insegue con **tutto** il ritardo dell'anello. ⇒

```
distacco = velocità della mano × ritardo dell'anello
```

⛔ **Il distacco non è costante: cresce quando si accelera e si richiude quando si rallenta.** In
locale è **zero a qualunque velocità**. ⇒ La finestra *nuota* rispetto alla mano, e questo si
percepisce come **mancanza di fluidità**, non come lentezza — che è esattamente la parola che
l'utente ha usato per primo, prima che ne conoscessimo la causa.

⭐⭐ **E il conto va nei due versi**: nota il distacco in pixel, si ricava il ritardo — ma il
risultato cambia molto secondo la velocità della mano. ⏳ `[?]` **A quale velocità l'utente stia
guardando non è deducibile**: va misurato l'anello, non chiesto a lui.

#### ⛔ E il limite si dichiara, perché la specifica dice «non identica»

Un anello di rete **non può avere distacco zero**: c'è un fotogramma del compositore, uno della
pagina, e il filo in mezzo. ⇒ Il distacco **si dimezza o meglio, non si toglie**. Chi promettesse
di farlo sparire prometterebbe una cosa che non esiste — ed è precisamente la parte che l'utente ha
messo nella specifica da sé: *«ma non identica: quello è impossibile»*.

⏳ **Il traguardo in numeri non si scrive qui finché l'anello non è rimisurato** sulla scena vera. Va
scritto **nell'unità dell'utente** — frazioni di barra del titolo a una velocità dichiarata — perché
è quella che lui può giudicare senza strumenti.

#### ⭐ E lo scambio che questa specifica vieta era GIÀ vietato qui sopra

§3.2 lo dice dal principio: *«ogni memoria intermedia compra fluidità e vende risposta»*, e *«una
scelta che alza il ritmo peggiorando il ritardo non si fa»*. ⇒ ⛔ **Mettere l'anello in parallelo**
— codificare l'N mentre si cattura l'N+1 — comprerebbe fotogrammi al secondo pagandoli in ritardo:
**peggiorerebbe l'elastico**, cioè proprio la cosa che l'utente vede. È **fuori**, e non per una
misura nuova: per una riga che stava scritta da prima che il difetto avesse un nome.

### ⚠ Le misure del ritardo sono storiche

*13 agosto 2026, fase 3 step 5*: il ritardo cattura → vetro è stato misurato sul ferro di allora,
con la codifica del prodotto di allora. ⇒ I numeri, il loro spezzettamento tratto per tratto e la
discussione sul compositore stanno in `STUDI.md` §gnome §8.2 e §13 e in `DECISIONI.md` §2.5: valgono
per quella macchina e per quel prodotto, **non sono garanzie** *(decisione dell'utente del 30
settembre 2026)*.

⛔ **Resta la regola di metodo**: il ritardo si misura fino al **disegno finito**, non al richiamo del
decodificatore — tagliare prima vuol dire regalarsi un pezzo del tetto (`CODER.md` §1-bis). ⚠ E il
pezzo cieco dello schermo dell'utente non esiste su Xvfb (`STUDI.md` §web §8).

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
| **codec video** | **H.264** e **HEVC**, **solo sulla scheda** — si negozia col browser (`DECISIONI.md` §1.13); ⛔ niente codifica sul processore (§11.4, `DECISIONI.md` §10.27) |
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

**PAM locale**, servizio `remotix`, con il **ban dell'indirizzo** dopo tre tentativi falliti.

⭐ ✅ **Tre autenticazioni fallite dallo stesso indirizzo entro 5 minuti, e quell'indirizzo è fuori
per 12 ore** *(deciso dall'utente il 10 agosto 2026 — `DECISIONI.md` §1.9, `RCP.md` §4.4-bis)*. Il
**nome utente non conta**: tre nomi diversi contano tre. Un accesso riuscito azzera il conto.

| | |
|---|---|
| **che cosa conta** | ⛔ **solo** l'autenticazione fallita — utente inesistente e parola sbagliata sono la stessa cosa, come §4.1 impone. Non gli errori di protocollo, non i tempi scaduti, **e non il rifiuto della seconda connessione** (§5.1), che è quel che riceve il secondo dispositivo dello stesso utente |
| **che cosa vede chi è bannato** | la pagina **si carica lo stesso** e dice che i tentativi sono esauriti. ⛔ Mai un silenzio: chi è bannato per errore è quasi sempre il proprietario |
| **come si esce** | ⭐ **le 12 ore che passano, oppure un comando di sblocco sul server** — che chiede l'accesso alla macchina, cioè l'unica chiave che quel caso ammette. Il ban **sopravvive al riavvio** |

⚠ **Il prezzo, dichiarato**: dietro un NAT gli indirizzi si condividono, quindi tre errori di una
persona chiudono la porta a tutti gli altri per dodici ore — ed è il caso per cui la forma
precedente aveva un secondo contatore, **tolto sapendolo**. E il primo a inciamparci è chi digita
una parola lunga sulla tastiera di un telefono.

> ⛔ *Riscritta il 10 agosto 2026. Questa sezione diceva: «cinque tentativi falliti in cinque minuti,
> poi un'attesa che parte da 30 secondi e raddoppia fino a un tetto di 15 minuti, con due contatori
> — uno per nome utente e uno per indirizzo». Era 🔸, cioè scritta da me e mai pronunciata; adesso è
> ✅ e più dura.*

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

> ### ⛔⛔ MA NON SOPRAVVIVE AL **SERVER** — `[M]` 25 agosto 2026
>
> ⭐ *«Sopravvive al client»* è vero e misurato. ⛔ **«Sopravvive al server» non lo è, e non era mai
> stato scritto da nessuna parte.**
>
> ⭐⭐ **SMENTITO DALLA MISURA DEL 29 SETTEMBRE 2026** (`fasi/17-l-installatore.md` §5.2, T2): dieci
> prove con Firefox vero sui quattro desktop — fermare l'unità (`KillMode=mixed`), uccidere il solo
> padre, uccidere il solo figlio — **nessun desktop muore**: muoiono padre, aiutante PAM e figlio; il
> palco (partito con `setsid --fork`, fuori dall'unità), la sessione e i programmi sopravvivono, e al
> riattacco torna lo stesso compositore con le finestre. Il fatto del 25 agosto oggi non si riproduce.
>
> `[M]` Fermando l'unità del server alle **18:14:29** per aggiornarlo, **la sessione dell'utente è
> morta con lei** — le sue finestre comprese; alle **18:14:44** ne è nata una **nuova e vuota**. La
> ragione è che la sessione grafica vive **nell'albero di processi del server**, e l'unità ha
> `KillMode=mixed`.
>
> ⇒ ⛔⛔ **Oggi aggiornare il server significa buttare fuori tutti** — ed è lo stesso danno che
> `DECISIONI.md` §4.7 vieta a chiunque di provocare spegnendo la macchina, ⚠ **fatto però da chi
> amministra, e senza che nessuno l'avesse dichiarato.**
>
> ⭐ **Non è una promessa rotta: è un confine che non era tracciato.** Sta qui perché il giorno in cui
> il prodotto diventerà un servizio da aggiornare senza fermare nessuno — **fase 15** (era la 14 fino al 21 set 2026) — questo è il
> punto da cui si riparte.
>
> ⚠ **E oggi non costa niente, e va detto**: *«nessuno sta lavorando sul server, REMOTIX è
> ancora in sviluppo»* — l'utente, 25 agosto 2026. ⇒ ⭐ **Non è un'emergenza: è un confine
> scritto adesso perché il giorno in cui ci sarà qualcuno dentro, si sappia già.**

### 5.2-bis ⭐ E finisce quando l'utente esce — le due uscite non sono la stessa

*Deciso dall'utente il 15 agosto 2026 (`DECISIONI.md` §4.1-ter e §4.1-quater).*

| il gesto dell'utente | che cosa succede |
|---|---|
| chiude la scheda, chiude il browser, **spegne o riavvia il proprio PC**, perde il campo | ⭐ **un caso solo**: il filo cade, la **sessione resta viva**, e chi torna ritrova tutto (§5.2). ⛔ Il PC dell'utente non è un attore del modello: non c'è niente da distinguere |
| sceglie **«Esci/logout»** dal menu di sistema del desktop | ⛔ **la sessione finisce**, e con lei si chiudono tutti i programmi che l'utente aveva in esecuzione. La pagina torna al **modulo di accesso** con la riga *«la sessione è terminata»*, e il motivo sul filo è `SESSIONE_TERMINATA` (`RCP.md` §8.2 `0x10`) |

⭐ **È l'unico gesto che dichiara «ho finito»**, e per questo la voce «Esci…» deve **esserci**: su
GNOME va accesa esplicitamente, perché con un utente e una sessione sola la shell non la mostra.

**E si raggiunge in due modi** *(deciso dall'utente il 15 agosto 2026, `DECISIONI.md`
§4.1-quinquies)*:

| | |
|---|---|
| la voce **«Esci…»** nel menu di sistema del desktop | la strada normale, e ⭐ **basta a sé stessa**: si raggiunge col puntatore e col dito, quindi c'è **su ogni dispositivo**, tastiera o no |
| ⭐ la scorciatoia **`Ctrl+Alt+Fine`** | la gestisce **la pagina**, non il desktop: una sola volta per tutti e quattro i desktop, e funziona **anche se il desktop non risponde più**. ⛔ La pagina se la tiene, quindi nella sessione remota quella combinazione **non arriva mai**. ⛔ **Chiede conferma** — *«terminare la sessione?»* — perché chiude tutti i programmi aperti e costa un gesto solo, dove il menu ne costa tre |

⛔ **E nessun bottone a schermo per il logout** *(deciso dall'utente il 15 agosto 2026)*: il bottone
di §7.3-bis esiste per `Ctrl+Alt+Canc`, che **non ha nessuna voce di menu**. Il logout ce l'ha.

### 5.3 I tre orologi

| Orologio | Quanto | Che cosa scatta |
|---|---|---|
| **silenzio del client** | 30 secondi | il client si considera **staccato**, e il codificatore si libera |
| **inattività dell'utente** | 30 minuti senza input | REMOTIX **stacca** il client: per rientrare servono utente e password |
| **abbandono della sessione** | ⭐ **60 minuti senza input** | la sessione si **chiude**, **con congedo pulito** (`0x03`) |

Sono in scala: secondi, minuti, minuti. Il secondo e il terzo sono **configurabili**, con quei
valori come predefiniti, e ⛔ **il valore in vigore si scrive nel registro all'avvio** — un tetto da
un'ora non lo verifica nessuno aspettando un'ora.

> ### ⛔ Il terzo orologio è cambiato — deciso dall'utente il **16 agosto 2026**
>
> Diceva ~~«**6 ore** senza alcun **attacco**»~~. ⇒ *«Niente timeout delle 6 ore: se dopo 60 minuti
> non c'è traccia di input la sessione viene killata.»*
>
> ⚠ **Cambiano due cose, non una**: il tetto (6 ore → 60 minuti) e **il criterio** — non più «nessuno
> si è attaccato», ma «nessuno ha toccato niente». Uno che si attacca e resta a **guardare** non
> rinnova più niente: il tetto si nutre degli stessi cinque gesti di §7.3 che nutrono l'orologio dei
> 30 minuti.
>
> ⭐ **E la decisione è venuta da una misura chiesta apposta**: una sessione abbandonata tiene
> memoria e quasi niente processore, e **non cresce** nel tempo. Non è una perdita, è un costo
> fisso — e l'utente ha scelto di pagarlo per un'ora invece che per sei. Il ragionamento intero, con
> la misura, è in `DECISIONI.md` §4.8.

⭐ **Un client che tace è un client che si è staccato**, e nessuna connessione «tiene il posto».
Chi arriva entra, senza timeout da aspettare: sparisce il caso «il telefono è morto in galleria e
ora non posso rientrare nella mia sessione». (`DECISIONI.md` §4.4)

⚠ Con QUIC il passaggio WiFi → LTE **non** conta come silenzio: la connessione si porta dietro il
cambio di indirizzo. I 30 secondi coprono solo le interruzioni vere.

⛔ **E una cosa che il client web aggiunge, dichiarata invece che scoperta** *(9 agosto 2026,
`STUDI.md` §web §1.2 D)*: una **scheda in secondo piano viene congelata dal browser dopo circa cinque
minuti** `[S]`. Una scheda congelata tace, quindi **si stacca**, e la sessione resta viva ad
aspettare — che è il comportamento giusto, ma va detto all'utente invece di sembrare un difetto.
⚠ L'esenzione documentata richiede un canale che WebTransport da solo non fornisce: chi volesse
tenere viva la scheda dovrebbe aggiungere **un secondo meccanismo di rete solo per quello**, e non
si fa senza una ragione misurata.

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

⭐ **Quante sessioni reggano dipende dal ferro e dalla scena**, e non si promette: le misure della
fase 10 sul ferro di allora stanno in `fasi/10-multi-tenant-e-il-budget.md` §6.

**Quando il budget è pieno si rifiuta, dichiarando il motivo.** Non si fa degradare chi sta già
lavorando per far entrare chi arriva: sarebbe una discesa non nata da una misura della linea,
cioè ciò che I1 vieta. (`DECISIONI.md` §4.6)

> ### ⭐⭐⭐ LA MONETA DEL BUDGET — fase 10, 24 agosto 2026
>
> ⛔ **La fase 10 ha smentito che il collo fosse il codificatore**: a saturarsi per primo, su quel
> ferro, era il motore che **compone** — lavoro del compositore, non nostro — e il dirupo cadeva su
> **quanto si sta componendo**, non sul numero di sessioni. ⇒ Le misure stanno in
> `fasi/10-multi-tenant-e-il-budget.md` e `DECISIONI.md` §4.6-nonies; sono storiche.
>
> ⇒ ⭐⭐ **È per questo che il budget si può calcolare PRIMA di accettare**: la moneta è il pixel
> composto, e il costo di una sessione si conosce dalla sua tela. ⛔ **Ma il pixel da solo non
> basta**: si guarda anche **il ritardo di chi è già dentro**, con una soglia
> (`BUDGET_RITARDO_AFFANNO_MS`, **22,9 ms**, in `src/budget.h`) tarata sulla macchina della fase 10.
>
> ### La regola, per intero
>
> ```
> regge(dentro, nuovo)  ⟺  domanda(dentro) + costo(nuovo)  ≤  C × tolleranza
>                           E  il ritardo di chi è dentro sta sotto la soglia
> ```
>
> **Tre manopole**, `src/budget.c`:
>
> | | predefinito | |
> |---|---|---|
> | `--budget-mpixel-s N` | ⛔ **0, cioè SPENTO** | ⭐ perché **I6**: quel che cambia ciò che l'utente vede nasce spento |
> | `--tetto-sessioni N` | **10** | e da qui scendono `MAX_ATTACCATE`, `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI` — ⭐ **il ripiego dei `#define` a 16 è finito** |
> | `--riserva F` | **0,5** | quanto si tiene da parte per chi è già dentro |
>
> ⭐ **E `BUDGET_PIENO 0x06` adesso parte davvero** — con la frase che dice *perché*, non un rifiuto
> muto. Fino alla fase 10 era dichiarato in `src/rcp.h` e in `RCP.md` §8.2 **e nessuna riga lo
> mandava mai**.
>
> ⚠ **Il giudizio dell'utente sulla capacità misurata allora è `DECISIONI.md` §4.6-septies.**

> ### ⛔ Alla fase 1 questa riga NON è onorata, ed è un ripiego dichiarato
>
> *Scritto qui l'11 agosto 2026, rilievo **R12C.17**: il ripiego era dichiarato **solo** in un
> commento di `src/main.c`, cioè dove non lo legge nessuno che non stia leggendo quel file — mentre
> questa sezione promette dieci sessioni insieme senza una riga che dica il contrario.*
>
> ### ⭐⭐ E DEI DUE RIPIEGHI, IL PRIMO È STATO CURATO — 12 agosto 2026
>
> *`DECISIONI.md` §1.10, misurato dal banco `banchi/02-pam-*` e scritto in
> `fasi/rapporti/PAM-filo-unico.md`.* ⛔ **La verifica PAM non blocca più il filo**: la interroga un
> **processo aiutante** (`src/aiutante.c`), e il ciclo `poll` torna al suo lavoro mentre PAM pensa.
>
> ⭐ Chi **non** si sta autenticando non aspetta più PAM, e la stretta di mano di chi arriva non si
> ferma; chi si autentica aspetta quanto decide PAM, e non doveva cambiare. Le misure prima/dopo
> stanno in `fasi/rapporti/PAM-filo-unico.md`.
>
> ### ⭐⭐ E IL SECONDO RIPIEGO È FINITO — 24 agosto 2026, fase 10
>
> ⛔ *Diceva: «`src/rcp.c` tiene **16** sessioni attaccate in una tabella fissa in compilazione
> (`MAX_ATTACCATE`), dove qui il tetto è dieci configurabile».* ⭐ **Adesso il tetto è uno solo,
> `RCP_TETTO_SESSIONI`, vale dieci, e si cambia a caldo con `--tetto-sessioni N`.**
>
> ⚠ Le copie a mano erano **cinque**, non una: `MAX_ATTACCATE` (`rcp.c`), `MAX_FIGLI` (`figlio.c`),
> `QUANTI_PRESENTI` (`main.c`), `WT_PALCHI` (`webtransport.c`, era **8** — cioè **un sesto numero
> ancora diverso**). ⭐ Tutte scendono dal tetto.
>
> ⛔ **E una è stata lasciata separata apposta**: `MAX_IN_VOLO` (`src/aiutante.c`) **non è** il numero
> delle sessioni — è quante verifiche PAM stanno in volo insieme. ⇒ ⭐ *unificare per simmetria quel
> che non è la stessa quantità è un difetto nuovo, non una cura.*
> Il confine per intero sta in `FASI.md` §01-filo-nudo, «Che cosa è stato sviluppato».
>
> ### ⭐ E i due ripieghi hanno una scadenza, decisa dall'utente l'11 agosto 2026
>
> ⛔ *Non si copia qui che cosa è stato deciso: si rimanda dove le decisioni vivono.*
>
> | | |
> |---|---|
> | **il filo** | ✅ **CURATO il 12 agosto 2026** — **`DECISIONI.md` §1.10**, con un **processo aiutante** come deciso. ⭐ La misura che ha spostato la decisione l'ha presa **B8**: il filo restava fermo per secondi a ogni tentativo, ⛔ e **a metterlo era PAM**. ⭐ E dopo la cura chi *non* si sta autenticando non aspetta più (`banchi/02-pam-fermo.py`, `fasi/rapporti/PAM-filo-unico.md`) |
> | **il tetto** | **`DECISIONI.md` §1.11** — ⛔ **resta 16 fisso fino alla fase 3**, di proposito: qui sopra è scritto che *«il limite vero non è un conteggio, è un budget di pixel al secondo»*, quindi qualunque numero di oggi è un segnaposto e cambiarlo adesso vuol dire cambiarlo due volte. ⚠ **E il prezzo è questa riga**: per due fasi il codice dice **16** e questa sezione dice **dieci**, ed è la stessa forma che ha prodotto il difetto della finestra di cinque minuti (R12C.5) |

---

### 5.9 ⭐⭐ LA SCALETTA DI UNA SESSIONE, PASSO PER PASSO

> #### ⛔ Perché questa scaletta sta QUI, e da dove viene
>
> *Era un documento suo, `SESSIONE.md`, nato il 16 agosto 2026 dal suggerimento dell'utente:
> «prepara una nota in cui riporti la scaletta punto per punto di cosa deve avvenire per il
> corretto set-up di una sessione». ⭐ È entrata qui il 16 agosto 2026, in §5, perché **descrive
> il prodotto**, non una fase: dice che cosa deve essere vero perché una sessione esista.*
>
> ⚠ **E il resto di quel documento non è venuto qui**: erano le misure del 16 agosto, e stanno
> in `FASI.md` §05-la-sessione, dove vivono le misure di quella fase.


> ⛔ **Perché questo documento esiste, e perché non esisteva prima.**
>
> La mattina del **16 agosto 2026** l'utente ha provato cinque volte la stessa scena — collegati,
> esci, ricollegati — e ogni volta ha trovato un difetto diverso: bande nere, desktop «rotto»,
> nessun input, il desktop che compare dopo molti secondi. ⛔ Ogni volta si curava **il sintomo che
> il registro mostrava**, e si tornava a provare.
>
> ⭐ Erano **quasi tutti lo stesso difetto**, visto da facce diverse: un passo di questa scaletta
> che non era mai stato scritto, e quindi nemmeno verificato.
>
> ⇒ *«Prepara una nota in cui riporti la scaletta punto per punto di cosa deve avvenire per il
> corretto set-up di una sessione»* — **suggerimento dell'utente**, ed è il documento che avrebbe
> risparmiato quella mattina.

⚠ **Come si legge**: la colonna «se manca» è quella che serve quando qualcosa non va. Si parte dal
sintomo, si trova il passo, e si guarda **chi** doveva farlo. ⛔ Non si parte mai dal codice.

---

### Parte A — quel che dev'essere vero PRIMA, e non lo fa il prodotto

*Sta in `src/provisiona.sh`, e si verifica con `sudo bash src/provisiona.sh verifica`.*

| # | che cosa | chi | se manca |
|---|---|---|---|
| A1 | l'**utente esiste** e ha una parola d'ordine | provisioning | PAM rifiuta: «utente o parola d'ordine non corretti» — e la diagnosi punta sulla parola |
| A2 | ⛔ l'utente è nei gruppi **`video`** e **`render`** | provisioning | ⚠ **il sintomo è «lento», non «rotto»**: senza seat non arrivano le ACL di `uaccess`, Mesa ripiega su **llvmpipe** e il compositore disegna in software: anche un comando nel terminale risponde con un ritardo che si vede |
| A3 | `/etc/pam.d/remotix` esiste **e chiama `pam_systemd`** | provisioning | nessuna sessione logind ⇒ il compositore **non parte affatto** (vedi B3) |
| A4 | la regola **polkit** (12 azioni) e `logind.conf` | provisioning | un utente remoto può spegnere la macchina e portarla via a tutti (`DECISIONI.md` §4.7) |
| A5 | la regola **udev** della scheda | provisioning | il compositore sceglie la GPU **a caso**; le misure valgono per quel ferro e non per il prodotto (§4.6-quinquies) |
| A6 | ⛔ **il server NON gira dentro una sessione utente** | chi avvia il servizio | `pam_systemd`, se chi chiama sta già in una sessione, **non ne crea una seconda e non lo dice**: i figli restano senza runtime, senza bus e senza desktop. ⚠ In produzione non capita (unità di sistema); **capita solo in prova**, cioè dove si studia |

> ### ⛔⛔ A6, la trappola dentro la trappola: `setsid` **non basta**
>
> `[M]` **16 agosto 2026.** Il server era stato riavviato via `ssh`, e
> `riavvia-7700.sh` lo lanciava con `setsid` — messo lì per un'altra ragione giusta (`sudo` con
> `use_pty` stronca quel che resta nel suo pseudo-terminale).
>
> ⇒ ⚠ **`setsid` stacca dal terminale, non dalla sessione di logind.** Il processo resta nel cgroup
> della sessione `ssh` di chi ha dato il comando, e da lì A6 scatta in pieno: `[M]` `loginctl` non
> mostrava **nessuna** sessione per `prova`, `/run/user/1001` non esisteva, e il registro ripeteva
> *«NON ho il bus di sessione: Could not connect: No such file or directory»*. **Otto giri di banco
> falliti su otto**, e la faccia del difetto era la solita: «il desktop non parte».
>
> ⭐ **La cura è farlo partire dove starebbe in produzione**: `systemd-run --unit=…`, cioè un'unità
> di sistema transitoria in `system.slice`. ⛔ E **si verifica**, perché A6 è silenzioso per
> costruzione: `riavvia-7700.sh` legge `/proc/PID/cgroup` del processo vivo e **rifiuta di dare
> l'OK** se ci trova `user@` o `session-`.
>
> ⚠ E c'era un secondo insegnamento nello stesso file: ⛔ **lo script che avvia il prodotto non era
> nel deposito** — viveva solo sulla macchina di prova. Le sue trappole erano scritte solo dentro se
> stesso, nessuna revisione le ha mai lette, e quella nuova è costata un'ora di diagnosi su un
> difetto che *questa tabella aveva già scritto*. ⇒ Adesso sta in `src/riavvia-7700.sh`.

---

### Parte B — quel che fa il prodotto, in quest'ordine

| # | che cosa | dove | se manca / se va storto |
|---|---|---|---|
| B1 | **PAM autentica** (asincrono, l'aiutante) | `aiutante.c` | il filo si ferma per secondi (§1.10) |
| B2 | nasce il **figlio**: gruppi → gid → uid, e si verifica col nucleo | `figlio.c` | un processo che gira come chi non deve |
| B3 | ⛔⭐ il figlio **apre la sessione PAM**: `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `PAM_RHOST`, **nessun `XDG_SEAT`** | `figlio.c`, passo 2-bis | ⛔ Mutter chiede `sd_pid_get_session()`, riceve **ENXIO** e muore con *«Failed to find any matching session»*. ⚠ Il **linger** non basta: dà runtime e bus, ma mette i processi in uno scope di classe `manager` |
| B4 | le variabili **`XDG_*`** si **leggono** da `pam_getenvlist`, non si inventano | `figlio.c` | un valore *dichiarato* al posto di uno *avuto*: regge finché regge |
| B5 | il client **ATTACCA dichiarando la tela = la finestra** | `pagina.html` | ⛔ la sessione nasce con la tela sbagliata e va **ridimensionata**, e il ridimensionamento è una gara: bande nere, desktop «rotto», input nel posto sbagliato |
| B6 | ⛔ il server **dice al palco la tela** nell'istante in cui la concede | `rcp.c`, dopo `SESSIONE` | il palco nasce a una misura che nessuno ha chiesto, e ogni fotogramma si butta |
| B7 | ⛔ **la sessione precedente dev'essere FINITA** — il gestore d'utente **e** `gnome-session-restart-dbus.service` | `sessione.c` | ⛔ la sessione nuova nasce dentro quella che muore e **muore con lei senza scrivere una riga**: `[M]` il suo registro resta a **zero byte** |
| B8 | si scrivono le **impostazioni**: `Ctrl+Alt+F*` svuotate, «Esci…» acceso, sospensione automatica spenta, blocca-schermo spento | `sessione.c` | il logout non ha una voce; la macchina si addormenta sotto una sessione viva |
| B9 | si scrive il **drop-in** della Shell (`--headless --no-x11`, ⛔ **senza `--virtual-monitor`**) | `sessione.c` | con un monitor suo la sessione è «sana» per v1 e **nera** per noi |
| B10 | si **avvia** `gnome-session`, e ⛔ **non si aspetta**: la risposta è il fotogramma | `sessione.c` + il ciclo di ri-tentativi | un figlio che aspetta 40 s è un figlio che non risponde al padre |
| B11 | il figlio **dice «ATTENDI»** finché il palco non c'è, e riprova subito | `figlio.c` | il padre **deduce** un fallimento dal silenzio e risponde `NON_ORA`: da lì i due lati non si rimettono più d'accordo |
| B12 | monta il **palco**: `RecordVirtual` → PipeWire → il monitor | `mutter.c`, `cattura.c` | nessun pixel |
| B13 | apre il **canale di input** (`libei`) sulla tela | `input.c` | il desktop si vede e non si comanda |
| B14 | **inibisce** sospensione e inattività (`SUSPEND\|IDLE`, ⛔ mai `LOGOUT`) | `sessione.c` | la notifica «Automatic Suspend», e la macchina che si addormenta |
| B15 | ⭐ **verifica**: la sessione non ha seat, e da qui non si spegne | `figlio.c` + `sentinella.c` | «scritto non è in vigore» (E1). ⛔ E la fa **il figlio**: root si sente rispondere «yes» perché logind guarda `CAP_SYS_BOOT` prima di polkit |

---

### Parte C — l'uscita, che è l'altra metà

| # | che cosa | se va storto |
|---|---|---|
| C1 | il **filo che cade** (scheda chiusa, PC spento, campo perso) ⇒ il posto si libera, **la sessione resta viva** (I4) | si perde il lavoro di chi voleva solo cambiare stanza |
| C2 | **«Esci»** — dal menu o con `Ctrl+Alt+Fine` ⇒ la sessione finisce e i programmi si chiudono | — |
| C3 | ⛔ il congedo **`0x10`** parte **PRIMA** che la sessione muoia, e va a **tutti** i client di quell'utente | chi guarda resta su uno schermo fermo per trenta secondi e legge «errore di rete» (rilievo B-7) |
| C4 | ⛔ il figlio **non** rifà la sessione dopo un'uscita: aspetta un attacco nuovo | il desktop che l'utente ha appena chiuso **ricompare da solo** |
| C5 | la pagina torna al **modulo di accesso**, e si rispoglia: via `data-schermo`, via la Pointer Lock, via lo schermo intero | un modulo di accesso dentro il vestito del desktop, col mouse ancora catturato |

---

### Parte D — dal sintomo al passo

⭐ **È la tabella da leggere per prima quando qualcosa non va.**

| il sintomo | il passo |
|---|---|
| «il desktop non compare» | B3 · B7 · A6 |
| «compare dopo molti secondi» | B7 (l'avvio fallito si recupera, ma dopo qualche secondo) · B10 |
| «bande nere ai lati» | B5 · B6 |
| «il desktop è rotto» | B5 · B6 (la tela e il palco non combaciano) |
| «nessun input» | B13 · **B6** (la regione del puntatore segue la tela: se la tela balla, i clic finiscono altrove) |
| «va lento» | **A2** (llvmpipe) · A5 (scheda sbagliata) |
| «il terminale resta congelato finché non muovo il mouse» | la coda della raffica in `cattura.c` (`LEZIONI.md` §6.5) |
| «si può spegnere la macchina» | A4 · B15 |
| «stavo leggendo e mi si è **congelato lo schermo**» · «qualcun altro mi ha preso il desktop» | ✅ **l'orologio del silenzio**, `FASI.md` §05-la-sessione §6-bis — riparato il 16 agosto. ⚠ Se ricompare, cerca nel registro *«il margine si sta assottigliando»* |
| «un tasto è rimasto premuto dopo che è caduta la linea» | ⭐ non succede: il server rilascia tutto al distacco (`RCP.md` §7.3) — `FASI.md` §05-la-sessione §6 |

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

### 6.1 ✅ ⭐⭐ ATTUATA il 15 agosto 2026 — e questa tabella adesso descrive il prodotto

*Fino a quella notte era il modello che si voleva; da lì è quel che il codice fa, misurato sulla
macchina di prova e giudicato dall'utente su due client («sia su Linux sia su Android è tutto
perfetto»).*

| momento | che cosa succede davvero | `[M]` |
|---|---|---|
| **attacco** | la pagina manda `ADATTA_TELA` con la misura della propria finestra, e la tela diventa quella | tela **1264×800** in una finestra 1265×800, scala di disegno **1,000** |
| **durante la sessione** | ⛔ il client riscala, e il desktop **non si tocca mai** — dal 17 agosto 2026 non c'è più nemmeno l'interruttore che lo faceva (`DECISIONI.md` §5.1-bis) | ~~il ridimensionamento a caldo~~ — misurato, e uscito lo stesso: costava poco su Mutter e **non si poteva fare** su KWin ≤ 6.7.4 |
| **riattacco da un altro dispositivo** | `SESSIONE` concede **la tela che il palco ha già** (§4.5), così i pixel arrivano subito, e poi la pagina chiede la sua | **0 fotogrammi scartati** |

⛔ **E la riga «È 1:1» è diventata vera in un senso più stretto di quel che sembrava**: non «un
pixel del desktop per un pixel dello schermo», ma **un pixel del desktop per un pixel della
finestra** — vedi §6.1-bis, che è stata corretta quella stessa notte.

### 6.1-bis ⛔ «La risoluzione del client», quando il client è una finestra

*Chiarito il 9 agosto 2026. Il modello di §6.1 diceva «la sessione legge la risoluzione del
client», e con un programma a schermo intero non c'era altro da dire. **Un browser è una finestra
dentro uno schermo**, e le due misure sono diverse — a volte molto.*

| | Che cosa è | Chi la usa |
|---|---|---|
| **la tela** | ⛔ ~~lo schermo del dispositivo~~ → ⭐ **la FINESTRA, in pixel fisici** — corretto il 15 agosto 2026, vedi il riquadro qui sotto | si fissa **all'attacco e al riattacco**, con `ADATTA_TELA`, e ⛔ **non cambia più per tutta la sessione** (§5.1-bis, 17 agosto 2026) |
| **la vista** | **la finestra**, cioè quanto la pagina ha davvero da disegnare, sempre in pixel fisici | si rinegozia a ogni ridimensionamento |

> ## ⛔⛔ CORRETTA IL 15 AGOSTO 2026 — la tela è la FINESTRA, non lo schermo
>
> *Questa tabella diceva: la tela è **lo schermo del dispositivo**, «non la finestra», e «si fissa
> all'attacco e non si muove». ⇒ Con quella regola tela e vista sono **quasi sempre diverse**, e da
> lì discendono le bande, la scala ≠ 1 e la conversione delle coordinate.*
>
> ⛔ **L'ha rovesciata `DECISIONI.md` §5.0-sexies**, decisa dall'utente il 14 agosto 2026 dopo due
> giorni in cui il mouse sul DeX è rimasto inutilizzabile: *«abbiamo due tele, quella del server e
> quella del client… se i compositori sanno dare la misura esatta, non servono nemmeno le
> conversioni»*. ⇒ La tela prende la misura della **finestra**, e con lei spariscono insieme
> **quattro sintomi**: bande nere, testo interpolato, ri-attacco a misura diversa e i quattro
> secondi fra login e desktop.
>
> ⚠ **E la ragione che questo paragrafo dava per scegliere lo schermo non è stata ignorata, è stata
> pagata**: *«un desktop grande quanto la finestra che avevi aperto per caso resterebbe tale per
> tutta la sessione — piccolo per sempre»*. ⛔ Era vero **finché la tela non si poteva cambiare**.
> Adesso si cambia **a ogni attacco e a ogni riattacco** — ⚠ *durante* la sessione no, e dal 17
> agosto 2026 nemmeno dietro un interruttore (`DECISIONI.md` §5.1-bis). La frase «piccolo per
> sempre» non descrive più niente lo stesso: bastava riattaccarsi.
>
> ⭐ **E il «appena vai a schermo intero torna 1:1 e nitido» è diventato la condizione NORMALE**, non
> il premio dello schermo intero: `[M]` scala **1,000** e `image-rendering: pixelated` in una
> finestra qualunque.

⭐ **Perché lo schermo e non la finestra**, che era l'altra scelta possibile: la tela è **il desktop**,
e un desktop grande quanto la finestra che avevi aperta per caso al primo collegamento resterebbe
tale per tutta la sessione — piccolo per sempre, e morbido appena ingrandisci (§6.3 ne dichiara già
il prezzo). Prendendo lo schermo, la finestra piccola mostra il desktop **rimpicciolito e intero**,
e appena vai a schermo intero torna **1:1 e nitido**.

⭐ **E c'è una seconda ragione, che arriva dalla tastiera**: la Keyboard Lock esiste **solo a schermo
intero** (§7.3-bis). Cioè il modo in cui questo prodotto si usa davvero *è* lo schermo intero — ed è
esattamente la condizione in cui vista e tela coincidono e non si scala niente.

⚠ **Quel che si accetta, dichiarato:**

| | |
|---|---|
| il telefono in mano, in verticale | la tela nasce **alta e stretta**, che come desktop è strano. È il ripiego d'emergenza (§7.2), e il caso primario è DeX con uno schermo vero |
| **ruotare il telefono** dopo l'attacco | ⛔ la tela **non gira**: si vedono le bande, e il client riscala impaginando (§6.2). ⚠ Ed è il comportamento **dichiarato**, non un difetto da curare: l'interruttore che la faceva girare è uscito il 17 agosto 2026 (`DECISIONI.md` §5.1-bis). ⭐ Per riavere la misura giusta ci si **riattacca** |
| uno schermo 4K | la tela nasce 4K, e sono **quattro volte i pixel** di 1080p da codificare per ogni sessione: pesa sul budget di §5.5, non sulla cattura (`LEZIONI.md` §6.4) |
| ⭐ **la tela al massimo 4096×2304** (dal 1 ottobre 2026, decisione dell'utente: *«4096 max di larghezza va benissimo, non ho mai preteso di più»*) — uno schermo 5K, 8K o ultralargo | la tela **non si rifiuta**: il lato che sfora si porta al massimo e l'altro resta (5120×2880 → **4096×2304**, 5120×1440 → **4096×1440**), e la pagina la impagina a scala 1 con le bande intorno (§6.2), come ogni tela più piccola della finestra. ⚠ Perché: H.264 sulla scheda Intel si ferma a **4096 px per lato**, e Firefox su Linux riceve solo H.264 — una tela più larga avrebbe avuto video solo su Chrome. 2304 è il 16:9 a 4096 (ci sta il DCI 4096×2160). Il limite è del protocollo, `RCP.md` §4.5; il minimo resta **320×240** |

`[?]` **Tre cose che nessuno ha misurato, e che vanno nella sonda del browser**, perché tutte e tre
cambiano il numero che il client dichiara:

1. ⛔ **lo zoom della pagina falsa il conto — MISURATO, e la formula qui sopra non regge.**
   ⚠ *Questa riga diceva* «*Va misurato quanto e su quali motori*»: **è misurato**, e la risposta è
   *«su uno dei due, del 50 %»* — banco **S5**, `[M]` 10 agosto 2026, dettaglio in
   `web/rapporti/S-esiti-sonda.md` §3 e in `DECISIONI.md` §5.0-quater. Corretta l'11 agosto 2026,
   rilievo **R12C.8**.

   | Motore | zoom 100 % | zoom 150 % | la tela che questa formula darebbe |
   |---|---|---|---|
   | **Chrome 151.0.7922.108** | `screen` 1920×1080, `dpr` 1 | `screen` **1920×1080**, `dpr` 1,5 | ⛔ **2880×1620** |
   | **Firefox 140.13.0esr** | `screen` 1920×1080, `dpr` 1 | `screen` **1280×720**, `dpr` 1,5 | ✅ 1920×1080 |

   ⛔ **Su Chrome `screen.width` non cambia con lo zoom di pagina**, quindi
   `screen.width × devicePixelRatio` dà `risoluzione × zoom`: un utente che ha premuto `Ctrl +`
   prima di collegarsi dichiara una tela **del 50 % più grande di quella che esiste**, e se la tiene
   per tutta la sessione. ⚠ **E non si aggiusta con una riga**: lo zoom di pagina non è leggibile da
   JavaScript in modo portabile, e nessuna delle due misure da sola dice quale sia quella vera.
   ⛔ **Finché la formula non è rivista, quel che questo documento prescrive produce un numero
   sbagliato su un motore su due** — e va scritto qui invece di essere scoperto alla fase 2, quando
   il sintomo sarà *«il desktop remoto è più grande dello schermo»*. La misura su **DeX** manca (la
   macchina non c'era): il verso in cui sbaglia un telefono non lo sa nessuno;
2. **su DeX, `screen` risponde con lo schermo esterno o con quello del telefono?** È l'uso primario,
   e la risposta decide se la tela nasce giusta o grande quanto un telefono;
3. i browser **arrotondano** queste misure per non far riconoscere il dispositivo: quanto, e se
   l'arrotondamento possa produrre un numero **dispari** — che `RCP.md` §4.5 rifiuta.

**Ridimensionare la finestra del client non tocca mai il desktop**, su nessuno dei quattro
compositori. Le ragioni, in ordine di peso: su KDE 6.3.6 — cioè Debian stabile — **non si può**
`[M]`; la correzione a monte esiste ma Debian non aggiorna Plasma; e ⛔ **anche dove funziona fa
una cosa peggiore**, perché ridimensionare un output **ridispone le finestre dell'utente** `[R]`.
La versione «giusta» scompiglia il lavoro, quella «rotta» lo lascia fermo. (`DECISIONI.md` §5.1)

### 6.2 Le proporzioni

**Si impagina, non si stira.** Se la finestra ha proporzioni diverse dalla tela si conservano le
proporzioni e si mettono le bande: allungare deforma il testo e lo rende illeggibile.

Il caso è raro per costruzione — all'attacco le proporzioni **combaciano sempre** — e resta solo
quando la finestra cambia misura dopo l'attacco (si riscala, `DECISIONI.md` §5.1-bis) e nel ripiego di §6.3. Sul telefono in verticale la banda sarebbe
enorme: lì serve lo zoom con scorrimento, che è nel ventaglio dei gesti (§7.2).

### 6.3 Il ripiego su KDE, dichiarato

Al riattacco a misura diversa su KWin < 6.8 la tela **non può** cambiare. Si tiene quella vecchia
e riscala il client — e non costa una riga in più, perché è lo stesso codice del punto
«durante la sessione». **Il ripiego si dichiara nel registro.**

### 6.4 ~~«Adatta il desktop a questa finestra»~~ — ⛔ uscita dal prodotto (`DECISIONI.md` §5.1-bis)

~~Il ridimensionamento vero della tela si fa nella forma della **negoziazione PipeWire** — una strada
sola per GNOME, wlroots e KDE ≥ 6.8, che su KDE si accende da sé all'aggiornamento.~~
⇒ La misura nuova si prende **solo ricollegandosi** (riattacco, F-018). Riconfermato dall'utente il
2 ottobre 2026, dopo la sua prova a mano.

> ### ⛔ CORRETTA IL 15 AGOSTO 2026 — «mai come automatismo» non è più vero, e la ragione è una decisione dell'utente
>
> *Questo paragrafo diceva: «Il ridimensionamento vero della tela resta come **scelta esplicita
> dell'utente**, mai come automatismo. Dove il compositore non lo sa fare la voce è **spenta**».*
>
> ⛔ **La prima metà è stata rovesciata da `DECISIONI.md` §5.0-sexies** (14 agosto 2026, decisa
> dall'utente): *«la tela del server si chiede della misura della tela del client»*, e quella misura
> si chiede **all'attacco di ogni sessione**, senza che nessuno prema niente. ⇒ All'attacco è un
> automatismo, ed è il punto: senza, tornano le bande nere, il testo interpolato, la conversione
> delle coordinate e i quattro secondi di attesa fra il login e il desktop.
>
> ⛔ **La seconda metà vale ancora, e dal 17 agosto 2026 vale in modo più netto**: durante la
> sessione viva la tela **non si tocca mai**, e non c'è più nemmeno l'interruttore per farlo
> (`DECISIONI.md` §5.1-bis — *«non voglio mettere delle eccezioni nel progetto»*). Su KWin ≤ 6.7.4
> ridimensionare un output non si può affatto, e dove si può ridispone le finestre dell'utente.
>
> ⚠ **E «dove il compositore non lo sa fare la voce è spenta» vale per intero**: il server risponde
> `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` e il client **DEVE** mostrarla spenta (`RCP.md` §7.1).
> Non si finge che sia riuscito.

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
| tocco sul bottoncino **⌨** in alto a destra | apre la tastiera del telefono; un altro tocco (o «indietro») la chiude |

⭐ **La tastiera a schermo si apre solo a richiesta** (`DECISIONI.md` §10.28): col telefono in mano non si
apre da sola, perché coprirebbe metà del desktop. Il bottoncino ⌨ c'è **solo** in questa disposizione — sul
computer e sul DeX col mouse non esiste — e non toglie niente al desktop: il dito clicca dove sta il puntatore,
non dove cade (§7.1). Sta in alto perché la tastiera aperta copre il basso.

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

**Sul telefono in mano** vale la stessa regola: quel che si scrive con la tastiera a schermo (aperta col
bottoncino ⌨, §7.2) arriva come **lettere**, correzioni automatiche comprese — la parola corretta si riscrive
cancellando quel che era cambiato; Invio e Cancella arrivano come **posizioni**.

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

> ⛔ **Riscritta la sera del 9 agosto 2026 dalla misura S3** (`STUDI.md` §web §5). Questa sezione diceva
> che la Keyboard Lock esiste *«solo su Chrome ed Edge»* e che `F11` e `Ctrl+Shift+I` sono perduti.
> **Era sbagliata su tre punti**, e in meglio.

| | |
|---|---|
| **la leva** | ⭐ **non è più solo di Chrome**: `keyboardLock` è entrato nello standard WHATWG l'**8 maggio 2026** e l'hanno spedito Safari 26.4 e Firefox 151 `[S]`. Chrome ed Edge restano sulla forma vecchia — ⚠ **la pagina deve saperle entrambe** |
| **quanto si perde** | ⭐ **`[M]` 14 agosto 2026 — MISURATO, ed era `[R]`.** Su **Chrome 151** la tesi regge: a schermo intero **con la Keyboard Lock** le riservate del browser passano da **8 a 0** — restano esattamente `F11` ed `Escape`. ⛔ **E su Firefox 140 ESR è FALSA, in modo che non avremmo indovinato: a schermo intero PEGGIORA** (5 → **7**), e non ha **nessuna delle due forme** della lock. ⚠ Safari **non provato**, e resta `[?]`: non si deduce dagli altri |
| ⭐ **e in una PWA installata è vuota** | tutte le scorciatoie arrivano alla sessione. ⛔ **Ma una PWA vuole un certificato fidato**: dietro l'eccezione di §4.1 il Service Worker non si installa `[R]`. **Chi ha un dominio non compra solo l'assenza dell'avviso: compra la tastiera intera** (`STUDI.md` §web §1.2 B) |

⛔ **Gli stati sono tre, non due**, e il secondo è il peggiore *(`STUDI.md` §web §8-bis, O8)*:

| | |
|---|---|
| **consegnata** | arriva alla sessione remota, e basta |
| ⛔ **consegnata *e* riservata** | la sessione remota riceve la battuta **e** il browser esegue il suo comando. ⛔⭐ **E lo stato esiste, è MISURATO ed è LARGO**: `[M]` 14 agosto 2026, **18 combinazioni su 42** su Chrome in finestra ⇒ *una prova che guardasse solo il lato della sessione le avrebbe dichiarate **tutte verdi**.* ⭐ **E si spegne con `preventDefault()`**: 18 → 0 su Chrome, 15 → 0 su Firefox. ⚠ **L'esempio che c'era qui era sbagliato**: `Ctrl+Tab` di Firefox **non** è in questo stato — misurato, sta nel **terzo**, e la pagina non ne vede nemmeno il `keydown` |
| **non consegnata** | il browser se la tiene |

⚠ **Da cui la misura non è «arriva?» ma «arriva *e basta*?»** — una prova che guarda solo il lato
della sessione dichiara verde proprio il caso peggiore.

**Quel che si perde davvero, e non si recupera:**

| | |
|---|---|
| `Ctrl+Alt+Canc` | ⭐ **non dal filo, ma dall'interfaccia**: si dà all'utente un **bottone a schermo**. Tre riferimenti maturi su tre lo fanno, ed è **un requisito, non un ripiego di fortuna** *(O7)* |
| l'uscita da schermo intero | ovunque, per costruzione: è la via di fuga dell'utente |
| ⛔ **su iPhone, tutto** | lo schermo intero è **parziale in tutte le versioni** `[S]`, e senza schermo intero **non c'è keyboard lock** *(O9)*. Su iPhone si perde l'intera partita della tastiera, non qualche scorciatoia |
| ⛔ **su macOS, tutte le scorciatoie di sistema** | non esiste un aggancio: la funzione che dovrebbe fornirlo **restituisce `nullptr`** `[R]` |
| ⛔ **su Android e DeX, ogni combinazione con Meta** | per regola AOSP — ⚠ e DeX è l'uso primario (`DECISIONI.md` §5-bis.0) |

⛔ **Che cosa si fa**: la pagina **dichiara** quali scorciatoie non può consegnare su quel browser.
NON si finge che funzionino, e non si inventa una scorciatoia sostitutiva senza dirlo.

⚠ **Due trappole della lock, e la seconda morde dove fa più male** *(O10)*: non esiste se lo
schermo intero è stato aperto con `F11` — **e non lo dice** — e **si spegne da sola quando la pagina
perde il fuoco**, cioè esattamente nell'istante in cui un modificatore resta premuto. ⭐ La cura non
tocca il protocollo: **la pagina rilascia tutto quel che ha premuto quando perde il fuoco**, e al
riattacco ci pensa `RCP.md` §7.3, che obbliga il server a rilasciare tutto al distacco.

`[?]` **Restano due domande, e sono le due che pesano di più**: se la Keyboard Lock funzioni su
**DeX**, e se la PWA valga anche su **Chrome per Android**.

### 7.4 Mouse e tastiera fisici — su Android è la strada principale

Il mouse passa da *Pointer Capture*: il cursore di Android sparisce — altrimenti se ne vedrebbero
due — e i suoi spostamenti muovono **lo stesso puntatore che muove il dito**. Una freccia sola,
due modi di spingerla. L'accelerazione la applica il **client**: applicata da entrambi si
sommerebbe.

> ⛔ **Superato dal 14-15 agosto 2026**: la cattura del puntatore non scatta più da sola (resta a
> mano, `REMOTIX.input_classico.aggancia()`), il puntatore è **assoluto** e ogni evento porta la
> propria posizione (`DECISIONI.md` §5.0-sexies). ⭐ **Dal 2 ottobre 2026 anche i clic** vengono dai
> pointer events (`pointerdown`/`pointerup`), come i movimenti: su Chrome per Android i `mousedown`
> di compatibilità nascono solo dopo un tocco riconosciuto, e un clic lungo o un trascinamento non
> arrivava (prova a mano dell'utente; verificato col DeX lo stesso giorno: *«i clic funzionano»*).
>
> ⚠ **Limite dichiarato, non nostro:** sui Samsung (DeX compreso) Chrome **non consegna i movimenti
> a pulsanti alzati** (noVNC #1727, aperto dal 2022, lo stesso su moonlight-android #573, che è
> un'app nativa). ⇒ Puntare, cliccare e trascinare colpiscono giusto; **manca l'anteprima**: la forma
> del puntatore sui bordi delle finestre, i pulsanti che si illuminano, i suggerimenti. Riconfermato
> dall'utente col DeX il 2 ottobre 2026.

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

### 8.1 Gli scenari da servire — e il pavimento

⭐ **La rete minima del prodotto è 30 Mbit/s**, ed è un **pavimento dichiarato**: sotto, REMOTIX
non promette niente e non misura niente come requisito. *«Al di sotto di questo limite l'utente
nemmeno riesce a navigare, figuriamoci usare remotix»* — l'utente, 23 agosto 2026
(`DECISIONI.md` §3.1-bis).

Sopra il pavimento il requisito resta **l'adattamento**, non una seconda soglia:

| Collegamento | Banda | Ritardo e perdita | Che cosa fa il server |
|---|---|---|---|
| fisso buono | **30+ Mbps** | bassi | punta al desiderato |
| ⭐ **il pavimento** | **30 Mbps** | medi | **spende tutto quel che c'è**, e tiene il minimo |
| ⚠ sotto il pavimento | < 30 Mbps | qualsiasi | **fuori dal promesso**: degrada e non stacca, ma non è un requisito |

⚠ **Il divieto di staccare (§8.3) non si indebolisce**: vale anche sotto il pavimento. Quel che
sotto il pavimento non c'è più è la **promessa**, non il comportamento.

> ⛔ **IL NUMERO ERA 20, ED È DIVENTATO 30 la notte del 23 agosto 2026** (`DECISIONI.md` §3.1-sexies):
> *«ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps»*. ⚠ Le misure della
> fase 9 sono tarate su 20 e **non si riscrivono**: stanno in `fasi/09-la-qualita-e-la-degradazione.md`,
> e sono storiche.

> ### ⛔⭐⭐ E LA BANDA NON È LA GRANDEZZA CHE DECIDE — `DECISIONI.md` §3.1-ter
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
> perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter»* — 23 agosto 2026.
>
> ⛔ E la fase 9 l'ha mostrato: a banda libera il caso peggiore reggeva, ma **la spirale di chiavi
> partiva al primo pacchetto perso**, molto prima del calo che l'utente **vede**
> (`fasi/09-la-qualita-e-la-degradazione.md`). ⇒ **Il pavimento di banda è una premessa, non un
> requisito mordente**: il requisito mordente è il comportamento su una linea **sporca**.
>
> ⛔ E una linea che perde **a raffiche** si dichiara morta (§3.1-quater): 10 s senza pacchetti, o
> una perdita copiosa dentro 1-2 s. ⚠ Non contraddice §8.3 — non si stacca *invece di degradare*: si
> dichiara rotto un filo che **non porta più niente**, e l'utente rientra a mano.

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
ma meno di quanto si temeva *(misura S3, 9 agosto 2026, `STUDI.md` §web §5.3)*:

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
(`EnableClipboard`). *Corretto il 9 agosto 2026 da `STUDI.md` §gnome §10 `[R]`; questa riga diceva il
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

### 10.1 ⛔⭐⭐ Quando la finestra si stringe, **l'audio passa davanti al video** — *24 agosto 2026*

⚠ **Questa riga arriva tardi**: la decisione era presa **nel codice** dall'inizio (`wt_scrivi()`) e
**non era scritta da nessuna parte** — né qui, né in `RCP.md` §6.3, né in `DECISIONI.md`, né in
`CODER.md`. È stata trovata cercando la causa dell'audio rifiutato su rete cattiva
(`fasi/09` §20.2-quater), ed è precisamente il genere di cosa che una fase di misura esiste per
scoprire: **una politica del prodotto che nessun documento dichiarava.**

> ⛔ **In ogni passata di scrittura i datagram entrano nel pacchetto PRIMA dei byte di video**, e su
> una finestra da due o tre pacchetti *«prima»* vuol dire **«invece»**.

⭐ **La ragione è che i due carichi non si degradano allo stesso modo:**

- un blocco d'**audio** in ritardo **non serve più a nessuno** — §6.3: nessuna ritrasmissione,
  nessun riordino, e chi ascolta ha un cuscino di 250 ms e poi **un buco che si sente**;
- un fotogramma in ritardo **è ancora un fotogramma**: gli stream sono affidabili, e i suoi byte
  partono la passata dopo.

⚠ **Il prezzo, dichiarato**: è banda tolta al video **proprio quando ce n'è poca**. ⭐ Ed è limitato
**per costruzione**: la coda dei datagram è lunga **otto**, quindi al massimo otto pacchetti passano
davanti.

*(La decisione è scritta per esteso, alternativa scartata compresa, nel riquadro di `wt_scrivi()`.)*

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
| **XFCE** (labwc) | studiato, non ancora servito — ⛔ **e non è lo stesso caso di LXQt**, vedi sotto |
| **LXQt** (labwc) | studiato, non ancora servito |

> ### ⛔ «XFCE (labwc)» e «LXQt (labwc)» **non** sono la stessa riga — corretto il 14 agosto 2026
>
> Le due voci qui sopra hanno lo stesso compositore fra parentesi, e da quel giorno in poi sono
> state lette come **un caso solo**. `[R]` **Non lo sono**, e la differenza morde proprio dove
> serve la tela su misura (`DECISIONI.md` §5.0-sexies):
>
> | | |
> |---|---|
> | **XFCE** | ha `xfsettingsd`, **primo client della sessione**, che riscrive tutti gli output e **per impostazione predefinita spegne ogni output nuovo** (`displays-wayland.c:526-529`). ⚠ Il rischio **non è la misura** — il modo su misura sopravvive alle sue riapplicazioni — è `enabled = FALSE` |
> | **LXQt** | **non ha niente di simile**: `lxqt-config-monitor` passa da KScreen, muore con `exit(1)`, e l'osservatore udev è dentro un ramo `if (isX11)` |
>
> ⚠ `[R]`, **non `[M]`**: né XFCE né LXQt sono installati sulle nostre macchine. La misura che
> chiude la domanda è se `xfsettingsd` ci spenga davvero l'output, e se un output presente
> **prima** del suo avvio conti come «nuovo» — se non conta, la cura è l'ordine di avvio.
| **Cinnamon** | 📖 **studiato il 9 agosto, ultimo della fila** — vedi [`STUDI.md` §cinnamon](STUDI.md#cinnamon) |

⛔ **Su Cinnamon tre cose non esistono a monte**: `RecordVirtual`, libei, e **gli appunti** — né la
via di GNOME né quella di wlroots. La fattibilità dipende da una misura sola, e la decisione
«dentro o fuori» si prende su quella, non sullo studio. (`DECISIONI.md` §7.13)

### 11.3 Il sistema attorno

| | |
|---|---|
| **init** | systemd |
| **distribuzioni** | rilevamento delle capacità e degradazione dichiarata; **Debian e Ubuntu** come riferimento |
| ⛔ **spegnimento, riavvio, sospensione, ibernazione** | ⭐ **tolti a tutti** — *deciso dall'utente il 15 agosto 2026, `DECISIONI.md` §4.7*. ⛔ **Non solo alla sessione remota**: nemmeno chi è fisicamente davanti alla macchina, perché spegnere è l'unico gesto che porta via **tutte** le sessioni insieme e chi lo compie non vede chi c'è collegato. ⭐ **Dentro il desktop remoto l'utente ha un solo gesto che finisce qualcosa: il logout** (§5.2-bis); quel che fa sul **proprio** PC è affar suo, e per noi è il filo che cade. ⚠ Resta possibile a **root**, e deve restare: la macchina va amministrata, e i client attaccati lo vengono a sapere con `SERVER_IN_CHIUSURA` (`RCP.md` §8.2 `0x0C`) |
| **GPU** | scelta per **id PCI** con una regola udev. ⚠ Negare il nodo lo nega a **tutta la sessione dell'utente**: chi usa l'altra scheda per altro va messo nel gruppo della regola |

### 11.4 L'accelerazione hardware

**La codifica passa dalla scheda, attraverso VA-API** — `libva` usata direttamente, senza strati
in mezzo: REMOTIX imposta i parametri, gestisce i buffer e scrive da sé le intestazioni del flusso.
La scala:

1. **sulla scheda**, con `libva`: **H.264** e **HEVC** — l'unica strada. Sulla copia zero anche la
   **conversione dei colori** si fa sulla scheda (VPP di VA-API); sulla strada «dalla memoria» i
   colori si convertono sul processore e i piani salgono sulla scheda, dove si codificano
2. ⛔ **Niente codifica sul processore** — *decisione dell'utente, 1 ottobre 2026* (`DECISIONI.md`
   §10.27): *«niente cpu senza scheda»*. Il ripiego in software (OpenH264, SVT-AV1) è **uscito** dal
   prodotto, dai pacchetti e dall'installatore. Senza una scheda capace di codificare:
   - il **server** lo dichiara all'avvio nel registro (*«QUESTO SERVER NON SA CODIFICARE VIDEO»*,
     con la ragione di ogni codec) e l'`ECCOMI` non offre codec: ogni `CIAO` finisce in
     `NIENTE_IN_COMUNE`, col motivo;
   - `remotix --prova-codifica` esce con **3** (*nessuna scheda sa codificare*), distinto da 0
     (la scheda codifica), 1 (si apre ma il fotogramma non esce) e 2 (errore d'uso);
   - l'**installatore** rifiuta già nel controllo preliminare, con la ragione: **RX-GPU-003**
     nessuna scheda · **RX-GPU-004** solo NVIDIA col driver proprietario **senza il suo driver
     Vulkan** (l'ICD `nvidia`: con quello la strada Vulkan Video la prende) · **RX-GPU-005**
     nessuna scheda Intel, AMD o NVIDIA (virtio, VMware, nouveau) · **RX-GPU-006** una scheda che su
     questa distribuzione non codifica né in VA-API né in Vulkan e non ha un driver da aggiungere
     (oggi AMD su Alma: la Mesa di RHEL è costruita senza H.264, in VA-API e in RADV). Il driver
     Vulkan della scheda AMD, dove quello della distribuzione codifica (Debian, Ubuntu, Arch), lo
     installa l'installatore (su Arch è solo un pacchetto facoltativo). Una scheda che codifica col driver di un deposito di
     terzi resta un avviso col consenso (D5). ⚠ Il controllo preliminare non apre la scheda: legge i
     driver VA e gli ICD Vulkan sul disco; la prova vera è `--prova-codifica` dopo l'installazione
3. ⛔ **Nessuna dipendenza GPL**: tutte le librerie del server sono permissive (MIT, BSD, Apache),
   condizione della licenza (`DECISIONI.md` §10.22)

⭐ La strada **Vulkan Video** (AMD, NVIDIA) è la fase 19 (`fasi/19-nvidia.md`), ✅ innestata il
1 ott 2026: si sceglie per capacità all'apertura di ogni codificatore (`h264_scheda`/`hevc_scheda`,
`src/codificatore.c`), Vulkan prima e VA-API dove Vulkan non c'è; `--codifica vulkan|vaapi` la forza
per le prove, e `--prova-codifica` dice quale ha codificato (`strada`). `[M]` 1 ott 2026 sul server:
Intel UHD 770 → `vaapi` (H.264 e HEVC), Radeon RX 6800 → `vulkan` (H.264 e HEVC).

⚠ Sul ferro di riferimento **nessuna delle due schede codifica AV1** `[M]` 9 agosto: il desiderato
a 10 bit passa da **HEVC Main10**, che tutt'e due codificano in hardware.

⚠ **AV1 in hardware non è nella scala** *(`STUDI.md` §web §8-bis, O2)*: in decodifica non porta
niente che HEVC non dia già, e chi lo volesse aggiungere deve misurare entrambi i lati. ⛔ E dalla
fase 19 AV1 non c'è nemmeno in software: è uscito col ripiego.

⛔ **Si codifica in BT.709, e l'HDR non si promette** `[S]` *(O3)*: BT.2020/PQ fa cadere il percorso
a zero copie nel browser, e quello a una copia converte con un risultato slavato. È una scelta del
**server**, non del client, e va scritta qui perché nessuno la prenda per una dimenticanza.

⚠ **E due parametri che il server deve emettere e che nessuno indovina** *(O12)*: la stringa di
livello per il traguardo è **5.1**, non 5.0, e oltre i 40 Mbit/s serve il **tier High**. Un livello
dichiarato troppo basso non dà un errore: **fa rifiutare la configurazione dal decodificatore**, e
il sintomo è «il browser non apre il flusso».

⛔ **E la parentesi «RDNA2 e Alder Lake lo decodificano soltanto» era sbagliata a metà**, corretta
lo stesso giorno con `vainfo` sui due nodi: la Radeon RX 6800 decodifica AV1 (`AV1Profile0`,
`VLD`), **l'Intel UHD 730 non espone alcun profilo AV1 — nemmeno in decodifica**. Il dettaglio
delle capacità delle due schede sta in `DECISIONI.md` §4.6.

### 11.4-bis Dove la scheda codifica: distribuzioni, schede, depositi

*Decisioni dell'utente del 1 ottobre 2026 (`DECISIONI.md` §10.27): la codifica è **sempre** sulla scheda; i
driver con i codec, quando una distribuzione li toglie per i brevetti, si chiedono all'amministratore (D5): *«il
problema delle licenze è di chi installa remotix, non del progetto»*. REMOTIX non distribuisce codec.*

| distribuzione | Intel | AMD | NVIDIA (driver proprietario) | desktop |
|---|---|---|---|---|
| Debian 13 | ✅ depositi ufficiali | ✅ depositi ufficiali | ⚠ Vulkan Video, non provata | i 4 |
| Ubuntu 26.04 | ✅ depositi ufficiali (universe) | ✅ depositi ufficiali | ⚠ Vulkan Video, non provata | i 4 |
| Fedora 44 | ✅ con **RPM Fusion** (nonfree) | ✅ con **RPM Fusion** (`mesa-va-drivers-freeworld`) | ⚠ Vulkan Video, non provata | i 4 |
| Red Hat / Alma / Rocky 10 | ✅ con **RPM Fusion EL** + **EPEL** | ⛔ **non supportata**: nessun deposito rimette la codifica AMD | ⚠ Vulkan Video, non provata | ⛔ **solo GNOME e KDE** |
| openSUSE Leap 16, Tumbleweed | ✅ depositi ufficiali | ✅ con **Packman** | ⚠ Vulkan Video, non provata | i 4 |
| Arch | ✅ depositi ufficiali | ✅ depositi ufficiali | ⚠ Vulkan Video, non provata | i 4 |

- La famiglia Red Hat si prova su **Alma**, che ne fa le veci (Red Hat è a pagamento).
- Un «no» al deposito dei driver **blocca** l'installazione (D5): senza, su quella macchina la scheda non codifica.
- ⚠ **NVIDIA**: la strada è scritta (Vulkan Video) ma nessuno l'ha vista funzionare su una NVIDIA vera — il
  laboratorio non ne ha. Resta «non provata» finché non si prova (macchina a noleggio o un utente con la scheda).
- Senza una scheda capace: REMOTIX non si installa (§11.4). Le macchine virtuali vanno solo con la scheda
  passata alla macchina (passthrough, vGPU).
- La tela è al massimo **4096×2304** (§6.1-bis): una finestra più grande riceve la tela ridotta.

### 11.5 I browser serviti, e perché vanno dichiarati

| browser | dove | codec | stato |
|---|---|---|---|
| Chrome (e i Blink: Edge…) | Linux, Windows | HEVC, se il dispositivo lo decodifica; altrimenti H.264 | ✅ supportato |
| Chrome | **Android** | HEVC o H.264 | ✅ supportato (`DECISIONI.md` §7.19) |
| Firefox | Linux | **H.264** (Firefox su Linux non decodifica HEVC) | ✅ supportato |
| Firefox | Windows | — | mai provato: né supportato né escluso |
| Firefox | **Android** | — | ⛔ **fuori dal progetto** (`DECISIONI.md` §7.18) |
| Safari | macOS, iOS | — | mai provato |


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

⛔ **E come la pagina viene servita è un vincolo di prodotto, non un dettaglio** *(`STUDI.md` §web §8-bis,
O11)*: va consegnata **isolata fra origini** — le due intestazioni che il browser pretende per dare
alla pagina i cronometri a piena risoluzione e la memoria condivisa. ⚠ Non è una taratura del banco:
**cambia come il server serve ogni risorsa della pagina**, e deciderlo dopo significa riscrivere il
modo in cui la pagina è confezionata.

⚠ **E le versioni contano più che sui desktop**: qui il pavimento non lo pone Debian, lo pone il
dispositivo dell'utente. Un telefono fermo a una versione vecchia di Chrome non ha WebCodecs, e
il sintomo va detto in una frase — non «non funziona».

> ### ⏳ A fine fase 3: i **mattoni** stanno su due motori, i **numeri** stanno su uno
>
> *13 agosto 2026, e va scritto qui perché la riga «si collauda su almeno due motori» non venga
> data per soddisfatta guardando il posto sbagliato.*
>
> | | |
> |---|---|
> | ✅ **i mattoni** | il comportamento del decodificatore al cambio di tela è `[M]` **su Chrome e su Firefox**, in tutt'e due i versi — 8 celle su 8, HEVC e AV1 (`RCP.md` §5.2) |
> | ⚠ **i numeri** | le misure di prestazione di allora erano **su Chrome 151 e basta**. ⛔ Dal 30 settembre 2026 non sono più una verifica del prodotto: *«eliminiamo i test di performance, sono troppo dipendenti dall'hardware»* — l'utente |

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
| ✅ **la licenza** | **codice chiuso, trial e versione full a pagamento** (`DECISIONI.md` §10.30, che supera §10.22) — resta il vincolo di §11.4: nessuna dipendenza GPL |
| 📖 **Cinnamon** | studiato, da misurare — §11.2 |
| `[?]` **il 4:4:4** | §3.1 |
| ✅ ~~la forma della limitazione dei tentativi PAM~~ | **chiusa il 9 agosto** e ⭐ **riaperta e richiusa dall'utente il 10**: non è una limitazione di frequenza, è un **ban** — tre tentativi, dodici ore (§4.2, `DECISIONI.md` §1.9) |
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

---

## 15. La licenza

*Scritto il **9 ottobre 2026**, su richiesta dell'utente: *«meglio creare un documento dove viene messo nero su
bianco la logica di funzionamento delle licenze; se ci dimentichiamo qualche particolare quel documento diventa
oro»*. ⭐ **Questo capitolo è il riferimento**: contiene solo le regole **in vigore**. Il perché, le date e le
scelte superate stanno in `DECISIONI.md` §10.30; come si costruisce, i passi e le ore in
`fasi/21-la-licenza.md`. ⛔ Se una decisione nuova cambia una regola, si corregge **qui**, nello stesso momento.
Il codice non c'è ancora: ogni riga è una decisione di prodotto.* 🔸 = **proposta tecnica** (di Claude o
*concordata con ChatGPT) **non ancora confermata dall'utente**: elenco in §15.13.*

### 15.1 I tre tipi di licenza

| tipo | utenti | durata | chi la ottiene |
|---|---|---|---|
| **trial** | illimitati | **14 giorni** | chiunque installi, una volta per macchina |
| **full** | illimitati | **1 anno**, rinnovo automatico | ⭐ **l'unica in vendita** |
| **gold** | illimitati | nessuna scadenza | ⛔ non in vendita: uso privato di chi vende, sue macchine e macchine di prova (le **4 scatole** e il server di prova: senza, i banchi si fermerebbero alla trial) |

- Ogni licenza vale per **una macchina**: un server fisico **oppure** una macchina virtuale.
- **Il programma non conta gli utenti** per nessuna licenza. Quanti utenti regge una macchina lo dice la tabella
  pubblica delle prestazioni, non la licenza.
- Una **full scaduta** si comporta come una **trial scaduta**: REMOTIX smette di funzionare.
- Gli **aggiornamenti** sono compresi finché la licenza è attiva.
- ⛔ **Un programma solo**: niente versione speciale senza controllo, nemmeno per la gold (un binario senza
  controllo, se esce, è la versione sbloccata per tutti). La gold passa dalla **stessa strada** del cliente ed è
  **revocabile**.
- Finché il pagamento non c'è, le **full si creano a mano** con lo strumento di chi vende.
- ⭐ **La gold è il caso semplice** (utente, 9 ott: *«i controlli sono ancora più ridotti … ma conserva il limite di
  una licenza per macchina»*):

  | | gold |
  |---|---|
  | scadenza, avvisi, rinnovo | **nessuno** |
  | una per macchina | **sì**: resta il controllo orario, che serve solo a questo e alla revoca |
  | se la rete manca | **14 giorni**, come le altre (utente, 9 ott) |
  | due copie attive | **avviso a chi vende con tutti i dettagli** (gli stessi dell'email della full, §15.8), e chi vende **disabilita una delle due** dallo strumento delle licenze; la copia tenuta riceve una chiave nuova. Nessuna pagina di scelta, nessuna fermata automatica |
  | revoca | da chi vende |

### 15.2 Le quattro parti

| parte | dove | che cosa fa |
|---|---|---|
| **il prodotto** | il server del cliente | attiva, controlla ogni ora, mostra avvisi e stati nella pagina, si ferma a licenza scaduta |
| **il servizio di licenze** | il VPS di chi vende (OVH, Debian 13), `https://remotix.nicfio.it/licenze/v1/` | registra attivazioni e trial, consegna i biglietti, scopre gli sdoppiamenti, manda le email, ospita la pagina di scelta e di recupero |
| **lo strumento di chi vende** | il computer di chi vende | crea full e gold, revoca, attiva una trial a mano, sblocca i limiti, guarda gli sdoppiamenti |
| **l'ingresso del pagamento** | il servizio | «rinnova» e «sospendi» una licenza; ⏳ il processore di pagamento non è scelto |

⛔ **Non esiste l'attivazione senza rete.** Il prodotto esce anche da un **proxy** aziendale.

### 15.3 L'attivazione

1. Chi compra riceve per email il **codice di licenza**: una stringa lunga da incollare. Indica **quale** licenza
   si è comprata.
2. Alla prima attivazione il prodotto crea la **chiave dell'installazione** (una coppia di chiavi; la parte
   segreta sta in un file leggibile solo da root e **non lascia mai** il server).
   🔸 Il codice ha **almeno 128 bit casuali** e il prodotto **non lo conserva** dopo l'attivazione.
3. Il servizio lega la licenza alla **chiave pubblica** dell'installazione e risponde con un **attestato
   firmato** (tipo, scadenza commerciale, fine della tolleranza, «valido fino a», il primo **biglietto**).
4. La **trial** si attiva senza codice: la lega l'**impronta dell'hardware** (§15.7).

### 15.4 Il controllo, ogni 60 minuti

- Ogni ora il prodotto chiede al servizio lo stato della licenza: **firma con la sua chiave** una sfida del
  servizio e presenta il **biglietto** dell'ultima volta.
- Il **biglietto** vale **una volta sola**: il servizio lo consuma e ne consegna uno nuovo insieme all'attestato.
  ⇒ Due copie della stessa installazione (un clone, un backup ripristinato) partono con lo stesso biglietto:
  una va avanti, l'altra resta indietro e lo **sdoppiamento è scoperto** (§15.8).
- ⛔ **Un guasto non fa mai un falso clone**: il prodotto scrive la richiesta su disco **prima** di spedirla; se
  la risposta non arriva la rispedisce **identica**, e il servizio ridà **la stessa risposta**.
- Solo il servizio REMOTIX tocca lo stato della licenza; «controlla ora» passa da lui.
- **L'orologio**: il prodotto ricorda l'ora più recente vista (sua e del servizio); se l'orologio della macchina
  torna indietro vale la più recente, così spostarlo non allunga una licenza.
- La licenza è legata alla **storia dell'installazione**, non al ferro: chi **spegne il vecchio server** e passa
  a uno nuovo (copiando lo stato) continua senza fare niente.

### 15.5 Quando il servizio non risponde

- Il prodotto continua a funzionare per **14 giorni dall'ultimo controllo riuscito**.
- L'amministratore viene avvisato **al primo controllo fallito**, poi **una volta al giorno** (registro e pagina
  d'accesso), con i giorni che restano.
- ⛔ Nessun attestato vale più di **14 giorni**, **gold compresa** (utente, 9 ott): un valore solo per tutte.

### 15.6 Scadenza, rinnovo, avvisi

- **Rinnovo fallito** della full (carta scaduta o rifiutata): **14 giorni** di tolleranza dopo la scadenza.
- **«La fine»** è il momento in cui REMOTIX si ferma davvero: per la trial il 14° giorno; per la full la fine
  dei 14 giorni di tolleranza dopo la scadenza commerciale (o dopo l'ultimo controllo riuscito, se la rete manca).
- **Gli avvisi**:

  | quando | chi | dove |
  |---|---|---|
  | **7 giorni prima della scadenza commerciale** (full) · **3 giorni prima della fine** (trial) | l'amministratore | registro e pagina d'accesso |
  | **ultimi 3 giorni prima della fine** | tutti gli utenti collegati | **3 messaggi nelle 24 ore** nella pagina di REMOTIX, sopra il desktop, con «ho letto»; insistono ma **non bloccano mai** (il modello è RootSpeak) |

- **Alla fine**:
  - ⭐ si ferma **solo REMOTIX**; ⛔ **mai** l'accesso al server (ssh, login locale, PAM del sistema restano intatti);
  - i **collegamenti** si chiudono, i **desktop restano vivi** col lavoro dentro;
  - al ricollegamento compare la finestra della licenza col campo del codice;
  - dopo il rinnovo ognuno rientra e trova il suo desktop com'era.

### 15.7 La trial

- **14 giorni, utenti illimitati**, legata all'**impronta dell'hardware**, **senza email**.
- **L'impronta** la calcola il prodotto da **più parti dell'hardware**: UUID e seriale della scheda madre, seriale
  del disco di sistema, indirizzo della scheda di rete. Le **scritte di fabbrica** («To be filled by O.E.M.»,
  «Not Specified», tutti zeri) **si scartano** prima del calcolo. Al servizio arrivano solo impronte cifrate.
- **Una trial per impronta**. Reinstallare durante la trial ridà **la stessa data di fine**; a trial scaduta non
  se ne ottiene un'altra.
- **Niente doppioni**: due copie attive della stessa trial ⇒ la trial si **disabilita**.
- Se non resta niente di distintivo, la trial **non parte da sola**: *«questa macchina non può avviare la prova
  automatica: scrivici»*, e chi vende la attiva a mano.
- ⚠ Dichiarato: una macchina virtuale **nuova** in cloud ha un'impronta nuova, quindi una trial nuova.

### 15.8 La full: due copie attive, sceglie il cliente

1. **Lo sdoppiamento** si scopre al controllo orario (§15.4), quindi entro un'ora.
2. Ogni copia riceve un **nome breve** («copia A · 4F7K»), mostrato anche sulla sua pagina d'accesso.
3. Il servizio manda **subito un'email all'acquirente** (e un avviso a chi vende) con, per ogni copia: nome breve;
   giorno e ora della scoperta e dell'ultimo contatto; **IP pubblico** con fornitore, paese e città approssimata
   (da **RDAP**); **IP interni** e **nome della macchina**; **descrizione dell'hardware** (scheda madre,
   processore, memoria, dischi). E un **link alla pagina di scelta**.
4. La pagina di scelta **mostra**; la scelta si **conferma con un pulsante** (un link aperto da un filtro di posta
   non sceglie niente). 🔸 Il link vale una volta e scade.
5. **72 ore** per scegliere, **promemoria dopo 24**.
6. **Scelta fatta**: la copia tenuta riceve una **chiave nuova**, l'altra si ferma (i suoi desktop restano vivi
   fino allo spegnimento).
7. **Nessuna scelta in 72 ore**: resta la copia col **biglietto più recente**, l'altra si ferma. Una scelta
   arrivata **dopo** vale comunque.
8. ⛔ **La licenza non si invalida mai da sola.**
9. **Uno scambio ogni 30 giorni**; chi vende può sbloccarlo a mano. **3 sdoppiamenti in 90 giorni** sulla stessa
   licenza ⇒ la licenza va a chi vende, che guarda e decide se revocarla.
10. ⛔ **L'impronta descrive, non decide**: a legare la full restano chiave e biglietto. Cambiare un disco o una
    scheda di rete non fa di un cliente una macchina nuova.

### 15.9 Spostamento e recupero

- **Spostamento a freddo**: si spegne il vecchio server, lo stato passa al nuovo ⇒ continua da solo (§15.4).
- **Spostamento volontario** dalla pagina d'accesso: la vecchia installazione **firma il rilascio**, la nuova si
  attiva.
- **Recupero** (backup ripristinato, copia rimasta indietro, server morto): l'amministratore preme **«Recupera»**,
  incolla il **codice di licenza**, e conferma dall'**email dell'acquirente**. Il prodotto crea una **chiave
  nuova** e la storia riparte da lì. 🔸 Uno ogni 30 giorni (chi vende può sbloccare); 🔸 acquirente e venditore
  avvisati a recupero fatto.
  ⛔ Non esiste un pulsante «adotta» solo locale: chi clona lo premerebbe.
- La **copia rimasta indietro** non viene allungata: lavora fino al suo «valido fino a» e mostra all'amministratore
  un messaggio **neutro** (*«questa installazione risulta una copia più vecchia, forse un backup ripristinato»*).
  Chiede il suo stato **ogni ora**, senza consumare biglietti.
- La pagina del recupero si raggiunge **anche a licenza scaduta**.

### 15.10 La pagina d'accesso

| stato | prima delle credenziali | dopo utente e parola d'ordine giuste |
|---|---|---|
| **trial** | «Trial version — restano N giorni» e il collegamento «Hai un codice di licenza?» | si entra |
| **licenza valida** | niente | si entra; collegamento piccolo «Cambia licenza» |
| **scaduta** | niente (chi non ha un account non scopre lo stato) | **campo del codice già aperto**, «Recupera», «Acquista» |

In più, quando servono: l'avviso dei giorni che restano, il nome breve della copia, il messaggio della copia
rimasta indietro.

### 15.11 Le chiavi di chi vende, e la rete

- Una **chiave madre fuori linea** (mai sul VPS) autorizza la **chiave del VPS**, che firma **solo gli attestati**.
- Indirizzi del servizio, chiavi valide e revoche stanno in un **elenco firmato dalla chiave madre**. Il prodotto
  ha dentro **due indirizzi** di partenza. ⇒ Una chiave del VPS rubata si revoca senza ricompilare il prodotto;
  un **dominio nuovo** non obbliga i clienti ad aggiornare.
- HTTPS con i certificati del sistema, 🔸 **niente pinning** (i proxy aziendali devono funzionare); l'autenticità
  la danno le firme dei messaggi, in un **formato binario fisso e firmato**.
- Il servizio: operazioni a transazione, **copie cifrate fuori dal VPS ogni giorno**, registro di attivazioni,
  recuperi e sblocchi. Se il VPS torna a un salvataggio vecchio, si rimette in pari **solo** con prove firmate da
  lui stesso, mai con numeri dichiarati dal cliente.
- 🔸 **Le email** partono dal VPS (Postfix solo in uscita, SPF/DKIM/DMARC). ⚠ Condizione: OVH deve lasciare aperta la
  porta 25 e permettere il nome inverso; altrimenti serve un inoltro (decisione dell'utente).

### 15.12 La riservatezza

- **Che cosa arriva al servizio**: la chiave pubblica dell'installazione, l'impronta cifrata, la descrizione
  dell'hardware, gli IP interni, il nome della macchina e l'IP da cui si collega. 🔸 Il servizio tiene **solo
  l'ultima** di ogni voce, salvo gli sdoppiamenti.
- **Quanto si tengono** (tetti, non minimi):

  | dati | per quanto |
  |---|---|
  | email dell'acquirente, licenze, registro delle attivazioni | **2 anni** dalla fine del rapporto |
  | impronte delle trial | **2 anni** dalla trial |
  | dati di uno sdoppiamento (IP, RDAP, nomi, hardware) | **6 mesi** dalla scelta, poi solo «sdoppiamento del giorno X, risolto così» |

- I dati di una copia finiscono nell'email dell'acquirente **anche quando la copia è di altri**: si fa per
  prevenire le frodi e va scritto nell'**informativa**, da far controllare a un legale prima di vendere.

### 15.13 Che cosa NON c'è

- ⛔ attivazione senza rete · conteggio degli utenti · TPM · integrazioni coi cloud (AWS, Google, Azure) ·
  impronta che decide della full · invalidazione automatica di una licenza · blocco dell'accesso al server.
- ⏳ **Sospesi**: il processore di pagamento e il **contratto di vendita** della full (si decidono insieme).
- ⚠ **Il contratto della trial**: §10.30 indicava la PolyForm Free Trial 1.0.0, che prevede **32 giorni**; la trial
  ora dura **14**. Da decidere insieme al contratto della full.
- ❓ **Da decidere con l'utente** (verifica del 9 ott):
  1. che cosa vede chi usa una licenza **sospesa** (dal pagamento) o **revocata** (da chi vende): proposta del piano,
     la finestra della licenza con la frase della sospensione, come una scaduta;
  2. il **primo avvio senza rete**: proposta del piano, la pagina dice «il server non ha ancora potuto attivare la
     licenza: serve l'accesso a internet»;
  3. le righe 🔸: recupero uno ogni 30 giorni e avviso a recupero fatto; email dal
     VPS; link della scelta usabile una volta; codice da 128 bit non conservato; niente pinning; solo l'ultima
     voce tenuta dal servizio.
