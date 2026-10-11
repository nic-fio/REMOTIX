#!/usr/bin/env bash
# =========================================================================
# 02-wire-launch.sh — ⛔ F2.4: the whole round of the wire bench, phase 2.
#
#     ./02-wire-launch.sh              everything that can be run TODAY
#     ./02-wire-launch.sh --list     the predictions, without measuring
#     ./02-wire-launch.sh --alive       ⏳ the client too, against 7514
#
# =========================================================================
# ⛔ WHY THIS SCRIPT EXISTS, AND IT IS NOT «for convenience»
#
# `PLAN.md` §0.4 moment 1: the reviewer steps in **as soon as the bench exists,
# BEFORE the product is written**.  The phase 2 product is not there:
#
#     grep -c '0x0301\|0x0302' src/rcp.c src/webtransport.c src/page.html
#     -> 0 · 0 · 0        `[M]` 12 Aug 2026
#
# ⛔ Hence the job of this file: **line up what can be
#    measured today, and DECLARE what cannot**.  A round that ran
#    only the pieces that pass and kept silent about the others would be the worst of
#    proofs: green, and on nothing.
#
# ⚠ And rule **B0.4** of `PHASES.md` §01-filo-nudo applies here more than elsewhere:
#   *«the expectation is compared by the bench, not by whoever reads»*.  Every piece below
#   exits with a status, and this file **compares** it — it does not just print it.
#
# =========================================================================
# ⛔ THE THREE SHELL TRAPS THIS FILE DOES NOT REPEAT
#
#  1. ⛔ **no `2>/dev/null`, and no exit status thrown into a
#     chain of `|`** (`REVIEWER.md` §1 point 4).  «Zero» and «failure» look
#     the same when the error has been swallowed, and it is error
#     form **E8**;
#
#  2. ⛔ **never a redirection AROUND `ssh` or `enter.sh`**.  `sudo`'s
#     password prompt comes out on **stderr**: throwing it away, nobody
#     can answer, and the command **hangs forever, silently**.
#     ⚠ `PHASES.md` §00-ambiente B3.3 — paid for **four times**, two of them
#     in the single night of 11 Aug 2026, and two of those **inside the files
#     that describe the trap in their header**;
#
#  3. ⛔ **`set -e` is NOT enough and it is not here**: it exits at the first red, and a
#     round that stops at the first red does not say how much it had covered.  The
#     reds are counted and it goes on, and at the end there is a denominator.
#
# =========================================================================
# ⛔ THE INITIAL STATE, DECLARED **AND CHECKED** — rule B0.1
#
# *«A bench that does not know which state it starts from measures the history of the machine.»*
#
#  · the F2.4 port is **7514**, and this script checks that it is free
#    before saying anything.  ⛔ If it is taken **nothing is switched off**:
#    it is declared and it exits.  On **7448** runs the house product and on
#    **7501** the P5 target, on on purpose (mandate §4);
#  · the pieces that run on CHUWI **do not touch the network**: the frame
#    judge and the recordings referee have no dependencies, and it is
#    intended — whoever reviews the bench before the product does not have the container;
#  · `aioquic` lives **only inside the container**, and its absence is
#    **declared**: ⛔ a piece skipped silently and a piece passed look
#    the same.
# =========================================================================
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTCOMES="$HERE/02-wire-outcomes.jsonl"
PORT=7514
GREEN=$'\033[1;32m'; RED=$'\033[1;31m'; YELLOW=$'\033[1;33m'; GRAY=$'\033[0m'

ROSSI=0
DONE=0
SKIPPED=0

says() { printf '%s\n' "$*"; }

# ⛔ The comparison is done by THIS function, not by whoever reads (B0.4).
piece() {
    local name="$1" expected="$2"; shift 2
    says ""
    says "== $name   (expected: exit $expected)"
    "$@"
    local seen=$?
    DONE=$((DONE + 1))
    if [ "$seen" -eq "$expected" ]; then
        says "   ${GREEN}OK${GRAY}  $name: exit $seen"
    else
        says "   ${RED}NO${GRAY}  $name: exit $seen, expected $expected"
        ROSSI=$((ROSSI + 1))
    fi
}

skip() {
    local name="$1" why="$2"
    SKIPPED=$((SKIPPED + 1))
    says ""
    says "   ${YELLOW}--${GRAY}  $name: SKIPPED — $why"
    says "       ⛔ and «skipped» is not «passed»: it enters the final count"
}

# -------------------------------------------------------------------------
if [ "${1:-}" = "--list" ]; then
    says "== F2.4 — the predictions, all of them, before any round"
    python3 "$HERE/02-wire-frame.py" --list
    says ""
    python3 "$HERE/02-wire-validator.py" --list
    says ""
    python3 "$HERE/02-wire-client.py" --list
    exit 0
fi

says "==========================================================="
says "  F2.4 — THE WIRE: a frame from RCP to the page"
says "==========================================================="
says ""
says "== ⛔ the initial state, declared AND checked (B0.1)"
says "   machine: $(uname -n)   python: $(python3 -V)"

# ⛔ The port is looked at, not freed.  And if `ss` is not there it is SAID, instead of
#    concluding «free» from a command that did not run (form E8).
if command -v ss >/dev/null; then
    OCCUPANTS="$(ss -lun | grep -c ":$PORT " || true)"
    if [ "$OCCUPANTS" -eq 0 ]; then
        says "   port $PORT: ${GREEN}free${GRAY} (${OCCUPANTS} listeners)"
    else
        says "   port $PORT: ${RED}TAKEN${GRAY} by $OCCUPANTS listeners"
        says "   ⛔ NOTHING is switched off.  It is declared and it exits: on 7448 runs"
        says "      the house product and on 7501 the P5 target."
        exit 2
    fi
else
    says "   port $PORT: ${YELLOW}NOT LOOKED AT${GRAY} — \`ss\` is not on"
    says "      this machine.  ⛔ And «not looked at» is not «free»."
fi

# ⛔ The presence of aioquic is DECLARED, and it decides what can be run.
if python3 -c "import aioquic" 2>&1 | grep -q ModuleNotFoundError; then
    AIOQUIC=no
    says "   aioquic: ${YELLOW}absent${GRAY} — the live pieces are not run"
    says "      ⚠ it lives only inside the container (\`/media/REMOTIX/enter.sh\`)"
else
    AIOQUIC=si
    says "   aioquic: ${GREEN}present${GRAY}"
fi

# ⛔ And the state of the PRODUCT, which is the reason half of this bench
#    cannot be run yet.  It is counted, not believed.
VIDEO_IN_PRODUCT=0
for f in "$HERE/../src/rcp.c" "$HERE/../src/webtransport.c" "$HERE/../src/page.html"; do
    if [ -r "$f" ]; then
        N="$(grep -c '0x0301\|0x0302' "$f" || true)"
        VIDEO_IN_PRODUCT=$((VIDEO_IN_PRODUCT + N))
    fi
done
says "   the phase 2 product: $VIDEO_IN_PRODUCT occurrences of 0x0301/0x0302 in src/"
if [ "$VIDEO_IN_PRODUCT" -eq 0 ]; then
    says "      ⏳ zero: the video is not written yet, and it is the right moment"
    says "         for a bench (\`PLAN.md\` §0.4 moment 1)"
fi

# -------------------------------------------------------------------------
says ""
says "==========================================================="
says "  WHAT IS MEASURED TODAY, WITHOUT PRODUCT AND WITHOUT NETWORK"
says "==========================================================="

piece "the frame judge" 0 \
    python3 "$HERE/02-wire-frame.py" --output "$OUTCOMES"

piece "the certification of the judge (healthy -> fault -> healed)" 0 \
    python3 "$HERE/02-wire-frame.py" --certify --output "$OUTCOMES"

piece "the video channel referee, certified against G4" 0 \
    python3 "$HERE/02-wire-validator.py" --certify --output "$OUTCOMES"

piece "the referee on a conforming recording" 0 \
    python3 "$HERE/02-wire-validator.py" \
        "$HERE/02-filo-prove/02-filo-prova-buona.rcpreg" --output "$OUTCOMES"

# ⛔ AND THE RED THAT MUST BE RED — the referee's positive control.
#
#    §11: *«before concluding that the validator finds no errors, it is given
#    a recording WITH AN ERROR INSIDE and it is checked that it sees it.  A
#    tool that has never found anything is not a clean tool: it is
#    an uncertified tool»*.
piece "⭐ the referee on a NON-conforming recording (must exit 1)" 1 \
    python3 "$HERE/02-wire-validator.py" \
        "$HERE/02-filo-prove/02-filo-prova-tipo-storto.rcpreg"

# ⛔ AND THE ONE THAT MUST SAY «I HAVE NOTHING TO JUDGE» (exit 3).
#
#    It is the half that gets forgotten: a referee that exited 0 on a
#    recording without one byte of video **would acquit without having looked**,
#    and it is finding R7.4 of phase 1.
piece "⭐ the referee on a recording without video (must exit 3)" 3 \
    python3 "$HERE/02-wire-validator.py" \
        "$HERE/02-filo-prove/02-filo-prova-solo-controllo.rcpreg"

# -------------------------------------------------------------------------
says ""
says "==========================================================="
says "  WHAT CANNOT BE MEASURED TODAY, AND WHY"
says "==========================================================="

if [ "${1:-}" = "--alive" ] && [ "$AIOQUIC" = si ] && [ "$VIDEO_IN_PRODUCT" -gt 0 ]; then
    piece "the test client receives the frame (port $PORT)" 0 \
        python3 "$HERE/02-wire-client.py" --port "$PORT" \
            --record "$HERE/02-filo-prove/02-filo-vivo.rcpreg" \
            --output "$OUTCOMES"
    piece "the referee on the live trace" 0 \
        python3 "$HERE/02-wire-validator.py" \
            "$HERE/02-filo-prove/02-filo-vivo.rcpreg" --output "$OUTCOMES"
else
    skip "the test client, live" \
        "the product does not send frames ($VIDEO_IN_PRODUCT occurrences), \
aioquic=$AIOQUIC, --alive=${1:-no}"
    says "       ⏳ its first round IS the first measurement of phase 2, and it must"
    says "          be done on $PORT, inside the container"
fi

skip "the decoded pixels against the captured ones" \
    "it is F2.6, and it is not a protocol measurement"
skip "the credit of the streams beyond 256 frames (§2.3)" \
    "phase 2 delivers ONE still frame: it is phase 3"

# -------------------------------------------------------------------------
says ""
says "==========================================================="
says "  THE VERDICT, WITH ITS DENOMINATOR"
says "==========================================================="
says ""
says "   pieces run:     $DONE"
says "   pieces skipped: $SKIPPED   ⛔ and «skipped» is not «passed»"
says "   log:            $OUTCOMES"
says ""
# ⛔ THE DOUBLE READINGS, AND THE COUNT OF THE RULES THAT HAVE A CASE THAT MAKES THEM
#    TRIGGER.
#
# ⚠ Until 11 Aug the four ambiguities of `RCP.md` were printed here with
#   the text to propose.  ⭐ On 12 Aug 2026 those four ENTERED the
#   document (§2.5, §5.2, §6.2) together with the other three, and this block
#   became the opposite question:
#
#     ⛔ *do the new rules have the input that makes them trigger?*
#
#   A referee that knows a rule and does not have the case that violates it does not
#   enforce it, and the green it gives is the one that gives confidence.  And the case that
#   **respects** it counts as much as the other: without it, a rule written too broadly
#   would stay green on the whole bench.
says "== ⭐⛔ THE LINES THAT ENTERED \`RCP.md\` ON 12 AUG 2026"
says "   Seven in the morning (P1-P7), **two in the evening** — P8 from D14 (the grace on"
says "   frames in flight) and P9 from D13 (the real keyframe at every canvas change) —"
says "   and ⛔ **two born from the two of the evening**: P10 (§5.2, WHEN the client"
says "   reconfigures) and P11 (§6.2, the window instead of «the previous one»),"
says "   found by applying the first ones and cured in the next round.  The number is not"
says "   written here: the two referees count it."
says "   The count is computed by the two referees looking up the cases by name: a"
says "   rule that lost one of the two turns red here, not six months from now."
python3 "$HERE/02-wire-frame.py" --list | grep -E 'rules with BOTH' | \
    sed 's/^ */   frame judge:            /'
python3 "$HERE/02-wire-validator.py" --list | grep -E 'lines with BOTH' | \
    sed 's/^ */   recordings referee: /'
says ""
# ⛔⛔ AND THE CURES `RCP.md` DOES NOT CARRY YET.  ⚠ Added on the evening of 12
#    Aug 2026 with defect **D14**, and the same evening the block changed
#    content: D14 went in (P8), and in its place there are the **two points
#    where that evening's cures do not hold** — P10 (the two new lines
#    contradict each other on the same frame) and P11 (the grace names «the previous
#    canvas» in the singular, and whoever drags a window sends two).
#    ⛔ Found **by applying** the lines to the two referees, which is the same way
#    the two wrong ones out of seven had been found in the morning.
#    ⚠ It sits in a block of ITS OWN and not together with the count
#    above: «lines the document carries» and «cures the document does not have»
#    are two different facts, and adding them up would give a number that means
#    nothing.  ⛔ And the pair has a different form: the test that shows it and
#    the one that prevents writing it too broadly.
says "== ⛔⛔ THE PROPOSALS STILL OPEN — \`RCP.md\` does not carry them"
python3 "$HERE/02-wire-frame.py" --list | grep -E 'proposals with ALL' | \
    sed 's/^ */   frame judge:            /'
python3 "$HERE/02-wire-validator.py" --list | grep -E "proposals with BOTH" | \
    sed 's/^ */   recordings referee: /'
says ""
says "== ⭐⛔ THE POINTS WHERE \`RCP.md\` DOES NOT DECIDE WELL, in this chapter"
says "   ⚠ Two families, and they are not the same thing: a **double reading** makes"
says "     two careful implementations diverge; an **internal contradiction**"
says "     makes them converge on the same wrong byte — and it is worse, because"
says "     no comparison between two implementations finds it."
python3 "$HERE/02-wire-frame.py" --list | grep -A1 'AMBIGUO$' | \
    grep -v '^--$' | sed 's/^/   /'
if ! python3 "$HERE/02-wire-frame.py" --list | grep -q 'AMBIGUO$'; then
    says "   ⭐ none: the EIGHT this bench found all entered"
    says "      the document on 12 Aug 2026 — four in the morning (P2 §6.2 ·"
    says "      P3 §2.5 · P5 §6.2 · P6 §5.2), three with them (P1 · P4 · P7), two"
    says "      in the evening (P8 §6.2 · P9 §5.2) and ⛔ two born FROM the two of the evening"
    says "      (P10 §5.2 · P11 §6.2), found by applying them a few hours later."
    says "   ⚠ And this does NOT mean that \`RCP.md\` has none left: it means"
    says "     that none are left among those THIS bench can look for."
fi

says ""
if [ "$ROSSI" -gt 0 ]; then
    says "   ${RED}⛔ F2.4: $ROSSI pieces out of $DONE do not pass${GRAY}"
    exit 1
fi
says "   ${GREEN}⭐ F2.4: $DONE pieces out of $DONE pass${GRAY}"
says "   ⚠ and it is NOT «the frame arrives»: in this round not one"
says "     byte went over the network, and $SKIPPED pieces were skipped for lack of"
says "     product.  The green is worth what the denominator says."
exit 0
