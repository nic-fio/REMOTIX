# REMOTIX — Specifica del prodotto

*Documento definitivo delle decisioni prese e delle funzionalità del prodotto.*
*Ultimo aggiornamento: 3 agosto 2026 — vincoli su linguaggio e stack RDP (§8-bis); due codec sulla
pipeline EGFX dopo la misura sul client Android (§3.1, §3.7).*

Documenti collegati:
- [`PIANO.md`](PIANO.md) — **piano di sviluppo**: le fasi, in che ordine, e che cosa si vede alla fine
  di ciascuna
- [`REFERENCE.md`](REFERENCE.md) — **riferimento di sviluppo**: le regole da rispettare perché il
  codice non entri in conflitto con i client Windows, Linux e Android. Da tenere aperto mentre si
  scrive; gli altri documenti spiegano il perché, questo dice il cosa
- [`LEZIONI.md`](LEZIONI.md) — **le lezioni imparate costruendo il supporto a GNOME**, nella forma
  che serve a chi aprirà il prossimo desktop: metodo di misura, trappole per famiglia di
  compositore, e i vicoli ciechi già percorsi
- [`protocollo-rdp.md`](protocollo-rdp.md) — studio del protocollo MS-RDP da Windows 10 in avanti:
  che cosa un client moderno negozia, che cosa un server deve implementare, e dove sta ciascuna cosa
  in FreeRDP 3
- [`gnome-remote-desktop.md`](gnome-remote-desktop.md) — studio del codice di `gnome-remote-desktop`,
  che dalla decisione del 3 agosto (§8-bis) è il riferimento principale: stesso linguaggio, stessa
  libreria RDP, stesso compositore
- [`kde.md`](kde.md) — **studio del codice di KDE Plasma e KWin 6.3.6**, per la fase 11: la cattura e
  il suo permesso, l'input via libei, la sessione senza monitor, la risoluzione dinamica che su KDE
  non si fa, e il conto per REMOTIX
- [`client-android.md`](client-android.md) — studio dell'ambiente Android come client: il panorama,
  la decodifica H.264, l'input, e il piano di prove
- [`xrdp-funzionalita.md`](xrdp-funzionalita.md) — analisi delle funzionalità di xrdp, primo riferimento

---

## 1. Che cosa è REMOTIX

Un **server RDP per Linux**, rivolto all'uso personale e alla piccola scala, che permette di
raggiungere da remoto il proprio desktop con client RDP standard su Linux, Windows e Android.

Nasce come alternativa a xrdp, con tre differenze di fondo:

- **Solo Wayland e solo moderno.** Niente compatibilità con protocolli e client di vent'anni fa.
- **Niente funzionalità aziendali.** Nessuna multi-tenancy, nessuna integrazione a dominio.
- **Qualità video come obiettivo primario**, con accelerazione hardware.

REMOTIX **non è un ambiente desktop**: restituisce all'utente il desktop che ha già installato.

---

## 2. Principi guida

1. **Rilevare le capacità, non la distribuzione.** All'avvio REMOTIX verifica cosa trova sul
   sistema, sceglie il percorso migliore disponibile e dichiara chiaramente cosa manca.
2. **Degradare, non fallire.** Ogni dipendenza mancante ha un ripiego. Il servizio funziona
   comunque, con meno.
3. **Dipendere, non riscrivere.** Ogni componente che scriviamo è un componente da mantenere
   per sempre. Si usano i meccanismi di sistema esistenti.
4. **Parlare direttamente ai compositor**, anziché passare per i portali, quando questo evita
   richieste di autorizzazione a video — inaccettabili per un servizio non presidiato.

---

## 3. Funzionalità

### 3.1 Video e grafica

> # ⛔ IL REQUISITO DI PRESTAZIONE, posto dall'utente il 7 agosto 2026
>
> *«Adesso scrivo quello che voglio, tu decidi cosa ci vuole per ottenerlo. Le soluzioni tecniche
> devono essere prese in funzione di questi vincoli, non il contrario.»*
>
> | | |
> |---|---|
> | **MINIMO** | **30 fotogrammi al secondo a 1080p, profondità colore 24 bit** |
> | **DESIDERATO** | **60 fotogrammi al secondo a 4K, profondità colore 32 bit** |
>
> **Questo capovolge l'ordine con cui il progetto ha lavorato fino a oggi**, e il capovolgimento è
> il punto: fino al 7 agosto si sceglieva una strada tecnica e poi si misurava cosa ne usciva. La
> fase 9 ha ottimizzato i millisecondi di CPU per fotogramma — da 41 a 6 — senza che nessuno avesse
> mai misurato i **fotogrammi al secondo consegnati all'utente**, che è la grandezza che si vede.
> Quando è stata misurata, la sera stessa, erano 18: e non li limitava il codificatore.
>
> **Da cui la regola di lavoro**: una scelta tecnica si giustifica mostrando che avvicina uno dei due
> numeri qui sopra. Una che li lascia dove sono non si fa, per quanto sia elegante il guadagno che
> porta altrove.
>
> Il conto di fattibilità — che cosa dei due è raggiungibile, con quali client, e a che prezzo — sta
> in **§3.1-bis**, ed è la prima cosa da aggiornare quando una misura lo smentisce.

**Obiettivo di qualità, non vincolo**: la migliore esperienza possibile dentro la banda
disponibile. Il 4K su 10 Mbps è il traguardo ideale; 2K a 30 fps sulla stessa banda è
considerato un risultato altrettanto buono.

> ⛔ **I 10 Mbps SONO UN PAVIMENTO, NON UN BUDGET.** *Posto dall'utente il 7 agosto 2026: «il valore
> di 10 Mbps è un limite MINIMO, non si deve scendere sotto».*
>
> Il testo qui sopra si prestava alla lettura opposta — «la migliore esperienza **dentro** la banda
> disponibile» suona come un tetto in cui stare — e su quella lettura la fase 10 ha spedito un
> controllo di bitrate che su un desktop poco mosso scendeva a **2–6 Mbit/s**, contento di
> risparmiare. L'utente l'ha giudicato sul desktop vero: *«siamo tornati indietro»*.
>
> **Il risparmio di banda non è un obiettivo di questo prodotto.** Su un collegamento che porta 10
> Mbps si spendono 10 Mbps: la banda non spesa non torna utile a nessuno, e la qualità persa si
> vede. Da cui, in concreto:
>
> - il controllo del bitrate lavora **a banda costante** verso il valore dichiarato;
> - un adattamento può solo **salire** quando la linea porta di più (§10 di `PIANO.md`), mai scendere
>   sotto il valore dichiarato;
> - scendere si può solo quando la linea **non porta abbastanza**, ed è una degradazione dichiarata,
>   non un'ottimizzazione.

**Punto di lavoro stabilito per misura** (calibrazione del 1 agosto 2026):
**4K a 30 fps su 10 Mbps è giudicato accettabile.** La prova ha confrontato tre scene — documento
quasi fermo, scorrimento di pagina, scorrimento veloce — generate alla risoluzione nativa e
codificate a 10 Mbps con VA-API.

*Limite della prova*: le scene erano a base di testo, cioè il contenuto tipico di un desktop ma
non il più esigente. Un video a schermo intero o immagini fotografiche sono più difficili. Non
cambia il punto di lavoro, ma **cambia il ruolo dell'adattamento automatico**, che diventa una
rete di sicurezza per i casi pesanti anziché la modalità ordinaria.

> ✅ **Quel limite è stato misurato il 7 agosto 2026, aprendo la fase 10** — con riferimenti senza
> perdita, che la calibrazione del 1 agosto non aveva conservato. Il dettaglio sta in `REFERENCE.md`
> **R31**; qui contano due cose.
>
> **Il testo costa niente**: a 2560×1440 bastano **234 kbit/s** perché una pagina di testo si legga
> benissimo. Il punto di lavoro dei 10 Mbps non lo decide il testo — lo decide il contenuto mosso, e
> quello è stato aggiunto al banco (video a schermo intero, e video in una finestra dentro una
> pagina ferma).
>
> **E la scala di ripiego qui sotto non è un lusso**: sotto i ~4 Mbit/s a 1440p il codificatore
> hardware **non rispetta più il tetto** — chiedendone 2 000 ne escono 3 700–4 100, in ogni modo di
> controllo. Da lì in giù l'unica leva sono meno pixel o meno fotogrammi. È anche la prima verifica
> di §5.5: sopra i 6 Mbit/s `h264_vaapi` e `libx264` si equivalgono entro 0,3 dB, sotto no.

Scala di ripiego dell'adattamento:

| Priorità | Risoluzione | Quando |
|---|---|---|
| 1 | **4K a 30 fps** | modalità ordinaria |
| 2 | 2K a 30 fps | contenuto esigente o banda ridotta |
| 3 | 1080p a 30-60 fps | banda scarsa o codifica software su CPU modesta |

- **Pipeline EGFX** (MS-RDPEGFX) come unico percorso di rendering
- **Due codec sulla stessa pipeline**, scelti al `CapsConfirm` in base ai flag dichiarati dal client
  (*deciso il 3 agosto 2026*):

  | Codec | Quando | Chi serve |
  |---|---|---|
  | **H.264 AVC420** | il client non accende `AVC_DISABLED` | Windows, Linux |
  | **RemoteFX Progressive** | il client non sa decodificare H.264 | **Android** |

  Non è un ripiego di emergenza: è la stessa struttura di `gnome-remote-desktop`, che usa AVC quando
  c'è accelerazione e RFX Progressive quando non c'è. E su Android **rende di più**, perché lì l'H.264
  si decodifica in software (vedi [`client-android.md`](client-android.md) §1.2-bis).

  Il motivo per cui la decisione è stata forzata: **Remote Desktop Manager non decodifica H.264**,
  misurato il 3 agosto. Il dettaglio in [`REFERENCE.md`](REFERENCE.md) §1.1.
- **Adattamento automatico di risoluzione e frame rate alla banda**, come funzionalità e non
  come ripiego

  > ⚠ **Corretto il 5 agosto 2026, chiudendo la fase 7.** Questa riga diceva *«riusa la stessa
  > macchina della risoluzione dinamica, guidata dalla rete anziché dalla finestra del client»*, e
  > quella strada **non funziona**: il client di riferimento rimanda la misura della propria finestra
  > ogni secondo (`xf_disp_OnTimer`), quindi a schermo intero disfa ogni riduzione decisa dal server;
  > e cambiare la misura del monitor virtuale **ridispone le finestre dell'utente**, che è un prezzo
  > troppo alto per un calo di banda di due secondi.
  >
  > L'**adattamento del frame rate** invece c'è, ed è quello che la fase 7 ha consegnato: il
  > regolatore a posti-fotogramma con soglia ricavata dall'RTT. Misurato: con la rete strozzata a
  > 250 kbit/s il ritmo scende da 30 a 23 fotogrammi al secondo **senza mai bloccarsi**, e i
  > fotogrammi in volo restano sotto la soglia invece di accumularsi.
  >
  > La **risoluzione** è passata alla fase 10, dove la scala qui sotto si tara insieme al bitrate, e
  > dove va valutato `MAPSURFACETOSCALEDOUTPUT` — che lascia il desktop alla misura chiesta e
  > rimpicciolisce solo la superficie codificata, senza litigare con MS-RDPEDISP.
  >
  > ⛔ **E il 7 agosto 2026 la fase 10 ha misurato che quella strada non c'è.** `xfreerdp3` rende lo
  > scaled output; **mstsc lo ignora** — pur non dichiarandolo spento — e RDM lo dichiara spento
  > (§10.2 di `REFERENCE.md`). Un client su tre, e non i due severi.
  >
  > **Quindi l'adattamento automatico di risoluzione non si fa, e questa riga della specifica va
  > letta come una funzionalità non realizzabile con i client di riferimento**, non come un lavoro
  > rimandato. Quel che resta, e funziona, è l'adattamento del **ritmo** (fase 7) e quello della
  > **qualità** dentro il bitrate (fase 10). La scala 4K → 2K → 1080p resta praticabile solo come
  > scelta dell'utente alla connessione, non come reazione automatica alla banda.
- **Accelerazione hardware** su GPU Intel, AMD e NVIDIA, con cattura **zero-copy** via DMA-BUF
- **Codifica software** (x264) come base sempre disponibile e come punto di partenza dello
  sviluppo

**L'astrazione è ffmpeg (`libavcodec`), non le API dei costruttori.** REMOTIX non parla né a
VA-API, né a NVENC, né a Vulkan: parla a `libavcodec` e sceglie il codificatore **per nome, a
runtime**, in base a cosa trova sulla macchina. Un solo percorso di codice, nessuna riga
specifica per costruttore.

Codificatori disponibili in ffmpeg su Debian Trixie, verificati sul campo:

| Nome | Copre |
|---|---|
| `libx264` | software, sempre disponibile |
| `h264_vaapi` | Intel e AMD |
| `h264_qsv` | Intel Quick Sync |
| `h264_nvenc` | NVIDIA |
| `h264_vulkan` | Vulkan Video, tutti e tre |

*Perché non Vulkan Video come unica via*: è disponibile su tutti e tre i costruttori, ma è
deliberatamente di basso livello — consegna il codificatore senza il controllo del bitrate, che
andrebbe scritto da noi. È precisamente la parte che decide se 10 Mbps risultino guardabili;
VA-API e NVENC la forniscono già messa a punto dal costruttore. Vulkan non è escluso: resta una
delle opzioni fra cui `libavcodec` può scegliere, e se maturerà basterà cambiare l'ordine di
preferenza.

*Conseguenza sul piano*: l'accelerazione hardware diventa molto più economica da aggiungere —
si parte con `libx264` e più avanti si cambia il nome del codificatore, senza riscrivere la
catena.
- **Monitor singolo.** Il multi-monitor è fuori scope: a 4K su 10 Mbps la banda è già
  interamente impegnata da uno schermo. L'implementazione va però tenuta parametrica su N
  output, per non precludere un'estensione futura

### 3.1-bis Il conto di fattibilità dei due requisiti

*Scritto il 7 agosto 2026, il giorno in cui il requisito è stato posto. Ogni riga è una previsione
basata sulle misure già fatte, non una promessa: quel che è misurato è marcato, il resto va
verificato prima di essere citato.*

| | Windows e Linux | Android (client di riferimento) |
|---|---|---|
| **30 fps a 1080p, 24 bit** *(minimo)* | **raggiungibile** — e dal 7 agosto **misurato**: la cattura ne dà 37 | **da verificare**, ed è il punto debole |
| **60 fps a 4K, 32 bit** *(desiderato)* | **non su GNOME** [M, 7 agosto]: Mutter si ferma a 37. Su KWin sono 60 misurati | **impossibile** |

**Il minimo.** Oggi arrivano ~18 fotogrammi al secondo, e non li limita il codificatore: la cattura
ne consegna 17,7 e il server ne spedisce 17,9 [M, 7 agosto]. Il lavoro sta quindi tutto nella
consegna dei fotogrammi dal compositore, non nella codifica — che è precisamente il pezzo su cui la
fase 9 ha lavorato. Il costo di codifica lascia margine abbondante fino a 30.

> ## ✅ MISURATO LA SERA DEL 7 AGOSTO 2026, e i 18 erano nostri
>
> *Il banco, le tabelle per intero e il metodo stanno in **R32** di `REFERENCE.md`. Qui c'è quel che
> cambia per il prodotto.*
>
> **I 18 fotogrammi non sono un limite di Mutter: sono il numero che gli abbiamo chiesto.** REMOTIX
> dichiara alla cattura un massimo di **30**, e Mutter ne consegna **18**. Dichiarandone **60** — che
> è quel che dichiara `gnome-remote-desktop` — ne consegna **37**. Si ottengono circa **sei decimi**
> di quel che si chiede, e oltre i 60 non si sale.
>
> | | Misurato, cattura sola, scena dichiarata e sempre in movimento |
> |---|---|
> | il client disegna | **60 fotogrammi al secondo**, su un monitor virtuale a 60,000 Hz |
> | Mutter ne consegna | **35–37**, a *qualunque* risoluzione da 1080p a 4K |
> | KWin ne consegna | **59–60**, a qualunque risoluzione |
> | sway e labwc (wlroots) | **61** a 1080p e 1440p |
>
> **Le tre ricadute sui due numeri di questo paragrafo:**
>
> 1. **il minimo si raggiunge cambiando una riga.** 30 fps a 1080p sono dentro i 37 che Mutter
>    consegna, e il codificatore ha già margine (fase 9). La riga è la cadenza dichiarata;
> 2. **il desiderato non è raggiungibile su GNOME**, e il motivo non è la potenza: né la risoluzione
>    né la profondità di colore costano niente alla consegna — 4K rende come 1080p — ma il
>    compositore perde il 40 % dei ridisegni e nessuna leva nostra lo sposta. È **Mutter** il tetto
>    dei 60 fps a 4K, non la GPU, non la banda, non il codec;
> 3. **e su un altro desktop quel tetto non c'è.** KWin consegna 60 a 4K, wlroots 61 a 1440p, sulla
>    stessa macchina e nello stesso minuto. La **fase 11** smette quindi di essere solo «servire più
>    desktop»: è anche la strada per il numero desiderato.

**Il desiderato, e i suoi due limiti duri:**

1. **60 fps a 4K non esiste su Android.** Non è una questione di potenza del server: il client di
   riferimento non decodifica H.264 affatto (§1.4 di `REFERENCE.md`, misurato il 3 agosto) e riceve
   un codec che il telefono decodifica in software. Il suo tetto è molto più basso, e lo pone lui.
2. **La «profondità colore a 32 bit» non è ottenibile con il formato video che si spedisce.** Il
   percorso H.264 di RDP porta 8 bit per canale con **risoluzione di colore dimezzata** (4:2:0): i
   colori sono giusti e non ci sono scalini, ma il dettaglio del colore è metà di quello della
   luminosità. Le uniche due strade per il colore pieno sono entrambe chiuse o care: AVC444, escluso
   dall'utente il 7 agosto per i problemi di luminanza di un tentativo precedente (§5.2), e RemoteFX
   Progressive, che il colore non lo sottocampiona ma costa CPU piena e non arriva a 4K60.

**Da cui la lettura onesta dei due numeri**: il minimo è un obiettivo di ingegneria, e si insegue.
Il desiderato è raggiungibile sui client che decodificano in hardware e per la parte «60 fps a 4K»;
la parte «32 bit» richiede di rinunciare o alla velocità o a un client, e va deciso quando ci si
arriva — non promesso adesso.

### 3.2 Audio

- **Uscita audio stereo in AAC**, con **PCM** come base obbligatoria per i client che non
  negoziano AAC
- **Redirezione del microfono** dal client alla sessione (MS-RDPEAI)
- Sorgente e destinazione: **PipeWire**

### 3.3 Sessione

- **Persistenza**: la sessione sopravvive alla disconnessione e si riattacca alla riconnessione
- **REMOTIX avvia la sessione**, non si limita ad agganciarne una esistente: al momento della
  connessione lancia il desktop dell'utente senza monitor
- **Risoluzione dinamica** (MS-RDPEDISP): il desktop si adatta alle dimensioni della finestra
  del client

### 3.3-bis REMOTIX avvia una **sessione**, non solo il compositore

*Deciso il 2 agosto 2026.*

Fino alla fase 4 si è avviato `gnome-shell --headless` da una shell qualunque, e
si è rifatto a mano, un pezzo per volta, ciò che `gnome-session` fa da sé: le
variabili d'ambiente che le applicazioni di GNOME leggono per riconoscere
l'ambiente, la registrazione della sessione, gli avvii automatici. Ogni rimedio
è costato una caccia al guasto, e il conto non era finito: «Esci» dal menu di
sistema non chiude nulla, perché chiama `org.gnome.SessionManager` che non
esiste.

Dalla fase 5 REMOTIX avvia la sessione intera. Ne discendono, gratis, il logout
funzionante, l'ambiente corretto senza doverlo indovinare, gli avvii automatici,
l'agente delle chiavi e i portali.

**Da accertare per primo**: `gnome-session` si aspetta una sessione grafica di
logind su un seat. È il passaggio che `gnome-remote-desktop` risolve con la
consegna da GDM, e che §5.6 ha accertato non servire per il solo compositore.
Se servisse per la sessione intera, la scelta va ripesata — non ribaltata.

---

### 3.3-ter Logout e distacco sono due cose diverse

*Deciso il 4 agosto 2026, chiudendo la fase 5.*

Sono i due modi in cui una connessione finisce, e **non vanno confusi**:

| | Cosa fa l'utente | Cosa succede alla sessione | Cosa trova al ritorno |
|---|---|---|---|
| **logout** | sceglie «Esci» **dentro** il desktop remoto | muore | dopo le credenziali, una sessione **nuova** |
| **distacco** | chiude il client, o cade la rete | **resta in piedi** | dopo le credenziali, la **sua** sessione, con le finestre dov'erano |

**Non c'è ambiguità possibile fra i due**, e non per convenzione: arrivano da due canali diversi.
Il distacco è la sola chiusura di un socket, e non annuncia niente. Il logout arriva come
`EndSession` da `gnome-session`, presso cui REMOTIX si registra come client — un annuncio
esplicito, che precede sempre la chiusura del socket. Per questo al client si manda
`ERRINFO_LOGOFF_BY_USER` e non una chiusura muta: chi riceve solo un socket chiuso non potrebbe
distinguere i due casi più di quanto potremmo noi.

**Fra i due sta il palco** — monitor virtuale, cattura e input — che appartiene alla sessione e non
alla connessione. È lui che permette a un distacco di non toccare la sessione, e a un cambio di
risoluzione di rifarsi senza buttarla via. Tre strati, non due:

| | Muore quando |
|---|---|
| **sessione grafica** (`gnome-session` + Mutter) | logout; oppure compare una sessione **locale**, che ha la precedenza (§5.10) |
| **palco** (monitor virtuale, PipeWire, libei) | muore la sessione, **oppure** cambia la misura dello schermo |
| **connessione** (un client RDP) | il client se ne va, per qualunque motivo |

La terminazione per **sessione locale** non è né un logout né un distacco: la sessione muore senza
che il remoto l'abbia chiesto, e infatti il client riceve un codice diverso
(`ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION`). Vanno tenute distinte anche nel codice: fanno la
stessa cosa alla sessione, non al client.

> **Resta da decidere**: una sessione staccata resta in piedi **per sempre**. `xrdp` fa lo stesso
> ma con un tetto configurabile. Se REMOTIX finirà su macchine con poca memoria, la domanda «dopo
> quante ore una sessione senza nessuno attaccato si chiude» andrà risposta. Non è un difetto, è
> una scelta non ancora fatta.

---

### 3.4 Autenticazione e regole di accesso

- **Autenticazione locale via PAM**
- **Una sola sessione grafica per utente** — la regola vale per **ogni** utente della macchina,
  non solo per quello che esegue il server:
  - se l'utente ha già una sessione grafica **locale** attiva, la connessione RDP è rifiutata
  - le sessioni **testuali** dello stesso utente possono coesistere liberamente
  - implementazione tramite **systemd-logind** (o **elogind**) su D-Bus, distinguendo il tipo
    di sessione (`wayland`/`x11` contro `tty`)

**Risoluzione dei conflitti**

- **La sessione locale vince**: se l'utente apre una sessione grafica locale mentre ha una
  sessione RDP attiva, quella RDP viene terminata — e con essa la **sessione grafica remota**, non
  solo il collegamento (deciso il 3 agosto; il perché e il come stanno in §5.10)
- **La seconda connessione RDP viene rifiutata**, con messaggio di errore esplicito

#### La tabella delle nove combinazioni

Scritta dall'utente il 3 agosto e **verificata caso per caso** contro il comportamento reale. Vale
per **ogni utente della macchina**, presi uno alla volta: le sessioni di utenti diversi non si
contendono nulla, e la tabella va letta come se ce ne fosse uno solo.

| # | Sessioni testuali | Sessione grafica attiva | Nuova richiesta | Esito | Chi lo garantisce | Provato |
|---|---|---|---|---|---|---|
| 1 | 0 o N | nessuna | testuale (ssh/tty) | consentita, illimitate | `sshd`/`logind`: REMOTIX non le tocca | sì |
| 2 | 0 o N | nessuna | grafica locale | consentita, è la prima | il gestore di accesso; REMOTIX non intralcia | sì |
| 3 | 0 o N | nessuna | grafica RDP | consentita, è la prima | REMOTIX | sì |
| 4 | 0 o N | locale | testuale (ssh/tty) | consentita, non interferisce | nessuno interviene | sì |
| 5 | 0 o N | locale | grafica locale | rifiutata, già attiva locale | **il gestore di accesso, non REMOTIX** | no (§) |
| 6 | 0 o N | locale | grafica RDP | rifiutata, la locale ha priorità | REMOTIX — **84 ms** | sì |
| 7 | 0 o N | RDP | testuale (ssh/tty) | consentita, non interferisce | nessuno interviene | sì |
| 8 | 0 o N | RDP | grafica locale | consentita, la locale sostituisce l'RDP | REMOTIX — client giù in **2 s**, sessione chiusa in **3 s** | sì |
| 9 | 0 o N | RDP | grafica RDP | rifiutata, già attiva grafica | REMOTIX — **78 ms** | sì |

Le prove stanno in `prova-e2e.sh`; le tre righe che REMOTIX garantisce da solo — 6, 8, 9 — hanno
ciascuna il proprio controllo, con il tempo misurato.

**(§) Il caso 5 non dipende da REMOTIX.** Impedire una *seconda sessione locale* allo stesso utente
è compito del gestore di accesso grafico, che riconosce quella esistente e la riprende invece di
aprirne un'altra. Nella VM non è verificabile perché un gestore di accesso non c'è — di proposito,
aprirebbe sessioni locali che confliggono con le prove. La riga resta vera, ma per merito d'altri.

**Il caso 9 si legge «seconda connessione *simultanea*».** Se il client se n'è andato — finestra
chiusa, rete caduta — la sessione grafica resta viva e chi torna **si riaggancia**, ritrovando le
finestre dov'erano: non è un secondo accesso, è lo stesso utente che rientra in casa propria, ed è
la persistenza voluta dalla fase 5. Il rifiuto scatta solo se un client è collegato *adesso*.

**Il caso 8 ha una finestra di sovrapposizione**, ed è il limite noto di questa tabella: fra la
comparsa della sessione locale e la chiusura di quella remota passano circa **tre secondi**, e lì
dentro le due sessioni grafiche coesistono davvero. Su una macchina con gestore di accesso il
compositore locale parte proprio in quell'intervallo e potrebbe trovare `org.gnome.Shell` ancora
occupato. Non provato: la sessione locale delle prove non contiene un compositore e la VM non ha
un gestore di accesso. Chiudere quella finestra richiede di sgomberare **prima** che il compositore
locale parta, e per accorgersene in tempo serve la registrazione in `logind` della sessione remota
— **questione aperta n.10**.

**⚠ Entra un solo utente: quello di cui REMOTIX serve la sessione.**
Segnalato dall'utente il 3 agosto come violazione di questa specifica, e lo era. PAM risponde a una
domanda diversa da quella che ci interessa: dice *«questa credenziale è buona»*, non *«questa
persona ha diritto a questa sessione»*. Poiché oggi REMOTIX serve **una sola sessione** — quella
dell'utente che lo esegue — qualunque altro utente della macchina, **con la propria password
vera**, si sarebbe trovato dentro il desktop di un altro. Non è solo la doppia sessione che questo
paragrafo vieta: è accesso ai dati altrui, che è peggio.

Il confronto si fa **prima** di PAM, e con l'utente ricavato dall'uid effettivo del processo — non
da `$USER`, che è una convenzione e può parlare di qualcun altro quando il server è avviato con
`sudo -u` o da un'unità systemd. Se quell'utente non si riesce a stabilire, REMOTIX **non parte**:
un server che non sa di chi sia la sessione che serve non deve aprire la porta.

Il registro dichiara all'avvio di chi è la sessione, e su ogni rifiuto scrive tutti e due i nomi —
`arrivato` e `atteso` — perché «ho sbagliato utente» e «qualcuno sta provando a entrare» si
distinguono solo così.

> **Il multiutente vero è un'altra cosa**, e arriverà con il servizio di sistema della fase 12: una
> sessione per ciascun utente, ciascuna con la propria regola sulla sessione locale. Oggi il
> server è di chi lo esegue, e il rifiuto degli altri è la forma corretta di quella limitazione —
> non un ripiego.

**⚠ Il validatore da solo non basta: chi non manda credenziali non viene validato.**
Accertato il 3 agosto, segnalato dall'utente («il client entra anche con una password vuota»).
IronRDP 0.13 interpella `CredentialValidator` **solo se il `ClientInfoPdu` porta delle
credenziali**; se non ce ne sono scrive `Skipping credential validation` e **lascia proseguire la
connessione** (`server.rs`, `client_accepted`). Con FreeRDP non si vede, perché manda comunque
nome e password vuota e PAM rifiuta; con un client che non dichiara nulla si entra senza che PAM
sia mai chiamato.

Il rimedio rovescia la regola invece di rattoppare il caso: una **guardia** che parte da *negato* a
ogni connessione, e che solo il validatore — accettando — apre. Chi non passa di lì:

- non riceve alcun desktop: `updates()` rifiuta e la connessione si chiude prima che si veda un
  pixel;
- non comanda nulla: gli eventi di tastiera e mouse vengono scartati prima di essere accodati.
  È difesa in profondità, perché fra l'arrivo degli eventi e la chiusura della connessione passa
  un istante.

*Conseguenze implementative:*

1. Non basta interrogare logind alla connessione: serve **sottoscriversi ai suoi segnali D-Bus**
   per accorgersi della comparsa di una sessione grafica locale e chiudere l'RDP in quel momento.
   Fatto il 3 agosto (`sentinella.rs`) — e nemmeno i segnali bastano da soli, perché il tipo di
   una sessione cambia dopo la nascita: §5.10 spiega come si riconosce una sessione grafica
   locale, e come la si apre per poterlo provare.
2. Poiché la seconda connessione è rifiutata, il server **deve accorgersi in fretta** che il
   client precedente è morto, altrimenti dopo una caduta di rete l'utente resta chiuso fuori
   dalla propria sessione. I keepalive TCP predefiniti attendono due ore prima della prima
   sonda: servono keepalive stretti o un heartbeat applicativo.

### 3.4-bis Cosa una sessione remota non deve poter fare

**Sospendere o ibernare la macchina.** Chi è collegato da lontano la spegnerebbe
sotto i piedi di chi ci sta lavorando da vicino o da un'altra sessione: il danno
non è suo, è di terzi, ed è per questo che non basta sconsigliarlo.

Si toglie la **capacità**, non si nasconde la voce di menu. Con
`AllowSuspend=no` e compagne in `/etc/systemd/sleep.conf.d/`, `logind` risponde
`CanSuspend = "no"`, GNOME smette da sé di mostrare la voce, e insieme sparisce
ogni altra strada: `loginctl`, un altro ambiente desktop, una scorciatoia di
tastiera. Nascondere il pulsante avrebbe lasciato aperte tutte le altre.

È **configurazione della macchina ospite**, non qualcosa che il server fa a
runtime: sta in `provision-vm.sh` e apparterrà al confezionamento della fase 12.
Verifica:

```bash
busctl call org.freedesktop.login1 /org/freedesktop/login1 \
       org.freedesktop.login1.Manager CanSuspend     # deve dire "no"
```

**Spegnimento e riavvio: tolti anche quelli.** Deciso dall'utente il 2 agosto.
Valgono le stesse ragioni della sospensione, con un'aggravante: uno spegnimento
deciso da lontano si ripara solo andando fisicamente davanti alla macchina.

Il meccanismo però è un altro, perché le due azioni passano da **polkit** e non
da `sleep.conf`: si nega `org.freedesktop.login1.power-off`, `reboot` e `halt`
con una regola in `/etc/polkit-1/rules.d/`. Verificato: `logind` risponde `no` a
`CanPowerOff`, `CanReboot` e `CanSuspend`, e GNOME smette da sé di mostrare le
voci.

Chi ha `sudo` può comunque spegnere, e va bene così: quella è amministrazione
della macchina, non una sessione remota che decide per gli altri.

---

### 3.5 Clipboard

Clipboard bidirezionale.

### 3.6 Sicurezza del trasporto

**TLS 1.2 e 1.3** come unico livello di sicurezza. Nessuna cifratura RDP classica, nessun FIPS,
nessun licensing.

### 3.7 Compatibilità client

| Piattaforma | Client di riferimento |
|---|---|
| Windows | `mstsc.exe`, Windows App |
| Linux | FreeRDP 3+, direttamente o via Remmina, GNOME Connections, KRDC |
| Android | **Remote Desktop Manager** (Devolutions) — il riferimento; Windows App — solo verifica |

**Percorso di rendering unico, solo EGFX.** Nessun fallback legacy: restano fuori ordini di
disegno GDI, cache di bitmap, glifi, pennelli e schermate, e compressione MPPC — cioè il grosso
di `libxrdp`.

> ✅ **La riserva è stata sciolta il 3 agosto, e ha prodotto una decisione.**
> Misurato contro `gnome-remote-desktop`: **Remote Desktop Manager non decodifica H.264.** Annuncia
> EGFX fino alla versione **10.7** — più in alto di mstsc — ma con `AVC_DISABLED` acceso in tutte le
> versioni. Il suo selettore dei codec si ferma a *RDP 8.0*, e l'H.264 su EGFX arriva con la 8.1.
> Verificato due volte, anche cambiando l'impostazione.
>
> **Deciso: Android resta fra i client di riferimento, e si aggiunge RemoteFX Progressive** come
> secondo codec sulla pipeline EGFX (§3.1).
>
> La soglia «solo EGFX» non è stata toccata — RDM la parla meglio di mstsc. A cambiare è **il codec
> dentro la pipeline**, non la pipeline.

**Su Android il riferimento è Remote Desktop Manager**, deciso dall'utente il 3 agosto 2026 dopo
averli provati: escludendo i prodotti di nicchia, quelli solo a pagamento e quelli legati al mondo
aziendale, è l'unico soddisfacente. Windows App resta nell'elenco per un motivo diverso — è quello che
la gente si trova installato — e va quindi **verificato**, non assunto come metro. Il perché e il
confronto stanno in [`client-android.md`](client-android.md) §1.

*Riserva*: quali client Android negozino effettivamente EGFX va verificato **provandoli** — il piano di
prove è in [`client-android.md`](client-android.md) §9, insieme a due scoperte che pesano su questa
riserva: il client ufficiale di FreeRDP su Android decodifica H.264 **in software** con OpenH264, e
tiene EGFX e H.264 su **due interruttori distinti, entrambi spenti per default**. Se un
test sul campo mostrasse un buco, si riapre la valutazione di un livello di fallback (Surface
Commands con RemoteFX), che costerebbe poco perché l'encoder RemoteFX serve comunque per rendere
nitido il testo dove l'H.264 in 4:2:0 sfuoca.

**Degradazione richiesta** su tutto ciò che è negoziato: audio su PCM se manca AAC; sessione
funzionante anche senza microfono; risoluzione fissa concordata alla connessione se manca
MS-RDPEDISP.

### 3.8 Aggancio al desktop

**L'asse rilevante è il compositor, non il desktop** — è lui a possedere schermo e input.
Tre famiglie coprono l'intero panorama Wayland (versioni verificate su Debian Trixie):

| Famiglia | Pacchetti | Desktop coperti |
|---|---|---|
| **Mutter** | mutter 48.7 | GNOME; Cinnamon 6.4.10 via Muffin 6.4.1 |
| **KWin** | kwin-wayland 6.3.6 | KDE Plasma 6.3.6 |
| **wlroots** | labwc 0.8.3, wayfire 0.9.0, sway 1.10.1 | XFCE, LXQt 2.1.1, Sway |

XFCE e LXQt non hanno un compositor proprio: girano sopra labwc o wayfire, quindi la famiglia
wlroots li copre senza lavoro aggiuntivo.

**Ordine di implementazione**: GNOME → KDE → XFCE → LXQt → Cinnamon.

**Meccanismi.** Cattura uniforme su tutte e tre le famiglie: **PipeWire ScreenCast**, che
consegna DMA-BUF. Input divergente, tramite le interfacce dirette dei compositor:

| Famiglia | Cattura | Input |
|---|---|---|
| Mutter | PipeWire via `org.gnome.Mutter.ScreenCast` | `org.gnome.Mutter.RemoteDesktop` |
| KWin | PipeWire via il protocollo Wayland **`zkde_screencast_unstable_v1`** | **libei**, con `connectToEIS` su D-Bus a KWin |
| wlroots | PipeWire, oppure `wlr-screencopy` diretto | `virtual-keyboard`, `virtual-pointer` |

> ⚠ **La riga di KWin è stata corretta il 7 agosto 2026, leggendo il codice** (`kde.md` §4 e §7).
> Diceva *«PipeWire via portale; interfacce KWin, protocollo `kde-fake-input`»*, ed era uno studio
> del 3 agosto mai verificato. Le due correzioni:
>
> - **il portale non serve**, ed è lui stesso un client dello stesso protocollo di KWin. La cattura
>   passa dal protocollo Wayland diretto, che però **è dietro un permesso**: si ottiene installando
>   un file `.desktop` con `X-KDE-Wayland-Interfaces` (`kde.md` §3). Nessun dialogo, mai;
> - **l'input passa da libei**, come su GNOME: KWin ha un backend libeis e consegna il descrittore
>   con una sola chiamata D-Bus, senza alcun controllo. `org_kde_kwin_fake_input` esiste ma è la
>   strada vecchia — quella che usa krfb, e che non sa produrre uno scatto di rotella.
>
> Ne discende che `input.c` e `tastiera.c`, scritti per libei, **si riusano quasi per intero**: le
> quattro differenze stanno in `kde.md` §7.2.

*Da verificare sul campo*: se Muffin abbia ereditato da Mutter la modalità senza monitor, e cosa
offra realmente `xdg-desktop-portal-xapp` per Cinnamon.

### 3.9 Portabilità fra distribuzioni

**Degradazione graduale** invece del fallimento:

| Se manca | Ripiego | Cosa si perde |
|---|---|---|
| VA-API / NVENC | Codifica software x264 | CPU impegnata; niente 4K, ma 1080p e 2K sì |
| PipeWire | `wlr-screencopy` diretto (solo wlroots) | Nulla su wlroots; su GNOME e KDE PipeWire c'è sempre |
| Portale desktop | Interfacce dirette del compositor | Nulla — è già la via principale |
| logind / elogind | Registro interno delle sessioni | Precisione nel rilevare la sessione grafica locale |

**Piattaforme di riferimento**, cioè collaudate da noi: **Debian e Ubuntu**.

Le altre funzionano se soddisfano il minimo: logind o elogind, PipeWire recente,
xdg-desktop-portal recente, Mesa con VA-API o driver NVIDIA, glibc, un compositor di una delle
tre famiglie. In pratica le distribuzioni dal 2024-2025 in avanti.

Distinzione da mantenere: *supportato* significa provato da noi; *funzionante* significa che lo
sarà se il sistema è abbastanza recente.

---

## 4. Fuori scope

### 4.1 Escluso esplicitamente dall'utente

| Funzionalità | Stato in xrdp | Costo del taglio |
|---|---|---|
| Redirezione USB | Già assente | Nessuno |
| Redirezione stampanti | Rilevata e rifiutata (`devredir.c:989`) | Nessuno |
| Autenticazione Kerberos e a dominio | Non nativa, solo via PAM | Marginale |
| Redirezione dischi del client | Implementata in xrdp | Elimina IRP asincroni e filesystem virtuale FUSE |
| Multi-monitor | Implementato in xrdp | Semplifica surface EGFX e contesti encoder |

**Attenzione**: escludere l'autenticazione aziendale **non** significa escludere PAM, che resta
il meccanismo con cui verificare le credenziali locali. Decade il contorno:
`domain_user_separator`, gruppi `TerminalServerUsers` e `TerminalServerAdmins`,
`enable_token_login`, messaggi per scenari gateway, registrazione in `utmp` e `wtmp`.

### 4.2 Multi-tenancy e amministrazione

Politiche di allocazione delle sessioni, controllo di accesso per gruppi di sistema, strumenti
di amministrazione, contabilizzazione delle sessioni, modalità FIPS, licensing RDP, shell
alternative amministrate.

### 4.3 Compatibilità legacy

Ordini di disegno GDI, cache di bitmap, glifi, pennelli, schermate e colori, compressione MPPC,
cifratura RDP classica, profondità di colore a tavolozza.

### 4.4 Componenti paralleli

Proxy VNC e proxy RDP, backend Xvnc, canale video proprietario, RemoteApp (RAIL), smartcard,
porte seriali e parallele, finestra di login con toolkit grafico proprietario.

### 4.5 Desktop X11

**Non si perde nessuna applicazione.** Sessione X11 e applicazione X11 sono cose diverse: le
applicazioni X11 girano dentro una sessione Wayland tramite **XWayland**, e per REMOTIX sono
finestre come tutte le altre. Restano fuori solo gli utenti il cui desktop offre *unicamente*
una sessione X11.

Motivo dell'esclusione: supportare X11 significherebbe **un secondo percorso completo di
cattura e input**, in sostanza un secondo progetto dentro il progetto, mentre tutti i desktop
in elenco hanno ormai una sessione Wayland. È una spesa che cresce mentre il problema che
risolve si restringe.

---

## 5. Vincoli tecnici accertati

### 5.1 RDP è tappato a H.264

I codec ammessi da MS-RDPEGFX sono RemoteFX, ClearCodec, Planar, AVC420 e AVC444/v2.
**Non esistono né HEVC né AV1.** Le GPU recenti (Intel Arc, AMD RDNA3+, NVIDIA Ada+) hanno
encoder AV1 che darebbero il 30-40% di banda in meno, ma non sono utilizzabili con client RDP
standard. Sfruttarli richiederebbe un client proprio, che contraddirebbe l'obiettivo.

### 5.2 Il 4:2:0 sfuoca il testo colorato

xrdp implementa **solo AVC420** (4:2:0, formato NV12). Gli identificativi `AVC444` e
`AVC444V2` sono dichiarati in `xrdp_egfx.h:105` ma mai usati.

AVC444 risolve il problema ma trasporta due flussi H.264, quindi circa il doppio della banda:
insostenibile come modalità predefinita. Strategia: AVC420 come base, AVC444 attivabile su
connessioni migliori; in alternativa codifica per regioni, con il testo in RemoteFX Progressive
e il video in H.264.

> **Aggiornamento del 3 agosto: la seconda alternativa costa molto meno di quando è stata scritta.**
> L'encoder RemoteFX Progressive **va scritto comunque** per servire Android (§3.1), quindi la
> codifica per regioni — testo in RFX, video in H.264 — smette di essere un'ipotesi con un costo
> proprio e diventa una **combinazione di due pezzi che ci saranno entrambi**.
>
> Resta comunque la strada più difficile delle due: richiede di classificare le regioni dello schermo
> in «testo» e «immagine» fotogramma per fotogramma, che è un problema aperto a sé. AVC444 su
> connessioni buone resta l'opzione più economica. Ma la porta ora è aperta, e non era scontato.
>
> Nota di merito su AVC444: `gnome-remote-desktop` lo implementa **per fotogramma**, mandando la sola
> luma e completandola con la croma poco dopo quando il collegamento è tranquillo — più fine di
> «attivabile su connessioni migliori» (vedi [`gnome-remote-desktop.md`](gnome-remote-desktop.md) §9.3).

> ⛔ **AVC444 è fuori, per decisione dell'utente del 7 agosto 2026.** *«In un precedente tentativo
> l'AVC444 dava problemi di luminanza.»*
>
> È un'esperienza sua, non nostra — REMOTIX non l'ha mai scritto — e va presa sul serio proprio
> perché descrive il difetto tipico di quel codec: la vista ausiliaria trasporta la crominanza
> **impacchettata dentro un piano di luminanza** ([MS-RDPEGFX] 2.2.4.6), quindi un errore di
> impacchettamento non si vede come un colore sbagliato, si vede come **luminosità sbagliata**. Un
> difetto che si presenta lontano dalla propria causa, e servito da un client solo su tre (§1.7 di
> `REFERENCE.md`: lo rende mstsc).
>
> **Quel che resta per il testo colorato nitido**, se un giorno servisse, è **RemoteFX Progressive**,
> che è a wavelet su RGB e non sottocampiona nulla — ed è già scritto e in servizio per Android. Il
> prezzo è la CPU: 1,20 core contro 0,47 dell'AVC420 in GPU (fase 9). Non si fa ora; si sa dov'è.

### 5.3 L'accelerazione hardware richiede il percorso a copia zero

A 4K e 30 fps un fotogramma RGBA è 33 MB: una copia via CPU costerebbe circa 1 GB/s di sola
memoria, prima ancora della conversione di colore. Wayland espone i DMA-BUF nativamente tramite
PipeWire; su X11 non esiste una strada pulita.

### 5.4 IronRDP non rende su mstsc — accertato sul campo

Prova del 1 agosto 2026, fase 1. Con `ironrdp-server` 0.13.0, il client Microsoft
(`mstsc.exe`) **non disegna nulla** in nessuna configurazione, mentre FreeRDP 3 su Linux e un
client Android moderno disegnano correttamente in tutte.

| Configurazione | mstsc | FreeRDP / Android |
|---|---|---|
| Bitmap classici, RemoteFX attivo | nero | ok |
| Bitmap classici, RemoteFX spento, fotogramma intero da 8,3 MB | riquadri sparsi | ok |
| Bitmap classici a bande da 512 KB | nero | ok |
| EGFX V10.0, fotogrammi non compressi | nero | ok |
| EGFX V8.1 senza AVC, fotogrammi non compressi | nero | ok |
| EGFX V8.1, **riquadro 64×64** in un solo frammento | nero | ok |

Dai registri del server, con mstsc collegato: TLS negoziato, capacità scambiate,
`Client accepted`, canali dinamici aperti, EGFX negoziato, superficie creata delle dimensioni
giuste, fotogrammi accodati e inviati senza errori, ridimensionamento gestito, disconnessione
pulita. Eppure schermo nero per l'intera sessione.

### Causa vera, trovata il 2 agosto: la superficie non veniva agganciata all'uscita

**In EGFX, creare una superficie e agganciarla all'uscita video sono due operazioni distinte**,
con due messaggi distinti: `CreateSurface` e `MapSurfaceToOutput`. In IronRDP corrispondono a
`create_surface()` e `map_surface_to_output()`, e la prima **non** chiama la seconda.

REMOTIX chiamava solo la prima. Il client riceveva quindi i fotogrammi, li decodificava e li
scriveva in una superficie non collegata allo schermo.

**Come si è trovata**: tracciando ogni messaggio scambiato e confrontando una sessione mstsc con
una FreeRDP. Il dato decisivo è stato che **mstsc confermava ogni fotogramma con 6-8 ms di
latenza** — cioè li elaborava davvero — pur non mostrando nulla. Questo escludeva ogni ipotesi
sul contenuto del flusso e spostava il sospetto su cosa il client fosse stato istruito a farne.

**Perché era sfuggito per due giorni**: FreeRDP e i client Android disegnano la superficie anche
senza l'aggancio. La loro indulgenza mascherava il difetto e faceva sembrare mstsc l'anomalia,
mentre era l'unico dei tre a comportarsi correttamente.

Lungo la strada sono stati corretti altri quattro difetti reali, tutti nostri:

| Difetto | Sintomo su mstsc |
|---|---|
| Elenco delle versioni EGFX troppo rado: mancava la famiglia 10.x intermedia, e mstsc si ferma alla 10.6 | ripiegava sulla 8.1 dove AVC420 risulta spento → **zero fotogrammi inviati** |
| Altezza non allineata: serve multipla di **64** (larghezza multipla di 16) | rinegoziazione e disconnessione |
| Bordi della regione AVC420 fuori-di-uno: sono **inclusivi** | rinegoziazione e disconnessione |
| `ResetGraphics` inviato con l'elenco dei monitor **vuoto** | immagine disegnata fuori posto, spostata a destra |

**Il filo conduttore di tutti e cinque i difetti**: informazioni che omettevamo e che i client
indulgenti — FreeRDP e Android — supplivano da soli, mentre mstsc prendeva alla lettera. Non era
il client Microsoft ad essere anomalo: era l'unico dei tre a comportarsi correttamente.

**Regole operative che ne discendono**, valide per tutto il progetto:

- l'allineamento del codificatore si assorbe **riempiendo il bordo**, non riducendo lo schermo:
  il desktop resta della dimensione chiesta dal client;
- ogni geometria dichiarata al client va verificata sulla convenzione **inclusiva o esclusiva**;
- la tela grafica va dichiarata **con la definizione del monitor**, non con l'elenco vuoto.

### La conclusione tratta il 1 agosto era sbagliata

Il 1 agosto si era concluso che IronRDP fosse incompatibile con mstsc e si era deciso di
migrare a FreeRDP. **Lo studio del codice di `gnome-remote-desktop`, suggerito dall'utente, ha
smentito quella conclusione.**

Il riferimento invia via EGFX **soltanto tre codec** — RemoteFX Progressive, AVC420, AVC444 —
e in tutto il progetto non esiste una riga che usi `RDPGFX_CODECID_UNCOMPRESSED`
(`grd-rdp-dvc-graphics-pipeline.c`, funzione `get_rdpgfx_codec_id`).

Noi inviavamo esattamente quello. Con ogni probabilità **mstsc non rende i fotogrammi EGFX non
compressi**: il difetto era nostro, non della libreria.

Ne consegue che le sei configurazioni fallite **non erano sei prove indipendenti**: condividevano
tutte lo stesso vizio, quindi valevano come una sola.

> ⚠ **Superato dal vincolo del 3 agosto (§8-bis): si usa FreeRDP 3.** Quanto segue resta agli atti
> perché la diagnosi vale ancora — il difetto era nostro, non della libreria — e perché le cinque
> correzioni elencate sopra valgono con qualunque libreria. La scelta di stack invece non è più aperta.

**Stato di allora**: si resta su IronRDP e si verifica l'ipotesi corretta, cioè inviare **AVC420**.
Il codificatore H.264 serve comunque al progetto, quindi non è lavoro sprecato ma solo anticipato.
Se anche con H.264 mstsc resta nero, la migrazione a FreeRDP avrà finalmente una prova solida.

*Nota su RemoteFX Progressive*: IronRDP espone `send_remotefx_progressive_frame`, ma il suo
modulo `progressive` sa solo **serializzare** la struttura del messaggio — non contiene un
codificatore da pixel. Usarlo richiederebbe di scrivere noi l'encoder. FreeRDP invece ce l'ha
già pronto: è un punto a suo favore, da ricordare se si dovesse tornare sulla decisione.

*Lezione di metodo*: quattro ipotesi inseguite prima di consultare il secondo parere e prima di
leggere un'implementazione funzionante. Entrambi sono arrivati dopo e sono valsi più dei
tentativi. **Studiare il riferimento viene prima di ipotizzare.**

### 5.5 Gli encoder hardware rendono peggio a bitrate bassi

A parità di banda molto stretta, x264 con preset lenti supera gli encoder GPU, che sono
ottimizzati per la velocità. Resta comunque la scelta obbligata per il tempo reale a 4K, e le
generazioni recenti hanno ridotto molto il divario.

---

### 5.6 La sessione senza monitor — accertato sul campo il 2 agosto

Verificato su Debian Trixie, GNOME 48.7, Mutter 48.7, PipeWire 1.4.2, dentro una macchina
virtuale con GPU virtio senza accelerazione.

**La sessione deve dichiararsi.** `gnome-shell --headless` avviato da una shell
qualunque produce una sessione che *funziona* ma non *si presenta*: niente
`XDG_CURRENT_DESKTOP`, e `XDG_SESSION_TYPE=tty` invece di `wayland`. Le
applicazioni di GNOME leggono quelle variabili per decidere se sono a casa
propria, e «Impostazioni» si rifiuta di partire con
`Running gnome-control-center is only supported under GNOME and Unity`.

Basta esportare `XDG_CURRENT_DESKTOP=GNOME` **prima** di avviare il compositore:
le applicazioni che il desktop lancia ereditano l'ambiente di `gnome-shell`.

**Una sola, non quattro.** Il primo tentativo ne aggiungeva anche
`XDG_SESSION_TYPE=wayland`, `XDG_SESSION_DESKTOP=gnome`,
`GNOME_SHELL_SESSION_MODE=user` e un `dbus-update-activation-environment
--systemd`. Risultato: «Impostazioni» partiva e **smettevano di partire tutte le
altre applicazioni**, con `Error 71 (Protocol error) dispatching to Wayland
display`. Dichiarare `XDG_SESSION_TYPE=wayland` è una bugia — per `logind` quella
sessione è `tty` — e `dbus-update-activation-environment --systemd` sporca il
gestore utente di systemd in modo che sopravvive al riavvio del compositore.

In una sessione vera questo lo fa `gnome-session`. Noi non lo usiamo, quindi
tocca a noi — e dalla fase 5 toccherà a REMOTIX, che la sessione la avvierà lui.

**GDM non serve.** `gnome-remote-desktop` avvia le sessioni senza schermo appoggiandosi a un
passaggio di consegne con GDM, e nella nostra VM quel passaggio fallisce. Non è un problema
nostro: quel meccanismo esiste perché `gnome-remote-desktop` deve agganciarsi alla schermata di
accesso, mentre REMOTIX la sessione la avvia lui. Basta:

```
gnome-shell --headless --no-x11
```

Senza `--virtual-monitor`: il monitor virtuale lo chiede REMOTIX a compositore già avviato, della
misura che vuole il client — vedi «Il monitor si chiede, non si impone» più sotto.

**Xwayland non completa l'avvio, e a volte si porta dietro il compositore.** È l'ostacolo
incontrato nella fase 2. In questa VM Xwayland **non serve mai** le richieste X: il display
esiste, il processo è vivo, ma resta fermo in attesa e non risponde. Nel registro l'unico
indizio è `Failed to initialize glamor, falling back to sw`.

Nella maggior parte degli avvii il compositore prosegue lo stesso e la sessione è pienamente
usabile — solo senza applicazioni X11. In circa un avvio su sei, invece, resta appeso anche lui:
GNOME scrive nel registro che è pronto, prende possesso dei suoi nomi sul bus, e poi **non
risponde più a nessuna chiamata**, nemmeno a `SIGTERM`. È la firma di un ciclo principale fermo.

Il tranello diagnostico: `org.freedesktop.DBus.Peer.Ping` e `Introspect` continuano a
rispondere, perché li serve la libreria D-Bus per conto proprio senza disturbare il programma.
Sembrano quindi la prova che il processo sia vivo, e non lo sono. La prova vera è chiamare un
metodo qualsiasi implementato davvero dal programma: se quello tace, il ciclo è fermo.

Due ipotesi si sono rivelate false, e vale la pena ricordarlo per non riprenderle: non è
`xauth` mancante, e non è il monitor virtuale chiesto sulla riga di comando. Verificato
ripetendo gli avvii e contandoli, perché a colpo singolo un difetto intermittente si legge come
un difetto deterministico — ed è esattamente l'errore che ho commesso.

Conseguenze pratiche: si avvia la sessione con `--no-x11` finché il nodo non è sciolto, e chi
avvia la sessione **deve verificare che risponda** entro pochi secondi, riavviandola altrimenti.
Il sospetto principale resta l'assenza di accelerazione grafica nella VM. **Va sciolto**, perché
§4.5 tiene X11 nello scope: senza Xwayland le applicazioni X11 non girano, e sono ancora la
maggioranza.

**Si usano le interfacce dirette di Mutter, non il portale.** `org.gnome.Mutter.ScreenCast`
versione 4. Il portale `xdg-desktop-portal` è pensato per chi chiede il permesso a un utente
seduto davanti allo schermo, e in una sessione senza monitor quell'interazione non può avvenire.

**Regole della cattura, tutte verificate:**

- la sessione di cattura **vive quanto la connessione D-Bus** di chi l'ha creata: se il processo
  si disconnette, Mutter la chiude e il flusso muore senza preavviso. Una sequenza di comandi
  `gdbus` separati non può funzionare, e nemmeno un processo che chiude la connessione dopo la
  configurazione;
- il nodo PipeWire viene annunciato da un **segnale emesso durante `Start`**: bisogna mettersi
  in ascolto prima di chiamarlo, o si aspetta per sempre un annuncio già passato;
- lo **stride si legge dal chunk del buffer**, mai calcolato come `larghezza × 4`. Il produttore
  allinea le righe come gli conviene. Dedurlo produce immagini oblique;
- per restare in memoria ordinaria ed evitare DmaBuf **non si dichiara il campo `modifier`** nel
  formato proposto: la negoziazione DmaBuf parte solo se il consumatore annuncia i modificatori
  che sa importare. Tacendo, si ottiene memoria condivisa senza dover aggiungere altro. Servirà
  invece il percorso DmaBuf in fase 9;
- Mutter invia un fotogramma **solo quando qualcosa cambia**. Un desktop immobile non produce
  nulla, e questo è il comportamento desiderato, non un guasto: chi consuma non deve
  interpretare il silenzio come un errore.

  Ne discende una regola che costa cara a scoprirsi: **l'ultimo fotogramma va conservato e
  rispedito appena c'è dove disegnarlo**. Un fotogramma che arriva prima che il client abbia
  finito di negoziare la pipeline grafica non si può disegnare, e se lo si butta su un desktop
  fermo non ne arriverà un altro: il client resta a fissare uno schermo nero a tempo
  indeterminato, finché qualcuno non muove qualcosa. Il difetto è insidioso perché **si corregge
  da sé** appena il desktop cambia, quindi in prova sembra un ritardo d'avvio e non un difetto.

**Il monitor si chiede, non si impone.** REMOTIX usa `RecordVirtual`, che fa creare a Mutter un
monitor virtuale apposta, invece di `RecordMonitor` su uno schermo preesistente. La differenza
conta: con `RecordVirtual` **la risoluzione la decide chi guarda**, perché si concorda nella
negoziazione PipeWire. È la base su cui poggerà la risoluzione dinamica della fase 6.

La misura si dichiara come **intervallo chiuso sul valore voluto** — minimo, preferito e massimo
coincidenti — e non come valore singolo:

- un valore singolo non lascia margine di accordo, e Mutter respinge la proposta con
  `no more input formats`, che è il suo modo di dire che non ha trovato nulla in comune;
- un intervallo aperto la lascia scegliere a lui, e sceglie 1280×720 ignorando la richiesta.

> ✅ **Il primo punto è stato smentito da una misura il 4 agosto 2026, con la catena in C.**
> Il **rettangolo singolo funziona**, ed è la forma che REMOTIX usa adesso — la stessa del
> riferimento (§11.1 di [`gnome-remote-desktop.md`](gnome-remote-desktop.md)). Provate entrambe le
> forme contro Mutter 48.7, **entrambe negoziano esattamente la misura chiesta**; l'intervallo
> chiuso resta raggiungibile con `REMOTIX_MISURA_INTERVALLO=1` per poterle confrontare senza
> ricompilare.
>
> Il `no more input formats` del 2 agosto era quindi legato alla catena di allora — il pacchetto
> Rust di PipeWire — o a una proposta che ometteva `is-platform: true` in `RecordVirtual`, che ora
> REMOTIX dichiara. **Il terzo punto resta vero e importante**: un intervallo *aperto* lascia
> scegliere a Mutter, che sceglie 1280×720.

Alla misura vanno affiancate la cadenza dichiarata a zero e un massimo come intervallo:
significa «mandami un fotogramma quando cambia qualcosa, non a ritmo fisso», che è esattamente
il comportamento che serve a un desktop remoto.

---

### 5.7 Il disegno del desktop e il ridimensionamento — accertato sul campo il 2 agosto

Sono le regole emerse portando il desktop vero dentro i client (fase 3). **Violarne una qualsiasi
produce uno schermo nero, o un'immagine che si forma lentissimamente, senza alcun messaggio
d'errore da nessuna delle due parti.** Vanno rilette prima di toccare `desktop.rs` o `egfx.rs`.

Il filo comune: ciascuna è stata scoperta perché **un solo client** la faceva emergere. Nessuno
dei tre copre i casi degli altri, e le differenze non sono casuali:

| client | cosa fa di suo | cosa fa emergere |
|---|---|---|
| FreeRDP | negozia EGFX subito, ridimensiona solo se glielo si chiede | nulla: è il più accomodante |
| mstsc | negozia EGFX subito, **non ridimensiona da sé** | in fase 1, il rigore sulla geometria |
| Android | chiede la propria misura **prima** di negoziare EGFX | tutte le regole qui sotto |

Che mstsc non ridimensioni automaticamente è il motivo per cui non ha mai innescato il percorso
dove si nascondevano le regole 1 e 2. Resta comunque da riprovare a ogni modifica: non innescare
un percorso non vuol dire essere immune a chi lo tocca.

#### Regola 1 — con EGFX attivo, un cambio di risoluzione non riattiva la sessione

La misura nuova si comunica **ridichiarando la tela grafica**, cosa che avviene creando la
superficie della nuova dimensione. Annunciarla invece come ridimensionamento della sessione
costringe RDP alla **sequenza di riattivazione**: il client rifà lo scambio delle capacità e
azzera il proprio stato grafico.

Verificato sul client Android: dopo una riattivazione **non rinegozia più EGFX**, per il resto
della sessione. Da lì in poi resta il solo percorso di ripiego, che manda pixel non compressi —
dieci megabyte a fotogramma — e la schermata si forma lentissimamente.

#### Regola 2 — un ridimensionamento chiesto prima della negoziazione va rinviato, non applicato

Il client Android chiede la propria misura **entro un decimo di secondo dalla connessione**,
prima di aver negoziato EGFX. Applicarlo subito ricade nella regola 1 e rovina la sessione.

Si rinvia fino a un secondo e mezzo aspettando la pipeline: quando arriva — e arriva in poche
decine di millisecondi — la misura passa per la tela grafica. Solo se non arrivasse affatto si
ricorre al ridimensionamento della sessione.

#### Regola 3 — l'ultimo fotogramma si conserva e si rispedisce

Mutter manda un fotogramma solo quando qualcosa cambia (§5.6). Un fotogramma arrivato prima che
il client abbia finito di negoziare non si può disegnare, e su un desktop fermo non ne arriverà
un altro: il client resta nero a tempo indeterminato.

Il difetto è insidioso perché **si corregge da sé** appena qualcuno muove qualcosa sullo
schermo, quindi in prova sembra un ritardo d'avvio e non un difetto.

#### Regola 3-bis — dopo un cambio di misura si aspetta che il desktop si sia ridisegnato

Segnalata dall'utente il 3 agosto — «sfondo grigio parziale a destra» — e riconoscibile da un
dettaglio che vale più di ogni ipotesi: **alla prima connessione si vede sbagliata, alla seconda
giusta**.

Quando il monitor virtuale cambia misura, Mutter manda un fotogramma **subito**, prima che GNOME
abbia ridisegnato: lo sfondo è ancora quello della misura vecchia e il resto è vuoto. Se il client
precedente era a 1920 e il nuovo chiede 2560, si vede il desktop coprire esattamente il 75% della
larghezza. E siccome su un desktop fermo non ne arrivano altri (regola 3), quell'immagine parziale
**resta** finché l'utente non tocca qualcosa — il che la fa sembrare un difetto grafico e non un
problema di tempi.

**Cosa manda Mutter, misurato in PNG fuori dalla catena RDP** (con `prova-cattura`, che salva i
fotogrammi su disco senza passare da RDP — è il modo per distinguere «GNOME disegna male» da «il
client mostra male»):

| fotogramma | contenuto |
|---|---|
| primo | barra in alto e **solo il colore di fondo**: niente sfondo, niente finestre |
| secondo | il desktop completo |
| poi | silenzio, perché il desktop è fermo |

Il difetto quindi **non è nostro**, ma diventa nostro se spediamo il primo: su un desktop fermo
quella immagine resta.

Si aspetta quindi il ridisegno raccogliendo i fotogrammi finché non smettono di arrivare — ma
**fidandosi del silenzio solo dopo il secondo**, perché il silenzio fra il primo e il secondo è
esattamente dove cadeva la prima stesura di questa attesa. Trecento millisecondi di quiete, tetto
di due secondi e mezzo.

> ⚠ **Questo toglie il fotogramma vuoto, ma su mstsc il sintomo resta.** Provato il 3 agosto: con
> FreeRDP l'immagine è piena, con mstsc no. Il difetto è quindi solo in parte quello descritto
> qui, e la parte che manca è la **questione aperta n.9**, dove sta tutto ciò che è già stato
> escluso — perché non lo si rifaccia da capo.

Vale **solo dopo un rimontaggio**. Al riaggancio alla stessa misura non c'è nulla da aspettare: il
fotogramma conservato è già quello giusto, ed è ciò che fa ricomparire il desktop all'istante.

#### Regola 4 — serve un percorso di ripiego, ma non deve arrivare per primo

Alcuni client aprono la connessione, restano in attesa di un aggiornamento grafico qualsiasi e,
non ricevendone, **si arrendono dopo una decina di secondi** e riprovano. Senza un ripiego a
bitmap il primo tentativo non produce nulla e si vede nero per tutta la durata dei tentativi a
vuoto.

Il ripiego però va **ritardato di un secondo**: i client di riferimento negoziano EGFX in un
decimo di secondo, e se il ripiego parte subito fa in tempo a disegnare qualche banda di pixel
grezzi — l'utente vede comparire una schermata a strisce, che solo dopo viene completata.

#### Regola 5 — una sola sorgente per volta, perché la pipeline grafica è una sola

Alcuni client aprono una seconda connessione prima di chiudere la prima. Se restano attive
entrambe, **due codificatori H.264 indipendenti**, ciascuno con i propri fotogrammi chiave,
scrivono sulla stessa superficie: il decodificatore riceve due flussi mescolati e non ricostruisce
nulla. Chi resta indietro di numero si fa da parte.

#### Regola 6 — lo stato grafico appartiene alla connessione, non al server

Canale, capacità negoziate e superfici valgono per **quel** client e per nessun altro. Tenerne
uno solo per tutti sembra funzionare finché le connessioni non si sovrappongono — e si
sovrappongono, perché alcuni client ne aprono una prima di chiudere l'altra.

Con uno stato unico, la connessione che muore per ultima azzera anche quella appena nata, che
resta a disegnare su una pipeline dichiarata spenta: schermo nero senza alcun errore. Il difetto
è peggiore di quelli sopra perché **dipende dall'ordine in cui le connessioni finiscono**, quindi
si presenta a intermittenza e non si riproduce a comando.

Corollario: distinguere una connessione nuova da una riattivazione si fa confrontando l'identità
dello stato, non contando le sorgenti aperte.

#### Regola 7 — non si aspetta mai dentro il ciclo asincrono

La cattura vive su un thread suo, e viene aperta e chiusa da dentro il ciclo del server.
Attendere lì l'avvio o la fine di quel thread **ferma un thread del runtime**, e con esso tutte
le connessioni che gli sono affidate — non solo la propria.

Vale per le attese esplicite e per quelle nascoste: un `Drop` che aspetta la fine di un thread è
un'attesa a tutti gli effetti, e non si vede leggendo il punto in cui l'oggetto viene lasciato
cadere. Si manda il segnale di fermata e si prosegue.

**Come si controlla**: a connessioni chiuse, il processo non deve avere thread di cattura
residui. Bastano i thread del runtime più il principale.

#### Come si verifica di non aver rotto nulla

Tre prove, in quest'ordine. Le prime due si fanno da soli, la terza richiede l'utente.

1. **Linux, connessione semplice** — `xfreerdp3 /v:… /gfx:avc420`: il desktop compare subito.
2. **Linux, ridimensionamento a caldo** — con `/dynamic-resolution`, si cambia la misura della
   finestra: l'immagine segue senza sporcarsi. Nel registro dev'esserci
   `ridimensiono la tela grafica`, **mai** una seconda `nuova sorgente`.
3. **Android e Windows** — il desktop compare all'istante, non "si forma" progressivamente, e non
   c'è la schermata a strisce.

Nel registro, la firma di una sessione sana è: **una sola** `nuova sorgente`, seguita da
`EGFX negoziato`, e i ridimensionamenti che passano per `ridimensiono la tela grafica` oppure
`applico il ridimensionamento rinviato con_egfx=true`. Una seconda `nuova sorgente` a pochi
istanti dalla prima significa che è avvenuta una riattivazione: è il sintomo da cui ripartire.

---

### 5.8 L'input — accertato sul campo il 2 agosto

Sono le regole emerse rendendo comandabile il desktop (fase 4). A differenza di quelle di §5.7,
queste **non producono schermi neri**: producono errori espliciti di Mutter, che però arrivano
in un punto lontano da dove sta la causa.

#### La via scelta: D-Bus, non libei

> ⚠ **Ribaltata il 4 agosto 2026, chiudendo la fase 3: si passa a libei.** Quanto segue descrive la
> scelta di allora e resta agli atti, perché le misure di questo paragrafo — la rotella, i tasti
> premuti, l'accodamento — valgono con qualunque trasporto.
>
> Il motivo del ribaltamento non è che i metodi `Notify*` non funzionino: funzionano, ed erano
> stati misurati. È che **libei consegna quattro cose che i `Notify*` non hanno**, e la prima
> chiude una questione aperta invece di rimandarla:
>
> | | `Notify*` | **libei** |
> |---|---|---|
> | Disposizione di tastiera della sessione | non la si legge | **`ei_device_keyboard_get_keymap`** — chiude la questione n.7 |
> | Stato reale di BlocMaiusc/BlocNum | si indovina | **evento `KEYBOARD_MODIFIERS`** |
> | Punto di sincronizzazione | non c'è | **`ei_ping`** |
> | Regioni degli schermi | si calcolano | **`ei_region` con `mapping_id`** |
>
> A questo si aggiunge che dal 3 agosto `gnome-remote-desktop` non è più un'analogia ma **codice
> trasferibile** (§8-bis): stesso linguaggio, stessa libreria, e libei è la sua strada. Il costo è
> una dipendenza in più (`libei-dev` 1.3.901 è in Trixie) e dispositivi virtuali da negoziare
> invece che imporre.
>
> **La fase 3 non ha scritto una riga di input**: crea la sessione di controllo — che serve
> comunque, perché la cattura vi si registra — e lascia alla fase 4 l'innesto di `ConnectToEIS`.
> La decisione era da prendere qui perché la sessione di cattura si crea in modo diverso nei due
> casi; sul filo la differenza è una chiamata sola, quindi tornare indietro costa poco.

Si usa `org.gnome.Mutter.RemoteDesktop` con i metodi `Notify*`, come per la cattura si usa
l'interfaccia diretta invece del portale. `gnome-remote-desktop` è passato a **libei**; non lo si
è seguito, perché libei serve a chi deve *chiedere il permesso* e *negoziare quali dispositivi
emulare*, mentre qui la sessione la avvia REMOTIX e i dispositivi li decide REMOTIX. I metodi
`Notify*` fanno esattamente ciò che serve, con una dipendenza in meno.

#### Regola 1 — controllo e cattura sono una coppia, e l'ordine dei quattro passi è obbligato

Il puntatore si muove in coordinate assolute **dentro un flusso di cattura**: `Notify­Pointer­Motion­Absolute`
vuole il percorso D-Bus dello *stream* di ScreenCast. Perché Mutter accetti di collegarli, la
sessione di cattura va creata dichiarando `remote-desktop-session-id`.

Da lì discende una sequenza che non ammette permute, e che ogni permuta punisce con un errore
diverso:

1. si crea la sessione di controllo e se ne legge `SessionId`, **senza avviarla**;
2. si crea la sessione di cattura dichiarando quell'identificativo;
3. **adesso** si avvia il controllo;
4. si registra il monitor virtuale e si avvia il **flusso** — non la sessione di cattura.

I due paletti, ciascuno costato un tentativo:

- avviare il controllo prima del punto 2 →
  `Remote desktop session already started`: Mutter registra la cattura solo su un controllo non
  ancora partito;
- avviare la cattura con `Session.Start` →
  `Must be started from remote desktop session`: una cattura associata la mette in moto l'avvio
  del controllo, e resta da far partire il singolo flusso con `Stream.Start`.

Lo stesso vale simmetricamente in chiusura: `Session.Stop` su una cattura associata risponde
`Must be stopped from remote desktop session`. Si chiude fermando il controllo, e la cattura lo
segue.

**Conseguenza sul ridimensionamento**: siccome la cattura si rifà a ogni cambio di misura (§5.6)
e una cattura nuova non si registra su un controllo già avviato, **anche il controllo si rifà**.
Il prezzo è che un tasto tenuto premuto mentre il client ridimensiona non risulta più premuto
dopo, perché la tastiera virtuale è un'altra.

> ✅ **Prezzo estinto il 5 agosto 2026, con la fase 6.** Il ridimensionamento non rifà più la
> cattura: si aggiornano i parametri del flusso PipeWire con `pw_stream_update_params` e Mutter
> riconfigura il monitor virtuale al suo posto (§11.3 di `gnome-remote-desktop.md`). Cattura,
> controllo e dispositivi virtuali di libei restano gli stessi, quindi resta anche il conto dei
> tasti premuti. Misurato sul banco della fase 6: `misura del monitor virtuale cambiata … senza
> rifare la cattura`, con **un solo** montaggio del monitor virtuale in tutta la sessione.

#### Regola 2 — la connessione D-Bus è una sola, condivisa con la cattura

Mutter verifica che le chiamate `Notify*` arrivino **dallo stesso peer** che ha creato la
sessione di controllo. Non verifica il peer nell'associare la cattura, ma tenerle sulla stessa
connessione toglie di mezzo la questione ed è ciò che fa anche `gnome-remote-desktop`.

Il prezzo si paga sulla regola di §5.6 «la sessione vive quanto la connessione»: quella
connessione ora vive quanto il server, quindi **le sessioni vanno chiuse esplicitamente**.
Lasciarle cadere significa un monitor virtuale in più a ogni ridimensionamento.

#### Regola 3 — non si chiama D-Bus dentro il ciclo di IronRDP

I metodi di `RdpServerInputHandler` sono sincroni e IronRDP li chiama dentro il proprio ciclo
asincrono, tenendo un lucchetto. Una chiamata D-Bus lì dentro fermerebbe un thread del runtime e
con esso tutte le connessioni affidate a quel thread: è la regola 7 di §5.7 vista dall'altro
lato. Si accoda su un canale non limitato — operazione che non attende mai — e un compito
separato svuota la coda.

Gli spostamenti del puntatore si **accorpano**: di una raffica conta dove il puntatore arriva,
non la strada che ha fatto. Si scarta uno spostamento solo quando il successivo è ancora uno
spostamento: se in mezzo c'è un clic, la posizione conta eccome.

#### Regola 4 — si tiene il conto di ciò che è premuto, e lo si dimentica a connessione finita

Mutter rifiuta con `Invalid key event` sia il rilascio di un tasto che non risulta premuto, sia
la pressione di uno che lo è già. I client mandano regolarmente l'uno e l'altra: il rilascio
quando riprendono il fuoco, la pressione ripetuta finché il tasto resta giù. Nessuna delle due
va inoltrata — la ripetizione la genera il compositore per conto suo.

Il conto va azzerato quando la connessione finisce, **anche se in quel momento non c'è più una
sessione a cui parlare**: è il difetto trovato in prova. A connessione finita il controllo è già
staccato, quindi trattando il rilascio come un evento qualsiasi lo si buttava e lo stato restava
sporco; alla connessione successiva il primo colpo su un tasto che risultava ancora premuto
veniva ingoiato, e la lettera non compariva.

#### Regola 5 — la tastiera virtuale va fatta esistere prima che serva

> ✅ **Sparita con libei, il 4 agosto 2026.** Non aggirata: sparita. Con i metodi `Notify*` Mutter
> creava i dispositivi virtuali **pigramente, al primo evento**, e il colpo a vuoto serviva a farli
> esistere prima che qualcuno scrivesse. Con libei i dispositivi li **annuncia il compositore**
> (`DEVICE_ADDED` → `DEVICE_RESUMED` → `ei_device_start_emulating`) e non si può spedire nulla prima:
> il difetto non ha più dove presentarsi. Misurato: sette lettere scritte nella panoramica di GNOME,
> **tutte e sette comparse**, prima inclusa.
>
> Il testo che segue descrive il difetto di allora, e resta perché la falsa pista che produceva —
> «la traccia dice che la lettera è stata inoltrata, quindi il difetto è del client» — è il genere
> di cosa che si riconosce solo se la si è già vista una volta.

Mutter crea i dispositivi virtuali **pigramente, al primo evento**
(`meta-remote-desktop-session.c`):

```c
if (pressed)
    ensure_virtual_device (session, CLUTTER_KEYBOARD_DEVICE);
```

Quando il dispositivo compare sul seat, Wayland deve annunciare ai client la
capacità tastiera e ricalcolare a chi spetta il fuoco. La battuta che ha
innescato tutto questo arriva prima che il fuoco sia stabilito, e va a vuoto.

Il sintomo per l'utente: **apre una finestra, scrive, e la prima lettera non
compare**; dalla seconda in poi tutto funziona. Il sintomo per chi indaga è
peggio, perché è una **falsa pista quasi perfetta**: la traccia del server mostra
che quella lettera è stata inoltrata a Mutter, quindi il difetto sembra stare nel
client o negli strumenti di prova. È stato attribuito a `xdotool` per mezza
giornata prima di essere riconosciuto.

Si manda quindi un colpo a vuoto appena la sessione parte, quando nessuno sta
ancora scrivendo: pressione e rilascio del codice evdev **0**, `KEY_RESERVED`,
che nessuna disposizione di tastiera associa a un simbolo. Non scrive nulla da
nessuna parte, ma fa esistere il dispositivo.

#### Regola 6 — la rotella arriva in due unità diverse a seconda del canale

RDP conta la rotella in unità da **120 per scatto**, positive verso l'alto; Mutter in passi da
**10**, positivi verso il basso. Ma il canale di input avanzato — un'estensione di FreeRDP, che i
suoi client preferiscono quando c'è — porta le stesse unità **moltiplicate per 0x10000**, per
poter descrivere anche le rotelle ad alta risoluzione.

Preso alla lettera, uno scatto vale 7 864 320: Mutter scarta il valore e la rotella non muove
nulla, senza dire perché. È il difetto che si è visto in prova.

I due assi inoltre non si comportano allo stesso modo: sul **verticale** RDP e Wayland contano in
verso opposto, sull'**orizzontale** concordano. Verificato su `gnome-remote-desktop` invece di
tirare a indovinare su quale dei due vada girato.

#### Cosa IronRDP 0.13 non consegna

La conversione da PDU a evento perde due cose sul percorso ordinario di RDP: il **bottone
centrale** e la **rotella orizzontale**, che finiscono entrambi nel ramo «movimento». Il primo si
traduce in uno spostamento verso una posizione dove il puntatore già si trova, quindi è
innocuo; la seconda può far comparire uno spostamento verso l'angolo, perché i client
riempiono di zeri le coordinate degli eventi di rotella.

Con i client di FreeRDP non si vede, perché entrambi passano dal canale di input avanzato, che li
consegna correttamente. Con mstsc sì. **Da sistemare a monte**, in IronRDP.

#### Cosa non si traduce, e perché si accetta

- **Il tasto Pausa**: sulla tastiera vera è l'unico col prefisso `0xE1`, e RDP lo segnala con un
  flag che IronRDP non consegna. Arriva come `0x1D`, cioè Ctrl sinistro: preme e rilascia un Ctrl
  a vuoto, che è innocuo.
- **Lo stato dei tasti a scatto**: non esiste un modo di *imporlo*, si può solo premere il tasto
  quando lo stato che crediamo non corrisponde a quello che il client dichiara. Il conto parte da
  «tutti spenti», che è vero perché la sessione grafica la avvia REMOTIX.

#### La disposizione della tastiera — sistemata il 3 agosto, a metà

Mandando posizioni fisiche, la lettera che ne esce la decide la disposizione configurata **dentro**
la sessione remota. Se il client ha una tastiera italiana e la sessione è americana i simboli non
corrispondono — e nel modo peggiore, perché le lettere sono giuste e sbagliano solo i segni di
interpunzione, cioè quelli che non si trovano a tentativi.

**Come si sistema oggi.** Si dichiara: `REMOTIX_TASTIERA=it` — o `it,us` per averne due, o
`it+nodeadkeys` per una variante — e REMOTIX la impone alla sessione a ogni connessione, scrivendo
`org.gnome.desktop.input-sources`. Se non è dichiarata **non si tocca nulla**: quella è una
preferenza dell'utente e vive nel suo dconf, e riscriverla di nostra iniziativa a ogni connessione
sarebbe un sopruso.

Misurato: partendo da una sessione americana e dichiarando `it`, la posizione AC10 — la prima a
destra della fila di mezzo — smette di produrre `;` e produce `ò`. È in `prova-e2e.sh`, ed è anche
il primo controllo automatico che **la tastiera scriva davvero**: la regola 2 di questo paragrafo,
finora affidata all'occhio.

**Perché si dichiara invece di concordarla.** Il client la dichiara, ma non a noi: il suo
identificatore di disposizione (KLID, es. `0x0410` per l'italiano) viaggia nel Client Core Data, e
`ironrdp-acceptor` lo conserva in `ConnectionResult.keyboard_layout` — con un commento che invita i
server a usarlo — ma `ironrdp-server` 0.13 **non lo consegna a nessun gancio**: non al display, non
all'handler di input, non a `ConnectionHandler`. Verificato sul sorgente, e 0.13 è l'ultima
pubblicata.

Manca quindi un contributo a monte, come per il bottone centrale del mouse (questione aperta n.6):
esporre il KLID all'applicazione. Con quello, la disposizione si sceglierebbe da sé — la
dichiarazione resterebbe come sovrascrittura, per chi ha una tastiera che il suo sistema
operativo descrive male. Fino ad allora resta la **questione aperta n.7**, ridotta a questo.

Il rimedio parziale che c'era prima resta e vale ancora: gli **eventi Unicode**, che alcuni client
mandano per i caratteri che la loro disposizione non colloca su nessun tasto.

#### Come si verifica

1. **Il puntatore va dove deve** — si muove il mouse e si confronta la coordinata che il registro
   annota (`puntatore x=… y=…`, a livello `debug`) con la posizione della finestra del client meno
   il bordo. Devono coincidere esattamente: è l'unico modo di distinguere un puntatore che sbaglia
   da un client che manda coordinate sue, perché il puntatore disegnato nell'immagine è l'esito di
   entrambe le cose insieme.
2. **La tastiera scrive** — si apre un terminale nella sessione, ci si clicca dentro e si scrive
   un comando che produca un risultato riconoscibile.
3. **La rotella scorre** — uno scatto dev'essere uno scatto: nel registro `asse dy=-10`.
4. **Niente resta premuto** — si tiene giù un modificatore, si uccide il client di netto, e nel
   registro dev'esserci `rilascio quel che era rimasto premuto`.
5. **Il ridimensionamento non rompe nulla** — dopo qualche cambio di misura, Mutter non deve avere
   più di una sessione di controllo viva.

**Attenzione alle prove automatiche**: `xdotool` perde di tanto in tanto la prima battuta di una
raffica mandata subito dopo un clic. Sembra un difetto del server e non lo è. Lo si è accertato
mettendo a confronto la traccia dei tasti col testo comparso: quando manca una lettera, quella
lettera non è mai arrivata.

**E il client consegna a volte la posizione PRECEDENTE del puntatore.** Misurato il 2 agosto: si
sposta il puntatore in tre punti distinti a tre secondi l'uno dall'altro, e ogni movimento fa
arrivare la coordinata del movimento prima; l'ultima non arriva finché non ce n'è un'altra.

Non è nostro, ed è la traccia dell'evento *in ingresso* a dirlo — quella aggiunta apposta in
`GestoreInput::mouse`, a livello `trace`: l'evento arriva da IronRDP **già vecchio**, e REMOTIX lo
inoltra a Mutter tre decimi di millisecondo dopo. Con un mouse mosso a mano non si nota, perché gli
eventi sono decine al secondo; con `xdotool`, che ne manda uno ogni tre secondi, falsa qualunque
misura costruita sull'assunto che l'ultima lettura sia l'ultimo movimento — la prima stesura della
prova annunciava uno spostamento di `-200x-150`, cioè l'esatto contrario di quello richiesto, con il
server che si stava comportando correttamente.

Da cui la regola per chi misura l'input: **si cerca la coppia di letture attesa, non la prima e
l'ultima**, e si manda un movimento di spurgo che faccia uscire quello tenuto indietro.

Il registro a livello `trace` annota **ogni tasto**: è a tutti gli effetti un registratore di
battitura, password comprese. Sta a `trace` e non a `debug` apposta.

---

### 5.9-bis La sessione intera parte senza monitor e senza GDM — accertato sul campo il 2 agosto

È il primo accertamento della fase 5, quello che condizionava gli altri due (§3.3-bis): **`gnome-session`
non pretende una sessione grafica di logind su un seat.** La sessione intera parte in una VM dove
`loginctl` conosce solo sessioni `tty` senza seat, e parte per intero.

Serve una cosa sola, ed è l'unica differenza rispetto a una sessione con schermo: la Shell va
avviata senza monitor, e la riga di comando dell'unità che la lancia non lo prevede. Si sovrascrive:

```ini
# ~/.config/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11
```

Poi `systemctl --user daemon-reload`, e la sessione si avvia con l'ambiente dichiarato **prima**:

```bash
export XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome
gnome-session --session=gnome
```

`XDG_SESSION_TYPE=wayland` **serve** e non è più la bugia di §5.6: l'unità della Shell porta
`ConditionEnvironment=XDG_SESSION_TYPE=wayland`, quindi senza quella variabile il compositore non
viene avviato affatto — la sessione parte monca e nessuno spiega perché. La differenza con il caso
punito in §5.6 è che lì la si dichiarava **al posto** di una sessione, qui **dentro** una sessione
che esiste davvero e che la esporta ai propri servizi.

**Cosa se ne ricava**, verificato subito dopo l'avvio: `org.gnome.SessionManager` risponde — quindi
«Esci» dal menu di sistema ora fa qualcosa; l'ambiente è completo e corretto senza doverlo
indovinare (`XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP`, `XDG_SESSION_CLASS=user`); i sedici
`gnome-settings-daemon` e i portali sono attivi. Sono esattamente le quattro voci che §9.4 elencava
come rimedi fatti a mano uno per volta.

**L'avvio è dentro REMOTIX dal 3 agosto** (`sessione.rs`). Alla connessione si accerta che ci sia
un compositore che risponde e, se manca, si avvia la sessione e la si aspetta. Serve in due
momenti, non uno: dopo un «Esci» — che ora funziona davvero, e prima lasciava l'utente con un
server in ascolto e nessun desktop — e al primo avvio della macchina, dove non c'è alcun gestore
di accesso grafico a farlo.

Due dettagli pagati subito:

- **la vitalità si accerta senza interpretare la risposta.** La prima stesura dichiarava il tipo
  di ritorno di `GetCurrentState`; la risposta non si deserializzava, e REMOTIX dava per morta una
  sessione che era partita benissimo. Ora si guarda solo che la risposta *arrivi*.
- **l'ambiente si compone da zero**, con `env_clear()` e una variabile per volta. È la lezione di
  `LC_ALL` messa nel codice invece che in una nota: chi avvia la sessione le regala tutto il
  proprio ambiente, quindi non gli si passa il proprio. La locale, in particolare, viene forzata a
  UTF-8 — se quella trovata non lo è si ripiega su `C.UTF-8`, perché con una locale non UTF-8 le
  applicazioni non si aprono.

#### Uscire dalla sessione deve chiudere la connessione

Avviarla non basta: bisogna anche accorgersi di **quando finisce**. Quando l'utente sceglie «Esci»
mentre è collegato, la cosa giusta è che il client venga disconnesso — come fa qualunque desktop
remoto — così per entrare nella sessione successiva bisogna riautenticarsi. Riavviarla sotto il
client, senza chiedere nulla, farebbe entrare nella sessione nuova chiunque avesse il client
aperto.

Ci sono voluti due passaggi, e il primo era un difetto che avevo appena introdotto io:

1. **Non confondere «desktop fermo» con «cattura finita».** Il palco unificava i due casi, perché
   su un desktop immobile Mutter non manda fotogrammi (§5.6) e la cosa sembrava innocua. Non lo
   era: uscendo dalla sessione il client restava attaccato a un'immagine congelata, senza che il
   registro dicesse nulla. Ora il palco distingue *niente per ora* da *finita*.
2. **Il canale però non si chiudeva lo stesso.** Il thread di PipeWire restava vivo anche a flusso
   `Unconnected`, quindi «finita» non arrivava mai. Ora il ciclo di cattura esce da sé quando il
   flusso passa a `Unconnected` **venendo da** `Paused` o `Streaming` — la condizione sul vecchio
   stato serve perché all'avvio si parte da `Unconnected`, e uscire lì sarebbe uscire prima di
   cominciare.

Misurato: il client cade entro tre secondi dall'uscita, e alla riconnessione nasce una sessione
nuova. Quattro controlli di `prova-e2e.sh` sorvegliano il ciclo intero.

**Cosa resta**: la sovrascrittura dell'unità della Shell è configurazione della macchina, sta in
`provision-vm.sh` e apparterrà al confezionamento della fase 12.

#### ⚠ Chi avvia la sessione le regala il proprio ambiente, tutto quanto

Costato la prima regressione grave della fase 5, segnalata dall'utente poche ore dopo: **le
applicazioni non si aprivano più**. Nessun errore in REMOTIX, desktop visibile e comandabile, ma
terminale e programmi non partivano.

La causa: `vm.sh` esporta `LC_ALL=C` per avere messaggi stabili; `ssh` di Debian spedisce `LANG` e
`LC_*` al server (`SendEnv`) e la VM li accetta (`AcceptEnv`). Ogni comando eseguito lì dentro
girava quindi con una locale **non UTF-8**. Finché di lì passava solo `gnome-shell` non si vedeva
nulla. Dal momento in cui si avvia una **sessione intera**, quell'ambiente viene esportato al
gestore systemd dell'utente e all'attivazione D-Bus — dove **sopravvive al compositore** — e ogni
applicazione lanciata dal desktop lo eredita. `gnome-terminal-server` si rifiuta di partire:

```
Non UTF-8 locale (ANSI_X3.4-1968) is not supported!     (uscita 8)
```

Il punto generale, che vale ben oltre questo caso: **una sessione eredita l'ambiente di chi la
avvia, comprese le variabili che non c'entrano nulla**, e da lì lo ridistribuisce a tutto ciò che
parte dopo. Vale oggi per la shell SSH; varrà domani per REMOTIX, che la sessione la avvierà lui e
che quindi dovrà **comporre l'ambiente in modo esplicito** invece di passare il proprio.

Il sintomo, ancora una volta, non diceva «manca una variabile»: diceva «le applicazioni non
partono». È §5.6 applicata alla lettera — l'ambiente si guarda **prima** del codice — ed è
esattamente ciò che l'utente ha suggerito di controllare mentre io stavo indagando altrove.

Pulizia: `systemctl --user unset-environment LC_ALL` e riavvio della sessione; la correzione
definitiva è in `vm.sh`, che ora invoca `ssh` con `env -u LC_ALL`.

**Verificato che non rompe nulla**: `prova-e2e.sh` passa venti controlli su venti contro la sessione
intera, cattura e input compresi.

---

### 5.9 Il server serve una connessione per volta, e le altre le fa aspettare

> ⚠ **Difetto specifico di `ironrdp-server` 0.13, superato dal vincolo del 3 agosto (§8-bis).**
> FreeRDP non ha questo problema: `gnome-remote-desktop` accetta con un `GSocketService`, cioè in
> parallelo. Restano valide le due conseguenze — i keepalive stretti e `TCP_USER_TIMEOUT`, più sotto —
> perché non dipendono dalla libreria ma dalla regola della sessione unica.

Accertato il 2 agosto, cercando perché il server «non sembrava attivo».

Il ciclo di accettazione di `ironrdp-server` 0.13 è **sequenziale**: accetta una
connessione e ne attende la fine (`run_connection(stream).await`) prima di
guardare la successiva. Chi arriva nel frattempo resta nella coda TCP, **senza
ricevere alcuna risposta**.

Il sintomo è ingannevole, perché tutto sembra a posto dal lato del server: il
processo è vivo, la porta è in ascolto, il registro non dice nulla. E dal lato
del client non c'è un rifiuto ma un silenzio, che dopo un po' diventa un errore
generico di rete.

La firma nel registro si riconosce dai tempi: le connessioni rimaste in coda
compaiono tutte **nello stesso millesimo di secondo in cui finisce quella che le
precedeva**, e falliscono subito con `accept_begin failed`, perché nel frattempo
il client ha rinunciato.

```
18:02:18.821  connessione conclusa peer=192.168.0.3   secondi=374
18:02:18.821  connessione conclusa peer=192.168.0.21  errore=accept_begin failed
18:02:18.821  connessione conclusa peer=192.168.0.21  errore=accept_begin failed
```

**In prova**: prima di dire che il server è giù, verificare che non ci sia già
qualcuno collegato — spesso è un proprio client dimenticato aperto.

**Deciso il 2 agosto dall'utente: si rifiuta.** Chi è dentro non viene disturbato.
Far aspettare in silenzio era la peggiore delle tre possibilità:

| | effetto |
|---|---|
| far aspettare *(fino alla fase 4)* | il secondo client resta muto e poi cade con un errore che non spiega nulla |
| **rifiutare** *(scelto)* | il secondo client cade subito; chi è dentro non viene disturbato |
| soppiantare | il secondo entra e il primo cade — comodo per riagganciarsi, ma chiunque si autentichi butta fuori chi sta lavorando |

### Il gancio che sembrava gratis non lo era

Qui sopra si era annotato che rifiutare fosse a costo zero, con
`ConnectionHandler::on_accept` che restituisce `false`. **È sbagliato, e per il
motivo che questa stessa sezione descrive**: quel gancio vive *dentro* il ciclo
sequenziale di IronRDP, quindi viene chiamato solo quando la connessione
precedente è già finita — cioè quando non c'è più nulla da rifiutare. Letto sul
codice di `ironrdp-server` 0.13 (`server.rs`, `run()`), non dedotto.

Il ciclo di accettazione è quindi passato a REMOTIX (`portiere.rs`). Due vincoli
lo hanno disegnato:

- il futuro di `run_connection` **non è `Send`** — dentro usa `Rc` — quindi non
  si può affidare a `tokio::spawn` e va eseguito sul compito che lo chiama;
- ma accettare e servire nello stesso ciclo riprodurrebbe il difetto di partenza.

Da cui la divisione: **accetta** un compito a parte, che maneggia solo socket ed
è `Send`; **serve** il compito principale, che non lo è. I due si parlano con un
canale, e un `compare_exchange` su un flag decide chi entra — non un «leggi, poi
scrivi», perché alcuni client aprono due connessioni nello stesso istante.

Misurato: il secondo client viene respinto in **meno di un decimo di secondo**, e
il primo non se ne accorge.

~~*Resta a debito*: il client dice «connessione chiusa», non «c'è già qualcuno».
RDP non ha un codice di rifiuto che significhi «occupato».~~

> ⚠ **Era sbagliato, e lo studio del protocollo del 3 agosto lo corregge**
> ([`protocollo-rdp.md`](protocollo-rdp.md) §17). Il codice c'è:
> **`ERRINFO_SERVER_DENIED_CONNECTION` (0x07)** dice esattamente «il server
> rifiuta», e per il caso opposto — quello in cui si sceglie di soppiantare —
> c'è `ERRINFO_DISCONNECTED_BY_OTHER_CONNECTION` (0x05). Si mandano con
> `freerdp_set_error_info()` prima di chiudere, e ogni client moderno li legge
> (dichiara `RNS_UD_CS_SUPPORT_ERRINFO_PDU`). L'affermazione nasceva dal fatto
> che IronRDP 0.13 non li esponeva: era un limite della libreria scambiato per
> un limite del protocollo.

### E siccome si rifiuta, bisogna accorgersi in fretta di chi se n'è andato

È la conseguenza che §3.4 prevedeva: con la sessione unica, un client sparito
senza salutare — caduta di rete, portatile chiuso — terrebbe la porta sbarrata
all'utente legittimo. I keepalive TCP predefiniti aspettano **due ore** prima
della prima sonda.

Ogni connessione nasce quindi con keepalive stretti — 10 secondi di attesa, sonda
ogni 5, tre tentativi: **venticinque secondi** — e con `TCP_NODELAY`, che toglie i
quaranta millisecondi che Nagle metterebbe fra un tasto e la sua eco.

#### Ma il keepalive da solo non basta — misurato il 3 agosto

Il keepalive era stato scritto e mai visto funzionare: la prova uccideva il
client, che chiudendosi chiude anche il socket, e il server lo sapeva subito.
**Non è lo stesso caso.** Fingendo per la prima volta una rete che sparisce —
i pacchetti verso la porta RDP buttati via dentro la VM — dopo **un minuto** il
server non se n'era ancora accorto, e il socket diceva:

```
Send-Q 669   timer:(on,27sec,8)   rto:52224  backoff:8  unacked:1
```

Cioè: **timer di ritrasmissione all'ottavo raddoppio**, con cinquantadue secondi
fino al tentativo successivo. Il keepalive non era nemmeno partito, e faceva
bene: si applica solo a un socket **inattivo**, ed è fatto per scoprire chi se
n'è andato mentre non si aveva niente da dirgli. Se invece ci sono dati non
riscontrati — e un server RDP ne ha quasi sempre — comanda l'RTO, che con i
valori predefiniti (`tcp_retries2` = 15) insiste per **un quarto d'ora**.

Con la sessione unica, un quarto d'ora chiusi fuori dalla propria sessione.

Il rimedio è **`TCP_USER_TIMEOUT`**, che pone un tetto assoluto al tempo in cui i
dati possono restare non riscontrati: passato quello, il kernel chiude. Impostato
a **30 secondi**, un po' più largo dei 25 del keepalive perché qui si conta anche
il tempo che serve ad accorgersi di dover cominciare a preoccuparsi.

Misurato dopo la correzione: caduta scoperta in **27 secondi** in una prova e
**45** in un'altra — la differenza sta in quando il server ha di nuovo qualcosa
da scrivere, perché è da lì che parte il conto. In entrambi i casi la porta si
libera e chi torna rientra nella propria sessione, con le finestre dov'erano.

### E l'altra metà: accorgersi che l'utente è uscito

*Scoperto e corretto il 3 agosto, segnalato dall'utente su Android.*

Il sintomo, con le sue parole: **«la connessione sembra restare viva»**. Non era
un'impressione, ed è istruttivo *perché* non lo era.

Fino a quel momento REMOTIX veniva a sapere di un «Esci» **per ultimo**: se ne
accorgeva quando moriva il flusso di cattura, cioè quando GNOME aveva già finito
di smontare tutto. Misurato dal telefono, con le applicazioni aperte:

| | |
|---|---|
| 13:09:45.842 | l'utente tocca **Log Out** |
| 13:09:45.923 | ultimo fotogramma spedito |
| | *5,1 secondi in cui non si spedisce più niente* |
| 13:09:51.017 | la cattura si ferma: **qui** ce ne accorgevamo |
| 13:09:51.172 | socket chiuso |

E il fotogramma rimasto sullo schermo del telefono era **uno sfondo pulito senza
finestre** — cioè visivamente identico a un desktop vivo e vuoto. Il client non
aveva alcun motivo di sospettare che la sessione fosse finita, perché nessuno
glielo aveva detto e l'immagine diceva il contrario.

**Il flusso non c'entrava.** Registrato con `REMOTIX_DUMP_H264` e decodificato:
53 fotogrammi, nessun errore, l'ultimo integro. La prima ipotesi — «continuiamo
per secondi a trasmettere un desktop in demolizione» — era falsa, e lo si è
saputo guardando i byte invece di ragionarci.

#### Perché non basta chiudere

Chiudere lo si faceva già. IronRDP 0.13, quando il flusso di aggiornamenti
finisce, arriva a `RunState::Disconnect`, che restituisce il socket e **non manda
niente**: né codice d'errore né congedo. Tutte le strade portano lì —
`next_update → None`, `ServerEvent::Quit(motivo)`, la fine del ciclo — e il
`motivo` di `Quit` finisce solo in una riga di registro. Il `ServerSetErrorInfoPdu`
esiste nel crate, e `LogoffByUser = 0x0C` pure, ma è privato e cablato sul
rifiuto delle credenziali.

Quindi il client riceve solo una chiusura di socket, e ognuno ne fa quel che
vuole: **xfreerdp esce, il client Android resta lì**. Da cui la lezione sulla
prova automatica, di cui sotto.

#### La correzione: sapere presto, e troncare di netto

Decisa dall'utente il 3 agosto, contro tre proposte più raffinate e peggiori:
*intercettare l'uscita e uccidere subito la connessione, prima la connessione e
poi la sessione.* Il ragionamento che la regge, che è suo: **il client darà un
errore, ma l'utente sa perché — è stato lui a scegliere di sloggarsi.** Un errore
che arriva quando te lo aspetti non è un guasto, è una conferma.

*Sapere presto* si ottiene registrandosi con `gnome-session` come fa qualunque
applicazione (`RegisterClient`, in `uscita.rs`). Misurato:

| | |
|---|---|
| logout richiesto | |
| `QueryEndSession` | +9 ms — la **domanda**: qualcuno si oppone? |
| `EndSession` | +16 ms — la **decisione**: si esce |
| `Stop` | +20 ms |
| morte del flusso di cattura | +324 ms *(qui ce ne accorgevamo prima)* |

Ci si aggancia a **`EndSession`**, non a `QueryEndSession`: la seconda è una
domanda a cui un inibitore può ancora rispondere di no, e in quel caso GNOME
annulla l'uscita — chi si aggancia alla domanda butta fuori l'utente per un
logout che poi non avviene.

*Troncare di netto* è `SO_LINGER` a zero, cioè un **RST** invece della chiusura
educata: l'unica cosa che nessun client può ignorare. Serve una maniglia sul
socket che sopravviva alla consegna a IronRDP, che se lo prende per valore;
`SO_LINGER` sta sul socket e non sul descrittore, quindi impostarlo dalla maniglia
vale anche per il descrittore altrui, e il RST parte alla chiusura dell'**ultimo**
descrittore.

Misurato dopo: la connessione cade **24 ms** dopo l'uscita, contro i 372 del caso
sintetico e i 5,1 secondi del caso vero.

#### La regola dell'ostaggio

**Un client registrato che non riscontra i segnali blocca l'uscita dell'utente.**
`gnome-session` aspetta lui, la sessione resta in piedi, e sullo schermo non c'è
niente che lo spieghi.

Non è un timore: è successo in prova, con una spia che rispondeva alla domanda ma
non alla decisione. La sessione è rimasta in ostaggio finché la spia non è
scaduta, mezzo minuto dopo.

Da cui la regola, scritta in `uscita.rs`: **si risponde sempre, e si risponde per
primo**, da un percorso che non può fermarsi ad aspettare nient'altro. Avvisare
chi serve la connessione viene dopo.

#### Il congedo dichiarato resta a debito

> ✅ **Debito pagato il 4 agosto 2026, con la fase 5** — e con una sorpresa che vale più del debito
> stesso. Misurato: il client cade **0,01 s** dopo l'annuncio dell'uscita, contro i 5,1 secondi di
> prima, e riceve `ERRINFO_LOGOFF_BY_USER`. Il `SO_LINGER` a zero non serve: non c'è bisogno di un
> RST se si può dire *perché*.
>
> **La sorpresa**: con FreeRDP servono **due** chiamate. `freerdp_set_error_info` registra il
> codice; a spedirlo è `freerdp_send_error_info`, che è una funzione a parte. Averne chiamata una
> sola ha prodotto per tre fasi esattamente il difetto descritto qui sopra — il client che riceve
> solo una chiusura di socket — senza che nessuna prova se ne accorgesse, perché nessuna guardava
> **dal lato del client**. Vedi R12 di `REFERENCE.md`.

`LogoffByUser` direbbe al client *perché* è finita, invece di lasciargli un errore
di rete. Non si può spedire dall'API pubblica di IronRDP 0.13: è il **terzo
contributo a monte**, accanto al bottone centrale del mouse (n.6) e al KLID (n.7).
Finché non c'è, meglio un errore onesto e immediato di un'immagine che mente.

#### E la lezione sulla prova automatica

La sezione «Logout» di `prova-e2e.sh` era **verde per tutto il tempo in cui il
difetto c'era**. Verificava che il processo `xfreerdp3` morisse — e moriva, perché
xfreerdp alla chiusura del socket esce da solo. Cioè: **collaudava l'unico dei tre
client che tollerava la nostra omissione.**

È la regola dei tre client (§5.7) in una forma nuova e più insidiosa: non basta
che una prova esista e sia verde, deve provare **sul client che il difetto lo
mostra**. La prova ora misura a decimi di secondo e boccia una caduta oltre i due
secondi, perché «cade prima o poi» era esattamente il difetto.

> La prova sta in `prova-e2e.sh` e va fatta **dentro la VM**, con `nft`:
> bloccare dal notebook non servirebbe, perché la connessione TCP che conta è
> quella fra QEMU e il server, e resterebbe viva.

### 5.10 La sessione locale vince — accertato sul campo il 3 agosto

L'altra metà di §3.4, quella che restava: se l'utente ha già una sessione grafica
**locale** non si entra, e se ne apre una mentre l'RDP è in corso l'RDP cade. Le
nove combinazioni possibili, con chi garantisce ciascuna e i tempi misurati,
stanno nella tabella di §3.4; qui c'è il come.

Il perché è concreto e già pagato altrove: due sessioni grafiche dello stesso
utente condividono `$XDG_RUNTIME_DIR`, il gestore systemd dell'utente, il bus di
sessione, l'agente delle chiavi e i portali — cioè tutto ciò che nella fase 5 si
è faticato a far funzionare **una volta sola**. Il guasto che ne segue non si
presenta come «due sessioni»: si presenta come applicazioni che non partono.

**Cosa conta come grafica locale.** Quattro condizioni insieme, lette da
`systemd-logind`, più una negativa:

| proprietà | valore | perché |
|---|---|---|
| `User` | il nostro uid | le sessioni altrui non ci riguardano |
| `Seat` | non vuoto | un seat è hardware vero: schermo e tastiera attaccati |
| `Type` | `wayland`, `x11`, `mir` | `tty` è testuale e **deve** poter convivere |
| `Class` | `user` | esclude `greeter`, `lock-screen`, `manager`, `background` |
| `Remote` | falso | una sessione X11 inoltrata da lontano non è qualcuno davanti alla macchina |

Le sessioni testuali convivono liberamente, ed è essenziale: REMOTIX stesso gira
dentro una sessione SSH, e con la regola scritta male («esiste una sessione
dell'utente, quindi rifiuto») non si collegherebbe nessuno, mai.

**Misurato**: nella VM la sessione SSH in cui gira REMOTIX **e la sessione GNOME
che REMOTIX avvia** sono una sola — `Type=tty`, senza seat. `gnome-session` non
ne crea una propria, perché resta nel cgroup di chi lo ha avviato. La sessione
remota quindi non si conta da sola; per prudenza la si esclude comunque per
identificatore, perché il giorno in cui si contasse il sintomo sarebbe «rifiuta
sempre tutti» e non farebbe sospettare la causa.

**Non basta chiedere alla connessione**, e §3.4 lo diceva: ci si sottoscrive a
`SessionNew`/`SessionRemoved` di logind. Ma **il segnale da solo non basta**: il
`Type` di una sessione cambia *dopo* la nascita — chi la registra la promuove a
grafica in un secondo momento — quindi un `SessionNew` letto troppo presto la
mostra ancora testuale. Serve anche un ripasso periodico, ogni due secondi: una
manciata di chiamate D-Bus al minuto, e nessuna finestra cieca.

Chi interroga non fa I/O: la `Sentinella` tiene lo stato aggiornato da parte, e
il portiere legge un valore già pronto. Interrogare D-Bus al momento
dell'accettazione significherebbe far aspettare ogni client per una risposta che
quasi sempre è «no».

**Come cade l'RDP.** Si abbandona il futuro che serve la connessione, dentro una
`select!`; con lui cade il socket. IronRDP non ha un modo per dire «chiudi
adesso» dall'esterno, e non serve averlo.

**E la sessione grafica remota si chiude, non si stacca soltanto.** Deciso
dall'utente il 3 agosto, dopo la domanda giusta: *siamo davvero a posto sul
fatto che lo stesso utente non possa avere due sessioni grafiche?* Non lo
eravamo. Staccare il client lascia in piedi il compositore remoto, e chi si
siede davanti alla macchina si ritrova **due sessioni grafiche a proprio nome**
sullo stesso `$XDG_RUNTIME_DIR`: la sua — la seconda — troverebbe occupato il
nome D-Bus `org.gnome.Shell`. Il difetto si vedrebbe dove nessuno lo cerca,
sulla sessione *locale* che non parte.

Chiude un compito a sé (`sgombera` in `main.rs`), non il portiere, perché il
caso più frequente è proprio quello in cui **non c'è nessuna connessione da
chiudere**: l'utente si siede davanti alla macchina quando da remoto non c'è
nessuno, e la sessione remota è lì che aspetta. Il compito:

1. chiede l'uscita ordinata, `Logout(1)`: le applicazioni ricevono l'avviso e
   possono salvare;
2. se dopo dieci secondi la sessione è ancora lì — un programma con modifiche
   non salvate ha il diritto di *inibire* l'uscita — passa a `Logout(2)`, che
   non accetta obiezioni, **dichiarandolo nel registro**: è una perdita
   possibile di lavoro non salvato, e chi legge deve poterla ricostruire;
3. **smonta il palco**. Non è un dettaglio: cattura e monitor virtuale sono
   oggetti di un compositore che non esiste più, e chi si ricollegasse alla
   stessa misura li troverebbe «già montati» — schermo nero;
4. aspetta che la sessione locale finisca prima di riarmarsi, altrimenti
   richiuderebbe una sessione per volta all'infinito.

Misurato: compositore remoto chiuso in **tre secondi**, palco smontato, e al
ritorno la sessione viene rifatta da capo.

**Se logind non c'è** si prosegue *senza* la regola, dichiarandolo nel registro.
L'alternativa — rifiutare tutti — trasformerebbe un bus non raggiungibile in un
server inaccessibile senza spiegazione; e chi non ha logind non ha nemmeno il
modo di aprire la sessione locale che si sta temendo.

Misurato: rifiuto in **95 ms**, caduta dell'RDP in **2 secondi**, rientro appena
la sessione locale finisce.

#### Come si prova, visto che nella VM non c'è nessuno seduto davanti

Con `finta-sessione-locale`, che non simula nulla: apre una sessione PAM
dichiarando `XDG_SESSION_TYPE=wayland`, `XDG_SEAT=seat0`, `XDG_VTNR`, e logind la
registra come tutte le altre. Serve `root`, e il servizio PAM di prova lo
riconosce con `pam_rootok` — non con `pam_permit`, che lascerebbe sulla macchina
un file che autentica chiunque.

> **⚠ Va avviato fuori da ogni sessione, o non fa niente — in silenzio.**
> Mezz'ora persa il 3 agosto: lanciato da una shell SSH, `pam_unix` apriva la
> sessione e `pam_systemd` non registrava nulla, senza un errore da nessuna
> parte. Il motivo è che **`pam_systemd` non crea una sessione dentro un'altra
> sessione**: vede il chiamante in `session-NNN.scope` e si ferma. Il rimedio è
> avviarlo come unità transitoria, che nasce in `system.slice`:
>
> ```bash
> sudo systemd-run --collect --quiet --unit=remotix-finta-locale \
>      /home/nicfio/finta-sessione-locale nicfio
> sudo systemctl stop remotix-finta-locale     # e la sessione si chiude
> ```

---

## 6. Ambienti

### 6.1 Sviluppo

Il server `192.168.0.2` (host `NIC-OS`), dentro un contenitore Debian Trixie su
`/media/REMOTIX`.

- Hardware: i5-13500T (20 thread), 31 GB di RAM, Radeon RX 6800 e grafica integrata Intel
- Il sistema è **live in RAM** e si azzera a ogni riavvio; solo `/media` (NVMe da 1,8 TB) è
  persistente
- Provisioning con `/media/REMOTIX/provision.sh`, **idempotente**, da rilanciare dopo ogni
  riavvio
- **Vincolo: niente deve finire fuori da `/media/REMOTIX`.** Lo script non installa nulla nel
  sistema host. La garanzia è anche strutturale, dato che `/` vive in RAM
- **Vincolo: non toccare i dischi.** Nessun partizionamento, formattazione o montaggio di
  dispositivi a blocchi senza istruzioni esplicite
- Ingresso nel contenitore: `bash /media/REMOTIX/enter.sh`

**⚠ I `--rbind` del contenitore vanno resi `slave`.** Costato il 3 agosto: `provision.sh` ed
`enter.sh` montavano `/dev` e `/sys` nel contenitore con `mount --rbind`, e la funzione di pulizia
faceva `umount -R`. Con la propagazione condivisa — quella predefinita — **lo smontaggio torna
indietro e smonta `/dev/pts` del server**. Il kernel non può più allocare pseudo-terminali e
nessuno riesce più ad aprire una sessione SSH interattiva:

```
PTY allocation request failed on channel 0
```

Il guasto è insidioso per due motivi: l'autenticazione continua a funzionare — si entra, ma senza
terminale — e **tutti gli script del progetto continuano a funzionare**, perché usano comandi non
interattivi che il PTY non lo chiedono. Il server è rimasto così per ore e se n'è accorto solo
l'utente, provando a collegarsi a mano.

Corretto aggiungendo `mount --make-rslave` dopo ogni `--rbind`, in `provision.sh` e nell'`enter.sh`
che esso genera. Rimedio se ricapita:

```bash
sudo mount -t devpts devpts /dev/pts -o gid=5,mode=620,ptmxmode=000
```

**Stato: pronto e verificato.** Rust 1.97.1, gcc 14.2, clang 19.1, Wayland 1.23.1, libva 1.22,
libdrm 2.4.124, PipeWire 1.4.2, Vulkan 1.4.309, PAM, OpenSSL 3.5.6. Entrambe le GPU visibili.

### 6.2 Runtime

> ## ⛔ Dal 6 agosto 2026 la macchina di runtime è **il server stesso, sul ferro nudo**
>
> *Deciso dall'utente, con questa motivazione: «le prove che riguardano l'hardware devono essere
> fatte su HW nativo, senza avere di mezzo tutta l'infrastruttura dell'hypervisor». E subito dopo:
> «usiamo il server nativamente, non tramite un container: basta installare GNOME sul server».*
>
> **Che cosa cade.** Il vincolo «macchina di sviluppo e macchina di runtime assolutamente distinte»
> qui sopra, e il vincolo di §6.1 «niente deve finire fuori da `/media/REMOTIX`»: `provision-server.sh`
> installa GNOME nel sistema dell'host. Non è una svista, è il prezzo del ferro nudo.
>
> Della vecchia divisione resta la metà che serve ancora: **il codice si compila sempre nel
> contenitore** (`enter.sh`) e sul server ci gira soltanto. Il binario si porta con
> `server.sh copia`, che è il gemello di `vm.sh copia`.
>
> **Che cosa si guadagna**, ed è il motivo di tutto: cadono in un colpo **tutti e quattro** i
> falsanti di §8.6-bis di `REFERENCE.md`.
>
> | quel che la VM falsava | sul ferro |
> |---|---|
> | niente 3D: `virtio-gpu` senza virgl | la iGPU Intel vera |
> | rete **SLIRP** in spazio utente | la rete del server |
> | quattro vCPU | venti thread |
> | dalla fase 9: **Mutter disegna su una scheda passata con VFIO** | Mutter disegna sulla scheda |
>
> L'ultima riga è quella che ha forzato la decisione: il passthrough era arrivato il 6 agosto ed era
> l'unica cosa nuova rispetto alle fasi 2-8, quindi l'unica che non si potesse escludere ragionando.
>
> **Il rootfs del server vive in RAM e si azzera a ogni riavvio**, quindi `provision-server.sh` va
> rieseguito dopo ogni riavvio. Non è un difetto — *«ripartire con un server pulito quando serve
> risolve parecchi problemi»* — e costa poco perché la cache dei `.deb` sta su `/media`.
>
> **Tre cose trovate installando**, che nella VM non si vedevano perché cloud-init le faceva da sé:
> mancava `libavfilter10`; l'utente non era nel gruppo **`render`**, e senza quello `vainfo` risponde
> *«Failed to open the given device!»*, che sembra una scheda assente ed è un permesso; e sul server
> ci sono **due schede DRM** (Intel e Radeon), mentre nella VM ne avevamo lasciata una sola apposta
> perché il DMA-BUF funzionasse (§7.3 di `REFERENCE.md`).
>
> ⚠ **Una sessione remota che spegne questa macchina spegne il server**, e con il rootfs in RAM si
> porta via anche tutto quel che `provision-server.sh` ha installato. Le protezioni di §3.4-bis —
> `sleep.conf` e polkit — qui non sono prudenza, sono necessarie.

> ## ⛔ E dal 7 agosto 2026 la VM esce di scena: **una macchina sola, sviluppo e prova**
>
> *Deciso dall'utente chiudendo GNOME: «adesso il server diventa sia macchina da sviluppo sia di
> test, così non litighiamo con le VM e le schede grafiche».*
>
> Il vincolo originario — sviluppo e runtime **assolutamente distinti** — era stato posto quando la
> prova girava dentro una macchina virtuale. Con il passaggio al ferro nudo quella separazione era
> già ridotta a metà (si compila nel contenitore, si esegue sull'host); adesso cade anche il resto,
> e con lei tutta la manutenzione del passthrough della GPU, dei nodi DRM doppi e della rete in
> spazio utente. **Quel che si perde è l'isolamento; quel che si guadagna è che ogni misura riguarda
> hardware vero**, che è il motivo per cui il trasloco era stato fatto.
>
> Ne discende che le misure delle fasi 2-9 prese nella VM **non hanno più una macchina su cui essere
> ripetute**. Non è una perdita grave: quelle che contano sono state rifatte sul ferro (la fase 9 il
> 6 agosto, e tutta la campagna sui compositori il 7 — `REFERENCE.md` **R32**).
>
> ### Che cosa un riavvio si porta via, e come si rimette
>
> Il rootfs vive in RAM e si azzera; **`/media` resta**. È una proprietà voluta — *«ripartire con un
> server pulito quando serve risolve parecchi problemi»* — a patto di sapere che cosa rieseguire:
>
> | Passo | Che cosa rimette |
> |---|---|
> | `bash /media/REMOTIX/provision-server.sh` | GNOME, i gruppi `video`/`render`, l'unità della Shell senza monitor, la regola `sudo` ristretta, `/etc/default/remotix` |
> | `bash /media/REMOTIX/server.sh copia` | il binario in `~`, che sta nel rootfs e sparisce (il **build** invece è su `/media` e resta) |
> | `bash /media/REMOTIX/tmp/banco-compositori/provision-banco.sh` | **il banco dei compositori**: scene, client di prova, KWin, sway, labwc, e i suoi quattro programmi ricompilati |
>
> ⚠ **Quel che NON va rimesso a mano, ed è la ragione per cui ci sta bene un riavvio**: la cadenza a
> 60 fotogrammi. Dal 7 agosto sta in `main.c`, non in `/etc/default/remotix` — proprio perché quel
> file vive in RAM e una volta si era già portato via una riga di guardia (`REFERENCE.md` R29).

**Quel che c'era prima, e resta agli atti perché le misure delle fasi 2-9 sono state prese lì.**

Una **macchina virtuale** sullo stesso server.

Vincolo dell'utente: macchina di sviluppo e macchina di runtime devono essere **assolutamente
distinte**. La VM è **effimera e senza nulla di preinstallato**, quindi serve un secondo script
`provision-vm.sh`, anch'esso idempotente.

Configurazione: 4 core, 8 GB di RAM, Debian Trixie minimale, un utente con privilegi di
amministratore, scheda video **virtio-gpu**.

~~**Nessun passthrough della GPU per ora.**~~ Fatto il 6 agosto 2026 con VFIO, e superato lo stesso
giorno dal passaggio al ferro nudo. Serve solo dalla fase 9 del piano; le fasi precedenti
girano con la scheda virtuale. L'orientamento era verso la **grafica integrata
Intel**: la Radeon RX 6800 ha già dato problemi su questa macchina, come testimoniano i
parametri di avvio del kernel che disattivano tutta la gestione energetica del driver AMD
(`amdgpu.runpm=0 amdgpu.aspm=0 amdgpu.bapm=0 pcie_aspm=off`), rimedio classico contro i blocchi.

---

## 7. Modo di lavorare

L'utente **non è uno sviluppatore**: decide le funzionalità, il codice lo scrive Claude.
Il collaudo avviene **vedendo il software funzionare**, non leggendo il codice. Ne consegue che
il progetto va costruito a **tappe piccole e dimostrabili**, ognuna delle quali produce
qualcosa di eseguibile e giudicabile a occhio.

### 7.0 ⛔ Regola vincolante: prima si legge `REFERENCE.md`

*Posta dall'utente il 3 agosto 2026.*

**Non si scrive una sola riga di codice senza aver prima consultato
[`REFERENCE.md`](REFERENCE.md).** Vale per ogni area del progetto e per ogni modifica, non solo per il
primo abbozzo.

La ragione è nella natura dei guasti che quel documento raccoglie: **non si manifestano come errori.**
Si manifestano come schermo nero, disconnessione improvvisa o immagine sbagliata, su **un client su
tre** — e di norma proprio su quello che non si sta usando per provare. Scrivere prima e verificare
dopo significa scoprire il difetto nel momento più costoso, e con la traccia più fredda.

Il conto già pagato per non averlo fatto, tutto registrato in §5: due giorni per un
`MapSurfaceToOutput` mancante; mezza giornata attribuita a `xdotool` per un difetto nostro; una prova
automatica rimasta verde per tutto il tempo in cui il difetto c'era, perché collaudava l'unico client
che tollerava l'omissione.

**Corollario**: quando una misura nuova contraddice `REFERENCE.md`, si aggiorna il documento **nello
stesso momento**, con data e fonte. Un riferimento che invecchia in silenzio è peggio di nessun
riferimento.

### 7.1 Il lavoro in team con DeepSeek

Lo sviluppo è **in team**: oltre a Claude è disponibile **DeepSeek**, raggiungibile via API.

**Configurazione accertata**

| | |
|---|---|
| Endpoint | `https://api.deepseek.com` |
| Modelli disponibili | `deepseek-v4-pro`, `deepseek-v4-flash` |
| Chiave API | `~/DEEPSEEK.key` **sul notebook**, non sul server |

Il fatto che la chiave stia sul notebook e non sul server ha una conseguenza pratica: le
chiamate partono dal notebook. Se in futuro servisse invocarlo da uno script sul server, la
chiave andrà resa disponibile lì, e sarà una decisione dell'utente.

**Il limite strutturale da tenere presente**

DeepSeek **non ha accesso al server, né ai file, né all'ambiente**. È un modello che risponde a
richieste via rete. Tutto ciò che deve vedere gli va incollato nella richiesta, e tutto ciò che
produce va integrato e verificato da Claude. Non è un collaboratore autonomo: è un consulente
al quale si sottopone materiale.

**I tre ruoli possibili**, in ordine di resa attesa:

1. **Revisore indipendente** *(raccomandato)*. Gli si sottopone il codice scritto chiedendogli
   di trovarvi difetti. È il ruolo dove un secondo modello rende di più, perché non condivide i
   punti ciechi del primo.
2. **Consulente di progettazione.** Gli si pongono le decisioni architetturali difficili e si
   confronta la sua risposta. Utile nei punti di incertezza.
3. **Implementatore di moduli isolati.** Gli si affida un componente autosufficiente con una
   specifica precisa. Funziona solo per parti che non richiedono di conoscere il resto del
   sistema.

**Regola vincolante sui dati.** Tutto ciò che viene inviato esce dalla macchina dell'utente e
raggiunge i server di DeepSeek. Per il codice di questo progetto è verosimilmente irrilevante,
ma **credenziali e chiavi non entrano mai in quelle richieste**: né la password del server, né
la chiave API stessa, né il contenuto di `SERVER.ssh`.

---

## 8. Sintesi delle decisioni prese

| Tema | Decisione |
|---|---|
| Linguaggio | **C** — vincolo dell'utente, 3 agosto 2026 (§8-bis) |
| Stack RDP | **FreeRDP 3** — vincolo dell'utente, 3 agosto 2026 (§8-bis) |
| Sicurezza del trasporto | **Solo TLS** 1.2 e 1.3 |
| Soglia client | **Solo EGFX**, nessun fallback legacy |
| Percorso di rendering | Pipeline EGFX con **due codec**: H.264 AVC420 dove c'è, **RemoteFX Progressive** dove manca — deciso il 3 agosto dopo la misura su RDM (§3.1) |
| Qualità video | 4K su 10 Mbps è **obiettivo, non vincolo**; 2K a 30 fps è risultato altrettanto buono |
| Astrazione di codifica | **ffmpeg / `libavcodec`**, codificatore scelto per nome a runtime |
| Accelerazione hardware | **Fuori dal percorso critico**: si parte in software con x264 |
| Multi-monitor | **Fuori** — monitor singolo, ma implementazione parametrica su N |
| Aggancio al desktop | Nessun compositor proprio; **interfacce dirette dei compositor** |
| Iniezione dell'input | **libei**, deciso il 4 agosto chiudendo la fase 3 — vedi §5.8. La sessione di controllo resta `org.gnome.Mutter.RemoteDesktop`, ma gli eventi passano da `ConnectToEIS` |
| Ordine dei desktop | GNOME → KDE → XFCE → LXQt → Cinnamon |
| Desktop X11 | **Fuori** (le applicazioni X11 restano supportate via XWayland) |
| Autenticazione | **PAM** locale — servizio `remotix`, fatto in fase 5 |
| Regole di sessione | Una sola sessione grafica per utente; la locale vince sull'RDP; **seconda connessione RDP rifiutata subito** (fatto), con keepalive stretti perché il rifiuto non chiuda fuori chi ha perso la rete |
| Spegnimento, riavvio, sospensione | **Tolti alla sessione remota**: `sleep.conf` per la sospensione, polkit per le altre due |
| Portabilità | Rilevamento delle capacità e degradazione graduale; **Debian e Ubuntu** come riferimento |
| Redirezione dischi | **Fuori** |

---

## 8-bis. I due vincoli del 3 agosto: C e FreeRDP 3

*Posti dall'utente il 3 agosto 2026, al riavvio del progetto.*

**Si scrive in C. Si usa FreeRDP 3.** Non sono preferenze da bilanciare con altro: sono vincoli, e il
resto della specifica si adatta a loro.

La conseguenza più grande non è il linguaggio in sé: è che **`gnome-remote-desktop` smette di essere un
riferimento da cui trarre ispirazione e diventa un riferimento da cui trarre codice**. Stesso
linguaggio, stessa libreria RDP, stesso compositore, stessi client. Ogni riga di
[`gnome-remote-desktop.md`](gnome-remote-desktop.md) che descrive una soluzione è ora una soluzione
*trasferibile*, non un'analogia.

### Che cosa decade

Tutto ciò che la specifica dava per acquisito su IronRDP va riletto. Non lo si cancella — le
misure restano vere e il modo in cui sono state ottenute vale ancora — ma le conclusioni operative
cambiano:

| Dove | Che cosa decade |
|---|---|
| **§5.4** | L'intera vicenda «IronRDP non rende su mstsc» resta valida come *diagnosi* (la causa era nostra: mancava `MapSurfaceToOutput`), ma la scelta di libreria che ne discendeva non è più in discussione |
| **§5.9** | Il ciclo di accettazione sequenziale è un difetto **di `ironrdp-server`**. FreeRDP non ce l'ha: `gnome-remote-desktop` accetta con un `GSocketService`, in parallelo per costruzione. `portiere.rs` non serve più |
| **§5.9** | Il «congedo dichiarato a debito» non è più un debito: FreeRDP espone `freerdp_set_error_info`, e il riferimento lo usa (`ERRINFO_RPC_INITIATED_DISCONNECT`) |
| **§5.8, questione n.6** | Bottone centrale e rotella orizzontale non consegnati: era un limite di IronRDP 0.13 |
| **§5.8, questione n.7** | Il KLID non esposto: era un limite di IronRDP 0.13. FreeRDP lo tiene in `rdpSettings` e lo consegna al server |
| **§5.8, §5.7** | Le regole sul «non aspettare dentro il ciclo asincrono» restano vere, ma cambiano forma: non più task Tokio e `Send`, ma thread e `GMainContext` |

I **tre contributi a monte** che la specifica metteva in conto a IronRDP (bottone centrale, KLID,
`LogoffByUser`) **spariscono tutti e tre**.

### Che cosa resta intatto

Tutto ciò che riguarda **Mutter, PipeWire, logind e il protocollo RDP**, cioè la maggior parte di §5:
la sequenza obbligata di §5.8 regola 1, le regole di cattura di §5.6, l'allineamento e le geometrie di
§5.4, la tabella delle nove combinazioni di §3.4, il ciclo di uscita di §5.9-bis, le misure di §5.10.
Quelle non parlavano di IronRDP: parlavano del sistema.

### Che cosa va deciso ancora

- **Se scrivere il server RDP contro l'API `freerdp_peer` a mano, o partire da una copia adattata di
  `gnome-remote-desktop`.** Sono due progetti diversi: il primo è più lungo e più nostro, il secondo è
  più corto e porta con sé scelte che REMOTIX ha rifiutato (NLA obbligatorio, seconda connessione che
  soppianta, nessun controllo del bitrate). Da decidere prima di scrivere la prima riga.
- **Se l'input passa a libei**, ora che il riferimento è trasferibile: risolverebbe la questione n.7
  leggendo la disposizione di tastiera dalla sessione invece di dichiararla. Vedi
  `gnome-remote-desktop.md` §13.1.
- **Il sistema di compilazione** (meson, come il riferimento) e le convenzioni di codice.

---

## 9. Questioni aperte

1. **Input touch** (MS-RDPEI): emulazione del mouse o multitouch nativo. Rilevante avendo
   Android tra i client.
2. **Ruolo di DeepSeek**: revisore indipendente, consulente di progettazione o implementatore
   di moduli isolati. Raccomandazione: revisore.
3. **Passthrough della GPU**: rimandato alla fase 9, orientamento verso l'integrata Intel
   (vedi §6.2).
4. ~~**Avviamo il compositore, non una sessione.**~~ **Deciso il 2 agosto: REMOTIX
   avvierà una sessione intera.** ~~Resta aperto il *come*~~ — **accertato sul campo
   la sera stessa: vedi §5.9-bis.** `gnome-session` non pretende una sessione
   grafica di logind su un seat; basta avviare la Shell senza monitor
   sovrascrivendo l'`ExecStart` della sua unità, e le quattro voci qui sotto si
   risolvono tutte insieme. Resta da portare l'avvio dentro REMOTIX. Il
   materiale raccolto:

   | Sintomo | Pezzo mancante |
   |---|---|
   | «Impostazioni» non parte | `XDG_CURRENT_DESKTOP`, che `gnome-session` esporta da sé |
   | «Esci» dal menu non fa nulla | `org.gnome.SessionManager`, cioè `gnome-session` |
   | `Error registering session with GDM` | la registrazione presso il gestore di accesso |
   | portali e servizi assenti nel registro | gli avvii automatici della sessione |

   Ognuno di questi è rimediabile a mano, e finora così si è fatto — ma sono
   sintomi di una scelta, non guasti indipendenti.

   L'ostacolo noto: `gnome-session` si aspetta una sessione grafica di logind su
   un seat, ed è precisamente il passaggio che `gnome-remote-desktop` risolve con
   la consegna da GDM — quella che §5.6 ha accertato non servirci per il **solo
   compositore**. Va verificato se serva per la sessione intera: è il primo
   accertamento della fase 5.

5. ~~**Senza client collegato la sessione resta senza monitor.**~~ **RISOLTA il
   3 agosto** con `palco.rs`: cattura, controllo e monitor virtuale non
   appartengono più alla connessione ma alla sessione grafica, e restano
   montati fra un client e l'altro. Verificato: dopo lo stacco Mutter conserva
   il suo schermo, non compare più alcun `Removed virtual monitor` e nessuna
   asserzione fallita. In dote arriva anche il **riaggancio**: chi si
   ricollega alla stessa misura ritrova il desktop com'era, senza rifare la
   cattura (`palco gia' montato della misura giusta: si riusa`).
   `prova-e2e.sh` lo sorveglia con due controlli dedicati.

   Il difetto era questo, ed è documentato qui perché la sua firma resta utile
   a riconoscerlo altrove. Il monitor virtuale esisteva solo mentre la cattura
   era aperta: alla disconnessione Mutter scriveva `Removed virtual monitor
   Meta-0` e restava con zero schermi. Da lì
   `libmutter` va in asserzione fallita
   (`meta_workspace_get_work_area_for_monitor: logical_monitor != NULL`), le
   applicazioni in esecuzione perdono la connessione Wayland con
   `Error 71 (Protocol error)` e quelle nuove non hanno dove aprirsi. È il
   difetto che rende la sessione inutilizzabile dopo il primo stacco, e va
   risolto in **fase 5** insieme a persistenza e riaggancio: la sessione deve
   conservare un monitor anche quando nessuno guarda. La via più semplice è non
   distruggere la cattura alla disconnessione, ma tenerne una viva finché non
   arriva il client successivo.

   **Colto sul fatto il 3 agosto**, ed è la prova che non è una questione
   teorica. L'utente ha segnalato un desktop che «non copre lo schermo». Il
   registro della Shell di quel minuto:

   ```
   04:55:31  Removed virtual monitor Meta-0
   04:55:31  meta_monitor_manager_get_logical_monitor_from_number: assertion failed
   04:55:31  meta_workspace_get_work_area_for_monitor: assertion 'logical_monitor != NULL' failed
   04:56:14  Added virtual monitor Meta-0          ← 2560x1080, non più 1920x1080
   ```

   Un client di prova dimenticato collegato a 1920x1080 era caduto 35 secondi
   prima; la sessione è rimasta **43 secondi senza alcun monitor**, con le
   applicazioni aperte, ed è ripartita con una misura diversa. Nella foto lo
   sfondo copriva circa il 76% della larghezza: **1920/2560 = 75%**.

   Non riprodotto a comando ripetendo la sola sequenza «cade il client, ne
   entra un altro con misura diversa»: serve altro — probabilmente lo stato che
   le finestre accumulano restando aperte a cavallo dello stacco. Da rifare
   quando il monitor persistente sarà in piedi, perché quella correzione
   dovrebbe togliere di mezzo la finestra patologica alla radice.

6. ~~**IronRDP non consegna bottone centrale e rotella orizzontale**~~ — **CADUTA il 3 agosto** con il
   passaggio a FreeRDP (§8-bis): era un limite di `ironrdp-server` 0.13, non del protocollo. Il testo
   originale resta qui solo perché descrive il sintomo, utile se ricomparisse.
   IronRDP non consegnava bottone centrale e rotella orizzontale sul percorso ordinario di RDP
   (§5.8). Con i client di FreeRDP non si nota, perché passano dal canale di input avanzato; con
   mstsc sì, e la rotella orizzontale può far saltare il puntatore verso l'angolo. Da sistemare a
   monte, contribuendo la correzione a IronRDP.
7. ~~**La disposizione della tastiera non viene *concordata***~~ (§5.8) — **CHIUSA il 4 agosto 2026
   con la fase 4.** Non si concorda e non si dichiara: **si legge dalla sessione**, con
   `ei_device_keyboard_get_keymap`. Misurato: la keymap arriva da libei, si compila, e REMOTIX
   scrive nel registro di quale disposizione si tratta (`English (US)`) — che è l'informazione da
   avere sotto mano il giorno in cui l'utente dice «i simboli non corrispondono».
   `REMOTIX_TASTIERA` non serve più: era il rimedio a un'informazione irraggiungibile, e ora
   l'informazione è raggiungibile.

   **Chiusa fino in fondo, RDM compreso.** La traduzione dei caratteri Unicode nel tasto fisico che
   li produce è misurata, non solo scritta: su Android non c'è una tastiera fisica da cui mandare
   scancode, quindi ciò che arriva sono caratteri, e il fatto che RDM comandi il desktop significa
   che quella traduzione funziona. Il testo che segue descrive lo stato di allora.
   Si
   può dichiarare (`REMOTIX_TASTIERA=it`) e REMOTIX la impone alla sessione: verificato, la
   posizione AC10 produce `ò` invece di `;`. Quel che manca è la scelta automatica: il client
   dichiara la propria disposizione nel Client Core Data, `ironrdp-acceptor` la conserva in
   `ConnectionResult.keyboard_layout`, ma `ironrdp-server` 0.13 non la espone ad alcun gancio.
   Serve un **contributo a monte** — lo stesso vale per la questione n.6 — dopo il quale la
   dichiarazione resterà solo come sovrascrittura.
8. **Xwayland non completa l'avvio nella VM** (§5.6). Per ora si gira con `--no-x11`, ma §4.5
   tiene X11 nello scope e senza Xwayland le applicazioni X11 non funzionano. Da capire se
   dipenda dall'assenza di accelerazione grafica — nel qual caso sparirebbe da sé con il
   passthrough della fase 9 — o se sia un difetto da aggirare comunque. **Da riverificare
   appena la VM avrà una GPU vera**, prima di investire tempo nel cercare la causa.

9. **Con mstsc, alla prima connessione dopo un cambio di misura lo sfondo copre solo la parte
   sinistra.** Segnalato dall'utente il 3 agosto, **rimandato per decisione sua** a una sessione
   dedicata dopo le altre fasi: è un difetto cosmetico e circoscritto, e non vale il blocco del
   progetto.

   Il sintomo: ci si collega con mstsc (2560x1080) dopo che il monitor era a 1920, e lo sfondo
   copre circa il 75% della larghezza — **1920/2560** — con il resto grigio. **Alla seconda
   connessione è corretto**, ed è il dato che orienta tutto: il palco viene riusato e il fotogramma
   conservato è già quello buono.

   **Cosa è già stato escluso, con misura.** Non si ricominci da qui:

   | ipotesi | esito |
   |---|---|
   | restano sessioni o monitor dei test precedenti | **no**: misurato durante la connessione, 1 monitor, 1 cattura, 1 controllo |
   | il fotogramma consegnato ha la misura vecchia | **no**: `stride=10240`, cioè 2560×4 |
   | la catena dichiara misure incoerenti | **no**: cattura, superficie EGFX, regione AVC420 e codificatore dicono tutti 2560x1080 |
   | è la panoramica Attività di GNOME | **no**: si vede anche con le finestre aperte |
   | è il primo fotogramma vuoto di Mutter | **in parte**: esiste ed è corretto (regola 3-bis), ma toglierlo non basta |
   | con FreeRDP alla stessa misura | l'immagine è **piena** |

   **L'unica differenza rimasta fra i due client** è la versione EGFX negoziata: mstsc **V10.6**,
   FreeRDP **V8.1**. Attenzione: *non* si provi a limitare il server alla 8.1 per confronto —
   l'ho fatto e mstsc resta nero, perché su quella versione non abilita AVC420 (§5.4). È un vicolo
   cieco già percorso.

   **Da dove ripartire**, in ordine di resa attesa:

   1. tracciare i messaggi EGFX inviati a mstsc (`REMOTIX_LOG=trace`) e **confrontarli** con quelli
    inviati a FreeRDP: è il metodo che ha risolto §5.4, e qui non è ancora stato applicato;
   2. verificare se con V10.x mstsc si aspetti qualcosa di diverso dopo `ResetGraphics` — per
    esempio che la superficie non venga riusata con lo stesso identificativo dopo un
    `DeleteSurface`;
   3. leggere come `gnome-remote-desktop` gestisce il cambio di misura del monitor, che è il
    riferimento e ha già risolto due volte problemi di questo tipo.

10. **La sessione grafica che REMOTIX avvia non è registrata in `logind`.** Vive dentro la
    sessione di chi ha lanciato il server — oggi una sessione SSH, che `logind` vede come `tty` —
    perché `gnome-session` resta nel cgroup di chi lo avvia e non ne crea una propria. Misurato
    nella VM il 3 agosto.

> ⚠ **Ritirata il 4 agosto 2026, la sera dello stesso giorno.** Per qualche ora questa nota ha
> detto che la questione n.10 «uccide il server»: che all'«Esci» GNOME smontasse l'intero albero
> dell'utente, che REMOTIX morisse in tutti e tre i cgroup provati (`session-N.scope`, `app.slice`,
> `background.slice`), e che quindi la fase 5 non si chiudesse senza la fase 12.
>
> **Era falso, e le tre misure erano vere.** Il `SIGTERM` arrivava in tutti e tre i casi perché non
> veniva da fuori: era REMOTIX a mandarselo, dentro `libgio`, che sulla connessione condivisa al bus
> di sessione tiene acceso `exit-on-close` e chiama `raise(SIGTERM)` quando il bus si chiude. Tre
> misure concordi su un mittente **mai chiesto**, sempre soltanto dedotto. Chiedere `si_pid` al
> nucleo ha risolto la questione in una sola esecuzione — §7.4 di `REFERENCE.md`.
>
> **La fase 5 si chiude senza la fase 12.** La questione n.10 resta aperta per quello che dice il
> testo qui sotto, e per nient'altro: il sistema non sa che esiste una sessione remota.

    Conseguenza: **il sistema non sa che esiste una sessione grafica remota**. Chi guarda
    `loginctl` non la vede, e un gestore di accesso grafico non ha modo di accorgersene per
    proporre di riprenderla invece di aprirne un'altra. Oggi la regola di §5.10 tiene lo stesso —
    perché a chiudere la sessione remota è REMOTIX, che sa di averla avviata — ma è una garanzia
    che sta tutta dentro il nostro processo: se REMOTIX non fosse in esecuzione, la sessione
    resterebbe lì invisibile.

    È anche ciò che tiene aperta la finestra di sovrapposizione del **caso 8** della tabella di
    §3.4: senza una sessione registrata, il gestore di accesso non sa che deve aspettare, e per
    tre secondi le due sessioni grafiche coesistono.

    Il rimedio è quello che §3.4 (nota su PAM) già prevede: **aprire una sessione PAM** quando si
    avvia la sessione grafica — classe `user`, tipo `wayland`, senza seat, `remote` vero — e
    tenerla aperta quanto la sessione. È lo stesso meccanismo di `finta-sessione-locale`, che è
    già scritto e funziona, con l'avvertenza già pagata: `pam_systemd` non registra nulla se il
    processo chiamante è già dentro una sessione, quindi la sessione grafica andrebbe avviata
    fuori da quella di chi lancia il server. Da fare quando REMOTIX diventerà un servizio
    (fase 12), perché è lì che il problema si presenta davvero.
