#!/bin/bash
#
# 02-child-start.sh — ⛔ IT RUNS ON THE SERVER (NIC-OS), **OUTSIDE** the container,
# and **AS ROOT**.  It switches on the product of `DECISIONS.md` §1.10-bis on **7571**.
#
#   sudo bash /media/REMOTIX/src/02-child-start.sh status
#   sudo bash /media/REMOTIX/src/02-child-start.sh bus
#   sudo bash /media/REMOTIX/src/02-child-start.sh start
#   sudo bash /media/REMOTIX/src/02-child-start.sh stop
#   sudo bash /media/REMOTIX/src/02-child-start.sh restart
#   sudo bash /media/REMOTIX/src/02-child-start.sh fault <uid|blind|off>
#
# ===========================================================================
# ⛔⭐ WHY AS ROOT, AND IT IS THE WHOLE MANDATE IN ONE LINE
#
# `02-montaggio-accendi.sh` starts the server as **nicfio** (uid 1000), and
# declares it: *«it is the uid that owns the session bus and the PipeWire
# socket»*.  ⛔ That server shows anyone who gets in the desktop of `nicfio` —
# even whoever gets in as `prova` — because the stage belongs to the PROCESS.
#
# ⭐ This one starts it as **root**, which is the real regime: root checks with PAM
#    anyone's password, and for every admitted user spawns a **child** that
#    runs as that user and does have the bus.  ⇒ What is seen in the tab is the
#    desktop **of whoever got in**, and no longer that of whoever started it.
#
# ⚠ And the consequence must be said BEFORE, or the scene is judged instead of the product:
#   getting in as `prova` (uid 1001, which on this machine has never logged
#   in) **you see nothing**, and it is not a defect — it is the measurement.  `prova`
#   has no `/run/user/1001`, so it has neither bus nor PipeWire, so it has no
#   stage.  ⛔ The previous server showed it someone else's desktop.
#
# ===========================================================================
# ⛔ THE PORT IS 7571, AND THE OTHER THREE ARE NOT TOUCHED
#
# 7448 (house product), 7501 (P5 target) and ⛔ **7561 (where the user is
# watching their own desktop)** are COUNTED before and after, and must stay as
# they are.  ⚠ Ban, command socket, certificates and log are ITS OWN: two
# servers sharing the ban file would ban each other.
set -uo pipefail

ADDR=${ADDR:-192.168.0.2}
PORT=${PORT:-7571}
D=${D:-/media/REMOTIX/src/02-figlio-src/src}
WORKDIR=${WORKDIR:-/media/REMOTIX/tmp/02-figlio}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
# ⛔ The survey folder is written by **the child**, that is the user: if it were
#    root's the survey would not come out, and the log would say so.  It is made `0777`
#    with the sticky bit, like /tmp, instead of guessing which user will get in.
SURVEY=$WORKDIR/rilievo
CERT=$WORKDIR/certificati
BAN=$WORKDIR/ban
SOCK=$WORKDIR/command.sock
LOG=$WORKDIR/registro.log
PIDF=$WORKDIR/pid

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

fingerprint() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

my_pid()
{
	local p
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--port $PORT" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⛔ The three ports that are NOT mine are counted before and after: if they drop, the round
#    did damage, and damage nobody counts did not happen.
neighbors()
{
	local a b c
	a=$(ss -tuln 2>/dev/null | grep -c ':7448\b')
	b=$(ss -tuln 2>/dev/null | grep -c ':7501\b')
	c=$(ss -tuln 2>/dev/null | grep -c ':7561\b')
	printf '7448: %s · 7501: %s · 7561: %s listeners\n' "$a" "$b" "$c"
}

case "${1:-status}" in
status)
	log "The child server, on $PORT"
	inf "$(neighbors)"
	if ! pid=$(my_pid); then
		ko "no server on $PORT"
		[ -x "$D/remotix" ] && inf "on disk: $(fingerprint "$D/remotix")…"
		exit 1
	fi
	inf "pid $pid, user $(ps -o user= -p "$pid" 2>/dev/null | tr -d ' ')"
	inf "running: $(fingerprint "/proc/$pid/exe")  ·  on disk: $(fingerprint "$D/remotix")"
	log "⭐ The children alive now (asked of /proc, not deduced)"
	# ⛔ They are looked up by their `argv[0]`, which is `remotix-child` and is written by
	#    `children_ensure()`: `pgrep remotix` would also catch the servers of the
	#    other benches, and a bench that counts someone else's processes measures
	#    the machine, not the product.
	matches=0
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		line=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)
		case "$line" in
		*--internal-child*)
			u=$(awk '/^Uid:/{print $2" "$3" "$4" "$5}' "/proc/$f/status" 2>/dev/null)
			g=$(awk '/^Gid:/{print $2" "$3" "$4" "$5}' "/proc/$f/status" 2>/dev/null)
			inf "child pid $f · Uid: $u · Gid: $g · «$line»"
			matches=$((matches+1)) ;;
		esac
	done
	[ "$matches" -eq 0 ] && inf "no child (nobody has got in yet)"
	exit 0 ;;

bus)
	# ⛔⭐ THE CHECK THAT HOLDS UP THE WHOLE MANDATE, MEASURED AGAIN NOW.
	#     `P2-6-montaggio.md` §5.4 measured it once; here it is redone every
	#     round, because a measurement from yesterday is not a measurement from today.
	#     ⭐ And they are TWO: the negative (root does not reach it) and the positive (the user
	#     does) — without the second, the first would only say «gdbus does not work».
	log "root ⟷ the session bus of uid 1000"
	if sudo -n env XDG_RUNTIME_DIR=/run/user/1000 \
	        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
	        gdbus call --session --dest org.freedesktop.DBus \
	        --object-path /org/freedesktop/DBus \
	        --method org.freedesktop.DBus.GetId >/dev/null 2>&1; then
		ko "⛔ root DOES REACH IT: the measurement §1.10-bis rests on no longer holds"
		ko "   on this machine.  ⚠ It is not a red of the product: it is a fact"
		ko "   of the system to be reported to the coordinator."
		outcome_bus=1
	else
		ok "⛔ root does NOT connect to the session bus of uid 1000 (expected)"
		outcome_bus=0
	fi
	log "uid 1000 ⟷ the same bus — the POSITIVE control"
	if setpriv --reuid=1000 --regid=1000 --init-groups \
	        env XDG_RUNTIME_DIR=/run/user/1000 \
	        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
	        gdbus call --session --dest org.freedesktop.DBus \
	        --object-path /org/freedesktop/DBus \
	        --method org.freedesktop.DBus.GetId >/dev/null 2>&1; then
		ok "⭐ uid 1000 DOES REACH IT: the tool can find a bus that is there"
	else
		ko "⛔ not even uid 1000 reaches it: the tool cannot see what is"
		ko "   surely there, so root's «no» above proves nothing"
		outcome_bus=2
	fi
	exit "$outcome_bus" ;;

stop)
	log "Switching off"
	inf "$(neighbors)"
	if ! pid=$(my_pid); then ok "nothing was on on $PORT"; exit 0; fi
	# ⛔ The children are counted BEFORE switching off, to be able to say afterwards whether they
	#    died with it: «the parent is off» and «the children are off» are two
	#    different facts, and the second is the one that counts (no orphan
	#    attached to a user's virtual monitor).
	#
	# ⛔⛔ AND THE **PIDS** ARE TAKEN, NOT THEIR NUMBER — cure of 13 Aug 2026.
	#
	#    The previous line counted, after switching off,
	#    `pgrep -f -- "--internal-child" | wc -l`: that is **EVERYBODY's children**.
	#    ⇒ two defects in a single line, opposite to each other:
	#      · another bench with a live child made this one come out RED with
	#        zero orphans of its own — an accusation against the product that belonged to the neighbour;
	#      · and it could not say whether the orphan was its own, so not even the real
	#        red would have said whose it was.
	#    ⚠ And it switches on **only when two benches run in parallel**, which is
	#      what phase 3 does for a living: until yesterday it was a dormant
	#      defect.
	#
	#    ⭐ The cure is not a smarter `pgrep` — a filter on the command
	#      line would remain a deduction.  The kernel is ASKED who its
	#      own children are **before** killing the parent, the list of
	#      pids is kept, and afterwards **that list** is looked at (`LESSONS.md` §1.6: one does not
	#      deduce, one asks).
	#    ⚠ A pid can be recycled by the kernel between before and after: that is
	#      why it is not enough for `/proc/$f` to exist — it is rechecked that the command
	#      line is still that of a child of ours.
	my_children=""
	before=0
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		line=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)
		case "$line" in
		*--internal-child*) my_children="$my_children $f"; before=$((before+1)) ;;
		esac
	done
	kill "$pid" 2>/dev/null
	g=0
	while [ -d "/proc/$pid" ] && [ "$g" -lt 30 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { ko "pid $pid did not die"; exit 3; }
	rm -f "$PIDF"

	remain=0
	orphans=""
	for f in $my_children; do
		line=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null) || continue
		case "$line" in
		*--internal-child*) remain=$((remain+1)); orphans="$orphans $f" ;;
		esac
	done
	ok "switched off (pid $pid, it had $before children of MINE)"
	if [ "$remain" -eq 0 ]; then
		ok "⭐ and NO child of MINE was left orphaned"
	else
		ko "⛔ $remain children of MINE are still alive:$orphans — they are orphans"
		ko "   attached to somebody's virtual monitor"
		for f in $orphans; do
			printf '        %s  %s\n' "$f" "$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)"
		done
	fi
	# ⚠ The OTHERS' children are counted anyway, and printed as background:
	#   they help understand the machine, and ⛔ do NOT enter the verdict.  Confusing them
	#   with one's own is exactly the defect cured above.
	others=$(( $(pgrep -f -- "--internal-child" 2>/dev/null | wc -l) ))
	inf "on the machine $others «--internal-child» processes remain in all"\
	    "(mine: $remain · of other benches: $((altrui - remain))) — ⚠ background, not verdict"
	inf "$(neighbors)"
	[ "$remain" -eq 0 ] || exit 4
	exit 0 ;;

fault)
	# ⛔⭐ THE FAULT IS A CHILD RUNNING AS THE WRONG USER, and it is injected
	#     into the COPY of the sources, never into the house product.  ⭐ It is healed
	#     by copying the real sources again (`02-child-launch.sh ship`).
	#
	#     They are TWO, and they go together, because the walls are two and independent:
	#
	#       `uid`    skips the `setuid()`: the child stays root.  ⛔ It must
	#                notice BY ITSELF — `getresuid()` after the `exec` — and
	#                exit 42 without touching anything;
	#       `blind`  skips the `setuid()` **and** the child's check.  ⛔ Here
	#                the only wall left is the PARENT, which reads the
	#                credentials stamped by the kernel on every message and
	#                takes down the child.  ⚠ Without this second case, «the parent
	#                checks at every message» would be a line of code that
	#                nobody has ever seen bite.
	F=$D/child.c
	case "${2:-}" in
	uid)
		log "Injecting: the child does NOT drop to the user"
		sed -i 's|^\tif (setuid(pw->pw_uid) != 0)$|\tif (0 \&\& setuid(pw->pw_uid) != 0) /* GUASTO INNESTATO */|' "$F" \
			&& grep -q 'GUASTO INNESTATO' "$F" \
			&& { ok "injected into $F"; exit 0; }
		ko "⛔ the fault was NOT injected: the line is not the one I thought."
		ko "   ⚠ A fault that is not injected and a green bench look the"
		ko "   same, and this exits 2 instead of letting you believe it measured."
		exit 2 ;;
	blind)
		log "Injecting: the child does not drop AND does not notice"
		# ⛔ Two seds, each on ONE single line: a fault that must break an
		#    `if` over two lines gets injected halfway and does not compile — and «does not
		#    compile» and «the fault does not bite» look the same to whoever
		#    looks only at the exit status.
		sed -i 's|^\tif (setuid(pw->pw_uid) != 0)$|\tif (0 \&\& setuid(pw->pw_uid) != 0) /* GUASTO INNESTATO */|' "$F"
		# ⛔ AND THEY ARE THREE, not one: the same check (`getresuid`) lives BEFORE
		#    the `exec` (exits 35 and 36) and AFTER (exit 42).  ⚠ Removing only
		#    one, the child stops at the first anyway — and the PARENT's wall,
		#    which is what this case exists to prove, never bites.
		#    `[M]` 12 Aug 2026: it is precisely what happened in the first
		#    round, and the case would have been «green» without having proved anything.
		sed -i 's|^\t\t_exit(35);$|\t\t(void)0; /* GUASTO CIECO: before the exec */|' "$F"
		sed -i 's|^\t\t_exit(36);$|\t\t(void)0; /* GUASTO CIECO: before the exec */|' "$F"
		sed -i 's|^\t\t_exit(42);$|\t\t(void)0; /* GUASTO CIECO: after the exec */|' "$F"
		if grep -q 'GUASTO INNESTATO' "$F" && [ "$(grep -c 'GUASTO CIECO' "$F")" -eq 3 ]; then
			ok "both injected into $F"
			grep -n 'GUASTO' "$F" | sed 's/^/        /'
			exit 0
		fi
		ko "⛔ the four faults were not all injected: I exit 2, not green"
		exit 2 ;;
	off)
		if grep -q 'GUASTO' "$F"; then
			ko "⛔ there are still faults in $F: it is healed by copying the sources again"
			grep -n 'GUASTO' "$F" | sed 's/^/        /'
			exit 1
		fi
		ok "no fault in $F"
		exit 0 ;;
	*) echo "usage: $0 fault <uid|blind|off>"; exit 2 ;;
	esac ;;

start) ;;
restart) bash "$0" stop || exit 3 ;;
*) echo "usage: $0 [status|bus|start|stop|restart|fault ...]"; exit 2 ;;
esac

# --- start ---------------------------------------------------------------
log "0. The terrain, declared before touching it"
inf "$(neighbors)"
[ "$(id -u)" -eq 0 ] || { ko "⛔ this must be launched AS ROOT: it is the whole point"; exit 2; }
[ -x "$D/remotix" ] || { ko "⛔ $D/remotix is not there"; exit 2; }
[ -f "$D/page.html" ] || { ko "⛔ $D/page.html is not there"; exit 2; }
inf "binary: $D/remotix  ($(fingerprint "$D/remotix")…)"
if grep -q 'GUASTO' "$D/child.c" 2>/dev/null; then
	inf "⚠ WARNING: an injected FAULT is in the sources —"
	grep -n 'GUASTO' "$D/child.c" | sed 's/^/        /'
fi

command -v ss >/dev/null || { ko "⛔ «ss» is not there: I did not look at the port"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
[ "$n" -eq 0 ] || { ko "⛔ port $PORT is already taken ($n lines)"; exit 2; }

mkdir -p "$CERT" "$SURVEY" || { ko "⛔ I could not prepare $WORKDIR"; exit 2; }
chmod 1777 "$SURVEY"
inf "the survey is $SURVEY, mode 1777: THE CHILD writes there, that is the user"

log "1. The libraries: the built ones, not the packaged ones"
export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if ! ldd "$D/remotix" > "$WORKDIR/ldd.txt" 2>&1; then
	ko "⛔ ldd did not finish: I do not say the libraries are there"; exit 2
fi
grep -q 'not found' "$WORKDIR/ldd.txt" && { ko "⛔ a library is missing:";
	grep 'not found' "$WORKDIR/ldd.txt" | sed 's/^/        /'; exit 2; }
for l in libngtcp2 libnghttp3; do
	line=$(grep -m1 "$l" "$WORKDIR/ldd.txt")
	case "$line" in
	*/media/REMOTIX/src/b2/*) ok "$l ← $(printf '%s' "$line" | sed 's/^[[:space:]]*//')" ;;
	*)  ko "⛔ $l does NOT come from the built tree: same soname, another library"
	    exit 2 ;;
	esac
done

log "2. The PAM service on the host"
[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix IS NOT THERE: PAM falls back on"
	ko "   «other» = pam_deny, and EVERY right password will be refused"; exit 2; }
ok "/etc/pam.d/remotix is there"

log "3. The stage the children will find — and WHOSE it is"
for u in 1000 1001; do
	if [ -S "/run/user/$u/bus" ]; then
		ok "uid $u: /run/user/$u/bus is there — a child at this uid will have the bus"
	else
		inf "⚠ uid $u: /run/user/$u/bus is NOT there — a child at this uid"
		inf "   will be born, will SAY SO, and will stay without a stage (it is not a defect:"
		inf "   it is a user who has never logged in on this machine)"
	fi
done

log "4. Switching on — AS ROOT, on $PORT"
# ⛔ The log is opened in APPEND mode, never truncated.
# ⛔ `--verbose` on: the periodic recheck of the children's identity
#    writes there, and without it nothing would be seen (`child.h`, `children_recheck`).
nohup "$D/remotix" --address 0.0.0.0 --name "$ADDR" --port "$PORT" \
      --certificates "$CERT" --page "$D/page.html" \
      --ban-file "$BAN" --command-socket "$SOCK" \
      --survey "$SURVEY" --verbose \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⛔ Markers, not `sleep`.  ⚠ And here start-up is FASTER than the
#   assembly one: the parent no longer captures anything (§1.10-bis), so it waits
#   neither for the 5 s of capture nor for the two encodings.
g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	ko "⛔ the server died at once.  The last lines of the log:"
	tail -20 "$LOG" | sed 's/^/        /'
	exit 3
fi
lines=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
[ "$lines" -ge 2 ] || { ko "⛔ pid $pid alive but $lines listeners: §2.4 wants TWO"
	tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
ok "on, pid $pid, $lines listeners on :$PORT after $((g/2)) s"

log "5. What it said at start-up — and this is the measurement, not the switching on"
grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (startup|child|video) ' "$LOG" \
	| tail -12 | sed 's/^/        /'
inf "$(neighbors)"
exec bash "$0" status
