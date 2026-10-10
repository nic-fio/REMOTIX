#!/bin/bash
#
# attrezzi-allinea-innesto.sh — ⛔ RUNS ON THE SERVER (outside the container).
# Puts back into the graft the three files that B3 copies there, and REBUILDS.
#
#   bash /media/REMOTIX/src/attrezzi-allinea-innesto.sh guarda   just tells
#   bash /media/REMOTIX/src/attrezzi-allinea-innesto.sh allinea  copy + ninja + terrain
#
# ---------------------------------------------------------------------------
# ⛔ WHY IT EXISTS — THE CHECK WAS THERE, THE CURE WAS NOT
#
# `[M]` the night between 11 and 12 Aug 2026.  The farewell cure
# (`DECISIONI.md` §1.12) had updated `rcp/rcp.c` at 13:43; the graft —
# `b2/ngtcp2/examples/rcp.c`, i.e. the file the server that SIX
# BENCHES query is compiled from — was still at the morning's code.  For half a day:
#
#   · the certifications of B3, B5, B6, B7, B8, B13 were EXPIRED (their files
#     had changed) — and the log said so;
#   · ⛔ but they were also UNREPEATABLE, and nobody said that:
#     re-running them would have written six lines dated tonight **on the
#     old code**.
#
# ⭐ The one that saw it was `01-b0-terreno.sh`, in half a second, on the first round:
#    *«examples/rcp.c is NOT rcp/rcp.c ⇒ the server measures a version that
#    nobody is reading»*.  ⛔ But then the cure was done BY HAND — `cp` and
#    `ninja` typed on the command line — and a cure by hand comes back: it is the
#    same reason `01-p5-accendi.sh` exists.
#
# ⇒ The check says WHAT is wrong; this file says HOW to put it back.
#
# ---------------------------------------------------------------------------
# ⛔ AND IT REFUSES IF THERE IS A GRAFTED FAULT IN THE GRAFT
#
# B12 and B11 graft faults RIGHT INTO `examples/rcp.c`.  ⛔ Copying the
# source over it while a round is in progress would remove the fault **from under
# whoever is measuring it**, and that round would say «the bench did not turn red» of a
# bench whose accused was taken out of its hands.  ⇒ If the marks are there, we
# stop here and say so.
#
# ⛔ And we look at the OUTCOME of `ninja`, not at the binary being there afterwards: it
#    is the trap already paid for on B11 (`LEZIONI.md` §1.9 point 8) — a binary from
#    two hours earlier answers «I exist» just like one from now.
set -uo pipefail

E=${ENTRA:-/media/REMOTIX/enter.sh}
FUORI=${FUORI:-/media/REMOTIX/src}
DENTRO=${DENTRO:-/srv/src}
ESEMPI_FUORI=$FUORI/b2/ngtcp2/examples
ESEMPI_DENTRO=$DENTRO/b2/ngtcp2/examples
FILE="rcp.c rcp.h autenticazione.c"

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

AZIONE=${1:-guarda}
case "$AZIONE" in guarda|allinea) ;; *) echo "usage: $0 [guarda|allinea]"; exit 2 ;; esac

# ---------------------------------------------------------------------------
log "1. The three files that B3 copies into the graft"
DIVERSI=""
MANCANTI=0
for f in $FILE; do
	s=$FUORI/rcp/$f
	d=$ESEMPI_FUORI/$f
	if [ ! -f "$s" ] || [ ! -f "$d" ]; then
		ko "⛔ cannot compare «$f»: missing $( [ -f "$s" ] || echo "rcp/$f" ) $( [ -f "$d" ] || echo "examples/$f" )"
		MANCANTI=$((MANCANTI+1))
		continue
	fi
	a=$(md5sum "$s" | cut -d' ' -f1)
	b=$(md5sum "$d" | cut -d' ' -f1)
	if [ "$a" = "$b" ]; then
		ok "$f identical  ($a)"
	else
		ko "⛔ $f DIFFERENT — source $a · graft $b"
		# ⭐ And we say HOW MANY lines differ, because «different» and «different by
		#    a whole cure» send you to look in two different places.
		inf "   lines that change: $(diff "$s" "$d" | grep -c '^[<>]')"
		DIVERSI="$DIVERSI $f"
	fi
done
[ "$MANCANTI" -gt 0 ] && { ko "⛔ with missing files I align nothing"; exit 2; }

# ⚠ And we declare what the terrain does NOT compare: today it looks only at rcp.c.
# ⛔ And no backticks inside double quotes: the first time I
#    ran this file the line below EXECUTED «01-b0-terreno.sh» instead
#    of printing it — «command not found» in the middle of a tool that worked.
inf "⚠ 01-b0-terreno.sh compares only rcp.c; here all three are checked"

# ---------------------------------------------------------------------------
# ⛔⭐ AND «IDENTICAL» IS NOT ENOUGH: THE BINARY MUST BE NEWER THAN THE SOURCES.
#
# `[M]` 12 Aug 2026, and the test of this very tool found it: after
# the copy the three files carry the DATE OF NOW, so a binary built
# before is old even if the content is the same.  ⛔ If the round stops
# between the copy and `ninja` — for me a `timeout` stopped it — what remains is a scene in
# which the fingerprints match, `guarda` would say «aligned», and the terrain
# would still reject it with «the binary is older than a source it
# declares».  ⇒ We look at the clock too, not only at the fingerprints.
BINARIO=$FUORI/b2/ngtcp2/build/examples/bsslserver
VECCHIO=""
if [ -f "$BINARIO" ]; then
	for f in $FILE; do
		[ "$ESEMPI_FUORI/$f" -nt "$BINARIO" ] && VECCHIO="$VECCHIO $f"
	done
	if [ -n "$VECCHIO" ]; then
		ko "⛔ the binary is OLDER than:$VECCHIO"
		inf "   bsslserver: $(stat -c %y "$BINARIO" | cut -c1-19)"
		inf "   ⇒ it must be rebuilt even if the fingerprints match"
	else
		ok "and the binary is newer than all three ($(stat -c %y "$BINARIO" | cut -c1-19))"
	fi
else
	ko "⛔ $BINARIO is not there: the graft has never been built"
	VECCHIO=" (binary missing)"
fi

if [ -z "$DIVERSI" ] && [ -z "$VECCHIO" ]; then
	ok "⭐ the graft is already aligned with the sources, and the binary comes after"
	[ "$AZIONE" = guarda ] && exit 0
	inf "nothing to copy and nothing to rebuild: straight to the terrain"
fi

# ---------------------------------------------------------------------------
log "2. ⛔ Is there a grafted fault inside the graft?"
TROVATI=0
for m in "REMOTIX B12 GUASTO" "REMOTIX B11"; do
	n=$(grep -ac "$m" "$ESEMPI_FUORI/rcp.c" 2>/dev/null)
	if [ "${n:-0}" -gt 0 ]; then
		ko "⛔ «$m» appears $n time(s) in examples/rcp.c"
		TROVATI=$((TROVATI+1))
	else
		ok "no trace of «$m»"
	fi
done
if [ "$TROVATI" -gt 0 ]; then
	ko "⛔ I TOUCH NOTHING: there is a grafted fault, and copying the"
	ko "   source over it would remove it FROM UNDER whoever is measuring it — that round"
	ko "   would write «the bench did not turn red» of a bench whose"
	ko "   accused was taken out of its hands."
	ko "   ⇒ Wait for the round to finish, or remove it with «--togli»."
	exit 3
fi

if [ "$AZIONE" = guarda ]; then
	inf "«guarda» stops here: to copy and rebuild, «allinea»"
	exit 1
fi

# ---------------------------------------------------------------------------
if [ -n "$DIVERSI" ]; then
	log "3. Copying the source into the graft"
	for f in $DIVERSI; do
		bash "$E" --root "cp $DENTRO/rcp/$f $ESEMPI_DENTRO/$f" || {
			ko "⛔ copying «$f» failed"; exit 3; }
		a=$(md5sum "$FUORI/rcp/$f" | cut -d' ' -f1)
		b=$(md5sum "$ESEMPI_FUORI/$f" | cut -d' ' -f1)
		[ "$a" = "$b" ] && ok "$f copied, and the fingerprints now match ($a)" \
		                || { ko "⛔ $f copied but the fingerprints do NOT match"; exit 3; }
	done

fi

if [ -n "$DIVERSI" ] || [ -n "$VECCHIO" ]; then
	log "4. Rebuilding — and looking at the OUTCOME, not at the binary"
	# ⛔⭐ HERE THERE WAS `>/dev/null 2>&1` **AROUND** `enter.sh`, AND IT IS THE
	#     TRAP THAT `FASI.md` §00-ambiente B3.3 DECLARES PAID FOR FOUR
	#     TIMES — this is the fifth.  `[M]` 12 Aug 2026, 15:22-15:32.
	#
	# `enter.sh` asks for the `sudo` password with `sudo -v -S -p`: the
	# prompt goes out on **stderr** and the answer is read from stdin.  Throwing
	# away stderr, the question reaches nobody — and whoever launches the round from
	# another machine cannot answer a question they do not see.
	# ⚠ And the symptom is the misleading one: not an error, but a **slow**
	#   tool.  `[M]` `ps` on the server: `sudo -v -S -p Password sudo:` stuck
	#   for 5 minutes and 28 seconds, with `attrezzi-allinea-innesto.sh` blocked
	#   right **after the copy and before `ninja`** — i.e. with the sources already
	#   replaced and the binary still the old one: the WORST scene, which
	#   is exactly the one the comment at the top of this file describes.
	# ⛔ From an interactive terminal the defect is invisible as long as the `sudo`
	#    credit holds: it shows only when it expires — i.e. on long rounds.
	#
	# ⭐ The cure is the house one (`01-b12-lancia.sh`, `01-p1-prodotto.sh`): we
	#    redirect **inside** the quotes, to a file, and read the file
	#    afterwards.  That way the outcome stays that of `ninja` and the error is not lost.
	rm -f "$FUORI/attrezzi-allinea-ninja.log"
	if bash "$E" --root "ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/attrezzi-allinea-ninja.log 2>&1"; then
		ok "⭐ bsslserver rebuilt"
		# ⚠ And we say how many rules it ran: «ninja had nothing to
		#   do» and «ninja recompiled» both exit 0, and after a
		#   copy of sources the two are not the same thing.
		inf "   $(tail -1 "$FUORI/attrezzi-allinea-ninja.log" 2>/dev/null)"
	else
		ko "⛔ the build FAILED: the binary that is there is the"
		ko "   old one, and now the source has changed under it — i.e."
		ko "   the WORST scene.  The error:"
		[ -f "$FUORI/attrezzi-allinea-ninja.log" ] \
			&& tail -20 "$FUORI/attrezzi-allinea-ninja.log" | sed 's/^/        /' \
			|| ko "   ⛔ and there is not even the ninja log: I read nothing"
		exit 3
	fi
fi

# ---------------------------------------------------------------------------
log "5. ⛔ And the terrain says it, not me"
bash "$FUORI/01-b0-terreno.sh" innesto
T=$?
if [ "$T" -eq 0 ]; then
	printf '\n    \033[1;32m⭐ graft aligned, and the terrain holds\033[0m\n'
else
	printf '\n    \033[1;31m⛔ the terrain does NOT hold (exit %s): do not launch benches\033[0m\n' "$T"
fi
exit "$T"
