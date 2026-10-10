#!/bin/bash
#
# 06-b5-esiti-cattura.sh — builds and launches `06-b5-esiti-cattura.c`.
#
#   bash banchi/06-b5-esiti-cattura.sh [n]
#
#   exit 0  the declared cases are green
#   exit 1  ⛔ at least one is not
#   exit 2  the environment cannot hold the bench — and it says WHICH piece is missing
#
# ⛔ RUNS ON THE LAPTOP, and the test machine is not needed: the stage is a
#    PipeWire producer inside the bench itself.  ⚠ It does need a **PipeWire
#    listening** on the user's session: without it, `pw_context_connect()`
#    fails and the bench exits **2** instead of stating a false number.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/.." && pwd)
LAVORO=${LAVORO:-/tmp/06-b5-esiti}
CC=${CC:-gcc}

mkdir -p "$LAVORO" || exit 2

# ⛔ Dependencies are ASKED for, and their absence is one line that names the
#    package — not a thirty-line `gcc` error.
for m in libpipewire-0.3 gio-2.0 libdrm; do
	pkg-config --exists "$m" || {
		printf '  ⛔ «%s» is missing: the bench cannot be built.\n' "$m"
		exit 2
	}
done
printf '  --  pipewire %s · glib %s · load %s\n' \
	"$(pkg-config --modversion libpipewire-0.3)" \
	"$(pkg-config --modversion gio-2.0)" \
	"$(cut -d' ' -f1-3 /proc/loadavg)"
pgrep -x pipewire >/dev/null || {
	printf '  ⛔ no `pipewire` listening for this user: the fake stage\n'
	printf '     has nowhere to register, and a red here would not come from the product.\n'
	exit 2
}

$CC -O1 -g -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
    -o "$LAVORO/esiti-cattura" \
    "$QUI/06-b5-esiti-cattura.c" \
    "$ALBERO/src/cattura.c" "$ALBERO/src/registro.c" "$ALBERO/src/cursore.c" \
    $(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm) \
    || { printf '  ⛔ does not compile\n'; exit 2; }

"$LAVORO/esiti-cattura" "${1:-}"
