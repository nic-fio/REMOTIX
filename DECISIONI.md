# DECISIONI — il registro di quel che è stato deciso, e da chi

*Aperto l'8 agosto 2026, al primo giorno di REMOTIX_V2.*

Questo documento non spiega e non convince: **registra**. A che serve, in una riga: una
decisione presa a voce e non scritta è una decisione che fra due settimane nessuno sa più
se era stata presa, e che il primo dubbio riapre da capo.

Ogni voce dice **che cosa**, **quando**, **perché** — e soprattutto **con che grado di
certezza**, perché la differenza fra «l'utente ha detto sì» e «è una conseguenza che ho
tratto io» è precisamente la differenza che `LEZIONI.md` §2.3-quater dice di non perdere.

| Marca | Significato |
|---|---|
| ✅ **Deciso** | l'utente ha detto sì, esplicitamente. Non si riapre senza una misura che la smentisca |
| 🔸 **Derivato** | conseguenza logica di una decisione ✅, scritta nei documenti ma mai pronunciata. Se sbaglio, si corregge senza discussione |
| ❓ **Aperto** | domanda posta, risposta non ancora data. **Non è una decisione**: è un buco che qualcuno deve chiudere |

E le marche delle *ragioni* restano quelle di `CODER.md` §5: `[M]` misurato, `[R]` letto nel
codice, `[S]` letto in una specifica, `[?]` ipotizzato.

---

## 0. Il principio che ha prodotto le altre

### 0.1 ✅ Si dipende dal compositore, non dal suo contorno

*8 agosto 2026. «Voglio evitare di smettere di correre dietro ai compositor e cominciare a
dover inseguire i display manager».*

Sta in cima perché non è una decisione fra le altre: è il criterio con cui se ne prendono
diverse, e almeno tre di quelle scritte qui sotto discendono da questa.

| | |
|---|---|
| **si insegue** | il **compositore**, perché solo lui consegna i fotogrammi e accetta l'input. `mutter.c` e `kwin.c` esistono per questo e continueranno a esistere |
| **non si insegue** | il **contorno**: blocca-schermo, demoni di inattività, gestori dell'energia, display manager. Fanno la stessa cosa in quattro modi, con quattro configurazioni che si riscrivono da sole |

**La prova, prima di appoggiarsi a un meccanismo:** *quante implementazioni diverse dovrei
inseguire, e quanto mi costa farla da me?* Quattro divergenti e un costo piccolo ⇒ si fa da
noi, una volta sola.

⚠ **Non è un permesso di riscrivere.** `logind`, PAM, PipeWire, `libei`, `xkbcommon`, QUIC:
uno solo ciascuno, uguale ovunque. Lì vale `CODER.md` §4.1 senza sconti, e scrivere il nostro
sarebbe il difetto che quella regola vieta.

**Dove ha già deciso:** §4.3 (il blocco è nostro invece di quello dei desktop), §5.1
(ridimensionare non tocca il compositore), e in negativo §1.1 — smettere di inseguire i client
altrui era lo stesso ragionamento applicato al filo.

*Scritta anche in `CODER.md` §4.1-bis, con la verifica corrispondente in `REVIEWER.md` E11 —
le due devono restare in coppia, altrimenti è una regola non verificata.*

---

### 0.2 ✅ Sviluppo agentico, con revisione avversariale a tre momenti

*9 agosto 2026. «Ricorda inoltre il metodo di lavoro: sviluppo agentico e review avversariali».*

Il lavoro è fatto da due tipi di agenti — `CODER.md` e `REVIEWER.md` — e il **quando** interviene
il revisore sta in `PIANO.md` §0.4: sul **banco** prima che il prodotto esista, sul **codice**
prima che venga misurato, sul **documento di fase** prima della chiusura.

⭐ **E qui la revisione ha un mestiere in più che in un progetto normale.** Buttando RDP abbiamo
perso l'arbitro esterno: in v1 `mstsc` protestava gratis quando sbagliavamo a capire la specifica.
Ora client e server sono nostri, e **due programmi scritti dalla stessa mano che vanno d'accordo
non confermano niente**. Le tre cose che sostituiscono quell'arbitro sono `RCP.md` (scritto), il
validatore del filo (meccanico) e **la revisione avversariale** — che è l'unica delle tre capace
di accorgersi che i due lati condividono lo **stesso** fraintendimento.

Le quattro pratiche che rendono la postura avversariale una cosa concreta invece che un tono: il
revisore riceve il codice e la specifica **ma non il ragionamento** di chi l'ha scritto, che
altrimenti àncora; si prova a **rompere**, costruendo l'ingresso che violerebbe l'invariante; un
rilievo si chiude con **una misura**, non con una discussione; e una revisione verde è **«non ho
trovato niente»**, mai «è giusto».

### 0.3 ✅ Il client Linux prima di quello Android — per il costo delle prove

*9 agosto 2026. «Il server lo si sviluppa ovviamente avendo in mente i 2 client, ma resta il
problema dei test: per android è molto più complicato, mentre lo è meno per linux».*

Il binario Android si sposta **da dopo la fase 4 a dopo la fase 9**, e può poi procedere in
parallelo alle fasi dei desktop nuovi (11-12), che sono lavoro di server e non toccano il filo.

⛔ **Ma lo spostamento porta via una difesa**, e va compensata. Android non stava alla fase 4 per
fare prima: era il **secondo lettore del protocollo**, l'unica cosa capace di accorgersi che
server e client condividono lo *stesso* fraintendimento (§0.2). Senza, tutto ciò che si costruisce
fra la 4 e la 12 poggerebbe su un protocollo validato da **una sola** implementazione.

🔸 **Le due compensazioni:**

1. **il cliente di prova**, aggiunto alla fase 1 — poche centinaia di righe, **in un linguaggio
   diverso dal server**, scritto leggendo `RCP.md` e **mai** il C. Fa lo stesso mestiere a un
   decimo del costo. Il validatore dice «questo byte non è conforme»; il cliente di prova dice
   **«voi due vi siete capiti su una cosa che la specifica non dice»**;
2. **la sonda Android**, nella fase 2 — ~50 righe che danno un file HEVC Main10 a MediaCodec e
   dicono se il telefono lo decodifica **in hardware**. È l'unica incognita di Android che non può
   aspettare, perché è il muro contro cui è morto v1. E si dichiara riuscita solo con la prova che
   sia hardware davvero: «ha istanziato un decoder ⇒ è in hardware» è la forma d'errore **E1**.

⚠ **Il rischio residuo, dichiarato e accettato**: restano cose che solo Android può rivelare e che
nessun lettore sostituisce — MediaCodec sotto carico, il tocco vero sotto le dita, l'IME, la
batteria, la rete che cambia in tasca. Quelle arrivano tardi.

> ⛔ **Superata il 9 agosto 2026 da §1.6**: non esistono più due client, quindi non esiste più
> l'ordine fra loro. ⭐ **Ma le due compensazioni sopravvivono, e una vale di più di prima**:
>
> - **il cliente di prova** resta, ed è **più necessario**, non meno. Prima era il secondo lettore
>   accanto a due implementazioni; adesso il client è **uno solo**, quindi è l'**unica** cosa
>   scritta dalla specifica invece che dal codice;
> - **la sonda** resta e cambia bersaglio: da «il telefono decodifica HEVC in hardware?» a
>   **«il browser del telefono lo decodifica in hardware?»** — stessa domanda, uno strato più in
>   là, e **senza APK**. Ci si aggiungono le altre due incognite del browser (§1.7 e §1.6).
>
> ⚠ E il rischio residuo qui sopra **non decade, si sposta**: MediaCodec sotto carico, l'IME, la
> batteria e la rete in tasca restano cose che solo il telefono vero rivela. Cambia che ora le
> rivela **aprendo una pagina**, che costa mezza giornata invece di una fase.

---

## 1. Il protocollo

### 1.1 ✅ RDP muore. Il protocollo è nostro.

*8 agosto 2026. «Windows e tutto quello lo riguarda muore».*

La riga `== NO WINDOWS ==` non è una nota a margine: è la leva che toglie i tre muri contro
cui v1 si è fermato, e che erano tutti e tre di RDP e non del problema — il tetto a H.264
(`v1/documenti/SPECIFICA.md` §5.1), il client Android che decodificava in software, e il
colore pieno irraggiungibile.

**Il prezzo, accettato:** il protocollo va progettato oltre che scritto, e i client vanno
scritti da zero — quello Android è un progetto a sé, non una funzionalità.

**Che cosa decade con RDP:** EGFX, `MapSurfaceToOutput`, RemoteFX Progressive, AVC444, NLA e
CredSSP, MS-RDPEDISP, `ERRINFO_*`, FreeRDP 3 come vincolo, la matrice dei tre client altrui,
e `v1/documenti/REFERENCE.md` quasi per intero.

### 1.2 ✅ Il protocollo si chiama RCP — *Remotix Control Protocol*

*8 agosto 2026, scelto dall'utente.*

```
librcp.so
rcp_frame_t · rcp_connect() · rcp_session_t
stretta di mano:  RCP/1
```

Due nomi provvisori l'hanno preceduto nello stesso pomeriggio e sono stati scartati: **FILO**
(«proprio non si può sentire») e **RXP**. Sono citati qui solo perché chi ritrova quei nomi in
un appunto sappia che si parlava di questo, e non di altro.

⚠ **Una collisione minore, da sapere prima di battezzare i binari**: `rcp` è il nome di un
comando Unix storico — la copia remota della famiglia `rsh` — oggi quasi ovunque disinstallato
e mai attivo di suo. Non tocca né il protocollo né la libreria; riguarda solo l'eventuale
comando a riga di comando, che conviene chiamare `remotix` e non `rcp`.

⭐ **E il nome dice una cosa giusta**: *Control*, non *Display*. Il protocollo non porta solo
pixel — porta input, appunti, geometria, congedo e stato della sessione, e il video è uno dei
suoi canali. È la differenza fra RCP e ciò che RDP faceva credere di essere.

### 1.3 ✅ La fiducia nel server: ricordata in silenzio, mai confermata a mano

*9 agosto 2026. «Se inserisco i dati fondamentali (ip, porta, userid e password) so che quel
server è mio. La sicurezza va bene, ma qui non stiamo costruendo un sistema basato su standard
militari».*

**Nessun confronto di impronte, nessuna autorità di certificazione, nessun dominio.** L'utente
digita indirizzo, porta, utente e password, e basta.

Il certificato serve comunque — QUIC pretende TLS, non esiste l'opzione «senza» — quindi il
server se ne genera uno autofirmato all'installazione. Il client, al primo collegamento, lo
**accetta in silenzio e se lo ricorda**; dalle volte successive, se cambia, avvisa. È quel che
fa SSH, e non si vede finché non serve: costa **zero interazione** e copre tutti i collegamenti
tranne il primo.

⚠ **La precisazione che è stata fatta e respinta, tenuta perché la decisione si capisca:** il
rischio non è digitare l'indirizzo sbagliato, è che qualcuno intercetti la connessione verso
quello giusto. La prima connessione resta scoperta. **Il rischio è stato valutato e accettato**
dall'utente per lo scenario previsto — server proprio, rete propria o VPN.

🔸 **Due conseguenze che non costano niente e non si vedono:**

1. **la password non parte prima** che il server abbia dimostrato di essere quello di ieri. È
   l'invariante I3 — la guardia parte da negato — applicata all'ordine della stretta di mano.
   Con RDP le credenziali partono presto e l'avviso sul certificato arriva quando ormai le hai
   date; qui è solo questione di cosa si scrive per primo sul filo;
2. **un certificato vero, se c'è, si usa e vale di più** — roba dell'amministratore, non
   dell'utente, e non aggiunge un passaggio a nessuno.

⚠ E una trappola già pagata da v1, da non ripetere: *«un certificato TLS condiviso uccideva il
server alla seconda connessione; una prova a connessione singola resta verde per sempre»*
(`LEZIONI.md` §2.1). Il banco della stretta di mano si fa **con due connessioni**, non con una.

> ⚠ **Riletta il 9 agosto 2026, dopo §1.6.** Il meccanismo descritto qui — accetta in silenzio la
> prima volta, ricorda, avvisa se cambia — **resta esatto e non lo scriviamo più noi: lo fa il
> browser**. Quel che cambia è il prezzo: l'accettazione della prima volta **non è silenziosa**,
> è un avviso con un clic (§1.7). E il *«zero interazione»* promesso qui vale ancora solo per chi
> mette un certificato vero, cioè per il caso che questa voce chiamava già «roba
> dell'amministratore».

### 1.4 🔸 La sessione non conosce il codec: lo negozia la connessione

Discende da 1.1 e da §4. Il palco produce fotogrammi; ogni connessione ci attacca il proprio
codificatore con le capacità del **suo** client. Se il codec fosse una proprietà della
sessione, riprendere da un dispositivo diverso — telefono la mattina, portatile il pomeriggio
— richiederebbe di rifare la sessione, che è esattamente ciò che la persistenza deve evitare.

### 1.5 🔸 Le chiusure di RCP/1 — ventisei buchi tappati prima della prima riga di codice

*9 agosto 2026, all'apertura della fase 1. Sono conseguenze scritte da me leggendo `RCP.md` con una
domanda sola — **due persone che lo leggono da sole scrivono lo stesso byte?** — e la risposta era
no. Tutte 🔸: si correggono senza discussione.*

⛔ **Il censimento in una riga**: dei **ventidue** messaggi che il protocollo aveva alla prima
stesura, **due** erano definiti byte per byte — il fotogramma e il datagram audio. Gli altri venti
avevano un nome e una descrizione a parole. Il canale meno specificato era proprio quello della
**stretta di mano**, cioè quello che la fase 1 deve scrivere. Il dettaglio sta in `RCP.md` §0-bis;
qui stanno solo le scelte che avrebbero potuto essere prese altrimenti.

⚠ **E il totale di oggi non è più ventidue: è ventisei**, tutti definiti byte per byte (`RCP.md`
§0-bis, casella corretta dal rilievo **R1.29**). I quattro aggiunti il 9 agosto sono
`RICHIEDI_CHIAVE` e `TELA` (§5.2, §7.1) e ⭐ **`BANCO_MARCA` e `BANCO_ESITO`** (§7.5, la notte del
9). *La distinzione fra i due totali è del 10 agosto 2026, rilievo **R11.13**: questa riga diceva
«dei ventidue messaggi del protocollo» al presente, e un lettore che verificasse la completezza
contando da qui — come R1.29 dichiara di aver fatto su §0-bis — ne trovava quattro in meno di
quelli che esistono.*

⚠ **E il conto del titolo, dichiarato perché non se ne inventi un altro** *(notte del 10 agosto
2026)*: le righe numerate qui sotto sono **ventisei**, di cui la **8** è *caduta* — le chiusure in
vigore sono **venticinque**. ⛔ E il ventisei del titolo **non è** il ventisei dei messaggi del
paragrafo qui sopra: sono due conteggi diversi che oggi danno lo stesso numero, e un numero senza
il suo denominatore è quel che `LEZIONI.md` §1.9 punto 4 vieta.

| # | La scelta | Perché così | Dove |
|---|---|---|---|
| 1 | **la porta è 7447**, e sono ⛔ **due ascoltatori con lo stesso numero**: **UDP** per HTTP/3 e WebTransport, **TCP** per il primo caricamento della pagina | libera in `/etc/services` di Trixie `[M]`. `[?]` IANA non verificata. ⚠ *Questa riga diceva «la porta è **UDP** 7447» e basta, mentre `RCP.md` §2.4 dichiara i due ascoltatori dal 9 agosto: chi implementava di qui apriva il solo UDP, e **la pagina non si sarebbe servita affatto** — cioè il sintomo «`https://192.168.0.2:7447` non risponde», che non nomina né la porta né il trasporto. Allineata la notte del 10 agosto 2026 dalla **rilettura di tutte e ventisei le righe** che `R11-documenti.md` §C punto 6 prescrive — `[R]` **N1**, e non era fra i rilievi di R11* | `RCP.md` §2.4 |
| 2 | le **stringhe** sono `u16` di lunghezza più UTF-8, senza terminatore | il terminatore invita a passare la stringa a `printf` senza copiarla, e un byte nullo in mezzo diventa un troncamento silenzioso | §6.0 |
| 3 | **il byte alto del `tipo` dice il canale** di uno stream | chi riceve uno stream unidirezionale deve sapere che cosa c'è dentro **prima** di leggerlo, e non era scritto da nessuna parte | §2.5 |
| 4 | **niente 0-RTT** | i dati 0-RTT si ripetono, e il secondo messaggio è `CREDENZIALI`. Il guadagno è un giro di rete su una sessione che dura ore | §2.3 |
| 5 | `disable_active_migration` **non si manda** | dichiararla spegne in silenzio la ragione per cui QUIC è stato scelto | §2.3 |
| 6 | ⛔ ~~credito degli stream ≥ 256~~ → **il server ne concede ≥ 16 al client** | *corretta il 9 agosto sera (**R1.14**): il 256 era un parametro che pretendevamo dal client, e **con un browser lo sceglie lui**. Chi implementava leggendo questa riga scriveva 256 dove `RCP.md` dice 16* | §2.3 |
| 7 | ⛔ ~~l'impronta si calcola sulla chiave pubblica~~ → **sul certificato in forma DER** | *corretta il 9 agosto sera (**R1.14**): `serverCertificateHashes` confronta l'impronta **del certificato**. Chi pubblicava quella della chiave otteneva un confronto che **non combacia mai**, con il sintomo «WebTransport non si connette» e nessun errore che nomini l'impronta. ⚠ E la ragione che ci stava accanto — «un certificato riemesso con la stessa chiave non deve far scattare l'avviso» — **è decaduta**: con l'impronta pubblicata dalla pagina, ogni riemissione la cambia comunque* | §4.1-bis |
| 8 | ⛔ ~~il client spegne i controlli X.509 di serie~~ | *caduta il 9 agosto sera (**R1.14**): il client è una pagina, e non ha nessun controllo X.509 da spegnere. Era un resto della stesura con un client nostro, rimasto nel documento che dice che cosa è stato deciso* | — |
| 9 | **`RESPINTO` è il congedo dell'autenticazione**, e ⛔ **il server** non ne manda un altro | §4.4 e §8.2 si sovrapponevano: due implementazioni potevano indovinare diverso, o **uguale perché scritte dalla stessa mano**. ⚠ *Diceva «e non ne segue un altro», senza dire di chi: il divieto è del **server**, e vale per `CONGEDO`. **Al client dopo `RESPINTO` resta una cosa che può dire, ed è proprio `CONGEDO`** — il divieto di §4.4 è di **riprovare**, non di congedarsi (chiarimento del 10 agosto, banco **B11**, che aveva messo un rosso sulla pagina mentre faceva quel che §8.1 le impone). Chi implementava la pagina leggendo questa riga taceva, e B11 pretende il congedo **una volta per motore**. Allineata la notte del 10 agosto 2026 dalla stessa rilettura — `[R]` **N2**, e non era fra i rilievi di R11* | §4.4 |
| 10 | **un solo tentativo di credenziali per connessione** | il limitatore conta una cosa sola, e non serve una macchina a stati per i tentativi ripetuti | §4.4 |
| 11 | ⛔ ~~**la limitazione: 5 in 5 minuti, poi attesa da 30 s che raddoppia fino a 15 min**, con due contatori~~ → **SOSTITUITA il 10 agosto 2026 da §1.9**, che è ✅ dell'utente: tre autenticazioni fallite e l'indirizzo è bannato **12 ore**, con **un** contatore solo e senza quello per nome utente. ⭐ **Sopravvive intatto** il resto della riga: **il secondo fisso di ritardo su ogni risposta, anche quando è «ammesso»** | il secondo fisso chiude la `[?]` di `SPECIFICHE.md` §4.2 e toglie il **tempismo** come canale: senza, la distinzione fra «utente inesistente» e «password sbagliata» che §4.4 vieta di scrivere la si legge col cronometro. ⚠ E su quel secondo c'è una misura che non torna: B8 dà **2636 ms** di mediana, cioè a governare i tempi è **PAM** — `[?]` aperta, e il ban **non** la chiude | §4.4-bis, §1.9 |
| 12 | **la tela DEVE avere lati pari**, fra 320×240 e 7680×4320 | una misura dispari la arrotonda **il codificatore, in silenzio**: due misure sotto la stessa etichetta, cioè la forma d'errore **E2** | §4.5 |
| 13 | **tre tetti di tempo sulla stretta di mano** (5 s, 60 s, 10 s) | una connessione ferma a metà tiene un posto; e i 30 s di QUIC misurano il **silenzio della rete**, non un client che non fa il suo mestiere | §4.6 |
| 14 | ⛔ **i fotogrammi chiave**: `tipo` `0x0301`/`0x0302` e il messaggio `RICHIEDI_CHIAVE` | **non era una lacuna, era un difetto di disegno**: §5.1 concede di abbandonare un fotogramma, e il video è compresso con predizione — abbandonarne uno lascia il decodificatore rotto finché non arriva una chiave, e non c'era modo né di dirlo né di chiederla. Costa **zero byte**: entra nei valori di un campo che c'era già | §5.2 |
| 15 | l'audio è **48 kHz, 2 canali**; ⛔ **i blocchi sono da 20 ms per Opus e da 5 ms per il PCM**, e il PCM è **s16 little-endian** | «Opus, con PCM come base» non è un formato. E l'endianness del carico utile è l'unica eccezione all'ordine di rete: dichiararla è ciò che impedisce a due implementazioni di divergere in silenzio. ⛔ *Questa riga diceva «blocchi da 20 ms» per **l'audio** e riservava al PCM il solo endianness: è la lettura che il rilievo **R1.1** — il più grave della revisione del 9 agosto — dichiara **letale**, perché 20 ms di PCM fanno 1920 campioni, 3840 byte, più 12 = **3852**, e un datagram QUIC non è frammentabile su un percorso da ~1200 byte. **L'audio PCM non sarebbe partito mai, su nessuna rete** — e il PCM è il controllo positivo di Opus. `RCP.md` §5.3 era stato corretto la sera del 9; questa riga no. Allineata il 10 agosto 2026, rilievo **R11.12*** | §5.3 |
| 16 | gli appunti si fermano a **1 000 000 byte**, e oltre **non si annunciano** | troncare un testo e incollarlo in un terminale è peggio che non averlo | §5.4 |
| 17 | il cursore si ferma a **256×256**, e ⛔ **`larghezza = 0` *e* `altezza = 0` insieme** vogliono dire nascosto — una sola delle due a zero è `ERRORE_PROTOCOLLO`, e in quel caso il **punto attivo DEVE valere `0,0`** | serviva un modo di dire «nessun cursore» che non fosse un messaggio in meno. ⚠ *Questa riga diceva «`larghezza = 0` vuol dire nascosto», senza l'altezza: chi implementava di qui mandava `larghezza=0, altezza=16` e §5.5 gliela dichiarava `ERRORE_PROTOCOLLO`. Allineata il 10 agosto 2026, rilievo **R11.11**, insieme all'eccezione sul punto attivo che §5.5 non aveva* | §5.5, §7.2 |
| 18 | **un fotogramma non supera 16 MiB**, e la lunghezza si controlla **prima di allocare** | senza tetto, sei byte scritti a mano si portano via la memoria del server | §6.1, §6.2 |
| 19 | i fotogrammi **possono arrivare fuori ordine**, e il client scarta i vecchi con aritmetica **modulo 2³²** | gli stream sono indipendenti: è una conseguenza di §5.1 che nessuno aveva scritto. A 60 al secondo il contatore gira in due anni, e una sessione può durare di più | §6.2 |
| 20 | **i codici di tasti e pulsanti sono quelli di evdev**, la rotella in **unità da 120** | è quel che vuole `libei`, cioè l'unico modo che abbiamo di iniettare input. Ogni altra convenzione aggiunge una tabella di traduzione che sbaglia in silenzio. ⚠ *Qui c'era anche «e in v1 quella tabella è costata il banco della rotella (`LEZIONI.md` §2.3)», ed è **falso**: §2.3 racconta che il banco della rotella cercava `asse dy=-10` mentre il registro scriveva `asse dx=0 dy=-10` — **rosso, col codice corretto**. È una stringa cercata male, non una conversione col segno sbagliato. `RCP.md` §7.3 era stato corretto la notte del 9 agosto (rilievo **R4.15**); questa riga no, ed è quella che il progetto designa come fonte. Allineata il 10 agosto 2026, rilievo **R11.14** — e conta perché citando la lezione sbagliata **la si perde nel punto in cui si applicherebbe**, cioè S7, che è ancora da misurare* | §7.3 |
| 21 | l'`id` dell'input è **uno solo per tutto il canale**, non uno per tipo | è quello che torna nel campo `input` del fotogramma: con contatori separati non tornerebbe niente | §7.3 |
| 22 | ⛔ **al distacco si rilasciano tutti i tasti e i pulsanti** | un Ctrl rimasto giù in una sessione che sopravvive al client rende il desktop inservibile al riattacco, e nessuno collega le due cose | §7.3 |
| 23 | **`TELA` è la risposta obbligatoria ad `ADATTA_TELA`** | §7.1 imponeva un «rifiuto motivato» e non esisteva un messaggio per dirlo: il client sarebbe rimasto ad aspettare per sempre | §7.1 |
| 24 | dopo un cambio di tela, **un secondo di grazia** sulle coordinate vecchie | è l'unico momento in cui i due lati hanno legittimamente due verità diverse. Dichiarata come eccezione a §3, non lasciata all'improvvisazione | §7.1 |
| 25 | il motivo del congedo viaggia **anche nel codice d'errore applicativo della chiusura della sessione WebTransport** | se il congedo non arriva — stream rotto, messaggio illeggibile — il motivo passa comunque. È la ferita di `LEZIONI.md` §1.7 curata con due strade invece che con una. ⚠ *Diceva «chiusura QUIC», ed è la lettura che il rilievo **R1.4** ha dichiarato impossibile per la pagina: l'API espone la chiusura **della sessione**, non quella della connessione HTTP/3 sotto. Allineata il 10 agosto 2026, rilievo **R11.8*** | §3.1 |
| 26 | ⭐ **la funzione di banco entra nel protocollo**: due tipi nuovi, `BANCO_MARCA` (`0x000F`) e `BANCO_ESITO` (`0x0010`) — il rettangolo 16×16, il colore, e il **ritardo `N` iniettabile** | l'anello del ritardo di §2.6 misura dal lato che riceve, e perché quel numero valga il banco deve poter **iniettare un ritardo noto** e verificare che la mediana salga di esattamente quello — *«un banco che non lo fa non sa di misurare»* (`web/rapporti/S4-ritardo-disegno.md` §4.2). Quel comando **attraversa il filo**: improvvisarlo nel codice di prova sarebbe il difetto muto contro cui `RCP.md` §0 esiste. ⛔ **La funzione è spenta di suo** (invariante I6) e spenta risponde `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`, mai un silenzio. ⛔⛔ **13 agosto 2026: la funzione NON dà il ritardo noto, e alla fase 3 non l'ha dato** — `BANCO_ACCESO 0` e il ramo `ACCETTATA` è **uno stub** `[R]`. Il ritardo noto è stato iniettato **fuori dal prodotto**, e P1 è `[M]` verde (N=25 → +25,08; N=60 → +58,58). ⭐ E fuori dal prodotto è **meglio**: l'ancora d'orologio non passa per il percorso iniettato, quindi P1 **sa ancora fallire**. ⇒ ⏳ resta da decidere se completare il ramo o togliere i due tipi (`RCP.md` §7.5) | §7.5 |

> ⭐ *La riga 26 è **della notte del 9 agosto 2026** e stava soltanto in `RCP.md` §7.5; è registrata
> qui il 10 agosto, rilievo **R11.13** e **R11.15**.* ⛔ **È 🔸, non ✅**: la provenienza dichiarata
> da §7.5 stessa è il **rilievo R3.4 della revisione del banco della fase 1**, e la motivazione
> viene da `web/rapporti/S4-ritardo-disegno.md` §5.3 — **non da una frase dell'utente**. Le
> decisioni che l'utente ha davvero pronunciato (§1.6, §1.8) portano qui la **frase virgolettata
> con la data**; questa non ha né frase né voce, e `fasi/01-filo-nudo.md` la marcava ✅.
>
> ⚠ **Perché la marca conta proprio su questa**: §7.5 aggiunge **due tipi di messaggio** e con essi
> consuma la clausola di §9 che `RCP.md` §12 dichiara essere stata *«l'ultima occasione»*.
> Marcata ✅ diventerebbe non correggibile senza tornare dall'utente; marcata per quel che è — 🔸
> derivata da una revisione — resta *«correggibile senza discussione»*, che è la condizione in cui
> la si vuole se un giorno quei due tipi dessero fastidio.

⚠ **E QUATTRO tipi di messaggio sono stati aggiunti** — `RICHIEDI_CHIAVE` e `TELA` il 9 agosto,
⭐ **`BANCO_MARCA` e `BANCO_ESITO` la notte del 9** (riga 26 qui sopra) — più **tre** motivi di
congedo (`TEMPO_SCADUTO`, `SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`). §9 lo vieta **dentro** una
versione maggiore, e la clausola che lo permetteva era che allora non esistesse nessuna
implementazione.

⛔ **E quella clausola è CONSUMATA dal 10 agosto 2026**, primo byte di codice: le implementazioni di
RCP/1 adesso esistono e sono contate in `RCP.md` §0-bis. Da qui in poi vale la regola senza sconti, e
i **quattro** tipi qui sopra sono tutto quel che la finestra ha lasciato passare. ⚠ *Questa riga
diceva «la clausola che lo permette è che **oggi** non esiste nessuna implementazione», al presente,
e lo dicevano con le stesse parole altri quattro punti di `RCP.md`: chi le leggeva dopo il 10 agosto
trovava scritto che il protocollo era ancora modificabile. Corretta l'11 agosto 2026, rilievo
**R12C.2**.*

> ⚠ *Corretta il 10 agosto 2026, rilievo **R11.13**: questa riga diceva «due tipi … più due motivi»,
> e i due della funzione di banco non comparivano in **nessun punto** di questo documento — mentre
> `RCP.md` §12 dichiara che sono entrati «sotto la clausola di §9, e **quella era l'ultima
> occasione**». `RCP.md` §0-bis rimanda proprio qui per le chiusure marcate 🔸: due tipi che
> consumano una finestra irripetibile non possono mancare dal documento che il progetto designa
> come fonte unica.*

⏳ Quel che RCP/1 lascia **volutamente** aperto — microfono, puntatore relativo, tocco, 4:4:4, più
schermi — sta in `RCP.md` §12, dichiarato invece che dimenticato.

### 1.6 ✅ ⭐ Niente client dedicati: il client è il browser

*9 agosto 2026. «Perché impazzire a sviluppare 2 client separati quando un client, e in aggiunta
universale, lo abbiamo già bello pronto? il WEB!» — e, alla precisazione: «Non una seconda: Remotix
funzionerà senza client dedicati, basterà avere un browser moderno».*

⛔ **È la decisione più grossa presa dopo la morte di RDP**, e va letta accanto a quella: §1.1
toglieva Windows per togliere i tre muri di RDP; questa toglie **i client** per togliere il costo
di scriverli due volte e il muro su cui v1 è morto davvero — un telefono che decodifica in
software.

| | Prima | Adesso |
|---|---|---|
| i client | Linux (C) e Android (Kotlin), scritti da noi | **una pagina web**, servita dal server |
| il binario B | cinque fasi, A1-A5 | ⛔ **non esiste più** |
| chi può collegarsi | due sistemi | **qualunque cosa abbia un browser moderno** |

**I fatti su cui poggia, tutti `[S]` e nessuno misurato da noi** — verificati il 9 agosto perché la
mia conoscenza si fermava a maggio e questa roba si muove in fretta:

| | |
|---|---|
| **WebTransport** | ⭐ **su tutti e tre i motori da marzo 2026**, con Safari 26.4. Dà a una pagina esattamente quel che RCP usa: stream QUIC indipendenti, `RESET_STREAM`, datagram, migrazione. ⚠ *«Baseline» tolto il 9 agosto sera: è un termine tecnico con un significato preciso, e non veniva da nessuno dei quattro rapporti (R2)* |
| **WebCodecs** | Chrome 94+, Firefox 130+, Safari 26+, Chrome per Android dalla **147** |
| **HEVC in hardware su Android** | via WebCodecs: 8 bit dalla Chrome 107, **10 bit dalla 108** — cioè il muro di v1 risulta **passabile**, e la sonda che lo verifica è una pagina invece di un APK |

⭐ **Che cosa il protocollo ci guadagna, ed è la ragione per cui l'idea si poteva accettare**: RCP
non cambia. WebTransport porta gli stessi mattoni su cui `RCP.md` §5.1 è stato disegnato — un
fotogramma per stream, l'abbandono, i datagram per l'audio. Se il filo fosse stato progettato su
TCP, questa idea sarebbe costata il protocollo intero.

⭐ **E Windows torna dentro senza sottostare alle sue regole** *(osservazione dell'utente)*. §1.1 e
`SPECIFICHE.md` §12 buttavano fuori Windows **come server** e **come client da servire con RDP** —
non le persone che lo usano. Un browser su Windows non è codice nostro, non è FreeRDP, non è
`mstsc`: è lo stesso client di tutti gli altri, e non costa una riga.

⭐⭐ **E ci restituisce un pezzo dell'arbitro perduto.** `PIANO.md` §0.4 dice che buttando RDP
abbiamo perso `mstsc`, che protestava gratis. Una pagina gira su **tre motori scritti da tre
squadre che non ci conoscono** — Blink, WebKit, Gecko: quando due sono d'accordo e il terzo no,
quello è un difetto che si dichiara da solo. ⚠ **Il rovescio va scritto insieme**: la matrice dei
client non sparisce, **cambia forma**, e i browser serviti vanno **dichiarati** e collaudati su
almeno due motori diversi — `LEZIONI.md` §2.1 non decade, si trasferisce.

⛔ **Che cosa costa, e non è «un piccolo aggravio»:**

1. il server acquista **un secondo mestiere**: servire una pagina. Non più solo QUIC nudo, ma
   **HTTP/3 con WebTransport** — più un ascoltatore **TCP** per il primo caricamento, perché un
   browser che apre `https://…` parte in TCP e passa a QUIC solo se il server glielo annuncia
   (`Alt-Svc`). Due porte in ascolto sullo stesso numero, una TCP e una UDP;
2. ⛔ **cambia il criterio con cui si sceglie la libreria QUIC** (§6.4): non basta più che parli
   QUIC, deve portare **HTTP/3 e WebTransport lato server**. È diventata la prima domanda, non
   l'ultima;
3. tre cose che con un client nostro decidevamo noi passano al browser: **il certificato** (§1.7),
   **le scorciatoie di tastiera** — `Ctrl+W` chiude la scheda, e la Keyboard Lock è `[S]` solo su
   Chrome e solo a schermo intero — e **gli appunti**, che richiedono permesso o gesto
   dell'utente proprio nel verso che `§5-ter.1` dice essere il più usato.

⚠ **Il rischio residuo, dichiarato**: la decodifica in hardware non la comandiamo più. Con un
client nostro guardavamo **il nome del decodificatore scelto** (`c2.` contro software); in un
browser quel nome non c'è, e se un dispositivo decodificasse in software **non avremmo leva** — si
misura e si dichiara. È il motivo per cui la sonda del browser va fatta **prima** di scrivere il
filo, non alla fase 2.

*Conseguenze già scritte dove vanno: `SPECIFICHE.md` §1, §4, §7.3, §9; `RCP.md` §2 e §4.1;
`PIANO.md`, dove il binario B sparisce e la sonda cambia natura.*

> ### ⭐ Da dove è venuta l'idea, e il riferimento che ne discende: **XPRA**
>
> *9 agosto 2026. «Ti spiego perché mi è venuto in mente il discorso WEB. In passato ho avuto modo
> di usare XPRA, e devo dire di essere rimasto molto sorpreso».*
>
> ⛔ **Non è un aneddoto: è il punto 0 della ricetta di `LEZIONI.md` §9** — *«cercare chi l'ha già
> fatto»*, che su KDE ci aveva fatto trovare `KRdp` **dopo** che lo studio lo aveva dato per
> inesistente, e a trovarlo era stata una domanda dell'utente. È successo di nuovo, e alla stessa
> maniera.
>
> **Xpra ha un client HTML5 che fa questo mestiere da anni**, e la sorpresa dell'utente all'uso è
> il dato più utile che abbiamo: dice che la strada **si percorre**, non che la nostra sarà uguale.
>
> 🔸 **Da cui uno studio, prima di scrivere la pagina** — piccolo, sulla forma degli altri:
> `reference-web/`, e le domande sono quelle del client, non del trasporto (Xpra è su WebSocket,
> noi su WebTransport, e quel pezzo non si eredita): **come dipinge**, come tratta la tastiera nel
> browser, come risolve gli appunti e il cursore, che cosa fa quando la finestra cambia misura,
> e quanto costa in ritardo.
>
> ⚠ **Con il confine di `§5-bis.0-bis`, che vale identico**: si studia **come si comporta e come si
> sente all'uso**, non si copia il codice — la licenza del progetto è rinviata a fine lavori (§7.6),
> e un pezzo preso da un progetto altrui la deciderebbe al posto nostro.

### 1.7 ✅ Il certificato: un clic la prima volta, e il certificato vero per chi ha un nome

*9 agosto 2026. «Per la parte che riguarda certificato, sicurezza, ecc riflettiamo: ribadisco il
principio che qui non dobbiamo rispettare standard militari».*

⛔ **La premessa che cambia tutto**: §1.3 prometteva **zero interazione** — *«si digitano
indirizzo, porta, utente e password, e basta»*. Con un client nostro quella riga la decidevamo noi.
Con un browser **non è più una nostra scelta**: la regola è di Chrome e di Safari, e «niente
standard militari» non la tocca.

> ## ⛔ Riscritta la sera del 9 agosto, dopo la misura S1 — il predefinito che avevo proposto **non funziona**
>
> *L'indagine sta in `web/rapporti/S1-certificato.md`, ed è lettura di codice con file e riga, non
> un'impressione.*
>
> Avevo scritto che l'eccezione concessa dall'utente sul certificato della pagina sarebbe valsa
> anche per la sessione WebTransport, e che quel clic **era** la fiducia al primo incontro di
> `RCP.md` §4.1. **È falso su due motori su tre:**
>
> | | Perché |
> |---|---|
> | **Chrome/Edge** | l'eccezione la consulta **un solo punto**, alimentato dagli errori delle richieste normali; il client WebTransport **non la interroga mai** `[R]` — assenza verificata con controllo positivo. ⛔ E c'è un **secondo muro indipendente**: il QUIC di Chrome pretende una radice **incorporata nel browser** |
> | **Firefox** | l'eccezione **viene** consultata anche su HTTP/3, e poi la sessione si chiude se la radice non è incorporata `[R]`. L'unica deroga scritta nel codice è, testualmente, `serverCertificateHashes` |
> | **Safari** | `[?]` **il caso aperto**: la sua eccezione mette il certificato **nel portachiavi**, e WebTransport passa di lì — potrebbe essere l'unico dove funziona. Nessuno l'ha documentato |
>
> ⛔ **E la proposta dell'autorità da installare (qui sotto) aveva una terza ragione per non
> funzionare, più dura delle due già scritte**: su Chrome **non basta nemmeno metterla nel
> magazzino di sistema**, perché quella radice non è *incorporata nel browser* e non lo diventa.
>
> ⭐ **Una cosa cade e semplifica**: `Alt-Svc` non c'entra — WebTransport apre la sua connessione da
> sé `[S]`. Il ripiego silenzioso su TCP che avevo dichiarato come pericolo **non può accadere**.

**Quel che vale, deciso dall'utente la sera del 9 agosto**: *«Stiamo complicando le cose. Abbiamo 2
livelli per la sicurezza: il trasporto e l'accesso. Per il trasporto usiamo quello che già oggi i
browser supportano senza problemi: tls. Per l'accesso: al momento restiamo fermi su ip:porta con
userid e password»*.

| Livello | Come |
|---|---|
| **trasporto** | **TLS**, sempre. Il certificato se lo fa il server, e ⭐ **la pagina passa al browser la sua impronta** (`serverCertificateHashes`) — che è il meccanismo che i browser espongono **proprio per i server senza dominio**, non un aggiramento |
| **accesso** | **indirizzo, porta, utente e password**. Niente altro |

⭐ **Perché questo non è la «strada complicata» che sembrava**: la rotazione del certificato ogni
14 giorni e la pubblicazione dell'impronta stanno **dentro il server** — è lui che serve la pagina,
quindi ci scrive dentro l'impronta corrente. L'utente non tocca niente e non sa che esista.

⚠ **Quel che resta a carico dell'utente, ed è il prezzo dichiarato di non avere un dominio**: il
**clic sull'avviso** al caricamento della pagina, la prima volta su ogni dispositivo. `[?]` Su
Chrome l'eccezione potrebbe durare **circa una settimana** e non per sempre — da misurare, e se
fosse vero è un clic ricorrente, non uno solo.

| Chi ha un dominio | mette un **certificato vero** (Let's Encrypt con sfida DNS, che non richiede di esporre niente): **una riga di configurazione, non una strada diversa**, e l'avviso non compare mai |
|---|---|

> ### ⭐ E un certificato vero compra molto più di quel che sembra — trovato incrociando S1 e S3
>
> Nessuno dei due rapporti poteva vederlo da solo:
>
> - **S1**: dietro un'eccezione di certificato, su Chrome **il Service Worker non si installa**
>   `[R]` ⇒ niente applicazione installabile;
> - **S3**: in una **PWA installata** la lista dei tasti riservati di Chrome è **vuota** `[R]` ⇒
>   arrivano alla sessione **tutte** le scorciatoie.
>
> ⛔ **Messe insieme: chi ha un dominio non compra l'assenza di un avviso, compra la tastiera
> intera.** È una differenza di **prodotto**, non di comodità, e va detta a chi installa — perché
> nessuno la dedurrebbe da sé. *(Dettaglio in `web.md` §1.2 B.)*

⛔ **Scartata: la «via Plex»** — un dominio nostro che risolve agli indirizzi privati dei server,
cioè certificato vero e zero fatica per l'utente. Sarebbe **un servizio da tenere in piedi per
sempre**, e il giorno in cui non ci fosse più smetterebbero di funzionare tutti i server
installati. È la dipendenza più pesante che il progetto abbia preso in considerazione, ed è stata
respinta dall'utente insieme al resto della complicazione.

⭐ **Safari e iPhone NON sono un buco: sono serviti come gli altri due.** `[R]` WebKit ha
implementato `serverCertificateHashes` il **2 ottobre 2025** (bug 300057,
`NetworkTransportSessionCocoa.mm`) e l'ha spedito in **Safari 26.4**. Quel che resta da misurare è
solo **una comodità** — se lì l'eccezione basti da sola, cioè se si possa fare a meno di pubblicare
l'impronta: l'impronta si usa comunque (`RCP.md` §4.1-bis).

> ⛔ *Corretto la notte del 9 agosto 2026, rilievo **R4.4** della revisione del banco della fase 1.*
> Qui c'era scritto *«`[?]` Safari e iPhone restano il buco dichiarato: WebKit non implementa
> `serverCertificateHashes` `[S]`»*. `web.md` §3.1 dichiarava di aver corretto **questo paragrafo**
> lo stesso 9 agosto — ⛔ **e la correzione non era mai arrivata qui**, né in `RCP.md` §4.1-bis.
> Tre documenti con la stessa frase falsa, uno dei quali è l'arbitro, e un rapporto che li dava per
> curati. È la forma della voce 6 di `fasi/00-ambiente.md`: *la lezione era già scritta, la cura è
> rimasta una nota in un documento.*

> ### ⛔ La proposta di far installare un'autorità nostra, e perché è stata scartata
>
> *Proposta dall'utente lo stesso giorno: «e se Remotix generasse il suo certificato e lo facesse
> installare al client alla prima connessione?». Tenuta scritta perché non venga riproposta senza
> le due ragioni.*
>
> Funziona, ed è la strada che **sembra** più pulita: si installa una volta e poi nessun avviso.
> Ma:
>
> 1. ⛔ **non toglie il rischio che vorrebbe togliere.** Per installare quel certificato bisogna
>    prima **scaricarlo dal server**, cioè attraverso la prima connessione — quella di cui non ci
>    si fida ancora. Chi si mette in mezzo ti fa installare **la sua** autorità;
> 2. ⛔ **e il danno peggiora invece di ridursi.** Un'eccezione su certificato autofirmato vale
>    **solo per il nostro indirizzo**; un'autorità installata vale per **qualunque sito**, su quel
>    dispositivo, per sempre. La strada che toglie l'avviso spaventoso è quella che l'avviso se lo
>    meriterebbe di più;
> 3. ⚠ più il costo vero: quattro o sette passi **nelle impostazioni di sistema**, diversi su ogni
>    sistema operativo, con un avviso permanente *«la rete potrebbe essere monitorata»* su Android
>    e due schermate separate su iPhone. E la chiave privata di quell'autorità vivrebbe **sul
>    server**.
>
> ⭐ **E quel che la proposta voleva ce l'abbiamo già**: «installalo una volta e non pensarci più»
> **è il clic sull'avviso** — un clic, dentro il browser, nessun amministratore, uguale su tutti i
> sistemi, e valido solo per noi.

⚠ **Una cosa sulla sicurezza che cambia di natura, e va scritta accanto al rischio già accettato in
§1.3.** Con un client nostro, chi si mette in mezzo alla prima connessione **intercetta dei byte**.
Con un client web **il client arriva dal server a ogni visita**: chi si mette in mezzo non
intercetta, **riscrive la pagina in cui si digita la password**. Il rischio è lo stesso — *la prima
connessione su ogni dispositivo* — ma **la conseguenza è più grossa**. Dopo il primo clic il
certificato è appuntato e uno diverso fa ricomparire l'avviso; con il certificato vero il caso non
si presenta.

~~`[?]` **La misura che decide la forma**: l'eccezione che l'utente concede sul caricamento della
pagina (TCP) copre anche la connessione WebTransport (UDP) allo stesso indirizzo?~~

⛔ **Chiusa leggendo, il 9 agosto 2026, per due motori su tre: la risposta è NO.** L'eccezione non
copre WebTransport né su Chrome né su Firefox `[R]`, per due ragioni tecniche indipendenti
(`web.md` §3.1). ⭐ **Quindi `serverCertificateHashes` non è un ripiego: è la strada**, su tutti e
tre i motori. Resta da misurare **solo Safari**, e solo per sapere se lì l'impronta si possa
risparmiare — che è una comodità, non una piattaforma.

> ⚠ *Riscritta la notte del 9 agosto 2026, rilievo **R4.4**. La domanda era ancora aperta in questa
> pagina mentre `web.md` §3.1 l'aveva già chiusa con due `[R]` letti nel codice: tenerla aperta
> faceva **pianificare una misura già fatta**, che è la forma del rilievo R1.25 di `RCP.md`.*

> ## ⏳⏳ Il debito di sicurezza, dichiarato dall'utente e messo in evidenza
>
> *9 agosto 2026. «Il tuo timore del "man in the middle" lo appunto bene in evidenza: prima
> completiamo il progetto, poi svilupperemo una sua evoluzione per mettere in sicurezza il server
> con i sistemi più solidi che la moderna tecnologia offre (es. MFA)».*
>
> ⛔ **Non è una svista da segnalare di nuovo fra sei mesi: è un rinvio deciso, con la sua data.**
> Va qui, in evidenza, perché chi riprenderà il progetto trovi scritto **che cosa si era accettato
> e in cambio di che cosa** — e non lo scopra da un difetto.
>
> **Quel che è accettato oggi**, e vale finché il prodotto non è completo:
>
> | | |
> |---|---|
> | la prima connessione su ogni dispositivo | scoperta a un uomo-in-mezzo (§1.3, rischio valutato e accettato) |
> | e con il client web | chi si mette in mezzo **riscrive la pagina** invece di intercettarla |
> | l'unica chiave | la **password PAM**, con il **ban dell'indirizzo** di `RCP.md` §4.4-bis — tre tentativi falliti, dodici ore (§1.9) |
>
> ⭐ **E questa nota chiude un cerchio che era già stato aperto**: `DECISIONI.md` §4.3 — il blocco è
> di REMOTIX, non del desktop — ha una **clausola di scadenza scritta l'8 agosto** con queste
> parole: *«il ragionamento regge solo finché la password PAM è l'unica chiave. Chi implementa
> l'autenticazione forte rilegge questa voce»*. L'MFA è precisamente quell'evento. **Quando si
> aprirà l'evoluzione, le voci da rileggere sono quattro e sono queste**: §1.3 (la fiducia), §1.7
> (questa), §4.3 (il blocco schermo, che con una seconda chiave tornerebbe a difendere qualcosa) e
> ⭐ **§1.9** — *aggiunta il 10 agosto 2026*: il ban a tre tentativi è la difesa che la password da
> sola pretende, e con una seconda chiave il suo prezzo — l'indirizzo del NAT chiuso a tutti per
> dodici ore — diventa più caro di quel che compra.

---

### 1.8 ✅ ⭐ Apple è un di più, non un obiettivo — e la sterzata sul browser è il motivo

*9 agosto 2026, dall'utente, chiudendo la domanda «serve procurare un Mac per misurare Safari?».*

> *«Apple copre il 4-5% dell'utenza; con la sterzata che ho impresso supportando il browser come
> client abbiamo recuperato Windows e la platea di potenziali utilizzatori sale al 95%. Apple è un
> di più: se capiterà l'occasione di testarlo bene, altrimenti pazienza.»*

⭐ **È §1.6 che si paga la terza volta.** Il client-pagina aveva già tolto due client nativi e
cinque fasi di piano, e riportato dentro **Windows come posto da cui ci si collega**. Qui fa una
cosa in più: **rende Apple una piattaforma che non costa niente non misurare**, perché il codice è
lo stesso per tutti e tre i motori.

⛔ **E la distinzione che va tenuta ferma, o questa voce verrà letta al contrario fra sei mesi:**

| | |
|---|---|
| **che cosa NON cambia** | Safari, iPhone e iPad **restano serviti**: `serverCertificateHashes` è spedito in **Safari 26.4** `[R]`, ed è la stessa strada degli altri due motori (§1.7, `RCP.md` §4.1-bis). Non si scrive una riga di codice in meno |
| **che cosa cambia** | non si **spende** per verificarlo: niente Mac da procurare, niente dispositivi in affitto, niente tunnel. La misura **S1a** esce dalla fase 1 e resta `[?]` |
| ⛔ **e che cosa non si può dire** | finché nessuno l'ha provato, *«funziona su iPhone»* è **una deduzione, non una misura** — forma **E5**. Il posto dove non deve comparire è la **documentazione del prodotto** |
| **il prezzo, dichiarato** | la scelta della libreria QUIC (§6.4) si fa su **due motori su tre**, e la riga sta scritta accanto alla scelta |

⚠ **Le percentuali sono una stima dell'utente**, non una misura di questo progetto: `[?]` 4-5% e
95%. Non cambiano la decisione — che è di **priorità**, non di tecnica — ma la marca si mette
comunque, perché una decisione presa citando un numero non misurato va sapendo di esserlo
(`LEZIONI.md` §2.3-quater).

⭐ **La porta resta aperta a costo zero**: i tre controlli di S1a sono già scritti in
`fasi/01-filo-nudo.md` e la pagina sonda è la stessa. Il giorno in cui passasse di mano un Mac o un
iPhone, **la misura è un pomeriggio**.

### 1.9 ✅ ⭐ Tre tentativi falliti, poi il ban dell'indirizzo per 12 ore

*10 agosto 2026, dall'utente, in due passaggi nello stesso discorso.*

> *«Secondo me la cosa deve funzionare in modo molto semplice: se l'utente sbaglia la password per 3
> volte consecutive, non vengono più accettate connessioni da quell'IP per 12 ore (ban).»*
>
> E poi, stringendo: *«3 tentativi di connessione fallita (perché user sbagliato o perché password
> sbagliata) causano il ban di quell'IP.»*

⛔ **Sostituisce la forma precedente per intero**, che era 🔸 e sta nella riga 11 di §1.5: 5 tentativi
in 5 minuti, finestra da 30 secondi che raddoppia fino a 15 minuti, **due** contatori — per nome
utente e per indirizzo — e l'azzeramento su un accesso riuscito. ⭐ **Il contatore per nome utente
non esiste più**: il conto guarda l'indirizzo e nient'altro, e tre nomi utente diversi contano tre.

| | |
|---|---|
| **il conto** | tre autenticazioni fallite dallo stesso indirizzo (**senza la porta**), ⛔ **dentro 5 minuti** — *regola dell'utente, stesso giorno: «i 3 tentativi falliti devono avvenire entro i 5 minuti per far scattare il ban»*. La finestra è **scorrevole**: si guardano gli ultimi tre, non si riparte dal primo |
| **la conseguenza** | quell'indirizzo è fuori per **12 ore** |
| **che cosa azzera** | 🔸 un'autenticazione **riuscita** da quell'indirizzo. *Derivata da «consecutive»: senza, tre errori di battitura sparsi in un anno bannerebbero l'indirizzo da cui si lavora tutti i giorni* |
| **che cosa conta** | ✅ **solo** l'autenticazione fallita. Non gli errori di protocollo, non i tempi scaduti, e ⛔ **non `GIA_ATTIVA_REMOTA`** — che è quel che riceve il secondo dispositivo dello **stesso** utente, e che bannerebbe l'utente da sé in tre riattacchi |
| **che cosa vede chi è bannato** | ✅ *«viene visualizzata una pagina di login rifiutato (max tries reached)»*: la pagina si serve lo stesso e **dice** che i tentativi sono esauriti. La sessione WebTransport si rifiuta con `TROPPI_TENTATIVI` per la scheda **già aperta**, che altrimenti resterebbe ad aspettare |
| **il ban sopravvive al riavvio** | ✅ **sì, su file.** Un ban che si azzera riavviando è una protezione che si perde da sé — invariante **I7** |
| **come si esce** | ✅ *«comando di sblocco oppure il trascorrere delle 12 ore»*. Il comando chiede l'accesso alla macchina, che è l'unica chiave che il caso ammette, e ⛔ **ogni sblocco si scrive nel registro** |

⭐ **Perché la forma nuova è migliore di quella che sostituisce, oltre che più dura**: spariscono il
raddoppio, le due finestre che si sovrappongono e la domanda «che cosa fa il contatore per nome
quando quello per indirizzo è già scattato». ⛔ E sparisce per costruzione il difetto che **B5** ha
trovato il 10 agosto — la chiave del contatore conteneva **la porta**, che con un solo tentativo per
connessione (§`RCP.md` 4.4) cambia ogni volta, quindi quel contatore valeva **sempre 1**.

⛔ **E `RCP.md` non guadagna un byte**: `TROPPI_TENTATIVI` (`0x08`) c'era già, nessun tipo nuovo,
nessuna deroga alla regola di §9 — che è la regola che il progetto si è dato e che da qui in poi non
ha più sconti.

⚠ **Il prezzo, accettato sapendolo, e non lo paga chi indovina:**

| | |
|---|---|
| **dietro un NAT** | gli indirizzi si condividono: tre errori di **una** persona chiudono la porta a tutti gli altri per dodici ore. È esattamente il caso per cui il contatore per nome utente esisteva |
| **il primo a inciamparci è il proprietario** | parola lunga, tastiera di un telefono. Da qui la pagina che **dice** che cos'è successo e il comando di sblocco: senza quei due, la regola è indistinguibile da un guasto |
| ⛔ **e la parola resta l'unica chiave** | tre tentativi per indirizzo alzano molto il costo, e non chiudono la partita: diecimila indirizzi fanno trentamila tentativi su un conto solo. La chiude l'autenticazione forte rinviata a fine progetto — §1.7, il riquadro del debito di sicurezza, ⭐ **e questa voce va nell'elenco di quelle da rileggere quel giorno** |

⭐ **E una cosa che il ban NON può fare**, scritta perché nessuno gliela attribuisca: nessuno può far
bannare l'indirizzo di **qualcun altro**. Per arrivare a `CREDENZIALI` bisogna aver completato la
stretta di mano QUIC, che pretende che i pacchetti tornino davvero a quell'indirizzo — il mittente
non si falsifica.

⚠ **E una conseguenza sul lavoro, non sul prodotto**: i banchi partono tutti dallo stesso indirizzo e
quello del limitatore fallisce di proposito. Con dodici ore, «si aspetta la scadenza» non è una cura:
il banco si serve del comando di sblocco, e quello del limitatore **non lo chiama dentro il proprio
giro** o non prova più niente (`fasi/01-filo-nudo.md`, regola B0.3).

*Conseguenze già scritte dove vanno: `RCP.md` §4.4-bis (riscritta per intero, e da 🔸 diventa ✅) e
§8.2; `SPECIFICHE.md` §4.2; `fasi/01-filo-nudo.md` B0.3 e B8.*

---

### 1.10 ✅ ⭐ La verifica PAM esce dal filo unico — **prima della fase 2**, e con un processo aiutante

*11 agosto 2026, sera, dall'utente, alla chiusura della fase 1. La domanda gli è stata portata con
il numero misurato accanto, non come un'ipotesi.*

**Il fatto.** Il server della fase 1 gira in **un ciclo `poll` solo** (`src/main.c`), e la verifica
PAM **blocca quel filo**. ⛔ Non è una stima: **B8 l'ha misurato la sera dell'11 agosto** —
`[M]` da **1,0 a 2,2 secondi** per tentativo (mediane **2123 · 2198 · 1086 ms**), e ⭐ **il ritardo
lo mette PAM, non noi**: il server attende **+1034 ms** oltre il proprio secondo fisso sui respinti
contro **+84 ms** sugli ammessi, che è la firma di `pam_faildelay`.

**La decisione.** ⛔ **Si cura prima di aprire la fase 2**, e ⭐ **con un processo aiutante, non con
un filo**: PAM non è affidabilmente rientrante, e un thread porterebbe guai suoi dentro la cura di
un problema di concorrenza.

> ⭐ **Perché prima della fase 2, e non alla 5 come diceva il ripiego.** Finché non c'è video, il
> sintomo è *«l'ultimo dei dieci aspetta dieci secondi»*: sgradevole e circoscritto. ⛔ **Dalla fase
> 2 in poi diventa un altro difetto**: lo schermo di **tutti** quelli collegati si pianta per uno o
> due secondi ogni volta che **qualcun altro** entra — e chi lo vedrà lo attribuirà al **video**,
> perché è lì che si vede. ⚠ È la forma «il sintomo non nomina la causa» che `LEZIONI.md` §1.6
> descrive, e curarla adesso significa **non farla nascere**.

⚠ **E costa poco proprio adesso**: `rcp.c` non si tocca, quindi **le dodici certificazioni dell'11
agosto restano valide**.

⛔ **La proprietà da provare non è «PAM funziona ancora»**: è **«mentre uno si autentica, gli altri
non se ne accorgono»** — cioè un secondo client che continua a ricevere pacchetti durante la
verifica. Oggi **non esiste nessun banco che la guardi**, e senza quel banco la cura è una speranza.

*Conseguenze da scrivere: `SPECIFICHE.md` §5.5 (il riquadro del ripiego, che oggi rimanda alla fase
5) e `src/main.c` (il commento «UN SOLO FILO, E VA DETTO»).*

---

### 1.10-bis ✅ ⭐ **Un figlio per utente** — e non è simmetria, è un fatto del sistema

*12 agosto 2026, dall'utente, davanti alla misura del montaggio della fase 2.*

**Il fatto, `[M]`**: ⛔ **root non si collega al bus di sessione dell'utente** — e ⛔ **solo root può
verificare con PAM la parola d'ordine di un altro**. ⇒ **Le due cose non stanno nello stesso
processo**, e non è un dettaglio di implementazione: senza bus non c'è cattura, senza root non c'è
autenticazione.

**La decisione.** Il server resta **privilegiato**, e per ogni utente ammesso genera un **figlio che
gira come lui** e tiene il suo bus di sessione, la sua cattura e i suoi dispositivi.

⭐ **È l'aiutante di §1.10 al contrario, ed è la stessa regola**: *un mestiere per processo*. Lì un
figlio **meno** privilegiato del padre fa la cosa che blocca; qui un figlio **diversamente**
privilegiato fa la cosa che il padre non può fare. ⇒ La forma del server non è stata scelta due
volte: è stata scelta una volta e applicata due.

⭐ **E paga oltre la fase 2**: è la strada naturale verso il multi-tenant della **fase 10**, e isola
un utente dall'altro **per costruzione** invece che per attenzione.

⚠ **Il prezzo, dichiarato**: un processo per sessione. Col tetto di §1.11 — 16 — sono sedici
processi, che è un costo noto e misurabile, non una sorpresa.

*Conseguenze scritte: `fasi/02-primo-fotogramma.md`, e il prodotto delle fasi che toccano la
sessione.*

### 1.10-ter 🔸 ⛔⛔ `/run/user/<uid>` dell'utente ce lo dà il **linger**, non noi — ed è un requisito, non una fortuna

*Scritta la sera del **15 agosto 2026**, alla fase 5, dopo un desktop che non si vedeva.*

> ### ⛔ E la prima stesura di questa voce era SBAGLIATA — corretta la sera stessa
>
> Diceva: *«la pila PAM del servizio deve chiamare `pam_systemd`, e la nostra non lo faceva»*,
> perché `remotix.pam` chiude con `common-session-noninteractive` — che su Debian 13 `[M]` **non**
> contiene `pam_systemd`, mentre `common-session` sì.
>
> ⛔ **La premessa era falsa**: il prodotto **non apre nessuna sessione PAM**. `figlio.c:2428` lo
> dichiara per esteso — *«`sessione_assicura()` farebbe NASCERE una sessione … quella è la strada
> del login vero (`pam_open_session` → `pam_systemd`), e non è di questo mandato»* — e `grep` lo
> conferma: in `src/` non esiste nessuna chiamata a `pam_open_session`. ⇒ Quale pila di sessione
> stia in `remotix.pam` oggi **non cambia niente**, perché quella pila non viene mai eseguita.
>
> ⚠ La riga `session optional pam_systemd.so` resta nel file, ma **come porta aperta dichiarata**,
> non come cura: il giorno in cui il prodotto aprisse davvero le sessioni, la pila «noninteractive»
> non ne creerebbe nessuna.

**Il fatto vero, misurato.** `/run/user/<uid>` — e con lui il socket del bus di sessione, senza il
quale il figlio non ha niente da catturare — nasce perché l'utente ha il **linger** acceso
(`loginctl enable-linger`). ⭐ È scritto da sempre nella ricetta che ha prodotto il primo desktop
vero (`fasi/rapporti/F5-desktop-vero.md`, passo 1: *«utente `prova` (uid 1001), parola d'ordine,
`enable-linger`»*) — ⛔ **ma non era scritto da nessuna parte che è un requisito del prodotto.**

`[M]` **Il prezzo, pagato il 15 agosto:** dopo il riavvio della macchina — il cui rootfs vive in RAM
— l'utente `prova` non esisteva più; ricreato il conto **senza linger**, il figlio ha scritto per
tre volte *«runtime `/run/user/1001` ⛔ NON c'è, socket del bus ⛔ non c'è»* e l'utente ha visto uno
**schermo nero**. ⚠ Il registro diceva esattamente che cosa mancava, e a nessuno era chiaro che
quella riga fosse una condizione d'ambiente e non un difetto del codice.

**Da cui, e sono tre obblighi come per l'headless di §4.3-bis:**

1. il linger si **dichiara** fra i requisiti dell'utente servito, non si eredita da come la macchina
   è stata preparata un giorno;
2. il figlio, quando non trova il runtime, **nomina la causa probabile** invece del solo sintomo —
   *«manca `/run/user/<uid>`: quell'utente ha il linger acceso?»*;
3. ⏳ e resta aperta la domanda che sta sotto: se il prodotto debba **aprire lui** la sessione
   (`pam_open_session`) invece di dipendere dal linger. ⚠ Oggi è dichiarato fuori mandato, e va bene
   — ⛔ ma allora il linger è una **dipendenza del prodotto**, e come tale va installata e verificata.

> ### ⭐⭐⭐ E LA DOMANDA 3 SI È CHIUSA LA SERA STESSA: **il prodotto apre lui la sessione**
>
> *15 agosto 2026, fase 5, dopo il via libera dell'utente. ⇒ Il linger **non serve più**: era un
> puntello, e il puntello lo si toglie quando il muro sta in piedi.*
>
> ⛔ **La ragione non è di eleganza, è che senza sessione il compositore non parte affatto**: Mutter
> chiede `sd_pid_get_session()` e si sente rispondere **ENXIO**, poi muore con *«Failed to find any
> matching session»*. Il linger dà `/run/user/<uid>` e il bus, ⛔ ma mette i processi in
> `user@<uid>.service`, che è uno scope di classe **`manager`** — non una sessione.
>
> **Dove**: `figlio.c`, `diventa_ed_esegui()` passo **2-bis** — dopo la chiusura dei descrittori e
> **prima** di scendere all'uid. Con `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`,
> `PAM_RHOST`, e ⛔ **nessun `XDG_SEAT`**: la sessione nasce **headless per costruzione**, che è
> quel che §4.3-bis chiede da agosto e che finora avevamo per accidente.
>
> ⚠ `pam_end()` **senza** `pam_close_session()`, di proposito: la sessione logind appartiene al
> processo **guida** — questo, dopo l'`exec` — e logind se la riprende quando lui muore. ⭐ È
> l'invariante **I4** vista dal lato del sistema: il palco sopravvive al client perché sopravvive il
> figlio.
>
> ⇒ ⭐ **E le variabili XDG smettono di essere inventate**: `XDG_SESSION_ID` la mette `pam_systemd` e
> noi la **leggiamo** (`pam_getenvlist`). È la risposta all'osservazione dell'utente del 15 agosto.
>
> ### ⛔⛔ E VIENE CON UN VINCOLO DI DISPIEGAMENTO CHE NON ESISTEVA PRIMA
>
> `[M]` **Il server non deve girare dentro una sessione utente.** `pam_systemd`, quando chi chiama
> sta già in una sessione, **non ne crea una seconda — e non lo dice**. ⇒ Un server avviato a mano
> da `ssh` mette i suoi figli nella sessione di chi l'ha avviato, e il figlio resta senza runtime,
> senza bus e senza compositore: **lo stesso schermo nero, per una causa nuova**.
>
> `[M]` Misurato: col vecchio `riavvia-7700.sh` (che usa `setsid` — stacca il terminale ma **non
> cambia il cgroup**) il server stava in `session-127.scope`; con `systemd-run` sta in
> `system.slice/remotix-7700.service`, e i figli aprono la loro. ⭐ In produzione il caso non esiste
> — `remotix.service` è un'unità di sistema — ⚠ ma va **scritto**, perché un server avviato a mano è
> rotto in un modo che non si vede.

### 1.11 ✅ Il tetto delle sessioni resta **16, fisso in compilazione**, fino alla fase 3

*11 agosto 2026, sera, dall'utente, alla chiusura della fase 1.*

**Il fatto.** `src/rcp.c` ha `#define MAX_ATTACCATE 16`, mentre `SPECIFICHE.md` §5.5 vuole
**«tetto predefinito 10 sessioni, configurabile»**.

**La decisione.** ⛔ **Non si cambia adesso.** Il ragionamento che la regge è quello che §5.5 scrive
di sé: *«il limite vero non è un conteggio: è un **budget** di pixel al secondo, e lo pone il
codificatore»*. ⇒ Qualunque numero messo oggi è **un segnaposto**, e portarlo a dieci adesso
significherebbe cambiarlo **due volte**: una per obbedire alla lettera, e una quando arriva il
budget vero.

⛔ **E il prezzo si dichiara, invece di lasciarlo implicito**: per due fasi **il codice dice 16 e la
specifica dice 10**, e chi legge una delle due crede di sapere una cosa che l'altra smentisce. ⚠ È
esattamente la forma che ha prodotto il difetto della **finestra di cinque minuti** (rilievo R12C.5):
una regola copiata in quattro documenti, e le quattro copie non uguali. ⇒ **La differenza va nominata
in tutt'e due i posti**, o alla fase 3 ci si arriva credendo che il tetto sia dieci.

⚠ **E l'altra metà, che vale per qualunque numero si scelga**: **nessun banco ha mai visto quel tetto
mordere**. Riempirlo richiede dieci utenti **diversi** (una seconda connessione dello stesso utente
prende `GIA_ATTIVA_REMOTA`, **I2**), e il motivo con cui si rifiuta chi arriva è fra quelli che
vogliono il codificatore. ⛔ Finché non c'è, è **codice presente che nessuno ha visto funzionare** —
la stessa forma del contatore per indirizzo che **B5** ha trovato: si leggeva bene, e non faceva
niente.

*Conseguenze da scrivere: `SPECIFICHE.md` §5.5 e `fasi/01-filo-nudo.md`, «I ripieghi di fase».*

### 1.12 ✅ ⭐ La cura del congedo è **fuori fase, e dichiarata** — la fase 1 resta chiusa a 12 su 14

*11 agosto 2026, tarda serata, dall'utente, **dopo** la chiusura della fase 1.*

**Il fatto.** Il difetto del congedo di §8.1 — chiudendo la scheda la pagina non manda nessun
`CONGEDO`, su tutt'e due i motori — è stato trovato e **attribuito** in fase 1, e **curato dopo la
chiusura**: `src/pagina.html` non azzera più `congeda_corrente` nel `finally` di `submit`, lo azzera
`wt.closed`. ⛔ E il documento di fase dice, con parole dell'utente, che *«una cura di prodotto
infilata dopo la chiusura non è una cura, è un cambiamento non dichiarato»*.

**La decisione, e sono tre cose insieme:**

| | |
|---|---|
| ⛔ **la fase 1 non si riapre** | la certificazione resta **12 su 14** com'è stata consegnata. Un verdetto già dato non si tocca per un fatto successivo: si riaprisse per questo, «chiusa» smetterebbe di voler dire qualcosa |
| ⭐ **e la cura non si arretra** | è **misurata** con lo stesso rigore della fase — l'atteso scritto prima, **due giri per motore**, il registro conservato in `banchi/01-p5-ff-registro-cura.log`. Toglierla dal prodotto per rimetterla fra una settimana significherebbe tenere in casa un difetto **noto e curato** per una ragione di calendario |
| ⭐ **la cura è un'APPENDICE DATATA** | sta nel riquadro P5 di `fasi/01-filo-nudo.md`, sotto la cura descritta, e dice *«applicata e rimisurata la tarda serata dell'11»*. ⛔ Non entra nel conto della certificazione, e **non cambia un numero** di quel documento |

⛔ **Che cosa passa alla fase 2, e non si perde qui**: la **ricertificazione di P5**, che non passava
proprio per questo difetto. ⚠ E vuole prima la cura della sua scena — `01-p5-lancia.sh` chiude
ancora `ctrl+w` **sull'unica scheda**, dove Firefox **esce** e non esce niente per nessuna via: senza
quella cura il giro nuovo sarebbe rosso per la scena, non per il prodotto.

> ### ⭐ E la stessa notte la regola ha retto una SECONDA volta — il posto muto
>
> *Dall'utente, poche ore dopo, curando la scena di P5.* ⛔ `src/rcp.c` libera il posto in quattro
> punti e **tre** lo scrivono nel registro: sulla strada del `CONGEDO` — quella che **§8.1 impone**,
> cioè quella che il prodotto sano percorre sempre — il `posto LASCIATO` **non veniva scritto**.
>
> ⚠ Il posto si liberava davvero (`[M]` dodici sessioni, ogni `posto PRESO` successivo dice
> `occupati adesso: 1`): il difetto **non era una perdita, era che l'invariante §8.2 `0x0F` non si
> poteva più osservare**. ⇒ P5 giudica quel numero, non lo trovava, e avrebbe dato **un rosso a un
> server sano**.
>
> **La decisione è la stessa di §1.12, e per le stesse tre ragioni**: si cura nel prodotto (una riga
> di registro, identica alle tre sorelle), **fuori fase e dichiarata**, e la fase 1 resta a 12 su 14.
> ⭐ Le ragioni che la reggono qui sono anche più semplici: è **additiva** — scrive quel che già
> succede, non cambia un comportamento — e ripara un buco che rende **non verificabile** un'invariante
> che il documento di fase dichiara verificata.
>
> ⭐ **Misurata**: `[M]` due giri per motore, quattro su quattro `PRESO(1) → si congeda 0x01 →
> LASCIATO(0)`, e il giudice di P5 passa da **1 guasto falso** a **0**. ⛔ *E «zero guasti» non vuol
> dire «P5 certificato»: quel che è verde è il giudice su un segmento vero, non il giro di P5.*
>
> ⚠ **E il prezzo dichiarato**: il binario del prodotto è stato **ricostruito** sulla macchina di
> prova, e `RCP.md` §0-bis porta i numeri nuovi di `rcp.c` (2.592 righe, `md5` `1adce15b…`) — quella
> casella dichiara che `src/rcp.c` e `banchi/rcp/rcp.c` sono identici byte per byte, e a farlo
> rispettare è il `Makefile`, che li confronta a ogni costruzione.

*Conseguenze scritte: `fasi/01-filo-nudo.md` (riquadro P5 e la tabella dei difetti), `README.md` e
`RCP.md` §0-bis.*

---

### 1.13 ✅ ⭐ HEVC **con un ripiego negoziato**, non un requisito dichiarato

*12 agosto 2026, dall'utente, davanti alla misura della fase 2. La domanda gli è stata portata col
numero accanto, non come un'ipotesi.*

**Il fatto, `[M]` 12 agosto 2026** (sotto-fase **F2.5**, `fasi/rapporti/F2-5-pagina.md`):

| | schermo vero (GPU) | Xvfb (senza GPU) |
|---|---|---|
| **Chrome 151** | ⭐ HEVC arriva al pixel, 8 celle su 8 | ⛔ **zero** |
| **Firefox 140 ESR** | ⛔ **zero**, `NotSupportedError` | ⛔ **zero** |

⭐ **VP9 dipinge 8 su 8 in tutti e quattro i casi**: il «no» è di HEVC, non del banco. E la causa è
misurata: con `prefer-software` Chrome dice `Unsupported`, con `prefer-hardware` dipinge ⇒
**Chrome su Linux non ha un decodificatore HEVC software**, HEVC esiste **solo via VA-API**.
⛔ *Confermato una seconda volta, sul Chrome vero dell'utente, con controllo positivo (VP9, H.264) e
negativo (un codec inventato).*

**La decisione.** ⛔ **Non si dichiara un requisito** *«serve Chrome con VA-API»*: **il codec si
negozia, e il ripiego si dichiara**. È quel che impone `CODER.md` §4.2 — *ogni dipendenza mancante
ha un ripiego, il servizio funziona comunque con meno, e il ripiego si dichiara* — e quel che
protegge la promessa di `DECISIONI.md` §1.6: *nessun client da installare, basta un browser
moderno*.

⭐ **E il meccanismo esiste già**: `RCP.md` §4.3 negozia `video.codec` e §6.2 porta il campo `codec`.
Non serve una riga nuova di protocollo — cioè **§9 non viene toccata**.

> ### 🔸 E il secondo codec è **AV1** — chiuso lo stesso giorno, su una misura
>
> *Conseguenza scritta da me, non pronunciata dall'utente: lui ha deciso **che ci sia** un ripiego;
> **quale** l'ha deciso il numero. Si corregge senza discussione (§1.5).*
>
> ⛔ **La domanda era vera, e il documento si era messo di traverso a sé stesso**: in RCP/1 i valori
> ammessi di `video.codec` sono **`hevc`** e **`av1`**, e `vp9` compare in §4.3 come **l'esempio
> canonico di valore che un'implementazione RCP/1 deve IGNORARE** ⇒ VP9 avrebbe voluto dire **aprire
> RCP/2**, mentre AV1 è già normativo e ha già il suo `codec = 2`. ⚠ Ma «AV1 è supportato ovunque»
> era una **deduzione**, e qui una deduzione presa per misura si è già pagata tre volte.
>
> **`[M]` 12 agosto 2026, F2.5** — quattro caselle su quattro, coi sei controlli del banco verdi in
> tutti e quattro i giri:
>
> | | Chrome vero | Firefox vero | Chrome Xvfb | Firefox Xvfb |
> |---|---|---|---|---|
> | **AV1 8 bit** | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 |
> | **AV1 10 bit** | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 | ⭐ 8/8 |
> | *(confronto)* **HEVC Main10** | 8/8 | ⛔ zero | ⛔ zero | ⛔ zero |
>
> ⭐ **AV1 riempie esattamente le tre caselle che HEVC lascia vuote**, e ⛔ **regge in software**:
> `prefer-software` dipinge 8/8 in tutte e quattro, a 8 e a 10 bit. ⇒ **è un ripiego vero, non un
> secondo requisito travestito.**
>
> ⭐⭐ **E i 10 bit li conserva, per la prima volta osservabili**: su Chrome un flusso a 10 bit veri
> dà `VideoFrame.format` = **`I420P10`**, `copyTo` su tre piani a 16 bit, **massimo del luma 870** —
> impossibile a 8 bit. È il **caso positivo** che la tabella del caso opposto non aveva mai potuto
> riempire: con HEVC in hardware il formato era `BGRA` e la domanda restava muta. ⚠ Su Firefox i 10
> bit **arrivano** (sfumatura a 210 livelli) ma **non sono osservabili**: il formato è `BGRX` per
> tutto. La domanda ha risposta **motore per motore**.
>
> **Le stringhe**: `av01.0.04M.08` e `av01.0.04M.10`, coi numeri letti dal flusso. ⚠ `seq_level_idx
> = 4` **non è «livello 4»: è il 3.0** — nella stringa va l'indice. ⭐ E **nessuna `description`**:
> AV1 prende le unità temporali di OBU così come sono, cioè **una cucitura in meno** rispetto alla
> coppia `hvcC`/Annex-B di HEVC.
>
> ⛔ **La scala di preferenza NON si rovescia**: l'ordine resta **`hevc,av1`**. Questa misura riempie
> il secondo posto, non il primo — HEVC resta il codec principale perché è quello che il telefono
> decodifica in hardware, ed è la domanda **S2**, ancora aperta.
>
> ⇒ ⭐ **`RCP.md` non si tocca**: `av1` era già fra i valori ammessi di §4.3 e ha già `codec = 2` in
> §6.2. La decisione dell'utente si realizza **senza una riga di protocollo nuova**, cioè senza
> sfiorare §9.
>
> **Le `[?]` che restano, e sono del ripiego, non della scelta**: il **ritmo** di AV1 in software
> (⛔ *è la domanda che decide se il ripiego è usabile o solo esistente*); il costo in banda contro
> HEVC; AV1 su Android/DeX e su Safari (manca il dispositivo — forma **E10**); e ⚠ perché **Firefox
> accetti `prefer-hardware` e dipinga** dove `vainfo` non elenca nessun entrypoint di decodifica AV1
> `[M]` — o ha una strada che VA-API non dichiara, o **ripiega in silenzio** (forma **E2**). Non è
> misurato quale, e non si scrive come se lo fosse.

*Conseguenze scritte: `fasi/02-primo-fotogramma.md`. ⭐ `RCP.md` **non richiede modifiche**.*

> ### ⭐⭐⭐ 1.13-bis — **AV1 NON PUÒ ANDARE IN HARDWARE**, e la scala di preferenza ne esce rafforzata
>
> *13 agosto 2026, sera, a codice fermo. ⛔ **Non è una decisione dell'utente: è un vincolo della
> macchina**, misurato. Si scrive qui perché cambia il peso di una decisione già presa, non il suo
> verso.*
>
> **`[M]` sul server, 3 giri su 3**, con l'esito letto dal **codice d'uscita** e non dalla prosa:
>
> ```
> av1_vaapi   ⛔ USCITA 218   «No usable encoding profile found»
> ```
>
> ⭐ **E la causa è nell'hardware, non in `ffmpeg`**: `vainfo` dà `VAProfileAV1Profile0 :
> VAEntrypointVLD` su `renderD129` e **niente AV1 affatto** su `renderD128` ⇒ **solo decodifica**.
> ⚠ `av1_vaapi` **compare** nell'elenco dei codificatori di `ffmpeg`: chi si fidasse dell'elenco
> invece di un giro butterebbe una consegna. *Un elenco dice che il codice c'è, non che la macchina
> lo sa fare.*
>
> | codificatore, 1920×1080 10 bit, **20 Mbit/s per tutti**, 120 fotogrammi contati in uscita | ms/fotogramma |
> |---|---|
> | ⭐ **hevc_vaapi** | **3,16 – 3,24** |
> | h264_vaapi | 3,11 – 3,16 |
> | vp9_vaapi profilo 2 | 6,95 – 7,28 |
> | ⛔ **av1_vaapi** | **non esiste** |
> | *(software)* libsvtav1 preset 10, sul numero della fase 3 | **22,23** |
>
> ⇒ ⛔⛔ **Restare su AV1 vuol dire restare in software per sempre**, su questa macchina. La riga
> *«la scala di preferenza NON si rovescia: l'ordine resta `hevc,av1`»* era stata scritta per una
> ragione (il telefono) e ⭐ **adesso ne ha una seconda, più forte**: **HEVC è l'unica strada verso
> l'hardware sul lato server.**
>
> ⛔ **E la riga che rendeva HEVC irraggiungibile è SMENTITA.** Era scritto qui sopra: *«Chrome su
> Xvfb: HEVC zero»*. `[M]` **la causa era la bandiera `--disable-gpu` del banco**, non il palco:
> senza quella, lo stesso Chrome sullo stesso Xvfb vede la GPU (`ANGLE (Intel, Mesa Intel(R)
> Graphics (ADL-N))`) e ⭐ **dipinge un flusso HEVC Main10 uscito da `hevc_vaapi`: 5 giri su 5,
> 1920×1080, 119 fotogrammi su 120, `powerEfficient: true`**.
> ⚠ **Quel che NON è smentito, e resta vero**: *Chrome su Linux non ha un decodificatore HEVC
> software* — HEVC esiste **solo via VA-API**. È **esattamente per questo** che il ripiego AV1
> **resta necessario** e la decisione dell'utente **non si tocca**: su un client senza VA-API per
> HEVC il ripiego è l'unica cosa che tiene in piedi la promessa di §1.6.
>
> ⭐⭐ **E LA `[?]` È STATA CHIUSA LA SERA STESSA, PRIMA DEL LAVORO GROSSO.** Era: *«il flusso è
> stato dipinto per la strada `<video>`, e il prodotto usa WebCodecs `VideoDecoder`»*.
> `[M]` **120 `VideoFrame` su 120 unità d'accesso, 5 giri su 5, su tutt'e due le strade di
> confezionamento** (Annex-B senza `description`, e `hvcC` demuxato dall'mp4) — fotogrammi contati
> all'uscita del *callback*, non dichiarati. HEVC è anche **il più veloce dei sei flussi provati**, e
> restituisce `VideoFrame.format: null`, cioè **fotogrammi opachi che stanno sulla GPU**.
> ⭐ Il controllo negativo separa netto: con `--disable-gpu` HEVC dà **zero** 5 volte su 5 e gli
> altri quattro flussi 120. ⚠ **Firefox headless** dà una risposta vera e diversa: positivi verdi,
> HEVC **`NotSupportedError` 5 su 5** ⇒ il ripiego AV1 **serve davvero**, e adesso è misurato invece
> che temuto.
>
> ⛔ **E una correzione al numero di due ore prima**: il *«119 fotogrammi su 120»* di `<video>` era
> **un artefatto del CONTENITORE, non del codec** — l'mp4 porta una *edit list* che salta 2,4
> fotogrammi in testa. Il flusso ne ha **120**, e tre fonti indipendenti lo dicono: `ffmpeg`
> dall'mp4 ne conta **118**, dallo stesso flusso in Annex-B **120**, `<video>` **119**,
> `VideoDecoder` — che contenitore non ne ha — **tutti e 120**. ⇒ Seconda ragione, indipendente, per
> cui la misura con `<video>` non bastava: **non contava nemmeno la stessa cosa.**
>
> ⭐⭐ **E anche QUESTA è stata chiusa, un'ora dopo, dalla corsia B**: i pacchetti versati dal
> **nostro** codificatore, col confine letto dalla lunghezza — *il prodotto non spezza niente, il
> confine è già scritto* — danno **120 fotogrammi su 120, 3 giri su 3**, `format: null`; controllo
> negativo con `--disable-gpu` → **0**.
>
> ---
>
> ### ⛔⛔⛔ E LA RAGIONE PER CUI SI NEGOZIAVA `codec 2` NON ERA NESSUNA DI QUELLE CERCATE
>
> *13 agosto 2026, notte. **Il prodotto ha codificato in software per giorni per una riga di un
> banco**, e ogni pezzo della catena rispondeva correttamente alla domanda che gli era stata fatta.*
>
> `banchi/02-pagina-sonda-codec.py:121` passava `-x265-params …:**keyint=1**:…`, e `keyint=1` fa
> emettere a libx265 **«Main 10 Intra» — Rext, `profile_idc = 4`** — ⛔ **annullando il
> `-profile:v main10` chiesto quattro righe sopra**. *Il profilo era stato chiesto e non applicato,
> senza un errore.* ⚠ Ed è la forma d'errore che **il commento di quello stesso file descrive**.
>
> Le due sonde finiscono **dentro `src/pagina.html`**, e la pagina le usa per decidere che cosa
> mettere nel `CIAO`:
>
> | pezzo | che cosa faceva | ed era giusto |
> |---|---|---|
> | la **stringa** dichiarata | `hev1.1.6…` / `hev1.2.4…` — profili **1** e **2** | sì, per quel che dichiarava |
> | i **byte** della sonda | `profile_idc = **4**` (Rext) | ⛔ no, e nessuno li leggeva |
> | `isConfigSupported` | **`true`** | sì: risponde **alla stringa** |
> | il decodificatore | `EncodingError` **sui byte** | sì |
> | `pagina.html` | *«HEVC non arriva al pixel»* ⇒ fuori dal `CIAO` | sì, dato quel che vedeva |
> | `rcp.c:1128` `prima_comune()` | prende la prima voce **dell'elenco del client** ⇒ `av1` = **2** | sì |
>
> ⭐ **La cura è di due righe** — tolto `keyint=1`, sonde rigenerate — **e il protocollo non si
> tocca**. `[M]` `ffprobe` dà adesso `profile=Main` e `profile=Main 10` (erano Rext), e
> `banchi/02-pagina-sonda-verifica.py` — che legge le sonde **dal file del prodotto** invece di
> ricopiarle e **conta i fotogrammi** — dà **4 su 4, 3 giri su 3**, con le due AV1 come controllo
> positivo. Prima: **zero fotogrammi**.
>
> ⛔ **La riga da portarsi via**: *chiedere non basta*. La stringa e il codec erano d'accordo **fra
> loro** e discordi **dal flusso**, e nessun controllo guardava i byte. ⇒ Quando si dichiara un
> formato, **si rilegge quel che si è prodotto** — è `CODER.md` §3.9 (*si chiede per nome e si
> verifica che sia stato dato*) applicato all'**uscita**, non solo all'ingresso.

---

## 2. I numeri

### 2.1 ✅ Minimo: 480p · 25 fps · 24 bit — ed è una garanzia, non un traguardo

*8 agosto 2026.*

Diceva «30 fps a 1080p», ed era il numero di v1 — che lo superava già `[M]`: la cattura di
Mutter consegnava 37 fotogrammi, KWin 60.

> ⛔ *13 agosto 2026: **il 37 non si riproduce**, e questa riga lo cita come se fosse un fatto
> stabile. Alla cadenza che chiedevamo Mutter consegna **31,5** con mediana 33,31 ms; rinegoziando
> la sola cadenza (monitor 120, freno 90) ne consegna `[M]` **61,4** (60,04). Il numero **non è una
> proprietà stabile di Mutter**, e la spiegazione più probabile — il resto di una divisione troncata
> — è `[R]`, non `[M]` (§2.5-bis). ⚠ Il **minimo** deciso qui non si tocca — resta lontanissimo in
> tutt'e due i casi.*

Il cambiamento è di **natura** più che di valore: il minimo smette di essere un'asticella da
inseguire e diventa il **livello sotto cui non si scende e non si stacca**, per quanto brutta
sia la linea. Nasce dal caso della rete mobile (§3.1), non da una rinuncia sulla qualità.

**Conseguenza già applicata** (`CODER.md` §1): la regola che governa le scelte tecniche è stata
sdoppiata, perché un'asticella che ogni scelta supera non filtra più niente. Verso l'alto
filtra il desiderato; verso il basso vincola il minimo.

### 2.2 ✅ Desiderato: 4K · 60 fps · 10 bit per canale

*8 agosto 2026. «direi che 10 bit è la scelta giusta».*

Diceva «profondità colore 32 bit», che non è una grandezza esistente: 32 bpp sono 24 bit di
colore più 8 di alfa, e l'alfa non si trasmette. L'intenzione dell'utente era *«massima
qualità»*, e sotto quella parola stavano due leve distinte:

| Leva | Cura | Prezzo |
|---|---|---|
| **10 bit per canale** | le strisce sulle sfumature | quasi nulla, e in hardware ovunque — decoder Android compreso |
| **4:4:4** | il testo colorato sfrangiato `[M]` v1 §5.2 | ~50 % di banda, **nessun decoder Android in hardware** |

Scelto il 10 bit: la massima qualità ottenibile **su entrambi i client insieme**, in hardware.

### 2.3-bis 🔸 ⛔ Il primo indizio contrario ai 10 bit, e viene da Android

*9 agosto 2026.* La documentazione di **mpv** riporta che sul percorso `mediacodec` di Android il
supporto a **10 bit è limitato, e l'uscita viene riportata a 8 bit**.

⚠ **Non è una prova**: è il percorso di mpv, non il nostro, e MediaCodec in generale non è quello.
Ma è **la prima cosa che punta contro il desiderato di §2.2**, e arriva dal lato dove non abbiamo
margine.

**Da cui la sonda della fase 2 chiede due cose invece di una**: che il telefono decodifichi HEVC
**Main10** in hardware, **e** che restituisca davvero 10 bit. La seconda può smentire §2.2, e
allora si rilegge lì.

### 2.3 🔸 Il 4:4:4 resta una `[?]`, non una promessa

Sarebbe un'opzione per il solo client Linux su GPU capaci — ⭐ **e sul nostro ferro la GPU capace
c'è**: `[M]` 9 agosto, l'Intel UHD 730 codifica **HEVC Main444 e Main444_10**, cioè 4:4:4 a 8
**e a 10 bit**, in hardware (la Radeon no). Il «Intel a volte» che questa riga diceva era una
`[?]`, e sul ferro di riferimento la risposta è **sì**.

⛔ **Ma non riapre la decisione, e va detto perché**: il 4:4:4 era stato messo da parte per il
lato **Android**, dove nessun decodificatore lo fa in hardware — e quel lato non è cambiato. Resta
quel che era: un'opzione per il solo client Linux, dietro un interruttore spento. Quel che cambia è
che ora **si può misurare senza comprare niente**.

Ma **nessuno ha misurato quanto si veda davvero la differenza** sul desktop dell'utente:
vale `LEZIONI.md` §2.3-quater. Si decide su un banco che metta le due immagini a confronto, e
a giudicare è l'utente (§7.3), dietro un interruttore spento di suo (§2.4).

> ⚠ **Riletta il 9 agosto 2026 dopo §1.6**: «un'opzione per il solo client Linux» non ha più un
> soggetto — i client sono spariti. La sostanza però non cambia, **cambia chi decide**: il 4:4:4
> resterebbe un'opzione per i **dispositivi il cui browser lo decodifica**, e questo lo si scopre
> **a runtime** invece che a tavolino. ⭐ È §2.7 in azione: il server offre il massimo, e chi non
> arriva riceve il 4:2:0 — **con la ragione dichiarata**, non in silenzio.

### 2.3-ter ⛔⛔ E il secondo indizio non è un indizio: **è una misura, ed è dalla nostra parte**

*`[M]` 12 agosto 2026, sotto-fase F2.2 della fase 2, sul ferro.*

⛔ **Dieci bit veri non escono dalla cattura di Mutter per NESSUNA strada.** Non è una deduzione
dal formato che ci capitava: sono state chieste **le due strade e i formati per nome**.

| | `[M]` |
|---|---|
| **in memoria (MemFd)** | solo **BGRx/BGRA** ⇒ 8 bit. Contati sulla sfumatura: **255/256/255 livelli distinti**, multipli di 4 a 0,26 |
| **DMA-BUF** | ⭐ Mutter **lo consegna** — 388 fotogrammi, 4 buffer, modificatore **LINEAR**, stride 7680 letto dal chunk — ⛔ **ma il formato è BGRx, 8 bit** |
| **chiedendo i formati a 10 bit da soli** | ⛔ `no more input formats`, **su tutt'e due le strade** |
| ⭐ **il controllo positivo** | BGRx chiesto allo stesso modo, sullo stesso binario, **riesce** ⇒ il «no» è del formato, non dello strumento |

⇒ ⛔ **Il desiderato di `SPECIFICHE.md` §3.1 — «10 bit per canale» — non è raggiungibile dalla
sorgente**, e non per una scelta nostra. `Main10` da qui significa **otto bit promossi a dieci**, e
l'etichetta continuerebbe a dirlo per tutta la catena senza che nessuno se ne accorga: l'immagine
viene bene lo stesso.

⚠ **E non è un muro** (§2.7): il massimo lo offre il server, l'altezza la mette il client. ⛔ **Ma
adesso il tetto è a monte**, non a valle — e va dichiarato all'utente come tale, non taciuto.
⭐ Quel che resta aperto non è più *«il nostro codice sa fare 10 bit?»* ma **«esiste una sorgente che
ce li dia?»**: è una domanda per il compositore, e vive nelle fasi in cui la cattura si tocca.

⭐ *E la previsione era stata scritta prima: F2.3 aveva messo a verbale «se la cattura dà 8 bit, tutta
la catena resta verde e l'etichetta dice Main10 lo stesso» come rischio da misurare. F2.2 ha
risposto: **è una certezza, e l'imputato sono io**.*

### 2.4 ✅ Il ritardo: 50 ms di tetto, 40 di traguardo — e solo per il pezzo che è nostro

*9 agosto 2026. «Per quello che è sotto il nostro controllo 50 ms (o anche 40) va bene, su
altre cose non possiamo agire».*

È il **terzo numero**, e prima di oggi non esisteva: né `SPECIFICHE.md` né la specifica di v1
nominavano la latenza, che è la grandezza che decide se un desktop remoto è piacevole. Trenta
fotogrammi con 40 ms si usano benissimo; sessanta con 200 ms sono insopportabili.

| | Dall'input che arriva al fotogramma che parte |
|---|---|
| **TETTO** | 50 ms |
| **TRAGUARDO** | 40 ms |

**Si misura solo il pezzo nostro**, e la ragione è che un requisito che si può fallire senza
aver sbagliato niente — per colpa di una galleria — non viene misurato da nessuno. Il totale
che l'utente sente è questo più la rete: si dichiara, non si promette.

*Scritto in `CODER.md` §1-bis, accanto agli altri due numeri.*

⛔ **13 agosto 2026 — il numero è stato misurato, e sfora**: `[M]` mediana **74,58 ms** cattura →
vetro, pezzo cieco 16-40 ms escluso (§2.5 e `SPECIFICHE.md` §3.2). ⛔ **E il muro dei 37 fotogrammi
di Mutter non ne è la causa**: Mutter vale il **22 %**, il **78 % è nostro** e quasi tutto sta nel
codificatore in software. La decisione dell'utente resta questa; cambia da chi si va a prendere i
millisecondi.
⛔ **E «il pezzo che è nostro» adesso ha un confine dichiarato**: la misura finisce al **disegno
finito**, non al richiamo del decodificatore. Sono **11 ms su 50** che la prima stesura si
regalava, ed è la parte che si dà volentieri via senza accorgersene.

### 2.5 🔸 ⛔⛔ Il traguardo dei 40 ms su GNOME — **MISURATO il 13 agosto, e la causa NON era Mutter**

*⛔ Questa voce si intitolava «Il traguardo dei 40 ms non è raggiungibile su GNOME — stesso muro dei
60 fps», e attribuiva il ritardo al muro dei 37 fotogrammi della cattura. **Il ritardo è stato
misurato alla fase 3, e sfora — ma per il 78 % è nostro.** Il conto qui sotto è tenuto perché era
la stima su cui la decisione è stata presa; la correzione è nel riquadro in fondo, e vale più della
stima.*

Il conto, sommando i pezzi che v1 ha misurato:

| | GNOME (Mutter) | KDE (KWin) |
|---|---|---|
| il desktop reagisce e ridisegna | ~16 ms | ~16 ms |
| **la cattura ci consegna il fotogramma** | **~27 ms** (37 al secondo `[M]`) | **~16 ms** (60 al secondo `[M]`) |
| la codifica | 3-6 ms `[M]` fase 9 | 3-6 ms |
| **totale** | **~48 ms** — dentro il tetto, fuori dal traguardo | **~37 ms** — dentro tutti e due |

⭐ **È lo stesso muro dei 60 fotogrammi a 4K, e per la stessa ragione**: Mutter consegna sei
decimi di quel che gli si chiede (`LEZIONI.md` §3, domanda 6). Il tetto del ritardo, come quello
del ritmo, **in buona parte lo pone il compositore**.

> ⭐ **E il «nessuna leva nostra lo sposta» che questa voce diceva è stato tolto il 9 agosto
> 2026.** `gnome.md` §8.2 ha trovato la causa dei sei decimi `[R]`: `maxFramerate` fa **due
> mestieri insieme** — freno della cattura e frequenza del monitor virtuale — e due orologi allo
> stesso numero battono fra loro. Da cui un candidato che costa **tre celle e zero righe di
> prodotto**: negoziare alto e poi rinegoziare **la sola cadenza**, a monitor fermo.
>
> ⚠ **Non cambia la decisione**, che è dell'utente e sta sui numeri: 50 di tetto, 40 di
> traguardo. Cambia che il traguardo **non si dà più per perso su GNOME prima di aver provato**,
> e la prova va fatta presto — se riesce, tutta la riga della cattura in questa tabella scende da
> ~27 ms a ~16, e GNOME entra nel traguardo come KDE.

⚠⚠ **E questa tabella è una stima, non una misura — marcata `[?]`.** È la somma di componenti
misurati separatamente, che è *precisamente* ciò contro cui mette in guardia `LEZIONI.md` §1.7:
sommare i registri di chi manda non dice che il byte è arrivato. Serve per orientarsi, **non per
concludere**. Il numero vero lo dà il banco di 2.6, e può smentirla.

> ## ⛔⛔ 13 agosto 2026 — il banco di §2.6 ha parlato, e ha smentito la tabella qui sopra
>
> *Fase 3, step 5. La stima diceva **~48 ms** e dava la colpa alla cattura di Mutter. La misura dice
> **74,58** e dà la colpa a noi. La previsione era sbagliata in tutt'e due i modi: nel numero e
> nell'imputato.*
>
> `[M]` **ritardo cattura → vetro, mediana 74,58 ms** — min 50,4 · p05 58,1 · p95 101,2 · p99
> 138,1, 6 giri da ~800 campioni, errore d'orologio **±0,63 ms**, banco `banchi/03-b17-ritardo.py`
> (31 controlli su 31, ponte 11 su 11). ⛔ **Pezzo cieco 16-40 ms non compreso** ⇒ sullo schermo
> dell'utente **90-115 ms**. ⇒ **Si sfora il tetto dei 50, non solo il traguardo dei 40.**
> ⚠ Non è input → vetro: il canale di input nasce alla fase 4 (`input` = 0 in 953 su 953), e al suo
> posto sta il controllo **P1**.
>
> | dove se ne va | mediana | di chi è |
> |---|---|---|
> | disegno → cattura (il `pts` di Mutter) | 16,66 ms | Mutter — **22 %** |
> | ⛔ **cattura → primo byte in pagina** | **39,17 ms** | ⛔ **nostro** — codificatore in software |
> | il filo | 0,32 ms | — |
> | stream completo → `decode()` | 0,08 ms | nostro |
> | decodifica | 7,58 ms | nostro |
> | richiamo → disegno finito | 10,51 ms | nostro |
>
> ⛔⛔ **Il muro NON è di Mutter, e le tre prove sono queste**: la scena disegna **59,98/s con 0
> attese**; il figlio del prodotto consegna **23,93/s con ZERO attese a vuoto** — *non aspetta mai
> Mutter*; il codificatore è **in software** e lo dichiara il prodotto stesso (libsvtav1 /
> libx265). ⇒ **58 ms su 74,6 sono nostri, il 78 %**, ~39 nel solo tratto cattura→filo.
>
> ⛔ **E il muro dei 37 non si riproduce.** Con monitor a **120** e freno **90**: `[M]` **61,4
> fotogrammi consegnati al secondo** (60,04), intervallo mediano **16,66 ms**. E i «sei decimi» non
> si riproducono nemmeno: la cella bassa dà **0,50 pulito**. ⚠ Il riquadro qui sopra dava la causa
> dei sei decimi come **battimento** fra due orologi allo stesso numero: è sbagliata anche quella, e
> al suo posto c'è una **quantizzazione** sui tick — `min_interval_us = 10⁶/maxFramerate` **troncato
> a intero** (16666 per 60) contro un tick da 16666,67 µs ⇒ chi cade sotto perde un tick intero.
> ⛔ **Ma la quantizzazione è `[R]`, letta nel codice di Mutter, non `[M]`.**
>
> > ⛔ ⚠ *Questo capoverso diceva «Legge verificata su **13 punti**, 8 confermano, **0 la
> > smentiscono**». **È falso**: il file degli esiti della griglia,
> > `banchi/03-b14-esiti-griglia.jsonl`, porta **tre righe** — il terreno e **due celle**, tutt'e
> > due con `scena_sul_mio_monitor: false` ⇒ rifiutate dal banco stesso, che stampa «⛔ la legge NON
> > regge su **0 punti su 0**». **Corretto il 13 agosto 2026**, rilievo del coordinatore della
> > fase 3, verificato sui due file di esiti. ⇒ Restano `[M]` il **61,4** e lo **0,50**, che vengono
> > dalle celle pulite di `03-b14-esiti.jsonl`; **cade la legge**, e con lei la chiusura di M3
> > (`gnome.md` §13).*
>
> ⛔⛔ **Ma quella cura il prodotto oggi non la sa chiedere**, e va scritto qui o si scambia una
> misura di banco per una prestazione: `MOVIMENTO_FPS 60` è una **costante di compilazione**
> (`src/figlio.c:1465`), `main.c` non ha nessuna opzione di cadenza, e **`RecordVirtual` non prende
> la frequenza** (`src/mutter.h:82`) — i quattro monitor virtuali sono tutti **1920×1080@60**. ⇒ Il
> «monitor 120 / freno 90» è **`[M]` sul banco e zero in produzione**.
>
> ⚠ **E il 60 non è il 40 ms**: la cadenza non è il ritardo (`LEZIONI.md` §6.2). I 60 fotogrammi
> tolgono un ostacolo; il numero lo fa il ritardo, ed è quello qui sopra.
>
> ⇒ ⛔ **Che cosa cambia per le decisioni**: la decisione dell'utente (50 di tetto, 40 di traguardo,
> e solo per il pezzo nostro) **non si tocca** — è sua, e sta sui numeri. Cambia **l'imputato**: il
> ritardo non si cura cambiando compositore, si cura **sulla codifica**, che è la fase 8. E cade la
> frase *«se la misura lo confermasse non è un difetto nostro»*: la misura ha confermato lo sforo e
> ha detto che **il difetto è nostro**.

### 2.5-bis ✅ Il tetto di Mutter è accettato: su GNOME il desiderato non si promette

*9 agosto 2026, alla chiusura della fase 0, guardando i numeri misurati.* «Sappiamo che tra tutti i
compositor dei 4 DE Mutter è quello che performa peggio […] GNOME non è in grado di garantire 4K/60
fps, ma va bene. Non sarà adatto per il gaming ma consente comunque una soddisfacente esperienza
desktop e multimedia.»

`[M]` 9 agosto: **36 ± 2 fotogrammi al secondo** su sei giri (33,7-37,8), scena dichiarata,
1080p, copia zero — mentre il client ne disegna **60**. Il tetto è del compositore.

| | |
|---|---|
| **il minimo** (`§2.1`) | lontanissimo, mai in discussione |
| **il desiderato** (`§2.2`) | ⛔ **su GNOME non si promette**. Resta il traguardo dove il compositore lo consente — KWin consegna 58,9 `[M]` sulla stessa macchina, nello stesso pomeriggio |
| il gaming | **fuori**, e non era mai stato dentro |

⚠ **Due cose che questa decisione NON dice**, e vanno tenute accanto o si attribuisce il tetto alla
cosa sbagliata:

1. ⛔ **non è un limite del 4K.** Il costo della risoluzione sulla cattura di Mutter è **zero** fino
   a 4K (`LEZIONI.md` §3, domanda 10): i 36 sono a 1080p, e a 4K sono gli stessi. «GNOME consegna
   ~36 a qualunque misura» è la frase giusta;
2. ⏳ **non chiude M3.** La firma degli intervalli misurata oggi — mediana 33,3 ms, minimo 16,2, mai
   valori intermedi — è quella di due orologi a 60 che battono fra loro, cioè la lettura di
   `gnome.md` §8.2. La cura candidata costa **zero righe di prodotto** ed è nella fase 3. Se
   riuscisse, questa voce si riscrive.

> ### ⚠ 13 agosto 2026 — **M3 riesce nel fatto, e questa voce va rimessa in discussione**
>
> *Punto 2 qui sopra: «se riuscisse, questa voce si riscrive». Il fatto è riuscito — ⛔ ma **M3 non
> è chiusa**: la causa non è misurata (`gnome.md` §13).*
>
> ⭐ **Il tetto non è del compositore, e la prova è `[M]`**: alla cadenza disaccoppiata GNOME
> consegna **61,4** invece di 31,5, sulla stessa macchina e con la stessa scena.
>
> ⚠ **Il perché è `[R]`**: nel codice di Mutter il freno calcola
> `min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) contro un tick da
> 16666,67 µs ⇒ chi cade sotto perderebbe un tick intero. Non un battimento fra due orologi, una
> **quantizzazione**. ⚠ E la firma «mediana 33,3, minimo 16,2, mai valori intermedi» è quel che una
> griglia produce e due orologi in battimento no — ⛔ **ma è un indizio coerente, non una legge
> misurata**.
>
> > ⛔ ⚠ *Questo capoverso diceva: «è una **quantizzazione**, legge verificata su **13 punti** (8
> > confermano, 0 smentiscono)». **È falso.** `banchi/03-b14-esiti-griglia.jsonl` ha **due sole
> > celle**, tutt'e due con `scena_sul_mio_monitor: false`, e il banco stampa «⛔ la legge NON regge
> > su **0 punti su 0**». **Corretto il 13 agosto 2026**, rilievo del coordinatore della fase 3.*
>
> | monitor | freno | consegnati | mediana | p99 | cella |
> |---|---|---|---|---|---|
> | 60 | 60 | 31,5 | 33,31 ms | 35,53 | **A** |
> | 120 | 120 | 82,9 | 12,12 ms | 18,53 | **B** |
> | 120 | 60 | 46,13 | 24,12 ms | 29,23 | **C** |
> | ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 | ⭐ **D** |
>
> *Le quattro celle vengono da `banchi/03-b14-esiti.jsonl`, tutte con `scena_sul_mio_monitor: true`
> e coi tre controlli — positivo, negativo, ritorno — che chiudono.*
>
> ⇒ ⛔ **Il «36 ± 2» resta vero alla cadenza che chiedevamo, e smette di essere un muro del
> compositore.** Alla cadenza disaccoppiata GNOME consegna **61,4**, cioè quanto KWin. ⚠ E i «sei
> decimi» **non si riproducono**: la cella bassa dà **0,50 pulito e deterministico**.
>
> ⛔⛔ **Ma la decisione dell'utente NON cambia oggi, e la ragione è che il prodotto non sa
> chiedere quella cadenza**: `MOVIMENTO_FPS 60` è una costante di compilazione (`src/figlio.c:1465`),
> `main.c` non ha opzioni di cadenza, `RecordVirtual` non prende la frequenza (`src/mutter.h:82`) e
> i quattro monitor virtuali sono tutti **@60**. ⇒ Il 61,4 è `[M]` **sul banco** e **zero in
> produzione**. Finché resta così, *«su GNOME il desiderato non si promette»* regge — ⛔ **ma la
> ragione è cambiata: non è più «Mutter non ce la fa», è «noi non gliela chiediamo».** Sono due
> frasi con cure opposte, e la seconda è nostra.
>
> ⚠ **E il ritmo non è il ritardo**: questa voce parla di fotogrammi al secondo. Il ritardo è §2.5,
> sfora, e per il 78 % è nostro (`LEZIONI.md` §6.2).

### 2.7 ✅ ⭐ Il massimo lo offre il server; l'altezza la mette il client

*9 agosto 2026, sul client web. «Meglio così, vorrà dire che una parte delle performance non sarà
più nostro compito. Remotix offrirà il massimo, sarà il client a dover essere all'altezza».*

⭐ **È la regola di §2.4 estesa a una seconda grandezza.** Lì l'utente aveva già stabilito che **si
promette solo il pezzo che è nostro** — la rete non è nostra, quindi si dichiara e non si promette.
Qui lo stesso criterio passa alla **decodifica**: il browser e il silicio del dispositivo non sono
nostri.

| | Di chi è |
|---|---|
| produrre fotogrammi buoni, in tempo, e spingerli sul filo | ⭐ **nostro, e ci si misura** |
| decodificarli e dipingerli | del **dispositivo**: si misura, si dichiara, **non si promette** |

⛔ **E questo toglie alla sonda del browser il potere di uccidere il progetto** (§1.6): se un
telefono decodificasse HEVC in software, non è un difetto di REMOTIX ed è un fatto da scrivere —
non un muro come quello di v1, dove il client lento **era il nostro**.

⚠ **Il confine, e va scritto adesso perché non diventi un alibi**, sono tre righe:

1. ⛔ **il minimo garantito resta una promessa nostra** (§2.1: 480p·25·24 bit), ma è una promessa su
   quel che il **server consegna sulla linea** — non su quel che un browser riesce a dipingere. Un
   client che non tiene il minimo va **detto**, non subìto in silenzio;
2. ⛔ **un ripiego silenzioso resta vietato** (`CODER.md` §4.2): «il client non ce la fa» è
   un'informazione che l'utente deve **vedere**, con la ragione. Due comportamenti sotto la stessa
   etichetta sono la forma d'errore **E2** anche quando la colpa è di qualcun altro;
3. ⚠ **e non ci esonera dal misurare.** «Non è compito nostro» vale per **promettere**, non per
   **sapere**: senza la misura non sapremmo nemmeno che cosa dichiarare, e `LEZIONI.md` §7.4 dice
   che le previsioni non contano — nemmeno quelle che ci fanno comodo.

### 2.6 🔸 Il banco della latenza esiste solo perché il client è nostro

Misurare il ritardo di un desktop remoto richiede di solito **una telecamera** che filma lo
schermo con un cronometro sopra. Qui no: l'input lo iniettiamo noi **e** il client lo scriviamo
noi.

**L'anello chiuso**: il client manda un input che provoca un cambiamento visivo enorme e
inequivocabile — lo schermo che cambia colore — e poi **guarda i fotogrammi che decodifica**
finché non vede il colore nuovo. La differenza fra i due istanti è la latenza vera, misurata
**dal lato che riceve** — la lezione che a v1 è costata tre fasi (`LEZIONI.md` §1.7).

Automatico, ripetibile, senza telecamere e senza nessuno che guardi. È il caso concreto di quel
che l'utente aveva osservato l'8 agosto: possedere il client non toglie solo lezioni, ne rende
alcune **molto più economiche da rispettare**.

> ✅ **Sopravvive intatto al client web** *(9 agosto 2026, §1.6)*: la pagina la scriviamo noi, quindi
> l'anello si chiude come prima — inietta l'input e guarda i fotogrammi che `VideoDecoder` le
> consegna. ⭐ E in dote arriva una cosa che con due client nativi non avevamo: **lo stesso banco
> gira su ogni dispositivo che ha un browser**, telefono compreso, senza compilare niente.

### 2.8 ✅ ⛔ La **tela** non va nel worker — la **decodifica** sì. *Attuato, misurato, tenuto spento*

*13 agosto 2026, fase 3. ⛔ Questa non è una prescrizione rinviata: è una prescrizione **eseguita**.
`web.md` §6.1 diceva «WebTransport, decodifica e canvas tutti in un worker dedicato», come strada
migliore. È stata scritta, misurata — e ⭐ **la misura l'ha spaccata in due**, non bocciata in
blocco.*

| tratto (mediana, ms) | prima | dopo | Δ |
|---|---|---|---|
| stream completo → `decode()` | 0,07 / 0,06 | **10,23** | ⛔ **+10,2** |
| ⭐ **la decodifica** | **7,17** / 6,13 | ⭐ **3,73** | ⭐ **−3,44 / −2,40** |
| richiamo → disegno finito ⚠ *(vedi la nota sotto: il nome del tratto è stato corretto)* | 9,63 / 9,11 | **27,19** | ⛔ **+17,6** |
| **mediana disegno → vetro** | 73,66 / 67,79 | ⛔ **101,30** | ⛔ **+27,6 / +33,5** |

> ### ⛔⛔ 14 agosto 2026 — **IL TRATTO «richiamo → disegno finito» PORTAVA UN NOME SBAGLIATO**
>
> *Corretto per decisione dell'utente, su due misure indipendenti della fase 4
> (`fasi/rapporti/F4-A2-pagina-dipinge.md`, `F4-A10-anello-input.md`), arrivate alla stessa
> conclusione da due lati senza mettersi d'accordo.*
>
> ⭐ **I numeri restano**; ⛔ **il nome no.** `[M]` il disegno vero costa **2,25 ms**: quel tratto
> misurava **l'attesa del fotogramma dalla GPU più il disegno**, perché un fotogramma HEVC
> decodificato in hardware esce **opaco** (`format = null`) e la rilettura della marca ne provoca il
> trasferimento GPU→CPU. ⭐ La prova che il confine era messo male: a **palco identico**, cambiando
> codec, «decodifica» e «disegno» si muovono in **versi opposti** e la somma si conserva — ma
> `drawImage` **non sa quale codec** ha prodotto il fotogramma.
>
> ⇒ ⭐ **La lezione, e vale oltre questo tratto**: una riga di scomposizione porta **un numero e un
> nome**. Il numero era `[M]`; il nome era **dedotto** — e nessuna marca distingueva le due metà
> della stessa riga.

⭐⭐ **La decisione, e non è «niente worker»: è DOVE passa il confine.**

| | |
|---|---|
| ⭐ **la decodifica fuori dal thread principale** | ✅ **vale** `[M]` **−3,44 ms** — il decodificatore consegna prima quando non contende |
| ⛔ **la tela fuori dal thread principale** | ⛔ **affonda il conto**: da sola **+17,6 ms**, più i +10,2 della consegna |

⛔ **Il meccanismo, ed è la parte che vale oltre questo caso**: una `OffscreenCanvas` in un worker
**si consegna al ritmo del quadro** — un `requestAnimationFrame` implicito che nessuno ha scritto.
`transferControlToOffscreen` impegna al quadro **da sé**. ⇒ Il divieto di `web.md` §6.1 non è sulla
parola: **è sul meccanismo**. ⛔⛔ E la prescrizione **conteneva la propria smentita**: prescriveva
il worker e vietava il salto di quadro, che il worker reintroduce in silenzio.

⚠ **E i fotogrammi dipinti dicono il contrario del ritardo, quindi vanno accanto** (`LEZIONI.md`
§6.2): sulla catena vera il worker dipinge **di più** (26,3/s contro 22,8-24,2), ma a saturazione il
tetto **crolla di tre quarti** — 127,6 → **33,9**/s a 1080p, 230,6 → **56,4**/s a 480p, cioè **≈ il
quadro dei 60 Hz**.

⇒ **Che cosa si decide oggi**: il codice resta in albero **dietro `#video=worker`, spento**. ⛔ **E
non è una bocciatura definitiva.** ⏳ `[?]` **il limite più grosso, e va letto accanto ai numeri**:
tutto è misurato su **Xvfb, in software, senza GPU**, e la penale è in gran parte sincronizzazione
al quadro. ⇒ **Su hardware vero il conto va rifatto prima di seppellire §6.1** — ed è la ragione
per cui il codice **non** è stato tolto: il giorno della GPU vera il numero si rifà senza
riscrivere niente.

---

## 3. La rete e la degradazione

### 3.1 ✅ I 30 Mbps non sono un pavimento: sono uno scenario

*8 agosto 2026. «il server deve poter fare il suo meglio per offrire la migliore esperienza
possibile a client che si collegano da connessioni critiche (come da una rete mobile).
Ovviamente non pretendo i miracoli come 4K a 300 kbps».*

Scritti come «banda minima 30 mbps» dicevano al programmatore l'opposto dell'intenzione — che
sotto i 30 non si va. Il requisito vero è **l'adattamento**, non una soglia.

Gli scenari da servire:

| Collegamento | Banda | Ritardo e perdita | Che cosa fa il server |
|---|---|---|---|
| fisso buono | 30+ Mbps | bassi | punta al desiderato |
| fisso modesto, WiFi | 5–15 Mbps | medi | **spende tutto quel che c'è** |
| mobile critico | < 2 Mbps, variabile | alti, con perdita | tiene il minimo, **e non stacca** |

### 3.2 🔸 L'invariante I1, riscritta

Il ritmo **non cala mai** per prudenza, per risparmio o perché la scena è ferma. Cala **solo**
quando la misura dimostra che la linea non porta, e ogni discesa è dichiarata nel registro.

La ferita della fase 10 di v1 resta protetta — il divieto di risparmiare è intatto — ma non
impedisce più di cedere quando cedere è l'unica cosa sensata. Vietata l'euristica prudente,
obbligatorio l'adattamento misurato.

*Applicata in `CODER.md` §2 e `REVIEWER.md` §3, che vanno in coppia.*

### 3.3 ✅ Sotto il minimo si calano i fotogrammi. Mai sgranare, mai staccare.

*8 agosto 2026. «continuare a calare i fotogrammi, mai staccare».*

Su un desktop **degradare nel tempo è meglio che degradare nello spazio**: a pochi fotogrammi
al secondo ognuno resta nitido e il testo si legge — è lento ma ci si lavora. Sgranando
l'immagine il testo diventa illeggibile e non ci si fa più niente. E a ritmo basso si possono
spendere più bit su ciascun fotogramma: la lentezza si paga una volta sola.

### 3.4 🔸 «Segni di vita» si verifica dal lato che riceve

Un client è vivo se **arrivano suoi pacchetti**, non se noi non abbiamo ricevuto errori
(`LEZIONI.md` §1.7). QUIC lo fa di suo, col proprio battito e il proprio tempo di inattività:
non va inventato, va letto dal lato giusto.

---

## 4. La sessione

### 4.1 ✅ La sessione sopravvive al client; è l'utente a chiudere e riprendere

*8 agosto 2026. «è l'utente da solo che capisce che è meglio chiudere il client (tenendo la
sessione aperta) e continuare quando la situazione migliora».*

È l'invariante I4 di v1 (`palco.c`, 1.545 righe, fra il codice che sopravvive), qui promossa
da dettaglio implementativo a **comportamento promesso all'utente**.

### 4.1-bis ✅ ⭐ Il server non butta fuori una sessione sana — e ogni chiusura sua ha un motivo che sa spiegare

*Decisa dall'utente l'**11 agosto 2026**, in coda alla decisione §7.14: «il server non deve
attaccare. È l'utente che decide di fare il logout oppure chiude il client (la scheda del browser)».*

⛔ **A chiudere è l'utente.** Il server non termina **mai** una sessione che sta funzionando: chi se
ne va, se ne va perché ha deciso di andarsene — con il logout o chiudendo la scheda. È §4.1 vista
dall'altro lato: là la sessione **sopravvive** al client, qui il server **non la porta via**.

> ### ⚠ E la formulazione stretta è stata scelta sapendo quale scartava
>
> *Le due letture sono state messe davanti all'utente l'11 agosto, e ha scelto la prima.*
>
> | | |
> |---|---|
> | ✅ **scelta** | *il server non butta fuori una sessione **sana**; chiude solo per un motivo che sa spiegare* |
> | ❌ **scartata** | *il server non chiude **mai**, in nessun caso* — ⛔ e cadrebbero il ban di §1.9, il rifiuto delle credenziali, la regola di rigore di `RCP.md` §3 e i tre tetti di §4.6, cioè quattro difese di cui **tre decise dall'utente stesso** |

⭐ **Che cosa questa regola vieta davvero, ed è più di quanto sembri**: vieta la chiusura **senza
motivo dicibile**. Non esiste una sessione che finisce «perché sì», né una che finisce con un
numero al posto di una frase. ⛔ Ogni percorso in cui il server chiude **deve** portarsi dietro un
motivo di `RCP.md` §8.2 **e** la frase che l'utente legge — e se un percorso non ce l'ha, quel
percorso è un difetto, non una svista.

**Le chiusure che restano, e ciascuna ha il suo motivo dicibile:**

| chi chiude | perché resta |
|---|---|
| il ban dopo tre tentativi (`§1.9`, `RCP.md` §4.4-bis) | ⭐ **deciso dall'utente il 10 agosto**, e chi è bannato **vede una pagina che glielo dice** |
| le credenziali sbagliate — `RESPINTO` | è il congedo dell'autenticazione, `RCP.md` §4.4 |
| la regola di rigore — `ERRORE_PROTOCOLLO` | `RCP.md` §3: chi riceve qualcosa che non capisce **deve** chiudere, o un difetto passa inosservato |
| i tre tetti della stretta di mano — `TEMPO_SCADUTO` | `RCP.md` §4.6, e sono **prima** che una sessione esista: non c'è ancora niente di sano da buttare fuori |
| l'utente è già collegato altrove — `GIA_ATTIVA_REMOTA` | invariante I2 |
| ⚠ **lo stacco a 30 minuti senza input** (`§4.3`) e **la chiusura a 6 ore** (`§4.2`) | ⛔ **decise dall'utente l'8 agosto**, e sono le due che sembrano contraddire questa regola e non la contraddicono: la prima **stacca il client e lascia viva la sessione**, la seconda raccoglie le risorse di una sessione che **non dà segni di vita da sei ore** — cioè non è più «sana», è abbandonata |

⛔ **E questa regola si misura, non si dichiara.** Il banco che la verifica esiste già ed è **B7**:
provoca ogni motivo di congedo e controlla che arrivi **dal lato che lo riceve**, con una frase
distinta per ciascuno. ⭐ Da oggi B7 non conta più solo *«sette motivi su sette»*: ⛔ **è il banco di
questa decisione**, e il suo denominatore è *«quanti percorsi di chiusura ha il server»* — non
*«quanti ne conosco»*. Un percorso che chiude senza un motivo dicibile **non compare** in un banco
che parte dall'elenco dei motivi: si trova solo partendo dal codice.

⚠ **Tocca `DECISIONI.md` §7.17, che è ancora ❓**: una sessione WebTransport che non apre mai il
canale di controllo oggi **non ha addosso nessun tetto** e resta lì per sempre. Non è una sessione
sana — non è una sessione affatto — quindi questa regola non la protegge. **Ma quanto possa restare
lì resta da decidere**, e non lo decide questa riga.

### 4.1-ter ✅ ⭐⭐ Le due uscite non sono la stessa uscita: il filo che cade, e il logout

*Decisa dall'utente il **15 agosto 2026**, all'apertura della fase 5: «distinguiamo il comportamento
del PC usato dall'utente rispetto a quello che fa REMOTIX. Se l'utente chiude, spegne o riavvia il
**proprio** PC, questo lo trattiamo come browser chiuso / connessione caduta. Se invece sceglie la
voce «Esci/logout», allora significa che l'utente vuole **terminare la sessione**, il che comporta
la chiusura di tutti i programmi che aveva in esecuzione».*

§4.1-bis diceva **chi** chiude — l'utente, non il server. Questa dice che quell'utente ha **due
gesti**, e che portano a due posti diversi.

| il gesto | che cos'è per noi | l'esito |
|---|---|---|
| ⭐ **il filo cade** — scheda chiusa, browser chiuso, **il PC dell'utente spento o riavviato**, il campo perso in galleria | ⭐ **un caso solo**, e non c'è niente da distinguere: il PC dell'utente non è un attore del nostro modello | il posto si libera, **la sessione resta viva** (I4). Il `CONGEDO 0x01` parte se fa in tempo; se il PC muore di colpo non parte, e a liberare il posto è l'orologio del silenzio a 30 s (§4.4) — **stesso esito, altra strada** |
| ⭐ **«Esci/logout» dal menu del desktop** | l'unico gesto che dichiara *«ho finito»* | ⛔ **la sessione finisce, e i programmi dell'utente si chiudono**. Niente a cui riattaccarsi |

⭐ **Il guadagno di questa distinzione è che toglie lavoro invece di aggiungerne**: il lato client non
deve rilevare niente — spegnimento, riavvio e chiusura della scheda sono **la stessa cosa già
implementata e misurata** (`pagehide` → `CONGEDO`, `pagina.html:2504`).

**E tre conseguenze che non sono state scelte, sono cadute da sole:**

1. ⛔ **`org.gnome.desktop.lockdown disable-log-out` è VIETATA.** Toglieva la voce «Esci…» **e**
   faceva rifiutare `org.gnome.SessionManager.Logout` (`gnome.md` §5.1). Adesso che il logout è una
   funzione **promessa**, quella chiave toglierebbe la funzione. ⇒ per togliere Spegni/Riavvia/
   Sospendi resta **solo** la regola polkit su logind, e ⭐ il congedo del server
   (`sessione_termina()`) e il logout dell'utente **passano dalla stessa porta**.
2. **`org.gnome.shell always-show-log-out` va acceso.** `[R]` `systemActions.js:394-410`: senza,
   su una macchina con un utente e una sessione sola gnome-shell **non mostra** la voce. ⚠ Rovescia
   `reference-gnome/rapporti/02-shell-blocco-voci.md:214` — *«va lasciata `false`»* — scritta quando
   l'obiettivo era togliere voci, non darne una.
3. **Fra il clic e la fine non tocchiamo niente**: un programma con lavoro non salvato fa comparire
   il dialogo **di GNOME** dentro il desktop remoto, come se l'utente fosse al monitor (I8).

### 4.1-quater ✅ ⭐ Dopo il logout la pagina torna al modulo di accesso — e il motivo è nuovo

*Proposta e accettata dall'utente il **15 agosto 2026**: «concordo, la pagina torna al modulo di
accesso».*

Finito il logout, il browser sta guardando **l'ultimo fotogramma di un desktop che non esiste più**.
La pagina **torna al modulo di accesso**, con sopra la riga *«la sessione è terminata»*: chi voleva
uscire ha finito, chi ha cliccato per sbaglio rientra scrivendo la password e trova un desktop
pulito. ⛔ **Non una schermata di chiusura**, che sarebbe un vicolo cieco da cui si esce ricaricando.

⛔ **E serve un motivo nuovo — `0x10 SESSIONE_TERMINATA` (`RCP.md` §8.2)**, non il riuso di `0x01`:
`CHIUSO_DALL_UTENTE` porta con sé la promessa *«riattacca e ritrovi tutto»*, che dopo un logout è
**falsa**. Due esiti opposti sotto lo stesso codice sono la forma di difetto che `CODER.md` §4.2
vieta: un ripiego silenzioso produce due comportamenti sotto la stessa etichetta.

⚠ **E il difetto vero di questo percorso è l'ORDINE, non il codice**: quando Mutter cade, il palco
cade con lui e il canale non serve più. Il motivo deve partire **prima**. È la stessa forma del
rilievo **B-7** — un motivo che esiste e che nessuno spedisce in tempo.

### 4.1-quinquies ✅ ⭐ Il logout ha anche una scorciatoia — `Ctrl+Alt+Fine`, e la gestisce la PAGINA

*Voluta dall'utente il **15 agosto 2026**: «vorrei venire incontro all'utente per permettergli di
effettuare il logout anche usando una combinazione di tasti». La combinazione l'ha scelta lui, fra
tre proposte.*

⛔ **Due combinazioni sono state provate e scartate PRIMA di scrivere una riga, e con una misura
ciascuna** — vanno scritte qui o qualcuno le riproporrà:

| scartata | perché, con la marca |
|---|---|
| ❌ `Ctrl+Alt+F12` — la prima idea dell'utente | `[R]` è il **predefinito di `switch-to-session-12`** (`org.gnome.mutter.wayland`), e Mutter la registra anche in headless perché il backend resta quello **nativo** (`keybindings.c:2797`, `NATIVE_KEYBINDINGS`). ⛔ È **`NON_MASKABLE`**: nessuna applicazione può prendersela. Iniettata, verrebbe ingoiata e Mutter proverebbe a passare a una console virtuale **che in headless non esiste** — un avviso nel registro e nient'altro. ⛔ **E sul PC dell'utente, se è Linux, non arriva neppure al browser**: la prende il suo compositore, per lo stesso identico motivo |
| ❌ `Win+F12` — la seconda | ⭐ `[M]` **misurato in casa, 14 agosto**: nel catalogo della sonda S3 `Super+KeyD` è **`non-consegnata` in tutti e quattro i palchi** — finestra, schermo intero, schermo intero **con la Keyboard Lock concessa**, e PWA installata. Le combinazioni col tasto Windows **non arrivano mai** alla pagina. ⛔ E su Android e DeX **ogni** combinazione con Meta è persa per regola AOSP — cioè proprio dove serve di più (`SPECIFICHE.md` §7.3-bis) |

✅ **Scelta: `Ctrl+Alt+Fine`.** ⭐ `[R]` **Non la lega nessuno**: cercata come `<Primary><Alt>End` in
tutte le fonti di GNOME e di KDE che abbiamo in casa, zero riscontri. ⚠ **E i due prezzi, dichiarati
perché l'utente li ha scelti sapendoli**: ha **due** modificatori invece di tre, quindi è più facile
premerla per sbaglio; e ha un **precedente RDP che dice un'altra cosa** — lì `Ctrl+Alt+End` manda
`Ctrl+Alt+Canc` alla sessione remota, quindi chi viene da RDP potrebbe aspettarsi quello.

**⭐ La gestisce la PAGINA, non il desktop**, e le tre ragioni sono di peso diverso:

1. **una volta invece di quattro**: legata al desktop andrebbe rifatta per GNOME, KDE, XFCE e LXQt,
   ciascuno col suo modo — cioè quattro righe di configurazione, che è I7 in agguato;
2. ⭐ **funziona quando serve**: legata al desktop, il tasto dovrebbe attraversare browser → rete →
   `libei` → compositore, e non arriverebbe proprio nel caso in cui uno la cerca — col desktop che
   non risponde più;
3. **finisce nella stessa porta del menu**: `org.gnome.SessionManager.Logout`, cioè
   `sessione_termina()`. ⇒ un solo percorso di uscita, non due che possono divergere.

⛔ **E la pagina la ingoia con `preventDefault()`: nella sessione remota quella combinazione non
arriverà mai.** È il prezzo di ogni scorciatoia di REMOTIX, e `SPECIFICHE.md` §7.3-bis obbliga a
**dichiararlo** invece di lasciarlo scoprire.

**Una cosa che viene con lei, e una che è stata tolta:**

- ⭐ **una conferma a schermo** — *«terminare la sessione?»*. Dal menu il logout costa tre gesti
  deliberati; una combinazione ne costa uno, e chiude **tutti** i programmi aperti. ⚠ La conferma è
  anche la difesa dal fraintendimento RDP di qui sopra: chi si aspettava `Ctrl+Alt+Canc` legge che
  cosa sta per succedere e annulla;
- ⛔ **nessun bottone a schermo per il logout** — *tolto dall'utente il 15 agosto 2026: «per quello
  basta la voce del menu di sistema»*. ⭐ **E aveva ragione contro l'argomento con cui gliel'avevo
  proposto**: avevo trasferito al logout il ragionamento di `Ctrl+Alt+Canc` (`SPECIFICHE.md`
  §7.3-bis), che il bottone ce l'ha perché **non ha nessuna voce di menu**. Il logout ce l'ha, e
  quella voce si raggiunge **col puntatore e col dito** — quindi esiste anche dove la tastiera si
  perde tutta, iPhone compreso. ⇒ ⚠ **La regola generale, da non ripagare**: un bottone a schermo si
  giustifica quando **non esiste un'altra strada**, non quando la strada che c'è passa da un tasto.

⚠ **E prima di essere promessa va MISURATA**: la sonda S3 (`banchi/04-b29-scorciatoie.py`) ha
provato 42 combinazioni su due motori e `Ctrl+Alt+Fine` **non è fra quelle**. Si aggiunge, si misura
su due motori, e se su uno non arriva la pagina lo **dichiara** — §7.3-bis: *non si finge che
funzionino*.

### 4.2 ✅ Dopo 6 ore senza segni di vita la sessione viene chiusa

*8 agosto 2026, proposta dall'utente.* Il valore resta, e con §4.3 il suo mestiere è chiarito:
**raccogliere le risorse**, non difendere la sicurezza — di quella si occupa lo stacco a 30
minuti. Su un server multi-utente ogni sessione dimenticata tiene memoria, GPU e un
codificatore.

### 4.3 ✅ Il blocco è di REMOTIX, non del desktop — 30 minuti senza input, poi stacco

*8 agosto 2026. «Se non arriva input dall'utente per 30 minuti la sessione si blocca:
l'utente dovrà fare il re-attach con user e password».*

Dopo 30 minuti senza input, REMOTIX **stacca il client**. Il desktop resta com'era, ma non lo
vede più nessuno: per rivederlo serve un attacco nuovo, con utente e password.

⛔ **Il blocco schermo dei desktop resta spento**, com'era in v1 — `--no-lockscreen` su KWin e
gli equivalenti sugli altri tre. Non è una svista ereditata: è una dipendenza, e ora ha una
ragione scritta. Le quattro strade del «modo A» sono queste, tutte `[R]`:

| Desktop | Che cosa succede bloccando davvero |
|---|---|
| **GNOME** | ⛔ **la revoca.** Entrando nel dialogo di sblocco, gnome-shell chiama `inhibit_remote_access()` e Mutter **chiude ScreenCast, RemoteDesktop e InputCapture, rifiutando di ricrearli** (`gnome.md` §4). C'è l'eccezione `is_headless()`, che è il nostro caso — ma è letta nel codice e **mai misurata** |
| **KDE** | ⛔ **la catena che si morde la coda.** A blocco attivo la nostra inibizione è ignorata (`powerdevilpolicyagent.cpp:509`); powerdevil spegne lo schermo a 10 minuti; con zero uscite KWin monta un output fittizio **con un filtro che inghiotte tutto l'input** (`kde.md` §10.2-10.3). Ci si blocca e non si sblocca più |
| **XFCE, LXQt** | i loro demoni di inattività, e su LXQt `enableIdlenessWatcher=false` **viene riscritto a `true`** dal demone al primo avvio (`lxqt.md`) |

**Le tre ragioni della scelta**, in ordine di peso:

1. **un comportamento solo per quattro desktop**, invece di quattro cure fragili — e tre di
   quelle cure sarebbero righe di configurazione, cioè ciò che l'invariante **I7** vieta;
2. **il conteggio è nostro e non ha incognite**: l'input lo iniettiamo noi, quindi sappiamo
   esattamente quando è passato l'ultimo. Col modo A dovremmo fidarci che il rilevatore di
   inattività di ciascun desktop veda gli eventi di `libei` — su KDE è `[R]` che sì
   (EIS → `simulateUserActivity`), sugli altri tre sarebbe da misurare;
3. **la sicurezza è la stessa**: l'unica strada per quel desktop passa da RCP, e RCP passa
   da PAM. La schermata di blocco chiederebbe la medesima password.

> ⚠ **E questa decisione ha una condizione di scadenza, posta dall'utente lo stesso giorno:**
> *«non escludo che un domani potremmo implementare un metodo di autenticazione molto più forte
> della semplice password, ma per il momento va bene solo questa»*.
>
> Il ragionamento del punto 3 **regge solo finché la password PAM è l'unica chiave**. Il giorno
> in cui RCP autenticasse con qualcosa di diverso — un gettone sul dispositivo, una chiave, un
> secondo fattore — il blocco del desktop smetterebbe di essere ridondante e diventerebbe una
> difesa vera, perché chiederebbe una chiave **che chi ha rubato la prima non ha**.
>
> **Chi implementa l'autenticazione forte rilegge questa voce**, e non la dà per acquisita.
>
> ⏳ **E quel giorno ha una data di apertura, decisa il 9 agosto 2026**: l'evoluzione con l'MFA,
> rinviata a progetto completato — §1.7, il riquadro del debito di sicurezza.

### 4.3-bis 🔸 ⛔ Essere *headless* su GNOME è un requisito, non una fortuna

*Scritta il 9 agosto 2026, leggendo `gnome.md` §4 e la lezione 3 del suo §14.*

§4.3 dice che il blocca-schermo dei desktop resta spento, e per GNOME la ragione è la **revoca**:
entrando nel dialogo di sblocco, Mutter chiude cattura, controllo e input **e rifiuta di
ricrearli**. L'unica eccezione è `is_headless()` — e quella eccezione è la nostra condizione.

⛔ **Ma non è una condizione che abbiamo chiesto.** Mutter si mette in headless **da solo** quando
la sessione logind è di tipo `wayland`, attiva e **senza seat** `[R]`. Nessuna nostra riga la
chiede, nessuna la verifica, e il giorno in cui la sessione nascesse con un seat — un `gdm3`
configurato diversamente, una prova fatta a mano, un ripristino incompleto — perderemmo cattura e
input **senza che nessuno colleghi le due cose**.

**Da cui, e sono tre obblighi distinti:**

1. la sessione si compone **dichiarando** che deve essere headless, non sperando che lo diventi;
2. l'esito si **verifica dopo l'avvio**, come per il tema del cursore trasparente di §5-bis.2 —
   che il presupposto sia scritto non è che sia stato ottenuto (`REVIEWER.md` E1: necessario non
   è sufficiente);
3. se non lo è, si **dichiara il fallimento** invece di proseguire: sarebbe una sessione che
   funziona finché nessuno blocca lo schermo (`CODER.md` §3.9, §4.2).

⭐ **È l'invariante I7 in una forma che non avevamo previsto.** I7 dice che la protezione di un
difetto noto non sta in una riga di configurazione che si può perdere; qui non sta **da nessuna
parte** — sta in un comportamento di ripiego di Mutter. `gnome.md` §14 lo scrive meglio: *una
condizione che ci salva per accidente va scritta come requisito.*

⚠ E la misura che la chiude è **M2** di `gnome.md` §13: headless sì/no contro
`inhibit_remote_access`. Fino ad allora la clausola di scadenza di §4.3 vale anche qui.

### 4.4 ✅ Un client che tace è un client che si è staccato

*8 agosto 2026. «Fantasma: lo trattiamo come nel caso in cui l'utente chiude il client».*

Nessuna connessione «tiene il posto». Chi tace è staccato, chi arriva entra — senza timeout da
aspettare, senza subentro da negoziare, senza il caso «il telefono è morto in galleria e ora
non posso rientrare dalla mia sessione» che v1 aveva dovuto tamponare con keepalive stretti.

Sparisce così anche il bivio *subentro contro attesa*: non esiste più, perché non esiste il
posto occupato.

> ### ⛔ Precisata la sera del 9 agosto 2026 — questa voce parlava solo del **fantasma**
>
> *«Se un utente ha già una sessione grafica remota attiva, e ne vuole attivare una seconda da un
> secondo device, la seconda connessione viene rifiutata.»*
>
> La revisione di `RCP.md` ha trovato che il protocollo non sapeva esprimere il caso **remoto
> contro remoto** — sei attaccato dal portatile e apri dal telefono — e che i motivi disponibili
> dicevano tutti «locale», cioè avrebbero mostrato all'utente una frase falsa.
>
> ⭐ **La regola completa sono due righe, e il discrimine è l'orologio del silenzio:**
>
> | Il client che c'era | Che cosa succede a chi arriva |
> |---|---|
> | **tace da 30 secondi** — il fantasma di questa voce | è **staccato**, non occupa niente: chi arriva **entra** |
> | **è vivo e attaccato** | chi arriva è **rifiutato**, con `GIA_ATTIVA_REMOTA` (`RCP.md` §8.2) |
>
> ⭐ **La seconda riga non è nuova: è l'invariante I2** — *«la seconda connessione è rifiutata con
> messaggio esplicito»* — che nessuno aveva collegato a questa voce. E il nuovo motivo è il gemello
> remoto di `GIA_ATTIVA_LOCALE`, così come `SPECIFICHE.md` §5.1 ha già la coppia locale.
>
> ⚠ **Il prezzo, dichiarato**: se il portatile si spegne di colpo senza congedarsi, dal telefono si
> entra **dopo trenta secondi**. È lo stesso orologio di §4.5, e nessuno l'ha spostato.

### 4.5 🔸 I tre orologi della sessione

Le decisioni 4.1-4.4 mettono in fila tre tempi diversi, che vanno tenuti distinti perché
misurano cose diverse:

| Orologio | Quanto | Che cosa scatta | Deciso in |
|---|---|---|---|
| **silenzio del client** | **30 secondi** | il client si considera staccato | §4.4, valore in §7.3-bis |
| **inattività dell'utente** | **30 minuti** senza input | REMOTIX stacca il client | §4.3 |
| **abbandono della sessione** | **6 ore** senza alcun attacco | la sessione viene chiusa, con congedo pulito | §4.2 |

Sono in scala: il primo si misura in secondi, il secondo in minuti, il terzo in ore. Un utente
che lascia il client aperto e va a pranzo viene staccato dopo mezz'ora e ritrova tutto
riattaccandosi; se non torna entro le sei ore successive, la sessione viene raccolta.

⚠ **Una conseguenza da tenere d'occhio**: «input» è quel che l'utente manda, non quel che
guarda. Chi resta mezz'ora a guardare un video senza toccare nulla viene staccato. Il costo è
piccolo — riattaccarsi è rapido — ma se emergesse come fastidio, la cura è un cenno di
presenza dal client, non l'allungamento della soglia.

### 4.6 ✅ Dieci sessioni grafiche come tetto — ma il limite è un budget, non un conteggio

*9 agosto 2026. «Quante sessioni grafiche può reggere contemporaneamente il sistema fra locali e
remote? […] credo che 10 potrebbe essere un numero molto comodo». E poi: «il mio è un tetto: non
capiterà mai che ci sono 10 utenti contemporaneamente che si collegano con client in 4K».*

> ⚠ **E alla fase 1 questo tetto non è onorato, ed è un ripiego dichiarato**: il server gira su **un
> filo solo** e la verifica PAM lo **blocca**, quindi dieci utenti che entrano insieme si mettono in
> fila (con il secondo fisso di `RCP.md` §4.4-bis, l'ultimo aspetta **dieci secondi**); e la tabella
> delle sessioni attaccate è un `#define` a **16**. ⛔ Non è una decisione che cambia: è una promessa
> **non ancora dovuta**, e sta scritta in `SPECIFICHE.md` §5.5 e in `fasi/01-filo-nudo.md` perché il
> giorno in cui sarà dovuta si sappia da dove ripartire. *Portata fuori dal commento in `src/main.c`
> l'11 agosto 2026, rilievo **R12C.17**.*

⛔ **Dieci non è il limite: è il tetto amministrativo.** Il limite vero lo pone il
**codificatore**, e si misura in pixel al secondo — con lo stesso ferro, le stesse dieci sessioni
sono facilissime o impossibili a seconda della qualità che ciascuna chiede.

Sul ferro di prova — i5-13500T, 31 GB, Intel UHD 730 (Alder Lake) `[M]` 9 agosto:

| 10 sessioni a… | Da codificare | Sulla sola Intel |
|---|---|---|
| 480p · 25 fps *(il minimo)* | ~100 Mpixel/s | ⭐ larghissimo, una cinquantina |
| 1080p · 30 fps | ~620 Mpixel/s | ✅ giusto al limite |
| 4K · 60 fps *(il desiderato)* | ~5 Gpixel/s | ⛔ **una sola sessione** |

> ### ✅ Confermate `[M]` il 9 agosto 2026 — `vainfo` installato ed eseguito sul ferro
>
> *Erano `[?]`, ricavate dalla generazione del chip. Ora sono lette dal driver, sui due nodi.*
>
> | | Intel UHD 730 — `renderD128`, iHD 25.2.3 | Radeon RX 6800 — `renderD129`, radeonsi navi21 |
> |---|---|---|
> | **HEVC Main10 in codifica** | ✅ **sì** (`EncSliceLP`) | ✅ sì (`EncSlice`) |
> | HEVC Main **4:4:4**, 8 e 10 bit | ⭐ ✅ **sì** — vedi §2.3 | ⛔ no |
> | H.264, VP9, JPEG in codifica | sì | H.264 sì |
> | **AV1** | ⛔ **nessun profilo, nemmeno in decodifica** | solo **decodifica** (`AV1Profile0`, `VLD`) |
>
> ⛔ **Il desiderato a 10 bit ha la sua strada in hardware su tutt'e due le schede**, e passa da
> HEVC Main10 come `SPECIFICHE.md` §11.4 prevedeva. La scala di preferenza di §11.4 resta valida:
> `hevc_vaapi` è la prima voce e la macchina ce l'ha.
>
> ⚠ **Un dettaglio da non perdere, che tocca la fase 8**: sull'Intel l'unico ingresso di codifica è
> `EncSliceLP` — il percorso *low power*. Non è un ripiego, è il solo che quel chip espone; ma è
> un percorso con opzioni di controllo del bitrate proprie, ed è precisamente il posto dove v1 si
> è fatto male due volte (`LEZIONI.md` §1.8: il driver che deduceva il modo di controllo da come
> erano riempiti due campi, banda costante senza che nessuno l'avesse scelta). **Si chiede per
> nome e si verifica che abbia obbedito.**
>
> ⭐ E la tabella del budget qui sopra resta `[?]` per un'altra ragione: `vainfo` dice **quali
> profili** ci sono, non **quanti pixel al secondo**. Il numero di sessioni va misurato saturando,
> ed è la fase 10.

**Da cui il disegno**: nessun numero cablato nel programma. Il server tiene un **budget** — sa
quanto sta già codificando e quanto può — e il dieci è il valore predefinito di un massimo
configurabile, come le sei ore di §4.2. La RAM non è il collo: dieci sessioni GNOME ferme sono
~12 GB dei 31, dieci LXQt ~5.

### 4.6-bis 🔸 Quando il budget è pieno si rifiuta, dichiarando il motivo

Non si fa degradare chi sta già lavorando per far entrare chi arriva. Sarebbe la scelta
apparentemente gentile, ma punisce in silenzio chi non ha fatto niente — ed è precisamente ciò
che I1 vieta: una discesa che non nasce da una misura della linea, ma da una decisione presa
altrove e mai dichiarata.

Il rifiuto dice **perché**: «questa macchina non ha più capacità di codifica». Non «riprova più
tardi» e basta.

### 4.6-ter 🔸 ⛔ La GPU si sceglie con una regola udev, e ha un prezzo da sapere prima

*Sul ferro dell'utente REMOTIX usa **l'Intel**; la Radeon RX 6800 è riservata all'inferenza.*

Il meccanismo esiste già: `v1/banco/gpu-udev.sh`, e la sua intestazione spiega perché non ce ne
sono di più semplici:

- **KWin prende la prima scheda che riesce ad aprire** e non guarda nessuna variabile
  (`KWIN_DRM_DEVICES` vale solo per il backend `drm`). L'unico modo di sceglierne una è rendere
  l'altra **non apribile**;
- ⛔ **e la via ovvia è una trappola**: `InaccessiblePaths=` nell'unità del compositore dà la
  scheda giusta e **chiude il cancello della cattura** — 0 righe di registro sui permessi contro
  13 (`kde.md` §3.3-bis). Si passa dai permessi del **nodo**;
- ⚠ **per id PCI, non per numero di nodo**: `renderD128` e `renderD129` si scambiano fra un
  avvio e l'altro, l'indirizzo PCI no.

⚠⚠ **Il prezzo, che lo script dichiarava già prima che l'inferenza esistesse**: negare il nodo
coi permessi lo nega a **tutta la sessione dell'utente**, non solo al compositore. Sul ferro
attuale questo significa che **l'utente che fa inferenza va messo nel gruppo** della regola, e
gli utenti delle sessioni remote no. Funziona — ma se un giorno l'inferenza smettesse di vedere
la Radeon, la causa è questo file, e nessuno la collegherebbe da solo.

⭐ E l'avvertenza di `LEZIONI.md` §4 trappola 6 — *«il compositore deve disegnare sulla scheda
giusta; un buffer di un'altra scheda non è importabile, e il sintomo è composizione in software
senza un errore»* — su una macchina a **due** GPU smette di essere teorica.

> ### ⭐ Su Mutter il meccanismo è un altro, e per ora gioca a favore — `[M]` 9 agosto 2026
>
> Questa voce è scritta su KWin, che *«prende la prima scheda che riesce ad aprire»*. Mutter no:
> alla fase 0, con tutt'e due i nodi visibili, ha dichiarato da sé
>
> > `Added device '/dev/dri/renderD129' (amdgpu)` · `Added device '/dev/dri/renderD128' (i915)` ·
> > **`Boot VGA GPU /dev/dri/renderD128 selected as primary`**
>
> — cioè ha scelto **l'Intel**, che è quella che vogliamo, con un criterio suo (*Boot VGA*) e
> senza che nessuno gliel'abbia chiesto. **Sul ferro attuale la regola udev non serve a GNOME.**
>
> ⛔ **Ma non si conclude che non serva.** È di nuovo una condizione che ci salva senza che
> l'abbiamo chiesta (§4.3-bis): dipende da quale scheda è la *Boot VGA* del BIOS, che è fuori dal
> nostro controllo e cambia spostando un cavo. La regola udev resta la **leva dichiarata**; questa
> misura dice solo che oggi, su GNOME, non è lei a decidere.
>
> ⚠ E una riga da capire, non ancora capita: `amdgpu_cs_ctx_create2 failed. (-13)` — la Radeon è
> vista e **non apribile** (permesso negato). `[?]` Se sia già la regola udev di questo file o
> altro, non è stato accertato. Non ostacola: il primario è quello giusto.

### 4.6-quinquies ✅ ⛔ **Si misura sulla GPU INTEGRATA**, non sulla discreta

*Vincolo posto dall'utente il **15 agosto 2026**, guardando la registrazione dell'Aquarium a 60 fps:
«i test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità del sistema la
si vede su GPU poco potenti, non mostri come la RX 6800».*

⭐ **È una regola di metodo, e vale più della misura che l'ha provocata**: un numero preso sul ferro
migliore non dice se il prodotto regge — dice quanto è veloce quel ferro. `LEZIONI.md` è pieno di
misure che sembravano un risultato e erano una proprietà del banco.

`[M]` **La macchina di prova ha due schede**, e fino a stasera **sceglieva il compositore**:

| | indirizzo PCI | nodo | chi è |
|---|---|---|---|
| ✅ **si usa questa** | `0000:00:02.0` | `renderD128` | **Intel UHD 730** (`i915`), l'integrata |
| ❌ esclusa | `0000:03:00.0` | `renderD129` | Radeon **RX 6800** (`amdgpu`) |

⛔ **E non era una scelta: era un accidente.** Senza la regola udev di §4.6-ter — `[M]` non era
installata, `/etc/udev/rules.d` era vuota — i gruppi `video`/`render` danno accesso a **tutte e
due**, e `[M]` il compositore aveva preso la **Radeon**. ⇒ La misura dell'Aquarium delle 22:09 —
60 fps inchiodati — è stata fatta **sulla scheda sbagliata**, e va rifatta.

**La cura è quella già decisa in §4.6-ter, finalmente applicata**: `v1/banco/gpu-udev.sh` con
l'indirizzo da **escludere**, che sposta il nodo in un gruppo senza membri. ⭐ `[M]` dopo il
riavvio del gestore d'utente e della sessione, `gnome-shell` apre **6 descrittori su `renderD128`**:
l'integrata, e solo quella.

⚠ **E il prezzo resta quello che §4.6-ter dichiara**: negare il nodo lo nega a **tutta la sessione
dell'utente**, non solo al compositore. Chi un giorno volesse la Radeon per altro — un
transcodificatore, un gioco — la troverebbe chiusa, e nessuno collegherebbe la cosa a questo file.

⏳ **E la fase 8 eredita una domanda in più**: la codifica hardware sceglie la sua scheda per conto
proprio (VA-API). ⛔ Se il compositore disegna sull'integrata e il codificatore cerca la discreta —
che qui è chiusa — il ripiego è in CPU, ed è il caso che `LEZIONI.md` §1.8 dice di **dichiarare**
invece di subire.

### 4.6-quater ✅ ⭐ Il confine del multi-tenant: la fase 5 regge **un utente per volta**, la fase del multi-tenant la macchina piena

> ⚠ **Il numero di quella fase è cambiato il 16 agosto 2026 — era la 12, adesso è la 10** — e il
> **confine qui deciso è intatto**: vedi **§4.6-sexies**. Il titolo diceva *«la 12 la macchina
> piena»*, e adesso dice la cosa senza il numero, che era la parte fragile.

*Chiesto dall'utente il **15 agosto 2026** all'apertura della fase 5 — «poiché qui trattiamo le
sessioni, mi chiedo se il multi-tenant non ricada in questa fase» — e deciso da lui lo stesso
giorno: «potremmo anche lasciare in questa fase 1 solo utente, e nella fase 12 il multi-tenant».*

⚠ **La domanda era buona perché i due documenti dicevano cose diverse**: `SPECIFICHE.md` §5.5 dice
*«il multi-tenant è delle fasi da 5 in poi»*, `PIANO.md` intitolava la **fase 12** «Multi-tenant e il
budget». Il confine, deciso:

| | dove | perché lì |
|---|---|---|
| **il multi-tenant come funzione** — più sessioni remote insieme, il **budget** del codificatore, `BUDGET_PIENO 0x06`, il rifiuto che non fa peggiorare chi sta già lavorando, `MAX_ATTACCATE` che smette di essere un `#define` | **fase 10** | ⭐ hanno bisogno di **un numero vero**, e il numero vero lo dà il codificatore hardware della **fase 8**. Misurarle prima vuol dire misurarle due volte (`LEZIONI.md` §7.2) |
| **un utente remoto per volta** | **fase 5** | è la scena che la fase promette, ed è già abbastanza carica: il logout col suo codice nuovo, le tre cinture di §4.7, il guardiano di logind, i tre orologi, il rilascio dei tasti, l'inibizione della sospensione, l'headless dichiarato |
| ⛔ **il codice chiavato sull'utente**, e il guardiano di logind che **discrimina per utente** | ⭐ **fase 5, e non è rinviabile** — vedi il riquadro | ⛔ non perché sia importante: perché **non si può scrivere «per un utente solo»** |

> ### ⛔⭐ Il pezzo che non si può rinviare, e la ragione è che la macchina lo smaschera da sola
>
> Il guardiano di logind che deve emettere `0x04` e `0x05` (`SPECIFICHE.md` §5.1) risponde a una
> domanda che suona in **due modi diversissimi**:
>
> > *«c'è una sessione grafica locale?»* — oppure — *«c'è una sessione grafica locale **di questo
> > utente**?»*
>
> ⛔ **Una riga di differenza nel codice, due prodotti diversi.** E la macchina di prova è **già**
> nella configurazione che smaschera l'errore: `nicfio` ha la sua sessione grafica **locale**,
> `prova` si collega da **remoto**. Scritto nel modo sbagliato, `prova` viene rifiutato con `0x05`
> — *«c'è già una sessione grafica locale»* — **il primo giorno, alla prima prova**, perché la
> sessione locale c'è davvero: è solo di un altro.
>
> ⭐ **Non serve inventare uno scenario multi-utente: è lo stato normale della macchina.** ⇒ Il banco
> di `0x04`/`0x05` si scrive su quella coppia — locale `nicfio` e remota `prova`, che **devono
> convivere senza toccarsi** — e costa quanto costerebbe comunque.

⚠ **E quel che resta ripiego resta dichiarato**: `MAX_ATTACCATE` è un `#define` a **16** in
`rcp.c:568` — e `MAX_FIGLI` a 16 in `figlio.c:83`, che dichiara di seguirlo — dove `SPECIFICHE.md`
§5.5 promette **dieci configurabile**. Oggi non morde — 16 > 10 — e la sua scadenza è la fase 10.
⚠ *Il riferimento diceva `rcp.c:490`, e il `#define` sta a **568**: corretto il 16 agosto 2026
rileggendo il file. ⛔ Un numero di riga invecchia in silenzio — è il motivo per cui accanto c'è
anche il nome della costante.*

### 4.6-sexies ✅ ⭐⭐ L'ordine cambia: il multi-tenant **prima** dei desktop nuovi

*Deciso dall'utente il **16 agosto 2026**, rivedendo il piano prima di aprire la fase 6: «PRIMA si
chiude lo sviluppo anche con il multi-tenant, e solo dopo si pensa agli altri DE».*

⛔ **Il confine di §4.6-quater NON cambia**: «un utente per volta» resta della fase 5, «la macchina
piena» resta della fase del multi-tenant, e il codice chiavato sull'utente resta non rinviabile.
⭐ **Cambia solo dove quella fase sta nella fila** — e con lei il suo numero:

| | prima | ⭐ adesso |
|---|---|---|
| Multi-tenant e il budget | fase **12** | **fase 10** |
| KDE | fase 10 | **fase 11** |
| XFCE e LXQt | fase 11 | **fase 12** |
| La qualità e la degradazione | fase 9 | **fase 9**, invariata — e adesso ha un secondo cliente: la scala di degradazione è **il modo** in cui più sessioni stanno sulla stessa macchina |
| Il servizio | fase 13 | **fase 13**, invariata — ⛔ e resta ultima **per una ragione**: §7.16 le fa **togliere dal binario** le marche di banco `BANCO_MARCA`/`BANCO_ESITO`, che le fasi dei desktop useranno per misurarsi. Metterla prima vorrebbe dire togliere il metro e poi provare tre desktop nuovi senza |

⭐ **La ragione è quella di §4.6-quater, applicata dall'altro capo.** Là si diceva: *«misurare il
budget prima del codificatore hardware vuol dire misurarlo due volte»* (`LEZIONI.md` §7.2). Qui:
⛔ **il budget è un budget di GPU, e la GPU è una** — `renderD128`, la stessa iGPU che compone
**ogni** desktop. È una proprietà **della macchina**, non del desktop. Misurata prima, le fasi 11 e
12 la ereditano; misurata dopo tre desktop nuovi, non si sa più quale numero appartenga a che cosa.
⇒ E se il multi-tenant tocca la sessione o il budget, la modifica va riverificata **su quattro
desktop invece che su uno**.

⚠ **E quel che questa decisione NON compra, detto per intero**: l'architettura multi-tenant c'è già
in buona parte — `figlio.c:80` dichiara *«un utente per figlio»*, un processo per sessione. ⇒ Non
si sta scansando una riscrittura strutturale; si sta evitando una misura ripetuta quattro volte.
È un argomento più debole di quel che sembra, e tira nella stessa direzione lo stesso.

⛔ **La precedenza che resta**: il multi-tenant sta **dopo la fase 8**, e la ragione è invariata —
la **copia zero** cambia quanto costa una sessione in memoria e banda di GPU, e un budget misurato
prima della copia zero è un budget da rifare.

> ### ⚠ E le parole del 15 agosto dicono «fase 12»: restano
>
> La citazione di §4.6-quater — *«nella fase 12 il multi-tenant»* — **non è stata riscritta**, né
> qui né in `fasi/05-la-sessione.md`: era il numero di allora, e correggere una frase fra virgolette
> è il modo più veloce per non sapere più che cosa è stato detto davvero.
> ⇒ **La decisione era ed è la stessa; è il posto in fila ad essere cambiato.**

### 4.7 ✅ ⛔⛔ Nessuno spegne il server — e «nessuno» comprende chi è davanti alla macchina

*Decisa dall'utente il **15 agosto 2026**, all'apertura della fase 5: «no, nessuno può spegnere,
riavviare, mettere in standby o sospensione il server, altrimenti si rischia di "buttare fuori"
anche altri eventuali utenti collegati alla macchina».*

⭐ **La ragione è la stessa che regge tutta la fase 5: la macchina è di più persone.** Spegnerla è
l'unico gesto che porta via **tutte** le sessioni insieme — e chi lo compie, dal menu di un desktop,
**non ha modo di vedere chi c'è collegato**. `SPECIFICHE.md` §11.3 lo prometteva già in una riga
(*«spegnimento, riavvio, sospensione: tolti alla sessione remota»*); questa decisione la allarga
— ⛔ **non «alla sessione remota»: a tutte** — e le dà per la prima volta un modo di essere
mantenuta.

**Tre cinture, e sono tre perché le strade sono tre:**

| | |
|---|---|
| **1 · la regola polkit**, `no` su `org.freedesktop.login1.power-off`, `reboot`, `suspend`, `hibernate` e le varianti `*-multiple-sessions` / `*-ignore-inhibit` | ⭐ **piatta, senza discriminante**: nessun `subject.local`, perché la decisione è «nessuno». ⭐ E copre **due strade con una riga sola**, perché guarda l'**azione** e non l'interfaccia: il menu del desktop **e** `systemctl poweroff` scritto in un terminale dentro la sessione. Su GNOME `CanShutdown` diventa falso e le voci **spariscono** (`gsm-manager.c`, `systemActions.js:340-359`). ⛔ **`no`, mai `auth_admin`**: `challenge` **mostra** la voce (`gnome.md` §5.1, `kde.md` §1579) |
| **2 · `logind.conf`**: `HandlePowerKey`, `HandleSuspendKey`, `HandleHibernateKey`, `HandleLidSwitch` = `ignore` | ⛔ il **tasto fisico** e il coperchio **non passano da polkit**: logind agisce per conto proprio, e la prima cintura non li vede |
| **3 · la sospensione automatica**: `Inhibit(…, SUSPEND\|IDLE)` **e** `sleep-inactive-ac-type=nothing` | ⚠ la prima cintura **ferma** la sospensione a inattività, ma l'utente vedrebbe lo stesso la notifica *«Automatic Suspend — Suspending soon»* `[M]` e poi un errore. Due cinture per **due sintomi diversi**: una impedisce il fatto, l'altra toglie la bugia dallo schermo |

> ### ⭐⭐ E LA SERA STESSA LE TRE CINTURE SONO STATE INSTALLATE E MISURATE — `[M]` 15 agosto 2026
>
> *Sulla macchina di prova, dopo il riavvio. ⛔ E la misura ha corretto **due** cose che questa voce
> diceva per deduzione.*
>
> | | |
> |---|---|
> | ⛔⛔ **la regola di v1 copriva tre azioni su dodici, e falliva ESATTAMENTE nel caso per cui era scritta** | `[M]` `org.freedesktop.login1.policy` elenca anche `*-multiple-sessions` e `*-ignore-inhibit`. ⛔ Quando sulla macchina ci sono sessioni di **più utenti**, logind non chiede `power-off`: chiede **`power-off-multiple-sessions`**, che la regola di v1 non nominava. ⇒ Con un utente solo funzionava, con due no — e nessuno l'avrebbe visto. ⚠ E `org.freedesktop.login1.halt` **non esiste** su questo systemd: quella riga era morta |
> | ⭐ **root non ha bisogno di nessuna eccezione** — *e la riga qui sotto, che ne prometteva una, era sbagliata* | `[M]` con la regola in vigore: da `nicfio` `CanPowerOff="no"`, **da root `"yes"`**. ⛔ Prima di interrogare polkit, logind guarda le **capacità** di chi chiede: chi ha `CAP_SYS_BOOT` è autorizzato e polkit **non viene consultato affatto**. ⇒ `sudo systemctl poweroff` funziona senza che la regola preveda niente |
> | ⛔⛔ **e da questo discende la trappola vera: la verifica NON si può fare dal server** | il server gira **da root**, quindi si sentirebbe rispondere `"yes"` sempre — un controllo che dice sempre di sì. ⇒ **La fa il FIGLIO**, dopo che è diventato l'utente. ⚠ Un controllo fatto dal posto sbagliato è peggio di un controllo che manca: il registro direbbe «verificato» |
> | ⭐ **il tasto fisico era vivo** | `[M]` in `/etc/systemd/logind.conf` tutte le righe `Handle*` erano **commentate**, cioè il predefinito — e `HandlePowerKey=poweroff`. ⇒ Fino a stasera il pulsante spegneva il server con chiunque collegato sopra. Adesso `ignore`, `[M]` riletto da `systemd-analyze cat-config` |
> | ⭐ **la sospensione ha una cintura più forte di polkit** | `sleep.conf.d` con `AllowSuspend=no` fa rifiutare la sospensione da **systemd**, non da polkit: `[M]` `CanSuspend="no"` **anche da root**. ⇒ Su suspend e hibernate la promessa è mantenuta anche contro l'amministratore |
>
> ⇒ **I due file stanno nel repository**, non solo sulla macchina — I7: `src/remotix-niente-spegnimento.rules`
> e `src/remotix-tasti.conf`.

⛔ **E quel che resta possibile va dichiarato adesso, non scoperto dopo: root.** ⭐ `[M]` root spegne
perché ha `CAP_SYS_BOOT`, e logind lo autorizza **prima** di arrivare a polkit; e in ogni caso
`systemctl --force poweroff` parla direttamente con PID 1. ⭐ **Ed è giusto che resti**: la macchina
deve restare amministrabile, e lo spegnimento per manutenzione è un gesto dell'**amministratore**,
non di un utente. ⇒ La promessa esatta, da scrivere così e non più larga:

> **Nessun utente, da nessuna sessione — remota o locale — spegne, riavvia o sospende il server.**
> Non «il server non si spegne».

> ### ⭐⭐ E l'utente l'ha specificato meglio, lo stesso giorno
>
> > *«L'utente collegato a REMOTIX può solo fare espressamente il logout o, ovviamente, operare sul
> > PC che sta utilizzando.»*
>
> ⭐ **Detta così, la regola smette di essere un elenco di divieti e diventa una regola sola**, ed è
> la forma da tenere:
>
> | dentro il desktop remoto | ⭐ **un solo gesto che finisce qualcosa: il logout** (§4.1-ter). Spegnere, riavviare, sospendere, ibernare **non gli appartengono** — non perché siano pericolosi, ma perché **non sono suoi**: quella macchina la stanno usando anche altri |
> |---|---|
> | sul PC da cui è collegato | ⭐ **fa quel che vuole, ed è affar suo**: lo spegne, lo riavvia, chiude il coperchio. Per noi è **il filo che cade**, cioè il caso già misurato — e non c'è niente da rilevare, da distinguere o da vietare |
>
> ⛔ **Da cui il metro del banco di §1.1 della fase 5**, che è più forte di «le voci sono sparite»:
> ⇒ *nel menu di sistema del desktop remoto resta «Esci…» **e nient'altro** di quella famiglia.*

> ⛔ *Qui c'era una riga che diceva di scrivere **l'eccezione di root dentro la regola**, perché
> altrimenti «perfino `sudo systemctl poweroff` fallirebbe». ⭐ La misura del 15 agosto l'ha smentita:
> l'eccezione non serve, perché non è polkit a decidere per root. La regola resta **piatta**, come
> l'utente l'ha voluta.*

⭐ **E questa regola dà finalmente un mestiere a `0x0C SERVER_IN_CHIUSURA`**: se l'unico spegnimento
legittimo è quello dell'amministratore, allora **quella è l'unica strada su cui i client vanno
avvisati**, e la cura del rilievo B-7 (`main.c:850`, `trasporto_congeda_tutte`) smette di essere una
riparazione e diventa **il percorso normale**.

⚠ **E le tre cinture sono tutte righe di configurazione, cioè quel che l'invariante I7 vieta**: vanno
**installate da noi** e **verificate dopo l'avvio**, come l'headless di §4.3-bis. ⭐ La verifica è si
chiede a logind `CanPowerOff` / `CanReboot` / `CanSuspend` / `CanHibernate` e si pretende **`no`** —
se risponde `yes` o `challenge`, la protezione non c'è e si dichiara il fallimento. ⛔ **E si chiede
dal FIGLIO, che è l'utente**: dal server, che è root, la risposta è `yes` per costruzione, e il
registro direbbe «verificato» avendo guardato la cosa sbagliata.

---

### 4.8 ✅ ⛔ Niente sei ore: **sessanta minuti senza input e la sessione si chiude**

*Decisa dall'utente il **16 agosto 2026**, con queste parole: «niente timeout delle 6 ore: se dopo 60
minuti non c'è traccia di input la sessione viene killata».*

`SPECIFICHE.md` §5.3 aveva scritto **6 ore senza alcun attacco**. ⇒ Cambiano **due cose**, e vanno
lette separate:

| | prima | adesso |
|---|---|---|
| il tetto | 6 ore | **60 minuti** |
| ⛔ **il criterio** | «nessuno si è **attaccato**» | «nessuno ha **toccato niente**» |

⭐ **Il secondo cambio è il più grosso**, e va detto: uno che si attacca e resta a guardare non
rinnova più niente. Il tetto si nutre degli stessi gesti dell'orologio dei 30 minuti — i cinque
input di §7.3 — e non del fatto che una connessione esista.

### ⭐ La decisione è venuta da un numero, e il numero è stato misurato apposta

*L'utente aveva chiesto: «misura la memoria. Potrei anche decidere di diminuire drasticamente questo
intervallo».*

`[M]` 16 agosto 2026, sessione abbandonata, PSS (le librerie condivise contate una volta sola):

| | |
|---|---|
| la sessione intera di `prova` | **477 MB** su 31 851 totali ⇒ **1,5 %** |
| di cui `gnome-shell` | 182 MB |
| di cui **il nostro figlio** (palco, cattura, codificatore) | **116 MB** |
| CPU | ~0,017 % di un nucleo |
| ⭐ **crescita in 4 minuti** | **nessuna**: 477 · 476 · 476 · 477 · 477 · 477 · 477 · 477 · 477 MB |

⇒ **Non è una perdita, è un costo fisso.** ⚠ E la scelta, con quel numero davanti, è dell'utente: si
paga per un'ora invece che per sei.

### ⚠ E una complicazione è stata proposta e SCARTATA — dall'utente, con una misura di buon senso

Avevo proposto di azzerare il tetto anche al **riaggancio**, temendo di uccidere una sessione mentre
qualcuno la guardava. La risposta:

> *«la tua ipotesi comporta il fatto che l'utente in 10 minuti non fa nemmeno un clic col mouse,
> alquanto improbabile»*

⭐ **Ed è giusta**: perché il danno avvenisse, uno dovrebbe rientrare e poi non toccare **niente** per
il resto dell'ora. ⇒ Si conta l'input e basta — la regola più semplice, e anche la più facile da
spiegare a chi la subisce.

### Che cosa comporta, in codice

- il motivo `0x03 SESSIONE_ABBANDONATA` di `RCP.md` §8.2 **esiste da sempre e non l'aveva mai spedito
  nessuno**: adesso è il suo. ⚠ Di solito non lo riceverà nessuno — se il tetto scade è perché non
  c'era più nessuno — ma chi c'è legge una frase invece di guardare uno schermo fermo;
- **configurabile** (`--abbandono-s`), `0` = spento, e il valore in vigore **si scrive nel registro
  all'avvio** insieme agli altri due: un tetto da un'ora non lo verifica nessuno aspettando un'ora.

---

## 5. La geometria — la tela e la vista

### 5.0 ✅ La tela nasce a ogni attacco, e sta ferma finché il client resta

*8 agosto 2026, modello dettato dall'utente.*

| Momento | Chi decide la misura | Chi adatta |
|---|---|---|
| **attacco** | il client: la sessione legge la sua risoluzione e usa quella | nessuno — è 1:1 |
| **durante la sessione** | nessuno: la tela non si muove | il **client** riscala l'immagine |
| **riattacco** da un altro dispositivo | il nuovo client, con la sua risoluzione | nessuno — di nuovo 1:1 |

Chiude la domanda che era aperta in §7.1: la tela **non** ha un valore predefinito né una
preferenza dell'utente. La detta il client, a ogni attacco.

**La virtù del modello è il caso mobile**, e viene giusto da solo: il telefono si attacca e la
tela nasce della forma del telefono — pixel veri, niente bande, niente scalatura. Nessuna
delle alternative discusse (tela fissa generosa, tela con vista scorrevole) faceva altrettanto
bene senza logica aggiuntiva.

**L'attacco funziona su tutti e quattro i desktop**, KDE compreso: la misura si scrive nella
riga di avvio del compositore (`--virtual --width W --height H`) **prima** che la sessione
parta, e la sessione parte al primo attacco.

### 5.0-bis 🔸 Il riattacco a misura diversa su KDE ≤ 6.7.4: degradazione dichiarata

> ⚠ *Il titolo diceva «KDE < 6.8», e §5.0-quater prometteva quella versione «a ottobre».*
> ⛔ **Corretto il 14 agosto 2026**: `[R]` verificato su invent.kde.org, **`Plasma/6.8` non
> esiste**, l'ultimo tag è **v6.7.4**, e i rami da `Plasma/6.3` a `Plasma/6.7` non hanno il
> ridimensionamento a caldo — c'è **solo su `master`**, senza una data di rilascio. ⇒ Una
> degradazione con una scadenza scritta invecchia peggio di una senza: qui la scadenza **non
> c'è**, e va detto.

È l'unico punto in cui il modello non può essere servito. A sessione viva KWin 6.3.6 non
cambia misura `[M]`, e riavviarlo significherebbe uccidere la sessione — cioè distruggere
proprio il distacco che il modello offre.

**Ripiego: si tiene la tela vecchia e riscala il client.** Non costa una riga in più, perché è
lo stesso codice del punto «durante la sessione». Su Debian stabile, riattaccandosi da un
dispositivo di forma diversa, si vede il desktop della forma precedente riscalato, finché la
sessione non viene chiusa. Su GNOME, wlroots e KDE ≥ 6.8 si vede la forma nuova.

Il ripiego **si dichiara nel registro** (`CODER.md` §4.2): un ripiego silenzioso produce due
comportamenti sotto la stessa etichetta.

### 5.0-ter 🔸 `[?]` Ridurre anche la misura codificata quando la finestra è piccola

Se l'utente restringe molto la finestra, il server continua a codificare la tela intera e il
client la rimpicciolisce: quei pixel si pagano in banda senza vederli. Si **potrebbe** far
scendere anche la misura codificata sotto una certa soglia, con assestamento.

⚠ **Non è nel modello, ed è volutamente fuori**: prima va misurato se il problema esiste
davvero, e quanto pesa. Un'ottimizzazione decisa prima della misura è §7.2 di `LEZIONI.md` —
ottimizzare nella direzione sbagliata.

### 5.0-quater 🔸 ⛔ ~~Con il browser, «la risoluzione del client» sono due misure diverse~~ → **la tela è la FINESTRA**

> ## ⛔⛔ SUPERATA DA §5.0-sexies, e attuata il 15 agosto 2026
>
> *Questa voce sceglieva **lo schermo del dispositivo** come tela, e la finestra come vista. ⛔ È
> stata rovesciata da §5.0-sexies — decisa dall'utente il 14 agosto — che prende **la finestra**:
> tela e vista coincidono, la scala vale 1 e la conversione delle coordinate sparisce.*
>
> ⚠ **E le due ragioni di questa voce non erano sbagliate: erano legate a un vincolo che non c'è
> più.** La prima diceva che una finestra piccola darebbe *«un desktop piccolo per tutta la
> sessione»* — vero **finché la tela non si poteva cambiare**. Da quando `figli_ritela()` →
> `cattura_ridimensiona()` esiste (`[M]` 6 ms a caldo, 15 agosto), la tela si rifà a ogni riattacco
> e, con `?adatta=segui`, anche durante la sessione.
>
> ⭐ **E la `[?]` dello zoom di pagina, che questa voce lasciava aperta, si è chiusa da sé**: la
> misura non si legge più dallo schermo — si legge dalla finestra, e il fattore di zoom ci è già
> dentro. Un client con zoom ≠ 100 % non dichiara più una tela sbagliata: dichiara la sua.
>
> ⇒ Quel che resta valido qui sotto è la **distinzione fra tela e vista** e il perché sono due
> grandezze diverse. Quel che cade è **quale delle due misure diventa la tela**.


*9 agosto 2026, chiedendolo l'utente dopo il passaggio al client web: «resta da chiarire il
comportamento della risoluzione avendo adesso come client un browser».*

§5.0 dice *«la sessione legge la risoluzione del client e usa quella»*, e con un programma nostro a
schermo intero non c'era altro da dire. ⛔ **Un browser è una finestra dentro uno schermo**, e le due
misure differiscono — su un telefono di un fattore tre, per via dei pixel logici.

| | |
|---|---|
| **la tela** | 🔸 **lo schermo del dispositivo, in pixel fisici** |
| **la vista** | la finestra, in pixel fisici |

**Le due ragioni, e la seconda non l'aveva vista nessuno:**

1. la tela **è il desktop**: prendendola dalla finestra, un collegamento aperto per caso in una
   finestrella darebbe un desktop piccolo **per tutta la sessione** — e §5.3 ha già dichiarato che
   ingrandire non inventa dettaglio;
2. ⭐ **la Keyboard Lock esiste solo a schermo intero** (`web.md` §5). Cioè il modo in cui questo
   prodotto si usa davvero *è* lo schermo intero, che è **esattamente la condizione in cui vista e
   tela coincidono**. Il modello non ha un caso normale e un caso degradato: ha un caso normale che
   coincide con quello ottimo.

⚠ **Non cambia nessuna decisione presa**: §5.0 resta (la tela la detta il client, all'attacco), §5.1
resta (ridimensionare la finestra non tocca il desktop), §5.2 resta come corretta oggi (si codifica
la tela, il client riscala). Cambia **che cosa il client legge** per rispondere.

`[?]` **E tre cose da misurare prima di crederci**, tutte in `SPECIFICHE.md` §6.1-bis: che lo zoom
della pagina non falsi il conto — ⛔ *l'utente che ha premuto `Ctrl +` prima di collegarsi
dichiarerebbe una tela sbagliata, e resterebbe per tutta la sessione* — che cosa risponde DeX, e se
l'arrotondamento dei browser possa produrre un numero dispari, che `RCP.md` §4.5 rifiuta.

> ### ⛔ La prima delle tre È MISURATA, e la risposta è la peggiore — `[M]` 10 agosto 2026
>
> *Banco **S5**, `banchi/01-s5-tela.sh` + `01-s5-pagina.html`, registro `banchi/01-s5-esiti.jsonl`
> (due giri identici, 23:13 e 23:14). Scena: schermo **Xvfb 1920×1080×24**, risoluzione letta **fuori
> dal browser** con `xdpyinfo` = 1920×1080. Il dettaglio sta in `web/rapporti/S-esiti-sonda.md` §3.*
>
> | Motore | zoom | `screen` | `devicePixelRatio` | **tela che il client dichiarerebbe** |
> |---|---|---|---|---|
> | **Chrome 151.0.7922.108** | 100 % | 1920×1080 | 1 | 1920×1080 |
> | | 150 % | **1920×1080** | 1,5 | ⛔ **2880×1620** |
> | **Firefox 140.13.0esr** | 100 % | 1920×1080 | 1 | 1920×1080 |
> | | 150 % | **1280×720** | 1,5 | ✅ 1920×1080 |
>
> ⛔ **Su Chrome `screen.width` NON cala con lo zoom di pagina**, mentre `devicePixelRatio` sale:
> la formula di `SPECIFICHE.md` §6.1-bis dà `risoluzione × zoom`. Un utente su un portatile 1920×1080
> con lo zoom al 150 % dichiarerebbe una tela **del 50 % più grande di quella che esiste** — ed è
> **esattamente il difetto che questa decisione dice di esistere per evitare**.
>
> ⛔ **Quindi la ragione scritta accanto a questa decisione era `[?]` e adesso è FALSA su un motore
> su due.** `fasi/01-filo-nudo.md` la giustificava così: *«`screen.width` cala di un terzo,
> `devicePixelRatio` sale di un mezzo, **il prodotto resta**»*. Resta su Firefox. Su Chrome no.
> È il caso di `LEZIONI.md` §2.3-quater preso in flagrante: *una decisione presa citando un
> comportamento non misurato è presa a metà* — e stavolta il comportamento, misurato, va nell'altro
> verso.
>
> ⚠ **Che cosa NON cambia, e va detto per non far credere a un ripensamento**: la decisione resta 🔸
> e resta *«la tela è lo schermo del dispositivo in pixel fisici»*. Quel che cade è **la formula con
> cui il client lo legge**, non che cosa deve leggere. ⛔ E non si aggiusta con una riga: lo zoom di
> pagina **non è leggibile da JavaScript in modo portabile**. La cura è di chi tiene `SPECIFICHE.md`
> §6.1-bis, e finché non c'è, un client su Chrome con zoom ≠ 100 % **dichiara una tela sbagliata**.
>
> ⚠ **E metà di S5 non è misurata**: il **DeX** non c'era. *«Il Chrome del portatile lo fa»* non dice
> niente del Chrome del telefono — forma **E10** — e la seconda delle tre `[?]` resta intera.

### 5.0-quinquies ✅ ⭐ ~~La tela resta **1920×1080**~~ → **accesa da §5.0-sexies il 14-15 agosto**

> ⭐ **Questa voce si è chiusa da sé, come aveva previsto.** Diceva: *«resta aperta, e va nominata
> alla fase in cui si accende, l'attuazione di `SPECIFICHE.md` §6.1»*. Quella fase è stata la **coda
> della fase 4**: §5.0-sexies l'ha decisa il 14 agosto e il 15 la tela ha smesso di essere
> 1920×1080 — prende la misura della finestra del client (`[M]` 1264×800 su una finestra 1265×800).
> ⚠ Il ragionamento qui sotto **resta valido per il suo giorno**, e la sua ultima riga è quella che
> ha aperto la porta.

*13 agosto 2026, all'apertura della fase 3, **decisa dall'utente**. Era ereditata dalla scena di un
banco e non era mai stata decisa da nessuno: `src/main.c:111` ha `TELA_L 1920` scritto a mano.*

La domanda è stata posta con il suo prezzo misurato accanto: sullo schermo dell'utente la tela
viene dipinta all'**86 %**, cioè **912 px di nero**. Le tre alternative messe davanti:

| | |
|---|---|
| ⭐ **tenerla a 1920×1080** | **scelta** |
| portarla a 2560×1440 (lo schermo dell'utente) | non scelta |
| accendere subito `SPECIFICHE.md` §6.1 — *la tela nasce dallo schermo del client* | non scelta: oggi il prodotto non lo fa |

⭐ **La ragione è di metodo, ed è la ragione per cui la decisione è stata presa il giorno stesso in
cui la fase si apriva**: la fase 3 misura il **tempo**, non la geometria. Con la tela ferma, un
ritardo che sfora i 50 ms accusa l'architettura; con la tela cambiata sotto, non si saprebbe se
accusa l'architettura o il conto dei pixel.

⛔ **E le bande nere non sono la risoluzione**, o la `[?]` verrà riaperta credendo di curarle:
2545×927 di finestra fanno un rapporto **2,74** contro un 16:9 di **1,7778**. Quelle bande sono la
**forma della finestra**, e sparirebbero solo a schermo pieno — cambiare la tela non le tocca.

⏳ **Resta aperta**, e va nominata alla fase in cui si accende, l'attuazione di `SPECIFICHE.md`
§6.1: oggi è una specifica scritta e **non attuata** (§5.0-quater ne racconta il pezzo difficile).

### 5.0-sexies ✅ ⭐⭐ La tela del server prende la misura della tela del client — e la conversione delle coordinate **sparisce**

*14 agosto 2026, sera, **decisa dall'utente** dopo una giornata in cui il mouse sul DeX è rimasto
inutilizzabile attraverso quattro cure. Sue parole: «abbiamo due tele: quella del server e quella
del client (la dimensione della finestra di rendering del browser). Bisogna solo convertire le
coordinate» — e poi, chiedendo la verifica: «se questo è possibile, allora non servono più nemmeno
le conversioni».*

⭐ **Non rovescia §5.0-quinquies: la accende.** Quella decisione teneva la tela a 1920×1080 per una
ragione di **metodo** («la fase 3 misura il tempo, non la geometria») e lasciava scritto ⏳ *«resta
aperta, e va nominata alla fase in cui si accende, l'attuazione di `SPECIFICHE.md` §6.1»*. È questa.

| | |
|---|---|
| **la tela del server** | si chiede della misura della **tela del client**, arrotondata in giù al **pari** |
| **la tela del client** | si stringe alla misura **concessa** ⇒ le due coincidono |
| **la conversione** | `x_desktop = x_tela`: **l'identità** |
| **le bande nere** | non esistono più *dentro* l'immagine: quel che avanza (≤1 px per asse) è **sfondo della pagina fuori dalla tela**, e non viaggia sul filo |

> ⚠ **E il monito di §5.0-quinquies non è stato ignorato**, è stato letto: *«le bande nere non sono
> la risoluzione… sono la forma della finestra, e cambiare la tela non le tocca»*. ⭐ È vero per il
> cambio che quella voce esaminava — da 1920×1080 a 2560×1440, **sempre 16:9**. Qui la tela prende
> il **rapporto del client**, quindi il monito non si applica: le bande spariscono perché sparisce
> la differenza di forma che le genera.

#### Le misure che l'hanno resa possibile — quattro banchi in parallelo, 14 agosto 2026

| | misura esatta | cambio a caldo |
|---|---|---|
| **Mutter** (GNOME) | `[M]` **30 richieste su 30**, da 1×1 a 7680×4320, scala **1,000000**, passo senza riempimento | `[M]` primo fotogramma nuovo a **41,6 ms**, nessun nero, sessione ed EIS intatti; **20 ridimensionamenti in 2 s, 20 esatti** |
| **labwc** (XFCE, LXQt) | `[M]` esatta **anche a larghezza dispari**; `1×1`, `1919×1079`, `32768×1080` tutte al pixel | `[M]` **5,1 ms**, **0 fotogrammi persi su 25** |
| **KWin** (KDE) | `[R]` nessuna validazione: né minimo, né massimo, né parità, né multipli | ⛔ solo su `master` — vedi §5.0-bis |
| **il codificatore** | `[M]` il vincolo è **pari, e basta** — non multiplo di 8 né di 16 | — |

⛔ **Il vincolo del pari è NOSTRO, non dei compositori**: è il 4:2:0 (`src/codificatore.c:1373` e
`:1512`). `[M]` In 4:4:4 passa anche il dispari. ⇒ Si tronca in **giù** (2133 → 2132) e **lo si
dichiara** con `TELA(ADATTATA)`: un pixel detto vale più di un pixel nascosto in una scala.

#### ⛔ Le tre guardie che dobbiamo scrivere noi — nessuno le fa a monte

Tutte e tre scoperte misurando, e tutte e tre della stessa famiglia: **il silenzio**.

1. **Il tetto della misura.** `[M]` Oltre **16384** per lato `gnome-shell` muore — e 16386 è
   *dentro* il `MAX_SIZE` che Mutter **dichiara**, quindi il limite dichiarato mente. `[M]` Su
   labwc `32768×32768` uccide il compositore **con zero righe di registro**. ⇒ Il tetto lo mette il
   nostro codice, e un client non può sceglierlo senza limiti.
2. ⛔⛔ **La scala di GNOME.** `[M]` Con `org.gnome.desktop.interface scaling-factor = 2` i pixel
   restano quelli chiesti ma il monitor logico prende **scala 2,0**: il layout diventa
   `roundf(2133/2) = 1067` e **1067×2 = 2134 ≠ 2133**. È lo spazio delle coordinate dell'**input**
   ⇒ **il puntatore va altrove e nessuno lo dice.** Cura: leggere la scala e **fallire** se non è
   `1,0`.
3. **Chiesto contro concesso.** `[R]` `src/cattura.c:914` non confronta mai la misura **chiesta** a
   PipeWire con quella **negoziata**, e `codificatore_comprimi()` riceve i pixel e il passo ma
   **non** larghezza e altezza, quindi non può fare da testimone. ⛔ Oggi è irraggiungibile perché
   si chiede sempre 1920×1080: **è questa decisione a renderlo raggiungibile**, e va chiuso
   insieme, non dopo.

#### La regola di forma, rubata a neatvnc

⭐ `[M]` Chiedere a labwc la misura **che l'output ha già** risponde «riuscito» e **non manda
nessun evento**; un serial vecchio risponde «annullato» e non fa niente. ⛔ `wayvnc` tratta
*riuscito*, *fallito* e *annullato* nello stesso ramo — da non copiare. ⇒ **La verità la dice il
fotogramma, non l'esito della richiesta.**

#### ⏳ ⭐ Per quando si affronterà il RI-ATTACCO: la soluzione è già misurata, e sta qui

*Annotato su richiesta dell'utente, 14 agosto 2026: «il problema della dimensione della finestra
del browser si ripresenterà, ma la soluzione è già bella pronta».*

⛔ **La domanda tornerà, ed è inevitabile**: §4.1 promette che **la sessione sopravvive al
client**, e §5.0 che la tela **nasce a ogni attacco**. ⇒ Il giorno in cui l'utente si stacca dal
DeX e si riattacca dal portatile, la finestra del browser ha **un'altra misura** — e la tela del
server è quella di ieri. È esattamente il caso che oggi produrrebbe di nuovo bande, scala e
conversione.

⭐ **E la risposta non va cercata quel giorno: è stata misurata il 14 agosto 2026**, ed è il
ridimensionamento **a caldo**, sulla sessione viva, senza rifarla:

| | costo misurato | che cosa NON succede |
|---|---|---|
| **Mutter** (GNOME) | `[M]` primo fotogramma nuovo a **41,6 ms** · **20 ridimensionamenti in 2 s, 20 esatti** | nessun fotogramma nero, **sessione ed EIS intatti**, nessuna riconnessione |
| **labwc** (XFCE, LXQt) | `[M]` **5,1 ms** · **0 fotogrammi persi su 25** | nessun fotogramma nero; il fotogramma successivo è già alla misura nuova |
| **KWin** (KDE ≤ 6.7.4) | ⛔ non esiste | ⇒ vale il ripiego dichiarato di §5.0-bis, e **solo lì** |

⇒ ⭐ **Il ri-attacco a misura diversa non è un problema aperto: è un caso già coperto**, su tre
desktop su quattro, a un costo che l'utente non percepisce. Chi affronterà quel tema non deve
studiare niente di nuovo — deve **chiamare** `cattura_ridimensiona()` e rileggere questa tabella.

> ### ✅ ⭐⭐ SCRITTA E MISURATA — la notte del 15 agosto 2026
>
> *Questa voce diceva «`cattura_ridimensiona()` alla data di questa voce **non esiste ancora**: è
> l'unica riga di lavoro rimasta». Adesso esiste, e con lei la catena intera.*
>
> **La catena, per nome**, e ogni anello sta dove sta la cosa che sa:
>
> | dove | che cosa |
> |---|---|
> | `src/pagina.html` | `chiedi_tela()` manda `ADATTA_TELA` con la misura della finestra, **all'attacco** |
> | `src/rcp.c` `T_ADATTA_TELA` | applica §4.5 (limiti, parità, `video.misura_massima`) e gira la richiesta al palco. ⛔ **Non risponde subito**: segna una richiesta «in volo» |
> | `src/webtransport.c` · `src/main.c` | portano la domanda oltre il confine di processo |
> | `src/figlio.c` `figli_ritela()` | → `MSG_INPUT/RITELA` al figlio |
> | `src/cattura.c` `cattura_ridimensiona()` | → `pw_stream_update_params()` |
> | ⭐ e **la risposta torna indietro**: `MSG_TELA` → `rcp_tela_dal_palco()` → `TELA(ADATTATA)` |
>
> ⛔ **La risposta torna, e non si indovina**: la prima stesura di stanotte faceva dedurre al padre
> l'esito **dai fotogrammi** («se ne arriva uno di misura diversa, il palco ha obbedito»), e quattro
> agenti mandati a refutarla hanno trovato tre casi in cui deduceva male — fra cui **due
> `ADATTA_TELA` incatenate**, cioè un utente che trascina il bordo della finestra. ⇒ Il figlio adesso
> risponde portando **due** misure: quella *chiesta* (per riconoscere a quale richiesta risponde) e
> quella *avuta* (`0x0` = non ce l'ha fatta).
>
> #### `[M]` Le misure della notte, sulla macchina di prova, utente `prova`, GNOME headless
>
> | | prima (14 ago) | adesso (15 ago) |
> |---|---|---|
> | ⭐⭐ dal canale video al primo fotogramma | **4,4 s** (659 «attese a vuoto») | **311 ms** |
> | la tela in vigore all'attacco | 1920×1080 fissa | **1264×800** = la finestra del browser |
> | la scala di disegno del client | 0,658 (`imageRendering: auto`) | **1,000** (`pixelated`) |
> | il ridimensionamento a caldo (1264×800 → 1000×640) | non esisteva | ⭐ **6 ms** dalla risposta del palco alla chiave spedita |
> | fotogrammi scartati per misura · trattenuti · errori | — | **0 · 0 · 0** |
>
> ⭐ **E il desktop lo dice da sé**: GNOME *Impostazioni → Displays* dentro la sessione remota
> riporta **«Resolution 1264 × 800 (3:2)»** e **«Scale 100%»**. Non è una nostra riga di registro:
> è il compositore che dichiara la misura che gli abbiamo chiesto.
>
> #### Le tre guardie: dove sono finite
>
> | guardia | stato |
> |---|---|
> | 1 · il tetto della misura | ✅ `rcp_misura_ammessa()`, e ⛔ **corretta stanotte**: i limiti sono quelli di §4.5 **per lato** (320..7680 × 240..4320), non i 200..8192 della prima stesura — che `ATTACCA` avrebbe rifiutato al ri-attacco |
> | 2 · la scala di GNOME | ✅ **chiusa stanotte** come §5.0-sexies chiedeva («leggere la scala e **fallire**»): `mutter_scala_nostra()` + il rifiuto in `prendi_il_palco()`. ⚠ Si guarda il **nostro** monitor, non il peggiore della macchina: un portatile con lo schermo interno a 2,0 non ha nessun difetto. `[M]` sulla macchina di prova la scala del nostro «Meta-0» è **1,000**, e la riga si scrive anche quando è buona |
> | 3 · chiesto contro concesso | ✅ in `cattura.c` (`su_parametri`), e da stanotte anche **nel figlio**: i 28 byte di §6.2 portano la misura del FOTOGRAMMA, non quella che si era chiesta |
>
> #### I tempi, e il perché di ciascuno
>
> | | valore | perché |
> |---|---|---|
> | `RCP_TELA_ATTESA_MS` | **3000 ms** | il fondo oltre cui si risponde `NON_ORA` comunque: §7.1 vuole un `TELA` per ogni `ADATTA_TELA`, e §6.2 fa **trattenere fotogrammi** al client finché aspetta |
> | `RCP_TELA_RICHIAMO_MS` | 500 ms, che raddoppia fino a 8 s | ogni quanto si **richiede** al palco di tornare alla tela in vigore, quando ne ha una sua |
> | `TELA_FONDO_MS` (client) | 250 ms | chi trascina un bordo produce decine di `resize` al secondo, e ogni richiesta girata al palco costa un fotogramma |
> | `RISVEGLIO_MS` (figlio) | 400 ms | ogni quanto si riavvia il flusso quando **una chiave è dovuta e la scena è ferma** — è la cura dei 4,4 secondi |
>
> ⛔ **E una cosa che il server NON fa, per una riga che manca a `RCP.md`**: quando il palco cambia
> misura **senza che nessuno gliel'abbia chiesto**, il server **non adotta** la misura nuova e non
> manda nessun `TELA`. La prima stesura lo faceva — sembrava gentile — ed è fatale: §6.2 dice che il
> client trattiene una misura mai annunciata **solo finché ha una `ADATTA_TELA` senza risposta**, e
> senza quella è `ERRORE_PROTOCOLLO`. ⇒ Si **richiede al palco di tornare**, con un'attesa che
> cresce, e nel frattempo la sessione mostra l'ultima immagine buona (I1: brutta e viva). ⏳ La riga
> che manca è in `RCP.md` §7.1: *che cosa fa un server quando il palco cambia misura da sé*.

⚠ E le tre guardie qui sopra valgono **a maggior ragione** al ri-attacco: è il momento in cui la
misura cambia davvero, cioè il momento in cui una divergenza silenziosa fra chiesto e concesso
avrebbe le sue conseguenze.

#### Su KDE non cambia niente: vale §5.0-bis

⚠ *E §5.0-bis va corretta in un punto*: diceva «KDE < 6.8». `[R]` Verificato il 14 agosto su
invent.kde.org: **`Plasma/6.8` non esiste**, l'ultimo tag è **v6.7.4**, e il ridimensionamento a
caldo è **solo su `master`**, senza una data. ⇒ Si legga «KDE ≤ 6.7.4, e la versione che lo porta
non è ancora uscita».

### 5.1 ✅ Se l'utente ridimensiona la finestra, l'immagine si riscala

*8 agosto 2026. «Tagliamo la testa al toro. Anziché correre dietro ai compositor, una scelta
che vale per tutti».*

**Ridimensionare la finestra del client non tocca mai il desktop.** Si adatta la vista; le
finestre dell'utente non si muovono. Uguale su GNOME, KDE, XFCE e LXQt.

> ### ⚠ E DAL 15 AGOSTO 2026 QUESTA VOCE VALE **DURANTE** LA SESSIONE, NON ALL'ATTACCO
>
> §5.0-sexies ha deciso che **la tela del server prende la misura della tela del client**, e quella
> misura la si chiede **all'attacco di ogni sessione**. ⇒ All'attacco il desktop *cambia* misura, ed
> è voluto: è la decisione dell'utente del 14 agosto.
>
> ⛔ **Ma le tre ragioni di questa voce non sono invecchiate**, e la terza meno che mai: su KWin
> ridimensionare un output **ridispone le finestre dell'utente**. ⇒ Durante la sessione viva il
> comportamento resta quello scritto qui — si riscala la vista, il desktop non si tocca — e
> l'inseguimento della finestra sta dietro un interruttore **spento di suo** (invariante I6):
>
> | `?adatta=` | che cosa fa |
> |---|---|
> | *assente* (predefinito) | chiede la tela **all'attacco** e basta |
> | `segui` | ⚠ la chiede **anche a ogni ridimensionamento** della finestra, con un fondo di 250 ms |
> | `no` | ⛔ non la chiede mai: è la pagina di prima del 15 agosto, e serve al **confronto A/B** che il giudizio dell'utente richiede (`LEZIONI.md` §7.3) |
>
> ⚠ Si legge da `?` **e** da `#`, come `video` e `disposizione`.

Le tre ragioni, e la terza è quella che ha deciso:

1. su KDE 6.3.6 — cioè Debian Trixie — **non si può** ridimensionare: la misura sta nella riga
   di comando di KWin (`--virtual --width W --height H`), il modo è `const`, e
   `stream_virtual_output` risponde `Could not find output` per ogni misura `[M]` 8 ago;
2. la correzione a monte esiste (`kwin!7932`, traguardo 6.8, ottobre) ma **Debian stabile non
   aggiorna Plasma**: 6.3.6 fino a Forky. Il ripiego non è un'impalcatura temporanea, è un
   percorso di codice da mantenere per anni;
3. ⛔ **e anche dove funziona, fa una cosa peggiore**: ridimensionare un output ridispone le
   finestre dell'utente `[R]`. Su KWin la chiave del `PlacementTracker` contiene la geometria
   dell'output, quindi tornando a una misura già vista le finestre vengono **teleportate**
   indietro. La versione «giusta» scompiglia il lavoro; quella «rotta» lo lascia fermo.

**Conseguenze:**
- il ridimensionamento del compositore esce dal percorso critico e resta come funzione
  facoltativa («adatta il desktop a questa finestra»), spenta dove il compositore non la sa
  fare, **con la ragione dichiarata** (`CODER.md` §4.2);
- quando si scriverà, si scriverà **nella forma della negoziazione PipeWire** — decisione già
  presa in `kde.md` §8.2 — perché è una strada sola per GNOME, wlroots e KDE 6.8, e su KDE si
  accende da sé all'aggiornamento;
- ⚠ e includerà la **guardia obbligatoria** `if (misura_attuale == misura_richiesta) return;`
  (`kde.md` §8.2-bis): senza, la rinegoziazione si morde la coda. Il difetto **non si vede su
  Trixie** e compare il giorno dell'aggiornamento a 6.8, quando nessuno lo sta più cercando.

### 5.2 🔸 ⛔ ~~Il codificatore lavora alla misura della finestra~~ → **no: lavora alla misura della tela**

> ⛔ **Corretta il 9 agosto 2026, scrivendo `RCP.md` §6.2.** Questa voce diceva: *«Regalo che
> arriva gratis da 5.1: finestra piccola ⇒ meno pixel da codificare ⇒ la stessa banda rende di
> più»*. **Contraddiceva §5.0-ter**, che è a due voci di distanza e dice il contrario — *«il server
> continua a codificare la tela intera e il client la rimpicciolisce»* — mettendo l'ottimizzazione
> **volutamente fuori dal modello**, come `[?]` da misurare prima.
>
> **Vince §5.0-ter**, e non per anzianità: è quella che regge insieme al resto. `SPECIFICHE.md`
> §6.1 dice che durante la sessione **è il client a riscalare**, e §6.3 dice che il ripiego su KDE
> *«non costa una riga in più, perché è lo stesso codice del punto durante la sessione»* — cioè la
> riscalatura nel client. Se il server codificasse alla misura della finestra, quel codice non
> esisterebbe e il ripiego costerebbe eccome.
>
> ⚠ **Il regalo non era gratis**: cambiare la misura codificata a ogni trascinamento del bordo
> significa rinegoziare il codificatore — e con `DECISIONI.md` §5-bis.0 il bordo si trascina
> **dieci volte al giorno**, perché su DeX la finestra è ridimensionabile. Era una `[?]` travestita
> da conseguenza, cioè la forma d'errore **E5** di `REVIEWER.md`.

**Quel che vale adesso**: il server codifica alla misura della **tela**, il client riscala. Il
messaggio `VISTA` di RCP esiste lo stesso e serve a scegliere **quanti bit spendere**, non quanti
pixel produrre; e l'intestazione del fotogramma porta la misura come campo, così che il giorno in
cui §5.0-ter venisse chiusa **il protocollo non cambi** (`RCP.md` §6.2, §7.1).

### 5.3 🔸 Il prezzo di 5.1, dichiarato

Tela 1080p vista da uno schermo 4K = desktop ingrandito, quindi morbido. Ingrandire non
inventa dettaglio. La via d'uscita è la voce «adatta il desktop», ed è il motivo per cui la
misura iniziale della tela conta — vedi la domanda aperta §7.1.

---

## 5-bis. L'input

### 5-bis.1 ✅ Il puntatore lo disegna il client, non il desktop

*8 agosto 2026, proposta dall'utente.*

Il dito trascina un puntatore **disegnato dal client**; un tap fa il clic sinistro sulla
posizione del puntatore, un tap a due dita il destro. Non è il «tocco diretto», dove il dito
è il puntatore: è il trackpad, e si vede dove si sta per cliccare **prima** di cliccare.

**Tre problemi diversi che questa scelta chiude insieme:**

1. ⭐ **la latenza percepita.** Il puntatore si muove alla velocità del dito, non a quella
   della rete. Su un collegamento mobile con 150 ms di ritardo è la differenza fra usabile e
   frustrante — e pesa più dei fotogrammi al secondo, che è la grandezza che di solito si
   guarda;
2. **le scie e le posizioni vecchie** del puntatore, che nascono proprio dal fatto che il
   puntatore viaggi *dentro il video* e arrivi in ritardo;
3. **la precisione.** Un dito è largo ~10 mm, i bersagli di un desktop ne misurano ~4, e nel
   tocco diretto il dito **copre il bersaglio** mentre lo si cerca. In più il passaggio del
   puntatore — da cui dipendono suggerimenti e menu — esiste solo se un puntatore c'è davvero.

### 5-bis.2 🔸 Il cursore non deve MAI essere dentro l'immagine catturata — e va verificato

Discende da 5-bis.1: se lo disegna il client e c'è anche in quel che arriva, se ne vedono
**due**. v1 aveva incontrato il problema tre volte senza collegarle, e la cura è la sua:
*«non nasconderlo: renderlo invisibile»* — un tema con un cursore 1×1 ad alfa zero.

| Desktop | Il cursore è nella cattura? | Il canale della cura |
|---|---|---|
| GNOME / Mutter | **no**, lo esclude di suo (`inhibit_cursor_overlay`) | ⚠ e se servisse, **non** `XCURSOR_THEME`: Mutter non la legge, legge `org.gnome.desktop.interface cursor-theme` |
| KDE / KWin `--virtual` | **sì** `[M]` — niente piano cursore ⇒ dipinto nel framebuffer | `XCURSOR_THEME` (+ `XCURSOR_SIZE`, che KWin pretende) |
| wlroots — XFCE, LXQt | **sì, sempre** su headless; `overlay_cursor` non lo toglie, lo **forza software** | `XCURSOR_THEME`; su labwc `XCURSOR_SIZE` non è obbligatoria |

⛔ **La trappola, e va verificata invece che sperata**: su wlroots un tema che carica **zero**
cursori fa ripiegare la libreria su un tema **incorporato e visibile** — cioè due puntatori,
per un ripiego silenzioso (`REVIEWER.md` E2). Serve almeno un cursore valido, `index.theme`
**senza `Inherits=`**, e i dieci nomi che labwc chiede. E l'esito si **controlla dopo l'avvio
della sessione**: che il tema sia stato scritto non è che sia stato caricato.

*Il posto dove metterlo c'è già: l'ambiente della sessione si compone da zero, una variabile
per volta (`CODER.md` §4.5) — quindi la cura sta nel programma e non in un file, come vuole I7.*

### 5-bis.0 ✅ Su Android l'uso primario è **Samsung DeX**, e il tocco è il ripiego

*9 agosto 2026. «DeX assolutamente. È l'uso primario che faccio quando uso android perché la
verità è che usare certi programmi con il touch anziché nel modo classico è un ripiego di
emergenza, non la normalità.»*

⛔ **Ribalta la priorità con cui era stato progettato l'input Android**, che era tutto attorno al
telefono in mano — cioè al caso che l'utente quasi non usa.

| | Prima | Adesso |
|---|---|---|
| mouse e tastiera fisici (5-bis.8) | un passeggero | **la strada principale** |
| i sette gesti (5-bis.3) | il modello di input | **il ripiego d'emergenza** |
| ridimensionare la finestra (§5.1) | un caso limite | **quel che si fa di continuo** |

Con DeX il telefono pilota uno schermo esterno con mouse e tastiera veri: la tela nasce di forma
**desktop** e non di forma telefono, e la finestra si trascina.

⭐ **Tre decisioni ne escono rafforzate, non indebolite:**

1. **il puntatore disegnato dal client** (5-bis.1) era giusto col dito; con un mouse vero diventa
   non negoziabile — un puntatore che insegue la mano mentre si lavora «nel modo classico» è la
   differenza fra usarlo e chiuderlo;
2. **il ridimensionamento che non tocca il compositore** (§5.1) passa da scelta prudente a scelta
   obbligata: se trascinando il bordo dieci volte al giorno le finestre *dentro* la sessione si
   rimescolassero, il prodotto sarebbe inservibile. Era stato deciso per il muro di KWin; si
   scopre che era giusto anche per l'uso vero;
3. **la regola sui modificatori di comando** (5-bis.6) era una precisazione; lavorando col
   classico diventa **portante**, perché le scorciatoie sono metà del lavoro.

⭐ **E una buona notizia sul costo**: se l'uso primario è DeX, il client Android somiglia molto più
a quello Linux di quanto previsto — stesso modello di interazione, diverso solo nello stack di
decodifica. Riduce il rischio segnalato in §0.3 spostando Android in fondo: il protocollo non è
stato progettato per il client sbagliato, perché i due client si somigliano.

> ⭐ **Confermata e resa più forte dal 9 agosto 2026 (§1.6).** La decisione resta intera — l'uso
> primario su Android è DeX, il tocco è il ripiego — e cambia solo che il programma è **il browser
> su DeX** invece di un'applicazione nostra. ⚠ Da cui una domanda nuova che non c'era, e che va
> alla sonda: **su DeX, in una finestra ridimensionabile, il browser dà `Pointer Lock` e le
> scorciatoie?** Senza il primo si vedono due puntatori (5-bis.8), senza le seconde metà del lavoro
> se ne va nel browser invece che nella sessione.

### 5-bis.0-ter ✅ L'emulatore Android è banco di lavoro, non strumento di misura

*9 agosto 2026. «Per android forse dovremmo ricorrere a degli emulatori (che entrerebbero a far
parte dell'ambiente di sviluppo).»*

Accettato: SDK, emulatore, `adb` e il collegamento al telefono entrano nell'ambiente, e si mettono
già alla **fase 0** perché la sonda della fase 2 li richiede.

⚠ **Corretto lo stesso giorno, dopo che l'utente ha chiesto di cercare meglio.** La prima
stesura diceva che DeX «sull'emulatore non esiste»: **è falso**. Esiste il **Desktop AVD**
(profilo «13.5" Freeform», da Android 11; la versione Android 13 aggiunge scorciatoie da tastiera
e supporto mouse), e **Samsung stessa documenta l'emulatore per DeX** — *«If you don't have the
DeX Station, you can test your app resize behavior in Android Studio using Android Virtual
Device»*, a 160 dpi e 1080×1920. Il modello di interazione che ci interessa **è testabile lì**, ed
è gran parte delle fasi A1 e A3. Samsung avverte però che l'emulatore **simula, non replica**.

⛔ **Il confine resta, ma è più stretto e più netto**: *sull'emulatore si sviluppa, non si misura.*
**Nessun numero di questo progetto viene dichiarato su un emulatore.** Quel che non dà è la
**decodifica in hardware** — il suo MediaCodec non è il silicio del telefono, e `[?]` non si è
riusciti a stabilire che esponga un decodificatore HEVC hardware — più il ritardo vero, la
batteria e la rete che cambia.

⚠ È `REVIEWER.md` **E10**, *una prova verde sul client sbagliato*: un emulatore che dice «funziona»
mentre il telefono no è un banco verde col difetto vivo — la forma che a v1 è costata di più, con
una correzione scritta su un banco che non riproduceva il difetto e spedita all'utente, **che ha
peggiorato le cose**.

**Il telefono vero è lo strumento di misura; l'emulatore è il banco di lavoro.**

> ⛔ **Decade quasi per intero il 9 agosto 2026, con §1.6**: non c'è più un'applicazione Android da
> costruire, quindi non servono né SDK né APK né Desktop AVD — **il banco di lavoro è il browser
> del portatile**, che è più comodo di qualunque emulatore.
>
> ⭐ **Ma la riga che conta sopravvive parola per parola, e vale ancora di più**:
> *«nessun numero di questo progetto viene dichiarato su un emulatore»* diventa **«nessun numero si
> dichiara su un browser che non sia quello del dispositivo vero»**. Un Chrome su portatile che
> decodifica HEVC in hardware **non dice niente** del Chrome del telefono: è la stessa forma
> d'errore **E10**, con un travestimento nuovo.

### 5-bis.0-bis ✅ RDM è un riferimento da cui **ispirarsi**, non un prodotto da rifare

*9 agosto 2026. «Ora noi non dobbiamo rifare RDP e/o RDM, ma secondo me trarne ispirazione sì.»*

⚠ **In v1 RDM aveva un ruolo diverso**: era il **client da servire** — *«se non funziona qui, non
funziona»* (`v1/documenti/client-android.md` §1.2). In V2 il client lo scriviamo noi, quindi
cambia mestiere: da **vincolo** a **riferimento**.

⛔ **E il confine è netto, perché RDM è proprietario** (Devolutions,
`com.devolutions.remotedesktopmanager`): si studia **come si comporta e come si sente all'uso**,
mai come è fatto dentro. La fonte migliore non è comunque il codice: è l'utente, che lo usa tutti
i giorni.

⭐ **Che cosa se ne prende, e viene da una frase sola**: *«funziona bene sia con interfaccia mobile
sia in modalità desktop»*. Non è il video che si adatta — sono **due interfacce**, e
l'applicazione sceglie da sé quale mostrare.

🔸 Da cui, per il nostro client Android: **una sola applicazione, due interfacce**, e il passaggio
è **automatico sul contesto** — schermo esterno e mouse collegati, oppure telefono in mano — non
un'impostazione che l'utente deve andare a cercare. È la forma che le fasi **A3** (il modo
classico) e **A4** (il tocco) hanno già preso.

> ⭐ **Sopravvive intatta al 9 agosto 2026 (§1.6), e diventa più facile**: «una applicazione, due
> interfacce» è **una pagina, due disposizioni**, e il passaggio automatico sul contesto è la cosa
> che una pagina sa fare meglio di qualunque altra tecnologia — si guarda se c'è un puntatore fine
> e quanto è grande la finestra, non «è Android o è Linux». ⚠ La sostanza però non cambia: **due
> disposizioni vere, non una che si stira**, ed è la lezione che si prende da RDM.

**Che cosa invece NON se ne prende:**

| | Perché |
|---|---|
| l'essere un **gestore di connessioni** — RDP, VNC, ARD, SSH, FTP e una cinquantina d'altro | è un pregio per loro e un fuori scope per noi: REMOTIX è un prodotto solo, e `SPECIFICHE.md` §12 esclude la compatibilità con altri protocolli |
| la sua **scelta di codec** (RemoteFX Progressive) | era ingegneria giusta *per RDP e per un telefono senza decodifica hardware*. Noi puntiamo su HEVC in hardware — ⚠ e se la sonda della fase 2 dicesse no, è **questa** la riga da rileggere |

### 5-bis.3 ✅ Il ventaglio dei gesti — **il ripiego, non la strada principale**

*9 agosto 2026, confermati tutti e sette. ⚠ E ridimensionati lo stesso giorno da 5-bis.0: su
Android l'uso primario è DeX, con mouse e tastiera veri. Questi gesti servono al telefono in
mano, che è il ripiego d'emergenza — restano necessari, ma non sono la cosa da azzeccare per
prima.*

| Gesto | Effetto |
|---|---|
| 1 dito trascina | muove il puntatore |
| 1 dito tap | clic sinistro |
| 2 dita tap | clic destro |
| 2 dita trascina | rotella / scorrimento |
| tap-e-mezzo (tap, poi premi e trascina) | trascinamento e selezione |
| 3 dita tap | clic centrale |
| pizzico | ingrandisce la **vista** del client, non l'applicazione |

⚠ Il *tap-e-mezzo* non è un lusso: senza, non si sposta una finestra e non si seleziona del
testo. Tap e trascinamento a due dita non si confondono — un tap è breve e fermo.

> ⭐ **E con quale riserva sono stati confermati**, che vale più della tabella: *«tanto poi sono
> sicuro che su alcune specifiche ci torneremo quando avremo il sistema funzionante sotto
> mano»*. È `LEZIONI.md` §7.3 applicata ai gesti, e sui gesti vale doppio — un gesto non si
> giudica leggendolo, si giudica usandolo. Questa tabella è quindi un **punto di partenza
> dichiarato**, non un impegno: chi la trova diversa fra sei mesi non ha trovato un difetto.

### 5-bis.3-bis ✅ ⭐ La barra porta **un bottone solo**: `Ctrl+Alt+Canc`

*14 agosto 2026, deciso dall'utente davanti alla misura della fase 4.*

⛔ **Il fatto che ha prodotto la domanda, ed è `[M]`** (`fasi/rapporti/F4-A9-scorciatoie.md`): sei
combinazioni **non arriveranno mai** al desktop remoto — `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`,
`Alt+F4`, `Ctrl+Alt+Canc`. ⚠ E non è un limite del browser: **le prende il compositore del client**,
e **nessuna API le riprenderà mai**. L'unico modo di darle è un bottone a schermo — che però toglie
pixel all'immagine del desktop.

**Scelto: uno solo.** ⛔ E la ragione per cui è quello e non un altro è di natura diversa dal gusto:
senza `Ctrl+Alt+Canc`, **in una sessione bloccata l'utente non entra più** — è l'unica delle sei che,
mancando, lo lascia **fuori** invece che scomodo. `SPECIFICHE.md` §7.3-bis la chiama *«un requisito,
non un ripiego di fortuna»*, e tre riferimenti maturi su tre lo fanno.

⚠ **Gli altri cinque restano scritti e spenti**, con la loro ragione accanto: la scelta è di gusto e
si rivede **guardandola**, non leggendola (`LEZIONI.md` §7.3, la stessa riserva con cui l'utente ha
confermato i sette gesti). ⛔ Accenderne uno costa **una riga**.
⛔ **E spento vuol dire NON DISEGNATO**, non «disegnato e inerte»: un bottone che c'è e non fa niente
è peggio di un bottone che non c'è. Le cinque combinazioni restano però **nella tavola delle
dichiarate**, dove l'utente legge che quella battuta se la tiene il suo computer — ⭐ perché
`SPECIFICHE.md` §7.3-bis vieta di **fingere** che siano arrivate, non di non offrirle.

---

### 5-bis.4 🔸 Il canale del cursore, e il suo compromesso

Il client deve sapere **che forma** disegnare: barretta sul testo, doppia freccia sui bordi,
mano sui collegamenti. Serve quindi un canale che porti **forma e punto attivo** quando
cambiano.

Il compromesso, accettato: la **posizione** è immediata perché locale, la **forma** arriva con
un giro di rete di ritardo. Muovendo in fretta sopra un bordo, la doppia freccia compare un
attimo dopo. È il verso giusto del compromesso — il ritardo di una forma non lo nota nessuno,
quello di una posizione lo notano tutti.

### 5-bis.5 🔸 Che cosa porta il canale di input

| | |
|---|---|
| puntatore **assoluto** | sì — ed è **l'unico** percorso del puntatore (vedi 5-bis.8) |
| ~~puntatore relativo~~ | ⛔ **tolto il 9 agosto**: era motivato con *Pointer Capture*, e la motivazione era sbagliata. Vedi 5-bis.8 |
| **scancode** | sì — tasti di controllo e tastiere fisiche |
| **Unicode** | sì, e su Android è la **strada principale** (vedi §7.10-bis) |
| **tocco multi-dito** | posto riservato, **non implementato** `[?]` |
| **stilo** (pressione, inclinazione) | fuori, per ora |

Il tocco nativo non entra perché non risolve la precisione, le applicazioni desktop lo
gestiscono male, e andrebbe verificato che l'EIS di Mutter e KWin espongano la capacità
«touch» — `libei` la prevede, che i due la offrano è `[?]`. Il **posto riservato** costa niente
adesso e fa risparmiare una riscrittura se un giorno servisse.

### 5-bis.6 ✅ Le lettere viaggiano come lettere, i tasti che non sono lettere come posizioni

*8 agosto 2026.*

| Che cosa | Come viaggia |
|---|---|
| lettere, numeri, segni — tutto ciò che si stampa | **come lettere** (carattere) |
| Invio, Tab, Esc, frecce, F1-F12, Ctrl, Alt, Maiusc, Super | **come posizioni** — non sono lettere, e stanno nello stesso posto su ogni tastiera |

**Il problema che questa scelta scioglie**, ed è quello che l'utente ha isolato da sé: una
tastiera fisica non manda lettere, manda **posizioni** — il tasto a destra della L dice «tasto
39», ed è il desktop a decidere se significa «ò» (disposizione italiana) o «;» (americana). Se
sul filo viaggiassero le posizioni, un client con tastiera americana attaccato a una sessione
italiana produrrebbe **le lettere sbagliate**: è il difetto classico di ogni desktop remoto.

Facendo viaggiare le lettere, la disposizione del *client* la applica il sistema del client, e
la nostra sessione non deve indovinare niente. Vale per **entrambi** i client, non solo per
Android — dove però è obbligatorio comunque, perché una tastiera Android non ha posizioni:
è un IME che produce testo.

⛔ **La precisazione che manca alla riga di sopra, aggiunta il 9 agosto: `Ctrl+C` non è testo,
è un comando.** Mandato come «lettera c», l'applicazione remota riceverebbe una c da scrivere
invece di una copia da fare. Quindi la regola completa è:

> Una battuta viaggia **come lettera** quando sta scrivendo del testo. Quando è tenuto premuto
> un modificatore **di comando** — Ctrl, Alt, Super — viaggia **come posizione**, perché in quel
> momento non è una lettera. Maiusc e AltGr non contano: quelli servono a *fare* la lettera, e
> restano dentro il percorso del testo.

⭐ **E questo dà una seconda ragione a 5-bis.7**, che era stata decisa per un motivo diverso: le
scorciatoie viaggiano come posizioni, e le posizioni combaciano solo se le due disposizioni
sono la stessa. Su una tastiera tedesca la Z sta dove sulla nostra sta la Y — senza
rinegoziare la disposizione all'attacco, `Ctrl+Z` finirebbe su un altro tasto.

⚠ **Resta la sola raggiungibilità.** Se nella disposizione della sessione un carattere non
esiste su nessun tasto — un'emoji, un alfabeto diverso — non esce **niente**, e il server lo
**dichiara nel registro**: mai una lettera diversa, mai un silenzio (`LEZIONI.md` §1.8).

**In dote**: i modificatori non sono mai stati il problema e si emulano normalmente (per «A»:
premi Maiusc, premi 30, rilascia 30, rilascia Maiusc); la ripetizione non è nostra (wlroots
scarta i tasti ripetuti, a ripetere è l'applicazione); e la disposizione dichiarata dal client
— la «questione n.7» di v1 — non serve più per *interpretare*, solo per *scegliere* (5-bis.7).

### 5-bis.6-bis ✅ ⭐ Gli accenti composti e le tastiere asiatiche restano **fuori, dichiarati**

*14 agosto 2026, deciso dall'utente davanti alla misura della fase 4
(`fasi/rapporti/F4-A7-pagina-classico.md`).*

**Che cosa funziona già** `[M]`: la `à` italiana, perché sulla disposizione italiana **è un tasto
suo** e passa dal percorso di `LETTERA` come tutte le altre.

⛔ **Che cosa resta fuori**: i **tasti morti** (la `à` composta in due battute di una tastiera
francese o «US international») e l'**IME** (cinese, giapponese, coreano). ⚠ E resta fuori
**dichiarato**: la pagina lo scrive, e **non fa uscire una lettera diversa né tace** — che è la
regola di `RCP.md` §7.3 applicata al lato del client.

**Il prezzo che si è scelto di non pagare**, ed era previsto: per avere tasti morti e IME serve un
**elemento modificabile col fuoco sopra la tela** — cioè `web.md` §1.2 C — e quell'elemento si mette
**fra il puntatore e l'immagine**: ⛔ il percorso con cui la pagina disegna oggi la freccia **andrebbe
rifatto**. ⇒ Costo certo e visibile, contro un guadagno che per l'utente di oggi è **zero**.

⚠ **E si riapre da sé il giorno in cui servisse una tastiera straniera**: il lavoro è dichiarato, non
perso. `LEZIONI.md` §2.4 — quel che cambia ciò che si vede sta dietro un interruttore finché
qualcuno non l'ha guardato.

---

### 5-bis.7 ✅ La disposizione si rinegozia all'attacco e al riattacco, come la risoluzione

*8 agosto 2026. «Per le tastiere vale il discorso delle risoluzioni: alla creazione della
sessione o re-attach viene rinegoziata anche la tastiera».*

Stessa forma di §5.0 — il client dichiara, la sessione si adegua — ma **con due differenze che
giocano a favore**:

1. **non costa niente di visibile.** Cambiare la misura dello schermo rimescola le finestre
   dell'utente e su KWin < 6.8 non si può proprio; cambiare la disposizione non sposta nulla,
   non riavvia la cattura, non si vede;
2. **e se fallisse, la degradazione è morbida.** Grazie a 5-bis.6 una disposizione vecchia non
   produce mai caratteri sbagliati — al massimo rende irraggiungibili un paio di accenti. Una
   misura vecchia, invece, la si vede per tutta la sessione.

`[?]` **Da misurare, due cose, e nessuna è urgente:** se il cambio di disposizione a sessione
viva riesca su tutti e quattro i desktop (la nascita è certa, il cambio a caldo no); e se
convenga dare alla sessione **più disposizioni insieme** — il sistema ne accetta fino a quattro
— per coprire il caso di chi passa da un telefono italiano a un portatile americano, che
sospetto sia raro ma non l'ha misurato nessuno.

### 5-bis.8 🔸 Mouse e tastiera fisici collegati al telefono

*Domanda posta dall'utente il 9 agosto. La risposta è che il disegno già scelto li assorbe
entrambi, e in un caso lo semplifica.*

**Il mouse.** Android offre due modi: quello normale mostra **il cursore di sistema** e
consegna posizioni — inservibile per noi, perché si vedrebbero **due puntatori**. Quello giusto
è **Pointer Capture**: il client dichiara di gestirlo lui, il cursore di Android sparisce, e
arrivano **spostamenti** più tasti e rotella.

⭐ E lì si chiude da sé: **quegli spostamenti muovono lo stesso puntatore che muove il dito.**
Una freccia sola, due modi di spingerla; si stacca il mouse e si continua col dito senza che
cambi niente. È il dividendo di 5-bis.1 — avendo il puntatore in casa, non importa da dove
arrivi la spinta.

⛔ **E da qui la correzione a 5-bis.5.** Avevo messo il «puntatore relativo» fra le cose che il
protocollo deve portare, **motivandolo con Pointer Capture**: è sbagliato. Se il puntatore lo
disegna il client, è il client a fare i conti, e sul filo continua a viaggiare solo la
**posizione**. Un percorso in meno.

`[?]` Il relativo servirà semmai per un motivo diverso — le applicazioni remote che
**catturano** il puntatore (un programma 3D, un gioco) — e quel caso lo segnala il **server**,
non il client. Da riprendere se e quando si presenta.

🔸 **L'accelerazione la applica il client**, non il server: si regola dove sta la mano ed è la
stessa per qualunque sessione. Applicata da tutt'e due si sommerebbe, e il puntatore
diventerebbe imprevedibile.

**La tastiera.** Android la gestisce e consegna comunque **il carattere**, applicando la
disposizione impostata nelle sue preferenze: la regola di 5-bis.6 vale identica, e non importa
che la tastiera sia disegnata o di plastica.

---

## 5-ter. Gli appunti

### 5-ter.1 ✅ Solo testo, nei due versi

*9 agosto 2026. «Per la clipboard ho idea precisa: solo testo». «Clipboard bi-direzionale. Dal
server al client e viceversa».*

**Solo testo**: niente immagini, niente file, niente formati ricchi.

**Nei due versi**: si copia sul desktop remoto e si incolla sul dispositivo in mano, e
viceversa. ⚠ Corregge `SPECIFICHE.md` riga 28, che diceva «clipboard testuale **server-client**»
e si leggeva in un verso solo — mentre il verso client → server (copio un indirizzo sul
telefono, lo incollo nel browser remoto) è quello che si usa di più dei due.

**Perché è la scelta giusta e non una rinuncia**, scritto perché nessuno la riapra per
distrazione: il testo copre il 95 % degli usi, costa una manciata di byte, e non ha
negoziazione — una stringa è una stringa. Le immagini aprono invece una scatola intera:
quali formati, chi converte, e soprattutto **chi paga la banda** quando si copia una schermata
da 8 MB su un collegamento mobile che stiamo faticando a tenere a 480p (§3.1).

### 5-ter.2 🔸 Il codice c'è già, e copre tre desktop su quattro con un file solo

Fra le cose che sopravvivono alla morte di RDP, gli appunti sono le più intatte: muore solo il
canale RDP che li trasportava, non il modo di parlare col desktop.

| | Righe | Copre |
|---|---|---|
| `v1/remotix-c/src/appunti_wlr.c` | 796 | **KDE, XFCE e LXQt insieme** — stesso protocollo (`zwlr_data_control_manager_v1`), e `xfce.md` §8 lo dà per funzionante così com'è |
| `v1/remotix-c/src/appunti_mutter.c` | 450 | GNOME, che ha una via sua |

### 5-ter.3 🔸 Di chi sono gli appunti cambia per desktop, e una trappola è già disinnescata

`LEZIONI.md` §3, domanda 14 — *«la clipboard di chi è?»*:

| | |
|---|---|
| **GNOME** | ⚠ **anche qui del compositore** — vedi la correzione qui sotto: è `MetaSelection`; della sessione remota è solo **la porta** (`EnableClipboard` sull'oggetto RemoteDesktop) |
| **KDE, wlroots** | del **compositore**: nessun permesso, e c'è anche se REMOTIX non c'è |

> ⛔ **Corretta il 9 agosto 2026**, leggendo `gnome.md` §10, che lo aveva già scritto l'8 e che
> nessuno aveva riportato qui. Diceva: *«della sessione remota: sta sull'oggetto RemoteDesktop, si
> accende con `EnableClipboard`, e senza sessione non esiste»*. `[R]` Le prime due mezze frasi
> descrivono la **porta**, non la proprietà; l'ultima è **falsa**: la sponda X11 di Mutter è
> incondizionata nei due versi, senza un solo controllo sul fuoco.
>
> ⭐ **E la conseguenza è un regalo per la fase 7**: `xclip` funziona su GNOME **senza** una nostra
> sessione, quindi il banco degli appunti può usarlo come lato indipendente — invece di far
> parlare fra loro due pezzi nostri, che è ciò che `PIANO.md` §0.4 chiama non confermare niente.
>
> ⚠ **Tre trappole di Mutter, tutte `[R]` in `gnome.md` §10**, che chi scrive la fase 7 legge lì e
> non qui: `DisableClipboard` è **a senso unico** (dopo, gli annunci non tornano più — non si
> chiama mai); la firma di `mime-types` è **asimmetrica** fra ingresso e uscita, e chi legge col
> tipo sbagliato ottiene `NULL` **senza errore**; e il gestore interno degli appunti tiene **un
> solo tipo MIME**.

⚠ **La trappola di GNOME, e perché non ci tocca più**: *«gnome-shell azzera la clipboard a ogni
blocco schermo: ci strappa la proprietà in silenzio»* (`gnome.md`). Con §4.3 — il blocco è
nostro e quello dei desktop resta spento — il caso non si presenta. **Ma torna il giorno in cui
qualcuno rimettesse il blocco del desktop**, ed è un'altra ragione per cui quella decisione va
riletta e non data per scontata.

---

## 6. Il codice che si eredita

### 6.1 ✅ Il patrimonio di v1 è qui, e versionato

*8 agosto 2026.* Portato dal server di sviluppo, dove viveva senza versionamento e senza una
seconda copia. Verificato per impronta SHA-256, 103 file su 103.

| | |
|---|---|
| `v1/remotix-c/` | **17.481 righe di C**, 26 moduli |
| `v1/remotix-c/prove/` | **4.563 righe di banchi**, uno script per fase |
| `v1/banchi/` | **262 file** dell'indagine sulla fase 11, `misura-cattura.c` compreso |
| `v1/remotix-rust/` | 7.163 righe, ramo IronRDP chiuso il 3 agosto |
| `v1/documenti/` | PIANO, SPECIFICA, REFERENCE, protocollo-rdp, client-android, xrdp |
| `v1/calibrazione/` | le tre scene della taratura del 1 agosto |

`LEZIONI.md` è stato promosso al livello di V2: è il fondamento di `CODER.md` e `REVIEWER.md`,
che lo citano 29 volte su 20 sezioni.

### 6.2 🔸 Circa il 79 % del C sopravvive alla morte di RDP

Misurato contando le occorrenze di `freerdp|winpr|rdpContext|RDPGFX|rdpSettings` per file:
7.442 righe **pulite** (`palco`, `cattura`, `kwin`, `mutter`, `appunti_wlr`, `superficie`,
`sentinella`, `autenticazione`…), 4.570 con contaminazione superficiale, 1.781 media, e
**3.688 che muoiono** (`server.c`, 134 occorrenze, e `rete.c` che va sostituito da QUIC).

⚠ È una misura di primo livello: contare gli `#include` dice chi *tocca* FreeRDP, non chi
*dipende* da RDP. `scambio.c` e `codificatore.c` vanno letti prima di dare il 79 % per buono.

### 6.3 ✅ Il server si scrive in C

*8 agosto 2026. «Confermo il C».*

⚠ **Non è un'eredità: è una decisione nuova che ripete la vecchia.** Il vincolo di v1
(`v1/documenti/SPECIFICA.md` §8-bis) aveva una ragione sola — *«gnome-remote-desktop smette di
essere un riferimento da cui trarre ispirazione e diventa un riferimento da cui trarre
codice»* — e **quella ragione è morta con RDP**: non c'è più niente da trapiantare, perché
nessuno ha scritto RCP prima di noi. La questione è stata riaperta a occhi aperti e richiusa
per un motivo diverso.

**Il motivo nuovo è il conto di §6.2**: circa 14.000 righe sopravvivono, con i loro banchi già
tarati. Il pezzo QUIC ne vale forse 2.000. Riscrivere quattordicimila righe misurate per
guadagnare l'ergonomia di duemila è uno scambio pessimo — ed è anche `LEZIONI.md` §10 in
azione, perché fra le cose che si butterebbero ci sono **4.563 righe di banchi**, e questo
progetto non è mai morto sul codice: è morto sulle misure.

**Che cosa questa decisione NON decide:** i client. Quello Android è Kotlin comunque, per via
di MediaCodec. Quello Linux è aperto — se sarà in C potrà condividere `librcp` col server, che
è un argomento a favore ma non una conclusione.

### 6.4 🔸 QUIC via `ngtcp2` + `nghttp3` — **chiusa il 10 agosto 2026, con un banco**

> ⭐ **La decisione, in tre righe.** Delle quattro candidate ne resta **una**: `ngtcp2`+`nghttp3`.
> `lsquic` è uscita perché **pretende l'SNI** e il prodotto si usa per indirizzo; `libwtf` era
> ultima in fila (seconda pila QUIC, licenza che si contraddice); e ⛔ **`quiche`, usata dal C, non
> riesce a dichiarare WebTransport** — la misura è qui sotto. `ngtcp2` invece regge: **due browser
> veri aprono la sessione**, e lo strato che manca costa **373 righe di codice** nostro
> (`[M]` 10 agosto 2026, ore 16:30 — la scomposizione e la successione delle misure stanno nel
> riquadro «Quante righe sono nostre, e a che ora» più sotto).
>
> ⚠ **Il prezzo, dichiarato**: quelle righe includono la **riscrittura del frame SETTINGS che
> nghttp3 sta scrivendo**, perché la sua API pubblica non permette di annunciare un'impostazione
> arbitraria. È collante che dipende dalla forma dei byte di una libreria, non da una sua promessa:
> ⛔ **va riprovato a ogni aggiornamento di nghttp3**, e il banco che lo riprova esiste.
>
> 🔸 *Derivata, correggibile senza discussione: se un giorno `quiche` esporrà
> `set_additional_settings` nell'FFI e Debian avrà `rustc` ≥ 1.88, la scelta si riapre — e i due
> banchi per rifare il confronto sono scritti.*

*Il testo qui sotto è la cronaca, e si legge in ordine: la decisione è nata come «`quiche`» su
carta, ed è finita all'opposto con tre misure.*

Era l'unico argomento serio a favore di Rust, e si risolve con una libreria invece che con un
linguaggio: **`quiche`** di Cloudflare ha un'**API C**, licenza **BSD-2**, ed è in produzione
da anni. Si prende il QUIC finito senza cucire ngtcp2 a mano e senza toccare la libertà di
licenza (§7.6).

L'alternativa in C puro è `ngtcp2` (MIT), che però richiede di portarsi il TLS e montare più
pezzi. **Da confermare quando si aprirà il trasporto**, non prima: è il tipo di scelta che si
fa con un banco davanti, non su carta.

> ⛔ **Il criterio è cambiato il 9 agosto 2026 con §1.6, e va riscritto prima di scegliere.** Non
> basta più che la libreria parli QUIC: il client è un browser, quindi il server deve portare
> **HTTP/3 e WebTransport**, più un ascoltatore **TCP** per il primo caricamento della pagina
> (`Alt-Svc`). La domanda non è più «quale QUIC», è **«quale delle due arriva fino a
> WebTransport lato server, e quanto collante resta a noi»**.
>
> `[M]` 9 agosto, sul ferro: Trixie ha `libngtcp2-dev` 1.11 **e** `libnghttp3-dev` 1.8 come
> pacchetti, `cargo`/`rustc` 1.85 per compilare `quiche`, e `python3-aioquic` 1.2 — che serve al
> cliente di prova, non al server.
>
> ⚠ **E questa scelta è diventata critica invece che secondaria**: prima decideva quante righe di
> collante scrivere, adesso decide **se il prodotto esiste**. Va chiusa con la sonda del browser
> davanti, non dopo.

> ### ⭐ Il censimento del 9 agosto notte — i candidati non erano due, e nessuno dei due originali porta WebTransport
>
> *Fatto prima di scrivere una riga di B2, come punto 0 della ricetta (`LEZIONI.md` §9): **chi, al
> mondo, fa già questa cosa?** Tutto quel che segue è `[S]` e `[R]` — **letto, non misurato**. La
> misura è B2, e serve proprio perché queste righe non bastano.*
>
> | Candidata | Lingua e API | WebTransport **lato server** | Che collante resta a noi |
> |---|---|---|---|
> | **`quiche`** | Rust con **API C** | ⛔ **no** — ma ha `h3::Config::enable_extended_connect()` (`SETTINGS_ENABLE_CONNECT_PROTOCOL`) `[R]` e i datagram QUIC completi (`dgram_send`/`dgram_recv`) `[R]` | **tutto lo strato WebTransport** |
> | **`ngtcp2` + `nghttp3`** | **C** | ⛔ **no** — ma nghttp3 implementa **RFC 9220** (l'extended CONNECT di HTTP/3) `[S]` **e** sa mandare e ricevere `SETTINGS_H3_DATAGRAM` con il **Capsule Protocol** `[S]` | lo strato WebTransport, ⭐ **con le fondamenta più complete delle quattro** |
> | ⭐ **`lsquic`** (LiteSpeed) | **C** | ⚠ **in parte** — vedi il riquadro qui sotto: il flag c'è, l'API pubblica è molto più magra del nome | **meno delle altre due, ma non «poco»** |
> | **`libwtf`** | C, ma **su MsQuic** | ⭐ sì, negozia draft-15/07/02 `[S]` | poco, ⚠ ma porta dentro **una seconda pila QUIC** |
> | ~~`web-transport-quiche`~~ | ⛔ **Rust puro, nessuna API C** | sì | ⛔ **escluso**: il server è in C (§6.3) |
>
> ⛔ **Il fatto che riordina tutto**: *«quale delle due arriva fino a WebTransport»* aveva una
> risposta sola — **nessuna delle due**. Le due candidate originali danno le **fondamenta**
> (extended CONNECT, datagram, capsule) e non lo strato di sopra: le impostazioni della sessione, il
> tipo di stream unidirezionale, il segnale sui bidirezionali, il prefisso dei datagram, la capsula
> di chiusura. La domanda vera è sempre stata la seconda — **quanto collante** — e adesso ha una
> forma elencabile.
>
> ⚠ **E i due nuovi arrivati vanno guardati con sospetto, non con sollievo:**
>
> | | |
> |---|---|
> | **`lsquic`** | ⛔ la funzione è **spenta per difetto** e **non compare nella documentazione della 4.9.3** `[R]`. «Implementato ma spento e non documentato» è la firma di un pezzo che **nessuno esercita**: va provato, non creduto |
> | **`libwtf`** | ⚠ 70 stelle, 51 commit, un autore — e ⛔ **la licenza si contraddice da sola**: il README dice MIT, il piè di pagina Apache-2.0. Su una libreria che entrerebbe nel cuore del prodotto è un difetto di per sé (§7.6) |
>
> ### ⛔ E `lsquic` è il caso da manuale di E1: il flag era necessario, non sufficiente
>
> *Letta l'intestazione pubblica `include/lsquic.h` invece di fidarsi del `CMakeLists.txt`.* Dietro
> `LSQUIC_WEBTRANSPORT_SERVER_SUPPORT` c'è **tutto quel che segue, e nient'altro** `[R]`:
>
> | | |
> |---|---|
> | due impostazioni | `es_webtransport_server`, `es_max_webtransport_server_streams` |
> | quattro funzioni, **tutte di classificazione** | `lsquic_stream_set_webtransport_session` · `..._is_webtransport_session` · `..._is_webtransport_client_bidi_stream` · `..._get_webtransport_session_stream_id` |
>
> ⛔ **Non c'è nessuna API per stabilire una sessione, per aprire uno stream WebTransport, per
> mandare un datagram WebTransport.** *«Il `CMakeLists` ha un flag che si chiama
> `WEBTRANSPORT_SERVER_SUPPORT`»* ⇒ *«lsquic fa WebTransport»* è **esattamente** la forma **E1**, la
> stessa che ha ucciso v1 e che `web.md` §9 punto 1 aveva già visto ricomparire travestita da API
> (`prefer-hardware`). ⭐ **Terza volta in tre giorni, e stavolta l'ha fermata la lettura.**
>
> ⚠ **Quel che quelle quattro funzioni implicano, però, è più di quel che dicono**: per rispondere
> *«questo stream appartiene alla sessione WebTransport numero N»* lsquic **deve** già leggere le
> intestazioni degli stream WT e associarli — che è la parte noiosa. È un indizio a favore, non una
> prova: **si misura**.
>
> ### ⭐ E la prima misura c'è — `[M]` 9 agosto 2026, `banchi/01-b2-costruisci.sh`
>
> | Che cosa | Atteso | Misurato |
> |---|---|---|
> | BoringSSL compila nel `devroot` | sì | ✅ sì |
> | `lsquic` **v4.9.3** compila con `-DLSQUIC_WEBTRANSPORT=ON` | sì | ✅ sì, e la define compare nei `FLAGS` di `build.ninja` |
> | ⛔ **il flag ha prodotto i simboli** | 4 su 4 | ⭐ **4 su 4** |
>
> ⭐ **E il codice non è un moncone**: `webtransport` compare in **sei file** — `include/lsquic.h`,
> `lsquic_stream.c/.h`, `lsquic_engine.c`, `lsquic_full_conn_ietf.c`, `lsquic_hcso_writer.c` `[R]`.
> Cioè tocca il motore, gli stream, la connessione IETF **e lo scrittore dello stream di controllo
> HTTP/3** — dove vivono le impostazioni. È un'implementazione distribuita nei punti giusti.
>
> ⛔ **Ma «i simboli ci sono» non è «la sessione si apre»**: è il gradino successivo di E1, e la
> misura che conta resta **un browser vero che apre una sessione**.
>
> ### ⛔ E leggendo oltre i simboli: `lsquic` parla la bozza **02**, i browser di oggi no
>
> *`[R]` `src/liblsquic/lsquic_hcso_writer.c`, dove il server scrive le impostazioni sullo stream di
> controllo HTTP/3.* Ecco **tutte** quelle che emette:
>
> | Impostazione | Valore | |
> |---|---|---|
> | `SETTINGS_ENABLE_WEBTRANSPORT` | `0x2b603742` | ⛔ **è della bozza 02** |
> | `WEBTRANSPORT_MAX_SESSIONS` | `0x2b603743` | ⛔ **idem** |
> | `H3_DATAGRAM_ENABLED` | `0x33` | ✅ corrente |
> | `SETTINGS_ENABLE_CONNECT_PROTOCOL` | `0x08` | ✅ corrente |
>
> ⛔ **E non emette mai `SETTINGS_WT_MAX_SESSIONS` (`0xc671706a`)**, che è l'impostazione con cui un
> server dichiara WebTransport dalla bozza 07 in poi — cioè quella che Chrome, Firefox e Safari
> cercano oggi.
>
> ⭐ **Da cui una previsione falsificabile, scritta PRIMA della misura** (`LEZIONI.md` §1.11: per
> ogni prova indiretta si scrive che aspetto avrebbe il contrario):
>
> | | |
> |---|---|
> | **la previsione** | un browser di oggi **non stabilirà** la sessione con `lsquic`: non vede la dichiarazione che cerca, e la `CONNECT` estesa viene rifiutata |
> | ⭐ **che aspetto avrebbe il contrario** | la sessione si apre lo stesso ⇒ **o** i browser accettano ancora le impostazioni della bozza 02, **o** ho letto male questo file. In tutt'e due i casi la previsione è sbagliata e va scritto perché |
> | **come si falsifica** | è la misura di B2: un browser vero contro un server minimo. **Costa quanto costa scrivere quel server** |
>
> ⚠ **Il che riporta `lsquic` in fondo alla fila invece che in testa**, e non per il difetto in sé:
> «implementato, spento per difetto, non documentato, **e fermo a una bozza di tre versioni fa**» è
> il ritratto di un pezzo che **nessuno esercita**. `CODER.md` §4.1 dice di dipendere invece di
> riscrivere — ma dipendere da codice che nessuno esercita è riscriverlo **con un ritardo**.
>
> ### ⛔⭐ `lsquic` è fuori, e per una ragione che nessuno aveva previsto — `[M]` 9 agosto 2026
>
> *Scritto il collante (`banchi/01-b2-lsquic-wt.c`, **333 righe**, di cui 236 di codice), compilato
> e messo in ascolto. Il cliente di prova si è collegato, e il server ha registrato questo:*
>
> ```
> handshake: for QUIC version 00000001, ALPN is h3
> handshake: SNI is not set, but is required in HTTP/3: fail certificate lookup
> handshake failed  ·  sending CONNECTION_CLOSE, error code: 336, reason: TLS alert 80
> ```
>
> `[R]` `lsquic_enc_sess_ietf.c:1326-1336`: in **modalità HTTP/3**, se il client non manda SNI,
> lsquic **fallisce la ricerca del certificato e chiude**. C'è una scappatoia — `esi_sni_bypass` —
> ⛔ **ma è dentro `#ifndef NDEBUG`**, cioè esiste solo nelle build di debug.
>
> ⛔ **E questo colpisce il caso primario del prodotto, non un caso limite.** `SPECIFICHE.md` e §1.7
> descrivono un server **senza dominio**, a cui l'utente arriva digitando `https://<indirizzo>:7447`
> — cioè **un indirizzo IP**. Un client che si collega a un IP **non manda SNI**: la specifica del
> TLS vieta gli indirizzi letterali in quel campo. Quindi:
>
> | | |
> |---|---|
> | ⛔ **`lsquic` non può servire un certificato a chi si collega per indirizzo** | ed è il modo in cui REMOTIX viene usato |
> | ⚠ **la previsione sulla bozza 02 resta APERTA** | non è stata né confermata né smentita: **non ci siamo mai arrivati**. Scriverla come «avevo ragione» sarebbe confermare una previsione con una prova che parla d'altro |
> | ⭐ **e il modello non è in discussione** | `aioquic`, sullo stesso indirizzo e con lo stesso certificato, serve **due browser** senza SNI. Il difetto è della libreria, non del disegno |
>
> ⭐ **Da cui un criterio nuovo per questa decisione, che nessuno aveva scritto perché nessuno lo
> immaginava**: la libreria **DEVE servire un certificato senza SNI**. Va provato per prima cosa su
> ogni candidata — costa una connessione, e qui ha eliminato una candidata dopo 333 righe.
>
> ⚠ *E il banco che ha prodotto questo `4 su 4` **aveva prima detto `0 su 4`**, per un difetto suo —
> `set -o pipefail` più `grep -q`. La cronaca sta in `fasi/01-filo-nudo.md`, «che cosa NON ha
> funzionato», ed è il motivo per cui questa riga porta la data e il nome dello script.*
>
> ⚠ **E un dettaglio che vale come odore**: il commento di `es_webtransport_server` dice *«Enable
> datagram extension for http3 server»* — cioè **documenta un'altra cosa**. Un campo la cui
> documentazione parla d'altro è un campo che nessuno ha riletto.

> ### ⭐⛔ `ngtcp2` passa il criterio nuovo, ed è il primo a essere provato prima del collante — `[M]` 10 agosto 2026
>
> *`banchi/01-b2-sni-ngtcp2.sh` (costruisce il bersaglio) · `01-b2-sonda-sni.py` (la sonda) ·
> `01-b2-lancia-sni.sh` (conduce). Il bersaglio è **il loro server d'esempio**, `bsslserver`, non un
> server nostro: un server nostro sarebbe collante, cioè la cosa che questa prova deve venire prima
> di scrivere. `ngtcp2` **16.11.0** + `nghttp3` **1.18.90**, sullo stesso BoringSSL di `lsquic`.*
>
> **La previsione, scritta prima** (`LEZIONI.md` §1.11): *passa*. `[R]` in **109 file** di
> `examples/` e **18** di `crypto/` non compare **nessuna** occorrenza di `servername`,
> `SSL_get_servername`, `SSL_CTX_set_tlsext_servername_callback`, `select_certificate_cb` — con i
> controlli positivi che rispondono (`SSL_CTX_use_certificate_chain_file` in 8 file, `alpn_select`
> in 6, `SSL_` in 10). Nessuno cerca il certificato per nome: è legato all'`SSL_CTX` e servito
> sempre. ⭐ **Che aspetto avrebbe avuto il contrario**: la stretta di mano che cade come su
> `lsquic`, e allora la candidata usciva qui invece che dopo il collante.
>
> | La misura | Atteso | Misurato |
> |---|---|---|
> | ⭐ **senza SNI sul filo** | la sessione si stabilisce | ⭐ **sì** |
> | ⛔ **e il certificato è QUELLO** | l'impronta del file | ⭐ **`35wqjGTOmKSj…` combacia** — la stretta che riesce non basta, il certificato si confronta |
> | con SNI (`remotix.prova`), il controllo | idem | ✅ sì |
>
> ⛔ **Quindi il criterio è soddisfatto, e `ngtcp2` resta in gara con `quiche`.** Il prezzo si
> conosce: lo strato WebTransport è tutto nostro (extended CONNECT in 9 file, WebTransport in 0).
>
> ⚠ **E il primo numero della colonna «quanto collante»**: il loro server d'esempio pesa **7.041
> righe** in **13 file** `.cc` `[M]` — ⛔ **è un tetto, non una stima**: è il loro HTTP/3 completo,
> con la gestione dei file, la migrazione, il retry. Il nostro sarà meno. Il numero che conta è
> quello del server minimo, e si conterà quando esisterà.
>
> ### ⭐ E la diagnosi di `lsquic` si chiude, con l'altra metà che mancava — `[M]` 10 agosto 2026
>
> Il 9 agosto si era letto *«SNI is not set»* nel suo registro e si era concluso — giustamente — che
> pretende l'SNI. ⛔ **Ma «fallisce senza» non è «riesce con»**: finché nessuno prova la seconda
> metà, la diagnosi resta a metà e la candidata è eliminata su mezza prova. Le due righe, dallo
> stesso registro e nella stessa esecuzione:
>
> | Gamba | Che cosa dice `lsquic` |
> |---|---|
> | senza SNI | `SNI is not set, but is required in HTTP/3: fail certificate lookup` |
> | con SNI | ⭐ `looked up cert for remotix.prova` — **il certificato lo trova** |
>
> ⛔ **Il difetto è l'SNI e nient'altro: l'eliminazione del 9 agosto regge, e adesso su una prova
> intera.**
>
> ⚠ **E una cosa resta aperta, dichiarata invece che arrotondata**: con l'SNI la stretta di mano
> cade lo stesso, ma **più avanti e per un'altra ragione** — avviso TLS **120**, `no suitable
> application protocol`, dopo che il certificato è stato trovato. **Non è stata indagata**: non
> serve a questa decisione, e `lsquic` è fuori per un motivo che non dipende da lei. Sta scritta
> perché nessuno la scopra da capo credendo che sia nuova.
>
> ⚠ **E la previsione sulla bozza 02 resta APERTA anche dopo questa misura**: nemmeno stavolta ci
> siamo arrivati — la connessione con l'SNI muore prima delle impostazioni HTTP/3.

> ### ⭐ `quiche` passa lo stesso criterio, e porta con sé un costo che non c'entra col QUIC — `[M]` 10 agosto 2026
>
> *`banchi/01-b2-sni-quiche.sh` (`leggi`, poi `costruisci`) · misurata dallo stesso conduttore e
> dalla stessa sonda delle altre due, nella stessa esecuzione.*
>
> **La previsione, scritta prima di costruire** (`LEZIONI.md` §1.11), su **81 file** di 3 alberi con
> il controllo positivo che risponde (*«quiche»* in 33 file): `select_certificate_cb` in **0** file,
> `servername` in **1**. ⭐ E quell'uno è un **lettore**: `quiche/src/tls/mod.rs:510-526` espone
> `server_name() -> Option<&str>` — che al C arriva come `quiche_conn_server_name()` — cioè *dice*
> che cosa ha mandato il pari, non *sceglie* niente. **Restituisce `Option`**: «nessun SNI» è uno
> stato che la firma sa rappresentare, non un errore. ⇒ **previsione: passa**.
>
> | La misura | Atteso | Misurato |
> |---|---|---|
> | ⭐ **senza SNI sul filo** | la sessione si stabilisce | ⭐ **sì** |
> | ⛔ **e il certificato è QUELLO** | l'impronta del file | ⭐ **`35wqjGTOmKSj…` combacia** |
> | con SNI (`remotix.prova`), il controllo | idem | ✅ sì |
>
> ⛔ **Quindi il criterio dell'SNI non separa più le due candidate**: `ngtcp2` e `quiche` lo passano
> tutt'e due, e la scelta si sposta su quel che resta — **quanto collante** e a che prezzo.
>
> ### ⛔ E il prezzo di `quiche` è emerso prima della misura, ed è una catena di strumenti
>
> | | |
> |---|---|
> | ⛔ **la versione più recente non si costruisce** | `quiche` **0.29.3** pretende **rustc 1.88**; Trixie ne ha **1.85** `[M]`. Non è un'opinione: cargo si ferma e non compila |
> | **la più recente che si costruisce è la 0.28.0** | il banco la sceglie da sé, confrontando il `rust-version` di ogni etichetta col compilatore presente, ⭐ **e stampa quale e perché** — la misura vale per *quella* versione |
> | ⚠ **e nemmeno la 0.28.0 basta da sola** | il loro deposito è un `workspace`: `tokio-quiche`, `h3i`, `qlog-dancer` tirano dentro `tonic`, `icu`, `time`, `image`, che pretendono fino a 1.88. Si costruisce **`-p quiche`**, cioè il solo pacchetto che useremmo |
> | ⛔ **la scelta che ne discende, e va fatta consapevolmente** | scegliendo `quiche` si sceglie **o** di restare sulla 0.28.0 finché Debian non aggiorna `rustc`, **o** di portarsi una catena Rust fuori dai pacchetti (`rustup`) dentro la costruzione del prodotto. `ngtcp2` non pone la domanda: è C, e Trixie ha tutto |
>
> ⚠ **Questo non elimina `quiche`**: è un costo, non un difetto, e va scritto **accanto alla
> scelta** invece che scoperto da chi costruirà il prodotto fra un mese.
>
> ### ⚠ I due numeri di «quanto collante», e perché NON si sottraggono
>
> | Candidata | Il loro esempio | Che cos'è |
> |---|---|---|
> | `ngtcp2`+`nghttp3` | **7.041 righe**, 13 file `.cc` | il loro **HTTP/3 completo** in C++: file, migrazione, retry, qlog |
> | `quiche` | **614 righe**, 1 file `.c` | un esempio **minimo** in C, che però fa già HTTP/3 |
>
> ⛔ **Confrontarli così sarebbe E1**: non misurano la stessa cosa. Quel che il confronto dice
> davvero è che `quiche` **espone HTTP/3 dalla sua API C** e ci si arriva in 614 righe, mentre su
> `ngtcp2` l'HTTP/3 lo monta `nghttp3` e l'esempio che lo fa è quello grosso. ⭐ **Il numero che
> conta resta quello del nostro server minimo**, e si conterà quando esisterà — su tutt'e due.
>
> ⚠ **E su tutt'e due manca ancora la stessa cosa**: lo strato **WebTransport**, che nessuna delle
> due porta (censimento del 9 agosto, ancora valido).

> ### ⭐⭐ Il server minimo su `ngtcp2` esiste, e un browser vero apre la sessione — `[M]` 10 agosto 2026
>
> *`banchi/01-b2-ngtcp2-wt-innesta.py` innesta lo strato WebTransport nel loro server d'esempio;
> `01-b2-lancia-wt.sh` lo misura col cliente di prova; `01-b2-lancia-sonda.sh` lo misura **da un
> browser**. Il numero di righe non è una stima: è `git diff` nel loro albero.*
>
> | Che cosa | Misurato |
> |---|---|
> | ⭐ **la sessione si apre da un BROWSER VERO** | **Chrome 151.0.0.0** e **Firefox 140.0**, tutt'e due `APERTA` su `https://192.168.0.2:7447/rcp/1`, impronta pubblicata, **nessun avviso**, e `"ciao"` torna identico |
> | ⛔ **e il percorso sbagliato si RIFIUTA** | `/rcp/9` ⇒ **404**, come impone `RCP.md` §2.2 con il rilievo R1.24. È il controllo che dice *no*, ed è nel banco |
> | **i due parametri di §2.2** | `max_idle_timeout` **30 000 ms** e `max_datagram_frame_size` **65 536**, ⛔ **letti dal pari** con `01-b2-sonda-trasporto.py` |
> | ⭐ **quante righe sono NOSTRE** | vedi il riquadro «Quante righe sono nostre, e a che ora» qui sotto: la misura di questa mattina era **456 aggiunte / 329 di codice**, ed è stata rifatta alle 16:30 |
>
> > ⛔ *La prima riga è stata corretta il 10 agosto 2026, rilievo **R11.6**.* Diceva **«stampati dal
> > server all'avvio»**, cioè portava la provenienza sbagliata scritta accanto al numero giusto: è
> > la **configurazione** del server — che cosa ha *chiesto* a ngtcp2 — non che cosa è *arrivato* al
> > pari. ⛔ **È il corollario di `LEZIONI.md` §1.9 punto 5** — *un denominatore si legge dove la
> > cosa succede* — contraddetto nel documento che lo cita, e `fasi/01-filo-nudo.md` la dichiara
> > **il difetto peggiore della giornata** (*«l'ho violato io, quel pomeriggio, su una misura
> > mia»*). ⭐ La cura non è togliere il numero: è **prenderlo dalla fonte giusta**, e la fonte
> > giusta esisteva già — la sonda del trasporto ha letto gli stessi due valori dal pari.
>
> ⛔ **E adesso si sa in che cosa consiste «lo strato non c'è», perché sono i tre punti che
> l'innesto tocca:**
>
> | | |
> |---|---|
> | **1. non si può annunciare WebTransport** | `nghttp3_settings` ha `enable_connect_protocol` e `h3_datagram` — le due che stanno negli RFC — e l'API pubblica offre `submit_request/info/response/trailers/shutdown_notice`. ⛔ **Nessun modo di mettere un'impostazione arbitraria** sullo stream di controllo, e `SETTINGS_WT_MAX_SESSIONS` è quel che i browser cercano. Si riscrive il `SETTINGS` di nghttp3 **mentre lo scrive** |
> | **2. gli stream WebTransport vanno sottratti a nghttp3** | cominciano col tipo di frame `0x41` seguito dal numero di sessione, e nghttp3 leggerebbe quel numero come una **lunghezza** |
> | **3. i byte di ritorno non hanno una strada** | nghttp3 non conosce quegli stream, quindi non li metterà mai fra i vettori da scrivere: la coda d'uscita è nostra |
>
> ⚠ **Nessuno dei tre è un difetto delle due librerie**: fanno HTTP/3, e WebTransport non è HTTP/3.
> È esattamente il prezzo che questa decisione voleva conoscere prima di scegliere.
>
> ⚠ **E le due bozze mordono davvero.** Il server manda **tutt'e due** le dichiarazioni —
> `0x2b603742` (bozza 02) e `0xc671706a` (bozza 07+) — perché `aioquic` 1.2, il **nostro cliente di
> prova**, implementa la **02** `[R]` `h3/connection.py:90`, e i browser cercano la 07. ⛔ Un server
> che ne mandasse una sola funzionerebbe con metà dei nostri strumenti, e la metà che funziona
> sarebbe quella sbagliata da cui trarre conclusioni.
>
> ### ⛔ Che cosa questa misura NON dice
>
> | | |
> |---|---|
> | ⚠ **non è il confronto con `quiche`** | il numero di `quiche` **non esiste ancora**: il suo esempio in C fa HTTP/3, non WebTransport. Finché non si innesta lo stesso strato anche lì, il nostro è un numero **senza il suo paragone** |
> | ⚠ **due proprietà su sei**, *alle 08:00* | delle sei che B2 doveva verificare qui, questa misura ne portava due — **datagram abilitati** e **`max_idle_timeout` 30 s**. ⭐ **Le altre quattro sono state chiuse mezz'ora dopo**, riquadro qui sotto: non restano `[?]` |
> | ⚠ **i millisecondi non si confrontano** | 118,6 ms (Chrome) e 140,0 ms (Firefox) sono **avvii a freddo dentro `xvfb`**, e lo stesso motore ha dato 22,2 ms in un altro giro. B2 misura *se la sessione si apre*, non quanto ci mette: chi metterà questi numeri accanto ai 30,2 ms del 9 agosto confronterà due cose diverse |

> ### ⭐ Le sei proprietà del trasporto: **6 su 6**, lette dal pari — `[M]` 10 agosto 2026, mattina
>
> *`banchi/01-b2-sonda-trasporto.py`, con una spia dichiarata su `pull_quic_transport_parameters` di
> `aioquic`. ⛔ **Dal pari, non dal registro del server**: è la fonte che il riquadro qui sopra
> aveva sbagliato.*
>
> | | |
> |---|---|
> | `max_idle_timeout` | **30 000 ms** |
> | datagram | abilitati, `max_datagram_frame_size` **65 536** |
> | credito stream unidirezionali | **16** |
> | migrazione | **non** disabilitata |
> | 0-RTT | **non offerto** |
> | `allowPooling` | **`false`**, e dichiarato nell'esito registrato |
> | ⛔ **e la settima, che serve a B3** | il tetto d'inattività **si può cambiare**: con `--timeout=10s` il pari legge **10 000 ms** |
>
> ⛔ **E leggerle dal pari ha trovato due difetti che nessun banco funzionale vedeva**: il server
> **offriva 0-RTT** (due biglietti, `max_early_data_size` `0xffffffff`), che §2.3 vieta perché i
> dati 0-RTT si possono ripetere e il secondo messaggio di RCP è `CREDENZIALI`; e concedeva **3**
> stream unidirezionali invece dei 16 che §2.3 impone. ⚠ *Nessuno dei due ha un sintomo: la
> sessione si apriva uguale. `fasi/01-filo-nudo.md` l'aveva previsto per il primo — «il sintomo di
> 0-RTT acceso non esiste».*
>
> ⚠ *Questo riquadro è stato aggiunto il 10 agosto 2026, rilievo **R11.5**: la misura c'era e stava
> in `README.md` e in `fasi/01-filo-nudo.md`, ma **non qui** — e §6.4 continuava a dichiararne
> quattro su sei ancora `[?]`. Tre righe dello stesso giorno e dello stesso banco che dicevano cose
> diverse, e quella che un lettore ha diritto di prendere per buona è questa (`README.md`: «le
> decisioni stanno in `DECISIONI.md`, una sola volta»). ⛔ **E non era simmetrica**: con la riga
> vecchia il divieto di 0-RTT di `RCP.md` §2.3 risultava non verificato mentre due documenti lo
> dichiaravano verificato.*

> ### ⭐ Quante righe sono nostre, e a che ora — `[M]` 10 agosto 2026
>
> ⛔ **Il numero è cresciuto tre volte in un giorno, e le tre misure non si confrontano se non si
> dice a che ora sono state prese.** Sono tutte `git diff` nell'albero di `ngtcp2`, mai stime.
>
> | Ora | Che cosa è stato misurato | Aggiunte | Codice | Commento | Vuote |
> |---|---|---|---|---|---|
> | **08:00** | lo strato WebTransport di B2, prima delle cure sul trasporto | **456** | **329** | 85 | 42 |
> | ~08:30~ | ⚠ `[?]` un numero **482 / 333** è entrato in `README.md` con il commit delle sei proprietà, e **nessun documento ne registra la scomposizione né il comando che l'ha prodotto**. Non lo si promuove e non lo si cancella: sta qui, dichiarato per quel che si sa | ~482~ | ~333~ | — | — |
> | ⭐ **16:30** | lo strato WebTransport di B2 **da solo**, dopo la lettura della capsula di chiusura | **553** | **373** | **134** | **46** |
>
> ⭐ **Come è stata presa quella delle 16:30, ed è il punto che la rende ripetibile**: su albero
> pulito, dopo `01-b3-rcp-innesta.py --togli` e `01-b2-ngtcp2-wt-innesta.py --togli`, riapplicando
> **il solo** `01-b2-ngtcp2-wt-innesta.py`. È la sequenza che `ricostruisci()` di
> `banchi/01-b11-guasto.sh` esegue già.
>
> ⛔ **E un numero che NON va in questa colonna**: con **tutt'e due** gli innesti applicati — B2 più
> i fili di B3 — l'esempio porta **972 righe aggiunte, 618 di codice** `[M]`, stessa ora. ⚠ *Non è
> confrontabile con i tre di sopra: misura due cose invece che una, ed è precisamente la ragione per
> cui `01-b3-rcp-innesta.py` è un innesto **separato** — «farlo crescere con RCP dentro renderebbe
> due misure diverse sotto la stessa etichetta» (forma **E2**).*
>
> ⚠ *Il riquadro è del 10 agosto 2026, rilievo **R11.1**. `README.md` portava 482/333 sotto il
> titolo «Che cosa è misurato `[M]`» — il posto in cui un numero senza provenienza pesa di più —
> mentre questo documento e `fasi/01-filo-nudo.md` portavano 456/329 dello stesso giorno. ⛔ E la
> giustificazione che il README dava per non rimisurare era falsa: la misura si sa prendere, e
> adesso è presa.*

> ### ⛔⭐ E `quiche` non arriva a WebTransport dal C: la dichiarazione non si può fare — `[M]` 10 agosto 2026
>
> *La regola delle 333 righe, applicata una seconda volta: **si prova per prima la cosa che può
> uccidere la candidata**. Qui è costata la lettura di due file e una connessione, invece di un
> secondo strato WebTransport scritto per intero.*
>
> **La lettura, e la previsione scritta prima** `[R]`:
>
> | | |
> |---|---|
> | ⭐ **`quiche` HA la funzione che a `nghttp3` manca** | `h3::Config::set_additional_settings(Vec<(u64,u64)>)` — `quiche/src/h3/mod.rs:644`. Un modo pulito e sostenuto di mettere un'impostazione arbitraria nel proprio SETTINGS |
> | ⛔ **ma non arriva all'API C** | **zero** occorrenze di `additional_settings` in `h3/ffi.rs` e **zero** in `include/quiche.h`. Il `quiche_h3_config` esporta **quattro** setter, e nessuno è quello |
> | ⛔ **e il trucco di `ngtcp2` lì non esiste** | su `ngtcp2` nghttp3 **consegna all'applicazione** i byte dello stream di controllo da scrivere, e li abbiamo riscritti al volo. `quiche` scrive dentro la connessione da sé: un'applicazione in C quei byte **non li vede mai** |
>
> ⇒ **previsione: `quiche`, dal C, non dichiarerà WebTransport.**
>
> **La misura** — `banchi/01-b2-sonda-impostazioni.py`, che legge `received_settings` di `aioquic`,
> cioè **quel che è arrivato sul filo**, non quel che la configurazione dice:
>
> | Server | Impostazioni dichiarate |
> |---|---|
> | ⭐ **`ngtcp2` col nostro strato** *(controllo positivo)* | **7**, fra cui `ENABLE_WEBTRANSPORT` **e** `WT_MAX_SESSIONS` |
> | ⛔ **`quiche`**, con tutto acceso | **4**: `ENABLE_CONNECT_PROTOCOL`, `H3_DATAGRAM`, `H3_DATAGRAM_00`, e una GREASE. ⛔ **Nessuna delle due dichiarazioni di WebTransport** |
>
> ⛔ **Quindi un browser non aprirebbe la sessione, e non c'è riga di codice nostro che rimedi**:
> quel frame lo scrive la libreria, e dal C non c'è modo di toccarlo.
>
> ⚠ **E la riga onesta accanto al verdetto**: *«impossibile»* sarebbe troppo. La funzione **esiste**,
> è solo non esposta — cioè **una decina di righe di FFI**, da mandare a monte o da portarsi dietro
> come patch. Sommata al `rustc` 1.88 contro 1.85, però, diventa: *per usare `quiche` bisogna
> toccare `quiche`*. Con `ngtcp2` non serve toccare niente, ed è C.
>
> ⚠ **E quel che questa misura NON dice**: **quante righe** costerebbe lo strato WebTransport su
> `quiche`. Non si sa, perché non si è arrivati a scriverlo — la candidata cade a un cancello
> precedente. ⭐ Ed è esattamente il punto della regola: il numero che non abbiamo è anche il
> lavoro che non abbiamo speso.
>
> ⭐ **Un dettaglio che vale come indizio di cura**: `quiche` manda una **GREASE**
> (`0x28d3890f99ed6413`), cioè un'impostazione inventata apposta perché i pari non si abituino a
> un elenco fisso (RFC 9114 §7.2.4.1). `ngtcp2`+`nghttp3`, col nostro strato, no.
>
> ### ⭐ E il punto di partenza di `ngtcp2`+`nghttp3`, misurato — `[M]` 9 agosto 2026
>
> *Banco `banchi/01-b2-costruisci-ngtcp2.sh`. Cercato dentro **447 file** dei due alberi, ⛔ **con il
> controllo positivo della ricerca**: la parola `nghttp3` compare in **110 file**, quindi il grep sta
> leggendo davvero.*
>
> | Che cosa | File |
> |---|---|
> | `SETTINGS_WT_MAX_SESSIONS` (`0xc671706a`) | ⛔ **0** |
> | il token `webtransport` | ⛔ **0** |
> | l'extended CONNECT (`:protocol`, `ENABLE_CONNECT_PROTOCOL`) | ✅ **9** |
>
> ⭐ **La previsione regge, e adesso è misurata**: le fondamenta ci sono, **lo strato WebTransport
> non c'è affatto**. Da cui il numero che B2 deve produrre — *quante righe di collante* — che si
> **conta**, non si stima.
>
> ⚠ *Il primo giro di questo stesso controllo aveva stampato «la previsione regge» da una ricerca
> **mai eseguita** — due alberi passati come una stringa sola, con `2>/dev/null` a nascondere
> l'errore. Il numero qui sopra vale perché il banco adesso dichiara il proprio denominatore. È la
> quarta regola di `LEZIONI.md` §1.9, nata da quell'errore.*
>
> ⛔ **Nessuna delle righe di questo riquadro è una misura del PRODOTTO.** Sono la lente che dice
> **a chi vale la pena scrivere il collante**, e quanto ne servirà.

---

## 7. ❓ Le domande aperte

**Non sono decisioni.** Sono buchi, elencati perché non si perdano.

### 7.1 ~~La misura della tela alla nascita~~ → **chiusa l'8 agosto, vedi §5.0**
La detta il client a ogni attacco. Niente predefiniti, niente preferenze.

### 7.2 ~~Blocco schermo alla disconnessione~~ → **chiusa l'8 agosto, vedi §4.3**
Il blocco è di REMOTIX, non del desktop: 30 minuti senza input e il client viene staccato. Con
una condizione di scadenza scritta, da rileggere se arriverà un'autenticazione più forte.

### 7.3 ~~Il fantasma: subentro o attesa?~~ → **chiusa l'8 agosto, vedi §4.4**
Nessuna delle due: chi tace è staccato, e il posto non lo tiene nessuno. Il bivio non esiste
più. ⚠ Resta fuori, e non è stata chiesta, la terza possibilità — **due client sullo stesso
desktop insieme**: costerebbe poco con un palco persistente, ma cambia il protocollo e andrebbe
decisa prima di scriverlo, non dopo.

### 7.3-bis ~~Dopo quanti secondi di silenzio un client è staccato?~~ → **chiusa il 9 agosto**
🔸 **30 secondi**, scritti in `SPECIFICHE.md` §5.3 — proposta mia, non pronunciata dall'utente.
La soglia decide **quando si libera il codificatore**, e non ha altri costi: essere dichiarati
staccati non fa perdere niente, perché nessuno tiene il posto (§4.4). Con QUIC il passaggio
WiFi → LTE non conta come silenzio, quindi i 30 secondi coprono solo le interruzioni vere.

### 7.4 ~~Proporzioni: bande o allungamento?~~ → **chiusa il 9 agosto**
🔸 **Si impagina, non si stira** — `SPECIFICHE.md` §6.2. Allungare deforma il testo e lo rende
illeggibile, che è l'unica cosa che un desktop non può permettersi. Il caso è raro per
costruzione: all'attacco le proporzioni combaciano sempre, e resta solo durante il
ridimensionamento e nel ripiego su KDE vecchio.

### 7.5 ~~Il linguaggio del server~~ → **chiusa l'8 agosto, vedi §6.3**
C, confermato. Non per eredità: la ragione di v1 era FreeRDP ed è morta con RDP. La ragione
nuova è il conto del riuso, banchi compresi.

### 7.6 ⏳ La licenza — **rinviata a fine progetto**, per decisione dell'utente (9 agosto 2026)
Non è più una domanda in attesa di risposta: è una decisione **programmata**, e la si prende
quando il progetto è finito. Fino ad allora vale il solo vincolo già emerso, che va rispettato
per non trovarsela decisa da sola: **niente x265** (GPL-only) come ripiego software. Con
SVT-AV1 (BSD-3) e FFmpeg compilato senza `--enable-gpl` la scelta resta interamente aperta.


### 7.7 ~~Multi-tenant: quanti utenti insieme?~~ → **chiusa il 9 agosto, vedi §4.6**
Dieci come tetto configurabile. Ma il limite vero non è un conteggio: è un budget di pixel al
secondo, e su una macchina sola lo pone il codificatore.

### 7.8 ~~La latenza~~ → **chiusa il 9 agosto, vedi §2.4-2.6**
50 ms di tetto, 40 di traguardo, e solo per il pezzo che è nostro. ⛔ *L'avvertenza che stava qui —
«il traguardo su GNOME probabilmente non si raggiunge, per lo stesso motivo dei 60 fotogrammi» — è
**caduta il 13 agosto 2026**: il ritardo è `[M]` **74,58 ms** e sfora anche il tetto, ma il motivo
non è quello. Mutter pesa il **22 %**, il **78 % è nostro**, e il muro dei 37 non si riproduce
(§2.5).*

### 7.9 ~~La fiducia: chi autentica il server verso l'utente?~~ → **chiusa il 9 agosto, vedi §1.3**
Fiducia al primo incontro, ricordata in silenzio. Nessuna impronta da confrontare: il rischio
sulla prima connessione è stato valutato e accettato per lo scenario previsto.

### 7.10 ~~Il touch da Android~~ → **chiusa l'8 agosto, vedi §5-bis**
Era la questione aperta n.1 di v1, mai chiusa in un anno. Risposta: trackpad con puntatore
disegnato dal client; tocco nativo con il posto riservato ma non implementato.

### 7.10-bis ~~La tastiera di Android: Unicode o scancode?~~ → **chiusa l'8 agosto, vedi §5-bis.6 e §5-bis.7**
Tutt'e due, ma non come pari: le **lettere** viaggiano come lettere, e solo i tasti che lettere
non sono viaggiano come posizioni. E la domanda si è allargata da Android a entrambi i client.
Quel che segue è il ragionamento che ci ha portati lì, tenuto perché la conclusione da sola non
si capisce.
Il passeggero del touch, e pesa di più. *«Una tastiera Android non è una tastiera fisica: non
ha scancode, ha un IME che produce testo»* (`v1/documenti/client-android.md` §5.2). Il client
manda quindi **Unicode** per i caratteri stampabili e **scancode** per i tasti di controllo —
Invio, Tab, frecce, modificatori.

**Proposto: tutti e due, e l'Unicode non come ripiego ma come strada principale.** In dote
arriva la chiusura della questione n.7 di v1: la disposizione di tastiera dichiarata dal
client, su Android, **non serve** — quello che arriva è già il carattere finale.

Resta da confermare, ed è la parte che costa: la conversione da carattere a **posizione fisica
nella disposizione della sessione**, con i modificatori applicati intorno.

### 7.11 ~~La clipboard: bidirezionale?~~ → **chiusa il 9 agosto, vedi §5-ter**
Sì, nei due versi, e solo testo. La domanda era nata perché `SPECIFICHE.md` diceva
«server-client», che si legge in un verso solo.

### 7.12 ~~Il «fuori scope»~~ → **chiusa il 9 agosto**
🔸 Scritto in `SPECIFICHE.md` §12, dieci voci, ciascuna esclusa **deliberatamente** e non
dimenticata: Windows, i desktop X11, la redirezione di dischi/stampanti/porte/smart card, il
trasferimento file, immagini e file negli appunti, il multi-monitor come funzione, lo stilo, il
tocco nativo, la registrazione della sessione, e la compatibilità con client RDP/VNC/SPICE.

### 7.13 📖 Cinnamon — non si decide, **si studia**

*9 agosto 2026. «Va fatto uno studio simile a quanto fatto per gli altri DE: Cinnamon è in fase
di migrazione verso Wayland ma il processo è iniziato da poco, quindi non conosco lo stato in
cui è».*

⚠ **La proposta di dichiararlo fuori scope è stata respinta**, e la ragione è giusta: dentro o
fuori non si decide su un'impressione. Gli altri quattro desktop hanno uno studio ciascuno,
questo non ce l'ha, e finché non ce l'ha ogni giudizio è `[?]`.

⭐ **Ma lo studio costa molto meno degli altri quattro, e va detto perché non venga rimandato
per paura della mole.** Muffin **non è un compositore indipendente**: è un fork di Mutter,
staccato ai tempi di GNOME 3, e ne eredita l'architettura. Quindi `cinnamon.md` non parte dal
foglio bianco — **parte da `gnome.md` e cerca le differenze**. È una lettura in negativo:
*questo pezzo di Mutter c'è ancora? è stato rinominato? è rimasto fermo a cinque anni fa?*

**Le due domande che decidono, e vanno fatte per prime:**

1. **si può creare uno schermo virtuale senza monitor?** Su GNOME è `RecordVirtual`; su KDE la
   risposta negativa è stata il risultato più costoso di tutto lo studio (`kde.md` §8.1);
2. **quanti fotogrammi consegna la cattura, con una scena dichiarata e sempre in movimento?**
   Mutter 37, KWin 60, wlroots 61 `[M]`.

Poi le altre dodici di `LEZIONI.md` §3, e la ricetta di §9 — a partire dal punto 0, *cercare chi
l'ha già fatto*, che su KDE aveva fatto trovare `KRdp` in un nono repository dopo che lo studio
lo aveva dato per inesistente.

> ## ✅ Lo studio è stato fatto il 9 agosto 2026 — sta in [`cinnamon.md`](cinnamon.md)
>
> Su `muffin` e `cinnamon` **6.7.4**, in `reference-cinnamon/`. **Tutto `[R]`, niente misurato.**
>
> **L'ipotesi del fork è confermata**: il binario `cinnamon` *è* il compositore, chiama
> `meta_init()` e `meta_run()` come gnome-shell. `ScreenCast` e `RemoteDesktop` sono le
> interfacce di Mutter rinominate, e **non c'è cancello** sul permesso di cattura.
>
> ⛔ **Ma tre cose che diamo per acquisite non esistono affatto** — verificate con lo strumento
> certificato prima su Mutter:
>
> | | Muffin 6.7.4 |
> |---|---|
> | `RecordVirtual` e `virtual_monitor` | **0 file** su tutto l'albero |
> | `ConnectToEIS` — l'input via libei | **0 file** |
> | `EnableClipboard` — gli appunti | **0 file**, e nemmeno `zwlr_data_control` |
> | un backend *headless* | solo in `src/tests/` |
>
> ⭐ **La via che resta**, ed è la ragione per non chiudere la voce: `META_DUMMY_MONITORS` +
> `MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60` forzano un monitor **fittizio** su qualunque
> backend, con la misura decisa all'avvio — l'equivalente del `--virtual --width W` di KWin, che
> il modello della tela (§5.0) già assorbe.
>
> ⚠ **Se regga davvero è `[?]`, ed è la misura M1 del §9 di `cinnamon.md`**: che il gestore dei
> monitor sia finto non dice che il renderer lo sia. Può anche riuscire **consegnando zero
> fotogrammi**, che è il modo peggiore perché sembra funzionare (`REVIEWER.md` E1).
>
> **Il giudizio provvisorio**: Cinnamon costa più di tutti e cinque, e le due difficoltà — un
> secondo percorso di input, e appunti che **oggi non hanno strada** — non sono difficoltà di
> lettura ma funzionalità mancanti a monte. **Va messo ultimo**, e la decisione si prende sulle
> misure, non su questo documento.
>
> ⏳ **E ha una data di scadenza, posta dall'utente il 9 agosto:** *«tanto Cinnamon sarà l'ultimo
> DE ad essere supportato, e le cose potrebbero cambiare»*. È la clausola giusta: le tre assenze
> che pesano — `RecordVirtual`, libei, la clipboard — sono **funzionalità che Mint può portare in
> qualunque momento**, esattamente come KDE ha portato il ridimensionamento con `kwin!7932`. Chi
> riapre questa voce **ricloni `muffin` e rifaccia le quattro ricerche** prima di fidarsi di
> `cinnamon.md`: un riferimento che invecchia in silenzio è peggio di nessun riferimento
> (`LEZIONI.md` §9.8).

---

> ## ⛔ Le tre domande della notte del 10 agosto 2026 — **si rispondono con una parola**
>
> Le tre che seguono (§7.14, §7.15, §7.16) sono nate dalla revisione `fasi/rapporti/R11-documenti.md`
> e stanno **qui** perché è qui che stanno le decisioni, una sola volta: `RCP.md`,
> `fasi/01-filo-nudo.md` e `README.md` **rimandano**, non copiano.
>
> ⛔ **Nessuna delle tre è decisa**, e la marca resta ❓ finché l'utente non parla — anche dove
> scrivo quale mi sembra più difendibile. Due di esse (§7.14, §7.15) **cambiano i byte sul filo**,
> e finché sono aperte due implementazioni conformi a `RCP.md` divergono senza che nessuna delle
> due abbia torto.
>
> ⚠ **E dall'11 agosto 2026 sono quattro**: §7.17 è nata il giorno dopo, **da una misura** — il banco
> B6 — e non da una lettura. Vale per lei tutto quel che è scritto qui sopra.
>
> ---
>
> ## ✅⭐ **TUTTE E QUATTRO SONO CHIUSE — l'11 agosto 2026**, e le ha chiuse l'utente
>
> | | la risposta | e che cosa ha portato con sé |
> |---|---|---|
> | **§7.14** | *«silenzio»* | chi riceve un `FIN` non spedisce più niente. ⛔ E `RCP.md` §8.1 guadagna l'eccezione: **chi ha ricevuto un `FIN` non è «chi chiude»** |
> | **§7.15** | *«se si può»* | il `CONGEDO` cade quando il canale è morto; il motivo resta nel codice di chiusura. ⭐ Chiude un **rosso su codice giusto** che B5 e B11 avrebbero dato |
> | **§7.16** | *«si tiene per i test, nel prodotto si fa pulizia»* | ⭐ e la risposta è stata **più larga della domanda**: è nato un principio — `SPECIFICHE.md` §2 punto 6, *sullo schermo dell'utente c'è il suo desktop e nient'altro* — con la pulizia da misurare alla fase 13 |
> | **§7.17** | *«5 secondi»* | ⛔ l'ultimo modo di **occupare un posto senza dire chi si è** |
>
> ⭐ **E tre di esse si incastrano su un caso solo**: il tetto di §7.17 scatta quando il canale di
> controllo non esiste ancora, quindi §7.15 dice che il `CONGEDO` non si manda e §7.14 dice per dove
> passa il motivo. ⚠ *Decise separatamente, nell'arco di un'ora, e nessuna delle tre sarebbe stata
> difendibile da sola.*
>
> ⛔ **Nessuna delle quattro è ancora provata sul ferro.** §7.17 chiede a **B6** un quarto caso,
> §7.14 chiede tre correzioni a `src/pagina.html` (righe 431, 479, 514, dove il prodotto fa oggi il
> contrario), §7.16 chiede un banco alla fase 13. **Decise ≠ misurate**, e finché non lo sono la
> distanza si dichiara.

### 7.14 ✅ Il `FIN` sul canale di controllo: chi lo riceve **tace**

> ## ✅ **IL SILENZIO** — deciso dall'utente l'**11 agosto 2026**
>
> *«silenzio, anche perché il server non attacca mai di sua iniziativa»*
>
> ⛔ **Chi riceve un `FIN` sul canale di controllo non spedisce più niente, nemmeno lì.** Il motivo
> viaggia per la seconda strada di `RCP.md` §3.1 punto 3 — il codice d'errore applicativo della
> chiusura — che non ha bisogno di un canale vivo.
>
> ### ⛔ La premessa era falsa, e va scritta qui perché è quella con cui la decisione è stata presa
>
> *«Il server non attacca mai di sua iniziativa»* **non regge**: attaccare di sua iniziativa è il
> comportamento **più misurato** della fase 1.
>
> | quando il server chiude da solo | quanto è provato |
> |---|---|
> | scade uno dei tetti di §4.6 | `[M]` **B6**: tutti e tre visti scattare — **5,0 · 60,1 · 10,0 s** — col congedo `TEMPO_SCADUTO` |
> | arriva una violazione | `[M]` **B5**: **36 casi su 36**, e dopo ciascuno una connessione nuova arriva a `ECCOMI` |
> | credenziali, ban, posto occupato | `RESPINTO` (§4.4) · `TROPPI_TENTATIVI` (§4.4-bis) · `GIA_ATTIVA_REMOTA` (§8.2) |
> | e il caso da cui nasce la domanda | ⛔ il **quarto difetto di B11** era *«il posto non si libera quando a chiudere il canale è il SERVER»*, `[M]` su Chrome |
>
> ⭐ **La decisione non cambia, e la ragione vera la rende più forte**: proprio perché il server
> chiude spesso, quel che fa chi riceve conta — e a scegliere è la misura, non la rarità del caso.
> ⚠ *Scritto così, e non «come ha detto l'utente», perché una ragione falsa in un registro delle
> decisioni vale più a lungo della decisione: è la forma **E5**, un fatto che era una deduzione mai
> misurata.*
>
> ⭐ **E la premessa non è finita lì: è diventata una regola.** Messa davanti alla contraddizione,
> l'utente ha scelto la forma stretta — *il server non butta fuori una sessione **sana**, e ogni sua
> chiusura ha un motivo che sa spiegare* — e non quella larga, che avrebbe portato via il ban, il
> rifiuto delle credenziali e la regola di rigore. ⇒ **`DECISIONI.md` §4.1-bis**, ✅ 11 agosto 2026.
> ⚠ *Cioè: la frase era falsa come descrizione di quel che il server fa **oggi**, ed era giusta come
> descrizione di quel che il server **deve** fare. Le due cose si somigliano abbastanza da passare
> per la stessa, e in un registro delle decisioni non lo sono.*
>
> ### La ragione che regge, ed è una misura
>
> `[M]` **10 agosto 2026**, difetto 2 di **B11**: **Chrome butta un messaggio spedito subito prima
> di chiudere la sessione.** Il `CONGEDO` della lettura B sarebbe dunque un **DEVE che un motore su
> due non può onorare** — la forma che il rilievo **R1.4** ha già dichiarato difetto. La seconda
> strada di §3.1 punto 3, invece, ⭐ **ha funzionato su tutt'e due i motori**, e su Firefox è
> **l'unica** che porti il motivo (il congedo arriva per due strade diverse, una per motore).
>
> ### Dove la decisione è andata, e il prezzo è pagato per intero
>
> | | |
> |---|---|
> | `RCP.md` §4.2 | il divieto passa da *«sugli altri canali»* a **«su nessun canale, compreso quello di controllo»** |
> | ⛔ `RCP.md` §8.1 | **l'eccezione scritta**: *chi ha ricevuto un `FIN` non è «chi chiude»*. ⚠ Senza di lei §4.2 vieta il byte e §8.1 lo impone: la decisione avrebbe **spostato** la contraddizione invece di chiuderla |
> | ⭐ `banchi/01-b11-lancia.sh` | il caso `fin-sul-controllo` aveva già l'atteso *«muta»*: ⛔ **il banco applicava questa lettura senza che nessuna riga la dicesse**, ed è la ragione per cui la domanda era stata posta |
> | ⛔ `src/pagina.html` **righe 431, 479, 514** | ⛔ **il prodotto fa oggi il CONTRARIO**: in tutt'e tre i punti, quando il server chiude il canale senza rispondere, la pagina chiama `congeda(ERRORE_PROTOCOLLO, …)` — cioè manda i nove byte. `[M]` 11 agosto 2026, letto nel sorgente. **Tre difetti da curare**, e la cura è togliere la chiamata lasciando l'`esito(...)` |
>
> ⚠ **E una cosa che la cura NON deve portarsi via**: quei tre punti chiamano `congeda()` anche per
> **scrivere l'esito all'utente**. Chi toglie la riga senza guardare toglie anche la frase che dice
> *«il server ha chiuso senza rispondere»*, e il sintomo diventa una pagina che non spiega niente —
> che è precisamente ciò che §8.2 vieta.

*Posta la notte del 10 agosto 2026, rilievo **R11.22**. Riguarda `RCP.md` §4.2 e §8.1. Le due
letture qui sotto sono lasciate come stavano: ⛔ una decisione senza l'alternativa che ha scartato
non si può rimettere in discussione quando i fatti cambiano.*

**Il fatto.** §4.2 dice: *«un `FIN` su quello stream, da una qualunque delle due parti, chiude la
sessione. Chi lo riceve **DEVE** considerarla finita; **NON DEVE** continuare a spedire **sugli
altri canali**»*. Il canale di controllo è uno stream **bidirezionale**: il `FIN` del server chiude
il verso del server, non quello della pagina. E §8.1 impone a chi chiude di mandare `CONGEDO`.
⛔ **Il divieto scritto nomina «gli altri canali» e non nomina quello di controllo**, quindi le due
letture sono tutt'e due conformi al testo di oggi.

| | **A — il silenzio** | **B — il congedo** |
|---|---|---|
| **la regola** | il `FIN` chiude la sessione **in tutt'e due i versi**: chi lo riceve non spedisce più niente, nemmeno sul controllo | il divieto è solo «sugli altri canali»: sul controllo la pagina **DEVE** ancora mandare il `CONGEDO` di §8.1, poi chiude |
| ⛔ **il byte sul filo** | **nessuno.** Il motivo viaggia solo nel codice d'errore applicativo della chiusura della sessione (§3.1 punto 3) | **nove byte** sul canale di controllo, prima della chiusura: `00 0C` (`CONGEDO`, §7.1) · `00 00 00 03` · il motivo di §8.2 · `00 00` (dettaglio vuoto). Poi la stessa chiusura di A |
| **chi la applica oggi** | ⛔ **il banco**: il caso `fin-sul-controllo` di B11 ha come atteso *«muta»*, e la pagina tace | nessuno |
| **il prezzo** | §8.1 deve guadagnare l'eccezione scritta — *chi ha ricevuto un `FIN` non è «chi chiude»* — o continua a imporre un obbligo che §4.2 vieta | il server non può contare su quel byte: ⛔ `[M]` 10 agosto, **Chrome butta un messaggio spedito subito prima di chiudere la sessione** (difetto 2 di B11). Un `DEVE` che un motore su due non onora |

**Il caso concreto, ed è già successo.** È il punto in cui il 10 agosto è nato il **quarto difetto
di B11**: su Chrome, dopo il `FIN` del server sul canale di controllo, **il posto di §8.2 `0x0F`
non si liberava** perché da lì in poi non arrivava più un byte capace di liberarlo, e l'utente
vedeva *«mi dice che sono già collegato, e non è vero»*. Con la lettura **B** quel byte esisterebbe
— è il `CONGEDO` — e arriverebbe dove il server già guarda. Con la lettura **A** il posto si libera
leggendo la capsula di chiusura, che è la cura che è stata scritta quella sera.

⭐ **Quale mi sembra più difendibile, e la ragione: A — il silenzio.** Non per il testo, che
ammette tutt'e due, ma per due misure dello stesso giorno: la seconda strada di §3.1 punto 3 —
il motivo dentro il codice di chiusura — **ha funzionato su tutt'e due i motori**, mentre il
`CONGEDO` della lettura B **è stato visto sparire su Chrome**. ⛔ Un `DEVE` che un browser su due
non può onorare è esattamente la forma che il rilievo R1.4 ha dichiarato difetto — *«era conforme
al testo quanto il primo»*. ⚠ E il prezzo di A va pagato per intero: senza l'eccezione scritta in
§8.1, A lascia in piedi la contraddizione invece di chiuderla.

**Come si chiude:** una parola — *«silenzio»* o *«congedo»*. Poi §4.2 dice se il `FIN` ricevuto
chiuda anche il verso di chi lo riceve, e §8.1 recepisce l'eccezione o la perde.

### 7.15 ✅ Il congedo di §8.1 vale **se il canale è ancora utilizzabile**

> ## ✅ **LA CONDIZIONE** — decisa dall'utente l'**11 agosto 2026**
>
> *«la soluzione più logica è "se si può". Se una connessione cade nessuno può dire al server
> "chiudo perché ho finito"»*
>
> ⛔ **L'obbligo del `CONGEDO` sul canale di controllo cade quando il canale non è utilizzabile.**
> Quel che non cade mai è il motivo dentro il **codice d'errore applicativo della chiusura**
> (`RCP.md` §3.1 punto 3), che viaggia nella chiusura stessa e parte anche a canale morto.
>
> ⭐ **E la ragione dell'utente è la ragione giusta, senza correzioni**: un `DEVE` che non si può
> rispettare non è una regola. `RCP.md` §0 lo dice di sé — *se una riga qui è ambigua, è un difetto
> di questo file* — e questa lo era: §8.1 lo imponeva senza condizioni, §3.1 punto 2 con la
> condizione, ⛔ e **un'implementazione conforme all'una era in violazione dell'altra**.
>
> ### Dove è andata, e che cosa ha chiuso
>
> | | |
> |---|---|
> | `RCP.md` §8.1 | la riga normativa porta la condizione dentro, e il riquadro dice perché |
> | ⭐ **un rosso su codice giusto** | **B5** e **B11** applicavano già il condizionale (rilievo R3.3): un banco scritto sulla forma assoluta **avrebbe bocciato un server corretto** ogni volta che la violazione arriva su uno stream unidirezionale col controllo già finito |
> | ⚠ **e non indebolisce §4.1-bis** | *ogni chiusura del server ha un motivo che sa spiegare*, decisa lo stesso giorno: il motivo arriva comunque. ⛔ Quel che si perde è **il byte sul canale morto**, cioè un byte che non partiva |
>
> ⛔ **Le due decisioni dell'11 agosto non si sostituiscono**: §7.15 dice **quando** l'obbligo cade,
> §7.14 dice **chi** non è tenuto affatto. Dopo un `FIN` ricevuto il canale, nel verso di chi lo ha
> ricevuto, **è ancora utilizzabile** — quindi senza §7.14 la condizione di §7.15 non lo salverebbe.

*Posta la notte del 10 agosto 2026, rilievo **R11.23**. Riguarda `RCP.md` §8.1 e §3.1 punto 2. Le
due letture qui sotto restano come stavano.*

**Il fatto.** §8.1: *«Chi chiude **DEVE** mandare `CONGEDO` con un motivo prima di chiudere la
sessione»*, e l'unica eccezione dichiarata è `RESPINTO`. §3.1 punto 2, per la stessa cosa:
*«**DEVE** mandare `CONGEDO` (§8) con il motivo, sul canale di controllo, **se il canale di
controllo è ancora utilizzabile**»*. ⛔ Un'implementazione che chiude **senza** congedo perché il
canale è rotto è **conforme a §3.1 e in violazione di §8.1**, nello stesso documento.

| | **A — l'obbligo è incondizionato** | **B — vale la condizione di §3.1** |
|---|---|---|
| **la regola** | chi chiude manda `CONGEDO` **sempre**, tranne dopo `RESPINTO` | l'obbligo cade quando il canale di controllo non è utilizzabile; il motivo passa comunque dal punto 3 |
| ⛔ **il byte sul filo** | i nove byte del `CONGEDO` **anche** quando il controllo è già chiuso o rotto — cioè un byte che spesso non può partire | **nessun byte** in quel caso: resta il solo codice d'errore applicativo della chiusura (§3.1 punto 3) |
| **chi la applica oggi** | nessuno | ⛔ **il banco**: B5 e B11 verificano le chiusure *«nei tre punti di §3.1 col secondo condizionale»* (`fasi/01-filo-nudo.md`, rilievo R3.3) |
| **il prezzo** | un banco scritto su §8.1 **boccia un server corretto** ogni volta che la violazione arriva su uno stream unidirezionale | §8.1 perde la forma assoluta, e va riscritta con la condizione dentro — una frase |

**Il caso concreto.** Una violazione arriva su uno **stream unidirezionale** dopo che il canale di
controllo è già finito: con **A** il server deve mandare un `CONGEDO` su un canale che non c'è più,
e il banco che pretende tutt'e tre i punti di §3.1 **dà rosso sul codice giusto** — è il rilievo
R3.3, già pagato una volta su questo stesso banco.

⭐ **Quale mi sembra più difendibile, e la ragione: B — la condizione.** Un `DEVE` che non si può
rispettare non è una regola, è un difetto del documento (`RCP.md` §0: *«se una riga qui è ambigua,
è un difetto di questo file»*), e la seconda strada non fallisce mai: il motivo viaggia nel codice
di chiusura anche quando il canale è morto. ⛔ **E costa una frase in §8.1, zero byte sul filo.**

⚠ **Le due domande si toccano e non si sostituiscono.** Rispondere *«vale la condizione»* a §7.15
**non** chiude §7.14: dopo un `FIN` ricevuto il canale di controllo, **nel verso di chi lo ha
ricevuto**, è ancora utilizzabile — ed è esattamente il punto che §7.14 chiede.

### 7.16 ✅ La funzione di banco resta 🔸 — e ⭐ **fuori dal prodotto consegnato**

> ## ✅ **DUE CASI DISTINTI** — deciso dall'utente l'**11 agosto 2026**
>
> *«Nessun quadratino: l'utente deve vedere il desktop senza artefatti, come se fosse davanti al
> monitor del PC» → e poi, messo davanti al prezzo: «distinguiamo i 2 casi: si tiene quello che
> serve per i test, ma poi nel prodotto finale si fa pulizia».*
>
> ⛔ **Il principio, ed è più grande della domanda che era stata posta**: sullo schermo dell'utente
> non compare **mai** niente che non sia il suo desktop. Non «spento per predefinito», non «dietro
> un interruttore»: **assente**. Chi si collega deve vedere quel che vedrebbe stando davanti al
> monitor del PC, e nient'altro.
>
> ⭐ **E la funzione di banco sopravvive, dall'altra parte del confine**: serve a **tarare il
> cronometro** del ritardo alla fase 3 — si inietta un ritardo noto e si verifica che la mediana
> salga di esattamente quello. ⛔ *«Un banco che non lo fa non sa di misurare»*
> (`web/rapporti/S4-ritardo-disegno.md` §4.2, controllo P1): toglierla del tutto avrebbe lasciato
> il numero più importante del progetto — il tetto dei 50 ms — **senza un modo di sapere se è
> vero**.
>
> ### Che cosa vuol dire, in concreto
>
> | | |
> |---|---|
> | **la marca resta 🔸** | non era una decisione dell'utente, e ⛔ **si può togliere senza tornare da lui**. Quel che l'utente ha deciso è il **confine**, non il messaggio |
> | ⛔ **il prodotto consegnato non la contiene** | non compilata, non raggiungibile, **non presente nel binario**. ⚠ *«Spenta»* non basta più: era la forma di prima, e questa decisione la sostituisce |
> | **il banco sì** | la costruzione di prova la contiene, e i due tipi `0x000F`/`0x0010` restano in `RCP.md` §7.5 come **funzione di banco dichiarata**, non come funzione del prodotto |
> | ⛔ **e la differenza si misura** | *«non c'è»* e *«c'è ed è spenta»* hanno lo stesso aspetto da fuori: si distinguono **cercando le marche dentro il binario consegnato**, come fa già `banchi/01-p1-prodotto.sh` con le sue otto marche. Senza quella prova, questa decisione è una buona intenzione |
>
> ### ⛔ Dove morde, e non è oggi
>
> **Fase 13 — il confezionamento.** È lì che nasce il binario che si installa, ed è lì che questa
> decisione si rispetta o si perde. ⚠ *Scritta anche in `PIANO.md` fase 13 e in `RCP.md` §7.5,
> perché una regola che vale fra undici fasi e sta scritta in un posto solo è una regola che nessuno
> troverà il giorno che serve.*
>
> ⚠ **E una cosa che questa decisione NON dice**: che la funzione di banco fosse un problema. Nasce
> **spenta**, e `banchi/01-b5-violazioni.py` verifica che a funzione spenta il server **rifiuti**
> dichiarando `FUNZIONE_SPENTA`. Il difetto non c'era: l'utente ha alzato l'asticella da *«non si
> vede»* a *«non c'è»*.

*Posta la notte del 10 agosto 2026, rilievo **R11.15**. La riga sta in §1.5 riga 26, ed è 🔸 — non
✅. La domanda com'era posta resta qui sotto.*

**Il fatto.** `RCP.md` §7.5 aggiunge al protocollo **due tipi di messaggio** — `BANCO_MARCA`
(`0x000F`) e `BANCO_ESITO` (`0x0010`) — e §7.5 dichiara di venire dal **rilievo R3.4** della
revisione del banco, con la motivazione da `web/rapporti/S4-ritardo-disegno.md` §5.3. ⛔ **Non c'è
né una frase né una voce**, mentre le decisioni che l'utente ha pronunciato davvero (§1.6, §1.8,
§1.9) portano qui la frase virgolettata con la data. `fasi/01-filo-nudo.md` la marcava ✅, cioè
*«deciso dall'utente»*: corretta a 🔸 il 10 agosto.

| | **A — era tua (✅)** | **B — è derivata (🔸)** |
|---|---|---|
| **che cosa cambia** | non si tocca senza tornare da te | *«si corregge senza discussione»* |
| ⛔ **il byte** | nessuno **oggi**: i due tipi ci sono in tutt'e due i casi. Cambia **la reversibilità** — con A i `0x000F`/`0x0010` restano in RCP/1 per sempre, con B si possono togliere | |
| **il peso** | quei due tipi hanno **consumato la clausola di §9** — *«oggi non esiste nessuna implementazione»* — che `RCP.md` §12 dichiara essere stata **l'ultima occasione** per aggiungere tipi di messaggio | |

**Il caso concreto.** Il giorno in cui quei due tipi diano fastidio — un'implementazione che deve
riconoscerli per essere conforme, in un ambiente dove *dipingere un quadratino sul desktop di
qualcuno* non è accettabile nemmeno dietro un interruttore — con **B** si tolgono, con **A** no. ⚠ E
c'è la metà che conta anche se la risposta è *«fate voi»*: **il tuo protocollo porta due tipi che
tu non hai chiesto**, e questa riga esiste perché tu lo sappia.

⭐ **Quale mi sembra più difendibile, e la ragione: B — 🔸.** La provenienza è dichiarata da §7.5
stessa e non è una tua frase; marcarla ✅ le darebbe una protezione che nessuna misura le ha dato
(`LEZIONI.md` §2.3-quater). ⛔ Ma è l'unica delle tre che **solo tu** puoi chiudere davvero, perché
la domanda è *se l'hai detta*.

**Come si chiude:** *«sì, era mia»* ⇒ diventa ✅ e §1.5 riga 26 riceve la frase con la data.
*«no»* ⇒ resta 🔸 dov'è, e non se ne parla più.

### 7.17 ✅ La sessione che non apre mai il canale di controllo: **5 secondi**

> ## ✅ **CINQUE SECONDI** — deciso dall'utente l'**11 agosto 2026**
>
> ⛔ **Dall'apertura della sessione WebTransport all'apertura del canale di controllo passano al
> massimo 5 s**, poi il server chiude con `TEMPO_SCADUTO` `0x0D`. ⇒ `RCP.md` §4.6, la riga che
> mancava.
>
> ⭐ **Perché 5 s, cioè lo stesso numero del primo tetto**: aprire il canale è il **primo atto
> obbligatorio** della sessione (`RCP.md` §2.5), non dipende da quanto è veloce a digitare una
> persona, e non dipende dalla rete più di quanto ne dipenda il `CIAO`.
>
> ⛔ **Che cosa chiude**: era **l'ultimo modo, in questa fase, di occupare un posto senza dire chi
> si è**. ⚠ E il tempo di inattività di QUIC non lo copriva — quello conta il **silenzio**, e una
> sessione che scrive su un altro stream non è silenziosa: teneva il posto **a tempo
> indeterminato**.
>
> ### ⭐ E qui le quattro decisioni dell'11 agosto si incastrano
>
> | | |
> |---|---|
> | **§7.15** | il canale di controllo non esiste ancora, quindi il `CONGEDO` **non si manda**: senza la condizione decisa un'ora prima, questa riga imporrebbe un byte su un canale mai nato |
> | **§7.14** | e il motivo viaggia dove viaggia sempre quando il canale non c'è: nel **codice d'errore applicativo della chiusura** (§3.1 punto 3) |
> | **§4.1-bis** | ⛔ è una chiusura decisa dal server, e **ha il suo motivo dicibile**: `TEMPO_SCADUTO`. Non è una sessione sana che viene buttata fuori — è una sessione che non è mai cominciata |
>
> ⚠ **Non serve nessun tipo di messaggio nuovo**, e conta: la finestra di §9 è chiusa dal 10 agosto
> 2026. `TEMPO_SCADUTO` c'era già.
>
> ⛔ **E resta da misurare**: `B6` guadagna un quarto caso — apri la sessione, non aprire il canale,
> e verifica che a 5 s arrivi `0x0D` **nel codice di chiusura**, non sul canale. Il banco oggi non
> ce l'ha: fino ad allora questa riga è **scritta e non provata**.

*Posta l'11 agosto 2026 da una **misura**, non da una lettura: il banco **B6** (rilievo **R12-A.25**,
e `fasi/01-filo-nudo.md` B6). Riguarda `RCP.md` §4.6. La domanda com'era posta resta qui sotto.*

**Il fatto, e sono due.** B6 ha chiuso la `[?]` **R3.27** — *da quale istante parte il primo tetto* —
e la risposta è: **dall'apertura del canale di controllo**, non dalla fine del TLS. `RCP.md` §4.6
riga 1 è stata corretta di quella parola l'11 agosto. ⛔ **Ma il banco ha dato una seconda risposta,
e dice che curare la parola non basta**: se il cronometro parte dall'apertura del **canale**, chi apre
la **sessione** WebTransport e il canale non lo apre mai **non ha addosso nessun tetto**. §4.6 non ha
una riga per quello stato: la tabella comincia da *«`CIAO` ricevuto»*, e prima del `CIAO` c'è uno
stato in cui il server non conta niente.

| | **A — un quarto tetto** | **B — nessun tetto, e si dichiara** |
|---|---|---|
| **che cosa dice** | dall'apertura della **sessione** all'apertura del **canale di controllo** passa al massimo *N* secondi, poi `CONGEDO(TEMPO_SCADUTO)` | quello stato lo copre il solo tempo di inattività di QUIC (30 s di **silenzio**), e §4.6 lo scrive invece di lasciarlo implicito |
| ⛔ **che cosa cambia sul filo** | arriva un `CONGEDO(0x0D)` — sul canale che non c'è, quindi **solo** il codice `0x0D` nella chiusura della sessione (§3.1 punto 3) — dove oggi non arriva niente | niente arriva, ed è **quel che succede oggi**: la differenza è che smette di essere un'omissione |
| **il costo** | un tetto in più da misurare, e un client lento a chiamare l'API si vede chiudere la sessione appena aperta | ⛔ una sessione che non manda `CIAO` ma **tiene il filo occupato** su un altro stream non scade **mai**: il posto resta preso |

**Il caso concreto, e non è di laboratorio.** Una pagina apre la sessione WebTransport, poi il
browser va in secondo piano o la rete cade fra i due passi. Con **A** la sessione muore con un motivo
leggibile; con **B** resta lì finché QUIC non si annoia — e se qualcosa continua a scrivere su un
altro stream, non si annoia mai. ⚠ È la connessione che *«tiene un posto e non lo dichiara a
nessuno»*, cioè la frase con cui §4.6 si apre: la sezione esiste per questo caso e non lo copre.

⭐ **Quale mi sembra più difendibile, e la ragione: A, con lo stesso numero della riga 1 — 5 s.**
Non per simmetria: perché l'apertura del canale di controllo è **il primo atto obbligatorio** della
sessione (§2.5), non dipende dall'utente, e non dipende dalla rete più di quanto ne dipenda il `CIAO`.
⛔ Ma è una riga normativa che aggiunge un tetto a un'implementazione conforme, quindi **resta ❓**
finché non la decidi: `RCP.md` §4.6 porta la riga marcata ❓ e rimanda qui, e §12 la dichiara fra le
cose che RCP/1 lascia aperte. ⭐ **Non serve nessun tipo di messaggio nuovo** — il motivo è
`TEMPO_SCADUTO`, che c'è già — e questo conta, perché la finestra di §9 è chiusa dal 10 agosto.

**Come si chiude:** un numero, o *«nessun tetto»*. Con la prima, §4.6 guadagna una riga e B6 un caso;
con la seconda, §4.6 guadagna comunque **la riga che dichiara lo stato**, perché un buco dichiarato e
un buco dimenticato non si distinguono dopo tre mesi.

---

## Come si tiene questo documento

Una voce ❓ che riceve risposta **si sposta** nella sezione che le compete e cambia marca; non
si risponde in fondo. Una voce 🔸 che l'utente conferma diventa ✅. Una voce ✅ si riapre solo
con una misura che la smentisce — e allora si riscrive **nello stesso momento**, con la data e
la fonte (`CODER.md` §5).
