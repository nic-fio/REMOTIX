# Il mouse è inutilizzabile su Samsung DeX — un problema aperto, e la richiesta di una soluzione alternativa

*Scritto il 14 agosto 2026. Questo documento è **autosufficiente**: chi lo legge non ha il nostro
codice sotto mano, quindi ogni affermazione porta la sua provenienza.*

> ## ⭐ Che cosa chiedo a chi legge
>
> **Una diagnosi alternativa, e una cura alternativa.** Non una conferma.
>
> Ho una spiegazione e due cure proposte (§7). Sono già stato smentito **due volte** su questo
> stesso difetto, e tutte e due le volte la spiegazione «ovvia» era una coincidenza (§5). Quindi:
>
> 1. **Che cosa c'è di sbagliato nella mia diagnosi?** Se la mia catena causale non regge, dimmi
>    dove si rompe e con quale scenario concreto.
> 2. **C'è una cura che non ho considerato?** In particolare una che non richieda di toccare né
>    il compositore né il protocollo.
> 3. **Quale misura distinguerebbe** fra le spiegazioni rimaste in piedi? Cerco l'esperimento che
>    fa cadere una delle due, non altre conferme.
>
> ⛔ **Prima di proporre una cura, controlla il §6**: otto ipotesi sono già state misurate e
> smentite, e ripercorrerle non serve.

---

## 1 · Che cos'è questo prodotto

Un **server di desktop remoto** per Linux, scritto da zero.

| pezzo | com'è fatto |
|---|---|
| **server** | C, ~9.600 righe, gira su Debian 13 |
| **compositore** | **GNOME/Mutter su Wayland**. Si cattura chiedendo a Mutter un **monitor virtuale** via D-Bus (`org.gnome.Mutter.ScreenCast` → `RecordVirtual`), e i fotogrammi arrivano da **PipeWire** |
| **input** | iniettato con **libei/EIS** (`ConnectToEIS` di Mutter) |
| **codifica** | **HEVC/AV1 in hardware** (Intel UHD 730, VAAPI) |
| **trasporto** | **WebTransport** (HTTP/3, QUIC), protocollo applicativo nostro |
| **client** | **una pagina web**, ~6.200 righe, che decodifica con **WebCodecs** e dipinge su `<canvas>` |

⛔ **Non usiamo RDP né VNC.** Il protocollo è nostro. Questo conta, perché quasi tutte le
soluzioni note al nostro problema sono scritte dentro RDP o VNC e vanno **tradotte**, non copiate.

### Il cursore, com'è trattato oggi

Chiediamo a Mutter la cattura con `cursor-mode = METADATA`: ⇒ **il cursore NON è dipinto dentro
l'immagine catturata**. Arriva come metadato accanto al fotogramma.

⇒ Conseguenza: **la pagina deve disegnarsi il puntatore da sola**, e oggi lo fa con un elemento
`<div>` che contiene un SVG, mosso con `transform: translate(...)`.

⚠ **E il cursore di sistema del client resta visibile.** Quindi sullo schermo dell'utente ci sono
**due puntatori sovrapposti**: quello di Android e quello che disegniamo noi.

---

## 2 · La scena esatta del difetto

| | |
|---|---|
| **client** | **Samsung DeX col cavo** (telefono Samsung agganciato a un monitor), **Chrome per Android** |
| **monitor** | **2560×1080**, ultrawide 21:9 |
| **periferiche** | mouse e tastiera **Bluetooth** |
| **finestra del browser** | `2133×772` pixel CSS · `devicePixelRatio` **1,2** · vista dichiarata **2560×926** |
| **rete** | LAN, **via cavo** dal lato server; il telefono è su Wi-Fi |
| **desktop remoto** | **1920×1080**, costante di compilazione ⇒ su uno schermo 21:9, **il 36 % dei pixel è banda nera** |

### ⭐ E c'è un controllo che funziona, sullo stesso ferro

Sullo **stesso** DeX, con lo **stesso** mouse Bluetooth e lo **stesso** monitor, l'utente usa
**Remote Desktop Manager di Devolutions** (un client RDP nativo per Android) e dice, testuale:
*«Con RDM non c'è nessun problema»*.

⇒ ⭐⭐ **Android, il Bluetooth, il DeX e il monitor sono scagionati.** Il difetto è nostro.

---

## 3 · Il sintomo, con le parole dell'utente

1. *«Il mouse ha sempre problemi con le coordinate degli elementi (esempio barra della finestra
   del terminale)»*
2. *«L'input da tastiera è sempre laggato»*
3. *«È come se si perdessero gli input»*
4. *«Il mouse è al limite dell'usabilità»* → poi, il giorno dopo: **«Non funziona, il mouse è
   inutilizzabile»**

---

## 4 · Le misure fatte

Tutte `[M]`, cioè misurate sul ferro vero, il 12-14 agosto 2026.

| che cosa | valore | come |
|---|---|---|
| ⭐⭐ **fotogrammi consegnati** | **134 in due minuti = 1,1 al secondo** | contatore del server, sessione vera dell'utente sul DeX |
| **ritardo «prima di noi»** | **9 ms** per i tasti, **12 ms** per i movimenti | `performance.now() − event.timeStamp` nel gestore dell'evento, sul DeX. ⛔ In questo numero **non c'è nessun salto di rete**: è il tratto dal dispositivo fisico al nostro codice JavaScript |
| **anello completo input → vetro** | **139,40 ms** (n=326) e **141,60 ms** (n=322) | due giri indipendenti, concordi entro 2,2 ms. ⚠ Il nostro obiettivo dichiarato è **50 ms**: sforiamo di quasi tre volte |
| **coda del canale di input** | **1** (peggiore: 1) | `desiredSize` del `WritableStream` di WebTransport. **Non si è mai riempita** |
| **movimenti del puntatore scartati** perché la coda era piena | **0** | contatore in pagina |
| **eventi di movimento ricevuti dalla pagina** | **165 · 227 · 320 · 200** per sessione | quattro sessioni. ⇒ Gli eventi **arrivano** |
| **tempo dal login al primo pixel** | **4,10 s su 5,21** | registro della sessione dell'utente |

### ⚠ Un numero che sembra latenza e non lo è

Il «giro completo» misurato dalla pagina dà una **mediana di 130 ms** e un **peggiore di
2161 ms**. ⛔ Il peggiore **non è latenza**: il giro si chiude solo quando arriva il fotogramma
successivo, e a 1,1 fotogrammi al secondo quel numero misura **l'attesa del prossimo fotogramma**.
La mediana regge, la coda della distribuzione no.

---

## 5 · ⛔ Due volte la spiegazione ovvia era una coincidenza

Lo scrivo perché è il motivo per cui chiedo un parere esterno.

**Prima volta.** Il puntatore sembrava «catturato» e scomodo. La specifica diceva che il mouse
fisico doveva arrivare da **Pointer Lock**. Studiando un altro progetto è saltato fuori che la
nostra stessa specifica, due paragrafi più in là, diceva che le coordinate sono **assolute**:
⇒ la Pointer Lock serve a dare gli **spostamenti relativi**, e con coordinate assolute **non
comprava niente** — costava solo il sequestro del puntatore. Due righe nostre che si
contraddicevano, attuate entrambe.

**Seconda volta, ed è peggio.** Avevamo misurato: mettendo `cursor: none` (nascondere il cursore
del browser per lasciare solo la nostra freccia), i movimenti passavano da **165-320 per
sessione** a **ZERO**, con **una sola variabile cambiata**. Correlazione fortissima. Ne avevamo
dedotto un divieto: *«su Android non si può nascondere il cursore del browser»*.

⛔ **Falso.** Andando a rileggere la storia del codice: la versione in vigore al momento di quella
misura registrava **`mousemove` e basta** — `pointermove` compariva solo dentro un commento. E su
Samsung è documentato da **quattro progetti indipendenti** (noVNC #1727, KasmVNC #222, Kasm
workspaces #20, moonlight-android #573) che Chrome consegna i `mousemove` **solo al clic**.

⇒ *«4 clic e zero movimenti»* era **quel** difetto, non `cursor: none`. E il meccanismo che
avevamo ipotizzato non esiste comunque: nel codice di Android, `dispatchPointerEvent()` viene
**prima** di `maybeUpdatePointerIcon()` — l'icona del puntatore è un **effetto** del movimento,
non una sua condizione.

> **Morale:** su questo difetto, una correlazione a una variabile sola **non basta**. Serve il
> meccanismo, letto in una fonte.

---

## 6 · ⛔ LE OTTO IPOTESI GIÀ SMENTITE — non ripercorrerle

| ipotesi | come è caduta |
|---|---|
| **la conversione delle coordinate sbaglia** | `[M]` rifatta a mano sui numeri veri del DeX: `(1170/0,833 − 457)/0,857 = 1105` contro il **1104** dichiarato dalla pagina; `160/0,833/0,857 = 224` contro **223**. Torna al pixel |
| **la mappatura ignora le bande nere** | ⛔ falso: il codice riempie le bande a ogni fotogramma e le sottrae nella conversione |
| **è il Wi-Fi o il risparmio energetico di Android** | ⛔ Doze e App Standby valgono **a schermo spento**; il risparmio 802.11 accoda la **discesa**, non la salita |
| **è l'IME di Android** (il famigerato `keyCode 229`) | ⛔ nel codice di Chromium l'IME entra **solo col fuoco su un nodo modificabile**. E `[M]` 13 lettere sono arrivate corrette: con l'IME nel mezzo sarebbero state scartate tutte |
| **incolonnamento nel canale di input** | ⛔ `[M]` coda **1**, scarti **0**. Non si è mai riempita |
| **un processo concorrente ruba il codificatore hardware** | ⛔ `[M]` quel processo non codificava |
| **`cursor: none` spegne i movimenti su Android** | ⛔ vedi §5: era `pointermove` mancante |
| **la latenza è nella rete o nel Bluetooth** | ⛔ `[M]` i 9-12 ms del tratto «prima di noi» **non contengono nessun salto di rete** |

---

## 7 · La mia diagnosi, e le due cure che propongo

### 7.1 Il meccanismo che credo di aver capito

Due scelte, **ciascuna corretta per conto suo**:

1. **Mutter consegna un fotogramma solo quando cambia un pixel** (è il comportamento giusto: non
   sprecare banda su una scena ferma);
2. **il cursore non è dipinto dentro l'immagine** (`cursor-mode = METADATA`).

⇒ **Muovere il mouse sopra lo sfondo del desktop non cambia nessun pixel, quindi non arriva
nessun fotogramma.** Il desktop remoto è, letteralmente, **fermo** mentre l'utente muove il mouse.
*«Come se si perdessero gli input»* descrive esattamente questo: **non se ne perde nessuno, non si
vede che arrivano.**

### ⚠ 7.2 E qui la mia diagnosi ha una crepa che non so chiudere

Se la freccia che disegniamo in pagina **si muove già** alla velocità della mano — e si muove,
perché è un elemento del DOM mosso da JavaScript a ogni evento, e `[M]` gli eventi arrivano
(165-320 per sessione) — allora **«1,1 fotogrammi al secondo» spiega perché il DESKTOP non
reagisce, ma non spiega perché il PUNTATORE sia scomodo.**

⇒ ❓ **Una delle due cose è vera, e non so quale**: o c'è un secondo difetto che non ho trovato,
o il sintomo «mouse inutilizzabile» è in realtà il sintomo «non vedo che cosa sto facendo».

### 7.3 Come lo risolvono gli altri — letto nel loro codice

Ho letto il codice di sei progetti che fanno questo mestiere:

| progetto | che cosa fa col puntatore |
|---|---|
| **xrdp** (server RDP) | `[M]` misurato da me sul ferro: **200 movimenti del mouse a schermo fermo = 0 byte dal server al client**. La posizione **non viaggia mai** |
| **FreeRDP** (client RDP) | non disegna nessuna freccia: **presta la forma al cursore del sistema operativo** (`XcursorImageLoadCursor` + `XDefineCursor`) |
| **FreeRDP per Android** | **butta via** i messaggi del puntatore: sei funzioni con il **corpo vuoto**. Su Android il puntatore fluido è **quello di sistema** |
| **xpra** (client HTML5) | il **cursore del browser veste la forma remota** con `cursor: url(data:image/png;base64,...) hx hy`. **Non usa `cursor: none` da nessuna parte** |
| **gnome-remote-desktop** (percorso VNC) | manda la **posizione** del cursore in un messaggio dedicato, perché il suo client non ha modo di saperla |
| **noVNC / Guacamole / KasmVNC / Chrome Remote Desktop** | 4 su 5 **chiedono al server di ridimensionare il desktop** alla misura del client, invece di impaginare con le bande |

⭐ **La riga che li accomuna tutti:**

> **Loro hanno UN puntatore, noi ne abbiamo DUE.**

⭐⭐ **E una scoperta che riguarda direttamente il nostro stack:** Mutter, in modo `METADATA`,
**consegna già un buffer PipeWire a ogni movimento del cursore**, anche quando non cambia nessun
pixel — un buffer con `chunk->size = 0` che porta dentro `spa_meta_cursor->position`, già
convertita in pixel della tela, fino a **60 volte al secondo**. **Noi quel buffer lo riceviamo e
ne leggiamo solo la forma: la posizione non compare in nessuna riga del nostro codice.**

⛔ **E xpra, che sta sullo stesso PipeWire, ha il nostro identico problema e non l'ha risolto**:
ha semplicemente **tolto il puntatore dal fotogramma**.

### 7.4 Le due cure che propongo

**Cura A — un puntatore solo, quello di sistema, vestito dal server.**
Togliere la freccia che disegniamo, e usare il messaggio di **forma del cursore** che il server
già ci manda (e che oggi la pagina riceve e **butta via**: la funzione che lo attuerebbe esiste,
scritta, e **non ha nessun chiamante**) per vestire il cursore del browser con
`cursor: url(data:...) hotspotX hotspotY`.

- **posizione**: dal client, istantanea, zero rete;
- **forma**: dal server, ~31 byte a cambio — ed è l'unico modo di sapere *che cosa c'è sotto il
  puntatore* (barra di testo su un campo, maniglia sul bordo di una finestra) **senza aspettare un
  fotogramma**.

⚠ Rischi che conosco: il **tremolio** se le forme arrivano fitte (chi l'ha già affrontato mette un
freno con pavimento a 10 ms); il limite di **Blink**, oltre i **32 DIP** il cursore sparisce se
tocca il bordo della vista (limite duro 128 DIP); e sbagliare il **punto attivo** riprodurrebbe
proprio il sintomo che vogliamo curare.

**Cura B — chiedere a Mutter un monitor virtuale della misura del client.**
Oggi chiediamo 1920×1080 fisso e impaginiamo con le bande. La conversione delle coordinate ha
quindi **tre stadi in cascata**:

```
x_desktop = ((clientX − bordo_tela) / scala_vetro − offset_banda) / scala_tela
```

⛔ Nessuno dei sei progetti studiati ne ha **più di uno**. Chiedendo un monitor della misura
giusta: bande zero, **conversione a uno stadio**, e il 36 % di pixel neri che oggi codifichiamo e
spediamo sparisce.

⚠ Vincoli raccolti: larghezza **pari**, fra 200 e 8192 (li rispetta il 2560×926 che ci
servirebbe).

---

## 8 · ⛔ I vincoli — quel che NON possiamo fare

Questi non sono negoziabili, e una cura che li viola non ci serve.

| vincolo | perché |
|---|---|
| **il client è una pagina web**, non un'app nativa | è una decisione di prodotto, presa e pagata |
| ⛔ **niente cattura del puntatore su Android** | in un'app nativa basta `View.requestPointerCapture()`. In Chrome per Android la Pointer Lock esiste ma `movementX` è **ricostruito** da Chromium e i micro-movimenti sono **scartati** ⇒ i movimenti relativi non sono affidabili |
| ⛔ **su Wayland non si può ordinare al compositore di ridipingere** | non esiste l'equivalente del modello di *damage* di X11. La sola leva che conosciamo è riavviare il flusso, che costa |
| **niente RDP, niente VNC** | il protocollo è nostro, su WebTransport |
| ⛔ **il cursore dipinto dentro l'immagine è da evitare** | costa banda a ogni movimento, e ha il difetto classico della **scia**. `gnome-remote-desktop` non lo usa mai |
| **il cursore di sistema del client non si può togliere di mezzo sul DeX** | è una `SurfaceControl` con flag `eCursorWindow`, mossa dal thread di input a **125 Hz**, indipendente dai fotogrammi dell'applicazione |

---

## 9 · Le domande precise

1. ⭐⭐ **La crepa del §7.2.** Se la freccia in pagina si muove già alla velocità della mano,
   perché l'utente giudica il mouse *inutilizzabile*? Quali spiegazioni restano in piedi, e **che
   misura le distingue**?
2. ⭐ **La cura A è sufficiente?** Togliere il secondo puntatore e vestire quello di sistema
   risolve *«problemi con le coordinate degli elementi»*, o sto curando un sintomo estetico
   mentre la causa è altrove?
3. **C'è una terza cura?** Qualcosa che non richieda né di toccare la misura del monitor virtuale
   né di aggiungere messaggi al protocollo.
4. **La latenza.** 139 ms input → vetro contro un obiettivo di 50, e `[M]` nessun singolo tratto
   domina. Con codifica hardware, WebCodecs e una LAN, quanto è realistico quell'obiettivo? E
   dove guarderesti per primo?
5. **La tastiera.** *«L'input da tastiera è sempre laggato»* non ha ancora una causa misurata, e
   IME, Bluetooth e coda sono già stati esclusi. Che cosa resta?
6. ⛔ **Che cosa ho sbagliato a misurare?** Due volte su due, la correlazione forte era una
   coincidenza. Quale dei numeri del §4 non misura quel che credo?

---

## Legenda delle marche

Nel testo ogni affermazione ne porta una:

| | |
|---|---|
| `[M]` | **misurato** da noi, sul ferro, con la data |
| `[R]` | **letto** nel codice sorgente di un progetto di riferimento |
| `[S]` | letto in una **specifica** |
| `[?]` | **ipotizzato**, non ancora misurato |

⛔ Nel §7.2 e nella domanda 1 c'è una `[?]` grossa e dichiarata: **non so perché il puntatore sia
scomodo**, e tutte le mie cure poggiano su quella. È il punto su cui vorrei essere contraddetto.
