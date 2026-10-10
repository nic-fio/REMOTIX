---
name: la-prova-la-fa-lutente
description: "An empty desktop is the worst possible witness — the tests that close a phase are done by Nic, with real work inside"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6c6f9648-d9f9-4e2a-9127-2557b8767681
  modified: 2026-08-16T18:02:58.631Z
---

⭐ **On 16 Aug 2026 phase 5 was closed by a test of Nic's, not one of mine.**
All of mine had an **empty desktop** — and an empty desktop, just reborn, is
identical to how it was: it is the worst possible witness for the question «did the
session survive?». I had noticed only by looking at the **PIDs**.

His: he logs in maximised, launches an infinite loop in the terminal, closes the
browser, shrinks the window, comes back in — and the loop was still running.
⇒ In a single gesture: I4, the reattach at a different size, and the scene on which the phase
is judged.

**And the things only he can test must be asked of him**, not worked around:
the refusal of the second device (`0x0F`) he closed with the **real phone**;
the tab frozen in the background he closed by leaving it there eleven minutes —
my measurement did not count, because Chrome **does not freeze a tab under
automation** (counter in the page: 542 beats out of 544).

**Why:** the defects that count come out when the product is *used*. In one
afternoon his three reports found the login form left
under the desktop and the return to the form tied to 2 reasons out of 15 — things that
no bench looked at.

**How to apply:**
- ⛔ **never restart the server while he is measuring**: I did it twice
  after saying I would ask, and each time I broke his test halfway;
- before one of his tests, **confirm the state from the log** (for example
  «occupati adesso: 1») instead of having him try in vain;
- when he points at a symptom, **read the code** — not his screenshot: two
  times out of three I removed the wrong thing by looking at the image.

See [[testimone-sul-desktop-vero]], [[processo-proporzionato-non-cerimonia]],
[[nic-regista-non-programmatore]].
