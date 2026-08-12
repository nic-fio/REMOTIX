# P2.4 — Il PRODOTTO del filo: il canale video, dentro `rcp.c`

*Il quarto anello della fase 2, scritto il **12 agosto 2026** dopo il banco (`F2-4-filo.md`).*
*Porta usata: **7514**. Il banco lo avevano scritto prima, e ⛔ **gli arbitri non li ho toccati**.*

---

## In una riga

Il canale video vive in **`src/rcp.c` + `src/rcp.h`** (⛔ **nessun `video.c`**, e ⭐ **zero righe di
`Makefile`**), rispetta **11 regole su 11** verificate dall'arbitro indipendente, ⭐ **il cliente di
prova ha girato per la prima volta** — arriva a `SESSIONE` e riporta **zero fotogrammi, uscita 5**,
perché la cucitura che apre lo stream sta in `webtransport.c`, che non è mio — e ⛔ **tre regole di
`RCP.md` non hanno retto applicandole**, una delle quali trovata dal primo giro dal vivo.

---

## 1. Dove vive il canale video, e perché lì

⛔ **In `src/rcp.c`, non in un `src/video.c`.** Il mandato lasciava le due strade; ho preso la prima,
e la ragione non è di gusto:

| delle undici regole… | parla di… |
|---|---|
| P1 — «nessuno stream prima di aver **spedito `SESSIONE`**» | lo **stato della sessione** |
| P5 — «`largh.`/`altezza` valgono la **tela in vigore**» | `SESSIONE` (§4.5) **o** l'ultimo `TELA` (§7.1) |
| `codec` «DEVE essere quello **negoziato**» | la negoziazione di §4.3, cioè il `CIAO` |
| P6 — «il **primo dopo `SESSIONE`** DEVE essere una chiave» | di nuovo `SESSIONE` |
| P9 — «e lo stesso a ogni **cambio di tela**» | di nuovo §7.1 |
| §5.2 — `RICHIEDI_CHIAVE`, e i 200 ms | un messaggio del **canale di controllo** |

⇒ **Sei regole su undici non parlano dei 28 byte: parlano dello stato che `rcp.c` già tiene.** Un
`video.c` a parte avrebbe dovuto **ricopiarsi** quello stato, e due copie di uno stato divergono —
è la ragione per cui `RCP.md` §0 esiste, applicata dentro un programma solo.

⭐ **E ha un secondo effetto, che si vede nel `Makefile`: zero righe da aggiungere.** `rcp.c` è già
fra i `SORGENTI` ed è già fra i `GEMELLATI`, quindi il canale video nasce **già confrontato byte per
byte con `banchi/rcp/rcp.c`** a ogni costruzione (rilievo R12.3). Un `video.c` sarebbe nato fuori da
quella guardia, e nessuno se ne sarebbe accorto.

| file | righe | `[M]` 12 ago 2026 |
|---|---|---|
| `src/rcp.c` | 2.764 → **3.369** (+613) | `md5 df4c5fc5…` |
| `src/rcp.h` | 239 → **415** (+176) | `md5 230221f7…` |
| `banchi/rcp/rcp.c`, `rcp.h` | **identici byte per byte** (`cmp`, verificato) | |
| `banchi/02-filo-prodotto.c` | **461** — nuovo: l'ospite finto che raccoglie i byte |
| `banchi/02-filo-prodotto.py` | **603** — nuovo: dà quei byte all'arbitro |
| `banchi/02-filo-cliente.py` | 554 → **708** — ⛔ **curato dal primo giro dal vivo**, vedi §4 |

### La forma che rende tre regole impossibili da violare, invece che facili da rispettare

⛔ **`largh.`, `altezza`, `codec` e `numero` non sono parametri di nessuna funzione pubblica.** Chi
codifica passa solo `chiave`, `lunghezza`, `istante_us`, `input`, `ora_ms`; gli altri quattro campi
li mette il modulo, dalla tela in vigore, dalla negoziazione di §4.3 e dal proprio contatore.

⚠ La strada alternativa — passarli e controllarli — era più corta e metteva la protezione dove si
può perdere. È l'invariante **I7** letta da dentro il programma.

---

## 2. Le undici regole: **11 su 11**, e come lo si verifica

Le undici sono quelle che `02-filo-fotogramma.py --elenco` conta: **P1, P2, P3, P4, P5, P6, P8, P9,
P11, P13, P14**.

| # | la regola, dal lato di chi MANDA | dove sta, nel codice |
|---|---|---|
| **P1** | nessuno stream video prima di aver **spedito** `SESSIONE` | `s->sessione_spedita`, accesa **dentro** l'`if (!w.pieno)` che spedisce `SESSIONE` |
| **P2** | `numero` parte da **1**, lo 0 è riservato, e **al giro si salta** | `numero_prossimo()`, e le due righe stanno una sotto l'altra apposta |
| **P3** | il video **solo** su uno stream unidirezionale del server | il gancio `video_apri`; ⛔ da lì in giù `s->g.manda` (il controllo) **non compare** |
| **P4** | FIN prima dei 28 byte è `ERRORE_PROTOCOLLO` | i 28 byte escono in **una** scrittura, e se non escono si **AZZERA** |
| **P5** | `largh.`/`altezza` = tela **in vigore** | `s->tela_l/tela_a`, posti da `SESSIONE` e da `rcp_tela_adattata()` |
| **P6** | il primo dopo `SESSIONE` **DEVE** essere una chiave | `s->serve_chiave`, acceso alla riga di `SESSIONE` |
| **P9** | e lo stesso a **ogni cambio di tela** | `rcp_tela_adattata()` — ⛔ e **solo se la misura cambia davvero** |
| **P8/P11/P13/P14** | la tolleranza sui fotogrammi in volo | ⚠ sono regole **del client**: dal lato server sono onorate *per costruzione*, perché la misura viene sempre dalla tela in vigore |
| §6.2 | il tetto di **16 MiB** vincola **prima** chi spedisce | il controllo sta **prima di aprire lo stream**: su un fotogramma troppo grande non parte un byte |
| §6.2 | **FIN ⇒ completo · RESET ⇒ si butta** | `rcp_video_finisci()` FA il FIN solo se i byte dichiarati sono usciti tutti; altrimenti azzera |
| §5.1/§5.2 | ogni abbandono **nel registro**, e una **chiave non si abbandona** | `rcp_video_abbandona()` rifiuta sulle chiavi e scrive sempre |

### ⛔ Come si verifica — e non è «ho riletto il codice»

⭐ **`banchi/02-filo-prodotto.c` + `banchi/02-filo-prodotto.py`, 17 scene.** L'ospite finto monta il
canale video di `banchi/rcp/rcp.c`, gli fa spedire un fotogramma per scena e **scrive i byte che
sono usciti** in JSON; il driver Python li dà a **`02-filo-fotogramma.py`**, cioè all'arbitro dei 48
casi, e confronta con la previsione scritta **prima** del giro.

⛔ **E il divieto è rispettato nel verso che conta**: il prodotto è in C, l'arbitro in Python, in un
altro processo, e i byte passano da un JSON. Il server **non importa il giudice** e non lo può
importare. È il banco a importarlo, che è quel che un banco deve fare.

```
python3 banchi/02-filo-prodotto.py             ⭐ 17 scene su 17 passano   [M]
python3 banchi/02-filo-prodotto.py --certifica ⭐ 6 guasti su 6: sano 0 → >0 → 0
bash     banchi/02-filo-lancia.sh              ⭐ 6 pezzi su 6 (gli arbitri, intatti)
```

⛔ **La certificazione risponde alla domanda di `REVIEWER.md` §1** — *«saprebbe accorgersi che non
funziona?»* — e i guasti si innestano **sui byte**, non sull'imputato: si finge un prodotto che ha
messo sul filo byte diversi, che è esattamente il modo in cui questo banco lo scoprirebbe.

| | il guasto | l'arbitro dice `[M]` |
|---|---|---|
| **GP1** | il primo fotogramma è un delta | `chiave-dopo-sessione: ACCETTATO → ERRORE_PROTOCOLLO` |
| **GP2** | `numero = 0` | idem, e la riga cita §6.2 e §7.1 |
| **GP3** | la misura resta quella di `SESSIONE` dopo un `TELA` — *§6.2 com'era per due ore* | `chiave-alla-misura-nuova: ACCETTATO → ERRORE_PROTOCOLLO` |
| **GP4** | uno stream azzerato chiuso con **FIN** — la forma **E8**, rilievo R1.7 | `abbandono-di-un-delta: SCARTATO → ACCETTATO` |
| **GP5** | un byte oltre il tetto | `16-mib-esatti: ACCETTATO → ERRORE_PROTOCOLLO` |
| **GP6** | `codec = 2` su una sessione che ha negoziato HEVC | `chiave-dopo-sessione: ACCETTATO → ERRORE_PROTOCOLLO` |

⛔ **E la marca ha due metà** (R12-A.3): è `scena: atteso -> visto`, e a giro sano i due coincidono
sempre — quindi `X: A -> B` con `A ≠ B` **esiste soltanto** quando qualcosa è rotto. Verificate
tutt'e due le metà su tutti e sei.

### ⚠ Due cose che questo banco **non** dice, e vanno dette

- ⛔ **la metà di P9 che sta nei dati**: §5.2 vuole una chiave **vera**, coi VPS/SPS/PPS davanti
  all'IDR. `rcp.c` **non guarda dentro i byte del codec** e non deve: farlo vorrebbe dire mettere
  HEVC e AV1 dentro il modulo del protocollo. ⇒ **È un obbligo che passo a F2.3**, ed è scritto nel
  codice per non farlo credere coperto;
- ⛔ **due regole si vedono solo in punti che l'interfaccia pubblica non raggiunge**, e per quelle
  il banco `#include` il sorgente invece di collegarlo: il **giro del contatore** (per provarlo sul
  filo bisogna portare `numero` a `0xFFFFFFFF`, e a 60 al secondo ci vogliono due anni e due mesi) e
  la **rottura a metà dell'intestazione**. Dichiarato nel file, col suo prezzo: qui si prova *lo
  stesso sorgente*, non *lo stesso binario*.

---

## 3. Quel che ho servito e quel che ho lasciato fuori

- ⭐ **`RICHIEDI_CHIAVE` (`0x000D`) adesso è servito**, e non è un extra: §5.2 **obbliga** il client a
  mandarlo appena vede un buco, e finora quel tipo cadeva nel `default` e **faceva perdere la
  sessione a un client conforme**. Il prezzo era dichiarato nel registro (*«la fase 1 non lo serve
  ancora»*), ma col video non si può più pagare. Insieme arriva l'eccezione 5 di §3 — 200 ms
  dall'ultima **chiave spedita**, non dall'ultima richiesta — ⛔ **e la tolleranza si scrive nel
  registro**, che §3 pretende;
- ⛔ **`ADATTA_TELA` (`0x000B`) NON è servito**, e resta il congedo di prima: rispondere `TELA`
  richiede un compositore che sappia ridimensionare, ed è l'anello di F2.1, non il mio. ⇒ ⚠ **Finché
  resta così, P5/P8/P9/P11/P13 non si possono esercitare sul filo**: il codice le rispetta e
  `rcp_tela_adattata()` è il punto in cui chi risponderà `TELA` deve chiamare, ma **nessun giro dal
  vivo le tocca**. Va detto invece di lasciarlo dedurre;
- `rcp_libera()` azzera uno stream video lasciato aperto: un fotogramma aperto quando la sessione
  finisce è per definizione incompleto, e azzerarlo è l'unica chiusura che significa «buttalo».

---

## 4. ⭐⭐ Il primo giro del cliente di prova — **la prima misura vera di questo anello**

*Scena dichiarata: server costruito dai sorgenti di adesso in un albero **suo**
(`/srv/src/f24`), acceso sulla **7514** con ban-file, socket e certificati **propri** — ⛔ 7448 e
7501 non toccate. Cliente `02-filo-cliente.py` dentro il contenitore, `aioquic` 1.2.0.*

### ⛔ Il primo giro è stato ROSSO, e la colpa era del banco

```
[wt]   sessione chiusa dal server, codice 0x0d = TEMPO_SCADUTO
⛔ TimeoutError                                        USCITA=2
```

Registro del server, alla stessa ora:

> *«sessione WebTransport aperta e canale di controllo **MAI aperto** entro 5000 ms — congedo 0x0d
> TEMPO_SCADUTO (§4.6)»*

⭐ **Il controllo positivo ha detto di chi era la colpa, e in un minuto**: `01-b3-cliente.py` contro
lo **stesso server, sulla stessa porta**, è arrivato a `SESSIONE` in **1003 ms** — *«⭐ SESSIONE:
stato=1 tela=1920x1080»*, e `01-b4-validatore.py` ha dichiarato **conforme** quella traccia, 6
messaggi su 6. ⇒ Il server non aveva sbagliato niente: aveva sbagliato **il cliente di prova**.

**Il difetto**, `[M]`: `_e_del_video()` diceva *«uno stream unidirezionale del server si riconosce
dai due bit bassi dell'identificatore QUIC»* — ⛔ e si prendeva **anche i tre stream unidirezionali
di HTTP/3**, il control stream e i due di QPACK, che `aioquic` apre da sé e che hanno gli stessi due
bit. Lo strato HTTP/3 restava senza i suoi byte, la CONNECT estesa non arrivava mai a `:status 200`,
il canale di controllo non si apriva.

⚠ **È la forma che questo progetto paga più spesso: un rosso puntato sull'imputato sbagliato.** E il
banco puntava sul server, che è precisamente ciò che `LEZIONI.md` §10 dice di aspettarsi.

### ⭐ Il secondo giro, curato il banco — ed è la misura

```
CONNECT estesa: :status = 200
⭐ SESSIONE: tela concessa 1920x1080
registrazione: f24-vivo.rcpreg (6 blocchi)
guardati: 0 flussi video · 0 conformi · 0 ambigui · 0 RICHIEDI_CHIAVE spedite
⛔ ZERO fotogrammi in 8.0 s.                                          USCITA=5
```

E l'arbitro delle registrazioni, sulla stessa traccia, **è d'accordo**:

```
⛔ NIENTE DA GIUDICARE: 6 blocchi, 0 sul canale video, ZERO flussi da giudicare
   Non e' «conforme»: e' l'assenza dell'oggetto del giudizio.          USCITA=3
```

⭐ **Che cosa questa misura dice, e vale più del verde che non è:**

1. ⭐ **il cliente di prova esiste davvero** — è stato girato, e al primo giro ha trovato un difetto
   (suo). Prima di oggi era `⏳ mai girato`;
2. ⭐ **la stretta di mano non è cambiata di un byte** con il `rcp.c` nuovo: `01-b3-cliente.py`
   arriva a `SESSIONE`, `01-b4-validatore.py` dice **conforme**, i tempi sono quelli (1003 ms del
   secondo fisso di §4.4-bis). Il canale video **non ha rotto niente**;
3. ⛔ **e zero fotogrammi non è un verde**: l'uscita **5** e l'uscita **3** dei due arbitri dicono
   *«non c'era niente da giudicare»*, e a mancare è **la cucitura di §5**, non il canale video.

---

## 5. Le righe che mancano — ⛔ e **non** sono in `main.c`

⭐ **`src/Makefile`: ZERO righe.** `rcp.c` è già nei `SORGENTI` e nei `GEMELLATI`.
⭐ **`src/main.c`: ZERO righe.** ⛔ **E questa è una correzione al mandato**: `main.c` non conosce
`rcp_ganci` — la struttura la riempie **`src/webtransport.c`**, nella funzione `rcp_avvia()` (riga
~797). Chi cercasse la cucitura in `main.c` non la troverebbe.

### `src/webtransport.c` — le due cuciture, e le primitive ci sono già

⚠ *Non l'ho toccato: non è mio (mandato §Vincoli). Qui c'è quel che serve, con i punti esatti.*

**(a) In `rcp_avvia()`, subito dopo `g.chiedi_verifica`:**

```c
	/* ⛔ §2.5: il canale video vive su stream unidirezionali del server. */
	g.video_apri   = gancio_video_apri;
	g.video_scrivi = gancio_video_scrivi;
	g.video_fin    = gancio_video_fin;
	g.video_azzera = gancio_video_azzera;
```

⚠ **E `memset(&g, 0, sizeof g)` c'è già** (riga 802): un ospite che non li collega non ha un canale
video, e `rcp.c` lo **dice** invece di tacere. La compatibilità con l'innesto di `banchi/rcp/` è
gratis.

**(b) I quattro ganci, e tutte le primitive esistono già in quel file:**

| il gancio | quel che deve fare | con che cosa |
|---|---|---|
| `video_apri` | apre uno stream uni e ci scrive il **preambolo di WebTransport** | `ngtcp2_conn_open_uni_stream()` (già usata a riga 1724 per i tre di HTTP/3) + `coda_metti(w, id, "\x40\x54" + varint(w->sessione), n, false)` |
| `video_scrivi` | accoda i byte | `coda_metti(w, id, d, n, false)` — ⛔ e **restituisce `false` se non entrano**, che `rcp.c` traduce in un azzeramento |
| `video_fin` | chiude con FIN | `coda_metti(w, id, NULL, 0, true)` — il flag `fin` c'è già (riga 394) |
| `video_azzera` | `RESET_STREAM` | `ngtcp2_conn_shutdown_stream_write()` (già usata a riga 1655) |

⛔ **Il preambolo `0x40 0x54` non è un dettaglio, ed è la proposta P18 qui sotto.** `webtransport.c`
lo sa già per gli stream **in arrivo** — riga 1164: *«uno stream WebTransport si riconosce dal suo
tipo, 0x54 — che come 0x41 non sta in un byte: sul filo sono 0x40 0x54»* — e lo stesso vale per
quelli in uscita.

**(c) Chi chiama il canale video** — cioè chi ha un fotogramma da spedire (F2.2 + F2.3):

```c
	/* §5.2: si chiede PRIMA di codificare, e costa zero. */
	bool chiave = rcp_video_serve_chiave(w->rcp);
	...
	int e = rcp_video_spedisci(w->rcp, chiave, dati, len, istante_us, input,
	                           ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
	if (e == RCP_VIDEO_TROPPO_GRANDE)   /* §6.2: si RICODIFICA, non si spedisce */
	if (e == RCP_VIDEO_SERVE_UNA_CHIAVE)/* §5.2: si ricodifica come chiave */
```

⛔ **E l'ordine conta**: `rcp_video_serve_chiave()` va chiesta **prima** di codificare. Chiederla
dopo vuol dire buttare un fotogramma già codificato ogni volta che la tela cambia.

---

## 6. ⛔⛔ Le regole che, applicandole, **non hanno retto** — tre

*`LEZIONI.md` §1.13, e ancora una volta le ha trovate **chi doveva farle rispettare**.*
*⛔ `RCP.md` **non è stato toccato**: qui c'è il caso concreto e il testo pronto.*

### ⭐⭐ P18 — `§2.5` · **lettura doppia**, ⛔ e la più grave: *«i primi due byte dello stream»* non esistono

**Il caso concreto.** Il server apre lo stream unidirezionale del fotogramma. §2.5 dice: *«si leggono
i **primi due byte dello stream**, che sono in ogni caso un campo `tipo`. Il byte alto dice il
canale»*. ⛔ **Su WebTransport non è vero.** Uno stream unidirezionale porta prima il **tipo dello
stream WebTransport** — `0x54`, che in varint sono **due byte, `40 54`** — e poi il **numero della
sessione**, anch'esso in varint. I 28 byte di §6.2 cominciano **dopo**.

Un lettore che applichi §2.5 alla lettera legge `0x4054` come campo `tipo`, ne ricava il **canale
`0x40`**, che non è nessuno dei cinque, e chiude con `ERRORE_PROTOCOLLO`. Un lettore che tolga il
preambolo legge `0x0301` e accetta. ⇒ **Due implementazioni conformi, due byte diversi, su ogni
fotogramma.**

⛔ **E non è una lacuna teorica: è un buco che oggi è tappato solo perché lo stesso autore ha scritto
tutt'e due i lati.** `src/webtransport.c` riga 1164 lo sa e lo commenta; `banchi/02-filo-cliente.py`
non lo sapeva, ⭐ **e il primo giro dal vivo è finito rosso proprio lì**. È il difetto muto contro cui
`RCP.md` §0 è stato scritto, ed è dentro la sezione che §0-bis presenta come *«la cura del buco più
insidioso»*.

⚠ **E vale anche per il canale di controllo**: uno stream bidirezionale di WebTransport comincia con
`0x41` (sul filo `40 41`) e col numero della sessione, e `RCP.md` non lo nomina in nessun punto —
§4.2 dice solo *«il primo stream bidirezionale della sessione»*.

> **Testo proposto**, da aggiungere a §2.5 subito prima di *«⭐ Come si riconosce il canale»*:
>
> ⛔ **E prima dei byte di RCP c'è il preambolo di WebTransport, che non è nostro e va tolto.** Uno
> stream **bidirezionale** comincia con il tipo di frame `WEBTRANSPORT_STREAM` (`0x41`) seguito dal
> **numero della sessione**; uno **unidirezionale** con il tipo di stream `0x54` seguito dallo
> stesso numero. ⚠ Tutt'e due sono **interi variabili di QUIC** (RFC 9000 §16), quindi sul filo
> `0x41` sono i due byte `40 41` e `0x54` i due byte `40 54`: chi li legge come un byte solo sfasa
> tutto quel che segue. ⇒ **Il «primo byte dello stream» di cui parla questo paragrafo è il primo
> byte DOPO il preambolo.** Senza questa riga, un lettore conforme ricava un canale `0x40` da ogni
> stream video e chiude con `ERRORE_PROTOCOLLO`.

### ⭐ P16 — `§6.2`, campo `numero` · **lettura doppia** · la stessa forma di P8→P14

**Il caso concreto.** Fase 3, linea cattiva. `SPECIFICHE.md` §8.3 e l'invariante **I1** impongono di
**calare i fotogrammi**: il server cattura 60 fotogrammi al secondo e ne spedisce 30. Il contatore
cresce di uno per fotogramma **catturato** o per fotogramma **spedito**?

⛔ **La stessa frase di §6.2 dice tutt'e due**, e sono grandezze diverse:

> *«contatore dei fotogrammi **catturati**, che cresce di uno per ogni fotogramma che il server
> **decide di spedire** — compresi quelli che poi abbandona»*

- «catturati» ⇒ il server che cala i fotogrammi lascia **un buco a ogni fotogramma saltato**, e §5.2
  fa mandare al client una `RICHIEDI_CHIAVE` **per ognuno**. ⛔ Ogni chiave costa dieci volte un
  delta, e §5.2 stesso chiude dicendo che *«un fotogramma chiave per ogni delta abbandonato è la
  spirale»*: la regola produce esattamente la spirale che la sezione esiste per evitare, **nella
  condizione che I1 protegge**;
- «che decide di spedire» ⇒ nessun buco, e i buchi restano quel che §6.2 vuole che siano: i
  fotogrammi **abbandonati**.

⭐ **È la forma di `LEZIONI.md` §1.13 letta al contrario**: il campo è **nominato** con una grandezza
(*i catturati*) e **definito** con un'altra (*gli spediti*), e chi legge il nome scrive un server
diverso da chi legge la definizione. ⚠ Oggi non si vede perché la fase 2 spedisce **un** fotogramma:
morde alla prima riga di fase 3 che cala il ritmo.

**Che cosa ho scritto io, e perché:** il contatore cresce **solo quando un fotogramma viene
spedito** — la metà operativa della frase, quella che non produce la spirale. `[M]` il banco lo
verifica sulla scena `giro-del-contatore`.

> **Testo proposto**, a sostituzione delle prime parole della riga `numero` di §6.2:
>
> | `numero` | ⛔ contatore dei fotogrammi **che il server decide di spedire** — **compresi quelli che poi abbandona**, e ⛔ **esclusi quelli che decide di NON spedire** per calare il ritmo (`SPECIFICHE.md` §8.3). ⚠ La differenza non è di parole: se il contatore crescesse anche per i fotogrammi saltati, calare il ritmo aprirebbe un buco a ogni fotogramma, e §5.2 farebbe chiedere al client una chiave per ognuno — la **spirale** che §5.2 stesso dichiara di voler evitare, e proprio quando la linea è cattiva, cioè nella condizione che l'invariante I1 esiste per proteggere. ⇒ Un buco nella successione significa **una cosa sola**: un fotogramma abbandonato (§5.1) |

### P17 — `§5.2`, i 200 ms · `[?]` · **un orologio dove la grandezza vera è una coda**

**Il caso concreto.** Il minimo dichiarato è **480p a 25** (`CODER.md` §1), quindi le linee cattive
sono **dentro** il modello. Il server spedisce una chiave da 3 MiB; su una linea che porta 2 Mbit/s
ci mette **dodici secondi** ad arrivare. Il client, che intanto vede un buco, manda
`RICHIEDI_CHIAVE`. §5.2 permette al server di ignorarla *«entro 200 ms dall'ultima chiave che ha
**spedito**»* — e quei 200 ms sono passati da un pezzo. ⇒ Il server spedisce **una seconda chiave**
mentre la prima è ancora in volo, e ⛔ **peggiora esattamente la condizione che l'ha provocata**.

⚠ **È la stessa forma di P13**, un passo più in là: la riga sceglie un **orologio** dove la grandezza
vera è **una coda**, e il protocollo la porta già — il server sa se lo stream della chiave precedente
è ancora aperto, perché è lui a tenerlo aperto fino al FIN. ⭐ E `RCP.md` ha già scelto bene una
volta, sulla stessa riga: *«non dall'ultima richiesta ricevuta»*, perché contando dalle richieste
l'orologio si sposta all'infinito. Il passo che manca è lo stesso, dall'altra parte.

> **Cura proposta** (⚠ `[?]`, **non misurata**: qui non c'è un banco con una linea lenta, e la riga
> è del coordinatore): *«il server PUÒ ignorare una `RICHIEDI_CHIAVE` finché **una chiave è ancora
> in volo** — lo stream aperto e non ancora chiuso con FIN — e per 200 ms dopo che l'ultima è
> uscita per intero»*.

**Che cosa ho scritto io:** ⛔ **la riga com'è**, i 200 ms dall'ultima chiave **spedita**, con il
rilievo dichiarato nel commento accanto. Il codice porta *quel che il documento comanda*, non quel
che sarebbe giusto — è la stessa regola che i due arbitri applicano a se stessi.

---

## 7. Che cosa resta `[?]`, e che cosa chiedo

| | |
|---|---|
| ⛔ **che un fotogramma arrivi davvero sulla rete** | ⏳ **ancora aperta**, e adesso si sa esattamente che cosa manca: i quattro ganci in `webtransport.c` (§5). Il cliente di prova è pronto e girato |
| ⛔ **il percorso del video nel cliente di prova non è mai stato percorso** | la cura di P18 nel banco (`_smista`) è scritta ma ⚠ **nessun byte video l'ha ancora attraversata**: nessuno ne ha spediti. Va riprovata al primo fotogramma vero |
| ⛔ **P5/P8/P9/P11/P13 sul filo** | `ADATTA_TELA` non è servito ⇒ le regole della tela non si esercitano dal vivo. Il codice le rispetta, `02-filo-prodotto.py` le prova **in processo** |
| **la chiave «vera»** (VPS/SPS/PPS dentro) | `rcp.c` non guarda i byte del codec, e non deve ⇒ **è di F2.3** |
| ⚠ **lo stesso sorgente, non lo stesso binario** | `02-filo-prodotto.c` compila `banchi/rcp/rcp.c` con un `#include`. Le due copie sono identiche per costruzione (`Makefile`), ma è un fatto diverso |

**A chi chiedo che cosa:**

| a chi | che cosa |
|---|---|
| ⛔ **il coordinatore** | le tre proposte di §6 — ⭐ **P18 per prima**: è una lettura doppia che fa cadere ogni fotogramma, e oggi è tappata solo perché lo stesso autore ha scritto i due lati |
| ⛔ **chi possiede `webtransport.c`** | le due cuciture di §5. Le primitive esistono già tutte in quel file |
| **F2.3** (la codifica) | chiamare `rcp_video_serve_chiave()` **prima** di codificare, e la metà di P9 che sta nei dati |
| **F2.2** (la cattura) | `istante_us` dall'orologio **monotono**, e `input` — l'id dell'ultimo input iniettato, 0 se nessuno |
| **F2.1** (la sessione) | quando `ADATTA_TELA` sarà servito, chiamare `rcp_tela_adattata()` **dopo** aver spedito `TELA(ADATTATA)` — la regola di §6.2 sta in un posto solo, lì |

---

## 8. Lo stato delle porte, e le certificazioni scadute

| | prima | dopo |
|---|---|---|
| **7448** (il prodotto di casa) | **2** ascoltatori | **2** ⭐ intatta |
| **7501** (il bersaglio di P5) | **2** ascoltatori | **2** ⭐ intatta |
| **7514** (la mia) | 0 | 0 — accesa per il giro e **spenta** |

⛔ **Non ho ricostruito il prodotto di casa.** Il server della misura è stato costruito in un albero
**suo** (`/srv/src/f24`, gemello `/srv/src/f24-rcp`) con ban-file, socket e certificati propri:
`/media/REMOTIX/src/remotix` **non è stato toccato**, quindi `01-casa-7448.sh stato` continua a dire
quel che diceva.

⚠ **Le certificazioni che questo giro fa scadere** — elencate, non rincorse:

| | perché |
|---|---|
| **B3** · **B5** · **B11** · **B13** | girano sul `rcp.c` del prodotto, che è cambiato. ⭐ Ma il filo della **fase 1** non è cambiato di un byte, e c'è la misura: `01-b3-cliente.py` arriva a `SESSIONE` e `01-b4-validatore.py` dichiara **conforme** la traccia sul binario nuovo `[M]` |
| **B6** · **B8** | usano `banchi/rcp/`, anch'esso cambiato (è la copia gemella, e deve esserlo) |
| **P5** (`01-p5-*`) | gira sulla 7501, che non ho toccato, ma il prodotto di riferimento è cambiato nei sorgenti |
| ⭐ **F2.4 (i due arbitri)** | **non scadute**: `02-filo-fotogramma.py` e `02-filo-validatore.py` non li ho toccati, e `02-filo-lancia.sh` dà **6 su 6** dopo le mie modifiche |

⛔ *«Scaduta» non è «fallita», e non è nemmeno «pulita»*: chi rimetterà in fila le certificazioni ha
qui l'elenco e la ragione di ciascuna.
