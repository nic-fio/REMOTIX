# F4-O2 — **Il numero dell'anello input → vetro**, e il tratto più caro chiamato per nome

*14 agosto 2026, pomeriggio. Anello **O2** della fase 4, in parallelo con O1.
Banco `banchi/04-b30-*` (ereditato da A10) + `banchi/04-b32-*` (nuovi).
Porte **7721-7723**, utente di banco **`provao2`** (uid 1003), albero `04-b30-src`.*

---

## 1. Che cosa cambia per l'utente

> ### ⭐⭐ Fra la sua mano e il pixel ci sono **~140 ms** — e adesso è un numero, non una stima.
>
> `[M]` **139,40 ms** (n = **326 su 326**) e **141,60 ms** (n = **322 su 322**) in **due giri
> indipendenti**: ⭐ concordano entro **2,2 ms**. · p95 **190-195** · p99 **200-232**.
> Con i due pezzi ciechi dichiarati accanto: **160-193 ms sullo schermo di un utente, più la rete.**
> ⛔ **Il tetto di `CODER.md` §1-bis è 50 ms: si sfora di quasi tre volte.**

**E prima di questo lavoro il numero non esisteva**: l'anello A10 aveva lasciato il metro certificato
(16 guasti su 16) con `n = 0` e uscita 3 — *«non ho niente da giudicare»*.

**Che cosa è cambiato per l'utente, in concreto:**

| | prima | dopo |
|---|---|---|
| ⛔ **il ritardo cresceva senza limite** | `[M]` +108 ms **al secondo**: 31,6 ms dopo 1 s → 1 461 dopo 11 s → **4 650 ms dopo 43 s**. Su un giro di tre minuti: **15-23 s** | `[M]` **non cresce**: −2 ms/s, e dopo 41 s vale **1,3 ms** |
| il ritardo input → vetro | ⛔ non era un numero: **cresceva** (4 176 ms nel primo giro, 8 246 nel secondo, 13 252 nel terzo *dello stesso giro*) | ⭐ **139,4 e 141,6 ms**, stabile e **ripetibile**, n = 326 e 322 |
| chi buttava l'avanzo | ⛔ **nessuno**: `scartati_ordine` 0 · `trattenuti` 0 · `corti` 0 | ⭐ `saltati_coda`, e si vede lavorare |

⚠ **E il difetto è CONDIZIONATO, il che è peggio e non meglio**: compare solo quando il server
consegna più di quanto la pagina dipinge. `[M]` in tre giri lo stesso server ha consegnato **39,6 ·
31,6 · 29,9** fotogrammi al secondo, e la pagina ne dipingeva **34,7 · 30,6 · 29,9**. ⛔ Al primo il
ritardo esplodeva, al terzo non succedeva niente — **con lo stesso codice**. ⇒ Un difetto che si
presenta a giorni alterni è un difetto che nessun giro di prova coglie per caso.

---

## 2. Serve una decisione di Nic?

**Sì, una — ed è la stessa che A10 gli aveva posto stamattina, adesso con la prova sul ferro.**

> ⭐ **La riga «il collo di bottiglia della fase 3 è IL DISEGNO — 28,0 ms su 78,1» è un'etichetta
> falsa su un numero vero, e sta in nove documenti.**
> `[M]` 14 agosto, sul prodotto vero: il **1° `drawImage`** (il `VideoFrame` che entra nel deposito)
> costa **25,56 ms** e il **2°** (deposito → tela visibile) **0,080 ms** — ⛔ **320 volte tanto**
> (e in un secondo giro indipendente: 24,51 contro 0,095, **258 volte**).
> ⇒ Quel tratto è per il **99,7 % ATTESA**, non disegno. ⭐ Stamattina era un'ipotesi; adesso è `[M]`.
>
> **Va riscritta o no?** Tocca `README.md`, `PIANO.md`, `CODER.md`, `DECISIONI.md` e
> `fasi/03-movimento.md`: è il modo in cui la fase 3 è stata chiusa e raccontata all'utente.

⚠ **E il costo del non farlo è già stato pagato una volta**: A10 segnalava che «A2 sta ottimizzando
`drawImage`». `[M]` `drawImage` vero costa **0,080 ms**: non c'era niente da ottimizzare lì.

*Tutto il resto — porte, utente di banco, cure, soglie — l'ho deciso e riferito.*

---

## 3. Che cosa ho MISURATO

Tutto `[M]` **14 agosto 2026**, macchina `192.168.0.2`, utente di banco `provao2`, prodotto sulla
**7722** dietro il ponte **7721**, ancora d'orologio **7723**.
⭐ **Il palco, dichiarato prima del numero**: Chrome 151 su CHUWI (⛔ **NON** sull'Xvfb — `xlsclients`
dice **0 clienti** su `:90`, quindi il browser sta sul desktop vero e il pezzo cieco in uscita
**esiste**), GPU `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))`; server con **HEVC in HARDWARE**
(`hev1.2.4.L120.B0`, nodo `renderD128` aperto **dai miei soli processi**, codifica 5,3 ms); scena
`04-b30-scena` a **58-60 disegni/s** su **`Meta-0`**, ⭐ **confermato da `wl_surface.enter`, cioè dal
compositore**, e uguale al monitor che il prodotto dichiara di catturare.

### 3.1 ⭐⭐ IL NUMERO, e il denominatore prima del numero

| | |
|---|---|
| messaggi §7.3 usciti sul filo | **326** |
| eventi ricevuti **dalla scena** | **1 673** |
| sonde tentate | **326** |
| ⭐ **sonde CHIUSE nei pixel** | **326** — *il denominatore vero, e vale il 100 %* |
| scena sul monitor catturato | ✅ **326 punti su 326** |

> **`[M]` input → vetro = 139,40 ms** (mediana) · min 76,4 · p25 127,8 · p75 151,5 · p95 194,6 ·
> p99 232,3 · max 299,4 · **n = 326**
> ⭐ **e rifatto da capo mezz'ora dopo: 141,60 ms** · p95 190,0 · p99 200,4 · **n = 322**.
> ⛔ **contro 50: SFORA. Contro 40: SFORA.** Anche al p95, in tutt'e due i giri.

⭐ **I due giri concordano entro 2,2 ms**, ed è la prova che il numero è del prodotto e non del
giorno. ⚠ **E il giro ancora prima, quando la cura di O1 non era ancora in `src/figlio.c`, dava
`[M]` 151,17 ms (n = 573)**: `[M]` **−10 ms** circa. ⛔ Vengono da due prodotti diversi e si
riportano tutt'e due, invece di tenere il più basso.

### 3.2 ⭐⭐ LA SCOMPOSIZIONE IN UNDICI TRATTI — e **nessuno domina**

*Mediane in ms. ⛔ I tratti 2 e 5 attraversano due macchine e portano dentro l'errore dell'ancora
(scarto 262,8 s, deriva **0,37 ppm**, errore ~0,6 ms).*

| # | tratto | mediana | quota |
|---|---|---|---|
| **1a** | evento → il prodotto lo vede (fase di cattura) | **13,09** | 9 % |
| 1b | il prodotto lo vede → i byte escono | 0,075 | 0,05 % |
| **2** | byte usciti → la **SCENA** riceve l'input *(filo d'andata + server + `libei` + compositore)* | **26,04** | 19 % |
| **3** | la scena riceve → la scena **DISEGNA** (l'attesa del quadro) | **26,61** | 19 % |
| **4** | la scena disegna → cattura (`pts` di Mutter) | **16,23** | 12 % |
| ⭐ **5** | cattura → PRIMO byte in pagina (codifica + filo di ritorno) | **30,37** | **22 %** |
| 6 | primo byte → ultimo byte | 0,195 | 0,1 % |
| 7 | stream completo → `decode()` | 0,085 | 0,06 % |
| 8 | `decode()` → richiamo del decodificatore *(la decodifica vera)* | **0,745** | 0,5 % |
| **9** | richiamo → **1° `drawImage` finito** (⛔ l'ATTESA) | **25,56** | 18 % |
| 10 | 1° → 2° `drawImage` finito (⛔ il disegno VERO) | **0,080** | 0,06 % |
| | **somma dei tratti** | **139,08** | |
| | ⭐ **TOTALE misurato di suo** | **139,40** | |

⭐ **E i due numeri tornano a 0,32 ms**: la somma degli undici tratti e il totale misurato
indipendentemente (`t_dip − t_evento`, tutt'e due `performance.now()` della stessa pagina) — ⛔ un
tratto perso per strada sarebbe un pezzo di catena che nessuno guarda.

⭐ **E il giro ripetuto dà gli stessi tratti**: `[M]` 12,26 · 0,075 · **24,65** · **26,41** · 16,22 ·
**31,36** · 0,19 · 0,08 · 0,75 · **27,12** · 0,08 ⇒ totale **141,60**. ⛔ Nessun tratto si sposta di
più di **1,6 ms** fra i due giri: la scomposizione è ripetibile quanto il totale.

> ### ⛔ LA TESI 1 DEL MANDATO È **REFUTATA**
> *«Il ritardo input → vetro è dominato da un tratto solo, e quel tratto NON è la codifica.»*
>
> ⭐ **La seconda metà regge, la prima no.** Non c'è nessun tratto dominante: i **sei** tratti
> maggiori valgono fra **13,1 e 30,4 ms** e insieme fanno il **99 %** del totale. ⛔ Curarne uno
> solo, qualunque sia, toglie al massimo **il 22 %** del ritardo — e il tetto resterebbe sforato di
> due volte e mezzo.
> ⚠ E la codifica c'è dentro, ma sta **dentro** il tratto 5 e vale **5,3 ms su 30,4**: la riga
> «il collo di bottiglia è la codifica» resta falsa, e adesso lo è **con un numero sotto**.
> ⭐ E la **decodifica** vera vale **0,745 ms**: lo 0,5 %.

⭐ **La quantità che il canale di input AGGIUNGE** rispetto al metro della fase 3 — misurata sullo
**stesso giro e sugli stessi fotogrammi**, non fra due giri: tratti 1a + 1b + 2 + 3 = **65,81 ms**,
cioè **il 47 %** del totale. ⇒ ⛔ **Il metro della fase 3 non vedeva quasi metà del ritardo che
l'utente sente.**
⛔ I due numeri non si sommano e non si sottraggono: *input → vetro* **contiene** *disegno → vetro*.

### 3.3 ⭐⭐ IL TRATTO PIÙ CARO — e ce ne sono **due**, di natura diversa

**(a) Il più caro fra i tratti stazionari: `5 cattura → primo byte`, 30,37 ms (22 %).**
Ci stanno dentro la conversione (5,6 ms), il caricamento sulla GPU (2,9 ms), la codifica (**5,3 ms,
in hardware**) e il filo di ritorno — e ⛔ **restano ~16 ms che nessuno dei tre spiega**.
⚠ Ha anche la coda peggiore: **p95 46,9 · max 64,4**.
⭐ E subito dietro ci sono **tre tratti quasi uguali** — `3` (26,61), `2` (26,04), `9` (25,56) — che
stanno in **tre posti diversi** della catena: la scena, il canale d'andata, e il client.

**(b) ⛔⛔ E il più caro in assoluto non è un tratto: è UNA CODA CHE CRESCE.**

`[M]` con il prodotto di stamattina, scena in movimento, `banchi/04-b32-coda.py`:

| | |
|---|---|
| il server **consegna** | **39,6** fotogrammi/s |
| la pagina **dipinge** | **34,7** fotogrammi/s |
| ⇒ avanzo | **~5/s**, e ⛔ **nessuno lo butta** (`scartati_ordine` 0 · `trattenuti` 0 · `corti` 0) |
| ⇒ il ritardo `decode()` → richiamo | **+108 ms al secondo**: 31,6 → 293 → 1 461 → 2 316 → 2 787 → **4 650 ms in 43 s** |

⛔ **Dopo un minuto l'utente comanda un desktop che ha visto sei secondi fa, e nessun registro lo
dice**: tutti i contatori dei fotogrammi restano verdi. ⚠ È la forma d'errore che `LEZIONI.md` §1.9
descrive — un verde che non è una prova.

⭐ **E la causa che lo produce sta nel tratto 9**: a **25,6-27,1 ms** per fotogramma il primo
`drawImage` mette un tetto di **~37-39 fotogrammi al secondo** a questa pagina, su questo hardware.
Quando il server ne consegna di più, l'avanzo si accumula nel decodificatore.

### 3.4 ⛔ LA TESI 2 — *«i 10,8 cambiamenti al secondo sono quante volte Mutter ci consegna»* — **REFUTATA**

`[M]` `banchi/04-b32-ritmo.py`, quattro conti nella **stessa finestra di 30 s**:

| punto della catena | al secondo |
|---|---|
| **1.** la scena disegna | **59,99** |
| **2.** Mutter ci consegna | **30,84** (il 51 %) |
| ⭐ **2-bis.** e quante volte abbiamo aspettato **a vuoto** | ⛔ **0,00** |
| **3.** il server spedisce sul filo | **30,54** |
| **4.** la pagina dipinge | **30,6** *(letto da `04-b32-coda`)* |

> ⛔⭐ **Le attese a vuoto sono ZERO: ogni volta che abbiamo chiesto un fotogramma ce n'era già uno
> pronto.** ⇒ **Non stiamo aspettando Mutter**: il limite sta **dentro il nostro ciclo**, a valle di
> lui. La tesi «è il compositore che non consegna» **non regge in questo regime**.
>
> ⚠ **E qui la trappola ha già morso una volta**: `src/figlio.c:2669` porta la riga *«la tesi era
> falsa: Mutter aveva i fotogrammi, e noi non eravamo lì a prenderli»* — e la riga di registro che
> avrebbe dovuto smascherarlo (*«scena ferma: Mutter consegna solo quando qualcosa cambia»*)
> **accusava il compositore di un difetto nostro**. ⇒ Questo strumento stampa `attese a vuoto`
> accanto al ritmo apposta: è l'unica riga che distingue le due diagnosi.

⛔ **Che cosa questo NON dice, e va detto:** i **10,8 cambiamenti al secondo** che l'utente ha
misurato dal suo video sono su un **desktop vero**, dove Mutter consegna solo quando qualcosa
cambia. Qui la scena si muove a 60/s **per obbligo** (`LEZIONI.md` §1.1) e il regime è l'opposto:
**abbondanza**, non scarsità. ⇒ Le due misure rispondono a due domande diverse, e questa non
sostituisce quella. `[?]` **Il ritmo su un desktop vero e fermo resta non misurato da me.**

### 3.5 ⭐⭐ LA TESI 3 — *«tastiera e mouse hanno lo stesso ritardo»*: **il numero c'è e NON è utilizzabile**, e a dirlo è la scomposizione

⭐ **Quel che è `[M]` e regge: il cammino della tastiera arriva fino al compositore, e si vede nei
pixel.** La Panoramica di GNOME si chiude mandando `Escape` **dal canale di input del prodotto**
(§7.3 `POSIZIONE_TASTO`, evdev 1) — riuscito **al primo tentativo in quattro giri su quattro**,
verificato guardando l'immagine e il fuoco della scena, non un registro.
⭐ E `[M]` la scena riceve **744 eventi di tastiera** nell'ultimo giro: il canale porta i tasti.

⭐ **E la mappa `event.code` → evdev è MISURATA, non ricopiata** da `src/pagina.html`: `F13`→183 …
`F24`→194, dodici su dodici, coppia giù/su verificata, mappa iniettiva. ⛔ Se il conto non torna la
mappa **non si consegna**, e la tastiera non si misura — meglio nessun numero che un numero
appaiato male.

> ### ⛔⛔ E IL NUMERO CHE È USCITO È **FALSO**, E A SMASCHERARLO È LA SCOMPOSIZIONE
>
> `[M]` ultimo giro: **35 sonde chiuse su 296**, mediana **151,69 ms** — contro i **141,60 ms** del
> mouse nello **stesso giro**. ⚠ Un numero verosimile: *«la tastiera è 10 ms più lenta del mouse»*.
>
> ⛔ **È falso, e la prova è che la sua scomposizione non è fisica**:
> `2 byte usciti → la scena riceve` = **−562,8 ms** — ⛔ **negativo**, cioè l'eco appaiato è stato
> dipinto **prima** che il messaggio partisse. E `8 la decodifica` = **476,5 ms** contro gli
> **0,75** del mouse.
> ⇒ ⭐ **L'accoppiamento sta prendendo il fotogramma sbagliato**, e il totale da solo non lo
> direbbe mai. **È esattamente il guasto n. 12 della certificazione di A10** — *«la mediana sale ma
> nel tratto sbagliato»* — visto dal vivo, sul mio stesso banco.
>
> **Perché succede, ed è misurato**: i codici di prova sono **dodici** e si ripetono; l'eco di un
> tasto vive finché non arriva il successivo, e ⛔ **l'88 % delle sonde non trova il proprio** —
> quelle che chiudono sono un campione scelto **dal difetto**, non da me.
> ⚠ E il primo giro l'aveva detto ancora più forte: **27 sonde su 584, mediana 1 007 ms** ≈ il
> **periodo di ripetizione** dei dodici tasti (840 ms). Il numero diceva la mia cadenza, non il
> prodotto. ⇒ Ho stretto la finestra d'accoppiamento **sotto** il periodo (500 ms) e separato il
> «giù» dal «su» di un intervallo di quadro: il denominatore è passato da 27/584 a 35/296, ⛔ **e
> non basta**.

⇒ ⛔ **La tesi 3 resta APERTA: non l'ho né confermata né refutata, e non ho pubblicato il numero.**
Che cosa serve per chiuderla (§6.3): un eco della tastiera che **non si sovrascriva** — cioè un
contatore di sequenza che il banco possa prevedere, o una scena che tenga in vita l'eco per un
numero fissato di quadri. **È lavoro mio su `04-b30-scena.c`, e lo faccio appena il coordinatore
conferma la priorità.**

⚠ **E la ragione per cui la domanda va posta comunque** resta scritta: in modo classico il mouse
muove un puntatore **disegnato dalla pagina** (`SPECIFICHE.md` §7.1), che l'utente vede **senza
rete**; la tastiera fa tutto il giro. ⇒ I **~140 ms** sono il giro completo per tutt'e due, ma quel
che l'utente *sente* col mouse è più corto di quel che questo numero dice. ⛔ **Mediarli sarebbe
stato sbagliato, e non è stato fatto.**

### 3.6 I DUE PEZZI CIECHI, dichiarati

| | | |
|---|---|---|
| in **INGRESSO** | `[?]` **4-12 ms** | mano → `event.timeStamp`: dispositivo, nucleo e compositore **del client** |
| in **USCITA** | `[?]` **16-40 ms** | disegno finito → pixel acceso (`STUDI.md` §web §6.2) — ⭐ e qui **esiste**, perché `xlsclients` dice **0 clienti sull'Xvfb**: il browser sta su un compositore vero |

⇒ **139,4-141,6 + 20-52 = 160-193 ms sullo schermo di un utente, più la rete.**

### 3.7 I controlli del banco — **10 su 11** all'ultimo giro, e il rosso è dichiarato

| | | |
|---|---|---|
| Q0 | ✅ | 326 spediti · 1 673 ricevuti dalla scena · **326 chiuse su 326** |
| Q1 | ✅ | scena e cattura sullo **stesso** `Meta-0`, confermato da `wl_surface.enter` |
| Q2 | ✅ | **1 467 su 1 467** fotogrammi con tutt'e due le marche |
| Q3 | ✅ | **1 467 su 1 467** eco leggibili, zero rifiuti |
| Q4 | ✅ | (a) **0 falsi positivi** su 241 fotogrammi veri dove la marca non c'è · (b) **311** eco distinti · ⭐ (c) **326 coordinate giuste, 0 storte** — `RCP.md` §7.3 rispettata |
| ⛔ **Q5** | **rosso** | ritardo di **25 ms** al RITORNO: ⭐⭐ il surplus **sta nel tratto 5** e vale **+24,70** — **a 0,3 ms da N**. ⛔ Ma il totale sale di **20,78** (scarto **−4,22**, appena fuori dai 4 di tolleranza) e il tratto 2 si muove di **−7,17** |
| ⭐⭐ **Q6** | **VERDE** | ritardo di **30 ms** all'ANDATA: il totale sale di **30,84** (scarto **+0,84**), ⭐ il surplus sta **nel tratto 2** (**+33,49**) e **in nessun altro tratto**. ⇒ **Il controllo che alla fase 3 non poteva esistere passa sul ferro** |
| Q7 | ✅ | i due confini cadono su fotogrammi diversi nel **97,8 %** dei casi; ⭐ il confine comodo si regala `[M]` **32,99 ms** di mediana |
| Q8 | ✅ | **27,11 contro 0,080 ms** ⇒ **339×**: il tratto non è il disegno, è l'attesa |
| Q9 | ✅ | il banco costa **1,10 ms** per fotogramma (due regioni) e ⭐ **l'1,1 %** di ritmo (30,08 contro 29,75 fotogrammi/s) |
| Q10 | ✅ | grana **0,005 ms**, pagina **isolata** (COOP+COEP) |

> ### ⛔ PERCHÉ Q5 E Q6 SONO ROSSI, E PERCHÉ **NON HO ALLARGATO LA TOLLERANZA**
>
> ⭐⭐ **Q6 passa, e vale più di quanto sembri**: è il controllo del ramo d'ANDATA, quello che alla
> fase 3 **non poteva esistere** — `[M]` iniettando 30 ms il totale sale di **30,84** e il surplus
> compare **tutto nel tratto 2** (+33,49) **e in nessun altro**. ⇒ Metà dell'anello che finora non
> aveva nessuna taratura adesso ce l'ha (`LEZIONI.md` §1.14).
>
> ⛔ **Q5 resta rosso, e per pochissimo**: il surplus **sta nel tratto giusto** (+24,70 contro N=25,
> **a 0,3 ms**), ma il **totale** sale di 20,78 invece di 25 — scarto **−4,22 ms**, cioè
> **0,22 ms oltre** la tolleranza.
>
> ⚠ La spiegazione c'è, ed è **misurabile, non una scusa**: fra l'input e il vetro ci sono **due
> orologi liberi** — la scena a 60 Hz e la cattura a ~31 Hz. Ritardare l'input di N sposta la sua
> fase rispetto a tutt'e due, e il totale guadagna o perde fino a **un intervallo di cattura**
> (32 ms) di quantizzazione. `[M]` gli scarti osservati sono **−9,2** e **+6,3 ms**: dentro
> mezzo intervallo, coi due segni, come ci si aspetta da uno spostamento di fase uniforme.
> ⚠ E i tre giri sono presi a **mani alternate** apposta, quindi non è deriva.
>
> ⛔ **Allargare la tolleranza da 4 a 20 ms avrebbe fatto passare tutt'e due**, ed è esattamente la
> mossa che `LEZIONI.md` §1.13 vieta. ⇒ Restano **rossi**, e la cura del controllo — non del
> prodotto — è dichiarata al §6.4.

### 3.8 Dove si ricontrolla

```
bash banchi/04-b30-lancia.sh certifica       # 53 su 53, 16 guasti su 16 — senza rete
bash banchi/04-b30-lancia.sh terreno         # utente provao2, sessione SENZA --virtual-monitor
bash banchi/04-b30-lancia.sh porta && bash banchi/04-b30-lancia.sh costruisci
bash banchi/04-b30-lancia.sh scena-costruisci && bash banchi/04-b30-lancia.sh accendi
bash banchi/04-b30-lancia.sh misura 45       # il numero, con n e la scomposizione
python3 banchi/04-b32-coda.py                # la coda: cresce o no
python3 banchi/04-b32-ritmo.py               # il ritmo in quattro punti
```
Righe depositate in `banchi/04-b30-esiti.jsonl` (giri `b30-o2-2` senza cura ⇒ **uscita 3**,
`b30-o2-cura1`, `b30-o2-finale`, `b30-o2-finale2`) e in `banchi/04-b32-esiti.jsonl`
(`coda-PRIMA-della-cura`, `coda-DOPO-la-cura`).
⛔ **La certificazione si rifà prima di ogni misura** e resta **53 su 53 · 16 guasti su 16**, anche
dopo tutte le estensioni di questo anello.

---

## 4. LA CURA — dichiarata prima di toccare il file, e rimisurata con lo stesso strumento

### 4.1 Il file accusato: `src/pagina.html`, funzione `dipingi()`

⛔ **Non è un file mio**, ed è dichiarato qui prima di essere toccato, come il mandato impone.
L'accusa è misurata: il **1° `drawImage`** costa 25-27 ms, il ritmo della pagina si ferma a ~35/s,
il server ne consegna 39,6, e **nessun contatore di scarto sale**.

⭐ **La cura, e non chiede una chiave**: si salta **il DISEGNO**, non la decodifica.

```js
/* ancora `F4-CODA-DEL-DECODIFICATORE` */
if (this.dec && this.dec.decodeQueueSize > 2) { this.conti.saltati_coda++; f.close(); return; }
```

⚠ **Perché così e non buttando il fotogramma prima del decodificatore**: saltare un delta rompe la
catena e obbliga a una `RICHIEDI_CHIAVE` — cioè un'immagine ferma per qualche centinaio di
millisecondi a ogni ciclo, e una chiave costa dieci volte un delta (§5.2). ⭐ Saltando **solo il
disegno** il decodificatore decodifica tutto, la catena resta intera, **nessun buco, nessuna
chiave**, e l'utente vede sempre **l'ultimo** fotogramma invece del primo di una coda.

⚠ **E la soglia è 2, non 0, e il numero è misurato**: in regime sano la coda vale ~1 fotogramma
(`[M]` 31,6 ms a 33/s), perché il decodificatore hardware tiene una pipeline sua. Con la soglia a 0
si butterebbe metà del ritmo per un'attesa che non è un ritardo.

⛔ **E il conto si tiene** (`saltati_coda`): un fotogramma buttato in silenzio è un ritmo che cala
senza che nessuno sappia perché, e l'invariante **I1** vuole che ogni discesa sia dichiarata.

### 4.2 La stessa misura, ripetuta — ⭐ stesso strumento, stessa scena, stesso banco

| `[M]` con `04-b32-coda.py` | avanzo | pendenza del ritardo | dopo ~41 s | `saltati_coda` |
|---|---|---|---|---|
| ⛔ **prima**, server a 39,6/s | **+4,9/s** | **+108 ms/s** | **4 650 ms** | *non esiste* |
| ⭐ **dopo**, server a 31,6/s | +0,73/s | **−2,0 ms/s** | **1,3 ms** | **30**, e salgono esattamente quando il ritardo fa un salto a 127 ms — subito dopo torna a 1,6 |
| ⭐ **dopo**, server a 29,9/s | **0,00/s** | −0,0 ms/s | **0,7 ms** | **0** — ⭐ senza avanzo la cura **non costa niente** |

⭐ **La riga di mezzo è la prova che il meccanismo lavora**: si vede il ritardo salire, `saltati_coda`
scattare, e il ritardo tornare giù nella stessa tabella.

⛔ **E il limite del confronto si dichiara**: il ritmo che il server consegna **non è stato tenuto
fermo** fra i tre giri (39,6 · 31,6 · 29,9), perché dipende dal carico della macchina di prova, che
in questo momento ospita dieci banchi. ⇒ Il «prima» e il «dopo» **non si sottraggono**; quel che si
sottrae è **la pendenza**, che è la grandezza vera del fenomeno.

### 4.3 E il numero, dopo la cura

`[M]` **139,40 ms (n = 326) e 141,60 ms (n = 322)** — cioè il numero del §3.1 (e **151,17 ms,
n = 573** sul prodotto di un'ora prima, cioè senza la cura di O1 in `src/figlio.c`).
⛔ **Prima della cura il numero non esisteva**: sullo stesso banco e con la stessa scena il giro
`b30-o2-2` ha chiuso **0 sonde su 258**, perché la conseguenza dell'input arrivava al vetro **4,2
secondi dopo** (e 8,2 e 13,3 nei due giri successivi *dello stesso giro*), fuori da qualunque
finestra d'accoppiamento sensata. ⇒ ⛔ **Non è «da 4 176 a 139»: è «da un numero che non esisteva a
un numero»**, e i due non si sottraggono.

---

## 5. ⛔ CHE COSA NON HA FUNZIONATO

*Si riempie anche quando fa una brutta figura. ⭐ E qui i primi tre difetti erano tutti **del banco o
del contorno**, non del canale di input — che ha funzionato al primo colpo.*

### 5.1 ⛔⛔ LA PANORAMICA DI GNOME SI MANGIAVA IL PALCO, e nessun documento la nominava

Una sessione GNOME headless appena nata si apre **in Panoramica**. ⇒ La scena «a schermo intero»
era **una miniatura riscalata a 0,79** dentro l'anteprima, e la Panoramica si teneva il fuoco.
Da fuori si vedevano **due sintomi che accusavano due imputati diversi, e nessuno era colpevole**:

| il sintomo | la diagnosi che suggeriva | la verità |
|---|---|---|
| `eventi_puntatore = 0` sulla scena, con l'iniezione riuscita | *«`libei` non consegna»* | la scena non aveva il fuoco |
| **0 marche lette su 966** | *«l'eco non si legge»* | una marca di celle da 24 px riscalata a 0,79 non ha più nessun CRC |

⭐ **A trovarlo è stato GUARDARE L'IMMAGINE**, non leggere un numero (`CODER.md` I8). Due ore di
diagnosi sbagliata chiuse da un `toDataURL` e un `Read`.
⇒ Cura nel banco: si manda `Escape` **dal canale del prodotto** e si **verifica** che la scena
prenda il fuoco; se non lo prende, il banco **si rifiuta di misurare**.

### 5.2 ⛔⛔ UN DIFETTO NELLA SCENA DI A10 — `oy` sommato due volte, e valeva `n = 0`

`banchi/04-b30-scena.c`, `dipingi_marca_a()`: `riquadro_marca_a(oy)` porta già `oy` dentro `b.y`, e
le celle lo sommavano **di nuovo**. ⇒ Sulla marca 1 (`oy = 0`) non si vedeva niente — 0 + 0 = 0, e
quella marca si leggeva benissimo. ⛔ Sulla marca 2 la **zona di quiete nera restava al suo posto e
le celle finivano fuori**, sullo sfondo del desktop: il lettore guardava un rettangolo nero e diceva
*«contrasto 0,0016, la marca non c'è»* — vero, e con la catena perfettamente funzionante.

⭐ **E la certificazione era VERDE, 53 su 53**: i sedici guasti si innestano nel **verbale**, e
**nessuno di loro dipinge un pixel**. ⇒ Ho aggiunto al banco il passo che l'ha trovato — *«lo
scorrimento della marca, misurato sui PIXEL VERI»* — che legge le **due** regioni e stampa il
contrasto di ciascuna. ⚠ Ed è anche **indispensabile**: `leggi_celle` gira con `ricerca=0`, lo
scorrimento non lo cerca, **lo eredita**; senza quel passo `B.scorrimento` resta `[0,0]` e ogni CRC
salta.

### 5.3 ⛔ IL CONTROLLO DI PRECONDIZIONE DI A10 HA DATO UN FALSO **ROSSO** — e un falso rosso spegne la misura

Cercava `.input_puntatore` in **`src/figlio.c`** e ne trovava zero ⇒ *«NON HO NIENTE DA GIUDICARE»*,
uscita 3, misura non eseguita. ⛔ Era **falso**: i ganci si attaccano in **`src/webtransport.c`**
(il canale sta nel **padre**); il figlio, dall'altra parte del confine di processo, **chiama**
`input_puntatore()` su `MSG_INPUT`. ⭐ È la stessa lezione della mattina presa dall'altro verso —
allora quel controllo aveva dato un falso **verde** (cinque `0x0101` dentro i commenti). ⇒ Adesso
guarda **tutt'e due i lati del confine**, ciascuno col nome del suo file.

### 5.4 ⚠ Tre inciampi del banco, e ciascuno ha lasciato una riga nel codice

1. ⛔ **`Input.dispatchMouseEvent` ritorna dopo 5,00 s esatti** (`[M]` cinque chiamate: 5,049 ·
   5,018 · 5,025 · 5,025 · 5,013 — un numero così stabile è un **tetto**, non un carico).
   Aspettarlo avrebbe voluto dire **dodici sonde al minuto**: il banco avrebbe misurato sé stesso.
   ⇒ `spara()` manda il comando CDP **senza aspettare la risposta**, e che l'evento arrivi lo dice
   `eventi_visti`, contato **dentro la pagina**.
2. ⛔ **Il primo ritiro portava fuori settantamila fotogrammi in un JSON solo** e il banco restava
   appeso per minuti senza un errore — «il banco non risponde» manda a cercare la rete. ⇒ Si svuota
   a mano prima di cominciare e si ritira **ogni secondo**.
3. ⚠ **La stampa restava nel buffer** e un giro di due minuti sembrava un banco appeso — e chi
   guarda un banco appeso lo ammazza, perdendo la misura invece del difetto. ⇒ `python3 -u`.

### 5.5 ⚠ E quel che NON ho misurato, dichiarato invece che colmato

| | |
|---|---|
| ⛔ **il ritardo della TASTIERA** | **35 sonde su 296**, e il numero che ne esce (151,7 ms) è **falso**: la sua scomposizione dà un tratto **negativo** (§3.5). ⇒ Non l'ho pubblicato |
| ⛔ **i 250 ms di `cattura_prendi()`** su un desktop **fermo** | ⚠ Il mio banco pretende una scena **in movimento** (`LEZIONI.md` §1.1): il caso «fermo» è **fuori dalla sua portata per costruzione**. ⭐ Quel che ho: su scena viva il tratto 2 **intero** vale **26,04 ms** (p95 34,3 · p99 51,3 · max 62,5) — cioè lì quei 250 ms **non mordono**: nemmeno il massimo li raggiunge. Vedi §6.2 |
| `[?]` **il ritmo su un desktop vero e fermo** | i 10,8/s dell'utente non sono confrontabili col mio regime di abbondanza (§3.4) |
| `[?]` **il pulsante e la rotella** | il canale li porta (`RCP.md` §7.3, A4 li ha misurati al desktop) ma **non ho chiuso l'anello su di loro**: solo puntatore |
| ⚠ **un browser solo** | Chrome 151. Firefox non è stato provato in questo anello |

---

## 6. Le cuciture che chiedo al coordinatore, con la firma esatta

### 6.1 ⛔ La riga che serve per spaccare in due il tratto 2 — *(è ancora la §5.2 di A10, e adesso ha un numero accanto)*

Il tratto 2 vale **26,04 ms** ed è **tutto insieme**: filo d'andata, coda del server, `libei`,
compositore. ⛔ Senza questa riga non si può dire **quale dei quattro**, e sono quattro cure diverse
— ⚠ ed è il **terzo** tratto della catena, a 4,3 ms dal primo: non è un dettaglio.

```c
/* src/input.c — al ritorno di ogni input_*() */
registro("b30 input id=%u tipo=%u arrivo_us=%llu iniezione_us=%llu esito=%d",
         id, tipo, (unsigned long long)arrivo_us, (unsigned long long)iniezione_us, esito);
```
⚠ `arrivo_us` e `iniezione_us` sullo **stesso** `CLOCK_MONOTONIC` del `pts` dei 28 byte, o non si
sottraggono.

### 6.2 ⛔ E la domanda di O1 sui **250 ms**: la risposta parziale è misurata, la mancante ha bisogno di quella riga

⭐ `[M]` **su scena viva quei 250 ms non mordono**: il tratto 2 *intero* — che li contiene — vale
**26,04 ms** di mediana, **51,3** al p99 e **62,5** al massimo, contro i 30,37 del tratto più caro.
⇒ **Nemmeno il caso peggiore misurato arriva a un quarto dei 250 ms**, e curarlo toglierebbe al
massimo il 19 % del totale.
⚠ Ma il tratto 2 è **terzo su undici** e a 4,3 ms dal primo: ⛔ **non è una cura da buttare, è una
cura che da sola non basta** — come tutte le altre (§3.2).
⛔ **Sul desktop FERMO non l'ho misurato e non posso**: questo banco pretende una scena in
movimento. ⇒ Servono **due** cose, e nessuna delle due è mia:
1. la riga §6.1 (in `src/input.c`), che dà l'istante d'arrivo **senza passare dai pixel** — ed è
   l'unico modo di misurare un input su un desktop che per definizione non disegna;
2. la firma che O1 propone (`cattura_prendi_o_sveglia`), che è la **cura**, non la misura.

⇒ ⭐ **Con la riga §6.1 il numero si prende in dieci minuti**, e con lo stesso banco: si spegne la
scena, si manda un input ogni due secondi, e si legge `arrivo_us − t_filo`. **Lo faccio io appena la
riga c'è.**

### 6.3 ⚠ L'eco della tastiera — perché la tesi 3 si possa chiudere

⛔ Non è più un problema di fuoco (`ho_il_fuoco_tastiera` vale **1** e la scena riceve **744**
eventi): è che **l'eco di un tasto si sovrascrive prima di essere dipinto**, e l'88 % delle sonde
non trova il proprio. ⇒ Serve un eco che il banco possa **prevedere** — un contatore di sequenza
che il client conosca, oppure una scena che tenga l'eco in vita per un numero fissato di quadri.
⭐ **È lavoro mio, su `banchi/04-b30-scena.c`**: lo faccio appena il coordinatore mi dice se viene
prima di altro. ⚠ Finché non c'è, il ritardo della tastiera **non si misura**, e questo rapporto
non ne porta nessuno.

### 6.4 ⚠ E la cura del controllo Q5/Q6, che è del banco e non del prodotto

I due controlli pretendono che il totale salga di **esattamente** N. ⛔ Fra i due capi ci sono due
orologi liberi (scena 60 Hz, cattura 31 Hz) e la quantizzazione aggiunge fino a un intervallo
intero. ⇒ La pretesa giusta è **sul tratto**, non sul totale — e sul totale va chiesto
`N ≤ salita ≤ N + intervallo_di_cattura`. **Non l'ho cambiato**: cambiare un controllo perché è
rosso, nello stesso giro in cui è rosso, è la mossa che `LEZIONI.md` §1.13 vieta. ⇒ Si cambia a
freddo, e si ricertifica.

---

## I file

| | |
|---|---|
| `banchi/04-b30-anello-input.py` | il banco di A10, **esteso**: il giro vero (§11), la mappa vista→tela **misurata**, lo scorrimento sui pixel veri, la Panoramica, `spara()`, `accoppia_tasti()` |
| `banchi/04-b30-scena.c` | **una riga curata** (`oy` sommato due volte) |
| `banchi/04-b30-lancia.sh` | porte **7721-25**, utente `provao2`, `terreno` e `accendi` |
| ⭐ `banchi/04-b32-terreno.sh` | *nuovo* — utente, sessione **senza `--virtual-monitor`**, gruppo **`render`** verificato, prodotto, ponte, scena |
| ⭐ `banchi/04-b32-coda.py` | *nuovo* — la coda del decodificatore, misurata **mentre cresce**: stampa la **pendenza**, non una mediana |
| ⭐ `banchi/04-b32-ritmo.py` | *nuovo* — il ritmo in **quattro punti** della stessa catena, con le **attese a vuoto** accanto |
| ⛔ `src/pagina.html` | **il prodotto**: l'ancora `F4-CODA-DEL-DECODIFICATORE` (§4.1), dichiarata qui |

⛔ **Non ho toccato** `src/cattura.c`, `src/cattura.h` né `src/figlio.c`: ci lavorava O1 — e quando
la sua cura è arrivata a metà del mio lavoro **ho riportato l'albero, ricostruito e rimisurato da
capo**, invece di tenere i numeri di prima.

---

## Che cosa resta acceso sulla macchina di prova

⭐ **Lasciati accesi apposta**, come la 7571: prodotto **7722**, ponte **7721**, ancora **7723**,
scena su `Meta-0`, utente `provao2` con `linger`. ⇒ *«Si guarda adesso»*:
`https://192.168.0.2:7721/` come **`provao2`**, parola `provao2-2026`.
⛔ Si spengono con `bash banchi/04-b30-lancia.sh spegni`, e l'utente si toglie con
`sudo bash /media/REMOTIX/src/04-b32-terreno.sh pulisci`.
⚠ **Le porte altrui sono state contate prima e dopo ogni giro e non sono cambiate**: 7448 · 7501 ·
7561 · 7571 · **7700** (dove l'utente sta lavorando) hanno due ascoltatori ciascuna all'inizio e
alla fine.
