#!/bin/bash
#
# 04-b25-launch.sh — the keyboard bench, and ITS CERTIFICATION.
#
# ⛔ Two jobs, and the second comes first in the order of trust:
#
#   1. compiles `src/keyboard.c` together with the bench and runs it;
#   2. ⛔ compiles the bench against THREE implementations wrong on purpose
#      (`04-b25-faults.c`) and DEMANDS that it says RED on each, and RED ON THE
#      RIGHT TEST.  A bench that has never seen the defect is not a test
#      (`CODER.md` §3.3, §3.4, §4.6).
#
# ⚠ No session is needed, nor a compositor, nor `libei`, nor a port:
#   the module is a pure function and is tested in isolation (`CODER.md` §3.6).  It runs
#   the same on the development machine and in the test machine's container.
#
#   usage:  bash benches/04-b25-launch.sh          (from the repository root)
#
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE" || exit 2
OUT="${OUT:-/tmp/04-b25-$$}"
mkdir -p "$OUT" || exit 2

CC="${CC:-cc}"
CFLAGS="-O1 -g -Wall -Wextra -Werror=implicit-function-declaration"
XKB_CFLAGS="$(pkg-config --cflags xkbcommon 2>/dev/null)"
XKB_LIBS="$(pkg-config --libs xkbcommon 2>/dev/null)"

if [ -z "$XKB_LIBS" ]; then
	echo "⛔ xkbcommon is missing (pkg-config): the bench cannot measure anything."
	echo "   Debian/Trixie: apt install libxkbcommon-dev"
	exit 2
fi

echo "== xkbcommon $(pkg-config --modversion xkbcommon)  ·  $(uname -n)  ·  $(date -Is)"

# ---------------------------------------------------------------------------
# 1. THE PRODUCT
# ---------------------------------------------------------------------------
echo
echo "———— 1. THE PRODUCT — src/keyboard.c ————"
# shellcheck disable=SC2086
$CC $CFLAGS $XKB_CFLAGS -o "$OUT/banco" \
	benches/04-b25-keyboard.c src/keyboard.c src/log.c $XKB_LIBS || {
	echo "⛔ the product does not compile"
	exit 2
}

"$OUT/banco" benches/04-b25-outcomes.jsonl
PRODUCT=$?

# ---------------------------------------------------------------------------
# 2. THE CERTIFICATION — the bench must be able to say RED
# ---------------------------------------------------------------------------
echo
echo "———— 2. THE CERTIFICATION — four defects planted on purpose ————"
echo "     (if one of these lines said VERDE, the bench would prove nothing)"
echo

# fault → a piece of the «prova» line that MUST come out red
declare -A WAIT=(
	[1]='U+00E9) on «us»'
	[2]='U+00E9) on «it»'
	[3]='zz_non_esiste'
	[4]='session «it» + negotiated «us»'
)
declare -A WHAT=(
	[1]='sends the «e» instead of the «é»'
	[2]='forgets the modifiers'
	[3]='falls back to «us» silently'
	[4]='trusts the negotiated name, not the keymap of the session'
)

CERTIFICATE=0
for G in 1 2 3 4; do
	# shellcheck disable=SC2086
	$CC $CFLAGS -DGUASTO=$G $XKB_CFLAGS -o "$OUT/guasto$G" \
		benches/04-b25-keyboard.c benches/04-b25-faults.c $XKB_LIBS 2>"$OUT/cc$G.txt" || {
		echo "⛔ fault $G does not compile:"
		sed 's/^/     /' "$OUT/cc$G.txt"
		CERTIFICATE=1
		continue
	}

	"$OUT/guasto$G" "$OUT/esiti-guasto$G.jsonl" >"$OUT/uscita$G.txt" 2>&1
	OUTPUT=$?

	# ⛔ «it said red» is not enough: it must have said red ON THE RIGHT TEST.
	#    A bench that goes red for any reason at all has not seen the defect.
	LINE=$(grep -F "${WAIT[$G]}" "$OUT/esiti-guasto$G.jsonl" 2>/dev/null | grep -c '"outcome":"red"')

	if [ "$OUTPUT" -eq 1 ] && [ "$LINE" -ge 1 ]; then
		printf '  ✅ fault %d (%s) ⇒ the bench says ROSSO, and on the right test\n' "$G" "${WHAT[$G]}"
		grep -F "${WAIT[$G]}" "$OUT/esiti-guasto$G.jsonl" |
			grep '"outcome":"red"' | head -1 | sed 's/^/       /'
	else
		printf '  ⛔ fault %d (%s) was NOT seen: exit=%d, expected red lines=%d\n' \
			"$G" "${WHAT[$G]}" "$OUTPUT" "$LINE"
		echo "     ⇒ THE BENCH IS NOT CERTIFIED: its green is worth nothing."
		sed 's/^/       /' "$OUT/uscita$G.txt" | tail -30
		CERTIFICATE=1
	fi
done

# ---------------------------------------------------------------------------
echo
echo "———— THE OUTCOME ————"
if [ "$CERTIFICATE" -ne 0 ]; then
	echo "⛔ THE BENCH IS NOT CERTIFIED — its green is not believed (CODER.md §3.3)."
	echo "   the files: $OUT"
	exit 2
fi
echo "✅ the bench is CERTIFIED: it saw all four defects, each on its own test."
if [ "$PRODUCT" -eq 0 ]; then
	echo "✅ and src/keyboard.c passes: benches/04-b25-outcomes.jsonl"
	rm -rf "$OUT"
	exit 0
fi
echo "⛔ but src/keyboard.c does NOT pass (exit $PRODUCT): benches/04-b25-outcomes.jsonl"
echo "   the files of the run: $OUT"
exit 1
