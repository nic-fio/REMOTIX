# R2 — Revisione avversariale di `web.md`

*9 agosto 2026. Revisione della sintesi `web.md` (330 righe) contro le quattro fonti:
`S1-certificato.md` (920), `S2-decodifica.md` (732), `S3-tastiera-appunti.md` (1.391),
`S4-ritardo-disegno.md` (671).*

**Che cosa ho fatto.** Ho riportato alla fonte **96 affermazioni** di `web.md`: ogni citazione
`[R]`/`[S]`, ogni cifra (versioni, date, conteggi, millisecondi, percentuali), ogni cella delle
tabelle, ogni rimando a `SPECIFICHE.md`, `DECISIONI.md` e `RCP.md`. Ho letto i quattro rapporti
per intero, non i loro sommari.

**Esito.** **17 affermazioni non tornano** — sette cambiano una decisione o rompono un banco — e
**12 cose che i rapporti dicono, e che avrebbero cambiato una decisione, la sintesi tace**.
⚠ Il conto va letto al netto: **la sintesi è fedele nella grande maggioranza dei punti**, e §3 lo
dichiara punto per punto. Va corretta in diciassette righe, non riscritta.

⛔ **E un'aggravante di tempistica**: `SPECIFICHE.md` §7.3-bis, `SPECIFICHE.md` §9 e
`DECISIONI.md` §1.7 sono **già stati riscritti citando `web.md`**. Tre dei rilievi qui sotto sono
quindi già passati nei documenti normativi del progetto, e la correzione va fatta in due posti.

⛔ **Non ho misurato niente e non ho modificato nessun file del progetto** (`REVIEWER.md` §5).
Nessun rilievo porta la marca `[M]`.

---

## 1. I rilievi, dal più grave al meno grave

*«Grave» = quanto costerebbe costruirci sopra prima di accorgersene.*

---

### R1 — Il controllo positivo del primo banco del progetto è stato sostituito con uno che non distingue lo zero dal fallimento

```
DOVE:             web.md §3.3, riquadro «Il banco», e §7 riga S1a
COSA CONTRADDICE: S1 §4.2 e §4.4; LEZIONI.md §1.9 regole 1 e 2; REVIEWER.md §1
                  punti 4 e 5
```

**Come si dimostra.** `web.md` §3.3 scrive: *«Il controllo positivo è ovvio e va fatto lo stesso:
**la stessa prova su Chrome deve fallire** — se passasse, il banco non sta misurando quel che
crede»*.

S1 §4.4 dice il contrario, e con la ragione scritta: *«Perché nello stesso giro, sullo stesso
browser, sulla stessa pagina, **P2 riesce e P3 fallisce**. […] Se P2 fallisse, non sto misurando
S1: sto misurando **un server che non risponde**»*. E S1 §4.2: *«Senza di loro, un fallimento di P1
non distingue "il browser rifiuta l'eccezione" da "il server non risponde su UDP 7447"»*.

Il caso concreto che rompe il controllo di `web.md`: **il firewall del server blocca UDP 7447**.
Allora P1 fallisce su Safari *e* fallisce su Chrome — cioè il controllo di `web.md` è **verde** — e
il banco scrive «l'eccezione di Safari non copre», che è la conclusione sbagliata sul dato mancante.
Il controllo di S1 (P2, `serverCertificateHashes` sulla **stessa** pagina) avrebbe detto «il canale
non c'è». È testualmente «vuoto» e «proibito» che hanno lo stesso aspetto (`LEZIONI.md` §1.9).

⛔ **E il costo è massimo perché è la prima misura**: `web.md` §3.3 la dichiara *«la prima misura del
progetto, e non ne serve nessun'altra prima»*. Un banco cieco messo per primo avvelena tutto quel
che viene dopo (`LEZIONI.md` §10).

```
MARCA: [R]
```

---

### R2 — «Safari non ha `serverCertificateHashes`» è l'errore che S1 corregge per nome, e `web.md` non riporta la correzione

```
DOVE:             web.md §3.1 (riga Safari), §3.2 (riga «la strada»), §7 riga S1a,
                  §8 (prima riga)
COSA CONTRADDICE: S1 §1.5, §2 (matrice), §3.3, §3.8 (il riquadro di chiusura), §5.8;
                  e, a valle, DECISIONI.md §1.7
```

**Come si dimostra.** S1 §3.3 dedica una sezione intera a questo, con la cronologia e il codice:
WebKit **ha implementato** `serverCertificateHashes` il 2 ottobre 2025 (bug 300057, `RESOLVED
FIXED`), l'implementazione sta in `NetworkTransportSessionCocoa.mm:77`, `:126-129`, `:222`, ed è
spedita in **Safari 26.4** `[R]`. S1 chiude con un riquadro esplicito:

> *«⚠ Una correzione al filone di ricerca, per non tramandare un errore. La ricerca secondaria
> riportava che "`serverCertificateHashes` funziona in modo affidabile solo su Chrome […] Safari da
> decidere". **È falso, e il codice lo smentisce**»*.

`web.md` **non riporta mai** che Safari abbia `serverCertificateHashes`. La riga Safari di §3.1
parla solo dell'eccezione e del portachiavi; §3.2 dice *«la strada: `serverCertificateHashes»*
senza dire su quali motori.

**Le due conseguenze, entrambe già pagate:**

1. `web.md` §7 motiva S1a così: *«decide se iPhone e iPad hanno **una strada senza dominio**»*.
   **È falso**: la strada senza dominio su iPhone c'è già ed è la stessa degli altri due motori.
   S1 §5.8 lo scrive testualmente: *«il codice del client deve usare `serverCertificateHashes`
   **sempre** […]; se poi Safari accettasse anche senza, sarebbe **un ripiego in più**, non un
   percorso diverso»*. S1a decide una comodità, non l'esistenza di una piattaforma — e con essa
   cade la ragione per cui `web.md` la mette per prima davanti a tutto;
2. `DECISIONI.md` §1.7, riscritta *«dopo la misura S1»*, contiene ancora:
   `[?] **Safari e iPhone restano il buco dichiarato**: WebKit non implementa
   serverCertificateHashes [S]`. È **esattamente** l'affermazione che S1 dichiara scaduta, rimasta
   in piedi perché la sintesi non ha trasportato la correzione.

```
MARCA: [R]
```

---

### R3 — La forma della pagina è fissata da S4 ignorando il vincolo opposto di S3, e i due si scontrano

```
DOVE:             web.md §6.1, riquadro «⚠ E impone la forma della pagina»
COSA CONTRADDICE: S3 §3.A.4 (chiusura) e §3.A.6; S4 §5.1 regola 6
```

**Come si dimostra.** `web.md` §6.1 chiude la forma della pagina in due mestieri e due thread, e
aggiunge: *«deciderlo adesso costa niente, scoprirlo alla fase 4 costa una riscrittura»*.

Ma i due rapporti impongono vincoli che si toccano, e **nessuno dei due autori poteva vederlo**:

| Da dove | Il vincolo |
|---|---|
| **S3** §3.A.4 | *«le lettere devono uscire da `beforeinput` […] e questo obbliga la pagina ad avere **un elemento modificabile con il fuoco** anche sul desktop, non solo su Android»* `[R]` — è l'`InputSink` di Guacamole, e senza di esso accenti e tasti morti non si producono |
| **S4** §5.1 regola 6 | *«niente `transform`, niente `border-radius`, **niente elementi sopra la tela**»* `[S]` `[R]` — perché una decorazione sopra il video fa cadere overlay e percorso desincronizzato (`overlay_processor_win.cc`: *«If the video is underneath e.g. controls or captions, we cannot remove the primary plane»*) |

Il caso concreto: si scrive la pagina con la sola tela nel worker (§6.1), si arriva alla fase 4, si
scopre che `^`+`e` non produce `ê` su nessun motore, si aggiunge la `textarea` nascosta sopra la
tela — e **si perde il percorso di disegno su cui tutto §6 è costruito**. È precisamente la
riscrittura che §6.1 dice di voler evitare, e la sintesi era l'unico posto dove si poteva vedere.

⚠ **È la terza convergenza vera fra i rapporti, e non è nella lista delle tre di §1.2.**

```
MARCA: [R]
```

---

### R4 — «Nessuna [misura] richiede una riga di prodotto» è smentito da due rapporti su quattro, e dallo stesso `web.md`

```
DOVE:             web.md §7, riga d'intestazione del piano delle misure
COSA CONTRADDICE: S4 §5.3 punto 5 e §4.1; S2 §5 esito C; e web.md §1.2 C e §4.3
```

**Come si dimostra.** S4 §5.3 punto 5, verbatim: *«**RCP: la marca del banco è un'estensione di
protocollo.** Il rettangolo di 16×16 e il comando che lo cambia (con il ritardo `N` iniettabile del
controllo P1) **vanno scritti in `RCP.md` come funzione di banco**, non improvvisati nel codice di
prova»*. L'anello di S4 §4.1 richiede inoltre che **il server** sappia disegnare la marca su comando
e ritardare di N ms noti: due funzioni che oggi non esistono.

E `web.md` si contraddice da solo a tre sezioni di distanza: §1.2 C — *«la diagnosi non può stare in
un banco di laboratorio: **deve stare nel prodotto**»* — e §4.3 — *«questo banco non resta in
laboratorio: la stessa misura, ridotta, **vive nel prodotto**»*.

Il costo: si pianifica la fase 1 come «solo banchi, zero prodotto», e a metà si scopre che due delle
sei misure aprono `RCP.md` e il server.

```
MARCA: [R]
```

---

### R5 — Un `[S]` del 2023 che S2 dichiara **non verificato** è diventato un `[R]`, e ci poggia sopra la richiesta di rendere provvisoria `DECISIONI.md` §2.2

```
DOVE:             web.md §1.2 A, riga «S2» della tabella
COSA CONTRADDICE: S2 §3.7 e §7 («Non l'ho trovato»); LEZIONI.md §2.3-quater;
                  REVIEWER.md §2 forma E5
```

**Come si dimostra.** `web.md` scrive: *«sui fotogrammi decodificati in hardware `VideoFrame.format`
è **null** e `copyTo()` è negato `[R]`»*.

S2 §3.7 marca la stessa affermazione **`[S]`** — è una *discussion* W3C (#631) di **Dale Curtis,
30 gennaio 2023** — e subito dopo dichiara il limite, verbatim:

> *«`[?]` **Non ho potuto verificare lo stato preciso dell'implementazione Chromium ad agosto
> 2026: dichiaro questo come non verificato**, non come assente. È la prima cosa che il banco deve
> accertare.»*

E S2 §7 lo ripete nella colonna **«Non l'ho trovato (assenza non dimostrata)»**: *«Lo stato preciso,
ad agosto 2026, dell'esposizione di `I420P10` […]. L'ultima fonte datata è del 2023»*.

⛔ **Perché costa**: quella riga è **una delle tre** su cui `web.md` §1.2 A costruisce la richiesta
di riscrivere provvisoria `DECISIONI.md` §2.2, cioè un desiderato deciso dall'utente. Una decisione
dell'utente si sposta con tre indizi, non con due indizi e una fonte di tre anni fa promossa di
marca. (La stessa `LEZIONI.md` §2.3-quater che `web.md` cita a sostegno è la lezione che vieta
questo.)

```
MARCA: [R]
```

---

### R6 — «Compra la tastiera intera» è più forte di quel che S3 sostiene, e `web.md` si smentisce da solo trenta righe dopo

```
DOVE:             web.md §1.2 B (conclusione in grassetto)
COSA CONTRADDICE: S3 §2.1, §2.2, §2.4 (tabella dei sistemi), §5.1-bis, §5.5;
                  e web.md §5.2 e §5.5
```

**Come si dimostra.** La convergenza B incrocia due `[R]` veri. La conclusione che ne trae — *«il
certificato vero […] **Compra la tastiera intera**»* — non regge su quattro punti, tutti in S3:

1. **La lista vuota della PWA è quella del *browser*, non del sistema.** S3 §2.4 «Il sistema
   operativo — quel che nessun browser recupera»: su macOS `⌘Spazio`/`⌘Tab`/screenshot sono
   **irrecuperabili su qualunque browser** `[R]`; su Android/DeX **qualunque combinazione con Meta**
   è persa per regola AOSP `[R]`. La PWA non tocca né gli uni né gli altri;
2. **il guadagno marginale è piccolo, non intero.** S3 §2.4 riga «Recuperabile»: le dodici riservate
   di Chrome sono recuperabili *«sì, con la lock — **e anche solo con lo schermo intero**»*, dove ne
   restano **due**. Fra «schermo intero + lock» e «PWA» ballano `F11` e l'uscita — e l'uscita la
   **specifica obbliga** a riservarla (S3 §2.2: *«User agents should reserve an additional input for
   the purposes of exiting fullscreen»*). Cioè: la PWA non arriva a «tutto» nemmeno su Chrome;
3. **vale solo su Chrome.** Su Firefox restano le sei riservate e `Ctrl+Tab` in **stato B**; su
   Safari la PWA non c'entra niente;
4. ⛔ **e sull'uso primario è una `[?]`.** S3 §5.1-bis: *«`[?]` **resta da misurare se valga anche
   per Chrome per Android**»*. Lo dice anche `web.md` §5.5 — *«le due `[?]` che contano di più […]
   se la PWA valga anche su Chrome per Android»* — e §7 riga S3b. **La stessa sintesi dà per
   acquisito in §1.2 quel che dichiara incerto in §5.5**, e in §1.2 la riga porta `[R]` senza `[?]`.

⛔ **Ed è già propagato**: `SPECIFICHE.md` §7.3-bis e `DECISIONI.md` §1.7 riportano la frase parola
per parola, citando `web.md` §1.2 B.

```
MARCA: [R]
```

---

### R7 — Due progetti diversi con nomi simili sono stati fusi, e ne esce un'affermazione che S2 smentisce esplicitamente

```
DOVE:             web.md §6.2, riquadro «⭐ La leva, se servisse»
COSA CONTRADDICE: S2 §3.10 (riga moonlight-web); S4 §3.9 e §6; S4 §3.4
```

**Come si dimostra.** `web.md` scrive: *«Selkies e **moonlight-web** non dipingono su canvas —
mandano i fotogrammi a un elemento `<video>` per prendere il percorso **overlay**, che salta il
compositore `[R]`»*.

Sono **due progetti diversi**:

| Nome | Chi | Che cosa fa |
|---|---|---|
| **moonlight-web** (`linckosz`) — citato da **S2**, e da `web.md` stesso in §4.2 | S2 §3.10 | ⛔ *«il video **non** va in `<video>`: WebCodecs in un worker → **WebGPU**»* |
| **moonlight-web-stream** (`MrCreativ3001`) — citato da **S4** | S4 §3.9, §6 | è questo che usa `MediaStreamTrackGenerator` → `<video>` |

Quindi `web.md` fa dire a `moonlight-web` — lo stesso progetto che cita due sezioni prima per
l'Annex-B — l'esatto contrario di quel che S2 ha letto nel suo codice.

**E la marca è gonfiata due volte.** «Che salta il compositore» in S4 §3.4 è `[S]` (riassunto
Khronos), accompagnato da: *«⛔ **Ma attenzione a come è giustificato**: la documentazione ufficiale
motiva gli overlay con **il consumo**, non con la latenza […] `[?]` Il guadagno di latenza
plausibile è **al più un quadro di compositore**, e **non ho trovato una fonte Chromium che lo
quantifichi**»*. `web.md` presenta una leva di latenza `[R]` dove S4 ha un'ipotesi `[?]` su un
beneficio energetico documentato. Cadono anche le condizioni di promozione (qualunque decorazione
sopra il video la fa fallire, S4 §3.4).

```
MARCA: [R]
```

---

### R8 — «Canvas 2D desincronizzato […] è anche l'unica che funziona su tutti e tre i motori»: la condizione cade e la frase diventa falsa

```
DOVE:             web.md §6.1
COSA CONTRADDICE: S4 §2 (righe A e A′), §3.1, §5.2 (ultima riga)
```

**Come si dimostra.** S4 §2 separa **A** (canvas 2D `drawImage`, ✅ su tutti e tre) da **A′** (lo
stesso *con* `{desynchronized:true}`), e la riga A′ dice: **Chrome ✅ ⛔ rotto su macOS `[S]`;
Firefox ❌ `[S]`; Safari ❌ `[S]`**. S4 §3.1 dà la fonte per ciascuno (bug Mozilla 1536809; thread
`graphics-dev` su `IOSurfaceImageBacking` sotto Metal), e S4 §5.2 lo mette fra le cose che vogliono
un interruttore: *«**`desynchronized`** — acceso di norma — ⛔ **rotto su macOS** `[S]`: serve un
interruttore per spegnerlo»*.

`web.md` fonde A e A′ in una riga sola e attribuisce alla combinazione l'universalità che vale solo
per A. Chi legge scrive il codice senza l'interruttore, e su macOS trova un canvas rotto senza
sapere perché. Cade anche la regola 8 di S4 §5.1: *«`ctx.getContextAttributes().desynchronized` si
legge e si dichiara — è una **richiesta**, non una garanzia»*.

```
MARCA: [R]
```

---

### R9 — La scadenza a sette giorni dell'eccezione di Chrome è stata **declassata** da fatto letto nel codice a incognita

```
DOVE:             web.md §3.3 («`[?]` La seconda: […] Il rapporto dice circa sette giorni —
                  **se fosse vero**») e §8 (riga «la durata dell'eccezione su Chrome»)
COSA CONTRADDICE: S1 §3.1 e S1 §7 («Che cosa questo rapporto non sa»)
```

**Come si dimostra.** S1 §3.1 legge la costante e il commento:
`kCertErrorBypassExpirationInSeconds = 604800` — *«Certificate error bypasses are remembered for one
week»* (`stateful_ssl_host_state_delegate.cc:43`), marcato **`[R]`**. Non è «circa sette giorni», è
una settimana esatta scritta nel sorgente. E S1 §7 — la lista di quel che il rapporto **non** sa —
ha sette voci e **la durata non è fra queste**.

`web.md` §8 la mette invece fra *«quel che questo studio NON sa»*. È il rovescio di E5: una cosa
stabilita declassata a `[?]`.

⛔ **E con il declassamento sparisce la conseguenza, che è la parte cara.** S1 §3.1 la scrive in un
riquadro: *«l'eccezione di Chrome è legata all'**impronta** del certificato e dura **7 giorni**»*.
Cioè: **anche con il certificato della pagina longevo e stabile — la cura che `web.md` §3.2
prescrive — su Chrome l'avviso torna ogni sette giorni.** `web.md` §3.2 dice solo che *«confonderli
fa ricomparire l'avviso ogni due settimane»*, lasciando credere che tenendoli distinti il clic sia
uno solo. La frase che si dice all'utente cambia, e `DECISIONI.md` §1.7 la porta già come `[?]`.

```
MARCA: [R]
```

---

### R10 — «1,5-2,5 intervalli di quadro: 16-40 ms a 60 Hz»: i due numeri non stanno insieme

```
DOVE:             web.md §6.2 e §1.1 riga 5
COSA CONTRADDICE: S4 §3.4 contro S4 §1.3 e §4.3
```

**Come si dimostra.** A 60 Hz T = 16,7 ms. 1,5 T = **25 ms**, 2,5 T = **42 ms**. S4 §3.4 scrive
infatti: *«cioè `[?]` **1,5–2,5 T**, che a 60 Hz fa **25–42 ms** e a 120 Hz **12–21 ms**»*.
L'intervallo **16–40 ms** compare altrove in S4 (§1.3, §4.3 riga «totale», §5.3), come stima del
tratto cieco complessivo.

`web.md` ha saldato la **frazione** di un punto del rapporto al **totale** di un altro, e ne esce
una riga che non torna con l'aritmetica. Chi la userà per dimensionare il tetto sbaglierà di 9 ms
sull'estremo basso — su un tetto di 50, e su un numero che `web.md` chiede di scrivere accanto al
tetto in `SPECIFICHE.md`.

⚠ Nota per il coder: **la contraddizione nasce in S4**, che porta i due numeri in due punti senza
riconciliarli. La cura sta lì, non solo nella sintesi.

```
MARCA: [R]
```

---

### R11 — «WebCodecs · Chrome per Android **147**»: la cifra non esiste in nessuno dei quattro rapporti

```
DOVE:             web.md §2, riga «WebCodecs» della mappa
COSA CONTRADDICE: S2 §2.1 e §2.2
```

**Come si dimostra.** S2 §2.1 dà `VideoDecoder` **94** per Chrome su *«Windows, macOS, Linux,
**Android**, ChromeOS»*, e S2 §2.2 dà HEVC Main10 su Chrome Android da **108.0.5343.0**. Nessuna
delle due è 147.

Cercato `147` nei quattro rapporti: compare **solo in S1** §3.5 e §7, e significa un'altra cosa —
*«**Local Network Access** (Chrome 147+)»*. È una contaminazione fra due rapporti diversi dentro
la stessa riga di tabella.

⛔ **E nella stessa riga manca il dato che cambia una piattaforma**: S2 §2.1 e §2.2 dicono
`VideoDecoder` **assente in release su Firefox Android** (solo Nightly) e HEVC **assente**. Cioè
Firefox su Android **non può essere un client**, e questo non è scritto da nessuna parte in
`web.md`, che altrove tratta Firefox come uno dei tre motori serviti.

```
MARCA: [R] per la cifra; [?] su quale numero volesse dire
```

---

### R12 — «Chrome/Edge restano sulla vecchia `navigator.keyboard.lock()`» è dato per fatto dove S3 dichiara di non esserci riuscito

```
DOVE:             web.md §5.1, riga «non è più solo Chrome»
COSA CONTRADDICE: S3 §6.4 (riquadro «Un limite di questa ricerca, dichiarato») e §5.1
```

**Come si dimostra.** S3 §6.4, verbatim:

> *«⛔ **non sono riuscito a stabilire da fonte diretta se Chrome supporti oggi
> `requestFullscreen({keyboardLock:"browser"})`.** `browser-compat-data` non ha ancora una voce […];
> `chromestatus` ha solo la voce del 2018 […]. **È `[?]`, ed è una riga del banco**»*.

`web.md` la scrive come un fatto, dentro una riga marcata `[S]`.

⛔ **E cade con essa la trappola che S3 §5.1 mette in guardia di non ripetere**: *«`requestFullscreen`
**ignora in silenzio** le opzioni che non conosce: chiamarlo con `{keyboardLock}` su Chrome **non
fallisce**, semplicemente non blocca niente. ⛔ **Il banco deve provare l'effetto, non l'esistenza**
— è la stessa lezione di `KWIN_COMPOSE=O2`, l'interruttore inerte (`LEZIONI.md` §1.11)»*. È la
lezione che `web.md` §9.1 celebra a parole nella sezione delle lezioni, e omette dove serviva.

```
MARCA: [R]
```

---

### R13 — «La conversione che `RCP.md` §7.3 richiede, già scritta e verificabile»: vera per una tabella su tre

```
DOVE:             web.md §5.4 punto 2
COSA CONTRADDICE: S3 §3.A.3, «Terza sorpresa» e le tre conseguenze
```

**Come si dimostra.** S3 §3.A.3 conta le tabelle e le trova **diverse**: Chromium **197** nomi
`code`, Gecko **159**, WebKitGTK **156** `[R]`. E ne trae tre conseguenze operative, tutte assenti
in `web.md`:

1. *«⛔ deve accettare **gli alias**: `VolumeUp` **e** `AudioVolumeUp`; `OSLeft` **e** `MetaLeft`;
   `LaunchMediaPlayer` **e** `MediaSelect`»*;
2. *«⛔ `""` e `"Unidentified"` sono **lo stesso caso**, e vanno nel registro come "posizione non
   determinabile", **mai indovinati»*;
3. la stringa vuota di Chromium è *«una **violazione di specifica**»*, non un valore da mappare.

Il caso concreto: si copia `dom_code_data.inc` come dice `web.md`, un utente Firefox preme il tasto
volume, arriva `VolumeUp`, il dizionario non lo conosce, e il server o tace o indovina — che è
esattamente il divieto di `SPECIFICHE.md` §7.3 (*«mai una lettera diversa, mai un silenzio»*).
`web.md` §5.4 dice invece che la conversione è **«già scritta e verificabile»**: una frase vera in
generale che diventa falsa quando le si toglie il contorno.

```
MARCA: [R]
```

---

### R14 — «Non si converte niente, e si risparmia una copia»: S2 dice che su Safari la conversione si paga

```
DOVE:             web.md §4.2, riga «il formato del flusso» e la chiusura
                  «⭐ La strada pigra è anche quella giusta»
COSA CONTRADDICE: S2 §3.5, sottosezione «E Safari?» e il riquadro «⭐ Il quadro completo»;
                  S2 §3.5(a)
```

**Come si dimostra.** S2 §3.5 chiude così, verbatim:

> *«⭐ **Il quadro completo**: **non esiste un percorso gratis per entrambi i browser.** Chromium
> converte hvcC → Annex-B; WebKit converte Annex-B → hvcC. **Dando Annex-B paghiamo la conversione
> solo su Safari**; dando hvcC la paghiamo su Chrome *e* rischiamo la trappola del PTL. Annex-B
> vince.»*

La conclusione (Annex-B) è la stessa; **la ragione che `web.md` le mette accanto è più forte del
vero**, e su Safari è falsa. Un rapporto onesto sul costo per fotogramma su iPhone partirebbe da
qui, e `web.md` lo toglie.

⚠ **E nella stessa riga una marca contaminata**: *«è quel che `hevc_vaapi` già produce»* è
marcato **`[?]`** in S2 §3.5(a) — è una deduzione su `libavcodec` più la condizione operativa
*«Basta **non** impostare `AV_CODEC_FLAG_GLOBAL_HEADER`»*, che `web.md` non riporta. Nella riga di
`web.md` finisce sotto lo stesso `[R]` degli altri due fatti.

```
MARCA: [R]
```

---

### R15 — Il banco di S2 perde il controllo che verifica il falso positivo

```
DOVE:             web.md §4.3, riga «⛔ il controllo positivo»
COSA CONTRADDICE: S2 §4.4, controlli A, B e il «criterio di validità»;
                  REVIEWER.md §1 punto 5
```

**Come si dimostra.** `web.md` riporta il solo **controllo A** (VP9 forzato in software). S2 §4.4 ne
chiede **due**, e mette il criterio in una riga sola:

> *«**Il criterio di validità del banco, in una riga**: *il banco è valido se, sullo stesso telefono,
> dichiara **software** il controllo A **e hardware** il controllo B.* Finché non lo fa, non pubblica
> verdetti.»*

Senza il controllo B (VP9 con `prefer-hardware`, che ogni telefono decodifica in hardware) un banco
che chiama «software» qualunque cosa — perché la soglia è tarata male, o perché il telefono è lento
— passa il controllo A e produce un verdetto «HEVC è software» che nessuno può smentire. È un banco
che sa dire di no e non sa dire di sì.

⚠ Cade anche il **controllo C** di S2 §4.4 (leggere `is_software_codec` da `media-internals` in
parallelo a `prefer-hardware` riuscito), che è la conferma sul campo del fatto centrale di §4.1.

```
MARCA: [R]
```

---

### R16 — Il banco di S4 perde il controllo negativo, cioè quello che distingue «zero» da «non ho guardato»

```
DOVE:             web.md §6.3, riga «⛔ il controllo decisivo»
COSA CONTRADDICE: S4 §4.2, controlli P3 e P5; LEZIONI.md §1.9 regola 1
```

**Come si dimostra.** `web.md` riporta il solo **P1** (il ritardo iniettato). S4 §4.2 ne elenca sette,
e due di quelli caduti sono precisamente della famiglia che questo progetto ha già pagato:

- **P3** — *«⛔ **Il rilevatore NON trova il colore che non c'è.** Si campiona nei fotogrammi
  **prima** dell'input […] se dice sempre sì, **si sta misurando zero e si è felici a torto»***;
- **P5** — *«⚠ **Il fuori ordine.** […] che un fotogramma vecchio non venga scambiato per la
  risposta»*, il cui sintomo è **un campione negativo**.

P1 da solo non li copre: un rilevatore che dice sempre «sì» fa salire la mediana di N insieme al
ritardo iniettato, quindi **passa P1**. Il banco resta verde con il rilevatore rotto.

```
MARCA: [R]
```

---

### R17 — «La stessa misura vive nel prodotto» è dato come incondizionato, in S2 è la conseguenza di un solo esito

```
DOVE:             web.md §1.2 C e §4.3 (riquadro finale)
COSA CONTRADDICE: S2 §5, riga «C — su una fascia di telefoni è software»
```

**Come si dimostra.** In S2 l'autodiagnosi nel prodotto compare **dentro una riga condizionale**
della tabella «Che cosa decide questa risposta»: *«**C — su una fascia di telefoni è software** →
Serve un negoziato all'avvio: il client esegue una versione ridotta del banco §4…»*. Negli esiti A,
B, D, E non c'è.

`web.md` la promuove a conclusione generale (*«Quindi la diagnosi non può stare in un banco di
laboratorio: **deve stare nel prodotto**»*) e ne fa una delle tre convergenze.

⚠ **Non dico che la conclusione sia sbagliata** — è difendibile, e `DECISIONI.md` §2.7 la sostiene.
Dico che **non è dei rapporti**: è una tesi della sintesi presentata come derivata, ed è la forma
d'errore E5 applicata al ragionamento invece che al dato. Va scritta come proposta, con il suo
autore.

```
MARCA: [?]
```

---

## 2. Le omissioni che avrebbero cambiato una decisione

*⭐ Questa è la parte che nessun controllo delle citazioni trova, perché non c'è niente da
controllare: la riga non c'è. Ogni voce è nella stessa forma, in breve.*

| # | DOVE (nel rapporto) | COSA CAMBIA, e perché tacerla costa |
|---|---|---|
| **O1** | **S2 §3.8** — il congelamento delle schede | *«un browsing context group viene **congelato** se tutte le pagine sono hidden e silent da oltre **5 minuti**»*, e l'esenzione documentata è *«una `RTCPeerConnection` con `RTCDataChannel` aperto o una `MediaStreamTrack` viva»*. S2 §5 lo marca ⭐ *«decisione di architettura che va presa **adesso**, non quando ci accorgeremo che la sessione muore dopo cinque minuti»*. ⛔ **E l'architettura che `web.md` §6.1 prescrive — WebTransport e basta — non rientra nell'esenzione.** È una convergenza S2↔S4 che la sintesi non ha fatto |
| **O2** | **S2 §3.9** — AV1 | *«⭐ **Verdetto**: AV1 è chiuso da entrambi i lati. Non è un ripiego, è un vicolo cieco»*, e S2 §5 chiede che *«non va tenuto nel piano nemmeno come opzione»*. `web.md` **non nomina mai AV1**, che `LEZIONI.md` (intestazione V2) dà ancora come codec di V2 accanto a HEVC. Un vicolo cieco documentato e non trascritto è un vicolo cieco che si ripercorre (`LEZIONI.md` §8) |
| **O3** | **S4 §5.3 punto 2** — HDR | *«⚠ **HDR non si promette.** BT.2020/PQ fa cadere lo zero-copy e il percorso a una copia converte verso BT.709 con risultato slavato `[S]`. **Si codifica BT.709**»*. È una scelta di codifica lato server, cioè una riga di `SPECIFICHE.md`, e non compare |
| **O4** | **S2 §3.6** — l'abbandono dei fotogrammi | Se si butta un `delta`, *«il decodificatore **non se ne accorge e non solleva alcun errore**»* e la corruzione si propaga fino al `key` successivo; per abbandonare senza rompere servono i **sotto-livelli temporali**, `[?]` da verificare su `EncSliceLP` della UHD 730, *«altrimenti ogni abbandono costa un IDR»*. ⛔ Si scontra con `RCP.md` §2.3, che prescrive **di buttare il fotogramma** quando manca credito: la sintesi era il posto dove le due righe si incontravano |
| **O5** | **S1 §3.3** — il ripiego di Safari | Safari è l'unico motore con WebTransport **su HTTP/2 e TCP**; S1: *«il nostro server non parla WebTransport su HTTP/2, quindi il ripiego finirebbe comunque in errore. **Va deciso** se implementarlo o dichiarare Safari fuori dal ripiego»*. Una decisione dichiarata aperta, sparita |
| **O6** | **S1 §5 punto 3** — la rotazione | *«la pagina già aperta in un browser ha in mano **un'impronta che invecchia**: alla riconnessione dopo la rotazione va ricaricata la pagina o richiesta l'impronta corrente. **Va deciso dove sta questo aggiornamento in RCP**»*. `web.md` §3.2 dice solo *«ruota da sé»*, che è la metà facile |
| **O7** | **S3 §3.A.2** — i bottoni a schermo | Tre riferimenti maturi su tre danno all'utente pulsanti/tastiera a schermo per quel che il browser non lascia passare (`Ctrl+Alt+Canc`); S3: *«⭐ **è un requisito, non un ripiego di fortuna»***. `web.md` §5.2 dichiara `Ctrl+Alt+Canc` «non recuperabile» e si ferma lì |
| **O8** | **S3 §3.A.2** — lo **stato B** | Tre stati, non due: *«**B — consegnata ma riservata** […] ⛔ **il peggiore**: la sessione remota riceve la battuta **e** la scheda si chiude»*, e su Firefox `Ctrl+Tab` è lì (*«sembra intercettabile e non lo è»*). S3 §5.5 chiede per questo di **riformulare la misura S3 di `PIANO.md` §1.2**. `web.md` non nomina né gli stati né la riformulazione, e §7 riga S3a chiede ancora «la lock su DeX» come se la domanda fosse una sola |
| **O9** | **S3 §3.B.6** — iPhone | *«lo schermo intero su iPhone: supporto **parziale** in tutte le versioni da 12 a 26.5 `[S]`. ⛔ Senza schermo intero **non c'è keyboard lock**, quindi su iPhone **si perde tutto il §3.A insieme»***. `web.md` mette iPhone al primo posto del piano delle misure (§7 S1a) senza dire che su quel dispositivo la tastiera è persa comunque |
| **O10** | **S3 §3.A.1** e §3.A.7 | Due trappole d'uso: la lock **non esiste se lo schermo intero è entrato con `F11`** (*«e non se ne accorge»*), e **si spegne da sola alla perdita del fuoco** — proprio l'istante in cui i modificatori restano giù. Più la cura ⭐ che S3 propone e nessun riferimento ha (*«il server è nostro, sa lo stato vero della sessione, e può **rimandarlo indietro**»*) e il **tri-stato** `null`≠`false` |
| **O11** | **S4 §5.1 regola 7** | Il cross-origin isolation (COOP+COEP) è in S4 una **regola di prodotto** (*«la pagina si serve cross-origin isolated»*), con conseguenze su come si servono le risorse. `web.md` §6.3 lo degrada a taratura del righello del banco (*«il righello va tarato»*) |
| **O12** | **S2 §2.3** | *«la stringa minima corretta per il nostro traguardo è **livello 5.1**, non 5.0»*, e sopra 40 Mbit/s serve il tier **High** (`H153`). È il parametro che il server dovrà emettere, e non c'è |

---

## 3. ⭐ Che cosa ho riportato alla fonte e **torna**

*Perché una sintesi fedele in novanta punti si corregge in diciassette, non si riscrive.*

**Le citazioni `[R]` con file e riga: le ho cercate tutte, e le ho trovate tutte.** Non c'è una sola
citazione inventata in `web.md`. In particolare, verificate parola per parola alla fonte:

| `web.md` | Torna in |
|---|---|
| l'eccezione di Chrome la consulta **un solo punto**, e l'assenza sul percorso WebTransport è verificata **con controllo positivo** | S1 §3.1, `[✗]` con `grep` di `OnSSLCertificateError` su `url_loader.cc:1119` come controllo |
| `ERR_QUIC_CERT_ROOT_NOT_KNOWN`, e «non basta nemmeno il magazzino di sistema» | S1 §3.1, `proof_verifier_chromium.cc:428-431` |
| Firefox: l'eccezione **è** consultata su HTTP/3 e poi la sessione si chiude | S1 §3.2, `Http3Session.cpp:2303-2340` |
| `Alt-Svc` non c'entra: WebTransport apre la sua connessione da sé | S1 §3.4, `[✗]` con controllo positivo (`SETTINGS` × 50 nello stesso draft) |
| dietro l'eccezione, su Chrome, **il Service Worker non si installa** | S1 §3.9, `service_worker_loader_helpers.cc` |
| il broker **butta via del tutto** la fabbrica dei decodificatori software su desktop | S2 §3.2, `video_decoder_broker.cc:204-222` |
| su Android Chromium sceglie **di proposito** un MediaCodec software per HEVC | S2 §3.3, `media_codec_video_decoder.cc:178-215` — e il nome `c2.android.hevc` |
| il dato **esiste** (`IsPlatformDecoder()`) e non compare in nessuna interfaccia JS | S2 §3.3 e §7, con il controllo positivo dichiarato |
| Main10: Android `108.0.5343.0` · Linux VA-API `108.0.5354.0` · Safari 16.4→26.0 | S2 §2.2, riga per riga |
| copertura ≈ **85 %** in Main10, e l'autore **non distingue hardware da software** | S2 §2.2, citazione verbatim del dataset |
| la trappola dell'hvcC (emulation prevention nel PTL) | S2 §3.5, `Mp4Muxer.js:252`, `:268-282` |
| il decodificatore software **supera le prime cinque prove** e cade su tre | S2 §4.3, otto righe: cinque «sì», tre «no» |
| lista riservata di Chrome = **dodici** comandi; a schermo intero **due**; PWA **vuota** | S3 §2.4, `browser_command_controller.cc:520-527`, `:484-505`, `:465-469` |
| Firefox **sei**, Safari **zero** con filtro a schermo intero, e la spiegazione del commento di noVNC | S3 §2.4, `browser-sets.inc` e `EventHandler.cpp:4150-4168` |
| su macOS `keyboard_hook_mac.mm` **restituisce `nullptr`**, e il controllo di sistema precede la lock | S3 §2.4, con le due righe 1434 e 1455 |
| su Android/DeX **qualunque combinazione con Meta**, per regola AOSP | S3 §2.4, `PhoneWindowManager.java` righe 4010 e 4056, verbatim |
| `keyboardLock` nel Fullscreen Standard l'**8 maggio 2026**; Safari 26.4 e Firefox 151 | S3 §3.A.1, PR whatwg/fullscreen#232 |
| `clipboardchange` in **Chrome 144, 13 gennaio 2026**, motivato dai desktop remoti, porta i soli tipi MIME, vuole il fuoco | S3 §3.B.3, intent to ship verbatim |
| assente su Firefox e Safari **verificato, non dedotto**; e il menu «Incolla» con **1 s** di attesa | S3 §6.6 e §3.B.1 |
| `code` → evdev **senza buchi da 1 a 94** | S3 §3.A.3: il codice non raggiungibile più basso è **95** (`KEY_KPJPCOMMA`) |
| la risincronizzazione dei modificatori **dagli eventi del mouse** | S3 §3.A.7 punto 3, `Keyboard.js:944-953` |
| Xpra ritarda **ogni battuta di 100 ms** | S3 §3.B.4, `Client.js:18` e `:1139-1141` |
| **S3: 96 `[R]`, 103 `[S]`, 23 `[?]`, zero `[M]`** | ⭐ contati: righe con `[R]` = **96**, con `[S]` = **103**, con `[?]` = **23**. Il conto è esatto |
| il cancello di zero-copy di WebGPU è `format == PIXEL_FORMAT_NV12`, P010 non passa | S4 §3.2, `external_texture_helper.cc` verbatim |
| l'aiutante `DownShiftHighbitVideoFrame` sul canvas 2D | S4 §3.2 punto 3 |
| dipingere **nella callback `output`**, non su rAF; tutto in un worker; zero copie CPU se NV12 8 bit | S4 §1, §3.3, §3.5, §5.1 |
| l'ordine `t0` → `t1` → disegno → **poi** la lettura 16×16, e perché è vincolante | S4 §4.1, con la ragione (il `copyTo` è un readback) |
| il controllo del **ritardo iniettato N**, e la mediana che deve salire di N | S4 §4.2, P1 |
| il pezzo cieco è invisibile a JavaScript e **va dichiarato accanto a ogni numero** | S4 §4.3, chiusura |
| grana **1 ms** dei cronometri su Firefox e Safari senza le due intestazioni | S4 §3.7, `nsRFPService.cpp` e `Performance.cpp` |
| Xpra e noVNC restano sul canvas e **nessuno dei due dichiara un numero di ritardo** | S4 §3.9, tabella |

**E tornano anche i rimandi ai documenti del progetto**: `RCP.md` §4.1-bis esiste ed è
*«`serverCertificateHashes` — la strada normale»*; `RCP.md` §7.3 esiste; `RCP.md` §2.3 contiene
davvero la `[?]` sugli stream al secondo (⚠ che però **non viene da nessuno dei quattro rapporti**:
`web.md` §8 la elenca sotto *«ogni rapporto ha la sua lista»*, e questa è di `RCP.md`);
`DECISIONI.md` §2.4 è davvero *«50 ms di tetto […] solo per il pezzo che è nostro»*; §2.7 è davvero
*«il massimo lo offre il server; l'altezza la mette il client»*; §5-bis.0 è davvero DeX come uso
primario. **La citazione di `LEZIONI.md` §1.11 sul necessario/sufficiente è pertinente e ben
applicata**: `prefer-hardware` riuscito su Android è la stessa forma del render node aperto, e la
riga di `web.md` §9.1 è la più solida del documento.

⭐ **E una cosa che `web.md` fa meglio delle fonti**: dichiarare in testa che `[M]` non compare mai,
*«e non è una dimenticanza: nessuno ha ancora acceso un browser»*. È esattamente la riga che
`LEZIONI.md` §1.3 e §2.3-quater chiedono, ed è scritta prima che qualcuno possa scambiarla.

---

## 4. Che cosa ho provato a rompere senza riuscirci

*Elencato perché non venga rifatto.*

1. **Ho cercato citazioni `[R]` inventate** — file, riga o funzione che nel rapporto non ci fossero,
   o che dicessero altro. **Non ho trovato niente**: `web.md` porta **28 marche `[R]`**, le ho
   controllate una per una, e tutte esistono nella fonte con il senso che `web.md` gli dà. I difetti
   sono di *marca* e di *contorno*, mai di invenzione.
2. **Ho provato a far cadere la convergenza A (i tre indizi contro i 10 bit)** cercando se i tre
   indizi fossero lo **stesso** indizio contato tre volte. **Non ci sono riuscito**: `mediacodec` di
   Android (`DECISIONI.md` §2.3-bis), la mancanza di percorsi di readback ad alta profondità (S2) e
   il cancello NV12 di WebGPU più `DownShiftHighbitVideoFrame` (S4) sono tre catene diverse — codec,
   API, disegno — e S4 §3.2 lo dichiara esplicitamente *«e arriva da una direzione diversa»*.
   L'indizio S2 è però più debole di come è marcato (R5): la convergenza regge su due gambe e mezza,
   non su tre.
3. **Ho provato a trovare una contraddizione fra i due `[R]` della convergenza B** (Service Worker e
   PWA): sono corretti tutti e due, e la catena «niente SW ⇒ niente PWA ⇒ niente lista vuota» è
   valida. **Il difetto non è nella catena, è nella conclusione** (R6).
4. **Ho provato a smentire «l'Annex-B è la strada giusta»** cercando in S2 una ragione per l'hvcC.
   **Non ho trovato niente**: le tre ragioni di S2 §3.5 reggono, il costo su WebKit c'è ma è
   sull'altro piatto, e la trappola del PTL è documentata dal codice di chi l'ha pagata. La
   conclusione di `web.md` §4.2 è giusta; è la sua *motivazione* a essere più forte del vero (R14).
5. **Ho provato a trovare in `web.md` un `[R]` costruito su una misura di terzi** spacciata per
   lettura di codice (la forma «una misura giusta con una spiegazione inventata», `LEZIONI.md` §8).
   **Non ho trovato niente**: i numeri di terzi che S4 raccoglie — i 70/960/230 fps di
   `webcodecsfundamentals`, i 98 ms di Hopp, il «30 ms» di GeForce NOW che S4 rifiuta di citare —
   **non compaiono in `web.md` in nessuna forma**. La sintesi ha ereditato la prudenza della fonte.
6. **Ho provato a trovare una degradazione silenziosa proposta** (invariante I1) fra le conseguenze
   di prodotto di `web.md`. **Non ho trovato niente**: le due volte in cui propone un ripiego (§6.2
   la leva `<video>`, §5.1 le due API della lock) lo mette esplicitamente *«sotto un interruttore
   spento»* e *«la pagina deve saperle entrambe»*.
7. **Ho controllato i conteggi delle righe dei rapporti** dichiarati in testa a `web.md`: S1 = 920
   ✅, S3 = 1.391 ✅, S2 = **732**, non 730 ⚠ (differenza irrilevante, la segnalo solo perché il
   mandato chiede ogni cifra), S4 senza numero.
8. **Ho cercato un `[?]` dei rapporti trasformato in `[S]`** nelle date e nelle versioni (8 maggio
   2026, 13 gennaio 2026, Chrome 144, Firefox 151, Safari 26.4, Chrome 68, 108.0.5343.0,
   108.0.5354.0, 604800 s). **Tutte tornano.** L'unica cifra della mappa che non ho potuto
   verificare da nessuna fonte è *«WebTransport — **Baseline** marzo 2026»*: la parola «Baseline» è
   un termine tecnico con un significato preciso e **non compare in S1** (che dà solo Safari 26.4,
   24 marzo 2026). ⚠ Non dico che sia falsa: dico che **non l'ho potuta riportare alla fonte**.

---

## 5. Che cosa passa al coder, e in che ordine

| Che cosa | Chi chiude, e come |
|---|---|
| **R1, R15, R16** — i tre banchi | ⛔ **prima di scrivere una riga di banco.** Sono correzioni di testo nei rapporti e in `web.md`, costo zero, e senza di esse la fase 1 misura male |
| **R2** | ⛔ **prima di toccare `DECISIONI.md` §1.7 di nuovo**, perché lì c'è già una riga falsa. E rivedere l'ordine di §7: S1a non decide più l'esistenza di una piattaforma |
| **R3, R4, O1** | ⛔ **prima di scrivere la pagina**: sono i tre vincoli che decidono la sua forma, e nessuno dei tre è nella sintesi |
| **R5, R6** | correggere le marche in `web.md`, **e nei due documenti dove sono già passate** (`SPECIFICHE.md` §7.3-bis, `DECISIONI.md` §1.7) |
| **R7-R14, R17** | correzioni di testo in `web.md` |
| **R10** | ⚠ la contraddizione è **dentro S4**: la chiude chi ha scritto S4, non la sintesi |
| **O2-O12** | dodici righe da riportare nella sintesi. Sette toccano `SPECIFICHE.md` o `RCP.md` |

⛔ **E il verdetto complessivo, dichiarato come vuole `REVIEWER.md` §5:** questa non è
un'assoluzione dei punti che non ho toccato. Ho riportato alla fonte 96 affermazioni su un documento
che ne contiene di più; delle restanti **non ho trovato niente**, che non è «sono corrette».
