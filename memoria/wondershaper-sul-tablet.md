---
name: wondershaper-sul-tablet
description: "To throttle the REAL PATH in phase 9 there is wondershaper in ~/.local/bin on Nic's tablet — not just netem on lo"
metadata:
  type: reference
---

`wondershaper` is in **`~/.local/bin` on Nic's tablet**. He pointed it out on 23 Aug 2026,
opening phase 9.

**Why:** the existing network benches throttle with `tc netem` on the test machine's **`lo`**
(`banchi/07-b64-rete.py`, `banchi/07-b65-datagram.py`), and that half has a **declared** limit:
on `lo` the MTU is 65536, so it does not re-measure how many bytes a datagram really carries. Throttling from
the **client** side measures the real path — WiFi, real MTU, real queue.

**How to apply:**
- it serves phase 9 at the **new working point: 20 Mbit/s**, the declared floor
  (`DECISIONI.md` §3.1-bis) — no longer the 2 Mbit/s the plan said;
- the isolation of [[banchi-in-parallelo-isolamento]] applies: a `tc` rule must be removed even if
  the script dies, or it stays on the machine;
- and [[la-prova-la-fa-lutente]] stays: throttling serves to produce the scene, the judgment is his.
