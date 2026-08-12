# Fase 2 — Il primo fotogramma

Aperta il **12 agosto 2026** · ⏳ **In corso** — il banco esiste, il prodotto no

> Il modello di questo documento sta in [`../PIANO.md`](../PIANO.md) §0.2; le decisioni stanno in
> [`../DECISIONI.md`](../DECISIONI.md) e qui si **rimanda**, non si copia. ⛔ E si rimanda anche ai
> **sei rapporti di sotto-fase**: quel che sta lì non si ricopia qui, o le due copie divergono —
> è la lezione del 10 agosto, quando i `.md` erano stati chiusi due ore prima del codice.

---

## Che cosa deve produrre

Cattura da una sessione GNOME vera → codifica → filo → `VideoDecoder` → tela della pagina.
**Un'immagine ferma.**

**Che cosa vede e giudica l'utente**: il proprio desktop, dentro una scheda del browser. Fermo, ma
suo — e da qualunque dispositivo.

**Il banco**: il fotogramma decodificato confrontato con quello catturato. Non «il programma non è
crollato»: **i pixel**.

---

## Come è stata divisa, e perché

⭐ **Su richiesta dell'utente, il 12 agosto 2026**: la fase è stata tagliata in **sei sotto-fasi** e
ciascuna affidata a un agente, che ha lavorato in parallelo agli altri. Il taglio segue **gli anelli
della catena**, non delle fette arbitrarie: ogni sotto-fase possiede file suoi, una porta sua, e
consegna alle altre attraverso una sezione dichiarata — **le cuciture**.

Il mandato comune sta in [`rapporti/MANDATO-12-agosto-fase2.md`](rapporti/MANDATO-12-agosto-fase2.md).

| # | Sotto-fase | Rapporto | Banco | Porta |
|---|---|---|---|---|
| **F2.1** | La sessione GNOME headless | [`rapporti/F2-1-sessione.md`](rapporti/F2-1-sessione.md) | `banchi/02-sessione-*` | 7511 |
| **F2.2** | La cattura | [`rapporti/F2-2-cattura.md`](rapporti/F2-2-cattura.md) | `banchi/02-cattura-*` | 7512 |
| **F2.3** | La codifica HEVC in software | [`rapporti/F2-3-codifica.md`](rapporti/F2-3-codifica.md) | `banchi/02-codifica-*` | 7513 |
| **F2.4** | Il filo | [`rapporti/F2-4-filo.md`](rapporti/F2-4-filo.md) | `banchi/02-filo-*` | 7514 |
| **F2.5** | La pagina | [`rapporti/F2-5-pagina.md`](rapporti/F2-5-pagina.md) | `banchi/02-pagina-*` | 7515 |
| **F2.6** | Il giudizio | [`rapporti/F2-6-giudizio.md`](rapporti/F2-6-giudizio.md) | `banchi/02-giudizio-*` | 7516 |

⛔ **E questo giro non ha scritto una riga di prodotto**, per la regola di `PIANO.md` §0.4: il
revisore interviene **appena il banco esiste**, prima che il prodotto esista, perché *«un difetto nel
prodotto lo trova un banco buono; un difetto nel banco non lo trova niente, e avvelena ogni misura
successiva perché dà fiducia»*. `src/` è **intatto**.

---

## Il banco

⭐ **Sei banchi, e tutti e sei certificati nello stesso giro in cui sono nati** — la regola scritta
l'11 agosto 2026 (*chi scrive un banco lo certifica nello stesso giro, o il conto non cala mai*)
è stata rispettata sei volte su sei.

| | La certificazione, `[M]` 12 agosto 2026 |
|---|---|
| **F2.1** | sul ferro `sano 0 → guasto 1 (zero monitor) → risanato 0`, girato **due volte**, sessione fermata e riavviata sei volte · sulle scene registrate **9 su 9**, otto guasti ciascuno nel suo punto |
| **F2.2** | `sano 0 → quattro guasti 1 → risanato 0`, con la marca **pretesa** *e* quella **vietata**: il grigio deve dare *«scena non riconosciuta»* e ⛔ **mai** *«fotogramma nero»*, o il giudice sbaglia la diagnosi peggiore proprio dove serve |
| **F2.3** | **30 su 30** verde su CHUWI **e** dentro il contenitore di NIC-OS · sano → guasto → risanato su **due** organi, cinque esecuzioni, marca verificata **assente** nel giro sano |
| **F2.4** | **6 pezzi su 6** · il giudice **27 su 27** come previsto · `sano 0 → guasto 4/1/2/3 → risanato 0`, marca vista nel guasto e mai nel sano |
| **F2.5** | sano → **cinque** guasti → risanato, uscita 0. ⚠ Due dei cinque sono **nati certificando**: erano stati innestati e non facevano virare niente |
| **F2.6** | `sano 0 → dodici guasti su dodici con la marca giusta → risanato 0` |

### ⭐⭐ E la cosa che dice se il giro è valso la pena: **nove difetti trovati dentro i banchi, prima che il prodotto esista**

⛔ Non nel prodotto — **nei banchi appena scritti**, e tutti trovati *girando*, non rileggendo:

- **F2.2** — ⛔ **il suo banco è uscito VERDE col difetto vivo**, al primo giro: zero fotogrammi di
  regime, riga gialla, verdetto verde. La forma **E8**. Causa: la sessione aveva già `Meta-0`, il
  banco montava `Meta-1`, e la scena finiva sul primo. ⭐ Curato in tre punti, e **le due righe
  sbagliate restano nel registro** con accanto la nota che dice perché non valgono.
- **F2.6** — quattro: un controllo che correlava i canali su tutta l'immagine (R, G, B sono correlati
  a 0,978 ⇒ **rosso su catena sana**); uno che sottraeva 8 bit da 16 (−3,18 dB su catena perfetta);
  uno che innestava il guasto sull'imputato e **ri-scambiando i piani li rimetteva a posto**; e uno
  che aggregava `None` con `is not False` e **promuoveva** un giro senza riferimento.
- **F2.4** — due: il confronto della regola citata dava **rosso su quattro giudizi esatti**, e le
  marche di due guasti erano nomi che compaiono **anche nel giro sano**.
- **F2.5** — due, quelli «nati certificando».

⇒ Ciascuno di questi, se il prodotto fosse stato scritto prima, sarebbe diventato **un'accusa al
prodotto**. La fase 1 ne ha pagati tre di quel tipo.

---

## Che cosa è stato sviluppato

**Niente prodotto** — e non è un ritardo, è l'ordine (`PIANO.md` §0.4). Quel che esiste è il banco,
e con esso la **forma** che il prodotto dovrà avere: le decisioni qui sotto sono vincoli per chi
scriverà il codice.

---

## Le misure

### ⛔ 1. Il terreno era rotto da due giorni, e nessuno lo sapeva

`[M]` 12 agosto: la sessione GNOME viva su NIC-OS **dal 10 agosto** girava `--headless --no-x11`
**senza** `--virtual-monitor`. `GetCurrentState` → **zero monitor**, con `IsSessionRunning` true,
cinquanta nomi sul bus, Nautilus e Terminale accesi.

⇒ **Il guasto M9 di `gnome.md` §13 non è stato innestato: era già addosso alla macchina.** Una
cattura puntata lì avrebbe misurato **zero fotogrammi** cercandoli dentro PipeWire, e l'imputato
sarebbe stata la cattura.

- ⚠ **La sessione nera non è solo nera: è fragile.** `Shell.Screenshot` su zero monitor fa tentare a
  Mutter una texture 0×0; con `OnFailure=gnome-session-shutdown.target` **cade tutta la sessione**.
  `[M]`, provato involontariamente e dichiarato.
- ⛔ **La cura di oggi non sopravvive a un riavvio**: il drop-in vive in `$XDG_RUNTIME_DIR`. Si
  rimette con `bash banchi/02-sessione-lancia.sh sano`.
- ⛔ **E la cura vera è di prodotto**: `v1/remotix-c/src/sessione.c:671` è
  `if (tipo == COMPOSITORE_KWIN && …)` — sul ramo GNOME `larghezza` e `altezza` **entrano nella
  funzione e si perdono**. Che il monitor virtuale stia in `provision-server.sh` invece che nel
  programma è l'invariante **I7** violato.

### ⛔ 2. La sorgente dà OTTO bit — il desiderato dei 10 bit non passa di qui

`[M]` 12 agosto: **Mutter consegna solo BGRx/BGRA**, cioè 8 bit per canale. 1920×1080, stride 7680
**letto dal manifesto** e non calcolato, 8 294 400 byte, range non dichiarato da Mutter ma **misurato
0-255**, e **nessuna matrice** — i pixel sono RGB.

Il conto che lo dimostra, fatto **sulla sfumatura** della scena (⚠ sulle barre piatte i livelli sono
una ventina per costruzione, e direbbe «8 bit» su qualunque cosa): **255/256/255 livelli distinti,
multipli di 4 a 0,259/0,259/0,249**.

⇒ ⛔ **Main10 da questa strada significa otto bit promossi a dieci**, e l'etichetta continuerebbe a
dire *«10 bit»* per tutta la catena. Il desiderato di `SPECIFICHE.md` §3.1 **non è raggiungibile in
fase 2 per via MemFd**, e la `[?]` viva si sposta su **DMA-BUF**, che F2.2 dichiara **non provata**.

⭐ E la previsione era stata scritta prima: F2.3 aveva messo a verbale *«se la cattura dà 8 bit, tutta
la catena resta verde e l'etichetta dice Main10 lo stesso»* come rischio da misurare. F2.2 ha
risposto: **è una certezza, e l'imputato sono io.**

### ⛔⛔ 3. HEVC non arriva al pixel su Firefox, e su Chrome esiste solo con la GPU

`[M]` 12 agosto, F2.5 — **e la scena decide una delle due risposte**:

| | schermo vero `:10` (GPU) | Xvfb (senza GPU) |
|---|---|---|
| **Chrome 151** | ⭐ **HEVC arriva al pixel**, 8 celle su 8, Main **e** Main10, Annex-B **e** hvcC | ⛔ **zero**: ogni stringa HEVC rifiutata |
| **Firefox 140 ESR** | ⛔ **zero**, `NotSupportedError` | ⛔ **zero**, identico |

⭐ **VP9 dipinge 8 su 8 in tutti e quattro i casi**: il «no» è **di HEVC**, non del banco — il
controllo positivo c'era.

**La causa è misurata, non dedotta**: con `prefer-software` Chrome dice `Unsupported`, con
`prefer-hardware` dipinge ⇒ `[M]` **Chrome su Linux non ha un decodificatore HEVC software**. HEVC
esiste **solo via VA-API**, e senza GPU sparisce.

> ⭐ **Verificato una seconda volta, su un secondo strumento e sul browser vero dell'utente** — `[M]`
> 12 agosto, ricognizione fatta guidando il Chrome di CHUWI da fuori, con i due controlli:
>
> ```
> hev1.1.6.L93.B0 (Main)     no-preference SI · prefer-hardware SI · prefer-software  no
> hvc1.1.6.L93.B0 (Main)     no-preference SI · prefer-hardware SI · prefer-software  no
> hev1.2.4.L93.B0 (Main10)   no-preference SI · prefer-hardware SI · prefer-software  no
> vp09.00.10.08  (positivo)  SI · SI · SI
> avc1.42E01E    (positivo)  SI · SI · SI
> pippo.00.00    (negativo)  no · no · no
> ```
>
> ⇒ La firma è **esattamente** quella descritta da F2.5: HEVC cade **solo** su `prefer-software`,
> mentre VP9 e H.264 reggono tutte e tre le strade e il codec inventato è rifiutato da tutte e tre.
> ⚠ **E questa non è un banco**: è una ricognizione a mano, non lascia traccia su disco e non si
> rifà domani. Vale come **secondo testimone** della causa, non come misura della fase — e
> `isConfigSupported` resta la forma **E1** (*necessario scambiato per sufficiente*): dice che la
> configurazione è accettata, **non** che il pixel arriva. Quello lo dice il banco di F2.5.

### ⭐⭐ 4. E su Firefox tre testimoni concordi dicono il falso

`[M]`: `mediaCapabilities` risponde `supported / smooth / powerEfficient: true` e `canPlayType`
risponde *«probably»* per **tutte e sette** le stringhe HEVC — mentre `isConfigSupported` dice
**false** e il pixel **non arriva**.

⇒ ⛔ **Una pagina che scegliesse il codec da lì non dipingerebbe niente**, e nessuno dei tre testimoni
l'avrebbe avvertita. È una trappola di prodotto, non di banco.

### 5. Le altre misure, in breve

| | |
|---|---|
| ⭐ **il prefisso non conta** | `hev1.` **e** `hvc1.` vanno tutti e due in Annex-B puro `[M]`: Chromium decide dalla presenza della `description`, non dal prefisso. ⇒ la `[?]` che F2.3 aveva lasciato aperta **è chiusa** |
| ⛔ **il livello non lo controlla il browser** | Chrome accetta `L30` su un flusso di livello 3.0 e **dipinge 8 su 8** `[M]`. L'atteso del banco è stato **smentito**, col guasto verificato in vigore ⇒ **il controllo del livello deve stare dal lato server** |
| ⛔ **`ffmpeg` non rifiuta un flusso corrotto: lo conceala** | due storpiature su tre escono con stato **0** `[M]` ⇒ un giudizio sulla decodifica **non si prende mai dallo stato d'uscita**: si prende sui pixel |
| ⛔ **il codec non è un rivelatore di corruzione** | un byte girato nell'intestazione di uno slice ha lasciato il fotogramma **identico bit per bit** `[M]` — numero da avere in mano se qualcuno propone scorciatoie attorno alle garanzie di QUIC |
| ⚠ **x265 sceglie da sé** | `bframes=4` e `open-gop` di default, che nessuno ha chiesto: costano **un fotogramma di ritardo** contro un tetto di 50 ms. v1 li vietava a mano ⇒ si decide, non si eredita |
| ⭐ **`cattura.h` e `gnome.md` §8.1 si contraddicevano** | sul buffer riciclato. Misurato: danno **parziale** e le sette bande **intere** ⇒ ha ragione `gnome.md`, il commento nel codice è vecchio. ⛔ Se avesse avuto ragione `cattura.h`, la fase 2 avrebbe consegnato **mezzo desktop senza un errore** |
| ⛔ **la `[?]` del piano sull'ordine di `libei` è contraddetta** | `[M]`, riprodotta due volte: un client Wayland tenuto vivo *attraverso* la nascita del puntatore **riceve** `capabilities(0)` → `capabilities(1)`. La spiegazione *«non si iscrive mai»* **non regge**, e la caccia si sposta dal compositore al client. ⭐ E la regola vera è più stretta del piano: `ensure_virtual_device()` sta nei gestori di `NotifyPointerMotion*`, **non** in `Start()` — il puntatore nasce al **primo movimento iniettato**, la tastiera al **primo tasto** `[R]` |
| ⛔ **E2 preso sul campo** | sul server ci sono **due** monitor virtuali, `Meta-0`/`MetaVirtualMonitor` e `Meta-1`/`Virtual remote monitor`, **entrambi 1920×1080@60**: li distingue **il nome del prodotto**, non la misura. Sceglierne uno «per misura» o «per indice» è la forma E2 |

---

## Le decisioni prodotte

| | La decisione | Perché |
|---|---|---|
| ⭐ **D1 — Annex-B puro, e NESSUNA `description`** | il flusso sul filo è `[00 00 00 01] VPS · SPS · PPS · SEI · IDR` | quattro ragioni **lette**: è quel che `libavcodec` già produce (l'hvcC lo fa il muxer MP4, e sarebbe codice nostro da mantenere — `CODER.md` §4.1); in Chromium l'hvcC costa **un'allocazione e una copia per fotogramma** perché converte comunque ad Annex-B `[R]`; l'hvcC ha una trappola documentata sul profile-tier-level che fa **rifiutare** `isConfigSupported()`; tre progetti su tre fanno così. ⚠ **Il prezzo dichiarato**: WebKit fa la conversione inversa ⇒ si paga su Safari |
| ⭐ **D2 — il primo fotogramma è sempre chiave, coi parameter set dentro** | e ogni chiave si decodifica da sola | oggi `RCP.md` lascia **conforme** un delta in apertura, e il client **non ha modo di accorgersene**: nessun buco, nessun errore dal decodificatore ⇒ la fase 2 mostrerebbe spazzatura **senza che nessuno abbia torto** |
| ⭐ **D3 — il metro della fase è a due piani** | *piano 1*: `pagina ⟷ riferimento ffmpeg`, perdita ammessa **zero**, soglia **PSNR-Y ≥ 45 dB** — perché la decodifica HEVC è **normativa** · *piano 2*: `Δ = PSNR(pagina, cattura) − PSNR(riferimento, cattura) ≥ −0,5 dB` | il piano 2 è una **differenza**: il QP scelto da F2.3 si cancella, e **la soglia non invecchia** quando la codifica cambia. ⭐ E il riferimento `ffmpeg` è **il secondo lettore** che `PIANO.md` §0.4 dichiara mancante |
| ⛔ **D4 — il controllo del livello sta dal lato server** | non dal lato pagina | misurato: Chrome accetta un livello sbagliato e dipinge lo stesso |
| ⛔ **D5 — `codificatore.c` si riscrive, non si «riporta»** | ne sopravvive **la forma**, non le righe | 889 righe (la cifra del piano è giusta), ma **77 nominano H.264/AVC**, **47 nominano RDP/FreeRDP**, e *HEVC*, *265*, *10 bit* compaiono **zero volte**: è un codificatore H.264 AVC420 per RDP, quattro candidati tutti `h264_*`, tutti **NV12 a 8 bit**. Sopravvivono il giro dei tentativi, il divieto di ripiego silenzioso, il conto dei tempi, il divieto di `GLOBAL_HEADER` |

### ⚠ E una correzione a una misura della fase 1

⛔ **La prova dei 10 bit «contando le bande»** — sonda **S2**, `web/` §3.7 punto 2 — **non
sopravvive alla codifica con perdita**: `[M]` rapporto **4,13** prima, **1,31** dopo QP 20.
⭐ Sostituita dai **due bit bassi del piano Y sulle zone sfumate**, che convergono con la misura
indipendente di F2.3 (**0,25** su catena sana contro **1,000** su un flusso troncato a 8 bit).
⚠ E la firma dei «multipli di 4» **non sopravvive alla conversione RGB→YUV**: i bit veri si misurano
**alla sorgente**, o non si misurano.

---

## ⛔ Che cosa NON ha funzionato

- ⛔ **La sessione del server è caduta**, chiamando `Shell.Screenshot` su zero monitor. Rimessa in
  due minuti; **7448 e 7501 verificate intatte** prima e dopo (girano nel contenitore). ⭐ Da lì è
  uscita la scoperta che la sessione nera è **fragile**, che vale più del disturbo.
- ⛔ **Un banco verde col difetto vivo** (F2.2, sopra). La forma E8, dentro un banco appena scritto.
- ⛔ **Nove difetti di banco** trovati girando (elenco sopra).
- ⚠ **In Chrome headless `VideoEncoder.flush()` non ritorna.** Aggirato con una finestra vera,
  ⛔ **non capito**: resta `[?]`, e chi lo riusa altrove deve saperlo.
- ⚠ **`misura-cattura.c` stampa nella riga di esito la misura CHIESTA, non quella negoziata** — la
  voce 12-bis fu curata in `misura-wlroots` e **non lì**. Rilievo `[R]` **lasciato aperto e non
  toccato**: non è di questa fase, ed è lo strumento che certifica gli altri banchi.

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⛔ **i 10 bit veri** | non passano da MemFd/BGRx `[M]`. Restano possibili **solo** per via **DMA-BUF**, **non provata** |
| ⛔ **il telefono** | hardware e 10 bit: **nessun numero prodotto, e nessuno dedotto**. Serve il dispositivo (vedi sotto) |
| ⛔ **il buffer della scheda sbagliata** | il banco della cattura **non lo vedrebbe**, e il suo verde **non lo assolve**. La macchina ha due GPU |
| ⚠ **che un fotogramma arrivi davvero sul filo** | il primo giro del cliente di prova sulla 7514 **è** la prima misura vera della fase |
| ⚠ **`VideoEncoder.flush()` in headless** | aggirato, non capito |
| ⚠ **le soglie M1b e M3 del metro** | **calcolate**, non tarate sul campo |
| ⚠ **Safari, e Chrome per Android/DeX** | manca il dispositivo |
| ⚠ **Firefox con `media.hevc.enabled`** | **non provato di proposito**: si misura il browser che l'utente ha, non quello che potrebbe configurare |

---

## Che cosa aspetta l'utente

### ⚖️ 1. Una decisione: HEVC esclude Firefox, e su Linux esclude chi non ha la GPU

Il progetto promette *«nessun client da installare — basta un browser moderno»*. Misurato oggi, con
HEVC quella frase vale per **Chrome con una GPU che porta VA-API**. Firefox non dipinge, e Chrome
senza GPU nemmeno. ⛔ **E la difesa dei tre motori indipendenti** — quella che `DECISIONI.md` §1.6
comprava al posto dell'arbitro perduto — **su HEVC non c'è**.

### ⚖️ 2. La sonda del telefono, che non si fa da soli

*Un telefono **Android** con **Chrome ≥ 108** — non il portatile — sulla stessa WiFi, con un cavo
USB e il debug acceso per `chrome://inspect`. Si apre l'indirizzo stampato da
`bash banchi/02-giudizio-telefono.sh serve`, si accetta l'avviso del certificato **una volta**, si
premono i bottoni 1 e 2 tenendo schermo acceso e scheda in primo piano: **~10 minuti**, più 10 di
fila per il decadimento quando le sequenze di F2.3 ci sono.*

⛔ **Non gli si chiede se «si vede bene»: la sonda produce numeri.**

### ⛔ 3. E un debito della fase 1 che questa fase NON può scavalcare

⚠ *Il `README.md` elenca fra «quel che aspetta l'utente» i due ripieghi — il filo unico e il tetto
delle sessioni. **Quella riga è scaduta**: tutt'e due sono state decise dall'utente la sera dell'11
agosto, e stanno in `DECISIONI.md` §1.10 e §1.11. Corretto il 12 agosto 2026.*

⛔ **E `DECISIONI.md` §1.10 impone una cosa a questa fase**: la verifica PAM esce dal filo unico
**prima che la fase 2 si apra**, con un **processo aiutante** e non con un filo — perché PAM non è
affidabilmente rientrante.

La ragione è scritta lì, ed è del video: *«finché non c'è video il sintomo è «l'ultimo dei dieci
aspetta dieci secondi», sgradevole e circoscritto; dalla fase 2 in poi lo schermo di **tutti** quelli
collegati si pianta per uno o due secondi ogni volta che **qualcun altro** entra — e chi lo vedrà lo
attribuirà al **video**»*. `[M]` da B8: **da 1,0 a 2,2 secondi** per tentativo, e il ritardo lo mette
`pam_faildelay`, non il nostro codice.

⇒ ⭐ **Il banco di questa fase poteva nascere prima della cura — il prodotto no.** Questo giro ha
scritto solo banchi, quindi il debito non è stato violato; ⛔ **ma la prima riga di prodotto della
fase 2 viene dopo quella cura**, o si misura il video con dentro un difetto che si attribuirà al
video.

### ⏳ 4. Il tetto delle sessioni resta 16, e il prezzo è dichiarato

`DECISIONI.md` §1.11: non si cambia fino alla fase 3, perché *«il limite vero non è un conteggio: è
un budget di pixel al secondo, e lo pone il codificatore»*. ⚠ Per due fasi **il codice dice 16 e la
specifica dice 10**.

---

## Il giudizio dell'utente

⏳ **Non ancora dato**: la fase è aperta e il prodotto non esiste. Quel che si giudica alla fine è
*il proprio desktop dentro una scheda del browser* — e finché non c'è quello, non c'è niente da
giudicare.
