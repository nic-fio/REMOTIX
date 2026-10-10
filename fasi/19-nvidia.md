# Phase 19 — Encoding always on the card: Vulkan first

*Opened on **1 Oct 2026** (`DECISIONI.md` §10.27). The user's requirement: on a machine with a card
capable of encoding, REMOTIX encodes **on the card**, NVIDIA included. Today on NVIDIA it falls back to the
processor (OpenH264).*

## 1. The route (decided on 1 Oct, `DECISIONI.md` §10.27)

The choice is made **by capability**, at startup, not by brand:

| order | route | who uses it today |
|---|---|---|
| 1 | **Vulkan Video** (H.264 for Firefox, HEVC for Chrome) | AMD (RADV, `[M]` Mesa 25.0.7), NVIDIA (proprietary driver) |
| 2 | **VA-API** (`src/vadiretta.c`, as it is today) | Intel integrated and Arc (in Vulkan only experimental, `[M]` Mesa 26.2.3) |
| — | ⛔ no processor | without a capable card REMOTIX does not install |

## 2. The work
1. The Vulkan route (H.264 and HEVC encoding, zero copy from dmabuf, colour conversion on the card), tested
   on the Radeon against VA-API: a stream of the same type, quality and times no worse.
   ✅ **module and test** (1 Oct, §3): `src/vulkanvideo.c/.h` + `banchi/19-vulkan/`; ✅ **the graft** (1 Oct,
   `1ddaa89`): in `codificatore.c` the route is chosen by capability when each encoder is opened
   (`h264_scheda`/`hevc_scheda`: `vulkanvideo_capacita()` for the node and the codec, if it encodes Vulkan, otherwise
   VA-API saying why; `*_vulkan`/`*_vaapi` by name, with no fallback), `--codifica scheda|vulkan|vaapi` to
   force it, `--prova-codifica` states the route (`strada`, `hevc_strada`, `h264_strada`), the `Makefile` and
   `src/Contenitore` (`libvulkan-dev`); ✅ `installatore/motore/strade.go` (`3a00878`): the «vulkan» route
   active with the ICD probe, proprietary NVIDIA admitted if it has its ICD; ✅ packages, build
   containers and boxes (`6c2ca0d`). `[M]` 1 Oct on the server: Intel → `vaapi`, Radeon → `vulkan`, H.264 and HEVC.
2. Out with the software fallback (`src/ripiego.c`, `src/colori709.c` if it is no longer needed by the from-memory route,
   OpenH264, SVT-AV1) from the product, the packages, the catalogue and the installer's engine; the preliminary
   check refuses without a capable card, with the reason.  ⭐ Done by line 1 (§3);
   `src/colori709.c` STAYS: it serves VA-API's «from memory» route.
3. **The anti-regression net** (the user's words, 1 Oct: *«bisognerà rivedere tutti i 4 DE per evitare che uno
   di loro smetta di funzionare»*): the full phase-15 suite runs **twice** on the 4 boxes (GNOME, KDE,
   XFCE, LXQt), with the real browsers in 4K — **Intel = VA-API** (nothing that is green today must break) and
   **Radeon = Vulkan** (the card passed to the boxes as in phase 16, `--scheda amd`). A desktop is fine
   only if it is green in both rounds. T10 reduced to the clean refusal in the VMs; the full installer
   tests in the containers with the real card.
⭐ **The priorities** (the user's words, 1 Oct: *«la precedenza assoluta va alla suite di funzionalità: quelle devono
restare inalterate. Per la suite delle performance quella dovrà essere rimisurata da capo»*): (a) the phase-15
suite is relaunched **identical** and must come back green on the 4 desktops in both rounds — ⛔ a red test is
cured in the **product**, never by retouching the test; the only exception is a test that looks at a behaviour changed
on purpose by the user (today: the canvas above 4096 reduced instead of refused), and it is updated **declaring it**, with
the decision next to it; (b) the performance campaign is redone **from zero**, once, with the architecture finished, with a
plan approved beforehand by the user.

⭐ **Android** (the user's words, 1 Oct: *«ricordiamoci poi il discorso Android»*): the two rounds of the suite also include
**Chrome on Android** (the emulator on the server, `/media/REMOTIX/android`, as per the project memory: Chrome,
never Firefox Android, §7.18), at least the tests that touch the client: connection, H.264 and HEVC video, keyboard,
touch, clipboard, re-entry.

4. ✅ **NVIDIA on rent** (the user's words, 1 Oct: *«al momento opportuno noleggerò un server nvidia per 1 o 2
   giorni»*). ⇒ Before the rental a **ready bench** is prepared (`banchi/19-nvidia/`): on a freshly
   started machine it installs desktop, REMOTIX and the suite, and runs it without improvising. What to rent: an NVIDIA card
   from the RTX 20 / T4 series up (L4, A10, RTX are fine), Ubuntu or Debian, root access via ssh, NVIDIA driver
   ≥ 550. Account and card are the user's.
   ✅ **The bench is ready** (1 Oct, log §3): `banchi/19-nvidia/` — `LEGGIMI.md` for the user,
   `19-nvidia.sh prepara` (before, on the laptop) and `19-nvidia.sh tutto INDIRIZZO` (on the day of the
   rental), `pulisci INDIRIZZO` at the end. System: Debian 13 or Ubuntu 26.04 (⛔ 22.04/24.04 no);
   ⛔ no A100/H100/H200 (no video encoder).
   (old entry) ❓ NVIDIA: a real card is needed (in the server, or a rented machine). The route exists (Vulkan Video, the
   same as the Radeon's): `remotix --prova-codifica` to be tested with the proprietary driver and its ICD.
5. ❓ After the graft: the `rete11-*` **boxes** must be rebuilt (`libvulkan1` + `mesa-vulkan-drivers` in the
   recipes, `6c2ca0d`) before the net of point 3, or the Radeon in the boxes stays on VA-API (and the log would
   say so: *«Vulkan Video NON è adatta … ⇒ si prova VA-API»*).
   ✅ **Done** (1 Oct, log §3): the 4 boxes rebuilt from the `fase-19` recipes, with the RADV ICD inside; Intel round GREEN, Radeon round in Vulkan (with the defect below).
6. ✅ **Closed on 3 Oct 2026 — `remotix.pam`** (`cb6061e`: in the boxes the product's file, md5 `467ee6bb`, and `utenti-negati`=root like `provisiona.sh`; full net `pam-d3-intel` **702 PASS**, 2 BLOCKED = F-030 in parallel; `banchi/11-scatole/11-pam-root-negato.py`: root rejected by the list and nictest in, 4/4). It was: **Open point — `remotix.pam`**: in the `rete11-*` boxes the PAM file remained the phase-18 one
   (`rete11/prodotto/remotix.pam`, md5 `d1734958`, `@include common-session-noninteractive` + `pam_systemd`),
   NOT the one of `src/remotix.pam` from phase 17/D3 (sshd, `pam_listfile` on `/etc/remotix/utenti-negati`, root
   excluded). The suite was relaunched **identical** to phase 18 (the priority rule), so it was not
   touched; but aligning it (and putting the file `/etc/remotix/utenti-negati` in the boxes) is a decision of its own —
   to be done in a dedicated round, not inside the anti-regression net.
7. ⛔ **The phase-19 defect to be decided** (log §3): **Vulkan** encoding on the RX 6800 goes into a GPU hang
   (`VK_ERROR_DEVICE_LOST` ⇒ amdgpu page fault ⇒ ring gfx/vcn_enc timeout ⇒ MODE1 reset, VRAM lost) on the **canvas
   change** (`F-018`/`P-C`, 4K→2560→4K); VA-API on the same resize is clean. The reset wipes the shared card
   and brings down in cascade the sessions of all the boxes in parallel. The cure is neither minimal nor obvious (the border with
   the RADV/amdgpu driver): **the user chooses it** before redoing the Radeon round.

## 3. The change log — for the technical manual

| commit | what | why | measure | installed |
|---|---|---|---|---|
| `9162e76` | **CPU fallback out of the product**: removed `src/ripiego.c/.h` (OpenH264 via dlopen, SVT-AV1), the `sw_*` border of `codificatore.c`, `codificatore_ripiego_software/_software_pronto/_software_rimedio`, `CRF_SOFTWARE`, `--software` of `--prova-codifica`, AV1 from the survey. `codificatore_di()` opens only `h264_vaapi`/`hevc_vaapi`; any other name is refused with the reason. `--prova-codifica`: outcome `hardware`\|`nessuno`, no `rimedio`, codes **0** card · **1** opens but nothing comes out · **2** usage · **3** no card. At startup the server declares it (*«QUESTO SERVER NON SA CODIFICARE VIDEO»*, with the reason per codec) and the `ECCOMI` offers no codec. Makefile: openh264/SvtAv1Enc out of CFLAGS, LIBS, `MINIMI` and checked headers (`-ldl` stays: libselinux in `figlio.c`). `colori709.c` STAYS (the «from memory» route). Build containers and boxes without the two libraries; `costruisci-tutti.sh` refuses an `ldd` that names them. 18-* benches: they compile without `src/ripiego.c` (18-software takes it from git `6bacca7`, as history) | `DECISIONI.md` §10.27: *«niente cpu senza scheda»*, *«eliminare la questione della codifica su cpu senza scheda»*, independence from ffmpeg and other pieces for the licences | `[M]` 1 Oct, on the server (`/media/REMOTIX/src/f19-cpu`): `--prova-codifica` Intel renderD128 H.264 and HEVC = `hardware`, code 0; Radeon renderD129 H.264 and HEVC = `hardware`, code 0; `--nodo /dev/dri/renderD199` = `nessuno`, code **3**; `--software` = usage, code 2. Server on 7633 with the VA driver hidden (`LIBVA_DRIVERS_PATH` empty): ⛔⛔ line at startup, `offerti` empty; with the card `«hevc,h264»`. `ldd` of the binary (container) without openh264/SvtAv1 | no |
| `35e3b44` | **OpenH264 and SVT-AV1 out of the packages**: `debian/control` (Build-Depends, Recommends `libopenh264-8 \| libopenh264-cisco8`), `remotix.spec` (BuildRequires, `Recommends: openh264` on Fedora and Alma), `PKGBUILD` (depends `openh264`, `svt-av1`), the licence text | as above | — (they are built with the release) | no |
| `2246cbc` | **OpenH264 and SVT-AV1 out of the installer, and the preliminary check that refuses without a card**: catalogue 2026.10.01.9 (seq. 9) without the `openh264` repository, `software_di_serie`, `pacchetti_software`; engine without the «openh264» repository type (`fedora-cisco-openh264`, `epel-cisco-openh264`, `repo-openh264`), `deposito.resta_epel`, the facts `h264.software`/`h264.openh264`, the C-RIPIEGO conditions; `consenso.deposito.openh264` withdrawn (an old file ends up among the «superflue»); RX-H264-005 and RX-GPU-001 withdrawn, RX-FUORI-005 rewritten without fallback. ⭐ `motore/strade.go`: the `StradeCodifica` table (vulkan declared and not active, vaapi active) and `VerdettoScheda` — to add Vulkan, `Attiva: true` with its `Rileva`/`Schede` is enough. New BLOCKING codes: **RX-GPU-003** no card, **RX-GPU-004** only NVIDIA with the proprietary driver (comes with the Vulkan route), **RX-GPU-005** no Intel/AMD (virtio, VMware, nouveau), **RX-GPU-006** Intel/AMD that on this distro does not encode without drivers to be added (today AMD on Alma). The card that is completed with a third-party repository stays a warning with consent (D5). The test after installation: output 3 = FAIL. EPEL on Alma STAYS (KDE, RPM Fusion EL): only the SVT-AV1 part goes | `DECISIONI.md` §10.27 | `[M]` `installatore/costruisci.sh prove`: **205 PASS**, 0 FAIL, `go vet`/`gofmt` clean; counter-test: with the verdict that never refuses, three tests turn red. ⚠ Not re-measured whether `intel-media-driver` from RPM Fusion EL pulls dependencies from EPEL. ⚠ A machine installed with the phase-18 engine with the «openh264» step in the log does not uninstall with the new engine (lab boxes only) | no |
| `49cce49` | **Line 2: the Vulkan Video encoder** — `src/vulkanvideo.c/.h` (standalone module, not yet grafted into `codificatore.c`): capability discovery per DRM node (`vulkanvideo_capacita`: card chosen with `VK_EXT_physical_device_drm`, not «the first one»), H.264 High / HEVC Main / Main 10 session with `VK_KHR_video_encode_h264/h265`, `StdVideo*` parameter sets with the same values as `vadiretta.c` (no B, one reference, limited BT.709 in the VUI, level computed like ffmpeg or imposed), SPS/PPS/VPS taken from the driver (`vkGetEncodedVideoSessionParametersKHR`, one set per call) and put in Annex-B in front of every key, CQP and VBR with the cap (mean = target, maximum = wire, buffer 40 ms, requested QP = the regulator's minimum QP), key on request, hot quality change, canvas change (reopening), `ULTRA_LOW_LATENCY` requested in the profile; zero-copy input from DMA-BUF (`VK_EXT_external_memory_dma_buf` + `VK_EXT_image_drm_format_modifier`, cache per generation like `codificatore.c`) and from memory (BGRx/RGBx → staging buffer → RGB image); RGB→NV12/P010 conversion with the compute shader `src/vulkanvideo_rgb_nv12.comp` (SPIR-V embedded in `vulkanvideo_rgb_nv12_spv.h`, generated by `banchi/19-vulkan/19-shader.sh`), which rewrites `colori709.c` in integers: same coefficients, same 1-3-3-1 chroma filter; it writes directly into the planes (`R8`/`R8G8` views on the NV12 image with `MUTABLE_FORMAT`+`EXTENDED_USAGE`) or, where the card does not allow it, into two images and then `vkCmdCopyImage` into the planes. Bench `banchi/19-vulkan/` (`19-confronto.c/.sh`, `19-tabella.py`, `19-decodifica-chrome.sh`): the scene of bench 18, Vulkan against VA-API (the product) on the same Radeon | `DECISIONI.md` §10.27: Vulkan first, chosen by capability | `[M]` 1 Oct 2026, server, Radeon RX 6800 (RADV, Mesa 25.0.7, devroot Debian trixie), 120 frames at 60 fps of fake desktop, QP 26, 42 tests, **all 120/120 decoded** (ffmpeg as a tool). **Quality**: from memory the shader gives the SAME planes as `colori709.c` — PSNR identical to the digit (H.264 1080p 39.619 dB both; 4K 42.646; HEVC 44.54/44.55; HEVC10 44.97/44.97) and in Chrome **pixel fingerprints EQUAL** (1080p and 4K H.264). From the card (zero copy) Vulkan converts better than radeonsi's VPP: H.264 1080p 39.62 dB against 38.55 (u: 39.5 against 36.9), 4K 42.65 against 39.02; HEVC 1080p 44.55 against 42.15, 4K 46.93 against 40.57 — with bytes +11 % at 1080p H.264 (higher quality, same bytes as the from-memory route) and −6 % in HEVC 4K. **Times** (median per frame, zero copy): encoding H.264 1080p 2.96 ms Vulkan against 3.35 VA-API, 4K 9.74 against 11.25; HEVC 1080p 3.06 against 3.38, 4K 9.79 against 11.61; HEVC10 4K 9.77 against 9.82; Vulkan conversion 0.55-0.62 ms at 1080p and 1.7-1.8 ms at 4K (with the fence wait inside; VA-API's VPP counts 0 because it is asynchronous and its cost sits in the encoding); from memory the Vulkan upload+conversion 0.84-0.94 ms at 1080p (VA-API 1.8-2.2 in CPU), 3.1 ms at 4K (VA-API 6.5-8.6). The copy route (forced with the bench's `REMOTIX_VULKAN_CONVERSIONE=copia`) gives **identical bytes** to the direct one (4/4, `cmp`) and costs +0.06 ms at 1080p, +0.2 ms at 4K. **Profile/level/colour** (ffprobe) equal to VA-API in all tests: High L4.2/L5.2, Main L4.0/L5.0, Main 10, yuv420p, tv, bt709×3. **Key on request** (frame 40: 583 KB, then delta), **new canvas** (60: reopening and key 1280x720), **hot quality** (60: QP 26→36, PSNR 39.6→33.4 H.264), **cap** 20 Mbit/s (does not bite: the scene costs 8.5 Mbit/s; Vulkan stays at QP 26 = 2.14 MB, radeonsi's QVBR drops all the same to 1.31 MB and 35.9 dB) and **cap 2 Mbit/s** (bites: Vulkan 640 KB with the key reduced to 307 KB, VA-API 784 KB; HEVC Vulkan 619 KB at 37.0 dB against 760 KB at 32.4). **Real Chrome 154, WebCodecs** (`19-decodifica-chrome.sh`): 8/8 H.264 tests PASS (1080p, 4K, key, canvas, cap, cap2: 120/120); HEVC NOT TESTED (headless Chrome without GPU does not configure `hev1`, with and without the VA-API/Vulkan flags, as in phase 18). **What the RADV 25.0.7 driver cannot do / does its own way**: `transform_8x8` NO (`stdSyntaxFlags` 0x5880: CABAC yes, 8x8 no — written regardless, the stream would not decode, «error while decoding MB 0 0»); `maxLevelIdc` not declared (0): the level structure in the session is omitted; in HEVC it writes `general_level_idc` in H.264's alphabet (40 for 4.0, 31 for 3.1): the module corrects the byte in the VPS and in the SPS and declares it (`livello_corretto_nei_byte`); `hasOverrides` always true on the parameter sets; `imageUsageFlags` of the video properties reports only the requested usage (the direct/copy choice is made with `vkGetPhysicalDeviceImageFormatProperties2`); the validation layer flags the `STORAGE` views on the NV12 planes (VUID 02275) but the result is bit-identical to the copy: a false positive to be clarified. Radeon capabilities: H.264 up to 4096x4096, HEVC 8192x4352, RC CQP/CBR/VBR, QP 0-51, 2 quality levels, granularity 16x16 (H.264) and 64x16 (HEVC). **Intel UHD 770 (ANV, Mesa 25.0.7)**: no `VK_KHR_video_encode_queue` even with `ANV_DEBUG=video-encode` — the experiment could NOT be done with the host's Mesa (with Arch's 26.2.3 it was there, §10.27); on Intel the route stays VA-API | no (module and bench; no product file touched) |
| `7f0e8f6` | **the canvas at most 4096×2304** (it was 7680×4320): `RCP_TELA_L/A_MASSIMA` in `rcp.h` (and the twin `banchi/rcp/`), `TELA_L/A_MASSIMA` in `pagina.html`, `RCP.md` §4.5, `SPECIFICHE.md` §6.1-bis. ⭐ **Above the maximum it is not refused: it is reduced** — the side that overflows goes to the maximum, the other stays (5120×2880 → 4096×2304, 5120×1440 → 4096×1440), with the line «⚠ RIPIEGO DICHIARATO (§4.5)» in the log, in `ATTACCA` (before it was `ERRORE_PROTOCOLLO`) and in `ADATTA_TELA` (before `TELA(MISURA_FUORI_LIMITI)`, now `TELA(ADATTATA)` at the reduced size). Below the minimum (320×240) and the odd size stay refused as before. The page itself already asks for at most the maximum, with the same rule (`tela_da_chiedere()`); the maximum is a constant of the protocol, not a field of the `ECCOMI` (the wire does not change). The check of the driver's maximum size in `codificatore.c` STAYS: it belongs to the driver, not to the protocol | the user's decision, 1 Oct: *«4096 max di larghezza va benissimo, non ho mai preteso di più»* — H.264 on Intel (`EncSliceLP`) stops at 4096 px per side and Firefox on Linux receives only H.264; 2304 = 16:9 at 4096 and `MaxFS` of the H.264 levels 5.1/5.2 (36 864 macroblocks) | `[M]` 1 Oct, laptop: `rcp_misura_ammessa()` directly — 3840×2160 and 4096×2304 equal, 5120×2880 and 7680×4320 → 4096×2304, 5120×1440 → 4096×1440, 319×240 refused; the page's `tela_da_chiedere()` (node) gives the same numbers; build in the container and on the server (`enter.sh`) clean. ⚠ **A real attach NOT tested** (Python client or Chrome) on the running product: the passwords of `prova`/`prova2` changed on 29 Sep and the one in `credenziali-banchi` is rejected by PAM. ⚠ Old benches that demand the refusal above 7680 (`04-b31` case 5, `06-b36` cases 14-15, `06-b35`, `06-b38`, `06-b40`, `01-b4`) not updated | no |
| `1ddaa89` | **THE GRAFT: the card's route is chosen by capability** — `codificatore.c`: `apri_dispositivo()` asks `vulkanvideo_capacita()` for the node and the codec (profile H.264 High / HEVC Main / Main 10, canvas between the card's min and max, the bitrate mode the cap asks for — VBR with the cap, CQP without —, the QP in the declared range, RGB input: the bench in yuv420p10le stays on VA-API); if suitable it opens `vulkanvideo_apri_dispositivo` and the route is `vulkan` (zero copy from the DMA-BUF and conversion in the shader; from memory the BGRx/RGBx go up and the shader converts them, no NV12 staging), otherwise it writes why and goes to VA-API. ⭐ **Six names** (`codificatore.h`): `h264_scheda`/`hevc_scheda` by capability (the product), `*_vulkan` and `*_vaapi` by name — requested by name it does not fall back on the other. `apri_scheda_vulkan()` with the same numbers as VA-API (cap in three numbers, buffer ≤ 50 ms, level §4.3, keys on request); `chiudi/apri_contesto` per route; `codifica_vulkan()` is the ONLY `if` between the two routes inside `comprimi_comune()`, before the byte border: everything downstream (16 MiB, scale and climb back, cap, `forma_va_bene`, confession from the SPS, D-023 frame, key on request, resize) stays one. Confession: `strada` («vaapi»/«vulkan»), `componente` = the name opened, `fornitore_va` = card + Vulkan driver, `modo_bitrate` 3 = VBR, `misura_massima`/`modi_bitrate` from the Vulkan capabilities (entrypoint: does not exist in Vulkan, `bassa_potenza_verificata` false). `codificatore_strada()`. `figlio.c`: `componente_di()` from `--codifica scheda|vulkan|vaapi` (server, passed to the child like the phase-9 cures; `--prova-codifica`); the JSON carries `strada`, `hevc_strada`, `h264_strada`, yesterday's fields unchanged (`codificatore` is `h264_vulkan`/`h264_vaapi`). `Makefile`: `vulkanvideo.c`, `pkg-config vulkan` (`-lvulkan`), MINIMI `vulkan:1.3.274`, `vulkan/vulkan.h`, `-Wno-missing-field-initializers` only on `vulkanvideo.o`; `src/Contenitore`: `libvulkan-dev` | `DECISIONI.md` §10.27: Vulkan first, by capability, no processor | `[M]` 1 Oct 2026, server (`/media/REMOTIX/src/f19-innesto/albero`, binary built in `enter.sh`): `--prova-codifica` **Intel renderD128**: H.264 and HEVC `hardware` via `h264_vaapi`/`hevc_vaapi` (route `vaapi`, EncSliceLP), forced `--codifica vulkan` → `nessuno`, code **3** (*«nessun dispositivo Vulkan con la coda di codifica … Intel(R) UHD Graphics 770»*); **Radeon renderD129**: H.264 and HEVC `hardware` via `h264_vulkan`/`hevc_vulkan` (route `vulkan`, *«AMD Radeon RX 6800 (RADV NAVI21) · radv Mesa 25.0.7»*), forced `--codifica vaapi` → `vaapi` (full EncSlice); 256×256 one H.264 frame: 1221 bytes in Vulkan against 1386 in VA-API, HEVC 1435 against 1420; `offerti` «hevc,h264» on both; non-existent node → code 3. ⚠ **HEVC string**: Vulkan declares `hev1.1.2.L60.B0`, VA-API `hev1.1.6.L60.B0` — the profile compatibility byte is written by the driver (RADV: Main only; iHD/radeonsi: Main + Main 10): to be checked in Chrome (bench 19 of 1 Oct decodes it with ffmpeg, Chrome HEVC not tested). Build in the container clean (no warning in the three files touched; `ldd` carries `libvulkan.so.1`) | no |
| `3a00878` | **installer: the «vulkan» route active** — `strade.go`: `rilevaVulkan` reads the loader's ICDs (`/usr/share/vulkan/icd.d`, `/etc/vulkan/icd.d`; `radeon_icd.x86_64.json` → `radeon`, `nvidia_icd.json` → `nvidia`, `lvp`, `intel`…) into `codifica.vulkan.icd` («nessuno» if empty) and `codifica.vulkan=attiva`; `schedeVulkan` = AMD with the `radeon` ICD, NVIDIA with the proprietary driver and the `nvidia` ICD (⛔ Intel no: ANV experimental, stays on VA-API); `SchedaSullaStrada` and the NVIDIA C-HARDWARE condition only WITHOUT ICD (`compatibilita.go`). Codes: **RX-GPU-004** = proprietary NVIDIA WITHOUT the Vulkan driver (remedy: the full driver with the ICD, or an Intel/AMD alongside), RX-GPU-002/005/006 rewritten with the two routes, it/en; `operazione.go` reads `strada` from `--prova-codifica` (a binary that does not write it passes all the same). ⚠ The preliminary check does NOT launch programs nor open the card (R1): the real test stays 7a. `[?]` The minimum Mesa version with RADV encoding by default is not measured (`[M]` 25.0.7 yes): on an older Mesa the preliminary would say yes and 7a no | `DECISIONI.md` §10.27 | `[M]` 1 Oct 2026: `installatore/costruisci.sh prove` gofmt/vet clean, `go test` ok; new: `TestStradaVulkan` (NVIDIA with ICD → passes without C-HARDWARE; without ICD → RX-GPU-004; only `lvp` → RX-GPU-004; AMD with RADV and no VA driver → passes; Intel with ANV → VA-API), the certification with `h264_vulkan` GREEN, the routes «vulkan,vaapi» | no |
| `6c2ca0d` | **packages, build containers, boxes**: `src/costruzione/Contenitore.*` with the loader+headers per distro; `.deb` Build-Depends `libvulkan-dev (>= 1.3.274)` and Recommends `mesa-vulkan-drivers`; `.rpm` BuildRequires `pkgconfig(vulkan) >= 1.3.274`, Recommends `mesa-vulkan-drivers`; Arch depends `vulkan-icd-loader`, makedepends `vulkan-headers`, optdepends `vulkan-radeon`/`nvidia-utils` (⚠ pacman's virtual `vulkan-driver` would ask for it: the card's driver is put in by the engine, T4 — to be added to the catalogue); `rete11-*` boxes (4 recipes): `libvulkan1` + `mesa-vulkan-drivers` (RADV for the Radeon) | the «Radeon = Vulkan» net (§2.3) without the ICD would measure VA-API | `[M]` 1 Oct 2026 in the podman images: Debian 13 `libvulkan-dev` 1.4.309, Ubuntu 26.04 1.4.341, Fedora 44 `vulkan-loader-devel` 1.4.341, Alma 10 1.4.328 (AppStream, not CRB), Leap 16 `vulkan-devel` 1.4.309, Tumbleweed 1.4.357, Arch `vulkan-headers`/`vulkan-icd-loader` 1.4.357, `vulkan-radeon` 26.2.3; `mesa-vulkan-drivers` Debian 25.0.7. ⚠ The images and the boxes have NOT been rebuilt | no |
| `ccec594` | **the old canvas benches to the new rule** (above 4096×2304 it is reduced): `04-b31` case 5, `06-b36` cases 14-15 and the mutations H11/H12 (anchors of today's `rcp.c`), `04-b31-certifica` G9, `06-b35` «limiti» round, `06-b38` round 3 and the arbiter's mutation, `06-b40` mirror and cases 3/8, `01-b4` arbiter (ATTACCA: minimum and parity, the maximum belongs to the granted canvas) and recordings 38/39 at 4096×2304 | the ⚠ line of `7f0e8f6` | `[M]` 1 Oct 2026, container: `04-b31` case 5 OK; `06-b36` 14 and 15 OK; `01-b4-lancia.py` **57 out of 57**. ⛔ **They stay red, and they were red before**: `04-b31` cases **9** («il palco fa di testa sua») and **18** («due sessioni, un palco solo»), `06-b36` cases **12** («il palco cambia tre volte da sé») and **24** («la data zero del ripiego senza orologio»); for those reds the two `*-certifica.sh` stop at «ROSSO sul codice intatto» and the mutations do not run (the new anchors verified by hand in `rcp.c`). ⚠ `06-b35`, `06-b38`, `06-b40` not rerun (they want the server running and the test client) | no |
| `(questo commit)` | **the benches on the integrated tree and the documents**: `banchi/19-vulkan/19-confronto.{c,sh}` + `19-tabella.py` with the third engine **`scheda`** (the integrated product: `h264_scheda`/`hevc_scheda`, the choice by capability inside `codificatore.c`, with all the cures downstream of the bytes; the JSON carries `strada_scheda`); `banchi/18-scheda/18-confronto.sh` compiles the integrated encoder (`vulkanvideo.c`, `-lvulkan`) and measures VA-API by name; `SPECIFICHE.md` (RX-GPU-004/005/006, the grafted route); this log | the anti-regression net of §2.3 starts from here | `[M]` 1 Oct 2026, server, tree `/media/REMOTIX/src/f19-innesto/albero` (binary `src/remotix` built in `enter.sh`, commit `1ddaa89`+). **19-confronto on the Radeon** (`tmp/confronto19`, 62 tests, all code 0 and 120/120 decoded): the integrated product («scheda») gives **the same bytes and the same PSNR as the Vulkan module** alone, test by test (e.g. H.264 1080p zero copy 2 124 327 bytes, 39.619 dB; 4K 1 957 479, 42.646; HEVC 1080p 1 495 205, 44.546; HEVC10 4K 2 828 429, 47.480) — and so against VA-API on the same card what line 2 had measured holds: zero copy H.264 1080p 39.62 dB against 38.55, 4K 42.65 against 39.02, HEVC 1080p 44.55 against 42.15, 4K 46.93 against 40.57, HEVC10 4K 47.48 against 44.72; median of H.264 1080p encoding **2.99 ms** (VA-API 3.68), 4K 9.66 (11.24), HEVC 1080p 2.96 (3.80), 4K 9.88 (11.51); conversion in the shader 0.44-0.69 ms at 1080p, 1.77-1.86 at 4K, from memory upload+conversion 0.84-0.96 ms (VA-API in CPU 1.7-2.2) and 3.05-3.23 at 4K (6.6-8.6). Key on request, new canvas, cap 20 and cap 2 Mbit/s: all green and identical to the module. The differences from VA-API already known (bytes +11 % at 1080p H.264 zero copy with PSNR +1 dB; cap 20 does not bite in Vulkan, +61 %/+33 % bytes with higher PSNR; cap 2 H.264 30.18 → 28.18 dB with −18 % bytes, HEVC 32.36 → 37.02). **18-confronto** (`tmp/confronto18`, Intel and Radeon, VA-API by name, old libavcodec against integrated): *«nessuna prova in cui il nuovo sia peggio del vecchio»* — bytes and PSNR equal to the digit on the zero copy on the two nodes, key/canvas/cap included. **The running product** on port **7651** (`accendi-7651.sh` in `/media/REMOTIX/src/f19-innesto/`, unit `remotix-7651`, log in `/media/REMOTIX/tmp/f19-innesto/registro.log`): it starts, declares *«strada per capacità su renderD128 — Vulkan Video NON è adatta (… non ha VK_KHR_video_encode_queue) ⇒ si prova VA-API»*, opens `hevc_vaapi`/`h264_vaapi` (*«strada vaapi (chiesta «scheda»)»*), `ECCOMI` «hevc,h264». ⚠ The session server opens `NODO_RENDERING` = renderD128 (Intel): the Radeon in Vulkan in the running product is seen in the boxes with `--scheda amd` (the mapped node), not on this port. ⚠ Real Chrome NOT rerun on the integrated tree (`19-decodifica-chrome.sh` remains line 2's); Vulkan's HEVC string is `hev1.1.2` (compat Main only) against VA-API's `hev1.1.6`: to be checked in Chrome with the net. ⚠ The `rete11-*` boxes not rebuilt | no — binary ready in `/media/REMOTIX/src/f19-innesto/albero/src/remotix` |
| `(questo commit)` | **THE ANTI-REGRESSION NET (§2.3): the 4 boxes rebuilt, Intel=VA-API round GREEN, Radeon=Vulkan round with the FIRST DEFECT of phase 19** — (1) `banchi/15-suite/registro.jsonl` (copy from the server, additions only) with the rounds `19-intel` and `19-radeon`; (2) generated reports `banchi/15-suite/rapporto-giro19-intel.{txt,html}` and `rapporto-giro19-radeon.{txt,html}` (never written by hand); (3) the tools `banchi/15-suite/19-scatole-scheda.sh` (redoes the 4 boxes on `intel`\|`amd`, like `15-rifai-scatole.sh` but with `REMOTIX_SCHEDA`) and `banchi/15-suite/19-f018-prova.sh` (binary/route comparison on one box). ⚠ `rete11/prodotto/remotix.pam` remained the phase-18 one (pre-D3): see the open point in §2 | the user's anti-regression net (1 Oct): *«bisognerà rivedere tutti i 4 DE»*, and §2 ⭐ «la precedenza assoluta va alla suite» | `[M]` 1 Oct 2026, server (i5-13500T · Intel UHD 770 · AMD RX 6800 renderD129, RADV Mesa 25.0.7, kernel 7.0). **The boxes**: rebuilt FROM ZERO from the `fase-19` recipes (`Contenitore.*` with `libvulkan1`+`mesa-vulkan-drivers`, without OpenH264/SVT-AV1, `firefox-esr` 140.16.0esr from the host's .deb on `hold`), binary of **HEAD `fase-19` (`0a1715f`)** built on the server in `enter.sh` (`src/costruisci.sh`, md5 **`18746ac2`**), page `210ff091`. Versions inside = phase 18 §5.2 and host (`intel-media-va-driver` 25.2.3, `libva2`/`libva-drm2` 2.22.0-3, `mesa-va-drivers`/`libgl1-mesa-dri`/`mesa-vulkan-drivers` 25.0.7-2+deb13u1, `libigdgmm12` 22.7.2, `libvulkan1` 1.4.309); `nictest` (sudo video render) in all four; `radeon_icd.json` present. **ROUND 1 — Intel = VA-API** (`19-intel`, route `vaapi` on all, ECCOMI «hevc,h264»): **337 healthy passes PASS + 336 with the fault seen = 673, 0 FAIL, 0 BLOCKED**; technical layer C7/C9/C18/C19 (healthy and with the fault) green, **C14 green** (786 s); 135 min, 4 desktops in parallel × real Firefox 140 and Chrome 154, 3840x2160. ⇒ **nothing that was green broke on the VA-API route**. **ROUND 2 — Radeon = Vulkan** (`--scheda amd`, renderD129 mapped inside as card0/renderD128; route `vulkan` 8/8 at startup: `h264_vulkan`/`hevc_vulkan`, «AMD Radeon RX 6800 (RADV NAVI21)»): ⛔ **STOPPED at the first defect** — 82 healthy PASS, **2 FAIL** (`T-P-C-lxqt-firefox`, `T-012-xfce-firefox`), 4 BLOCKED (`F-018b/c` gnome and kde). **THE DEFECT BELONGS TO PHASE 19**: the SAME test `F-018`/`P-C` (re-attach at a different size, 4K→2560→4K) on the SAME lxqt box with the binary `18746ac2` forced `--codifica vaapi` = **PASS**, and with the phase-18 binary `4b39195c` (VA-API) = **PASS**; only the **Vulkan** route breaks (tool `19-f018-prova.sh`, outcomes E1…E4 in `/media/REMOTIX/misure/fase15/giro19-diagnosi/`). **Cause, with evidence** (`journalctl -k` of the host, logs of the boxes): on the canvas change Vulkan encoding on the RX 6800 goes into **`VK_ERROR_DEVICE_LOST`** (`vkQueueSubmit2`) ⇒ amdgpu **page fault** (gfxhub/mmhub, client TCP then VMC) ⇒ **ring `gfx_0.0.0` and `vcn_enc_0.0` in timeout** ⇒ **GPU MODE1 reset** (*«VRAM is lost»*, `devcoredump` written). Intermittent but reproducible (E3r on lxqt, E4r on xfce; E4 first run clean). ⚠ **The reset wipes the SHARED card**: all the Vulkan sessions of the 4 boxes in parallel lose the device in cascade — the 2 FAIL + 4 BLOCKED and the many «DEVICE_LOST»/«il palco se n'è andato» in the four logs come from a single hang. In the faults **`labwc` and `kwin_wayland`** also appear as processes: the amdgpu/RADV stack destabilises on the reconfiguration of the output together with the encode. **VA-API on the same resize is clean** (0 faults, 0 resets: E1 and E2). ⇒ **The user's decision**: the cure is neither minimal nor obvious (it sits at the border with the RADV/amdgpu driver of this Mesa) — the Radeon round is **NOT green** and **has not been redone**, waiting for the user's choice. **HEVC in Chrome on Vulkan** (`hev1.1.2` against VA-API's `hev1.1.6`): **NOT verified**, the Radeon round was stopped before getting there. **Android**: hand tests by the user with the phone (decision of 1 Oct). Boxes left on **Intel** (card0/renderD128 = UHD 770), binary `18746ac2`, route `vaapi` | no |
| `(questo commit)` | **installer: the card's Vulkan driver from the catalogue** — catalogue **2026.10.01.10** (seq. 10): in the `h264` block of every platform `vulkan_scheda` (vendor → OFFICIAL Vulkan driver that encodes, installed by the engine without consent: Debian and Ubuntu `mesa-vulkan-drivers`, **Arch `vulkan-radeon`**, only for AMD) and `vulkan_nvidia` (the package that carries the ICD with the proprietary driver, **only in the remedy** of RX-GPU-004: it must have the driver's number, which can also come from NVIDIA); openSUSE: Packman's `libvulkan_radeon` together with `Mesa-dri,Mesa-libva` (`pacchetti_scheda` AMD and repository commands). Engine: `H264Piattaforma.VulkanScheda/VulkanNvidia`, `VulkanPerLaScheda`, the **`vulkan`** step of the plan after the package; `schedeVulkan` with the catalogue judges AMD from the platform (Arch without ICD counts; Alma with the `radeon` ICD NO ⇒ RX-GPU-006); RX-GPU-006 rewritten (it/en), `SPECIFICHE.md`, the comment of the `PKGBUILD`. ⛔ Intel never (ANV experimental, stays on VA-API); ⛔ Fedora nothing in Vulkan: the RADV with RPM Fusion's codecs (`mesa-vulkan-drivers-freeworld`) **replaces** the official one (dnf puts it in only with a «swap»: as an addition, it chose the i686), it stays VA-API freeworld | `vulkan-radeon` on Arch is only an optdepends, and a «Recommends» is skipped on machines without recommends; and on the distributions with the «all_free» Mesa the `radeon` ICD made the preliminary say yes when 7a would have said no | `[M]` 1 Oct 2026, podman images `remotix-costruzione-*`: **who carries the ICDs** — Debian 13: `mesa-vulkan-drivers` 25.0.7 (`radeon_icd.json`, `intel_icd.json`), NVIDIA `nvidia-vulkan-icd` 550.163.01 (non-free; for `nvidia-driver-libs` only *Recommends*); Ubuntu 26.04: `mesa-vulkan-drivers` 26.0.8, NVIDIA `libnvidia-gl-<N>` (`nvidia_icd.json`, *Depends* of `nvidia-driver-<N>`, up to 610); Fedora 44: `mesa-vulkan-drivers` 26.2.3, RPM Fusion `mesa-vulkan-drivers-freeworld` 26.2.3 and `xorg-x11-drv-nvidia-libs` 615.71.09 (`nvidia_icd.x86_64.json`); Alma 10: `mesa-vulkan-drivers` 25.2.7 (AppStream), **no** freeworld in RPM Fusion EL; Leap 16: `libvulkan_radeon`/`libvulkan_intel` 24.3.3 (official and Packman), NVIDIA `nvidia-gl-G06/G07` (NVIDIA's repository); Tumbleweed: same 26.2.3, Packman `.pm.`; Arch: `vulkan-radeon`, `vulkan-intel` 26.2.3, `nvidia-utils` 615.71.09 (all *Provides* `vulkan-driver`). **The codecs**: Fedora 44 and Alma 10 build Mesa without `-Dvideo-codecs` ⇒ `all_free` (from the spec and from the source's `meson.options`), openSUSE removes them («re-disable video codecs»); Packman: `zypper install --from packman --allow-vendor-change Mesa-dri Mesa-libva libvulkan_radeon` = 3 updated with the vendor change, nothing removed. `[?]` that Packman's and Leap's 24.3.3 RADV really encodes could not be tested (no card: RADV's «null» device has no video queues). `installatore/costruisci.sh prove` green (gofmt/vet clean), new `TestVulkanDelCatalogo` and `TestPianoVulkan` | no |
| `(questo commit)` | **the bench for the NVIDIA rental** (`banchi/19-nvidia/`, §2.4): `LEGGIMI.md` (one page for the user: what to rent, how to launch, how long it lasts); `19-nvidia.sh` from the laptop — `prepara` (the .debs for Debian 13 and Ubuntu 26.04 with `costruisci-deb.sh`, the installer, the benches: the «suitcase» in `costruzione-uscita/19-nvidia/`), `tutto IP` (sends, starts in a systemd unit that survives ssh, follows, reboots by itself if the driver asks for it, collects into `misure/19-nvidia/` with the sha256), `pulisci IP`, and in pieces `manda/avvia/segui/stato/raccogli/entra`; `UTENTE=ubuntu` with sudo, `CONTENITORE=` for the local test. `19-nv-macchina.sh` on the machine, as root, one step at a time and restartable: **checks** (distribution, card from the bus, `nvidia-smi` ≥ 550, ⛔ cards without NVENC A100/H100/H200, `nvidia-drm modeset`, the DRM nodes and WHICH one is the NVIDIA's — the server encodes on `renderD128` —, the ICD, `vulkaninfo` with `VK_KHR_video_encode_queue/h264/h265`, dmabuf, modifiers; and the snapshot of the machine as it was) · **driver** (only if missing: Debian `nvidia-driver`+`nvidia-vulkan-icd` from non-free, Ubuntu `ubuntu-drivers install` — ⛔ not `--gpgpu`, which has no ICD —; the ICD alone if the driver is «headless»; `modeset=1`; output 10 = reboot) · **dependencies** (XFCE under labwc like the `rete11-xfce` box, the tools, `firefox-esr` — on Ubuntu from Mozilla's repository —, Google's Chrome, the user `rxbanco`) · **remotix** (with the INSTALLER: `verifica`, `piano --installa --pacchetto`, `applica --approva`, `certifica`; if it refuses, the refusal stays as a result and the .deb goes with the package manager; name in the certificate and stderr in a file declared in two files of `/etc` that `pulisci` removes) · **encoding** (`--prova-codifica` h264/hevc, on the NVIDIA node, forced vulkan, and as a user: GREEN only with route `vulkan`) · **comparison** (`19-confronto.sh` with `MOTORI="vulkan scheda"`, `ORDINE_PRODOTTO=1`) · **suite** (`19-nv-suite.py`: F-001 F-002 F-003 F-011 F-013 F-016 F-018, Firefox and Chrome, healthy+fault, the phase-15 tests IDENTICAL, with `Scatola.dentro` = `sudo -n sh -c` on the machine; browsers in their own labwc without a screen, pixman, 3840x2160, or declared headless; log in the format of `15-giro.py`, round `19-nvidia`, report from `15-rapporto.py`) · **collect** · **clean** (installer `disinstalla --purge`, the bench's users, `modeset`, the NEW packages only if apt's simulation touches no package that was there, `/etc/apt` as it was). `19-confronto.sh`: `MOTORI` and the canvas test **in a cycle** (`--ciclo 20:3840x2160,2560x1440`, H.264 and HEVC). `19-nv-prova-contenitore.sh`: the local test without a card | §2.4: the bench ready before the rental, *«senza improvvisare»* | `[M]` 1 Oct 2026, laptop: `bash -n` and `shellcheck -S warning` clean (excluding only the intended warnings), `py_compile`; `prepara` GREEN (the two .debs with the checks R13/R14/R4 YES, installer, suitcase); **test in a container with systemd and without a card, Debian 13 and Ubuntu 26.04**: checks RED (no NVIDIA: correct), dependencies GREEN (Firefox 153.4.0esr, Chrome 154, labwc 0.8.3 / 0.9.3, XFCE 4.20), the installer installs, its verification 7a does not pass (no driver) and **rolls back by itself**, the .deb with the package manager, the server listens and declares *«QUESTO SERVER NON SA CODIFICARE VIDEO»*, `--prova-codifica` code 3, `19-confronto` compiles, suite NOT LOOKED AT (no NVIDIA node), archive brought back with the same sha256, **clean: packages, `/etc/apt`, users and folders exactly as before**. `19-nv-suite.py --interno … --certifica` on f001 and f018: the pure functions pass through the graft. Cured during the test: a blind purge stopped on `sudo` leaving dpkg pending (⇒ simulation first, `SUDO_FORCE_REMOVE`, `dpkg --configure -a`); on Ubuntu `apt-cache show firefox-esr` exits 0 for a name with no candidate (⇒ `apt-cache policy`). ⚠ In the container without `/dev/dri` the installer's preliminary does not give RX-GPU-003 (nodes not read = no refusal) and the refusal comes only from 7a: to be looked at. ⛔ NOT tested without the card: the driver step, the run of `19-confronto`, the suite with the browsers | no |
| `(questo commit)` | **Chrome green on the Radeon: the HEVC coded size aligns to the card's granularity** — `src/vulkanvideo.c`: `larg_cod`/`alt_cod` (the size in the SPS and in the `codedExtent`) are aligned, besides 16, to the card's `encodeInputPictureGranularity` (RX 6800/RADV: **64x16**), and the rest is cut by the conformance window (like radeonsi in VA-API, 1920x1088). Before, at 2544x1344 the SPS said 2544 and the card encoded in blocks of 64. The bench: `banchi/19-vulkan/chrome/` (WebCodecs page with the product's configuration, `hev1.1.6.L153.B0`, in its own labwc). ⚠ The string `hev1.1.2` (Vulkan) against `hev1.1.6` (VA-API) has NOTHING to do with it: it is the Main10 compatibility flag in the SPS, and the page configures `hev1.1.6` anyway | in the F-002/003/… suites on Chrome the canvas stayed **green** (0,136,0) at the browser's canvas **2544x1344** (window 2560x1353): 2544 is not a multiple of 64. At 3840/3776 it did not show (multiples of 64); Firefox green-OK by chance of size/codec | `[M]` 1 Oct 2026 on the server, `19-confronto --motore scheda` on the Radeon, 30 frames: **before** 2544x1344 ⇒ ffmpeg «cu_qp_delta 35 outside the valid range» and image correct only in the first CTB rows, then green; Chrome 154 (VA-API Intel) dominant (0,136,0) on 30/30. **After** (coded 2560x1344): ffmpeg 0 errors and whole image, Chrome 30/30 decoded, not degenerate; 3824x2064 (coded 3840x2064) same; 3840x2160 and 1918x1078 (→1920x1088) 0 errors; H.264 2544x1344 0 errors. VA-API Intel not touched (only `vulkanvideo.c`); `--prova-codifica`: Radeon `strada vulkan` (hevc and h264), Intel `vaapi`. No page fault/timeout in the kernel | `rete11/prodotto/remotix.ad3ba33a` (not installed: `prodotto/remotix` stays `e678cf8b`) |
| `(questo commit)` | **the bench of the Android tests on the real phone (§5, §5.1)** — `banchi/19-android/`: `19-android.sh`/`19-android.py` from the laptop (`controlla` · `prova <1..10>|tutte [--desktop]` · `ripristina` · `a-secco`), `telefono.py` (the suite's `--browser telefono` driver: a tab of OURS via `/json/new`, only towards `https://192.168.0.2:8511-8514/8611-8614`, a call guard before the gestures), `LEGGIMI.md` for the user; new test **`15-f031-tocco.py`** (F-031, `SOLO_TELEFONO`: real finger `adb input swipe`, real tap `adb input tap`, tap-and-a-half with the protocol; scene and judges of F-004). The tests are THOSE of the suite, with their judges and faults, launched ON THE SERVER by `15-giro.py --browser telefono` with `ssh -R` (19333 → the phone's DevTools via `adb forward`, 19334 → the laptop's «counter», the only one that uses adb: call?, ready, tap, scroll, rotate, kill-chrome). Minimal hooks: `suite.py` («telefono» choice), `15-g6-comune.py` (`uccidi_browser` → `am force-stop`; `accendi_a_misura` → phone rotated), `11-c21` (`foto_piena` at `devicePixelRatio`), `15-f014` (clipboard permission for the phone too), `15-giro.py` (`REMOTIX_SISTEMA_15`, `SOLO_TELEFONO`), `15-rapporto.py` («telefono» column), `15-porta.sh` (also carries `19-android`). Its own log: `/media/REMOTIX/misure/fase19-android/registro.jsonl`; benches brought into `/media/REMOTIX/src/controllo-android` (does not touch `controllo`). The phone is left as found: the user's tabs noted and never touched, rotation and `screen_off_timeout` put back, Chrome closed again if it was (state in `~/.cache/remotix-19-android/`). Test 9 cuts the line from the SERVER (the suite's nft), not the Wi-Fi: with the Wi-Fi off adb would be lost | the user's decision of 1 Oct (§5: «il telefono è tuo», Phonestra) and the suite's rule: same tests, same judges | `[M]` 1 Oct 2026 on the laptop, **dry** (phone and server NOT touched): `19-android.sh a-secco` **22/22** — without a phone `controlla` and `prova 1` say «telefono non visto» and exit with 2 (adb only got `devices`); with a FAKE adb and a laptop Chrome 154 (`--headless=new`, throwaway profile) on a local page: its own tab, refusal of an address outside the boxes, snapshot of the canvas via CDP, click/key/finger to the page, trackpad pointer brought onto the target (error < 1 px), call ⇒ 409 and gesture stopped, closing and restoring (the user's tab intact, tabs towards the boxes closed, rotation and screen-off put back). `--certifica` of f031/f001/f018 green. ⚠ NOT tested: the real phone (adb, `input`, rotation, `force-stop`, Chrome Android's DevTools) and the run on the server — they are tested with the first `prova` | no |
| `(questo commit)` | **the «comune» labwc of the LONG tests has its own name** — `banchi/15-suite/15-compositori.sh` also starts «comune» (socket written in `$XDG_RUNTIME_DIR/15-compositori/comune`), `15-giro.py` → `compositore()` reads it for the LONG tests instead of `REMOTIX_WAYLAND_VERI`/«wayland-0». No judge touched | after the server reboot (1 Oct) `15-compositori.sh accendi` had started first and «wayland-0» was **gnome**'s labwc: the F-030 tests of the four desktops ended up there, under the browser of gnome's row, and one stayed covered ⇒ black «DEGENERE» canvas (T-030-xfce in the rounds `19-radeon-ff`/`-3`, T-030-kde in `-3b`). It was not the product: the server was sending the desktop and the page was painting (the box's logs and the page's diary) | `[M]` 1 Oct 2026, server: round `19-radeon-3` (binary `ad3ba33a`, Radeon = Vulkan, 4 desktops × Firefox 153 and Chrome 154, technical layer) **669 PASS, 0 FAIL, 4 BLOCKED** (T-030-xfce, T-029-kde, healthy+fault), kernel clean (0 page faults, 0 resets, 0 fence fallbacks, 0 ring timeouts); alone: F-030 xfce 2/2 PASS, F-029 kde 3/3 PASS; mini-round `19-radeon-3b` (f029+f030, 4 desktops) 14 PASS and T-030-kde BLOCKED — the covering moves; **with the «comune» labwc cured, mini-round `19-radeon-3c` (f029+f030, 4 desktops together, Firefox) 16/16 PASS**; short round `19-intel-3` (f001/f003/f011/f018, Intel = VA-API) **128/128 PASS**. T-029-kde of the round: Plasma did not start 1 boot in 50 (kcminit stuck, ksplash «eglSwapBuffers failed»), screen really black: not the encoding's | no |
| `(questo commit)` | **Android on the real phone: tests 1-10 green (full round GNOME, short KDE/XFCE/LXQt), and the bench's cures** — `11-c21` `foto_piena`: with dpr > 1 the snapshot of the whole glass and the crop (Chrome Android with `clip.scale` > 1 repeats the page in tiles); `telefono.py`: the protocol's finger and the real one consume the slop like the page does (D_TAP 9 px: one sacrificial step, +10 px to the real finger), the real scroll starts from the centre of the canvas, short (≤ 30 %) and waited for up to 3 s; `15-f031` up to 8 finger passes; `telefono.py` admits port 8599 (the non-existent server of F-001's fault); `19-android.py` reads the card from the route in the box's log (in the box's `/sys` renderD128 is always the Intel); `15-f018` compares the canvas with the view × devicePixelRatio (the page: `misura_vista()`) — on the computer dpr 1, outcomes unchanged (`--certifica` green) | §5 and §4-bis: the second gate | `[M]` 2 Oct 2026, S23+ (Android 16, Chrome 154.0.8037.92), boxes on the Radeon (Vulkan, `ad3ba33a`). **Portrait, real screen** (phone in hand): GNOME 1 (4/4), 2 F-031 (healthy and fault PASS: a finger that moves, a tap that clicks, a tap-and-a-half that drags), 3 keyboard, 4 clipboard, 7 phone rotated and put back (F-018 + P-C: canvas 2096x832 for the view 750x297 CSS × dpr 2.8125, and back 1072x1936), 8 Chrome killed and re-entry, 9 network dropping, 10 Esci — all PASS healthy+fault; KDE/XFCE/LXQt 1 and 9 PASS. ⚠ In portrait test 5 (video: the judge's aim outside the crop on the narrow video, 11 % of the frames; the video was full, no mosaic) and test 6 (F-003: the test window on the 1072-wide canvas is maximised by the desktop, and dragged it shrinks) do not pass: they belong to the narrow canvas, not to the product. **Landscape** (Chrome from Phonestra's drawer, virtual screen 2560x1000 — the DeX case, the user's suggestion): 6 PASS on the four desktops, 5 PASS (video 100 % good frames, audio), 1/3/4/8 PASS. ⚠ Open: with the S23+ an `adb input swipe` that starts in the lower half of the canvas during the session does not reach the page (on an empty page it does): to be looked at by hand | no |
| `(questo commit)` | **«Tastiera solo a richiesta» (DECISIONI §10.28)** — `src/pagina.html`: with the phone in hand (touch layout) the hidden paste field carries `inputmode="none"`, `virtualkeyboardpolicy="manual"`, `autocapitalize`/`autocorrect="off"` (removed in the classic one: computer and DeX with mouse identical); the **⌨ command at the top right** (40 px, only with `data-disposizione="tocco"` and the session on; `touchend` in the gesture: `blur`+`focus` with the new `inputmode` and `navigator.virtualKeyboard.show/hide`) opens and closes the keyboard; Android's closing («back») is seen from the `visualViewport` that goes back up tall. ⭐ And the text ARRIVES: `tastiera_su_input` sends the field's DIFFERENCE (letters as `LETTERA`, what disappears as Backspace, `\n` as Enter — autocorrections included), `tastiera_su_keydown` the real keys (Enter/Backspace with the field empty, Bluetooth keyboard without mouse); the field empties outside composition. `incolla_campo_crea()` separated from `incolla_campo_prendi()`; the paste reads are skipped with the keyboard open. `REMOTIX.tocco.tastiera()` to read. Bench: `15-f031` fourth gesture «tastiera» (closed after the gestures · the ⌨ with a REAL tap opens it · «prova» via composition+commit CDP arrives in field «a» of the scene · the ⌨ closes it again; fault: the tap 60 px to the left of the ⌨ ⇒ red; `--certifica` with the judge `giudica_tastiera`); `19-android.py` counter `/tastiera` (`dumpsys input_method`, `mInputShown`) and fake adb; `telefono.py` `tastiera_aperta`/`aspetta_tastiera`/`comando_tastiera`/`tocco_vero_in`/`scrivi_ime`; SPECIFICHE §7.2-7.3 | `[M]` 2 Oct, S23+: the keyboard opened by itself and covered the lower half for 60 % of F-031 (the `adb swipe` in the lower half «did not arrive»: they fell on the keyboard); and it wrote nothing: `[M]` the product's page in Chrome with emulated touch, before the cure, «ciao» from the input method and from the keys ⇒ **zero** messages (in touch mode nobody was listening) | dry (2 Oct): local bench on the product's page in headless Chrome 16/16 (touch: `inputmode=none`, ⌨ visible, a tap on the canvas does not open, the ⌨ opens, «ciao » composed arrives, «cisao»→«ciao» = 3 Backspace + «ao», keys x/Enter/Backspace, the canvas with the keyboard open does not close it, the ⌨ closes it again; classic: no attributes, no ⌨, «ci» goes once, the IME text no — as before); gesture «tastiera» of `15-f031` against the real page with a fake counter 5/5 (healthy PASS, fault FAIL, opened by itself FAIL); `15-f031 --certifica` green; `19-android a-secco` 25/26 (the 4 new ones green; red «il puntatore si porta sul bersaglio» already before: `porta_il_puntatore` not touched). ⛔ I did not use the real phone: the test is the user's | no |
| `(questo commit)` | **The work of 2 October that was only on the server, and the arrow under capture on the DeX (3 October)** — brought back from `/media/REMOTIX/src/f19-audio/albero` (binary `54a98acc`, page `d827a225`, in force in the boxes since 2 Oct): `sessione.c` stops the `pipewire-pulse` left over from the previous session (GNOME mute after «Esci», the user's hand test); `trasporto.c` gives back the streams' credit when a client stream closes (`[M]` after 19 streams the clipboard stopped); `pagina.html` the clipboard (no warning at every access on GNOME/KDE without a user gesture, the Ctrl+V after a remote copy, the second button as a «chorded button»). ⭐ And one new line, page `34fde3d7`: `:not([data-agganciato="si"])` on the rule that hides `#puntatore` in `sistema` mode — `[M]` on the DeX (S23, Android 16, Chrome 154 and Samsung Internet 30) hover does not arrive (noVNC #1727: position only before the click, ids in a row) and the double arrow on the border never appears; with pointer capture the movements with buttons up arrive (>150 in a row) but the arrow had disappeared. With the line, the user: «con la cattura la situazione migliora», resizing from the border seen in the log (hover → pressed → dragged). |
| `63f5562` `67628ff` `(questo commit)` | **On the DeX pointer capture at the first click (DECISIONI §10.29)** — `src/pagina.html`: `cl_hover_manca()` on `pointerdown` of type `mouse` (no pass with buttons up since loading or since the last release, or the last one at `CL_SALTO_PX`=8 px or more from the click ⇒ `cl_aggancia()`; ⛔ the first version counted the passes, <10, and `[M]` round `19-cattura` the bench's Firefox with 5 passes was captured on a computer); `cl_spinta_oltre_il_bordo()` releases after `CL_SPINTA_USCITA`=160 CSS px of push out of the canvas; the first `movementX` after the lock beyond `CL_SALTO_FINTO`=100 px is discarded (`[M]` two releases in the same second as the start). `[M]` 3 Oct, DeX, Radeon then Intel: capture on at the first click on GNOME, KDE, XFCE, LXQt, exit from the border and recapture, no spurious release with the page `1f1cbb73`; the user: «risultato eccellente». |
| `8d30a7c` `a0a3aa5` | **The check on the computers, and what it found** — `[M]` round `19-cattura` (criterion «<10 passaggi»): the bench's Firefox captured with 5 passes ⇒ new criterion (no pass, or the last one at least 8 px from the click). Round `19-cattura-2` (39 PASS, 1 FAIL, 24 BLOCKED): BLOCKED of the bench (the scene's ports left by the interrupted round; C22/F-003 counted only the `mousedown`, which the page since 2 Oct turns off by taking the click from `pointerdown` ⇒ now they count the pointers too) and one real FAIL, Chrome on GNOME selected «beta gamma delt»: **the release too carries its position** (`cl_su_mouseup`). Round `19-cattura-3`, page `f78df3ed`, Intel: **F-003 F-004 F-006, 4 desktops × Firefox/Chrome, 48/48 PASS**; no capture switched on by the bench. |
| `(questo commit)` | **The user's hand test, Linux, Intel (3 Oct, morning)** — the user's words: *«sui 4 DE il resize delle finestre funziona», «la selezione del testo funziona»*. `[M]` diary of the 4 boxes: client `piattaforma=Linux`, **no capture switched on** (the DeX rule does not trigger on the computer). |
| `(questo commit)` | **The user's hand test, Linux, Radeon (3 Oct)** — the user's words: *«resize ok anche sulla radeon»*. Boxes redone with `19-scatole-scheda.sh amd` (it failed before: the copies of the `shm` inside devroot, cured in `3535800`). |
| `(questo commit)` | **Android, test 2 (F-031 touch) RED on the keyboard — and it is NOT the page** — `[M]` 3 Oct, S23 (Android 16, Chrome 154, Samsung keyboard 5.9.30.97, no update since yesterday), Radeon, GNOME: «il secondo tocco sul ⌨ NON chiude la tastiera», then on retrying «aperta da sola» (consequence: it had stayed open). Red with Phonestra, red **without** Phonestra, and red **with yesterday's page `3fc5777d`** which on 1 Oct was green ⇒ the phone changed, not the product. No external keyboard connected. `[?]` Different from yesterday: USB debugging switched on today by the user, Chrome restarted with `am start`, the phone this morning on the DeX. ⭐ **Then the user by hand, phone in portrait: «la tastiera si apre e si chiude»** ⇒ the red belongs to the BENCH. Suspicion to be verified: `telefono.py` `tastiera_aperta()` reads `dumpsys input_method | grep -m1 mInputShown=` — the FIRST line, which today may not be Chrome's (other screens/clients after DeX and Phonestra). Test 3 was not done. adb: one gets in with `ADB_VENDOR_KEYS=~/.config/Phonestra/adbkey` (the phone no longer recognises the key of the tablet's adb). |
| `cd7c59e` | **The full net to close: round `19-chiusura-intel`, Intel, binary `54a98acc`, page `f78df3ed`: 700 PASS, 2 FAIL, 2 BLOCKED (129 min)** — FAIL: F-012B on GNOME (the previous session's `pipewire-pulse`: at «Esci» `pipewire` stops and pulse does not, at the new login `pipewire` restarts before the check) ⇒ `sessione.c` compares the start instants; binary **`05e7c7d1`**: F-012B **20/20 PASS** on the 4 desktops × 2 browsers. BLOCKED: F-030 (black Firefox canvas in the first 45 s) only with the long tests in parallel, each time on a different desktop (LXQt; then KDE and XFCE) ⇒ redone one desktop at a time: **4/4 PASS** ⇒ it is the bench's load (4 Firefox in 4K decoding on the same Intel that encodes), not the product. |

## 4-bis. The closing of the functionality tests

The user's words (1 Oct 2026): *«prima di ritenere chiusi i test di funzionalità voglio verificare di persona che
tutto sia ok»*. ⇒ Three gates, in order: (1) the automatic suite green in both rounds (Intel = VA-API,
Radeon = Vulkan); (2) Android on the user's phone (§5); (3) **the user's hand test** on the boxes
(first the 4 desktops on the **Intel**, then the 4 on the **Radeon** — the user's choice; user `nictest`, ports 8511-8514), with the server stopped. Only after
the third is phase 19 declared closed and the `fase-19` branch goes into `fase-10-cure`.

### 4-bis.1 The hand test on the Intel (2 Oct 2026)

The user's first pass on the 4 desktops: *«funziona quasi tutto bene»*, three reports.
1. **Ctrl+C / Ctrl+V «non sempre»** — two real defects, cured and measured (commits `5443a77`, `18419b7`;
   binary `fbfceb41`, page `1fb65a01`): the server granted **19 unidirectional streams in the whole
   session** (`trasporto.c`, the credit is now given back at closing), and the `Ctrl+V` left before
   the clipboard announcement (the V now waits for the read, at most 400 ms, only on `Ctrl+V`).
   New test `15-f014c` (the clipboard as a person uses it): with the old product **red** (4-5 rounds
   out of 5 with the old text), with the cures **green**; round `cure-intel-6` **128/128**. ⚠ In the terminal
   `Ctrl+V` writes «^V»: it is the terminal (paste with `Ctrl+Maiusc+V`), not a defect.
2. **Hot resizing** — already out of the product since 17 August (`DECISIONI.md` §5.1-bis);
   reconfirmed, the two outdated sentences removed.
3. **Android, Chrome with the mouse: the clicks do not arrive** — the clicks now come from the pointer events (page);
   verified by the user **with the DeX: «i clic funzionano»**. The declared limit of the Samsungs remains
   (no hover ⇒ no shape on the borders, `SPECIFICHE.md` §7.4). ⚠ The first report was made with
   **Phonestra** from the laptop, which injects events into the phone. ⇒ **The user's decision (2 Oct): the user's
   hand test on Android is done with the DeX**, not with Phonestra (which remains the tool of the automatic
   benches, `banchi/19-android`).

✅ **Second pass, same day: «Test incolla ok».** ⇒ **The Intel is closed** (Android excluded:
it is redone on the Radeon with the phone).

### 4-bis.2 The hand test on Android with the DeX (4 Oct 2026)

The user's words: *«Possiamo chiudere il caso DEX»*. Tested successfully (binary `05e7c7d1`, page `f78df3ed`, the closing product, §7):
- audio and video synchronised on a **4K** YouTube video;
- **detach and re-entry** of the session while the video plays;
- the **resizing of the windows** of the applications;
- the **clipboard**.

✅ ⇒ **Android with the DeX is closed**, and with it the third gate of §4-bis.

## 5. Android: the real phone, driven from here

⭐ **1 Oct 2026, the user's words: «ti lancio l'app e il telefono è tuo»** — thanks to **Phonestra** (the user's
project) the user's phone (Samsung S23+, Android 16, Chrome 154) can be reached via wireless adb with the
key already authorised by Phonestra: `[M]` connection successful, Chrome fully drivable with the DevTools
protocol (`adb forward … localabstract:chrome_devtools_remote`), real taps with `adb shell input`. ⇒ The tests
of the table below become **automatic**, on the real phone, at every round. The connection stays on the
laptop and reaches the suite on the server through an ssh tunnel: the phone's key never leaves the laptop.
⛔ Only Chrome towards the boxes; never during a call (`dumpsys telephony.registry`, one line per SIM); the
phone is left as it was found.

*(The table was born as the user's hand sheet; it remains as the list of tests.)*

### 5.1 The tests


*The user's decision (1 Oct 2026): «per android i test funzionali li faccio io». With the user's phone, **Chrome**
(never Firefox Android, `DECISIONI.md` §7.18), on the local network towards the server's boxes (`https://192.168.0.2:8511`
GNOME · `8512` KDE · `8513` XFCE · `8514` LXQt), user `nictest`. Each row is marked **PASS / FAIL / BLOCKED** with
date, desktop, card (Intel or Radeon) and, if FAIL, a sentence on what was seen; it enters the suite's log
with executor «utente».*

**Full round**: GNOME, with the box on the **Radeon** (the new route, Vulkan). **Short round** (rows 1, 2, 6, 9):
KDE, XFCE, LXQt.

| # | test (ref. phase 15) | what to do | what must happen |
|---|---|---|---|
| 1 | F-001, F-002 access and first image | open the address, accept the certificate, enter | form, then the desktop in view within a few seconds, not black nor in pieces |
| 2 | F-031 touch | tap on an icon; tap-and-a-half to drag a window; the little ⌨ button at the top right, a word, ⌨ again | the click arrives where you tap; the window follows the finger; the keyboard does not open by itself, the ⌨ opens it, the word arrives, the ⌨ closes it |
| 3 | F-007, F-009 keyboard | open an editor, write «Prova è à @ €», Enter, delete | the right characters, accents included |
| 4 | F-014, F-015 clipboard | copy a text on the phone and paste it into the editor; and the other way round | the text passes in both directions |
| 5 | F-012, F-013 audio and video | open a video in the remote desktop | continuous image and sound on the phone |
| 6 | F-003 update | open, move and close a window | the screen follows with no leftovers nor visible delays |
| 7 | F-018 re-attach at a different size | rotate the phone (portrait ↔ landscape), then reload the page | the canvas takes the new size (on KDE: it stays and rescales, exception) |
| 8 | F-016, F-017, F-020 detach and re-entry | close Chrome abruptly, reopen it, re-enter | the session is still there, with the editor and the text written |
| 9 | F-019 network | turn off the Wi-Fi for 20 seconds, turn it back on, re-enter | you get back in and the session is there |
| 10 | F-021 Esci | «Esci» from the menu | the session ends, the page goes back to the form |

## 7. ✅ PHASE 19 CLOSED — 3 Oct 2026

Closed on the user's word («Chiudi la fase 19»). State at closing: binary **`05e7c7d1`**, page **`f78df3ed`**,
boxes on the **Intel**. Full net `19-chiusura-intel` 700 PASS + the cures redone green (F-012B 20/20, F-030 4/4
alone); the user's hand test green on Linux (Intel and Radeon: resizing, text selection) and on the DeX
(capture at the first click, DECISIONI §10.29; clipboard).
**Left open, declared:**
- F-031 on the phone in hand: the bench says the ⌨ does not close the keyboard again, the user by hand sees that it does ⇒
  a defect of the BENCH (suspect `grep -m1 mInputShown`); test 3 not done. Touch is the fallback (§5-bis), it does not block.
- F-030 with the long tests in parallel on the Intel alone: black Firefox canvas because of the bench's load.
- Work after the phase: §6 «Lavori da fare dopo la fase 19».

### 7-bis. After the closing — 4 Oct 2026

- ✅ **The user's hand test with the DeX** (§4-bis.2): *«Possiamo chiudere il caso DEX»*.
- ✅ **F-012B on the 4 desktops** with the closing product (`05e7c7d1`/`f78df3ed`), Firefox: rounds `f012b-1` (GNOME,
  LXQt) and `f012b-2` (KDE, XFCE), PASS=8. **Counter-test** on GNOME with the old binary `fbfceb41`: **RED**
  (`f012b-controprova`, FAIL=1); `05e7c7d1` put back, green again (`f012b-ritorno`).
- 🔀 Two histories reunited: since 2 Oct this branch had locally, never pushed, the tests `15-f014c` (the clipboard as
  a person uses it) and `15-f012b` (the audio after «Esci»), which `fase-10-cure` did not have; the product (`src/`) was already
  equal in the two. In the probes of C22 and F-003 the closing version stays (it counts `mouse*` and pointer together).

## 6. Restart from here (2 Oct 2026, evening — session closed by the user)

**State.** Automatic suite GREEN on the two cards (Radeon = Vulkan, round `19-radeon-3` 669 PASS, the bench's 4 BLOCKED
redone 16/16; Intel = VA-API, short round `19-intel-3` 128/128). Android on the real phone green (rows 1-10 on GNOME,
short on the other three; in portrait F-003 and F-013 depend on the narrow canvas, in landscape green). Boxes on the
**Radeon**, binary `ad3ba33a`, page `210ff091`. Last work: **the phone's keyboard only on request**
(DECISIONI §10.28, commits `25f878a`/`5168275`): page `prodotto/pagina.html.3fc5777d` on the server, NOT yet in the boxes.

**First thing of the new session, in order:**
1. from the `fase-19` branch: `bash banchi/15-suite/15-porta.sh`; on the server the new page in the boxes
   (`cp -n prodotto/pagina.html prodotto/pagina.html.210ff091 && cp prodotto/pagina.html.3fc5777d prodotto/pagina.html`,
   then `11-accendi.sh prodotto|server` for the 4 desktops) and the targeted round
   `15-giro.py --giro 19-tastiera --desktop gnome,kde,xfce,lxqt --browser firefox,chrome --prove f007,f009,f014,f031-tocco`;
   ⚠ after a server reboot, first `15-compositori.sh accendi`;
2. Android with the phone (Phonestra open): `bash banchi/19-android/19-android.sh prova 2` and `prova 3`
   (the ⌨, and `[?]` the backspace on an empty field with the Samsung keyboard) — ~20 minutes;
3. **the user's hand test** (§4-bis): first the 4 desktops on the Intel, then the 4 on the Radeon (nictest, 8511-8514);
   on the phone: a finger that starts from the lower half moves the pointer (with the keyboard closed);
4. closing of phase 19 and `fase-19` into `fase-10-cure`.

**The order of the work after phase 19** (the user's decision, 4 Oct 2026):
1. **performance measures** (from zero, with a plan the user approves);
2. **functionality tests on the NVIDIA machine** — ⛔ no performance measures on NVIDIA: the machine is
   rented, time is short. *Claude's proposals, to be confirmed:* (a) in the same rental the installer too,
   or a second rental would be needed; (b) the times the product already writes in the log are kept as an
   observation, never declared as a measure;
3. **trial and full version**;
4. **installer**.
(The boxes' access file, D3, is already done: commits `cb6061e`/`1fc64bb`, 3 Oct.)

⭐ **Restart from here (4 Oct 2026, session closed by the user — usage limit, it resumes Wednesday 7 Oct
afternoon).** Phase 19 closed and pushed (`fase-10-cure` = `fase-19`). First thing: `git fetch`, then the **plan
of the performance measures**, on **both of the server's cards, Intel and Radeon** (the user's answer, 4 Oct: VA-API and Vulkan
are two routes of the product, each with its own numbers). And the two proposals about the NVIDIA (point 2) to be confirmed. Boxes: product `05e7c7d1`/`f78df3ed`
on the 4 desktops, no user session open.
⭐ **4 Oct, evening:** in the boxes the new login page «Satinato» (`2e72f3c`, chosen by the user among the
20 proposals of `grafica/login-premium/`): product `05e7c7d1`/**`cc09a1aa`**, the 4 servers restarted (8511-8514) and
`[M]` served with the new page; the binary has not changed.

**Work to be done after phase 19** (the user's list, 2 Oct 2026):
- boxes: the login file `remotix.pam` updated (D3), in a separate round;
- **trial and full version** (to be defined with the user);
- NVIDIA: the test on the rented machine, with the bench already ready (`banchi/19-nvidia/LEGGIMI.md`);
- performance: the measures to be redone from zero, with a plan the user approves;
- installer: the tests in the containers with the real card, and a VM without a card that must refuse with a clear message.

⭐ **5 Oct 2026 — we start from the NVIDIA** (the user: *«partirei dai test funzionali su nvidia, visto che devo
sborsare un po' di soldi»*; and before the measures, so that the measures stay with the architecture finished). Planned
rental: **LeaderGPU**, 1× RTX 3090, whole machine, 64 GB, Xeon E5-2609 v4, 0.62 €/h, at most 48 hours; automatic
systems Ubuntu 22.04/24.04, on request within one working day (to ask: 26.04 or Debian 13, and the
emergency console). The bench (`8412ad3`): step **«aggiorna»** (Ubuntu 20.04/22.04/24.04 ⇒ 26.04 with
`do-release-upgrade`, one jump and one reboot at a time, up to 10 reboots from the laptop; ⛔ it cannot be undone) and
**spare memory** of 4 GiB below 12 GiB. `[M]` 5 Oct, laptop: `prepara` + empty test Debian 13 with the
product `a8396bc` GREEN as on 1 Oct (cleaning identical to the start); in container ubuntu:24.04 ⇒ 26.04 in
one jump, ubuntu:22.04 ⇒ 24.04 ⇒ 26.04 in two, then «niente da aggiornare». ⚠ A container has no kernel,
nor the renter's network nor drivers: on the real machine the risk of the jump remains (hence the console).

### 7-ter. The real NVIDIA — 5 Oct 2026, LeaderGPU (RTX 4090)

`[M]` Whole machine, 1× RTX 4090, Xeon E5-2630 v4, 128 GB; delivered Ubuntu 24.04, brought by the bench to
**26.04.1** (one jump), driver **595.91.07 open** from Ubuntu's repository, Vulkan ICD, `modeset=Y`, `renderD128`.
- **Installer**: green, certificate 0. **Encoding**: H.264 and HEVC on the **Vulkan** route (`h264_vulkan`,
  `hevc_vulkan`, «NVIDIA GeForce RTX 4090 · NVIDIA 595.91.07»), HEVC `hev1.1.2.L60.B0` like the RADV.
- **Comparison from memory**: 12 out of 12 good, 1080p and 4K, H.264 / HEVC 8 / HEVC 10 (PSNR 38.6–46.2 dB, SSIM
  0.985–0.996). ⛔ **From the card (zero copy): 0 out of 34** — NVIDIA's GBM refuses `LINEAR|RENDERING`
  (`Invalid argument`; it accepts LINEAR without RENDERING, or RENDERING with its own modifier `0x300000000e08014`).
  The product falls back to memory **and declares it**. Possible cure (slabs with the card's modifier and
  Vulkan import with the modifier): **to be decided**.
- ⛔ **PRODUCT DEFECT found and cured** (`129e488`): on the NVIDIA labwc offers in memory only `BG24`
  (3 bytes per pixel); downstream 4 bytes are read ⇒ every frame DISCARDED, black session (F-001 red).
  Cure in `src/wlroots.c`: the 24 bits are widened to 32 (`BG24`→`XB24`, `RG24`→`XR24`), only on that route.
- **Two defects of the BENCH, cured without touching the tests** (`abb7f1a`, `479630e`): Mozilla's Firefox ESR 153
  opens the «Terms of Use» window on top of the scene (rule `SkipTermsOfUse`); and it runs as `firefox-bin`, while
  F-016/F-017 look for `firefox-esr` (name aligned with a link).
- **Suite on XFCE, Firefox 153 and Chrome 154: 43 PASS, 0 FAIL, 1 BLOCKED** (F-013 Firefox: the «ear» has
  collected 106 samples out of 120 — a measure of the bench, not a red). Rounds: 1 (before the cure) F-001 red and 38
  BLOCKED; 2 (with the cure) 15 PASS; 3 (Firefox rule) 30 PASS 9 FAIL; 4 (name aligned) 43 PASS.
- ⭐ **Zero copy on the NVIDIA** (`d62958c`): the GBM refuses the linear slab; the slab is born with one of the
  modifiers that the Vulkan encoder declares it imports (`0x300000000606014`). Comparison from the card
  **28 out of 28** good. The server delivers at 60/s with ~22 ms from capture to bytes (from memory: ~11/s, ~90 ms).

#### 7-ter.1 The XFCE panel that does not stop — 5-6 Oct 2026

`[M]` After the zero copy F-003 on Firefox was red in 4 rounds out of 4 («foto vecchia» of 1-4.7 s), Chrome green.
- **The new witness** (`wlroots.c`, only with `--parlantina`): the damage the compositor DECLARES, every 120
  frames — mean area, whole ones, and the last rectangle. And a `copy_with_damage` probe written for the occasion
  (in memory, outside the product) attached to the live session.
- **The fact**: on a STILL desktop the compositor answers at 60/s, with the damage on a rectangle 49 px
  high at the bottom (or 27 at the top): it is `xfce4-panel` redrawing itself at EVERY frame, alternating the position
  of the bar centred for 1280 (x=487) and for the real canvas. ⇒ 60 4K frames per second for nothing, and a
  slow client falls behind by seconds.
- **It is not the zero copy**: with the package without zero copy and the same witness, the cycle is there all the same (and
  F-003 red); the zero copy only makes it run faster (60/s instead of ~11). The «without zero copy» green
  of the first comparison was a lucky birth.
- **It is the birth race** (the same as pcmanfm-qt on LXQt, phase 14): labwc's output is born 1280x720 and
  the client's size arrives ~200 ms later; if `xfce4-panel` is born in between, it stays in the cycle. `[M]`
  with the panel restarted (`xfce4-panel -r`) the cycle disappears and F-003 goes back to green; with a session ALREADY born
  resized (`wlr-randr`), the cycle is not born. labwc 0.9.3, xfce4-panel 4.20.7, gtk-layer-shell 0.10.0.
- ⭐ **The cure** (`sessione.c`, `primario_misurato()`, formerly `primario_lxqt()`): on XFCE too labwc's primary client
  is an `sh` that gives the size with `wlr-randr` and then does `exec xfce4-session`. The head of the line
  (`labwc -m --session`) is the same macro as `XFCE4_SESSION_COMPOSITOR`: the logout belt does not change.
  ⇒ `wlr-randr` enters the components of XFCE **and of LXQt** in the catalogue (2026.10.05.11: it was missing on all
  platforms except Leap, also for the already existing LXQt cure), and in the rpm `(wlr-randr if xfce4-session)`.
- **Measured**: F-003 green on Firefox and Chrome; with a still screen the server no longer delivers anything.
  **Full XFCE suite with zero copy and cure: 43 PASS, 1 FAIL** (round `remotix-nv-ubuntu2404-20261005-2215`).
- **The logout belt with the new command**: F-021 («Esci») **4/4 PASS**, F-012B (the sound after «Esci»)
  4/4, F-004 (the mouse) 4/4, F-012 (the sound) 4/4 — Firefox 153 and Chrome. ⚠ F-021 on the NVIDIA wants the scenes
  in `/opt/remotix` as on the boxes: the bench puts them there, and `pulisci` removes them if the folder was its own.

#### 7-ter.2 F-013 on Firefox: it stays red — open

- The **image** stopping at times belongs to the CLIENT: the bench's browsers draw in software (labwc pixman,
  llvmpipe; Firefox's `CanvasRenderer` ~65%) on a Xeon E5-2630 v4. Counter-test `CLIENTE_SCHEDA=1` (the
  browsers' compositor on the card, only for the counter-test): the image passes.
- The **sound** does not: audible 23-56% even with the client on the card. The server sends ~50 blocks per second,
  0 lost, without holes; the «ear» inside the page hears the sound in bursts. On this machine Firefox
  had never measured it (before the zero copy: BLOCKED, 104-106 samples out of 120). Firefox here is
  **Mozilla's 153 ESR**; on the Intel benches, where F-013 passes, it is another version. ⏳ To understand whether it is the iron
  or Firefox 153 (it is tested outside this machine).
  `[M]` 6 Oct: **F-012 (the sound WITHOUT video) green on Firefox 153 and Chrome** on the same machine ⇒ Firefox 153
  receives the sound and plays it; it breaks only with the 4K video at 60/s on top. ⇒ The suspicion goes to the client's
  iron (Firefox decodes in software, `RDD` ~45%, on a Xeon from 2016), not to the product. ⚠ It is not closed:
  the test of Firefox 153 + 4K video on a fast client is missing.
- **A defect of the bench**: Ubuntu 26.04 has the coreutils in Rust, and `tail -5` is an error (`tail -n 5`
  works). The tests collected the evidence with `tail -N`: corrected in all the benches.

#### 7-ter.3 GNOME on the NVIDIA — 6 Oct 2026 (the user's choice: the rental time that remains)

`[M]` GNOME 50.1 (`ubuntu-session`, mutter 50.1) installed alongside XFCE (`DESKTOP_NV=gnome`); the product,
having found both, chooses GNOME. ⚠ The installation lasted ~4 hours (not explained).
- ⛔ **PRODUCT DEFECT, BLACK session**: the capture's proposal offered LINEAR and INVALID; Mutter on the
  NVIDIA agreed on INVALID, could not allocate it, withdrew it ⇒ «no more input formats», never a
  frame. And the fallback to memory did not trigger: it looked only at «nessun formato concordato».
  Suite: 4 PASS, 2 FAIL, 38 BLOCKED.
- ⭐ **The cure**, two pieces:
  1. `figlio.c` `modificatori_per_la_strada()` + `cattura_modificatori_scheda()`: if the card REFUSES the linear
     slab (`vulkanvideo_scheda_rifiuta_il_lineare()`, the same question as `wlroots.c`), the proposal also offers
     the modifiers that the Vulkan encoder imports, between LINEAR and INVALID. Where linear succeeds
     (Intel, Radeon) the proposal stays the usual one. `[M]` agreed `0x300000000606014`: zero copy.
  2. `cattura_formato_rifiutato()`: «format agreed but no frame ever arrived» is also a refusal
     — the net underneath, for every card. ⚠ To be re-measured on Intel and Radeon (it was not possible here).
- **GNOME suite with the cure: 41 PASS, 2 FAIL, 1 BLOCKED** (round `remotix-nv-ubuntu2404-20261006-0524`):
  F-013 Firefox (the same as XFCE, §7-ter.2); **F-003 Chrome «chiude»**: with the program closed, the window
  stays in the snapshot for 10.7 s — the server delivers two frames at closing (the last one of 47 KB) and then
  NOTHING: Mutter sends no more damage. Redone 8 times (2 Chrome, then 3 × Firefox and Chrome): all green
  ⇒ **1 out of 9**. ⏳ Intermittent, open: never seen on the Intel; to be looked at if it comes back.

#### 7-ter.4 Closing of the rental — 6 Oct 2026

The user's choice: it closes. `19-nvidia.sh pulisci`: REMOTIX uninstalled by the installer, 649 new
packages removed, `/etc/apt` as it was, no package different from before; suitcase and work folders removed.
What remains: users created by the packages (`colord`, `geoclue`, `pipewire`) and `rxprova` (uid 1003, from a test
round); reboot advised. ⏳ Open: F-013 Firefox (sound with video, §7-ter.2), F-003 «chiude» on GNOME
(1 out of 9, §7-ter.3), the new fallback to be re-measured on Intel and Radeon.

#### 7-ter.5 How many encodings together — 6 Oct 2026 (the user's choice)

`[M]` RTX 4090, driver 595, ffmpeg 8.0 `h264_vulkan` (the same API as the product), 4K60 in steps:
1 → 122 fps; 8 → 8×31; 9 → 9×28; 10 → 10×25; 12 → 12×21; **16 → 12 succeeded, 4 refused**
(`AuthorizeEncoderSession: Failed to authorize this encoder instance`). ⇒ **The driver gives 12 encoding
slots in all**, counted on the WHOLE card (the user's programs that encode too). REMOTIX's cap
is 10 sessions: it fits, with 2 slots of margin. ⚠ The fps here are the generator's (`testsrc2` in
software, on the slow processor): the count that matters is the slots, not the speed.
- **With the 12 slots occupied** a real session gets in («Ammesso») and stays BLACK: `vkCreateVideoSessionKHR`
  returns -10. The log said «VkResult sconosciuto» and «questo codec NON c'è su questa macchina» —
  false. ⇒ `VK_ERROR_TOO_MANY_OBJECTS` has a name, and the line says «la scheda c'è ma ha FINITO i posti».
- **The retry was already there and works**: slots freed after 45 s, the session has the first frame
  ~8 s later (retries at 0.5 → 10 s), F-001 PASS. ⏳ The browser is told nothing in the meantime: to be decided.

#### 7-ter.6 An hour of video — 6 Oct 2026 (the user's choice)

`[M]` GNOME, Chrome, F-013 (4K video with sound) **19 times in a row in 60 minutes: 19/19 PASS**, on the same
server without restarts; every 30 s the card and the parent (`misure/19-nvidia/campioni-sessione-lunga-20261006.txt`):
card memory ~913 MB during the sessions and **back to 1 MB** between one and the next; the parent `remotix`
**19.1 → 19.3 MB** of RSS and 11-12 descriptors from the first to the last sample. ⇒ No leak between one
session and the next. ⚠ What it does NOT say: a single session held for an hour (each one here lasts ~3 min).

#### 7-ter.7 The full net on the Intel with the cures — 6 Oct 2026 (in parallel with the NVIDIA, the user's choice)

`[M]` Home server, the 4 boxes redone (`19-scatole-scheda.sh intel`), binary **`5c186779`** (`02bb7f3`:
the XFCE cure, the proposal with the modifiers, the fallback «no frame ever arrived»), page `ae66b9b4`;
`wlr-randr` also put in the XFCE box (and in `Contenitore.xfce`). Round **`19-nvcure-intel`**, 4 desktops
× Firefox 140 and Chrome 154 + the technical layer: **737 PASS, 0 FAIL, 0 BLOCKED (146 min)**
(`banchi/15-suite/rapporto-giro19-nvcure-intel.{txt,html}`). ⇒ The cures break nothing on the Intel.
And on the **Radeon** (`19-scatole-scheda.sh amd`, same binary, Vulkan encoding): round **`19-nvcure-radeon`**,
**737 PASS, 0 FAIL, 0 BLOCKED (146 min)** (`rapporto-giro19-nvcure-radeon.{txt,html}`).

#### 7-ter.8 F-013 on Firefox 153: closed — it is the client's iron

`[M]` Home server (i5-13500T, ~3.3 times faster than the Xeon E5-2630 v4 on one thread: the same computation in
Python, 1.13 s against 3.72 s), Mozilla's Firefox **153.4.0esr** in a folder of its own
(`/media/REMOTIX/strumenti/firefox-153`, first in the PATH, with the same `SkipTermsOfUse` rule), round
`ff153-intel`: **F-013 PASS on XFCE and on GNOME**, healthy and fault (the version is written by the log). ⇒ The red
of F-013 on the NVIDIA (image and sound) belongs to the slow client, not to Firefox 153 nor to the product.

#### 7-ter.9 KDE on the NVIDIA — 6 Oct 2026 (the user's choice)

`[M]` Ubuntu 26.04's Plasma (`plasma-workspace`, `kwin-wayland`; `gnome-session-bin` removed so that the product
does not choose GNOME), installed in ~1.5 minutes. KWin's capture agrees on `0x300000000606014`: **the cure of the
proposal (§7-ter.3) holds for KWin too**, zero copy. **KDE suite: 41 PASS, 2 FAIL, 1 BLOCKED.**
- F-013 Firefox: the sound, as on XFCE and GNOME — the slow client (§7-ter.8).
- **F-003 Firefox «foto vecchia» (0.8-2.3 s), 4 out of 4 red, even with the client on the card (`CLIENTE_SCHEDA=1`)**:
  KWin delivers ~58 frames/s where Mutter and labwc deliver ~5-7 (same scene), and ~80% arrive
  with the damage DECLARED EMPTY (on the Intel, Debian's KWin: 0 out of 1200). The server holds (≈20 ms from capture
  to bytes); it is the slow client that cannot keep up with 60 4K frames.
- ⛔ **Cure tested and REMOVED**: giving back at once the frames with the damage declared empty. F-003 Firefox green,
  but **F-003 Chrome «chiude» red 4 times out of 5** (the closed window stays on screen): on KWin an empty
  damage sometimes carries a real change. ⇒ Better a slow client lagging than a ghost window.
  It is not in the product.

#### 7-ter.10 LXQt on the NVIDIA — 6 Oct 2026 (the user's choice)

`[M]` Ubuntu 26.04's LXQt under labwc 0.9.3 (Plasma, XFCE and GNOME removed: the product would choose them first),
the size given before `lxqt-session` (`primario_misurato()`, `wlr-randr`). **LXQt suite: 43 PASS, 1 FAIL** —
F-013 Firefox, the sound of the slow client (§7-ter.8). ⇒ **On the NVIDIA the four desktops run**: XFCE 43/44,
GNOME 41/44, KDE 41/44, LXQt 43/44; all the remaining reds belong to the slow client, except F-003 «chiude» on GNOME
(intermittent, 3 out of 23).

#### 7-ter.11 The hunt for F-003 «chiude» on GNOME — 6 Oct 2026 (the user's choice)

Tools (put aside in `git stash` «nvidia-chiude-traccia-e-fence», not in the product): one line for EVERY
Mutter buffer with its fate, and on the card's delivered ones the fraction of CYAN pixels (the test's
window) over 4096 samples of the mapped memory (tiling permutes the pixels, it does not change their count).
`[M]` 10 sessions, 3 red:
- at closing Mutter delivers **two** full-damage frames at ~40 ms: the first WITHOUT the window (cyan
  12-26 out of 4096), the second **with the window again** (153-653 out of 4096; whole window = 678); then for
  ~1 s no buffer, not even cursor-only. **It happens in ALL the sessions**, green and red: the test
  turns red when that second frame has enough cyan to pass the threshold (16%).
- ⛔ **Hypothesis refuted**: «we read before Mutter's GPU has finished». With the wait for the
  DMA-BUF fence (as on the wlroots route): 69 fences waited for, **0 expired**, and the same red. Removed.
- ⏳ Open: is it GNOME 50's closing animation (the second frame being its start) that Mutter stops
  recording while we hold the buffers (the RETENTION)? The next step: the same trace on the Intel
  (Debian's GNOME 48), to see whether the pattern is there too.
- `[M]` **The same trace on the Radeon** (box rete11-gnome, Debian's GNOME 48, binary `baf0ce80` only
  for the test, then `5c186779` put back): F-003 6 times, 6 PASS. At closing **ONE** frame, cyan **0**
  out of 4096, and that's all; and the cursor-only buffers are few (~120 in the whole session, against ~1100 on the
  NVIDIA). ⇒ The second frame «with the window» belongs to GNOME 50 on the NVIDIA, not to our capture
  in itself. ⏳ The test that separates: GNOME 50 with the animations off (if the second frame is the start
  of the closing animation, it disappears).

#### 7-ter.12 The whole suite on GNOME and KDE — 6 Oct 2026 (Ubuntu 26.04: GNOME 50.1, Plasma 6.6.6)

**GNOME** (31 tests, 2 browsers): 129 PASS, 7 FAIL, 40 BLOCKED. The BLOCKED are tests that are not done here
(our server's port, G8 server, tesseract, real phone). FAIL: F-013 Firefox (slow client, already
known) and **F-014C/F-014D/F-015C** (computer clipboard ↔ session) on both browsers: the server
delivers the bytes in both directions (log), on the home server they pass everywhere ⇒ client side of this
machine, ⏳ not closed.

**KDE**, first round: 115 PASS, 18 FAIL, 43 BLOCKED. Two **real defects of the product**, both from
Plasma 6.6 (on the home server there is 6.3, and there everything passed):
- **the clipboard did not open**: KWin 6.6 no longer exposes `zwlr_data_control_manager_v1`, only the
  standard `ext_data_control_manager_v1`. The two are equal on the wire (XMLs compared) ⇒ `appunti_kde.c`
  binds `ext` if `zwlr` is missing and drives it with the same functions (`2f1ad7d`). [M] «appunti agganciati a KWin
  con ext_data_control_manager_v1 v1», F-014 Chrome PASS.
- **the session stayed English** (F-009): KWin 6.6 no longer listens to `org.kde.keyboard reloadConfig`, it watches
  kxkbrc with a `KConfigWatcher` ⇒ `kwin_disposizione()` also sends `org.kde.kconfig.notify
  ConfigChanged` on `/kxkbrc` (group «Layout»). [M] KEYMAP CAMBIATA → «it [Italian]», F-009 PASS=4.
  Plus a net: if the keymap that arrives is not the negotiated one, it is requested again (max 3).
- in passing: `19-nv-suite.py` fell over a line cut in the middle of an emoji (log with
  `backslashreplace`); and the .debs of the same day are sorted by hash (`2f1ad7d` < `22c178e`) ⇒ apt
  sees them as a «downgrade»: on the bench `dpkg -r` first.
⏳ What remains on KDE: F-007/F-008 on Firefox (REPEATED keys: «Enter» ×10, Ctrl+V pasted 3 times — KWin's
autorepeat when the release arrives late from the slow client?), F-003 Firefox (old
snapshot up to 3.4 s), F-026 image. Second whole round with the cures in progress.

#### 7-ter.13 Two more real defects, and the confirmation round — 6/7 Oct 2026

- **the pointer shape never changed on LXQt and XFCE** (F-005, NVIDIA only): labwc on the NVIDIA
  offers the 3x3 probe a wl_shm format of **3 bytes** (stride 9), and the probe demanded 4 ⇒ «non ha un
  buffer». `wlroots.c` also reads RGB888/BGR888 (`sonda_bpp`). [M] F-005 PASS on XFCE and LXQt.
- **after «Esci» processes remained** (F-021, XFCE on Ubuntu 26.04): `localsearch-3` and `agent` (geoclue),
  from the autostart the machine has for GNOME's packages, in the `session-N.scope`. ⇒
  `sessione_sgombera_scope()`: with the session exited (from the menu or from the product) SIGTERM to what remains
  of the user in the scope, 2 s, then SIGKILL. [M] «SIGTERM a 2 processi (localsearch-3 agent)», F-021 PASS.

**Confirmation round** on the NVIDIA with the binary `716e35b` (all the cures), whole suite:
GNOME 129/7, KDE 122/12, LXQt 129/7, XFCE 129/7 (PASS/FAIL; the BLOCKED are the tests that are not done here).
The FAILs that remain are NOT the product's: F-013 Firefox (slow client), F-014C/D/F-015C on all desktops
and both browsers (the client computer's clipboard; the server delivers in both directions), and on KDE Firefox
F-003/F-004/F-007/F-008 (repeated keys, old snapshots: the slow client) and F-026 Chrome (⏳).

**Home server**, same commit (`716e35b`, binary `e2b1afae`, `rete11/prodotto/VERSIONE` written):
round `19-finale-intel` **732 PASS, 0 FAIL, 5 BLOCKED**; `19-finale-amd` **733 PASS, 0 FAIL, 4 BLOCKED**.
The blocked ones repeated: all PASS except **F-030 Firefox** (first frame black 45 s, once per round
on a different desktop; with the binary `5c186779` never seen in 2 rounds) ⇒ ⏳ A/B test old/new in progress.
- ✅ **closed, they are not the product's** (7 Oct morning): **F-026 KDE Chrome** 3 PASS out of 3 repeated alone
  (it was intermittent); **F-007/F-008 KDE Firefox** (repeated keys): in the server's log, for the Firefox
  sessions the release arrives 700–1160 ms after the press **according to the client's own instant** (Chrome:
  ≤150 ms) ⇒ the delay is born in the browser on the slow processor; KWin repeats a key held beyond ~600 ms,
  as it must with a key really held. The product forwards the right times.

#### 7-ter.14 The rental closed — 7 Oct 2026, ~11:00 (the user's decision: *«abbiamo svolto dei test esaurienti»*)

- **GNOME «chiude»**: animations off (system dconf `enable-animations=false`) ⇒ F-003 Firefox **20/20
  PASS**; counter-test with the animations on, same day ⇒ **8/8 PASS** (stopped there). ⇒ The hypothesis
  «GNOME 50's closing animation» is NOT proven: today the red does not appear in either of the two. It stays
  intermittent (3/23 on 6 Oct), cause unknown, and the capture delivers what Mutter gives it.
- **Computer clipboard** (F-014C/D, F-015C): steadily red, all desktops, both browsers; the server
  delivers in both directions and on the home server they pass ⇒ a fault between the browser and the clipboard of the bench's
  compositor on that machine. ⏳ Not demonstrated; it does not touch the product.
- Evidence collected (`misure/19-nvidia/remotix-nv-ubuntu2404-20261007-0851.tar.gz`), removed by hand what
  the animation test had added (`/etc/dconf/profile/user`, `db/local*`, `dconf-cli`), then
  `19-nvidia.sh pulisci`: REMOTIX uninstalled, 1028 new packages removed, `/etc/apt` as it was, suitcase
  removed. ⚠ «riavvio consigliato» (driver/modeset removed): the machine is being returned, it is not needed.
