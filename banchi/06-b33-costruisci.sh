#!/bin/bash
#
# 06-b33-costruisci.sh — ⛔ RUNS INSIDE THE CONTAINER.  Builds the witness
# of sub-phase 6.1 and drops it in the work folder.
#
#   printf '<parola>\n' | bash /media/REMOTIX/enter.sh --root \
#       'bash /srv/src/06-i-src/banchi/06-b33-costruisci.sh'
#
# ⛔ It exists because of the house rule «a file has no levels of quoting»: a
#    `$(pkg-config …)` written inside `ssh → enter.sh → bash -c` is expanded by
#    the WRONG shell — the host's, where `pkg-config` is not there.
#
# ⛔ And the witness binary is NOT the product: it is a Wayland client that
#    touches not one line of `src/`.  It is built separately on purpose — so a
#    fault injected into the product does not touch it, and the instrument stays
#    the same between the healthy run and the faulty run (`CODER.md` §3.3).
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
LAV=${LAV:-/srv/remotix/tmp/06-i}
XDG=${XDG:-/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml}

mkdir -p "$LAV"
cd "$QUI" || exit 2

echo "== the xdg-shell protocol"
[ -f "$XDG" ] || { echo "⛔ $XDG is not there"; exit 2; }
wayland-scanner client-header "$XDG" xdg-shell-client-protocol.h || exit 2
wayland-scanner private-code  "$XDG" xdg-shell-protocol.c || exit 2
echo "   made xdg-shell-client-protocol.h and xdg-shell-protocol.c"

echo
echo "== the witness"
# ⛔ It is thrown away BEFORE building: so «it is there» means «it is from now»,
#    and not «there was one from yesterday» (`LEZIONI.md` §1.9 point 8).
rm -f "$LAV/06-b33-testimone"
gcc -O1 -g -Wall -o "$LAV/06-b33-testimone" 06-b33-testimone.c xdg-shell-protocol.c \
	$(pkg-config --cflags --libs wayland-client) || exit 2
[ -x "$LAV/06-b33-testimone" ] || { echo "⛔ the witness was NOT built"; exit 2; }
ls -la "$LAV/06-b33-testimone"

echo
echo "== the mark: what is INSIDE the binary"
# ⛔ We look inside the binary, not in the source: between the two there is a
#    compilation, and that is what we want to verify.  ⛔⛔ And NOT with
#    `| grep -q`: with `pipefail` the early exit of `grep -q` gives SIGPIPE to
#    `strings`, the pipeline exits 141 and the `if` takes the wrong branch.
R=$(strings "$LAV/06-b33-testimone" | grep -c 'RITELA')
echo "   «RITELA»: $R"
if [ "$R" -gt 0 ]; then
	echo "   ⭐ the line is there that says, FROM THE RECEIVING SIDE, that the canvas has changed"
else
	echo "   ⛔ the RITELA line is not there: the witness could not say it has"
	echo "      been resized, and «nothing happened» and «I did not"
	echo "      see it» would look the same"
	exit 3
fi
exit 0
