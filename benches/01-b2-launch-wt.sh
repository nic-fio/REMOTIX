#!/bin/bash
#
# 01-b2-launch-wt.sh — runs ON THE SERVER, and measures the minimal server of B2.
#
#   bash /media/REMOTIX/src/01-b2-launch-wt.sh
#
# ---------------------------------------------------------------------------
# WHAT IT MEASURES
#
# `PHASES.md` §01-filo-nudo, group 2: **a WebTransport session on `/rcp/1`,
# and a byte that comes back**.  Here it is tested without a browser, with the
# test client — which is necessary and NOT sufficient (`LESSONS.md`: it is E10,
# the green test on the wrong client).  The browser comes later, with the page.
#
# ⛔ AND WITH THE CHECK THAT SAYS NO, which in the two reviews of 9 Aug fell
#    every time: `RCP.md` §2.2 requires that the server **MUST NOT** accept a
#    session on a different path, and that the refusal be **404** (finding
#    R1.24).  A bench that tests only the right path cannot tell "the server
#    checks the path" from "the server accepts anything".
# ---------------------------------------------------------------------------
set -uo pipefail

ENTER=/media/REMOTIX/enter.sh
OUT=/media/REMOTIX/src
INSIDE=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$INSIDE/b2/ngtcp2/build/examples/bsslserver"
LIBS="$INSIDE/b2/ngtcp2/build/lib"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⚠ Three actions, and they are needed because the BROWSER measurement needs the
#   server to stay up while another script, on the other machine, conducts it.
#   "measure" turns on, tests with the test client and turns off.
ACTION=${1:-measure}
ADDR=${2:-192.168.0.2}
PORT=${3:-7447}
# ⚠ The server's extra options: B3 needs them, raising `max_idle_timeout` to
#   120 s to tell "the server knows a session is detached" from "QUIC closed
#   by itself" (finding R3.19).
# ⛔ `shift 3` with FEWER than three arguments shifts nothing and does not fail
#    in a useful way: `$*` stayed "start", the server received the name of
#    the action as an option and died with "port: invalid port number".
#    Seen on 10 Aug 2026 — and the symptom was a client that "does not
#    connect", that is, the red once again on the wrong suspect.
if [ $# -gt 3 ]; then
	shift 3
	OPTIONS="$*"
else
	OPTIONS=""
fi

# ---------------------------------------------------------------------------
# ⛔ STOPPING BY PID MEANS FIRST LOOKING AT WHICH PID IT IS — finding R8.13.
#
# The PID file may be yesterday's: only whoever stops properly deletes it, and
# an interrupted run leaves it there.  The server's rootfs lives in RAM and gets
# rebooted, while `/media/REMOTIX/src` survives: at reboot PIDs restart from
# the bottom and that number points to **a system process**.  ⛔ Then a `kill`
# was done as root inside the container, with `|| true` hiding even the
# error.
#
# ⭐ The cure costs one read: `/proc/<pid>/comm` gives the program name, and
#    `enter.sh` uses `chroot` and not a PID namespace — the numbers are the
#    same on both sides, so it can be read from here without sudo.
# ⚠ And after the `kill` we CHECK that it is dead, before throwing away the file:
#    deleting it first is losing the only handle we had.
stop_by_pid() # $1 = PID file, $2 = expected program name
{
	local file=$1 expected=$2 p="" comm=""
	[ -f "$file" ] && p=$(cat "$file" 2>/dev/null)
	if [ -z "$p" ]; then
		printf '    --  no server to stop\n'
		return 0
	fi
	if [ ! -d "/proc/$p" ]; then
		printf "    --  PID %s no longer exists: throwing away the file\n" "$p"
		rm -f "$file"
		return 0
	fi
	comm=$(cat "/proc/$p/comm" 2>/dev/null)
	if [ "$comm" != "$expected" ]; then
		ko "⛔ PID $p is now «$comm», not «$expected»: NOT killing it."
		ko "   The file $file is from a previous run, and PIDs get"
		ko "   reused.  Just throwing it away — check yourself what that process is."
		rm -f "$file"
		return 1
	fi
	bash "$ENTER" --root "kill $p"
	local outcome=$?
	if [ "$outcome" -ne 0 ]; then
		ko "the kill of PID $p ($comm) failed (exit $outcome)"
		return 1
	fi
	# ⚠ A successful `kill` is a delivered signal, not a dead process.
	local n=0
	while [ -d "/proc/$p" ] && [ "$n" -lt 10 ]; do
		sleep 1
		n=$((n + 1))
	done
	if [ -d "/proc/$p" ]; then
		ko "PID $p ($comm) is still alive after $n seconds: not throwing away the file"
		return 1
	fi
	rm -f "$file"
	printf '    --  stopped the server (PID %s, %s)\n' "$p" "$comm"
	return 0
}

if [ "$ACTION" = stop ]; then
	stop_by_pid "$OUT/b2-wt.pid" "$(basename "$SERVER")"
	exit $?
fi
if [ "$ACTION" != measure ] && [ "$ACTION" != start ]; then
	ko "unknown action: $ACTION  (measure | start | stop)"
	exit 2
fi

log "Credentials for the container"
bash "$ENTER" --root "true" || { ko "cannot enter the container"; exit 2; }
ok "sudo validated"

# ---------------------------------------------------------------------------
# ⛔ "PORT FREE" AND "I COULD NOT LOOK" ARE NOT THE SAME THING — R8.15.
#
# `CHI=$(bash enter.sh --root "ss | grep …")` captures only standard output, and
# FOUR different outcomes give the same empty string: `enter.sh` failing on a
# mount or on an expired credential, `ss` absent in the chroot, `grep` finding
# nothing, and the port really free.  ⛔ The bench read "I could not look" as
# "there is nothing", launched a second server on top of the first, and the red
# that followed landed on the wrong suspect.  It is the same shape this file
# fights a little further down by choosing `/proc` instead of `kill -0`.
#
# ⭐ The cure: the list is written to a FILE, and the redirection stays inside
#    the quotes of the remote command — never around `enter.sh`, which would
#    carry off sudo's password prompt with it.  Then three distinct things are
#    looked at: the status of `enter.sh`, the status of `ss`, and the content.
#
# Exits 0 = taken · 1 = free · 2 = could not look.
look_port() # $1 = port
{
	local p=$1
	rm -f "$OUT/b2-porte.txt" "$OUT/b2-porte.stato"
	bash "$ENTER" --root \
		"ss -ulnp > $INSIDE/b2-porte.txt 2>&1; echo \$? > $INSIDE/b2-porte.stato"
	local entry=$?
	if [ "$entry" -ne 0 ]; then
		ko "could not look at the ports: enter.sh exited $entry"
		return 2
	fi
	if [ ! -f "$OUT/b2-porte.stato" ] || [ ! -f "$OUT/b2-porte.txt" ]; then
		ko "could not look at the ports: the list was not written"
		return 2
	fi
	local state_ss
	state_ss=$(cat "$OUT/b2-porte.stato")
	if [ "$state_ss" != 0 ]; then
		ko "«ss» inside the container exited $state_ss:"
		sed 's/^/        /' "$OUT/b2-porte.txt"
		return 2
	fi
	grep ":$p " "$OUT/b2-porte.txt" | sed 's/^/        /' && return 0
	return 1
}

log "The port"
look_port "$PORT"
FREE=$?
if [ "$FREE" -eq 2 ]; then
	exit 3
fi
if [ "$FREE" -eq 0 ]; then
	ko "port $PORT is already taken (the list is above)"
	ko "stop it by PID (never with pkill -f) and relaunch"
	exit 3
fi
ok "port $PORT free"

# ---------------------------------------------------------------------------
log "The minimal server (the ngtcp2 example with the WebTransport layer grafted on)"
rm -f "$OUT/b2-wt.log" "$OUT/b2-wt.pid"
bash "$ENTER" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER $OPTIONS $ADDR $PORT $CERT/sessione.key $CERT/sessione.pem < /dev/null > $INSIDE/b2-wt.log 2>&1 & echo \$! > $INSIDE/b2-wt.pid"
sleep 2
PID=$(cat "$OUT/b2-wt.pid" 2>/dev/null)
# ⛔ `/proc`, not `kill -0`: the server belongs to root and this script does not
#    — and as a normal user `kill -0` answers "operation not permitted", that is
#    an error, not "does not exist" (10 Aug 2026).
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "the server did not start.  The log says:"
	sed 's/^/        /' "$OUT/b2-wt.log"
	exit 4
fi
# ⛔ "LISTENING" MEANS "ON THIS PORT" — finding R8.14.
#
#    `grep 'pid=$PID,'` is true for ANY UDP port held by that process: a
#    server that ignored its positional arguments and bound to its own default
#    port passed the check, and the bench printed "listening" on a false fact.
#    It is the necessary taken for sufficient (E1), right in the file that
#    tells of the defect of the crooked arguments.
look_port "$PORT"
HOLDS=$?
if [ "$HOLDS" -eq 2 ]; then
	exit 4
fi
if [ "$HOLDS" -ne 0 ] || ! grep ":$PORT " "$OUT/b2-porte.txt" | grep -q "pid=$PID,"; then
	ko "the server is alive but does NOT hold port $PORT (the list is above)"
	sed 's/^/        /' "$OUT/b2-wt.log"
	exit 4
fi
ok "listening on port $PORT, PID $PID"
inf "what it said at startup:"
grep "REMOTIX B2" "$OUT/b2-wt.log" | head -4 | sed 's/^/        /'

stop_server() {
	# ⚠ Same road as the shutdown: we look at which PID it is, and check
	#   that it is dead before throwing away the file (R8.13).
	stop_by_pid "$OUT/b2-wt.pid" "$(basename "$SERVER")"
}

if [ "$ACTION" = start ]; then
	ok "the server stays on: stop it with «01-b2-launch-wt.sh stop»"
	inf "the fingerprint of the session certificate, for the page:"
	bash "$ENTER" --root \
		"openssl x509 -in $CERT/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0" \
		| tail -1 | sed 's/^/        /'
	exit 0
fi

# ---------------------------------------------------------------------------
log "1. The RIGHT path — /rcp/1"
inf "expected: :status 200, and the bytes come back identical"
bash "$ENTER" --root \
	"python3 $INSIDE/01-b2-aioquic-client.py https://$ADDR:$PORT/rcp/1"
OUTCOME_YES=$?
inf "test client: exit $OUTCOME_YES"

# ---------------------------------------------------------------------------
log "2. ⛔ The WRONG path — /rcp/9, the check that says NO"
inf "expected: 404.  RCP.md §2.2: an unknown path is refused, and"
inf "          finding R1.24 chose 404 among the three statuses that were legitimate."
# ⛔ The number is passed to the client and the client does the comparison —
#    finding R8.8.  Before, only "non-zero exit" was kept, and a CONNECT timeout,
#    filtered UDP or an already dead server gave the same green: the check that
#    says NO did not tell refusal from failure.  Now the expected is **404**,
#    that is what the document asks for, and any other outcome is red.
bash "$ENTER" --root \
	"python3 $INSIDE/01-b2-aioquic-client.py https://$ADDR:$PORT/rcp/9 404"
OUTCOME_NO=$?
inf "test client: exit $OUTCOME_NO (expected: 0, that is «refused with 404»)"

# ---------------------------------------------------------------------------
log "What the server saw"
grep "REMOTIX B2" "$OUT/b2-wt.log" | sed 's/^/        /'

stop_server

log "Outcome"
ALL_GOOD=0
if [ "$OUTCOME_YES" -eq 0 ]; then
	ok "/rcp/1: session opened and bytes came back"
else
	ko "/rcp/1: did NOT work (exit $OUTCOME_YES)"
	ALL_GOOD=1
fi
if [ "$OUTCOME_NO" -eq 0 ]; then
	ok "/rcp/9: REFUSED with 404, as §2.2 requires"
else
	ko "⛔ /rcp/9 was NOT refused with 404 (exit $OUTCOME_NO):"
	ko "   either the server accepts it — and then it is a violation of RCP.md"
	ko "   §2.2 — or the refusal came with another status, or the test"
	ko "   did not even start.  The log above says which."
	ALL_GOOD=1
fi
inf "the complete log stays in $OUT/b2-wt.log"
exit "$ALL_GOOD"
