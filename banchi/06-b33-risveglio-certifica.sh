#!/bin/bash
#
# 06-b33-risveglio-certifica.sh — ⛔⛔ THE POSITIVE CONTROL of the §7.1 bench.
#
#   ⚠ RUNS ON THE SERVER (192.168.0.2), as user `nicfio`, NOT as root.
#
#   bash 06-b33-risveglio-certifica.sh <file-parola-sudo> [RG1 RG2 RG3 RG4 RG5]
#
# ===========================================================================
# ⛔ WHAT IT CERTIFIES, AND WHY IT DOES NOT COMPARE THE REDS
# ===========================================================================
#
# `06-b33-certifica.sh` compares the set of **red** cases.  ⛔ Here that is not
# possible: the expectations of this bench have **three colours**, and the two
# cases that matter — T3 and T4 — with the defect alive do not turn red, they
# turn `DIFETTO_VIVO`, which is the right colour for a measured defect.  ⇒ A
# comparison on the reds would not see them change, and every fault would pass.
#
# ⇒ What is compared is **the map of verdicts** — case by case, colour by
#   colour — between the healthy round and the faulty round, and it is
#   demanded that **exactly** the cases declared in
#   `06-b33-risveglio-guasti.py` have changed.
#
# ⭐ It is stronger than the comparison on the reds for another reason too: it
#   also sees the cases that become **greener**, which are the symptom of a
#   fault that is not the one we believed.
#
# ===========================================================================
# ⛔⛔ AND THIS BENCH HAS ALREADY REFUTED TWO OF MY EXPLANATIONS — 21 August 2026
# ===========================================================================
#
# I had declared RG3 "the fault worth more than all the others", with this
# reason: *"it removes the `close()` of the old descriptor, so Mutter sees no
# detach and the desktop stays stuck"*.  ⛔ `[M]` Nothing changes.
# Then I had written RG4: *"then it is `ei_disconnect()` that sends the
# detach"*.  ⛔ `[M]` Nothing changes with it either.
#
# ⇒ ⭐ The two paths are **redundant**, and each one is enough on its own.
#     Only `RG5`, which removes **both**, breaks the healing.
#
# ⚠ And the lesson counts more than the mechanics: **two consecutive
#   hypotheses, both plausible, both refuted by an injected fault.**  Neither
#   would have been discovered by rereading the code, and the first was already
#   written in `mutter.h` as if it were a fact.  ⇒ It is `PIANO.md` §0.4 point 2
#   taken literally: one tries to break, not to confirm.
set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
SUDO_PASSWORD=${1:?needs the 0600 file with the sudo password}
shift
FAULTS=${*:-RG1 RG2 RG3 RG4 RG5}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
HEALTHY=$LAV/sani-risveglio

# ⛔⛔ THE PATHS INSIDE THE CONTAINER ARE DERIVED, NOT WRITTEN — finding R4
#      of the adversarial review, 22 August 2026.
#
#      `enter.sh` shows `/media/REMOTIX/src` as `/srv/src` and
#      `/media/REMOTIX/tmp` as `/srv/remotix/tmp`.  ⚠ The tree name **crosses
#      the container boundary**, and it is exactly the point where
#      `07-b41-accendi.sh` has already paid: *"with a different tree it
#      compiled the previous one and started the new one — "it compiled" and
#      "it compiled THE RIGHT ONE" had the same face"*.
#
# ⛔ And it is CHECKED that the tree sits where the container can see it: an
#    `SRC` outside `/media/REMOTIX/src` would not compile at all, and the worst
#    way to find out is a fault that "does nothing".
case "$SRC" in
/media/REMOTIX/src/*) ;;
*) printf '⛔ SRC=%s is not under /media/REMOTIX/src: the container does not see it,\n' "$SRC"
   printf '   and a fault injected in there would NEVER reach the binary.\n'
   exit 2 ;;
esac
case "$LAV" in
/media/REMOTIX/tmp/*) ;;
*) printf '⛔ LAV=%s is not under /media/REMOTIX/tmp: the binary would come out in\n' "$LAV"
   printf '   one place and the terrain would look for it in another.\n'
   exit 2 ;;
esac
INSIDE_SRC=/srv/src/${SRC#/media/REMOTIX/src/}
INSIDE_WORK=/srv/remotix/tmp/${LAV#/media/REMOTIX/tmp/}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; OUTCOME=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
OUTCOME=0

[ -r "$SUDO_PASSWORD" ] || { printf '⛔ %s cannot be read\n' "$SUDO_PASSWORD"; exit 2; }
my_sudo() { printf '%s\n' "$(cat "$SUDO_PASSWORD")" | sudo -S -p 'Password: ' "$@"; }
inside()   { printf '%s\n' "$(cat "$SUDO_PASSWORD")" | sudo -S -p 'Password: ' \
                 bash /media/REMOTIX/enter.sh --root "$@"; }

build() {
	# ⛔ We look at the builder's OUTCOME, not at the presence of the file: a
	#    binary from yesterday answers "yes" to *does it exist?* just like one
	#    from now.
	#
	# ⛔⛔ AND THE PATH IS DERIVED FROM `$SRC`, not written by hand — finding R4
	#      of the adversarial review, 22 August 2026.
	#
	#      Here there was a hard-wired `/srv/src/06-i-src`, while the fault, the
	#      healthy copies and the restoration all went through `$SRC`.  ⇒
	#      Passing a different `SRC` was enough to **fault one tree and
	#      recompile another**: the fault did not reach the binary, RG3 and RG4
	#      (expected "none") came out green **by construction**, and the
	#      restored one matched.  ⚠ It is the same shape that in another bench
	#      has already produced a false red against the product.
	#
	# ⚠ Inside `enter.sh` the folder `/media/REMOTIX/src` is seen as `/srv/src`
	#   and `/media/REMOTIX/tmp` as `/srv/remotix/tmp`: the translation is done
	#   HERE, only once, and with the reason next to it.
	inside "SRC=$INSIDE_SRC/src LAV=$INSIDE_WORK bash $INSIDE_SRC/banchi/06-b33-risveglio-costruisci.sh" \
		> "$LAV/constr-$1.log" 2>&1
}

# ⛔⛔ THE ROUND, AND WHAT HAPPENS IF IT DOES NOT RUN — finding R3, 22 August 2026.
#
# Before, this function **threw away the outcome** of `risveglio.sh` and
# printed the line count with `inf`, never with `ko`; and `map()` read the
# **last** `s2-tenuto` line from a file that the judge opens in **append** and
# that nobody truncated.
#
# ⇒ A server running on the port was enough for `injector-turn-on` to refuse,
#   `remount` to return 3 and `risveglio.sh` to exit **without appending
#   anything**: `SANA` became **yesterday's green** map, every faulty map was
#   the same line, the restored one matched ⇒ ⛔ **green certification on zero
#   rounds**.
#
# The two cures, and both are needed:
#   1. **every round has a results file of ITS OWN**, deleted first: if it stays
#      empty, the round did not run, and there is no line from yesterday to read;
#   2. **the outcome of `risveglio.sh` is looked at**.  ⚠ But "different from
#      zero" is not enough: with an injected fault the red cases MUST be there,
#      and then the script exits 1 legitimately.  ⇒ It is told apart by code:
#      **3 = the scene did not hold** (`remount` failed, witness not opened),
#      0/1 = the round gave a verdict.
#
# Fills `MAP`; returns 1 if the round did not run.
MAP=""
lap() { # $1 = label
	local f e
	f=$LAV/outcomes-$1.jsonl
	MAP=""
	# ⛔ And it is CHECKED that it is gone, not hoped: the judge writes that file
	#    **as root**, and if one day the folder were no longer ours the `rm`
	#    would fail silently ⇒ yesterday's line would be read again, that is,
	#    exactly the defect this function exists to close.
	rm -f "$f" 2>/dev/null || my_sudo rm -f "$f" >/dev/null 2>&1
	if [ -e "$f" ]; then
		ko "⛔ THE BENCH: I cannot delete $f ⇒ I would read YESTERDAY's outcome"
		return 1
	fi
	OUTCOMES="$f" bash "$HERE/06-b33-risveglio.sh" "$SUDO_PASSWORD" kept \
		> "$LAV/lap-$1.log" 2>&1
	e=$?
	if [ "$e" -ge 2 ]; then
		ko "⛔ THE BENCH: round \"$1\" did not hold (exit $e) — the scene was not"
		ko "   mounted, and there is NO verdict to compare.  Tail:"
		tail -6 "$LAV/lap-$1.log" | sed 's/^/        /'
		return 1
	fi
	if [ ! -s "$f" ]; then
		ko "⛔ THE BENCH: round \"$1\" exited $e but wrote NO outcome"
		ko "   in $f ⇒ the judge did not even speak"
		return 1
	fi
	MAP=$(map "$f")
	if [ -z "$MAP" ]; then
		ko "⛔ THE BENCH: in $f there is no \"s2-tenuto\" line"
		return 1
	fi
	inf "round $1: $(grep -acE 'OK|NO|DIFETTO|NON_IN_SCENA' "$LAV/lap-$1.log") verdict lines"
	return 0
}

# the "case → outcome" map of the given round — ⛔ from ITS OWN file, not from
# a shared file in append: see the box above.
map() { python3 - "$1" <<'EOF'
import json, sys
try:
    line_list = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
except OSError:
    line_list = []
for r in reversed(line_list):
    if r["label"] == "s2-tenuto":
        print(" ".join("%s=%s" % (c["case_v"].split()[0], c["outcome"]) for c in r["cases"]))
        break
EOF
}

# the cases whose verdict CHANGED between two maps
changed() { python3 - "$1" "$2" <<'EOF'
import sys
a = dict(x.split("=") for x in sys.argv[1].split())
b = dict(x.split("=") for x in sys.argv[2].split())
outside = []
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        outside.append(k)
print(" ".join(outside))
EOF
}

mkdir -p "$HEALTHY"

log "0. The HEALTHY copies of the two files the faults touch"
for f in input.c mutter.c; do
	cp "$SRC/src/$f" "$HEALTHY/$f" || { ko "I did not make the copy of $f"; exit 2; }
	inf "$f saved ($(wc -l < "$HEALTHY/$f") lines)"
done
heals() { for f in input.c mutter.c; do cp "$HEALTHY/$f" "$SRC/src/$f"; done; }

log "1. The HEALTHY round — ⛔ and if this is not green nothing is certified"
build healthy || { ko "⛔ the healthy tree does not compile"; tail -5 "$LAV/costr-sano.log"; exit 3; }
# ⛔ And if the round does not run we STOP: without a healthy map there is
#    nothing to compare with, and going on would mean certifying against
#    nothing.
lap healthy || { ko "⛔ without the healthy round nothing is certified"; exit 3; }
SANA=$MAP
inf "healthy map: $SANA"
case "$SANA" in
*=NO*) ko "⛔ the HEALTHY round has reds: the bench cannot be certified"; exit 3 ;;
*DIFETTO_VIVO*) ko "⛔ the HEALTHY round still has DIFETTO_VIVO: cures \"A\" and \"C\""
                ko "   are not in, or they do not work.  Nothing is certified"; exit 3 ;;
*) ok "the healthy round is all green" ;;
esac

for G in $FAULTS; do
	EXPECTED=$(python3 "$HERE/06-b33-risveglio-guasti.py" --listing \
		| grep -A1 "^$G " | sed -n 's/.*must CHANGE: //p')
	FILE=$(python3 "$HERE/06-b33-risveglio-guasti.py" --listing \
		| grep "^$G " | sed -n 's/.*\[\(.*\)\]/\1/p')
	log "2.$G — must change: $EXPECTED   (in $FILE)"
	heals
	if ! python3 "$HERE/06-b33-risveglio-guasti.py" --tree "$SRC" --fault "$G"; then
		ko "⛔ $G was not injected: this is NOT \"the fault does nothing\""
		continue
	fi
	if ! build "$G"; then
		ko "⛔ $G does not compile:"; tail -6 "$LAV/constr-$G.log" | sed 's/^/        /'
		continue
	fi
	# ⛔ And if the faulty round does not run, it is NOT compared: "I did not
	#    look" and "the fault does nothing" look the same in a missing map, and
	#    it is precisely the way this script could print green on zero rounds
	#    (finding R3).
	if ! lap "$G"; then
		ko "⛔ $G: the round did not run ⇒ NOTHING can be said about this fault"
		continue
	fi
	BROKEN=$MAP
	inf "faulty map: $BROKEN"
	OCT=$(changed "$SANA" "$BROKEN")
	inf "changed cases: ${OCT:-none}"
	# ⛔ EQUALITY OF THE SET, not membership: a fault that changed EVERYTHING
	#    would necessarily contain the declared case, and would pass.
	# ⛔ "none" is an expectation, not a case to look for: it is the EMPTY set.
	#    ⚠ Without this line the comparison looked for a case named "none" and
	#      declared red a non-fault that had done exactly what it should —
	#      bench defect, 21 Aug 2026.
	[ "$EXPECTED" = none ] && EXPECTED=""
	A=$(printf '%s\n' $EXPECTED | sort | tr '\n' ' ')
	B=$(printf '%s\n' $OCT | sort | tr '\n' ' ')
	if [ "$A" = "$B" ]; then
		ok "⭐ $G changed EXACTLY the declared cases ($EXPECTED)"
	else
		ko "⛔ $G should have changed \"${A% }\" and changed \"${B:-nothing}\"."
		ko "   ⚠ Either the fault is not what I believe, or the bench cannot see it,"
		ko "   or it sees more than one: the EXPECTATION is corrected with the reason written"
		ko "   next to it, not the verdict"
	fi
done

log "3. The HEALTHY files are put back and rebuilt"
heals
if build heals; then
	ok "restored and rebuilt"
else
	ko "⛔ the restoration did NOT rebuild: the tree stays FAULTY"
fi
if lap healed; then
	RESULT=$MAP
	inf "restored map: $RESULT"
	[ "$RESULT" = "$SANA" ] && ok "the restored round is identical to the healthy one" \
		|| ko "⛔ the restored one did NOT come back like the healthy one: $RESULT"
else
	ko "⛔ the restored round did not run: ⚠ it CANNOT be said that the tree is"
	ko "   healthy again, and the doubt remains that a fault is inside"
fi

log "Outcome"
inf "results: $LAV/outcomes-<label>.jsonl (one per round)"
exit $OUTCOME
