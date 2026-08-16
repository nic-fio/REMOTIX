# F4-A10 — L'anello **input → vetro**, e il metro su cui la fase si chiude

*14 agosto 2026. Anello **A10** della fase 4, uno di dieci in parallelo.
⛔ Questo anello **non scrive prodotto**: scrive il metro.*

---

## 1. Che cosa cambia per l'utente

**Niente, oggi — e questo è il punto: da domani il numero che gli diciamo è quello che sente
davvero.** Fino a ieri misuravamo *cattura → vetro* (78,1 ms) e chiamavamo «ritardo» una grandezza
che l'utente non tocca con la mano; da adesso c'è un metro che misura **dal suo movimento al pixel
che cambia**, e che si rifiuta di dare un numero quando non ha guardato niente.

---

## 2. Serve una decisione di Nic?

**Sì, una sola, e non è tecnica.**

> ⭐ **La riga «il collo di bottiglia della fase 3 è IL DISEGNO — 28,0 ms su 78,1, il 36 %» è
> un'etichetta falsa su un numero vero, e sta in nove documenti.**
> Il numero è del tratto *«richiamo del decodificatore → disegno finito»*; l'etichetta dice
> `drawImage`. ⇒ **Va riscritta o no?**

Perché è una decisione di Nic e non mia: riscriverla tocca `README.md`, `PIANO.md`, `CODER.md`,
`DECISIONI.md` e `fasi/03-movimento.md` — cioè il modo in cui la fase 3 è stata chiusa e **come è
stata raccontata all'utente**. Io ho la prova (§3) e non ho il mandato.

⚠ E c'è un costo del non farlo, già in corso: **l'anello A2 sta ottimizzando `drawImage`**, e
`drawImage` non è il problema.

*Tutto il resto — porte, banchi, guasti, codici d'uscita — l'ho deciso e riferito.*

---

## 3. Che cosa ho MISURATO

### 3.1 ⭐ Quanti guasti il metro sa accusare, **su quanti**

| | |
|---|---|
| **guasti innestati accusati** | ⭐ **16 su 16** |
| controlli della certificazione | **53 su 53**, esito **PROMOSSO** |
| di cui del ponte | **19 su 19** — e **3 sono nuovi**, per il ramo d'andata |
| controlli vivi del banco | **11** (Q0…Q10) |

`[M]` 14 agosto 2026, `python3 banchi/04-b30-anello-input.py --certifica`, uscita **0**.
Riga depositata in `banchi/04-b30-esiti.jsonl`.

**I sedici guasti, e ciascuno rompe UNA cosa:**

| | il guasto | chi lo accusa |
|---|---|---|
| 1 | il canale di input **non c'è** (nessun §7.3 sul filo) | Q0 → uscita **3** |
| 2 | l'input esce sul filo e **non arriva al desktop** | Q0 → uscita **3** |
| 3 | il conto della scena non si legge (⚠ «non arrivato» ≠ «non guardato») | Q0 → uscita **3** |
| 4 | ⛔ **la scena è sul monitor SBAGLIATO** (la trappola §1.1-bis) | Q1 → **0 punti su 0** |
| 5 | nessun `wl_surface.enter`: «non lo so» ≠ «è sul mio» | Q1 |
| 6 | l'eco non si legge più | Q2, Q3 |
| 7 | ⛔ il rilevatore dell'eco **dice sempre sì** (il guasto di v1) | Q4 |
| 8 | l'eco non cambia mai | Q4 |
| 9 | ⛔ il server **trasforma le coordinate** (§7.3 lo vieta) | Q4 |
| 10 | il ponte non ritarda il **ritorno** | Q5 |
| 11 | ⭐ il ponte non ritarda l'**andata** | Q6 |
| 12 | ⛔⛔ **la mediana sale di N ma NEL TRATTO SBAGLIATO** | Q5+Q6 |
| 13 | ⛔⛔ **il metro chiude sul confine COMODO** | Q7 |
| 14 | il banco non separa i due `drawImage` | Q8 |
| 15 | la pagina non è isolata (grana da 1 ms su un tetto di 50) | Q10 |
| 16 | il banco costa mezzo ritmo | Q9 |

⭐ **I numeri 11, 12 e 13 alla fase 3 non erano nemmeno esprimibili.** Il 12 è quello che vale di
più: *«la mediana è salita di N»* la passa anche un metro che attribuisce il ritardo al tratto
sbagliato — un metro così **non diventa mai rosso**, dice solo bugie sulla diagnosi.

### 3.2 ⛔ Il numero **input → vetro**: NON C'È, e il banco esce **3**

> ## ⛔ n = 0. Sonde chiuse: **0 su 0**.

`[M]` 14 agosto 2026, letto dal banco stesso (`--misura` guarda **e stampa il denominatore**):

| | letto nel codice |
|---|---|
| il CLIENT scrive sul filo | `createBidirectionalStream` **1** (4 665 righe) — c'è il canale di controllo |
| il SERVER decodifica l'input | `T_PUNTATORE` **4** (4 507 righe) ✅ |
| il SERVER inietta l'input | `ei_device_pointer_motion_absolute` **1**, `ei_device_scroll` **4** (968 righe) ✅ |
| ⛔ **i GANCI sono cuciti** | `.input_puntatore` **0**, `input_puntatore =` **0** (2 655 righe) ⛔ |

⭐ Il server c'è quasi: `src/input.c` è passato da **284 byte a 35 368** mentre scrivevo.
⛔ **Ma il canale è scritto ai due capi e non collegato in mezzo**, e `src/pagina.html` non ha
ancora un mittente di §7.3.

⇒ Il banco dice **«non ho niente da giudicare»** ed esce **3**, non 0. ⚠ È il difetto che al
validatore della fase 1 è costato una riscrittura: *«tutti quelli provati sono andati bene» è vero
anche quando i provati sono zero*.

**E la scomposizione c'è già, in undici tratti** — provata sul finto, che li somma al totale con
scarto **0,00 ms**:

```
1a evento → il prodotto lo vede (fase di cattura)        [pagina]
1b il prodotto lo vede → i byte escono (il gestore)      [pagina]
2  byte usciti → la SCENA riceve l'input                 [ancora]  ⭐ nuovo
3  la scena riceve → la scena DISEGNA                    [server]  ⭐ nuovo
4  la scena disegna → cattura (`pts` di Mutter)          [server]
5  cattura → PRIMO byte in pagina                        [ancora]
6  primo byte → ULTIMO byte                              [pagina]
7  stream completo → richiamo di `decode()`              [pagina]
8  `decode()` → richiamo del decodificatore              [pagina]
9  ⭐ richiamo → 1° `drawImage` finito (l'ATTESA)         [pagina]  ⭐ nuovo
10 ⭐ 1° → 2° `drawImage` finito (il disegno VERO)        [pagina]  ⭐ nuovo
```

⭐ **E il totale non porta dentro l'errore dell'ancora**: `t0` e `t1` sono tutt'e due
`performance.now()` della stessa pagina. **Il numero della fase 3 non aveva questo vantaggio.**

### 3.3 ⛔⛔ I pezzi ciechi sono **DUE**, e la fase 3 ne dichiarava uno solo

| | | |
|---|---|---|
| in **USCITA** | `[?]` 16-40 ms | disegno finito → pixel acceso (`STUDI.md` §web §6.2). ⛔ **non su Xvfb**, dove non esiste affatto |
| ⭐ in **INGRESSO** | `[?]` 4-12 ms | mano → `event.timeStamp`: dispositivo, nucleo e compositore **del client**. ⛔ **Nessuno lo aveva ancora nominato** |

Sono in una funzione sola (`con_pezzi_ciechi`), così **non si può stampare un numero senza**.

### 3.4 ⭐⭐ LA TESI 3 — *«il metro della fase 3 è affidabile»*: **PROVATA, e NON regge come è scritta**

`[M]` 14 agosto 2026, rileggendo `banchi/03-b17-esiti.jsonl`. ⚠ Non è un ricalcolo: sono i numeri
che quel file porta già.

| giro | tratto 5 «decodifica» | tratto 6 «disegno» | **5+6** | n |
|---|---|---|---|---|
| `E-C-software-av1` | 6,315 | **9,105** | 15,42 | 508 |
| `E-B-hardware-stessapagina` | 6,315 | **9,155** | 15,47 | 509 |
| `E2-A-software-hevc` | 1,495 | **29,250** | 30,75 | 375 |
| `E2-B-hardware-hevc` | 0,775 | **25,105** | 25,88 | 799 |
| `E3-deposito-hw-5punti` ⭐ *il numero della fase* | 0,730 | **27,995** | 28,73 | 379 |

⛔ **I due tratti si muovono in versi OPPOSTI.** Un `drawImage` non può diventare tre volte più caro
perché a monte c'è un decodificatore diverso: **`drawImage` non sa quale codec ha prodotto il
fotogramma.** Qualcosa si è spostato **attraverso il confine fra il tratto 5 e il 6**.

⛔ **E il palco non è la spiegazione**: `[M]` rileggendo il campo `palco` dei tre giri, browser,
bandiere, GPU (`ANGLE (Intel, Mesa Intel(R) Graphics)`) e contesa (`clienti_sull_xvfb: 0`, cioè il
desktop dell'utente) sono **identici**.

> ### ⇒ La risposta alla domanda del coordinatore: **da dove viene la differenza**
>
> Non dalla scena, non dal palco, non dal conteggio. **Dal CONFINE della misura**: il tratto 6 è
> `richiamo del decodificatore → disegno finito`, e su HEVC contiene qualcosa che su AV1 stava nel
> tratto 5. Il numero è vero; ⛔ **il nome è falso**, ed è il nome che è finito nei documenti.

**⭐ A2 e la fase 3 non si contraddicono: misurano i due lati di un confine mal posto.**
Gli **8,45 ms** di A2 sono il costo vero di disegnare un fotogramma **già pronto**; i **28,0** sono
quello di aspettare che lo sia **più** disegnarlo. ⇒ ⛔ **Il difetto è nel metro, ed è mio**, come
il coordinatore sospettava — ma non è un errore di conto: è **un'etichetta**.

**Quel che invece regge, ed è nuovo**: `[M]` il costo del **client dopo il filo** raddoppia con
HEVC — **15,42 e 15,47** sui due giri AV1 (concordi entro 0,05 ms) contro **25,88 e 30,75** sui due
HEVC ⇒ **+10,5 … +15,3 ms**. Il tetto sfora **anche per un motivo che sta nel client**.

**Due dispersioni che nessun documento porta accanto al 28,00**:
· fra i due giri HEVC il tratto 6 vale **25,105 (n=799)** e **29,250 (n=375)** — 4,15 ms, e cambia
solo il codificatore del **server**, che il `drawImage` del client non può vedere;
· fra due giri della **stessa** configurazione: **25,105** e **27,995** — 2,89 ms, l'**11 %**.

> ### ⛔⛔ E la cella che manca — e chiuderebbe la questione con una riga
>
> `[M]` `banchi/03-palco-esiti.jsonl`, giro **`con-gpu`**: `powerEfficient: **true**` per **HEVC
> Main10**, VP9 profilo 2 e H.264. ⛔ **AV1 in quel giro non è stato provato**: le voci sono tre e
> AV1 non è fra loro.
> ⚠ L'unica lettura di AV1 che esiste (`02-pagina-esiti.jsonl`, giro `f25-chrome-1786535362`) dice
> `powerEfficient: false` — ⛔ **ma nello stesso giro anche VP9 dice `false` e HEVC dice
> `supported: false`**: è la firma del browser **accecato** di `LEZIONI.md` §2.0, e **non è
> utilizzabile**.
> ⇒ **Il confronto AV1/HEVC su cui la fase 3 si chiude non ha mai avuto la sua cella di controllo.**
> Costa una riga: rigirare `03-palco-dipinge.py` con AV1 nell'elenco.

⚠ **Quel che resta `[?]`, dichiarato invece che colmato**: *perché* il costo attraversi quel
confine. L'ipotesi — il decodificatore hardware consegna il `VideoFrame` prima che la sua superficie
sia utilizzabile, e il primo `drawImage` paga l'attesa — è `[?]`, **non** `[M]`.
⭐ **Il fatto invece è `[M]` e non dipende dall'ipotesi.**
⛔ E la prova falsificabile è **dentro il banco** (Q8): il tratto si spacca in `9` e `10`
avvolgendo `drawImage`. Se il 9 è grande e il 10 piccolo, è l'attesa; se sono simili, è il disegno.

### 3.5 ⛔ La tesi 1 del mandato — **refutata**

> *«Con il canale di input, lo STESSO metro misura finalmente input → vetro.»*

**Non è vero**, e crederlo sbaglierebbe in **due versi opposti**: manca a monte (cinque tratti che
il metro della fase 3 non attraversa affatto) e **sovrappone** a valle (il `t0` della fase 3 è *«la
scena ha disegnato»*, che nell'anello di input **è la conseguenza dell'input**, non l'origine).
⇒ ⭐ **I due numeri non si sommano e non si sottraggono: il secondo CONTIENE il primo.** Il banco
stampa la quantità **aggiunta** (tratti 1a+1b+2+3), sullo **stesso giro** e sugli **stessi
fotogrammi** — non fra due giri, dove si mettono in mezzo deriva, palco e contesa.

### 3.6 ⭐ La tesi 2 — accettata, **e allargata**: i confini sono due

Quello di **chiusura** è già scomodo (disegno finito) ed è ereditato. ⛔ Quello di **apertura** è
nuovo e ha **tre** posizioni difendibili: la chiamata alla funzione di spedizione (comodissima), la
consegna dei byte a `WebTransport` (comoda), e **`event.timeStamp`** (scomoda) — scelta la terza,
con un ascoltatore in **fase di cattura** installato prima di ogni script della pagina.
⛔ E la differenza fra le tre **non si stima: si misura** (tratti 1a e 1b).

⭐ **E l'anello ha due accoppiamenti indipendenti, non uno**: l'**eco nei pixel** (confine scomodo)
e il **campo `input` dei 28 byte** (confine comodo). Il banco li consegna **tutt'e due** e dichiara
come numero il secondo. Sul finto il confine comodo si regala `[M]` **16,7 ms** — un intervallo di
quadro.

---

## 4. ⛔ Che cosa NON ha funzionato

1. ⛔⛔ **La mia prima stesura del finto aveva i due confini che cadevano sullo STESSO fotogramma.**
   Q7 usciva rosso sul giro sano, e la tentazione era di rilassare Q7. Sarebbe stato il difetto
   peggiore possibile: **avrei certificato Q7 su un mondo in cui il difetto che Q7 cerca non può
   esistere**. Il difetto era del finto (metteva `input = id` sul fotogramma che mostra l'eco,
   mentre §6.2 dice «l'ultimo input iniettato **prima della cattura**» ⇒ è `id+1`).

2. ⛔⛔ **La certificazione era VERDE mentre la stampa del verdetto era rotta.** Leggevo lo scarto
   fra i due orologi da una chiave (`errore_ancora_us`) che nel verbale **non esiste più**: `.get`
   tornava 0, lo scarto non veniva sottratto, e i tratti 2 e 5 uscivano dell'ordine dei **500 000
   ms**. I giudici sono funzioni pure e la stampa non è un giudice — `LEZIONI.md` §2.2 in
   miniatura. ⭐ **A trovarlo è stato `--finto`**, cioè il finto usato per quel che serve.
   ⇒ Cura: il controllo **H** lega le due cose, e se divergono di nuovo diventa rosso qui invece di
   uscire in un rapporto.

3. ⚠ **Il primo `_p1` era rosso per costruzione**: contava anche i totali fra i tratti «in cui il
   surplus non deve comparire» — e il totale **deve** salire, è la pretesa n. 1. Un controllo che
   non può mai passare è inutile quanto uno che non può mai fallire.

4. ⚠ **Ho scritto `[M]` su una cosa che era `[?]`** — *«E-C è AV1 col decodificatore in software
   (dav1d)»* — e me ne sono accorto **andando a cercare la misura invece di ricordarla**. La misura
   di AV1 non esiste (§3.4), e l'unica che sembrava esserci veniva da un browser accecato. Corretto
   nel banco e qui. ⛔ È `LEZIONI.md` §2.3-quater: una ragione non misurata dentro una conclusione.

5. ⛔⛔ **Il mio controllo di precondizione ha dato un FALSO VERDE, e l'ho pagato dentro il banco
   che esiste per non pagarlo.** Cercava `0x0101` in `pagina.html`, ne trovava **cinque** e diceva
   ⭐OK⭐ *«il client manda l'input»*. Erano **tutt'e cinque dentro i commenti**: il client non
   manda niente. ⇒ ⭐ Cura: gli aghi adesso sono **chiamate di API**, che in un commento non possono
   stare — e la riga dice che è una **precondizione, non una prova**: la prova è sul filo, e la fa
   Q0. ⚠ È `LEZIONI.md` §1.9 nella sua forma più banale, un verde prodotto dallo **strumento**, e a
   trovarlo è stato il fatto di **stampare il denominatore accanto al risultato** — cioè la regola
   4 di quella lezione, applicata a me stesso.

6. ⚠ **La misura vera non è stata eseguita** e non poteva esserlo. Non ho fabbricato un giro «per
   avere un numero»: sarebbe stato un verbale vuoto con l'aria di una misura. ⛔ `--misura` esce
   **3** e `04-b30-lancia.sh accendi` **si rifiuta**.

7. ⚠ **Sono caduto una volta per un errore del server (API 529)**, non per un difetto del lavoro.
   `04-b30-ponte.py` e `04-b30-scena.c` erano già su disco e non li ho rifatti.

---

## 5. Che cosa manca al prodotto perché l'anello si chiuda — **con la firma esatta**

### 5.1 ⛔ Il client deve MANDARE l'input *(il blocco vero — A3/A7/A8 + coordinatore)*

Oggi `src/pagina.html` non ha nessun mittente di §7.3. Al banco basta che **i byte escano**: li
riconosce sul filo da sé, con `RCP.md` §6.1 + §7.3, senza sapere come il prodotto li manda.

⛔ **Le due sole cose che il banco pretende:**
- l'inquadratura è quella di §6.1 (`u16 tipo`, `u32 lunghezza`, corpo), e la lunghezza del corpo è
  **esattamente** quella di §7.3 (`PUNTATORE` = 20 byte);
- i byte passano da `WebTransport` (`createUnidirectionalStream`, `createBidirectionalStream` o
  `datagrams.writable`): il prologo avvolge tutt'e tre.

### 5.2 ⛔ Il server deve dire QUANDO — *la firma esatta che mi serve*

Senza questa riga il tratto 2 resta **un tratto solo** e non si può dire se il ritardo sta nel filo
d'andata, nella coda del server o in `libei`. Basta **una riga di registro per input**:

```c
/* src/input.c — al ritorno di ogni input_*() */
registro("b30 input id=%u tipo=%u arrivo_us=%llu iniezione_us=%llu esito=%d",
         id, tipo,
         (unsigned long long)arrivo_us,      /* CLOCK_MONOTONIC, quando rcp.c l'ha decodificato */
         (unsigned long long)iniezione_us,   /* CLOCK_MONOTONIC, dopo ei_device_frame() */
         esito);                             /* 0 consegnato · -1 no · 1 non producibile */
```

⚠ `arrivo_us` e `iniezione_us` sullo **stesso** orologio del `pts` dei 28 byte
(`CLOCK_MONOTONIC`, come `src/figlio.c:1616-1653` verifica) — o non si sottraggono.

### 5.3 ⛔ Il prodotto deve dichiarare QUALE MONITOR cattura

⛔ Senza, **Q1 esce «0 punti su 0»** e il banco non dà nessun verdetto — e ha ragione: è la trappola
di `LEZIONI.md` §1.1-bis, che ha già morso due volte, la seconda **sul risultato che la citava**.

```c
/* src/mutter.c — dopo RecordVirtual */
registro("b30 monitor catturato=%s", nome_connettore);  /* lo stesso nome che wl_output.name dà */
```

⭐ È la stessa riga che serve ad **A1** (il desktop vero): il difetto del desktop vuoto e il metro
sul monitor sbagliato sono **la stessa domanda** — *chi cattura chi*.

### 5.4 ⚠ E i ganci vanno cuciti

`src/rcp.h` li dichiara tutti e sei e `src/input.c` li attua, ma `input_puntatore = …` non compare
in `figlio.c` né in `main.c`: **il canale è scritto ai due capi e non collegato in mezzo.** È la
cucitura del coordinatore (`fasi/04-si-comanda.md`), ed è esattamente il difetto di
`F5-desktop-vero.md`: *fra due pezzi ciascuno corretto per conto suo*.

---

## I file

| | |
|---|---|
| `banchi/04-b30-anello-input.py` | il banco: 11 controlli, 16 guasti innestati, 4 codici d'uscita |
| `banchi/04-b30-scena.c` | la scena che **riceve l'input** — copia di `03-scena.c` + `wl_seat` + la seconda marca (l'eco) |
| `banchi/04-b30-ponte.py` | copia di `03-b17-ponte.py` + **il ritardo sul ramo d'ANDATA** |
| `banchi/04-b30-lancia.sh` | porte **7691-7695**, ban-file e socket **miei** |
| `banchi/04-b30-esiti.jsonl` | le righe depositate |

⛔ **Nessun file `03-*` è stato toccato**: `03-b17-ritardo.py` e `03-marca.py` si **importano**, così
se cambiano questo banco se ne accorge.

**Per vedere che cosa dirà quando il prodotto arriva:**
```
bash banchi/04-b30-lancia.sh certifica    # 53 su 53, 16 guasti su 16
bash banchi/04-b30-lancia.sh finto        # la FORMA della misura, non la misura
```
⛔ **Nessun numero del finto va in un documento con la marca `[M]`.**
