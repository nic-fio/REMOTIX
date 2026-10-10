#!/bin/bash
#
# 04-b25-lancia.sh — the keyboard bench, and ITS CERTIFICATION.
#
# ⛔ Two jobs, and the second comes first in the order of trust:
#
#   1. compiles `src/tastiera.c` together with the bench and runs it;
#   2. ⛔ compiles the bench against THREE implementations wrong on purpose
#      (`04-b25-guasti.c`) and DEMANDS that it says ROSSO on each, and ROSSO ON THE
#      RIGHT TEST.  A bench that has never seen the defect is not a test
#      (`CODER.md` §3.3, §3.4, §4.6).
#
# ⚠ No session is needed, nor a compositor, nor `libei`, nor a port:
#   the module is a pure function and is tested in isolation (`CODER.md` §3.6).  It runs
#   the same on the development machine and in the test machine's container.
#
#   usage:  bash banchi/04-b25-lancia.sh          (from the repository root)
#
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$QUI" || exit 2
FUORI="${FUORI:-/tmp/04-b25-$$}"
mkdir -p "$FUORI" || exit 2

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
echo "———— 1. THE PRODUCT — src/tastiera.c ————"
# shellcheck disable=SC2086
$CC $CFLAGS $XKB_CFLAGS -o "$FUORI/banco" \
	banchi/04-b25-tastiera.c src/tastiera.c src/registro.c $XKB_LIBS || {
	echo "⛔ the product does not compile"
	exit 2
}

"$FUORI/banco" banchi/04-b25-esiti.jsonl
PRODOTTO=$?

# ---------------------------------------------------------------------------
# 2. THE CERTIFICATION — the bench must be able to say ROSSO
# ---------------------------------------------------------------------------
echo
echo "———— 2. THE CERTIFICATION — four defects planted on purpose ————"
echo "     (if one of these lines said VERDE, the bench would prove nothing)"
echo

# fault → a piece of the «prova» line that MUST come out red
declare -A ATTESA=(
	[1]='U+00E9) on «us»'
	[2]='U+00E9) on «it»'
	[3]='zz_non_esiste'
	[4]='session «it» + negotiated «us»'
)
declare -A COSA=(
	[1]='sends the «e» instead of the «é»'
	[2]='forgets the modifiers'
	[3]='falls back to «us» silently'
	[4]='trusts the negotiated name, not the keymap of the session'
)

CERTIFICATO=0
for G in 1 2 3 4; do
	# shellcheck disable=SC2086
	$CC $CFLAGS -DGUASTO=$G $XKB_CFLAGS -o "$FUORI/guasto$G" \
		banchi/04-b25-tastiera.c banchi/04-b25-guasti.c $XKB_LIBS 2>"$FUORI/cc$G.txt" || {
		echo "⛔ fault $G does not compile:"
		sed 's/^/     /' "$FUORI/cc$G.txt"
		CERTIFICATO=1
		continue
	}

	"$FUORI/guasto$G" "$FUORI/esiti-guasto$G.jsonl" >"$FUORI/uscita$G.txt" 2>&1
	USCITA=$?

	# ⛔ «it said red» is not enough: it must have said red ON THE RIGHT TEST.
	#    A bench that goes red for any reason at all has not seen the defect.
	RIGA=$(grep -F "${ATTESA[$G]}" "$FUORI/esiti-guasto$G.jsonl" 2>/dev/null | grep -c '"esito":"rosso"')

	if [ "$USCITA" -eq 1 ] && [ "$RIGA" -ge 1 ]; then
		printf '  ✅ fault %d (%s) ⇒ the bench says ROSSO, and on the right test\n' "$G" "${COSA[$G]}"
		grep -F "${ATTESA[$G]}" "$FUORI/esiti-guasto$G.jsonl" |
			grep '"esito":"rosso"' | head -1 | sed 's/^/       /'
	else
		printf '  ⛔ fault %d (%s) was NOT seen: exit=%d, expected red lines=%d\n' \
			"$G" "${COSA[$G]}" "$USCITA" "$RIGA"
		echo "     ⇒ THE BENCH IS NOT CERTIFIED: its green is worth nothing."
		sed 's/^/       /' "$FUORI/uscita$G.txt" | tail -30
		CERTIFICATO=1
	fi
done

# ---------------------------------------------------------------------------
echo
echo "———— THE OUTCOME ————"
if [ "$CERTIFICATO" -ne 0 ]; then
	echo "⛔ THE BENCH IS NOT CERTIFIED — its green is not believed (CODER.md §3.3)."
	echo "   the files: $FUORI"
	exit 2
fi
echo "✅ the bench is CERTIFIED: it saw all four defects, each on its own test."
if [ "$PRODOTTO" -eq 0 ]; then
	echo "✅ and src/tastiera.c passes: banchi/04-b25-esiti.jsonl"
	rm -rf "$FUORI"
	exit 0
fi
echo "⛔ but src/tastiera.c does NOT pass (exit $PRODOTTO): banchi/04-b25-esiti.jsonl"
echo "   the files of the run: $FUORI"
exit 1
