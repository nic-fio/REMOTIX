# F4-A3 — Il filo dell'input

*Anello **A3** della fase 4, 14 agosto 2026. `RCP.md` §7.3 dal lato del filo: decodifica,
convalida e consegna dei cinque messaggi di input, e il campo `input` dei fotogrammi (§6.2).*

---

## 1. Che cosa cambia per l'utente

**Niente, ancora — e la ragione è una cucitura che non è mia** (punto 5). Quel che c'è adesso è la
metà del canale di input che sta nel protocollo: `rcp.c` sa leggere `PUNTATORE`, `PULSANTE`,
`ROTELLA`, `LETTERA` e `POSIZIONE_TASTO`, sa rifiutare ogni loro violazione con il motivo giusto, e
sa consegnare l'azione a `input.h`. ⛔ Ma i byte non gli arrivano: `src/webtransport.c` oggi il
canale di input lo riconosce come lecito e **scarta i suoi byte** (`G_UNI_OK`, riga 1883-1898), e
quel file non è di questo anello.

Quel che l'utente **si porta a casa** quando la cucitura c'è, e che senza questo anello non avrebbe:

| | |
|---|---|
| ⭐ **il bordo dello schermo si può cliccare** | su una tela 1920×1080 il pixel `(1919, 1079)` passa. `[M]` — ed è il caso su cui `RCP.md` §7.3 ha già un rilievo scritto contro di sé (**R1.16**) |
| ⭐ **una finestra ridimensionata non stacca la sessione** | il secondo di grazia di §7.1: un puntatore partito prima che il `TELA` arrivasse viene **saturato**, non usato per chiudere. `SPECIFICHE.md` §8.3 — «mai staccare» |
| ⭐ **lo scorrimento fine funziona** | 60 unità sono mezzo scatto e arrivano come 60. `[M]` |
| ⭐ **la rotella non va al contrario** | `rcp.c` **non** inverte il segno: lo inverte `input_rotella()`, una volta sola (§7.3, riquadro `[M]` 10 ago). Due inversioni si annullano, ed è la forma E11 |
| ⭐ **nessun Ctrl rimasto giù** | §7.3 «al distacco si rilascia tutto», chiamato su **quattro** strade — congedo, congedo del client, canale chiuso, pagina chiusa — più il silenzio di §5.3 e `rcp_libera()` come ultima rete. `[M]` esattamente **una** volta per sessione |
| ⭐ **muovere il mouse tiene viva la sessione** | l'orologio del silenzio di §5.3 si azzera anche sui byte dell'input. `[R]` Senza, chi usa il desktop **senza scrivere** perdeva il posto dopo trenta secondi |

---

## 2. Serve una decisione di Nic?

**No.** Nessuna scelta di prodotto è rimasta aperta. Ci sono **tre `[?]` da misurare, non da
decidere** (punto 4), e **cinque cuciture da chiedere al coordinatore** (punto 5).

⚠ Una sola cosa è una **scelta mia, dichiarata**, e la nomino perché Nic la possa ribaltare se
vuole: `RCP.md` §7.3 dice che l'`id` «cresce di almeno uno» e **non dice cosa succede al giro dei
2³²**, mentre per il `numero` dei fotogrammi §6.2 lo dice per esteso. Ho scelto la lettura
letterale — crescita stretta, e al giro la sessione cade con `ERRORE_PROTOCOLLO` — invece di
inventare un'aritmetica modulare che il documento non scrive. `[S]` A mille input al secondo il
caso arriva dopo **49 giorni** di sessione continua. ⛔ Inventare la tolleranza sarebbe stato
inventare una nona eccezione a §3, che §3 vieta: la riga giusta è in `RCP.md`, non qui.

---

## 3. Che cosa ho MISURATO

### Il banco, e il denominatore dichiarato

`banchi/04-b23-filo-input.c` manda i byte e **non giudica niente**;
`banchi/04-b23-filo-input.py` tiene le previsioni e giudica. Due programmi, due linguaggi, nessuno
dei due importa l'altro (`RCP.md` §0).

⛔ **I byte si consegnano UNO ALLA VOLTA**, e ogni violazione dichiara **in anticipo su quale byte**
deve essere accusata. È la colonna che distingue un server che giudica l'intestazione da uno che
accumula il corpo e poi si accorge — cioè che ha già regalato il megabyte che §6.1 gli vieta.

| misura | `[M]` 14 agosto 2026 | denominatore |
|---|---|---|
| violazioni accusate **sul byte dichiarato** | **29** | / 29 |
| violazioni col motivo giusto (`ERRORE_PROTOCOLLO`) **in `CONGEDO`** | **29** | / 29 |
| §3.1 punto 3 — motivo dentro il codice di chiusura | **29** | / 29 |
| ⭐ **verdi attesi**, sessione viva | **25** | / 25 |
| ⭐ verdi attesi, **iniettato esattamente quel che si doveva** (valore per valore) | **25** | / 25 |
| ⭐ §6.2 — il campo `input` letto dai **28 byte veri** del fotogramma | **4** | / 4 |
| ⛔ dopo ciascuno, **una connessione nuova fino a `ECCOMI`** | **54** | / 54 |
| §7.3 — rilascio al distacco, **una** volta per sessione | **53** | / 53 |

⛔ **29 violazioni e 25 verdi attesi: 54 casi.** I due numeri li calcola `conta()` dalle previsioni;
nessun commento li riscrive a mano (rilievo R7.14 — tre numeri scritti a mano, nessuno dei tre
tornava).

⚠ **Perché i verdi attesi valgono quanto le violazioni**: senza di loro «il server chiude su
tutto» darebbe verde su tutto. E non basta che la sessione regga — si guarda **la lista esatta,
in ordine, di quel che i cinque ganci hanno ricevuto**: un server che accettasse ogni messaggio e
non iniettasse mai niente avrebbe lo stesso conteggio.

### ⭐ Il banco è CERTIFICATO — e questa è la misura che conta di più

Un banco passato al primo giro non ha dimostrato niente (`CODER.md` §3.4). `banchi/04-b23-guasti.py`
rompe `banchi/rcp/rcp.c` in **12 modi noti**, uno per giro, e pretende che B23 diventi rosso
**esattamente sui casi dichiarati** — non «da qualche parte» e non «su tutto».

`[M]` **12 guasti su 12**, e prima di tutti il controllo positivo: col sorgente sano, 54 verdi su 54.

⛔ **Il guasto che certifica la colonna del byte** è `lunghezza-tardiva`: sposta il controllo della
lunghezza dopo l'arrivo del corpo. Il motivo resta giusto, il `CONGEDO` parte, il codice di
chiusura è quello, la sessione muore — **un banco che contasse le violazioni resterebbe verde**. A
cambiare colore è la sola colonna «su quale byte», su cinque casi.

⭐ **E la certificazione ha trovato due cose che nessun giro verde avrebbe trovato**, tutte e due
riportate al punto 4.

### Dove si ricontrolla

```
bash banchi/04-b23-lancia.sh          # gemello → certificazione → giro vero
python3 banchi/04-b23-filo-input.py --elenco   # le 54 previsioni, senza misurare
python3 banchi/04-b23-guasti.py --elenco       # i 12 guasti e i rossi attesi
```

| | |
|---|---|
| la traccia depositata | `banchi/04-b23-esiti.jsonl` — 54 righe, una per caso |
| il bersaglio | `banchi/rcp/rcp.c` compilato **in processo**, cioè lo stesso sorgente di `src/rcp.c`, confrontato byte per byte dal `Makefile` |
| `[M]` **due macchine** | qui (`cc` locale) e nel contenitore di **192.168.0.2** (`cc` Debian 14.2.0, Python 3.13.5): **stessi numeri** |
| `[M]` il prodotto compila | `make rcp.o` con le opzioni vere del `Makefile`: pulito, zero avvertimenti. E il controllo `GEMELLATI` passa su tutt'e tre i file |

### Le tre tesi che dovevo refutare

| tesi | esito |
|---|---|
| 1. *«ogni violazione di §7.3 è rifiutata col motivo GIUSTO, per tutt'e due le strade di §3.1»* | ⭐ **non refutata** — 29/29 sul byte dichiarato, 29/29 in `CONGEDO`, 29/29 nel codice di chiusura. ⚠ Il motivo è **sempre** `ERRORE_PROTOCOLLO`: §7.3 non ne prevede altri, e le due strade portano lo stesso byte |
| 2. *«fuori tela chiude, salvo la grazia; e 1919 su 1920 passa»* | ⭐ **non refutata** — e il guasto `bordo-stretto` mostra che il banco lo vedrebbe. ⛔ **Con un di più che non mi aspettavo**: la cura ingenua del bordo (`x + 1 < tela_l`) manda `0xFFFFFFFF + 1` in overflow a `0`, e **la coordinata più sbagliata di tutte diventa la più accettabile**. Il banco lo dice da sé perché dichiara l'insieme **esatto** dei rossi invece di «almeno questi» |
| 3. *«l'`id` cresce su TUTTO il canale, non uno per tipo — e il campo `input` torna indietro coerente»* | ⭐ **non refutata**. Il caso che separa le due implementazioni è uno solo ed è nel banco: `PULSANTE(9)` e poi `PUNTATORE(4)` — con cinque contatori per tipo quel 4 è un legittimo «primo PUNTATORE» e **passa**. `[M]` il campo `input` letto all'offset 24 dei 28 byte veri: **9** dopo gli id 1, 2, 5, 9 |

⭐ E il campo `input` porta **l'ultimo INIETTATO, non l'ultimo ricevuto**: due casi lo provano dal
lato scomodo — il gancio che risponde `-1`, e la `LETTERA` non producibile — e in tutt'e due il
fotogramma porta `0` mentre l'`id` accettato era 7 e 3. Il guasto `campo-input-su-ricevuto` li fa
diventare rossi.

---

## 4. ⛔ Che cosa NON ha funzionato

### ⛔ Un difetto MIO, trovato dalla certificazione e non dal banco

`if (s->inp_acc_len < 6u + lung)` — `lung` è `uint32_t`, quindi **la somma si calcola a 32 bit**: con
`lung = 0xFFFFFFFF` il risultato non è 4 294 967 301, è **5**. Un ricevente che ci arrivasse
crederebbe il corpo completo dopo sei byte e leggerebbe quattro gigabyte di memoria altrui a
partire da un accumulo di 32.

⚠ **Non era raggiungibile** — il controllo `lung != attesa` sta tre righe sopra e chiude prima — ma
«non raggiungibile oggi» e «non pericoloso» sono due fatti diversi: chi domani spostasse quei due
`if` rimetterebbe la lettura fuori dai limiti senza che niente cambiasse colore. Corretto con
`(size_t)6u + lung`, e il commento accanto dice perché.

⛔ **E il modo in cui è saltato fuori è il punto**: il guasto `lunghezza-tardiva` doveva far
diventare rossi cinque casi e ne faceva quattro. `lunghezza-4gib` restava verde **per via
dell'overflow**. Un catalogo scritto con «almeno questi rossi» non se ne sarebbe accorto.

### ⛔ Il banco NON gira sul filo vero, ed è una lacuna dichiarata

I byte entrano da `rcp_ricevi_input()` chiamata in processo, non da uno stream WebTransport.
⇒ **Non è provato** dal lato che riceve *sul filo*: il preambolo di WebTransport (`40 54` + numero
di sessione, rilievo **P18**), la vera capsula di chiusura, e il comportamento sotto perdita di
pacchetti. La ragione è al punto 5, cucitura **(a)**: senza quella riga in `webtransport.c` non c'è
niente da mettere in rete, e le porte 7621-7625 che mi erano assegnate **sono rimaste libere**.

⚠ Quel che invece è provato per intero: §7.3, §6.1, §6.0, §2.5 e §3.1 **sullo stesso sorgente** che
il prodotto compila.

### ⛔ Il prodotto non si collega su questa macchina

`make` si ferma su `main.o` con `nghttp3/nghttp3.h: File o directory non esistente`. ⚠ **Non è mio e
non è di questa fase**: è l'ambiente del portatile, non del contenitore, e cade prima di arrivare a
qualunque file della fase 4. `make rcp.o` con le opzioni vere passa.

### Tre `[?]` che restano, e vanno misurate prima di essere credute

1. `[?]` **il giro dei 2³² dell'`id`** — vedi il punto 2: la riga giusta manca in `RCP.md` §7.3, non
   nel codice;
2. `[?]` **i codici evdev non sono convalidati per intervallo.** §7.3 dà i codici (`BTN_LEFT` = 0x110,
   `KEY_A` = 30) e **non dà un intervallo**; `KEY_MAX` di evdev è 0x2FF. ⛔ Ho scelto di **non**
   inventare un limite: sarebbe stata una regola mia travestita da regola dell'arbitro. ⇒ Un codice
   inesistente arriva a `input.c`, che lo rifiuterà — e la riga di registro lo dirà. Da chiudere in
   `RCP.md`, non qui;
3. `[?]` **§7.3 non dice che cosa sia un FIN sullo stream di input**, che «si tiene aperto». Non ho
   messo nessuna regola: oggi un FIN lo vede solo l'ospite e non arriva fin qui.

---

## 5. Le cuciture che chiedo al coordinatore

### (a) ⛔ `src/webtransport.c` — i byte dell'input non arrivano a `rcp.c`

È **la cucitura che blocca tutto il resto**. Oggi `smista_uni()` classifica il canale `0x01` come
`G_UNI_OK` e i suoi byte finiscono in `conta_credito()` e basta (righe 1883-1898 e 1948-1950).

Serve, nel ramo `G_UNI_OK`, di distinguere il canale `0x01` dal `0x02` e chiamare:

```c
bool rcp_ricevi_input(rcp_sessione *s, int64_t stream, const uint8_t *dati,
                      size_t len, uint64_t ora_ms);
```

⛔ `stream` è l'identificatore dell'ospite, **e serve davvero**: §2.5 dice «uno solo», e senza un
identificatore `rcp.c` non può distinguere il secondo stream di input dalla continuazione del primo.
⚠ `false` vuol dire «sessione finita», esattamente come `rcp_ricevi()`, e va trattato allo stesso
modo (`webtransport.c:1539` ha già la forma).
⛔ E i byte da passare sono **quelli del carico RCP**, cioè dopo il preambolo di WebTransport — è
il rilievo **P18**, e `smista_uni()` quel preambolo lo consuma già.

### (b) ⛔ `src/input.h` — la riga del contratto che è sbagliata, e il `Makefile` lo dimostra

L'intestazione di `input.h` dice: *«Chi legge questo file: `rcp.c` — decodifica i messaggi di
`RCP.md` §7.3 e **chiama queste funzioni**»*.

⛔ **Non si può fare**, e non è una preferenza di stile. `rcp.c` esiste in **due cartelle** e il
`Makefile` (variabile `GEMELLATI`) pretende che combacino byte per byte; la seconda copia la
porta `banchi/01-b3-rcp-innesta.py` dentro `examples/` di ngtcp2, e quel file elenca **tre nomi**
(`rcp.c`, `rcp.h`, `autenticazione.c`). Un `#include "input.h"` in `rcp.c` **non compila l'innesto**,
cioè spegne B3, B5, B6, B8 e B11 in un colpo solo.

⇒ Ho seguito **la forma che c'è** — la stessa che `rcp.h` usa già per PAM e per gli stream: sei
ganci in `rcp_ganci`, con **le firme di `input.h` campo per campo**. `figlio.c` li collega, ed è
proprio il file che `input.h` nomina come quello che «cuce i due».

```c
/* in rcp_ganci, gia' aggiunti in `src/rcp.h` — servono i sei adattatori */
int (*input_puntatore)(void *ctx, uint32_t x, uint32_t y);
int (*input_pulsante)(void *ctx, uint16_t codice, int premuto);
int (*input_rotella)(void *ctx, int32_t asse_x, int32_t asse_y);
int (*input_lettera)(void *ctx, uint32_t carattere);
int (*input_posizione)(void *ctx, uint16_t codice, int premuto);
int (*input_rilascia_tutto)(void *ctx);
```

⛔ **Si collegano tutti e sei o nessuno**: `rcp.c` li guarda tutti, e un canale che sapesse muovere
il puntatore e non sapesse rilasciare un pulsante lascerebbe il desktop peggio di come l'ha trovato.
⚠ Senza i ganci la sessione **regge** e il messaggio viene convalidato lo stesso: «non ho un canale
di input» e «il client ha sbagliato» sono due fatti diversi, e c'è un caso verde che lo prova.

⇒ **Chiedo di correggere quella riga di `input.h`**, che è tua: dice una cosa che il costruttore
rende impossibile, e il prossimo che la legge ci riprova.

### (c) ⚠ `input_rilascia_tutto()` viene chiamata da due parti — va coordinata

`input.h` la assegna a `figlio.c` («al distacco»); io la chiamo da `rcp.c` su **quattro** strade più
il silenzio, perché sono le tre che §7.3 nomina — «per congedo, per silenzio, per errore» — e
`rcp.c` è l'unico posto da cui si osservano tutte e tre insieme.

⚠ Le due chiamate **non litigano**: la funzione rilascia quel che risulta premuto, e la seconda
volta non trova niente e torna 0. ⛔ Ma il doppione va deciso da te, non subìto. `[M]` dal banco:
con i ganci collegati il rilascio è chiesto **esattamente una volta per sessione**, su 53 sessioni
— e il guasto `niente-rilascio` fa cadere quel conteggio.

### (d) ⛔ Manca in `input.h` un modo di dire a `input.c` che la tela è cambiata

`input_apri()` prende `tela_l`/`tela_a` **una volta sola**, e dopo un `TELA(ADATTATA)` (§7.1) la tela
in vigore è un'altra. `rcp.c` da quel momento satura le coordinate alla **nuova** tela, mentre
`input.c` resta mappato sulla **vecchia**: i due lati avrebbero due verità, ed è la forma di difetto
che la fase 3 ha già pagato *fra* due pezzi ciascuno corretto per conto suo.

⚠ `input.h` dice che `input_gira()` rilegge le regioni a ogni `DEVICE_ADDED`, e **forse** basta —
`[?]` non è misurato, e il momento del `DEVICE_ADDED` non è il momento del `TELA`. Se non basta,
la firma che serve è:

```c
/* ⛔ §7.1: la tela in vigore e' cambiata.  Rimappa la regione del puntatore
 *    assoluto.  0 se fatto, -1 se no. */
int input_ritela(Input *, uint32_t tela_l, uint32_t tela_a);
```

### (e) `rcp_input_ultimo_iniettato()` va letto da chi cattura, e collegato

```c
uint32_t rcp_input_ultimo_iniettato(const rcp_sessione *s);
```

⛔ Va letto **nell'istante della cattura** e passato come parametro `input` a `rcp_video_apri()` /
`rcp_video_spedisci()` — oggi `webtransport.c:1432` lo riceve dal suo chiamante. ⚠ **Non se lo
prende `rcp_video_apri()` da sé**, e non è una dimenticanza: «l'ultimo iniettato **prima della
cattura**» è un fatto dell'istante della cattura, e fra la cattura e la chiamata passa tutta la
codifica. Prenderlo là dentro direbbe «l'ultimo iniettato prima della **spedizione**» — un numero
più alto, e una promessa più grande di quella che il fotogramma può mantenere.

### (f) ⚠ Una funzione in più, e il ripiego della vecchia è dichiarato

```c
void rcp_tela_adattata_ora(rcp_sessione *s, uint32_t lar, uint32_t alt,
                           uint64_t ora_ms);
```

Chi servirà `ADATTA_TELA` sul filo **deve** usare questa: `rcp_tela_adattata()` non ha un orologio da
cui far partire il secondo di grazia di §7.1, quindi **non lo apre** — e lo scrive nel registro
invece di tacere (`CODER.md` §4.2). ⛔ La vecchia firma è rimasta intatta perché
`banchi/02-filo-prodotto.c` la chiama e non è mio.

---

## I file di questo anello

| | |
|---|---|
| `src/rcp.h` · `src/rcp.c` | il canale di input: sei ganci, `rcp_ricevi_input()`, i due accessori, `rcp_tela_adattata_ora()` |
| `banchi/rcp/rcp.h` · `banchi/rcp/rcp.c` | i gemelli, `[M]` identici — il `Makefile` lo conferma |
| `banchi/04-b23-filo-input.c` | il cliente: manda i byte guasti, uno alla volta, e **non giudica niente** |
| `banchi/04-b23-filo-input.py` | il giudice: le 54 previsioni, e i conteggi coi denominatori |
| `banchi/04-b23-guasti.py` | ⭐ la certificazione: 12 guasti innestati, e il gemello rimesso a posto in un `finally` |
| `banchi/04-b23-lancia.sh` | gemello → certificazione → giro vero, in quest'ordine |
| `banchi/04-b23-esiti.jsonl` | la traccia depositata, 62 righe |

---

# Coda — `CURSORE_FORMA` sul filo (§7.2)

*Aggiunta il 14 agosto 2026, dopo che il coordinatore ha cucito le cuciture del punto 5 e che A6 ha
chiuso il cursore: `SPA_META_Cursor` si chiede davvero e la forma arriva — `[M]` 62 buffer e 0 forme
prima, 49 su 49 dopo. ⇒ `CURSORE_FORMA` non è più un canale senza sorgente, e mancava il mio lato.*

## 1. Che cosa cambia per l'utente

⭐ **Il puntatore ha una forma.** La freccia, la mano sopra un collegamento, la barra sul testo, la
clessidra: la forma viaggia in banda laterale e il client la disegna da sé — pixel puliti
nell'immagine, così non se ne vedono due (`SPECIFICHE.md` §7.1). E il cursore **nascosto** funziona:
entrare in un campo di testo fa sparire il puntatore invece di lasciarne uno fermo.

## 2. Serve una decisione di Nic?

**No.**

## 3. Che cosa ho MISURATO

`rcp_cursore_forma()` — e il conto è **il terzo**, con un denominatore suo, perché la proprietà è
diversa dalle altre due: non è una violazione del client né un verde del client, è
**autocontrollo del server**. ⛔ §7.2 fa rilevare la lunghezza sbagliata a **chi riceve**: un
messaggio storto spedito da qui fa chiudere la sessione **alla pagina**, e il registro del server non
ne saprebbe niente. ⇒ La regola è **nel dubbio non si manda**, e si scrive perché.

| misura | `[M]` 14 agosto 2026 | denominatore |
|---|---|---|
| ⭐ §7.2 — `CURSORE_FORMA`: la lunghezza che il server non sbaglia | **8** | / 8 |

⛔ **I numeri di B23 diventano: 29 violazioni + 25 verdi attesi + 8 sul cursore = 62 casi**, e 62/62
riprese fino a `ECCOMI`. La certificazione sale a **14 guasti su 14**.

⛔ **Si giudica sui byte usciti, non sul valore di ritorno**: il cliente riapre il canale di
controllo e **rifà il conto di §7.2 sui campi arrivati** — `lunghezza == 8 + l × a × 4`. E
l'immagine si ricontrolla **byte per byte** contro un disegno noto (`i & 0xFF`): ⚠ con un
riempimento di zeri, «memoria altrui» e «l'immagine giusta» avrebbero lo stesso aspetto, che è
precisamente il difetto che §7.2 nomina.

I tre casi che devono partire, e i cinque che **non** devono:

| | |
|---|---|
| ⭐ `16×16` | lunghezza **1032**, campi e punto attivo intatti |
| ⭐ `256×256` | **262 152** byte di corpo — il massimo che §5.5 concede, e **deve passare**: un tetto di §6.1 messo male qui ucciderebbe il cursore più grande che l'arbitro ammette |
| ⭐ nascosto | `0×0` con `0,0`, **8 byte esatti** |
| ⛔ lunghezza in meno / in più | zero byte sul filo. ⭐ È il caso che il coordinatore ha chiesto |
| ⛔ immagine `NULL` con misura addosso | zero byte: leggerla non sarebbe un messaggio storto, sarebbe la fine del processo |
| ⛔ oltre 1 MiB (§6.1) | zero byte |
| ⛔ prima di `SESSIONE` (§5) | zero byte, e **non è l'errore di nessuno**: la cattura comincia prima che il client si attacchi |

⚠ In nessuno degli otto la sessione cade: **rifiutare di mandare un cursore non è un motivo per
congedare nessuno.** Il giudice lo pretende.

## 4. ⛔ Che cosa NON ha funzionato

### ⛔ Un secondo difetto mio, e il banco l'ha trovato al PRIMO giro

Spedivo `w.len` invece di `n`. `scrittore` conta i byte passati **da lui**, e l'immagine ci arriva
con una `memcpy` che non vede: dopo i quattro `sc_u16` vale **8**. ⇒ Il `CURSORE_FORMA` dichiarava
`16×16` e portava **otto byte di corpo** — cioè la lunghezza che non torna, **prodotta da me**. La
pagina avrebbe chiuso con `ERRORE_PROTOCOLLO` a ogni cambio di forma, e il sintomo per l'utente
sarebbe stato *«la sessione cade quando muovo il mouse su un bordo»*.

⛔⭐ **E il registro del server scriveva la riga giusta**, perché la calcolava da `n`: *«1032 byte di
corpo = 8 + 16×16×4»*. **Il registro diceva il vero e il filo un'altra cosa.** È alla lettera la
ragione per cui `CODER.md` §3.8 vuole che si verifichi dal lato che riceve — e un banco che avesse
guardato il valore di ritorno, o il registro, sarebbe stato verde.

⚠ **Il cursore nascosto restava verde**: lì il corpo *è* otto byte. Un banco col solo caso facile non
avrebbe visto niente. Il difetto è rimesso nel catalogo come guasto
`cursore-lunghezza-da-scrittore`, e i due casi che deve far cadere sono dichiarati.

⇒ Aggiunto anche un controllo `w.len != 8` prima di spedire: irraggiungibile oggi, e c'è perché il
giorno in cui non lo fosse lo dica qualcuno invece di spedire un messaggio storto.

### ⛔ Un buco del BANCO, che avrebbe dato rosso all'imputato sbagliato

Il buffer del canale di controllo dell'ospite finto era di **8 KiB**, e un `CURSORE_FORMA` di
`256×256` pesa **262 158 byte**. Il giudice avrebbe letto un messaggio troncato **dal banco** e
avrebbe scritto «la lunghezza non torna» su un server che aveva fatto tutto giusto
(`LEZIONI.md` §1.9, il rosso all'imputato sbagliato). Portato a 512 KiB, con la ragione accanto.

### ⛔ Un buco nella catena dei controlli, dichiarato e NON chiuso

Ho seguito l'istruzione di non ricontrollare i limiti di §5.5. ⚠ Ma va detto per intero che cosa
questo lascia scoperto: §5.5 dice *«una sola delle due a zero è `ERRORE_PROTOCOLLO`»*, e una forma
`0×5` produce `attesa = 0` — cioè **una lunghezza che torna**. ⇒ Il controllo che è mio la
lascia passare, e a fermarla c'è solo `cursore.c`. Se quella riga regredisse lì, niente da questo
lato impedirebbe al messaggio di arrivare alla pagina e farle chiudere la sessione.

⛔ **Non l'ho chiuso**, perché due controlli sulla stessa regola diventano due regole. La riga che lo
chiuderebbe, se il coordinatore la vuole, è una:

```c
if ((larghezza == 0) != (altezza == 0)) { /* §5.5, e non si manda */ }
```

⇒ **Decida lui dove sta**: qui, o solo in `cursore.c` con questa nota come traccia del prezzo.

## 5. Le cuciture che chiedo al coordinatore

### (g) ⛔ L'adattatore di `CursoreForma`, e perché non posso scriverlo io

`FILE_NOSTRI` di `banchi/01-b3-rcp-innesta.py` è ancora `["rcp.c", "rcp.h", "autenticazione.c"]`
`[R]`: un `#include "cursore.h"` in `rcp.c` **non compila l'innesto**, cioè spegne B3, B5, B6, B8 e
B11. ⇒ La firma che mi hai dato non può stare in `rcp.c`; sta **dalla tua parte**, dove `cursore.h`
si può includere, e sono sei righe:

```c
/* in figlio.c (o dove si registra `cursore_apri`) — `chi` e' la sessione RCP */
int rcp_cursore_forma_da_cursore(void *chi, const CursoreForma *f)
{
	return rcp_cursore_forma((rcp_sessione *)chi, f->larghezza, f->altezza,
	                         f->attivo_x, f->attivo_y, f->immagine,
	                         (size_t)f->larghezza * f->altezza * 4u);
}
```

Quel che c'è in `rcp.h`, già scritto e provato:

```c
int rcp_cursore_forma(rcp_sessione *s, uint16_t larghezza, uint16_t altezza,
                      int16_t attivo_x, int16_t attivo_y,
                      const uint8_t *immagine, size_t immagine_n);
```

⛔ **`immagine_n` non è ridondante**, ed è la sola ragione per cui la firma non prende solo la
misura: senza sapere quanti byte esistono davvero, questa funzione ne leggerebbe
`larghezza × altezza × 4` **sulla fiducia** — cioè farebbe, dal lato del mittente, esattamente il
«leggo quel che c'è e vado avanti» che §7.2 nomina. Il cursore fatto di memoria altrui lo
confezionerebbe il server. ⚠ Nell'adattatore qui sopra i due numeri coincidono per costruzione, e va
bene: il valore del parametro è che il giorno in cui **non** coincidessero il messaggio non parte.

### (h) ⛔⛔ NON chiamarla dal thread di tempo reale della cattura

`cattura.c:335` (`cursore_rimbalzo()`) chiama `CursoreArrivata` **sul thread di PipeWire**, e lo
dichiara. ⛔ `rcp.c` non ha nessun lucchetto e `g.manda` scrive nella coda del trasporto: entrarci da
lì mentre il ciclo `poll` è dentro `rcp_ricevi()` è una corsa sui dati sulla sessione **e** sulla
coda di spedizione.

⭐ Nel prodotto ci passa già bene, perché la cattura sta nel **figlio** e la sessione nel **padre** —
la forma attraversa il tubo e rientra sul ciclo. ⚠ Ma `figlio.c` oggi **non nomina il cursore**
`[R]`: quella metà del tubo non è scritta, ed è tua. ⛔ Se invece si registrasse
`rcp_cursore_forma_da_cursore` **direttamente** come `CursoreArrivata` di un `cursore_apri()` nel
processo del padre, il difetto sarebbe una corsa — che non si vede in nessun banco e si vede sul
desktop dell'utente una volta al mese.

## I file, aggiornati

| | |
|---|---|
| `src/rcp.h` · `src/rcp.c` | in più: `T_CURSORE_FORMA` e `rcp_cursore_forma()` |
| `banchi/04-b23-filo-input.c` | in più: gli otto casi di §7.2, l'immagine-disegno, il canale di controllo da 512 KiB |
| `banchi/04-b23-filo-input.py` | in più: il terzo conto, col suo denominatore |
| `banchi/04-b23-guasti.py` | **14** guasti: in più `cursore-lunghezza-da-scrittore` (il difetto vero, rimesso) e `cursore-lunghezza-non-controllata` |
| `banchi/04-b23-esiti.jsonl` | 62 righe |

---

# Coda 2 — il buco `0×5`, chiuso

*14 agosto 2026. Deciso dal coordinatore dopo che la coda 1 lo aveva dichiarato aperto: il controllo
va **anche** in `rcp.c`.*

## 1. Che cosa cambia per l'utente

⭐ **Una forma di cursore malformata non gli porta più via la sessione.** Prima, un `0×5` sarebbe
partito e la pagina l'avrebbe rifiutato come §5.5 le ordina: sessione chiusa, per colpa nostra, con
un sintomo che non nomina il cursore.

## 2. Serve una decisione di Nic?

**No** — questa la ha già decisa il coordinatore, e la ragione è quella che rende la riga non un
doppione:

| | |
|---|---|
| `cursore.c` | decide **che cos'è** quel cursore |
| ⛔ `rcp.c` | non deve **EMETTERE** un messaggio che la specifica vieta, mai, da nessuna strada |

## 3. Che cosa ho MISURATO

Aggiunto in `rcp_cursore_forma()`, **prima** dell'aritmetica della lunghezza:

```c
if ((larghezza == 0) != (altezza == 0)) { /* §5.5 — non si manda, e si scrive */ }
```

⛔ **Ed è l'unico posto in cui il controllo di lunghezza — che è giusto — non basta**: `0×5` dà
`0 × 5 × 4 = 0` byte d'immagine, cioè un messaggio di **otto byte la cui lunghezza TORNA**. Il valore
malformato passava proprio il controllo che doveva fermarlo.

| misura | `[M]` 14 agosto 2026 | denominatore |
|---|---|---|
| ⭐ §7.2 — `CURSORE_FORMA`: la lunghezza che il server non sbaglia | **10** | / 10 |

⛔ **B23: 29 violazioni + 25 verdi attesi + 10 sul cursore = 64 casi**, 64/64 riprese fino a
`ECCOMI`. La certificazione sale a **16 guasti su 16**.

### ⭐ La coppia, e perché vale solo intera

I tre casi si distinguono **solo se ci sono tutti e tre**, e i due guasti nuovi lo dimostrano nei due
versi opposti:

| guasto innestato | diventa rosso | e questo prova |
|---|---|---|
| `cursore-zeri-non-appaiati` — il controllo si toglie | `0×5` e `5×0` | ⛔ senza la riga, un messaggio che §5.5 vieta **parte** |
| `cursore-rifiuta-ogni-zero` — `!=` diventa `\|\|` | **solo** `0×0` | ⛔ un controllo che rifiuta *qualunque* zero soddisfa `0×5` e `5×0` e **fa sparire per sempre il cursore nascosto** — la forma di difetto che §5.5 ha già pagato (rilievo R11.11, «una regola che vieta un caso che il documento stesso definisce») |

⚠ **Nessuno dei tre casi, da solo, distinguerebbe le due implementazioni.** È per questo che il
secondo guasto ha un insieme atteso di **un solo rosso**, ed è il caso *positivo*.

## 4. ⛔ Che cosa NON ha funzionato

⛔ **Un numero scritto a mano nel mio lanciatore**: `04-b23-lancia.sh` annunciava «dodici guasti
innestati» quando erano già sedici. ⚠ È alla lettera il rilievo **R7.14** — *un numero scritto a mano
è il numero che nessuno ricalcola* — e l'avevo scritto io, nello stesso giro in cui il giudice
calcola i propri. Togliuto: adesso il numero lo stampa `04-b23-guasti.py` dal proprio catalogo, e il
lanciatore non lo nomina.

⚠ **E il buco della coda 1 non era teorico.** L'avevo lasciato aperto per non duplicare una regola, e
il ragionamento era sbagliato in un punto preciso: non stavo duplicando la *decisione* su che cosa
sia il cursore, stavo omettendo il *divieto di emettere*. Sono due obblighi a due strati, e a
confonderli si perde quello che protegge l'utente.

## 5. Le cuciture

Nessuna nuova. ⭐ L'adattatore di sei righe **(g)** e il passaggio per il ciclo **(h)** restano come
scritti nella coda 1, e il coordinatore li ha presi: sta scrivendo il tubo dal palco al filo, e la
forma del cursore attraversa il confine di processo come lo attraversa il fotogramma — che è
esattamente la via che **(h)** chiedeva.

## I file, aggiornati

| | |
|---|---|
| `src/rcp.c` · `src/rcp.h` | in più: il controllo di §5.5 sugli zeri appaiati |
| `banchi/04-b23-filo-input.c` | in più: `cursore-una-sola-a-zero-0x5` e `5x0` |
| `banchi/04-b23-filo-input.py` | il terzo conto sale a 10 |
| `banchi/04-b23-guasti.py` | **16** guasti: in più `cursore-zeri-non-appaiati` e `cursore-rifiuta-ogni-zero` |
| `banchi/04-b23-lancia.sh` | tolto il numero scritto a mano |
| `banchi/04-b23-esiti.jsonl` | 64 righe |
