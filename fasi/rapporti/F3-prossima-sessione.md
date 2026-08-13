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
subito ───┼── B  LA CODIFICA HW ────────────┼──▶ GIUNZIONE 1 ──▶ E  L'ANELLO RIMISURATO ──┐
  in      ├── C  I 74,58: [M] o [?] ────────┘                                              ├──▶ GIUDIZIO
parallelo └── D  IL SECONDO MOTORE ──────────────────────────────────────────────────────  │
                                                                                           │
   sempre ─── K  IL CATALOGO (proprietario unico, serie) ──────────▶ GIUNZIONE 2 ──────────┘
```

⛔ **La regola che rende il parallelo possibile, ed è stata pagata oggi**: *ogni corsia ha **porta,
file di ban, socket, registro e COPIA del prodotto propri**. Due banchi che condividono un ban-file
si fermano a vicenda.* E il perimetro dei **file** è dichiarato per corsia: chi ne ha bisogno di uno
altrui **lo chiede al coordinatore**, non lo tocca.

⚠ **Le porte protette, sempre**: **7448** (prodotto di casa) · **7501** (bersaglio di P5) · ⛔
**7561, quella che l'utente apre** — si leggono e **non si toccano**.

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

## 🅐 CORSIA A — Lo scoglio HEVC: esiste un client che lo accetti?

**Parte subito. È la corsia più corta e la più bloccante: se dice no, il piano di misura cambia.**

| | |
|---|---|
| **Che cosa** | Il codec negoziato in tutte le misure del 13 è **AV1**, perché la sonda HEVC di quel Chrome **fallisce su Xvfb** (`EncodingError: Decoding error`). ⛔ **Senza un client che accetti HEVC, l'anello intero non si misura** — al massimo il lato server, e sarebbe **mezzo anello** |
| **La domanda** | ⇒ *Un client che accetti **HEVC Main10** su questo palco esiste, sì o no?* Chrome vero (non headless) · Chrome con GPU · Firefox · il telefono. ⛔ **Una risposta secca, con la prova sui pixel** |
| **Perimetro file** | `banchi/03-hevc-*` (nuovi). ⛔ **Niente `src/`, niente `.md`, nessun banco `03-b1x` esistente** |
| **Porta / palco** | **7621** · browser veri su CHUWI (Chrome 151, Firefox 140esr) |
| **Dipende da** | niente |
| **Consegna a** | ⛔ **GIUNZIONE 1**, ed è la metà che può bloccarla |
| **Ripiego se la risposta è NO** | si misura il **lato server soltanto** (quanto costa la codifica in hardware contro quella in software, a parità di fotogramma) e **si dichiara che è mezzo anello** — non lo si spaccia per l'anello |

---

## 🅑 CORSIA B — La codifica HEVC in hardware nel prodotto

**Parte subito. È il lavoro grosso.**

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

| # | | |
|---|---|---|
| **C1** | ⛔⛔ **il verdetto sul numero della fase** | `03-b17-ritardo.py --certifica` esce **30 su 31** da CHUWI (3 giri su 3, sempre lo stesso controllo, **del ponte**: *«fuori ordine: 0 inversioni su 40 pacchetti»*), mentre l'autore dichiarava **31/31**. ⇒ Se il controllo che cade **non entra** nel cammino della mediana, il numero **regge** e va detto **con la prova**; se ci entra, **il numero della fase è `[?]`** e chi riprende deve saperlo |
| **C2** | **dove si riproduce il 31/31, e perché no altrove** | due letture, e sono cose diverse: **(a)** differenza di macchina ⇒ limite dichiarato del banco; **(b)** **regressione** fra pomeriggio e sera ⇒ va nominata |
| **C3** | ⛔ **P5, il fuori ordine, non è MAI stato eseguito** | tre iniettori provati: 0 scavalcati su 200 · 0 su 220 · al terzo la pagina smetteva di consegnare. *«`scavalcati = 0` non è "l'anello regge", è "il fenomeno non si è presentato"»*. ⇒ Serve un fotogramma **grosso** (una chiave) mentre scorrono delta piccoli, o un iniettore che ritardi **un intero stream** invece che dei pacchetti |
| **C4** | ⚠ **il ponte è rotto o sta dicendo la verità?** | ⛔ **Non curarlo prima di aver risposto**: curare uno strumento che sta dicendo la verità è il modo di perdere l'unica riga onesta che c'era |

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

## 🅚 CORSIA K — Il catalogo: **proprietario unico**, e lavora in serie

⛔⛔ **Questa corsia esiste perché `banchi/01-b12-guasti.py` e il suo registro sono una RISORSA
CONDIVISA**: tre lavori diversi ci scrivono dentro. ⇒ **Un solo proprietario, che li fa in fila.**
Chiunque altro abbia bisogno del catalogo **glielo chiede**.

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
| **Porta / palco** | **7625**, copie proprie |
| **⛔ Vincolo** | ⛔ **K1 prima che B tocchi `codificatore.c`.** ⛔ **K6 solo dopo che il prodotto ha smesso di cambiare** — rigirare le certificazioni mentre `src/` si muove le fa scadere una seconda volta, ed è l'errore che il 13 agosto è nato per non ripetere |

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
| ⛔ **la scena deve stare sul monitor che si sta catturando** | il palco ha **quattro** monitor virtuali (`Meta-0…3`, tutti 1920×1080@60): il proprio si legge **dal registro del proprio server**, non si indovina. Una scena sul monitor sbagliato dà **zero fotogrammi per dieci secondi con la catena perfetta**. Costo: **quattro giri** |
| ⛔ **la scena accesa PRIMA della sessione non disegna** | Mutter non manda i *frame callback* a una superficie su un monitor che nessuno registra. Si accende **a sessione aperta** |
| ⛔ **su Xvfb `requestAnimationFrame` non gira MAI** | 0 quadri in 3 s, con e senza GPU, a scheda «visible». Ogni cammino di prodotto che ci passa dietro è **codice morto sul banco** |
| ⛔ **`curl` normalizza** | non manda il frammento e si mangia il `?` vuoto. Sul filo grezzo serve `--request-target`, o si misura curl |
| ⛔ **`&` dentro `ssh → enter.sh → bash -c`** non arriva dove sembra | **si usa un file, non una riga annidata** |
| ⭐ **la parola d'ordine di `sudo` sta in `~/SERVER.ssh`** | convenzione del progetto (`banchi/02-pam-lancia.sh:59`). Un gruppo si è fermato **per non saperlo** |
| ⛔ **il prodotto legge `pagina.html` UNA VOLTA SOLA all'accensione** | dopo ogni modifica **si riaccende**, o si prova la pagina di prima |
| ⛔ **su CHUWI il prodotto NON si compila** | manca `nghttp3/nghttp3.h`. Vive in un contenitore su **192.168.0.2** (`enter.sh`, sorgenti `/srv/src/remotix`); i **browser veri** stanno su CHUWI |
| ⛔ **`src/rcp.c` e `banchi/rcp/rcp.c` sono GEMELLI** | il `Makefile` pretende che siano identici: se divergono **nessuno compila**, e non si vede finché non ci si sbatte contro |
| ⚠ **`/tmp` su CHUWI, tmpfs da 3,8 G al 94 %** | quando si riempie, Chrome non apre il profilo e il banco fallisce con un errore che **accusa la pagina**. Si guarda il disco **prima** di credergli |

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
- ⛔ **e DUE righe ripetute invece che misurate hanno quasi deciso un piano**: i «37 fotogrammi di
  Mutter» e *«non c'è un codificatore hardware»*. **La seconda nella stessa giornata in cui si
  scopriva la prima.**

⇒ ⭐ **Zero volte i banchi hanno sbagliato a favore del prodotto.**
