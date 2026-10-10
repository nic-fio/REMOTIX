---
name: remotix-prove-sul-banco-non-sull-utente
description: "REMOTIX — the user is not the bench: tests are done by the bench, hunts have a declared ceiling, and the choice «cure or postpone» is put forward at once"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4bbea89f-379f-45d3-8703-bf57c8fe4e7c
  modified: 2026-08-07T13:53:48.773Z
---

In REMOTIX the user **must not be used as a test bench**. It applies to long investigations:
every hypothesis that asks «connect and tell me» costs him an intervention, and a hunt done
this way burns his day even when the diagnosis is correct.

**Why:** on 7 Aug 2026 the hunt for the alternation defect (phase 9, zero-copy)
consumed half of the user's day — «mi sembra che stiamo perdendo tempo», «il
progetto è arenato» — while the usable cure (`REMOTIX_DMABUF=0`) was known after
an hour. The rest was recovering an optimisation: 6 ms of CPU per frame instead
of 18, on a twenty-thread machine. And the correction written in the dark, validated on a
bench that did not show the defect, made it worse for him.

**How to apply:**

1. **as soon as the cure exists, apply it and declare it**: «it works, the rest is
   optimisation» — and put the choice «continue or postpone» in front of the user
   at once, not after five rounds;
2. **put a ceiling** on a hunt, declared at the start;
3. **tests are done by the bench.** If the bench does not reproduce, nothing is shipped to
   be tried out: first the bench, then the correction (rule written in `PIANO.md` phase 9 and
   in `REFERENCE.md` R29);
4. **the meter is what one sees.** The user judges the software working (§7 of
   `SPECIFICA.md`): a performance number that nobody perceives does not justify
   his time.

**⛔ AND TWO MORE RULES, paid for on the afternoon of 7 Aug 2026, which cost phase 10:**

5. **a change to what one SEES, validated only on the bench, is not shipped to the working server.**
   The switch to VBR had PSNR, SSIM and a still frame looked at by eye; it did not have
   the user's judgment on the real desktop. The judgment, which came afterwards: *«siamo tornati indietro»*,
   then *«sono proprio deluso del progetto, è un fallimento»*. What changes the image stays behind
   a switched-off switch until he has looked at it;
6. **at the start of every session, compare the STATE OF THE MACHINE with what the documents
   declare.** `/etc/default/remotix` had been read at eleven and the line that kept
   zero-copy off was no longer there — lost when the file had been rewritten to change the port, and that
   file lives in RAM. Nobody noticed, and the user found a known defect in his face. From
   here the general rule, now in `REFERENCE.md` R29: *the protection against a known defect is not entrusted
   to a configuration line that can be lost* — it lives in the code.

See [[remotix-requisito-prestazione]].

See [[remotix-metodo-documentazione]] and [[remotix-fase9-ripresa]].
