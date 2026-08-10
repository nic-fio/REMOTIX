# R5 — revisione avversariale del banco B11 (lo strumento che giudica la pagina)

**Area**: `banchi/01-b11-lancia.sh`, `banchi/01-b11-guasto.sh`,
`banchi/01-b11-guasto-innesta.py`.
**Letti prima**: `REVIEWER.md` (intero), `fasi/rapporti/MANDATO-10-agosto.md` (intero).
**Letti come arbitri e come «altro pezzo di codice»**: `banchi/01-b2-lancia-wt.sh`,
`banchi/01-b2-raccogli.py`, `banchi/01-b11-pagina.html`, `banchi/rcp/rcp.c`,
`banchi/01-b3-rcp-innesta.py`, `banchi/01-b2-ngtcp2-wt-innesta.py`.

⚠ Non ho eseguito niente e non ho misurato niente: ogni «come si dimostra» è un
ingresso concreto costruito leggendo il codice, non un esito osservato.
Nessun rilievo porta `[M]`.

---

## 0. Le cinque domande di `REVIEWER.md` §1, in breve

| domanda | risposta letta nel codice |
|---|---|
| 1. la scena si dichiara e si muove? | non pertinente: B11 non misura fotogrammi. I tredici casi dichiarano l'atteso **prima** (`01-b11-pagina.html:358-385`), e questo è a posto. |
| 2. il banco è certificato prima dell'uso? | **no**: il «controllo che dice NO» è soddisfatto da qualunque fallimento, e può essere saltato in silenzio → R5.3, R5.16. |
| 3. riproduce davvero il difetto? | il server guasto esiste ed è vero; ma **non è verificato** che i guasti innestati siano quelli di questo giro → R5.10, R5.11, R5.12. |
| 4. distingue lo zero dal fallimento? | **no** in almeno cinque punti → R5.4, R5.5, R5.9, R5.14, R5.15. |
| 5. ha un controllo positivo? | c'è (`CON`, il congedo di §8.1), ma il suo verdetto è dichiarato senza essere misurato → R5.5, R5.7. |

---

## 1. I rilievi `[R]`

---

### R5.1

```
DOVE:             banchi/01-b11-guasto.sh:101  (azione «spegni», `ricostruisci sano`)
COSA CONTRADDICE: il commento dello stesso file, righe 55-65 — «"Il file c'e'" e
                  "il file e' quello che ho appena costruito" sono due domande
                  diverse, e solo la seconda ha un denominatore» — applicato in
                  `accendi` (riga 127) e NON in `spegni`; e l'intestazione del
                  file, righe 10-19 («un server che mente di proposito non deve
                  sopravvivere alla fase»).  Forma E1 e E7.
COME SI DIMOSTRA: `ricostruisci` restituisce lo stato di `ninja` (righe 66-67).
                  In `accendi` è letto (`if ! ricostruisci con-guasti`); in
                  `spegni` è **buttato**: `ricostruisci sano` è una istruzione
                  nuda.  Ingresso concreto: si fa fallire la ricostruzione del
                  server sano — basta che `01-b3-rcp-innesta.py` esca con 2
                  («N appigli non sono UNO: non si scrive niente», riga 733-735)
                  oppure che il suo `--togli` abbia già rimosso `rcp.c` e la
                  riapplicazione non riesca: la compilazione fallisce e sul
                  disco resta **il binario guasto**.  `spegni` prosegue, trova
                  il sorgente pulito (grep alla riga 102), stampa
                  «⭐ nessuna traccia di B11 nel sorgente: il server e' quello
                  vero» ed esce 0.  Il prossimo
                  `01-b2-lancia-wt.sh accendi` accende quel binario — che è
                  esattamente lo scenario descritto, e dichiarato pericoloso, in
                  `01-b11-lancia.sh:155-161`.
MARCA:            [R]
```

Nota: `spegni` verifica il **sorgente**, cioè il lato che non conta. Quel che
sopravvive alla fase è il binario e il processo, non il testo `.c`.

---

### R5.2

```
DOVE:             banchi/01-b11-lancia.sh:78-84 (`ripulisci`, `trap ... EXIT`),
                  e la stessa forma alla riga 163
COSA CONTRADDICE: `01-b2-raccogli.py:9-14`, che cita la regola B0.4 — «l'atteso
                  lo confronta il banco, non chi legge»; e l'intestazione di
                  `01-b11-guasto.sh` («un interruttore così, se sopravvive alla
                  fase, un giorno lo trova acceso qualcuno»).
COME SI DIMOSTRA: `spegni` ha un esito di fallimento vero e proprio: esce **5**
                  con «⛔ RESTANO $QUANTI righe di B11 nel sorgente»
                  (`01-b11-guasto.sh:106-108`).  In `ripulisci` quell'esito
                  attraversa `2>&1 | sed 's/^/        /'`: nessuno lo prova, e
                  comunque la funzione gira dentro un `trap ... EXIT` invocato
                  **dopo** `exit "$ESITO"` (riga 292), quindi non può più
                  cambiare il codice d'uscita.  Ingresso concreto: si lascia una
                  riga `REMOTIX B11 GUASTO` in `http3_server_proto_codec.cc` (è
                  proprio il caso che il difetto noto n.1 del mandato rende
                  probabile: `--togli` che non toglie).  Il banco stampa
                  «⭐ B11: la pagina applica §3 …» ed **esce 0**, e la
                  segnalazione della ripulitura fallita compare **dopo** la riga
                  verde, affidata all'occhio di chi legge.
                  Stessa forma alla riga 163: lo `spegni` che deve rimettere il
                  binario sano *prima del controllo* è anch'esso in una pipeline
                  (`| tail -3 | sed`) e il suo stato non è mai provato, benché il
                  commento immediatamente sopra (155-161) spieghi perché quello
                  è il punto in cui il rosso finirebbe sull'imputato sbagliato.
MARCA:            [R]
```

---

### R5.3

```
DOVE:             banchi/01-b11-lancia.sh:150-178 (§2, «IL CONTROLLO CHE DICE NO»)
COSA CONTRADDICE: `REVIEWER.md` §1 domanda 2 e domanda 4; `LEZIONI.md` §1.9;
                  forma E8 («il silenzio scambiato per zero»).  E contraddice il
                  proprio commento, riga 151-152: «nessuno dei dodici casi puo'
                  passare».
COME SI DIMOSTRA: due ingressi, tutt'e due concreti.
                  (a) Il controllo passa confrontando **una sola stringa**:
                  `visto != NON-CONFORME` (riga 141).  Ma la pagina scrive
                  `NON-CONFORME` non appena `guasti > 0`
                  (`01-b11-pagina.html:548,558`), e `guasti` conta ogni caso il
                  cui `fatto` differisce dall'atteso — compreso
                  `fatto = "errore:WebTransportError"` per tutti e tredici.
                  Ingresso: un'impronta del certificato stantia nel `?impronta=`
                  (la si estrae da `sano.log` alla riga 170, e basta che
                  `01-b2-certificati.sh` abbia ruotato la chiave nel frattempo).
                  Nessuna sessione WebTransport si apre, la pagina non legge un
                  byte di RCP, e il banco stampa
                  «OK controllo: NON-CONFORME, come atteso».  ⛔ Cioè: il
                  controllo che deve provare «la pagina sa dire di NO» è
                  soddisfatto da una pagina che non ha detto niente.
                  (b) Il dato che distinguerebbe i due casi **c'è ed è
                  inutilizzato**: la pagina spedisce `casi: [{nome, atteso,
                  fatto, ok}, …]` (riga 562 della pagina), e il banco legge solo
                  `.esito` (riga 130).
                  (c) Il commento della riga 152 è per giunta falso: contro il
                  server SANO i casi `sessione-desktop-kde`,
                  `sessione-desktop-gnome` e `silenzio` hanno atteso
                  `"prosegue"` e **passano**, perché un server sano fa proprio
                  quel che chiedono.  Il banco non se ne accorge perché guarda
                  solo l'esito aggregato.
                  (d) A differenza del giro contro il guasto, il controllo non
                  ha **nessun denominatore**: `b2-wt.log` non viene mai letto,
                  e il conteggio `SERVITI` (riga 215) riguarda solo il server
                  guasto.
MARCA:            [R]
```

---

### R5.4

```
DOVE:             banchi/01-b11-lancia.sh:215-222 (`SERVITI`)
COSA CONTRADDICE: `LEZIONI.md` §1.9 (quarta regola, il denominatore) e il
                  commento della riga 119-121 dello stesso file, che chiama
                  «IL DENOMINATORE» proprio questo genere di conteggio.
COME SI DIMOSTRA: il banco conosce il numero esatto che deve trovare — 13 casi
                  × `ATTESI` motori — e lo confronta **solo con zero**
                  (`if [ "${SERVITI:-0}" -eq 0 ]`).  Ingresso concreto: un giro
                  in cui la pagina abbandona dopo il primo caso (per esempio
                  `WebTransport` che smette di aprire sessioni dopo il primo
                  `close()`): `SERVITI` vale 1, il banco stampa
                  «ok guasti serviti: 1» e prosegue verso il verde.  È lo stesso
                  contatore che il difetto noto n.3 del mandato ha già colto a
                  mentire (26 → 21) senza che nessuno se ne accorgesse: quella
                  volta il colpevole era la finestra, ma il motivo per cui la
                  bugia è passata è che **nessuno confronta quel numero con
                  niente**.
MARCA:            [R]
```

---

### R5.5

```
DOVE:             banchi/01-b11-lancia.sh:271-273
COSA CONTRADDICE: `REVIEWER.md` §0 («il verdetto è sempre "questo contraddice
                  X", mai "questo è giusto"») e il commento delle righe 244-248
                  dello stesso file, che dichiara le due strade come la cosa da
                  misurare.
COME SI DIMOSTRA: il ramo verde stampa
                  «⭐ … e ⛔ per DUE strade diverse — §3.1 punto 3 non e'
                  ridondanza, e' l'altra strada» sulla sola condizione
                  `CON -eq ATTESI`.  `CANALE` e `CHIUSURA` sono **calcolati e
                  mai provati**.  Ingresso concreto: due motori che si congedano
                  tutt'e due sul canale di controllo → `CANALE=2`,
                  `CHIUSURA=0`, `CON=2=ATTESI` → il banco afferma, in verde, una
                  cosa che i suoi stessi numeri smentiscono nella riga
                  immediatamente sopra (riga 266).
                  Seconda faccia dello stesso ramo: con `ATTESI=0` (vedi R5.16)
                  il confronto diventa `CON -eq 0` → vero, e il banco stampa
                  «⭐ il congedo di §8.1 arriva ogni volta: 0 su 0».  Un
                  controllo positivo che si dichiara superato con zero
                  osservazioni non è un controllo positivo (`REVIEWER.md` §1
                  domanda 5).
MARCA:            [R]
```

---

### R5.6

```
DOVE:             banchi/01-b11-lancia.sh:108-114 e 128-140 (`prova_motore`)
COSA CONTRADDICE: `LEZIONI.md` §1.9; e il proprio scopo dichiarato alla riga 141
                  («$nome: esito $visto»), che attribuisce a UN motore un esito
                  che non è legato a quel motore.
COME SI DIMOSTRA: l'attesa è su un **conteggio di righe** di
                  `banchi/b2-esiti.jsonl` (`wc -l >= PRIMA+1`), il verdetto si
                  legge da `tail -1` / `splitlines()[-1]` dello stesso file, e
                  niente lega le due cose allo stesso record: il JSON porta il
                  campo `motore` (`01-b11-pagina.html:560`) e il banco non lo
                  guarda mai.  Ingressi concreti:
                  (a) `b2-esiti.jsonl` è il registro **condiviso** di tutto B2
                  (`01-b2-raccogli.py:34`): una qualunque altra sonda che scriva
                  lì durante il giro fa uscire il ciclo di attesa su una riga
                  altrui;
                  (b) `kill "$p"` (riga 115) uccide `xvfb-run`, non il browser
                  che `xvfb-run` ha avviato: un browser sopravvissuto al giro
                  precedente può depositare il suo POST dopo. In tutt'e due i
                  casi il motore successivo esce dal ciclo con `i=0` e il banco
                  stampa «chrome: CONFORME, come atteso (dopo 0 secondi)»
                  leggendo l'esito **di un altro giro**.
MARCA:            [R]
```

---

### R5.7

```
DOVE:             banchi/01-b11-lancia.sh:255-264 (il blocco `awk`, la variabile `visto`)
COSA CONTRADDICE: il difetto noto n.6 del mandato («B11 ha dato verdetti diversi
                  fra giri identici … non è dimostrato che le due cause curate
                  fossero le sole»); e la classificazione dichiarata alle
                  righe 244-248.
COME SI DIMOSTRA: dentro il blocco di `respinto-poi-congedo` l'`awk` conta
                  **solo la prima** riga «CONGEDO di commiato» (`&& !visto`) e
                  la classifica su `index($0, "seconda strada")`.  Ma un motore
                  che usa tutt'e due le strade produce **due** righe distinte:
                  `banchi/rcp/rcp.c:1056` (il CONGEDO arrivato sul canale) e
                  la riga innestata da `01-b3-rcp-innesta.py:392-396` in
                  `wt_chiusa_dal_client` (il codice di chiusura).  La pagina fa
                  esattamente le due cose una dietro l'altra in `chiudi()`:
                  `manda(T_CONGEDO, …)` e poi `wt.close({closeCode: motivo})`
                  (`01-b11-pagina.html:246-255`).  Quale delle due righe finisce
                  prima nel registro dipende da come il trasporto consegna i
                  byte e la capsula di chiusura: **il verdetto `CANALE` /
                  `CHIUSURA` è deciso da chi arriva primo**, non da quel che la
                  pagina ha fatto.  Con la stessa struttura il banco non può, in
                  linea di principio, osservare «due strade per lo stesso
                  motore»: la seconda riga viene scartata.
MARCA:            [R]
```

---

### R5.8

```
DOVE:             banchi/01-b11-guasto.sh:45-54 (`ricostruisci`)
COSA CONTRADDICE: il difetto noto n.1 del mandato, che indica proprio questa
                  funzione come il punto che «si appoggia a quel --togli per
                  rimettere il server sano»; e `REVIEWER.md` §1 domanda 4.
COME SI DIMOSTRA: le quattro invocazioni (righe 47-50) hanno tutte
                  `> /dev/null` **dentro** il comando remoto e nessuna prova
                  dello stato d'uscita.  I due innesti hanno un cortocircuito
                  che stampa «⚠ l'innesto c'e' gia': non si tocca niente» e
                  restituisce **0** (`01-b2-ngtcp2-wt-innesta.py:837-840`,
                  `01-b3-rcp-innesta.py:683-685`); `01-b3-rcp-innesta.py`
                  restituisce **2** quando gli appigli non sono unici (riga 735).
                  Ingresso concreto: si fa fallire il `git checkout -- examples`
                  di `01-b2-ngtcp2-wt-innesta.py:821-824` (albero non pulito,
                  permessi, `git` assente).  La marca `REMOTIX B3` resta nel
                  `.cc`, `01-b3-rcp-innesta.py` esce **prima di ricopiare
                  `rcp.c`** (il cortocircuito è alla riga 683, la copia alla
                  690-691), e il banco non vede né il messaggio né il codice.
                  ⛔ La ricostruzione del sorgente sano — l'unica cosa che
                  impedisce al server bugiardo di sopravvivere alla fase — non
                  ha nessun testimone.
MARCA:            [R]
```

---

### R5.9

```
DOVE:             banchi/01-b11-lancia.sh:214, 223-229 (`DOPO`), letto dentro
                  la finestra di banchi/01-b11-guasto.sh:92-93 (`tail -600`)
COSA CONTRADDICE: il commento di `01-b11-guasto.sh:88-91 — «il tetto c'e'
                  ancora, ma sta sopra a quel che il banco produce, e se un
                  giorno lo tocca il conto dei casi se ne accorge da se'».  E il
                  difetto noto n.3 del mandato, di cui questa è l'altra faccia.
COME SI DIMOSTRA: la garanzia dichiarata è falsa nella direzione che conta.
                  `tail -600` scarta le righe **più vecchie**, cioè quelle del
                  **primo** motore.  Il conto dei casi (`CASI`) se ne accorge
                  solo quando il taglio arriva a mangiare una riga
                  «guasto chiesto … respinto-poi-congedo»; una singola riga
                  «⛔ N byte arrivati DOPO la fine della sessione»
                  (`banchi/rcp/rcp.c:1063`) del primo motore esce dalla finestra
                  **molto prima**, perché sta più in alto.  Ingresso concreto:
                  un giro che produca 610 righe filtrate con una violazione di
                  §4.4 di Firefox fra le prime dieci → `DOPO=0` → il banco
                  stampa «⭐ nessun byte e' arrivato dopo la fine della sessione
                  (§4.2, §4.4)» mentre ce n'è stato uno.  ⛔ È il verde più
                  vuoto che ci sia: quello che non ha bisogno che sia successo
                  niente, e che questo stesso banco dichiara di voler evitare
                  (righe 231-236).
MARCA:            [R]
```

---

### R5.10

```
DOVE:             banchi/01-b11-guasto.sh:102 (in `spegni`) e :134 (in `accendi`)
COSA CONTRADDICE: `banchi/01-b11-guasto-innesta.py:45-254`, che innesta in
                  **tre** file (`rcp.c`, `http3_server_proto_codec.cc`,
                  `http3_server_proto_codec.h`); forma E1 (necessario preso per
                  sufficiente).
COME SI DIMOSTRA: `SORG` è un file solo
                  (`examples/http3_server_proto_codec.cc`, riga 29), e su quel
                  file solo si decide sia «i guasti ci sono» (accendi) sia
                  «nessuna traccia di B11» (spegni).  Dei tredici guasti, dieci
                  vivono in `rcp.c` (innesti 1-7 della lista) e uno
                  nell'header.  Ingresso concreto per il lato `accendi`: si
                  cancella dalla lista `INNESTI` un innesto di `rcp.c` (o lo si
                  fa saltare) lasciando i due del `.cc`: `QUANTI` vale 2, il
                  banco stampa «costruito, e i guasti ci sono», e i casi che
                  quel guasto doveva provocare falliscono con il rosso puntato
                  sulla **pagina**.  È la stessa forma del difetto che il
                  commento delle righe 55-65 dichiara di aver curato — curato
                  per la domanda «il binario è nuovo?», non per la domanda «i
                  guasti che credo di aver innestato ci sono tutti?».
MARCA:            [R]
```

---

### R5.11

```
DOVE:             banchi/01-b11-guasto-innesta.py:258-262 (`--togli`)
COSA CONTRADDICE: la riga 4 dello stesso file — «python3
                  01-b11-guasto-innesta.py --togli    li toglie» — e il difetto
                  noto n.1 del mandato, di cui questa è un'altra faccia, per
                  costruzione.
COME SI DIMOSTRA: il ramo `--togli` stampa tre righe e fa `return 0`.  Non apre
                  nessun file, non tocca `rcp.c`, non tocca il `.cc`, non tocca
                  il `.h`.  Ingresso concreto: `python3
                  01-b11-guasto-innesta.py --togli && grep -c 'REMOTIX B11
                  GUASTO' examples/rcp.c` → esce 0 e stampa 7.  Un comando che
                  dichiara di togliere, non toglie, e **restituisce successo**:
                  è esattamente il difetto già pagato su
                  `01-b3-rcp-innesta.py --togli`, riscritto qui in forma pura.
                  Che oggi nessuno lo chiami non lo rende innocuo: la riga 4 è
                  l'istruzione d'uso che leggerà chi troverà questo file fra sei
                  mesi.
MARCA:            [R]
```

---

### R5.12

```
DOVE:             banchi/01-b11-guasto-innesta.py:270-272 (la guardia
                  «c'e' gia'»)
COSA CONTRADDICE: il messaggio che quella stessa riga stampa («c'e' gia'», che
                  implica «non si riapplica»); e il proprio invariante
                  dichiarato alle righe 281-285 («un innesto a meta' produce un
                  server che sbaglia in un modo diverso da quello che il banco
                  crede di misurare»).
COME SI DIMOSTRA: la guardia è `MARCA in testo AND appiglio not in testo`.  Tre
                  innesti conservano il proprio appiglio **dentro il
                  sostituto**, per costruzione:
                  n.1 `"\tchar audio[32];\n"` (riga 49-50),
                  n.2 `'\t\tif (strcmp(nome, "video.codec") == 0)\n'` (righe 59,66),
                  n.7 la riga di `rcp_utente` (righe 189-190).
                  Su un `rcp.c` già guasto la guardia è falsa per tutt'e tre
                  (l'appiglio c'è ancora), `n == 1`, e l'innesto **si riapplica**.
                  Ingresso concreto: due esecuzioni di
                  `01-b11-guasto-innesta.py` di fila sullo stesso albero →
                  `char guasto[64];` dichiarato due volte e `rcp_guasto`
                  definita due volte (errore di compilazione, cioè un rosso
                  senza nome), oppure — se passa — la riga
                  `⚠ B11 GUASTO: guasto chiesto dal client` scritta **due volte
                  per caso**, che raddoppia `SERVITI` e `CASI` in
                  `01-b11-lancia.sh` e manda in rosso il confronto
                  `CASI -ne ATTESI` addossandolo alla pagina.
MARCA:            [R]
```

---

### R5.13

```
DOVE:             banchi/01-b11-guasto.sh:148-157 (accensione del server guasto)
COSA CONTRADDICE: `banchi/01-b2-lancia-wt.sh:103-108`, che dopo la stessa
                  accensione verifica `ss -ulnp | grep 'pid=$PID,'` e spiega
                  perché («il server e' vivo ma non tiene nessuna porta UDP»);
                  forma E1.
COME SI DIMOSTRA: B11 conserva la metà del controllo (`[ ! -d "/proc/$PID" ]`)
                  e butta l'altra metà.  Due conseguenze concrete:
                  (a) «il processo è vivo» viene usato come se fosse «il
                  processo è in ascolto su 7447»: un server che sia ancora vivo
                  a 2 s ma abbia già fallito il `bind` (o che stia per uscire)
                  fa stampare «ok server GUASTO in ascolto, PID $PID», e tutti e
                  tredici i casi falliscono con il rosso sulla pagina;
                  (b) `$PID` è `$!` **dentro** `bash enter.sh --root`, cioè il
                  PID visto dal contenitore, mentre `/proc/$PID` è letto **fuori**
                  dal contenitore (riga 152 non passa da `$ENTRA`, a differenza
                  delle righe 118, 129, 134, 161).  Se il contenitore ha uno
                  spazio dei PID suo, il controllo interroga un processo
                  qualunque della macchina ospite.  `01-b2-lancia-wt.sh` è
                  immune perché la verifica successiva (`ss … pid=$PID`) gira
                  **dentro**; qui quella verifica non c'è.
MARCA:            [R]
```

---

### R5.14

```
DOVE:             banchi/01-b11-guasto.sh:118-124 (il controllo della porta)
COSA CONTRADDICE: `REVIEWER.md` §1 domanda 4, che nomina il caso alla lettera:
                  «un grep senza stato d'uscita … rifiuta».
COME SI DIMOSTRA: `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")`; si
                  prova solo `[ -n "$CHI" ]`.  «Vuoto» ha tre cause opposte:
                  la porta è libera, `ss` non c'è nel contenitore, `enter.sh`
                  non ha eseguito il comando.  Ingresso concreto: si toglie
                  `iproute2` dal contenitore → `CHI` è vuoto → il banco stampa
                  «ok porta 7447 libera» e accende un secondo server sulla porta
                  di uno già acceso; il primo continua a rispondere e B11 misura
                  **il server sbagliato** (che potrebbe essere quello sano — il
                  difetto che il commento di `01-b11-lancia.sh:155-161` dichiara
                  di voler evitare).  La stessa forma è in
                  `01-b2-lancia-wt.sh:79`, ma lì il `bind` fallito verrebbe
                  colto dal controllo `ss … pid=$PID` che qui manca (R5.13).
MARCA:            [R]
```

---

### R5.15

```
DOVE:             banchi/01-b11-guasto.sh:92-94 (azione «registro»)
COSA CONTRADDICE: `REVIEWER.md` §1 domanda 4, che nomina alla lettera «un
                  comando con `2>/dev/null`: rifiuta».
COME SI DIMOSTRA: tre cose insieme sulla stessa istruzione: `2>/dev/null` sul
                  `grep`, l'assenza di qualunque prova dello stato d'uscita
                  (`grep` esce 1 quando non trova niente), e `exit 0`
                  incondizionato subito dopo.  Il secondo testimone di B11 —
                  l'unico posto da cui si osservano due proprietà **negative**
                  della pagina — riferisce «successo, nessuna riga» in modo
                  indistinguibile da «il file non esiste», «il server non è mai
                  partito», «il contenitore non risponde».  Ingresso concreto:
                  si rinomina `b11-server.log`; `registro` esce 0 con uscita
                  vuota, e in `01-b11-lancia.sh:213` anche lo stato dell'SSH è
                  buttato (il `>` cattura solo l'uscita).  Oggi il danno è
                  contenuto dal solo `SERVITI -eq 0` (riga 216), cioè da un
                  controllo che R5.4 mostra essere a sua volta senza
                  denominatore.
MARCA:            [R]
```

---

### R5.16

```
DOVE:             banchi/01-b11-lancia.sh:254 (`ATTESI=$((PROVATI - 1))`),
                  con :92-99 (`prova_motore`, i due salti)
COSA CONTRADDICE: `REVIEWER.md` §1 domanda 2 (il banco certificato prima
                  dell'uso); e il commento delle righe 153-154 («gira con UN
                  motore solo, e si dichiara»), che presume il controllo sempre
                  eseguito.
COME SI DIMOSTRA: `PROVATI` non è «i motori provati contro il guasto»: è «le
                  chiamate a `prova_motore` che hanno superato i due
                  `command -v`», controllo compreso.  Il salto è un `inf` e
                  restituisce **0**: né `ESITO` né alcun conteggio ne prendono
                  nota.  Ingresso concreto: una macchina con Chrome e **senza**
                  Firefox.  Il controllo (riga 177, che chiama `firefox` a
                  prescindere da `$MOTORI`) viene saltato, `PROVATI` vale 1,
                  `ATTESI` vale 0, e Chrome — che ha servito il caso una volta —
                  fa `CASI=1`: il banco stampa «⛔ il caso e' stato servito 1
                  volte, e i motori contro il guasto sono 0» e addossa alla
                  pagina un rosso che è la propria aritmetica.  ⛔ E, cosa più
                  grave, il giro è arrivato a un verdetto **senza che il
                  controllo che dice NO sia mai stato eseguito**, e senza che il
                  banco lo dichiari: l'unica guardia è `PROVATI -eq 0`
                  (riga 282), che non distingue «zero motori» da «zero
                  controlli».
MARCA:            [R]
```

---

### R5.17

```
DOVE:             banchi/01-b11-guasto-innesta.py:290
COSA CONTRADDICE: `LEZIONI.md` §1.9; e il proprio scopo, righe 264-279, dove
                  ogni innesto viene contato uno per uno.
COME SI DIMOSTRA: `print(f"\n   OK  {len(INNESTI)} guasti innestati in
                  {len(testi)} file")` stampa una **costante** (11) e il numero
                  di file **letti**, non applicati né scritti.  Ingresso
                  concreto: un albero in cui tutti gli innesti prendono il ramo
                  «c'e' gia'» (riga 270-272): zero sostituzioni, e il programma
                  dichiara comunque «OK 11 guasti innestati in 3 file» e
                  restituisce 0.  Un conteggio che non può valere zero non è un
                  conteggio: è una didascalia.
MARCA:            [R]
```

---

### R5.18

```
DOVE:             banchi/01-b11-guasto.sh:96-99 (`spegni`, la parte che ferma)
COSA CONTRADDICE: l'intestazione dello stesso file, righe 10-19 («⭐ Per questo
                  `spegni` ferma il processo **e** ricostruisce il server sano,
                  e lo verifica»); forma E7 (si verifica dal lato sbagliato).
COME SI DIMOSTRA: quel che viene verificato è **il sorgente**; che il processo
                  sia morto non è verificato mai.  Tre buchi in tre righe:
                  `cat … 2>/dev/null` (se il file dei PID manca, `P` è vuoto e
                  **non si uccide niente**), `[ -n "$P" ] &&` (nessun ramo
                  `else`: l'assenza del PID non è un errore), `kill $P
                  2>/dev/null || true` (l'esito del `kill` è cancellato due
                  volte).  Dopo di che il file dei PID viene rimosso comunque
                  (riga 99), quindi la traccia del processo superstite sparisce.
                  Ingresso concreto: si cancella `b11-server.pid` mentre il
                  server guasto gira, poi si chiama `spegni`: nessun `kill`,
                  ricostruzione del sorgente sano, grep pulito, stampa
                  «⭐ nessuna traccia di B11 nel sorgente: il server e' quello
                  vero», uscita 0 — **e il server bugiardo è ancora acceso sulla
                  porta 7447**, che è precisamente lo scenario che le righe
                  12-15 dello stesso file descrivono come inaccettabile.
                  Nessuna delle due ripuliture (qui e in
                  `01-b11-lancia.sh:78-83`) verifica mai che la porta sia
                  tornata libera.
MARCA:            [R]
```

---

## 2. I rilievi `[?]` — da misurare, non da correggere a vista

### R5.19

```
DOVE:             banchi/01-b11-lancia.sh:213 (lettura del registro), subito
                  dopo :115-116 (`kill "$p"` / `wait "$p"`)
COSA CONTRADDICE: la promessa della riga 212 — «il server scrive ogni byte
                  arrivato dopo la fine» — letta come se il registro fosse
                  completo nel momento in cui lo si legge.
COME SI DIMOSTRA: `wait "$p"` ritorna quando muore `xvfb-run`, non quando
                  l'ultimo pacchetto dell'ultimo caso è stato consegnato e
                  registrato dal server sull'altra macchina.  Fra la morte del
                  browser e la lettura non c'è nessuna attesa né nessuna
                  sincronizzazione.  Una violazione di §4.4 prodotta
                  dall'ultimo caso, o la riga «CONGEDO di commiato» della
                  seconda strada, possono arrivare **dopo**: `DOPO` resta 0 e
                  `CON` perde un'unità.  Non l'ho potuto misurare: dipende dai
                  tempi di rete e di scarico di `stderr`, e per questo è `[?]`.
                  ⚠ Va accanto al difetto noto n.6 del mandato, che dichiara
                  aperta la causa dei verdetti diversi fra giri identici.
MARCA:            [?]
```

### R5.20

```
DOVE:             banchi/01-b11-lancia.sh:109 (`while [ "$i" -lt 240 ]`)
COSA CONTRADDICE: il proprio commento, righe 106-107 («il tetto e' generoso
                  apposta»), che dichiara generoso un tetto mai derivato dai
                  tempi che la pagina può prendersi.
COME SI DIMOSTRA: la pagina fa fino a tre `attendi` per caso, ciascuno con
                  `prossimo(12000)` (`01-b11-pagina.html:204, 399, 403, 406`),
                  più 8000 ms nel caso `silenzio`, più 4000 ms nel ramo
                  `RESPINTO`, più fino a 2000 ms di chiusura per caso, su
                  **tredici** casi: il tetto peggiore della pagina supera
                  ampiamente i 240 s del banco.  Un server guasto che tardi le
                  risposte (macchina carica) fa scadere il banco prima della
                  pagina, e il messaggio che ne esce — «$nome non ha registrato
                  niente in $i secondi» — punta di nuovo sulla pagina.  Il
                  numero giusto è calcolabile dai tempi della pagina e non lo è;
                  che il margine di oggi sia sufficiente è un'ipotesi, quindi
                  `[?]`.
MARCA:            [?]
```

### R5.21

```
DOVE:             banchi/01-b11-guasto.sh:43, 66-67, e in genere ogni
                  `bash "$ENTRA" --root "…"`
COSA CONTRADDICE: il commento delle righe 55-65, che fa poggiare tutta
                  l'onestà di `accendi` sullo stato d'uscita di `ninja`.
COME SI DIMOSTRA: lo stato di `ninja` arriva al banco solo se
                  `/media/REMOTIX/enter.sh --root` **propaga** il codice
                  d'uscita del comando che esegue.  `enter.sh` non sta in questo
                  albero e non l'ho potuto leggere; la riga 43
                  (`bash "$ENTRA" --root "true" || exit 2`) mostra che la
                  propagazione è **assunta**, mai verificata.  Se `enter.sh`
                  restituisse lo stato del proprio `sudo`/`nspawn` invece che
                  quello del comando, il controllo aggiunto oggi
                  (`if ! ricostruisci con-guasti`) sarebbe muto e il difetto del
                  primo giro del 10 agosto sarebbe ancora lì, con una riga di
                  codice in più a farlo sembrare curato.  Basta una misura:
                  `bash /media/REMOTIX/enter.sh --root "exit 7"; echo $?`.
MARCA:            [?]
```

### R5.22

```
DOVE:             banchi/rcp/rcp.c:1052-1065 (il classificatore del «dopo la
                  fine»), consumato da banchi/01-b11-lancia.sh:214
COSA CONTRADDICE: la distinzione che il commento di rcp.c:1032-1051 dichiara di
                  fare — «si distingue sul tipo letto dai byte».
COME SI DIMOSTRA: il tipo è letto dai primi due byte del **pezzo appena
                  arrivato**, come se ogni consegna coincidesse con l'inizio di
                  un messaggio.  Su uno stream WebTransport non è garantito: un
                  `CONGEDO` di 22 byte spezzato in due consegne fa leggere al
                  secondo pezzo i primi due byte del **corpo** come tipo → non è
                  `T_CONGEDO` → viene registrato «⛔ N byte arrivati DOPO la
                  fine», e `01-b11-lancia.sh:223-229` manda in rosso la pagina
                  per un commiato che §8.1 le **impone**.  È la stessa forma del
                  difetto del 10 agosto descritto in quel commento, curata sul
                  caso «un messaggio, una consegna» e non sul caso generale.
                  Non ho modo di provocare la frammentazione da qui: `[?]`.
MARCA:            [?]
```

---

## 3. Che cosa ho provato a rompere e non sono riuscito a rompere

Dichiarato perché vale come informazione (`PIANO.md` §0.4):

- **La perdita della variabile `ATTESO` fra il controllo e i motori**
  (`01-b11-lancia.sh:177`): è un'assegnazione a prefisso di comando, quindi vive
  solo per quella chiamata; i giri successivi ricadono correttamente su
  `CONFORME`.  Non si contamina.
- **Il confronto «desktop non cambia niente»**
  (`01-b11-pagina.html:532-534`): esclude il `CIAO` dal confronto **e** pretende
  che il resto non sia vuoto (`dopoCiao(kde) !== ""`).  Ho cercato un caso in
  cui due giri entrambi vuoti dessero verde: la seconda condizione lo chiude.
- **Il confronto degli appigli negli innesti** (`n != 1 → non si scrive
  niente`, `01-b11-guasto-innesta.py:273-285`): il rifiuto è per **file
  interi**, quindi un innesto a metà non finisce sul disco.  L'ho provato a
  rompere con appigli duplicati: si ferma correttamente.
- **`PRIMA` letto prima dell'avvio del raccoglitore**
  (`01-b11-lancia.sh:63`): la forma `wc -l < f 2>/dev/null || echo 0` restituisce
  0 anche quando il file non c'è, e la variabile è un intero in ogni ramo.  Non
  sono riuscito a farla valere vuoto e far saltare il confronto numerico.
- **La cattura dell'impronta** (`01-b11-lancia.sh:170-174, 192-196`): il
  controllo di lunghezza (`-ne 44`) distingue davvero «tagliata» da «assente», e
  il ramo `exit 4` gira con il `trap` già installato.  Non sono riuscito a farla
  passare corta o vuota.
- **L'ordine del `trap`** (`01-b11-lancia.sh:84`): è installato prima di ogni
  `exit` che segue, e le due uscite precedenti (righe 70-72) fanno la loro
  ripulitura a mano.  Non ho trovato un percorso che salti la ripulitura.  ⚠ Ho
  trovato invece che la ripulitura, quando fallisce, non si vede: R5.2.
- **L'iniezione attraverso `eval "$(awk …)"`** (`01-b11-lancia.sh:255-264`):
  l'`awk` stampa un formato fisso di quattro interi, quindi una riga di registro
  ostile non arriva a `eval`.  Non rompibile per quella strada.

---

## 4. Verdetto

Non è un'approvazione, e non ne esiste una: `REVIEWER.md` §0 dice che una
review verde è solo «non ho trovato niente», e questa non è verde.

Diciotto contraddizioni `[R]` e quattro sospetti `[?]`.  La forma che le tiene
insieme è una sola, ed è quella che `LEZIONI.md` §10 attribuisce al progetto
intero: **il banco B11 sa dire «rosso» meglio di quanto sappia dire «verde»**.
I suoi verdi poggiano su conteggi che possono valere zero senza che nessuno lo
noti (R5.4, R5.5, R5.9), su un controllo che si accontenta di un fallimento
qualunque (R5.3), e su una ripulitura il cui fallimento non entra nel codice
d'uscita (R5.1, R5.2, R5.18) — cioè proprio sul punto che l'intestazione di
`01-b11-guasto.sh` dichiara di aver costruito per non lasciare in piedi un
server che mente.
