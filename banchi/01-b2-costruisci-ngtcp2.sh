#!/bin/bash
#
# 01-b2-costruisci-ngtcp2.sh — the second candidate of B2.
#
#   bash 01-b2-costruisci-ngtcp2.sh          builds
#   bash 01-b2-costruisci-ngtcp2.sh controlla only says what is already there
#
# ---------------------------------------------------------------------------
# WHY FROM THEIR EXAMPLE AND NOT FROM A BLANK PAGE
#
# B2 must measure **how much glue is left to us**, and that number makes sense
# only if we start where anyone starts: the project's example server.
# Writing everything from scratch would measure our patience, not the library.
#
# ⚠ And for ngtcp2 there is no "minimal fifty-line server": the library
#   is deliberately low level — UDP socket, TLS assembled by hand,
#   connection IDs, retransmission timers — and nghttp3 goes on top of it for
#   HTTP/3.  This is a datum of B2, not a complaint: it is exactly the
#   "how much glue" column of `DECISIONI.md` §6.4.
#
# ---------------------------------------------------------------------------
# THE EXPECTED, DECLARED FIRST (rule B0.4)
#
#   1. nghttp3 compiles                                    -> expected: yes
#   2. ngtcp2 compiles with BoringSSL                      -> expected: yes
#   3. the example server builds                           -> expected: yes
#   4. ⛔ does their example already speak WebTransport?    -> expected: NO
#
# ⛔ Point 4 is the one that counts, and it is written as a prediction: nghttp3
#    implements RFC 9220 (the extended CONNECT of HTTP/3) `[S]`, that is the
#    FOUNDATIONS, and not the WebTransport layer.  If the example already spoke
#    it, the prediction is wrong and why must be written down — which is
#    `LEZIONI.md` §1.11 applied to a reading instead of a measurement.
#
# ⚠ And the BoringSSL already built by `01-b2-costruisci.sh` is reused: two
#   different TLS stacks for two candidates would give two measurements that
#   cannot be compared, which is the reason `provision-server.sh` and
#   `provision-vm.sh` have the same list.
# ---------------------------------------------------------------------------
set -uo pipefail

SRC=/srv/src/b2
BSSL="$SRC/boringssl"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-costruisci}

log "Starting state"
inf "sources   $SRC"
for d in boringssl nghttp3 ngtcp2; do
	[ -d "$SRC/$d" ] && inf "$d: cloned" || inf "$d: to be cloned"
done
if [ ! -f "$BSSL/build/libssl.a" ]; then
	ko "BoringSSL is not built: run 01-b2-costruisci.sh first"
	exit 2
fi
ok "BoringSSL reused from lsquic (same TLS stack for all candidates)"

[ "$AZIONE" = controlla ] && exit 0

# ---------------------------------------------------------------------------
# 1. nghttp3 — HTTP/3, that is the half that brings the extended CONNECT
# ---------------------------------------------------------------------------
log "nghttp3"
if [ ! -d "$SRC/nghttp3" ]; then
	git clone --depth 1 --recursive https://github.com/ngtcp2/nghttp3 "$SRC/nghttp3" \
		|| { ko "clone failed"; exit 3; }
fi
if [ ! -f "$SRC/nghttp3/build/lib/libnghttp3.a" ]; then
	cmake -B "$SRC/nghttp3/build" -S "$SRC/nghttp3" -GNinja \
		-DCMAKE_BUILD_TYPE=Release -DENABLE_LIB_ONLY=ON -DENABLE_STATIC_LIB=ON \
		|| { ko "cmake failed"; exit 3; }
	ninja -C "$SRC/nghttp3/build" || { ko "build failed"; exit 3; }
fi
NGH=$(find "$SRC/nghttp3/build" -name 'libnghttp3.a' | head -1)
[ -n "$NGH" ] && ok "libnghttp3.a built" || { ko "libnghttp3.a absent"; exit 3; }
inf "version $(cd "$SRC/nghttp3" && git describe --tags 2>/dev/null || echo '(no tag)')"

# ---------------------------------------------------------------------------
# 2. ngtcp2 — the QUIC
# ---------------------------------------------------------------------------
log "ngtcp2 with BoringSSL"
if [ ! -d "$SRC/ngtcp2" ]; then
	git clone --depth 1 --recursive https://github.com/ngtcp2/ngtcp2 "$SRC/ngtcp2" \
		|| { ko "clone failed"; exit 4; }
fi
inf "version $(cd "$SRC/ngtcp2" && git describe --tags 2>/dev/null || echo '(no tag)')"

if [ ! -f "$SRC/ngtcp2/build/lib/libngtcp2.a" ]; then
	cmake -B "$SRC/ngtcp2/build" -S "$SRC/ngtcp2" -GNinja \
		-DCMAKE_BUILD_TYPE=Release \
		-DENABLE_STATIC_LIB=ON -DENABLE_SHARED_LIB=OFF \
		-DENABLE_BORINGSSL=ON \
		-DBORINGSSL_INCLUDE_DIR="$BSSL/include" \
		-DBORINGSSL_LIBRARIES="$BSSL/build/libssl.a;$BSSL/build/libcrypto.a" \
		|| { ko "cmake failed"; exit 4; }
	ninja -C "$SRC/ngtcp2/build" || { ko "build failed"; exit 4; }
fi
NGT=$(find "$SRC/ngtcp2/build" -name 'libngtcp2.a' | head -1)
[ -n "$NGT" ] && ok "libngtcp2.a built" || { ko "libngtcp2.a absent"; exit 4; }

# ---------------------------------------------------------------------------
# 3. ⛔ THE CHECK THAT COUNTS: does their example speak WebTransport?
#
# Not "it compiles": what it can do.  We look for the three things without which
# a WebTransport session is not born, and say how many are found.
# ---------------------------------------------------------------------------
log "The check: how much WebTransport is already there"
inf "expected: NONE — nghttp3 brings the extended CONNECT (RFC 9220), not the WT layer"

# ⛔ THREE DEFECTS IN NINE LINES, ON 9 AUG 2026, AND ALL OF THE SAME
#    FAMILY: the bench said ZERO where it had not LOOKED.
#
#    1. the two trees were passed as ONE string — `"$SRC/ngtcp2 $SRC/nghttp3"`
#       — so grep received a single path, with a space inside, that does not
#       exist.  Zero results;
#    2. `2>/dev/null` hid the "No such file or directory" that would have
#       said so at once.  ⛔ It is precisely what `REVIEWER.md` §1 point 4
#       orders us to reject;
#    3. the diagnostic `printf` ended up inside `$(...)`, so it vanished from
#       the terminal: the bench did not even show what it was looking for.
#
#    Result: "no trace of SETTINGS_WT_MAX_SESSIONS: the prediction
#    holds" — a GREEN printed by a search never executed.
#
# ⭐ The cure is not fixing the grep: it is that the bench SAYS WHAT IT
#    LOOKED AT.  A count without its denominator is not a measurement.
ALBERI=("$SRC/ngtcp2" "$SRC/nghttp3")
for a in "${ALBERI[@]}"; do
	if [ ! -d "$a" ]; then
		ko "the tree $a does not exist: the search cannot be done"
		exit 5
	fi
done
FILE_TOT=$(find "${ALBERI[@]}" \( -name '*.c' -o -name '*.h' -o -name '*.cc' -o -name '*.hh' \) | wc -l)
inf "looking inside $FILE_TOT files of ${#ALBERI[@]} trees"
if [ "$FILE_TOT" -lt 100 ]; then
	ko "only $FILE_TOT files: the search is looking in the wrong place"
	exit 5
fi

cerca()
{
	local etichetta=$1 modello=$2
	local n
	# ⚠ No `2>/dev/null`: if grep complains, it must be seen.
	n=$(grep -rIl --include='*.c' --include='*.h' --include='*.cc' --include='*.hh' \
		-e "$modello" "${ALBERI[@]}" | wc -l)
	printf '    --  %-34s %s files\n' "$etichetta" "$n" >&2
	echo "$n"
}

N1=$(cerca "SETTINGS_WT_MAX_SESSIONS (0xc671706a)" "c671706a")
N2=$(cerca "the token 'webtransport'"              "webtransport")
N3=$(cerca "the extended CONNECT (:protocol)"      "ENABLE_CONNECT_PROTOCOL\|:protocol")

# ⛔ AND THE POSITIVE CONTROL OF THE SEARCH ITSELF: we look for something that
#    MUST be there.  If this too gives zero, it is not the library that is
#    missing: it is the grep that is not reading anything, and that is the
#    error this box tells about.
CTRL=$(cerca "control: the word 'nghttp3'"         "nghttp3")
if [ "$CTRL" -eq 0 ]; then
	ko "⛔ the positive control of the search FAILED: zero files name 'nghttp3'"
	ko "   the search is not looking at anything. No number below is valid."
	exit 5
fi
ok "positive control of the search: 'nghttp3' found in $CTRL files"

printf '\n'
log "Outcome"
if [ "$N1" -eq 0 ]; then
	ok "no trace of SETTINGS_WT_MAX_SESSIONS: the prediction holds"
	inf "⇒ we write the WebTransport layer ourselves, and the lines are COUNTED"
else
	ko "⛔ the prediction is WRONG: SETTINGS_WT_MAX_SESSIONS is in $N1 files"
	inf "why must be reread, before writing one line of glue"
fi
inf "extended CONNECT present in $N3 files — it is the foundations, not the layer"
exit 0
