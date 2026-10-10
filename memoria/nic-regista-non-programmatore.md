---
name: nic-regista-non-programmatore
description: "Nic directs REMOTIX but is not a programmer — he decides on explanations in plain Italian, one question at a time"
metadata: 
  node_type: memory
  type: user
  originSessionId: f705453b-99bd-4262-9ad0-9967e8c7c1df
  modified: 2026-08-09T16:43:31.575Z
---

Nic is the director of the project: he sets the requirements, judges what he sees and makes the decisions.
**He is not a programmer** — the handoff of his other project, Nic-OS, states it too
(`~/Documenti/NIC-DE/HANDOFF.md`): *«Nic = regista: visione, gusto, prova e approva. Non è
programmatore.»*

**Why:** a dense technical explanation does not put him in a position to decide; a concrete
explanation does. On 8 Aug the question about the Android keyboard was asked in jargon («libei accetta
keycode, non caratteri») and the answer was *«non riesco a capire il problema»*. Rephrased
with the typewriter and its little hammers, he understood at once and isolated the difficult case by himself
(reattach from a keyboard with a different layout).

**How to apply:**
- **one question at a time** — he asked for it explicitly on 9 Aug;
- explain with concrete objects before the mechanism, and give a recommendation instead of a
  list of options;
- he brings real technical contributions when he understands the problem — the clause on the screen lock
  timeout and the pointer drawn by the client are his;
- he rejects unjustified complications («qui non stiamo costruendo un sistema basato su
  standard militari»): if a defence costs the user friction, it must be defended or removed;
- ⛔ **the easiest way to lose him is to relay the agents' results to him as they arrive.**
  On the evening of 9 Aug, after four investigations and two reviews reported with their tables and their
  marks, he said *«su questi ultimi punti non ci ho capito niente. Che devo fare?»*. Of a
  technical finding he needs three things and none of them is the finding: **what changes for the user**,
  **whether a decision of his is needed**, and **what he must do now** — often «nothing».

- ⛔ **a decision is presented as the SCENE he lives, not as the rule to set.** On the
  evening of 10 Aug I proposed a choice to him talking about *«chi chiude e chi riattacca»* and he
  answered *«il tuo modo di spiegare non mi fa capire niente. Cosa succede quando l'utente sceglie
  logout o chiude la scheda?»* — that is, the right question, which I had not asked. ⭐ His question
  also showed that the case I was talking about **was not that one**: describing the scene would have
  shown at once that the user's case was already decided and working;
- ⛔ **the argument «some day someone else» does not hold**: *«siamo noi che stiamo sviluppando il
  server, mica qualcun altro»*, and he is right — we write both page and server. ⭐ The argument that
  holds is **what actually broke between two pieces of ours**: on 10 Aug, three times in one
  day (the client that read a format the server had changed, a hook rewritten
  three hours earlier, a moved signal). Writing both sides does not protect: **it is exactly what
  makes the disagreement silent**;
- ⚠ and when a doubt changes nothing visible for whoever uses the program, **it is not his**: it is
  taken as 🔸 and his time is given back to him. See [[via-libera-permanente]].

See [[remotix-convenzioni]].
