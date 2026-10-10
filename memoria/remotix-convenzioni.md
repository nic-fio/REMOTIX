---
name: remotix-convenzioni
description: "In REMOTIX one writes in Italian, every statement carries a mark, and decisions live in DECISIONI.md only once"
metadata: 
  node_type: memory
  type: project
  originSessionId: f705453b-99bd-4262-9ad0-9967e8c7c1df
  modified: 2026-08-09T06:15:49.110Z
---

Documents, comments and names in the code are **in Italian** (`palco`, `cattura`, `sentinella`,
`appunti`). Every statement carries a mark: `[M]` measured with the date, `[R]` read in the code,
`[S]` read in a specification, `[?]` hypothesised. Decisions live in `DECISIONI.md` **only
once**, marked ✅ (decided by the user), 🔸 (derived by me, correctable without discussion) or ❓
(open); the other documents refer to them instead of copying.

**Why:** the project died once on measurements that did not measure what was believed, and the
code of v1 was lost while the documents survived — they are what made it
possible to start again. Distinguishing «the user said yes» from «I deduced it» is the difference that
`LEZIONI.md` §2.3-quater says not to lose.

**How to apply:**
- before asserting an absence, **certify the tool** on a case where the thing is surely there:
  on 9 Aug a search looked in `src/` and did not find `RecordVirtual` **not even in Mutter**,
  where it is, because the XML files are in `data/dbus-interfaces/`;
- when a measurement contradicts a document, update it **at the same moment**, with date and
  source;
- the entry point is `README.md`, which says in what order to read.

See [[nic-regista-non-programmatore]].
