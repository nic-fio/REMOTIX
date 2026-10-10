---
name: prestazioni-sul-ferro-modesto
description: "REMOTIX's performance is ALWAYS declared together with the hardware: it is obtained on an integrated Intel UHD 730, not on a powerful card"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 884e8876-d549-42f8-9eaf-845107fbde4b
  modified: 2026-08-16T20:50:45.841Z
---

On 16 Aug 2026, after the judgment *«il test su Windows lo dichiaro superato al 100 %»*, Nic
added: **«ricordiamoci sempre che otteniamo performance eccellenti su una Intel integrata»**.

⇒ **A performance number of this project is never reported alone**: it is reported with the
hardware it was taken on — `[M]` **Intel UHD 730** (`i915`, `0000:00:02.0`, `renderD128`), which is
a modest integrated GPU. The Radeon RX 6800 of the same machine is **excluded on purpose** with a udev
rule (`DECISIONI.md` §4.6-ter and §4.6-quinquies).

**Why:** they are two things in one, and both are his.
1. **It is the method he set** on 15 Aug 2026: *«i test vanno fatti sulla GPU integrata,
   altrimenti "trucchiamo" il gioco. La solidità del sistema la si vede su GPU poco potenti, non
   mostri come la RX 6800»* — and that rule was born because a measurement of Aquarium at 60 fps had
   been taken **on the wrong card**, by accident.
2. **It is the result**, and without the hardware alongside you cannot tell how much it is worth: *«funziona tutto e con
   performance eccellenti»* on an office integrated GPU says about the product what the same number
   on a gaming card would not say at all.

**How to apply:**
- when reporting a number — fps, ms, delay, frames — name **the card**, not only the
  machine: «on integrated Intel UHD 730», never just «on the test machine»;
- ⛔ if a measurement comes from different hardware (the Radeon, a laptop, a phone), **declare it
  on that line**: a measurement on better hardware does not say whether the product holds up, it says how
  fast that hardware is;
- it also holds towards the outside: it is the sentence that qualifies the product, and it must be kept at the top of any
  performance summary.

⏳ And the question that phase 8 inherits remains: hardware encoding chooses its card by itself
(VA-API). If the compositor draws on the integrated GPU and the encoder looked for the discrete one — closed —
the fallback is on the CPU, and it must be **declared** instead of suffered.

See [[remotix-convenzioni]], [[la-prova-la-fa-lutente]] and [[utente-prova-si-conserva]].

⛔⛔ **18 Sep 2026, restated by the user: «niente RADEON. Si rimane inchiodati sulla Intel
Integrata».** Said when it came out that the exclusion held only on the host: into the boxes
of the net went the whole `--device /dev/dri`, and the tenants also ended up in the
Radeon's group. ⇒ Now **only** the Intel's `card0` and `renderD128` go into the boxes (found by
PCI address), `gpu-udev.sh` also closes the Radeon's `card` node, and `provisiona.sh` no longer
puts anyone in the `remotix-nogpu` group. ⚠ Any new road to the card must be
checked against this rule **inside** the environment where it runs, not only on the host.
