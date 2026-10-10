---
name: dex-mouse-aperto
description: "The mouse on DeX: the real symptom is «it moves only with the button pressed», it is noVNC #1727 and it is not ours — and the cure is «two canvases 1:1»"
metadata:
  node_type: memory
  type: project
  originSessionId: 9394ca2b-2373-463b-909d-b459cf512df0
  modified: 2026-08-15T05:47:38.706Z
---

⭐ **The real symptom became known only on the evening of 14 Aug 2026**, in the
user's words: *«per attivare il puntatore del desktop devo premere il tasto
sinistro; se muovo il mouse il puntatore del server non si muove, se lo muovo
col tasto premuto allora si muove»*.

⇒ It is **noVNC #1727** — *«Moving hardware mouse without drag ignored on Chrome
Android»*, open since 2022, specific to **Samsung**, reproduced by KasmVNC
#222, Kasm #20 and ⭐ **moonlight-android #573, which is a NATIVE app**. ⛔ **It is not
ours and it cannot be cured**: on that device movements with buttons up do not
reach the page.

⛔ **The four cures of the evening are all off target** and were
corrected anyway because they were real defects: `CURSORE_FORMA` received and thrown away,
the three pointer modes, **84 % of movements sent twice** (both
`mousemove` and `pointermove` were registered), and the click that did not carry
its own position. None of them changed the symptom.

⭐⭐ **The real cure was designed by the user**: *«abbiamo due tele, quella del
server e quella del client — bisogna solo convertire le coordinate»*, and then
*«se i compositori sanno dare la misura esatta, non servono nemmeno le
conversioni»*. ⇒ `DECISIONI.md` **§5.0-sexies**, and the defect becomes
**harmless** instead of cured: every event carries its own position, so
**pointing and clicking hit right even without hover**. Only the
preview is lost (buttons that do not light up, no tooltips).

⛔ **Two `[?]` are DEAD, do not fish them out again**: `cursor: none` does **not** remove the
movements on Android (it was `pointermove` that was missing, and in Android
`dispatchPointerEvent()` comes before `maybeUpdatePointerIcon()`); and pointer
capture **makes it worse** (`movementX` is reconstructed by Chromium).

**Why:** for two days **a judgment** was cured — *«è inutilizzabile»* —
instead of **a symptom**. The question that solved everything was *«che cosa vedi
esattamente succedere?»*, and it was not asked. ⚠ And the contradiction that
contained it had been in the log for hours: 213 movements recorded by the server while
the user saw zero.

**How to apply:** read `fasi/rapporti/F4-IN-6-punto-fermo.md` (the fixed
point) and `F4-IN-7-due-tele.md` (the design in bytes).

✅ **And the cure WAS WRITTEN on the night of 15 Aug 2026**: the chain
`figli_ritela()` → `cattura_ridimensiona()` is there, and `[M]` the server's canvas
takes the size of the window (1264×800), the drawing scale is **1.000**
(`pixelated`) and GNOME *Settings → Displays* **inside the remote session**
declares «Resolution 1264 × 800». ⇒ Pointing and clicking hit, and the text is
no longer interpolated. The report is `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.

⚠ **Chrome's defect stays what it was**: hover does not arrive, so
no preview (buttons that do not light up, no tooltips). What
changed is that **it is no longer a correctness problem**.

✅ **And DeX judged it on 15 Aug 2026**: *«sia su Linux sia su Android
(DeX) è tutto perfetto»*. ⇒ The `[?]` of the half pixel (the `margin: 0 auto` when
`clientWidth × devicePixelRatio` is odd) **does not show up** — ⚠ but nobody
measured it: if one day the terminal text came back frayed on an
odd width, that is the first thing to look at.

See also [[agenti-a-refutare]] and [[utente-prova-si-conserva]].
