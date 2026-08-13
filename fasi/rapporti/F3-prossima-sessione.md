# La sessione nuova — il piano di lavoro, in corsie parallele

*Scritto la notte del 13 agosto 2026, **a codice fermo**, alla fine della giornata che ha misurato
la fase 3. ⭐ Deciso dall'utente: **la codifica in hardware si anticipa dentro la fase 3**, e la
fase **non si chiude** finché non è fatta. ⭐ E su sua richiesta, l'elenco è **raggruppato per poter
lavorare in parallelo**.*

⛔ **Questo file è il compagno del riquadro «DA QUI SI RIPRENDE» del `README.md`**: là c'è il
*perché*, qui c'è il *chi fa che cosa, quando, e senza pestare i piedi a chi*.

---

## 0. Come si legge questo piano

**Sei corsie.** Quattro partono **subito e insieme**; due sono **serie** e aspettano un ricongiungimento.

```
          ┌── A  IL CLIENT HEVC ────────────┐
subito ───┼── B  LA CODIFICA HW ────────────┼─▶ GIUNZ. 1 ─▶ E  L'ANELLO RIMISURATO ──┐
  in      ├── C  I 74,58: [M] o [?] ────────┘                    (finestra esclusiva) │
parallelo └── D  IL SECONDO MOTORE ────────────────────────────────────────────────── ├─▶ GIUDIZIO
                                                                                      │
  K1 ─┬─ K2 ─┬─ K3 ─┬─ K4 ─┬─ K5 ─┐                                                   │
      │      │      │      │      │  ← a VENTAGLIO, una porta e una scheggia ciascuno  │
      └──────┴──────┴──────┴──────┴─▶ UNIONE del registro ─▶ K6 ─▶ GIUNZ. 2 ───────────┘
                                        (l'unico passo in serie)
```

⛔ **La regola che rende il parallelo possibile, ed è stata pagata oggi**: *ogni corsia ha **porta,
file di ban, socket, registro e COPIA del prodotto propri**. Due banchi che condividono un ban-file
si fermano a vicenda.* E il perimetro dei **file** è dichiarato per corsia: chi ne ha bisogno di uno
altrui **lo chiede al coordinatore**, non lo tocca.

⚠ **Le porte protette, sempre**: **7448** (prodotto di casa) · **7501** (bersaglio di P5) · ⛔
**7561, quella che l'utente apre** — si leggono e **non si toccano**.

---

### ⛔⛔ 0-bis. LE DUE FAMIGLIE DI LAVORO, E SI PARALLELIZZANO IN MODO OPPOSTO

*⭐ Deciso su richiesta dell'utente: **anche i test, le misure e le certificazioni si fanno in
parallelo**. ⛔ Ma non tutte allo stesso modo, e la differenza non è di comodo: **è la differenza
fra un numero e un numero falso**.*

| | **CORRETTEZZA** — «il banco sa dire di no?» | **TEMPO** — «quanto ci mette?» |
|---|---|---|
| che cosa | certificazioni · guasti innestati · conformità al protocollo · sano→guasto→risanato | l'anello del ritardo · la cadenza · i fotogrammi al secondo · i tetti a saturazione |
| esito | un **codice d'uscita** | un **numero** |
| ⇒ **si parallelizza?** | ⭐⭐ **SÌ, senza limite pratico** | ⛔⛔ **NO — o si misura la contesa** |
| perché | l'esito non dipende da quanto la macchina è carica: un guasto innestato si vede lo stesso | ⛔ **due misure di ritmo sono state buttate il 13 agosto proprio così**, perché *«il prodotto dell'utente stava ciclando»*. `[M]`, non una precauzione |

⭐ **Quindi il parallelo si fa su DUE assi diversi**, e vanno tenuti separati:

**1. La correttezza va a ventaglio.** N corsie insieme, ciascuna con la propria copia, la propria
porta e ⛔ **la propria SCHEGGIA DI REGISTRO** — `01-b12-registro-<corsia>.jsonl` — che a fine giro
si **unisce**. ⭐ **E il meccanismo esiste già**: il progetto unisce e rispecchia da sempre due
registri, uno per macchina (*«le due copie unite e rispecchiate, 90 giri»*, e il 13 agosto
*«registro unito e rispecchiato: le due macchine sono identiche»*). ⇒ **Da due schegge a N è la
stessa cosa**: quel che va aggiunto è che l'unione **rifiuti** due righe in conflitto invece di
prenderne una — ed è già successo il 13 agosto, due giudizi caduti **nello stesso secondo**, e
l'unione **l'ha detto**.

**2. Il tempo va a finestre esclusive.** Chi misura un tempo prende **il palco in esclusiva**, e
⛔ **non basta prenderlo: va DICHIARATO e VERIFICATO**. È la stessa forma di `LEZIONI.md` §1.1 —
*una misura senza la scena dichiarata non è una misura* — portata sulla macchina invece che sulla
scena:

> ⛔ **Il banco che misura un tempo controlla di essere solo, e lo scrive accanto al numero**: carico
> della macchina, quali altre sessioni grafiche sono vive, quali altre porte `:76xx` rispondono,
> quanti processi del prodotto girano. ⭐ **E se non è solo, RIFIUTA di misurare** invece di
> consegnare un numero. Un numero preso con un vicino che cicla ha lo stesso aspetto di uno buono.

⚠ **E le finestre sono DUE, una per macchina**, quindi anche il tempo ha del parallelo dentro:
**NIC-OS** (cattura, codifica, il server) e **CHUWI** (i browser, la decodifica, il disegno)
⇒ una misura lato server e una lato client **possono girare insieme**, purché nessuna delle due
attraversi l'altra macchina. ⛔ **L'anello del ritardo le attraversa tutt'e due**: quando gira lui,
**tutt'e due le finestre sono sue**.

⚠ **Anche `/tmp` è una risorsa condivisa su CHUWI** (tmpfs da 3,8 G, il 13 agosto al 94 %): quattro
corsie che lanciano browser insieme la riempiono, e il sintomo **accusa la pagina** invece del
disco. Chi lancia browser dichiara quanto spazio serve, e lo libera a fine giro.

---

## 👥 L'ORGANICO — **fino a 10 agenti**, deciso dall'utente

⭐ *E ciascuno con **porta, ban, socket, registro, scheggia di catalogo e COPIA del prodotto
propri**. Il perimetro dei **file** è la cosa che rompe il parallelo prima delle porte: è dichiarato
qui, e chi ha bisogno di un file altrui **lo chiede al coordinatore**.*

| # | agente | corsia | quando parte | porta | perimetro dei file |
|---|---|---|---|---|---|
| **1** | ⛔ **il punto cieco del catalogo** | **K1** | ⛔⛔ **PER PRIMO, da solo** — dieci minuti, e sblocca il n. 2 | — | `01-b12-guasti.py` + registro |
| **2** | **il client HEVC** | **A** | subito, in parallelo al n. 1 | 7621 | `banchi/03-hevc-*` (nuovi) |
| **3** | ⛔ **l'anello: i 74,58 sono `[M]` o `[?]`** | **C** | subito | 7623 | `banchi/03-b17-*` |
| **4** | **il secondo motore** | **D** | subito | 7624 | `banchi/03-ff-*` (nuovi) |
| **5** | ⭐ **la codifica HEVC in hardware** | **B** | ⛔ **quando il n. 1 ha consegnato** | 7622 | `src/codificatore.*` · `figlio.c` · `Makefile` — ⛔ **solo nella COPIA** |
| **6** | ⭐⭐ **il refutatore del n. 5** | **B** | quando il n. 5 consegna | 7632 | copia **sua**; del n. 5 **legge**, non scrive |
| **7** | le marche: `03-scena` · `03-marca` · `03-deposita` | **K2·K3** | dopo il n. 1 | 7625 | `03-scena*` · `03-marca*` · `03-deposita*` |
| **8** | le marche: `03-b16` + la copia ad albero | **K2·K4** | dopo il n. 1 | 7626 | `03-b16-*` |
| **9** | ⛔ **le marche a TEMPO**: `03-b14` · `03-b19` | **K2** | dopo il n. 1, ⛔ **in finestra esclusiva** | 7627 | `03-b14-*` · `03-b19-*` |
| **10** | propagazione su NIC-OS · `03-b15-lancia.sh` · ⭐ **l'unione delle schegge** | **K5·K7** | dopo il n. 1 | 7628 | NIC-OS · `03-b15-lancia.sh` · l'unione |

**Al ricongiungimento**, senza aggiungere agenti:
- ⭐ **il n. 3 diventa la corsia E** — possiede già `03-b17-*`, quindi il *prima* e il *dopo* escono
  dalla stessa mano e **si sottraggono davvero**;
- ⭐ **il n. 1 o il n. 10 fa K6**, le cinque certificazioni scadute per il `Makefile`.

### ⛔ Le due contese da arbitrare, e le arbitra il coordinatore

| | |
|---|---|
| ⛔⛔ **la finestra esclusiva** | il n. **9** e la corsia **E** misurano tutt'e due un **tempo** ⇒ **non possono girare insieme**, e nemmeno accanto a un vicino che cicla. `[M]` il 13 agosto due giri di griglia interi sono stati **buttati** proprio così. ⇒ **Una alla volta, e il banco verifica di essere solo** (§0-bis) |
| ⚠ **`/tmp` su CHUWI** | i n. **2**, **4**, **8** e **9** lanciano browser: tmpfs da 3,8 G, il 13 agosto al **94 %**. Ciascuno dichiara quanto gli serve e **libera a fine giro**, o il sintomo accuserà la pagina invece del disco |

⭐ **E il mandato di tutti e dieci è di REFUTARE, non di verificare** — e **ammette il rifiuto**: se
la cura che arriva dal coordinatore è sbagliata, si rifiuta **con un caso**. Il 13 agosto è successo
**sette volte su sette**, e avevano ragione loro tutte e sette.

---

## ⏱ PRIMA DI TUTTO — il coordinatore, dieci minuti, da solo

*Non è una corsia: è la precondizione di tutte.*

| | |
|---|---|
| **P1** | **Lo stato, verificato e non ricordato**: albero pulito · `ss -ltn` ⛔ **su 192.168.0.2, non su CHUWI** (l'errore è già stato fatto oggi) · `python3 banchi/01-b12-guasti.py --registro` |
| **P2** | ⏳ **La scadenza**: `bash banchi/01-s1b-eccezione.sh oggi`, una volta al giorno **fino al 18 agosto**. Il 13: 4 controlli su 4, 2,50 giorni su 7; Chrome si è segnato **2026-08-17T21:09:47Z** |
| **P3** | ⛔ **I commit di `banchi/`**, rimasti fuori dalla sessione del 13 (~46 voci: nove banchi nuovi, le cure ai vecchi, il catalogo). Erano in scrittura da due gruppi quando la sessione è finita. ⚠ **Si committano PRIMA di far partire le corsie**, o il primo giro sporca uno stato mai committato |
| **P4** | ⚠ **`/tmp` su CHUWI è una tmpfs da 3,8 G al 94 %**. Si libera `/tmp/google-chrome` e `/tmp/claude-*`; ⛔ **si guarda prima di cancellare il resto**: dentro ci sono le **prove** dei giri del 13 |

---

## 🅐 CORSIA A — ⛔ **IL PALCO SENZA GPU** — e la domanda è già stata risposta

> ### ⛔⛔ **RISPOSTA GIÀ DATA la notte del 13 agosto: NO, un client che accetta HEVC su questo palco NON esiste.** E la causa **non è HEVC**.
>
> `[M]` **5 giri validi su 5**, nell'ambiente esatto del banco (Xvfb + `google-chrome` 151 coi flag
> di `03-b17-ritardo.py:620`): `isConfigSupported` è **`false`** per **tutte** le stringhe HEVC
> (`hev1.1.6.L93`, `hev1.2.4.L120`, `hvc1.*`) e **`true`** per AV1. **Ecco perché si negozia AV1.**
>
> ⭐⭐ **E la causa vera**: su **Xvfb non c'è GPU affatto** — la stessa pagina risponde *«niente
> webgl»*. Chrome **non ha un decodificatore HEVC in software**, quindi senza VAAPI dice no.
> ⇒ **Non è un problema di codec: è un problema di PALCO.**
>
> ⚠ *E questa riga corregge la mia: non è che «la sonda fallisce con `EncodingError`» — nel giro
> vero **non ci arriva nemmeno**, si ferma prima, a `isConfigSupported`.*

**⇒ La corsia cambia mestiere: non «trovare un client HEVC», ma «dare al banco un palco con una
GPU vera».** ⭐ **Ed è da qui che comincia la sessione, non dal codificatore** — il codificatore
hardware **c'è e funziona già**, misurato (vedi corsia B).

| | |
|---|---|
| **Che cosa** | ⭐ CHUWI **ha una GPU**, e il Chrome del banco monta un `gpu-process` su `renderD128` **sotto Wayland**. ⛔ Ma il palco lo lancia su **Xvfb** (`03-b17-ritardo.py:604`), dove GPU non ce n'è. ⇒ **Portare il palco dove la GPU c'è** |
| **La domanda** | *Con un browser su GPU vera, `isConfigSupported` dice sì a HEVC Main10?* E se sì, **la catena intera si misura**. Chrome sotto Wayland · Chrome con `--ozone-platform` · il telefono (che HEVC Main10 lo dipinge già, `[M]` 13 agosto) |
| ⚠ **Un'anomalia da inseguire** | ⛔ **un giro della sonda ha detto HEVC = `true` con GPU, e non si è più riprodotto** (0 su 5 successivi). Non ci si costruisce sopra niente — ⭐ **ma se fosse raggiungibile sbloccherebbe tutto**, quindi si insegue |
| **Perimetro file** | `banchi/03-palco-*` (nuovi). ⛔ **Niente `src/`, niente `.md`, nessun banco `03-b1x` esistente** |
| **Porta / palco** | **7621** · browser veri su CHUWI |
| **Dipende da** | niente. ⭐ **È la corsia che sblocca tutte le altre: parte per prima e con la persona migliore** |
| **Consegna a** | ⛔ **GIUNZIONE 1**, ed è la metà che può bloccarla |
| **Ripiego se resta NO** | si misura il **lato server soltanto**, e ⛔ **si dichiara che è mezzo anello** — non lo si spaccia per l'anello. ⚠ In quel caso l'anello intero resta col codec **AV1**, e la fase 8 andrà misurata su AV1 in software contro HEVC in hardware, che **non è un confronto pulito** e va detto |

---

## 🅑 CORSIA B — La codifica HEVC in hardware nel prodotto

**Parte subito. È il lavoro grosso.**

> ### ⭐⭐ IL CODIFICATORE HARDWARE È GIÀ STATO MISURATO — `[M]` la notte del 13 agosto
>
> Stesso fotogramma **1920×1080 a 10 bit**, 120 fotogrammi, sul server:
>
> | codificatore | ms per fotogramma | byte in uscita |
> |---|---|---|
> | **libsvtav1 preset 10** — ⛔ **quello in uso oggi** | **22,23** | 5 550 007 |
> | libx265 `medium` | 36,00 | 2 821 318 |
> | libx265 `ultrafast` | 11,58 | 2 803 676 |
> | ⭐⭐ **hevc_vaapi / renderD128** | ⭐ **2,85** | 4 595 717 |
> | hevc_vaapi / renderD129 | 3,43 | 4 371 626 |
>
> ⇒ ⭐ **Circa otto volte più veloce di quel che gira adesso.** Il pezzo grosso dei 39 ms è
> aggredibile per davvero.
>
> ⛔ **E tre avvertenze, perché il numero non venga letto per più di quel che è:**
> 1. **è mezzo anello**: è la portata di `ffmpeg` **in blocco e pipelined**, non il ritardo per
>    fotogramma nel cammino **seriale** del prodotto ⇒ **sottostima la latenza**;
> 2. è **`EncSliceLP`**, la codifica a bassa potenza — non è equivalente alla piena;
> 3. il contenuto è **sintetico**, non la scena vera.
>
> ⚠⚠ **E una correzione che cambia il bersaglio**: il codec negoziato oggi è **`codec 2` = AV1**,
> quindi il codificatore che fa i 39 ms è **SVT-AV1**, ⛔ **non x265**. Chi arrivasse con una
> manopola per x265 non toccherebbe niente — *è già successo il 13 agosto, e chi l'aveva preparata
> l'ha rifiutata da sé prima di consegnarla.*

⭐ `[M]` **L'hardware c'è**, verificato il 13 agosto sul server:

```
Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
```

| # | | |
|---|---|---|
| **B1** | la codifica HEVC Main10 via VA-API | ⛔ **su una COPIA** finché non è misurata, mai sull'albero del deposito |
| **B2** | **quale nodo di rendering** | ce ne sono **due** (`renderD128`, `renderD129`): si stabilisce e **si dichiara**, non si indovina |
| **B3** | ⚠ **`EncSliceLP` è la codifica «a bassa potenza»** | veloce, ma con limiti suoi di qualità e di funzioni. **Non è equivalente** alla piena: si dichiara **accanto al numero** |
| **B4** | ⚠ **chiave/delta e `RICHIEDI_CHIAVE` con VA-API** | i codificatori hardware trattano le **chiavi forzate** diversamente da quelli software. ⇒ `03-b15-movimento.py` **va rigirato per controllo** — non perché la certificazione scada, ma perché **è il posto dove guarderei per primo** |
| **B5** | ⛔ **che cosa NON si anticipa** | la **copia zero** resta alla fase 8 |
| **B6** | ⭐ **l'occasione dentro l'occasione** | `EncSliceLP` è l'entrypoint che `web.md` nomina come *«da verificare»* per i **sotto-livelli temporali**: la strada per **abbandonare un fotogramma senza rompere quelli dopo**, che oggi costa **una chiave ogni volta**. ⚠ **Non farla dentro questa corsia**: si nomina, si misura la fattibilità, e diventa lavoro suo |

| | |
|---|---|
| **Perimetro file** | `src/codificatore.c` · `src/codificatore.h` · `src/figlio.c` · `src/Makefile` — ⛔ **e SOLO nella copia sul server**. ⚠ Nessun `.md`, nessun banco |
| **Porta / palco** | **7622**, copia del prodotto sul server, ban+socket+registro propri |
| **Dipende da** | **K1** (il punto cieco del catalogo) — vedi corsia K, ed è una cosa da dieci minuti |
| **Consegna a** | ⛔ **GIUNZIONE 1** |

---

## 🅒 CORSIA C — I 74,58 ms sono `[M]` o `[?]`?

**Parte subito. ⛔ È la domanda più urgente di tutte, e non dipende da nessuno.**

> ### ⭐⭐ **C1 e C2 SONO GIÀ CHIUSE la notte del 13 agosto — e il numero REGGE**
>
> ⛔ **Non era una differenza di macchina: era una REGRESSIONE**, e l'affermazione *«i 31/31 erano su
> NIC-OS»* è **smentita con un caso**. Tutt'e due gli esiti sono scritti **sulla stessa macchina**,
> nel registro del banco:
>
> | ora | esito |
> |---|---|
> | 12:46 → **13:18:28** | PROMOSSO **31/31**, sei giri |
> | **13:24:28** → 14:35 | BOCCIATO **30/31**, otto giri, sempre lo stesso rosso |
>
> `03-b17-ponte.py` ha mtime **13:23**; il `.pyc` **13:23:53**; il primo giro bocciato si chiama
> `b17-20260813-**132353**` — **coincidenza al secondo**.
> ⭐ **Il meccanismo**: la logica della «raffica» aggiunta alle 13:23 ritarda i pacchetti dal 2° al
> 40° **tutti di 60 ms** ⇒ l'ordine si conserva, `inversioni = 0`, **per aritmetica, su qualunque
> macchina**. Degenera quando `raffica % fo == 0`: `[M]` raffica 1→13 inversioni, **2→0**, 3→7,
> **4→0**, 5→5, **6→0**. ⭐ Rimesso il ponte a com'era, **su CHUWI**: **PROMOSSO 31/31**.
>
> ⭐ **E il ponte NON è rotto**: l'iniettore vero gira a `fo=400, raffica=4` — **non degenera**, e
> riordina benissimo. Cade solo l'**autoprova**, che usa `fo=2`, un assetto che **il banco non usa
> mai**. Il difetto vero è un **modo di degenerazione silenzioso**: per certe parità smette di
> riordinare e ritarda tutto uniformemente, **senza dirlo**.
>
> ⛔ **E la mia ipotesi «è la stessa lacuna di P5» è stata RIFIUTATA con un caso**: sono due livelli
> diversi — qui **datagram UDP su loopback**, dove riordinare è banale (13 inversioni con
> raffica=1); P5 fallisce sui **fotogrammi su stream QUIC**. ⇒ **Curare il ponte non renderebbe P5
> eseguibile.**

> ### ⭐⭐⭐ **I 74,58 ms RESTANO `[M]`** — ma la ragione non era quella scritta
>
> ⭐ **L'accoppiamento è per CONTENUTO, non per posizione**: `ritardo_ms = t_dip −
> marca["istante_us"]` — ogni fotogramma porta **il proprio istante di partenza dipinto nei suoi
> pixel**. `[M]` sul verbale vero (804 campioni): mediana **74,576** in ordine originale,
> **74,576** mescolata a caso, **74,576** invertita. ⇒ ⛔ **Un fuori ordine NON PUÒ spostare la
> mediana**, e il controllo che cade **non la mina**.
> ⭐ **Riprova indipendente la sera stessa, stesso banco stessa scena: 72,19 ms** (n=417), P1 P2 P3
> P6 P7 P8 verdi. **Il numero è riproducibile.**
>
> ⛔ **Ma tre correzioni, e la prima è grave:**
> 1. ⛔⛔ **il rilevatore di P5 è CIECO PER COSTRUZIONE**: il prodotto scarta i fuori ordine a
>    `src/pagina.html:1576`, **prima** del decodificatore; il banco guarda solo **dopo**.
>    ⇒ *«0 fuori ordine»* è **un'identità algebrica, non una misura**. Su una rete che riordinasse
>    davvero, i fotogrammi scavalcati **sparirebbero dal campione** e P5 direbbe ancora «non
>    eseguito». ⛔ **Il limite non è «non so se l'anello reggerebbe» — è «il banco non può
>    accorgersene»** ⇒ si guarda `scartati_ordine` **del prodotto**, che l'informazione ce l'ha già
>    (e dice **0 su 7 672** consegnati);
> 2. ⚠ **«0 su 783 spontanei» è un numero FOSSILE**, incollato nei commenti: il giro vero ha **804**
>    campioni, e il P5 giudicato ne ha **213**;
> 3. ⛔ **`giri_verdi: 6` è gonfiato — sono 3.** Il giro da 72,794 aveva **P3 rosso**, e P3 valida
>    proprio l'`istante_us` che entra nel ritardo ⇒ ⛔ **`73,69` (il consolidato) va a `[?]`**;
>    ⭐ **`74,576` (il giro finale) resta `[M]`**.
> ⚠ *E il giro finale era partito da una certificazione **BOCCIATA**: l'ultima promossa prima del
> numero della fase è quella delle 13:18:28.*

| # | che cosa RESTA da fare | |
|---|---|---|
| **C3** | ⛔⛔ **rifare il rilevatore di P5, che oggi è cieco** | non nel ponte — **nel banco**: si guarda `scartati_ordine` del **prodotto**. Finché non lo si fa, *«P5 non eseguito»* e *«tutto a posto»* hanno **lo stesso aspetto** |
| **C4** | **il modo di degenerazione del ponte** | va **nominato o curato**, ⛔ ma la cura onesta è **riscrivere il controllo** perché misuri quel che il ponte fabbrica adesso — **non mettere una toppa dispari** |
| **C5** | **marcare `73,69` come `[?]`** e togliere il numero fossile «783» dai commenti | e ⚠ il registro **non conserva quale parte di P3 fosse rossa**: è un limite del registro, non del giro |

| | |
|---|---|
| **Perimetro file** | `banchi/03-b17-*` |
| **Porta / palco** | **7623**, copia propria |
| **Dipende da** | niente |
| **Consegna a** | ⭐ **subito al coordinatore** — e a **E**, che rimisurerà con lo stesso banco |

---

## 🅓 CORSIA D — Il secondo motore

**Parte subito. Indipendente da tutto.**

| | |
|---|---|
| **Che cosa** | `SPECIFICHE.md` §11.5 vuole **due motori**; i numeri sono di **Chrome soltanto**. ⭐ I **mattoni** sono già verificati su due (`crossOriginIsolated` true anche nel worker, `VideoDecoder`, `WebTransport`, `OffscreenCanvas`, trasferimento di `ReadableStream`); ⛔ **mancano i NUMERI**, perché i banchi passano dal CDP e Firefox non ce l'ha — e non apre finestre su Xvfb |
| **La strada già trovata** | ⭐ far **rimandare gli esiti alla pagina stessa**, con Firefox `--headless`: è così che i mattoni sono stati verificati il 13 |
| **Perimetro file** | `banchi/03-ff-*` (nuovi) |
| **Porta / palco** | **7624** · Firefox 140.13.0esr su CHUWI |
| **Dipende da** | niente |
| **Consegna a** | il coordinatore. ⚠ Se ci arriva **prima** della giunzione, i suoi numeri entrano nel giudizio; se no, resta `[?]` **dichiarata**, forma d'errore **E10** — che è già la posizione onesta di oggi |

---

## 🅚 CORSIA K — Il catalogo: **a ventaglio**, con un solo punto di cucitura

⭐ **Le certificazioni sono lavoro di CORRETTEZZA** (§0-bis) ⇒ **si parallelizzano senza limite
pratico**: ogni banco si certifica **contro la propria copia del prodotto, sulla propria porta**, e
l'esito è un **codice d'uscita**, che non cambia se la macchina è carica.

⛔ **L'unica cosa che NON si parallelizza è la SCRITTURA nel catalogo** — `banchi/01-b12-guasti.py`
e `01-b12-registro.jsonl`. ⇒ ⭐ **E non serve serializzare il lavoro per serializzare la scrittura**:
ogni certificatore scrive la **propria scheggia** — `01-b12-registro-<corsia>.jsonl` — e a fine
ventaglio **si uniscono**.
⭐ **Il meccanismo esiste già e non va inventato**: il progetto unisce e rispecchia da sempre **due**
registri, uno per macchina. Da due schegge a N è la stessa cosa. ⚠ Quel che va aggiunto è che
l'unione **rifiuti** due righe in conflitto invece di prenderne una a caso — e il 13 agosto è già
successo: due giudizi caduti **nello stesso secondo**, e l'unione **l'ha detto**.

⛔⛔ **E restano DUE VINCOLI D'ORDINE, che non sono negoziabili e non c'entrano col parallelo**: uno
in testa (**K1**) e uno in coda (**K6**). Nel mezzo, tutto va a ventaglio.

| # | quando | | |
|---|---|---|---|
| **K1** | ⛔ **PER PRIMO, e blocca la corsia B** | **IL PUNTO CIECO** | **Nessuna certificazione guarda `codificatore.c`. Nessuna. E nemmeno `figlio.c`.** ⇒ Si può riscrivere il codificatore da capo a fondo e il conto direbbe *«15 su 15, tutto verde»*. Non è nato oggi — si vede **adesso** perché adesso la corsia B sta per lavorare proprio lì. ⭐ **Costa due righe, e va fatto prima che B scriva un carattere** |
| **K2** | mentre A-B-C-D girano | **le marche dei banchi nuovi** | sette sono a catalogo come **MAI PROVATI**, col campo `marca` **vuoto di proposito** — *una marca si **misura**, e una dedotta dal sorgente è la forma d'errore già pagata su B4 e B7*. ⭐ Su `03-marca` poggia la mediana **74,58 ms**: se ce n'è una che vale, è quella. ⛔ **Meglio tre misurate bene che sette dedotte** |
| **K3** | insieme a K2 | **`03-deposita` non è certificabile** | e non per la marca: **nessuno rilegge `03-scena-esiti.jsonl`**, quindi un guasto lascerebbe il giro verde. Il controllo mancante **costa due righe** |
| **K4** | insieme a K2 | **`03-b16` vuole una copia ad ALBERO** | e `prepara_copia()` non lo sa fare: va costruita a mano |
| **K5** | insieme a K2 | ⚠ **propagazione su NIC-OS** | là il conto legge **11/15** perché tre file di *banco* sono vecchi. Non tocca la validità — quei giri sono partiti da CHUWI — ma va allineato |
| **K6** | ⛔ **DOPO la giunzione 1** | **le certificazioni che scadono** | **cinque su quindici** — **B10 · B13 · P1 · P5 · P5R** — ⛔ e **nessuna per colpa del codificatore**: scadono perché guardano **`remotix/Makefile`**, che cambia per legare VA-API. ✅ **Reggono**: B3·B5·B6·B7·B8 (`rcp/rcp.c`) · B9 (`RCP.md`) · B2·B4·B11·C2 · 03-b14·03-b15·03-b18 (banchi propri) |
| **K7** | insieme a K6 | ⚠ **`03-b15-lancia.sh`** | usa ancora la porta 7603 e l'ordine vecchio **scena → misura**, che dà **zero fotogrammi** |

| | |
|---|---|
| **Perimetro file** | `banchi/01-b12-guasti.py` · `banchi/01-b12-registro.jsonl` · `banchi/03-scena*` · `banchi/03-marca*` · `banchi/03-deposita*` · `banchi/03-b14-*` · `banchi/03-b16-*` · `banchi/03-b19-*` · `banchi/03-b15-lancia.sh` |
| **Porte / palco** | ⭐ **7625-7639**, una per certificatore, **copia propria** ciascuno |
| **Registro** | ⭐ ciascuno scrive la **propria scheggia** `01-b12-registro-<corsia>.jsonl`; ⛔ **l'unione è l'unico passo in serie**, e **rifiuta** i conflitti invece di sceglierli |
| **⛔ I due vincoli d'ordine** | ⛔ **K1 PRIMA che B tocchi `codificatore.c`** — oggi **nessuna certificazione guarda quel file**, quindi finché K1 non è fatto la corsia B lavora **senza rete**. ⛔ **K6 SOLO DOPO** che il prodotto ha smesso di cambiare — rigirare le certificazioni mentre `src/` si muove le fa scadere **una seconda volta**, ed è l'errore che il 13 agosto è nato per non ripetere. ⭐ **Fra i due, tutto a ventaglio** |
| ⚠ **E K2 è dell'ALTRA famiglia** | le **marche** dei banchi nuovi si misurano con `sano → guasto → risanato`: ⭐ è **correttezza**, non tempo ⇒ va a ventaglio anche lei. ⛔ **Tranne per i banchi che misurano un TEMPO** — `03-b14` (la cadenza) e `03-b19` (i dipinti): la loro marca si prende **dentro una finestra esclusiva**, o si misura la contesa e la marca è finta |

---

## ⚡ GIUNZIONE 1 — quando A e B sono tutt'e due arrivate

⛔ **Non prima.** Con la sola B si misura mezzo anello; con la sola A non c'è niente da misurare.

---

## 🅔 CORSIA E — L'anello rimisurato, ed è il numero su cui la fase si chiude

**Parte alla giunzione 1.**

| # | | |
|---|---|---|
| **E1** | ⭐ **l'anello con la codifica in hardware** | ⛔ **STESSO banco (`03-b17-ritardo.py`) e STESSA scena** del 13 agosto, o i due numeri **non si sottraggono** |
| **E2** | ⛔⛔ **i CINQUE tratti affiancati, non il totale** | *tolta la codifica software, gli altri quattro restano dove sono?* ⇒ Se **restano** (Mutter ~16,66 · disegno ~10,51 · decodifica ~7,58 · filo ~0,32), la sottrazione `74,58 − 39,17 = 35,4` è **confermata** e **l'architettura è assolta**. Se **scendono** (meno contesa sulla CPU) o **salgono** (il pipelining nascondeva qualcosa), hai trovato **più** del numero che cercavi |
| **E3** | ⚠ **i fotogrammi consegnati accanto ai millisecondi** | `LEZIONI.md` §6.2: in v1 il costo per fotogramma scese da **41 ms a 6** *mentre i consegnati calavano da **29 a 22,7***. Con un numero solo in mano non si vede |
| **E4** | **quanto vale davvero il tratto della codifica** | 39 ms diventano 5 o 25? È il numero che dice se il tetto dei 50 si prende |

| | |
|---|---|
| **Perimetro file** | `banchi/03-b17-*` — ⚠ **ereditato dalla corsia C**, che a quel punto ha finito |
| **Porta / palco** | **7623**, la stessa di C, con la copia della corsia B montata dietro |
| **Dipende da** | ⛔ **A + B (giunzione 1)** · ⚠ **C** (se C dice che i 74,58 sono `[?]`, il «prima» va rifatto **anche lui**, o la sottrazione non vale) |

---

## ⚡ GIUNZIONE 2 — E consegnata, K6 rigirata

⇒ Da qui il prodotto è fermo, le certificazioni valgono, e il numero è di una configurazione che
**non ha più il freno a mano tirato**.

---

## 🏁 IL GIUDIZIO — e come si prepara

| | |
|---|---|
| ⭐ **Che cosa** | il desktop **che si muove**, dentro una scheda, e l'utente dice se è fluido |
| ⚠ **Come** | **davanti a un elenco**, come la fase 2: un'approvazione data senza sapere che cosa manca è un'approvazione al buio |
| ⛔ **E sono DUE giudizi distinti** | l'utente guarda **il suo** desktop, che si muove quando lo muove lui — **un'altra scena** da quella misurata. ⇒ Il suo giudizio dice *«è fluido abbastanza»*, e **non conferma né smentisce** il numero dell'anello. Valgono tutti e due, **separati** |
| ⭐⭐ **E la sessione del giudizio PRODUCE UN DATO** | ⇒ vedi **D1** qui sotto: si guarda **e si legge** |

---

## ⏳ I due punti che l'utente ha lasciato APERTI di proposito

⛔ **Non sono dimenticanze: sono decisioni.** Tutt'e due per la stessa ragione — *non si decide su
un sintomo temuto invece che osservato* (`LEZIONI.md` §2.6). Il dettaglio sta in
[`../03-movimento.md`](../03-movimento.md).

| | | come si chiude | quando |
|---|---|---|---|
| **D1** | **il debito di chiave strozzato a una richiesta al secondo** — `rcp_video_serve_chiave()` non ha chiamanti in `src/`, e ⛔ **un abbandono legittimo ne genera fino a sessanta illegittimi** | ⭐ **leggendo il registro della sessione in cui l'utente dà il giudizio**: il prodotto scrive già ogni abbandono (`RCP.md` §5.1). **Costa zero.** Tre numeri: quante volte scatta · quanti delta per volta · quanto passa fino alla chiave | ⛔ **subito dopo il giudizio**, non prima |
| **D2** | **dove finisce di contare il tetto dei 50 ms** — al **disegno** o al **pixel acceso**? Con un codificatore gratis fa **~35,4** al disegno e **51-75** sul vetro: *la stessa architettura è promossa o bocciata a seconda di dove si mette il traguardo* | **dopo la corsia E**, con due numeri veri davanti invece di una forbice. ⚠ Il pezzo cieco è a sua volta una `[?]` larga **due volte e mezzo** (16-40 ms). ⛔ **Non scrivere una risposta in `SPECIFICHE.md` prima**: una soglia decisa per prudenza e poi trovata comoda si sposta di un passo a ogni rilettura | dopo **E**, e la decide **l'utente** |

---

## 🚧 Le trappole già pagate — non si ripagano

*Ciascuna è costata dei giri buttati il 13 agosto. **Vanno lette da OGNI corsia prima di partire.***

| | |
|---|---|
| ⛔⛔ **la scena deve stare sul monitor che si sta catturando** — ⭐ **è la n. 1, ed è quella che è tornata** | il palco ha **quattro** monitor virtuali (`Meta-0…3`, tutti 1920×1080@60): il proprio si legge **dal registro del proprio server**, non si indovina. Una scena sul monitor sbagliato dà **zero fotogrammi per dieci secondi con la catena perfetta**. Costo: **quattro giri** — ⛔ **più il risultato più grosso della giornata**, vedi il riquadro qui sotto |
| ⛔ **la scena accesa PRIMA della sessione non disegna** | Mutter non manda i *frame callback* a una superficie su un monitor che nessuno registra. Si accende **a sessione aperta** |
| ⛔ **su Xvfb `requestAnimationFrame` non gira MAI** | 0 quadri in 3 s, con e senza GPU, a scheda «visible». Ogni cammino di prodotto che ci passa dietro è **codice morto sul banco** |
| ⛔ **`curl` normalizza** | non manda il frammento e si mangia il `?` vuoto. Sul filo grezzo serve `--request-target`, o si misura curl |
| ⛔ **`&` dentro `ssh → enter.sh → bash -c`** non arriva dove sembra | **si usa un file, non una riga annidata** |
| ⭐ **la parola d'ordine di `sudo` sta in `~/SERVER.ssh`** | convenzione del progetto (`banchi/02-pam-lancia.sh:59`). Un gruppo si è fermato **per non saperlo** |
| ⛔ **il prodotto legge `pagina.html` UNA VOLTA SOLA all'accensione** | dopo ogni modifica **si riaccende**, o si prova la pagina di prima |
| ⛔ **su CHUWI il prodotto NON si compila** | manca `nghttp3/nghttp3.h`. Vive in un contenitore su **192.168.0.2** (`enter.sh`, sorgenti `/srv/src/remotix`); i **browser veri** stanno su CHUWI |
| ⛔ **`src/rcp.c` e `banchi/rcp/rcp.c` sono GEMELLI** | il `Makefile` pretende che siano identici: se divergono **nessuno compila**, e non si vede finché non ci si sbatte contro |
| ⚠ **`/tmp` su CHUWI, tmpfs da 3,8 G al 94 %** | quando si riempie, Chrome non apre il profilo e il banco fallisce con un errore che **accusa la pagina**. Si guarda il disco **prima** di credergli |

> ## ⛔⛔⛔ E la trappola n. 1 è tornata a mordere **il risultato che la citava** — la sera stessa
>
> *Va letta prima delle altre, perché non è una trappola nuova: è quella già pagata quattro volte
> **la mattina dello stesso giorno**, e già scritta in `LEZIONI.md` §1.1.*
>
> Il pomeriggio del 13 agosto la «legge della griglia» di Mutter è stata dichiarata **verificata su
> 13 punti, 8 confermano, 0 la smentiscono**, ed è stata scritta in **nove documenti**. ⛔ Le celle
> della griglia erano **due**, e portavano tutt'e due `scena_sul_mio_monitor: **false**`.
>
> ⭐⭐ **Il banco lo aveva scritto nel proprio file.** Le ha contate **contaminate** e sul verdetto
> ha stampato per esteso *«⛔ la legge NON regge su 0 punti su 0»*. ⛔ **Nessuno ha guardato: si è
> letto il numero, e non la riga accanto.**
>
> | | |
> |---|---|
> | ⛔ **la regola che ne esce** | prima di copiare un numero in un documento si legge **il verdetto del banco**, non la cella. Se il banco ha un campo di validità, **quel campo si cita insieme al numero** — o non si cita il numero |
> | ⚠ **e perché non basta stare attenti** | un numero **verosimile non attiva nessun sospetto**: i 13 punti erano plausibili, il banco sapeva davvero produrli, e la spiegazione tornava |
> | ✅ **che cosa è sopravvissuto** | `banchi/03-b14-esiti.jsonl`, sette celle tutte `scena_sul_mio_monitor: true` ⇒ il **61,4** a monitor 120 e freno 90 resta `[M]`; la **causa** torna `[R]`; **M3 resta mezza** |
>
> ⇒ ⭐ **La lezione intera sta in `LEZIONI.md` §1.1-bis**: *un banco che dichiara la propria
> invalidità non serve a niente se chi legge guarda solo il risultato.* Corretto il **13 agosto
> 2026**, rilievo del coordinatore della fase 3.

---

## ⭐⭐ Il metodo — e il 13 agosto ha un conto che lo dimostra

**Gli agenti si mandano a REFUTARE, non a verificare.** ⭐ **E il mandato deve ammettere il
rifiuto**: la cura che arriva dall'alto può essere sbagliata, e chi cura deve poterla rifiutare
**con un caso**, non con un'opinione.

- **sette cure passate dal coordinatore rifiutate con un caso**, e avevano ragione **tutte e sette**;
- **un difetto attribuito al prodotto era del BANCO** — che annunciava il credito **dopo** la stretta
  di mano, contro RFC 9000 §4.6, e poi accusava il prodotto di non reggerlo;
- **un verde in catalogo lo produceva lo STRUMENTO** — una funzione di stampa opzionale svegliava il
  rendering, e quelle pretese non erano **mai** state innestate con un guasto;
- **tre falsi rossi** trovati nei banchi, che accusavano il prodotto mentre faceva la cosa giusta;
- ⛔ **e TRE righe ripetute invece che misurate hanno quasi deciso un piano**: i «37 fotogrammi di
  Mutter», *«non c'è un codificatore hardware»* — **la seconda nella stessa giornata in cui si
  scopriva la prima** — e ⛔⛔ **la «legge della griglia verificata su 13 punti»**, scritta in nove
  documenti mentre il banco aveva già stampato *«la legge NON regge su 0 punti su 0»*.
  ⭐ **La terza è la peggiore**: le prime due erano righe vecchie ripetute, questa è stata
  **prodotta oggi**, dallo stesso progetto che aveva appena scritto la lezione per evitarla.

⇒ ⭐ **Zero volte i banchi hanno sbagliato a favore del prodotto.**
