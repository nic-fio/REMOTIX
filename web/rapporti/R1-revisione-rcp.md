# R1 — Revisione avversariale di `RCP.md`

*9 agosto 2026. Revisore: agente avversariale (`REVIEWER.md`).*

**L'imputato**: `RCP.md`, 1.083 righe, versione del 9 agosto 2026 ore 17:43.
**La domanda che governa tutto**: *due programmatori che leggono questo documento da soli, senza
parlarsi, scrivono gli stessi byte?*

⛔ **Che cosa NON è questo rapporto.** Non è un'assoluzione di quel che non compare qui. Dove non ho
trovato niente lo scrivo con quelle parole (§B), mai «è corretto» (`REVIEWER.md` §0). Non ho
misurato nulla: non c'è una sola marca `[M]`.

**Il conto**: **26 `[R]`** · **3 `[?]`** · 0 `[M]`.

I rilievi sono ordinati **dal più grave al meno grave**, dove grave = *quanto costerebbe scoprirlo
dopo invece che adesso*.

---

## R1.1 — Il datagram del PCM non entra in un datagram QUIC

```
DOVE:              §5.3 (righe 622-631), incrociata con §6.3 (righe 744-765) e §2.1 (riga 137)
COSA CONTRADDICE:  RFC 9221 e RFC 9000, che §2 dichiara come base normativa
                   («QUIC versione 1 (RFC 9000)», riga 109);
                   `SPECIFICHE.md` §10 («PCM come base sempre disponibile»);
                   §4.3 riga 406, che fa del PCM il **controllo positivo** di Opus.
COME SI DIMOSTRA:  §5.3 prescrive, per il PCM: 48 000 Hz, 2 canali, s16, blocchi da 20 ms
                   = 1920 campioni = **3840 byte**. §6.3 mette davanti 12 byte di
                   intestazione. Il datagram che il server DEVE spedire è quindi di
                   **3852 byte**.
                   Un DATAGRAM di QUIC (RFC 9221) **non è frammentabile**: deve stare in un
                   singolo pacchetto QUIC. Su un percorso Internet normale (MTU 1500,
                   IPv6 40 + UDP 8 + intestazione QUIC e AEAD ~30) il carico utile
                   disponibile è ~1400 byte, e i browser espongono `maxDatagramSize`
                   intorno a **1200**. 3852 > 1200: il messaggio non parte, mai, su
                   nessun percorso reale.
                   Le due letture difendibili, e producono due prodotti diversi:
                   (a) «un blocco = un datagram» come dice la riga → l'audio PCM non
                       funziona affatto, e il **controllo positivo** di §4.3 è proprio la
                       cosa che non funziona: quando Opus si negozia male, si ripiega su
                       una strada che non c'è;
                   (b) «si spezza in più datagram» → serve un numero di sequenza e un
                       indice di frammento che **non esistono in §6.3**, e i due
                       programmatori li inventano diversi.
                   ⚠ E la forma dell'errore è quella di `LEZIONI.md` §2.2, riga 309:
                   «il banco contava blocchi riscontrati; il difetto cambiava i campioni —
                   l'audio era rumore a fondo scala». Qui non arriverebbe nemmeno il rumore.
MARCA:             [R]
```

---

## R1.2 — Il certificato è uno solo o sono due: §4.1 e §4.1-bis dicono il contrario, tutt'e due con ⛔

```
DOVE:              §4.1 righe 314-317  contro  §4.1-bis righe 339-342
COSA CONTRADDICE:  se stesse. Ed è la contraddizione che §0 esiste per impedire, perché
                   entrambe le righe sono marcate ⛔ (normative) e nessuna cita l'altra.
COME SI DIMOSTRA:  §4.1: «la pagina e la sessione WebTransport **devono presentare lo stesso
                   certificato** […] se portassero due certificati diversi l'utente si
                   troverebbe due avvisi».
                   §4.1-bis: «⛔ **Da cui due certificati, e vanno tenuti distinti nel
                   codice**: uno **longevo** per la pagina […] uno **a scadenza breve** per
                   la sessione».
                   Il programmatore A serve lo stesso certificato sui due ascoltatori di
                   §2.4. Ma §4.1-bis riga 334 impone alla sessione un certificato valido
                   **meno di 14 giorni** (vincolo `[S]` di `serverCertificateHashes`): quel
                   certificato è anche quello della pagina, quindi **l'avviso del browser
                   ricompare ogni due settimane** — esattamente il sintomo che §4.1-bis
                   riga 342 dichiara come conseguenza dell'errore opposto.
                   Il programmatore B genera due certificati. L'utente concede l'eccezione
                   sul certificato longevo della pagina; la sessione WebTransport ne
                   presenta un altro. §4.1 dice che questo produce «un avviso e un
                   fallimento muto».
                   Due implementazioni, due prodotti, e **nessuna delle due sbaglia a
                   leggere**: sbaglia il documento.
                   ⚠ La cura non è ovvia e non è mia da scrivere, ma il fatto che decide
                   sta già in casa: `S1-certificato.md` §1.5 dice che con
                   `serverCertificateHashes` il browser **non guarda l'eccezione** — quindi
                   i due certificati non devono essere «lo stesso», devono essere
                   **dichiarati** in due modi diversi. Questa è la riga che manca.
MARCA:             [R]
```

---

## R1.3 — Nessun motivo di congedo dice «un altro client ha preso il tuo posto», e §8.2 non è estendibile

```
DOVE:              §8.2 (righe 974-991), incrociata con §4.5 (`SESSIONE`, stato 2 = RIPRESA)
COSA CONTRADDICE:  `SPECIFICHE.md` §5.3 riga 246 («Un client che tace è un client che si è
                   staccato […] Chi arriva entra, senza timeout da aspettare»),
                   `DECISIONI.md` §4.4, e l'invariante **I2** di `CODER.md` §2 («la seconda
                   connessione è rifiutata con **messaggio esplicito**»).
                   E §9 riga 1012 vieta di aggiungere tipi o motivi dentro RCP/1.
COME SI DIMOSTRA:  Utente `nic` è attaccato dal portatile. Dal telefono apre la stessa
                   sessione. Due esiti sono possibili e RCP non ne sa esprimere **nessuno
                   dei due**:
                   — se vince chi arriva (SPECIFICHE §5.3), il portatile va congedato con un
                     motivo. I quattordici di §8.2 sono: utente, inattività, abbandono,
                     **sessione locale** prevalsa, **già attiva locale**, budget, credenziali,
                     tentativi, niente in comune, versione, protocollo, server in chiusura,
                     tempo scaduto, non servibile. Nessuno dice «un altro client remoto».
                     `SESSIONE_LOCALE_PREVALSA` (0x04) sarebbe **falso**: la §8.2 lo definisce
                     «l'utente ha aperto una sessione grafica **locale**», e §8.2 riga 993
                     impone che ogni motivo sia mostrabile all'utente in una frase
                     comprensibile. La frase sarebbe una bugia;
                   — se vince chi c'era (invariante I2), il telefono va rifiutato «con
                     messaggio esplicito», e l'unico motivo vicino è `GIA_ATTIVA_LOCALE`
                     (0x05), che dice **locale** e sarebbe falso allo stesso modo.
                   Il costo di scoprirlo dopo è quello di §9: un motivo nuovo è una
                   **versione maggiore nuova**, e la finestra per aggiungerlo gratis —
                   dichiarata in §0-bis riga 60 e in §9 riga 1020 — si chiude **al primo
                   byte scritto**. È il rilievo che il tempo rende irreparabile.
MARCA:             [R]
```

---

## R1.4 — Il motivo dentro il `CONNECTION_CLOSE` di QUIC: una pagina non lo scrive e non lo legge

```
DOVE:              §3.1 punto 3 (righe 275-282), §8.1 riga 964, §11 riga 1053
COSA CONTRADDICE:  §2.3 righe 168-172, che è la riga con cui questo stesso documento
                   riconosce il confine: «con un browser non si può: quei parametri li
                   sceglie lui, e nessuna riga di questo documento glieli cambia».
                   E `DECISIONI.md` §1.6 (il client è il browser).
COME SI DIMOSTRA:  §3.1 impone: «DEVE chiudere la connessione QUIC con `CONNECTION_CLOSE`
                   **di tipo applicativo**, e il codice d'errore applicativo DEVE essere il
                   codice del motivo di §8.2». §8.1 lo ripete per **chi chiude**, che è
                   `↔`: anche il client.
                   Il client è una pagina. L'API WebTransport non espone né la scrittura né
                   la lettura del `CONNECTION_CLOSE` della connessione QUIC: espone la
                   chiusura **della sessione**, con il proprio codice applicativo. Sono due
                   piani diversi, e la connessione HTTP/3 sottostante può reggere altro.
                   In concreto: il client rileva una lunghezza incoerente e applica §3.1.
                   Il punto 1 (registro) lo può fare, il punto 2 (`CONGEDO`) lo può fare,
                   il punto 3 **non lo può fare**. Un programmatore chiude la sessione con
                   codice 0x0B e dichiara assolta la regola; l'altro legge «connessione
                   QUIC» alla lettera, non trova l'API e lascia il punto 3 non
                   implementato. Due implementazioni, e la seconda **è conforme al testo
                   quanto la prima**.
                   ⛔ E il danno vero è a valle: §3.1 riga 278 dice che il punto 3 «è quello
                   che salva le diagnosi» quando il congedo non arriva, e §11 riga 1053
                   costruisce su di esso un banco — «per ciascuno dei quattordici motivi si
                   verifica **anche il codice nella chiusura QUIC**». Quel banco, dal lato
                   che riceve (cioè la pagina), **non è scrivibile**. La cura della ferita
                   di `LEZIONI.md` §1.7 poggia su una gamba sola senza che sia scritto da
                   nessuna parte.
MARCA:             [R]
```

---

## R1.5 — «Il primo stream bidirezionale (identificatore 0)»: in WebTransport lo 0 è già occupato

```
DOVE:              §4.2 riga 350, §2.5 righe 219 e 224-232
COSA CONTRADDICE:  §2 riga 109 (il trasporto è WebTransport su HTTP/3) e §2.3 riga 168.
                   È un resto della stesura a QUIC nudo.
COME SI DIMOSTRA:  In una connessione HTTP/3 lo stream QUIC **0** — primo bidirezionale
                   iniziato dal client — è quello della **richiesta HTTP**, cioè
                   verosimilmente lo stream del `CONNECT` esteso che **stabilisce la
                   sessione WebTransport stessa**. Il primo stream bidirezionale che la
                   pagina può aprire dentro la sessione non ha identificatore 0, e l'API
                   non gliene mostra nessuno: `createBidirectionalStream()` restituisce un
                   oggetto, non un numero.
                   Due letture, entrambe difendibili:
                   (a) «identificatore 0» = lo stream QUIC numero 0 → il server cerca il
                       canale di controllo su uno stream su cui sta arrivando il `CONNECT`,
                       e non lo trova mai;
                   (b) «identificatore 0» = il primo stream bidirezionale **della sessione
                       WebTransport**, qualunque numero abbia → funziona, ma allora §2.5
                       riga 224 («Il client NON DEVE aprire stream bidirezionali oltre lo
                       0») e §2.5 riga 232 («il controllo vive solo sullo stream 0») vanno
                       riscritte, perché parlano di un numero che nessuno dei due lati usa.
                   Il sintomo della lettura (a) è una connessione che non parte, con la
                   diagnosi «il client non apre il canale di controllo» — e il client lo ha
                   aperto.
MARCA:             [R]
```

---

## R1.6 — `numero` «senza buchi voluti» spegne in silenzio il meccanismo di recupero di §5.2

```
DOVE:              §6.2 riga 719 («contatore del fotogramma, crescente, **senza buchi
                   voluti**») contro §5.2 riga 604 e §2.3 riga 178
COSA CONTRADDICE:  §5.1 riga 573 (il server PUÒ abbandonare un fotogramma), §2.3 riga 178
                   («quando il credito manca, si BUTTA il fotogramma»), §5.2 riga 604
                   («il client DEVE mandare `RICHIEDI_CHIAVE` quando si accorge di un
                   **buco** nella successione dei `numero`»).
COME SI DIMOSTRA:  Il server cattura i fotogrammi 100, 101, 102. Abbandona il 101 con
                   `RESET_STREAM` (§5.1). Due letture di «senza buchi voluti»:
                   (a) il contatore conta i fotogrammi **catturati** → il client vede
                       100, 102, riconosce il buco e chiede la chiave. Il meccanismo
                       funziona, ma la riga «senza buchi voluti» è falsa: il buco è
                       precisamente **voluto**, lo ha voluto §5.1;
                   (b) il contatore conta i fotogrammi **spediti** — che è la lettura
                       letterale, perché è l'unico modo di non avere buchi voluti → il
                       client vede 100, 101 (che è il vecchio 102) e **non c'è nessun
                       buco da riconoscere**. `RICHIEDI_CHIAVE` non parte mai, il
                       decodificatore resta rotto fino alla chiave successiva, e il
                       sintomo è «l'immagine si sfascia ogni tanto sulle reti brutte».
                   La lettura (b) non è una svista: è ciò che la riga dice. E il banco di
                   §11 riga 1056 («si abbandona un delta di proposito e si verifica che
                   arrivi una chiave») **resta verde anche con (b)**, perché §5.2 riga 602
                   obbliga il server a mandare la chiave da sé dopo un abbandono: il banco
                   misura il ramo del server, non quello del client. È `LEZIONI.md` §1.3 —
                   un banco che non riproduce il difetto.
MARCA:             [R]
```

---

## R1.7 — Un fotogramma abbandonato e uno finito hanno lo stesso aspetto: manca la regola sul FIN

```
DOVE:              §6.2 riga 696 («Nessuna lunghezza: **la fine dello stream è la fine del
                   fotogramma**») contro §5.1 riga 573 e §5.2 riga 606
COSA CONTRADDICE:  §5.2 riga 606: «finché non arriva una chiave, il client NON DEVE mostrare
                   fotogrammi che sa incompleti»; e `REVIEWER.md` §2, forma d'errore **E8**
                   («il silenzio scambiato per zero»: qui, uno stream troncato scambiato per
                   uno stream finito).
COME SI DIMOSTRA:  Il server apre lo stream del fotogramma 101, spedisce l'intestazione di
                   28 byte e 40 KB di dati su 60 KB, poi chiama `RESET_STREAM` perché è
                   partito il 102 (§5.1).
                   Il client ha in mano 40 KB e uno stream che **è finito**. §6.2 gli dice,
                   in una riga sola, che la fine dello stream è la fine del fotogramma:
                   consegna 40 KB al decodificatore. Il decodificatore o rifiuta, o —
                   peggio — produce mezza immagine.
                   L'altra lettura, altrettanto difendibile: «solo uno stream chiuso con FIN
                   porta un fotogramma completo; uno stream azzerato si butta». È quella
                   giusta, **e non è scritta da nessuna parte**. Le due parole che mancano
                   in §6.2 sono «con FIN».
                   ⚠ Nota che il client non può nemmeno usare la lunghezza per accorgersene:
                   §6.2 dichiara apposta che non c'è nessuna lunghezza. L'unica informazione
                   che distingue i due casi è **come** lo stream è terminato, e il documento
                   non ne parla mai.
MARCA:             [R]
```

---

## R1.8 — I 60 secondi della password contro i 30 secondi del silenzio, senza nessuno che tenga viva la linea

```
DOVE:              §4.6 riga 541 (60 s da `ECCOMI` a `CREDENZIALI`) contro §2.2 riga 146
                   (`max_idle_timeout` = 30 s) e §2.2 riga 161 (niente battito applicativo)
COSA CONTRADDICE:  se stesso; e `SPECIFICHE.md` §5.3 («silenzio del client: 30 secondi → il
                   client si considera staccato»).
COME SI DIMOSTRA:  Il server manda `ECCOMI`. L'utente digita la parola d'ordine con calma:
                   45 secondi. Sul filo, in quei 45 secondi, non passa **niente** — §2.2
                   vieta un battito applicativo, e non c'è nessun altro canale attivo prima
                   dell'attacco.
                   Al secondo 30 scatta il tempo di inattività di QUIC, che §2.2 dichiara
                   «l'orologio del silenzio: scaduto, il client è staccato». La connessione
                   muore **prima** che il tetto di 60 secondi possa mai essere raggiunto, e
                   muore in silenzio: il tempo di inattività di QUIC chiude senza
                   `CONNECTION_CLOSE`, quindi nessuno dei due lati manda un motivo e §3.1
                   non si applica.
                   Il tetto di 60 secondi di §4.6 è dunque **irraggiungibile per
                   costruzione**: nessuna implementazione conforme lo vedrà mai scadere, e
                   il banco di §11 riga 1058 («si apre una connessione e si tace, per
                   ciascuno dei tre tetti di §4.6») fallirà sul secondo tetto misurando 30 s
                   invece di 60 — e il programmatore penserà che sbagli il banco.
                   La sola via d'uscita è che qualcuno mandi PING di trasporto durante
                   l'attesa. Non è vietato da §2.2 (non è un battito **applicativo**), ma
                   **non è scritto**: un'implementazione lo fa, l'altra no, e la seconda
                   perde gli utenti che digitano piano. Difetto intermittente, il peggiore
                   da diagnosticare.
MARCA:             [R]
```

---

## R1.9 — «Si butta il fotogramma» butta anche le chiavi, e non lascia traccia nel registro

```
DOVE:              §2.3 riga 178 contro §5.2 riga 601 e §5.1 riga 578
COSA CONTRADDICE:  §5.2 riga 601 («il server **NON DEVE** abbandonare un fotogramma
                   **chiave**. Abbandonare la cura non è una cura»); §5.1 riga 578 («ogni
                   abbandono **DEVE** essere scritto nel registro»); invariante **I1** di
                   `CODER.md` §2 e `REVIEWER.md` §3 («ogni degradazione che avvenga senza
                   una riga nel registro»).
COME SI DIMOSTRA:  Sequenza concreta. La linea peggiora, il server abbandona il delta 400
                   (§5.1) e, come impone §5.2 riga 602, prepara subito un fotogramma
                   **chiave**, il 401. In quel momento il credito degli stream concesso dal
                   browser è esaurito — è proprio la condizione che ha appena prodotto
                   l'abbandono. §2.3 riga 178 ordina: «⛔ e quando il credito manca, si
                   **BUTTA** il fotogramma, non si aspetta».
                   Il fotogramma buttato è **la chiave**. §5.2 lo vieta con un ⛔, §2.3 lo
                   impone con un ⛔. Le due righe non si citano.
                   E il caso si richiude su sé stesso: il client chiede una chiave con
                   `RICHIEDI_CHIAVE`, il server la produce, il credito manca ancora, la
                   butta ancora. Il decodificatore resta rotto finché il credito non torna,
                   e nel frattempo §5.2 riga 606 vieta al client di mostrare qualunque cosa:
                   **schermo fermo, e nessuna riga nel registro che dica perché**, perché
                   l'obbligo di registro di §5.1 parla di «abbandono» (`RESET_STREAM`) e qui
                   lo stream non è mai nato.
                   Due misure diverse sotto la stessa etichetta: è la forma d'errore **E2**
                   di `REVIEWER.md` §2, quella che §4.5 riga 503 cita per giustificare la
                   parità dei lati.
MARCA:             [R]
```

---

## R1.10 — La quarta eccezione non dichiarata a §3: una misura fuori limiti che non uccide la connessione

```
DOVE:              §7.1 righe 805-812 (`TELA`, motivo 2 = `MISURA_FUORI_LIMITI`) contro
                   §4.5 riga 498
COSA CONTRADDICE:  §3 riga 249 («Vale per: […] un **campo fuori intervallo**») e §3 riga 260,
                   che dichiara **una sola** eccezione, più le due aggiunte in §6.3 riga 763
                   e §7.1 riga 853 — tre in tutto, contate dal documento stesso.
COME SI DIMOSTRA:  Lo stesso valore, 100×100, in due messaggi diversi:
                   — in `ATTACCA` (§4.5 riga 498): «⛔ I limiti, e sono normativi […] Fuori
                     da lì è `ERRORE_PROTOCOLLO`» → la connessione **cade**;
                   — in `ADATTA_TELA` (§7.1): il server risponde
                     `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)` → la connessione **vive**, e il
                     campo fuori intervallo è stato tollerato.
                   Un programmatore che legge §3 come prima regola scrive un validatore
                   unico sui campi di geometria e chiude la connessione in tutti e due i
                   casi — con il risultato che l'utente che sbaglia a trascinare una
                   finestra si vede cadere la sessione. Un altro legge §7.1 e tollera.
                   Entrambi hanno una riga ⛔ dalla loro.
                   ⚠ E il motivo `MISURA_FUORI_LIMITI` **esiste** in `TELA`: la tolleranza è
                   voluta. Il difetto non è la scelta, è che non è dichiarata come eccezione
                   nel posto dove §3 tiene il conto delle eccezioni — che è precisamente il
                   meccanismo con cui questo documento si difende dall'indulgenza.
MARCA:             [R]
```

---

## R1.11 — Gli appunti: un trasferimento non può stare su «il suo stream», e non ha un identificatore

```
DOVE:              §7.4 riga 950, §2.5 riga 222, §7.4 righe 934-943
COSA CONTRADDICE:  §2.5 riga 222 (gli stream degli appunti sono **unidirezionali**, aperti
                   da **entrambi**) e §6.0 riga 674 («Ogni intero ha un solo significato di
                   assente, e va dichiarato dove serve»).
COME SI DIMOSTRA:  §7.4 riga 950: «⛔ **Ogni trasferimento va sul suo stream**, e i tre
                   messaggi **non DEVONO** essere mescolati con quelli di un altro
                   trasferimento».
                   Ma i tre messaggi di un trasferimento viaggiano in **due versi**:
                   `APPUNTI_ANNUNCIO` (A→B), `APPUNTI_CHIEDI` (B→A), `APPUNTI_TESTO` (A→B).
                   Gli stream sono unidirezionali. Un trasferimento occupa quindi **almeno
                   due stream**, uno per verso, e la regola «un trasferimento, uno stream»
                   non è soddisfacibile da nessuna implementazione.
                   Peggio: **non esiste nessun campo che leghi i due stream**.
                   `APPUNTI_CHIEDI` ha «corpo vuoto» (riga 938). Caso concreto:
                     t0  server → client:  APPUNTI_ANNUNCIO(lunghezza=12)   [stream S1]
                     t1  server → client:  APPUNTI_ANNUNCIO(lunghezza=4096) [stream S2]
                     t2  client → server:  APPUNTI_CHIEDI                   [stream S3]
                   A quale dei due annunci risponde S3? Il ricevente non ha **nessun byte**
                   per deciderlo. §7.4 riga 951 se ne accorge a metà — «un `APPUNTI_CHIEDI`
                   che arriva quando l'annuncio è già stato superato si serve con il testo
                   attuale» — ma quella riga risolve la corsa e non la **correlazione**: con
                   due trasferimenti aperti nei due versi contemporaneamente (l'utente copia
                   di qua mentre incolla di là) le due implementazioni appaiano le richieste
                   agli annunci in ordine diverso e si scambiano i testi.
                   ⚠ E la regola «non DEVONO essere mescolati» non è verificabile da nessuno:
                   non c'è un identificatore da controllare. È una regola con **DEVE** che
                   nessun banco può vedere fallire.
MARCA:             [R]
```

---

## R1.12 — Un valore sconosciuto dentro una capacità conosciuta: si ignora o si muore?

```
DOVE:              §4.3 righe 378-404
COSA CONTRADDICE:  §3 riga 260, che dichiara l'eccezione per le **capacità** ma la definisce
                   su «una **voce** sconosciuta», e §4.3 riga 378 che la restringe a «un
                   **nome** sconosciuto».
COME SI DIMOSTRA:  Il client manda in `CIAO`:
                     nome  = "video.codec"       (nome CONOSCIUTO)
                     valore= "hevc,vp9"          (un valore dell'elenco SCONOSCIUTO)
                   Lettura A: la regola di §4.3 riga 378 copre solo i **nomi**; un valore
                   fuori dall'elenco dichiarato è «un campo fuori intervallo», quindi §3
                   ordina `ERRORE_PROTOCOLLO` e la connessione cade.
                   Lettura B: il senso dell'eccezione è la crescita per capacità (§9 riga
                   1012); un valore sconosciuto si scarta e si intersecano gli altri,
                   quindi si negozia `hevc` e la sessione parte.
                   Le due letture producono **byte diversi sul filo per lo stesso ingresso**,
                   ed è il caso che si presenta il primo giorno in cui esisterà un RCP/2 che
                   parla `vvc`: il server vecchio o continua o cade, e il documento non dice
                   quale.
                   ⚠ La stessa domanda, senza risposta, su: `video.profondita = "8,12"`;
                   `audio.codec = "opus,flac"`; `input.tocco = "forse"`; e sul **mittente
                   sbagliato** — `video.misura_massima` è dichiarato «client» in tabella,
                   e non è scritto che cosa succede se lo manda il server (nome conosciuto,
                   quindi l'eccezione dei nomi non si applica).
                   ⚠ E ancora: §4.3 riga 406 impone che `pcm` e `8` siano dichiarati da
                   entrambi con un **DEVE**, ma non dice con quale motivo si congeda chi non
                   lo fa: `NIENTE_IN_COMUNE` (0x09) o `ERRORE_PROTOCOLLO` (0x0B)? Due
                   implementazioni, due codici, e il banco di §11 riga 1053 ne aspetta uno.
MARCA:             [R]
```

---

## R1.13 — `TROPPI_TENTATIVI`: dentro quale messaggio, e «attesa» di che cosa

```
DOVE:              §4.4-bis righe 465-470, incrociata con §4.4 righe 428-445 e §8.2 riga 985
COSA CONTRADDICE:  §4.4 riga 447, che dichiara di aver **già chiuso** esattamente questa
                   forma di ambiguità per `CREDENZIALI_ERRATE` («senza dire se dopo il primo
                   arrivasse anche il secondo […] due implementazioni potevano indovinare
                   diverso»). La stessa ambiguità è rimasta viva sul motivo accanto.
COME SI DIMOSTRA:  **Prima ambiguità — il contenitore.** §4.4-bis: «ogni nuovo tentativo
                   riceve `TROPPI_TENTATIVI`». `TROPPI_TENTATIVI` è un **motivo** (§8.2,
                   0x08), non un messaggio. Due letture:
                     A) `RESPINTO`(0x0005) con corpo `u8 = 0x08` — coerente con §4.4, che fa
                        di `RESPINTO` «il congedo dell'autenticazione»;
                     B) `CONGEDO`(0x000C) con corpo `u8 = 0x08` + stringa — coerente con
                        §8.2, che è intitolata «I motivi» del **congedo**.
                   Sul filo sono due tipi diversi (`0x0005` contro `0x000C`) e due corpi di
                   lunghezza diversa (1 byte contro 3+n). Il client che aspetta A e riceve B
                   applica §3 e chiude per errore di protocollo: **il limitatore dei
                   tentativi diventa un errore di protocollo**, e la diagnosi punterà
                   ovunque tranne che qui.
                   **Seconda ambiguità — che cosa è «l'attesa».** «riceve `TROPPI_TENTATIVI`
                   […] per un'attesa che parte da 30 secondi e raddoppia fino a 15 minuti»:
                     C) il server **ritarda la risposta** di 30 s (poi 60, 120 … 900);
                     D) il server risponde **subito**, e resta in rifiuto per una **finestra**
                        di 30 s (poi 60, 120 … 900).
                   La lettura C è dimostrabilmente impossibile: §2.2 fissa il tempo di
                   inattività a **30 secondi**, e §4.4 + `DECISIONI.md` §1.5 riga 10 impongono
                   **un solo tentativo per connessione** — quindi il server dovrebbe tenere
                   viva e muta una connessione per 15 minuti, cioè trenta volte il tempo di
                   inattività. Con C il rifiuto non arriva mai al client, che vede solo una
                   connessione caduta.
                   Due programmatori onesti scrivono due limitatori incompatibili, e nessuno
                   dei due sbaglia a leggere.
MARCA:             [R]
```

---

## R1.14 — `DECISIONI.md` §1.5 tiene tre righe che `RCP.md` ha già smentito

```
DOVE:              `DECISIONI.md` §1.5, righe 6, 7 e 8 della tabella (righe 226-228 del file)
                   contro `RCP.md` §2.3 riga 176 e §4.1-bis riga 334
COSA CONTRADDICE:  `SPECIFICHE.md` riga 672: «quando una misura contraddice questo documento,
                   lo si aggiorna **nello stesso momento**. Un riferimento che invecchia in
                   silenzio è peggio di nessun riferimento».
COME SI DIMOSTRA:  Riga 6 di `DECISIONI.md` §1.5: «**credito degli stream ≥ 256**, e va
                   rinnovato», con rimando a `RCP.md` §2.3. `RCP.md` §2.3 riga 176 dice
                   **16**, e la riga 168 spiega perché il 256 è caduto (i parametri li sceglie
                   il browser). Chi implementa leggendo `DECISIONI.md` — che è il documento
                   delle decisioni — scrive 256. Chi legge `RCP.md` scrive 16. Il numero
                   256 sopravvive anche in `RCP.md` §11 riga 1057, dove però è il numero di
                   **fotogrammi** del banco: due grandezze diverse con lo stesso numero, in
                   due documenti, sullo stesso argomento.
                   Riga 7: «l'impronta si calcola sulla **chiave pubblica**, non sul
                   certificato», con la ragione «un certificato riemesso con la stessa chiave
                   non deve far scattare l'avviso». `RCP.md` §4.1-bis riga 333 dice
                   «l'impronta **SHA-256 del certificato**», e `S1-certificato.md` §1.5 lo
                   conferma `[S]`: «impronta SHA-256 del **DER**». Chi implementa la riga 7
                   pubblica nella pagina l'impronta della SPKI, il browser la confronta con
                   quella del DER, **non combaciano mai**, e il sintomo è «WebTransport non
                   si connette» senza nessun errore che nomini l'impronta. E la ragione
                   scritta accanto — la riemissione con la stessa chiave — è **decaduta**:
                   con `serverCertificateHashes` ogni riemissione cambia l'impronta comunque.
                   È `LEZIONI.md` §2.3-quater, la decisione presa citando un comportamento mai
                   misurato.
                   Riga 8: «il client **spegne** i controlli X.509 di serie». Il client è una
                   pagina: non ha nessun controllo X.509 da spegnere. Resto della stesura
                   precedente, rimasto nel documento che dice che cosa è stato deciso.
MARCA:             [R]
```

---

## R1.15 — La quinta eccezione non dichiarata: `RICHIEDI_CHIAVE` si può ignorare

```
DOVE:              §5.2 riga 608
COSA CONTRADDICE:  §3 riga 245: «DEVE chiudere la connessione […] **NON DEVE ignorarlo**»,
                   e §3 riga 262, che distingue «ignorare *un'offerta*» (lecito) da
                   «ignorare *un comando*» (vietato).
COME SI DIMOSTRA:  «⚠ il server **PUÒ ignorare** `RICHIEDI_CHIAVE` ripetute entro **200 ms**
                   l'una dall'altra». `RICHIEDI_CHIAVE` non è un'offerta di capacità: è un
                   comando, ed è per giunta il comando che §5.2 ha inventato apposta per
                   uscire da uno stato rotto. Ignorarlo è precisamente la cosa che §3 vieta,
                   e non compare fra le eccezioni che il documento si dichiara (§3 riga 260,
                   §6.3 riga 763, §7.1 riga 853).
                   Il caso limite che due programmatori scrivono diverso: il client manda
                   `RICHIEDI_CHIAVE(ultimo=400)` a t=0 e `RICHIEDI_CHIAVE(ultimo=400)` a
                   t=190 ms, perché nel frattempo il decodificatore ha rifiutato un altro
                   fotogramma. Il server A ignora la seconda (è dentro i 200 ms). Il server B
                   nota che **il corpo è cambiato** rispetto al caso previsto — non lo è —
                   ovvero conta i 200 ms dall'ultima **chiave spedita** invece che
                   dall'ultima richiesta **ricevuta**: il documento non dice da quale dei due
                   eventi si contano. Due orologi, due comportamenti, e la differenza si vede
                   solo su una linea cattiva, cioè quando nessuno sta guardando (§11 riga
                   1056 lo dice per l'abbandono, e vale identico qui).
                   ⚠ E un terzo caso di tolleranza non dichiarata nella stessa famiglia:
                   §7.4 riga 951, un `APPUNTI_CHIEDI` fuori tempo «si serve con il testo
                   attuale» invece di essere un errore.
MARCA:             [R]
```

---

## R1.16 — Una coordinata sul bordo della tela: legale o mortale?

```
DOVE:              §7.3 righe 909-912
COSA CONTRADDICE:  §6.0 riga 674 («Ogni intero ha un solo significato di assente, e va
                   dichiarato dove serve: non esistono valori sentinella impliciti») —
                   qui manca l'intervallo, che è la stessa specie di omissione.
COME SI DIMOSTRA:  Tela concessa 1920×1080. Il client manda `PUNTATORE(x=1920, y=1080)`,
                   cioè il puntatore all'angolo in basso a destra come lo calcola una
                   pagina che divide la posizione del mouse per il fattore di scala e
                   arrotonda per eccesso.
                   Lettura A: le coordinate sono **indici di pixel**, quindi valide da 0 a
                   1919 e da 0 a 1079. 1920 è «fuori dalla tela» → §7.3 riga 911 impone
                   `ERRORE_PROTOCOLLO`, **la sessione cade**.
                   Lettura B: le coordinate sono **posizioni** sulla superficie, e 1920 è il
                   bordo destro, dentro la tela → si inietta.
                   Il documento scrive «una coordinata **fuori dalla tela**» e non definisce
                   il confine. La lettura A trasforma un arrotondamento del client in una
                   disconnessione, ed è la forma che `SPECIFICHE.md` §8.3 vieta («mai
                   staccare»); la lettura B lascia passare un pixel che non esiste.
                   ⚠ La stessa ambiguità si ripresenta amplificata in §7.1 riga 851, dove
                   dopo `TELA(ADATTATA)` il server deve **saturare** le coordinate vecchie
                   «alla nuova» tela per un secondo: saturare a 1919 o a 1920 sono due
                   implementazioni, e la differenza è un clic che cade su una finestra
                   diversa.
MARCA:             [R]
```

---

## R1.17 — La vista con lati pari e minimo 320×240: una finestra di browser non li garantisce

```
DOVE:              §7.1 riga 846 («⛔ **La vista DEVE stare dentro i limiti di §4.5** — pari,
                   e fra 320×240 e 7680×4320»)
COSA CONTRADDICE:  §4.5 riga 501, che giustifica la parità **solo** con i blocchi del
                   codificatore; e §7.1 riga 822, che dichiara che in RCP/1 la vista **non
                   cambia la misura di quel che si codifica**. La ragione della regola non si
                   applica all'oggetto della regola.
COME SI DIMOSTRA:  L'utente stringe la finestra del browser a 300 px di larghezza, o apre la
                   pagina in una finestra affiancata su un telefono. La vista reale è
                   300×800. Il client deve mandare `VISTA`:
                   — se manda 300×800, il server applica §3 (campo fuori intervallo) e
                     **chiude la connessione** perché l'utente ha ridimensionato una
                     finestra;
                   — se manda 320×800 mentendo, ha appena introdotto una misura diversa sotto
                     la stessa etichetta — la forma d'errore **E2** che §4.5 riga 503 cita
                     per giustificare questa stessa regola;
                   — se non manda niente, il server continua a spendere bit per la vista
                     vecchia, che è l'unico uso dichiarato del messaggio (§7.1 riga 824).
                   Sulla parità: su un telefono con fattore di scala 2,75 una finestra di
                   393 px CSS vale 1080,75 px fisici. Qualunque arrotondamento produce un
                   numero che può essere dispari, e il client **deve** arrotondarlo ancora
                   per rispettare §7.1 — un arrotondamento silenzioso in più, di nuovo E2, su
                   un numero che in RCP/1 non tocca nessun codificatore.
                   ⚠ Nessun banco di §11 guarda `VISTA`: il difetto vivrebbe finché qualcuno
                   non stringe una finestra.
MARCA:             [R]
```

---

## R1.18 — §11 non contiene nessun banco per l'audio, per gli appunti, né per il rilascio dei tasti

```
DOVE:              §11 righe 1049-1058 (otto banchi elencati)
COSA CONTRADDICE:  §5.3 (formato audio), §5.4 e §7.4 (appunti), §7.3 riga 921 («⛔ **Al
                   distacco si rilascia tutto**»), §4.4-bis riga 470 (il ritardo fisso),
                   §4.3 riga 411 (la scelta va scritta nel registro); e `LEZIONI.md` §2.2
                   riga 309, dove il difetto dell'audio a fondo scala è **già stato pagato**
                   con un banco che contava blocchi invece di ascoltarli.
COME SI DIMOSTRA:  Regole normative che nessuno degli otto banchi saprebbe vedere fallire:
                   1. **§7.3 riga 921, il rilascio dei tasti al distacco.** Un server che
                      dimentica di rilasciare Ctrl lascia una sessione inservibile al
                      riattacco, e §7.3 riga 923 dichiara che «nessuno collega le due cose»
                      (trappola 11 di `LEZIONI.md` §4). Nessun banco di §11 stacca una
                      connessione con un tasto premuto e riattacca a verificare. È la regola
                      con il rapporto danno/costo di banco più alto del documento.
                   2. **§5.3, il formato audio.** Nessun banco apre un datagram. Un server
                      che spedisce 44 100 Hz invece di 48 000, o PCM big-endian invece di
                      little-endian, resta verde su tutti e otto — e il sintomo, come in v1,
                      «sembra un difetto di rete» (§5.3 riga 620, che lo scrive e poi non
                      mette il banco).
                   3. **§5.4 e §7.4, gli appunti.** Ventisette righe normative, tre tipi di
                      messaggio, zero banchi.
                   4. **§4.4-bis riga 470, il secondo fisso anche su `AMMESSO`.** È una
                      proprietà di sicurezza che si misura solo col cronometro, e nessun
                      banco cronometra. Una regressione che la togliesse non farebbe fallire
                      niente e rimetterebbe il canale del tempismo che §4.4 vieta.
                   ⛔ E un banco elencato che non è eseguibile come è scritto: §11 riga 1053
                   chiede il congedo «per ciascuno dei **quattordici** motivi». I motivi 0x07
                   (`CREDENZIALI_ERRATE`) e 0x08 (`TROPPI_TENTATIVI`) **non viaggiano mai in
                   un `CONGEDO`**: §4.4 riga 442 impone `RESPINTO` e vieta esplicitamente di
                   mandare anche `CONGEDO`. Il banco fallisce su due motivi su quattordici
                   per costruzione, e chi lo scrive penserà di aver sbagliato lui.
MARCA:             [R]
```

---

## R1.19 — Il disegno di §1 dice ancora che il client confronta il certificato col ricordo

```
DOVE:              §1 riga 74 (passo ②: «il client CONFRONTA col ricordo»)
COSA CONTRADDICE:  §4.1 righe 293-303, che dichiara quei passi **riscritti due volte** e
                   caduti; §4.1-bis riga 333, dove il modello è l'opposto — l'impronta viene
                   **dichiarata dalla pagina**, non ricordata dal client; e `S1-certificato.md`
                   §1, che dimostra `[R]` che l'eccezione non è nemmeno consultabile.
COME SI DIMOSTRA:  §1 è «il modello, in una pagina»: è la sezione che chi arriva legge per
                   prima e l'unica che si tiene a mente. Il passo ② descrive il modello di
                   fiducia **della prima stesura** — TOFU, il client che si ricorda
                   l'impronta e la confronta — che era la forma con un client nostro
                   (`DECISIONI.md` §1.3, «ricordata in silenzio, mai confermata a mano»).
                   Con il browser il confronto lo fa il motore, e ciò che il prodotto fa è
                   **pubblicare** l'impronta nella pagina perché il browser la accetti.
                   Un programmatore che implementa §1 scrive un magazzino di impronte lato
                   client — che in una pagina significa `localStorage` — e una schermata di
                   avviso nostra. Sono due settimane di lavoro su un meccanismo che §4.1-bis
                   ha sostituito, e non le vede sbagliate finché non arriva a §4.1.
                   ⚠ Nella stessa riga, «① QUIC + TLS 1.3 UDP 7447» omette il passo che §2.4
                   dichiara obbligatorio — il caricamento della pagina in TCP — cioè
                   **l'unico posto dove l'utente vede l'avviso**.
MARCA:             [R]
```

---

## R1.20 — Gli appunti: un tipo MIME senza campo, e due lunghezze per la stessa cosa

```
DOVE:              §7.4 riga 948 e §5.4 riga 642, contro §7.4 righe 940-943 e §6.1 riga 686
COSA CONTRADDICE:  §2.2 riga 161, che vieta i doppi meccanismi con la ragione esatta:
                   «un secondo meccanismo produrrebbe **due verità sullo stesso fatto**».
COME SI DIMOSTRA:  **Il tipo che non c'è.** §7.4 riga 948: «⛔ Solo
                   `text/plain;charset=utf-8`. Un **tipo diverso** è `ERRORE_PROTOCOLLO`».
                   Nessuno dei tre messaggi di §7.4 porta un campo di tipo: `APPUNTI_ANNUNCIO`
                   è `u32 lunghezza`, `APPUNTI_CHIEDI` è vuoto, `APPUNTI_TESTO` è
                   `u32 lunghezza` + byte. **Non esiste un ingresso che possa violare questa
                   regola**, quindi nessuna implementazione la può rispettare o violare e
                   nessun banco la può vedere fallire. Peggio: suggerisce a chi legge che un
                   campo di tipo debba esserci, e un programmatore diligente lo aggiunge —
                   sfasando di 4 o 32 byte tutto il corpo rispetto all'altro.
                   **Le due lunghezze.** Un `APPUNTI_TESTO` con 10 byte di testo:
                     tipo=0x0203 · lunghezza(§6.1)=14 · lunghezza(§7.4)=10 · 10 byte
                   Che cosa fa il ricevente se legge `lunghezza(§6.1)=14` e
                   `lunghezza(§7.4)=12`? §6.1 riga 686 dice «una lunghezza incoerente con
                   quel che il tipo prevede DEVE chiudere», ma non dice **quale delle due**
                   sia la verità né se il controllo sia obbligatorio; e §6.1 riga 691 impone
                   di controllare la lunghezza **prima di allocare**, cioè di fidarsi di una
                   delle due. Un'implementazione alloca su quella esterna, l'altra su quella
                   interna, e la differenza è il difetto di memoria che §6.1 riga 691 esiste
                   per impedire.
                   ⚠ La stessa ridondanza esiste in `CURSORE_FORMA`, ma lì §7.2 riga 870 la
                   risolve con una riga esplicita («la lunghezza DEVE valere esattamente
                   8 + l×a×4»). Per gli appunti quella riga manca.
MARCA:             [R]
```

---

## R1.21 — Il cursore: larghezza 0 con altezza diversa da 0, e un punto attivo senza intervallo

```
DOVE:              §7.2 righe 862-873 contro §5.5 riga 650 e `DECISIONI.md` §1.5 riga 17
COSA CONTRADDICE:  §6.0 riga 674 («non esistono valori sentinella impliciti»); e la riga 17
                   di `DECISIONI.md` §1.5 dice «`larghezza = 0` vuol dire nascosto», mentre
                   `RCP.md` §5.5 riga 650 dice «`larghezza = altezza = 0`». Due documenti,
                   due condizioni.
COME SI DIMOSTRA:  Il server manda `CURSORE_FORMA` con larghezza=0, altezza=17,
                   attivo_x=0, attivo_y=0, e nessun byte d'immagine. Lunghezza del corpo: 8.
                   La regola di §7.2 riga 870 è soddisfatta: 8 + 0×17×4 = 8. ✔
                   Lettura A (§7.2 riga 863, «0 = cursore nascosto» scritto **solo** accanto
                   a larghezza, e `DECISIONI.md` riga 17): è un cursore nascosto valido.
                   Lettura B (§5.5 riga 650, «larghezza = **altezza** = 0»): è un messaggio
                   malformato → `ERRORE_PROTOCOLLO`, connessione chiusa.
                   Un server che nasconde il cursore azzerando solo la larghezza — che è la
                   lettura di `DECISIONI.md` — fa cadere la sessione contro un client che ha
                   letto §5.5. E il difetto è **muto** se client e server sono scritti dalla
                   stessa mano, che è il caso di §0.
                   ⚠ **Il punto attivo non ha intervallo.** `attivo_x`/`attivo_y` sono `i16`
                   e §7.2 dice «può essere negativo», senza limiti. `attivo_x = -32768` su un
                   cursore 32×32 è legale secondo ogni riga del documento. §3 punisce «un
                   campo fuori intervallo», ma qui l'intervallo non è stato scritto: non c'è
                   niente da punire, e due client disegnano il puntatore in due posti diversi
                   dello schermo.
MARCA:             [R]
```

---

## R1.22 — Lo stream di input si apre «all'attacco»: quando esattamente?

```
DOVE:              §2.5 riga 221 («**uno solo**, aperto all'attacco e tenuto aperto»)
COSA CONTRADDICE:  §1 riga 101 («⛔ **L'ordine dei cinque passi non ammette permute.** Un
                   messaggio che arriva in uno stato in cui non è previsto è
                   `ERRORE_PROTOCOLLO`») e §3 riga 250 («un messaggio arrivato nello stato
                   sbagliato della macchina»). La macchina a stati è dichiarata rigida e i
                   suoi stati non sono elencati per gli **stream**, solo per i messaggi.
COME SI DIMOSTRA:  «All'attacco» ammette due istanti:
                   A) subito **dopo aver spedito `ATTACCA`** — il client apre lo stream di
                      input e ci mette dentro il primo `PUNTATORE` appena l'utente muove il
                      dito;
                   B) solo **dopo aver ricevuto `SESSIONE`** — che è l'unico momento in cui
                      il client conosce la **tela concessa**, e §7.3 riga 909 impone che le
                      coordinate siano sulla tela.
                   Con A, il server riceve uno stream unidirezionale con byte alto `0x01`
                   mentre è ancora nello stato «ATTACCA in lavorazione»: secondo §1 riga 101
                   è un messaggio in uno stato non previsto, quindi `ERRORE_PROTOCOLLO` e
                   sessione caduta. Con B, un client scritto secondo A funziona contro un
                   server tollerante e cade contro uno rigoroso — e siccome §11 riga 1055
                   prova il rigore («la connessione deve cadere ogni volta»), il server
                   rigoroso è quello conforme.
                   ⚠ E la lista degli stati leciti manca anche per: `VISTA` e
                   `DISPOSIZIONE` prima di `ATTACCA`; `RICHIEDI_CHIAVE` prima di `SESSIONE`;
                   qualunque messaggio **dopo** aver spedito `CONGEDO`. §1 riga 103 promette
                   che qui, a differenza della trappola 1 di `LEZIONI.md` §4, «lo dice» —
                   ma lo dice per i cinque messaggi del disegno, non per gli altri diciassette
                   né per gli stream.
MARCA:             [R]
```

---

## R1.23 — Una tela legale può produrre un fotogramma illegale, e nessuna regola vincola chi lo spedisce

```
DOVE:              §6.2 riga 723 («un fotogramma NON DEVE superare **16 MiB**. Chi ne riceve
                   uno più lungo chiude con `ERRORE_PROTOCOLLO`») contro §4.5 riga 498
COSA CONTRADDICE:  §4.5 riga 498, che dichiara legale una tela fino a **7680×4320**; e
                   `SPECIFICHE.md` §8.2 / invariante **I1** («mai staccare»).
COME SI DIMOSTRA:  La tela 7680×4320 è esplicitamente legale (§4.5) e la profondità 10 bit è
                   il desiderato (`SPECIFICHE.md` §3.1). Un fotogramma **chiave** di una
                   scena complessa a quella misura è 33 milioni di pixel: bastano ~4 bit per
                   pixel perché superi 16 MiB. Un fotogramma chiave a qualità alta li supera.
                   A quel punto §6.2 ordina al **ricevente** di chiudere la connessione —
                   cioè il client stacca la sessione perché il server ha fatto una cosa che
                   §4.5 gli permette. E siccome §5.2 riga 601 vieta di abbandonare le chiavi,
                   il server non ha nemmeno la via d'uscita dell'abbandono.
                   La riga che manca è quella che vincola **chi spedisce**: «il server NON
                   DEVE produrre un fotogramma più lungo di 16 MiB, e se ci arriva DEVE
                   [ricodificare / calare la qualità / dichiararlo nel registro]». Senza,
                   il tetto è solo una punizione per il ricevente.
                   `[?]` **La misura che chiude il cerchio, e non la faccio io**: quanto pesa
                   davvero una chiave 7680×4320 HEVC Main10 alla qualità che il prodotto
                   punta. Se sta sotto i 16 MiB in ogni scena, resta comunque il difetto di
                   forma (nessun vincolo sul mittente); se non ci sta, è una sessione che
                   cade da sola sul ferro migliore.
MARCA:             [?]
```

---

## R1.24 — La versione nel percorso e la versione in `CIAO` possono dire due cose diverse

```
DOVE:              §2.2 riga 149 e riga 157, contro §9 riga 1006
COSA CONTRADDICE:  §2.2 riga 158 dichiara che «il percorso non lo sostituisce», ma non dice
                   che i due devono **coincidere**; e §9 riga 1006 fa scegliere al server
                   senza guardare il percorso.
COME SI DIMOSTRA:  Un giorno esisterà RCP/2. Un client apre la sessione su
                   `https://host:7447/**rcp/1**` (perché è l'indirizzo che l'utente ha
                   scritto a mano, caso che §2.2 riga 159 prevede esplicitamente) e manda
                   `CIAO(versione=**2**)`.
                   §9 riga 1006: «il server sceglie la versione più alta che sa parlare e che
                   non superi quella del `CIAO`» → sceglie **2**, risponde `ECCOMI(2)`, e da
                   quel momento parla RCP/2 su un percorso che dichiara RCP/1.
                   L'altra lettura, altrettanto difendibile: la versione del percorso è
                   vincolante e un `CIAO(2)` su `/rcp/1` è `ERRORE_PROTOCOLLO` o
                   `VERSIONE_INCOMPATIBILE`.
                   Tre esiti possibili (`ECCOMI(2)`, `ERRORE_PROTOCOLLO`,
                   `VERSIONE_INCOMPATIBILE`) e il documento non dice quale. La finestra per
                   scriverlo è la stessa di §9 riga 1020: **adesso**, perché il giorno in cui
                   serve non si può più.
                   ⚠ Sulla stessa riga: §2.2 riga 152 dice di rifiutare un percorso
                   sconosciuto «con **lo stato HTTP di rifiuto**» senza dire quale. 404 e 400
                   e 421 sono tutti difendibili, e la pagina non li distingue.
MARCA:             [R]
```

---

## R1.25 — §4.1 tiene aperta una `[?]` che il riquadro in cima alla stessa sezione ha già chiuso

```
DOVE:              §4.1 righe 319-323, contro §4.1 righe 293-303 e §4.1-bis riga 327
COSA CONTRADDICE:  `SPECIFICHE.md` riga 672 (l'obbligo di aggiornare nello stesso momento) e
                   `LEZIONI.md` §2.6 («l'utente non è il banco»: una `[?]` costa un
                   intervento).
COME SI DIMOSTRA:  Il riquadro che apre §4.1 dichiara, con marca `[R]` e citando S1:
                   «l'eccezione dell'utente non la copre né su Chrome né su Firefox».
                   Trentacinque righe più sotto, la stessa sezione chiede: «`[?]` **La misura
                   che decide la forma del predefinito** […] l'eccezione che l'utente concede
                   sul caricamento della pagina **copre anche la sessione WebTransport**? […]
                   È la prima domanda della sonda del browser».
                   La domanda è già risposta per due motori su tre, e §4.1-bis riga 327 ha già
                   preso la decisione che quella `[?]` doveva informare
                   («promossa da rete di sicurezza a **strada principale**»).
                   Che cosa costa: chi legge §4.1 in ordine trova una misura da fare che è
                   già fatta, e chi pianifica la sonda del browser la mette in cima. Resta
                   aperta **solo** la riga di Safari, che §4.1-bis riga 337 già dichiara come
                   `[?]` nel posto giusto.
                   ⚠ La stessa `[?]` è ancora viva anche in `SPECIFICHE.md` §13
                   («l'eccezione del certificato copre WebTransport?»), con la stessa
                   formulazione generale.
MARCA:             [R]
```

---

## R1.26 — Il segno della rotella: evdev per i tasti, `wl_pointer` per la rotella, e i due non concordano

```
DOVE:              §7.3 riga 905
COSA CONTRADDICE:  §7.3 riga 904, che nella riga precedente fissa la convenzione su **evdev**
                   con la ragione «`libei` […] lavora in evdev, e ogni altra convenzione
                   aggiungerebbe una tabella di traduzione che sbaglia in silenzio».
COME SI DIMOSTRA:  §7.3 riga 905 dice due cose insieme: «unità da **120 per scatto**,
                   **positive verso l'alto e verso sinistra**. È l'unità di
                   `wl_pointer.axis_value120`, quindi **non si converte niente**».
                   Le due metà citano due convenzioni con segni opposti: in evdev
                   `REL_WHEEL`/`REL_WHEEL_HI_RES` è positivo **verso l'alto** e
                   `REL_HWHEEL` è positivo **verso destra**; in `wl_pointer` il valore
                   dell'asse è positivo nel verso in cui **scorre il contenuto**, cioè verso
                   il basso. Almeno una delle due metà della riga è sbagliata, e
                   l'orizzontale («positive verso **sinistra**») non corrisponde a nessuna
                   delle due.
                   Il caso concreto: il client manda `ROTELLA(asse_x=0, asse_y=+120)`
                   perché l'utente ha girato la rotella in su. Il server che ha creduto alla
                   prima metà inietta `REL_WHEEL_HI_RES=+120` e la pagina sale; quello che ha
                   creduto alla seconda inietta `-120` e la pagina scende. **Nessuno dei due
                   ha sbagliato a leggere.**
                   ⚠ E il precedente è in casa: `LEZIONI.md` §2.3 riga 319 racconta il banco
                   della rotella che dava rosso sul codice giusto, e `DECISIONI.md` §1.5 riga
                   20 dice che «in v1 quella tabella è costata il banco della rotella».
                   `[?]` Va misurata, non decisa a tavolino: si inietta con `libei` e si
                   guarda da che parte va la pagina. È la misura più corta di tutto questo
                   rapporto.
MARCA:             [?]
```

---

## R1.27 — L'`istante` dell'input: nessuno lo consuma, e un browser non lo sa produrre

```
DOVE:              §7.3 riga 893 (`u64 istante`, microsecondi dell'orologio monotono del
                   CLIENT)
COSA CONTRADDICE:  §6.2 riga 741 («`istante` non è un'ora […] Il client **NON DEVE**
                   confrontarlo con il proprio: solo con altri `istante` dello stesso
                   server») — la regola simmetrica dal lato del server non è scritta, e
                   nessuna riga del documento dice che cosa il server debba farne.
COME SI DIMOSTRA:  Sono 8 byte su ogni messaggio di input — su un trascinamento a 100 eventi
                   al secondo, 800 byte al secondo — di un campo che **nessuna regola
                   consuma**. Il ritardo lo misura il banco ad anello chiuso di
                   `DECISIONI.md` §2.6, e il campo `input` del fotogramma (§6.2 riga 721)
                   porta l'`id`, non l'`istante`.
                   E il client non lo sa produrre come è scritto: in una pagina l'orologio
                   monotono è `performance.now()`, che è in **millisecondi** e la cui
                   risoluzione è deliberatamente ingrossata dai browser per motivi di
                   privacy. Due implementazioni: una scrive `ms × 1000` (microsecondi finti,
                   sempre multipli di mille), l'altra scrive il valore più fine che il motore
                   concede. I byte sono diversi, nessuno se ne accorge, e se un giorno
                   qualcuno usasse quel campo per una misura la userebbe su un numero
                   arrotondato senza saperlo — che è `LEZIONI.md` §1.9 applicata a un campo
                   di protocollo.
MARCA:             [R]
```

---

## R1.28 — `CREDENZIALI`: utente e parola vuoti sono legali

```
DOVE:              §4.4 righe 423-426
COSA CONTRADDICE:  §4.3 riga 400, che per le capacità dichiara: «⛔ un valore **vuoto** è
                   `ERRORE_PROTOCOLLO`: chi non ha niente da dire non manda la capacità».
                   La stessa cura non è applicata al messaggio che porta la password.
COME SI DIMOSTRA:  §6.0 riga 667 dichiara legale la stringa vuota (`lunghezza = 0`). Un
                   client manda `CREDENZIALI` con utente di 0 byte e parola di 0 byte:
                   tipo=0x0003 · lunghezza=4 · 00 00 · 00 00. Nessuna riga lo vieta.
                   Lettura A: si passa a PAM, che risponde di no, e si consuma un tentativo
                   del limitatore di §4.4-bis. Lettura B: è `ERRORE_PROTOCOLLO` e la
                   connessione cade **senza** consumare un tentativo.
                   La differenza non è estetica: sotto la lettura B un attaccante che manda
                   credenziali vuote non incrementa **nessuno dei due contatori** di
                   §4.4-bis, perché la connessione muore prima; sotto la lettura A sì. Due
                   implementazioni con due profili di robustezza diversi, e il documento non
                   sceglie.
                   ⚠ Nella stessa famiglia: i tetti «≤ 256 byte» e «≤ 1024 byte» di §4.4 non
                   dicono che cosa fare a chi li supera. §3 dice «un campo fuori intervallo»
                   → `ERRORE_PROTOCOLLO`; ma §6.1 riga 686 dice «una lunghezza incoerente
                   con quel che il tipo prevede» → anche lì `ERRORE_PROTOCOLLO`. Qui i due
                   convergono, ed è l'unico punto di questa famiglia dove convergono.
MARCA:             [R]
```

---

## R1.29 — Il censimento dichiara 22 corpi definiti su 22, e sono 24

```
DOVE:              §0-bis riga 39 («corpi di messaggio definiti byte per byte | Prima 2 su 22
                   | Adesso **22 su 22**») e `DECISIONI.md` §1.5 riga 215
COSA CONTRADDICE:  §7.1 (14 tipi) + §7.3 (5) + §7.4 (3) = **22 messaggi**, ai quali §6.2 e
                   §6.3 aggiungono il fotogramma e il datagram audio = **24 corpi**.
COME SI DIMOSTRA:  Il conto della prima stesura torna: 12 di controllo + 5 di input + 3 di
                   appunti = 20 «con il solo nome», più fotogramma e datagram audio già
                   definiti = 22 corpi in tutto, 2 su 22. ✔
                   Poi §0-bis riga 53 e §9 riga 1021 dichiarano di aver **aggiunto due tipi**
                   (`RICHIEDI_CHIAVE`, `TELA`). Il totale diventa 24, e la casella «Adesso»
                   dovrebbe dire **24 su 24**.
                   Perché non è pedanteria: quella tabella è **la prova che il documento porta
                   di essere completo**, ed è l'unica. Chi vuole verificarla conta i corpi e
                   ne trova 24, cioè due più di quelli dichiarati: o il documento ha
                   dimenticato di contare qualcosa, o ha contato male. In tutti e due i casi
                   la verifica va rifatta a mano, e il censimento perde il suo mestiere.
MARCA:             [R]
```

---

# §A. Che cosa ho provato a rompere senza riuscirci

⛔ *Questa sezione non assolve niente* (`REVIEWER.md` §0): dice solo dove ho cercato e non ho
trovato. Vale quanto i rilievi perché è la parte che dice **dove non rifare la stessa caccia**.

| Che cosa ho attaccato | Come | Esito |
|---|---|---|
| **L'aritmetica del tetto degli appunti** (§5.4 vs §6.1) | ho costruito il messaggio massimo: 6 byte di inquadratura + 4 di lunghezza + 1 000 000 = 1 000 010 byte, contro il tetto di 1 MiB = 1 048 576 | **regge**, e regge anche il caso limite che la riga dichiara di voler proteggere (il testo grande **esattamente** quanto il tetto). Non ho trovato niente |
| **Il cursore contro il tetto del messaggio** | 256×256×4 + 8 + 6 = 262 158 byte contro 1 MiB | **regge**. Non ho trovato niente |
| **La mappa dei canali di §2.5** | ho cercato un tipo di §7 il cui byte alto contraddicesse la tabella, e un valore fuori dai cinque | i 22 tipi stanno tutti nel canale che la tabella gli assegna; `0x0301`/`0x0302` e `0x0401` pure. **Non ho trovato niente** |
| **Il giro del contatore dei fotogrammi** | 2³² ÷ 60 fps = 71 582 788 s = 828 giorni = 2 anni e 3 mesi, contro «due anni e due mesi» dichiarato in §6.2 riga 732 | il numero è giusto, per difetto. **Non ho trovato niente** |
| **Il conto dei motivi di congedo** | §8.2 elenca 0x01…0x0E senza salti né doppioni = 14, e §11 dice «quattordici» | il conto torna (il difetto che ho trovato è **quali** dei quattordici sono raggiungibili, R1.18, non quanti) |
| **La sovrapposizione fra `RESPINTO` e `CONGEDO`** | è la contraddizione che §4.4 riga 447 dichiara di aver chiuso il 9 agosto | **è chiusa davvero** per `CREDENZIALI_ERRATE`: la riga «`RESPINTO` è il congedo dell'autenticazione […] e NON DEVE mandare anche `CONGEDO`» non ammette due letture. Resta aperta per `TROPPI_TENTATIVI` (R1.13) |
| **`AMMESSO` con corpo vuoto** | ho cercato se «corpo vuoto» fosse ambiguo fra «lunghezza = 0» e «nessun campo lunghezza» | §6.1 non ammette messaggi senza inquadratura: `lunghezza = 0` è l'unica lettura. Lo stesso per `APPUNTI_CHIEDI`. **Non ho trovato niente** |
| **L'ordine dei byte** | ho cercato un secondo posto, oltre al PCM di §5.3, dove il documento cambi ordine senza dirlo | l'eccezione del little-endian è dichiarata una volta e non se ne nasconde una seconda. **Non ho trovato niente** |
| **L'allineamento delle strutture** | ho ricontato l'intestazione del fotogramma campo per campo: 2+2+4+4+4+8+4 = **28** ✔, e il datagram: 2+2+8 = **12** ✔ | i due offset dichiarati sono esatti, riempimenti inclusi (cioè: nessuno). **Non ho trovato niente** — ed è la correzione del 9 agosto che regge |
| **La regola di crescita di §9** | ho cercato un posto dove RCP/1 crescesse aggiungendo un campo invece che una capacità | non ce n'è. I due tipi aggiunti il 9 agosto sono dichiarati sotto la clausola «oggi non esiste nessuna implementazione». **Non ho trovato niente** |
| **`video.misura_massima` contro la tela concessa** | ho cercato una combinazione in cui il server non possa concedere niente di legale | con `misura_massima` ≥ 320×240 c'è sempre una tela pari e legale da concedere. Il caso patologico (`misura_massima` dichiarata sotto 320×240) esiste ma è coperto: la tela chiesta sarebbe già illegale in `ATTACCA`. **Non ho trovato niente** |
| **L'invariante I5 (il volume)** | ho cercato in RCP un campo o un messaggio che portasse il volume | non c'è, ed è dichiarato in §5.3 riga 633 e §10. **Non ho trovato niente** |
| **L'invariante I4 (il palco appartiene alla sessione)** | ho cercato una riga di RCP che legasse il palco alla connessione | `SESSIONE(stato=RIPRESA)` esiste apposta, e nessuna riga smonta niente alla chiusura. **Non ho trovato niente** — ma vedi R1.3, che è il buco accanto: la sessione sopravvive e non c'è modo di dire a chi la teneva che gli è stata presa |

---

# §B. Le linee di caccia, e che cosa ha dato ciascuna

| Linea | Esito |
|---|---|
| 1 · Ambiguità di codifica | R1.6, R1.7, R1.11, R1.12, R1.16, R1.20, R1.21, R1.27, R1.28 |
| 2 · Coerenza dei limiti | R1.1, R1.17, R1.23; e i tre casi di §A dove i tetti tornano |
| 3 · La quarta eccezione a §3 | trovate **due**: R1.10 (`ADATTA_TELA` fuori limiti) e R1.15 (`RICHIEDI_CHIAVE` ignorabile), più due tolleranze minori citate dentro (R1.9, R1.15 in coda) |
| 4 · I resti della stesura a QUIC nudo | R1.4, R1.5, R1.8, R1.14, R1.19 |
| 5 · Le macchine a stati e i tempi | R1.8 (i tempi si contraddicono), R1.22 (gli stati degli stream non sono scritti) |
| 6 · Il rapporto con gli altri documenti | R1.3 (rende impossibile `SPECIFICHE.md` §5.3 e I2), R1.14, R1.25 |
| 7 · Il collaudo di §11 | R1.18 — e non è una regola sola: sono quattro famiglie |
| 8 · I **DEVE** irrispettabili | R1.4, R1.5, R1.11 (la regola senza identificatore), R1.17, R1.20 (il tipo MIME senza campo) |

---

# §C. Che cosa passa al coder e in quale ordine

⛔ **Non ho corretto niente** (`REVIEWER.md` §5): nessun file del progetto è stato toccato da
questa revisione, all'infuori di questo rapporto.

**Prima di scrivere il primo byte** — perché §9 chiude la finestra al primo byte e questi tre
cambiano i **byte sul filo** o i **tipi**: R1.1 (l'audio PCM), R1.3 (il motivo che manca), R1.11
(l'identificatore di trasferimento degli appunti).

**Prima di scrivere la fase 1** — perché sono la stretta di mano e la fiducia: R1.2, R1.4, R1.5,
R1.8, R1.12, R1.13, R1.14, R1.25.

**Le tre `[?]` da misurare, non da decidere**: R1.23 (quanto pesa una chiave 8K), R1.26 (da che
parte gira la rotella con `libei`), e la coda di R1.1 (quanto è davvero il tetto di un datagram su
ciascun motore — la sonda del browser lo può chiedere in una riga).
