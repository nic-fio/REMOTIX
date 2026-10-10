---
name: av1-esce-entra-h264
description: "17 Aug 2026, decided by the user: AV1 leaves the product, H.264 comes in — Firefox Android has neither HEVC nor AV1, and here AV1 is the only codec without hardware"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6917bf53-6d6d-42bb-8bd5-f1d628833c28
  modified: 2026-08-17T17:37:11.600Z
---

⛔⛔ **Decided by the user on 17 Aug 2026**: *«la scelta è obbligata: dobbiamo
abbandonare AV1»*, and the chosen replacement is **H.264**.

**The cause, and it is his**: **Firefox for Android supports neither HEVC nor AV1.**
⇒ For that browser the product did not exist, which contradicts the opening
line of the `README` — *«nessun client da installare, basta un browser
moderno»*.

**And the measurement that confirms it** (`vainfo` on the CHUWI, 17 Aug):

| codec | decoding on the tablet | Firefox | encoding on the server |
|---|---|---|---|
| HEVC | ⭐ hardware | ⛔ **no** | ⭐ hardware, 3.16 ms |
| AV1 | ⛔ **no profile** | yes | ⛔ **does not exist**, software only |
| H.264 | ⭐ hardware | yes | ⭐ hardware, **3.11 ms** (the fastest) |
| VP9 | ⭐ hardware | yes | ⭐ hardware, 6.95-7.28 ms |

⇒ AV1 was **the only codec without hardware anywhere** in this setup.

⭐ **And the string is already verified**: `avc1.640032` (High, level 5.0) —
Firefox accepts it and decodes 300 frames out of 300 with zero errors
(`banchi/07-b48`). It does not need to be guessed.

⚠ **Two measured things that will be needed when writing the encoder:**
- the frame that WebCodecs delivers on Firefox is **`BGRX`**, not planar: the
  colour conversion is already done by the decoder;
- the **hardware** H.264 decoder on this machine converts with a
  different scale from `ffmpeg`: **+8 levels on the light areas**, smooth and
  uniform. It is not a block fault, but it is a wrong colour for the user.

**The work that follows from it** (not done yet): `RCP.md` §4.3 and §6.2 (the registry
of codecs, today `1` = HEVC, `2` = AV1), `codificatore.c` (`h264_vaapi` **and** the
NAL reader that recognises the IDR, because §5.2 wants the true key),
`figlio.c` (the third codec in the per-codec structures), `pagina.html`
(`CODEC_RCP`, the preference, and the probe's test stream, which is actually
painted and has to be manufactured).

⭐⭐ **DONE on 20 Aug 2026**: `rcp.h` (`RCP_CODEC_VIDEO_MAX`), `rcp.c`
(`hevc,h264`), `codificatore.c` (`h264_vaapi`, 1.6 ms; Annex-B reader and SPS of
H.264), `figlio.c`, `pagina.html` (**generated** probes, `avc1.6400<liv esa>`).
⛔ And the number **2 stays AV1 forever**: it is not reused.

⚠ **The trap we paid for**: a new number goes into five places and one stays
behind — four per-codec arrays of length `[3]` (an out-of-bounds write that
dirtied the variable next to it) and a **silent** guard in
`wt_video_diffondi()` that threw away every frame. See `LEZIONI.md` §1.17.

⛔⛔⭐ **AND ON 21 AUG 2026 THE PREMISE TURNED OUT TO BE INCOMPLETE — measured on the
real phone.** Firefox 154 on Android 16 is not a browser «without HEVC and without
AV1»: it is a browser **without WebCodecs**. `[M]` The page, in the server's
log: *«WebCodecs NON c'e'»*, and `typeof VideoDecoder === "undefined"`.

⇒ **The switch to H.264 did NOT open Firefox Android**, and no codec will
ever be able to: in `pagina.html` the road to the pixels is ONE — WebCodecs — and there is
**no** occurrence of `MediaSource`. ⚠ The decision on H.264 stays
good for the other reasons in the table above (AV1 without hardware
anywhere), but the reason «so Firefox Android works» **was false**.

⚠ **Chrome for Android has WebCodecs**: there the product has a road. And if one
day Firefox Android were wanted, a second drawing path is needed (MSE with
a `<video>`), which is real work and changes the delay — not a switch.

See [[niente-eccezioni-per-compositore]], [[prestazioni-sul-ferro-modesto]],
[[i-quadrati-sono-della-tela-2d]].
