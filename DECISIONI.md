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
parallelo alle fasi 10-11, che sono lavoro di server e non toccano il filo.

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

### 1.4 🔸 La sessione non conosce il codec: lo negozia la connessione

Discende da 1.1 e da §4. Il palco produce fotogrammi; ogni connessione ci attacca il proprio
codificatore con le capacità del **suo** client. Se il codec fosse una proprietà della
sessione, riprendere da un dispositivo diverso — telefono la mattina, portatile il pomeriggio
— richiederebbe di rifare la sessione, che è esattamente ciò che la persistenza deve evitare.

### 1.5 🔸 Le chiusure di RCP/1 — venticinque buchi tappati prima della prima riga di codice

*9 agosto 2026, all'apertura della fase 1. Sono conseguenze scritte da me leggendo `RCP.md` con una
domanda sola — **due persone che lo leggono da sole scrivono lo stesso byte?** — e la risposta era
no. Tutte 🔸: si correggono senza discussione.*

⛔ **Il censimento in una riga**: dei ventidue messaggi del protocollo, **due** erano definiti byte
per byte — il fotogramma e il datagram audio. Gli altri venti avevano un nome e una descrizione a
parole. Il canale meno specificato era proprio quello della **stretta di mano**, cioè quello che la
fase 1 deve scrivere. Il dettaglio sta in `RCP.md` §0-bis; qui stanno solo le scelte che avrebbero
potuto essere prese altrimenti.

| # | La scelta | Perché così | Dove |
|---|---|---|---|
| 1 | **la porta è UDP 7447** | libera in `/etc/services` di Trixie `[M]`. `[?]` IANA non verificata | `RCP.md` §2.4 |
| 2 | le **stringhe** sono `u16` di lunghezza più UTF-8, senza terminatore | il terminatore invita a passare la stringa a `printf` senza copiarla, e un byte nullo in mezzo diventa un troncamento silenzioso | §6.0 |
| 3 | **il byte alto del `tipo` dice il canale** di uno stream | chi riceve uno stream unidirezionale deve sapere che cosa c'è dentro **prima** di leggerlo, e non era scritto da nessuna parte | §2.5 |
| 4 | **niente 0-RTT** | i dati 0-RTT si ripetono, e il secondo messaggio è `CREDENZIALI`. Il guadagno è un giro di rete su una sessione che dura ore | §2.3 |
| 5 | `disable_active_migration` **non si manda** | dichiararla spegne in silenzio la ragione per cui QUIC è stato scelto | §2.3 |
| 6 | **credito degli stream ≥ 256, e va rinnovato** | il video consuma uno stream per fotogramma: chi imposta il numero e non rinnova il credito funziona **quattro secondi** | §2.3 |
| 7 | l'impronta si calcola sulla **chiave pubblica**, non sul certificato | un certificato riemesso con la stessa chiave non deve far scattare l'avviso | §4.1-bis |
| 8 | il client **spegne** i controlli X.509 di serie | altrimenti rifiuta il nostro autofirmato e la causa sta nella libreria, non nel nostro codice | §4.1-bis |
| 9 | **`RESPINTO` è il congedo dell'autenticazione**, e non ne segue un altro | §4.4 e §8.2 si sovrapponevano: due implementazioni potevano indovinare diverso, o **uguale perché scritte dalla stessa mano** | §4.4 |
| 10 | **un solo tentativo di credenziali per connessione** | il limitatore conta una cosa sola, e non serve una macchina a stati per i tentativi ripetuti | §4.4 |
| 11 | ⭐ **la limitazione: 5 in 5 minuti, poi attesa da 30 s che raddoppia fino a 15 min** — più **un secondo fisso di ritardo su ogni risposta, anche quando è «ammesso»** | chiude la `[?]` di `SPECIFICHE.md` §4.2. Il ritardo fisso toglie il **tempismo** come canale: senza, la distinzione fra «utente inesistente» e «password sbagliata» che §4.4 vieta di scrivere la si legge col cronometro | §4.4-bis |
| 12 | **la tela DEVE avere lati pari**, fra 320×240 e 7680×4320 | una misura dispari la arrotonda **il codificatore, in silenzio**: due misure sotto la stessa etichetta, cioè la forma d'errore **E2** | §4.5 |
| 13 | **tre tetti di tempo sulla stretta di mano** (5 s, 60 s, 10 s) | una connessione ferma a metà tiene un posto; e i 30 s di QUIC misurano il **silenzio della rete**, non un client che non fa il suo mestiere | §4.6 |
| 14 | ⛔ **i fotogrammi chiave**: `tipo` `0x0301`/`0x0302` e il messaggio `RICHIEDI_CHIAVE` | **non era una lacuna, era un difetto di disegno**: §5.1 concede di abbandonare un fotogramma, e il video è compresso con predizione — abbandonarne uno lascia il decodificatore rotto finché non arriva una chiave, e non c'era modo né di dirlo né di chiederla. Costa **zero byte**: entra nei valori di un campo che c'era già | §5.2 |
| 15 | l'audio è **48 kHz, 2 canali, blocchi da 20 ms**, e il PCM è **s16 little-endian** | «Opus, con PCM come base» non è un formato. E l'endianness del carico utile è l'unica eccezione all'ordine di rete: dichiararla è ciò che impedisce a due implementazioni di divergere in silenzio | §5.3 |
| 16 | gli appunti si fermano a **1 000 000 byte**, e oltre **non si annunciano** | troncare un testo e incollarlo in un terminale è peggio che non averlo | §5.4 |
| 17 | il cursore si ferma a **256×256**, e `larghezza = 0` vuol dire nascosto | serviva un modo di dire «nessun cursore» che non fosse un messaggio in meno | §5.5, §7.2 |
| 18 | **un fotogramma non supera 16 MiB**, e la lunghezza si controlla **prima di allocare** | senza tetto, sei byte scritti a mano si portano via la memoria del server | §6.1, §6.2 |
| 19 | i fotogrammi **possono arrivare fuori ordine**, e il client scarta i vecchi con aritmetica **modulo 2³²** | gli stream sono indipendenti: è una conseguenza di §5.1 che nessuno aveva scritto. A 60 al secondo il contatore gira in due anni, e una sessione può durare di più | §6.2 |
| 20 | **i codici di tasti e pulsanti sono quelli di evdev**, la rotella in **unità da 120** | è quel che vuole `libei`, cioè l'unico modo che abbiamo di iniettare input. Ogni altra convenzione aggiunge una tabella di traduzione che sbaglia in silenzio — e in v1 quella tabella è costata il banco della rotella (`LEZIONI.md` §2.3) | §7.3 |
| 21 | l'`id` dell'input è **uno solo per tutto il canale**, non uno per tipo | è quello che torna nel campo `input` del fotogramma: con contatori separati non tornerebbe niente | §7.3 |
| 22 | ⛔ **al distacco si rilasciano tutti i tasti e i pulsanti** | un Ctrl rimasto giù in una sessione che sopravvive al client rende il desktop inservibile al riattacco, e nessuno collega le due cose | §7.3 |
| 23 | **`TELA` è la risposta obbligatoria ad `ADATTA_TELA`** | §7.1 imponeva un «rifiuto motivato» e non esisteva un messaggio per dirlo: il client sarebbe rimasto ad aspettare per sempre | §7.1 |
| 24 | dopo un cambio di tela, **un secondo di grazia** sulle coordinate vecchie | è l'unico momento in cui i due lati hanno legittimamente due verità diverse. Dichiarata come eccezione a §3, non lasciata all'improvvisazione | §7.1 |
| 25 | il motivo del congedo viaggia **anche nel codice d'errore della chiusura QUIC** | se il congedo non arriva — stream rotto, messaggio illeggibile — il motivo passa comunque. È la ferita di `LEZIONI.md` §1.7 curata con due strade invece che con una | §3.1 |

⚠ **E due tipi di messaggio sono stati aggiunti** (`RICHIEDI_CHIAVE`, `TELA`) più due motivi di
congedo (`TEMPO_SCADUTO`, `SESSIONE_NON_SERVIBILE`). §9 lo vieta **dentro** una versione maggiore,
e la clausola che lo permette è che **oggi non esiste nessuna implementazione**. Dal primo byte
scritto in poi vale la regola senza sconti.

⏳ Quel che RCP/1 lascia **volutamente** aperto — microfono, puntatore relativo, tocco, 4:4:4, più
schermi — sta in `RCP.md` §12, dichiarato invece che dimenticato.

---

## 2. I numeri

### 2.1 ✅ Minimo: 480p · 25 fps · 24 bit — ed è una garanzia, non un traguardo

*8 agosto 2026.*

Diceva «30 fps a 1080p», ed era il numero di v1 — che lo superava già `[M]`: la cattura di
Mutter consegnava 37 fotogrammi, KWin 60.

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

### 2.5 🔸 ⛔ Il traguardo dei 40 ms non è raggiungibile su GNOME — stesso muro dei 60 fps

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
> ed è la fase 12.

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

### 5.0-bis 🔸 Il riattacco a misura diversa su KDE < 6.8: degradazione dichiarata

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

### 5.1 ✅ Se l'utente ridimensiona la finestra, l'immagine si riscala

*8 agosto 2026. «Tagliamo la testa al toro. Anziché correre dietro ai compositor, una scelta
che vale per tutti».*

**Ridimensionare la finestra del client non tocca mai il desktop.** Si adatta la vista; le
finestre dell'utente non si muovono. Uguale su GNOME, KDE, XFCE e LXQt.

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

### 6.4 🔸 QUIC via `quiche`

Era l'unico argomento serio a favore di Rust, e si risolve con una libreria invece che con un
linguaggio: **`quiche`** di Cloudflare ha un'**API C**, licenza **BSD-2**, ed è in produzione
da anni. Si prende il QUIC finito senza cucire ngtcp2 a mano e senza toccare la libertà di
licenza (§7.6).

L'alternativa in C puro è `ngtcp2` (MIT), che però richiede di portarsi il TLS e montare più
pezzi. **Da confermare quando si aprirà il trasporto**, non prima: è il tipo di scelta che si
fa con un banco davanti, non su carta.

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
50 ms di tetto, 40 di traguardo, e solo per il pezzo che è nostro. Con l'avvertenza che il
traguardo su GNOME probabilmente non si raggiunge, per lo stesso motivo dei 60 fotogrammi.

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

## Come si tiene questo documento

Una voce ❓ che riceve risposta **si sposta** nella sezione che le compete e cambia marca; non
si risponde in fondo. Una voce 🔸 che l'utente conferma diventa ✅. Una voce ✅ si riapre solo
con una misura che la smentisce — e allora si riscrive **nello stesso momento**, con la data e
la fonte (`CODER.md` §5).
