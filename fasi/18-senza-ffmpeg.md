# Fase 18 — REMOTIX senza ffmpeg

*Aperta dall'utente il **30 settembre 2026** (`DECISIONI.md` §10.22, §10.25). Nasce dalla licenza: REMOTIX sarà
sotto **PolyForm Noncommercial**, incompatibile con la libavcodec **GPL** delle distribuzioni. Togliendo ffmpeg
tutte le dipendenze di REMOTIX diventano permissive (MIT, BSD, Apache).*

## 1. Che cosa fa ffmpeg oggi, e con che cosa si sostituisce

| lavoro | oggi | domani | licenza |
|---|---|---|---|
| codifica sulla scheda | `h264_vaapi`, `hevc_vaapi` (libavcodec) | **libva diretta** (parametri, buffer, intestazioni del flusso scritte da REMOTIX) | MIT |
| ripiego software | `libx264`, `libx265`, `libsvtav1` | **OpenH264** (H.264), **SVT-AV1** diretta (AV1); ⛔ niente HEVC software | BSD |
| audio | encoder Opus via libavcodec | **libopus** diretta | BSD |
| conversione dei colori | libswscale | sulla scheda (VPP di VA-API); nel ripiego una libreria permissiva (libyuv) o codice nostro | BSD |

## 2. La condizione: indistinguibile, misurato

Il cambio entra **solo** se:
- la **suite funzionale della fase 15** completa è verde sulle **4 scatole** (GNOME, KDE, XFCE, LXQt) **in
  parallelo**, coi browser veri, in 4K;
- ~~la campagna della fase 16~~ — ⛔ **tolta** dall'utente il 30 set: *«eliminiamo i test di performance, sono
  troppo dipendenti dall'hardware»*; resta (🔸 proposta, da confermare) il **confronto relativo** del codificatore
  sulla stessa macchina e sulle stesse immagini, vecchio contro nuovo: tempo per fotogramma, dimensione, qualità
  (PSNR/SSIM) — il nuovo non dev'essere peggio del vecchio;
- il flusso che arriva al browser è dello stesso tipo di oggi (profili, livelli, intestazioni): la pagina non
  cambia.
Se non ci arriva: resta ffmpeg, e la licenza si riapre.

## 3. Le linee di lavoro, in parallelo

- **Linea V (video)**: libva diretta per H.264 e HEVC sulla scheda; OpenH264 e SVT-AV1 per il ripiego; la
  scelta del codificatore invariata per il browser.
- **Linea A (audio e colori)**: libopus diretta; la conversione dei colori senza libswscale.
- Poi: le prove (§2), l'installatore adeguato (niente libavcodec nelle dipendenze; su openSUSE con Intel
  Packman non serve più; Fedora continua a chiedere RPM Fusion per i driver), **T10** della fase 17.

## 4. Il registro delle modifiche — per il manuale tecnico

| commit | che cosa | perché | misura | installata |
|---|---|---|---|---|
| `1db22a3` `acf4698` | linea A: l'audio con **libopus diretta** (`src/audio.c`), senza libavcodec; complessità 10 e VBR non vincolato scritti esplicitamente (erano i valori dell'involucro di ffmpeg, diversi dal predefinito di libopus) | licenza (§10.22) | `[M]` banco `banchi/18-a1`, 42 s di segnale misto: pacchetti **identici byte per byte** al vecchio, 0 campioni diversi su 4 032 000 in decodifica; Chrome 154 col decodificatore WebAssembly della pagina: 1 860 pacchetti, 0 rifiutati. ⚠ Prodotto intero col browser non ancora provato (lo fa la suite) | no |
| `77141de` | **Linea V-scheda: la codifica sulla scheda con libva DIRETTA** — `src/vadiretta.c/.h` (configurazione, parametri di sequenza/immagine/slice, CQP e QVBR col tetto, le intestazioni SPS/PPS/VPS/slice/SEI scritte bit per bit con `src/scrittore_bit.c`, il giro begin/render/end, i byte codificati); `src/codificatore.c` apre la scheda con vadiretta (stesso nodo, stessa regola dell'entrypoint, stessa VPP della copia zero), la strada dalla memoria carica i BGRx in una superficie RGB e converte con la VPP (niente libswscale sulla scheda), la cornice di D-023 è riscritta sui bit (niente `hevc_metadata`), i byte consegnati sono nostri; il ripiego SOFTWARE (libavcodec) resta dietro il confine `RipiegoSoftware`/`sw_*` per la linea del ripiego. `h264_vaapi`/`hevc_vaapi` restano i NOMI della strada della scheda (figlio.c, `--prova-codifica`). Makefile: `libva-drm` | §10.22/§10.25: PolyForm Noncommercial e libavcodec GPL non stanno insieme; la scheda era l'unico posto in cui libavcodec faceva qualcosa che libva non fa da sola | `banchi/18-scheda/18-confronto.sh` sul server, 30 set: 120 fotogrammi di desktop finto (testo, finestre, scorrimento, trascinamento), H.264 / HEVC 8 / HEVC 10, 1080p e 4K, Intel (iHD 25.2.3, EncSliceLP) e Radeon (radeonsi 25.0.7, EncSlice), vecchio (libavcodec, `545ec55`) contro nuovo. **Copia zero: identici** — PSNR/SSIM uguali alla sesta cifra, byte uguali (±2 in H.264 = la stringa del SEI), `ffprobe` identico (profilo, livello 4.2/5.2 H.264 e 4.0/5.0 HEVC, colore 709 tv), 120/120 decodificati, tempi di codifica uguali (es. Intel H.264 1080p 2118 → 2113 µs, HEVC 4K 7368 → 7340 µs); chiave a richiesta, tela nuova a metà, tetto (QVBR 20 Mbit): identici. **Strada dalla memoria: il nuovo è uguale alla copia zero, cioè PEGGIO del vecchio** che convertiva in CPU con swscale: Intel 1080p H.264 PSNR 38,9 → 37,9 dB e +82 % di byte, HEVC 44,3 → 40,4 dB e +255 %; a 4K −0,1/−0,2 dB e byte uguali; Radeon −1 … −6 dB (la VPP di Mesa perde sul croma anche sulla copia zero, vecchia e nuova). La preparazione del fotogramma dalla memoria è più veloce (Intel 1080p 4602 → 2734 µs; 4K 18620 → 9036). Il banco D-023 (`16-d023-cornice.sh`): Intel 8 PASS, Radeon la cornice scatta e il flusso dichiara la tela (il PSNR sotto 40 sulla Radeon è la VPP, non la cornice) | no |
| `1186271` + questo | **Le altre prove della linea V-scheda** (30 set): `banchi/18-scheda/18-decodifica-chrome.sh` — Chrome 154 headless sul server decodifica con WebCodecs (la strada della pagina: Annex-B → `EncodedVideoChunk` → `VideoDecoder`) i 28 flussi H.264 vecchi e nuovi: **120/120 tutti, impronte dei pixel UGUALI** su copia zero, chiave a richiesta, tela nuova, tetto (10 PASS); le 4 coppie «memoria» decodificano 120/120 ma le impronte differiscono, com'è atteso (l'immagine è convertita dalla VPP e non da swscale); i 22 HEVC restano **non provati in Chrome**: headless senza GPU non ha HEVC in nessuna combinazione di flag (`isConfigSupported` falso per vecchio e nuovo) — per HEVC vale ffmpeg (120/120) più l'identità dei byte. `cmp` byte per byte sulla copia zero: HEVC 8 e 10 Intel, HEVC 8 Radeon 4K, tetto, chiave **IDENTICI**; HEVC 10 Radeon 1080p un byte in più al byte 92: davanti allo slice IDR il codice d'inizio è `00 00 00 01` invece di `00 00 01` (VPS/SPS/PPS identici alla traccia; tutt'e due le forme sono Annex-B legale e `annexb_prossimo()` e Chrome le leggono entrambe), H.264 ±2 byte = la stringa del SEI. Il prodotto intero costruito dal mio albero con `src/costruisci.sh` dentro `enter.sh` (marca dentro il binario OK): `--prova-codifica` ⇒ `{"esito":"hardware","codificatore":"h264_vaapi","nodo":"/dev/dri/renderD128", …, avc1.640c15, 1583 byte}`; acceso sulla porta **7611** con ban-file e socket propri: pagina servita (200, 874 KB), spento pulito; una sessione con desktop non è stata provata (niente utente con desktop fuori dalle scatole) | la condizione di §2 pretende il browser vero e il prodotto intero, non solo il banco | Chrome: 10 PASS, 4 «diverse per costruzione», 22 non provabili qui; prodotto: parte, codifica in hardware, serve la pagina | no |
