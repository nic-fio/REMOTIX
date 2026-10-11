#!/bin/bash
#
# 02-capture-build.sh — ⛔ IT RUNS ON THE SERVER (NIC-OS), outside the container.
# It builds the PRODUCT of sub-phase F2.2 (`src/capture.c`, `src/mutter.c`)
# into the producer of the bench that puts it to the test.
#
#   bash /media/REMOTIX/src/02-capture-build.sh          builds
#   bash /media/REMOTIX/src/02-capture-build.sh look   just tells
#
# ===========================================================================
# ⛔ WHY THE PRODUCT'S `Makefile` IS NOT USED
#
# `src/Makefile` builds **a single binary** — the server — and in phase 2 the
# server does not yet call capture: the lines that will put it there are in the
# report `P2-2-cattura.md`, and the coordinator grafts them in.  ⛔ Four agents
# are writing the other links right now, and two touching the same
# `Makefile` would erase each other.
#
# ⇒ This file builds **the same sources** with **the same options** as the
#   `Makefile` (`-std=gnu11 -D_GNU_SOURCE -Wall -Wextra`), plus the three libraries
#   capture brings with it.  Whoever grafts the lines into the `Makefile` will not
#   discover that the code does not compile: here it is already compiled with its rules.
#
# ===========================================================================
# ⛔ NEVER A REDIRECTION **AROUND** `enter.sh`
#
# `sudo`'s password prompt goes to stderr, and a redirection
# swallows it: the command hangs forever, silently.  Inside the
# quotes yes, around no.  `PHASES.md` §00-ambiente B3.3, paid for **five**
# times — and I avoided the sixth by writing it here instead of remembering it.
#
# ===========================================================================
# ⛔ AND THE COMPILER'S OUTCOME IS LOOKED AT, NOT THE PRESENCE OF THE BINARY AFTERWARDS
#
# `LESSONS.md` §1.9: a binary from two hours ago answers «I exist» just like one from
# now.  Here the exit status of `gcc` is read, and in addition the
# binary is required to be NEWER than all four sources.
set -uo pipefail

HERE=${HERE:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
PRODUCT=${PRODUCT:-$SRC/remotix}          # the product tree, seen from the host
INSIDE_SRC=${INSIDE_SRC:-/srv/src}          # the same, seen from the container
INSIDE_HERE=${INSIDE_HERE:-/srv/remotix/tmp/02-cattura}
BINARY=$HERE/02-capture-product
LOG=$HERE/costruzione-prodotto.log

# ⛔ This agent's port is 7512, and no port is opened here.  The
#    line exists anyway: a bench that does not name its own port is a bench
#    that one day takes someone else's.  On 7448 and on 7501 two wanted
#    servers run, and they stay on.
THIS_BENCH_PORT=7512

PRODUCT_SOURCES="capture.c mutter.c log.c"
BENCH_SOURCE=02-capture-product.c

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

log "0. The sources, declared (B0.1: declare AND check)"
missing=0
for f in $PRODUCT_SOURCES capture.h mutter.h log.h; do
	if [ -r "$PRODUCT/$f" ]; then
		ok "$PRODUCT/$f  ($(md5sum < "$PRODUCT/$f" | cut -c1-12))"
	else
		ko "⛔ missing $PRODUCT/$f"
		missing=$((missing + 1))
	fi
done
if [ -r "$SRC/$BENCH_SOURCE" ]; then
	ok "$SRC/$BENCH_SOURCE  ($(md5sum < "$SRC/$BENCH_SOURCE" | cut -c1-12))"
else
	ko "⛔ missing $SRC/$BENCH_SOURCE"
	missing=$((missing + 1))
fi
if [ "$missing" -ne 0 ]; then
	ko "⛔ $missing sources are missing: I do not build, and I do NOT say it is fine"
	inf "they are brought over with: bash benches/tools-align-product.sh align  (from CHUWI)"
	exit 2
fi

if [ "${1:-costruisci}" = guarda ]; then
	log "1. Is the binary there, and is it newer than the sources?"
	if [ ! -x "$BINARY" ]; then
		ko "⛔ there is no $BINARY"
		exit 1
	fi
	old=
	for f in $PRODUCT_SOURCES capture.h mutter.h log.h; do
		[ "$PRODUCT/$f" -nt "$BINARY" ] && old="$old $f"
	done
	[ "$SRC/$BENCH_SOURCE" -nt "$BINARY" ] && old="$old $BENCH_SOURCE"
	if [ -n "$old" ]; then
		ko "⛔ the binary is OLDER than:$old"
		inf "measuring now would mean running code different from the code read"
		exit 1
	fi
	ok "the binary is newer than all the sources"
	exit 0
fi

log "1. The build, inside the container"
mkdir -p "$HERE" || exit 2
inf "options: the same as src/Makefile, plus libpipewire-0.3, gio-2.0, libdrm"
# ⛔ No redirection around enter.sh: the log is written INSIDE the
#    quotes, to a file on the server, and it is read back here below.
bash /media/REMOTIX/enter.sh "cd $INSIDE_HERE && \
    gcc -O2 -g -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
        -I$INSIDE_SRC/remotix \
        -o 02-capture-product \
        $INSIDE_SRC/$BENCH_SOURCE \
        $INSIDE_SRC/remotix/capture.c $INSIDE_SRC/remotix/mutter.c \
        $INSIDE_SRC/remotix/log.c \
        \$(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm) \
        > $INSIDE_HERE/costruzione-prodotto.log 2>&1; \
    echo \"uscita-gcc: \$?\" >> $INSIDE_HERE/costruzione-prodotto.log"
outcome_enter=$?

log "2. The COMPILER's outcome, not the presence of the binary"
if [ ! -r "$LOG" ]; then
	ko "⛔ there is no build log ($LOG): enter.sh exited with $outcome_enter"
	inf "⚠ and this is NOT «it compiled»: it is «I could not look»"
	exit 2
fi
sed 's/^/       /' "$LOG"
output_gcc=$(sed -n 's/^uscita-gcc: //p' "$LOG" | tail -1)
if [ -z "$output_gcc" ]; then
	ko "⛔ the log does not carry gcc's exit: I do not know whether it compiled"
	exit 2
fi
if [ "$output_gcc" != 0 ]; then
	ko "⛔ gcc exited with $output_gcc: I built NOTHING"
	exit 1
fi
if [ ! -x "$BINARY" ]; then
	ko "⛔ gcc says 0 and the binary is not there: $BINARY"
	exit 2
fi
ok "gcc exit 0, and the binary is there"
ls -la "$BINARY"

log "3. The verdict"
ok "⭐ built: $BINARY"
inf "now the bench is pointed at the PRODUCT like this, and the judge does not change:"
inf "    PROG=$BINARY SOURCE=$SRC/$BENCH_SOURCE \\"
inf "        bash $SRC/02-capture-launch.sh measure"
inf "and the whole certification:"
inf "    PROG=$BINARY SOURCE=$SRC/$BENCH_SOURCE \\"
inf "        bash $SRC/02-capture-certify.sh"
exit 0
