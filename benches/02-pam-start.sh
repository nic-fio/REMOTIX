#!/bin/bash
# ⭐ UPDATED 25 Oct 2026 (D4b of DECISIONS-11.md §11.50) FOR TODAY'S TREE.  What changed:
#   · it no longer needs the NIC-OS container: every path is a variable with a default that works from a checkout
#     (SRC=<repo>/src, D=$TMPDIR/02-pam-target, TWIN=<repo>/benches/rcp, TMP=$TMPDIR/02-pam-tmp); it must still run as ROOT on a
#     machine that has /etc/pam.d/remotix and the account the bench logs in with (see 02-pam-standstill.py, «HOW TO RUN»);
#   · the FAULT is no longer «the old synchronous fallback, the wire stalls» (that fallback is gone): `fault` now builds a copy whose
#     asynchronous hook is NOT connected, so every login is refused 0x0E, not counted, and the wire never stops;
#   · `kill-helper` is the other fault, at run time: SIGKILL to the helper; the server restarts it by itself (1 s, 2 s, 4 s …), and in
#     the meantime the logins are refused 0x0E (the scene «restart» of 02-pam-standstill.py).
#
# 02-pam-start.sh — ⛔ IT RUNS INSIDE THE CONTAINER.  It switches on THIS BENCH'S
# TARGET: a copy of the product on port 7531, with ban, socket,
# certificates, log and pid file all of its own.
#
#   bash /srv/src/02-pam-start.sh copy     remakes the copy and rebuilds it
#   bash /srv/src/02-pam-start.sh start
#   bash /srv/src/02-pam-start.sh stop
#   bash /srv/src/02-pam-start.sh log  prints the target's log
#
# ---------------------------------------------------------------------------
# ⛔ WHY A TARGET OF MY OWN AND NOT THE HOUSE ONE
#
# On NIC-OS, on 12 Aug 2026, already running are: **7448** (the house product),
# **7501** and **7522** (the targets of P5, from another round).  ⛔ They are
# on on purpose and are not touched.  ⚠ And the rule «a parallel bench has
# its OWN port, ban file and socket» is not zeal: the attempt count of
# §4.4-bis is **per address**, and all the benches of this machine start
# from the same address — whoever shares a ban file with another round locks
# that one out for twelve hours too.
#
# ⭐ The perimeter sits in ONE variable (`PREFIX`), as in `01-p5-accendi.sh`:
#    so no piece of it can be forgotten.  It is the cure born on 12 Aug
#    2026 when ban, socket, log, certificate and **pid file** were
#    written out literally, and a second target would have deleted those of the
#    first — including the `.pid`, that is `stop` would have killed the wrong
#    process.
#
# ---------------------------------------------------------------------------
# ⛔ THE FAULT IS INJECTED INTO THE COPY, NEVER INTO THE HOUSE PRODUCT
#
# The certification of this bench wants the round `healthy -> fault -> healed`,
# and the fault is **the cure removed**: the asynchronous hook not connected, that is
# exactly the state of the server before 12 Aug 2026.  ⛔ Injecting it into the
# product of `/srv/src/remotix` would put it under the feet of anyone else
# who is using it.
#
# ⛔ B0.7: MARKERS, NOT `sleep`.  «The process is alive» and «the port answers»
#    are two different facts, and the measurement needs the second.
set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
SRC=${SRC:-$HERE/../src}
D=${D:-${TMPDIR:-/tmp}/02-pam-target}
TWIN=${TWIN:-$HERE/../benches/rcp}
TMP=${TMP:-${TMPDIR:-/tmp}/02-pam-tmp}
PORT=${PORT:-7531}
ADDR=${ADDR:-127.0.0.1}
PREFIX=${PREFIX:-pam2-7531}

CERT=$TMP/$PREFIX-cert
BAN=$TMP/$PREFIX-ban
SOCK=$TMP/$PREFIX.sock
LOG=$TMP/$PREFIX.log
PIDF=$TMP/$PREFIX.pid

mkdir -p "$TMP"

case "${1:-start}" in
stop)
	if [ -f "$PIDF" ]; then
		pid=$(cat "$PIDF")
		# ⛔ By PID and only its own: `pkill -f remotix` would take away
		#    7448, 7501 and 7522, which belong to others.  ⭐ And a stale pid file
		#    may name a pid that has been REUSED by someone else: the process
		#    must be running THIS target's binary.
		exe=$(readlink "/proc/$pid/exe" 2>/dev/null || true)
		exe=${exe% (deleted)}   # a rebuilt binary is «… (deleted)» while the old one runs
		if [ ! -d "/proc/$pid" ]; then
			printf -- '--  pid %s is not alive: nothing to stop\n' "$pid"
			rm -f "$PIDF" "$SOCK"
			exit 0
		fi
		if [ "$exe" != "$(readlink -f "$D/remotix")" ]; then
			printf 'NO  ⛔ pid %s is not mine (its exe is «%s», not %s): I stop nothing\n' "$pid" "$exe" "$D/remotix"
			exit 2
		fi
		kill "$pid" 2>/dev/null
		g=0
		while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
		[ -d "/proc/$pid" ] && printf 'NO  pid %s did not die\n' "$pid" \
		                    || printf 'OK  switched off (pid %s)\n' "$pid"
		rm -f "$PIDF"
	else
		printf -- '--  no %s: nothing of mine was on\n' "$PIDF"
	fi
	rm -f "$SOCK"
	exit 0 ;;
log)
	[ -f "$LOG" ] || { echo "NO  ⛔ $LOG is not there"; exit 2; }
	cat "$LOG"
	exit 0 ;;
kill-helper)
	# ⛔⭐ IT SITS IN A FILE, AND NOT INSIDE THREE LEVELS OF QUOTES — 12 Aug
	#     2026, and the lesson was already written in `01-p5-accendi.sh`: «a file
	#     has no levels of quotes».  ⚠ Written inside `ssh → enter.sh →
	#     bash -c`, this piece died on a `$(...)`  — and the trouble was not
	#     the error: it was that the case «the helper is dead» ran
	#     anyway, on a LIVE helper, and gave a red to a healthy server.
	#
	# ⛔ And the pid is read from the log OF THIS target: a `pgrep` on
	#    «remotix» would also find 7448, 7501 and 7522, which belong to
	#    others.  ⚠ «I killed it» and «I killed one» are two different
	#    facts.
	[ -f "$LOG" ] || { echo "NO  ⛔ $LOG is not there: I killed nothing"; exit 2; }
	p=$(sed -n 's/.*PAM helper started: pid \([0-9]*\).*/\1/p' "$LOG" | tail -1)
	if [ -z "$p" ]; then
		echo "NO  ⛔ no helper pid in the log: it is not «it died»,"
		echo "    it is «it was never born», and they are two different things."
		exit 2
	fi
	# ⛔⭐ «ALIVE» AND «ZOMBIE» ARE NOT THE SAME THING, AND IN /proc THEY LOOK ALIKE
	#     — 12 Aug 2026, and this check has already given a wrong NO.
	#
	# `[ -d /proc/$p ]` answers «yes» also for a process already dead that its
	# parent has not reaped yet.  ⛔ The bench said «the helper is still
	# alive after SIGKILL» while it had been dead for a second, and the diagnosis pointed
	# at the product.  ⭐ The real state is in the third field of /proc/<pid>/stat:
	# `Z` is a zombie, that is dead.
	alive() # $1 = pid.  0 = really alive, 1 = dead (absent or zombie)
	{
		[ -r "/proc/$1/stat" ] || return 1
		s=$(awk '{print $3}' "/proc/$1/stat" 2>/dev/null)
		[ "$s" = Z ] && return 1
		return 0
	}
	if ! alive "$p"; then
		echo "NO  ⛔ pid $p is not alive ALREADY NOW: the case that follows"
		echo "    would measure a scene I did not prepare."
		exit 2
	fi
	# ⛔ Identity BEFORE the kill (a pid from a log can be reused): the process is called «remotix-pam» (`helper_main()` sets
	#    its name) and its PARENT is this target's server, whose pid is in $PIDF.
	comm=$(cat "/proc/$p/comm" 2>/dev/null)
	ppid=$(sed -n 's/^PPid:[[:space:]]*//p' "/proc/$p/status" 2>/dev/null)
	srv=$(cat "$PIDF" 2>/dev/null)
	if [ "$comm" != "remotix-pam" ] || [ -z "$srv" ] || [ "$ppid" != "$srv" ]; then
		echo "NO  ⛔ pid $p is not mine (comm «$comm», parent «$ppid», this target's server «$srv»): I kill nothing"
		exit 2
	fi
	kill -9 "$p"
	# ⭐ No `sleep 1`: it returns as soon as the death is CONFIRMED (polled every 50 ms, 5 s at most), because the server starts the
	#    helper again after a pause of 1 s and the scene «restart» must still find it down.
	g=0
	while alive "$p" && [ "$g" -lt 100 ]; do sleep 0.05; g=$((g+1)); done
	if alive "$p"; then
		echo "NO  ⛔ pid $p is still ALIVE after SIGKILL (state $(awk '{print $3}' "/proc/$p/stat"))"
		exit 3
	fi
	echo "OK  helper $p killed with SIGKILL: it could not write anything,"
	echo "    and no handler could answer in its place"
	exit 0 ;;
copy)
	[ -d "$SRC" ] || { echo "NO  ⛔ $SRC is not there"; exit 2; }
	# ⛔ The copy is remade from scratch: an old copy answers «I exist» just like
	#    a current one (LESSONS.md §1.9 point 8).
	# ⛔ A guard on the `rm -rf`: $D must be a non-empty path under TMPDIR (or /tmp), not a mountpoint (an sshfs of the repo was once
	#    emptied this way), and neither the checkout nor a parent of it.
	root=$(readlink -f "${TMPDIR:-/tmp}")
	dd=$(readlink -m "$D")
	case "$dd" in "$root"/?*) ;; *) echo "NO  ⛔ D=$D is not under $root: I delete nothing"; exit 2 ;; esac
	if findmnt -rn --mountpoint "$dd" >/dev/null 2>&1; then echo "NO  ⛔ D=$D is a mountpoint: I delete nothing"; exit 2; fi
	case "$(readlink -f "$SRC")/" in "$dd"/*) echo "NO  ⛔ D=$D contains the source tree: I delete nothing"; exit 2 ;; esac
	rm -rf --one-file-system "$dd"
	mkdir -p "$(dirname "$D")"
	cp -a "$SRC" "$D"
	rm -f "$D"/*.o "$D/remotix"
	printf -- '--  copy: %s → %s\n' "$SRC" "$D"
	TWIN="$TWIN" bash "$D/build.sh" || exit 3
	exit 0 ;;
fault)
	# ⛔⭐ THE FAULT, 25 Oct 2026: THE HELPER'S HOOK IS NOT CONNECTED.  Until D4b this was «the cure removed» — the server fell back
	#     on a SYNCHRONOUS PAM call and the wire stalled for 1-2 s.  That fallback is gone: a server whose asynchronous hook is
	#     not connected now refuses EVERY login with 0x0E (SESSION_UNSERVABLE, «our defect»), after the fixed second, not
	#     counted towards the ban, and the wire never stops.  It is the state «no helper», and the scene
	#     `02-pam-standstill.py --wait unchecked` expects exactly that (20 refusals in a row, never 0x07, never 0x08).
	#
	# ⛔ What it proves: that the bench can SEE the difference.  A bench that stayed green with a healthy server in the place of this
	#    one would be blind (`CODER.md` §4.6).
	#
	# ⚠ It is injected into the COPY (`$D`), never into the product or the checkout.
	[ -f "$D/webtransport.c" ] || { echo "NO  ⛔ $D/webtransport.c is not there"; exit 2; }
	python3 - "$D/webtransport.c" <<'FINE'
import sys
p = sys.argv[1]
t = open(p).read()
anchor = "\tif (w->help)\n\t\tg.ask_verify = hook_ask;\n"
if t.count(anchor) != 1:
    print("NO  ⛔ the anchor is not unique (%d times): I inject nothing" % t.count(anchor))
    sys.exit(2)
fault = ("\t/* REMOTIX 02-PAM FAULT — the asynchronous hook NOT connected: no helper.\n"
         "\t * rcp.c refuses every login as OURS (0x0E), not counted.\n"
         "\t * If 02-pam-standstill.py --wait unchecked stays green on a HEALTHY server, it is blind. */\n"
         "\tstatic const char rx_fault_mark[] __attribute__((used)) = \"REMOTIX-02-PAM-FAULT-BUILD\";\n")
open(p, "w").write(t.replace(anchor, fault, 1))
print("OK  fault injected: the asynchronous hook is no longer connected")
FINE
	[ $? -eq 0 ] || exit 3
	TWIN="$TWIN" bash "$D/build.sh" >/dev/null 2>&1 \
		|| { echo "NO  ⛔ the rebuild with the fault failed"; exit 3; }
	# ⛔ And it is CHECKED in the BINARY, not only in the source: the injected statement carries a string
	#    (`rx_fault_mark`, kept by `used`) that only a build WITH the fault contains; «I wrote it» and «it is inside what runs»
	#    are two different facts.
	if grep -a -F -q "REMOTIX-02-PAM-FAULT-BUILD" "$D/remotix" \
	   && ! grep -a -F -q "g.ask_verify = hook_ask" "$D/webtransport.c"; then
		echo "OK  ⛔ rebuilt WITH the fault: $(sha256sum "$D/remotix" | cut -c1-16)…"
	else
		echo "NO  ⛔ the fault is not where it should be"
		exit 3
	fi
	exit 0 ;;
start) KEEP_BAN=0 ;;
restart)
	# ⛔⭐ AND THIS STEP EXISTS BECAUSE OF A RED THE BENCH HAD GIVEN ITSELF
	#     — 12 Aug 2026, and the first suspect was the bench (`REVIEWER.md` §1).
	#
	# `start` deletes the ban file, and rightly so: a round must start from
	# a KNOWN state, and a ban inherited from the previous round would make it measure
	# `TOO_MANY_ATTEMPTS` where PAM was meant to be measured.  ⛔ But the case
	# «the ban survives the restart» (invariant **I7**) is proved by SWITCHING OFF AND
	# ON AGAIN, and with that `rm` it always said no — **full red on a
	# product that does keep the ban**.
	#
	# ⚠ It is the form of `LESSONS.md` §1.9: the bench was measuring its own leg and
	#   the diagnosis pointed at the server.  ⭐ Now the two steps are two, and the
	#   name says which state is being asked for.
	KEEP_BAN=1 ;;
*) echo "usage: $0 [copy|fault|start|restart|stop|log|kill-helper]"; exit 2 ;;
esac

# ⛔ A HEALTHY target lets the scenes log in for real: a desktop is born for the account, the render grant and the card groups are
#    written (/var/lib/remotix, `usermod`), logind and /dev/dri are touched.  That is for the THROWAWAY container only.  The faulty
#    copy (`fault`) never logs anybody in and is safe anywhere.
if [ ! -e /run/.containerenv ] && [ "${I_KNOW_IT_IS_THE_HOST:-0}" != 1 ] \
   && ! grep -a -F -q "REMOTIX-02-PAM-FAULT-BUILD" "$D/remotix" 2>/dev/null; then
	echo "NO  ⛔ this is not a container (/run/.containerenv is not there) and the target is HEALTHY: it would touch /var/lib/remotix,"
	echo "    usermod, logind and /dev/dri of this machine.  Run it in the throwaway container, or set I_KNOW_IT_IS_THE_HOST=1."
	exit 2
fi
command -v ss >/dev/null || { echo "NO  ⛔ «ss» is not there: I did not look at the port, and I do not call it free"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ port $PORT is already taken ($n lines): it is not mine, I do not touch it"
	ss -tuln | grep ":$PORT\b"
	exit 2
fi
echo "OK  port $PORT free (ss looked and printed $n lines about it)"

[ -x "$D/remotix" ] || { echo "NO  ⛔ $D/remotix is not there or not executable — the «copy» step is missing"; exit 2; }
[ -f "$D/page.html" ] || { echo "NO  ⛔ $D/page.html is not there: the server would serve nothing"; exit 2; }
echo "--  binary   : $(sha256sum "$D/remotix" | cut -c1-16)…  $(stat -c '%y' "$D/remotix")"

# ⛔ AND BEFORE DELETING ANYTHING, IT CHECKS WHETHER IT BELONGS TO SOMEONE ELSE ALIVE.
if [ -f "$PIDF" ] && [ -d "/proc/$(cat "$PIDF" 2>/dev/null)" ]; then
	echo "NO  ⛔ «$PIDF» says pid $(cat "$PIDF"), and it is ALIVE: another target"
	echo "    with this same prefix («$PREFIX») is already on."
	exit 2
fi
if [ "${KEEP_BAN:-0}" = 1 ]; then
	rm -f "$LOG" "$PIDF" "$SOCK"
	echo "--  ⚠ the ban file is NOT deleted: it is the «restart» step, and"
	echo "    that file IS the thing to prove (I7, §4.4-bis)"
	[ -f "$BAN" ] && echo "--  bans before the restart: $(wc -l < "$BAN") lines in $BAN" \
	              || echo "--  ⛔ $BAN IS NOT THERE: it is not «zero bans», it is «there was nothing to keep»"
else
	rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.new"
fi
mkdir -p "$CERT"
# ⭐ It is started FROM INSIDE its folder: the product looks for `page.html`
#    next to itself.
cd "$D" || exit 3
# ⭐ 1.5: split is the default as root — this bench is about the single process (it starts the server by hand): --no-split.
nohup ./remotix --address 0.0.0.0 --no-split --name "$ADDR" --port "$PORT" \
      --certificates "$CERT" \
      --ban-file "$BAN" --command-socket "$SOCK" --verbose \
      > "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ the server died at once.  The log says:"
	sed 's/^/        /' "$LOG"
	exit 3
fi
lines=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
if [ "$lines" -lt 2 ]; then
	echo "NO  ⛔ process $pid is alive but on :$PORT there are $lines listeners."
	echo "    §2.4 wants TWO — UDP for RCP, TCP for the page."
	sed 's/^/        /' "$LOG"
	exit 3
fi
# ⛔ And the PAM service is checked in the server's LOG, not from memory: without
#    /etc/pam.d/remotix every right password is refused, and this bench
#    would measure a scene in which NOBODY gets in — that is a green number because
#    there was nothing to block.
if grep -q "DOES NOT EXIST" "$LOG"; then
	echo "NO  ⛔ the server says /etc/pam.d/remotix is not there: every right"
	echo "    password would be refused, and this bench's scene does not exist."
	exit 3
fi
echo "OK  on, pid $pid, $lines listeners on :$PORT after $((g/2)) s of waiting"
echo "--  log: $LOG · ban: $BAN · socket: $SOCK"
