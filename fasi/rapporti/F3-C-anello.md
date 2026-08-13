# CORSIA C — I 74,58 ms sono `[M]` o `[?]`?

*13 agosto 2026, sera. Le tre code C3 · C4 · C5, più la certificazione di `03-b17`.
⛔ Il mandato era **refutare**, e quattro premesse sono state smentite con un caso — tre del piano,
una del catalogo.*

---

## In una riga

⭐ **`74,576` resta `[M]`, e la corsia C lo rinforza invece di indebolirlo**: `73,69` va a `[?]` per
una ragione **aritmetica** e non di principio, e togliendo il giro invalido i cinque restanti danno
**esattamente 74,576**. ⭐ **`03-b17` è CERTIFICATO** — sano 0 → guasto 1 → risanato 0, con la marca
**misurata** — e il muro che lo bloccava era una **regressione del controllo del ponte**, non la
macchina. ⛔ E cercando il caso che mi smentisse ne è uscito uno grosso: **il banco che ha prodotto
il numero della fase esce SEMPRE 0 quando rilegge un verbale** — il quarto della famiglia, e non lo
aveva contato nessuno.

| coda | esito |
|---|---|
| **C3** — il rilevatore di P5 cieco per costruzione | ⭐ **curato nel banco e certificato**, con tre risposte distinte dove prima ce n'erano due |
| **C4** — il modo di degenerazione del ponte | ⭐ **nominato E curato**: il ponte adesso lo **dichiara**, e il controllo misura quel che il ponte fabbrica |
| **C5** — `73,69` a `[?]`, via il fossile «783» | ⭐ **fatto**, con una rettifica accanto al registro (la riga originale **non** è stata riscritta) |
| ⭐ **certificazione `03-b17`** | ⭐ **PROMOSSO** — 38 controlli su 38 sano, 37 su 38 col guasto, 38 su 38 risanato |

---

## ⛔ La scena, dichiarata prima dei numeri

⛔ **Non ho misurato NESSUN tempo della fase**, e quindi non ho chiesto la finestra esclusiva.
Tutto quel che segue è **correttezza** — codici d'uscita — che `§0-bis` dichiara parallelizzabile.

| | |
|---|---|
| macchina | **CHUWI**, `--certifica` gira **qui**, senza rete, senza server, senza browser: i giudici sono funzioni **pure** su un verbale sintetico, e il ponte si certifica da solo su **loopback** con porte effimere |
| ⚠ **ero solo?** | ⛔ **NO, e si dice**: durante i tre passi giravano un `mutter --headless` di un'altra corsia (`remotix-scena-7626`) e una sonda WebCodecs con Chrome. **Load average 3,49 · 4,84 · 3,99** ai tre passi |
| ⇒ che cosa ne discende | i controlli a **forma di tempo** che stanno dentro l'autoprova del ponte (costo < 2 ms al p95; salita di N ± 2 ms) sono passati **col vicino acceso**: è un'evidenza **in più**, non in meno. ⛔ Ma **nessun numero della fase** è uscito da questa corsia |
| scena Wayland | ⛔ **nessuna**: la trappola n.1 (la scena sul monitor sbagliato) **qui non si applica**, e lo dico invece di lasciarlo intendere |
| porte protette | **7448 · 7501 · 7561** contate **prima e dopo** sul server (⚠ non su CHUWI: ascoltano di là). Presenti tutt'e tre prima, presenti tutt'e tre dopo, **nessun'altra 76xx accesa**. Non toccate |
| `/tmp` | 98 % (92 M liberi) all'inizio, 66 % (1,4 G) alla fine — liberato da altri. ⛔ Nessuno dei miei giri apre browser |
| perimetro | `banchi/03-b17-ritardo.py` · `banchi/03-b17-ponte.py` · `banchi/03-b17-esiti.jsonl` · `banchi/01-b12-registro-C.jsonl` · questo rapporto. **Nessun `src/`**, nessun altro banco, nessun `.md` d'altri |

---

## ⛔⛔ I CASI CHE SMENTISCONO — quattro, e uno cambia un conto della sessione

### 1. ⛔⛔⛔ **Il banco che ha prodotto il numero della fase esce SEMPRE 0 quando rilegge un verbale**

Il catalogo delle trappole dice: *«tre banchi che escono SEMPRE 0 … due curati, **il terzo è ancora
lì** (`03-b19-ritardo-worker.py`, percorso `--verdetto`)»*.

⛔ **Erano QUATTRO.** Il quarto è `03-b17-ritardo.py` stesso, e nella stessa identica forma:
`--verdetto <file>` chiamava `stampa_verdetto()` — che stampa i rossi con `ko()` — e poi
**`return 0` incondizionato**.

⭐ **Misurato su un verbale VERO, e la cura è misurata nei due versi** (`/tmp/03-b17/verbale.json`,
giro `b17-20260813-193656`, il solo sopravvissuto):

| | |
|---|---|
| **prima della cura** | stampa `NO P5 …` a schermo, **esce 0** |
| **dopo la cura** | stessa stampa, **esce 1** |
| ⭐ **e il controllo positivo** | su un verbale **tutto verde** esce **0** ⇒ non è «esce sempre 1», discrimina |

⇒ ⛔ **La riga del catalogo va corretta**: la famiglia del `return 0` **non è chiusa a tre**, e il
membro che mancava era proprio il banco su cui poggia il numero dello step 5.

### 2. ⛔ **«I 31/31 erano su NIC-OS» — smentito, e i «sei giri promossi» erano NOVE**

Il catalogo (voce `03-b17`) dice: *«il giro sano di `--certifica` NON è verde su CHUWI, 3 giri su 3
… i sette PROMOSSO 31 su 31 erano su NIC-OS: `atteso_sano = 0` vale là e non qui»*.

- ⭐ `[M]` **riprodotto qui, su CHUWI, col file di ieri**: BOCCIATO **30/31**, e cade **sempre lo
  stesso** controllo, quello del ponte. ⇒ Il fatto è vero, **la spiegazione no**: non è la macchina,
  è **il controllo** (vedi C4). Riscritto il controllo, su **CHUWI**: **38/38**.
- ⚠ E la finestra «12:46 → 13:18:28, **sei giri** PROMOSSO 31/31» del piano, riletta nel registro,
  contiene **nove** certificazioni: **sette** PROMOSSO 31/31 e ⛔ **DUE BOCCIATO 20 su 31**
  (12:51:23 e 12:52:04) che nessun documento nomina. ⛔ **Il registro non conserva quali undici
  controlli cadessero**: è un limite del registro, e non si inventa.

### 3. ⛔ **C3 non rende P5 «eseguito»: lo rende ONESTO. E la differenza va detta subito**

Il mandato lascia intendere che guardare `scartati_ordine` chiuda la lacuna. ⛔ **Non la chiude.**
`[M]` sul verbale vero: `scartati_ordine` vale **0** in **tutte** le istantanee del giro — dalla
prima (98 consegnati) all'ultima (**3 469** consegnati), **iniettore acceso compreso**.

⇒ Con la cura, P5 dice ancora **«non eseguito»** — ma adesso **è una misura ai due capi** (0 visti
dal banco **e** 0 dichiarati dal prodotto) invece di un'identità algebrica. ⛔ *Il fenomeno continua
a non presentarsi: quel che è cambiato è che adesso lo sappiamo.*

### 4. ⚠ **Due dettagli del mandato, corretti perché il prossimo non li ricerchi**

| detto | misurato |
|---|---|
| lo scarto per ordine è a `src/pagina.html:**1576**` | è a **`:1578`** (il campo è dichiarato a `:1235`) |
| «`scartati_ordine` dice 0 su **7 672** consegnati» | nel verbale che sopravvive: **0 su 3 469** nella finestra di P5. Il 7 672 è di un giro il cui verbale **non esiste più** |

---

## 🅒 C3 — il rilevatore di P5, cieco per costruzione

### Che cos'era, in una frase

Il prodotto **scarta i fotogrammi fuori ordine PRIMA del decodificatore** (`src/pagina.html:1578`,
§6.2 rilievo P14: *«la sua misura non si guarda nemmeno»*); il banco guarda solo i fotogrammi
**dipinti**. ⇒ Un fotogramma scavalcato **non arriva mai** nel campione, e *«0 fuori ordine»* era
un'identità algebrica.

### La cura, e dove sta

⭐ **Nel banco, non nel ponte**, come chiedeva il mandato. `p5_fuori_ordine()` adesso prende **due
istantanee dei conti del prodotto** e ne fa la **differenza**:

```
fuori ordine = scavalcati VISTI (dopo il decodificatore)
             + scartati DAL PRODOTTO (prima del decodificatore, `conti.scartati_ordine`)
```

⛔ **E ho verificato che `scartati_ordine` sia il contatore GIUSTO invece di crederci**: in
`src/pagina.html` le strade per cui un fotogramma non arriva sono cinque — `azzerati` (stream
abbandonato), `corti` (intestazione rotta), `scartati_misura` (misura sbagliata), `trattenuti`
(`TELA` in volo) e `scartati_ordine`. ⭐ **Solo l'ultima scarta per ORDINE**: il contatore è quello,
ed è completo per il fenomeno che P5 misura.

### Le TRE risposte, dove prima ce n'erano DUE

⛔ Il difetto vero era che **due stati del mondo davano la stessa riga**, e un terzo non aveva riga
affatto. Adesso sono tre frasi diverse, ed è **certificato che siano diverse**:

| stato del mondo | che cosa dice adesso |
|---|---|
| il fuori ordine **non è successo** | **rosso**, «NON ESEGUITO … e stavolta è MISURATO ai due capi» |
| il fuori ordine **è successo** e il prodotto l'ha assorbito prima del decodificatore | ⭐ **verde**, «ESEGUITO … ha scartato N fotogrammi per ORDINE … nel campione non ce n'è nessuno **per costruzione**» |
| ⛔ **non ho i conti del prodotto** | **rosso**, «NON HO POTUTO GUARDARE … è un'assenza di informazione» — `LEZIONI.md` §2.0 |

⚠ **E quel che P5 continua a NON dire, scritto dentro la sua stessa risposta**: *quanto sarebbe
stato il ritardo dei fotogrammi scartati*. Quei fotogrammi al vetro non ci arrivano mai — è un
limite **del fenomeno**, non del banco, e va dichiarato invece che colmato.

### Come è certificato

- ⭐ un **guasto sintetico nuovo** nel giro sano→guasto→risanato: *«P5 spariscono i conti del
  PRODOTTO (la cecità per costruzione)»* ⇒ P5 diventa **rosso**, e **solo** P5.
  ⛔ Prima della cura questo guasto **non era nemmeno esprimibile**: il banco quei conti non li
  guardava, quindi toglierli non cambiava niente.
- ⭐ un blocco **C-bis** con cinque controlli che provano le tre risposte **sullo stesso verbale**,
  cambiando **una cosa per volta**, e che pretendono esplicitamente che le frasi (1) e (2) **non
  coincidano**;
- ⭐ il gemello negativo del contatore: un conto che **torna indietro** (la pagina si è riaccesa)
  dà *«non ho potuto»*, **non «zero»**.

⚠ **Il prezzo, dichiarato**: da adesso ogni verbale **vecchio** riletto con `--verdetto` dà **P5
rosso** con *«non ho potuto guardare»*. ⭐ È la risposta giusta per quei verbali — non portavano
l'istantanea del «prima» — ma chi rilegge il 13 agosto deve saperlo prima di leggerlo come un
difetto nuovo.

---

## 🅒 C4 — il modo di degenerazione del ponte

### Il difetto, e l'aritmetica che lo genera

La raffica parte al pacchetto `k·fo` e ne copre `raffica`. Il primo pacchetto dopo la raffica ha
indice `k·fo + raffica`, che è **ancora un multiplo di `fo`** ⇔ `raffica % fo == 0` — e allora ne
fa partire subito un'altra, all'infinito. ⇒ **Da lì in poi il ponte ritarda TUTTI i pacchetti della
stessa quantità**: l'ordine si conserva **per aritmetica**, su qualunque macchina, **e in silenzio**.

⭐ L'iniettore vero gira a `fo=400, raffica=4` (4 % 400 = 4): **non degenera**.
⛔ Degenerava **l'autoprova**, che usa `fo=2` con la raffica di riposo **4**.

### La cura — ⛔ *non* una toppa dispari

**Due pezzi, e servono tutt'e due:**

**a) il ponte lo DICE.** Tre cose nuove, e nessuna è una deduzione dal sorgente:

| | |
|---|---|
| `degenere` | la bandiera aritmetica, ricalcolata a ogni cambio d'assetto, ⛔ inizializzata a **`None`** e non a `False` — «non ho ancora guardato» e «non degenera» non sono la stessa cosa |
| `fo_dritti` / `fo_trattenuti` | i due **conti misurati**: sono i pacchetti *dritti* a scavalcare i trattenuti ⇒ **`fo_dritti == 0` vuol dire «non sto riordinando niente»**, e lo dice il conto, non l'algebra |
| una riga su `stderr` | al cambio d'assetto, quando degenera |

**b) il controllo misura quel che il ponte fabbrica ADESSO**, in due assetti invece che uno:

| assetto | esito misurato |
|---|---|
| ⭐ **VERO** — `fo=10, raffica=4` (la **forma** del `fo=400/raffica=4` dell'iniettore: raffica non multipla di fo, fo ≫ raffica) | **40 inversioni** su 120 tornati · 45 trattenuti · **75 dritti** · `degenere = false` · 0 persi |
| ⛔ **DEGENERE** — `fo=2, raffica=4` | **0 inversioni** · **120 trattenuti su 120** · ⭐ **0 dritti** · `degenere = true` · 0 persi |

⚠ **Perché `fo=10` e non `fo=400`**: l'autoprova manda 120 pacchetti, e con una raffica ogni 400 non
ne partirebbe **nemmeno una** ⇒ zero inversioni **per un motivo terzo**, che è esattamente l'errore
che si sta curando. Quel che si conserva del vero è la **forma**, e sta scritto accanto al numero.

⇒ ⭐ **Il ponte esce PROMOSSO 15 controlli su 15**, e il modo degenere adesso è **provato**, non
dedotto: c'è un controllo che fallirebbe se il ponte tornasse a tacere.

---

## 🅒 C5 — `73,69` a `[?]`, e il fossile via

### ⭐ La ragione è ARITMETICA, e va nella direzione opposta a quella temuta

`[M]` **rileggendo il registro** (`03-b17-esiti.jsonl`), non ricordandolo:

| mediana | giro | i sette controlli |
|---|---|---|
| 64,551 · 76,415 · 70,999 | 13:02 · 13:08 · 13:15 | ⭐ **tutti e sette veri** (3 giri) |
| 76,309 · 74,576 | 13:22 · 13:40 | solo **P5** rosso — *«non eseguito»*, un fenomeno che non si presenta |
| ⛔ **72,794** | 13:34 | ⛔ **P3 ROSSO** (e P5) — e P3 valida l'`istante_us` che entra nel ritardo |

⇒ ⛔ **`giri_verdi: 6` è gonfiato**, e la correzione è **più precisa** di «sono 3»: i giri con tutti
e sette i controlli veri sono **3**; i giri **utilizzabili** per il numero sono **5**; il giro da
buttare è **uno solo**.

> ### ⭐⭐ E qui c'è il pezzo che nessuno aveva fatto: **il conto**
>
> Con **sei** valori la mediana è la **media dei due di mezzo**, e i due di mezzo sono proprio
> **72,794** (il giro con P3 rosso) e **74,576** (il giro finale):
>
> | | |
> |---|---|
> | mediana dei **sei** | **73,685** ⇒ arrotondata: `73,69` |
> | ⭐ mediana dei **cinque**, tolto il giro con P3 rosso | ⭐⭐ **74,576 — esattamente il numero che resta `[M]`** |
>
> ⇒ ⛔ `73,69` è **letteralmente la metà strada fra un giro invalido e quello buono**.
> ⭐ **La rettifica non abbassa il numero della fase: lo CONFERMA**, e toglie di mezzo l'unico giro
> che lo tirava verso il basso.

### Come è stata scritta

⛔ **La riga originale del registro NON è stata riscritta.** Un verbale non si riscrive: si
**rettifica accanto**, con la data, così chi legge vede che cosa c'era e che cosa è stato corretto.
La riga nuova è in `banchi/03-b17-esiti.jsonl`, tipo **`RETTIFICA — corsia C, coda C5`**, e porta le
prove rilette dal registro invece delle conclusioni.

### Il fossile

⛔ «0 su **783**» tolto dai commenti di `03-b17-ritardo.py`. ⚠ **783 era il numero di campioni di un
ALTRO giro** (`b17-20260813-131128`, mediana 70,999): non era il denominatore dei fuori ordine del
giro che ha prodotto il numero della fase, che di campioni ne ha **804**. ⇒ Il denominatore adesso
**non si scrive nei commenti**: lo consegna `p5_fuori_ordine` a ogni giro, insieme al conto del
prodotto — l'unico posto in cui può essere vero.

---

## ⭐ La certificazione di `03-b17` — sano → guasto → risanato

`python3 banchi/01-b12-guasti.py --provabile 03-b17` ⇒ **uscita 0, nessun `MANCA`**: provabile da
CHUWI.

| passo | uscita | esito | la **marca**, contata | impronta della copia | load |
|---|---|---|---|---|---|
| **1. SANO** | **0** | PROMOSSO **38/38** | **0 volte** | `12895b0a…` = l'originale | 3,49 |
| **2. GUASTO innestato** | **1** | BOCCIATO **37/38** | ⭐ **1 volta** | `8cb8c6cf…` | 4,84 |
| **3. RISANATO** | **0** | PROMOSSO **38/38** | **0 volte** | ⭐ `12895b0a…`, **byte per byte** l'originale | 3,99 |

- **Il guasto**: la finestra di sanità dell'istante **spalancata** (`dentro = list(scarti)`) —
  il setaccio che smaschera un rilevatore che **inventa** il tempo. Appiglio verificato **unico**.
- ⭐⭐ **LA MARCA È MISURATA, NON DEDOTTA.** Fra sano e guasto cambia **una sola riga** in tutta
  l'uscita, e la stringa è:

  ```
  rossi nessuno (attesi ['P3'])
  ```

  ⛔ Nel giro sano quella stessa riga dice `rossi ['P3'] (attesi ['P3'])`, e la stringa
  «rossi nessuno» **non compare mai** — contata: **0** nel sano, **1** nel guasto, **0** nel
  risanato. ⇒ Il rosso si **attribuisce**, e non è «il banco è uscito 1».
- ⭐ **Un solo controllo cade col guasto** (37 su 38): il guasto non ne sporca altri.
- La riga di registro è nella **mia scheggia**: `banchi/01-b12-registro-C.jsonl`. ⛔ **Non** nel
  registro comune — l'unione la fa il coordinatore.

### ⛔ Che cosa NON ho potuto fare, e non l'ho dedotto

⛔ Il campo `marca` della voce `03-b17` in `01-b12-guasti.py` è **oggi vuoto**, e finché è vuoto
`--giudica` **rifiuta** questa riga — ed è giusto così. **`01-b12-guasti.py` è fuori dal mio
perimetro**, quindi la modifica **non l'ho fatta**: la scrivo qui e nella scheggia.

---

## ⛔ RICHIESTE AL COORDINATORE — tre righe fuori dal mio perimetro

| # | file | che cosa |
|---|---|---|
| **1** | `banchi/01-b12-guasti.py`, voce `03-b17` | il campo `marca` (oggi `""`) va messo a **`rossi nessuno (attesi ['P3'])`** — ⭐ **misurato**, non dedotto |
| **2** | `banchi/01-b12-guasti.py`, `nota` di `03-b17` | ⛔ va corretta: *«il giro sano NON è verde su CHUWI»* e *«i 31/31 erano su NIC-OS»* erano **una regressione del controllo del ponte**, non una differenza di macchina. **`atteso_sano = 0` vale su CHUWI**, ed è misurato |
| **3** | `fasi/rapporti/F3-prossima-sessione.md`, §4 delle trappole · `LEZIONI.md` | ⛔ *«tre banchi che escono SEMPRE 0 … il terzo è ancora lì»* ⇒ **erano QUATTRO**, e il quarto era `03-b17-ritardo.py --verdetto`, cioè **il banco del numero della fase**. Curato e misurato, ma il **conto** della famiglia va corretto |

---

## ⛔ CHE COSA NON HA FUNZIONATO

| | |
|---|---|
| ⛔⛔ **il verbale ha un percorso FISSO, e dei quattordici giri del 13 agosto ne sopravvive UNO** | `--verbale` scrive sempre `/tmp/03-b17/verbale.json` e ogni giro **riscrive** il precedente. ⇒ Il verbale del giro da **74,576** — quello del numero della fase — **non esiste più**, e nemmeno quello del giro con **P3 rosso**. ⭐ Sopravvive solo l'ultimo (`b17-20260813-193656`, 72,19). **La cura costa una riga in `03-b17-lancia.sh`**, ma non l'ho fatta: ⛔ curarla adesso **non riporterebbe indietro** i verbali perduti, e una cura che nessuno ha visto mordere non è una cura. **È il primo lavoro della corsia E**, prima del suo primo giro |
| ⛔ **un commento che dichiara un controllo che il codice NON fa** | in `certifica()` sta scritto: *«e NON deve far diventare rosso nient'altro di inatteso, o il controllo non sta distinguendo»* — ma `preso = all(k in rossi for k in attesi)`, e gli `extra` finiscono **solo in un ⚠ stampato**. `[M]`: il guasto «P7 il ritmo è morto» **arrossa anche P3 e P5** e il controllo **passa lo stesso**. ⚠ **Non l'ho stretto**: renderlo vincolante boccerebbe il giro sano **oggi**, e sarebbe una consegna che cambia l'atteso invece di curarlo. ⇒ **Va deciso**, non lasciato al commento |
| ⚠ **il guasto più fedele allo spirito di B12 resta bloccato** | è quello sul `pts` del fotogramma **precedente** in `figlio.c` della copia. Lo blocca un difetto **del banco**: la riga che stampa per un P3 rosso è un `json.dumps(...)[:220]`, e i 220 caratteri **si esauriscono prima** del campo che cambia ⇒ sano e guasto stampano lo stesso prefisso, e **una marca non esiste**. La cura è dare a P3 un campo `perche` (due righe). ⛔ **Non l'ho fatta**: da qui quel guasto **non si può innestare** (vuole il server), e curare un banco per un rosso che non posso far uscire sarebbe la cura non eseguita spacciata per fatta |
| ⚠ **non ero solo, e non ho chiesto la finestra** | c'era un altro agente con Mutter e Chrome accesi. ⭐ Non l'ho chiesta **perché non ho misurato nessun tempo della fase** — ma se qualcuno leggesse i millisecondi dell'autoprova del ponte come numeri della fase, li leggerebbe male: sono **controlli**, non misure |
| ⚠ **il registro non conserva abbastanza** | non sa dire **quale parte di P3** fosse rossa nel giro da 72,794, né **quali undici controlli** cadessero nei due BOCCIATO 20/31 delle 12:51. ⛔ Sono limiti **del registro**, non dei giri, e non si colmano inventando |

---

## ⛔ CHE COSA RESTA `[?]`

| | |
|---|---|
| ⛔ **`73,69`** — il consolidato | **`[?]`**, e adesso si sa **perché**: media fra un giro con P3 rosso e il giro buono. ⭐ Il sostituto onesto è **`74,576`**, che è insieme il giro finale **e** il consolidato dei cinque giri validi |
| ⚠ **quale parte di P3 fosse rossa** | `[?]` **per sempre**: il verbale di quel giro è stato sovrascritto |
| ⛔ **P5 resta NON ESEGUITO** | ⭐ ma non è più `[?]`: è **`[M]` che il fenomeno non si presenta** — 0 visti dal banco **e** 0 dichiarati dal prodotto su 3 469 consegnati, iniettore acceso. ⚠ Resta `[?]` **che cosa farebbe l'anello su una rete che riordinasse davvero**: i fotogrammi scavalcati il prodotto li butta prima del decodificatore, e il loro ritardo **non è osservabile da nessuna parte** |
| ⚠ **i due BOCCIATO 20/31 del 12:51** | `[?]`: undici controlli caduti insieme e mai spiegati, in mezzo alla finestra che i documenti descrivono come «sei giri promossi» |
| ⚠ **il numero dell'anello con l'assetto di oggi** | non è compito mio: **la corsia E** lo rifà con lo stesso banco e la stessa scena. ⭐ Il banco che eredita è **certificato**, il ponte non degenera più in silenzio, e P5 sa dire quale delle tre cose sta succedendo |

---

## I file toccati

| file | che cosa |
|---|---|
| `banchi/03-b17-ritardo.py` | C3 (il rilevatore + i suoi controlli), C5 (il fossile), la cura del `return 0` di `--verdetto`, le due istantanee dei conti del prodotto in `misura()` |
| `banchi/03-b17-ponte.py` | C4 (il modo degenere dichiarato e misurato, il controllo riscritto) |
| `banchi/03-b17-esiti.jsonl` | la riga **RETTIFICA** di C5, e le righe di certificazione dei giri |
| `banchi/01-b12-registro-C.jsonl` | ⭐ la **scheggia** della corsia C — `03-b17` certificato |
| `banchi/01-b12-copie/03-b17-*` | le copie rifatte da `--verifica`/`--applica`/`--togli`, **tornate identiche all'originale** |

⛔ **Nessun commit**: lo fa il coordinatore.
