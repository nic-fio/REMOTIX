# STUDI — il codice degli altri, letto prima di scrivere il nostro

*Cuciti in un documento solo il **16 agosto 2026**, per decisione dell'utente: erano otto file
sparsi nella radice del progetto. ⛔ **Non è un riassunto**: il testo è quello che era, riga per
riga, con i titoli abbassati di un livello per farli stare sotto ai capitoli. Nessuna misura, nessuna
marca e nessuna data sono state toccate.*

> ## ⛔ Che cos'è questo documento, e che cosa NON è
>
> **Non è documentazione di REMOTIX.** È lo studio del codice **di altri** — compositori, browser,
> prodotti che fanno il nostro stesso mestiere — fatto **prima** di scrivere il nostro, per non
> ripagare quello che qualcuno aveva già pagato.
>
> ⇒ Quel che REMOTIX **è** sta in `SPECIFICHE.md`; quel che **fa** in `PIANO.md`; quel che è stato
> **deciso** in `DECISIONI.md`; quel che è stato **pagato** in `LEZIONI.md`. Qui c'è solo materiale
> letto.
>
> ⚠ **E le date contano più che altrove.** Sei di questi otto studi sono del **7-9 agosto 2026**,
> cioè **prima che il piano di V2 esistesse** — sono stati scritti per **v1**. ⛔ Dove dicono *«per
> la fase 11»* o *«per la fase 10»* intendono **le fasi di v1**, non quelle di `PIANO.md`. Il
> riferimento è rimasto com'era scritto, ed è questa riga a dire come si legge.

## Come si trova una cosa qui dentro

Ogni capitolo tiene **la numerazione delle sezioni che aveva da file separato**. ⇒ Un rimando che
prima diceva §kde §3.3-bis adesso dice **`STUDI.md` §kde 3.3-bis**, e la sezione ha lo stesso
numero di prima: **le chiavi dei capitoli sono i nomi che avevano i file**.

| capitolo | che cosa studia | scritto il | righe |
|---|---|---|---|
| **§web** | il browser come client — W3C/WHATWG, Chromium, Gecko, WebKit, Guacamole, noVNC | 9 ago 2026 | 566 |
| **§gnome** | GNOME e Mutter — il primo desktop | 9 ago 2026 | 587 |
| **§kde** | KDE Plasma e KWin 6.3.6 — il secondo desktop | 7 ago 2026 | 2 213 |
| **§xfce** | XFCE, labwc e wlroots — il terzo | 8 ago 2026 | 857 |
| **§lxqt** | LXQt su Wayland — il quarto | 8 ago 2026 | 511 |
| **§cinnamon** | Cinnamon e Muffin 6.7.4 — il quinto | 9 ago 2026 | 321 |
| **§gnome-remote-desktop** | il prodotto di GNOME che fa il nostro mestiere | — | 1 018 |
| **§xpra** | XPRA — lo studio arrivato tardi, e lo dice da solo | 14 ago 2026 | 222 |

⚠ **Ogni capitolo porta la propria legenda delle marche** — `[R]` letto nel codice, `[M]` misurato,
`[?]` non verificato — perché ce l'aveva da file separato. **Sono otto copie quasi identiche e
concordano**: non ne è stata tolta nessuna, per la stessa ragione per cui non è stato tolto nient'altro.

⛔ **E una cosa che questo documento NON risolve**: gli studi sono **fotografie di una versione**.
§kde ha letto KWin **v6.3.6**, §cinnamon muffin **6.7.4**. Quel che dicono era vero di quel
tag — e il giorno dell'aggiornamento va riletto, non ricordato.


---

# Parte I — Il client


<a id="web"></a>

## Il browser come client — studio, per la fase 1

*Scritto il 9 agosto 2026, con quattro indagini parallele sulle specifiche W3C/WHATWG e sul codice
sorgente di Chromium, Gecko, WebKit, Guacamole, noVNC e Xpra. È il **sesto studio** del progetto, e
il primo che non parla di un compositore.*

> ### ⚠ Perché questo studio esiste
>
> Il 9 agosto 2026 l'utente ha deciso che **REMOTIX non avrà client dedicati**: il client è una
> pagina web (`DECISIONI.md` §1.6). Gli altri cinque studi rispondevano alla domanda *«questo
> desktop ci lascia lavorare?»*; questo risponde a *«il browser ci lascia lavorare?»*, ed è la
> stessa domanda rivolta a un componente che **non possiamo modificare, non possiamo scegliere e
> non possiamo interrogare**.
>
> ⭐ **Ed è il primo studio fatto prima di scrivere il codice invece che dopo** — che è
> precisamente il punto 1 della ricetta di `LEZIONI.md` §9.

> **Le marche:** **[R]** letto nel codice sorgente, con file e riga — non è una misura · **[S]**
> letto in una specifica o in una documentazione ufficiale, con l'URL · **[?]** dedotto o non
> verificato · **[M]** misurato da noi — ⛔ **in questo documento non compare mai**, e non è una
> dimenticanza: nessuno ha ancora acceso un browser.
>
> Il dettaglio sta nei quattro rapporti in `web/rapporti/`: **S1** certificato (920 righe), **S2**
> decodifica (730), **S3** tastiera e appunti (1.391), **S4** ritardo del disegno.
>
> ⭐ **E dalla notte del 10 agosto 2026 in quella cartella c'è un quinto file che non è uno studio**:
> `web/rapporti/S-esiti-sonda.md`, **gli esiti misurati** della sonda del browser — S7, S1b, S5 — con
> la scena accanto a ogni numero, i registri `.jsonl` a cui risalire, e ⛔ **la ricontata dell'11
> agosto che dichiara quali numeri hanno una provenienza su disco e quali no**. ⚠ È lì che il `[M]`
> di questo studio comincia a esistere; qui dentro continua a non comparire.

---

### 1. In due minuti

#### 1.1 ⭐ Le cinque cose che questo studio ha cambiato

| # | | |
|---|---|---|
| 1 | ⛔ **L'eccezione del certificato NON copre WebTransport** | né su Chrome né su Firefox `[R]`. Il predefinito «un clic e vai» che era stato proposto **non funziona**, e la strada diventa `serverCertificateHashes` — §3 |
| 2 | ⛔ **`prefer-hardware` non prova niente su Android** | Chromium sceglie **di proposito** un decodificatore HEVC software quando non ne trova uno hardware `[R]`. È la forma d'errore **E1**, cioè il muro di v1, **ricomparso un livello più in alto** — §4 |
| 3 | ⭐ **Si perde molto meno tastiera del temuto** | a schermo intero la lista riservata di Chrome scende da dodici comandi a **due** `[R]` — §5. ⚠ Ma quel che il **sistema operativo** si tiene non lo recupera nessun browser |
| 4 | ⭐ **La clipboard si può sorvegliare, da gennaio 2026** | `clipboardchange` è in Chrome 144, ed è stato motivato **esplicitamente dai client di desktop remoto** `[S]` — §5 |
| 5 | ⛔ **Il compositore del browser costa 25-42 ms a 60 Hz** | `[?]` 1,5-2,5 intervalli di quadro fra il disegno e il pixel acceso — **più di tutto il nostro tetto**. E nessuna API JavaScript lo vede — §6 |

#### 1.2 ⛔ E le quattro convergenze fra rapporti, che nessuno dei quattro poteva vedere da solo

Sono la ragione per cui questo documento esiste oltre ai quattro rapporti.

> ⚠ **E sono la parte più fragile, per costruzione**: nessuno dei due autori le ha validate.
> *Riviste il 9 agosto 2026 dalla revisione **R2** (`web/rapporti/R2-revisione-web.md`), che ne ha
> indebolita una, ridimensionata un'altra, aggiunte due che mancavano, e stabilito che una terza
> **non era dei rapporti**: era una mia tesi presentata come derivata.*

**A. I 10 bit hanno tre indizi contrari, e nessuno è una misura.**

| Da dove | Che cosa dice |
|---|---|
| `DECISIONI.md` §2.3-bis | sul percorso `mediacodec` di Android il supporto a 10 bit è limitato e **l'uscita torna a 8** `[S]` |
| **S2** | ⚠ `[S]` **non `[R]`, e non verificato**: che sui fotogrammi decodificati in hardware `VideoFrame.format` sia **null** viene da una discussione W3C di **gennaio 2023**, e S2 §3.7 dichiara di **non aver potuto stabilire lo stato di Chromium ad agosto 2026**. *Marca corretta da R2: era stata promossa a `[R]`* |
| **S4** | la condizione di zero-copy di WebGPU è letteralmente `format == PIXEL_FORMAT_NV12` `[R]`: **P010 non passa**. E il canvas 2D ha un aiutante che si chiama `DownShiftHighbitVideoFrame` `[R]` |

⚠ **Sono tre catene diverse** — il codec, l'API, il disegno — e R2 ha provato a farle collassare in
una sola senza riuscirci. ⛔ **Ma reggono su due gambe e mezza, non su tre**: l'indizio di mezzo è
una fonte di tre anni fa.

**Da cui, e la forma conta**: `DECISIONI.md` §2.2 — il desiderato a 10 bit, deciso dall'utente
l'8 agosto — **si segnala come da verificare**, e la verifica è la prima cosa che il banco della
fase 2 accerta. ⛔ Non si riscrive provvisoria su questa base: R2 ha ragione a dire che *«una
decisione dell'utente si sposta con tre indizi, non con due indizi e una fonte di tre anni fa
promossa di marca»* — ed è la stessa `LEZIONI.md` §2.3-quater che avevo citato a sostegno.

⚠ E la difficoltà si chiude su sé stessa: **dal browser i 10 bit non sono leggibili**, quindi la
prova finale è **guardare una sfumatura**, cioè `LEZIONI.md` §2.4 — il metro è quel che si vede.

**B. La PWA lega S1 e S3 — e vale meno di quanto avevo scritto.**

| | |
|---|---|
| **S1** | dietro un'eccezione di certificato, su Chrome **il Service Worker non si installa** `[R]` ⇒ niente PWA |
| **S3** | in una **PWA installata** la lista dei tasti riservati di Chrome è **vuota** `[R]` |

> ⛔ **Avevo concluso «compra la tastiera intera». È troppo forte, su quattro punti** *(R2)*:
>
> 1. la lista vuota è quella **del browser**, non del sistema: su macOS `⌘Spazio` e `⌘Tab`, su
>    Android e DeX **ogni combinazione con Meta**, restano perse su qualunque configurazione `[R]`;
> 2. il guadagno marginale è **piccolo**: a schermo intero le riservate di Chrome sono già solo due,
>    e una delle due — l'uscita — la **specifica obbliga** a riservarla. Fra «schermo intero + lock»
>    e «PWA» ballano `F11` e poco altro;
> 3. vale **solo su Chrome**: su Firefox restano le sei riservate, su Safari la PWA non c'entra;
> 4. ⛔ **e sull'uso primario è una `[?]`**: se valga anche per Chrome per Android non lo sa nessuno
>    — lo dichiara §5.5 di questo stesso documento, e in §1.2 l'avevo dato per acquisito.
>
> **Quel che resta vero**: il certificato vero toglie l'avviso **e** apre la strada della PWA, che
> su Chrome desktop recupera qualche scorciatoia in più. È un vantaggio, non una categoria diversa.

**C. ⛔ La forma della pagina è decisa da due vincoli che si scontrano** *(aggiunta da R2)*.

| Da dove | Il vincolo |
|---|---|
| **S3** | le lettere devono uscire da `beforeinput`, e questo obbliga la pagina ad avere **un elemento modificabile con il fuoco** — anche su desktop, non solo su Android. Senza, **accenti e tasti morti non si producono** `[R]` |
| **S4** | ⛔ **niente elementi sopra la tela**, o cadono il percorso overlay e il canvas desincronizzato `[S]` `[R]` |

**Il caso concreto**: si scrive la pagina con la sola tela, si arriva alla fase 4, si scopre che
`^`+`e` non produce `ê` su nessun motore, si aggiunge il campo nascosto sopra la tela — e **si
perde la strada di disegno su cui tutto §6 è costruito**. ⭐ È precisamente la riscrittura che §6.1
dice di voler evitare, e **la sintesi era l'unico posto dove si poteva vedere**.

**D. ⛔ La scheda in secondo piano si congela dopo cinque minuti** *(aggiunta da R2; era in S2 §3.8
e non l'avevo riportata)*.

Un gruppo di pagine viene **congelato** se resta nascosto e silenzioso per oltre **cinque minuti**,
e l'esenzione documentata richiede un canale WebRTC aperto o una traccia multimediale viva `[S]`.
⛔ **L'architettura di §6.1 — WebTransport e basta — non rientra nell'esenzione.** S2 la marca come
*«decisione di architettura da prendere adesso, non quando ci accorgeremo che la sessione muore
dopo cinque minuti»*.

⚠ **E tocca una promessa**: `SPECIFICHE.md` §5.3 dice che un client che tace 30 secondi **è
staccato**. Una scheda congelata tace — quindi il telefono in tasca si stacca da sé. Non è un
difetto (la sessione sopravvive, `DECISIONI.md` §4.1), **ma è un comportamento da dichiarare**, e
oggi non è scritto da nessuna parte.

**E una tesi mia, che va attribuita invece che spacciata per conclusione dei rapporti** *(R17)*:
`DECISIONI.md` §2.7 obbliga a dichiarare un ripiego, e S2 dimostra che da JavaScript la verità sul
decodificatore non è leggibile `[R]` — **da cui propongo** che la diagnosi viva **nel prodotto**,
perché il dispositivo dell'utente è l'unico posto dove la domanda ha risposta. ⚠ In S2
l'autodiagnosi compare **dentro un solo esito su cinque**, non come conclusione generale: la tesi è
difendibile, ma è mia, ed è la forma d'errore **E5** applicata al ragionamento invece che al dato.

---

### 2. La mappa

| Che cosa | Versione su cui è stato letto |
|---|---|
| **Chromium / Blink** | 151 |
| **Gecko / Firefox** | 151-153 |
| **WebKit / Safari** | 26.4 |
| WebTransport | Safari 26.4, **24 marzo 2026** — con essa ci sono tutti e tre i motori. ⚠ *La parola «Baseline» che questa riga portava non viene da nessuno dei quattro rapporti: era della ricerca del 9 agosto, ed è stata tolta perché è un termine tecnico con un significato preciso (R2)* |
| WebCodecs `VideoDecoder` | Chrome **94+** su tutte le piattaforme, **Android compreso** · Firefox 130+ · Safari 26+. ⚠ *La cifra «Chrome per Android 147» era una contaminazione fra due rapporti: 147 è la versione di un'altra cosa (R2)* |
| ⛔ **Firefox su Android** | `VideoDecoder` **assente in release** (solo Nightly), HEVC assente `[S]` ⇒ **non può essere un client**. Manca in tutto il resto di questo documento, che altrove tratta Firefox come uno dei tre motori serviti |
| Fullscreen Standard, `keyboardLock` | entrato nello standard WHATWG l'**8 maggio 2026** |
| `clipboardchange` | **Chrome 144**, 13 gennaio 2026 |
| I riferimenti letti | Guacamole, noVNC, Xpra html5, Selkies, moonlight-web |

⚠ **Questo capitolo invecchia più in fretta di tutti gli altri cinque.** I compositori si muovono a
cicli di sei mesi e Debian li congela; i browser si aggiornano da soli, sul dispositivo
dell'utente, e **due delle cinque cose più importanti di questo studio sono del 2026**. Chi rilegge
questo file fra sei mesi **rifaccia le ricerche prima di fidarsi**.

---

### 3. S1 — Il certificato: l'eccezione non copre la sessione

*Dettaglio: `web/rapporti/S1-certificato.md`.*

#### 3.1 La risposta, motore per motore

| | |
|---|---|
| **Chrome/Edge** | ⛔ **no**, e per due ragioni indipendenti. L'eccezione dell'utente vive nel processo browser e la consulta **un solo punto**, alimentato dagli errori delle richieste normali: il client WebTransport **non la interroga mai** `[R]` — assenza verificata **con controllo positivo** su un punto dove quel meccanismo invece c'è. E il QUIC di Chrome pretende una radice **incorporata nel browser**: `ERR_QUIC_CERT_ROOT_NOT_KNOWN` |
| **Firefox** | ⛔ **no**, per una ragione diversa: l'eccezione **viene** consultata anche su HTTP/3, e subito dopo la sessione si chiude se la radice non è incorporata `[R]`. L'unica deroga scritta nel codice è, testualmente, `serverCertificateHashes` |
| **Safari** | `[?]` **il caso aperto**: la sua eccezione non aggira niente, mette il certificato **nel portachiavi**, e WebTransport passa di lì. Potrebbe essere l'unico dove la risposta è sì. **Nessuno l'ha documentato** |

> ### ⛔ E Safari **ha** `serverCertificateHashes` — la correzione che avevo perso per strada
>
> *Rilievo R2, ed è il più caro dei diciassette perché era già passato in un documento di
> decisione.* WebKit l'ha implementato il **2 ottobre 2025** (bug 300057, `RESOLVED FIXED`),
> l'implementazione sta in `NetworkTransportSessionCocoa.mm` `[R]`, ed è spedita in **Safari 26.4**.
>
> ⛔ Il rapporto S1 dedicava un riquadro apposta a correggere l'affermazione contraria — *«vera nel
> 2024, ripetuta nel 2026»* — e io **non l'ho riportata**, scrivendo invece in `DECISIONI.md` §1.7
> che *«WebKit non implementa `serverCertificateHashes`»*. Corretto lì lo stesso giorno.
>
> **Le due conseguenze:**
>
> 1. ⭐ **iPhone e iPad hanno già una strada senza dominio**, ed è **la stessa** degli altri due
>    motori. Non è una piattaforma da salvare: è una piattaforma servita;
> 2. la misura **S1a** perde il primo posto. Non decide più *«se iPhone ha una strada»* — decide
>    **una comodità**: se su Safari l'eccezione basti da sola, cioè se lì si possa fare a meno di
>    pubblicare l'impronta. S1 §5.8 lo scrive: l'impronta si usa **sempre**, e un'eventuale
>    tolleranza di Safari sarebbe **un ripiego in più, non un percorso diverso**.

⛔ **E questo chiude, con una ragione tecnica dura, la proposta di far installare un'autorità
nostra** (`DECISIONI.md` §1.7): su Chrome **non basta nemmeno il magazzino di sistema**, perché
quella radice non è *incorporata nel browser*.

#### 3.2 Che cosa se ne è ricavato

| | |
|---|---|
| **la strada** | `serverCertificateHashes`, promosso da rete di sicurezza a **strada normale** (`RCP.md` §4.1-bis) — ⭐ **e vale su tutti e tre i motori**, Safari 26.4 compreso |
| ⛔ **due certificati, non uno** | uno **longevo** per la pagina — è quello su cui vive l'eccezione dell'utente — e uno **breve, ≤14 giorni**, per la sessione, che ruota da sé. ⚠ Confonderli fa ricomparire l'avviso ogni due settimane |
| ⛔ **e l'avviso torna comunque ogni sette giorni** | `[R]` `kCertErrorBypassExpirationInSeconds = 604800`, con il commento *«Certificate error bypasses are remembered for one week»*. ⚠ *Questa riga mancava, e con essa la conseguenza: **anche tenendo il certificato della pagina fermo, su Chrome il clic si rifà ogni settimana**. Cambia la frase che si dice all'utente (R2)* |
| ⭐ **una cosa che cade e semplifica** | `Alt-Svc` **non c'entra**: WebTransport apre la sua connessione da sé `[S]`. Il ripiego silenzioso su TCP che era stato dichiarato come pericolo **non può accadere** |
| ⛔ **il prezzo dell'eccezione** | dietro di essa, su Chrome, **il Service Worker non si installa** `[R]` — e vedi §1.2 B |
| ⏳ **due cose che S1 lascia da decidere, e che avevo taciuto** | **(1)** Safari è l'unico motore con WebTransport anche su **HTTP/2 e TCP**: il nostro server non lo parla, quindi il suo ripiego finirebbe in errore — *va deciso* se implementarlo o dichiarare Safari fuori dal ripiego. **(2)** una pagina già aperta ha in mano **un'impronta che invecchia**: alla riconnessione dopo la rotazione va ricaricata o va richiesta l'impronta corrente — *va deciso dove sta questo aggiornamento in `RCP.md`* |

#### 3.3 Il banco

⛔ **Il controllo positivo che avevo scritto era cieco, ed è il rilievo più grave della revisione**
(R2, rilievo R1). Diceva: *«la stessa prova su Chrome deve fallire»*. Con **la porta UDP 7447
chiusa nel firewall**, la prova fallisce su Safari *e* fallisce su Chrome — cioè **il controllo è
verde** — e il banco conclude «l'eccezione di Safari non copre», che è la conclusione sbagliata su
un dato mancante. È «vuoto» e «proibito» con lo stesso aspetto (`LEZIONI.md` §1.9), messo al primo
posto del progetto.

**Il controllo giusto, che S1 aveva scritto e che avevo sostituito**: sullo **stesso browser**,
sulla **stessa pagina**, nello **stesso giro** — si prova l'eccezione da sola *e* si prova la
connessione con l'impronta pubblicata. La seconda **deve riuscire**: se fallisce anche quella, non
si sta misurando l'eccezione, **si sta misurando un server che non risponde**.

> #### ⛔ E i controlli sono tre, non uno — la cura era rimasta a metà
>
> *Aggiunti la notte del 9 agosto 2026, rilievo **R3.1** della revisione del banco della fase 1.
> La cura del rilievo R1 aveva rimesso il controllo che dice **sì** (P2) e non quelli che dicono
> **no** — ed è la stessa forma, un livello più in basso.*
>
> | | |
> |---|---|
> | **P2** | la connessione con **l'impronta pubblicata** deve **riuscire** |
> | ⛔ **P3** | la connessione con l'impronta **sbagliata di un byte** deve **fallire** |
> | ⛔ **P4** | un certificato rigenerato a **30 giorni**, con la sua impronta giusta, deve fallire **per durata** |
>
> S1 §4.4, testualmente: *«**solo con P2 verde e P3 rosso** il risultato di P1 significa
> qualcosa»*, e su P3: *«**se riesce, il banco non distingue nulla**»*.
>
> ⛔ **Il caso concreto che chiude solo P3**: una pagina che considera «riuscita» la costruzione
> dell'oggetto `WebTransport` invece di attendere `ready` — o che guarda la promessa sbagliata —
> fa riuscire **anche** la prova con l'impronta storpiata. Il banco scrive `[M]` *«su Safari
> l'eccezione copre WebTransport»*, che è un `[M]` **falso** contro due `[R]` letti nel codice di
> Chromium e di Gecko. P2 da solo non lo vede: è verde in tutti e due i mondi.

⚠ **E la misura ha perso il primo posto**: con Safari che ha `serverCertificateHashes` (§3.1), S1a
non decide più se una piattaforma è servibile — decide se lì l'impronta si possa risparmiare.

---

### 4. S2 — La decodifica: la trappola di v1 travestita da API

*Dettaglio: `web/rapporti/S2-decodifica.md`.*

#### 4.1 ⛔ Il fatto che conta più di tutti

| | |
|---|---|
| **su desktop** | `hardwareAcceleration: "prefer-hardware"` è una prova vera: il broker **butta via del tutto** la fabbrica dei decodificatori software `[R]` |
| ⛔ **su Android no** | quando non trova un decodificatore HEVC hardware, Chromium ne sceglie **di proposito** uno software di MediaCodec `[R]`, perché non ne impacchetta uno suo |

**Da cui**: `prefer-hardware` riuscito, `powerEfficient: true` e fotogrammi corretti sono **tutti
compatibili con la CPU**. È la forma d'errore **E1** — necessario preso per sufficiente — cioè
esattamente ciò che ha ucciso v1.

⭐ **E l'indagine non si è fermata al «non l'ho trovato»**: il dato **esiste** dentro Chromium
(`IsPlatformDecoder()`) e **non compare in nessuna interfaccia JavaScript** `[R]`. Non è una
ricerca finita male: è un fatto.

#### 4.2 Il supporto, e il formato del flusso

| | |
|---|---|
| **HEVC Main10 in WebCodecs** | Chrome per Android da **108.0.5343.0** · Chrome su Linux solo via VA-API da **108.0.5354.0** · Safari da 16.4 (solo video) e pieno da **26.0** `[S]` |
| copertura di campo 2026 | ≈ **85 %** in decodifica Main10 — ⚠ e l'autore del dato dichiara che **non distingue hardware da software** |
| ⭐ **il formato del flusso** | **Annex-B senza `description`**: è legale, è **quel che `hevc_vaapi` già produce**, e in Chromium **risparmia un'allocazione e una copia per fotogramma** `[R]`. Tre progetti su tre fanno così; moonlight-web prova Annex-B **per primo** proprio su HEVC |
| ⚠ la trappola dell'hvcC | Chromium riparsa l'SPS e **rifiuta la configurazione** se i byte di prevenzione dell'emulazione cadono nel campo sbagliato `[R]` — un motivo in più per non prendere quella strada |

⭐ **La strada pigra è anche quella giusta**, ed è raro: non si scrive un impacchettatore, non si
converte niente, e si risparmia una copia.

#### 4.3 Il banco

Un decodificatore software **supera le prime cinque prove** e cade solo su tre:

| | |
|---|---|
| **portata a saturazione** | 4K60 Main10, e si guarda dove si ferma |
| **una canarina di CPU** | un lavoro noto dentro un worker, che rallenta se la CPU sta decodificando |
| **il decadimento su dieci minuti** | il silicio tiene, la CPU scalda e cala |
| ⛔ **controllo A** | VP9 forzato **in software** — software per costruzione. Se il banco non lo dichiara tale, il suo verdetto su HEVC va buttato |
| ⛔ **controllo B** | ⭐ VP9 in **`prefer-hardware`** — **deve essere dichiarato hardware**. *Mancava, ed è quello che dice **no**: senza, una soglia tarata larga fa passare per hardware l'HEVC **software di MediaCodec**, cioè proprio quel che Chromium sceglie di proposito su Android (§4.1). S2 §4.4: «il banco è valido se, sullo stesso telefono, dichiara **software** il controllo A **e hardware** il controllo B. Finché non lo fa, **non pubblica verdetti**». Ripristinato dal rilievo **R3.1***, 9 ago |
| ⭐ **controllo C** | **`is_software_codec` letto via `chrome://inspect`**, in parallelo alle prove indirette. ⛔ Il dato **esiste** in `media_codec_video_decoder.cc`, col nome che arriva da `MediaCodec.getName()`: *«il browser sa e non risponde»* è vero **da JavaScript**, e il banco non è JavaScript. Rinunciarci sull'uso primario era una scelta non dichiarata (**R3.13**) |
| ⛔ **e gli esiti sono TRE** | ≥ 90 fps ⇒ hardware · ≤ 30 ⇒ software · **in mezzo: verdetto sospeso**. Un banco a due uscite promuove la banda incerta a certezza |

⚠ **E questo banco non resta in laboratorio** (§1.2 C): la stessa misura, ridotta, vive **nel
prodotto**, perché il dispositivo dell'utente è l'unico posto dove la domanda ha risposta.

---

### 5. S3 — Tastiera e appunti: il 2026 ha ribaltato le premesse

*Dettaglio: `web/rapporti/S3-tastiera-appunti.md` — 96 `[R]`, 103 `[S]`, 23 `[?]`, zero `[M]`.*

#### 5.1 ⛔ Una riga di `SPECIFICHE.md` §7.3-bis era sbagliata, e l'ho scritta io

Diceva: *«la Keyboard Lock esiste solo su Chrome ed Edge, e solo a schermo intero»*, e che
`Ctrl+W`, `F11` e `Ctrl+Shift+I` sono perduti. **Falso su tre punti:**

| | |
|---|---|
| **non è più solo Chrome** | `requestFullscreen({keyboardLock:"browser"})` è entrato nel Fullscreen Standard WHATWG l'**8 maggio 2026**, e l'hanno spedito **Safari 26.4** e **Firefox 151** `[S]`. Chrome/Edge restano sulla vecchia `navigator.keyboard.lock()`: ⚠ **la pagina deve saperle entrambe** |
| **si perde molto meno** | la lista riservata di Chrome è di **dodici** comandi; **a schermo intero scende a due** — `F11` e l'uscita — **senza chiamare nessuna API** `[R]`. Firefox ne ha **sei**, Safari **zero** (ma filtra a schermo intero, e ⭐ **questo spiega il vecchio commento di noVNC su Safari**) |
| ⭐ **in una PWA installata è vuota** | `// In Apps mode, no keys are reserved` `[R]` |

#### 5.2 Quel che si perde davvero

| | |
|---|---|
| `Ctrl+Alt+Canc` | ovunque, e non è recuperabile |
| l'uscita da schermo intero | per costruzione: è la via di fuga dell'utente |
| ⛔ **su macOS, tutte le scorciatoie di sistema** | non esiste un aggancio — la funzione che dovrebbe fornirlo **restituisce `nullptr`** `[R]`, e il controllo di sistema precede la lock |
| ⛔ **su Android e DeX, qualunque combinazione con Meta** | per regola AOSP — ⚠ e **DeX è l'uso primario dichiarato** (`DECISIONI.md` §5-bis.0) |

#### 5.3 Gli appunti: l'ipotesi «non si può sorvegliare» è superata

| | |
|---|---|
| ⭐ `clipboardchange` | **Chrome 144, 13 gennaio 2026** — e la motivazione scritta nella proposta sono **i client di desktop remoto** `[S]`. Porta solo i tipi MIME, vuole il fuoco |
| ⛔ **non esiste su Firefox e Safari** | verificato, non dedotto. Là ogni lettura costa il menu «Incolla» con **un secondo di attesa** |

#### 5.4 ⭐ Tre regali dalla lettura del codice altrui

1. ⛔ **La cura del modificatore rimasto giù**, che per noi è il difetto più grave perché **la
   sessione sopravvive alla connessione**: Guacamole risincronizza lo stato dei modificatori
   **dagli eventi del mouse** `[R]`. Non c'è altro modo, e nessuno l'avrebbe inventato;
2. la tabella `KeyboardEvent.code` → **evdev** di Chromium, canonica e **senza buchi da 1 a 94**
   `[R]` — cioè la conversione che `RCP.md` §7.3 richiede, già scritta e verificabile;
3. la corsa fra `Ctrl+V` e la lettura degli appunti, che **tutti e tre** i riferimenti disinnescano
   a mano — Xpra ritarda **ogni battuta di 100 ms** `[R]`. ⚠ Per noi 100 ms sono **due volte il
   tetto del ritardo**: quella cura non si copia, si sostituisce.

#### 5.5 Le due `[?]` che contano di più

Entrambe su DeX, che è l'uso primario: **se la lock funzioni su DeX** (esiste solo da Android 16
QPR1) e **se la PWA valga anche su Chrome per Android**.

---

### 6. S4 — Il ritardo del disegno

*Dettaglio: `web/rapporti/S4-ritardo-disegno.md`.*

#### 6.1 La strada — ⛔ **non più una prescrizione: una decisione misurata** *(13 agosto 2026)*

*⛔ Questo paragrafo era scritto prima di qualunque riga di pagina, e prescriveva. Alla fase 3 è
stato **attuato e misurato**, e la misura ha diviso la prescrizione in due metà con esiti opposti.
Il testo originale è tenuto qui sotto perché la parte che regge è ancora quella.*

`drawImage(videoFrame)` **dentro la callback del decodificatore** — ⛔ **non** su
`requestAnimationFrame`. Zero copie in CPU se il fotogramma è NV12 a 8 bit; una conversione di
colore in GPU `[R]`. È anche l'unica che funziona su tutti e tre i motori.

| la prescrizione diceva | esito `[M]` 13 agosto |
|---|---|
| ⭐ dipingere **dentro la callback del decodificatore**, non su `requestAnimationFrame` | ✅ **regge, ed è la metà che vale** |
| ⭐ la **decodifica** fuori dal thread principale | ✅ **VALE, ed è misurato**: `[M]` **−3,44 ms** (7,17 → 3,73) |
| ⛔ la **tela** fuori dal thread principale | ⛔⛔ **AFFONDA IL CONTO**: `[M]` **+17,6 ms** sul disegno, più **+10,2** sulla consegna dello stream |
| il canvas 2D **desincronizzato** | ⚠ **non è mai stato acceso nel prodotto**: `src/pagina.html:407` ha `desynchronized` **spento** `[R]`, e la strada per accenderlo (`?tela=desincronizzata`) **non esiste** — non è un interruttore spento, è un interruttore che non c'è. ⇒ Non è una prescrizione respinta: è una prescrizione **mai eseguita**, e il guadagno resta `[?]` |

> #### ⛔⛔ Il worker: attuato, misurato — e **sbagliato A METÀ, non per intero**
>
> *`[M]` stessa macchina, stessa sessione, **stessa pagina** (cambia solo l'interruttore), stesso
> strumento rigirato per il «prima» e per il «dopo». Due giri di «prima», per sapere quanto vale il
> rumore: **5,9 ms**, e l'effetto lo supera di **cinque volte**. Errore d'orologio ±0,63-0,65 ms.*
>
> | ritardo disegno → vetro | n | p05 | **mediana** | p95 | p99 |
> |---|---|---|---|---|---|
> | PRIMA-A (thread principale) | 432 | 58,85 | **73,66** | 99,53 | 218,46 |
> | PRIMA-B (ripetuto) | 492 | 53,93 | **67,79** | 88,51 | 98,16 |
> | ⛔ **DOPO (worker)** | 483 | 84,48 | ⛔ **101,30** | 126,13 | 157,82 |
>
> ⇒ **+27,6 / +33,5 ms di mediana.** ⛔ Ma il totale nasconde la cosa che serve, e la scomposizione
> la mostra:
>
> | tratto (mediana, ms) | PRIMA-A | PRIMA-B | DOPO | Δ |
> |---|---|---|---|---|
> | stream completo → `decode()` | 0,07 | 0,06 | **10,23** | ⛔ **+10,2** |
> | ⭐ **la decodifica** | **7,17** | 6,13 | ⭐ **3,73** | ⭐ **−3,44 / −2,40** |
> | richiamo → disegno finito (`drawImage` ×2) | 9,63 | 9,11 | **27,19** | ⛔ **+17,6** |
> | **somma dei tre** | 16,87 | 15,30 | **41,15** | **+24,3 / +25,9** |
>
> ⭐⭐ **⇒ §6.1 non è sbagliata per intero: è sbagliata a metà. Vale la DECODIFICA, non la TELA.**
> Il decodificatore **consegna prima quando non contende** — `[M]` **−3,44 ms**, ed è un guadagno
> vero, non un arrotondamento. È la **tela** che affonda il conto, e da sola vale **+17,6**.
> ⇒ ⛔ **La riga utilizzabile non è *«il worker è sbagliato»***, che sarebbe solo una porta chiusa:
> è ***«la decodifica sì, la tela no»***, che dice a chi verrà dove mettere il confine.
>
> #### E i fotogrammi dipinti, obbligatori accanto (`LEZIONI.md` §6.2)
>
> | | catena vera (P7) | saturazione 1080p | saturazione 480p |
> |---|---|---|---|
> | thread principale | 22,8-24,2 /s | **127,6** /s | **230,6** /s |
> | worker | **26,3** /s | **33,9** /s (−73,4 %) | **56,4** /s (−75,5 %) |
>
> ⚠⚠ **Le due grandezze dicono cose OPPOSTE**: sulla catena vera il worker dipinge **di più** (è la
> coda), ma a saturazione il tetto **crolla di tre quarti**. Chi ne guardasse una sola leggerebbe
> metà del fatto — e **quale metà dipende da quale grandezza ha scelto per prima**.
>
> #### ⭐⭐ Il meccanismo, ed è la scoperta che cambia una REGOLA
>
> Costo extra per fotogramma **13,4 ms a 480p** e **21,7 ms a 1080p**; e a 480p il worker si ferma a
> **56,4 dipinti/s ≈ il quadro dei 60 Hz**, mentre il thread principale ne fa **230,6**.
> ⇒ ⛔ **`transferControlToOffscreen` impegna la tela al ritmo del quadro: è un
> `requestAnimationFrame` implicito.** Il worker prescritto da questo paragrafo reintroduce **in
> silenzio** proprio il salto di quadro che il paragrafo vieta a voce alta.
> ⛔⛔ **La prescrizione conteneva la propria smentita, e nessuna rilettura del documento poteva
> accorgersene senza misurarla.**
>
> ⇒ ⛔ **Il divieto si estende AL MECCANISMO, non alla parola.** Non basta «non chiamare
> `requestAnimationFrame`»: **qualunque strada che consegni al ritmo del quadro è vietata allo
> stesso modo**, e chi la prende paga il quadro senza averlo mai nominato.
>
> #### ⏳ `[?]` E questo va letto ACCANTO ai numeri, non in fondo
>
> ⛔⛔ **Tutto è misurato su Xvfb, in software, SENZA GPU**, e la penale è in gran parte
> **sincronizzazione al quadro**. ⇒ **Su hardware vero il conto va rifatto PRIMA di seppellire
> §6.1**: questi numeri chiudono la strada per oggi, **non per sempre**.
> ⏳ `[?]` E un `WebTransport` aperto **dentro** il worker toglierebbe i **+10,2** del tratto della
> consegna, ⛔ **non** i **+17,6** del disegno — che sono quelli che decidono.
>
> ⇒ ⭐ **Il codice resta in albero dietro `#video=worker`, SPENTO**, proprio perché il giorno della
> GPU vera il numero si rifà senza riscrivere niente (`DECISIONI.md` §2.8).
> ⚠ **E l'interruttore legge il FRAMMENTO, non la stringa di ricerca**, ed è una conseguenza di un
> difetto: `?video=worker` prende **404** (`src/pagina.c:243`). La sintassi col `?` tornerà valida
> quando quel difetto sarà curato.

⚠ *La riga «e impone la forma della pagina: il video vive nel worker, l'input nel thread
principale» **cade con il worker**: oggi video e input stanno tutti e due nel thread principale, e
il confine che questo paragrafo diceva di dover decidere subito non esiste più. ⛔ Se il worker
tornasse, torna anche quel confine — ma dovrà tornare con una misura nuova, non con questa riga.*

#### 6.2 Il pezzo che non è nostro e si sente lo stesso

`[?]` Fra il disegno e il pixel acceso passano **1,5-2,5 intervalli di quadro: 16-40 ms a 60 Hz**,
cioè **quanto tutto il nostro tetto**. Il tetto «solo per il pezzo che è nostro» resta legittimo
(`DECISIONI.md` §2.4), ma **quella riga va scritta accanto al tetto** o si promette una cosa e
l'utente ne sente un'altra.

⭐ **La leva, se servisse**: Selkies e moonlight-web non dipingono su canvas — mandano i fotogrammi
a un elemento `<video>` per prendere il percorso **overlay**, che salta il compositore `[R]`. Va
sotto un interruttore spento, non scritta per prima. ⚠ Xpra e noVNC restano sul canvas, e **nessuno
dei due dichiara un numero di ritardo**.

> ⛔⛔ **E su Xvfb questo pezzo cieco NON ESISTE** — *13 agosto 2026, e vale per ogni banco browser
> del progetto.* I 16-40 ms sono il tempo fra il disegno e il **pixel acceso su uno schermo**. Su
> Xvfb non c'è schermo, non c'è scanout, e **`requestAnimationFrame` non gira mai**: `[M]` **0
> quadri in 3 secondi**, con e senza GPU, con `visibilityState` a «visible».
> ⇒ ⛔ **La stima 16-40 ms si dichiara accanto ai numeri destinati all'utente, e NON accanto ai
> numeri del banco.** Sommarla a una misura presa su Xvfb gonfia il totale di un pezzo che lì non
> c'è; toglierla da un numero che si promette all'utente lo sgonfia dello stesso pezzo. È lo stesso
> numero, e i due errori hanno segno opposto.

#### 6.3 Il banco, e il suo pezzo cieco

L'anello di `DECISIONI.md` §2.6 si costruisce così: `t0` prima di spedire, `t1` come **prima riga**
della callback del decodificatore, poi si disegna, e **solo dopo** si legge la marca con una
lettura di 16×16 pixel. ⛔ **Quell'ordine è vincolante**: leggere prima sarebbe un ritorno dalla
GPU, e falserebbe la misura che sta prendendo.

| | |
|---|---|
| ⛔ **P1, il controllo decisivo** | il server ritarda di **N millisecondi noti**, e la mediana **deve salire di esattamente N**. Un banco che non lo fa non sa di misurare |
| ⛔ **P2 e P3, e P3 era caduto** | **P2**: il rilevatore trova il colore **che c'è**. ⛔ **P3**: **non** trova quello che **non c'è**. *S4 §4.2: «se dice sempre sì, si sta misurando zero e si è felici a torto» — e un rilevatore che dice sempre «ho visto la marca» **passa anche P1**, perché i N ms si sommano identici. Ripristinato dal rilievo **R3.1***, 9 ago |
| ⛔ **P5, il fuori ordine** | i fotogrammi arrivano su stream indipendenti: un anello che non lo regge misura la coda invece del ritardo. ⛔ **13 agosto: P5 NON È STATO ESEGUITO, e adesso lo dice.** Dopo tre iniettori `scavalcati = 0` — e *«zero fuori ordine»* non è «l'anello regge», è **«il fenomeno non si è presentato»** (`LEZIONI.md` §1.9). Prima il banco lo dichiarava **verde** |
| ⭐ **P5 — e la causa del fuori ordine è misurata** | ⛔ **non nasce (solo) dalla rete: nasce dalla DIMENSIONE del fotogramma.** `stream_video` scatta al **completamento** dello stream ⇒ l'ordine d'arrivo è **l'ordine delle dimensioni**, non quello di partenza, e **una chiave grossa viene scavalcata dai delta** che le partono dietro. ⚠ E il conto lo paga il protocollo: uno scavalcamento **costa una chiave** (`RCP.md` §5.2, §6.2 — «la regola dell'ordine si applica prima di quella della misura»). ⇒ Un iniettore che ritarda i pacchetti non riproduce il fenomeno: **lo riproduce chi cambia le dimensioni** |
| ⛔ **P6, la grana dell'orologio** | senza le due intestazioni di isolamento fra origini, su Firefox e Safari i cronometri cadono su una griglia da **1 ms** — su un tetto di **50**. ⚠ E `SPECIFICHE.md` §11.5 ne fa un **vincolo di prodotto**, non una taratura del banco (O11) |
| ⛔ **P7, il ritmo come controllo del percorso** | il ritmo consegnato dice se si sta misurando la strada che si crede |
| ⛔ **dove finisce la misura** | ⛔ **al disegno finito, non al richiamo del decodificatore.** *Corretto il 13 agosto 2026: la prima stesura chiudeva al richiamo, regalandosi **~11 ms** nostri e misurabili su un tetto di 50. Il numero è salito da **63,8 a 74,6** e lo si è lasciato salire.* ⇒ Il confine si sposta **nella direzione scomoda**, o il metro lavora per chi lo tiene |
| ⛔ **il pezzo cieco** | la misura finisce al disegno; il pixel si accende `[?]` 16-40 ms dopo, e **nessuna API JavaScript lo vede**. Si stima, e **la stima si dichiara accanto a ogni numero** invece di far finta che il numero sia il totale. ⛔⛔ **Ma su Xvfb quel pezzo NON esiste** (§6.2): la stima vale per lo schermo dell'utente, **non per il banco** |
| ⚠ **e una misura singola non vale nulla** | si lavora **a distribuzioni**, non a campioni |

---

### 7. Il piano delle misure

Nell'ordine, e ciascuna col suo controllo positivo. **Nessuna richiede una riga di prodotto.**

| # | La misura | Perché prima o dopo |
|---|---|---|
| **S1a** | l'eccezione su **Safari** lascia passare WebTransport? (macOS e iOS separati) | ⛔ **la prima**: decide se iPhone e iPad hanno una strada senza dominio |
| **S1b** | quanto dura l'eccezione su Chrome | cambia la frase che si dice all'utente: «una volta» o «una volta a settimana» |
| **S2** | HEVC Main10 in hardware **sul telefono vero** — saturazione, canarina, decadimento | decide che cosa la pagina dichiara, non se il progetto esiste (`DECISIONI.md` §2.7) |
| **S3a** | la Keyboard Lock su **DeX** | è l'uso primario, ed è una `[?]` |
| **S3b** | la PWA su Chrome per Android | vale la tastiera intera (§1.2 B) |
| **S4** | l'anello del ritardo, con il ritardo noto come controllo | dà il numero, e **la misura del pezzo cieco** |

> ⛔ **E tre etichette della sonda NON sono nate qui**, contro quel che `FASI.md` §01-filo-nudo
> dichiarava: **S5** (la tela che il client dichiara), **S6** (il carico utile di un datagram) e
> **S7** (il segno della rotella) non compaiono in **nessuna riga** di questo documento — `[M]` 11
> agosto 2026, `grep -cE '\bS5\b|\bS6\b|\bS7\b' web.md` → **0**, con il controllo positivo accanto
> (le sei etichette della tabella qui sopra compaiono **24** volte). Sono nate nel documento della
> fase 1, dalle domande di `SPECIFICHE.md` §6.1-bis, `RCP.md` §5.3 e `RCP.md` §7.3, e **rimandano
> lì**. ⚠ *Scritto qui l'11 agosto 2026, rilievo **R12C.10**: la frase sbagliata era quella che
> stabilisce la convenzione dei rimandi, e chi cercava la procedura di S5, S6 o S7 in questo §7 non
> l'avrebbe trovata.*
>
> ⭐ **E gli esiti di quel che è stato eseguito stanno in `web/rapporti/S-esiti-sonda.md`** — il
> quinto file di quella cartella, che non è un rapporto di studio ma **l'unico che porta numeri
> misurati**: S7 completa, S1b avviata, S5 a metà, e la ricontata che dice quali numeri hanno una
> provenienza su disco.

⛔ **E tutte sul dispositivo vero.** «Il Chrome del portatile lo fa» non dice niente del Chrome del
telefono: è la forma d'errore **E10** con un travestimento nuovo (`DECISIONI.md` §5-bis.0-ter).

---

### 8. ⏳ Quel che questo studio NON sa

*Elencato perché non venga riscoperto come chiuso. Ogni rapporto ha la sua lista; queste sono le
voci che toccano una decisione.*

| | |
|---|---|
| `[?]` Safari e WebTransport dietro eccezione | §3.1 — **e Apple non documenta nemmeno se l'eccezione si possa concedere su iOS** |
| ⏳ ~~`[?]` la durata dell'eccezione su Chrome~~ — **la misura è AVVIATA** | ⛔ **non era `[?]`, e questo documento si contraddiceva**: §3.2 la dà `[R]` da `kCertErrorBypassExpirationInSeconds = 604800`, cioè **sette giorni**. *Corretto la notte del 9 agosto 2026, rilievo **R4.14**: chi leggeva §8 pianificava una misura per **sapere** il numero, chi leggeva §3.2 per **confermarlo**, e a un banco che deve aspettare una settimana la differenza cambia la soglia di pazienza.* Restava da misurare **quanto quel `[R]` regga sul campo** — ⭐ **e la misura è in moto dal 10 agosto 2026, 21:10:01 UTC**, su **Chrome 151.0.7922.108** con un profilo persistente: `banchi/01-s1b-eccezione.sh`, registro `banchi/01-s1b-stato.jsonl`, esiti in `web/rapporti/S-esiti-sonda.md` §2. ⭐ **E l'11 agosto 2026 la misura ha risposto, senza aspettare il verdetto del 17**: `01-s1b-eccezione.sh scavalca`, **6 controlli su 6**. ⚠ L'obiezione scritta qui sopra era giusta — *«la contabilità di Chrome non è il comportamento»* — ed è **proprio quella** che il giro nuovo chiude: su una **copia** del profilo la scadenza è stata riscritta **a ieri**, e la pagina **non si apre più**; riscritta a **+30 giorni** (stessa manomissione, segno opposto) si apre ancora. ⇒ Chrome **onora** l'istante che si segna. E la scadenza riletta **dopo una visita** è identica: **non si rinnova** — la domanda che l'orologio dei sette giorni non poteva porre, perché la pagina la visita tutti i giorni. ⇒ **All'utente si dice «una volta a settimana»**. ⏳ Il 17-18 agosto resta come conferma indipendente: il profilo vero non è stato toccato |
| `[?]` i 10 bit fino allo schermo | §1.2 A — e **non è verificabile da JavaScript** |
| `[?]` la Keyboard Lock su DeX, e la PWA su Android | §5.5 |
| ⛔ ~~`[?]` i 16-40 ms del compositore~~ — **resta aperta, ma NON dove si credeva** | §6.2 — nessuna API li espone, e questo non è cambiato. ⛔ **Quel che è cambiato è dove valgono**: `[M]` 13 agosto, **su Xvfb `requestAnimationFrame` non gira mai** — **0 quadri in 3 secondi**, con e senza GPU, `visibilityState` «visible». Senza schermo non c'è scanout ⇒ **su Xvfb il pezzo cieco non esiste**. La stima si dichiara accanto ai numeri dell'**utente**, non accanto a quelli del banco |
| ⏳ ~~`[?]` quanti stream al secondo regge ciascun browser~~ — ⭐ **un numero c'è, per un browser solo** | `RCP.md` §2.3 — il video ne consuma uno per fotogramma. `[M]` 13 agosto, **Chrome 151 su Linux**: **60,0** fotogrammi dipinti al secondo offrendone 60 (cioè 60 stream/s, senza perdite), e **127,6/s** come **tetto a saturazione**. ⛔ **Resta `[?]` su Firefox e su Safari**, ed è la stessa `[?]` di `SPECIFICHE.md` §11.5: i mattoni stanno su due motori, i numeri su uno |

---

### 8-bis. ⛔ Le dodici cose che i rapporti dicevano e questa sintesi taceva

*Riportate la sera del 9 agosto 2026, rilievi **O1-O12** della revisione R2. ⭐ È la parte che
nessun controllo delle citazioni trova, perché non c'è niente da controllare: la riga non c'era.*

| # | Che cosa | Dove va, e che cosa cambia |
|---|---|---|
| **O1** | ⛔ **la scheda in secondo piano si congela dopo 5 minuti**, e l'esenzione vuole un canale WebRTC o una traccia multimediale viva `[S]` — che WebTransport da solo non è | §1.2 D, e `SPECIFICHE.md` §5.3: **un client congelato tace, quindi si stacca**. Va dichiarato, non scoperto |
| **O2** | ⛔ **AV1 è un vicolo cieco da entrambi i lati** — il nostro ferro non lo codifica `[M]`, e in decodifica non aggiunge niente che HEVC non dia | `SPECIFICHE.md` §11.4: resta nella scala di preferenza **come porta per l'hardware di domani**, non come strada da provare. ⚠ Un vicolo cieco non trascritto è un vicolo cieco che si ripercorre (`LEZIONI.md` §8) |
| **O3** | ⚠ **l'HDR non si promette**: BT.2020/PQ fa cadere lo zero-copy, e il percorso a una copia converte con un risultato slavato `[S]` | `SPECIFICHE.md` §11.4: ⛔ **si codifica BT.709**, ed è una scelta del server, non del client |
| **O4** | ⛔ **buttare un delta non dà nessun errore al decodificatore**: la corruzione si propaga in silenzio fino alla chiave successiva, e per abbandonare senza rompere servirebbero i **sotto-livelli temporali** `[?]` — da verificare su `EncSliceLP` dell'Intel | `RCP.md` §5.2, che già impone la chiave dopo un abbandono: la riga nuova è **perché** quell'obbligo non è facoltativo |
| **O5** | Safari è l'unico motore con WebTransport anche su **HTTP/2 e TCP**, e il nostro server non lo parla: il suo ripiego finirebbe in errore | §3.2 — **va deciso** se implementarlo o dichiarare Safari fuori dal ripiego ✅ *riportata* |
| **O6** | la pagina già aperta ha in mano **un'impronta che invecchia**: dopo la rotazione va ricaricata, o va chiesta l'impronta corrente | §3.2, e serve una riga in `RCP.md` su **dove sta quell'aggiornamento** ✅ *riportata* |
| **O7** | ⭐ **i bottoni a schermo sono un requisito, non un ripiego di fortuna**: tre riferimenti maturi su tre danno all'utente un modo di mandare quel che il browser non lascia passare | `SPECIFICHE.md` §7.3-bis: `Ctrl+Alt+Canc` non è «non recuperabile», è **recuperabile in un altro modo** |
| **O8** | ⛔ **gli stati sono tre, non due**: consegnata · **consegnata *e* riservata** · non consegnata. Il secondo è il peggiore — la sessione riceve la battuta **e** la scheda si chiude | §5.2, e riformula la misura **S3**: la domanda non è «arriva?» ma «arriva **e basta**?» |
| **O9** | ⛔ **su iPhone lo schermo intero è parziale in tutte le versioni** `[S]`, e senza schermo intero **non c'è keyboard lock** | §5.2: su iPhone si perde **tutta** la partita della tastiera, non qualche scorciatoia |
| **O10** | ⚠ la lock **non esiste se lo schermo intero è entrato con `F11`**, e **si spegne da sola alla perdita del fuoco** — cioè proprio nell'istante in cui i modificatori restano giù | §5.4: ⭐ e la cura **non richiede protocollo** — il client manda il rilascio di tutto quel che ha premuto quando perde il fuoco, e al riattacco ci pensa `RCP.md` §7.3 |
| **O11** | l'isolamento fra origini (COOP+COEP) è una **regola di prodotto**, non una taratura del banco: cambia come si servono le risorse | §6.3 lo degradava a «tarare il righello». Va in `SPECIFICHE.md` come vincolo di come il server serve la pagina |
| **O12** | la stringa di livello corretta per il traguardo è **5.1**, non 5.0 — e oltre 40 Mbit/s serve il tier **High** | è il parametro che **il server deve emettere**: `RCP.md` §4.3, accanto al codec |

⛔ **E la lezione che le tiene insieme**: una sintesi fedele in novanta punti che tace un vincolo
produce **un piano che lo scopre a metà lavoro**. Non è un difetto di accuratezza — le dodici righe
qui sopra non contraddicono niente di quel che era scritto: **non c'erano**.

### 9. Le lezioni che questo studio aggiunge

1. ⭐ **Una lezione vecchia è ricomparsa un livello più in alto.** `LEZIONI.md` §1.11 dice che una
   condizione **necessaria** non è **sufficiente** — ed era nata su «il processo ha aperto un render
   node ⇒ rende in GPU». Qui la stessa forma torna vestita da API ufficiale:
   `hardwareAcceleration: "prefer-hardware"` **riuscito** non dice che il decodificatore sia
   hardware. ⛔ **Cambiare strato non regala immunità**: una promessa di un'API va trattata come la
   dichiarazione di un compositore.
2. ⛔ **Il componente che non possiamo interrogare va fatto diagnosticare al prodotto.** Con i
   compositori, quando la prova indiretta non bastava, si chiedeva a loro (`LEZIONI.md` §1.11,
   seconda regola: *«se il componente sa rispondere, gli si chiede»*). **Il browser sa e non
   risponde** `[R]`. Quando succede, la misura non può stare in laboratorio: **deve vivere nel
   prodotto**, sul dispositivo dell'utente, che è l'unico posto dove la domanda ha una risposta.
3. ⚠ **Un capitolo che invecchia in mesi, non in anni.** I compositori li congela Debian; i browser
   si aggiornano da soli, e **due delle cinque cose più importanti di questo studio sono del
   2026** — una di maggio, una di gennaio. `LEZIONI.md` §9.8 dice di aggiornare i documenti quando
   una misura li smentisce; qui va aggiunto che **anche senza misure, questo file scade**.
4. ⭐ **Chi legge il codice altrui trova cure che nessuno inventerebbe.** La risincronizzazione dei
   modificatori **dagli eventi del mouse** (§5.4) non è deducibile: si trova solo guardando come
   l'ha risolta chi ci è passato prima. È il punto 0 della ricetta che continua a pagare — e per la
   seconda volta in due giorni **l'ha innescato una frase dell'utente**, non una nostra ricerca.


---

# Parte II — I cinque desktop


<a id="gnome"></a>

## GNOME come desktop — studio del codice, per la fase 11

*Scritto l'8 agosto 2026, con dieci ricerche parallele sui sorgenti clonati alle versioni di Debian
Trixie. È l'ottavo studio del progetto, e chiude il giro dei quattro desktop.*

> ### ⚠ Perché questo studio esiste, e perché arriva per ultimo
>
> GNOME è il desktop che REMOTIX serve **in produzione da dieci fasi**. Ma il documento che avevamo —
> §gnome-remote-desktop — studia **il server RDP di GNOME**, cioè un concorrente, **non il
> desktop**. Sessione, schermo di blocco, energia, voci pericolose, configurazione: su KDE, XFCE e
> LXQt li abbiamo studiati tutti; su GNOME **mai**, perché nessuno ci aveva costretti.
>
> ⭐ **Il risultato è che questo studio trova più difetti nostri di quanti ne trovino gli altri tre
> messi insieme** — e tutti sul desktop che consideravamo finito.

> **Le marche:** **[R]** letto nel codice, con `file:riga` — non è una misura · **[R-pkg]** letto nel
> pacchetto Debian · **[M]** misurato · **[?]** dedotto · **[✗]** verificato assente, con controllo
> positivo · **`[≠]`** ⚠ **il codice contraddice un nostro documento**.
>
> Dettaglio nei dieci rapporti in `reference-gnome/rapporti/`.

---

### 1. In due minuti

#### 1.1 ⛔ Le sette cose che su GNOME non abbiamo mai fatto

*Lette nel codice del prodotto sul server, sola lettura.*

| # | | |
|---|---|---|
| 1 | **il drop-in dell'unità della Shell** | `scrivi_dropin()` è chiamata **solo** `if (tipo == COMPOSITORE_KWIN)` (`src/sessione.c:671`). Su GNOME la Shell parte con `ExecStart=/usr/bin/gnome-shell` secco, **senza `--headless`** |
| 2 | **l'inibizione dell'energia** | `energia_inibisci()` **ritorna NULL** su Mutter (`src/energia.c:112-113`) |
| 3 | **il blocco schermo** | zero chiavi, zero recupero |
| 4 | **le voci pericolose** | nessun lockdown — su KDE l'utente l'aveva chiesto e l'aveva avuto |
| 5 | **la configurazione** | **zero occorrenze** di `gsettings`/`dconf`/`org.gnome.desktop` in tutto `src/` |
| 6 | **`SPA_META_Cursor`** | chiediamo `cursor-mode=2` (metadato) ma non chiediamo il metadato ⇒ **il cursore non arriva affatto** |
| 7 | **`SPA_META_SyncTimeline`** | e **Mutter lo offre** — è il *release* mancante della copia zero, cioè la caccia della fase 9 nel posto giusto |

⭐ **Una sola mossa ne paga tre**: un profilo dconf in `$XDG_RUNTIME_DIR` chiude insieme il blocco
schermo, le voci pericolose e la configurazione (§6).

#### 1.2 ⛔ E la cosa che ci tiene in piedi oggi è un incidente

**Su GNOME lo schermo di blocco non mostra uno schermo di blocco: ci stacca la sessione RDP.**
Entrando in `unlock-dialog`, gnome-shell chiama `inhibit_remote_access()` e Mutter — testualmente —
*«Any active remote access session will be terminated»*: chiude ScreenCast, RemoteDesktop e
InputCapture, **e rifiuta di ricrearne**.

✅ **L'eccezione è `is_headless()`.** E noi siamo headless — **ma non perché l'abbiamo chiesto**: Mutter
si degrada da sé quando la sessione logind non ha un seat, con un `g_message`
(`meta-backend-native.c:759-764`). ⛔ **La precondizione che ci salva non è scritta in nessuna nostra
riga.**

#### 1.3 ⭐ E la scoperta che riapre una caccia chiusa male

**R29 è sbagliata: il DMA-BUF di Mutter non è un «diff».** Due prove indipendenti nel codice — il blit
copia **l'intero** framebuffer di vista, e Cogl **svuota deliberatamente lo stack di clip** prima di
`glBlitFramebuffer`; e per un CRTC virtuale la vista è un **`CoglOffscreen` singolo e persistente**,
non uno swapchain, quindi il ridisegno parziale vi si **accumula**.

⭐ **Da cui si spiega perché la cura peggiorava le cose**: la superficie di accumulo copiava i soli
rettangoli danneggiati da un buffer che conteneva **già il fotogramma intero**.

⭐ **E il difetto vero è il *release***: `can_reuse_pw_buffer` — l'unico punto in cui Mutter aspetta
noi — **si arrende alla prima riga** se manca `SPA_META_SyncTimeline`, e riusa il buffer **mentre
VA-API lo sta ancora leggendo**. Due schermate che si alternano è esattamente il sintomo che ci si
aspetta da lì. E il riferimento fa il contrario di quel che avevamo concluso: **trattiene** il
`pw_buffer` fino a lettura finita.

⚠ **È una lettura di codice, non una misura** — ma è coerente con tutti i sintomi, e le due cure
candidate sono entrambe piccole.

---

### 2. La mappa

| Che cosa | Dove | Versione Trixie |
|---|---|---|
| il compositore | `reference-gnome/mutter/` | **48.7** |
| la shell | `gnome-shell/` | **48.7** |
| la sessione | `gnome-session/` | **48.0** |
| energia, media keys, xsettings | `gnome-settings-daemon/` | **48.1** |
| gli schemi | `gsettings-desktop-schemas/` | **48.0** |
| il gestore d'accesso | `gdm/` | **48.0** |
| il concorrente | `gnome-remote-desktop/` | **48.1** |
| il portale, le impostazioni, dconf | `xdg-desktop-portal-gnome/` 48.0, `gnome-control-center/` 48.4, `dconf/` 0.40.0 | |

⚠ **[M] Sul server GNOME non è più installato** (`dpkg-query` → not-installed, nessuna
`gnome.desktop`): **niente di questo studio è oggi verificabile sulla nostra macchina**, e il
ripristino va rifatto prima di qualunque misura.

---

### 3. La sessione senza monitor

*Dettaglio: `rapporti/01-sessione-gnome.md`, `08-gdm-remote-login.md`.*

#### 3.1 ⭐ La più semplice delle tre famiglie

| | |
|---|---|
| **Mutter** | ⭐ **nessuna opzione necessaria**: se la sessione logind è di tipo `wayland`, attiva e **senza seat**, si mette in headless **da solo** (`meta-backend-native.c:759-764`) |
| KWin | `--virtual --width/--height` obbligatori; `--drm` da SSH **esce con stato 1** |
| labwc | `WLR_BACKENDS=headless` obbligatoria |

⚠ **Ma serve che la sessione logind esista**, e che `XDG_SESSION_ID` sia esportata, o Mutter può
agganciare la sessione sbagliata. ⛔ **E `--virtual-monitor` non è opzionale**: in headless
`needs_outputs=false`, quindi senza quell'opzione la sessione parte **viva, completa e nera**.

**La forma**: ambiente da zero + drop-in su `org.gnome.Shell@wayland.service` con
`gnome-shell --headless --virtual-monitor WxH`, poi `gnome-session --session=gnome`.

⛔ **`SHELL` va messa vuota**: `gnome-session.in:3-14` si ri-esegue dentro una shell di **login** se
`$SHELL` è in `/etc/shells` — cioè si riporta dentro `~/.profile`. È `LEZIONI.md` §5 in agguato.

#### 3.2 ⭐ Il logout: una sentinella gratis, e un segnale che non esiste

`gnome-session` **non esce** dopo aver avviato il target: apre un fifo e dorme, uscendo esattamente a
sessione smontata (`main.c:447-487`). È la forma di `labwc --session`: **si sorveglia con un
`SIGCHLD`**, senza `RegisterClient`.

⛔ **[✗] `SessionOver` è dichiarato nell'XML e non viene MAI emesso** — un solo hit in tutti i
repository, la riga dell'XML stessa (controllo positivo: `SessionRunning` c'è anche
nell'implementazione). Chi ci avesse progettato sopra avrebbe aspettato per sempre.

⛔ **`Logout(1)` non basta**: mostra il dialogo se esiste un inibitore. Il congedo va su **`Logout(2)`**.

**La prontezza**: `SessionRunning` **più** `IsSessionRunning()`, che esiste apposta per la corsa fra
sottoscrizione ed evento. ⛔ Il nome `org.gnome.Shell` **non** è un indicatore: è preso prima di
`meta_context_start()`.

✅ **[✗] Nessun equivalente degli 8 s di XFCE**: la catena è a eventi. ✅ **[✗] Nessun
`loginctl terminate-session`, nessun subreaper.**

#### 3.3 ⭐ Trovata la riga del difetto storico del bus

Il «bus di sessione che non dà errore, dà silenzio» di `LEZIONI.md` §5 ha un colpevole con nome e
riga: `gnome-session-shutdown.target` tira `gnome-session-restart-dbus.service`, che fa
`StopUnit("dbus.service")` sul manager d'utente (`tools/gnome-session-ctl.c:130-133`). **Il demone
muore, il socket resta.**

⚠ E il ragionamento che salva KDE — «bus d'utente ⇒ sopravvive» — **qui è falso**, pur essendo vera la
premessa. **[?] Contromisura da provare**: mascherare quel servizio (il legame è `Wants=`, debole).

#### 3.4 ✅ GDM non ci ostacola

Tutta la sua manovra sul VT è dentro `if (seat_id == "seat0" && seat0_has_vts)`, e l'unico «kill» che
possiede agisce solo su sessioni create da lui. **Una sessione senza seat non la vede: `gdm3` può
restare acceso.** Va spento solo se un giorno vorremo un seat vero.

---

### 4. ⛔ La revoca: lo stato che GNOME ha e gli altri no

*È il fatto più importante del capitolo desktop, e non ha analoghi.*

| | |
|---|---|
| **che cosa succede** | entrando in `unlock-dialog`, gnome-shell chiama `inhibit_remote_access()` (`js/ui/main.js:136-145`); Mutter chiude **ScreenCast, RemoteDesktop e InputCapture** e **rifiuta di ricrearne** (`meta-remote-access-controller.c:146-164`, `meta-backend.c:1454-1468`, `meta-dbus-session-manager.c:349-353`) |
| **l'eccezione** | ✅ `is_headless()` — vero **solo** con backend headless (`meta-backend-native.c:361-369`) |
| **il recupero** | ⭐ esiste e **non chiede password**: `org.gnome.ScreenSaver.SetActive(false)`, oppure il segnale `Unlock` di logind. ⚠ Va eseguito **dal processo REMOTIX**, non dal client |

**Le tre difese, in ordine di forza:**

1. ⭐⭐ **non far girare `gdm.service`**: lo ScreenShield è creato solo se `canLock()`, che interroga
   `org.gnome.DisplayManager` — **[✗] nome non attivabile via D-Bus**. Senza GDM il blocco è
   **impossibile**. ⚠ Ma su Trixie GDM **è attivo**, quindi da solo non basta;
2. **un session mode nostro**: il modo esclude `unlockDialog` ⇒ gnome-shell rifiuta di bloccare.
   ⛔ `parentMode:"user"` **lo rimette**: va ricopiato per intero;
3. **il lockdown** (§5).

⭐ **Da cui la domanda 16 per `LEZIONI.md`**: *«c'è uno stato in cui il compositore ci REVOCA quel che
ci ha già concesso, e chi ha il dito su quel pulsante?»* La domanda 3 chiede se c'è un permesso; questa
chiede se il permesso **può essere ritirato a caldo**, ed è una cosa diversa. Su GNOME esiste un'API
dedicata a farlo.

---

### 5. Il lockdown, le voci, il cursore

*Dettaglio: `rapporti/02-shell-blocco-voci.md`.*

#### 5.1 ⭐ Il lockdown vale più del KIOSK di KDE

Delle undici chiavi di `org.gnome.desktop.lockdown`, **quattro** sono lette da gnome-shell 48.7 e una
da gnome-session — e **la voce sparisce**, non si ingrigisce (`system.js:218-226` lega `can-*` a
`visible`), con l'intero pulsante nascosto se spariscono tutte.

| chiave | effetto |
|---|---|
| `disable-lock-screen` | toglie «Blocca». ⛔ **Non copre `SetActive(true)`** — falla nota |
| `disable-user-switching` | toglie «Cambia utente». ⛔ Da togliere **sempre**: l'azione **blocca prima di fallire** |
| `disable-log-out` | ⭐ la più potente: gnome-session risponde `false` a `CanShutdown` ⇒ spariscono **anche Spegni e Riavvia**. ⛔ Ma rifiuta pure `SessionManager.Logout`: **il nostro congedo va rifatto passivo** |
| `disable-command-line` | toglie il dialogo Esegui |

⛔ **[✗] Due chiavi da non mettere**: `user-administration-disabled` **non è letta da nessuno**, e
`idle-activation-enabled` è deprecata e ignorata.

⚠ **La scorciatoia del blocco non è `Ctrl+Alt+L`**: è `<Super>l` più `screensaver-static`, e **le due
liste si concatenano** — vanno azzerate entrambe. ⚠ E come su KDE, la regola polkit per Sospendi va
scritta **`no`, non `auth_admin`**: `challenge` **mostra** la voce.

#### 5.2 ⭐ Il cursore: la cura di KDE non serve, e c'è di meglio

Su Mutter il cursore non è nell'immagine **perché lo chiediamo noi**: dichiariamo `metadata` e Mutter
risponde con `inhibit_cursor_overlay`. Con `cursor-mode=1` sarebbe dentro, come su KWin e wlroots.

⭐ **La scelta giusta è `cursor-mode=2` (METADATA)**: pixel puliti **e** forma, posizione e hotspot in
banda laterale, da inoltrare come **cursore RDP nativo** — cioè la cosa a cui su KDE avevamo dovuto
rinunciare. ⛔ **Ma oggi non chiediamo `SPA_META_Cursor`, quindi quei dati non arrivano affatto.**

⛔ E se un giorno servisse il tema trasparente, **il canale non è `XCURSOR_THEME`**: Mutter non la
legge (l'unico `getenv` rilevante è `XCURSOR_PATH`), legge `org.gnome.desktop.interface cursor-theme`.
Trappola peggiore di wlroots: un tema vuoto dà un **quadrato grigio**.

#### 5.3 ⚠ I dialoghi che compaiono da soli

Otto, e tre ci riguardano davvero: il **fail-whale** di gnome-session (trigger concreto per noi: il
controllo GL fallito), il **dialogo di benvenuto** (si spegne impostando una chiave, non bloccandola),
e ⭐ il **dialogo di accessibilità innescabile dal nostro stesso input** (Maiusc premuto cinque volte):
il cancello è `org.gnome.desktop.a11y.keyboard enable`, che è già `false` di suo ma **va bloccato**.

✅ **[✗] E la trappola di KWin senza output non ha gemelli**: nessun segnaposto, il vincolo del
puntatore è un no-op, la tastiera non è toccata. Lo schermo virtuale su GNOME è precondizione del
*disegno*, non della sopravvivenza.

---

### 6. ⭐ dconf: l'unica configurazione dei quattro desktop che regge

*Dettaglio: `rapporti/04-dconf-configurazione.md` — ed è l'unico rapporto con misure `[M]` proprie.*

| | |
|---|---|
| **i lock reggono** | `gsettings set` su chiave bloccata **esce con 1** e lo dice: il controllo è **sincrono e locale**, prima che parta il messaggio D-Bus. ⭐ Dove xfconf usciva con successo e ripristinava in silenzio |
| **vincono sul valore dell'utente** | **[M]** utente `true`, lock e db `false` ⇒ `gsettings get` risponde `false`: il valore in casa viene **saltato in lettura** |
| ⭐ **non serve root** | `$XDG_RUNTIME_DIR/dconf/profile` è la terza priorità di caricamento. **[M]** scritto il file la sessione vede valori e lock; cancellato, torna tutto com'era; **zero byte scritti in `~`** |

**Le tre trappole, tutte misurate:**

1. ⛔ **`.gschema.override` non è un'alternativa**: cambia il *default*, che sta **sotto** al valore
   dell'utente — e l'utente ha già `lock-enabled=true`, che è sempre il caso reale;
2. ⛔ **`XDG_CONFIG_HOME` effimero fallisce in silenzio**: `dconf-service` è un processo separato con
   **il suo** ambiente ⇒ la scrittura riesce e finisce **nella casa vera**;
3. ⛔ **un lock senza valore non congela: azzera al default del fornitore** (600 → 300). Ogni chiave
   bloccata va **anche** valorizzata.

⚠ E due dettagli che costano un pomeriggio: una riga di lock **senza `/` iniziale è scartata in
silenzio** (l'unica verifica è `gsettings writable` chiave per chiave), e **`file-db:` non rilegge mai**
a caldo — se serve il caldo serve `system-db:`, e quindi root.

⭐ **Il precedente da copiare è GDM, non `gnome-remote-desktop`**: GDM fa esattamente questo — profilo
nell'ambiente di lancio, `file-db:`, **28 chiavi bloccate** **[R-pkg]** — e da lì si rubano due righe
che non avremmo pensato: azzerare la scorciatoia del blocco **oltre** a disabilitarlo, e neutralizzare
il terminale predefinito.

⛔ **[✗] `gnome-remote-desktop` non configura la sessione affatto**: nessun profilo, nessun lock,
nessuna inibizione. **Il vuoto è nostro, non stiamo duplicando niente.**

---

### 7. ⛔ L'energia: il server si addormenta

*Dettaglio: `rapporti/03-energia-inibizioni.md`.*

**Il default upstream *e* Debian di `sleep-inactive-ac-type` è `suspend`, con timeout 900 s**, e
`gsd-power` chiama `logind Suspend(false)`.

⚠ **Oggi non ci morde, ma per accidente**: `SessionIsActive` è falso perché non esiste una sessione
logind grafica, quindi gsd-power si disarma da sé. **Un guadagno che non abbiamo scelto e che una
misura può ribaltare** — misurato: una sessione logind **senza seat** risulta comunque `Active=yes`.

⭐ **La cura è una chiamata sola**: `org.gnome.SessionManager.Inhibit(app_id, 0, reason, 12)` — cioè
`SUSPEND(4) | IDLE(8)` **insieme**. Con il solo `IDLE`, se lo screensaver si è acceso prima
dell'inibizione, l'unica difesa che resta chiede il bit `SUSPEND`: è la forma attenuata del difetto
pagato su KDE. ⛔ **Mai il bit `LOGOUT(1)`**: ci renderebbe ostaggio dell'uscita dell'utente.

✅ **La precondizione quasi non si pone**: `Inhibit` sta sullo **stesso oggetto** di `RegisterClient`,
che REMOTIX già chiama (`src/uscita.c:180`) — se la registrazione riesce, il nome c'è.

⭐ **Due buone notizie:**

- **l'input che iniettiamo azzera davvero l'inattività** — né via D-Bus né via libei l'evento è marcato
  `SYNTHETIC` (`core/events.c:126-138`): un utente remoto che lavora tiene sveglia la sessione da sé.
  Ma un client passivo no;
- ✅ **se perdessimo la corsa, l'immagine non muore**: `PowerSaveMode` **non ferma** i fotogrammi di un
  monitor virtuale, perché le view virtuali sono offscreen. Il difetto di labwc non si ripresenta, e
  **la cura di wayvnc non serve**. Si vedrebbe però la schermata di blocco — cioè §4.

⚠ E tre trappole di configurazione: `idle-delay=0` **non** ferma la sospensione (il timer di sleep ha
un timeout proprio); `idle-delay=0` con `idle-dim=true` accende un dim a 60 s; `disable-lock-screen`
ferma `lock()` ma **non** `activate()` — la leva vera è `lock-enabled=false`.

---

### 8. La cattura, riletta nel codice

*Dettaglio: `rapporti/05-mutter-cattura.md`. Sette `[≠]`.*

#### 8.1 Le correzioni a R29

| Che cosa dicevamo | Che cosa dice il codice |
|---|---|
| il DMA-BUF è un **diff** su quattro buffer riciclati | ⛔ **falso**: blit dell'intero framebuffer, stack di clip **svuotato deliberatamente**, e la vista virtuale è un `CoglOffscreen` **persistente** |
| la cura è una **superficie di accumulo** | ⛔ per questo peggiorava: copiavamo i rettangoli danneggiati da un buffer **già intero** |
| «la fence implicita è quella sbagliata» | ⚠ copre metà del contratto — l'*acquire*. Quel che manca è il **release** |
| «trattenere il buffer non serve» | ⛔ il riferimento fa **il contrario**, ed è l'unica protezione senza timeline |
| «la timeline quando c'è» | ⛔ `gnome-remote-desktop` 48.1 **non nomina mai** `SPA_META_SyncTimeline` |
| «`cattura.c` non chiede un solo `SPA_PARAM_Meta`» | ⚠ superata: oggi chiede Header e VideoDamage |

**Il contratto della timeline, per chi la scriverà**: `blocks=3`, i due `spa_data` `SyncObj` in **coda**
(stesso fd), primo `SPA_PARAM_Buffers` con `metaType` MANDATORY; e i buffer vanno alzati (Mutter ne
propone fino a 16; i nostri quattro li chiediamo noi).

#### 8.2 ⭐ La cadenza: il fatto è `[M]`, ⚠ **la causa è `[R]`**. *Misurato il 13 agosto 2026, e corretto la sera stessa*

`framerate` è un **valore fisso `0/1`** — ecco perché una cadenza fissa non negozia. E il
`maxFramerate` fa **due cose insieme**: è il freno della cattura **ed è la frequenza del monitor
virtuale**.

⛔ *Questo paragrafo diceva: «Stesso numero ⇒ **battimento** ⇒ 0,61». **È sbagliato**, e la misura
della fase 3 (step 1, M3) lo smentisce in tutt'e due le metà: né il battimento né lo 0,61.*

⭐ **IL FATTO, che è `[M]` e non si tocca**: negoziando il monitor a **120 Hz** e rinegoziando la
**sola** cadenza a **90**, GNOME consegna **61,4 fotogrammi al secondo** (60,04 dalla mediana), con
intervallo mediano **16,66 ms** e p99 **20,43**. È la cella **D** di `banchi/03-b14-esiti.jsonl`.

⚠ **LA CAUSA, che è `[R]` e va detta per quello che è**: letta nel codice di Mutter, `maxFramerate`
non sembra un tetto continuo ma una **griglia** — il freno calcola
`min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) e lo mette contro un tick
da **16666,67 µs**, e chi cade sotto **perde un tick intero**. ⭐ **Resta la spiegazione migliore che
abbiamo**, ed è **coerente con la cella D**, che è pulita. ⛔ **Ma è una lettura del codice, non una
legge misurata**, e non va scritta come se lo fosse.

> ⛔⛔ ⚠ *Qui stava scritto, e in altri otto documenti con lei: «`[M]` legge verificata su **13
> punti**: 8 la confermano, **0 la smentiscono**». **È FALSO.** Il file degli esiti della griglia —
> `banchi/03-b14-esiti-griglia.jsonl` — porta **tre righe in tutto**: il terreno e **due celle**
> (`griglia-apertura-120` e `griglia-freno-90`), e **tutt'e due portano `scena_sul_mio_monitor:
> false`** ⇒ sono **rifiutate dal banco stesso**, che sul proprio verdetto stampa «⛔ la legge NON
> regge su **0 punti su 0**». I tredici punti non stanno in nessun file di esiti. ⇒ La
> quantizzazione **torna `[R]`**. **Corretta il 13 agosto 2026**, rilievo del coordinatore della
> fase 3, verificato riga per riga sui due file di esiti.*
>
> ⭐⭐ **E la ragione del rifiuto è la trappola numero uno di `LEZIONI.md` §1.1**: *la scena deve
> stare sul monitor che si sta catturando*. Il banco **lo aveva scritto nel proprio file**, campo per
> campo, e nessuno ha guardato quel campo: si è letto il numero e non la riga accanto.

**La tabella qui sotto viene TUTTA da `banchi/03-b14-esiti.jsonl`** — sette celle, **tutte** con
`scena_sul_mio_monitor: true`, con i tre controlli (positivo: crollo a 9,57 chiedendo 10; negativo:
60→60 resta su 46,07; ritorno: 83,03, cioè torna su B) che chiudono:

| monitor | freno | consegnati | mediana | p99 | cella |
|---|---|---|---|---|---|
| 60 | 60 | 31,5 | 33,31 ms | 35,53 | **A** |
| 120 | 120 | 82,9 | 12,12 ms | 18,53 | **B** |
| 120 | 60 | 46,13 | 24,12 ms | 29,23 | **C** |
| ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 | ⭐ **D** |

⛔ **E i «sei decimi» non si riproducono**: la cella bassa dà **0,50 pulito e deterministico**, che è
quel che una griglia produce e un battimento no. ⭐ **Questa cella è pulita** — è la **A**, e regge.

> ⛔ ⚠ *E cade anche il riscontro incrociato.* Qui stava scritto: «Riscontro incrociato con una
> seconda scena indipendente: concordano **entro il 4 %**, attese **0** ovunque». ⛔ **Non regge**, e
> lo dice il file stesso, `banchi/03-b14-esiti-scena2.jsonl`: la sua **cella D** — cioè proprio il
> risultato da confermare — porta `scena_sul_mio_monitor: false`, `palco_stabile: false` e **1
> fotogramma in 25 s (0,04/s)**, e non ha nemmeno il conto delle attese, perché il suo step 2 non
> c'è. E il suo **controllo di RITORNO** dà **52,84** contro gli **80,28** della sua stessa cella B:
> **non torna**, quindi la catena dei controlli di quella scena **non chiude**. Entro il 4 %
> concordano solo la cella A (31,28 contro 31,5), la B (3,2 %) e il controllo positivo; la C sta al
> **5,4 %** e il controllo negativo al **7 %**. ⇒ ⛔ **Il 61,4 oggi ha UNA scena sola.** Corretto il
> 13 agosto 2026, stesso rilievo.

⭐ **`ensure_virtual_monitor` esce prima se la misura non cambia**, e il disaccoppiamento
**funziona**: negoziare alto (monitor 120) e rinegoziare la sola cadenza (freno 90) porta GNOME a
**61,4**, cioè quanto KWin. È costato tre celle e **zero righe di prodotto**, come previsto.

⛔⛔ **Ma il prodotto oggi non sa chiederlo, e va scritto qui**: `MOVIMENTO_FPS 60` è una costante di
compilazione (`src/figlio.c:1465`), `main.c` non ha nessuna opzione di cadenza, e **`RecordVirtual`
non prende la frequenza** (`src/mutter.h:82`) — i quattro monitor virtuali sono tutti
**1920×1080@60**. ⇒ Il risultato è `[M]` **sul banco** e **zero in produzione**.

⛔⛔ **E sulla catena vera il collo NON è `maxFramerate`: è il codificatore in software.** Misurato
il ritardo cattura → vetro (mediana **74,58 ms**, `SPECIFICHE.md` §3.2), il disegno → cattura di
Mutter pesa **16,66 ms su 74,6, cioè il 22 %**: il **78 % è nostro**, e ~39 ms stanno nel tratto
cattura → primo byte in pagina, dominato dal codificatore in software (libsvtav1 / libx265). ⇒ Il
figlio del prodotto consegna **23,93 fotogrammi/s con ZERO attese a vuoto**: **non aspetta mai
Mutter**. Alzare la cadenza della cattura non sposterebbe il ritardo.

#### 8.3 Il resto

**[✗] Un fotogramma intero a richiesta non esiste** (nessuna proprietà, nessun flag, nessun parametro)
— **e non serve**, visto §8.1. **[✗] Solo `BGRx` e `BGRA`**: R32 confermata riga per riga. ⛔ **I buffer
di solo cursore stantii esistono anche su Mutter**, l'analogo esatto di §kde §4.7 — già gestito nel
nostro codice dal 7 agosto.

---

### 9. L'input, riletto nel codice

*Dettaglio: `rapporti/06-mutter-input.md`. Quattro `[≠]`.*

⛔ **`EI_EVENT_KEYBOARD_MODIFIERS` non arriva nemmeno su GNOME**: `eis_device_keyboard_send_xkb_modifiers`
ha **zero occorrenze** in Mutter 48.7 (controllo positivo: 25 altre `eis_device_*` usate). La frase che
avevamo in **due** documenti — su KWin non arriva, *a differenza di GNOME* — **è falsa: sono pari**.

✅ **La fonte vera su GNOME sono due proprietà D-Bus** (`CapsLockState`/`NumLockState`) con
`SYNC_CREATE`, che danno anche lo **stato iniziale** — cosa che su labwc non abbiamo.

| Altro `[≠]` | |
|---|---|
| il `mapping-id` | **non lo dichiariamo noi**: lo genera Mutter come UUID e ce lo pubblica nei `Parameters`. Il verso è **Mutter → noi**, e `compositore_mapping_id` è invertito |
| il tasto Pausa | il riferimento pretende il flag E1: il nostro «riconoscibile anche senza» è **una scelta**, non un fatto |
| touch/RDPEI | **[✗] non esiste nella 48.1**: tre sezioni del nostro documento descrivono la **49+** |

⭐ **La rotella `/120 → ×10` è giusta, ma non per la ragione scritta**: con `scroll_delta` Mutter forza
`SOURCE_WHEEL` e **salta** l'accumulatore. La soglia reale di uno scatto è **60**, cioè mezzo. ⚠ E
`ei_device_scroll_discrete` fa una **divisione intera per 120**: i mezzi scatti spariscono.

⛔ **Due ricambi che toccano la fase 6**: un cambio di **keymap** distrugge e ricrea il dispositivo
tastiera; un cambio di **geometria** distrugge e ricrea tutti i dispositivi assoluti. Il puntatore al
device vecchio smette di funzionare **senza errore**: keymap e regioni vanno rilette **a ogni
`DEVICE_ADDED`**.

⚠ E un fallimento silenzioso da conoscere: `transform_position` che fallisce **non è un errore** — una
riga di log e il metodo D-Bus **ritorna con successo**.

---

### 10. La clipboard

*Dettaglio: `rapporti/07-clipboard-portale.md`. Sei `[≠]`.*

⛔ **La clipboard di GNOME non è della sessione RemoteDesktop.** È `MetaSelection`, cioè **del
compositore**, come su KDE e wlroots; della sessione è solo la **porta**. La riga della domanda 14 in
`LEZIONI.md` va riscritta.

| Che cosa dicevamo | Che cosa dice il codice |
|---|---|
| «chi si ricollega non riceve un annuncio, e ci è costato» | ⛔ **falso**: `EnableClipboard` con opzioni **vuote** emette subito `SelectionOwnerChanged`. Era la nostra ricetta a perderlo |
| «l'eco va distinta con un'euristica» | ✅ è **etichettata** (`session-is-owner`), e `SelectionRead` sulla propria selezione è **rifiutata**: lo stallo di KWin qui è impossibile |
| «la clipboard non sopravvive alla morte di chi ha copiato» | ⛔ **su GNOME sopravvive**: Mutter ha un **clipboard manager interno**, avviato incondizionatamente — ma **in un solo tipo MIME**, con tetti 4 MiB / 200 MiB |
| «senza sessione la clipboard non esiste» | ⛔ **la sponda X11 è incondizionata nei due versi** (zero controlli sul fuoco): `xclip` funziona senza sessione, **e il banco su GNOME può usarlo** |

**Tre trappole operative:**

1. ⛔ **`DisableClipboard` è a senso unico**, per un difetto di Mutter: il flag ha **un solo
   assegnamento in tutto il file**, a `TRUE`. Dopo il Disable, `Enable` risponde «Already enabled» e
   gli annunci non arrivano più. **Regola: non chiamarla mai** — per lasciare la clipboard si usa
   `SetSelection` senza `mime-types`;
2. ⛔ **firma asimmetrica**: `mime-types` è **`as`** in ingresso e **`(as)`** in uscita. Chi legge il
   segnale con il tipo sbagliato ottiene `NULL` **senza errore** — confermato da tre implementazioni
   indipendenti;
3. ⛔ **gnome-shell azzera la clipboard a ogni blocco schermo**: ci strappa la proprietà in silenzio.

⚠ E `POLLHUP` vale «pronto» anche qui, ma il fd di `SelectionWrite` che riceviamo è **bloccante**,
mentre quello di `SelectionRead` arriva già non bloccante.

---

### 11. Il concorrente, guardato in faccia

*Dettaglio: `rapporti/09-chi-lo-fa.md`.*

> ⭐ **`gnome-remote-desktop` è un ottimo backend RDP e un prodotto incompleto; REMOTIX è un prodotto
> più completo con un backend meno rifinito.**

**Che cosa facciamo noi che lui non fa** — e gli otto che contano stanno tutti fra «accendi una Debian
senza monitor» e «vedi un desktop»:

| | |
|---|---|
| ⭐ **avviamo la sessione** | il suo README dice che la sessione headless dev'essere *«independently set up»*. **[✗]** nessun codice che avvii un compositore |
| ⭐ **autenticazione vera** | lui impone NLA con un **file SAM fabbricato**, credenziali scollegate dall'account. **[✗] Kerberos nella 48.1 non esiste** |
| **TLS puro** | il suo rifiuto del ripiego è la causa di una fila di segnalazioni chiuse come «Not GNOME» |
| ⭐ **H.264 su GPU di serie** | ⛔ da lui la VA-API è **dietro una variabile di debug**: senza NVIDIA il percorso normale è **RemoteFX Progressive in CPU** |
| **controllo del bitrate** | lui è QP fisso a 22, nessun target |
| ⛔ **rifiuto della seconda connessione** | **[✗]** in headless 48.1 **nessuna politica**: sessioni parallele illimitate |
| **il resto** | certificato generato da noi, distinzione logout/distacco, sink audio creato dal nulla, inibizioni, più compositori, numeri propri |

**Dove è avanti lui** — quasi tutte **ore di lavoro**, non vantaggi strutturali: il **cursore**
(572 righe, cache LRU — noi non lo mandiamo affatto), i **file negli appunti** via FUSE, il
**microfono**, **AAC/Opus**, un **regolatore di latenza audio a 300 ms**, la **gestione della
sospensione degli ack**, il ridimensionamento senza rifare la cattura, il multi-monitor, la
**strumentazione** (metriche con fotogrammi saltati e un canale di telemetria che legge i tempi del
client), il **Remote Login**, e il **confezionamento**.

> #### ⛔ Una cosa da verificare nel nostro codice **subito**, non a fine studio
>
> Il client RDP può **sospendere gli ack** mandando `queueDepth == 0xFFFFFFFF`, e un regolatore che
> non lo gestisce **si ferma per sempre**. Il nostro concede `MAX(2, rtt·fps/10⁶+2)` posti: se quel
> valore viene trattato come un numero, la coda si chiude e il desktop si pianta.

⚠ **Il documento §gnome-remote-desktop è scritto sulla 51.alpha**, non sulla 48.1 di Trixie: sei
sezioni sono da correggere (niente Kerberos, niente touch, niente throttler, `CURSOR_MODE_EMBEDDED`
mai usato, VA-API dietro debug, due formule di posti invece di una). ⛔ E Debian dichiara **trixie
48.1-4 vulnerabile a CVE-2025-5024**, un DoS non autenticato.

#### 11.1 ⭐ L'handover di GNOME 48, che è portabile

Il socket TCP **non viene mai chiuso**: viaggia come **file descriptor su D-Bus**, e chi lo instrada
aveva letto in **`MSG_PEEK`**, quindi il destinatario rifà la negoziazione RDP da zero. Più il **Server
Redirection PDU** con routing token, che è RDP puro e FreeRDP lo espone.

**Sei cose da copiare, tutte portabili su KDE, XFCE e LXQt**: il socket per fd; `MSG_PEEK` per
instradare senza consumare; il Redirection PDU; autorizzare **per sessione logind** invece che per
polkit; `Inhibit("sleep","block")` finché c'è un client; l'autolicenziamento del greeter.

⛔ **Ma non conviene appoggiarsi al Remote Login**: significherebbe **smettere di essere il server RDP**
(lui il server, noi al massimo un client), funzionerebbe **solo su GNOME** — quindi la strada «avvio da
me» resterebbe da scrivere comunque per gli altri tre, e sarebbero **due prodotti**. Con in più un dato
di campo: l'handover **fallisce a caso in circa due avvii su tre** su Fedora 42, e sono cinque processi
in tre contesti di sicurezza sincronizzati su un timeout di 30 s.

---

### 12. La matrice, rifatta col denominatore giusto

*§lxqt §4.1 contava 9 combinazioni. Erano **10**.*

**Cinnamon 6.4.10 e muffin 6.4.1 sono in Trixie** con una sessione `cinnamon-wayland.desktop`
**[R-pkg]**. ⛔ Ma muffin **rinomina il bus in `org.cinnamon.Muffin.*`** ed è un fork della linea 3.38,
a ~10 cicli da Mutter: **non è gratis né dalla fase wlroots né dal lavoro su GNOME**.

| | |
|---|---|
| combinazioni realistiche su Trixie | **10** |
| coperte oggi | **2** (20 %) |
| dopo la sola fase wlroots | **8 su 10 — 80 %** |
| la prossima che costa meno | **LXQt su labwc: zero righe** |

⭐ **Ma la cosa che costa davvero meno non è una combinazione nuova: sono le cinque voci del debito di
§1.1**, sul desktop che serviamo già.

---

### 13. Il piano di misure

⚠ **Passo zero: rimettere GNOME sul server**, che oggi non è installato.

| # | La misura | Perché |
|---|---|---|
| **M1** | ⛔ il nostro regolatore regge `queueDepth == 0xFFFFFFFF` | §11: un desktop che si pianta per sempre. Si prova con un client strumentato, non aspettando |
| **M2** | headless sì/no contro `inhibit_remote_access` | §4: è la precondizione che oggi abbiamo **per accidente** |
| ⚠ **M3** | la cadenza disaccoppiata — ⭐ **il fatto è ottenuto**, ⛔ **ma la misura è MEZZA e non è chiusa** | §8.2: `[M]` monitor 120 + freno 90 ⇒ **61,4 consegnati** (60,04), mediana **16,66 ms** — cella **D**, pulita, con i tre controlli che chiudono. ⛔ **Ma la causa è `[R]`, non `[M]`**: la «legge della griglia» su 13 punti **non esiste** (vedi il riquadro di §8.2), e ⛔ **il riscontro su una seconda scena non c'è**: la cella D di `03-b14-esiti-scena2.jsonl` è rifiutata dal banco. ⚠ **Non attuabile dal prodotto oggi** (`RecordVirtual` non prende la frequenza), e ⛔ **non è la cura del ritardo**: sulla catena vera il collo è il codificatore in software |
| **M4** | `SPA_META_SyncTimeline` con acquire/release, **oppure** trattenere il `pw_buffer` | §8.1: è la caccia della fase 9 nel posto giusto |
| **M5** | `SPA_META_Cursor` + `cursor-mode=2` → cursore RDP nativo | §5.2: oggi il puntatore non arriva da nessuna parte |
| **M6** | il profilo dconf in `$XDG_RUNTIME_DIR` con i lock, e **ogni chiave riletta** | §6: paga §1.1 punti 3, 4 e 5 insieme |
| **M7** | `Inhibit(…, 12)` regge 20 minuti, e la macchina non si sospende | §7 |
| **M8** | la clipboard: annuncio alla riconnessione, e il blocco schermo che la azzera | §10 |
| **M9** | prova **guasta di proposito**: `SHELL` non vuota, e `--virtual-monitor` assente | ⭐ imparare come si legge il guasto: sessione **viva, completa e nera** |

> #### ⚠ M3 — **lo stato vero**, scritto il 13 agosto 2026 dopo il rilievo
>
> *Stamattina questa riga diceva **✅ CHIUSA il 13 agosto 2026**, e lo diceva **sulla base della
> griglia**. La griglia è caduta — le sue due celle sono rifiutate dal banco stesso, §8.2. ⇒ **M3 non
> è chiusa e non è aperta: è mezza**, e va tenuta mezza finché non si fanno le due metà che mancano.
> ⛔ Non la si forza a «chiusa» perché il numero è bello, né ad «aperta» perché una riga era falsa.*
>
> | | |
> |---|---|
> | ✅ **quel che M3 HA ottenuto** | `[M]` **61,4** a monitor 120 e freno 90 — cella **D** di `banchi/03-b14-esiti.jsonl`, `scena_sul_mio_monitor: true`, con controllo positivo (crollo a 9,57), negativo (fermo su 46,07) e di ritorno (83,03) che chiudono. **Questo è un fatto, e resta** |
> | ⛔ **quel che M3 NON ha** | la **causa**. La quantizzazione è `[R]`: letta nel codice di Mutter, coerente con la cella D, **mai misurata su una griglia di punti** |
> | ⛔ **e nemmeno** | il **riscontro su una seconda scena**: la cella D di `banchi/03-b14-esiti-scena2.jsonl` porta `scena_sul_mio_monitor: false` e **1 fotogramma in 25 s** ⇒ il 61,4 ha **una scena sola** |
> | ⇒ **che cosa la chiuderebbe** | rifare la **griglia** con la scena sul monitor che si cattura, e rifare la **cella D** sulla seconda scena. È lo stesso banco `banchi/03-b14-cadenza.py`, e ⭐ **il campo per accorgersene ce l'ha già**: è `scena_sul_mio_monitor`, e stamattina nessuno l'ha guardato |

---

### 14. Le lezioni che questo studio aggiunge

1. ⭐ **La domanda 16**: *«c'è uno stato in cui il compositore ci REVOCA quel che ci ha già concesso, e
   chi ha il dito su quel pulsante?»* La domanda 3 chiede se esiste un permesso; questa chiede se può
   essere **ritirato a caldo**. Su GNOME esiste un'API che *«termina ogni sessione di accesso remoto
   attiva»*, e nessuna delle quindici domande la copriva.
2. ⛔ **Il desktop che serviamo meglio è quello che abbiamo studiato peggio.** Dieci fasi su GNOME
   hanno prodotto una conoscenza profonda della *cattura* e nessuna del *desktop*: sette voci mai
   affrontate, e due di esse (§4 e §7) sono difetti che l'utente incontrerebbe **lasciando la sessione
   ferma venti minuti**.
3. ⭐ **Una condizione che ci salva per accidente va scritta come requisito.** Siamo headless perché
   Mutter si degrada da sé senza seat, non perché l'abbiamo chiesto — e da quella condizione dipende
   il fatto che un blocco schermo non ci stacchi. È la forma generale di `LEZIONI.md` §2.5: *la
   protezione di un difetto noto non si affida a qualcosa che si può perdere.*
4. ⚠ **Le misure invecchiano peggio delle letture.** R29 è stata scritta da misure corrette e da una
   **diagnosi sbagliata**, ed è rimasta in piedi due fasi perché nessuno aveva letto il codice che le
   stava sotto. La lezione §1.9 diceva «quando codice e misura si contraddicono, sospetta la misura»;
   questo studio aggiunge il caso opposto — **una misura giusta con una spiegazione inventata è più
   pericolosa di una misura sbagliata**, perché nessuno la rimette in discussione.


<a id="kde"></a>

## KDE Plasma e KWin — studio del codice, per la fase 11

*Analisi condotta sul codice sorgente originale di KDE, clonato da `invent.kde.org` il 7 agosto 2026
e tenuto in `reference-kde/`, con la stessa convenzione di `reference/xrdp`.*

| Repository | Versione clonata | Perché |
|---|---|---|
| `plasma/kwin` | tag **v6.3.6** | il compositore: è **lui** che possiede schermo e input |
| `plasma/plasma-workspace` | tag **v6.3.6** | la sessione: avvio, logout, ksmserver, klipper |
| `plasma/kpipewire` | tag **v6.3.6** | consuma PipeWire e **codifica in H.264**: fa il nostro stesso lavoro |
| `plasma/xdg-desktop-portal-kde` | tag **v6.3.6** | la via «ufficiale» alla cattura, e il consenso |
| `plasma/libkscreen` | tag **v6.3.6** | configurazione degli schermi da fuori |
| `plasma/powerdevil` | tag **v6.3.6** | energia, inibizioni, spegnimento |
| **`plasma/krdp`** | tag **v6.3.6** *e* master `1dd52ba` (6.7.80) | ⭐ **il server RDP di KDE**: stessa libreria RDP, stesso compositore, stessi client. **È il riferimento principale della fase**, l'equivalente di `gnome-remote-desktop` |
| `network/krfb` | master `6b2832b` (KDE Gear 26.11.70) | il desktop remoto VNC di KDE |
| `libraries/plasma-wayland-protocols` | master | gli XML dei protocolli di KDE |

**6.3.6 è la versione di Debian Trixie** (§3.8 di `SPECIFICA.md`), cioè quella che gira sulla
macchina di runtime: le righe citate qui sono quelle che l'utente ha davvero installate.

Insieme ai sorgenti di KDE è stato riletto **il nostro codice di banco** — `banco/nodo-kwin.c` (il
client del protocollo di KWin), `banco/misura-cattura.c` (il consumatore PipeWire),
`banco/banco-altri.sh`, `banco/zkde-screencast-unstable-v1.xml` — perché metà del valore di questo
studio sta nel confronto fra quel che KDE fa e quel che noi abbiamo già scritto.

Ogni affermazione porta una marca, come in `REFERENCE.md`:

| Marca | Significato |
|---|---|
| **[R]** | **letto nel codice**, con `file:riga`. È il grosso di questo documento |
| **[M]** | misurato da noi, sul campo, con data |
| **[?]** | **non deciso dal codice**: va misurato sul banco. Le `[?]` sono elencate in §14 |
| **[✗]** | **cercato e non trovato**: una dichiarazione negativa, che vale quanto una positiva |

> ⚠ **Questo documento è di lettura, non di misura.** `LEZIONI.md` §1 dice che il progetto non si è
> mai fermato su un problema difficile ma su una misura che non misurava quel che credevamo: qui non
> c'è nessuna misura nuova, e nemmeno una riga eseguita. Quel che c'è è il codice, che dice **che cosa
> è possibile** — e in tre punti dice che **una nostra misura del 7 agosto guardava la cosa sbagliata**
> (§5.1 e §15). Prima di spostare un numero nei documenti si rifà la misura.

---

### 1. In due minuti

Le **quattro domande** che `PIANO.md` fase 11 e la memoria di progetto chiedevano di chiudere prima
di progettare qualunque cosa, con la risposta che il codice dà:

| # | La domanda | La risposta |
|---|---|---|
| **1** | **Come si ottiene il permesso della cattura, per un servizio non presidiato?** | ✅ **Un file `.desktop` con `X-KDE-Wayland-Interfaces`.** Nessun dialogo, nemmeno la prima volta; sopravvive a riavvio e logout; nessuna patch. È il meccanismo con cui si autorizzano il portale di KDE e `krfb-virtualmonitor` (§3). ✅ **MISURATO il 7 agosto — funziona**, e con un requisito in più che il codice non mostrava: **`XDG_MENU_PREFIX=plasma-`** nell'ambiente, o l'indice dei servizi resta vuoto e il cancello non si apre (§3.3-bis) |
| **2** | **KWin senza monitor può disegnare sulla GPU?** | ✅ **Sì**, e ora **misurato**, non solo letto: `renderD129` aperto, `libEGL_mesa`+`libgbm` caricate, `zwp_linux_dmabuf_v1` v4 annunciato. **La nostra misura del 7 agosto («zero nodi DRM, nessuna libreria GL») era sbagliata nell'etichetta: R32 va corretta** (§5.1) |
| **3** | **Come si avvia una sessione Plasma senza monitor?** | ✅ Ambiente da zero con **due** variabili obbligatorie (**più `XDG_MENU_PREFIX`, vedi la domanda 1**), unità del compositore sovrascritta, `startplasma-wayland`. Più semplice di GNOME. Con **due vincoli duri**: `--xwayland` non è opzionale, e `--virtual` non sa creare output a richiesta (§6). ⛔ **E `--virtual` non è più una scelta**: `--drm` da una sessione senza seat non parte [M] (§5.2) |
| **4** | **Per quale strada passa l'input?** | ✅ **libei**, con una sola chiamata D-Bus a KWin e **senza alcun controllo di permesso**. `SPECIFICA.md` §3.8 («protocollo `kde-fake-input`») è superata dal codice: `fake_input` è la strada vecchia (§7). ✅ **MISURATO**: `connectToEIS(7)` da una shell SSH qualunque → `(handle 0, 1)` |

E le **undici domande al compositore nuovo** di `LEZIONI.md` §3, con la colonna di KWin riempita
da questo studio. Le celle marcate `[?]` sono quelle che il codice non decide.

| # | La domanda | Mutter 48.7 | **KWin 6.3.6** |
|---|---|---|---|
| 1 | Come si chiede la cattura senza portale? | D-Bus `org.gnome.Mutter.ScreenCast` | protocollo Wayland `zkde_screencast_unstable_v1` **v5** [R] |
| 2 | Spinge i fotogrammi o li fa tirare? | spinge (PipeWire) | **spinge** (PipeWire), e frena lui sul `maxFramerate` [R] |
| 3 | Il protocollo è dietro un permesso? | no | **sì**, e il permesso è **un campo di un file `.desktop`** [R] — **+ `XDG_MENU_PREFIX`** [M, 7 ago] |
| 4 | Senza monitor, disegna sulla GPU? | sì | **sì** [R] **e misurato** [M, 7 ago]: render node aperto, EGL/gbm, dmabuf v4 |
| 5 | Si può chiedere uno schermo virtuale della misura voluta? | sì, `RecordVirtual` | **sì**, `stream_virtual_output` — ma **solo col backend `--drm`** [R] |
| 6 | Quanto consegna, con una scena che cambia a ogni ridisegno? | ~37 su 60 | **59–60** [M, 7 agosto] — misurato però con `--virtual` + `stream_output`, non nella configurazione del prodotto |
| 7 | La cadenza dichiarata come si comporta? | sei decimi, oltre 60 non sale, **fissa rifiutata** | `framerate` **deve** essere `0/1`; il tetto è `maxFramerate`, **onorato lato server** con aritmetica intera in ms [R] |
| 8 | Consegna fotogrammi interi o «diff»? | **a copia zero è un diff** | **interi, sempre** [R] — il difetto di R29 non si ripresenta |
| 9 | Il buffer arriva già disegnato? | **no**: il 100 % col disegno in corso | **sì**: KWin fa `glFlush()`, o `glFinish()` su NVidia e llvmpipe [R] |
| 10 | Che cosa costa la risoluzione? | niente fino a 4K | niente [M] |
| 11 | Che cosa costa la profondità di colore? | niente | niente; `BGRx` è negoziabile [R] |

> #### ⭐ E su KDE **esiste un `gnome-remote-desktop`**: si chiama `KRdp`
>
> *Trovato la sera del 7 agosto, dopo una domanda dell'utente. La prima stesura di questo documento
> diceva che in KDE non c'era traccia di RDP, e sbagliava (§12.0).*
>
> Server RDP di KDE, **C++ su FreeRDP + kpipewire**, 4 222 righe nella versione di Trixie. Conferma
> per intero la risposta alla domanda 1 — il suo `.desktop` dichiara
> `X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1` — e conferma **i due
> codec**, **il regolatore a fotogrammi in volo dall'RTT**, **i bordi esclusivi delle regioni** e
> **TLS puro quando si autentica con PAM**. Non risolve invece le due cose che restano nostre:
> **non avvia la sessione** (vive dentro Plasma) e **non ridimensiona lo schermo virtuale**.
>
> ⛔ **E `xrdp` non c'entra**: non ha alcun percorso Wayland — lancia un `Xorg` o un `Xvnc` e dentro
> ci fa girare la sessione **X11** di Plasma (§12.3). Non ha risolto il nostro problema: l'ha evitato.

**Il quadro in una riga**: su KDE la cattura è **più semplice e più sana** che su GNOME (fotogrammi
interi, sincronizzazione fatta dal compositore), l'input è **più corto** (una chiamata D-Bus,
nessun permesso), la sessione è **più prevedibile** (nessun `ConditionEnvironment`, il bus non muore)
— e in cambio **la risoluzione dinamica non c'è**: un output virtuale di KWin non si ridimensiona, e
va chiuso e rifatto (§8).

> #### ⛔ «CURSORE FUORI DAL PERCORSO DEL CODIFICATORE» ERA SCRITTO QUI, ED È FALSO CON `--virtual`
>
> *[M, 8 agosto 2026, e l'ha visto l'utente al primo uso: «non c'è la scia, ma è quello di KDE che
> segue quello vero» — cioè **due puntatori**.]*
>
> Il modo cursore `Metadata` governa se lo screencast **aggiunge** un cursore, non se la scena ne
> contiene già uno. E con il backend `--virtual` ne contiene sempre uno:
>
> | | |
> |---|---|
> | `compositor_wayland.cpp:573-608` | se il backend non ha un piano cursore, `hardwareCursor` resta falso e il **cursorLayer software** viene reso visibile |
> | `backends/virtual/` | ⛔ **non definisce `cursorLayer()`** [✗]: il backend virtuale un piano cursore non ce l'ha |
> | `virtual_egl_backend.cpp:187-194` | `textureForOutput` restituisce il **framebuffer dell'uscita**, cioè quello in cui il cursorLayer è stato dipinto |
> | `pointer_input.cpp:99-108` | e KWin lo mostra appena esiste un dispositivo di puntamento sul seat — il nostro, di libei |
>
> **Non c'è alcuna leva per impedirlo**: `Cursors::hideCursor()` è interna e la chiamano solo
> `pointer_input` e `hide_cursor_spy`; nessun protocollo, nessun D-Bus. Chiedere il modo `Hidden` non
> cambierebbe niente. Con il backend `--drm` — che §5.2 ha escluso — ci sarebbe un piano cursore e il
> problema non esisterebbe.
>
> ✅ **L'unica cura è dall'altra parte**: si dice al **client** di nascondere il proprio puntatore,
> con `SYSPTR_NULL`, che è RDP di base. Il prezzo è che il puntatore si muove alla latenza del
> **video** invece che a quella della rete — su una LAN è un fotogramma.
>
> ⚠ **E su Mutter NON si fa**: là il cursore è davvero fuori dall'immagine, e nascondere quello del
> client lascerebbe l'utente senza alcun puntatore. È una differenza fra compositori, non una
> preferenza.
>
> #### ⛔ E la cura funziona su due client su tre — non su tutti
>
> *[M, 8 agosto 2026, giudizio dell'utente su xfreerdp e su RDM]*
>
> | client | esito |
> |---|---|
> | **xfreerdp** | ✅ un puntatore solo, quello di KDE |
> | **RDM (Android)** | ⛔ **restano due**, pur avendo il server dichiarato e il client **accettato** il PDU (`14:02:28 puntatore del client nascosto`, cioè `PointerSystem()` ha risposto vero) |
>
> La spiegazione è che il secondo puntatore di RDM **non è il puntatore RDP**: è il *touch pointer*
> che l'applicazione disegna sopra la propria finestra per rendere usabile un desktop col dito.
> Vive fuori dal protocollo, e **nessun server può toglierlo** — si spegne solo dalle impostazioni
> del client, passando alla modalità mouse.
>
> ⚠ Da cui la regola generale: `SYSPTR_NULL` toglie il puntatore che il client disegna **per conto
> del protocollo**, non ogni pixel a forma di freccia. È l'ennesima forma della regola dei tre
> client (`LEZIONI.md` §2.1): la stessa riga di codice dà tre esiti.
>
> #### ⭐ E allora la cura giusta è l'opposta: il cursore di KDE si rende TRASPARENTE
>
> *[M, 8 agosto 2026, dopo che l'utente ha chiesto di chiudere il punto sul serio]*
>
> Il ragionamento di sopra è giusto e la conclusione era corta. Vero che con `--virtual` KWin
> disegna il cursore dentro l'immagine e che non c'è leva per impedirglielo — **ma non serve
> impedirglielo: basta che quel che disegna non si veda.**
>
> KWin prende il tema del cursore da **`XCURSOR_THEME`, e lo guarda solo se c'è anche
> `XCURSOR_SIZE`** (`cursor.cpp:134-145`: `if (!themeName.isEmpty() && ok)`). L'ambiente della
> sessione lo componiamo noi. Quindi: un tema con un cursore **1×1 ad alfa zero**, scritto in
> `$XDG_RUNTIME_DIR/remotix/icons/` e indicato con `XCURSOR_PATH`, e il puntatore torna a essere
> **quello che il client disegna da sé — come su Mutter**, alla latenza della rete invece che del
> video, e **uno solo su ogni client**, compresi quelli che se lo disegnano per conto proprio.
>
> ✅ **Misurato**: `XCURSOR_THEME=remotix-invisibile`, `XCURSOR_SIZE=24` e `XCURSOR_PATH` presenti
> nell'ambiente di `kwin_wayland` (letto da `/proc/<pid>/environ` con `sudo`, §del binario non
> dumpable), **68 forme scritte**, file `Xcur v1.0 1×1 alfa 0` di 68 byte, e **nessuna riga
> «Failed to load cursor theme»** nel journal dell'unità del compositore.
>
> ⛔ **Il tema deve caricarsi davvero.** Se `CursorTheme` risulta vuoto KWin **ripiega sul tema
> predefinito** (`pointer_input.cpp:1183-1196`), cioè sul cursore visibile: un tema con zero forme
> non nasconde niente, lo *rimette*. Per questo le forme si scrivono tutte, e per questo il controllo
> che vale è l'assenza del ripiego, non la presenza dei file.
>
> ⚠ **Il prezzo**: si perde il cambio di forma — la I sul testo, le frecce di ridimensionamento —
> esattamente come su GNOME oggi. Restituirlo significa mandare la forma vera sul **canale puntatore
> di RDP**, prendendola dai metadati PipeWire che già chiediamo (modo `Metadata`): è un lavoro a sé,
> e vale per tutti e due i compositori.
>
> Da cui `compositore_cursore_nell_immagine()` **è tornata falsa anche su KWin**, e `SYSPTR_NULL`
> non si manda più. La funzione resta scritta: il giorno in cui un compositore disegnasse il cursore
> nell'immagine **senza** lasciarci cambiare il tema, la risposta è lì e non va ritrovata da capo.

---

### 2. La mappa: dove sta ciascuna cosa

| Che cosa | Dove, in `reference-kde/` |
|---|---|
| Il protocollo di cattura, lato Wayland | `kwin/src/wayland/screencast_v1.{h,cpp}` — solo segnali Qt |
| Il motore della cattura | `kwin/src/plugins/screencast/` — `screencastmanager.cpp`, `screencaststream.cpp` (1000 righe), `outputscreencastsource.cpp`, `regionscreencastsource.cpp`, `screencastbuffer.cpp` |
| Il filtro dei permessi | `kwin/src/wayland_server.cpp:127-193`, `kwin/src/utils/serviceutils.h`, `kwin/src/utils/executable_path_proc.cpp` |
| L'input moderno (libei) | `kwin/src/plugins/eis/` — `eisbackend.cpp`, `eiscontext.cpp`, `eisdevice.cpp` (1829 righe) |
| L'input vecchio | `kwin/src/backends/fakeinput/fakeinputbackend.cpp` |
| I backend di uscita | `kwin/src/backends/{drm,virtual,wayland,x11}/` |
| Gli output e la loro configurazione | `kwin/src/core/output.{h,cpp}`, `kwin/src/wayland/outputmanagement_v2.cpp`, `kwin/src/core/outputconfigurationstore.cpp` |
| Gli appunti | `kwin/src/wayland/datacontrol*_v1.cpp`, `kwin/src/wayland/seat.cpp`, `kwin/src/xwayland/clipboard.cpp`, `plasma-workspace/klipper/` |
| L'avvio della sessione | `plasma-workspace/startkde/startplasma{,-wayland}.cpp`, `startkde/systemd/*.target`, `kwin/plasma-kwin_wayland.service.in`, `kwin/src/helpers/wayland_wrapper/kwin_wrapper.cpp` |
| Il logout | `plasma-workspace/startkde/plasma-shutdown/shutdown.cpp`, `plasma-workspace/ksmserver/{logout,server}.cpp`, `kwin/src/sm.cpp` |
| Energia e inibizioni | `powerdevil/daemon/powerdevilpolicyagent.cpp`, `powerdevil/daemon/powerdevilsettingsdefaults.cpp` |
| Il consumatore PipeWire di KDE, con encoder | `kpipewire/src/` — `pipewiresourcestream.cpp`, `pipewireproduce.cpp`, `h264vaapiencoder.cpp`, `vaapiutils.cpp` |
| Il desktop remoto di KDE | `krfb/framebuffers/pipewire/pw_framebuffer.cpp`, `krfb/events/xdp/xdpevents.cpp` |

---

### 3. ⛔ Il cancello: come KWin decide chi può catturare

È la risposta alla **prima** domanda della fase, e conviene metterla prima di tutto il resto perché
condiziona ogni prova: **finché il cancello è chiuso, il sintomo è «questo compositore non espone il
protocollo», e non arriva alcun errore.**

#### 3.1 Il meccanismo, per intero

**[R]** KWin installa un filtro globale di libwayland — `wl_display_set_global_filter`
(`kwin/src/wayland/filtered_display.cpp:44`) — e `KWinDisplay::allowInterface()`
(`kwin/src/wayland_server.cpp:146-192`) nega il bind di **sei** interfacce a chi non le dichiara.
La lista nera, `wayland_server.cpp:129-136`:

```cpp
const QSet<QByteArray> interfacesBlackList = {
    QByteArrayLiteral("org_kde_plasma_window_management"),
    QByteArrayLiteral("org_kde_kwin_fake_input"),
    QByteArrayLiteral("org_kde_kwin_keystate"),
    QByteArrayLiteral("zkde_screencast_unstable_v1"),      // ← la cattura
    QByteArrayLiteral("org_kde_plasma_activation_feedback"),
    QByteArrayLiteral("kde_lockscreen_overlay_v1"),
};
```

Se il filtro nega, **il global non viene nemmeno annunciato nel registry**: il client vede un
compositore senza quel protocollo. Il diagnostico esiste ma è `qCDebug`, spento per difetto
(`wayland_server.cpp:184`).

Il criterio **non** è uid, non è pid, non è polkit, non è un elenco in `kwinrc`. È una catena di
tre passi, tutti **[R]**:

1. `SO_PEERCRED` sul socket del client → pid;
2. pid → `/proc/<pid>/exe`, risolto canonicamente (`kwin/src/utils/executable_path_proc.cpp:11-14`);
3. si cercano **tutte** le applicazioni installate e si prende quella il cui **primo token di
   `Exec=`**, canonicalizzato, coincide con quel percorso (`kwin/src/utils/serviceutils.h:27-49`,
   via `KApplicationTrader::query`); di quella si legge il campo
   **`X-KDE-Wayland-Interfaces`** (`serviceutils.h:24`).

Autorizzato **solo** se quel campo contiene il nome esatto dell'interfaccia.

Le due scorciatoie: il client è KWin stesso (`client->processId() == getpid()`,
`wayland_server.cpp:152`), oppure `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` **nell'ambiente di KWin**
(`:168`, letta in una `static`), che apre **tutte e sei** le interfacce a **tutti** i client.

#### 3.2 I precedenti, cioè il modello da copiare

**[R]** Tutti nel sistema reale, tutti con lo stesso meccanismo:

| File `.desktop` | Interfacce dichiarate |
|---|---|
| `xdg-desktop-portal-kde/data/org.freedesktop.impl.portal.desktop.kde.desktop.in:49-51` | `org_kde_kwin_fake_input,org_kde_plasma_window_management,zkde_screencast_unstable_v1` |
| **`krfb/krfb/org.kde.krfb.virtualmonitor.desktop.cmake:84`** | `zkde_screencast_unstable_v1`, con `NoDisplay=true` — **è il nostro caso identico** |
| `plasma-workspace/shell/org.kde.plasmashell.desktop.cmake:76` | `…,zkde_screencast_unstable_v1,…` |
| `kpipewire/tests/org.kde.kpipewireheadlesstest.desktop.cmake:6` | `zkde_screencast_unstable_v1` |

E il messaggio che kpipewire stampa a se stesso quando il global manca dice esattamente dove
guardare: *«Remember requesting the interface on your desktop file:
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1»*
(`kpipewire/tests/screencasting.cpp:79`, `plasma-workspace/libtaskmanager/screencasting.cpp:44`).

#### 3.3 I tre punti fragili, tutti di confezionamento

1. ⛔ **REMOTIX non deve girare come root.** `/proc/<pid>/exe` di un processo di **altro uid** non è
   leggibile, `executablePath()` torna vuoto, e `wayland_server.cpp:170-173` **nega**. Va eseguito
   come servizio dell'utente — che è comunque quel che §3.4 di `SPECIFICA.md` prescrive.
2. ⛔ **`Exec=` deve nominare l'eseguibile che apre il socket**, non un lanciatore di shell: il
   confronto è sul percorso canonico del binario vero.
3. ✅ **`kbuildsycoca6` non serve, e non serve riavviare KWin.** [R, `kf6-kservice 6.13.0-1`, la
   versione di Trixie] `ensureCacheValid()` ricostruisce la cache **dentro il processo di KWin**, con
   un limite di frequenza di **1 500 ms** (`ksycoca_ms_between_checks`). Quindi un `.desktop`
   installato è visibile entro un secondo e mezzo — e *Sunshine*, che se lo scrive a runtime, aspetta
   **3 000 ms** per prudenza (§12.4).
4. ⛔ **Il quarto punto fragile, e rompe tutto in silenzio**: `serviceutils.h:35` prende
   `servicesFound.first()`, e il bug KDE **446628** (confermato dal 2021) mostra che **un `.desktop`
   d'utente omonimo ombreggia quello di sistema** — se quello che vince non ha il campo, il permesso
   è negato senza un errore. E contano gli `XDG_DATA_DIRS` **di KWin**, non i nostri: la §6.1
   prescrive di comporre l'ambiente da zero, quindi il file va installato dove **il compositore**
   guarda.

#### 3.3-bis ⭐ MISURATO — il cancello si apre, ma dipende da `XDG_MENU_PREFIX`

> **[M] Misura M1, banco del 7 agosto 2026, KWin 6.3.6-1 e kf6-kservice 6.13.0-1.**
>
> **Il meccanismo di §3.1 funziona**: con un `.desktop` che dichiara
> `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1` e `NoDisplay=true` — la forma di KRdp e di
> krfb — KWin annuncia il global e la cattura parte. Nessun dialogo, nessun portale, come previsto.
>
> **Ma prima di funzionare ha negato per cinque volte, e la causa non è nulla di ciò che §3.3
> elenca.** Il diniego era questo, e il documento va letto con questa aggiunta:
>
> ⛔ **`kbuildsycoca6` non indicizza nulla se `XDG_MENU_PREFIX` non è impostata.** L'indice dei
> servizi si costruisce a partire da `${XDG_MENU_PREFIX}applications.menu`, e Debian **non installa
> `/etc/xdg/menus/applications.menu`**: installa `plasma-applications.menu` e
> `kf5-applications.menu`. Senza il prefisso, `kbuildsycoca6` esce con **stato 0** dicendo soltanto
> `"applications.menu" not found in QList("/etc/xdg/menus")`, e `KApplicationTrader::query` non
> trova **nessuna** applicazione — nemmeno le 133 di sistema.
>
> La prova, nella dimensione della cache: **226 275 byte** senza il prefisso, **379 292** con
> `XDG_MENU_PREFIX=plasma-`. E il verdetto di KWin passa da
>
> ```
> KWIN_UTILS: Could not find the desktop file for "…/nodo-kwin"
> kwin_core:  Interface "zkde_screencast_unstable_v1" not in X-KDE-Wayland-Interfaces of "…/nodo-kwin"
> ```
> a
> ```
> KWIN_UTILS: Interfaces found for "…/nodo-kwin" "X-KDE-Wayland-Interfaces" : QList("zkde_screencast_unstable_v1")
> ```
>
> ✅ **In una sessione Plasma vera il problema non si vede**, perché `startplasma` imposta la
> variabile da sé: `qputenv("XDG_MENU_PREFIX", "plasma-")`
> (`plasma-workspace/startkde/startplasma.cpp:366`). **Riguarda noi** perché §6.1 prescrive di
> comporre l'ambiente da zero: se la componiamo senza quella variabile, il cancello resta chiuso e
> il sintomo è quello di §3 — «il compositore non espone il protocollo».
>
> ⛔ **E c'è una fragilità che va scritta**: il nome del file di cache **non** dipende dal prefisso
> (`ksycoca6_<locale>_<hash>`, e l'hash è lo stesso nei due casi). Quindi un qualunque processo che
> ricostruisca l'indice **senza** il prefisso sovrascrive quello buono, e il permesso torna a essere
> negato **a KWin già avviato** — un guasto intermittente, senza messaggi. Chi confeziona il
> servizio esporta `XDG_MENU_PREFIX=plasma-` nell'ambiente di **tutto** l'albero della sessione.
>
> **Come si diagnostica in tre secondi**, che è la cosa da ricordare: la riga che dice la causa sta
> nella categoria **`KWIN_UTILS`**, non in `kwin_core` (`kwin/src/utils/serviceutils.h:40,46`), e si
> accende con `QT_LOGGING_RULES='KWIN_UTILS.debug=true'`. Le due righe hanno cure opposte:
> *«Could not find the desktop file»* = l'indice non associa (questo caso); *«Interfaces found … :
> ()»* = associa, e manca il campo.
>
> Altri due fatti misurati, che escludono le spiegazioni comode: il diniego era identico per un
> cliente in **`/usr/bin`** (`wayland-info`) e per il nostro su `/media` — quindi **non** era il
> montaggio, e **non** era `NoDisplay`, né le virgolette in `Exec`, né un argomento in `Exec`: tutte
> e cinque le varianti negate, tutte con la stessa riga.

> #### ✅✅ E il cancello si apre anche DENTRO una sessione Plasma vera
>
> **[M] 8 agosto 2026.** La prova di §3.3-bis era su un `kwin_wayland` nudo. Ripetuta dentro una
> sessione avviata con `startplasma-wayland` (la ricetta di §6.1), con lo stesso `.desktop`:
>
> ```
> KWIN_UTILS: Interfaces found for "…/nodo-kwin" "X-KDE-Wayland-Interfaces" : QList("zkde_screencast_unstable_v1")
> ⇒ zkde_screencast annunciato, e un flusso vero: nodo PipeWire 55
> ```
>
> Quindi la catena intera — sessione Plasma, permesso, cattura, flusso PipeWire — **è verificata sul
> campo**. Nella stessa sessione KWin scrive 13 righe `Interfaces found for …`, fra cui quelle del
> portale di KDE con le sue tre interfacce: cioè si vede il meccanismo funzionare anche per gli altri.
>
> ⛔ **MA una cosa lo rompe, e va scritta perché la si incontra proprio confezionando il servizio:
> `InaccessiblePaths=` nell'unità del compositore chiude il cancello.** Serviva a scegliere la GPU
> (§5.6) e ha questo effetto collaterale: con quella riga il global **non** viene annunciato, e KWin
> **non arriva nemmeno a interrogare l'indice** — **0 righe `KWIN_UTILS` contro 13** nello stesso
> ambiente. Non è la visibilità dei file: dentro il namespace, `nsenter` mostra il `.desktop` e la
> cache `ksycoca6_en_…` presenti e leggibili; e non è `/proc`, che è montato normalmente e mostra gli
> altri processi. Il meccanismo esatto **non è stato dimostrato** (l'ipotesi residua è la prima
> condizione di `allowInterface()`: `executablePath()` vuoto ⇒ nega, `wayland_server.cpp:170-173`).
>
> **La regola che ne segue è comunque netta**: l'unità del compositore **non si irrigidisce con
> namespace di monti** (`InaccessiblePaths`, e per prudenza tutto ciò che implica `PrivateMounts`).
> Quel che serve si ottiene altrimenti — per la GPU, coi permessi del nodo (§5.6).

#### 3.4 Chi è protetto e chi non lo è — la tabella che conta

**[R]** Il modello dei permessi di KWin 6.3.6 è **incompleto**, e per noi è una fortuna. Riassunto
per tutto ciò che ci serve:

| Ci serve per | Interfaccia / oggetto | Protetto? |
|---|---|---|
| cattura + output virtuale | `zkde_screencast_unstable_v1` | **sì** — `.desktop` con `X-KDE-Wayland-Interfaces` |
| **input** | `org.kde.KWin.EIS.RemoteDesktop` (D-Bus) | **NO, nessun controllo** (`kwin/src/plugins/eis/eisbackend.cpp:70`, `ExportAllInvokables`) |
| input, strada vecchia | `org_kde_kwin_fake_input` | **sì**, stessa via `.desktop` — e il suo `authenticate` non autentica nulla (`fakeinputbackend.cpp:107-113`, `// TODO: make secure`) |
| **appunti** | `zwlr_data_control_manager_v1` | **NO** (`wayland_server.cpp:386`, non in lista nera) |
| leggere/scrivere il layout schermi | `kde_output_device_v2`, `kde_output_management_v2` | **NO** |
| stato dei tasti a scatto | `org_kde_kwin_keystate` | **sì**, stessa via `.desktop` |
| catture singole | `org.kde.KWin.ScreenShot2` | **sì**, via `X-KDE-DBUS-Restricted-Interfaces` (`screenshotdbusinterface2.cpp:331-355`) — **unico oggetto D-Bus protetto in tutto KWin** |

**Da cui la ricetta di confezionamento**: un solo `.desktop`, che dichiara
`zkde_screencast_unstable_v1` (per la cattura) e — se e quando serviranno — `org_kde_kwin_keystate`
e `org_kde_kwin_fake_input`. L'input via EIS non ne ha bisogno.

> ⚠ **Un buco che non useremo, ma che dice com'è fatto il modello.** [R]
> `wp_security_context_manager_v1` **non è in lista nera** (`wayland_server.cpp:378`): un client
> qualunque può dichiarare come `app_id` il nome del `.desktop` di qualcun altro e riconnettersi
> ottenendo l'autorizzazione (`wayland_server.cpp:121-127` + `display.cpp:282-297`, e
> `serviceutils.h:51-58` che per i client in sandbox usa `KService::serviceByDesktopName`).
> Il modello è **dichiarativo**, non impositivo. La variante *legittima* di questa via — dichiarare
> il **proprio** app-id — è l'unica scappatoia se un giorno il vincolo su `Exec=` ci fosse scomodo.

#### 3.5 Le vie che NON prendiamo, e perché va scritto

| Via | Esito |
|---|---|
| **Il portale con `restore_token`** | implementato (`xdg-desktop-portal-kde/src/screencast.cpp:222-279`), ma **il primo consenso è un dialogo modale** (`:272`), il token identifica il monitor per **posizione** (`outputsmodel.cpp:93-94`) e se non risolve **ricompare il dialogo**. Per un servizio non presidiato: **no** |
| **La «mega-autorizzazione» di KDE** | esiste e è documentata nel commento: *«Particularly useful for headless setups and when the user is not physically at the machine»* (`xdg-desktop-portal-kde/src/remotedesktop.cpp:34-71`, usata a `:227` per **saltare del tutto il dialogo**). ✅ **E si scrive**, contro quel che diceva la prima stesura di questo documento: `flatpak permission-set kde-authorized remote-desktop <app-id> yes` — documentato in `xdg-desktop-portal-kde!326`, unita nel **gennaio 2025, milestone 6.3: c'è già in Trixie** [I]. Per un'applicazione non in sandbox l'`app-id` viene dal **nome dell'unità systemd** (`app-<app-id>.service`), quindi REMOTIX può averne uno. Resta il **piano B** — passa comunque dal portale — ma ora è verificato, non congetturato |
| `zwlr_screencopy_manager_v1`, `ext_image_copy_capture_v1` | ⛔ **non esistono in KWin 6.3.6**: non sono filtrati, sono **assenti** [✗]. Della famiglia wlroots KWin implementa solo `wlr-layer-shell` e **`wlr-data-control`** |
| `org.kde.KWin.ScreenShot2` | **uno scatto per chiamata**, immagine cruda su una pipe. Nessuna continuità, nessun output virtuale: non serve |
| `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` | è la scorciatoia con cui abbiamo misurato (`banco/banco-altri.sh:33`). Da banco, non da prodotto — e apre anche `fake_input` a chiunque |

---

### 4. La cattura: `zkde_screencast_unstable_v1`

#### 4.1 Le due metà, e la versione

**[R]** Il protocollo è un guscio di segnali Qt (`kwin/src/wayland/screencast_v1.cpp`), il motore è
un **plugin** (`kwin/src/plugins/screencast/`, `EnabledByDefault: true`, caricato solo in modalità
Wayland, `main.cpp:28-35`).

**KWin 6.3.6 annuncia la versione 5** (`screencast_v1.cpp:18`, `static int s_version = 5`), anche
se compilato contro un `plasma-wayland-protocols` che dichiara la 6. Il nostro
`banco/zkde-screencast-unstable-v1.xml` **è la copia giusta**: è la v5, e l'unica differenza dal
master è l'evento `serial` aggiunto nella 6.

#### 4.2 Le richieste

**[R]** `screencast_v1.cpp:89-142`:

| Richiesta | `since` | Argomenti | Note |
|---|---|---|---|
| `stream_output` | 1 | `new_id`, `wl_output`, `pointer` | cattura un'uscita esistente |
| `stream_window` | 1 | `new_id`, `window_uuid`, `pointer` | una finestra |
| **`stream_virtual_output`** | 2 | `new_id`, `name`, `width`, `height`, `scale`, `pointer` | **fa creare l'uscita** — l'analogo di `RecordVirtual` |
| `stream_region` | 3 | `new_id`, `x`, `y`, `width`, `height`, `scale`, `pointer` | un rettangolo dello spazio di lavoro |
| `stream_virtual_output_with_description` | 4 | come sopra + `description` | la descrizione compare in kscreen |

`pointer` è l'enum del cursore, e **non è validato** (cast secco, `screencast_v1.cpp:91`):

| Valore | Modo | Effetto |
|---|---|---|
| 1 | `Hidden` | nessun cursore |
| 2 | `Embedded` | disegnato nel buffer |
| **4** | **`Metadata`** | come `SPA_META_Cursor`, fuori dall'immagine |

Vanno mandati esattamente 1, 2 o 4: con 0 o 3 nessun `case` corrisponde ma il flag del contenuto
viene comunque alzato — stato incoerente.

#### 4.3 `stream_virtual_output`, in dettaglio

**[R]** `screencastmanager.cpp:56-68`:

```cpp
auto output = kwinApp()->outputBackend()->createVirtualOutput(name, description, size, scale);
streamOutput(stream, output, mode);
connect(stream, &ScreencastStreamV1Interface::finished, output, [output] {
    kwinApp()->outputBackend()->removeVirtualOutput(output);
});
```

Cioè: **l'uscita vive quanto lo stream**. Sul backend DRM diventa una `DrmVirtualOutput`
(`drm_backend.cpp:340-347`), e da lì discendono cinque fatti che pesano su tutto il resto:

| | **[R]** |
|---|---|
| Il nome dell'uscita diventa **`"Virtual-" + name`** | `drm_virtual_output.cpp:32`. È l'**unico** modo per ritrovare il proprio `wl_output`: il protocollo non dice al client quale uscita ha creato. `wl_output` è annunciato a **v4**, che ha `name` (`kwin/src/wayland/output.cpp:24,159`) |
| **Un solo modo**, della misura chiesta, a **60000 mHz fissi** | `drm_virtual_output.cpp:28`. Da qui l'impossibilità di ridimensionare (§8) |
| `width`/`height` sono i **pixel** del modo | l'XML li chiama «logical»; `scale` finisce solo nella geometria logica (`core/output.cpp:457-459`). **Si passa `scale = 1` e la misura in pixel**: `DrmVirtualOutput` usa la misura tale e quale, mentre il backend annidato fa `size * scale` (`wayland_backend.cpp:567`) — due interpretazioni diverse nello stesso protocollo |
| La cadenza è un **`SoftwareVsyncMonitor`**, cioè un `QTimer` a granularità di millisecondo | `drm_virtual_output.cpp:24,51-56`; `softwarevsyncmonitor.cpp:44-56`. **È il tetto strutturale a ~60 fps**, e la sua irregolarità |
| **Nessuna validazione della misura** | `screencast_v1.cpp:98-112` passa due `int32` grezzi: nessun minimo, nessun massimo, nessun rifiuto dei negativi (`stream_region`, per confronto, almeno controlla `isValid()`). **[?]** che cosa fa con 0×0 o 16384² va misurato |

#### 4.4 Il nodo PipeWire, e perché la trappola di Mutter qui non esiste

**[R]** La catena: richiesta → `integrateStreams()` collega **prima** i tre segnali e **poi** chiama
`init()` (`screencastmanager.cpp:131-145`) → `pw_stream_connect(... PW_DIRECTION_OUTPUT,
PW_STREAM_FLAG_DRIVER | PW_STREAM_FLAG_ALLOC_BUFFERS ...)` → allo stato `PAUSED` KWin legge l'id del
nodo e lo annuncia una volta sola (`screencaststream.cpp:126-131`) → evento `created`.

**La trappola numero 2 di `LEZIONI.md` §4 — «ci si iscrive all'annuncio del nodo prima di avviare
il flusso» — su KDE non può presentarsi.** Su Mutter l'annuncio è un broadcast D-Bus su un oggetto
creato dal server, e chi si iscrive tardi perde qualcosa di già passato. Qui l'oggetto
`zkde_screencast_stream_unstable_v1` ha un **id allocato dal client nella stessa richiesta**: gli
eventi finiscono nella coda della connessione e arrivano al primo dispatch. Basta registrare il
listener prima di `wl_display_dispatch` — e `banco/nodo-kwin.c:142-143` lo fa già.

⚠ **Ma `failed` è sincrono** (`screencastmanager.cpp:82,141-144`): chi non ha il listener attivo lo
perde e aspetta per sempre. **Serve un timeout comunque.**

**[R]** L'id del nodo **non cambia** per tutta la vita del flusso, comprese le rinegoziazioni di
formato e i cambi di misura.

#### 4.5 Il formato, riga per riga

**[R]** `screencaststream.cpp:735-783`. KWin propone **fino a tre** `SPA_PARAM_EnumFormat`:
DMA-BUF con un solo modificatore (dopo la fissazione), DMA-BUF con l'intera lista
(`MANDATORY | DONT_FIXATE`), e **memoria condivisa** senza la proprietà `modifier`.

| Campo | Valore | Nota |
|---|---|---|
| formato pixel | 11 corrispondenze DRM↔SPA; per output e regione il formato DMA-BUF è **sempre `DRM_FORMAT_ARGB8888`** | e per BGRA/RGBA KWin annuncia anche la variante senza alfa: **`BGRx` è negoziabile**, ed è quel che serve a RDP (`:775-783`) |
| `VIDEO_size` | rettangolo singolo della misura corrente | `resize()` lo aggiorna in banda (§8.3) |
| **`VIDEO_framerate`** | **`SPA_FRACTION(0,1)` fisso** | ⛔ chi propone una cadenza **fissa** diversa non trova intersezione: la stessa forma del vicolo cieco di Mutter, e la nostra opzione `--fissa` del banco **è inutilizzabile su KWin** |
| `VIDEO_maxFramerate` | `RANGE(default = refreshRate/1000, 1/1, refreshRate)` | **è il freno server-side**: KWin coalizza il danno e blitta a quel ritmo (`:507-516`) |
| buffer | **`RANGE(3, 2, 4)`** | il consumatore può stringere, non allargare. Il nostro banco chiede `RANGE(4,2,8)`: si intersecano su 2..4 |
| tipo di dato | `1 << SPA_DATA_DmaBuf` **oppure** `1 << SPA_DATA_MemFd` | mai un'unione; **`MemPtr` non è mai offerto**: il `mmap` lo fa il consumatore |

⚠ **L'aritmetica del freno è intera, in millisecondi** (`:507-516`): chiedendo 60 si ottiene un
intervallo di 16 ms (≈62 fps), chiedendo 30 si ottiene 33 ms (≈30,3). Il danno accumulato non si
perde.

⛔ **E se un modificatore fallisce, viene rimosso per sempre.** `onStreamParamChanged` prova ad
allocare davvero un buffer (`testCreateDmaBuf`, `:920-951`); se non riesce, quei modificatori
escono dalle offerte future (`:260-264`): un client che insiste non otterrà il DMA-BUF una seconda
volta.

**I metadati offerti**, sempre (`:196-217`):

| Meta | Dimensione |
|---|---|
| `SPA_META_Header` | `sizeof(spa_meta_header)` |
| `SPA_META_VideoDamage` | `RANGE(16 regioni, 1, 16)` |
| `SPA_META_Cursor` | bitmap fino a **256×256** |
| `SPA_META_SyncTimeline` | **solo con DMA-BUF** |

#### 4.6 ✅ Fotogrammi interi, non un «diff» — la differenza che conta

**[R]** `screencaststream.cpp:618` → `outputscreencastsource.cpp:63-80`:

```cpp
GLFramebuffer::pushFramebuffer(target);
outputTexture->render(textureSize());   // l'INTERA texture, sempre
GLFramebuffer::popFramebuffer();
```

Nessuno scissoring, nessun uso della regione danneggiata. Lo stesso per il ramo in memoria
(`screencastutils.h:42-77`) e per la regione. E la texture di partenza è essa stessa completa: il
layer dell'uscita ricicla uno swapchain con *damage journal* e **ripara ogni slot in base alla sua
età** prima di ridisegnarlo (`drm_virtual_egl_layer.cpp:76-88`,
`drm_egl_layer_surface.cpp:192-199`).

| | Mutter (misurato, R29) | **KWin 6.3.6** [R] |
|---|---|---|
| Contenuto del buffer prestato | **un *diff*** sul buffer riciclato | **fotogramma intero** |
| Buffer riciclati | 4 | 2–4, default 3 |
| Danno dichiarato | sì | sì, fino a 16 rettangoli, poi il *bounding rect* |

> ✅ **Ricaduta diretta sul difetto che tiene spenta la copia zero su GNOME.** La superficie di
> accumulo di R29 **non serve su KWin**: il danno serve a non ricodificare quel che non è cambiato,
> non a ricostruire il fotogramma. Chi porta la cattura su KDE non eredita quel debito.

Il danno arriva già **in pixel** (`outputscreencastsource.cpp:92-97`), e la lista è chiusa da una
regione sentinella `SPA_REGION(0,0,0,0)` (`:703-728`).

#### 4.7 ⛔ La trappola vera: i buffer «corrotti» del cursore

**[R]** `screencaststream.cpp:659-664`:

```cpp
if (effectiveContents & Content::Video) {
    spa_data->chunk->flags = SPA_CHUNK_FLAG_NONE;
} else {
    // in pipewire terms, corrupted means "do not look at the frame contents" and here they're empty.
    spa_data->chunk->flags = SPA_CHUNK_FLAG_CORRUPTED;
}
```

In modo cursore `Metadata`, **ogni movimento del puntatore** produce un buffer senza
`m_source->render()` (`:447-451`, `:590-596`): dentro ci sono i pixel **stantii** di due-quattro
fotogrammi prima, e l'unica indicazione è quel flag.

> ⛔ **È l'analogo funzionale della trappola di Mutter, in una veste nuova**: un consumatore che
> ignora `chunk->flags` mostra un fotogramma vecchio **a ogni movimento del mouse**. kpipewire lo
> gestisce (`kpipewire/src/pipewiresourcestream.cpp:618-621`); **`banco/misura-cattura.c` no**, e li
> conta come fotogrammi consegnati — cioè la nostra misura di fps su KWin è gonfiabile muovendo il
> mouse. Su un desktop non presidiato il mouse è fermo e le misure del 7 agosto probabilmente
> reggono, ma il conteggio va reso onesto prima di rimisurare.

#### 4.8 ✅ La sincronizzazione: **la fa KWin**, e spiega un nostro vicolo cieco

**[R]** `screencaststream.cpp:637-655`. Con explicit sync attivo KWin **non aspetta** il
completamento GPU e mette i punti in `acquire_point`/`release_point`; senza, fa **`glFlush()`** — e
**`glFinish()` su NVidia e llvmpipe**, con il commento *«Implicit sync is broken on Nvidia and with
llvmpipe»*.

> ⛔ **`LEZIONI.md` §8 registra come vicolo cieco «aspettare la *fence* implicita del DMA-BUF: non
> cambia niente, è quella sbagliata».** Il codice di KWin dice il perché in generale: **non c'è
> alcuna fence implicita da aspettare se chi disegna non l'ha messa.** La domanda giusta da fare a
> Mutter non è «la fence è pronta?» ma «Mutter fa il flush?». È un'ipotesi nuova su un difetto che
> avevamo lasciato aperto, e non costa niente verificarla.

**Il contratto di `SPA_META_SyncTimeline`, che non stava da nessuna parte** [R]
(`screencastbuffer.cpp:86-107`, `screencaststream.cpp:534-537`, `606-613`, `639-647`):

- due `spa_data` in più, di tipo `SPA_DATA_SyncObj`, agli indici `planeCount` e `planeCount+1`,
  **con lo stesso fd**; `blocks = planeCount + 2`;
- `acquire_point` e `release_point` nel metadato;
- il produttore **non riusa il buffer** finché il `release_point` non è materializzato;
- KWin propone **due** `SPA_PARAM_Buffers`: il primo con `metaType` `SPA_META_SyncTimeline` marcato
  `MANDATORY`, il secondo di ripiego «per implicit sync o MemFd». **Chiedere la timeline è una
  scelta deliberata del consumatore**, non un caso.

Per REMOTIX: l'implicit sync è la strada corta e basta, perché KWin fa il flush. L'explicit è
un'ottimizzazione successiva.

> #### ⚠ MISURATO — «la fa KWin» va inteso alla lettera: **flush non è finish**
>
> **[M] 8 agosto 2026, con una scena in movimento** (`weston-simple-egl` a schermo intero) e il
> misuratore che interroga la fence implicita con `poll(POLLIN, 0)` sul descrittore del DMA-BUF —
> **lo stesso metodo con cui misurammo Mutter**, quindi i due numeri sono confrontabili:
>
> | percorso | fotogrammi | «disegno non finito» |
> |---|---|---|
> | **DMA-BUF** | 594 in 10,03 s | **830 su 830** |
> | in memoria (MemFd) | 435 in 10,03 s | **0** |
>
> ⛔ Cioè **su questa macchina il 100 % dei buffer DMA-BUF arriva con il disegno in corso.** Non
> contraddice §4.8: KWin fa `glFlush()`, che **sottomette** il lavoro alla GPU e non aspetta che sia
> finito (`glFinish()` lo fa **solo** su NVidia e llvmpipe — cioè proprio dove la fence implicita è
> rotta). Su AMD e su Intel, quindi, **la fence c'è ed è il consumatore che deve aspettarla.**
>
> ✅ **La buona notizia resta intatta, ed è un'altra**: i fotogrammi sono **interi** (§4.6), quindi il
> difetto di R29 — il «diff» su buffer riciclati, che ci ha fatto spegnere la copia zero su GNOME —
> **non si ripresenta**. Su KDE la copia zero richiede *una* cosa: aspettare la fence prima di
> codificare, che è il comportamento corretto di qualunque consumatore.
>
> ⚠ E il conteggio dei buffer: 830 buffer contro 594 fotogrammi contati, con «danno parziale 829,
> pieno 1». I ~236 di differenza sono verosimilmente i buffer di **solo cursore** di §4.7, che il
> misuratore scarta: un'altra ragione per rendere onesto quel conteggio prima di citarlo.

#### 4.9 Ciclo di vita — e i due modi di perdere il flusso

**[R]** `screencaststream.cpp`, `screencastmanager.cpp`, `outputscreencastsource.cpp`:

| Evento | Che cosa fa KWin |
|---|---|
| il client Wayland si disconnette | `finished()` → `close()`; per un output virtuale, `removeVirtualOutput()` |
| **il consumatore PipeWire si sgancia** (`UNCONNECTED`) | ⛔ **`close()`**: il flusso non sopravvive, e con lui **muore l'output virtuale** (`:142-144`) |
| il consumatore mette in pausa | `m_source->pause()`: si scollega dal danno |
| il consumatore riparte (`STREAMING`) | ✅ `resume()` → **un fotogramma pieno subito** (`outputscreencastsource.cpp:99-109`) |
| **l'uscita viene disabilitata** (`enabled=false`, per esempio da kscreen) | ⛔ `closed()` → flusso morto (`outputscreencastsource.cpp:27-32`) |
| PipeWire cade (`-EPIPE`) | `close()` |

> ⛔ **Regola per il palco su KDE**: fra due client RDP **non si distrugge il `pw_stream`** — si fa
> `pw_stream_set_active(false)`. Un `UNCONNECTED` smonta l'output virtuale, e chi si ricollega non
> trova più niente. È la stessa forma della regola del palco di §7.3 di `REFERENCE.md`, con un
> meccanismo diverso.

**Nessuna richiesta «mandami un fotogramma pieno adesso»** esiste nel protocollo [✗]: il fotogramma
pieno arriva solo alla ripresa da pausa. **R9 vale identica su KDE**: l'ultimo fotogramma va
conservato e rispedito da noi.

**Sessione inattiva (cambio VT) — buona notizia da confermare.** `DrmGpu::setActive(false)`
inibisce i render loop **solo** dei `m_drmOutputs`, e i virtual output vivono in un'altra lista
(`drm_gpu.cpp:710-723`, `drm_backend.cpp:340-347`); `present()` di un virtual output non fa alcun
commit KMS. **Sulla carta la cattura continua a sessione in background** — è esattamente ciò che
serve a un servizio non presidiato. **[?]** da misurare con un `chvt`. Lo stesso per il DPMS:
`DrmVirtualOutput::setDpmsMode()` scrive solo lo stato, non inibisce il render loop
(`drm_virtual_output.cpp:66-71`).

#### 4.10 Il cursore

**[R]** Il modo si decide **una volta sola**, prima di `init()`, e **non è cambiabile a flusso
vivo** (`setCursorMode`, `:915-918`).

Con `Metadata` (`addCursorMetadata`, `:801-860`): posizione e hotspot **già scalati** e mappati
nell'output, a ogni movimento; **la bitmap solo quando la forma cambia** (`bitmap_offset = 0`
altrimenti — il consumatore deve **ricordare** l'ultima forma); formato RGBA premoltiplicato,
**troncata** a 256×256, non scalata; `id = 0` quando il cursore non è visibile.

Tre vincoli **[R]**:

1. il cursore c'è **solo se sta sopra il nostro output** (`cursor->isOnOutput`,
   `outputscreencastsource.cpp:124-131`): con un output virtuale bisogna portarci il puntatore, e
   prevedere il caso «è andato altrove» — il client resta senza cursore, senza errore;
2. gli aggiornamenti di cursore passano dallo **stesso freno** del video: negoziare un
   `maxFramerate` basso **strozza anche il cursore** (`:501-517`). Conviene negoziare alto e
   limitare la codifica da noi;
3. `Cursors::isCursorHidden()` lo azzera in blocco.

> **Per RDP il modo giusto è `Metadata` (4)**: RDP ha un canale puntatore proprio, e così il cursore
> non costa una ricodifica. Il prezzo è §4.7. Se si volesse partire semplici, `Embedded` (2) è a
> prova di errore ma paga un fotogramma intero per ogni movimento del mouse.
>
> E una nota che vale di più: **la posizione del cursore la sappiamo già noi**, perché siamo noi a
> iniettare il movimento. Il metadato serve per la **forma** e per i movimenti che non generiamo.

---

### 5. Senza monitor: i backend, e la GPU

#### 5.1 ⛔ La nostra misura del 7 agosto è contraddetta dal codice

`REFERENCE.md` R32 e `LEZIONI.md` §3 dicono: *«KWin senza monitor disegna in software: col backend
`--virtual` non apre alcun nodo DRM e non carica alcuna libreria GL»*. Il codice dice il contrario.

**[R]** `kwin/src/backends/virtual/virtual_backend.cpp:23-56`: il costruttore del backend enumera i
dispositivi DRM con `drmGetDevices2()` e apre un **nodo di rendering** (`DRM_NODE_RENDER`,
`renderD*`) con un `::open(O_RDWR)` diretto — **senza logind**. E `:73-81`:
`OpenGLCompositing` è dichiarato **solo se** quel nodo si è aperto; altrimenti resta soltanto
`QPainterCompositing`. Il renderer OpenGL è **EGL su gbm** (`virtual_egl_backend.cpp:108-115`,
`EGL_PLATFORM_GBM_KHR`), con swapchain di buffer gbm.

E la prova sta **nella nostra stessa tabella**: `banco/tabella-altri.txt` riporta per KWin
`tipo=DMA-BUF`, `fence=1010`, 59,50 fps. Ma un flusso screencast **può essere DMA-BUF solo se il
compositore è un `AbstractEglBackend`** (`screencaststream.cpp:920-925`, e `:154-155` per la scelta
del tipo di buffer). Cioè: **in quella misura KWin stava già componendo sulla GPU.**

Le sole cause di un `findRenderDevice() == nullptr`, dal codice: nessun `/dev/dri` visibile;
**permessi** sul render node (gruppo `render`) — e allora compare `Failed to open drm node: <path>`
(`core/drmdevice.cpp:77`, `qCWarning`, **visibile per difetto**); gbm/Mesa mancante.

> ⛔ **Che cosa va fatto, e in quale ordine.** Non si corregge il documento su una lettura di codice:
> si rifà la misura, con le due prove che non dipendono da quel che KWin dichiara (§5.3). Poi si
> corregge R32 con data e fonte. Fino a quel momento, **il numero «KWin: 60 fps a 4K» resta valido
> come misura e sospetto quanto alla sua etichetta**: quel che è in dubbio non è il 60, è il «in
> software».

> #### ✅ MISURATO — e l'etichetta «in software» era sbagliata
>
> **[M] Misura M3, banco del 7 agosto 2026, `kwin_wayland --virtual` 6.3.6-1, Mesa 25.0.7.**
> Le tre prove, tutte concordi:
>
> | Prova | Esito |
> |---|---|
> | nodi DRM aperti dal compositore | **`/dev/dri/renderD129`** — un render node, aperto |
> | librerie di rendering caricate | `libEGL.so.1.1.0`, **`libEGL_mesa.so.0.0.0`**, `libgbm.so.1.0.0`, `libgallium-25.0.7` |
> | global `zwp_linux_dmabuf_v1` | **annunciato, versione 4** — e nasce solo da `AbstractEglBackend::initWayland()` |
>
> **Verdetto: KWin senza monitor compone sulla GPU.** La lettura del codice era giusta e la nostra
> etichetta era sbagliata: **R32 va corretta**, il «60 fps a 4K» resta ma non è «in software».
>
> ⚠ **Una trappola nella prova, per chi la rifà.** Su Mesa 25 tutti i driver gallium — llvmpipe
> compreso — stanno in **un'unica** `libgallium-*.so`: quindi *«non vedo llvmpipe fra le librerie»*
> **non prova niente**, e la vecchia ricerca di `swrast_dri`/`llvmpipe` per nome non funziona più.
>
> ⛔ **E la prova che avevo dato per buona il 7 agosto — «il render node aperto» — NON prova la GPU.**
> [M, 8 agosto] Con `KWIN_COMPOSE=Q`, cioè KWin **in QPainter**, `/dev/dri/renderD129` risulta
> **aperto comunque**: il nodo lo apre il *costruttore* di `VirtualBackend`, prima che si scelga il
> compositore. Quindi quella riga dice «il backend ha trovato un device», non «sta rendendo in GPU».
>
> ✅ **La prova che regge è una sola, e KWin la regala** (§5.3-bis): la stringa del renderer, via
> `org.kde.KWin.supportInformation` su D-Bus. Sul banco:
> `OpenGL renderer string: AMD Radeon RX 6800 (radeonsi, navi21, LLVM 19.1.7, DRM 3.64, 7.0)`,
> `Mesa 25.0.7`. Nessuna interpretazione possibile.
>
> La gerarchia delle prove, dopo il banco, dalla più forte alla più debole:
>
> | Prova | Che cosa dimostra davvero |
> |---|---|
> | **stringa del renderer** (`supportInformation`) | ✅ il driver e il chip esatti: **GPU o llvmpipe** |
> | `zwp_linux_dmabuf_v1` annunciato | **EGL sì/no** — con `KWIN_COMPOSE=Q` scompare (0), con OpenGL c'è (1). **Non** distingue GPU da llvmpipe |
> | render node aperto | ⛔ **niente**: aperto anche in QPainter |
>
> ⚠ **E per leggere quel `/proc` serve `sudo`, con una ragione precisa**: `/usr/bin/kwin_wayland`
> porta l'attributo esteso **`security.capability`** (verificato: `cap_sys_nice`), e un binario con
> file capabilities è **non dumpable** — il kernel nega `/proc/<pid>/fd` e `/proc/<pid>/maps` anche
> all'utente che l'ha avviato. Non è un difetto del banco. (Copiare il binario per perdere l'xattr
> **non** è una scorciatoia praticabile: la copia non carica il plugin QPA `wayland-org.kde.kwin.qpa`
> e muore con `Aborted`.)
>
> 🟡 **Quel che invece resta aperto è il tipo di buffer (M3d).** Il flusso negoziato sul banco è
> `1280x720 BGRx, modificatore 0x0, memoria` — cioè **MemFd**, non DMA-BUF. Ma questo **non**
> contraddice il verdetto: è il *nostro* cliente che non offre DMA-BUF (la copia zero è rinviata
> dalla fase 9). Il criterio di §5.3 punto 1 vale solo a parti invertite: se il cliente offre
> DMA-BUF e KWin lo nega, allora KWin è in QPainter. Da rifare quando il cliente saprà offrirlo.

#### 5.2 I backend, e la scelta fra `--virtual` e `--drm`

**[R]** La selezione è in `main_wayland.cpp:428-463`, e l'ordine conta: `--drm` → `--x11-display` →
`--wayland-display` → `--virtual` → **poi** l'euristica sull'ambiente (`WAYLAND_DISPLAY` → annidato
Wayland, `DISPLAY` → annidato X11, **altrimenti drm**).

> ⛔ **Da cui una regola operativa**: il backend si passa **sempre** esplicitamente. Se REMOTIX gira
> dentro una sessione dove `WAYLAND_DISPLAY` o `DISPLAY` sono impostate, senza opzione KWin sceglie
> il backend annidato; con l'ambiente pulito sceglie **drm** e senza logind muore.

| | `--virtual` | `--drm` con zero uscite fisiche |
|---|---|---|
| GPU | **sì**, su un render node, per difetto [R] | sì, sul nodo primario `card*` [R] |
| Prerequisiti | **solo r/w su `/dev/dri/renderD*`**; niente logind, niente seat, niente DRM master (`Session::Type::Noop`, `main_wayland.cpp:513`) | **sessione logind attivabile su un seat**, con `Activate` + `TakeControl` + `TakeDevice` (`session_logind.cpp:109-131`, `161-188`) |
| `stream_virtual_output` | ⛔ **NON funziona**: `VirtualBackend` non ridefinisce `createVirtualOutput()`, la base torna `nullptr` (`core/outputbackend.cpp:80-83`) → `sendFailed("Could not find output")` | ✅ funziona (`drm_backend.cpp:340-347`) |
| Uscite | fisse, decise all'avvio (`--output-count`, `--width`, `--height`, `--scale`) | nessuna all'avvio; si creano a runtime |
| Scanout diretto | no | sì (`drm_virtual_egl_layer.cpp:140-153`) |
| Modificatori DRM | no: swapchain forzata a `DRM_FORMAT_MOD_INVALID` | sì |
| Scelta della GPU | **nessuna**: prende la prima che si apre, nessuna variabile [R] | `KWIN_DRM_DEVICES` |
| libinput / `/dev/input` | non serve: `createInputBackend()` non è ridefinito, nessun libinput | serve |
| Se fallisce | compone in software con due `qCWarning` | ⛔ `std::exit(1)`, **rumoroso** |

**[R]** `--drm` **parte con zero connettori collegati**: `DrmGpu::updateOutputs()` non crea nulla e
torna `true`, la GPU primaria sopravvive, `EglGbmBackend::init()` non tocca le uscite, e il
Workspace mette un `PlaceholderOutput` 1920×1080 **non composto e non esposto come `wl_output`**
(`workspace.cpp:1217-1231`). Alla prima `stream_virtual_output` il segnaposto viene distrutto e
nasce un `wl_output` vero. E **non accetta mai un render node**: `drmIsKMS()` lo scarta
(`drm_backend.cpp:216-220`), l'enumerazione udev cerca solo `card[0-9]`.

⛔ **`--drm` con una sessione Noop è impossibile per costruzione**: `NoopSession::openRestricted()`
torna `-1` sempre (`session_noop.cpp:41-44`), quindi tutte le `addGpu` falliscono e KWin esce.

> #### ⛔ MISURATO — `--drm` **non** è praticabile senza seat, e quindi la scelta è già fatta
>
> **[M] Misura M2, banco del 7 agosto 2026.** Era «la domanda che decide», e la risposta è **no**.
> Da una sessione senza seat (`loginctl show-session`: `Seat=` vuoto, `Remote=yes`, `VTNr=0`, con
> `seat0` esistente e la console su tty1), `kwin_wayland --drm` **esce con stato 1** dicendo:
>
> ```
> kwin_core:        Failed to activate /org/freedesktop/login1/session/_351 session.
>                   Maybe another compositor is running?
> kwin_wayland_drm: failed to open drm device at "/dev/dri/card0"
> kwin_wayland_drm: failed to open drm device at "/dev/dri/card1"
> kwin_wayland_drm: No suitable DRM devices have been found
> ```
>
> ⚠ **E non è un problema di permessi Unix**, che è la spiegazione comoda da escludere: nello stesso
> ambiente e con gli stessi gruppi, il giro `--virtual` **apre `renderD129` senza difficoltà**. Il
> punto di rottura è `Activate()`, cioè esattamente la riga di `session_logind.cpp:109-131` che la
> tabella qui sopra dà come prerequisito.
>
> **Conseguenza per la fase**: l'unico modo di avere `--drm` sarebbe una sessione **su `seat0`**,
> cioè imitare un display manager e **occupare la console fisica** — e allora non è più un servizio
> remoto che convive con l'utente locale. Quindi **la «scelta fra `--virtual` e `--drm`» (§13.4,
> decisione 1) non è una scelta**: è `--virtual`, e con essa il prezzo di §8.1 (nessun
> `stream_virtual_output`, nessun ridimensionamento prima di KWin 6.8).
>
> ⚠ **Nota di banco**: ogni comando SSH apre una sessione logind **nuova** (49, 50, 51…), tutte senza
> seat. Un identificativo di sessione letto in un comando non vale nel comando successivo — «No
> session '49' known» — e chi scrive prove su logind deve rileggerlo ogni volta.

#### 5.3 Come si accerta se KWin è in GPU o in software

**[R]** Le due prove che non dipendono da quel che KWin dichiara:

1. **Il tipo di buffer che il flusso screencast offre.** DMA-BUF ⇒ EGL/gbm su un nodo DRM reale;
   solo MemFd ⇒ QPainter, cioè CPU (`screencaststream.cpp:920-925`, `154-155`). Nessun modo di
   simulare l'uno con l'altro.
2. **La presenza del global `zwp_linux_dmabuf_v1`**, creato pigramente e **solo** da
   `AbstractEglBackend::initWayland()` (`abstract_egl_backend.cpp:118-196`,
   `wayland_server.cpp:516-530`). Se `wayland-info` sul socket di KWin non lo elenca, KWin è in
   QPainter.

Più, dal sistema operativo: `ls -l /proc/$(pidof kwin_wayland)/fd | grep dri`.

⚠ **Quello che invece non basta**: `compositingType` distingue OpenGL da QPainter, **non GPU da
software**; e `supportInformation` va letto **insieme** alla riga `OpenGL renderer string`, perché
llvmpipe e softpipe **non** fanno ripiegare KWin su QPainter (`m_recommendedCompositor` resta
`OpenGLCompositing`, `glplatform.h:331`, `glplatform.cpp:876-886`). *«Compositing Type: OpenGL»* su
llvmpipe è possibile, ed è il caso peggiore: rendering software travestito da GPU.

#### 5.4 ⛔ `KWIN_COMPOSE` non protegge all'avvio

**[R]** L'enforcement di `KWIN_COMPOSE` è `qApp->quit()` (`compositor_wayland.cpp:164`), ma
`createRenderer()` gira dentro `performStartup()`, chiamata **sincronamente** da
`Application::start()` **prima** di `a.exec()` (`main.cpp:144`, `main_wayland.cpp:620-622`). Senza
ciclo di eventi, `quit()` è inerte: il ciclo dei candidati prosegue, QPainter riesce, e **KWin parte
in software nonostante `KWIN_COMPOSE=O2`**, con una sola `qCCritical` a testimoniarlo.

> È la lezione 1.8 di `LEZIONI.md` in casa d'altri: **quando un componente può decidere da sé,
> bisogna dirgli cosa fare — e verificare che abbia obbedito.** Tutte le misure prese con
> `KWIN_COMPOSE=O2` presuppongono che quell'interruttore funzioni.

> #### ⛔ MISURATO — `KWIN_COMPOSE=O2` **non protegge**, e la lettura del codice era giusta
>
> **[M] Misura M4, 8 agosto 2026.** Per rispondere bisognava rendere OpenGL *impossibile*, e non
> bastava renderlo *lento*: `LIBGL_ALWAYS_SOFTWARE=1`, `GALLIUM_DRIVER`, `MESA_LOADER_DRIVER_OVERRIDE`
> e `__EGL_VENDOR_LIBRARY_DIRS` **non hanno alcun effetto** su KWin (il renderer resta
> `AMD Radeon RX 6800 (radeonsi)`: verificato con `supportInformation`). La condizione si ottiene
> togliendo l'accesso ai render node — sul banco con un namespace di monti privato.
>
> Allora, con tutti i render node inaccessibili:
>
> | | esito |
> |---|---|
> | senza `KWIN_COMPOSE` *(controllo)* | `Configured compositor not supported by Platform. Falling back to defaults` → **QPainter**, e KWin parte |
> | **con `KWIN_COMPOSE=O2`** | `Compositing forced to OpenGL mode by environment variable` → **`Falling back to defaults`** → **`QPainter compositing has been successfully initialized`**, e **KWin parte** |
>
> ⛔ **Quindi l'interruttore è inerte**, esattamente come diceva §5.4: il `qApp->quit()` gira prima del
> ciclo di eventi. **Conseguenza operativa**: `KWIN_COMPOSE=O2` non va usato come garanzia in nessuna
> nostra ricetta né in nessun banco; l'unico modo di sapere come sta rendendo KWin è **chiederglielo**
> (la stringa del renderer, §5.1). E la cattura resta disponibile anche in QPainter: `zkde_screencast`
> è annunciato e il global `zwp_linux_dmabuf_v1` scompare — l'unico segno visibile del ripiego.

#### 5.3-bis ✅ La prova diretta: chiedere a KWin che renderer usa

**[M, 8 agosto 2026]** La misura che chiude ogni dubbio su GPU-o-software, e che non richiede né
`/proc` né `sudo`:

```sh
gdbus call --session --dest org.kde.KWin --object-path /KWin \
    --method org.kde.KWin.supportInformation | grep -oE 'OpenGL renderer string: [^\\]*'
```

Funziona su KWin nudo e dentro una sessione Plasma. In QPainter la riga **non c'è** — che è a sua
volta una risposta.

#### 5.6 ⚙ Scegliere QUALE GPU usa il compositore — deciso dall'utente

> **Decisione dell'utente, 8 agosto 2026: «non usare la Radeon, usa la Intel integrata».**
> La macchina di prova ha due GPU: Intel AlderLake-S (i915) su `renderD128` e Radeon RX 6800
> (amdgpu) su `renderD129`.

**[R]** Con `--virtual` **non esiste alcuna leva**: `findRenderDevice()`
(`virtual_backend.cpp:23-56`) itera `drmGetDevices2()` e prende **la prima che si apre**, senza
guardare nessuna variabile — `KWIN_DRM_DEVICES` vale solo per il backend `drm`. Sul banco l'ordine
mette la Radeon davanti, e KWin prende quella.

**[M]** Quindi la Intel si ottiene in un modo solo: **rendere l'altra GPU non apribile da quel
processo**. Due strade provate, e una sola va bene:

| Strada | GPU | Cancello della cattura |
|---|---|---|
| `InaccessiblePaths=/dev/dri/renderD129` nell'unità | ✅ Intel | ⛔ **chiuso** (§3.3-bis, riquadro) |
| `DeviceAllow=` + `DevicePolicy=closed` | ⛔ nessun effetto: resta la Radeon (in un'unità **d'utente** il controllo dei device non è delegato) | ✅ aperto |
| ✅ **permessi del nodo** (`renderD129` fuori dal gruppo `render`) | ✅ **Intel** | ✅ **aperto**, e flusso PipeWire ottenuto |

✅ **La via buona è la terza**, e per il prodotto si scrive come **regola udev** che assegna il nodo
della GPU da non usare a un gruppo che l'utente del servizio non ha — identificando la scheda per
**id PCI** (`/dev/dri/by-path/pci-0000:03:00.0-render`), perché il numero del nodo non è stabile.

⚠ **E il prezzo va detto**: negare il nodo coi permessi lo nega **a tutta la sessione dell'utente**,
non solo al compositore. Se un giorno servisse la Radeon per un'altra cosa nella stessa sessione, la
strada giusta diventa un'altra (per esempio far scegliere a *noi* il device e non a KWin, che oggi
non è possibile senza toccare KWin).

#### 5.7 📊 Quanto eroga la cattura **sulla Intel integrata** — la tabella che conta per il prodotto

**[M] 8 agosto 2026.** Le tabelle di `REFERENCE.md` R32 sono della Radeon; queste sono della GPU che
il prodotto userà. Misura della **sola cattura**, scena dichiarata e in movimento
(`weston-simple-egl` a schermo intero, sincronizzato al ridisegno), tetto dichiarato 60 fps, 10
secondi per cella, `kwin_wayland --virtual` con la Radeon negata:

| Risoluzione | copia zero (DMA-BUF) | in memoria (MemFd) |
|---|---|---|
| 1280×720 | **59,4** *(mediana 16,5 ms)* | 49,6 *(20,2 ms)* |
| 1920×1080 | **59,2** *(17,2 ms)* | 43,3 *(23,2 ms)* |
| 2560×1440 | **59,3** *(17,2 ms)* | 37,0 *(27,0 ms)* |
| **3840×2160** | **59,0** *(17,2 ms)* | **27,0** *(37,4 ms)* |

⭐ **Due letture, e sono le più importanti di tutta la fase:**

1. ✅ **A copia zero la risoluzione non costa niente**: 59 fotogrammi al secondo **da 720p a 4K**, con
   la mediana degli intervalli ferma a 17 ms. Il requisito dell'utente — *«30 a 1080p, 60 a 4K»*
   (`REFERENCE.md` R32, e la memoria del progetto) — **è raggiungibile su una Intel integrata**.
2. ⛔ **In memoria la risoluzione costa tutto**: da 49,6 a **27,0** salendo a 4K, cioè meno della metà
   del bisogno. **Il collo di bottiglia è la copia**, non il compositore e non la GPU.

> **Da cui la conseguenza per il piano**: su KDE la copia zero non è un'ottimizzazione, è **la
> condizione** per i 60 a 4K. E su KDE è anche più facile che su GNOME, perché i fotogrammi sono
> interi (§4.6) e resta solo da aspettare la fence (§4.8). La fase 9, rinviata su GNOME per il
> «diff», qui va ripresa con una prospettiva diversa.

E il ripiego è silenzioso quasi ovunque: le righe che lo raccontano sono `qCDebug`, spente per
difetto. L'unica visibile è *«Configured compositor not supported by Platform. Falling back to
defaults»* (`:139`) — che scatta proprio nel caso «il render node non si è aperto». Sul backend
`drm` nemmeno quella: `supportedCompositors()` dichiara sempre `{OpenGL, QPainter}`.

#### 5.5 Xwayland — meglio che su GNOME

**[R]** `--xwayland` è opzionale sulla riga di comando e in compilazione; l'avvio è **pigro** (parte
solo quando un client tocca il socket X11, `xwaylandlauncher.cpp:95-99`) e **non bloccante**
(`-displayfd` + `QSocketNotifier`); un fallimento produce un `qCWarning` e **il compositore
continua**; un crash ha una politica di riavvio con conteggio.

> La questione aperta n.8 di `SPECIFICA.md` — «Xwayland non completa l'avvio e a volte si porta
> dietro il compositore» — **su KWin non ha l'equivalente**: qui un Xwayland assente o bloccato non
> appende il compositore. Ma vedi §6.4: su Plasma, X11 serve **a ksmserver**, e quindi
> `--xwayland` diventa obbligatorio per un'altra ragione.

---

### 6. La sessione Plasma senza monitor

#### 6.1 La ricetta

**[R]**, e le due variabili obbligatorie sono solo due:

```sh
# 1. ambiente composto da zero (env_clear), con:
XDG_RUNTIME_DIR=/run/user/1000                         # obbligatoria: senza, wl_socket_create()
                                                       # torna NULL e il wrapper fa qFatal
                                                       #   [R] wl-socket.c:132-136
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus  # obbligatoria: senza, return 1
                                                       #   [R] startplasma-wayland.cpp:58-61
HOME= USER= PATH= SHELL=
LANG=it_IT.UTF-8                                       # consigliata [R] startplasma.cpp:213-216

# ⛔ NON impostare DISPLAY, WAYLAND_DISPLAY, QT_QPA_PLATFORM
#    [R] main_wayland.cpp:452-463, ksmserver/main.cpp:106-117

# 2. sovrascrittura dell'unità del compositore — su Wayland è l'unica leva
#    $XDG_RUNTIME_DIR/systemd/user.control/plasma-kwin_wayland.service.d/remotix.conf
[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width W --height H --no-lockscreen
#    poi: systemctl --user daemon-reload

# 3. avvio
exec /usr/bin/startplasma-wayland
```

**Che cosa mette Plasma da sé**, e che quindi non va dichiarato (`startplasma.cpp:353-414`,
`startplasma-wayland.cpp:64`): `XDG_CURRENT_DESKTOP=KDE`, `XDG_SESSION_TYPE=wayland`,
`KDE_FULL_SESSION`, `KDE_SESSION_VERSION=6`, `KDE_SESSION_UID`, `XDG_MENU_PREFIX`,
`XDG_CONFIG_DIRS`, le `XKB_DEFAULT_*` da locale1, `LANG`/`LC_*` da `plasma-localerc`. E
`WAYLAND_DISPLAY`/`DISPLAY`/`XAUTHORITY` le esporta il wrapper del compositore
(`kwin_wrapper.cpp:157-163`).

> ⛔ **E fra quelle che «mette Plasma da sé» ce n'è una che non è un dettaglio: `XDG_MENU_PREFIX`.**
> [M, 7 agosto 2026] Senza di essa **il permesso della cattura non funziona**, per la ragione
> spiegata in §3.3-bis: l'indice dei servizi resta vuoto e KWin non trova nessun `.desktop`. In
> questa ricetta è coperta, perché `startplasma` la imposta
> (`startplasma.cpp:366` — e **non** esegue `kbuildsycoca6`: l'indice si costruisce da sé nel primo
> processo KDE che lo usa, che dentro la sessione ha già il prefisso giusto).
>
> **Il pericolo è per chi non passa da `startplasma-wayland`**: un banco che avvia `kwin_wayland` a
> mano, uno script di manutenzione o un `kbuildsycoca6` lanciato da una shell SSH **senza** il
> prefisso sovrascrivono l'indice buono e chiudono il cancello a compositore già avviato, senza un
> messaggio. Chi scrive prove esporta `XDG_MENU_PREFIX=plasma-` **sempre**.

> #### ✅ MISURATO — la ricetta funziona, con tre precisazioni
>
> **[M] 8 agosto 2026.** `startplasma-wayland` avviato da una shell SSH con l'ambiente qui sopra e il
> drop-in dell'unità: **plasmashell compare in 1 secondo**, il socket è `wayland-0`, KWin risponde su
> D-Bus, la cattura è autorizzata e un flusso PipeWire si monta (§3.3-bis). Le tre precisazioni:
>
> 1. ⛔ **niente `InaccessiblePaths=` (né altro che implichi un namespace di monti) nel drop-in**:
>    chiude il cancello della cattura (§3.3-bis, riquadro). Per la GPU si usano i permessi del nodo
>    (§5.6).
> 2. ⚠ **`ksmserver` e `Xwayland` non sono partiti affatto** (zero processi), e la sessione ha
>    funzionato comunque: plasmashell, kwin_wayland e kded6 in piedi. Su questo §6.4 va riletta — il
>    vincolo «`--xwayland` è obbligatorio per ksmserver» **non si è manifestato** in questa prova, e
>    Xwayland parte pigramente (§5.5). Resta da capire se ksmserver serva per il *logout ordinato* o
>    per il ripristino della sessione: **non si tolga `--xwayland` prima di averlo verificato.**
> 3. ⚠ La sessione **crea 23 file di configurazione** in `~/.config` al primo avvio (`kdeglobals`,
>    `plasmashellrc`, `plasma-localerc`, `kwinrc`…). È normale, ma va saputo: la prima sessione
>    scrive nella casa dell'utente, e `plasma-localerc` fissa la locale (sul banco: `LANG=C.UTF-8`).

> ✅ **Il difetto silenzioso pagato su GNOME non c'è.** `ConditionEnvironment=` **non esiste in
> nessuna unità** dei sette repo [R]: su GNOME l'unità della Shell portava
> `ConditionEnvironment=XDG_SESSION_TYPE=wayland` e senza quella variabile il compositore non
> partiva affatto, senza che nessuno lo spiegasse (§5.9-bis di `SPECIFICA.md`).
>
> ✅ **E Plasma fa da sé la pulizia che noi facciamo a mano.** `dropSessionVarsFromSystemdEnvironment()`
> (`startplasma.cpp:445-473`) toglie a **ogni avvio** dall'ambiente del manager systemd le variabili
> di sessione (`DISPLAY`, `XAUTHORITY`, `WAYLAND_DISPLAY`, `WAYLAND_SOCKET`, tutte le `XDG_*`), con
> il commento: *«Those can be leftovers from previous sessions … e.g. `$DISPLAY` might break
> kwin_wayland»*. È la nostra lezione «chi sopravvive al logout non riusa niente della sessione
> morta», applicata dal desktop stesso.

#### 6.2 La catena, e chi lancia il compositore

**[R]** `startplasma-wayland` **non lancia KWin**: fa `StartUnit("plasma-workspace-wayland.target")`
(`startplasma.cpp:726`), e l'unità è

```ini
# kwin/plasma-kwin_wayland.service.in
ExecStart=<bindir>/kwin_wayland_wrapper --xwayland
BusName=org.kde.KWinWrapper
PartOf=graphical-session.target
```

Il wrapper **rigira tutti i propri argomenti** a `kwin_wayland` (`kwin_wrapper.cpp:128-130`): basta
aggiungerli all'`ExecStart`. La ricetta per farlo senza toccare `$HOME` è di KDE stessa —
copia in `$XDG_RUNTIME_DIR/systemd/user.control` più `daemon-reload`
(`login-sessions/startplasma-dev.sh.cmake:8-13`).

L'ordine effettivo che ne risulta: `plasma-kwin_wayland` → `kcminit` → `kded6` →
**`ksmserver`** → `plasmashell` → `plasma-core.target` → `plasma-workspace.target`
(powerdevil, kglobalaccel, kwallet-pam, …) → `graphical-session.target` → autostart.

⚠ **Due fragilità da conoscere** [R]: l'unità del compositore dichiara `BusName=` **senza
`Type=dbus`**, quindi l'ordinamento di ksmserver poggia solo su `After=`, cioè sull'*exec* del
wrapper e non sull'export di `DISPLAY` — nella strada classica il commento è esplicito: *«This must
block until started as it sets the WAYLAND_DISPLAY/DISPLAY env variables needed for the rest of the
boot»* (`plasma-session/startup.cpp:162-165`). E `plasma-core.target` /
`plasma-workspace.target` hanno `RefuseManualStart=yes`: si avvia **solo**
`plasma-workspace-wayland.target`.

#### 6.3 ✅ Non serve una sessione logind su un seat — con `--virtual`

**[R]** `--virtual` impone `Session::Type::Noop` (`main_wayland.cpp:513`): **niente logind, niente
seat, niente `/dev/dri` via `TakeDevice`, niente `/dev/input`**. `XDG_SEAT` e `XDG_VTNR` **non sono
letti da nessuno dei sette repo** [✗]. È l'equivalente esatto del nostro accertamento su
`gnome-session` (§5.9-bis di `SPECIFICA.md`).

Con `--drm`, invece, serve una sessione logind **attivabile** su un seat: cioè quel che fa un
gestore di accesso, e che per definizione non abbiamo. **È il compromesso centrale della fase**
(§13).

#### 6.4 ⛔ `--xwayland` non è opzionale, e la ragione è ksmserver

**[R]** `plasma-workspace/ksmserver/main.cpp`: forza `QT_QPA_PLATFORM=xcb` (`:106-107`, *«force xcb
QPA plugin as ksmserver is very X11 specific»*), costruisce una `QGuiApplication`, e a `:124`
dereferenzia il display X11 **senza alcun controllo di nullità**. E `ksmserver` è `Requires=` di
`plasma-core.target`, che è `Requires=` della catena fino al target di sessione: **un suo guasto
abbatte tutta la sessione.**

> Cioè: KWin non ha bisogno di Xwayland, **Plasma sì**. E la nostra riga di banco
> (`banco/banco-altri.sh:33`) avvia KWin **senza** `--xwayland`: con quella riga una **sessione
> Plasma non parte**. I 59–60 fps misurati valgono per **KWin nudo**, non per una sessione Plasma
> completa — e questa è la seconda etichetta da correggere sulle misure del 7 agosto.

#### 6.5 Il logout: non c'è `RegisterClient`, e la strada buona è passiva

**[R]** Gli attori sono quattro: `plasma-shutdown` (`org.kde.Shutdown`), `ksmserver-logout-greeter`
(`org.kde.LogoutPrompt`), `ksmserver` (`org.kde.ksmserver`), KWin (`org.kde.KWin` `/Session`).

| Come accorgersene | Quando | Rischio |
|---|---|---|
| ✅ **`NameOwnerChanged` su `org.kde.Shutdown`** (nome attivabile: compare quando il logout comincia, `plasma-shutdown/shutdown.cpp:20-23`) | **all'inizio** | nessuno: siamo spettatori |
| ✅ **`NameOwnerChanged` su `org.kde.KWinWrapper`** (sparisce a sessione finita) | alla fine | nessuno |
| ⚠ registrazione **XSMP** presso ksmserver (`$SESSION_MANAGER`, libSM/libICE) | all'inizio, con obbligo di risposta | **la regola dell'ostaggio vale identica**: chi si registra e non risponde frena il logout di **15 s** (`ksmserver/logout.cpp:293-303`), poi viene ignorato |

Le prime due sono esattamente quel che fa `startplasma` per decidere di uscire
(`startplasma.cpp:673-689`). **È la strada da prendere**: costa due sottoscrizioni sul bus e non
mette in gioco la sessione dell'utente. L'equivalente vero di `RegisterClient` esiste — ma è XSMP su
ICE, richiede `libSM`/`libICE` e un `DISPLAY`, e `org.kde.KSMServerInterface` **non ha alcun segnale
«la sessione sta finendo»** [R].

**Comandare il logout da fuori** [R]:

| Che si vuole | Chiamata |
|---|---|
| senza conferma (= `Logout(1)` di GNOME) | `org.kde.Shutdown` `/Shutdown` `logout()` |
| con conferma | `org.kde.LogoutPrompt` `/LogoutPrompt` `promptLogout()` |
| **forzato** (`Logout(2)` **non esiste** [✗]) | `StopUnit("plasma-workspace.target", "fail")` — è quel che fa `plasma-shutdown` alla fine (`shutdown.cpp:151-157`) |
| brutale | `org.kde.KWin` `/Session` `quit()` |

⛔ **E il percorso ordinato può annullarsi da sé.** `KWin::SessionManager::closeWaylandWindows()`
(`kwin/src/sm.cpp:422-508`): dopo **10 s** mostra una notifica persistente con *Cancel Logout* /
*Log Out Anyway*, e se **nessuno risponde** attende fino a **2 minuti** prima di procedere. In una
sessione non presidiata nessuno risponde mai: la seconda metà del nostro `sgombera` (§5.10 di
`SPECIFICA.md`, `Logout(1)` e poi `Logout(2)`) **va riprogettata su KDE** — il secondo passo è
`StopUnit`.

E per non far comparire finestre che nessuno vedrà: `ksmserverrc [General] confirmLogout=false`
(`sessionmanagementbackend.cpp:49-52`).

#### 6.6 ✅ Il bus di sessione non muore — se è quello d'utente

**[R]** In tutti e sette i repo **non c'è alcun riferimento a `dbus.service`, `dbus-launch` o
`dbus --exit-with-session`** fuori dai test: Plasma **non gestisce il ciclo di vita del bus**. Lo
pretende in piedi, oppure si fa avvolgere da `plasma-dbus-run-session-if-needed`, che mette
`dbus-run-session` davanti **solo se** `DBUS_SESSION_BUS_ADDRESS` è vuota.

> ✅ **Ricaduta**: se usiamo il bus **d'utente** (`/run/user/UID/bus`) e lo dichiariamo
> nell'ambiente, **sopravvive al logout** e la connessione resta valida. I due difetti pagati su
> GNOME — la connessione da buttare e riaprire, e `exit-on-close` che chiama `raise(SIGTERM)` per
> conto nostro (§7.4 di `REFERENCE.md`) — **non si presentano**, purché non si lasci lavorare
> `dbus-run-session`. **È una scelta nostra, e va fatta per il bus d'utente.**

> #### ✅ MISURATO — misura M9: il logout non porta via niente di nostro
>
> **[M] 8 agosto 2026.** Sessione Plasma vera, chiusa con `org.kde.Shutdown.logout()` — la sentinella
> passiva di §6.5, chiamata come la chiamerebbe il prodotto:
>
> | Dopo il logout | |
> |---|---|
> | `plasmashell`, `kwin_wayland`, `kded6` | **tutti spariti** (0 processi) |
> | il socket `wayland-0` | **sparito** |
> | **il bus d'utente** | ✅ **risponde ancora** (`GetId` riesce sulla stessa connessione) |
> | `systemd --user` | ✅ vivo (`degraded`, per unità di sessione terminate) |
>
> Quindi la scelta «bus d'utente» è confermata dal campo, e il difetto di GNOME **non si ripresenta**.
> ⚠ Un dettaglio da non dimenticare: dopo il logout il socket è `wayland-0` *libero di nuovo*, e al
> riavvio della sessione il numero **può cambiare** — va riletto, come dice il capoverso qui sotto.

**Riavviare la sessione dallo stesso processo funziona** [R], e Plasma lo prevede: `ResetFailed` e
`Reload` a ogni avvio (`startplasma.cpp:648-649`). Cambiano `WAYLAND_DISPLAY` (il socket è il primo
`wayland-N` libero), `DISPLAY` e `SESSION_MANAGER`: **vanno riletti, non ricordati.**

#### 6.7 La disposizione di tastiera

**[R]** Su Wayland la impone **KWin**, che legge `kxkbrc [Layout]` da sé (non esiste più un `kxkb`
separato). Tre vie per noi:

1. **`XKB_DEFAULT_LAYOUT`/`_VARIANT`/`_MODEL`/`_OPTIONS` nell'ambiente di `kwin_wayland`**, che
   `applyEnvironmentRules()` usa come riempimento (`xkb.cpp:557-575`); con
   **`KWIN_XKB_DEFAULT_KEYMAP=1`** si **forza** l'uso del solo ambiente, ignorando `kxkbrc` e
   locale1 (`xkb.cpp:522-545`). **È la leva pulita**: la disposizione arriva dal client e la si mette
   nell'ambiente prima di avviare il compositore;
2. D-Bus `org.kde.keyboard` `/Layouts`: `getLayout`, **`setLayout(index)`**, `getLayoutsList`,
   `switchToNextLayout` (`keyboard_layout.cpp:186-245`), senza permessi — ma **sceglie solo fra le
   disposizioni già caricate**;
3. scrivere `kxkbrc` e far ricaricare KWin (`org.kde.KWin` `/KWin` `reconfigure()`). **[?]** quale
   dei due basti.

E comunque: **la keymap della sessione la leggiamo da libei** (§7.4), come su GNOME. Questa sezione
serve per il caso in cui la si voglia *imporre*.

#### 6.8 Le animazioni: nessun gancio per-cattura

**[R]** Mutter offre `disable-animations` come opzione della sessione di cattura; il protocollo di
KWin ha **una sola** opzione per stream — il modo del cursore — e nel plugin di cattura non c'è una
riga sulle animazioni [✗]. Su KDE si spengono **a sessione**:

| Leva | Dove | Note |
|---|---|---|
| `KWIN_EFFECTS_FORCE_ANIMATIONS=0` | ambiente di `kwin_wayland` | dichiara le animazioni **non supportate** (`effecthandler.cpp:1425-1433`); letta in una `static`, **non cambiabile a caldo** |
| `AnimationDurationFactor=0` nel gruppo `[KDE]` | `kwinrc` **e** `kdeglobals` | vale **a caldo**, un `KConfigWatcher` la sorveglia (`options.cpp:96-101`); ⚠ `0` non azzera i tempi, li porta a **1 ms** (`effect/effect.cpp:447-457`) |

---

### 7. L'input: KWin parla libei

#### 7.1 ✅ Un backend EIS vero, e si apre con una chiamata D-Bus

**[R]** `kwin/src/plugins/eis/`, 1829 righe, plugin **attivo per default**, caricato solo in
modalità Wayland. Il descrittore si ottiene così:

```
servizio     org.kde.KWin
oggetto      /org/kde/KWin/EIS/RemoteDesktop
interfaccia  org.kde.KWin.EIS.RemoteDesktop
metodo       connectToEIS(i capabilities) → (h fd, i cookie)
             disconnect(i cookie)
```

(`eisbackend.h:39-40`, `eisbackend.cpp:70-104`; firma confermata dall'altro lato,
`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). La maschera è quella del portale xdg:
**tastiera 1, puntatore 2, tocco 4** → per noi **7**. Il `cookie` serve a chiudere.

> ⛔ **Nessun controllo sul chiamante.** `registerObject` è `ExportAllInvokables` senza filtro, e
> `message().service()` è usato **solo** per la durata di vita (se il chiamante muore, il contesto
> cade). Nessun pid, nessun `.desktop`, nessun `X-KDE-DBUS-Restricted-Interfaces`, nessun dialogo:
> il meccanismo esiste in KWin ma **in tutto 6.3.6 lo usa solo `ScreenShot2`**.
>
> Per un servizio non presidiato è **meglio di GNOME**: nessuna sessione da creare, nessun portale.
> Va però trattato come **una porta che può chiudersi**: l'errore D-Bus è un caso normale, non un
> bug, e il ripiego è `fake_input` (che invece il `.desktop` lo richiede).

⚠ **Trappola di distribuzione** [R]: `libeis-1.0` è **opzionale** in compilazione
(`kwin/CMakeLists.txt:319-320`, `431`). Se la distribuzione compila KWin senza, il plugin **non
esiste** e l'oggetto D-Bus non compare: non è un errore a runtime, è un'assenza. **[?]** lo stato di
Debian Trixie va misurato.

**I dispositivi** (`eiscontext.cpp:155-174`, `eisbackend.cpp:116-171`): fino a tre per seat —
«eis pointer» (relativo), **«eis absolute device»** (assoluto **+ tocco**), «eis keyboard». Il seat
annuncia solo le capacità concesse dalla maschera. Il nostro contesto deve essere **sender**: un
receiver viene buttato giù (`eiscontext.cpp:127-131`).

#### 7.2 Che cosa si riusa del nostro `input.c`, e che cosa cambia

Il confronto con le quattro cose che libei ci dà su GNOME:

| | via **EIS** su KWin | via `fake_input` |
|---|---|---|
| **keymap della sessione** | ✅ **sì**, XKB testo v1 su memfd sigillato (`eisbackend.cpp:159-171`) | no |
| **stato dei modificatori a scatto** | ⛔ **no**: `eis_device_keyboard_send_xkb_modifiers` **non è chiamato da nessuna parte in KWin** [✗] | no |
| **ping / sincronizzazione** | ✅ sì — ma per una proprietà accidentale: non c'è un `case EIS_EVENT_SYNC`, e il pong parte perché l'`unref` è fuori dallo `switch` (`eiscontext.cpp:333`) | no |
| **regioni degli schermi** | ✅ sì, una per output — ⚠ **senza `mapping_id`** (`eis_region_set_mapping_id` non è chiamato) [✗] | no |

**Le quattro cose da toccare, tutte circoscritte:**

1. ⛔ **La rotella va cambiata.** Il nostro `/120 → ×10` usa `ei_device_scroll_delta`, che su KWin
   dà `deltaV120 = 0` (`eiscontext.cpp:246-258`) → un `wl_pointer.axis` liscio **senza
   `axis_value120` né `axis_discrete`** (`pointer.cpp:281-358`): chi conta gli scatti non ne vede
   nessuno, e Xwayland deve indovinare i bottoni 4/5. Va usato **`ei_device_scroll_discrete(±120)`**,
   che KWin converte in `delta = 15` + `deltaV120 = ±120` (`eiscontext.cpp:272-286`), cioè la
   rotella vera. **Si passa il valore RDP quasi com'è: più semplice di oggi.** Verticale negato
   (la convenzione `wl_pointer` è positivo = giù).

   > **✅ Misura M10, chiusa l'8 agosto 2026 — per lettura, e la lettura è conclusiva.**
   > `eiscontext.cpp:272-285`: KWin **non inverte nulla** e tratta i due assi **con la stessa
   > formula**, senza casi particolari:
   > ```cpp
   > constexpr auto anglePer120Step = 15 / 120.0;
   > if (x != 0) Q_EMIT device->pointerAxisChanged(PointerAxis::Horizontal, x * anglePer120Step, x, …);
   > if (y != 0) Q_EMIT device->pointerAxisChanged(PointerAxis::Vertical,   y * anglePer120Step, y, …);
   > ```
   > Il segno passa **tale e quale** sia nel delta angolare sia nel `v120` grezzo. Quindi il verso che
   > arriva alle applicazioni è quello di libinput, **identico per verticale e orizzontale**, e
   > l'adattamento da RDP è **tutto nostro** — come già su GNOME. Non c'è nessuna asimmetria di KWin
   > da compensare, che era il sospetto. ⚠ Resta da guardare **con l'occhio** nella fase, perché il
   > verso è una di quelle cose che si giudicano vedendole (`LEZIONI.md` §7.3).
2. ⛔ **I modificatori a scatto non arrivano.** La riconciliazione di BlocMaiusc/BlocNum dopo un
   ping — quella che su GNOME abbiamo fatto bene — **per questa strada non si fa**. Il ripiego è
   `org_kde_kwin_keystate` v5 (`kwin/src/wayland/keystate.cpp`), che dà `unlocked/latched/locked/pressed`
   **con notifica spontanea**, ma è **in lista nera**: richiede di essere anche client Wayland e di
   dichiararlo nel `.desktop`. **È una scelta da mettere davanti all'utente** (§13.4).
3. **Le regioni si cercano per geometria**, non per chiave: sono già in coordinate globali logiche,
   quindi `transform_position` si semplifica — cambia il criterio di ricerca, non la formula. E
   `libei` scarta una posizione assoluta **fuori da ogni regione**.
4. **I dispositivi si ricambiano.** A ogni cambio di output o di disposizione KWin fa
   `eis_device_remove` + `eis_device_add` (`eisdevice.cpp:42-53`, via `updateScreens`/`updateKeymap`):
   dal nostro lato il dispositivo **scompare e ricompare**. Va retto il ricambio, rileggendo keymap
   e regioni a ogni `DEVICE_ADDED`.

**Quel che invece resta identico** [R]:

| | |
|---|---|
| tasti | **codice evdev senza il −8**: KWin somma lui l'offset, in un punto solo (`xkb.cpp:45`, `772`). La nostra conversione scancode RDP → `WINPR_KEYCODE_TYPE_EVDEV` vale tale e quale |
| bottoni | codici evdev intatti (`BTN_LEFT` 0x110 …) |
| movimento assoluto | coordinate **globali logiche**, formula riusabile |
| tocco | stesse coordinate, sul dispositivo assoluto |
| `ei_device_frame()` | **obbligatorio**: senza, i client Wayland non applicano il movimento (`eiscontext.cpp:190-200` → `wl_pointer.frame`) |
| pressioni ripetute e rilasci non appaiati | **KWin li scarta in silenzio** (`eiscontext.cpp:287-303`): non siamo *costretti* a tenere il conto come su Mutter, ma le nostre tabelle restano utili — servono a noi per sapere che cosa rilasciare |
| rilascio a fine connessione | ✅ **KWin fa da rete di sicurezza**: nel distruttore del dispositivo rilascia ogni tasto e bottone premuto e annulla i tocchi (`eisdevice.cpp:27-40`), e il contesto cade quando il servizio D-Bus chiamante scompare |
| Xwayland | ✅ l'input iniettato **la raggiunge** per la via normale del `wl_seat` (`xwayland.cpp:240-330`): nessun XTEST, nessuna strada separata |

⚠ **Un difetto di KWin trovato per strada** [R]: quattro `continue` dentro lo `switch` di
`eiscontext.cpp` (righe 236, 241, 294, 300) saltano l'`eis_event_unref` finale — ogni pressione
ripetuta e ogni rilascio non appaiato **perde un riferimento**. Non ci cambia niente
funzionalmente, ma è un motivo per non bombardare KWin di eventi ridondanti.

#### 7.3 `fake_input`, la strada vecchia

**[R]** `org_kde_kwin_fake_input` (non `zkde_fake_input`), implementato in
`kwin/src/backends/fakeinput/fakeinputbackend.cpp`, **versione 5** mentre l'XML dichiara la 6
(`keyboard_keysym` **non è implementato**). È a senso unico: **zero eventi**. Il suo `authenticate`
ignora gli argomenti e non autentica nulla (`:107-113`, `// TODO: make secure`), ma il permesso
vero è il filtro dei global.

E il suo limite serio: `axis` forza **`deltaV120 = 0` sempre** (`:179`) — **fake_input non può
produrre uno scatto discreto**. È la ragione tecnica per cui krfb scorre male su Wayland.

---

### 8. Output, geometria e risoluzione dinamica

#### 8.1 ⛔ Un output virtuale non si ridimensiona

È il risultato più costoso di questo studio. Quattro barriere, tutte **[R]**:

1. **il modo è immutabile**: `OutputMode::m_size` e `m_refreshRate` sono `const`
   (`core/output.h:127-128`);
2. **l'elenco dei modi non viene mai riscritto** per un output virtuale: `DrmVirtualOutput` lo fissa
   nel costruttore (`drm_virtual_output.cpp:37-40`), `VirtualOutput` in `init()`. Le sole
   riscritture a runtime sono nei backend annidati e nei connettori DRM veri;
3. **`kde_output_management_v2` può solo *scegliere* un modo esistente**: la richiesta prende un
   `wl_resource` di `kde_output_device_mode_v2`, cioè un oggetto già annunciato
   (`outputmanagement_v2.cpp:122-142`). Non esiste una richiesta «misura arbitraria» — e libkscreen
   è lo stesso protocollo con un cappotto, quindi non è una via alternativa;
4. e se anche ci fosse un secondo modo, **su DRM verrebbe ignorato**: `Output::applyChanges()` non
   tocca mai `currentMode` (`core/output.cpp:517-543`).

**Non esistono** [✗]: `org.kde.KWin.VirtualOutputs` (c'era in KWin 5), una variabile `KWIN_*` che
crei output, una richiesta di resize nel protocollo screencast. `VirtualBackend::setVirtualOutputs()`
esiste ma i suoi **unici chiamanti sono gli autotest**.

> #### ✅ MISURATO — misure M7 e M11
>
> **[M] 8 agosto 2026.**
>
> **M7a — `stream_virtual_output` con `--virtual` non funziona**, come diceva la lettura del codice:
> `KWin ha rifiutato: Could not find output`. Verificato, e senza sorprese.
>
> **M11 — le misure assurde**: `0x0`, `-1x-1`, `1x1`, `16384x16384`, `99999x99999` → **tutte
> rifiutate con la stessa riga** (`Could not find output`) e **KWin resta vivo dopo tutte e cinque**.
> ⚠ Ma il rifiuto arriva perché *manca l'output virtuale*, non perché KWin **validi** le misure:
> quindi **la validazione resta non misurata**, e non è misurabile con `--virtual` — servirebbe
> `--drm`, che §5.2 ha escluso. Chi un giorno girasse su KWin ≥ 6.8 la rifaccia.
>
> **M7b — quanto costa mettere in piedi un flusso**: dal collegamento al socket al nodo PipeWire
> annunciato, **65, 65 e 67 ms** su tre giri consecutivi. È la componente fissa del «buco» del
> ripiego «chiudi e rifai» (§8.3); a quella va aggiunto il tempo di ricreare l'output, che su
> `--virtual` non si può misurare perché l'output non si crea affatto.

#### 8.2 Il paradosso: tutto il resto c'è già, ed è identico a Mutter

**[R]** `ScreenCastStream::resize()` (`screencaststream.cpp:672-682`) fa
**`pw_stream_update_params`** sullo stesso nodo, ed è chiamata **alla fine di ogni fotogramma**
confrontando `m_source->textureSize()` (`:669`). Il consumatore vede solo un
`param_changed(SPA_PARAM_Format)`, poi i buffer nuovi. **Se l'output potesse cambiare modo, lo
stream lo seguirebbe da solo** — è precisamente la meccanica che la fase 6 ci ha dato su GNOME. E
funziona già oggi per gli **output reali**: se l'utente cambia risoluzione a un monitor mentre lo
catturiamo, lo stream si adegua.

Manca un pezzo minuscolo: un `DrmVirtualOutput::resize()` modellato su `WaylandOutput::resize()`
(`wayland_output.cpp:293-303`) più una richiesta nel protocollo. **Una dozzina di righe upstream.**

> ### ✅ E QUELLE RIGHE SONO GIÀ STATE SCRITTE — nove giorni prima di questo studio
>
> *[I] `kwin!7932` «screencast: Resizable Virtual Monitors», **unita il 29 luglio 2026** (commit
> `452707eb`, milestone **6.8**), con `kpipewire!205` e `krdp!113`.*
>
> **E il modo in cui l'hanno fatto è quello che ci serve.** Non una richiesta nuova nel protocollo —
> quella è stata **proposta e respinta** (`plasma-wayland-protocols!138` + `kwin!9519`, 1–2 luglio
> 2026, chiuse in un giorno) con questa motivazione di David Edmundson: *«We have this over pipewire
> […] Which is better because: things work the same in gnome; sandboxed clients using the portal can
> resize it»*. Il meccanismo scelto è **la negoziazione PipeWire**: il consumatore propone un
> `SPA_POD_CHOICE_RANGE_Rectangle` e **KWin segue la misura dello stream**, con i limiti 200×200 …
> 10000×10000.
>
> **Cioè: è esattamente il codice della nostra fase 6**, e il lato consumatore sono tre righe.
>
> ⚠ **Ma è la 6.8, cioè ottobre 2026**: su Trixie (6.3.6) non c'è, e non c'è nemmeno su sid. Da cui la
> conseguenza operativa, che vale più del fatto: **il ridimensionamento su KDE non è una funzionalità
> perduta, è una che arriva** — e il nostro codice va scritto **nella forma della negoziazione**, che
> è quella che diventa giusta da sé quando l'utente aggiorna. La strategia (A) resta il ripiego per
> le versioni che non ce l'hanno, non la strada principale.
>
> Da tenere d'occhio, perché è il tavolo su cui chiedere quel che ci manca:
> `plasma-wayland-protocols!130`, **una versione 2 del protocollo di cattura**, in bozza da marzo 2026.

#### 8.2-bis ⛔ La guardia obbligatoria: senza, la rinegoziazione si morde la coda

*Dal rapporto 16 §1.5, e non è una nostra deduzione: è un difetto **trovato da altri** durante la
revisione di `kwin!7932`, cioè proprio il lavoro che porterà il ridimensionamento in 6.8.*

**[I]** Nick Haghiri, 3 luglio 2026, sulla richiesta di merge di KWin:

> *«Resizing re-emits `outputsQueried()`, which triggers a full output reconfiguration, which can
> cause the stream to renegotiate again and call back into `resize()`. … this results in repeatedly
> tearing down and recreating the capture pipeline. Symptoms: the `ScreencastLayer` gets
> destroyed/recreated many times per session, PipeWire toggles `streaming ↔ paused` repeatedly, and
> video freezes intermittently.»*

La cura, nel codice unito ([C] `outputscreencastsource.cpp:170-181`), è **una riga**:

```cpp
void OutputScreenCastSource::resize(const QSize &size)
{
    if (m_output->pixelSize() == size) {   // ← senza questo, ciclo infinito
        return;
    }
    m_output->resize(size);
}
```

> #### ✅ E L'INPUT È STATO SCRITTO E PROVATO — 8 agosto 2026, voce 2
>
> *Le quattro differenze di §7.2 sono tutte nel codice, e tutte e quattro hanno una riga di banco.*
>
> | | Esito |
> |---|---|
> | `connectToEIS(7)` da REMOTIX | ✅ **concesso**, gettone 1, nessun permesso chiesto. ⚠ Il descrittore viaggia in una **lista a parte**: il tipo `h` porta solo un indice, e chi legge il corpo del messaggio prende uno **zero** — cioè lo standard input, un fd validissimo che punta alla cosa sbagliata |
> | la keymap | ✅ letta da libei: `English (US)`, come su GNOME |
> | la rotella | ✅ **scatti discreti nei due versi**, misurati. Il valore di RDP si passa quasi com'è |
> | le regioni | ✅ trovata per **geometria**: `0,0 1920x1080`, con `mapping-id «assente»` — cioè il criterio per chiave non poteva funzionare, ed è esattamente quel che questo documento prevedeva |
> | `org_kde_kwin_keystate` | ✅ **parla**, e `fetchStates` dà lo stato di partenza. Lo stesso `.desktop` della cattura lo autorizza: è un nome in più, come previsto |
>
> ⛔ **E la conferma che vale di più è negativa**: `EI_EVENT_KEYBOARD_MODIFIERS` non è mai arrivato,
> in nessuna prova. La riconciliazione dei lucchetti scritta per GNOME, su KDE, **non girerebbe** — e
> senza `keystate` sarebbe rimasta lì, scritta e morta, senza che nessun banco se ne accorgesse.

⛔ **E lo specchio vale per noi, che siamo il consumatore.** kpipewire applica la stessa guardia
([C] `pipewiresourcestream.cpp:467-475`): se la misura richiesta è **uguale** a quella già richiesta,
**non si segnala nulla**. Senza quella condizione, ogni cambio di formato del flusso richiama la
nostra richiesta di misura, che richiama un cambio di formato: video che si blocca a intermittenza e
flusso che sfarfalla fra `streaming` e `paused`.

> ⚠ **Perché conta adesso**: l'utente ha deciso (8 agosto) che il ridimensionamento si scrive **nella
> forma della negoziazione**, così da accendersi da sé su KWin 6.8. Quella forma **include questa
> guardia**: è la prima riga della funzione, non un'ottimizzazione. Chi la dimentica non vede il
> difetto su Trixie (dove il resize non funziona) e lo scopre **il giorno dell'aggiornamento a 6.8**.

#### 8.3 Le strategie residue, e il loro prezzo

| | Che cos'è | Prezzo |
|---|---|---|
| **(A)** chiudere lo stream e rifarlo con la misura nuova | l'unica via completa oggi | ✅ **su KDE non trascina l'input**: EIS e `fake_input` sono indipendenti dallo screencast, quindi **lo stato dei tasti premuti non si perde** — il prezzo che §5.8 di `SPECIFICA.md` accettava a malincuore su GNOME qui non si paga. Restano: un buco video di qualche fotogramma, un **nuovo nodo PipeWire**, e il riposizionamento delle finestre |
| **(B)** output virtuale grande + `stream_region` ricreata | economica: non tocca gli output | dà un **ritaglio**, non un desktop ridimensionato: le finestre massimizzate restano grandi. E la regione è `const`: va ricreata. Serve al *letterboxing*, non a MS-RDPEDISP |
| **(C)** `kde_output_management_v2` su una delle 15 misure comuni | solo per monitor fisici | fuori discussione su una sessione viva |
| **(D)** patch upstream | il pezzo mancante | la strada giusta se la fase 11 diventa un impegno lungo |

⛔ **E c'è un prezzo che nessuna delle quattro evita**: **ridimensionare un output ridispone le
finestre dell'utente**, per due vie [R] — `desktopResized()` → `rearrange()` →
`Window::checkWorkspacePosition()` (massimizzate, fullscreen, edge-keeping, correzione off-screen,
`window.cpp:4052-4253`), e il `PlacementTracker`, la cui chiave **contiene la geometria
dell'output** (`workspace.cpp:296-297`): ogni misura è una chiave, e **tornando a una misura già
vista le finestre vengono teleportate indietro**. In più `updateOutputs()` **annulla un
trascinamento in corso**. KWin stesso, quando subisce ridimensionamenti, li accorpa a un fotogramma
con il commento *«Output resizing is a resource intensive task»* (`wayland_output.cpp:342-349`).

> È lo stesso prezzo che su GNOME ha fatto scartare l'adattamento automatico di risoluzione (§3.1 di
> `SPECIFICA.md`, riquadro della fase 7 in `PIANO.md`). Su KDE quindi **MS-RDPEDISP è una scelta da
> ripesare**, non un lavoro da rifare: si può servire la misura chiesta **alla connessione** e
> accorpare i cambi con l'assestamento di R10-bis, che già abbiamo.

#### 8.4 I protocolli degli output, e i vincoli sulla geometria

**[R]** Nessuno dei protocolli di output è dietro un permesso:

| Protocollo | Versione | Che cosa dà |
|---|---|---|
| `kde_output_device_v2` | **11** | leggere tutto: geometria, misura fisica, modi, scala, EDID, `enabled`, uuid, VRR, HDR |
| `kde_output_management_v2` | **12** | scrivere: `enable`, `mode` (solo esistenti), `transform`, `position`, `scale`, `overscan`, … |
| `wl_output` | **4** | ha `name`/`description`: **è così che si ritrova `"Virtual-remotix"`** |
| `zxdg_output_manager_v1` | 3 | posizione e misura logiche |
| `wlr-output-management` | **assente** [✗] | — |

Vincoli e trappole [R]:

- ⛔ **su DRM `width`/`height` sono pixel**, non unità logiche — l'XML dice «logical» e krfb ci
  casca. **Si passa `scale = 1`**;
- ⛔ **la scala richiesta viene buttata via**: `generateConfig` la rimpiazza con `chooseScale()`
  (`outputconfigurationstore.cpp:507`, `607-656`), che su un `physicalSize` pari ai pixel dà sempre
  1.0;
- larghezza e altezza **pari** non sono richieste da KWin, ma le richiede il codificatore 4:2:0:
  vincolo nostro;
- ✅ **il metro dichiarato dal client Android non può arrivare a KWin**: `stream_virtual_output` non
  ha un argomento di misura fisica, e `DrmVirtualOutput` impone `physicalSize = size`. Anche se
  arrivasse, `chooseScale()` è difeso (`< 3 mm` → scala 1, con il commento *«these are all caused by
  the screen mis-reporting its size»*) e la scala è limitata a `[1.0, 3.0]`. Il filtro sul DPI di
  `misura.c` resta comunque necessario **per il nostro lato** (la superficie EGFX e il codificatore).

---

### 9. Gli appunti: più facili che su GNOME

**[R]** La via è **`zwlr_data_control_manager_v1` versione 2** (`wayland_server.cpp:386`), e
**non è in lista nera**: nessun permesso, nessun `.desktop`. `ext_data_control_v1` non esiste in
6.3.6 [✗], e il portale RemoteDesktop di KDE dichiara `clipboard_enabled: false`
(`remotedesktop.cpp:264`) — la via GNOME (la clipboard dentro la sessione di controllo) **non ha
equivalente**, e non serve.

**Leggere**: `get_data_device(seat)` → il server manda **subito** `data_offer` + gli `offer(mime)` +
`selection`; poi `receive(mime, fd)` e si legge fino a EOF, mentre il proprietario scrive.
⚠ Un `offer(mime)` può arrivare **dopo** `selection`: l'elenco dei tipi non è completo all'istante
dell'evento.

**Scrivere**: `create_data_source()` → `offer(mime)` → `set_selection(source)`. ⚠ **Un source si usa
una volta sola** (`error_used_source`), e quando qualcuno legge riceviamo `send(mime, fd)` con KWin
che **chiude subito la propria copia del fd**: scrivere e chiudere è a nostro carico, e **senza
bloccare** il loop (una pipe da 64 KB con un consumatore lento ci blocca).

**Le tre asimmetrie di Mutter, riposte a KWin** [R]:

| La domanda | Mutter | **KWin** |
|---|---|---|
| Chi si ricollega riceve un annuncio? | **no**, e ci è costato | ✅ **sì**: `registerDataControlDevice()` manda subito selezione e primary selection (`seat.cpp:228-229`) — ⚠ se non c'è selezione manda un annuncio **vuoto**, non l'assenza di annuncio |
| L'annuncio torna indietro dopo una nostra scrittura (eco)? | sì | ⛔ **sì**: `setSelection()` cicla su **tutti** i data control device, **compreso l'originatore** (`seat.cpp:1257-1259`), e il filtro «stessa selezione» non aiuta perché ogni source è nuovo |
| Esiste un interruttore irreversibile (`DisableClipboard`)? | **sì**, e ci ha ucciso gli appunti | ✅ **no** [✗]: la clipboard non appartiene a una sessione |

⛔ **Due trappole dell'eco**, da evitare per costruzione: leggere l'eco significa farsi chiedere i
dati **dal proprio source** (stallo, se la lettura è sincrona); girarlo al client RDP significa
entrare nel ciclo. Il criterio robusto: **ignorare il primo `selection` che arriva dopo un nostro
`set_selection`**, confrontando anche la lista dei tipi. **[?]** Nel protocollo non c'è un serial né
un'attribuzione.

**I due coinquilini** [R]:

- **klipper** *rimette* l'ultimo elemento quando la clipboard si svuota, marcandolo
  `application/x-kde-onlyReplaceEmpty` (`klipper/systemclipboard.cpp:403-411`): se distruggiamo il
  nostro source senza sostituirlo, **il contenuto precedente torna**. E si difende dai cicli con
  **10 cambi al secondo** (`:50`): non superarli. ⚠ E KWin ha un aggiramento dedicato
  (`seat.cpp:200-226`) che **annulla in silenzio** un `set_selection` che dichiari quel tipo mime:
  **non usarlo mai**;
- **la sponda Xwayland**: X11 → Wayland è incondizionato; **Wayland → X11 solo quando una finestra
  Xwayland è attiva** (`xwayland/clipboard.cpp:88-100`, con il commento *«shield against snooping X
  windows»*), e si recupera al primo `windowActivated`. ⛔ **Una prova con `xclip` fallisce senza
  errore**: è la forma di banco verde su difetto vivo che `LEZIONI.md` §2.2 elenca.

#### 9.1 ✅ SCRITTA E PROVATA — 8 agosto 2026, `prove/fase11-appunti.sh`

```
OK  la sessione ha copiato qualcosa: 6 tipi
OK  il client ha «SESSIONE-VERSO-CLIENT-àèìòù-ok»
OK  la sessione incolla «CLIENT-VERSO-SESSIONE-àèìòù-ok»
OK  nessun ciclo (2 annunci veri, 1 eco buttata)
OK  l'eco e' arrivata ed e' stata riconosciuta
guasti: 0
```

Sta in **`src/appunti_wlr.c`**, e il nome dice `wlr` non `kwin` di proposito: il protocollo è di
wlroots, quindi il file serve già anche i compositori di XFCE e LXQt (§3.8 di `SPECIFICA.md`). La
porta `appunti.h` è rimasta una, con `appunti.c` ridotto a smistamento e la strada di Mutter spostata
in `appunti_mutter.c` — la stessa forma di `compositore.c`.

> #### ⛔ La guardia contro l'eco: il criterio di §9 era più debole del necessario
>
> «Ignorare il **primo** `selection` dopo un nostro `set_selection`» è una regola a tempo, e le
> regole a tempo si sbagliano quando due cose capitano insieme. Il criterio scritto è invece **di
> stato**: si ignora un annuncio se **la sorgente è ancora nostra** *e* i tipi coincidono.
>
> Regge perché l'ordine lo garantisce KWin: quando qualcun altro copia, è lo stesso `setSelection` a
> mandare prima `cancelled` alla vecchia sorgente e poi l'annuncio ai device. A quel punto «la
> sorgente è nostra» è già falso e l'annuncio passa. Nessun contatore, nessuna finestra temporale.

> #### ⛔ `POLLHUP` vale come «pronto», e trattarlo da guasto costa una diagnosi sbagliata
>
> *[M, 8 agosto 2026 — il primo giro del banco]*
>
> Chi possiede gli appunti scrive e chiude. Con dati corti la `poll` può tornare con **`POLLHUP` e
> basta**: i byte sono nel tubo, ma nessuno li ha ancora letti. Il codice guardava solo `POLLIN` e
> concludeva «non ha risposto» — **subito**, scrivendo a registro una scadenza di cinque secondi
> *che non era mai passata*. Il registro diceva `entro 5000 ms` a tre secondi dall'annuncio, e quel
> numero impossibile è stato l'unico indizio.
>
> In lettura `POLLHUP` è un esito (la `read` che segue dirà zero); in scrittura no, lì vuol dire che
> chi incollava se n'è andato.

⚠ **E l'annuncio non si consegna quando arriva `selection`**: un `offer(mime)` può arrivare dopo, e
un elenco monco fa incollare la cosa sbagliata senza che nessuno se ne accorga. La pompa fa un giro
completo — `wl_display_roundtrip` — e *poi* consegna.

---

### 10. Il sistema attorno: energia, blocco, credenziali, audio

#### 10.1 ✅ La cura di §3.4-bis funziona, e Plasma **nasconde**

**[R]** `sessionmanagementbackend.cpp:108-121` accende la voce di menu solo se logind risponde
`"yes"` o `"challenge"`; i valori di difetto sono `false`, e i consumatori usano `visible:` /
`addIfValid`. Quindi `sleep.conf` + la regola polkit di §3.4-bis di `SPECIFICA.md` **valgono
identiche su KDE**, e in dote arriva che `canSuspend=false` porta l'auto-sospensione di powerdevil a
`NoAction` da sé.

⛔ **Ma la regola polkit va scritta `no`, non *auth_admin***: `"challenge"` **mostra** la voce.

#### 10.2 ⛔ Su KDE c'è un secondo comandante dell'inattività, e il blocco si accende da sé

Due difetti di configurazione che una sessione remota incontra dopo pochi minuti, entrambi **[R]**:

| | |
|---|---|
| powerdevil ha **«spegni lo schermo dopo 10 minuti» acceso per difetto**, indipendente dalla cura di logind | `powerdevilsettingsdefaults.cpp:61-80` |
| `kscreenlockerrc [Daemon] Autolock` vale **`true`** con `Timeout=5` minuti | `kscreenlockersettings.kcfg:8-18` |

**La via precisa per inibire**: `org.kde.Solid.PowerManagement.PolicyAgent.AddInhibition(types=4, …)`
— dove `4` è `ChangeScreenSettings` e **implica** `InterruptSession`
(`powerdevilpolicyagent.cpp:737-745`); nessun controllo di permesso, effetto dopo **5 s**, si
rilascia da sé alla caduta del nome D-Bus. ⚠ La via freedesktop
(`org.freedesktop.PowerManagement.Inhibit`) mappa **solo** su `InterruptSession`
(`powerdevilfdoconnector.cpp:84-93`): **non ferma lo schermo.**

⛔ **E a blocco attivo la nostra inibizione viene ignorata** (`powerdevilpolicyagent.cpp:509`):
spegnere il locker non è una comodità, è **una dipendenza**. La leva è
`kwin_wayland --no-lockscreen` (`main_wayland.cpp:550-556`) — che le unità systemd stock **non
passano**, perché su Wayland il blocco è di KWin (`ksmserver/main.cpp:171-175`).

Due note che ridimensionano il problema, entrambe **[R]**: la cattura **non si ferma** al blocco (ma
la scena rende il lockscreen, quindi si vedrebbe **l'immagine di blocco**), e **l'input iniettato
raggiunge il greeter** — cioè l'utente remoto può sbloccare digitando. Il blocco è una seccatura,
non un'esclusione. E l'input iniettato **azzera i timer di inattività** (EIS →
`simulateUserActivity`), quindi una sessione usata non si blocca.

#### 10.3 ⛔ Senza nessun output, KWin si autoblocca

**[R]** `workspace.cpp:1216-1223`: con zero uscite abilitate il Workspace monta un
`PlaceholderOutput` con render loop inibito **e un filtro che inghiotte tutto l'input**. **Lo schermo
virtuale è una precondizione, non un risultato**: fra la morte di uno stream e la creazione del
successivo (strategia (A) di §8.3) si passa da lì.

#### 10.4 Le altre voci, in breve

| | **[R]** |
|---|---|
| **kwallet** | nessuno lo avvia in questo albero; il rischio di un dialogo di credenziali in una sessione non presidiata resta da misurare **[?]** |
| **Il sink audio** | **zero righe di Plasma toccano i dispositivi audio**, e la lista di preferenze di Phonon è stata svuotata (`kdeplatformplugin.cpp:128-149`). La scelta di §7.5 di `REFERENCE.md` — creiamo noi il sink virtuale e ne catturiamo il monitor — **si riusa identica**. Conferma finale: una misura, non un lavoro |
| **Notifiche che compaiono da sole** | ⛔ il modulo kded `devicenotifications` (autoload `true`) fa comparire *«Display Detected/Removed»* **a ogni schermo virtuale che creiamo o distruggiamo** (`devicenotifications.cpp:290-351`) — cioè, con la strategia (A), **a ogni cambio di risoluzione** |
| **Permessi D-Bus** | **nessun controllo** su nessuna interfaccia di sistema di KWin/Plasma/powerdevil, salvo `ScreenShot2` e `PlasmaShell.evaluateScript` |
| ~~**Rischio da chiudere per primo**~~ **misura M12, corretta l'8 agosto** | il `QMessageBox` modale *«Plasma Failed To Start»* c'è (`shell/main.cpp:176-179`), **ma non è il primo rischio, e non scatta al primo fallimento.** Rileggendo `shell/main.cpp:160-181`: al primo errore di contesto OpenGL plasmashell **scrive `SceneGraphBackend=software` in `kdeglobals` — `Global | Persistent` — e si riavvia da sé** (`QProcess::startDetached`); il dialogo compare **solo al secondo giro**, se anche il ripiego software fallisce. ⛔ **Il rischio vero è quindi un'altra cosa: una sessione avviata senza GPU lascia una configurazione permanente** che rende software il rendering anche quando la GPU torna. [M] Nella sessione misurata, **con** la GPU: zero righe `Open GL context could not be created` e **nessun `SceneGraphBackend` scritto**, come deve essere. ⚠ La riproduzione del caso «senza GPU» non è stata fatta: negare la GPU al solo compositore non basta (plasmashell è un'altra unità), servirebbe negarla a tutta la sessione |
| **Le regole di sessione** (le nove combinazioni di §3.4) | non dipendono dal desktop: logind è lo stesso. **Niente da rifare**, salvo verificare che il *tipo* di sessione si comporti come su GNOME **[?]** |

#### 10.5 ⛔ Il cursore del volume non governava niente — e non era colpa di KDE

*[M, 8 agosto 2026, aperto dall'utente: «se abbasso il volume l'audio resta sempre alto; in pratica
audio del server e del client sono scollegati»]*

Il sink virtuale lo creiamo noi (§7.5 di `REFERENCE.md`) e ne catturiamo il monitor. **In PipeWire
il volume di un nodo si applica a valle della presa del monitor**, e la proprietà che sposta la
presa — `monitor.channel-volumes` — vale **`false`** se non la si chiede. Chi crea il sink con
`pactl load-module module-null-sink` non se ne accorge mai, perché `pipewire-pulse` la mette da sé
per compatibilità con PulseAudio, dove il monitor è sempre stato a valle del volume. Noi il sink lo
creiamo a mano, con `pw_core_create_object`, e ce la scordavamo.

La misura, tono a 440 Hz di ampiezza nota (25,9 % del fondo scala), letto sul monitor:

| volume del sink | `monitor.channel-volumes` **non chiesta** (com'era) | chiesta (sink di `pactl`) |
|---|---|---|
| 100 % | 25,39 % | 25,39 % |
| 25 % | **25,39 %** | 0,40 % |
| 10 % | — | 0,03 % |
| 0 % | **25,39 %** | 0,00 % |

I numeri della colonna di destra non sono «quasi giusti»: sono **esattamente** la curva cubica di
PulseAudio (0,25³ = 1,56 %, e 25,9 × 0,0156 = 0,40). La colonna di sinistra è piatta: il volume non
arriva, **mute compreso**. Nella sessione viva il nodo era a `channelVolumes 0.0` e `mute true`
mentre il client riceveva il segnale intero.

✅ **Cura**: `"monitor.channel-volumes", "true"` fra le proprietà del sink, in `suono.c`.

> ⚠ **Il verso conta, ed è il motivo per cui questo cursore è l'unico che può funzionare.** RDP ha
> un solo PDU di volume, `SNDC_SETVOLUME`, e va **dal server al client** — noi lo mandiamo a fondo
> scala alla scelta del formato (`altoparlante.c`). **Non esiste il verso opposto**: un client non
> ha modo di dire al server «abbassa». Quindi l'unico cursore che governa davvero il livello è
> quello che si vede **dentro** la sessione, e va fatto funzionare.

#### 10.6 Le voci di menu che non possono funzionare, tolte dal menu

*[chiesto dall'utente, 8 agosto 2026: «sarebbe meglio nascondere le voci di *switch user* e *lock*
(anche se non funzionano, ed è il comportamento corretto)»]*

In una sessione servita da REMOTIX **«Blocca schermo» e «Cambia utente» non possono funzionare**, ed
è giusto così: il locker lo spegniamo noi con `--no-lockscreen`, perché a blocco attivo powerdevil
ignora le inibizioni (§10.2), e cambiare utente vorrebbe dire un display manager che qui non c'è. Ma
**una voce che non fa niente è peggio di una voce che manca**: chi la preme conclude che il server è
rotto.

La leva è **KIOSK**, cioè `KAuthorized`. I nomi delle azioni non si indovinano, sono quelli che
Plasma interroga davvero:

| che cosa governa | azione | dove |
|---|---|---|
| `SessionManagement::canLock()` | `lock_screen` | `libkworkspace/sessionmanagement.cpp:126-129` |
| `SessionManagement::canSwitchUser()` | `start_new_session` | `libkworkspace/sessionmanagement.cpp:121-124` |
| `SessionsModel::canSwitchUser()` | `switch_user` | `components/sessionsprivate/sessionsmodel.cpp:45` |

⚠ **`switch_user` e `start_new_session` servono tutti e due**: il primo governa l'elenco delle
sessioni, il secondo il pulsante. Toglierne uno lascia mezza interfaccia.

Il file si scrive in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals` e la cartella si mette **in testa a
`XDG_CONFIG_DIRS`**, dove KConfig la legge come configurazione di *sistema*:

```ini
[KDE Action Restrictions][$i]
action/lock_screen=false
action/start_new_session=false
action/switch_user=false
```

> ⚠ `[$i]` non è decorativo: senza, il `kdeglobals` dell'utente — che sta più in alto — rimette le
> voci al loro posto.
>
> ⚠ `/etc/xdg` **si tiene in coda, non si sostituisce**: da lì viene `menus/plasma-applications.menu`,
> cioè proprio il file che `XDG_MENU_PREFIX` va a cercare. Sostituirlo spegnerebbe la cattura per la
> strada di §3.3-bis.
>
> ⛔ E **`logout` non si tocca**: è la strada con cui si chiude la sessione, e quella su cui poggia
> la sentinella di uscita.

Non si scrive in `~/.config`: quel che imponiamo vale per la sessione servita, e non deve cambiare
la configurazione che l'utente si è scelto né sopravvivere alla macchina. Conseguenza: **ha effetto
dal prossimo avvio di sessione**, non su una sessione già viva.

---

### 11. `kpipewire`: il codice che fa il nostro stesso lavoro

È il pezzo più direttamente trasferibile di tutto KDE: consuma PipeWire e **codifica in H.264**.

#### 11.1 Danno e sincronizzazione: **non li fa**, e il perché è la risposta

**[R]** `SPA_META_VideoDamage` è chiesto **solo** se qualcuno chiama `setDamageEnabled(true)`, e
**nessuno lo chiama** in tutto l'albero (`pipewiresourcestream.cpp:68`, `369-379`; zero chiamanti in
`src/` e `tests/`). Quando arriva, l'unico consumatore è un **overlay di debug** che disegna i
rettangoli in rosso (`pipewiresourceitem.cpp:295-310`). Di sincronizzazione **non c'è niente**: zero
`SPA_META_SyncTimeline`, zero `poll()` su un fd di buffer, zero ioctl, zero `eglCreateSyncKHR`, zero
`glFinish` [✗].

**E non è una svista**: è il lato consumatore di quel che §4.6 e §4.8 dicono del produttore — KWin
ridisegna il fotogramma intero e si sincronizza lui. Il danno, su KDE, **è un suggerimento**.

> ✅ **Conclusione che vale per tutto il progetto**: il difetto delle schermate alternate (R29) **è di
> Mutter, non del modello PipeWire**. E la cura che abbiamo scritto — la superficie di accumulo — su
> KWin non serve.

#### 11.2 Le tre cose da copiare

1. ⛔ **Per la codifica in GPU si chiede solo `DRM_FORMAT_MOD_LINEAR`** (`vaapiutils.cpp:119-135`):
   RadeonSI **rifiuta** i buffer con DCC, iHD li **accetta e poi forza LINEAR internamente** — cioè
   accetta e sbaglia in silenzio, la nostra forma di guasto preferita (R27, R30). Giorni risparmiati.
2. **Il contesto VAAPI non si crea: lo si fa creare al grafo di filtri.**
   `hwmap=mode=direct:derive_device=vaapi,scale_vaapi=format=nv12:mode=fast`, `hw_device_ctx`
   assegnato a **ogni** filtro *prima* di `avfilter_graph_config()`, e poi lo si prende dal
   buffersink con `av_buffersink_get_hw_frames_ctx()` (`h264vaapiencoder.cpp:89-97`, `151`). Cura
   preventivamente il terzo caso di R30 — l'`h264_vaapi` che si è aperto con un contesto proprio.
3. **Quando un modificatore fallisce non si spegne il DMA-BUF**: si toglie *quel* modificatore e si
   rinegozia, rientrando nel thread giusto con `pw_loop_add_event`/`pw_loop_signal_event`
   (`pipewiresourcestream.cpp:261-273`). È anche il meccanismo per cambiare strada a caldo senza
   rifare la cattura — cioè la nostra R30, scritta da altri.

Regalo misurato da altri, due ore per provarlo: `flags +mv4` e `-flags +loop` su **tutti** gli
encoder, con il commento *«disable motion estimation … speeds up encoding by an order of
magnitude»*.

#### 11.3 Che cosa kpipewire **non** fa

| | |
|---|---|
| **controllo del bitrate** | ⛔ **assente** per H.264: mai `bit_rate`, mai `rc_mode`. È **lo stesso vuoto di `gnome-remote-desktop`** (§9.1) e di R31: su quel punto REMOTIX resta solo, e ora la solitudine è confermata da due riferimenti invece di uno |
| ridimensionamento a caldo | assente |
| cursore su DMA-BUF | non composto |
| `max_b_frames` | **0 in ogni encoder** — conferma indipendente di R11 |

**Quattro difetti da non copiare** [R]: `stride*height*4`, un `ceil` su una divisione intera, la
cadenza in aritmetica intera con divisione per zero, `mapoffset` ignorato.

**Riusabile da un programma in C**, riscrivendo solo i tipi Qt: `queryDmaBufModifiers`,
`buildFormat`, la costruzione dell'`AVDRMFrameDescriptor`, e tutto `vaapiutils.cpp`. **Da
riscrivere**: il percorso software (tre copie per fotogramma), il bitrate, il danno, il cursore.

---

### 12. I riferimenti di KDE, e quanto valgono

#### 12.0 ⭐ `KRdp` — il riferimento vero, e lo studio l'aveva mancato

> ⛔ **Correzione del 7 agosto 2026, sera.** La prima stesura di questo documento diceva
> *«altre tracce di RDP in KDE: nessuna»*. **Era falso**, e per un errore di metodo che vale la pena
> registrare: la ricerca era stata fatta **dentro i repository clonati**, e `krdp` non era fra quelli.
> Cercare in casa propria non è cercare. Lo ha trovato una domanda dell'utente — *«su KDE qualcuno ha
> affrontato i problemi prima di noi: xrdp. Come fa con KWin?»* — e la risposta è che xrdp non
> c'entra (§12.3), ma **qualcun altro sì**.

**Che cos'è.** `KRdp` è il server RDP di KDE: **C++ su FreeRDP**, con `kpipewire` per i pixel, ed è
quel che Plasma 6.2+ presenta come *«Condivisione del desktop (RDP)»* nelle Impostazioni di sistema.
**4 222 righe** nella 6.3.6 di Trixie, 5 877 nel master. Cioè: stessa libreria RDP, stesso
compositore, stessi client, e un ordine di grandezza in meno di `gnome-remote-desktop` — che lo rende
leggibile per intero in una sessione.

**La conferma che pesa più di tutte** — il suo file `.desktop`, `server/org.kde.krdpserver.desktop.cmake`:

```ini
[Desktop Entry]
Type=Application
Exec=@CMAKE_INSTALL_PREFIX@/bin/krdpserver
NoDisplay=true
X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1
```

**La via del permesso di §3 non è una nostra deduzione: è quel che fa il server RDP di KDE**, per la
cattura *e* per l'input, in tre righe e senza un dialogo.

**Come è fatto** — tutto **[R]**, sul master salvo dove indicato:

| | |
|---|---|
| **Dove gira** | `server/app-org.kde.krdpserver.service.in`: `Type=exec`, `After=plasma-core.target`, **`WantedBy=plasma-workspace.target`** — cioè **dentro** una sessione Plasma già in piedi, come servizio d'utente. ⛔ **Non avvia la sessione**: è la differenza strutturale con REMOTIX, e il motivo per cui KRdp non risolve la nostra §6 |
| **La cattura** | due strade, e ⛔ **quella predefinita è il portale**, non i protocolli di Plasma: la diretta si sceglie con **`--plasma`** (`server/main.cpp:128`), e **l'unità systemd non lo passa**. La diretta è `PlasmaScreencastV1Session.cpp:173-199` (`createVirtualMonitorStream`, `createOutputStream`, `createWorkspaceStream`, tutte con cursore `Metadata`) |
| **La misura** | `server/main.cpp:49-52`: **`--virtual-monitor 1920x1080@1`**, opzione a riga di comando. La misura la decide **chi avvia il servizio**, non il client. ⛔ **E senza `--plasma` non può funzionare**: KRdp chiede al portale il tipo di sorgente «virtuale» (4), che `xdg-desktop-portal-kde` **non annuncia**, e il cui dialogo non costruisce alcun elenco (`screenchooserdialog.cpp:148-231`) — pagina vuota. Cioè: **lo schermo virtuale esiste solo sulla strada diretta** |
| **L'input** | ⛔ **`fake_input`, non EIS**: `PlasmaScreencastV1Session.cpp:26-35, 164-165` lega `org_kde_kwin_fake_input` **v4** e chiama `authenticate("krdpserver", "")`. Non usa il backend EIS di KWin |
| **La keymap** | ✅ **la legge dal `wl_seat`**, essendo client Wayland: `wl_keyboard.keymap` → `xkb_keymap_new_from_string` (`:121-143`). Poi `keycodeFromKeysym()` cerca il tasto che produce il simbolo e **applica i livelli** — livello 1 → `KEY_LEFTSHIFT`, livello 2 → `KEY_RIGHTALT` (`:68-89`, `:265-278`), con `EVDEV_OFFSET = 8`. È **il nostro percorso Unicode**, scritto da loro senza libei |
| **I due codec** | ✅ **la nostra stessa struttura** (R3): `VideoStream.cpp:635-656` — H.264 se il client dichiara AVC **e** YUV420, altrimenti **RemoteFX Progressive** (`progressive_context_new(TRUE)`). `KRDP_DISABLE_H264` forza il ripiego. ⚠ Il profilo è **`H264Baseline`** (`:273`), non *Constrained High* come R11 |
| **La codifica** | delegata a `kpipewire`: `PipeWireEncodedStream` con `EncodingPreference::Speed`, `ColorRange::Full`, `quality` 0–100 (`--quality`), `maxFramerate`, `maxPendingFrames`. Nessun bitrate dichiarato — coerente con §11.3 |
| **Il regolatore** | ✅ **lo stesso della nostra fase 7**: `NetworkDetection::rttChanged` → `updateInFlightWindow()`, `hasInFlightCapacity()`, coda dei fotogrammi e un thread di spedizione (`VideoStream.cpp:376-398`). L'ultimo commit del master è *«smooth the RTT used for the in-flight window»* |
| **Il danno** | ✅ **lo usa**, al contrario di krfb: `setDamageEnabled(true)` sul percorso Progressive (`:299`), accumulo del danno fra i fotogrammi in coda (`:456-466`) e conversione in `REGION16` di FreeRDP (`:201-238`) — con i bordi **esclusivi**, `right = rect.right() + 1`: la nostra R5, confermata da un terzo |
| **Il ridimensionamento** | ⚠ `DisplayControl.cpp` **esiste solo nel master**: `MaxNumMonitors = 1`, factor 8192 (identici ai nostri), accetta **solo** `NumMonitors == 1`, e il layout arrivato va a **`VideoStream::setRequestedSize`** (`server/SessionController.cpp:58`) → cioè **all'encoder**, non all'output. ⛔ **Nemmeno KRdp ridimensiona lo schermo virtuale**, e nella 6.3.6 di Trixie **non ha il ridimensionamento affatto** (`kpipewire` 6.3.6 non ha nemmeno `setRequestedSize` [✗]) |
| **La sicurezza** | `RdpConnection.cpp:426-428`: `NlaSecurity = !usePam`, **`TlsSecurity = usePam`** — cioè **NLA per difetto, e TLS puro quando si autentica con PAM**, che è la nostra scelta (§3.6). E PAM c'è davvero (`pam_appl.h`, `:88-134`) |
| **Le capacità** | `ColorDepth = 32`, `SupportGraphicsPipeline`, `NetworkAutoDetect = true`, e rifiuti espliciti se mancano pipeline grafica o pointer cache (`:573-584`): le nostre §3.2 e §3.3 |
| **Una trappola che noi non avevamo** | `VideoStream.cpp:575-588`: *«Windows clients (mstsc) send CapsAdvertise **twice**»* — e KRdp tratta il secondo come **reset del canale**, distruggendo le superfici e rifacendole. La nostra R2 dice che un secondo `CapsAdvertise` è lecito solo da 10.3; questo dice **che cosa farne** |

**Che cosa non risolve per noi**, e va detto: **non avvia la sessione** (vive dentro Plasma, quindi la
nostra §6 resta interamente nostra), **non ridimensiona** (§8 resta aperta), e usa la strada
dell'input **vecchia** — dove noi abbiamo già scritto quella nuova. Non ho ancora letto in dettaglio
`Clipboard.cpp`, `Cursor.cpp`, `NetworkDetection.cpp` e `PortalSession.cpp`: sono **la prossima
lettura**, e sono tutti pezzi che ci servono.

#### 12.0-bis ⛔ I difetti di KRdp da non ripetere — l'elenco che vale più del codice

*Riversato dai rapporti 12 §6.4, 14 §2.2 e 15 §8.1-8.2 l'8 agosto 2026 (passo 0 del piano di lavoro).
Il ramo di sviluppo di KRdp ne ha corretti diciotto rispetto alla 6.3.6 di Trixie: **ogni riga
corretta è un difetto che noi non dobbiamo scrivere**. Qui stanno i quattordici che ci riguardano,
in ordine di quanto morderebbero noi.*

| ⛔ | Il difetto | Dove, nella 6.3.6 | Che cosa ci insegna |
|---|---|---|---|
| **1** | **Il client senza AVC420+YUV420 veniva *disconnesso***: `qCWarning("Client does not support H.264…"); return CHANNEL_RC_INITIALIZATION_ERROR` | `VideoStream.cpp:308-313` | ⭐ **conferma la nostra R3 come necessità, non come lusso**: senza RemoteFX Progressive il nostro client Android non si collegherebbe affatto |
| **2** | **`RDPGFX_SURFACE_COMMAND` riempita a metà**: 10 campi su 13, gli altri **spazzatura di stack** — `contextId` compreso, che per AVC420 deve valere 0 | `:377-392` vs `freerdp/channels/rdpgfx.h:195-210` | **si azzera la struttura** (`= {}`) prima di riempirla. È della stessa famiglia del nostro difetto sul `MONITOR_DEF` (R5) |
| **3** | **Nessun codice di ritorno controllato**: `ResetGraphics`, `CreateSurface`, `MapSurfaceToOutput`, `StartFrame`, `SurfaceCommand`, `EndFrame` — tutti chiamati e ignorati | `:367`, `:376`, `:385`, `:411-414` | ⭐ *«un errore su `CreateSurface` diventa uno schermo nero senza una riga di log»* — **è il modo in cui abbiamo perso tempo noi** |
| **4** | **Nessuna `DeleteSurface`, mai**, e `ResetGraphics` chiamata con superfici vive | `:349-385` | le superfici **si accumulano nel client**. È precisamente quel che la nostra **R6** vieta |
| **5** | **`pendingFrames` (una `QSet`) usata da due thread senza lock** | `:118`, `:333`, `:344`, `:397` | corruzione della tabella hash e `erase` di un iteratore invalido: un crash che arriva a caso |
| **6** | **Nessuna contropressione**: si spediva tutto quel che c'era in coda | `:174-188` | su rete lenta il buffer TCP si gonfia: **secondi** di latenza che non recuperano più |
| **7** | **`queueDepth`/`SUSPEND_FRAME_ACKNOWLEDGEMENT` ignorati** con la finestra in volo attiva | `:677-692` (**anche nel master**) | **blocco eterno**: se il client dice «non aspettare i miei riscontri» e noi aspettiamo, non parte più niente. Quando è sospeso, **la finestra si disattiva** |
| **8** | **Nessun recupero dai riscontri persi** | idem | `totalFramesDecoded` **come pavimento**, e una scadenza per i fotogrammi in attesa |
| **9** | **`close()` chiudeva il canale *prima* di fermare il thread di spedizione**; il distruttore era **vuoto** | `:194-207`, `:143-145` | l'ordine giusto è: **fermare i flussi → aspettare i thread → svuotare le code → distruggere le superfici → chiudere il canale** |
| **10** | **Lo stimatore di cadenza con la condizione sempre falsa**: `(estimate.timeStamp - now) > periodo` con `timeStamp <= now`, cioè differenza **negativa** | `:427-433` | perdita di memoria illimitata **e** una media calcolata su tutta la sessione, che quindi non si adatta più a niente. ⭐ Un difetto che **nessuna prova funzionale trova**: il programma funziona, solo non regola più |
| **11** | **Misura di banda aperta e chiusa attorno a *ogni* fotogramma** | `:353`, `:416` | la misura di banda è un giro di richiesta/risposta: farla 60 volte al secondo **la rende rumore** |
| **12** | **Numero di sequenza `uint32` in un campo a 16 bit**: l'RTT muore dopo **~76 minuti** e l'hash delle richieste cresce senza limite | `NetworkDetection.cpp:69`, `:75`, `:244-252` | contatore **`uint16_t`** con giro esplicito, e **scadenza** delle richieste senza risposta. ⚠ Ed è una prova che va fatta **a 90 minuti**, non a cinque |
| **13** | **La cadenza delle sonde appesa ai risvegli del socket**: a desktop fermo la misura **si spegne** | `RdpConnection.cpp:563` | un timer vero, o un'attesa con **timeout** pari alla cadenza |
| **14** | **La rotella con `angleDelta/120`**, divisione **intera** | `PortalSession.cpp:161` | qualunque scatto sotto una tacca **si perde**. Conferma §7.2: si usa `ei_device_scroll_discrete(±120)` e si passa il valore quasi com'è |

> ⭐ **E il difetto più istruttivo di tutti sta nel rapporto 14 §2.2**: nella 6.3.6 **il verso di
> pressione e rilascio dei tasti era invertito**. È lo stesso punto che nel nostro `input.c:218`
> abbiamo verificato essere giusto (`gboolean premuto = !(flags & KBD_FLAGS_RELEASE)`). Un server RDP
> maturo, dentro KDE, ha spedito per una release un difetto che si vede alla prima parola digitata:
> **la prova sui tre client non è burocrazia.**

#### 12.1 `krfb` — per metà, e non per la metà che si spera

`gnome-remote-desktop` era un riferimento pieno: stesso linguaggio, stessa libreria RDP, stesso
compositore, 68 730 righe. **krfb è ~5 000 righe di C++ e parla VNC**, e su questo ramo
⛔ **non apre nemmeno la porta**: `RfbServer::start()` racchiude `rfbInitServer` in
`if (passwordSet())` e torna `true` comunque, e nel percorso normale nessuno chiama `setPasswordSet`
(`rfbserver.cpp:114`). Va letto come **archivio**, non come metro.

**Le tre cose per cui vale** [R]:

1. ✅ **conferma il nostro modello di palco**: un framebuffer per processo, vivo dall'avvio alla
   chiusura, indifferente al connettersi dei client (`rfbservermanager.cpp:113-133`;
   `startMonitor`/`stopMonitor` **vuoti**);
2. **la sequenza dei pixel su KWin in un file solo** (`pw_framebuffer.cpp:125-346`), traducibile in
   C quasi riga per riga se un giorno passassimo dal portale — e la scelta chiave: aprire una
   sessione **RemoteDesktop** e innestarvi `ScreenCast.SelectSources`, che su KDE compra **un solo
   dialogo** per schermo e input e l'accesso alla mega-autorizzazione;
3. **otto difetti reali che possiamo non pagare**, e due sono della famiglia che ci ha già morso:
   il **danno mai negoziato** (`setDamageEnabled` non è chiamato in tutto l'albero, quindi krfb
   accoda **lo schermo intero a ogni fotogramma**), e un `QTimer` a 50 ms che impone **20 fps** —
   cioè un tetto scritto in casa propria, esattamente il difetto dei nostri 18 (R32). Gli altri:
   `buttonMask` passato dove il portale vuole uno `state` 0/1 (`xdpevents.cpp:78` → pulsanti
   incastrati), doppio evento di rotella per scatto, uno scatto che arriva come `delta=±1 px`,
   `||` invece di `&&` nel cursore, pixel fisici dove servono unità logiche, e nessun ascolto della
   fine della sessione.

*(La prima stesura scriveva qui «altre tracce di RDP in KDE: nessuna». Era falso: vedi §12.0.)*

#### 12.4 Gli altri due, trovati cercando fuori casa

*[I]/[C], 7 agosto 2026. Sono la prova che il passo zero di `LEZIONI.md` §9 serve: nessuno dei due
stava nei repository che avevo scelto.*

| | |
|---|---|
| **Sunshine** | ha da maggio 2026 un `kwingrab.cpp` (772 righe) che parla **il nostro stesso protocollo diretto**, e che **si scrive da sé il file `.desktop`** con `X-KDE-Wayland-Interfaces` a runtime, aspettando 3 000 ms perché KWin lo veda. È la **terza implementazione indipendente** del cancello di §3, dopo KRdp e krfb: la via del permesso non è più un'interpretazione |
| **Chrome Remote Desktop** | il bug KDE **512620** è stato aperto da un ingegnere Google che sta portando CRD su KDE Wayland. È un quarto riferimento serio, e vale tenerlo d'occhio |

**E una cosa che nessuno fa** [✗]: **`kwin_wayland --drm` senza monitor**. Cercata nel codice, nei
bug, nelle wiki e nei forum: nessun precedente. La misura resta interamente nostra. Due bug
confermano però che **non stiamo aggirando una via ufficiale, perché non ce n'è una**: il **492285**
dice che `startplasma` non inoltra la scelta del backend al compositore (nessuna merge request), e il
**523735**, aperto sei giorni prima di questo studio, **chiede proprio la sessione headless** — e
nessuno l'ha risolta.

**Due regali dal fronte dell'input** [I]: `krdp!217` sta portando KRdp **a libei, rendendolo
obbligatorio** — cioè la strada che abbiamo scelto è la direzione in cui KDE si sta muovendo, e la
loro conversione a `fake_input` diventerà codice morto. E nella discussione di quella merge request
c'è la risposta parziale a una nostra misura aperta: **con libei il verso della rotella è quello di
Wayland**, senza l'inversione che il portale si porta dietro. Più, nel master di KWin,
`EIS_DEVICE_CAP_TEXT` (richiede libeis ≥ 1.6, non ancora disponibile): il giorno in cui arriva, il
nostro giro «carattere → keysym → tasto → livelli» diventa superfluo.

⚠ **E una precisazione sulle versioni**: Debian Trixie ha **krdp 6.3.5-1**, non 6.3.6 — il tag che
abbiamo clonato è una versione che sulla macchina dell'utente non c'è. Per le differenze fra 6.3.5 e
6.3.6 non ho materiale [?].

#### 12.3 `xrdp` — non affronta KWin: lo evita

*Verificato sul sorgente il 7 agosto 2026 (clone di `neutrinolabs/xrdp` master).*

La domanda «come fa xrdp con KWin?» ha una risposta secca: **non ci parla**. In tutto il codice C di
xrdp la parola *wayland* compare **11 volte**, e nessuna riguarda la cattura o l'input: sono nomi di
display (`"wayland-n"`), un commento, e **una riga che dichiara a `pam_systemd` il tipo di sessione**
(`sesman/libsesman/verify_user_pam.c:405-413`) quando il display non è X11 — cioè una predisposizione
di etichetta, non un'implementazione.

Che cosa fa invece: `sesman/sesexec/session.c` lancia **`Xorg`** (con `xorgxrdp`) oppure **`Xvnc`**, e
dentro quel server X esegue `sesman/startwm.sh`, che a sua volta chiama la sessione del desktop —
per KDE, `startplasma-x11`. Cioè xrdp fa girare **Plasma in sessione X11**, dove il compositore è
`kwin_x11` e la cattura è una cattura X11: nessun protocollo Wayland, nessun PipeWire, nessun
permesso da chiedere.

**Ne discendono tre cose per noi:**

1. ⛔ **xrdp non è un riferimento per la fase 11.** I problemi che stiamo studiando — il permesso
   della cattura, l'output virtuale, l'input su Wayland — nel suo modello **non esistono**. Il
   riferimento è `KRdp` (§12.0);
2. **quella strada esiste ancora, e funziona oggi**: Plasma 6.3.6 ha ancora la sessione X11
   (`plasma-workspace/login-sessions/plasmax11.desktop.cmake`, `startkde/startplasma-x11.cpp`,
   `kwin/src/main_x11.cpp`) [R]. È **la ragione per cui xrdp su KDE va**, ed è anche la ragione per
   cui non ci serve: §4.5 di `SPECIFICA.md` ha escluso le sessioni X11 — un secondo percorso completo
   di cattura e input — e KDE quella sessione la sta chiudendo;
3. e vale la pena registrarlo come **conferma della scelta di fondo del progetto**: il concorrente più
   diffuso non ha ancora affrontato Wayland, mentre REMOTIX su Wayland ha già un desktop che
   funziona.

#### 12.2 Il portale — da conoscere per scartarlo con cognizione

**[R]** Sette fatti che decidono:

| | |
|---|---|
| `ConnectToEIS` **esiste** in 6.3.6 | ed è **un inoltro di sei righe utili** a `org.kde.KWin.EIS.RemoteDesktop`: passare dal portale **non aggiunge nulla** rispetto a chiamare KWin, tranne il dialogo |
| l'output virtuale **non è annunciato** fra le sorgenti | `AvailableSourceTypes = Monitor\|Window` (`screencast.h:53-56`): solo l'utente può scegliere «schermo virtuale» nel dialogo |
| e la sua misura è **cablata a 1920×1080** | `screencast.cpp:299` — nessun modo di chiedere 4K, cioè il numero desiderato dall'utente |
| il nodo PipeWire lo crea e lo possiede **KWin** | `screencastmanager.cpp:84-90`; il portale attende `created` in un event loop bloccante con **timeout di 3 s** (`waylandintegration.cpp:354`) |
| i `Notify*` passano da `fake_input` | e portano due difetti: `NotifyPointerAxis` **inverte il segno di y** (`:434`) mentre `NotifyPointerAxisDiscrete` no, e `NotifyKeyboardKeysym` **non rilascia mai** il modificatore che premette (`:579-592`) |
| ⛔ `XDG_CURRENT_DESKTOP` deve valere **esattamente `KDE`** | altrimenti ScreenCast e RemoteDesktop **non vengono nemmeno registrati** (`desktopportal.cpp:43-44`). **Prima riga di qualunque diagnosi** |
| la mega-autorizzazione | §3.5: la scappatoia documentata per il non presidiato, ma **nessuna interfaccia scrive** quella voce |

---

### 13. Il conto per REMOTIX

#### 13.1 Che cosa conferma

| Decisione di REMOTIX | Conferma nel codice di KDE |
|---|---|
| **Parlare al compositore, non al portale** | il portale di KDE è **un client** dello stesso protocollo, e aggiunge solo il dialogo (§12.2) |
| **Il palco appartiene alla sessione, non alla connessione** | krfb lo pratica per costruzione (§12.1); e su KWin è obbligatorio: un `UNCONNECTED` smonta l'output virtuale (§4.9) |
| **R9** — l'ultimo fotogramma si conserva e si rispedisce | nessuna richiesta «mandami un fotogramma pieno» esiste [✗]; il pieno arriva solo alla ripresa da pausa |
| **Cadenza dichiarata «quando cambia»** | `framerate` **deve** essere `0/1`; il tetto è `maxFramerate` (§4.5) |
| **Lo stride si legge dal chunk** | `SPA_ROUND_UP_N(width*bpp, 4)`: non è `width × 4` |
| **Il codificatore senza fotogrammi B** | `max_b_frames = 0` in ogni encoder di kpipewire (§11.3) |
| **Il sink audio lo creiamo noi** | zero righe di Plasma toccano i dispositivi audio (§10.4) |
| **`libavcodec` invece delle API dei costruttori** | kpipewire scrive contro libav, non contro libva a mano — e il controllo del bitrate **non ce l'ha nemmeno lui** (§11.3) |
| **Le nove combinazioni di §3.4** | logind è lo stesso: niente da rifare |
| **Il conto dei tasti premuti** | KWin scarta ripetizioni e rilasci non appaiati, e rilascia tutto alla morte del client (§7.2) |
| ⭐ **Il `.desktop` come via del permesso** | **è quel che fa `KRdp`**, il server RDP di KDE, per la cattura *e* per l'input (§12.0) |
| ⭐ **I due codec sulla stessa pipeline** (R3) | `KRdp` fa la stessa scelta: H.264 se il client dichiara AVC **e** YUV420, altrimenti RemoteFX Progressive |
| ⭐ **Il regolatore a fotogrammi in volo con soglia dall'RTT** (fase 7) | `KRdp` ha lo stesso meccanismo, e nel master lo ha appena raffinato smussando l'RTT |
| ⭐ **I bordi esclusivi delle regioni** (R5) | `KRdp` scrive `right = rect.right() + 1`: terza fonte concorde |
| ⭐ **TLS puro con PAM** (§3.6) | `KRdp`: `TlsSecurity = usePam`, `NlaSecurity = !usePam` — la nostra scelta è anche la sua, quando autentica come noi |

#### 13.2 Che cosa smentisce, o corregge

1. ⛔ **`SPECIFICA.md` §3.8 va corretta**: dice *«KWin: cattura PipeWire via **portale**, input
   interfacce KWin, protocollo `kde-fake-input`»*. Il codice dice: cattura **via protocollo Wayland
   diretto** (il portale è un client come noi), input **via libei/EIS su D-Bus** (`fake_input` è la
   strada vecchia).
2. ⛔ **`REFERENCE.md` R32 e `LEZIONI.md` §3 riga 4**: *«KWin senza monitor disegna in software»* è
   contraddetto dal codice, e la nostra stessa tabella (DMA-BUF con fence) lo conferma. **Da
   rimisurare prima di correggere** (§5.1, §15).
3. ⛔ **Le misure dei 59–60 fps hanno due etichette da rivedere**: sono state prese con
   `KWIN_WAYLAND_NO_PERMISSION_CHECKS=1` (cioè scavalcando il cancello) e con `--virtual` +
   `stream_output` **senza `--xwayland`** — cioè su **KWin nudo**, non su una sessione Plasma, e non
   nella configurazione del prodotto (`stream_virtual_output`, che con `--virtual` **non funziona**).
   Il numero resta un fatto; la sua etichetta no.
4. ⛔ **La risoluzione dinamica non si fa come su GNOME** (§8): un output virtuale non si
   ridimensiona. Il prezzo che la fase 6 aveva estinto torna, in forma diversa — e su KDE **non
   trascina l'input**.
5. ✅ **Due debiti di GNOME non si presentano**: la connessione al bus di sessione che non
   sopravvive al logout (§6.6), e il difetto delle schermate alternate a copia zero (§4.6).
6. ⚠ **`banco/misura-cattura.c` va corretto prima di rimisurare su KWin**: `--fissa` non può
   negoziare (§4.5), e i buffer `SPA_CHUNK_FLAG_CORRUPTED` del cursore vengono contati come
   fotogrammi (§4.7).

#### 13.3 Che cosa conviene copiare, in ordine di resa

0. ⭐ **Leggere per intero `KRdp`** — 4 222 righe, cioè una sessione di lettura: è un server RDP
   sullo stesso compositore, con la stessa libreria, e ogni sua scelta è una risposta a una domanda
   che abbiamo (§12.0). Restano da leggere `Clipboard.cpp`, `Cursor.cpp`, `NetworkDetection.cpp` e
   `PortalSession.cpp`.
1. **Il `.desktop` con `X-KDE-Wayland-Interfaces`**, sul modello di
   `org.kde.krdpserver.desktop` (§12.0) o di `org.kde.krfb.virtualmonitor.desktop` (§3.2). È la
   chiave della fase, e sono tre righe.
2. **`ei_device_scroll_discrete(±120)`** invece del nostro `/120 → ×10` (§7.2): più semplice di
   quel che facciamo, e produce una rotella vera.
3. **Il solo `DRM_FORMAT_MOD_LINEAR` per la codifica in GPU** e **il contesto VAAPI creato dal
   grafo di filtri** (§11.2): due difetti silenziosi già pagati da altri.
4. **La rinegoziazione dei modificatori invece dello spegnimento del DMA-BUF** (§11.2).
5. **`AddInhibition(types=4)` di powerdevil** per non farsi spegnere lo schermo sotto i piedi
   (§10.2).
6. **`org.kde.Shutdown` come sentinella passiva del logout** (§6.5): due sottoscrizioni, zero
   rischio di tenere in ostaggio la sessione dell'utente.
7. **`KWIN_XKB_DEFAULT_KEYMAP` + `XKB_DEFAULT_*` nell'ambiente del compositore** (§6.7), se un
   giorno servisse *imporre* la disposizione invece di leggerla.

#### 13.4 Le scelte da mettere davanti all'utente, prima di scrivere

Sono decisioni di prodotto, non di tecnica, e `LEZIONI.md` §2.6 dice di metterle davanti **subito**.

> ⚠ **Erano tre; dopo il banco del 7 agosto 2026 ne restano due**, ed è un miglioramento: **la prima
> l'ha decisa la misura, non l'utente** (M2, §5.2). Vale la regola di
> `remotix-prove-sul-banco-non-sull-utente`: quel che si può misurare non si chiede.

> #### ✅ DECISO DALL'UTENTE l'8 agosto 2026 — tutte e tre, e nella direzione migliore
>
> | La domanda | La decisione |
> |---|---|
> | **La copia zero: adesso o dopo?** *(domanda nuova, nata dalle misure di §5.7)* | ✅ **adesso, dentro il lavoro su KDE.** Quindi **la cattura si scrive a copia zero dal principio**, con l'attesa della fence (§4.8) — non si scrive in memoria per poi tornarci sopra. È la condizione dei 60 fps a 4K |
| **Il ridimensionamento su Trixie** | ✅ **misura fissa alla connessione**: nessun buco video, nessuna finestra riposizionata, nessuna notifica di sistema. ⛔ **E si scrive nella forma della negoziazione PipeWire** (§8.2), che è il codice della fase 6: così su **KWin 6.8** il ridimensionamento vero si accende da sé, senza che nessuno riscriva niente |

> #### ⛔ «L'IMMAGINE SI SCALA NEL CLIENT» ERA FALSO — e l'ha trovato l'utente
>
> *[M, 8 agosto 2026: «non riesco a vedere tutto lo schermo, la risoluzione sembra ignorata».]*
>
> La decisione qui sopra è stata scritta con accanto la frase «l'immagine si scala nel client», e
> quella frase **non era mai stata misurata**. `xfreerdp3` non scala niente: apre una finestra
> **grande quanto la tela dichiarata**. Con il desktop a 1920×1080 e uno schermo più piccolo, la
> finestra non ci sta — e chi guarda vede «la risoluzione che ho chiesto viene ignorata», che è
> esattamente quel che succede.
>
> **La scalatura lato client esiste, e passa da `MAPSURFACETOSCALEDOUTPUT`** — che il **7 agosto**
> avevamo già misurato essere resa da **un client su tre**: `xfreerdp3` sì, mstsc no, RDM la dichiara
> spenta (§10.2 di `REFERENCE.md`). Cioè: la smentita era già in casa, su un'altra pagina, e la
> decisione dell'8 agosto l'ha ignorata.
>
> ⭐ **Quel che regge davvero della decisione, ed è più forte di quel che si pensava**: la misura del
> desktop la fissa **la prima connessione**, e su KDE è REMOTIX ad avviare la sessione — quindi il
> desktop nasce *esattamente* della misura chiesta. Il prezzo non è un'immagine scalata: è che **per
> cambiare misura bisogna far finire la sessione**. Adesso il registro lo dice, invece di lasciar
> credere a una scalatura che non avviene.
>
> **La lezione, che non riguarda KDE**: una decisione di prodotto presa citando un comportamento non
> misurato è una decisione presa a metà. `LEZIONI.md` §1.11 lo dice per le prove; vale identico per
> le premesse.
| **BlocMaiusc e BlocNum** | ✅ **si legge lo stato vero da KWin**, con `org_kde_kwin_keystate` v5. Costa poco **perché su KDE siamo già client Wayland** per la cattura: basta aggiungere il nome dell'interfaccia allo stesso `.desktop` (`X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1,org_kde_kwin_keystate`) e un ascoltatore. ⚠ Nella valutazione del 7 agosto l'avevo data come «una seconda strada nel codice»: **era sbagliata**, la connessione Wayland c'è comunque |

| | La scelta | Il prezzo di ciascuna via |
|---|---|---|
| ~~**1**~~ | ~~**`--virtual` o `--drm`?**~~ ⛔ **NON è più una scelta: la misura M2 del 7 agosto 2026 l'ha chiusa.** `--drm` da una sessione senza seat esce con stato 1 (`Failed to activate … session`, poi `No suitable DRM devices have been found`), e l'unico modo di avercelo sarebbe occupare `seat0`, cioè la console fisica. **Si va di `--virtual`**, pagando §8.1: risoluzione fissa all'avvio e nessun `stream_virtual_output` prima di KWin 6.8. Non c'è niente da chiedere all'utente | (riquadro in §5.2) |
| **2** | ~~**La risoluzione dinamica su KDE**~~ ✅ **la scelta si è ridotta da sé**: il ridimensionamento arriva in **KWin 6.8** per **negoziazione PipeWire**, cioè con il codice che la fase 6 ha già scritto (§8.2). Quindi si scrive **in quella forma** — che diventa giusta da sé quando l'utente aggiorna — e per le versioni che non ce l'hanno (Trixie compresa) resta la domanda **piccola**: ripiego «chiudi e rifai lo stream», o misura fissa alla connessione? | Il ripiego costa un buco video, le finestre ridisposte e una notifica di sistema a ogni giro; la misura fissa non costa nulla e si vede solo come immagine scalata. **Da decidere guardando**, e non blocca niente |
| **3** | **BlocMaiusc e BlocNum**: aprire **anche** una connessione Wayland (per `org_kde_kwin_keystate`, che richiede il `.desktop`), tenere il conto approssimato, o rinviare? | La prima costa una seconda strada nel codice; la seconda è quel che facevamo su GNOME prima di libei |

---

### 14. Le domande che il codice non chiude — il piano di misure

In ordine di quanto pesano. Sono le `[?]` di questo documento, e sono il contenuto della prima
giornata di banco della fase 11.

> #### Lo stato dopo il banco del 7 agosto 2026
>
> **Cinque chiuse su dodici, e sono le cinque che pesano di più**: le due «decisive» (M1, M2) più
> M3, M5, M6. Nessuna ha smentito il codice; **una ha smentito noi** (R32, il «in software»), e una
> ha aggiunto un requisito che nessuna lettura di codice aveva mostrato (`XDG_MENU_PREFIX`, §3.3-bis).
> Gli script del banco stanno in `reference-kde/banco/` (`misure-kde.sh`, `permesso-kde.sh` …
> `permesso6-kde.sh`) e sul server in `/media/REMOTIX/tmp/banco-compositori/`.

| # | Che cosa | Perché pesa |
|---|---|---|
| ~~**1**~~ | ✅ **CHIUSA: sì, autorizza** — con `NoDisplay=true`, la forma di KRdp. ⛔ **Ma a una condizione che il codice non mostrava: `XDG_MENU_PREFIX=plasma-`**, senza la quale `kbuildsycoca6` non indicizza **niente** e KWin dice `Could not find the desktop file for …`. Cinque varianti del file negate prima di trovarlo. §3.3-bis | è il cancello: se non passa, tutto il resto è teoria (§3) |
| ~~**2**~~ | ⛔ **CHIUSA: no.** `--drm` senza seat esce con 1 (`Failed to activate … session` → `No suitable DRM devices`), e **non** per permessi Unix: nello stesso ambiente `--virtual` apre `renderD129`. Quindi **`--virtual`**, e la decisione 1 di §13.4 non si chiede più all'utente. §5.2 | decide la scelta n.1 di §13.4 (§5.2, §6.3) |
| ~~**3**~~ | ✅ **CHIUSA: GPU.** `renderD129` aperto, `libEGL_mesa` + `libgbm` caricate, `zwp_linux_dmabuf_v1` **v4** annunciato. **R32 va corretta.** ⚠ Due trappole trovate: su Mesa 25 llvmpipe sta dentro `libgallium-*.so` (cercarlo per nome non prova nulla), e `kwin_wayland` è **non dumpable** per l'xattr `security.capability` (il `/proc` va letto con `sudo`). 🟡 Resta **M3d**, il tipo di buffer: negoziato `MemFd/BGRx/LINEAR`, ma per limite del **nostro** cliente. §5.1 | corregge R32 (§5.1, §5.3) |
| ~~**4**~~ | ⛔ **CHIUSA: parte in software.** Con i render node inaccessibili e `KWIN_COMPOSE=O2`: `forced to OpenGL` → `Falling back to defaults` → `QPainter … successfully initialized`, **e KWin parte**. L'interruttore è **inerte**: va cassato dalle ricette e da ogni banco, e l'unico modo di sapere come rende KWin è **chiederglielo** (§5.3-bis). ⚠ Nota: `LIBGL_ALWAYS_SOFTWARE` e le altre variabili di Mesa **non hanno effetto** su KWin. §5.4 | se parte, va cassato dalle nostre ricette, e tutte le misure fatte con quella variabile vanno rilette (§5.4) |
| ~~**5**~~ | ✅ **CHIUSA: sì, senza nulla.** `gdbus … org.kde.KWin.EIS.RemoteDesktop.connectToEIS 7` da una shell SSH qualunque → **`(handle 0, 1)`**: un descrittore e un cookie, **senza sessione, senza portale, senza dialogo e senza `.desktop`**. L'input via libei su KDE è confermato sul campo | è la quarta domanda della fase, e il codice dice sì (§7.1) |
| ~~**6**~~ | ✅ **CHIUSA: sì.** `libeis-dev` è nei `Build-Depends` di `kwin 4:6.3.6-1`, e — prova che non mente — **`eis.so` è dentro il pacchetto `kwin-common`** (`/usr/lib/<triplet>/qt6/plugins/kwin/plugins/eis.so`), libei 1.3.901. ⚠ `kwin-wayland` **non** dipende da `libeis1`: guardare lì avrebbe dato la risposta sbagliata | la premessa dell'input c'è (§7.1) |
| ~~**7**~~ | ✅ **CHIUSA in parte.** Montare un flusso costa **65–67 ms** (tre giri), ed è la componente fissa del buco. Il tempo di *ricreare l'output* non è misurabile su `--virtual`, dove `stream_virtual_output` è rifiutato (`Could not find output`, verificato). §8.1 | decide la scelta n.2 di §13.4 (§8.3) |
| ~~**8**~~ | ✅ **CHIUSA: la cattura è indipendente dal VT.** Il compositore `--virtual` **non apre nessuna tty/console** (verificato su `/proc/<pid>/fd`), la sua sessione ha `VTNr=0` e `Seat=` vuoto; cambiando VT (tty1 → tty2 → tty1 con `VT_ACTIVATE`, perché `chvt` non è installato) **compositore, flusso e protocollo restano tutti vivi**. §4.9 | è la condizione di un servizio non presidiato (§4.9) |
| ~~**9**~~ | ✅ **CHIUSA: sì.** Dopo `org.kde.Shutdown.logout()` tutti i processi Plasma spariscono e il socket Wayland con loro, **ma il bus d'utente risponde ancora sulla stessa connessione** e `systemd --user` è vivo. Il difetto di GNOME non si ripresenta. §6.6 | se sì, un difetto di GNOME non si ripresenta (§6.6) |
| ~~**10**~~ | ✅ **CHIUSA per lettura, e la lettura è conclusiva**: `eiscontext.cpp:272-285` **non inverte** e usa **la stessa formula per i due assi** (`delta = v120 × 15/120`, `v120` grezzo a valle). Nessuna asimmetria di KWin da compensare: l'adattamento è tutto nostro. Resta la verifica a occhio nella fase. §7.2 | §7.2 |
| ~~**11**~~ | 🟡 **CHIUSA per quel che si può**: `0x0`, `-1x-1`, `1x1`, `16384²`, `99999²` **tutte rifiutate** e **KWin sopravvive a tutte**. Ma il rifiuto è per l'assenza di output virtuale, non per validazione: **la validazione resta non misurabile con `--virtual`**. §8.1 | nessuna validazione nel codice (§4.3) |
| ~~**12**~~ | 🟡 **CORRETTA**: il dialogo **non** è il primo rischio. Al primo fallimento di OpenGL plasmashell scrive **`SceneGraphBackend=software` in modo persistente** e si riavvia; il `QMessageBox` è solo al secondo giro. Il rischio vero è **la configurazione permanente lasciata nella casa dell'utente**. Con la GPU: nulla di tutto questo (verificato). §10.4 | dieci secondi, e blocca una sessione (§10.4) |
| **13** *(nuova, dal banco)* | **`InaccessiblePaths=` nell'unità del compositore chiude il cancello della cattura** — 0 righe `KWIN_UTILS` contro 13. Il meccanismo non è dimostrato; la regola operativa sì: **niente namespace di monti nell'unità di KWin**. §3.3-bis | era la via ovvia per scegliere la GPU, ed è una trappola |

**Il metodo, che vale più dell'elenco**: le misure 3 e 4 vanno fatte **prima** delle altre e con le
prove che non dipendono da quel che KWin dichiara. È la lezione 1.8 di `LEZIONI.md`, e su KWin il
codice mostra due punti in cui il ripiego è silenzioso per costruzione.

> #### Lo stato dopo il secondo giorno di banco (8 agosto 2026)
>
> **Dodici su dodici hanno una risposta**, più una tredicesima trovata strada facendo. Sette sono
> state chiuse in questa giornata (M3d, M4, M7, M8, M9, M10, M11, M12), e i risultati che cambiano il
> piano sono tre:
>
> 1. ⭐ **la copia zero è la condizione dei 60 fps a 4K** sulla GPU scelta dall'utente (§5.7);
> 2. ⛔ **`KWIN_COMPOSE=O2` non protegge** (M4), quindi ogni misura va accompagnata dalla stringa del
>    renderer (§5.3-bis);
> 3. ⛔ **il modo ovvio di scegliere la GPU rompe il permesso della cattura** (§5.6, §3.3-bis).
>
> ⚠ **E due prove strutturali che avevamo per buone non valgono**: «render node aperto» non prova la
> GPU (aperto anche in QPainter), e «il flusso è MemFd» non prova che il compositore sia in software
> (dipende da cosa chiede il *cliente*). Le lezioni sono in `LEZIONI.md` §1.9 e §1.11.

> #### ✅ E L'8 AGOSTO 2026 LA VOCE 1 HA MESSO ALLA PROVA IL DOCUMENTO INTERO
>
> *Banco `prove/fase11.sh`, con REMOTIX vero al posto di `nodo-kwin`. Il racconto sta in `PIANO.md`
> fase 11; qui c'è quel che cambia in questo documento.*
>
> **Niente di quel che è scritto qui è stato smentito.** Le quattro cose che il campo ha aggiunto:
>
> | | |
> |---|---|
> | ✅ **il cancello si apre anche per noi** (§3) | `.desktop` con `Exec=` sul binario canonico e `NoDisplay=true`, più `XDG_MENU_PREFIX=plasma-` nell'ambiente di KWin: il global compare, nessun dialogo. Con `--installa-desktop` il file lo scrive REMOTIX stesso, da `/proc/self/exe` |
> | ✅ **la fence si aspetta, e basta** (§4.8) | **2 400 buffer su 2 400** col disegno in corso — la misura dell'8 agosto confermata su un campione otto volte più grande — e **zero attese scadute** con un tetto di 50 ms. Il difetto di R29 non si ripresenta: i fotogrammi sono interi |
> | ✅ **il modificatore che si ottiene è `0x0`, lineare** (§11.2) | è quello che il codificatore vuole, e per averlo è bastato metterlo **primo** nell'enum della proposta. `INVALID` resta come seconda scelta |
> | ✅ **il ritmo regge, sulla catena vera** (§5.7) | **58,1 fps a 1080p e 58,4 a 4K** sulla Intel, contro i 59,2 e 59,0 misurati col solo `misura-cattura`. La differenza è la conversione sulla scheda, che il banco non faceva |
>
> ⛔ **E una trappola nuova, che non è di KDE ma dei banchi che rifanno la sessione**: uccidere
> `kwin_wayland` mette in coda su systemd un lavoro di *stop* per la sua unità, e un
> `StartUnit("plasma-workspace-wayland.target")` che arrivi prima che quel lavoro sia finito viene
> **rifiutato in blocco** — *«Transaction … is destructive»* — con `startplasma-wayland` che dice
> soltanto «Could not start Plasma session». Chi rifà la sessione due volte di fila fallisce la
> seconda: si ferma il target e si **aspetta** che l'unità sia `inactive`.

---

### 14-bis. ✅ Lo studio è chiuso — quel che si è imparato SCRIVENDO, non leggendo

*8 agosto 2026, a fase 11 conclusa per KDE.*

Le dodici misure sono chiuse (§14), e la loro resa è alta: **undici domande su undici avevano una
risposta prima di scrivere una riga**. Ma quattro difetti sono comparsi solo mettendo il codice
davanti a un utente, e vale la pena elencarli perché **sono il tipo di cosa che rileggere il codice
non trova** — e quindi si ripresenterà su XFCE:

| Trovato da | Che cosa | Dove sta ora |
|---|---|---|
| **l'utente, al primo sguardo** | due puntatori del mouse | riquadro in testa: il cursore è dentro l'immagine, e la cura è un tema trasparente |
| **l'utente** | il cursore del volume non governava niente | §10.5 — e il difetto era **anche su GNOME**, da sempre |
| **l'utente** | «Blocca» e «Cambia utente» inerti nel menu | §10.6 — KIOSK, tre azioni e non due |
| **il banco, ma solo dopo averlo rinforzato** | «una via audio nuova parte al massimo» non funziona | `REFERENCE.md` §7.5, **aperto** |

⭐ **Tre su quattro erano nel percorso condiviso**, cioè erano difetti di GNOME che nessuno aveva
visto in dieci fasi. Aprire un secondo compositore non ha solo aggiunto un desktop: ha fatto da
banco al primo.

⛔ **E la lezione di metodo, che è la più cara**: il difetto del volume è rimasto invisibile perché
la prova era stata fatta su **un sink equivalente creato con `pactl`** invece che sul nostro — e
`pipewire-pulse` mette da sé la proprietà che a noi mancava. Un banco che prova *qualcosa di simile*
assolve il codice (`LEZIONI.md` §1.11 e §5).

---

### 15. Le correzioni da fare ai documenti

Come prescrive §7.0 di `SPECIFICA.md`, quando una misura contraddice un documento lo si aggiorna
**nello stesso momento**. Le prime tre righe nascevano da una **lettura di codice** e furono annotate
come tensioni da sciogliere; **il banco del 7 agosto 2026 le ha sciolte**, e ora sono smentite vere:

| Documento | Che cosa dice oggi | Che cosa dice il banco |
|---|---|---|
| `SPECIFICA.md` §3.8 | «KWin: cattura via **portale**, input `kde-fake-input`» | cattura via **protocollo Wayland diretto**, input via **libei/EIS** (§13.2 n.1) — **correzione applicata**, con la data. E ora **misurata**: `connectToEIS(7)` → `(handle 0, 1)`, e il `.desktop` apre il global |
| `REFERENCE.md` **R32** | «KWin senza monitor disegna in software: zero nodi DRM, nessuna libreria GL» | ⛔ **smentita, con tre prove** [M]: `renderD129` aperto, `libEGL_mesa`+`libgbm` caricate, `zwp_linux_dmabuf_v1` v4 annunciato. **Va corretta**: il «60 fps a 4K» resta, l'etichetta «in software» no (§5.1) |
| `LEZIONI.md` §3, riga 4 e riga «KWin tiene la cattura dietro un controllo di permessi» | «NO, in software»; «serve il permesso per la via che KDE prevede» | la prima come sopra; la seconda ha ora **una risposta misurata**: il `.desktop` **più `XDG_MENU_PREFIX=plasma-`** (§3.3-bis) |
| `PIANO.md` fase 11 | le quattro domande d'apertura | **quattro su quattro hanno risposta di banco**, e la decisione «`--virtual` o `--drm`» è stata chiusa da una misura invece che dall'utente (§5.2) |

> ✅ **Tutte applicate**, e l'ultima l'8 agosto 2026 con la chiusura della fase. Due correzioni si
> sono aggiunte strada facendo, e vanno lette insieme alle prime perché nascono dallo stesso errore —
> **aver creduto a una lettura di codice senza misurarla**:
>
> | Documento | Che cosa diceva | Che cosa dice il banco |
> |---|---|---|
> | `LEZIONI.md` §3, domanda 5 | «KWin: sì, `stream_virtual_output`» | ⛔ **no**: col backend `--virtual` risponde `Could not find output`, per ogni misura. **Corretta** |
> | questo documento, in testa | «il cursore è fuori dal percorso del codificatore» | ⛔ **è dentro l'immagine**, e l'ha visto l'utente prima di noi. **Corretta**, con la cura |

---

### 16. Che cosa non c'è, per non cercarlo

Tutte dichiarazioni negative verificate per grep su tutti gli otto repository [✗]:

| Funzionalità | Stato in KDE 6.3.6 |
|---|---|
| `zwlr_screencopy_manager_v1`, `ext_image_copy_capture_v1` | **assenti** in KWin |
| Un'interfaccia D-Bus di screencast (l'analogo di `org.gnome.Mutter.ScreenCast`) | **assente**: la cattura passa dal protocollo Wayland, punto |
| `org.kde.KWin.VirtualOutputs` | **assente** (c'era in KWin 5) |
| Una richiesta di **resize** nel protocollo screencast | **proposta e respinta** (`plasma-wayland-protocols!138`), perché la strada scelta è la **negoziazione PipeWire**: unita in `kwin!7932`, milestone **6.8** — non c'è in Trixie, ma arriva (§8.2) |
| `wlr-output-management`, `ext-data-control-v1`, `kde_primary_output_v1` (global) | **assenti** |
| `eis_device_keyboard_send_xkb_modifiers` in KWin | **assente**: nessun `KEYBOARD_MODIFIERS` |
| `eis_region_set_mapping_id` in KWin | **assente**: regioni senza chiave |
| `keyboard_keysym` di `fake_input` v6 | **non implementato** (KWin ferma a v5) |
| Un controllo di permesso su `org.kde.KWin.EIS.RemoteDesktop` | **assente** |
| `EnableClipboard`/`DisableClipboard` | **assenti**: la clipboard non appartiene a una sessione |
| Un `Logout(2)` forzato | **assente**: la forzatura è `StopUnit` |
| `RegisterClient`/`EndSession` su D-Bus | **assenti**: l'equivalente è XSMP su ICE |
| `ConditionEnvironment=` nelle unità di KDE | **assente** |
| Un renderer **Vulkan** in KWin | **assente** |
| `libseat`/`seatd` | **assenti**: solo logind, ConsoleKit, Noop |
| Controllo del bitrate H.264 in kpipewire | **assente**, come in `gnome-remote-desktop` |
| ~~Un backend RDP in KDE~~ | ⛔ **sbagliato**: c'è **`KRdp`** (§12.0), che è il riferimento della fase |
| Un `disable-animations` per sessione di cattura | **assente**: si spengono a sessione |


<a id="xfce"></a>

## XFCE, labwc e wlroots — studio del codice, per la fase 11

*Scritto l'8 agosto 2026, aprendo il terzo desktop, con dieci ricerche parallele sui sorgenti clonati
alle versioni di Debian Trixie. È il sesto studio del progetto, dopo `protocollo-rdp.md`,
§gnome-remote-desktop, `client-android.md`, `xrdp-funzionalita.md` e §kde.*

> **Come si legge questo documento.** Ogni affermazione porta una marca, e la marca conta più della
> frase:
>
> | | |
> |---|---|
> | **[R]** | letto nel codice, con `file:riga`. **Non è una misura**: dice che cosa il programma *può* fare, non che cosa *fa* sulla nostra macchina |
> | **[M]** | misurato. Dove c'è, è detto su quale macchina e quando |
> | **[?]** | deduzione o ipotesi. Da trattare come una domanda aperta, non come un fatto |
> | **[✗]** | verificata **assente**, dicendo come è stata cercata e con quale controllo positivo |
>
> Il dettaglio con i `file:riga` sta nei **dieci rapporti** in `reference-xfce/rapporti/`
> (~9 000 righe). Qui c'è quel che serve per decidere e per scrivere.

---

### 1. In due minuti

**XFCE non ha un compositore proprio.** Su Wayland avvia **labwc**, e labwc è **wlroots** — la terza e
ultima famiglia del panorama. Serviti GNOME (Mutter) e KDE (KWin), questa chiude il giro.

**La differenza che cambia la forma del codice**, e che era già scritta in `LEZIONI.md` §3: wlroots
**fa tirare** i fotogrammi invece di spingerli. Non c'è PipeWire in mezzo, non c'è D-Bus: c'è un
protocollo Wayland, `zwlr_screencopy_manager_v1`, e per ogni fotogramma si fa
`capture_output → frame → copy → ready`. Il flusso non si «monta»: si chiede, uno per volta.

**Le sei risposte che contano, tutte migliori che su KDE:**

| | |
|---|---|
| **Il permesso della cattura** | ✅ **non esiste**. [M, portatile, 8 ago] Un client nudo (`env -i`, sole `XDG_RUNTIME_DIR` e `WAYLAND_DISPLAY`) vede 45 global e cattura al primo colpo. Nessun `.desktop`, nessun dialogo, nessun portale. L'unico cancello è l'UID: `/run/user/1000` è `drwx------` |
| **Il seat** | ✅ **non serve**. Con `WLR_BACKENDS=headless` non si crea mai una `wlr_session` e libseat non viene sfiorato: il muro su cui `kwin_wayland --drm` moriva **qui non esiste** |
| **La GPU** | ✅ **una variabile**: `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128`. Niente regola udev, niente permessi di nodo negati a tutta la sessione dell'utente |
| **Il ridimensionamento a caldo** | ✅ **sì**: `set_custom_mode` su un output headless non ha alcun tetto. Il ripiego «misura fissa alla connessione» che KDE ci ha imposto **non serve** |
| **La cadenza** | ⭐ **è un parametro nostro**: su headless il refresh dell'output *è* il periodo del timer dei fotogrammi |
| **Gli appunti** | ✅ **`appunti_wlr.c` funziona così com'è**: è scritto contro un protocollo di wlroots, e qui siamo in casa sua |

**E le cinque che costano:**

| | |
|---|---|
| ⛔ **Nessun protocollo crea un output** | `wlr-virtual-output` **non esiste** [✗]. Un output headless nasce **1280×720 cablati**, e labwc non ha né IPC né `<output>` in configurazione: la misura si dà **solo** col protocollo, **dopo** l'avvio |
| ⛔ **Il cursore è sempre dentro l'immagine** | il backend headless non ha `set_cursor`, quindi non esiste cursore hardware; e `overlay_cursor` **non lo toglie** — lo *forza* software. È la stessa forma di `KWIN_COMPOSE=O2`: una leva che sembra esserci e non fa niente |
| ⛔ **libei non esiste su wlroots** | [✗] cercato in wlroots, labwc, sway, wayfire, weston, xdpw, wayvnc: zero. `input.c` **diventa un client Wayland**: si riusano le tabelle, non il trasporto |
| ⛔ **`xfce4-power-manager` ci spegne l'output** | parla Wayland nativo e dopo **10 minuti** su rete elettrica manda `zwlr_output_power_v1(OFF)`; output spento ⇒ nessun fotogramma ⇒ `failed` sulla cattura |
| ⛔ **Al logout XFCE può ammazzare la nostra sessione** | se la riga del compositore non contiene *sia* `labwc` *sia* `--session`, `xfce4-session` esegue `loginctl terminate-session ''` |

**E il passo zero — *«chi, al mondo, fa questa cosa su questo desktop?»* — ha una risposta che va
detta per intera**: **nessuno fa RDP su wlroots senza monitor**. Un solo server RDP al mondo parla
con wlroots (Rust, licenza BSL) e **dichiara di richiedere un desktop già acceso**; `xrdp` non ha
Wayland dal 2017; `freerdp-shadow` non ha un backend Wayland e i manutentori hanno scritto che è
improbabile che arrivi; e chi passa dal portale su wlroots è **video-only**, perché
`xdg-desktop-portal-wlr` non implementa `RemoteDesktop`.

> ⭐ **Ma un precedente c'è, ed è dalla nostra parte.** wlroots un backend RDP **ce l'aveva**, ed è
> stato rimosso nella 0.10 *«interamente in favore di wayvnc»* dopo cinque issue di crash. La
> comunità ha già deliberato che il posto giusto per questa cosa è **un client esterno del
> compositore** — cioè esattamente dove siamo. E labwc **cita wayvnc alla lettera nella propria
> documentazione**, prevedendo l'output virtuale ridimensionabile dal client remoto.

---

### 2. La mappa: dove sta ciascuna cosa

| Che cosa | Dove | Versione Trixie |
|---|---|---|
| il compositore | `reference-xfce/labwc/` | **0.8.3** |
| la libreria del compositore | `reference-xfce/wlroots/` | **0.18.2** |
| i protocolli di wlroots | `reference-xfce/wlr-protocols/` | (screencopy, data-control, virtual-pointer, output-management…) |
| i protocolli standard | `reference-xfce/wayland-protocols/` | **1.38** |
| la sessione | `reference-xfce/xfce4-session/` | **4.20.2** |
| pannello, scrivania, impostazioni | `xfce4-panel/` 4.20.4, `xfdesktop/` 4.20.1, `xfce4-settings/` 4.20.1 | |
| l'astrazione X11/Wayland di XFCE | `libxfce4windowing/` | **4.20.2** |
| le librerie comuni | `libxfce4ui/` 4.20.1, `libxfce4util/` 4.20.1, `xfconf/` 4.20.0, `garcon/` 4.20.0 | |
| energia e blocco | `xfce4-power-manager/` 4.20.0, `xfce4-screensaver/` 4.18.4 | |
| **chi lo fa già** | `wayvnc/` 0.9.1 + `neatvnc/` 0.9.1, `weston/` 14.0.2 (backend RDP), `xdg-desktop-portal-wlr/` 0.7.1 | |
| i termini di paragone | `sway/` 1.10.1, `wayfire/` 0.9.0 | |

⚠ **Le versioni installate sul server coincidono esattamente con quelle clonate** [M, 8 ago]: labwc
0.8.3-1, xfce4-session 4.20.2-2, xfce4-panel 4.20.4-1, xfdesktop4 4.20.1-1, xfce4-settings 4.20.1-1,
sway 1.10.1-2, weston 14.0.2-1. Lo studio e il banco parlano della stessa macchina.

⚠ **Wayfire non è nella stessa famiglia di codice**: `meson.build:45,49` chiede wlroots
`>=0.17.0, <0.18.0` e lo vendorizza. Tutto quel che segue vale per **labwc** (il nostro bersaglio) e
per **sway** (il termine di paragone). Wayfire va riletto sulla 0.17 se e quando servirà.

---

### 3. ✅ Il cancello che non c'è

Su KWin questa sezione è la più lunga del documento e ha richiesto cinque prove di banco. Qui si
chiude in tre righe, ed è **misurata** [M, portatile con labwc 0.8.3, 8 agosto 2026] prima ancora che
dedotta.

| | |
|---|---|
| **Che cosa vede un client nudo** | 45 global, fra cui `zwlr_screencopy_manager_v1` **v3**, `zwlr_virtual_pointer_manager_v1` **v2**, `zwp_virtual_keyboard_manager_v1` **v1**, `zwlr_data_control_manager_v1` **v2**, `zwlr_layer_shell_v1` v4 |
| **Che cosa serve nell'ambiente** | `XDG_RUNTIME_DIR` e `WAYLAND_DISPLAY`. Nient'altro: la cattura è riuscita al primo colpo (`buffer(1280×720, stride 5120)` → `copy()` → `ready`, checksum non nullo) |
| **Il codice che lo spiega** | `labwc/src/server.c:344` — `return true` per ogni client **senza** security context; `wlroots/types/wlr_security_context_v1.c:435-437` — chi entra dal socket normale non ha contesto |

**[✗] wlroots 0.18.2 non filtra nulla**: zero chiamate a `wl_display_set_global_filter` in tutto
l'albero. Il filtro che labwc e sway hanno scatta **solo** sui client entrati da un `listen_fd`
altrui, cioè Flatpak e bwrap — e noi non ci saremo mai. Wayfire non filtra affatto.

⛔ **E non esiste il verso opposto**: `rc.xml` di labwc **non ha alcun interruttore di protocollo**
[✗], su nessuno dei tre compositori. Un amministratore che volesse *chiudere* la cattura non ha una
leva di configurazione — informazione che ci riguarda perché significa che **nessuno può chiuderci la
porta per errore**.

#### 3.1 ⚠ Dove sta il rischio, invece: la diagnosi

Il permesso non è il pericolo; il pericolo è **non vedere perché una cosa fallisce**.

| | |
|---|---|
| ⛔ **labwc non logga** | né la connessione né il `bind`, nemmeno con `-d`. Su richiesta illegale scrive solo `error in client communication (pid N)`, a livello **INFO** (invisibile senza `-V`): il PID, non l'interfaccia né il codice |
| ⛔ **`WLR_DEBUG` non esiste** [✗] | `wlroots/util/log.c` non ha un solo `getenv`. Il livello lo decide il compositore, con `-d`/`-V` sulla riga di comando |
| ✅ **La diagnosi si fa dal lato client, ed è ottima** | libwayland stampa da sé su stderr `zwlr_screencopy_frame_v1#3: error 1: invalid buffer dimensions`, e `wl_display_get_protocol_error()` restituisce **interfaccia e codice**. `WAYLAND_DEBUG=1` dà la traccia completa |

⭐ **Da cui una regola per il nostro codice**: dopo *ogni* fallimento, chiamare
`wl_display_get_protocol_error()` e scriverne l'esito. È l'equivalente della lezione §1.10 — *prima di
provare varianti, farsi dire la causa* — con la differenza che qui il componente che nega non parla, e
il nostro cliente sì.

#### 3.2 ⛔ Un errore di protocollo uccide la connessione

Non è un fotogramma perso: è la connessione. [M] `roundtrip = -1`, `EPROTO`, nessuna ripresa — va
rifatto tutto da `wl_display_connect`.

**Le tre regole che ne discendono, e che valgono per tutto il codice nuovo:**

1. **Formato, dimensioni e stride si copiano *esattamente* dall'evento `buffer`.** Nessun allineamento
   nostro (`wlroots/types/wlr_screencopy_v1.c:384-432`);
2. **un solo `copy()` per frame**, poi un `capture_output()` nuovo (`:391`);
3. **la keymap prima del primo tasto**, o `no_keymap` (`wlroots/types/wlr_virtual_keyboard_v1.c:84,107`).

---

### 4. La cattura: `zwlr_screencopy_manager_v1`

*Dettaglio: `reference-xfce/rapporti/01-cattura-screencopy.md`.*

#### 4.1 ✅ Fotogrammi interi, sempre — e il difetto di GNOME non si ripresenta

`frame_shm_copy`/`frame_dma_copy` usano `frame->box`, cioè **l'output intero**, e non consultano mai
il danno (`wlr_screencopy_v1.c:214-219`, `:255-268`). Il buffer sorgente è a sua volta completo grazie
al *buffer age* del damage ring (`types/scene/wlr_scene.c:1910-1911`).

⭐ **Cioè la trappola che su GNOME tiene spenta la copia zero — il buffer che è un «diff» su quattro
buffer riciclati, R29 — qui non esiste.** Un pool di buffer riusati va bene senza precauzioni, e la
superficie di accumulo non serve.

#### 4.2 ⛔ Il modello a tiro, e le sue due trappole

| | |
|---|---|
| **`copy_with_damage` a schermo fermo** | ⛔ **`ready` non arriva mai**, e non c'è alcun timeout: il listener resta agganciato (`:297-303`). Serve **un timer nostro** che, scaduto, distrugga il frame e riapra con `copy` semplice |
| **`copy` semplice** | ⛔ chiama `wlr_output_update_needs_frame()` (`:448`), cioè **forza il rendering** anche a schermo immobile. Un ciclo ingenuo a 30 fps fa rendere al compositore 30 fotogrammi al secondo di nulla |

⭐ **La forma giusta la mostra wayvnc**, ed è la correzione strutturale al problema dei 18 fps del
7 agosto: `copy_with_damage` di regola, `copy` intero solo quando serve un fotogramma subito (primo
client, cambio output, cambio misura, riaccensione) — e **la cadenza sottrae la latenza misurata del
compositore**: `time_left = 1/rate − dt − delay`, con `delay` misurato a ogni `ready` e filtrato
passa-basso a 0,5 s (`wayvnc/src/screencopy.c:308`, `:214-215`).

#### 4.3 ⭐ Il libro doppio del danno — obbligatorio, non un'ottimizzazione

Ogni buffer porta **due** danni: `frame_damage` (che va al codificatore) e `buffer_damage` (che va al
compositore). Quando un fotogramma è pronto con danno D, D si somma al `buffer_damage` di **tutti** i
buffer del pool (`wayvnc/src/buffer.c:693-704`).

⛔ **Senza, si mandano fotogrammi con pezzi vecchi, e nessuna misura di fotogrammi al secondo lo
rivela** — è il difetto di R29 in forma generale, e la ragione per cui va scritto ora e non poi.

⚠ E il danno di wlroots è **un solo rettangolo** (gli extents, con un `// TODO` esplicito a
`:168-178`), in coordinate pixel dell'output, **non** traslato per `capture_output_region`. Va
**ritagliato** al rettangolo del buffer prima di fidarsene, come fa wayvnc (`main.c:1145-1146`).

#### 4.4 La copia zero: possibile, e in una forma migliore di quella di Mutter

| Strada | Che cosa consegna | Verdetto |
|---|---|---|
| **`copy` su buffer DMA-BUF** | un **blit GPU** dentro un buffer **di proprietà del client** (`wlr_renderer_begin_buffer_pass` + `add_texture` + `submit`, `wlr_screencopy_v1.c:249-270`) | ✅ **la nostra strada**: niente lettura CPU, buffer stabile, formato per VA-API |
| `copy` su buffer shm | `glFinish()` + `glReadPixels` (`render/gles2/texture.c:206,218`) | ⛔ **blocca il ciclo principale del compositore** |
| `zwlr_export_dmabuf_v1` | il buffer *del compositore*, ma con flag **TRANSIENT** sempre alzato (`wlr_export_dmabuf_v1.c:75`) | ⛔ è la trappola di GNOME in forma pura. Da scartare |

⚠ **Non è copia zero in senso stretto** — c'è un blit — ma è **una copia sola, sulla scheda**, e il
buffer è nostro: è precisamente la forma che le fasi 8 e 9 hanno imparato a consumare.

⚠ **La sincronizzazione**: con GLES2 il ramo DMA-BUF fa solo `glFlush()` (`render/gles2/pass.c:39`),
**nessuna fence esplicita**: si dipende dal sync implicito. Il renderer Vulkan invece importa
correttamente una sync file nel DMA-BUF (`render/vulkan/renderer.c:1025-1029`) — ma in `auto` Vulkan
**non è mai tentato** in 0.18.2 (`wlr_renderer.c:244`). È lo stesso punto che su Mutter è costato la
fase 9, e va **misurato** prima di crederci.

⚠ **I modifier non vengono dall'evento `linux_dmabuf`**, che porta solo format/width/height
(xml:214-223) e non è controllato da wlroots: vanno presi dal feedback di `zwp_linux_dmabuf_v1`, come
fanno wayvnc e il portale.

#### 4.5 Formati e profondità

Il formato shm lo sceglie il renderer via `GL_IMPLEMENTATION_COLOR_READ_FORMAT` e **non è
richiedibile**; il campo va trattato come **fourcc**, non come enum (`render/pixel_format.c:215-224`).
`BGR888` a 24 bit esiste in tabella ma **[?]** non uscirà mai dalla query GL: si riceve 32 bit e si
converte a valle — come su Mutter, dove R32 aveva già stabilito che un percorso a 24 bit impacchettati
non esiste.

#### 4.6 Il successore, e perché il codice va scritto con due implementazioni

**[✗] `ext-image-copy-capture-v1` non esiste** in wlroots 0.18.2, labwc 0.8.3, wayfire 0.9.0 né sway
1.10.1 (grep a zero su tutti e quattro, con controllo positivo su `screencopy`). Su Trixie **l'unica
via è `zwlr_screencopy`**.

Ma **wayvnc 0.9.1 lo parla già**, e sceglie a runtime in dodici righe
(`wayvnc/src/screencopy-interface.c:29-45`), con le capacità diverse in una maschera di bit e **un
solo punto** in cui il codice si dirama. ⭐ **È la forma da copiare**, perché il protocollo nuovo
porta due cose che ci servono: i **modifier**, e una **sessione cursore** con posizione e hotspot —
cioè la cura definitiva al doppio puntatore.

⚠ E porta anche un cambio di modello da sapere adesso: **il nuovo protocollo è a diff** («at least
the union of the region passed by the client and the region advertised by `damage`»), con danno pieno
solo al primo fotogramma. Chi lo scriverà senza sapere questo ripaga R29 una terza volta.

---

### 5. Senza monitor: headless, GPU, cadenza

*Dettaglio: `reference-xfce/rapporti/03-output-headless-gpu.md`.*

#### 5.1 ✅ Nessun seat, nessun libseat

`grep session|libseat|drm backend/headless/` → **vuoto** [✗]. Con `WLR_BACKENDS=headless` non si crea
mai una `wlr_session` (`backend/backend.c:308-316`). Il muro su cui `kwin_wayland --drm` usciva con
stato 1 da una shell SSH **qui non esiste**, e non serve alcun `Activate()` di logind.

#### 5.2 ⭐ La GPU si sceglie con una variabile — e il ripiego è la trappola

| | |
|---|---|
| **Come si sceglie** | `WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128` (`render/wlr_renderer.c:147-158`, accetta solo `renderD*`) |
| **Il default** | il **primo** render node di `drmGetDevices2()`, con `break` immediato |
| ⛔ **Il ripiego** | **non esiste**: se l'`open` fallisce, wlroots **non prova l'altra scheda** — cade in **pixman**, cioè in software, senza errore |

⭐ **Da cui: la regola udev di KDE non serve, e negare un nodo sarebbe controproducente.** Su KWin
negare il nodo era l'unico modo di scegliere la scheda, e il prezzo era negarlo a tutta la sessione
dell'utente. Qui basta una variabile d'ambiente.

⚠ **E la lezione §1.11 vale identica**: «render node aperto» non prova la GPU nemmeno qui, e
«DMA-BUF offerto» prova **l'allocatore**, non il disegno. **[✗] Non esiste API né IPC per chiedere il
renderer** in 0.18.2 (`struct wlr_renderer` non ha `name`): niente di equivalente a
`supportInformation` di KWin. Restano due strade, entrambe da usare: **`-V` all'avvio del
compositore** (labwc e sway partono a `WLR_ERROR` e non stampano `GL renderer:` senza), e il
**controllo positivo obbligatorio** — rifare la misura con `WLR_RENDERER=pixman` e vedere che
**cambia**.

Con headless e default: **GLES2 + allocatore GBM** (`allocator.c:101-103`), quindi la copia zero è
disponibile. Con pixman l'allocatore è shm e screencopy **non offre affatto** il formato DMA-BUF
(`wlr_screencopy_v1.c:574-577`) — il che, notato di passaggio, è una prova *negativa* utile: se il
DMA-BUF non viene offerto, siamo in software.

#### 5.3 ⭐ La cadenza è un parametro nostro

Su un output headless `frame_delay = 1 000 000 / refresh_mHz` ms (`backend/headless/output.c:25-32`):
**il terzo argomento di `set_custom_mode` diventa il periodo del timer dei fotogrammi.**

| refresh dichiarato | periodo | tetto |
|---|---|---|
| 60 Hz | 16 ms | **62,5 fps** |
| 30 Hz | 33 ms | 30 fps |

Nessun altro compositore ci ha mai dato questa leva: su Mutter la cadenza si dichiarava a PipeWire e
se ne ottenevano sei decimi; su KWin il tetto era `maxFramerate` e lo onorava il server. ⚠ wayvnc lo
lascia a 0 con un TODO, quindi qui **non abbiamo un precedente da copiare**.

⛔ **E i fotogrammi si tirano davvero**: niente danno ⇒ niente commit
(`types/scene/wlr_scene.c:1705-1709`) ⇒ il timer non si riarma (`headless/output.c:76`). A riaccendere
è la cattura stessa, con `wlr_output_update_needs_frame()` dentro `copy`.

#### 5.4 ⛔ Due silenzi da conoscere prima di scrivere

1. **Mai toccare l'adaptive sync**: `ADAPTIVE_SYNC_ENABLED` è **fuori** dalla maschera headless
   (`headless/output.c:10-14`) e fa fallire **l'intero** commit con `Unsupported output state fields:
   0x40` — che sembra un rifiuto della misura. `false` invece è un no-op silenzioso;
2. **Chiedere la misura che l'output ha già** non produce un modeset: `output_compare_state` toglie il
   campo `MODE` e il commit riesce **senza fare niente** (labwc lo aggira alzando la larghezza di 1,
   `labwc/src/output.c:1084-1104`).

E una terza, sul protocollo di configurazione: **serial vecchio ⇒ `cancelled`, non `failed`**
(`wlr_output_management_v1.c:446-455`). Chi ascolta solo `succeeded`/`failed` resta appeso per sempre.

---

### 6. ✅ Il ridimensionamento a caldo: si può — e il ripiego di KDE non serve

*È la domanda 13 di `LEZIONI.md` §3, quella che su KWin ha deciso metà del piano.*

`zwlr_output_configuration_head_v1::set_custom_mode` ridimensiona un output headless a caldo.
**L'unica validazione in tutto il percorso** è `width<=0 || height<=0 || refresh<0`
(`wlr_output_management_v1.c:216-241`) più `pending_width==0` (`types/output/output.c:593-596`).
**[✗] Nessun tetto**, cercato con grep su wlroots e sui tre compositori.

**Il precedente esiste e non è nostro**: wayvnc ridimensiona l'output alla risoluzione del client
(`wayvnc/src/main.c:802-826` → `output-management.c:230-287`), e da lì si copia anche la disciplina —
**enumerare tutte le head** con enable/disable, o wayfire rifiuta.

#### 6.1 ⛔ Ma l'output NON si crea, e non si distrugge

| | |
|---|---|
| **[✗] `wlr-virtual-output` non esiste** | dieci protocolli in `wlr-protocols/unstable/`, nessuno crea output. `wlr-output-management` li *configura*: *«Heads cannot be created nor destroyed by the client»* |
| **[✗] Nessuna variabile dà la misura iniziale** | ⚠ *precisato l'8 agosto, studiando LXQt*: le misure cablate sono **due, diverse secondo la via** — `WLR_HEADLESS_OUTPUTS` crea output **1280×720** (`wlroots/backend/backend.c:237`), mentre gli output virtuali **di labwc** nascono **1920×1080** (`labwc/src/output-virtual.c:52-53`). Nessuna delle due porta la misura: `WLR_HEADLESS_OUTPUTS` porta solo il **numero** |
| **[✗] labwc non ha IPC** | `grep -rli ipc labwc/src` → nulla, e `rc.xml` non ha alcun `<output>`. `VirtualOutputAdd` accetta il **nome** ma non la misura ed è raggiungibile **solo da keybind**. ⚠ Esiste però **`LABWC_FALLBACK_OUTPUT`** (`output-virtual.c:109-135`): a layout **vuoto** labwc crea da sé un output virtuale col nome dato — ed è il meccanismo che upstream documenta perché un nome `NOOP-…` faccia riconoscere a wayvnc un output ridimensionabile. Scatta **solo** a layout vuoto, quindi vuole `WLR_HEADLESS_OUTPUTS=0` [?, da provare] |

⭐ **Da cui la forma obbligata**: si avvia il compositore headless, ci si collega, e **si ridimensiona
l'output esistente**. Non «si crea l'output della misura chiesta», che è quel che facevamo su KWin con
`--virtual --width/--height`.

⛔ **E distruggere e ricreare è vietato da tre parti diverse**, tutte in XFCE:

| | |
|---|---|
| `xfsettingsd` | se compare un output **nuovo** lo **disabilita** e lancia `xfce4-display-settings` (`displays-wayland.c:524-528`, `:541-546`). ⚠ E attenzione al verso: `action <= SHOW_DIALOG` significa che **anche `/Notify=0` disabilita** — servono 2 o 3 |
| `xfce4-panel` | esce senza far niente se `n_monitors == 0` (`panel-window.c:2640-2642`, commento «temporary state on Wayland») |
| `xfdesktop` | perde le impostazioni dello sfondo se cambia il nome del connector: **la chiave xfconf *è* il connector** (`xfdesktop-backdrop-manager.c:169`) |

⚠ E un dettaglio da tenere per il banco: il pannello **non usa** l'API monitor di
`libxfce4windowing` [✗], ascolta `GdkScreen::monitors-changed`. Quel che dobbiamo far scattare è GDK.

---

### 7. L'input: `input.c` diventa un client Wayland

*Dettaglio: `reference-xfce/rapporti/04-input.md`.*

**[✗] libei non esiste su wlroots** — cercato `libei|EIS|ei_device|ei_seat|ei_new` in wlroots, labwc,
sway, wayfire, weston, xdg-desktop-portal-wlr e wayvnc: zero, con controllo positivo su
`virtual_keyboard` che dà 67/15/16/10 righe. E **[✗] `xdg-desktop-portal-wlr` non ha `RemoteDesktop`**
(`wlr.portal:3`: solo Screenshot e ScreenCast).

Quindi: `zwp_virtual_keyboard_manager_v1` **v1** e `zwlr_virtual_pointer_manager_v1` **v2**, senza
alcun permesso (wlroots non filtra; labwc e sway filtrano solo i client in sandbox).

#### 7.1 Che cosa si riusa, e che cosa si riscrive

| | |
|---|---|
| ✅ **si riusa** | le tabelle scancode set 1 → VK → evdev, la mappa dei pulsanti, la macchina a stati del tasto Pausa, la logica di sessione. L'offset evdev↔X11 è **8** in entrambe le direzioni |
| ⛔ **si riscrive** | il trasporto (D-Bus/EIS → `wl_registry`) e **tutta la gestione dei modificatori**, che con libei non esisteva |

**[?] Circa metà del file.** ⚠ E una decisione da prendere **prima** di scrivere: se anche la cattura
è un protocollo Wayland, **una sola connessione `wl_display` serve entrambi**.

#### 7.2 ⛔ Le cinque trappole silenziose

| # | | |
|---|---|---|
| 1 | **La rotella vuole scatti da ±1**, non ±120 | `axis_discrete(t, axis, value, discrete)` con `discrete` **in scatti interi**; wlroots moltiplica **lui** per 120 (`wlr_virtual_pointer_v1.c:183-184`). La convenzione di KWin qui darebbe **120 scatti** |
| 2 | **`value` non deve mai essere 0** | con `value == 0` parte un `axis_stop` e lo scatto sparisce (`wlr_seat_pointer.c:369-391`). wayvnc usa **15.0**, «valore magico misurato con `wev`» |
| 3 | **Senza `frame` non arriva niente** | gli assi restano nel buffer (`wlr_virtual_pointer_v1.c:109-122`), e `frame` serve a **tutti** gli eventi, non solo alla rotella |
| 4 | **I modificatori li mandiamo noi, sempre** | wlroots costruisce l'evento con `update_state = false` (`:92`) e non aggiorna `xkb_state`: **senza `modifiers`, Shift+A dà `a`**. Serve un `xkb_state` nostro |
| 5 | **`wlr_pointer_finish()` non rilascia i pulsanti** (`types/wlr_pointer.c:38-42`) | alla disconnessione dobbiamo mandare noi `button(release)` + `frame` prima di `destroy`, o **il desktop resta col tasto sinistro premuto**. La tastiera invece li rilascia da sola |

⚠ **Il verso della rotella**: verticale **invertito** rispetto a Wayland, orizzontale no — e **nessuno
lo corregge per noi**, perché su un device virtuale labwc salta libinput (`scroll_factor = 1.0`,
niente natural scrolling né accelerazione). Su sway e wayfire invece `scroll_factor` **si applica
anche a noi**. Weston conferma la conversione riga per riga, ed è il pezzo più prezioso del suo
backend RDP: valore negli 8 bit bassi dei flag, negativo = `(0xff - v) * -1`, **due accumulatori per
asse** (`≥ 12` passo fluido, `/120` scatto discreto, con `%=` che conserva il resto).

#### 7.3 ⭐ I lucchetti si leggono — ma solo perché il compositore è labwc

wlroots manda `wl_keyboard.modifiers` **solo al client con il fuoco**
(`seat/wlr_seat_keyboard.c:191-213`). Noi non abbiamo una surface, quindi non dovremmo vedere niente.

**Ma labwc lo trasmette a tutti, senza surface** (`input/keyboard.c:106-133`, chiamato a `:186-193`),
con un commento che dice che **sway lo faceva e ha smesso**. Quindi `mods_locked` dà BlocMaiusc e
BlocNum **veri**, e `group` dà il layout.

| | |
|---|---|
| ✅ | su KDE questa risposta era costata un protocollo dedicato (`org_kde_kwin_keystate`) |
| ⚠ | **è comportamento di labwc, non di protocollo**: su sway la stessa lettura è `[✗]` |
| ⚠ | **lo stato iniziale non arriva mai** — si conosce il primo cambiamento, non la situazione di partenza |
| ⚠ | attenzione all'**anello di retroazione** coi nostri stessi `modifiers` |

#### 7.4 La keymap: presentarla noi, ma copiata dal filo

Obbligatoria prima di ogni `key` (`no_keymap`, `wlr_virtual_keyboard_v1.c:83-88`). ⭐ **La forma
giusta**: fare `wl_seat.get_keyboard` — wlroots manda `keymap` subito, senza fuoco
(`seat/wlr_seat_keyboard.c:412-417`) — e **rigirare quel contenuto**. È meglio di wayvnc, che la
genera da configurazione, e c'è una ragione forte: su labwc **ogni tasto** fa
`wlr_seat_set_keyboard`, che **rimanda la keymap a tutti i client**.

✅ **La ripetizione non la facciamo noi**: nessuno ripete lato compositore, i `key down` ripetuti di
RDP sono comunque **scartati** da wlroots (`wlr_keyboard.c:68-83`), e la ripetizione la fa
l'applicazione via `repeat_info`.

#### 7.5 ⚠ Le nostre scorciatoie le mangia labwc

`match_keybinding(..., is_virtual)` salta il confronto per keycode ma **applica comunque le
scorciatoie** (`input/keyboard.c:225-228`, `:548-560`), e le mousebind di scorrimento ingoiano lo
scatto usando anche **i nostri** modificatori (`keyboard_get_all_modifiers`, `:57-79` — con un
commento che nomina wayvnc). Da mettere in conto: parte di quel che mandiamo non arriva alle
applicazioni.

#### 7.6 Il seat: si inietta in quello esistente

**[✗] labwc non crea `ext_transient_seat_v1`** (sway sì, wlroots ce l'ha). Su XFCE **non c'è scelta**:
si inietta nel seat dell'utente. ⭐ E dato che REMOTIX gira **senza utente presente**, è anche il caso
migliore — è precisamente ciò che ci regala la lettura dei lucchetti veri di §7.3.

---

### 8. ✅ Gli appunti: `appunti_wlr.c` funziona così com'è

*Dettaglio: `reference-xfce/rapporti/05-appunti.md`.*

`zwlr_data_control_manager_v1` **v2** su tutti e tre i compositori, senza permessi. Il file l'abbiamo
scritto per KWin ma **contro il protocollo di wlroots**: qui siamo in casa sua.

**Le due lezioni pagate su KWin reggono, e per lo stesso motivo meccanico:**

| | |
|---|---|
| **L'eco è certa, non probabile** | ogni device si iscrive a `seat->events.set_selection` **senza filtro sull'originatore** (`wlr_data_control_v1.c:620-622`) |
| **`cancelled` precede `selection`** | e più solidamente che su KWin: sta tutto dentro `wlr_seat_set_selection` — riga 196 distrugge la vecchia source, riga 211 emette il segnale. **Due righe della stessa funzione, nessun rientro asincrono in mezzo.** La guardia di stato **non va rivista** |
| **`POLLHUP` vale come «pronto»** | `client_source_send` fa `close(fd)` subito dopo l'evento (`:131`): con dati corti la `poll` torna con solo `POLLHUP` |

**Le tre riserve, tutte nostre e tutte piccole:**

1. **[?] `kwin_display_apri`** (`appunti_wlr.c:441`): se filtra il socket per nome, su labwc non si
   apre nulla. È l'unica cosa che può impedire al file di funzionare;
2. **wlroots scarta i MIME duplicati in silenzio** (`:47-54`) e la nostra `tipi_uguali` boccia su
   lunghezza diversa: un duplicato nell'elenco del client ⇒ guardia saltata ⇒ **ciclo infinito**;
3. lo scavalco `onlyReplaceEmpty` è inutile qui: **[✗]** assente da tutto l'albero.

⭐ **E c'è una guardia migliore della nostra, da valutare**: wayvnc offre un **secondo MIME sintetico**
`x-wayvnc-client-%08x` e, se lo rivede in un'offerta, sa che è sua e la ignora
(`wayvnc/src/data-control.c:196-199`). È più solido di un confronto sui tipi, e in RDP il problema è
identico.

**Il resto, in breve**: **[✗] `ext-data-control-v1` non esiste** né in wlroots 0.18.2 né in
wayland-protocols 1.38 — su Trixie `zwlr` è l'unica porta, benché a monte sia già marcato deprecato.
Il ponte Xwayland funziona **in entrambe le direzioni gratis**, passando dallo stesso stato del seat.
La clipboard **non sopravvive alla morte di chi ha copiato**, e in XFCE su Wayland **non c'è nessun
gestore** (`xfsettingsd` lo avvia solo sotto X11): cioè il coinquilino che su KDE era klipper qui non
c'è.

---

### 9. La sessione XFCE senza monitor

*Dettaglio: `reference-xfce/rapporti/06-sessione-xfce.md`.*

#### 9.1 Il compositore è cablato in uno script

`default_compositor="labwc"` in `xfce4-session/scripts/startxfce4.in:121` — **non è una
configurazione, è una riga di script**. Si sostituisce solo passando la riga di comando a
`startxfce4 --wayland <cmd>` (`:37-40`, `:164`), oppure con `XFCE4_SESSION_COMPOSITOR`, che viene
`exec`-ato tal quale (`xinitrc.in:147`).

⭐ **La riga da copiare**: `labwc --config-dir … --config … --session xfce4-session`. Il `--session`
rende `xfce4-session` il *primary client*: quando esce, **labwc termina**
(`labwc/src/main.c:43`, `:96-104`; `server.c:167-170`). Il logout viene gratis.

#### 9.2 ⛔ La trappola che può ammazzare la nostra sessione

Se `XFCE4_SESSION_COMPOSITOR` non contiene **sia** `labwc` **sia** `--session`, al logout
`xfce4-session` esegue **`loginctl terminate-session ''`** (`xfce4-session/main.c:257-273`) — cioè la
sessione logind di REMOTIX.

**Doppia difesa**, e vanno messe tutte e due: xfconf `xfce4-session` `/general/WaylandLogoutCommand`
= `/bin/true` (ha la precedenza, `:259`) **più** la variabile d'ambiente scritta come si deve.

⚠ **È la prima cosa da provare sul banco**, e mai sull'utente (`LEZIONI.md` §2.6).

#### 9.3 L'ambiente: che cosa mettere e che cosa togliere

| Mettere | Perché |
|---|---|
| `XDG_RUNTIME_DIR` | labwc esce senza (`main.c:201-204`) |
| `XDG_CURRENT_DESKTOP=XFCE` | **prima** di labwc, che altrimenti la mette a `labwc:wlroots` con `overwrite=0` (`config/session.c:249`) |
| `XDG_MENU_PREFIX=xfce-` | ⚠ **non perché manchi** — garcon ripiega su `xfce-` da sé (`garcon-private.h:37-39`, con un commento che dice espressamente «so garcon doesn't break when xfce is not started with startxfce4»). Il pericolo è **ereditarne una sbagliata** (`plasma-`, `gnome-`) **o vuota**: il test è `prefix != NULL`, non `*prefix`, e allora `garcon_menu_load()` fallisce con `G_FILE_ERROR_NOENT` **senza alcun ripiego**. È la lezione §1.10 in forma rovesciata: non «metti la variabile», ma **«componi l'ambiente da zero, o ti porti dietro quella di un altro desktop»** |
| `WLR_BACKENDS=headless` | e `WLR_LIBINPUT_NO_DEVICES=1`, che è la ricetta dichiarata da wayvnc (`FAQ.md:3-8`) e **[M]** provata sul portatile |
| `WLR_RENDER_DRM_DEVICE` | la scheda, §5.2 |
| `LABWC_UPDATE_ACTIVATION_ENV=1` | ⚠ **obbligatoria**: labwc propaga `WAYLAND_DISPLAY` al bus e a systemd **solo se il backend è DRM** (`config/session.c:186-207`). Su headless non lo fa, **in silenzio** |
| `XCURSOR_THEME` (+ `XCURSOR_SIZE`) | §10.1 |

| Togliere | Perché |
|---|---|
| `WAYLAND_DISPLAY`, `WAYLAND_SOCKET` | backend annidato (`wlroots/backend/backend.c:375-402`) |
| `DISPLAY` | backend X11 — e su GTK fa ripiegare su X11 **in silenzio**, riaccendendo XSETTINGS, grab della tastiera e systray XEmbed: **due comportamenti sotto la stessa etichetta**, cioè la lezione §1.8 |
| `SESSION_MANAGER` | `xfce4-session` esce (`main.c:97-102`) |
| `GDK_BACKEND` | va messo a **`wayland` secco**, non `wayland,x11` |

⚠ **`~/.ICEauthority` deve essere scrivibile**: `xfce4-session` esce anche su Wayland se non riesce ad
aprirlo (`main.c:114-127`).

#### 9.4 ⚠ Otto secondi per gruppo di priorità, e sono strutturali

Su Wayland **nessun client si registra al gestore di sessione**, quindi ogni gruppo di priorità si
sblocca **a timeout**: `STARTUP_TIMEOUT_WAYLAND = 8000` (`xfsm-manager.h:43`).

E la ragione è definitiva, non un caso limite: `xfce-sm-client.c` è compilato **solo dentro
`if ENABLE_X11`** (`libxfce4ui/Makefile.am:73-82`), `configure` forza `enable_libsm=no` senza X11, la
connessione è XSMP puro e richiede `$SESSION_MANAGER`, che `xfce4-session` esporta solo nello strato
X11. **[✗] Nessuno può registrarsi su Wayland, e nessuna chiave xfconf accorcia il timeout** — le
costanti sono cablate.

⭐ **Da cui: il timeout di REMOTIX per «il desktop è su» va tarato ≥ 8 s**, e una sessione salvata con
priorità diverse lo moltiplica.

#### 9.5 Il logout: sorveglianza passiva, come su KDE

| | |
|---|---|
| **bus** | `org.xfce.SessionManager` |
| **path** | `/org/xfce/SessionManager` |
| **interfaccia** | `org.xfce.Session.Manager` ⚠ **nome ≠ interfaccia**, attenzione al punto |
| **segnale** | `StateChanged(u old, u new)` — 0 Startup, 1 Idle, 2 Checkpoint, 3 Shutdown, 4 Phase2 |
| **«il desktop è su»** | `StateChanged(old=0, new=1)` (`xfsm-manager.c:861-867`). ⚠ Usare `old==0`: il Checkpoint produce 1→2→1 |

✅ **Non registrarsi e non inibire**: `Logout` **non consulta l'inibitore**
(`xfsm-manager.c:2409-2431`), e un `RegisterClient` ci farebbe aspettare fino a `DIE_TIMEOUT` — lo
stesso errore che su KDE avrebbe frenato il logout di quindici secondi.

#### 9.6 ⚠ La sessione salvata è legata al nome del socket

`~/.cache/sessions/xfce4-session-<display>` con `display` = `wayland-0`… Un socket diverso è una
sessione diversa, e **una sessione salvata sbagliata risorge con priorità e geometrie di un altro
schermo**. `SaveOnExit` è già `false` di default, ma la cache va **cancellata a ogni avvio**.

È la stessa forma del difetto di KDE, dove plasmashell scriveva `SceneGraphBackend=software` in modo
persistente: **una sessione avviata male lascia un segno nella casa dell'utente**.

#### 9.7 Il bus di sessione — una decisione da prendere

`startxfce4 --wayland` usa **`dbus-run-session`**: bus privato che nasce col compositore e muore col
logout. ⚠ Se lo usiamo, **il sorvegliante di REMOTIX non vede `StateChanged`**.

Su Trixie `dbus-user-session` è installato, quindi **[?] la strada raccomandata è il bus d'utente di
systemd** (`$XDG_RUNTIME_DIR/bus`) senza `dbus-run-session`. È una scelta di progetto, da provare.

---

### 10. Il sistema attorno: cursore, energia, voci di menu

*Dettaglio: `reference-xfce/rapporti/07-componenti-xfce.md` e `06-sessione-xfce.md` §13.*

#### 10.1 ⭐ Il cursore: la cura di KDE si trasporta, con un vincolo in meno

**Il fatto**: su output headless il cursore è **sempre** dentro l'immagine catturata. Il backend
headless non implementa `set_cursor` [✗], quindi non esiste cursore hardware, quindi la scena lo
dipinge nel framebuffer (`types/output/cursor.c:285-289`, `types/scene/wlr_scene.c:1998`). E
`overlay_cursor` **non toglie niente**: *forza* i cursori software (`wlr_screencopy_v1.c:451-454`).

⭐ **La cura è la stessa di KDE — rendere il cursore invisibile, non nasconderlo**: un tema
`XCURSOR_THEME` con un cursore 1×1 ad alfa zero, e il puntatore torna a essere quello del client.

| | |
|---|---|
| ✅ **un vincolo in meno** | su labwc il tema arriva da `XCURSOR_THEME`/`XCURSOR_SIZE` **dell'ambiente** (`labwc/src/input/cursor.c:1405-1414`), e **`XCURSOR_SIZE` non è obbligatoria** (default 24 nella riga stessa) — a differenza di KWin, che il tema lo guardava solo se c'era anche la misura |
| ⛔ **la stessa trappola** | se il tema carica **zero** cursori, wlroots ripiega su un tema **incorporato e visibile** (`wlr_xcursor.c:219-221`). Serve almeno un cursore valido, `index.theme` **senza `Inherits=`**, e i dieci nomi che labwc chiede (`cursor.c:39-64`) |
| ⚠ **due leve, non una** | l'ambiente copre il compositore e i client non-GTK; i client **GTK3** usano il proprio tema, che su Wayland arriva da xfconf `xsettings /Gtk/CursorThemeName` via un **modulo GTK annunciato su D-Bus** (`org.gtk.Settings`), non più via XSETTINGS |
| ✅ **il punto d'inserimento c'è già** | XFCE spedisce `xfce4-session/labwc/labwc-environment:7` con `XCURSOR_THEME=Adwaita`, e `startxfce4.in:141-146` lo copia **solo se manca** |

#### 10.2 ⛔ `xfce4-power-manager` spegne l'output, e va inibito

Parla Wayland nativo: `zwlr_output_power_v1_set_mode(OFF)` (`xfpm-dpms-wayland.c:233`), con default
`DPMS_ENABLED TRUE` e **10 minuti su rete elettrica** (`common/xfpm-config.h:50-60`). labwc espone il
protocollo (`server.c:683-688`) e su `MODE_OFF` **disabilita l'output** (`output.c:1063-1078`) ⇒
timer mai riarmato ⇒ **`failed` sulla cattura**.

| Via | Come |
|---|---|
| **D-Bus** | `org.freedesktop.PowerManagement.Inhibit` su `/org/freedesktop/PowerManagement/Inhibit`, firma `(ss)→u` (`xfpm-inhibit.c:349-353`). Copre DPMS + idle + screensaver in un colpo. ⚠ **Precondizione**: xfce4-power-manager **non ha attivazione D-Bus** [✗] — se non gira, la chiamata fallisce (è la forma del difetto di powerdevil su KDE, dove l'errore era `ServiceUnknown`) |
| **xfconf** | `dpms-enabled=false`, `inactivity-on-{ac,battery}=0`, `presentation-mode=true` |
| ⭐ **la cura di wayvnc** | `set_mode(MODE_ON)` **prima** di catturare, più ritento a 100 ms (`wayvnc/src/main.c:1022-1045`, `:1055-1063`) — cioè non fidarsi dell'inibizione, ma **riaccendere** |

✅ **`xfce4-screensaver` invece non è un rischio**: è X11 puro e esce con `EXIT_FAILURE` se il display
GDK non è X11. ⚠ Ma con `GDK_BACKEND=wayland,x11` potrebbe risorgere su Xwayland: **`wayland` secco**.

#### 10.3 ⭐ Il blocco schermo si spegne con una chiave sola

Su KDE questa parte è stata KIOSK; qui la leva è più semplice e più forte: xfconf canale
`xfce4-session`, chiave **`/general/LockCommand`**. Se è impostata, `xfce_screensaver_lock()` la
esegue e **ritorna il suo esito senza provare nient'altro** — niente D-Bus, niente `xdg-screensaver`,
niente ripieghi (`libxfce4ui/xfce-screensaver.c:570-596`).

Impostandola a `/bin/false` si neutralizzano **in un colpo** `xflock4`, il metodo D-Bus
`org.xfce.Session.Manager.Lock` e ogni pulsante del pannello.

⚠ **La stringa vuota conta come «non impostata»** (`:299-305`): il default Debian `LockCommand=""` è
normalizzato a NULL, quindi oggi la catena D-Bus prosegue. Va scritto un valore **vero**.

⚠ E due dettagli che spiegano perché conviene: la catena D-Bus può **attivare** `xfce4-screensaver`
(che su Wayland esce subito), e i tre ripieghi sono `g_spawn_command_line_sync`, cioè **bloccano il
ciclo principale di `xfce4-session`**.

#### 10.4 ⛔ In XFCE non esiste un KIOSK — e le voci vanno tolte, non bloccate

Confermato in modo definitivo: in tutto l'albero clonato, librerie comprese, `xfce_kiosk_query`
compare **solo** in `xfsm-shutdown.c:137-138`, con due sole capacità: **`Shutdown`** e
**`SaveSession`**. [✗] Nessun uso in pannello, scrivania, impostazioni, energia, salvaschermo,
libxfce4ui. **KIOSK non può togliere il blocco schermo né toccare il pannello.**

| | |
|---|---|
| **Il blocco xfconf** | impedisce di **cambiare** una voce, **non la rimuove** |
| **La leva vera** | plugin `actions` del pannello: `xfce4-panel /plugins/plugin-<N>/items`, **array di stringhe** con prefisso `+`/`-`; il `-` fa `continue`, cioè **la voce non viene creata** (`actions.c:1318`, `:1518`). Una voce `+` non permessa resta invece **visibile e grigia** |
| ⚠ **due insidie** | i nomi `logout`/`logout-dialog` sono **invertiti** rispetto agli enum; e il default di serie ha già `+lock-screen` e `+switch-user` |
| ⛔ **togliere `xflock4` non basta** | il plugin ripiega su `loginctl lock-session`, `dm-tool`, `gdmflexiserver`, `shutdown`, `systemctl` (`actions.c:1049-1085`) |
| **[✗] il dialogo di logout** | nessuna chiave toglie «Log Out/Restart/Shut Down»: restano solo polkit e logind |

⭐ **Il modo di preimpostare il pannello**: `xfce4/panel/default.xml` cercato lungo `XDG_CONFIG_DIRS`
(`migrate/main.c:36-37`, `:63-101`), applicato **in silenzio** se non è quello di serie. Per gli altri
canali i default di sistema stanno in `/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/<canale>.xml`.

#### 10.6 xfconf: il lock, e la scrittura che riesce senza riuscire

| | |
|---|---|
| **Il lock è un attributo XML**, non un file a parte | `locked="utente"` (o `unlocked=`) su `<channel>` o `<property>` (`xfconf/docs/spec/perchannel-xml.txt:44-53`). Ammesso **solo nei file di sistema**: in un file d'utente è un **errore di parsing** |
| ⭐ **Col canale bloccato il file dell'utente non viene nemmeno letto** | (`xfconf-backend-perchannel-xml.c:1710`) — è la forma più forte, ed è quella che ci serve |
| ⛔ **Due trappole del lock** | **`locked="*"` non blocca nessuno** (nessun jolly: solo `strcmp`), e **`@gruppo` guarda solo `gr_mem[]`**, quindi **ignora il gruppo primario** — su Debian `@<nomeutente>` non funziona. Si scrive **il nome utente secco** |

⛔ **E il punto che cambia il modo di scrivere il provisioning**: **una scrittura su proprietà bloccata
non dà errore a chi scrive.** Il demone rifiuta con `XFCONF_ERROR_PERMISSION_DENIED`, ma
`xfconf_channel_set_property()` è **asincrona**: aggiorna la cache locale, emette `property-changed`,
**ritorna TRUE**; alla risposta il valore viene ripristinato e resta un `g_warning` su stderr. ⇒
**`xfconf-query` esce con `EXIT_SUCCESS`.**

⭐ **Da cui la regola, che è `LEZIONI.md` §1.9 applicata alla configurazione: dopo aver scritto un
valore, lo si rilegge.** Un banco che si accontenta dello stato d'uscita di `xfconf-query` è verde su
una configurazione che non è stata applicata.

⚠ E tre dettagli del demone: `xfconfd` **ha** attivazione D-Bus e i canali si caricano pigramente
(quindi scrivere i default *prima* che parta funziona); ma **[✗] non ha alcun `GFileMonitor`** — un
canale già caricato **non rilegge** un file cambiato sotto; e la scrittura su disco è **ritardata di
5 secondi**, con flush ordinato su `SIGTERM` e **perso** su `SIGKILL`.

⛔ **Correzione a quel che si poteva sperare**: i default di sistema evitano di *scrivere* nella casa
dell'utente, **non** che vi resti traccia. `xfconfd` **crea sempre**
`~/.config/xfce4/xfconf/xfce-perchannel-xml/` all'avvio — e **non parte** se non ci riesce — e alla
prima scrittura vi riversa **l'intero albero del canale**. **[?] L'unica via per non lasciare traccia
è un `XDG_CONFIG_HOME` effimero**, che è una decisione di progetto, non un dettaglio.

#### 10.7 ✅ Il menu: garcon non ha la trappola di KDE

**[✗] garcon non costruisce alcun indice su disco** (grep su `g_file_set_contents|fopen|g_mkdir…` →
zero, con controllo positivo): la cache è **solo in memoria**. Cioè il difetto che su KDE ci ha
negato un permesso — *un indice costruito vuoto che resta vuoto* — **qui non può succedere sul
disco**.

⛔ **Ma la stessa forma esiste in memoria**: `garcon_menu_start_monitoring()` è chiamata **dopo** il
caricamento riuscito (`garcon-menu.c:817-819`). Se il primo caricamento fallisce, **non esiste alcun
monitor**, quindi `reload-required` non arriva mai e il menu resta vuoto **per la vita del
processo** — e il fallimento è **una finestra modale in faccia all'utente remoto**. Su XFCE non si
cancella un file: **si riavvia il processo**.

⚠ E `XDG_CURRENT_DESKTOP` va **`XFCE` secco, maiuscolo, senza suffissi**: per i sottomenu garcon
**non spezza sui `:`** (mentre per le voci sì), quindi con `XFCE:qualcosa` le directory
`OnlyShowIn=XFCE;` **spariscono**. Con la variabile *vuota* il filtro si spegne e si vede **di più**,
non di meno.

✅ Infine, letto nel menu spedito: **«Esci» è una voce del file**, mentre **«Blocca schermo» e «Cambia
utente» non sono voci di menu** [✗] — vivono solo nel pannello (§10.4).

#### 10.5 I requisiti duri di XFCE sul compositore

| Protocollo | Chi lo pretende | Che cosa succede senza |
|---|---|---|
| `zwlr_layer_shell_v1` | xfdesktop, xfce4-panel | ⛔ **xfdesktop esce con `exit(1)`** (`xfdesktop-application.c:1017-1027`); il pannello degrada e non carica plugin esterni |
| `zxdg_output_manager_v1` | libxfce4windowing | la geometria **logica** viene solo da lì: senza, resta `{0,0,0,0}` e con essa il workarea |
| `wl_output` **v4** | libxfce4windowing | il `name` è l'identificatore |
| `ext_workspace_manager_v1` | il pager | ✅ labwc ce l'ha; **[✗]** sway e wayfire no |

✅ Tutti presenti in labwc 0.8.3. ⚠ E `xfsettingsd` su Wayland **non registra alcuna scorciatoia**
(sei moduli dietro `#ifdef ENABLE_X11`): il canale `xfce4-keyboard-shortcuts` è **inerte**, e nessuna
combinazione può lanciare `xflock4`. Effetto collaterale: XSettings non propagato, quindi temi e font
diversi da quelli attesi.

---

### 11. Chi lo fa già, e che cosa gli si ruba

*Dettaglio: `reference-xfce/rapporti/08-wayvnc.md`, `09-weston-rdp.md`, `10-portale-e-chi-lo-fa.md`.*

#### 11.1 wayvnc — il riferimento pratico della famiglia

**Le cinque cose da copiare:**

1. ⭐ **la cadenza che sottrae la latenza del compositore** (§4.2): è la correzione strutturale al
   problema dei 18 fps;
2. ⭐ **il libro doppio del danno** (§4.3): obbligatorio, non un'ottimizzazione;
3. ⭐ **l'interfaccia astratta con due implementazioni di cattura** e le capacità in una maschera di
   bit, con **un solo punto** di diramazione;
4. **il MIME-marchio anti-eco** sulla clipboard (§8);
5. **`--show-performance`**: fotogrammi al secondo **e percentuale media di area danneggiata**, ogni
   secondo. Il secondo numero è quello che i nostri banchi non hanno mai avuto.

**Le tre da non copiare:** DMA-BUF **spento di default** (`--gpu`); nessuno scaler per client — chi
non sa ridimensionarsi **viene disconnesso**, e col nostro requisito 4K/60 non regge; e la creazione
dell'output **delegata a `swaymsg`**, che su labwc non esiste.

⚠ E due suoi difetti utili come avvertimento: il regolatore di banda **è volontario** (se il client
non annuncia `FENCE` il freno non si arma mai — il nostro deve restare obbligatorio), e il cursore
viene **solo** dal protocollo nuovo: con il solo `wlr-screencopy` wayvnc **non manda alcun cursore**.

#### 11.2 Weston — il backend RDP più vecchio del mondo Wayland

**Il suo video è arretrato e non c'è niente da copiare lì**: [✗] niente MS-RDPEGFX, niente H.264,
niente GPU (anche col renderer GL il buffer viene riletto in RAM e compresso dalla CPU), il danno
diventa un bounding box, e **[✗] il regolatore di flusso non esiste** — annuncia
`SurfaceFrameMarkerEnabled=TRUE` e poi non ascolta gli ack. **La nostra formula è più avanzata del
progetto di riferimento.**

**Ma tre cose valgono, e sono tutte accessibili a noi:**

| | |
|---|---|
| ⭐ **la rotella RDP→Wayland** | riga per riga (§7.2) |
| ⭐ **il ponte thread → ciclo eventi** | `eventfd(EFD_SEMAPHORE)` + lista con mutex + `assert_compositor_thread()` in cima a ogni callback (`rdputil.c:79-226`). Serve subito: anche il nostro `cliprdr` gira su un thread di FreeRDP |
| ⭐ **il certificato per peer, mai condiviso** | il backend tiene solo i **percorsi**; ogni peer fa `freerdp_certificate_new_from_file()` e cede la proprietà a FreeRDP (`rdp.c:1755-1764`). **È l'antidoto diretto al difetto che su KDE uccideva il server alla seconda connessione** |

E due regali per la conversione dell'input: la catena
`GetVirtualKeyCodeFromVirtualScanCode → KBDEXT → GetKeycodeFromVirtualKeyCode(XKB) → scan_code - 8`
(nessuna tabella a mano: si delega a WinPR), e ⚠ **la trappola di FreeRDP 3**: `KBD_FLAGS_DOWN` non è
mai settato — **l'assenza di `KBD_FLAGS_RELEASE` *è* la pressione**.

⚠ **E una lezione §1.11 in forma pura**: i lucchetti di Weston **non funzionano**, e non lo dichiara
nessuno. `weston_keyboard_set_locks()` esce con `-1` alla prima riga se `!seat->led_update`, e il
seat RDP non lo imposta mai. L'idea è giusta, l'attuazione è morta: **va verificato il primo `return`
di ogni API che chiamiamo**.

Del ridimensionamento: **[✗] MS-RDPEDISP non c'è**, ma c'è una cosa da rubare — alla nuova misura
Weston **copia il vecchio contenuto nel nuovo buffer** (`PIXMAN_OP_SRC`) per non mostrare nero al
primo fotogramma.

#### 11.3 Il ponte PipeWire: gratis sulle copie, caro su tutto il resto

`xdg-desktop-portal-wlr` alloca i buffer lui e **passa lo stesso `wl_buffer` a screencopy**: DMA-BUF =
**un blit GPU**, che è la copia intrinseca del protocollo e ci sarebbe identica parlando screencopy
da soli. **Sulle copie il ponte non costa niente.**

**Il prezzo è altrove, e sono quattro fatti strutturali:**

| | |
|---|---|
| ⛔ **non possiamo chiedere un fotogramma** | nessun `.process`, nessun `PW_STREAM_FLAG_DRIVER`, e **sempre `copy_with_damage`** — a schermo fermo `ready` non arriva |
| ⛔ **non possiamo negoziare la misura** | [✗] `SPA_POD_CHOICE_RANGE_Rectangle` non esiste: la misura è un `SPA_POD_Rectangle` fisso. Il ridimensionamento passa da un protocollo **separato** |
| ⛔ **niente cursore separato** | `METADATA` è rifiutato, `SPA_META_Cursor` mai citato. RDP vuole il *Pointer Update* a parte |
| ⚠ **quattro processi, ≥3 salti IPC** | su un budget di **16,6 ms** per fotogramma |

**Il conto opposto**: parlare screencopy direttamente costa **[R] ≈1 200 righe nuove** — ma il
DMA-BUF resta un `gbm_bo` allocato da noi, quindi **l'importazione e l'attesa della fence delle fasi
8 e 9 si riusano intere**: si perde solo lo strato `pw_stream`.

---

### 12. Le quattordici domande di `LEZIONI.md` §3, con la colonna wlroots riempita

*Tutte **[R]** salvo dove segnato: è una lettura di codice, non una misura, e §14 dice quali vanno
misurate per prime.*

| # | La domanda | wlroots 0.18.2 / labwc 0.8.3 |
|---|---|---|
| 1 | **Come si chiede la cattura senza portale?** | `zwlr_screencopy_manager_v1` **v3**, protocollo Wayland diretto |
| 2 | **Spinge o fa tirare?** | ⛔ **fa tirare**: `capture_output → frame → copy → ready`, uno per fotogramma |
| 3 | **È dietro un permesso?** | ✅ **no** [M]. Nessun filtro, nessun `.desktop`, nessun dialogo |
| 4 | **Senza monitor disegna sulla GPU?** | ✅ **sì** con headless + default (GLES2 + GBM). ⚠ ma il ripiego in pixman è **silenzioso**, e non c'è modo di chiedere al compositore che renderer usa [✗] |
| 5 | **Si può chiedere uno schermo virtuale della misura voluta?** | ⛔ **non all'avvio** (1280×720 cablati), ✅ **sì dopo**, con `set_custom_mode` |
| 6 | **Quanto consegna?** | **61** a 1080p e 1440p, **40,3** a 4K [M, 7 ago, sway, `wl_shm`] — a 4K il costo è la copia in memoria |
| 7 | **La cadenza dichiarata come si comporta?** | ⭐ **non esiste una cadenza da dichiarare**: il refresh dell'output headless *è* il periodo del timer, e il ritmo lo detta il nostro ciclo |
| 8 | **Interi o «diff»?** | ✅ **interi, sempre** — il danno non è mai consultato nella copia |
| 9 | **Il buffer arriva già disegnato?** | ⚠ **[?]**: GLES2 fa solo `glFlush()`, nessuna fence esplicita. **Da misurare** |
| 10 | **Che cosa costa la risoluzione?** | a 4K **sì** in memoria (61 → 40); **[?]** in DMA-BUF, da misurare |
| 11 | **Che cosa costa la profondità di colore?** | niente; nessun percorso a 24 bit impacchettati |
| 12 | **Si può cambiare misura a cattura viva?** | ✅ **sì** — ma **[?]** che cosa succede alla cattura in corso va misurato |
| **12-bis** | ⭐ **Il cursore è dentro l'immagine?** | ⛔ **sì, sempre**, su headless. E `overlay_cursor` non lo toglie |
| **13** | ⭐ **Uno schermo virtuale si ridimensiona a caldo?** | ✅ **sì, senza tetto** — la risposta migliore delle tre famiglie |
| **14** | ⭐ **La clipboard di chi è?** | **del compositore**, `zwlr_data_control_manager_v1` v2, nessun permesso — e **nessun gestore di appunti** in XFCE su Wayland |

⭐ **E la quindicesima, che questo desktop aggiunge alla lista per il prossimo**: **«chi possiede il
ciclo dei fotogrammi?»** Su Mutter e KWin lo possiede il compositore e noi consumiamo; qui lo
possediamo **noi**, e con esso il ritmo, il costo e la responsabilità di non far rendere il
compositore a vuoto. È la domanda 2 portata alle sue conseguenze, e va posta **prima** della 6:
perché su un compositore a tiro, *«quanto eroga»* non è una proprietà del compositore — **è una
proprietà del nostro ciclo**.

---

### 13. Le scelte da mettere davanti all'utente

| # | La scelta | I termini |
|---|---|---|
| **1** | **Screencopy diretto o ponte PipeWire?** | diretto: ~1 200 righe nuove, ma controllo del ritmo, del cursore e della misura, e riuso intero del consumatore DMA-BUF delle fasi 8-9. Ponte: meno righe, ma ⛔ nessuna delle tre cose sopra, e quattro processi sul budget di 16,6 ms |
| **2** | **Il ridimensionamento a caldo si accende subito?** | su KDE si era scelta la misura fissa **perché KWin non sapeva fare altro**. Qui **si può**, e il precedente (wayvnc) esiste. Resta da decidere se farlo nella fase 11 o dopo |
| **3** | **Il cursore: dentro l'immagine o sul canale RDP?** | oggi il tema trasparente è la cura pronta (§10.1). Il cursore *vero* — forma e hotspot sul canale puntatore di RDP — arriva **solo col protocollo nuovo**, che su Trixie non c'è: sarebbe lavoro che oggi non si può nemmeno provare |
| **4** | **Il bus di sessione: privato o d'utente?** | `dbus-run-session` è quel che XFCE fa di suo, ma **ci nasconde `StateChanged`**. Il bus d'utente di systemd è la strada raccomandata **[?]**, e va provata |
| **5** | **Le voci pericolose: quante ne togliamo?** | «Blocca schermo» ha una cura netta (§10.3). «Cambia utente» e lo spegnimento chiedono di riscrivere la disposizione del pannello — che è una modifica alla casa dell'utente, e il suo prezzo lo paga lui |

---

### 14. Il piano di misure che apre la fase

*Nell'ordine, e ogni misura ha un controllo positivo, perché «zero» e «proibito» hanno lo stesso
aspetto (`LEZIONI.md` §1.9).*

| # | La misura | Perché è lì |
|---|---|---|
| **M1** | i due global dell'input compaiono davvero da una **shell SSH**, e i device si creano | è la premessa di tutto il capitolo 7. Il permesso della cattura è già misurato, quello dell'input no |
| **M2** | ⛔ **`WaylandLogoutCommand` impedisce `loginctl terminate-session ''`** | è l'unica misura che, sbagliata, **ammazza la sessione di chi la esegue**. Sul banco, mai sull'utente |
| **M3** | screencopy su **DMA-BUF**: il buffer è intero? la fence è pronta o va aspettata? | sono le domande 8 e 9, e decidono se la copia zero nasce accesa come su KDE |
| **M4** | la **cadenza a 1080p e 4K** con la scena dichiarata, contando anche quanto disegna il client | R32 rifatta per questa famiglia — e qui il numero dipende **dal nostro ciclo**, non dal compositore |
| **M5** | GPU o pixman: **controllo positivo** con `WLR_RENDERER=pixman` e con la scheda sbagliata | §5.2. Il ripiego è silenzioso per costruzione |
| **M6** | `set_custom_mode` a cattura viva: la cattura sopravvive? il pannello si ridispone? | §6, e il verso di `xfsettingsd` che disabilita gli output nuovi |
| **M7** | la sessione XFCE completa parte headless, e in quanti secondi | §9.4: gli otto secondi per gruppo di priorità sono strutturali |
| **M8** | l'inibizione del DPMS regge dieci minuti | §10.2, e la precondizione che xfce4-power-manager sia vivo |
| **M9** | il tema del cursore trasparente **non fa ripiegare** wlroots sul tema visibile | §10.1, ed è la trappola già pagata su KDE |
| **M10** | `appunti_wlr.c` così com'è, contro labwc | §8, e le tre riserve |
| **M11** | ogni valore xfconf scritto dal provisioning **si rilegge** | §10.6: la scrittura riuscita non prova niente, ed è un verde che costa un pomeriggio |

---

### 15. Le lezioni che questo studio aggiunge, prima ancora di misurare

1. ⭐ **Su un compositore a tiro, «quanto eroga» non è una domanda sul compositore.** Le tabelle di
   R32 per Mutter e KWin misuravano *loro*; qui misureranno **il nostro ciclo**. Chi citerà il numero
   deve citare anche la cadenza che gli abbiamo chiesto e il modo in cui gliel'abbiamo chiesta.
2. ⭐ **La leva che sembra esserci e non fa niente si ripresenta, con un altro nome.** Su KWin era
   `KWIN_COMPOSE=O2`; qui è `overlay_cursor`, che *forza* i cursori software invece di togliere il
   cursore. **Per ogni interruttore che troviamo, va scritto che cosa mostrerebbe il caso opposto**
   (§1.11) — e questa volta lo sappiamo prima di misurare, non dopo.
3. ⭐ **Il precedente più utile può essere una rimozione.** wlroots ha *tolto* il proprio backend RDP
   in favore di un client esterno: è la conferma più forte che l'architettura di REMOTIX sia quella
   giusta, e non l'avremmo trovata leggendo il codice presente — solo cercando **chi lo fa, e chi ha
   smesso**.
4. ⚠ **Legarsi ai protocolli, non alla libreria.** XFCE sta scrivendo un compositore proprio in Rust
   su smithay, non su wlroots. Tutto ciò che scriviamo contro `zwlr_screencopy`,
   `zwlr_virtual_pointer` e `zwlr_data_control` sopravvive a quel cambio; tutto ciò che assume
   *wlroots* no.
5. ⭐ **Una scrittura che riesce non è una configurazione applicata.** `xfconf-query` esce con zero
   anche quando il demone ha rifiutato e ripristinato il valore, perché l'API è asincrona e la cache
   locale risponde prima. È `LEZIONI.md` §1.9 spostata dalla misura alla configurazione: **una
   scrittura che può essere rifiutata dev'essere riletta**, e vale per ogni valore che il
   provisioning imposta.
6. ⚠ **Le variabili d'ambiente pericolose non sono quelle che mancano, ma quelle che si ereditano.**
   Garcon ha un ripiego per `XDG_MENU_PREFIX` assente, e nessuno per una sbagliata; `XDG_CURRENT_DESKTOP`
   con un suffisso fa sparire i sottomenu; `DISPLAY` fa ripiegare GTK su X11 in silenzio. È la lezione
   §5 di `LEZIONI.md` — *chi avvia una sessione le regala tutto il proprio ambiente* — e su questo
   desktop morde in tre punti diversi.


<a id="lxqt"></a>

## LXQt su Wayland — studio del codice, per la fase 11

*Scritto l'8 agosto 2026, con dieci ricerche parallele sui sorgenti clonati alle versioni di Debian
Trixie. È il settimo studio del progetto, e il **quarto desktop** dopo GNOME, KDE e XFCE.*

> **Le marche, e contano più delle frasi:**
>
> | | |
> |---|---|
> | **[R]** | letto nel codice, con `file:riga`. **Non è una misura** |
> | **[R-pkg]** | letto nel pacchetto Debian (`apt-cache`, `dpkg-deb -c`): dice che cosa la distribuzione *spedisce*, che è cosa diversa da che cosa il progetto *scrive* |
> | **[M]** | misurato |
> | **[?]** | deduzione o ipotesi |
> | **[✗]** | verificata assente, con il modo in cui è stata cercata e un controllo positivo |
>
> Il dettaglio sta nei **dieci rapporti** in `reference-lxqt/rapporti/`. Qui c'è quel che serve per
> decidere.

---

### 1. In due minuti, e la riga che conta più di tutte

> ### ⛔ **Su Debian Trixie, LXQt su Wayland non esiste come sessione installabile.**
>
> **[R-pkg]**, tre prove indipendenti con controllo positivo:
>
> | | |
> |---|---|
> | `lxqt-wayland-session` **non è in Trixie** | `apt-cache policy` → nessun candidato; l'indice `Packages` elenca **37** pacchetti `lxqt-*` e non lui (controllo positivo: `lxqt-session` → 2.1.1-1, `labwc` → 0.8.3-1) |
> | **nessun pacchetto LXQt** installa un file in `/usr/share/wayland-sessions/` | l'intero `wayland-sessions` di trixie/main ha **10 voci** — labwc, phosh, plasma, sway, weston, **xfce-wayland**… **nessuna LXQt**. LXQt compare solo in `xsessions/` |
> | e lo dice il codice stesso | `lxqt-config-session` crea la pagina «Wayland Settings» **solo se trova l'eseguibile `startlxqtwayland`** (`sessionconfigwindow.cpp:65`), che su Trixie non c'è; e `lxqt-session` avvia il window manager **solo su xcb** (`lxqtmodman.cpp:82-83`) |
>
> Non è un rifiuto di Debian: è un **ritardo**. Il pacchetto esiste in forky/sid a **0.3.1-1**,
> caricato dopo il freeze di Trixie.
>
> ⭐ **Ma il codice Wayland è già spedito e funzionante**: `lxqt-panel` 2.1.4 contiene
> `libwmbackend_wlroots.so` **e** `libwmbackend_kwin_wayland.so` **[R-pkg]**. **Manca solo il
> lanciatore** — che è precisamente la cosa che REMOTIX si scrive da sé, perché la sessione la
> avviamo noi. Il pezzo mancante è **uno script**, non una funzionalità.

**Il compositore è `labwc`** — lo stesso di XFCE — e la struttura è **rovesciata rispetto a X11**: è
il compositore a lanciare la sessione (`labwc -C <dir> -S lxqt-session`), non viceversa
(`lxqt-wayland-session/startlxqtwayland.in:116` **[R]**). Il logout viene gratis dal `-S`, come su
XFCE.

#### 1.1 Il conto del riuso, che è il motivo per cui questo studio esiste

| | Voci | Che cosa |
|---|---|---|
| ✅ **riuso integrale** | **5 su 9** | cattura, input, appunti, ridimensionamento, audio |
| ⚙ **adattamento** | **3** | uscita/logout (cambia il bersaglio D-Bus), cursore (la cura c'è ma passa da un altro canale), energia e blocco (**nessuna** delle leve pagate su GNOME/KDE/XFCE esiste qui) |
| ✍ **da scrivere** | **1, e non è tecnica** | l'avvio della sessione — perché il pacchetto non c'è |

⭐ **Quel che LXQt aggiunge sul compositore è quasi niente**, e va detto chiaramente perché cambia la
taglia della fase: nel caso base è **lo stesso labwc di XFCE**, e il capitolo pixel/tasti/appunti è
§xfce **senza modifiche**. Anzi, **meno tre trappole**:

| Trappola di XFCE | Su LXQt |
|---|---|
| `xfsettingsd` **disabilita** gli output nuovi e apre un dialogo | **[✗]** nessun componente parla `zwlr_output_manager_v1` (2 sole righe in tutto l'albero, e sono stringhe che consigliano `kanshi`) |
| il pannello **esce** se i monitor sono zero | **[✗]** QtWayland crea sempre uno **schermo segnaposto** (`qwaylanddisplay.cpp:402-412`): `screens().at(0)` non è mai fuori range |
| la chiave dello sfondo **è il nome del connector** | **[✗]** `[Desktop] Wallpaper` è unica e globale (`pcmanfm-qt/settings.cpp:243`): il nome dell'output è libero |

⭐ **È il desktop più facile dei quattro sul ridimensionamento a caldo** — e sul ridimensionamento
**siamo l'unico comandante**, cosa che non era vera né su GNOME né su KDE.

#### 1.2 E le cinque cose che costano

| | |
|---|---|
| ⛔ **la sessione va composta a mano** | e con essa `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE`, `XDG_MENU_PREFIX`, `XDG_CONFIG_DIRS`, `QT_QPA_PLATFORM`, l'`rc.xml` di labwc e l'autostart |
| ⛔ **`XDG_CURRENT_DESKTOP` decide metà del pannello** | il backend WM è scelto **dai token della variabile**, case-sensitive, a punteggio. Sbagliarla dà un desktop **vivo e inerte**, con un solo `qWarning` |
| ⛔ **l'autostart che LXQt propone spegne l'output** | `swayidle -w timeout 300 "wlopm --off *"` (`configurations/labwc/autostart:31`): il gemello di `xfce4-power-manager`, ma a **5 minuti invece di 10** |
| ⛔ **le tre cure già pagate non si applicano** | `PowerManagement.Inhibit` **[✗] non esiste**; `LockCommand=/bin/false` qui apre una **finestra modale**; `enableIdlenessWatcher=false` **viene riscritto a `true`** dal demone al primo avvio |
| ⚠ **c'è un coinquilino della clipboard** | `qlipper`, dipendenza del metapacchetto `lxqt`, che **rimette l'ultimo elemento quando la clipboard si svuota** — come klipper, ma **senza marcatura e senza tetto di frequenza** |

#### 1.3 Il passo zero: chi lo fa già

**[✗] Nessuno fa RDP su LXQt-Wayland, su nessun compositore.** Più netto che su XFCE, perché si
somma il fatto che la sessione non è pacchettizzata. Il concorrente è **`xrdp` su X11**
(`/etc/xrdp/startwm.sh` → `Xsession` → `startlxqt`; `grep -ri wayland /etc/xrdp/` → **zero**
**[R-pkg]**).

⭐ **E LXQt appare nelle guide di xrdp più di ogni altro desktop per una ragione che ci riguarda: è
quello che si consiglia quando la macchina remota è piccola.** Cioè il nostro campo esatto.

⭐ **Un precedente inatteso, e importante**: `lxqt-panel_wayland.desktop.in:14` dichiara
`X-KDE-Wayland-Interfaces=org_kde_plasma_window_management` sotto il commento *«Make KWin recognize
us as priviledged client»* **[R]**. È il **quarto precedente indipendente** del meccanismo di permesso
che abbiamo trovato su KDE — dopo KRdp, krfb e il portale — **e l'unico fuori da Plasma**.

---

### 2. La mappa

| Che cosa | Dove | Versione Trixie |
|---|---|---|
| la sessione | `reference-lxqt/lxqt-session/` | **2.1.1** |
| il pannello | `lxqt-panel/` | **2.1.4** |
| impostazioni, aspetto, monitor | `lxqt-config/` | **2.1.1** |
| la scrivania | `pcmanfm-qt/` 2.1.0, `libfm-qt/` 2.1.0 | |
| energia, scorciatoie, notifiche, policykit | `lxqt-powermanagement/` 2.1.0, `lxqt-globalkeys/` 2.1.0, `lxqt-notificationd/` 2.1.1, `lxqt-policykit/` 2.1.0 | |
| librerie e tema Qt | `liblxqt/` 2.1.0, `libqtxdg/` 4.1.0, `lxqt-qtplugin/` 2.1.0, `lxqt-themes/` 2.1.0 | |
| il menu | `lxqt-menu-data/` 2.1.0 | |
| ⚠ **il lanciatore Wayland** | `lxqt-wayland-session/` | **0.4.1 — NON è la versione di Trixie** |
| il compositore e i protocolli | `../REMOTIX_V2/reference-xfce/` (labwc 0.8.3, wlroots 0.18.2, wlr-protocols, wayland-protocols 1.38) | |

⛔ **Attenzione al clone di `lxqt-wayland-session`**: è **0.4.1** (maggio 2026) e richiede **LXQt ≥
2.4.0** e una labwc molto più nuova. **Si legge come specifica delle intenzioni, non si copia**: i
suoi file di configurazione sono per compositori che Trixie non ha. È l'unico repository dello studio
che non corrisponde alla macchina.

---

### 3. La sessione: come si compone quel che Debian non spedisce

*Dettaglio: `rapporti/01-sessione-lxqt.md`.*

#### 3.1 La forma

```
labwc -C <dir nostra> -S lxqt-session
```

Il compositore è il padre; `lxqt-session` è il *primary client*: quando esce, labwc termina. È la
stessa forma di XFCE (`labwc --session xfce4-session`), quindi **il codice di avvio è lo stesso**.

#### 3.2 L'ambiente — e qui si concentra il rischio

| Variabile | Valore | Perché, e che cosa succede sbagliandola |
|---|---|---|
| ⭐ `XDG_CURRENT_DESKTOP` | **`LXQt:labwc:wlroots`** | il pannello sceglie il backend WM **dai token, case-sensitive, a punteggio** (`wlroots` 50, `labwc` 30 — `lxqtpanelapplication.cpp:206-270`). Con `LXQt` secco casca sul backend **`dummy`**: taskbar vuota, pager a uno, tutto inerte, **un solo `qWarning`**. ⛔ E i moduli hanno `OnlyShowIn=LXQt;`: senza il token `LXQt` la sessione è **viva con lo schermo nero e zero messaggi** |
| `XDG_SESSION_TYPE` | `wayland` | non è cosmetica: il pannello sceglie il backend da lì, **non** da `platformName()` (`:206-209`) |
| ⭐ `QT_QPA_PLATFORM` | **`wayland` secco** | **[✗]** nessun componente LXQt la imposta. Con la lista `wayland;xcb` Qt prende «il primo che carica» con **un solo `qCWarning`**; con un elemento solo, se il plugin manca si arriva a `qFatal`. È `LEZIONI.md` §1.8 chiusa a codice |
| `XDG_CONFIG_DIRS` | **deve contenere `/usr/share`** | i default LXQt stanno in `/usr/share/lxqt/*.conf`. Col default Debian non si trovano — e spariscono **in silenzio** |
| `XDG_MENU_PREFIX` | `lxqt-` | **[✗] nessun ripiego cablato** in libqtxdg, a differenza di garcon su XFCE. ✅ Ma il file `/etc/xdg/menus/lxqt-applications.menu` **esiste** in `lxqt-menu-data` **[R-pkg]** |
| `LABWC_UPDATE_ACTIVATION_ENV` | `1` | come su XFCE: su backend headless labwc **non propaga** `WAYLAND_DISPLAY` al bus |
| `XCURSOR_THEME` (+ `XCURSOR_SIZE`) | il tema trasparente | §6.1 |
| ⛔ **da NON passare** | `DISPLAY`, `WAYLAND_DISPLAY`, `QT_QPA_PLATFORM` ereditate, `SESSION_MANAGER` | vedi sotto |

⛔ **Il ripiego a `xcb` è peggio che su KDE, e non è «un po' peggio»: è un'altra sessione.** Se Qt
sceglie xcb, `lxqt-session` **avvia un secondo window manager**, può aprire un **dialogo modale** di
scelta del WM e bloccare il ciclo eventi **30 secondi** (`lxqtmodman.cpp:82-83`, `:209-214`, `:237`);
smette di filtrare i moduli `X-LXQt-X11-Only`, accende `setxkbmap`, `xrdb`, l'osservatore udev degli
input **e quello DRM che lancia `lxqt-config-monitor -l` a ogni cambio di display** — cioè **un
secondo comandante della risoluzione**.

#### 3.3 Quel che NON serve, e sono tre debiti che non paghiamo

| | |
|---|---|
| ✅ **[✗] nessun `loginctl terminate-session`** | grep su `lxqt-session` e `liblxqt`, con controllo positivo che trova quello di XFCE. **La doppia difesa di §xfce §9.2 non serve** |
| ✅ **[✗] nessuna registrazione client di sessione** | né XSMP né D-Bus: il rischio «ostaggio del logout» pagato su KDE **non esiste**. E il logout non consulta inibitori, non mostra nulla, non si annulla |
| ✅ **[✗] nessun salvataggio di sessione** | la trappola `~/.cache/sessions/…` di XFCE non ha equivalente: non c'è niente da cancellare |
| ✅ **[✗] nessun seat richiesto** | `XDG_SEAT`/`XDG_VTNR`/`libsystemd` assenti dai 17 repository |
| ✅ **[✗] nessun gruppo di priorità** | gli **otto secondi** strutturali di XFCE non hanno equivalente: il tetto «desktop su» può essere corto |
| ✅ **il bus di sessione** | **[✗] `dbus-run-session` non compare da nessuna parte**: si usa `$XDG_RUNTIME_DIR/bus`. ⭐ **La decisione lasciata aperta in §xfce §9.7 qui si chiude da sé** |

⛔ **Ma `lxqt-session` è subreaper** (`procreaper.cpp:56`) e al logout manda `SIGTERM` a tutto ciò che
ha il suo ppid (`:129`, `:191-198`). Noi siamo *sopra* e siamo salvi — **ma nulla di REMOTIX va
avviato sotto `lxqt-session`**, perché ogni orfano gli viene riassegnato.

#### 3.4 ⭐ La prontezza si legge, meglio che sugli altri tre

Segnale **`moduleStateChanged(QString, bool)`** su `org.lxqt.session`, oggetto `/LXQtSession`
(`sessiondbusadaptor.h:53`, `:57`): si aspetta `("lxqt-panel.desktop", true)`.

⚠ Il **nome sul bus** compare nel costruttore (`sessionapplication.cpp:48`), quindi «il nome c'è» **non
significa «desktop su»** — è la stessa distinzione che su KDE ci aveva ingannati.

**Il logout**: servizio, oggetto e interfaccia sono tutti `org.lxqt.session` / `/LXQtSession`.
**[✗] Nessun segnale «sto uscendo»** — la sorveglianza passiva è `SIGCHLD` su labwc (la verità) più
`NameOwnerChanged` (l'anticipo). Per comandarlo: `logout()`, **oppure `SIGTERM` a `lxqt-session`**,
che è la stessa cosa. ⛔ Mai `lxqt-leave --logout`: apre una conferma modale.

#### 3.5 ⚠ Tre finestre modali possono fermare una sessione non presidiata

1. `QMessageBox` se `dbus-update-activation-environment` non parte in 2 s (`sessionapplication.cpp:81-84`);
2. «Crash Report» dopo 5 crash in 60 s (`lxqtmodman.cpp:330`);
3. ⛔ **il caso peggiore**: `compositor=` vuoto — **che è il default di serie** — fa avviare
   `lxqt-config-session` invece del desktop. Socket, global, cattura e input sarebbero **tutti
   verdi**, e sullo schermo ci sarebbe un wizard di configurazione.

⭐ **Da cui il controllo di prontezza va fatto sul bus, non sui pixel**: `org.lxqt.session` + il
segnale del pannello. È la lezione §2.2 — *un banco che conta non basta* — in forma preventiva.

---

### 4. Il compositore: la matrice, e perché non c'è codice nuovo

*Dettaglio: `rapporti/02-compositori-matrice.md`.*

LXQt dichiara **sette** compositori (`lxqt-wayland-session/README.md:5-14`); **Trixie ne pacchettizza
quattro**: labwc 0.8.3, kwin-wayland 6.3.6, wayfire 0.9.0, sway 1.10.1. Hyprland, niri e river
**[✗]** non ci sono.

| | labwc / sway / wayfire | kwin_wayland 6.3.6 |
|---|---|---|
| **Cattura** | `zwlr_screencopy` v3 | `zkde_screencast` v5 |
| **Permesso** | **nessuno** | `.desktop` + `X-KDE-Wayland-Interfaces` |
| **Input** | `zwlr_virtual_pointer` v2 + `zwp_virtual_keyboard` v1 | libei (EIS su D-Bus) |
| **Appunti** | `zwlr_data_control` **v2** | `zwlr_data_control` **v2** ✅ |
| **Ridimensionamento** | `set_custom_mode`, **senza tetto** | ⛔ misura **fissa** con `--virtual` |

**Una riga su otto in comune fra le due famiglie** — ed è la clipboard, cioè il file che avevamo già.

⭐ **Verdetto: codice nuovo zero, per tutti e quattro.** Sei compositori su sette ricadono sul modulo
wlroots della fase XFCE; il settimo sul modulo KDE.

**Sul caso KWin**, che sarebbe «niente da scrivere»: l'affermazione **regge ma non conviene**, per
quattro riserve — lo script di LXQt pianta `XDG_MENU_PREFIX=lxqt-` e il ramo KWin **non lo corregge**
(`startlxqtwayland.in:66`, `:125-142`), il che secondo §kde §3.3-bis potrebbe lasciare vuoto
l'indice dei servizi e **chiudere il cancello del permesso** [?, da misurare — ⚠ e una seconda lettura
la capovolge: `/etc/xdg/menus/lxqt-applications.menu` **esiste** in `lxqt-menu-data` **[R-pkg]**,
quindi l'indice **dovrebbe** costruirsi]; si eredita la **misura fissa** che labwc non ha; serve
comunque il nostro `.desktop`; e KWin senza Plasma non è mai stato misurato.

⭐ **La scelta indicata è labwc**: è il ripiego di LXQt stesso, il primo nel `Depends` upstream,
ha il ridimensionamento senza tetto e nessun permesso.

#### 4.1 ⭐ La matrice, e il numero che cambia il senso della fase

Se un desktop non implica più un compositore, il prodotto non ha «cinque desktop»: ha una **matrice**.

| | |
|---|---|
| combinazioni realistiche su Trixie | **9** |
| coperte oggi | **2** (22 %) |
| coperte **gratis** dalla sola fase wlroots | **+5** |
| **totale dopo la fase wlroots** | ⭐ **8 su 9 — l'89 %** |

**E LXQt ne porta quattro, tutte gratis.** ⚠ Riserva: wayfire vendorizza wlroots **0.17**, quindi il
suo «gratis» è **[?]** finché non si legge quella versione.

#### 4.2 Il rilevamento: non chiedere al desktop, guardare i global

`XDG_CURRENT_DESKTOP` **si scrive e non si legge**: lo script di LXQt la costruisce in **tre forme
diverse** nello stesso file, dice `wlroots` anche per compositori che non lo sono, e sbaglia già le
maiuscole in casa propria.

⭐ **Il criterio solido è enumerare i global** con un `wl_display_roundtrip` sul registry: non c'è
ambiguità, perché `zwlr_screencopy_manager_v1` e `zkde_screencast_unstable_v1` sono **mutuamente
esclusivi** su tutta Trixie. Costa zero righe nuove — la connessione al registry esiste già in
`kwin.c:451-495` — e serve anche un compositore fuori elenco.

---

### 5. Che cosa si riusa senza toccare niente

| | |
|---|---|
| **Cattura** | `zwlr_screencopy` su labwc: §xfce §4 **integrale** |
| **Input** | `virtual-keyboard` + `virtual-pointer`: §xfce §7 **integrale**, comprese le cinque trappole |
| **Appunti** | ✅ **`appunti_wlr.c` così com'è**, e la riserva di §xfce §8 **cade**: `kwin_display_apri` **non filtra il socket per nome** (`src/kwin.c:451-484`) — prende `WAYLAND_DISPLAY` e in mancanza prova `wayland-0`…`wayland-9` |
| **Ridimensionamento** | `set_custom_mode`: **integrale, e più facile che su XFCE** (§7) |
| **Audio** | il percorso PipeWire non dipende dal desktop |

⭐ **Le scorciatoie non ci disturbano**: `lxqt-globalkeys` **[✗] non gira affatto su Wayland** — non è
il caso ambiguo del demone che ingoia i tasti senza usarli: `lxqt-session` **lo salta per
costruzione** (`X-LXQt-X11-Only=true` + `lxqtmodman.cpp:106-112`), ed è Xlib puro, **zero rami
Wayland in 3 414 righe** (controllo positivo: 60+ righe X11). Tutti i suoi clienti passano da lui via
D-Bus, quindi sono morti anche loro.

⛔ **Restano le keybind del compositore**, che sono un elenco **completo** in un file che scriviamo
noi — e `W-l → lxqt-leave --lockscreen` è fra quelle di serie (`rc.xml:295-297`): va tolta, o labwc
mangia il tasto comunque (§xfce §7.5).

⚠ **Due dettagli dell'input che LXQt aggiunge:**

1. **NumLock parte spento** (`enableNumlock()` è dietro il cancello X11, e `<numlock>` è commentato in
   `rc.xml`): il tastierino esce in modalità frecce. Rimedio nostro, mettendolo in `mods_locked`;
2. la **disposizione di tastiera**: `lxqt-config-input` **si rifiuta di partire su Wayland**, e nel
   codice c'è un `// FIXME: how to set keyboard layout in Wayland?`. L'unica via è
   `XKB_DEFAULT_LAYOUT` letta da labwc, e **[✗] nessuno legge `/etc/vconsole.conf`** su Trixie: **la
   scriviamo noi, o esce `us`**;
3. ✅ la **ripetizione** la decide labwc (25 Hz / 600 ms) e la applica **esplicitamente anche alle
   tastiere virtuali**: il `[Keyboard]` di LXQt **[✗] non raggiunge il compositore**. Nulla da fare;
4. ⚠ ma `wheelScrollLines=3` in `lxqt.conf [Qt]` è applicato **da Qt dentro ogni applicazione**: un
   nostro scatto diventa **tre righe**. La manopola è lì, non nel nostro accumulatore.

---

### 6. Che cosa si adatta

#### 6.1 ⭐ Il cursore: la cura c'è, ma il canale è un altro

**La buona notizia**: su labwc il cursore delle applicazioni **Qt** lo disegna **il compositore**.
labwc espone `wp_cursor_shape_manager_v1` e Qt 6.8 lo usa **prima** di caricare qualunque tema
(`qwaylandinputdevice.cpp:230-236`), e su `set_shape` labwc usa il proprio `xcursor_manager`, cioè il
tema di **`XCURSOR_THEME`**. ⇒ **una leva sola copre compositore e client Qt.**

⛔ **Le tre trappole, tutte pagate altrove in forma diversa:**

| | |
|---|---|
| `session.conf [Environment]` **non serve** | su Wayland labwc è il **padre**: le variabili di `lxqt-session` arrivano troppo tardi. E LXQt **rimuove apposta** `XCURSOR_THEME` da lì (`selectwnd.cpp:188-192`) |
| `~/.icons/default/index.theme` | `lxqt-config-appearance` vi scrive `Inherits=<tema>`, ed è **il ripiego di Xcursor**: se il nostro tema 1×1 non carica, ricompare un cursore visibile da lì |
| il ripiego di Qt sull'hint del tema | fuori da labwc, Qt legge **solo** `QPlatformTheme::MouseCursorTheme`, che `lxqt-qtplugin` prende da `session.conf [Mouse]` — con un **`cursor_size` 16 cablato** che scavalca `XCURSOR_SIZE`. ⇒ impostare **anche** quella chiave, che costa una riga |

✅ E una differenza a nostro favore rispetto a wlroots: se il tema fallisce **lato Qt**, Qt **non**
ripiega su un tema visibile (`qwaylanddisplay.cpp:1054-1064`). Il ripiego visibile resta solo quello
di wlroots, già noto.

#### 6.2 ⛔ Energia e blocco: nessuna delle leve già pagate funziona qui

| Leva pagata altrove | Su LXQt |
|---|---|
| `AddInhibition` di powerdevil (KDE) | **[✗]** non esiste |
| `PowerManagement.Inhibit` (XFCE) | **[✗]** LXQt non lo espone né lo consuma: **zero occorrenze**. La domanda «il servizio ha attivazione D-Bus?» **non si pone: non c'è servizio** |
| `LockCommand=/bin/false` (XFCE) | ⛔ **qui apre una `QMessageBox` modale**: un'uscita ≠ 0 chiama `reportLockProcessError()`. Le sole scelte sicure sono **chiave assente/vuota** o **`/bin/true`** |
| KIOSK (KDE) | **[✗]** non esiste |

✅ **Ma il pericolo è molto minore, perché LXQt su Wayland è quasi disarmato:**

- **[✗] `lxqt-powermanagement` non ha alcuna leva che spenga un output**: l'unica che conosce è DPMS
  via XCB, chiusa dentro due `if (platformName()=="xcb")` **senza ramo `else`**;
- **[✗] il server non si addormenta**: le azioni di inattività valgono `-1` (niente) e `doAction(-1)` è
  un ramo vuoto;
- **[✗] «Cambia utente» non esiste in LXQt** (grep con controllo positivo): **metà del requisito è già
  soddisfatta dal desktop**;
- ✅ il blocco schermo **è già inerte**: `lock_command_wayland` è letta **senza default** e nessun file
  spedito la imposta.

⛔ **Restano due pericoli veri, e il primo non è di LXQt:**

1. **l'autostart che LXQt propone per labwc** lancia `swayidle -w timeout 300 "wlopm --off *"` — e
   `~/.config/labwc/` viene copiato **una volta sola** (`if [ ! -d … ]`), quindi una configurazione
   sbagliata è **permanente**;
2. ⛔ **se un locker è installato, il blocco riesce davvero**, perché labwc implementa
   `ext-session-lock-v1`. **Requisito nuovo: nessun `swaylock`/`waylock`/`hyprlock` nell'immagine.**

⭐ **E c'è una leva che non dipende dal desktop, ed è la migliore**: labwc crea
`zwp_idle_inhibit_manager_v1` **incondizionatamente** (`idle.c:81`), e un inibitore fa
`wlr_idle_notifier_v1_set_inhibited(true)`, che **disarma ogni timer `ext-idle-notify`**. Cioè
spegniamo il sorvegliante alla fonte, **qualunque cosa dica la configurazione di LXQt**, senza
chiedere niente a nessuno. ⛔ Non ferma però un `set_mode(OFF)` diretto: la cura di wayvnc
(riaccendere prima di catturare) resta.

⚠ **E una trappola di configurazione che è pura `LEZIONI.md` §1.9**: scrivere
`enableIdlenessWatcher=false` **non basta** — il demone lo **riscrive a `true`** al primo avvio
(`powermanagementd.cpp:112-113`). Serve **anche** `runCheckLevel=1`.

#### 6.3 Le voci pericolose

**[✗] Nessun KIOSK, nessun `locked=`**: le voci vanno **tolte**, non bloccate. Tre leve, tutte senza
patch:

1. `.desktop` omonimi con `Hidden=true`/`NoDisplay=true` in `$XDG_DATA_HOME/applications/` per i sette
   file di `lxqt-leave`;
2. **togliere `fancymenu`** dalla chiave `plugins` di `panel.conf` — è il pulsante «Leave», ed è
   **incondizionato, senza chiave, cliccabile anche a menu non caricato** — o sostituirlo con
   `mainmenu`, che in 2.1.4 non ha voci di energia;
3. polkit `no` su logind, che **grigia** Suspend/Hibernate/Shutdown. ⛔ Eccezione: **«Lock screen» non
   è mai grigiata** — non esiste una `canLock()`.

⛔ **E il default Debian ha già una voce pericolosa di serie**: `lxqt-branding-debian` spedisce un
`/etc/xdg/lxqt/panel.conf` con **`lxqt-leave.desktop` fissato nel quicklaunch** **[R-pkg]**.

⚠ `lxqt-policykit-agent` **parte anche su Wayland** e fa `show()` + `activateWindow()`: un dialogo di
autenticazione in una sessione non presidiata. È **[?] una decisione dell'utente**, per coerenza con
il giudizio dato su KDE («le operazioni privilegiate nel terminale funzionano»).

✅ Le **notifiche** non rubano il fuoco (`KeyboardInteractivityNone`) e si zittiscono con
`doNotDisturb=true`. ⛔ Ma `lxqt-leave` usa `KeyboardInteractivityExclusive`: **mentre è aperto,
grabba la tastiera in esclusiva**.

---

### 7. ✅ Il ridimensionamento a caldo: qui siamo l'unico comandante

*È la voce in cui LXQt è **migliore** di tutti e tre i desktop precedenti.*

| | |
|---|---|
| **[✗] nessun componente parla `zwlr_output_manager_v1`** | 2 sole righe in tutto l'albero, e sono stringhe che consigliano `kanshi` |
| `lxqt-config-monitor` passa da **KScreen** | che su Wayland sceglie il backend KWayland, il quale pretende i protocolli **di KWin** — **[✗] assenti in labwc**. `isReady()` falso ⇒ plugin scartato |
| l'unico effetto visibile | un `QMessageBox` «Platform Unsupported… use kanshi» + `exit(1)` — **ma solo se l'utente apre a mano lo strumento**. Si nasconde con un `.desktop` omonimo `NoDisplay=true` |
| il sorvegliante DRM che rilancerebbe lo strumento | è dentro `if (isX11)`: **inerte** |
| ⛔ **da non fare** | impostare `KSCREEN_BACKEND=QScreen`: il backend è valido ma **di sola lettura**, e `setConfig` **ritorna successo** — cioè un «Applica» che non applica |

**E la catena Qt regge, verificata riga per riga**: wlroots manda `logical_size` + `done`, Qt emette
`handleScreenGeometryChange`, e ⭐ **`QWaylandWindow::reset()` ha quattro soli chiamanti, e la
geometria non è fra questi**: niente ricreazione di superfici, niente sfarfallio, niente finestra
nera. Le finestre le riposiziona **labwc**, che ricorda la geometria precedente; il pannello ascolta
`QScreen::geometryChanged` e si rimette a posto.

⛔ **Ma il divieto di §xfce §6.1 si rafforza**: **distruggere** l'output fa montare a Qt un
`QPlatformPlaceholderScreen` — e vale per **tutte** le applicazioni, non solo per i pezzi del
desktop. Si ridimensiona; non si distrugge.

⚠ Una sola riserva, **[?] da misurare**: che labwc generi davvero un `output_layout.change` sul
`set_custom_mode`, che è ciò che fa partire tutta la catena. E un difetto dichiarato upstream
(`lxqt-panel#2432`) dice che **il pannello non segue il resize**: è il primo difetto che l'utente
vedrebbe.

✅ **Scala e DPI: nessuna trappola.** LXQt **[✗]** non gestisce il DPI; a `scale=1` il testo è 1:1 e
il `physical_size` 0×0 del nostro output headless è irrilevante, perché Qt su Wayland restituisce
**96 dpi fissi**. A 4K il testo è nitido ma **piccolo**: la leva pulita è il **font** in
`lxqt.conf [Qt]`, non `QT_SCALE_FACTOR` (che non tocca GTK).

✅ **Le decorazioni**: una barra sola e nessun lampo — Qt manda `unset_mode`, labwc decide per
`rc.xml`, e LXQt spedisce `<decoration>server</decoration>`. **Non toccare né quella chiave né
`QT_WAYLAND_DISABLE_WINDOWDECORATION`.**

---

### 8. Gli appunti, e il coinquilino

*Dettaglio: `rapporti/06-appunti-qt.md`.*

✅ **`appunti_wlr.c` funziona così com'è, su labwc e su KWin.** La riserva aperta da §xfce §8 è
chiusa **in positivo**.

⚠ **Ma LXQt ha un coinquilino che XFCE non aveva: `qlipper`**, che il metapacchetto `lxqt` tira come
dipendenza (`qlipper | clipit | xfce4-clipman`) e `lxqt-core` raccomanda. Si autoavvia da
`/etc/xdg/autostart/`, **non** ha `X-LXQt-X11-Only`, e **rimette l'ultimo elemento quando la clipboard
si svuota** — come klipper, ma **senza marcatura e senza tetto di frequenza** (klipper almeno aveva
10/s).

⭐ **Su Wayland è quasi inerte, e il «quasi» dipende da un `Recommends`**: qlipper è Qt5 e usa solo
`QClipboard`, quindi senza fuoco non vede e non scrive. **Ma** in un'immagine costruita con
`--no-install-recommends` il plugin `qtwayland5` manca, qlipper ripiega su xcb, e **via Xwayland
rinasce coinquilino pieno**. ⚠ **Il banco deve dichiarare quale dei due casi sta misurando** — è
esattamente la forma della lezione §2.3-bis.

**Tre cose su Qt6 che cambiano il nostro codice della clipboard:**

| | |
|---|---|
| ⛔ **mai `text/markdown` in testa** | Qt6 **incolla markdown** se è il primo formato offerto (`qwidgettextcontrol.cpp:2721-2726`) |
| `text/plain;charset=utf-8` | è presentato all'applicazione **come `text/plain`**: offriamo solo l'UTF-8 |
| ⚠ **il tetto di lettura di Qt è 1 secondo** | contro i nostri 5: su rete lenta l'utente vede **un incolla muto** mentre il nostro registro dichiara un trasferimento riuscito. È la lezione §1.7 — *si verifica dal lato che deve ricevere* |

✅ **La primary selection si può ignorare** (un solo uso in tutto l'albero, e **[✗]** nessuna
configurazione che la unisca alla clipboard). ✅ Il ponte **Xwayland** è identico a XFCE, gratis nelle
due direzioni. ✅ E su LXQt+KWin **klipper non c'è**: il suo `.desktop` è `Exec=/usr/bin/false`, è una
libreria di plasmashell.

---

### 9. La configurazione: dove si scrive, e la tensione da chiudere sul banco

⛔ **`LXQt::Settings` scrive nella casa dell'utente alla sola costruzione** (`__userfile__=true` +
`sync()`, `lxqtsettings.cpp:53-59`), e **[✗] non esiste** né un `SystemScope` né un equivalente del
`locked=` di xfconf. ✅ In compenso c'è un `QFileSystemWatcher`: a differenza di `xfconfd`, LXQt
**rilegge a caldo**.

> #### ⚠ Una tensione fra i rapporti, lasciata aperta di proposito
>
> | Chi | Che cosa dice |
> |---|---|
> | `rapporti/03` | i default di sistema in **`/etc/xdg/lxqt/*.conf`** funzionano: `QSettings("lxqt", modulo)` fa fallback chiave-per-chiave, **ed è il meccanismo con cui Debian personalizza LXQt** (`lxqt-branding-debian`) |
> | `rapporti/04` e `rapporti/05` | il percorso di sistema è **uno solo**, quello fissato alla compilazione di Qt, e i file LXQt sono installati in **`/usr/share/lxqt/`** — quindi serve `XDG_CONFIG_DIRS`, e l'unica via sicura è un **`XDG_CONFIG_HOME` effimero** |
>
> **Le due cose possono coesistere** — `QSettings` legge `XDG_CONFIG_DIRS`, il cui default è
> `/etc/xdg`, e Debian può installare in tutti e due i posti. ⛔ **Ma quale percorso vinca sulla
> nostra macchina è una misura, non una lettura**, ed è di quelle che se date per scontate costano un
> pomeriggio: è precisamente la forma di `LEZIONI.md` §1.9. **Misura M6.**

⭐ **Il menu ha lo stesso difetto di garcon, aggravato**: se il file `.menu` non esiste,
`addWatchPath()` non viene **mai** chiamato ⇒ menu morto **per la vita del processo**, il plugin non
ritenta, e all'utente remoto arriva un **`QMessageBox` modale** durante l'avvio del pannello. ✅ Ma
**[✗] nessuna cache su disco** (`USE_MENU_CACHE=OFF`) — il difetto di KDE, l'indice costruito vuoto
che resta vuoto, **qui non può succedere sul disco**; e **[✗]** il difetto dei sottomenu di XFCE non
c'è, perché le directory non sono mai filtrate sull'ambiente.

⚠ **Due dipendenze fragili da tenere d'occhio**: `qt6-wayland` è solo un `Recommends` di `libqt6gui6`
— e **la libreria** `libqt6waylandclient6` è invece dipendenza dura di `lxqt-panel`, quindi **si può
avere la libreria senza il plugin, con apt contento**; e `lxqt-qtplugin` dipende da
`qt6-base-private-abi (= 6.8.2)`, **uguaglianza esatta**: un aggiornamento di Qt lo spegne, e la
sessione parte lo stesso **con un altro aspetto**.

---

### 10. Il piano di misure

*Le prime due decidono se la fase esiste; le altre sono nell'ordine in cui mordono.*

| # | La misura | Perché è lì |
|---|---|---|
| **M1** | ⭐ una sessione LXQt-Wayland **composta a mano** parte davvero: `labwc -S lxqt-session` + le sei variabili di §3.2 | è la voce «da scrivere», e su Trixie non ha precedenti: nessuno l'ha mai installata da pacchetto |
| **M2** | il controllo di prontezza è **sul bus** (`org.lxqt.session` + `moduleStateChanged`) e distingue il desktop dal **wizard** di §3.5 | il caso in cui tutto è verde e sullo schermo c'è un'altra cosa |
| **M3** | ⭐ `set_custom_mode` a cattura viva: pannello, scrivania e applicazioni Qt seguono? | §7, e il difetto `lxqt-panel#2432` dice di no |
| **M4** | il tema del cursore trasparente copre **compositore e client Qt**, e `~/.icons/default/index.theme` non lo scavalca | §6.1: tre canali, e basta che uno resti aperto |
| **M5** | l'inibizione `zwp_idle_inhibit` regge, e **nessuno** spegne l'output in 10 minuti | §6.2, autostart compreso |
| **M6** | ⭐ **quale percorso di configurazione vince**: `/etc/xdg/lxqt/` o `/usr/share/lxqt/` — e ogni valore scritto **si rilegge** | il riquadro di §9, e la lezione §1.9 |
| **M7** | `appunti_wlr.c` contro labwc, **con e senza** qlipper vivo | §8: due casi, e vanno dichiarati entrambi |
| **M8** | prova **guasta di proposito**: `XDG_CURRENT_DESKTOP` sbagliata, e poi `DISPLAY` ereditata | ⭐ imparare **come si legge il guasto** prima di incontrarlo sull'utente. Sono i due difetti che danno «sessione viva e inerte» con un solo `qWarning` |

---

### 11. Le lezioni che questo desktop aggiunge

1. ⭐ **Manca un passo zero-bis alla ricetta**: *«questo desktop, su questa distribuzione, ha una
   sessione Wayland?»* — due comandi (`apt-cache policy`, e cercare in `/usr/share/wayland-sessions/`).
   Qui avrebbero cambiato la fase **prima che cominciasse**, e invece l'abbiamo scoperto al secondo
   rapporto su dieci. Il passo zero esistente chiede *«chi lo fa al mondo?»*; questo chiede **«esiste
   sulla macchina che abbiamo?»**, ed è più a monte.
2. ⭐ **E una domanda 0 alle quattordici**: *«questo desktop ha un compositore, o ne ha un elenco?»*
   Per Mutter, KWin e labwc la risposta era una sola; per LXQt sono **sette**, e cambia la forma della
   risposta a tutte le altre — perché le domande vanno fatte al compositore, non al desktop.
3. ⚠ **Un pacchetto assente non è una funzionalità assente.** Il codice Wayland di LXQt è compilato e
   spedito: manca **il lanciatore**. Se avessimo dedotto «LXQt non fa Wayland» dal `apt-cache policy`
   avremmo saltato un desktop che invece è **il più facile dei quattro**.
4. ⚠ **La versione clonata va confrontata con quella installata, sempre.** Il nostro
   `lxqt-wayland-session` è **0.4.1** e richiede LXQt 2.4: si stava per studiare codice che su Trixie
   non gira. Per gli altri sedici repository le versioni coincidono, e questo è l'unico che avrebbe
   mentito.
5. ⭐ **Il quarto desktop conferma che l'asse giusto è il compositore, non il desktop** — che
   `SPECIFICA.md` §3.8 diceva già, ma ora ha un numero: **8 combinazioni su 9 coperte dopo la sola
   fase wlroots**, e quattro di quelle le porta LXQt senza una riga.


<a id="cinnamon"></a>

## Cinnamon e Muffin — studio del codice, per il quinto desktop

*Scritto il 9 agosto 2026, su `muffin` e `cinnamon` **6.7.4** (cloni del giorno stesso).*

> ### ⛔ Tutto quel che segue è `[R]`. Nulla è misurato.
>
> Questo studio è stato fatto **leggendo il codice**, e vale quel che vale una lettura: dice che
> cosa il compositore *può* fare, non che cosa *fa* sulla nostra macchina. È la lezione che
> `LEZIONI.md` §1.11 e il riquadro di §3 hanno già pagato su KDE — dove la lettura diceva GPU e
> la prima misura diceva software, e ad avere ragione era il codice **ma solo dopo che la misura
> era stata rifatta**.
>
> Le ricerche negative di questo documento (*«X non esiste»*) sono state fatte con lo strumento
> **certificato su Mutter prima dell'uso**: la prima ricerca cercava in `src/`, non trovava
> `RecordVirtual` nemmeno in Mutter — dove c'è — perché Mutter recente tiene gli XML in
> `data/dbus-interfaces/`. Con il percorso corretto il controllo positivo passa, e solo allora
> l'assenza su Muffin significa qualcosa. È `LEZIONI.md` §1.9, presa sul fatto.

---

### 1. In due minuti

**Cinnamon sta a Muffin esattamente come gnome-shell sta a Mutter**: il binario `cinnamon` *è* il
compositore — chiama `meta_get_option_context()`, `meta_plugin_manager_set_plugin_type()`,
`meta_init()` e `meta_run()` (`cinnamon/src/main.c:327-418`). Non è un'analogia: è la stessa
architettura, con i nomi cambiati.

Da cui la buona notizia e la cattiva, che sono la stessa cosa vista da due lati.

⭐ **La buona**: metà di §gnome si trasferisce senza tradurre. `org.cinnamon.Muffin.ScreenCast`
e `org.cinnamon.Muffin.RemoteDesktop` sono le interfacce di Mutter rinominate, la cattura passa da
PipeWire come là, e **non c'è nessun cancello sul permesso** — `check_permission()` verifica solo
che chi chiama sia lo stesso che ha creato la sessione (`meta-screen-cast-session.c:196-201`),
esattamente come Mutter e al contrario di KWin.

⛔ **La cattiva**: il fork si è staccato dal *backend* di Mutter parecchi anni fa, e tre cose che
REMOTIX dà per acquisite **non ci sono affatto**.

| Cerchiamo | In Mutter | In Muffin 6.7.4 |
|---|---|---|
| `RecordVirtual` — creare uno schermo virtuale | ✅ `data/dbus-interfaces/…ScreenCast.xml` | ⛔ **0 file** su tutto l'albero |
| `virtual_monitor` — il monitor virtuale nel backend | ✅ 22 occorrenze in `meta-monitor-manager.c` | ⛔ **0 file** |
| `ConnectToEIS` — l'input via libei | ✅ `…RemoteDesktop.xml`, `…InputCapture.xml` | ⛔ **0 file** |
| `EnableClipboard` — gli appunti della sessione remota | ✅ `…RemoteDesktop.xml` | ⛔ **0 file** |
| un backend *headless* | ✅ modo del backend nativo | ⛔ `headless` compare **solo in `src/tests/`** |

E il paradosso che spiega tutto: **i protocolli Wayland di Muffin sono aggiornatissimi** —
`cursor-shape`, `single-pixel-buffer`, `xdg-dialog`, `xdg-toplevel-icon`, `xdg-toplevel-tag`,
`pointer-warp`, roba del 2024-2025. Mint tiene il passo sul lato *client* di Wayland e **non ha
mai portato l'evoluzione del backend remoto di Mutter**. Il risultato è un compositore moderno
con un'API di desktop remoto ferma a circa Mutter 41.

**Il verdetto provvisorio**: Cinnamon non è escluso, ma **non è servibile con il codice che
abbiamo**, e la sua fattibilità dipende da una misura sola, descritta in §3.3. Finché quella non
è fatta, ogni giudizio è `[?]`.

---

### 2. La mappa

| Dove | Che cosa |
|---|---|
| `muffin/src/backends/` | la parte che ci interessa, gemella di quella di Mutter |
| `muffin/src/org.cinnamon.Muffin.{ScreenCast,RemoteDesktop,DisplayConfig,IdleMonitor}.xml` | le interfacce D-Bus — ⚠ ancora in `src/`, mentre Mutter le ha spostate in `data/dbus-interfaces/` |
| `muffin/src/backends/meta-monitor-manager-dummy.c` | ⭐ **il pezzo che decide tutto**, vedi §3 |
| `muffin/src/backends/native/` | il backend KMS |
| `muffin/src/backends/x11/nested/` | il backend annidato in X11 |
| `cinnamon/src/main.c` | il plugin che *è* il desktop |
| `cinnamon/cinnamon-wayland.session.in` | la sessione |

---

### 3. ⛔ La domanda che decide: lo schermo virtuale

È la domanda 5 di `LEZIONI.md` §3, ed è quella che su KDE è costata più di tutte.

#### 3.1 La via di Mutter non esiste

`org.cinnamon.Muffin.ScreenCast` espone **due soli metodi di registrazione**:

```
RecordMonitor (connector, properties) → stream_path
RecordWindow  (properties)            → stream_path
```

Niente `RecordVirtual`, niente `RecordArea`. E non è un XML rimasto indietro rispetto al codice:
`virtual_monitor` non compare in **nessun file** dell'albero, XML compresi.

Quindi la strada di `gnome-remote-desktop` — *creo uno schermo che non esiste e ci catturo sopra*
— su Cinnamon **non c'è**.

#### 3.2 I tre backend, e perché nessuno è headless

`calculate_compositor_configuration()` (`muffin/src/core/main.c:434-496`) ne sceglie uno di tre:

| Opzione | Backend | Che cosa serve |
|---|---|---|
| `--wayland` / `--display-server` | `META_TYPE_BACKEND_NATIVE` | un dispositivo DRM con un'uscita **vera** |
| `--nested` | `META_TYPE_BACKEND_X11_NESTED` | un server X in cui annidarsi |
| (nessuna) | X11 compositing manager | un server X |

**Non esiste `--headless` e non esiste `--virtual-monitor`.** Il backend nativo non ha nemmeno
l'enumerazione dei modi che in Mutter distingue `DEFAULT` da `HEADLESS`.

#### 3.3 ⭐ Ma c'è un monitor fittizio, e due variabili d'ambiente che lo comandano

È il pezzo che salva lo studio, ed è la ragione per cui Cinnamon non va dichiarato fuori scope.

`meta_backend_create_monitor_manager()` (`muffin/src/backends/meta-backend.c:804-812`):

```c
static MetaMonitorManager *
meta_backend_create_monitor_manager (MetaBackend *backend, GError **error)
{
  if (g_getenv ("META_DUMMY_MONITORS"))
    return g_object_new (META_TYPE_MONITOR_MANAGER_DUMMY, NULL);

  return META_BACKEND_GET_CLASS (backend)->create_monitor_manager (backend, error);
}
```

⭐ **Quel controllo sta nella classe base, prima della chiamata virtuale**: `META_DUMMY_MONITORS`
scavalca la scelta di **qualunque** backend, nativo compreso.

E la misura di quello schermo finto si detta da fuori
(`meta-monitor-manager-dummy.c:148-175`, `:403-431`):

| Variabile | Effetto |
|---|---|
| `MUFFIN_DEBUG_DUMMY_MODE_SPECS` | i modi, come `1920x1080@60`, più d'uno separati da `:` |
| `MUFFIN_DEBUG_NUM_DUMMY_MONITORS` | quanti schermi |
| `MUFFIN_DEBUG_DUMMY_MONITOR_SCALES` | le scale |
| `MUFFIN_DEBUG_TILED_DUMMY_MONITORS` | schermi affiancati |

**È l'equivalente funzionale del `--virtual --width W --height H` di KWin**: la misura del desktop
si decide **all'avvio del compositore** e non si cambia più a sessione viva — che è esattamente il
vincolo di KDE, e che il modello della tela di `DECISIONI.md` §5.0 già assorbe.

#### 3.4 ⛔ Le due strade, e quale va misurata per prima

**Strada (A) — nativo + monitor fittizio.** `META_DUMMY_MONITORS=1
MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60 cinnamon --wayland --replace`.
Se regge, Cinnamon gira **senza X e senza monitor**, e il costo per REMOTIX crolla.

⚠ **Ma è precisamente il tipo di deduzione che `LEZIONI.md` §1.11 vieta di dare per buona.** Che
il gestore dei monitor sia finto non dice che il *renderer* lo sia: il backend nativo disegna via
KMS e vuole dei CRTC su cui presentare, e con schermi inventati quei CRTC non ci sono. Può
funzionare, può fallire all'avvio, e **può funzionare consegnando zero fotogrammi** — che è il
modo peggiore, perché sembra riuscito.

**Strada (B) — annidato in Xvfb.** `--nested` usa il monitor fittizio **per costruzione**
(`meta-backend-x11-nested.c:57-60`): è la sua unica implementazione di `create_monitor_manager`.
Quindi la (B) funziona quasi certamente, al prezzo di un server X in più nella pila e,
verosimilmente, di **GL software** (llvmpipe) — cioè il desktop intero disegnato in CPU, che
`LEZIONI.md` §3 domanda 4 considera discriminante per dire se un desktop è servibile su una
macchina da server.

> ### Il piano: si misura (A), e (B) è il ripiego
>
> La (A) è il premio e la (B) è la rete di sicurezza. **La misura si fa nell'ordine
> (A) → (B)**, e la (A) non si dichiara riuscita perché il processo sta in piedi: si dichiara
> riuscita quando `misura-cattura` (in `v1/banchi/banco-compositori/`) conta fotogrammi su una
> scena dichiarata e sempre in movimento. È `LEZIONI.md` §1.1 e §3.2 di `CODER.md`.

---

### 4. La cattura: la parte che funziona

**Pienamente implementata**, e con la stessa struttura di Mutter:
`meta-screen-cast-monitor-stream-src.c`, `meta-screen-cast-window-stream-src.c`,
`handle_record_monitor()` a `meta-screen-cast-session.c:299`.

✅ **Nessun cancello.** `check_permission()` confronta il nome D-Bus di chi chiama con quello che
ha creato la sessione — è un controllo di proprietà, non di autorizzazione. Nessun polkit, nessun
portale, nessun campo in un file `.desktop`. Su questo Cinnamon sta con GNOME e wlroots, **non**
con KDE.

`[?]` **Quel che non si può leggere**: quanti fotogrammi consegna, se il buffer arriva già
disegnato, se il cursore finisce dentro l'immagine, quanto costa la risoluzione. Su Mutter erano
37 al secondo `[M]`; su Muffin **non c'è ragione di supporre lo stesso numero**, perché il
percorso di rendering è quello che è cambiato di più fra i due — ed è esattamente la deduzione
che §1.11 vieta.

---

### 5. L'input: un salto indietro di due anni

`org.cinnamon.Muffin.RemoteDesktop` espone i vecchi metodi di notifica:

```
NotifyKeyboardKeycode · NotifyKeyboardKeysym
NotifyPointerButton · NotifyPointerAxis · NotifyPointerAxisDiscrete
NotifyPointerMotionRelative · NotifyPointerMotionAbsolute
NotifyTouchDown · NotifyTouchMotion · NotifyTouchUp
```

⛔ **Niente `ConnectToEIS`**, quindi **niente libei** — e `v1/remotix-c/src/input.c` (906 righe) è
scritto per libei, deciso il 4 agosto 2025 chiudendo la fase 3 di v1.

Le tre conseguenze:

1. **serve un secondo percorso di input**, quello D-Bus, che v1 aveva scritto *prima* di passare
   a libei e che non è sopravvissuto nel codice attuale;
2. ⭐ **`NotifyKeyboardKeysym` esiste**, e vale la pena notarlo alla luce di `DECISIONI.md`
   §5-bis.6: qui il *simbolo* si può iniettare direttamente, senza cercare quale tasto lo
   produca. Non cambia la decisione — la regola resta «le lettere viaggiano come lettere» — ma su
   Cinnamon il lato server costa meno;
3. ⚠ **e c'è `zwp_virtual_keyboard_v1`** fra i protocolli Wayland, che sarebbe una terza strada.
   `[?]` Da valutare solo se la seconda si rivelasse insufficiente: §0.1 di `DECISIONI.md` dice di
   non collezionare percorsi.

`[?]` **Non letto, e va letto prima di scrivere**: se `NotifyPointerMotionAbsolute` accetti un
riferimento allo *stream* come su Mutter, e come si comporti con il monitor fittizio.

---

### 6. ⛔ Gli appunti: qui la strada non c'è proprio

È il buco peggiore, e non ha un ripiego evidente.

| Via | Su Cinnamon |
|---|---|
| `EnableClipboard` sull'oggetto RemoteDesktop (la via di GNOME) | ⛔ **0 occorrenze**: l'API è precedente all'aggiunta della clipboard in Mutter |
| `zwlr_data_control_manager_v1` (la via di KDE, XFCE e LXQt) | ⛔ **assente** dai protocolli di Muffin |
| `ext_data_control_v1` | ⛔ assente |

Quindi **nessuno dei due file che abbiamo serve**: né `appunti_mutter.c` (450 righe), né
`appunti_wlr.c` (796), che insieme coprono tutti e quattro gli altri desktop.

`[?]` **Le vie residue, tutte da verificare e nessuna gradevole**: fare il client `wl_data_device`
ordinario — ma la clipboard di Wayland richiede il fuoco, e una sessione non presidiata non ce
l'ha; passare da XWayland; o contribuire a monte. **La terza è probabilmente la sola sensata**, ed
è la stessa conclusione a cui §kde §8.2 era arrivato per il ridimensionamento.

⚠ Da mettere in conto nella decisione «Cinnamon dentro o fuori»: `DECISIONI.md` §5-ter mette la
clipboard bidirezionale fra le funzioni promesse. **Su Cinnamon oggi non è servibile.**

---

### 7. Che cosa si trasferisce da §gnome, e che cosa no

| Argomento | Si trasferisce? |
|---|---|
| l'architettura ScreenCast/PipeWire | ✅ **sì, quasi alla lettera** |
| l'assenza di cancello sul permesso | ✅ sì |
| il ciclo di vita della sessione D-Bus | ✅ probabilmente `[?]` |
| **la revoca al blocco schermo** (`inhibit_remote_access`) | `[?]` **da verificare**, ed è importante: se c'è, vale la stessa cura di `DECISIONI.md` §4.3 |
| `RecordVirtual` e il monitor virtuale | ⛔ no, non esistono |
| libei e `ConnectToEIS` | ⛔ no |
| la clipboard | ⛔ no |
| il lockdown via `org.gnome.desktop.lockdown` | `[?]` Cinnamon ha il proprio albero di impostazioni |

---

### 8. Le quattordici domande di `LEZIONI.md` §3, colonna Cinnamon

| # | Domanda | Cinnamon / Muffin 6.7.4 |
|---|---|---|
| 1 | Come si chiede la cattura senza portale? | ✅ D-Bus `org.cinnamon.Muffin.ScreenCast` — gemella di Mutter `[R]` |
| 2 | Spinge i fotogrammi o li fa tirare? | ✅ spinge, PipeWire `[R]` |
| 3 | È dietro un permesso? | ✅ **no** — solo controllo di proprietà `[R]` |
| 4 | Senza monitor, disegna sulla GPU? | ⛔ `[?]` **la domanda che decide** — vedi §3.4. Sulla strada (B) quasi certamente **no** |
| 5 | Si può chiedere uno schermo virtuale della misura voluta? | ⛔ **no** via protocollo; ⭐ **sì** via `META_DUMMY_MONITORS` + `MUFFIN_DEBUG_DUMMY_MODE_SPECS`, all'avvio `[R]` |
| 6 | Quanti fotogrammi consegna? | `[?]` **non deducibile da Mutter** |
| 7 | La cadenza dichiarata come si comporta? | `[?]` |
| 8 | Fotogrammi interi o «diff»? | `[?]` |
| 9 | Il buffer arriva già disegnato? | `[?]` |
| 10 | Che cosa costa la risoluzione? | `[?]` |
| 11 | Che cosa costa la profondità di colore? | `[?]` |
| 12-bis | Il cursore è dentro l'immagine catturata? | `[?]` — e con `DECISIONI.md` §5-bis.2 è **obbligatorio** saperlo |
| 13 | Uno schermo virtuale si ridimensiona a caldo? | ⛔ **no** `[R]`: la misura è nell'ambiente all'avvio, come su KDE |
| 14 | La clipboard di chi è? | ⛔ **di nessuno raggiungibile** — vedi §6 |

**Undici domande su quattordici restano `[?]`**, contro le undici su undici che lo studio di KDE
aveva chiuso leggendo. Non è pigrizia dello studio: è che su KDE le risposte stavano nel codice,
e qui le tre che contano stanno in un'esecuzione.

---

### 9. Il piano di misure, in ordine

Il minimo per decidere «dentro o fuori». Serve una macchina con Cinnamon 6.7 e i banchi di
`v1/banchi/banco-compositori/`.

| # | Che cosa | Come si dichiara riuscita |
|---|---|---|
| **M1** | strada (A): `META_DUMMY_MONITORS=1 MUFFIN_DEBUG_DUMMY_MODE_SPECS=1920x1080@60 cinnamon --wayland` da SSH, senza monitor | il compositore sta in piedi **e** `RecordMonitor` apre uno stream **e** `misura-cattura` conta fotogrammi > 0 su scena in movimento. Tre condizioni, non una |
| **M2** | se M1 fallisce: strada (B), `--nested` dentro Xvfb | idem |
| **M3** | i fotogrammi al secondo consegnati, con scena dichiarata | il numero, confrontabile con Mutter 37 / KWin 60 / wlroots 61 |
| **M4** | rende in GPU o in software? | ⚠ **non** «ha aperto un render node» (§1.11): si guarda il tipo di buffer che lo stream riesce a offrire, **dopo** aver chiesto DMA-BUF |
| **M5** | il cursore è dentro l'immagine? | si guarda un fotogramma |
| **M6** | il blocco schermo revoca la cattura, come su GNOME? | si blocca e si guarda se lo stream muore |

⛔ **M1 non si dichiara riuscita perché il processo non è morto.** È la forma d'errore E1: una
condizione necessaria presa per sufficiente.

---

### 10. Il conto per REMOTIX

**Quel che si riusa**, se M1 o M2 passano: la struttura della cattura (`cattura.c`), il ciclo di
sessione D-Bus, e il modello della tela di `DECISIONI.md` §5.0 — che assorbe già il vincolo
«la misura si decide all'avvio», perché lo assorbiva per KDE.

**Quel che va scritto nuovo**, e non è poco:

| | Costo |
|---|---|
| un `cinnamon.c` accanto a `mutter.c` e `kwin.c` | medio — è Mutter con altri nomi |
| **un secondo percorso di input**, D-Bus invece di libei | ⚠ **alto**: è la fase 4 di v1 rifatta |
| **gli appunti**, che oggi non hanno strada | ⛔ **aperto** — vedi §6 |

**Il giudizio, dichiarato come provvisorio:** Cinnamon è il desktop che costa **più di tutti** fra
i cinque, e le sue due difficoltà — l'input e la clipboard — non sono difficoltà di lettura ma
funzionalità mancanti a monte. Non va dichiarato fuori scope, perché M1 potrebbe cambiare il
conto; ma va messo **ultimo**, dopo che gli altri quattro funzionano, e la decisione va presa
sulle misure di §9 e non su questo documento.

⚠ **E se M1 e M2 fallissero entrambe**, Cinnamon non è servibile affatto — non per una nostra
mancanza, ma perché un compositore che non sa disegnare senza uno schermo non può servire una
sessione remota. In quel caso la voce si chiude, con la misura accanto.


---

# Parte III — Chi fa il nostro stesso mestiere


<a id="gnome-remote-desktop"></a>

## gnome-remote-desktop — studio del codice e delle funzionalità

Analisi condotta sul codice sorgente originale, clonato da `gitlab.gnome.org/GNOME/gnome-remote-desktop`:

- **51.alpha** (commit `038caa60`, 9 luglio 2026) — ramo di sviluppo, usato come riferimento principale
- **48.2** — la versione che accompagna GNOME 48, cioè quella di **Debian Trixie**, la piattaforma di
  runtime di REMOTIX. Le differenze rispetto alla 51 sono in §17

Dimensione: **68 730 righe di C** in ~200 file, più gli XML delle interfacce D-Bus e gli shader.

Perché questo documento esiste: la specifica di REMOTIX cita `gnome-remote-desktop` ogni volta che un
problema si è risolto (§5.4, §5.8, §5.10, questione aperta n.9), e ogni volta lo ha consultato a pezzi.
La lezione di metodo scritta in §5.4 — *«studiare il riferimento viene prima di ipotizzare»* — chiede
che il riferimento sia studiato **una volta sola e per intero**. Il §18 raccoglie il conto: cosa
conferma delle decisioni di REMOTIX, cosa le smentisce, e cosa conviene copiare.

> **E dal 3 agosto 2026 conta molto di più.** Con i vincoli posti dall'utente — **linguaggio C** e
> **FreeRDP 3** (§8-bis di `SPECIFICA.md`) — REMOTIX e `gnome-remote-desktop` condividono linguaggio,
> libreria RDP, compositore e client. Quello che segue non è più materiale di confronto: è codice
> leggibile e, dove serve, trasferibile.

---

### 1. Che cos'è

Il server desktop remoto del progetto GNOME. Non è un desktop e non è un compositore: **parla al
compositore**, esattamente come REMOTIX. Due backend di protocollo, **RDP** (predefinito, su FreeRDP 3)
e **VNC** (opzionale, su LibVNCServer, disattivato di default in build).

I mattoni sono gli stessi che REMOTIX ha scelto: **PipeWire** per i pixel, **libei** per l'input,
**API RemoteDesktop di Mutter** per la gestione di alto livello.

Licenza GPL v2 o successiva. Autori principali: Jonas Ådahl (architettura, sessione) e Pascal Nowack
(tutto il grosso del backend RDP).

---

### 2. I quattro modi di funzionamento

Sono la struttura portante di tutto il programma: un solo eseguibile, quattro `GrdRuntimeMode`
(`grd-daemon.c:1198`), ciascuno con la propria classe di daemon e la propria classe di impostazioni.

| Modo | Opzione | Classe | Bus | A cosa serve |
|---|---|---|---|---|
| `SCREEN_SHARE` | *(nessuna)* | `GrdDaemonUser` | sessione | Assistenza remota: ci si attacca alla sessione già attiva di chi è seduto davanti |
| `HEADLESS` | `--headless` | `GrdDaemonUser` | sessione | Utente singolo, sessione grafica senza schermo avviata a parte |
| `SYSTEM` | `--system` | `GrdDaemonSystem` | **sistema** | Accesso remoto multiutente: fa da portiere davanti a GDM |
| `HANDOVER` | `--handover` | `GrdDaemonHandover` | sessione | Il processo che riceve la connessione consegnata dal modo `SYSTEM` |

Unità systemd corrispondenti: `gnome-remote-desktop.service` (utente, per screen share),
`gnome-remote-desktop-headless.service` (utente), `gnome-remote-desktop.service` (sistema).

**Il modo che assomiglia a REMOTIX è `HEADLESS`**: una sola sessione, un solo utente, il server gira
dentro la sessione. Gli altri tre risolvono problemi che REMOTIX ha messo fuori scope (§4.2 della
specifica: multi-tenancy e amministrazione).

#### 2.1 Il passaggio di consegne con GDM (`SYSTEM` → `HANDOVER`)

È il meccanismo che la specifica di REMOTIX cita in §5.6 come *«quel passaggio esiste perché
gnome-remote-desktop deve agganciarsi alla schermata di accesso»*. Il codice conferma: sta tutto in
`grd-daemon-system.c` (1520 righe) e `grd-daemon-handover.c` (911 righe), ed è la parte più
complicata dell'intero programma.

Come funziona, in breve:

1. il daemon di sistema gira come utente dedicato `gnome-remote-desktop`, sul **bus di sistema**, e
   ascolta sulla 3389;
2. all'arrivo di una connessione **sbircia i primi byte del socket** (`grd-rdp-routing-token.c`)
   cercando il prefisso `Cookie: msts=` del Routing Token, senza consumarli — con un tetto di 2
   secondi;
3. se il token non c'è, è un client nuovo: si autentica contro una credenziale di sistema, e attraverso
   `org.gnome.DisplayManager.RemoteDisplayFactory` chiede a GDM di creare una sessione di accesso;
4. quella sessione avvia un secondo `gnome-remote-desktop --handover`, che espone
   `org.gnome.RemoteDesktop.Rdp.Handover` sul bus di sessione;
5. il daemon di sistema manda al client una **Server Redirection PDU** (`grd_session_rdp_send_server_redirection`)
   con routing token, credenziali e certificato del bersaglio;
6. il client si ricollega, questa volta col token; il daemon di sistema riconosce il token e **passa
   il socket** al processo handover, che serve la sessione.

Il livello di sicurezza del secondo collegamento è **RDSTLS** (`FreeRDP_RdstlsSecurity = TRUE`,
`grd-session-rdp.c:1547`) — cioè proprio quello che xrdp ha in tabella ma non implementa.

Per REMOTIX questo capitolo è **interamente fuori scope**, ma va letto una volta perché spiega perché
il resto del programma è fatto come è fatto.

---

### 3. Architettura dei processi

Un solo eseguibile principale, `gnome-remote-desktop-daemon` (in `libexecdir`), più tre utilità:

| Binario | Ruolo |
|---|---|
| `gnome-remote-desktop-daemon` | Il server vero, in tutti e quattro i modi |
| `grdctl` | Configurazione da riga di comando (gsettings + credenziali) |
| `gnome-remote-desktop-configuration-daemon` | Espone la configurazione su D-Bus per il pannello Impostazioni |
| `gnome-remote-desktop-enable-service` | Abilita l'unità di sistema passando per polkit |

**Nomi sul bus** (`grd-private.h`): `org.gnome.RemoteDesktop.User`, `.Headless`, `.Handover` sul bus
di sessione; `org.gnome.RemoteDesktop` sul bus di sistema.

**Thread** — sono quattro famiglie, e la divisione conta perché è la stessa che REMOTIX ha dovuto
inventarsi (§5.7 regola 7, §5.8 regola 3):

| Thread | Chi lo crea | Cosa fa |
|---|---|---|
| principale (`GMainContext` di default) | GLib | D-Bus, logind, ciclo di vita delle sessioni, layout manager |
| **socket** (uno per sessione RDP) | `grd_session_rdp_new` | `WaitForMultipleObjects` sugli handle FreeRDP, legge il protocollo |
| **grafica** (uno per sessione) | `grd_rdp_renderer_start` | `GMainContext` privato: codifica, invio dei frame EGFX |
| **EGL** (uno per processo) | `GrdContext` | Tutte le operazioni GL/EGL, che devono stare su un thread solo |
| PipeWire (uno per stream) | `pw_context` | Cattura |

Il thread grafico ha un **`GMainContext` proprio** (`renderer->graphics_context`) e tutte le sorgenti
grafiche vi si attaccano esplicitamente. È l'equivalente disciplinato di ciò che REMOTIX ottiene con
i task Tokio.

---

### 4. Dipendenze

Obbligatorie sempre: glib ≥ 2.75, gio, **libpipewire ≥ 1.2**, **libei ≥ 1.3.901**, cairo, libdrm,
epoxy, xkbcommon ≥ 1.0, libnotify, libsecret, **krb5**, **tss2** (TPM 2.0), libsystemd (opzionale ma
necessaria per `SYSTEM`/`HANDOVER`).

Per il backend RDP: **freerdp3 ≥ 3.22**, winpr3, freerdp-server3, **libva** + libva-drm, **vulkan ≥ 1.2**,
**ffnvcodec ≥ 11.1.5** (NVENC), **fdk-aac**, **opus**, **fuse3 ≥ 3.9.1**, polkit ≥ 122, e in build
`glslc` + `spirv-opt` per gli shader SPIR-V.

Da notare per REMOTIX: **niente ffmpeg**, **niente x264**. La codifica è scritta a mano contro libva e
contro l'API NVENC. Vedi §9.

---

### 5. Il ciclo di vita di una sessione — la sequenza esatta

È la parte di maggior valore immediato per REMOTIX, perché è la stessa danza che §5.8 regola 1 della
specifica ha ricostruito a tentativi. Qui c'è la versione del riferimento, letta in
`grd-session.c`.

```
grd_session_start()
 │
 ├─ 1. org.gnome.Mutter.RemoteDesktop.CreateSession()          → percorso sessione
 │
 ├─ 2. Session.ConnectToEIS(options={})                        → fd
 │      └─ ei_new_sender() + ei_setup_backend_fd(fd)
 │         GSource su ei_get_fd(), ei_configure_name("gnome-remote-desktop")
 │
 ├─ 3. connessione dei segnali: "closed", "selection-owner-changed",
 │      "selection-transfer"
 │
 ├─ 4. org.gnome.Mutter.ScreenCast.CreateSession({
 │        "remote-desktop-session-id": <SessionId del passo 1>,
 │        "disable-animations": true })
 │
 ├─ 5. org.gnome.Mutter.RemoteDesktop.Session.Start()      ← ADESSO, non prima
 │
 └─ 6. ScreenCast.Session.RecordVirtual({cursor-mode, is-platform:true})
        └─ Stream proxy → Stream.Start()                   ← il flusso, non la sessione
```

**I due paletti sono identici a quelli che REMOTIX ha pagato** (§5.8 regola 1): la sessione di cattura
si crea dichiarando `remote-desktop-session-id` *prima* di avviare il controllo, e ciò che si avvia
alla fine è lo **Stream**, non la Session di ScreenCast.

Due dettagli che REMOTIX non ha:

- **`disable-animations: true`** nelle opzioni della sessione di cattura. Le animazioni di GNOME su un
  collegamento remoto costano banda e non aggiungono nulla. Una riga, da copiare.
- **`is-platform: true`** in `RecordVirtual`. Dichiara che il monitor virtuale è «di piattaforma»,
  cioè trattato come uno schermo vero dal punto di vista della configurazione monitor.

**La chiusura** è simmetrica e ha lo stesso vincolo: `grd_session_stop` chiama
`RemoteDesktop.Session.Stop`, e la cattura muore con lui. La sessione di ScreenCast **non** viene
fermata direttamente.

**Come si accorge che la sessione è finita**: segnale `closed` sulla sessione di Mutter
(`on_remote_desktop_session_closed`). Non c'è alcuna registrazione presso `gnome-session`: quella è
un'invenzione di REMOTIX (§5.9 di `SPECIFICA.md`, `uscita.rs`), e — dati i tempi misurati là — è
un'invenzione *migliore*, perché il segnale `closed` di Mutter arriva a smontaggio già avviato.

L'unico punto in cui `gnome-remote-desktop` parla con `gnome-session` è
`grd_session_manager_call_logout_sync()` (`grd-daemon-utils.c:207`), e lo fa nella direzione opposta:
chiama `Logout(NO_CONFIRMATION)` per **chiudere** la sessione greeter quando il client se ne va nel
modo handover.

---

### 6. Il percorso RDP

#### 6.1 Cosa il server pretende dal client

In `rdp_peer_capabilities` e `rdp_peer_post_connect` (`grd-session-rdp.c`). Chi non soddisfa una di
queste condizioni **viene disconnesso**:

| Requisito | Riga | Motivo dichiarato nel codice |
|---|---|---|
| **Graphics Pipeline (EGFX)** | 1162 | *"Client did not advertise support for the Graphics Pipeline, closing connection"* |
| **32 bpp** | 1177 | Violazione di protocollo se dichiara codec ma non 32 bit |
| **Desktop resize** | 1193 | *"Client doesn't support desktop resizing"* |
| **Canale DRDYNVC** | 1199 | Senza canali dinamici non c'è EGFX |
| **Pointer cache > 0** | 1286 | *"Client doesn't have a pointer cache"* |
| **Fastpath output** | 1291 | *"Client does not support fastpath output"* |

**Questo è il fatto che più conta per REMOTIX**: il riferimento ha preso *esattamente* la decisione di
§3.7 della specifica — **solo EGFX, nessun ripiego legacy** — e la applica chiudendo la connessione.
La riserva sui client Android («va verificato provandoli») trova qui una risposta indiretta: GNOME
serve gli stessi client Android che REMOTIX ha in elenco, e li serve solo via EGFX.

Due degradazioni interessanti, entrambe sull'audio:

- se il client **non sa fare autodetect di rete**, l'audio in uscita viene **spento**
  (`grd-session-rdp.c:1316`): senza misura della banda, mandare audio peggiora il video;
- se il client è **iOS o Android**, l'audio in uscita viene **spento comunque**
  (`grd-session-rdp.c:1323`), con la motivazione: *«Client cannot handle graphics and audio
  simultaneously»*. Da tenere presente: REMOTIX ha Android fra i client di riferimento **e** l'audio
  AAC in §3.2.

#### 6.2 Come il server configura FreeRDP

Estratto significativo di `init_rdp_session` (`grd-session-rdp.c:1539` e seguenti):

```c
RdpSecurity   = FALSE;      TlsSecurity = FALSE;      NlaSecurity = TRUE;
ColorDepth    = 32;
SupportGraphicsPipeline = TRUE;
GfxAVC444v2   = FALSE;   GfxAVC444 = FALSE;   GfxH264 = FALSE;   /* accesi dopo, in CapsAdvertise */
GfxSmallCache = FALSE;   GfxThinClient = FALSE;
RemoteFxCodec = TRUE;    RemoteFxImageCodec = TRUE;   NSCodec = TRUE;
SurfaceFrameMarkerEnabled = TRUE;   FrameMarkerCommandEnabled = TRUE;
PointerCacheSize = 100;
FastPathOutput = TRUE;   NetworkAutoDetect = TRUE;   RefreshRect = FALSE;
SupportMultitransport = FALSE;                       /* niente UDP */
VCFlags = VCCAPS_COMPR_SC;   VCChunkSize = 16256;
HasExtendedMouseEvent = TRUE;  HasHorizontalWheel = TRUE;  HasRelativeMouseEvent = TRUE;
HasQoeEvent = FALSE;           UnicodeInput = TRUE;
AudioCapture = TRUE;   AudioPlayback = TRUE;   RemoteConsoleAudio = TRUE;
OsMajorType = UNIX;    OsMinorType = PSEUDO_XSERVER;
```

**`NlaSecurity = TRUE` con le altre due a `FALSE` significa che NLA è obbligatorio.** È la divergenza
più grossa rispetto a REMOTIX, che ha scelto TLS puro (§3.6). Vedi §7.

#### 6.3 Riconoscimento del client

`grd_session_rdp_is_client_mstsc()` (`grd-session-rdp.c:251`) riconosce mstsc guardando
`OsMajorType == WINDOWS && OsMinorType == WINDOWS_NT`. Il riferimento quindi **ammette apertamente che
i client vanno distinti**, ed è la conferma della regola dei tre client di §5.7 di `SPECIFICA.md`.

---

### 7. Autenticazione

#### 7.1 NLA obbligatorio, con due meccanismi

`GrdRdpAuthMethods` è un insieme di bandiere (predefinito: `['credentials']`):

- **`credentials`** — NTLM. Il server **fabbrica un file SAM temporaneo** con l'utenza configurata
  (`grd-rdp-sam.c`) e lo passa a FreeRDP come `NtlmSamFile`. Le credenziali non sono quelle di
  sistema: sono una coppia utente/password specifica del desktop remoto, tenuta nel portachiavi;
- **`kerberos`** — richiede un keytab con il principal `TERMSRV`. Dopo l'handshake, `rdp_peer_logon`
  interroga il contesto NLA (`SECPKG_ATTR_AUTH_IDENTITY`), converte il principal in nome locale con
  `krb5_aname_to_localname` e **verifica che l'uid corrisponda a quello del processo**
  (`is_auth_identity_current_user`, `grd-session-rdp.c:991`).

Quest'ultimo controllo è **la stessa regola che REMOTIX ha dovuto scoprire il 3 agosto** — «entra un
solo utente: quello di cui il server serve la sessione», §3.4 di `SPECIFICA.md`. Il riferimento la fa
sull'uid effettivo, esattamente come la nota di REMOTIX prescrive. Con NTLM invece non applica alcuna
politica aggiuntiva (`"Authenticated using NTLM, not applying any additional policy"`) — e non ne ha
bisogno, perché la credenziale NTLM è già specifica di quella sessione.

#### 7.2 Dove stanno le credenziali

Tre implementazioni intercambiabili di `GrdCredentials`:

| Backend | File | Uso |
|---|---|---|
| **libsecret** | `grd-credentials-libsecret.c` | Modo utente: portachiavi GNOME |
| **TPM 2.0** | `grd-credentials-tpm.c` + `grd-tpm.c` (809 righe) | Modo sistema: sigilla il segreto nel TPM |
| **file** | `grd-credentials-file.c` | Ripiego quando non c'è TPM |
| **one-time** | `grd-credentials-one-time.c` | Handover: credenziale usa e getta |

La variante TPM è pensata per il servizio di sistema, che gira senza sessione utente e quindi senza
portachiavi sbloccato.

#### 7.3 TLS

Certificato e chiave si configurano come **percorsi a file PEM** (`tls-cert`, `tls-key`); il server li
legge e li passa a FreeRDP con `freerdp_certificate_new_from_pem` / `freerdp_key_new_from_pem`.
Nessuna generazione automatica: il README rimanda a `winpr-makecert`, `certtool` o `openssl`.
L'impronta del certificato viene esposta su D-Bus (`tls-fingerprint`) perché il pannello Impostazioni
la mostri.

---

### 8. La pipeline grafica EGFX

`grd-rdp-dvc-graphics-pipeline.c`, 2287 righe. È il file che la specifica di REMOTIX cita in §5.4.

#### 8.1 Negoziazione delle capacità

L'elenco delle versioni provate, **in ordine decrescente** (`cap_list`, riga 1567):

```
10.7, 10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 8.1, 8.0
```

Si sceglie la **prima versione dell'elenco che il client dichiara**, e si conferma quella sola con un
`CapsConfirm`. La versione decide se AVC è disponibile:

| Versione | AVC420 | AVC444 |
|---|---|---|
| 10.0 … 10.7 | sì, salvo `RDPGFX_CAPS_FLAG_AVC_DISABLED` | idem |
| 8.1 | solo se `RDPGFX_CAPS_FLAG_AVC420_ENABLED` | no |
| 8.0 | **no** | no |

**È esattamente il difetto che REMOTIX ha pagato** (§5.4: *«elenco delle versioni EGFX troppo rado:
mancava la famiglia 10.x intermedia, e mstsc si ferma alla 10.6»*). Questa tabella è la versione
autorevole: dieci voci, nessun buco.

Altre regole di protocollo applicate:

- **timeout di 10 secondi** (`PROTOCOL_TIMEOUT_MS`) dall'apertura del canale: se non arriva un
  `CapsAdvertise`, la sessione viene chiusa con `ERRINFO_BAD_CAPABILITIES`;
- un `CapsAdvertise` **ripetuto** è lecito solo se la versione iniziale era ≥ 10.3 (è il *protocol
  reset* previsto dalla specifica Microsoft); altrimenti è violazione;
- un `CapsAdvertise` ripetuto che **spegnerebbe AVC** viene rifiutato con chiusura della sessione;
- `CacheImportOffer` riceve una `CacheImportReply` **vuota** — cioè la cache non viene mai usata, come
  in xrdp;
- `QoeFrameAcknowledge` è accettato e ignorato.

#### 8.2 Superfici

`grd_rdp_dvc_graphics_pipeline_acquire_gfx_surface` (riga 439) fa, in quest'ordine:

1. `grd_rdp_gfx_surface_new` → **`CreateSurface`** (formato `GFX_PIXEL_FORMAT_XRGB_8888`);
2. crea il *frame controller*;
3. **`map_surface`** → **`MapSurfaceToOutput`** con `outputOriginX/Y`.

**Le due chiamate sono adiacenti e nessuna delle due è opzionale.** È la conferma diretta della causa
trovata da REMOTIX il 2 agosto (§5.4): creare la superficie e agganciarla all'uscita sono due
operazioni distinte.

L'unico tipo di mappatura implementato è `MAP_TO_OUTPUT`. `MapSurfaceToWindow` e le varianti *scaled*
non esistono, come in xrdp.

**Superficie di rendering separata**: se l'allineamento richiesto dall'encoder non coincide con
l'allineamento a 16, viene creata una *seconda* superficie EGFX, si codifica su quella, e si copia
sulla superficie visibile con `SurfaceToSurface`. È l'unico uso di `SurfaceToSurface` nel programma.

#### 8.3 Allineamento e geometrie — le due convenzioni

Nel percorso NVENC (`refresh_gfx_surface_avc420`, riga 1084):

```c
aligned_width  = surface_width  + (surface_width  % 16 ? 16 - surface_width  % 16 : 0);
aligned_height = surface_height + (surface_height % 64 ? 64 - surface_height % 64 : 0);
```

**Larghezza multipla di 16, altezza multipla di 64** — identico a quanto REMOTIX ha accertato in §5.4.

Sulle geometrie il codice usa **due convenzioni diverse, e questo va letto con attenzione** perché la
specifica di REMOTIX ne registra una sola:

| Struttura | Dove | Convenzione |
|---|---|---|
| `RECTANGLE_16` della meta AVC420 | `set_region_rects`, riga 559 | `right = x + width`, `bottom = y + height` → **esclusiva** |
| `RDPGFX_SURFACE_COMMAND` (`cmd.right/bottom`) | riga 686 | `right = extents.x + extents.width` → **esclusiva** |
| `MONITOR_DEF` di `ResetGraphics` | `maybe_reset_graphics`, riga 438 | `right = left + width - 1` → **inclusiva** |

> ⚠ **Da riverificare in REMOTIX.** §5.4 di `SPECIFICA.md` annota *«bordi della regione AVC420
> fuori-di-uno: sono inclusivi»*. Il riferimento fa il contrario sulla regione AVC420 ed è inclusivo
> solo sui `MONITOR_DEF`. Le due cose possono convivere se l'API di IronRDP applica già una
> conversione, ma è un punto dove un errore di ±1 produce esattamente il sintomo descritto
> (rinegoziazione e disconnessione), e va accertato guardando i byte, non il codice Rust.

#### 8.4 ResetGraphics

`grd_rdp_dvc_graphics_pipeline_reset_graphics` (riga 462) apre con:

```c
g_assert (g_hash_table_size (graphics_pipeline->surface_table) == 0);
```

**Tutte le superfici devono essere state cancellate prima di ridichiarare la tela.** E l'elenco dei
monitor non è mai vuoto: `maybe_reset_graphics` costruisce l'array dai monitor correnti, con
`g_assert (n_monitors > 0)`. Conferma la quarta correzione di §5.4 di `SPECIFICA.md`.

#### 8.5 Invio di un fotogramma

```
StartFrame(frameId, timestamp)      ← timestamp = ora<<22 | min<<16 | sec<<10 | ms
SurfaceCommand(surfaceId, codecId, ...)
[SurfaceToSurface, solo se c'è una superficie di rendering separata]
EndFrame(frameId)
```

Per RemoteFX Progressive esiste la scorciatoia `SurfaceFrameCommand`, che manda i tre PDU insieme.

Il `frameId` viene registrato in `frame_serial_table` insieme al *serial* della superficie, in modo che
un ack in ritardo che si riferisce a una superficie già distrutta non faccia danni: il serial è
contato a parte con `surface_serial_ref` / `unref`. È una raffinatezza che serve solo con
ridimensionamenti frequenti.

---

### 9. Codec ed encoder — la sorpresa

**`gnome-remote-desktop` non ha un encoder H.264 software.** Non usa ffmpeg, non usa x264, non usa
OpenH264. La selezione, in `grd-rdp-render-context.c:561`:

```
il client sa fare AVC (420 o 444)  ∧  c'è VAAPI  →  AVC444v2 se il client lo sa, altrimenti AVC420
altrimenti                                        →  RemoteFX Progressive (software)
```

Più un percorso separato, più vecchio, per **NVENC** (CUDA), che vive dentro la pipeline grafica e
scavalca il resto (`refresh_gfx_surface_avc420`).

| Percorso | File | Note |
|---|---|---|
| **VAAPI** | `grd-encode-session-vaapi.c` (1915 righe) | Scritto **direttamente contro libva**: SPS/PPS/slice generati a mano in `grd-nal-writer.c` (886 righe) |
| **NVENC** | `grd-hwaccel-nvidia.c` + `.cu` | Include due kernel CUDA (`grd-cuda-avc-utils.cu`, `grd-cuda-damage-utils.cu`) |
| **Vulkan** | `grd-hwaccel-vulkan.c` (1022 righe) | **Non è un encoder**: serve per importare i DMA-BUF e convertire il colore. La codifica resta VAAPI |
| **RFX Progressive** | `grd-rdp-sw-encoder-ca.c` | Ripiego software: usa `rfx_encode_message` di FreeRDP e riscrive il messaggio nel formato RDPEGFX |

#### 9.1 Controllo del bitrate: non c'è

`grd-encode-session-vaapi.c:1696`:

```c
config_attributes[1].type  = VAConfigAttribRateControl;
config_attributes[1].value = VA_RC_CQP;
```

**Quantizzazione costante, QP 22** (`picture_param->pic_init_qp = 22`, riga 923), profilo **H.264
High**, nessuna misura del bitrate, nessun VBV, nessun target. Anche nel percorso NVENC i valori
dichiarati nella meta sono fissi: `qp = 22`, `qualityVal = 100`.

> **Questo tocca direttamente §3.1 di `SPECIFICA.md`.** La specifica di REMOTIX motiva la scelta di
> `libavcodec` così: *«Vulkan Video consegna il codificatore senza il controllo del bitrate, che
> andrebbe scritto da noi… VA-API e NVENC lo forniscono già messo a punto dal costruttore»*. Il
> riferimento mostra che **VA-API messa a nudo non regala nulla**: il controllo del bitrate è un
> attributo di configurazione che va scelto e alimentato, e GNOME ha scelto di **non usarlo affatto**.
>
> La conclusione non ribalta la decisione di REMOTIX — `libavcodec` la comodità la dà davvero, perché
> incapsula VBV, GOP e preset dietro un'API sola — ma corregge la premessa: il merito è di ffmpeg, non
> di VA-API. E soprattutto: **sul punto di lavoro dei 10 Mbps il riferimento non ha niente da
> insegnare**, perché non ci prova nemmeno. Là REMOTIX è da solo.

#### 9.2 Come adatta, allora

Non adattando la qualità, ma **il numero di fotogrammi**. Vedi §10.

#### 9.3 AVC444

Implementato davvero, a differenza di xrdp. `prepare_avc444_bitstream` (riga 604) gestisce i tre casi
del campo `LC`: vista doppia (`LC=0`, due flussi), sola luma (`LC=1`), sola croma (`LC=2`). Il
`render_state` decide fotogramma per fotogramma se mandare la vista ausiliaria, ed esiste una logica di
*upgrade* ritardato (`FRAME_UPGRADE_DELAY_US = 60 ms`, `TRANSITION_TIME_US = 200 ms`,
`grd-rdp-surface-renderer.c`): quando il collegamento è tranquillo, il fotogramma «solo luma» già
mandato viene **completato** con la croma poco dopo.

È una risposta concreta alla strategia abbozzata in §5.2 di `SPECIFICA.md` (*«AVC420 come base, AVC444
attivabile su connessioni migliori»*): il riferimento lo fa per fotogramma, non per sessione, e paga
solo la croma quando c'è margine.

---

### 10. Controllo di flusso e adattamento

#### 10.1 Misura della rete (`grd-rdp-network-autodetection.c`)

Usa il meccanismo di autodetect di MS-RDPBCGR:

- **RTT**: `RTTMeasureRequest` con numeri di sequenza tracciati. Due cadenze — **70 ms** quando
  qualcuno ha bisogno di RTT preciso (cioè quando la pipeline grafica sta lavorando), **700 ms**
  altrimenti. Media su una finestra di 500 ms;
- **banda**: `BandwidthMeasureStart/Stop`, agganciata all'invio dei fotogrammi. Si misura **solo su
  fotogrammi ≥ 10 KB** (`MIN_BW_MEASURE_SIZE`), per non falsare la misura con pacchetti minuscoli;
- rilevamento di client che non rispondono: se restano più di 16 384 richieste senza risposta, il
  codice scrive *«Protocol violation: Client leaves requests unanswered»* e azzera.

C'è anche una autodetect **al momento della connessione** (`grd-rdp-connect-time-autodetection.c`, 643
righe), attivata dal gancio `OnConnectTimeAutoDetectBegin`.

#### 10.2 Il regolatore (`grd-rdp-gfx-frame-controller.c`)

Tre stati: `INACTIVE`, `ACTIVE`, `ACTIVE_LOWERING_LATENCY`. La grandezza regolata è il numero di
**«posti fotogramma»** (`total_frame_slots`) concessi al renderer: `0` significa fermo,
`UINT32_MAX` significa nessun limite.

La soglia di attivazione si ricava **dall'RTT**:

```c
delayed_frames = rtt_us * refresh_rate / 1e6;
activate_throttling_th = MAX (2, MIN (delayed_frames + 2, refresh_rate));
```

Cioè: quanti fotogrammi stanno «in volo» nel tempo di un round trip, più due. Superata quella soglia
di fotogrammi non riscontrati, si smette di produrre; scesi a ≤ 1, si riparte senza limiti. In mezzo,
i posti concessi sono `ack_rate + 1 − enc_rate`, cioè si produce al ritmo con cui il client conferma.

**Non c'è alcun adattamento di risoluzione, né di bitrate, né di frame rate nominale.** Il refresh rate
di riferimento è fisso: `TARGET_SURFACE_REFRESH_RATE = 60` (`grd-rdp-layout-manager.c:36`).

> Per REMOTIX: §3.1 di `SPECIFICA.md` prevede *«adattamento automatico di risoluzione e frame rate alla
> banda»*, riusando la macchina della risoluzione dinamica. Il riferimento **non fa così**: regola solo
> la cadenza di produzione, e lo fa contro il backlog di ack invece che contro la banda misurata (che
> pure misura, e usa solo per informare il client). È una scelta più semplice e più robusta, e vale
> come punto di partenza: la retroazione sugli ack è a costo quasi zero e va comunque implementata,
> l'adattamento di risoluzione è la rete di sicurezza sopra.

#### 10.3 Soppressione dell'uscita

`SuppressOutput` (MS-RDPBCGR) è gestito: quando il client minimizza la finestra, il renderer smette e
il consumatore di RTT viene rimosso, così le sonde rallentano da 70 a 700 ms.

---

### 11. Cattura

`grd-rdp-pipewire-stream.c`, 1326 righe.

#### 11.1 Il formato proposto

```c
SPA_FORMAT_VIDEO_format      = SPA_VIDEO_FORMAT_BGRx
SPA_FORMAT_VIDEO_size        = rettangolo FISSO (larghezza, altezza del monitor virtuale)
SPA_FORMAT_VIDEO_framerate   = 0/1                    ← «solo quando cambia»
SPA_FORMAT_VIDEO_maxFramerate= intervallo [1/1 … refresh_rate/1]
```

La cadenza dichiarata a zero con un massimo a intervallo è **esattamente** quanto REMOTIX ha accertato
in §5.6 di `SPECIFICA.md`.

> ✅ **La divergenza è chiusa: ha ragione il riferimento.** [M, 4 agosto 2026] Con la catena in C,
> contro Mutter 48.7, il **`SPA_POD_Rectangle` singolo funziona** e negozia esattamente la misura
> chiesta — provato a 1282×802, con `is-platform: true` dichiarato in `RecordVirtual`. Provato anche
> l'intervallo chiuso (min = pref = max): **funziona pure quello**, con lo stesso esito.
>
> Il `no more input formats` misurato da REMOTIX il 2 agosto era quindi un fatto della *sua* catena
> di allora — il pacchetto Rust di PipeWire — o dell'assenza di `is-platform`. Fra le tre
> spiegazioni ipotizzate qui, la versione di Mutter è esclusa (è la stessa); fra le altre due non si
> è discriminato, e non ne vale la pena: la forma pulita funziona e si usa quella. §5.6 di
> `SPECIFICA.md` è stato corretto di conseguenza.
>
> Resta vero che un intervallo **aperto** lascia scegliere a Mutter, che sceglie 1280×720.

#### 11.2 DMA-BUF

I modificatori si dichiarano solo se c'è un thread EGL **e non c'è NVENC**, con la proprietà marcata
`MANDATORY | DONT_FIXATE` e chiusa da `DRM_FORMAT_MOD_INVALID`. Quando si dichiarano i modificatori si
aggiunge sempre **un secondo formato di ripiego senza modificatori**, così se la negoziazione DMA-BUF
fallisce resta la memoria condivisa.

Conferma per contrasto la regola di REMOTIX (§5.6): *«per restare in memoria ordinaria non si dichiara
il campo `modifier`»*. Il riferimento fa il contrario perché il DMA-BUF lo vuole; la meccanica è la
stessa.

Tipi di buffer accettati: `MemFd` sempre, `DmaBuf` se c'è EGL. Da 2 a 8 buffer. Con DMA-BUF ed
**explicit sync** disponibile si chiede anche la meta `SPA_META_SyncTimeline`.

Meta richieste sempre: `SPA_META_Header` e **`SPA_META_Cursor`** (fino a 384×384) — il cursore arriva
come metadato e viene reso a parte, non disegnato nell'immagine, salvo in modalità screen-share dove si
usa `CURSOR_MODE_EMBEDDED`.

#### 11.3 Il ridimensionamento — la differenza che conta

`grd_rdp_pipewire_stream_resize()` (riga 402) fa **una cosa sola**:

```c
add_format_params (stream, virtual_monitor, ...);   /* con la misura nuova */
pw_stream_update_params (stream->pipewire_stream, params, n);
```

**Nessuna nuova sessione di cattura, nessun nuovo monitor virtuale, nessun nuovo `RecordVirtual`.**
Mutter riconfigura il monitor virtuale e risponde con `on_stream_param_changed`, dove il server
ridimensiona rilevatore di danno e pool di buffer, e emette `video-resized`.

> **È la risposta alla domanda aperta di §5.8 di `SPECIFICA.md`.** REMOTIX oggi rifà la cattura a ogni
> cambio di misura, e siccome una cattura nuova non si registra su un controllo già avviato, **rifà
> anche il controllo** — pagando il prezzo di perdere lo stato dei tasti premuti. La specifica annota
> *«sparirà con la fase 6, se il ridimensionamento smetterà di rifare la cattura»*. Il riferimento
> dimostra che si può, e come: si aggiorna il parametro del flusso PipeWire, e basta.

#### 11.4 Lo stride

Il codice calcola `stride = width * 4` in `on_stream_param_changed`, ma è solo per dimensionare il
pool; i dati veri si leggono sempre dal chunk (`grd-rdp-pw-buffer.c`). La regola di REMOTIX — *«lo
stride si legge dal chunk del buffer, mai calcolato»* — resta valida e vale anche qui.

---

### 12. Layout e ridimensionamento

`grd-rdp-layout-manager.c`, 1043 righe. È una macchina a stati esplicita, e merita di essere copiata
quasi così com'è.

```
AWAIT_CONFIG ──(arriva una configurazione monitor)──► inhibit_rendering()
                                                       │
                                              AWAIT_INHIBITION_DONE
                                                       │ (nessun render context in uso)
                                              PREPARE_SURFACES
                                                       │ crea/aggiorna gli stream
                                    ┌──────────────────┴──────────────────┐
                              AWAIT_STREAMS                        AWAIT_VIDEO_SIZES
                                    └──────────────────┬──────────────────┘
                                              START_RENDERING
                                                       │ uninhibit_rendering()
                                                  AWAIT_CONFIG
```

I punti che risolvono problemi noti a REMOTIX:

- **il rendering viene inibito prima di toccare qualunque cosa** e riacceso solo quando *tutti* gli
  stream hanno confermato la misura nuova. È la forma disciplinata della regola 3-bis di §5.7 di
  `SPECIFICA.md` («dopo un cambio di misura si aspetta che il desktop si sia ridisegnato»): invece di
  aspettare un silenzio di 300 ms, si aspetta un **evento**;
- l'inibizione non è un flag ma un **conteggio di risorse in uso**: `inhibition-done` viene emesso
  quando `acquired_render_contexts` è vuoto, cioè quando nessun fotogramma è a metà strada;
- durante `AWAIT_CONFIG` — e solo allora — `grd_rdp_layout_manager_transform_position` accetta le
  coordinate del puntatore. In ogni altro stato **l'input viene scartato**, perché la geometria non è
  stabile;
- una configurazione che arriva mentre se ne sta applicando un'altra **sostituisce** quella in coda
  (`pending_monitor_config`), non si accoda. È la risposta alle raffiche di ridimensionamento che i
  client mandano trascinando il bordo della finestra;
- se uno stream «monitor fisico» si chiude da solo, parte un timer di **50 ms**
  (`LAYOUT_RECREATION_TIMEOUT_MS`) che tenta di ricostruire l'ultima configurazione buona.

#### 12.1 Validazione della configurazione monitor

`grd-rdp-monitor-config.c`. Le regole, applicate identiche alle tre sorgenti possibili (Client Core
Data, Client Monitor Data, MS-RDPEDISP):

| Vincolo | Valore |
|---|---|
| Larghezza e altezza | **200 … 8192** |
| Dimensione fisica (mm) | 10 … 10000, altrimenti azzerata |
| Fattore di scala | 100 … 500, altrimenti azzerato |
| Monitor primario | deve stare a **(0, 0)**; se nessuno lo dichiara, se ne elegge uno che ci sta |
| Sovrapposizioni | **vietate** (verifica con `cairo_region`) |
| `DeviceScaleFactor` | **ignorato** — deprecato, solo Windows 8.1 |

Il desktop complessivo è l'estensione dell'unione delle regioni; l'offset del layout serve a
riportare tutto in coordinate non negative.

Su MS-RDPEDISP il server dichiara `MaxMonitorAreaFactorA = MaxMonitorAreaFactorB = 8192` e il numero
massimo di monitor: **16** nei modi headless/sistema, **1** in screen share.

---

### 13. Input

#### 13.1 libei, non i metodi `Notify*`

`gnome-remote-desktop` usa `ConnectToEIS` e parla libei, come la specifica di REMOTIX già annota in
§5.8. Vale la pena registrare **cosa se ne ricava**, perché sono cose che i metodi `Notify*` non danno:

| Cosa | Come |
|---|---|
| **La disposizione di tastiera della sessione** | `ei_device_keyboard_get_keymap()` → fd → `xkb_keymap_new_from_string` |
| **Lo stato reale di BlocMaiusc e BlocNum** | evento `EI_EVENT_KEYBOARD_MODIFIERS` |
| **Le regioni degli schermi** | `ei_device_get_region()` con `mapping_id` |
| **Un punto di sincronizzazione** | `ei_ping` / `EI_EVENT_PONG` |

Il primo punto è la **risposta alla questione aperta n.7 di REMOTIX** (§5.8: la disposizione di
tastiera non viene concordata). Il riferimento non impone nulla e non chiede nulla al client: **legge
la keymap dalla sessione**, e per gli eventi Unicode cerca quale tasto fisico produce quel simbolo
nella disposizione corrente, applicando i modificatori di livello:

```c
pick_keycode_for_keysym_in_current_group()   /* scorre keycode × livelli */
apply_level_modifiers()                      /* Shift per il livello 1, ISO_Level3_Shift per il 2 */
ei_device_keyboard_key (evcode, state)
evcode = xkb_keycode - 8                     /* XKB → evdev */
```

Gli eventi di scancode invece passano diretti: scancode RDP → `GetVirtualKeyCodeFromVirtualScanCode`
→ `GetKeycodeFromVirtualKeyCode(..., WINPR_KEYCODE_TYPE_EVDEV)`. Cioè: **le posizioni fisiche restano
posizioni fisiche**, e il simbolo lo decide la sessione — proprio la situazione che REMOTIX descrive.
La differenza è che il riferimento, avendo la keymap in mano, sa tradurre gli eventi Unicode con
precisione, mentre REMOTIX oggi deve dichiarare `REMOTIX_TASTIERA`.

> Nota pratica: con FreeRDP il KLID del client è disponibile (sta in `rdpSettings`), quindi la
> questione n.7 si può chiudere in due modi — dichiarando la disposizione dal KLID, oppure leggendola
> dalla sessione con libei come fa il riferimento. Il secondo è più solido, perché non si fida di come
> il sistema operativo del client descrive la propria tastiera.

#### 13.2 Dispositivi e capacità

Alla comparsa del seat: `ei_seat_bind_capabilities(POINTER, KEYBOARD, POINTER_ABSOLUTE, BUTTON,
SCROLL, TOUCH)`. I dispositivi arrivano poi con `EI_EVENT_DEVICE_ADDED`, e su
`EI_EVENT_DEVICE_RESUMED` si chiama `ei_device_start_emulating` con un numero di sequenza crescente.

**Il puntatore assoluto lavora per regioni**: ogni regione ha un `mapping_id`, e il `mapping_id` dello
stream di cattura fa da chiave. `transform_position` (`grd-session.c:703`) riscala le coordinate del
client sulla regione:

```c
scale_x = input_rect_width / ei_region_get_width (region);
x = ei_region_get_x (region) + motion_abs->x / scale_x;
```

È la sostituzione elegante del percorso D-Bus dello stream che REMOTIX passa a
`NotifyPointerMotionAbsolute`.

#### 13.3 La rotella

`grd-session-rdp.c:639`:

```c
axis_value = flags & WheelRotationMask;        /* complemento a due se negativo */
axis_step  = -axis_value / 120.0;              /* RDP conta 120 per scatto */
if (flags & PTR_FLAGS_WHEEL_NEGATIVE) axis_step = -axis_step;

verticale:   axis (0,  axis_step * 10.0)
orizzontale: axis (-axis_step * 10.0,  0)
```

`DISCRETE_SCROLL_STEP = 10.0`. **Il verticale è negato, l'orizzontale è negato in senso opposto** —
conferma esatta della regola 6 di §5.8 di `SPECIFICA.md`, compreso il fattore 120 → 10.

C'è anche `grd_session_notify_pointer_axis_discrete`, che rimoltiplica per 120 verso libei.

#### 13.4 Il tasto Pausa

Implementato con una macchina a quattro stati (`is_pause_key_sequence`, riga 738): riconosce la
sequenza `Ctrl↓(E1) → NumLock↓ → Ctrl↑(E1) → NumLock↑` e la traduce in `XKB_KEY_Pause` premuto e
rilasciato.

> Per REMOTIX: §5.8 dà il tasto Pausa per perso, perché IronRDP non consegna il flag `KBDFLAGS_EXTENDED1`.
> Il riferimento mostra che **il flag E1 serve solo a disambiguare**: la sequenza è riconoscibile
> anche dal solo susseguirsi di Ctrl e NumLock. Se il flag manca, la macchina a stati funziona
> ugualmente con un rischio di falso positivo trascurabile.

#### 13.5 Tasti premuti e tasti a scatto

- due tabelle, `pressed_keys` (per keycode) e `pressed_unicode_keys` (per keysym), che **scartano** la
  pressione ripetuta e il rilascio non appaiato — identico alla regola 4 di REMOTIX;
- alla chiusura della sessione, entrambe vengono svuotate rilasciando tutto, e la coda viene
  **svuotata forzatamente** (`grd_rdp_event_queue_flush`);
- l'evento di sincronizzazione RDP (`rdp_input_synchronize_event`) rilascia tutto e registra lo stato
  atteso di BlocMaiusc/BlocNum;
- la riconciliazione avviene **dopo un ping libei**: si aspetta che l'input in volo sia stato
  digerito (`grd_session_flush_input_async` → `EI_EVENT_PONG`), poi si confronta lo stato atteso con
  quello reale letto da `EI_EVENT_KEYBOARD_MODIFIERS` e, se diverge, si **preme e rilascia il tasto**.

Quest'ultimo punto è la versione fatta bene di ciò che §5.8 di `SPECIFICA.md` descrive come
approssimazione (*«non esiste un modo di imporlo… il conto parte da tutti spenti»*): con libei lo
stato reale si legge, e il ping evita di confrontarlo mentre ci sono eventi ancora in coda.

#### 13.6 Coda degli eventi

`grd-rdp-event-queue.c`: gli eventi arrivano dal thread socket e vengono accodati; una `GSource` sul
thread principale li svuota. **Nessuna chiamata bloccante dal ciclo del protocollo** — la regola 3 di
§5.8 di REMOTIX, applicata identica.

#### 13.7 Touch e penna (MS-RDPEI)

`grd-rdp-dvc-input.c` (764 righe) implementa il canale `RDPEI`: fino a **256 contatti**, con una
macchina a stati per contatto, più gli eventi penna. I contatti si mappano su `ei_touch` con le stesse
regioni del puntatore assoluto.

> È la **questione aperta n.1 di REMOTIX** (input touch, rilevante avendo Android fra i client). Il
> riferimento la risolve nativamente, non emulando il mouse.

---

### 14. Canali virtuali

| Canale | File | Stato |
|---|---|---|
| **RDPGFX** (EGFX) | `grd-rdp-dvc-graphics-pipeline.c` | Obbligatorio |
| **DISP** (MS-RDPEDISP) | `grd-rdp-dvc-display-control.c` | Solo in modalità `extend` |
| **RDPEI** (touch/penna) | `grd-rdp-dvc-input.c` | Sempre |
| **CLIPRDR** | `grd-clipboard-rdp.c` (2674 righe!) | Se il client si unisce al canale |
| **AUDIO_PLAYBACK** | `grd-rdp-dvc-audio-playback.c` | Se `AudioPlayback` e non `RemoteConsoleAudio` |
| **AUDIO_INPUT** | `grd-rdp-dvc-audio-input.c` | Se `AudioCapture` |
| **RDPECAM** (camera) | `grd-rdp-dvc-camera-*.c` | Sempre (novità della 49+) |
| **TELEMETRY** | `grd-rdp-dvc-telemetry.c` | Sempre |

Tutti derivano da `GrdRdpDvc`, che gestisce apertura, `ChannelIdAssigned`, sottoscrizione allo stato di
creazione e smontaggio. L'inizializzazione avviene nel thread socket quando `DRDYNVC` passa a
`DRDYNVC_STATE_READY`.

#### 14.1 Appunti

`grd-clipboard-rdp.c` è il file più grosso del progetto. Copre testo (UTF-8 e UTF-16), HTML,
immagini (BMP, TIFF, GIF, JPEG, PNG) e **file**, questi ultimi tramite un filesystem FUSE
(`grd-rdp-fuse-clipboard.c`, 1591 righe) che espone i file del client dentro la sessione. Formati
dichiarati in `grd-mime-type.c`.

REMOTIX ha la clipboard in §3.5 («bidirezionale», una riga). Il conto vero è questo: **il testo è
poche centinaia di righe, i file sono un progetto a sé**. Vale la pena scriverlo nel piano.

#### 14.2 Audio

Uscita: si negozia il formato migliore fra quelli offerti dal client, in ordine **AAC → Opus → PCM**.
Stereo fisso. AAC via fdk-aac, Opus a 48 kHz, PCM 16 bit. `grd-rdp-dsp.c` incapsula i tre encoder e
implementa anche la decodifica A-law per l'ingresso.

Sorgente e destinazione sono **PipeWire** (`grd-rdp-audio-output-stream.c`), non moduli PulseAudio
compilati a parte come in xrdp. È la stessa scelta di §3.2 di `SPECIFICA.md`.

Il volume del client viene applicato lato server moltiplicando i campioni PCM.

#### 14.3 Camera

`grd-rdp-dvc-camera-device.c` (1783 righe) + `grd-rdp-camera-stream.c`: redirezione della webcam del
client **dentro** la sessione, esposta come sorgente PipeWire. Supporta H.264 con un decodificatore
software (`grd-decode-session-sw-avc.c`). È fuori scope per REMOTIX, ma è la funzionalità che xrdp non
ha e che GNOME ha aggiunto per prima.

---

### 15. Configurazione

Tutto in GSettings, sotto `org.gnome.desktop.remote-desktop`, con schemi separati per
`rdp`, `rdp.headless`, `vnc`, `vnc.headless`. Le credenziali no: quelle stanno nel portachiavi o nel TPM.

| Chiave RDP | Predefinito | Note |
|---|---|---|
| `port` | 3389 | |
| `negotiate-port` | `true` | Prova i 10 porti successivi se occupato |
| `enable` | `false` | |
| `screen-share-mode` | `mirror-primary` | oppure `extend` (monitor virtuale) |
| `tls-cert`, `tls-key` | `''` | Percorsi a file PEM |
| `view-only` | **`true`** | Predefinito prudente: si guarda e basta |
| `auth-methods` | `['credentials']` | `credentials` (NTLM) e/o `kerberos` |
| `kerberos-keytab` | `''` | |

Opzioni da riga di comando del daemon: `--headless`, `--system`, `--handover`, `--rdp-port`,
`--vnc-port`, `--max-parallel-connections` (predefinito **10**, `0` = illimitate).

`grdctl` ha la forma `grdctl [--system|--headless] rdp <comando>`, con `set-credentials`,
`set-tls-cert`, `set-tls-key`, `enable`/`disable`, `enable-view-only`/`disable-view-only`,
`set-auth-methods`, `set-kerberos-keytab`, `--show-credentials`.

---

### 16. Connessioni concorrenti e limiti

Due meccanismi distinti, e conviene non confonderli.

**Il throttler** (`grd-throttler.c`) agisce *prima* di creare la sessione, contro gli abusi:

| Limite | Predefinito |
|---|---|
| Connessioni per peer | 5 |
| Connessioni in attesa | 5 |
| Tentativi al secondo (per peer) | 10 |
| Connessioni totali | `--max-parallel-connections`, 10 |

Chi supera viene **rifiutato**; chi arriva troppo in fretta viene messo in coda e servito quando il
rateo lo consente.

**La politica sulla seconda sessione** è invece in `on_session_post_connect` (`grd-rdp-server.c:176`):

```c
if (runtime_mode == HANDOVER || runtime_mode == HEADLESS)
  g_list_foreach (rdp_server->sessions, maybe_stop_session, nuova_sessione);
```

Cioè: nei modi a utente singolo, **la connessione nuova soppianta quella vecchia**, e lo fa dopo il
`PostConnect`, cioè dopo che il nuovo client si è autenticato.

> **È la terza opzione della tabella di §5.9 di `SPECIFICA.md`, quella che l'utente ha scartato** il 2
> agosto («soppiantare: comodo per riagganciarsi, ma chiunque si autentichi butta fuori chi sta
> lavorando»). Vale la pena registrare che il riferimento ha scelto diversamente da REMOTIX, e perché
> può permetterselo: le credenziali RDP di `gnome-remote-desktop` sono una coppia dedicata al desktop
> remoto, non le credenziali di sistema, quindi «chiunque si autentichi» è di fatto sempre la stessa
> persona che rientra. In REMOTIX, dove si autentica con PAM contro l'utenza vera, il ragionamento non
> regge allo stesso modo, e il rifiuto resta la scelta giusta.

Da notare anche: **il ciclo di accettazione è un `GSocketService`**, quindi le connessioni si accettano
in parallelo per costruzione. Il difetto di §5.9 di `SPECIFICA.md` — il ciclo sequenziale di
`ironrdp-server` — è specifico di IronRDP e qui non esiste.

#### 16.1 Il congedo

`grd_session_rdp_stop` (riga 1847) prima di chiudere imposta l'informazione d'errore RDP:

```c
if (!has_session_close_queued (session_rdp))
  freerdp_set_error_info (peer->context->rdp, ERRINFO_RPC_INITIATED_DISCONNECT);
else if (session_rdp->rdp_error_info)
  freerdp_set_error_info (peer->context->rdp, session_rdp->rdp_error_info);
```

I codici usati altrove: `ERRINFO_BAD_CAPABILITIES`, `ERRINFO_BAD_MONITOR_DATA`,
`ERRINFO_CLOSE_STACK_ON_DRIVER_FAILURE`, `ERRINFO_GRAPHICS_SUBSYSTEM_FAILED`,
`ERRINFO_CB_CONNECTION_CANCELLED`.

> **Era il «congedo dichiarato» che REMOTIX aveva a debito** (§5.9 di `SPECIFICA.md`). Con FreeRDP il
> debito non esiste: `freerdp_set_error_info` è API pubblica. Il riferimento usa
> `RPC_INITIATED_DISCONNECT` per la chiusura ordinata, non `LogoffByUser` — e la scelta è sensata,
> perché descrive chi ha chiuso, non perché.

---

### 17. Che cosa cambia fra la 48 (Debian Trixie) e la 51

L'architettura è la stessa: **la 48 usa già libei**, ha già il layout manager, l'encoder VAAPI, il
frame controller e la pipeline EGFX nella forma descritta qui. Le differenze:

**Aggiunto dopo la 48:**

- redirezione della **camera** (MS-RDPECAM): `grd-rdp-dvc-camera-*`, `grd-rdp-camera-stream`
- **decodifica** H.264 software (serve alla camera): `grd-decode-session-sw-avc`
- il **throttler** delle connessioni: `grd-throttler`
- `grd-frame-clock`, `grd-sample-buffer`, `grd-vk-physical-device`, `grd-vk-sync-file` (explicit sync)
- `grd-settings-headless` come classe a sé
- rinominati con prefisso `dvc`: `grd-rdp-graphics-pipeline` → `grd-rdp-dvc-graphics-pipeline`, e così
  per audio, display control e telemetria; introdotto `grd-rdp-dvc-handler`

**Requisiti diversi:** FreeRDP ≥ 3.1 (48) contro ≥ 3.22 (51); libei ≥ 1.2 contro ≥ 1.3.901.

Per REMOTIX significa che **tutto ciò che è utile qui è già nella 48.x che gira su Trixie**, e che le
misure fatte contro Mutter 48.7 restano confrontabili.

---

### 18. Il conto per REMOTIX

#### 18.1 Cosa conferma

| Decisione di REMOTIX | Conferma nel riferimento |
|---|---|
| **Solo EGFX**, nessun ripiego legacy | `rdp_peer_capabilities` chiude la connessione se manca (§6.1) |
| Interfacce dirette di Mutter, non il portale | Idem, e per la stessa ragione |
| `RecordVirtual` invece di `RecordMonitor` | Idem in modalità `extend` |
| `CreateSurface` + `MapSurfaceToOutput` | Adiacenti e obbligatorie (§8.2) |
| Larghezza ×16, altezza ×64 | Identico (§8.3) |
| `ResetGraphics` con la definizione dei monitor | `g_assert (n_monitors > 0)` (§8.4) |
| Cadenza PipeWire dichiarata a 0 + massimo a intervallo | Identico (§11.1) |
| Ultimo fotogramma conservato e rispedito | `invalidate_surface` ripropone `last_buffer` |
| Conteggio dei tasti premuti, rilascio a fine connessione | Identico (§13.5) |
| Rotella: /120 → ×10, verticale negato | Identico (§13.3) |
| Niente D-Bus dentro il ciclo del protocollo | Coda di eventi + `GSource` (§13.6) |
| PipeWire per l'audio | Identico (§14.2) |
| Sessione remota solo per l'utente che la possiede | Controllo sull'uid in `rdp_peer_logon` (§7.1) |
| Il congedo dichiarato serve | `freerdp_set_error_info` prima della chiusura (§16.1) |

#### 18.2 Cosa contraddice, o corregge

1. **NLA obbligatorio.** Il riferimento non offre TLS puro: `NlaSecurity = TRUE`, gli altri due a
   `FALSE`. REMOTIX ha scelto TLS + PAM. Non è un errore — è una scelta diversa con conseguenze
   diverse: con NLA le credenziali si verificano *prima* di allocare la sessione, e mstsc mostra la
   finestra di credenziali sua; con TLS puro l'autenticazione avviene dentro il protocollo RDP e il
   difetto trovato il 3 agosto (§3.4: «chi non manda credenziali non viene validato») **non potrebbe
   esistere**. Da mettere agli atti: la guardia che parte da *negato* è il prezzo del TLS puro.

2. **Il controllo del bitrate non lo dà VA-API.** §9.1. La motivazione di §3.1 di `SPECIFICA.md` va
   corretta nella premessa; la conclusione (usare `libavcodec`) regge lo stesso, anzi si rafforza.

3. **Non esiste un encoder H.264 software.** Il ripiego di GNOME è RemoteFX Progressive. REMOTIX
   prevede `libx264` come base sempre disponibile e punto di partenza dello sviluppo: è una scelta
   ragionevole e più semplice, ma va saputo che **il riferimento non la valida** — nessuno ha mai
   provato quella strada con questi client.

4. **La seconda connessione soppianta, non viene rifiutata.** §16. REMOTIX ha deciso diversamente e
   con ragione, ma la ragione va scritta: dipende dal fatto che REMOTIX autentica contro l'utenza vera.

5. **Il ridimensionamento non rifà la cattura.** §11.3. Questa è la correzione più utile: cancella il
   prezzo che §5.8 di `SPECIFICA.md` accetta a malincuore.

6. ~~**Rettangolo PipeWire singolo invece di intervallo chiuso.**~~ §11.1. **CHIUSA il 4 agosto: ha
   ragione il riferimento**, il rettangolo singolo funziona ed è la forma che REMOTIX usa. [M]

7. **Convenzione dei bordi della regione AVC420.** §8.3. Da riverificare sui byte.

#### 18.3 Cosa conviene copiare, in ordine di resa

1. **La macchina a stati del layout manager** (§12). Risolve insieme la regola 3-bis, le raffiche di
   ridimensionamento e lo scarto dell'input durante il cambio di geometria. È la cosa più preziosa del
   file.
2. **Il ridimensionamento via `pw_stream_update_params`** (§11.3). Toglie un rifacimento completo di
   cattura e controllo a ogni cambio di misura.
3. **Il regolatore a posti-fotogramma con soglia dall'RTT** (§10.2). Poche decine di righe, e dà
   l'adattamento di base gratis.
4. **L'elenco completo delle versioni EGFX** (§8.1), da tenere allineato.
5. **`disable-animations: true`** nella creazione della sessione di cattura (§5). Una riga.
6. **La validazione della configurazione monitor** (§12.1): limiti, primario a (0,0), niente
   sovrapposizioni.
7. **La riconciliazione dei tasti a scatto dopo un ping** (§13.5), se e quando si passa a libei.

#### 18.4 Le questioni aperte di REMOTIX su cui il riferimento dice qualcosa

| Questione | Cosa dice il riferimento |
|---|---|
| **n.1** — input touch | Implementato nativamente via MS-RDPEI + `ei_touch`, 256 contatti (§13.7) |
| **n.6** — bottone centrale e rotella orizzontale | **Caduta**: era un limite di IronRDP. FreeRDP consegna `MouseEvent`, `ExtendedMouseEvent` e `RelMouseEvent` distinti (§6.2, §13.3) |
| **n.7** — disposizione di tastiera | Non si concorda: **si legge dalla sessione** via `ei_device_keyboard_get_keymap` (§13.1). In alternativa il KLID è in `rdpSettings` |
| **n.9** — mstsc, sfondo al 75% dopo cambio di misura | Nessuna corrispondenza diretta, ma §12 suggerisce dove guardare: il riferimento **non manda nulla** fra l'inibizione e la conferma di tutti gli stream. Se REMOTIX manda il fotogramma conservato prima che il palco sia coerente, il sintomo è quello |
| **n.10** — sessione non registrata in logind | Il riferimento usa `sd_session_get_class` e `sd_session_is_remote` (`grd-daemon-utils.c:195`), quindi **assume** che la sessione sia registrata. Nei modi headless è chi avvia la sessione a doverlo garantire, non il server |

---

### 19. Cosa non c'è

Per completezza, e per non cercarlo:

| Funzionalità | Stato |
|---|---|
| Encoder H.264 software | **Assente** — il ripiego è RemoteFX Progressive |
| Controllo del bitrate | **Assente** — CQP fisso, QP 22 |
| Adattamento di risoluzione alla banda | **Assente** — si regola solo la cadenza |
| Multitransport UDP (MS-RDPEUDP) | `SupportMultitransport = FALSE` |
| Gateway RDP (MS-TSGU) | Assente |
| Redirezione dischi del client | Assente (la FUSE serve solo ai file della clipboard) |
| Redirezione stampanti, seriali, USB | Assente |
| RemoteApp (RAIL) | Assente |
| Smartcard | Assente |
| Cache delle superfici EGFX | Dichiarata e sempre rifiutata (`CacheImportReply` vuota) |
| Backend X11 | Assente — solo Wayland, come REMOTIX |
| HEVC, AV1 | Impossibili: non sono in MS-RDPEGFX |


<a id="xpra"></a>

## XPRA — lo studio, fatto il 14 agosto 2026

*Il settimo studio del progetto. ⛔ Era previsto da `PIANO.md` §1.3 **prima di scrivere la pagina**
e non è mai stato fatto: si scrive adesso, a pagina scritta, ed è tardi — ⭐ ma non troppo, perché
metà di quel che c'è qui dentro ha cambiato il prodotto **oggi stesso**.*

> ### ⭐⭐⭐ Perché questo studio esiste, e chi l'ha chiesto
>
> **L'ha chiesto l'utente, due volte.** La prima il 9 agosto, ed è l'origine di tutto il binario
> web: *«ti spiego perché mi è venuto in mente il discorso WEB: in passato ho avuto modo di usare
> XPRA, e devo dire di essere rimasto molto sorpreso»* (`DECISIONI.md` §1.6).
>
> La seconda **il 14 agosto**, davanti al prodotto che finalmente si usava, e con un difetto in
> mano: *«un piccolo difetto è la cattura del puntatore del mouse… per questa funzionalità puoi
> studiare la soluzione che ha adottato il progetto XPRA»*.
>
> ⇒ ⛔ **E aveva ragione in mezz'ora**: la soluzione di Xpra al puntatore ha smontato una riga delle
> nostre specifiche che ne contraddiceva un'altra. È `LEZIONI.md` §9 punto 0 — *«cercare chi l'ha
> già fatto»* — per la terza volta, e per la terza volta a chiederlo è stato l'utente.

### Come è stato fatto, e che cosa vale

⛔ **Letto nel codice**, non nella documentazione: `Xpra-org/xpra-html5`, i file `html5/js/Client.js`
e `html5/js/Window.js`, più `docs/Usage/Encodings.md` del server. ⇒ Quel che segue è `[R]`, salvo
dove è scritto `[S]`.

⚠ **E il confine si dichiara**: Xpra è su **WebSocket** e noi su **WebTransport**; il suo server è
nato attorno al modello di *damage* di X11 e il nostro parla con un compositore Wayland. ⛔ **Il
trasporto non si eredita, e nemmeno il modello di aggiornamento.** Quel che si eredita è la **forma
delle domande** che il client fa al server — ed è lì che siamo indietro.

⚠ **E una cosa che NON ho potuto misurare**: il `README` non elenca i limiti del client HTML5
(appunti, audio, disposizioni di tastiera, IME, schermo intero). ⇒ `[?]` — non li deduco dal codice
letto a campione.

---

### ⭐⭐⭐ 1. La cosa che vale di più, e ci serviva OGGI: **il primo fotogramma si CHIEDE**

```javascript
request_refresh(wid) {
  this.send([PACKET_TYPES.buffer_refresh, wid, 0, 100,
            {"refresh-now": true, batch: {reset: true}}, {}]);
}
```

⛔⛔ **Il client di Xpra non ASPETTA che lo schermo cambi: dice al server «ridipingi adesso».**

⇒ E questo è **esattamente** il difetto che l'utente ha sentito oggi come *«il tempo fra il login e
la comparsa del desktop è troppo lungo»*: `[M]` 14 agosto 2026, dal registro della sua sessione
vera, fra il canale video acceso e il primo pixel passano **4,10 secondi su 5,21**, e il registro
dice il perché — *«scena ferma: Mutter consegna solo quando qualcosa cambia»*.

| | |
|---|---|
| ⛔ **quel che ci manca** | in `RCP.md` **non esiste un messaggio che chieda l'immagine**. C'è `RICHIEDI_CHIAVE` (§7.1), ma chiede una **chiave** di quel che è già stato catturato: se non arriva niente dal compositore, non produce niente |
| ⚠ **e non si copia alla lettera** | il `buffer_refresh` di Xpra costa poco perché il loro server possiede il modello di damage di X11. ⛔ Su Wayland **non si può ordinare a Mutter di ridipingere**: la leva equivalente è **riavviare il flusso**, che consegna un buffer — `[M]` è così che nasce il nostro fotogramma del `+325 ms` |
| ⇒ ⭐ **quel che si eredita** | **la forma**: il client deve poter dire «dammi lo schermo adesso», e il server deve avere *una* strada per obbedire. Chi la attua è affare nostro |

---

### ⭐⭐ 2. Il cursore: **lo disegna il browser, non la pagina** — e niente cattura

```javascript
function set_cursor_url(url, x, y, w, h) {
  window_element.css("cursor", `url('${url}') ${x} ${y}, auto`);
}
```

⭐ **Il cursore del browser INDOSSA la forma di quello remoto**, punto attivo compreso, da una
`data:image/png;base64`. ⛔ **Nessun elemento disegnato sopra la tela, nessun `cursor: none`.** E la
scala la fa lui quando `devicePixelRatio ≠ 1`, aggiustando anche il punto attivo.

**E la cattura del puntatore?** C'è, ⛔ **ma è un'opzione dell'utente**, non un automatismo:

```javascript
if (window.cursor_lock && win.canvas) { win.canvas.requestPointerLock(); }
```

⇒ un bottone (`#cursor-lock-button`) che si preme. Le coordinate sono **assolute per difetto**; con
la lock accesa passano agli spostamenti (`e.movementX`).

> #### ⛔⛔ E qui lo studio ha smontato una nostra riga con un'altra nostra riga
>
> | dove | che cosa diceva |
> |---|---|
> | `SPECIFICHE.md` §7.1 | *«il mouse fisico arriva da **Pointer Lock**… senza, se ne vedrebbero due»* |
> | `SPECIFICHE.md` §7.5 | *«puntatore **assoluto** — è l'**unico** percorso del puntatore»* |
>
> ⇒ La lock serve a dare gli **spostamenti relativi**. Noi mandiamo **posizioni assolute**. ⛔ Non
> comprava niente, e costava il sequestro del puntatore — che è precisamente quel che l'utente ha
> visto.
> ⭐ **E il motivo per cui era stata messa** — *«altrimenti se ne vedono due»* — si risolve meglio
> nell'altro modo, **con il pezzo che avevamo costruito la mattina stessa e non stavamo usando**:
> `CURSORE_FORMA` (`RCP.md` §7.2).
>
> ✅ **Adottato il 14 agosto 2026**: il cursore del browser veste la forma remota, la freccia
> disegnata si toglie di mezzo nel modo classico, la cattura resta accendibile a mano. Il modo a
> **tocco** tiene il puntatore disegnato, e deve: ⭐ **il dito non ha un cursore da vestire.**

---

### ⭐⭐ 3. La misura della finestra: **il client la dice, il server la esegue**

```javascript
_screen_resized(event) {
  const packet = [PACKET_TYPES.configure_display,
                  {"desktop-size": [this.desktop_width, this.desktop_height],
                   "monitors": this._get_monitors(), …}];
  this.send(packet);
}
```

⭐ **Il client comunica la propria misura e il server RIDIMENSIONA il desktop.** Lo scalamento CSS
locale (`transform: scale(1/scale)`) resta come ripiego, non come strada principale.

⇒ ⛔ **È la nostra `RCP.md` §4.5, «la tela concessa» — e oggi nessuno la mantiene**: `[M]` 14 agosto
(anello A1), un client che chiede **1280×720** ottiene la concessione, ma il palco cattura
**1920×1080** (costante di compilazione) e `rcp` rifiuta **ogni** fotogramma: *145 prodotti, 0
spediti, client nero senza errori*.

⚠ **E il prezzo si vede sullo schermo dell'utente**: il suo è **21:9** (2560×1080), il desktop
remoto **16:9** ⇒ `[M]` dal suo video, **il 36 % dei pixel è banda nera**.

---

### 4. Come dipinge — e qui **noi siamo avanti**

| Xpra HTML5 `[R]` | noi |
|---|---|
| **canvas 2D** con un *offscreen canvas* e `swap_buffers()` | canvas + **WebCodecs** |
| codifiche accettate: `rgb32`, `rgb24`, `jpeg`, `png`, `webp`, `scroll`, `void` | **HEVC/AV1 in hardware** |
| ⛔ `h264` **rifiutato nel percorso principale**: *«h264 decoding is only supported via the decode workers»* | il video è la strada normale, non l'eccezione |

⇒ ⭐ **La loro strada di riferimento è ancora a immagini** (jpeg/png/webp) con il video come caso
speciale in un worker. La nostra nasce sul video. ⚠ E questo spiega la frase dello studio del web:
*«Xpra e noVNC restano sul canvas, e **nessuno dei due dichiara un numero di ritardo**»* (§web).

#### ⭐ Una cosa che loro hanno e noi no: la codifica `scroll`

`[S]` *«tries harder to send screen updates using motion vectors»* — invece dei pixel si manda
**«questa zona si è spostata di N»**. È il caso di chi scorre una pagina o un terminale, cioè
**quel che l'utente fa tutto il giorno**.
⚠ **Non è una cosa da prendere adesso**: con HEVC in hardware i vettori di moto li trova il
codificatore, ed è il suo mestiere. ⭐ Ma la riga va tenuta per il giorno in cui la banda stringe:
`SPECIFICHE.md` §8.

---

### 5. La tastiera: **loro mandano posizioni, noi lettere** — e la differenza è voluta

```javascript
[PACKET_TYPES.key_action, wid, keyname, pressed, modifiers, keyval, keystring, keycode, group]
```

⛔ Xpra manda **il codice e il nome del tasto**, più `keyval`, `keystring` e il `group`. ⇒ È la
strada che `SPECIFICHE.md` §7.3 ha scartato **con una ragione scritta**: *«un client con tastiera
americana attaccato a una sessione italiana produrrebbe le lettere sbagliate»*, e su Android una
tastiera **non ha posizioni affatto**.

⭐ **E i tasti morti loro li trattano, noi no** — esplicitamente:

```javascript
const dead = keystring.toLowerCase() === "dead";
if (dead && ((this.last_keycode_pressed !== keycode && !pressed) || pressed)) { … }
```

⇒ ✅ **Ed è coerente con la decisione presa dall'utente oggi** (`DECISIONI.md` §5-bis.6-bis): i
tasti morti e l'IME restano **fuori, dichiarati**. ⚠ Lo studio conferma che il prezzo esiste — Xpra
lo paga con codice apposta — e che **la nostra strada è un'altra scelta, non una dimenticanza**.
`[?]` E l'**IME** non compare nemmeno da loro: chi scrive in cinese dentro un browser, in Xpra,
`[?]` non l'ho trovato servito.

---

### 6. Il ritardo: **lo misurano, e noi no**

```javascript
this.server_ping_latency = 0;
this.client_ping_latency = 0;
PING_FREQUENCY = 5000;   // ms
```

⭐ Un `ping` ogni cinque secondi, e **due** numeri distinti: quanto ci mette il server e quanto il
client. ⇒ ⛔ Noi il ritardo lo misuriamo **al banco** (`DECISIONI.md` §2.6) e **non lo mostriamo mai
all'utente**: quando dice *«mi sembra lento»* non ha un numero da darci, e noi non abbiamo il suo.

⚠ **Non è la stessa misura del nostro tetto di 50 ms** — il loro è il giro di rete, il nostro è
input → vetro. ⭐ Ma la lezione è di forma: **un numero che l'utente vede è un numero che l'utente
può contestare**, ed è più utile di dieci nei nostri file di esiti.

---

### ⛔ Che cosa NON si prende da Xpra

| | perché |
|---|---|
| il **trasporto** (WebSocket) | `DECISIONI.md` §6.4: noi su WebTransport, e quel pezzo non si eredita |
| la **strada a immagini** (jpeg/png/webp con il video in un worker) | è il contrario del nostro punto di partenza: `SPECIFICHE.md` §3.1 vuole 4K a 60 con la codifica in hardware |
| le **posizioni di tasto** come strada principale | §7.3, con la ragione già scritta e già pagata in v1 |
| il modello di **damage di X11** | il nostro compositore è Wayland: la stessa domanda si fa, la risposta la dà un altro meccanismo |

---

### ⭐ Che cosa questo studio ha già cambiato, e che cosa apre

| | stato |
|---|---|
| ⭐ **il cursore vestito dal browser, e niente cattura** | ✅ **fatto il 14 agosto 2026** |
| ⛔ **il client deve poter chiedere l'immagine** («ridipingi adesso») | ⏳ **aperto** — ed è il lavoro sul tempo di apparizione del desktop |
| ⛔ **la tela alla misura del client** | ⏳ **aperto**: `RCP.md` §4.5 esiste e non è mantenuta. Sul 21:9 dell'utente il **36 %** dello schermo è nero |
| ⚠ **un numero di ritardo mostrato all'utente** | 🔸 da valutare: costa poco e cambia il modo in cui i giudizi tornano indietro |
| la codifica `scroll` | 📖 tenuta da parte per quando la banda stringe |

> #### ⭐⭐ E la riga da portarsi via, che non è tecnica
>
> Lo studio era previsto **prima** di scrivere la pagina, ed è stato fatto **dopo**. ⛔ Nel mezzo
> abbiamo scritto una specifica che si contraddiceva (§7.1 contro §7.5), l'abbiamo attuata, e il
> difetto l'ha trovato **l'utente in trenta secondi d'uso** — indicandoci anche dove guardare.
>
> ⇒ ⚠ *Il costo di saltare il punto 0 di `LEZIONI.md` §9 non è il tempo dello studio: è il codice
> scritto nel frattempo, e la fiducia spesa a difenderlo.*
