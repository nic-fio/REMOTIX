#!/bin/bash
#
# 02-capture-certify.sh — runs ON THE SERVER.  ⛔ The certification of the
# F2.2 bench on the B12 model: healthy N → fault M → healed N, with the expected numbers
# **written before the round**.
#
#   bash /media/REMOTIX/src/02-capture-certify.sh            healthy round + the four faults
#   bash /media/REMOTIX/src/02-capture-certify.sh PREFISSO   reuses a healthy round already done
#
# ===========================================================================
# ⛔ WHY IT EXISTS, AND WHY IN THE SAME ROUND AS WHOEVER WRITES THE BENCH
#
# ⭐ The rule born on 11 Aug 2026: *whoever writes a bench certifies it in the
#    same round*, or the count never goes down.  And `PLAN.md` §0.3 point 4: every
#    phase, before declaring a number, proves that its bench can see the
#    defect it is looking for.
#
# ⛔ And for F2.2 the question is not academic.  The defect this bench exists
#    to see is **a black and valid frame**: a buffer of the right
#    size, with the right stride, the right damage, the right sequence — and
#    nothing inside.  ⛔ It is the worst fault of this sub-phase because every
#    other tool of the project would promote it: `misura-cattura` of phase 0
#    would count 36 frames per second and would not look inside even one.
#
# ⇒ A bench that cannot tell a black frame from a full one **would give
#   confidence**, and it is precisely the case `REVIEWER.md` §1 calls the
#   worst: *«a defect in the bench is found by nothing, and it poisons every
#   following measurement because it gives confidence»*.
#
# ===========================================================================
# ⛔ THE FAULT IS INJECTED INTO THE PIXELS, AND TOUCHES NEITHER THE PRODUCER NOR THE JUDGE
#
# It is the reason why the producer (`02-capture-frame.c`) and the judge
# (`02-capture-judge.py`) are two separate programs: between the two there is a file,
# and in that file anything can be put.  ⭐ No recompilation,
# no line changed, no `git`.  The fault is the **data**, which is the most
# honest way of breaking a judge.
#
# ⛔ AND ALWAYS ON A COPY, with the original kept aside and the fingerprint next to it
#    — like `01-b12-guasti.py`, which never touches the file to be broken.
#
# ===========================================================================
# ⛔ THE EXPECTATIONS, WRITTEN BEFORE THE ROUND (B0.4)
#
#   the HEALTHY round exits 0 (GREEN) — and it is not a widened expectation: the frame
#   is there, it is 1920×1080 as requested, and it contains the «bandiera» scene.
#   ⚠ If the healthy round did NOT exit 0, the certification **stops**: no
#     fault is injected on a bench already red, because the red afterwards would not
#     say anything (`PHASES.md` §00-ambiente, and the lesson of B13).
#
#   | # | the fault injected into the .raw | expected | REQUIRED mark           | FORBIDDEN mark |
#   |---|-------------------------------|--------|-------------------------|---------------|
#   | G1| full black, same bytes        |   1    | BLACK FRAME             | —             |
#   | G2| uniform grey, same bytes      |   1    | SCENE NOT RECOGNISED    | BLACK FRAME   |
#   | G3| last bytes cut off            |   1    | BYTES DO NOT ADD UP     | —             |
#   | G4| the «first» copied onto «steady»|  1    | THE BUFFER DID NOT CHANGE | BLACK FRAME |
#
#   and the HEALED one goes back to 0 after each.
#
# ⭐ THE TWO COLUMNS «REQUIRED» AND «FORBIDDEN» ARE THE HALF THAT COUNTS, and without the
#    second this certification would be a performance:
#
#   - **G2** is the fault that tells a judge from a brightness
#     meter.  A uniform grey is not black: calling it black would mean
#     getting the worst diagnosis wrong precisely in the case where it is needed, and the cure
#     would be looked for on the wrong side — the same half day that
#     `PLAN.md` tells about for the black session;
#   - **G4** is the fault of trap 8 of `LESSONS.md` §4: *«the last
#     frame must be kept and resent, or whoever connects to a still desktop
#     stays on black»*.  An old buffer resent is a
#     perfectly valid frame, not black, with the scene inside — ⛔ **green on every
#     check that looks at a single frame**.  It shows only by comparing
#     two, and that is why the producer takes two.
#
# ⛔ And a fault that is NOT in this table, declared instead of kept silent:
#    **the buffer of the wrong card** (`LESSONS.md` §4 trap 6, two GPUs
#    on this machine).  It cannot be injected here and this bench would not
#    see it: on the memory road the pixels arrive anyway.  It stays a
#    `[?]` of the report, not something this green acquits.
# ===========================================================================
set -uo pipefail

HERE=${HERE:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
JUDGE=$SRC/02-capture-judge.py
LAUNCH=$SRC/02-capture-launch.sh
SCENE=${SCENE:-flag}
mkdir -p "$HERE" || { echo "⛔ I cannot create $HERE" >&2; exit 2; }
LOG=$HERE/certificazione-$(date -u +%Y%m%d-%H%M%S).log

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

EXPECTED_HEALTHY=0

# ---------------------------------------------------------------------------
#  The injection: always on a copy, with the fingerprint before and after
# ---------------------------------------------------------------------------
graft()
{
	local desc=$1 regime=$2 first=$3
	python3 - "$desc" "$regime" "$first" <<'FINE'
import os, sys
che, regime, primo = sys.argv[1:4]
n = os.path.getsize(regime)
if che == "nero":
    dati = bytes(n)
elif che == "grigio":
    # ⛔ Not just any grey: BGRx with B=G=R=128 and x=255, that is a
    #    perfectly valid and perfectly useless frame.
    dati = bytes([128, 128, 128, 255]) * (n // 4) + bytes(n % 4)
elif che == "troncato":
    dati = open(regime, "rb").read()[: n - 40000]
elif che == "copy":
    dati = open(primo, "rb").read()
    if len(dati) > n:
        dati = dati[:n]
    elif len(dati) < n:
        dati = dati + bytes(n - len(dati))
else:
    print("unknown fault:", che, file=sys.stderr)
    sys.exit(2)
open(regime, "wb").write(dati)
print("    --  injected «%s»: %d bytes (they were %d)" % (che, len(dati), n))
FINE
	return $?
}

fingerprint() { sha256sum "$1" | cut -d' ' -f1; }

# ---------------------------------------------------------------------------
#  A round of the judge, and the comparison with the expectation written beforehand
# ---------------------------------------------------------------------------
judge()
{
	local prefix=$1 dove=$2
	python3 -u "$JUDGE" --manifest "$prefix.json" --scene "$SCENE" \
	        --json "$dove.json" > "$dove.log" 2>&1
	return $?
}

marks_of()
{
	# ⛔ Only the RED marks: a warning on the `first` frame — where the scene
	#    is not there yet — is not a finding, and counting it here would pass off as
	#    «the fault was seen» a noise that was there in the healthy round too.
	python3 -c '
import json, sys
v = json.load(open(sys.argv[1]))
m = [r["mark"] for f in v.get("frames", {}).values()
     for r in f.get("findings", []) if r.get("red", True)]
m += [r["mark"] for r in v.get("confronto_primo_regime", {}).get("findings", [])]
print(" ".join(sorted(set(m))))' "$1"
}

verify()
{
	local name=$1 output=$2 expected=$3 marks=$4 claim=$5 forbidden=$6
	local good=si
	if [ "$output" != "$expected" ]; then
		ko "$name: exit $output, expected $expected"; good=
	fi
	if [ -n "$claim" ] && [[ "$marks" != *"$claim"* ]]; then
		ko "$name: the REQUIRED mark «$claim» is missing — found: ${marks:-none}"; good=
	fi
	if [ -n "$forbidden" ] && [[ "$marks" == *"$forbidden"* ]]; then
		ko "$name: the FORBIDDEN mark «$forbidden» is there — the judge gets the diagnosis wrong"; good=
	fi
	if [ -n "$good" ]; then
		ok "$name: exit $output as expected, marks: ${marks:-none}"
		return 0
	fi
	return 1
}

# ===========================================================================
{
log "0. THE INITIAL STATE — declared and checked (B0.1)"
for f in "$JUDGE" "$LAUNCH"; do
	if [ ! -r "$f" ]; then ko "⛔ cannot read: $f"; exit 2; fi
done
ok "the two files of the bench can be read"

log "0-bis. THE JUDGE FIRST OF ALL: does it pass its own positive control?"
inf "⛔ A bench is not certified with an uncertified tool: it would be measuring"
inf "   with a ruler whose scale was never checked (LESSONS.md §1.2)."
python3 -u "$JUDGE" --positive-check-only
if [ $? -ne 0 ]; then
	ko "⛔ the judge is NOT certified: the certification stops here"
	exit 2
fi
ok "the judge finds the flag, calls black the black, and does NOT call black the grey"

# ---------------------------------------------------------------------------
log "1. THE HEALTHY ROUND — and the expectation is $EXPECTED_HEALTHY, written beforehand"
PREFIX=${1:-}
if [ -z "$PREFIX" ]; then
	inf "no prefix given: I do a real round with $LAUNCH"
	SCENE=$SCENE bash "$LAUNCH" measure
	U_LAUNCH=$?
	inf "the healthy round exited with $U_LAUNCH"
	# ⛔ The exit is not enough: the PREFIX of the round is needed, and it is taken from the
	#    most recent file instead of guessed.  ⚠ And the list is built with a
	#    glob, not with `ls` inside a pipe: «no file» and «ls failed»
	#    look the same in a chain of `|`, and it is item 3 of
	#    `PHASES.md` §00-ambiente — «no line found» was a denied read.
	CANDIDATES=()
	for m in "$HERE"/giro-*.json; do
		case "$m" in *-verdetto.json) continue ;; esac
		[ -f "$m" ] && CANDIDATES+=("$m")
	done
	if [ ${#CANDIDATES[@]} -eq 0 ]; then
		ko "⛔ no manifest in $HERE: the healthy round produced nothing."
		inf "⚠ It is not «the bench is broken»: it is «there was no round»."
		exit 2
	fi
	PREFIX=$(ls -t "${CANDIDATES[@]}" | head -1)
	PREFIX=${PREFIX%.json}
fi
if [ -z "$PREFIX" ] || [ ! -f "$PREFIX.json" ]; then
	ko "⛔ I cannot find the manifest of the healthy round ($PREFIX.json)"
	exit 2
fi
ok "healthy round: $PREFIX"

REGIME=$PREFIX-regime.raw
FIRST=$PREFIX-primo.raw
if [ ! -f "$REGIME" ] || [ ! -f "$FIRST" ]; then
	ko "⛔ the two .raw of the healthy round are missing: there is nothing to break"
	inf "⚠ and this is NOT a broken bench: it is a round that took no frames."
	exit 2
fi

# ⛔ THE ORIGINAL IS PUT ASIDE BEFORE TOUCHING IT, with the fingerprint next to it.
ORIGINAL=$HERE/originale-regime.raw
cp -f "$REGIME" "$ORIGINAL" || exit 2
IMP_ORIG=$(fingerprint "$ORIGINAL")
inf "original put aside: $ORIGINAL"
inf "fingerprint: $IMP_ORIG"

judge "$PREFIX" "$HERE/cert-sano"; U_HEALTHY=$?
M_HEALTHY=$(marks_of "$HERE/cert-sano.json")
verify "healthy" "$U_HEALTHY" "$EXPECTED_HEALTHY" "$M_HEALTHY" "" ""
if [ $? -ne 0 ]; then
	ko "⛔ THE HEALTHY ROUND IS NOT HEALTHY: the certification stops."
	inf "Injecting a fault on a bench already red would give a red that says nothing."
	inf "The judge's log:"
	sed 's/^/       /' "$HERE/cert-sano.log"
	cp -f "$ORIGINAL" "$REGIME"
	exit 2
fi

# ---------------------------------------------------------------------------
FAILED=0
#      name        expected  REQUIRED mark             FORBIDDEN mark
FAULTS=(
	"nero|1|BLACK FRAME|"
	"grigio|1|SCENE NOT RECOGNISED|BLACK FRAME"
	"troncato|1|BYTES DO NOT ADD UP|"
	"copia|1|THE BUFFER DID NOT CHANGE|BLACK FRAME"
)
for entry in "${FAULTS[@]}"; do
	IFS='|' read -r NAME EXP CLAIM FORBIDDEN <<< "$entry"

	log "2. FAULT «$NAME» — expected $EXP, required mark «$CLAIM», forbidden «${FORBIDDEN:-none}»"
	cp -f "$ORIGINAL" "$REGIME" || exit 2
	graft "$NAME" "$REGIME" "$FIRST" || { ko "injection failed"; FAILED=$((FAILED+1)); continue; }
	inf "fingerprint after the injection: $(fingerprint "$REGIME")"

	judge "$PREFIX" "$HERE/cert-guasto-$NAME"; U=$?
	M=$(marks_of "$HERE/cert-guasto-$NAME.json")
	verify "guasto/$NAME" "$U" "$EXP" "$M" "$CLAIM" "$FORBIDDEN" || FAILED=$((FAILED+1))

	log "3. HEALED after «$NAME» — expected $EXPECTED_HEALTHY"
	cp -f "$ORIGINAL" "$REGIME" || exit 2
	IMP=$(fingerprint "$REGIME")
	if [ "$IMP" != "$IMP_ORIG" ]; then
		ko "⛔ the healing did not put the file back as it was: $IMP ≠ $IMP_ORIG"
		FAILED=$((FAILED+1))
	else
		ok "the fingerprint went back to the one before: $IMP"
	fi
	judge "$PREFIX" "$HERE/cert-risano-$NAME"; U=$?
	M=$(marks_of "$HERE/cert-risano-$NAME.json")
	verify "risanato/$NAME" "$U" "$EXPECTED_HEALTHY" "$M" "" "" || FAILED=$((FAILED+1))
done

# ---------------------------------------------------------------------------
log "4. THE VERDICT OF THE CERTIFICATION"
cp -f "$ORIGINAL" "$REGIME"
if [ $FAILED -eq 0 ]; then
	ok "⭐ THE F2.2 BENCH IS CERTIFIED: healthy $EXPECTED_HEALTHY → four faults → healed $EXPECTED_HEALTHY"
	inf "⚠ And this does not say the bench is right: it says it can see THESE four"
	inf "  defects. «I found nothing» is not «it is right» (REVIEWER.md §0)."
	OUTCOME=0
else
	ko "⛔ THE CERTIFICATION DOES NOT PASS: $FAILED checks failed."
	inf "Until it passes, no number of this bench counts."
	OUTCOME=1
fi
inf "the full log of this round: $LOG"

# The catalogue, in the form of 01-b12-guasti.py, printed here so that it stays
# next to the numbers instead of in a separate document.
cat <<FINE

  THE LINE FOR THE CATALOGUE OF CERTIFICATIONS
  ────────────────────────────────────────────────────────────────────────
  name            F2.2 — capture (the black and valid frame)
  command         bash /media/REMOTIX/src/02-capture-certify.sh
  expected healthy 0 (VERDE: a 1920×1080 frame that contains the scene)
  faults          nero · grigio · troncato · copia — injected into the .raw, never
                  into the code, always on a copy with the original aside
  expected fault  1  each, with the required mark AND the forbidden one
  expected healed 0  after each, with the fingerprint back to the one before
  cost            file-copy (no recompilation)
  reference       fasi/rapporti/F2-2-cattura.md · STUDIES.md §gnome §3.1 §13 M9 ·
                  LESSONS.md §1.9 §4 trap 8 · REVIEWER.md §1 point 4, E1

FINE
exit $OUTCOME
} 2>&1 | tee "$LOG"
exit "${PIPESTATUS[0]}"
