#!/usr/bin/env bash
# ===========================================================================
# 09-b81-terreno — the ground of the bench of the TWO NEW CURES (agent NR6)
#
#   port 7960 · user `provanr6` (uid 1060) · tree /media/REMOTIX/src/09nr6-src
#   work /media/REMOTIX/tmp/09nr6 · unit remotix-7960
#   ⭐ and a SECOND user, `provanr6b` (uid 1061): it serves test 5, «two
#      different users do not evict each other», which cannot be stated without it.
#
# ⛔ IT DOES NOT REWRITE `07-b64-terreno.sh`: it passes it MY environment and calls it.
#    Only two steps are done on its own, and each has its reason:
#
# ⛔⛔⭐ 1. THE SOURCES ARE TAKEN FROM THE WORKING TREE, **NOT** from `git
#          archive HEAD` — and it is the exact opposite of `09-b76-terreno.sh`.
#
#          The reason is the target: tonight's two cures — the DEAD LINE
#          (`webtransport.c`, `trasporto.c`) and the GHOST EVICTION
#          (`rcp.c`) — **are not committed**.  `git archive HEAD` would send
#          yesterday's product, the bench would run just fine, and every predicate
#          would say «the cure did not fire» on a binary that does not have
#          the cure.  ⚠ It is the D5 form in its worst version: not a stale
#          binary that stays green, but a stale binary that passes off as
#          MEASURED a cure that never ran.
#
#          ⇒ The working tree is sent, and the `md5` of what
#            was sent and of what came out of it is DECLARED: without the two fingerprints
#            this number cannot be reproduced by anyone.
#          ⚠ And `*.o` and `src/remotix` are excluded: if they were sent, `make` would find
#            everything up to date and the laptop's binary would remain.
#
# ⛔ 2. THE SECOND USER.  `07-b64-terreno.sh username` can make only one and
#      writes its password in `$LAV/password`; the second ends up in
#      `$LAV/password2`, so the two cannot swap places.
#
# ⛔ And `banchi/01-b4-validatore.py` is carried too: it is the REFEREE of the
#    §11.1 format and the trace reader looks for it inside the tree.
#
# Usage (from the laptop):
#     bash banchi/09-b81-terreno.sh port      # working tree + build + md5
#     bash banchi/09-b81-terreno.sh username     # provanr6 and provanr6b
#     bash banchi/09-b81-terreno.sh turn_on    # SERVER_OPTIONS='...' for the cures
#     bash banchi/09-b81-terreno.sh state
#     bash banchi/09-b81-terreno.sh turn_off
# ===========================================================================
set -uo pipefail

MACHINE=${MACHINE:-nicfio@192.168.0.2}
SUDO_PASSWORD=${SUDO_PASSWORD:-nicfio}
export MACHINE SUDO_PASSWORD
export ADDR=${ADDR:-192.168.0.2}
export PORT=${PORT:-7960}
export ACCOUNT=${ACCOUNT:-provanr6}
export UID_B=${UID_B:-1060}
export USER_PASSWORD=${USER_PASSWORD:-nr6-cure-nuove-2026}
export USER2=${USER2:-provanr6b}
export UID_B2=${UID_B2:-1061}
export USER2_PASSWORD=${USER2_PASSWORD:-nr6b-secondo-utente-2026}
export TREE=${TREE:-/media/REMOTIX/src/09nr6-src}
export LAV=${LAV:-/media/REMOTIX/tmp/09nr6}
export INSIDE_TREE=${INSIDE_TREE:-/srv/src/09nr6-src}
export INSIDE_WORK=${INSIDE_WORK:-/srv/remotix/tmp/09nr6}
export UNIT=${UNIT:-remotix-$PORT}

HERE=$(cd "$(dirname "$0")/.." && pwd)
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE CARD GROUPS ARE GIVEN IN ONE PLACE ONLY — `attrezzi-gruppi-scheda.sh`
#
# ⛔ Here there was `usermod -aG render,video` (or nothing at all), with the NAMES
#    HARD-CODED and without reading back: two defects in a single line.  The reason
#    why the cure lives in a separate file, and the numbers that justify it,
#    are in the box at the top of that file — ⛔ they are not copied here, or
#    they become ten places to diverge from (`LEZIONI.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
CARD_GROUPS_SH=${CARD_GROUPS_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$CARD_GROUPS_SH" ] || { ko "⛔ $CARD_GROUPS_SH is missing: without it, the tenant would be born BLIND"; exit 2; }
. "$CARD_GROUPS_SH"


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS ON THE TEST MACHINE, AS ROOT — and it does one step only
# ═══════════════════════════════════════════════════════════════════════════
if [ "${1:-}" = "--sul-server" ]; then
	[ "$(id -u)" -eq 0 ] || { ko "⛔ «--sul-server» must be run AS ROOT"; exit 2; }
	case "${2:-}" in
	user2)
		log "The SECOND bench user: $USER2 (uid $UID_B2)"
		mkdir -p "$LAV" 2>/dev/null
		if id "$USER2" >/dev/null 2>&1; then
			ok "already there — I do not redo it"
		else
			useradd -m -u "$UID_B2" -s /bin/bash "$USER2" || {
				ko "⛔ useradd did not succeed"; exit 2; }
			ok "created"
		fi
		# ⛔ D12: the password in a 0600 file, never in argv.
		( umask 077; printf '%s:%s\n' "$USER2" "$USER2_PASSWORD" > "$LAV/.chp2" )
		chmod 600 "$LAV/.chp2"
		chpasswd < "$LAV/.chp2" || { ko "⛔ chpasswd failed"; rm -f "$LAV/.chp2"; exit 2; }
		rm -f "$LAV/.chp2"
		ok "password set (from stdin, never in argv — D12)"
		# ⛔ Here there were the two HARD-CODED names and no reading back.
		card_groups_give_to "$USER2" || exit 3
		ok "groups: $(id -nG "$USER2")"
		loginctl enable-linger "$USER2" || { ko "⛔ enable-linger failed"; exit 2; }
		ok "linger on: /run/user/$UID_B2 will live even with nobody connected"
		# ⛔ In a SEPARATE file: if it went into `$LAV/password` test 5 would open
		#    two sessions of the SAME user believing it had opened two of
		#    different users — that is, it would measure test 4 and call it 5.
		( umask 077; printf '%s\n' "$USER2_PASSWORD" > "$LAV/password2" )
		chmod 600 "$LAV/password2"
		ok "the second user's password is in $LAV/password2, 0600"
		exit 0 ;;
	*)
		ko "⛔ «--sul-server» here can only do «user2»"; exit 2 ;;
	esac
fi

# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS ON THE LAPTOP
# ═══════════════════════════════════════════════════════════════════════════
STEP=${1:-state}
case "$STEP" in
port)
	log "1 · The sources OF THE WORKING TREE in $TREE (⛔ not git archive)"
	printf '    --  HEAD = %s · state of the tree:\n' "$(cd "$HERE" && git rev-parse --short HEAD)"
	(cd "$HERE" && git status --short -- src banchi/rcp) | sed 's/^/        /'
	log "   the fingerprints of what I SEND (⛔ the cures live here)"
	(cd "$HERE" && md5sum src/webtransport.c src/webtransport.h src/trasporto.c \
		src/rcp.c src/rcp.h src/main.c banchi/rcp/rcp.c banchi/rcp/rcp.h) | \
		sed 's/^/        /'
	# ⛔ WITHOUT `sudo`: `printf … | sudo -S` would eat stdin, which here IS the
	#    `tar` stream.  And it is not needed: /media/REMOTIX/src belongs to `nicfio`.
	(cd "$HERE" && tar --exclude='*.o' --exclude='src/remotix' -czf - \
		src banchi/rcp \
		banchi/01-b3-cliente.py banchi/01-b8-sblocca.py \
		banchi/01-b4-validatore.py \
		banchi/09-b78-apertura.py banchi/09-b81-terreno.sh \
		banchi/attrezzi-gruppi-scheda.sh banchi/07-b64-terreno.sh banchi/07-b64-scena.py banchi/07-b64-orecchio.py) | \
		ssh -o BatchMode=yes "$MACHINE" \
		"mkdir -p $TREE && tar -C $TREE -xzf -" || {
		ko "⛔ the sources did not arrive"; exit 2; }
	ok "sources in $TREE"

	log "2 · Building inside the container on the test machine"
	if ! ssh -o BatchMode=yes "$MACHINE" \
		"printf '%s\n' '$SUDO_PASSWORD' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'PFX=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $INSIDE_TREE/src/costruisci.sh 2>&1 | tail -25'"; then
		ko "⛔ the build failed: I do NOT start anything"
		exit 2
	fi
	ok "built"

	# ⛔⛔ AND NOW WE DECLARE WHAT CAME OUT, and the binary's `md5` is not
	#     enough: the real question is *«are the two cures inside?»*.  A
	#     binary that builds and does not have them is exactly the case this
	#     ground exists to rule out (⇒ the box at the top).  We look for the
	#     strings that ONLY the new cures put into the executable.
	log "3 · The binary's fingerprint, and the MARK of the two cures inside"
	ssh -o BatchMode=yes "$MACHINE" "md5sum $TREE/src/remotix" | sed 's/^/        /'
	for m in "dead-line %s reason_why=" "DEAD LINE — the QUIC connection is closing" \
	         "reason_why=%s stall_ms=" "stall_threshold_ms=" "exited_bytes=" \
	         "EVICTION for silence:" "EVICTION DENIED:" "--dead-line-stall-ms" \
	         "--eviction-ms"; do
		N=$(ssh -o BatchMode=yes "$MACHINE" \
			"grep -ac -- '$m' $TREE/src/remotix 2>/dev/null || echo 0")
		if [ "${N:-0}" = "0" ]; then
			ko "⛔ the mark «$m» is NOT in the binary: the cure is not there"
			exit 2
		fi
		ok "mark present: «$m»"
	done

	# ⛔⛔⭐ AND THE REMOVED OPTION IS CHECKED **BY TYPING IT**, not by searching for it.
	#
	#      `--linea-morta-permille` was removed on 23 August 2026 after
	#      this bench had refuted it, and a binary that still accepted it
	#      would be the OLD cure — the one that gave different reds on the same
	#      numbers.  ⇒ It must be checked.
	#
	# ⛔⛔ BUT NOT WITH A `grep` ON THE BINARY, and I fell for it: `[M]` 23 Aug
	#      2026, the first round of this check gave RED on a CORRECT
	#      binary.  The string is there all right — it sits in the **help text**, where
	#      `main.c` explains why the option no longer exists.  ⇒ Searching for
	#      the absence of a string answers «is it written somewhere?»
	#      and not «is it ACCEPTED?», which is the only question that matters.
	#      ⚠ It is the form of `LEZIONI.md` §1.9: a check that answers a
	#        question different from the one you think.
	#
	# ⇒ We TYPE the option and check that the binary REFUSES it: help on
	#   output and a non-zero code.  ⚠ Port 7999 and no certificate: the
	#   refusal comes during argument parsing, before opening anything.
	B2LIB=/srv/src/b2/ngtcp2/build/lib:/srv/src/b2/prefisso/lib
	RC=$(ssh -o BatchMode=yes "$MACHINE" \
		"printf '%s\n' '$SUDO_PASSWORD' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'LD_LIBRARY_PATH=$B2LIB $INSIDE_TREE/src/remotix --linea-morta-permille 50 \
		  --port 7999 >/dev/null 2>&1; echo \$?'" | tail -1 | tr -d '\r')
	if [ "${RC:-0}" = "0" ]; then
		ko "⛔⛔ the binary ACCEPTS «--linea-morta-permille» (exit $RC): this is"
		ko "     the OLD cure, the refuted one.  I do NOT measure."
		exit 2
	fi
	ok "⭐ «--linea-morta-permille» is REFUSED (exit $RC): it is the NEW cure"
	exit 0 ;;
username)
	# ⛔ First mine, with `07-b64-terreno.sh` (which already knows how)…
	bash "$HERE/banchi/07-b64-terreno.sh" username || exit 2
	# …and then the SECOND, which that script cannot do.
	ssh -o BatchMode=yes "$MACHINE" \
		"printf '%s\n' '$SUDO_PASSWORD' | sudo -S -p '' env \
		 USER2=$USER2 UID_B2=$UID_B2 USER2_PASSWORD=$USER2_PASSWORD LAV=$LAV \
		 bash $TREE/banchi/09-b81-terreno.sh --sul-server user2"
	exit $? ;;
*)
	# ⛔ Everything else is `07-b64-terreno.sh`, with MY environment exported:
	#    not one line of it is rewritten.
	exec bash "$HERE/banchi/07-b64-terreno.sh" "$STEP" ;;
esac
