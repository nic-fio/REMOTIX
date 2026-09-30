# A3 — La Radeon rallenta la codifica a gruppi di 5 fotogrammi (dossier per gli sviluppatori del driver)

*⚠ Misure storiche, sulla macchina di allora. Con la fase 18 (senza ffmpeg) sono state tolte quelle che il cambio ha invalidato — codifica senza scheda e conversione dei colori con swscale; quelle della codifica sulla scheda e dell'audio restano, perché il flusso nuovo è identico (confronto del 30 set 2026). Decisione dell'utente.*

> Stato: **aperto, fuori dall'ambito di REMOTIX** — decisione dell'utente del 29 set 2026
> («è fuori dal nostro ambito»; strada 2: documentare e segnalare, non aggirare). Se il driver
> lo risolve, la Radeon in 4K reggerà più utenti senza toccare REMOTIX.
> Contesto nella fase: `fasi/16-stress-e-capacita.md`, «Anomalia A3». Evidenze compatte in
> `misure/fase16/` (i livelli citati sotto); grezzi nell'archivio `fase16-grezzi-2026-09-29.tar.zst`.

## 1. In breve (per chi decide)

REMOTIX comprime ogni fotogramma del desktop in H.264 con la scheda. Sulla **AMD Radeon RX 6800**
un fotogramma costa di solito **8,5–8,7 ms**; ogni 12–40 secondi arriva un **gruppo di esattamente
5 fotogrammi consecutivi da ~31 ms ciascuno** (≈ 8,7 + 22 ms). Sulla Intel UHD 770 lo stesso lavoro
non lo fa mai (p99 8,7 ms, massimo 10,4). Il p95 del ritardo sale oltre i 50 ms di SPECIFICHE §3.2
e in 4K la Radeon risulta reggere 0–3 utenti contro i 13–15 del 3K. Le cause nostre sono state
escluse una per una con misure; il rallentamento sta **dentro la chiamata di codifica del VCN**.

## 2. La macchina

| cosa | valore |
|---|---|
| scheda | AMD Radeon RX 6800, PCI `1002:73bf` rev `c3`, sottosistema `e437`, VBIOS `113-2437SM2-U16` |
| famiglia | navi21 (RDNA2), VCN 3.0 |
| firmware VCN | `0x0412100e` (da `amdgpu_firmware_info`); SMC 58.91.0 |
| nucleo | Linux 7.0 (Debian 13 «trixie»), DRM 3.64 |
| Mesa | 25.0.7-2+deb13u1, radeonsi, LLVM 19.1.7 — `VA Driver version: Mesa Gallium driver 25.0.7-2+deb13u1 for AMD Radeon RX 6800 (radeonsi, navi21, LLVM 19.1.7, DRM 3.64, 7.0)` |
| libva | 2.22.0 (VA-API 1.22) |
| FFmpeg | 7.1.5-0+deb13u1 (libavcodec `h264_vaapi` / `hevc_vaapi`) |
| CPU | Intel i5-13500T (la iGPU UHD 770 è l'altra scheda della macchina, usata per il confronto) |
| compositori | GNOME/Mutter 48, KDE/KWin 6 (Plasma), labwc (XFCE, LXQt) — il fenomeno è su tutti |

## 3. Che cosa fa REMOTIX (la catena, in dettaglio)

1. **Cattura**: ScreenCast del compositore via PipeWire; il fotogramma arriva come **DMA-BUF
   BGRx 8 bit, modificatore `0x0` (LINEAR)**, es. 3776×2016 passo 15104 (4K meno i bordi della
   finestra del browser). Buffer riciclati dal compositore: 4 su KDE, 6 su GNOME.
2. **Importazione**: il DMA-BUF diventa una superficie VA-API (`vaCreateSurfaces` con
   `VASurfaceAttribExternalBuffers`/DRM PRIME), in cache per buffer (`src/codificatore.c`,
   `importa_dmabuf`).
3. **Conversione**: VA-API VideoProc RGB→NV12 in una superficie del magazzino di libavcodec
   (`converti_sulla_gpu`). ⚠ Su radeonsi 25.0.7 dal 16° fotogramma il VPP **non converte**: registra
   la sorgente RGB e torna (EFC, `frontends/va/postproc.c` ~486–507), e la conversione la fa il
   **VCN dentro la codifica** leggendo il buffer RGB lineare (`picture.c` ~1203–1207).
4. **Codifica**: `h264_vaapi`, entrypoint **`VAEntrypointEncSlice`** (la Radeon non dichiara
   `EncSliceLP`), **CQP QP 26**, profilo High, livello imposto 5.1, **`async_depth=1`**,
   `idr_interval=0`, GOP infinito (IDR solo a richiesta), nessun B-frame (verificato: `dts == pts`
   su ogni pacchetto), `initial_pool_size` 8. Un `avcodec_send_frame` + `avcodec_receive_packet`
   per fotogramma, fino a 60/s chiesti, consegnati solo quando la scena cambia.
5. Spedizione su WebTransport; decodifica nel browser (fuori dal tratto misurato).

Una sessione = un processo figlio = **un proprio `VADisplay`, un proprio contesto VPP e un proprio
contesto di codifica** sulla stessa scheda. Con N utenti ci sono N contesti VCN in parallelo.

## 4. Le misure

### 4.1 La forma del fenomeno
Riga per fotogramma del figlio (`registro_dettaglio`), es. da `a3-misura-kde/livello-01/server.log`:
```
codec 3: 421 byte, delta, caricamento 0 us, codifica 31035 us (invio 31031), barriera 18 us, conversione 41 us
```
- **Bimodale**: mediana 8,5–8,7 ms; p99 ~31 ms; massimo 32–35 ms. Nessun valore intermedio.
- **Sempre 5 fotogrammi di fila** (64 gruppi su 64 contati nelle campagne `amd-freq-*`,
  `amd-b-4k-kde`, `amd-b-4k-gnome`; più un fotogramma isolato da 25,7 ms in tutto), ciascuno
  **30,4–32,1 ms**.
- **Non dipende dalla dimensione**: delta da 300 byte e fotogrammi da 480 KB costano uguale nel
  gruppo. **Nessuna chiave** dentro un gruppo.
- **Conta fotogrammi, non tempo**: un gruppo su GNOME si allunga su 1,2 s (2 lenti, 1,16 s di
  scena ferma senza fotogrammi, poi altri 3 lenti); un altro su 0,8 s con 200 ms fra l'uno e l'altro.
- **Ogni 12–40 s**; 11 gruppi su 13 cominciano entro 1,5 s da un'azione dell'utente che fa
  ridisegnare (clic, rotella, tasto), ma non all'istante: es. clic alle 13:25:08.78, fotogrammi a
  8,5 ms fino al gruppo alle 13:25:10.31, su fotogrammi statici (~303 byte).
- **Per sessione**: in `amd-b-4k-kde` (20:41:01.889 e 20:41:06.296 UTC) la sessione u99 fa 5 × 31 ms
  mentre **u1, sulla stessa scheda e lo stesso VCN, codifica a 8,4–8,9 ms negli stessi istanti**; in
  `amd-freq-auto` i gruppi di u1 e u99 non coincidono mai.
- **Scheda quasi ferma** nei secondi dei gruppi: motore grafico 2–6 %.
- **Tutti i compositori** (GNOME, KDE, XFCE, LXQt) e tutte le misure; in 3K e sotto il p95 regge
  perché i gruppi pesano meno sul totale.

### 4.2 Confronto con la Intel, stessa macchina e stesso lavoro
`intel-b-4k-kde/livello-01`: 5732 fotogrammi, codifica mediana 8,1 ms, p99 8,7, massimo 10,4 —
nessun gruppo. (Sulla Intel il VPP è reale: VEBOX, conversione ~8,6 ms separata.)

## 5. Le ipotesi escluse, con la misura

| ipotesi | esperimento | risultato |
|---|---|---|
| frequenza bassa della scheda che risale piano | `power_dpm_force_performance_level` = `auto` contro `high`, KDE 4K, 1 utente, due gradini ciascuno (`amd-freq-auto`, `amd-freq-alta`) | NOSTRO p95 39,3/38,6 ms (auto) contro 37,5/42,0 ms (high): **uguale** |
| VPP sugli shader in fila dietro al ridisegno del desktop | lettura di Mesa 25.0.7 + risorse per motore | il VPP non gira sugli shader (EFC); motore grafico 2–6 %; **e i gruppi sono per sessione**: esclusa ogni contesa globale |
| attesa implicita della scrittura del compositore sul DMA-BUF | **esperimento 1** (binario `3e510160`, ramo `a3-esperimenti`): `DMA_BUF_IOCTL_EXPORT_SYNC_FILE` (`DMA_BUF_SYNC_READ`) + `poll` prima dell'importazione, misurato a parte; codifica divisa in invio/ricezione | barriera **0,37 ms** sui normali, **0,02 ms** sui lenti; i 22 ms sono **tutti dentro `avcodec_send_frame`** (ricezione 0,0 ms); 100 e 105 lenti per gradino (`a3-misura-kde`) |
| il VCN che legge il buffer RGB lineare (EFC) | **esperimento 2** (binario `39e3ed86`): conversione doppia sul primo fotogramma ⇒ per la regola di `postproc.c` Mesa spegne l'EFC per sempre; ogni fotogramma passa da una NV12 vera | conversione vera 0,75 ms mediana; **gruppi identici**: 95 e 106 lenti per gradino, p99 31,1–31,3 ms (`a3-senza-efc-kde`) |
| riciclo dei buffer del compositore, cadenza di cattura | conti dei buffer e del produttore | 4 buffer su KDE, 6 su GNOME, il gruppo è sempre 5; il produttore non è in ritardo (i fotogrammi si accodano durante il gruppo e si smaltiscono a 31 ms) |
| chiavi, dimensione, contenuto | righe per fotogramma | nessuna chiave nei gruppi; 300 B e 480 KB costano uguale |
| un difetto di Mesa 25.0.7 già corretto più avanti | **gradino 1, 29 set 2026**: nella scatola KDE Mesa **26.1.6** (`trixie-backports`, `26.1.6-1~bpo13+1`: `mesa-va-drivers`, `mesa-libgallium`, `libgl1-mesa-dri`, `libegl-mesa0`, `libglx-mesa0`, `libgbm1`), `vainfo` conferma «Mesa Gallium driver 26.1.6»; binario di prodotto `4fb3287d`, stessa scena di 6.1, due gradini da 6 min (`a3-mesa26-kde`) | **100 e 102 lenti** per gradino (su 5209 e 5168 codifiche), tutti fra 30,4 e 39,0 ms, mediana 31,0 ms; raffiche: 18 da 5, una da 4, 3, 2, 1 ⇒ **identico a 25.0.7**: Mesa più nuova non cura |

⇒ **Resta**: con `async_depth=1` `avcodec_send_frame` include la sottomissione al VCN e l'attesa del
risultato; il tempo in più è lì dentro, per un contesto di codifica alla volta, per 5 fotogrammi.
Non è un difetto già chiuso in Mesa: con la 26.1.6 (settembre 2026) il fenomeno è identico, quindi
va segnalato anche sulla versione corrente. Candidati non ancora provati: **stato interno del contesto VCN / firmware** (5 = un numero di slot?
una finestra del controllo di frequenza per istanza?), **posizione della superficie** (buffer lineare
da ~30 MB migrato fra GTT e VRAM), **superfici non tiled**.

## 6. Come si riproduce

### 6.1 Con REMOTIX (riproduzione garantita)
Sul server di prova, scatola KDE con la sola Radeon (`REMOTIX_SCHEDA=amd`), un utente col browser
in 4K che naviga (profilo A di `banchi/16-stress/16-lavori.py`):
```
python3 banchi/16-stress/16-salita.py --scatola kde --misura 4k --campagna a3-riproduci \
    --gradini 1 --minuti 6 --minuti-ultimo 6 --scheda amd \
    --video /media/REMOTIX/misure/fase16/video/bbb_sunflower_2160p_30fps_x4.mp4 --fps-video 30
```
poi nel `server.log` del livello: `grep "] codec [0-9]*: [0-9]* byte"` e contare le codifiche
> 20 ms (atteso ~100 in 6 minuti, a gruppi di 5). Col binario del ramo `a3-esperimenti` la riga
porta anche invio, barriera e conversione.

### 6.2 Riproduzione minima, senza REMOTIX (⏳ da scrivere — il primo passo per il driver)
Un programma C di ~200 righe: `vaCreateSurfaces` da un DMA-BUF lineare BGRx 3776×2016 (o una
superficie RGB32 riempita a mano), `vaProcess` in NV12, codifica `VAEntrypointEncSlice` H.264 CQP
26 un fotogramma alla volta con `vaSyncSurface` sul coded buffer, 60/s per 5 minuti, cambiando una
piccola regione a ogni fotogramma; registrare il tempo di ciascun `vaEndPicture`+sync. Varianti:
un contesto contro due in parallelo; superficie lineare contro tiled; `async_depth` 1 contro 2.
Se si riproduce lì, il rapporto a Mesa diventa indipendente da REMOTIX.

## 7. Le evidenze
- `misure/fase16/a3-misura-kde/`, `a3-senza-efc-kde/`, `a3-mesa26-kde/`, `amd-freq-auto/`, `amd-freq-alta/`,
  `amd-b-4k-kde/`, `amd-b-4k-gnome/`, `intel-b-4k-kde/` — giudizi e diari (nel deposito);
- le righe per fotogramma (`server.log` di ogni livello) nell'archivio dei grezzi;
- il codice degli esperimenti: ramo `a3-esperimenti`, commit `18b6437`;
- l'analisi di Mesa 25.0.7: `postproc.c` 470–510 (la regola EFC), `picture.c` ~1203–1207.

## 8. Draft of the upstream report (Mesa GitLab, radeonsi / VA-API)

**Title:** radeonsi VA-API H.264 encode (navi21/VCN3): periodic bursts of exactly 5 frames at
~31 ms instead of ~8.7 ms, per encode context

**Hardware/software:** RX 6800 (1002:73bf rev c3), VCN fw 0x0412100e, Linux 7.0, Mesa 25.0.7
(Debian 25.0.7-2+deb13u1), libva 2.22.0, FFmpeg 7.1.5 `h264_vaapi`.

**Setup:** screen-capture encoder. Input is a compositor DMA-BUF, BGRx 3776×2016, LINEAR modifier,
imported as a VA surface, converted with VideoProc to NV12 (EFC active after frame 16), and encoded
with `VAEntrypointEncSlice`. The encoder runs CQP QP 26, High profile, level 5.1, no B-frames,
infinite GOP (IDR on demand) and `async_depth=1`. It encodes one frame at a time, up to 60 fps,
only when damage occurs. Several independent processes each have their own VADisplay and encode
context on the same GPU.

**Observed:** encode time per frame, measured around `avcodec_send_frame`, is ~8.7 ms. Every
12–40 s one context produces a burst of **exactly 5 consecutive frames at 30.4–32.1 ms each**.
- Independent of frame size (300 B to 480 KB) and of time: the burst can span >1 s of idle.
- Not synchronized across contexts: another process encodes at 8.5 ms during the burst.
- GFX engine 2–6 % busy.
- Identical with EFC disabled (real VPP blit to NV12).
- Identical with `power_dpm_force_performance_level=high`.
- The DMA-BUF read fence wait, measured explicitly, is 0.02 ms on burst frames.
- The Intel iHD path on the same machine and workload never shows it (p99 8.7 ms).

**Expected:** stable per-frame encode latency.

**Repro:** see §6 (REMOTIX harness); a standalone libva reproducer is being prepared.
