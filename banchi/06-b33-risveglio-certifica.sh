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

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PAROLA_SUDO=${1:?needs the 0600 file with the sudo password}
shift
GUASTI=${*:-RG1 RG2 RG3 RG4 RG5}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
SANI=$LAV/sani-risveglio

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
DENTRO_SRC=/srv/src/${SRC#/media/REMOTIX/src/}
DENTRO_LAV=/srv/remotix/tmp/${LAV#/media/REMOTIX/tmp/}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ESITO=0

[ -r "$PAROLA_SUDO" ] || { printf '⛔ %s cannot be read\n' "$PAROLA_SUDO"; exit 2; }
sudo_mio() { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
dentro()   { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' \
                 bash /media/REMOTIX/enter.sh --root "$@"; }

costruisci() {
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
	dentro "SRC=$DENTRO_SRC/src LAV=$DENTRO_LAV bash $DENTRO_SRC/banchi/06-b33-risveglio-costruisci.sh" \
		> "$LAV/costr-$1.log" 2>&1
}

# ⛔⛔ THE ROUND, AND WHAT HAPPENS IF IT DOES NOT RUN — finding R3, 22 August 2026.
#
# Before, this function **threw away the outcome** of `risveglio.sh` and
# printed the line count with `inf`, never with `ko`; and `mappa()` read the
# **last** `s2-tenuto` line from a file that the judge opens in **append** and
# that nobody truncated.
#
# ⇒ A server running on the port was enough for `iniettore-accendi` to refuse,
#   `rimonta` to return 3 and `risveglio.sh` to exit **without appending
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
#      **3 = the scene did not hold** (`rimonta` failed, witness not opened),
#      0/1 = the round gave a verdict.
#
# Fills `MAPPA`; returns 1 if the round did not run.
MAPPA=""
giro() { # $1 = label
	local f e
	f=$LAV/esiti-$1.jsonl
	MAPPA=""
	# ⛔ And it is CHECKED that it is gone, not hoped: the judge writes that file
	#    **as root**, and if one day the folder were no longer ours the `rm`
	#    would fail silently ⇒ yesterday's line would be read again, that is,
	#    exactly the defect this function exists to close.
	rm -f "$f" 2>/dev/null || sudo_mio rm -f "$f" >/dev/null 2>&1
	if [ -e "$f" ]; then
		ko "⛔ THE BENCH: I cannot delete $f ⇒ I would read YESTERDAY's outcome"
		return 1
	fi
	ESITI="$f" bash "$QUI/06-b33-risveglio.sh" "$PAROLA_SUDO" tenuto \
		> "$LAV/giro-$1.log" 2>&1
	e=$?
	if [ "$e" -ge 2 ]; then
		ko "⛔ THE BENCH: round \"$1\" did not hold (exit $e) — the scene was not"
		ko "   mounted, and there is NO verdict to compare.  Tail:"
		tail -6 "$LAV/giro-$1.log" | sed 's/^/        /'
		return 1
	fi
	if [ ! -s "$f" ]; then
		ko "⛔ THE BENCH: round \"$1\" exited $e but wrote NO outcome"
		ko "   in $f ⇒ the judge did not even speak"
		return 1
	fi
	MAPPA=$(mappa "$f")
	if [ -z "$MAPPA" ]; then
		ko "⛔ THE BENCH: in $f there is no \"s2-tenuto\" line"
		return 1
	fi
	inf "round $1: $(grep -acE 'OK|NO|DIFETTO|NON_IN_SCENA' "$LAV/giro-$1.log") verdict lines"
	return 0
}

# the "case → outcome" map of the given round — ⛔ from ITS OWN file, not from
# a shared file in append: see the box above.
mappa() { python3 - "$1" <<'EOF'
import json, sys
try:
    righe = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
except OSError:
    righe = []
for r in reversed(righe):
    if r["etichetta"] == "s2-tenuto":
        print(" ".join("%s=%s" % (c["caso"].split()[0], c["esito"]) for c in r["casi"]))
        break
EOF
}

# the cases whose verdict CHANGED between two maps
cambiati() { python3 - "$1" "$2" <<'EOF'
import sys
a = dict(x.split("=") for x in sys.argv[1].split())
b = dict(x.split("=") for x in sys.argv[2].split())
fuori = []
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        fuori.append(k)
print(" ".join(fuori))
EOF
}

mkdir -p "$SANI"

log "0. The HEALTHY copies of the two files the faults touch"
for f in input.c mutter.c; do
	cp "$SRC/src/$f" "$SANI/$f" || { ko "I did not make the copy of $f"; exit 2; }
	inf "$f saved ($(wc -l < "$SANI/$f") lines)"
done
risana() { for f in input.c mutter.c; do cp "$SANI/$f" "$SRC/src/$f"; done; }

log "1. The HEALTHY round — ⛔ and if this is not green nothing is certified"
costruisci sano || { ko "⛔ the healthy tree does not compile"; tail -5 "$LAV/costr-sano.log"; exit 3; }
# ⛔ And if the round does not run we STOP: without a healthy map there is
#    nothing to compare with, and going on would mean certifying against
#    nothing.
giro sano || { ko "⛔ without the healthy round nothing is certified"; exit 3; }
SANA=$MAPPA
inf "healthy map: $SANA"
case "$SANA" in
*=NO*) ko "⛔ the HEALTHY round has reds: the bench cannot be certified"; exit 3 ;;
*DIFETTO_VIVO*) ko "⛔ the HEALTHY round still has DIFETTO_VIVO: cures \"A\" and \"C\""
                ko "   are not in, or they do not work.  Nothing is certified"; exit 3 ;;
*) ok "the healthy round is all green" ;;
esac

for G in $GUASTI; do
	ATTESO=$(python3 "$QUI/06-b33-risveglio-guasti.py" --elenco \
		| grep -A1 "^$G " | sed -n 's/.*must CHANGE: //p')
	FILE=$(python3 "$QUI/06-b33-risveglio-guasti.py" --elenco \
		| grep "^$G " | sed -n 's/.*\[\(.*\)\]/\1/p')
	log "2.$G — must change: $ATTESO   (in $FILE)"
	risana
	if ! python3 "$QUI/06-b33-risveglio-guasti.py" --albero "$SRC" --guasto "$G"; then
		ko "⛔ $G was not injected: this is NOT \"the fault does nothing\""
		continue
	fi
	if ! costruisci "$G"; then
		ko "⛔ $G does not compile:"; tail -6 "$LAV/costr-$G.log" | sed 's/^/        /'
		continue
	fi
	# ⛔ And if the faulty round does not run, it is NOT compared: "I did not
	#    look" and "the fault does nothing" look the same in a missing map, and
	#    it is precisely the way this script could print green on zero rounds
	#    (finding R3).
	if ! giro "$G"; then
		ko "⛔ $G: the round did not run ⇒ NOTHING can be said about this fault"
		continue
	fi
	GUASTA=$MAPPA
	inf "faulty map: $GUASTA"
	OTT=$(cambiati "$SANA" "$GUASTA")
	inf "changed cases: ${OTT:-none}"
	# ⛔ EQUALITY OF THE SET, not membership: a fault that changed EVERYTHING
	#    would necessarily contain the declared case, and would pass.
	# ⛔ "none" is an expectation, not a case to look for: it is the EMPTY set.
	#    ⚠ Without this line the comparison looked for a case named "none" and
	#      declared red a non-fault that had done exactly what it should —
	#      bench defect, 21 Aug 2026.
	[ "$ATTESO" = none ] && ATTESO=""
	A=$(printf '%s\n' $ATTESO | sort | tr '\n' ' ')
	B=$(printf '%s\n' $OTT | sort | tr '\n' ' ')
	if [ "$A" = "$B" ]; then
		ok "⭐ $G changed EXACTLY the declared cases ($ATTESO)"
	else
		ko "⛔ $G should have changed \"${A% }\" and changed \"${B:-nothing}\"."
		ko "   ⚠ Either the fault is not what I believe, or the bench cannot see it,"
		ko "   or it sees more than one: the EXPECTATION is corrected with the reason written"
		ko "   next to it, not the verdict"
	fi
done

log "3. The HEALTHY files are put back and rebuilt"
risana
if costruisci risana; then
	ok "restored and rebuilt"
else
	ko "⛔ the restoration did NOT rebuild: the tree stays FAULTY"
fi
if giro risanato; then
	RIS=$MAPPA
	inf "restored map: $RIS"
	[ "$RIS" = "$SANA" ] && ok "the restored round is identical to the healthy one" \
		|| ko "⛔ the restored one did NOT come back like the healthy one: $RIS"
else
	ko "⛔ the restored round did not run: ⚠ it CANNOT be said that the tree is"
	ko "   healthy again, and the doubt remains that a fault is inside"
fi

log "Outcome"
inf "results: $LAV/esiti-<round>.jsonl"
exit $ESITO
