# PIANO — le fasi, in ordine, e come si chiudono

*Aperto il 9 agosto 2026, dopo `SPECIFICHE.md` e `RCP.md` e prima di qualunque riga di codice.*

---

## 0. Come è fatto questo piano

**Una fase è una cosa sola che si può mostrare.** Se a fine fase non c'è niente che l'utente possa
guardare e giudicare, la fase è divisa male.

Ogni fase ha quattro cose, e la terza è quella che di solito si dimentica:

| | |
|---|---|
| **che cosa produce** | in una riga |
| **che cosa vede l'utente** | e giudica — è il criterio di chiusura, non il documento |
| **il banco** | ⛔ **scritto prima di sviluppare**, non dopo |
| **il documento** | `fasi/NN-nome.md`, **aperto quando si apre la fase** |

### 0.1 La regola che tiene in piedi il resto

> ⛔ **Il documento di fase si apre all'inizio e si riempie strada facendo. Non si scrive alla
> fine.**

Un documento scritto dopo è un **resoconto**, e in un resoconto le misure si *ricordano* invece di
essere *registrate*. È `LEZIONI.md` §9.8: si aggiorna nello stesso momento, con la data e la
fonte.

⭐ E ha un effetto collaterale che vale da solo: **se non sai scrivere il banco all'inizio, non hai
ancora capito la fase.** Una fase che non sa dire come si misurerà non è pronta ad aprirsi.

### 0.2 Il modello del documento di fase

```markdown
# Fase N — <titolo>
Aperta il <data> · Chiusa il <data>

## Che cosa deve produrre
Una riga. E: che cosa l'utente vede e giudica alla fine.

## Il banco                      ← scritto PRIMA di sviluppare
Come si misura, con quale scena, quale numero ci aspettiamo.
E il controllo positivo: come so che questo banco sa vedere il difetto?

## Che cosa è stato sviluppato
File, righe, a cosa servono.

## Le misure                     ← riempito strada facendo
| che cosa | atteso | misurato | data |
La scena dichiarata accanto a ogni numero.

## ⛔ Che cosa NON ha funzionato
I vicoli ciechi, con il motivo. Anche quelli imbarazzanti.

## Le decisioni prodotte
Collegamenti a DECISIONI.md §x.y — **non copie**.

## Che cosa resta [?]
Quel che la fase lascia aperto, dichiarato invece che dimenticato.

## Il giudizio dell'utente
La frase vera, con la data.
```

### 0.3 Le quattro regole del piano

1. ⛔ **Le decisioni stanno in `DECISIONI.md`, una sola volta.** Il documento di fase **rimanda**,
   non copia. Undici registri delle decisioni sono undici posti dove cercare, e prima o poi due si
   contraddicono.
2. ⛔ **«Che cosa non ha funzionato» si riempie anche quando fa una brutta figura.** Il capitolo
   più utile di v1 — i sette vicoli ciechi di `LEZIONI.md` §8 — esiste solo perché i fallimenti
   erano stati scritti. Un vicolo cieco documentato costa meno di uno riscoperto.
3. ⛔ **Una fase si chiude su una misura giudicata dall'utente**, non su un documento completo. È
   l'invariante I8.
4. ⛔ **Il banco si certifica prima di essere creduto.** Ogni fase, prima di dichiarare un numero,
   dimostra che il suo banco sa vedere il difetto che cerca (`LEZIONI.md` §1.2 e §1.9).

### 0.4 Il metodo: sviluppo agentico e revisione avversariale

Il lavoro è fatto da due tipi di agenti, con le regole nei loro documenti — [`CODER.md`](CODER.md)
e [`REVIEWER.md`](REVIEWER.md). Qui sta **quando** intervengono dentro una fase, che è la parte che
quei documenti non dicono.

#### Il revisore è uno dei tre sostituti dell'arbitro che abbiamo perso

⭐ È la ragione per cui la revisione qui pesa più che in un progetto normale. In v1 l'arbitro era
**mstsc**: quando sbagliavamo a capire la specifica, un client altrui protestava — gratis, subito,
senza che nessuno dovesse accorgersene. Buttando RDP quel segnale è sparito, e **due programmi
scritti dalla stessa mano che vanno d'accordo non confermano niente**.

Le tre cose che lo sostituiscono, e nessuna basta da sola:

| | |
|---|---|
| **`RCP.md`** | l'arbitro **scritto**: dice chi ha torto, ma solo se qualcuno lo consulta |
| **il validatore del filo** | l'arbitro **meccanico**: vede i byte non conformi, ma solo quelli |
| **la revisione avversariale** | l'arbitro **che ragiona**: è l'unico che può accorgersi che server e client condividono lo **stesso** fraintendimento |

#### I tre momenti in cui il revisore interviene

⛔ **Non uno solo, e il primo non è sul prodotto.**

| Quando | Su che cosa | Perché lì |
|---|---|---|
| **1. appena il banco esiste**, prima di scrivere il prodotto | il **banco** | `REVIEWER.md` §1: *il banco è il primo imputato*. Un difetto nel prodotto lo trova un banco buono; un difetto nel banco non lo trova niente, e avvelena ogni misura successiva **perché dà fiducia** |
| **2. quando il codice c'è**, prima di misurarlo | il **prodotto** | misurare codice che contraddice già una regola scritta è tempo speso per sapere una cosa che si sapeva |
| **3. prima della chiusura** | il **documento di fase** | che ogni numero abbia la sua scena dichiarata, che i fallimenti ci siano, che le `[?]` non siano state promosse a fatti in silenzio |

#### La postura avversariale, in concreto

Non è un tono: sono quattro pratiche.

1. ⛔ **Il revisore riceve il codice e la specifica, non il ragionamento di chi l'ha scritto.** Una
   spiegazione del perché è giusto **àncora** chi legge, e trasforma la ricerca di contraddizioni
   in una verifica di coerenza con la spiegazione.
2. ⛔ **Si prova a rompere, non a confermare.** Per ogni invariante che la modifica tocca, il
   revisore costruisce **l'ingresso concreto** che lo violerebbe. Se non riesce a costruirlo, lo
   dichiara — è informazione anche quella.
3. ⛔ **Un rilievo si chiude con una misura, non con una discussione.** `[R]` si corregge; `[?]` si
   **misura**, e la misura è del coder, sul ferro. Il revisore non misura e non riscrive.
4. ⛔ **Una revisione verde non è un'approvazione.** È «non ho trovato niente», e va dichiarata con
   quelle parole. Il verdetto ha sempre la forma *«questo contraddice X»*, mai *«questo è giusto»*.

⚠ **E la separazione dei mestieri va difesa in tutt'e due i versi**: il coder non chiede al revisore
di misurare al suo posto, e non riscrive il codice su un `[?]` senza prima misurarlo.

---

## 1. I due binari

Il server si scrive avendo in mente **tutti e due** i client. Ma il **client Linux viene prima**,
e non per gerarchia: **per il costo delle prove**. Ogni giro su Android costa compilazione,
installazione, un dispositivo o un emulatore, strumentazione più difficile e automazione peggiore.
Farlo in parallelo a un server che si muove ancora moltiplica quel costo per ogni giro.

```
  binario A — server + client Linux
  0 ─ 1 ─ 2 ─ 3 ─ 4 ─ 5 ─ 6 ─ 7 ─ 8 ─ 9 ─ 10 ─ 11 ─ 12 ─ 13
      │       ·                      │
      │       · sonda Android        └──▶ binario B — client Android
      │       ·  (50 righe)                A1 ─ A2 ─ A3 ─ A4 ─ A5
      │                                    ↑ in parallelo a 10-11, che non toccano il filo
      └─ cliente di prova, scritto dalla SPECIFICA
```

### 1.1 ⛔ Che cosa costa spostare Android in fondo, e come si compensa

*Deciso il 9 agosto 2026, dopo che il piano lo innestava alla fase 4.*

Nella prima stesura Android stava alla fase 4 **non** per fare prima: era il **secondo lettore del
protocollo**, l'unica cosa capace di accorgersi che server e client condividono lo *stesso*
fraintendimento (§0.4). Spostandolo in fondo, tutto ciò che si costruisce fra la 4 e la 12
poggerebbe su un protocollo validato da **una sola** implementazione — e un difetto di disegno
scoperto alla fase 12 presenterebbe il conto tutto insieme.

⭐ **Ma quel mestiere non deve farlo Android.** Lo può fare un lettore molto più economico, purché
abbia la proprietà che conta: **essere scritto dalla specifica, non dal codice**.

| | |
|---|---|
| **il cliente di prova** | poche centinaia di righe, **in un linguaggio diverso dal server**, scritto leggendo `RCP.md` e **mai** il C. Aggiunto alla **fase 1**, cresce con le fasi |
| perché non basta il validatore | il validatore dice «questo byte non è conforme»; il cliente di prova dice **«voi due vi siete capiti su una cosa che la specifica non dice»** |

⚠ **Il rischio residuo, dichiarato e accettato**: restano cose che solo Android può rivelare e che
nessun lettore sostituisce — il comportamento di MediaCodec, il tocco vero sotto le dita, l'IME, la
batteria, la rete che cambia in tasca. Quelle arrivano tardi, e va bene così **tranne una**.

### 1.2 La sonda Android, presto e a poco prezzo

L'unica incognita di Android che **non** può aspettare è quella che ha ucciso v1: **che il telefono
decodifichi in hardware quel che produciamo**.

Non serve un client per saperlo. Servono ~50 righe che diano un file **HEVC Main10** a MediaCodec e
dicano se è stato decodificato **in hardware** e a che ritmo. Va nella **fase 2**, appena il primo
fotogramma esiste.

⛔ **E si dichiara riuscita solo con la prova che sia hardware davvero**, non perché il file si è
aperto: «ha istanziato un decoder ⇒ è in hardware» è la forma d'errore E1, una condizione
necessaria presa per sufficiente. Si guarda il **nome** del decoder scelto (`c2.` contro `OMX.`
software) **e** il ritmo, e i due devono concordare.

Se la risposta fosse **no**, è molto meglio saperlo con due fasi costruite che con nove.

---

# BINARIO A — il server e il client Linux

## Fase 0 — L'ambiente e i banchi

**Produce**: la macchina che compila, e i banchi di v1 rimessi in funzione.

**L'utente vede**: i numeri di v1 **riprodotti** — la cattura di Mutter che consegna ~37
fotogrammi al secondo, KWin ~60. Non è un risultato di prodotto: è il **controllo positivo di
tutto il progetto**. Se il banco non sa riprodurre un numero che sappiamo vero, ogni misura futura
è sospetta.

**Il banco**: `v1/banchi/banco-compositori/misura-cattura.c` e `banco.sh`, che rigenera da sé le
scene con `ffmpeg -f lavfi -i testsrc2`.

**Si riusa**: tutto `v1/banchi/` (262 file), `v1/banco/` per il provisioning.

⚠ Da fare qui e non dopo: installare `vainfo` sul ferro di prova e **confermare** le capacità del
codificatore Intel, che oggi sono `[?]` ricavate dalla generazione del chip (`DECISIONI.md` §4.6).

**E qui entra anche l'ambiente Android**, benché il binario B cominci molto dopo: SDK, emulatore
(AVD), `adb`, e il collegamento al telefono vero sulla rete locale. Si mette adesso perché la
**sonda della fase 2** lo richiede già.

> ### ⛔ Sull'emulatore si sviluppa. Non si misura.
>
> **Nessun numero di questo progetto viene dichiarato su un emulatore.**
>
> L'emulatore è ottimo per il ciclo di sviluppo — interfaccia, logica dei gesti, IME, la stretta
> di mano — ed è veloce, scriptabile e automatizzabile. Ma **non può misurare le due cose che
> decidono il binario Android**:
>
> | | |
> |---|---|
> | **la decodifica in hardware** | il MediaCodec dell'emulatore non è il silicio del telefono |
> | **DeX** | non esiste sull'emulatore. Si può avvicinare con schermo grande, mouse e tastiera dell'ospite, ma quello è il *modello di interazione*, non DeX: il gestore di finestre e le regole d'input sono suoi |
>
> E non attendibili nemmeno: il ritardo vero, la batteria, la rete che cambia.
>
> ⚠ È `REVIEWER.md` **E10** — *una prova verde sul client sbagliato*. Un emulatore che dice
> «funziona» mentre il telefono no è un banco verde col difetto vivo, ed è la forma che a v1 è
> costata di più: una correzione scritta su un banco che non riproduceva il difetto, spedita
> all'utente, **che ha peggiorato le cose**.
>
> **Il telefono vero è lo strumento di misura; l'emulatore è il banco di lavoro.** Due mestieri, e
> il primo non si delega al secondo.

---

## Fase 1 — Il filo nudo

**Produce**: la stretta di mano di RCP su QUIC, dai due lati. Niente video, niente input.

**L'utente vede**: si collega da riga di comando, e il programma dice *«ammesso, sessione nuova,
tela 1920×1080, desktop GNOME»*. O dice perché no.

**Il banco**:
- ⛔ **la stretta di mano su DUE connessioni, mai una**: in v1 un certificato condiviso uccideva il
  server **alla seconda**, e una prova a connessione singola resta verde per sempre
  (`LEZIONI.md` §2.1);
- il **validatore del filo** nella sua prima forma: legge una registrazione e dice quale byte non è
  conforme a `RCP.md` §6;
- ⛔ **e le prove di violazione**: tipo sconosciuto, lunghezza sbagliata, messaggio nello stato
  sbagliato. La connessione **deve cadere ogni volta**. Un banco che non prova a violare il
  protocollo non prova il protocollo (`RCP.md` §11).

**Controllo positivo del validatore**: gli si dà una registrazione **con un errore dentro** e si
verifica che lo veda. Uno strumento che non ha mai trovato niente non è pulito: è non certificato.

⭐ **E qui nasce il cliente di prova** (§1.1): la stretta di mano scritta **una seconda volta**, in
un linguaggio diverso, **leggendo solo `RCP.md`**. Chi lo scrive non guarda il C — se lo guardasse
ne erediterebbe i fraintendimenti, e non servirebbe più a niente. Cresce di fase in fase insieme al
protocollo.

**Si riusa**: `autenticazione.c` (144 righe, PAM), `registro.c` (140).

---

## Fase 2 — Il primo fotogramma

**Produce**: cattura da una sessione GNOME vera → codifica → filo → decodifica → finestra.
Un'immagine ferma.

**L'utente vede**: ⭐ **il proprio desktop**, dentro una finestra, sull'altro computer. Fermo, ma
suo.

**Il banco**: il fotogramma decodificato confrontato con quello catturato. Non «il programma non è
crollato»: **i pixel**.

**Si riusa**: `cattura.c` (1060 righe), `mutter.c` (353), `superficie.c` (675), `immagine.c` (273),
`codificatore.c` (889, da riportare a HEVC), `palco.c` per la parte di montaggio.

⚠ Qui la codifica è **software**, di proposito. L'accelerazione è la fase 8, e metterla prima
significherebbe non sapere quale dei due pezzi sbaglia.

⛔ **E qui va la sonda Android** (§1.2), che è la sola cosa del binario B che non può aspettare: un
file HEVC Main10 dato a MediaCodec, per sapere **adesso** se il telefono lo decodifica in hardware.
È il muro contro cui è morto v1, e scoprirlo qui costa due fasi invece di nove.

⛔ **La sonda gira sul telefono vero, mai sull'emulatore** (fase 0): è precisamente la misura che
un emulatore non sa dare, perché il suo MediaCodec non è il silicio del telefono.

---

## Fase 3 — Il movimento

**Produce**: uno stream per fotogramma, l'abbandono con `RESET_STREAM`, la cadenza.

**L'utente vede**: il desktop **che si muove**, e dice se è fluido.

**Il banco**, ed è il cuore:
- ⛔ **la scena si dichiara e si muove sempre** — un client a schermo intero che ridisegna a ogni
  richiamo del compositore. Tutte le misure di ritmo delle fasi 3-9 di v1 sono state buttate per
  questo (`LEZIONI.md` §1.1);
- **i fotogrammi consegnati all'utente**, non quelli elaborati. Il numero che in v1 nessuno aveva
  mai contato, e che era 18 mentre si ottimizzava altro;
- ⭐ **l'anello del ritardo**: il client manda un input che cambia colore allo schermo e guarda i
  fotogrammi decodificati finché non lo vede. Misurato **dal lato che riceve**
  (`DECISIONI.md` §2.6).

**I numeri da raggiungere**: ritardo ≤ 50 ms, traguardo 40 (`SPECIFICHE.md` §3.2).

⚠ **Attesa dichiarata in anticipo**: su GNOME il traguardo dei 40 ms probabilmente **non si
raggiunge**, per il muro dei 37 fotogrammi di Mutter. Se la misura lo confermasse, non è un difetto
nostro — ed è una ragione in più per la fase 10.

---

## Fase 4 — Si comanda

**Produce**: il canale di input, il puntatore disegnato dal client, le lettere e le posizioni.

**L'utente vede**: ⭐ **usa il desktop**. È il momento in cui smette di essere una dimostrazione.

**Il banco**:
- ⛔ **il cursore del desktop non deve comparire nell'immagine**: si guarda un fotogramma. E su
  wlroots si verifica che il tema trasparente sia stato **caricato**, non solo scritto — un tema
  che carica zero cursori fa ripiegare su uno visibile (`SPECIFICHE.md` §7.1);
- una lettera accentata scritta in una sessione con la disposizione giusta, e una in una
  sessione con la disposizione sbagliata: la seconda **deve** finire nel registro come non
  producibile, non uscire diversa;
- `Ctrl+C` che copia invece di scrivere una c.

**Si riusa**: `input.c` (906 righe, libei), `tastiera.c` (372, xkbcommon).

---

## Fase 5 — La sessione

**Produce**: PAM per intero, il palco che sopravvive al distacco, i tre orologi, una sola sessione
grafica per utente.

**L'utente vede**: chiude il client, va a pranzo, riapre — **e ritrova tutto com'era**.

**Il banco**:
- distacco e riaggancio, **due volte di fila**: un banco che passa solo da macchina pulita non è un
  banco, è una dimostrazione (`LEZIONI.md` §2.3-ter);
- ⛔ **la sessione senza nessuno che guarda**: in v1 il monitor virtuale spariva al distacco e
  `libmutter` andava in asserzione fallita, con le applicazioni che perdevano la connessione
  Wayland. È il difetto che rende la sessione inutilizzabile dopo il primo stacco;
- i tre orologi, ciascuno con la sua prova;
- l'apertura di una sessione locale mentre la remota è viva → la remota **deve** cadere con
  `SESSIONE_LOCALE_PREVALSA`, e il motivo si verifica **dal lato che lo riceve**.

**Si riusa**: `palco.c` (1545 righe — la più preziosa), `sessione.c` (797), `sentinella.c` (307,
logind), `uscita.c` (384), `energia.c` (149), `compositore.c` (229).

---

## Fase 6 — La tela e la vista

**Produce**: la tela concordata all'attacco, la vista che riscala, il riattacco a misura diversa.

**L'utente vede**: ridimensiona la finestra e l'immagine si adatta **senza che le finestre dentro
si muovano**. Poi si riattacca da una macchina con un altro schermo e ritrova la sessione adattata.

**Il banco**: il ripiego su KWin < 6.8 **dichiarato nel registro** — si verifica che la riga ci
sia, non che «funzioni lo stesso» (`SPECIFICHE.md` §6.3).

---

## Fase 7 — Audio e appunti

**Produce**: Opus e PCM in uscita; appunti testuali nei due versi.

**L'utente sente e vede**: la musica, e il copia-incolla che funziona in tutt'e due i versi.

**Il banco**:
- ⛔ **si ascolta**, non si contano i blocchi: in v1 il banco contava i campioni mentre l'audio era
  **rumore a fondo scala**, e restava verde;
- ⛔ **i due lati si sincronizzano con marcatori, non con `sleep`**: al banco degli appunti di KDE i
  due lati erano sfasati di **tredici secondi** e il controllo dava rosso su codice che funzionava
  (`LEZIONI.md` §2.3-quinquies);
- ⚠ e la clipboard si **svuota all'inizio** di ogni giro: quel che resta dal giro prima viene
  annunciato alla connessione e sembra un risultato.

**Si riusa**: `altoparlante.c` (892), `suono.c` (582), `appunti_mutter.c` (450), `appunti.c` (115).

⚠ Invariante I5: il volume appartiene alla sessione, e chi si collega lo trova **al massimo**.

---

## Fase 8 — L'accelerazione

**Produce**: HEVC in hardware su Intel, 10 bit, e la copia zero.

**L'utente vede**: **la stessa immagine di prima**, e giudica che non sia peggiorata.

**Il banco**, ed è la lezione che è costata di più:
- ⛔ **si misurano i fotogrammi consegnati, non i millisecondi di CPU.** La fase 9 di v1 ha portato
  il costo per fotogramma da 41 ms a 6 mentre i fotogrammi consegnati **scendevano** da 29 a 22,7.
  Un guadagno che si paga in fluidità non è un guadagno (`LEZIONI.md` §6.2);
- ⛔ **chiedere il codificatore per nome e verificare che abbia obbedito**: un codificatore che
  ripiega in CPU credendosi in GPU produce due misure sotto la stessa etichetta. Se non obbedisce,
  si dichiara il fallimento (`LEZIONI.md` §1.8);
- ⚠ e la prova «ha aperto un render node ⇒ rende in GPU» **non prova niente** (§1.11).

⚠ Qui vive la trappola della GPU: con due schede, il compositore che disegna su quella sbagliata dà
composizione in software **senza un errore**. La regola udev di `v1/banco/gpu-udev.sh` va applicata
e verificata (`DECISIONI.md` §4.6-ter).

---

## Fase 9 — La qualità e la degradazione

**Produce**: il controllo del ritmo, la scala di degradazione, il comportamento su rete cattiva.

**L'utente vede e giudica**: l'immagine. ⛔ **Ed è l'unico giudizio che conta**: in v1 questa fase
era stata validata con PSNR, SSIM e l'occhio dello sviluppatore, e il giudizio dell'utente sul
desktop vero fu *«siamo tornati indietro»*. La fase fu azzerata.

**Il banco**: la rete strozzata a valori veri — 2 Mbit/s con perdita e giro lungo — e la verifica
che il ritmo cali **senza mai bloccarsi** e senza mai staccare.

⛔ **La cosa che si verifica per prima**: che il ritmo **non** cali quando la scena è ferma. È
l'invariante I1, ed è la ferita da cui nasce.

⚠ E ciò che cambia quel che si vede sta **dietro un interruttore spento** finché l'utente non l'ha
guardato (I6).

---

## Fase 10 — KDE

**Produce**: il secondo desktop.

**L'utente vede**: la stessa cosa su Plasma.

⭐ **E qui si insegue il numero desiderato**: KWin consegna 60 fotogrammi al secondo dove Mutter ne
dà 37 `[M]`. La fase 10 non è solo «servire più desktop»: è la strada per i 60 a 4K e per il
traguardo dei 40 ms.

**Si riusa**: `kwin.c` (822 righe), `appunti_wlr.c` (796).

⚠ Le trappole sono già scritte in `kde.md`: `XDG_MENU_PREFIX` senza cui il cancello della cattura
non si apre; niente `InaccessiblePaths=` nel drop-in; il ridimensionamento **nella forma della
negoziazione**, con la guardia contro il ciclo infinito che **non si vede su Trixie** e compare il
giorno dell'aggiornamento a 6.8.

---

## Fase 11 — XFCE e LXQt

**Produce**: il terzo e il quarto desktop, che condividono wlroots e quindi quasi tutto.

**Si riusa**: `appunti_wlr.c` già scritto per questa famiglia; le risposte alle quattordici domande
sono già in `xfce.md` §12 e `lxqt.md`.

---

## Fase 12 — Multi-tenant e il budget

**Produce**: più utenti insieme, il budget del codificatore, il rifiuto motivato.

**L'utente vede**: due sessioni vere in contemporanea; e quando la macchina è piena, un messaggio
che **dice perché**.

**Il banco**: si satura il codificatore di proposito e si verifica che l'undicesimo riceva
`BUDGET_PIENO` — e che **i dieci che stavano lavorando non peggiorino** (`DECISIONI.md` §4.6-bis).

---

## Fase 13 — Il servizio

**Produce**: unità systemd, confezionamento, installazione, il certificato generato all'avvio,
la limitazione dei tentativi.

**Il banco**: ⛔ **il ripristino si prova riavviando**, non rileggendo lo script. In v1 il primo
riavvio vero ha mostrato che mancavano due pezzi, e nessuno dei due era nei documenti: il disco che
non si montava da solo, e i pacchetti installati a mano mesi prima che il provisioning ereditava
senza dichiararli (`LEZIONI.md` §2.5-bis).

---

# BINARIO B — il client Android

> ⭐ **Il bersaglio primario di questo binario è Samsung DeX**, non il telefono in mano
> (`DECISIONI.md` §5-bis.0). Il che lo rende **più vicino al client Linux** di quanto sembri:
> stesso modello di interazione — puntatore, tastiera, finestra ridimensionabile — e diverso solo
> nello stack di decodifica. Il telefono in mano è il caso **secondo**, e il suo posto è la fase A4.
>
> ⚠ DeX vale come **caso di prova a sé, non come variante del telefono**: è dove il
> ridimensionamento della finestra viene esercitato sul serio, perché la finestra si trascina.
>
> ⭐ **Una applicazione, due interfacce.** Il passaggio fra il modo classico (A3) e il tocco (A4) è
> **automatico sul contesto** — schermo esterno e mouse collegati, oppure telefono in mano — non
> un'impostazione da cercare. È l'unica cosa che si prende da RDM come disegno
> (`DECISIONI.md` §5-bis.0-bis); il resto è ispirazione, non un prodotto da rifare.

*Si innesta **dopo la fase 9**, quando l'esperienza su Linux è completa e giudicata, e il
protocollo è stato esercitato dalla stretta di mano fino alla rete cattiva. Può procedere **in
parallelo alle fasi 10-11**, che sono lavoro di server e non toccano il filo.*

*Kotlin, e MediaCodec per la decodifica. La domanda che di solito apre questo binario — «il
telefono ce la fa?» — a questo punto ha già risposta, perché l'ha data la sonda della fase 2.*

## Fase A1 — Il filo su Android
La stretta di mano e l'attacco. L'utente vede: *«ammesso, sessione ripresa»* sul telefono.
⭐ **Ed è qui che il protocollo viene messo alla prova per davvero**: la seconda implementazione è
l'unica cosa che somiglia a un arbitro esterno, anche se scritta dalla stessa mano.

## Fase A2 — Il video
MediaCodec, HEVC, 10 bit. L'utente vede il proprio desktop sul telefono.
⚠ È il muro contro cui è morto v1 — lì il client decodificava in software. Il banco misura
**i fotogrammi decodificati in hardware**, e la prova che lo siano davvero.

## Fase A3 — Mouse e tastiera: il modo classico
⭐ **È la strada principale, non un accessorio** (`DECISIONI.md` §5-bis.0): l'uso primario di
Android è **Samsung DeX**, dove il telefono pilota uno schermo esterno con mouse e tastiera veri.
Il puntatore disegnato dal client mosso da *Pointer Capture*, le scorciatoie di comando, la
finestra che si trascina.

**L'utente vede**: lavora come su un desktop, e giudica se il puntatore «segue la mano».

## Fase A4 — Il tocco, e la tastiera a schermo
Il ripiego per il telefono in mano: i sette gesti (`SPECIFICHE.md` §7.2) e l'IME che produce testo.
⚠ La tabella dei gesti è **un punto di partenza dichiarato**: qui si scopre quali sono giusti, e si
cambia.

## Fase A5 — La vita dell'applicazione
Lo sfondo, la rete che cambia — ⭐ **la migrazione QUIC da WiFi a rete mobile senza distacco**, che
è la ragione migliore per cui QUIC è stato scelto — il riattacco, la batteria.

---

## L'ordine, e perché

**Il filo prima del contenuto** (1 prima di 2): un canale che non si sa aprire non si sa nemmeno
riempire, e i difetti di protocollo trovati con dentro il video sono tre volte più cari.

**Il software prima dell'hardware** (2-3 prima di 8): con la codifica accelerata dall'inizio, un
difetto d'immagine ha due sospetti invece di uno.

**La sessione dopo il movimento** (5 dopo 3): la persistenza è la cosa più difficile del progetto,
e affrontarla prima di avere qualcosa da guardare significa non sapere se il palco regge.

**Un desktop solo fino alla 9**: gli altri tre si aprono quando la catena è chiusa, altrimenti si
inseguono differenze di compositore e difetti nostri nello stesso momento.

**Android dopo la 9**, e non dopo la 4 come diceva la prima stesura: **le prove su Android costano
dieci volte quelle su Linux**, e farle contro un server che si muove ancora moltiplica il costo per
ogni giro. Il mestiere di secondo lettore che Android doveva fare passa al **cliente di prova**
della fase 1 — più economico, e con la stessa proprietà che conta: **è scritto dalla specifica, non
dal codice**. Resta presto solo la **sonda** della fase 2, perché la decodifica in hardware sul
telefono è l'unica incognita che non si può rimandare.

---

## Il metodo, in sei righe

1. Il documento di fase si apre **prima** di sviluppare, e contiene il banco.
2. Il banco si certifica **prima** di essere creduto — e **si fa revisionare per primo**, prima
   del prodotto.
3. Si prova a **rompere**, non a confermare. Una revisione verde è «non ho trovato niente».
4. Quel che non ha funzionato si scrive **anche** quando fa una brutta figura.
5. Un rilievo si chiude con **una misura**, non con una discussione.
6. La fase si chiude quando **l'utente ha guardato e ha detto la sua** — non quando il documento è
   pieno.
