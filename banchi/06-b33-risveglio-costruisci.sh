#!/bin/bash
#
# 06-b33-risveglio-costruisci.sh — ⛔ RUNS INSIDE THE CONTAINER.  Builds
# the injector of §7.1 (the second door of the dying click) and drops it in the
# work folder.
#
#   printf '<parola>\n' | bash /media/REMOTIX/enter.sh --root \
#       'bash /srv/src/06-i-src/banchi/06-b33-risveglio-costruisci.sh'
#
# ⛔ It exists because of the house rule «a file has no levels of quoting»: a
#    `$(pkg-config …)` written inside `ssh → enter.sh → bash -c` is expanded by
#    the WRONG shell.
#
# ⛔⛔ And HERE THE BINARY **IS** THE PRODUCT, the opposite of the witness.
#      `06-b33-costruisci.sh` says, of the witness, that *«it touches not one
#      line of `src/`, so a fault injected into the product does not touch
#      it»*.  Here it is the reverse and it is intended: the defendant is
#      `cattura_risveglia()`, and a fault injected into `src/cattura.c`
#      **must** change this binary — or the positive control would control
#      nothing.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
SRC=${SRC:-$QUI/../src}
LAV=${LAV:-/srv/remotix/tmp/06-i}
USCITA=$LAV/06-b33-risveglio

mkdir -p "$LAV"
cd "$QUI" || exit 2

# ⛔ It is thrown away BEFORE building: so «it is there» means «it is from now»,
#    and not «there was one from yesterday» (`LEZIONI.md` §1.9 point 8).
rm -f "$USCITA"

CFLAGS=$(pkg-config --cflags glib-2.0 gio-2.0 libpipewire-0.3 libdrm libei-1.0 xkbcommon) || exit 2
LIBS=$(pkg-config --libs glib-2.0 gio-2.0 libpipewire-0.3 libei-1.0 xkbcommon) || exit 2

echo "== the wake-up injector"
# shellcheck disable=SC2086
gcc -O1 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE \
	-I"$SRC" $CFLAGS \
	-o "$USCITA" \
	06-b33-risveglio.c \
	"$SRC/cattura.c" "$SRC/input.c" "$SRC/mutter.c" "$SRC/tastiera.c" "$SRC/registro.c" \
	"$SRC/cursore.c" \
	$LIBS -lm || exit 2

[ -x "$USCITA" ] || { echo "⛔ the injector was NOT built"; exit 3; }
ls -la "$USCITA"

echo
echo "== the mark: what is INSIDE the binary"
# ⛔ We look inside the binary, not in the source: between the two there is a
#    compilation, and that is what we want to verify.  ⛔⛔ And NOT with
#    `| grep -q`: with `pipefail` the early exit of `grep -q` gives SIGPIPE to
#    `strings`, the pipeline exits 141 and the `if` takes the wrong branch.
R=$(strings "$USCITA" | grep -c 'stream RESTARTED at the same size')
echo "   the line of «cattura_risveglia»: $R"
if [ "$R" -gt 0 ]; then
	echo "   ⭐ inside is the PRODUCT's function, not an imitation of it"
else
	echo '   ⛔ the line of `cattura_risveglia()` is not there: this binary does NOT'
	echo "      contain the function under test — every measurement would be of"
	echo "      something else"
	exit 3
fi
O=$(strings "$USCITA" | grep -c 'were PRESSED on the device the compositor has just removed')
echo "   the line of the ORPHANS of src/input.c: $O"
[ "$O" -gt 0 ] || { echo "   ⛔ missing: the product's input is not linked in"; exit 3; }
exit 0
