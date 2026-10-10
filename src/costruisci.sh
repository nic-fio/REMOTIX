#!/bin/bash
#
# costruisci.sh — builds the server INSIDE the test machine's
#                 container.  It already runs inside `enter.sh`, it does not call it.
#
#   bash <where-this-file-is>/costruisci.sh
#
# ⚠ The path is NOT fixed, and it changed on the night of 10 August 2026 (finding
#   R12.8): the line above said `/srv/src/remotix/costruisci.sh`, and
#   `/srv/src` is the BENCHES' folder — no script in the repo copies anything
#   into `/srv/src/remotix`.  Everything it needs it derives from `$QUI`, that is from
#   where this file is: put the `src/` folder wherever you like and launch it.
#
# ⛔ AND THE ENVIRONMENT VARIABLES IT ACCEPTS, because a guessed path is
#    a path that one day changes:
#
#      PREFISSO   where ngtcp2/nghttp3 are installed       (def. /srv/src/b2/prefisso)
#      NGTCP2     the ngtcp2 source tree                   (def. /srv/src/b2/ngtcp2)
#      NGHTTP3    the nghttp3 source tree                  (def. /srv/src/b2/nghttp3)
#      GEMELLO    the twin copy of rcp.c/rcp.h/autenticazione.c to compare
#                 (def. <QUI>/../banchi/rcp, and `nessuno` to DECLARE not
#                  comparing — see the Makefile, finding R12.3)
#
# -----------------------------------------------------------------------------
# ⛔ AFTER BUILDING WE LOOK AT THE BUILDER'S OUTCOME, NOT AT THE PRESENCE OF THE
#    FILE.
#
# `LEZIONI.md` §1.9 point 8: "a file from yesterday answers 'yes' to *does it exist?*
# exactly like one from now".  The B11 bench started the HEALTHY server
# declaring it had started the broken one, because it checked `test -x`.
#
# ⭐ Hence the two things this script does that a bare `make` does not:
#    1. it deletes the binary BEFORE rebuilding, so "it is there" means "it is
#       from now";
#    2. it checks the MARK inside the produced binary — which answers the
#       right question: *is what should be in it inside?*
# -----------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PREFISSO=${PREFISSO:-/srv/src/b2/prefisso}
NGTCP2=${NGTCP2:-/srv/src/b2/ngtcp2}
NGHTTP3=${NGHTTP3:-/srv/src/b2/nghttp3}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# -----------------------------------------------------------------------------
# 1. Where ngtcp2 and nghttp3 are.  ⛔ We DECLARE where we looked: a
#    "not found" without the denominator is not a measurement (`LEZIONI.md` §1.9).
log "The dependencies built from source"

INC=""
LIB=""

cerca_ngtcp2()
{
	local i h
	for i in "$NGTCP2/build/lib/includes" "$NGTCP2/lib/includes" \
	         "$PREFISSO/include"; do
		[ -f "$i/ngtcp2/ngtcp2.h" ] || [ -f "$i/ngtcp2/version.h" ] && \
			INC="$INC -I$i"
	done
	# the crypto headers live in a separate tree
	h="$NGTCP2/crypto/includes"
	[ -f "$h/ngtcp2/ngtcp2_crypto_ossl.h" ] && INC="$INC -I$h"

	for i in "$NGTCP2/build/lib" "$NGTCP2/build/crypto/ossl" "$PREFISSO/lib" "$PREFISSO/lib64"; do
		[ -d "$i" ] && LIB="$LIB -L$i -Wl,-rpath,$i"
	done
}

cerca_nghttp3()
{
	local i
	for i in "$NGHTTP3/lib/includes" "$NGHTTP3/build/lib/includes" \
	         "$PREFISSO/include"; do
		[ -f "$i/nghttp3/nghttp3.h" ] || [ -f "$i/nghttp3/version.h" ] && \
			INC="$INC -I$i"
	done
	for i in "$NGHTTP3/build/lib" "$PREFISSO/lib" "$PREFISSO/lib64"; do
		[ -d "$i" ] && LIB="$LIB -L$i -Wl,-rpath,$i"
	done
}

cerca_ngtcp2
cerca_nghttp3

printf '    --  I looked in:\n'
printf '        %s\n' "$NGTCP2" "$NGHTTP3" "$PREFISSO"
printf '    --  headers:      %s\n' "${INC:-(none)}"
printf '    --  libraries:    %s\n' "${LIB:-(none)}"

[ -n "$INC" ] || { ko "no header found"; exit 2; }
[ -n "$LIB" ] || { ko "no library found"; exit 2; }
ok "paths composed"

# -----------------------------------------------------------------------------
log "OpenSSL"
V=$(openssl version 2>&1)
printf '    --  %s\n' "$V"
case "$V" in
	OpenSSL\ 3.[5-9]*|OpenSSL\ [4-9]*) ok "3.5 or later: the native QUIC API is there" ;;
	*) ko "OpenSSL >= 3.5 is needed for ngtcp2_crypto_ossl"; exit 2 ;;
esac

# -----------------------------------------------------------------------------
log "The old binary is thrown away BEFORE building"
rm -f "$QUI/remotix" "$QUI"/*.o
if [ -e "$QUI/remotix" ]; then
	ko "the old binary cannot be deleted: it could not be told apart from the new one"
	exit 2
fi
ok "old one gone"

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# ⛔⭐ THE TWO COPIES OF THE SAME MODULE — finding R12.3.
#
# `rcp.c`, `rcp.h` and `autenticazione.c` live in two folders of this repo,
# because they are the same module mounted on two hosts.  The comparison is done by the
# `impronte` target of the Makefile, and the Makefile STOPS the build if they
# diverge.  ⚠ Here we only choose WHERE to look, and DECLARE if we could
# not look: "I found no differences" and "I did not look" are two
# different facts.
log "The twin copy of rcp.c"
if [ -z "${GEMELLO:-}" ]; then
	for c in "$QUI/../banchi/rcp" "$QUI/rcp-gemello" /srv/src/rcp; do
		if [ -f "$c/rcp.c" ]; then GEMELLO=$c; break; fi
	done
fi
if [ -z "${GEMELLO:-}" ]; then
	ko "⛔ no twin copy found: I looked in"
	printf '        %s\n' "$QUI/../banchi/rcp" "$QUI/rcp-gemello" /srv/src/rcp
	ko "   It is NOT «the copies match»: it is «I could not look».  We"
	ko "   build anyway, and this line is the declaration (R12.3)."
	GEMELLO=nessuno
else
	ok "comparing against «$GEMELLO»"
fi

# -----------------------------------------------------------------------------
log "make"
# ⚠ make's output goes to the terminal as it comes: no pipes, or the status that is
#   read would be that of the last command of the pipe (`LEZIONI.md` §1.9).
make -C "$QUI" \
	GEMELLO="$GEMELLO" \
	CFLAGS="-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter $INC" \
	LDFLAGS="$LIB" \
	tutto
ESITO=$?

if [ "$ESITO" -ne 0 ]; then
	ko "⛔ the build has FAILED (exit $ESITO).  The binary was NOT"
	ko "   built, and whatever may be on disk is not from now."
	exit "$ESITO"
fi
ok "make exited 0"

# -----------------------------------------------------------------------------
# ⛔ And now the right question: is what should be in it inside?
log "The mark inside the binary"
if [ ! -x "$QUI/remotix" ]; then
	ko "make exited 0 and the binary is not there: something does not add up"
	exit 3
fi

# ⚠ `grep -a` on the binary, and NOT `strings`: `binutils` may be missing — and the
#   first draft of this script tripped on it, declaring all five
#   marks absent because the TOOL was not there.  It is `LEZIONI.md` §1.9
#   second rule: it was the positive control that said so, not the five red
#   lines.
cerca() # $1 = file, $2 = text
{
	grep -a -F -q -e "$2" -- "$1"
}

MANCA=0
# ⚠ The last three marks are from the night of 10 August 2026, and each answers
#   a question a successful `make` does NOT answer:
#     NON-BANNATO         the unblock command on the socket really is there (R12.1)
#     transport PINGs ON  the cure of §4.6 is inside this binary (B-2)
#     pam.d/remotix       the PAM service is that of SPECIFICHE.md §4.2 (B-11)
for marca in "REMOTIX — phase 1, the bare wire" "Cross-Origin-Embedder-Policy" \
             "Cross-Origin-Opener-Policy" "/rcp/1" "/impronta" \
             "NON-BANNATO" "transport PINGs ON" "/etc/pam.d/remotix"; do
	if cerca "$QUI/remotix" "$marca"; then
		ok "«$marca» is in the binary"
	else
		ko "«$marca» is NOT in the binary"
		MANCA=1
	fi
done

# ⛔ And the markers the server replaces in the page are in the PAGE, not
#    in the binary: it is the check `pagina_apri()` redoes at startup, and without
#    which the server would forever serve a page without fingerprint — or a
#    page that does not say whether the address is banned (R12.2).
for segno in "__IMPRONTA__" "__AVVISO__" "__BANNATO__" "__RESTANO_MS__"; do
	if cerca "$QUI/pagina.html" "$segno"; then
		ok "«$segno» is in pagina.html"
	else
		ko "«$segno» is NOT in pagina.html: the server will refuse to start"
		MANCA=1
	fi
done

# The positive control of the tool: can it find something that is certainly there?
# Without it, "I did not find it" and "I cannot search" have the same face.
if cerca "$QUI/remotix" "GCC:" || cerca "$QUI/remotix" "main.c"; then
	ok "positive control: the tool can find what is certainly there"
else
	ko "⛔ the tool does NOT even find the compiler's mark: the NOs"
	ko "   above are worth nothing"
	exit 3
fi

[ "$MANCA" -eq 0 ] || exit 3

# -----------------------------------------------------------------------------
# ⛔⭐ THE PAM SERVICE — `SPECIFICHE.md` §4.2, finding B-11.
#
# Without `/etc/pam.d/remotix`, Linux-PAM falls back to the `other` service, which on
# Debian is `pam_deny`: EVERY right password is refused, and what
# one reads is "wrong user or password".  ⛔ The defect is a missing
# file and the diagnosis points at the password — the exact form that
# `LEZIONI.md` §1.9 calls the most expensive.
#
# ⚠ An already present file is not overwritten: whoever administers the machine may
#   have modified it, and rewriting it at every build would be a
#   configuration that loses itself.
log "The PAM service"
# ⭐ PHASE 17: the PAM file excludes whoever is in /etc/remotix/utenti-negati, with
#    onerr=fail ⇒ without the file nobody gets in.  The file first, and it is not
#    rewritten if it is there.
if [ -f /etc/remotix/utenti-negati ]; then
	ok "/etc/remotix/utenti-negati is already there (not touching it)"
elif install -D -m 644 /dev/null /etc/remotix/utenti-negati 2>/dev/null \
     && echo root > /etc/remotix/utenti-negati; then
	ok "written /etc/remotix/utenti-negati: root"
else
	ko "⛔ /etc/remotix/utenti-negati is NOT there and I could not write it (root needed):"
	ko "   with the new PAM NOBODY will get in.  By hand:  echo root > /etc/remotix/utenti-negati"
fi
if [ -f /etc/pam.d/remotix ]; then
	ok "/etc/pam.d/remotix is already there (not touching it)"
elif cp "$QUI/remotix.pam" /etc/pam.d/remotix 2>/dev/null; then
	ok "installed /etc/pam.d/remotix from $QUI/remotix.pam"
else
	ko "⛔ /etc/pam.d/remotix is NOT there and I could not install it (root needed)."
	ko "   The server will start and will REFUSE every password, saying it is"
	ko "   wrong.  Copy it by hand:  cp $QUI/remotix.pam /etc/pam.d/remotix"
fi

log "The libraries it really depends on"
ldd "$QUI/remotix" | grep -E 'ngtcp2|nghttp3|ssl|crypto|pam' || true

printf '\n'
ok "⭐ built: $QUI/remotix"
