# Fase 2 — Il primo fotogramma

Aperta il **12 agosto 2026** · ⭐⭐⭐ **CHIUSA il 13 agosto 2026, sul giudizio dell'utente** — la
catena consegna, e l'utente ha guardato il proprio desktop dentro una scheda del browser.
⭐ La provenienza sta in [`rapporti/GIUDIZIO-13-agosto.md`](rapporti/GIUDIZIO-13-agosto.md): la scena,
il registro del server verbatim, le impronte, e ⭐ **la misura fatta sui pixel dello scatto**.

> ⚠ *Questa riga diceva «il banco esiste, il prodotto no», e con lei altri tre punti del documento
> (§«Come è stata divisa», §«Che cosa è stato sviluppato», §«Il giudizio dell'utente»). Erano vere
> del **giro del 12 agosto mattina** e sono rimaste addosso al documento mentre il prodotto nasceva
> la sera stessa. ⛔ **È la causa di processo di R12-C alla terza occorrenza**: il documento è stato
> chiuso alle **08:36** del 13 agosto e il codice è arrivato fino alle **09:55** — quattro commit
> più tardi. Corretto il 13 agosto 2026 a codice fermo, revisione **R13**, rilievi 1 e 2.*

> Il modello di questo documento sta in [`../PIANO.md`](../PIANO.md) §0.2; le decisioni stanno in
> [`../DECISIONI.md`](../DECISIONI.md) e qui si **rimanda**, non si copia. ⛔ E si rimanda anche ai
> **sei rapporti di sotto-fase e ai sette del prodotto**: quel che sta lì non si ricopia qui, o le
> due copie divergono — è la lezione del 10 agosto, quando i `.md` erano stati chiusi due ore prima
> del codice.

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

⛔ **E il giro del 12 agosto MATTINA non ha scritto una riga di prodotto**, per la regola di
`PIANO.md` §0.4: il revisore interviene **appena il banco esiste**, prima che il prodotto esista,
perché *«un difetto nel prodotto lo trova un banco buono; un difetto nel banco non lo trova niente,
e avvelena ogni misura successiva perché dà fiducia»*. In quel momento `src/` era **intatto**.

⭐ **Il prodotto è arrivato la sera dello stesso giorno**, con lo stesso taglio ad anelli e un
rapporto per ciascuno — ⛔ e questa tavola non li nominava, così che chi riprendeva leggendo questo
documento **non sapeva che esistessero** (revisione **R13**, rilievo 1; è il danno di R12C.1, dove
*«chi riprendeva il lavoro leggeva quella riga e riscriveva da zero un server che esiste»*):

| # | Il prodotto dell'anello | Rapporto |
|---|---|---|
| **P2.1** | la sessione GNOME | [`rapporti/P2-1-sessione.md`](rapporti/P2-1-sessione.md) |
| **P2.2** | la cattura | [`rapporti/P2-2-cattura.md`](rapporti/P2-2-cattura.md) |
| **P2.3** | la codifica, HEVC **e** AV1 in software | [`rapporti/P2-3-codifica.md`](rapporti/P2-3-codifica.md) |
| **P2.4** | il canale video, dentro `rcp.c` | [`rapporti/P2-4-filo.md`](rapporti/P2-4-filo.md) |
| **P2.5** | la pagina che dipinge il fotogramma | [`rapporti/P2-5-pagina.md`](rapporti/P2-5-pagina.md) |
| **P2.6** | il montaggio: i cinque anelli messi insieme | [`rapporti/P2-6-montaggio.md`](rapporti/P2-6-montaggio.md) |
| **P2.7** | il figlio per utente (`DECISIONI.md` §1.10-bis) | [`rapporti/P2-7-figlio.md`](rapporti/P2-7-figlio.md) |

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

**Il 12 agosto mattina, niente prodotto** — e non era un ritardo, era l'ordine (`PIANO.md` §0.4).
Quel che esisteva era il banco, e con esso la **forma** che il prodotto avrebbe dovuto avere: le
decisioni qui sotto erano vincoli per chi avrebbe scritto il codice.

⭐ **Il prodotto è stato scritto la sera del 12 e la mattina del 13**, e sta in `src/` — la sessione,
la cattura, le due codifiche, il canale video dentro `rcp.c`, la pagina che dipinge, il montaggio e
il figlio per utente. I sette rapporti sono nella tavola `P2.1` … `P2.7` qui sopra, e **quel che sta
lì non si ricopia qui**.

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
- ⛔⛔ **E un difetto del COORDINAMENTO, che è mio.** La regola *«ogni agente possiede file suoi, e
  non tocca quelli degli altri»* — scritta per impedire che sei agenti si sovrascrivessero — ha
  prodotto questo: l'agente degli arbitri ha **fatto e riferito cinque ricertificazioni**, e
  **nessuna ha scritto una riga nel registro**, perché il registro apparteneva a un altro agente.
  ⇒ Per ore il conto ha detto *«B9 scaduta»* mentre B9 era stato rigirato **quattro volte**.
  ⚠ È la stessa forma che questa giornata ha inseguito tutto il tempo — ***«fatto» e «scritto dove
  qualcuno lo legge» sono due cose diverse*** — applicata al registro invece che al filo.
  ⭐ **La regola che ne esce**: *chi è autorizzato a certificare deve essere autorizzato a scrivere
  la riga della certificazione*. Un permesso a metà produce lavoro che non esiste per nessuno.
- ⚠ **`misura-cattura.c` stampa nella riga di esito la misura CHIESTA, non quella negoziata** — la
  voce 12-bis fu curata in `misura-wlroots` e **non lì**. Rilievo `[R]` **lasciato aperto e non
  toccato**: non è di questa fase, ed è lo strumento che certifica gli altri banchi.

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⛔ **i 10 bit veri** | ⇒ **`DECISIONI.md` §2.3-ter, e non è più una `[?]`**: non escono da Mutter per **nessuna** strada — né MemFd né DMA-BUF, e i formati a 10 bit chiesti **per nome** danno `no more input formats` su tutt'e due, col controllo positivo accanto. ⚠ *Questa riga diceva «restano possibili solo per via DMA-BUF, non provata»: era una **copia invecchiata di una decisione**, cioè proprio quel che il riquadro in testa promette di non fare, e teneva aperta una speranza che una misura aveva chiuso (R13.5b)* |
| ⚠ **il telefono, e la `[?]` adesso è più stretta** | `[M]` **13 agosto 2026**, telefono vero — **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte**, HEVC Main10 **e** AV1 10 bit. ⛔ **Ma `copyTo` dà `format` `RGBA` e 4 byte per pixel**: al capo del dispositivo i dieci bit sono **otto promossi**, come alla sorgente. ⛔ **E resta aperto l'hardware**: senza cavo dati non si legge `Created MediaCodec <nome>`, quindi *«lo decodifica il silicio o la CPU?»* non ha risposta — e il criterio A/B esce `valido: false`, perché misura **spesa fissa**. ⚠ *Questa riga diceva «nessun numero prodotto, e nessuno dedotto», e i numeri stanno in `banchi/02-giudizio-sonda.jsonl` dalle 07:53 del 13 (R13.5a)* |
| ⛔ **il buffer della scheda sbagliata** | il banco della cattura **non lo vedrebbe**, e il suo verde **non lo assolve**. La macchina ha due GPU |
| ✅ **che un fotogramma arrivi davvero sul filo** | ⭐ **chiusa il 13 agosto**: l'utente l'ha guardato, e il registro del server lo scrive — `fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte, FIN` |
| ⛔ **M5 — lo scarto di crominanza fra due decodificatori** | 0,9791 contro un limite di 0,98: è **l'unico rosso rimasto su catena sana** — M0 e M1 erano rossi ai giri delle 09:19-09:20, prima della cura del riscalamento. ⛔ **Non si riproduce sulla mira**, e **la soglia non è stata allargata**: il rosso non è stato curato, **è sparito quando è cambiata la scena** |
| ⛔ **P15** | `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto della fase dove un orologio decide**. Sta per esteso in [`rapporti/F2-4-filo.md`](rapporti/F2-4-filo.md) |
| ⛔⛔ **«due utenti con due sessioni vere, ciascuno vede LA PROPRIA»** | ⛔ **non lo copre nessun banco**, ed è il buco più grande della fase. `[M]` 13 agosto: il caso `senza-palco` di `02-figlio-prova.py` prova **la metà negativa** — `prova` (uid 1001, tutti e quattro i campi chiesti al nucleo) **non** vede il desktop di `nicfio`, e il cliente RCP indipendente conta **zero** fotogrammi dove il 12 agosto ne contava uno conforme. ⛔ **Ma la metà positiva no**: su quella macchina `prova` non ha mai fatto login — niente `/run/user/1001`, niente bus, niente palco — quindi **un prodotto che non consegnasse niente a nessuno passerebbe allo stesso modo**. La metà positiva regge oggi **solo per uid 1000**. ⚠ Guardati e scartati: `01-b10-secondo-utente.py`, `attrezzi-prova2.sh`, `02-pam-i3.py --caso secondo` si fermano tutti **all'autenticazione**, non al vedere |
| ⚠ **`02-figlio-accendi.sh:165` conta i figli di tutti** | `pgrep -f -- "--figlio-interno" \| wc -l` non guarda **di chi** sono: allo spegnimento ha accusato due orfani che erano figli vivi di padri vivi (la 7693 di un altro banco e ⛔ **la 7561 dell'utente**). È la stessa forma che il file **vieta trenta righe più su** per l'azione `stato`. ⚠ Non cura, non ferma nessuno (`spegni` esce 0 lo stesso) — si accende solo quando due banchi girano in parallelo, e il 12 agosto infatti taceva |
| ⛔ **la risoluzione del desktop, `1920×1080`** | ⛔ **ereditata dalla scena di un banco, senza decisione né misura** — `grep 1920 DECISIONI.md` non trova nessuna decisione che la fissi, e in v1 era **2560×1080**. ⚠ È la tela che l'utente vedrà: `LEZIONI.md` §2.3-quater la vuole scritta come **provvisoria**, ed è quel che questa riga fa |
| ⚠ **`VideoEncoder.flush()` in headless** | aggirato, non capito |
| ⚠ **le soglie M1b e M3 del metro** | **calcolate**, non tarate sul campo |
| ⚠ **Safari, e Chrome per Android/DeX** | manca il dispositivo |
| ⚠ **Firefox con `media.hevc.enabled`** | **non provato di proposito**: si misura il browser che l'utente ha, non quello che potrebbe configurare |

---

## Che cosa aspetta l'utente

### ✅ 1. ~~Una decisione: HEVC esclude Firefox~~ — **decisa e chiusa il 12 agosto**

Il progetto promette *«nessun client da installare — basta un browser moderno»*, e con HEVC quella
frase valeva per **Chrome con una GPU che porta VA-API**: Firefox non dipinge, e Chrome senza GPU
nemmeno. ⛔ La difesa dei tre motori indipendenti — quella che `DECISIONI.md` §1.6 comprava al posto
dell'arbitro perduto — **su HEVC non c'era**.

✅ **L'utente ha deciso: `DECISIONI.md` §1.13** — HEVC **con un ripiego negoziato**, non un requisito
dichiarato, perché `CODER.md` §4.2 impone che ogni dipendenza mancante abbia un ripiego e che il
ripiego **si dichiari**.

🔸 **E il secondo codec è AV1**, chiuso lo stesso giorno **su una misura** e non su una preferenza:
`[M]` **quattro caselle su quattro** — i due motori, con GPU e senza — a **8 e a 10 bit**, e ⛔ **con
`prefer-software`**, cioè senza dipendere dalla GPU. ⭐ AV1 riempie **esattamente** le tre caselle che
HEVC lascia vuote, e ⭐⭐ i 10 bit su Chrome diventano per la prima volta **osservabili**
(`VideoFrame.format` = `I420P10`, massimo del luma **870** — impossibile a 8 bit).

⭐ **E non costa una riga di protocollo**: `av1` era già fra i valori ammessi di `RCP.md` §4.3 e aveva
già `codec = 2` in §6.2 ⇒ **§9 non viene sfiorata**. ⛔ *VP9, che pure era misurato funzionare,
sarebbe costato **RCP/2**: in §4.3 compare come l'esempio di valore che RCP/1 deve **ignorare**.*

⛔ **L'ordine di preferenza non si rovescia**: resta `hevc,av1`. HEVC è ancora il primo, perché è
quello che il telefono decodifica in hardware — ed è la domanda **S2**, ancora aperta.

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

---

## ⭐ LA SERA DEL 12 AGOSTO — il cancello si apre, e l'arbitro si corregge sei volte

*Su richiesta dell'utente — «fai una lista dei bug, assegna un agente a ciascuno, e arriva al
completamento della fase 2» — sono stati aperti **dodici difetti** (`rapporti/DIFETTI-12-agosto.md`)
e affidati a un agente ciascuno, in ondate che non si pestassero i piedi.*

### ⭐⭐ Il cancello della fase 2 è aperto: `DECISIONI.md` §1.10 è applicata e misurata

La verifica PAM esce dal filo unico, **con un processo aiutante** — tre piani: il server scrive su un
`socketpair` SEQPACKET e torna al `poll`; uno **smistatore** che non chiama mai PAM legge e forca; un
**nipote** fa **una sola** transazione PAM e muore. ⇒ La rientranza di PAM non è *«gestita»*: **non è
in gioco**.

| | `[M]` 12 agosto 2026, cinque giri per lato |
|---|---|
| ⭐⭐ **chi NON si autentica** | picco **2259 → 3 ms** |
| ⭐ **la stretta di mano di chi arriva in quel momento** | **2262 → 10 ms** |
| ⚠ **chi si autentica** | 2260 → 1844 ms, cioè **invariato** — e deve restarlo: quel tempo lo mette PAM |

⛔ **E il fallimento è un no, non un forse** (I3): il `true` nasce in **un punto solo del programma**,
e sette strade portano a un no. Provato ammazzando l'aiutante con `SIGKILL` e presentando la parola
**giusta** → `RESPINTO` in 1001 ms, col controllo positivo accanto.

⭐ **E il filo NON è cambiato**: B3 `0→2→0` e B5 `0→1→0` danno gli **stessi identici numeri** di
prima della cura. L'ipotesi di chi l'ha scritta è diventata una misura.

### ⛔ Il prodotto sul server non era il prodotto che avevamo scritto

`[M]`: **10 file su 24 diversi**, e i due che mancavano **del tutto** erano i due nuovi
(`aiutante.c`, `aiutante.h`); il binario girava dall'11 agosto con `exe` marcato `(deleted)`.

⭐ **E la cura non è la copia: è l'attrezzo che mancava** — `banchi/attrezzi-allinea-prodotto.sh`,
che **enumera l'albero intero** invece di un elenco scritto a mano. È esattamente la lezione del
difetto: *i due file che mancavano sono quelli che un elenco a mano non avrebbe mai avuto*. E non si
ferma ai sorgenti: ⛔ **sorgenti allineati e binario nuovo non bastano finché il processo vivo è
l'altro**.

### ⛔⛔ E l'arbitro si è corretto sei volte in una sera

Le sette righe di F2.4 sono entrate in `RCP.md`; ⛔ **due erano sbagliate**, e le due cure che le
sistemavano ne hanno generate altre quattro. La successione **P8 → P11 → P13 → P14** e la lezione che
ne esce stanno in **`LEZIONI.md` §1.13**, ed è la cosa più riusabile prodotta oggi:

> ⭐ *Una tolleranza si scrive sulla **grandezza vera del fenomeno**, o si sposta di un passo a ogni
> rilettura.* La risposta esatta stava dentro i 28 byte dell'intestazione da tre giorni — il campo
> `numero` — e le prime tre stesure hanno usato una **grandezza sostitutiva**: una misura, un tempo,
> un evento.

⚠ **E chi le ha trovate, tutte e quattro: non chi rileggeva il documento, ma chi doveva far
rispettare la regola** scrivendo l'arbitro che la giudica.

### Il conto dei banchi, la sera del 12 agosto

```
banchi nel catalogo: 15   (P5R e' entrato: il guasto che toglie il RITIRO, non il valore)
13  certificati e valgono oggi
 0  non riverificabili        ⭐ la riga di P5R adesso porta le impronte
```

⚠ **E il numero è sceso e risalito sei volte in una sera**, sempre per la stessa ragione dichiarata:
curare il prodotto o l'arbitro **fa scadere le certificazioni che li guardavano**. ⛔ *«Scaduta» non
è «fallita»*, e non è nemmeno «pulita».

### ⭐ Gli attrezzi nuovi, e servono al prossimo giro

- **`attrezzi-allinea-prodotto.sh`** — quel che il `README` dichiarava mancante da ieri.
- **`02-sessione-guardia.sh`** — si mette **davanti** a una misura e fa le **due domande separate**:
  *«è viva?»* e *«ha un monitor?»*. Con tre bande d'uscita, così un **rifiuto** non si confonde con
  un fallimento del comando.
- ⭐⭐ **il controllo positivo dell'àncora** (in `01-b8-cronometro.py`, riusato in
  `01-b10-secondo-utente.py`) — allunga la riga di registro nei modi già successi e pretende che
  l'esito **non cambi**. ⛔ Nato perché **un'àncora fragile passa tutti i guasti**: rompersi *fa*
  diventare rossi, quindi nessuno dei quindici guasti la smascherava.
- **`01-b12-lancia.sh`** prende `B12_BERSAGLIO=innesto|prodotto`, e ⛔ **la scena finisce in ogni
  riga del registro**: chi non la dichiara ottiene *«non dichiarata»*, mai «innesto».

---

## ⭐⭐⭐ L'UTENTE HA VISTO IL PROPRIO DESKTOP — 13 agosto 2026, mattina

*Non è il giudizio di fase: è il fatto che la catena consegna. Si scrive qui perché è la prima volta
che un essere umano guarda l'uscita di questo prodotto, e perché fin qui tutto quel che ne sapevamo
erano decibel.*

> **«È lo sfondo GNOME, è OK.»** — l'utente, davanti a `https://192.168.0.2:7561/`, entrato come sé
> stesso.

⭐ Cattura → codifica → filo → `VideoDecoder` → pixel sullo schermo di una persona, con in mezzo un
protocollo scritto da zero. Il registro del server, dalla stessa sessione:

```
il client dichiara video.misura_massima=3840x2160   ← MISURATA decodificando, non dedotta dallo schermo
sessione aperta utente=nicfio  tela=1920x1080  vista=2559x922
fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte, FIN — spediti 1, abbandonati 0
```

⚠ **E si scrive che cosa questo NON è**: non è il giudizio della fase, e la fase resta aperta.

⚠ *Questo riquadro, chiuso alle **08:36**, proseguiva così: «L'immagine è **piccola** — la pagina non
riscala alla vista, che §6.1 le impone — e il metro a pixel sulla catena vera non è stato girato».
⛔ **Tutt'e due le metà sono morte nell'ora e venti che è seguita**, e il documento è rimasto indietro
di quattro commit (R13.2):*

- ⭐ *il riscalamento è **in servizio** dalle **08:56** (`dc2f6a9`): due grandezze si chiamavano
  tutt'e due «larghezza della tela». E il rimando era **rotto** — `RCP.md` §6.1 è «Sui canali
  affidabili» e non nomina né vista né riscalamento; la sezione giusta è **`SPECIFICHE.md` §6.1**,
  ed è la terza volta in due fasi che un `§x.y` manda altrove (R13.8);*
- ⭐ *il metro a pixel **ha girato sulla catena vera** alle **09:50** — e quel che dice, per intero e
  senza arrotondarlo, sta nella sezione qui sotto.*

### ⛔ E i tre difetti che l'utente ha trovato in una mattina, che 518 file di banco non avevano preso

| | Che cosa ha visto | Perché il banco non lo vedeva |
|---|---|---|
| **1** | ⛔ entrando come `prova` vedeva il desktop di **`nicfio`** | il deposito dei fotogrammi era **di processo**, non di sessione — e nessun banco entrava con **due** utenti diversi sullo stesso server |
| **2** | ⛔ **pagina vuota**, nessuna spiegazione | la pagina dichiarava `video.misura_massima` dalla **misura dello schermo** invece che da quel che sa decodificare ⇒ tela concessa più piccola della cattura, e il prodotto **si rifiutava di spedire**. ⚠ Le pagine di prova dichiaravano un tetto comodo: **solo la pagina del prodotto, su uno schermo vero, sbagliava** |
| **3** | ⚠ l'immagine è **piccola** | i banchi guardano **se** i pixel arrivano, non **quanto grandi** sono dipinti |

⇒ ⭐ **È l'invariante I8 in azione** — *il metro è quel che l'utente vede, non il numero che esce dal
banco*. Quella notte i banchi dicevano **48,27 dB**; l'utente ha detto *«non vedo nessun desktop»*, e
aveva ragione lui.

---

---

## ⭐ Il metro ha girato sulla catena vera — e che cosa dice, per intero

`[M]` **13 agosto 2026**. I quattro ingressi messi insieme per la prima volta: la **cattura** (il
buffer BGRx che il prodotto ha scritto con `--rilievo`), il **flusso** che il prodotto ha spedito, il
**riferimento** (lo stesso flusso decodificato da `ffmpeg` — ⭐ il *secondo lettore* che `PIANO.md`
§0.4 dichiarava mancante) e la **pagina** (`getImageData` dalla tela, in un browser vero collegato al
server vero).

| la scena | l'esito | PSNR-Y | strumenti vivi |
|---|---|---|---|
| ⭐ **la mira di F2.6 a sfondo del desktop** | **PROMOSSO** | **62,09 dB** (soglia 45) | **12 su 12**, zero ciechi |
| ⛔ **il desktop naturale dell'utente** | **BOCCIATO su M5** | 58,62 dB | 8 su 12 — ciechi *precedente · otto-bit · piani · ribaltato* |

⛔ **E le due righe non si scelgono: si leggono insieme.** Il verde è del metro **con la mira**; sul
desktop nudo il metro vede meno — senza i marcatori, M4, M7 e M-V si spengono per costruzione — e
trova un rosso. ⚠ Il rosso di M5 **non è stato curato: è sparito quando è cambiata la scena**, e
resta `[?]`.

### ⛔ E uno dei dodici era verde per costruzione

Trovato da una **revisione avversariale** il 13 agosto, mandata a *refutare* la frase invece che a
confermarla. M8 leggeva un contatore `reset` che la pagina del prodotto chiama **`azzerati`**: valeva
sempre zero, e con lui due costanti scritte a mano. ⇒ **erano 11 vivi più un verde vuoto.**

⭐ Curato, **e la cura di una parola era sbagliata**: `azzerati > 0` è *il prodotto che si comporta
bene*, quindi leggerlo lì avrebbe prodotto un **falso rosso**. La grandezza vera è l'invariante
**`consegnati > completi`**. La storia intera, col controllo del falso rosso e con quel che la
certificazione **non** dice, sta in [`rapporti/F2-6-giudizio.md`](rapporti/F2-6-giudizio.md) — qui non
si ricopia.

### ⛔ Il punto cieco che non è del metro: **a monte della cattura**

Il fondo di verità del metro è **il buffer che il prodotto stesso ha catturato**. ⇒ Quale monitor,
quale sessione, **quale utente** sono fuori dalla sua portata: se il prodotto catturasse il desktop
di un altro utente, cattura, flusso, riferimento e pagina sarebbero **tutti d'accordo**, e il metro
direbbe **62 dB e promosso**.

⛔ **Ed è il difetto numero 1 che l'utente ha trovato in una mattina.** Lo copre un altro banco,
`02-figlio-prova.py` — rigirato il 13 agosto sul prodotto di oggi, **9 misure, 9 uscite 0, nessuna
uscita 2** — ⛔ ma solo per **metà**: vedi la tavola «Che cosa resta `[?]`».

---

## ⛔ Che cosa va detto insieme al verde, o il giudizio è preso su metà quadro

*Scritta il 13 agosto 2026, revisione **R13** rilievo 9. ⛔ Queste tre cose vivevano solo in un
riquadro del `README`, e chi leggeva **questo** documento — che il `README` gli dice di leggere per
primo — ne trovava una e mezza, e sbagliata.*

### 1. Il **piano 2** del metro non è applicabile: la catena intera non è stata giudicata

Il metro ha due piani (`banchi/02-giudizio-metro.py:46,56`): **piano 1** confronta *pagina ⟷
riferimento* — il browser contro `ffmpeg` **sullo stesso flusso**, cioè due decodificatori
indipendenti; **piano 2** confronta *pagina ⟷ cattura*, che è la catena intera.

⛔ **Il numero che il verde porta è del piano 1.** Il piano 2 il metro lo dichiara **non
applicabile**, e la ragione è aritmetica: perché la sottrazione misuri il client e non la tela, la
perdita del codificatore deve stare **10 dB sotto** il rumore della tela a 8 bit, e qui ne sta
**7,01** (55,08 contro 62,09). Il numero grezzo esiste — **54,11 dB** — ma non è un giudizio.

> ⚠ **E si dichiara un difetto dello strumento**: il messaggio che finisce nel file di esiti dice
> *«non è almeno **6 dB** sotto la prima»* mentre il codice usa **10** (`02-giudizio-metro.py:610`).
> La soglia vera è quella del codice; il messaggio è rimasto alla prima stesura.

### 2. I dieci bit sono **otto promossi**, e lo sono **a tutt'e due i capi**

- **alla sorgente**: ⇒ `DECISIONI.md` §2.3-ter — non escono da Mutter per **nessuna** strada, né
  MemFd né DMA-BUF, e i formati a 10 bit chiesti per nome danno `no more input formats`;
- **al dispositivo**: `[M]` 13 agosto sul telefono vero — `VideoFrame.format` è **`RGBA`** e `copyTo`
  dà **4 byte per pixel**, su una sequenza dichiarata `hev1.2.4.L90.90`, profondità 10.

⇒ ⛔ **L'etichetta `Main10` continuerebbe a dirlo per tutta la catena senza che nessuno se ne
accorga**: l'immagine viene bene lo stesso. Non è un ripiego nostro, ed è per questo che si scrive.

### 3. Il telefono **è stato misurato**, ma non sull'hardware

`[M]` 13 agosto, **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte** — HEVC
Main10 **e** AV1 10 bit, `tela_rileggibile: true`.

⛔ **Quel che non ha risposta è «lo decodifica il silicio o la CPU?»**: nel browser il nome del
decodificatore non c'è, senza cavo dati non si legge `Created MediaCodec <nome>` da
`chrome://media-internals`, e il criterio A/B esce **`valido: false`** perché misura *spesa fissa*.
⇒ `[?]` dichiarata — ed è la misura **S2** che `PIANO.md` §1.2 mette in questa fase.

---

## ⭐⭐⭐ Il giudizio dell'utente — **dato il 13 agosto 2026, e la fase è chiusa**

L'utente ha riaperto `https://192.168.0.2:7561/` **come sé stesso** dopo la cura del riscalamento, ha
consegnato lo scatto come risultato, e — messe davanti le **sette cose dichiarate aperte** — ha deciso
di **chiudere la fase adesso**, con quelle scritte come aperte.

⭐ **E questa volta il giudizio non è solo una frase**: lo scatto è stato letto **pixel per pixel**, e
il numero si confronta con quel che il server dichiara.

| dal registro del server, `08:45:44 UTC` | dai pixel dello scatto, otto secondi dopo |
|---|---|
| `vista=2545x927` | la zona dipinta è alta **927 px** ⭐ **identico** |
| `tela=1920x1080` | larga **1648 px**, rapporto **1,7778** contro un 16:9 di **1,7778** |

⇒ ⭐⭐ **La pagina riscala alla vista rispettando la proporzione, e non di un pixel storta** — è
`SPECIFICHE.md` §6.1 misurata **sul vetro**, non dichiarata. Le bande nere (448 a sinistra, 464 a
destra) sono la conseguenza aritmetica di una finestra 2,74 che ospita una tela 16:9: l'alternativa
sarebbe **stirare**, che §6.1 vieta.

⛔ **E lo scatto ha sollevato una cosa che nessun banco aveva visto**: la tela viene dipinta all'**86%**
su un monitor largo **2560**. Non è un difetto del riscalamento — è la `[?]` sulla risoluzione, e
**912 px di nero** sono il suo prezzo, misurato.

⚠ *Si scrive quel che è successo e non una frase che non è stata detta: il verdetto dell'11 agosto
era una **citazione**, questo è una **decisione presa davanti a un elenco**. Le due cose hanno lo
stesso valore e non la stessa forma.* ⇒
[`rapporti/GIUDIZIO-13-agosto.md`](rapporti/GIUDIZIO-13-agosto.md).
