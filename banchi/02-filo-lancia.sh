#!/usr/bin/env bash
# =========================================================================
# 02-filo-lancia.sh — ⛔ F2.4: the whole round of the wire bench, phase 2.
#
#     ./02-filo-lancia.sh              everything that can be run TODAY
#     ./02-filo-lancia.sh --elenco     the predictions, without measuring
#     ./02-filo-lancia.sh --vivo       ⏳ the client too, against 7514
#
# =========================================================================
# ⛔ WHY THIS SCRIPT EXISTS, AND IT IS NOT «for convenience»
#
# `PIANO.md` §0.4 moment 1: the reviewer steps in **as soon as the bench exists,
# BEFORE the product is written**.  The phase 2 product is not there:
#
#     grep -c '0x0301\|0x0302' src/rcp.c src/webtransport.c src/pagina.html
#     -> 0 · 0 · 0        `[M]` 12 Aug 2026
#
# ⛔ Hence the job of this file: **line up what can be
#    measured today, and DECLARE what cannot**.  A round that ran
#    only the pieces that pass and kept silent about the others would be the worst of
#    proofs: green, and on nothing.
#
# ⚠ And rule **B0.4** of `FASI.md` §01-filo-nudo applies here more than elsewhere:
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
#     ⚠ `FASI.md` §00-ambiente B3.3 — paid for **four times**, two of them
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

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ESITI="$QUI/02-filo-esiti.jsonl"
PORTA=7514
VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'

ROSSI=0
FATTI=0
SALTATI=0

dice() { printf '%s\n' "$*"; }

# ⛔ The comparison is done by THIS function, not by whoever reads (B0.4).
pezzo() {
    local nome="$1" atteso="$2"; shift 2
    dice ""
    dice "== $nome   (expected: exit $atteso)"
    "$@"
    local visto=$?
    FATTI=$((FATTI + 1))
    if [ "$visto" -eq "$atteso" ]; then
        dice "   ${VERDE}OK${GRIGIO}  $nome: exit $visto"
    else
        dice "   ${ROSSO}NO${GRIGIO}  $nome: exit $visto, expected $atteso"
        ROSSI=$((ROSSI + 1))
    fi
}

salta() {
    local nome="$1" perche="$2"
    SALTATI=$((SALTATI + 1))
    dice ""
    dice "   ${GIALLO}--${GRIGIO}  $nome: SKIPPED — $perche"
    dice "       ⛔ and «skipped» is not «passed»: it enters the final count"
}

# -------------------------------------------------------------------------
if [ "${1:-}" = "--elenco" ]; then
    dice "== F2.4 — the predictions, all of them, before any round"
    python3 "$QUI/02-filo-fotogramma.py" --elenco
    dice ""
    python3 "$QUI/02-filo-validatore.py" --elenco
    dice ""
    python3 "$QUI/02-filo-cliente.py" --elenco
    exit 0
fi

dice "==========================================================="
dice "  F2.4 — THE WIRE: a frame from RCP to the page"
dice "==========================================================="
dice ""
dice "== ⛔ the initial state, declared AND checked (B0.1)"
dice "   machine: $(uname -n)   python: $(python3 -V)"

# ⛔ The port is looked at, not freed.  And if `ss` is not there it is SAID, instead of
#    concluding «free» from a command that did not run (form E8).
if command -v ss >/dev/null; then
    OCCUPANTI="$(ss -lun | grep -c ":$PORTA " || true)"
    if [ "$OCCUPANTI" -eq 0 ]; then
        dice "   port $PORTA: ${VERDE}free${GRIGIO} (${OCCUPANTI} listeners)"
    else
        dice "   port $PORTA: ${ROSSO}TAKEN${GRIGIO} by $OCCUPANTI listeners"
        dice "   ⛔ NOTHING is switched off.  It is declared and it exits: on 7448 runs"
        dice "      the house product and on 7501 the P5 target."
        exit 2
    fi
else
    dice "   port $PORTA: ${GIALLO}NOT LOOKED AT${GRIGIO} — \`ss\` is not on"
    dice "      this machine.  ⛔ And «not looked at» is not «free»."
fi

# ⛔ The presence of aioquic is DECLARED, and it decides what can be run.
if python3 -c "import aioquic" 2>&1 | grep -q ModuleNotFoundError; then
    AIOQUIC=no
    dice "   aioquic: ${GIALLO}absent${GRIGIO} — the live pieces are not run"
    dice "      ⚠ it lives only inside the container (\`/media/REMOTIX/enter.sh\`)"
else
    AIOQUIC=si
    dice "   aioquic: ${VERDE}present${GRIGIO}"
fi

# ⛔ And the state of the PRODUCT, which is the reason half of this bench
#    cannot be run yet.  It is counted, not believed.
VIDEO_NEL_PRODOTTO=0
for f in "$QUI/../src/rcp.c" "$QUI/../src/webtransport.c" "$QUI/../src/pagina.html"; do
    if [ -r "$f" ]; then
        N="$(grep -c '0x0301\|0x0302' "$f" || true)"
        VIDEO_NEL_PRODOTTO=$((VIDEO_NEL_PRODOTTO + N))
    fi
done
dice "   the phase 2 product: $VIDEO_NEL_PRODOTTO occurrences of 0x0301/0x0302 in src/"
if [ "$VIDEO_NEL_PRODOTTO" -eq 0 ]; then
    dice "      ⏳ zero: the video is not written yet, and it is the right moment"
    dice "         for a bench (\`PIANO.md\` §0.4 moment 1)"
fi

# -------------------------------------------------------------------------
dice ""
dice "==========================================================="
dice "  WHAT IS MEASURED TODAY, WITHOUT PRODUCT AND WITHOUT NETWORK"
dice "==========================================================="

pezzo "the frame judge" 0 \
    python3 "$QUI/02-filo-fotogramma.py" --uscita "$ESITI"

pezzo "the certification of the judge (healthy -> fault -> healed)" 0 \
    python3 "$QUI/02-filo-fotogramma.py" --certifica --uscita "$ESITI"

pezzo "the video channel referee, certified against G4" 0 \
    python3 "$QUI/02-filo-validatore.py" --certifica --uscita "$ESITI"

pezzo "the referee on a conforming recording" 0 \
    python3 "$QUI/02-filo-validatore.py" \
        "$QUI/02-filo-prove/02-filo-prova-buona.rcpreg" --uscita "$ESITI"

# ⛔ AND THE RED THAT MUST BE RED — the referee's positive control.
#
#    §11: *«before concluding that the validator finds no errors, it is given
#    a recording WITH AN ERROR INSIDE and it is checked that it sees it.  A
#    tool that has never found anything is not a clean tool: it is
#    an uncertified tool»*.
pezzo "⭐ the referee on a NON-conforming recording (must exit 1)" 1 \
    python3 "$QUI/02-filo-validatore.py" \
        "$QUI/02-filo-prove/02-filo-prova-tipo-storto.rcpreg"

# ⛔ AND THE ONE THAT MUST SAY «I HAVE NOTHING TO JUDGE» (exit 3).
#
#    It is the half that gets forgotten: a referee that exited 0 on a
#    recording without one byte of video **would acquit without having looked**,
#    and it is finding R7.4 of phase 1.
pezzo "⭐ the referee on a recording without video (must exit 3)" 3 \
    python3 "$QUI/02-filo-validatore.py" \
        "$QUI/02-filo-prove/02-filo-prova-solo-controllo.rcpreg"

# -------------------------------------------------------------------------
dice ""
dice "==========================================================="
dice "  WHAT CANNOT BE MEASURED TODAY, AND WHY"
dice "==========================================================="

if [ "${1:-}" = "--vivo" ] && [ "$AIOQUIC" = si ] && [ "$VIDEO_NEL_PRODOTTO" -gt 0 ]; then
    pezzo "the test client receives the frame (port $PORTA)" 0 \
        python3 "$QUI/02-filo-cliente.py" --porta "$PORTA" \
            --registra "$QUI/02-filo-prove/02-filo-vivo.rcpreg" \
            --uscita "$ESITI"
    pezzo "the referee on the live trace" 0 \
        python3 "$QUI/02-filo-validatore.py" \
            "$QUI/02-filo-prove/02-filo-vivo.rcpreg" --uscita "$ESITI"
else
    salta "the test client, live" \
        "the product does not send frames ($VIDEO_NEL_PRODOTTO occurrences), \
aioquic=$AIOQUIC, --vivo=${1:-no}"
    dice "       ⏳ its first round IS the first measurement of phase 2, and it must"
    dice "          be done on $PORTA, inside the container"
fi

salta "the decoded pixels against the captured ones" \
    "it is F2.6, and it is not a protocol measurement"
salta "the credit of the streams beyond 256 frames (§2.3)" \
    "phase 2 delivers ONE still frame: it is phase 3"

# -------------------------------------------------------------------------
dice ""
dice "==========================================================="
dice "  THE VERDICT, WITH ITS DENOMINATOR"
dice "==========================================================="
dice ""
dice "   pieces run:     $FATTI"
dice "   pieces skipped: $SALTATI   ⛔ and «skipped» is not «passed»"
dice "   log:            $ESITI"
dice ""
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
dice "== ⭐⛔ THE LINES THAT ENTERED \`RCP.md\` ON 12 AUG 2026"
dice "   Seven in the morning (P1-P7), **two in the evening** — P8 from D14 (the grace on"
dice "   frames in flight) and P9 from D13 (the real keyframe at every canvas change) —"
dice "   and ⛔ **two born from the two of the evening**: P10 (§5.2, WHEN the client"
dice "   reconfigures) and P11 (§6.2, the window instead of «the previous one»),"
dice "   found by applying the first ones and cured in the next round.  The number is not"
dice "   written here: the two referees count it."
dice "   The count is computed by the two referees looking up the cases by name: a"
dice "   rule that lost one of the two turns red here, not six months from now."
python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -E 'rules with BOTH' | \
    sed 's/^ */   frame judge:            /'
python3 "$QUI/02-filo-validatore.py" --elenco | grep -E 'lines with BOTH' | \
    sed 's/^ */   recordings referee: /'
dice ""
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
dice "== ⛔⛔ THE PROPOSALS STILL OPEN — \`RCP.md\` does not carry them"
python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -E 'proposals with ALL' | \
    sed 's/^ */   frame judge:            /'
python3 "$QUI/02-filo-validatore.py" --elenco | grep -E "proposals with BOTH" | \
    sed 's/^ */   recordings referee: /'
dice ""
dice "== ⭐⛔ THE POINTS WHERE \`RCP.md\` DOES NOT DECIDE WELL, in this chapter"
dice "   ⚠ Two families, and they are not the same thing: a **double reading** makes"
dice "     two careful implementations diverge; an **internal contradiction**"
dice "     makes them converge on the same wrong byte — and it is worse, because"
dice "     no comparison between two implementations finds it."
python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -A1 'AMBIGUO$' | \
    grep -v '^--$' | sed 's/^/   /'
if ! python3 "$QUI/02-filo-fotogramma.py" --elenco | grep -q 'AMBIGUO$'; then
    dice "   ⭐ none: the EIGHT this bench found all entered"
    dice "      the document on 12 Aug 2026 — four in the morning (P2 §6.2 ·"
    dice "      P3 §2.5 · P5 §6.2 · P6 §5.2), three with them (P1 · P4 · P7), two"
    dice "      in the evening (P8 §6.2 · P9 §5.2) and ⛔ two born FROM the two of the evening"
    dice "      (P10 §5.2 · P11 §6.2), found by applying them a few hours later."
    dice "   ⚠ And this does NOT mean that \`RCP.md\` has none left: it means"
    dice "     that none are left among those THIS bench can look for."
fi

dice ""
if [ "$ROSSI" -gt 0 ]; then
    dice "   ${ROSSO}⛔ F2.4: $ROSSI pieces out of $FATTI do not pass${GRIGIO}"
    exit 1
fi
dice "   ${VERDE}⭐ F2.4: $FATTI pieces out of $FATTI pass${GRIGIO}"
dice "   ⚠ and it is NOT «the frame arrives»: in this round not one"
dice "     byte went over the network, and $SALTATI pieces were skipped for lack of"
dice "     product.  The green is worth what the denominator says."
exit 0
