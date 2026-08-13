# La sessione nuova — il piano di lavoro, in corsie parallele

*Scritto la notte del 13 agosto 2026, **a codice fermo**, alla fine della giornata che ha misurato
la fase 3. ⭐ Deciso dall'utente: **la codifica in hardware si anticipa dentro la fase 3**, e la
fase **non si chiude** finché non è fatta. ⭐ E su sua richiesta, l'elenco è **raggruppato per poter
lavorare in parallelo**.*

> ## ⭐⭐⭐ RADDRIZZATO alle 20:40 del 13 agosto, **prima che partisse un solo agente**
>
> *L'utente ha chiesto di rileggere il piano «per controllare che non ci siano problemi». Il
> controllo è stato fatto **misurando lo stato**, non ricordandolo, e ha trovato quattro cose. ⛔ La
> più grossa è che **la corsia A poggiava su una conclusione FALSA**, e sarebbe stata la corsia da
> cui «comincia la sessione».*
>
> | | |
> |---|---|
> | ⛔⛔ **la corsia A è CANCELLATA** | non era «su Xvfb non c'è GPU»: era ⛔ **la bandiera `--disable-gpu` del banco stesso**. Tolta quella, la GPU c'è, HEVC dice sì, e il flusso del codificatore hardware **si dipinge**. `[M]` 5 giri su 5 — vedi la corsia A qui sotto |
> | ⛔⛔ **la codifica AV1 in hardware NON ESISTE** | e adesso è **misurata**, non dedotta: `av1_vaapi` esce **218** con *«No usable encoding profile found»*, 3 giri su 3. ⇒ Il codec negoziato oggi (`codec 2` = AV1) **non potrà mai** andare in hardware su questa macchina |
> | ⚠ **la corsia K è per metà GIÀ FATTA** | il piano diceva «sette MAI PROVATI su quindici»; il catalogo dice **24 banchi, 20 certificati, 4 mai provati**. Tre agenti del ventaglio diventano circa uno |
> | ⚠ **P3-bis fatto, P3 già fatto, P4 no** | le tre porte del 13 sono spente (sul server restano **solo** 7448 · 7501 · 7561, contate prima e dopo); i commit di `banchi/` c'erano già; ⛔ `/tmp` su CHUWI è al **98 %** |
>
> ⇒ ⭐ **La giunzione 1 non esiste più**: era «A e B tutt'e due arrivate», e A è caduta.
> **La strada critica è B → E**, e non ha più il ramo che poteva bloccarla.

⛔ **Questo file è il compagno del riquadro «DA QUI SI RIPRENDE» del `README.md`**: là c'è il
*perché*, qui c'è il *chi fa che cosa, quando, e senza pestare i piedi a chi*.

---

## 0. Come si legge questo piano

**Cinque corsie** (A è caduta). Tre partono **subito e insieme**; una è **serie** e aspetta B.

```
          ┌── ⛔ A  CANCELLATA ── una riga di cura alla sonda, non una corsia
subito ───┼── B  LA CODIFICA HW ──────────────▶ E  L'ANELLO RIMISURATO ─────────────┐
  in      ├── C  I 74,58: [M] o [?] ────────┘         (finestra esclusiva)          │
parallelo └── D  IL SECONDO MOTORE ────────────────────────────────────────────────  ├─▶ GIUDIZIO
                                                                                     │
  K1 ─┬─ K2 ─┬─ K3 ─┐                                                                │
      │      │      │  ← a VENTAGLIO, una porta e una scheggia ciascuno              │
      └──────┴──────┴─▶ UNIONE del registro ─▶ K6 ─▶ GIUNZ. 2 ─────────────────────  ┘
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

⛔ **RIVISTO alle 20:40 del 13**: da **dieci** agenti a **sei**. Tre righe sono cadute perché il
lavoro **era già fatto** (03-b16, 03-b14, 03-marca sono certificati), e una perché **la corsia A non
esiste più**.

| # | agente | corsia | quando parte | porta | perimetro dei file |
|---|---|---|---|---|---|
| **1** | ⛔ **il punto cieco del catalogo** | **K1** | ⛔⛔ **PER PRIMO, da solo** — dieci minuti, e sblocca il n. 5 | — | `01-b12-guasti.py` + registro |
| **3** | ⛔ **le tre code della corsia C** | **C** | subito | 7623 | `banchi/03-b17-*` |
| **4** | **il secondo motore** | **D** | subito | 7624 | `banchi/03-ff-*` (nuovi) |
| **5** | ⭐ **la codifica HEVC in hardware** | **B** | ⛔ **quando il n. 1 ha consegnato** | 7622 | `src/codificatore.*` · `figlio.c` · `Makefile` — ⛔ **solo nella COPIA** |
| **6** | ⭐⭐ **il refutatore del n. 5** | **B** | quando il n. 5 consegna | 7632 | copia **sua**; del n. 5 **legge**, non scrive |
| **7** | le marche che restano: `03-scena` · `03-deposita` · `03-b19` | **K2·K3** | dopo il n. 1 | 7625 | `03-scena*` · `03-deposita*` · `03-b19-*` |

⛔ **Cadute, e perché** — *non «rimandate»: fatte*:

| | |
|---|---|
| **n. 2** — il client HEVC (corsia A) | ⛔ **la domanda è chiusa**: HEVC in hardware **si dipinge**, `[M]` 5 su 5. Resta **una riga di cura** alla sonda, che fa il n. 1 |
| **n. 8** — `03-b16` + la copia ad albero | ✅ **03-b16 è CERTIFICATO** (13 agosto). La copia ad albero è stata costruita |
| **n. 9** — `03-b14` a tempo | ✅ **03-b14 è CERTIFICATO**. Resta solo `03-b19`, ed è passato al n. 7 |
| **n. 10** — propagazione + unione | ⚠ **rientra nel n. 1**: le schegge da unire sono **due**, non cinque, e l'unione costa meno del coordinamento |

**Al ricongiungimento**, senza aggiungere agenti:
- ⭐ **il n. 3 diventa la corsia E** — possiede già `03-b17-*`, quindi il *prima* e il *dopo* escono
  dalla stessa mano e **si sottraggono davvero**;
- ⭐ **il n. 1 fa K6**, le cinque certificazioni scadute per il `Makefile`.

### ⛔ Le due contese da arbitrare, e le arbitra il coordinatore

| | |
|---|---|
| ⛔⛔ **la finestra esclusiva** | il n. **7** (per `03-b19`, che misura un tempo) e la corsia **E** ⇒ **non possono girare insieme**, e nemmeno accanto a un vicino che cicla. `[M]` il 13 agosto due giri di griglia interi sono stati **buttati** proprio così. ⇒ **Una alla volta, e il banco verifica di essere solo** (§0-bis) |
| ⚠ **`/tmp` su CHUWI** | i n. **4** e **7** lanciano browser: tmpfs da 3,8 G, ⛔ **il 13 agosto sera al 98 %**, 100 M liberi. Ciascuno dichiara quanto gli serve e **libera a fine giro**, o il sintomo accuserà la pagina invece del disco |

⭐ **E il mandato di tutti e dieci è di REFUTARE, non di verificare** — e **ammette il rifiuto**: se
la cura che arriva dal coordinatore è sbagliata, si rifiuta **con un caso**. Il 13 agosto è successo
**sette volte su sette**, e avevano ragione loro tutte e sette.

---

## ⏱ PRIMA DI TUTTO — il coordinatore, dieci minuti, da solo

*Non è una corsia: è la precondizione di tutte.*

⭐ **FATTO alle 20:30-20:40 del 13 agosto.** Le righe restano perché l'esito è la scena da cui
partono le corsie, e ⛔ **due sono andate diversamente da come erano scritte**.

| | | esito |
|---|---|---|
| **P1** | **Lo stato, verificato e non ricordato**: albero pulito · `ss -ltn` ⛔ **su 192.168.0.2, non su CHUWI** (l'errore è già stato fatto) · `python3 banchi/01-b12-guasti.py --registro` | ✅ albero pulito; catalogo **24 banchi, 20 certificati, 4 mai provati** (`03-b17` · `03-b19` · `03-deposita` · `03-scena`) |
| **P2** | ⏳ **La scadenza**: `bash banchi/01-s1b-eccezione.sh oggi`, una volta al giorno **fino al 18 agosto** | ✅ fatto il 13 alle 09:03 — l'eccezione regge, **2,50 giorni su 7**, Chrome si è segnato **2026-08-17T21:09:47Z**. ⏳ Il prossimo è il **14** |
| **P3** | ⛔ **I commit di `banchi/`**, rimasti fuori dalla sessione del 13 (~46 voci) | ✅ **erano già dentro** (10caa3c, 769de61): l'albero è pulito. La riga era invecchiata di due commit |
| **P3-bis** | ⚠ **TRE PORTE LASCIATE ACCESE**, e non sono le protette: **7603** · **7605** · **7615**. ⛔ Lasciate **APPOSTA**, ispezionabili | ✅ **spente** con `03-b17-lancia.sh spegni` e `03-b15-lancia.sh spegni`. ⭐ Contate **prima e dopo**: sul server restano **solo** 7448 · 7501 · 7561 |
| **P4** | ⚠ **`/tmp` su CHUWI**: si libera `/tmp/google-chrome` e `/tmp/claude-*`; ⛔ **si guarda prima di cancellare il resto**: dentro ci sono le **prove** dei giri del 13 | ⛔ **NON fatto**: è al **98 %**, 100 M liberi. 1,3 G sono vecchi scratchpad di sessioni chiuse. ⚠ **Chi lancia browser lo guarda prima di credere a un errore che accusa la pagina** |

---

## ⛔ CORSIA A — **CANCELLATA la sera del 13 agosto**: non era un palco, era una BANDIERA

> ### ⛔⛔⛔ **LA CONCLUSIONE DEL 13 ERA FALSA, E QUESTA È LA TRAPPOLA PIÙ CARA DELLA GIORNATA**
>
> Era scritto: *«su Xvfb non c'è GPU affatto ⇒ non è un problema di codec, è un problema di
> PALCO»*, e su quella riga la corsia A diventava **la corsia da cui comincia la sessione**.
>
> ⛔ **È la BANDIERA `--disable-gpu` del banco stesso.** `03-b17-ritardo.py:626` la infila quando
> `self.gpu` è falso. `[M]` **A/B con UNA SOLA VARIABILE**, lo stesso script girato due volte:
>
> | Chrome su Xvfb | webgl visto dalla pagina | HEVC `isConfigSupported` |
> |---|---|---|
> | **senza** `--disable-gpu` | ⭐ `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
> | **con** `--disable-gpu` | `niente webgl` | no |
>
> ⭐ **E la GPU su Xvfb c'è**: è la iGPU di CHUWI, presa dal nodo DRM. `vainfo` su CHUWI dice
> `VAProfileHEVCMain10 : VAEntrypointVLD` — **la decodifica HEVC a 10 bit in hardware, sul client**.
>
> ⭐⭐ **E l'anomalia del piano è spiegata**: *«un giro ha detto HEVC true e non si è più
> riprodotto»* era il giro **senza la bandiera**. Non era un caso: era l'unico giro giusto.
>
> ⭐ **Quel che NON è successo, e va detto perché era il rischio grosso**: `03-b17-ritardo.py:582`
> ha **`gpu=True` di default** (`--senza-gpu` è opt-in) ⇒ ⛔ **l'anello dei 74,58 ms NON era
> misurato al buio**. Era **la sonda dei codec** a esserlo, non la misura.

> ### ⭐⭐⭐ E HEVC IN HARDWARE **SI DIPINGE DAVVERO** — non «dice di sì»: dipinge
>
> ⛔ `isConfigSupported` è una **dichiarazione**. Quindi il flusso uscito da `hevc_vaapi` sul server
> è stato **fatto suonare** al Chrome del banco, e i fotogrammi **contati**. `[M]` **5 giri su 5**,
> identici:
>
> | flusso | esito |
> |---|---|
> | ⭐ **HEVC Main10** (`hevc_vaapi`) | 1920×1080, **119 fotogrammi su 120**, `powerEfficient: true` |
> | VP9 profilo 2 10 bit (`vp9_vaapi`) | 1920×1080, 120 su 120, `powerEfficient: true` |
> | H.264 high (`h264_vaapi`) | 1920×1080, 120 su 120, `powerEfficient: true` |
>
> ⭐⭐⭐ **E IL PEZZO CHE MANCAVA È STATO CHIUSO LA SERA STESSA** — `banchi/03-palco-webcodecs.py`:
> **120 `VideoFrame` su 120 unità d'accesso, 5 giri su 5, su tutt'e due le strade di
> confezionamento** (Annex-B e `hvcC`). ⭐ E reso **refutabile invece che dimostrato**: due strade
> invece di una, perché è quel che separa *«Chrome non decodifica HEVC»* da *«non ho saputo
> chiedere»* — e ogni strada porta un controllo positivo che passa per **la stessa riga di codice**
> (`h264` Annex-B usa lo stesso spezzatore di HEVC, `h264` avcC lo stesso demuxer).
> **60 occasioni, 120/120 sui positivi.** Col `--disable-gpu`: HEVC **zero** 5 su 5, gli altri 120.
>
> ⛔ **E ha corretto il numero di due ore prima**: il *«119 su 120»* era **un artefatto del
> contenitore** (una *edit list* che salta 2,4 fotogrammi), non del codec. Il flusso ne ha **120**.
>
> ⚠ **La `[?]` che RESTA, e non è del decodificatore**: lì i chunk arrivano **già spezzati, da un
> file completo, su localhost**; nel prodotto arriveranno **dalla rete, a pezzi**, e a spezzare sarà
> il client. ⇒ Chiuso *«il decodificatore accetta e conta»*; **non** chiuso *«il nostro
> impacchettatore produce chunk che accetta»*. **È la prima cosa che tocca alla corsia B.**

**⇒ Quel che resta della corsia A è UNA RIGA DI CURA, e la fa il n. 1 insieme a K1:**

| | |
|---|---|
| **La cura** | la sonda dei codec **non deve girare con `--disable-gpu`**. E ⛔ **il banco deve DIRE con che palco ha risposto**: una sonda che risponde «no a HEVC» senza scrivere se aveva una GPU **ha lo stesso aspetto** di una che risponde bene |
| **Perimetro file** | `banchi/03-palco-*` (nuovi, per la sonda che resta come prova) |
| **Consegna a** | il coordinatore — ⛔ **e la GIUNZIONE 1 non esiste più**: B consegna direttamente a E |

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

> ### ⭐⭐ SECONDA MISURA, la sera del 13 — **a parità di bitrate, e coi fotogrammi CONTATI**
>
> ⛔ **Il primo giro di questa sonda NON era un confronto, e il banco si è accusato da sé**: VP9
> consegnava **129 221 byte** dove HEVC ne consegnava **3 893 620** — *trenta volte meno*. «Più
> veloce» a un trentesimo del bitrate **non è più veloce**. Rifatto **a 20 Mbit/s per tutti**, con
> `ffprobe` a contare i fotogrammi in uscita (un codificatore che ne butta 60 è veloce il doppio, e
> il cronometro da solo non se ne accorge). **3 giri:**
>
> | codificatore | ms/fotogramma | byte | fotogrammi in uscita |
> |---|---|---|---|
> | ⭐ **hevc_vaapi** | **3,16 – 3,24** | 5 356 148 | **120 su 120** |
> | h264_vaapi | 3,11 – 3,16 | 5 784 639 | 120 su 120 |
> | vp9_vaapi 10 bit | 6,95 – 7,28 | 4 927 115 | 120 su 120 |
> | ⛔ **av1_vaapi** | **non esiste** — uscita 218, *«No usable encoding profile found»* | — | — |
>
> ⭐ **Il controllo tiene**: `hevc_vaapi` senza vincolo di bitrate dà **2,92 ms** contro i **2,85**
> del 13 ⇒ questa sonda e quella della notte **parlano la stessa lingua**, e i numeri si leggono
> sulla stessa scala.
>
> ⛔⛔ **E la riga che cambia il bersaglio per sempre: la codifica AV1 in HARDWARE NON ESISTE.**
> Né su `renderD128` né su `renderD129` — `vainfo` dà `VAProfileAV1Profile0 : VAEntrypointVLD`,
> cioè **solo decodifica**. ⚠ `av1_vaapi` **compare** nell'elenco di `ffmpeg`: chi si fidasse
> dell'elenco invece che di un giro butterebbe una consegna. ⇒ **Restare su AV1 vuol dire restare in
> software per sempre**, su questa macchina.
>
> ⇒ ⭐ **HEVC è il bersaglio giusto, e adesso per una ragione MISURATA ai due capi**: il più veloce
> in codifica **e** l'unico che il client dipinge in hardware. **VP9 non serve** — era la strada di
> ripiego, è più lento, e avrebbe voluto un numero di codec nuovo nel protocollo (`RCP.md:1404` dà
> `1` = HEVC, `2` = AV1, e basta).
>
> ⚠ **Una cosa che NON si può leggere da questi numeri**: il `libsvtav1` di questa sonda fa **9,9
> ms**, non 22,23 — perché **la scena è diversa** (contenuto sintetico, e i byte lo dicono: 2,8 M
> contro 5,5 M). ⭐ I codificatori in hardware sono quasi indifferenti al contenuto (2,92 contro
> 2,85), quelli **software no**. ⇒ ⛔ **Il rapporto software/hardware va preso da un giro sulla
> STESSA scena** — ed è esattamente quel che fa la corsia E.
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
| **B0** | ⛔⛔ **IL PRIMO CONTROLLO, prima di scrivere un carattere** | la decodifica HEVC via **WebCodecs `VideoDecoder`** — non `<video>` — con un flusso vero di `hevc_vaapi`. ⭐ Oggi c'è la dichiarazione e c'è la decodifica via `<video>`, `[M]` 5 su 5; **manca la strada che il prodotto usa davvero**. ⚠ Se cadesse, cade **prima** del lavoro grosso, non dopo |
| **B7** | ⚠ **la negoziazione dice già HEVC** | `RCP.md:699` elenca `hevc, av1` e `:1404` dà `codec 1 = HEVC`. ⇒ **il protocollo non va toccato**: va tolto il motivo per cui il prodotto sceglie `2` |

| | |
|---|---|
| **Perimetro file** | `src/codificatore.c` · `src/codificatore.h` · `src/figlio.c` · `src/Makefile` — ⛔ **e SOLO nella copia sul server**. ⚠ Nessun `.md`, nessun banco |
| **Porta / palco** | **7622**, copia del prodotto sul server, ban+socket+registro propri |
| **Dipende da** | **K1** (il punto cieco del catalogo) — vedi corsia K, ed è una cosa da dieci minuti |
| **Consegna a** | ⭐ **direttamente a E** — ⛔ la giunzione 1 non esiste più, la corsia A è caduta |

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
| **Consegna a** | il coordinatore. ⚠ Se ci arriva **prima che E chiuda**, i suoi numeri entrano nel giudizio; se no, resta `[?]` **dichiarata**, forma d'errore **E10** — che è già la posizione onesta di oggi |
| ⭐ **E una cosa in più, gratis** | la sonda del palco scritta la sera del 13 (`isConfigSupported` + decodifica vera, esiti **rimandati dalla pagina**, niente CDP) **funziona già su tutt'e due i motori**: la corsia D non ha bisogno di un attrezzo diverso, solo di puntarla ai numeri invece che ai sì/no |

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

⛔ **RIVISTO alle 20:40 del 13 col catalogo davanti** — `python3 banchi/01-b12-guasti.py --registro`:
**24 banchi, 20 CERTIFICATI, 4 mai provati** (`03-b17` · `03-b19` · `03-deposita` · `03-scena`).
⇒ **K4 e metà di K2 erano già fatte**, e il piano non lo sapeva perché è stato scritto **prima**
degli ultimi due commit della giornata.

| # | quando | | |
|---|---|---|---|
| **K1** | ⛔ **PER PRIMO, e blocca la corsia B** | **IL PUNTO CIECO** | ⭐ **VERIFICATO, e va detto più preciso di com'era scritto**: `src/codificatore.c` non compare in **nessuna** lista di `FILE_CHE_CONTANO` — vero. ⛔ Ma *«e nemmeno `figlio.c`»* **è smentito**: `figlio.c` c'è, nella lista di `03-b17` (riga 352). ⚠ Solo che **`03-b17` è uno dei quattro MAI PROVATI** ⇒ la rete c'è **sulla carta e non nei fatti**. La cura resta la stessa; la frase no. ⭐ **Costa due righe, e va fatto prima che B scriva un carattere** |
| **K2** | mentre B-C-D girano | **le marche dei banchi che RESTANO** | ⭐ **03-b14, 03-b16, 03-b15, 03-b18 e 03-marca sono CERTIFICATI** (13 agosto sera). ⛔ Restano **`03-scena`, `03-deposita`, `03-b19`** — e `03-b17`, che però è della corsia C. Il campo `marca` resta **vuoto di proposito**: *una marca si **misura**, e una dedotta dal sorgente è la forma d'errore già pagata su B4 e B7* |
| **K3** | insieme a K2 | **`03-deposita` non è certificabile** | e non per la marca: **nessuno rilegge `03-scena-esiti.jsonl`**, quindi un guasto lascerebbe il giro verde. Il controllo mancante **costa due righe** |
| ~~**K4**~~ | ✅ **FATTA** | ~~`03-b16` vuole una copia ad ALBERO~~ | **03-b16 è certificato**: la copia ad albero è stata costruita |
| **K5** | insieme a K2 | ⚠ **propagazione su NIC-OS** | là il conto era **11/15** perché tre file di *banco* erano vecchi. Non tocca la validità — quei giri sono partiti da CHUWI — ma va allineato, e ⚠ **il denominatore adesso è 24** |
| **K6** | ⛔ **DOPO che B ha consegnato** (la giunzione 1 non esiste più) | **le certificazioni che scadono** | ⭐ **CONTROLLATO nel sorgente**: sono **cinque**, e sono esattamente quelle che portano `FILE_DEL_BINARIO = ["remotix/main.c", "remotix/Makefile"]` (riga 269) — **B10 · B13 · P1 · P5 · P5R**. ⛔ **Nessuna per colpa del codificatore**: scadono perché guardano il **`Makefile`**, che cambia per legare VA-API. ⚠ Il piano diceva «cinque su **quindici**»: sono **cinque su ventiquattro**. ✅ **Reggono**: B3·B5·B6·B7·B8 (`rcp/rcp.c`) · B9 (`RCP.md`) · B2·B4·B11·C2 · 03-b14·03-b15·03-b16·03-b18·03-marca (banchi propri) |
| **K7** | insieme a K6 | ⚠ **`03-b15-lancia.sh`** | usa ancora la porta 7603 e l'ordine vecchio **scena → misura**, che dà **zero fotogrammi** |
| **K8** | ⭐ **insieme a K1** | ⛔ **la sonda che ha mentito** | `03-b17` porta `figlio.c` a catalogo ma **non è mai stato provato**, e la sonda dei codec del 13 girava con `--disable-gpu` **senza dirlo**. ⇒ **Un banco che risponde «no» deve scrivere CON CHE PALCO ha risposto**, o la risposta e la cecità hanno lo stesso aspetto |

| | |
|---|---|
| **Perimetro file** | `banchi/01-b12-guasti.py` · `banchi/01-b12-registro.jsonl` · `banchi/03-scena*` · `banchi/03-marca*` · `banchi/03-deposita*` · `banchi/03-b14-*` · `banchi/03-b16-*` · `banchi/03-b19-*` · `banchi/03-b15-lancia.sh` |
| **Porte / palco** | ⭐ **7625-7639**, una per certificatore, **copia propria** ciascuno |
| **Registro** | ⭐ ciascuno scrive la **propria scheggia** `01-b12-registro-<corsia>.jsonl`; ⛔ **l'unione è l'unico passo in serie**, e **rifiuta** i conflitti invece di sceglierli |
| **⛔ I due vincoli d'ordine** | ⛔ **K1 PRIMA che B tocchi `codificatore.c`** — oggi **nessuna certificazione guarda quel file**, quindi finché K1 non è fatto la corsia B lavora **senza rete**. ⛔ **K6 SOLO DOPO** che il prodotto ha smesso di cambiare — rigirare le certificazioni mentre `src/` si muove le fa scadere **una seconda volta**, ed è l'errore che il 13 agosto è nato per non ripetere. ⭐ **Fra i due, tutto a ventaglio** |
| ⚠ **E K2 è dell'ALTRA famiglia** | le **marche** dei banchi nuovi si misurano con `sano → guasto → risanato`: ⭐ è **correttezza**, non tempo ⇒ va a ventaglio anche lei. ⛔ **Tranne per i banchi che misurano un TEMPO** — `03-b14` (la cadenza) e `03-b19` (i dipinti): la loro marca si prende **dentro una finestra esclusiva**, o si misura la contesa e la marca è finta |

---

## ⛔ GIUNZIONE 1 — **SCIOLTA la sera del 13 agosto**

Era *«non prima che A e B siano tutt'e due arrivate: con la sola B si misura mezzo anello»*.
⭐ **La metà che mancava c'è già**: il client dipinge HEVC in hardware, `[M]` 5 giri su 5.
⇒ **B consegna direttamente a E**, e la strada critica perde il ramo che poteva bloccarla.

---

## 🅔 CORSIA E — L'anello rimisurato, ed è il numero su cui la fase si chiude

**Parte quando B ha consegnato** — ⛔ la giunzione 1 è sciolta, non c'è più niente da aspettare.

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
| **Dipende da** | ⛔ **B soltanto** (la giunzione 1 è sciolta) · ⚠ **C** (se C dice che i 74,58 sono `[?]`, il «prima» va rifatto **anche lui**, o la sottrazione non vale) |
| ⛔ **E una cosa da non sbagliare** | il «prima» e il «dopo» devono avere **lo stesso palco**: se il giro nuovo gira **con** la GPU e quello vecchio **senza**, la differenza non è il codificatore. ⭐ `03-b17-ritardo.py` ha `gpu=True` di default in tutt'e due, **ma va DICHIARATO accanto al numero**, non creduto |

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

## 🚧 LE TRAPPOLE GIÀ PAGATE — il catalogo completo, e si legge PRIMA di partire

*⭐ Raccolte su richiesta dell'utente alla chiusura del 13 agosto 2026, da **tutti e dodici** i
gruppi di lavoro della giornata. ⛔ **Ciascuna è costata dei giri buttati, e il costo è scritto
accanto.** Sono qui perché non li costino di nuovo.*

⛔ **Ogni corsia le legge prima di lanciare il primo giro.** Non è cerimonia: **sette di queste sono
state pagate DUE VOLTE nella stessa giornata**, da gruppi diversi, perché il secondo non sapeva del
primo.

---

### 1. ⛔⛔ IL PALCO — la famiglia più cara della giornata

*Tutte hanno lo stesso sintomo: **la catena funziona perfettamente e il numero è zero, o falso**.*

| | costo |
|---|---|
| ⛔⛔ **la scena deve stare sul MONITOR CHE SI STA CATTURANDO** — il palco ha **quattro** monitor virtuali (`Meta-0…3`, tutti 1920×1080@60), e il proprio si legge **dal registro del proprio server**, non si indovina. Una scena sul monitor sbagliato dà **zero fotogrammi per dieci secondi con la catena perfetta** | **quattro giri**, due gruppi |
| ⛔⛔ **e la stessa trappola è tornata a mordere il RISULTATO che la citava**: due file di esiti su tre portavano `scena_sul_mio_monitor: **false**` — scritto **dal banco stesso, accanto al numero** — e nessuno l'ha guardato. ⇒ La «legge della griglia su 13 punti» e il «riscontro incrociato entro il 4 %» **non esistevano** | **13 correzioni in 10 documenti** |
| ⛔ **la scena accesa PRIMA della sessione resta viva e NON disegna** — Mutter non manda i *frame callback* a una superficie su un monitor che nessuno registra. Si accende **a sessione aperta** | due gruppi |
| ⛔ **la scena smette di disegnare quando nessuno registra più il suo monitor, e non riparte da sola** — va riaccesa prima di ogni misura | un caso perso |
| ⛔ **la finestra a schermo intero viene SPOSTATA VIA dal monitor quando il palco cambia** — e un monitor fermo non consegna niente, senza un errore | un giro |
| ⛔ **una guardia sul palco che confronta solo i DUE ESTREMI della finestra di misura non vede un monitor d'altri smontato e rimontato in mezzo** ⇒ **due punti sono entrati in tabella come se fossero misure**. Si legge `mutter.log` **dentro** la finestra | due punti falsi |

### 2. ⛔⛔ LA CONTESA — chi misura un tempo e non è solo, misura la contesa

| | costo |
|---|---|
| ⛔⛔ **due giri di griglia interi buttati** perché **il prodotto dell'utente stava ciclando** accanto | **due giri** |
| ⛔ **CHUWI ha 4 core**: durante un giro dell'anello un altro banco girava al **74 % di CPU** con `load` 3,8 ⇒ i tratti della **decodifica** e del **disegno** ne risentono, e il numero non lo dice | contaminazione dichiarata |
| ⇒ ⭐ **la cura è §0-bis**: chi misura un tempo **verifica di essere solo e lo scrive accanto al numero**, e **se non è solo RIFIUTA di misurare** | — |

### 3. ⛔ I BANCHI CHE SI AUTOINGANNANO — e sono i più insidiosi, perché escono verdi

| | |
|---|---|
| ⛔⛔ **una certificazione VERDE che provava il giudice nell'UNITÀ SBAGLIATA** — le celle si campionano 0-255 e il giudice le voleva 0-1: passava nell'unità del **lettore** invece che in quella dell'**acquisizione** |
| ⛔ **un caso verde perché lo produceva lo STRUMENTO**: `Page.captureScreenshot` — chiamata da un'opzione di **stampa** (`--copia`) — svegliava il rendering. Senza, lo stesso banco su prodotto **sano** dava **5 pretese rosse** |
| ⛔ **quattro pretese MAI innestate con nessun guasto**: verdi da sempre, e nessuno sapeva se sapessero fare altro |
| ⛔ **un rilevatore CIECO PER COSTRUZIONE**: il prodotto scarta i fuori ordine **prima** del decodificatore, il banco guarda solo **dopo** ⇒ «0 fuori ordine» è **un'identità algebrica, non una misura** |
| ⛔ **una funzione di arricchimento NON IDEMPOTENTE**: la seconda passata consumava le celle e **cancellava 264 letture buone** ⇒ «zero campioni» con la catena perfetta |
| ⛔ **un controllo dell'orologio che confrontava un numero CON SÉ STESSO** |
| ⛔ **un contatore letto su fette intrecciate** dava 6,5 fotogrammi/s di una catena che ne consegnava 23 |
| ⛔ **un banco che leggeva il registro INTERO** invece che dalla propria riga di partenza ⇒ il controllo *negativo* leggeva le righe del giro precedente e arrossiva su un prodotto sano |
| ⛔ **un `w` invece di un `>>` sugli esiti**: i tre giri sparivano uno alla volta. *Trovato guardando il file, non il codice* |
| ⛔ **tre FALSI ROSSI** che accusavano il prodotto mentre faceva la cosa giusta: cercavano una riga di registro che **un prodotto che si comporta bene non scrive mai** |
| ⛔ **un banco che pretendeva ZERO BUCHI** nella successione dei `numero`, mentre l'arbitro dice che **un buco è normale e significa qualcosa** |
| ⛔ **`giri_verdi: 6` gonfiato — erano 3**, e uno dei giri contati aveva rosso proprio il controllo che valida il numero usato |
| ⛔ **numeri FOSSILI incollati nei commenti** («0 su 783») mentre il giro vero ne aveva 804 |
| ⛔ **una voce di catalogo che diceva «1 guaio» dove i guai erano 3**: la certificazione sarebbe caduta **per una virgola** |
| ⛔⛔⛔ **una sonda che ha spento da sé quel che stava cercando**: chiedeva a Chrome se sapesse decodificare HEVC, e lo lanciava con **`--disable-gpu`**. Cinque «no» su cinque, e il «sì» che ogni tanto usciva è stato archiviato come *anomalia non riproducibile*. ⇒ **Ne è nata una corsia intera del piano** — «dare al banco un palco con una GPU vera» — su una conclusione **falsa**. ⭐ La cura non è tecnica: **un banco che risponde «no» deve scrivere CON CHE PALCO ha risposto**, o «non c'è» e «non ho potuto guardare» hanno lo stesso aspetto |
| ⛔⛔ **un confronto fra codificatori che NON era un confronto**: VP9 sembrava concorrenziale, e consegnava **trenta volte meno byte** di HEVC. «Più veloce» a un trentesimo del bitrate non è più veloce. ⇒ **Si fissa il bitrate a tutti, e i fotogrammi in uscita si CONTANO** — uno che ne butta 60 è veloce il doppio, e il cronometro da solo non se ne accorge |
| ⛔ **un elenco di `ffmpeg` creduto invece che girato**: `av1_vaapi` **compare** fra i codificatori, e all'uso esce **218** — *«No usable encoding profile found»*, perché l'hardware l'entrypoint non ce l'ha. ⇒ **Un elenco dice che il codice c'è, non che la macchina lo sa fare** |

### 4. ⛔ I CODICI D'USCITA — il rosso che non esce dal programma

| | |
|---|---|
| ⛔⛔ **tre banchi che escono SEMPRE 0**: `ko()` **stampa e basta**, e il `return` finale è incondizionato ⇒ col guasto dentro il rosso resta **nella prosa** e chi legge a macchina vede verde. Due curati, ⛔ **il terzo è ancora lì** (`03-b19-ritardo-worker.py`, percorso `--verdetto`) |
| ⛔ **`RuntimeError` fa uscire Python con 1 — lo STESSO codice di un caso rosso**: un `Xvfb` rimasto da un giro ucciso ha prodotto **«uscita 1 con zero righe rosse»**. ⭐ È il campo `marca` che l'avrebbe fermato |

### 5. ⛔ L'AMBIENTE — quel che manca, e non è dove lo cerchi

| | |
|---|---|
| ⛔ **su CHUWI il prodotto NON si compila**: manca `nghttp3/nghttp3.h`. Vive in un contenitore su **192.168.0.2** (`enter.sh`, sorgenti `/srv/src/remotix`); i **browser veri** stanno su CHUWI |
| ⭐ **la parola d'ordine di `sudo` sta in `~/SERVER.ssh`** (`banchi/02-pam-lancia.sh:59`) — ⛔ **un gruppo si è fermato per un'intera consegna per non saperlo** |
| ⛔ **`weston-simple-egl` NON esiste** su nessuna delle due macchine, e tre documenti lo prescrivevano come scena. È stato scritto da zero |
| ⛔ **`numpy` non c'è su NIC-OS** — chi legge i pixel lo fa **da CHUWI** |
| ⛔ **`bc` non c'è sul server**, e `y4m` non accetta il 10 bit ⇒ due giri persi in cronometri a zero |
| ⛔ **Firefox non apre finestre su Xvfb `:81`** (0 finestre in 90 s) e **non ha CDP** ⇒ si prova `--headless` **facendo rimandare gli esiti alla pagina stessa** |
| ⛔⛔⛔ **~~su Xvfb non c'è GPU AFFATTO~~ — SMENTITA la sera del 13, ed è la riga più cara della giornata**: la GPU su Xvfb **c'è** (`ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))`). A spegnerla era ⛔ **la bandiera `--disable-gpu` del banco stesso** (`03-b17-ritardo.py:626`). `[M]` A/B con una sola variabile: senza bandiera → webgl **e HEVC true**; con bandiera → *«niente webgl»* e HEVC no. ⚠ **La riga su `requestAnimationFrame` (0 quadri in 3 s) va rimisurata**: era presa sullo stesso palco cieco |
| ⚠ **`/tmp` su CHUWI è una tmpfs da 3,8 G, il 13 agosto al 94 %**: quando si riempie Chrome non apre il profilo e il banco fallisce con un errore che **accusa la pagina**. ⛔ Si guarda il disco **prima** di credergli — ed è **già successo** |

### 6. ⛔ GLI ATTREZZI — che mentono in silenzio

| | |
|---|---|
| ⛔ **`curl` NORMALIZZA**: non manda il frammento e si mangia il `?` vuoto ⇒ due prove erano **verdi per costruzione**. Sul filo grezzo serve `--request-target` |
| ⛔ **`&` dentro `ssh → enter.sh → bash -c`** non arriva dove sembra: **si usa un file, non una riga annidata**. ⚠ E un `grep` annidato allo stesso modo **contava zero** su un registro che la riga ce l'aveva |
| ⛔ **modificare uno script `bash` MENTRE GIRA** butta il giro: bash rilegge il file **a offset** |
| ⛔ **`Page.addScriptToEvaluateOnNewDocument` NON entra nei worker** ⇒ un banco non adattato conta **zero richiami** su una catena viva, e si legge come «non arriva niente» |
| ⛔ **la presa CDP diretta al bersaglio `worker` accetta la connessione e poi NON RISPONDE** (`Runtime.enable` scade a 15 s) — *una presa che si apre e tace è peggio di una che rifiuta: sembra agganciata*. Serve `Target.setAutoAttach(flatten)` |
| ⛔ **`scp` risponde «Failure» se il binario è IN USO** da un altro banco |
| ⛔ **`set -u` è un amico**: due variabili non definite hanno fatto uscire due controlli rossi con «NON MISURATI» — ⭐ **senza, la scena sarebbe partita sul display sbagliato in silenzio** |
| ⛔ **un'ancora testuale che compare DUE VOLTE** nel file ferma l'innesto del guasto: l'ancora va di due righe |

### 7. ⛔ IL PRODOTTO E IL DEPOSITO — quel che blocca tutti

| | |
|---|---|
| ⛔⛔ **`src/rcp.c` e `banchi/rcp/rcp.c` sono GEMELLI**: il `Makefile` pretende che siano identici, e se divergono **NESSUNO compila** — e non si vede finché non ci si sbatte contro. È successo, e ha bloccato due gruppi |
| ⛔ **il prodotto legge `pagina.html` UNA VOLTA SOLA all'accensione**: dopo ogni modifica **si riaccende**, o si prova la pagina di prima |
| ⛔ **`src/pagina.c` rispondeva 404 a QUALUNQUE stringa di ricerca** (curato oggi): `/?x=1` → 404. ⇒ Ogni interruttore `?…` era **irraggiungibile**, e i banchi non se n'erano accorti perché servono la pagina da un `http.server` di Python, **che il `?` lo ignora** |
| ⛔ **il codec in uso è AV1 (SVT-AV1), non x265**: una manopola preparata per x265 **non avrebbe toccato niente** — *chi l'aveva scritta l'ha rifiutata da sé prima di consegnarla* |
| ⚠ **il binario «risanato» non torna identico a quello «sano»** pur coi sorgenti uguali: la costruzione **non è riproducibile bit per bit** |
| ⚠ **le porte protette**: **7448** · **7501** · ⛔ **7561, quella che l'utente apre** — si leggono e **non si toccano**. E ⛔ **si contano PRIMA e DOPO ogni passo**, che è quel che ha permesso di dire «non le ho toccate» invece di crederlo |
| ⚠ **`ss` va girato sulla macchina GIUSTA**: un controllo delle porte fatto su CHUWI ha concluso che i tre server dell'utente erano spenti — **ascoltano su NIC-OS** |

### 8. ⚠ IL COORDINAMENTO — quel che si rompe fra i gruppi

| | |
|---|---|
| ⛔ **il registro rifiuta due giudizi caduti nello STESSO SECONDO** — ed è giusto così: li ha visti come conflitto e **l'ha detto**, invece di sceglierne uno |
| ⚠ **una macchina ai byte di ieri**: NIC-OS andava riallineata prima di certificare |
| ⚠ **un binario stantio che non esisteva più**: va riseminato **verificandone l'impronta** |
| ⛔ **un agente ha toccato un file fuori dal proprio perimetro senza avvisare** — il codice era giusto, la regola no. ⇒ **Il perimetro si dichiara per file, non per cartella** |
| ⚠ **due agenti sono morti a 140 byte senza fare niente**: recuperati con un secondo giro |

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
