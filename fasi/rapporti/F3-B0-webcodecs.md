# F3-B0 — `VideoDecoder` decodifica HEVC Main10, e i fotogrammi si contano

**Banco**: `banchi/03-palco-webcodecs.py` (nuovo) · **esiti**: `banchi/03-palco-esiti.jsonl`, righe
`"banco":"03-palco-webcodecs"` · **macchina**: CHUWI · **13 agosto, sera-notte**

---

## ⭐ La `[?]` e' CHIUSA, e nella direzione buona

> **`VideoDecoder` decodifica davvero HEVC Main10 su questo palco: 120 `VideoFrame` su 120
> unita' d'accesso, 5 giri su 5, su TUTT'E DUE le strade di confezionamento.**

E non e' la parola di `isConfigSupported`: sono i fotogrammi contati all'uscita del
`output` callback, con `f.close()` su ognuno.

⛔ **Ma il numero che chiude la `[?]` porta con se' una correzione al 13 agosto sera**: il
`<video>` aveva detto «119 su 120», e quel 119 era **sbagliato per una ragione che non
riguarda il codec** — vedi «Il terzo numero» piu' sotto. Il flusso ha **120** immagini, e
`VideoDecoder` le tira fuori **tutte e 120**.

---

## Che cosa ho misurato

Sei flussi, non uno: perche' **uno spezzatore sbagliato consegna zero fotogrammi
esattamente come un codec non supportato**, e senza controlli il «no» non si distingue dal
«non ho saputo chiedere».

| flusso | codec | come e' confezionato | ruolo |
|---|---|---|---|
| `vp9-ivf` | `vp09.02.41.10` | IVF, `description` assente | ⭐ controllo dell'**harness** |
| `av1-ivf` | `av01.0.08M.08` | IVF, `description` assente | ⭐ controllo chiesto dal mandato |
| `h264-annexb` | `avc1.640028` | Annex-B, `description` assente | ⭐ controllo dello **spezzatore Annex-B** |
| `h264-avcc` | `avc1.640028` | `description` = `avcC`, campioni lungo-prefissati | ⭐ controllo della **strada description** |
| `hevc-annexb` | `hev1.2.4.L120` | Annex-B, `description` assente | ⛔ **la domanda** |
| `hevc-hvcc` | `hvc1.2.4.L120` | `description` = `hvcC`, campioni lungo-prefissati | ⛔ **la domanda, seconda strada** |

### La strada che ho preso, e perche' — le ho prese TUTT'E DUE

Il mandato chiedeva di scegliere fra Annex-B e demux dell'mp4. **Ho fatto tutt'e due, e
non per scrupolo: e' la scelta che rende il risultato refutabile.**

- Con la **sola** Annex-B, un «no» su HEVC si spiega in due modi che non si distinguono:
  «Chrome non decodifica HEVC» oppure «Chrome non accetta il mio Annex-B».
- Con la **sola** `hvcC`, un «no» si spiega con «il mio demux mp4 ha sbagliato la tabella
  dei campioni».
- **Con tutt'e due, ognuna col suo controllo positivo sullo stesso codice**, i due modi si
  separano. `h264-annexb` passa per lo **stesso** `spezza_annexb()` di `hevc-annexb`;
  `h264-avcc` passa per lo **stesso** `demux_mp4()` di `hevc-hvcc`.

⇒ Ogni «no» su HEVC ha accanto un «si» prodotto dalla **stessa riga di codice** su un codec
che funziona di sicuro. Se lo spezzatore fosse rotto, sarebbe rosso anche il controllo, e
il banco esce **6** invece di dare un «no» che non vale niente.

Lo spezzatore Annex-B taglia sulle **unita' d'accesso**, non sui NAL:
`first_slice_segment_in_pic_flag` (HEVC, primo bit dopo i 2 di header) e `first_mb_in_slice
== 0` (H.264), coi NAL non-VCL che aprono (VPS/SPS/PPS/AUD/SEI) attaccati al fotogramma che
**segue**. Prova indipendente che il taglio e' giusto: **120 pezzi su tutt'e sei i flussi**,
e per HEVC il numero coincide con i **120 campioni** letti dalla tabella `stsz` dell'mp4,
che e' una fonte diversa e indipendente.

---

## I numeri, con la scena accanto a ognuno

**Scena comune a tutt'e tre le tabelle**: CHUWI · Xvfb `:95`..`:99` 1280x1024x24 · flussi
usciti dal codificatore **hardware** del server (`hevc_vaapi`, `vp9_vaapi`, `h264_vaapi`) e
presi da `/tmp/sonda-vp9/`, derivati **in memoria** e serviti da `127.0.0.1:8890`..`8894` ·
esiti **rimandati dalla pagina** con un POST, **niente CDP** · **5 giri**, un Xvfb e un
profilo nuovi per giro · strada **WebCodecs `VideoDecoder`**, ⛔ **non** `<video>`.

### 1. Chrome 151.0.7922.137, **senza** `--disable-gpu` — la domanda

webgl visto dalla pagina: `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N), OpenGL ES 3.2)`

| flusso | fotogrammi, 5 giri | ms per 120 fotogrammi | `VideoFrame.format` |
|---|---|---|---|
| `vp9-ivf` | 120 · 120 · 120 · 120 · 120 | 221 221 221 159 183 | `null` 1920x1080 |
| `av1-ivf` | 120 · 120 · 120 · 120 · 120 | 372 384 332 369 364 | `I420` 1920x1080 |
| `h264-annexb` | 120 · 120 · 120 · 120 · 120 | 209 205 204 205 204 | `BGRX` 1920x1080 |
| `h264-avcc` | 120 · 120 · 120 · 120 · 120 | 213 201 200 201 203 | `BGRX` 1920x1080 |
| **`hevc-annexb`** | **120 · 120 · 120 · 120 · 120** | **176 172 171 172 181** | `null` 1920x1080 |
| **`hevc-hvcc`** | **120 · 120 · 120 · 120 · 120** | **181 172 170 171 178** | `null` 1920x1080 |

`isConfigSupported` ha detto `true` su tutt'e sei. **Uscita del banco: 0.**

⭐ **HEVC e' il piu' VELOCE dei sei**, 171-181 ms per 120 fotogrammi 1080p10 (≈1,4 ms
l'uno). E `format: null` vuol dire **fotogramma opaco che sta sulla GPU**: non e' passato
per la CPU. Lo stesso vale per VP9. ⇒ La decodifica HEVC va **in hardware**, e questo
combacia col `powerEfficient: true` misurato dal `<video>` il 13 sera.

### 2. Chrome 151, **con** `--disable-gpu` — ⭐ il controllo negativo

webgl visto dalla pagina: `niente webgl` · **unica variabile cambiata: la bandiera.**

| flusso | fotogrammi, 5 giri | ms | `VideoFrame.format` |
|---|---|---|---|
| `vp9-ivf` | 120 · 120 · 120 · 120 · 120 | 1616 1258 1192 933 940 | `I420P10` **1984**x1080 |
| `av1-ivf` | 120 · 120 · 120 · 120 · 120 | 709 370 399 354 341 | `I420` 1920x1080 |
| `h264-annexb` | 120 · 120 · 120 · 120 · 120 | 505 861 796 402 425 | `I420` 1920x**1090** |
| `h264-avcc` | 120 · 120 · 120 · 120 · 120 | 465 428 419 638 660 | `I420` 1920x**1090** |
| **`hevc-annexb`** | **0 · 0 · 0 · 0 · 0** | 1 1 2 2 1 | — |
| **`hevc-hvcc`** | **0 · 0 · 0 · 0 · 0** | 3 3 3 2 2 | — |

Su HEVC: `isConfigSupported` → `false`, e `configure()` alza
`OperationError: Unsupported configuration`. **Uscita del banco: 0** (il «no» era l'atteso).

⭐ **Il banco NON e' cieco, e lo dimostra su tre assi contemporaneamente:**
1. **distingue i codec** — HEVC 0 fotogrammi, gli altri quattro 120;
2. **distingue le vie di decodifica** — VP9 passa da `null`/GPU a `I420P10`/CPU, e da 221 ms
   a 1258; `codedWidth` passa da 1920 a **1984** (l'imbottitura del decodificatore
   software), e per H.264 `codedHeight` passa da 1080 a **1090**. Non e' lo stesso
   decodificatore, e si vede senza doverlo chiedere;
3. **il rosso arriva nel codice d'uscita** — provato apposta, sotto.

⚠ `av1-ivf` costa uguale con e senza GPU (≈360 ms, `I420` in tutt'e due) ⇒ AV1 andava **gia'
in software (dav1d)** anche col palco a GPU accesa. Utile saperlo prima di sceglierlo.

### 3. Firefox 140.13.0esr `--headless` — ⚠ **regge, e da' una risposta vera**

Il mandato diceva «se non regge, dillo». **Regge.** Nessuna finestra su Xvfb, nessun CDP,
la pagina rimanda gli esiti da sola esattamente come su Chrome.
webgl visto dalla pagina: `Intel(R) HD Graphics, or similar` · `VideoDecoder in window`: `true`

| flusso | fotogrammi, 5 giri | ms | `VideoFrame.format` |
|---|---|---|---|
| `vp9-ivf` | 120 · 120 · 120 · 120 · 120 | 1300 1079 1083 1527 1612 | `BGRX` 1920x1080 |
| `av1-ivf` | 120 · 120 · 120 · 120 · 120 | 447 469 458 1280 943 | `BGRX` 1920x1080 |
| `h264-annexb` | 120 · 120 · 120 · 120 · 120 | 497 496 520 885 999 | `BGRX` 1920x1080 |
| `h264-avcc` | 120 · 120 · 120 · 120 · 120 | 488 446 461 669 674 | `BGRX` 1920x1080 |
| **`hevc-annexb`** | **0 · 0 · 0 · 0 · 0** | 2 3 2 3 2 | — |
| **`hevc-hvcc`** | **0 · 0 · 0 · 0 · 0** | 2 2 3 4 2 | — |

`isConfigSupported` → `false` su HEVC, e `configure()` alza `NotSupportedError`.
**Uscita del banco: 2 (ROSSO).**

⛔ **Il rosso e' corretto e va letto cosi'**: la tabella degli attesi e' scritta per Chrome
(HEVC atteso `si` col palco a GPU accesa). Firefox dice `no`, quindi il banco esce 2 — ed e'
proprio il fatto nuovo: **Firefox non decodifica HEVC con `VideoDecoder` su questa
macchina, ne' per Annex-B ne' per `hvcC`**, mentre i quattro controlli positivi sono verdi
5 giri su 5. ⇒ Il «no» di Firefox **non e'** colpa dello spezzatore.

⚠ Firefox e' il piu' lento su tutti e quattro i codec che decodifica, e **non da' mai un
fotogramma opaco**: sempre `BGRX`, mai `null`.

---

## Il controllo positivo — e perche' ce ne sono quattro

`vp9-ivf` (IVF: 32 byte + 12 per fotogramma, come chiedeva il mandato) e' il controllo
dell'**harness del conteggio**: se qui non si contassero fotogrammi, nessun «no» del banco
varrebbe niente. `av1-ivf` e' il controllo che il mandato chiedeva per nome.
`h264-annexb` e `h264-avcc` sono i controlli delle **due strade di confezionamento**, che
sono la parte davvero fragile.

**In 15 giri × 6 flussi = 90 misure, i quattro controlli positivi hanno dato 120/120 in
tutte e 60 le occasioni**, su tutt'e tre le scene (Chrome con GPU, Chrome senza GPU,
Firefox). ⇒ Lo spezzatore e il conteggio non sono in discussione in nessuna delle tre.

## Che il banco sappia dire di no — **provato, non promesso**

Tre banchi che uscivano sempre 0 sono gia' costati una giornata, percio' i codici rossi li
ho fatti scattare apposta, da fuori, senza toccare il banco
(`spec_from_file_location` + attesa cambiata, poi rimesso):

| come l'ho forzato | uscita | che cosa ha stampato |
|---|---|---|
| HEVC atteso `si` su palco **senza** GPU | **2** | `⛔ ROSSO: ['hevc-annexb','hevc-hvcc'] non ha fatto quel che era atteso` |
| `vp9-ivf` (controllo positivo) atteso `no` | **6** | `⛔ BANCO CIECO: il controllo positivo ['vp9-ivf'] e' rosso ⇒ nessun «no» di questo giro vale niente` |
| `SORGENTI` puntato a una cartella che non c'e' | **5** | `⛔ preparazione fallita — «non ho potuto guardare», non «no»` |

⛔ **`RuntimeError` non esce 1**: `main()` e' avvolto e un guasto imprevisto esce **7**.
Il **1** resta riservato a «Python e' morto da solo» e **non e' mai un caso rosso**.
La scala intera: `0` verde · `2` rosso · `3` palco non montato · `4` pagina muta ·
`5` preparazione · `6` banco cieco · `7` guasto del banco · `1` riservato.

---

## Il terzo numero: 120, 119 o 118? — ⛔ **il 119 del 13 agosto era un artefatto del CONTENITORE**

Tre misure sullo **stesso** `prova-hevc.mp4` davano tre numeri diversi, e la cosa andava
chiusa prima di fidarsi di uno qualunque:

| chi conta | quanti | scena |
|---|---|---|
| `<video>` + `getVideoPlaybackQuality()` | **119** su 120 | 13 agosto sera, Chrome, `<video>` |
| `ffmpeg -i prova-hevc.mp4` | **118** | decodificatore software, **dall'mp4** |
| `ffmpeg -i` sullo **stesso flusso in Annex-B** | **120** | stesso decodificatore, **senza contenitore** |
| **`VideoDecoder`**, tutt'e due le strade | **120** | questo banco, 5 giri su 5 |

**La causa e' una `elst`** (edit list) dentro l'mp4: `media_time = 614` tick, `mdhd
timescale = 15360`, cioe' 256 tick per fotogramma a 60 fps.

- `614 / 256` = **2,40 fotogrammi saltati in testa**
- durata dichiarata `1967 ms` = **118,02 fotogrammi presentati**

⇒ Il flusso elementare ha **120 immagini codificate** (120 campioni in `stsz`, 120 unita'
d'accesso in Annex-B, 1 IDR + 119 TRAIL, **zero** RASL/RADL da scartare, `0 decode errors`).
Il **contenitore** ne presenta 118. `ffmpeg` obbedisce alla edit list e ne da' 118;
`<video>` le obbedisce a meta' e ne da' 119; **`VideoDecoder` non ha contenitore per
niente** e restituisce tutte e **120**.

⭐ **E questa e' una seconda ragione, indipendente, per cui la misura del 13 sera non
bastava**: `<video>` e `VideoDecoder` non contavano nemmeno **le stesse cose**. Il `<video>`
guardava attraverso un contenitore che si mangiava due fotogrammi e mezzo.

---

## ⚠ Che cosa NON ha funzionato

**1. ⛔ `~/.cache` su CHUWI e' un COLLEGAMENTO a `/tmp`.** Il mandato diceva «metti i
profili sotto `~/.cache/` perche' `/tmp` e' pieno». `readlink -f ~/.cache` → `/tmp`: e'
**la stessa tmpfs**, e la prescrizione **non sposta un byte**. Anche `~/.cache/sonda-vp9/`
e `/tmp/sonda-vp9/` sono la stessa cartella, non due copie.
⇒ Il banco mette i profili in `banchi/03-palco-profili/`, su `/dev/sda2` (178 G liberi), e
li cancella a fine giro. Stampa i megabyte liberi di tutt'e due i filesystem nella scena,
e li ristampa dentro il messaggio d'errore quando la pagina non risponde — **cosi' un
disco pieno non riesce a farsi passare per un guasto della pagina.**

**2. ⛔ 15 MB di file derivati sono finiti in un commit, e non nel mio.** Avevo messo tre
flussi derivati (`hevc.265`, `h264.264`, `vp9.ivf`, 15,7 MB) in `banchi/03-palco-lavoro/`
per provare gli spezzatori **prima** di scriverli nel banco. Mentre lavoravo, il commit
`0a99177` («La riga che ha quasi deciso una sessione…») li ha **presi dentro**, insieme al
banco. Sono **derivati** — si rifanno con un `ffmpeg -c copy` — e per la regola che
`.gitignore` scrive gia' per `b4-registrazioni/` e `01-b12-copie/` («la fonte e' il
generatore, non i file binari») non dovevano entrare.
⇒ Li ho **cancellati dal disco**, e il coordinatore ha gia' committato la cancellazione
(`290d92d`, «I quindici mega che il coordinatore ha committato per distrazione»): **non sono
piu' tracciati**. **La versione finale del banco non ne ha bisogno**: deriva i flussi **in
memoria** con `ffmpeg … pipe:1` e non scrive nessun file.
⚠ Restano pero' dentro la **storia** di `0a99177`: il peso del clone non torna indietro con
una cancellazione, e quello lo decide chi puo' riscrivere la storia — non io.

**3. ⚠ `M banchi/03-b17-ritardo.py` (+103 righe) non e' mio.** Un altro banco stava
lavorando sullo stesso albero mentre giravo. Non l'ho toccato, e HEAD si e' mosso sotto di
me da `7370682` a `868c265` durante la sessione. **Se qualcuno legge un `git status`
sporco, quella riga non e' di B0.**

**4. Il primo taglio era per NAL, e non contava niente.** Spezzare sui soli start code da'
4-5 pezzi per fotogramma e il decodificatore non ne cava un `VideoFrame`. Il confine giusto
e' l'**unita' d'accesso**. E' esattamente il modo in cui un banco cieco avrebbe risposto
«HEVC: no» con la faccia seria — la ragione per cui i controlli positivi passano per lo
stesso codice.

**5. ⚠ AV1 non esce dal codificatore hardware, e la sua riga ha una scena DIVERSA dalle
altre.** `av1_vaapi` su questa macchina da' «No usable encoding profile found» (gia'
misurato da `03-palco-codificatori`). `av1-ivf` e' quindi un **transcode software**
(`libsvtav1 preset 10 crf 40`) **dal file h264**, non un flusso del codificatore del
server. Vale come controllo positivo del decodificatore; **non** vale come misura del
codificatore.

**6. ⚠ Collisione di porta possibile con `03-palco-codec.py`.** Quel banco usa la **8899**,
che sta dentro l'intervallo 8890-8899 assegnato a me. Con 5 giri arrivo alla 8894 e non si
toccano, ma **un giro da 10 arriverebbe sulla 8899**. Chi allunga i giri lo sappia.

**7. Negli esiti ci sono 12 righe mie, e vanno lette le ULTIME TRE.** `>>` e mai `w`,
neanche a mano: percio' ci sono anche i due giri di rodaggio (`"giri":1`) e due tornate
intermedie, tutte vere e tutte riuscite, ma piu' povere. **Le righe buone sono le tre in
coda**, le uniche che hanno `av1-ivf` dentro `fotogrammi` **e** i campi `ms` e
`formato_fotogramma`. I numeri di questo rapporto vengono da quelle tre e solo da quelle.
⚠ Le tornate precedenti **concordano** su tutti i verdetti: nessun esito e' cambiato
aggiungendo AV1 o i tempi.

**Porte protette**: `7448 · 7501 · 7561` contate **prima e dopo ogni giro**, e la conta sta
dentro ogni riga di esito (`porte_protette_prima` / `porte_protette_dopo`). **Nessuna in
ascolto ne' prima ne' dopo, in nessuno dei giri.** Nessun `alert`/`confirm` nella pagina.

---

## Che cosa resta `[?]`

1. **`[?]` HEVC Main10 attraverso il vero anello del prodotto.** Qui i chunk arrivano
   **gia' spezzati in Python, da un file completo, su localhost**. Il prodotto li ricevera'
   **dalla rete, a pezzi, in tempo reale**, e chi spezza sara' il **client**. Quel che e'
   chiuso e' «il decodificatore accetta e conta»; **non** «il nostro impacchettatore
   produce chunk che il decodificatore accetta».
2. **`[?]` HEVC su una GPU che non sia questa.** Tutte le misure sono su **una sola**
   macchina, ADL-N con Mesa. Il si' e' di questo silicio e di questo driver.
3. **`[?]` `--disable-gpu` non e' «niente GPU».** Il controllo negativo dice che con la
   bandiera HEVC sparisce, e questo basta a mostrare che il banco distingue. **Non** dice
   che HEVC sparisce su una macchina **senza** GPU: sono due scene diverse, e quella non e'
   stata montata.
4. **`[?]` la latenza per fotogramma.** I 171-181 ms sono per **120 fotogrammi tutti in
   fila**, dati al decodificatore il piu' in fretta possibile. Non e' la latenza da chunk a
   `VideoFrame`, che e' la cosa che il prodotto sentira'. Serve un banco diverso.
5. **`[?]` HEVC in Firefox.** Misurato solo che **non** c'e'. **Non** ho provato se una
   preferenza (`media.hevc.enabled` o simili) lo accende. Se la corsia D ha bisogno di
   Firefox, questo va guardato prima di dare HEVC per perduto.
6. **`[?]` `03-palco-dipinge.py` esce sempre 0.** Il suo `main()` fa `return 0` qualunque
   cosa sia successo — anche se un flusso da' zero fotogrammi. Non l'ho toccato (il mandato
   dice che non va rifatto), ma **le sue righe di esito non hanno mai avuto un rosso capace
   di fermare qualcuno**, ed e' un quarto banco della stessa famiglia dei tre che sono
   costati una giornata.
