---
name: niente-eccezioni-per-compositore
description: "A function that cannot be done on all supported desktops leaves the product, instead of staying behind a switch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 15e28402-67da-47fb-bd4c-3dda47c97a40
  modified: 2026-08-17T05:29:49.571Z
---

If a function can be done on one compositor and not on another, Nic removes it instead of
keeping it behind a switch or a conditional branch. His words, 17 Aug 2026, deciding
on the live resizing of the canvas: *«non voglio mettere delle eccezioni nel progetto.
Il dynamic resolution esce dalle funzionalità di Remotix»* — and it held even for a function
already written, measured (6 ms on Mutter) and green on the bench.

**Why:** a product that does different things depending on who hosts it costs two branches, two benches
and an explanation to the user for each — and the poor branch stays alive for years, because
stable distributions do not update their desktops. In the same spirit he had already stopped
multi-monitor («non è previsto dal progetto. Sei andato fuori strada»).

**How to apply:** before proposing or writing a function that touches the compositor, say
at once on which of the supported desktops it can be done and on which not — that, not the cost in
milliseconds, is the datum that decides. If the answer is «on one yes and on another no», the proposal
to bring him is to remove it, not to hide it behind a switched-off switch. ⚠ Do not confuse the
case with the one that stays legitimate: something done **before the session exists** (the canvas
taken from the window size at attach) is not an exception, because every compositor
knows how to do it in its own way. The exception is changing live. See [[processo-proporzionato-non-cerimonia]]
and [[nic-regista-non-programmatore]].
