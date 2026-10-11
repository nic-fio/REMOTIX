#!/bin/bash
#
# 02-codifica-costruisci.sh — builds the encoder ON ITS OWN, and the tool
# with which the bench points at it.
#
#   bash banchi/02-codifica-costruisci.sh              builds
#   bash banchi/02-codifica-costruisci.sh deps   says what is missing
#
# Exits **0** if it built, **1** if compilation failed, **2** if it could not
# even try (dependencies).  ⛔ Three outcomes, not two.
#
# ===========================================================================
# ⛔ WHY `src/Makefile` IS NOT USED
#
# On 12 Aug 2026 four agents write four links of phase 2 in
# parallel.  `src/Makefile` and `src/main.c` belong to everybody and nobody: whoever
# writes in them overwrites the others' work, and the symptom would reach
# someone else.  ⇒ This script compiles **only** `codificatore.c`, and the exact
# lines for the Makefile and for `main.c` are in the report
# `fasi/rapporti/P2-3-codifica.md`, to be applied when the four links are
# stitched back together.
#
# ===========================================================================
# ⛔ THE DEPENDENCIES, DECLARED
#
#   libavcodec-dev   >= 61   the encoder, asked for BY NAME (libx265/libsvtav1)
#   libavutil-dev    >= 59   frames and pixel formats
#   libswscale-dev   >= 8    ⭐ NEW in this sub-phase: BGRx (what
#                            the GNOME capture delivers, `[M]` F2.2) →
#                            yuv420p10le.  `CODER.md` §4.1: of RGB→YUV there is
#                            ONE standard implementation, and writing our own
#                            would be a component to maintain forever
#                            — moreover slower than the one with
#                            vector instructions, on a path where v1 had
#                            already measured the bottleneck (12.5 ms).
#
# On Debian Trixie: `apt install libavcodec-dev libavutil-dev libswscale-dev`.
# ⚠ All three from the `ffmpeg` source package 7:7.1.5-0+deb13u1, that is the
#   SAME version of the `ffmpeg` the bench uses as independent reader.
#
# ⛔ And NOTHING from outside the packages: it is the lesson of `quiche`, discarded
#    also because it required a Rust toolchain outside the packages
#    (`DECISIONI.md` §6.4).
#
# ⚠ If `libswscale-dev` is not installed and there is no `root`, this script can
#   download the official Trixie archive and unpack it into a working
#   folder: `BORROW=1 bash banchi/02-codifica-costruisci.sh`.  ⛔ It is a
#   declared LOAN, not a hidden dependency — the library that gets linked
#   stays the system one (`libswscale.so.8`), only the headers
#   are taken.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
SRC=$HERE/../src
WORKDIR=${WORK_BUILD:-/tmp/02-codifica-costruisci}
CC=${CC:-cc}
BORROW=${BORROW:-0}
LDFLAGS_LOAN=""

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

mkdir -p "$WORKDIR" || { ko "cannot create $WORKDIR"; exit 2; }

# ───────────────────────────────────────────────────────────────────────────
# The three dependencies, asked of `pkg-config` and not guessed.
CFLAGS_AV=""
MISSING=""
for P in libavcodec libavutil libswscale libdrm libva; do
	if V=$(pkg-config --modversion "$P" 2>/dev/null); then
		ok "$P $V"
		CFLAGS_AV="$CFLAGS_AV $(pkg-config --cflags "$P")"
	else
		ko "missing $P (package ${P}-dev)"
		MISSING="$MISSING $P"
	fi
done

# ⚠ The loan of only the libswscale headers, when there is no root.
if [ -n "$MISSING" ] && [ "$BORROW" = 1 ]; then
	inf "BORROW=1: downloading the headers from the official Trixie packages"
	for P in $MISSING; do
		( cd "$WORKDIR" && apt-get download "${P}-dev" ) > "$WORKDIR/scarica.log" 2>&1 || {
			ko "could not download ${P}-dev — see $WORKDIR/scarica.log"; exit 2; }
		DEB=$(ls "$WORKDIR"/${P}-dev_*.deb 2>/dev/null | head -1)
		[ -n "$DEB" ] || { ko "no ${P}-dev archive"; exit 2; }
		dpkg -x "$DEB" "$WORKDIR/prestito" || { ko "cannot unpack $DEB"; exit 2; }
		# ⛔ The library that gets LINKED stays the system one: only the
		#    unversioned name the linker looks for (`-lswscale`) is made.  ⚠ If
		#    the archive's one were linked, it would build against a library
		#    that does not run on the machine — two versions under the same label.
		REAL_SO=$(ls /usr/lib/"$(uname -m)"-linux-gnu/${P}.so.* 2>/dev/null | head -1)
		if [ -z "$REAL_SO" ]; then
			ko "⛔ $P is not installed even as a runtime library"; exit 2
		fi
		mkdir -p "$WORKDIR/prestito/collega"
		ln -sf "$REAL_SO" "$WORKDIR/prestito/collega/${P}.so"
		ok "headers of $P on loan from $(basename "$DEB"); linking $REAL_SO"
	done
	CFLAGS_AV="$CFLAGS_AV -I$WORKDIR/prestito/usr/include/$(uname -m)-linux-gnu -I$WORKDIR/prestito/usr/include"
	LDFLAGS_LOAN="-L$WORKDIR/prestito/collega"
	MISSING=""
fi

if [ -n "$MISSING" ]; then
	ko "⛔ I could not even try to compile: missing$MISSING"
	inf "cure:  sudo apt install libavcodec-dev libavutil-dev libswscale-dev"
	inf "or without root:  BORROW=1 bash banchi/02-codifica-costruisci.sh"
	exit 2
fi

if [ "${1:-}" = deps ]; then
	ok "all three dependencies are there"
	exit 0
fi

# ───────────────────────────────────────────────────────────────────────────
# ⚠ `registro.c` goes in because `codificatore.c` writes to the log instead of
#   to `stderr`: every fallback and every degradation **is declared there**
#   (`CODER.md` §6), and a log scattered over twenty `fprintf`s has neither instant
#   nor area.
WARNINGS="-Wall -Wextra -Wno-unused-parameter"
CFLAGS_ALL="-O2 -g -std=gnu11 -D_GNU_SOURCE $WARNINGS $CFLAGS_AV"
LIBS="-lavcodec -lavutil -lswscale -lva"

printf '\n\033[1m== compiling the encoder\033[0m\n'
if ! $CC $CFLAGS_ALL -c -o "$WORKDIR/codificatore.o" "$SRC/codificatore.c" 2> "$WORKDIR/cc.log"; then
	ko "⛔ codificatore.c does not compile"
	cat "$WORKDIR/cc.log"
	exit 1
fi
if [ -s "$WORKDIR/cc.log" ]; then
	# ⛔ The warnings are printed.  A warning nobody reads is a
	#    defect waiting.
	inf "compiler warnings:"
	cat "$WORKDIR/cc.log"
fi
ok "codificatore.o"

if ! $CC $CFLAGS_ALL -c -o "$WORKDIR/registro.o" "$SRC/registro.c" 2>> "$WORKDIR/cc.log"; then
	ko "⛔ registro.c does not compile"; cat "$WORKDIR/cc.log"; exit 1
fi
ok "registro.o"

printf '\n\033[1m== building the tool with which the bench points at the product\033[0m\n'
if ! $CC $CFLAGS_ALL -o "$HERE/02-codifica-prova" "$HERE/02-codifica-prova.c" \
	"$WORKDIR/codificatore.o" "$WORKDIR/registro.o" $LDFLAGS_LOAN $LIBS 2>> "$WORKDIR/cc.log"; then
	ko "⛔ 02-codifica-prova was not built"
	cat "$WORKDIR/cc.log"
	exit 1
fi
ok "banchi/02-codifica-prova"
inf "now:  ENCODER=product bash banchi/02-codifica-lancia.sh"
exit 0
