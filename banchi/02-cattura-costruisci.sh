#!/bin/bash
#
# 02-cattura-costruisci.sh — ⛔ IT RUNS ON THE SERVER (NIC-OS), outside the container.
# It builds the PRODUCT of sub-phase F2.2 (`src/cattura.c`, `src/mutter.c`)
# into the producer of the bench that puts it to the test.
#
#   bash /media/REMOTIX/src/02-cattura-costruisci.sh          builds
#   bash /media/REMOTIX/src/02-cattura-costruisci.sh guarda   just tells
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
# quotes yes, around no.  `FASI.md` §00-ambiente B3.3, paid for **five**
# times — and I avoided the sixth by writing it here instead of remembering it.
#
# ===========================================================================
# ⛔ AND THE COMPILER'S OUTCOME IS LOOKED AT, NOT THE PRESENCE OF THE BINARY AFTERWARDS
#
# `LEZIONI.md` §1.9: a binary from two hours ago answers «I exist» just like one from
# now.  Here the exit status of `gcc` is read, and in addition the
# binary is required to be NEWER than all four sources.
set -uo pipefail

QUI=${QUI:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
PRODOTTO=${PRODOTTO:-$SRC/remotix}          # the product tree, seen from the host
DENTRO_SRC=${DENTRO_SRC:-/srv/src}          # the same, seen from the container
DENTRO_QUI=${DENTRO_QUI:-/srv/remotix/tmp/02-cattura}
BINARIO=$QUI/02-cattura-prodotto
REGISTRO=$QUI/costruzione-prodotto.log

# ⛔ This agent's port is 7512, and no port is opened here.  The
#    line exists anyway: a bench that does not name its own port is a bench
#    that one day takes someone else's.  On 7448 and on 7501 two wanted
#    servers run, and they stay on.
PORTA_DI_QUESTO_BANCO=7512

SORGENTI_PRODOTTO="cattura.c mutter.c registro.c"
SORGENTE_BANCO=02-cattura-prodotto.c

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

log "0. The sources, declared (B0.1: declare AND check)"
mancano=0
for f in $SORGENTI_PRODOTTO cattura.h mutter.h registro.h; do
	if [ -r "$PRODOTTO/$f" ]; then
		ok "$PRODOTTO/$f  ($(md5sum < "$PRODOTTO/$f" | cut -c1-12))"
	else
		ko "⛔ missing $PRODOTTO/$f"
		mancano=$((mancano + 1))
	fi
done
if [ -r "$SRC/$SORGENTE_BANCO" ]; then
	ok "$SRC/$SORGENTE_BANCO  ($(md5sum < "$SRC/$SORGENTE_BANCO" | cut -c1-12))"
else
	ko "⛔ missing $SRC/$SORGENTE_BANCO"
	mancano=$((mancano + 1))
fi
if [ "$mancano" -ne 0 ]; then
	ko "⛔ $mancano sources are missing: I do not build, and I do NOT say it is fine"
	inf "they are brought over with: bash banchi/attrezzi-allinea-prodotto.sh allinea  (from CHUWI)"
	exit 2
fi

if [ "${1:-costruisci}" = guarda ]; then
	log "1. Is the binary there, and is it newer than the sources?"
	if [ ! -x "$BINARIO" ]; then
		ko "⛔ there is no $BINARIO"
		exit 1
	fi
	vecchio=
	for f in $SORGENTI_PRODOTTO cattura.h mutter.h registro.h; do
		[ "$PRODOTTO/$f" -nt "$BINARIO" ] && vecchio="$vecchio $f"
	done
	[ "$SRC/$SORGENTE_BANCO" -nt "$BINARIO" ] && vecchio="$vecchio $SORGENTE_BANCO"
	if [ -n "$vecchio" ]; then
		ko "⛔ the binary is OLDER than:$vecchio"
		inf "measuring now would mean running code different from the code read"
		exit 1
	fi
	ok "the binary is newer than all the sources"
	exit 0
fi

log "1. The build, inside the container"
mkdir -p "$QUI" || exit 2
inf "options: the same as src/Makefile, plus libpipewire-0.3, gio-2.0, libdrm"
# ⛔ No redirection around enter.sh: the log is written INSIDE the
#    quotes, to a file on the server, and it is read back here below.
bash /media/REMOTIX/enter.sh "cd $DENTRO_QUI && \
    gcc -O2 -g -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
        -I$DENTRO_SRC/remotix \
        -o 02-cattura-prodotto \
        $DENTRO_SRC/$SORGENTE_BANCO \
        $DENTRO_SRC/remotix/cattura.c $DENTRO_SRC/remotix/mutter.c \
        $DENTRO_SRC/remotix/registro.c \
        \$(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm) \
        > $DENTRO_QUI/costruzione-prodotto.log 2>&1; \
    echo \"uscita-gcc: \$?\" >> $DENTRO_QUI/costruzione-prodotto.log"
esito_enter=$?

log "2. The COMPILER's outcome, not the presence of the binary"
if [ ! -r "$REGISTRO" ]; then
	ko "⛔ there is no build log ($REGISTRO): enter.sh exited with $esito_enter"
	inf "⚠ and this is NOT «it compiled»: it is «I could not look»"
	exit 2
fi
sed 's/^/       /' "$REGISTRO"
uscita_gcc=$(sed -n 's/^uscita-gcc: //p' "$REGISTRO" | tail -1)
if [ -z "$uscita_gcc" ]; then
	ko "⛔ the log does not carry gcc's exit: I do not know whether it compiled"
	exit 2
fi
if [ "$uscita_gcc" != 0 ]; then
	ko "⛔ gcc exited with $uscita_gcc: I built NOTHING"
	exit 1
fi
if [ ! -x "$BINARIO" ]; then
	ko "⛔ gcc says 0 and the binary is not there: $BINARIO"
	exit 2
fi
ok "gcc exit 0, and the binary is there"
ls -la "$BINARIO"

log "3. The verdict"
ok "⭐ built: $BINARIO"
inf "now the bench is pointed at the PRODUCT like this, and the judge does not change:"
inf "    PROG=$BINARIO FONTE=$SRC/$SORGENTE_BANCO \\"
inf "        bash $SRC/02-cattura-lancia.sh misura"
inf "and the whole certification:"
inf "    PROG=$BINARIO FONTE=$SRC/$SORGENTE_BANCO \\"
inf "        bash $SRC/02-cattura-certifica.sh"
exit 0
