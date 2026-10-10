---
name: taratura-non-caccia-al-difetto
description: "When Nic reports a small thing, he also says how small it is — and expects the register of the answer to follow it: tuning, not a defect hunt"
metadata:
  type: feedback
---

On 22 Aug 2026 Nic described the only remark he had left — a window dragged fast
is *«leggermente meno fluido»* than local. I answered with an arithmetic ceiling, the ~16 ms
unexplained promoted to *«meta' del tuo problema»* and a fault-hunting list. He corrected the
register, not the facts: **«bada bene: e' questione di micro-secondi, non di secondi, ecco perche'
parlavo di ottimizzazione e non di debug»**.

**Why:** he was not disputing the measurements — he was saying that the product **is not broken**, and that
a big defect found inside a symptom he calls small is almost always a sign that I have
mistaken a design ceiling for a fault. Treating tuning as an emergency makes him
lose trust in the rest of my measurements, and inflates the work of a phase he had
sized well.

**How to apply:**
- when he says **«ottimizzazione»**, the work is moving a number that already works; when he says
  **«non funziona»**, it is a defect. They are two registers, and he chooses the word on purpose;
- the size he reports is a **datum**: if my measurements say much bigger, it is a
  disagreement to declare in one line — with the number — not to resolve by raising the tone;
- and the rule of [[la-prova-la-fa-lutente]] stays: the measurement of the case **he** describes (the
  dragged window) comes before any figure derived from scenes of another kind.

See [[processo-proporzionato-non-cerimonia]] and [[parlare-come-al-regista]].
