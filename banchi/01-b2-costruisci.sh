#!/bin/bash
#
# 01-b2-costruisci.sh — builds the candidates of bench B2 of phase 1.
#
#   bash 01-b2-costruisci.sh lsquic     BoringSSL + lsquic with WebTransport
#   bash 01-b2-costruisci.sh controlla  only says what is already there
#
# ---------------------------------------------------------------------------
# WHAT IT DECIDES, AND WHY READING IS NOT ENOUGH
#
# `DECISIONI.md` §6.4 chooses the QUIC library, and the criterion changed on
# 9 Aug 2026: speaking QUIC is not enough, it must bring HTTP/3 and WebTransport
# ON THE SERVER SIDE.  The survey of the night of the 9th read the four
# candidates and established that:
#
#   - `quiche` and `ngtcp2+nghttp3` give the FOUNDATIONS (extended CONNECT,
#     datagram, capsule) and not the WebTransport layer;
#   - `lsquic` has `OPTION(LSQUIC_WEBTRANSPORT ... OFF)` in the CMakeLists [R],
#     ⛔ but in the public header it exposes ONLY two settings and four
#     stream classification functions — no session API, no opening of WT
#     streams, no WT datagram.
#
# ⛔ It is exactly E1 — necessary taken for sufficient.  A build flag called
#    WEBTRANSPORT_SERVER_SUPPORT does not say that the server does WebTransport:
#    it says that someone wrote some code behind that name.  How much it does
#    is MEASURED, and this script prepares the measurement.
#
# ⚠ And a detail that counts as a clue, not as proof: the comment of
#   `es_webtransport_server` in the header says "Enable datagram extension
#   for http3 server" — that is, it documents ANOTHER thing.  A field whose
#   documentation talks about something else is a field nobody has reread.
#
# ---------------------------------------------------------------------------
# THE EXPECTED, DECLARED FIRST (rule B0.4 of `FASI.md` §01-filo-nudo)
#
#   1. BoringSSL compiles                                  -> expected: yes
#   2. lsquic compiles WITH -DLSQUIC_WEBTRANSPORT=ON        -> expected: yes
#   3. the four WT symbols are in the produced library      -> expected: 4 of 4
#
# ⛔ Point 3 is the check that makes the first two credible: a library that
#    compiles "with the flag" and does not contain the symbols is a library in
#    which the flag did nothing — and the first to find out would have been
#    whoever writes the server, three days later.
# ---------------------------------------------------------------------------
set -uo pipefail

SRC=/srv/src/b2
# ⚠ No `-b <branch>`: the repository's default branch is taken.  The first
#   round of 9 Aug 2026 asked BoringSSL for `master` and failed with "Remote
#   branch master not found" — Google renamed it.  A branch written by hand
#   in a script is a dependency on someone else's name.
#
# ⛔ And the failure arrived with "exit 0" on the terminal of whoever was
#    watching, because the remote command was piped into `tail`: the exit
#    status was that of `tail`.  It is `LEZIONI.md` §1.9 — zero and failure
#    with the same face — caught in the INVOCATION instead of in the script.
#    Whoever launches this bench must not put a `| tail` after it without `PIPESTATUS`.

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-lsquic}

mkdir -p "$SRC" || exit 2
cd "$SRC" || exit 2

# ---------------------------------------------------------------------------
# 0. What is already there
# ---------------------------------------------------------------------------
log "Starting state"
inf "go       $(go version 2>/dev/null || echo MISSING)"
inf "cmake    $(cmake --version 2>/dev/null | head -1 || echo MISSING)"
inf "gcc      $(gcc -dumpversion 2>/dev/null || echo MISSING)"
inf "sources  $SRC"
[ -d "$SRC/boringssl" ] && inf "boringssl already cloned" || inf "boringssl to be cloned"
[ -d "$SRC/lsquic" ]    && inf "lsquic already cloned"    || inf "lsquic to be cloned"

if [ "$AZIONE" = controlla ]; then
	exit 0
fi

# ---------------------------------------------------------------------------
# 1. BoringSSL
#
# ⚠ lsquic does not talk to OpenSSL: it wants BoringSSL, and BoringSSL is built
#   with Go.  That is the reason `golang-go` entered `provision.sh`.
# ---------------------------------------------------------------------------
log "BoringSSL"
if [ ! -d "$SRC/boringssl" ]; then
	git clone --depth 1 https://boringssl.googlesource.com/boringssl "$SRC/boringssl" \
		|| { ko "clone failed"; exit 3; }
fi
if [ ! -f "$SRC/boringssl/build/libssl.a" ] && [ ! -f "$SRC/boringssl/build/ssl/libssl.a" ]; then
	cmake -B "$SRC/boringssl/build" -S "$SRC/boringssl" -GNinja -DCMAKE_BUILD_TYPE=Release \
		|| { ko "cmake failed"; exit 3; }
	ninja -C "$SRC/boringssl/build" ssl crypto || { ko "build failed"; exit 3; }
fi
BSSL_SSL=$(find "$SRC/boringssl/build" -name libssl.a | head -1)
BSSL_CRY=$(find "$SRC/boringssl/build" -name libcrypto.a | head -1)
if [ -n "$BSSL_SSL" ] && [ -n "$BSSL_CRY" ]; then
	ok "libssl.a and libcrypto.a built"
else
	ko "the BoringSSL libraries are not there"
	exit 3
fi

# ---------------------------------------------------------------------------
# 2. lsquic, WITH the flag
# ---------------------------------------------------------------------------
log "lsquic with LSQUIC_WEBTRANSPORT=ON"
if [ ! -d "$SRC/lsquic" ]; then
	git clone --depth 1 --recursive https://github.com/litespeedtech/lsquic "$SRC/lsquic" \
		|| { ko "clone failed"; exit 4; }
fi
inf "version $(cd "$SRC/lsquic" && git describe --tags 2>/dev/null || echo '(no tag)')"

cmake -B "$SRC/lsquic/build" -S "$SRC/lsquic" -GNinja \
	-DCMAKE_BUILD_TYPE=Release \
	-DLSQUIC_WEBTRANSPORT=ON \
	-DBORINGSSL_DIR="$SRC/boringssl" \
	-DBORINGSSL_LIB_ssl="$BSSL_SSL" \
	-DBORINGSSL_LIB_crypto="$BSSL_CRY" \
	-DBORINGSSL_INCLUDE="$SRC/boringssl/include" \
	-DLSQUIC_TESTS=OFF \
	|| { ko "cmake failed"; exit 4; }
ninja -C "$SRC/lsquic/build" lsquic || { ko "build failed"; exit 4; }
# ⭐ And the example programs, which are the cheapest way to have a REAL
#    HTTP/3 server to point a real browser at.  They want libevent: without
#    it, cmake warns "binaries won't be built" and carries on — that is, the
#    bench would be left without the piece it needs, and with exit zero.
if ninja -C "$SRC/lsquic/build" http_server 2>/dev/null; then
	ok "example http_server built"
else
	inf "http_server not built (libevent missing?) — does not block the check"
fi
LIB=$(find "$SRC/lsquic/build" -name 'liblsquic.a' | head -1)
[ -n "$LIB" ] && ok "liblsquic.a built" || { ko "liblsquic.a not found"; exit 4; }

# ---------------------------------------------------------------------------
# 3. ⛔ THE CHECK: did the flag produce anything?
#
# Not "it compiles", not "the flag is accepted": the SYMBOLS.  An ignored flag
# produces a library identical to the one without the flag, and no message.
# ---------------------------------------------------------------------------
log "The check: the WebTransport symbols inside the library"
# ⛔ The bench declares WHAT it is looking at, and how many it sees in all,
#    before saying which are missing.  The first round of 9 Aug 2026 said
#    "0 of 4" while a hand reading on the same archive showed 4:
#    without these three lines there was no way of knowing which of the two was lying.
inf "archive $LIB"
inf "bytes   $(stat -c %s "$LIB" 2>/dev/null || echo '?')"
inf "symbols naming webtransport, at a glance: $(nm -g --defined-only "$LIB" 2>/dev/null | grep -ci webtransport)"
nm -g --defined-only "$LIB" 2>/dev/null | grep -i webtransport | sed 's/^/        /' | head -8
ATTESI=(
	lsquic_stream_set_webtransport_session
	lsquic_stream_is_webtransport_session
	lsquic_stream_is_webtransport_client_bidi_stream
	lsquic_stream_get_webtransport_session_stream_id
)
# ⛔ The symbols are read ONCE and searched in a string, not in a pipe.
#
#    The first round of 9 Aug 2026 did `nm ... | grep -q " $s$"` and said
#    **0 of 4** while the four symbols were in the archive — it printed them
#    itself three lines above.  The cause: `set -o pipefail` at the top, and
#    `grep -q` exiting at the FIRST match, closing the pipe.  `nm` is still
#    writing, gets SIGPIPE, dies with 141 — and `pipefail` makes that 141 the
#    outcome of the pipeline.  ⛔ **The successful match was read as failure**:
#    the easier the symbol was to find, the sooner grep exited, the surer the
#    false red.
#
#    It is `LEZIONI.md` §2.3 — a test that fails the right code costs as much
#    as one that passes the wrong one — in the same family as the scroll wheel
#    bench.  Here it would have struck off the best candidate of `DECISIONI.md`
#    §6.4 with a false [M] against an [R].
SIMBOLI=$(nm -g --defined-only "$LIB" 2>/dev/null)
TROVATI=0
for s in "${ATTESI[@]}"; do
	if grep -q " $s\$" <<<"$SIMBOLI"; then
		ok "$s"
		TROVATI=$((TROVATI + 1))
	else
		ko "$s  — absent"
	fi
done

printf '\n'
log "Outcome"
inf "expected:  4 symbols of 4"
inf "found:     $TROVATI of 4"
if [ "$TROVATI" -eq 4 ]; then
	ok "the flag produced code: we can move on to the real session"
	exit 0
else
	ko "the flag did NOT produce what it declares"
	printf '\n    ⛔ And this is the case in which the bench is worth more than anything:\n'
	printf '       the library compiles, the flag is accepted, and the code is not there.\n'
	exit 1
fi
