# Fase 4 — Si comanda

*Aperta il 14 agosto 2026, mattina. ⛔ Questo documento è aperto **all'apertura della fase**, non
alla chiusura: le misure qui si **registrano** strada facendo, non si ricordano dopo
(`fasi/README.md`).*

---

## Che cosa deve produrre

`PIANO.md` §«Fase 4 — Si comanda», e in testa la priorità decisa dall'utente:

| | | |
|---|---|---|
| ⭐ **1** | **IL DESKTOP VERO** — deciso dall'utente il 14 agosto 2026, ed è **dentro la fase, in testa** | finché il desktop non si vede, **non c'è niente da comandare** |
| **2** | il **canale di input**: puntatore assoluto, pulsanti, rotella, lettere, posizioni | `RCP.md` §7.3 |
| **3** | il **puntatore disegnato dalla pagina**, e il cursore che non entra mai nell'immagine | `SPECIFICHE.md` §7.1 |
| **4** | le **due disposizioni della pagina** — classica con `Pointer Lock`, tocco coi sette gesti, **passaggio automatico sul contesto** | `DECISIONI.md` §5-bis.0-bis |
| **5** | le **scorciatoie che il browser si tiene**, **dichiarate** e non falsificate | `SPECIFICHE.md` §7.3-bis |

**E i due lavori ereditati dalla fase 3**, che senza di loro l'utente non ha niente da giudicare:

| | | dove |
|---|---|---|
| ⛔ | **HEVC non dipinge nel browser dell'utente** — 1 748 consegnati, **0 dipinti** | `fasi/03-movimento.md` §0-ter |
| ⛔ | **il disegno: 28,0 ms su 78,1 — il 36 %**, il collo di bottiglia nuovo | `fasi/rapporti/F3-E-anello-rimisurato.md` |

**L'utente vede**: ⭐ **usa il desktop**. È il momento in cui REMOTIX smette di essere una
dimostrazione.

---

## Il banco *(scritto PRIMA di sviluppare)*

⛔ **Ogni sottofase scrive il proprio banco prima del proprio codice, e lo certifica prima di
crederlo** (`CODER.md` §3.3). L'elenco vive qui e si riempie strada facendo.

**Le dieci sottofasi, un agente ciascuna** *(lanciate il 14 agosto 2026, in parallelo)*:

| | sottofase | il banco | che cosa accusa | porte | esito |
|---|---|---|---|---|---|
| **A1** | ⭐ il desktop vero | `04-b20-desktop-vero` | la shell è **sul monitor che si cattura** — non uno schermo in più, vuoto | 7601-05 | ✅ **205 contro 0** |
| **A2** | la pagina che dipinge | `04-b21-dipinge` · `04-b22-disegno` | fotogrammi **dipinti**, non «consegnati» · il tratto del disegno scomposto | 7611-15 | ⭐ **le due accuse CADONO** |
| **A3** | il filo dell'input | `04-b23-filo-input` | le violazioni di `RCP.md` §7.3, ciascuna col motivo giusto | 7621-25 | ✅ **64 su 64** |
| **A4** | l'iniezione (libei/EIS) | `04-b24-iniezione` | l'input arriva **al desktop**, e il segno della rotella è quello giusto | 7631-35 | ✅ **27 OK, 0 NO** |
| **A5** | la tastiera | `04-b25-tastiera` | la lettera accentata con la disposizione giusta **e** con quella sbagliata | 7641-45 | ✅ **26 su 26** |
| **A6** | il cursore | `04-b26-cursore` | il cursore **non** è nell'immagine, e la forma arriva in banda laterale | 7651-55 | ✅ **0 contro 762** |
| **A7** | la pagina, modo classico | `04-b27-classico` | `Pointer Lock`, il puntatore disegnato, il rilascio alla perdita del fuoco | 7661-65 | ✅ **19 su 19**, due giri |
| **A8** | la pagina, modo tocco | `04-b28-gesti` | i sette gesti, e il passaggio automatico sul contesto | 7671-75 | ⭐ **24 su 25**, tre giri |
| **A9** | le scorciatoie (sonda S3) | `04-b29-scorciatoie` | «arriva **e basta**?» — i tre stati, su due motori | 7681-85 | ⭐ **594 misure**, 74 buttate |
| **A10** | i banchi di fase | `04-b30-anello-input` | ⭐ l'anello **input → vetro**, che alla fase 3 non era misurabile | 7691-95 | ⭐ **16 su 16**, e ⏳ `n=0` |
| ⭐ **O2** | **il numero dell'anello** | `04-b30-*` (esteso) · `04-b32-terreno` · `04-b32-coda` · `04-b32-ritmo` | ⭐ **il ritardo input → vetro, con `n` e la scomposizione**, e la coda che cresce | **7721-25** | ⭐⭐ **~140 ms, n = 326 e 322**, 10 controlli su 11 |

⭐ **E le cuciture le tiene il coordinatore, non gli anelli** — `src/input.h`, `src/tastiera.h`,
`src/cursore.h`, più `figlio.c`, `main.c` e il `Makefile`. ⛔ È la lezione di
`fasi/rapporti/F5-desktop-vero.md`: *il difetto della fase 3 non era **dentro** un pezzo, era **fra**
due pezzi ciascuno corretto per conto suo — e le cuciture, non avendo un proprietario, non le
guardava nessun banco.* Qui il proprietario ce l'hanno.

---

## Che cosa è stato sviluppato

### ⭐ A5 — la tastiera *(chiusa il 14 agosto 2026)*

`src/tastiera.c` su `xkbcommon` 1.7.0: dato un carattere Unicode e la disposizione, quali codici
**evdev** premere e in che ordine. Rapporto in
[`rapporti/F4-A5-tastiera.md`](rapporti/F4-A5-tastiera.md).

---

## Le misure *(si riempie strada facendo)*

### ⭐ Il costruttore, prima di ogni misura — `[M]` 14 agosto 2026

L'albero della fase 4 **costruisce**: `make` esce 0 nel contenitore della macchina di prova, con
`-lei -lxkbcommon` collegate davvero e `input.o · tastiera.o · cursore.o` dentro il binario.
⛔ È il controllo che vale **prima** di tutti gli altri: dieci anelli interrotti a metà da un guasto
del server potevano lasciare l'albero rotto, e non l'hanno fatto. ⭐ E i **gemelli sono pari**
(`src/rcp.c` ≡ `banchi/rcp/rcp.c`).

### ⭐⭐ LA CATENA DELL'INPUT È CUCITA DA UN CAPO ALL'ALTRO — `[M]` 14 agosto 2026

*E la cucitura è del coordinatore, per la ragione scritta in testa a questo documento.*

⛔ **Il fatto che nessun anello aveva in mano, e che cambia la forma del lavoro: il palco vive in un
ALTRO PROCESSO.** `libei` parla con la sessione grafica dell'utente, e quella ce l'ha il **figlio**;
QUIC, RCP e i byte del client stanno nel **padre**. ⇒ Fra il tasto premuto nel browser e il tasto
premuto sul desktop c'è **un confine di processo**, e nessuno dei due lati poteva attraversarlo da
solo.

| il tubo | il verso | dove |
|---|---|---|
| ⭐ **l'input** | padre → figlio | `MSG_INPUT` + `figli_input()` · i **sei ganci** in `rcp_avvia()` · il ponte `input_al_figlio()` in `main.c` |
| ⭐ **la forma del cursore** | figlio → padre | `MSG_CURSORE` a pezzi (un 256×256 in BGRA fa 262 144 byte, otto volte `PEZZO_MAX`) · `wt_cursore_diffondi()` · `rcp_cursore_forma()` |
| ⭐ **il campo `input` dei fotogrammi** | figlio → padre, **dentro il fotogramma** | ⛔ e questa è la scelta che lo rende **vero** invece di plausibile |

> #### ⛔⭐ Perché il campo `input` lo timbra il FIGLIO e non il padre
>
> §6.2 promette che «l'effetto di quell'input è già nella scena». Il padre sa che cosa ha
> **mandato** al palco; solo il figlio sa che cosa il compositore ha **preso**, e in che istante ha
> catturato. ⇒ Riempirlo nel padre direbbe *«l'ultimo input spedito prima della spedizione»*: un
> numero più alto, e l'anello del ritardo misurerebbe un ritardo **più corto del vero — in nostro
> favore**, che è la direzione in cui nessuno sbaglia per caso.
> ⭐ Da cui due conseguenze scritte nel codice: il contatore avanza **solo se l'iniezione è
> riuscita**, e il fotogramma *tenuto* porta il **suo** `input`, non quello di adesso.
> `CODER.md` §1-bis: *il confine si sposta nella direzione scomoda*.

⭐ **E l'albero costruisce con tutti e tre i tubi collegati**: `make` esce 0, `-lei -lxkbcommon`
dentro, gemelli pari, e la marca nel binario verificata.

---

### ⭐⭐ A1 — il desktop vero, e **la persistenza** `[M]` 14 agosto 2026

**L'A/B, stessa scena in movimento, stesso quarto d'ora:**

| | monitor | fotogrammi al client in 40 s | verdetto sui pixel |
|---|---|---|---|
| **con** `--virtual-monitor` | 1 → 2 | ⛔ **0** (`0 guasti`: uno zero vero) | ⛔ **VUOTO** |
| **senza** (curato) | 0 → 1 | ⭐ **205 conformi** | ⭐ **SHELL** (salto di luminanza 51,3 · fronti del testo 548) |

⭐ **E il banco non si fida di «c'è lo sfondo»** — è l'errore che ha nascosto il difetto per due fasi.
Distingue con **due indicatori di natura diversa**, calibrati su immagini vere *prima* di fissare le
soglie: il **salto di luminanza** al bordo basso della barra (11,8 shell / 0,07 sfondo) e i **fronti**
del testo dell'orologio (565 / 0). ⛔ Il terzo indicatore (la dock) **non distingueva, e sta scritto
che è stato scartato**.

#### ⛔ Tre cose che hanno smentito il mandato che avevo scritto

| | |
|---|---|
| ⛔ **`sessione.c:650` non lo esegue nessuno** | `sessione_assicura()` **non è chiamata dal prodotto**. Su questa macchina `--virtual-monitor` lo impone un drop-in scritto a mano ⇒ **I7 violato**, e il desktop di `prova` si vedeva grazie a un file di configurazione, non al prodotto |
| ⛔ **la cura è in QUATTRO posti, non due** | coi due soli, `sessione_assicura()` avrebbe **ucciso la sessione giusta a ogni chiamata** (0 monitor = `SESSIONE_NERA` = «fai rinascere»). La macchina a stati è stata rovesciata, e dichiarato |
| ⛔ **la tela concessa è una promessa che nessuno mantiene** | client a 1280×720: il server la concede, il palco cattura a 1920×1080 (costante di compilazione), `rcp` rifiuta ogni fotogramma — `[M]` **145 prodotti, 0 spediti, client nero senza errori**. ⚠ E la misura la decide il **nostro** formato PipeWire `[R]`, non `RecordVirtual`: la `[?]` n. 1 di questo documento è **risolta, e la risposta era un'altra** |

#### ⭐⭐ E la persistenza REGGE — la tesi del difetto è **falsa**

*Nata da un'obiezione dell'utente, il 14 agosto: «deve lavorare anche quando nessuno guarda lo
schermo — altrimenti che senso ha la persistenza della sessione?».*

⛔ **La tesi da refutare era**: *«un client che si stacca porta via l'unico monitor: la sessione resta
senza dove disegnare, e le applicazioni se ne accorgono»* — cioè il difetto che in v1 mandava
`libmutter` in asserzione fallita. `[M]` otto letture in 11 minuti, sessione fatta nascere dal
prodotto curato, scena dichiarata (una finestra che scrive l'ora 5 volte al secondo, **sullo schermo
e su un file**):

| | |
|---|---|
| ⭐ il monitor | **mai sparito**: sempre **1**, `Virtual remote monitor`, anche nei quattro minuti senza nessuno. Mai `0` |
| ⭐ l'applicazione | **1 160 righe fra 07:37:36 e 07:41:36** — i 240 s a 4,8/s **senza un buco**, mentre non guardava nessuno |
| ⭐ `libmutter` | **nessuna asserzione nuova**: le 2 asserzioni e 7 critiche sono **costanti** dalla prima all'ultima lettura, e portano il pid di un `gnome-shell` che il prodotto stava **congedando** |
| ⭐ al riattacco | `riattacco-1` **120 fotogrammi conformi → SHELL**; `riattacco-2` → **SHELL**. ⭐ Ed è **la stessa finestra**: **pid invariato** (465823 all'inizio e alla fine, da 154 a 3 497 righe) — una finestra nuova avrebbe un pid nuovo |

⇒ ⭐ **L'esito è «il monitor c'è e nessuno lo cattura», che non è un difetto: è l'invariante I4
mantenuta.** E il merito è del **figlio**, che sopravvive al distacco per costruzione.
⚠ **Ma resta una cosa per la fase 5, e non era attesa**: **il palco muore col FIGLIO, non con la
sessione** ⇒ chi congederà un figlio che gira a vuoto **toglierebbe il monitor a una sessione viva**
— il difetto di v1 preso dall'altro capo.

⛔ **E tre numeri del banco mentivano**, trovati da chi li aveva scritti: il conteggio dei monitor era
**il doppio** (`GetCurrentState` elenca ogni schermo due volte) e sbagliava **nella direzione che
rassicura**; il contatore dei client **non esisteva** (QUIC vive su un solo socket non connesso, e
dava zero in tutt'e due i modi di guardare); e il file di esiti non era JSON valido. ⭐ **Nessuno dei
tre entrava nel verdetto — e proprio per questo nessuno li avrebbe controllati.**

---

### ⭐⭐ A2 — le due accuse ereditate dalla fase 3 sono CADUTE

| | |
|---|---|
| ⛔ «HEVC non dipinge» | **falso**: `[M]` **8 caselle su 8** dipingono (profilo della stringa × profondità del flusso, HEVC e AV1, 64×48 **e** 1920×1080), compresa la combinazione esatta del prodotto — flusso Main10 letto con la stringa Main8. Palco = il **desktop vero**, GPU vera, dichiarato e verificato dall'altro capo. E in continuo: **60 su 60**, sei giri |
| ⛔ i «1 748 consegnati, 0 dipinti» | ⛔ **il conto era letto male**: nella finestra della sessione nera il contatore **entra a 1748 ed esce a 1748** per 2 min 38 s — il 1748 è **il residuo della sera prima** (`ciclo_fotogrammi` è statico di file). E il «1 659» era un `grep -c` su tutto il file da 6,7 MB: nella finestra vera sono **653** |
| ⇒ la causa vera | **il monitor aggiunto e vuoto**: nulla si muove, Mutter non consegna. **Lavoro di A1, non del codec** |
| ⛔ «il disegno costa 28,0 ms» | **falso**: `[M]` **2,25 ms** (5 giri, dispersione 0,30), stesso confine della fase 3. E il controllo positivo su AV1 dà **6,25-8,45** contro i **9,07** della fase 3 ⇒ **il cronometro era tarato** |

⭐ **E la prima ipotesi dell'anello — profondità 8 negoziata contro flusso a 10 — è stata scritta
prima di misurare e smentita alla prima casella.** *Scritta prima, quindi smentibile: è il verso
giusto.*

---

### ⭐⭐ A3 — il filo dell'input: **64 casi su 64**, e **16 guasti** certificati

29 violazioni + 25 verdi attesi + **10 su §7.2** (il cursore). 64/64 con una connessione nuova che
arriva a `ECCOMI` dopo ciascuna, e gli stessi numeri su due macchine.

⭐ **E la certificazione ha trovato DUE difetti del prodotto che nessun giro verde avrebbe visto:**

| | |
|---|---|
| ⛔ `6u + lung` a 32 bit | con `lung = 0xFFFFFFFF` vale **5**: un annuncio da 4 GiB passava il controllo di lunghezza |
| ⛔⭐ il `CURSORE_FORMA` da otto byte | spediva `w.len` invece di `n` ⇒ dichiarava `16×16` con **otto byte di corpo**, e **la pagina avrebbe chiuso a ogni cambio di forma**. ⭐ E la riga più preziosa: **il registro del server scriveva il vero e il filo un'altra cosa** — un banco che avesse guardato il valore di ritorno sarebbe stato **verde** |

⭐ **E la coppia dei limiti è provata nei DUE versi**, che è la cosa che un caso solo non dimostra:
`0×5` e `5×0` devono essere **rifiutati** *e* `0×0` (il nascosto) deve **passare**. Due guasti
opposti: togliendo il controllo parte il messaggio vietato; rendendolo troppo severo **sparisce per
sempre il cursore nascosto**. ⛔ Nessuno dei tre casi, da solo, distingue le due implementazioni.

⚠ **E la divisione dei compiti che ne è uscita**, che vale oltre il cursore: `cursore.c` decide **che
cos'è** quel cursore; `rcp.c` non deve **emettere** ciò che la specifica vieta. *Sono due obblighi a
due strati, e confonderli fa perdere quello che protegge l'utente.*

---

### ⭐⭐ A4 — l'iniezione: l'input arriva DAVVERO al desktop `[M]` 14 agosto 2026

*Macchina di prova, utente `prova`, `libmutter` 48.7 · `libei` 1.3.901 · `wl_seat` v8.*

⛔ **Come si è misurato, ed è la metà che conta**: il testimone è **una finestra Wayland vera**
(`banchi/04-b24-testimone.c`) a schermo intero **sul monitor che abbiamo montato noi**, che stampa
una riga per ogni evento che il **compositore le consegna**. ⚠ Il registro dell'iniettore *non è* la
misura: dice che abbiamo chiamato una funzione.
⭐ **E il monitor non si spera, si sceglie per misura**: la sessione aveva già un `Meta-0` di un
altro client; il nostro `RecordVirtual` monta `Meta-1`, e il testimone si mette **su quello**. Senza,
ogni iniezione sarebbe finita sullo schermo sbagliato — la stessa forma d'errore che alla fase 2
teneva verde un banco mentre la cattura riceveva zero fotogrammi.

**Il giro sano: 27 righe `OK`, 0 `NO`, 0 `??`.** E il banco è **certificato con due guasti innestati
su una COPIA di `input.c`** — ⛔ e se la copia risulta identica all'originale **il banco si rifiuta di
girare**, perché un guasto che non cambia niente certifica il nulla:

| guasto | il banco ha detto |
|---|---|
| **`segno`** — si toglie l'inversione | ⛔ **ROSSO**: *«lo schermo remoto scorre AL CONTRARIO»* — ⭐ e la riga del mezzo scatto è rimasta **verde**: ha accusato **il segno**, non «qualcosa» |
| **`conto`** — il rilascio non rilascia | ⛔ **ROSSO** su tre righe, e una è **dal lato che riceve**: *«la finestra NON ha visto il rilascio del tasto»* |

#### ⭐ I quattro `[R]` portati a `[M]`

| | |
|---|---|
| ⭐⭐ **il `mapping-id` era INVERTITO in v1** | quello che dichiariamo (`277896a5…`) **non è** quello che la regione porta (`d72788c1…`): lo genera **Mutter** e ce lo pubblica, e `handle_record_virtual` **ignora in silenzio** la nostra proprietà. ⇒ Riusare v1 alla lettera dava **un puntatore che finiva sull'altro monitor** |
| **il segno della rotella, nei DUE versi** | `+120` (utente in su) → `axis_value120 = −120`; `−120` → `+120`. ⭐ Segni **opposti**: si misura il segno, non «che qualcosa si muove». E l'orizzontale passa com'è, misurato anche lui nei due versi |
| **i mezzi scatti** | `60` → `−60`. ⛔ Con `scroll_discrete` sarebbe stato `60/120 = 0`: la strada è `scroll_delta` |
| ⭐⭐ **i due ricambi silenziosi, riprodotti a dispositivo IN USO** | keymap `us`→`de` (68 402 → 70 138 byte, `ricambi_tastiera 0→1`) e geometria 1600×900 → 1280×720 (`ricambi_puntatore 0→2`). ⭐ **E il codice li regge**: rilegge keymap e regioni a ogni `DEVICE_ADDED` |

⭐ **E due fatti che nessun documento portava**: **la regione non è all'origine** (`1920,0`) — senza
sommarla il puntatore va sull'altro schermo **senza errore** — e **senza un consumatore PipeWire il
dispositivo assoluto non nasce affatto**.

⭐ **Il rilascio al distacco** (`RCP.md` §11): conto tenuto, `input_rilascia_tutto()` ritorna **2**, e
⭐ **la finestra vede i due rilasci**. ⏳ La metà «e si riattacca a verificare» è della fase 5, ed è
dichiarata.

⛔ **Che cosa NON ha funzionato**: **Firefox non chiede mai la pagina** in questa sessione (5 giri,
149 s, **zero richieste HTTP**, causa non trovata) ⇒ lo strumento è stato sostituito con il testimone
Wayland nativo — ⭐ più vicino alla verità, ⛔ **ma il ponte con `deltaY` scende da `[M]` a `[S]`**.
E **tre difetti erano del banco**: il contatore dei ricambi cieco (accusava «non riprodotto» su un
difetto avvenuto), la prova del rilascio che girava dopo i ricambi e **accusava la cosa sbagliata**,
e — dopo la cura — il banco che **leggeva il `PRONTA` di ieri** e stampava un `NO` falso contro il
prodotto.

---

### ⭐⭐ A7 — la pagina, modo classico: **19 casi su 19**, due giri di fila

`[M]` 14 agosto 2026, Chrome 151, GNOME Wayland, pagina **isolata fra origini**. ⭐ **Il verdetto si
costruisce sui BYTE**, decodificati fuori dal browser da un lettore scritto leggendo `RCP.md` §7.3 —
**mai dal registro della pagina**. E il giudice è **certificato prima di ogni misura** (sano → otto
guasti → risanato).

| | |
|---|---|
| ⭐ **il caso del bordo** | spinto oltre con `Pointer Lock` esce **1919, 1079 e mai 1920**. ⚠ E l'attesa è **ricalcolata in Python** a cinque fattori di scala: a `1279×719` il valore vero è **1918,5**, dove `round`/`ceil` direbbero 1919 — cioè il banco sa distinguere l'arrotondamento giusto da quello che chiude la sessione |
| ⭐ **`Ctrl+C` copia** | `29↓ 46↓ 46↑ 29↑`, **zero `LETTERA`**; e `Maiusc+a` → **una** `LETTERA` U+0041 e **zero** posizioni |
| ⭐ **il rilascio alla perdita del fuoco** | fuoco tolto con una **scheda vera**: i due rilasci escono. A fuoco tenuto: **nessuno** |
| **la rotella** | +120 su, −120 giù, **+60 mezzo scatto**, e il segno invertito **una volta sola** (dal server) |

⛔⭐ **E la tesi 5 è metà refutata, con una misura**: l'`id` è confermato, ⛔ ma **la premessa
dell'`istante` in `RCP.md` §7.3 era FALSA** — `performance.now()` ha grana **5 µs**, non 1 ms:
**duecento volte** più fine. ⇒ La riga è stata corretta in `RCP.md` il 14 agosto: la regola
sopravvive alla premessa, ma un client che moltiplicasse i millisecondi per mille butterebbe via
**199 parti su 200** di una misura che ha già.

⛔ **Che cosa NON ha funzionato**: `unadjustedMovement` **rifiutato** da Chrome su Wayland (ripiego
dichiarato) · la lock è **negata senza fuoco** · ⚠ **tre rossi su tre erano del BANCO**, non del
prodotto (l'attesa sul bordo, `wheelDelta` che gonfia il mezzo scatto a uno intero `[M]`, e le fasi
marcate a tempo invece che a quiete) · **«e poi che cosa fa il desktop» non è misurato** · e **solo
Chrome**.

---

### ⭐⭐ A6 — il cursore: il canale aveva un capo e nessuna sorgente

| | |
|---|---|
| ⛔ **il `[R]` portato a `[M]`** | con la negoziazione di ieri: **62 buffer, 0 `SPA_META_Cursor`, 0 `CURSORE_FORMA`**. Lo stesso strumento con una riga in più: ⭐ **49 su 49**. ⇒ *Lo zero era uno zero, non una cecità* |
| ⭐ **il cursore NON è nell'immagine** | riquadro 96×96 sul puntatore fermo su tinta nota: **0 pixel** fuori tinta con `cursor-mode=2`, ⛔ **762** con `cursor-mode=1` — il controllo positivo sui pixel veri |
| ⭐ **la forma arriva, riletta dai byte** | 48×48 (attivo 6,2) · `0×0` nascosto · 48×48 al ritorno · 32×32 (3,1). **Zero violazioni** di §7.2/§5.5 |
| ⭐ **e non si rimanda mille volte** | 52 metadati ⇒ **4** forme (7,7 %); **40 movimenti ⇒ 0 forme nuove** |

⛔ **E una cosa che va dichiarata invece di inventata**: su un flusso appena aperto la forma **può non
arrivare mai** — `cursor_bitmap_invalid` nasce falso e si accende **solo** su `cursor-changed`
(43 metadati su 43 con la sola posizione). `cursore.c` lo **dichiara**, e non inventa una freccia.

---

### ⭐⭐ A8 — la pagina, modo tocco: **24 verdi su 25**, tre giri

`[M]` 14 agosto 2026, Chrome 151. Giudice certificato **verde → rosso → verde su 5 guasti**, uno per
**famiglia di confusione**; 78 messaggi §7.3 con `id` 1→78 crescenti.

⛔⭐ **E le tre confusioni che ha trovato, `DECISIONI.md` §5-bis.3 non ne nomina NESSUNA** — cioè la
tabella dei sette gesti descrive che cosa fare, non che cosa *si confonde con che cosa*:

| | |
|---|---|
| ⛔ **tap-e-mezzo e doppio clic sono lo stesso gesto** | ⭐ e la cura **non è una soglia**: *si preme al contatto e si rilascia al distacco*, e le due strade divergono da sole **senza ritardo**. ⚠ La stesura «prudente» — aspettare per decidere — **rompe il doppio clic**. Provato coi casi gemelli |
| ⛔ **«2 dita tap» contro «1 dito tap ripetuto»** | un **clic destro che esce come doppio clic sinistro**. ⛔ Nessuna soglia in ms li separa, e separarli costerebbe **300 ms su ogni clic** — vietati da `CODER.md` §1-bis. ⇒ La soglia è **una sovrapposizione: ≥ 1 campione**, e sotto quella il difetto è **DICHIARATO**, non nascosto |
| ⛔ **rotella contro pizzico** | che la tabella non nomina affatto: si confronta Δdistanza contro Δcentro, e si decide **una volta sola** |

**Le soglie, in ms e px CSS**: `T_TAP` **180 ms per CONTATTO** · `D_TAP` 9 px · `T_SEQUENZA` 300 ms ·
⭐ `D_STESSO_DITO` **40 px ≈ 10 mm** — e viene da `SPECIFICHE.md` §7.1: **lo stesso millimetraggio che
motiva il puntatore disegnato** separa il tap-e-mezzo dal tap a due dita · `D_PIZZICO` 24 px `[?]` ·
`PX_PER_SCATTO` 40 px `[?]`.

⭐ **Due difetti trovati dal banco e non dalla lettura**: la durata va misurata **per contatto** (o il
tap a tre dita **non esce mai**), e **un dito che si stacca sposta il centro di 40 px senza che
nessuno si muova** — veniva letto come rotella.

---

### ⭐⭐ A9 — le scorciatoie: **594 misure, 520 credibili, 74 buttate e CONTATE**

`[M]` 14 agosto 2026, Chrome 151 e Firefox 140 ESR.

> #### ⛔⛔ Lo stato di mezzo esiste, è misurato, **ed è LARGO**
> `[M]` **18 combinazioni su 42** su Chrome in finestra arrivano alla sessione remota **e** fanno
> agire anche il browser. ⇒ ⭐ *Una prova che avesse guardato solo il lato della sessione le avrebbe
> dichiarate **tutte verdi**.* È la ragione per cui §7.3-bis dice che la misura non è «arriva?» ma
> «arriva **e basta**?», e adesso quella riga ha un numero sotto.

**La ricetta, ogni gradino col suo numero:**

| gradino | Chrome 151 | Firefox 140 ESR |
|---|---|---|
| `preventDefault()` nella pagina | caso peggiore **18 → 0** | **15 → 0** |
| schermo intero **+ Keyboard Lock** | riservate dal browser **8 → 0** | ⛔ **impossibile**: non ha nessuna delle due forme, e a schermo intero **PEGGIORA** (5 → 7) |
| i bottoni a schermo | restano **5** | idem |

⛔ **E quel che resta perso non è del browser**: `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`, `Alt+F4`,
`Ctrl+Alt+Canc` — sono del **compositore del client**, e **nessuna API le riprenderà mai**.

⭐⭐ **E il giro salvato dalla regola di credibilità vale quanto la misura**: un giro di Firefox usciva
*«Firefox si tiene tutto, `Ctrl+C` compreso»* — **verosimile e interamente falso**, perché
`document.hasFocus()` ⛔ **mente su Firefox/Wayland**. ⇒ Da lì il cancello vero: **non si chiede alla
pagina se CREDE di avere il fuoco — le si chiede di DIMOSTRARE che riceve i tasti.** 74 righe su 594
buttate da quella regola, e **contate**.

⛔ **Non provati, e non dedotti** (ciascuno col suo strumento scritto nel rapporto): Safari/WebKit,
iPhone, **DeX**, **PWA su Chrome per Android**, Firefox ≥ 151, Edge. ⭐ La PWA è `[M]` **solo sul
desktop** (`--app`: **0 riservate già in finestra**); la metà Android resta `[?]`.

---

### ⛔⭐ E la quinta cucitura rotta della fase, trovata dall'anello che la subiva

`REMOTIX_PUNTATORE.muovi()` non accendeva `cl_noto` ⇒ su una pagina che nasce in **disposizione a
tocco** e non entra mai nel modo classico, il dito muoveva **un puntatore che non compariva mai** —
⛔ e senza nessun errore, da nessuna parte. Cura di **una riga**, chiusa dal coordinatore.
⭐ **E l'anello del tocco nel frattempo aveva fatto la cosa giusta**: ha verificato la cucitura, ha
**dichiarato il ripiego nel registro** e ha disegnato un puntatore suo — invece di tacere o di
rompersi. Il ripiego sparisce da sé adesso che la riga c'è.

⚠ ⭐ **Cinque cuciture rotte su cinque erano FRA due pezzi, e nessuna dentro uno.** È la lezione di
`fasi/rapporti/F5-desktop-vero.md` verificata cinque volte in una fase sola.

---

### ⭐⭐ A10 — il metro dell'anello **input → vetro**

| | |
|---|---|
| ⭐ **la certificazione** | **16 guasti innestati accusati su 16** · **53 controlli su 53** (uscita 0) · di cui il ponte **19 su 19** |
| ⭐ **tre guasti NUOVI**, che alla fase 3 non erano nemmeno esprimibili | e il più importante è *«la mediana sale di N ma **nel tratto sbagliato**»*: ⛔ **un metro così non diventa mai rosso — dice bugie sulla diagnosi**, che è esattamente quel che è successo all'etichetta del disegno |
| ⭐ **la catena in UNDICI tratti** (quattro nuovi) | provata sul finto che li somma al totale con scarto **0,00 ms** |
| ⛔ **e il numero NON c'è: `n = 0`, uscita 3** | *«non ho niente da giudicare»* — ⭐ **e dirlo è la cosa giusta**: il client non manda ancora §7.3. È il difetto che il validatore della fase 1 aveva (conforme e «niente da giudicare» con lo stesso codice d'uscita), qui evitato per costruzione |
| ⭐ **i pezzi ciechi sono DUE, non uno** | quello in uscita (16-40 ms, noto) e ⭐ **quello in INGRESSO** — `[?]` **4-12 ms** fra la mano e `event.timeStamp` — **che nessuno aveva mai nominato** |

⛔ **E il suo controllo di precondizione ha dato un FALSO VERDE**: cercava `0x0101` in `pagina.html`,
ne trovava cinque, ed erano **tutti commenti**. ⚠ *Pagata dentro il banco che esiste per non pagarla.*

---

### ⭐⭐⭐ O2 — IL NUMERO C'È: **~140 ms fra la mano e il pixel**, e sono **due giri che concordano**

*14 agosto 2026, pomeriggio. Rapporto in [`rapporti/F4-O2-anello-input.md`](rapporti/F4-O2-anello-input.md).*

`[M]` **139,40 ms** (n = **326 su 326**) e **141,60 ms** (n = **322 su 322**), due giri indipendenti
che concordano entro **2,2 ms** · p95 **190-195** · p99 **200-232**. ⛔ **Il tetto è 50 ms: si sfora
di quasi tre volte.** Coi due pezzi ciechi dichiarati: **160-193 ms sullo schermo di un utente, più
la rete.** ⚠ E sul prodotto di un'ora prima — senza la cura di O1 in `src/figlio.c` — erano
**151,17 ms** (n = 573).

⭐ **E la scomposizione dice che NESSUN TRATTO DOMINA** — la tesi 1 del mandato è **refutata**:

| tratto | ms | | tratto | ms |
|---|---|---|---|---|
| **5** cattura → primo byte *(codifica compresa)* | **30,4** | | **4** la scena disegna → cattura | **16,2** |
| **3** la scena riceve → disegna | **26,6** | | **1a** evento → il prodotto lo vede | **13,1** |
| **2** byte usciti → la scena riceve | **26,0** | | **8** la decodifica **vera** | **0,75** |
| **9** richiamo → 1° `drawImage` *(l'ATTESA)* | **25,6** | | **10** 1° → 2° `drawImage` *(il disegno VERO)* | **0,08** |

⇒ I **sei** tratti maggiori valgono fra **13,1 e 30,4 ms** e fanno il **99 %**: curarne uno solo
toglie al massimo il **22 %** del ritardo, e il tetto resterebbe sforato di due volte e mezzo.
⚠ La codifica sta **dentro** il tratto 5 e vale **5,3 su 30,4**; la **decodifica** vale **0,75 ms**:
«il collo di bottiglia è la codifica» resta falsa, e adesso con un numero sotto.
⭐ **E la scomposizione è ripetibile quanto il totale**: nessun tratto si sposta di più di **1,6 ms**
fra i due giri.

⭐⭐ **E i tratti che il metro della fase 3 NON attraversava** (1a + 1b + 2 + 3) valgono **65,8 ms**,
cioè **il 47 %**: ⛔ *il numero della fase 3 non vedeva quasi metà del ritardo che l'utente sente.*

> #### ⛔⛔ E IL DIFETTO PIÙ GRAVE NON È UN TRATTO: È UNA CODA CHE CRESCE
> `[M]` il server consegna **39,6** fotogrammi/s, la pagina ne dipinge **34,7**, e ⛔ **nessuno
> butta l'avanzo** (`scartati_ordine` 0 · `trattenuti` 0 · `corti` 0). ⇒ Il ritardo cresce di
> **+108 ms al secondo**: 31,6 ms dopo 1 s → **4 650 ms dopo 43 s**. **Dopo un minuto l'utente
> comanda un desktop che ha visto sei secondi fa, e tutti i contatori sono verdi.**
> ⭐ **Curato** in `src/pagina.html` (ancora `F4-CODA-DEL-DECODIFICATORE`): si salta **il disegno**,
> non la decodifica — nessun buco, nessuna chiave. `[M]` dopo: pendenza **−2 ms/s**, ritardo **1,3
> ms** dopo 41 s.

> #### ⛔ E LA TESI 2 — *«il ritmo è quanto ci consegna Mutter»* — **REFUTATA in questo regime**
> `[M]` quattro conti nella stessa finestra di 30 s: la scena disegna **59,99/s**, Mutter ce ne
> consegna **30,84** (il 51 %), il server ne spedisce **30,54**, la pagina ne dipinge **30,6** —
> ⭐ e le **attese a vuoto sono 0,00/s**: ogni volta che abbiamo chiesto un fotogramma ce n'era già
> uno pronto. ⇒ **Non stiamo aspettando Mutter: il limite è nel nostro ciclo.**
> ⚠ `[?]` I 10,8/s che l'utente ha misurato dal suo video sono su un desktop **vero**, cioè in
> regime di scarsità: le due misure rispondono a due domande diverse.

> #### ⛔⛔ E LA TESI 3 (tastiera contro mouse) NON È CHIUSA — ⭐ e a dirlo è **la scomposizione**
> `[M]` ultimo giro: **35 sonde chiuse su 296**, mediana **151,7 ms** contro i **141,6** del mouse
> nello stesso giro. ⚠ Verosimile: *«la tastiera è 10 ms più lenta»*. ⛔ **È falso**, e la prova è
> che la sua scomposizione **non è fisica**: `2 byte usciti → la scena riceve` = **−562,8 ms**,
> negativo. ⇒ L'accoppiamento prende il fotogramma sbagliato, e **il totale da solo non lo direbbe
> mai**: è il **guasto n. 12 della certificazione di A10** visto dal vivo.
> ⇒ ⛔ **Il numero non è stato pubblicato.** Serve un eco della tastiera che non si sovrascriva
> (lavoro mio su `04-b30-scena.c`).

⭐ **Quel che invece è `[M]` e regge: il cammino della tastiera arriva al compositore** — `Escape`
mandato dal canale del prodotto **chiude la Panoramica di GNOME**, quattro volte su quattro,
verificato nei pixel; e la scena riceve **744** eventi di tastiera in un giro.

⭐⭐ **E Q6 — il controllo del ramo d'ANDATA, che alla fase 3 non poteva esistere — PASSA sul ferro**:
iniettando 30 ms il totale sale di **30,84** e il surplus compare **tutto nel tratto 2** (+33,49) e
**in nessun altro**. ⇒ Metà dell'anello che non aveva nessuna taratura adesso ce l'ha.
⛔ Q5 (ramo di ritorno) resta rosso **per 0,2 ms**: il surplus sta nel tratto giusto (+24,70 contro
N = 25) ma il totale sale di 20,78. ⚠ **La tolleranza non è stata allargata.**

**⛔ E i tre difetti che tenevano `n = 0` erano tutti del banco o del contorno, nessuno del canale:**

| | |
|---|---|
| ⛔⛔ **la Panoramica di GNOME** | una sessione headless appena nata si apre in Panoramica: la scena «a schermo intero» era **una miniatura a 0,79** e la Panoramica teneva il fuoco. ⇒ `eventi_puntatore = 0` (diagnosi suggerita: «`libei` non consegna») **e** 0 marche lette su 966 (diagnosi suggerita: «l'eco non si legge»). ⭐ **A trovarlo è stato guardare l'immagine**, non leggere un numero |
| ⛔ **`04-b30-scena.c`: `oy` sommato due volte** | le celle della **seconda** marca finivano fuori dalla loro zona di quiete, sullo sfondo del desktop. Sulla marca 1 (`oy = 0`) non si vedeva. ⭐ E la certificazione era verde 53 su 53: **i sedici guasti si innestano nel verbale, e nessuno dipinge un pixel** |
| ⛔ **il controllo di precondizione di A10, falso ROSSO** | cercava i ganci in `figlio.c`; stanno in `webtransport.c` (il canale è del **padre**). ⚠ Stamattina lo stesso controllo aveva dato un falso **verde**: adesso guarda tutt'e due i lati del confine |

---

### ⭐ A5 — la tastiera: **26 prove, 0 rosse** `[M]` 14 agosto 2026

Identiche in locale e nel contenitore (`xkbcommon` 1.7.0 su tutt'e due). Si ricontrolla con
`bash banchi/04-b25-lancia.sh` — ⭐ **senza sessione, senza `libei` e senza nessuna porta**.

| | |
|---|---|
| ⭐ **il metro è la lettera che ESCE** | non il codice che parte: il banco simula il compositore su una `xkb_state` costruita da sé e **legge il carattere** |
| ⭐ **e ha un controllo negativo** | tasto 26 **senza** Maiusc ⇒ `è`, non `é`. Senza di lui, un simulatore compiacente avrebbe dato verde anche a chi dimentica i modificatori |
| **le tre prove che `PIANO.md` nomina** | `é` su `it` ⇒ `42+26`, esce `é` · `é` su `us` ⇒ ⛔ **niente**, e la riga nel registro · `@` per due strade: `100(AltGr)+16` su `it`, `42(Maiusc)+3` su `us` · emoji e `中` non producibili ovunque |
| ⭐ **il banco è CERTIFICATO** | tre implementazioni sbagliate apposta, e il lanciatore pretende **ROSSO sulla prova giusta**: quella che manda `e` al posto di `é` è rossa |
| **il ripiego non è silenzioso** | `[M]` `xkbcommon` 1.7.0 **non ripiega da sé** (ritorna NULL), e `tastiera_disposizione()` dice `it [Italian]` ⇒ un ripiego entrato da altrove si leggerebbe nel registro come `it [English (US)]` |

⛔ **E tre misure hanno cambiato il codice** — cioè il banco ha lavorato:

| | |
|---|---|
| ⛔ **evdev 84 non esiste** | la prima stesura sceglieva per l'AltGr italiano un codice che **non è in `linux/input-event-codes.h`** (c'è un buco fra 83 e 85). ⚠ **Il banco era VERDE**: dal lato che riceve quel codice funziona. Trovato **guardando il numero**, non dal banco. Ora esce `100` |
| **`de(neo)`** | `√` vuole `100+43+17`, e il terzo livello lì è il tasto **43**, non il `100` che v1 aveva scritto a mano. ⭐ E la stessa misura risponde alla domanda implicita del contratto: **quattro posizioni bastano**, il caso peggiore ne usa tre |
| il Maiusc | usciva **destro**; ora sinistro |

### ⛔⛔ E il contratto della tastiera era SBAGLIATO — il rifiuto è stato accolto

*`src/tastiera.h` diceva: «la disposizione è la stringa negoziata all'attacco». L'anello l'ha
attuata, ha visto che funzionava, **e l'ha rifiutata lo stesso** — con la ragione giusta.*

⛔ **Non scegliamo noi la disposizione della sessione: la sceglie GNOME, e `libei` ce la CONSEGNA**
col dispositivo tastiera. Il danno, in concreto — sessione `it`, client che ha negoziato `us`,
l'utente scrive `[`:

| | |
|---|---|
| su `us` | `[` sta sul tasto **26**, da solo |
| su `it` | sul tasto **26** c'è la **`è`**, e `[` vuole l'AltGr |

⇒ Mandiamo `26` e sullo schermo compare **`è`**: ⛔ non un carattere *mancante* — **un carattere
DIVERSO**, che `RCP.md` §7.3 vieta. E nessuno collegherebbe il sintomo alla disposizione.
⚠ **E rende falsa una riga che credevamo vera**: `DECISIONI.md` §5-bis.7 dice che la degradazione è
morbida — *«mai caratteri sbagliati, al massimo un paio di accenti irraggiungibili»*. È vero **solo**
usando la keymap della sessione.
⭐ **E v1 lo faceva già così** (`v1/remotix-c/src/tastiera.c:69`): è l'unico pezzo di v1 che il primo
contratto di V2 non aveva ripreso.

⇒ ✅ **Accolto il 14 agosto 2026**: `tastiera_apri_da_keymap()` è in `src/tastiera.h`, e
`input_apri()` **non** prende la disposizione — la keymap arriva da `libei` dentro `input.c`, a ogni
`DEVICE_ADDED`.

---

## ⛔ Che cosa NON ha funzionato

⏳ *si riempie anche quando fa una brutta figura.*

---

## Le decisioni prodotte

⏳ *le decisioni stanno in `DECISIONI.md` una sola volta: qui si **rimanda**.*

---

## Che cosa resta [?]

Aperte all'apertura della fase, e vanno **misurate prima di essere credute**:

1. ~~chi decide la misura del monitor ora che non la dà più la sessione~~ ⇒ ✅ **CHIUSA il
   14 agosto 2026, e la risposta era un'altra da quella che la domanda supponeva**: ⛔ **non la
   decide `RecordVirtual` — la decide il NOSTRO formato PipeWire** `[R]`. E la promessa della tela
   concessa **oggi nessuno la mantiene**: `[M]` client a 1280×720 ⇒ il server la concede, il palco
   cattura a 1920×1080 (costante di compilazione), `rcp` rifiuta ogni fotogramma — **145 prodotti,
   0 spediti, client nero senza errori**. ⏳ La cura è lavoro della fase 6 (`RCP.md` §4.5);
2. ⚠ `PIANO.md` **399, 402-404, 591-593** e `gnome.md` **108-109, 111-112, 551** dicono che
   `--virtual-monitor` **non è opzionale**: ⛔ sono vere solo per una sessione che deve vivere
   **senza nessuno che la catturi**, e vanno riscritte. *(Righe individuate da A1, non toccate da
   lui: si riscrivono a codice fermo.)*
3. `[?]` la Keyboard Lock su **DeX**, e la PWA su **Chrome per Android** (`SPECIFICHE.md` §7.3-bis);
4. `[?]` il segno della rotella sugli **altri quattro** compositori (`RCP.md` §7.3);
5. ⭐ **CHIUSA il 14 agosto 2026 — la persistenza al distacco REGGE**, e la tesi del difetto è
   **falsa**: il monitor non sparisce (sempre 1, anche senza nessuno), l'applicazione lavora
   (1 160 righe in 240 s senza un buco), `libmutter` non scrive asserzioni nuove, e al riattacco
   si ritrova **la stessa finestra** (pid invariato), due volte di fila. ⚠ **Ma il palco muore col
   FIGLIO, non con la sessione**: chi congederà un figlio che gira a vuoto toglierebbe il monitor a
   una sessione viva — ⏳ **fase 5**;
6. ⛔ **aperta il 14 agosto, e nessuno l'aveva posta**: se la sessione ha `us` e il client ha
   negoziato `it`, **chi cambia la disposizione della sessione?** `DECISIONI.md` §5-bis.7 dice che
   si rinegozia all'attacco — ⚠ ma un client `libei` **non può imporre una keymap all'EIS: la
   riceve**. ⇒ O la si cambia dalla sessione (`org.gnome.desktop.input-sources`, prima di
   attaccare), oppure §5-bis.7 va riscritta come *«il client **dichiara**, il server **si adegua a
   quel che trova**, e lo dice»*. `[?]` — nessuno l'ha misurato.

---

## Il giudizio dell'utente — ⭐ DATO il 14 agosto 2026

> ## *«Mi sembra ok.»*
> — l'utente, 14 agosto 2026, dopo aver usato il desktop di `prova` dentro una scheda di Chrome
>
> e, poco prima, sulle due cose che aveva chiesto di ottimizzare:
> > *«La situazione mi sembra migliorata. La comparsa del desktop è più immediata.»*

⭐⭐ **E la fase si chiude qui**, come `PIANO.md` §0.2 impone: *«su una misura giudicata dall'utente,
non su un documento completo»*.

### ⭐ Che cosa il giudizio ha confermato, e con quale numero accanto

| la sua frase | il numero che le corrisponde |
|---|---|
| *«la comparsa del desktop è più immediata»* | `[M]` **5,11 s → 1,04-1,13 s** (7 giri) — e di quel secondo, **1,00 s è il secondo fisso di §4.4-bis**: ⭐ quel che è nostro sono **34-124 ms** |
| *«mi sembra ok»* (dopo qualche minuto d'uso) | `[M]` il ritardo **non cresce più**: pendenza da **+108 ms/s a −2 ms/s**, e **1,3 ms** dopo 41 s |

### ⛔ E i limiti del giudizio, scritti PRIMA che lo desse e non dopo

*Gli sono stati messi davanti in tavola prima della prova — «un giudizio dato senza sapere che cosa
manca è un'approvazione al buio», la stessa regola con cui ha chiuso la fase 2.*

| | |
|---|---|
| ⛔ **il ritardo SFORA** | `[M]` **139,40 ms** (n=326) contro un tetto di **50**. ⚠ Ha giudicato **con gli occhi**, non su quel numero — e i due non si sostituiscono |
| ⛔ **nessun tratto domina** | sei tratti da ~25 ms: **nessuna cura singola** porta 140 a 50. È lavoro della **fase 8**, e va detto perché il giudizio non venga letto come «il ritardo è a posto» |
| ⛔ **la tela non è la sua** | il suo schermo è **21:9**, il desktop remoto **16:9** ⇒ `[M]` dal suo video, **il 36 % dei pixel è banda nera**. Ha giudicato una finestra, non uno schermo pieno |
| ⚠ **un browser solo** | **Chrome 151**. Safari, iPhone e DeX restano `[?]` **dichiarate, non dedotte** |
| ⚠ **qualche minuto, non qualche ora** | i tre orologi della sessione sono della **fase 5**: l'abbandono lungo non è stato giudicato |

### ⭐⭐ E il giudizio dell'utente ha trovato SETTE difetti che nessuno dei dieci banchi vedeva

*Non è un aneddoto: è il conto della giornata, ed è la ragione per cui il piano fa chiudere le fasi
così.*

| che cosa ha detto | che cosa c'era sotto |
|---|---|
| *«se il server non mostra il desktop, a che serve REMOTIX?»* | il monitor aggiunto e vuoto — **due fasi** l'avevano preso per uno sfondo |
| *«non si vede nessun desktop»* | **due server nostri** che montavano un monitor a testa sulla stessa sessione |
| *«lo schermo appare strano»* | la dichiarazione delle scorciatoie che copriva il **38 %** della finestra |
| *«non vedo il drawer di gnome»* | la barra piazzata **esattamente dove GNOME tiene il dock** |
| *«il puntatore sembra catturato… studia XPRA»* | ⭐ `SPECIFICHE.md` §7.1 che contraddiceva §7.5: la cattura **non comprava niente** |
| *«niente desktop»*, due volte | il figlio che tiene per sempre **un palco fallito** |
| *«il tempo fra login e desktop è troppo lungo»* | ⛔ **una riga del coordinatore**: `poll()` su due descrittori e `pf.revents` mai guardato |

⛔ **Sette su sette stavano FRA i pezzi, nessuno dentro uno** — ed è la lezione di
`fasi/rapporti/F5-desktop-vero.md` verificata sette volte in una giornata sola.

---

## ⭐⭐ Il numero della fase — `[M]` 14 agosto 2026

*L'anello **input → vetro**, che alla fase 3 non era misurabile: il campo `input` valeva 0 in 953
fotogrammi su 953, perché il canale non esisteva.*

| | |
|---|---|
| ⭐ **il numero** | **139,40 ms** (n = 326 su 326) e **141,60 ms** (n = 322 su 322), ⭐ **due giri indipendenti che concordano entro 2,2 ms** |
| ⚠ **coi pezzi ciechi** | **160-193 ms** sullo schermo dell'utente, **più la rete** |
| ⛔ **contro il tetto** | **50 ms**. Si sfora di quasi **tre volte**, e si scrive com'è |

### ⭐ La scomposizione, e la risposta a «che cosa ottimizzo?»

| tratto | mediana |
|---|---|
| cattura → primo byte | **30,4 ms** |
| la scena riceve → disegna *(è il desktop remoto, non noi)* | 26,6 |
| byte → scena | 26,0 |
| richiamo → primo `drawImage` | 25,6 |
| disegno → cattura | 16,2 |
| decodifica | 0,75 |
| ⭐ **il `drawImage` vero** | **0,08** |

⇒ ⛔ **Nessun tratto domina**: sono sei tratti da ~25 ms. **Nessuna cura singola porta 140 a 50.**
⭐ La somma dei tratti fa **139,08** contro un totale di **139,40** — scarto **0,32 ms**: la
scomposizione è completa, non ha buchi.
⭐⭐ **E i tratti che il metro della fase 3 NON attraversava valgono 65,8 ms, il 47 %**: metà del
ritardo vero stava fuori dal vecchio metro.

> ### ⭐⭐ E la prova sul ferro che l'etichetta corretta stamattina era giusta
> Il **primo** `drawImage` costa **25,6-27,1 ms**, il **secondo 0,080** ⇒ **320-339 volte**.
> ⛔ *Il disegno non è mai stato caro: era l'attesa del fotogramma dalla GPU.*

---

## ⭐⭐ Le due ottimizzazioni chieste dall'utente — e tutt'e due erano NOSTRE

### 1. Il login → desktop: **5,11 s → 1,04-1,13 s**

⛔⛔ **E la causa era una riga del coordinatore, scritta la mattina stessa.** Per far arrivare
l'input più in fretta era stato messo il descrittore di `libei` nello stesso `poll()` del figlio —
⛔ ma il codice dopo **non guardava `pf.revents`**: svegliandosi per `libei`, il figlio andava lo
stesso a leggere il socket del padre, **bloccante**.
⇒ *Una modifica fatta per risparmiare millisecondi sull'input costava **quattro secondi** al login.*
⭐ **La cura è una riga**: `if (!pf.revents) break;`

⚠ **E il registro lo diceva già**: *«0 fotogrammi consegnati, **0 attese a vuoto**»* — zero attese a
vuoto vuol dire che il ciclo **non aveva nemmeno provato** a catturare. ⛔ Era scritto, ed è stato
letto due volte come «la scena è ferma». *Il difetto ha resistito a due sonde leggere che davano
risposte opposte: l'ha chiuso solo un debugger attaccato al processo.*

### 2. ⭐⭐ E il ritardo CRESCEVA senza limite, con tutti i contatori verdi

`[M]` il server consegnava **39,6 fotogrammi/s**, la pagina ne dipingeva **34,7**, e **nessuno
buttava l'avanzo**: `scartati_ordine 0 · trattenuti 0 · corti 0`.

| | |
|---|---|
| la crescita | ⛔ **+108 ms al secondo** |
| dopo 43 s | ⛔ **4 650 ms** — si comandava un desktop visto **sei secondi prima** |
| ⭐ curato | pendenza **−2 ms/s**, ritardo **1,3 ms** dopo 41 s |

⇒ ⛔ **È il difetto che l'utente sentiva e che nessun contatore contava**: tutti verdi, e la coda del
decodificatore che si allungava e basta.

### ⭐ E i due difetti che potevano rovinare una macchina vera

| | prima | dopo |
|---|---|---|
| il registro a raffica | **151,9 MB/s** (⛔ `[M]` **30,8 GB** scritti in una mattina) | **284 B/s** |
| un nucleo bruciato a vuoto | **1,00** | **0,00** |
| il desktop dopo che la sessione grafica torna | ⛔ **non tornava mai** | ⭐ **1,11 s, stesso figlio** |

⚠ ⭐ **E il ciclo a vuoto ha DUE facce, e una è MUTA**: per questo il banco misura il registro **e**
la CPU. E con un client muto **un difetto ne nasconde un altro** — serve un client che *chieda le
chiavi*, come fa un client vero che non vede niente.
