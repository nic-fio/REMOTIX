# R8 — Revisione avversariale dei lanciatori e delle sonde di B2 e B3

**10 agosto 2026** · oggetto: `banchi/01-b2-lancia-wt.sh`, `01-b2-lancia-sonda.sh`,
`01-b2-lancia-impostazioni.sh`, `01-b2-lancia-trasporto.sh`, `01-b2-sonda-impostazioni.py`,
`01-b2-sonda-trasporto.py`, `01-b2-raccogli.py`, `01-b3-lancia.sh`, `01-b3-terzo-giro.sh`,
`01-b3-quarto-giro.sh`, `01-b3-quinto-giro.sh`, `01-b3-cliente.py`.

**La lente**: `REVIEWER.md` §1 — *il banco è il primo imputato*. Questi dodici file hanno prodotto i
numeri che `README.md` e `DECISIONI.md` §6.4 citano come **misurati**. La domanda ripetuta su
ciascuno è una sola: **che aspetto ha il caso in cui questo script è verde e il difetto è vivo?**

> ⛔ Non ho ricevuto il ragionamento di chi ha scritto il codice (`PIANO.md` §0.4 pratica 1). Ho
> letto `REVIEWER.md`, `MANDATO-10-agosto.md`, `RCP.md` §2.2–§2.4 e §8.2, `DECISIONI.md` §6.4,
> `fasi/01-filo-nudo.md`, i dodici file d'area, e — come materiale di prova — `v1/banco/enter.sh`,
> `v1/strumenti/sshpw.py`, `banchi/01-b2-cliente-aioquic.py`, `banchi/01-b2-sonda.html`,
> `banchi/01-b4-validatore.py`, `banchi/rcp/rcp.c`, `banchi/b2-esiti.jsonl`, `banchi/01-b11-lancia.sh`.
> **Non ho misurato niente e non ho toccato nessun file fuori da questo rapporto** (`REVIEWER.md` §5).
>
> I sei difetti noti di `MANDATO-10-agosto.md` §3 non sono ripetuti qui. Il rilievo **R8.5** sta
> accanto al n. 1 di quell'elenco: è la stessa forma — *uno smontaggio che si dichiara fatto e non
> lo è* — su un file diverso.

---

## 1. I rilievi, in ordine di gravità

*«Gravità» = quanto costa costruirci sopra prima di accorgersene. Un banco cieco costa più di un
banco assente, perché **dà fiducia** (`LEZIONI.md` §10).*

| # | Dove | Il rilievo, in una riga | Marca |
|---|---|---|---|
| **R8.1** | `01-b3-quarto-giro.sh:99` | ⛔ **`grep -q "SESSIONE"` è verde ESATTAMENTE sul difetto che il quarto giro esiste per vedere**: il rifiuto porta la parola «SESSIONE» dentro il proprio messaggio d'errore | `[R]` |
| **R8.2** | `01-b3-quarto-giro.sh:111` | ⛔ **`/proc/$MUTA` guarda il processo, non la connessione**: il cliente dorme e resta vivo anche se il server o QUIC hanno chiuso — cioè il controllo che deve escludere «è stato QUIC» non può vederlo | `[R]` |
| **R8.3** | `01-b3-quarto-giro.sh:5,9-20` | ⛔ **il tetto a 120 s è la premessa di tutto il giro e non lo mette né lo misura nessuno**: nessuno script lancia il server con `--timeout=120s` per B3, e il giro non legge `max_idle_timeout` dal filo | `[R]` |
| **R8.4** | `01-b3-terzo-giro.sh:91-99` | ⛔ **«la prima è sopravvissuta» è il codice d'uscita di un cliente che dorme**: uno spodestamento non lo cambia, e la prova che c'è (`b3-viva.log`) non la legge nessuno | `[R]` |
| **R8.5** | `01-b3-terzo-giro.sh:39` | ⛔ **le due registrazioni del terzo giro non si buttano**: `valida viva` può giudicare un `.rcpreg` di ieri — è il difetto che `01-b3-lancia.sh:55-58` dichiara curato | `[R]` |
| **R8.6** | `01-b3-lancia.sh:73-74` | ⛔ **`\| tail -3` mangia il verdetto dell'arbitro**: il validatore di B4 non entra in `BENE`, e «B3: tre giri su tre» si stampa con tre tracce NON CONFORMI | `[R]` |
| **R8.7** | `01-b2-lancia-sonda.sh:186` | ⛔ **`APERTA` non vuol dire «i byte tornano»**, e nel registro c'è già la prova: due esiti `APERTA` del 10 agosto portano *«lo stream non ha funzionato»* | `[R]` |
| **R8.8** | `01-b2-lancia-wt.sh:159-161` | ⛔ **«RIFIUTATO, come impone §2.2» da un `$? != 0`**: `RCP.md` chiede **404**, e un timeout, un UDP filtrato o un server morto danno lo stesso verde | `[R]` |
| **R8.9** | `01-b3-lancia.sh:110-111` | ⛔ **«sulle due tracce» ne valida una**: `b3-terza.rcpreg`, la traccia che porta il `CONGEDO(0x0F)` sotto esame, non arriva mai all'arbitro | `[R]` |
| **R8.10** | `01-b2-lancia-sonda.sh:153-186` | ⛔ **il motore si identifica contando le righe di un registro condiviso**, e il campo `motore` non si confronta mai: l'esito di uno può essere accreditato all'altro, o a B11 | `[R]` |
| **R8.11** | `01-b2-sonda-trasporto.py:141-142` | ⛔ **«datagram sulla connessione HTTP/3» misurato come parametro di trasporto QUIC**: la sonda non apre nessuna connessione HTTP/3, e `H3_DATAGRAM` (0x33) non lo guarda | `[R]` |
| **R8.12** | `01-b2-sonda-trasporto.py:148-149` | ⛔ **«almeno 16 in ogni momento» misurato all'istante zero**: `initial_max_streams_uni` è il credito iniziale, e §2.3 parla del credito che **finisce** | `[R]` |
| **R8.13** | `01-b2-lancia-impostazioni.sh:93,117` · `01-b2-lancia-wt.sh:57-64` | ⛔ **`kill` su un PID letto da un file che può essere di ieri**, da root dentro il contenitore, senza nessuna verifica che quel PID sia quel programma | `[R]` |
| **R8.14** | `01-b2-lancia-wt.sh:103-108` · `01-b2-lancia-impostazioni.sh:71-76` | ⛔ **«in ascolto» concluso da «tiene UNA porta UDP»**, non da «tiene la porta su cui la sonda andrà a bussare» | `[R]` |
| **R8.15** | `01-b2-lancia-wt.sh:79` · `-trasporto.sh:56` · `-impostazioni.sh:45` | ⛔ **«porta libera» e «il comando è fallito» sono la stessa stringa vuota**: lo stato d'uscita della catena `enter.sh \| ss \| grep` è buttato | `[R]` |
| **R8.16** | `01-b2-lancia-sonda.sh:89-97` | ⛔ **il ramo che dovrebbe dire «non ho l'impronta» è irraggiungibile**, e il caso zero esce con la diagnosi sbagliata («è tagliata») | `[R]` |
| **R8.17** | `01-b3-quinto-giro.sh:96-97` | ⚠ **«il browser CONFRONTA l'impronta» dedotto da `NON-APERTA`**: la pagina elenca da sé tre cause con lo stesso aspetto, e il lanciatore non ne distingue nessuna | `[?]` |
| **R8.18** | `01-b2-sonda-trasporto.py:98,191` | ⚠ **«niente 0-RTT» da un'attesa fissa di 1,5 s**, e il controllo positivo citato è di un'esecuzione precedente, non di questa | `[?]` |
| **R8.19** | `01-b2-lancia-sonda.sh:160-161,117` | ⚠ **`kill` sull'involucro `xvfb-run` non uccide il browser**, e il profilo si cancella sotto un browser vivo — è il meccanismo che alimenta R8.10 | `[?]` |
| **R8.20** | `01-b2-lancia-wt.sh:93` · `-impostazioni.sh:61` · `-trasporto.sh:65,80` | ⚠ **`sleep 2` / `sleep 1` al posto della condizione osservata** (la porta che compare, la porta che sparisce) | `[?]` |

---

## 2. I rilievi, per esteso

### R8.1 — Il quarto giro è verde esattamente quando l'orologio del silenzio non c'è `[R]`

```
DOVE:             banchi/01-b3-quarto-giro.sh:98-106
COSA CONTRADDICE: l'intestazione dello stesso file (righe 26-33: «a +35 s la terza DEVE
                  entrare»), l'invariante I4, SPECIFICHE.md §5.3, e LEZIONI.md §1.9 —
                  una misura che può dire «zero» deve poter dire anche «sono fallito»
COME SI DIMOSTRA: la catena, tutta leggibile:
                    1. banchi/rcp/rcp.c:850-855 — il posto si nega DENTRO il trattamento
                       di ATTACCA: `congeda(s, RCP_GIA_ATTIVA_REMOTA, ...)`;
                    2. 01-b3-cliente.py:258 sta aspettando SESSIONE, e 01-b3-cliente.py:177-181
                       solleva  RuntimeError("CONGEDO invece di SESSIONE: motivo 0x0f =
                       GIA_ATTIVA_REMOTA");
                    3. 01-b3-cliente.py:311-313 la stampa su stdout, che 01-b3-quarto-giro.sh:52
                       redirige in b3-tardi.log;
                    4. 01-b3-quarto-giro.sh:99 `grep -q "SESSIONE" b3-tardi.log` TROVA la
                       parola dentro quel messaggio, e la riga 100 stampa
                       «⭐ ENTRATA: chi tace è staccato, chi arriva entra (§5.3, §4.4)».
                  Cioè: **il server che NON ha l'orologio del silenzio, e che al minuto 35
                  rifiuta ancora la terza, fa stampare al banco che l'orologio c'è.**
                  La stessa trappola una seconda volta: MOTIVI[0x0E] = "SESSIONE_NON_SERVIBILE"
                  (01-b3-cliente.py:49) contiene «SESSIONE», quindi anche un
                  CONGEDO(SESSIONE_NON_SERVIBILE) a qualunque passo dà verde.
MARCA:            [R]
```

⚠ Il codice d'uscita del cliente, che sarebbe l'informazione giusta, **c'è e si butta**:
`cliente()` (righe 47-53) lo restituisce e nessuno lo legge — solo il `grep` decide. E il
controllo negativo a +6 s (riga 84, `grep -q "GIA_ATTIVA_REMOTA"`) è invece corretto: la
metà «no» del giro funziona, la metà «sì» no. È la combinazione peggiore, perché il primo
tempo dà credito al secondo.

### R8.2 — `/proc/$MUTA` misura il processo, non la connessione `[R]`

```
DOVE:             banchi/01-b3-quarto-giro.sh:108-117
COSA CONTRADDICE: il commento immediatamente sopra (righe 108-110: «se fosse caduta, a
                  liberare il posto sarebbe stato QUIC e non il server — che è
                  esattamente quel che questo giro esiste per escludere»), E1 e E7
COME SI DIMOSTRA: 01-b3-cliente.py:285-291 — dopo SESSIONE il cliente scrive il file di
                  segnale e poi fa `await asyncio.sleep(a.resta)` e basta. **Non legge
                  più niente dalla connessione.** Se il server chiude la sessione
                  WebTransport, `quic_event_received` mette un `None` in `self.messaggi`
                  (righe 151-153) che nessuno preleva; se QUIC chiude la connessione per
                  inattività, `asyncio.sleep` non se ne accorge. In tutt'e tre i casi —
                  connessione viva, sessione chiusa dal server, connessione morta per
                  scadenza — il processo è vivo a +35 s e `[ -d "/proc/$MUTA" ]` è vero.
                  Il banco stampa allora «⭐ e la connessione della prima è ancora viva: a
                  liberare il posto è stato il SERVER, non il tetto d'inattività di QUIC»
                  su un fatto che non ha osservato.
MARCA:            [R]
```

### R8.3 — Il tetto a 120 s è una premessa dedotta, mai misurata `[R]`

```
DOVE:             banchi/01-b3-quarto-giro.sh, intestazione (righe 5, 9-20) e tutto il corpo
COSA CONTRADDICE: E5 (un «fatto» che era una deduzione mai misurata) e il corollario di
                  LEZIONI.md §1.9 che 01-b2-sonda-trasporto.py:19-28 scrive per esteso —
                  *un denominatore si legge dove la cosa succede*
COME SI DIMOSTRA: `grep -rn 'timeout=120s' banchi/` dà due sole occorrenze, e sono di altri
                  due banchi: 01-b11-guasto.sh:149 e 01-b5-lancia.sh:122. Nessuno script
                  accende un server con `--timeout=120s` per B3: 01-b3-lancia.sh non accende
                  nessun server, 01-b3-quarto-giro.sh nemmeno, e 01-b2-lancia-sonda.sh:57
                  lancia `01-b2-lancia-wt.sh accendi $IND $PORTA` — tre argomenti, quindi
                  01-b2-lancia-wt.sh:50 mette OPZIONI="".
                  Con il tetto predefinito (30 s, misurato da 01-b2-lancia-trasporto.sh:84)
                  al minuto 35 la connessione della prima **è già caduta da sola**: il posto
                  si libera senza che il server abbia nessun orologio, la terza entra, e
                  R8.2 fa dire al banco che la prima era viva. ⛔ **Il quarto giro benedice
                  la violazione di I4 che dichiara di escludere.**
                  E lo strumento per chiudere il buco esiste già ed è a due file di distanza:
                  01-b2-sonda-trasporto.py legge `max_idle_timeout` dal pari.
MARCA:            [R]
```

### R8.4 — Il terzo giro non distingue «rifiuta il secondo» da «si fa spodestare» `[R]`

```
DOVE:             banchi/01-b3-terzo-giro.sh:91-99
COSA CONTRADDICE: l'intestazione dello stesso file (righe 22-25) e 01-b3-lancia.sh:23-26
                  («è la sola prova che distingue "il server rifiuta il secondo" da "il
                  server si fa spodestare"»), l'invariante I2, ed E7
COME SI DIMOSTRA: `wait "$PRIMA"; VIVA=$?` legge il codice d'uscita del primo cliente. Per
                  01-b3-cliente.py:288-291 quel cliente, dopo SESSIONE, dorme 12 secondi e
                  `principale` ritorna 0 — **qualunque cosa sia successa alla connessione nel
                  frattempo**, per la stessa ragione di R8.2. Un server che spodestasse il
                  primo (chiudendogli la sessione per far posto al secondo) lascerebbe
                  `VIVA=0`, e il banco stamperebbe «⭐ e la PRIMA è sopravvissuta: nessun
                  client vivo viene spodestato».
                  ⛔ E la prova esiste, nel file accanto, e si butta: 01-b3-cliente.py:146-150
                  stampa `[wt]   sessione chiusa dal server, codice 0x0f = GIA_ATTIVA_REMOTA`
                  dentro b3-viva.log. Quel file lo si legge solo nel ramo rosso (riga 97,
                  `tail -5`), cioè **solo quando si è già concluso il contrario**.
                  Alla domanda «da quale lato lo osserva»: dal codice d'uscita di un processo,
                  che è il lato in cui il dato non c'è.
MARCA:            [R]
```

⚠ Secondo effetto, indipendente: il primo cliente ha `--resta 12` (riga 45) e la finestra
d'attacco può durare fino a 15 s (righe 61-67). Se il secondo cliente impiegasse più di
~11 s, il primo sarebbe uscito **da solo** prima che il secondo arrivi, e `VIVA=0` non
direbbe niente nemmeno se il codice d'uscita fosse informativo: è un'attesa a tempo fisso al
posto della condizione «la prima era ancora attaccata quando è arrivata la seconda».

### R8.5 — Le registrazioni del terzo giro non si buttano `[R]`

```
DOVE:             banchi/01-b3-terzo-giro.sh:39
COSA CONTRADDICE: il commento di 01-b3-lancia.sh:55-58, che dichiara il difetto già curato:
                  «Il 10 agosto 2026 il validatore ha dichiarato "conforme" un file rimasto
                  da un giro precedente, mentre il cliente di QUESTO giro non si era nemmeno
                  collegato: un verde da un file stantio»
COME SI DIMOSTRA: la riga 39 butta `b3-viva.log`, `b3-terza.log` e `b3-viva.attaccato`, e
                  **non** `b3-viva.rcpreg` né `b3-terza.rcpreg` — che sono i due file che
                  01-b3-cliente.py:266-268 scrive e che 01-b3-lancia.sh:111 (`valida viva`)
                  dà in pasto al validatore.
                  Il caso concreto: si spegne il server e si lancia `01-b3-lancia.sh`. Il
                  terzo giro esce a 01-b3-terzo-giro.sh:72 con codice 3 senza aver scritto
                  nessun `.rcpreg`; `01-b3-lancia.sh:69` trova comunque il file del giro
                  precedente, e il validatore stampa «⭐ conforme». La cura di
                  01-b3-lancia.sh:59 esiste solo per le etichette `uno` e `due`, cioè per i
                  due giri che quel file lancia da sé; sui due che stanno nell'altro file
                  non c'è.
MARCA:            [R]
```

### R8.6 — Il verdetto dell'arbitro non entra nell'esito `[R]`

```
DOVE:             banchi/01-b3-lancia.sh:64-75, e i tre usi alle righe 86, 96, 111
COSA CONTRADDICE: l'intestazione dello stesso file, righe 28-29: «⛔ E ogni traccia passa dal
                  VALIDATORE di B4: è l'arbitro, e non si collauda il server contro il
                  client»; e REVIEWER.md §1 domanda 4
COME SI DIMOSTRA: `bash "$ENTRA" --root "python3 …/01-b4-validatore.py …" | tail -3 | sed …`
                  — con `set -uo pipefail` ma **senza `set -e`**, e soprattutto senza che
                  nessuno legga il valore: `valida` restituisce lo stato di `sed`, che è 0
                  sempre, e i tre chiamanti (righe 86, 96, 111) lo ignorano comunque.
                  La variabile `BENE` si tocca solo alle righe 83, 94 e 109, cioè dai codici
                  d'uscita dei tre clienti.
                  Caso concreto: 01-b4-validatore.py:444-447 stampa «⛔ NON CONFORME — <regola>»
                  e ritorna 1 su tutt'e tre le tracce; 01-b3-lancia.sh:119 stampa lo stesso
                  «⭐ B3: tre giri su tre» ed esce 0. ⚠ Il `tail -3` per giunta taglia
                  l'elenco delle violazioni: quel che si vede è la coda, non il verdetto.
MARCA:            [R]
```

### R8.7 — `APERTA` non vuol dire che i byte tornano `[R]`

```
DOVE:             banchi/01-b2-lancia-sonda.sh:181-196 (il confronto della riga 186)
COSA CONTRADDICE: il ⛔ scritto nella pagina che questo lanciatore conduce —
                  01-b2-sonda.html:156-160: «"ready" non basta: si manda un byte e si
                  aspetta che torni. Una sessione che si apre e non trasporta niente è la
                  forma di verde che questo banco esiste per non produrre» — e
                  DECISIONI.md §6.4, che su questo banco poggia «due browser veri aprono la
                  sessione»
COME SI DIMOSTRA: 01-b2-sonda.html:164-173 avvolge l'andata e ritorno in un `try/catch` suo;
                  se lo stream fallisce si scrive una riga nel dettaglio e **si prosegue** a
                  riga 176-177 con `registra("APERTA", …)`. Lo stesso vale per il caso
                  «⚠ i byte tornano DIVERSI» (riga 171). Il lanciatore legge solo il campo
                  `esito` (righe 182-185) e lo confronta con `APERTA`.
                  ⛔ E la dimostrazione non è un'ipotesi, è nel registro versionato:
                  `banchi/b2-esiti.jsonl`, righe con ora `2026-08-10T09:36:16` (Firefox 140)
                  e `2026-08-10T09:36:32` (Chrome), tutt'e due `"esito": "APERTA"`, tutt'e
                  due con dettaglio «⚠ sessione aperta ma lo stream non ha funzionato:
                  WebTransportError». Su quelle due esecuzioni 01-b2-lancia-sonda.sh:197 ha
                  stampato l'OK.
MARCA:            [R]
```

### R8.8 — «Rifiutato come impone §2.2» è dedotto da un codice d'uscita qualunque `[R]`

```
DOVE:             banchi/01-b2-lancia-wt.sh:136-143 e 159-165
COSA CONTRADDICE: RCP.md §2.2 riga 165 — «Un percorso sconosciuto si rifiuta con **404**» —
                  e la riga 139 di questo stesso script, che quel 404 lo cita: «il rilievo
                  R1.24 ha scelto 404 fra i tre stati che erano leciti». E la forma E1.
COME SI DIMOSTRA: il banco tiene solo `ESITO_NO=$?` e verifica `-ne 0`. Ma
                  01-b2-cliente-aioquic.py ritorna **1** per qualunque `:status` diverso da
                  200 (righe 175-177) e **2** per qualunque eccezione (righe 194-196):
                  timeout della CONNECT, UDP filtrato, server già morto, traceback.
                  Caso concreto: si lascia cadere il traffico UDP verso 7447 fra la prima e
                  la seconda gamba. Il cliente su `/rcp/9` esce 2, e la riga 160 stampa
                  «OK /rcp/9: RIFIUTATO, come impone §2.2». Il controllo che dice NO — quello
                  che l'intestazione (righe 15-20) dichiara essere la ragione d'essere del
                  file, e che «nelle due revisioni del 9 agosto cadeva ogni volta» — non
                  distingue il rifiuto dal fallimento, ed è la domanda 4 di REVIEWER.md §1.
                  ⚠ Il dato giusto passa sotto gli occhi e non si cattura:
                  01-b2-cliente-aioquic.py:170 stampa `risposta alla CONNECT estesa:
                  :status = <n>`; nessuno lo confronta con 404.
MARCA:            [R]
```

### R8.9 — «Sulle due tracce del terzo giro» ne valida una `[R]`

```
DOVE:             banchi/01-b3-lancia.sh:110-111
COSA CONTRADDICE: il testo della riga 110 («e il validatore di B4 sulle due tracce del terzo
                  giro») contro il codice della riga 111 (`valida viva`, una sola);
                  e RCP.md riga 1459: «il congedo — verificato **dal lato che riceve**, per
                  ciascuno dei motivi che viaggiano in un CONGEDO»
COME SI DIMOSTRA: 01-b3-terzo-giro.sh:77-79 fa scrivere al secondo cliente
                  `$QUI/b3-terza.rcpreg`. Quel file contiene la traccia di chi ha RICEVUTO il
                  `CONGEDO(GIA_ATTIVA_REMOTA)`, cioè **l'unico oggetto che il terzo giro
                  esiste per produrre**, e non viene passato al validatore da nessuna parte:
                  `grep -n 'b3-terza' banchi/*.sh` dà solo le righe di 01-b3-terzo-giro.sh.
                  Il solo controllo su quel rifiuto resta il `grep -q` della riga 84, che
                  guarda una stringa stampata e non i byte — e che non distingue un
                  `CONGEDO(0x0F)` da un `RESPINTO(0x0F)`, perché 01-b3-cliente.py:182-185
                  formatta i due casi con la stessa parola.
MARCA:            [R]
```

### R8.10 — Il motore si identifica contando le righe di un registro condiviso `[R]`

```
DOVE:             banchi/01-b2-lancia-sonda.sh:102, 153-159, 181-207
COSA CONTRADDICE: l'intestazione dello stesso file, righe 33-35 («la pagina lo spedisce da sé
                  a 01-b2-raccogli.py, che lo scrive con l'ora e **la versione del motore** —
                  il campo che una trascrizione a mano dimentica sempre»),
                  01-b2-raccogli.py:16-20, e LEZIONI.md §1.9 sul denominatore
COME SI DIMOSTRA: l'attesa (righe 153-159) è soddisfatta da `wc -l >= PRIMA+1`, cioè da
                  **una riga qualunque** apparsa nel registro; l'esito si legge dall'ultima
                  riga (righe 182-185) e il campo `motore` si stampa (riga 202) ma non si
                  confronta mai con il motore in prova.
                  Tre strade concrete che infilano lì la riga sbagliata:
                    a) il ramo di fallimento (righe 162-178) **non incrementa `PRIMA`**;
                       il browser di quel giro non è morto (R8.19: `kill "$p"` uccide
                       `xvfb-run`, non il browser) e la sua POST tardiva arriva mentre
                       gira il motore successivo, che se la prende;
                    b) il registro `b2-esiti.jsonl` è condiviso con B11 —
                       01-b11-lancia.sh:47,63,64,110,131 usano lo stesso file, lo stesso
                       raccoglitore e la stessa porta 8899 — e infatti il file contiene già
                       righe `CONFORME` / `NON-CONFORME` che con B2 non c'entrano;
                    c) il registro non si tronca mai, quindi due esecuzioni sovrapposte si
                       rubano le righe a vicenda.
                  ⛔ Un banco che scrive «chrome ha registrato il suo esito» sotto uno
                  `userAgent` di Firefox è la forma esatta della lezione che questo file cita.
MARCA:            [R]
```

### R8.11 — Il datagram di HTTP/3 misurato al livello di QUIC `[R]`

```
DOVE:             banchi/01-b2-sonda-trasporto.py:112, 141-142
COSA CONTRADDICE: RCP.md §2.2, riga della tabella: «datagram — **DEVONO** essere abilitati
                  sulla connessione **HTTP/3**»; il docstring di questo stesso file (riga 14)
                  che quella riga la ricopia; e la forma E1
COME SI DIMOSTRA: la sonda si collega con `connect(...)` e `alpn_protocols=H3_ALPN` e **non
                  costruisce nessuna `H3Connection`** — quindi non legge nessun SETTINGS. Il
                  valore che chiama «datagram abilitati» è `max_datagram_frame_size`, il
                  parametro di trasporto **QUIC** (RFC 9221). L'impostazione HTTP/3 che
                  §2.2 pretende è `H3_DATAGRAM = 0x33` (RFC 9297), e il file accanto sa
                  benissimo che è un'altra cosa: 01-b2-sonda-impostazioni.py:54 la elenca
                  per nome.
                  Caso concreto: un server che alza `max_datagram_frame_size` sul trasporto e
                  **non** annuncia `H3_DATAGRAM` passa questo controllo, e i datagram
                  dell'audio non partirebbero — il sintomo di `LEZIONI.md` §2.2, «sembra un
                  difetto di rete».
MARCA:            [R]
```

### R8.12 — Il credito «in ogni momento» misurato all'istante zero `[R]`

```
DOVE:             banchi/01-b2-sonda-trasporto.py:114, 144-149
COSA CONTRADDICE: RCP.md §2.3 — «almeno **16** disponibili **in ogni momento**» — citata
                  parola per parola nel commento delle righe 144-147; e la forma E9
COME SI DIMOSTRA: `initial_max_streams_uni` è il credito che il server concede **all'apertura
                  della connessione**, e non dice niente su quel che succede dopo. §2.3 è
                  scritta esattamente per il dopo: «Se il credito finisse, l'input non
                  partirebbe affatto e il sintomo sarebbe "il desktop non risponde"», e
                  RCP.md subito sotto lo dichiara «la forma di difetto che un banco corto
                  **non vede** — funziona per i primi secondi e si ferma dopo
                  (`LEZIONI.md` §1.4)», rimandando al banco di §11 che tiene la sessione viva
                  oltre 256 fotogrammi. Questa sonda apre una connessione, legge un numero e
                  chiude: è il banco corto contro cui quella riga è stata scritta.
                  ⚠ Il verdetto di riga 176 («⭐ 5 controlli su 5») copre quindi una
                  proprietà che non è quella nominata.
MARCA:            [R]
```

### R8.13 — `kill` su un PID che può essere di ieri `[R]`

```
DOVE:             banchi/01-b2-lancia-impostazioni.sh:81-87, con gli usi alle righe 93 e 117;
                  banchi/01-b2-lancia-wt.sh:57-66
COSA CONTRADDICE: la regola scritta in 01-b2-lancia-wt.sh:83 («fermalo per PID, mai con
                  pkill -f»), che vale solo se il PID è verificato; e REVIEWER.md §1
                  domanda 2 (il banco certificato prima di essere usato)
COME SI DIMOSTRA: `ferma bsslserver` alla riga 93 gira **prima** di `avvia`, quindi legge
                  `$FUORI/b2-imp-bsslserver.pid` scritto da un'esecuzione precedente — il
                  file lo cancella solo `avvia` (riga 58) e `ferma` (riga 86), e se una delle
                  due esecuzioni è stata interrotta il file resta. Poi esegue
                  `bash enter.sh --root "kill $p || true"`: **da root, dentro il chroot, senza
                  guardare `/proc/$p/comm`**.
                  Caso concreto: il rootfs del server è vivo in RAM e si riavvia
                  (`v1/strumenti/sshpw.py`, docstring), mentre `/media/REMOTIX/src` è un
                  supporto che sopravvive; al riavvio lo spazio dei PID riparte dal basso e il
                  file punta a un processo di sistema. Il `|| true` fa sì che l'errore non si
                  veda nemmeno.
                  Stessa forma in 01-b2-lancia-wt.sh:57-64, dove per giunta `spegni` non
                  verifica che il processo sia poi morto prima di cancellare il file.
MARCA:            [R]
```

### R8.14 — «In ascolto» concluso da «tiene una porta UDP qualunque» `[R]`

```
DOVE:             banchi/01-b2-lancia-wt.sh:103-109; banchi/01-b2-lancia-impostazioni.sh:70-77
COSA CONTRADDICE: la forma E1 (necessario scambiato per sufficiente), e l'intestazione di
                  01-b2-lancia-wt.sh:45-49, che racconta proprio il difetto di un server a
                  cui gli argomenti arrivano storti
COME SI DIMOSTRA: `ss -ulnp | grep 'pid=$PID,'` è vero per **qualunque** porta UDP tenuta da
                  quel processo, non per `$PORTA`. Un server che ignorasse i suoi argomenti
                  posizionali e si legasse alla sua porta predefinita passerebbe il controllo,
                  e il banco stamperebbe «in ascolto, PID …» su un fatto falso.
                  ⚠ Dove pesa: in 01-b2-lancia-impostazioni.sh:119 la gamba `quiche` — quella
                  su cui DECISIONI.md §6.4 fonda «quiche, usata dal C, non riesce a
                  dichiarare WebTransport» — lancia l'esempio altrui con due argomenti
                  posizionali e verifica solo questo. La sonda poi ritorna 3 e la gamba
                  finisce rossa invece che verde-falsa (01-b2-sonda-impostazioni.py:94-98),
                  quindi il verdetto di §6.4 non è avvelenato; ma la riga «quiche in ascolto,
                  PID p» resta un'affermazione che il banco non ha verificato, ed è a un
                  passo di distanza dal caso in cui lo sarebbe.
                  Il rimedio è nella stessa riga: `grep "pid=$PID," | grep ":$PORTA "`.
MARCA:            [R]
```

### R8.15 — «Porta libera» e «il comando è fallito» hanno lo stesso aspetto `[R]`

```
DOVE:             banchi/01-b2-lancia-wt.sh:79-86; 01-b2-lancia-trasporto.sh:55-61;
                  01-b2-lancia-impostazioni.sh:42-53
COSA CONTRADDICE: LEZIONI.md §1.9 / E8 (il silenzio scambiato per zero), e REVIEWER.md §1
                  domanda 4
COME SI DIMOSTRA: `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` cattura solo lo
                  standard output. `enter.sh` ha `set -euo pipefail` (riga 20) e può uscire
                  non-zero su un `mount` fallito o su una credenziale scaduta; `ss` può non
                  esserci nel chroot; `grep` esce 1 quando non trova. Tutt'e quattro gli esiti
                  producono `CHI=""`, e la riga 86 stampa «OK porta $PORTA libera».
                  Il caso concreto: si smonta `/media/REMOTIX/devroot/proc` e si rilancia —
                  `enter.sh` fallisce, il banco dichiara la porta libera, lancia un secondo
                  server sopra il primo, e il rosso che segue arriva su un imputato sbagliato.
                  ⚠ È la stessa forma che il file combatte alla riga 96 (`/proc` invece di
                  `kill -0`, «per non leggere "operazione non permessa" come "non esiste"»):
                  qui si legge «non ho potuto guardare» come «non c'è niente».
MARCA:            [R]
```

### R8.16 — Il ramo «non ho l'impronta» è irraggiungibile `[R]`

```
DOVE:             banchi/01-b2-lancia-sonda.sh:81, 89-97
COSA CONTRADDICE: sé stesso: la riga 93 (`if [ -z "$IMPRONTA" ]`) e il suo messaggio non
                  possono essere raggiunti
COME SI DIMOSTRA: `grep -oE '[A-Za-z0-9+/]{43}='` produce, per costruzione, solo stringhe di
                  **44** caratteri o niente. Quindi il test della riga 89 (`-ne 44`) è vero
                  se e solo se `IMPRONTA` è vuota, ed esce a riga 91 con «l'impronta ha 0
                  caratteri invece di 44: è tagliata» — che è la diagnosi dell'altro difetto.
                  Il caso concreto è quello che conta: il server non si accende, `acceso.log`
                  non contiene nessuna impronta, e il banco accusa un taglio invece di dire
                  «non ho l'impronta». ⚠ È «il silenzio scambiato per un errore diverso»: la
                  causa vera (nessuna impronta) e la causa cercata (impronta troncata) escono
                  dallo stesso ramo con il nome della seconda.
                  Nota accanto: la regex accetta anche 43 caratteri qualunque seguiti da `=`
                  presi **dentro** una stringa più lunga; `tail -1` sceglie l'ultima
                  occorrenza del registro, non l'impronta per nome.
MARCA:            [R]
```

---

## 3. I sospetti, da misurare `[?]`

### R8.17 — Il controllo negativo del quinto giro passa per qualunque ragione `[?]`

```
DOVE:             banchi/01-b3-quinto-giro.sh:96-103
COSA CONTRADDICE: 01-b2-sonda.html:181-186, che elenca da sé «tre cause con lo stesso
                  aspetto, e vanno distinte a mano»; e la forma E1
COME SI DIMOSTRA: il tempo 4 conclude «⭐ rifiutata: il browser CONFRONTA l'impronta» da
                  `esito == NON-APERTA`, che la pagina registra per qualunque eccezione di
                  `wt.ready`: UDP filtrato, server non riacceso, certificato oltre i 14
                  giorni, impronta sbagliata. Il campo `dettaglio` contiene l'eccezione e il
                  lanciatore lo stampa senza leggerlo (01-b2-lancia-sonda.sh:188-193).
                  ⚠ Perché resta `[?]` e non `[R]`: il tempo 3 gira poco prima con la stessa
                  catena e, se cadesse per una di quelle cause, sarebbe rosso — quindi il
                  falso verde richiede un guasto che compaia **fra** i due tempi. È
                  possibile (i due tempi riaccendono il server ciascuno per conto suo) ma
                  non l'ho potuto costruire dalla sola lettura.
MARCA:            [?]
```

### R8.18 — «Niente 0-RTT» da un'attesa fissa, senza controllo positivo nel giro `[?]`

```
DOVE:             banchi/01-b2-sonda-trasporto.py:96-98, 166-170, 191
COSA CONTRADDICE: REVIEWER.md §1 domanda 5 (lo strumento sa trovare qualcosa che c'è di
                  sicuro, prima di concludere che qualcosa non c'è?)
COME SI DIMOSTRA: la conclusione «niente 0-RTT» si regge su `await asyncio.sleep(1.5)` e su
                  una lista vuota. Il controllo positivo c'è ed è dichiarato onestamente
                  (righe 160-165: «al primo giro il server d'esempio ha mandato due biglietti
                  con max_early_data_size = 4294967295») — ma è di **un'esecuzione
                  precedente e di un server precedente**: nel giro che si sta eseguendo,
                  «zero biglietti» e «non ho aspettato abbastanza» e «il gancio non viene
                  più chiamato» hanno tutt'e tre lo stesso aspetto.
                  Va misurato: alzare `--attesa-biglietto` e vedere se il numero cambia, e/o
                  ripuntare la sonda su un server con 0-RTT acceso **nello stesso giro**.
MARCA:            [?]
```

### R8.19 — `kill` sull'involucro non uccide il browser `[?]`

```
DOVE:             banchi/01-b2-lancia-sonda.sh:149, 160-161, e il trap di riga 117
COSA CONTRADDICE: il ⛔ delle righe 113-116 dello stesso file: «il profilo usa-e-getta si
                  BUTTA davvero … "Usa-e-getta" era solo la prima metà»
COME SI DIMOSTRA: `$p` è il PID di `xvfb-run`, che è uno script di shell: lancia `Xvfb` in
                  secondo piano e poi esegue il browser come figlio, senza `exec`. Un
                  `kill "$p"` termina la shell; il browser e `Xvfb` restano, orfani. Poi il
                  trap fa `rm -rf "$TEMP"` **sotto un browser vivo**.
                  Conseguenze da misurare: (a) i processi si accumulano fra le esecuzioni,
                  cioè la stessa forma dei 740 MB del 10 agosto; (b) è il meccanismo che
                  rende concreta la strada (a) di R8.10.
                  Perché `[?]`: non ho potuto eseguire `pgrep` dopo un giro per contarli.
MARCA:            [?]
```

### R8.20 — Attese a tempo fisso al posto della condizione osservata `[?]`

```
DOVE:             banchi/01-b2-lancia-wt.sh:93; 01-b2-lancia-impostazioni.sh:61;
                  01-b2-lancia-trasporto.sh:65 e 80; 01-b2-lancia-sonda.sh:106
COSA CONTRADDICE: la pratica che questo stesso insieme di banchi ha già scritto altrove —
                  01-b2-lancia-sonda.sh:151-159 aspetta che il registro cresca, e
                  01-b3-terzo-giro.sh:49-67 aspetta un file: «⭐ Un file scritto e chiuso è
                  un fatto»
COME SI DIMOSTRA: dopo `sleep 2` il banco decide, e in caso di server lento conclude «non è
                  partito» (o «non tiene nessuna porta») su un server che stava partendo. La
                  condizione osservabile esiste già ed è la riga sotto: la comparsa della
                  porta in `ss`. Simmetricamente 01-b2-lancia-trasporto.sh:78-80 fa `kill` e
                  `sleep 1`, e il secondo giro riparte sperando che la porta sia sparita.
                  ⚠ Ha un secondo effetto sul carattere del banco: rende i giri **non
                  ripetibili uguali**, che è la condizione dichiarata in
                  01-b2-sonda.html:189-195 per poter dire che una misura è cambiata perché è
                  cambiato il server.
MARCA:            [?]
```

---

## 4. Che cosa ho provato a rompere e non ci sono riuscito

*Dichiarato, perché `PIANO.md` §0.4 lo chiede: anche il fallimento di un attacco è
informazione. ⚠ E `REVIEWER.md` §0: quel che segue non è un'assoluzione.*

| Che cosa ho attaccato | Perché non è caduto |
|---|---|
| **La gamba `quiche` di `DECISIONI.md` §6.4** — cioè «non dichiara WebTransport» che potrebbe essere «non mi sono collegato» | `01-b2-sonda-impostazioni.py:89-106` separa i due casi in modo esplicito: eccezione → 3, elenco vuoto → 3, elenco non vuoto senza le due impostazioni → verdetto. E `01-b2-lancia-impostazioni.sh:137` pretende **0**, non «non-zero». Il silenzio non può passare per uno zero |
| **Il controllo positivo della sonda delle impostazioni** | C'è, ed è prima: `01-b2-lancia-impostazioni.sh:90-103` misura `ngtcp2` col nostro strato e, se fallisce, esce a riga 135 senza scrivere niente su §6.4. È la domanda 5 di `REVIEWER.md` §1, soddisfatta |
| **`received_settings` letto dal lato sbagliato** (E7) | `01-b2-sonda-impostazioni.py:72` legge `H3Connection.received_settings`, cioè il SETTINGS **del pari**; l'`enable_webtransport=True` di riga 66 riguarda quel che manda il client e non entra nel verdetto |
| **Il denominatore zero della sonda dei browser** | C'è il conteggio, ed è dichiarato: `01-b2-lancia-sonda.sh:128,141,242-247` — `PROVATI`, con l'uscita 6 se è zero. Il salto per browser assente si stampa. Questa è la forma di verde vuoto che il mandato chiedeva di cercare, e **qui è chiusa** |
| **`shift 3` con meno di tre argomenti** in `01-b2-lancia-wt.sh` | Curato e commentato alle righe 45-55, e i chiamanti passano tre argomenti (`01-b2-lancia-sonda.sh:57`) |
| **`/proc/$PID` letto da fuori mentre il processo gira dentro il contenitore** | `v1/banco/enter.sh` usa `chroot`, non uno spazio dei nomi dei PID: i numeri sono gli stessi da tutt'e due i lati. La scelta di `/proc` invece di `kill -0` (commento a `01-b2-lancia-wt.sh:95-97`) regge |
| **Lo stato d'uscita perso attraverso `enter.sh` e `sshpw.py`** | `enter.sh` finisce con `sudo chroot …` come ultimo comando e non ha `exec`, quindi propaga; `sshpw.py:esegui` ritorna `os.waitstatus_to_exitcode`. `ESITO_SI=$?` e `E1=$?` leggono davvero il codice del programma remoto |
| **La sottoshell in secondo piano che si porta via la richiesta di password di `sudo`** | Curata dividendo i file: `01-b3-lancia.sh:101-106` chiama `01-b3-terzo-giro.sh` con una riga sola, e dentro il contenitore non c'è nessun `sudo`. Non ho trovato un `$( … enter.sh … )` né un `enter.sh … &` in nessuno dei dodici file d'area |
| **Il segnale «attaccato» letto da una riga di registro non ancora scaricata** | Curato in tutt'e due i posti: `01-b3-cliente.py:285-287` scrive e chiude un file, e `01-b3-terzo-giro.sh:61-67` / `01-b3-quarto-giro.sh:64-68` aspettano **quel file**. Il `python3 -u` c'è dove serve |
| **Il registro del terzo giro giudicato mentre il buffer è ancora pieno** | `01-b3-cliente.py:266-268` scrive la registrazione **prima** del segnale e della dormita, e la chiude col `with` |
| **La porta della pagina (8899) già occupata da un raccoglitore di ieri** | `ThreadingHTTPServer` non riesce a legarsi a una porta con un socket in ascolto, il processo muore e `01-b2-lancia-sonda.sh:107-111` lo vede sparito entro un secondo. ⚠ Non l'ho potuto misurare, ma il ramo esiste |
| **Il conteggio delle richieste al raccoglitore usato come denominatore** | `01-b2-raccogli.py:68-79` scrive una riga per **ogni** richiesta e `01-b2-lancia-sonda.sh:173` conta `^richiesta: ` con `grep -c`, non le occorrenze del nome del file. La cura del 10 agosto tiene |
| **`ATTESO` che scivola fra i due tempi del quinto giro** | I due valori (`APERTA`, `NON-APERTA`) combaciano esattamente con le stringhe che la pagina registra (`01-b2-sonda.html:177,188`), e il caso «niente WebTransport» ha una terza etichetta sua (riga 118), quindi non si confonde con un rifiuto per impronta |
| **La rotazione del quinto giro che non avviene** | `01-b3-quinto-giro.sh:75-79` confronta le due impronte ed esce 4 se sono uguali. È il controllo giusto, ed è nel posto giusto |

---

## 5. Il filo che lega i primi sei rilievi

⛔ **B3 ha tre osservatori, e tutti e tre guardano dal lato sbagliato.**

| Che cosa si vuole sapere | Da dove lo si legge oggi | Dove sta davvero |
|---|---|---|
| la terza è entrata dopo il silenzio | una parola dentro un messaggio d'errore (`R8.1`) | il codice d'uscita del cliente, che c'è e si butta; o il `SESSIONE` nella registrazione |
| la prima è ancora connessa | l'esistenza di un processo che dorme (`R8.2`, `R8.4`) | la riga `[wt] sessione chiusa dal server` in `b3-viva.log`, che c'è e si butta |
| il tetto d'inattività è 120 s | l'intestazione di un file (`R8.3`) | il filo, con `01-b2-sonda-trasporto.py`, che c'è e non si chiama |
| la traccia è conforme | l'occhio di chi legge il terminale (`R8.6`) | il codice d'uscita del validatore, che c'è e lo mangia un `tail` |
| il secondo è stato congedato con 0x0F | una stringa stampata (`R8.9`) | `b3-terza.rcpreg`, che si scrive e non si valida |

In tutt'e cinque le righe **il dato giusto esiste già, sullo stesso disco, nello stesso giro**.
Non manca uno strumento: manca la riga che lo legge. Ed è la ragione per cui questi rilievi
sono `[R]` e non `[?]` — non serve misurare niente per stabilire che il banco sta guardando
un'altra cosa.

⚠ E la conseguenza su `MANDATO-10-agosto.md` §3 punto 6 («B11 ha dato verdetti diversi fra
giri identici … non è dimostrato che fossero le sole»): `R8.10` mostra che B2, B3 e B11
condividono un registro, un raccoglitore e una porta, e che l'identità di chi ha scritto
l'ultima riga non si verifica in nessuno dei tre. È un candidato per quella causa che manca,
e si chiude con un confronto su un campo che è già nel file.
