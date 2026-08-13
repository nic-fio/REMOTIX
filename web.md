# Il browser come client — studio, per la fase 1

*Scritto il 9 agosto 2026, con quattro indagini parallele sulle specifiche W3C/WHATWG e sul codice
sorgente di Chromium, Gecko, WebKit, Guacamole, noVNC e Xpra. È il **sesto studio** del progetto, e
il primo che non parla di un compositore.*

> ## ⚠ Perché questo studio esiste
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

## 1. In due minuti

### 1.1 ⭐ Le cinque cose che questo studio ha cambiato

| # | | |
|---|---|---|
| 1 | ⛔ **L'eccezione del certificato NON copre WebTransport** | né su Chrome né su Firefox `[R]`. Il predefinito «un clic e vai» che era stato proposto **non funziona**, e la strada diventa `serverCertificateHashes` — §3 |
| 2 | ⛔ **`prefer-hardware` non prova niente su Android** | Chromium sceglie **di proposito** un decodificatore HEVC software quando non ne trova uno hardware `[R]`. È la forma d'errore **E1**, cioè il muro di v1, **ricomparso un livello più in alto** — §4 |
| 3 | ⭐ **Si perde molto meno tastiera del temuto** | a schermo intero la lista riservata di Chrome scende da dodici comandi a **due** `[R]` — §5. ⚠ Ma quel che il **sistema operativo** si tiene non lo recupera nessun browser |
| 4 | ⭐ **La clipboard si può sorvegliare, da gennaio 2026** | `clipboardchange` è in Chrome 144, ed è stato motivato **esplicitamente dai client di desktop remoto** `[S]` — §5 |
| 5 | ⛔ **Il compositore del browser costa 25-42 ms a 60 Hz** | `[?]` 1,5-2,5 intervalli di quadro fra il disegno e il pixel acceso — **più di tutto il nostro tetto**. E nessuna API JavaScript lo vede — §6 |

### 1.2 ⛔ E le quattro convergenze fra rapporti, che nessuno dei quattro poteva vedere da solo

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

## 2. La mappa

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

## 3. S1 — Il certificato: l'eccezione non copre la sessione

*Dettaglio: `web/rapporti/S1-certificato.md`.*

### 3.1 La risposta, motore per motore

| | |
|---|---|
| **Chrome/Edge** | ⛔ **no**, e per due ragioni indipendenti. L'eccezione dell'utente vive nel processo browser e la consulta **un solo punto**, alimentato dagli errori delle richieste normali: il client WebTransport **non la interroga mai** `[R]` — assenza verificata **con controllo positivo** su un punto dove quel meccanismo invece c'è. E il QUIC di Chrome pretende una radice **incorporata nel browser**: `ERR_QUIC_CERT_ROOT_NOT_KNOWN` |
| **Firefox** | ⛔ **no**, per una ragione diversa: l'eccezione **viene** consultata anche su HTTP/3, e subito dopo la sessione si chiude se la radice non è incorporata `[R]`. L'unica deroga scritta nel codice è, testualmente, `serverCertificateHashes` |
| **Safari** | `[?]` **il caso aperto**: la sua eccezione non aggira niente, mette il certificato **nel portachiavi**, e WebTransport passa di lì. Potrebbe essere l'unico dove la risposta è sì. **Nessuno l'ha documentato** |

> ## ⛔ E Safari **ha** `serverCertificateHashes` — la correzione che avevo perso per strada
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

### 3.2 Che cosa se ne è ricavato

| | |
|---|---|
| **la strada** | `serverCertificateHashes`, promosso da rete di sicurezza a **strada normale** (`RCP.md` §4.1-bis) — ⭐ **e vale su tutti e tre i motori**, Safari 26.4 compreso |
| ⛔ **due certificati, non uno** | uno **longevo** per la pagina — è quello su cui vive l'eccezione dell'utente — e uno **breve, ≤14 giorni**, per la sessione, che ruota da sé. ⚠ Confonderli fa ricomparire l'avviso ogni due settimane |
| ⛔ **e l'avviso torna comunque ogni sette giorni** | `[R]` `kCertErrorBypassExpirationInSeconds = 604800`, con il commento *«Certificate error bypasses are remembered for one week»*. ⚠ *Questa riga mancava, e con essa la conseguenza: **anche tenendo il certificato della pagina fermo, su Chrome il clic si rifà ogni settimana**. Cambia la frase che si dice all'utente (R2)* |
| ⭐ **una cosa che cade e semplifica** | `Alt-Svc` **non c'entra**: WebTransport apre la sua connessione da sé `[S]`. Il ripiego silenzioso su TCP che era stato dichiarato come pericolo **non può accadere** |
| ⛔ **il prezzo dell'eccezione** | dietro di essa, su Chrome, **il Service Worker non si installa** `[R]` — e vedi §1.2 B |
| ⏳ **due cose che S1 lascia da decidere, e che avevo taciuto** | **(1)** Safari è l'unico motore con WebTransport anche su **HTTP/2 e TCP**: il nostro server non lo parla, quindi il suo ripiego finirebbe in errore — *va deciso* se implementarlo o dichiarare Safari fuori dal ripiego. **(2)** una pagina già aperta ha in mano **un'impronta che invecchia**: alla riconnessione dopo la rotazione va ricaricata o va richiesta l'impronta corrente — *va deciso dove sta questo aggiornamento in `RCP.md`* |

### 3.3 Il banco

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

> ### ⛔ E i controlli sono tre, non uno — la cura era rimasta a metà
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

## 4. S2 — La decodifica: la trappola di v1 travestita da API

*Dettaglio: `web/rapporti/S2-decodifica.md`.*

### 4.1 ⛔ Il fatto che conta più di tutti

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

### 4.2 Il supporto, e il formato del flusso

| | |
|---|---|
| **HEVC Main10 in WebCodecs** | Chrome per Android da **108.0.5343.0** · Chrome su Linux solo via VA-API da **108.0.5354.0** · Safari da 16.4 (solo video) e pieno da **26.0** `[S]` |
| copertura di campo 2026 | ≈ **85 %** in decodifica Main10 — ⚠ e l'autore del dato dichiara che **non distingue hardware da software** |
| ⭐ **il formato del flusso** | **Annex-B senza `description`**: è legale, è **quel che `hevc_vaapi` già produce**, e in Chromium **risparmia un'allocazione e una copia per fotogramma** `[R]`. Tre progetti su tre fanno così; moonlight-web prova Annex-B **per primo** proprio su HEVC |
| ⚠ la trappola dell'hvcC | Chromium riparsa l'SPS e **rifiuta la configurazione** se i byte di prevenzione dell'emulazione cadono nel campo sbagliato `[R]` — un motivo in più per non prendere quella strada |

⭐ **La strada pigra è anche quella giusta**, ed è raro: non si scrive un impacchettatore, non si
converte niente, e si risparmia una copia.

### 4.3 Il banco

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

## 5. S3 — Tastiera e appunti: il 2026 ha ribaltato le premesse

*Dettaglio: `web/rapporti/S3-tastiera-appunti.md` — 96 `[R]`, 103 `[S]`, 23 `[?]`, zero `[M]`.*

### 5.1 ⛔ Una riga di `SPECIFICHE.md` §7.3-bis era sbagliata, e l'ho scritta io

Diceva: *«la Keyboard Lock esiste solo su Chrome ed Edge, e solo a schermo intero»*, e che
`Ctrl+W`, `F11` e `Ctrl+Shift+I` sono perduti. **Falso su tre punti:**

| | |
|---|---|
| **non è più solo Chrome** | `requestFullscreen({keyboardLock:"browser"})` è entrato nel Fullscreen Standard WHATWG l'**8 maggio 2026**, e l'hanno spedito **Safari 26.4** e **Firefox 151** `[S]`. Chrome/Edge restano sulla vecchia `navigator.keyboard.lock()`: ⚠ **la pagina deve saperle entrambe** |
| **si perde molto meno** | la lista riservata di Chrome è di **dodici** comandi; **a schermo intero scende a due** — `F11` e l'uscita — **senza chiamare nessuna API** `[R]`. Firefox ne ha **sei**, Safari **zero** (ma filtra a schermo intero, e ⭐ **questo spiega il vecchio commento di noVNC su Safari**) |
| ⭐ **in una PWA installata è vuota** | `// In Apps mode, no keys are reserved` `[R]` |

### 5.2 Quel che si perde davvero

| | |
|---|---|
| `Ctrl+Alt+Canc` | ovunque, e non è recuperabile |
| l'uscita da schermo intero | per costruzione: è la via di fuga dell'utente |
| ⛔ **su macOS, tutte le scorciatoie di sistema** | non esiste un aggancio — la funzione che dovrebbe fornirlo **restituisce `nullptr`** `[R]`, e il controllo di sistema precede la lock |
| ⛔ **su Android e DeX, qualunque combinazione con Meta** | per regola AOSP — ⚠ e **DeX è l'uso primario dichiarato** (`DECISIONI.md` §5-bis.0) |

### 5.3 Gli appunti: l'ipotesi «non si può sorvegliare» è superata

| | |
|---|---|
| ⭐ `clipboardchange` | **Chrome 144, 13 gennaio 2026** — e la motivazione scritta nella proposta sono **i client di desktop remoto** `[S]`. Porta solo i tipi MIME, vuole il fuoco |
| ⛔ **non esiste su Firefox e Safari** | verificato, non dedotto. Là ogni lettura costa il menu «Incolla» con **un secondo di attesa** |

### 5.4 ⭐ Tre regali dalla lettura del codice altrui

1. ⛔ **La cura del modificatore rimasto giù**, che per noi è il difetto più grave perché **la
   sessione sopravvive alla connessione**: Guacamole risincronizza lo stato dei modificatori
   **dagli eventi del mouse** `[R]`. Non c'è altro modo, e nessuno l'avrebbe inventato;
2. la tabella `KeyboardEvent.code` → **evdev** di Chromium, canonica e **senza buchi da 1 a 94**
   `[R]` — cioè la conversione che `RCP.md` §7.3 richiede, già scritta e verificabile;
3. la corsa fra `Ctrl+V` e la lettura degli appunti, che **tutti e tre** i riferimenti disinnescano
   a mano — Xpra ritarda **ogni battuta di 100 ms** `[R]`. ⚠ Per noi 100 ms sono **due volte il
   tetto del ritardo**: quella cura non si copia, si sostituisce.

### 5.5 Le due `[?]` che contano di più

Entrambe su DeX, che è l'uso primario: **se la lock funzioni su DeX** (esiste solo da Android 16
QPR1) e **se la PWA valga anche su Chrome per Android**.

---

## 6. S4 — Il ritardo del disegno

*Dettaglio: `web/rapporti/S4-ritardo-disegno.md`.*

### 6.1 La strada — ⛔ **non più una prescrizione: una decisione misurata** *(13 agosto 2026)*

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

> ### ⛔⛔ Il worker: attuato, misurato — e **sbagliato A METÀ, non per intero**
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
> ### E i fotogrammi dipinti, obbligatori accanto (`LEZIONI.md` §6.2)
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
> ### ⭐⭐ Il meccanismo, ed è la scoperta che cambia una REGOLA
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
> ### ⏳ `[?]` E questo va letto ACCANTO ai numeri, non in fondo
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

### 6.2 Il pezzo che non è nostro e si sente lo stesso

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

### 6.3 Il banco, e il suo pezzo cieco

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

## 7. Il piano delle misure

Nell'ordine, e ciascuna col suo controllo positivo. **Nessuna richiede una riga di prodotto.**

| # | La misura | Perché prima o dopo |
|---|---|---|
| **S1a** | l'eccezione su **Safari** lascia passare WebTransport? (macOS e iOS separati) | ⛔ **la prima**: decide se iPhone e iPad hanno una strada senza dominio |
| **S1b** | quanto dura l'eccezione su Chrome | cambia la frase che si dice all'utente: «una volta» o «una volta a settimana» |
| **S2** | HEVC Main10 in hardware **sul telefono vero** — saturazione, canarina, decadimento | decide che cosa la pagina dichiara, non se il progetto esiste (`DECISIONI.md` §2.7) |
| **S3a** | la Keyboard Lock su **DeX** | è l'uso primario, ed è una `[?]` |
| **S3b** | la PWA su Chrome per Android | vale la tastiera intera (§1.2 B) |
| **S4** | l'anello del ritardo, con il ritardo noto come controllo | dà il numero, e **la misura del pezzo cieco** |

> ⛔ **E tre etichette della sonda NON sono nate qui**, contro quel che `fasi/01-filo-nudo.md`
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

## 8. ⏳ Quel che questo studio NON sa

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

## 8-bis. ⛔ Le dodici cose che i rapporti dicevano e questa sintesi taceva

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

## 9. Le lezioni che questo studio aggiunge

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
