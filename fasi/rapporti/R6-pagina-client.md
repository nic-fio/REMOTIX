# R6 — la pagina, cioè il CLIENT del prodotto

*Revisione avversariale del 10 agosto 2026. Area: `banchi/01-b11-pagina.html` (566 righe), con
`banchi/01-b2-sonda.html` e `banchi/01-b2-raccogli.py` come termine di paragone.*

Arbitro: `RCP.md`, i **DEVE** e i **NON DEVE del client**. Regole di chi revisiona: `REVIEWER.md`,
in particolare §5 — *«non supplisci»* — e §0: **il verdetto è sempre «questo contraddice X»**.

⚠ **Questa revisione non è un'assoluzione di quel che non ha trovato.** Ha letto il codice, non lo ha
eseguito: ogni rilievo porta un ingresso concreto, e nessuno porta una misura.

⛔ **Il quadro, in una riga.** La pagina è scritta per **accusare il server** e applica §3 con rigore
su sette cose. Ma il rigore si ferma dove il server sbaglia in un modo che la pagina non ha
elencato: **tutto quel che §3 chiama «una lunghezza che non torna» e «un campo fuori intervallo» è
fuori dal suo raggio**, e passa. E in due punti la pagina viola essa stessa il documento con cui
giudica: manda un `CONGEDO` con il motivo **0x00** che §3.1 vieta con un ⛔ — dieci righe dopo aver
dichiarato quello stesso byte una violazione del server — e scrive **la parola d'ordine** in un file
di registro, che §4.4 vieta *«a nessun livello»*.

---

## I rilievi `[R]`

### R6.1 — la pagina si congeda con il motivo `0x00`, che §3.1 le vieta e che essa stessa punisce

```
DOVE:             01-b11-pagina.html:281  (throw new Violazione(0, …))
                  consumato in :420-422 (await rcp.chiudi(e.motivo, …)) e in :246-255
COSA CONTRADDICE: RCP.md §3.1 ultima riga — «⚠ Il codice 0 significa "chiusura senza motivo" e
                  NON DEVE essere usato: ogni chiusura ha un motivo di §8.2»;
                  RCP.md §8.1 — «chi chiude DEVE mandare CONGEDO con un motivo»;
                  e **la riga :289-291 della pagina stessa**, che davanti a un `CONGEDO(0x00)` del
                  server solleva `Violazione(ERRORE_PROTOCOLLO, "CONGEDO con motivo 0x00, che §3.1
                  vieta")`
COME SI DIMOSTRA: un server che tace. `attendi()` riceve `null` da `prossimo()`, non trova un
                  codice di chiusura, e solleva `new Violazione(0, "niente invece di ECCOMI
                  (silenzio)")`. In `gira()` il ramo `e instanceof Violazione` chiama
                  `rcp.chiudi(0, …)`, che (a) spedisce `CONGEDO` con il byte del motivo **0x00**,
                  (b) chiude la sessione WebTransport con `closeCode: 0`, (c) scrive nel proprio
                  registro `motivo 0 = ?` — perché `MOTIVO[0]` non esiste.
                  ⭐ **E non è un caso di scuola**: `MANDATO-10-agosto.md` §3 punto 6 riporta
                  `congedo:0x00 invece di 0x0b` fra i verdetti divergenti già osservati il 10
                  agosto, e questa è la sola riga del file che possa produrre quella stringa
                  (`"congedo:0x" + (0).toString(16).padStart(2,"0")`, :422).
MARCA:            [R]
```

⚠ La forma è quella di `REVIEWER.md` §5: la pagina è **indulgente con sé stessa** nel punto esatto
in cui è severa con il server. E il danno è quello che §3.1 punto 3 esiste per evitare: il motivo
viaggia nella chiusura della sessione, e quel motivo è **«nessun motivo»**.

---

### R6.2 — la parola d'ordine finisce, in esadecimale, nel file di registro e sul terminale

```
DOVE:             01-b11-pagina.html:238  (this.usciti.push(…toString(16)…))
                  stampata in :537-540, spedita al raccoglitore in :561 (`dettaglio`)
                  scritta su disco da 01-b2-raccogli.py:52-53, e stampata da :60-61
COSA CONTRADDICE: RCP.md §4.4 ultima nota — «la parola d'ordine … non deve comparire in nessun
                  registro a nessun livello — nemmeno in `traccia`»;
                  RCP.md §11.1, che è scritta **per intero** per risolvere questo problema («si
                  sostituiscono i soli byte segreti con altrettanti byte di riempimento»)
COME SI DIMOSTRA: `manda()` accoda in `usciti` l'esadecimale del **messaggio intero**, compreso
                  `CREDENZIALI = str(UTENTE) · str(PAROLA)` (:402). Basta che il confronto
                  `desktop-non-cambia-niente` dia `DIVERSI` — e dà `DIVERSI` ogni volta che uno dei
                  due giri va in errore, perché `dopoCiao()` di un giro fallito vale `""` — perché
                  le righe :538-539 stampino `kde  : 000100000…` e `gnome: …`, cioè i byte di
                  `CREDENZIALI` di tutt'e due i giri. Quelle righe entrano in `righe`, `righe`
                  entra in `dettaglio` (:561), e `01-b2-raccogli.py` le scrive in
                  `banchi/b2-esiti.jsonl` **e le stampa a terminale**.
                  Con `?parola=segreta`, in `b2-esiti.jsonl` compare `…0773656772657461…`.
MARCA:            [R]
```

---

### R6.3 — gli stream unidirezionali in arrivo e i datagram non vengono mai letti: metà di §2.5 non è applicabile

```
DOVE:             01-b11-pagina.html:148-161  (_sorveglia guarda solo incomingBidirectionalStreams)
                  — non compare mai `incomingUnidirectionalStreams`, né `wt.datagrams`
COSA CONTRADDICE: RCP.md §2.5, tabella dei byte alti: «`0x00` controllo — su uno stream
                  unidirezionale è ERRORE_PROTOCOLLO»; «`0x04` audio — ⛔ solo su datagram. Su uno
                  stream è ERRORE_PROTOCOLLO»; «⛔ Un byte alto diverso da questi cinque è
                  ERRORE_PROTOCOLLO. E un canale usato nel verso sbagliato … lo è a sua volta»;
                  RCP.md §3 — «NON DEVE ignorarlo, NON DEVE proseguire»
COME SI DIMOSTRA: il server guasto apre uno stream **unidirezionale** e ci scrive i due byte
                  `0x00 0x04` (audio su uno stream) oppure `0x00 0x01` (input, che §2.5 dà al
                  **client**) oppure `0x00 0x00` (controllo fuori dallo stream 0). La pagina non
                  ha nessun lettore su quel flusso: lo stream resta lì, nessuna `Violazione` viene
                  accodata, il caso arriva in fondo e dichiara `prosegue`. È la stessa forma che
                  `_sorveglia()` è stato scritto per togliere sui bidirezionali — e il commento
                  :142-145 la nomina: *«la pagina se ne accorge solo se STA A GUARDARE questo
                  flusso»*. Sugli unidirezionali non guarda.
MARCA:            [R]
```

⚠ Conseguenza sul banco: dei cinque canali di §2.5 la pagina ne sorveglia **uno**, e i tredici casi
non contengono nessuna violazione di verso su stream unidirezionale. Un server che sbagliasse verso
resterebbe **verde su B11**.

---

### R6.4 — la pagina decide su un cronometro fisso di 12 s, dove RCP non dà al server nessun tetto

```
DOVE:             01-b11-pagina.html:204  (async prossimo(attesa_ms = 12000))
                  usato da :267-268 per ECCOMI (:399), AMMESSO (:403) e SESSIONE (:406)
COSA CONTRADDICE: RCP.md §4.6, che fissa **tre** tetti e sono tutti sul **client** («`CIAO`
                  ricevuto», «`CREDENZIALI` ricevute», «`ATTACCA` ricevuto»): **al server non è dato
                  nessun tetto di risposta**, e §7.1/§4.5 gli impongono soltanto di rispondere
                  «mai con un silenzio». Un client che si fa un tetto proprio, e non scritto, misura
                  il proprio orologio e lo chiama violazione del server;
                  e RCP.md §3.1, perché l'esito di quel tetto è la `Violazione(0)` di R6.1
COME SI DIMOSTRA: `ATTACCA` è il messaggio con cui il server **avvia una sessione grafica** (§4.5:
                  `SESSIONE(stato=1 NUOVA)`, e §8.2 `SESSIONE_NON_SERVIBILE` = «un compositore che
                  non parte»). L'avvio di un compositore su una macchina carica supera dodici
                  secondi senza che nessuno abbia violato niente. Alla scadenza la pagina non
                  dichiara «il server è lento»: solleva `Violazione(0, "niente invece di SESSIONE
                  (silenzio)")`, spedisce `CONGEDO(0x00)` e registra `congedo:0x00`, cioè accusa il
                  server con un motivo che non esiste. ⚠ Lo stesso vale per `AMMESSO`, che §4.4-bis
                  obbliga a **ritardare di un secondo** e che passa da PAM: un PAM su LDAP lento
                  esaurisce i dodici secondi.
MARCA:            [R]
```

---

### R6.5 — un nome di capacità ripetuto due volte viene ingoiato, e vince l'ultimo

```
DOVE:             01-b11-pagina.html:337  (cap[n] = v;)
COSA CONTRADDICE: RCP.md §4.3 — «⛔ **un nome ripetuto due volte è `ERRORE_PROTOCOLLO`.** "Vince
                  l'ultimo" e "vince il primo" sono due implementazioni diverse dello stesso
                  documento, che è precisamente ciò che questo documento esiste per impedire»
COME SI DIMOSTRA: `ECCOMI` con `quante = 2` e le coppie `video.codec=hevc` e `video.codec=av1`. Il
                  ciclo :324-337 esegue `cap["video.codec"]="hevc"` e poi `cap["video.codec"]="av1"`:
                  nessun controllo di ripetizione, nessuna riga di registro, la pagina prosegue —
                  e ha implementato «vince l'ultimo», cioè **una delle due letture che §4.3 ha
                  vietato entrambe**.
MARCA:            [R]
```

---

### R6.6 — l'UTF-8 non valido si trasforma in `U+FFFD` invece di chiudere

```
DOVE:             01-b11-pagina.html:101  (new TextDecoder().decode(...))
COSA CONTRADDICE: RCP.md §6.0, riga «stringa» — «⛔ UTF-8 non valido è `ERRORE_PROTOCOLLO`»;
                  RCP.md §3 — «NON DEVE indovinare»
COME SI DIMOSTRA: `ECCOMI` con una capacità di valore `0xFF 0xFE` (lunghezza 2). `TextDecoder`
                  senza `{ fatal: true }` **non solleva**: sostituisce e restituisce `"��"`.
                  La pagina lo registra come «capacità sconosciuta ignorata» e prosegue. Lo stesso
                  su `SESSIONE.desktop` (:343) e su `CONGEDO.dettaglio` (:288). ⚠ È indovinare **e**
                  tacere: due byte illegali diventano due caratteri legali, e nessuno dei due lati
                  può più sapere che cosa era stato spedito.
MARCA:            [R]
```

---

### R6.7 — nessun corpo viene mai verificato in lunghezza: §6.1 non è applicata dal lato che riceve

```
DOVE:             01-b11-pagina.html:311-339 (leggi_eccomi), :341-353 (leggi_sessione),
                  :285-302 (CONGEDO e RESPINTO in attendi), :303-308 (AMMESSO)
COSA CONTRADDICE: RCP.md §6.1 — «⛔ `lunghezza` **DEVE** essere il numero esatto dei byte del corpo.
                  Un ricevente che legge una lunghezza incoerente con quel che il tipo prevede
                  **DEVE** chiudere con `ERRORE_PROTOCOLLO`»;
                  RCP.md §3, che elenca «una lunghezza che non torna» fra i casi che impongono la
                  chiusura;
                  e RCP.md §4.4, che dà `AMMESSO` **corpo vuoto** e `RESPINTO` **un solo `u8`**
COME SI DIMOSTRA: quattro ingressi, tutti accettati:
                  1. `AMMESSO` con 1024 byte di corpo — `attendi` guarda solo `NOME_T[m.tipo]` e
                     restituisce `m.corpo` (:303-308), che il chiamante butta (:403). Passa.
                  2. `ECCOMI` con `quante = 0` e 500 byte di coda — il ciclo non gira, `l.corto`
                     resta falso, nessuno confronta `l.i` con `corpo.length`. Passa.
                  3. `SESSIONE` con 4 byte in più dopo `desktop` — stessa cosa (:344). Passa.
                  4. ⛔ `RESPINTO` con **corpo vuoto**: `m.corpo[0]` vale `undefined`, quindi
                     `e.respinto = undefined`, quindi in `gira()` il ramo
                     `else if (e.respinto !== undefined)` (:426) **non scatta** e il caso finisce
                     nel ramo generico `errore:Error` (:446-448). Un `RESPINTO` malformato non
                     produce `ERRORE_PROTOCOLLO`: produce un esito che il banco non sa leggere.
MARCA:            [R]
```

---

### R6.8 — le regole di §4.3 sulle capacità sono applicate per una sola su sei

```
DOVE:             01-b11-pagina.html:324-338 (leggi_eccomi)
COSA CONTRADDICE: RCP.md §4.3, cinque ⛔ consecutivi che la pagina non applica:
                  «un **nome** è fatto di `a-z`, `0-9`, `.` e `_`, da 1 a 64 byte»;
                  «un **valore** è testo UTF-8 stampabile, al massimo 256 byte»;
                  «⛔ un valore **vuoto** è `ERRORE_PROTOCOLLO`»;
                  «⛔ se dopo lo scarto l'elenco resta vuoto, si congeda con `NIENTE_IN_COMUNE`»;
                  «⚠ `pcm` **DEVE** essere dichiarato da entrambi … allo stesso modo `8` **DEVE**
                  comparire in `video.profondita` di entrambi»;
                  e §4.3 «⛔ Se l'intersezione di `video.codec` è vuota, … `NIENTE_IN_COMUNE`»
COME SI DIMOSTRA: quattro `ECCOMI` che passano tutti:
                  `audio.codec=""` (valore vuoto → §4.3 lo dichiara `ERRORE_PROTOCOLLO`);
                  `VIDEO.CODEC=hevc` (nome fuori dal charset → viene solo registrato come «nome
                  sconosciuto», cioè trattato con l'eccezione che §4.3 dice di non estendergli);
                  `ECCOMI` con `quante = 0` (né `pcm` né `8`: §4.3 impone `NIENTE_IN_COMUNE`);
                  `video.codec=vp9` contro il `CIAO` della pagina che offre `hevc,av1`
                  (intersezione vuota → `NIENTE_IN_COMUNE`).
                  ⭐ **La prova che il buco è strutturale**: il motivo `0x09 NIENTE_IN_COMUNE` è
                  nella tabella `MOTIVO` a :57, e **non esiste nel file nessuna riga che lo
                  sollevi**. È un motivo che questa pagina non può emettere.
MARCA:            [R]
```

---

### R6.9 — un motivo di congedo fuori da §8.2 viene accettato, e metà dei motivi di §8.2 non ha nome

```
DOVE:             01-b11-pagina.html:56-59 (la tabella MOTIVO), :293 e :299 (MOTIVO[…] || "?")
COSA CONTRADDICE: RCP.md §3 — «un campo fuori intervallo» impone la chiusura;
                  RCP.md §8.2 — «⛔ Ogni motivo **DEVE** essere mostrabile all'utente in una frase
                  comprensibile. `BUDGET_PIENO` non è "errore 6" … ⛔ **La frase la costruisce il
                  client, dal codice**»
COME SI DIMOSTRA: due ingressi.
                  1. `CONGEDO` con motivo `0x99`, che §8.2 non definisce: la pagina lo accetta come
                     congedo legittimo e dichiara `congedato-dal-server:0x99` (:293, :425). Solo
                     `0x00` è rifiutato. Un motivo inventato non è un motivo.
                  2. `CONGEDO(0x06 BUDGET_PIENO)` — motivo **definito** da §8.2: la tabella della
                     pagina parte da `0x07`, quindi la riga di registro è `CONGEDO 6 = ?`.
                     Mancano `0x01`…`0x06` e `0x0C`, cioè **sette motivi su quindici**.
                  ⭐ E la prova sta in casa: la pagina si congeda con `0x01 CHIUSO_DALL_UTENTE`
                     (:470, :473) e `chiudi()` scrive `motivo 1 = ?` (:247) — **non sa il nome del
                     motivo che manda lei stessa**.
MARCA:            [R]
```

---

### R6.10 — `n in { … }` interroga la catena dei prototipi: nomi di capacità legali che la pagina crede di conoscere

```
DOVE:             01-b11-pagina.html:331-335
                  if (!(n in { "video.codec": 1, "video.profondita": 1, … })) reg(…)
COSA CONTRADDICE: RCP.md §3, eccezione 1 e la riga che la chiude — «⛔ **E ogni tolleranza va
                  scritta nel registro.** Una tolleranza silenziosa è indistinguibile da un
                  difetto»; e RCP.md §4.3, che dichiara legale il carattere `_` nei nomi
COME SI DIMOSTRA: l'operatore `in` risale `Object.prototype`. Con `ECCOMI` che dichiara la capacità
                  **`__proto__`** — nove byte di `a-z` e `_`, dentro il limite di 64, quindi un
                  nome **perfettamente legale secondo §4.3** — accade questo:
                  `SOLO_DEL_CLIENT.has("__proto__")` è falso;
                  `"__proto__" in { … }` è **vero**, quindi la riga di registro obbligatoria **non
                  viene scritta**: la pagina la tratta come una capacità che conosce;
                  `cap["__proto__"] = "abc"` non memorizza niente (assegnare una stringa a
                  `__proto__` è un no-op silenzioso), quindi la capacità **sparisce**.
                  Lo stesso con `constructor`, `valueOf`, `tostring`. ⚠ E il caso
                  `capacita-sconosciuta` (:361) è il caso che dovrebbe accorgersene: basta che il
                  server guasto scelga uno di questi nomi perché diventi verde **tacendo**, cioè
                  esattamente il contrario di quel che misura.
MARCA:            [R]
```

---

### R6.11 — la sessione si chiude senza aspettare che il `CONGEDO` sia partito

```
DOVE:             01-b11-pagina.html:249-254 (chiudi) e :470-473 (il congedo di fine caso)
COSA CONTRADDICE: RCP.md §3.1, che è un elenco **numerato e ordinato** — «Chi rileva la violazione,
                  **in quest'ordine**: … 2. DEVE mandare `CONGEDO` … 3. DEVE chiudere la sessione
                  WebTransport»; RCP.md §8.1 — «prima di chiudere»
COME SI DIMOSTRA: `await this.manda(...)` attende `w.write(b)`, che si risolve quando il chunk è
                  **accodato** allo stream, non quando è sul filo; la riga successiva chiama
                  `this.wt.close(...)`, che abbatte la sessione — e con essa lo stream e i byte non
                  ancora spediti. I due passi sono nello stesso turno di microtask, senza
                  `w.close()`, senza `w.ready`, senza `await` sulla chiusura dello stream.
                  ⭐ **Che la corsa esista non è un'ipotesi: sta scritta in questo file**, righe
                  123-129, dove il 10 agosto un `RESPINTO` *«spedito»* è stato *«buttato insieme
                  alla sessione che si chiudeva nello stesso volo»*. La pagina ha riconosciuto la
                  corsa nel server e l'ha lasciata in sé stessa. ⚠ E `MANDATO-10-agosto.md` §3
                  punto 6 dichiara aperto proprio questo: verdetti diversi fra giri identici, con
                  due cause curate e *«non è dimostrato che fossero le sole»*.
MARCA:            [R]
```

---

### R6.12 — un errore di trasporto viene scambiato per il FIN di §4.2, e non lascia una riga

```
DOVE:             01-b11-pagina.html:179  catch (e) { this.fine = true; this._sveglia(); }
COSA CONTRADDICE: RCP.md §4.2 — «⛔ In byte: **un FIN** su quello stream … chiude la sessione»: il
                  FIN è un fatto preciso, non «la lettura è finita in qualunque modo»;
                  RCP.md §3, ultima riga — «⛔ E ogni tolleranza va scritta nel registro»;
                  forma d'errore **E8** di `REVIEWER.md` §2 — il silenzio scambiato per zero
COME SI DIMOSTRA: il ramo `done` (:167-172) scrive «il canale di controllo si e' chiuso (FIN)»; il
                  ramo `catch` — che scatta su `RESET_STREAM`/`STOP_SENDING` sul canale di
                  controllo, o sulla caduta della sessione — pone **la stessa** `fine = true` e
                  **non scrive niente**. Ingresso: nel caso `fin-sul-controllo` (:373, atteso
                  `muta`) il server, invece del FIN, azzera lo stream di controllo. La pagina
                  produce `fatto = "muta"`, il banco stampa `OK fin-sul-controllo`, e il registro
                  del caso è vuoto: **il caso non distingue il fatto che dichiara di misurare**.
MARCA:            [R]
```

---

### R6.13 — le tre proprietà negative si giudicano dal lato che spedisce

```
DOVE:             01-b11-pagina.html:238 (usciti), :451, :513-515 (ok), :532-546 (i due confronti)
COSA CONTRADDICE: forma d'errore **E7** di `REVIEWER.md` §2 — «si verifica dal lato che invia, non
                  da quello che riceve»;
                  RCP.md §8.1 — «il congedo si verifica **dal lato che lo riceve**, mai dal registro
                  di chi lo manda»; RCP.md §11, riga «il congedo»;
                  e **il commento di questa stessa pagina**, righe 33-43: *«una proprieta' negativa
                  non si misura guardando la pagina … Un banco che le desse per buone "perche' nel
                  codice non c'e' un setInterval" proverebbe il codice di oggi, non il protocollo»*
COME SI DIMOSTRA: `usciti` è alimentato **solo** da `manda()` (:238), cioè è il registro di quel che
                  la pagina **ha deciso** di spedire, scritto *prima* di `await this.w.write(b)`:
                  è il registro del mittente, non del destinatario. Su di esso poggiano entrambe le
                  proprietà negative delle righe :532-546 (`desktop-non-cambia-niente` e
                  `nessun-battito-applicativo`). E il caso `respinto-non-riprovare` (:377), il cui
                  commento dice *«lo verifica il registro del SERVER»*, ha `ok` calcolato a :513
                  come `r.fatto === caso.atteso`, cioè **dal solo stato interno della pagina**: la
                  pagina dichiara verde una proprietà che dichiara di non poter osservare.
                  ⚠ Ingresso concreto: un battito spedito **fuori** da `manda()` — una scrittura
                  diretta su `this.w`, o su uno stream unidirezionale, che è il canale di input di
                  §2.5 — non comparirebbe in `usciti`, e `nessun-battito-applicativo` resterebbe
                  `OK`. Il conto `battiti === 3` (:545) prova il codice di oggi, non §2.2.
MARCA:            [R]
```

---

### R6.14 — un guasto d'ambiente viene riferito come «la pagina non è conforme»

```
DOVE:             01-b11-pagina.html:388-392 (atob dell'impronta, fuori da ogni try),
                  :507-511 (il catch che trasforma tutto in `errore:…`), :548, :558
COSA CONTRADDICE: `LEZIONI.md` §1.9 e `REVIEWER.md` §1 domanda 4 — «una misura che può dire "zero"
                  deve poter dire anche "sono fallito"»;
                  e `banchi/01-b2-sonda.html`:142-147 e :178-188, che per lo **stesso** ingresso
                  distingue tre cause e le stampa
COME SI DIMOSTRA: si lancia la pagina senza `?impronta=` (o con un'impronta non base64). Nel primo
                  caso `wt.ready` è rifiutata per ognuno dei tredici casi — §4.1-bis e la misura S1
                  dicono che l'eccezione dell'utente **non copre** WebTransport su Chrome né su
                  Firefox; nel secondo `atob()` solleva prima ancora del `try`. In tutt'e due,
                  ciascun caso finisce in `fatto = "errore:…"` (:509-510), `guasti` vale 15 (:548) e
                  il campo che il banco legge è `esito: "NON-CONFORME"` (:558).
                  ⛔ In `b2-esiti.jsonl` quella riga è **identica** a quella di una pagina che ha
                  davvero violato §3 tredici volte, e `01-b11-lancia.sh`:128-131 legge esattamente
                  quel campo. La sonda di B2, davanti allo stesso guasto, scrive `NON-APERTA` ed
                  elenca le tre cause: qui la distinzione è stata persa.
MARCA:            [R]
```

---

### R6.15 — la POST dell'esito non è protetta e non è verificata: la pagina non sa se il suo verdetto è arrivato

```
DOVE:             01-b11-pagina.html:494-496 e :554-564  (await fetch("/esito", …))
COSA CONTRADDICE: `LEZIONI.md` §1.9 quarta regola, citata da `01-b2-raccogli.py`:69-79 —
                  «la richiesta È il denominatore dell'esito»;
                  e `banchi/01-b2-sonda.html`:75-92, che la stessa chiamata la avvolge in un
                  `try/catch` e, se fallisce, **lo scrive sullo schermo**: *«⚠ Se il raccoglitore
                  non c'e', il banco NON deve fingere: si dice»*;
                  forma **E7** — «il registro dice "ho chiamato la funzione", non "il byte è
                  arrivato"»
COME SI DIMOSTRA: due ingressi.
                  1. si ferma il raccoglitore dopo che la pagina è stata caricata: `fetch` è
                     rifiutata, non c'è `catch`, la promessa dell'IIFE `async` muore come
                     *unhandled rejection*. Lo schermo mostra il verdetto completo, il file non ha
                     niente, e **la pagina non dice niente**. Per `01-b11-lancia.sh`:117-125 questo
                     è indistinguibile da «la pagina si è piantata a metà».
                  2. la POST riceve **404 o 500** — per esempio perché la pagina è servita da un
                     origine diversa dal raccoglitore, o perché la scrittura di
                     `01-b2-raccogli.py`:52 solleva. `fetch` **non rifiuta** sugli stati 4xx/5xx,
                     e la pagina non guarda `response.ok`: l'`await` si risolve, la pagina
                     considera consegnato un esito che non è stato scritto da nessuna parte.
MARCA:            [R]
```

---

### R6.16 — `SESSIONE.stato` non è validato

```
DOVE:             01-b11-pagina.html:343  (const stato = l.u8(), …) — `stato` non è più letto
COSA CONTRADDICE: RCP.md §4.5 — «`u8 stato   1 = NUOVA, 2 = RIPRESA`»; RCP.md §3, «un campo fuori
                  intervallo»
COME SI DIMOSTRA: `SESSIONE` con `stato = 7`. `leggi_sessione` controlla i limiti e la parità della
                  tela (:348) e non tocca `stato`: la pagina prosegue e stampa
                  `SESSIONE: tela 1920x1080, desktop=…`. Un terzo stato inesistente entra senza
                  che nessuno lo nomini — ed è la coppia esatta del caso `sessione-tela-dispari`,
                  che invece la pagina rifiuta: due campi dello stesso messaggio, due rigori
                  diversi.
MARCA:            [R]
```

---

### R6.17 — dopo `RESPINTO` la guardia blocca il solo `CREDENZIALI`, dove §4.4 ammette il solo `CONGEDO`

```
DOVE:             01-b11-pagina.html:233-236  (if (this.respinto && tipo === T.CREDENZIALI))
COSA CONTRADDICE: RCP.md §4.4, il riquadro del 10 agosto 2026 — «⛔ **E dopo `RESPINTO` al client
                  resta una cosa sola che può dire: `CONGEDO`.** … ⛔ Qualunque **altro** messaggio,
                  **e in particolare** un secondo `CREDENZIALI`, è la violazione che §4.4 vieta».
                  «in particolare» dice che `CREDENZIALI` è **un** caso, non **il** caso
COME SI DIMOSTRA: la guardia è scritta come un elenco di uno. Un `ATTACCA`, un `VISTA`, un
                  `RICHIEDI_CHIAVE` spediti dopo `RESPINTO` passano — e il registro del server, che
                  §4.4 dichiara adesso contare separatamente i commiati dai tentativi, li conta
                  come byte dopo la fine. ⚠ Oggi nessun percorso del file li spedisce: la
                  contraddizione è fra la guardia e il commento :228-232 che dichiara di
                  implementare §4.4, non ancora fra la guardia e un byte sul filo.
MARCA:            [R]
```

---

### R6.18 — la pagina risponde `CHIUSO_DALL_UTENTE` a un congedo del server: un motivo che non ha osservato

```
DOVE:             01-b11-pagina.html:468-471  (if (!rcp.congedato && !rcp.fine) … manda(CONGEDO, 0x01))
COSA CONTRADDICE: RCP.md §8.2 — `0x01 CHIUSO_DALL_UTENTE` = «l'utente ha chiuso il client»: nessun
                  utente ha chiuso niente, è il banco che finisce un caso;
                  RCP.md §4.2 — «Chi lo riceve DEVE considerarla finita; NON DEVE continuare a
                  spedire»
COME SI DIMOSTRA: nel ramo `e.congedo !== undefined` (:423-425) la pagina **non** chiama `chiudi()`,
                  quindi `congedato` resta falso; se il server ha mandato `CONGEDO` senza FIN,
                  `fine` resta falso; alla riga :468 le due condizioni sono soddisfatte e la pagina
                  spedisce `CONGEDO(0x01)` **in risposta al congedo del server**, cioè dopo la fine
                  della sessione e con un motivo falso. Ingresso: un server che risponde al `CIAO`
                  con `CONGEDO(0x09 NIENTE_IN_COMUNE)`.
MARCA:            [R]
```

---

### R6.19 — la versione nel percorso e la versione nel `CIAO` non vengono mai confrontate

```
DOVE:             01-b11-pagina.html:47 (URL_SERVER dalla query) contro :263 (u16(1) in corpo_ciao)
COSA CONTRADDICE: RCP.md §2.2 — «⛔ **E le due DEVONO coincidere**: un `CIAO(versione=2)` su
                  `/rcp/1` è `VERSIONE_INCOMPATIBILE`, non una negoziazione da risolvere»;
                  RCP.md §9, che dal 10 agosto nomina §2.4 apposta perché «chi legge solo una delle
                  due trov[i] l'altra»
COME SI DIMOSTRA: `?url=https://host:7447/rcp/2`. La pagina apre la sessione su `/rcp/2` e ci
                  spedisce dentro `CIAO(versione=1)` — la sola combinazione che §2.2 dichiara
                  illegale — senza una riga di registro. La versione è codificata a mano in due
                  posti che non si guardano: la costante `1` di :263 e la stringa che l'operatore
                  digita. ⚠ È il caso che B5 ha già trovato dal lato del server (§9, riquadro del
                  10 agosto); dal lato del client non lo guarda nessuno.
MARCA:            [R]
```

---

### R6.20 — la pagina annuncia dodici casi e ne gira tredici

```
DOVE:             01-b11-pagina.html:11-13 («dodici cose sbagliate»), :356 («I DODICI CASI»)
                  contro l'array `CASI` :358-385, che ha **tredici** voci
COSA CONTRADDICE: RCP.md §0-bis, rilievo **R1.29** — «⚠ *diceva "22 su 22", e il conto era della
                  prima stesura* … **non è pedanteria — quella casella è l'unica prova che il
                  documento porta di essere completo, e chi la verificava contando ne trovava di
                  più**»
COME SI DIMOSTRA: si contano le voci fra :359 e :384: `eccomi-versione-2`, `capacita-sconosciuta`,
                  `misura-massima-in-eccomi`, `tipo-sconosciuto`, `congedo-motivo-zero`,
                  `sessione-tela-dispari`, `bidi-dal-server`, `fin-sul-controllo`,
                  `respinto-poi-congedo`, `respinto-non-riprovare`, `sessione-desktop-kde`,
                  `sessione-desktop-gnome`, `silenzio` = **13**. ⚠ E il testo che l'utente legge è
                  doppiamente falso: quattro di quelle tredici (`capacita-sconosciuta`, i due
                  `sessione-desktop-*`, `silenzio`) **non sono «cose sbagliate»**, sono casi in cui
                  il server è conforme e si misura che la pagina non reagisca. Lo stesso conteggio
                  è ripetuto in `01-b11-guasto-innesta.py`:29 e in `01-b11-lancia.sh`:22-24.
MARCA:            [R]
```

---

## I sospetti `[?]`

### R6.21 — i cronometri di `prossimo()` non vengono mai cancellati

```
DOVE:             01-b11-pagina.html:204-217
COSA CONTRADDICE: nulla di normativo. Contraddice la dichiarazione implicita del parametro
                  `attesa_ms`: che l'attesa duri quel tempo
COME SI DIMOSTRA: non si dimostra con un ingresso — ed è per questo che è `[?]`. Ogni giro del
                  `while` installa un `setTimeout` che nessuno cancella quando il messaggio arriva
                  prima. Il cronometro superstite chiama `this._sveglia()` più tardi e risveglia
                  **l'attesa in corso**; poiché `scaduto` è la variabile della chiamata nuova, la
                  guardia :211 non scatta, il `while` rientra e **riarma l'attesa piena**. Un
                  `prossimo(8000)` può quindi durare 16 s. Nei tempi attuali (la stretta di mano si
                  chiude in ~1,5 s, i cronometri superstiti scadono a 12-13 s, `gira()` finisce a
                  ~4 s) non risulta raggiunto — ma è una durata che il codice non garantisce, e
                  `MANDATO-10-agosto.md` §3 punto 6 dichiara aperta la ricerca delle cause dei
                  verdetti divergenti.
MARCA:            [?]
```

### R6.22 — `b2-esiti.jsonl` è condiviso fra B2 e B11, e il campo `banco` non lo legge nessuno

```
DOVE:             01-b11-pagina.html:557 (banco: "B11") contro 01-b2-raccogli.py:34 (un file solo)
                  e 01-b11-lancia.sh:128-131 (legge **l'ultima riga**, per conteggio)
COSA CONTRADDICE: `REVIEWER.md` §1 domanda 4 — distinguere lo zero dal fallimento
COME SI DIMOSTRA: la pagina spedisce `banco: "B11"` e nessuno lo confronta: il raccoglitore scrive
                  in `b2-esiti.jsonl` qualunque cosa arrivi, e il lanciatore identifica «l'esito di
                  questo giro» come «l'ultima riga, quando il conteggio è salito di uno». Se una
                  sonda B2 registrasse nella stessa finestra — o se un secondo motore in coda
                  scrivesse per primo — il conteggio salirebbe e la riga letta sarebbe di un altro
                  banco, con un `esito` («APERTA», «NON-APERTA») che non è nemmeno del vocabolario
                  di B11. Non ho potuto verificare che accada: serve una misura.
MARCA:            [?]
```

### R6.23 — `str()` tronca la lunghezza a 16 bit senza dirlo, e i limiti di §4.4 non sono controllati in uscita

```
DOVE:             01-b11-pagina.html:69-75 (str), :402 (str(UTENTE), str(PAROLA))
COSA CONTRADDICE: RCP.md §4.4 — «stringa utente da 1 a **256** byte», «stringa parola da 1 a
                  **1024** byte»; RCP.md §6.1 — il tetto di 1 MiB, che la pagina applica in entrata
                  (:188) e non in uscita
COME SI DIMOSTRA: `?parola=` con 2000 caratteri produce un `CREDENZIALI` che supera il limite di
                  §4.4 e che la pagina spedisce senza una riga; con 65 536 caratteri
                  `setUint16(0, b.length)` **avvolge a zero** e la pagina spedisce un'inquadratura
                  incoerente — cioè commette essa stessa la violazione di §6.1 che il caso
                  `tipo-sconosciuto` esiste per punire nel server. ⚠ Marcato `[?]` perché nessun
                  percorso del banco passa oggi una stringa di quella misura: dipende da chi
                  digita la riga di comando.
MARCA:            [?]
```

### R6.24 — il messaggio del `CONGEDO` non porta quel che §3.1 punto 1 pretende

```
DOVE:             01-b11-pagina.html:326 («ECCOMI troncato»), :344 («SESSIONE troncato»),
                  :281 («niente invece di …»)
COSA CONTRADDICE: RCP.md §3.1 punto 1 — «**DEVE** scrivere nel registro *che cosa* non ha capito —
                  **il tipo ricevuto, la lunghezza, lo stato in cui si trovava**. Non "errore di
                  protocollo"»
COME SI DIMOSTRA: `ECCOMI` con `quante = 3` e il corpo tagliato a metà: la sola riga che finisce nel
                  registro e nel `dettaglio` del `CONGEDO` è `ECCOMI troncato`. Non c'è la
                  lunghezza dichiarata, non c'è quella ricevuta, non c'è il numero della capacità su
                  cui si è rotto. Le tre informazioni che §3.1 elenca sono zero su tre. ⚠ `[?]`
                  perché §3.1 non dice se «il tipo ricevuto» basti quando il tipo è quello atteso;
                  ma su `SESSIONE troncato` mancano tutte e tre senza ambiguità.
MARCA:            [?]
```

### R6.25 — `_sfoglia()` accoda una violazione nuova a ogni chunk, e non svuota il buffer

```
DOVE:             01-b11-pagina.html:188-193
COSA CONTRADDICE: RCP.md §6.1 — «⛔ E la lunghezza si controlla **prima di allocare**», che la
                  pagina rispetta; ma non c'è nessuna regola su che cosa fare **dopo**
COME SI DIMOSTRA: un server che dichiara `lunghezza = 0x7FFFFFFF` e continua a spedire byte: il
                  ramo :188 accoda una `Violazione` e fa `return` **senza consumare `arrivati` e
                  senza smettere di leggere**; `_leggi()` continua ad accumulare in memoria e a
                  chiamare `_sfoglia()`, che accoda una copia della stessa violazione a ogni chunk.
                  La coda e il buffer crescono finché il consumatore non chiude. `[?]` perché in
                  pratica il consumatore chiude entro un turno, e non ho misurato quanto cresca.
MARCA:            [?]
```

---

## Che cosa ho provato a rompere e non ci sono riuscito

Dichiarato perché vale quanto un rilievo (`PIANO.md` §0.4):

- **il disallineamento dei `DataView`**: `_sfoglia()` costruisce `new DataView(this.arrivati.buffer,
  this.arrivati.byteOffset)` e `Lettore` `new DataView(b.buffer, b.byteOffset, b.length)`. Ho
  cercato un percorso in cui `arrivati` o `corpo` fossero una **vista** su un buffer più grande —
  che darebbe letture di byte altrui: non c'è. `_leggi()` costruisce sempre un `Uint8Array` nuovo, e
  `.slice()` su un `TypedArray` restituisce un buffer nuovo con `byteOffset` 0. Non sono riuscito a
  farlo sbagliare.
- **il confronto `desktop-non-cambia-niente`**: ho cercato un modo di farlo dire `IDENTICI` su due
  giri realmente diversi. `dopoCiao()` scarta il primo messaggio, che è il `CIAO`, e la guardia
  `dopoCiao(kde) !== ""` (:534) impedisce che due giri **entrambi vuoti** contino come identici.
  Regge. ⚠ Resta che il confronto guarda `usciti`, cioè il lato che spedisce — è R6.13, non un
  difetto di questo confronto.
- **il conto `battiti === 3`**: ho cercato di farlo salire con il `CONGEDO` di fine caso. Non ci
  riesco: `usciti` viene fotografato a :451, **prima** del congedo di :470. Il numero 3 è quello
  giusto per i tre messaggi della stretta di mano.
- **la guardia di `manda()` su `fine`**: ho cercato un percorso che spedisse dopo un FIN. `manda()`
  è l'unico punto in cui si scrive su `this.w`, e la guardia :224 lo copre. Regge — a patto che
  nessuno scriva mai direttamente su `this.w`, che oggi non accade.
- **il `CIAO` della pagina contro §4.3**: dichiara `pcm` in `audio.codec` e `8` in
  `video.profondita`, come §4.3 impone a **entrambi**; `banco.guasto` è un nome legale per il
  charset di §4.3 e i valori dei casi sono testo stampabile sotto i 256 byte. Non sono riuscito a
  trovarci una violazione.
- **`SOLO_DEL_CLIENT`**: contiene esattamente i quattro nomi che §4.3 assegna al solo client
  (`video.livello`, `video.misura_massima`, `input.tocco`, `client.nome`), e non contiene
  `appunti.testo`, che §4.3 dà a entrambi. Ho verificato nome per nome sulla tabella: è giusto.
- **il rifiuto della tela di `leggi_sessione`**: i limiti (320-7680, 240-4320) e la parità sono
  quelli di §4.5, e valgono sulla tela **concessa**, che è il campo giusto. Ho provato 320×240,
  7680×4320, 321×240, 0×0: tutti trattati come §4.5 impone. Regge. ⚠ Sul campo `stato` dello stesso
  messaggio no — è R6.16.
- **la doppia `wt.close()`** (:253 e :473): ho cercato di farne derivare un secondo codice di
  chiusura che sovrascrivesse il primo. La specifica WebTransport rende `close()` un no-op quando la
  sessione è già chiusa, e `chiudi()` la chiude per primo. Non sono riuscito a rompere l'ordine —
  ma non l'ho eseguito.

---

## ⚠ La dichiarazione che chiude, come vuole `REVIEWER.md` §0

Questo rapporto trova **contraddizioni**, non verità. Non ho eseguito una riga, non ho misurato un
byte: ogni «come si dimostra» è un ingresso costruito leggendo il codice e l'arbitro, e va **girato
al coder perché lo esegua**. Un rilievo che il banco non riproduce non è un rilievo smentito —
è un rilievo non ancora misurato (`LEZIONI.md` §1.3 letta al rovescio).

E il rovescio vale anche per quel che non c'è qui dentro: le venticinque voci sopra non sono
l'elenco dei difetti della pagina. Sono **quelli che ho trovato**.
