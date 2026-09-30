# Fase 18 — REMOTIX senza ffmpeg

✅ **CHIUSA il 30 settembre 2026**: suite della fase 15 verde sulle 4 scatole (673/673 in hardware, 80/80 di fumo
in software); il prodotto non collega più libavcodec, libavutil né libswscale. Unita in `fase-10-cure` (`13ccabd`).
Prossimo passo: T10 della fase 17 sul prodotto senza ffmpeg.

*Aperta dall'utente il **30 settembre 2026** (`DECISIONI.md` §10.22, §10.25). Nasce dalla licenza: REMOTIX sarà
sotto **PolyForm Noncommercial**, incompatibile con la libavcodec **GPL** delle distribuzioni. Togliendo ffmpeg
tutte le dipendenze di REMOTIX diventano permissive (MIT, BSD, Apache).*

## 1. Che cosa fa ffmpeg oggi, e con che cosa si sostituisce

| lavoro | oggi | domani | licenza |
|---|---|---|---|
| codifica sulla scheda | `h264_vaapi`, `hevc_vaapi` (libavcodec) | **libva diretta** (parametri, buffer, intestazioni del flusso scritte da REMOTIX) | MIT |
| ripiego software | `libx264`, `libx265`, `libsvtav1` | **OpenH264** (H.264), **SVT-AV1** diretta (AV1); ⛔ niente HEVC software | BSD |
| audio | encoder Opus via libavcodec | **libopus** diretta | BSD |
| conversione dei colori | libswscale | sulla copia zero la VPP della scheda (com'era); dalla memoria e nel ripiego **codice nostro** (`src/colori709.c`, BT.709 limitato, SSE2) — ⛔ non libyuv, che non ha la matrice 709; ⛔ non la VPP dalla memoria, misurata peggio | nostro |

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
| fc19168 | installatore e pacchetti senza ffmpeg: catalogo (seq. 8) coi driver VA **per fornitore** (Fedora: RPM Fusion — Intel `intel-media-driver` dal ramo **nonfree**, AMD `mesa-va-drivers-freeworld`; openSUSE: Packman **solo AMD** (`Mesa-dri`, `Mesa-libva`); Alma: Intel da RPM Fusion nonfree, AMD niente), deposito nuovo «openh264» (Cisco) e EPEL su Alma come depositi di REMOTIX stesso (D5), preflight senza libavcodec (OpenH264 vero contro `noopenh264`), `.deb`/`.rpm`/PKGBUILD con OpenH264, SVT-AV1, libopus e libyuv su una riga sola | via la libavcodec GPL (§10.22); i driver con H.264 sono l'unica cosa che resta di terzi | `[M]` 30 set, immagini podman: Debian 13 tutto in main; Ubuntu 26.04 OpenH264 e SVT-AV1 in universe; Fedora 44 `openh264` da `fedora-cisco-openh264` acceso di serie; Alma 10 `openh264` 2.5.1 (so.7) solo da `epel-cisco-openh264` (da aggiungere; firma EPEL verificata), SVT-AV1 in EPEL, **libyuv assente**; Leap 16/TW `libopenh264-8` vero da `repo-openh264`, in repo-oss la copia vuota; iHD ufficiale di openSUSE completo (classi AVC come RPM Fusion), Mesa ufficiale senza h264/h265; `go test ./...` verde | no |
| (questo commit) | **L'INTEGRAZIONE: REMOTIX senza ffmpeg** — (1) `codificatore.c` innesta il ripiego di `ripiego.c` al posto di libavcodec: `sw_apri`→`ripiego_apri`, `sw_codifica`→`ripiego_codifica`, il cambio di qualità (`abbassa`/`risali`) passa da `cambia_qualita()`→`ripiego_qualita` (H.264 a caldo), `codificatore_ridimensiona`→`ripiego_ridimensiona`; tutto il resto delle cure resta (16 MiB, scala, risalita, `forma_va_bene`, confessione dall'SPS, cornice D-023). (2) **La strada dalla memoria torna quella di prima**: conversione in CPU con `colori709_a_nv12`/`_a_p010` nell'appoggio e caricamento dei piani con `vadiretta_carica_nv12`/`_p010` (vaDeriveImage/vaPutImage); via la superficie RGB e la VPP dalla memoria. La copia zero non si tocca. (3) **HEVC in software mai**: `figlio.c` `codificatore_di()` con `hevc_vaapi` chiuso torna NULL con la ragione; **l'elenco dei codec dell'`ECCOMI` è misurato all'avvio** (`figlio_capacita_video()`, in un processo a parte: «hevc» solo se la scheda lo codifica, «h264» se scheda o OpenH264 VERO, «» se niente ⇒ ogni CIAO in NIENTE_IN_COMUNE, dichiarato con il rimedio per la distro — `rcp_video_codec_imposta()`, `banchi/rcp` allineato); `--prova-codifica [h264\|hevc] [--nodo N] [--software]` con le chiavi JSON in più `codec`, `offerti`, `hevc`, `h264`, `rimedio`. (4) **Via ffmpeg**: nessun `#include <libav…>`, `Makefile` senza `-lavcodec -lavutil -lswscale` (OpenH264 solo `--cflags` + `-ldl`, `SvtAv1Enc` collegata, `MINIMI` e intestazioni aggiornati), `src/Contenitore` e gli otto `costruzione/Contenitore.*` con `openh264`/`svt-av1`/`opus` per distro, `costruisci-tutti.sh` rifiuta un `ldd` con libav; `ripiego.c` con le guardie per SVT-AV1 3.x e 4.x (`svt_av1_enc_init_handle` a due argomenti, niente `color_description_present_flag`, `EbSvtIOFormat` solo piani; dalla 4.0 `aq_mode` e `LOW_DELAY`). (5) `banchi/18-scheda/18-confronto.sh` costruisce il nuovo con `ripiego.c`/`colori709.c` e rifiuta simboli `av_`; `18-software-confronto.sh` si rilancia con `bash "$0"` | §10.22/§10.25; decisione dell'utente (30 set): senza scheda e senza OpenH264 vero AV1 NON rientra — si dichiara, col rimedio | `[M]` 30 set 2026, server (i5-13500T, Intel UHD 730 iHD 25.2.3 + Radeon RX 6800 radeonsi 25.0.7), albero integrato contro `545ec55`: **`18-confronto.sh` «nessuna prova in cui il nuovo sia peggio del vecchio»** — copia zero identica (PSNR/SSIM/byte uguali, ±2 byte del SEI), **strada dalla memoria tornata pari**: Intel 1080p H.264 38,926→38,925 dB e +0,2 % byte, HEVC 44,32→44,31, 4K ±0,02 dB; Radeon ±0,04 dB; la preparazione del fotogramma dalla memoria a metà tempo (Intel 1080p 4024→1964 µs, 4K 16720→7816); chiave, tela, tetto identici. **`18-software-confronto.sh`**: colori ±1 livello da swscale (PSNR minimo 73 dB Y, croma diverso ≤4 %), H.264 nuovo (OpenH264) contro corretto 1080p PSNR-Y 46,4 vs 43,3 dB · SSIM 0,99757 vs 0,99748, 4K 48,3 vs 43,9; AV1 nuovo vs vecchio 57,12 vs 57,21 e 56,51 vs 56,60 (stessi byte); rifiuti dichiarati (H.264 10 bit, >36 864 MB, senza perdita). **`18-a1`**: VERDE, 8400 blocchi identici byte per byte. **Prodotto** costruito sul server da questo albero: `ldd` senza libav*/libswscale/libx26x, `nm -D` 0 simboli `av_`/`sws_`; `--prova-codifica` ⇒ hardware su renderD128 (Intel, `avc1.640c15`, `hev1.1.6.L60.B0`) e su `--nodo renderD129` (Radeon), `--software` ⇒ `openh264` 1816 byte, `hevc --software` ⇒ «nessuno» col perché (codice 1); acceso sulla porta **7631** con ban-file e socket propri: pagina 200 (874 KB), all'avvio «video.codec offerti: «hevc,h264» — … software OpenH264 NO … ⇒ rimedio: apt install libopenh264-8» (l'host non ha la libreria: la dichiarazione funziona), spento pulito. Contenitori (`costruisci-tutti.sh`): Debian 13, **Fedora 44** (SVT-AV1 3.1.2, OpenH264 2.6.0 da fedora-cisco-openh264) e **Arch** (SVT-AV1 4.2.0) compilano senza avvisi, `ldd` pulito, e `--prova-codifica --software` dentro i due contenitori ⇒ `openh264`, 1816 byte, `avc1.640c15`; ⚠ la strada AV1 con SVT 3.x/4.x è compilata, non eseguita (nessun ferro con quelle versioni). ⚠ Non provato: una sessione con desktop e browser (la fa la suite sulle 4 scatole) | no |
| (questo commit, banchi) | **le scatole della suite come la macchina vera** — `banchi/11-scatole/Contenitore.{gnome,kde,xfce,lxqt}`: nella riga «le librerie del Makefile» `libopenh264-8 libsvtav1enc2 libopus0 libva-drm2` al posto di `libavcodec61 libavutil59 libswscale8` (ffmpeg resta nella scatola solo come attrezzo del cliente Python); nelle quattro scatole accese `libopenh264-8` 2.6.0 (1,1 MB, non la copia vuota) messo con apt, senza rifare le immagini | la suite della fase 15 (§2) deve provare il prodotto senza ffmpeg con l'ECCOMI che offre h264 anche in software | `[M]` 30 set 10:34: registro d'avvio di rete11-{gnome,kde,xfce,lxqt} col binario `4b39195c` (da `92caeb3`; il vecchio `4fb3287d` salvato in `rete11/prodotto/remotix.4fb3287d`): «OpenH264 2.6.0 aperto da libopenh264.so.8», «video.codec offerti nell'ECCOMI: «hevc,h264» — HEVC: scheda renderD128 · H.264: scheda si', software OpenH264 si'» | scatole |
| (questo commit) | **⭐ LA SUITE FUNZIONALE DELLA FASE 15 SUL PRODOTTO SENZA FFMPEG — VERDE** (§2, prima condizione): giro `18-suite` sulle quattro scatole in parallelo (rete11-gnome/kde/xfce/lxqt), Firefox 140.16.0 e Chrome 154.0.8037.57 veri, 3840x2160, 29 prove (F-001…F-032, F-018b/c, F-024b, F-031B, percorsi A-F, negative N-1 N-3 N-4) col guasto innestato, più lo strato tecnico (C7 C9 C18 C19 × 4, C14). Registro in `banchi/15-suite/registro.jsonl` (copia del server, solo aggiunte, 6994 righe), rapporto generato `banchi/15-suite/rapporto-giro18-suite.{txt,html}`, evidenze sul server in `/media/REMOTIX/misure/fase15/giro18-suite/` | il cambio entra solo se la suite completa è verde (§2) | `[M]` 30 set 10:36→12:51 UTC, 135 min, binario `4b39195c` (da `92caeb3`), pagina `fb9a18f3`, banchi `3ccbe10`: **673 PASS, 0 FAIL, 0 BLOCKED** — per scatola: 44 sane + 44 col guasto con Firefox, 36 + 36 con Chrome, 4 + 4 tecniche; C14 PASS. Codifica in HARDWARE (Intel iHD 25.2.3, `avc1.640c15`), ECCOMI «hevc,h264». ⇒ Nessun FAIL da confrontare col binario vecchio (`4fb3287d`, con ffmpeg, salvato in `rete11/prodotto/remotix.4fb3287d`) | scatole: `4b39195c` |
| (questo commit) | **Il giro di fumo in SOFTWARE** (OpenH264, la strada del prodotto su una macchina senza driver VA): giro `18-software-2`, F-001 F-002 F-003 F-004 F-013 (video, ~155-195 s), 4 scatole × Firefox e Chrome, col guasto. Modo: nelle scatole `iHD_drv_video.so` rinominato (⇒ «H.264: scheda no, software OpenH264 sì», ECCOMI «h264»), server riacceso con `11-accendi.sh server`; poi driver rimesso e server riaccesi in hardware. ⚠ `LIBVA_DRIVER_NAME` nell'ambiente del server NON basta: il figlio compone l'ambiente da zero (`execve`, CODER.md §4.5) e le sessioni del primo tentativo (`18-software`) codificavano in HARDWARE — quel giro non vale come prova software; il suo unico FAIL (F-003 kde/chrome, «foto vecchia» 1026-1409 ms contro il tetto di 1000 ms, passata sana; il guasto BLOCKED di conseguenza) è lo stesso banco che nel giro completo e in `18-software-2` è PASS col binario nuovo e che è PASS col binario vecchio `4fb3287d` sulla stessa scatola (`18-f003-kde-vecchio`): intermittente al limite del tetto, non della fase 18 | la suite completa passa solo dalla scheda; il ripiego software è la strada dichiarata per chi non ha il driver | `[M]` 30 set 13:11→13:26 UTC, 15 min: **80 PASS, 0 FAIL, 0 BLOCKED** (40 sane, 40 guasti visti); nel registro di ogni scatola tutte le sessioni «in software» (8 su gnome/kde, 16 su xfce/lxqt), 0 «COPIA ZERO in vigore». Rapporto `banchi/15-suite/rapporto-giro18-software-2.{txt,html}` | scatole: `4b39195c`, driver rimesso |

## 5. Le misure rifatte — dopo la fase 18 (1 ottobre 2026)

*Decisione dell'utente (1 ott): «l'abbandono di ffmpeg ha invalidato una serie di misure di performance
misurate con il precedente sistema che devono essere rifatte. Quindi bisogna far rigirare, almeno
parzialmente, la suite dei test di performance». Le cifre stanno SOLO qui; nel diario storico, accanto a
ogni misura tolta che qui è rifatta, c'è un rimando a questa sezione. ⛔ Nessuna cifra nei quattro documenti
del prodotto.*

**La macchina, per tutte le cifre di §5**: server i5-13500T (20 fili, 31 GB), Intel UHD 770 (`8086:4680`,
`i915`, iHD 25.2.3, EncSliceLP), Radeon RX 6800 (`1002:73bf`, `amdgpu`, radeonsi Mesa 25.0.7) — Debian 13,
kernel 7.0, libva 2.22.0; i browser VERI **sul server** in 4K (3840×2160) nei compositori annidati (`labwc`
0.8.3 senza schermo): Firefox ESR 140.16.0, Chrome 154.0.8037.57; il prodotto nelle scatole `rete11-*` =
binario **`4b39195c`** (da `92caeb3`: ⭐ è il binario di `fase-10-cure` di oggi, `src/` non è cambiato da
allora), pagina `fb9a18f3`.

### 5.1 L'inventario: che cosa i commit «da unire solo a suite verde» hanno tolto, e che cosa si rifà

Letti i 34 diff dei commit «📋 fase 18 (da unire solo a suite verde)». Due ondate: la prima (30 set
10:56-11:11) ha tolto TUTTE le cifre di prestazione per la regola «le cifre vanno in git» (§10.26) — quelle
restano valide e **non si rifanno** (scheda con copia zero, cattura sola, filo, audio, ammissione, avvii,
rete cattiva, capacità della fase 16); la seconda (12:32-12:48) ha tolto le misure **invalidate** dal
cambio. Sono queste, raggruppate in insiemi:

| insieme | che cosa misurava (documento · sezione · cifra vecchia) | banco d'origine | ha senso oggi? | che cosa si fa |
|---|---|---|---|---|
| **S — la codifica SENZA scheda** (libx264 / libx265 / libsvtav1 via libavcodec) | DECISIONI §1.13-bis `libsvtav1` preset 10 **22,23 ms/fot** a 1080p (contro hevc_vaapi 3,16); fasi/10 §3.6 ripiego `libx265` **~22 ms contro ~3**; FASI §03 / DECISIONI §2.5 §7.8 / LEZIONI §6.2 / STUDI: la catena della fase 3 su Xvfb con AV1/HEVC in software — ritardo cattura→vetro **74,58 ms** (cattura→primo byte 39,17 = 53 %), tetto dipinti **127,6/s**, worker **+27,6 ms**, 23,93 fot/s; LEZIONI §5 SVT-AV1 a 962 **PSNR 43,3 dB**; RCP §5 / fasi/08 D.2 ripiego `libx264` a 8K **18,7 MiB** per chiave; fasi/09 §0.5 v1 R31 `libx264` 1 992 kbit/s; LEZIONI §0 v1 41→6 ms; §8 sws_scale a più fili 13,8/12,5 ms | `03-palco-codificatori.sh`, `03-b17-ritardo.py`, `03-b16-dipinti.py`, `03-b19-*` (Xvfb, cliente di allora, ffmpeg); `08-D2-ripiego.py` (ffmpeg); v1 | **in parte**: oggi il software è SOLO H.264 con OpenH264 (niente HEVC, niente AV1 come ultimo ripiego, 8K rifiutato: DECISIONI §10.26); la catena della fase 3 (Xvfb, senza desktop) non è più il prodotto | **rifatta** come catena intera coi browser veri in 4K con OpenH264 (§5.4: ritardo, fotogrammi, tempi di conversione e codifica per fotogramma dal registro del figlio) e come **capacità** (§5.5). La qualità OpenH264 contro x264 sta già in §4 (`18-software-confronto.sh`, 30 set: 1080p PSNR-Y 46,4 vs 43,3 dB) |
| **M — la scheda DALLA MEMORIA** (sws_scale + `av_hwframe_transfer_data`, poi la VPP dalla memoria) | fasi/08 agente C **21,61 ms** per fotogramma a 1080p (sws_scale 5,39 + caricamento 0,98), F4 prima/dopo **22,82 → 6,41 ms**; fasi/09 §13.6 §14.6 4K «conversione **11 466 µs** + codifica 8 895 = 20,4 ms ⇒ ~49/s», 2560×1080 6 652 + 3 827; fasi/10 §6.2 N=24 con **12,0 nuclei**, **6,0 nuclei** per dieci 1080p contro 0,7 in copia zero, `ffmpeg` libero 406,2 fot/s; §5.1 righe MEMORIA; §6.1 taratura del metro GPU con `hwupload` (12,68 % per 1080p30, retta 0,1968·Mpx/s); §6.6 e §6.10 lo studio del ferro con ffmpeg (875/852 fot/s, 24,6 → 50,2 W con la conversione, 1,8/1,47 Gpixel/s, CQP 876,8 / QVBR 816,0 / CBR 812,8); fasi/06 §4.9 `h264_vaapi` 1,6 ms e 5 940 byte; DECISIONI §1.13-bis i `*_vaapi` 3,11-7,28 ms via `hwupload`; RCP §5.2 `-bf 1` −16 % e 67 ms | `08-c-*`, `08-f4-*` (**mancano** in `banchi/`), `10-b88-saturatore.py --strada memoria` (lega libavcodec), `10-b87-metro-gpu.py`, `10-b94-ferro-carico.py`, `03-palco-codificatori.sh` (tutti ffmpeg) | **sì per la strada del prodotto** (oggi: `colori709.c` in CPU + `vaPutImage`), **no per lo studio del ferro con ffmpeg** (misurava ffmpeg, che non c'è più; i contesti 2048/1021 e `vaQueryProcessingRate` restano validi perché di libva) | i banchi originali non girano più (mancano o legano libavcodec): il sostituto è **`banchi/18-scheda/18-confronto.sh`**, già eseguito il 30 set (§4): preparazione dalla memoria **1080p 4 024 → 1 964 µs, 4K 16 720 → 7 816 µs**, qualità pari (±0,02 dB). In più, qui: i tempi di conversione per fotogramma a 4K col binario nelle scatole (§5.4, la riga `TRATTO` del figlio) |
| **C — le catene intere prese su binari che passavano da quelle strade** (fase 4, 6, 7, 8; e la fase 3) | FASI §04 O2 mano→pixel **139,40 ms**; fasi/08 §1.4, A/B/F1/F2: `input → vetro` **99,07 → 89,86 → 55,20 ms**, distacco **0,27 → 0,16 barre**, F2 70,5 ms; fasi/06 §4.2 §4.8 §5.6 §5.9 (tela girata 4-6 ms, Mutter 32-39, giro `ADATTATA` 42-44, `SESSIONE`→1° fotogramma 14-335 ms), §5.8 contesa con 5 ffmpeg; fasi/07 §8 (audio→video ~400 ms, AV mediana 236 ms), §8-ter netem, §8-quater | `04-b30-anello-input.py`, `08-b67-elastico.py` (portatile + tablet dell'epoca: non riproducibili come allora), `06-b35-tempi.py`, `06-b41-contesa.sh` (ffmpeg), `07-b61-*` | **sì, ma col metro di oggi**: la catena intera in 4K coi browser veri è quella della fase 16 (`16-salita.py`, `16-classifica.py`: ritardo del prodotto p95, giro dell'eco, dipinti/saltati, nascita), presa il 26-27 set col binario `45d048c8` **con ffmpeg** in copia zero | **rifatta** con lo stesso banco della fase 16 e il binario nuovo: gradino 1 in HARDWARE sui 4 desktop (§5.3), da confrontare riga per riga con `intel-b-4k-<desktop>/livello-01`. Le cifre del portatile/tablet (barre, 139,40 ms) non si rifanno: era un altro cliente e un'altra rete |
| **K — quante sessioni regge il server SENZA scheda** | mai misurato: la fase 16 è tutta in hardware | `16-salita.py` | **sì** (misura nuova chiesta dall'utente) | §5.5: `--senza-scheda` (adattamento dichiarato in §5.2), 4K, i 4 desktop, soglie §9 della fase 16 |
| **non più sensate** | HEVC in software (`libx265`: fasi/10 §3.6, RCP §6.2 CRF, fasi/08 D.2) — il prodotto non lo fa più; AV1 in software come ultimo ripiego; 8K in software (OpenH264 rifiuta oltre 4096×2304, dichiarato); lo studio del ferro **con ffmpeg** (fasi/10 §6.1, §6.6, §6.10 parte ffmpeg); le misure di v1 | — | no | niente: restano tolte |
| **da riconfermare, non da rifare** (segnalazione) | fasi/16-a3 e 16-stress A3: sulla Radeon gruppi di 5 fotogrammi da ~31 ms ogni 12-40 s, localizzati «dentro `avcodec_send_frame`» — copia zero, quindi valide per §10.26, ma la chiamata non esiste più | `16-salita.py --scheda amd` | sì, un gradino 1 su KDE 4K basta a vedere se i gruppi ci sono ancora | §5.6, se il tempo lo consente |

⚠ **Incoerenze trovate nei diff, da decidere (non toccate qui)**: la seconda ondata ha lasciato in FASI §04
(O2 139,40 ms, clic 136 → 41 ms), LEZIONI §1.26 (17,48 ms), §1.28/§1.33 (0,47 barre) e DECISIONI §1.13-bis
(i `*_vaapi` 3,11-7,28 ms via `hwupload`) cifre prese su binari dalla memoria/sws_scale, che per il criterio
di `f3acbe8` (fasi/08) andrebbero via anch'esse. E `banchi/10-b92-scene.py`, citato in fasi/10 §6.12, non è
nel deposito; i banchi degli agenti C, F1, F4 e A della fase 8 (`08-c-*`, `08-f1-*`, `08-f4-*`) nemmeno.

### 5.2 Prima delle misure: le scatole rifatte come la macchina vera

Decisione dell'utente (1 ott): le 4 scatole della suite si ricostruiscono dalle ricette attuali
(`banchi/11-scatole/Contenitore.*`, senza libavcodec), perché quelle accese avevano immagini di 8 giorni con
ffmpeg dentro e `libopenh264-8` messo a mano.

**Le versioni, prima e dopo** (`[M]` 30 set 19:35 e 19:47 UTC; dpkg dentro le scatole e sull'ospite):

| pacchetto | scatole vecchie (immagini del 22-24 set) | scatole nuove (1 ott) | ospite |
|---|---|---|---|
| `intel-media-va-driver` (iHD) | 25.2.3+dfsg1-1 | **uguale** | 25.2.3+dfsg1-1 |
| `libva2` / `libva-drm2` | 2.22.0-3 | uguale | 2.22.0-3 |
| `mesa-va-drivers`, `libgl1-mesa-dri` | 25.0.7-2+deb13u1 | uguale | 25.0.7-2+deb13u1 |
| `libigdgmm12`, `libvpl2` | 22.7.2+ds1-1, 2.14.0-1+b1 | uguale | uguale |
| `libopenh264-8`, `libsvtav1enc2`, `libopus0` | 2.6.0+dfsg-2 (a mano), 2.3.0+dfsg-1, 1.5.2-2 | uguale (dalla ricetta) | — / 2.3.0 / 1.5.2 |
| `firefox-esr` (dentro la scatola: il browser degli utenti «A» della salita e di C8) | 140.16.0esr-1~deb13u1 | ⚠ il deposito `trixie-security` dà ora **153.4.0esr**: ⇒ **fissato alla 140.16.0esr** dal .deb dell'ospite (`/media/REMOTIX/cache/apt-host`), `apt-mark hold` | 140.16.0esr |
| `google-chrome-stable` (ospite: i browser della suite e degli attori) | — | — | 154.0.8037.57-1 |
| desktop: `gnome-shell` 48.7-0+deb13u2 · `kwin-wayland` 6.3.6-1 · `plasma-workspace` 6.3.6-2 · `labwc` 0.8.3-1 · `xfce4-session` 4.20.2-2 · `lxqt-session` 2.1.1-1 · `pipewire` 1.4.2-1 · `xwayland` 24.1.6-1 | | tutti uguali | |
| kernel dell'ospite (= delle scatole) | 7.0 | 7.0 | 7.0 |
| `ffmpeg` (programma, attrezzo dei banchi C2/C3/C8b) e con lui `libavcodec61` 7.1.5 | presenti | presenti (la ricetta lo tiene come attrezzo; il prodotto non lo collega: `ldd` senza libav) | presenti |

⇒ La sola differenza rispetto alle scatole delle misure precedenti sarebbe stata Firefox 140 → 153 dentro
la scatola: **evitata** fissando il pacchetto. Driver, libva, Mesa e browser della suite sono **identici**.
Modifiche alle ricette (in questo ramo): `Contenitore.{gnome,kde,xfce,lxqt}` blocco 4-ter installa
`firefox-esr` dal .deb dell'ospite (`COPY pacchetti/…`) e lo mette in `hold`; `11-accendi.sh costruisci` copia
il .deb dalla cache nel contesto e si ferma se manca. `nictest:nictest` (sudo, video, render) c'è in tutt'e
quattro, LXQt compresa. Il binario dentro resta `4b39195c`, pagina `fb9a18f3`; all'avvio ogni server dice
«video.codec offerti nell'ECCOMI: «hevc,h264» — HEVC: scheda renderD128 · H.264: scheda si', software
OpenH264 si'».

**Il giro di fumo sulle scatole nuove** (`[M]` 30 set 19:48→20:02 UTC, giro `18-scatole-nuove`: F-001/F-002,
F-003, F-004, F-013 col guasto, 4 scatole in parallelo × Firefox e Chrome): **75 PASS, 1 FAIL, 4 BLOCKED**
su 80; tutte le sessioni in HARDWARE (38 «in HARDWARE», 0 in software nei registri). I cinque rossi —
xfce/firefox F-013 («nessun pixel cambia», e il guasto BLOCKED di conseguenza), gnome/chrome e xfce/chrome
F-004 («la fotografia: nessuna risposta dal browser in 25 s»), lxqt/chrome F-013 guasto — **rifatti uno alla
volta** (giro `18-scatole-nuove-r`, 21:01→21:10): **8 PASS su 8**. Come nel giro del 29 set (fase 16 §17.1,
D-022): sono i rossi del parallelismo a quattro scatole sulla stessa macchina, non delle scatole. ⇒ Le
scatole nuove funzionano; da qui le misure, una configurazione alla volta.

### 5.3 Insieme C — la catena intera in HARDWARE col binario nuovo (gradino 1, 4K, i 4 desktop)

`[M]` 30 set 21:11→22:04 UTC, campagne `f18hw-4k-<desktop>` (`banchi/16-stress/16-coda.sh f18hw` con
`REMOTIX_16_IN_PIU="--gradini 1 --minuti 10 --minuti-ultimo 10"`: lo stesso banco della fase 16, un
gradino solo da 10 minuti, una configurazione alla volta, server vuoto e `uptime` letto dalla salita
stessa — carico 0,8-1,3 a 1 utente). Utente 1 = profilo A (Firefox 140 vero in 4K, che naviga nella
sessione), più il controllo corto (u99, Firefox) negli ultimi 2 minuti; classifica di `16-classifica.py`,
soglie §9 della fase 16. Il «vecchio» è `intel-b-4k-<desktop>/livello-01` del 26-27 set: **stesso banco,
stessa macchina, stesse versioni** (§5.2), binario `45d048c8` **con ffmpeg** (`h264_vaapi` via libavcodec,
copia zero). Evidenze: `/media/REMOTIX/misure/fase16/f18hw-4k-*/livello-01/`, registro
`banchi/16-stress/registro.jsonl` sul server.

| 4K, 1 utente (Firefox), per sessione | GNOME vecchio → **nuovo** | KDE vecchio → **nuovo** | XFCE vecchio → **nuovo** | LXQt vecchio → **nuovo** |
|---|---|---|---|---|
| classe del livello | GREEN → **GREEN** | GREEN → **GREEN** | GREEN → **GREEN** | GREEN → **GREEN** |
| ritardo del prodotto p95 (classifica; tetto 50) | 33,2 → **35,3 ms** | 39,6 → **38,7** | 36,4 → **36,1** | 36,2 → **36,6** |
| NOSTRO (copia → byte fuori) p95 dei p95 · mediana | 24,2 · 17,0 → **26,3 · 16,9** | 30,6 · 19,3 → **29,7 · 19,1** | 27,4 · 22,0 → **27,1 · 22,1** | 27,2 · 21,9 → **27,6 · 22,1** |
| giro dell'eco (tasto → fotogramma, pagina) p95 | 55 → **51,6 ms** | 64,3 → **61,7** | 64,2 → **55,8** | 72,6 → **69,5** |
| TRATTO (mediane sull'anello di 512): totale · conversione (VPP) · codifica | 17,5 · 8,7 · 7,9 → **17,4 · 8,8 · 7,9** | 25,0 · 8,6 · 8,1 → **24,9 · 8,6 · 8,0** | 21,9 · 3,3 · 8,0 → **21,8 · 3,3 · 7,9** | 21,8 · 3,3 · 8,0 → **22,1 · 3,3 · 7,9** |
| primo fotogramma H.264 3776×2016: conversione · codifica (µs) | 12 290 · 9 303 → **12 063 · 9 136** | 13 734 · 9 736 → **13 058 · 8 703** | 14 571 · 9 569 → **12 017 · 8 576** | 15 170 · 9 020 → **11 420 · 8 502** |
| dipinti / consegnati · saltati · buchi | 799/799 · 0 % · 0 → **768/768 · 0 % · 0** | 1434/1434 · 0 · 0 → **1524/1524 · 0 · 0** | 579/579 · 0 · 0 → **567/567 · 0 · 0** | 730/730 · 0 · 0 → **690/690 · 0 · 0** |
| blocco più lungo dell'immagine | 0,061 → **0,056 s** | 0,065 → **0,068** | 0,068 → **0,063** | 0,068 → **0,073** |
| banda | 0,69 → **0,71 Mbit/s** | 0,95 → **1,01** | 0,30 → **0,31** | 0,62 → **0,61** |
| nascita di un utente nuovo (u99, accesso → primo fotogramma) · controllo corto | 2,44 s · GREEN → **2,63 · GREEN** | 2,26 → **2,25** | 2,06 → **2,07** | 1,64 → **1,67** |
| CPU nella finestra: recinto `remotix` · `sessioni` (nuclei) · macchina | 0,03 · 0,32 · 4,3 % → **0,03 · 0,33 · 4,2 %** | 0,05 · 0,36 · 5,0 % → **0,04 · 0,38 · 5,4 %** | 0,11 · 0,27 · 4,3 % → **0,11 · 0,27 · 4,5 %** | 0,09 · 0,29 · 4,4 % → **0,09 · 0,30 · 4,7 %** |
| GPU Intel nella finestra: render · video · video-enhance (%) | 13,4 · 4,1 · 7,0 → **13,0 · 4,1 · 7,2** | 40,8 · 11,2 · 18,8 → **41,1 · 12,1 · 18,8** | 11,1 · 3,3 · 1,9 → **10,8 · 3,2 · 1,9** | 13,0 · 3,8 · 2,2 → **13,0 · 3,8 · 2,2** |

⇒ **Indistinguibile**: ogni grandezza del nuovo sta dentro la dispersione del vecchio (ritardo ±2 ms, tratti di
conversione e codifica uguali al decimo di millisecondo, GPU uguale al punto percentuale); la catena intera
in hardware col binario senza ffmpeg è quella della fase 16, e le misure della campagna della fase 16
restano il riferimento. (Su GNOME e KDE la VPP converte da RGB, 8,6-8,8 ms; su XFCE e LXQt il compositore
wlroots dà già NV12 e la conversione è 3,3 ms con 5,3 ms di copia: com'era.) Il primo fotogramma di KDE
nel vecchio era HEVC (Chrome del controllo corto, 29 064 µs), nel nuovo l'ordine dei browser del controllo
corto è cambiato: non è una differenza del codificatore.

### 5.4 Insieme S — la catena intera SENZA scheda (OpenH264), 4K, 1 utente

`[M]` 30 set 22:04→23:28 UTC, campagne `f18sw-4k-<desktop>` (`16-coda.sh f18sw`, `REMOTIX_16_IN_PIU=
"--senza-scheda --minuti 10 --minuti-ultimo 10"`). **Adattamenti dichiarati del banco**: (1) `16-salita.py
--senza-scheda` — nella scatola rifatta, dopo `prodotto` e prima di `server`, `iHD_drv_video.so` è rinominato
(come nel giro di fumo di §4: `LIBVA_DRIVER_NAME` non basta, il figlio compone l'ambiente da zero), e la
salita **pretende** che il registro d'avvio dica «H.264: scheda no (/dev/dri/renderD128), software OpenH264
si'» — così è stato in tutt'e quattro; il compositore continua a disegnare sulla scheda (Mesa iris), è solo
la codifica a scendere in OpenH264 2.6.0, com'è per chi non ha il driver VA; (2) ogni livello dura 10 minuti,
anche l'ultimo (la regola «sessioni al massimo 10 minuti»). Tutto il resto è la salita della fase 16 (§6:
gradini 1 → 4 → 8 → 12 → 16, la regola di non-prosecuzione, la ripetizione, la ricerca a metà; §9: le soglie).
Utente 1 = profilo A (Firefox 140 in 4K); controllo corto negli ultimi 2 minuti.

**Il 4K in software cede già a 1 utente, sui 4 desktop**: il livello 1 è **DEGRADED significativo** (l'unica
sessione DEGRADED; su KDE anche oltre metà fascia), ripetuto una volta con lo stesso esito ⇒ la salita si
ferma (§6), «ultimo GREEN: nessuno». Non è un FAIL: nessun input perso, tutti i fotogrammi dipinti, nessun
buco, blocchi di 0,1 s; è il **ritardo** che sta fuori dal tetto dei 50 ms.

| 4K, 1 utente (Firefox), software OpenH264 — livello 1 e ripetizione | GNOME | KDE | XFCE | LXQt | (hardware, §5.3) |
|---|---|---|---|---|---|
| ritardo del prodotto p95 (tetto 50 GREEN, 150 FAIL) | **97,3 · 96,6 ms** | **123,9 · 115,2** | **86,9 · 92,3** | **111,5 · 94,9** | 35-39 |
| NOSTRO (copia → byte fuori) p95 dei p95 · mediana | 88,3 · 47,6 | 114,9 · 50,9 | 77,9 · 45,9 | 102,5 · 48,8 | 26-30 · 17-22 |
| giro dell'eco p95 (pagina) | 114,9 · 109,3 | 116,3 · 114,8 | 96,0 · 99,7 | 107,5 · 107,7 | 52-70 |
| TRATTO (mediane su 512): totale · conversione (`colori709`, CPU) · codifica (OpenH264) | 58,2 · 5,5 · **26,2** | 62,4 · 5,7 · **26,5** | 43,0 · 5,7 · **24,0** | 45,0 · 5,7 · **24,5** | 17-25 · 3,3-8,8 · 7,9 |
| primo fotogramma 3776×2016 (µs): conversione · codifica | 8 340 · 17 505 | 8 288 · 15 323 | 6 938 · 14 024 | 6 911 · 14 294 | 11-13 000 · 8 500-9 100 |
| dipinti/consegnati · saltati · buchi · blocco max | 653/653 · 0 % · 0 · 0,12 s | 868/868 · 0 · 0 · 0,13 | 418/418 · 0 · 0 · 0,11 | 483/483 · 0 · 0 · 0,11 | 0 % · 0 · 0,06-0,07 |
| banda | 0,46 Mbit/s | 0,52 | 0,20 | 0,39 | 0,3-1,0 |
| controllo corto (u99: nascita, F-004, F-007, F-003, F-014) | GREEN | GREEN | GREEN | GREEN | GREEN |
| CPU nella finestra: recinto `remotix` (nuclei) · macchina | **0,34** · 5,1 % | **0,68** · 7,4 % | 0,30 · 4,5 % | 0,32 · 4,8 % | 0,03-0,11 · 4-5 % |
| PSS del recinto `remotix` | 509 MB | 521 | 581 | 435 | 41-92 MB |
| GPU Intel: render · video · video-enhance | 14,4 · **1,0** · **0,0** % | 32,1 · 2,2 · 0,0 | 9,7 · 0,8 · 0,0 | 10,7 · 0,9 · 0,0 | 11-41 · 3-12 · 2-19 |

Letture: **la codifica di un fotogramma 4K in OpenH264 costa 24-26 ms** (mediana; 14-17 ms il primo, che è
una chiave) contro 7,9 ms della scheda; la conversione dei colori in CPU (`colori709.c`, SSE2) costa **5,5-5,7
ms** a 3776×2016, cioè *meno* della VPP della scheda su GNOME/KDE (8,6-8,8 ms) e poco più della strada NV12
di wlroots (3,3 + 5,3 di copia) — e nel vecchio (fasi/09 §13.6, `sws_scale`) il primo fotogramma 4K
costava 11 466 µs di conversione: **oggi 6 900-8 300**. Il motore video della scheda sta a ~1 % (è il browser
che decodifica) e il video-enhance a 0: la scheda non codifica. Il recinto `remotix` passa da 0,03-0,11 a
**0,3-0,7 nuclei** per una sessione 4K, e da 40-90 a **430-580 MB** di PSS (i buffer di OpenH264 a 4K).
⇒ Per il prodotto: **senza scheda il 4K non sta nel tetto dei 50 ms nemmeno con un utente**; la capacità
va cercata alle misure più basse (§5.5). Contro la fase 3 (74,58 ms cattura→vetro con libsvtav1/libx265 a
1080p su Xvfb): non confrontabile numero a numero (altra tela, altro cliente, altro metro), ma il verso è
lo stesso — in software il codificatore è più della metà del ritardo.

**Di quanto si sta sotto le soglie, e che cosa limita** (4K, 1 utente, software; richiesta dell'utente):

| | GNOME | KDE | XFCE | LXQt |
|---|---|---|---|---|
| ritardo p95: **1,7-2,5× il tetto** dei 50 ms (fascia DEGRADED 50-150; FAIL > 150) | 97 ms = 1,9× | 124 = 2,5× (oltre metà fascia) | 87-92 = 1,8× | 95-112 = 2,2× |
| i secondi peggiori (max di NOSTRO al secondo) — dentro il livello ce ne sono **sopra i 150** | 141 ms | 152-262 | 102-115 | 169-170 |
| fotogrammi consegnati nel lavoro (l'utente A naviga: consegna quando la scena cambia) — hardware → software | 10,3 → **8,6 fot/s** (−17 %) | 21,6 → **11,2** (−48 %) | 8,2 → **6,2** (−24 %) | 9,3 → **6,1** (−34 %) |
| saltati · buchi · input persi | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 |

Che cosa lo limita: **il codificatore**. OpenH264 2.6.0 è aperto dal prodotto con «QP 25 costante (dal CRF
20) · CABAC · contenuto schermo · **4 fili**» (i fili sono fissati da `ripiego.c`, su una macchina da 20) e
codifica un fotogramma 3776×2016 in **24-26 ms** di mediana (chiave 14-17 ms; i secondi peggiori sopra i
100 ms sono i fotogrammi con molto cambiamento: la pagina che scorre): da solo è la metà del tetto dei
50 ms, e con conversione (5,6 ms), copia e cattura il tratto nostro fa 43-62 ms di mediana. I 4 fili tengono
`remotix` a 0,3-0,7 nuclei: la CPU non è satura (macchina al 5-7 %), è la latenza del codificatore a un
fotogramma alla volta che pesa — a 24 ms per fotogramma il ritmo massimo è ~40/s e ogni fotogramma paga il
suo tempo per intero. Nessun'altra grandezza è vicina a una soglia (saltati 0 %, buchi 0, blocchi ≤ 0,13 s,
nascita 2-3 s, controllo corto GREEN).
I 4 fili sono 4 **fette** (slice) per fotogramma (`ripiego.c`, `RIPIEGO_H264_FILI` fisso, compilato: OpenH264
parallelizza per fette, non per fotogrammi, quindi non aggiunge fotogrammi in canna); il prezzo sono pochi
byte. 🔸 Candidata di taratura, NON fatta qui (è una scelta di prodotto): più fette su una macchina con più
nuclei (8 o 16 su 20) accorcerebbe il tempo per fotogramma a 4K — da misurare col banco `18-software-confronto`
(che legge `RIPIEGO_H264_FILI` dall'ambiente) prima di cambiare il numero.

### 5.6 La Radeon: l'anomalia A3 riconfermata senza libavcodec (gradino 1, 4K, KDE e GNOME)

`[M]` 30 set 23:28→23:49 UTC, campagne `f18amd-4k-kde`, `f18amd-4k-gnome` (`16-coda.sh f18amd` con
`--scheda amd --gradini 1 --minuti 10 --minuti-ultimo 10`: nella scatola entra la RX 6800 come
`renderD128`, driver VA «Mesa Gallium 25.0.7 for AMD Radeon RX 6800 (radeonsi, navi21)», i browser-cliente
restano sulla Intel come nella fase 16 §11). Il «vecchio» è `amd-b-4k-<desktop>/livello-01` del 27 set,
binario `28a947f5` con ffmpeg. Per fotogramma: le righe «codec 3: … codifica N us» del figlio nel `server.log`
del livello (6 434 fotogrammi su KDE, 3 134 su GNOME), le stesse lette in `fasi/16-a3-radeon-vcn.md`.

| Radeon RX 6800, 4K, 1 utente | KDE vecchio → **nuovo** | GNOME vecchio → **nuovo** | (Intel KDE, per confronto) |
|---|---|---|---|
| classe del livello | DEGRADED → **GREEN** | DEGRADED → **GREEN** | GREEN → GREEN |
| ritardo del prodotto p95 | 50,7 → **49,2 ms** | 55,8 → **48,8** | 39,6 → 38,7 |
| NOSTRO p95 dei p95 · mediana | 41,7 · 8,8 → **40,2 · 8,9** | 46,8 · 9,3 → **39,8 · 9,3** | 30,6 · 19,3 → 29,7 · 19,1 |
| codifica per fotogramma: mediana · p95 · **p99** · max | 8,7 · 9,7 · **30,9** · 38,2 → **8,7 · 9,8 · 30,9 · 34,0** | 9,1 · 10,5 · **31,0** · 38,4 → **9,1 · 10,4 · 30,9 · 32,3** | 8,1 · 8,4 · 8,6 · 10,7 → 8,0 · 8,4 · 8,6 · 11,0 |
| fotogrammi sopra i 20 ms | 125 su 6 436 (1,9 %) → **125 su 6 434 (1,9 %)** | 60 su 3 151 (1,9 %) → **60 su 3 134 (1,9 %)** | 0 → 0 |
| come sono raggruppati i lenti | **25 corse da esattamente 5** → **25 corse da esattamente 5** | 12 da 5 → **12 da 5** | — |
| conversione (EFC della scheda) · TRATTO totale | 0,03 · 17,6 → **0,02 · 19,0** | 0,03 · 9,9 → **0,02 · 9,9** | 8,6 · 25,0 → 8,6 · 24,9 |
| blocco più lungo · dipinti · saltati | 0,36 s · 1644/1644 · 0 → **0,06 · 1653/1653 · 0** | 1,18 s · 839/839 · 0 → **0,35 · 843/843 · 0** | |

⇒ **L'anomalia A3 c'è ancora, identica**: gruppi di **esattamente 5 fotogrammi da ~31 ms** ogni 12-40 s,
l'1,9 % dei fotogrammi, p99 30,9 ms — stessi numeri con libva diretta e con libavcodec. Nella fase 16 era
localizzata «dentro `avcodec_send_frame`»: quella era solo la chiamata in cui l'attesa affiorava; è del
driver/ferro (radeonsi, VCN 3.0), non di ffmpeg. Le misure di `fasi/16-a3-radeon-vcn.md` e dell'anomalia A3
in `fasi/16-stress-e-capacita.md` §14 **restano valide** e la bozza del rapporto a Mesa non cambia. (I due
livelli sono GREEN oggi contro DEGRADED il 27 set: il ritardo p95 sta di 1-2 ms sotto i 50 invece che
sopra — è la stessa dispersione di sempre attorno al tetto, non un miglioramento del codificatore, che
misura uguale al decimo.)
