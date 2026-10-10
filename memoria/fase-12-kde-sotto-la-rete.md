---
name: fase-12-kde-sotto-la-rete
description: "Nic's directive for phase 12 (18 Sep 2026) — KDE in small increments, full net after each one, checkpoints as gates, Fable 5 on blockers, status every 30 min"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7ed6518e-06c6-45b1-a053-d2827ab2eb17
  modified: 2026-09-18T15:25:28.685Z
---

Binding directive from Nic, 18 Sep 2026, opening phase 12 (KDE): *«Voglio arrivare a KDE
funzionante senza dover mai dire "prima funzionava, ma questa modifica era necessaria"»*.

**Why:** the net of phase 11 must be used as a permanent guardian, not as a final acceptance test.

**How to apply:**
- cycle for every increment: CP0 baseline (full net `--famiglia tutto`, 4 boxes, same
  binary) → CP1 definition (OBJECTIVE/INVARIANT/MODULES/KDE TEST/CLIENT TEST/GNOME
  REGRESSIONS/CRITERION) → CP2 measured observation GNOME vs KDE → CP3 minimal change → implementation
  → CP4 KDE test → real clients (Chrome and Firefox Linux, Chrome on the Android emulator) → full
  net → GNOME unchanged + faults still caught → checkpoint (commit) → next increment;
- red on GNOME = regression until proven otherwise; classes A/B/C/D, D never a shortcut;
- serious/blocking problem ⇒ agent with the **fable** model with a structured request (PROBLEM,
  CONTEXT, EXPECTED, OBSERVED, EVIDENCE, LAST GOOD CONFIG, CONSTRAINTS, ATTEMPTS, QUESTION); its
  answer must then be measured and certified;
- agents in parallel on independent work, with a written perimeter; integration and
  certification stay mine;
- silence: one update every ~30 min in the format STATUS/OBJECTIVE/WORK/TEST/REGRESSIONS/
  BLOCKS/NEXT; interrupt only for checkpoint, regression, block, Fable, decision.

See [[parlato-al-minimo]], [[agenti-a-refutare]], [[niente-eccezioni-per-compositore]].
