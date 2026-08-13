# CORSIA B — La codifica HEVC in hardware dentro il prodotto

*13 agosto 2026, sera. Tutto quel che segue è stato misurato sulla macchina, non dedotto dal
sorgente. Le misure di tempo portano la scena accanto.*

---

## ⭐⭐ In una riga

**Il prodotto codifica HEVC Main10 in hardware su `/dev/dri/renderD128`, e i suoi byte —
impacchettati come li impacchetta lui — escono dal `VideoDecoder` di Chrome come **120 fotogrammi su
120, 3 giri su 3**, `format: null` (opachi, sulla GPU).** Il tratto della codifica scende da **28,0 ms
a 2,6 ms** per fotogramma.

⛔ **E il motivo per cui oggi si negozia il codec 2 è TROVATO, con il caso, e non è nel server**:
sono le due sonde HEVC incollate in `src/pagina.html`, che portano `profile_idc = 4` (**Rext**)
invece di Main/Main10. Chrome le rifiuta — `EncodingError` — e la pagina conclude che HEVC non
arriva al pixel. **Sta fuori dal mio perimetro: serve il via del coordinatore.** (§B7)

---

## 0. Dove ho lavorato, e le impronte

| | |
|---|---|
| **copia** | `/media/REMOTIX/src/03-B-src/` sul server → `/srv/src/03-B-src/` nel contenitore, con `src/` e `banchi/rcp/` (il gemello) |
| ⛔ **l'albero del deposito** | **NON toccato**: `src/codificatore.c` · `.h` · `figlio.c` · `Makefile` hanno le stesse sha256 di quando ho cominciato (`02babbc4…`, `bb3424a5…`, `ecb60d93…`, `c25a1445…`) |
| ⛔ **porte protette** | **7448 · 7501 · 7561**, contate **prima** (19:09) e **dopo** (19:40): le stesse tre, e nessun'altra `:7xxx` sul server. Non le ho toccate |
| **porta mia** | nessuna aperta: il lavoro non ha mai acceso il prodotto — vedi «cosa NON ho fatto» |

### Le impronte dei binari

| | sha256 |
|---|---|
| il prodotto del deposito, **intatto** (`/srv/src/remotix/remotix`) | `a097385b12d4fe816920f0769322aef6197600ec1c9ca065e957df7b38e4de4b` |
| **SANO** — la mia copia, sorgenti del deposito, ricostruita | `5796dae430dd40b7d8285f62fff3ceecb01c5322ede10dd78cd0460ff326841c` |
| ⭐ **NUOVO** — la mia copia, con la codifica in hardware | `7a5ee61d13ef010f2f36eda9fcf90df8bb1d7552bef665fb3b2daac4b16ec56f` |

⚠ Il SANO non torna identico al binario del deposito pur avendo gli stessi sorgenti: **la
costruzione non è riproducibile bit per bit**, ed è la trappola già scritta nel catalogo. Per questo
il confronto è SANO↔NUOVO, non deposito↔NUOVO.

### Le impronte dei sorgenti nuovi (sulla copia)

```
dcc7ed3ad4927514e05c496c13d26ec7cb9d9acb92d7e2f37a9114065dd60e23  codificatore.c
7bc74545753c801707b0186357dacbc04bb88238b6ac142bb6612d548e27692c  codificatore.h
5b61b12200c92b1de32ce8d58c8e4e8d1b70c22376276445a5b90495eb9dc268  figlio.c
69577003bec70d87f5eca2a50ea88a8d13251348d8e78f1a9e6ac643324784a8  Makefile
```

---

## ⛔⛔ 1. TRE PREMESSE DEL MANDATO SONO SMENTITE, E OGNUNA CON UN CASO

### 1.1 «`VAProfileHEVCMain10 : VAEntrypointEncSliceLP` su renderD128 **e renderD129**» — FALSO

I due nodi **non sono due code della stessa scheda**: sono **due fornitori diversi**.

```
/dev/dri/renderD128  →  0000:00:02.0  i915    Intel  (8086:4680)
                        VA: Intel iHD 25.2.3
                        VAProfileHEVCMain10 : VAEntrypointEncSliceLP     ← solo LP
/dev/dri/renderD129  →  0000:03:00.0  amdgpu  AMD Radeon RX 6800 (navi21)
                        VA: Mesa Gallium 25.0.7 (radeonsi)
                        VAProfileHEVCMain10 : VAEntrypointEncSlice       ← la PIENA
```

⭐ **E la prova non è `vainfo`: è il controllo negativo del prodotto.** Chiedendo la codifica
**piena** su `renderD128`, il codificatore rifiuta e **dice che cosa il driver ha davvero**:

> `su «/dev/dri/renderD128» (Intel iHD driver for Intel(R) Gen Graphics - 25.2.3 ()) il profilo 18
> NON ha l'entrypoint EncSlice (piena): il driver ne dichiara [1,8]`

(1 = `VAEntrypointVLD`, 8 = `VAEntrypointEncSliceLP`.)

### 1.2 ⛔⛔ `renderD129` (AMD) **NON È USABILE a 1080p**, e non è un'opinione

Il codificatore del prodotto ha **rifiutato ogni fotogramma** su quel nodo:

> `⛔ il flusso MOSTRA 1920x1088 (ne codifica 1920x1088) e la tela e' 1920x1080`

⭐ **E non è il nostro lettore che sbaglia — l'ho verificato con uno strumento terzo.** `ffprobe`
sullo stesso flusso:

| nodo | `ffprobe` dice |
|---|---|
| `renderD128` (Intel) | `1920,1080,1920,1080` |
| ⛔ `renderD129` (AMD) | **`1920,1088,1920,1088`** |

⇒ `hevc_vaapi` su radeonsi allinea a 1088 e **non scrive la finestra di conformità**: un client
dipingerebbe **otto righe di spazzatura** in fondo, e l'immagine sarebbe alta 1088. ⭐ **Il prodotto
se n'è accorto da sé** perché il controllo `RCP.md` §6.2 c'era.

### 1.3 ⚠ «B3: `EncSliceLP` … si dichiara accanto al numero» — vero, ma **non è tutta la scelta**

Il mandato la dava come limitazione da dichiarare. ⭐ In realtà su questa macchina la codifica
**piena esiste**, sull'AMD — solo che (§1.2) consegna un flusso inservibile a 1080p. ⇒ La riga
onesta non è *«siamo in bassa potenza e ce lo teniamo»*: è **«la piena c'è, l'ho provata, e cade per
un'altra ragione»**. Il prezzo di qualità della LP resta `[?]` (§«cosa resta»).

---

## 2. B0 — il primo controllo, e la metà che restava aperta

Non ho rifatto la prova del `VideoDecoder`: l'ha chiusa l'altro agente
(`fasi/rapporti/F3-B0-webcodecs.md`, 120 su 120, 5 giri su 5). ⭐ **Ho chiuso la metà che lui ha
dichiarato aperta**, ed era la sua condizione perché B1 finisse — §6 qui sotto.

Ho letto `banchi/03-palco-esiti.jsonl` e le quattro sonde `03-palco-*` prima di scrivere un
carattere. ⛔ **Non ho modificato nessun banco.**

---

## 3. B1 · B2 · B3 — che cosa ho sviluppato

### `src/codificatore.h` — quattro cose nuove, e tutte per non indovinare

| | |
|---|---|
| `nodo_rendering` | ⛔ `NULL` **non vuol dire «quello buono»**: vuol dire *fallisci dicendolo*. Vedi §1.1 |
| `PotenzaEntrypoint` | **tre esiti, non due**: `NON_DICHIARATA` (lo zero) fallisce apposta, poi `PIENA` e `BASSA` |
| `CODIFICATORE_QUALITA_QP` | ⛔ un modo **a parte**, non «CRF sull'hardware». CRF e QP non sono la stessa grandezza, e chiamare QP «CRF» sarebbe due misure sotto la stessa etichetta |
| `us_caricamento` | ⭐ il **quarto tempo**, e sta separato apposta: è esattamente il tratto che la **copia zero della fase 8** esiste per togliere. Sommarlo alla codifica renderebbe invisibile quanto varrà quel lavoro |

E nella confessione: `in_hardware`, `nodo`, **`fornitore_va`** (chiesto a `vaQueryVendorString()`, non
dedotto dal numero del nodo), `bassa_potenza` + `bassa_potenza_verificata`,
`profondita_asincrona`, `larghezza/altezza_codificata`.

### `src/codificatore.c`

- apertura VA-API sul nodo **dichiarato**, magazzino di superfici `P010LE` (10 bit) / `NV12` (8);
- ⭐ **la coppia (profilo, entrypoint) si legge dal driver con `vaQueryConfigEntrypoints` PRIMA di
  aprire**. Fra *«ho passato `low_power=1` a libavcodec»* e *«il driver ce l'ha»* c'è la stessa
  distanza che fra un'opzione stampata come errore e un'uscita 0;
- ⛔ **`async_depth = 1`**, e **si rilegge dopo l'apertura**. ⚠ Il difetto di `hevc_vaapi` è **2**, e
  nessuno l'aveva chiesto: è lo stesso difetto non chiesto di `bframes=4` su x265, in un'altra
  veste. Con 2, il ciclo di `figlio.c` — che manda un fotogramma e ne aspetta subito il pacchetto —
  prenderebbe `EAGAIN` al primo giro, cioè il ramo che mette il codificatore in scarico e lo fa
  riaprire, **con una chiave in più a ogni fotogramma**;
- `rc_mode = CQP` chiesto **per nome** (non `auto`, che sceglie in base alle altre opzioni),
  `idr_interval = 0`, profilo chiesto anche sull'opzione del componente;
- ⛔ **nessun ripiego silenzioso**: `LOSSLESS` in hardware **fallisce dicendo perché** (e dicendo che
  `qp=0` NON è «senza perdita», è la sentinella «non chiesto» — la stessa forma già pagata su
  `crf=0`), e `CRF` in hardware fallisce indicando `QUALITA_QP`.

### ⭐ Una cura che non cercavo — il lettore di SPS saltava la finestra di conformità

`leggi_sps_hevc()` leggeva i quattro `conf_win_*_offset` **e li buttava via**. ⚠ Non si era mai
visto perché `libx265` a 1920×1080 non ne mette una. È saltato fuori solo con l'hardware. **È curato**
(scarti in unità di croma, `[S]` H.265 §7.4.3.2), e adesso le due grandezze — quel che si **codifica**
e quel che si **mostra** — sono **due campi separati**, perché un giorno la differenza costerà banda.

⛔ **La cura non salva renderD129**: lì la finestra **non c'è proprio** (§1.2).

### `src/figlio.c` — B2 e B7 lato server

```c
#define NODO_RENDERING   "/dev/dri/renderD128"
#define POTENZA_RENDERING CODIFICATORE_POTENZA_BASSA
#define QP_HARDWARE      26
```

⛔ **Nel programma, non in una variabile d'ambiente** (invariante I7): un nodo preso dall'ambiente
sparirebbe il giorno in cui qualcuno accende il servizio a mano, e il sintomo sarebbe **il
codificatore in software con la stessa etichetta**.

**Perché l'Intel e non l'AMD**: (1) l'AMD consegna un flusso inservibile a 1080p `[M]`; (2) è più
veloce `[M]`; (3) è la scheda che compone il desktop, cioè quella dove i fotogrammi staranno già
quando la fase 8 toglierà la copia.

⭐ **HEVC si prova prima in hardware; AV1 no**, e la ragione è misurata: `av1_vaapi` esce 218. Il
ripiego su `libx265` **si scrive nel registro** con il conto accanto (~22 ms contro ~3), e
`codificatore_nome()` porta **nodo, fornitore ed entrypoint dentro il nome** — la riga che finisce
nel registro accanto a ogni numero:

> `HEVC 10 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD driver for Intel(R) Gen
> Graphics - 25.2.3 () · ⚠ EncSliceLP, bassa potenza — NON e' la codifica piena)`

### `src/Makefile`

`libva` (>= 1.22) innestata come **sesta dipendenza dichiarata**, con accanto le due sole funzioni
per cui serve, e aggiunta ai controlli di `dipendenze`. ⚠ Sul contenitore c'era già, tirata dentro da
`libavutil-dev`: **la riga sta lì lo stesso**, perché una dipendenza che c'è per rimbalzo sparisce il
giorno in cui l'altra cambia idea.

---

## 4. LE MISURE — ciascuna con la scena accanto

### La scena, dichiarata

| | |
|---|---|
| macchina | **NIC-OS 192.168.0.2**, dentro il contenitore |
| carico | **0,18–0,37** a un minuto |
| vicini | **11** processi `remotix`/`Xvfb`/`chrome` guardati **su una finestra vera di mezzo secondo**: ⭐ **nessuno consuma più dello 0 %** — accesi e fermi |
| porte | `:7448 :7501 :7561` prima e dopo, nient'altro |
| contenuto | **SINTETICO**, in **due** varietà (vedi sotto) |
| metodo | `codificatore_comprimi()` chiamata **da fuori** (`CODER.md` §3.6), 120 fotogrammi **dopo 10 di riscaldamento** (§3.5), **mediana** |

⛔ **Il banco RIFIUTA di misurare se non è solo, e l'ha fatto due volte** — la prima con 6 vicini
contati per presenza, la seconda con il carico a 2,12 lasciato dal mio giro precedente. È uscito
**2**, non 0.

⚠ **E il criterio è stato corretto durante il lavoro, perché era spento**: contare la *presenza* dei
vicini avrebbe fatto rifiutare **sempre** — i tre server dell'utente sono sempre accesi. Adesso
conta quanto **consumano**, processo per processo, e li stampa.

### ⛔ Perché DUE scene, e non una

`[M]` i codificatori in hardware sono quasi indifferenti al contenuto, quelli in software no. **Con
una scena sola si può dimostrare quel che si vuole**, e tutte e due le frasi sarebbero «misurate».

### ⭐ Il cammino SERIALE — che è quello del prodotto, non la portata di `ffmpeg`

*mediana in ms per fotogramma, 1920×1080 a 10 bit, ingresso BGRx*

| | **scena FACILE** | | | | **scena DURA** | | | |
|---|---|---|---|---|---|---|---|---|
| | **totale** | conv. | carico | codifica | **totale** | conv. | carico | codifica |
| ⭐ **hevc_vaapi** renderD128 · LP · QP 26 | **9,73** | 5,65 | 1,44 | **2,64** | **11,41** | 5,64 | 1,46 | **3,93** |
| `libx265` software · CRF 20 | **31,44** | 3,33 | — | 28,03 | **229,50** | 3,37 | — | 225,89 |
| ⛔ `libsvtav1` software · CRF 20 — **quel che gira oggi** | **9,84** | 3,52 | — | 6,17 | **116,43** | 3,41 | — | 113,10 |
| `hevc_vaapi` renderD129 (AMD) · PIENA | ⛔ **0 fotogrammi su 120** | | | | ⛔ **0 su 120** | | | |

Byte per fotogramma, stessa tabella: hardware 1 138 / 1 388 273 · x265 640 / 691 402 · svtav1 512 /
1 771 970.

### ⛔⛔ Quel che questi numeri dicono, e **NON è quel che il mandato si aspettava**

1. ⭐ **Il tratto della codifica crolla**: 28,03 → **2,64 ms** contro x265, 6,17 → 2,64 contro
   SVT-AV1 sulla scena facile; e sulla scena dura **113,10 → 3,93**. Il codificatore in hardware è
   **quasi indifferente al contenuto** (2,64 → 3,93, +49 %), quello in software no (6,17 → 113,10,
   **×18**). Questo regge da tutte le parti.
2. ⛔⛔ **MA IL TOTALE SERIALE, SULLA SCENA FACILE, NON MIGLIORA: 9,73 contro 9,84.** Perché il collo
   di bottiglia **si è spostato**: con la codifica a 2,6 ms, **il pezzo grosso è la CONVERSIONE dei
   colori — 5,65 ms, più del doppio della codifica**. E la conversione verso `P010LE` (hardware)
   costa **5,65** dove quella verso `yuv420p10le` (software) costa **3,52**: ⇒ **l'hardware si è
   comprato 3,5 ms di codifica pagandone 2,1 di conversione e 1,4 di caricamento.**
3. ⇒ ⛔ **La riga «circa otto volte più veloce» del piano vale per il TRATTO, non per l'anello.**
   Quanto valga davvero sull'anello dipende da quanto la scena vera è dura — e su quella,
   `libsvtav1` faceva **22,23 ms**, cioè sta molto più vicino alla mia scena dura che alla facile.
   **Il numero che conta lo farà la corsia E**, sulla scena vera, con `03-b17-ritardo.py`.
4. ⭐ **E la conseguenza operativa è che c'è un secondo pezzo da aggredire, e non era in programma**:
   `swscale` BGRx→P010 in software. È il candidato naturale della **copia zero della fase 8** —
   ⛔ **che non ho anticipato (B5)**, ma che adesso ha un numero attaccato: **7,1 ms su 9,7**.

---

## 5. B4 — la chiave forzata con VA-API

⭐ **Funziona su `renderD128`, e non l'ho creduto: l'ho innestato.** Al fotogramma 60 (a regime, non
all'avvio) il banco chiama `codificatore_chiedi_chiave()`, e:

- il codificatore ha consegnato una **CHIAVE**, non un delta;
- la forma dei byte è passata: **VPS+SPS+PPS davanti all'IDR**, verificati su ogni chiave da
  `forma_va_bene()` come prima;
- `riordina: no` (`dts == pts` su tutti i 120), `trattenuto: no` (nessun `EAGAIN`).

⛔ **E il rilevatore non è cieco**: se fosse uscito un delta, `codificatore_comprimi()` sarebbe
tornata `false` da sé — il rosso è **dentro il prodotto**, e il banco lo legge. ⚠ **Non ho rigirato
`banchi/03-b15-movimento.py`**: è fuori dal mio perimetro. Vedi §8.

---

## 6. ⭐⭐ La `[?]` che il coordinatore ha lasciato aperta — CHIUSA

> *«È chiuso "il decodificatore accetta e conta". **Non** è chiuso "il NOSTRO impacchettatore
> produce chunk che quel decodificatore accetta".»*

⛔ **E non ho riusato il suo spezzatore, apposta**, perché la sostanza della prova è che **il
prodotto non spezza niente**: `codificatore_comprimi()` consegna **un pacchetto = un fotogramma**, e
`RCP.md` §6.2 lo mette sul filo con la lunghezza davanti. Il confine **non si indovina rileggendo il
bitstream: è già scritto.**

Ho fatto **versare al codificatore del prodotto** i suoi pacchetti, uno per fotogramma (4 byte di
lunghezza + 1 byte chiave/delta), e li ho dati al `VideoDecoder` di Chrome **leggendo il confine
dalla lunghezza**.

**Scena**: CHUWI, Xvfb `:110-:112`, `google-chrome` 151 **senza** `--disable-gpu`, `/tmp` a 1 450 M
liberi, GPU vista dalla pagina `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))`.

| giro | pezzi | chiavi | fotogrammi in uscita | misura | `format` |
|---|---|---|---|---|---|
| 1 | 120 | 2 | ⭐ **120** | 1920×1080 | `null` |
| 2 | 120 | 2 | ⭐ **120** | 1920×1080 | `null` |
| 3 | 120 | 2 | ⭐ **120** | 1920×1080 | `null` |
| ⛔ controllo negativo `--disable-gpu` | 120 | 2 | **0** | — | `OperationError: Unsupported configuration` |

⭐ `format: null` = fotogrammi **opachi, sulla GPU**. E il controllo negativo dice che a
decodificare è davvero l'hardware: senza GPU **`configure()` stesso rifiuta**.

⛔ **E questo giro è nato ROSSO, per colpa MIA**: il primo versamento partiva dal fotogramma 10, cioè
da un **delta**, e Chrome ha risposto *«A key frame is required after configure()»* **3 giri su 3**.
Difetto del banco, non del prodotto — **e si è visto solo perché il decodificatore sa dire di no**.

---

## 7. ⛔⛔ B7 — PERCHÉ OGGI SI SCEGLIE IL CODEC 2, E LA CATENA È COMPLETA

### La catena, letta nel sorgente e poi misurata

| | |
|---|---|
| `src/rcp.c:1128-1190` | `prima_comune()` scorre **l'elenco del CLIENT** e prende la prima voce che il server conosce ⇒ **l'ordine lo detta il client** |
| `src/pagina.html:2288-2300` | nel `CIAO` finiscono **solo** i codec che su quel browser hanno **davvero dipinto** una sonda vera |
| ⇒ | se il client non mette `hevc` nel `CIAO`, il server sceglie `av1` = **2**, e **non c'è una riga del server da cambiare** |

### La misura — e la mia prima ipotesi è stata SMENTITA da sé

Sospettavo la **misura** delle sonde: sono **64×48**, e `hevc_vaapi` rifiuta di **codificare** sotto
128×128 (*«Hardware does not support encoding at size 64x48 (constraints: width 128-16384 height
128-12288)»*, `[M]` oggi). ⛔ **Falso.** Ho decodificato una scala intera in Chrome con GPU:

| flusso | misura | `isConfigSupported` | fotogrammi in uscita |
|---|---|---|---|
| ⛔ **la sonda del prodotto, 8 bit** (`pagina.html:497`) | 64×48 | **true** | ⛔ **0** — `EncodingError: Decoding error` |
| ⛔ **la sonda del prodotto, 10 bit** (`pagina.html:500`) | 64×48 | **true** | ⛔ **0** — `EncodingError: Decoding error` |
| ⭐ `libx265` Main10, **stessa misura** | 64×48 | true | ⭐ **1** |
| `libx265` Main10 | 128×96 | true | ⭐ 1 |
| `libx265` Main10 | 320×240 | true | ⭐ 1 |
| `hevc_vaapi` renderD128 | 320×240 | true | ⭐ 1 |
| `hevc_vaapi` renderD128 | 640×480 | true | ⭐ 1 |
| ⭐ `hevc_vaapi` renderD128 — **il controllo** | 1920×1080 | true | ⭐ **1** |

⇒ **Non è la misura, non è il codec, non è il palco: sono proprio QUEI BYTE.**

### La causa, letta nei byte e riprodotta

```
sonda8.265      (da src/pagina.html)   profile_idc = 4   ← Rext
sonda10.265     (da src/pagina.html)   profile_idc = 4   ← Rext
x265-64x48.265  (fatto da me)          profile_idc = 2   ← Main 10
```

`ffprobe` conferma: le sonde del prodotto sono **`Rext`**, non `Main`/`Main 10`. E la stringa che la
pagina dichiara è `hev1.**1.6**…` / `hev1.**2.4**…`, cioè profilo **1** e **2**. ⇒ **La stringa e i
byte dicono due cose diverse**, `isConfigSupported` risponde alla stringa (e dice **true**), e il
decodificatore hardware — che ha `VAProfileHEVCMain`/`Main10`, non Rext — **cade sui byte**.

⭐ **E la riga esatta, riprodotta tre volte:**

| `-x265-params` | profilo che esce |
|---|---|
| `log-level=none:bframes=0:**keyint=1**:info=0` ← quello di `banchi/02-pagina-sonda-codec.py:121` | ⛔ **Rext** |
| `log-level=none:bframes=0:info=0` (**senza `keyint=1`**) | ⭐ **Main 10** |

⛔ **`keyint=1` fa emettere a libx265 «Main 10 Intra» (`profile_idc` 4) ANNULLANDO il `-profile:v
main10` chiesto due righe sopra.** Ed è la forma d'errore che **il commento di quel file stesso
descrive**, alla riga 115: *«x265 lasciato scegliere emette Main 10 Intra (Rext, profile_idc 4), che
non è quel che il prodotto configura»*. Il profilo **è stato chiesto** — e **non applicato**, senza
un errore.

⚠ **E la sonda non è "vecchia"**: ho rigirato `banchi/02-pagina-sonda-codec.py` e produce **il
base64 identico, byte per byte**, a quello che sta in `pagina.html`. Il generatore è ancora
difettoso oggi.

### ⛔ La cura è di due righe, e sta FUORI dal mio perimetro

| che cosa | dove | perché non l'ho fatto |
|---|---|---|
| togliere `keyint=1` (o chiederlo in un modo che non cambi il profilo) | `banchi/02-pagina-sonda-codec.py:121` | ⛔ è un **banco** |
| ⭐ e **aggiungere il controllo che manca**: leggere `profile_idc` **dai byte prodotti** e cadere se non è quello chiesto | idem | idem — ⚠ senza questo, la cura regge finché nessuno rimette un'opzione che fa cambiare profilo |
| reincollare le due `dati:` di `SONDE` | `src/pagina.html:497-506` | ⛔ è un `src/` **non mio** |

⇒ ⭐ **Il protocollo NON va toccato**, esattamente come dice il mandato: `RCP.md:699` e `:1404`
restano dove sono, `NOSTRO_CODEC` resta `"hevc,av1"`, e `prima_comune()` non si tocca. **Va tolto il
motivo, e il motivo è un fotogramma di 114 byte.**

⚠ **E il ripiego AV1 deve restare vivo e dichiarato**, come il coordinatore ha misurato: senza GPU
HEVC dà zero, e Firefox headless dà `NotSupportedError` 5 su 5. Nel mio `figlio.c` il ripiego **è**
dichiarato nel registro con il conto accanto.

---

## 8. B5 e B6 — quel che ho nominato e NON ho fatto

**B5 — la copia zero**: ⛔ **non anticipata**, resta alla fase 8. ⭐ Ma adesso ha un numero:
`us_caricamento` è **1,44-1,47 ms**, e la conversione che la precede è **5,65**. ⇒ Il tratto che la
fase 8 può togliere è **~7,1 ms su 9,7**, cioè **il 73 % del cammino seriale della codifica**. Il
campo è separato apposta perché quel numero si possa leggere invece di doverlo stimare.

**B6 — i sotto-livelli temporali con `EncSliceLP`**: **nominato, non fatto**. `[M]` `ffmpeg -h
encoder=hevc_vaapi` **non espone nessuna manopola** per i livelli temporali: le sole righe che
somigliano sono `b_depth` (profondità di riferimento dei B, e con `low_power` su Intel i B non ci
sono) e `tier`. ⇒ ⚠ **Per come stanno le cose oggi, la strada non passa da un'opzione di ffmpeg**:
vorrebbe o `nal_temporal_id_plus1` scritto da noi, o VA-API parlata direttamente. **È lavoro suo**, e
la `[?]` da chiudere per prima è *«l'`EncSliceLP` di iHD accetta più di un livello temporale?»* —
che si risponde con `vaQueryConfigAttributes`, non con `ffmpeg`.

---

## ⛔ 9. CHE COSA NON HA FUNZIONATO

| | |
|---|---|
| ⛔⛔ **`renderD129` (AMD): 0 fotogrammi su 120, tutte e due le scene** | consegna 1920×**1088** senza finestra di conformità. Confermato da `ffprobe`, cioè **non è il nostro lettore**. Il nodo è **inservibile a 1080p** finché o si allinea la tela a 64, o si cura ffmpeg |
| ⛔ **Il mio banco è nato ROSSO tre volte, e tutte e tre per colpa sua** | (1) rifiutava di misurare contando i vicini **per presenza** invece che per consumo ⇒ non avrebbe misurato **mai**; (2) versava i pezzi partendo da un **delta** ⇒ Chrome *«A key frame is required»* 3 su 3; (3) `Address already in use` sulla porta del servo fra un giro e l'altro. **Tutti e tre curati**, e il secondo l'ha trovato **il decodificatore**, non io |
| ⛔ **La mia prima ipotesi su B7 era sbagliata** | «le sonde sono 64×48 e l'hardware non scende sotto 128» — ⇒ **smentita da un caso**: un Main10 di 64×48 decodifica benissimo. La causa vera è il **profilo**, non la misura |
| ⚠ **Il totale seriale sulla scena facile NON migliora** | 9,73 contro 9,84 di oggi. Il guadagno è tutto nel tratto della codifica, e sulla scena facile se lo mangia la conversione. ⛔ Non è un fallimento dell'hardware: è **il collo di bottiglia che si è spostato**, e va detto prima che qualcuno legga «×8» sull'anello |
| ⚠ **Il primo tentativo di misura è stato rifiutato dal banco stesso** | carico 2,12 lasciato dal giro precedente ⇒ uscita **2**. Ho aspettato e rimisurato. È il comportamento voluto |
| ⚠ **`nome[160]` troncava il fornitore VA** | l'unico avviso del compilatore, e non l'ho zittito: portato a 320, perché un nome troncato nel registro toglie **proprio** il pezzo che dice quale macchina ha fatto il numero |

---

## ⏳ 10. CHE COSA RESTA `[?]`

| | |
|---|---|
| ⛔⛔ **quanto vale davvero sull'anello** | le mie due scene sono **sintetiche** e **bracchettano**: facile 9,73≈9,84 (nessun guadagno), dura 11,41 contro 116,43 (×10). La scena vera sta in mezzo, e `libsvtav1` su quella faceva 22,23 ms — più vicino alla dura. ⇒ **Il numero è della corsia E**, stesso banco e stessa scena del 13 |
| ⛔ **la qualità di `EncSliceLP` a parità di banda** | **non misurata**. So che il flusso esce, che è Main10 e che si dipinge; **non so quanto è brutto** rispetto alla piena o a x265. ⚠ E il confronto ovvio — l'AMD in codifica piena — **non si può fare**, perché quel nodo non consegna (§1.2) |
| ⚠ **QP 26 non è CRF 20** | i byte per fotogramma non combaciano (1 138 contro 640 sulla scena facile). ⛔ Le due righe della tabella **non sono allo stesso punto di lavoro**, e non l'ho aggiustato: il punto di lavoro è della **fase 9**. Il tratto della codifica regge lo stesso, perché in hardware il tempo dipende pochissimo dal bitrate |
| ⚠ **il prodotto INTERO non è stato acceso** | ho misurato il codificatore **isolato**, chiamandolo da fuori (`CODER.md` §3.6). ⛔ Non ho provato una sessione vera con cattura di Mutter: ci vuole il palco, ed è la corsia E |
| ⚠ **`03-b15-movimento.py` non rigirato** (B4) | fuori perimetro. ⭐ Ma il controllo che quel banco fa — chiave chiesta ⇒ chiave vera coi parameter set davanti — **l'ho innestato dentro il mio**, e passa. ⇒ Il rischio residuo è che `03-b15` guardi qualcosa che io non guardo |
| ⚠ **quale scheda compone davvero il desktop** | ho scelto `renderD128` anche perché *«è quella che compone il desktop»*: `[?]` **l'ho dedotto** dal fatto che è l'iGPU sulla 00:02.0, **non l'ho misurato** guardando Mutter. Se fosse l'AMD, la ragione (3) cade — le altre due no |
| ⚠ **la profondità: 8 bit promossi a 10** | invariata e sempre dichiarata. L'hardware non la cambia |
| ⚠ **`renderD129`: si potrebbe salvare?** | non provato: allineare la tela a un multiplo di 64 (1920×1088) toglierebbe il rifiuto ma cambierebbe la tela concessa, cioè `RCP.md` §4.5. **Non è una cosa da decidere qui** |

---

## 11. Che cosa chiedo al coordinatore

1. ⛔⛔ **B7 — i due file fuori perimetro**, e senza questi **il lavoro non si vede**: il prodotto
   continuerà a negoziare AV1 e il codificatore in hardware **non verrà mai aperto**.
   `banchi/02-pagina-sonda-codec.py:121` (togliere `keyint=1` **e** aggiungere il controllo del
   `profile_idc` letto dai byte) e `src/pagina.html:497-506` (reincollare le due `dati:`).
   ⭐ Il caso è al §7, riprodotto tre volte. **Il protocollo non va toccato.**
2. ⚠ **`banchi/03-b15-movimento.py` da rigirare** contro la copia nuova (B4), da chi ce l'ha in
   perimetro.
3. ⚠ **La copia è pronta per la corsia E**: `/srv/src/03-B-src/src/remotix`,
   `7a5ee61d13ef010f2f36eda9fcf90df8bb1d7552bef665fb3b2daac4b16ec56f`. ⛔ Ma **finché il punto 1 non
   è fatto, E misurerebbe ancora AV1 in software** — la corsia B senza il punto 1 è invisibile
   all'anello.
4. ⭐ **Il pezzo nuovo trovato per la fase 8**: la conversione BGRx→P010 in software, **5,65 ms**,
   che con l'1,44 del caricamento fa **7,1 ms su 9,7**. È il candidato della copia zero, e adesso ha
   un numero.

⛔ **Non ho committato niente**, non ho toccato nessun `.md` fuori da questo, e i file del deposito
nel mio perimetro hanno le sha256 di partenza.

---
---

# APPENDICE — IL TRAVASO NEL DEPOSITO

*14 agosto 2026, notte. Aggiunta dopo il messaggio del coordinatore con i numeri dell'anello
(corsia E). ⭐ **Il travaso è FATTO e VERIFICATO su una sessione vera.***

---

## A0. In una riga

**I quattro file sono nel deposito**, il deposito **compila** (gemelli `rcp` compresi), e un
prodotto **costruito dal deposito** ha aperto una **sessione vera** in cui — nello **stesso giro** —
il codec negoziato è **`hevc`**, il nodo **`/dev/dri/renderD128`** è aperto **in hardware**, e da lì
è **uscito un fotogramma** con `hev1.2.4.L120.B0` letto **dal flusso**. ⛔ Nessun ripiego dichiarato.
Le porte protette sono le stesse prima e dopo.

---

## A1. Che cosa ho traspostato, e da dove

⛔ **Non ho ricopiato "quel che credevo di avere": ho verificato che la sorgente del travaso fosse
esattamente quella che l'anello ha misurato.** La copia sul server era ancora intatta —
`remotix` = `7a5ee61d…`, cioè il binario dei tre giri di E — e i quattro sorgenti avevano le stesse
sha256 della mia copia di lavoro. Solo allora ho copiato.

| file | sha256 (identica su copia, server e adesso deposito) |
|---|---|
| `src/codificatore.c` | `dcc7ed3ad4927514e05c496c13d26ec7cb9d9acb92d7e2f37a9114065dd60e23` |
| `src/codificatore.h` | `7bc74545753c801707b0186357dacbc04bb88238b6ac142bb6612d548e27692c` |
| `src/figlio.c` | `5b61b12200c92b1de32ce8d58c8e4e8d1b70c22376276445a5b90495eb9dc268` |
| `src/Makefile` | `69577003bec70d87f5eca2a50ea88a8d13251348d8e78f1a9e6ac643324784a8` |

⛔ **`git status src/` dice quattro file e basta.** ⭐ **`src/pagina.html` non è stata toccata**
(non compare fra i modificati), e i tre **gemelli** `rcp.c` · `rcp.h` · `autenticazione.c` sono
`cmp`-identici alle copie di `banchi/rcp/`.

⚠ **La base non si era mossa sotto di me**: prima di copiare ho verificato che i quattro file del
deposito avessero ancora le sha256 da cui ero partito (`02babbc4…` `bb3424a5…` `ecb60d93…`
`c25a1445…`). Se si fossero mosse, mi sarei fermato.

---

## A2. La costruzione — ⛔ dal DEPOSITO, e non nell'albero del prodotto di casa

Ho estratto `src/` + `banchi/rcp/` del deposito in una copia **nuova**,
`/srv/src/03-B-verifica/`, e l'ho costruita lì. ⛔ **Non ho ricostruito
`/media/REMOTIX/src/remotix/`**, che è l'albero dietro la **7448** — una porta protetta.

```
OK  rcp.c            identico a …/banchi/rcp/rcp.c            (8cdc80c64ada2eea…)
OK  rcp.h            identico a …/banchi/rcp/rcp.h            (77c562f9c0b14737…)
OK  autenticazione.c identico a …/banchi/rcp/autenticazione.c (86451cd1c8bb6367…)
OK  make e' uscito 0
OK  ⭐ costruito: /srv/src/03-B-verifica/src/remotix
```

- **nessun errore, nessun avviso** del compilatore;
- binario del deposito: `283571055af77243e58364848b1653d2726b7dbe4621933d8fb49e083a485d1e`.

⚠ Non coincide con `7a5ee61d…` per **due** ragioni, tutte e due note e nessuna preoccupante: la
costruzione **non è riproducibile bit per bit**, e la `pagina.html` del deposito è quella **curata**,
diversa da quella della mia copia.

---

## A3. Il codificatore del deposito, provato da fuori

Ho ricompilato il mio banco isolato contro il **`codificatore.o` costruito dal deposito**. ⛔ È una
prova di **correttezza**, non di tempo — ma il banco ha comunque dichiarato la scena e verificato di
essere solo (carico 0,05 · 13 vicini, **nessuno consuma**).

| | copia misurata da E | ⭐ **deposito** |
|---|---|---|
| `hevc_vaapi` renderD128, cammino seriale | 9,73 / 9,77 ms | **9,80 ms** |
| fotogrammi consegnati | 120 su 120 | **120 su 120** |
| **B4** chiave su richiesta | SI | **SI** |
| riordina · trattenuto | no · no | **no · no** |
| controllo negativo «nodo non dichiarato» | rifiuta | **rifiuta** |
| controllo negativo «EncSlice piena su renderD128» | rifiuta, e dice `[1,8]` | **rifiuta, e dice `[1,8]`** |
| ⚠ `renderD129` (AMD) | ⛔ 0 su 120 | ⛔ **0 su 120** |

⇒ **Il travaso non ha cambiato niente**, e l'unico rosso è quello **già dichiarato e atteso**
(§1.2): l'AMD che consegna 1088 righe. **Non è una regressione.**

---

## A4. ⭐⭐ LA CONDIZIONE 2 — LA SESSIONE VERA

### ⛔ Perché NON ho usato l'anello, e perché è la scelta giusta

Ho provato per primo `03-b17-ritardo.py --misura` contro la mia copia. **Si è rifiutato**, ed
aveva ragione:

> `⛔ NON SONO SOLO — mi RIFIUTO di misurare un tempo: CHUWI: un vicino mangia CPU: chrome (pid
> 571048) al 30.0 % · chrome (pid 567382) al 20.0 %`

⚠ **Ho guardato di chi fossero prima di dare la colpa a qualcuno**: `--ozone-platform=wayland`,
vivi da 23 minuti ⇒ è **il Chrome dell'utente sul suo desktop**. Non miei, e non si toccano.

⇒ ⭐ **Ma la mia non è una misura di tempo: è un sì/no** — §0-bis, *«la correttezza non dipende da
quanto la macchina è carica»*. L'anello è lo strumento della famiglia sbagliata. Ho scritto un
apri-sessione che **riusa il `Palco` già certificato** di quel banco (`CODER.md` §4.1 — si dipende,
non si riscrive) e che **non misura niente**.

### Il giro, e la regola doppia che vale contro me stesso

⛔ **Ho preteso TRE fatti, non uno**, perché *un descrittore aperto non dice che i fotogrammi ci
passino* — è la regola che avevo proposto io, e qui l'ho puntata sul mio lavoro.

**Scena**: prodotto **costruito dal deposito** sulla **7626** (ponte 7622, lavoro e certificati
miei); Chrome su Xvfb `:89`, ⭐ **senza `--disable-gpu`** (bandiere stampate nel giro); utente
`nicfio`, parola da file 0600, **mai da argv**. ⛔ Il registro è stato letto **solo dai 2 145 byte in
poi** — non dall'inizio, che è la trappola già pagata.

```
21:20:49.410 rcp     negoziato video.codec=hevc video.profondita=8 audio.codec=opus
21:20:49.584 video   aperto: HEVC 10 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 ·
                     Intel iHD driver for Intel(R) Gen Graphics - 25.2.3 () · ⚠ EncSliceLP,
                     bassa potenza — NON e' la codifica piena) · 1920x1080 · QP costante
21:20:49.603 figlio  ⭐ PRIMO fotogramma codificato: codec 1, 3334 byte, CHIAVE,
                     «hev1.2.4.L120.B0», profondita' nel flusso 10, livello 120,
                     promozione 8→10 SI (dichiarata), conversione 7177 us,
                     caricamento sulla GPU 3882 us, codifica 7645 us
```

| | |
|---|---|
| **1/3** | ⭐ il codec negoziato è **`hevc`** — cioè **il codec 1**, e la cura B7 funziona da capo a fondo |
| **2/3** | ⭐ `/dev/dri/renderD128` aperto **IN HARDWARE**, col **fornitore VA** scritto accanto |
| **3/3** | ⭐ e da lì è **uscito un fotogramma**: `hev1.2.4.L120.B0`, 10 bit **letti dal flusso**, chiave vera |

⛔ **E i tre contatori del silenzio sono tutti a zero**: `RIPIEGO DICHIARATO` **0** · `ha trattenuto
il fotogramma` **0** · `non ha consegnato` **0**. ⇒ Il software **non** ha preso il posto
dell'hardware, e nessun fotogramma è rimasto in canna.

### ⭐ E una verifica in più, che costa zero e chiude il cerchio su B7

Le sonde HEVC dentro `src/pagina.html` del deposito, rilette **nei byte**:

```
hevc-8   114 byte  profile_idc = 1   ⭐ Main
hevc-10  116 byte  profile_idc = 2   ⭐ Main10
```

⇒ **La Rext è sparita.** È esattamente la cura che avevo chiesto al §7, ed è la ragione per cui
adesso il `CIAO` porta `hevc` e il server sceglie 1 invece di 2.

---

## ⛔ A5. CHE COSA NON HA FUNZIONATO

| | |
|---|---|
| ⛔ **la scena non si è accesa** | il mio gancio a `03-b17-accendi.sh scena-avvia` è fallito 6 tentativi su 6 ⇒ i contatori **della pagina** sono a zero (`consegnati: 0, dipinti: 0`). ⚠ **Non inficia la condizione 2**, che si legge nel registro **del prodotto** e riguarda la codifica, non il disegno — e il fotogramma codificato c'è. ⇒ Ma va detto: **quel giro non prova che il client dipinga**; a provarlo sono i 799 fotogrammi di E e i 120 su 120 del §6 |
| ⛔ **l'anello si è rifiutato** | e correttamente: il Chrome dell'utente ciclava. ⇒ Cambiato strumento, non forzata la misura |
| ⛔ **`03-b17-accendi.sh spegni` non ha morso** | ha lasciato vivi prodotto, figlio e ponte. Li ho chiusi **per PID esplicito**, uno per uno, dopo aver letto la riga di comando di ciascuno ⇒ ⛔ **nessun `pkill` a tappeto vicino a tre porte protette** |
| ⚠ **`sshpw.py` non eleva il `sudo`** | i miei `kill` via quello strumento sono usciti 0 **senza uccidere niente** — «ha risposto» e «ha fatto» avevano lo stesso aspetto. Me ne sono accorto **ricontando i processi**, non fidandomi del codice d'uscita |
| ⚠ **il mio apri-sessione è nato rotto due volte** | leggeva la lunghezza del registro e il conto delle porte dallo stdout di `ssh`, dove ci sono anche la richiesta della parola e il rumore di `tput`. Curato pescando il numero con una regex invece di presumere che l'output fosse solo il numero |

---

## ⏳ A6. CHE COSA RESTA `[?]` dopo il travaso

| | |
|---|---|
| ⚠ **il giro della condizione 2 non ha dipinto** | zero fotogrammi **alla pagina**, per la scena spenta. La catena fino al **client** è provata altrove (E: 799 fotogrammi, 30,18 fps; io: 120 su 120 nel `VideoDecoder`), **non in questo giro** |
| ⚠ **il deposito non è stato provato sull'ANELLO** | E ha misurato il binario della **mia copia**, non quello del deposito. I sorgenti sono **identici byte per byte** e il codificatore si comporta identico (§A3) — ma la sottrazione dei cinque tratti resta quella di E |
| ⚠ **`03-b17` e `03-b19` scadono** | `src/codificatore.c` è cambiato. ⛔ **Non ho toccato il catalogo**, come da istruzione: le rigira il coordinatore |
| ⚠ **il disegno a 25,1 ms** | il collo di bottiglia si è spostato di nuovo, adesso è il disegno lato client. **Non è mio**, ma è il numero che tiene il totale sopra AV1 software |
| ⚠ **tutto il resto delle `[?]` di §10** | invariato: qualità della LP non misurata, QP 26 ≠ CRF 20, `renderD129` inservibile, quale scheda componga il desktop |

---

## A7. Lo stato in cui lascio le cose

| | |
|---|---|
| **deposito** | 4 file modificati, `src/pagina.html` **intatta**, gemelli `rcp` identici. ⛔ **Non committato** |
| **porte sul server** | ⭐ `7448 · 7501 · 7561` e **nient'altro** — contate all'inizio, durante e alla fine. Le mie 7622/7626/7627 sono **spente** |
| **copie sul server** | `/srv/src/03-B-src/` (quella misurata da E) e `/srv/src/03-B-verifica/` (quella del deposito) restano, spente, ispezionabili |
| **CHUWI** | Xvfb e profili dei miei giri chiusi e cancellati a fine giro; `/tmp` a ~1,4 G liberi |

⇒ ⭐ **Domattina l'utente giudicherebbe il prodotto SENZA il freno tirato**: negozia HEVC e codifica
in hardware. ⚠ E se qualcosa dovesse andare storto, il ritorno indietro è **`git checkout -- src/`**
su quattro file, e nient'altro.

---
---

# APPENDICE B — LA VERIFICA SULLA 7571, QUELLA CHE L'UTENTE GUARDERÀ

*14 agosto 2026, 00:25-00:55. Su richiesta del coordinatore, che ha acceso la 7571 col mio binario
perché l'utente possa confrontare le due configurazioni senza toccare la sua 7561.*

## B0. ⭐⭐ QUATTRO SU QUATTRO — e il quarto è quello che mancava

**Sessione vera contro `https://192.168.0.2:7571/`**, Chrome su Xvfb `:90` ⭐ **senza
`--disable-gpu`**, utente `nicfio`, parola da file 0600 mai da argv. Registro letto **solo dal
taglio in poi**.

| | |
|---|---|
| **1/4** | ⭐ `negoziato video.codec=hevc video.profondita=8 audio.codec=opus` — **codec 1** |
| **2/4** | ⭐ `aperto: HEVC 10 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD driver … · ⚠ EncSliceLP, bassa potenza)` |
| **3/4** | ⭐ `PRIMO fotogramma codificato: codec 1, 3334 byte, CHIAVE, «hev1.2.4.L120.B0», profondità nel flusso 10` |
| ⭐⭐ **4/4** | **IL CLIENT DIPINGE**: **1 047 fotogrammi dipinti**, e la catena arriva al vetro |

### ⭐ E il quarto porta un numero che si legge da sé

```
t+ 4s  consegnati  567 · dipinti  567 · scartati_ordine 0 · buchi 0
t+ 8s  consegnati  687 · dipinti  687 · scartati_ordine 0 · buchi 0
t+12s  consegnati  807 · dipinti  807 · scartati_ordine 0 · buchi 0
t+16s  consegnati  927 · dipinti  927 · scartati_ordine 0 · buchi 0
t+20s  consegnati 1047 · dipinti 1047 · scartati_ordine 0 · buchi 0
```

⭐ **+120 ogni 4 secondi = 30 fotogrammi al secondo esatti**, e **`consegnati == dipinti` a ogni
lettura**: ⛔ **non ne cade nemmeno uno**. Zero fuori ordine, zero buchi.

⚠ **E il 30 non è un numero mio**: è lo stesso **30,18 fps** che la corsia E ha misurato sull'anello.
Due banchi diversi, due scene diverse, la stessa cadenza.

⛔ **Che cosa questo NON è**: non è una misura di ritardo. È un conteggio di fotogrammi — famiglia
**correttezza** — e non ha preso nessuna finestra esclusiva. Il numero del ritardo resta quello di E.

## B1. ⛔ Che cosa NON ha funzionato, e sono tutte cose MIE

*Tre giri, e i primi due sono usciti storti per difetti del banco, non del prodotto.*

| | |
|---|---|
| ⛔⛔ **«il registro non nomina nessun monitor» — di un registro che lo nominava** | il mio estrattore passava le virgolette a caporale dentro il comando `ssh`, e `«»` non sopravvive al giro `ssh → shell → grep`. ⇒ Ho concluso che il prodotto non dicesse una cosa che **diceva**: `monitor «Meta-2»`. ⭐ Curato spostando il filtro **in Python**, dopo il trasporto |
| ⛔ **e poi la regex era in una stringa RAW** | `r"«"` **non è** «: in una stringa raw resta il testo `«`. Secondo giro perso allo stesso punto, per una ragione diversa |
| ⛔ **«nessuna apertura in hardware» al secondo giro** | ⚠ ed era **giusto che mancasse**: il palco **sopravvive al distacco** (invariante **I4**), quindi alla seconda connessione il codificatore **non si riapre** e le sue righe stanno *prima* del taglio. ⇒ Curato allargando la finestra — ⛔ **ma DICENDOLO**, con una riga che scrive «ho guardato più indietro». Un banco che allarga la finestra in silenzio è un banco che trova sempre quel che cerca |
| ⚠ **la scena si è accesa ma non ha stampato un conteggio** | e lo script l'ha detto: *«la scena è viva ma non ha stampato un conteggio: NON dico che sta disegnando — "vivo" non è "disegna"»*. ⭐ **A dire che disegnava sono stati i 1 047 fotogrammi della pagina**, non il fatto che il processo esistesse |

⇒ ⭐ **Zero volte il banco ha sbagliato a favore del prodotto**: tutti e tre i difetti facevano
apparire il prodotto **peggiore** di quel che è.

## B2. Che cosa resta `[?]`

| | |
|---|---|
| ⚠ **la scena è SINTETICA** | è la barra in movimento dello step 2, non il desktop dell'utente. ⇒ I 1 047 fotogrammi dicono che **la catena regge a 30/s**, non che il *suo* desktop sarà fluido: quello lo dirà lui |
| ⚠ **`chiavi_chieste: 0`** | in venti secondi nessuna chiave è stata richiesta ⇒ **B4 non è stato esercitato in questo giro**. È provato altrove (§5 e §A3), non qui |
| ⚠ **il disegno a ~25 ms** | il collo di bottiglia lato client, misurato da E. Non tocca questi conteggi, ma è il motivo per cui il totale resta sopra AV1 software |
| ⚠ **il binario della 7571 è COPIATO, non ricostruito lì** | come il coordinatore ha dichiarato. ⭐ È lo stesso binario che questo giro ha esercitato per davvero — quindi «copiato» qui non è una `[?]`: è un fatto verificato dall'uso |

## B3. Come lascio le cose

| | |
|---|---|
| ⭐ **7571** | **viva e intatta** (pid 410731/410737) — non l'ho accesa io e non l'ho spenta |
| ⛔ **7561** | **mai toccata**, né lei né `/media/REMOTIX/src/remotix` |
| ⛔ **il `--figlio-interno` di `02-montaggio`** | **non ucciso**: è suo, come detto |
| **la mia scena** | **spenta** a fine giro (`scena-ferma`): non lascio una finestra di prova sul monitor che l'utente guarderà |
| **porte** | `7448 · 7501 · 7561 · 7571` — contate prima, durante e dopo. Nessuna mia |
| **CHUWI** | Xvfb `:90` e profili chiusi e cancellati dal giro stesso |

⇒ ⭐ **La 7571 non mente**: dice HEVC in hardware, e fa HEVC in hardware, fino al pixel dipinto.
