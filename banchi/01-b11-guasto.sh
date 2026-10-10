#!/bin/bash
#
# 01-b11-guasto.sh — runs ON THE SERVER.  Turns the FAULTY server of B11 on and off.
#
#   bash /media/REMOTIX/src/01-b11-guasto.sh accendi
#   bash /media/REMOTIX/src/01-b11-guasto.sh registro
#   bash /media/REMOTIX/src/01-b11-guasto.sh spegni     ⛔ and PUTS BACK the healthy server
#
# ---------------------------------------------------------------------------
# ⛔ "SPEGNI" IS NOT ONLY TURNING OFF
#
# The B11 faults are lines that make **the server lie**.  A switch like
# that, if it survives the phase, will one day be found turned on by someone who did not
# know it existed — and the symptom would be "the server declares a version it does
# not speak", two months later, with nothing linking it to a bench.
#
# ⭐ That is why `spegni` stops the process **and rebuilds the healthy server**, and
#    verifies it: if after `spegni` the mark `REMOTIX B11` is still in the
#    source, this script says so out loud.
#
# ⛔ AND IT VERIFIES IT FROM THREE SIDES, since 10 Aug 2026.  Before, it looked **only at the
#    `.cc` source**, that is the side that does not count: what survives the
#    phase is the binary and the process, not the text.  Now it verifies
#
#      the PROCESS   is it really dead?  (before, the `kill` had no witnesses)
#      the PORT      is anyone still answering on 7447?  ⭐ it is the side that
#                    RECEIVES, the only one that can say "it stayed on"
#      the THREE FILES  the faults are in `rcp.c`, in the `.cc` and in the `.h`
#
#    (findings R5.10 and R5.18 of the adversarial review of 10 Aug 2026.)
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
# ⛔ THE FAULTS LIVE IN THREE FILES, NOT IN ONE.
#
#    `01-b11-guasto-innesta.py` grafts into `rcp.c`, into
#    `http3_server_proto_codec.cc` and into the `.h`, and **eight grafts out of eleven**
#    are in `rcp.c`.  Deciding "the faults are there" by looking at the `.cc` alone is
#    form E1 — necessary taken for sufficient: it was enough for one
#    graft of `rcp.c` to be skipped for the bench to print "built, and the faults are
#    there" and for the cases that fault was meant to provoke to fall with the red
#    pointed at the PAGE, which has nothing to do with it.
SORGENTI=(
	"$DENTRO/b2/ngtcp2/examples/rcp.c"
	"$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc"
	"$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.h"
)
IND=192.168.0.2
PORTA=7447
FILTRO="B11|AFTER the end|parting CONGEDO|congedo motivo|control channel opened"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-accendi}
MARCHE_ATTESE=""

# ⛔ No redirection AROUND enter.sh: it would carry off sudo's password
#    prompt, and the script would stay stuck on a question nobody
#    sees.  Inside the quotes instead it belongs to the remote command.  ⭐ This first
#    call is the one that asks for it, and from here on the credentials are
#    valid: the reads that follow can capture the output.
bash "$ENTRA" --root "true" || { ko "cannot enter the container"; exit 2; }

# ---------------------------------------------------------------------------
# ⛔ THE SENTINEL: "empty" is not "zero" (`REVIEWER.md` §1 question 4, form E8)
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` said "port
# free" in three opposite cases: the port is really free, `ss` is not in the
# container, `enter.sh` did not execute the command.  The third case turned on
# a SECOND server on the port of one already on, the first kept
# answering, and B11 measured **the wrong server** — which could be the
# HEALTHY one, that is exactly the defect the comment of `01-b11-lancia.sh`
# declares it wants to avoid.
#
# ⭐ Here the remote command prints its own exit status by itself.  If the line
#    `B11-FINE` does not arrive, the command did not reach the end — and this can be
#    told apart from "it ran and found nothing".
# ⚠ And so the measurement no longer rests on `enter.sh` propagating the
#   exit code of the command it runs, which nobody has ever verified
#   (finding R5.21, still open: it is closed with
#   `bash /media/REMOTIX/enter.sh --root "exit 7"; echo $?`).
USCITA=""
dentro() # $1 = remote command.  Output in $USCITA, status = that of the command
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB11-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B11-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B11-FINE=')
	if [ -z "$stato" ]; then
		return 125   # the command did not reach the end: it is not a zero
	fi
	return "$stato"
}

# Who holds the port.  0 = taken (the lines in $CHI) · 1 = free · 2 = un-
# known, and "unknown" is not rounded to "free".
CHI=""
chi_tiene_la_porta()
{
	local st
	dentro "ss -ulnp"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss -ulnp» did not answer inside the container (exit $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	# ⭐ THE POSITIVE CONTROL OF THE TOOL: `ss -ulnp` always prints at least
	#    its own header.  If it prints nothing it has looked at nothing,
	#    and a tool that cannot see what is there cannot say that
	#    something is missing (`REVIEWER.md` §1 question 5).
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss -ulnp» printed NOTHING, not even the header:"
		ko "   the tool is mute, and its silence is not a free port"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

# How many B11 marks there are in a file.  The count in $N; 2 = it could not
# be counted.  ⚠ `grep -c` exits 1 when the count is zero and >=2 when it could not
# read: they are two different things and here they stay different.
N=0
marche()
{
	local st
	dentro "grep -c 'REMOTIX B11 GUASTO' $1"
	st=$?
	if [ "$st" -gt 1 ]; then
		ko "⛔ the marks in $1 could not be counted (exit $st):"
		printf '%s\n' "$USCITA" | tail -3 | sed 's/^/        /'
		return 2
	fi
	N=$(printf '%s' "$USCITA" | tr -cd '0-9')
	if [ -z "$N" ]; then
		ko "⛔ the count of the marks in $1 did not produce a number"
		return 2
	fi
	return 0
}

ricostruisci() # $1 = "con-guasti" | "sano"
{
	local passo st
	# ⛔ AND EVERY STEP IS TESTED.
	#
	#    The four invocations all had `> /dev/null` and **no test
	#    of the exit status**.  It was enough to make the `git checkout --
	#    examples` of `01-b2-ngtcp2-wt-innesta.py --togli` fail (tree not clean,
	#    permissions, `git` absent): the mark `REMOTIX B3` stayed in the `.cc`,
	#    `01-b3-rcp-innesta.py` took the short circuit "the graft is already
	#    there" — which returns **0** — and exited BEFORE copying `rcp.c` again.
	#    ⚠ The rebuilding of the healthy source, that is the only thing preventing
	#      the lying server from surviving the phase, had no
	#      witness (finding R5.8).
	for passo in "01-b3-rcp-innesta.py --togli" \
	             "01-b2-ngtcp2-wt-innesta.py --togli" \
	             "01-b2-ngtcp2-wt-innesta.py" \
	             "01-b3-rcp-innesta.py"; do
		dentro "python3 $DENTRO/$passo"
		st=$?
		if [ "$st" -ne 0 ]; then
			ko "⛔ «$passo» failed (exit $st):"
			printf '%s\n' "$USCITA" | tail -20 | sed 's/^/        /'
			return 1
		fi
	done
	if [ "$1" = con-guasti ]; then
		dentro "python3 $DENTRO/01-b11-guasto-innesta.py"
		st=$?
		printf '%s\n' "$USCITA" | sed 's/^/        /'
		if [ "$st" -ne 0 ]; then
			ko "⛔ the graft of the B11 faults failed (exit $st)"
			return 1
		fi
		# ⭐ THE DENOMINATOR IS COMPUTED BY WHOEVER GRAFTS, and printed.  Here no
		#    number is written by hand: it would age with the first graft
		#    someone adds to the table.
		MARCHE_ATTESE=$(printf '%s\n' "$USCITA" \
			| sed -n 's/^== B11-MARCHE-ATTESE: \([0-9][0-9]*\)$/\1/p' | tail -1)
		if [ -z "$MARCHE_ATTESE" ]; then
			ko "⛔ the graft did not declare how many marks are expected:"
			ko "   without that number the check below has no denominator"
			return 1
		fi
	fi
	# ⛔ AND NINJA'S OUTCOME IS RETURNED.
	#
	#    The first round of 10 Aug 2026 did not look at it: it only
	#    checked that `bsslserver` **existed and was executable**.  The
	#    compilation had failed, the binary from two hours before was still there,
	#    and the bench turned on **the HEALTHY server declaring it had turned on the
	#    faulty one**.  ⚠ All the B11 cases would have failed, and the red would have
	#    landed on the PAGE — which had nothing to do with it.
	#
	# ⭐ "The file is there" and "the file is the one I just built" are two
	#    different questions, and only the second has a denominator.
	dentro "ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b11-compila.log 2>&1"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ the compilation FAILED (exit $st).  The log says:"
		dentro "grep -m6 -n error $DENTRO/b11-compila.log"
		printf '%s\n' "$USCITA" | sed 's/^/        /'
		return 1
	fi
	return 0
}

# The B11 marks across all three sources.  The total in $TOTALE.
TOTALE=0
conta_le_marche()
{
	local f
	TOTALE=0
	for f in "${SORGENTI[@]}"; do
		marche "$f" || return 2
		inf "$(basename "$f"): $N marks «REMOTIX B11 GUASTO»"
		TOTALE=$((TOTALE + N))
	done
	return 0
}

case "$AZIONE" in
registro)
	# ⛔ The server log is the SECOND WITNESS of B11: two of the
	#    lines of the table are NEGATIVE properties of the page — "after
	#    RESPINTO it does not retry", "no application heartbeat" — and a negative
	#    property cannot be seen from inside the page.
	# ⭐ And the "parting CONGEDO" travels with them: it is the POSITIVE witness
	#    of the same rule — without it, "zero bytes after the end" would be true
	#    even for a page that never said farewell.
	#
	# ⛔⭐ AND THE CUT AT THE TAIL IS A DENOMINATOR THAT LIES, in both
	#    directions, and that is why it is no longer there.
	#
	#    It was `tail -60`.  On 10 Aug 2026, adding ONE more line to
	#    this filter, the "faults served" went from 26 to 21 — and the
	#    server had not changed anything: it was the old lines, pushed
	#    out of the window by the new ones.  ⚠ The `tail -600` that had
	#    replaced it had the same defect further on: it discards the **oldest**
	#    lines, that is those of the FIRST engine, and a "bytes arrived
	#    AFTER the end" line of the first engine leaves the window long before the
	#    count of the cases notices — "zero bytes after the end" becomes the
	#    emptiest green there is (finding R5.9).
	#
	# ⭐ In place of the cap there is the COUNT: how many lines the filter found is
	#    declared here, and whoever reads over there compares with how many
	#    arrived.  A truncation, wherever it comes from, can be seen.
	if [ ! -f "$FUORI/b11-server.log" ]; then
		ko "⛔ $FUORI/b11-server.log is not there."
		ko "   It is not «zero lines»: it is a read that could not be done, and"
		ko "   the second witness of B11 has nothing to say (form E8)."
		exit 7
	fi
	QUANTE=$(grep -Ec "$FILTRO" "$FUORI/b11-server.log")
	ST=$?
	if [ "$ST" -gt 1 ]; then
		ko "⛔ the log could not be read (grep exited $ST)"
		exit 7
	fi
	grep -E "$FILTRO" "$FUORI/b11-server.log"
	printf '== RIGHE-DEL-REGISTRO-FILTRATE: %s\n' "$QUANTE"
	exit 0
	;;
spegni)
	log "1. ⛔ The FAULTY server is stopped, and it is verified that it is DEAD"
	# ⛔ What must be verified is THE PROCESS, not the source (form E7).
	#
	#    The three lines from before threw the outcome away three times: `cat … 2>/dev/null`
	#    (PID file absent ⇒ `P` empty ⇒ nothing is killed), `[ -n "$P" ]
	#    &&` without an `else` branch (the absence of the PID was not an error), `kill $P
	#    2>/dev/null || true`.  And the PID file was removed anyway,
	#    carrying away the trace of the surviving process.
	#    ⚠ With `b11-server.pid` deleted while the server runs, `spegni` did not
	#      kill anything, rebuilt the healthy source, found the grep clean
	#      and printed "⭐ the server is the real one" exiting 0 — **with the lying
	#      server still on at 7447** (finding R5.18).
	P=""
	if [ -f "$FUORI/b11-server.pid" ]; then
		P=$(cat "$FUORI/b11-server.pid")
	else
		inf "⚠ $FUORI/b11-server.pid is not there: it is not known WHICH process to stop,"
		inf "  and so we ask the port, which is the side that receives"
	fi
	if [ -n "$P" ]; then
		dentro "kill $P"
		ST=$?
		[ "$ST" -eq 0 ] || inf "⚠ «kill $P» answered $ST: maybe it was already dead"
		I=0
		STATO=0
		while [ "$I" -lt 10 ]; do
			dentro "test -d /proc/$P"
			STATO=$?
			[ "$STATO" -eq 0 ] || break
			sleep 1
			I=$((I + 1))
		done
		case "$STATO" in
		1) ok "process $P is dead (after $I seconds)" ;;
		0) ko "⛔ the faulty server (PID $P) is STILL ALIVE after $I seconds."
		   ko "   We do not go on: the phase would stay with a lying server"
		   ko "   on, and the next one to find it will not know where it comes from."
		   exit 6 ;;
		*) ko "⛔ it could not be known whether PID $P is alive (exit $STATO)"
		   exit 6 ;;
		esac
	fi
	chi_tiene_la_porta
	ST=$?
	case "$ST" in
	1) ok "port $PORTA is free: nobody answers any more" ;;
	0) ko "⛔ port $PORTA is STILL HELD by someone:"
	   printf '%s\n' "$CHI" | sed 's/^/        /'
	   ko "   ⚠ it may be the HEALTHY B2 server left on: the PID is up"
	   ko "   there.  In both cases the cleanup is not finished, and"
	   ko "   saying so now costs less than discovering it at the next «accendi»."
	   exit 6 ;;
	*) exit 6 ;;
	esac
	# ⭐ Only now is the PID file thrown away: it is the trace of the process, and it is
	#    lost last.
	rm -f "$FUORI/b11-server.pid"

	log "2. ⛔ The HEALTHY server is put back"
	# ⛔ AND THE OUTCOME OF THE REBUILD IS READ.
	#
	#    `ricostruisci sano` was a bare statement: the same exit status
	#    that `accendi` tests (`if ! ricostruisci con-guasti`) was thrown
	#    away here.  It was enough to make the rebuild of the healthy server fail for
	#    **the faulty binary** to stay on disk while the source went back
	#    clean: the grep below was green, "the server is the real
	#    one" was printed, and the next `01-b2-lancia-wt.sh accendi` turned on that
	#    binary (finding R5.1).
	if ! ricostruisci sano; then
		ko "⛔ THE REBUILD OF THE HEALTHY SERVER FAILED."
		ko "   On disk there may still be the FAULTY binary, and the clean"
		ko "   source does not say so: put back the B2 and B3 grafts by hand."
		exit 5
	fi
	conta_le_marche || exit 5
	if [ "$TOTALE" -eq 0 ]; then
		ok "⭐ no trace of B11 in the ${#SORGENTI[@]} sources, and the binary"
		ok "   is the one just rebuilt: the server is the real one"
	else
		ko "⛔ $TOTALE lines of B11 REMAIN in the sources."
		ko "   A server that lies on purpose must NOT survive the phase."
		exit 5
	fi
	exit 0
	;;
accendi) ;;
*) ko "unknown action: $AZIONE  (accendi | registro | spegni)"; exit 2 ;;
esac

# ---------------------------------------------------------------------------
log "1. The port"
chi_tiene_la_porta
ST=$?
case "$ST" in
1) ok "port $PORTA free — and «ss» says so, not the silence" ;;
0) ko "port $PORTA is taken:"
   printf '%s\n' "$CHI" | sed 's/^/        /'
   exit 3 ;;
*) exit 3 ;;
esac

log "2. The faulty server is built"
if ! ricostruisci con-guasti; then
	ko "   and NOTHING is turned on: the old binary is still on disk, and"
	ko "   turning it on would mean measuring a HEALTHY server believing it faulty"
	exit 4
fi
conta_le_marche || exit 4
if [ "$TOTALE" -ne "$MARCHE_ATTESE" ]; then
	ko "⛔ on disk there are $TOTALE B11 marks, and whoever grafted them"
	ko "   declares $MARCHE_ATTESE: the faults the bench believes it measures are not"
	ko "   those the server has inside, and the red would land on the PAGE"
	exit 4
fi
ok "built, and the faults are all there: $TOTALE of $MARCHE_ATTESE expected, in ${#SORGENTI[@]} files"

log "3. Turning on"
rm -f "$FUORI/b11-server.log" "$FUORI/b11-server.pid"
# ⚠ `--timeout=120s`: the «silenzio» case stays quiet for eight seconds to prove that the
#   page does not send an application heartbeat (§2.2).  With the default cap at
#   30 s the connection would hold all the same, but the cases in a row on a single
#   page would not.
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b11-server.log 2>&1 & echo \$! > $DENTRO/b11-server.pid"
sleep 2
PID=$(cat "$FUORI/b11-server.pid" 2>/dev/null)
# ⚠ `/proc/$PID` is read from here and not from inside, and that is correct: that of
#   `enter.sh` is a `chroot` (`fondamenta/banco/enter.sh`), which shares the
#   host's PID namespace — not a container with a namespace of its own.
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "the faulty server did not start:"
	sed 's/^/        /' "$FUORI/b11-server.log"
	exit 4
fi
# ⛔ "ALIVE" IS NOT "LISTENING", and it is form E1 in a single line.
#
#    `01-b2-lancia-wt.sh` does this same verification and explains why: "the
#    server is alive but holds no UDP port".  B11 kept half of it
#    and threw away the other: a server still alive at 2 s but that had already
#    failed the `bind` made it print "ok FAULTY server listening", and all the
#    cases fell with the red on the PAGE (finding R5.13).
chi_tiene_la_porta
ST=$?
if [ "$ST" -ne 0 ]; then
	ko "the server is alive (PID $PID) but on port $PORTA there is nobody:"
	sed 's/^/        /' "$FUORI/b11-server.log"
	exit 4
fi
ASC=$(printf '%s\n' "$CHI" | grep "pid=$PID,")
if [ -z "$ASC" ]; then
	ko "⛔ port $PORTA is held by ANOTHER process, not by our $PID:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "   B11 would measure the wrong server — which could be the HEALTHY one"
	exit 4
fi
ok "FAULTY server listening, PID $PID"
printf '%s\n' "$ASC" | sed 's/^/        /'
inf "⛔ it is a server that lies on purpose: it is turned off with «spegni», which"
inf "   also puts back the healthy source"
inf "the fingerprint of the session certificate, for the page:"
bash "$ENTRA" --root \
	"openssl x509 -in $CERT/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0" \
	| tail -1 | sed 's/^/        /'
exit 0
