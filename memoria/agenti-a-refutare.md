---
name: agenti-a-refutare
description: "Nic explicitly asks for more agents in parallel to speed things up — and the mandate that pays off most: «prova a REFUTARE questa frase», not «verifica»"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4825e50b-60a3-47f4-968c-276b245986d4
  modified: 2026-08-13T08:52:25.210Z
---

On 13 Aug 2026, with phase 2 almost closed, Nic wrote: *«usa agenti multipli per accelerare lo
sviluppo, cerchiamo di chiudere questa fase 2»*. ⇒ **Parallelism with agents is requested, not something to
propose every time** — it counts as a green light on the method, just as [[via-libera-permanente]] counts on the
substance.

**Why:** that round produced the best result of the day, and not because of speed. An
agent sent with an **adversarial** mandate — *«questa frase è falsa: provalo»* — refuted the
line on which I was about to ask for the phase judgment: one of the twelve faults of the meter was **green by
construction** (the bench read a counter `reset` that the product calls `azzerati`, so it
was always zero). An agent sent to *verify* would have read the same line and confirmed it.
⭐ And the same holds the other way round: the agent sent to **fix** **refused the fix that I had
handed it**, with a concrete case — my fix would have produced a false red, worse than the false
green. A mandate that allows refusal is worth more than one that orders.

**How to apply:**
- the mandate is written to **refute**, not to verify: *«parti dall'ipotesi che sia falsa e
  cerca la prova; se non ci riesci, dillo — ma solo dopo averci provato davvero»*;
- always ask **what would be true if the agent were right** — the concrete scenario,
  input and wrong output — or the finding stays an opinion;
- say explicitly that **refusing the mandate is allowed**: *«se la grandezza giusta non è
  quella che ti ho detto, dillo e fermati»*;
- declare the **constraints on shared resources** in every mandate (live ports, files of another
  agent) — see [[banchi-in-parallelo-isolamento]];
- verify the most serious finding **yourself** before believing it: two minutes of `grep` on the code
  confirmed the M8 defect before I acted.

See [[processo-proporzionato-non-cerimonia]] and [[nic-regista-non-programmatore]].
