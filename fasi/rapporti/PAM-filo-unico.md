# PAM esce dal filo unico — il rapporto

*12 agosto 2026. Mandato: `DECISIONI.md` **§1.10**, deciso dall'utente l'11 agosto alla chiusura
della fase 1. ⛔ È la prima modifica a `src/` dopo quella chiusura.*

---

## 0. In una riga

⛔ Il ciclo `poll` del server **non chiama più PAM**: la interroga un processo aiutante, e
`[M]` il tempo che chi **non** si sta autenticando passa fermo mentre qualcun altro sbaglia la
parola d'ordine è passato da **2259 ms a 3 ms**, sulla stessa scena, con lo stesso banco.

⚠ E il numero che **non** doveva cambiare non è cambiato: chi si autentica aspetta ancora
1,0-2,5 s, perché quel tempo lo mette PAM.

---

## 1. La forma scelta, e perché quella

§1.10 impone **un processo, non un filo** — *«PAM non è affidabilmente rientrante, e un thread
porterebbe guai suoi dentro la cura di un problema di concorrenza»*. ⭐ Qui si è andati un passo
oltre, e costa dieci righe: **la forma è a tre piani**, e ogni transazione PAM vive in un processo
che ne fa **una sola** e poi muore.

| chi | che cosa fa | perché così |
|---|---|---|
| **il server** | scrive una richiesta su un socket e torna al `poll` | ⭐ è tutto il punto: nessuna attesa dentro il ciclo asincrono (`CODER.md` §4.4) |
| **lo smistatore** | un figlio, acceso una volta all'avvio. ⛔ **Non chiama mai PAM nemmeno lui**: legge una richiesta e forca | è il solo processo di lunga vita in gioco, e non tocca `libpam` — quindi non può accumulare stato di nessuno |
| **il nipote** | chiama PAM **una volta**, scrive l'esito, esce | ⭐ **la rientranza di PAM così non è "gestita": non è in gioco.** Nessun processo che tocca `libpam` la tocca due volte, e i moduli di PAM — codice altrui, caricato a runtime, con dentro `getpwnam`, socket verso `nscd`, `dlopen` — non condividono niente con nessuno |

⭐ **E il secondo guadagno, misurato e non dedotto**: due che sbagliano la parola nello stesso
istante **non fanno la fila**. `[M]` `02-pam-i3.py --caso insieme`: il muro totale è **1939 ms**
mentre il più lento dei due ne ha presi 1849 e la somma sarebbe stata **3364**.

**Le scelte di dettaglio che si vedono solo nel codice:**

- ⛔ **`SOCK_SEQPACKET`, non `SOCK_STREAM`**: i confini dei messaggi li tiene il nucleo. Con uno
  stream l'inquadramento sarebbe stato nostro, cioè un pezzo di codice in cui un difetto produce
  *«la risposta di un altro»* — che è **I3 violata da un errore di parsing**;
- ⛔ **`socketpair()` anonimo**: non ha un nome nel filesystem, non ci si collega da fuori, muore con
  i due processi;
- ⛔ **si accende PRESTO**, prima di `trasporto_apri()` e `pagina_apri()`. Un `fork()` regala al
  figlio tutti i descrittori: acceso dopo, l'aiutante si porterebbe dietro il socket UDP e
  l'ascoltatore TCP, e alla morte del server **la porta resterebbe occupata da un processo che non
  la usa** — sintomo «indirizzo già in uso» senza nessun server in vista;
- ⛔ **`PR_SET_PDEATHSIG`**: se il server muore di brutto, l'aiutante muore con lui. Nessun orfano
  attaccato a un socket che nessuno legge.

---

## 2. ⛔ Come il fallimento diventa un **no**, e non un forse (I3)

L'invariante I3 (`CODER.md` §2) dice che la guardia parte da negato. ⭐ **Il `true` nasce in un solo
punto del programma**: il byte `1` che il nipote scrive dopo un `PAM_SUCCESS` su tutt'e due i passi
di `rcp_autentica()`. Ogni altro byte, ogni altra lunghezza e ogni silenzio sono un no.

Le sette strade per cui qualcosa può andare storto, e dove ciascuna sbuca:

| # | che cosa va storto | dove sbuca | esito |
|---|---|---|---|
| 1 | l'aiutante non si è acceso | `aiutante_chiedi` → `false` | **NO** |
| 2 | il socket è pieno (`EAGAIN`) | `aiutante_chiedi` → `false` | **NO** |
| 3 | più di 16 pratiche in volo | `aiutante_chiedi` → `false` | **NO** |
| 4 | lo smistatore è morto (EOF) | `muore()`: tutte le pratiche in volo | **NO** |
| 5 | il nipote è morto senza rispondere | la pratica scade (8 s, `aiutante.c`) | **NO** |
| 6 | la risposta è corta o storpiata | si scarta, poi (5) | **NO** |
| 7 | la risposta porta un byte che non è **esattamente 1** | `ri.esito == 1u` | **NO** |

⛔ **E ci sono quattro muri anche a valle**, in `rcp_verdetto()`: la sessione dev'essere viva e in
`attesa-verdetto`; il verdetto dev'essere stato **chiesto**; il numero di pratica dev'essere **il
suo** (è il muro che vale di più: senza, la risposta di un utente potrebbe ammetterne un altro); e
`verdetto_atteso` si spegne lì, così *«ho ricevuto due verdetti»* non diventa *«vince l'ultimo»*.

⛔ **E due reti di sicurezza indipendenti, in due processi diversi**: la scadenza dell'aiutante
(8 s) e `TETTO_VERDETTO` in `rcp.c` (12 s). ⚠ Sono due apposta — la prima non può scattare se a
essere guasto è proprio chi la tiene.

### ⭐ Il caso concreto, provato sul ferro

`banchi/02-pam-i3.py --caso morto`, `[M]` 12 agosto 2026, porta 7531:

1. si legge il pid dell'aiutante **dal registro di quel bersaglio** (non da `pgrep`, che troverebbe
   anche i server degli altri) e lo si ammazza con `SIGKILL` — così non può scrivere niente e
   nessun gestore può rispondere al posto suo;
2. si presenta la parola d'ordine **GIUSTA**.

```
⭐ OK  parola GIUSTA con l'aiutante morto -> RESPINTO(CREDENZIALI_ERRATE) in 1001 ms
⭐ OK  e il secondo fisso c'è lo stesso (1001 ms)
```

E il registro del server lo racconta per intero, senza che nessuno debba dedurlo:

```
⛔ l'aiutante di PAM non c'è più (il socket si è chiuso dal suo lato): le 0 verifiche in
   volo diventano NO, e ogni tentativo successivo sarà un NO (invariante I3).
⛔ la domanda a PAM non è partita: RESPINTO senza appello (invariante I3).  ⚠ E NON conta
   come tentativo fallito di §4.4-bis: il difetto è nostro…
⛔ e questo RESPINTO è NOSTRO, non di PAM: la verifica non è stata fatta.  ⚠ Sul filo il
   motivo è lo stesso (§4.4 vieta di distinguerli), e il conto di §4.4-bis NON è stato toccato
```

⭐ **Il controllo positivo accanto**, o quel rosso sarebbe verde per la ragione sbagliata:
`--caso libera` fa entrare `prova` con la parola giusta, `AMMESSO in 1004 ms`.

---

## 3. ⛔ I due numeri: quanto sta fermo chi **non** si sta autenticando

### 3.1 La scena, dichiarata

Tre connessioni, ciascuna con un mestiere (`banchi/02-pam-fermo.py`):

| | |
|---|---|
| **A** — «già dentro» | stretta di mano completa fino a `SESSIONE`. ⭐ È **il righello**: da attaccata manda `BANCO_MARCA` (§7.5) ogni 50 ms e cronometra il `BANCO_ESITO` che torna. È l'unica coppia domanda/risposta che RCP concede a una sessione ATTIVA alla fase 1 — ⭐ e dalla fase 2 al suo posto ci sarà un fotogramma, e il numero vorrà dire la stessa cosa: **quanto sta fermo lo schermo di chi sta già lavorando** |
| **C** — «il caso lento» | `CREDENZIALI` con la parola **SBAGLIATA**. ⛔ Il motivo del `RESPINTO` si pretende `0x07`: un `0x08 TROPPI_TENTATIVI` vuol dire che PAM **non è stata nemmeno interrogata**, e quel campione si butta dicendo perché |
| **B** — «la seconda che fa la stretta di mano» | nasce nell'istante in cui C manda `CREDENZIALI`, e si cronometra da zero a `ECCOMI` |

**Il denominatore**: prima della finestra si cronometrano ~20 marche a ciclo tranquillo. `[M]`
mediana **1,5 ms** in tutti i giri. Se non fosse piccola il righello sarebbe rotto, e il banco lo
dichiara invece di dividere per un numero che non ha guardato.

### 3.2 ⭐ L'atteso e il caso opposto, scritti PRIMA del giro

Sono in testa a `02-pam-fermo.py` e li stampa `--previsione`:

> ⛔ **Il caso opposto — che aspetto avrebbe una cura che NON funziona**: picco e stretta restano
> ≥ 900 ms **mentre il tempo di C non cambia**, cioè la stessa fotografia del «prima» con il codice
> nuovo dentro.

### 3.3 I numeri, `[M]` 12 agosto 2026, NIC-OS, porta 7531, 5 giri per lato

| | **prima** (fase 1) | **dopo** (la cura) | |
|---|---|---|---|
| ciclo tranquillo (denominatore) | 1,5 ms | 1,5 ms | il righello è lo stesso |
| ⛔ **picco della marca in finestra** | **2259 ms** *(max 2542)* | ⭐ **3,2 ms** *(max 4)* | **×706** |
| ⛔ **tempo fermo di A** (somma degli scarti) | **2258 ms** | ⭐ **2,3 ms** | |
| ⛔ **stretta di mano di B** | **2262 ms** | ⭐ **9,6 ms** | **×236** |
| ⚠ **chi si autentica (C)** | 2260 ms | **1844 ms** | ⭐ **non doveva cambiare, e non è cambiato**: quel tempo lo governa PAM (mediane di B8: 1086-2198 ms) |
| il secondo fisso su `AMMESSO` | 1001 ms | 1002-1004 ms | §4.4-bis regge |

⭐ **Il giro «prima» è anche il controllo positivo del banco**: il server della fase 1 il blocco ce
l'aveva, misurato, e questo righello **doveva vederlo**. Se non l'avesse visto, il «dopo» verde
sarebbe stato la peggiore delle prove (`CODER.md` §4.6).

### 3.4 La certificazione del banco: **sano → guasto → risanato**

⛔ Il guasto **è la cura tolta** — il gancio asincrono non collegato, cioè lo stato del server prima
di §1.10. È il guasto migliore che si potesse innestare: un difetto che è davvero esistito e che è
davvero stato misurato. Innestato **nella copia**, mai nel prodotto di casa.

| passo | picco della marca | verdetto |
|---|---|---|
| **sano** | **3,6 ms** | ⭐ verde |
| ⛔ **guasto** | **2640 ms** *(max 2801)* | ⛔ **rosso — il banco vede il proprio guasto** |
| **risanato** | **3,6 ms** | ⭐ verde |

**La riga per il catalogo delle certificazioni**, nella forma di `01-b12-guasti.py` (⛔ *non l'ho
scritta dentro quel file: è di un altro giro*):

| | |
|---|---|
| **nome** | `02-PAM` — «quanto sta fermo chi non si sta autenticando» |
| **comando** | `bash banchi/02-pam-lancia.sh misura libero 3` |
| **atteso sano** | picco della marca **< 150 ms**, stretta di B **< 300 ms** |
| **guasto da innestare** | `bash banchi/02-pam-lancia.sh guasto` — in `webtransport.c` si toglie `g.chiedi_verifica = gancio_chiedi;` |
| **atteso guasto** | picco della marca **≥ 900 ms** (misurato: 2640), e la marca *«atteso «libero»: il picco doveva essere < 150 ms»* con un `NO` accanto |
| **file che contano** | `02-pam-fermo.py`, `02-pam-i3.py`, `02-pam-accendi.sh`, `src/rcp.c`, `src/aiutante.c` |

---

## 4. ⛔ Che cosa ho fatto perché il secondo fisso e il ban restino quelli

La cura ha toccato **tutt'e due** nel codice, e per questo li ho misurati tutt'e due.

### 4.1 Il secondo fisso di §4.4-bis

⛔ **Che cosa è cambiato**: `attesa-verdetto` adesso aspetta **due** cose invece di una — il secondo
fisso *e* la risposta dell'aiutante — e **l'ordine fra le due non è garantito**. Prima la seconda
era già arrivata quando quello stato cominciava, perché PAM aveva bloccato il filo.

⭐ **Che cosa non è cambiato**: il secondo fisso resta un **pavimento, non un soffitto**. Una
risposta arrivata in 10 ms non fa uscire `AMMESSO` in 10 ms, perché §4.4-bis vuole che il
cronometro non distingua quel che il motivo non distingue.

`[M]` `02-pam-i3.py --caso secondo`:
```
⭐ OK  parola GIUSTA   -> AMMESSO in 1004 ms                    (atteso ≥ 1000)
⭐ OK  parola SBAGLIATA -> RESPINTO(CREDENZIALI_ERRATE) in 1878 ms (atteso ≥ 1000)
```
⭐ E vale anche sul rifiuto che **non viene da PAM**: con l'aiutante morto, `RESPINTO` a
**1001 ms**. Un rifiuto istantaneo direbbe col cronometro quel che il motivo non dice.

### 4.2 Il conto per indirizzo e il ban al quarto tentativo (`DECISIONI.md` §1.9)

⛔ **Che cosa è cambiato, ed è la modifica più rischiosa di tutto il lavoro**: `segna_fallito()` e
`azzera_falliti()` si sono **spostati** da `tratta_credenziali()` a `rcp_verdetto()`, perché è lì che
adesso esiste il fatto *«un tentativo è fallito»*. ⚠ Uno spostamento è precisamente il tipo di
modifica **che si legge bene e non fa niente** — la forma che **B5** ha già trovato una volta, con
il contatore che valeva sempre 1.

⭐ **Da cui la misura, e non la rilettura.** `[M]` `02-pam-i3.py --caso ban`:

```
-- fallito 1/3 (utente «prova»)             RESPINTO(CREDENZIALI_ERRATE) in 2546 ms
-- fallito 2/3 (utente «prova2»)            RESPINTO(CREDENZIALI_ERRATE) in 1975 ms
-- fallito 3/3 (utente «nessuno-di-questi») RESPINTO(CREDENZIALI_ERRATE) in 2182 ms
⭐ OK  e il QUARTO, con la parola GIUSTA -> RESPINTO(TROPPI_TENTATIVI) in 1001 ms
```

⛔ **Tre nomi utente diversi**, perché §4.4-bis conta l'indirizzo e non il nome — con un nome solo
si proverebbe la regola vecchia. ⭐ E il quarto **con la parola giusta**: è la prova che distingue
un ban da un contatore.

⛔ **E sopravvive al riavvio** (invariante I7): server spento, riacceso **conservando il file dei
ban**, e la parola giusta riceve ancora `TROPPI_TENTATIVI`.

⛔ **E una cosa che il ban NON deve fare, e adesso è scritta nel codice**: un «no» che viene da
**noi** — aiutante spento, pratica scaduta — **non incrementa il conto**. §4.4-bis dice che un
difetto del server che bannasse l'utente per dodici ore sarebbe *«la peggiore diagnosi che questo
progetto possa produrre»*, e con la verifica in un altro processo quel caso è diventato possibile
per la prima volta.

### 4.3 `CODER.md` §4.4 — non si aspetta mai dentro il ciclo asincrono

⛔ **La cura non ha spostato l'attesa altrove.** I punti in cui si sarebbe potuta reintrodurre, e
che cosa c'è al loro posto:

| dove | che cosa c'è |
|---|---|
| la scrittura della domanda | socket **non bloccante**; un `EAGAIN` è un **no**, non un'attesa |
| la lettura delle risposte | non bloccante, in un ciclo che esce su `EAGAIN` |
| la raccolta dell'aiutante morto | `waitpid(**WNOHANG**)`; se non è finito si riprova al giro dopo |
| lo spegnimento (`aiutante_spegni`) | ⚠ **aspetta** il figlio, e lo dichiara: sta **dopo l'ultimo giro del ciclo**, accanto ai 4 s di attesa dei congedi che §8.1 già impone. §4.4 vieta l'attesa **dentro** il ciclo |
| il nipote | `alarm(20)`, così un modulo PAM impiantato non lascia processi in eterno |

---

## 5. ⛔ Le certificazioni che questa modifica invalida

⛔ **`src/rcp.c` è stato toccato**, e §1.10 prevedeva di no (*«`rcp.c` non si tocca, quindi le
dodici certificazioni dell'11 agosto restano valide»*). ⚠ **Non era evitabile**, e la ragione è che
lo stato `attesa-verdetto`, il secondo fisso di §4.4-bis e il conto dei tentativi vivono lì dentro:
una verifica che non blocca ha bisogno di uno stato che sappia aspettare, e quello stato è di
`rcp.c`. Nessuna delle due alternative regge — parcheggiare la risposta sopra RCP vorrebbe dire far
parsare `CREDENZIALI` a `webtransport.c`, e restituire un verdetto provvisorio è I3 violata.

⇒ Il Makefile impone che `src/rcp.c` e `banchi/rcp/rcp.c` siano identici byte per byte (R12.3), e la
modifica è stata **portata in tutt'e due** — «se il cambiamento è voluto, va portato in tutte e due,
o il prodotto e il banco misureranno due codici diversi».

**`01-b12-guasti.py --registro`, dopo la modifica, dice che sono scadute per `rcp/rcp.c`:**

| banco | era certificato |
|---|---|
| **B3** | 12 ago 14:33, NIC-OS |
| **B5** | 11 ago 20:09, NIC-OS |
| **B6** | 12 ago 14:33, NIC-OS |
| **B7** | 12 ago 14:33, NIC-OS |
| **B8** | 12 ago 14:43, NIC-OS |
| **B13** | 12 ago 14:34, NIC-OS |

⚠ **Cinque delle sei erano state certificate oggi stesso**, da un altro giro: il prezzo è reale e va
pagato con un giro di ricertificazione, **non da me** (il mandato lo vieta) e non mentre le altre
lavorazioni sono vive.

⭐ **B10 è sopravvissuto**, e non per fortuna: la sua certificazione poggia su
`banchi/rcp/autenticazione.c`, e **`autenticazione.c` non è stato toccato di una riga**. Era un
obiettivo di progetto — `rcp_autentica()` è rimasta identica, e a cambiare è **chi** la chiama.

⭐ **E la ricertificazione dovrebbe essere a costo zero di comportamento**: sull'innesto il gancio
`chiedi_verifica` resta **NULL**, quindi `rcp.c` percorre la strada sincrona di prima, riga per riga.
Il gancio è stato aggiunto **in fondo** a `rcp_ganci` apposta: l'innesto inizializza per posizione
(`{nullptr, manda, chiudi, registra, verifica}`) e continua a compilare senza una modifica.

### ⛔ E una cosa che NON ho toccato, e che va toccata

**`RCP.md` §0-bis** porta righe e `md5` di `rcp.c` (2.592 righe, `md5 1adce15b…`), e quella casella
dichiara che `src/rcp.c` e `banchi/rcp/rcp.c` sono identici. ⛔ **Adesso è stantia**: `rcp.c` è a
**2.764 righe** con `md5 6d858886…`. Non l'ho corretta perché il mandato mi vieta `RCP.md` e §9 è
chiusa. ⚠ **Il filo non è cambiato di un byte** — nessun tipo nuovo, nessun motivo nuovo, nessun
campo nuovo — quindi non è un cambio di protocollo: è una casella di censimento da riallineare.

---

## 6. ⭐ Due difetti trovati dal banco, e tutt'e due erano **del banco**

`REVIEWER.md` §1: *il banco è il primo imputato.* Due volte in un pomeriggio.

| | |
|---|---|
| ⛔ **il ban «non sopravviveva al riavvio»** | e sopravviveva benissimo: era il mio `accendi` che **cancellava il file dei ban** a ogni accensione. ⇒ **rosso pieno su un prodotto sano**. Curato separando `accendi` (parte da uno stato noto) da `riaccendi` (conserva il file, perché quel file **è** la cosa da provare) |
| ⛔ **«l'aiutante è ancora vivo dopo `SIGKILL`»** | era uno **zombie**: il server non lo raccoglieva, e in `/proc` uno zombie e un processo vivo hanno **la stessa faccia**. ⭐ Curato in tutt'e due i posti: il banco legge lo stato vero (`Z` = morto) da `/proc/<pid>/stat`, e **il prodotto adesso lo raccoglie** con `waitpid(WNOHANG)` appena si accorge che è morto — perché «l'aiutante è morto» e «l'aiutante non muore» non devono avere la stessa faccia per chi diagnostica |

⚠ E un terzo, che non ha prodotto un numero sbagliato solo per fortuna: il passo che ammazza
l'aiutante era scritto **dentro tre livelli di virgolette** (`ssh` → `enter.sh` → `bash -c`), è
morto su un `$(...)`, ⛔ **e il caso «l'aiutante è morto» è girato lo stesso su un aiutante vivo**,
dando un rosso a un server sano. Spostato in un file dentro il contenitore — *«un file non ha
livelli di virgolette»*, che è la lezione già scritta in `01-p5-accendi.sh`.

---

## 7. I file

| file | |
|---|---|
| `src/aiutante.h` · `src/aiutante.c` | ⭐ **nuovi** — il processo aiutante, i tre piani, le sette strade che portano a un no |
| `src/rcp.h` · `src/rcp.c` | il gancio `chiedi_verifica` (in fondo alla struttura), `rcp_verdetto()`, `TETTO_VERDETTO`, e il conto di §4.4-bis spostato dove adesso esiste il fatto |
| `banchi/rcp/rcp.h` · `banchi/rcp/rcp.c` | la copia gemella, allineata byte per byte (R12.3) |
| `src/webtransport.h` · `.c` | `gancio_chiedi`, `wt_verdetto()`, l'aiutante che attraversa lo strato senza esserne posseduto |
| `src/trasporto.h` · `.c` | `trasporto_verdetto()`: il verdetto si passa a tutte le connessioni vive e una sola lo prende — ⭐ nessuna tabella di puntatori a connessioni che possono morire mentre PAM risponde |
| `src/main.c` | l'aiutante acceso **presto**, il suo descrittore nel `poll`, le scadenze fatte scorrere **anche quando non arriva niente**, e il riquadro «UN SOLO FILO» riscritto |
| `src/Makefile` | `aiutante.c` fra i sorgenti. ⚠ **Non** fra i `GEMELLATI`: è del prodotto e basta |
| `SPECIFICHE.md` §5.5 | il riquadro del ripiego: il primo dei due è curato, con i due numeri |
| `banchi/02-pam-fermo.py` | ⭐ **il banco che §1.10 dichiarava mancante** — «mentre uno si autentica, gli altri non se ne accorgono» |
| `banchi/02-pam-i3.py` | I3, il secondo fisso, il ban, I7, e le due autenticazioni in parallelo |
| `banchi/02-pam-accendi.sh` · `02-pam-lancia.sh` | il bersaglio sulla **7531** con prefisso proprio, il guasto da innestare, e lo sblocco sempre dichiarato |
| `banchi/02-pam-esiti.jsonl` | un esito per giro, con la scena dentro |

**La macchina, prima e dopo**: `[M]` 7448 e 7501 accese all'inizio (2 ascoltatori ciascuna) e accese
alla fine, con lo stesso pid (`211429`, `201326`). ⚠ La **7522** c'era all'inizio e non c'è più: non
è mia — il suo padrone l'ha spenta alle 14:58:54 con il proprio `spegni`, e il suo registro porta il
congedo `0x0c` regolare e il file del pid rimosso. Il mio bersaglio sulla 7531 è **spento**.

---

## 8. Le `[?]` che restano

| | |
|---|---|
| ⚠ **il tetto di 16 pratiche in volo** | è **letto, non misurato**: nessun giro ha mai messo 17 autenticazioni insieme sul filo. La strada che ne esce è un `false` → un no, cioè la direzione giusta, ma il caso non è stato visto |
| ⚠ **il `[?]` del secondo fisso resta aperto**, e non è questa cura a chiuderlo | §4.4-bis vuole che il cronometro non distingua l'ammesso dal respinto. `[M]` ammesso ~1004 ms, respinto 1500-2600 ms: ⛔ **si distinguono benissimo**, e a distinguerli è `pam_faildelay`. È lo stesso `[?]` che B8 ha aperto l'11 agosto e la cura non lo tocca — ⭐ ma adesso il prezzo lo paga **solo chi si autentica**, non più tutti gli altri |
| ⚠ **la ricertificazione dei sei banchi** | è dovuta, e non è mia (§5) |
