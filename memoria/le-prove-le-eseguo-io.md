---
name: le-prove-le-eseguo-io
description: "«Se non mi dai il tempo di fare le prove non si va da nessuna parte; altrimenti falle tu» — I drive the browser benches with Marionette, I do not have him open them"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6917bf53-6d6d-42bb-8bd5-f1d628833c28
  modified: 2026-08-17T17:36:50.026Z
---

⛔ **17 Aug 2026, and the sentence is his**: *«se non mi dai il tempo di fare le
prove non si va da nessuna parte»* — *«altrimenti falle tu»* — *«tanto hai il
controllo del tablet»*.

This is what had happened: I had asked him to open the same bench six times with
six different switches, **and meanwhile I was changing the page underneath**. His measurements
described versions that no longer existed.

**Why:** a bench round costs me thirty seconds and him an interruption; and
a page that changes between one of his openings and the next produces numbers that cannot
be compared — that is, it makes him work for nothing.

**How to apply:**
- ⭐ a bench that runs in the browser **I drive it**: `banchi/07-b48-testimone.py`
  starts a real Firefox with the Marionette protocol, does all the rounds and reads
  `window.RISULTATO` — no coordinates, no eyes;
- ⛔ do **not** ask him to open more than ONE address at a time, and do not touch
  the page until he has answered;
- ⚠ `--visibile` opens a window on his screen: warn him **before**, not
  after;
- what stays his is the **judgment** — «gli artefatti ci sono», «l'audio fa
  schifo» — which no bench can give: see [[la-prova-la-fa-lutente]].

⛔⛔ **And on 20 Aug 2026 he said it louder**: *«non voglio fare più test:
hai il controllo del PC, sistema tutto e fai le prove su chrome e firefox»* —
after I had made him reload the page three times for defects that a
bench would have found by itself in two minutes.

⭐ **The tool that came out of it**: `banchi/07-b51-due-browser.py` — Firefox with
Marionette **and** Chrome with the diagnostics protocol (CDP), four checks per
browser, and the input verified **from the server's log** (where the
click arrived), not from the page. ⛔ To be used **before** calling him to look.

⚠ **And the rule underneath**: *a single engine is not a test, it is half a test*. The
cure of `DECISIONI.md` §5.4 was measured on Firefox and on Chrome it broke
image **and** input.

See [[via-libera-permanente]], [[nic-regista-non-programmatore]].
