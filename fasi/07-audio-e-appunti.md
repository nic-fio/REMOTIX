# Fase 7 — Audio e appunti

⭐ **Aperta il 17 agosto 2026**, col suo documento e **prima di una riga di codice**
(`PIANO.md` §0.1). Il piano è `PIANO.md` §«Fase 7 — Audio e appunti»; il modello di questo
documento è `PIANO.md` §0.2.

> **La scena che l'utente giudicherà**: *«apre un video nel desktop remoto e lo **sente** dal
> portatile; copia un indirizzo sul telefono e lo **incolla** dentro la sessione, e viceversa.»*

⚠ **E una cosa da dire subito, perché non sia una scoperta**: la **fase 6 non è chiusa** — il suo
§8 aspetta il giudizio dell'utente su due scene (il trascinamento del bordo e il clic tenuto giù).
Aprire la 7 è una decisione dell'utente del 17 agosto 2026 (*«in questa sessione sviluppiamo la
fase 7»*); ⛔ quel che resta della 6 **resta aperto e non si chiude da sé**.

---

> # ⭐⭐⭐ DA QUI SI RIPRENDE — **17 agosto 2026, sera**
>
> *Deciso dall'utente: «per gli appunti apriamo una nuova sessione».*
>
> ## ✅ L'AUDIO È FATTO, e il giudizio c'è: **«problema audio risolto»**
>
> | | |
> |---|---|
> | **la misura** | 49,95 blocchi/s ricevuti contro 50 prodotti — **perdita zero**, **2 buchi** (dell'avvio) e coda stabile a 311-341 ms |
> | **la scena** | un video di **YouTube** riprodotto nella sessione remota, giudicato a orecchio |
> | ⛔ **e prima ci sono stati sette «fa schifo»** | §6.8, ed è il capitolo che insegna: sei cure su otto erano difetti **veri** che non erano quello che l'utente sentiva |
>
> ## ⭐⭐ E GLI APPUNTI SONO FATTI — **«clipboard funziona in entrambi i versi»**, 17 ago 2026 sera
>
> *Giudizio dell'utente col browser, porta 7730.* ⇒ 📖 §4.5 (che cosa è stato scritto), §6.9
> (⛔ l'arbitro esterno del banco **non esiste**, e perché), §9.2-bis (il verdetto, e che cosa non
> dice).
>
> ⛔ **Nessun banco automatico ha mai visto passare un byte di appunti**: quel giudizio è l'unica
> prova che questa metà della fase abbia.
>
> *Quel che segue era il piano di partenza, ed è rimasto vero tranne §2.4:*
>
> Il piano è §0 e §2 di questo documento; tutto quel che serve è già scritto lì:
>
> - ⭐ **il lato indipendente c'è ed è gratis**: su GNOME la sponda X11 di Mutter è incondizionata,
>   quindi **`xclip` funziona senza una nostra sessione** — è l'arbitro esterno (§2.4);
> - ⛔ **tre trappole di Mutter** che il banco non vede e il prodotto sì (`PIANO.md` §Fase 7):
>   `DisableClipboard` è **a senso unico** (non si chiama mai); la firma di `mime-types` è
>   **asimmetrica** e chi legge col tipo sbagliato ottiene `NULL` **senza errore**; il gestore
>   interno tiene **un solo tipo MIME**;
> - **si riusa** `v1/remotix-c/src/appunti_mutter.c` (450 righe, GNOME);
> - ⚠ e la clipboard **si svuota all'inizio di ogni giro**, o quel che resta dal giro prima viene
>   annunciato e sembra un risultato (`LEZIONI.md` §2.3-quinquies).
>
> ## ⚙ Lo stato della macchina, per non ricostruirlo
>
> | | |
> |---|---|
> | **il server dell'audio** | acceso sulla **7710** (`banchi/07-b41-accendi.sh --hz 0`), albero `/media/REMOTIX/src/07-audio-src` |
> | ⛔ **le porte occupate** | 7448 · **7700** · 7710 — un banco nuovo prende la sua (07-b43 usa la 7720) |
> | **la parola di `prova`/`prova2`** | `prova2026`, dalla riga `chpasswd` di `src/provisiona.sh`. ⛔ **Non** quella di `credenziali-banchi`, che è del `prova2` **del contenitore** |
> | ⛔ **niente è stato messo in `git`** | ~2300 righe in 13 file modificati e 7 nuovi. **Va deciso dall'utente** |
>
> ## ⏳ E quel che resta aperto sull'audio, dichiarato
>
> - ⚠ **il cuscino di 250 ms** non è mai stato giudicato per sé: l'utente ha detto «risolto», non
>   «e il ritardo va bene». Se un giorno dà fastidio, la cura non è stringerlo ma togliere l'audio
>   dal thread principale (`AudioWorklet`);
> - ⏳ **il bitrate di Opus (96 kbit/s)** e il cuscino vanno a verbale in `DECISIONI.md`, che per
>   l'audio **non ha ancora un capitolo** (§7);
> - ⛔ **il banco `07-b43` va rifatto dopo tutte queste cure**: l'ultimo giro verde è di **prima**
>   delle otto modifiche al trasporto;
> - ⚠ e restano i due `[?]` della revisione (§6.4) e la **fase 6 non chiusa**.

---

## 0 · Che cosa deve produrre questa fase

| | |
|---|---|
| **l'audio** | il suono della sessione sul dispositivo dell'utente: **Opus**, con **PCM** come base sempre disponibile (`SPECIFICHE.md` §10, `RCP.md` §5.3) |
| **gli appunti** | testo semplice, **nei due versi** (`DECISIONI.md` §5-ter.1) |

⛔ **Fuori, e dichiarato**: il **microfono** (client → sessione). `SPECIFICHE.md` §10 lo dà per
non urgente e `RCP.md` §12 dichiara che *«il verso è previsto in §5, il formato non è definito»*.
Non si inventa un formato in questa fase.

⛔ **Fuori anche**: immagini e file negli appunti (`SPECIFICHE.md` §9, `DECISIONI.md` §5-ter.1).

### 0.1 · L'ordine di lavoro, deciso dall'utente

**Prima l'audio, poi gli appunti** (*«cominciamo con l'audio»*, 17 agosto 2026). Questo documento
è scritto per intero lo stesso, perché il banco si scrive prima e le due metà condividono un
pezzo — il **canale di controllo** e la **negoziazione** — ma il lavoro si fa in quest'ordine.

---

## 1 · Quel che già esiste, e non si riscrive

### 1.1 · Nel prodotto di V2, oggi

| | stato | dove |
|---|---|---|
| ✅ la **negoziazione** di `audio.codec` | **fatta e viva**: `opus,pcm` dichiarati dai due lati, intersezione, scarto scritto nel registro, `pcm` obbligatorio per entrambi | `src/rcp.c:1513-1816`, `src/pagina.html:3247` |
| ✅ la **negoziazione** di `appunti.testo` | dichiarata dai due lati (`si`) | `src/rcp.c:1527`, `src/pagina.html:3249` |
| ✅ il **rifiuto** dell'audio su uno stream | il canale `0x04` su uno stream è `ERRORE_PROTOCOLLO`, e la riga di registro lo nomina | `src/webtransport.c:2618`, `src/rcp.c:4258` |
| ✅ lo **scarto dichiarato** dei datagram | alla fase 1 si scartava scrivendolo nel registro, apposta perché *«la differenza fra "l'audio non arriva" e "l'audio arriva e lo butto" si vede solo se questa riga esiste da prima»* | `src/trasporto.c:333-357` |
| ⛔ il **verso di uscita** dei datagram | **NON ESISTE**: nessuna funzione manda un datagram. `webtransport.h` non ne ha una, e `wt_scrivi` non li tocca | — |
| ⛔ i **tre messaggi degli appunti** | **NON ESISTONO**: `0x0201/0x0202/0x0203` non compaiono in nessun file del prodotto. La pagina riceve uno stream `0x02` e scrive *«ricevuto e non usato»* | `src/pagina.html:3949` |
| ⛔ il **suono nella sessione** | **NON ESISTE**: nessun sink, nessuna cattura audio. `libpipewire` è già collegato, ma per i **fotogrammi** | `src/cattura.c` |

### 1.2 · Da v1, e sono le cose più intatte che il progetto abbia

| file | righe | che cosa vale |
|---|---|---|
| `v1/remotix-c/src/suono.c` + `.h` | 582 + 87 | ⭐⭐ **il pezzo più riusabile della fase**: crea il sink virtuale (`support.null-audio-sink`) e ne cattura il **monitor**. Non tocca RDP in nessuna riga |
| `v1/remotix-c/src/altoparlante.c` + `.h` | 892 + 117 | ⛔ **RDP dentro fino al collo** (`WTSVirtualChannelWrite`, `SendSamples2`, i formati di MS-RDPEA). ⭐ **Ma la forma si eredita**: la coda fra il thread PipeWire e il ciclo della connessione, il buttare **i campioni più vecchi**, il blocco intero per giro |
| `v1/remotix-c/src/appunti.c` + `.h` | 115 + 136 | lo smistamento fra le due strade |
| `v1/remotix-c/src/appunti_mutter.c` + `.h` | 450 + 28 | **GNOME**, che è il desktop di questa fase |
| `v1/remotix-c/src/appunti_wlr.c` | 796 | KDE, XFCE e LXQt — **fasi 11 e 12**, non questa |

⛔ **E la divisione che v1 aveva già trovato, e che qui vale identica**: *«il sink è della
SESSIONE, la cattura è della CONNESSIONE»* (`v1/…/suono.h`). È la stessa forma di I4: un
dispositivo audio che compare e sparisce a ogni riconnessione lascia le applicazioni già aperte
su un dispositivo morto.

---

## 2 · Il banco — ⛔ scritto PRIMA del prodotto

`PIANO.md` §0.3.4: *«il banco si certifica prima di essere creduto»*. E `PIANO.md` §«Fase 7» pone
tre regole che nascono da tre difetti veri di v1, non da prudenza.

### 2.1 · ⛔ Si ASCOLTA, non si contano i blocchi

`LEZIONI.md` §2.2, prima riga: *«il banco contava fotogrammi spediti e blocchi riscontrati; il
difetto cambiava **i campioni** — l'audio era rumore a fondo scala»*. Un banco che conta resta
verde per tutto il tempo in cui il difetto è vivo.

⇒ **Il giudice misura il segnale, non il traffico.**

| la scena | un **tono puro a 440 Hz**, ampiezza nota, suonato **dentro la sessione** su un'applicazione vera |
|---|---|
| **che cosa si misura** | la **frequenza dominante** e l'**ampiezza** dei campioni ricevuti dal lato client, dopo la decodifica |
| **l'atteso** | 440 Hz ± tolleranza, e l'ampiezza attesa entro la tolleranza del codificatore |

⛔ **E i quattro controlli positivi, scritti prima**, cioè le quattro forme in cui questo banco
**deve** dare rosso — sono le stesse che `RCP.md` §11 nomina:

| il guasto innestato | che cosa deve vedere il giudice |
|---|---|
| il server spedisce a **44 100 Hz** dichiarando 48 000 | la frequenza dominante si sposta |
| il PCM parte **big-endian** | il tono sparisce: rumore a banda larga, nessuna riga dominante |
| i canali **non interlacciati** | ⚠ da decidere che aspetto abbia: se il giudice non lo distingue, il caso non entra |
| il **silenzio** (nessun campione) | ⛔ e va distinto da *«ho ricevuto e non ho saputo leggere»*: `CODER.md` §3.10 — una misura che può dire zero deve poter distinguere lo zero dal fallimento |

⚠ **Il quarto è il più importante e il più facile da scrivere male**: senza di lui *«non ho
sentito niente»* e *«non ho guardato»* hanno lo stesso aspetto.

> ### ⛔⛔ E IL GIUDICE AVEVA UN DIFETTO CHE AVREBBE BOCCIATO CODICE GIUSTO
>
> *Trovato il 17 agosto 2026 dal banco dell'audio vero (`07-b43`), mentre lo scriveva.*
>
> **La purezza dipende dalla lunghezza della finestra.** `[M]` stesso file, stesso tono:
>
> | finestra | 0,25 s | 0,5 s | 1 s | 2 s |
> |---|---|---|---|---|
> | purezza | **0,2501** | **0,5001** | **1,000** | **1,000** |
>
> ⛔ La soglia del giudice è **0,80**. ⇒ Mezzo secondo di analisi avrebbe scritto *«non è un
> tono, è rumore — il difetto di v1»* **su un tono perfetto**. È `LEZIONI.md` §2.3: *«una prova
> che boccia il codice giusto costa quanto una che promuove quello sbagliato»*.
>
> ⭐ La cura non è alzare la soglia: è che il giudice **rifiuta** una finestra che non sia un
> numero intero di secondi, invece di giudicare su una finestra che non sa valutare.
>
> ⚠ E la ragione è aritmetica, non un difetto del Goertzel: 440 Hz in mezzo secondo non è un
> numero intero di periodi, e l'energia si sparpaglia sulle righe vicine. Il giudice misurava
> bene una cosa che non aveva senso misurare così.

> ### ⭐⭐ IL GIUDICE È CERTIFICATO — `[M]` 17 agosto 2026, **sei casi su sei**, su due motori
>
> `banchi/07-b40-sonda-audio.html`, funzione `giudica()`: frequenza dominante (Goertzel, passo
> 1 Hz, 100-2000 Hz), ampiezza RMS, e ⭐ **la purezza** — quanta parte dell'energia sta nella
> riga dominante, che è ciò che distingue **un tono da rumore a fondo scala**, cioè il difetto
> di v1 che nessun conta-blocchi vedeva (`LEZIONI.md` §2.2).
>
> | # | il caso | `hz` | `rms` | purezza | verdetto |
> |---|---|---|---|---|---|
> | **0** | ⭐ sano, 48 000 Hz | **440** | 0,3536 | **1,000** | ✅ verde |
> | **1** | 44 100 Hz spacciati per 48 000 | **479** | 0,3536 | 0,975 | ⛔ **visto** |
> | **2** | PCM big-endian riletto little | 1000 | 0,5644 | **0,142** | ⛔ **visto** |
> | **3** | canali **non** interlacciati | 880 | 0,3536 | 0,500 | ⛔ **visto** |
> | **4** | silenzio (campioni a zero) | 0 | **0** | — | ⛔ **visto** |
> | **5** | non ho letto niente | — | — | — | ⭐ **`NIENTE DA GIUDICARE`**, esito a sé |
>
> ⛔ **E l'atteso del caso 1 scritto qui sopra era SBAGLIATO, in direzione.** Questo documento
> prediceva *«440 × 44100/48000 ≈ 404 Hz»*; la misura dà **479**, che è 440 × 48000/44100. ⚠ Un
> campionamento più **lento** spacciato per uno più veloce fa suonare il tono **più acuto**, non
> più grave. ⇒ La predizione stava scritta **prima** della misura, ed è la ragione per cui
> l'errore si vede invece di sparire: `LEZIONI.md` §1.11.
>
> ⭐ **Il caso 2 è quello che conta**: il big-endian **non** si riconosce dalla frequenza — il
> giudice legge 1000 Hz, un numero perfettamente rispettabile — ⛔ **si riconosce dalla
> purezza, 0,142 contro 1,000**. Un giudice che guardasse la sola frequenza dominante avrebbe
> dato **verde a un rumore a fondo scala**, che è letteralmente il difetto di v1.

### 2.2 · ⛔ I due lati si sincronizzano con MARCATORI, non con `sleep`

`LEZIONI.md` §2.3-quinquies: al banco degli appunti di KDE i due lati erano sfasati di **tredici
secondi**, e il controllo dava **rosso su codice che funzionava**. Un file che il primo tocca e il
secondo aspetta costa tre righe.

### 2.3 · ⚠ La clipboard si SVUOTA all'inizio di ogni giro

Stesso §2.3-quinquies, il corollario: quel che resta dal giro prima viene annunciato alla
connessione **e sembra un risultato**.

### 2.4 · ⛔ Il lato indipendente degli appunti NON c'è — *corretto il 17 agosto 2026, misurando*

> ⛔⛔ **QUESTO PARAGRAFO DICEVA IL CONTRARIO, E LA MISURA LO HA SMENTITO.**
> Diceva: *«il lato indipendente c'è già, ed è gratis — `STUDI.md` §gnome §10 `[R]`: la sponda X11
> di Mutter è incondizionata nei due versi ⇒ **`xclip` funziona senza una nostra sessione**. È
> l'arbitro esterno che a questa fase serviva e che non credevamo di avere.»*
>
> ⛔ `[M]` 17 agosto 2026: il compositore gira come **`gnome-shell --headless --no-x11`**, cioè
> **XWayland non parte affatto**. La riga di `STUDI.md` è vera del **codice** di Mutter e falsa
> delle **nostre sessioni** — ed è una `[R]` letta nel sorgente, non una `[M]` presa sulla
> macchina.
>
> ⚠ E il ripiego su un client Wayland vero (GTK) non regge neanche lui: per possedere la selezione
> serve il *serial* di un evento d'ingresso, e in una sessione headless non arriva a nessuno.
>
> ⇒ 📖 **§6.9**, che è il capitolo che insegna: i tre tentativi, la causa vera, e perché REMOTIX ci
> riesce lo stesso.

⇒ **Che cosa resta.** Il verso `dispositivo → sessione` un arbitro ce l'ha — il **cliente di
prova**, che ha letto solo `RCP.md` (`PIANO.md` §1.1). ⛔ Il verso `sessione → dispositivo` no, e
oggi lo giudica **l'utente**: è l'invariante I8, non un ripiego.

### 2.5 · ⛔ E il secondo lettore resta il cliente di prova

`PIANO.md` §1.1: il cliente di prova (`banchi/01-b3-cliente.py`, in Python, scritto leggendo solo
`RCP.md`) **cresce con le fasi**. I messaggi nuovi di questa fase — il datagram `0x0401` e i tre
degli appunti — ci entrano, o il filo di questa fase sarebbe validato da **una sola**
implementazione. E il **validatore** (`banchi/01-b4-validatore.py`) impara le stesse inquadrature.

---

## 3 · Le domande da chiudere PRIMA di scrivere l'audio

⛔ Sono quattro, e **tre cambiano quel che si scrive**. `PIANO.md` §1.2 chiama questa cosa «la
sonda», e la regola che porta è di `LEZIONI.md` §1.11: *per ogni prova indiretta si scrive prima
che aspetto avrebbe il contrario*.

| # | La domanda | Che cosa decide | stato |
|---|---|---|---|
| **A1** | ⛔ il browser **decodifica Opus**? `AudioDecoder` di WebCodecs con `codec: "opus"`, su Chrome e su Firefox | se Opus è una strada o solo una dichiarazione. ⚠ Se **no su un motore**, `RCP.md` §4.3 ha già la risposta pronta: si negozia **`pcm`**, che è la base obbligatoria per entrambi — **non è un ripiego improvvisato, è il meccanismo** | ✅ **CHIUSA** `[M]` 17 ago — §3.2 |
| **A2** | ⛔ **quanti byte porta davvero un datagram** su ciascun motore | `RCP.md` §5.3 la dichiara `[?]` **per nome**: il PCM è dimensionato a **5 ms = 972 byte** su un carico utile stimato `[S]` ~1200. ⛔ Se il numero vero fosse più basso, **il PCM scende ancora** — e il PCM è il controllo positivo di Opus | ✅ **CHIUSA** `[M]` 17 ago — §3.3 |
| **A3** | come si **suona** nella pagina senza accumulare ritardo | `AudioContext` + `AudioWorklet` con un anello, o `decodeAudioData`. ⚠ Il riferimento ha un **regolatore di latenza a 300 ms** (`STUDI.md` §gnome §11): per noi è **sei volte il tetto del video** — si guarda, non si copia | ⏳ **da progettare** |
| **A4** | il **sink** e il **monitor**: la trappola del volume | ⭐ **già chiusa da v1, e con una misura**: `monitor.channel-volumes = "true"` fra le proprietà del sink, o il volume **non arriva, muto compreso** (`STUDI.md` §kde §10.5, `LEZIONI.md` §5) | ✅ `[M]` 8 ago 2026 |

### 3.2 · ⭐⭐ A1 è CHIUSA — Opus si decodifica su tutt'e due i motori, **misurato non dichiarato**

`[M]` 17 agosto 2026, `banchi/07-b40-lancia.py chrome|firefox`.

⛔ **`isConfigSupported` dice `true` su tutt'e due, e non è la risposta**: è una dichiarazione, e
`CODER.md` §3.9 vieta di crederci. ⇒ Si è fatto **il giro vero**: si codifica un tono a 440 Hz in
Opus, si danno al decodificatore i **pacchetti nudi** — nessun contenitore, come impone
`RCP.md` §6.3 (*«un datagram, un blocco di Opus»*) — e si giudica **quel che esce**.

| | Chrome 151 | Firefox 140esr |
|---|---|---|
| `AudioDecoder` / `AudioEncoder` / `AudioWorklet` | ✅ tutti | ✅ tutti |
| pacchetti codificati (50 blocchi da 20 ms) | 51 | 51 |
| ⭐ **frequenza dominante decodificata** | **440 Hz** | **440 Hz** |
| ⭐ **ampiezza RMS** (attesa **0,3536**) | **0,3504** | **0,3510** |
| byte per pacchetto, min-max (96 kbit/s, stereo) | **241 - 376** | **309 - 439** |
| errori di codifica o decodifica | nessuno | nessuno |

⇒ ⭐ **Opus è una strada vera, non una dichiarazione**, e il decodificatore accetta i pacchetti
**senza contenitore** — che è la forma in cui il protocollo li manda.

⚠ **E tre cose vanno dette invece che taciute:**

1. ⛔ **è un browser di banco, non il dispositivo dell'utente**: `HeadlessChrome/151` e
   `Firefox/140` su questo portatile. È la forma d'errore **E10** (`REVIEWER.md`), e la regola
   di `PIANO.md` §1.2 è *«si sviluppa sull'emulatore, si misura sul telefono»*. ⭐ Il giro su
   **Chrome 151 non headless** (il browser vero dell'utente su questa macchina) è stato fatto e
   dà gli stessi numeri; ⛔ **su Samsung DeX e sul telefono resta `[?]`**, e il telefono ce l'ha
   l'utente;
2. ⚠ **il giro misura il decodificatore con il NOSTRO codificatore del browser**, non con
   `libopus` del server: i due possono divergere. La prova che chiude questo punto è il banco
   della fase, non la sonda;
3. ⚠ **`byte per pacchetto` è a 96 kbit/s scelti da noi**: non è il bitrate del prodotto, che
   non è ancora deciso.

### 3.3 · ⛔⭐ A2 è CHIUSA, e il numero è **più basso della stima** — ma il PCM sopravvive

`[M]` 17 agosto 2026, contro il **server vero** (`https://192.168.0.2:7700/rcp/1`, prodotto vivo
sulla macchina di prova), impronta pubblicata, nessuna credenziale e nessuna sessione: si apre, si
legge `datagrams.maxDatagramSize` e si congeda.

| | Chrome 151 | Firefox 140esr |
|---|---|---|
| subito dopo `ready` | **1024** byte | **1024** byte |
| dopo 800 ms | **1024** byte | ⭐ **1214** byte |
| il PCM di §5.3 ne chiede (12 + 480×2) | 972 | 972 |
| ⭐ **ci sta?** | **sì**, margine **52 byte** | **sì**, margine **242 byte** |

⛔ **`RCP.md` §5.3 stimava `[S]` «~1200 byte» e la stima era ottimista di un quinto su Chrome.**
La riga di §5.3 che apriva la `[?]` — *«se il numero fosse più basso di 972, il PCM scende
ancora»* — **non scatta**: 1024 > 972. ⭐ Ma il margine su Chrome è **52 byte**, cioè il PCM di
questo protocollo sta dentro il datagram di Chrome **per meno del 6 %**.

⚠ **E i due motori non danno lo stesso numero, né lo stesso numero nel tempo**: Firefox parte da
1024 e **cresce a 1214** quando ha misurato il percorso. ⇒ ⛔ **Chi dimensionasse i blocchi
leggendo `maxDatagramSize` una volta sola, subito dopo `ready`, prenderebbe il numero peggiore e
non lo saprebbe.** Il blocco del PCM però è **fisso in specifica**, non negoziato: qui il numero
serve a sapere che ci sta, non a scegliere.

`[?]` **Quel che resta aperto, e non si estrapola**: questa misura è su **rete locale, cavo**.
Su rete mobile — dove `SPECIFICHE.md` §3.1 mette lo scenario dei 30 Mbps — il percorso può
portare meno. ⛔ Il PCM a 972 byte è la strada che **non ha margine**, ed è proprio quella su cui
si ripiega quando Opus non si negozia.

### 3.4 · ⛔ E una quinta domanda, che non è del browser ma della nostra architettura

**Da dove escono i campioni.** Il sink e la cattura vivono nel **figlio** (`src/figlio.h`), che è
l'unico processo che ha il bus di sessione e `/run/user/<uid>`; i datagram li scrive il **padre**,
che tiene la connessione QUIC. ⇒ Serve un messaggio nuovo sul socket fra i due — la forma è quella
di `FiglioDeposito`, che già porta i fotogrammi.

⚠ **E la regola di v1 vale identica qui, ed è la ragione per cui c'è una coda**: il thread di
PipeWire gira **in tempo reale**, e chi ci scrive dentro una chiamata che aspetta *«non ferma
soltanto l'audio: fa saltare il quanto a tutto il grafo PipeWire, cattura del desktop compresa»*
(`v1/…/suono.h`). Si copia e si torna.

⛔ **E la priorità è del sistema, non del processo**: `LEZIONI.md` §5 — *«il percorso audio vuole
tempo reale, e va concesso dall'unità di sistema; un processo senza quel permesso non può
chiederlo, e il sintomo è audio che scoppietta quando il desktop lavora»*.

---

## 4 · Che cosa è stato sviluppato

### 4.1 · Il banco, prima del prodotto — **17 agosto 2026**

| file | che cos'è |
|---|---|
| `banchi/07-b40-sonda-audio.html` | la **sonda dell'audio**: capacità dichiarate, il **giro vero** Opus (codifica → pacchetti nudi → decodifica → giudizio), la misura del **datagram** contro il server vero, e ⭐ **il controllo positivo del giudice** — sei casi, cinque guasti innestati |
| `banchi/07-b40-lancia.py` | il lanciatore: serve la pagina su `http://localhost` (contesto sicuro su tutt'e due i motori), apre **il motore che gli si nomina**, e aspetta il **portatore** invece di leggere uno scatto. ⛔ Verifica dallo `user agent` che a rispondere sia stato quello chiamato (`CODER.md` §3.9) |

⛔ **Del prodotto non era stata scritta una riga**, ed era voluto: `PIANO.md` §0.3.4 — il banco si
certifica prima di essere creduto. Il prodotto è §4.2.

### 4.2 · Il prodotto — **17 agosto 2026**, il verso d'uscita dei datagram

| file | che cosa fa |
|---|---|
| ⭐ `src/audio.c` + `.h` (nuovi, ~250 righe) | il **codificatore**: Opus per `libavcodec` (encoder `libopus`, chiesto **per nome**), PCM s16 **little-endian scritto a mano** — non con una `memcpy`, che darebbe l'ordine della macchina |
| ⭐⭐ `src/webtransport.c` | il **verso d'uscita dei datagram**, che non esisteva: la coda (8 blocchi, e chi non ci sta si **butta** — §6.3 vieta la ritrasmissione), il prefisso di **RFC 9297**, l'inquadratura di §6.3, `wt_audio_diffondi()` con la guardia **I3**, e `audio_regola()` che accende il canale |
| `src/rcp.c` + `.h` | `rcp_audio_negoziato()`: da `opus`/`pcm` ai numeri `1`/`2` di §6.3, **in un posto solo** |
| `src/main.c` | `--audio-prova <hz>`: la sorgente di prova, **spenta** se nessuno la accende (I6) |
| ⭐ `src/pagina.html` | il **ricevente**: legge i datagram, applica §6.3 (corti · tipo · **istante non più recente**), decodifica Opus con `AudioDecoder` o srotola il PCM, e suona con un cuscino di **60 ms** |
| `banchi/01-b3-cliente.py` | ⭐ il **secondo lettore cresce con la fase** (`PIANO.md` §1.1): riceve i datagram e tiene **sei contatori**, uno per ogni regola di §6.3 che può essere violata |
| `banchi/07-b41-accendi.sh` · `07-b42-giudice.py` | il server del banco (porta, ban-file e socket **propri**) e il giudice che *ascolta* |
| ⭐ `banchi/07-b43-audio-vero.sh` · `07-b43-giudizio.py` | il banco dell'audio **vero**: la sessione suona, il client raccoglie, il giudice ascolta. Porta **7720**, albero e socket propri |
| ⭐ `banchi/07-b44-ritardo-opus.c` | il programma minimo che chiede a `libopus` **una cosa sola**: accumula i blocchi? (`CODER.md` §3.6) |

### 4.3 · La cucitura fra padre e figlio — **17 agosto 2026**

⛔ **L'audio attraversa un confine di processo, ed è la terza volta che succede per la stessa
ragione** — dopo `MSG_VIDEO` (fase 3) e `MSG_INPUT` (fase 4). Ormai è una legge
dell'architettura, non una scelta: **PipeWire parla con la sessione dell'utente, e quella sta nel
figlio**; i datagram li scrive **il padre**, che tiene QUIC.

| | |
|---|---|
| `MSG_AUDIO` (padre → figlio) | *«cattura l'audio, e codificalo così»* — `0` = spegni |
| `MSG_BLOCCO` (figlio → padre) | un blocco **già codificato**, con il suo `istante` |

⛔ **E il figlio codifica PRIMA di mandare**, invece di spedire i campioni crudi. Non è
un'ottimizzazione qualunque: 20 ms di PCM stereo sono **3840 byte**, lo stesso blocco in Opus ne
misura `[M]` **241-439**. Spedire crudo costerebbe **dieci volte** il socket, cinquanta volte al
secondo.

⛔⭐ **E la cosa che governa tutto il disegno è un vincolo, non un'architettura**: il richiamo dei
campioni gira sul **thread di PipeWire, in tempo reale**. Chi ci scrive dentro una chiamata che
aspetta *«non ferma soltanto l'audio: fa saltare il quanto a tutto il grafo PipeWire, cattura del
desktop compresa»*. ⇒ Fra i due c'è un **anello a un produttore e un consumatore**, senza
lucchetti — il produttore muove solo `testa`, il consumatore solo `coda`, e i due indici sono
atomici. ⚠ E nel richiamo **non si scrive nel registro**: il traboccamento si *conta* lì e si
*scrive* dal ciclo.

⭐ **Tre decisioni che il codice porta con la loro ragione accanto:**

1. **il sink è della sessione, il codificatore della connessione** — I4. Spegnere ferma la
   cattura, **non** il sink: farlo sparire a ogni distacco interromperebbe il suono a chi ascolta
   *dentro* la sessione e lascerebbe le applicazioni su un dispositivo morto;
2. **l'orologio dell'audio è il conto dei campioni**, non `CLOCK_MONOTONIC`. §6.3 vuole *«l'istante
   del primo campione»*; l'ora di parete al momento dell'invio metterebbe nel campo **quando l'ho
   spedito**, e il client riordinerebbe sul nostro jitter invece che sul suono. ⛔ E quando
   l'anello trabocca **la base si sposta dei campioni persi**, o gli `istante` racconterebbero un
   suono continuo dove c'è stato un buco;
3. ⛔ **l'audio si svuota PRIMA della parte video**, che esce con `continue` quando nessuno guarda.
   Altrimenti *«audio acceso, video spento»* non suonerebbe e **nessuna riga direbbe perché** — ed
   è il caso di chi ascolta musica con la scheda in secondo piano. ⚠ Per la stessa ragione il
   ciclo, con l'audio acceso, non può più dormire un secondo: l'anello si riempie a 48 000
   fotogrammi al secondo **anche col desktop fermo**.

### 4.4 · `suono.c` — il sink e la cattura, portati da v1 · **17 agosto 2026**

**869 righe**, compila pulito. ⛔ **Nella sessione non c'è niente da catturare e va creato**: `[M]`
5 agosto 2026, con `pipewire`, `pipewire-pulse` e `wireplumber` tutti attivi, `wpctl status` mostra
**zero device, zero sink, zero source** — è il caso normale di un server senza scheda sonora.
⚠ Il riferimento (`gnome-remote-desktop`) apre la cattura sui sink che **trova** e un sink non lo
crea mai: col suo codice, qui, non arriverebbe un campione — e senza un errore da nessuna parte.

> #### ⛔⛔ E IL PORTO HA TROVATO UN DIFETTO IN v1: **l'attesa che non aspettava**
>
> `suono_ascolto_ferma()` di v1 dichiarava *«il lucchetto del ciclo **è** l'attesa»*, e su quella
> riga poggiava il permesso di liberare il contesto della connessione.
>
> ⛔ **È falsa con `PW_STREAM_FLAG_RT_PROCESS`**: la richiamata arriva dal **thread dei dati**, che
> quel lucchetto non ferma `[R]` (`pipewire/stream.h:150` e `:466`). ⇒ Chi tornava da lì poteva
> liberare la memoria **mentre il thread di tempo reale ci stava ancora scrivendo** — un difetto
> che si presenta una volta ogni tanto, alla chiusura, cioè dove nessuno guarda.
>
> ⭐ **Adesso l'attesa è in due tempi**: si spegne un flag atomico di consegna e si aspetta che il
> richiamo sia davvero uscito; **poi** si distrugge il flusso. Con un tetto di 2 s, e se scade si
> esce **dichiarando «⛔ NON liberare il contesto»** invece di appendere la sessione.
>
> ⚠ E una seconda cosa che v1 faceva e qui non si fa: **stampare dal thread di tempo reale**. Una
> riga di registro è una `vsnprintf` più una `write`, cioè esattamente la chiamata che non si può
> fare lì. ⇒ Il thread conta, e quel che v1 stampava **si chiede da fuori**.

⚠ **E quel che `suono.c` NON accumula, dichiarato**: consegna i fotogrammi come PipeWire glieli dà
(~256 per richiamo, e il numero **varia**). L'accumulo in blocchi da 960 o 240 lo fa l'anello nel
figlio — una seconda memoria intermedia per lo stesso mestiere avrebbe deciso *quando* il suono
parte, che è di chi spedisce, e allo spegnimento avrebbe buttato in silenzio fino a 959 fotogrammi.

⛔ **Non è stato eseguito niente**: l'agente non aveva una sessione grafica. Che il sink compaia,
che il monitor consegni campioni e che `monitor.channel-volumes` funzioni **su questa macchina**
sono `[?]`, e li chiude il banco.

---

### 4.5 · ⭐⭐ GLI APPUNTI — **17 agosto 2026, sera**, e sono la seconda metà della fase

*Ordine di lavoro dell'utente: «prima l'audio, poi gli appunti» (§0.1). L'audio è chiuso col suo
giudizio; questa sezione è quel che è stato scritto dopo.*

> ### ⛔ E LA DOMANDA DELL'UTENTE ERA «TESTO FORMATTATO» — chiusa prima di scrivere una riga
>
> L'apertura di questa sessione chiedeva *«la copia server↔client di **testo formattato**»*.
> ⛔ `DECISIONI.md` §5-ter.1 dice l'opposto, **con parole sue del 9 agosto**: *«per la clipboard ho
> idea precisa: solo testo»* — niente immagini, niente file, **niente formati ricchi**.
>
> ⚠ E non era una sfumatura: `RCP.md` §7.4 ha costruito i tre messaggi **senza nessun campo che
> dichiari il tipo**, e ci ha scritto accanto la ragione — *«non esiste perché non c'è niente da
> scegliere»*. Per l'HTML servirebbe quel campo, e §9 vieta di aggiungere campi a messaggi esistenti
> dentro una versione maggiore: **la finestra è chiusa dal 10 agosto**.
>
> ⭐ Chiesto all'utente prima di scrivere codice, e **ha scelto «solo testo semplice»**. ⇒ La
> decisione del 9 agosto regge, e questa riga esiste perché la prossima volta che qualcuno legge
> «formattato» sappia che la domanda è già stata fatta.

#### 4.5.1 · I sei file, e che cosa fa ciascuno

| file | che cosa porta |
|---|---|
| ⭐ `src/appunti.h` + `.c` (**nuovi**, ~640 righe) | il lato **Mutter**, portato da `v1/…/appunti_mutter.c` con le quattro trappole disinnescate sul posto. ⛔ Solo testo: i tipi MIME vivono lì dentro e non escono |
| `src/figlio.c` | quattro messaggi nuovi sul socket padre↔figlio (`APPUNTI_OFFERTA`, `APPUNTI_DAL_CLIENT`, `APPUNTI_DALLA_SESSIONE`, `APPUNTI_VUOLE`), il **terzo tavolo di montaggio** e il **fondo di tempo** di chi incolla |
| `src/rcp.c` + `.h` | i tre messaggi di §7.4, la tabella degli stream in arrivo, i cinque ganci nuovi, e la **cura della corsa con `Ctrl+V`** |
| `src/webtransport.c` + `.h` | il canale `0x02` in arrivo (`G_UNI_APPUNTI`) e i tre ganci che aprono uno stream verso il client |
| `src/main.c` | la **quarta cucitura** della stessa famiglia: video, input, audio, appunti |
| `src/pagina.html` | il lato browser: `clipboardchange` dove c'è, l'evento `paste` dove non c'è, e la scrittura negli appunti locali col ripiego dichiarato |

⭐ **E `mutter.h` ha una riga nuova sola**: `mutter_bus()`. Gli appunti vivono sulla **stessa**
sessione `RemoteDesktop` del palco, e aprire una seconda connessione al bus vorrebbe dire un secondo
nome sul bus — cioè un mittente che Mutter non riconosce come proprietario della sessione.

#### 4.5.2 · ⛔⭐⭐ LA CORSA FRA `Ctrl+V` E L'ANNUNCIO, e la cura NON è quella di Xpra

`SPECIFICHE.md` §9 la nomina e dichiara di **non** volerla risolvere come il riferimento:

> *«una trappola che tutti e tre i riferimenti letti disinnescano a mano: la corsa fra `Ctrl+V` e la
> lettura degli appunti. Xpra la risolve ritardando **ogni battuta di 100 ms** — ⛔ per noi sono
> **due volte il tetto del ritardo**: quella cura non si copia, si sostituisce.»*

**La corsa, per esteso.** L'utente batte `Ctrl+V` nel browser. I tasti partono sul canale di input;
l'annuncio degli appunti parte sul canale appunti e fa la stessa strada. ⛔ Ma il desktop, ricevuto
il `Ctrl+V`, chiede il testo **subito** — e l'annuncio può non essere ancora arrivato. ⇒ **La prima
incollata di ogni testo nuovo tornerebbe vuota**, e la seconda funzionerebbe: il sintomo peggiore
che ci sia, perché «a volte non va» non manda a cercare da nessuna parte.

⭐ **La sostituzione costa zero e non tocca nessun tasto**: la richiesta di incolla **si mette in
coda** invece di tornare vuota, e la domanda al client parte **quando l'annuncio arriva**
(`rcp.c`, `rcp_appunti_chiedi` e il ramo `T_APPUNTI_ANNUNCIO` di `tratta_appunti`).

⚠ E l'attesa è limitata da qualcun altro, non da un timer nostro in più: il **fondo di 4 s del
figlio** risponde «non ce l'ho» a chi incolla se l'annuncio non arriva mai.

#### 4.5.3 · ⛔ I DUE FONDI DI TEMPO, e sono due perché i debiti sono due

Questa è la parte che nessun banco avrebbe chiesto e che il prodotto sì.

| dove | quanto | che debito paga |
|---|---|---|
| ⛔ **nel figlio** (`figlio.c`, `APPUNTI_ATTESA_MS`) | **4000 ms** | il debito verso **Mutter**. Un `SelectionTransfer` senza risposta lascia appesa **a tempo indeterminato** l'applicazione che sta incollando, e quel che l'utente vede è **un desktop piantato** — un difetto che nessuno collega agli appunti |
| ⚠ **nel padre** (`rcp.c`, `APPUNTI_FONDO`) | **8000 ms** | che il **canale** non resti bloccato. Senza, un client che non risponde una volta manda in coda **tutte le incollate successive**: «gli appunti hanno funzionato una volta e poi mai più» |

⭐ **E il fondo verso Mutter sta nel FIGLIO, non nel padre**, per una ragione che non è di comodità:
il padre può non avere nessun client attaccato (la sessione sopravvive al client — invariante I4), il
client può sparire a metà trasferimento, e il padre stesso può morire. ⛔ Il debito verso il
compositore invece resta di chi ha la sessione, **e la sessione è nel figlio**.

⚠ E i due numeri sono diversi **apposta**: stringerli fino a coincidere li farebbe scadere insieme,
e un testo arrivato al millesimo giusto non troverebbe più nessuno da servire da nessuna delle due
parti.

#### 4.5.4 · 🔸 Dove §2.5 ammetteva due letture, e quale si è presa

`RCP.md` §2.5 dice che il canale appunti vuole uno stream *«uno **per trasferimento**»*. ⚠ Un
trasferimento dalla nostra parte è fatto di **due messaggi lontani nel tempo** — `APPUNTI_ANNUNCIO`
adesso, `APPUNTI_TESTO` **se e quando** qualcuno chiede.

⇒ Si è presa la lettura **uno stream per messaggio**, e la ragione è un conto: si copia molto più
spesso di quanto si incolli, quindi tenere aperto uno stream fra i due messaggi vorrebbe dire
tenerlo aperto **per sempre** nella stragrande maggioranza dei casi — e §2.5 concede al server un
numero finito di stream.

⭐ **E si può fare, perché a legare i messaggi di un trasferimento NON è lo stream**: è il campo
`trasferimento`, che esiste esattamente per questo (rilievo R1.11, 9 agosto 2026).

⚠ Il prezzo, dichiarato: un client che contasse gli stream per contare i trasferimenti conterebbe il
doppio. Nessuna riga di `RCP.md` gli dice di farlo, e il campo che deve guardare ce l'ha. ⭐ Il
cliente di prova ha fatto **la stessa scelta leggendo solo il documento**, il che dice che la riga è
ambigua ma che l'ambiguità non morde.

#### 4.5.5 · ⛔ Due valori che venivano LETTI E BUTTATI, e la stessa forma del rilievo B-1

| dove | che cosa succedeva |
|---|---|
| `src/rcp.c` (`CIAO`) | `appunti.testo` era in `NOMI_NOTI` come nome lecito e il **valore veniva buttato**. ⇒ Il server non poteva né evitare di annunciare a chi non li aveva chiesti, né rifiutare byte sul canale `0x02` da un client che non li aveva dichiarati — cioè **una capacità usata senza negoziarla**, che è il caso che §4.3 esiste per rendere impossibile |
| `src/pagina.html` (`ECCOMI`) | idem: la pagina lo stampava nella riga dell'`ECCOMI` e non lo teneva da nessuna parte. ⇒ Non avrebbe potuto accendere niente |

⚠ È **la stessa forma del rilievo B-1** su `video.misura_massima` (10 agosto 2026): un valore del
protocollo che si dichiara di aver capito e non si ha da nessuna parte.

---

## 5 · Le misure

*(si riempie strada facendo — la scena dichiarata accanto a ogni numero)*

| che cosa | atteso | misurato | data |
|---|---|---|---|
| ⭐ **il codificatore Opus non costa una dipendenza nuova** | — | `libavcodec` **61.19.101** sulla macchina di prova **è collegato a `libopus.so.0`**, e `ffmpeg -encoders` dichiara **`libopus`** (oltre al nativo `opus`, sperimentale). ⇒ `avcodec_find_encoder_by_name("libopus")`, e il `Makefile` **non cambia** | `[M]` 17 ago 2026, dentro `enter.sh --root` sulla macchina di prova |
| ⚠ **e `opus.pc` NON c'è** | — | nessun `libopus-dev` in `devroot`: la strada dell'API nativa di libopus **costerebbe un pacchetto su due ambienti di costruzione** (il contenitore del portatile e il `devroot` della macchina di prova) | `[M]` 17 ago 2026 |
| ⭐⭐ **il browser decodifica Opus** (A1) | ⏳ ignoto | **440 Hz**, RMS **0,3504** (Chrome 151) e **0,3510** (Firefox 140esr), contro 0,3536 attesa — pacchetti **nudi**, nessun errore. Scena: 50 blocchi da 20 ms, tono 440 Hz ampiezza 0,5, 48 kHz stereo, giro codifica→decodifica dentro il browser | `[M]` 17 ago 2026, `07-b40`, **due motori** |
| ⭐⭐ **il giudice vede i guasti** | 5 su 5 | ⭐ **6 casi su 6**: sano verde, quattro guasti visti, e `NIENTE DA GIUDICARE` come esito a sé. ⛔ Il big-endian si riconosce **dalla purezza (0,142)**, non dalla frequenza | `[M]` 17 ago 2026, `07-b40`, due motori |
| ⛔ **quanti byte porta un datagram** (A2) | `[S]` ~1200 | **1024** su Chrome 151 (fisso) · **1024 → 1214** su Firefox 140esr. Scena: server **vero** sulla macchina di prova, porta 7700, rete locale via cavo, nessuna sessione aperta | `[M]` 17 ago 2026, `07-b40 --wt` |
| ⭐ **il PCM di §5.3 ci sta** | ci deve stare | **sì su tutt'e due**, margine **52 byte** su Chrome e **242** su Firefox | `[M]` 17 ago 2026 |
| ⭐⭐ **il filo dell'audio, PCM** | 200 blocchi/s, 440 Hz | **1000 blocchi su 1000** in 5,000 s — **resa 100,0 %**, passo fra gli `istante` **sempre 5000 µs**, zero fuori passo. Segnale: **440 Hz**, RMS **0,3535** (attesa 0,3536), **purezza 0,9963** | `[M]` 17 ago 2026, `07-b41` + `01-b3-cliente` + `07-b42` |
| ⭐⭐ **il filo dell'audio, Opus** | 50 blocchi/s | **251 blocchi** in 5 s (50,2/s = i 20 ms di §5.3), **279-439 byte** per pacchetto a 96 kbit/s | `[M]` 17 ago 2026 |
| ⭐⭐⭐ **i pacchetti del NOSTRO server decodificati dal BROWSER** | — | **440 Hz**, RMS **0,3515**, purezza **0,997**, su **Chrome 151 e Firefox 140esr**, 251 pacchetti su 251, zero errori. ⛔ Non i pacchetti che il browser aveva codificato da sé: quelli usciti da `libopus` dentro il server, presi **dal filo** | `[M]` 17 ago 2026, `07-b40 --pacchetti` |
| ⭐⭐ **la catena VERA è viva** (sink → monitor → Opus → socket → datagram) | 50 blocchi/s | **397 blocchi in 8 s = 49,6/s**, zero persi, zero scartati. Il sink compare in `wpctl status` come **predefinito**, `monitor.channel-volumes: true`. Scena: sessione GNOME di `prova2` sul server, tono di prova **spento** | `[M]` 17 ago 2026, porta 7710 |
| ⭐⭐⭐ **e il suono della sessione ARRIVA** | 440 Hz | ⛔ *La prima misura diceva «silenzio», ed era la SCENA a essere rotta — vedi §6.5.* Con la scena certificata: `suono.c` consegna **PICCO 16383 su 32767** (= metà fondo scala, l'ampiezza esatta del tono) e i tratti contigui danno **440 Hz, rms 0,3535** — identici a quel che legge `pw-record` sullo stesso monitor | `[M]` 17 ago 2026, `07-b43` |
| ⭐⭐ **e il volume GOVERNA** | I5 e §kde §10.5 | volume pieno **0,3536** · al 25 % **0,0078** (atteso 0,005525) · muto **0,0**. ⇒ La trappola del monitor a monte del volume **non c'è**: `monitor.channel-volumes` è chiesta e funziona | `[M]` 17 ago 2026, `07-b43`, contro il prodotto |
| ⭐⭐⭐ **il banco dell'audio vero: 5 giri su 5** | l'atteso scritto **prima** | **1-sano** 440 Hz rms 0,3535 (atteso 0,3536) · **2-silenzio** 0 Hz rms 0,0 · **3-frequenza** 660 Hz · **4-volume-25** rms **0,0055** (atteso 0,0055) · **5-muto** 0,0. ⛔ E i giri 2 e 3 sono difetti **innestati apposta**: il banco li vede, quindi non è cieco | `[M]` 17 ago 2026, `07-b43`, contro il prodotto |
| ⭐⭐ **e RIFATTO dopo le otto cure al trasporto** | 5 su 5 | **5 su 5**, e ⭐ **meglio di prima**: la purezza è **1,000** su tutti i giri con segnale (era **0,29** quando i blocchi si perdevano), e il giudice ha potuto guardare **96 000 campioni** invece di 48 000 — perché adesso c'è abbastanza suono **contiguo** da giudicare. ⛔ Rifarlo non era una formalità: l'altro verde era di **prima** che si toccassero la coda dei datagram, il tetto ai rinvii, la coalescenza e il riempimento — cioè un verde vecchio su un codice nuovo | `[M]` 17 ago 2026, sera |
| ⭐ **il datagram che non partiva** | 0 % di perdita | da **38,5 %** a **0,3 %**: 2994 spediti, 8 rifiutati, 1 buttato per coda piena su ~3003. ⚠ Su **Opus** la perdita era già **zero** (0 su 747): il difetto mordeva il **PCM**, che costa 13 volte la banda | `[M]` 17 ago 2026 |
| ⭐ **libopus non accumula** | `[?]` | **1000 blocchi entrati, 1000 usciti, zero EAGAIN** ⇒ l'`istante` di §6.3 appartiene al blocco che parte | `[M]` 17 ago 2026, `07-b44` |
| ⚠ **il pre-skip di Opus** | non dichiarato da nessuno | `initial_padding` = **312 campioni = 6,50 ms**, **costante** su mille pacchetti. Il decodificatore lo toglie da sé, quindi end-to-end si cancella | `[M]` 17 ago 2026, `07-b44` |
| ⭐⭐ **gli appunti si aprono su una sessione GNOME VERA** | `EnableClipboard` concesso | ⭐ `appunti della sessione accesi (solo testo, nei due versi) su /org/gnome/Mutter/RemoteDesktop/Session/u1`. ⛔ È la prima e per ora **unica** prova che `appunti.c` funziona contro Mutter | `[M]` 17 ago 2026, porta 7730, utente `prova` |
| ⛔⛔ **XWayland NON esiste nelle nostre sessioni** | `xclip` doveva funzionare (§2.4) | `gnome-shell --headless --no-x11` ⇒ **nessuna sponda X11**. ⚠ I due socket in `/tmp/.X11-unix` sono avanzi del **15 agosto**: un banco che li avesse presi per buoni avrebbe misurato una sessione morta | `[M]` 17 ago 2026 |
| ⛔ **e nessun client Wayland ordinario possiede la selezione lì dentro** | l'arbitro doveva copiare | `wl-copy` dice **«This seat has no keyboard»**; un client GTK dice `COPIATO` ⛔ **e al compositore non arriva niente** — il prodotto, che è strumentato, non registra **nessun** `SelectionOwnerChanged`. ⚠ Nemmeno con una finestra presentata, e nemmeno con un client REMOTIX attaccato (cioè con la tastiera virtuale di libei presente) | `[M]` 17 ago 2026, tre tentativi |
| ⭐⭐ **la trappola del volume, riprodotta** | il volume deve arrivare | due sink gemelli, PipeWire **1.4.2**: con `monitor.channel-volumes=true` il monitor legge **0,3535 · 0,0055 · 0,0000** al 100 % · 25 % · muto; ⛔ **senza**, legge **0,3535 sempre, muto compreso** | `[M]` 17 ago 2026, `07-b43` |

---

## 6 · ⛔ Che cosa NON ha funzionato

*`PIANO.md` §0.3.2: si riempie anche quando fa una brutta figura.*

### 6.1 · Due difetti del banco nel primo pomeriggio, e tutt'e due mentivano sul MOTIVO

⭐ **Nessuno dei due dava un risultato sbagliato: davano il risultato giusto con la ragione
sbagliata scritta accanto** — che è la forma che costa mezza giornata quando si presenta su un
numero che conta.

| # | il difetto | come si presentava | la cura |
|---|---|---|---|
| **1** | il servente confrontava `self.path` **con la query dentro**: `/?wt=…` non è `/`, quindi **404** | *«nessun portatore in 45 s»* — cioè *«la pagina non è arrivata in fondo»*, mentre la pagina **non era mai stata servita** | si taglia la query prima del confronto |
| **2** | `wt.ready` **può non tornare mai**, né risolta né respinta, e la sonda non aveva tetto | anche qui *«nessun portatore»*: la scadenza del **lanciatore** scritta al posto della scadenza della **connessione** | un tetto di 10 s, con l'esito **`SCADUTA`** distinto dagli altri |

⇒ ⛔ **Due volte nello stesso pomeriggio il banco ha detto «non ho misurato» quando doveva dire
«ho misurato e non ci sono riuscito, ecco dove».** È `CODER.md` §3.10 — *«una lettura negata non
è una lettura che dice zero»* — trovata nello strumento scritto per applicarla.

⚠ **E il primo dei due si è visto solo perché la sonda funzionava già senza `--wt`**: il caso
sano esisteva da prima. Senza quel confronto, l'imputato sarebbe stato il motore.

### 6.2 · ⛔⛔ Una diagnosi sbagliata che «migliorava» — e mi ha quasi comprato una modifica

*È il difetto più istruttivo della giornata, e non è nel prodotto: è nel mio ragionamento.*

Il primo giro del tono dava **402 blocchi su 600** in 3 s — resa **67 %** — ⭐ con **zero blocchi
persi**: il passo fra gli `istante` era **sempre esattamente 5000 µs**. Ho concluso *«la coda dei
datagram è diventata il tetto del ritmo»* e l'ho portata da 8 a 32.

⭐ **La resa è salita a 80 %.** Cioè il numero è migliorato, e sembrava una conferma.

⛔ **Non confermava niente.** 2,01 s su 3 e 4,01 su 5 non sono una frazione: sono **T − 1**. Il
terzo punto l'ha deciso in trenta secondi — **9,01 s su 10**. ⇒ Non era una resa: era **un secondo
fisso in testa a ogni presa**, e la coda non c'entrava.

| | |
|---|---|
| **la causa vera** | il tono aspettava il **battito normale** di QUIC prima del primo blocco, perché `wt_battito_ns()` accorciava l'attesa solo *dopo* che il primo blocco era stato prodotto |
| **la cura** | due righe: il primo blocco è **dovuto subito** |
| **il risultato** | **1000 blocchi su 1000**, resa **100,0 %** |
| ⛔ **e il 32 è tornato 8** | `[M]` a 8 i blocchi persi erano **già zero**: era sufficiente. Un valore più alto sarebbe rimasto nel codice **senza una ragione**, giustificato da una diagnosi falsa |

⇒ ⭐ **La lezione è di metodo, e vale oltre l'audio**: *un numero che migliora non è una conferma*.
Due punti stanno su una retta per caso; il terzo costava trenta secondi. ⚠ E il sintomo — una
**percentuale** — indirizzava verso il *ritmo*, mentre il difetto era un **ritardo d'avvio**: due
posti completamente diversi del codice. La forma è quella di `LEZIONI.md` §1.9, *il rosso puntato
sull'imputato sbagliato*, in una variante nuova: **il verde parziale che sale**.

### 6.3 · E tre inciampi minori, con la loro causa

1. ⛔ **`printf … | sudo -S` si mangia lo `stdin`** — due volte nello stesso script: la prima ha
   fatto leggere al `tar` la parola d'ordine (*«gzip: stdin: not in gzip format»*), la seconda ha
   dato a `bash -s` uno stdin vuoto, ⚠ **e quella non ha dato nessun errore**: il passo stampava
   la sua intestazione e non faceva niente. *«Non ha fatto niente» aveva la stessa faccia di «ha
   funzionato»*;
2. ⛔ **ho spedito alla macchina di prova anche i `.o` del portatile**, e `make` non ha compilato
   niente. ⭐ **Il controllo `ldd` l'ha rifiutato** — è il suo mestiere — ma senza quel controllo
   avrei misurato il codice del portatile credendolo del server: il difetto **D5**;
3. ⛔ **la parola d'ordine di `prova2` l'ho presa dal file sbagliato**: `credenziali-banchi` è del
   `prova2` **del contenitore**, non di quello dell'host che PAM verifica. ⚠ **Era già scritto**,
   in `banchi/06-b38-tela.sh`, con le parole *«sono due utenti diversi con lo stesso nome, e le due
   parole si somigliano abbastanza da far perdere un'ora»*. Costo: **1 tentativo su 3** prima del
   ban di §4.4-bis.

---

### 6.3-bis · E tre difetti del banco dell'audio vero, trovati girandolo

⭐ Nessuno dei tre si vedeva leggendo il codice, e il terzo vale da solo:

1. `env $* $SUL_SERVER` metteva il nome del passo **prima** del comando ⇒ `env: 'cancello': No
   such file or directory`, uscita 127;
2. un passo scriveva in una cartella non ancora creata ⇒ *«No such file or directory»* travestito
   da *«non riesco a leggere il grafo»*;
3. ⛔ **`timeout 8 <funzione di shell>` esce 127**, perché `timeout` esegue un programma e una
   funzione non lo è. ⚠ Per due giri l'esito è stato letto come *«il sink non nasce»* — mentre il
   sink **non era mai stato chiesto**. È `LEZIONI.md` §1.9 in forma pura: il rosso puntato
   sull'imputato sbagliato, e l'imputato vero era il tetto messo nel posto sbagliato.

### 6.5 · ⛔⛔ «L'audio è silenzio» era una MIA misura rotta, e c'è voluta una refutazione

*17 agosto 2026. È il difetto più caro della giornata, e non era nel prodotto.*

Avevo misurato, e scritto, che la cattura consegnava silenzio: il sink c'era, le porte `monitor_*`
c'erano, `pw-play` arrivava al sink — ⛔ ma «nessun collegamento consumava il monitor» e «il nodo
della cattura non compariva nel grafo», mentre dichiarava 48 000 fotogrammi al secondo.

⭐ **Tre difetti di scena, tutti miei**, trovati da un agente mandato a refutare:

1. ⛔ **il tono non suonava affatto.** `pw-play` lo diceva per nome — *«no target node
   available»* — perché **il sink nasce col primo ascoltatore**, e nei miei giri partiva prima.
   Una scena che non suona misura il nulla;
2. ⛔ **le fotografie del grafo le scattavo a sipario chiuso**: l'attesa del marcatore non
   agganciava e consumava i suoi 45 s interi, così la sonda arrivava **~1 s dopo la fine della
   sessione**. Da lì «nessun nodo» e «nessun collegamento»;
3. ⛔ **avevo letto male `pw-mon`**: `removed: id 47` non era il nostro nodo, era un
   identificativo **riciclato**. Gli id globali di PipeWire si riusano.

⇒ ⭐ **E il punto 6 era vero e coerente**: la cattura consegnava correttamente il silenzio di una
sessione in cui non suonava nessuno. ⚠ *Due misure che si contraddicono, e a mentire era quella
che sembrava più solida*: `CODER.md` §3.11 dice esattamente di sospettare prima della misura.

⭐⭐ **E la cura non è stata una cura: è lo strumento che mancava.** In `suono.c` adesso c'è il
**picco del campione** — il più forte in valore assoluto — stampato nella riga di chiusura. Senza,
*«non si sente niente»* ha **due cause con la faccia identica** (48 000 fotogrammi/s consegnati, 0
scartati, flusso in `streaming`): *nessuno suonava* oppure *PipeWire ci dà buffer vuoti*. È
`CODER.md` §3.10 applicata al **campione** invece che al conteggio, e letta per prima chiude la
diagnosi in una riga.

⚠ **E cinque strade sono state provate e refutate con una misura, non con un ragionamento**: «è
un'altra istanza di PipeWire» (stesso `client.id`), «WirePlumber sospende il sink dopo 5 s»
(`suspend-timeout` a 0: rms ancora 0), «i buffer non sono condivisibili» (aggiunto `MemFd`: picco
ancora 0), «WirePlumber distrugge il nodo» (letto il componente: pretende flag che non mettiamo),
«un volume salvato a zero» (letto lo stato: tutto a 1,0).

### 6.6 · ⭐⭐ Il 38 % dell'audio che non partiva — e la causa scritta era sbagliata

`[M]` 17 agosto 2026, audio vero in **PCM** con il video acceso: **1163 datagram rifiutati su
3001**, e il giudice leggeva **464 Hz invece di 440** con purezza **0,29**. ⚠ Il suono non era
«con qualche buco»: concatenare quel che resta fa saltare la fase ogni due blocchi, ed **era un
altro suono**.

Il commento nel codice diceva: *«nel pacchetto non ci stava, quindi non ci starebbe mai»*.
⛔ **La misura dice il contrario**: `cwnd_left` = **12 198 byte** contro 973 chiesti, `destlen`
1452. ⇒ Non è né il buffer né la congestione: **è il pacer di QUIC**, che dice *«non adesso»*.
E «non adesso» diventa «mai» solo se lo buttiamo noi.

| la cura, in tre tempi | rifiutati |
|---|---|
| come stava — si buttava subito | **1163 su 3001** (38,5 %) |
| si RIMANDA invece di buttare (tetto 8) | 1064 su 2999 — ⛔ **quasi niente** |
| e il rimando si lega al **tempo**, non alle chiamate | 236 su 3001 (7,9 %) |
| ⭐ e il tetto dei rimandi sale da 8 a **64** | **8 su 3003** — e 1 buttato per coda piena ⇒ **0,3 %** |

⭐ **E il terzo passo l'ha chiesto il giudice, non io**: a 7,9 % di perdita leggeva ancora
**465 Hz**, ⛔ e quel numero *è* la perdita — concatenare i blocchi superstiti comprime il tempo,
e 440 / (1 − 0,054) ≈ 465. ⇒ La frequenza letta era un **misuratore di perdita**, non un difetto
del suono.

⚠ **E il tetto basso non proteggeva da niente**: il ritardo lo governa già la **coda** (otto
blocchi = 40 ms, e oltre si butta il più vecchio). Un tetto sui rimandi buttava un blocco che
sarebbe partito — due meccanismi per lo stesso mestiere, e quello sbagliato mordeva per primo.

⛔ **Il passo di mezzo è quello che insegna**: `ngtcp2_conn_write_aggregate_pkt2` richiama la
scrittura più volte per comporre un lotto, **con lo stesso `ts`**. Gli otto rimandi si consumavano
tutti lì dentro, in un microsecondo — senza che passasse **un istante** in cui il pacer potesse
cambiare idea. ⚠ E il conto sembrava dire il contrario: *8008 rimandi «riusciti»* accanto a 1064
blocchi buttati lo stesso.

### 6.7 · ⛔ Il banco si dichiarava CIECO, e aveva ragione — la scena non si zittiva

*Dopo la cura di §6.6 il prodotto dava **440 Hz esatti**, ⛔ ma il giro «2-silenzio» misurava
**440 Hz a 0,3535** — cioè il tono a pieno volume dove non doveva suonare niente.*

⭐ **E il banco non ha dato verde: si è dichiarato cieco.** *«Doveva vedere SILENZIO e ha detto
VERDE»* — cioè ha rifiutato di certificare gli altri quattro giri, che è esattamente il suo
mestiere: *un banco cieco dà verde a tutto*.

⛔ **La causa era la scena, non il prodotto**: `kill "$PP"` uccideva l'**involucro** (`setpriv`),
non `pw-play`, che sopravviveva e cantava **dentro il giro dopo**. ⚠ È la trappola che
`LEZIONI.md` §2.3-quinquies nomina per la clipboard — *«quel che resta dal giro prima va svuotato
all'inizio»* — e vale per ogni scena condivisa: il suono è una scena condivisa.

⭐ **E la cura non è uccidere: è verificare.** Il banco adesso legge dal grafo che i legami in
ingresso al sink siano **zero** prima di andare avanti. *«Ho ucciso»* e *«non suona più nessuno»*
sono due fatti diversi, e al giro dopo serve il secondo.

⇒ ⭐ **5 giri su 5**, e i due difetti innestati visti tutti e due.

### 6.8 · ⛔⛔⛔ IL DIFETTO VERO, E PERCHÉ CI SONO VOLUTE SETTE CURE PER ARRIVARCI

*17 agosto 2026. È il capitolo più caro della fase, e il difetto era in una riga.*

**Il difetto**: si spediva **un solo datagram per passata di scrittura**, e le passate sono ~25 al
secondo. Il figlio ne produce **50**. ⇒ Uno passava, uno restava in coda, e la metà dell'audio
moriva. ⛔ Non era la rete, non era il pacer, non era il video: **era il ciclo, che ne offriva uno
per volta**. E lo spazio c'era da vendere — un pacchetto è **1452 byte**, un blocco di Opus **230**:
il pacchetto restava mezzo vuoto mentre l'audio veniva buttato.

⭐ **La precisione del numero era l'indizio**: *esattamente* la metà. Una perdita di rete non è
mai esattamente la metà; un'aritmetica sì.

#### Le sei cure prima di quella giusta, e che cosa insegnano

| # | che cosa ho curato | l'esito | che cosa era |
|---|---|---|---|
| 1 | il rimando invece dello scarto | 38,5 % → 7,9 % | cura vera, ma a valle |
| 2 | il rimando legato al **tempo** e non alle chiamate | 7,9 % → 0,3 % *in locale* | cura vera |
| 3 | la coalescenza col pacchetto video (`MORE`) | nessun cambiamento per l'utente | ⛔ diagnosi sbagliata: *«il video si mangia la finestra»* — e i suoi fotogrammi erano da **70-1300 byte** |
| 4 | la priorità di tempo reale (**R26**) | nessun cambiamento | ⭐ difetto **vero e necessario**, ma non questo |
| 5 | il riempimento GSO (`PADDING`) | nessun cambiamento | ⭐ difetto vero, non questo |
| 6 | il pacchetto che buttavo con dentro i riscontri | nessun cambiamento | ⭐ difetto vero e grosso, non questo |
| ⭐ **7** | **più datagram nello stesso pacchetto** | 50 % → 18 % | **la causa** |
| ⭐ **8** | e il tetto ai rinvii tolto: **decide la coda** | 18 % → **0 %** | la coda del difetto |

⇒ ⛔ **Sei cure su otto erano difetti veri che non erano quello che l'utente sentiva.** Ognuna
sembrava confermata dal ragionamento e nessuna dalla misura, perché **la misura che serviva non
esisteva**.

#### ⭐⭐⭐ E LA LEZIONE È UNA SOLA, E NON È SULL'AUDIO

**Avevo i numeri di tre anelli su quattro.** Il figlio diceva quanti blocchi produce, il server
quanti ne spedisce e quanti ne rifiuta, la sessione quanti campioni consegna. ⛔ **Della pagina —
cioè del lato che ASCOLTA — non si sapeva niente**: quanti ne arrivano, quanti se ne suonano,
quanti buchi fa la riproduzione.

⇒ Per sei cure ho curato **il lato che parla**, misurandolo, mentre il difetto si vedeva solo
mettendo i due lati sulla stessa riga. Il giorno in cui quei contatori sono esistiti, la diagnosi
è durata **un passaggio**:

> 50 prodotti → 40 consegnati → deficit 20 % → cuscino 250 ms → **un buco ogni 1,25 s**.
> Misurati: **23 buchi in 30 s**.

⭐ **Il conto si è chiuso al decimale, e ha assolto tre imputati in un colpo** (la pagina, il
cuscino, il thread principale) indicando l'unico colpevole rimasto.

⚠ È `CODER.md` §3.8 — *«si verifica dal lato che deve ricevere»* — e io l'avevo applicata al
**contenuto** (il giudice ascolta i campioni) e **non al ritmo**. Un banco che ascolta *che cosa*
arriva e non *quando* arriva è cieco su metà dei difetti possibili.

⛔ **E l'endpoint che serviva costava trenta righe** (`/diario` in `pagina.c`): il riquadro di
diagnostica della pagina non bastava, perché col desktop acceso la pagina è a tutto schermo e quel
riquadro **non è raggiungibile** — chiederne la lettura all'utente era chiedergli una cosa che non
si può fare.

### 6.9 · ⛔⛔ L'ARBITRO ESTERNO DEGLI APPUNTI NON ESISTE — e §2.4 prometteva il contrario

*17 agosto 2026, sera, alla prima accensione del banco `07-b45`.*

§2.4 di questo documento diceva, in grassetto: *«il lato indipendente del banco degli appunti c'è
già, ed è gratis»* — `xclip` funziona senza una nostra sessione, perché la sponda X11 di Mutter è
incondizionata (`STUDI.md` §gnome §10 `[R]`).

⛔ **È vero del codice di Mutter e falso delle nostre sessioni.** `[M]`: il compositore gira come

```
gnome-shell --headless --no-x11
```

⇒ **XWayland non parte affatto.** Non c'è nessuna sponda X11 da usare.

⚠ **E la trappola dentro la trappola**: `/tmp/.X11-unix` conteneva `X0` e `X1`, di proprietà di
`prova`. Un banco che avesse creduto a quei socket avrebbe puntato a una sessione **morta dal 15
agosto** e avrebbe dato il rosso al prodotto. ⛔ Il passo 0 di `07-b45` li cercava proprio così: la
prima stesura del banco conteneva il difetto che il banco esisteva per evitare.

#### E il ripiego non ha retto neanche lui

L'arbitro è stato rifatto su **GTK/GDK** — un client Wayland vero, che è anche *meglio*: prova la
strada che percorre un'applicazione, non una sponda che i nostri utenti non hanno. ⛔ Non funziona
lo stesso, e le cause provate sono state tre:

| tentativo | esito |
|---|---|
| `Gdk.Display.get_default()` | **`None`**: senza `Gtk.init()` non c'è display. ⚠ E il messaggio d'errore accusava **la sessione** di non esistere mentre la sessione era viva — `CODER.md` §3.11, il sospetto va prima sulla misura |
| `Gdk.Display.open(None)` | **aborto**, `gdk_display_open() was called before gtk_init()` |
| `Gtk.init_check()` | ⭐ il display si apre, `set()` riesce, ⛔ **e al compositore non arriva niente** |

⛔ **La causa vera è di protocollo**: per `wl_data_device.set_selection` serve il *serial* di un
evento d'ingresso, e a un client senza superficie a fuoco non arriva nessun evento. ⚠ Presentare
una finestra non è bastato, e nemmeno avere un client REMOTIX attaccato — cioè con la tastiera
virtuale di libei presente, che era il primo sospetto (`wl-copy` dice **«This seat has no
keyboard»**). ⇒ **Due cause plausibili per lo stesso sintomo, e la prima non era quella.**

⭐ **E questo spiega perché REMOTIX invece ci riesce**: `appunti.c` passa dalla sessione
`RemoteDesktop` di Mutter, che è **la via privilegiata e non chiede il fuoco**. È esattamente il
motivo per cui quella via esiste — e il banco l'ha dimostrato per contrasto.

⏳ **Che cosa resta da decidere**: un arbitro esterno per il verso `sessione → dispositivo` va
trovato in un'applicazione **vera con una finestra a fuoco**, pilotata dall'input di REMOTIX — cioè
la scena dell'utente. ⚠ Oppure si accetta che quel verso lo giudichi **lui**, che è l'invariante I8
e non un ripiego.

### 6.10 · ⛔ E DUE DIFETTI DEL CLIENTE DI PROVA, tutt'e due miei, tutt'e due travestiti

Scrivendo il canale appunti nel secondo lettore di `RCP.md`.

**1. Aspettavo DUE byte per riconoscere uno stream unidirezionale.** Gli stream QPACK del server
ne portano **uno solo** (il tipo, `0x02` e `0x03`) e poi tacciono: quel byte finiva nel mio
accumulo e non arrivava mai ad `aioquic`. ⇒ Il suo strato HTTP/3 non consegnava le intestazioni
della CONNECT, il cliente restava ad aspettare, ⛔ **e il server lo congedava con `TEMPO_SCADUTO`
per non aver mai aperto il canale di controllo** (§4.6).

⚠ **Il rosso finiva sul server**, che aveva fatto esattamente quel che §4.6 gli dice di fare.
`LEZIONI.md` §2.3: *«una prova che boccia il codice giusto costa quanto una che promuove quello
sbagliato»*. ⭐ La cura non è accumulare meglio: è **non accumulare affatto** quel che non è nostro —
uno stream WebTransport comincia per `0x40`, e ogni altro primo byte è di `aioquic`.

**2. Il giudizio «altro» non aveva un ramo suo.** Uno stream già riconosciuto come video (`0x03`)
ricadeva nel ramo «non so ancora che cos'è» a **ogni pacchetto**, veniva ribattezzato «h3», ⛔ e i
byte di un fotogramma finivano dentro lo strato HTTP/3. ⚠ Il sintomo era
`Only one QPACK decoder stream is allowed` — **un errore di HTTP/3 su una connessione dove HTTP/3
non c'entrava niente**, e la connessione cadeva a metà giro.

⭐ Tutt'e due sono la stessa forma: **un difetto del banco travestito da difetto del prodotto**, ed è
la ragione per cui `PIANO.md` §0.3.4 vuole il banco certificato prima di essere creduto.

---

### 6.4 · ⭐⭐ La revisione avversariale — **tredici rilievi, e quattro erano seri**

*17 agosto 2026, su `audio.c`, `webtransport.c`, `pagina.html`, `rcp.c`, `main.c`. Il revisore ha
ricevuto **il codice e la specifica, non il ragionamento di chi l'aveva scritto** (`PIANO.md` §0.4).*

| # | il difetto | perché era serio |
|---|---|---|
| ⛔⛔ **4** | `wt_battito_ns()` e `tono_passo()` avevano **due guardie diverse per lo stesso fatto** | in ogni caso coperto da una e non dall'altra, il battito tornava un istante **nel passato** e nessuno lo spostava: `poll()` con timeout 0, **ciclo al 100 % di CPU**. ⚠ E il caso è normale — *un browser chiude la sessione e tiene viva la connessione*, scritto nel nostro stesso file |
| ⛔⛔ **1** | la pagina dichiarava `opus` **senza chiedersi se sapeva decodificarlo** | §4.3 obbliga il server a seguire l'ordine di preferenza del client ⇒ su un motore senza `AudioDecoder` il server **doveva** scegliere Opus: 50 datagram/s in un `continue`, e il PCM — che esiste per essere il controllo positivo — non entrava mai in gioco. ⭐ Il video, nello stesso file, filtrava già con `isConfigSupported` |
| ⛔ **2** | `AudioContext` e `AudioDecoder` **mai chiusi** | al settimo riattacco senza ricaricare, il motore rifiuta; l'eccezione usciva dal `for(;;)` del lettore dei datagram e **uccideva l'audio per tutta la sessione, senza una riga** |
| ⛔ **3** | `suona()` **sovrapponeva invece di buttare** | il commento diceva «butto il più vecchio»; il codice non teneva i riferimenti e non fermava niente. ⇒ Non un buco: **un segnale raddoppiato** |
| ⛔ **5** | `opus_apri()` fuori dal `try` | una `configure()` rifiutata uccideva il lettore in silenzio, **e lasciava `a.dec` assegnato ma non configurato** |
| ⛔ **6** | sei strade di scarto su otto **mute** | e `wt_audio_conti()` **non aveva un solo chiamante**: i contatori non raggiungevano mai una riga. ⇒ «l'audio buttato» e «l'audio mai arrivato» avevano la stessa faccia |
| ⛔ **8** | *«lo scrive nel registro a ogni sessione»* — **non lo scriveva** | l'interruttore di I6 c'era, la dichiarazione che deve seguirlo no: chi leggeva il registro un'ora dopo non poteva sapere che quel che si sente è un tono di banco |
| ⛔ **13** | `dgram_accoda` rifiutava **senza contare e senza dirlo** | irraggiungibile oggi, ⚠ ma con `figlio.c` stava arrivando il secondo chiamante |

⭐ **E il rilievo 7 chiedeva una misura, non una discussione** — ed è quello che ha reso di più:
*«`audio.h` dichiara che Opus può non produrre un pacchetto per ogni blocco; §6.3 vuole nell'istante
il tempo del primo campione. Una delle due è falsa.»* ⇒ Misurato in isolamento (`07-b44`): **falsa
la prima**, e la misura ha trovato in più il **pre-skip** che nessuno aveva dichiarato.

⚠ **Sette aree dichiarate «non ho trovato niente»**, con quelle parole: l'inquadratura di §6.3
contata byte per byte, il little-endian, l'aritmetica dell'anello, l'invariante I3 sull'audio, il
confronto degli istanti, la fame degli stream, le perdite di memoria. ⛔ *Non è un'assoluzione*, ed
è la forma che `PIANO.md` §0.4 impone.

⏳ **Restano `[?]` da misurare**: il rilievo 9 (il datagram davanti agli stream può **rimpicciolire
il segmento GSO** di tutta la passata, cioè tre `sendto` per fotogramma invece di uno) e il 10
(`nw == 0` ha **tre** cause e il registro ne nomina una).

---

## 7 · Le decisioni prodotte

*(collegamenti a `DECISIONI.md` §x.y — **non copie**)*

⚠ **E una cosa da notare prima di cominciare**: `DECISIONI.md` ha un capitolo intero per gli
appunti (**§5-ter**) e **nessuno per l'audio**. Le scelte dell'audio stanno sparse in
`SPECIFICHE.md` §10, `RCP.md` §5.3 e l'invariante **I5**. ⇒ Se questa fase prende una decisione
sull'audio — la strada del codificatore, la profondità della coda, come si suona nella pagina —
**va messa a verbale lì**, non lasciata dentro un commento nel codice.

---

## 8 · Che cosa resta `[?]` — **riscritto il 21 agosto 2026**

> ⛔ **Questa sezione mentiva.** Era ferma al 17 agosto *«dopo la sonda e prima del prodotto»* ed
> elencava come aperte cose chiuse quella sera stessa dal giudizio dell'utente — *«problema audio
> risolto»*, *«clipboard funziona in entrambi i versi»*. ⚠ Un documento di fase che racconta uno
> stato di quattro giorni fa è la specie di difetto contro cui `PIANO.md` §0.1 esiste: chi lo legge
> rifà lavoro già fatto, o cerca un guasto dove non c'è. ⇒ Qui c'è lo stato **vero**, e l'elenco
> vecchio è stato tolto invece di essere lasciato accanto.

### ⭐ Difetti veri, aperti: **nessuno** — 21 agosto 2026, sera

⭐ **La coda dell'audio non è più un punto aperto**, e non perché sia stata diagnosticata: perché
**l'utente ha ascoltato**. *«Chrome su Android offre un'esperienza completa: audio e video
perfetti»* — §9.7. ⇒ I 400–420 ms restano scritti come **numero misurato** (§«la prima sessione
Android»), non come difetto: è il metro **I8** che decide, e per l'audio I8 è l'orecchio.

⚠ **E quel numero non si cancella**: se un giorno qualcuno lo abbassa, lo fa perché serve a un'altra
scena — non per chiudere un difetto, che non c'è.

### ⏳ Aperti perché nessuno li ha ancora misurati

- ⏳ **il datagram su rete non locale**: 1024/1214 byte sono presi **su cavo**. ⚠ Il giudizio di
  §9.7 è su rete di casa, e vale per **quella**;
- ⏳ **la priorità in tempo reale del percorso audio**: l'unità concede `LimitRTPRIO=20`
  (`07-b41`), ⚠ ma nessuno ha guardato che cosa ne fa PipeWire dentro il figlio.

### ⭐ Chiusi dal 17 al 21 agosto — e qui c'è scritto **come**

| era aperto | chiuso da |
|---|---|
| «gli appunti non hanno mai girato contro niente» | il giudizio dell'utente del 17 agosto sera, e poi i banchi `07-b53`, `07-b54`, `07-b56` |
| «la coda dell'audio a 400–420 ms», ⛔ l'unico difetto vero aperto | ⭐ il giudizio dell'utente del 21 agosto sera: **«audio e video perfetti»** su Chrome per Android — §9.7 |
| «nessuno ha ancora ascoltato l'audio da un telefono» | ⭐ adesso qualcuno l'ha ascoltato, ed è l'utente — §9.7 |
| «il cuscino di 60 ms (A3) e il bitrate di Opus: 🔸 derivati, mai giudicati» | ⭐ giudicati **sul risultato** dal 21 agosto: sono i valori che hanno prodotto quell'ascolto. ⚠ Restano derivati come *numeri* — quel che è chiuso è il dubbio se **rendano** |
| «l'arbitro esterno del banco non esiste» | ⭐ vero, e **non si aggira**: §6.9. I banchi guidano browser veri con Marionette e CDP, e la sessione con `wl-copy`/`wl-paste` |
| `DISPLAY` della sessione di «prova» · `xclip` sulla macchina di prova | ⛔ non servono più: la sponda X11 non c'è (`gnome-shell --no-x11`), e i banchi non la usano |
| l'incolla col **mouse** (tasto destro → «Incolla») | §9.5 — quattro anelli, e `07-b56`: 3 su 3 per motore |
| la clipboard del desktop **persa al collegamento** | §9.6 — il figlio rende alla sessione il testo che aveva lei |


## 9 · Il giudizio dell'utente

*La fase si chiude su una misura giudicata dall'utente, non su un documento completo.
⛔ Non si scrive un verdetto che l'utente non ha dato.*

### 9.1 · ⭐⭐⭐ L'AUDIO: **«problema audio risolto»** — 17 agosto 2026

Dato su un **video di YouTube** riprodotto nella sessione remota, e confermato dai contatori:

| | |
|---|---|
| blocchi ricevuti dalla pagina | 2184 → 3183 in 20 s = **49,95/s** contro 50 prodotti |
| perdita | **zero** |
| **buchi nella riproduzione** | **2**, e fermi — nessun nuovo buco in venti secondi |
| coda | stabile a **311-341 ms** |

### 9.2-bis · ⭐⭐⭐ GLI APPUNTI: **«clipboard funziona in entrambi i versi»** — 17 agosto 2026

*Dato dall'utente col browser, sulla porta 7730, sessione dell'utente `prova`.*

⛔ **È il metro I8, e non lo sostituisce niente**: nessun banco automatico ha mai visto passare un
byte di appunti — l'arbitro esterno che §2.4 prometteva **non esiste** (§6.9), e quel verdetto è
l'unica prova che questa metà della fase abbia.

⭐ **E copre tutt'e due i versi**, cioè anche quello che `DECISIONI.md` §5-ter.1 dichiara il più
usato: *«copio un indirizzo sul telefono e lo incollo nel browser remoto»*.

⭐ **E con lui passa, di striscio, la cura della corsa con `Ctrl+V`** (§4.5.2): il verso
`dispositivo → sessione` **è** quella corsa: l'annuncio e i tasti partono insieme, e se la cura non
avesse funzionato la prima incollata sarebbe tornata vuota.

> ⚠ **Quel che il verdetto NON dice**, e va scritto perché non venga letto per più di quel che è:
>
> - **su quale browser**: la riga del registro della pagina — quella che dice se `clipboardchange`
>   c'è e **dove sta** — non è stata riportata. ⇒ Resta `[?]` se il verso
>   `dispositivo → sessione` abbia funzionato per **sorveglianza** (Chrome) o per **`Ctrl+V` sulla
>   pagina** (Firefox e Safari). Sono due strade diverse (§4.5, `pagina.html`), e sapere quale ha
>   retto cambia che cosa si dichiara all'utente in §9 di `SPECIFICHE.md`;
> - **niente numeri**: nessuna misura di quanto testo, di quanto tempo, né del secondo giro quando
>   il browser nega la scrittura negli appunti;
> - **il DeX e il telefono** restano `[?]`, come per l'audio.

⇒ **La fase 7 ha adesso i suoi due giudizi**: *«problema audio risolto»* e *«clipboard funziona in
entrambi i versi»*. ⛔ E la **fase 6 resta aperta**: il suo §8 aspetta ancora il giudizio su due
scene (il trascinamento del bordo e il clic tenuto giù), e quel che resta della 6 **non si chiude da
sé**.

### 9.2 · ⛔⛔ E PRIMA DEL «RISOLTO» CI SONO STATI SETTE «FA SCHIFO»

*Va scritto, perché è la parte che insegna.* Il banco `07-b43` era **verde su cinque giri su
cinque** — 440 Hz esatti, ampiezza esatta, volume che governa — e l'utente sentiva
*«jitter pazzesco»*. ⇒ **I8 non è una formalità**: il metro è quel che l'utente sente, e cinque
verdi non lo sostituiscono.

⭐ **E tre passi avanti su quattro li ha fatti lui, non io:**

1. *«forse il datagram è troppo piccolo?»* → il manuale di ngtcp2 dà ragione all'intuizione in una
   riga: un lotto GSO si scrive **solo se il primo pacchetto è di misura piena**;
2. *«nella cartella REMOTIX l'audio funzionava, esaminala»* → **R26**, la priorità di tempo reale
   negata dall'unità, misurata il 5 agosto 2026 e da me riscritta come `[?]` senza mai farla;
3. *«riproduci un video e monitora byte per byte»* → è il giro che ha prodotto **il numero
   esatto**, e da lì la diagnosi ha smesso di essere una serie di ipotesi.

---

### 9.3 · ⛔⛔⭐ «SI È BLOCCATO FIREFOX CON LA CLIPBOARD» — e non era Firefox

*20 agosto 2026, difetto riferito dall'utente mentre provava i due browser. ⚠ Non era un blocco del
browser: era **la nostra pagina** che mandava `ERRORE_PROTOCOLLO` e chiudeva la sessione — e da
fuori si vede come un'immagine che si ferma.*

**`[M]` Il registro del server, 19:04:06, e la catena sta in quattro righe:**

```
19:04:06.560  annunciato al client il trasferimento 3 — 1155 byte
19:04:06.560  annunciato al client il trasferimento 4 — 1155 byte   ← stesso millisecondo
19:04:06.569  il client chiede il 3, superato dal 4: lo servo col testo ATTUALE
19:04:06.612  il client si congeda, motivo=0x0b — «i messaggi di trasferimenti
              diversi non si mescolano (§7.4)»
```

⇒ ⭐ **Il server aveva ragione e la pagina torto**, e l'arbitro è scritto: `RCP.md` §7.4 dice
*«un `APPUNTI_CHIEDI` che arriva quando l'annuncio è già stato superato si serve **con il testo
attuale** … è la corsa normale fra due che copiano, **non un errore**»* — la **quinta eccezione
dichiarata a §3**. La pagina applicava la regola generale e ignorava l'eccezione.

⛔⛔ **E lo stesso sbaglio era scritto nei DUE capi**: `rcp.c` chiudeva la sessione nel caso
speculare (il client che serve una richiesta superata). ⚠ La pagina, invece, applicava l'eccezione
**correttamente** quando era lei a *servire*: la stessa regola scritta due volte, e la seconda
diversa — è la forma **E2** dentro un solo file.

**La cura, ai due capi**: l'errore è un testo **che nessuno ha mai chiesto**, non un testo con un
numero vecchio. ⇒ Si confronta con **quel che si è chiesto** (`APPUNTI.chiesti` nella pagina,
`app_chiesto_id` nel server), e la lunghezza si pretende **solo** sul trasferimento vivo — su uno
superato il testo servito è quello di *adesso*.

#### ⭐⭐ E il banco ne ha trovati altri DUE, tutti e due miei, dopo la cura

*È il valore di `banchi/07-b53-appunti-corsa.py`, ed è il motivo per cui esiste.*

| | il difetto | come si presentava |
|---|---|---|
| 1 | **cancellavo il ricordo al primo uso** | una seconda risposta per lo stesso trasferimento — legittima — trovava il ricordo vuoto e chiudeva la sessione. ⇒ La domanda giusta è *«l'ho MAI chiesto?»*, non *«ne ho una in volo?»* |
| 2 | ⛔ **segnavo la richiesta DOPO l'`await`** | e la risposta può arrivare prima che l'attesa si sciolga: ⭐ **verde su Firefox, rosso su Chrome**, per un decimo di millisecondo. ⇒ Il fatto si segna **prima** di consegnare, e si segna l'identificatore che si è messo nel messaggio — non quello riletto dopo |

⛔ **Il secondo è la ragione per cui un banco solo non basta**: la stessa cura, sullo stesso
prodotto, nello stesso minuto, **passava su un motore e falliva sull'altro**.

#### ⚙ Il banco, e perché riproduce uno STATO invece di una coincidenza

⚠ `[M]` La finestra vera dura quanto la lettura della clipboard dalla sessione: **sotto il
millisecondo** su rete locale. Sei copie a raffica dentro la sessione (`wl-copy`, 15 ms l'una
dall'altra) **non l'hanno aperta nemmeno una volta**. ⇒ Il banco mette la pagina **esattamente
nello stato** che ha chiuso la sessione dell'utente: chiede un trasferimento e fa arrivare — prima
della risposta — un annuncio più nuovo. ⛔ È bianco, tocca `REMOTIX.appunti`, **e lo dichiara**:
quel che verifica è la **regola**, non il tempismo.

⭐ **E si certifica**: rimessa la riga vecchia, `[M]` il banco vede la sessione chiudersi con
`motivo=0x0b` — la stessa faccia del difetto dell'utente. Rimessa la cura, **4 giri su 4 verdi,
Firefox e Chrome**.

⛔ **E un difetto che ho fatto mentre curavo**, perché è la parte che insegna: per esporre lo stato
al banco avevo agganciato `APPUNTI` al riquadro `window.REMOTIX`, che gira **molto prima** della sua
dichiarazione — leggere un `const` nella sua zona morta ferma **tutto il resto dello script**.
⚠ Il sintomo non nominava niente di tutto questo: il modulo d'accesso perdeva il suo gestore e la
pagina finiva in `GET /?utente=…&parola=…`, cioè **la parola d'ordine nella barra dell'indirizzo**.
Un difetto di ordine di dichiarazione diventato, per due minuti, un difetto di privatezza.

---

### 9.4 · ⛔⛔⭐ «DA SERVER A CLIENT FUNZIONA, IL CONTRARIO NO» — su Firefox, e le cause erano TRE

*20 agosto 2026, riferito dall'utente. ⚠ E il verso che non funzionava è quello che nessun banco
aveva mai provato **con i tasti veri su un browser vero**: `07-b45` misurava il protocollo, non il
percorso del browser.*

#### La riproduzione, ed è la parte che decide

⛔ **In headless il difetto NON si vede**: l'evento `paste` arriva lo stesso. Neanche su X11 (Xvfb).
⭐ Si vede in **un compositore Wayland annidato** (`cage`), con il testo copiato da **un'altra
applicazione** — cioè l'ambiente dell'utente. `[M]` Il diario della pagina, tre righe:

```
appunti · Ctrl+V visto · sorveglianza=«nessuna»
appunti · evento `paste` arrivato · 0 caratteri          ← VUOTO
appunti · l'evento `paste` è arrivato: strada gratis, nessun permesso
```

e `annunciati: 0`: **non è mai partito niente**.

#### Le tre cause, e sono tutte nostre

| | la causa | perché mordeva |
|---|---|---|
| 1 | ⛔ **un `paste` vuoto contava come consegna** | `ultimo_paste_ms` si segnava **prima** di guardare se ci fosse del testo ⇒ il ripiego `readText()` veniva spento («strada gratis») e non si provava più niente |
| 2 | ⛔ **non c'era niente di modificabile a fuoco** | e l'evento `paste` nasce solo lì. ⚠ Il commento di §9 diceva *«la cura ovvia non si può fare»* perché un `TEXTAREA` a fuoco spegne la tastiera (`cl_nel_modulo`) — ⭐ **era falso**: bastava **nominare l'eccezione** invece di rinunciare |
| 3 | ⛔ **il testo «in attesa di gesto» rubava gli appunti** | il testo venuto dal desktop remoto aspettava un gesto per entrare negli appunti locali, e il gesto poteva essere **il `Ctrl+V` dell'utente** — cioè gli si scriveva sopra la copia proprio mentre la incollava. `[M]` Il banco l'ha visto: il desktop remoto riceveva **indietro il proprio testo** |

#### Le cure, e sono quattro

⭐ **Il campo nascosto** (`incolla_campo_prendi`): prende il fuoco **solo per i 400 ms del `Ctrl+V`**,
l'incolla del browser ha dove andare, l'evento `paste` nasce col testo dentro, e **non si chiede
nessun permesso**. ⛔ E `cl_nel_modulo()` lo esenta per nome: i tasti continuano ad andare al
desktop remoto — il banco lo verifica battendo una lettera **dopo** ogni incolla.

⭐ **La seconda strada**: dopo 120 ms si legge **quel che il browser ha davvero incollato nel
campo**. Non dipende da `clipboardData`, che può arrivare vuoto. `[M]` Su X11 è la strada che ha
consegnato: *«il campo dell'incolla porta 45 caratteri»*.

⭐ **Un `paste` vuoto non conta**, quindi il ripiego `readText()` resta disponibile.

⭐ **E il testo in attesa non si scrive mai su un gesto della clipboard** (`Ctrl+V`, `Ctrl+C`,
`Ctrl+X`), ⛔ e **si butta** se l'utente copia qualcosa di suo: *«i suoi appunti valgono di più»*.

⛔ **E il silenzio si rompe**: se `readText()` non risponde entro 1,5 s — su Wayland Firefox apre il
suo bottoncino «Incolla» e **aspetta**, senza risolvere né fallire — la pagina lo **dice** all'utente
invece di lasciarlo davanti a una cosa che «non funziona».

#### ⚙ Il banco — `banchi/07-b54-appunti-due-versi.py`, e misura QUATTRO caselle

*sessione→client e client→sessione, per Firefox e per Chrome, ⭐ più una quinta: **la tastiera è
ancora viva dopo l'incolla?*** — perché una cura che aggiusta gli appunti e spegne i tasti sarebbe
un pessimo affare.

⛔ **E non usa nessun permesso speciale**: le preferenze di prova di Firefox
(`dom.events.testing.asyncClipboard`) spegnerebbero proprio il difetto che si cerca. La clipboard si
riempie con un `Ctrl+C` **vero** e si legge con un `Ctrl+V` **vero**. ⚠ E il gesto che sblocca la
scrittura dev'essere un **clic del guidatore**: un evento fabbricato in JavaScript non è
un'«attivazione dell'utente», e il browser rifiuta lo stesso.

**`[M]` L'esito, 20 agosto 2026 — quattro ambienti:**

| ambiente | firefox | chrome |
|---|---|---|
| headless | ⭐ ⭐ ⭐ | ⭐ ⭐ ⭐ |
| X11 (Xvfb, browser veri) | ⭐ ⭐ ⭐ | ⭐ ⭐ ⭐ |
| Wayland (`cage` annidato) | ⭐ ⭐ ⭐ | *(non provato)* |
| copia da **un'altra applicazione** → incolla nel prodotto (X11) | ⭐ | — |

⚠ **E quel che NON si è potuto provare, dichiarato**: il caso «Wayland **+** clipboard di un'altra
applicazione **+** tasti sintetici» resta rosso, e ⛔ **non è il prodotto**: Wayland consegna gli
appunti solo a fronte di un evento d'input **vero** (serve il *serial* del compositore), che un tasto
finto non ha. ⇒ Su quel percorso l'ultima parola è di una tastiera vera — cioè dell'utente.

---

### 9.5 · ⛔⛔⭐ «FUNZIONA CON `Ctrl+V`, MA NON COL MOUSE» — 21 agosto 2026, e gli anelli rotti erano **quattro**

> *«Ecco perche'! Funziona l'incolla con ctrl+v, ma non con il mouse e scegliendo dal menu la voce
> "incolla"»* — l'utente, la mattina del 21 agosto, subito dopo aver verificato la cura di §9.4.

⭐ **Una frase che vale una giornata di diagnosi**: dice che la cura del giorno prima è entrata (il
`Ctrl+V` consegna) e nomina esattamente la strada rimasta scoperta.

#### La differenza, e perché nessuno dei quattro banchi verdi poteva vederla

| l'utente fa | chi tocca | che cosa nasce sulla pagina |
|---|---|---|
| `Ctrl+V` sulla pagina | **il browser** | l'evento `paste`, con dentro il testo — gratis |
| tasto destro → «Incolla» **dentro il desktop remoto** | **il desktop remoto** | ⛔ **niente** |

⇒ Quel menu è dipinto nel video, e la voce «Incolla» la esegue un'applicazione che sta dall'altra
parte del filo. L'unica notizia che ne arriva alla pagina è l'`APPUNTI_CHIEDI` del server.
⛔ **E i quattro banchi verdi di §9.4 battevano tutti `Ctrl+V`**: misuravano l'unica strada che già
funzionava. Il banco che mancava è `banchi/07-b56-incolla-col-mouse.py`, che non batte mai un tasto.

#### I quattro anelli, in ordine di scoperta — e **tre erano miei**

**1 · La pagina non veniva nemmeno interpellata.** `rcp.c` non chiede niente a un client che non ha
mai annunciato: mette la richiesta in coda («*la domanda ASPETTA l'annuncio*») e il fondo del figlio
la chiude a mani vuote dopo quattro secondi. ⇒ Finché l'utente non aveva battuto **almeno un**
`Ctrl+V`, un incolla col mouse non arrivava a fare **nemmeno una domanda**: nessuna riga, da nessuna
parte.
⭐ **Cura**: la pagina manda un **annuncio d'apertura da zero byte** appena la sessione è nata.
Costa otto byte una volta, apre il canale della domanda, e dice il vero — in quell'istante di
appunti letti non ne ha.

**2 · ⛔ E quell'annuncio partiva TROPPO PRESTO, e chiudeva la sessione.** `[M]` Registro delle
05:55:42: *«congedo motivo=0x0b — byte sullo stream di appunti (14) prima che `SESSIONE` sia partita
(stato: attesa-verdetto)»*. `avvia_appunti()` gira all'ECCOMI, cioè **prima delle credenziali**.
⇒ L'annuncio d'apertura è stato spostato dopo `SESSIONE` (`appunti_apri_la_domanda`).

**3 · ⛔ L'offerta alla sessione cadeva nel vuoto, e nessuno la rifaceva.** `[M]` 06:00:15 —
l'annuncio alle `.868`, l'apertura degli appunti della sessione alle `.982`: **114 ms** in mezzo, e
in quei 114 ms il figlio scriveva *«gli appunti della sessione non ci sono: l'offerta cade»*.
⇒ Il compositore non diventava mai proprietario della selezione, e dentro il desktop la voce
«Incolla» **non aveva niente da dare**.
⭐ **Cura**: `figlio.c` tiene **un bit** (`appunti_offerta_arretrata`) e rifà l'offerta appena gli
appunti si aprono. È la stessa forma della domanda arretrata di `rcp.c`: invece di ritardare
qualcosa per tutti, si ricuce.

**4 · ⛔⛔ E l'annuncio nuovo UCCIDEVA l'incollata che lo aveva provocato.** Il difetto l'ha detto
Mutter con parole sue: `[M]` *«SelectionWrite per la richiesta 2 è stata rifiutata — Transfer serial
2 doesn't match any transfer request»*.
⚠ Offrire la selezione al compositore (`SetSelection`) **annulla i trasferimenti in volo**: è il
compositore che, vedendo una selezione nuova, butta le richieste aperte sulla vecchia. E noi
ri-offrivamo *proprio mentre servivamo* — la pagina rilegge la clipboard, annuncia il testo nuovo, e
quell'annuncio buttava l'incollata in corso. ⇒ **Chi incollava vedeva vuoto**, che è il sintomo da
cui eravamo partiti.
⭐ **Cura**: finché ci sono richieste in attesa l'offerta si **rimanda** (`app_offri_dopo`), e parte
quando la risposta è partita.

#### E la cura che sta al centro: **si rilegge quando il desktop chiede**

`appunti_rileggi_prima_di_servire()` — sull'`APPUNTI_CHIEDI`, prima di servire, la pagina rilegge la
clipboard del dispositivo. ⭐ Il permesso c'è: **il clic sulla voce «Incolla» del menu remoto è un
clic su questa pagina**, quindi l'attivazione transitoria è fresca di millisecondi.

⛔ **E non si rilegge se la strada gratis ha appena consegnato** (`paste` da meno di 4 000 ms):
senza questa riga si curava l'incolla col mouse **rompendo quello con la tastiera**, perché su
Firefox ogni rilettura costa il bottoncino «Incolla».

#### Il prezzo, misurato — `banchi/07-b56`, 3 incollate per browser

| | Chrome | Firefox |
|---|---|---|
| l'incolla col mouse arriva | ⭐ **3 su 3** | ⭐ **3 su 3** |
| il bottoncino «Incolla» compare | **mai** | ⚠ **3 volte su 3** |
| incollando lo **stesso** testo una seconda volta | — | ⚠ compare **di nuovo** |

⚠ **Su Firefox l'incolla col mouse costa un clic in più, ogni volta.** Non è una scelta nostra:
`readText()` lì apre sempre il bottoncino di conferma, anche a clipboard immutata (`SPECIFICHE.md`
§9 — «*ogni lettura costa il menu Incolla*»). ⭐ Ma stavolta compare **dove l'utente sta già
cliccando**, non in un angolo che nessuno guarda. E il `Ctrl+V` resta gratis su tutti e due i
motori.

#### ⛔ Tre difetti del banco, e due avrebbero dichiarato rotto un prodotto sano

1. **Chrome non andava sullo schermo del banco.** Senza `--ozone-platform=x11` prende Ozone/Wayland
   e si attacca alla sessione grafica **vera**: leggeva un'**altra** clipboard, e `readText()`
   tornava vuoto mentre `xclip -o` sullo schermo del banco mostrava il testo.
2. **Il banco cliccava troppo presto.** Fra il clic e `wl-paste` ci sono `ssh`, `sudo` e `runuser`:
   `[M]` secondi interi, e l'attivazione transitoria dura cinque secondi. ⇒ *«lack of user
   activation»* era il banco, non il prodotto. Cura: il copione remoto dice **`PRONTO`** e aspetta
   un secondo e mezzo, così l'ordine dei fatti è quello vero.
3. **`xclip` appendeva il banco**, come `wl-copy` nella sessione: si biforca per *servire* la
   selezione e tiene aperte le sue uscite. ⇒ Non si aspetta.

⭐ E per cliccare il bottoncino di Firefox il banco entra nel **contesto chrome**
(`clipboardReadPasteMenuPopup`), con `-remote-allow-system-access`: ⛔ **non** si accende
`dom.events.testing.asyncClipboard`, che spegnerebbe proprio la cosa da misurare. Il banco paga il
prezzo davanti a tutti e **riferisce quante volte**.

### 9.6 · ⛔⛔⭐ «COME UNA SESSIONE LOCALE» — la direttiva, e il difetto che ha fatto emergere

> *«L'esperienza dell'utente con REMOTIX dev'essere quanto più vicina possibile all'esperienza con
> una sessione grafica locale. […] niente trucchi, pulsanti strani o soluzioni tecniche che si
> allontanino da questa direttiva»* — l'utente, 21 agosto 2026. `DECISIONI.md` §5-ter.8.

⭐ Verificando la cura di §9.5 alla luce di quella frase è saltata fuori una domanda che nessun banco
aveva mai fatto: **se nel desktop avevo già copiato qualcosa e poi mi collego, quel testo c'è
ancora?**

⛔ `[M]` **No, e la colpa era della cura del mattino.** `wl-paste` dentro la sessione diceva
`TESTO-CHE-ERA-GIA-NEL-DESKTOP` prima del collegamento e **`«»`** dopo.

⇒ La catena: per farsi trovare quando qualcuno incolla col mouse, la pagina si annuncia appena entra
— e annunciarsi vuol dire **prendersi la selezione**, che è una sola. Prendendola a mani vuote si
cancellava quel che l'utente aveva copiato di là. ⛔ È esattamente il contrario di una sessione
locale, dove la clipboard non sparisce perché è entrato qualcuno.

#### E la diagnosi ha corretto una riga di codice che affermava il falso

`appunti.c` diceva che `EnableClipboard` con opzioni vuote fa arrivare un `SelectionOwnerChanged`
**subito**, *«ed è proprio l'annuncio che fa ritrovare gli appunti a chi si ricollega»*.
⛔ **Falso, misurato**: `wl-copy` vivo e proprietario, `wl-paste` che rilegge il suo testo prima e
dopo, e nel registro del figlio **nessuna riga di lettura**. Mutter racconta i **cambi** di
proprietario, non chi lo è già. ⇒ La clipboard che c'è si **chiede** (`appunti_leggi_adesso()`), e
si richiede **a ogni riattacco** — il figlio sopravvive fra un collegamento e l'altro, quindi la
lettura fatta all'accensione vale una volta sola (`MSG_RIMANDA_PALCO`, che vuol dire esattamente
«un client si è riattaccato»).

#### La cura definitiva sta dove il testo c'è davvero

⭐ **Se il client non ha appunti da dare, il figlio rende alla sessione l'ultimo testo che la
sessione stessa gli aveva dato** (`appunti_rispondi`). La selezione cambia di mano, **il contenuto
no**. ⇒ Chi si collega non perde niente, e la strada dell'incolla col mouse resta aperta.

⚠ **E due cure intermedie sono state buttate, con la loro ragione**:

| cura provata | perché è caduta |
|---|---|
| «un annuncio vuoto non porta via la selezione a chi ha qualcosa» (in `rcp.c`) | proteggeva la clipboard **chiudendo la strada del mouse**: senza la selezione, il desktop non ci chiede niente |
| «il primo testo della sessione si impara ma non si scrive negli appunti del dispositivo» (nella pagina) | non sapeva distinguere *lo stato iniziale* dalla *prima copia fatta nella sessione*, e ha mandato rosso il verso sessione → client su tutti e due i motori (`07-b54`) |

⇒ ⭐ La lezione, ed è la stessa di sempre: **la cura va messa dove l'informazione c'è**. Né la pagina
né il protocollo sanno che cosa contiene la clipboard del desktop; il figlio sì.

#### ⛔ E tre altri difetti del banco, tutti che dichiaravano rotto un prodotto sano

1. **`wl-copy` ucciso dal `timeout` del banco**: si biforca per *servire* la selezione, e il
   `timeout 12` che avvolge il copione se lo portava via insieme al gruppo. ⇒ `setsid`, e la copia
   **si verifica rileggendola**.
2. **La clipboard del browser non era vuota**: il banco chiedeva «il desktop ha perso il suo testo?»
   mentre il dispositivo aveva del testo suo — e allora il desktop riceve **quello**, ed è giusto.
   ⇒ La domanda si fa solo a clipboard del dispositivo vuota, e la si svuota con un proprietario che
   dichiara zero byte (⛔ non rileggendola con `readText()`: su Firefox quella lettura vuole un
   gesto, e si finirebbe per misurare il permesso).
3. **Dal secondo browser in poi non si misura un collegamento, si misura una coda**: il figlio
   sopravvive e si porta dietro lo stato della prova precedente. ⇒ La prova «sopravvive?» si fa col
   **primo** browser del giro, e per l'altro motore si rilancia il banco a server appena acceso.

#### Lo stato misurato — 21 agosto 2026

| | Firefox | Chrome |
|---|---|---|
| incolla col mouse (`07-b56`) | ⭐ 3 su 3 | ⭐ 3 su 3 |
| la clipboard del desktop sopravvive al collegamento | ⭐ sì | ⚠ non misurabile da solo *(vedi difetto 3; la cura è nel figlio, non nel motore)* |
| `Ctrl+V` nei due versi (`07-b54`) | ⭐ | ⭐ |
| la corsa di §7.4 (`07-b53`) · la tela e il clic (`07-b51`) | ⭐ · ⭐ 4/4 | ⭐ · ⭐ 4/4 |
| il bottoncino «Incolla» di Firefox | ⚠ **ogni volta** | mai |


### 9.7 · ⭐⭐⭐ CHROME PER ANDROID: **«un'esperienza completa, audio e video perfetti»** — 21 agosto 2026, sera

> *«Chrome su Android offre un'esperienza completa: audio e video perfetti.»* — l'utente.

⭐ **È il giudizio che mancava a questa fase**, ed è quello che il §2.1 pretendeva fin dall'inizio:
*si ascolta, non si contano i blocchi*. I contatori della prima sessione Android erano verdi già la
mattina — **8 935 blocchi ricevuti, 8 933 suonati, 2 buchi in 3 min 30** — ma un contatore verde non
ha mai chiuso niente qui dentro.

⛔ **E chiude il difetto che al mattino era l'unico vero aperto**: la coda dell'audio che si assestava
a **401 → 421 ms**. ⚠ La misura non era sbagliata, e non è stata «spiegata»: è stata **giudicata**.
Quattro decimi di secondo di coda si sentono in una scena — un metronomo, un video con le labbra in
campo — e in questa non si sono sentiti. ⇒ Il numero resta scritto dov'è, come numero; smette di
essere un difetto.

⭐ **Con questo, l'audio della fase 7 ha tre giudizi dell'utente, su tre mezzi diversi**: il video di
YouTube da desktop (§9.1), gli appunti nei due versi (§9.2-bis), e adesso **un telefono**.

⚠ **E il confine si scrive, perché "pienamente supportato" vuol dire *funziona, e sai in che
condizioni*** (`DECISIONI.md` §0.1-bis):

| | |
|---|---|
| il giudizio vale per | **Chrome per Android**, Samsung DeX, rete di casa |
| ⛔ **non** vale per | **Firefox per Android** — dichiarato incompatibile dall'utente lo stesso giorno (`DECISIONI.md` §7.18) |
| resta non misurato | il **datagram su rete non locale**, e la **priorità in tempo reale** dentro il figlio |
