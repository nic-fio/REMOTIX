# P2.3 — Il prodotto della codifica: HEVC e AV1, in software

*Terzo anello della fase 2. Prodotto scritto il 12 agosto 2026, contro il banco di
[`F2-3-codifica.md`](F2-3-codifica.md), che esisteva già ed era certificato 30 su 30 su due
macchine.*

⛔ **Questo giro ha scritto prodotto**: `src/codificatore.c` (1 375 righe) e `src/codificatore.h`
(322). Il banco è stato **esteso** per poterlo puntare addosso, e **ri-certificato** — su quattro
organi invece di due.

⚠ **Porte**: la 7513 assegnata a F2.3 resta **non usata**, come nel giro del banco: qui non si
ascolta e non si parla con nessuno. **7448 e 7501**: contate su CHUWI **prima** e **dopo**, `0` e
`0` — vivono dentro NIC-OS, e ⛔ **NIC-OS non è stato toccato**: nessun `ssh`, nessun `enter.sh`,
nessuna redirezione attorno a essi.

---

## 1. Che cosa fa, in una riga per ciascuno

| | |
|---|---|
| **`src/codificatore.h`** | l'interfaccia, e la **ragione** di ogni decisione: i due codec, la forma dei byte, la promozione a 10 bit, i due testimoni di E2 |
| **`src/codificatore.c`** | libavcodec con il componente **chiesto per nome**; la conversione BGRx→YUV con la matrice **imposta**; il lettore di **SPS** e di **sequence header OBU** che rilegge quel che ha appena prodotto; il tetto dei 16 MiB; il cambio di tela |
| **`banchi/02-codifica-costruisci.sh`** | compila `codificatore.c` **da solo**, senza toccare `src/Makefile` |
| **`banchi/02-codifica-prova.c`** | il guscio con cui il **banco punta sul prodotto** invece che su `ffmpeg` |
| **`banchi/02-codifica-obu.py`** | la forma del flusso **AV1**, letta sui byte — il gemello di `02-codifica-nal.py` |
| **`banchi/02-codifica-lancia.sh`** | ⭐ due leve nuove: `CODIFICATORE=ffmpeg\|prodotto` e `CODEC=hevc\|av1`, più il **passo 8** |
| **`banchi/02-codifica-guasti.py`** | i guasti sono **quattro**: A e B nel banco (già c'erano), ⭐ **C e D nel prodotto** |

⛔ **Non toccati**: `src/Makefile`, `src/main.c`, `RCP.md`, `banchi/02-codifica-nal.py` (impronta
`616dc259…` **invariata**, ed è la prova che il guasto B certifica ancora quel che certificava),
`banchi/02-codifica-immagine.py`. Nessun comando `git` che scrive.

---

## 2. ⛔ Che libreria per ciascun codec, e con che ragione

### 2.1 HEVC — **`libx265`**, e la ragione è che le altre non sono in software

`[M]` 12 agosto 2026, `ffmpeg -encoders` su Trixie: i codificatori HEVC sono **cinque**, e
**quattro sono in hardware** — `hevc_vaapi`, `hevc_qsv`, `hevc_nvenc`, `hevc_vulkan`. Resta
`libx265`, che è anche quello contro cui il banco è stato certificato.

⛔ **Il modo di chiedere conta quanto il nome**: `avcodec_find_encoder_by_name("libx265")`, mai
`avcodec_find_encoder(AV_CODEC_ID_HEVC)`. Il secondo lascia scegliere a libavcodec fra quei cinque,
e ⚠ **la fase 8 entrerebbe di soppiatto nella fase 2** — cioè non si saprebbe più quale dei due
pezzi sbaglia, che è la ragione per cui `PIANO.md` dice *«in software, di proposito»*.

### 2.2 AV1 — **`libsvtav1`**, e la ragione è un numero

I candidati in software nei pacchetti di Trixie sono tre. `[M]` 12 agosto 2026, stessa scena
1920×1080 a 10 bit, **tutti fotogrammi chiave** (il caso peggiore):

| componente | tempo per fotogramma | |
|---|---|---|
| ⭐ **`libsvtav1`** | **99 ms** (preset 12) · **162** (preset 10) · **390** (preset 8) · 4 906 (preset 5) | scelto |
| `librav1e` | **2 347 ms** per **un** fotogramma | **15×** più lento del preset 10 |
| `libaom-av1` | ⛔ **non ha finito UN fotogramma in 95 s** | fuori scala |
| *(confronto)* `libx265` | 306–319 ms, preset `medium` | |

⛔ **E il numero non è un dettaglio di comodo**: `DECISIONI.md` §1.13 lascia aperta esattamente
questa `[?]` — *«il ritmo di AV1 in software è la domanda che decide se il ripiego è **usabile** o
solo **esistente**»*. Con `libaom` il ripiego sarebbe **solo esistente**.

⚠ **E il numero va letto per quel che è**: 99–390 ms per un fotogramma chiave a 1080p sono
**da 2 a 8 volte il tetto dei 50 ms** di `SPECIFICHE.md` §3.2. Non morde nella fase 2 — un
fotogramma fermo — e ⛔ **non si è misurato niente sul regime** (`CODER.md` §3.5: un campione
all'avvio non dice niente del regime, e qui non c'è nemmeno un regime). Resta la `[?]` n. 3 di §8.

**Preset scelto: 10**, che è quello di difetto dell'involucro di ffmpeg. ⚠ È un difetto **non
chiesto che si tiene**, quindi si dichiara qui invece di ereditarlo in silenzio; il punto di lavoro
fra qualità e tempo è della fase 9, dove ci sarà un regime su cui sceglierlo.

---

## 3. ⛔ Come si verifica che il componente abbia obbedito — e i testimoni sono due

`CODER.md` §3.9, e la riga che v1 aveva scritto dopo averla pagata
(`v1/remotix-c/src/codificatore.c:550-566`): *«chiesto per nome, nessun ripiego»*.

### 3.1 Primo testimone: il contesto, riletto **dopo** l'apertura

`apri_contesto()` non presume: rilegge `AVCodecContext` e **fallisce dicendo perché** se una di
queste cinque non torna — nome del componente aperto, identità del codec, formato dei pixel,
`GLOBAL_HEADER` spento, `max_b_frames == 0`.

### 3.2 ⭐ Secondo testimone: **i byte**, e non dipende dal primo

`codificatore.c` legge l'**SPS di HEVC** (togliendo gli *emulation prevention byte*, con Exp-Golomb
sul `profile_tier_level`) e la **sequence header OBU di AV1**, e ne ricava profondità, profilo,
livello, tier, misura e formato di croma. Se il flusso dice una profondità diversa da quella
chiesta, ⛔ **il fotogramma non parte**.

**Che non sia una deduzione lo dice un terzo, indipendente**: `ffprobe`, che legge gli stessi campi
dallo stesso flusso, dà gli **stessi numeri** `[M]` — livello **255** in lossless, **120** a CRF 20,
**93** a 1280×720, `seq_level_idx` **8** su AV1.

⛔ **E perché il lettore di byte non è un lusso**: `[M]` 12 agosto 2026, **SVT-AV1 non scrive
nessuna confessione nel flusso**. x265 ci mette un `PREFIX_SEI` di user data con `bitdepth=`,
`annexb`, `repeat-headers`, `bframes=` — ed è su quello che il banco fondava la verifica di E2. Su
AV1 quella stringa **non c'è**: senza il lettore nostro, i testimoni indipendenti sarebbero **uno**,
e il banco lo dice a voce alta (`⛔ QUESTO GIRO NON CERTIFICA E2 SU AV1`) quando gira con
`CODIFICATORE=ffmpeg`.

### 3.3 ⛔ Il modo di disobbedire che è stato **misurato**, non immaginato

> `[M]` **libsvtav1 ignora un'opzione che non conosce e continua, uscendo 0.**
> `-svtav1-params lossless=1` stampa *«Error parsing option»* e **codifica lo stesso**.
> ⇒ Un'opzione chiesta e non applicata ha lo **stesso aspetto** di un'opzione applicata.

> `[M]` **`crf=0` su libsvtav1 vuol dire «non chiesto»**: è il valore di difetto dell'opzione,
> l'involucro lo scarta, e il flusso esce a **CRF 35** senza che nessuno lo dica. È un valore
> sentinella implicito dentro una singola opzione — la forma **E2** in miniatura.
> ⇒ Il prodotto **rifiuta** `crf < 1` su AV1, con la ragione scritta nel messaggio.

### 3.4 Il terzo testimone, che vale per tutt'e due i codec: **`dts == pts`**

Un codificatore che riordina lo dichiara lì, qualunque cosa abbia fatto delle opzioni. E se
trattiene il fotogramma (`EAGAIN`), il prodotto lo **conta e lo scrive nel registro** invece di
fingere: *«ha trattenuto il fotogramma invece di consegnarlo: è un fotogramma di RITARDO contro i
50 ms»*. ⭐ Verificato che funzioni: col guasto **F2.3-D** innestato quella riga compare a **ogni**
fotogramma.

---

## 4. ⛔ `bframes` e `open-gop`: che cosa si è deciso, e perché

`[M]` il banco aveva misurato che **x265 fa `bframes=4` e `open-gop` di suo**, e che **SVT-AV1 dice
«pred struct: random access»** — tre difetti che nessuno aveva chiesto e che comprano compressione
**vendendo risposta**.

| manopola | deciso | perché |
|---|---|---|
| ⛔ **`bframes=0`** | **vietati** | ogni fotogramma B costringe ad attendere il successivo: **un fotogramma di ritardo in più** contro i **50 ms** di `SPECIFICHE.md` §3.2, e `CODER.md` §1-bis dice che *il ritardo pesa più dei fotogrammi*. v1 li vietava a mano con la stessa ragione (`codificatore.c:241`), e la ragione **non dipende dal codec** |
| ⛔ **`open-gop=0`** | **chiuso** | non è (solo) latenza: un GOP aperto ha figure che dipendono da **prima** della chiave ⇒ ⛔ **quella chiave non si decodifica da sola**, e `RCP.md` §5.2 pretende una chiave **vera** — *«portare con sé tutto quel che serve a decodificarla da sola»*. Con `open-gop` la riga di RCP sarebbe violata **da un difetto di x265**, non da una nostra scelta |
| ⛔ **`repeat-headers=1`** | **acceso** | i parameter set davanti a **ogni** chiave. È la metà che si dimentica, e morde in fase 3 |
| ⚠ **`rc-lookahead=0`, `frame-threads=1`** | **spenti** | il ritardo non lo fanno solo i fotogrammi B: il lookahead e i fili di fotogramma tengono immagini in canna. ⚠ **Il prezzo è in compressione, e si dichiara**: `[M]` a CRF 20 il prodotto fa **28 957 byte** dove ffmpeg col preset intero ne fa **21 569** — il **34 % in più**, comprato in risposta |
| ⛔ **AV1 `pred-struct=1`** | **bassa latenza** | l'equivalente AV1 dei fotogrammi B |
| ⚠ **`info=1` di x265** | **acceso**, e dichiarato | è la confessione che il banco legge. Costa `[M]` ~2,2 KB per chiave (il 2,3 % di una chiave 1080p lossless). ⭐ Spegnerlo è una decisione della **fase 9**, e quando si spegnerà il testimone che resta è il **lettore di SPS**, che non costa un byte sul filo |
| ⚠ **chiavi periodiche** | **nessuna** (`keyint=-1`) | `RCP.md` §5.2: le chiavi **si chiedono** (`RICHIEDI_CHIAVE`), e mandarne a orologio su una linea cattiva è *«la spirale»* che quel paragrafo vieta. Il campo `chiavi_ogni` esiste, e vale 0 in fase 2 |

⭐ **E una cosa che si è imparata innestando il guasto D**: `[M]` x265 **non si apre** con
`rc-lookahead=0` e `bframes=4` insieme (*«Lookahead depth must be greater than the max consecutive
bframe count»*). ⇒ **Le due manopole della bassa latenza sono legate**, e chi ne tocca una domani
deve saperlo prima e non scoprirlo dall'errore.

⭐ **E una seconda, sull'ordine**: le opzioni di x265 si applicano **in ordine, e l'ultima vince**.
La prima stesura del guasto D scriveva `bframes=4` nel punto sbagliato e il `rc-lookahead=0` che
veniva **dopo** restava in vigore ⇒ **il guasto non innestava l'organo che doveva innestare**.

---

## 5. ⛔ Le altre decisioni, con la ragione accanto

### 5.1 La forma dei byte — **Annex-B, e nessuna `description`** (D1, invariata)

`AV_CODEC_FLAG_GLOBAL_HEADER` **non si accende**, e ⛔ **non ci si fida di non averlo acceso**:
`apri_contesto()` verifica che sia spento, e prima di consegnare ogni fotogramma
`forma_va_bene()` cammina sui NAL e pretende **VPS+SPS+PPS davanti alla chiave**. Se non ci sono,
il fotogramma **non parte** e il registro dice perché.

⭐ **Che questa guardia non sia decorativa lo dimostra il guasto C** (§7): con `repeat-headers=0`
x265 toglie i parameter set **anche dalla prima chiave** — e a diventare rosso è **la guardia del
prodotto**, non il passo 6 del banco. ⇒ **Il difetto che v1 aveva comprato oggi non arriverebbe sul
filo.**

Per **AV1** l'analogo è la **sequence header OBU** davanti a ogni fotogramma chiave, verificata allo
stesso modo — `[M]` 3 chiavi, 3 sequenze.

### 5.2 ⛔ Il colore: **BT.709, range limitato**, e scritto nel flusso

F2.2 ha misurato che **Mutter non dichiara niente** — range, matrice, trasferimento e primari sono
quattro `UNKNOWN` — e che alla cattura i pixel sono **RGB**: *«la matrice la sceglie F2.3»*. Scelta:

- **709** perché è quel che un desktop sRGB si aspetta ed è il difetto che i due motori applicano
  quando il flusso tace: scrivere una cosa diversa dal difetto **senza necessità** vorrebbe dire
  scommettere che tutti leggano la VUI;
- **range limitato** perché è il difetto che ogni decodificatore azzecca, ⛔ **e qui non costa
  precisione**: 8 bit pieni sono 256 livelli, e l'intervallo limitato a 10 bit ne ha **877**.

⛔ **E si scrive nel flusso, non solo nel nostro registro**: F2.5 converte YUV→RGB per la tela e
F2.6 confronta i pixel. Due matrici diverse ai due capi **misurerebbero la matrice**.

⭐ **La prova che la matrice è quella che diciamo** è il passo **8a** del banco, ed è byte per byte:
la nostra conversione contro quella di `ffmpeg` con le **stesse quattro cose dichiarate** →
`[M]` **0 campioni diversi su 6 220 800**.

### 5.3 ⚠ La promozione a 10 bit — dichiarata, non subita

`[M]` F2.2: la cattura dà **8 bit veri**. Main10 da lì sono **otto bit promossi**, e l'etichetta
continuerà a dire *«Main 10»* per tutta la catena. ⛔ Il prodotto lo **scrive nel registro alla
prima codifica** e lo espone in `confessione.promozione_8_a_10` — `DECISIONI.md` §2.7 riga 2: *un
ripiego silenzioso resta vietato anche quando la colpa non è nostra*.

### 5.4 Il tetto dei 16 MiB — `RCP.md` §6.2

Se il pacchetto supera il tetto: **si ricodifica** a qualità inferiore (lossless → CRF 24, poi +6),
fino a **tre** tentativi, **si scrive nel registro**, e ⛔ **non si spedisce mai**. Se nemmeno dopo
tre tentativi ci sta, il fotogramma **non parte**.

⭐ **E il percorso è stato eseguito, non solo scritto**: con una copia del sorgente col tetto
abbassato a 30 KiB `[M]` — *«fotogramma di 96 235 byte, oltre i 30 720 del tetto: si RICODIFICA»* →
**24 868 byte**, consegnato. ⚠ Un percorso che non gira mai è codice che nessuno ha provato.

### 5.5 Il cambio di tela — `RCP.md` §5.2

`codificatore_ridimensiona()` **riapre davvero** (un codificatore aperto a una misura e alimentato a
un'altra non protesta: taglia o riempie) e il primo fotogramma dopo è una **chiave vera**.
`[M]` provato: `1920×1080 → 1280×720` dà **2 gruppi di parameter set su 2 chiavi**, e il secondo SPS
dichiara `1280×720`, livello **93**.

### 5.6 ⚠ Le cose che il prodotto **rifiuta** invece di arrangiarsi

| si chiede | risposta |
|---|---|
| un componente che non c'è | *«non se ne prende un altro, si fallisce dicendolo»* |
| `libx264` per HEVC | *«non è un codificatore HEVC»* |
| AV1 senza perdita | ⛔ *«SVT-AV1 2.3.0 non ha un modo senza perdita, e non lo si finge. Il regime più vicino è CRF 1 [M]»* |
| AV1 a `crf 0` | ⛔ *«lo zero vale «non chiesto» e il flusso esce a CRF 35 in silenzio [M]»* |
| 8 bit con un ingresso a 10 | *«non si mescolano»* — ⚠ il sintomo sarebbe **la memoria sfondata**, non un'immagine brutta |
| una misura dispari | *«4:2:0 vuole misure pari»* |

---

## 6. ⭐ L'esito del banco contro il mio codice

⛔ **Il banco è stato puntato sul prodotto, non lasciato puntato su `ffmpeg`.** Un giro verde su
`ffmpeg` certifica **ffmpeg**: è la forma **E10** di `REVIEWER.md` §2, *«una prova verde sul client
sbagliato»*, con l'imputato sbagliato.

`[M]` 12 agosto 2026, CHUWI, ffmpeg 7.1.5-0+deb13u1 — **quattro giri, tutti e quattro verdi**:

| giro | controlli | flusso giro A | bframes | livelli veri / opposto | gruppi | storpiature |
|---|---|---|---|---|---|---|
| `ffmpeg` · `hevc` *(il giro con cui il banco era certificato)* | **30 / 30** | 96 237 | ⚠ **4** | 877 / 220 | 3 | 3 |
| ⭐ **`prodotto` · `hevc`** | **36 / 36** | **96 235** | ⭐ **0** | 877 / 220 | 3 | 3 |
| ⭐ **`prodotto` · `av1`** | **29 / 29** | 138 400 | n/a | 877 / 220 | 3 | 3 |
| `ffmpeg` · `av1` | 26 / 26 | 138 211 | n/a | 877 / 220 | 3 | 3 |

⭐ **Le tre righe che dicono che il prodotto non è ffmpeg travestito**:

1. **`bframes` 4 → 0**: la decisione è **nel codice**, e la confessione di x265 la conferma;
2. **campioni diversi dopo il giro lossless: 0** — il flusso del *prodotto* torna **identico byte
   per byte**, e l'organo dei 10 bit ci regge intero (877 contro 220, 0,25 contro 1,000);
3. **passo 8**, che con `ffmpeg` non esisteva: la strada **vera**, da BGRx.

### 6.1 ⛔⛔ E il passo 8 ha trovato una cosa che nessuno dei sette poteva trovare

I passi 1-7 entrano da un'immagine **già in YCbCr a 10 bit**. La cattura non consegna quello:
consegna **BGRx a 8 bit**. Sulla strada vera, `[M]`:

| | misurato | |
|---|---|---|
| **8a** la nostra conversione contro quella di ffmpeg | **0 campioni diversi** | ⭐ la matrice è quella che diciamo |
| **8b** la promozione 8→10 | **dichiarata** | ⛔ nel registro, alla prima codifica |
| **8c** livelli distinti sulla rampa | **256**, non 877 | ⛔ otto bit, come dev'essere |
| **8c** verdetto del misuratore | ⛔ **«10-bit-veri»** | **falso verde** |
| conversione BGRx→YUV, 1920×1080 | **9,4–11,8 ms** | v1 ne misurava 12,5 a 2560×1024 in NV12 |

> ⛔⛔ **L'organo che smaschera i 10 bit finti NON sopravvive alla conversione RGB→YUV.** La
> frazione di multipli di 4 vale **0,2495** su una catena che porta **otto** bit, perché la matrice
> sparpaglia i valori — e il verdetto dice *«10-bit-veri»* di una catena a 8 bit. ⇒ Su questa strada
> l'unico organo che regge è il **conteggio dei livelli** (256 contro 877), più la **promozione
> dichiarata dal prodotto**.
>
> ⚠ Non è una scoperta nuova, è una **conferma indipendente**: `fasi/02-primo-fotogramma.md` lo
> aveva già scritto per la sonda S2 della fase 1 — *«i bit veri si misurano **alla sorgente**, o non
> si misurano»*. Qui lo dice un secondo strumento, su un'altra catena, con un numero.

### 6.2 ⚠ Che cosa questo verde **non** dimostra

- **non** che un browser lo decodifichi: il lettore indipendente è `ffmpeg`, non è Chromium. Quello
  è **F2.5**, e il telefono è **F2.6**;
- **non** niente sul ritmo né sul ritardo in regime: un fotogramma fermo, e `CODER.md` §3.5;
- **non** che la cattura consegni davvero quello che F2.2 dichiara: il sorgente qui è **costruito**;
- **non** che il tetto dei 16 MiB regga a 8K: il numero di §5.4 è stato ottenuto **abbassando il
  tetto**, non producendo un fotogramma grande davvero.

---

## 7. ⛔ Le certificazioni: due invalidate, quattro rifatte

⛔ **Ho toccato `02-codifica-lancia.sh`** (le due leve, il passo 8, i deviatoi per AV1) ⇒ **le
certificazioni F2.3-A e F2.3-B del giro del banco sono scadute**. *«Scaduta» non è «fallita»*, e non
è nemmeno «pulita»: vanno **rifatte**, e sono state rifatte.

⭐ **E ne sono state aggiunte due, perché ci sono due organi nuovi**: il prodotto esiste, e la
domanda *«questo banco sa vedere un difetto del CODIFICATORE?»* prima non si poteva porre.

`[M]` 12 agosto 2026 — **quattro organi, dodici esecuzioni**, e la marca **contata** in tutt'e due i
versi:

| organo | comando | sano | guasto | risanato |
|---|---|---|---|---|
| **F2.3-A** i 10 bit veri | `02-codifica-lancia.sh` | **0** · verde 30/30 · marca **0** | **1** · rosso 2 falliti · marca **1** | **0** · verde 30/30 · impronta `0a84abdd…` combacia |
| **F2.3-B** il rifiuto | idem | **0** · verde 30/30 · marca **0** | **1** · rosso 3/31 · marca **1** | **0** · verde · impronta `616dc259…` combacia |
| ⭐ **F2.3-C** i parameter set **nel prodotto** | `costruisci.sh && CODIFICATORE=prodotto …` | **0** · verde 36/36 · marca **0** | **1** · marca **1** | **0** · verde 36/36 · impronta `02babbc4…` |
| ⭐ **F2.3-D** i fotogrammi B **decisi** | idem | **0** · verde 36/36 · marca **0** | **1** · rosso 1/36 · marca **1** | **0** · verde 36/36 · impronta combacia |

⛔ **La metà che si dimentica è stata verificata tutte e quattro le volte**: la marca **non compare
nel giro sano**, contata — 0 nel verde, 1 nel rosso.

⚠ **E l'impronta di `02-codifica-nal.py` è ancora `616dc259…`**, la stessa del giro dell'11 agosto:
il file non è stato toccato, quindi il guasto B certifica ancora **esattamente** quel che
certificava.

### 7.1 ⭐ Le due cose che i guasti nuovi hanno insegnato mentre venivano innestati

1. ⛔ **F2.3-C non arriva dove doveva, e la ragione è una buona notizia.** Con `repeat-headers=0`
   x265 toglie i parameter set **anche dalla prima chiave** (finirebbero in `extradata`, cioè fuori
   dal flusso): a diventare rosso è la **guardia del prodotto**, non il passo 6 — *«chiave senza
   VPS+SPS+PPS davanti»*, e il fotogramma non parte affatto. ⇒ Il difetto di v1 **non arriverebbe
   sul filo**.
2. ⛔ **F2.3-D, alla prima stesura, non innestava niente**: x265 rifiutava di aprirsi
   (`rc-lookahead=0` + `bframes=4`), e il banco leggeva *«la codifica è fallita»* invece della marca
   giusta. È la trappola n. 2 di `01-b12-guasti.py` — *il guasto che non è stato innestato* — presa
   sul fatto, e la cura è scritta nell'appiglio.

### 7.2 ⛔ E un difetto di banco trovato **girando**, non rileggendo

> ⛔ **Il demuxer di un flusso AV1 grezzo si chiama `obu`, non `av1`.** La prima stesura del
> deviatoio passava `-f "$CODEC"`: ffmpeg falliva su **ogni** flusso, compresi quelli sani — e il
> passo 7 ha stampato **«tre storpiature rifiutate»** avendone rifiutate **zero**.
>
> ⚠ Il controllo negativo era **verde per la ragione sbagliata**. L'ha smascherato il giro A, che
> nello stesso giro diceva *«il lettore indipendente non ha decodificato il flusso»*: ⇒ è la
> **ridondanza fra i passi** ad averlo preso, non un occhio.

---

## 8. Le dipendenze nuove — una, e dichiarata

| | |
|---|---|
| ⭐ **`libswscale-dev`** | ⛔ **nuova.** La conversione **BGRx → yuv420p10le**: la cattura consegna BGRx (`[M]` F2.2) e il codificatore vuole YUV planare a 10 bit |
| `libavcodec-dev`, `libavutil-dev` | erano già la strada di v1, e restano |

**Perché una libreria e non sessanta righe nostre** — `CODER.md` §4.1, con la prova di §4.1-bis
(*«quante implementazioni diverse di questa cosa dovrei inseguire?»*): di RGB→YUV esiste **una**
implementazione standard, uguale ovunque ⇒ la 4.1 vale **senza sconti**. E il conto pratico: la
nostra sarebbe **più lenta** di quella vettorizzata, su un cammino dove v1 aveva già **misurato** il
collo di bottiglia (12,5 ms contro 3,8 di codifica).

⛔ **Esiste nei pacchetti di Trixie**: `libswscale-dev 7:7.1.5-0+deb13u1`, **stesso pacchetto
sorgente e stessa versione** dell'`ffmpeg` che il banco usa come lettore indipendente. ⚠ Niente
catene fuori dai pacchetti: è la lezione di `quiche` (`DECISIONI.md` §6.4).

⚠ **Su CHUWI non è installata e non ho `root`**: `02-codifica-costruisci.sh` sa prenderne **le sole
intestazioni** dall'archivio ufficiale di Trixie (`PRESTITO=1`), e ⛔ **la libreria che si collega
resta quella di sistema** (`libswscale.so.8`). È un **prestito dichiarato**, non una dipendenza
nascosta. ⇒ **Sulla macchina dove vivrà il prodotto va installata davvero**:

```
apt install libavcodec-dev libavutil-dev libswscale-dev
```

---

## 9. ⛔ Le righe per `Makefile` e `main.c` — da applicare quando i quattro anelli si ricuciono

⛔ **Non ho toccato nessuno dei due**: il 12 agosto quattro agenti scrivono quattro anelli in
parallelo, e chi ci scrive dentro sovrascrive il lavoro degli altri. Queste sono le righe esatte.

### 9.1 `src/Makefile` — quattro modifiche

```make
#   libavcodec >= 61          la codifica video          (P2-3-codifica.md §2)
#   libavutil  >= 59          i fotogrammi
#   libswscale >= 8           BGRx (dalla cattura) -> yuv420p10le, BT.709
#                             ⛔ NUOVA: apt install libswscale-dev
```

```make
SORGENTI := main.c trasporto.c webtransport.c pagina.c comando.c certificati.c \
            tls.c registro.c rcp.c autenticazione.c aiutante.c codificatore.c
```

```make
LIBS := -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam \
        -lavcodec -lavutil -lswscale
```

```make
# ⛔ `codificatore.c` NON e' fra i GEMELLATI: e' del prodotto e basta.
codificatore.o:   codificatore.h registro.h
```

e nel bersaglio `dipendenze`, tre intestazioni in più nell'elenco:

```make
	for h in ngtcp2/ngtcp2.h ngtcp2/ngtcp2_crypto_ossl.h nghttp3/nghttp3.h \
	         openssl/ssl.h security/pam_appl.h \
	         libavcodec/avcodec.h libavutil/frame.h libswscale/swscale.h; do \
```

⚠ **E una riga per `.gitignore`**, perché l'attrezzo del banco è un binario:
`banchi/02-codifica-prova`.

### 9.2 `src/main.c` — l'inclusione, e nient'altro di mio

```c
#include "codificatore.h"
```

⛔ **Il resto non è di `main.c`**: la sessione possiede il codificatore, e chi lo apre e lo chiama è
l'anello che possiede il ciclo del video — **F2.4**. La forma è questa, e ci sono tre sole cose da
sapere:

```c
	CodificatoreRichiesta r = {
		.codec = CODIFICATORE_HEVC,        /* il valore negoziato in RCP §4.3;
		                                      e' gia' il `codec` di §6.2 */
		.larghezza = tela_larghezza, .altezza = tela_altezza,
		.fotogrammi_al_secondo = 30,
		.modo = CODIFICATORE_QUALITA_CRF, .qualita = 20,
		.profondita = 10,
		.formato = CODIFICATORE_PIXEL_BGRX,   /* quel che consegna la cattura */
		.chiavi_ogni = 0,                     /* le chiavi si chiedono (RCP §5.2) */
	};
	char errore[256];
	Codificatore *cod = codificatore_nuovo(&r, errore, sizeof(errore));
	if (!cod)
		registro_dice("video", "⛔ niente video: %s", errore);
```

```c
	CodificatoreFotogramma fg;
	if (codificatore_comprimi(cod, pixel, passo_dal_manifesto, &fg)) {
		/* fg.chiave  → tipo 0x0301, altrimenti 0x0302 (RCP.md §6.2) */
		spedisci(fg.dati, fg.byte, fg.chiave);
		codificatore_rilascia(cod);
	}
	/* ⛔ `false` non e' «un fotogramma vuoto»: e' «questo non si spedisce»,
	 *    e il registro ha gia' detto perche'. */
```

| a chi | la riga |
|---|---|
| **F2.4** | `RICHIEDI_CHIAVE` → `codificatore_chiedi_chiave(cod)`. Un delta abbandonato → **la stessa cosa**, subito (`RCP.md` §5.2) |
| **F2.4** | `TELA(ADATTATA)` → `codificatore_ridimensiona(cod, l, a, errore, sizeof errore)`, e il primo fotogramma dopo **è una chiave vera** |
| **F2.5** | la stringa per `VideoDecoder.configure()` è `codificatore_confessione(cod)->stringa_codec` — ⛔ **letta dai byte, non indovinata**: `[M]` `hev1.2.4.L120.90`, `av01.0.08M.10`. E la `description` **non si passa** |
| **F2.5 / RCP §4.3** | `livello_flusso` è il livello **vero**. ⛔ D4: *il controllo del livello sta dal lato server*, perché `[M]` Chrome accetta un livello sbagliato e dipinge lo stesso |

---

## 10. Le cuciture

### Che cosa **prometto** — la forma esatta dei byte, confermata sul prodotto

```
  HEVC Main10 4:2:0, ANNEX-B, nessuna description
  [00 00 00 01] VPS (32) · SPS (33) · PPS (34) · [00 00 01] PREFIX_SEI (39) · IDR_N_LP (20)
  [M] misurato sul flusso del PRODOTTO: 96 235 byte in lossless, 28 957 a CRF 20

  AV1 Main 4:2:0 10 bit, unita' temporali di OBU, nessuna description
  TEMPORAL_DELIMITER · SEQUENCE_HEADER · FRAME(chiave)
  [M] 138 400 byte a CRF 1, 63 347 a CRF 20
```

| a chi | che cosa |
|---|---|
| **F2.4 (il filo)** | i byte **così come sono**, un fotogramma = un blocco contiguo. ⛔ `fg.chiave` dice se il `tipo` è `0x0301` o `0x0302`. Il tetto dei 16 MiB è **già rispettato qui**: se un fotogramma non ci stava, `comprimi` ha restituito `false` e non c'è niente da spedire |
| **F2.5 (la pagina)** | `codec:` dalla confessione; ⛔ **`description` assente**; il primo chunk è `key` e porta i parameter set **con sé** |
| **F2.6 (il giudizio)** | ⛔ **la matrice è BT.709 range limitato**, ed è scritta nella VUI (`ffprobe` legge `color_range=tv`, `color_space=bt709`). Un confronto fatto con un'altra matrice **misura la matrice**. ⚠ E sulla strada BGRx la firma dei multipli di 4 **non vale**: il conteggio dei livelli sì (§6.1) |
| **F2.2 (la cattura)** | niente di nuovo: passo e formato si prendono **dal manifesto**, come F2.2 chiede, e il codificatore li riceve invece di calcolarli |

### Che cosa **chiedo**

| a chi | che cosa |
|---|---|
| ⛔ **a chi ricuce** | le righe di §9, e ⛔ **l'installazione di `libswscale-dev`** sulla macchina del prodotto |
| **a F2.4** | che `RICHIEDI_CHIAVE` e `TELA(ADATTATA)` arrivino qui: senza, `RCP.md` §5.2 è rispettata solo per caso sul primo fotogramma |
| ⚠ **alla fase 3** | il numero di §2.2: **99–390 ms** per una chiave 1080p in AV1 software, **306** in HEVC. È il primo numero che dice che la fase 8 non è un lusso |

---

## 11. Le `[?]` che restano

| # | `[?]` | perché non è chiusa | di chi è |
|---|---|---|---|
| 1 | ⛔ **il ritmo, e il ritardo** | qui si è codificato **un fotogramma fermo**: i millisecondi di §2.2 sono un campione all'avvio, non un regime (`CODER.md` §3.5) | fase 3, e **fase 8** per l'accelerazione |
| 2 | ⛔ **AV1 in software è usabile o solo esistente?** | `DECISIONI.md` §1.13 la lascia aperta e questo giro l'ha **ristretta**, non chiusa: il componente giusto è misurato, il regime no | fase 3 |
| 3 | ⚠ **il preset e il punto di lavoro** | `medium` per x265 e `10` per SVT-AV1 sono i **difetti**, tenuti e dichiarati. Sceglierli adesso vorrebbe dire fissare un numero senza il regime che lo giustifica | fase 9 |
| 4 | ⚠ **`info=0` di x265** | spegnerlo risparmia ~2,2 KB per chiave **e porta via un testimone** — che però adesso è il *secondo*, non l'unico | fase 9 |
| 5 | ⚠ **il tetto dei 16 MiB su una chiave vera** | il percorso è stato eseguito **abbassando il tetto**, non producendo un fotogramma grande davvero: quanto pesi una chiave 8K a 10 bit non lo sa nessuno (`RCP.md` §6.2 lo dice) | fase 8 |
| 6 | ⚠ **i 10 bit veri** | ⛔ **non passano da questa sorgente**, e non è una `[?]` di questo anello: la cattura dà BGRx. Restano possibili solo per via **DMA-BUF**, non provata | F2.2 |
| 7 | ⚠ **il costo della bassa latenza in banda** | `[M]` +34 % a CRF 20 su **una scena ferma e ostile**: su un desktop vero il numero è un altro | fase 9 |

---

## 12. Il conto onesto di che cosa è sopravvissuto di v1

`PIANO.md` diceva *«`codificatore.c` (889, da riportare a HEVC)»*, e la decisione **D5** aveva già
corretto la frase. Il conto adesso si può fare sui due file:

| | |
|---|---|
| righe di v1 **ricopiate** | ⛔ **zero** |
| ⭐ quel che è **sopravvissuto** | la **forma**: il componente chiesto per nome e il divieto di ripiego silenzioso; il divieto di `GLOBAL_HEADER`; il conto separato dei tempi (conversione / codifica); il commento sui fotogrammi B, **che è l'unica cosa riusata parola per parola perché la ragione non dipende dal codec** |
| ⭐ quel che è **nuovo e non c'era in nessuna forma** | i due codec e la negoziazione; il **lettore di SPS e di sequence header**; la stringa `codec` costruita dai byte; il tetto dei 16 MiB; il cambio di tela; la promozione dichiarata; il testimone `dts == pts` |

⚠ **Chi scrivesse «riusato `codificatore.c`» nella colonna del riuso starebbe scrivendo una cosa non
vera** — e adesso c'è il numero per dirlo: `1 375 + 322` righe, **59** delle quali nominano HEVC,
H.265, 10 bit o AV1, dove il file di v1 ne aveva **zero**.
