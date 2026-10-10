# A3 — The Radeon slows down encoding in groups of 5 frames (dossier for the driver's developers)

*⚠ Historical measures, on the machine of the time. With phase 18 (without ffmpeg) those that the change invalidated were removed — encoding without a card and colour conversion with swscale; those of encoding on the card and of the audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision.*

> State: **open, outside REMOTIX's scope** — the user's decision of 29 Sep 2026
> («è fuori dal nostro ambito»; route 2: document and report, do not work around). If the driver
> solves it, the Radeon in 4K will bear more users without touching REMOTIX.
> Context in the phase: `fasi/16-stress-e-capacita.md`, «Anomalia A3». Compact evidence in
> `misure/fase16/` (the levels cited below); raw data in the archive `fase16-grezzi-2026-09-29.tar.zst`.

## 1. In brief (for whoever decides)

REMOTIX compresses every desktop frame in H.264 with the card. On the **AMD Radeon RX 6800**
a frame usually costs **8.5–8.7 ms**; every 12–40 seconds a **group of exactly
5 consecutive frames of ~31 ms each** arrives (≈ 8.7 + 22 ms). On the Intel UHD 770 the same work
never does it (p99 8.7 ms, maximum 10.4). The delay's p95 rises beyond the 50 ms of SPECIFICHE §3.2
and in 4K the Radeon turns out to bear 0–3 users against the 13–15 of 3K. Our own causes were
excluded one by one with measures; the slowdown is **inside the VCN's encoding call**.

## 2. The machine

| what | value |
|---|---|
| card | AMD Radeon RX 6800, PCI `1002:73bf` rev `c3`, subsystem `e437`, VBIOS `113-2437SM2-U16` |
| family | navi21 (RDNA2), VCN 3.0 |
| VCN firmware | `0x0412100e` (from `amdgpu_firmware_info`); SMC 58.91.0 |
| kernel | Linux 7.0 (Debian 13 «trixie»), DRM 3.64 |
| Mesa | 25.0.7-2+deb13u1, radeonsi, LLVM 19.1.7 — `VA Driver version: Mesa Gallium driver 25.0.7-2+deb13u1 for AMD Radeon RX 6800 (radeonsi, navi21, LLVM 19.1.7, DRM 3.64, 7.0)` |
| libva | 2.22.0 (VA-API 1.22) |
| FFmpeg | 7.1.5-0+deb13u1 (libavcodec `h264_vaapi` / `hevc_vaapi`) |
| CPU | Intel i5-13500T (the UHD 770 iGPU is the machine's other card, used for comparison) |
| compositors | GNOME/Mutter 48, KDE/KWin 6 (Plasma), labwc (XFCE, LXQt) — the phenomenon is on all of them |

## 3. What REMOTIX does (the chain, in detail)

1. **Capture**: the compositor's ScreenCast via PipeWire; the frame arrives as an **8-bit BGRx
   DMA-BUF, modifier `0x0` (LINEAR)**, e.g. 3776×2016 stride 15104 (4K minus the borders of the
   browser window). Buffers recycled by the compositor: 4 on KDE, 6 on GNOME.
2. **Import**: the DMA-BUF becomes a VA-API surface (`vaCreateSurfaces` with
   `VASurfaceAttribExternalBuffers`/DRM PRIME), cached per buffer (`src/codificatore.c`,
   `importa_dmabuf`).
3. **Conversion**: VA-API VideoProc RGB→NV12 into a surface of libavcodec's pool
   (`converti_sulla_gpu`). ⚠ On radeonsi 25.0.7 from the 16th frame the VPP **does not convert**: it records
   the RGB source and returns (EFC, `frontends/va/postproc.c` ~486–507), and the conversion is done by the
   **VCN inside the encoding** reading the linear RGB buffer (`picture.c` ~1203–1207).
4. **Encoding**: `h264_vaapi`, entrypoint **`VAEntrypointEncSlice`** (the Radeon does not declare
   `EncSliceLP`), **CQP QP 26**, High profile, level imposed 5.1, **`async_depth=1`**,
   `idr_interval=0`, infinite GOP (IDR only on request), no B-frames (verified: `dts == pts`
   on every packet), `initial_pool_size` 8. One `avcodec_send_frame` + `avcodec_receive_packet`
   per frame, up to 60/s requested, delivered only when the scene changes.
5. Sending over WebTransport; decoding in the browser (outside the measured stretch).

One session = one child process = **its own `VADisplay`, its own VPP context and its own
encoding context** on the same card. With N users there are N VCN contexts in parallel.

## 4. The measures

### 4.1 The shape of the phenomenon
The child's per-frame line (`registro_dettaglio`), e.g. from `a3-misura-kde/livello-01/server.log`:
```
codec 3: 421 byte, delta, caricamento 0 us, codifica 31035 us (invio 31031), barriera 18 us, conversione 41 us
```
- **Bimodal**: median 8.5–8.7 ms; p99 ~31 ms; maximum 32–35 ms. No intermediate value.
- **Always 5 frames in a row** (64 groups out of 64 counted in the campaigns `amd-freq-*`,
  `amd-b-4k-kde`, `amd-b-4k-gnome`; plus one isolated frame of 25.7 ms in all), each
  **30.4–32.1 ms**.
- **It does not depend on size**: 300-byte deltas and 480 KB frames cost the same in the
  group. **No key** inside a group.
- **It counts frames, not time**: a group on GNOME stretches over 1.2 s (2 slow, 1.16 s of
  still scene without frames, then 3 more slow); another over 0.8 s with 200 ms between one and the next.
- **Every 12–40 s**; 11 groups out of 13 begin within 1.5 s of a user action that makes
  the page redraw (click, wheel, key), but not instantly: e.g. click at 13:25:08.78, frames at
  8.5 ms up to the group at 13:25:10.31, on static frames (~303 bytes).
- **Per session**: in `amd-b-4k-kde` (20:41:01.889 and 20:41:06.296 UTC) session u99 does 5 × 31 ms
  while **u1, on the same card and the same VCN, encodes at 8.4–8.9 ms at the same instants**; in
  `amd-freq-auto` the groups of u1 and u99 never coincide.
- **Card almost idle** in the seconds of the groups: graphics engine 2–6 %.
- **All compositors** (GNOME, KDE, XFCE, LXQt) and all sizes; at 3K and below the p95 holds
  because the groups weigh less on the total.

### 4.2 Comparison with the Intel, same machine and same work
`intel-b-4k-kde/livello-01`: 5732 frames, encoding median 8.1 ms, p99 8.7, maximum 10.4 —
no group. (On the Intel the VPP is real: VEBOX, separate conversion ~8.6 ms.)

## 5. The hypotheses excluded, with the measure

| hypothesis | experiment | result |
|---|---|---|
| low card frequency rising slowly | `power_dpm_force_performance_level` = `auto` against `high`, KDE 4K, 1 user, two steps each (`amd-freq-auto`, `amd-freq-alta`) | OURS p95 39.3/38.6 ms (auto) against 37.5/42.0 ms (high): **equal** |
| VPP on the shaders queued behind the desktop redraw | reading of Mesa 25.0.7 + resources per engine | the VPP does not run on the shaders (EFC); graphics engine 2–6 %; **and the groups are per session**: any global contention excluded |
| implicit wait for the compositor's write on the DMA-BUF | **experiment 1** (binary `3e510160`, branch `a3-esperimenti`): `DMA_BUF_IOCTL_EXPORT_SYNC_FILE` (`DMA_BUF_SYNC_READ`) + `poll` before the import, measured separately; encoding split into send/receive | fence **0.37 ms** on the normal ones, **0.02 ms** on the slow ones; the 22 ms are **all inside `avcodec_send_frame`** (receive 0.0 ms); 100 and 105 slow per step (`a3-misura-kde`) |
| the VCN reading the linear RGB buffer (EFC) | **experiment 2** (binary `39e3ed86`): double conversion on the first frame ⇒ by the rule of `postproc.c` Mesa turns off the EFC for good; every frame goes through a real NV12 | real conversion 0.75 ms median; **identical groups**: 95 and 106 slow per step, p99 31.1–31.3 ms (`a3-senza-efc-kde`) |
| recycling of the compositor's buffers, capture cadence | counts of the buffers and of the producer | 4 buffers on KDE, 6 on GNOME, the group is always 5; the producer is not late (frames queue up during the group and are drained at 31 ms) |
| keys, size, content | per-frame lines | no key in the groups; 300 B and 480 KB cost the same |
| a defect of Mesa 25.0.7 already corrected later | **step 1, 29 Sep 2026**: in the KDE box Mesa **26.1.6** (`trixie-backports`, `26.1.6-1~bpo13+1`: `mesa-va-drivers`, `mesa-libgallium`, `libgl1-mesa-dri`, `libegl-mesa0`, `libglx-mesa0`, `libgbm1`), `vainfo` confirms «Mesa Gallium driver 26.1.6»; product binary `4fb3287d`, same scene as 6.1, two steps of 6 min (`a3-mesa26-kde`) | **100 and 102 slow** per step (out of 5209 and 5168 encodings), all between 30.4 and 39.0 ms, median 31.0 ms; bursts: 18 of 5, one of 4, 3, 2, 1 ⇒ **identical to 25.0.7**: newer Mesa does not cure |

⇒ **What remains**: with `async_depth=1` `avcodec_send_frame` includes the submission to the VCN and the wait for the
result; the extra time is in there, for one encoding context at a time, for 5 frames.
It is not a defect already closed in Mesa: with 26.1.6 (September 2026) the phenomenon is identical, so
it must be reported on the current version too. Candidates not yet tested: **internal state of the VCN context / firmware** (5 = a number of slots?
a window of the frequency control per instance?), **position of the surface** (linear buffer
of ~30 MB migrated between GTT and VRAM), **non-tiled surfaces**.

## 6. How to reproduce it

### 6.1 With REMOTIX (guaranteed reproduction)
On the test server, KDE box with the Radeon alone (`REMOTIX_SCHEDA=amd`), one user with the browser
in 4K browsing (profile A of `banchi/16-stress/16-lavori.py`):
```
python3 banchi/16-stress/16-salita.py --scatola kde --misura 4k --campagna a3-riproduci \
    --gradini 1 --minuti 6 --minuti-ultimo 6 --scheda amd \
    --video /media/REMOTIX/misure/fase16/video/bbb_sunflower_2160p_30fps_x4.mp4 --fps-video 30
```
then in the level's `server.log`: `grep "] codec [0-9]*: [0-9]* byte"` and count the encodings
> 20 ms (expected ~100 in 6 minutes, in groups of 5). With the binary of the `a3-esperimenti` branch the line
also carries send, fence and conversion.

### 6.2 Minimal reproduction, without REMOTIX (⏳ to be written — the first step for the driver)
A C program of ~200 lines: `vaCreateSurfaces` from a linear BGRx 3776×2016 DMA-BUF (or an
RGB32 surface filled by hand), `vaProcess` to NV12, `VAEntrypointEncSlice` H.264 CQP
26 encoding one frame at a time with `vaSyncSurface` on the coded buffer, 60/s for 5 minutes, changing a
small region at every frame; record the time of each `vaEndPicture`+sync. Variants:
one context against two in parallel; linear surface against tiled; `async_depth` 1 against 2.
If it reproduces there, the report to Mesa becomes independent of REMOTIX.

## 7. The evidence
- `misure/fase16/a3-misura-kde/`, `a3-senza-efc-kde/`, `a3-mesa26-kde/`, `amd-freq-auto/`, `amd-freq-alta/`,
  `amd-b-4k-kde/`, `amd-b-4k-gnome/`, `intel-b-4k-kde/` — judgements and diaries (in the repository);
- the per-frame lines (`server.log` of every level) in the raw archive;
- the code of the experiments: branch `a3-esperimenti`, commit `18b6437`;
- the analysis of Mesa 25.0.7: `postproc.c` 470–510 (the EFC rule), `picture.c` ~1203–1207.

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
