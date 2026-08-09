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

---

## 1. In due minuti

### 1.1 ⭐ Le cinque cose che questo studio ha cambiato

| # | | |
|---|---|---|
| 1 | ⛔ **L'eccezione del certificato NON copre WebTransport** | né su Chrome né su Firefox `[R]`. Il predefinito «un clic e vai» che era stato proposto **non funziona**, e la strada diventa `serverCertificateHashes` — §3 |
| 2 | ⛔ **`prefer-hardware` non prova niente su Android** | Chromium sceglie **di proposito** un decodificatore HEVC software quando non ne trova uno hardware `[R]`. È la forma d'errore **E1**, cioè il muro di v1, **ricomparso un livello più in alto** — §4 |
| 3 | ⭐ **Si perde molto meno tastiera del temuto** | a schermo intero la lista riservata di Chrome scende da dodici comandi a **due**, e in una **PWA installata è vuota** `[R]` — §5 |
| 4 | ⭐ **La clipboard si può sorvegliare, da gennaio 2026** | `clipboardchange` è in Chrome 144, ed è stato motivato **esplicitamente dai client di desktop remoto** `[S]` — §5 |
| 5 | ⛔ **Il compositore del browser costa 16-40 ms** | `[?]` fra il disegno e il pixel acceso, cioè **quanto tutto il nostro tetto**. E nessuna API JavaScript lo vede — §6 |

### 1.2 ⛔ E le tre convergenze fra rapporti, che nessuno dei quattro poteva vedere da solo

Sono la ragione per cui questo documento esiste oltre ai quattro rapporti.

**A. I 10 bit hanno tre indizi contrari, e nessuno è una misura.**

| Da dove | Che cosa dice |
|---|---|
| `DECISIONI.md` §2.3-bis | sul percorso `mediacodec` di Android il supporto a 10 bit è limitato e **l'uscita torna a 8** `[S]` |
| **S2** | sui fotogrammi decodificati in hardware `VideoFrame.format` è **null** e `copyTo()` è negato `[R]`; uno sviluppatore di Chromium scrive che quei percorsi *«possono subire una conversione a 8 bit»* `[S]` |
| **S4** | la condizione di zero-copy di WebGPU è letteralmente `format == PIXEL_FORMAT_NV12` `[R]`: **P010 non passa**. E il canvas 2D ha un aiutante che si chiama `DownShiftHighbitVideoFrame` `[R]` |

⛔ **Da cui `DECISIONI.md` §2.2 — il desiderato a 10 bit, deciso dall'utente l'8 agosto — va scritta
provvisoria**, che è la regola già in vigore (`LEZIONI.md` §2.3-quater: una decisione che poggia su
una `[?]` è presa a metà). ⚠ E la difficoltà si chiude su sé stessa: **dal browser i 10 bit non
sono leggibili**, quindi la prova finale è **guardare una sfumatura**, cioè `LEZIONI.md` §2.4 — il
metro è quel che si vede.

**B. ⭐ La PWA lega S1 e S3, e cambia quanto vale un certificato vero.**

| | |
|---|---|
| **S1** | dietro un'eccezione di certificato, su Chrome **il Service Worker non si installa** `[R]` ⇒ niente PWA |
| **S3** | in una **PWA installata** la lista dei tasti riservati di Chrome è **vuota** `[R]` ⇒ tutte le scorciatoie arrivano alla sessione |

⛔ **Messe insieme**: il certificato vero non compra solo «nessun avviso». **Compra la tastiera
intera.** Chi ha un dominio ha un prodotto migliore, non solo più comodo — e questa riga va detta a
chi installa, perché nessuno la dedurrebbe.

**C. Il decodificatore invisibile obbliga il prodotto a diagnosticarsi da sé.**

`DECISIONI.md` §2.7 dice che il massimo lo offre il server e l'altezza la mette il client, **ma che
un ripiego va dichiarato**. S2 dimostra che **da JavaScript la verità non è leggibile** `[R]`.
⛔ Quindi la diagnosi non può stare in un banco di laboratorio: **deve stare nel prodotto**, perché
il dispositivo dell'utente è l'unico posto dove la domanda ha una risposta. La pagina misura la
propria portata e **lo dice** — è I7 in una forma nuova: la protezione sta nel programma.

---

## 2. La mappa

| Che cosa | Versione su cui è stato letto |
|---|---|
| **Chromium / Blink** | 151 |
| **Gecko / Firefox** | 151-153 |
| **WebKit / Safari** | 26.4 |
| WebTransport | Baseline **marzo 2026**, con Safari 26.4 |
| WebCodecs | Chrome 94+ · Firefox 130+ · Safari 26+ · **Chrome per Android 147** |
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

⛔ **E questo chiude, con una ragione tecnica dura, la proposta di far installare un'autorità
nostra** (`DECISIONI.md` §1.7): su Chrome **non basta nemmeno il magazzino di sistema**, perché
quella radice non è *incorporata nel browser*.

### 3.2 Che cosa se ne è ricavato

| | |
|---|---|
| **la strada** | `serverCertificateHashes`, promosso da rete di sicurezza a **strada normale** (`RCP.md` §4.1-bis) |
| ⛔ **due certificati, non uno** | uno **longevo** per la pagina — è quello su cui vive l'eccezione dell'utente e **non deve cambiare** — e uno **breve, ≤14 giorni**, per la sessione, che ruota da sé. ⚠ Confonderli fa ricomparire l'avviso ogni due settimane, e nessuno collegherebbe le due cose |
| ⭐ **una cosa che cade e semplifica** | `Alt-Svc` **non c'entra**: WebTransport apre la sua connessione da sé `[S]`. Il ripiego silenzioso su TCP che era stato dichiarato come pericolo **non può accadere** |
| ⛔ **il prezzo dell'eccezione** | dietro di essa, su Chrome, **il Service Worker non si installa** `[R]` — e vedi §1.2 B |

### 3.3 Il banco

⛔ **La prima misura del progetto, e non ne serve nessun'altra prima**: Safari. Si prova se
l'eccezione concessa alla pagina lasci passare la sessione WebTransport, su macOS **e su iOS
separatamente**. Il controllo positivo è ovvio e va fatto lo stesso: **la stessa prova su Chrome
deve fallire** — se passasse, il banco non sta misurando quel che crede.

`[?]` **La seconda**: quanto dura l'eccezione su Chrome. Il rapporto dice **circa sette giorni** —
se fosse vero, il clic non è «una volta per dispositivo» ma **una volta a settimana**, ed è
un'informazione che cambia la frase che si dice all'utente.

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
| ⛔ **il controllo positivo** | VP9 forzato in software — **software per costruzione**. Se il banco non lo dichiara tale, il suo verdetto su HEVC va buttato |

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

### 6.1 La strada

`drawImage(videoFrame)` su canvas 2D **desincronizzato**, dipinto **dentro la callback del
decodificatore** — non su `requestAnimationFrame` — con WebTransport, decodifica e canvas **tutti
in un worker dedicato**, così il fotogramma non attraversa mai un `postMessage`. Zero copie in CPU
se il fotogramma è NV12 a 8 bit; una conversione di colore in GPU `[R]`. È anche l'unica che
funziona su tutti e tre i motori.

⚠ **E impone la forma della pagina**: il video vive nel worker, l'input vive nel thread principale
(gli eventi di tastiera e puntatore sono del DOM). Due mestieri, due thread, e il confine passa fra
loro — deciderlo adesso costa niente, scoprirlo alla fase 4 costa una riscrittura.

### 6.2 Il pezzo che non è nostro e si sente lo stesso

`[?]` Fra il disegno e il pixel acceso passano **1,5-2,5 intervalli di quadro: 16-40 ms a 60 Hz**,
cioè **quanto tutto il nostro tetto**. Il tetto «solo per il pezzo che è nostro» resta legittimo
(`DECISIONI.md` §2.4), ma **quella riga va scritta accanto al tetto** o si promette una cosa e
l'utente ne sente un'altra.

⭐ **La leva, se servisse**: Selkies e moonlight-web non dipingono su canvas — mandano i fotogrammi
a un elemento `<video>` per prendere il percorso **overlay**, che salta il compositore `[R]`. Va
sotto un interruttore spento, non scritta per prima. ⚠ Xpra e noVNC restano sul canvas, e **nessuno
dei due dichiara un numero di ritardo**.

### 6.3 Il banco, e il suo pezzo cieco

L'anello di `DECISIONI.md` §2.6 si costruisce così: `t0` prima di spedire, `t1` come **prima riga**
della callback del decodificatore, poi si disegna, e **solo dopo** si legge la marca con una
lettura di 16×16 pixel. ⛔ **Quell'ordine è vincolante**: leggere prima sarebbe un ritorno dalla
GPU, e falserebbe la misura che sta prendendo.

| | |
|---|---|
| ⛔ **il controllo decisivo** | il server ritarda di **N millisecondi noti**, e la mediana **deve salire di esattamente N**. Un banco che non lo fa non sa di misurare |
| ⛔ **il pezzo cieco** | la misura finisce alla callback; il pixel si accende `[?]` 16-40 ms dopo, e **nessuna API JavaScript lo vede**. Si stima, e **la stima si dichiara accanto a ogni numero** invece di far finta che il numero sia il totale |
| ⚠ **e il righello va tarato** | senza le due intestazioni di isolamento fra origini, su Firefox e Safari i cronometri hanno grana **1 ms** — su un tetto di 50 |

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

⛔ **E tutte sul dispositivo vero.** «Il Chrome del portatile lo fa» non dice niente del Chrome del
telefono: è la forma d'errore **E10** con un travestimento nuovo (`DECISIONI.md` §5-bis.0-ter).

---

## 8. ⏳ Quel che questo studio NON sa

*Elencato perché non venga riscoperto come chiuso. Ogni rapporto ha la sua lista; queste sono le
voci che toccano una decisione.*

| | |
|---|---|
| `[?]` Safari e WebTransport dietro eccezione | §3.1 — **e Apple non documenta nemmeno se l'eccezione si possa concedere su iOS** |
| `[?]` la durata dell'eccezione su Chrome | §3.3 |
| `[?]` i 10 bit fino allo schermo | §1.2 A — e **non è verificabile da JavaScript** |
| `[?]` la Keyboard Lock su DeX, e la PWA su Android | §5.5 |
| `[?]` i 16-40 ms del compositore | §6.2 — nessuna API li espone |
| `[?]` quanti stream al secondo regge ciascun browser | `RCP.md` §2.3 — il video ne consuma uno per fotogramma |

---

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
