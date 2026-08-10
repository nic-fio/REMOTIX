# R7 — revisione avversariale dei due arbitri meccanici: B4 e B5

*10 agosto 2026. Area: `banchi/01-b5-violazioni.py`, `banchi/01-b5-lancia.sh`,
`banchi/01-b4-validatore.py`, `banchi/01-b4-registrazioni.py`, `banchi/01-b4-lancia.py`.
Arbitro scritto contro cui si misura la coerenza: `RCP.md`.*

⛔ Letti prima di scrivere un rilievo: `REVIEWER.md` per intero,
`fasi/rapporti/MANDATO-10-agosto.md` per intero, `RCP.md` §2.2-§2.5, §3, §3.1, §4.3-§4.6,
§6.0-§6.3, §7.1, §7.5, §8.1, §8.2, §9, §11, §11.1.

> **Che cosa è questo documento.** Non è un'approvazione. `REVIEWER.md` §0: il verdetto ha
> sempre la forma *«questo contraddice X»*. Dove non ho trovato niente lo dico con quelle
> parole, in §3, insieme a quel che ho provato a rompere senza riuscirci.

⚠ **Perché quest'area conta più delle altre.** `REVIEWER.md` §1: *«un difetto nel banco non lo
trova niente, e avvelena ogni misura successiva — perché dà fiducia»*. Questi due programmi non
sono banchi qualunque: sono **gli arbitri meccanici** del progetto. B4 è l'unico terzo lettore di
`RCP.md`; B5 è l'unico posto in cui si prova che il server **applica** §3 invece di limitarsi a
non cadere. Sopra i loro verdi poggiano, oggi, due righe pubblicate in `README.md` (righe 30, 34,
35) e la tabella di `fasi/01-filo-nudo.md` riga 612.

---

## 0. Il conto

| | |
|---|---|
| rilievi `[R]` | **15** |
| rilievi `[?]` | **7** |
| di cui toccano un verdetto **pubblicato** | 6 (`README.md` 30, 34, 35; `fasi/01-filo-nudo.md` 307, 612) |

⚠ **Cinque dei quindici `[R]` li ho verificati eseguendo il validatore su registrazioni
costruite apposta**, in una cartella di lavoro fuori dal progetto: nessun file del progetto è
stato toccato. Restano marcati `[R]` — non `[M]` — perché non misurano il **prodotto**: leggono
il comportamento dello **strumento**, che è quel che questa revisione ha per oggetto. L'uscita
osservata è riportata dentro «COME SI DIMOSTRA» perché il rilievo si possa rifare in un minuto.

---

# I rilievi `[R]`

---

## R7.1 — ⛔ Il motivo si **raschia dal testo dell'eccezione**, e un caso che non è mai arrivato alla violazione conta come verde

```
DOVE:             banchi/01-b5-violazioni.py:632-637, e la decisione a :827
COSA CONTRADDICE: REVIEWER.md §2 forma E6 («il mittente dedotto invece che chiesto»),
                  E7 («si verifica dal lato che invia»), LEZIONI.md §1.6;
                  e la riga 24 del docstring dello stesso file, che dichiara
                  «il motivo giusto, letto DAL LATO CHE RICEVE (§8.1)»
```

`gira_caso` avvolge **tutto** — l'apertura, la stretta di mano preparatoria *e* la violazione —
in un solo `try`, e nel `except` fa questo:

```python
except Exception as e:
    es.errore = f"{type(e).__name__}: {e}"
    for c, n in MOTIVI.items():
        if n in str(e):
            es.motivo = c
            break
```

Poi, a riga 827, il verdetto del caso è **`ok = es.motivo == atteso`** — e `es.errore` **non
viene consultato**. Il motivo non è letto da un `CONGEDO` sul filo: è cercato come
**sottostringa** dentro la rappresentazione testuale di un'eccezione qualunque.

```
COME SI DIMOSTRA: il caso `banco-id-zero` (:556) chiama `fino_a_sessione`, che manda
                  l'ATTACCA fisso `attacca()` = 1920x1080/"it".  Si supponga un server
                  che rifiuti QUELL'ATTACCA — per esempio perché non riconosce la
                  disposizione "it", o perché sbaglia la parità.  `b3.attendi` solleva
                  `RuntimeError("CONGEDO invece di SESSIONE: motivo 0x0b =
                  ERRORE_PROTOCOLLO")` (01-b3-cliente.py:179-181).  La raschiatura trova
                  "ERRORE_PROTOCOLLO" nella stringa, imposta es.motivo = 0x0B, e 0x0B è
                  esattamente l'atteso del caso.  ⛔ VERDE — e `BANCO_MARCA(id=0)`, cioè
                  la violazione che il caso esiste per provare, NON È MAI PARTITA.
```

⛔ **Quanti casi ha sotto.** Tutti quelli che hanno una preparazione e attendono
`ERRORE_PROTOCOLLO`: `credenziali-due-volte` (:467), `tela-1921x1080` (:475), `tela-319x240`
(:483), `tela-7682x4320` (:489), `disposizione-malformata` (:512), `banco-id-zero` (:556),
`banco-prima-di-sessione` (:565), più i cinque casi degli stream (:574-:615) che passano da
`fino_a_eccomi`. **Dodici casi su quarantaquattro** possono essere verdi senza che il byte
storto sia mai stato spedito.

⚠ **E si richiude su sé stesso**: più il server è rotto a monte, più questi casi diventano
verdi, perché più eccezioni portano un nome di motivo nel testo. È la forma esatta di
`LEZIONI.md` §1.3 — un banco che non riproduce il difetto non assolve il codice — con in più
che qui il banco *scambia il difetto per la prova*.

---

## R7.2 — ⛔ Sui casi che **DEVONO passare**, «il server ha chiuso» è indistinguibile da «la sessione regge»

```
DOVE:             banchi/01-b5-violazioni.py:824 (`ok = es.motivo is None and es.errore is None`),
                  con :167, :179, :209 dove `Esito.viva` viene calcolato e mai usato
COSA CONTRADDICE: il docstring dello stesso file, righe 48-50: «`banco-spento` ⛔
                  `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`, **non una chiusura** e non
                  un silenzio»; «`banco-ritardo` … **e la sessione RESTA APERTA**».
                  E RCP.md §7.5 regola 2, RCP.md §11 riga «la funzione di banco spenta»
```

`Esito` ha un campo `viva` (`:167`), lo si calcola (`:209`
`es.viva = not cli.finito and es.motivo is None`) e lo si **stampa** (`:179`). Il verdetto non
lo guarda. Guarda solo che non sia arrivato un motivo e che non sia stata sollevata
un'eccezione. Nemmeno `es.codice_wt` — la chiusura della sessione WebTransport — entra nel
giudizio degli otto casi che devono passare.

```
COME SI DIMOSTRA: caso `hevc-e-vp9` (:410).  Il server manda ECCOMI (b3.attendi è
                  soddisfatta, nessuna eccezione), e subito dopo CHIUDE la sessione
                  WebTransport senza mandare CONGEDO.  In `Cliente.quic_event_received`
                  (01-b3-cliente.py:151-153) `finito` diventa True e in coda finisce
                  `None`; `raccogli` esce sul ramo `if m is None: break` (:196-197)
                  lasciando `es.motivo = None`; nessuna eccezione è stata sollevata,
                  quindi `es.errore = None`.  ⛔ ok = True, e la riga stampata è
                  «OK  hevc-e-vp9   la sessione regge» — mentre la sessione è morta.
                  Lo stesso ingresso rende verdi `capacita-sconosciuta`,
                  `nome-con-trattino-basso`, `vista-300x801`, `vista-1x1`,
                  `disposizione-con-variante`.
```

⚠ **Seconda strada per lo stesso verde**, ed è ancora più corta: a `:201` il motivo si legge
`corpo[0] if corpo else None`. Un `CONGEDO` con **corpo vuoto** — che RCP.md §7.1 non ammette,
il corpo vuole `u8 motivo` + `stringa dettaglio` — lascia `es.motivo = None` e produce lo stesso
verde. Un server che chiude male è **più facile** da far passare di uno che chiude bene.

⛔ **Perché è grave e non è una pignoleria.** Le righe 42-53 del docstring dichiarano che questi
casi sono *«il controllo che dice no a "questo server chiude tutto"»*. Il controllo positivo del
banco è precisamente il pezzo che non controlla la cosa che dice di controllare — è
`REVIEWER.md` §1 domanda 5 applicata al suo stesso controllo positivo.

---

## R7.3 — ⛔ Il punto 3 di §3.1 si **stampa** e non si conta: «per tutt'e due le strade» è un'affermazione senza verifica

```
DOVE:             banchi/01-b5-violazioni.py:840-849
COSA CONTRADDICE: RCP.md §3.1 punto 3 e RCP.md §8.1 («DEVE ripetere il motivo nel codice
                  d'errore applicativo della chiusura»), RCP.md §3.1 ultima riga
                  («Il codice 0 … NON DEVE essere usato»), RCP.md §11 riga «il congedo»
                  («per ciascuno si verifica ANCHE il codice nella chiusura della sessione»);
                  e README.md riga 34 e fasi/01-filo-nudo.md riga 612, che pubblicano
                  «per tutt'e due le strade di §3.1 ogni volta»
```

Il blocco è questo, e sta **dopo** che `ok` è già stato deciso:

```python
if atteso is not None and es.motivo == atteso:
    vie = []
    if es.motivo is not None: vie.append("CONGEDO")
    if es.codice_wt == atteso: vie.append("chiusura-WT")
    elif es.codice_wt is not None: vie.append(f"chiusura-WT={es.codice_wt:#04x} ⛔ DIVERSA")
    print(f"        §3.1: il motivo e' arrivato per {' + '.join(vie)}")
```

`guasti` non viene toccato in nessuno dei tre rami. Un `⛔ DIVERSA` non è un rosso; un
`es.codice_wt is None` — cioè **la seconda strada non è arrivata affatto** — non compare
nemmeno nell'elenco `vie`, e la riga stampata diventa `§3.1: il motivo e' arrivato per CONGEDO`,
che è vera e dice il contrario di quel che il lettore ci legge.

```
COME SI DIMOSTRA: un server che manda CONGEDO(0x0B) sul canale di controllo e poi chiude
                  la sessione WebTransport con codice applicativo 0 — cioè la chiusura
                  «senza motivo» che RCP.md §3.1 vieta con un ⚠ esplicito.  `es.motivo`
                  = 0x0B = atteso ⇒ ok = True ⇒ nessun guasto; la riga stampata è
                  «§3.1: il motivo e' arrivato per CONGEDO + chiusura-WT=0x00 ⛔ DIVERSA»
                  e il banco esce 0.  Trentasei casi su trentasei restano verdi con il
                  punto 3 di §3.1 mai implementato.
```

⛔ **E il docstring giustifica l'omissione citando il rilievo sbagliato.** Righe 26-31: *«§3.1
dice "se il canale di controllo è ancora utilizzabile": qui si registra quale delle due è
arrivata, e non si pretendono sempre tutt'e due (rilievo R3.3)»*. In RCP.md §3.1 la clausola
condizionale sta sul **punto 2** (il `CONGEDO`), non sul **punto 3** (la chiusura della
sessione): il punto 3 è un **DEVE** incondizionato, ed è quello che §3.1 chiama *«quello che
salva le diagnosi»*. Il banco ha invertito quale dei due è facoltativo, e ha reso facoltativo
proprio quello che il documento dichiara essere l'ultima risorsa quando l'altro non arriva.

---

## R7.4 — ⛔ Il validatore dichiara **conforme** una registrazione in cui non ha giudicato niente

```
DOVE:             banchi/01-b4-validatore.py:340 (`for nb in range(quanti)`),
                  :383-386 (`continue` su ogni canale != 0x00), :431-433
COSA CONTRADDICE: banchi/01-b4-lancia.py:75-79, che dello stesso difetto un livello più
                  in su scrive: «⛔ Il denominatore del verdetto: se le registrazioni
                  fossero zero, "tutte passano" sarebbe vero e vuoto (LEZIONI.md §1.9,
                  punto 6)».  E REVIEWER.md §1 domanda 4, forma E8
```

Tre modi di ottenere `uscita 0 — conforme` senza che una sola regola di RCP sia stata
applicata.

```
COME SI DIMOSTRA (eseguito, uscita riportata alla lettera):

  a) registrazione con zero blocchi — 16 byte in tutto:
       MAGIA + struct.pack("!II", 0, 0)
     →  uscita 0    «⭐ conforme: 0 blocchi, nessuna violazione»

  b) registrazione fatta di soli blocchi video (canale 0x03):
       r.blocco(SERVER, b"\x03\x01" + b"\x00"*26, canale=0x03, stream=7)
     →  uscita 0    «⭐ conforme: 1 blocchi, nessuna violazione»
     (il blocco esce dal `continue` di :386 con «non giudicato da questo validatore»,
      e la riga finale dice comunque «nessuna violazione»)

  c) `quanti` sotto-dichiarato: si prende b4-registrazioni/1-lunghezza-incoerente.rcpreg
     — che il banco certifica come NON CONFORME al byte 508 — e si scrive 4 al posto di
     6 nel campo quanti_blocchi dell'intestazione:
       d[8:12] = struct.pack("!I", 4)
     →  uscita 0    «⭐ conforme: 4 blocchi, nessuna violazione»
     Il blocco offensivo è il quinto: non viene mai letto, e il file resta valido per
     ogni altra riga di §11.1.

  d) coda di spazzatura dopo i blocchi dichiarati:
       conforme.rcpreg + b"\xff" * 4096
     →  uscita 0    «⭐ conforme: 6 blocchi, nessuna violazione»
```

⛔ **E il controllo che c'è è quello che non può fallire.** A `:431` sta
`if visti != quanti: raise Malformata(...)`. `visti` è incrementato una volta per iterazione di
un `for nb in range(quanti)` che o completa o solleva: `visti != quanti` è **codice morto**. Il
controllo che coprirebbe (c) e (d) — `p == len(d)` alla fine del ciclo — **non c'è**. Un
controllo impossibile da far fallire, in piedi al posto di quello che servirebbe: è la stessa
forma del contatore per indirizzo che B5 ha trovato nel server (README.md riga 36), *«codice
presente, che sembra giusto, e che non fa niente»*, qui dentro l'arbitro.

---

## R7.5 — ⛔ Un file che non si può leggere esce **1 = «non conforme»**: il terzo esito esiste e non copre il caso per cui è stato inventato

```
DOVE:             banchi/01-b4-validatore.py:325-326 (l'`open` fuori da ogni try),
                  :441-451 (`main` cattura NonConforme e Malformata, non OSError)
COSA CONTRADDICE: il docstring dello stesso file, righe 21-29: «⛔ TRE ESITI, NON DUE …
                  Il terzo esiste perché "il file è rotto" e "il filo non era conforme"
                  sono due fatti diversi con due cure diverse, e un validatore che li
                  confondesse manderebbe a cercare un difetto di protocollo dentro un
                  difetto di banco».  E REVIEWER.md §2 forma E8 («una lettura negata
                  letta come "non c'è niente"»), REFERENCE.md R32
```

`valida()` apre il file alla prima riga, fuori da qualunque protezione. `main()` cattura
`NonConforme` (→ 1) e `Malformata` (→ 2). Un `OSError` non è nessuna delle due: risale, Python
stampa la traccia e **il processo esce 1** — che in questo programma vuol dire, per contratto
scritto in cima al file, *«non è conforme — e si dice QUALE byte e QUALE regola»*.

```
COME SI DIMOSTRA (eseguito):

  python3 01-b4-validatore.py non-esiste.rcpreg
    →  uscita 1   FileNotFoundError: [Errno 2] No such file or directory

  chmod 000 negato.rcpreg; python3 01-b4-validatore.py negato.rcpreg
    →  uscita 1   PermissionError: [Errno 13] Permission denied
```

⛔ **Dove fa danno davvero**: la seconda riga è E8 alla lettera. Il validatore gira anche
**dentro il contenitore**, su registrazioni scritte da un server lanciato come root e lette da
un altro utente. Il giorno in cui i permessi non tornano, l'arbitro dirà *«il filo non è
conforme»* e la diagnosi partirà dal protocollo. `01-b4-lancia.py` non salva: per una voce
`non-conforme` legge l'uscita 1, poi cerca `byte (\d+) nel file` nel testo, non lo trova, e
riporta `atteso il byte 508, accusato None` — cioè un rosso sul **byte** invece che sul **file**,
che è esattamente ciò che le righe 9-16 del suo docstring dichiarano di esistere per
distinguere.

---

## R7.6 — ⛔ Due dei quarantaquattro casi di B5 violano **due** regole insieme, e la seconda è già provata da un altro caso

```
DOVE:             banchi/01-b5-violazioni.py:363-367 (`valore-vuoto`)
                  banchi/01-b5-violazioni.py:370-374 (`valore-257-byte`)
                  in relazione a :116-117 (`BUONE`) e :377-382 (`capacita-ripetuta`)
COSA CONTRADDICE: PIANO.md §0.4 («si costruisce l'ingresso concreto che violerebbe
                  l'invariante», uno per volta) e la premessa del banco stesso:
                  un verde deve dire QUALE controllo ha risposto
```

`BUONE` (`:116`) contiene già `("client.nome", "banco-b5 0.1.0")`. I due casi mandano
`ciao(BUONE + [("client.nome", …)])`: il `CIAO` che arriva al server porta **`client.nome` due
volte**.

```
COME SI DIMOSTRA: `valore-vuoto` (:363) manda l'elenco
                    video.codec · video.profondita · audio.codec · client.nome ·
                    client.nome(vuoto)
                  RCP.md §4.3 dà DUE ragioni per chiuderlo con ERRORE_PROTOCOLLO:
                    «⛔ un nome ripetuto due volte è ERRORE_PROTOCOLLO»
                    «⛔ un valore vuoto è ERRORE_PROTOCOLLO»
                  Un server che implementi SOLO la prima — cioè che il caso
                  `capacita-ripetuta` (:377) già prova — dà VERDE su `valore-vuoto` e su
                  `valore-257-byte` senza aver mai guardato la lunghezza di un valore.
                  Il controllo di «valore vuoto» e quello di «valore oltre 256 byte»
                  restano non provati, e il banco riporta 44 su 44.
```

⛔ La cura è di una riga e non è mia (`REVIEWER.md` §5, non riscrivo): l'ingresso deve portare
**una sola** violazione. ⚠ Lo stesso sospetto, più debole, su `nome-maiuscolo` (`:340`): manda
`("Video.Codec", "hevc")`, che per un server che normalizzasse i nomi in minuscolo prima di
confrontarli diventerebbe il duplicato di `video.codec` di `BUONE` — verde dalla regola dei
duplicati invece che da quella dei caratteri. Lo marco `[?]` in §2 perché dipende da come il
server normalizza, che non ho letto.

---

## R7.7 — ⛔ `uni-video` manda un tipo di fotogramma che RCP.md §6.2 dichiara illegale di suo: il verso non viene mai messo alla prova

```
DOVE:             banchi/01-b5-violazioni.py:592-598
COSA CONTRADDICE: RCP.md §6.2, tabella del campo `tipo`: «`0x0301` fotogramma chiave,
                  `0x0302` fotogramma delta.  ⛔ Altri valori: ERRORE_PROTOCOLLO».
                  E la dichiarazione del caso stesso (:592-594): «il canale VIDEO (0x03)
                  DAL CLIENT: verso sbagliato»
```

```python
u = cli.apri_uni()
cli.manda_su(u, struct.pack("!H", 0x0300) + b"\x00" * 26)
```

`0x0300` non è né `0x0301` né `0x0302`.

```
COME SI DIMOSTRA: un server che legga i due byte del tipo, veda 0x0300, non lo trovi fra
                  i due valori di §6.2 e congedi con ERRORE_PROTOCOLLO **senza aver mai
                  guardato da che parte arriva lo stream** dà verde su questo caso.  La
                  regola che il caso dichiara di provare — «un canale usato NEL VERSO
                  SBAGLIATO … lo è a sua volta» (RCP.md §2.5, ultimo capoverso) — resta
                  non provata, e nessun altro caso la copre: `uni-audio` (:601) prova la
                  regola diversa «l'audio solo su datagram», `uni-byte-alto-ignoto` (:610)
                  prova i cinque canali.  Con `0x0301` al posto di `0x0300` l'unica
                  regola applicabile sarebbe il verso.
```

⚠ **La stessa forma, più discutibile, in altri due casi**, che segnalo qui invece di
moltiplicare i rilievi:

- `secondo-bidirezionale` (`:574-580`) apre il secondo stream bidirezionale e ci scrive
  `b"\x00\x01\x00\x00\x00\x00"`, cioè un `CIAO` con corpo di **zero** byte, mandato **dopo che
  `ECCOMI` è già arrivato**. Tre regole diverse lo condannano: lo stream in più (§2.5), il corpo
  che finisce prima di `versione` (§6.1), il `CIAO` nello stato sbagliato (§4). Il caso è verde
  anche su un server che non conta gli stream bidirezionali.
- `uni-controllo` (`:583-589`) manda `struct.pack("!HI", 0x0001, 0)`, cioè lo stesso `CIAO`
  vuoto e ripetuto, su uno stream unidirezionale: verde da due regole che un altro caso già
  prova.

---

## R7.8 — ⛔ Manca il caso che DEVE passare sulla quarta eccezione di §3, e con lui il banco non distingue il rigore dal «chiudo su ogni numero fuori intervallo»

```
DOVE:             banchi/01-b5-violazioni.py, i 44 casi di CASI — nessuno prova
                  ADATTA_TELA, un datagram corto, o una RICHIEDI_CHIAVE ravvicinata
COSA CONTRADDICE: RCP.md §3, tabella delle cinque eccezioni, righe 284-292 — e in
                  particolare l'eccezione 4, che è scritta con un ⚠ apposta perché
                  qualcuno la provi: «lo stesso valore fuori intervallo uccide la
                  connessione in ATTACCA e non in ADATTA_TELA, e la differenza è
                  VOLUTA — l'utente che trascina male una finestra non deve perdere la
                  sessione (rilievo R1.10)»
```

RCP.md §3 dichiara **cinque** eccezioni alla regola di rigore, e dice *«fuori da questo elenco
non se ne inventano»*. B5 ne prova **una**: la prima, con `capacita-sconosciuta` (`:393`) e
`hevc-e-vp9` (`:410`). Le altre quattro non hanno nessun caso.

```
COME SI DIMOSTRA: si prenda un server che applichi il controllo dei limiti di §4.5 in una
                  funzione sola, chiamata sia da ATTACCA sia da ADATTA_TELA, e che
                  congedi con ERRORE_PROTOCOLLO in tutt'e due i casi.
                  → `tela-1921x1080` (:475), `tela-319x240` (:483), `tela-7682x4320`
                    (:489): tutti e tre VERDI, perché su ATTACCA quel comportamento è
                    corretto;
                  → nessun altro caso lo tocca, quindi B5 esce 44 su 44;
                  → e RCP.md §3 eccezione 4 è violata: l'utente che trascina la finestra
                    a una misura dispari **perde la sessione**, che è il sintomo esatto
                    che quella riga è stata scritta per impedire.
                  Il caso mancante è di sei righe, ed è il gemello di `banco-ritardo-20000`
                  (:546): `ADATTA_TELA(1921, 1081)` dopo SESSIONE, atteso
                  `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)` **con la sessione ancora aperta**.
```

⚠ **E le altre tre eccezioni scoperte**, che elenco perché il mandato chiede *«ne manca uno che
oggi non c'è?»* e la risposta onesta è **quattro**:

| eccezione di §3 | che cosa proverebbe | oggi |
|---|---|---|
| 2 (§6.3) | un datagram di 4 byte, o con `tipo` ≠ `0x0401`, si **scarta** invece di far cadere la connessione | nessun caso — e `apri()` (`:213`) configura già `max_datagram_frame_size=65536`, quindi costa una riga |
| 3 (§7.1) | il **secondo di grazia** sulle coordinate vecchie dopo `TELA(ADATTATA)` | nessun caso |
| 5 (§5.2, §7.4) | due `RICHIEDI_CHIAVE` a meno di 200 ms: la seconda **si può ignorare**, non è un errore | nessun caso |

⛔ Tutte e quattro hanno la stessa forma, ed è la forma che il docstring di B5 dichiara di
temere (righe 40-53): un server che **chiude su tutto** oggi prende trentasei verdi su
trentasei fra le violazioni, e le otto che dovrebbero smascherarlo stanno **tutte dentro la
stretta di mano**, dove il server è più probabile che sia stato scritto bene.

---

## R7.9 — ⛔ `RESPINTO` conta come `CONGEDO`: due tipi diversi sotto lo stesso verdetto

```
DOVE:             banchi/01-b5-violazioni.py:200-205
COSA CONTRADDICE: RCP.md §4.4 («⛔ `RESPINTO` è il congedo dell'autenticazione … e NON
                  DEVE mandare anche `CONGEDO`»), RCP.md §8.1 («l'unica eccezione è
                  `RESPINTO`»), RCP.md §11 riga «il congedo» e il rilievo R1.18 che vi è
                  citato.  E REVIEWER.md §2 forma E3
```

```python
if tipo == CONGEDO or tipo == 0x0005:
    es.motivo = corpo[0] if corpo else None
```

Da qui in poi `es.motivo` non ricorda più **in quale messaggio** il motivo è arrivato, e il
verdetto di `:827` non lo chiede.

```
COME SI DIMOSTRA: caso `utente-vuoto` (:438), atteso ERRORE_PROTOCOLLO.  Un server che
                  invece di applicare §3 tratti l'utente di zero byte come un tentativo
                  fallito e risponda `RESPINTO(0x0B)` — messaggio sbagliato, ma motivo
                  giusto — dà es.motivo = 0x0B, ok = True, VERDE.  E la differenza non è
                  formale: dopo `RESPINTO` §4.4 vieta al client di riprovare sulla stessa
                  connessione, mentre dopo un `CONGEDO(ERRORE_PROTOCOLLO)` la connessione
                  è finita e basta — sono due macchine a stati diverse.  Lo stesso vale
                  al contrario su `senza-pcm` (:420) e `senza-8` (:429), dove RCP.md §4.3
                  impone un CONGEDO(NIENTE_IN_COMUNE) e un RESPINTO passerebbe.
```

⚠ Nota che RCP.md §11 dichiara esplicitamente il confine — *«`CREDENZIALI_ERRATE` e
`TROPPI_TENTATIVI` viaggiano in `RESPINTO`»*, tutti gli altri in `CONGEDO` — e che il banco ha
l'informazione per applicarlo: `es.messaggi` (`:166`, `:199`) registra i tipi arrivati **in
ordine** e non viene consultato da nessun verdetto.

---

## R7.10 — ⛔ Il validatore non registra `RESPINTO` nella macchina degli stati: `RESPINTO` seguito da `AMMESSO` è **conforme**

```
DOVE:             banchi/01-b4-validatore.py:300-320 (`Stato.ammette` / `Stato.segna`)
COSA CONTRADDICE: RCP.md §4.4: «⛔ RESPINTO è il congedo dell'autenticazione.  Dopo averlo
                  mandato il server DEVE chiudere la connessione come dice §3.1 … E dopo
                  RESPINTO al client resta una cosa sola che può dire: CONGEDO».
                  E RCP.md §1: «⛔ L'ordine dei cinque passi non ammette permute»
```

Due buchi nella stessa funzione:

1. `segna()` (`:316`) appende a `fatti` **solo** i nomi che stanno in `ORDINE`. `RESPINTO` non
   c'è. Dopo un `RESPINTO`, `fatti` finisce ancora con `CREDENZIALI`, quindi
   `ammette("RESPINTO")` continua a dire sì (un secondo `RESPINTO` passa) e `ORDINE[len(fatti)]`
   vale ancora `AMMESSO` (un `AMMESSO` dopo il rifiuto passa).
2. `ammette()` (`:307`) restituisce `None` per **qualunque** nome non appena `self.attiva` è
   vero, prima di controllare che il nome faccia parte della stretta di mano.

```
COME SI DIMOSTRA (eseguito, registrazioni costruite con 01-b4-registrazioni.py):

  a) CIAO · ECCOMI · CREDENZIALI · RESPINTO(0x07) · RESPINTO(0x07) · AMMESSO ·
     ATTACCA · SESSIONE
     →  uscita 0   «⭐ conforme: 8 blocchi, nessuna violazione»
     Cioè: un server che rifiuta le credenziali, lo dice due volte, poi ammette
     l'utente e apre la sessione, è dichiarato conforme dall'unico arbitro esterno
     del progetto.

  b) la stretta di mano conforme, seguita da un secondo CREDENZIALI e da un secondo CIAO
     →  uscita 0   «⭐ conforme: 8 blocchi, nessuna violazione»
     Un secondo CREDENZIALI è la violazione che RCP.md §4.4 nomina per esteso
     («qualunque ALTRO messaggio, e in particolare un secondo CREDENZIALI, è la
     violazione che §4.4 vieta») e che B5 prova con `credenziali-due-volte` (:467).
     ⛔ I due arbitri danno verdetti opposti sulla stessa regola.
```

⚠ Il commento a `:308` — *«a sessione aperta l'ordine non è più vincolato»* — è una lettura di
`RCP.md` che il documento non autorizza: §1 dice che **l'ordine dei cinque passi** non ammette
permute, non che dopo il quinto tutto è permesso. È `MANDATO-10-agosto.md` §1: *«un commento che
spiega perché una riga è giusta non è una prova che lo sia»*.

---

## R7.11 — ⛔ L'impronta degli intervalli oscurati si legge e si **butta**: `hashlib` è importato e mai usato

```
DOVE:             banchi/01-b4-validatore.py:41 (`import hashlib`), :350
                  (`impronta = d[p+8:p+40]`), :360 (`del impronta`)
COSA CONTRADDICE: RCP.md §11.1: «si registra la lunghezza vera, si sostituiscono i soli
                  byte segreti con altrettanti byte di riempimento, e il formato dichiara
                  quali intervalli sono oscurati, **con l'impronta di quel che c'era**»;
                  e il paragrafo che spiega perché il campo esiste: «sostituirla e
                  riscrivere la lunghezza farebbe convalidare al validatore un documento
                  riscritto dal banco — e allora non è più un arbitro»
```

Trentadue byte per blocco oscurato viaggiano nel formato per una ragione sola: legare quel che
il registratore dichiara di aver nascosto a quel che c'era davvero. Il validatore li estrae in
una variabile e la cancella con `del` alla riga successiva. `hashlib`, importato in cima, non
compare in nessun'altra riga del file.

```
COME SI DIMOSTRA (eseguito): si prende b4-registrazioni/conforme.rcpreg e si sostituisce
                  l'impronta del blocco CREDENZIALI con 32 byte di zeri, lasciando
                  intatto tutto il resto:
                    r.blocchi[2] = (v, c, st, carico, [(ini, qua, b"\x00"*32)])
                  →  uscita 0   «⭐ conforme: 6 blocchi, nessuna violazione»
```

⛔ **Perché non è una raffinatezza.** L'impronta è l'unica cosa che impedisce a un registratore
di **oscurare quel che gli fa comodo**: senza verificarla, un registratore che dichiarasse
oscurato un intervallo che in realtà conteneva un campo malformato otterrebbe l'assoluzione — il
validatore non guarda dentro gli intervalli oscurati per obbligo di §11.1 (`:167-170`), e non
guarda l'impronta per omissione. ⚠ Il caso non è ipotetico: `01-b3-cliente.py:236-238` costruisce
l'intervallo oscurato con un calcolo (`ini = 6 + 2 + len(utente) + 2`) che nessuno controlla, e
un errore lì fa sparire dal giudizio dei byte che non sono la parola d'ordine.

---

## R7.12 — ⛔ Il validatore accusa il byte sbagliato sulle violazioni di §4.5, e i suoi due scostamenti indicano **due byte diversi**

```
DOVE:             banchi/01-b4-validatore.py:250-257 (i due `raise` con `le.base, 0`)
COSA CONTRADDICE: RCP.md §11.1 ultima riga: «⛔ E il validatore riferisce lo scostamento
                  del byte offensivo in due modi: assoluto nel file, e relativo al carico
                  del blocco.  Il primo serve a chi guarda il file con un editor, il
                  secondo a chi legge questa specifica».
                  E il docstring dello stesso file, righe 32-39: «⛔ E RIFERISCE QUALE
                  BYTE, NON SOLO CHE È ROSSO … Rosso giusto, byte sbagliato — e su una
                  traccia vera manda la diagnosi a leggere il messaggio sbagliato»
```

Tutti gli altri `raise` del file calcolano l'offset del campo. Questi quattro no: passano
`le.base, 0`, cioè l'inizio del **corpo del messaggio** come assoluto e **zero** come relativo.

```
COME SI DIMOSTRA (eseguito): registrazione conforme in cui ATTACCA porta
                  tela = 1921 x 1081 (dispari tutt'e due):
                    ⛔ NON CONFORME — RCP.md §4.5
                       tela_larghezza = 1921 e' dispari
                       byte 496 nel file · scostamento 0 nel carico del blocco
                  I numeri veri per quella registrazione sono:
                    inizio del blocco ATTACCA nel file        490
                    inizio del corpo del messaggio            496
                    primo byte di tela_larghezza              496
                    primo byte di tela_altezza                500
                  ⛔ 496 e 0 NON SONO LO STESSO BYTE: il primo dista sei byte dall'inizio
                  del blocco, il secondo è l'inizio del blocco.  §11.1 chiede due modi di
                  dire lo stesso byte; il validatore ne dice due diversi, e chi apre il
                  file con un editor e chi legge la specifica non guardano lo stesso punto.
                  E su `tela_altezza = 1081` accusa ancora 496 / 0, mentre il byte
                  offensivo sta a 500.
```

⚠ **Ed è invisibile a B4** perché nessuna delle sei registrazioni guaste esercita §4.5: il
manifesto non ha nessuna riga con `"regola": "RCP.md §4.5"`. Il banco che esiste per prendere
«rosso giusto, byte sbagliato» non copre la famiglia di regole in cui il difetto c'è davvero.

⚠ Della stessa famiglia, minore: `:160` cita **`RCP.md §4.4`** per ogni stringa più corta del
minimo, compresi i **nomi di capacità**, che stanno in §4.3 (`:196` passa `minimo=1`). Un rosso
con la sezione sbagliata accanto passa il controllo `voce["regola"] not in testo` di
`01-b4-lancia.py:59` senza che nessuno se ne accorga, perché nessuna registrazione lo esercita.

---

## R7.13 — ⛔ B4 legge registrazioni e attese scritte da **un'altra esecuzione**, e non ha nessun caso per il terzo esito

```
DOVE:             banchi/01-b4-lancia.py:29-31 (legge `manifesto.json` e i `.rcpreg` da
                  una cartella, senza mai rigenerarli), e
                  banchi/01-b4-registrazioni.py:146-240 (`costruisci`: sette casi, nessuno
                  malformato)
COSA CONTRADDICE: REVIEWER.md §1 domanda 2 («il banco è certificato PRIMA di essere
                  usato?») e domanda 5 («ha un controllo positivo?»);
                  banchi/01-b4-validatore.py righe 21-29, che dichiara TRE esiti;
                  RCP.md §11.1: «⛔ Il validatore … DEVE rifiutare una registrazione in cui
                  un intervallo oscurato cade fuori dal carico o si sovrappone a un altro:
                  una registrazione malformata e un filo non conforme sono due cose
                  diverse, e vanno dette con due frasi diverse»
```

**Due difetti, nello stesso punto della catena.**

**(a) La lettura di un giro vecchio.** `01-b4-lancia.py` non esegue `01-b4-registrazioni.py`, non
ne confronta l'impronta, non guarda le date. Certifica il validatore contro i file che trova.

```
COME SI DIMOSTRA: si cambia in 01-b4-registrazioni.py lo scostamento atteso di un caso —
                  per esempio `r.scostamento(4, 6 + 12)` a riga 168 — e si lancia
                  `python3 01-b4-lancia.py`.  Il banco stampa «7 su 7 … È certificato»,
                  perché legge il manifesto.json del giro precedente.  L'ATTESO che il
                  docstring di 01-b4-registrazioni.py chiama «scritto qui e non nella
                  testa di chi guarda» (riga 266) è scritto in un file che nessuno lega
                  al programma che lo ha prodotto.
                  ⚠ Oggi i sette file su disco coincidono con quel che il programma
                  produce — l'ho verificato rigenerandoli in una cartella di lavoro e
                  confrontandoli byte per byte, sette su sette identici.  Il rilievo non
                  è che siano vecchi: è che **niente lo impedisce**, ed è la forma
                  dell'errore che il mandato §3 punto 3 dichiara già pagata due volte
                  oggi.
```

**(b) L'esito 2 non ha nessun controllo positivo.** Le sette registrazioni sono una conforme
(uscita 0) e sei non conformi (uscita 1). **Nessuna è malformata.** L'esito che il validatore
dichiara essere la ragione per cui gli esiti sono tre non è mai stato osservato dal banco che lo
certifica.

```
COME SI DIMOSTRA: si rompa `Malformata` — per esempio si cambi `raise Malformata(...)` a
                  :362 in `raise NonConforme("RCP.md §6.1", ..., p, 0)`.  Il validatore
                  risponderebbe «non conforme» a un file troncato, cioè commetterebbe
                  esattamente l'errore che le righe 27-29 del suo docstring dichiarano di
                  esistere per evitare — e `01-b4-lancia.py` continuerebbe a stampare
                  «7 su 7 … È certificato», perché nessuna delle sette registrazioni è
                  troncata.
                  L'ottava registrazione mancante è di tre righe: la conforme, con
                  `quanti_blocchi` intatto e il carico dell'ultimo blocco tagliato a metà,
                  attesa `uscita 2`.  ⚠ E ce ne vorrebbe una nona, per il caso che §11.1
                  nomina esplicitamente: due intervalli oscurati che si sovrappongono.
```

---

## R7.14 — ⛔ «44 violazioni su 44» è un conteggio di sé stesso, e le otto che devono passare sono contate come violazioni

```
DOVE:             banchi/01-b5-violazioni.py:892-894, e il docstring righe 42-53
COSA CONTRADDICE: LEZIONI.md §1.9 e REVIEWER.md §1 domanda 4 (un conteggio senza
                  denominatore); e i numeri pubblicati in README.md righe 34-35 e in
                  fasi/01-filo-nudo.md riga 612
```

```python
print(f"⭐ B5: {len(casi)} violazioni su {len(casi)}, il motivo giusto ogni volta, "
      f"e il server vivo dopo ciascuna")
```

Il numeratore e il denominatore sono la stessa espressione: la riga stampa `N su N`
qualunque cosa sia successo, e la stampa **solo** quando `guasti == 0`, cioè non porta
informazione che il colore non porti già. E `len(casi)` conta **tutti** i casi.

```
COME SI DIMOSTRA (contato sul file):
                  44 casi in totale;
                  8 con `atteso is None`, cioè che DEVONO passare —
                    nome-con-trattino-basso · capacita-sconosciuta · hevc-e-vp9 ·
                    vista-300x801 · vista-1x1 · disposizione-con-variante ·
                    banco-spento · banco-ritardo-20000;
                  36 violazioni vere.
                  ⛔ «44 violazioni su 44» ne conta otto che non sono violazioni e su cui
                  «il motivo giusto ogni volta» è falso per costruzione: su quegli otto
                  non deve arrivare nessun motivo.
                  ⛔ E il docstring, righe 42 e 52-53, dice «Cinque casi qui dentro sono
                  verdi attesi» e «Senza di loro … darebbe trentacinque verdi su
                  trentacinque»: i casi sono OTTO, e 44 − 8 = 36, non 35.  Nessuno dei tre
                  numeri torna con il file.
                  ⛔ README.md riga 35 riporta l'errore aggravato: «i cinque casi che
                  DEVONO passare … Senza di loro, "il server chiude su tutto" darebbe 44
                  verdi su 44» — che è aritmeticamente impossibile, perché senza di loro
                  i casi sarebbero 36.
```

⚠ È la casella che `RCP.md` §0-bis chiama *«l'unica prova che il documento porta di essere
completo»*, nella sua versione da banco: il numero che dichiara la copertura è l'unico che
nessuno ricalcola, ed è sbagliato in tre punti su tre.

---

## R7.15 — ⛔ `01-b5-lancia.sh`: un filtro che non trova niente è **verde**, e un filtro che trova qualcosa è **rosso** per costruzione

```
DOVE:             banchi/01-b5-lancia.sh:136-141 e :155-172, con
                  banchi/01-b5-violazioni.py:806 (`casi = [...] if not a.solo or ...`)
                  e :892 (`if guasti == 0`)
COSA CONTRADDICE: REVIEWER.md §1 domanda 4 («una misura che può dire "zero" deve poter
                  dire anche "sono fallito"»), LEZIONI.md §1.9;
                  e la riga 5-7 del suo stesso commento d'uso, che offre
                  `01-b5-lancia.sh solo tela` come modo normale di lavorare
```

**Due facce dello stesso difetto, in versi opposti.**

**(a) Zero casi = verde.** `:806` filtra `CASI` per sottostringa. Se il filtro non combacia con
nessun nome, `casi` è vuoto, il ciclo di `:821` non gira mai, e se le sezioni successive passano
`guasti` resta 0.

```
COME SI DIMOSTRA: `bash 01-b5-lancia.sh solo pippo`
                  → `--solo pippo` seleziona zero casi
                  → il ciclo delle violazioni non esegue nulla
                  → «⭐ B5: 0 violazioni su 0, il motivo giusto ogni volta, e il server
                     vivo dopo ciascuna»  e uscita 0
                  → lo script stampa «⭐ B5 passa».
                  Un errore di battitura nel filtro è indistinguibile da un banco verde.
```

**(b) Un filtro qualunque = rosso.** Le due verifiche di `:155-172` girano **sempre**, anche
quando il caso che le produce non è stato selezionato.

```
COME SI DIMOSTRA: `bash 01-b5-lancia.sh solo tela` seleziona i tre casi `tela-*`.
                  Nessuno di essi manda `video.codec = hevc,vp9`: quella capacità è solo
                  in `hevc-e-vp9` (:410) e in `capacita-sconosciuta` (:393).
                  → `grep -q "scartate voci sconosciute" b5-server.log` fallisce
                  → ESITO=1 e «⛔ B5: qualcosa non passa», con la diagnosi «lo scarto di
                     vp9 NON è nel registro: una negoziazione riuscita con dentro il
                     contrario di quel che si voleva…»
                  cioè un rosso su una regola che non si è chiesto al server di applicare.
                  ⛔ È il difetto che lo script stesso dichiara di temere a :68-71 per
                  l'innesto («il banco darebbe rosso su una regola che il server non ha
                  mai avuto occasione di applicare»), commesso venti righe più in basso su
                  un'altra regola.
```

⚠ **E i due `grep` di `:157` e `:164` non distinguono l'assenza dalla lettura fallita**: se
`$FUORI/b5-server.log` non esiste — mappatura del volume saltata, server mai partito, nome
cambiato — `grep -q` esce 2 e il ramo `else` accusa il **server** di non aver scritto una riga
che RCP.md §4.3 gli impone. Forma **E8**, e l'unica differenza rispetto al caso reale è una riga
su `stderr` che nessuno legge.

⚠ **Un terzo pezzo, minore, stessa riga di ragionamento**: `:116` cancella `b5-server.log` e
`b5-server.pid` prima del giro, e **non** `b5-compila.log`. Se la compilazione fallisce prima di
scrivere il registro — `enter.sh` che non entra, `ninja` che non parte — il `tail -25` di `:98`
mostra **il registro di compilazione del giro precedente**, e la diagnosi parte da un errore che
non è successo oggi.

---

# I rilievi `[?]`

---

## R7.16 — `[?]` La seconda strada di §3.1 si legge da **un solo byte** della capsula, all'offset giusto per caso

```
DOVE:             banchi/01-b3-cliente.py:146-148, importato e usato da
                  banchi/01-b5-violazioni.py:208 (`es.codice_wt = cli.codice_chiusura`)
COSA CONTRADDICE (sospetto): RCP.md §3.1 punto 3, che chiede il «codice d'errore
                  applicativo» della chiusura di sessione — che in WebTransport è un
                  intero a 32 bit, non un byte
```

```python
if len(event.data) >= 7 and event.data[0] == 0x68 and event.data[1] == 0x43:
    codice = event.data[6]
```

`0x68 0x43` è il tipo di capsula `CLOSE_WEBTRANSPORT_SESSION` (0x2843) in varint a due byte;
segue una lunghezza in varint, poi il codice a 32 bit. Con una lunghezza che sta in un byte, il
codice occupa i byte 3-6 e `data[6]` ne è **l'ultimo ottetto**. Funziona finché il codice è
< 256 — e i motivi di §8.2 arrivano a `0x0F`.

```
COME SI DIMOSTRA (non l'ho potuto misurare): resta da verificare (i) che `aioquic`
                  consegni la capsula come dati grezzi sullo stream della sessione e non
                  la consumi nel suo strato H3; (ii) che i tre byte 3-5 siano zeri, cosa
                  che il codice non controlla e che renderebbe indistinguibile
                  `0x0000000B` da `0xFFFFFF0B`; (iii) che la capsula non arrivi mai
                  spezzata su due eventi, nel qual caso `data[0] != 0x68` e la seconda
                  strada di §3.1 sparisce in silenzio.
                  ⚠ Il sospetto pesa perché R7.3 mostra che nessun caso dà rosso quando
                  `codice_wt` è None: se questa lettura non funzionasse mai, B5 non lo
                  direbbe, e README.md riga 34 continuerebbe a pubblicare «per tutt'e due
                  le strade di §3.1 ogni volta».
```

---

## R7.17 — `[?]` Il banco lancia il server con `--timeout=120s`, cioè con il parametro di §2.2 fuori specifica, e nessun caso prova §4.6

```
DOVE:             banchi/01-b5-lancia.sh:117-122
COSA CONTRADDICE (sospetto): RCP.md §2.2, riga `max_idle_timeout` = «30 s, imposto dal
                  server»; e RCP.md §11, riga «i tempi della stretta di mano»
```

Il commento a `:117-120` motiva la scelta ed è onesto: alcuni casi aspettano dodici secondi. Ma
la conseguenza è che B5 misura un server **configurato diversamente da come RCP lo vuole**, e
che nessuno dei 44 casi tocca i tre tetti di §4.6 né il motivo `TEMPO_SCADUTO` (`0x0D`), che
`MOTIVI` conosce e nessun caso attende.

```
COME SI DIMOSTRA (non l'ho potuto misurare): serve una misura del coder — un server che
                  non implementi affatto §4.6 e §2.2 supera B5 al completo.  La domanda da
                  chiudere è se il tetto d'inattività sia davvero impostato a 30 s nel
                  server di produzione, e dove sia il banco che lo dice: `01-b5-lancia.sh`
                  lo sovrascrive, `01-b3-lancia.sh` non l'ho letto in questa revisione.
```

---

## R7.18 — `[?]` `apri()` perde il gestore della connessione quando fallisce, e la connessione resta aperta

```
DOVE:             banchi/01-b5-violazioni.py:212-223, con i tre chiamanti :624, :660, :685
COSA CONTRADDICE (sospetto): il difetto NOTO n. 6 del mandato — «B11 ha dato verdetti
                  diversi fra giri identici … `GIA_ATTIVA_REMOTA` sul caso successivo …
                  ⚠ Non è dimostrato che fossero le sole [cause]»
```

`apri()` entra nel gestore asincrono (`gestore.__aenter__()`, `:219`) e lo restituisce **solo
alla fine**. Se `wait_connected` o `cli.accettata` scadono, l'eccezione risale e il gestore
resta nella variabile locale di `apri`, che muore. Nei tre chiamanti `gestore` vale ancora
`None`, quindi il `finally` non chiama `__aexit__` e **la connessione QUIC non viene chiusa**.

```
COME SI DIMOSTRA (non l'ho potuto misurare): il banco apre almeno 44 + 44 + 3 + 1 + 14
                  connessioni per giro (`ancora_vivo` dopo ogni caso, `il_percorso`,
                  `giro_completo`, `limitatore`).  Ogni fallimento di apertura ne lascia
                  una viva dal lato del server.  Se il server conta le sessioni per
                  applicare I2 / `GIA_ATTIVA_REMOTA` (RCP.md §8.2 `0x0F`), una connessione
                  abbandonata occupa il posto **per i trenta secondi dell'orologio del
                  silenzio** — che è esattamente la finestra descritta nel riquadro di
                  `0x0F`.  ⚠ È la stessa forma del sintomo n. 6 del mandato, in un altro
                  banco: se il difetto sopravvive alle due cure già fatte, questo è un
                  posto dove cercarlo.
```

---

## R7.19 — `[?]` Il limitatore: si misura il settimo tentativo e mai la soglia, e la previsione scritta nel file è stata smentita e non tolta

```
DOVE:             banchi/01-b5-violazioni.py:720-794, in particolare :769-774
COSA CONTRADDICE (sospetto): RCP.md §4.4-bis, riga «soglia: 5 tentativi falliti in 5
                  minuti»; e README.md riga 36, che dichiara il difetto del contatore per
                  indirizzo già curato
```

Due cose.

**(a) La soglia non è misurata.** Il commento a `:769-770` dice *«I primi cinque sono
`CREDENZIALI_ERRATE`; dal sesto in poi la soglia è passata»*, ma il verdetto guarda solo
`motivi[-1]`, il settimo. I primi sei vengono stampati e non asseriti.

```
COME SI DIMOSTRA (non l'ho potuto misurare): un server che rispondesse TROPPI_TENTATIVI
                  al PRIMO tentativo fallito — un limitatore con la soglia a 0 — darebbe
                  verde su `contatore-per-indirizzo` e verde su
                  `blocca-anche-la-parola-giusta`.  Il numero 5 di §4.4-bis non è
                  verificato da nessuna riga.  ⚠ Il `giro-completo` di :878 corre prima e
                  lo prenderebbe, ma per un'altra via e con un'altra diagnosi.
```

**(b) La previsione smentita è rimasta nel file.** Il docstring `:728-734` dichiara
*«Previsione scritta prima di misurare: (b) sarà ROSSO»*, e `README.md` riga 36 dichiara il
difetto trovato e curato — *«Ora al sesto tentativo scatta `TROPPI_TENTATIVI`»*. La previsione
nel banco non è stata aggiornata né annotata. ⚠ Il valore di una previsione scritta in anticipo
è che si possa dire se ha tenuto: una che resta scritta dopo essere stata chiusa insegna a non
leggerle.

---

## R7.20 — `[?]` Il validatore non guarda né la versione, né le due capacità che §4.3 impone a entrambi

```
DOVE:             banchi/01-b4-validatore.py:230-232 (`le.u16("la versione")`, letta e
                  scartata) e :190-225 (`leggi_capacita`)
COSA CONTRADDICE (sospetto): RCP.md §4.3 — «RCP/1 vale 1»; «`pcm` DEVE essere dichiarato
                  da entrambi … Allo stesso modo `8` DEVE comparire in `video.profondita`
                  di entrambi»; e RCP.md §2.4 — «un `CIAO(versione=2)` su `/rcp/1` è
                  `VERSIONE_INCOMPATIBILE`»
```

```
COME SI DIMOSTRA (eseguito): registrazione conforme in cui il CIAO porta `versione = 7`
                  →  uscita 0   «⭐ conforme: 6 blocchi, nessuna violazione»
                  registrazione conforme in cui il CIAO dichiara
                    video.codec=hevc · video.profondita=10 · audio.codec=opus
                  cioè senza `pcm` e senza `8`
                  →  uscita 0   «⭐ conforme: 6 blocchi, nessuna violazione»
```

⚠ Lo marco `[?]` e non `[R]` per una ragione di confine che va decisa da chi ha scritto il
validatore, non da me: `RCP.md` §4.3 punisce la mancanza di `pcm` con `NIENTE_IN_COMUNE`, cioè
con un **congedo**, non con `ERRORE_PROTOCOLLO` — quindi un `CIAO` senza `pcm` è un messaggio
**ben formato** su cui la reazione giusta è di un altro livello. La domanda aperta è **quanto in
là arriva il mandato del validatore**: se giudica solo la forma dei byte, queste due omissioni
sono corrette e vanno **dichiarate** nel docstring accanto alle altre («i corpi che questo
validatore non serve ancora», `:283-285`); se giudica la conformità del filo, allora `versione =
7` su `/rcp/1` è un rosso che manca. ⛔ Oggi il documento del validatore non dice quale delle
due cose sia, e le due letture danno verdetti opposti sulla stessa registrazione.

---

## R7.21 — `[?]` Il campo `stream` della registrazione si legge e non si usa, e un commento afferma il controllo che manca

```
DOVE:             banchi/01-b4-validatore.py:343 (`verso, canale, stream, lung, nosc = …`)
                  e :388 (il commento «Il canale di controllo vive solo sullo stream 0
                  della sessione (§2.5)»), senza nessuna riga che lo verifichi
COSA CONTRADDICE (sospetto): RCP.md §2.5 — «`0x00` controllo … e su uno stream
                  unidirezionale è `ERRORE_PROTOCOLLO`: il controllo vive solo sullo
                  stream 0»; e RCP.md §11.1, che mette `u64 stream` nel formato
```

```
COME SI DIMOSTRA (eseguito): la registrazione conforme, col solo campo `stream` del primo
                  blocco portato da 0 a 3
                  →  uscita 0   «⭐ conforme: 6 blocchi, nessuna violazione»
                  La violazione che B5 prova con `uni-controllo` (:583) è invisibile
                  all'arbitro che dovrebbe giudicarla su una traccia registrata.
```

⚠ `[?]` e non `[R]` perché il campo `stream` di §11.1 è *«l'identificatore dello stream QUIC»* e
il documento **non dice** quale valore abbia il canale di controllo in una sessione WebTransport
— §4.2 dice esplicitamente che *«l'API non espone nessun numero»* e che il «(identificatore 0)»
era un resto della stesura a QUIC nudo (rilievo R1.5). ⛔ Quindi il commento di `:388` afferma
una cosa che RCP.md ha smentito in §4.2, e il campo `stream` del formato non ha una regola che
lo interpreti. La chiusura è del documento, non del codice.

---

## R7.22 — `[?]` `nome-maiuscolo` potrebbe essere respinto dalla regola dei duplicati

```
DOVE:             banchi/01-b5-violazioni.py:340-344
COSA CONTRADDICE (sospetto): la stessa forma di R7.6 — un verde di cui non si sa quale
                  controllo l'ha prodotto
```

```
COME SI DIMOSTRA (non l'ho potuto misurare, dipende dal server): il caso manda
                  `("Video.Codec", "hevc")` in coda a `BUONE`, che contiene già
                  `("video.codec", "hevc,av1")`.  Un server che normalizzi i nomi in
                  minuscolo prima di confrontarli — cosa che RCP.md §4.3 non vieta,
                  perché si limita a dire che i nomi sono fatti di `a-z 0-9 . _` — vede
                  `video.codec` due volte e chiude per duplicato, con lo stesso
                  ERRORE_PROTOCOLLO.  Basta leggere `banchi/rcp/rcp.c` per chiuderlo: se
                  il confronto dei caratteri viene prima della normalizzazione, il caso
                  è pulito.
```

---

# 2. Il quadro, in una tabella

| # | Dove | Forma | Marca |
|---|---|---|---|
| R7.1 | `01-b5-violazioni.py:632-637`, `:827` | E6, E7 — il motivo dedotto dal testo di un'eccezione | `[R]` |
| R7.2 | `01-b5-violazioni.py:824` | E8 — «ha chiuso» = «regge», su tutti i casi che devono passare | `[R]` |
| R7.3 | `01-b5-violazioni.py:840-849` | E1 — §3.1 punto 3 stampato e non contato | `[R]` |
| R7.4 | `01-b4-validatore.py:340`, `:386`, `:431` | E8 — niente da giudicare = conforme; controllo morto | `[R]` |
| R7.5 | `01-b4-validatore.py:325`, `:441` | E8 — lettura negata = «non conforme» | `[R]` |
| R7.6 | `01-b5-violazioni.py:363`, `:370` | due violazioni in un ingresso solo | `[R]` |
| R7.7 | `01-b5-violazioni.py:592` | verde possibile da una regola diversa da quella provata | `[R]` |
| R7.8 | `01-b5-violazioni.py`, i 44 casi | quattro delle cinque eccezioni di §3 senza controllo | `[R]` |
| R7.9 | `01-b5-violazioni.py:200` | E3 — `RESPINTO` e `CONGEDO` sotto la stessa etichetta | `[R]` |
| R7.10 | `01-b4-validatore.py:300-320` | E4 — l'ordine che ammette permute | `[R]` |
| R7.11 | `01-b4-validatore.py:41`, `:360` | l'impronta di §11.1 letta e buttata | `[R]` |
| R7.12 | `01-b4-validatore.py:250-257` | rosso giusto, byte sbagliato — e due scostamenti discordi | `[R]` |
| R7.13 | `01-b4-lancia.py:29`, `01-b4-registrazioni.py:146` | giro vecchio; nessun controllo positivo per l'esito 2 | `[R]` |
| R7.14 | `01-b5-violazioni.py:892`, docstring `:42-53` | conteggio senza denominatore, e tre numeri sbagliati | `[R]` |
| R7.15 | `01-b5-lancia.sh:136`, `:155-172` | zero = verde in un verso, rosso finto nell'altro | `[R]` |
| R7.16 | `01-b3-cliente.py:146` | il codice della chiusura letto da un byte solo | `[?]` |
| R7.17 | `01-b5-lancia.sh:117-122` | `--timeout=120s` contro §2.2; §4.6 senza banco | `[?]` |
| R7.18 | `01-b5-violazioni.py:212-223` | connessione persa, e il posto che resta occupato | `[?]` |
| R7.19 | `01-b5-violazioni.py:769` | la soglia di §4.4-bis mai asserita; previsione stantia | `[?]` |
| R7.20 | `01-b4-validatore.py:230`, `:190` | versione e `pcm`/`8` non giudicati, e il mandato non dichiarato | `[?]` |
| R7.21 | `01-b4-validatore.py:343`, `:388` | il campo `stream` letto e non usato; il commento afferma un controllo assente | `[?]` |
| R7.22 | `01-b5-violazioni.py:340` | possibile secondo motivo di rifiuto | `[?]` |

---

# 3. Che cosa ho provato a rompere **senza riuscirci**

`MANDATO-10-agosto.md` §5 punto 3, e `PIANO.md` §0.4: quel che non si rompe si dichiara.

**Su B4:**

1. **Il calcolo degli scostamenti attesi in `01-b4-registrazioni.py`.** Ho ricostruito a mano i
   sei scostamenti — `r.scostamento(4, 6+12)`, `r.scostamento(0, 6+scost)` con l'accumulo su
   tutte le voci che precedono, `r.scostamento(3, 6)` — e tornano tutti. In particolare
   l'aritmetica di `scostamento()` (`:108-116`), che deve saltare `16 + 40 × len(osc)` byte per
   ogni blocco, è giusta anche sul blocco 2, l'unico con un intervallo oscurato: il byte 508
   accusato sulla registrazione 1 è il byte giusto. ⭐ E i tre commenti che dichiarano gli errori
   dell'ATTESO già corretti (`:161-166`, `:181-184`) sono, per quel che ho potuto verificare,
   corretti davvero.
2. **La lettura degli intervalli oscurati.** Ho provato a far leggere al validatore dentro un
   intervallo oscurato — parola d'ordine sostituita da byte che formerebbero un `ERRORE`
   plausibile, intervalli a cavallo del confine fra un messaggio e il successivo. `Lettore.
   oscurato()` (`:148-151`) e la ri-basatura degli intervalli sul sotto-lettore (`:422-424`)
   reggono: l'intersezione è calcolata bene e la stringa oscurata torna `None` invece di essere
   decodificata. **Non ho trovato niente.**
3. **Il controllo del riempimento `0x2A`.** Ho provato a dichiarare un intervallo oscurato fatto
   di zeri, e a dichiararne uno che sborda dal carico, e uno che si sovrappone al precedente:
   tutti e tre danno `uscita 2`, con la frase giusta. ⭐ È la riga di §11.1 implementata bene, ed
   è quella che il documento marca con due ⛔.
4. **La distinzione fra uscita 1 e uscita 2 in `01-b4-lancia.py`.** Ho cercato un modo di far
   passare una registrazione malformata per «non conforme»: il controllo `if uscita != 1` a
   `:51` lo prende. **Non ho trovato niente** — il difetto è che non esiste una registrazione
   che eserciti quel ramo (R7.13), non che il ramo sia sbagliato.

**Su B5:**

5. **Il controllo che il server sia ancora vivo dopo ogni caso** (`ancora_vivo`, `:673-697`,
   più il testimone esterno di `01-b5-lancia.sh:144-152`). Ho cercato un modo di farlo passare
   con il server morto: apre una connessione nuova e arriva a `ECCOMI`, e il `finally`
   restituisce `False` su qualunque eccezione. ⭐ È la metà del banco che `REVIEWER.md` §1
   chiama «quella che nessuno scrive», ed è scritta bene — e il secondo testimone, `/proc/$PID`
   dal di fuori, è un testimone davvero diverso. **Non ho trovato niente.**
6. **L'ordine fra `giro_completo` e `limitatore`.** Il commento di `:869-876` sostiene che
   invertirli darebbe rosso quando la regola funziona. Ho provato a costruire una sequenza in
   cui l'ordine scelto nasconda un difetto invece di rivelarlo, e non ci sono riuscito: il
   blocco per indirizzo parte solo dentro `limitatore`, che è ultimo. **Non ho trovato niente**,
   e l'ordine è una misura come dice il commento.
7. **`il_percorso`** (`:648-670`). Ho cercato di farlo passare senza che il server risponda
   404: il confronto è `stato == atteso` su una stringa, e un'eccezione produce
   `errore NomeClasse`, che non è `"404"` → rosso. ⭐ Prova anche il caso positivo `/rcp/1` →
   200, che è il controllo positivo di `REVIEWER.md` §1 domanda 5. **Non ho trovato niente.**
8. **La verifica campo per campo di `BANCO_ESITO`** (`banco_esito`, `:132-154`). Ho cercato il
   verde comodo — «è arrivata una risposta e la sessione regge» — e non c'è: confronta `id`,
   `esito` e `motivo`, controlla la lunghezza minima, e verifica che `istante` valga 0 quando
   l'esito è RIFIUTATA, che è la riga di §7.5 più facile da dimenticare. ⭐ È il pezzo di B5
   scritto meglio.
9. **L'importazione del cliente di B3 invece della copia** (`:74-77`). Ho cercato una
   divergenza fra il cliente importato e quel che B5 assume: `manda`, `apri_controllo`,
   `attendi`, `MOTIVI`, `inquadra`, `s` sono usati con la stessa firma. ⚠ Con una riserva
   dichiarata: `b3.MOTIVI` (`01-b3-cliente.py:47-50`) contiene **otto** dei quindici motivi di
   §8.2, e `es.motivo` viene stampato con `MOTIVI.get(self.motivo, '?')` — un motivo fra i sette
   mancanti si stampa come `?`. Non è un difetto di verdetto (il confronto è numerico), ma la
   raschiatura di R7.1 cerca proprio dentro quel dizionario, quindi la sua superficie è più
   piccola di quanto sembri. Lo dico qui e non fra i rilievi perché rende R7.1 **meno** grave,
   non più.
10. **Il conteggio di `guasti` nel ciclo principale.** Ho cercato un esito che sopravvivesse a
    un errore di esecuzione: `gira_caso` cattura tutto e restituisce sempre un `Esito`; il
    `finally` chiude il gestore; un caso che esplode diventa rosso *se atteso è None*. ⛔ Per i
    casi con un atteso, invece, no — ed è R7.1. Il meccanismo è giusto, la decisione a `:827`
    no.

**Su tutt'e due:**

11. **La forma dei due programmi rispetto a `RCP.md` §11.** Ho cercato una riga normativa che i
    due banchi contraddicessero apertamente e che non fosse già in un rilievo qui sopra —
    per esempio le proporzioni della tela, i limiti degli appunti (§5.4), i limiti del cursore
    (§5.5): nessuno dei due banchi tocca quelle regole, e **non toccarle non è contraddirle**.
    Sono banchi di fasi successive, e `fasi/01-filo-nudo.md` non pretende il contrario.
12. **La certificazione di B4 prima dell'uso** (`REVIEWER.md` §1 domanda 2). Il principio è
    rispettato: il validatore *è* certificato prima di essere puntato sulle tracce vere, e la
    settima registrazione conforme esiste apposta perché «6 su 6» sarebbe compatibile con un
    validatore che boccia tutto. ⭐ Questa è la cosa migliore delle due aree, e va detta. Il
    rilievo R7.13 non è che la certificazione manchi: è che ha **due buchi dichiarabili** — non
    lega il manifesto al programma che lo produce, e non copre il terzo esito.

---

# 4. Le due domande che lascio aperte al coder, e a nessun altro

⚠ `REVIEWER.md` §4: un `[?]` si passa al coder perché lo misuri. Queste due non sono rilievi, sono
misure da fare, e le scrivo qui perché non si perdano in fondo a un elenco.

1. **`README.md` righe 30, 34, 35 e `fasi/01-filo-nudo.md` righe 307 e 612 pubblicano verdetti
   che poggiano su R7.1, R7.2, R7.3 e R7.14.** Nessuno di quei quattro rilievi dice che i verdi
   siano **falsi**: dicono che il banco **non li ha dimostrati**. La differenza è tutta in
   `REVIEWER.md` §0 — *«una review che non trova niente non assolve il prodotto»*, e il suo
   rovescio: un banco che non guarda non condanna, ma nemmeno assolve. ⛔ Finché R7.1-R7.3 non
   sono curati e B5 non è rifatto girare, «44 su 44 per tutt'e due le strade di §3.1» va letto
   come **«36 violazioni hanno prodotto il motivo atteso sul canale di controllo»**, che è meno
   di quel che è scritto.
2. **Fra R7.8 e la fase 9 c'è un ponte.** Le quattro eccezioni di §3 senza banco — datagram
   corti, secondo di grazia, `ADATTA_TELA` fuori limiti, `RICHIEDI_CHIAVE` ravvicinata — sono
   tutte e quattro **tolleranze**, cioè posti in cui il server DEVE **non** chiudere. E
   l'invariante I1 (`REVIEWER.md` §3) dice: *«ogni percorso che, quando la linea non porta,
   chiuda la connessione invece di continuare a calare i fotogrammi»*. ⛔ Un server che oggi
   passa B5 al completo può essere un server che chiude a ogni sorpresa, ed è precisamente la
   forma che I1 vieta. Il caso di sei righe su `ADATTA_TELA` costa poco e chiude la porta.

---

*Fine di R7. Nessun file del progetto è stato modificato all'infuori di questo.*
