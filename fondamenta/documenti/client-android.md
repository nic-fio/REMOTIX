# L'ambiente Android come client RDP — studio

*Che cosa c'è, che cosa fa sul filo, che cosa decodifica, e che cosa REMOTIX deve provare.*

Android è nell'elenco dei client di riferimento di REMOTIX fin dall'inizio (§3.7 di `SPECIFICA.md`), e
non per completezza: è il client che ha fatto emergere **quasi tutte** le regole di §5.7 — le regole 1,
2 e 3 sono state scoperte perché il client Android faceva cose che gli altri due non facevano.

Questo documento raccoglie ciò che si può sapere senza provare, separa ciò che è **verificato** da ciò
che va **misurato**, e chiude con un piano di prove.

Fonti: il sorgente di **FreeRDP 3.22.0** per il client ufficiale Android (tutte le costanti riportate
sono lette da lì); le note di rilascio e gli avvisi di sicurezza di Devolutions; la documentazione
Microsoft; le misure già registrate in [`SPECIFICA.md`](SPECIFICA.md) §5.4 e §5.7.

> ⚠ **Una lacuna da colmare subito.** `SPECIFICA.md` parla sempre di *«un client Android moderno»* e
> non registra mai **quale**. Tutte le misure di §5.4 e §5.7 — comprese quelle su cui poggiano le
> regole 1, 2 e 3 — sono state fatte con un client che non sappiamo nominare. Ora che si è scelto
> Remote Desktop Manager come client di riferimento, **quelle misure vanno rifatte e attribuite**,
> perché client Android diversi si comportano in modo molto diverso (§6).

---

## 1. Il panorama nel 2026

### 1.1 Windows App (Microsoft) — il client ufficiale, ed è un problema

Microsoft ha **ritirato** «Remote Desktop» e lo ha sostituito con **Windows App**, disponibile su
Google Play come `com.microsoft.rdc.androidx`. Il ritiro è avvenuto per gradi: la versione dal
Microsoft Store è stata dismessa il **27 maggio 2025**, l'installer MSI classico e il client web il
**27 maggio 2026**. Su Android il passaggio è già completato.

Windows App non è un client RDP: è **un portale verso i servizi di virtualizzazione Microsoft** —
Windows 365, Azure Virtual Desktop, Dev Box, Remote Desktop. Il collegamento diretto a un PC c'è, ma
non è più il caso d'uso principale, e si vede.

**I problemi documentati**, che confermano la valutazione dell'utente:

- la pagina ufficiale delle limitazioni note elenca, per Android/Chrome OS, **una sola voce**, e
  riguarda l'accesso con identità esterne. Cioè: le limitazioni reali non sono documentate;
- la community Microsoft riporta **latenza di input e schermate congelate** con RemoteApp e su
  dispositivi palmari;
- arresti anomali attivando la redirezione dell'archiviazione;
- errori di connessione aprendo file `.rdp`;
- la tastiera virtuale che smette di funzionare — barra spaziatrice e alcuni numeri;
- nessuna nota di rilascio trasparente e **nessun modo di tornare a una versione precedente** senza
  riconfigurare tutto.

> Per REMOTIX Windows App resta comunque **un client di prova obbligatorio**, non perché sia buono ma
> perché è quello che la maggior parte delle persone si troverà installato. Se REMOTIX non funziona
> lì, «non funziona su Android» per il novanta per cento di chi prova.

### 1.2 Remote Desktop Manager (Devolutions) — la scelta

> **Giudizio dell'utente, 3 agosto 2026.** *«Escludendo prodotti di nicchia, disponibili solo a
> pagamento e legati al mondo enterprise, fra tutti gli altri Remote Desktop Manager è l'unico che ho
> trovato soddisfacente.»*
>
> Non è una preferenza fra pari: è il risultato di averli provati. E il criterio con cui è stato
> ottenuto — niente nicchia, niente solo-a-pagamento, niente legato all'azienda — **è coerente con
> quello che REMOTIX è** (§1 di `SPECIFICA.md`: uso personale e piccola scala). Un client che
> presuppone un abbonamento o un'infrastruttura aziendale non serve a chi vuole raggiungere il proprio
> desktop.
>
> Ne discende l'ordine di priorità per tutto il progetto:
>
> | | Ruolo |
> |---|---|
> | **Remote Desktop Manager** | **Il client Android di riferimento.** Se non funziona qui, non funziona |
> | **Windows App** | Client di verifica obbligatorio, **non** di riferimento: si prova perché è quello che la gente si trova installato, non perché sia buono |
> | **aFreeRDP** | Strumento di sviluppo (§1.3), non client d'uso |
>
> Il che riduce anche il peso della lacuna segnalata in testa a questo documento: le misure di §5.4 e
> §5.7 vanno rifatte **con RDM**, e quello che dicono su RDM è quello che conta.

Pacchetto `com.devolutions.remotedesktopmanager`. Versione più recente al momento dello studio:
**2026.2.1.6**, di fine luglio 2026. Aggiornamenti frequenti (2026.1.x → 2026.2.x nel giro di mesi).

### 1.2-bis Perché è il più veloce, ed è istruttivo

*Osservazione dell'utente, 3 agosto 2026: «fra i client che ho provato, RDM è comunque di gran lunga
più performante di aRDP e del client ufficiale MS».*

Sembra un paradosso — RDM è l'unico dei tre che **non** decodifica H.264 — e invece è la spiegazione.

| Client | Cosa decodifica | Costo sul telefono |
|---|---|---|
| aFreeRDP | H.264 **in software** (OpenH264; MediaCodec spento nei rilasci, §2.1) | CPU satura, calore, fotogrammi persi |
| Windows App | H.264 | latenza e congelamenti documentati (§1.1) |
| **RDM** | **RemoteFX Progressive** su EGFX | decodifica a costo basso |

RemoteFX Progressive è un codec **a wavelet pensato per il contenuto desktop**: poca CPU, nessun
decodificatore hardware richiesto, e **progressivo** — raffina l'immagine invece di ritrasmetterla.

> **La conclusione che conta per il progetto**: su un telefono, H.264 *senza* decodificatore hardware
> è peggio di un buon codec desktop. La scelta di Devolutions non è arretratezza, è ingegneria per il
> mobile. Aggiungere RFX Progressive a REMOTIX non è quindi una concessione a un client limitato: è
> **allinearsi a ciò che su Android rende di più**.

Non è nato come client RDP: è un **gestore di connessioni** che parla RDP, VNC, ARD, SSH, Telnet,
FTP/SFTP/SCP, RDP Gateway e una cinquantina d'altro. La parte RDP è una funzione fra molte, il che è
insieme un pregio (è mantenuta da chi vive di accesso remoto) e un rischio (non è il prodotto).

**Quello che le note di rilascio dicono della parte RDP** — ed è tutto ciò che è pubblicamente
verificabile:

| Area | Che cosa espone |
|---|---|
| **Risoluzione** | «Force Dynamic Resolution» con interruttore **Scale Factor**; modalità «Stretch»; risoluzione personalizzata (aggiunta dopo: prima si usava sempre quella del dispositivo) |
| **Tastiera** | Configurazione della disposizione; **«Disable local IME»**; modalità dei tasti funzione in una sezione dedicata; supporto Unicode per la disposizione portoghese |
| **Puntatore** | Opzioni di visualizzazione del cursore; **modalità dimensione puntatore, con configurazione 32×32**; **Pointer Capture**; supporto stilo |
| **Input fisico** | Mouse fisico e tastiera hardware |
| **Audio** | Audio e microfono nelle sessioni RDP |
| **Appunti** | Presenti (i pulsanti Copia/Incolla/Taglia sono stati introdotti e poi rimossi) |
| **Rete** | RDP Gateway |
| **Altro** | Samsung DeX; scanner di codici a barre; ripresa della sessione |

**Due cose che le note di rilascio non dicono, e sono le due che contano di più:**

1. **quale motore RDP usa.** Non è documentato pubblicamente. Devolutions sviluppa **IronRDP**
   (implementazione RDP in Rust, la stessa che REMOTIX ha usato fino al 3 agosto), ma non c'è alcuna
   dichiarazione che il client Android la usi, e non se ne trova traccia. **Va trattato come
   un'incognita** e determinato sul filo (§9);
2. **se e come negozia EGFX e H.264.** Nessuna menzione di EGFX, AVC, H.264 o RemoteFX in tutte le
   note di rilascio. Anche questo va misurato.

> ⚠ **Un precedente di sicurezza da tenere presente: CVE-2024-11621.** Fino alla versione **2024.3.3.7**
> compresa, RDM su Android — e su macOS, Linux, iOS e PowerShell — **non validava affatto il
> certificato TLS**: qualunque certificato veniva accettato senza avvisare l'utente. CVSS 8.6.
>
> Corretto nelle versioni successive. La conseguenza pratica per REMOTIX è che **il comportamento con
> un certificato autofirmato è cambiato**: prima passava in silenzio, ora deve fare qualcosa. Che cosa
> — avviso, rifiuto, o accettazione con impronta memorizzata — **è la prima cosa da provare**, perché
> REMOTIX userà certificati autofirmati (§7.3 di `protocollo-rdp.md`).

### 1.3 aFreeRDP — il client ufficiale di FreeRDP

Pacchetto `com.freerdp.afreerdp`, distribuito su F-Droid. È **nell'albero di FreeRDP**
(`client/Android/Studio`), quindi tutto ciò che lo riguarda è verificabile leggendo il codice — ed è
l'unico dei tre di cui si possa dire qualcosa con certezza. Vedi §3.

Per REMOTIX ha un ruolo particolare e va capito bene: siccome il server sarà **anch'esso FreeRDP 3**,
provare con aFreeRDP significa mettere alle due estremità la **stessa libreria**. È quindi ottimo come
client di sviluppo — riproduce in fretta, i registri sono leggibili, si può ricompilare — e **pessimo
come prova di conformità**, perché entrambe le parti condividono le stesse assunzioni e gli stessi
difetti. Vale la lezione di §5.7 di `SPECIFICA.md`: *«non basta che una prova sia verde, deve provare
sul client che il difetto lo mostra»*.

### 1.4 Gli altri

| Client | Note |
|---|---|
| **Jump Desktop** | A pagamento, RDP e VNC, buona reputazione per l'esperienza d'uso |
| **Parallels Client** | Gratuito, orientato a RAS/VDI, redirezioni ricche |
| **aFreeRDP SC** | Fork di aFreeRDP con smartcard (Rutoken), MPL 2.0 |
| **Chrome Remote Desktop** | Non parla RDP: protocollo proprietario Google |

Nessuno di questi entra fra i client di riferimento. Jump Desktop può servire come terzo parere se
RDM e Windows App divergono su qualcosa.

---

## 2. La domanda che decide tutto: come si decodifica H.264 su Android

REMOTIX manda **H.264 AVC420 su EGFX** e nient'altro (§3.1 di `SPECIFICA.md`). Su Android quel flusso
può finire in due posti molto diversi, e la differenza si vede sulla batteria, sul calore e sui
fotogrammi persi.

| Via | Che cos'è | Costo |
|---|---|---|
| **Hardware** — `MediaCodec` | Il decodificatore del SoC, via `AMediaCodec` dell'NDK | Quasi gratis: decine di milliwatt |
| **Software** — OpenH264 / FFmpeg | Decodifica sulla CPU | 4K30 è **fuori portata** su quasi ogni telefono; 1080p30 costa uno o due core |

### 2.1 aFreeRDP decodifica in software, ed è verificato

Le configurazioni di rilascio ufficiali di FreeRDP per Android
(`scripts/android-build-release.conf` e `android-build-64.conf`) dicono:

```
WITH_OPENH264=1          ← decodifica software, Cisco OpenH264 v2.6.0
WITH_MEDIACODEC=0        ← decodifica hardware SPENTA
WITH_FFMPEG=1            ← FFmpeg n7.1.2 (per audio e come alternativa)
NDK_TARGET=23 / 21
BUILD_ARCH="armeabi-v7a x86 arm64-v8a x86_64"
```

E il backend MediaCodec, che pure esiste (`libfreerdp/codec/h264_mediacodec.c`, 527 righe), è
dichiarato **sperimentale** nelle opzioni di build:

> `option(WITH_MEDIACODEC "[experimental] Use MediaCodec API (currently no fallback if no device support)" OFF)`

Cioè: nessun ripiego se il dispositivo non lo supporta. Per questo è spento nei rilasci.

**Conseguenza diretta per REMOTIX**: con aFreeRDP, un flusso 4K a 30 fps viene decodificato **dalla CPU
del telefono**. Il punto di lavoro di §3.1 di `SPECIFICA.md` — 4K30 come modalità ordinaria — su
Android **non è realistico** con questo client. La scala di ripiego (2K, poi 1080p) non è una rete di
sicurezza: su Android è la modalità normale.

### 2.2 Che cosa il decodificatore accetta

OpenH264 supporta in decodifica il **Constrained Baseline** e il **Constrained High**. «Constrained
High» è il High profile **senza fotogrammi B e senza codifica di campo**, ma **con** CABAC, predizione
intra 8×8, trasformata 8×8 e matrici di quantizzazione.

Da cui **due regole vincolanti per il codificatore di REMOTIX**:

1. **mai fotogrammi B.** Non è solo una questione di compatibilità: un fotogramma B richiede di
   attendere quello successivo, e in un desktop remoto significa aggiungere un fotogramma di latenza.
   RDP AVC420 ragiona per I e P, e va tenuto così;
2. **mai codifica interlacciata / di campo.**

Con quei due vincoli, **High profile con CABAC va bene** — e conviene, perché CABAC vale da solo un
5–10 % di banda rispetto a CAVLC. È anche quello che il riferimento produce
(`gnome-remote-desktop.md` §9: `H264_PROFILE_HIGH`, `constraint_set4_flag = 1` e
`constraint_set5_flag = 1`, che sono esattamente i due flag che dichiarano «niente B, niente campo» —
cioè **Constrained High**).

> Questa è la conferma incrociata più utile di tutto il documento: il riferimento produce già
> esattamente il profilo che il decodificatore Android accetta, e lo dichiara con i flag giusti.
> **Copiare quei due `constraint_set` non è cosmesi: è ciò che rende il flusso decodificabile su
> Android.**

### 2.3 Se invece si passasse da MediaCodec

Il backend hardware, quando è acceso, ha vincoli propri che vale la pena conoscere perché sono i
vincoli **del dispositivo**, non della libreria:

- **dimensione minima 320×240** (`MEDIACODEC_MINIMUM_WIDTH/HEIGHT`). Sotto quella, il decodificatore
  si rifiuta di partire;
- formato di uscita richiesto: `COLOR_FormatYUV420Planar` (19), con `COLOR_FormatYUV420Flexible`
  (`0x7f420888`) come alternativa;
- il decodificatore **può cambiare da sé la misura di uscita** rispetto a quella d'ingresso
  (`AMEDIACODEC_INFO_OUTPUT_FORMAT_CHANGED`), e chi consuma deve rileggere lo stride;
- la riconfigurazione a caldo (cambio di risoluzione) passa da `AMediaFormat_setInt32` e un riavvio del
  decodificatore: **non è gratuita**, e un ridimensionamento a raffica la fa pagare a ogni passo.

L'ultimo punto è quello che riguarda REMOTIX: **su Android un ridimensionamento non è solo una
rinegoziazione di protocollo, è un riavvio del decodificatore**. Un altro motivo per accorpare le
raffiche di `MONITOR_LAYOUT` invece di applicarle una per una (§12 di `gnome-remote-desktop.md`).

### 2.4 Che cosa chiede aFreeRDP quando accende H.264

Nel codice del client (`LibFreeRDP.java`):

```java
if (flags.getGfx())            args.add("/gfx");
if (flags.getH264() && mHasH264) args.add("/gfx:AVC444");
```

Cioè: due interruttori distinti nell'interfaccia — **«Gfx»** e **«Gfx H264»** — e quando il secondo è
acceso il client chiede **AVC444**, non AVC420. `mHasH264` viene da `freerdp_has_h264()`, che riflette
la build.

Tre conseguenze:

1. **EGFX e H.264 sono separati.** Un utente può negoziare EGFX con H.264 spento: il client
   annuncerà `RDPGFX_CAPS_FLAG_AVC_DISABLED` e il server dovrà mandare **RemoteFX Progressive o niente**.
   Con un server solo-AVC420 significa **schermo nero**;
2. **le opzioni sono spente per default** nelle impostazioni di aFreeRDP, e vanno accese a mano;
3. chiedere AVC444 non obbliga il server a mandarlo: AVC420 resta lecito. Ma dice che il client si
   aspetta il meglio.

> **La regola operativa che ne discende, e che vale per ogni client Android**: prima di dare la colpa
> al server, **verificare che nel client l'opzione grafica sia accesa**. Uno schermo nero su Android con
> registri del server puliti è, nella maggioranza dei casi, un interruttore spento nel client.

---

## 3. aFreeRDP nei numeri

Tutto verificato sul sorgente di FreeRDP 3.22.0.

| Voce | Valore |
|---|---|
| `minSdkVersion` | **23** (Android 6.0 Marshmallow) |
| `targetSdkVersion` / `compileSdkVersion` | **35** (Android 15) |
| NDK | 29.0.13113456 |
| Architetture | `armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64` |
| Decodifica H.264 | OpenH264 **v2.6.0**, software |
| MediaCodec | **spento** nei rilasci |
| FFmpeg | n7.1.2 |
| OpenSSL | 3.5.3 |
| Tipo di build | `Release` |

Le impostazioni per connessione esposte all'utente (`BookmarkBase.java`) comprendono risoluzione,
profondità colore, **`perf_remotefx`**, **`perf_gfx`**, **`perf_gfx_h264`**, e una serie parallela con
suffisso `_3g` — cioè **due profili distinti, uno per WiFi e uno per rete mobile**, con impostazioni
grafiche indipendenti.

> Quest'ultima è un'idea da rubare concettualmente: il client sa già che WiFi e rete mobile sono due
> mondi. Un server che adatta alla banda misurata (§10 di `gnome-remote-desktop.md`) ottiene la stessa
> cosa senza chiedere niente all'utente.

---

## 4. Il display Android, e che cosa arriva al server

### 4.1 La misura che il client dichiara non è quella del pannello

Un telefono del 2026 ha tipicamente un pannello da 1080×2400 o 1440×3200 con densità 400–500 dpi. **Ma
quello che il client dichiara al server nel Client Core Data non è il pannello**: è la misura della
sua finestra utile, in pixel, dopo aver tolto barra di stato, barra di navigazione, ritaglio della
fotocamera, e dopo l'eventuale fattore di scala che il client applica.

Per RDM su Android il valore predefinito è **la risoluzione del dispositivo**; la possibilità di
imporne una personalizzata è stata aggiunta in seguito. La modalità consigliata da Devolutions stessa
per avere prestazioni accettabili è **«Dynamic Resolution»**.

Ne discendono tre cose che il server deve aspettarsi:

1. **misure verticali.** Un desktop 1080×2400 è una geometria che nessun desktop Linux si aspetta. Il
   compositore la accetta, ma il risultato è un desktop altissimo e strettissimo. Non è un difetto del
   server, ma è un caso da provare;
2. **misure dispari.** Larghezze e altezze arbitrarie, non multiple di 16 né di 64, non
   necessariamente pari. **L'allineamento del codificatore va assorbito riempiendo il bordo** — la
   regola operativa già scritta in §5.4 di `SPECIFICA.md`;
3. **misure fuori dai limiti.** MS-RDPEDISP impone 200–8192 per lato
   (`protocollo-rdp.md` §12). Un tablet in orizzontale ci sta comodamente; una finestra ridotta a
   striscia in multi-finestra Android **no**, e la richiesta va rifiutata invece che applicata.

### 4.2 Frequenza di aggiornamento

I telefoni recenti hanno pannelli a 90, 120 o 144 Hz, spesso **adattivi**: il sistema abbassa la
frequenza da solo quando il contenuto è statico. Per un desktop remoto questo è **un vantaggio, non un
problema**: mandare 30 fps a un pannello che scende a 30 Hz è coerente.

Non c'è nulla nel protocollo RDP che comunichi la frequenza del pannello. Il server non la saprà mai:
si regola sui riscontri dei fotogrammi (§10.2 di `gnome-remote-desktop.md`), che è la grandezza giusta
perché misura la catena intera — rete, decodifica e disegno — invece del solo schermo.

### 4.3 Rotazione

Ruotare il dispositivo cambia la geometria della finestra, e un client con risoluzione dinamica manda
un `MONITOR_LAYOUT` nuovo. Sul server questo è **un rimontaggio completo**: nuova misura del monitor
virtuale, nuova superficie EGFX, nuovo `ResetGraphics`, e su Android anche **un riavvio del
decodificatore** (§2.3).

Va provato esplicitamente, ruotando avanti e indietro qualche volta di seguito, perché è il modo più
facile di generare la raffica di ridimensionamenti che la macchina a stati del layout deve assorbire.

---

## 5. L'input da Android

È l'area dove Android diverge di più da un client desktop, e dove REMOTIX ha già una questione aperta
(n.1, input touch).

### 5.1 Il tocco

I client offrono tipicamente due modalità:

- **modalità puntatore** — il dito muove un cursore, come un trackpad. Sul filo sono **eventi mouse
  normali** (`PTR_FLAGS_MOVE`, `BUTTON1`), e il server non si accorge di niente;
- **modalità tocco diretto** — il dito è il puntatore. Se il client supporta **MS-RDPEI** manda veri
  eventi di contatto sul canale `Microsoft::Windows::RDS::Input`; altrimenti li emula come clic.

**Che cosa fa RDM non è documentato.** Le note di rilascio menzionano «Touch mode», «Pointer Capture» e
il supporto allo stilo, ma non MS-RDPEI. Da misurare: se il canale `Microsoft::Windows::RDS::Input`
viene aperto, il client fa tocco nativo.

> Per REMOTIX la questione n.1 si può quindi riformulare: **non serve implementare MS-RDPEI finché il
> client di riferimento non lo usa**. Se RDM emula il mouse, il tocco funziona già oggi. Se lo usa,
> senza il canale si perdono i gesti multi-dito.

### 5.2 La tastiera software

È il punto più delicato. Una tastiera Android **non è una tastiera fisica**: non ha scancode, ha un
IME che produce testo.

La conseguenza sul protocollo: i client Android mandano prevalentemente **eventi Unicode**
(`FASTPATH_INPUT_EVENT_UNICODE`) invece di scancode, almeno per i caratteri stampabili; per i tasti di
controllo (Invio, Tab, frecce, modificatori) mandano scancode.

Da cui:

1. **il percorso Unicode non è un ripiego, su Android è la strada principale.** Va implementato bene:
   keysym → posizione fisica nella disposizione *della sessione*, con i modificatori di livello
   applicati intorno (§13.2 di `protocollo-rdp.md`);
2. **la disposizione dichiarata dal client (KLID) è quasi inutile su Android**, perché quello che arriva
   è già il carattere finale. Il che, per la questione aperta n.7, è una buona notizia: sul client dove
   il KLID sarebbe meno affidabile, il KLID non serve;
3. l'opzione **«Disable local IME»** di RDM esiste proprio per forzare il percorso a scancode quando
   l'IME dà problemi. È un interruttore che cambia radicalmente ciò che arriva al server, e va provato
   **in entrambe le posizioni**.

### 5.3 Mouse e tastiera fisici

Android supporta mouse e tastiere Bluetooth o USB, e RDM li gestisce, con anche **Pointer Capture** —
l'API Android che cattura il puntatore e consegna movimenti **relativi**.

Se il client usa Pointer Capture, sul filo può mandare `TS_FP_RELPOINTER_EVENT` (§13.1 di
`protocollo-rdp.md`), che è un percorso diverso da quello assoluto: **va gestito anche quello**, altrimenti
con un mouse collegato il puntatore non si muove.

### 5.4 Lo stilo

RDM dichiara il supporto stilo. Sul filo, un vero supporto passa da MS-RDPEI (campi `PRESSURE`,
`TILTX`, `TILTY`, `ROTATION`); senza quel canale è un mouse con un dito sottile. Da misurare.

---

## 6. Che cosa il client Android fa sul filo — quello che già sappiamo

Dalle misure registrate in `SPECIFICA.md`, con l'avvertenza del cappello: **non sappiamo con quale
client Android siano state fatte.**

| Comportamento | Dove | Conseguenza |
|---|---|---|
| **Chiede la propria misura entro un decimo di secondo dalla connessione, prima di negoziare EGFX** | §5.7 regola 2 | Il ridimensionamento va **rinviato** fino a 1,5 s aspettando la pipeline |
| **Dopo una riattivazione non rinegozia più EGFX**, per il resto della sessione | §5.7 regola 1 | Mai usare Deactivate All per cambiare misura |
| **Disegna la superficie anche senza `MapSurfaceToOutput`** | §5.4 | Indulgenza che nasconde un difetto del server |
| **Disegna anche i fotogrammi EGFX non compressi** | §5.4 | Idem |
| **Alla chiusura del socket resta lì**, mostrando l'ultimo fotogramma | §5.9 | Serve un congedo esplicito: `SET_ERROR_INFO`, e in subordine un RST |
| **Il logout mostrava uno sfondo pulito senza finestre**, visivamente identico a un desktop vivo | §5.9 | Il client non ha modo di sospettare che la sessione sia finita |

L'ultima riga è quella che è costata di più: il difetto è stato **segnalato dall'utente su Android**, e
su nessun altro client si vedeva, perché xfreerdp esce da solo alla chiusura del socket.

E c'è un'osservazione dal riferimento che riguarda Android in modo diretto:

> `gnome-remote-desktop` **spegne l'audio in uscita** quando il client è iOS o Android, con la
> motivazione scritta nel codice: *«Client cannot handle graphics and audio simultaneously»*
> (`grd-session-rdp.c:1323`).

Non è una diceria: è una decisione presa nel riferimento e mantenuta. Va verificata con RDM, perché se
è vera anche lì, **§3.2 di `SPECIFICA.md` (audio AAC) e §3.7 (Android fra i client di riferimento)
sono in tensione fra loro** e la tensione va risolta consapevolmente, non scoperta in prova.

---

## 7. Rete e ciclo di vita dell'applicazione

Tre fatti di Android che un server desktop remoto sente, e che un client desktop non ha.

**Il passaggio WiFi ↔ rete mobile** cambia l'indirizzo IP e uccide la connessione TCP. Il client
riprova; il server vede un client sparito e uno nuovo. Con la regola della sessione unica di §3.4 di
`SPECIFICA.md`, il secondo verrebbe **rifiutato** finché il primo non è stato dichiarato morto — cioè
per i 30 secondi di `TCP_USER_TIMEOUT`. Su Android quel caso non è raro: è quotidiano.

> **È il caso d'uso che più mette alla prova la scelta di rifiutare invece di soppiantare.** Vale la
> pena misurarlo: uscire di casa con la sessione aperta, e contare quanti secondi passano prima di
> poter rientrare. Se sono trenta, l'esperienza è cattiva; e la risposta giusta probabilmente non è
> cambiare la regola, ma **accorciare il rilevamento** con il battito RDP (`protocollo-rdp.md` §4.2),
> che misura il client invece del socket.

**Doze e le restrizioni in background**: quando l'applicazione va in secondo piano, Android può
sospenderne l'attività di rete. La sessione RDP smette di consumare fotogrammi, i riscontri non
arrivano, e il regolatore di flusso del server (§10.2 di `gnome-remote-desktop.md`) va in throttling
totale. È il comportamento corretto — ma il server deve distinguere **«il client è occupato»** da
**«il client è morto»**, e il criterio è il tempo.

**Lo schermo che si spegne**: il client tipicamente sospende gli aggiornamenti. Alcuni mandano un
`SuppressOutput` (§10.3 di `gnome-remote-desktop.md`), che è la cosa giusta e che il server deve
onorare smettendo di codificare. Se un client non lo manda, il server continua a codificare per uno
schermo spento — spreco puro, su entrambe le batterie.

---

## 8. Samsung DeX

RDM lo dichiara esplicitamente. DeX trasforma il telefono in un desktop con schermo esterno, mouse e
tastiera: significa **finestra ridimensionabile, mouse vero, tastiera vera, risoluzione da monitor**.

Per REMOTIX è il caso Android **più simile a un client desktop** e quindi il più facile; ma è anche
quello in cui la risoluzione dinamica viene esercitata sul serio, perché la finestra si trascina.

Vale come caso di prova a sé, non come variante del telefono.

---

## 9. Che cosa va misurato — il piano di prove Android

Nessuna delle domande che contano ha risposta pubblica. Ecco come si risponde, in ordine.

### 9.1 Prima tornata — che cosa negozia RDM

Da fare con il registro del server a livello `trace`, una connessione sola, guardando i PDU:

| # | Domanda | Come si legge |
|---|---|---|
| 1 | **Livello di sicurezza** | `RDP_NEG_REQ`: chiede `PROTOCOL_SSL` o pretende `HYBRID` (NLA)? |
| 2 | **Certificato autofirmato** | Avvisa, rifiuta, o accetta? (dopo CVE-2024-11621, §1.2) |
| 3 | **EGFX** | `RNS_UD_CS_SUPPORT_DYNVC_GFX_PROTOCOL` (0x0100) negli early caps? |
| 4 | **Versione EGFX** | Quale `RDPGFX_CAPVERSION_*` nel `CAPSADVERTISE`? |
| 5 | **AVC** | `AVC_DISABLED` acceso o spento? `AVC420_ENABLED` in 8.1? |
| 6 | **MS-RDPEDISP** | Apre `Microsoft::Windows::RDS::DisplayControl`? |
| 7 | **MS-RDPEI** | Apre `Microsoft::Windows::RDS::Input`? |
| 8 | **Autodetect** | `RNS_UD_CS_SUPPORT_NETCHAR_AUTODETECT` (0x0080)? |
| 9 | **Errore alla chiusura** | `RNS_UD_CS_SUPPORT_ERRINFO_PDU` (0x0001)? |
| 10 | **Misura dichiarata** | Che geometria arriva nel Client Core Data, e coincide col pannello? |
| 11 | **Quando chiede la misura** | Prima o dopo aver negoziato EGFX? (è la regola 2 di §5.7) |

Le stesse undici domande vanno fatte a **Windows App** e a **aFreeRDP**, e messe in tabella. È
mezz'ora di lavoro e sostituisce tutte le congetture di questo documento.

### 9.2 Seconda tornata — che cosa regge

| # | Prova | Che cosa dice |
|---|---|---|
| 12 | 1080p30, poi 2K, poi 4K | Dove si ferma la decodifica prima di perdere fotogrammi |
| 13 | La stessa scena per dieci minuti | Calore e batteria: se scalda, sta decodificando in software |
| 14 | Rotazione avanti e indietro cinque volte | La macchina a stati del layout assorbe la raffica? |
| 15 | Tastiera software, testo con accenti e punteggiatura | Il percorso Unicode è corretto? |
| 16 | «Disable local IME» acceso, stessa prova | Che cosa cambia sul filo |
| 17 | Mouse Bluetooth collegato | Arrivano eventi assoluti o relativi? |
| 18 | Audio acceso insieme al video | Il problema che il riferimento dichiara esiste davvero? |
| 19 | Uscire di casa (WiFi → mobile) | Quanti secondi prima di poter rientrare |
| 20 | Schermo spento e riacceso | Arriva `SuppressOutput`? |
| 21 | «Esci» dalla sessione | Il client se ne accorge con `SET_ERROR_INFO`? |

La 21 è la riprova di un difetto già trovato e corretto (§5.9 di `SPECIFICA.md`), e va rifatta perché
**la correzione precedente usava un RST**; con FreeRDP si manda `ERRINFO_LOGOFF_BY_USER` e il
comportamento del client può essere diverso — si spera migliore.

### 9.3 Le tre incognite che decidono il progetto

1. **RDM negozia AVC420?** Se no, un server solo-AVC420 non serve il client di riferimento Android, e
   §3.7 di `SPECIFICA.md` va riaperto: o si aggiunge RemoteFX Progressive come secondo codec, o Android
   esce dai client di riferimento.
2. **RDM decodifica in hardware?** Se no, il punto di lavoro su Android è 1080p, non 4K, e la scala di
   ripiego di §3.1 va riscritta con Android in mente.
3. **Audio e video insieme reggono?** Se no, va deciso se spegnere l'audio su Android come fa il
   riferimento, o accettare il degrado.

---

## 10. Che cosa cambia nella specifica, comunque vada

Indipendentemente dalle misure, tre cose sono già acquisite.

**1. Il codificatore va vincolato a Constrained High.** Niente fotogrammi B, niente codifica di campo,
`constraint_set4_flag = constraint_set5_flag = 1`. Non è una preferenza: è ciò che rende il flusso
decodificabile dal decodificatore software che Android usa più spesso. (§2.2)

**2. Il percorso Unicode dell'input è primario, non secondario.** §5.8 di `SPECIFICA.md` lo tratta come
«rimedio parziale»: su Android è la strada normale. (§5.2)

**3. Le misure di §5.4 e §5.7 vanno riattribuite.** Sono state fatte con un client Android ignoto, e
tre delle regole più importanti del progetto poggiano su di esse. Rifarle con RDM è la prima voce del
piano di prove, non l'ultima.

---

## 11. Riepilogo: che cosa è verificato e che cosa no

**Verificato sul sorgente o su fonte ufficiale:**

- aFreeRDP: API 23–35, NDK 29, OpenH264 v2.6.0 in software, MediaCodec spento, FFmpeg n7.1.2,
  OpenSSL 3.5.3, quattro architetture;
- aFreeRDP chiede `/gfx` e `/gfx:AVC444` come due interruttori distinti, entrambi spenti per default;
- MediaCodec: minimo 320×240, `COLOR_FormatYUV420Planar`, sperimentale e senza ripiego;
- OpenH264 decodifica Constrained Baseline e Constrained High;
- Windows App ha sostituito Remote Desktop su Android; le limitazioni note documentate per Android
  sono **una sola**; i problemi riportati dalla community sono latenza, congelamenti, arresti anomali
  e tastiera;
- RDM Android 2026.2.1.6, aggiornato di frequente; espone risoluzione dinamica con fattore di scala,
  IME disattivabile, Pointer Capture, stilo, audio e microfono, DeX;
- CVE-2024-11621: RDM Android ≤ 2024.3.3.7 non validava i certificati TLS.

**Misurato sul campo il 3 agosto 2026** — telefono reale, proxy byte-per-byte, xrdp 0.10.1 a `TRACE` e
`gnome-remote-desktop` 48.1. Il quadro completo è in [`REFERENCE.md`](REFERENCE.md) §1.1:

- RDM **accetta TLS puro**, non pretende NLA (offre `SSL | HYBRID`), e accetta il certificato
  autofirmato;
- il suo stack TLS è **vecchio**: massimo TLS 1.2, niente SNI, cipher Camellia e GOST → OpenSSL 1.x.
  Ne discende che **non è IronRDP** (un client Rust mostrerebbe TLS 1.3 e GREASE);
- **negozia EGFX alla versione 10.7**, più in alto di mstsc;
- **non decodifica H.264**: `AVC_DISABLED` in tutte le versioni, e il selettore codec si ferma a
  *RDP 8.0*. Verificato due volte;
- apre `RDPGFX`, `DISP`, `AUDIO_PLAYBACK`, `AUDIO_INPUT`, `CLIPRDR`, `TELEMETRY` — **non** MS-RDPEI:
  il tocco arriva come mouse;
- audio: **solo PCM**, né AAC né Opus;
- **è un client severo**, della famiglia di mstsc: riscontra i fotogrammi e non disegna se qualcosa
  non gli torna;
- dichiara KLID `0x0409` (US) e una **dimensione fisica assurda** — 1000 mm per 984 px, cioè 24 DPI.
  La dimensione fisica è dimostrabilmente falsa (mstsc, per confronto, ne dichiara una realistica:
  334 mm per 1080 px, 82 DPI). Il KLID non è verificato, ma su una tastiera software **non descrive
  nulla di reale** in ogni caso.

**Ancora da misurare:**

- se il problema «audio e grafica insieme» esiste davvero su RDM. Nota: `gnome-remote-desktop` **non**
  ha spento l'audio per RDM, perché la sua regola si attiva su `OsMajorType == ANDROID/IOS` e RDM si
  dichiara *«Unspecified platform»*;
- come si comporta con RemoteFX Progressive, che è ora il codec candidato per Android;
- **con quale client Android sono state fatte le misure di §5.4 e §5.7 di `SPECIFICA.md`** — resta la
  lacuna storica, ma pesa meno: quel che conta ora è come si comporta RDM, e lo stiamo misurando.
