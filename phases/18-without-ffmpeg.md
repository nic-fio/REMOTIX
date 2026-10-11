# Phase 18 — REMOTIX without ffmpeg

✅ **CLOSED on 30 Sep 2026**: phase-15 suite green on the 4 boxes (673/673 in hardware, 80/80 smoke
in software); the product no longer links libavcodec, libavutil nor libswscale. Merged into `fase-10-cure` (`13ccabd`).
Next step: T10 of phase 17 on the product without ffmpeg.

*Opened by the user on **30 Sep 2026** (`DECISIONI.md` §10.22, §10.25). It is born from the licence: REMOTIX will be
under **PolyForm Noncommercial**, incompatible with the distributions' **GPL** libavcodec. By removing ffmpeg
all of REMOTIX's dependencies become permissive (MIT, BSD, Apache).*

## 1. What ffmpeg does today, and what replaces it

| job | today | tomorrow | licence |
|---|---|---|---|
| encoding on the card | `h264_vaapi`, `hevc_vaapi` (libavcodec) | **libva directly** (parameters, buffers, stream headers written by REMOTIX) | MIT |
| software fallback | `libx264`, `libx265`, `libsvtav1` | **OpenH264** (H.264), **SVT-AV1** directly (AV1); ⛔ no software HEVC | BSD |
| audio | Opus encoder via libavcodec | **libopus** directly | BSD |
| colour conversion | libswscale | on zero copy the card's VPP (as it was); from memory and in the fallback **our own code** (`src/colori709.c`, limited BT.709, SSE2) — ⛔ not libyuv, which does not have the 709 matrix; ⛔ not the VPP from memory, measured worse | ours |

## 2. The condition: indistinguishable, measured

The change goes in **only** if:
- the complete **phase-15 functional suite** is green on the **4 boxes** (GNOME, KDE, XFCE, LXQt) **in
  parallel**, with the real browsers, in 4K;
- ~~the phase-16 campaign~~ — ⛔ **removed** by the user on 30 Sep: *«eliminiamo i test di performance, sono
  troppo dipendenti dall'hardware»*; what remains (🔸 proposal, to be confirmed) is the **relative comparison** of the encoder
  on the same machine and on the same images, old against new: time per frame, size, quality
  (PSNR/SSIM) — the new one must not be worse than the old;
- the stream that reaches the browser is of the same type as today (profiles, levels, headers): the page does not
  change.
If it does not get there: ffmpeg stays, and the licence reopens.

## 3. The lines of work, in parallel

- **Line V (video)**: libva directly for H.264 and HEVC on the card; OpenH264 and SVT-AV1 for the fallback; the
  choice of encoder unchanged for the browser.
- **Line A (audio and colours)**: libopus directly; colour conversion without libswscale.
- Then: the tests (§2), the installer adapted (no libavcodec in the dependencies; on openSUSE with Intel
  Packman is no longer needed; Fedora keeps asking for RPM Fusion for the drivers), **T10** of phase 17.

## 4. The change log — for the technical manual

| commit | what | why | measure | installed |
|---|---|---|---|---|
| `1db22a3` `acf4698` | line A: the audio with **libopus directly** (`src/audio.c`), without libavcodec; complexity 10 and unconstrained VBR written explicitly (they were the values of ffmpeg's wrapper, different from libopus's default) | licence (§10.22) | `[M]` bench `banchi/18-a1`, 42 s of mixed signal: packets **identical byte for byte** to the old, 0 different samples out of 4 032 000 in decoding; Chrome 154 with the page's WebAssembly decoder: 1 860 packets, 0 rejected. ⚠ Whole product with the browser not yet tested (the suite does it) | no |
| `77141de` | **Line V-card: encoding on the card with libva DIRECTLY** — `src/vadiretta.c/.h` (configuration, sequence/picture/slice parameters, CQP and QVBR with the cap, the SPS/PPS/VPS/slice/SEI headers written bit by bit with `src/scrittore_bit.c`, the begin/render/end round, the coded bytes); `src/codificatore.c` opens the card with vadiretta (same node, same entrypoint rule, same zero-copy VPP), the from-memory route uploads the BGRx into an RGB surface and converts with the VPP (no libswscale on the card), the D-023 frame is rewritten on the bits (no `hevc_metadata`), the bytes delivered are ours; the SOFTWARE fallback (libavcodec) stays behind the `RipiegoSoftware`/`sw_*` border for the fallback line. `h264_vaapi`/`hevc_vaapi` remain the NAMES of the card's route (figlio.c, `--prova-codifica`). Makefile: `libva-drm` | §10.22/§10.25: PolyForm Noncommercial and GPL libavcodec do not go together; the card was the only place where libavcodec did something that libva does not do on its own | `banchi/18-scheda/18-confronto.sh` on the server, 30 Sep: 120 frames of fake desktop (text, windows, scrolling, dragging), H.264 / HEVC 8 / HEVC 10, 1080p and 4K, Intel (iHD 25.2.3, EncSliceLP) and Radeon (radeonsi 25.0.7, EncSlice), old (libavcodec, `545ec55`) against new. **Zero copy: identical** — PSNR/SSIM equal to the sixth digit, bytes equal (±2 in H.264 = the SEI string), `ffprobe` identical (profile, level 4.2/5.2 H.264 and 4.0/5.0 HEVC, colour 709 tv), 120/120 decoded, encoding times equal (e.g. Intel H.264 1080p 2118 → 2113 µs, HEVC 4K 7368 → 7340 µs); key on request, new canvas halfway, cap (QVBR 20 Mbit): identical. **From-memory route: the new one equals the zero copy, that is WORSE than the old** which converted in CPU with swscale: Intel 1080p H.264 PSNR 38.9 → 37.9 dB and +82 % bytes, HEVC 44.3 → 40.4 dB and +255 %; at 4K −0.1/−0.2 dB and bytes equal; Radeon −1 … −6 dB (Mesa's VPP loses on chroma on zero copy too, old and new). The preparation of the frame from memory is faster (Intel 1080p 4602 → 2734 µs; 4K 18620 → 9036). The D-023 bench (`16-d023-cornice.sh`): Intel 8 PASS, Radeon the frame triggers and the stream declares the canvas (the PSNR below 40 on the Radeon is the VPP, not the frame) | no |
| `1186271` + this | **The other tests of line V-card** (30 Sep): `banchi/18-scheda/18-decodifica-chrome.sh` — headless Chrome 154 on the server decodes with WebCodecs (the page's route: Annex-B → `EncodedVideoChunk` → `VideoDecoder`) the 28 old and new H.264 streams: **120/120 all, pixel fingerprints EQUAL** on zero copy, key on request, new canvas, cap (10 PASS); the 4 «memory» pairs decode 120/120 but the fingerprints differ, as expected (the image is converted by the VPP and not by swscale); the 22 HEVC remain **not tested in Chrome**: headless without GPU has no HEVC in any combination of flags (`isConfigSupported` false for old and new) — for HEVC ffmpeg (120/120) plus the identity of the bytes holds. `cmp` byte for byte on zero copy: HEVC 8 and 10 Intel, HEVC 8 Radeon 4K, cap, key **IDENTICAL**; HEVC 10 Radeon 1080p one extra byte at byte 92: in front of the IDR slice the start code is `00 00 00 01` instead of `00 00 01` (VPS/SPS/PPS identical to the trace; both forms are legal Annex-B and `annexb_prossimo()` and Chrome read both), H.264 ±2 bytes = the SEI string. The whole product built from my tree with `src/costruisci.sh` inside `enter.sh` (mark inside the binary OK): `--prova-codifica` ⇒ `{"esito":"hardware","codificatore":"h264_vaapi","nodo":"/dev/dri/renderD128", …, avc1.640c15, 1583 byte}`; started on port **7611** with its own ban-file and socket: page served (200, 874 KB), turned off clean; a session with a desktop was not tested (no user with a desktop outside the boxes) | the condition of §2 demands the real browser and the whole product, not just the bench | Chrome: 10 PASS, 4 «different by construction», 22 not testable here; product: starts, encodes in hardware, serves the page | no |
| fc19168 | installer and packages without ffmpeg: catalogue (seq. 8) with the VA drivers **per vendor** (Fedora: RPM Fusion — Intel `intel-media-driver` from the **nonfree** branch, AMD `mesa-va-drivers-freeworld`; openSUSE: Packman **AMD only** (`Mesa-dri`, `Mesa-libva`); Alma: Intel from RPM Fusion nonfree, AMD nothing), new «openh264» repository (Cisco) and EPEL on Alma as repositories of REMOTIX itself (D5), preflight without libavcodec (real OpenH264 against `noopenh264`), `.deb`/`.rpm`/PKGBUILD with OpenH264, SVT-AV1, libopus and libyuv on a single line | out with the GPL libavcodec (§10.22); the drivers with H.264 are the only third-party thing left | `[M]` 30 Sep, podman images: Debian 13 everything in main; Ubuntu 26.04 OpenH264 and SVT-AV1 in universe; Fedora 44 `openh264` from `fedora-cisco-openh264` on by default; Alma 10 `openh264` 2.5.1 (so.7) only from `epel-cisco-openh264` (to be added; EPEL signature verified), SVT-AV1 in EPEL, **libyuv absent**; Leap 16/TW real `libopenh264-8` from `repo-openh264`, in repo-oss the empty copy; openSUSE's official iHD complete (AVC classes like RPM Fusion), official Mesa without h264/h265; `go test ./...` green | no |
| (questo commit) | **THE INTEGRATION: REMOTIX without ffmpeg** — (1) `codificatore.c` grafts the fallback of `ripiego.c` in place of libavcodec: `sw_apri`→`ripiego_apri`, `sw_codifica`→`ripiego_codifica`, the quality change (`abbassa`/`risali`) goes through `cambia_qualita()`→`ripiego_qualita` (H.264 hot), `codificatore_ridimensiona`→`ripiego_ridimensiona`; all the rest of the cures stays (16 MiB, scale, climb back, `forma_va_bene`, confession from the SPS, D-023 frame). (2) **The from-memory route goes back to what it was**: conversion in CPU with `colori709_a_nv12`/`_a_p010` into the staging buffer and upload of the planes with `vadiretta_carica_nv12`/`_p010` (vaDeriveImage/vaPutImage); out with the RGB surface and the VPP from memory. Zero copy is not touched. (3) **HEVC in software never**: `figlio.c` `codificatore_di()` with `hevc_vaapi` closed returns NULL with the reason; **the `ECCOMI`'s list of codecs is measured at startup** (`figlio_capacita_video()`, in a separate process: «hevc» only if the card encodes it, «h264» if card or REAL OpenH264, «» if nothing ⇒ every CIAO in NIENTE_IN_COMUNE, declared with the remedy for the distro — `rcp_video_codec_imposta()`, `banchi/rcp` aligned); `--prova-codifica [h264\|hevc] [--nodo N] [--software]` with the extra JSON keys `codec`, `offerti`, `hevc`, `h264`, `rimedio`. (4) **Out with ffmpeg**: no `#include <libav…>`, `Makefile` without `-lavcodec -lavutil -lswscale` (OpenH264 only `--cflags` + `-ldl`, `SvtAv1Enc` linked, `MINIMI` and headers updated), `src/Contenitore` and the eight `costruzione/Contenitore.*` with `openh264`/`svt-av1`/`opus` per distro, `costruisci-tutti.sh` refuses an `ldd` with libav; `ripiego.c` with the guards for SVT-AV1 3.x and 4.x (`svt_av1_enc_init_handle` with two arguments, no `color_description_present_flag`, `EbSvtIOFormat` planes only; from 4.0 `aq_mode` and `LOW_DELAY`). (5) `banchi/18-scheda/18-confronto.sh` builds the new one with `ripiego.c`/`colori709.c` and refuses `av_` symbols; `18-software-confronto.sh` relaunches itself with `bash "$0"` | §10.22/§10.25; the user's decision (30 Sep): without a card and without real OpenH264 AV1 does NOT come back in — it is declared, with the remedy | `[M]` 30 Sep 2026, server (i5-13500T, Intel UHD 730 iHD 25.2.3 + Radeon RX 6800 radeonsi 25.0.7), integrated tree against `545ec55`: **`18-confronto.sh` «nessuna prova in cui il nuovo sia peggio del vecchio»** — zero copy identical (PSNR/SSIM/bytes equal, ±2 bytes of the SEI), **from-memory route back to even**: Intel 1080p H.264 38.926→38.925 dB and +0.2 % bytes, HEVC 44.32→44.31, 4K ±0.02 dB; Radeon ±0.04 dB; the preparation of the frame from memory in half the time (Intel 1080p 4024→1964 µs, 4K 16720→7816); key, canvas, cap identical. **`18-software-confronto.sh`**: colours ±1 level from swscale (minimum PSNR 73 dB Y, chroma different ≤4 %), new H.264 (OpenH264) against corrected 1080p PSNR-Y 46.4 vs 43.3 dB · SSIM 0.99757 vs 0.99748, 4K 48.3 vs 43.9; AV1 new vs old 57.12 vs 57.21 and 56.51 vs 56.60 (same bytes); refusals declared (H.264 10 bit, >36 864 MB, lossless). **`18-a1`**: GREEN, 8400 blocks identical byte for byte. **Product** built on the server from this tree: `ldd` without libav*/libswscale/libx26x, `nm -D` 0 `av_`/`sws_` symbols; `--prova-codifica` ⇒ hardware on renderD128 (Intel, `avc1.640c15`, `hev1.1.6.L60.B0`) and on `--nodo renderD129` (Radeon), `--software` ⇒ `openh264` 1816 bytes, `hevc --software` ⇒ «nessuno» with the why (code 1); started on port **7631** with its own ban-file and socket: page 200 (874 KB), at startup «video.codec offerti: «hevc,h264» — … software OpenH264 NO … ⇒ rimedio: apt install libopenh264-8» (the host does not have the library: the declaration works), turned off clean. Containers (`costruisci-tutti.sh`): Debian 13, **Fedora 44** (SVT-AV1 3.1.2, OpenH264 2.6.0 from fedora-cisco-openh264) and **Arch** (SVT-AV1 4.2.0) compile without warnings, `ldd` clean, and `--prova-codifica --software` inside the two containers ⇒ `openh264`, 1816 bytes, `avc1.640c15`; ⚠ the AV1 route with SVT 3.x/4.x is compiled, not executed (no iron with those versions). ⚠ Not tested: a session with desktop and browser (the suite does it on the 4 boxes) | no |
| (questo commit, banchi) | **the suite's boxes like the real machine** — `banchi/11-scatole/Contenitore.{gnome,kde,xfce,lxqt}`: in the «le librerie del Makefile» line `libopenh264-8 libsvtav1enc2 libopus0 libva-drm2` in place of `libavcodec61 libavutil59 libswscale8` (ffmpeg stays in the box only as a tool of the Python client); in the four running boxes `libopenh264-8` 2.6.0 (1.1 MB, not the empty copy) put in with apt, without redoing the images | the phase-15 suite (§2) must test the product without ffmpeg with the ECCOMI that offers h264 in software too | `[M]` 30 Sep 10:34: startup log of rete11-{gnome,kde,xfce,lxqt} with the binary `4b39195c` (from `92caeb3`; the old `4fb3287d` saved in `rete11/prodotto/remotix.4fb3287d`): «OpenH264 2.6.0 aperto da libopenh264.so.8», «video.codec offerti nell'ECCOMI: «hevc,h264» — HEVC: scheda renderD128 · H.264: scheda si', software OpenH264 si'» | boxes |
| (questo commit) | **⭐ THE PHASE-15 FUNCTIONAL SUITE ON THE PRODUCT WITHOUT FFMPEG — GREEN** (§2, first condition): round `18-suite` on the four boxes in parallel (rete11-gnome/kde/xfce/lxqt), real Firefox 140.16.0 and Chrome 154.0.8037.57, 3840x2160, 29 tests (F-001…F-032, F-018b/c, F-024b, F-031B, paths A-F, negatives N-1 N-3 N-4) with the grafted fault, plus the technical layer (C7 C9 C18 C19 × 4, C14). Log in `banchi/15-suite/registro.jsonl` (copy from the server, additions only, 6994 lines), generated report `banchi/15-suite/rapporto-giro18-suite.{txt,html}`, evidence on the server in `/media/REMOTIX/misure/fase15/giro18-suite/` | the change goes in only if the complete suite is green (§2) | `[M]` 30 Sep 10:36→12:51 UTC, 135 min, binary `4b39195c` (from `92caeb3`), page `fb9a18f3`, benches `3ccbe10`: **673 PASS, 0 FAIL, 0 BLOCKED** — per box: 44 healthy + 44 with the fault with Firefox, 36 + 36 with Chrome, 4 + 4 technical; C14 PASS. Encoding in HARDWARE (Intel iHD 25.2.3, `avc1.640c15`), ECCOMI «hevc,h264». ⇒ No FAIL to compare with the old binary (`4fb3287d`, with ffmpeg, saved in `rete11/prodotto/remotix.4fb3287d`) | boxes: `4b39195c` |
| (questo commit) | **The smoke round in SOFTWARE** (OpenH264, the product's route on a machine without VA driver): round `18-software-2`, F-001 F-002 F-003 F-004 F-013 (video, ~155-195 s), 4 boxes × Firefox and Chrome, with the fault. Method: in the boxes `iHD_drv_video.so` renamed (⇒ «H.264: scheda no, software OpenH264 sì», ECCOMI «h264»), server restarted with `11-accendi.sh server`; then driver put back and servers restarted in hardware. ⚠ `LIBVA_DRIVER_NAME` in the server's environment is NOT enough: the child composes the environment from zero (`execve`, CODER.md §4.5) and the sessions of the first attempt (`18-software`) encoded in HARDWARE — that round does not count as a software test; its only FAIL (F-003 kde/chrome, «foto vecchia» 1026-1409 ms against the cap of 1000 ms, healthy pass; the fault BLOCKED as a consequence) is the same bench that in the complete round and in `18-software-2` is PASS with the new binary and that is PASS with the old binary `4fb3287d` on the same box (`18-f003-kde-vecchio`): intermittent at the edge of the cap, not phase 18's | the complete suite only goes through the card; the software fallback is the declared route for whoever does not have the driver | `[M]` 30 Sep 13:11→13:26 UTC, 15 min: **80 PASS, 0 FAIL, 0 BLOCKED** (40 healthy, 40 faults seen); in every box's log all the sessions «in software» (8 on gnome/kde, 16 on xfce/lxqt), 0 «COPIA ZERO in vigore». Report `banchi/15-suite/rapporto-giro18-software-2.{txt,html}` | boxes: `4b39195c`, driver put back |

## 5. The measures redone — after phase 18 (1 Oct 2026)

*The user's decision (1 Oct): «l'abbandono di ffmpeg ha invalidato una serie di misure di performance
misurate con il precedente sistema che devono essere rifatte. Quindi bisogna far rigirare, almeno
parzialmente, la suite dei test di performance». The figures live ONLY here; in the historical diary, next to
every removed measure that is redone here, there is a reference to this section. ⛔ No figure in the four documents
of the product.*

**The machine, for all the figures of §5**: server i5-13500T (20 threads, 31 GB), Intel UHD 770 (`8086:4680`,
`i915`, iHD 25.2.3, EncSliceLP), Radeon RX 6800 (`1002:73bf`, `amdgpu`, radeonsi Mesa 25.0.7) — Debian 13,
kernel 7.0, libva 2.22.0; the REAL browsers **on the server** in 4K (3840×2160) in the nested compositors (`labwc`
0.8.3 without a screen): Firefox ESR 140.16.0, Chrome 154.0.8037.57; the product in the `rete11-*` boxes =
binary **`4b39195c`** (from `92caeb3`: ⭐ it is today's `fase-10-cure` binary, `src/` has not changed since
then), page `fb9a18f3`.

### 5.1 The inventory: what the commits «da unire solo a suite verde» removed, and what is redone

Read the 34 diffs of the commits «📋 fase 18 (da unire solo a suite verde)». Two waves: the first (30 Sep
10:56-11:11) removed ALL the performance figures because of the rule «le cifre vanno in git» (§10.26) — those
stay valid and **are not redone** (card with zero copy, capture alone, wire, audio, admission, starts,
bad network, phase-16 capacity); the second (12:32-12:48) removed the measures **invalidated** by the
change. They are these, grouped into sets:

| set | what it measured (document · section · old figure) | bench of origin | does it make sense today? | what is done |
|---|---|---|---|---|
| **S — encoding WITHOUT a card** (libx264 / libx265 / libsvtav1 via libavcodec) | DECISIONI §1.13-bis `libsvtav1` preset 10 **22.23 ms/frame** at 1080p (against hevc_vaapi 3.16); fasi/10 §3.6 fallback `libx265` **~22 ms against ~3**; FASI §03 / DECISIONI §2.5 §7.8 / LEZIONI §6.2 / STUDI: the phase-3 chain on Xvfb with AV1/HEVC in software — capture→glass delay **74.58 ms** (capture→first byte 39.17 = 53 %), paint ceiling **127.6/s**, worker **+27.6 ms**, 23.93 frames/s; LEZIONI §5 SVT-AV1 at 962 **PSNR 43.3 dB**; RCP §5 / fasi/08 D.2 fallback `libx264` at 8K **18.7 MiB** per key; fasi/09 §0.5 v1 R31 `libx264` 1 992 kbit/s; LEZIONI §0 v1 41→6 ms; §8 multi-threaded sws_scale 13.8/12.5 ms | `03-palco-codificatori.sh`, `03-b17-ritardo.py`, `03-b16-dipinti.py`, `03-b19-*` (Xvfb, the client of the time, ffmpeg); `08-D2-ripiego.py` (ffmpeg); v1 | **partly**: today software is ONLY H.264 with OpenH264 (no HEVC, no AV1 as last fallback, 8K refused: DECISIONI §10.26); the phase-3 chain (Xvfb, without desktop) is no longer the product | **done**: the whole chain with the real browsers in 4K with OpenH264 (§5.4: delay, frames, conversion and encoding times per frame from the child's log) and the **capacity** (§5.5). The OpenH264 quality against x264 is already in §4 (`18-software-confronto.sh`, 30 Sep: 1080p PSNR-Y 46.4 vs 43.3 dB) |
| **M — the card FROM MEMORY** (sws_scale + `av_hwframe_transfer_data`, then the VPP from memory) | fasi/08 agent C **21.61 ms** per frame at 1080p (sws_scale 5.39 + upload 0.98), F4 before/after **22.82 → 6.41 ms**; fasi/09 §13.6 §14.6 4K «conversione **11 466 µs** + codifica 8 895 = 20,4 ms ⇒ ~49/s», 2560×1080 6 652 + 3 827; fasi/10 §6.2 N=24 with **12.0 cores**, **6.0 cores** for ten 1080p against 0.7 in zero copy, free `ffmpeg` 406.2 frames/s; §5.1 MEMORIA rows; §6.1 calibration of the GPU meter with `hwupload` (12.68 % for 1080p30, line 0.1968·Mpx/s); §6.6 and §6.10 the iron study with ffmpeg (875/852 frames/s, 24.6 → 50.2 W with the conversion, 1.8/1.47 Gpixel/s, CQP 876.8 / QVBR 816.0 / CBR 812.8); fasi/06 §4.9 `h264_vaapi` 1.6 ms and 5 940 bytes; DECISIONI §1.13-bis the `*_vaapi` 3.11-7.28 ms via `hwupload`; RCP §5.2 `-bf 1` −16 % and 67 ms | `08-c-*`, `08-f4-*` (**missing** in `banchi/`), `10-b88-saturatore.py --strada memoria` (links libavcodec), `10-b87-metro-gpu.py`, `10-b94-ferro-carico.py`, `03-palco-codificatori.sh` (all ffmpeg) | **yes for the product's route** (today: `colori709.c` in CPU + `vaPutImage`), **no for the iron study with ffmpeg** (it measured ffmpeg, which is no longer there; the 2048/1021 contexts and `vaQueryProcessingRate` stay valid because they are libva's) | ⛔ **NOT DONE** (the user's stop, 1 Oct 06:23): the original benches no longer run (they are missing or link libavcodec) and a substitute on the product was not written. The 30 Sep comparison in §4 remains (`18-confronto.sh`: preparation from memory 1080p 4 024 → 1 964 µs, 4K 16 720 → 7 816 µs, quality even) |
| **C — the whole chains taken on binaries that went through those routes** (phases 4, 6, 7, 8; and phase 3) | FASI §04 O2 hand→pixel **139.40 ms**; fasi/08 §1.4, A/B/F1/F2: `input → vetro` **99.07 → 89.86 → 55.20 ms**, gap **0.27 → 0.16 bars**, F2 70.5 ms; fasi/06 §4.2 §4.8 §5.6 §5.9 (rotated canvas 4-6 ms, Mutter 32-39, `ADATTATA` round 42-44, `SESSIONE`→1st frame 14-335 ms), §5.8 contention with 5 ffmpeg; fasi/07 §8 (audio→video ~400 ms, AV median 236 ms), §8-ter netem, §8-quater | `04-b30-anello-input.py`, `08-b67-elastico.py` (laptop + tablet of the time: not reproducible as back then), `06-b35-tempi.py`, `06-b41-contesa.sh` (ffmpeg), `07-b61-*` | **yes, but with today's yardstick**: the whole chain in 4K with the real browsers is phase 16's (`16-salita.py`, `16-classifica.py`: product delay p95, echo round trip, paints/skipped, birth), taken on 26-27 Sep with the binary `45d048c8` **with ffmpeg** in zero copy | ⛔ **NOT DONE** as a set: the loop measures of phases 4/6/7/8 (hand→pixel, bars, the laptop's stretches, audio→video) were not redone. Only **step 1 in HARDWARE in 4K on the 4 desktops** was redone with the phase-16 bench (§5.3), which says that the whole chain with the new binary is phase 16's |
| **K — how many sessions the server bears WITHOUT a card** | never measured: phase 16 is all in hardware | `16-salita.py` | **yes** (new measure requested by the user) | **done**: §5.5 — 4K and 1080p on the 4 desktops, 1440p on GNOME and KDE (as far as it got); ⛔ 1440p on XFCE and LXQt **not done** |
| **no longer meaningful** | HEVC in software (`libx265`: fasi/10 §3.6, RCP §6.2 CRF, fasi/08 D.2) — the product no longer does it; AV1 in software as last fallback; 8K in software (OpenH264 refuses beyond 4096×2304, declared); the iron study **with ffmpeg** (fasi/10 §6.1, §6.6, §6.10 ffmpeg part); v1's measures | — | no | nothing: they stay removed |
| **to be reconfirmed** | fasi/16-a3 and 16-stress A3: on the Radeon groups of 5 frames of ~31 ms every 12-40 s, localised «dentro `avcodec_send_frame`» — zero copy, so valid for §10.26, but the call no longer exists | `16-salita.py --scheda amd` | yes, one step 1 on KDE 4K is enough to see whether the groups are still there | **done**: §5.6 |

⚠ **Inconsistencies found in the diffs, to be decided (not touched here)**: the second wave left in FASI §04
(O2 139.40 ms, click 136 → 41 ms), LEZIONI §1.26 (17.48 ms), §1.28/§1.33 (0.47 bars) and DECISIONI §1.13-bis
(the `*_vaapi` 3.11-7.28 ms via `hwupload`) figures taken on from-memory/sws_scale binaries, which by the criterion
of `f3acbe8` (fasi/08) should go too. And `banchi/10-b92-scene.py`, cited in fasi/10 §6.12, is not
in the repository; the benches of agents C, F1, F4 and A of phase 8 (`08-c-*`, `08-f1-*`, `08-f4-*`) are not either.

### 5.2 Before the measures: the boxes redone like the real machine

The user's decision (1 Oct): the suite's 4 boxes are rebuilt from the current recipes
(`banchi/11-scatole/Contenitore.*`, without libavcodec), because the running ones had 8-day-old images with
ffmpeg inside and `libopenh264-8` put in by hand.

**The versions, before and after** (`[M]` 30 Sep 19:35 and 19:47 UTC; dpkg inside the boxes and on the host):

| package | old boxes (images of 22-24 Sep) | new boxes (1 Oct) | host |
|---|---|---|---|
| `intel-media-va-driver` (iHD) | 25.2.3+dfsg1-1 | **the same** | 25.2.3+dfsg1-1 |
| `libva2` / `libva-drm2` | 2.22.0-3 | the same | 2.22.0-3 |
| `mesa-va-drivers`, `libgl1-mesa-dri` | 25.0.7-2+deb13u1 | the same | 25.0.7-2+deb13u1 |
| `libigdgmm12`, `libvpl2` | 22.7.2+ds1-1, 2.14.0-1+b1 | the same | the same |
| `libopenh264-8`, `libsvtav1enc2`, `libopus0` | 2.6.0+dfsg-2 (by hand), 2.3.0+dfsg-1, 1.5.2-2 | the same (from the recipe) | — / 2.3.0 / 1.5.2 |
| `firefox-esr` (inside the box: the browser of the climb's «A» users and of C8) | 140.16.0esr-1~deb13u1 | ⚠ the `trixie-security` repository now gives **153.4.0esr**: ⇒ **pinned to 140.16.0esr** from the host's .deb (`/media/REMOTIX/cache/apt-host`), `apt-mark hold` | 140.16.0esr |
| `google-chrome-stable` (host: the browsers of the suite and of the actors) | — | — | 154.0.8037.57-1 |
| desktop: `gnome-shell` 48.7-0+deb13u2 · `kwin-wayland` 6.3.6-1 · `plasma-workspace` 6.3.6-2 · `labwc` 0.8.3-1 · `xfce4-session` 4.20.2-2 · `lxqt-session` 2.1.1-1 · `pipewire` 1.4.2-1 · `xwayland` 24.1.6-1 | | all the same | |
| host kernel (= the boxes') | 7.0 | 7.0 | 7.0 |
| `ffmpeg` (program, tool of the C2/C3/C8b benches) and with it `libavcodec61` 7.1.5 | present | present (the recipe keeps it as a tool; the product does not link it: `ldd` without libav) | present |

⇒ The only difference compared with the boxes of the previous measures would have been Firefox 140 → 153 inside
the box: **avoided** by pinning the package. Drivers, libva, Mesa and the suite's browsers are **identical**.
Changes to the recipes (in this branch): `Contenitore.{gnome,kde,xfce,lxqt}` block 4-ter installs
`firefox-esr` from the host's .deb (`COPY pacchetti/…`) and puts it on `hold`; `11-accendi.sh costruisci` copies
the .deb from the cache into the context and stops if it is missing. `nictest:nictest` (sudo, video, render) is there in all
four, LXQt included. The binary inside stays `4b39195c`, page `fb9a18f3`; at startup every server says
«video.codec offerti nell'ECCOMI: «hevc,h264» — HEVC: scheda renderD128 · H.264: scheda si', software
OpenH264 si'».

**The smoke round on the new boxes** (`[M]` 30 Sep 19:48→20:02 UTC, round `18-scatole-nuove`: F-001/F-002,
F-003, F-004, F-013 with the fault, 4 boxes in parallel × Firefox and Chrome): **75 PASS, 1 FAIL, 4 BLOCKED**
out of 80; all the sessions in HARDWARE (38 «in HARDWARE», 0 in software in the logs). The five reds —
xfce/firefox F-013 («nessun pixel cambia», and the fault BLOCKED as a consequence), gnome/chrome and xfce/chrome
F-004 («la fotografia: nessuna risposta dal browser in 25 s»), lxqt/chrome F-013 fault — **redone one at a
time** (round `18-scatole-nuove-r`, 21:01→21:10): **8 PASS out of 8**. As in the round of 29 Sep (phase 16 §17.1,
D-022): they are the reds of the four-box parallelism on the same machine, not of the boxes. ⇒ The
new boxes work; from here the measures, one configuration at a time.

### 5.3 The whole chain in HARDWARE with the new binary (step 1, 4K, the 4 desktops)

`[M]` 30 Sep 21:11→22:04 UTC, campaigns `f18hw-4k-<desktop>` (`banchi/16-stress/16-coda.sh f18hw` with
`REMOTIX_16_IN_PIU="--gradini 1 --minuti 10 --minuti-ultimo 10"`: the same bench as phase 16, a
single step of 10 minutes, one configuration at a time, empty server and `uptime` read by the climb
itself — load 0.8-1.3 at 1 user). User 1 = profile A (real Firefox 140 in 4K, browsing in the
session), plus the short check (u99, Firefox) in the last 2 minutes; classification by `16-classifica.py`,
thresholds §9 of phase 16. The «old» is `intel-b-4k-<desktop>/livello-01` of 26-27 Sep: **same bench,
same machine, same versions** (§5.2), binary `45d048c8` **with ffmpeg** (`h264_vaapi` via libavcodec,
zero copy). Evidence: `/media/REMOTIX/misure/fase16/f18hw-4k-*/livello-01/`, log
`banchi/16-stress/registro.jsonl` on the server.

| 4K, 1 user (Firefox), per session | GNOME old → **new** | KDE old → **new** | XFCE old → **new** | LXQt old → **new** |
|---|---|---|---|---|
| level class | GREEN → **GREEN** | GREEN → **GREEN** | GREEN → **GREEN** | GREEN → **GREEN** |
| product delay p95 (classification; cap 50) | 33.2 → **35.3 ms** | 39.6 → **38.7** | 36.4 → **36.1** | 36.2 → **36.6** |
| OURS (copy → bytes out) p95 of the p95s · median | 24.2 · 17.0 → **26.3 · 16.9** | 30.6 · 19.3 → **29.7 · 19.1** | 27.4 · 22.0 → **27.1 · 22.1** | 27.2 · 21.9 → **27.6 · 22.1** |
| echo round trip (key → frame, page) p95 | 55 → **51.6 ms** | 64.3 → **61.7** | 64.2 → **55.8** | 72.6 → **69.5** |
| STRETCH (medians over the ring of 512): total · conversion (VPP) · encoding | 17.5 · 8.7 · 7.9 → **17.4 · 8.8 · 7.9** | 25.0 · 8.6 · 8.1 → **24.9 · 8.6 · 8.0** | 21.9 · 3.3 · 8.0 → **21.8 · 3.3 · 7.9** | 21.8 · 3.3 · 8.0 → **22.1 · 3.3 · 7.9** |
| first H.264 frame 3776×2016: conversion · encoding (µs) | 12 290 · 9 303 → **12 063 · 9 136** | 13 734 · 9 736 → **13 058 · 8 703** | 14 571 · 9 569 → **12 017 · 8 576** | 15 170 · 9 020 → **11 420 · 8 502** |
| painted / delivered · skipped · holes | 799/799 · 0 % · 0 → **768/768 · 0 % · 0** | 1434/1434 · 0 · 0 → **1524/1524 · 0 · 0** | 579/579 · 0 · 0 → **567/567 · 0 · 0** | 730/730 · 0 · 0 → **690/690 · 0 · 0** |
| longest image stall | 0.061 → **0.056 s** | 0.065 → **0.068** | 0.068 → **0.063** | 0.068 → **0.073** |
| bandwidth | 0.69 → **0.71 Mbit/s** | 0.95 → **1.01** | 0.30 → **0.31** | 0.62 → **0.61** |
| birth of a new user (u99, login → first frame) · short check | 2.44 s · GREEN → **2.63 · GREEN** | 2.26 → **2.25** | 2.06 → **2.07** | 1.64 → **1.67** |
| CPU in the window: enclosure `remotix` · `sessioni` (cores) · machine | 0.03 · 0.32 · 4.3 % → **0.03 · 0.33 · 4.2 %** | 0.05 · 0.36 · 5.0 % → **0.04 · 0.38 · 5.4 %** | 0.11 · 0.27 · 4.3 % → **0.11 · 0.27 · 4.5 %** | 0.09 · 0.29 · 4.4 % → **0.09 · 0.30 · 4.7 %** |
| Intel GPU in the window: render · video · video-enhance (%) | 13.4 · 4.1 · 7.0 → **13.0 · 4.1 · 7.2** | 40.8 · 11.2 · 18.8 → **41.1 · 12.1 · 18.8** | 11.1 · 3.3 · 1.9 → **10.8 · 3.2 · 1.9** | 13.0 · 3.8 · 2.2 → **13.0 · 3.8 · 2.2** |

⇒ **Indistinguishable**: every quantity of the new one sits within the spread of the old (delay ±2 ms, conversion
and encoding stretches equal to the tenth of a millisecond, GPU equal to the percentage point); the whole chain
in hardware with the binary without ffmpeg is phase 16's, and the measures of the phase-16 campaign
remain the reference. (On GNOME and KDE the VPP converts from RGB, 8.6-8.8 ms; on XFCE and LXQt the wlroots
compositor already gives NV12 and the conversion is 3.3 ms with 5.3 ms of copy: as it was.) KDE's first frame
in the old one was HEVC (the short check's Chrome, 29 064 µs), in the new one the order of the short check's
browsers changed: it is not a difference of the encoder.

### 5.4 The whole chain WITHOUT a card (OpenH264), 4K, 1 user (set S)

`[M]` 30 Sep 22:04→23:28 UTC, campaigns `f18sw-4k-<desktop>` (`16-coda.sh f18sw`, `REMOTIX_16_IN_PIU=
"--senza-scheda --minuti 10 --minuti-ultimo 10"`). **Declared adaptations of the bench**: (1) `16-salita.py
--senza-scheda` — in the redone box, after `prodotto` and before `server`, `iHD_drv_video.so` is renamed
(as in the smoke round of §4: `LIBVA_DRIVER_NAME` is not enough, the child composes the environment from zero), and the
climb **demands** that the startup log says «H.264: scheda no (/dev/dri/renderD128), software OpenH264
si'» — so it was in all four; the compositor keeps drawing on the card (Mesa iris), it is only
the encoding that goes down to OpenH264 2.6.0, as it is for whoever does not have the VA driver; (2) every level lasts 10 minutes,
the last one too (the rule «sessioni al massimo 10 minuti»). Everything else is the phase-16 climb (§6:
steps 1 → 4 → 8 → 12 → 16, the non-continuation rule, the repetition, the search halfway; §9: the thresholds).
User 1 = profile A (Firefox 140 in 4K); short check in the last 2 minutes.

**4K in software already gives way at 1 user, on the 4 desktops**: level 1 is **DEGRADED significant** (the only
session DEGRADED; on KDE even beyond half the band), repeated once with the same outcome ⇒ the climb
stops (§6), «ultimo GREEN: nessuno». It is not a FAIL: no input lost, all frames painted, no
hole, stalls of 0.1 s; it is the **delay** that sits outside the 50 ms cap.

| 4K, 1 user (Firefox), software OpenH264 — level 1 and repetition | GNOME | KDE | XFCE | LXQt | (hardware, §5.3) |
|---|---|---|---|---|---|
| product delay p95 (cap 50 GREEN, 150 FAIL) | **97.3 · 96.6 ms** | **123.9 · 115.2** | **86.9 · 92.3** | **111.5 · 94.9** | 35-39 |
| OURS (copy → bytes out) p95 of the p95s · median | 88.3 · 47.6 | 114.9 · 50.9 | 77.9 · 45.9 | 102.5 · 48.8 | 26-30 · 17-22 |
| echo round trip p95 (page) | 114.9 · 109.3 | 116.3 · 114.8 | 96.0 · 99.7 | 107.5 · 107.7 | 52-70 |
| STRETCH (medians over 512): total · conversion (`colori709`, CPU) · encoding (OpenH264) | 58.2 · 5.5 · **26.2** | 62.4 · 5.7 · **26.5** | 43.0 · 5.7 · **24.0** | 45.0 · 5.7 · **24.5** | 17-25 · 3.3-8.8 · 7.9 |
| first frame 3776×2016 (µs): conversion · encoding | 8 340 · 17 505 | 8 288 · 15 323 | 6 938 · 14 024 | 6 911 · 14 294 | 11-13 000 · 8 500-9 100 |
| painted/delivered · skipped · holes · max stall | 653/653 · 0 % · 0 · 0.12 s | 868/868 · 0 · 0 · 0.13 | 418/418 · 0 · 0 · 0.11 | 483/483 · 0 · 0 · 0.11 | 0 % · 0 · 0.06-0.07 |
| bandwidth | 0.46 Mbit/s | 0.52 | 0.20 | 0.39 | 0.3-1.0 |
| short check (u99: birth, F-004, F-007, F-003, F-014) | GREEN | GREEN | GREEN | GREEN | GREEN |
| CPU in the window: enclosure `remotix` (cores) · machine | **0.34** · 5.1 % | **0.68** · 7.4 % | 0.30 · 4.5 % | 0.32 · 4.8 % | 0.03-0.11 · 4-5 % |
| PSS of the `remotix` enclosure | 509 MB | 521 | 581 | 435 | 41-92 MB |
| Intel GPU: render · video · video-enhance | 14.4 · **1.0** · **0.0** % | 32.1 · 2.2 · 0.0 | 9.7 · 0.8 · 0.0 | 10.7 · 0.9 · 0.0 | 11-41 · 3-12 · 2-19 |

Readings: **encoding a 4K frame in OpenH264 costs 24-26 ms** (median; 14-17 ms the first, which is
a key) against 7.9 ms on the card; colour conversion in CPU (`colori709.c`, SSE2) costs **5.5-5.7
ms** at 3776×2016, that is *less* than the card's VPP on GNOME/KDE (8.6-8.8 ms) and a little more than wlroots'
NV12 route (3.3 + 5.3 of copy) — and in the old one (fasi/09 §13.6, `sws_scale`) the first 4K frame
cost 11 466 µs of conversion: **today 6 900-8 300**. The card's video engine sits at ~1 % (it is the browser
that decodes) and video-enhance at 0: the card does not encode. The `remotix` enclosure goes from 0.03-0.11 to
**0.3-0.7 cores** for one 4K session, and from 40-90 to **430-580 MB** of PSS (OpenH264's buffers at 4K).
⇒ For the product: **without a card 4K does not fit in the 50 ms cap even with one user**; the capacity
must be looked for at lower sizes (§5.5). Against phase 3 (74.58 ms capture→glass with libsvtav1/libx265 at
1080p on Xvfb): not comparable number to number (another canvas, another client, another yardstick), but the direction is
the same — in software the encoder is more than half of the delay.

**By how much it sits below the thresholds, and what limits it** (4K, 1 user, software; the user's request):

| | GNOME | KDE | XFCE | LXQt |
|---|---|---|---|---|
| delay p95: **1.7-2.5× the cap** of 50 ms (DEGRADED band 50-150; FAIL > 150) | 97 ms = 1.9× | 124 = 2.5× (beyond half the band) | 87-92 = 1.8× | 95-112 = 2.2× |
| the worst seconds (max of OURS per second) — inside the level there are some **above 150** | 141 ms | 152-262 | 102-115 | 169-170 |
| frames delivered in the job (user A browses: it delivers when the scene changes) — hardware → software | 10.3 → **8.6 frames/s** (−17 %) | 21.6 → **11.2** (−48 %) | 8.2 → **6.2** (−24 %) | 9.3 → **6.1** (−34 %) |
| skipped · holes · inputs lost | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 |

What limits it: **the encoder**. OpenH264 2.6.0 is opened by the product with «QP 25 costante (dal CRF
20) · CABAC · contenuto schermo · **4 fili**» (the threads are fixed by `ripiego.c`, on a 20-thread machine) and
encodes a 3776×2016 frame in **24-26 ms** median (key 14-17 ms; the worst seconds above
100 ms are the frames with a lot of change: the page scrolling): on its own it is half of the
50 ms cap, and with conversion (5.6 ms), copy and capture our stretch makes 43-62 ms median. The 4 threads keep
`remotix` at 0.3-0.7 cores: the CPU is not saturated (machine at 5-7 %), it is the latency of the encoder one
frame at a time that weighs — at 24 ms per frame the maximum rate is ~40/s and every frame pays its
time in full. No other quantity is close to a threshold (skipped 0 %, holes 0, stalls ≤ 0.13 s,
birth 2-3 s, short check GREEN).
The 4 threads are 4 **slices** per frame (`ripiego.c`, `RIPIEGO_H264_FILI` fixed, compiled: OpenH264
parallelises by slices, not by frames, so it does not add frames in the pipe); the price is a few
bytes. 🔸 A tuning candidate, NOT done here (it is a product choice): more slices on a machine with more
cores (8 or 16 out of 20) would shorten the time per frame at 4K — to be measured with the `18-software-confronto` bench
(which reads `RIPIEGO_H264_FILI` from the environment) before changing the number.

### 5.6 The Radeon: the A3 anomaly reconfirmed without libavcodec (step 1, 4K, KDE and GNOME)

`[M]` 30 Sep 23:28→23:49 UTC, campaigns `f18amd-4k-kde`, `f18amd-4k-gnome` (`16-coda.sh f18amd` with
`--scheda amd --gradini 1 --minuti 10 --minuti-ultimo 10`: the RX 6800 enters the box as
`renderD128`, VA driver «Mesa Gallium 25.0.7 for AMD Radeon RX 6800 (radeonsi, navi21)», the client browsers
stay on the Intel as in phase 16 §11). The «old» is `amd-b-4k-<desktop>/livello-01` of 27 Sep,
binary `28a947f5` with ffmpeg. Per frame: the child's lines «codec 3: … codifica N us» in the `server.log`
of the level (6 434 frames on KDE, 3 134 on GNOME), the same ones read in `fasi/16-a3-radeon-vcn.md`.

| Radeon RX 6800, 4K, 1 user | KDE old → **new** | GNOME old → **new** | (Intel KDE, for comparison) |
|---|---|---|---|
| level class | DEGRADED → **GREEN** | DEGRADED → **GREEN** | GREEN → GREEN |
| product delay p95 | 50.7 → **49.2 ms** | 55.8 → **48.8** | 39.6 → 38.7 |
| OURS p95 of the p95s · median | 41.7 · 8.8 → **40.2 · 8.9** | 46.8 · 9.3 → **39.8 · 9.3** | 30.6 · 19.3 → 29.7 · 19.1 |
| encoding per frame: median · p95 · **p99** · max | 8.7 · 9.7 · **30.9** · 38.2 → **8.7 · 9.8 · 30.9 · 34.0** | 9.1 · 10.5 · **31.0** · 38.4 → **9.1 · 10.4 · 30.9 · 32.3** | 8.1 · 8.4 · 8.6 · 10.7 → 8.0 · 8.4 · 8.6 · 11.0 |
| frames above 20 ms | 125 out of 6 436 (1.9 %) → **125 out of 6 434 (1.9 %)** | 60 out of 3 151 (1.9 %) → **60 out of 3 134 (1.9 %)** | 0 → 0 |
| how the slow ones are grouped | **25 runs of exactly 5** → **25 runs of exactly 5** | 12 of 5 → **12 of 5** | — |
| conversion (the card's EFC) · total STRETCH | 0.03 · 17.6 → **0.02 · 19.0** | 0.03 · 9.9 → **0.02 · 9.9** | 8.6 · 25.0 → 8.6 · 24.9 |
| longest stall · painted · skipped | 0.36 s · 1644/1644 · 0 → **0.06 · 1653/1653 · 0** | 1.18 s · 839/839 · 0 → **0.35 · 843/843 · 0** | |

⇒ **The A3 anomaly is still there, identical**: groups of **exactly 5 frames of ~31 ms** every 12-40 s,
1.9 % of the frames, p99 30.9 ms — same numbers with libva directly and with libavcodec. In phase 16 it was
localised «dentro `avcodec_send_frame`»: that was only the call in which the wait surfaced; it belongs to the
driver/iron (radeonsi, VCN 3.0), not to ffmpeg. The measures of `fasi/16-a3-radeon-vcn.md` and of the A3 anomaly
in `fasi/16-stress-e-capacita.md` §14 **stay valid** and the draft of the report to Mesa does not change. (The two
levels are GREEN today against DEGRADED on 27 Sep: the delay p95 sits 1-2 ms below 50 instead of
above — it is the same usual spread around the cap, not an improvement of the encoder, which
measures equal to the tenth.)

### 5.5 How many sessions the server bears WITHOUT a card (set K, the new measure)

The user's request (1 Oct): «quante sessioni regge il server quando codifica senza scheda», with the criteria
of the phase-16 campaign (§6 steps 1-4-8-12-16 with repetition and search halfway, §7 the four
jobs A/B/C/D — browsing, file manager, terminal, **4K video** in Firefox in the session —, §9 the
thresholds, one level = 10 min; §8 the scale: if a size gives way, it goes down). Same setup as §5.4
(`--senza-scheda`, OpenH264 2.6.0 with 4 slices, iHD hidden, declared by the product at every level).
Browsers alternating Firefox/Chrome, one per user, in the nested compositors on the server. `[M]` 30 Sep
22:04 → 1 Oct 04:37 UTC; evidence in `/media/REMOTIX/misure/fase16/f18sw-<misura>-<desktop>/`.

**The matrix** (in brackets the phase-16 campaign in HARDWARE, `intel-b`, same machine and same bench,
binary `45d048c8`): «good» = last level GREEN or DEGRADED not significant (the
non-continuation rule, §6); «true GREEN» = all sessions GREEN.

| without a card (OpenH264), Intel i5-13500T | GNOME | KDE | XFCE | LXQt |
|---|---|---|---|---|
| **4K** 3840×2160: last good · break | **0** · 1 (DEGRADED at 1 user, §5.4) *(hw: 3 · 4)* | **0** · 1 *(hw: 3 · 4)* | **0** · 1 *(hw: 8 · 9)* | **0** · 1 *(hw: 1 · 2)* |
| **1080p** 1920×1080: last good · break · true GREEN | **5** · 6 · 1 *(hw: 12 · 13 · 12)* | **5** · 6 · 4 *(hw: 11 · 12 · 8)* | **4** · 5 · 1 *(hw: 12 · 13 · 12)* | **4** · 5 · 1 *(hw: 12 · 13 · 12)* |
| **1440p** 2560×1440: last good · break · true GREEN | **2** · 3 · 2 *(hw: 8 · 9 · 1)* | **2 so far** · (4 broken; 3 interrupted) · 2 *(hw: 8 · 9 · 4)* | ⛔ not done *(hw: 11 · 12 · 8)* | ⛔ not done *(hw: 1 · 2 · 1)* |

**1080p, level by level** (class · who degrades and why · CPU of the `remotix` enclosure in cores · render GPU
of the Intel, which is shared among the sessions, the client browsers and the nested compositors):

| 1080p without a card | GNOME | KDE | XFCE | LXQt |
|---|---|---|---|---|
| 1 user | GREEN · delay p95 43 ms · `remotix` 0.15 · render 6 % | GREEN · 0.29 · 11 % | GREEN · 0.23 · 5 % | GREEN (the first pass DEGRADED because of a 1.10 s stall of the browsing actor, repeated GREEN) · 0.24 · 5 % |
| 4 users | DEGRADED not sign. (u1 A stall 1.12 s) · 1.39 · **84 %** | GREEN at the repetition (the first: 3 DEGRADED — u1 stall 1.01 s, u3 C and u4 D delay 52-53) · 1.68 · 87 % | DEGRADED not sign. (u4 D delay 56) · 1.46 · 79 % | DEGRADED not sign. (u4 D delay 58) · 1.47 · 79 % |
| 5 users (search) | DEGRADED not sign. (u4 D delay 57) · 1.67 · 86 % ⇒ **last good** | DEGRADED not sign. (u4 D 57) · 2.00 · 90 % ⇒ **last good** | **DEGRADED sign.** (4 out of 5: delay 51-72, D at 71) · 1.69 · 80 % ⇒ break | **DEGRADED sign.** (3 out of 5: u1 stall 1.18 s, u4 D 72, u5 A 66) · 1.71 · 80 % ⇒ break |
| 6 users (search) | DEGRADED sign. (u4 D 77, u5 A 65) · 1.92 · 88 % ⇒ break | DEGRADED sign. (u3 C 55, u4 D 71) · 2.16 · 91 % ⇒ break | DEGRADED sign. (3 out of 6: A 60, D 73, A 54) · 1.81 · 81 % | DEGRADED sign. (D 64, A 66) · 1.82 · 81 % |
| 8 users (step, + repetition) | DEGRADED sign. ×2: 8 out of 8 (delay 51-103, the two D at 96-103) · 2.24 · **99 %** | DEGRADED sign. ×2: 4 out of 8 (D at 95-112, A/B/C 53-64) · 2.84 · 99 % | **FAIL ×2**: the two D at **11 frames/s of video out of 30** (< 0.4·f) and delay 99-103; the other 6 DEGRADED (53-89) · 2.04 · 99 % | **FAIL ×2**: the two D at 11.3-11.7 frames/s and delay 92-104; 6 DEGRADED (55-78) · 2.06 · 99 % |
| OpenH264 encoding per 1080p frame (median of the STRETCH) | A/B/C **5-10 ms** · D (video) **22-30 ms** | 8-10 · 22-25 | 5-10 · 16-28 | 6-10 · 16-26 |

Readings:
- **Without a card, at 1080p, the server bears 4-5 sessions** with the four phase-16 jobs (against 11-12 in
  hardware); at 4K none within the 50 ms cap. The first to degrade is always a **D** user (the 4K video
  in Firefox in the session): at 1080p one of its frames costs OpenH264 **22-30 ms** (it is all change) against
  5-10 ms of the office jobs, and its delay p95 passes 50 ms already at 4-5 users; on the wlroots desktops (XFCE,
  LXQt) at 8 users the Ds go **FAIL** because the page paints 11 frames per second out of 30 (< 0.4·f).
- **The bottleneck is not the CPU**: at 8 users the `remotix` enclosure does 2.0-2.8 cores out of 20 and the machine sits at
  24-33 %; it is the **shared iGPU**: render at 99 % (the sessions' compositors, the 9 client browsers that
  decode and draw, the 9 nested labwc — the declared limit of phase 16 §15: the server also acts as the
  client). In hardware the same iGPU also encoded, and yet it bore 12: encoding in CPU with 4 slices brings
  the times per frame from 8 to 22-30 ms on the videos, and with render saturated the compositor delivers later.
  ⇒ On a machine **truly** without a card (no iGPU for the client browsers, which sit elsewhere) the number
  might be different: this is the lower bound measurable here, as for phase 16.
- The low «true GREEN» (1 on GNOME, XFCE, LXQt) is almost always **a stall of 1.0-1.2 s** seen by the browsing
  actor (threshold 1 s) — the same as in hardware; the «good» are DEGRADED not significant.
- Memory: `remotix` PSS 130-135 MB at 1 user, 750 MB at 8 (90 MB per extra session: OpenH264's
  buffers); no growth within the level beyond 5 %.

**1440p (2560×1440), as far as it got** (`[M]` 1 Oct 04:37→06:23 UTC, `f18sw-2k-gnome` whole; `f18sw-2k-kde`
stopped by the user during level 3 of the search):

| 1440p without a card | GNOME | KDE |
|---|---|---|
| 1 user | GREEN · delay p95 48.4 ms (at the edge of the cap) · OpenH264 encoding 12 ms · `remotix` 0.20 cores · render 8 % | GREEN · 49.5 · 11.5 ms · 0.43 · 18 % |
| 2 users (search) | GREEN · 49.9 · 12.5 ms · 0.34 · 14 % ⇒ **last good** | GREEN · 49.3 · 11.9 ms · 0.54 · 25 % ⇒ **good so far** |
| 3 users (search) | DEGRADED sign. (u1 A 50.8 · u3 C 52.8) · 0.40 · 16 % ⇒ break | ⛔ **interrupted** (stop, 06:23) |
| 4 users (step, + repetition) | DEGRADED sign. ×2 (3 out of 4: A 54-64, B 51-56, **D 96-99**) · 2.02 · 92 % | DEGRADED sign. ×2 (4 out of 4: A 56-59, B 56-57, C 59-60, **D 92-93**) · 2.28 · 96 % |

⇒ At 1440p without a card the server bears **2 sessions** (GNOME; KDE at least 2): already at 1 user the delay p95
sits at 48-50 ms, that is on the cap, with 11-12 ms of OpenH264 per frame; the fourth user (the video) brings it
to 92-99. 1440p on XFCE and LXQt: ⛔ **not done**.

### 5.7 What stays done, and what not — at the user's stop (1 Oct 2026, 06:23 UTC)

| | outcome |
|---|---|
| suite boxes redone from the recipes, versions equal to before (Firefox pinned), smoke round | ✅ §5.2 |
| the whole chain in HARDWARE with the new binary, 4K, step 1, 4 desktops | ✅ §5.3 — **indistinguishable** from phase 16 |
| the chain WITHOUT a card in 4K, 1 user, 4 desktops (set S) | ✅ §5.4 — DEGRADED (delay 87-124 ms), OpenH264 24-26 ms/frame |
| capacity WITHOUT a card (set K): 4K and 1080p on the 4 desktops; 1440p GNOME and KDE | ✅ §5.5 — 4K: 0 · 1080p: 5/5/4/4 · 1440p: 2/2 |
| capacity WITHOUT a card at 1440p on XFCE and LXQt; at 3K | ⛔ not done |
| the Radeon: A3 reconfirmed without libavcodec | ✅ §5.6 |
| set M (the card from memory with the product in the boxes) | ⛔ not done — §4 (30 Sep) remains |
| set C (the loop of phases 4/6/7/8) | ⛔ not done — only step 1 in hardware of §5.3 |
| the tuning of OpenH264's slices | ⛔ not done (candidate, §5.4) |

**The state the boxes are left in** (06:24 UTC): `rete11-{gnome,kde,xfce,lxqt}` redone from the new image
(iHD driver present, no `.nascosto`), product `4b39195c` and page `fb9a18f3`, servers on in
**hardware** («H.264: scheda si', software OpenH264 si'», ECCOMI «hevc,h264»), `nictest` and `provanic` inside,
no tenant of the benches, `FERMA` removed, no bench actor/browser alive; on the host the two `labwc`
of `15-compositori` from before (not ours). The evidence: `/media/REMOTIX/misure/fase16/f18hw-4k-*`,
`f18sw-{4k,fhd,2k}-*`, `f18amd-4k-*` (log `banchi/16-stress/registro.jsonl` on the server),
`/media/REMOTIX/misure/fase15/giro18-scatole-nuove{,-r}`, `/media/REMOTIX/misure/fase18/` (build,
rounds, `salite.log`). The tools used and not kept: `/media/REMOTIX/tmp/{f18-salite,f18-salite-2,
rimetti-18,costruisci-18}.sh`, `f18-estrai.py` (agents' reports, they are not kept).
