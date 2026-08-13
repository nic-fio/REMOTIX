# Fase 3 — Il movimento

Aperta il **13 agosto 2026**, subito dopo la chiusura della fase 2.
⏳ **In corso.** Questo documento è aperto **all'apertura della fase**, non alla chiusura: è la
regola di [`README.md`](README.md) di questa cartella, e la ragione è che in un documento scritto
dopo le misure si *ricordano* invece di essere *registrate*.

> ⛔ **Stato al 13 agosto 2026, sera**: le **misure sono finite**, i **documenti sono allineati**,
> e restano due cose prima del giudizio — **rigirare le certificazioni** (curare il prodotto le ha
> fatte scadere, ed era previsto) e **il giudizio dell'utente**. ⚠ La fase **non si chiude su un
> documento completo**: si chiude su una misura che l'utente guarda.

> Il modello sta in [`../PIANO.md`](../PIANO.md) §0.2; le decisioni stanno in
> [`../DECISIONI.md`](../DECISIONI.md) e qui si **rimanda**, non si copia.

---

## Che cosa deve produrre

Uno **stream per fotogramma**, l'abbandono con `RESET_STREAM`, la **cadenza**.

**Che cosa vede e giudica l'utente**: il desktop **che si muove**, e dice se è fluido.

**I numeri da raggiungere**: ritardo **≤ 50 ms**, traguardo **40** (`SPECIFICHE.md` §3.2).

---

## ⛔ Le tre cose decise PRIMA di scrivere, e da chi

*Il punto di ripresa del 13 agosto ne elencava tre, e imponeva di scioglierle prima di qualunque
riga. Sciolte tutte e tre la mattina del 13 agosto, a codice ancora fermo.*

| # | La cosa | Decisa da | Che cosa è stato deciso |
|---|---|---|---|
| **1** | ⛔⛔ **la risoluzione della tela** | ⭐ **l'utente**, 13 agosto 2026 | **1920×1080 resta**. Era ereditata dalla scena di un banco e mai decisa; adesso è **decisa** |
| **2** | ⛔ **la scena** | il progetto, su `LEZIONI.md` §1.1 | un client **a schermo intero, opaco, che ridisegna a ogni *frame callback*** del compositore, che **conta da sé quanto disegna**, e che porta una **marca leggibile a macchina** |
| **3** | ⚠ **l'attesa dichiarata in anticipo** | il progetto, su `SPECIFICHE.md` §3.2 | il numero da battere è **≤ 50 ms**; il traguardo dei **40** è dichiarato **a rischio** sul muro dei 37 fotogrammi di Mutter — ⛔ **e l'attesa è stata sbagliata due volte**, vedi §3 |

### 1. ⭐ La tela: **1920×1080**, e adesso è una decisione

La domanda era posta con il suo prezzo misurato accanto: sullo schermo dell'utente la tela viene
dipinta all'**86 %**, cioè **912 px di nero**. Le alternative messe davanti erano tre — tenerla,
portarla a 2560×1440 (lo schermo dell'utente), o accendere subito `SPECIFICHE.md` §6.1 (*la tela
nasce dallo schermo del client*, che il prodotto oggi **non** fa: `src/main.c:111` ha `TELA_L 1920`
scritto a mano).

⭐ **Scelta la prima**, e la ragione è di metodo: la fase 3 misura il **tempo**, non la geometria.
Con la tela ferma, un ritardo che sfora i 50 ms accusa l'architettura; con la tela cambiata sotto,
non si saprebbe se accusa l'architettura o il conto dei pixel.

⛔ **E le bande nere non sono la risoluzione**: 2545×927 di finestra fanno un rapporto **2,74**
contro un 16:9 di **1,7778**. Quelle bande sono la **forma della finestra**, e sparirebbero solo a
schermo pieno — cambiare la tela non le tocca. Va detto perché la `[?]` non venga riaperta
credendo di curarle.

⏳ **Resta aperta** — e va nominata alla fase in cui si accende — l'attuazione di `SPECIFICHE.md`
§6.1: *la tela nasce dallo schermo del client*. Oggi è una specifica scritta e non attuata.

### 2. ⛔ La scena, e perché non è negoziabile

`LEZIONI.md` §1.1 la prescrive, e il prezzo di averla sbagliata è già stato pagato: **tutte le
misure di ritmo delle fasi 3-9 di v1 sono state buttate**. Un compositore Wayland consegna un
fotogramma **solo quando qualcosa cambia** ⇒ una misura di fotogrammi senza la scena dichiarata
**non è una misura**.

Le due parti, e la seconda è quella che si dimentica:

1. la scena **si muove a ogni ridisegno** — non a raffiche, come farebbe una scena mossa battendo
   tasti;
2. ⛔ **si conta quanto disegna il client**, che è il controllo che dice se il tetto è **del
   compositore** o **della scena**. Senza, il 7 agosto si sarebbe attribuito a Mutter un tetto che
   era della scena — e viceversa.

⭐ **E la fase 3 ne chiede una terza, che §1.1 non chiede**: la scena porta una **marca** — un
contatore che cresce a ogni disegno, e l'istante — rileggibile **dai pixel del fotogramma
decodificato**, e ⛔ **rileggibile dopo la codifica con perdita**, il che va **provato** e non
supposto. Serve a chiudere **M6** e a riaprire il `giro` di **M8** (qui sotto).

### 3. ⚠ L'attesa, dichiarata prima della misura

Su GNOME il traguardo dei **40 ms** probabilmente **non si raggiunge**, per il muro dei 37
fotogrammi di Mutter. ⛔ Se la misura lo confermasse **non è un difetto nostro** — ed è una ragione
in più per la fase 10. Il numero da battere resta **≤ 50 ms**.

⭐ **Ma prima di dichiararlo si prova la cadenza disaccoppiata**, ed è lo **step 1** proprio perché
costa **tre celle e zero righe di prodotto**.

> ### ⛔⛔ L'attesa era sbagliata, e **la parte che ha sbagliato è quella che dava la colpa a un altro**
>
> *Scritto alla chiusura, e questa è la ragione per cui l'attesa si dichiara **prima**: perché poi
> si possa scrivere di quanto si era sbagliato, e in che direzione.*
>
> | quel che l'attesa diceva | quel che la misura dice |
> |---|---|
> | il traguardo dei **40** è a rischio | ⛔ **peggio**: si sfora anche il **tetto dei 50**. `[M]` mediana **74,58 ms**, e con il pezzo cieco **90-115 ms** sullo schermo dell'utente |
> | ⛔ per il **muro dei 37 fotogrammi di Mutter** | ⛔⛔ **falso in tutt'e due i pezzi**: il 37 **non si riproduce**, e Mutter pesa il **22 %** del ritardo. Il **78 % è nostro**, quasi tutto nel codificatore in software |
> | ⛔ *«non è un difetto nostro»* | ⛔ **è un difetto nostro.** Ed è la riga che questa fase ha smentito nel modo più utile |
>
> ⚠ **E la cura dello step 1 riesce, ma non salva il numero**: monitor 120 + freno 90 danno `[M]`
> **61,4** fotogrammi al secondo — e il ritardo **non si muove**, perché il collo è altrove. La
> cadenza non è il ritardo (`LEZIONI.md` §6.2).
>
> ⭐ **Che cosa ha funzionato del metodo**: dichiarare l'attesa prima ha reso **visibile** lo
> scarto. Un'attesa non scritta si sarebbe riadattata al risultato, e nessuno avrebbe notato che la
> fase è entrata credendo di misurare la colpa di Mutter ed è uscita con la propria.

---

## Come è divisa: cinque step

⭐ **Su richiesta dell'utente, il 13 agosto 2026**: la fase è tagliata in **cinque step**, e a
ciascuno sono assegnati **uno o due agenti**, che si occupano di **sviluppo, prova e correzione**.
Il taglio segue le dipendenze, non delle fette arbitrarie.

| # | Step | Che cosa produce | Dipende da | Porta |
|---|---|---|---|---|
| **1** | ⭐ **La cadenza disaccoppiata** | la misura **M3** di `gnome.md` §13: `maxFramerate` rinegoziato **da solo**, a monitor fermo | — | 7601 |
| **2** | ⛔ **La scena che si dichiara** | la scena, il conto dei suoi disegni, la marca e il suo lettore | — | 7602 |
| **3** | **Il prodotto: uno stream per fotogramma** | cattura continua · chiave/delta · l'intestazione da 28 byte · `RESET_STREAM` · il credito di stream | 1, 2 | 7603 |
| **4** | **La pagina: i fotogrammi consegnati** | molti stream in parallelo · FIN contro RESET · l'ordine · il buco → `RICHIEDI_CHIAVE` · ⭐ **il conto dei fotogrammi DIPINTI** | 3 | 7604 |
| **5** | ⭐ **L'anello del ritardo (S4)** | il numero, i sette controlli di `web.md` §6.3, e il pezzo cieco dichiarato | 4 | 7605 |

⛔ **Ogni step ha porta, file di ban e socket propri**: in fase 3 i banchi girano in parallelo per
davvero, e due banchi che condividono un ban-file si fermano a vicenda.
⚠ **Le tre porte che non si toccano**: **7448** (prodotto di casa), **7501** (bersaglio di P5) e
soprattutto **7561**, che è **quella che l'utente apre** ed è anche il bersaglio del metro — si
legge, non si tocca.

⭐⭐ **E il mandato degli agenti è di REFUTARE, non di verificare.** È la lezione che il 13 agosto
ha prodotto il risultato migliore della giornata: la riga su cui si stava per chiedere il giudizio
è stata smentita da chi era mandato a smentirla, e uno mandato a *verificare* l'avrebbe confermata.
⭐ **E il mandato ammette il rifiuto**: una cura passata dall'alto può essere sbagliata, e chi cura
deve poterla rifiutare con un caso.

---

## ⭐ Che cosa la fase 3 eredita, con due occasioni dentro

| | |
|---|---|
| ⭐ **M6 si può chiudere** | «il fotogramma è del giro prima» è l'unico controllo che vede quel guasto, e **non è mai stato misurato sulla catena vera** perché mancava la cattura del giro precedente. In fase 3 i giri precedenti **ci sono** |
| ⭐ **il `giro` di M8 si può riaprire** | oggi è dichiarato **NON APPLICABILE** perché il prodotto non conosce il nome del giro del banco. Con un `numero` che cresce a ogni fotogramma la domanda torna ponibile ⇒ [`rapporti/F2-6-giudizio.md`](rapporti/F2-6-giudizio.md) |
| ⛔ **P15** | `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto dove un orologio decide**. La fase 3 è tutta tempo — è qui che si scopre se regge |
| ⛔ **il punto cieco a monte della cattura** | il metro non guarda prima della cattura, e con molti fotogrammi il punto cieco **si allarga** |
| ⛔ **«due utenti, ciascuno vede la propria sessione»** | non lo copre nessun banco (metà positiva scoperta). Col movimento diventa **più caro** sbagliarlo, non meno |
| ⚠ **`02-figlio-accendi.sh:165`** | conta i figli **di tutti** invece dei propri: si accende solo quando due banchi girano in parallelo, **e in fase 3 girano** |

### Gli esiti delle sei eredità, alla chiusura

| | esito |
|---|---|
| ⭐ **M6** | ✅ **chiusa**: da `[?]` a `[M]`, ⛔ **col limite della catena scritto accanto** — mancano la cattura PipeWire e la tela del browser riletta, quindi non è la catena intera |
| ⭐ **il `giro` di M8** | ✅ **riaperto**: la dichiarazione *«NON APPLICABILE per costruzione»* **cade**, con il `numero` che cresce a ogni fotogramma il controllo è **eseguibile** |
| ⛔ **P15**, il secondo di grazia | ⏳ non è quel che ha morso. L'orologio che ha fatto danni in questa fase è stato un altro: quello **del banco**, non del protocollo (§P1 a blocchi, `LEZIONI.md` §1.13) |
| ⛔ **il punto cieco a monte della cattura** | ⛔ **si è allargato come previsto, e adesso ha un numero**: 16-40 ms non compresi nel 74,58. ⚠ E **su Xvfb non esiste**: la stima vale per l'utente, non per il banco |
| ⛔ **«due utenti, ciascuno vede la propria sessione»** | ⭐ **il prezzo è stato pagato, non rinviato**: il deposito del video è sparito **del tutto** — non «uno per sessione», **nessuno**. ⏳ Il banco che copre la metà positiva **resta da scrivere** |
| ⚠ **`02-figlio-accendi.sh:165`** | ✅ **curato** `[R]` — ⛔ **e non eseguito**: la cura è letta nel codice, non girata. Non porta la marca `[M]` |

---

## Lo stato della macchina all'apertura

⛔ *Verificato il 13 agosto 2026, non ricordato.*

| | |
|---|---|
| **albero** | pulito, `f2f21c2` |
| ⭐ **il catalogo dei banchi** | **15 su 15 certificati oggi**, zero scadute, zero non riverificabili — `python3 banchi/01-b12-guasti.py --registro`, rieseguito **all'apertura della fase 3** |
| ⏳ **la scadenza del giorno** | `01-s1b-eccezione.sh oggi` — **4 controlli su 4**, a **2,50 giorni su 7**; la scadenza che Chrome si è segnato è il **2026-08-17T21:09:47Z** |
| ⚠ **le porte in ascolto** | 7448, 7501, 7561 — le sole `:7xxx` |

⛔ **E va detto in anticipo**: la fase 3 tocca `rcp.c` e la pagina, e **curare il prodotto fa
scadere le certificazioni che lo guardavano**. Il catalogo va ricontato alla chiusura, non
all'apertura soltanto.

> ⭐ **È successo esattamente così, ed era previsto dal documento** — quindi non è una riga da
> correggere, è **la riga da rieseguire**. Alla sera del 13 agosto il catalogo dava **5 su 15**, con
> **10 scadute**, e ⛔ **nove banchi nuovi non erano ancora a catalogo** con le loro impronte:
> **sei numerati** — `03-b14` · `03-b15` · `03-b16` · `03-b17` · `03-b18` · `03-b19` — **più tre
> senza numero**: `03-scena`, `03-marca`, `03-deposita`.
> ⚠ **I tre senza numero sono quelli che si dimenticano**, ed è la ragione per cui il conto si fa
> con `ls banchi/03-*` e non a memoria: un catalogo contato sui nomi che uno ricorda è un catalogo
> che dichiara un denominatore falso (`LEZIONI.md` §1.9, regola 5).
> ⚠ **La ricontata si fa a codice fermo e a documenti scritti**, non prima: è la stessa ragione per
> cui questo documento si aggiorna tutto insieme alla chiusura.

---

## Che cosa è stato sviluppato

⛔ *Scritto alla chiusura, **a codice fermo**, dai numeri dei sei gruppi di lavoro — non a memoria.*

### ⭐ Il numero della fase, che è quel che la fase esisteva per produrre

`[M]` **ritardo cattura → vetro: mediana 74,58 ms** — min 50,4 · p05 58,1 · p95 101,2 · p99 138,1,
**6 giri** da ~800 campioni ciascuno, errore d'orologio **±0,63 ms**.
⛔ **Pezzo cieco 16-40 ms NON compreso** ⇒ sullo schermo dell'utente **90-115 ms**, contro un tetto
di **50**. ⇒ ⛔⛔ **SFORA il tetto e il traguardo.**
⚠ **Non è input → vetro**: il canale di input nasce alla fase 4 (`input` = 0 in **953 su 953**), e
al suo posto sta il controllo **P1**.

| dove se ne va | mediana | di chi è |
|---|---|---|
| disegno → cattura (il `pts` di Mutter) | 16,66 ms | Mutter — **22 %** |
| ⛔ **cattura → primo byte in pagina** | **39,17 ms** | ⛔ **nostro** — codificatore in software |
| il filo | 0,32 ms | — |
| stream completo → `decode()` | 0,08 ms | nostro |
| decodifica | 7,58 ms | nostro |
| richiamo → disegno finito (due `drawImage`) | 10,51 ms | nostro |

⛔⛔ **Il muro non è di Mutter, e le tre prove sono queste**: la scena disegna **59,98/s con 0
attese**; il figlio del prodotto consegna **23,93/s con ZERO attese a vuoto** — *non aspetta mai
Mutter*; il codificatore è **in software** e lo dichiara il prodotto stesso (libsvtav1 / libx265).
⇒ **58 ms su 74,6 sono nostri**, ~39 nel solo tratto cattura→filo. **La cura è la fase 8.**

### La tavola dei cinque step, con gli esiti

| # | Step | Che cosa ha prodotto | Esito |
|---|---|---|---|
| **1** | ⭐ **La cadenza disaccoppiata** (M3) | `[M]` monitor **120** + freno **90** ⇒ **61,4** consegnati (60,04), mediana **16,66 ms** — cella **D**, pulita. ⚠ E la spiegazione, che è `[R]`: `min_interval_us = 10⁶/maxFramerate` **troncato a intero** contro un tick da 16666,67 µs — una **quantizzazione**, non un battimento, **letta nel codice di Mutter** | ⭐ **il fatto riesce** — ⛔ **ma M3 è MEZZA, non chiusa**: la causa non è misurata, il prodotto non sa chiedere quella cadenza, e la causa scritta in tre documenti era sbagliata |
| **2** | ⛔ **La scena che si dichiara** | `banchi/03-scena.c` — `wl_shm` + `xdg-shell`, marca a **144 bit**, quattro conti fra cui le **attese**, verifica `wl_surface.enter` — e il suo lettore | ✅ **34 verdi / 0 rossi**. M6 chiusa `[M]`, il `giro` di M8 riaperto |
| **3** | **Il prodotto: uno stream per fotogramma** | **135 fotogrammi**, `numero` 1→135 · **132 delta e 3 chiavi** · il primo dopo `SESSIONE` è una **chiave con FIN** · `RICHIEDI_CHIAVE` → chiave in **≤ 200 ms** · **10 stream azzerati contro 18 con FIN**, nessuna chiave abbandonata, **E8 provata sul filo** · ⭐ nei 28 byte il **`pts` di Mutter** (scarto dal nostro `CLOCK_MONOTONIC`: **11 347 µs**) · ⭐ **il deposito del video sparito del tutto** | ✅ **6 punti su 7 chiusi** · 13 controlli di certificazione, **13 verdi** · giro dal vivo **8 verdi, 1 rosso** |
| **4** | **La pagina: i fotogrammi consegnati** | **60,0 fotogrammi dipinti al secondo** offrendone 60; tetto a saturazione **127,6/s** a 1080p | ✅ **19 casi verdi**, **8 guasti innestati su 8 accusati** |
| **5** | ⭐ **L'anello del ritardo (S4)** | il numero qui sopra. **P1** verde (N=25 → **+25,08**; N=60 → **+58,58**), con l'iniezione **fuori dal prodotto** e l'ancora d'orologio che **non ci passa**. **P3** verde **sui pixel veri**: 234 fotogrammi in movimento, **0 falsi positivi** | ✅ **banco 31 su 31, ponte 11 su 11** — ⛔ **ma P5 NON ESEGUITO, e adesso lo dice** |

> ⛔⛔ ⚠ **La riga dello step 1 diceva un'altra cosa, e va detto che cosa diceva.** *Fino alla sera
> del 13 agosto 2026 portava: «13 punti, 8 confermano, 0 smentiscono» e l'esito «⭐ **M3 chiusa, e
> riesce**». ⛔ **Falso tutt'e due.** Il file degli esiti della griglia,
> `banchi/03-b14-esiti-griglia.jsonl`, porta **tre righe**: il terreno e **due celle**
> (`griglia-apertura-120` e `griglia-freno-90`), e **tutt'e due portano `scena_sul_mio_monitor:
> false`** ⇒ sono rifiutate dal banco stesso, che sul verdetto stampa «⛔ la legge NON regge su **0
> punti su 0**». **Corretta il 13 agosto 2026**, rilievo del coordinatore della fase 3, verificato
> sui due file di esiti.*
>
> | | |
> |---|---|
> | ✅ **che cosa sopravvive** | tutto quel che sta in `banchi/03-b14-esiti.jsonl`: sette celle, **tutte** con `scena_sul_mio_monitor: true` — A (60/60 → 31,5), B (120/120 → 82,9), C (120/60 → 46,13), ⭐ **D (120/90 → 61,4, mediana 16,66, p99 20,43)** e i tre controlli. E con loro il **«sei decimi non si riproducono»** (la A dà 0,50 pulito) e il **«37 non si riproduce»** |
> | ⛔ **che cosa cade** | la **legge della griglia verificata**. La quantizzazione torna `[R]`: resta la spiegazione migliore che abbiamo, coerente con la cella D, **ma è letta nel codice di Mutter, non misurata** |
> | ⛔ **e cade anche** | il **riscontro incrociato**: in `banchi/03-b14-esiti-scena2.jsonl` la cella D porta `scena_sul_mio_monitor: false` e **1 fotogramma in 25 s**, e il controllo di ritorno di quella scena non torna. ⇒ **il 61,4 ha una scena sola** |
> | ⚠ **e M3** | **non è chiusa: è mezza** — il fatto è `[M]`, la causa `[R]`, il riscontro non c'è (`gnome.md` §13) |
>
> ⭐⭐ **E la cosa che vale più della correzione**: la ragione del rifiuto è **la trappola numero uno
> della giornata** — *la scena deve stare sul monitor che si sta catturando* — che stamattina era
> già costata **quattro giri** ad altri due gruppi ed era già stata scritta in `LEZIONI.md` §1.1.
> ⛔ Il banco **lo aveva scritto nel proprio file**, campo `scena_sul_mio_monitor: false`, e nessuno
> l'ha guardato: si è letto il numero e non la riga accanto. ⇒ *Un banco che dichiara la propria
> invalidità non serve a niente se chi legge guarda solo il risultato* — `LEZIONI.md` §1.1-bis.

### ⭐ E tre cose che il prodotto sa fare adesso e non sapeva stamattina

1. ⭐ **il deposito del video non esiste più.** Il prezzo dichiarato il 12 agosto — *«due utenti
   insieme non possono vedere tutt'e due il proprio»* — **è pagato**, e la cura non è «un deposito
   per sessione»: è **nessun deposito**. `wt_video_deposita` non esiste;
2. ⛔ **la cura B-18**, che è la più cara di tutte a non averla: uno dei tre percorsi di abbandono di
   un delta **non accendeva** la richiesta di chiave ⇒ **un solo delta saltato per mancanza di posto
   sfasciava l'immagine per sempre e in silenzio** — il `numero` non veniva consumato, quindi nessun
   buco, quindi il client non poteva chiedere la chiave, e con un GOP infinito non ne arrivava più
   una da sola;
3. ⛔ **la pagina nel worker**, scritta per intero, **misurata e tenuta spenta** — vedi qui sotto.
   ⭐ È uno sviluppo finito nella colonna delle cose che non hanno funzionato, **e ha prodotto lo
   stesso una riga utilizzabile**: `[M]` la **decodifica** fuori dal thread principale vale
   **−3,44 ms**; è la **tela** che affonda il conto (+17,6).

---

## ⛔ Che cosa non ha funzionato

⭐ *Si riempie anche quando fa una brutta figura — è la regola 2 del modello. E questa fase ne ha
prodotta abbastanza da riempirla: ci vanno i **giri buttati**, le **cure rifiutate**, e i **banchi
che hanno accusato il prodotto a torto**.*

### ⛔⛔⛔ 0. LA PEGGIORE, e non è stata trovata da un banco: è stata trovata **rileggendo un piano**

*13 agosto 2026, sera, a codice fermo, sulla richiesta dell'utente di **controllare che il piano
della sessione nuova non avesse problemi**.*

Il piano della sessione seguente si apriva con una corsia dichiarata *«quella da cui comincia la
sessione»*: **dare al banco un palco con una GPU vera**. Nasceva da una conclusione scritta la notte
prima, e scritta con la fermezza di una misura ripetuta — *«`[M]` 5 giri validi su 5:
`isConfigSupported` è `false` per tutte le stringhe HEVC. E la causa vera: su **Xvfb non c'è GPU
affatto** ⇒ non è un problema di codec, è un problema di PALCO»*.

⛔⛔ **Era la bandiera `--disable-gpu` del banco stesso** (`03-b17-ritardo.py:626`). La sonda
chiedeva a un browser **accecato da lei** se vedesse.

| Chrome, stesso Xvfb, stesso script, **una sola variabile** | webgl | HEVC |
|---|---|---|
| **senza** `--disable-gpu` | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
| **con** `--disable-gpu` | `niente webgl` | no |

⭐⭐ **E non è rimasta una dichiarazione**: il flusso uscito da `hevc_vaapi` è stato fatto
**dipingere** allo stesso Chrome — `[M]` **5 giri su 5**, 1920×1080, **119 fotogrammi su 120**,
`powerEfficient: true`.

⚠ **Il segnale c'era, ed era stato archiviato**: il piano stesso annotava *«un giro della sonda ha
detto HEVC = true con GPU, e non si è più riprodotto (0 su 5 successivi)»*, catalogandolo come
**anomalia da inseguire**. ⇒ Era **l'unico giro giusto**. *Un esito che non si riproduce una volta
su sei non è rumore: è una **variabile non dichiarata**.*

⭐ **Quel che NON è successo, e va detto perché era il rischio grosso**: `03-b17-ritardo.py:582` ha
**`gpu=True` di default** — `--senza-gpu` è opt-in ⇒ ⛔ **il numero della fase, i 74,58 ms, NON era
misurato al buio.** Era **la sonda dei codec** a esserlo, non la misura.

⇒ **Costo**: una corsia intera di un piano, e la sessione seguente sarebbe cominciata da lì.
⇒ **Riga nuova per `LEZIONI.md`, ed è la §2.0**: *un banco che risponde «no» deve scrivere **con che
palco** ha risposto* — «non c'è» e «non ho potuto guardare» hanno lo stesso aspetto, e il secondo è
più frequente del primo.

### ⛔ 1. I giri buttati, e sono tutti dello stesso errore

⛔ **La scena stava sul monitor sbagliato**, e i monitor virtuali erano **quattro**. Una scena
aperta su quello che non si stava catturando produce un banco che **gira, non fallisce, e misura il
palco di qualcun altro**. *Costo: **quattro giri** — due allo step 3 e due allo step 1.*
⚠ E la stessa forma è arrivata come **cura passata dall'alto**: *«accendi su `Meta-3`»* — il monitor
giusto era `Meta-2`, e seguirla avrebbe fatto misurare il palco di un altro gruppo.
⇒ **Riga nuova per `LEZIONI.md` §1.1**: *la scena deve stare sul monitor che si sta catturando*, che
su un palco con monitor virtuali **non è quello dell'utente**.

### ⛔⛔ 2. Le cure passate dal coordinatore e RIFIUTATE — cinque, e avevano ragione tutte e cinque

*È il risultato di metodo della giornata, e va scritto qui perché l'imputato è chi coordinava.*

| la cura passata | perché è stata rifiutata |
|---|---|
| la `ResizeObserver` | ⛔ **la premessa era falsa** |
| la seconda cura della vista | ⛔ **caduta alla misura**: `overflow-y: scroll` tiene `clientWidth` **fermo** |
| il **seqlock in contesa** | ⛔ **200 letture su 200 riuscite** con la scena a 1034 disegni/s. La causa era un **relitto a `seq` dispari**, non la contesa |
| *«quel che manca ai 60 è di Mutter»* | ⛔ **zero attese a vuoto** |
| *«accendi su `Meta-3`»* | ⛔ i monitor sono **quattro**, il suo era `Meta-2` |

⭐ **E il mandato ammetteva il rifiuto**, che è la ragione per cui i cinque si sono visti. Una cura
passata dall'alto può essere sbagliata, e chi cura deve poterla rifiutare **con un caso**.

### ⛔⛔ 3. I banchi che hanno accusato il prodotto a torto

1. ⛔⛔ **lo `STREAM_LIMIT_ERROR`, ed è la specie peggiore: il banco aveva creato lui la condizione,
   e illegalmente.** Doveva provare che il prodotto regge un credito basso, e annunciava
   `initial_max_streams_uni = 6` **dopo** la stretta di mano — cosa che **RFC 9000 §4.6 vieta** ⇒
   ⛔ **il `6` non è mai passato sul filo.** `[M]` il server aveva **128 posti concessi** e ne ha
   aperti **14**. ⇒ **`ngtcp2` non ha violato niente, e lì il prodotto non ha un difetto.** ⚠ Il
   prodotto reagiva **correttamente** a una condizione impossibile, e la reazione corretta è stata
   letta come il guasto. ⭐ Ma cercandolo è uscito **B-18**, che era vero e peggiore;
2. ⛔ **«nessuna delle tre porte protette è in ascolto»**: misura presa dalla **macchina sbagliata**
   — il controllo girava su CHUWI, e 7448/7501/7561 ascoltano su **NIC-OS**. Verificato: `ss -ltn`
   su `192.168.0.2` le dà tutt'e tre vive, più la **7603** dello step 3;
3. ⛔ **la mia diagnosi del seqlock in contesa era sbagliata**, ed è la stessa specie: accusava il
   lettore mentre il difetto stava nella scena.

### ⛔⛔ 4. Un verde in catalogo lo produceva lo STRUMENTO — ed era peggio di un falso verde

**Non era falso nel merito: non era mai stato provato capace di arrossire.** Su Xvfb i quadri non
girano, e in Blink l'evento `resize` si consegna **dentro** il giro di rendering ⇒ senza quadri non
arriva mai. A svegliare la conduttura era `Page.captureScreenshot`, chiamata solo `if args.copia`:
⛔ **un'opzione di comodo di stampa**, con un effetto collaterale non dichiarato.

| il banco ORIGINALE, sul prodotto SANO | esito |
|---|---|
| **senza** `--copia` | ⛔ **ROSSO, 5 pretese cadute** — fra cui «la tela è stata RICOMPOSTA (1 → 1)» |
| con `--copia` | verde (1 → 3) |

⛔ **E il buco strutturale**: le **quattro** pretese di quel blocco **non erano mai state innestate
con nessun guasto**. Verdi da sempre, senza che nessuno sapesse se sapessero fare altro.
⭐ **Curato**: il quadro si batte apposta (5 battiti fissi, non «finché diventa verde»); una spia del
palco conta quadri ed eventi; ⭐ **si giudica prima il palco** — se il `resize` non è arrivato il
banco dice *«IL PALCO, NON IL PRODOTTO»* e si ferma; due guasti nuovi accusano 5 e 4 pretese.
Tre giri: **9 giri, 5 scene sane verdi, 4 pagine guaste rosse**.
⚠ **Stessa trappola armata altrove e oggi non vulnerabile**: un secondo banco regge solo perché
nessuna sua pretesa passa da un quadro. Chi ve ne aggiunga una ci cade, **in verde**.

### ⛔⛔ 5. La scena che correva a vuoto, e i suoi due sintomi erano lo stesso difetto

**Causa unica**: `buffer_libero()` chiamava `wl_display_dispatch()` **da dentro un gestore di
eventi** ⇒ `disegna()` annidata ⇒ da un `wl_surface.frame` in volo se ne fanno due, e si moltiplica.
⚠ Si accende **solo fuori da casa sua**: serve che i tre buffer siano occupati insieme, cioè un
compositore più carico — **quel che succede quando accanto gira una cattura**.

| | sano | guasto innestato | risanato |
|---|---|---|---|
| `fidato` | true | **false** | true |
| `frame` in volo, max | **1** | **18** (fino a 26) | 1 |
| disegni/s a 60 Hz | 60 | **461,7** (fino a 1034) | 60 |

⭐ **E i due sintomi erano lo stesso difetto**: una scena in corsa a vuoto non torna al ciclo
principale ⇒ ignora `--secondi` (**6 chiesti, 146 vissuti**) ⇒ il banco la **uccide** ⇒ la morte cade
a metà scrittura ⇒ `seq` del seqlock resta **dispari per sempre**. Il lettore vecchio falliva **3 su
3**, non «ogni tanto».
⭐ **Il rilevatore misura la CAUSA, non il ritmo**: *«i `wl_surface.frame` in volo non possono mai
essere più di 1»* — un invariante di protocollo, che non ha bisogno di sapere a che frequenza va il
monitor. E lo **stato d'uscita porta il verdetto** (2 = letto ma NON fidato), così `set -e` ferma chi
legge i disegni senza guardare `fidato`. **Chiusa: 43 righe verdi, 0 rosse.**

⛔⛔ **RIGA CHE VALE PER TUTTO IL PROGETTO**: *ogni cella di ritmo misurata con `03-scena` **prima**
del 13 agosto va rifatta o marcata `[?]`* — la scena poteva correre a vuoto senza dirlo.
⭐ **Le celle che contano dello step 1 reggono**: `banchi/03-b14-esiti.jsonl` usa `03-b14-scena`
(EGL, sua), e la matrice dei tetti rifatta con la cura è **invariata** (60,0-60,2 disegni/s,
0 attese).

> ⛔ ⚠ *Questa riga diceva: «**Il riscontro incrociato dello step 1 regge** […] ⇒ l'accordo **entro
> il 4 %** fra due scene indipendenti tiene». **Non regge.** La seconda scena del riscontro è
> proprio `03-scena`, cioè quella che questa stessa riga dichiara da rifare — e in
> `banchi/03-b14-esiti-scena2.jsonl` la sua **cella D** porta `scena_sul_mio_monitor: false`,
> `palco_stabile: false` e **1 fotogramma in 25 s**, mentre il suo controllo di **ritorno** dà 52,84
> contro gli 80,28 della sua cella B: **non torna**. Il 4 % vale su A (0,7 %), B (3,2 %) e il
> controllo positivo; C sta al **5,4 %** e il negativo al **7 %**. ⇒ ⛔ **La cella D — il 61,4 — ha
> UNA scena sola.** Corretta il 13 agosto 2026, rilievo del coordinatore della fase 3.*

### ⛔ 6. Il metro si stava regalando 11 ms, e P5 si dichiarava verde senza esserlo

1. ⛔ **la prima stesura del metro chiudeva al richiamo del decodificatore**, regalandosi **~11 ms**
   nostri e misurabili su un tetto di 50. ⭐ **Il confine è stato spostato nella direzione scomoda**:
   il numero è salito da **63,8 a 74,6** e lo si è lasciato salire;
2. ⛔ **P5 si dichiarava verde**, e dopo tre iniettori `scavalcati = 0` non è *«l'anello regge»*: è
   *«il fenomeno non si è presentato»*. Adesso è dichiarato **NON ESEGUITO**. ⚠ E la causa vera del
   fuori ordine è la **dimensione** del fotogramma, non la rete: l'evento scatta al completamento
   dello stream, quindi l'ordine d'arrivo è quello delle dimensioni — e **una chiave grossa viene
   scavalcata dai delta**.

### ⛔ 7. La pagina nel worker: scritta, misurata, e **sbagliata a metà**

`web.md` §6.1 la prescriveva. Attuata, ha dato `[M]` **+27,6 / +33,5 ms** di mediana (73,66 / 67,79
→ **101,30**) e **tetto −73,4 %** a 1080p (127,6 → **33,9** dipinti/s). ⛔ **Ma il totale nasconde
la cosa che serve**, e la scomposizione la mostra:

| tratto (mediana, ms) | prima | dopo | Δ |
|---|---|---|---|
| stream completo → `decode()` | 0,07 / 0,06 | **10,23** | ⛔ **+10,2** |
| ⭐ **la decodifica** | **7,17** / 6,13 | ⭐ **3,73** | ⭐ **−3,44 / −2,40** |
| richiamo → disegno finito | 9,63 / 9,11 | **27,19** | ⛔ **+17,6** |

⭐⭐ **⇒ §6.1 non è sbagliata per intero: vale la DECODIFICA, non la TELA.** Il decodificatore
consegna prima quando non contende; è la tela che affonda il conto. ⇒ La riga utilizzabile non è
*«il worker è sbagliato»* — quella sarebbe solo una porta chiusa — ma *«la decodifica sì, la tela
no»*, che dice dove mettere il confine.

⭐ **E il meccanismo è la scoperta che cambia una regola**: `transferControlToOffscreen` **impegna la
tela al ritmo del quadro** — un `requestAnimationFrame` implicito che nessuno ha scritto. ⛔⛔ **La
prescrizione conteneva la propria smentita**: §6.1 prescriveva il worker e vietava il salto di
quadro, che il worker reintroduce in silenzio. Nessuna rilettura del documento poteva accorgersene
senza misurarla.

⚠ **E le due grandezze dicono cose opposte**: sulla catena vera il worker dipinge **di più**
(26,3/s contro 22,8-24,2), a saturazione crolla di tre quarti (`LEZIONI.md` §6.2).

⏳ ⛔ **`[?]` E questo va letto accanto ai numeri, non in fondo**: tutto è su **Xvfb, in software,
senza GPU**, e la penale è in gran parte sincronizzazione al quadro. ⇒ **Su hardware vero il conto
va rifatto prima di seppellire §6.1.** Il codice resta dietro `#video=worker`, **spento**, proprio
perché quel giorno il numero si rifà senza riscrivere niente (`DECISIONI.md` §2.8).

### ⚠ 8. E le cose che non hanno funzionato senza essere colpa di nessuno

- ⛔ **`src/pagina.c:243`**: `strcmp(percorso, "/")` ⇒ `/?qualunque-cosa` prende **404** (`[M]`: `/`
  → 200 / 166107 byte, `/?video=worker` → 404 / 9). ⇒ **`?tela=desincronizzata` non è MAI stato
  raggiungibile**, e il commento della pagina indica da sempre una strada che non esiste. Non visto
  da nessuno perché i banchi servono la pagina da un `http.server` di Python, che il `?` lo ignora;
- ⛔ **i due gemelli `rcp.c` divergevano**, e **il prodotto non compilava per nessuno**. Riallineati
  la sera del 13;
- ⚠ **`weston-simple-egl` non è installato** sulla macchina di prova (rootfs in RAM), mentre due
  documenti lo davano presente e uno lo prescriveva come scena. Ha smesso di essere un riferimento:
  la scena della fase 3 è la nostra;
- ⚠⚠ **`/tmp` è una tmpfs da 3,8 G al 94 %**, 246 M liberi: ha già fatto fallire un giro di
  `03-b16` (Chrome non parte). ⛔ **Non è stata svuotata di proposito** — dentro ci sono le prove
  dei giri di oggi, e buttarle toglierebbe la **provenienza** dei numeri di questa fase.

---

## Il giudizio dell'utente

⏳ *La fase si chiude su **una misura giudicata dall'utente**, non su un documento completo.*

---

## ⏳ Il punto lasciato APERTO dall'utente — il debito di chiave strozzato

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**a freddo non si può prendere una decisione:
l'esperienza potrebbe essere migliore di quello che si teme. Lasciamo il punto aperto**».*

⛔ **E la decisione è metodologicamente giusta, non una rinuncia**: è `LEZIONI.md` §2.6 — *l'utente
non è il banco*. Curare sulla base di un sintomo **temuto** invece che **osservato** è scrivere una
tolleranza su una grandezza che nessuno ha misurato (`LEZIONI.md` §1.13).

### Che cos'è

`rcp_video_serve_chiave()` **non ha nessun chiamante in `src/`**: il debito di chiave arriva al
codificatore solo per una strada laterale (`webtransport.c:1352`), **strozzata a una richiesta al
secondo**. Il prodotto è **conforme** a `RCP.md` §5.2 — la chiave arriva — ma paga il ritardo.

⛔ **E il numero non è quel che sembra: `[M]` 343 delta buttati in un giro solo NON sono 343
intoppi. Sono UNO, moltiplicato.** La catena:

1. si butta **un** fotogramma (legittimo, §5.1 — «si butta il passato quando è passato»);
2. scatta il debito di chiave (§5.2);
3. il server **rifiuta tutti i delta** finché la chiave non è pronta;
4. ⛔ ma la richiesta passa da una strada che ne lascia passare **una al secondo**;
5. ⇒ per quel secondo, **tutto quel che il prodotto produce viene buttato**.

⇒ A 60 fotogrammi al secondo, **un abbandono legittimo ne genera fino a sessanta illegittimi**, e
il sintomo — l'immagine che resta rotta **per un secondo intero** dopo un singolo intoppo — è
precisamente quel che un utente chiama *«va a scatti»* senza saper dire perché.

### ⭐ Come si chiude, e costa ZERO lavoro in più

Il prodotto **scrive già ogni abbandono nel registro**: `RCP.md` §5.1 lo impone — *«un fotogramma
perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto dal lato che riceve»*.

⇒ ⭐ **Basta leggere il registro DOPO la sessione in cui l'utente dà il giudizio.** Tre numeri, e
decidono da soli:

| che cosa si legge | che cosa dice |
|---|---|
| quante volte il debito di chiave è scattato | se sulla rete vera l'evento **capita** o no |
| quanti delta sono stati buttati per ciascuno | se il moltiplicatore è **60** o **2** |
| quanto è passato fra l'abbandono e la chiave | se il secondo di strozzatura si paga davvero |

⛔ **Se il debito non scatta mai sulla LAN dell'utente, il punto si chiude come `[?]` che non morde
qui** — e va nominato alla fase in cui la rete è cattiva per davvero. **Se scatta, il numero dice di
quanto**, e la cura si giustifica su un fatto invece che su un timore.

⚠ **Quel che NON va fatto**: chiudere questo punto perché il desktop *sembrava* fluido. La sessione
del giudizio si guarda **e si legge**, ed è la stessa disciplina con cui la fase 2 è stata chiusa —
davanti a un elenco, non a un'impressione.

---

## ⏳ Il secondo punto lasciato APERTO dall'utente — dove finisce di contare il tetto

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**alla tua domanda si può rispondere solo dopo
aver misurato i risultati con l'accelerazione HW**».*

### La domanda che oggi nessun documento risponde

`SPECIFICHE.md` §3.2 chiede **≤ 50 ms**. ⛔ **Ma non dice fino a dove si conta**, e la fase 3 ha
scoperto che la differenza non è accademica:

| dove si smette di contare | con la codifica di **oggi** (software) | con un codificatore **gratis** `[R]` |
|---|---|---|
| al **disegno finito** | **74,58 ms** ⇒ fuori | **~35,4 ms** ⇒ ⭐ **dentro il tetto, vicino al traguardo** |
| al **pixel acceso** (col pezzo cieco) | 90-115 ms ⇒ fuori | **51-75 ms** ⇒ ⛔ **fuori anche a fase 8 fatta** |

⇒ **La stessa architettura è promossa o bocciata a seconda di dove si mette il traguardo.**

⚠ *E il confine della **misura** è stato spostato oggi, nella direzione scomoda: la prima stesura
dell'anello chiudeva al richiamo del decodificatore, regalandosi ~11 ms nostri e misurabili. Il
numero è salito da 63,8 a 74,58 ed è stato lasciato salire. `CODER.md` §1-bis dichiara adesso dove
finisce la **misura** — non fino a dove vale il **tetto**, che è questa domanda.*

### ⛔ Perché NON si decide adesso, e sono due ragioni indipendenti

1. **il pavimento con l'accelerazione vera non è misurato**, e non lo sarà finché la fase 8 non
   esiste;
2. ⛔ **il pezzo cieco è a sua volta una `[?]`**: **16-40 ms** è una forbice larga **due volte e
   mezzo**, e nessuna API JavaScript la espone (`web.md` §6.2). Decidere dove finisce di contare un
   tetto di **50** appoggiandosi a un numero che oscilla di **24** è decidere su niente — ed è la
   grandezza sostitutiva che `LEZIONI.md` §1.13 vieta.

⇒ È la stessa disciplina del primo punto aperto: **non si cura, e non si decide, su un sintomo
temuto invece che osservato** (`LEZIONI.md` §2.6).

### ⛔ E una cosa che va detta perché non venga letta male

**Il «codificatore finto» misurato in fase 3 NON è un codificatore hardware.** Risponde a
*«la catena regge quando la codifica costa poco?»*, che è una domanda utile e **diversa**. Un
codificatore vero in hardware ha un profilo di ritardo suo — la consegna alla GPU, l'attesa della
fine, il ritorno dei byte — che un finto **non modella affatto**.
⇒ ⛔ **Quel numero dice se l'architettura ha margine, NON quanto varrà la fase 8.** Le due cose non
si sommano, e chi le sommasse otterrebbe una previsione che nessuno ha misurato.

### ⭐ Come si chiude

Alla **fase 8**, e nell'ordine:

1. si misura l'anello **con la codifica in hardware**, con lo stesso banco (`03-b17-ritardo.py`) e
   la stessa scena, così i due numeri si sottraggono davvero;
2. si guarda **dove cade il totale al disegno finito**, e **quanto vale davvero** il tratto della
   codifica quando è la GPU a farla;
3. ⛔ **solo allora** la domanda «fino al disegno o fino al vetro» ha davanti due numeri veri invece
   di una forbice, e l'utente decide **sapendo che cosa costa ciascuna delle due letture**.

⚠ **Quel che NON va fatto**: scrivere in `SPECIFICHE.md` una risposta oggi. Una soglia decisa per
prudenza, e poi trovata comoda, è una soglia che si sposta di un passo a ogni rilettura — è la
famiglia **P8 → P11 → P13 → P14**, che questo progetto ha già percorso quattro volte.

---

## ⭐⭐⭐ LA FASE NON SI CHIUDE QUI — la codifica in hardware è anticipata dentro la fase 3

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**si anticipa la codifica HW alla fase 3. Per
questo però dopo servirà una nuova sessione**».*

⛔ **Quindi tutto quel che sta scritto sopra è vero e NON è finale.** Il documento resta com'è —
non si riscrive una misura perché è arrivata una decisione — e questa sezione dice **che cosa manca
ancora prima del giudizio**.

### Perché, in un numero

Il ritardo misurato è **74,58 ms**, e ⛔ **39,17 di quelli — il 53 % — sono la codifica in
software**. Gli altri quattro tratti sommano **~35,4 ms**, che sarebbe il **pavimento della catena a
codificatore gratis**: `[R]` **dentro il tetto dei 50, e vicino al traguardo dei 40**.

⇒ L'obiezione dell'utente, che è quella giusta: *«senza accelerazione hw stiamo ragionando e
sviluppando su numeri non molto affidabili»*. Un totale dominato da un pezzo che sta per essere
sostituito **non è un numero su cui prendere decisioni** — e le fasi 4-7 ne produrrebbero altri
uguali, da rifare dopo.

⚠ **Ma il danno era stretto, e va detto perché non si legga la giornata come persa**: dei risultati
della fase 3, **solo il verdetto sul ritardo** dipendeva dal codificatore. La cella **D** (61,4 a
monitor 120 e freno 90), il verde prodotto dallo strumento, **B-18**, **B-20**, il worker respinto,
la scena che correva a vuoto e i tre falsi rossi **non ci si appoggiano affatto**.

> ⛔ ⚠ *Questa riga cominciava l'elenco con «**La legge della griglia**». **Va tolta di lì**: la
> legge della griglia non è mai stata misurata — le due celle della griglia sono rifiutate dal banco
> stesso (riquadro nella tavola dei cinque step). Al suo posto sta la **cella D**, che è pulita e
> regge. **Corretta il 13 agosto 2026**, rilievo del coordinatore della fase 3.*

### ⭐⭐ E si può fare — `[M]` verificato il 13 agosto sul server

```
Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
```

⛔ **E questa riga corregge un errore di oggi**: un agente aveva riferito *«su questo server non c'è
un codificatore hardware per nessuno dei due codec»*, e **nessuno l'aveva verificata**. È vera per
**AV1** — e stava già nei documenti — ed è **falsa per HEVC**. ⚠ È la stessa forma dei «37
fotogrammi di Mutter»: una riga **ripetuta** invece che **misurata**, che poi decide un piano.

### Che cosa manca, e in che ordine

| | |
|---|---|
| 1 | ⛔ **il primo scoglio, e va affrontato per primo**: il codec negoziato nelle misure di oggi è **AV1**, perché la sonda HEVC di Chrome **fallisce su Xvfb** (`EncodingError`). Senza un client che accetti HEVC, l'anello intero non si misura — al massimo si misura il lato server, e sarebbe **mezzo anello** |
| 2 | la codifica HEVC in hardware nel prodotto, **su una copia** finché non è misurata |
| 3 | ⭐ **l'anello rimisurato con lo STESSO banco e la STESSA scena** — o i due numeri non si sottraggono |
| 4 | ⛔ **i CINQUE tratti affiancati**, non il totale: *tolta la codifica in software, gli altri quattro restano dove sono?* Se restano, l'architettura è **assolta**; se si muovono, c'è una contesa che nessuno ha visto |
| 5 | ⚠ **i fotogrammi consegnati accanto ai millisecondi** (`LEZIONI.md` §6.2): in v1 il costo per fotogramma scese da 41 a 6 **mentre i consegnati calavano da 29 a 22,7** |
| 6 | e **solo allora** il giudizio dell'utente, su un numero che non ha il freno a mano tirato |

⚠ **`EncSliceLP` è la codifica «a bassa potenza»**: veloce, ma con limiti suoi di qualità e di
funzioni. **Non è equivalente** alla codifica piena, e va dichiarato accanto al numero.
⭐ **E porta un'occasione**: `EncSliceLP` è l'entrypoint che `web.md` nomina come *«da verificare»*
per i **sotto-livelli temporali** — cioè la strada per abbandonare un fotogramma **senza rompere
quelli dopo**, che oggi costa una chiave ogni volta.

⛔ **Che cosa NON si anticipa**: la **copia zero** resta alla fase 8. È lavoro suo, e non tocca
questo numero.
