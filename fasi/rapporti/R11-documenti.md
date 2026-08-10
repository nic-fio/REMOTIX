# R11 — I documenti contro le misure

*Revisione avversariale del 10 agosto 2026, terzo momento di `PIANO.md` §0.4. Area: `README.md`,
`RCP.md`, `DECISIONI.md`, `fasi/01-filo-nudo.md`, `LEZIONI.md`, contro `banchi/b2-esiti.jsonl` e
contro il codice dei banchi.*

⛔ **Letti prima di scrivere un rilievo**: `REVIEWER.md` per intero e
`fasi/rapporti/MANDATO-10-agosto.md` per intero, con la **rettifica** del coordinatore ai punti 1 e
2 del §3 del mandato (`--togli` fa una rimozione **parziale** e la **dichiara**; 972/618 e 482/333
non sono confrontabili perché il primo è con due innesti e il secondo con uno).

⚠ **Questa non è una revisione verde.** I difetti già noti del mandato §3 non sono riscoperti qui:
dove compaiono, è perché un documento dice **il contrario** di quel che il mandato dichiara, o
perché ne condivide la forma in un altro punto.

⚠ **Il perimetro della prova documentale.** `banchi/b2-esiti.jsonl` è l'**unico** file di esiti del
progetto (`find . -name '*.jsonl'`), e vi scrivono **tre** programmi soltanto —
`01-b2-raccogli.py`, `01-b2-lancia-sonda.sh`, `01-b11-lancia.sh` (`grep -l b2-esiti banchi/*`).
Contiene **B2 col browser** e **B11**, e `grep -c 'B3\|B4\|B5'` dà **0**. Ogni numero di B3, B4, B5,
B10 e delle sei proprietà del trasporto vive **solo come prosa**: non è un rilievo di per sé, ma è
la condizione che rende verificabile solo una parte di quel che segue, e va detta prima.

---

# I rilievi `[R]`

---

## R11.1 — Il numero del collante nel README è di un'altra misura, e il «333» è di un'altra candidata

```
DOVE:              README.md righe 23, 89, 97
COSA CONTRADDICE:  DECISIONI.md riga 1892 e fasi/01-filo-nudo.md riga 601, che portano lo
                   stesso [M] dello stesso giorno con altri numeri
COME SI DIMOSTRA:  README.md:23 — «lo strato WebTransport su ngtcp2+nghttp3: 482 righe
                   aggiunte, di cui 333 di codice, misurate con git diff e non stimate».
                   DECISIONI.md:1892 — «456 aggiunte in 4 file — di cui 329 di codice, 85 di
                   commento, 42 vuote».  fasi/01-filo-nudo.md:601 — «ngtcp2: 456 righe
                   aggiunte, di cui 329 di CODICE [M], in 4 file».
                   ⛔ Il conto di DECISIONI torna da sé: 329 + 85 + 42 = 456.  Quello del
                   README non torna con nessuna scomposizione dichiarata da nessuna parte.
                   ⛔ E il 333 ha un padrone: è il collante di **lsquic**, la candidata
                   eliminata — DECISIONI.md:1744 «banchi/01-b2-lsquic-wt.c, 333 righe, di cui
                   236 di codice» e fasi/01-filo-nudo.md:245 «lsquic ... e il collante
                   scritto (333 righe) [M]».  Il README attribuisce a ngtcp2 il numero della
                   candidata che ngtcp2 ha battuto.
                   ⛔ E l'errore si propaga: README.md:97 dice «le 333 righe includono la
                   riscrittura del frame SETTINGS di nghttp3», mentre DECISIONI.md:1612 dice
                   «quelle 329 righe includono la riscrittura del frame SETTINGS».
                   ⚠ La riga 23 sta sotto il titolo «Che cosa è misurato [M]»: è il posto in
                   cui un numero non misurato pesa di più.
MARCA:             [R]
```

---

## R11.2 — La cura scritta oggi in `RCP.md` §9 rimanda tre volte a una sezione che non contiene la regola

```
DOVE:              RCP.md righe 1393, 1400, 1410 (e, di riflesso, README.md riga 37 e
                   fasi/01-filo-nudo.md riga 615)
COSA CONTRADDICE:  RCP.md §2.2, righe 145-172, dove la regola vive davvero; e
                   web/rapporti/R1-revisione-rcp.md riga 769, che la colloca per numero
COME SI DIMOSTRA:  Le sette parole aggiunte il 10 agosto sono «⛔ fra quelle che il percorso
                   ammette (§2.4)» (RCP.md:1393), e il riquadro che le motiva dice «§2.4 dice
                   che un CIAO(versione=2) su /rcp/1 è VERSIONE_INCOMPATIBILE» (1400) e
                   «⭐ Vince §2.4» (1410).
                   ⛔ **§2.4 è «La porta»** (RCP.md:211): 7447, TCP e UDP, la nota su Alt-Svc,
                   la [?] sulla registrazione IANA.  Non nomina né i percorsi né le versioni.
                   La regola sta in **§2.2** (righe 152, 154-166): «l'indirizzo della
                   sessione ... il numero dopo la barra è la versione maggiore», «Il server
                   NON DEVE accettare una sessione WebTransport su un percorso diverso», «E le
                   due DEVONO coincidere: un CIAO(versione=2) su /rcp/1 è
                   VERSIONE_INCOMPATIBILE».
                   ⛔ E lo dice il documento stesso due righe sotto, alla 167: «Le due righe
                   qui sopra sono della sera del 9 agosto 2026, rilievo R1.24» — dentro §2.2.
                   Il rilievo originale è ancora più esplicito:
                   web/rapporti/R1-revisione-rcp.md:769 «DOVE: §2.2 riga 149 e riga 157,
                   contro §9 riga 1006».
                   ⚠ Il caso concreto: chi scrive il server legge §9, va a §2.4 come gli si
                   dice, trova la porta, non trova nessun vincolo, e torna a §9 — cioè
                   ricostruisce **esattamente** la lettura che ha prodotto `banchi/rcp/rcp.c`
                   nella sua prima stesura, quella che «accettava un CIAO(2) e rispondeva
                   ECCOMI(1)» (RCP.md:1407).  La cura di una contraddizione fra due sezioni,
                   scritta perché «chi legge solo una delle due trova l'altra» (1411), manda a
                   una terza.
MARCA:             [R]
```

---

## R11.3 — La terza connessione di B3 è dichiarata «passa» contro un esito registrato che dice che lo stream non ha funzionato

```
DOVE:              README.md riga 32; fasi/01-filo-nudo.md riga 607
COSA CONTRADDICE:  banchi/b2-esiti.jsonl righe 12-13 (i due esiti con l'impronta nuova) e
                   fasi/01-filo-nudo.md riga 252, che è il criterio di B2
COME SI DIMOSTRA:  Il criterio, scritto nello stesso documento (01-filo-nudo:252): «passa | la
                   sessione si apre su Chrome e Firefox, **e la pagina riceve un byte dal
                   server**».
                   Gli esiti del giro col certificato ruotato (impronta `5o99/7rSTJER…`,
                   2026-08-10T09:36:16 e 09:36:32) dicono:
                     Firefox 140 — «⭐ SESSIONE APERTA in 149.0 ms / ⚠ sessione aperta ma lo
                       stream non ha funzionato: WebTransportError: remote WebTransport close»
                     Chrome 151  — «⭐ SESSIONE APERTA in 180.0 ms / ⚠ sessione aperta ma lo
                       stream non ha funzionato: WebTransportError: The session is closed.»
                   ⛔ Tutti gli altri esiti `APERTA` del file (righe 2-11) portano invece
                   «andata e ritorno su stream: "ciao" / ✅ i byte tornano identici».  I due
                   del giro ruotato sono gli **unici** in cui la seconda metà del criterio non
                   è soddisfatta, e sono proprio quelli su cui i documenti dicono «⭐ passa
                   [M]» (01-filo-nudo:607) e «la pagina ritira l'impronta corrente e apre»
                   (README:32).
                   ⚠ E la seconda metà del rilievo, sullo stesso giro: i documenti
                   attribuiscono il rifiuto con l'impronta **vecchia** al confronto
                   dell'impronta — 01-filo-nudo:607 «impronta vecchia ⇒ rifiutata da tutt'e
                   due (WebTransport connection rejected).  Il browser **confronta** davvero».
                   Gli esiti (righe 14-15) dichiarano di loro che quella conclusione non è
                   disponibile: «⚠ tre cause con lo stesso aspetto, e vanno distinte a mano:
                   1. UDP filtrato  2. l'impronta non è quella del certificato servito
                   3. il certificato della sessione supera i 14 giorni».  È la forma **E1**
                   del catalogo di REVIEWER.md §2, e il banco l'aveva già dichiarata.
                   ⚠ Terzo dettaglio, minore ma dello stesso segno: la frase citata come
                   comune ai due motori — «WebTransport connection rejected» — è di Firefox;
                   Chrome ha scritto «Opening handshake failed.»
MARCA:             [R]
```

---

## R11.4 — Il documento della fase dichiara ancora Chrome 9 su 12 e una riga «che non c'è ancora», mentre il README dichiara B11 chiuso

```
DOVE:              fasi/01-filo-nudo.md righe 616, 617, 1003-1007
COSA CONTRADDICE:  README.md righe 41-43 e 56-60; README.md riga 267 (la convenzione)
COME SI DIMOSTRA:  README.md:41 — «B3, B5 e adesso B11 sono chiusi.  Tredici casi su tredici
                   su TUTT'E DUE i motori».  README.md:56-60 — il difetto 4 («il posto non si
                   liberava quando a chiudere il canale era il SERVER») è dichiarato curato:
                   «ed è quello che chiude i tre casi rossi di Chrome».
                   fasi/01-filo-nudo.md:616, ultima riga di B11 nella tabella delle misure:
                   «⭐ 12 su 12 su Firefox 140 [M] ... ⛔ Su Chrome 151: 9 su 12».
                   fasi/01-filo-nudo.md:1006-1007: «⛔ Il server deve liberare il posto anche
                   quando a chiudere è lui, e **quella riga non c'è ancora**.  Firefox 140 fa
                   12 su 12; Chrome 151 9 su 12, e i tre sono questi.»
                   ⛔ Il commit che chiude B11 lo dimostra: `git show --stat e5d54f9` tocca
                   README.md, RCP.md, cinque file di banco e b2-esiti.jsonl — e **non tocca
                   fasi/01-filo-nudo.md**.  Il documento che `MANDATO-10-agosto.md` §2 elenca
                   come l'arbitro di «che cosa questa fase dichiara di aver misurato» è
                   rimasto alla sera prima.
                   ⚠ E le due righe adiacenti non concordano nemmeno fra loro sul
                   denominatore: la 616 conta su **12**, la 617 conta «9 casi su **13**
                   falliti».  Gli esiti registrati ne portano 13 (`jq '.casi|length'` sulle
                   righe di B11).
                   ⚠ Conseguenza pratica, ed è quella che il progetto ha già pagato: chi
                   riprende domani leggendo il documento della fase — come `PIANO.md` §0.1
                   prescrive — riscopre come aperto un difetto curato, e cerca una riga che
                   c'è.
MARCA:             [R]
```

---

## R11.5 — `DECISIONI.md` §6.4 dichiara quattro delle sei proprietà di B2 ancora `[?]`, e gli altri due documenti le dichiarano misurate

```
DOVE:              DECISIONI.md riga 1917
COSA CONTRADDICE:  README.md righe 24-25 e fasi/01-filo-nudo.md righe 596-597
COME SI DIMOSTRA:  DECISIONI.md:1917, dentro il riquadro «Che cosa questa misura NON dice»
                   aggiunto oggi: «⚠ due proprietà su sei | delle sei che B2 doveva verificare
                   qui, sono misurate datagram abilitati e max_idle_timeout 30 s.  Restano
                   [?]: niente 0-RTT, migrazione non disabilitata, allowPooling a false, e che
                   il banco possa cambiare il tetto d'inattività (serve a B3)».
                   README.md:24 — «le sei proprietà di B2: 6 su 6 | tetto 30 s · datagram ·
                   credito 16 stream uni · migrazione non disabilitata · niente 0-RTT ·
                   allowPooling: false».  README.md:25 e 01-filo-nudo:597 — il tetto si può
                   cambiare, «con --timeout=10s il pari legge 10 000 ms».
                   ⛔ Le tre righe sono dello **stesso giorno** e dello **stesso banco**.  Una
                   delle due è falsa, e quella che sta in `DECISIONI.md` è la sola che, per la
                   convenzione di README.md:263 («le decisioni stanno in DECISIONI.md, una
                   sola volta»), un lettore ha diritto di prendere per buona.
                   ⚠ Non è simmetrica: se vale la riga di DECISIONI, allora il divieto di
                   0-RTT di RCP.md §2.3 — quello di cui 01-filo-nudo:257 dice «il sintomo di
                   0-RTT acceso non esiste» — risulta non verificato mentre due documenti lo
                   dichiarano verificato.
MARCA:             [R]
```

---

## R11.6 — `DECISIONI.md` presenta come misura la riga che il documento della fase dichiara «non una misura»

```
DOVE:              DECISIONI.md riga 1891
COSA CONTRADDICE:  fasi/01-filo-nudo.md righe 813-822; LEZIONI.md §1.9 punto 5
COME SI DIMOSTRA:  DECISIONI.md:1891, nella tabella «Misurato» del riquadro `[M]` del 10
                   agosto: «i due parametri di §2.2 | max_idle_timeout 30 000 ms e
                   max_datagram_frame_size 65 536, **stampati dal server all'avvio**».
                   fasi/01-filo-nudo.md:815-818: «Il 10 agosto il server minimo stampava
                   all'avvio REMOTIX B2: max_idle_timeout=30000ms
                   max_datagram_frame_size=65536, e quella riga è finita nei documenti come
                   una misura di RCP.md §2.2.  ⛔ Ma è la sua configurazione, non il filo: dice
                   che cosa il server ha *chiesto* a ngtcp2, non che cosa è *arrivato* al
                   pari.»
                   ⛔ Il documento della fase dichiara quella riga come **il difetto peggiore
                   della giornata** («l'ho violato io, quel pomeriggio, su una misura mia»,
                   riga 821-822), e il documento delle decisioni la conserva come prova, con
                   la sua provenienza scritta accanto — «stampati dal server all'avvio» —
                   cioè dichiarando il denominatore falso invece di toglierlo.  È il
                   corollario della quarta regola (LEZIONI.md §1.9 punto 5, «un denominatore
                   si legge dove la cosa succede») contraddetto nel documento che lo cita.
                   ⚠ E la cura esiste ed è nello stesso file: la riga 596 di 01-filo-nudo
                   porta gli stessi due numeri **letti dal pari**.  Basta la fonte giusta.
MARCA:             [R]
```

---

## R11.7 — Il paragrafo del README su `--togli` descrive uno strumento che non è quello che sta nel deposito

```
DOVE:              README.md righe 91-95
COSA CONTRADDICE:  banchi/01-b3-rcp-innesta.py righe 667-678; banchi/01-b11-guasto.sh
                   righe 45-51
COME SI DIMOSTRA:  README.md:91-93 — «il 10 agosto 01-b3-rcp-innesta.py --togli **non ha tolto
                   niente** — ha detto di sì e ha lasciato l'innesto dov'era — quindi la
                   misura "B2 da solo" adesso non si sa prendere».
                   Il codice, 01-b3-rcp-innesta.py:667-678:
                     print("== Si rimette l'esempio com'era (resta l'innesto di B2)")
                     git checkout -- examples/CMakeLists.txt
                     for f in FILE_NOSTRI: os.remove(...)
                     print("   ⚠ i file .cc/.h toccati da B3 vanno rimessi con"
                           " 01-b2-ngtcp2-wt-innesta.py --togli e riapplicati")
                   ⛔ Toglie i file nostri, ripristina il `CMakeLists.txt`, e **dichiara a
                   schermo** l'unica cosa che non rimuove e come rimuoverla.  «Non ha tolto
                   niente» e «ha detto di sì» sono due affermazioni false sullo stesso
                   comando.
                   ⛔ E la conseguenza dichiarata è falsa a sua volta: «la misura B2 da solo
                   adesso non si sa prendere» è smentita da `ricostruisci()` in
                   01-b11-guasto.sh:47-51, che esegue esattamente la sequenza prescritta —
                   `01-b3-rcp-innesta.py --togli`, `01-b2-ngtcp2-wt-innesta.py --togli`, poi i
                   due innesti riapplicati nell'ordine.  Fermandosi al secondo comando si ha
                   l'albero con **il solo** innesto di B2, cioè la misura che il README
                   dichiara irraggiungibile.
                   ⛔ Da cui cade anche l'allarme di README.md:94-95 («quel --togli che non
                   toglie va guardato: ricostruisci in 01-b11-guasto.sh ci si appoggia per
                   rimettere il server sano»): `ricostruisci` non si appoggia a quel --togli
                   da solo, fa la coppia, ed è la coppia che lo script del B3 prescrive.
                   ⚠ E la conseguenza sul numero: essendo la misura ripetibile, R11.1 non ha
                   la giustificazione che il README le dà.  I 972/618 citati alla riga 93 sono
                   con **due** innesti e i 482/333 con **uno**: non sono lo stesso conto e non
                   si mettono in fila.
MARCA:             [R]
```

---

## R11.8 — «`CONNECTION_CLOSE`» e «la connessione QUIC» sopravvivono in tre punti alla correzione R1.4 di §3.1

```
DOVE:              RCP.md riga 560 (§4.4); RCP.md riga 1324 (§8.1); DECISIONI.md riga 247
                   (§1.5, riga 25 della tabella)
COSA CONTRADDICE:  RCP.md righe 305-317 (§3.1 punto 3 e il riquadro del rilievo R1.4)
COME SI DIMOSTRA:  §3.1, corretto la sera del 9 agosto: «3. DEVE chiudere la **sessione
                   WebTransport** con il codice d'errore applicativo pari al codice del motivo
                   di §8.2», e il riquadro: «Questa riga diceva "la connessione QUIC con
                   CONNECTION_CLOSE di tipo applicativo".  ⛔ **Una pagina non lo può fare**:
                   l'API espone la chiusura *della sessione*, con il proprio codice, non
                   quella della connessione HTTP/3 sotto».
                   §4.4 riga 559-560, non toccata: «Dopo averlo mandato il server DEVE
                   chiudere la connessione come dice §3.1 — **con lo stesso motivo nel
                   `CONNECTION_CLOSE`** — e NON DEVE mandare anche CONGEDO».
                   §8.1 riga 1324, non toccata: «Chi chiude DEVE mandare CONGEDO con un motivo
                   prima di chiudere **la connessione QUIC**, e DEVE ripetere il motivo nel
                   codice d'errore applicativo della chiusura (§3.1)».
                   DECISIONI.md:247: «il motivo del congedo viaggia anche nel codice d'errore
                   della **chiusura QUIC**».
                   ⛔ §8.1 è il paragrafo che detta l'obbligo a **chi chiude**, e chi chiude è
                   spesso la pagina: è il lato che R1.4 dichiara incapace di fare quel che
                   quella riga gli impone.  È **lo stesso ingresso con due byte diversi** — un
                   `CONNECTION_CLOSE` di trasporto contro una `CLOSE_WEBTRANSPORT_SESSION` —
                   e §4.4 lo impone proprio sul percorso `RESPINTO`, cioè quello che B11 ha
                   appena riaperto oggi (README.md:61-64).
                   ⚠ La forma è quella che R1.4 dichiara: «Un programmatore chiudeva la
                   sessione e dichiarava assolta la regola; l'altro cercava l'API della
                   connessione, non la trovava, e lasciava il punto 3 non implementato — ed
                   era conforme al testo quanto il primo».  Oggi il testo che lo consente è
                   ancora lì, in tre posti.
MARCA:             [R]
```

---

## R11.9 — «Lo stream 0» sopravvive in due punti alla correzione R1.5, e uno dei due era nominato dal rilievo

```
DOVE:              RCP.md riga 256 (§2.5); RCP.md riga 719 (§5, tabella dei canali)
COSA CONTRADDICE:  RCP.md righe 427-435 (§4.2 e il riquadro del rilievo R1.5);
                   web/rapporti/R1-revisione-rcp.md riga 159
COME SI DIMOSTRA:  §4.2, corretto: «⛔ Corretto la sera del 9 agosto 2026, rilievo R1.5: qui
                   c'era "(identificatore 0)", ed è un resto della stesura a QUIC nudo.  In
                   una connessione HTTP/3 lo stream QUIC numero 0 è già occupato ... e l'API
                   non espone nessun numero: apre uno stream e restituisce un oggetto.  Chi
                   leggeva "0" alla lettera cercava il canale di controllo dove non arriverà
                   mai».
                   §2.5 riga 256, non toccata: «`0x00` | controllo | ... **il controllo vive
                   solo sullo stream 0**».
                   §5 riga 719, non toccata: «**controllo** | **stream bidirezionale 0** | ↔ |
                   sì».
                   ⛔ E §2.5 non è un punto trovato adesso: il rilievo lo nominava.
                   web/rapporti/R1-revisione-rcp.md:159 — «DOVE: §4.2 riga 350, **§2.5 righe
                   219 e 224-232**».  La cura è stata applicata a uno dei due luoghi indicati.
                   ⚠ Il caso concreto è quello scritto da R1.5 e vale identico: chi implementa
                   §2.5 alla lettera scrive un ricevente che riconosce il canale di controllo
                   **dal numero di stream** invece che dal byte alto di `tipo`, e la diagnosi
                   che ne esce è «il client non apre il canale» mentre il client lo ha aperto.
                   ⚠ Aggravante: §2.5 è la sezione che il censimento di §0-bis presenta come
                   la cura del «buco più insidioso» — come si riconosce un canale.  Il numero
                   di stream ci è rimasto dentro come seconda risposta alla stessa domanda.
MARCA:             [R]
```

---

## R11.10 — Dentro `RCP.md` §4.4-bis, «subito» e «non prima di un secondo» valgono per lo stesso ingresso

```
DOVE:              RCP.md riga 607 contro RCP.md riga 622 (stessa sezione, stessa tabella)
COSA CONTRADDICE:  sé stessa; e fasi/01-filo-nudo.md riga 449, che l'aveva già nominata
COME SI DIMOSTRA:  RCP.md:607 — «**oltre la soglia** | ogni nuovo tentativo riceve RESPINTO
                   con motivo TROPPI_TENTATIVI — **subito**, e senza che PAM venga interrogata
                   — per una finestra che parte da 30 secondi...».
                   RCP.md:622, tre righe sotto, nella stessa tabella — «⛔ **il ritardo fisso**
                   | il server **NON DEVE** rispondere a CREDENZIALI prima che sia passato **un
                   secondo** dalla ricezione, **anche quando la risposta è AMMESSO**».
                   ⛔ Un sesto tentativo dentro la finestra è un `CREDENZIALI`: la prima riga
                   ordina di rispondere subito, la seconda vieta di rispondere prima di 1000
                   ms.  Due implementazioni scrivono il byte a t=0 e a t=1000, tutt'e due
                   conformi a una riga e in violazione dell'altra — che è la definizione di
                   difetto che RCP.md §0 si assegna («Se una riga qui è ambigua, è un difetto
                   di questo file»).
                   ⛔ E non è un caso di scuola trovato adesso: fasi/01-filo-nudo.md:449, nel
                   banco B8, lo dichiara come un rosso già previsto — «e "subito" vale un
                   secondo | il ritardo fisso vale "anche quando la risposta è AMMESSO",
                   quindi a maggior ragione sui rifiuti: chi cronometra "subito" e si aspetta
                   zero **dà rosso sul codice giusto**».  La cura è stata scritta nel banco e
                   **non nell'arbitro**, che è l'ordine sbagliato: il banco si collauda contro
                   `RCP.md` (§11), non viceversa.
                   ⚠ E il valore in gioco non è cosmetico: è la proprietà di sicurezza che
                   §4.4-bis dichiara di esistere per proteggere — il tempismo come canale.
MARCA:             [R]
```

---

## R11.11 — Il cursore nascosto non può soddisfare la regola del punto attivo, e `DECISIONI.md` ne dà una terza versione

```
DOVE:              RCP.md righe 841-842 (§5.5); DECISIONI.md riga 239 (§1.5, riga 17)
COSA CONTRADDICE:  RCP.md riga 841 contro RCP.md riga 842, nella stessa tabella; e
                   DECISIONI.md riga 239 contro tutt'e due
COME SI DIMOSTRA:  RCP.md:841 — «cursore nascosto | ⛔ `larghezza = 0` **e** `altezza = 0`,
                   tutt'e due, e nessun byte d'immagine.  Una sola delle due a zero è
                   ERRORE_PROTOCOLLO».
                   RCP.md:842 — «il punto attivo | ⛔ **DEVE** stare dentro l'immagine:
                   `0 ≤ attivo_x < larghezza`, `0 ≤ attivo_y < altezza`».
                   ⛔ Con `larghezza = 0` l'intervallo `0 ≤ attivo_x < 0` è **vuoto**: nessun
                   valore di un `i16` lo soddisfa.  Un `CURSORE_FORMA` di cursore nascosto —
                   che la riga sopra dichiara legale e obbligatorio in quella forma — viola la
                   riga sotto **sempre**, qualunque cosa il mittente ci metta.  Un ricevente
                   che applica §5.5 alla lettera chiude con ERRORE_PROTOCOLLO ogni volta che
                   il puntatore sparisce, e il sintomo («la sessione cade quando entro in un
                   campo di testo») non nomina né il cursore né la regola.
                   ⚠ È la stessa forma del trattino basso di §4.3 trovato oggi dal validatore
                   di B4 (RCP.md:480-486): una regola che vieta un caso che il documento
                   stesso definisce.
                   ⛔ E la terza lettura: DECISIONI.md:239 — «il cursore si ferma a 256×256, e
                   **`larghezza = 0` vuol dire nascosto**», senza l'altezza.  Chi implementa
                   dal documento delle decisioni manda `larghezza=0, altezza=16` come cursore
                   nascosto, e §5.5 gliela dichiara ERRORE_PROTOCOLLO.
                   ⚠ Il difetto è precisamente quello che R1.21 dichiarava di aver chiuso —
                   «Il cursore: larghezza 0 con altezza diversa da 0, e un punto attivo senza
                   intervallo» (web/rapporti/R1-revisione-rcp.md:673): l'intervallo è stato
                   aggiunto senza eccettuare il caso che la riga accanto rende obbligatorio.
MARCA:             [R]
```

---

## R11.12 — `DECISIONI.md` §1.5 fissa il PCM a 20 ms, che è il difetto più grave curato in `RCP.md` §5.3

```
DOVE:              DECISIONI.md riga 237 (§1.5, riga 15 della tabella)
COSA CONTRADDICE:  RCP.md righe 798-818 (§5.3 e il riquadro del rilievo R1.1)
COME SI DIMOSTRA:  DECISIONI.md:237 — «l'audio è **48 kHz, 2 canali, blocchi da 20 ms**, e il
                   PCM è **s16 little-endian** | "Opus, con PCM come base" non è un formato».
                   RCP.md:801 — «**PCM** | campioni s16, little-endian, ⛔ **5 ms per
                   datagram** — 480 campioni, 960 byte, che con i 12 dell'intestazione fanno
                   **972**».
                   RCP.md:803-811, il riquadro: «⛔ Corretto la sera del 9 agosto 2026 —
                   rilievo R1.1, **il più grave della revisione**.  Questa riga diceva 20 ms
                   anche per il PCM: 1920 campioni, 3840 byte, più 12 = 3852.  ⛔ Un datagram
                   QUIC non è frammentabile ... **Quindi l'audio PCM non sarebbe partito mai,
                   su nessuna rete.**»
                   ⛔ La riga di `DECISIONI.md` porta i 20 ms come proprietà de «l'audio» e
                   riserva al PCM il solo endianness: è la stessa lettura che R1.1 dichiara
                   letale, conservata nel documento che README.md:263 designa come il posto in
                   cui la decisione sta **una sola volta**.  Chi implementa da lì scrive
                   blocchi da 3852 byte, e il difetto si presenta alla fase 7 come «l'audio
                   PCM non arriva» — cioè lontano dalla riga che lo ha causato, e sul codec
                   che §4.3 usa come **controllo positivo** di Opus.
                   ⚠ Ed è la seconda volta che la stessa forma si presenta oggi: una cura
                   applicata a `RCP.md` e non al documento che la registra (vedi R11.8,
                   R11.14).
MARCA:             [R]
```

---

## R11.13 — `DECISIONI.md` §1.5 conta ancora ventidue messaggi e due tipi aggiunti, e ignora i due che hanno chiuso la finestra di §9

```
DOVE:              DECISIONI.md righe 215 e 248-251
COSA CONTRADDICE:  RCP.md riga 39 (§0-bis, la casella corretta dal rilievo R1.29) e RCP.md
                   §7.5 righe 1248-1252; RCP.md §12 riga 1540
COME SI DIMOSTRA:  DECISIONI.md:215 — «dei **ventidue** messaggi del protocollo, due erano
                   definiti byte per byte».  DECISIONI.md:248 — «⚠ E **due** tipi di messaggio
                   sono stati aggiunti (`RICHIEDI_CHIAVE`, `TELA`) più due motivi di congedo».
                   RCP.md:39 — «corpi di messaggio definiti byte per byte | 2 su 22 | **26 su
                   26** (§6, §7) — ⚠ *diceva "22 su 22", e il conto era della prima stesura: i
                   due tipi aggiunti il 9 agosto portavano il totale a 24, e i **due della
                   funzione di banco** (§7.5, la notte del 9) a **26**.  Corretto dal rilievo
                   R1.29, e non è pedanteria — quella casella è **l'unica prova che il
                   documento porta di essere completo***».
                   ⛔ `grep -n "BANCO_MARCA\|funzione di banco\|banco.marca" DECISIONI.md` non
                   restituisce **nessuna riga**.  I due tipi `0x000F` e `0x0010`, che RCP.md
                   §12:1540 dichiara entrati «sotto la clausola di §9 — "oggi non esiste
                   nessuna implementazione" — e **quella era l'ultima occasione**», non
                   compaiono in nessun punto del documento delle decisioni.
                   ⚠ Perché è un difetto e non un'omissione: RCP.md §0-bis:56 rimanda proprio
                   lì — «Le chiusure sono marcate 🔸 in `DECISIONI.md` §1.5» — e §1.5 è
                   presentato come il censimento completo («venticinque buchi tappati prima
                   della prima riga di codice»).  Un lettore che verifichi la completezza del
                   protocollo contando da §1.5, come R1.29 dichiara di aver fatto su §0-bis,
                   ne trova quattro in meno di quelli che esistono — e due di essi hanno
                   consumato una finestra che §9 dichiara irripetibile.
MARCA:             [R]
```

---

## R11.14 — `DECISIONI.md` §1.5 attribuisce ancora alla rotella di v1 la tabella di conversione che R4.15 ha tolto da `RCP.md`

```
DOVE:              DECISIONI.md riga 242 (§1.5, riga 20 della tabella)
COSA CONTRADDICE:  LEZIONI.md §2.3; RCP.md righe 1162-1167; fasi/01-filo-nudo.md righe 217 e
                   1061
COME SI DIMOSTRA:  DECISIONI.md:242 — «i codici di tasti e pulsanti sono quelli di evdev, la
                   rotella in unità da 120 | ... Ogni altra convenzione aggiunge una tabella
                   di traduzione che sbaglia in silenzio — e **in v1 quella tabella è costata
                   il banco della rotella** (`LEZIONI.md` §2.3)».
                   RCP.md:1162-1167, curato: «⚠ Il precedente che questa riga citava era
                   sbagliato, ed è stato corretto la notte del 9 agosto 2026 (rilievo R4.15):
                   diceva che "in v1 questa esatta tabella di conversione è costata il banco
                   della rotella".  `LEZIONI.md` §2.3 dice un'altra cosa — il banco della
                   rotella cercava `asse dy=-10` mentre il registro scriveva `asse dx=0
                   dy=-10`: **rosso, col codice corretto**.  È una stringa cercata male, non
                   una conversione col segno sbagliato».
                   fasi/01-filo-nudo.md:1061, sotto «Le cure fuori da questo documento»,
                   elenca la cura come **fatta**: «`RCP.md` §7.3 | attribuiva al banco della
                   rotella di v1 una tabella di conversione ... (R4.15)».
                   ⛔ La cura è stata applicata a un documento su due, e quello rimasto è
                   quello che il progetto designa come fonte unica.  Il danno è quello che
                   R4.15 dichiara con le sue parole (01-filo-nudo:217): «citando la lezione
                   sbagliata **la si perde nel punto in cui si applicherebbe**» — cioè S7, che
                   è ancora da misurare e che sta due righe sopra nella tabella delle misure.
MARCA:             [R]
```

---

## R11.15 — `RCP.md` §7.5 è registrato come decisione dell'utente, e non risulta presa dall'utente né registrata dove le decisioni stanno

```
DOVE:              fasi/01-filo-nudo.md riga 1030
COSA CONTRADDICE:  RCP.md righe 1248-1252 (§7.5, la sua provenienza); README.md righe 263-265
                   (la convenzione ✅ / 🔸 / ❓)
COME SI DIMOSTRA:  fasi/01-filo-nudo.md:1030, nella tabella «Le decisioni prodotte»:
                   «**✅** `RCP.md` §7.5 | ⭐ chiusa la notte del 9 agosto: la funzione di
                   banco — BANCO_MARCA e BANCO_ESITO — è entrata prima del primo byte, sotto
                   la clausola di §9».
                   README.md:265 definisce la marca: «✅ (**deciso dall'utente**)».
                   RCP.md:1250-1252, la provenienza dichiarata da §7.5 stessa: «*Aggiunta la
                   notte del 9 agosto 2026, **rilievo R3.4 della revisione del banco della
                   fase 1**, e prima del primo byte di codice*», e la motivazione viene da
                   `web/rapporti/S4-ritardo-disegno.md` §5.3, non da una frase dell'utente.
                   ⛔ E non c'è nessun altro posto dove verificarlo: `grep -n
                   "BANCO_MARCA\|funzione di banco\|banco.marca" DECISIONI.md` è vuoto (vedi
                   R11.13).  Le decisioni che l'utente ha davvero pronunciato — §1.6, §1.8 —
                   portano in `DECISIONI.md` la **frase virgolettata con la data**
                   (DECISIONI.md:259-261 sotto §1.6, 508-512 sotto §1.8); questa non ha né
                   frase né voce.
                   ⚠ Perché conta: §7.5 aggiunge **due tipi di messaggio** al protocollo e con
                   essi consuma la clausola di §9 («oggi non esiste nessuna implementazione»)
                   che RCP.md §12:1540 dichiara essere stata «l'ultima occasione».  Marcarla ✅
                   la rende non correggibile senza tornare dall'utente; marcata per quel che è
                   — 🔸 derivata da una revisione — resterebbe «correggibile senza
                   discussione», che è la condizione in cui la si vorrebbe se un giorno quei
                   due tipi dessero fastidio.
MARCA:             [R]
```

---

## R11.16 — `RCP.md` §4.1-bis dichiara nella stessa tabella che vale su tre motori e che Safari resta fuori

```
DOVE:              RCP.md riga 401 contro RCP.md riga 397
COSA CONTRADDICE:  fasi/01-filo-nudo.md riga 100; DECISIONI.md riga 525; README.md riga 188
COME SI DIMOSTRA:  RCP.md:397 — «⚠ e quel che i due motori NON provano | ... E **Safari resta
                   fuori per decisione** (`DECISIONI.md` §1.8)».
                   RCP.md:401, quattro righe sotto nella stessa tabella — «⭐ **e vale su tutti
                   e tre i motori** | `[R]` WebKit lo ha implementato il 2 ottobre 2025 (bug
                   300057, NetworkTransportSessionCocoa.mm) ed è spedito in **Safari 26.4**:
                   iPhone e iPad hanno **la stessa** strada degli altri due, non una da
                   salvare».
                   ⛔ «Vale su» è un'affermazione di funzionamento; il `[R]` che la sostiene è
                   la lettura di un commit.  È la forma **E1** di REVIEWER.md §2 — una
                   condizione necessaria usata come sufficiente — e il progetto la nomina già
                   per questo caso: fasi/01-filo-nudo.md:100 «finché nessuno prova su Safari,
                   *«funziona su iPhone»* è **una deduzione, non una misura**.  È la forma
                   **E5**, e il posto dove non deve comparire è la documentazione del
                   prodotto»; README.md:188 «Safari resta **servito**, non **verificato**:
                   sono due cose diverse, e la seconda non si scrive nella documentazione
                   finché nessuno l'ha misurata».
                   ⚠ `RCP.md` è l'arbitro, cioè il documento contro cui si dà torto a
                   un'implementazione: è il posto in cui la deduzione pesa più che nella
                   documentazione del prodotto.  Basta la formulazione della riga 397 — «la
                   stessa strada è **disponibile** su tutti e tre», non «vale».
MARCA:             [R]
```

---

## R11.17 — Tre `[M]` di B3 stanno nella tabella delle misure senza la data, in un capitolo che apre imponendo la data

```
DOVE:              fasi/01-filo-nudo.md righe 605, 606, 607
COSA CONTRADDICE:  fasi/01-filo-nudo.md riga 559 (l'intestazione del capitolo) e la regola
                   B0.6 alla riga 154; README.md riga 256
COME SI DIMOSTRA:  Riga 559, che apre «Le misure»: «*⛔ Con la scena, il dispositivo e la
                   **versione** dichiarati accanto a ogni numero (B0.6).*»  L'intestazione
                   della tabella (riga 577) è «| Che cosa | Atteso | Misurato | **Data** |».
                   Le righe 605, 606 e 607 hanno **tre** celle invece di quattro
                   (`awk 'NR>=577&&NR<=627{n=gsub(/\|/,"|"); if(n!=5) print NR}'`): la colonna
                   della data non esiste, e sono i tre risultati più citati di B3 — la seconda
                   connessione mentre la prima è viva, l'orologio del silenzio a 35 s, la
                   terza col certificato ruotato.
                   ⛔ Sono gli stessi tre che README.md:32 riassume come «B3: cinque giri su
                   cinque», e sono marcati `[M]`.  README.md:256 definisce `[M]` come
                   «misurato da noi, sul ferro, **con la data**».
                   ⚠ Non è formalismo in questo progetto: B0.6 esiste perché «un risultato
                   senza versione, fra sei mesi, non vale niente», e la riga 607 è quella che
                   dichiara un esito su **due browser**, cioè quella che la regola nomina per
                   prima.
MARCA:             [R]
```

---

## R11.18 — Rimandi a sezioni che non esistono

```
DOVE:              RCP.md riga 134 → `SPECIFICHE.md` §2.3
                   RCP.md righe 279, 918, 1262, 1481 → «§0» di RCP.md
COSA CONTRADDICE:  la struttura di SPECIFICHE.md e di RCP.md
COME SI DIMOSTRA:  RCP.md:134 — «porta quattro cose che questo protocollo usa deliberatamente,
                   e che vanno usate **invece** di reimplementarle (`SPECIFICHE.md` §2.3)».
                   `grep -n '^#' SPECIFICHE.md`: §2 è «I principi guida» (riga 55) e non ha
                   sottosezioni — la voce successiva è «## 3. I tre numeri» (riga 74).  Il
                   §2.3 rimandato non esiste, e la regola citata («usare QUIC invece di
                   rifarlo») non ha un indirizzo verificabile.
                   RCP.md cita **«§0»** quattro volte, sempre come l'argomento portante del
                   documento: riga 279 «siccome non c'è più un client altrui che protesti
                   (§0)», riga 918 «il difetto muto contro cui questo documento è stato
                   scritto (§0)», riga 1262 «cioè il difetto muto contro cui §0 esiste», riga
                   1481 «il difetto muto contro cui §0 è stato scritto».  La numerazione del
                   documento comincia da **§0-bis** (riga 26) e poi §1: la sezione §0 non c'è.
                   Il riquadro che quelle righe intendono citare — «⛔ Perché questo documento
                   esiste, e perché viene prima», righe 6-22 — non ha numero.
                   ⚠ Lo stesso rimando inesistente è ripetuto in fasi/01-filo-nudo.md:328
                   («il difetto muto contro cui `RCP.md` §0 è stato scritto»).
                   ⚠ Costa poco e vale: quelle quattro righe sono le uniche che portano il
                   lettore alla ragione per cui l'arbitro esiste, cioè al primo paragrafo che
                   `README.md` §«Da dove si comincia a leggere» gli chiede di aver capito.
MARCA:             [R]
```

---

## R11.19 — Il README dichiara curati 44 rilievi su 44, e il documento della fase ne tiene tre aperti per nome

```
DOVE:              README.md righe 9-10
COSA CONTRADDICE:  fasi/01-filo-nudo.md righe 15 e 1045-1047
COME SI DIMOSTRA:  README.md:9-10 — «banco scritto e revisionato prima del prodotto (**44
                   rilievi, 38 `[R]`, tutti curati**)».
                   fasi/01-filo-nudo.md:15 — «**44 rilievi: 38 `[R]`, 6 `[?]`**, nessun `[M]`».
                   REVIEWER.md §4 dà il destino delle due marche: «`[R]` — la si corregge ...
                   `[?]` — si passa al coder perché la **misuri**.  La misura chiude il
                   cerchio, non la review».
                   fasi/01-filo-nudo.md:1045-1047, sotto «Che cosa resta `[?]`», elenca per
                   numero tre dei sei: «⭐ il segno della rotella su più di un compositore |
                   **R3.25**», «⭐ l'istante da cui parte il primo tetto | **R3.27**», «⭐ la
                   pila PAM per un utente diverso dal proprietario del processo | **R3.26**».
                   ⛔ «Tutti curati» è quindi vero al massimo per i 38 `[R]`, e la riga li
                   somma ai 44.  ⚠ La forma è quella che REVIEWER.md §0 vieta al revisore e
                   che vale a maggior ragione per chi riassume: dichiarare chiuso per assenza
                   di lavoro residuo invece che per misura.
MARCA:             [R]
```

---

# I sospetti `[?]`

---

## R11.20 — `[?]` «Cinquantuno contraddizioni» e «quindici trappole» sono due conteggi che non si ritrovano

```
DOVE:              README.md riga 167; README.md righe 120-129
COSA CONTRADDICE:  web/rapporti/R1-revisione-rcp.md e R2-revisione-web.md; l'elenco che segue
                   il titolo alla riga 122
COME SI DIMOSTRA:  README.md:167 — «⛔ due revisioni avversariali | **51 contraddizioni**
                   trovate e curate prima del primo byte: i verdetti sono `web/rapporti/R1-` e
                   `R2-`».  `grep -cE '^## R1\.[0-9]+' web/rapporti/R1-revisione-rcp.md` → 29;
                   `grep -cE '^### ' web/rapporti/R2-revisione-web.md` → 17 (R1..R17).
                   Totale **46**.
                   README.md:120 — «⛔ **Quindici trappole in due giorni**».  L'elenco che
                   segue (righe 122-129) porta **undici** voci distinte, due delle quali
                   marcate «(rifatto)»: 13 occorrenze al massimo.  ⚠ Il titolo precedente
                   diceva «Dieci trappole in due sere» su otto voci: il conto non tornava
                   nemmeno prima, quindi non è una svista di oggi ma una serie.
                   ⚠ Marcato `[?]` e non `[R]` perché non escludo un criterio di conteggio
                   diverso e non scritto (per esempio i rilievi `O*` dei rapporti S, o le
                   trappole raccontate in `fasi/01-filo-nudo.md` e non elencate qui).  ⛔ Ma è
                   proprio quello il punto: un numero il cui denominatore non è scritto è
                   quel che `LEZIONI.md` §1.9 punto 4 vieta — «un conteggio senza
                   denominatore non è una misura: è una speranza con un numero davanti» — e
                   qui l'affermazione riassunta è **quanto lavoro di revisione è stato fatto**.
MARCA:             [?]  — si chiude dichiarando che cosa si conta, o correggendo i due numeri
```

---

## R11.21 — «Come si rimette in piedi il banco» elenca solo i banchi di B2, e la stessa pagina dichiara chiusi B3, B5 e B11

```
DOVE:              README.md righe 105-118
COSA CONTRADDICE:  README.md righe 41-43; fasi/01-filo-nudo.md riga 546
COME SI DIMOSTRA:  La sezione elenca quattordici file, **tutti** `01-b2-*`.  Non compaiono
                   `01-b3-lancia.sh`, `01-b3-terzo-giro.sh`, `01-b3-quarto-giro.sh`,
                   `01-b3-quinto-giro.sh`, `01-b4-lancia.py`, `01-b4-validatore.py`,
                   `01-b5-lancia.sh`, `01-b11-lancia.sh`, `01-b11-guasto.sh` — che esistono
                   tutti in `banchi/` e che producono i risultati dichiarati chiusi trenta
                   righe sopra.
                   ⚠ La regola che rende la lacuna un difetto è nello stesso progetto,
                   fasi/01-filo-nudo.md:546: «⛔ Un banco che ha bisogno di una mano **non si
                   può rifare uguale**, e rifarlo uguale è l'unico modo di sapere se una
                   misura è cambiata perché è cambiato il server».  Un banco che non è
                   nominato dove si dice come rimettere in piedi i banchi ha lo stesso destino
                   di uno che ha bisogno di una mano.
                   ⚠ Marcato `[?]` perché è omissione, non affermazione falsa: non so se la
                   sezione intenda coprire solo B2 per scelta.  Se sì, va detto nel titolo.
MARCA:             [?]
```

---

## R11.22 — Il README giustifica un difetto di B11 con un divieto che `RCP.md` §4.2 non scrive

```
DOVE:              README.md righe 56-59 (difetto 4 di B11)
COSA CONTRADDICE:  RCP.md righe 437-438 (§4.2)
COME SI DIMOSTRA:  README.md:57-58 — «Da lì in poi non arrivava più un byte che potesse
                   liberarlo, e la pagina non poteva rimediare: **§4.2 le vieta di spedire
                   dopo la fine**».
                   RCP.md:437-438, il testo di §4.2 per intero: «⛔ **In byte**: un FIN su
                   quello stream, da una qualunque delle due parti, chiude la sessione.  Chi
                   lo riceve **DEVE** considerarla finita; **NON DEVE** continuare a spedire
                   **sugli altri canali**».
                   ⛔ Il divieto è «sugli altri canali», non sul canale di controllo, e su uno
                   stream bidirezionale il FIN del server non chiude il verso della pagina: la
                   pagina **potrebbe** mandare il `CONGEDO` che §8.1 le impone.  Le due letture
                   producono byte diversi per lo stesso ingresso — un `CONGEDO(0x01)` contro
                   il silenzio — e il banco ha scelto la seconda (`b2-esiti.jsonl`, caso
                   `fin-sul-controllo`: «muta (atteso muta)»).
                   ⚠ Marcato `[?]` e non `[R]` perché non so quale delle due il progetto
                   voglia; ma è esattamente un punto in cui `RCP.md` ammette due letture, cioè
                   il materiale che fasi/01-filo-nudo.md §«Che cosa NON ha funzionato» dichiara
                   di voler raccogliere (riga 633).  ⛔ E oggi la lettura scelta è scritta in
                   `README.md` come se fosse in `RCP.md`.
MARCA:             [?]  — si chiude scrivendo in §4.2 se il FIN ricevuto chiuda anche il verso
                          di chi lo riceve, e come si concili con l'obbligo di §8.1
```

---

## R11.23 — `[?]` §8.1 impone il congedo senza condizioni, §3.1 lo condiziona, e il banco applica la seconda

```
DOVE:              RCP.md riga 1324 (§8.1) contro RCP.md righe 306-307 (§3.1 punto 2)
COSA CONTRADDICE:  fasi/01-filo-nudo.md righe 360-363
COME SI DIMOSTRA:  §8.1: «Chi chiude **DEVE** mandare `CONGEDO` con un motivo prima di
                   chiudere ... ⚠ L'unica eccezione è `RESPINTO`».
                   §3.1 punto 2: «**DEVE** mandare `CONGEDO` (§8) con il motivo, sul canale di
                   controllo, **se il canale di controllo è ancora utilizzabile**».
                   fasi/01-filo-nudo.md:360-363: «⚠ La chiusura si verifica nei tre punti di
                   §3.1 ⛔ **col secondo condizionale**: §3.1 dice "se il canale di controllo è
                   ancora utilizzabile", e un banco che pretende tutt'e tre sempre **dà rosso
                   sul codice giusto** quando la violazione arriva su uno stream
                   unidirezionale (R3.3)».
                   ⛔ §8.1 dichiara **una** eccezione «e sono tutte qui» nella sostanza, e la
                   condizione di §3.1 non è quella: un'implementazione che chiude senza
                   `CONGEDO` perché il canale è rotto è conforme a §3.1 e in violazione di
                   §8.1, e un banco scritto su §8.1 la boccia.
                   ⚠ `[?]` perché la lettura combinata è difendibile (§8.1 rimanda a §3.1 fra
                   parentesi).  ⛔ Ma è la stessa forma delle tre contraddizioni chiuse oggi —
                   due sezioni normative che non si nominano abbastanza — e il banco ha già
                   dovuto scegliere.
MARCA:             [?]  — si chiude aggiungendo a §8.1 la condizione di §3.1, o dichiarando in
                          §3.1 che il punto 2 non ammette condizioni per chi chiude di sua
                          volontà
```

---

## R11.24 — `[?]` Il controllo che dice «no» di B11 gira su un motore solo, e il README lo mette in fila con i due motori

```
DOVE:              README.md righe 41-43
COSA CONTRADDICE:  banchi/01-b11-lancia.sh righe 150-178
COME SI DIMOSTRA:  README.md:41-43 — «Tredici casi su tredici su **TUTT'E DUE i motori** —
                   Firefox 140 e Chrome 151 — più le due proprietà negative, **più il
                   controllo che dice di no**, e ⛔ il secondo testimone verde».
                   banchi/01-b11-lancia.sh:152-153, che lo dichiara di suo: «⚠ gira con **UN
                   motore solo**, e si dichiara: quel che prova è che la pagina sa dire di NO,
                   e per quello un motore basta»; la riga 177 lo lancia solo su `firefox`.
                   Gli esiti lo confermano: ogni `NON-CONFORME` con **9 guasti** — cioè il
                   controllo contro il server sano, 9 casi falliti su 13 — ha `motore`
                   **Firefox**, e nessuno ha Chrome (`ore 15:13:37 · 15:30:17 · 15:34:54 ·
                   15:42:25 · 15:46:45 · 15:51:11 · 15:54:08`). I due giri completi finali
                   sono `15:51:11` controllo → `15:51:54` Firefox → `15:52:28` Chrome, e
                   `15:54:08` controllo → `15:54:51` Firefox → `15:55:24` Chrome: **un solo
                   controllo per coppia, e sempre sullo stesso motore**.
                   ⚠ `[?]` perché la frase del README non afferma esplicitamente che il
                   controllo sia stato fatto sui due motori; ma la elenca dentro una serie
                   introdotta da «su tutt'e due i motori», che è la lettura naturale.  ⛔ E la
                   differenza conta proprio qui: i tre casi rossi di oggi vivevano **nella
                   differenza fra i due motori** (README:59-60), cioè nel punto in cui «un
                   motore basta» è la premessa che è appena stata smentita.
MARCA:             [?]  — si chiude scrivendo nel README «il controllo che dice di no, su un
                          motore» oppure eseguendolo anche sull'altro
```

---

# §A. Che cosa ho provato a rompere senza riuscirci

*Elencato perché anche questa è informazione (`MANDATO-10-agosto.md` §5 punto 3).*

| Che cosa ho provato | Che cosa ho trovato |
|---|---|
| **i numeri di B2 col browser contro gli esiti registrati** | reggono. `RCP.md` §4.1-bis dichiara 30,2 ms (Chrome 151) e 52,0 ms (Firefox 140) il 9 agosto: sono le righe 2 e 3 di `b2-esiti.jsonl`, `2026-08-09T22:47:17` e `22:49:59`, con l'impronta pubblicata e i byte che tornano. `fasi/01-filo-nudo.md`:594 dichiara 118,6 e 140,0 il 10 agosto: sono le righe 6 e 7, `07:57:13` e `07:57:14`. **Le quattro cifre combaciano al decimo** |
| **il 13 su 13 di B11 sui due motori** | regge sugli esiti finali: `15:54:51` Firefox `CONFORME` con `guasti: 0`, `15:55:24` Chrome `CONFORME` con `guasti: 0`, e i tredici casi elencati per nome nel `dettaglio` di tutt'e due, ciascuno con il suo atteso accanto. Il difetto è che il **documento della fase** non lo dice (R11.4), non che il numero sia inventato |
| **la ripetizione dichiarata dal README** *(«e ripetuto»)* | regge: le coppie `15:51:54`+`15:52:28` e `15:54:51`+`15:55:24` sono due giri completi conformi sui due motori, separati dal controllo negativo su server sano |
| **il conto dei corpi di `RCP.md` §0-bis, «26 su 26»** | torna: §7.1 ne definisce 16 (`0x0001`-`0x0010`), §7.3 cinque, §7.4 tre, §6.2 il fotogramma, §6.3 il datagram audio. Nessun messaggio nominato nel documento resta senza corpo |
| **le cinque eccezioni dichiarate a §3** | tornano e si citano a vicenda: §4.3 (capacità), §6.3 (datagram), §7.1 (secondo di grazia), §7.1 (misura fuori limiti), §5.2 con §7.4 (chiave ripetuta e appunti fuori tempo). Non ne ho trovata una sesta praticata e non dichiarata |
| **la coerenza dei byte alti di §2.5 con tutti i tipi definiti** | tiene: `0x00xx` controllo, `0x01xx` input, `0x02xx` appunti, `0x03xx` video, `0x0401` audio. Nessun tipo cade fuori dai cinque canali |
| **il tetto degli appunti contro il tetto del messaggio** | tiene, ed è deliberato: 1 000 000 byte contro 1 MiB = 1 048 576, con la ragione scritta in §5.4 |
| **i rimandi fra documenti, tutti** | ho verificato meccanicamente ogni `<file>.md §<n>` in README, RCP, DECISIONI, LEZIONI e 01-filo-nudo contro le intestazioni dei file bersaglio: **due soli** falliscono, ed è R11.18. `PIANO.md` §0.1-§0.4, `LEZIONI.md` §1.9/§2.1/§2.3/§9, `DECISIONI.md` §5.0-ter/§5-bis.8/§2.6, `web.md` §3.1 esistono tutti |
| **i file nominati nel README** | esistono tutti: i quattordici banchi elencati, i sei studi, `v1/strumenti/sshpw.py`, `web/rapporti/`. Nessun rimando a un file inesistente |
| **`DECISIONI.md` §1.8 come decisione ✅** | regge, ed è il modello: data, domanda a cui risponde, **frase virgolettata dell'utente**, e le percentuali citate marcate `[?]` perché sono una stima dell'utente e non una misura del progetto. È il metro con cui ho misurato R11.15 |
| **la promozione `[S]`→`[M]` di §4.1-bis** | è chiusa da una misura vera, su due motori indipendenti, con il banco nominato e la data. Non l'ho potuta rompere |
| **il conteggio «44 rilievi, 38 [R], 6 [?]»** | torna: `R3-revisione-banco-01.md` ne ha 28 e `R4-` 16 |

---

# §B. Le linee di caccia, e che cosa ha dato ciascuna

| Linea | Esito |
|---|---|
| `[?]` promosse a `[M]`/`[S]` senza misura | **una** trovata e grave (R11.6: una configurazione presentata come misura del filo); il verso opposto è più diffuso — misure vere che i documenti **non** hanno recepito (R11.4, R11.5) |
| `[M]` senza data e scena | R11.17 (tre righe di B3), R11.1 (un numero senza scomposizione né provenienza) |
| numeri senza riscontro nei banchi | R11.1 (482/333), R11.20 (51 e 15). ⚠ E la constatazione di perimetro in cima: B3, B4, B5 e B10 non lasciano **nessun** esito registrato |
| ✅ che l'utente non risulta aver preso | R11.15 (`RCP.md` §7.5) |
| 🔸 che decide che cosa fa il prodotto | non l'ho portata a rilievo: `RCP.md` §4.4-bis (il blocco fino a 15 minuti e il secondo fisso su ogni accesso) e §4.4 (la regola del 10 agosto su che cosa è lecito dopo `RESPINTO`) sono 🔸 e si vedono dall'utente, ma tutt'e due dichiarano la propria natura in prima riga e chiudono una `[?]` di `SPECIFICHE.md`. Lo segnalo qui e non come rilievo perché non ho una regola scritta che lo vieti |
| contraddizioni interne a `RCP.md` | **cinque**: R11.2, R11.8, R11.9, R11.10, R11.11 — più R11.16 dentro una sola tabella e R11.23 come `[?]`. ⛔ La forma dominante non è la coppia di regole opposte: è **una cura applicata in un posto solo**, con il rilievo originale che nominava anche l'altro (R11.9 in modo documentabile) |
| le tre chiusure dichiarate oggi | §4.3 (trattino basso) regge, e non ho trovato altri caratteri usati e vietati. §2.4-contro-§9 è chiusa **male** (R11.2). §4.4-contro-§8.1 è chiusa nel merito ma lascia dietro `CONNECTION_CLOSE` (R11.8) e la condizionalità (R11.23) |
| README che dichiara chiuso ciò che il mandato §3 tiene aperto | il README **dichiara** onestamente i punti 4 (rotazione automatica), 5 (`lsquic` e la bozza 02) e 3 (il registro). ⛔ Il punto 1 è dichiarato al contrario del vero (R11.7). Il punto 6 (verdetti diversi fra giri identici) non compare nel README, che dice solo «e ripetuto» |
| rimandi a sezioni o file inesistenti | R11.18, e nient'altro su cinque documenti |

---

# §C. Che cosa passa al coder, e in quale ordine

1. **R11.2** — la cura di §9 va rifatta puntando a **§2.2**, e con essa `README.md`:37 e
   `fasi/01-filo-nudo.md`:615. È l'arbitro, e oggi manda chi legge nel posto sbagliato.
2. **R11.1** e **R11.7** — il paragrafo delle righe 89-95 del README va riscritto sul comportamento
   vero di `--togli`, e il numero riportato a 456/329 o rimisurato con la coppia di `--togli` che
   `ricostruisci()` già esegue.
3. **R11.4**, **R11.5**, **R11.6** — i due documenti che sono rimasti indietro rispetto alle misure
   di stasera. `fasi/01-filo-nudo.md` è quello che `PIANO.md` §0.1 fa leggere per primo alla ripresa.
4. **R11.3** — o il terzo giro di B3 non è «passa», o il criterio di B2 va dichiarato diverso per
   quel giro, per iscritto. E l'attribuzione del rifiuto all'impronta va tolta o dimostrata con la
   distinzione che l'esito stesso pretende.
5. **R11.8, R11.9, R11.10, R11.11** — quattro righe di `RCP.md` che oggi consentono due
   implementazioni conformi e divergenti. Nessuna costa più di una frase.
6. **R11.12, R11.13, R11.14** — `DECISIONI.md` §1.5 non ha ricevuto tre cure che `RCP.md` ha
   ricevuto. Vanno rilette tutte e venticinque le righe di quella tabella contro il testo attuale
   dell'arbitro: le tre che ho trovato non ho ragione di credere che siano le sole.
7. Il resto, nell'ordine in cui sta scritto.

⛔ **E il verdetto, dichiarato come tale**: questa revisione **non è verde**. Diciannove `[R]` e
cinque `[?]` su cinque documenti, di cui cinque contraddizioni interne all'arbitro e tre cure
applicate a metà. Nessuno di questi rilievi è una prova che il resto sia giusto: è solo quel che
sono riuscito a rompere (`REVIEWER.md` §0).
