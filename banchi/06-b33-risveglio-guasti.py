#!/usr/bin/env python3
"""06-b33-risveglio-guasti.py — ⛔ THE INJECTED FAULTS of the §7.1 bench.

    python3 06-b33-risveglio-guasti.py --elenco
    python3 06-b33-risveglio-guasti.py --albero /media/REMOTIX/src/06-i-src \\
        --guasto RG1

⛔ It injects into a COPY of the tree, never into the original: the caller saves
   the healthy files BEFORE and puts them back AFTER
   (`06-b33-risveglio-certifica.sh`).

===========================================================================
⛔ WHY THIS FILE EXISTS, AND WHY `06-b33-guasti.py` WAS NOT ENOUGH
===========================================================================

`06-b33-guasti.py` injects faults into `input.c` and judges them with the
**resize** scene.  ⛔ Since 21 August 2026 that scene is no longer enough, and
for a reason that must be written down so that nobody rediscovers it:

  ⭐ The cure at `figlio.c:3964` releases everything **before**
    `cattura_ridimensiona()`.  ⇒ In that scene, with the HEALTHY product,
    nothing is pressed any more at the moment of the replacement:
    `segna_orfani()` **is not called at all**, and fault G3 — which removes
    it — does not change a thing.
    `[M]` Certification of 21 August: G3 injected lights up **zero** cases.

⇒ The scene in which orphans are really born is the one of **this** bench: a
  button held down during a `cattura_risveglia()`, which the cure at `:3964`
  does not cover (§7.1).  ⭐ The positive control of G3 lives here, and it is
  `RG2`.

===========================================================================
⛔ THE FAULTS, AND THE CASE EACH ONE MUST CHANGE
===========================================================================

⚠ And here the question is not "which case turns RED", but **which verdicts
  CHANGE** compared with the healthy round.  The reason is that the
  expectations of this bench have three colours: removing cure "C" the cases
  T3 and T4 do not turn red, they go back to `DIFETTO_VIVO` — which is the
  right colour for a measured defect, and a comparison that looked only at
  red would not see them.

  RG1  "cure C does not kick in"              ⇒ T3 and T4 go back to DIFETTO_VIVO
  RG2  "the orphans of the BUTTONS are not marked"  ⇒ T1 T3 T4 T7
       ⭐ it is the former G3, which in `06-b33` can no longer be certified
  RG3  ⛔ MEASURED NON-FAULT: "the reattach does not close the old descriptor"
       ⇒ **no case changes**, and the discovery is worth more than the fault
  RG4  ⛔ SECOND MEASURED NON-FAULT: "the detach is not sent to libei"
       ⇒ **no case changes** — and together with RG3 it tells the true thing
  RG5  "neither detach nor close: the old context stays alive"
       ⇒ T3 T4 T5 T7.  ⭐ it is the fault that closes the question

===========================================================================
⛔⛔ AND ONE OF MY EXPLANATIONS WAS REFUTED BY THE MEASUREMENT — 21 August 2026
===========================================================================

I had written, and the coordinator had taken it as a specification, that *"the
cure cannot live in `input.c`, because as long as the descriptor set aside by
`mutter.c` stays open the socket is still connected and Mutter sees no
detach"*.  ⛔ **RG3 refutes it**: with the `close()` removed, the healing works
all the same and **no case changes**.

⛔⛔ AND MY SECOND EXPLANATION WAS REFUTED IN TURN.  I had said:
     *"then it is `ei_disconnect()` that sends the detach as a protocol
     message"*, and I had written RG4 to prove it.  ⛔ `[M]` **RG4 does not
     change anything either.**

⇒ ⭐ **The two paths are REDUNDANT, and each one is enough on its own**:
     · `ei_disconnect()` sends the protocol detach;
     · `ei_unref()` + the `close()` in `mutter.c` close the last descriptor
       of the socket, and Mutter sees the EOF.
   ⇒ Removing ONE of them the healing holds (RG3, RG4).  `RG5` removes
     **both** and is the only fault that breaks it.

⚠ The lesson, and it is worth more than the mechanics: **two consecutive
  hypotheses, both plausible, both refuted by the injected fault.**  Neither of
  the two would have been discovered by rereading the code — and the first was
  already written in `mutter.h` as if it were a fact (`CODER.md` §4.6: `[R]` is
  not `[M]`).

⭐ `mutter_eis_riattacca()` remains necessary anyway, and this was NOT
  refuted: after the detach the descriptor set aside is dead, and a NEW one
  can be asked for only by whoever has the bus and the session path.
"""
import argparse
import os
import sys

# (file, description, cases that must CHANGE, search, replace)
GUASTI = {
    # ⛔ RG1 — cure "C" exists but is never called.  It is the positive
    #    control of the cure itself: if removing it the bench stays green, the
    #    green was not the cure's.
    "RG1": (
        "src/input.c",
        "cure \"C\" does not kick in: `guarisci()` is never called",
        "T3 T4",
        """	if (in->guarigione_dovuta && !in->caduto)
		guarisci(in);""",
        """	/* fault RG1 injected: cure "C" does not kick in */
	(void) guarisci;""",
    ),
    # ⛔ RG2 — the former G3, moved into the scene where orphans are really born.
    #    ⚠ It touches ONLY the buttons: in the scene the Ctrl is held down too,
    #      and the call for the KEYS stays — so the healing kicks in anyway and
    #      T3/T4 do NOT change.  ⭐ It is intended: this way the fault is
    #      surgical and lights up a single case, and the equality comparison
    #      demands it.
    "RG2": (
        "src/input.c",
        "the orphans of the BUTTONS are not marked: the log goes back to saying \"done\"",
        # ⛔ THE EXPECTATION WAS CORRECTED BY THE MEASUREMENT, not the verdict —
        #    21 Aug 2026.  I had declared "only T1", reasoning that the Ctrl held
        #    down would have triggered the KEYS' `segna_orfani()` and therefore
        #    the healing.  ⛔ False, and it is `[M]`: at the viewport change the
        #    keyboard **is not replaced** (`remove_viewport_devices` looks only
        #    at TOUCH and POINTER_ABSOLUTE), so `dispositivo_tolto()` is never
        #    called for it and its orphans are never marked.  ⇒ In this scene
        #    the healing flag depends **only on the buttons**.
        "T1 T3 T4 T7",
        """		segna_orfani(in, in->bottoni, in->bottoni_orfani, MAX_BOTTONE, in->quanti_bottoni,
		             "buttons");""",
        """		/* fault RG2 injected: the orphans of the buttons are not marked */""",
    ),
    # ⛔⛔ RG3 — THE MEASURED NON-FAULT, and the discovery is worth more than the fault.
    #
    #      I had declared it "the most precious of the three", with this reason:
    #      *"`input_apri()` does a `dup` of the descriptor that `mutter.c` keeps
    #      aside, and as long as THAT one stays open the socket is still
    #      connected ⇒ Mutter sees no detach"*.  And I had written next to it:
    #      *"if this fault changed nothing, it would mean that the close is not
    #      needed"*.
    #
    # ⛔ `[M]` 21 August 2026: **nothing changes**.  ⇒ My explanation was
    #    wrong, and the line above is the only reason I know it.
    #
    # ⭐ The detach is sent by `ei_disconnect()` as a protocol message, and
    #   Mutter runs `meta_eis_client_disconnect()` without waiting for the EOF
    #   of the socket.  RG4 proves it.
    #
    # ⚠ The fault STAYS in the list with the expectation "none", like G1 in
    #   `06-b33-guasti.py`: a measured non-fault is information, and removing
    #   it would make someone rediscover the same wrong hypothesis in a month.
    "RG3": (
        "src/mutter.c",
        "MEASURED NON-FAULT: the reattach does not close the old descriptor",
        "",
        """	if (sessione->eis >= 0)
	{
		close(sessione->eis);""",
        """	if (sessione->eis >= 0)
	{
		/* fault RG3 injected: it is NOT closed */""",
    ),
    # ⛔⛔ RG4 — THE SECOND MEASURED NON-FAULT.
    #
    #      Born because RG3 had refuted the first explanation, and we needed to
    #      know which one was right.  I had declared "T3 T4", convinced that
    #      the detach was the protocol message of `ei_disconnect()`.
    #      ⛔ `[M]` 21 August 2026: **nothing changes with it either**.
    #
    # ⇒ ⭐ The two paths are REDUNDANT: `ei_disconnect()` sends the detach, and
    #     `ei_unref()` + the `close()` in `mutter.c` make Mutter see the EOF
    #     of the socket.  Each one is enough on its own — and it is `RG5` that
    #     proves it, removing both.
    "RG4": (
        "src/input.c",
        "SECOND MEASURED NON-FAULT: the detach is not sent to libei",
        "",
        """	ei_disconnect(in->ei);
	ei_unref(in->ei);""",
        """	/* fault RG4 injected: no detach, it just lets go */
	ei_unref(in->ei);""",
    ),
    # ⛔⛔ RG5 — THE FAULT THAT CLOSES THE QUESTION.  It removes **both**
    #      paths: no protocol detach AND no closing of the context (so the
    #      `libei` `dup` stays open, and the socket does not die even when
    #      `mutter.c` closes its own).
    #
    # ⇒ If this did NOT break the healing, it would mean that the seat gets
    #   unstuck for a third reason we have not understood yet — and then cure
    #   "C" would be a green whose cause we do not know.
    #
    # ⚠ The old context is abandoned (a leak of memory and of a descriptor): it
    #   is a fault, not a proposal.
    "RG5": (
        "src/input.c",
        "neither detach nor close: the old context stays alive and connected",
        # ⛔ THE EXPECTATION WAS CORRECTED BY THE MEASUREMENT — I had declared
        #    "T3 T4", and **T5** changes too (the release of the Ctrl).  ⚠ The
        #    reason holds and is worth writing down, because it tells RG5 from
        #    RG2:
        #      · in RG2 the healing does NOT kick in, so the keyboard is never
        #        replaced (it is not a viewport device) and its release arrives
        #        ⇒ T5 stays green;
        #      · in RG5 the healing KICKS IN — a new context is born with a new
        #        keyboard — ⛔ but the old channel does not die, so
        #        `drop_device()` does not run: the Ctrl stays down on the old
        #        device and the release on the new one is swallowed by
        #        `handle_key`.
        #    ⭐ It is the same shape as the button, on the keyboard: the first
        #      time this project sees it really happen.
        "T3 T4 T5 T7",
        """	ei_disconnect(in->ei);
	ei_unref(in->ei);
	in->ei = NULL;""",
        """	/* fault RG5 injected: the old context stays ALIVE and connected */
	in->ei = NULL;""",
    ),
}


def main():
    p = argparse.ArgumentParser(description="06-b33 §7.1 — the injected faults")
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--albero", default="")
    p.add_argument("--guasto", default="")
    a = p.parse_args()

    if a.elenco:
        for nome, (f, desc, casi, _c, _s) in GUASTI.items():
            print("%s  %s  [%s]" % (nome, desc, f))
            print("    ⇒ must CHANGE: %s" % (casi or "none"))
        return 0

    if not a.albero or not a.guasto:
        print("⛔ --albero and --guasto are needed (or --elenco)", file=sys.stderr)
        return 2
    if a.guasto not in GUASTI:
        print("⛔ unknown fault: %s" % a.guasto, file=sys.stderr)
        return 2

    rel, _desc, _casi, cerca, sost = GUASTI[a.guasto]
    percorso = os.path.join(a.albero, rel)
    with open(percorso, encoding="utf-8") as f:
        testo = f.read()

    # ⛔ IT IS COUNTED, and a single occurrence is a requirement: an anchor that
    #    appears twice would inject two faults, and nobody knows about one of them.
    quante = testo.count(cerca)
    if quante != 1:
        print("⛔ the anchor of %s appears %d times in %s (ONE is needed): the fault is NOT "
              "injected, and this is NOT \"the fault does nothing\""
              % (a.guasto, quante, rel), file=sys.stderr)
        return 3

    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo.replace(cerca, sost, 1))
    print("⭐ %s injected into %s" % (a.guasto, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
