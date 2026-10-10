---
name: i-quadrati-sono-della-tela-2d
description: "The 64x192 blocks were not REMOTIX's: it is the 2D canvas that breaks on its way to the screen. `bitmaprenderer` is clean, and the hunt was closed on 17 Aug 2026"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6917bf53-6d6d-42bb-8bd5-f1d628833c28
  modified: 2026-08-17T18:01:46.539Z
---

⭐⭐⭐ **17 Aug 2026, evening — the hunt is closed, and the blame was NOT ours.**
The user saw rectangular blocks of **64×192** that moved with the
content. They were cleared, one by one and with the measurement alongside:

| suspect | the evidence |
|---|---|
| the capture / Mutter | `scatto-ingresso.bgrx` taken **while the blocks were in view**: clean |
| the encoder, 300 deltas in a chain | the same bytes via `ffmpeg`: **0 superblocks damaged out of 600**, mean 1.68 |
| the shape of the pieces | 300 temporal units, 1 frame each, no hidden ones |
| `VideoDecoder` | `copyTo` against the truth: 0 out of place |
| the canvas **read back** | `getImageData` against the truth: **0 out of 180 000**, worst 2.9 levels |
| **the canvas PAINTED on the screen** | ⛔ **photographed with the mobile phone: the rectangles are there** |

⇒ **The pixels enter the canvas right and break when the canvas goes to the
screen.** No program can read them there: `getImageData` reads the backing store,
not what the compositor has lit.

⛔ **And it is not the browser**: Firefox **and** Chrome do the same. It is not the GPU in
general: `ffplay` and YouTube — which paint into a **`<video>`** — are
**clean**. It is the road of the **2D `<canvas>`**.

⭐⭐ **THE CURE, measured**: paint with **`createImageBitmap()` +
`transferFromImageBitmap()`** on a **`bitmaprenderer`** context, which does not have the
2D backing store. The user's judgment on the same scene: *«NIENTE ARTEFATTI!»*

⭐⭐ **AND IT IS IN THE PRODUCT since 20 Aug 2026** (`src/pagina.html`): a single
conversion instead of two `drawImage`, the store is no longer needed
(`transferFromImageBitmap` sizes the canvas by itself and the content survives
resizing), sequence number + epoch because `createImageBitmap` is
asynchronous, and `?tela=2d` turns on the old road for comparison. `[M]` with the
Marionette witness: `dipinti == consegnati`, `tard 0`, `err 0`, sharp PNG.
⏳ **The user's judgment on the PRODUCT is missing** (so far it was on a bench), and
`[?]` how much `createImageBitmap` costs — the figure to beat is 34.03 ms.

**What it involved, and now it is done:**
- today the frame goes through **two** 2D canvases: `deposito_p.drawImage(f)` and then
  `componi()` → `pennello.drawImage(deposito)`;
- ⭐ the **cursor is not painted on the canvas** — it is a CSS cursor — so the visible
  canvas does not have to composite anything, and `bitmaprenderer` is enough for it;
- ⚠ the only thing lost is **centring/framing** when the window is
  wider than the image: it is done with CSS;
- ⚠ and **the cost must be measured**: `createImageBitmap` is asynchronous, and the delay is
  the number for which phase 3 exists.

The bench that proves it is `banchi/07-b48` (+ `07-b49` for the eye) and it **does not have
a single line of REMOTIX inside**.

⛔⛔⭐ **20 Aug 2026: they were TWO overlapping defects, not one.** The
`bitmaprenderer` cure cleaned up **Chrome** and on **Firefox** the blocks stayed.
The second suspect is its **AV1 decoder**, isolated with three images
of the same instant (`banchi/07-b52`): clean capture · sent stream read back
by `ffmpeg/dav1d` clean over 22 deltas · Chrome clean · **Firefox in blocks**, with
`dipinti == consegnati` and zero errors.

⭐⭐ **The cure is H.264, and it is in the product since 20 Aug**: same scene, 35
delivered = 35 painted, **no blocks**. ⇒ The decision [[av1-esce-entra-h264]],
born for Firefox Android, was also the cure for this.

See [[av1-esce-entra-h264]], [[le-prove-le-eseguo-io]], [[la-prova-la-fa-lutente]].
