---
name: parlare-come-al-regista
description: "«Non sto capendo nulla, stai usando un linguaggio incomprensibile» — reports to Nic go in simple Italian, the details stay in the documents"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 84687524-93d6-4003-8cd1-1ed07aa63454
  modified: 2026-08-22T08:46:05.618Z
---

⛔ **22 Aug 2026, in his words**: *«Io non sto capendo nulla di quello
che dici, stai usando un linguaggio incomprensibile.»*

I was writing him reports dense with internal jargon — bench names
(`06-b37`), section numbers (§1.20), trade metaphors («il gemello
dimenticato», «la spirale delle chiavi», «gli annunci»), and sentences built for
another programmer.

**Why:** [[nic-regista-non-programmatore]] already said it, but it applies
specifically to **progress reports**, which are the thing he reads most.
A report that cannot be understood is not a report: it is noise that costs him time
and forces him to ask.

**How to apply:**
- ⭐ **in messages to him**: simple Italian, short sentences, no file
  names, no section numbers, no trade metaphors. *«Il controllo
  che verifica la pagina non provava mai a rompere niente»* instead of *«06-b37
  non ha guasti innestati»*;
- ⭐ **the technical detail goes in the documents**, where it serves whoever works on them — and
  there the project's jargon is right and must be kept;
- ⛔ **what is NOT simplified**: the measured numbers, the prices to pay, and
  what stays open. Simplifying the language does not mean removing the uncomfortable
  things;
- ⚠ and when asking him for a decision: **one question at a time**, described
  by what he would see happen, not by how it is made inside. The first
  attempt of 22 Aug was rejected with *«non ho capito che devo
  decidere»*, and it was a question written in terms of code.

⛔⛔ **And on 25 Aug 2026 he had to tell me again, with phase 11 just opened**:
*«usa un linguaggio naturale in questa sessione, io non sono un ingegnere»* —
after I had written him tables full of project jargon in a
**conversation**, not in a document.

⇒ ⭐⭐ **The rule holds also when DISCUSSING, not only in progress
reports.** And «simple Italian» must be taken literally: no acronyms, no
component names, no section numbers **in the message**. If something cannot
be said in normal Italian, we have not understood it well ourselves either.
⚠ The proof that it works: when he is spoken to this way, **he asks questions that move the
project** — on 25 Aug he asked *«e usare un contenitore anziché la VM?»* and
*«il buco riguarda solo GNOME o anche gli altri?»*, and both changed
the design of the phase.

⭐ **And his vocabulary wins over mine**: when he corrects a term —
«si chiama **re-scaling**» — that becomes the name, in reports and in
documents.

See [[nic-regista-non-programmatore]], [[remotix-convenzioni]].
