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

## 1. Un binario solo

*Riscritto il 9 agosto 2026: `DECISIONI.md` §1.6 toglie i client dedicati, e con essi il binario B.*

⛔ **Il piano aveva due binari perché i client erano due.** Adesso il client è **una pagina web**,
servita dal server, e le cinque fasi Android — A1-A5 — **non esistono più**: quel che portavano
dentro è diventato lavoro dentro le fasi del binario unico, ed è scritto qui sotto perché nessuno
lo perda.

```
  server + pagina web
  0 ─ 1 ─ 2 ─ 3 ─ 4 ─ 5 ─ 6 ─ 7 ─ 8 ─ 9 ─ 10 ─ 11 ─ 12 ─ 13
      │
      ├─ sonda del BROWSER  ⭐ prima di tutto, e decide la forma del resto
      └─ cliente di prova, scritto dalla SPECIFICA
```

### 1.1 ⛔ Il cliente di prova adesso vale il doppio

*Scritto il 9 agosto 2026 quando Android fu spostato in fondo, e rimasto vero quando Android è
sparito del tutto — per una ragione più forte.*

Il secondo client serviva a una cosa sola: accorgersi che **server e client condividono lo stesso
fraintendimento** (§0.4). Prima ce n'erano due e la difesa era debole; adesso **ce n'è uno solo**,
e senza un secondo lettore il protocollo sarebbe validato da **una sola** implementazione, scritta
dalla stessa mano che ha scritto il server.

| | |
|---|---|
| **il cliente di prova** | poche centinaia di righe, **in un linguaggio diverso dal server e dalla pagina**, scritto leggendo `RCP.md` e **mai** il codice. Aggiunto alla **fase 1**, cresce con le fasi |
| perché non basta il validatore | il validatore dice «questo byte non è conforme»; il cliente di prova dice **«voi due vi siete capiti su una cosa che la specifica non dice»** |
| ⭐ **e una difesa che arriva gratis** | la pagina gira su **tre motori** scritti da tre squadre che non ci conoscono. Quando due sono d'accordo e il terzo no, quel difetto **si dichiara da solo** — è il pezzo di arbitro che avevamo perso con `mstsc` (`DECISIONI.md` §1.6) |

### 1.2 ⭐ La sonda del browser — prima di tutto, perché decide la forma del resto

*Sostituisce la sonda Android, e cambia di natura: quella rispondeva a una domanda sola, questa a
quattro, e tre di esse cambiano quel che si scrive.*

⛔ **Va fatta prima di scegliere la libreria QUIC e prima di scrivere il filo**, non alla fase 2:
`DECISIONI.md` §6.4 dipende dal suo esito, perché il server deve portare HTTP/3 e WebTransport.

| # | La domanda | Che cosa decide |
|---|---|---|
| **S1** | ⛔ l'eccezione che l'utente concede sul certificato della **pagina** (TCP) **copre anche la sessione WebTransport** (UDP)? | se il predefinito «un clic» funziona ovunque, o se serve `serverCertificateHashes` — e allora **su iPhone resta solo il certificato vero** (`DECISIONI.md` §1.7) |
| **S2** | il browser del **telefono vero** decodifica **HEVC Main10 in hardware**? | `[S]` documentato da Chrome 108, mai misurato da noi. ⚠ **Non è più un muro** ma una cosa da dichiarare (`DECISIONI.md` §2.7) |
| **S3** | quante **scorciatoie** si perdono, motore per motore — e la clipboard nel verso dispositivo → sessione? | che cosa la pagina deve **dichiarare spento**, e quali browser conviene consigliare (`SPECIFICHE.md` §7.3-bis, §9) |
| **S4** | quanto costa in **ritardo** dipingere: dal fotogramma decodificato al pixel sullo schermo | è metà del tetto dei 50 ms, e dipende dalla strada scelta per la GPU |

⛔ **E si dichiara riuscita solo con la prova che sia hardware davvero.** Nel browser **il nome del
decodificatore non c'è**: la prova indiretta va costruita con cura — ritmo sostenuto, occupazione
della CPU, e il caso opposto scritto prima (`LEZIONI.md` §1.11: per ogni prova indiretta si scrive
che aspetto avrebbe il contrario, o la prova non distingue).

⛔ **Sul dispositivo vero, mai su un browser di comodo.** «Il Chrome del portatile decodifica in
hardware» non dice **niente** del Chrome del telefono: è la forma d'errore **E10** con un
travestimento nuovo (`DECISIONI.md` §5-bis.0-ter).

### 1.3 📖 E prima della pagina, uno studio: XPRA

*Aggiunto il 9 agosto 2026, ed è il **punto 0 della ricetta** di `LEZIONI.md` §9 — «chi, al mondo,
fa già questa cosa?» — applicato al client web.*

Xpra ha un client HTML5 che fa questo mestiere da anni, e l'utente lo ha usato. Si studia **come si
comporta**, non come è fatto dentro: come dipinge, la tastiera nel browser, gli appunti, il
cursore, il ridimensionamento, il ritardo. ⚠ Il **trasporto no**: Xpra è su WebSocket, noi su
WebTransport, e quel pezzo non si eredita. Confine e ragione in `DECISIONI.md` §1.6.

---

# IL SERVER E LA PAGINA

## Fase 0 — L'ambiente e i banchi

**Produce**: la macchina che compila, e i banchi di v1 rimessi in funzione.

**L'utente vede**: i numeri di v1 **riprodotti** — la cattura di Mutter che consegna ~37
fotogrammi al secondo, KWin ~60. Non è un risultato di prodotto: è il **controllo positivo di
tutto il progetto**. Se il banco non sa riprodurre un numero che sappiamo vero, ogni misura futura
è sospetta.

**Il banco**: `v1/banchi/banco-compositori/misura-cattura.c` e `banco.sh`, che rigenera da sé le
scene con `ffmpeg -f lavfi -i testsrc2`.

**Si riusa**: tutto `v1/banchi/` (262 file), `v1/banco/` per il provisioning.

⛔ **Passo zero, e senza di questo la fase non parte: GNOME non è più installato sul server**
`[M]` — `dpkg-query` dice *not-installed*, non c'è una `gnome.desktop` (`gnome.md` §2). Il
controllo positivo di tutto il progetto è la riproduzione dei ~37 fotogrammi di Mutter, e oggi
non è eseguibile. Si rimette GNOME **prima** di credere a qualunque numero.

⚠ Da fare qui e non dopo: installare `vainfo` sul ferro di prova e **confermare** le capacità del
codificatore Intel, che oggi sono `[?]` ricavate dalla generazione del chip (`DECISIONI.md` §4.6).

⚠ **E il ripristino si prova riavviando**, non rileggendo lo script: in v1 il primo riavvio vero
ha mostrato due pezzi mancanti che nessun documento dichiarava (`LEZIONI.md` §2.5-bis). Vale
adesso, non solo alla fase 13 — perché è adesso che la macchina viene rimessa in piedi.

> ## ⛔ L'ambiente Android decade — 9 agosto 2026
>
> Questa fase prevedeva SDK, emulatore (AVD), `adb` e il collegamento al telefono, per la sonda
> della fase 2. **Con `DECISIONI.md` §1.6 non serve più niente di tutto questo**: non c'è
> un'applicazione da costruire, e la sonda è **una pagina web**.
>
> ⭐ **Il telefono vero resta**, ed è più importante di prima: è lo strumento di misura di **S2** e
> **S4** (§1.2). Ma ci si arriva **aprendo un indirizzo nel browser**, che è la cosa più economica
> che questo progetto abbia mai chiesto a un dispositivo di prova.
>
> ⚠ *Il riquadro sull'emulatore che segue è tenuto per storia: la sua conclusione — «nessun numero
> si dichiara su un emulatore» — sopravvive nella forma «nessun numero si dichiara su un browser
> che non sia quello del dispositivo vero».*

> ### L'emulatore copre più di quanto sembri — ma non la decodifica
>
> *Verificato il 9 agosto 2026, dopo che una prima stesura lo aveva liquidato troppo in fretta.*
>
> ⭐ **Esiste il Desktop AVD**, profilo hardware «13.5" Freeform», da Android 11 in su; la
> versione Android 13 ha aggiunto **scorciatoie da tastiera e supporto mouse** oltre al
> ridimensionamento a trascinamento e al drag-and-drop. E **Samsung stessa documenta
> l'emulatore per DeX**: *«If you don't have the DeX Station, you can test your app resize
> behavior in Android Studio using Android Virtual Device»*, alla densità e risoluzione
> equivalenti a DeX (160 dpi, 1080×1920).
>
> Quindi **il modello di interazione è testabile lì**: finestra freeform, mouse vero, tastiera
> vera, bordi che si trascinano. È gran parte delle fasi **A1** e **A3**.
>
> ⚠ Con l'avvertenza che Samsung mette nella stessa pagina: l'emulatore **simula, non replica**
> — la modalità freeform si abilita da riga di comando ed è *«not reflective of actual DeX
> hardware behavior»*.
>
> ⛔ **Quel che l'emulatore NON dà, e va tenuto fermo:**
>
> | | |
> |---|---|
> | **la decodifica in hardware** | il suo MediaCodec non è il silicio del telefono. `[?]` Non si è riusciti a stabilire che esponga un decodificatore HEVC hardware; l'unico riscontro trovato è chi sull'emulatore **non trova profili HEVC 4K** |
> | il ritardo vero, la batteria, la rete che cambia | non attendibili |
> | la parità con DeX vero | approssimazione, non replica |
>
> > ⛔ **Da cui la regola, che resta:** *si sviluppa sull'emulatore, si misura sul telefono.*
> > **Nessun numero di questo progetto viene dichiarato su un emulatore.**
>
> ⚠ È `REVIEWER.md` **E10** — *una prova verde sul client sbagliato*. Un emulatore che dice
> «funziona» mentre il telefono no è un banco verde col difetto vivo, ed è la forma che a v1 è
> costata di più: una correzione scritta su un banco che non riproduceva il difetto, spedita
> all'utente, **che ha peggiorato le cose**.
>
> **Il telefono vero è lo strumento di misura; l'emulatore è il banco di lavoro** — e il banco di
> lavoro è più largo di quanto la prima stesura dicesse.

---

## Fase 1 — Il filo nudo

**Produce**: la stretta di mano di RCP su **WebTransport**, dai due lati. Niente video, niente
input.

**L'utente vede**: ⭐ **apre un indirizzo nel browser**, digita utente e password, e la pagina dice
*«ammesso, sessione nuova, tela 1920×1080, desktop GNOME»*. O dice perché no.

⛔ **E prima di tutto il resto, la sonda del browser** (§1.2): quattro misure che decidono la forma
di quel che si scrive dopo — a cominciare da **quale libreria QUIC**, che adesso deve portare
HTTP/3 e WebTransport (`DECISIONI.md` §6.4).

⚠ **Il server acquista qui il suo secondo mestiere**: servire la pagina. Due ascoltatori con lo
stesso numero di porta — **TCP** per il primo caricamento, **UDP** per HTTP/3 e WebTransport — e
l'annuncio `Alt-Svc` che li lega. ⛔ Dimenticarlo non dà errore: dà **una pagina che si apre e un
desktop che non arriva mai** (`RCP.md` §2.4).

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
un linguaggio diverso, **leggendo solo `RCP.md`**. Chi lo scrive non guarda il C né la pagina — se
li guardasse ne erediterebbe i fraintendimenti, e non servirebbe più a niente. Cresce di fase in
fase insieme al protocollo.

**Si riusa**: `autenticazione.c` (144 righe, PAM), `registro.c` (140).

⛔ **Ma `autenticazione.c` va cambiato in un punto, e non è un dettaglio**: rifiuta chiunque non
sia l'utente che possiede il processo (`autenticazione_utente_atteso()`, dall'uid effettivo). Era
giusto in v1, dove il server girava dentro la sessione di una persona; **contraddice il
multi-tenant** di `SPECIFICHE.md` §5.5, dove il servizio è di sistema e serve dieci utenti diversi.
Chi lo riusa senza toglierlo ottiene un server che funziona **solo per sé** — e il sintomo, per
tutti gli altri, è «credenziali errate».

---

## Fase 2 — Il primo fotogramma

**Produce**: cattura da una sessione GNOME vera → codifica → filo → **`VideoDecoder`** → tela della
pagina. Un'immagine ferma.

**L'utente vede**: ⭐ **il proprio desktop, dentro una scheda del browser**. Fermo, ma suo — e da
qualunque dispositivo, che è la cosa che alla fase 2 di v1 non c'era.

**Il banco**: il fotogramma decodificato confrontato con quello catturato. Non «il programma non è
crollato»: **i pixel**.

**Si riusa**: `cattura.c` (1060 righe), `mutter.c` (353), `superficie.c` (675), `immagine.c` (273),
`codificatore.c` (889, da riportare a HEVC), `palco.c` per la parte di montaggio.

⚠ Qui la codifica è **software**, di proposito. L'accelerazione è la fase 8, e metterla prima
significherebbe non sapere quale dei due pezzi sbaglia.

⛔ **E qui nasce la sessione GNOME, che v1 avviava senza mai averla studiata** — le trappole sono
in `gnome.md` §3 e valgono tutte al primo avvio, non dopo: `SHELL` va messa **vuota**, o
`gnome-session` si ri-esegue dentro una shell di login e si riporta dentro `~/.profile` `[R]`;
`--virtual-monitor WxH` **non è opzionale**, perché in headless la sessione parte altrimenti
**viva, completa e nera**; il drop-in dell'unità della Shell oggi si scrive **solo per KWin**
(`src/sessione.c:671`), quindi su GNOME va scritto adesso.

⭐ E una prova da fare **guasta di proposito** (M9 di `gnome.md` §13): senza `--virtual-monitor`,
per imparare che aspetto ha il guasto. Una sessione nera e perfettamente viva è la cosa che si
scambia per un difetto di cattura, e si cerca per mezza giornata dalla parte sbagliata.

⛔ **E qui la sonda del browser torna, sul serio invece che in prova** (§1.2): il primo fotogramma
vero dato a `VideoDecoder` **sul telefono**, per sapere se lo decodifica in hardware e se
restituisce davvero **10 bit**.

| | |
|---|---|
| 1 | decodifica **HEVC Main10 in hardware**? `[S]` Chrome lo documenta dalla 108; nel browser **il nome del decodificatore non c'è**, quindi la prova è indiretta e va costruita col caso opposto scritto prima (`LEZIONI.md` §1.11) |
| 2 | ⛔ **e restituisce davvero 10 bit?** `[?]` La documentazione di mpv segnala che sul percorso `mediacodec` il supporto a 10 bit è **limitato e l'uscita torna a 8 bit** — è la prima indicazione contraria al desiderato di `SPECIFICHE.md` §3.1, e arriva dal lato dove non abbiamo margine (`DECISIONI.md` §2.3-bis) |

⚠ **Che cosa cambia se la risposta fosse no**, ed è cambiato il 9 agosto: **non è più un muro**. Il
massimo lo offre il server, l'altezza la mette il client (`DECISIONI.md` §2.7): un dispositivo che
decodifica in software è un fatto da **misurare e dichiarare**, non un difetto nostro. ⛔ Ma
dichiarato **va dichiarato**: un ripiego silenzioso resta vietato anche quando la colpa è di
qualcun altro.

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

⭐ **Ma prima di dichiararlo si prova la cadenza disaccoppiata**, ed è la prima cosa da fare in
questa fase perché costa **tre celle e zero righe di prodotto**: `maxFramerate` fa da freno alla
cattura **e** da frequenza al monitor virtuale, e due orologi allo stesso numero battono fra loro
`[R]` (`LEZIONI.md` §3, il riquadro dei sei decimi; misura M3 di `gnome.md` §13). Si negozia alto
e poi si rinegozia **la sola cadenza**, a monitor fermo. Se riesce, GNOME entra nel traguardo e
questa riga va riscritta; se non riesce, il muro diventa `[M]` invece di `[?]` — che è un
guadagno comunque, perché oggi è una stima che tre documenti citano come se fosse un fatto.

---

## Fase 4 — Si comanda

**Produce**: il canale di input, il puntatore disegnato dalla pagina, le lettere e le posizioni —
⭐ **e le due disposizioni della pagina**, che è il lavoro ereditato dalle fasi A3 e A4 sciolte: il
modo classico con `Pointer Lock`, e il tocco con i sette gesti, **con il passaggio automatico sul
contesto** e non un'impostazione da cercare (`DECISIONI.md` §5-bis.0-bis).

**L'utente vede**: ⭐ **usa il desktop**. È il momento in cui smette di essere una dimostrazione.

⛔ **E qui si scopre che cosa il browser si tiene**: `Ctrl+W`, `Ctrl+T`, `F11`. La pagina **DEVE
dichiarare** quali scorciatoie non può consegnare su quel motore, invece di lasciar credere che
siano arrivate (`SPECIFICHE.md` §7.3-bis). ⚠ La misura è **S3** della sonda, e va fatta su almeno
due motori: quel che si perde su Chrome non è quel che si perde su Safari.

**Il banco**:
- ⛔ **il cursore del desktop non deve comparire nell'immagine**: si guarda un fotogramma. E su
  wlroots si verifica che il tema trasparente sia stato **caricato**, non solo scritto — un tema
  che carica zero cursori fa ripiegare su uno visibile (`SPECIFICHE.md` §7.1);
- una lettera accentata scritta in una sessione con la disposizione giusta, e una in una
  sessione con la disposizione sbagliata: la seconda **deve** finire nel registro come non
  producibile, non uscire diversa;
- `Ctrl+C` che copia invece di scrivere una c.

⛔ **E qui si scopre che il cursore non arriva affatto**, il che rende `CURSORE_FORMA` (`RCP.md`
§7.2) un canale senza sorgente: su Mutter chiediamo `cursor-mode=2` — cioè «dammi il cursore
come metadato» — **ma non chiediamo `SPA_META_Cursor`**, quindi forma, posizione e punto attivo
non vengono consegnati `[R]` (`gnome.md` §1.1 punto 6 e §5.2). Da chiedere qui, dove il canale
nasce. ⭐ **Il verso è quello giusto per noi**: pixel puliti nell'immagine *e* la forma in banda
laterale, che è esattamente ciò che serve al puntatore disegnato dal client.

⚠ **Due ricambi silenziosi di libei**, che mordono qui e alla fase 6: un cambio di **keymap**
distrugge e ricrea il dispositivo tastiera, un cambio di **geometria** tutti i dispositivi
assoluti — e il puntatore al dispositivo vecchio smette di funzionare **senza errore** `[R]`
(`gnome.md` §9). Keymap e regioni si rileggono a **ogni** `DEVICE_ADDED`, non una volta all'avvio.

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

⛔ **E due difetti che l'utente incontrerebbe lasciando la sessione ferma venti minuti**, tutt'e
due su GNOME e tutt'e due mai affrontati in v1 (`gnome.md` §4 e §7):

| | |
|---|---|
| **la revoca** | il blocca-schermo di GNOME non mostra un blocco: **ci stacca**. Ci salva `is_headless()`, che però **non abbiamo mai chiesto** — Mutter ci si mette da solo quando la sessione logind non ha un seat. Qui l'headless si **dichiara** e si **verifica dopo l'avvio**, e se non c'è si fallisce dichiarandolo (`DECISIONI.md` §4.3-bis, misura M2) |
| **la macchina si addormenta** | `sleep-inactive-ac-type` vale `suspend` a 900 s, upstream **e** Debian `[R]`. Oggi non morde solo per accidente. La cura è una chiamata sola — `SessionManager.Inhibit(…, 12)`, cioè `SUSPEND\|IDLE` **insieme** — e `energia_inibisci()` su Mutter oggi **ritorna NULL** (`src/energia.c:112-113`). ⛔ Mai il bit `LOGOUT` |

⚠ **Il banco dei tre orologi li incrocia**: sei ore di abbandono su una macchina che si sospende
a quindici minuti non si misurano affatto — e il banco resterebbe verde, perché la sessione al
risveglio c'è ancora.

**Si riusa**: `palco.c` (1545 righe — la più preziosa), `sessione.c` (797), `sentinella.c` (307,
logind), `uscita.c` (384), `energia.c` (149), `compositore.c` (229).

---

## Fase 6 — La tela e la vista

**Produce**: la tela concordata all'attacco, la vista che riscala, il riattacco a misura diversa.

**L'utente vede**: ridimensiona la finestra e l'immagine si adatta **senza che le finestre dentro
si muovano**. Poi si riattacca da una macchina con un altro schermo e ritrova la sessione adattata.

**Il banco**: il ripiego su KWin < 6.8 **dichiarato nel registro** — si verifica che la riga ci
sia, non che «funzioni lo stesso» (`SPECIFICHE.md` §6.3).

⛔ **E il riattacco rinegozia anche la disposizione di tastiera** (`SPECIFICHE.md` §7.3), che su
Mutter **distrugge e ricrea il dispositivo tastiera**; un cambio di geometria ricrea tutti i
dispositivi assoluti. Il puntatore al dispositivo vecchio smette di funzionare **senza errore**
`[R]` (`gnome.md` §9). Il banco del riattacco **deve battere un tasto e muovere il puntatore
dopo**, non solo verificare che la sessione ci sia: è la forma «una prova verde col difetto vivo»
esattamente dove si presenta.

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

⭐ **Il lato indipendente del banco degli appunti c'è già, ed è gratis**: su GNOME la sponda X11
di Mutter è incondizionata nei due versi, quindi **`xclip` funziona senza una nostra sessione**
`[R]` (`gnome.md` §10). Copiare con `xclip` e leggere col client — invece di far parlare fra loro
due pezzi nostri — è l'arbitro esterno che a questa fase serviva e che non credevamo di avere.

⛔ **Tre trappole di Mutter, che il banco non vede e il prodotto sì**: `DisableClipboard` è **a
senso unico** (dopo, gli annunci non tornano più — non si chiama mai: per lasciare la clipboard
si usa `SetSelection` senza tipi); la firma di `mime-types` è **asimmetrica** fra ingresso `as` e
uscita `(as)`, e chi legge col tipo sbagliato ottiene `NULL` **senza errore**; il gestore interno
degli appunti tiene **un solo tipo MIME**.

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

⛔ **E la copia zero si riapre dal lato giusto**: le due schermate che si alternavano non erano un
problema di *acquire* ma di **release** — `can_reuse_pw_buffer` si arrende se manca
`SPA_META_SyncTimeline` e Mutter riusa il buffer **mentre VA-API lo sta ancora leggendo** `[R]`
(`LEZIONI.md` §8, il riquadro della caccia sbagliata). Due cure candidate, entrambe piccole:
chiedere la timeline — che Mutter offre — oppure **trattenere** il `pw_buffer` fino a lettura
finita. ⚠ E **il DMA-BUF di Mutter non è un diff**: chi riprendesse la superficie di accumulo
rifarebbe la cura che peggiorava le cose.

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

⭐ **E qui il client web si ripaga la seconda volta**: la pagina sta **dentro lo stesso pacchetto**
del server. Niente APK, niente store, nessuna versione del client da inseguire — ⛔ e nessun caso
«client vecchio contro server nuovo», che è precisamente quello che `RCP.md` §9 dice di temere.
Il client si aggiorna **ricaricando**.

⚠ **Con un caso che resta e va provato**: la **scheda già aperta** mentre il server viene
aggiornato. Lì il client vecchio contro il server nuovo esiste davvero, per il tempo di un
ricaricamento — ed è il solo posto dove la negoziazione di versione serve a qualcosa.

**Il banco**: ⛔ **il ripristino si prova riavviando**, non rileggendo lo script. In v1 il primo
riavvio vero ha mostrato che mancavano due pezzi, e nessuno dei due era nei documenti: il disco che
non si montava da solo, e i pacchetti installati a mano mesi prima che il provisioning ereditava
senza dichiararli (`LEZIONI.md` §2.5-bis).

---

# ⛔ BINARIO B — sciolto il 9 agosto 2026

*Erano cinque fasi — A1-A5, il client Android in Kotlin. `DECISIONI.md` §1.6 le ha cancellate: il
client è una pagina web, e non c'è più un secondo prodotto da costruire.*

⛔ **Ma niente di quel che quelle fasi dovevano fare è sparito insieme a loro.** Questa tabella
esiste perché nessuno lo perda, ed è l'unico posto in cui è scritto dove è finito ciascun pezzo:

| Fase sciolta | Dove è finito il suo lavoro |
|---|---|
| **A1** — il filo su Android | **fase 1**: la pagina *è* il client, e la stretta di mano si scrive una volta sola. Il mestiere di secondo lettore passa al **cliente di prova** (§1.1) |
| **A2** — il video, MediaCodec | **fase 2**, con `VideoDecoder` al posto di MediaCodec — e la domanda *«il telefono ce la fa?»* la risolve la sonda (§1.2, misura **S2**) |
| **A3** — mouse e tastiera, il modo classico | **fase 4**, che diventa la fase dove si scrive **l'interfaccia classica della pagina**: `Pointer Lock` al posto di *Pointer Capture*, e le scorciatoie con il loro limite dichiarato (`SPECIFICHE.md` §7.3-bis) |
| **A4** — il tocco e la tastiera a schermo | **fase 4** anch'essa, come **seconda disposizione della stessa pagina**: i sette gesti restano quelli, e il passaggio fra le due resta **automatico sul contesto** (`DECISIONI.md` §5-bis.0-bis) |
| **A5** — la vita dell'applicazione | ⚠ **si sparpaglia, e una parte va sorvegliata**: la migrazione QUIC da WiFi a rete mobile è **fase 9** (è la ragione migliore per cui QUIC è stato scelto); il riattacco è **fase 5**. ⛔ **Quel che cambia natura è lo sfondo**: una scheda del browser che finisce dietro viene rallentata o congelata dal sistema, e non è più un ciclo di vita che governiamo noi — è una cosa da **misurare e dichiarare** |

⭐ **E DeX non sparisce come caso di prova** (`DECISIONI.md` §5-bis.0): resta il posto in cui il
ridimensionamento della finestra viene esercitato sul serio, perché la finestra si trascina. Cambia
che a trascinarla è il browser.

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

⛔ ~~**Android dopo la 9**~~ → **Android non c'è più** *(9 agosto 2026)*. La ragione che lo
spostava in fondo — *«le prove su Android costano dieci volte quelle su Linux»* — è stata risolta
alla radice invece che riorganizzata: **non esiste più un secondo prodotto da provare**. Il
mestiere di secondo lettore resta al **cliente di prova** della fase 1, che è più economico e ha la
proprietà che conta: **è scritto dalla specifica, non dal codice**.

⭐ **E una cosa arriva prima di tutto il resto, che prima non c'era**: la **sonda del browser**
(§1.2). Non perché sia urgente in sé, ma perché **decide che cosa si scrive**: la libreria QUIC
dipende da WebTransport, il predefinito del certificato dipende da una misura, e quel che la pagina
deve dichiarare spento dipende dal motore. Una fase che comincia prima di quelle risposte scrive
codice che poi si butta.

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
