#!/bin/bash
#
# 01-casa-7448.sh — ⛔ RUNS INSIDE THE CONTAINER.  The «home server»: the
# PRODUCT on port 7448, the one the other benches find running.
#
#   bash /srv/src/01-casa-7448.sh status      who is running, and on which binary
#   bash /srv/src/01-casa-7448.sh build rebuilds from the current sources
#   bash /srv/src/01-casa-7448.sh start
#   bash /srv/src/01-casa-7448.sh stop
#   bash /srv/src/01-casa-7448.sh restart  build + stop + start
#
# ---------------------------------------------------------------------------
# ⛔ WHY IT EXISTS — «THE SERVER IS RUNNING» DOES NOT SAY ON WHAT
#
# `[M]` the night between 11 and 12 Aug 2026: the home server had been running
# **since 08:28** and the binary on disk was from **17:26**.  `readlink /proc/PID/exe`
# said `/srv/src/remotix/remotix (deleted)`, and the two fingerprints were different —
# `53c46311…` running against `abc021cf…` on disk.  ⇒ For thirteen hours
# anyone who queried 7448 would have measured **the product without the
# farewell cures**, believing they were measuring the cured one.
#
# ⚠ And nobody had noticed because the command line had been typed by
#   hand: there was no file to reread, and «it is running» looked like a
#   complete answer.  It is the same shape as the misaligned graft of the
#   same night (`attrezzi-allinea-innesto.sh`, retired 11 Oct 2026, DECISIONI §10.44) and of the trap already paid for
#   on B11 — *«the file is there» and «the file is the one I have just built» are
#   two different questions* (`LEZIONI.md` §1.9 point 8).
#
# ⭐ Hence `status`, which does not ask «is it alive?» but **«is it running the
#    binary that is on disk?»**, and says so by comparing the two fingerprints.
#
# ---------------------------------------------------------------------------
# ⛔ THE COMMAND LINE IS THE ONE THAT WAS RUNNING, COPIED FROM `/proc/PID/cmdline`
#
# Not rebuilt from memory: read from the live process before killing it, on
# 12 Aug 2026.  ⚠ In particular `--page` **is used** here (unlike
# `01-p5-accendi.sh`, which starts from inside the folder on purpose): changing it
# would change the scene the other benches expect.
#
# ⛔ AND THE LOG IS OPENED IN APPEND (`>>`), NEVER TRUNCATED: truncating a log
#    that a process holds open digs a hole of NULs into it that blinds
#    every `grep` (`LEZIONI.md` §1.9 point 9, paid for the same night).
set -uo pipefail

D=${D:-/srv/src/remotix}
TWIN=${TWIN:-/srv/src/rcp}
PORT=${PORT:-7448}
ADDR=${ADDR:-192.168.0.2}

CERT=/srv/src/remotix-cert
BAN=/srv/src/remotix-ban
SOCK=/srv/src/b8-command.sock
LOG=/srv/src/remotix-browser.log
PIDF=/srv/src/remotix-casa.pid

# ⛔ The PID is not looked for with `pgrep -f remotix`: it would take away the servers of
#    the other runs (P5's 7501, B13's 7481).  The port is looked for.
my_pid()
{
	local p
	# ⭐ First the file, which is a written fact; then the command line, for the
	#    servers started by hand before this file existed.
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--port $PORT" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

fingerprint() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

case "${1:-status}" in
status)
	if ! pid=$(my_pid); then
		echo "--  no server on $PORT"
		[ -x "$D/remotix" ] && echo "--  on disk: $(fingerprint "$D/remotix")…  $(stat -c '%y' "$D/remotix" | cut -c1-16)"
		exit 1
	fi
	disk=$(fingerprint "$D/remotix")
	alive=$(fingerprint "/proc/$pid/exe")
	echo "--  pid $pid, started on $(ps -o lstart= -p "$pid" 2>/dev/null | sed 's/^ *//')"
	echo "--  exe: $(readlink "/proc/$pid/exe" 2>/dev/null || echo '⛔ not readable: root is needed')"
	echo "--  running: ${alive:-⛔ not readable}   ·   on disk: ${disk:-⛔ missing}"
	if [ -z "$alive" ]; then
		echo "NO  ⛔ I could not read the running binary: I do NOT say it matches"
		exit 2
	fi
	if [ "$alive" = "$disk" ]; then
		echo "OK  ⭐ it is running the binary that is on disk"
		exit 0
	fi
	echo "NO  ⛔ IT IS RUNNING ANOTHER BINARY: whoever queries $PORT measures"
	echo "    a product different from the one the sources say.  Cure:"
	echo "      bash $0 restart"
	exit 3 ;;
build)
	[ -d "$D" ] || { echo "NO  ⛔ $D is not there"; exit 2; }
	# ⛔ One looks at the builder's OUTCOME, not at the presence of the binary afterwards
	#    (LEZIONI.md §1.9 point 8).
	( cd "$D" && TWIN="$TWIN" bash costruisci.sh ) || {
		echo "NO  ⛔ the build FAILED: I turn nothing off, and the server"
		echo "    that is running stays the previous one — which at least is known"
		exit 3
	}
	echo "OK  built: $(fingerprint "$D/remotix")…"
	exit 0 ;;
stop)
	if ! pid=$(my_pid); then echo "--  there was nothing running on $PORT"; exit 0; fi
	kill "$pid" 2>/dev/null
	g=0
	while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { echo "NO  ⛔ pid $pid did not die"; exit 3; }
	rm -f "$PIDF"
	echo "OK  turned off (pid $pid)"
	exit 0 ;;
start) ;;
restart)
	bash "$0" build || exit 3
	bash "$0" stop     || exit 3
	;;
*) echo "usage: $0 [status|build|start|stop|restart]"; exit 2 ;;
esac

# --- start ---------------------------------------------------------------
command -v ss >/dev/null || { echo "NO  ⛔ «ss» is not there: I did not look at the port, and I do not call it free"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ port $PORT is already taken ($n lines): turn it off first"
	exit 2
fi
[ -x "$D/remotix" ] || { echo "NO  ⛔ $D/remotix is not there: the «build» step is missing"; exit 2; }
[ -f "$D/pagina.html" ] || { echo "NO  ⛔ $D/pagina.html is not there"; exit 2; }

# ⛔ The command line is the one read from /proc/PID/cmdline of the server that
#    was running: it is not "improved" here, or the scene of the other benches changes.
nohup "$D/remotix" --address 0.0.0.0 --name "$ADDR" --port "$PORT" \
      --certificates "$CERT" --page "$D/pagina.html" \
      --ban "$BAN" --command-socket "$SOCK" \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⛔ B0.7: markers, not `sleep`.  «The process is alive» and «the port answers»
#    are two different facts, and whoever comes after needs the second.
g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ the server died right away.  The last lines of the log:"
	tail -5 "$LOG" | sed 's/^/        /'
	exit 3
fi
lines=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
if [ "$lines" -lt 2 ]; then
	echo "NO  ⛔ pid $pid alive but on :$PORT there are $lines listeners: §2.4 wants TWO"
	tail -5 "$LOG" | sed 's/^/        /'
	exit 3
fi
echo "OK  started, pid $pid, $lines listeners on :$PORT after $((g/2)) s"
exec bash "$0" status
