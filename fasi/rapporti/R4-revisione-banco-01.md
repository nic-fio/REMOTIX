# R4 — Revisione avversariale del banco della fase 1

*9 agosto 2026. Rivisto `fasi/01-filo-nudo.md` nella sua forma di apertura — dodici banchi, nessuna
riga di prodotto — con **una lente sola: la coerenza con quel che è già scritto**.*

Non si giudica qui se il banco sappia misurare (è di un'altra revisione). Si guarda **la copertura
normativa** di `RCP.md`, le contraddizioni con `RCP.md` · `SPECIFICHE.md` · `DECISIONI.md` ·
`PIANO.md` · `LEZIONI.md`, le citazioni una per una, le marche, le convenzioni di `PIANO.md` §0.2-0.3
e il confine della fase contro l'invariante **I2**.

---

# ⛔ 1. Il censimento della copertura normativa

*Ogni **DEVE** / **NON DEVE** / **PUÒ** di `RCP.md` che la fase 1 tocca, contro il banco che lo
prova. «⛔ scoperto» vuol dire: **nessuno lo verificherà**. «⚠ di riflesso» vuol dire: se fosse
violato **qualcos'altro** diventerebbe rosso, ma non c'è una prova che lo guardi.*

| § | L'obbligo | Il banco |
|---|---|---|
| **2.2** | `max_idle_timeout` **30 s**, imposto dal server | ⚠ di riflesso (B3 riga 5, B6) |
| **2.2** | i **datagram DEVONO** essere abilitati sulla connessione HTTP/3 | ⛔ **scoperto** — S6 misura il browser, non il prodotto |
| **2.2** | ALPN `h3` | non applicabile: lo negozia il browser |
| **2.2** | l'indirizzo è `/rcp/1`; un percorso diverso **NON DEVE** essere accettato → **404** | B5 ✓ |
| **2.2** | percorso e `CIAO` **DEVONO** coincidere → `VERSIONE_INCOMPATIBILE` | B5 ✓ |
| **2.2** | ⛔ **NON DEVE** esistere un battito applicativo | ⛔ **scoperto** |
| **2.3** | il server **DEVE** concedere al client almeno **16** stream unidirezionali in ogni momento | ⛔ **scoperto**, e nessuna fase lo dichiara (B12 manda alla fase 3 il credito **nell'altro verso**) |
| **2.3** | il server **DEVE** reggere il rifiuto di aprire uno stream | fase 3 (B12) ✓ |
| **2.3** | il server **NON DEVE** offrire **0-RTT** | ⛔ **scoperto** |
| **2.3** | il server **NON DEVE** disabilitare la **migrazione** | ⛔ **scoperto** |
| **2.4** | due ascoltatori sulla **7447**: UDP per WebTransport, TCP per la pagina | ⚠ di riflesso (B2 come criterio, e il giudizio dell'utente) |
| **2.5** | il controllo è il **primo** stream bidirezionale, uno per sessione | ⚠ di riflesso |
| **2.5** | il client **NON DEVE** aprire bidirezionali oltre il primo | B5 ✓ |
| **2.5** | ⛔ **il server NON DEVE aprire stream bidirezionali** | ⛔ **scoperto** — nessuno guarda dal lato della pagina |
| **2.5** | un byte alto fuori dai cinque canali è `ERRORE_PROTOCOLLO` | B4 ✓ · B5 ✓ |
| **2.5** | un canale nel **verso sbagliato** (`0x03` dal client) | B5 ✓ |
| **2.5** | `0x00` (controllo) su uno stream **unidirezionale** è `ERRORE_PROTOCOLLO` | ⛔ **scoperto** |
| **2.5** | `0x04` (audio) su uno **stream** è `ERRORE_PROTOCOLLO` | ⛔ **scoperto** |
| **2.5** | l'input: **uno solo**, aperto dopo `SESSIONE` | fase 4 |
| **3** | chi non capisce **DEVE** chiudere e scrivere *che cosa* non ha capito | B5 ✓ |
| **3** | eccezione 1: una **capacità sconosciuta si ignora** — non si chiude | ⛔ **scoperto** |
| **3** | ⛔ **ogni tolleranza va scritta nel registro** | ⚠ di riflesso: B5 solo per la voce di elenco scartata |
| **3** | la regola vale per **un'implementazione RCP**, cioè **anche per la pagina** che riceve | ⛔ **scoperto** → R4.1 |
| **3.1** | i **tre** punti della chiusura (registro · `CONGEDO` · codice della sessione) | B5 ✓ · B7 ✓ |
| **3.1** | il codice **0 NON DEVE** essere usato | ⛔ **scoperto** |
| **4.1** | la chiave **DEVE** essere **ECDSA P-256**, mai RSA | ⚠ di riflesso (senza, l'impronta non passa) |
| **4.1** | chiave privata con permessi **`0600`** | ⛔ **scoperto** |
| **4.1** | `subjectAltName` = l'indirizzo su cui il server risponde | ⛔ **scoperto** |
| **4.1** | se c'è un certificato d'autorità, il server **DEVE** usarlo e **non DEVE** rigenerare il proprio | ⛔ **scoperto**, e **nessuna fase lo dichiara** |
| **4.1-bis** | **due** certificati distinti: longevo per la pagina, ≤14 giorni per la sessione | B3 ✓ |
| **4.1-bis** | `allowPooling` a **`false`** | ⛔ **scoperto** |
| **4.1-bis** | la pagina ritira l'impronta corrente **fuori da RCP** | B3 ✓ |
| **4.1-bis** | il banco **DEVE** provare il **secondo** collegamento e un terzo con la chiave cambiata | B3 ✓ |
| **4.2** | un **FIN** sul canale di controllo **è** la fine della sessione; chi lo riceve **DEVE** considerarla finita | ⛔ **scoperto** |
| **4.3** | la forma dei **nomi**: `a-z`, `0-9`, `.`, da 1 a 64 byte | ⛔ **scoperto** |
| **4.3** | il **valore**: UTF-8 stampabile, ≤ 256 byte | ⛔ **scoperto** |
| **4.3** | ⛔ un **nome ripetuto** è `ERRORE_PROTOCOLLO` | B4 ✓ · C1 ✓ |
| **4.3** | ⛔ un **valore vuoto** è `ERRORE_PROTOCOLLO` | ⛔ **scoperto** |
| **4.3** | una voce sconosciuta **dentro** un elenco si scarta (e si registra) | B5 ✓ |
| **4.3** | elenco vuoto dopo lo scarto → `NIENTE_IN_COMUNE` | B5 ✓ |
| **4.3** | una capacità dal **lato sbagliato** → `ERRORE_PROTOCOLLO` | B5 ✓ |
| **4.3** | ⛔ `pcm` e `8` **DEVONO** essere dichiarati **da entrambi**; chi non lo fa → `NIENTE_IN_COMUNE` | ⛔ **scoperto** → R4.8 |
| **4.3** | intersezione vuota anche su `video.profondita` e `audio.codec` | ⛔ **scoperto** (provato solo `video.codec`) |
| **4.3** | ⛔ la scelta del server **DEVE** essere scritta nel registro | ⛔ **scoperto** |
| **4.3** | `video.livello`: il server **DEVE** emettere un flusso non superiore | ⛔ **scoperto**, e nessuna fase lo dichiara |
| **4.3 · 4.5** | ⛔ `video.misura_massima` è un **tetto** che la tela concessa **DEVE** rispettare | ⛔ **scoperto**, e **contraddetto dal confine** → R4.2 |
| **4.4** | utente **vuoto** = `ERRORE_PROTOCOLLO`, e i contatori non si muovono | B5 ✓ |
| **4.4** | **parola vuota** = `ERRORE_PROTOCOLLO` | ⛔ **scoperto** |
| **4.4** | gli intervalli 1-256 (utente) e 1-1024 (parola) | ⛔ **scoperto** |
| **4.4** | ⛔ **NON DEVE** distinguere nel motivo fra utente inesistente e parola sbagliata | ⚠ di riflesso: B8 cronometra, nessuno confronta i **codici** |
| **4.4** | dopo `RESPINTO`: chiusura con lo stesso motivo, e ⛔ **NON DEVE** seguire un `CONGEDO` | ⛔ **scoperto** |
| **4.4** | il client **NON DEVE** riprovare sulla stessa connessione | ⛔ **scoperto** |
| **4.4** | ⛔ la parola d'ordine **in nessun registro a nessun livello** | ⛔ **scoperto** — B4 lo enuncia, nessuno lo verifica |
| **4.4-bis** | **due** contatori — nome **e** indirizzo — e si applica il più severo | ⛔ **scoperto** per l'indirizzo (B8 prova solo il nome) |
| **4.4-bis** | soglia: 5 falliti in 5 minuti | B8 ✓ |
| **4.4-bis** | finestra da 30 s che **raddoppia** fino a 15 minuti | ⚠ di riflesso: B8 la enuncia, non la scompone |
| **4.4-bis** | `RESPINTO(TROPPI_TENTATIVI)` **senza interrogare PAM** | B8 ✓ |
| **4.4-bis** | un accesso riuscito **azzera** | B8 ✓ (controllo positivo) |
| **4.4-bis** | il contatore per indirizzo scade dopo **30 minuti** di quiete | ⛔ **scoperto** |
| **4.4-bis** | ⛔ il **ritardo fisso** ≥ 1 s, **anche su `AMMESSO`** | B8 ✓ · C1 ✓ |
| **4.5** | limiti **320×240 … 7680×4320**, entrambi **pari** | B5 ✓ |
| **4.5** | `disposizione`: malformata → `ERRORE_PROTOCOLLO`; sconosciuta → `SESSIONE_NON_SERVIBILE` | B5 ✓ |
| **4.5 · 7.1** | ⛔ **la vista NON ha i vincoli della tela**: da 1×1 in su, **dispari compresa** | ⛔ **scoperto** → R4.10 |
| **4.5** | la tela **concessa** rispetta comunque limiti e parità | ⚠ di riflesso |
| **4.5** | il client **NON DEVE** cambiare comportamento in base a `desktop` | ⛔ **scoperto** |
| **4.5** | se l'attacco non si serve: congedo — **mai un silenzio, mai una sessione a metà** | B5 ✓ |
| **4.6** | i tre tetti **5 s · 60 s · 10 s** → `TEMPO_SCADUTO` | B6 ✓ |
| **4.6** | ⛔ i **PING del trasporto** finché si aspettano le credenziali | B6 ✓ · C1 ✓ |
| **6.0** | stringa = `u16` + UTF-8 **valido** | B4 ✓ |
| **6.0** | ⛔ **nessun allineamento, nessun riempimento** | B4 ✓ |
| **6.1** | `lunghezza` **DEVE** essere esatta | B4 ✓ · B5 ✓ |
| **6.1** | ⛔ nessun messaggio oltre **1 MiB** | ⛔ **scoperto** |
| **6.1** | ⛔ **la lunghezza si controlla prima di allocare** | ⛔ **scoperto** |
| **7.1** | i tipi della stretta di mano e `CONGEDO` | tutti i banchi ✓ |
| **7.1 · 8.2** | il campo `dettaglio` **NON DEVE** essere mostrato all'utente | B7 ✓ |
| **8.2** | `SESSIONE_NON_SERVIBILE` **DEVE** portare il dettaglio **nel corpo** | ⛔ **scoperto** |
| **8.1** | `CONGEDO` prima di chiudere, e il motivo **ripetuto** nel codice della chiusura | B7 ✓ |
| **8.2** | ogni motivo mostrabile in **una frase**, costruita dal client | B7 ✓ |
| **8.2** | `GIA_ATTIVA_LOCALE` (`0x05`) | ⛔ **scoperto**, e **di nessuna fase** → R4.16 |
| **9** | il server sceglie la più alta che non superi il `CIAO` | ⚠ di riflesso (provato solo `CIAO(2)`) |
| **9** | ⛔ **il client DEVE verificare la versione di `ECCOMI` e congedare** se non la sa parlare | ⛔ **scoperto** → R4.1 |
| **11** | dodici banchi: sei presi, sei collocati | B12 ✓ (ma vedi R4.7) |

> ⛔ **Il conto: 38 obblighi scoperti, 9 coperti solo di riflesso.**
>
> ⚠ **E fra i trentotto ce n'è un gruppo che ha una forma sola, contata**: gli **undici** che
> riguardano quel che il server manda alla pagina e quel che la pagina deve farne — §2.5 (il server
> non apre bidirezionali; `0x00` su unidirezionale; `0x04` su stream), §3 (la regola vale anche per
> chi riceve), §3.1 (il codice 0), §4.2 (il FIN), §4.4 (dopo `RESPINTO` nessun `CONGEDO`; il client
> non riprova sulla stessa connessione), §4.5 (il client non cambia comportamento su `desktop`),
> §8.2 (il dettaglio nel corpo), §9 (il client verifica `ECCOMI`). **Per nessuno degli undici esiste
> una prova**, e non è un caso: il banco punta in **un verso solo** → R4.1.

---

# 2. I rilievi, per gravità

| # | Che cosa | Marca |
|---|---|---|
| **R4.1** | ⛔ il rigore è provato **in un verso solo**: nessuna violazione arriva mai alla pagina | `[R]` |
| **R4.2** | ⛔ «la tela concessa è quella chiesta» contraddice il **DEVE** di §4.5 su `video.misura_massima` | `[R]` |
| **R4.3** | ⛔ l'ordine dichiarato **B1 prima di B2** è impossibile: S1a, S4 e S6 pretendono il server che B2 deve scegliere | `[R]` |
| **R4.4** | ⛔ S1a cita `RCP.md` §4.1-bis a sostegno di ciò che §4.1-bis **nega** | `[R]` |
| **R4.5** | ⛔ B3 pretende la vita della sessione e l'orologio del silenzio, che il documento stesso rimanda alla **fase 5** | `[R]` |
| **R4.6** | C1 dice «**un guasto per banco**» e ne elenca quattro su dieci: B3, B7, B9 restano senza controllo positivo | `[R]` |
| **R4.7** | «il rilascio dei tasti al distacco → **fase 4**»: quel banco richiede il **riattacco**, che è fase 5 | `[R]` |
| **R4.8** | che cosa il server della fase 1 dichiara in `ECCOMI` non è scritto, e §4.3 lo rende **normativo** | `[R]` |
| **R4.9** | «oggi non è scritto da nessuna parte» sulla scheda congelata: **è scritto**, in `SPECIFICHE.md` §5.3 | `[R]` |
| **R4.10** | la **vista** non ha banco, ed è l'unico campo di `ATTACCA` a cui i limiti **non** si applicano | `[R]` |
| **R4.11** | l'**isolamento fra origini** (`SPECIFICHE.md` §11.5) è un vincolo di prodotto della fase 1, e non compare | `[R]` |
| **R4.12** | decisioni **copiate** invece che richiamate — contro `README.md` «Le convenzioni» e `PIANO.md` §0.3 regola 1 | `[R]` |
| **R4.13** | S2: l'atteso «`[S]` sì da Chrome 108» è la marca del **supporto**, messa come atteso dell'**hardware** | `[R]` |
| **R4.14** | S1b: `[?]` in `web.md` §8, `[R]` qui, e la promozione non è dichiarata | `[?]` |
| **R4.15** | «questa tabella è costata il banco della rotella» non è quel che dice `LEZIONI.md` §2.3 | `[?]` |
| **R4.16** | `GIA_ATTIVA_LOCALE` (`0x05`) non è dichiarato da nessuna fase | `[?]` |

---

## R4.1 ⛔ Il rigore è provato in un verso solo

**DOVE** — `fasi/01-filo-nudo.md`, **B5** («Le prove di violazione»), tutte e dodici le righe della
tabella; e per contrasto B4, che legge una registrazione senza iniettare niente.

**COSA CONTRADDICE** — `RCP.md` §3, che è scritta su **«un'implementazione RCP»** e non «il
server»; `RCP.md` §9, che ha un **DEVE esplicito del client**: *«Il client DEVE verificare che la
versione di `ECCOMI` sia una che sa parlare, e congedare con `VERSIONE_INCOMPATIBILE` se non lo è —
un server che risponde con una versione più alta di quella chiesta sta sbagliando, e accettarla in
silenzio è l'indulgenza che §3 vieta»*; `RCP.md` §2.5 (*«il server NON DEVE aprire stream
bidirezionali»* — chi lo rileva è il client); `REVIEWER.md` §5 *«non supplisci»*; `LEZIONI.md` §2.1,
che di questa fase è la lezione fondativa.

**COME SI DIMOSTRA** — un caso solo: il server della fase 1, per un errore di scrittura, risponde
`ECCOMI(versione = 2)` a un `CIAO(versione = 1)`. Dodici prove di B5 restano verdi (nessuna manda
niente alla pagina), B4 resta verde (le sue sei registrazioni guaste sono costruite a mano, e questa
non c'è), B9 non lo vede perché il cliente di prova apre **la sua** connessione. La pagina —
l'unica implementazione che l'utente userà — accetta la versione più alta in silenzio, e il difetto
esce alla fase 9 come «il telefono vecchio non si collega». ⛔ È **esattamente il client indulgente
che nasconde l'omissione**, con l'aggravante che stavolta l'indulgente è nostro. Lo stesso vale per
un `SESSIONE` con la tela dispari, per un `CONGEDO` con motivo `0x00` (vietato da §3.1) e per un
secondo stream bidirezionale aperto dal server.

**MARCA** — `[R]`

---

## R4.2 ⛔ «La tela concessa è quella chiesta» contraddice §4.5

**DOVE** — `fasi/01-filo-nudo.md`, il riquadro del confine: *«`stato` vale sempre `NUOVA`, **la tela
concessa è quella chiesta**, `desktop` è quello che il sistema dichiara installato»*.

**COSA CONTRADDICE** — `RCP.md` §4.5: *«La tela concessa **DEVE** rispettare `video.misura_massima`
se il client l'ha dichiarata»*, e §4.3: *«`video.misura_massima` **non** cambia la tela: è un tetto
che il server **DEVE** rispettare quando concede la tela (§4.5). Esiste perché il decodificatore di
un telefono ha limiti che il suo schermo non dichiara»*. La riga del confine non ammette eccezioni:
*sempre* quella chiesta.

**COME SI DIMOSTRA** — un telefono con schermo 4K e decodificatore limitato a 1080p: la pagina
manda `CIAO` con `video.misura_massima = 1920x1080` (è quel che §4.3 le fa dichiarare) e `ATTACCA`
con tela `3840×2160` (è quel che `DECISIONI.md` §5.0-quater le fa chiedere: **lo schermo in pixel
fisici**). Il server della fase 1 concede `3840×2160` e viola un **DEVE**. In fase 1 non si vede —
non c'è video — e nessun banco lo guarda (§4.5 sta nel censimento come scoperto). Alla fase 2 il
sintomo è *«il browser non apre il flusso»*, che `RCP.md` §4.3 dichiara essere il sintomo di un
**livello** dichiarato male: si cercherà nel codificatore un difetto nato nella stretta di mano.
⚠ E il difetto è **strutturale, non un caso limite**: quel tetto e quella tela vengono da due
misure diverse dello stesso dispositivo, e su un telefono divergono sempre.

**MARCA** — `[R]`

---

## R4.3 ⛔ L'ordine dichiarato B1 → B2 è impossibile per tre misure su nove

**DOVE** — `fasi/01-filo-nudo.md`, «Il banco»: *«I banchi sono **dodici**, in tre gruppi, e
**l'ordine non è decorativo**»*, con B1 primo («nessuna riga di prodotto») e B2 secondo («senza di
esso il resto non ha su che cosa girare»).

**COSA CONTRADDICE** — sé stesso, e `PIANO.md` §1.2 (*«va fatta **prima** di scegliere la libreria
QUIC»*). Le due affermazioni non stanno insieme se le misure di B1 hanno bisogno di un server
WebTransport, e tre di esse ce l'hanno scritto dentro.

**COME SI DIMOSTRA** — riga per riga, dal documento stesso:

| Misura | Che cosa pretende |
|---|---|
| **S1a** | il controllo positivo è *«la connessione con l'impronta pubblicata **deve riuscire**»* — cioè una sessione WebTransport servita da un server che pubblica `serverCertificateHashes` |
| **S4** | *«**il server** ritarda di N ms noti e la mediana deve salire di esattamente N»* — c'è un server, e spedisce fotogrammi da decodificare |
| **S6** | *«si spedisce un datagram di quella misura esatta e **si verifica che arrivi**»* — c'è un capo dall'altra parte |

Il server minimo che li regge **è quello di B2** («cinquanta righe, che si buttano»), e B2 è il
banco che deve ancora **scegliere la libreria che lo permette**. Chi esegue il documento nell'ordine
scritto si ferma alla prima riga della prima misura. ⚠ E la conseguenza non è di calendario: se
S1a viene eseguita con il server minimo di una candidata e la candidata poi cambia, il controllo
positivo è stato fatto su un motore diverso da quello del prodotto — che è la forma **E10**.

**MARCA** — `[R]`

---

## R4.4 ⛔ S1a cita §4.1-bis a sostegno di quel che §4.1-bis nega

**DOVE** — `fasi/01-filo-nudo.md`, B1, riga **S1a**, colonna «Che cosa decide»: *«una **comodità**,
non una piattaforma: con `serverCertificateHashes` in Safari 26.4 l'impronta si usa comunque
(`RCP.md` §4.1-bis)»*.

**COSA CONTRADDICE** — `RCP.md` §4.1-bis, riga **«chi resta fuori»**: *«`[S]` WebKit **non lo
implementa**: su **Safari, iPhone e iPad** la strada è l'eccezione — `[?]` **se funziona**, ed è la
prima misura di S1 — oppure il certificato vero»*. Il paragrafo citato dice **il contrario** di quel
che gli si fa dire. Il fatto vero sta in `web.md` §3.1 (WebKit l'ha implementato il 2 ottobre 2025,
`NetworkTransportSessionCocoa.mm` `[R]`, spedito in Safari 26.4) e in `DECISIONI.md` §1.7, corretta
lo stesso giorno — **`RCP.md` non è stata aggiornata**, ed è l'arbitro.

**COME SI DIMOSTRA** — due persone leggono i due documenti da sole, che è la prova che `RCP.md`
§0-bis si impone. Chi legge il documento di fase scrive un server che pubblica l'impronta e la dà a
tutti e tre i motori; chi legge l'arbitro scrive il ramo «su Safari l'impronta non serve, si va di
eccezione o di certificato vero» — e lo scrive **conforme alla lettera**. ⛔ La stessa riga
sostiene anche il criterio di B2 (*«una libreria che va con Chrome e non con Safari non è una
libreria che va»*): se valesse §4.1-bis, Safari non aprirebbe **mai** la sessione con l'impronta e
B2 boccerebbe **entrambe** le candidate. ⚠ La cura non è di questo documento: è di `RCP.md`
§4.1-bis. Ma il documento di fase **promuove a fatto** una correzione che l'arbitro non ha ancora
recepito, e lo fa **citando l'arbitro** — che è il modo peggiore, perché chi controlla la citazione
trova un rimando e non lo legge.

**MARCA** — `[R]`

---

## R4.5 ⛔ B3 pretende quel che il confine rimanda alla fase 5

**DOVE** — `fasi/01-filo-nudo.md`, **B3**, righe 3 e 5: *«2ª connessione, **mentre la prima è
viva**: `CONGEDO(GIA_ATTIVA_REMOTA = 0x0F)`»* e *«**la 2ª dopo 30 secondi di silenzio della 1ª**:
⭐ entra — il discrimine è **l'orologio del silenzio**»*.

**COSA CONTRADDICE** — il riquadro del confine **dello stesso documento**: *«La sessione grafica
vera nasce alla **fase 2**, **la sua vita e i suoi tre orologi alla fase 5**»*; e `PIANO.md` fase 5,
che dichiara di **produrre** *«il palco che sopravvive al distacco, **i tre orologi, una sola
sessione grafica per utente**»* con banco *«i tre orologi, ciascuno con la sua prova»*.
L'«orologio del silenzio» è il primo dei tre (`SPECIFICHE.md` §5.3, `DECISIONI.md` §4.5).

**COME SI DIMOSTRA** — per rispondere `GIA_ATTIVA_REMOTA` alla seconda connessione il server deve
sapere che **esiste una sessione, di quell'utente, con un client vivo attaccato**: cioè deve tenere
lo stato di sessione fra due connessioni, distinguere attaccato da staccato, e far scattare i 30
secondi. Ma lo stesso documento dichiara che alla fase 1 la sessione *«non ha ancora un compositore
dietro»* e che `stato` **vale sempre `NUOVA`** — anche alla seconda connessione dello stesso utente,
dove `SPECIFICHE.md` §5.2 vuole una ripresa. ⛔ Il risultato è che **la fase 1 produce metà del
meccanismo di I2 senza dichiararlo fra quel che produce**, e la fase 5 lo dichiara come proprio:
o la riga del confine è falsa, o B3 non è eseguibile qui. ⚠ E il pezzo mancante è quello che
`DECISIONI.md` §4.4 chiama *«il discrimine»*: senza i tre orologi, la riga 5 di B3 misura il tempo
di inattività di QUIC (30 s, §2.2) e lo chiama orologio del silenzio — due grandezze uguali per
accidente, che alla fase 5 diventeranno configurabili e si scolleranno.

**MARCA** — `[R]`

---

## R4.6 «Un guasto per banco», e sono quattro su dieci

**DOVE** — `fasi/01-filo-nudo.md`, **B11**, prova **C1**: *«si guasta il server di proposito, **un
guasto per banco**: si toglie il PING (B6), si toglie il ritardo fisso (B8), si accetta un nome di
capacità ripetuto (B5), si rimette `autenticazione_utente_atteso()` (B10)»* — e la tabella delle
misure: *«C1 — **i quattro guasti** costruiti a mano | 4 rossi su 4»*.

**COSA CONTRADDICE** — sé stesso nella stessa riga; `PIANO.md` §0.3 regola 4 (*«**ogni fase**,
prima di dichiarare un numero, dimostra che il suo banco sa vedere il difetto che cerca»*);
`REVIEWER.md` §1 punti 2 e 5; `LEZIONI.md` §1.2 e §1.9.

**COME SI DIMOSTRA** — i banchi del filo sono B3, B4, B5, B6, B7, B8, B9, B10 (B4 ha il suo
controllo positivo per conto suo, le sei registrazioni guaste). I guasti coprono B5, B6, B8, B10.
Restano scoperti **B3, B7 e B9**, e il caso di B7 è quello che pesa: è il banco costruito sul
difetto che in v1 è durato **tre fasi** — il server scriveva «congedo il client», il client scriveva
«errore di rete» (`LEZIONI.md` §1.7). Il guasto da costruire è di una riga: **si toglie l'invio del
`CONGEDO` e si lascia il registro**. Se B7 resta verde, sta leggendo il registro di chi manda —
cioè fa **esattamente** quel che la sua prima riga vieta — e nessuno se ne accorgerebbe, perché il
banco è nato per non farlo. ⚠ Stesso ragionamento per B3: il guasto è *«il server muore alla
seconda connessione»*, che è il difetto di v1 da cui B3 nasce.

**MARCA** — `[R]`

---

## R4.7 Il rilascio dei tasti al distacco è mandato in una fase in cui non si può eseguire

**DOVE** — `fasi/01-filo-nudo.md`, **B12**: *«il rilascio dei tasti al distacco → **fase 4** — nasce
col canale di input»*.

**COSA CONTRADDICE** — `RCP.md` §11, che di quel banco scrive la procedura: *«si stacca una
connessione **con un tasto premuto** e **si riattacca** a verificare che non sia rimasto giù»*; e
`PIANO.md` fase 5, che dichiara di produrre *«il palco che sopravvive al distacco»* e il cui banco è
*«distacco e riaggancio, due volte di fila»*. Alla fase 4 **non esiste una sessione a cui
riattaccarsi**: `PIANO.md` fase 4 non ha né la sopravvivenza al distacco né il riattacco fra i suoi
banchi (cursore, lettera accentata, `Ctrl+C`).

**COME SI DIMOSTRA** — si prova a scrivere quel banco alla fase 4: si preme Ctrl, si chiude la
pagina, e la sessione **muore con la connessione** (è il difetto che `PIANO.md` fase 5 dichiara di
curare). Non c'è niente su cui verificare che il tasto sia rimasto giù, e il banco o non si scrive
o si scrive verde per costruzione. ⛔ `RCP.md` §11 lo chiama *«la regola con il rapporto
danno/costo più alto del documento»*: il documento di fase lo colloca, PIANO non lo raccoglie, e il
banco cade **fra la fase 4 e la fase 5** — che è precisamente il caso che B12 esiste per impedire.

**MARCA** — `[R]`

---

## R4.8 Che cosa il server dichiara in `ECCOMI` non è scritto, e §4.3 lo rende normativo

**DOVE** — `fasi/01-filo-nudo.md`, il riquadro del confine, che dichiara tre cose di `SESSIONE`
(`stato`, tela, `desktop`) e **niente** di `ECCOMI`; e la tabella delle misure, riga *«B9 — il
cliente di prova completa la stretta di mano»*.

**COSA CONTRADDICE** — `RCP.md` §4.3: *«`pcm` **DEVE** essere dichiarato **da entrambi**… Allo
stesso modo `8` **DEVE** comparire in `video.profondita` di entrambi»*, e *«chi **non dichiara**
`pcm` o `8` … si congeda con `NIENTE_IN_COMUNE`»*; *«Se l'intersezione di `video.codec` è vuota, il
server **DEVE** congedare con `NIENTE_IN_COMUNE`»*. La fase 1 dichiara *«niente video, niente
audio»*: quali capacità metta in `ECCOMI` un server che non ha né codificatore né audio è una
domanda **normativa**, e il documento non la pone.

**COME SI DIMOSTRA** — B9 è scritto *«leggendo `RCP.md` e mai il codice»*: chi lo scrive implementa
§4.3 alla lettera e, ricevendo un `ECCOMI` senza `audio.codec` e senza `video.profondita`, **congeda
con `NIENTE_IN_COMUNE`**. Il banco «B9 completa la stretta di mano» diventa rosso, il rosso è
**corretto**, e chi ha scritto il cliente di prova penserà di aver sbagliato lui — che è, parola per
parola, la forma che `RCP.md` §11 dichiara di aver già pagato con il rilievo R1.18 e che B7 cita
come trappola da evitare. ⚠ E l'esito opposto è peggio: il server dichiara `hevc` e `10` che non
sa produrre, e la fase 2 eredita una negoziazione che mente.

**MARCA** — `[R]`

---

## R4.9 «Oggi non è scritto da nessuna parte» — è scritto, e nel punto che il documento cita

**DOVE** — `fasi/01-filo-nudo.md`, «Le decisioni prodotte», ultima riga: *«⏳ **`SPECIFICHE.md`
§5.3 — la scheda congelata** | ⛔ **da dichiarare**: … Non è un difetto (`DECISIONI.md` §4.1), ma
**oggi non è scritto da nessuna parte** (`web.md` §1.2 D)»*.

**COSA CONTRADDICE** — `SPECIFICHE.md` §5.3, righe 259-265, che lo dichiara già, con la data e la
fonte: *«⛔ **E una cosa che il client web aggiunge, dichiarata invece che scoperta** (9 agosto
2026, `web.md` §1.2 D): una **scheda in secondo piano viene congelata dal browser dopo circa cinque
minuti** `[S]`. Una scheda congelata tace, quindi **si stacca**, e la sessione resta viva ad
aspettare»*. La frase «non è scritto da nessuna parte» è **di `web.md` §1.2 D**, che è invecchiata
nel giro della stessa giornata: il documento di fase l'ha copiata invece di verificarla.

**COME SI DIMOSTRA** — `grep -n "congelata" SPECIFICHE.md` restituisce la riga 260. ⛔ È la forma
del rilievo **R1.25** di `RCP.md` — *«tenerla aperta faceva pianificare una misura già fatta»* —
applicata a una decisione: la fase 1 si iscrive un lavoro che `SPECIFICHE.md` ha già chiuso, e la
prossima persona che legge le due righe insieme non saprà quale delle due è la verità corrente.

**MARCA** — `[R]`

---

## R4.10 La vista non ha banco, ed è l'unico campo di `ATTACCA` a cui i limiti non si applicano

**DOVE** — `fasi/01-filo-nudo.md`, **B5**, riga *«una tela `1921×1080`, o `319×240` |
`ERRORE_PROTOCOLLO` (§4.5)»* — e nessuna riga sulla **vista**, in nessuno dei dodici banchi.

**COSA CONTRADDICE** — `RCP.md` §7.1: *«⛔ **La vista non ha i vincoli della tela**, e va detto
perché la riga precedente diceva il contrario: qualunque misura da **1×1 in su** è legale, **dispari
compresa**»*, con il riquadro del rilievo **R1.17** che ne dà il caso concreto e la ragione
(*«farsi chiudere la sessione perché ha ridimensionato una finestra»*).

**COME SI DIMOSTRA** — `ATTACCA` porta **quattro** `u32` in fila (§4.5). Chi lo scrive in C scrive
una `valida_misura()` e la chiama quattro volte: è la cosa naturale da fare, e produce un server che
rifiuta `vista 300×800` con `ERRORE_PROTOCOLLO`. Nessuna delle dodici righe di B5 manda una vista
piccola o dispari, e nessuna riga di nessun banco ne manda una **valida** per vedere che passi:
il difetto attraversa la fase 1 verde. Emerge alla fase 6, come *«l'utente stringe la finestra e la
sessione cade»* — cioè il sintomo che `SPECIFICHE.md` §8.3 vieta («mai staccare») e che R1.17 è
stato scritto per prevenire. ⚠ Su un telefono con fattore di scala 2,75 la vista è **dispari quasi
sempre**: 393 pixel logici valgono 1080,75 fisici (`RCP.md` §7.1).

**MARCA** — `[R]`

---

## R4.11 L'isolamento fra origini è un vincolo di prodotto della fase 1, e non compare

**DOVE** — `fasi/01-filo-nudo.md`: «Che cosa deve produrre» (*«la pagina servita dal server
stesso»*), B2 (*«più un ascoltatore **TCP** per la pagina»*), e la misura **S4**. In nessuno dei tre
compare l'isolamento fra origini.

**COSA CONTRADDICE** — `SPECIFICHE.md` §11.5: *«⛔ **E come la pagina viene servita è un vincolo di
prodotto, non un dettaglio** (`web.md` §8-bis, O11): va consegnata **isolata fra origini** — le due
intestazioni che il browser pretende per dare alla pagina i cronometri a piena risoluzione e la
memoria condivisa. ⚠ Non è una taratura del banco: **cambia come il server serve ogni risorsa della
pagina**, e deciderlo dopo significa riscrivere il modo in cui la pagina è confezionata»*. La fase 1
è **la** fase in cui il server acquista il mestiere di servire la pagina (`PIANO.md` fase 1): non
c'è nessun'altra fase che dichiari questo vincolo.

**COME SI DIMOSTRA** — due conseguenze, una nel prodotto e una nel banco di questo stesso documento.
Nel prodotto: la pagina della fase 1 viene servita senza le due intestazioni, e alla fase 2 il
worker di `web.md` §6.1 chiede la memoria condivisa e non la ottiene — si riconfeziona il modo in
cui ogni risorsa viene servita, che è la riscrittura che §11.5 dice di voler evitare. Nel banco:
**S4 è in questo documento**, e `web.md` §6.3 dichiara che *«senza le due intestazioni di isolamento
fra origini, su Firefox e Safari i cronometri hanno grana **1 ms** — su un tetto di 50»*. La riga di
S4 nel documento riporta il controllo positivo e il pezzo cieco, e **tace sul righello**: la misura
che decide metà del tetto viene presa con uno strumento la cui grana non è dichiarata.

**MARCA** — `[R]`

---

## R4.12 Decisioni copiate invece che richiamate

**DOVE** — tre punti:

| | |
|---|---|
| **B3**, ultima riga | *«E i due certificati vanno tenuti distinti nel banco come nel codice: uno **longevo** per la pagina, uno **≤ 14 giorni** per la sessione. Confonderli fa ricomparire l'avviso ogni due settimane, e nessuno collegherebbe le due cose»* |
| **B10** | il paragrafo su `autenticazione_utente_atteso()` — *«Era giusto in v1, dove il server girava dentro la sessione di una persona; contraddice il multi-tenant»* |
| **B9** | *«la pagina gira su **tre motori** scritti da tre squadre che non ci conoscono… è il pezzo di arbitro che avevamo perso con `mstsc`»* |

**COSA CONTRADDICE** — `README.md` «Le convenzioni» (*«Le decisioni stanno in `DECISIONI.md`, una
sola volta. Gli altri documenti **rimandano, non copiano**»*), `PIANO.md` §0.3 regola 1 e
`fasi/README.md` regola 1. Il primo è `RCP.md` §4.1-bis parola per parola, ⛔ **incluso il ⚠
finale**; il secondo è `PIANO.md` fase 1 parola per parola; il terzo è `PIANO.md` §1.1, e nel
copiarlo **ha perso il rimando a `DECISIONI.md` §1.6** che l'originale porta.

**COME SI DIMOSTRA** — il giorno in cui i 14 giorni cambiassero (`RCP.md` §4.1-bis li marca `[S]`,
cioè letti in una specifica altrui che si muove), i posti da correggere sono tre e uno di essi è un
documento di fase che nessuno rilegge. È la ragione scritta della regola: *«undici registri delle
decisioni sono undici posti dove cercare, e prima o poi due si contraddicono»*. ⚠ Non vale per i
numeri **attesi** dei banchi — B6 e B8 devono dire 5 s · 60 s · 10 s e ≥ 1 s, o non sono banchi:
quella è la misura, non la decisione.

**MARCA** — `[R]`

---

## R4.13 L'atteso di S2 è la marca di un'altra misura

**DOVE** — `fasi/01-filo-nudo.md`, «Le misure», riga **S2**: *«HEVC Main10 **in hardware** |
telefono vero | Atteso: `[S]` **sì da Chrome 108**»*.

**COSA CONTRADDICE** — `web.md` §4.1: *«⛔ **su Android no**: quando non trova un decodificatore
HEVC hardware, Chromium ne sceglie **di proposito** uno **software** di MediaCodec `[R]`»*, e §4.2,
dove il `[S]` di Chrome 108 riguarda *«HEVC Main10 **in WebCodecs**»* — cioè il **supporto**, non
l'hardware. E `LEZIONI.md` §1.11 / forma d'errore **E1**, che `web.md` §1.1 punto 2 dichiara essere
*«il muro di v1 ricomparso un livello più in alto»*.

**COME SI DIMOSTRA** — la casella «atteso» è quella che il banco confronta con la casella
«misurato». Se il telefono decodifica Main10 **in software**, la misura risulta *«sì»* e coincide
con l'atteso: il banco è verde e la domanda che S2 pone — *in hardware?* — non ha ricevuto risposta.
⛔ È E1 messa nella casella dell'atteso, dove nessuno la cerca. ⚠ La stessa formulazione sta in
`PIANO.md` §1.2 e in `SPECIFICHE.md` §13: il documento di fase l'ha ereditata, non inventata, ma è
questo il documento in cui diventerà un numero.

**MARCA** — `[R]`

---

## R4.14 S1b: `[?]` in un documento, `[R]` in questo, e la promozione non è dichiarata

**DOVE** — `fasi/01-filo-nudo.md`, «Le misure», riga **S1b**: *«durata dell'eccezione su Chrome |
Atteso: **7 giorni `[R]`**»*.

**COSA CONTRADDICE** — `web.md` §8, «Quel che questo studio NON sa»: *«`[?]` **la durata
dell'eccezione su Chrome** | §3.3»*. La marca `[R]` viene da `web.md` §3.2
(`kCertErrorBypassExpirationInSeconds = 604800`): **le due righe di `web.md` si contraddicono**, e
il documento di fase ne ha scelta una **in silenzio**.

**COME SI DIMOSTRA** — chi legge `web.md` §8 pianifica una misura per **sapere** il numero; chi
legge il documento di fase la pianifica per **confermarlo**, e a un banco che deve aspettare una
settimana la differenza cambia la soglia di pazienza: un risultato a 6 giorni e 23 ore è un
successo nel secondo caso e un dato nel primo. ⛔ `README.md` chiede che una `[?]` promossa sia
dichiarata tale, con la fonte — qui la promozione c'è ed è probabilmente giusta, ma **non è
scritta**, ed è la forma **E5**.

**MARCA** — `[?]` — si chiude riconciliando `web.md` §3.2 e §8, non misurando.

---

## R4.15 «Questa tabella è costata il banco della rotella» non è quel che dice `LEZIONI.md`

**DOVE** — `fasi/01-filo-nudo.md`, B1, riga **S7**: *«in v1 **questa tabella** è costata il banco
della rotella»*.

**COSA CONTRADDICE** — `LEZIONI.md` §2.3: *«Il banco della rotella cercava `asse dy=-10` mentre il
registro scriveva `asse dx=0 dy=-10`: rosso, con **il codice corretto**»*. Il banco della rotella è
costato una **stringa di registro cercata male**, non una tabella di conversione col segno sbagliato.
La frase è ereditata da `RCP.md` §7.3, che la scrive per prima.

**COME SI DIMOSTRA** — chi costruisce S7 con questa premessa si guarda dal segno e non dal
confronto: e il controllo positivo di S7 (*«si inietta anche `-120`»*) protegge dal segno, non dal
modo in cui l'esito viene letto. La lezione vera — *un banco che confronta stringhe boccia il codice
giusto* — è quella che serviva a S7, e citando la lezione sbagliata **la si perde nel punto in cui
si applicherebbe**. ⚠ La cura sta in `RCP.md` §7.3, non qui.

**MARCA** — `[?]`

---

## R4.16 `GIA_ATTIVA_LOCALE` non è dichiarato da nessuna fase

**DOVE** — `fasi/01-filo-nudo.md`, **B7**, che elenca *«ciascuno dei motivi che **questa fase sa
produrre**»* — otto, senza `GIA_ATTIVA_LOCALE` — e **B12**, che colloca quel che la fase non prende.

**COSA CONTRADDICE** — `RCP.md` §8.2, motivo `0x05`, e `SPECIFICHE.md` §5.1 prima riga: *«ha una
sessione grafica **locale** attiva e apre una remota → ⛔ la remota è **rifiutata**, con messaggio
esplicito»*. `PIANO.md` fase 5 dichiara il **verso opposto** (`SESSIONE_LOCALE_PREVALSA`: la locale
che arriva e caccia la remota) e non questo; nessun'altra fase lo nomina.

**COME SI DIMOSTRA** — si cerca `GIA_ATTIVA_LOCALE` in `PIANO.md` e nei documenti di fase: non
compare. È un rifiuto che nasce **all'attacco**, cioè nel messaggio che questa fase scrive, e la
riga di `SPECIFICHE.md` §5.1 che lo impone è la stessa che genera `GIA_ATTIVA_REMOTA`, che invece
B3 prova. ⚠ Il gemello dei due è provato, l'altro no, e nessun documento dice dove va: **cade fra
le fasi**.

**MARCA** — `[?]` — basta una riga in B12 o in `PIANO.md`, non una misura.

---

# 3. ⭐ Quel che ho provato a rompere e non ci sono riuscito

*Dichiarato perché è informazione anche questa (`PIANO.md` §0.4, pratica 2).*

| Che cosa ho attaccato | Esito |
|---|---|
| **il conto dei dodici banchi di §11** | `RCP.md` §11 ne elenca **dodici**; la fase ne prende **sei** (B3 · B4 · B5 · B6 · B7 · B8) e B12 ne colloca **sei**. 6 + 6 = 12, e nessuno è contato due volte |
| **i tre tetti di §4.6** | 5 s · 60 s · 10 s, con `TEMPO_SCADUTO` `0x0D`: identici, e con il PING nella riga giusta |
| **i due motivi che NON viaggiano in un `CONGEDO`** | B7 esclude `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` **e cita il rilievo R1.18 che lo stabilisce**. È il punto in cui mi aspettavo la contraddizione, ed è quello scritto meglio |
| **tutti i codici numerici** | `0x09` `NIENTE_IN_COMUNE`, `0x0A` `VERSIONE_INCOMPATIBILE`, `0x0B` `ERRORE_PROTOCOLLO`, `0x0D` `TEMPO_SCADUTO`, `0x0E` `SESSIONE_NON_SERVIBILE`, `0x0F` `GIA_ATTIVA_REMOTA`: tutti concordi con §8.2 |
| **le sei registrazioni guaste di B4** | ogni rimando (§6.1 · §6.0 · §4.3 · §2.5 · §1 · §6.2) punta al paragrafo che contiene davvero la regola |
| **l'aritmetica del PCM** | 5 ms a 48 kHz, 2 canali, s16 = 480 campioni = 960 byte, + 12 di intestazione = **972**, sotto i ~1200 `[S]`. Torna |
| **le nove misure della sonda** | 4 (`PIANO.md` §1.2) + 6 (`web.md` §7) con la sovrapposizione dichiarata, + le tre `[?]` che vivono davvero in `RCP.md` §5.3, `RCP.md` §7.3 e `SPECIFICHE.md` §6.1-bis |
| **`stato = NUOVA` come `[?]` promossa a fatto** | non lo è: il confine lo dichiara con un ⛔ e scrive *«non è implementata»*. È l'opposto di **E5** |
| **il modello di `PIANO.md` §0.2** | tutte e otto le sezioni presenti, nell'ordine, comprese le due che si dimenticano sempre — «che cosa NON ha funzionato» e «il giudizio dell'utente» — **vuote per costruzione e dichiarate tali** |
| **i due file di banco citati** | `banchi/00-sessione-gnome.sh` e `banchi/00-c1-kwin.sh` esistono sul disco |
| **i numeri del limitatore in B8** | 5 in 5 minuti · 30 s che raddoppiano · 15 minuti · ≥ 1 s anche su `AMMESSO`: identici a `RCP.md` §4.4-bis, senza deriva |
| **il ⛔ di `RCP.md` §2.4 su `Alt-Svc`** | il documento di fase **non** lo ripete, pur essendo ancora vivo in `PIANO.md` fase 1 e in `DECISIONI.md` §6.4. Ha preso la versione corretta |

---

# 4. Il verdetto

⛔ **Il banco della fase 1 non si può ancora credere.**

**Non ho trovato niente** che smentisca l'impianto: i dodici banchi, la loro certificazione, il
cliente di prova e il validatore sono la struttura giusta, e le citazioni puntuali reggono quasi
tutte alla verifica riga per riga.

Ma **la lente della coerenza trova due cose che non sono dettagli**:

1. ⛔ **la copertura è di un verso solo.** 38 obblighi normativi non hanno un banco, e **undici di
   essi — contati uno per uno nel censimento — stanno dalla parte della pagina**: quel che il server
   le manda, e quel che lei deve farne. `RCP.md` §3 è scritta su *«un'implementazione RCP»* e §9 ha
   un **DEVE** esplicito del client: sono **simmetriche**, il banco no. In un progetto che ha perso
   `mstsc` e che scrive `RCP.md` proprio per non fidarsi di due programmi della stessa mano, un
   client mai messo alla prova è **il buco al posto dell'arbitro** (R4.1);
2. ⛔ **cinque righe promettono un comportamento che l'arbitro vieta o che un'altra fase rivendica**:
   la tela concessa contro §4.5 (R4.2), l'ordine B1→B2 (R4.3), la citazione di §4.1-bis rovesciata
   (R4.4), la vita della sessione presa in prestito dalla fase 5 (R4.5), il rilascio dei tasti
   mandato dove non si può eseguire (R4.7).

**I rilievi sono 16: 13 `[R]` e 3 `[?]`. Nessun `[M]` — non misuro.**

I `[R]` si correggono nel documento (o, per R4.4, in `RCP.md` §4.1-bis, che è la vera stonatura). I
`[?]` si chiudono riconciliando due documenti, non sul ferro.

⚠ E la regola che chiude ogni verdetto di questo progetto: **una revisione verde non sarebbe stata
un'approvazione**, e questa non è nemmeno verde.
