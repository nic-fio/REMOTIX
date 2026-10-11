#!/usr/bin/env python3
"""06-b33-risveglio-giudice.py — ⛔ THE VERDICT OF §7.1, and the sender does not give it.

    python3 06-b33-risveglio-giudice.py --seen .../visto.jsonl \\
        --injector .../06-b33-risveglio.log --since 12 --mode held \\
        --label s2-tenuto --canvas 1264x800 --outcomes .../esiti.jsonl

⚠ Runs ON THE SERVER, outside the container, as root (the two files are root's).
  No dependency beyond the standard library.

===========================================================================
⛔ WHAT IT JUDGES, AND FROM WHICH SIDE
===========================================================================

Two sources, and **they do not weigh the same**:

  · `--seen`      what a REAL Wayland window inside the session has
                   received.  ⭐ It is the measurement (`CODER.md` §3.8);
  · `--injector`  what the sending program **says** it did.
                   ⛔ It is NOT proof that the desktop received anything: it
                   is read for two things only — the `ricambi_puntatore`
                   count, which is a window on the internal state of
                   `input.c` and not a log line, and the presence of the lines
                   that DECLARE a fallback, where the question is precisely
                   "is the line there?".

===========================================================================
⛔ THE EXPECTED DEFECT IS NOT A GREEN, AND THE EXPECTED GREEN IS NOT A RED
===========================================================================

In `tenuto` mode there are cases whose **right outcome with today's world** is
`DIFETTO_VIVO`: the release after the replacement does not arrive, and neither
does the fresh click.  ⇒ `DIFETTO_VIVO` is declared and not `OK` — a bench
that called a measured defect "green" is what `CODER.md` §4.6 forbids — and
not `NO` either, which would mean "the bench found something it did not
expect".

⭐ The day the cure is there, those cases must become `OK`.  And if they do
not, the cure is not the one we believed.
"""
import argparse
import json
import re
import sys

GREEN, RED, YELLOW, BLUE, GRAY = ("\033[1;32m", "\033[1;31m", "\033[1;33m",
                                     "\033[1;34m", "\033[0m")
BTN_LEFT, KEY_ENTER, KEY_CTRL = 272, 28, 29

# ---------------------------------------------------------------------------
# ⛔⛔⛔ THE PRODUCT LINES THE JUDGE SEARCHES FOR — and **a line written with
#       `%s` IS NOT ONE LINE, it is N lines**.
#
# *Finding of the adversarial review of 22 August 2026, and it was MY
# regression: the old bench (`06-b33-giudice.py:86-88`) had the distinction,
# and writing this new bench I lost it.*
#
# `src/input.c` `mark_orphans()` has **a single** format string —
# `"%u %s were PRESSED on the device the compositor has just removed"` —
# with `%s` = `"buttons"` **or** `"keys"`.  ⇒ Searching for the common part
# means not telling the pointer from the keyboard.
#
# ⛔ The concrete case that would have passed in green: the release of the
#    BUTTON does not arrive and its path stays silent — that is, the defect T7
#    exists to catch — but a keymap change produced the KEYBOARD line ⇒ T7
#    green.  And in `free_slot` mode, L4 red against `input.c` for a legitimate
#    keyboard line.
#
# ⇒ Every marker carries the **variable** part inside itself, and lives in one
#   place only with its writer next to it.  ⚠ And the space before
#   "buttons"/"keys" is there on purpose: it is the `%u %s`, and it anchors the
#   marker to the whole word.
#
# ⚠ The same holds for `"DOES NOT LEAVE: it was pressed on a…"`, which without
#   what follows matches both *"on a DEVICE"* (the pointer) and *"on a
#   KEYBOARD"*.
# ---------------------------------------------------------------------------
M_ORPHAN_BUTTONS = " buttons were PRESSED on the device the compositor has just removed"
M_ORPHAN_KEYS = " keys were PRESSED on the device the compositor has just removed"
M_BUTTON_NOT_LEAVING = "DOES NOT LEAVE: it was pressed on a device"
M_KEY_NOT_LEAVING = "DOES NOT LEAVE: it was pressed on a keyboard"
# cure "C", `src/input.c` `heal()` — ⚠ long form: "HEALING" alone would
# also show up in a comment or in a future line of another module
M_HEALING = "HEALING (n."
M_HEALED = "EIS channel REDONE"


def read_seen(fpath, da):
    """The witness lines with `n` > `da`.  ⛔ And the number is kept: it is the
    denominator, and without it "zero events" and "I did not look" are the same."""
    report = []
    try:
        f = open(fpath, encoding="utf-8", errors="replace")
    except OSError:
        return report
    with f:
        for line in f:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("n", 0) > da:
                report.append(d)
    return report


def button_code(lines, pressed, after=-1):
    for i, d in enumerate(lines[after + 1:], start=after + 1):
        if (d.get("type") == "BUTTON" and d.get("button") == BTN_LEFT
                and d.get("pressed") == pressed):
            return i
    return -1


def keystroke(lines, code, pressed, after=-1):
    for i, d in enumerate(lines[after + 1:], start=after + 1):
        if (d.get("type") == "KEY" and d.get("code") == code
                and d.get("pressed") == pressed):
            return i
    return -1


def main():
    p = argparse.ArgumentParser(description="06-b33 §7.1 — the verdict")
    p.add_argument("--seen", required=True)
    p.add_argument("--injector", required=True)
    p.add_argument("--since", type=int, default=0)
    p.add_argument("--mode", choices=["instrument", "free", "held"],
                   default="tenuto")
    p.add_argument("--label", default="round")
    p.add_argument("--scene", default="(not declared)")
    p.add_argument("--canvas", default="1264x800")
    p.add_argument("--outcomes", default="")
    a = p.parse_args()

    lines = read_seen(a.seen, a.since)
    try:
        with open(a.injector, encoding="utf-8", errors="replace") as f:
            ini = f.read()
    except OSError:
        ini = ""

    # ⛔ The wake-ups and their deltas, READ from the injector's lines: the count
    #    comes from `input_count()`, which is the internal state of `input.c`,
    #    not a deduction from a log.
    wakeups = [(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                for m in re.finditer(
                    r"WAKE-UP n\.(\d+) outcome=(-?\d+) ricambi_puntatore \d+ → \d+ "
                    r"\(delta (-?\d+)\)", ini)]
    resize = [(int(m.group(1)), int(m.group(2)))
             for m in re.finditer(
                 r"RESIZED to \S+ outcome=(-?\d+) ricambi_puntatore \d+ → \d+ "
                 r"\(delta (-?\d+)\)", ini)]

    cases = []

    def test_case(name, outcome, detail):
        cases.append({"case": name, "outcome": outcome, "detail": detail})

    # ---- C0: has the instrument seen anything? ----------------------------
    # ⛔ A judge that said "no BOTTONE" on an empty file would accusations the
    #    product of something it did not do (`CODER.md` §3.10).
    #
    # ⛔⛔ AND THE INSTRUMENT IS NOT THE SAME IN ALL SCENES — bench defect found
    #      on 21 August 2026, at the second round.  In the `free_slot` scene
    #      **nothing is injected to the witness**: the measurement is the count
    #      of replacements, which comes from `input_count()`.  ⇒ Demanding
    #      witness lines in there was a red that accused the bench of itself,
    #      and that would have hidden the real measurement.
    if a.mode == "free":
        if not ini.strip():
            test_case("C0 the instrument has spoken", "NO",
                 "⛔ THE BENCH: the injector's log is EMPTY")
            return show(a, cases)
        test_case("C0 the instrument has spoken", "OK",
             f"{len(ini.splitlines())} lines from the injector — ⚠ and in this "
             f"scene the witness is NOT the instrument: nothing is injected "
             f"that should reach it")
    else:
        if not lines:
            test_case("C0 the instrument has seen something", "NO",
                 f"ZERO witness lines after n={a.since}: ⛔ THE BENCH, NOT THE "
                 f"PRODUCT — the witness was not open, or did not have the focus")
            return show(a, cases)
        test_case("C0 the instrument has seen something", "OK",
             f"{len(lines)} lines after n={a.since}")

    if a.mode == "instrument":
        # ⭐ THE ZERO CHECK: a click with no replacement in between.  If this
        #   is not green, every red of the other scenes accuses the bench.
        g = button_code(lines, 1)
        s = button_code(lines, 0, g) if g >= 0 else -1
        test_case("S0 the click arrives when there is NO replacement",
             "OK" if g >= 0 and s >= 0 else "NO",
             f"BTN_LEFT down {'yes' if g >= 0 else 'NO'}, up {'yes' if s >= 0 else 'NO'}"
             + ("" if g >= 0 and s >= 0 else
                " — ⛔ THE BENCH: without this green no other red means anything"))
        test_case("S0-bis and NO wake-up was requested",
             "OK" if not wakeups else "NO",
             f"wake-ups in the injector's log: {len(wakeups)} (expected 0)")
        return show(a, cases)

    if a.mode == "free":
        # ---- THE THESIS OF §7.1, taken in order to refute it --------------
        deltas = [d for (_n, _e, d) in wakeups]
        test_case("L1 the three wake-ups went off",
             "OK" if len(wakeups) == 3 and all(e for (_n, e, _d) in wakeups) else "NO",
             f"wake-ups={len(wakeups)} outcomes={[e for (_n, e, _d) in wakeups]} "
             f"(expected 3, all outcome=1)")
        test_case("L2 ⭐ EVERY wake-up recreates the devices — §7.1",
             "OK" if deltas and all(d >= 1 for d in deltas) else "NO",
             f"delta of ricambi_puntatore per wake-up: {deltas} (expected [1,1,1] "
             f"or more).  ⛔ If they were zeros, §7.1 IS FALSE and must be corrected: "
             f"`[R]` `meta-screen-cast-virtual-stream-src.c:283` calls "
             f"`meta_eis_viewport_notify_changed()` at every `..._src_enable()`")
        test_case("L3 and NOBODY touched the canvas",
             "OK" if not resize else "NO",
             f"calls to cattura_ridimensiona(): {len(resize)} (expected 0) — "
             f"it is the half of the thesis that makes §7.1 a NEW door")
        # ⚠ With the hand raised nothing is pressed: the orphans line must NOT
        #   be there.  If it were, the count of `input.c` would be dirty.
        #
        # ⛔ And buttons and keys are looked at SEPARATELY, and it is SAID which
        #    of the two showed up: they are two different defects (the pointer
        #    is replaced at the viewport, the keyboard only at a keymap change)
        #    and a red that does not tell them apart sends one looking in the
        #    wrong place.
        orph_p = M_ORPHAN_BUTTONS in ini
        orph_t = M_ORPHAN_KEYS in ini
        which_ones = ("buttons" if orph_p and not orph_t
                 else "keys" if orph_t and not orph_p
                 else "buttons AND keys" if orph_p else "")
        test_case("L4 with the hand raised there are NO orphans",
             "OK" if not (orph_p or orph_t) else "NO",
             "no orphans line, neither of buttons nor of keys, as it should be"
             if not (orph_p or orph_t)
             else f"⛔ the orphans line ({which_ones}) is there without anything being "
                  f"pressed: the count of input.c is dirty")
        return show(a, cases)

    # ------------------------------------------------------------------ #
    #  "kept" mode: the bad scene, with the wake-up or with the resize
    # ------------------------------------------------------------------ #
    port = "wake-up" if wakeups else ("resize" if resize else "NONE")
    deltas = ([d for (_n, _e, d) in wakeups] or [d for (_e, d) in resize])

    test_case("T0 the door opened: the devices were replaced",
         "OK" if deltas and any(d >= 1 for d in deltas) else "NO",
         f"door={port}, delta of ricambi_puntatore={deltas} (expected ≥1).  "
         f"⛔ If it were 0 the defect was NOT reproduced, and what follows "
         f"measures nothing")

    # ⛔ Was the BUTTON DOWN BEFORE the door?  Without it, there is no orphan to
    #    measure and the red would accusations the wrong thing.
    #
    # ⛔⛔ And the form **of the buttons** is searched, not the common part: the
    #      scene also holds the Ctrl down, and the KEYS line is written by the
    #      same `printf` (`%u %s were PRESSED…`).  ⚠ With the common part, T1
    #      would be green for a keyboard line even if the button had never
    #      become an orphan — that is, precisely when the scene does not hold.
    #      *Regression found by the adversarial review on 22 Aug 2026: the
    #      old bench had the distinction.*
    orph_p = M_ORPHAN_BUTTONS in ini
    orph_t = M_ORPHAN_KEYS in ini
    test_case("T1 the BUTTON was pressed at the moment of the replacement",
         "OK" if orph_p else "NO",
         "`input.c` declares the orphans of the BUTTONS, so the button was there"
         if orph_p
         else "⛔ THE BENCH: no orphan of BUTTONS declared"
              + (" — there is only the KEYS one, which is another thing: at "
                 "the viewport change the keyboard is not replaced, so this "
                 "scene did not do what it believed" if orph_t
                 else " — either nothing was pressed, or the replacement arrived "
                      "before the press"))

    g = button_code(lines, 1)
    test_case("T2 the witness saw the button GO DOWN",
         "OK" if g >= 0 else "NO",
         "BTN_LEFT down seen" if g >= 0
         else "⛔ THE BENCH: the witness did not even see the press")

    # ---- T3: the release, WHEREVER it is ----------------------------------
    # ⛔ And the right question is "does the release arrive?", not "does it
    #    arrive AFTER the replacement": with a cure that releases BEFORE, the
    #    release arrives before — and a bench that looked only at the "after"
    #    would call the cure red.
    # ⛔⛔ AND THE RELEASE OF THE HELD BUTTON IS TOLD FROM THAT OF THE FRESH
    #      CLICK **by the press that separates them** — bench defect found on
    #      21 August 2026 on the twin `06-b33-giudice.py`: taking "the first
    #      release after the held press" risks taking the release of the NEW
    #      click, and then T3 turns green on a stuck desktop.
    #  ⇒ The boundary is the SECOND press: what comes before belongs to the
    #    held button, what comes after belongs to the fresh click.
    g2 = button_code(lines, 1, g) if g >= 0 else -1
    limit = g2 if g2 >= 0 else len(lines)
    s = -1
    if g >= 0:
        cand = button_code(lines[:limit], 0, g)
        s = cand
    test_case("T3 ⛔ the button release reaches the desktop (before or after, as long as it arrives)",
         "OK" if s >= 0 else "DIFETTO_VIVO",
         "the release arrives — ⭐ so this door is cured" if s >= 0
         else "it does NOT arrive: the seat counts the button as still down "
              "(`meta-seat-impl.c:899-908`), and `handle_button` "
              "(`meta-eis-client.c:612-621`) silently swallows the release on the "
              "new device")

    # ---- T4: ⭐ THE MEASUREMENT THAT COUNTS — does the desktop still take clicks? -----
    s2 = button_code(lines, 0, g2) if g2 >= 0 else -1
    test_case("T4 ⭐⭐ does a FRESH click, after all, still arrive?",
         "OK" if g2 >= 0 and s2 >= 0 else "DIFETTO_VIVO",
         f"fresh click: down {'yes' if g2 >= 0 else 'NO'}, up {'yes' if s2 >= 0 else 'NO'}"
         + ("" if g2 >= 0 and s2 >= 0 else
            " — ⛔ from now on the desktop DOES NOT TAKE A CLICK ANY MORE, for the "
            "whole session: it is \"on Android the mouse no longer takes clicks\""))

    # ---- T5: the check INSIDE the scene — the keyboard ---------------------
    # ⚠ The keyboard is not a viewport device (`remove_viewport_devices` looks
    #   at TOUCH and POINTER_ABSOLUTE), so at a geometry replacement it is NOT
    #   replaced and its release MUST arrive.  If it did not, the cause would
    #   be something else and T3/T4 would accusations the wrong thing.
    #
    # ⛔⛔ And "not injected" IS NOT "injected and lost" — bench defect found
    #      on 21 August 2026, at the first run of the `guarigione` scene: that
    #      scene presses no key, and T5/T6 came out RED saying *"not even the
    #      key arrives"* — that is, the bench accused the product of something
    #      nobody had asked of it (`CODER.md` §3.10).
    #      ⇒ If the key was not even REQUESTED from the injector, the case is
    #      out of scene, not red.
    requested_ctrl = "posizione 29 1 ->" in ini
    requested_send = "posizione 28 1 ->" in ini
    kg = keystroke(lines, KEY_CTRL, 1)
    ks = keystroke(lines, KEY_CTRL, 0, kg) if kg >= 0 else -1
    if not requested_ctrl:
        test_case("T5 the KEY instead goes down and comes back up (check inside the scene)",
             "NON_IN_SCENA",
             "this scene presses no Ctrl: there is nothing to judge")
    else:
        test_case("T5 the KEY instead goes down and comes back up (check inside the scene)",
             "OK" if kg >= 0 and ks >= 0 else "NO",
             f"Ctrl down {'yes' if kg >= 0 else 'NO'}, up {'yes' if ks >= 0 else 'NO'}"
             + ("" if kg >= 0 and ks >= 0 else
                " — ⛔ not even the key arrives: the cause is NOT the replacement "
                "of the POINTER, and T3/T4 are accusing the wrong thing"))

    ke = keystroke(lines, KEY_ENTER, 1)
    if not requested_send:
        test_case("T6 and a FRESH key still arrives", "NON_IN_SCENA",
             "this scene presses no Enter: there is nothing to judge")
    else:
        test_case("T6 and a FRESH key still arrives",
             "OK" if ke >= 0 else "NO",
             "Enter seen" if ke >= 0
             else "⛔ not even the keyboard works any more: the damage is wider "
                  "than what §4.6 describes")

    # ---- T7: the line that declares the BUTTON's fallback -------------------
    # ⛔ And the expectation depends on the WORLD, it is not fixed: if the
    #    release arrived (cure present) there is no fallback to declare, and
    #    demanding the line would be writing the expectation of the world with
    #    the defect alive.
    #
    # ⛔⛔ And the form **of the button** is searched: `"DOES NOT LEAVE: it was
    #      pressed on a…"` without what follows matches both *"on a DEVICE"*
    #      (the pointer) and *"on a KEYBOARD"*.  ⚠ The defect T7 exists to
    #      catch is the BUTTON release that does not arrive while its path
    #      stays silent: a keyboard line would have let it pass in green.
    #      *Regression found by the adversarial review on 22 Aug 2026.*
    np_button = M_BUTTON_NOT_LEAVING in ini
    np_key = M_KEY_NOT_LEAVING in ini
    if np_button:
        test_case("T7 the impossible release of the BUTTON is DECLARED", "OK",
             "the line is there: the log does NOT say \"done\" while the desktop "
             "stays stuck")
    elif s >= 0:
        test_case("T7 the impossible release of the BUTTON is DECLARED", "OK",
             "⭐ the line is not there — and that is right: the release ARRIVED, "
             "so there was no fallback to declare")
    else:
        test_case("T7 the impossible release of the BUTTON is DECLARED", "NO",
             "⛔ the button release did not arrive AND its path stays "
             "silent: it is the green that is not true (`CODER.md` §4.6)"
             + (".  ⚠ The KEYBOARD line is there, which is another thing and "
                "does not count for the button" if np_key else ""))

    return show(a, cases)


def show(a, cases):
    print(f"\n== 06-b33 §7.1 · judgement «{a.label}» · mode {a.mode}")
    print(f"   scene: {a.scene}")
    rossi = 0
    for c in cases:
        clr = {"OK": GREEN, "NO": RED, "DIFETTO_VIVO": YELLOW,
               "NON_IN_SCENA": BLUE}[c["outcome"]]
        print(f"   {clr}{c['outcome']:12s}{GRAY} {c['case']}")
        print(f"                {c['detail']}")
        if c["outcome"] == "NO":
            rossi += 1
    living = sum(1 for c in cases if c["outcome"] == "DIFETTO_VIVO")
    report = sum(1 for c in cases if c["outcome"] == "NON_IN_SCENA")
    print(f"\n   {len(cases)} cases · {rossi} red · {living} live defects "
          f"declared · {report} out of scene")
    if a.outcomes:
        with open(a.outcomes, "a", encoding="utf-8") as f:
            f.write(json.dumps({"label": a.label, "mode": a.mode,
                                "scene": a.scene, "cases": cases},
                               ensure_ascii=False) + "\n")
        print(f"   results: {a.outcomes}")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
