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
| **il documento** | `fasi/NN-nome.md`, **aperto quando si apre la fase** — e alla chiusura diventa un capitolo di [`FASI.md`](FASI.md) |

### 0.1 La regola che tiene in piedi il resto

> ⛔ **Il documento di fase si apre all'inizio e si riempie strada facendo. Non si scrive alla
> fine.**

Un documento scritto dopo è un **resoconto**, e in un resoconto le misure si *ricordano* invece di
essere *registrate*. È `LEZIONI.md` §9.8: si aggiorna nello stesso momento, con la data e la
fonte.

> #### ⭐ E dove vive quel documento — *cambiato il 16 agosto 2026, per decisione dell'utente*
>
> ⚠ *La regola qui sopra **non è toccata**. Cambia solo il posto in cui il documento sta.*
>
> | | |
> |---|---|
> | **la fase in corso** | ha un file suo, `fasi/NN-nome.md`, aperto il giorno in cui si apre la fase ⇒ si lavora sempre su un file piccolo |
> | **la fase chiusa** | diventa un **capitolo di `FASI.md`**, ripiegato dentro alla chiusura |
>
> ⇒ Il progetto tiene **dieci documenti a fase chiusa e undici mentre si lavora**, e non si edita
> mai un file da settemila righe nel mezzo di una fase.
>
> ⛔ **E quel che questo NON allenta**: il capitolo non si scrive alla chiusura, si **sposta** un
> documento che esisteva già. Un capitolo che comparisse in `FASI.md` senza essere mai esistito
> come file avrebbe violato §0.1 — e **si vedrebbe**, perché le sue misure non avrebbero l'ora
> accanto.

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

> ### ⛔ Corretto la notte del 9 agosto 2026 — rilievi **R3.4** e **R4.3**, e l'ordine era circolare
>
> Questo paragrafo dice *«prima di scegliere la libreria QUIC e prima di scrivere il filo»*, e
> `STUDI.md` §web §7 aggiunge *«nessuna richiede una riga di prodotto»*. **Tre delle misure non stanno in
> piedi senza un server WebTransport**, cioè senza la libreria che si sta scegliendo:
>
> | | |
> |---|---|
> | **S1** | il controllo positivo è *«la connessione con l'impronta pubblicata **deve riuscire**»* |
> | ⛔ **S4** | vuole un server che **spedisca fotogrammi codificati** e un decodificatore che li accetti: non è «senza prodotto», è **la fase 3** — e pretende pure **una riga di protocollo** (`RCP.md` **§7.5** — `BANCO_MARCA` `0x000F` e `BANCO_ESITO` `0x0010`). ⚠ *Questa riga mandava a `RCP.md` §12, dove la voce è **sbarrata**: fu chiusa la notte del 9 agosto e resa normativa in §7.5, e chi seguiva il rimando trovava una voce cancellata. Corretto il 12 agosto 2026, trovato da **F2.4**.* |
> | la misura del **datagram** | vuole un ricevente |
>
> ⭐ **L'ordine onesto**: prima le misure che non toccano il filo — la durata dell'eccezione, la
> decodifica, la tastiera, la tela dichiarata, il segno della rotella — poi **il banco della
> libreria**, che produce un server minimo da cinquanta righe, e **sopra quello** il certificato e
> il datagram. ⚠ E se la candidata cambia, **quelle due si rifanno**: un controllo positivo preso su
> un motore diverso da quello del prodotto è la forma **E10**.
>
> Il conto completo, con i dispositivi che ciascuna pretende, sta in `FASI.md` §01-filo-nudo.

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

> ### ✅ FATTO il 14 agosto 2026 — [`STUDI.md` §xpra](STUDI.md#xpra) — ⛔ **e in ritardo, con un prezzo pagato**
>
> ⛔ *Questo studio doveva stare **prima della pagina**, ed è stato fatto **dopo**: l'ha chiesto
> l'utente una seconda volta, davanti al prodotto che finalmente si usava e con un difetto in mano
> («il puntatore sembra catturato… studia la soluzione di XPRA»).*
>
> | che cosa ha trovato | |
> |---|---|
> | ⭐⭐ **il cursore lo veste il browser** (`css("cursor", "url(…) x y, auto")`), e la cattura del puntatore è **un bottone**, non un automatismo | ✅ **adottato lo stesso giorno** — e ha smontato §7.1, che contraddiceva §7.5 |
> | ⭐⭐ **il primo fotogramma si CHIEDE** (`buffer_refresh` con `refresh-now`), non si aspetta | ⏳ **è il lavoro sul tempo di apparizione del desktop**, `[M]` 4,10 s su 5,21 spesi ad aspettare |
> | ⭐ **il client dice la sua misura e il server ridimensiona** (`configure_display`) | ✅ **fatto, ma solo a un capo**: la misura si dice e si prende **all'attacco e al riattacco** (`RCP.md` §4.5, `ADATTA_TELA`). ⛔ *Durante* la sessione no — uscito il 17 agosto 2026, `DECISIONI.md` §5.1-bis. ⚠ Xpra qui fa una cosa che noi **abbiamo deciso di non fare**, non una che ci manca |
>
> ⇒ ⚠ **Il costo di aver saltato il punto 0 non è stato il tempo dello studio**: è il codice scritto
> nel frattempo, e il difetto trovato dall'utente in trenta secondi d'uso invece che da noi.

---

# IL SERVER E LA PAGINA

## Fase 0 — L'ambiente e i banchi

**Produce**: la macchina che compila, e i banchi di v1 rimessi in funzione.

**L'utente vede**: i numeri di v1 **riprodotti** — la cattura di Mutter che consegna ~37
fotogrammi al secondo, KWin ~60. Non è un risultato di prodotto: è il **controllo positivo di
tutto il progetto**. Se il banco non sa riprodurre un numero che sappiamo vero, ogni misura futura
è sospetta.

> ⛔ *13 agosto 2026, e va letto insieme alla riga qui sopra: **il 37 non si riproduce**. Alla
> cadenza che chiedevamo Mutter consegna **31,5**; rinegoziando la sola cadenza, **61,4**. Non è il
> banco che sbaglia: il 37 non è una proprietà del compositore — ⚠ e che sia il resto di una
> divisione troncata è `[R]`, letto nel codice, **non misurato** (`STUDI.md` §gnome §8.2; la «legge su 13
> punti» che si leggeva qui il 13 agosto **è caduta la sera stessa**). ⇒ Il controllo positivo di
> questa fase va rifatto **contro le celle pulite di `banchi/03-b14-esiti.jsonl`**, non contro il
> numero.*

**Il banco**: `v1/banchi/banco-compositori/misura-cattura.c` e `banco.sh`, che rigenera da sé le
scene con `ffmpeg -f lavfi -i testsrc2`.

**Si riusa**: tutto `v1/banchi/` (262 file), `v1/banco/` per il provisioning.

⛔ **Passo zero, e senza di questo la fase non parte: GNOME non è più installato sul server**
`[M]` — `dpkg-query` dice *not-installed*, non c'è una `gnome.desktop` (`STUDI.md` §gnome §2). Il
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

> ### ⛔ Una domanda che la fase 1 ha trovato e che morde QUI — `[M]` 10 agosto 2026
>
> *Trovata dalla sonda S7, dopo tre giri andati a vuoto, dal controllo che dice «la pagina non vede
> nemmeno muoversi il puntatore». Portata qui l'11 agosto 2026 invece di essere riscoperta da un
> utente (`web/rapporti/S-esiti-sonda.md` §8, voce **S.4**).*
>
> ⛔ **In una sessione GNOME senza dispositivi di input fisici, se il client parte PRIMA che il
> puntatore virtuale di `libei` esista, non riceve nulla** — né rotella, né bottoni, **né il
> movimento del puntatore**. Se parte **dopo**, riceve tutto. `[M]`, ed è **l'ordine** a essere
> misurato.
>
> ⚠ **E non è che l'iniezione non arrivi**: Mutter la riceve in tutt'e due i casi —
> `org.gnome.Mutter.IdleMonitor.GetIdletime` cade da **35 952 ms a 1 013 ms** al primo movimento.
> ⛔ **Il compositore la prende e non la consegna alla finestra.**
>
> `[?]` **La causa non è verificata**: la spiegazione plausibile — una sessione senza dispositivi
> annuncia un `wl_seat` **senza puntatore**, e il cliente partito prima non si iscrive mai — non è
> stata provata. Quel che è `[M]` è l'ordine.
>
> ⛔ **Perché riguarda il prodotto, e riguarda questa fase e la 6**: nel prodotto la sessione grafica
> nasce **senza alcun dispositivo di input**, e le applicazioni aperte **prima** che un client si
> colleghi potrebbero trovarsi nello stesso stato — l'utente muove il mouse e quella finestra non
> risponde. ⇒ **Il banco di questa fase apre l'applicazione DOPO aver creato i dispositivi**, o
> misura una scena che il prodotto non avrà mai.

⚠ Qui la codifica è **software**, di proposito: l'accelerazione viene dopo, e metterla prima
significherebbe non sapere quale dei due pezzi sbaglia. ⭐ *E infatti è arrivata dopo, ma **prima**
della fase che la prometteva: la codifica in hardware è entrata nel prodotto il **13 agosto 2026**,
a fase 3 in corso, per poter misurare il prima e il dopo con lo stesso banco. La fase 8 non si
chiama più «l'accelerazione»: si chiama **«la copia zero»**, ed è quel che ne resta.*

⛔ **E qui nasce la sessione GNOME, che v1 avviava senza mai averla studiata** — le trappole sono
in `STUDI.md` §gnome §3 e valgono tutte al primo avvio, non dopo: `SHELL` va messa **vuota**, o
`gnome-session` si ri-esegue dentro una shell di login e si riporta dentro `~/.profile` `[R]`;
`--virtual-monitor WxH` **non è opzionale**, perché in headless la sessione parte altrimenti
**viva, completa e nera**; il drop-in dell'unità della Shell oggi si scrive **solo per KWin**
(`src/sessione.c:671`), quindi su GNOME va scritto adesso.

⭐ E una prova da fare **guasta di proposito** (M9 di `STUDI.md` §gnome §13): senza `--virtual-monitor`,
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

> # ⭐⭐⭐ DA QUI SI RIPRENDE — **la caccia è chiusa, e adesso si attua** · 20 agosto 2026
>
> *La caccia agli artefatti si è chiusa la sera del **17 agosto** con il giudizio dell'utente —
> **«NIENTE ARTEFATTI!»** — su un banco. ⛔ **Nel prodotto la cura non c'è ancora**, e finché non
> c'è l'utente vede quel che vedeva prima.*
>
> ## Che cosa si è saputo, in tre righe
>
> | | |
> |---|---|
> | ⛔ **la colpa non era nostra** | i pixel **entrano giusti** nella tela e si rompono **andando allo schermo**: `getImageData` legge il magazzino, non lo schermo ⇒ ogni banco che rilegge la tela era verde **per costruzione** |
> | ⭐ **la cura è misurata** | `createImageBitmap()` + `transferFromImageBitmap()` su un contesto **`bitmaprenderer`** — `DECISIONI.md` §5.4, prove in `fasi/06-la-tela-e-la-vista.md` §4.9 |
> | ⛔ **e AV1 esce dal prodotto** | Firefox per **Android** non ha né HEVC né AV1 ⇒ **H.264**, `avc1.640032` già verificato — `DECISIONI.md` §1.13-ter |
>
> ⛔ **Le otto ipotesi morte non si rifanno**: le sette del riquadro precedente (flusso AV1 rotto ·
> allineamento 962→968 · misura sbagliata alla pagina · errori del decodificatore · percorso di
> disegno della pagina · profondità 10/8 · xrdp+RemoteFX) ⛔ **più il `VideoDecoder`**, scagionato
> da `copyTo` contro la verità. Ognuna ha la sua misura in §4.9.
>
> ## ⭐ IL LAVORO CHE VIENE, in quest'ordine
>
> **1. ⭐⭐ La cura dentro `src/pagina.html`** — ⭐ **FATTA il 20 agosto 2026**, ed è in servizio
> sulla **7730**: `dipinti == consegnati`, `tard 0`, `err 0`, tela nitida a 1:1 col testimone
> Marionette (`fasi/06` §4.9-bis). ⏳ **Aspetta il giudizio dell'utente**, che è l'unica cosa che
> può chiuderla: nessun banco vede questo difetto. ⚠ E resta `[?]` **quanto costa
> `createImageBitmap`** — il conto da battere è 34,03 ms del `drawImage` che sostituisce.
>
> *Quel che è stato fatto, per chi rilegge:* è quel che l'utente **vede**, e andava davanti a tutto.
> Spariscono le **due** tele 2D (`deposito_p.drawImage(f)` e `pennello.drawImage(deposito)`); la
> tela visibile diventa `bitmaprenderer`; il deposito **non serve più** perché
> `transferFromImageBitmap` dimensiona la tela da sé e il contenuto sopravvive al
> ridimensionamento; il centraggio si fa **col CSS**. ⚠ E si **misura il costo**:
> `createImageBitmap` è asincrona ed entra nel ritardo.
> ⛔ **Chi giudica è l'utente, sulla sua scena** — nessun banco può vedere questo difetto (I8).
>
> **2. H.264 nel prodotto** — `RCP.md` §4.3/§6.2 (il terzo numero di codec **si aggiunge**),
> `codificatore.c` (`h264_vaapi` e il lettore dei NAL che riconosce l'**IDR**), `figlio.c`, e in
> `pagina.html` la scala di preferenza e il flusso di prova della sonda. ⚠ Con dentro la `[?]`
> della **scala di colore** del decodificatore hardware: +8 livelli sulle zone chiare.
>
> **3. ⚠ E resta la fase 6 aperta**: il suo §8 aspetta ancora il giudizio su due scene — il
> trascinamento del bordo e il clic tenuto giù.
>
> ## ⚙ Lo stato della macchina — verificato il 20 agosto 2026
>
> | | |
> |---|---|
> | **dove si lavora** | il deposito `git` sta sul **CHUWI** (`192.168.0.3`), che è anche la macchina da cui l'utente **guarda** |
> | **dove gira** | `NIC-OS`, **192.168.0.2**: `remotix-7700.service` e `remotix-7730.service` **tutt'e due vivi**, e la macchina **non si è riavviata** |
> | ⛔ **il deposito ha lavoro non commesso** | `figlio.c` (lo **scatto a comando**, `SIGUSR1`), `pagina.html` (la riga `MARCA` che dice **chi sta parlando**), e i banchi `07-b48`/`b49`/`b50` |
> | si riaccende con | `ALBERO=/media/REMOTIX/src/07-appunti-src LAV=/media/REMOTIX/tmp/07-appunti bash banchi/07-b41-accendi.sh --porta 7730 --hz 0` |
> | ⛔ le porte occupate | 7448 · 7700 · 7710 · 7720 · **7730** |
> | ⚠ il browser mette in cache | serve **`Ctrl+Maiusc+R`** dopo ogni cambio della pagina |
>
> ## ⛔ E i due difetti nostri che la caccia ha lasciato per strada
>
> **`?video=worker` non dipinge su Firefox**, e la causa è in mano: gli stream trasferiti al worker
> non vengono mai letti, quindi non si chiudono, e si esauriscono i **1024** stream unidirezionali
> di credito («il client ne concede ancora 0 … il delta che veniva dopo il 1023»). ⛔ E
> `postMessage` **non lancia**: la premessa del commento in `pagina.html` è falsa, quindi il
> ripiego non scatta mai. ⇒ La cura è un **riscontro**: se entro N ms il worker non ha letto il
> primo byte, si dichiara e si ripiega.
>
> ⚠ **E la verifica su Chrome è ancora in scadenza**: dopo la cura della profondità Chrome non
> l'ha più guardato nessuno.
>
> ---

## Fase 3 — Il movimento ✅ **CHIUSA il 14 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«abbastanza fluido, non il massimo ma pur sempre fluido»*
>
> | | |
> |---|---|
> | **il numero** | **78,1 ms** con la codifica **in hardware** (P1 verde, n=379) · **71,86 ms** con AV1 in software, che è la configurazione **giudicata** |
> | ⭐ **l'architettura** | **ASSOLTA**: togliendo la codifica in hardware si perdono **31,7 ms** e **gli altri quattro tratti non si muovono** (Mutter −0,02 · filo −0,12 · decodifica −0,76) |
> | ⭐ **la codifica in hardware** | **nel prodotto**, non su una copia: la chiave passa da **114,5 ms a 5,1**, il ritmo **raddoppia** |
> | ⛔ **il tetto** | **SFORA** — 78,1 contro 50, e **sforerebbe anche a codifica gratis** |
> | ⛔⛔ **il collo di bottiglia nuovo** | ⚠ ~~**il DISEGNO: 28,0 ms su 78,1, il 36 %**~~ ⇒ ⛔ **CORRETTO il 14 agosto 2026** (deciso dall'utente, su due misure indipendenti della fase 4): **il disegno costa 2,25 ms `[M]`**; i 28,0 erano **l'ATTESA del fotogramma dalla GPU** più il disegno — un fotogramma HEVC in hardware esce opaco e la rilettura della marca del banco ne provoca il trasferimento. ⭐ Il totale 78,1 resta vero. `fasi/rapporti/F4-A2-pagina-dipinge.md`, `F4-A10-anello-input.md` |
>
> ⛔ **E i tre limiti del giudizio sono scritti in `FASI.md` §03-movimento, non taciuti**: è su AV1
> in software; HEVC in hardware **non è giudicabile** perché il browser dell'utente non lo dipinge;
> e l'utente **non ha visto un desktop** ma un monitor aggiunto con dentro la scena dei banchi.
>
> ⭐⭐ **E il giudizio ha prodotto due difetti che nessun banco aveva trovato** — HEVC che non
> dipinge nella sessione vera, e il prodotto che **aggiunge** un monitor invece di mostrare il
> desktop. ⇒ *È esattamente il valore che il piano attribuiva al giudizio, e si è realizzato in
> trenta secondi.*

> ### ⭐⭐⭐ LA CODIFICA IN HARDWARE È ANTICIPATA QUI — deciso dall'utente il 13 agosto 2026, sera
>
> *E la fase 3 **non si chiude** finché non è fatta.*
>
> ⛔ **La ragione, e non è un'opinione: è un numero.** L'anello del ritardo misurato il 13 agosto
> dà **74,58 ms** di mediana, e la scomposizione dice dove sta:
>
> | tratto | mediana | cambia con l'accelerazione? |
> |---|---|---|
> | ⛔ **cattura → primo byte** (la codifica, **in software**) | **39,17 ms — il 53 %** | ⭐ **sì, è tutta lì** |
> | Mutter | 16,66 ms | no — è un intervallo di quadro a 60 Hz |
> | il disegno nella pagina | 10,51 ms | no |
> | la decodifica | 7,58 ms | poco, ed è già solo il 10 % |
> | il filo | 0,32 ms | no |
>
> ⇒ **Finché la codifica è in software, ogni numero di ritardo che le fasi 3-7 producono è dominato
> da un pezzo che sta per essere sostituito** — e andrebbe rifatto dopo. È l'obiezione dell'utente,
> ed è giusta: *«senza accelerazione hw stiamo ragionando e sviluppando su numeri non molto
> affidabili»*.
>
> ⭐⭐ **E si può fare, `[M]` verificato il 13 agosto 2026 sul server:**
>
> ```
> Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
> VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
> VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
> ```
>
> ⚠ *Un agente aveva riferito «su questo server non c'è un codificatore hardware per nessuno dei due
> codec». **È vero per AV1** — e stava già nei documenti — **ed è FALSO per HEVC**, che è proprio
> quel che la fase 8 promette. Nessuno l'aveva verificato: la riga è stata ripetuta, non misurata.*
>
> ⭐ **E costa poco farlo adesso**, per una ragione precisa: la catena che si muove **esiste da
> oggi**, il banco dell'anello è scritto, la scena e la marca sono certificate. ⇒ Il *prima* e il
> *dopo* si misurano con **lo stesso strumento e la stessa scena**, quindi i due numeri **si
> sottraggono davvero** — cosa che non sarebbe più vera fra tre fasi.
>
> ⛔ **Che cosa si anticipa, e che cosa NO**: si prende **la sola codifica in hardware**. La **copia
> zero** resta alla fase 8, è lavoro suo e non tocca questo numero.
>
> ⚠ **E la fase 8 non sparisce**: resta con la copia zero, e con la sua lezione che vale anche qui —
> *«si misurano i fotogrammi consegnati, non i millisecondi di CPU»*. In v1 il costo per fotogramma
> scese da 41 ms a 6 **mentre i fotogrammi consegnati scendevano da 29 a 22,7**.
>
> ⏳ **Il lavoro comincia in una sessione nuova** (deciso dall'utente). Il punto di ripresa sta nel
> `README.md`.
>
> ---
>
> ### ⭐⭐⭐ 13 agosto, sera — **IL BERSAGLIO È CONFERMATO AI DUE CAPI, e uno scoglio non c'era**
>
> *Il piano della sessione nuova è stato riletto **prima che partisse un agente**, e controllato
> misurando invece che ricordando. Ne sono uscite tre righe che cambiano il lavoro.*
>
> **1. ⛔⛔ La codifica AV1 in hardware NON ESISTE su questa macchina** — `[M]`, 3 giri su 3:
> `av1_vaapi` esce **218**, *«No usable encoding profile found»*, e `vainfo` dà AV1 in **sola
> decodifica** su tutt'e due i nodi. ⚠ Il codificatore **compare** nell'elenco di `ffmpeg`: *un
> elenco dice che il codice c'è, non che la macchina lo sa fare*.
> ⇒ ⭐ **Restare su AV1 vuol dire restare in software per sempre.** HEVC non è una preferenza: sul
> lato server è **l'unica strada verso l'hardware**.
>
> **2. ⛔⛔ Lo scoglio «nessun client accetta HEVC» era una BANDIERA del banco**, non un palco.
> `[M]` A/B con una sola variabile: senza `--disable-gpu` il Chrome del banco vede la GPU e dice sì
> a HEVC; con la bandiera dice no. ⭐ E **dipinge davvero** un flusso di `hevc_vaapi`: 5 giri su 5,
> 1920×1080, 119 fotogrammi su 120, `powerEfficient: true`.
> ⇒ **La corsia che doveva aprire la sessione è cancellata**, e la strada critica diventa
> *codifica → anello rimisurato*, senza rami che possano bloccarla.
>
> **3. ⭐ I numeri dei codificatori, a parità di bitrate e coi fotogrammi in uscita CONTATI** —
> 1920×1080 10 bit, 20 Mbit/s per tutti, 120 su 120 consegnati:
> **`hevc_vaapi` 3,16-3,24 ms** · `h264_vaapi` 3,11-3,16 · `vp9_vaapi` 6,95-7,28 · `av1_vaapi` **non
> esiste**. ⚠ Il primo giro di quella sonda **non era un confronto e il banco l'ha detto da sé**:
> a bitrate libero VP9 consegnava **trenta volte meno byte**. *«Più veloce» a un trentesimo del
> lavoro non è più veloce.*

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
  (`DECISIONI.md` §2.6). ⛔ **E qui arriva anche S4**, la misura del ritardo del *disegno* nel
  browser, che §1.2 metteva nella sonda: senza codifica, trasporto e decodifica non è eseguibile
  *(9 agosto 2026, rilievo **R3.4**)*. I suoi sette controlli e il **pezzo cieco** — 16-40 ms fra
  il disegno e il pixel acceso, che nessuna API vede e che **si dichiara accanto a ogni numero** —
  stanno in `STUDI.md` §web §6.3.

**I numeri da raggiungere**: ritardo ≤ 50 ms, traguardo 40 (`SPECIFICHE.md` §3.2).

> ## ⛔⛔ 13 agosto 2026 — l'esperimento è FATTO, e l'esito non era fra i due previsti
>
> *Qui stava scritto: «su GNOME il traguardo dei 40 ms probabilmente non si raggiunge, per il muro
> dei 37 fotogrammi di Mutter; se la misura lo confermasse non è un difetto nostro — ed è una
> ragione in più per la fase di KDE». E accanto: «prima di dichiararlo si prova la cadenza
> disaccoppiata… se riesce, GNOME entra nel traguardo; se non riesce, il muro diventa `[M]`».*
>
> ⛔ **L'esito non è «riesce» né «non riesce». È: «riesce con un numero diverso, e il prodotto non
> ci arriva» — e intanto il ritardo è stato misurato altrove, e la colpa è nostra.** Le tre metà:
>
> | | |
> |---|---|
> | ⭐ **la cadenza disaccoppiata RIESCE** | `[M]` monitor **120** + freno **90** ⇒ **61,4** consegnati (60,04), intervallo mediano **16,66 ms** — cella **D**, pulita. ⚠ **Ma M3 di `STUDI.md` §gnome §13 NON è chiusa: è mezza**, perché la causa non è misurata |
> | ⛔ **ma la causa scritta era sbagliata, e quella nuova è `[R]`** | non un **battimento** fra due orologi ma una **quantizzazione** — `min_interval_us = 10⁶/maxFramerate` troncato a intero (16666 per 60) contro un tick da 16666,67 µs — ⛔ **letta nel codice, non misurata**. E i «sei decimi» **non si riproducono**: la cella bassa dà **0,50 pulito** |
> | ⛔⛔ **e il prodotto non ci arriva** | `MOVIMENTO_FPS 60` è una costante di compilazione (`src/figlio.c:1465`), `main.c` non ha opzioni di cadenza, **`RecordVirtual` non prende la frequenza** (`src/mutter.h:82`): i quattro monitor virtuali sono tutti **@60**. È `[M]` **sul banco** e **zero in produzione** |
>
> ⛔ **E il ritardo, che è il numero per cui la fase esisteva, SFORA**: `[M]` mediana **74,58 ms**
> cattura → vetro, pezzo cieco 16-40 ms **escluso** ⇒ sullo schermo dell'utente **90-115 ms**,
> contro un tetto di 50. ⛔⛔ **Ma il muro non è di Mutter**: 16,66 su 74,6 è il **22 %**, il
> **78 % è nostro**, e ~39 ms stanno nel tratto cattura → primo byte, dominato dal **codificatore
> in software**. ⇒ La cura è la **fase 8**, non la 10 (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> ⚠ **E il 60 non è il 40 ms**: la cadenza non è il ritardo (`LEZIONI.md` §6.2). I 60 fotogrammi
> tolgono un ostacolo; il numero lo fa il ritardo.
>
> > ⛔⛔ ⚠ *La seconda riga della tavola diceva: «Legge su **13 punti**, 8 confermano, 0
> > smentiscono», e la prima dava **M3 per chiusa**. **Tutt'e due false**, e corrette la sera del
> > 13 agosto 2026 (rilievo del coordinatore della fase 3, verificato sui file di esiti): il file
> > `banchi/03-b14-esiti-griglia.jsonl` porta **due sole celle**, tutt'e due con
> > `scena_sul_mio_monitor: **false**` ⇒ rifiutate dal banco stesso, che stampa «⛔ la legge NON
> > regge su **0 punti su 0**». ⇒ **Il 61,4 resta un fatto `[M]`; il perché torna `[R]`; M3 resta
> > mezza.** ⭐ E la ragione del rifiuto è la trappola n. 1 di `LEZIONI.md` §1.1 — la scena non era
> > sul monitor che si catturava — **tornata a mordere il risultato che la citava**: §1.1-bis.*

---

## Fase 4 — Si comanda ✅ **CHIUSA il 14 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«mi sembra ok»*
>
> *e, sulle due ottimizzazioni che aveva chiesto: «la situazione mi sembra migliorata, la comparsa
> del desktop è più immediata».*
>
> | | |
> |---|---|
> | ⭐⭐ **che cosa vede** | **usa il desktop**: clicca, scrive, scorre, sposta le finestre. REMOTIX ha smesso di essere una dimostrazione |
> | ⭐ **il numero della fase** | l'anello **input → vetro**: `[M]` **139,40 ms** (n=326) e **141,60** (n=322), due giri indipendenti che concordano entro **2,2 ms** |
> | ⛔ **il tetto** | **SFORA** — 139 contro 50, e **160-193 ms** sul vetro coi due pezzi ciechi |
> | ⛔⛔ **e nessun tratto domina** | sei tratti da ~25 ms ⇒ **nessuna cura singola porta 140 a 50**: è lavoro della **fase 8** |
> | ⭐ **il login → desktop** | **5,11 s → 1,04-1,13 s**, e di quel secondo **1,00 è il fisso di §4.4-bis** |
> | ⭐⭐ **e il ritardo non cresce più** | prima **+108 ms al secondo** (⛔ 4,6 s di ritardo dopo 43 s, **con tutti i contatori verdi**); adesso **−2 ms/s** |
>
> ⭐⭐ **E il giudizio dell'utente ha trovato SETTE difetti che nessuno dei dieci banchi vedeva** —
> il monitor aggiunto, due server nostri sulla stessa sessione, la barra sul dock di GNOME, la
> cattura del puntatore, il palco fallito tenuto per sempre, ⛔ e **una riga del coordinatore** che
> costava quattro secondi al login. **Sette su sette stavano FRA i pezzi, nessuno dentro uno.**
>
> ⛔ **E si chiude con cinque cose dichiarate aperte**, messe davanti all'utente **prima** che
> giudicasse: il ritardo che sfora · la tela che non è la sua (**36 % di banda nera** sul suo 21:9)
> · il monitor chiesto sempre invece di guardare se c'è · un pezzo cieco dentro il tratto da 26 ms
> · e **un browser solo**. Stanno in [`FASI.md` §04-si-comanda](FASI.md#04-si-comanda).


> ### ⭐⭐⭐ IL PRIMO LAVORO DELLA FASE 4 È IL **DESKTOP VERO** — deciso dall'utente il 14 agosto 2026
>
> *E non è una premessa alla fase: **è dentro la fase**, in testa.*
>
> ⛔ **La ragione, in una riga**: la fase 4 esiste perché *«l'utente **usa** il desktop»* — ma
> **finché il desktop non si vede, non c'è niente da comandare**. I banchi del cursore, delle
> lettere accentate e delle scorciatoie non avrebbero **dove guardare**: si misurerebbero su uno
> schermo vuoto.
>
> **Il difetto, e la cura è in DUE posti non uno:**
>
> | | |
> |---|---|
> | `src/sessione.c:650` | crea la sessione con `--headless --no-x11 **--virtual-monitor %ux%u**` ⇒ GNOME mette la shell **su quel monitor** |
> | `src/mutter.c:450` | cattura con **`RecordVirtual`**, che **ne monta un altro** e registra quello ⇒ **l'utente guarda il secondo, vuoto** |
> | ⛔ **e la seconda metà della cura** | `src/sessione.c:668` **rilegge l'`ExecStart` in vigore e PRETENDE `--virtual-monitor %ux%u`** ⇒ tolta la bandiera, il controllo **fallirebbe**. *Il controllo è giusto, l'atteso no* |
>
> ⭐ **La tesi è già PROVATA, il 14 agosto, senza toccare il prodotto**: sessione dell'utente
> `prova` avviata **senza** `--virtual-monitor` (`GetCurrentState` → **0 monitor**, la sessione
> *«viva, completa e nera»* di `STUDI.md` §gnome §3.1); collegato il client, `RecordVirtual` monta
> **l'unico** monitor e ⭐ **la shell ci va sopra: barra, sfondo, dock**. La prova sta in
> [`fasi/rapporti/F5-desktop-vero.md`](fasi/rapporti/F5-desktop-vero.md) e nell'immagine
> `F3-verbali/desktop-vero-14ago.png`.
>
> ⚠ **Due cose da MISURARE prima di crederle, e non sono dettagli:**
> 1. ⛔ **chi decide la misura del monitor** adesso che non la dà più la sessione: la dà
>    `RecordVirtual`, e **che cosa succede se il client ne chiede un'altra?** È `RCP.md` §4.5, la
>    tela concessa, e da qui in poi tocca questo pezzo;
> 2. ⚠ **`PIANO.md` (questo file, più su) e `STUDI.md` §gnome §108 dicono che `--virtual-monitor` non è
>    opzionale**. ⇒ **Vanno riscritte**: sono vere solo per una sessione che deve vivere **senza
>    nessuno che la catturi**.
>
> ⚠ **E l'utente `prova` si conserva** (deciso il 14 agosto): è l'unico posto dove oggi il desktop
> vero si vede, perché `nicfio` ha già una sessione con un monitor suo e §5.1 ne ammette **una sola
> per utente**.

**Produce**: ⭐ **il desktop vero** (qui sopra) · il canale di input, il puntatore disegnato dalla pagina, le lettere e le posizioni —
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
non vengono consegnati `[R]` (`STUDI.md` §gnome §1.1 punto 6 e §5.2). Da chiedere qui, dove il canale
nasce. ⭐ **Il verso è quello giusto per noi**: pixel puliti nell'immagine *e* la forma in banda
laterale, che è esattamente ciò che serve al puntatore disegnato dal client.

⚠ **Due ricambi silenziosi di libei**, che mordono qui e alla fase 6: un cambio di **keymap**
distrugge e ricrea il dispositivo tastiera, un cambio di **geometria** tutti i dispositivi
assoluti — e il puntatore al dispositivo vecchio smette di funzionare **senza errore** `[R]`
(`STUDI.md` §gnome §9). Keymap e regioni si rileggono a **ogni** `DEVICE_ADDED`, non una volta all'avvio.

**Si riusa**: `input.c` (906 righe, libei), `tastiera.c` (372, xkbcommon).

---

## Fase 5 — La sessione ✅ **CHIUSA il 16 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«funziona»* · *«il task nel terminale era ancora in esecuzione»*
>
> *E la prova che vale l'ha fatta lui, con un lavoro VERO dentro: si logga massimizzato, lancia un
> ciclo infinito nel terminale, chiude il browser, rimpicciolisce la finestra, rientra — e il ciclo
> girava ancora. ⛔ Tutte le prove nostre avevano un desktop **vuoto**, che è il testimone peggiore
> possibile: appena rinato è identico a com'era.*
>
> | | |
> |---|---|
> | ⭐ **l'accesso** | `[M]` **2087 ms** di mediana su venti giri dal browser, **187 ms** di dispersione; peggiore caso a freddo **2353 ms**. ⛔ La mattina era 3211 ms di mediana con **p90 17255** e max **18158** |
> | ⭐ **la coda dei 17 secondi** | trovata: il palco nasceva alla tela di ripiego e il ridimensionamento **non si compie su una scena ferma**. ⇒ il figlio aspetta la tela del cliente |
> | ⭐ **§7.3, il rilascio al distacco** | provato sul **desktop vero** con un testimone che conta le battute: un tasto rimasto giù si ripete **33 volte al secondo**, e il rilascio lo ferma in **15-28 ms** |
> | ⭐ **i tre orologi** | il silenzio contava **l'utente invece del client** (un secondo dispositivo entrava sul desktop di chi stava leggendo: **I2 rotta**) ⇒ riparato sui pacchetti · l'inattività (`0x02`) **non esisteva** ⇒ fatta · le 6 ore diventano **60 minuti**, per decisione dell'utente su una misura di memoria |
> | ⭐ **`0x0F`** | il secondo dispositivo è respinto, provato **da un telefono vero** — mai uscito prima su una connessione vera |
> | ⭐ **la sessione senza nessuno che guarda** | costa **0,017 %** di un nucleo e **477 MB** che non crescono. In v1 `libmutter` andava in asserzione fallita |
> | ⛔ **e tre righe di registro mentivano** | `RILASCIO AL DISTACCO: 0` che non poteva dire altro · il testo `0x02` della pagina che nominava l'orologio sbagliato · *«l'utente ha chiesto di uscire»* detto da un orologio. ⇒ `LEZIONI.md` §1.9 ha la sua **quinta regola** |
> | ⛔ **e il modulo d'accesso stava sotto il desktop** | da sempre: il «vestito da desktop» non nascondeva niente. Trovato dall'utente, in tre segnalazioni |
>
> ⇒ ⭐ **Restano due cose sole**, e l'elenco è stato **tagliato** col criterio dell'utente — *«se i
> punti non toccano il prodotto è solo rumore burocratico»*: `0x05` (l'utente con una sessione
> grafica **locale**, che vuole una persona alla consolle) e il banco del puntatore dopo il ricambio
> dei dispositivi. Dettagli in `FASI.md` §05-la-sessione §7.

**Produce**: PAM per intero, il palco che sopravvive al distacco, i tre orologi, una sola sessione
grafica per utente.

> ### ⭐ E il confine col multi-tenant è stato deciso il 15 agosto 2026 — `DECISIONI.md` §4.6-quater
>
> **Qui: un utente remoto per volta.** Niente budget, niente conteggio, `MAX_ATTACCATE` resta il
> `#define` a 16 dichiarato come ripiego. Il multi-tenant come **funzione** — più sessioni insieme,
> `BUDGET_PIENO`, il tetto configurabile — è della **fase 10**, perché ha bisogno di un numero vero
> e il numero lo dà il codificatore hardware della **fase 8**.
>
> ⛔ **Con un pezzo che non si rinvia**: il guardiano di logind di `0x04`/`0x05` deve discriminare
> **per utente**, e non è una scelta — è la macchina di prova che lo impone. `nicfio` ha la sessione
> grafica **locale** e `prova` arriva da **remoto**: un guardiano che chieda *«c'è una sessione
> locale?»* invece di *«di questo utente?»* rifiuta `prova` **il primo giorno**.
>
> ⭐ **E le quattro decisioni della sera del 15 agosto stanno tutte in `FASI.md` §05-la-sessione**: le
> due uscite (§4.1-ter), il ritorno al modulo di accesso col motivo nuovo `0x10` (§4.1-quater), la
> scorciatoia `Ctrl+Alt+Fine`, senza bottone a schermo (§4.1-quinquies), e ⛔ **nessuno spegne il
> server** (§4.7).

**L'utente vede**: chiude il client, va a pranzo, riapre — **e ritrova tutto com'era**.

**Il banco**:
- distacco e riaggancio, **due volte di fila**: un banco che passa solo da macchina pulita non è un
  banco, è una dimostrazione (`LEZIONI.md` §2.3-ter);
- ⛔ **la sessione senza nessuno che guarda**: in v1 il monitor virtuale spariva al distacco e
  `libmutter` andava in asserzione fallita, con le applicazioni che perdevano la connessione
  Wayland. È il difetto che rende la sessione inutilizzabile dopo il primo stacco;
- i tre orologi, ciascuno con la sua prova;
- l'apertura di una sessione locale mentre la remota è viva → la remota **deve** cadere con
  `SESSIONE_LOCALE_PREVALSA`, e il motivo si verifica **dal lato che lo riceve**;
- ⭐ **e il gemello che mancava**: una sessione locale **già attiva** e una remota che arriva →
  `GIA_ATTIVA_LOCALE` `0x05` (`SPECIFICHE.md` §5.1). *Aggiunto il 9 agosto 2026, rilievo **R4.16**:
  era di `RCP.md` §8.2 e di nessuna fase, e sarebbe caduto fra le fasi;*
- ⛔ **il rilascio dei tasti al distacco**, che `RCP.md` §11 chiama *«la regola col rapporto
  danno/costo più alto del documento»*: si stacca con un tasto premuto **e si riattacca** a
  verificare che non sia rimasto giù. *Portato qui dalla fase 4 il 9 agosto 2026, rilievo **R4.7**:
  alla fase 4 non esiste una sessione a cui riattaccarsi — la sessione muore con la connessione —
  quindi quel banco lì o non si scrive o **si scrive verde per costruzione**.*

⛔ **E due difetti che l'utente incontrerebbe lasciando la sessione ferma venti minuti**, tutt'e
due su GNOME e tutt'e due mai affrontati in v1 (`STUDI.md` §gnome §4 e §7):

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

> ## ⏳⛔ PRIMA DELLA FASE 6: IL PIANO VA RIVISTO — rilievo dell'utente, 16 agosto 2026
>
> Alla chiusura della fase 5, l'utente: *«prima dobbiamo rivedere il piano che ha alcuni punti
> secondo me fuori sequenza»*.
>
> ⇒ ⛔ **La fase 6 non si apre finché quella revisione non è fatta.** ⚠ E il sospetto ha già un
> precedente in questo stesso documento: la fase 6 dichiara che **tre quarti del suo lavoro sono già
> fatti** — nella coda della **fase 4** — perché *«il numero della fase lo dà il perché si è fatto il
> lavoro, non l'elenco delle cose prodotte»*. Un piano in cui una fase nasce già fatta per tre quarti
> è esattamente il posto dove guardare.

## Fase 6 — La tela e la vista

**Produce**: la tela concordata all'attacco, la vista che riscala, il riattacco a misura diversa.

> ## ⭐⭐ TRE QUARTI SONO GIÀ FATTI E MISURATI — nella **coda della fase 4**, il 15 agosto 2026
>
> ⛔ **E non è un errore di numerazione**: il numero della fase lo dà il **perché** si è fatto il
> lavoro, non l'elenco delle cose prodotte. `DECISIONI.md` §5.0-sexies aveva reso la tela **la cura
> di quattro sintomi del mouse e del video** — bande nere, testo interpolato, ri-attacco, e i 4
> secondi fra login e desktop — cioè il pezzo che mancava alla **fase 4**. Tutti i rapporti di quella
> notte si chiamano `F4-IN-*`. ⇒ Il documento sta in `FASI.md` §04-si-comanda, §«la coda della fase
> 4»; il rapporto tecnico è `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.
>
> | quel che questa fase chiede | stato |
> |---|---|
> | la **tela concordata all'attacco** | ✅ `[M]` la tela prende la misura della finestra, scala **1,000** |
> | il **riattacco a misura diversa** | ✅ `[M]` `SESSIONE` concede la tela che il palco ha già, zero fotogrammi scartati |
> | la **vista che riscala** | ✅ c'era dalla fase 2, e adesso la scala vale 1 quando le due tele combaciano |
> | ⛔ *(in più)* ~~il **ridimensionamento a caldo**~~ | **USCITO dal prodotto il 17 agosto 2026** — `DECISIONI.md` §5.1-bis, decisione dell'utente: *«non voglio mettere delle eccezioni nel progetto»*. ⚠ Era `[M]` 6 ms su Mutter, e **impossibile** su KWin ≤ 6.7.4 |
> | ⛔ il **ripiego su KWin dichiarato nel registro** | **APERTO**: non verificabile finché KDE è la fase 11. Il percorso di codice c'è (`COMPOSITORE_INCAPACE`) ed è provato dal caso 11 di `banchi/04-b31`, **su un ospite finto** |
> | ⛔ il **banco del riattacco che BATTE UN TASTO dopo** | **APERTO**: il fatto si è visto nel registro (`libei` ricrea i dispositivi, `input.c` li riaggancia) e l'utente ha scritto in un terminale dopo un riattacco — ⛔ ma un banco che lo provi non c'è |
> | ⛔ il **multi-monitor** | **APERTO**, e fuori scopo come funzione (§6.5) |
>
> ⇒ ⭐ **Quando questa fase si aprirà davvero, il suo lavoro è quel che resta in fondo a questa
> tabella** — e le prime quattro righe si rimisurano invece di rifarle.
>
> ⛔ **E quel che di questa fase resta APERTO, per intero:**
> - il **ripiego su KWin ≤ 6.7.4 dichiarato nel registro**, che è il banco nominato qui sotto;
> - ⛔ **il banco del riattacco che batte un tasto e muove il puntatore DOPO** — la riga qui sotto
>   che parla dei dispositivi ricreati. `[M]` il 15 agosto si è visto nel registro che al cambio di
>   geometria `libei` **ricrea davvero** i dispositivi assoluti («regione del puntatore per chiave»,
>   quattro volte di fila), e che `input.c` li riaggancia — ⚠ ma a battere un tasto dopo il
>   riattacco **non ci ha ancora provato nessuno**;
> - il **multi-monitor** e tutto il resto di §6.5.

**L'utente vede**: ridimensiona la finestra e l'immagine si adatta **senza che le finestre dentro
si muovano**. Poi si riattacca da una macchina con un altro schermo e ritrova la sessione adattata.

> ⭐ **E dal 17 agosto 2026 questa frase è vera sempre, non «salvo un interruttore»** — l'immagine
> si adatta e **il desktop non si tocca mai**, su ogni compositore (`DECISIONI.md` §5.1-bis).
> ⚠ Il prezzo dichiarato: se la finestra cambia **forma**, o il tablet si **ruota**, le proporzioni
> non combaciano più e si vedono le bande. Per riavere la misura giusta ci si **riattacca**.

**Il banco**: il ripiego su KWin < 6.8 **dichiarato nel registro** — si verifica che la riga ci
sia, non che «funzioni lo stesso» (`SPECIFICHE.md` §6.3).

⛔ **E il riattacco rinegozia anche la disposizione di tastiera** (`SPECIFICHE.md` §7.3), che su
Mutter **distrugge e ricrea il dispositivo tastiera**; un cambio di geometria ricrea tutti i
dispositivi assoluti. Il puntatore al dispositivo vecchio smette di funzionare **senza errore**
`[R]` (`STUDI.md` §gnome §9). Il banco del riattacco **deve battere un tasto e muovere il puntatore
dopo**, non solo verificare che la sessione ci sia: è la forma «una prova verde col difetto vivo»
esattamente dove si presenta.

⛔ **E con lo stesso peso, l'ordine fra la nascita del puntatore virtuale e l'avvio delle
applicazioni** — riquadro nella fase 2, `[M]` 10 agosto 2026: un cliente Wayland partito **prima**
che i dispositivi di input esistano **non riceve niente**, e il compositore l'iniezione la prende lo
stesso. Al riattacco i dispositivi si **distruggono e si ricreano**: è esattamente il caso in cui
questa trappola torna, su applicazioni già aperte che nessuno riavvierà.

---

## Fase 7 — Audio e appunti

> ## ⭐⭐ L'AUDIO È FATTO — 17 agosto 2026, sul giudizio dell'utente: **«problema audio risolto»**
>
> *Dato su un **video di YouTube** riprodotto nella sessione remota.* `[M]` **49,95 blocchi/s
> ricevuti contro 50 prodotti** — perdita **zero**, 2 buchi (dell'avvio), coda 311-341 ms.
> ⭐ E il volume **governa**: pieno 0,3536 · 25 % 0,0078 · muto 0,0.
>
> ## ⭐⭐ E GLI APPUNTI FUNZIONANO — **«clipboard funziona in entrambi i versi»**
>
> *Giudizio dell'utente col browser, 17 agosto 2026 sera, porta 7730.* Solo testo, nei due versi:
> `appunti.c` nuovo, i tre messaggi di §7.4 nel filo, la cucitura nei due processi e il lato
> browser. ⇒ 📖 `fasi/07-audio-e-appunti.md` §4.5, §6.9, §9.2-bis.
>
> ⛔ **E l'arbitro esterno del banco NON ESISTE**: `gnome-shell` gira con `--no-x11`, quindi `xclip`
> non ha nessuna sponda a cui parlare, e un client Wayland senza fuoco non possiede la selezione.
> ⇒ Quel giudizio è **l'unica prova** che questa metà della fase abbia — e la riga di §2.4 che
> prometteva un arbitro gratis è stata riscritta.
>
> ⭐ *E la richiesta d'apertura diceva «testo formattato»: chiesto all'utente, che ha confermato
> «solo testo semplice» — `DECISIONI.md` §5-ter.4.*
>
> ⛔ **E la lezione della fase non è sull'audio**: cinque giri di banco verdi e l'utente sentiva
> «jitter pazzesco». `LEZIONI.md` §2.7 — *non c'è miglior strumento di diagnosi che monitorare una
> sessione vera, byte per byte*. Le decisioni prodotte stanno in `DECISIONI.md` **§5-quater**, che
> prima di oggi non esisteva.

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
`[R]` (`STUDI.md` §gnome §10). Copiare con `xclip` e leggere col client — invece di far parlare fra loro
due pezzi nostri — è l'arbitro esterno che a questa fase serviva e che non credevamo di avere.

⛔ **Tre trappole di Mutter, che il banco non vede e il prodotto sì**: `DisableClipboard` è **a
senso unico** (dopo, gli annunci non tornano più — non si chiama mai: per lasciare la clipboard
si usa `SetSelection` senza tipi); la firma di `mime-types` è **asimmetrica** fra ingresso `as` e
uscita `(as)`, e chi legge col tipo sbagliato ottiene `NULL` **senza errore**; il gestore interno
degli appunti tiene **un solo tipo MIME**.

**Si riusa**: `altoparlante.c` (892), `suono.c` (582), `appunti_mutter.c` (450), `appunti.c` (115).

⚠ Invariante I5: il volume appartiene alla sessione, e chi si collega lo trova **al massimo**.

---

## Fase 8 — La copia zero ✅ **CHIUSA il 22 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»*, e *«per me è ok»*
>
> *Il titolo del piano dice ancora «la copia zero»; il documento di fase si chiama
> [`fasi/08-l-anello.md`](fasi/08-l-anello.md) perché il mandato vero — dettato dall'utente il
> 22 agosto — era **l'anello**, di cui la copia zero è un tratto.*
>
> | | |
> |---|---|
> | ⭐⭐ **che cosa vede** | trascina una finestra veloce e **la finestra segue la freccia**. Al mattino restava indietro di **mezza barra del titolo** |
> | ⭐ **il numero della fase** | `input → vetro` **89,86 → 55,20 ms** (−39 %), **appaiato**: due giri che condividono tutto tranne il binario, `macchina carica: false` scritto dal banco in tutt'e due |
> | ⭐ **nell'unità dell'utente** | distacco **0,27 → 0,16 barre** ⇒ da **2,1** a **1,23 volte il locale** — e ⭐ il **locale** adesso è misurato: **0,142 barre** (n=254) |
> | ⭐⭐ **e non è una vittoria di cronometro** | `[M]` i fotogrammi **dipinti** salgono del **+9 %**. `LEZIONI.md` §6.2 rispettata, dopo che in questa stessa fase era stata sfiorata **due volte** |
> | ⛔ **il tetto dei 50 ms** | **non è verificato**, e non perché manchi poco: **55,20 sta su un confine diverso** da quello dei 50 (`SPECIFICHE.md` §3.2 misura fino al *fotogramma che parte*). ⇒ I due numeri **non si confrontano** — è `LEZIONI.md` §1.28 applicata a noi stessi |
>
> **⭐ Le tre eredità, tutte e tre risposte**: `EncSliceLP` **non** sa fare i sotto-livelli temporali
> (7 profili su 7, due controlli positivi) · la chiave alla tela dell'utente sta allo **0,13 %** del
> tetto, margine **782×** · la scheda del codificatore adesso si **dichiara** invece di ripiegare in
> silenzio. E `RCP.md` §5.2 e §6.2 passano da `[?]` a ✅.
>
> **⭐⭐ E i difetti trovati per strada, nessuno dei quali era il bersaglio**: la **chiave abbandonata**
> (§5.2 la vieta, ed era la spirale) · la **scala delle ricodifiche corta di uno scalino** · il
> **passo non multiplo di 64** che dava un desktop **inclinato senza errori** · e il **cronometro del
> prodotto che misurava il banco**.
>
> **⛔⛔ E le due lezioni che sopravvivono alla fase**, `LEZIONI.md` **§1.26**, **§1.27** e **§1.28**:
> due banchi sulla stessa **macchina** si falsano in silenzio (e danno **un numero plausibile**, non
> un rosso) · il **colore medio è cieco** a un'immagine sbagliata a ogni riga · e **due banchi che
> non concordano possono avere ragione tutti e due**: misurano due grandezze diverse.
>
> ⏳ **Che cosa NON è stato fatto, e si porta avanti:**
> - ⛔ **il muro di Mutter**: `[M]` **16,0 ms**, un quadro a 60 Hz esatto, **un sesto dell'anello** —
>   non si è mosso di tre decimi in tutta la giornata, e **non l'ha toccato nessuno**;
> - ⛔ **metà del guadagno non è spiegato**: **15,9 dei 34,7 ms** stanno in un tratto che la copia
>   zero **non attraversa**. `[?]` L'ipotesi — il produttore fuori dal thread di tempo reale — è
>   **dichiarata, non misurata**;
> - ⚠ **la ritenuta del `pw_buffer` è in vigore senza prova**: il controllo positivo **non ha
>   riprodotto il danno**. Prudenza, non necessità misurata;
> - `[?]` **il modello del distacco ha predetto male due volte, in versi opposti** — prima meno del
>   vero, poi più. ⛔ **È un fatto sul modello, non sull'utente**, ed è lavoro nostro;
> - 🔸 **la tela multipla di 16** (`rcp_misura_ammessa()`): renderebbe la copia zero valida su **ogni**
>   schermo, ⛔ ma è una **modifica al protocollo** — `RCP.md` §4.5 oggi pretende solo che i lati siano
>   pari. **Decide l'utente.**

## ~~Fase 8 — La copia zero~~

> ## ⭐ E IL 22 AGOSTO 2026 L'UTENTE LE HA INDIRIZZATO **L'UNICO APPUNTO CHE GLI RESTAVA**
>
> *Dopo aver dichiarato OK l'audio su tutti e quattro i motori supportati:* **«l'unico piccolo
> appunto è un'ottimizzazione sulle performance grafiche, che credo sia lo scopo della fase 8»**.
>
> ⭐ **Non sbaglia**, ed è la seconda volta che indirizza una cosa a questa fase leggendo il piano.
> ⚠ **E vale come mandato**: quando questa fase si apre, il suo metro non è «la copia zero è
> scritta», è **quel che lui vede muoversi meglio**.
>
> ⏳ **E ci arriva con due misure già in mano**, prese la notte del 21-22 agosto:
> - `[M]` **`createImageBitmap` costa 3,8 ms mediani per fotogramma**, l'8 % del tetto di 50 —
>   accanto ai ~4,8 ms del codificatore in hardware. ⭐ E il percorso attuale costa **nove volte
>   meno** del disegno 2D che c'era prima;
> - `[M]` **il percorso `?video=worker` funziona e NON rende**: abbassa il tetto del **19 %**. ⇒ La
>   strada «spostare il disegno su un altro thread» è **già stata provata e non paga**: chi apre
>   questa fase non la rifaccia.

> ## ⭐⭐ IL TITOLO È CAMBIATO, E DUE TERZI DELLA FASE SONO GIÀ FATTI — *16 agosto 2026*
>
> *Rilievo dell'utente all'apertura della fase 6: «gli ultimi test sono stati eseguiti con l'ausilio
> della Intel integrata, e quindi usando l'accelerazione HW, o sbaglio?». **Non sbaglia**, ed è
> scritto qui perché chi arriva a questa fase non cerchi lavoro già consegnato.*
>
> *Qui il titolo era **«L'accelerazione»** e la riga diceva: «**Produce**: HEVC in hardware su
> Intel, 10 bit, e la copia zero».*
>
> **La codifica in hardware è entrata nel prodotto il 13 agosto 2026**, di proposito e con la
> ragione scritta sopra alla fase 3: la catena si muoveva **da quel giorno**, quindi il *prima* e
> il *dopo* si potevano misurare **con lo stesso banco e la stessa scena** — cosa che fra tre fasi
> non sarebbe più stata vera. `src/codificatore.c:614` la chiama *«la fase 8 entrata di soppiatto
> nella fase 2»*.
>
> | la promessa di questa fase | dov'è finita |
> |---|---|
> | ⭐ **HEVC in hardware su Intel** | ✅ **fatto e misurato.** `src/figlio.c:2434` chiede `hevc_vaapi` su **`/dev/dri/renderD128`** — l'iGPU Intel, entrypoint `EncSliceLP` — e il ripiego su `libx265` **scrive di essere un ripiego**. `[M]` il tratto della codifica **61,77 → 30,37 ms**, i fotogrammi **14,53 → 30,18 al secondo** (`F3-E`, stesso palco, notte del 14 agosto), e oggi la chiamata al codificatore vale **5,3 ms** dentro quel tratto (fase 4, `hev1.2.4.L120.B0`, nodo aperto dai soli processi nostri) |
> | ⚠ **10 bit** | ⛔ **nominali, e il muro è a monte, non qui.** `DECISIONI.md` §2.3-ter `[M]`: dalla cattura di Mutter dieci bit veri **non escono per nessuna strada** — MemFd dà BGRx, il DMA-BUF pure, e chiedendo i formati a 10 bit da soli si prende `no more input formats` su tutt'e due. `Main10` da qui vuol dire **otto bit promossi a dieci**. ⇒ La domanda non è più *«il nostro codice sa fare 10 bit?»* ma *«esiste una sorgente che ce li dia?»*, ed è **una domanda per la cattura**, non per la codifica |
> | ⛔ **la copia zero** | **intatta — e non anticipata di proposito** (`README.md`: *«la copia zero NON si anticipa: resta alla fase 8»*). È tutto quel che segue |
>
> ⭐⭐ **E il conto della fase 4 dice che quel che resta pesa più di quel che è stato tolto.** Il
> tratto più caro dell'anello è ancora `cattura → primo byte`, `[M]` **30,37 ms**, e dentro ci sta:
>
> | | ms | lo toglie la copia zero? |
> |---|---|---|
> | la conversione (swscale) | **5,6** | ⭐ **sì** |
> | il caricamento sulla GPU | **2,9** | ⭐ **sì** |
> | la codifica, **in hardware** | 5,3 | no — è già curata |
> | ⛔ **e ~16 ms che nessuno dei tre spiega** | **~16** | ⏳ `[?]` **da scoprire, e stanno in questo tratto** |
>
> ⇒ ⭐ **8,5 ms sono esattamente il lavoro che la copia zero cancella** — convertire e ricaricare
> sulla GPU un fotogramma che **sulla GPU ci stava già** — cioè **il doppio** di quel che la
> codifica costa oggi. ⛔ E i ~16 ms non spiegati sono **nello stesso tratto**: è qui che si cercano,
> e questa fase è l'unica che ha il motivo di guardarci dentro.

> ## ⭐⭐⭐ E IL 22 AGOSTO L'UTENTE HA DETTATO LA SPECIFICA — `SPECIFICHE.md` §3.2-bis
>
> *«La mia specifica è avere un'esperienza utente **il più vicina possibile a una situazione
> locale**, ma non identica: quello è impossibile.»*
>
> ⭐ **E ha precisato il sintomo con l'occhio, che è una misura**: trascinando veloce una finestra,
> la distanza fra la freccia e la finestra che la insegue è **«metà della barra del titolo»** ⇒ su
> una finestra di 720 px, **≈ 360 px**.
>
> ⛔⛔ **Da cui il vero mandato di questa fase, e NON è la copia zero**: quel distacco è
> `velocità della mano × ritardo dell'anello`, la freccia è locale e la finestra no ⇒ **è un
> ELASTICO** che si apre quando la mano accelera. La copia zero toglie **8,5 ms su ~139**: il **6 %**.
> ⇒ Serve **l'anello intero**, ed è quel che la fase 4 aveva già scritto chiudendo: *«sei tratti da
> ~25 ms ⇒ nessuna cura singola porta 140 a 50: è lavoro della fase 8»*.
>
> ⛔ **E una strada è chiusa prima di aprirsi**: mettere l'anello in parallelo comprerebbe
> fotogrammi pagandoli in ritardo ⇒ **allargherebbe l'elastico**. §3.2 lo vietava già: *«una scelta
> che alza il ritmo peggiorando il ritardo non si fa»*.
>
> ⏳ **Il primo numero del banco** non è più un tratto: è **`input → vetro` rimisurato sulla scena
> vera** — finestra 720×433, velocità mediana **3 400 px/s**, picchi **12 400** (`[M]` dal video
> dell'utente, 22 agosto). Il 139,40 ms della fase 4 ha otto giorni e due fasi di cure in mezzo.

**Produce**: ⭐ **l'anello più corto**, di cui la copia zero è **un tratto su sei** — il fotogramma
va dalla cattura al codificatore **senza uscire dalla GPU**.

**L'utente vede**: ⭐ **la finestra che insegue la freccia più da vicino**, e giudica quanto ci si è
avvicinati al locale. ⚠ *(Era: «la stessa immagine di prima, e giudica che non sia peggiorata» — il
metro di quando questa fase era solo la copia zero.)*

**Il banco**, ed è la lezione che è costata di più:
- ⛔ **si misurano i fotogrammi consegnati, non i millisecondi di CPU.** La fase 9 di v1 ha portato
  il costo per fotogramma da 41 ms a 6 mentre i fotogrammi consegnati **scendevano** da 29 a 22,7.
  Un guadagno che si paga in fluidità non è un guadagno (`LEZIONI.md` §6.2). ⛔⛔ **E qui morde
  due volte**, perché la fase 4 ha trovato la coda che cresce: il server consegnava **39,6**
  fotogrammi/s e la pagina ne dipingeva **34,7**. Un guadagno di millisecondi che si trasformasse
  in fotogrammi che nessuno dipinge **peggiorerebbe il ritardo** invece di curarlo;
- ⛔ **chiedere il codificatore per nome e verificare che abbia obbedito**: un codificatore che
  ripiega in CPU credendosi in GPU produce due misure sotto la stessa etichetta. Se non obbedisce,
  si dichiara il fallimento (`LEZIONI.md` §1.8). ⭐ Il modo giusto è già nel prodotto e si riusa:
  `componente_e_hardware()` **chiede al componente** quali formati accetta — una superficie, non
  dei pixel — invece di leggere `_vaapi` dentro il nome;
- ⚠ e la prova «ha aperto un render node ⇒ rende in GPU» **non prova niente** (§1.11);
- ⛔ **e il numero si rifà con lo STESSO banco e la STESSA scena della fase 4** (`03-b17-ritardo.py`),
  o il prima e il dopo non si sottraggono. ⚠ Non basta il totale: si affiancano **i tratti**, perché
  la domanda di questa fase è *«tolta la copia, gli altri restano dove sono?»*.

⛔ **E la copia zero si riapre dal lato giusto**: le due schermate che si alternavano non erano un
problema di *acquire* ma di **release** — `can_reuse_pw_buffer` si arrende se manca
`SPA_META_SyncTimeline` e Mutter riusa il buffer **mentre VA-API lo sta ancora leggendo** `[R]`
(`LEZIONI.md` §8, il riquadro della caccia sbagliata). Due cure candidate, entrambe piccole:
chiedere la timeline — che Mutter offre — oppure **trattenere** il `pw_buffer` fino a lettura
finita. ⚠ E **il DMA-BUF di Mutter non è un diff**: chi riprendesse la superficie di accumulo
rifarebbe la cura che peggiorava le cose.

⭐ **E la strada è aperta `[M]`**: Mutter il DMA-BUF **lo consegna davvero** — 388 fotogrammi, 4
buffer, modificatore **LINEAR**, stride 7680 letto dal chunk (`DECISIONI.md` §2.3-ter). ⚠ Il
formato resta **BGRx a 8 bit**: la copia zero si fa su quello, e i dieci bit non tornano da questa
porta.

> ### ✅ ⭐ La trappola della GPU è CHIUSA, e va detto perché nessuno la ricerchi — *15 agosto 2026*
>
> *Qui stava scritto: «con due schede, il compositore che disegna su quella sbagliata dà
> composizione in software **senza un errore**. La regola udev di `v1/banco/gpu-udev.sh` va
> applicata e verificata».*
>
> ⛔ **Ed era peggio di un rischio: era già successo.** `[M]` `/etc/udev/rules.d` era **vuota**, i
> gruppi `video`/`render` davano accesso a tutt'e due le schede, e il compositore aveva preso la
> **Radeon** — una misura di 60 fps buttata perché fatta sulla scheda sbagliata.
>
> ⭐ **La regola è stata applicata e verificata** (`DECISIONI.md` §4.6-ter): `gnome-shell` apre
> **6 descrittori su `renderD128`**, l'integrata, e solo quella. ⇒ **Compositore e codificatore
> stanno sulla stessa scheda** — che è precisamente la condizione senza la quale la copia zero non
> avrebbe senso: un fotogramma non si passa senza copia fra due schede diverse.
>
> ⚠ **Il prezzo resta dichiarato**: negare il nodo lo nega a **tutta la sessione dell'utente**, non
> al solo compositore.

⏳ **Che cosa questa fase NON deve più portarsi dietro**, e dove sono andati:
- i **10 bit veri** → una domanda per la **cattura**, e vive nelle fasi in cui la cattura si tocca;
- ⚠ la **qualità di `EncSliceLP` contro l'entrypoint pieno** → `[?]` **mai misurata**: la codifica a
  bassa potenza è veloce e **non è equivalente** alla piena. È il punto di lavoro fra qualità e
  banda, cioè la **fase 9** — e se un giorno si scoprisse peggiore, si cura lì, non qui.

---

## Fase 9 — La qualità e la degradazione ✅ **CHIUSA il 24 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«il prodotto cambia in meglio; questa fase era per rendere più solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli»*
>
> 📖 `fasi/09-la-qualita-e-la-degradazione.md` — la sintesi in testa, e §17-§21 la parte che conta.
>
> ⭐⭐ **Il bersaglio l'ha corretto lui a fase aperta** (`DECISIONI.md` §3.1-ter): non la **banda** —
> *«30 mbps sono una connessione da metà anni 90»* — ma **la rete che perde, riordina e sfarfalla**.
> Ed era la grandezza giusta: sulla banda il prodotto non cedeva, su un filo sporco sì.
>
> **La scala che chiude la fase, e viene dai suoi occhi** (§19.1, §19.6):
>
> | perdita reale | senza cure | con cure |
> |---|---|---|
> | 1 % | *«mi sembra ok»* | — |
> | 5,6 % | *«è tutto fluido»* | — |
> | **10 %** | ⛔ *«bloccato»* | ⛔ *«bloccato lo stesso»* |
>
> ⛔ **Sopra una certa perdita la scala di degradazione non ha più niente da offrire**, e l'unica
> risposta onesta è dichiarare la linea morta (§3.1-quater) — che è la decisione che lui ha preso
> **prima** di avere quel numero.
>
> **Le cinque cure sono ACCESE** (§3.1-septies), ognuna con una strada sola per spegnerla, e ⭐ **la
> prova che poteva far ritirare tutto è verde**: `[M]` sulla linea sana 39,69 fotogrammi/s contro
> 39,60 a cure spente — **nessun peggioramento**, che è la ferita per cui v1 perse questa fase.
>
> **I tre fatti che restano**, e valgono oltre la fase:
> 1. ⭐⭐ **il difetto non comincia dove si vede**: la spirale di chiavi parte al **primo pacchetto
>    perso** (0,10 %), il calo che l'utente **vede** arriva cinque volte più in là (0,53-0,75 %);
> 2. ⭐⭐ **l'innesco ha un rischio costante** — ~5 % al secondo, mediana **13 s**, e una volta acceso
>    non si spegne. ⛔ I banchi girano 25 s, **le sessioni durano ore**: ogni misura presa vicino al
>    bordo **sottostima**;
> 3. ⛔ **il disordine viene scambiato per perdita**, e ci è tornato addosso: la prima «linea morta»
>    era tarata su `pkt_lost`, e `[M]` una linea che **regge** ne dichiarava il **512‰** contro il
>    **123‰** di una che **non regge**. Rifatta sullo **stallo dell'uscita**.
>
> ⚠ **E il conto degli errori di metodo, che è la parte più utile**: `[M]` **nove difetti nei
> banchi**, tutti della forma *«silenzio invece di rosso»* · **tre prove che non mordevano**, scoperte
> contando i pacchetti · **due conclusioni mie ritirate** (le applicazioni che «non arrivavano», la
> prova della claquette dichiarata «nulla» e smentita dal terzo giudizio) · e **due premesse false**
> ereditate e corrette (l'utente non è mai stato su PCM; il +331 ms non raggiunge il suo orecchio).


**Produce**: il controllo del ritmo, la scala di degradazione, il comportamento su rete cattiva.

> ### ⛔⭐⭐⭐ IL BERSAGLIO È STATO CORRETTO — **23 agosto 2026, a fase aperta**
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti
> che perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».*
> — ⇒ `DECISIONI.md` **§3.1-ter**.
>
> ⛔ **La banda esce dal corpo della fase.** La giornata era stata passata a stringere la linea, e
> `[M]` §16: sul **percorso vero** il caso peggiore chiede 21,5-23,1 Mbit/s e il prodotto lo regge
> **senza degradare e con tutte le cure spente** — 7 125 consegnati → 7 125 dipinti, **una** chiave.
> Un banco che non riesce a far cedere quel che misura **non sta misurando la grandezza giusta**.
>
> ⭐ **Le tre grandezze nuove, e non sono la stessa cosa:**
> **perdita** (il video ritrasmette ⇒ si paga in ritardo; l'audio no ⇒ si paga in buchi) ·
> **fuori sequenza** (⭐ è la condizione mancante della cura del riordino dell'audio, l'unica cura
> del 23 agosto la cui metà utile non è mai stata verificata) ·
> **jitter** (`[?]` QUIC può scambiarlo per perdita e stringere la finestra **senza motivo**: se
> succede il calo è **nostro**, non della rete).
>
> ⚠ **§3.1-bis non è annullata**: il pavimento dichiarato resta — ⛔ **ed è passato a 30 Mbit/s la
> notte stessa** (§3.1-sexies: *«ho già detto che il pavimento, per quanto riguarda la banda, è a
> 30 mbps»*). Cambia il suo mestiere — da **domanda** della fase a **premessa** su cui si misurano
> le altre tre.
>
> ⛔⭐⭐ **E la fase ha prodotto una decisione nuova, §3.1-quater**: una linea che perde **a raffiche**
> si dichiara **morta** — 10 s senza pacchetti, o una perdita copiosa dentro 1-2 s — e ✅ **l'utente
> rientra a mano**. Nasce dalla scelta fra due mali misurati: `[M]` senza cure lo schermo si congela
> **14,26 s**, con le cure si muove con **4,5 s di ritardo**. ⇒ Nessuno dei due va servito.
> ⛔ Prerequisito: **§3.1-quinquies**, il *fantasma* — rientrando, l'utente trova il proprio posto
> occupato da sé stesso per 30,5 s, e con un messaggio che per lui è **falso**.
>
> ⛔ E il `netem` su `lo` diventa **risorsa unica con lucchetto** (`banchi/09-lucchetto.py`): la
> disciplina si mette sulla radice dell'interfaccia, quindi due banchi che guastano insieme non si
> dividono il lavoro — il secondo **cancella il guasto del primo**, e il primo continua a misurare
> credendo di averlo. ⚠ Non darebbe rosso: darebbe un numero plausibile.

**L'utente vede e giudica**: l'immagine. ⛔ **Ed è l'unico giudizio che conta**: in v1 questa fase
era stata validata con PSNR, SSIM e l'occhio dello sviluppatore, e il giudizio dell'utente sul
desktop vero fu *«siamo tornati indietro»*. La fase fu azzerata.

**Il banco**: la rete strozzata a valori veri — ⭐ **20 Mbit/s, il pavimento dichiarato dall'utente
il 23 agosto** (`DECISIONI.md` §3.1-bis), con perdita e giro lungo — e la verifica che il ritmo cali
**senza mai bloccarsi** e senza mai staccare.

> ⛔ **Il numero era «2 Mbit/s», ed è cambiato il 23 agosto 2026.** *«Mi ero tenuto più largo:
> ritengo che una connessione minima debba essere 20 mbps: al di sotto di questo limite l'utente
> nemmeno riesce a navigare, figuriamoci usare remotix».* ⇒ ⭐ **Cambia che cosa si sta tarando**:
> la scala di degradazione copre i **cali temporanei di una linea buona**, non le linee povere.
> ⚠ E cambia il verso di un rischio: a 20 Mbit/s il fondo scala non si raggiunge quasi mai, quindi
> il difetto che si nasconde non è più «degrada male», ma **«degrada quando non dovrebbe»** — che
> è l'invariante I1, ed è precisamente la prima cosa che questa fase verifica.
>
> ⭐ **Lo strumento per strozzare dal lato del client c'è**: `wondershaper` in `~/.local/bin` sul
> tablet dell'utente — ⇒ si può strozzare **il percorso vero**, non solo `lo` con `netem`, che è
> il limite dichiarato di `banchi/07-b64-rete.py`.

⛔ **La cosa che si verifica per prima**: che il ritmo **non** cali quando la scena è ferma. È
l'invariante I1, ed è la ferita da cui nasce.

⚠ E ciò che cambia quel che si vede sta **dietro un interruttore spento** finché l'utente non l'ha
guardato (I6).

> ### ⛔⛔ CORREZIONI DEL **23 agosto 2026, sera** — quel che i fatti hanno superato
>
> *📖 Tutto in `fasi/09-la-qualita-e-la-degradazione.md`, la sintesi in testa.*
>
> **1. ⛔ «Strozzare a 20 Mbit/s» NON prova quel che questa fase deve provare.** `[M]` §3.10:
> con la banda chiesta **sotto** il buco **non succede assolutamente niente**. ⇒ ⭐ **Serve un
> GRADINO** — larga → 3 s stretti → larga — non un limite costante: un limite costante misura il
> **regime**, e in regime la previsione è che non succeda niente. ⛔ E **tre secondi bastano**:
> portano il ritmo da 40 a 13/s e fanno diventare **metà dei fotogrammi delle chiavi**.
>
> **2. ⭐⭐ «Che il ritmo non cali a scena ferma» è MISURATO, e la risposta è più netta della
> domanda**: a scena ferma il ritmo **non cala, si FERMA** — 1 fotogramma in 30 s, poi zero.
> ⛔ **E non è una nostra decisione**: `RecordVirtual` di Mutter consegna **solo sul cambiamento**
> (123 attese a vuoto al secondo). ⭐ **E il risveglio non costa niente**: 180 colpi, **13 ms** di
> mediana da 0,2 a 15 s di quiete, coda larga **2 ms**. ⇒ È una violazione **letterale** di I1 che
> **non costa niente a chi guarda**, e **non è un difetto della fase**.
>
> **3. ⭐ Le due cose «già misurate» del riquadro qui sotto SONO STATE SCRITTE il 23 agosto**, con
> altre tre: la cura di `video_sgombra()` (`--sgombra-soglia-ms`, spenta), il riordino dell'audio
> (senza interruttore), la risalita della qualità (`--qualita-risale`, spenta), il tetto di banda
> (`--tetto-banda-mbit`, spento) e ⛔ **la cura di un crollo**: il server è morto di `SEGV` alle
> 08:28:09 per un **uso dopo la liberazione** in `webtransport.c`. ⚠ **Nessuna delle cinque è stata
> misurata sulla macchina di prova.**
>
> **4. ⛔ E il difetto che si nasconde non è solo «degrada quando non dovrebbe».** `[M]` §3.8: con
> QP 26 fisso e nessun tetto, un **film con la grana a schermo intero** chiede **58,7 Mbit/s = il
> 293 % del pavimento**. ⭐ **Ma il desktop vero dell'utente ne chiede l'1 %.** ⇒ Il tetto è per il
> **caso duro**, e la fase ha **due** bersagli, non uno.
>
> **5. ⛔ E il regolatore del ritmo ha un ordine obbligato**: viene **dopo** la soglia sulla coda.
> Finché `video_sgombra()` svuota la coda a ogni fotogramma, la grandezza su cui il regolatore si
> aggancia è **zero per costruzione** — e un regolatore muto e una linea sana hanno la stessa faccia.

⭐ **E questa fase adesso ha un secondo cliente, che prima non aveva**: la scala di degradazione è
**il modo in cui si fa stare più gente sulla stessa macchina**. Un budget senza la scala sa dire
solo *«no»*; con la scala sa dire *«sì, più piccolo»* — ed è la fase 10, che viene subito dopo.

⏳ **E qui arriva una domanda che la fase 8 le ha passato**: `[?]` la qualità dell'entrypoint
`EncSliceLP` — la codifica a **bassa potenza**, quella che il prodotto usa — contro quello **pieno**,
a parità di banda. **Non è mai stata misurata**, e il punto di lavoro fra qualità e banda è di
questa fase.

> ### ⭐⭐ E LA NOTTE DEL 21 AGOSTO QUESTA FASE HA RICEVUTO DUE COSE GIÀ MISURATE
>
> *Arrivano dalla chiusura dei buchi delle fasi 6 e 7, ⛔ e sono state **spostate qui dall'utente**:
> «i problemi di rete non rientrano in questa fase, qui stiamo chiudendo i buchi delle fasi 6 e 7».
> ⚠ Il coordinatore aveva portato la decisione nella stanza sbagliata.*
>
> **1 · ⛔ Il motore della spirale: `video_sgombra()` abbandona i delta a OGNI fotogramma.**
> `[M]` Su linea larga non abbandona quasi mai; su linea stretta un delta non esce in 33 ms, quindi
> viene abbandonato **sempre**, e ogni abbandono riaccende il debito di §5.2 — il registro lo dice
> **28 volte al secondo**. ⇒ Il video degenera in **un flusso di sole chiavi**, che è la forma
> peggiore di degradazione: pesante, a scatti, e affama l'audio.
> ⭐ **La cura è nominata e §5.1 la permette senza imporla**: abbandonare un delta solo quando è
> *davvero senza speranza* (una soglia sulla coda) invece che a ogni fotogramma più recente. Così
> sotto congestione il video calerebbe di **ritmo** restando fatto di delta.
> ⚠ **Il prezzo va giudicato dall'utente**, ed è esattamente il mestiere di questa fase: per una
> frazione di secondo si vedrebbe qualcosa di leggermente vecchio. ⛔ In v1 una fase come questa fu
> azzerata perché validata con PSNR invece che con l'occhio: **non si decide senza di lui**.
>
> **2 · ⛔ La finestra di riordino dell'audio.** `src/pagina.html` scarta un datagram *«più vecchio
> di quel che è già ARRIVATO»*, mentre `RCP.md` §6.3 dice *«già consumati»*. ⇒ Si butta un blocco
> arrivato **un millisecondo** fuori ordine **mentre si tengono 250 ms di cuscino**.
> `[M]` con `netem`: ritardo di 30 ms fissi ⇒ purezza **1,000**; **jitter di ±2 ms ⇒ 0,175**, con
> 1 004 datagram scartati su 4 989. ⭐ Su WiFi vero, invece, i «vecchi» sono **zero** — ed è la
> ragione per cui è di questa fase e non della 7.
> ⚠ Due avvertenze già pagate: `netem delay X Y` **riordina davvero**, una coda di casa di solito
> no; e la misura è in **PCM da 5 ms** — con Opus (20 ms) la soglia sarebbe ~4 volte più alta.
>
> ⭐ **E la strumentazione per giudicarle è già scritta**: `banchi/07-b65-datagram.py` (la rete
> strozzata coi byte veri presi dal qdisc, il controllo scena accesa/spenta che decide),
> `banchi/07-b64-rete.py` e `banchi/07-b64-orecchio.py` (il giudice del tono, certificato 4 su 4).
> ⇒ Questa fase non parte da zero: parte da un banco che sa già dire quando **non** ha misurato
> niente.

---

## Fase 10 — Multi-tenant e il budget

> ## ⭐⭐ SPOSTATA QUI DALLA CODA DEL PIANO — *16 agosto 2026, decisione dell'utente*
>
> *Era la **fase 12**, dopo i tre desktop nuovi. L'utente: «PRIMA si chiude lo sviluppo anche con il
> multi-tenant, e solo dopo si pensa agli altri DE».*
>
> ⚠ **Le fasi dei desktop non sono state declassate: sono state riconosciute per quel che sono.**
> Producono **larghezza** — il secondo, terzo e quarto desktop — su una forma che il multi-tenant
> può ancora cambiare. E l'argomento non è nuovo: è **lo stesso** con cui `DECISIONI.md` §4.6-quater
> aveva rimandato il multi-tenant dopo la fase 8 — *«misurarle prima vuol dire misurarle due volte»*
> (`LEZIONI.md` §7.2) — applicato dall'altro capo:
>
> | | |
> |---|---|
> | ⭐⭐ **la profondità prima della larghezza** | se il multi-tenant tocca la sessione o il budget, la modifica va riverificata **su quattro desktop invece che su uno**. È «misurarle due volte», moltiplicato per quattro |
> | ⛔ **e il budget è un budget di GPU, e la GPU è UNA** | il numero si misura su `renderD128` — la stessa iGPU che compone **ogni** desktop. È una proprietà **della macchina**, non del desktop: misurata una volta, le fasi 11 e 12 la ereditano. Misurata dopo, non si sa più quale numero appartenga a che cosa |
> | ⭐ **e la dipendenza inversa non esiste** | niente qui dentro ha bisogno di KDE, XFCE o LXQt |
> | ⚠ **e la macchina di prova è GIÀ multi-utente** | `nicfio` locale + `prova` remoto che devono convivere: §4.6-quater lo chiama *«lo stato normale della macchina, non uno scenario da inventare»* |
>
> ⚠ **E quel che questa fase NON evita, detto per intero**: l'architettura c'è già in buona parte —
> `figlio.c:80` dichiara *«un utente per figlio»*, un processo per sessione. ⇒ Non si sta scansando
> una riscrittura strutturale; si sta evitando di **misurare un numero di macchina quattro volte**.
>
> ⛔ **E la precedenza che resta, e va rispettata**: questa fase sta **dopo la 8**. La copia zero
> cambia **quanto costa una sessione** in memoria e banda di GPU — e il budget misurato prima della
> copia zero è un budget da rifare. È §4.6-quater alla lettera, e non è cambiato niente.
>
> ⚠ **Le parole dell'utente del 15 agosto dicevano «fase 12»** (`DECISIONI.md` §4.6-quater,
> `FASI.md` §05-la-sessione), e **restano scritte così** dove sono citate: era il numero di allora.
> ⭐ **La decisione non è cambiata — è cambiato l'ordine**: il confine fra «un utente per volta» e
> «la macchina piena» è ancora quello che lui ha tracciato.

**Produce**: più utenti insieme, il budget del codificatore, il rifiuto motivato.

**L'utente vede**: due sessioni vere in contemporanea; e quando la macchina è piena, un messaggio
che **dice perché**.

**Il banco**: si satura il codificatore di proposito e si verifica che l'undicesimo riceva
`BUDGET_PIENO` — e che **i dieci che stavano lavorando non peggiorino** (`DECISIONI.md` §4.6-bis).

⚠ **E il debito con la scadenza scritta è di questa fase**: `MAX_ATTACCATE` è un `#define` a **16**
in `rcp.c:568` — e `MAX_FIGLI` a 16 in `figlio.c:83`, che lo segue — dove `SPECIFICHE.md` §5.5
promette **dieci configurabile**. Oggi non morde, perché 16 > 10. ⭐ Qui scade.

> ## ✅ APERTA IL 24 AGOSTO 2026, **CHIUSA IL 25** sul giudizio dell'utente
>
> *«Sono soddisfatto. Riprodotto audio e video su una connessione del 1990. Non credo che si
> possa chiedere di più.»* ⚠ E **due decisioni non prese**, dichiarate: QVBR resta **spenta**,
> tetto **10** e riserva **0,5**.
>
> 📖 **`fasi/10-multi-tenant-e-il-budget.md`**.
>
> ⭐ **Il debito è saldato**: i `#define` a 16 erano **cinque, non due** (`MAX_ATTACCATE`,
> `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI` — e quest'ultimo era **8**, un sesto numero ancora
> diverso). Adesso scendono tutti da **`RCP_TETTO_SESSIONI`**, vale **dieci**, e si muove a caldo con
> **`--tetto-sessioni N`**.
>
> ⛔⛔ **E la premessa della fase era sbagliata**: *«il budget del codificatore»*. `[M]` Il collo è la
> **composizione** — **0,97 Gpixel/s** contro **1,86** — e a saturarlo è **`gnome-shell`**, non noi.
> ⇒ `DECISIONI.md` **§4.6-nonies**.
>
> ⭐ **E quel che l'utente vede è stato prodotto**: due sessioni vere insieme (ne stanno **almeno
> undici** sul desktop vero), e ⭐ **`BUDGET_PIENO 0x06` parte davvero**, con una frase che dice
> *perché* — fino a questa fase era dichiarato in `rcp.h` e in `RCP.md` **e nessuna riga del server
> lo mandava mai**.

---

## Fase 11 — La rete di sicurezza

> ## ⭐⭐⭐⭐⭐ DECISA DALL'UTENTE IL 25 AGOSTO 2026, a fase 10 appena chiusa
>
> *«Prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi. Prima di
> passare agli altri DE è necessaria una sessione dedicata per studiare una modalità che impedisca di
> introdurre regressioni man mano che verrà implementato il supporto ai nuovi DE.»*
>
> ⇒ `DECISIONI.md` **§4.6-duodecies**. ⚠ **KDE, XFCE e LXQt scalano di uno**: diventano le fasi 12,
> 13 e 14. Le fasi **non cambiano di una riga** — cambia il loro posto, come già il 16 agosto.

**Produce**: un modo di accorgersi **da soli** che qualcosa si è rotto, prima che lo scopra l'utente.

**L'utente vede**: niente di nuovo sullo schermo — ⭐ **e questo è il punto**: vede che le cose che
funzionavano **continuano a funzionare** quando arrivano i desktop nuovi.

---

### ⛔ Perché questa fase esiste — tre difetti veri, non un timore generico

| il difetto | nascosto per | ⛔ perché era invisibile |
|---|---|---|
| **la sessione che nasce cieca** (fase 10 §7.4) | giorni | ⛔ **nessuno apriva una sessione NUOVA**: si riusavano quelle già aperte, che il monitor ce l'avevano |
| **`~/.cache -> /tmp`** | **due fasi** | ⛔ e il controllo che *«chiudeva la questione»* girava da un utente **con lo stesso difetto** |
| **cinque banchi che contavano zero fotogrammi** | un giro | ⛔ una cura al registro ne aveva rotto le espressioni, e la funzione tornava **0 invece di «non lo so»** |

⇒ ⭐⭐ **Tutti e tre invisibili per la stessa ragione**: si guardava sempre **lo stesso pezzo di
scena**, e si guardava **il processo invece del pixel**.

---

### Che cosa deve produrre, in concreto

| # | | ⛔ e il perché sta in un difetto vero |
|---|---|---|
| **1** | ⭐ **Una prova di CONSEGNA che parte da zero**: macchina pulita → utente nuovo → sessione nuova → **un'immagine del desktop con una finestra dentro** | ⛔ è l'unica forma che avrebbe preso la sessione cieca. Una prova che riusa una sessione **non la prende mai** |
| **2** | ⭐ **Invarianti eseguibili**, poche e vere: la sessione ha un monitor · una finestra si apre · i fotogrammi arrivano · **chi c'è già non peggiora** (I1) · le gemelle R12.3 combaciano · il registro dice **di chi** parla | ⚠ Poche. ⛔ Una rete con cento maglie che nessuno legge è cerimonia |
| **3** | ⛔ **Che giri DA SOLA** dopo ogni modifica, senza che qualcuno se ne ricordi | ⛔ le tre volte di oggi nessuno se n'è ricordato — **e nessuno era distratto**: semplicemente non c'era il gancio |
| **4** | ⭐⭐ **Che sia CERTIFICATA lei stessa** — `--certifica`, coi guasti innestati | ⛔ `LEZIONI.md` §1.36: *lo strato che coordina i banchi è un banco anche lui, e nessuno lo certifica*. `[M]` **sei difetti** trovati lì dentro in una fase sola |
| **5** | ⭐⭐⭐ **Che sia CIECA AL DESKTOP** — le stesse invarianti puntate su GNOME, KDE, XFCE, LXQt senza riscriverle | ⛔ è l'intera ragione per cui la fase sta **prima** dei desktop nuovi: una rete scritta su misura di GNOME va riscritta quattro volte |
| **6** | ⚠ **Che guardi la CONSEGNA, non solo il sorgente** | ⛔ `~/.cache -> /tmp` non era nel nostro codice: era nella **macchina**. Una rete che compila e prova solo `src/` non l'avrebbe presa mai |

---

### ⛔⛔ IL COLLAUDO DELLA FASE — ed è già scritto, oggi

⭐⭐ **La rete si punta contro il codice del 25 agosto 2026, e DEVE diventare rossa su §7.4** — la
sessione che nasce cieca — ⛔ **senza che nessuno le abbia detto dove guardare.**

⚠ **E il secondo collaudo**: deve prendere anche `~/.cache -> /tmp`.

⇒ ⛔ **Se non li prende, non è una rete: è un rituale.** ⭐ E il metro della fase non è *«quante prove
girano»*: è **che cosa la rete PRENDE**.

---

### ⚠ Quel che questa fase NON è

⛔ **Non è «scrivere più banchi».** Ce ne sono già più di cento, ⭐ e non sono serviti: i tre difetti
di oggi sono passati **in mezzo a loro**. ⇒ Il problema non è la quantità delle prove — è ⭐ **da dove
partono** (da zero, o da uno stato che funzionava già) e ⭐ **che cosa guardano** (il pixel, o il
processo).

⚠ **E non è una fase di ceremonia**: se alla fine la rete non ha preso niente che l'occhio non
avrebbe preso, **la fase è fallita**, e va detto.

---

## Fase 12 — KDE

⚠ *Era la **fase 10** fino al 16 agosto 2026: il multi-tenant le è passato davanti, e la ragione sta
nel riquadro della fase 10. **La fase non è cambiata di una riga** — è cambiato il suo posto.*

**Produce**: il secondo desktop.

**L'utente vede**: la stessa cosa su Plasma.

> ## ⛔⛔ La motivazione PRESTAZIONALE di questa fase è caduta — *13 agosto 2026*
>
> *Qui stava scritto: «E qui si insegue il numero desiderato: KWin consegna 60 fotogrammi al secondo
> dove Mutter ne dà 37 `[M]`. La fase di KDE non è solo "servire più desktop": è la strada per i 60 a 4K
> e per il traguardo dei 40 ms».*
>
> ⚠⚠ **La fase resta, e resta giusta: è «il secondo desktop», ed è la ragione per cui era stata
> messa nel piano.** Quel che si toglie è **la promessa sul ritardo**, che si appoggiava a due
> numeri e nessuno dei due regge:
>
> | quel che la riga diceva | che cosa dice la misura del 13 agosto |
> |---|---|
> | «Mutter ne dà **37**» | ⛔ **non si riproduce**. Alla cadenza che chiedevamo Mutter consegna **31,5** (mediana 33,31 ms); rinegoziando la sola cadenza (monitor 120, freno 90) ne consegna `[M]` **61,4** — cioè **quanto KWin**. Il 37 non è una proprietà del compositore; ⚠ che sia il resto di una divisione troncata è `[R]`, letto nel codice e non misurato (`STUDI.md` §gnome §8.2) |
> | «è la strada per il traguardo dei **40 ms**» | ⛔ **no.** Il ritardo misurato è `[M]` **74,58 ms** cattura → vetro, e Mutter ne vale il **22 %** (16,66 su 74,6). Il **78 % è nostro**, ~39 ms nel tratto cattura → primo byte, **dominato dal codificatore in software**. ⇒ Cambiare compositore **lascerebbe intatti i 39 ms di codifica** |
>
> ⇒ ⛔ **Chi arriva a questa fase aspettandosi che porti il ritardo dentro il tetto resterà deluso**,
> e va scritto qui perché nessuno ci conti sopra pianificando: il ritardo **non si cura cambiando
> compositore** (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> > #### ⛔⛔ E LA DOMANDA APERTA HA AVUTO RISPOSTA — *e la mezza promessa qui sopra è caduta anche lei, 16 agosto 2026*
> >
> > *Qui stava scritto: «⏳ `[?]` **Resta aperto e non è stato misurato** quanto scenderebbe il numero
> > con un codificatore **hardware**: è la domanda della fase 8, non di questa» — e, un rigo prima,
> > «il ritardo si cura **sulla codifica**, ed è la **fase 8**».*
> >
> > ⭐ **Misurato**, perché la codifica in hardware è entrata nel prodotto il 13 agosto, e la
> > risposta sta in `fasi/rapporti/F3-E-anello-rimisurato.md`. ⛔ **Ed è a due facce**:
> >
> > | | `[M]`, stesso palco, notte del 14 agosto |
> > |---|---|
> > | ⭐ **il tratto della codifica** | **61,77 → 30,37 ms**, cioè **−31 ms**: il pezzo ha ceduto per intero, come il piano sperava |
> > | ⭐⭐ **i fotogrammi consegnati** | **14,53 → 30,18 al secondo**, dipinti **1 407 → 2 949** — ⭐ **il doppio**. È la lezione di `LEZIONI.md` §6.2 applicata e **passata**: senza questo numero il −31 sarebbe stato metà della notizia |
> > | ⭐ **e gli altri quattro tratti restano dove sono** | Mutter −0,01 · filo −0,07 · decodifica −0,72 ⇒ **l'architettura è assolta**: tolta la codifica, non è emerso niente di nascosto |
> > | ⛔⛔ **ma il TOTALE non è sceso** | **72,40** (AV1 in software) **→ 75,23** (HEVC in hardware, n = 799): il codec che rende possibile l'hardware **sposta ~16 ms sul client** — l'attesa del fotogramma dalla GPU, che per un giorno si è chiamata «il disegno» |
> >
> > ⇒ ⛔ **Il collo di bottiglia si è SPOSTATO, non è sparito**, e adesso sta nel client: **28,0 ms
> > su 78,1, il 36 %**, contro i **5** che ormai costa la codifica. ⭐ E si vede solo perché i tre
> > giri esistevano tutti e tre: con due soli si sarebbe letto *«−33 ms, vittoria»* oppure
> > *«+2,8 ms, l'hardware non serve»*, e **sono tutt'e due sbagliate**.
> >
> > ⇒ ⛔⛔ **La lezione, e vale per tutto il piano**: *«il ritardo si cura sulla fase N»* era vera
> > **sul pezzo** e falsa **sul totale**. Il collo di bottiglia più grosso è stato tolto per intero,
> > e il ritardo che l'utente sente non è migliorato — è raddoppiato il **ritmo**, che è un'altra
> > grandezza. ⚠ Chi scrive la prossima riga che promette un tetto da una fase sola la scriva
> > sapendo questo.

⭐ **E qui si guadagna comunque una cosa che vale**: KWin consegna **58,9** fotogrammi al secondo
`[M]` senza che gli si debba rinegoziare niente, mentre su GNOME lo stesso risultato richiede una
cadenza che **il prodotto oggi non sa chiedere** (`DECISIONI.md` §2.5-bis). ⚠ È un guadagno sul
**ritmo**, non sul **ritardo**: sono due grandezze diverse, e `LEZIONI.md` §6.2 esiste perché sono
già state confuse.

**Si riusa**: `kwin.c` (822 righe), `appunti_wlr.c` (796).

⚠ Le trappole sono già scritte in `STUDI.md` §kde: `XDG_MENU_PREFIX` senza cui il cancello della cattura
non si apre; niente `InaccessiblePaths=` nel drop-in.

> ### ⛔⭐ E UNA TRAPPOLA È USCITA DAL PIANO IL 17 AGOSTO 2026 — `DECISIONI.md` §5.1-bis
>
> Qui c'era la terza: *«il ridimensionamento **nella forma della negoziazione**, con la guardia
> contro il ciclo infinito che non si vede su Trixie e compare il giorno dell'aggiornamento a
> 6.8»*. ⛔ **Non è più lavoro di questa fase**, perché non è più lavoro di nessuna: il
> ridimensionamento a caldo è uscito dal prodotto — *«non voglio mettere delle eccezioni nel
> progetto»* — ed è uscito **proprio per non avere un ramo KDE diverso da quello GNOME**.
>
> ⚠ **Quel che questa fase deve ancora fare, e che non è la stessa cosa**: rispondere
> `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` all'`ADATTA_TELA` che il client manda **all'attacco e al
> riattacco**, così che la pagina riscali e lo dichiari (§6.3). ⭐ E su KDE è il **caso normale**,
> non il ramo povero: KWin ≤ 6.7.4 prende la misura dalla riga di avvio (`--virtual --width W
> --height H`) e non la cambia più. Il percorso di codice esiste già ed è provato sull'ospite
> finto (caso 11 di `banchi/04-b31`).
>
> ⭐ **Il guadagno del taglio si vede qui**: la fase 11 non deve più portare una funzione, deve
> solo dichiarare un rifiuto — e la guardia contro il ciclo infinito di `kwin!7932`, che sarebbe
> stata un difetto invisibile su Trixie e vivo dopo l'aggiornamento, non ci riguarda più.

---

## Fase 13 — XFCE e LXQt

⚠ *Era la **fase 12** fino al 25 agosto 2026: **la rete di sicurezza** le è passata davanti
(`DECISIONI.md` §4.6-duodecies). **La fase non è cambiata di una riga** — è cambiato il suo
posto, come già il 16 agosto.*

⚠ *Era la **fase 11** fino al 16 agosto 2026 — stesso spostamento della 11, stessa ragione.*
⛔ **E qui una trappola di lettura**: `STUDI.md` §xfce e `STUDI.md` §lxqt portano in testa *«per la fase 11»*, ma
quella è **la fase 11 di v1** — sono studi dell'8 agosto 2026, scritti prima che questo piano
esistesse. ⇒ Il numero in quei due titoli **non è questo numero**, e non va inseguito.

**Produce**: il terzo e il quarto desktop, che condividono wlroots e quindi quasi tutto.

**Si riusa**: `appunti_wlr.c` già scritto per questa famiglia; le risposte alle quattordici domande
sono già in `STUDI.md` §xfce §12 e `STUDI.md` §lxqt.

---

## Fase 14 — Il servizio

⚠ *Era la **fase 13** fino al 25 agosto 2026, per lo stesso scalo.*

> ### ⛔⛔ E UNA COSA DA FARE QUI È GIÀ MISURATA — *25 agosto 2026*
>
> `[M]` **Fermare l'unità del server porta via TUTTE le sessioni degli utenti**, finestre
> comprese: la sessione grafica vive nel suo albero di processi (`KillMode=mixed`). ⇒ ⛔ **Oggi
> aggiornare il server significa buttare fuori tutti** — lo stesso danno che `DECISIONI.md` §4.7
> vieta a chiunque di provocare spegnendo la macchina.
>
> ⭐ `SPECIFICHE.md` §5.2 promette *«la sessione sopravvive al CLIENT»*, ed è vero e misurato.
> ⛔ *«Sopravvive al server»* **non era mai stato promesso, e non è vero.** ⇒ Il confine è ora
> tracciato lì, e **questa è la fase che lo deve spostare**: aggiornare senza fermare nessuno.
>
> ⚠ Il rilievo per intero: `fasi/10-multi-tenant-e-il-budget.md` **§7.5**.

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

> ### ⛔⭐ E qui si fa la pulizia: la funzione di banco non entra nel pacchetto — ✅ 11 agosto 2026
>
> *Decisione dell'utente, `DECISIONI.md` §7.16: «l'utente deve vedere il desktop senza artefatti,
> come se fosse davanti al monitor del PC … si tiene quello che serve per i test, ma poi nel
> prodotto finale si fa pulizia». ⚠ **Scritta qui, undici fasi prima di servire**, perché è la forma
> di decisione che si perde: vale alla fase 13 e viene decisa alla 1.*
>
> ⛔ **Il binario che si installa non contiene la funzione di banco di `RCP.md` §7.5** — i due tipi
> `BANCO_MARCA` e `BANCO_ESITO`. Non spenta: **assente**, non compilata, non raggiungibile.
>
> ⛔ **E si misura, o è una buona intenzione**: *«non c'è»* e *«c'è ed è spenta»* hanno lo stesso
> aspetto da fuori. Il banco di questa fase **cerca le marche dentro il binario del pacchetto** e
> pretende di **non** trovarle — con il controllo positivo che dice che lo strumento sa trovarle,
> cioè le stesse marche cercate nel binario **di prova**, dove ci sono. È la tecnica già scritta in
> `banchi/01-p1-prodotto.sh` della fase 1, che distingue un binario nuovo da uno vecchio con otto
> marche e due controlli.

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

---

# ⏳ PUNTO DI RIPRESA — 22 agosto 2026, **sera**

*La giornata del 22 agosto: **nove agenti in due ondate**, il coordinatore alla fusione e al
collaudo. ⭐⭐ **La fase 8 aperta e chiusa in un giorno**, sul giudizio dell'utente. E le fasi 6 e 7
restano senza nessun difetto vero aperto.*

## ⭐⭐⭐ Che cosa è cambiato per l'utente

> *«Il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»* · **«per me è ok»**
>
> *Al mattino, sulla stessa scena:* *«la distanza fra freccia e finestra è la metà della barra del titolo»*.

| | |
|---|---|
| l'anello **`input → vetro`** | **89,86 → 55,20 ms** (−39 %), **appaiato** — due giri che condividono tutto tranne il binario |
| il distacco, **nell'unità dell'utente** | **0,27 → 0,16 barre** ⇒ da **2,1** a **1,23 volte il locale** |
| ⭐ e il **locale** adesso è misurato | **0,142 barre** · 30,05 ms (n=254). ⇒ *«non identica: quello è impossibile»* è confermato dalla misura |
| ⭐⭐ **i fotogrammi DIPINTI** | **+9 %**. Non è una vittoria di cronometro |

## ⭐ Quel che è chiuso, e non si riapre

| | |
|---|---|
| **fasi 6 e 7** | ⭐ nessun difetto vero aperto |
| **fase 8** | ✅ **CHIUSA il 22 agosto**, `fasi/08-l-anello.md` |
| **fase 9** | ✅ **CHIUSA il 24 agosto**, `fasi/09-la-qualita-e-la-degradazione.md` — e le cinque cure sono **accese** |
| **`RCP.md` §5.2 e §6.2** | ✅ le due `[?]` chiuse con la misura: `EncSliceLP` **non** sa fare i sotto-livelli temporali · la chiave alla tela dell'utente sta allo **0,13 %** del tetto |
| **il «puntatore doppio»** | ✅ **non esiste** — smentito dall'occhio dell'utente, e l'agente fermato dopo pochi minuti |
| **i motori** | Linux Chrome ✅ · Linux Firefox ✅ · Windows Chrome ✅ · Android Chrome ✅ · ⛔ Android Firefox fuori · ⚠ **Firefox su Windows: NON PROVATO** |

## ⛔ E i quattro difetti veri trovati in fase 8 — **nessuno era il bersaglio**

la **chiave abbandonata** (§5.2 la vieta, ed era la spirale) · la **scala delle ricodifiche corta di
uno scalino** · il **passo non multiplo di 64** che dava un desktop **inclinato senza errori, coi
millisecondi già perfetti** · e il **cronometro del prodotto che misurava il banco**.

## ⛔⛔ Le tre lezioni nuove — `LEZIONI.md` §1.26 · §1.27 · §1.28

1. **Due banchi sulla stessa MACCHINA si falsano in silenzio.** §1.24 parlava di quel che si
   *ammazza*; questa di quel che **non** si ammazza — e non dà un rosso, dà **un numero plausibile**;
2. **Il colore medio è cieco**: un'immagine sbagliata a ogni riga ha **le stesse statistiche** di
   quella giusta. *Un controllo deve leggere una cosa che si può sbagliare, non una che si può mediare*;
3. ⭐⭐ **Due banchi che non concordano possono avere ragione tutti e due**: misurano due grandezze
   diverse. ⇒ **E l'occhio dell'utente aveva ragione**: i banchi guardavano un pezzo più corto
   dell'anello vero, e il pezzo mancante era invisibile **perché la loro mano è finta**.

## ⏳ I punti aperti — nessuno è un difetto

1. ⛔ **il muro di Mutter**: `[M]` **16,0 ms**, un quadro a 60 Hz esatto, **un sesto dell'anello** —
   non si è mosso di tre decimi in tutta la fase, e **non l'ha toccato nessuno**;
2. ⛔ **metà del guadagno della fase 8 non è spiegato**: 15,9 dei 34,7 ms stanno in un tratto che la
   copia zero **non attraversa**. `[?]` Ipotesi dichiarata, non misurata;
3. ⚠ **la ritenuta del `pw_buffer` è in vigore senza prova**: il controllo positivo non ha
   riprodotto il danno. Prudenza, non necessità;
4. `[?]` **il modello del distacco ha predetto male due volte, in versi opposti**. È un fatto sul
   modello, **non sull'utente**, ed è lavoro nostro;
5. **il datagram su rete non locale** e la **priorità del percorso audio** (`nice`);
6. **la misura `AV`** da riprendere con l'`aoff` curato — per accorgersi se il ritardo torna;
7. **il 4/18 del 16 agosto** non riprodotto: due cause escluse con la misura, resta una corsa da
   setacciare;
8. `[?]` **il desktop immortale** — letto nel codice, non misurato;
9. `[?]` **su DeX lo schermo risponde col monitor esterno o col telefono?** Serve il telefono dell'utente;
10. **Firefox su Windows**, mai provato;
11. ⚠ **il tetto dei 50 ms non è verificato**, e non perché manchi poco: **55,20 sta su un confine
    diverso**. I due numeri **non si confrontano** — §1.28 applicata a noi stessi.

## 🔸 Le decisioni che aspettano l'utente

- 🔸 **la tela multipla di 16** (`rcp_misura_ammessa()`): renderebbe la copia zero valida su **ogni**
  schermo, ⛔ ma è una **modifica al protocollo** — `RCP.md` §4.5 oggi pretende solo i lati pari;
- 🔸 **il `nice` a tutto il percorso audio**;
- 🔸 **si apre o no un difetto a monte in Mutter?** (fase 6 §7.1-bis) — azione verso l'esterno;
- 🔸 **il DeX** col suo telefono;
- 🔸 **`BANCO_MARCA`/`BANCO_ESITO`**: completare il ramo o togliere i due tipi;
- 🔸 ~~**al congedo il palco a misura di riposo?**~~ — **provvisoria**, si lascia com'è
  (`DECISIONI.md` §5.0-septies). *«Per il momento accetto, ma poi ci penserò su.»*

## ⚠ Pulizia da fare prima del prossimo giro

⛔ **Quattro server di prova degli agenti sono rimasti accesi** sulla macchina (porte **7746, 7752,
7765-67, 7775**), e girano da `root`. Non danno fastidio a riposo, ⚠ **ma falserebbero la prossima
misura** — che è precisamente l'errore di §1.26. **Vanno spenti prima di misurare.**

⭐ Vivi e voluti: **7730** (dell'utente) e **7790** (il prodotto con la fase 8 dentro, che l'utente
ha giudicato).

> ✅ **CHIUSA il 23 agosto 2026**: dopo il riavvio e la riprovisione la macchina aveva **una sola
> porta 7xxx aperta, la 7900** — verificato con `ss -tuln` **prima** di misurare.
> ⚠ E la regola che ne è uscita, pagata due volte nella giornata (`fasi/09` §3.17): fra due banchi
> sullo stesso utente **si verifica che il posto sia libero** — nessun cliente vivo **e** nessun
> palco — ⛔ **non si conta il tempo**. Un palco orfano non dà un rosso: dà **un numero plausibile**,
> e quel giorno stava per far accusare tre cure innocenti.

## Come si riparte

```
# il prodotto con la fase 8 dentro
ALBERO=/media/REMOTIX/src/08-prova-src LAV=/media/REMOTIX/tmp/08-prova \
  bash banchi/07-b41-accendi.sh --porta 7790 --hz 0

# il metro dell'utente: il distacco freccia↔finestra, in barre del titolo
python3 banchi/08-b67-elastico.py --certifica      # 13 guasti innestati su 13

# l'anello intero, e ⛔ VA IN ROSSO se la macchina non e' scarica
python3 banchi/04-b30-anello-input.py --certifica  # 57 su 57, 18 guasti su 18
```

⚠ **Due trappole che hanno morso oggi**: il posto della sessione è **uno** e quello di prima resta
attaccato una ventina di secondi · e ⛔ **non si misura in due sulla stessa macchina** (§1.26).
