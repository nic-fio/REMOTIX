---
name: banchi-in-parallelo-isolamento
description: "How to run several REMOTIX benches together without poisoning each other: own port, ban-file and socket for each"
metadata: 
  node_type: memory
  type: project
  originSessionId: cb1700c8-7c41-4750-828a-e216987d359a
  modified: 2026-08-11T13:55:27.696Z
---

Several benches can run **in parallel** against the product only if each one starts
**its own server**: `remotix --porta N --ban-file … --comando-socket …`. Without that,
the ban of §4.4-bis (per address, 12 hours) triggered by one bench puts out of action
all the others, because they all start from the same address.

Assignment used on 11 Aug 2026, five agents together: 7471-75 (B8) · 7481-85 (B13) ·
7491-95 (B10) · 7501-05 (P1/P5) · 7511-15. ⛔ 7447 belongs to the graft and 7448 to the running
product: they are not touched.

And three rules of coexistence that cost less than they could have:
- each agent owns **its own files** and shared files are touched only with `Edit` on
  a unique anchor, never rewriting them whole (a `--put` of the whole log risked
  deleting another agent's line);
- **no agent writes `.md` and nobody does `git`**: documents are written at the end,
  with the code frozen — it is finding R12C, and git with several hands tramples the index;
- certification faults are grafted onto a **copy** of the product tree, or
  for a few minutes the others measure a lying binary.

See [[remotix-convenzioni]] and [[via-libera-permanente]].
