# F2.3 — La codifica HEVC in software

*Sotto-fase della fase 2 «Il primo fotogramma». Aperta e chiusa il 12 agosto 2026.*
*Mandato: `fasi/rapporti/MANDATO-12-agosto-fase2.md`. Porta assegnata: **7513** — ⛔ **non usata**,
e §7 dice perché.*

⛔ **Questo giro non ha scritto prodotto.** `src/` non è stato toccato. Quel che segue è **il banco
e lo studio che dice al prodotto che forma deve avere** (mandato §1).

---

## 1. Che cosa deve produrre

**Dal fotogramma catturato a un flusso HEVC Main10 che un browser vero sappia decodificare — in
software, di proposito.**

Che cosa misura il banco: non «il codificatore non è crollato», ma **i valori dei pixel** di un
fotogramma ridecodificato da uno strumento indipendente, e **un numero che distingue i 10 bit veri
dai 10 bit dichiarati**.

Che cosa vede l'utente: niente, ancora. L'utente vede alla fine della fase 2, quando il fotogramma
arriva nella scheda del browser (F2.5) e viene confrontato coi pixel catturati (F2.6). ⚠ Questa
sotto-fase gli prepara **i byte**, e la sua unica promessa verso l'alto è che quei byte siano quelli
giusti.

---

## 2. ⛔ Il banco — scritto prima del prodotto

### 2.1 La scena, dichiarata — ed è ferma di proposito

**`SCENA-2.3-A`** · un'immagine nota **1920×1080**, `yuv420p10le`, BT.709 **range limitato**
(Y in [64, 940], croma attorno a 512). Generata da `banchi/02-codifica-immagine.py`, deterministica,
**senza font di sistema e senza risorse esterne**: un font 5×7 è scritto dentro il generatore,
perché due giri con due font diversi non si confrontano.

⚠ **La scena è ferma, e `CODER.md` §3.2 non è violata.** Quella regola — *«la scena si dichiara, e
si muove sempre»* — nasce contro chi misura **un ritmo** su uno schermo fermo. Qui non si misura
nessun ritmo: la fase 2 è «un'immagine ferma» per mandato, e si misurano **i valori dei pixel di un
fotogramma**. ⛔ Il ritmo è la fase 3, e lì la scena dovrà muoversi.

La scena è invece **ostile di proposito**, che è l'altra metà della stessa regola: un'immagine
facile passerebbe qualunque prova.

| righe | che cosa c'è | che difetto smaschera |
|---|---|---|
| 0–255 | ⭐ **rampa di grigio a 1 LSB per passo**, da 64 a 940 | **i 10 bit**, e le strisce sulle sfumature |
| 256–511 | sfumature morbide blu→ciano e verde→giallo | le strisce, per l'occhio |
| 512–767 | ⭐ **testo rosso saturo su blu saturo**, a quattro ingrandimenti | **il testo sfrangiato** (4:2:0) |
| 768–1023 | scacchiere da 1 px e barre da 1, 2, 3 px | il taglio del croma |
| 1024–1079 | toppe piatte di riferimento | il rumore su fondo fermo |

⭐ **La scacchiera rossa/blu da 1 px collassa in un viola piatto già nel sorgente**, prima che il
codificatore la veda: è il 4:2:0 che fa il suo mestiere, ed è la dimostrazione visiva più netta del
prezzo di `DECISIONI.md` §2.3.

### 2.2 Che cosa si conta — e il numero che distingue

Il problema di questa sotto-fase è che **tre errori diversi hanno tutti lo stesso aspetto: un
fotogramma che viene bene.** In particolare, ⛔ **se il codificatore è aperto in Main10 ma la catena
gli consegna 8 bit, nessuno se ne accorge guardando i pixel**: le strisce sulle sfumature ci sono,
ma un occhio le attribuisce al bitrate. È la forma **E1** di `REVIEWER.md` §2 applicata al colore —
«`ffprobe` dice Main 10» è **necessario** perché i 10 bit ci siano, e non è affatto **sufficiente**.

⭐ **Il numero che distingue**, letto sulla riga 128 del piano Y del fotogramma **decodificato**:

| grandezza | 10 bit veri | 8 bit travestiti |
|---|---|---|
| livelli distinti sulla rampa | **877** | **220** |
| frazione di campioni multipli di 4 | **~0,251** | **1,000** |

La ragione della seconda riga: un campione a 8 bit promosso a 10 vale `v << 2`, cioè è **sempre** un
multiplo di 4; su una rampa a 10 bit veri i multipli di 4 capitano per caso, uno ogni quattro.
⛔ **1,000 contro 0,251 non è una sfumatura: è un interruttore**, e non ha bisogno di un occhio.

### 2.3 ⛔ Il caso opposto — prodotto, non ragionato

`LEZIONI.md` §1.11 regola 1: *per ogni prova indiretta si scrive cosa mostrerebbe il caso opposto;
se non si sa dire come apparirebbe il contrario, la prova non distingue e va cambiata.*

Il banco **fabbrica** il caso opposto: `sorgente-8in10.yuv` è la stessa identica immagine passata
per 8 bit e rimessa in un contenitore a 10 (`(v >> 2) << 2`), e viene **codificata e ridecodificata
per la stessa strada**. ⭐ E il punto è questo:

> **L'etichetta del caso opposto è identica a quella del giro vero, ed è onesta.** `ffprobe` legge
> `Main 10` e `yuv420p10le` dall'SPS di tutti e due, e ha ragione tutte e due le volte: il
> codificatore **è** Main10. È la **catena** ad avergli consegnato 8 bit. Chi si fermasse a
> `ffprobe` scriverebbe «10 bit» nel rapporto della fase 2. `[M]` 12 agosto 2026.

### 2.4 ⛔ I due giri, e perché non possono essere uno solo

A un bitrate realistico HEVC **distrugge una rampa a 1 LSB** per costruzione: è l'ultimo bit di un
dettaglio che nessuno vede, ed è il primo che il quantizzatore butta. Un banco che contasse i
livelli a CRF 20 troverebbe pochi livelli **anche su una catena a 10 bit perfetta**, e il rosso non
distinguerebbe *«la catena è a 8 bit»* da *«il bitrate era basso»* — due diagnosi opposte sotto la
stessa etichetta, cioè **E2 dentro il banco** invece che nel prodotto.

| giro | come | che cosa dimostra |
|---|---|---|
| **A — la catena** | `lossless=1` | il flusso torna **identico byte per byte**: qui, e solo qui, i 10 bit si misurano senza nulla a cui dare la colpa |
| **B — la resa** | `crf=20` | *quanto* si perde. Le strisce che si vedono qui sono del bitrate, ed è il giro A a permettere di dirlo |

### 2.5 ⛔ Il controllo positivo — quattro, e girano prima di ogni misura

`CODER.md` §3.10: *«questo strumento sa trovare qualcosa che c'è di sicuro?»*

1. il **comparatore** dice «uguali» su un file contro sé stesso;
2. il comparatore dice «diverse» su una copia con **un solo byte girato** — un comparatore che
   rispondesse «uguali» renderebbe verde ogni giro futuro, per sempre;
3. il **misuratore dei bit** dice «10 bit veri» sul sorgente vero;
4. ⛔ e dice «8 bit travestiti» sul caso opposto. **È la metà che si dimentica**: uno strumento che
   dicesse sempre «10 bit» passerebbe i primi tre.

### 2.6 ⛔ Il controllo negativo in coda — e la sorpresa che ha prodotto

Tre storpiature del flusso sano, e il lettore indipendente **deve** non consegnare il fotogramma
buono: `senza-parametri` (VPS/SPS/PPS tolti — è cosa succederebbe se qualcuno accendesse
`GLOBAL_HEADER`), `byte-girato`, `troncato` al 60 %.

⛔⭐ **E qui il banco ha insegnato qualcosa prima di misurare qualunque cosa** `[M]` 12 agosto 2026:

| storpiatura | uscita di ffmpeg | fotogrammi | byte diversi (su 6 220 800) |
|---|---|---|---|
| parameter set tolti | **183** | 0 | — |
| un byte girato al 2 % dello slice | **0** | 1 | **4 695 520** |
| flusso troncato al 60 % | **0** | 1 | **1 196 441** |

⛔ **ffmpeg non rifiuta: conceala.** Due storpiature su tre escono **0**. Un banco che avesse
giudicato il rifiuto sullo **stato d'uscita** avrebbe dichiarato «flusso corrotto accettato» due
volte su tre — e sarebbe stato un banco che non sa vedere un rifiuto **pur avendo il controllo
negativo scritto**. ⇒ Il criterio è: **rifiutato = (zero fotogrammi) OPPURE (i pixel non sono
quelli del sorgente)**; e una storpiatura che desse uscita 0 **e** pixel identici condanna **il
banco**, non il flusso.

⛔ **E una seconda cosa, che è più grave e va detta a F2.4** `[M]`: la prima stesura girava il byte
**24** del NAL — che su 1920×1080 cade ancora dentro l'**intestazione** dello slice. Il fotogramma
decodificato è tornato **identico al sorgente, bit per bit**. Cioè: *un singolo byte corrotto sul
filo può non lasciare **nessuna** traccia — né nello stato, né nei pixel.* Girando lo stesso byte
al 2 % del corpo, i campioni diversi sono passati **da 0 a 4 710 663**.

### 2.7 ⛔ Come questo banco si certifica — sano → guasto → risanato

Con i numeri **scritti prima del giro** (`bash banchi/02-codifica-lancia.sh elenco` li stampa senza
misurare niente). ⭐ Regola dell'11 agosto: *chi scrive un banco lo certifica nello stesso giro.*

| | atteso, scritto prima | misurato `[M]` 12 ago |
|---|---|---|
| **sano** | uscita **0**, «VERDE», nessuna marca | **0**, verde, **30 controlli passati su 30** |
| **guasto F2.3-A** | uscita **1**, «ROSSO», e l'uscita **contiene** «10 BIT DICHIARATI MA NON VERI» | **1**, rosso, 2 controlli falliti, marca presente **1 volta** |
| **risanato** | uscita **0**, marca assente, **impronta del file ritornata** | **0**, verde, marca **0 volte**, sha256 `cbed4476…` combacia |
| **guasto F2.3-B** | uscita **1**, e l'uscita **contiene** «NON SA VEDERE UN RIFIUTO» | **1**, rosso, 3 falliti, marca presente **1 volta** |
| **risanato** | uscita **0**, impronta ritornata | **0**, verde, sha256 `616dc259…` combacia |

⛔ **E la metà che si dimentica** (`01-b12-guasti.py` trappola n.1): la marca **non compare nel giro
sano**. Verificato per tutt'e due, contando: 0 occorrenze nel verde, 1 nel rosso.

**Il giro sano è stato eseguito su due macchine**, e sono verdi tutt'e due `[M]`:

| macchina | ffmpeg | esito | byte del flusso lossless |
|---|---|---|---|
| CHUWI | 7.1.5-0+deb13u1 | verde 30/30 | 96 237 |
| **NIC-OS, dentro il contenitore** — dove vivrà il prodotto | 7.1.5-0+deb13u1 | verde 30/30 | 96 238 |

⚠ **Un byte di differenza fra le due macchine, e non è nei pixel** (0 campioni diversi in tutti e
due i casi): il SEI informativo di x265 contiene opzioni dipendenti dalla macchina (`numa-pools`).
⇒ Il flusso HEVC **non è riproducibile byte per byte fra macchine diverse**, e i **pixel sì**.
Chi un giorno confrontasse due flussi con `md5sum` starebbe misurando il numero di nodi NUMA.

### 2.8 I file, e i comandi

| file | che cos'è |
|---|---|
| `banchi/02-codifica-lancia.sh` | l'orchestratore. `bash banchi/02-codifica-lancia.sh` · `… elenco` per gli attesi senza misurare |
| `banchi/02-codifica-immagine.py` | l'immagine nota, il caso opposto, il misuratore dei bit, il comparatore, e `--autoprova` (il controllo positivo) |
| `banchi/02-codifica-nal.py` | la **forma** del flusso letta sui byte, la **confessione** del codificatore, e le tre storpiature |
| `banchi/02-codifica-guasti.py` | i due guasti, con `--catalogo` che stampa la riga di §8 |
| `banchi/02-codifica-esiti.jsonl` | una riga per giro, con l'ora, la macchina, la scena e tutte le misure |

⚠ **Nessuna dipendenza nuova installata, né sul CHUWI né su NIC-OS.** Il banco usa `ffmpeg`,
`ffprobe` e `python3` **già presenti**, e nient'altro: nessun `numpy`, nessuna libreria di immagini,
nessun font. È una scelta, non un caso — una dipendenza nuova è una decisione (mandato §4).

---

## 3. ⛔ Le tre decisioni che F2.4 e F2.5 ereditano

### 3.1 ⛔ Il profilo: **HEVC Main10, 4:2:0** — e va scritto esplicitamente

`SPECIFICHE.md` §3.1 mette il **desiderato** a *«4K · 60 fps · **10 bit per canale**»*, e
`CODER.md` §1 spiega perché la sola altra leva è stata scartata:

> | Leva | Cura | Prezzo |
> |---|---|---|
> | **10 bit per canale** | le strisce sulle sfumature | quasi nulla, e in hardware ovunque — decoder Android compreso |
> | **4:4:4** | il testo colorato sfrangiato `[M]` v1 | ~50 % di banda, **nessun decoder Android in hardware** |
>
> «**Scelto il 10 bit** — la massima qualità ottenibile su entrambi i client insieme, in hardware,
> senza compromessi.» (`CODER.md` §1; `DECISIONI.md` §2.2)

⇒ ⭐ **Il profilo di REMOTIX è `Main 10`, croma `4:2:0`, cioè `yuv420p10le` / `P010`.** In stringa
codec per il browser: **`hev1.2.4.L<livello>.B0`** — `2` è Main10, e il prefisso `hev1` (non `hvc1`)
perché i parameter set viaggiano **in banda** (`S2-decodifica.md` §3.5, `[S]`).

⛔ **Il 4:4:4 resta una `[?]`, non una promessa** (`DECISIONI.md` §2.3): sarebbe un'opzione per i
soli dispositivi il cui browser lo decodifica, **dietro un interruttore spento** (I6), e nessuno ha
misurato quanto si veda davvero la differenza. ⚠ Questa sotto-fase gli ha però regalato uno
strumento: la fascia 768–1023 dell'immagine nota, dove la scacchiera rossa/blu da 1 px **collassa in
viola piatto già nel sorgente**. Chi riaprirà la `[?]` ha la scena già pronta.

### 3.2 ⛔ La forma del flusso: **Annex-B senza `description`** — e non hvcC

`VideoDecoder` accetta **due formati alternativi ed esclusivi**, e non sono intercambiabili `[S]`
(registrazione HEVC del W3C, citata in `S2-decodifica.md` §3.5): **`hevc`** con una `description`
(un `HEVCDecoderConfigurationRecord`, cioè l'`hvcC`) e i NAL a prefisso di lunghezza; **`annexb`**
senza `description`, coi codici di inizio, e col chunk `key` che deve portare **anche tutti i
parameter set**.

⭐ **F2.3 decide: si spedisce Annex-B, senza `description`.** Quattro ragioni, in ordine di peso:

| # | ragione | marca |
|---|---|---|
| 1 | **È quel che il codificatore già produce.** `libavcodec` restituisce i pacchetti HEVC in Annex-B; l'hvcC non è mai prodotto dal codificatore ma dal *muxer* MP4 (`libavformat/hevc.c`, `ff_isom_write_hvcc`). Produrre un hvcC vorrebbe dire scriverlo a mano o passare da un muxer fittizio — cioè **codice nostro da mantenere per sempre**, che `CODER.md` §4.1 vieta | `[R]` `S2-decodifica.md` §3.5(a) · `[M]` qui: x265 **si dichiara `annexb`** nel proprio SEI |
| 2 | **In Chromium l'Annex-B è la strada più veloce, non la più lenta.** Se `description` è presente, Chromium costruisce un `VideoDecoderHelper` e converte a Annex-B **per ogni fotogramma**, con un'allocazione e una copia (`video_decoder.cc:466-495`, `:611-633`). A 4K60 sono 60 allocazioni e copie di alcuni megabyte al secondo, **regalate** | `[R]` `S2-decodifica.md` §3.5(b) |
| 3 | **L'hvcC ha una trappola documentata.** ISO/IEC 14496-15 vuole gli *emulation prevention byte* conservati negli array NAL, ma Chromium riparsa l'SPS e confronta il profile-tier-level: se l'SPS grezzo contiene `00 00 03` nella zona PTL i valori non coincidono e **`isConfigSupported()` rifiuta**. Il rimedio di chi ci è passato è scrivere NAL de-emulati, *«technically non-compliant … but required for Chrome compatibility»* | `[R]` `S2-decodifica.md` §3.5, moonlight-web `Mp4Muxer.js:252` |
| 4 | **È la prassi di chi lo fa già**: Xpra, scrcpy/Tango e moonlight-web passano tutti Annex-B senza `description`; moonlight-web prova **per HEVC l'Annex-B per primo** e l'hvcC solo dopo | `[R]` `S2-decodifica.md` §3.5(c) |

⚠ **E il conto onesto, perché non sembri gratis**: non esiste un percorso gratis per entrambi i
browser. Chromium converte hvcC → Annex-B; **WebKit fa l'inverso**, prende l'Annex-B e costruisce
l'hvcC internamente perché VideoToolbox vuole una `CMVideoFormatDescription` `[R]`. ⇒ **Dando
Annex-B si paga la conversione solo su Safari; dando hvcC la si paga su Chrome *e* si corre la
trappola del PTL.** Annex-B vince, e il prezzo su Safari è **dichiarato**, non nascosto.

**La conseguenza verificabile, e il banco la verifica sui byte:** il flusso comincia con
**VPS (32), SPS (33), PPS (34)** e poi una figura **IDR**, e i parameter set si ripetono davanti a
**ogni** IDR. `[M]` misurato: sequenza `VPS SPS PPS PREFIX_SEI IDR_N_LP`, e **3 gruppi su 3 IDR**.

⛔ **In concreto, per chi scriverà il prodotto**: **non si accende mai
`AV_CODEC_FLAG_GLOBAL_HEADER`.** È lo stesso divieto che v1 aveva già pagato e scritto a
`v1/remotix-c/src/codificatore.c:268-272` — *«su RDP i parametri di sequenza devono viaggiare NEL
flusso, davanti all'IDR; metterli da parte darebbe un flusso che il client riceve e non sa
decodificare, e il sintomo sarebbe schermo nero con i fotogrammi riscontrati»*. ⭐ La ragione era
RDP, **la conclusione vale identica per `VideoDecoder`**, e per una volta una regola di v1 si
trasporta senza sconti.

### 3.3 ⛔ Il primo fotogramma deve essere un fotogramma chiave — e perché

`[S]` Dopo `configure()` e dopo `flush()`, il primo chunk **deve** essere `key`, altrimenti
`DataError`. ⛔ E **Chromium non si fida della nostra etichetta**: rilegge il bitstream
(`video_decoder.cc:206-214` chiama `media::mp4::HEVC::AnalyzeAnnexB()`), e se l'etichetta dice `key`
ma i NAL dicono altro, errore. Ha persino un messaggio dedicato al nostro esatto errore possibile:

> *«A key frame is required after configure() or flush(). If you're using HEVC formatted H.265 you
> must fill out the description field in the VideoDecoderConfig.»* `[R]` `S2-decodifica.md` §3.6

E in Annex-B «fotogramma chiave» vuol dire **due cose insieme**: una figura IDR/CRA/BLA **e tutti i
parameter set necessari a decodificarla**. Un IDR nudo è marcato `key` e non è un `key`.

⇒ ⭐ **`banchi/02-codifica-nal.py --verifica` è il pezzo di Chromium che possiamo eseguire a casa
nostra.** Se la forma è sbagliata, lo si scopre qui invece che in F2.5 — dove il sintomo sarebbe
«la pagina resta nera» e la ricerca comincerebbe a tre anelli di distanza dalla causa.

⚠ **E la metà che morde in fase 3, non qui**: con un fotogramma solo i parameter set ci sono per
forza. Il guaio arriva quando gli IDR sono tanti e i parameter set stanno **solo in testa**: un
client che si collega dopo riceve un IDR nudo, e il sintomo è **schermo nero con i fotogrammi che
arrivano**. Per questo il banco ne codifica **tre** con `keyint=1` e pretende **tre gruppi**.

### 3.4 ⛔ E2 — il componente che decide da sé: si chiede per nome, e si verifica

`REVIEWER.md` §2 **E2** è la forma di casa: *«il codificatore che ripiega in CPU senza dirlo»*.
`CODER.md` §3.9: *chiedi il componente per nome, e verifica che abbia obbedito.*

**Come si chiede**, nel banco e domani nel prodotto:

- ⛔ **`-c:v libx265`, mai `-c:v hevc`**: `hevc` lascia scegliere a ffmpeg, e due giri finirebbero
  nel rapporto sotto la stessa etichetta;
- ⛔ **`-pix_fmt yuv420p10le` e `-profile:v main10`** esplicitamente, mai per difetto.

**Come si verifica che abbia obbedito** — ⭐ e i testimoni sono **due e indipendenti**:

| testimone | che cosa dice | come lo sa |
|---|---|---|
| `ffprobe` | `codec_name=hevc`, `profile=Main 10`, `pix_fmt=yuv420p10le` | li **ricava dall'SPS**, cioè dai byte, non dai nostri argomenti |
| ⭐ **x265 stesso** | `bitdepth=10`, `annexb`, `repeat-headers`, `bframes=4`, `keyint=250`, `lossless` | li **scrive nel flusso**, in un PREFIX_SEI di user data: è il codificatore che confessa |

Il secondo è `CODER.md` §3.7 applicata al colore — *non si deduce il mittente, lo si chiede*. ⚠ E la
dipendenza va dichiarata: quella confessione esiste perché x265 ha `info=1` acceso di suo, e **il
banco lo tiene acceso di proposito**. Se il prodotto lo spegnesse per risparmiare byte, il controllo
sparirebbe **in silenzio** e resterebbe il solo `ffprobe`.

⚠⛔ **E la confessione ha già detto una cosa che nessuno aveva chiesto** `[M]`:

> **x265 fa `bframes=4` e `open-gop` di default.** Un fotogramma B costringe ad attendere il
> successivo, cioè **un fotogramma di ritardo in più** — e `SPECIFICHE.md` §3.2 dà **50 ms di
> tetto**, con `CODER.md` §1-bis che dice *«il ritardo pesa più dei fotogrammi»*. v1 li vietava a
> mano (`v1/remotix-c/src/codificatore.c:241`, `max_b_frames = 0`, con la ragione scritta accanto).
> ⇒ Qui non morde — un fotogramma solo — ma è **una decisione che il prodotto deve prendere, non
> ereditare in silenzio**. Ereditarla sarebbe **E2 al contrario**: non un ripiego non dichiarato,
> ma un **default** non dichiarato.

---

## 4. Che cosa si riusa da v1 — righe **contate**, non ricopiate

`PIANO.md` §«Fase 2» dice: *«`codificatore.c` (889, **da riportare a HEVC**)»*.

**La cifra è giusta: 889 righe** `[M]` (`wc -l v1/remotix-c/src/codificatore.c`), più
`codificatore.h` a **127**. ⛔ **Ma «riportare a HEVC» è una descrizione ottimista di quel che serve
fare**, e vale la pena scriverlo prima che qualcuno apra il file aspettandosi una sostituzione di
stringhe.

### 4.1 Che cosa fa **oggi**, davvero `[R]`

**Non è un codificatore HEVC in nessun senso**: è un codificatore **H.264 / AVC420 per RDP**.

| conteggio, sul file `[M]` | |
|---|---|
| righe che nominano H.264 / AVC / AVC420 | **77** |
| righe che nominano RDP, FreeRDP, la metablock o RemoteFX Progressive | **47** |
| righe che nominano HEVC, H.265, Main10, P010 o i 10 bit | ⛔ **0** |

Con quale libreria: **libavcodec**, con **quattro candidati provati in ordine** (`CANDIDATI[]`,
righe 31-41) — `h264_vaapi`, `h264_qsv`, `h264_nvenc`, `libx264` — **tutti e quattro H.264**, e
**tutti e quattro in NV12 a 8 bit**. Più due percorsi alternativi: il codificatore H.264 di
**FreeRDP** come ultima spiaggia (`apri_freerdp`, righe 477-504) e **RemoteFX Progressive**
(righe 517-529), che con RCP non c'entrano più niente.

Che cosa consegna: non un flusso, ma un **`RDPGFX_SURFACE_COMMAND`** con dentro una
`RDPGFX_AVC420_BITMAP_STREAM` e la sua **metablock** (rettangoli e valori di quantizzazione,
righe 81-90 e 531-538), con perfino l'aritmetica dei byte della metablock in
`codificatore_byte()` (righe 857-869).

### 4.2 Che cosa vuol dire «riportare», di preciso

| pezzo | righe | destino |
|---|---|---|
| la tabella dei candidati e il giro dei tentativi | 31-41, 280-474 | ⭐ **la forma si riusa, i nomi cambiano tutti**: `libx265` per la fase 2, e `hevc_vaapi`/`hevc_qsv`/`hevc_nvenc` per la fase 8. ⚠ E il formato dei pixel cambia con loro: **NV12 → P010LE** in **sette punti** (righe 37-40, 52, 55, 140, 285, 407, 457-459) |
| il profilo e i fotogrammi B | 232-243 | `AV_PROFILE_H264_HIGH` → `AV_PROFILE_HEVC_MAIN_10`. ⭐ **Il commento sui fotogrammi B si riusa parola per parola**: la ragione (un fotogramma di ritardo) non dipende dal codec, e §3.4 mostra che x265 ne fa 4 se nessuno glielo vieta |
| ⭐ il divieto di `GLOBAL_HEADER` | 268-272 | ⭐ **si riusa intatto, e cambia solo la ragione**: era «su RDP i parametri devono viaggiare nel flusso», diventa «in Annex-B il chunk `key` deve portare i parameter set». Stessa regola, stesso sintomo (schermo nero coi fotogrammi che arrivano) |
| la conversione di colore `sws` | 420-459 | la struttura resta, la destinazione no: `BGR0 → NV12` diventa `→ P010LE`. ⚠ E il commento che la dichiara **collo di bottiglia misurato** (12,5 ms contro 3,8 di codifica, su 2560×1024) resta valido come storia, ma il numero va rimisurato: a 10 bit i byte sono il doppio |
| il conto dei tempi (conversione/caricamento/codifica) | 63-74, 674-700 | ⭐ **si riusa intero**, ed è la cosa più preziosa del file: senza quei tre numeri «il ritmo è calato» non si attribuisce a niente |
| ⛔ tutto l'apparato RDP: metablock, `RDPGFX_SURFACE_COMMAND`, `codificatore_byte`, `avc420_compress` | 81-90, 531-538, 704-772, 857-869 | ⛔ **muore**. Lo sostituisce quel che decide **F2.4** sul filo |
| ⛔ il percorso FreeRDP e RemoteFX Progressive | 477-504, 517-529, 749-771 | ⛔ **muoiono**: erano ripieghi per client altrui, e in V2 i client sono nostri (`DECISIONI.md` §1.6) |
| ⛔ tutto il percorso VA-API / superfici / copia zero | 111-157, 299-399, 652-671, 820-855 | ⏳ **non muore, ma non è di questa fase**: la codifica qui è software **di proposito** (`PIANO.md` §«Fase 2»). Si riapre in **fase 8** |

⭐ **La conclusione onesta**: di 889 righe, quel che sopravvive alla fase 2 è **la forma** (il giro
dei tentativi, il rifiuto del ripiego silenzioso, il conto dei tempi, il divieto di
`GLOBAL_HEADER`) e **quasi nessuna riga letterale**. ⚠ Chi scrivesse «riusato `codificatore.c`»
nella colonna del riuso starebbe scrivendo una cosa non vera.

### 4.3 ⭐ E la riga che si riusa più di tutte, ed è di quattro righe

`v1/remotix-c/src/codificatore.c:550-566`:

> *«⛔ CHIESTO PER NOME, NESSUN RIPIEGO. Chi indica un codificatore sta misurando: ripiegare su un
> altro darebbe due misure diverse con la stessa etichetta, che è peggio di non misurare.»*

È **E2** scritta da chi l'aveva già pagata, ed è la regola che §3.4 di questo rapporto ha solo
riscritto con parole nuove. `[R]`

---

## 5. ⛔ Le trappole già pagate che mordono qui

| trappola | dove sta scritta | come morde in F2.3 | che cosa si è fatto |
|---|---|---|---|
| **E1** — necessario scambiato per sufficiente | `REVIEWER.md` §2 · `LEZIONI.md` §1.11 | «`ffprobe` dice Main 10 ⇒ ci sono i 10 bit». È **necessario** e non **sufficiente**, e il caso opposto lo dimostra: l'etichetta è identica e onesta su una catena a 8 bit | §2.2, §2.3: il conteggio dei livelli e la frazione di multipli di 4, con il caso opposto **prodotto** |
| **E2** — un componente che decide da sé | `REVIEWER.md` §2 · `LEZIONI.md` §1.8 · `CODER.md` §3.9 | `-c:v hevc` lascia scegliere a ffmpeg; e x265 sceglie `bframes=4` e `open-gop` **da solo**, che costano ritardo | §3.4: si chiede per nome, e **due testimoni indipendenti** verificano — `ffprobe` sull'SPS e la confessione di x265 nel SEI |
| **E8** — il silenzio scambiato per zero | `REVIEWER.md` §2 · `LEZIONI.md` §1.9 | ffmpeg esce **0** su due storpiature su tre: «flusso valido» e «flusso corrotto che il decodificatore ha concelato» hanno lo stesso stato d'uscita | §2.6: rifiutato si giudica **sui pixel**, non sullo stato. E lo stato si cattura in una variabile, mai in una catena di tubi |
| **il banco che si certifica** | `LEZIONI.md` §1.2 · `PIANO.md` §0.3 regola 4 | «un banco che non è mai diventato rosso non è pulito: è NON CERTIFICATO» | §2.7: due guasti, sano → guasto → risanato, con la marca verificata **assente nel verde** |
| **il guasto che non è stato innestato** | `01-b12-guasti.py` trappola n.2 | ⛔ **è successo davvero, in questo giro**: la storpiatura `byte-girato` cadeva nell'intestazione dello slice e lasciava i pixel **identici** | §2.6: la storpiatura entra al 2 % del corpo, e il fatto è scritto invece che nascosto |
| **il terreno che non è quello che credo** | `01-b0-terreno.sh` · R12-A.44/45 | un banco verde su un ffmpeg senza libx265, o su due versioni diverse fra CHUWI e contenitore | passo 1: gli strumenti si verificano **a ogni giro**, e la versione finisce nel registro |
| ⛔ **la fase 2 apre l'applicazione DOPO i dispositivi di input** | `PIANO.md` §«Fase 2», riquadro S.4 `[M]` | ⚠ **non morde qui**, e va detto: F2.3 non apre nessuna sessione e non inietta nessun input. Morde F2.1 e F2.6 | nulla da fare, ma è dichiarato invece che dimenticato |
| **le prove indirette** | `LEZIONI.md` §1.11 | «il flusso si decodifica ⇒ il browser lo decodificherà». ⛔ Il lettore indipendente è ffmpeg, **non è Chromium** | il banco stampa in coda che cosa **non** dimostra, e F2.5/F2.6 restano l'unica prova |

⭐ **E una trappola nuova, comprata in questo giro e scritta perché non si ricompri**: la prima
stesura del passo 1 diceva `ffmpeg -encoders | grep -q libx265`. Con `set -o pipefail`, `grep -q`
chiude il tubo al primo riscontro, ffmpeg muore di **SIGPIPE (141)**, e ⛔ **la pipeline riporta un
fallimento proprio quando la cosa cercata C'È**. Il banco ha dichiarato «libx265 non c'è» su una
macchina che ce l'ha. È `LEZIONI.md` §1.9 **al contrario** — non lo zero letto come guasto, ma il
**successo** letto come guasto. ⇒ L'uscita si cattura in una variabile e si esamina fuori dal tubo.

---

## 6. Le `[?]` che restano

| # | `[?]` | perché non è chiusa | di chi è |
|---|---|---|---|
| 1 | ⛔ **I 10 bit VERI dalla cattura.** Questo banco dimostra che il codificatore e il flusso portano 10 bit veri su un sorgente **costruito**. Che cosa consegni **Mutter** — 8 bit per canale in BGRx? DMA-BUF a 10 bit? — non è misurato da nessuno | il sorgente qui è fabbricato, non catturato. ⚠ E se la cattura desse 8 bit, tutta la catena resterebbe **verde**: l'etichetta direbbe Main 10 ed è quello che il guasto F2.3-A riproduce | ⛔ **F2.2**, e F2.3 le ha lasciato lo strumento per misurarlo |
| 2 | ⛔ **I 10 bit veri dal telefono.** `DECISIONI.md` §2.3-bis: mpv riporta che sul percorso `mediacodec` di Android il supporto a 10 bit è limitato e **l'uscita torna a 8 bit** | è il percorso di mpv, non il nostro. ⭐ Ma il misuratore di §2.2 funziona identico dall'altra parte: la rampa a 1 LSB e la frazione di multipli di 4 si leggono su un `VideoFrame` come su un file | **F2.6** (sonda sul telefono), con `S2-decodifica.md` §4.1 sequenza E |
| 3 | `[?]` **Chromium accetta il prefisso `hev1.` in Annex-B?** `S2-decodifica.md` §3.5 lo dà per probabile (Xpra e Tango passano Annex-B con prefisso `avc1.`), ma **va provato al banco** | il banco di F2.3 non ha un browser | **F2.5** |
| 4 | `[?]` **Il punto di lavoro del bitrate.** CRF 20 è un numero di comodo per far vedere che il flusso regge fuori dal lossless, non una scelta: `[M]` differenza massima Y **76** su 1023, 21 569 byte contro 96 237 | il punto di lavoro è la **fase 9**, e dipende dalla rete | fase 9 |
| 5 | `[?]` **Quanto costa la codifica software a 4K.** Qui si è codificato **un fotogramma a 1080p** e non si è cronometrato niente: sarebbe un numero senza regime (`CODER.md` §3.5) | la fase 2 è un'immagine ferma | fase 3, e la fase 8 per l'accelerazione |
| 6 | `[?]` **Il SEI di x265 va spento nel prodotto?** `[M]` **2 238 byte per fotogramma chiave** di stringa di versione — il **55 %** del flusso a 320×64, e il **2,3 %** a 1080p lossless | spegnerlo (`info=0`) risparmia byte **e porta via un testimone** (§3.4) | ⏳ decisione del prodotto, da prendere **dichiarandola** |
| 7 | `[?]` **Il 4:4:4** | `DECISIONI.md` §2.3, invariata. ⭐ Questo giro le lascia la scena pronta (§3.1) | l'utente, su un banco che metta le due immagini a confronto (I8) |

---

## 7. Le cuciture

### Che cosa F2.3 **chiede**

| a chi | che cosa |
|---|---|
| ⛔ **F2.2 (la cattura)** | **il formato esatto dei pixel in ingresso, e la sua profondità di bit vera.** Il codificatore vuole `P010LE` (10 bit, 4:2:0, croma interlacciato) o un piano a 10 bit da cui convertirlo. ⛔ **Tre cose vanno dichiarate, non dedotte**: (a) **quanti bit per canale** consegna Mutter davvero — `[?]` viva, ed è la n. 1 di §6; (b) **il range** (limitato o pieno) e la **matrice** (BT.601 o BT.709), perché un confronto di pixel con la matrice sbagliata misura la matrice; (c) se il buffer è **BGRx a 8 bit**, ⛔ **allora i 10 bit del desiderato sono già persi prima del codificatore**, e va scritto in `DECISIONI.md` invece che scoperto in F2.6. ⚠ E se la conversione la fa `sws_scale` come in v1, va saputo che a 10 bit i byte raddoppiano e il collo di bottiglia misurato in v1 (12,5 ms) va rimisurato |
| **F2.1 (la sessione)** | niente. F2.3 non apre sessioni e non tocca NIC-OS oltre a eseguire il proprio banco dentro il contenitore |
| **F2.6 (il giudizio)** | ⭐ **prenda l'immagine nota di §2.1 e il misuratore di §2.2**: la rampa a 1 LSB e la frazione di multipli di 4 funzionano identiche su un `VideoFrame` del browser. È la `[?]` n. 2, ed è la sola prova che può smentire `DECISIONI.md` §2.2 |

### Che cosa F2.3 **promette** — la forma esatta dei byte

⭐ **A F2.4 (il filo) e a F2.5 (la pagina), e sono la stessa promessa letta dai due capi:**

```
  flusso HEVC Main10 4:2:0, in ANNEX-B, senza description.

  [00 00 00 01] VPS (tipo 32)
  [00 00 00 01] SPS (tipo 33)      ← profile_idc = 2 (Main10), bit_depth = 10
  [00 00 00 01] PPS (tipo 34)
  [00 00 01]    PREFIX_SEI (39)    ⚠ presente, ~2,2 KB, e si può spegnere (§6 n.6)
  [00 00 01]    IDR_N_LP (20)      ← il primo fotogramma è SEMPRE un fotogramma chiave
```

| a F2.4 — il filo | |
|---|---|
| **i byte da portare** | il flusso Annex-B **così com'è**, senza riconfezionarlo: nessun prefisso di lunghezza, nessuna `description` da trasportare a parte. ⭐ Un fotogramma è **un blocco contiguo di byte**, e il confine di fotogramma lo dà **RCP**, non i codici di inizio |
| **la taglia** | `[M]` a 1080p: **96 237 byte** in lossless, **21 569** a CRF 20, e un IDR **non è mai piccolo** — chi dimensiona un buffer su un fotogramma «tipico» sbaglia sul primo |
| ⛔ **l'integrità è del filo, non del codec** | `[M]` §2.6: **un byte corrotto nell'intestazione dello slice ha lasciato i pixel identici; uno al 2 % del corpo ne ha corrotti 4,7 milioni — e ffmpeg è uscito 0 in tutti e due i casi.** ⇒ **Il codec non è un rivelatore di corruzione.** Se il filo consegna byte sbagliati, il sintomo è un'immagine sbagliata, non un errore. QUIC lo copre; ⚠ ma qualunque scorciatoia che aggiri quella garanzia va guardata con questo numero in mano |
| **il primo fotogramma** | è marcato **chiave**, e la marca è verificabile sui byte (`02-codifica-nal.py --verifica`) — F2.4 può riusare quel validatore invece di scriverne un altro |

| a F2.5 — la pagina | |
|---|---|
| **`VideoDecoder.configure()`** | `codec: "hev1.2.4.L<livello>.B0"` — ⛔ **`hev1`, non `hvc1`**, perché i parameter set viaggiano in banda (§3.2). Il livello si legge dall'SPS del flusso vero, **non si indovina** |
| ⛔ **`description`** | **assente. Non si passa.** Passarla farebbe interpretare il flusso come a prefisso di lunghezza, e il sintomo sarebbe una pagina nera senza errore parlante |
| **il primo `EncodedVideoChunk`** | `type: "key"`, e **contiene VPS+SPS+PPS+IDR insieme**. ⛔ Chromium rilegge il bitstream e non si fida dell'etichetta (§3.3) |
| **le opzioni consigliate** | `optimizeForLatency: true`; e `hardwareAcceleration` va provato nelle tre forme, perché su Android `prefer-hardware` **non prova niente** (`S2-decodifica.md` §3.4 punto 2) |
| ⚠ **quel che non si potrà vedere** | in regime `VideoDecoder` **non verifica il bitstream** e non solleva errore su un riferimento perso `[?]`. F2.3 ha misurato il fratello di quel comportamento su ffmpeg `[M]`: **la corruzione si vede nei pixel, non nello stato** |

| a chi scriverà il prodotto (giro dopo) | |
|---|---|
| ⛔ | **`-c:v libx265` per nome**, `-profile:v main10`, `-pix_fmt yuv420p10le`. Mai `hevc` generico |
| ⛔ | **mai `AV_CODEC_FLAG_GLOBAL_HEADER`** (§3.2, e v1 `codificatore.c:268-272`) |
| ⛔ | **`bframes=0`**: x265 ne fa 4 di suo, e costano ritardo (§3.4). E ogni default non chiesto che si tiene **si dichiara** |
| ⚠ | **il ripiego resta vietato anche quando la colpa non è nostra** (`DECISIONI.md` §2.7, `CODER.md` §4.2): un codificatore che scendesse a 8 bit perché la catena non dà di più deve **dirlo nel registro**, non arrangiarsi |

---

## 8. La riga per il catalogo delle certificazioni

Nella forma di `banchi/01-b12-guasti.py`. La stampa `python3 banchi/02-codifica-guasti.py --catalogo`.

```
┌── F2.3-A — organo: la prova dei 10 bit veri
│  banco            02-codifica-lancia.sh
│  comando          bash banchi/02-codifica-lancia.sh
│  ⛔ ATTESO SANO   uscita 0 · «VERDE — 30 controlli passati, 0 falliti»
│                   · e la marca «10 BIT DICHIARATI MA NON VERI» NON compare
│  guasto           la catena consegna 8 bit al codificatore, e l'etichetta resta ONESTA
│    file           02-codifica-lancia.sh
│    si sostituisce SORGENTE_VERA="$LAV/sorgente-10bit.yuv"
│    con            SORGENTE_VERA="$LAV/sorgente-8in10.yuv"  # GUASTO F2.3-A
│  ⛔ ATTESO GUASTO uscita 1 · «ROSSO» · e l'uscita CONTIENE
│                   «10 BIT DICHIARATI MA NON VERI»
│  dimostra         il codificatore È Main10 e non mente: ffprobe legge «Main 10» e
│                   «yuv420p10le» dall'SPS, e ha ragione.  È la CATENA a consegnargli 8 bit.
│                   Il fotogramma viene BENE e nessun occhio lo distingue.  Solo i livelli
│                   sulla rampa cadono da 877 a 220 e i multipli di 4 salgono da ~0,25 a 1,000
└  riferimento      SPECIFICHE.md §3.1 · DECISIONI.md §2.2, §2.3-bis · LEZIONI.md §1.11
                    · REVIEWER.md §2 E1

┌── F2.3-B — organo: il controllo negativo, «questo banco sa vedere un rifiuto?»
│  banco            02-codifica-lancia.sh
│  comando          bash banchi/02-codifica-lancia.sh
│  ⛔ ATTESO SANO   uscita 0 · «VERDE» · e la marca «NON SA VEDERE UN RIFIUTO» NON compare
│  guasto           `--storpia` non storpia: consegna una copia intatta
│    file           02-codifica-nal.py
│    si sostituisce         dati[dove] ^= 0xFF
│    con                    dati[dove] ^= 0x00  # GUASTO F2.3-B
│  ⛔ ATTESO GUASTO uscita 1 · «ROSSO» · e l'uscita CONTIENE «NON SA VEDERE UN RIFIUTO»
│  dimostra         un controllo negativo che non innesta niente passa da solo.  Un banco
│                   che contasse le storpiature TENTATE invece di quelle RIFIUTATE direbbe
│                   «3 su 3» avendone rifiutate 2
└  riferimento      REVIEWER.md §1 punto 5 · CODER.md §3.10 · 01-b12-guasti.py trappola n.2
```

**Esito della certificazione, `[M]` 12 agosto 2026** — cinque esecuzioni, non due:

| giro | atteso (scritto prima) | misurato | |
|---|---|---|---|
| sano | 0 · verde · marca assente | **0** · verde 30/30 · marca 0 volte | ✅ |
| F2.3-A innestato | 1 · rosso · marca presente | **1** · rosso 2/30 · marca 1 volta | ✅ |
| risanato | 0 · impronta ritornata | **0** · verde 30/30 · sha256 combacia | ✅ |
| F2.3-B innestato | 1 · rosso · marca presente | **1** · rosso 3/31 · marca 1 volta | ✅ |
| risanato | 0 · impronta ritornata | **0** · verde 30/30 · sha256 combacia | ✅ |

⭐ **Il banco di F2.3 è CERTIFICATO su due organi.** ⚠ E «certificato» vuol dire *«sa diventare
rosso per le due ragioni per cui deve»* — non *«il flusso è giusto»*. `REVIEWER.md` §0.
