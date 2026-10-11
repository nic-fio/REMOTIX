#!/bin/bash
#
# 02-session-launch.sh — the bench of sub-phase F2.1: the headless GNOME session
# is born, and is born WITH a virtual monitor of the requested size.
#
#   bash 02-session-launch.sh inspect        just looks: touches nothing
#   bash 02-session-launch.sh healthy          starts it WITH --virtual-monitor
#   bash 02-session-launch.sh fault        starts it WITHOUT — the M9 test
#   bash 02-session-launch.sh devices   when the virtual pointer is born
#   bash 02-session-launch.sh stop         Logout(2)
#   bash 02-session-launch.sh certify     healthy → fault → healed
#   bash 02-session-launch.sh as-at-boot  makes it be born again WITHOUT any
#                                            drop-in of this bench: as it is
#                                            after a server reboot
#   bash 02-session-launch.sh guard [...] the guard to put in front of someone
#                                            else's measurement (→ 02-session-guard.sh)
#
# ⛔ IT RUNS ON THE NIC-OS HOST, not inside the container: the graphical session
#    lives there, with real logind, systemd --user and /dev/dri.
#
# ===========================================================================
# ⛔ WHY IT EXISTS, AND IT IS NOT «TO START A SESSION»
# ===========================================================================
#
# Starting a session is something `benches/00-gnome-session.sh`, from phase 0,
# already does.  What that bench does NOT do, and which is the whole reason for this
# file, is ask for the MONITOR:
#
#   ⛔ `00-gnome-session.sh` never names `--virtual-monitor`, nor even
#      `--headless`: it relies on the drop-in that `fondamenta/banco/provision-server.sh`
#      (lines 224-231) writes in /etc/systemd/user, which sets `--headless
#      --no-x11` and **nothing else**.  ⇒ Every session started that way is BLACK.
#
#   ⭐ And it is not a deduction.  `[M]` 12 Aug 2026, opening this round: the
#      GNOME session alive on NIC-OS for two days — gnome-shell 214465,
#      IsSessionRunning true, fifty names on the bus, Nautilus and the Terminal
#      running — answered GetCurrentState with **zero monitors and zero logical
#      monitors**.  The fault of `STUDIES.md` §gnome §13 M9 did not need injecting: it
#      was on the machine already, and nobody had noticed.
#
# ⇒ A phase 2 bench that measured capture on that session would read
#   zero frames and send you looking for the defect inside PipeWire.  This
#   script exists to make that fault IMPOSSIBLE TO MISTAKE: it can switch it
#   on, it can switch it off, and the tool gives it a number of its own.
#
# ===========================================================================
# ⛔ AND A SECOND THING THE BLACK SESSION DOES, WHICH NO DOCUMENT SAID
# ===========================================================================
#
# `[M]` 12 Aug 2026, and I paid for it myself: on a headless session with ZERO
# monitors, `org.gnome.Shell.Screenshot.Screenshot` brings down gnome-shell.
#
#     CRITICAL: cogl_texture_2d_new_with_size: assertion 'width >= 1' failed
#     WARNING : Failed to take screenshot: Failed to create 0x0 texture
#
# and since the unit carries `OnFailure=gnome-session-shutdown.target` with
# `Restart=no`, **the whole session** goes away.  ⇒ The black session is not only
# «alive and black»: it is **fragile**, and falls at the first one who asks it for a
# frame through the Shell.  Whoever saw the session fall in the middle of a
# measurement would look for the defect in their own code.
#
# ===========================================================================
# ⛔ THE DROP-IN: WHERE IT IS WRITTEN, AND WHY NOT WHERE IT SEEMS
# ===========================================================================
#
# `gnome-session` does NOT launch gnome-shell: it starts the user unit
# `org.gnome.Shell@wayland.service`, whose `ExecStart` is fixed.  To change
# the command line a drop-in is needed — and that is what `src/session.c:671` does
# **only for KWin** (read on 12 Aug 2026: the line is exactly
# `if (kind == COMPOSITORE_KWIN && !write_dropin(...))`, and on the GNOME branch
# nobody reads `width` and `height`).
#
# ⭐ Here it is written in `$XDG_RUNTIME_DIR/systemd/user.control/`, as v1 does for
#    KWin, for three reasons:
#      1. no root needed — the unit is a USER unit;
#      2. it disappears by itself at reboot: a bench must not leave configuration
#         on the machine;
#      3. the name starts with `zz-` **on purpose**: the drop-ins of all the
#         folders are applied in FILE NAME order, and in
#         /etc/systemd/user there is already one called
#         `remotix-headless.conf`.  `zz-…` comes after, so it wins.
#
# ⛔ And written is not in force (E1).  After every start the command line of the
#    PROCESS is read back, and if it does not match what was asked, the
#    verdict is DISAGREEMENT (exit 6), not «fine all the same».
#
# ===========================================================================
# ⛔ WHAT THIS BENCH DOES NOT TOUCH, AND HOW IT MAKES SURE
# ===========================================================================
#
# On NIC-OS two wanted servers run, on **7448** and on **7501**, and they are
# not part of this round.  They live inside the container and do not depend on the
# graphical session — but «they do not depend» was a hypothesis until I
# looked, so this script COUNTS their listeners before and after every
# cycle, and if the number drops it stops and says so.
#
# ⭐ And this bench's port, **7511**, does not needs to talk to anybody:
#    it is the LOCK.  A graphical session is one per user (invariant I2):
#    two copies of this bench cycling it together would give two different
#    measurements under the same label.  Whoever cannot take 7511 does not
#    start.
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TOOL=${TOOL:-$HERE/02-session-state.py}
OUTCOMES=${OUTCOMES:-$HERE/02-session-outcomes.jsonl}
SCENE=${SCENE:-$HERE/02-session-scenes}

SIZE=${SIZE:-1920x1080}
LOCK_PORT=${LOCK_PORT:-7511}
PORTS_NOT_TO_TOUCH=${PORTS_NOT_TO_TOUCH:-"7448 7501"}

U=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$U}
LOG=$RUNTIME/remotix-session.log
SHELL_LOG=$RUNTIME/mutter.log
DROPIN_DIR=$RUNTIME/systemd/user.control/org.gnome.Shell@wayland.service.d
DROPIN=$DROPIN_DIR/zz-f21-monitor.conf
# ⛔ The PERSISTENT drop-in, the one written by `fondamenta/banco/provision-server.sh`.
#    Ours lives in $XDG_RUNTIME_DIR and disappears by itself at reboot — which is
#    right for a bench, and is exactly why this other one must be looked at
#    too: if ONLY ours keeps the monitor up, the machine
#    turns black at the first reboot and the defect starts all over again.
PERSISTENT_DROPIN=${PERSISTENT_DROPIN:-/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
expect() { printf '    \033[1;33m⚠\033[0m   %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ THE LOCK ON 7511 — not a listener, a RIGHT TO CYCLE.
# It is held by an `nc`/python process that occupies the port while it lives.
# ---------------------------------------------------------------------------
PID_LOCK=""
take_lock()
{
	python3 -c "
import socket, sys, time
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
try:
    s.bind(('127.0.0.1', $LOCK_PORT))
except OSError as e:
    print('busy: %s' % e); sys.exit(1)
s.listen(1)
print('taken')
sys.stdout.flush()
time.sleep(86400)
" &
	PID_LOCK=$!
	sleep 1
	if ! kill -0 "$PID_LOCK" 2>/dev/null; then
		ko "⛔ port $LOCK_PORT is already taken: another copy of this"
		ko "   bench is cycling the session.  I do not start: two cycles together"
		ko "   would give two different measurements under the same label."
		return 1
	fi
	ok "lock taken on $LOCK_PORT (pid $PID_LOCK)"
	return 0
}
release_lock()
{
	[ -n "$PID_LOCK" ] && kill "$PID_LOCK" 2>/dev/null
	PID_LOCK=""
}
trap molla_lucchetto EXIT

# ---------------------------------------------------------------------------
count_listeners() # $1 = port
{
	ss -tuln | grep -c ":$1\b"
}

neighbors_before()
{
	NEIGHBORS=""
	for p in $PORTS_NOT_TO_TOUCH; do
		NEIGHBORS="$NEIGHBORS $p:$(count_listeners "$p")"
	done
	inf "the neighbours I do not touch, before:$NEIGHBORS"
}

neighbors_after()
{
	local troubles=0 p n expected
	for p in $PORTS_NOT_TO_TOUCH; do
		expected=$(echo "$NEIGHBORS" | tr ' ' '\n' | grep "^$p:" | cut -d: -f2)
		n=$(count_listeners "$p")
		if [ "$n" -lt "${expected:-0}" ]; then
			ko "⛔ on $p the listeners went from $expected to $n:"
			ko "   I touched something that was not mine.  STOPPING EVERYTHING."
			troubles=1
		fi
	done
	[ "$troubles" -eq 0 ] && ok "the two wanted servers are both still up"
	return $troubles
}

# ---------------------------------------------------------------------------
# The environment, built from scratch — the recipe of `session.c:compose_environment`.
#
# ⛔ EMPTY SHELL: `gnome-session.in:3-14` re-executes itself inside a LOGIN shell
#    if `$SHELL` is non-empty and is in /etc/shells, and pulls in
#    `~/.profile`.  The real check is `[ -n "$SHELL" ]`, so empty and
#    absent are both fine — and v1 leaves it ABSENT, because it builds
#    the environment from scratch and does not set SHELL (zero occurrences in `session.c`).
#    Here it is set EMPTY, which is the same thing and shows in `/proc/…/environ`.
#
# ⛔ XDG_SESSION_TYPE=wayland IS NEEDED: the Shell unit carries
#    `ConditionEnvironment=XDG_SESSION_TYPE=wayland` (checked in the file
#    installed on NIC-OS on 12 Aug 2026), and without it the compositor does not
#    start at all — a crippled session, and no line saying why.
start_session()
{
	env -i \
		HOME="$HOME" \
		USER="$(id -un)" \
		PATH=/usr/local/bin:/usr/bin:/bin \
		SHELL= \
		LANG=C.UTF-8 \
		XDG_RUNTIME_DIR="$RUNTIME" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$RUNTIME/bus" \
		XDG_CURRENT_DESKTOP=GNOME \
		XDG_SESSION_DESKTOP=gnome \
		XDG_SESSION_TYPE=wayland \
		setsid --fork sh -c "exec >>'$LOG' 2>&1; exec gnome-session --session=gnome"
}

viva() { pgrep -u "$U" -x gnome-shell >/dev/null; }

# ⛔ The farewell is `Logout(2)`, not `systemctl --user stop`: `gnome-session` does not
#    exit after starting the target, it opens a fifo and sleeps (`STUDIES.md` §gnome §3.2),
#    and `Logout(1)` shows the dialog if an inhibitor exists — in an unattended
#    session nobody answers it.
# ⛔ And it waits for `inactive`, NOT «other than active»: `is-active` passes through
#    `deactivating`, and restarting in there is another first execution
#    (`PHASES.md` §00-ambiente, defect 4 of phase 0).
stop_and_wait()
{
	local expiry=$((SECONDS + ${1:-60})) state
	gdbus call --session -d org.gnome.SessionManager -o /org/gnome/SessionManager \
	    -m org.gnome.SessionManager.Logout 2 >/dev/null
	while [ $SECONDS -lt $expiry ]; do
		state=$(systemctl --user is-active gnome-session-manager@gnome.service)
		case "$state" in
		inactive|failed|unknown)
			if ! viva; then
				systemctl --user reset-failed
				return 0
			fi
			;;
		esac
		sleep 0.5
	done
	return 1
}

should_wait() # waits for an EVENT, with a declared ceiling
{
	local expiry=$((SECONDS + ${1:-60}))
	while [ $SECONDS -lt $expiry ]; do
		if viva && gdbus call --session -d org.gnome.SessionManager \
		    -o /org/gnome/SessionManager \
		    -m org.gnome.SessionManager.IsSessionRunning 2>&1 | grep -q true
		then
			return 0
		fi
		sleep 0.5
	done
	return 1
}

# ---------------------------------------------------------------------------
# ⛔ THREE modes, and the third was born on 12 Aug for a reason that counts more
#    than the other two:
#
#   con    this bench's drop-in ASKS for the monitor           → the healthy scene
#   without  this bench's drop-in does NOT ask for it            → the M9 fault
#   bare   ⭐ NO drop-in of this bench: the session is born with only the
#          PERSISTENT configuration of the machine, that is **as it is after a
#          reboot**.  It is the only way to measure the outcome of a reboot without
#          rebooting the server — which cannot be done, because inside the
#          container two wanted servers run (7448, 7501) and the rootfs lives
#          in RAM.
#
#   ⛔ And «bare» IS NOT A REBOOT, and it must be said every time: it does not prove that /media
#      is remounted, that the rootfs comes back, that someone reruns
#      `provision-server.sh`.  It proves the LAST link — given the persistent
#      configuration, does a newborn session have the monitor? — which is
#      precisely the link that gave way on 10 Aug.  The other links
#      stay `[?]` until a real reboot touches them.
write_dropin() # $1 = "con" | "without" | "bare"
{
	case "$1" in
	con)
		mkdir -p "$DROPIN_DIR"
		cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor $SIZE
CONF
		;;
	senza)
		mkdir -p "$DROPIN_DIR"
		cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11
CONF
		;;
	nudo)
		rm -f "$DROPIN"
		rmdir "$DROPIN_DIR" 2>&1 | grep -v "Directory not empty" || true
		;;
	*) ko "⛔ unknown drop-in mode: $1"; return 1 ;;
	esac
	systemctl --user daemon-reload || return 1
	# ⛔ And it is CHECKED that the drop-in is in force, not that it is written.
	local effect
	effect=$(systemctl --user show -p ExecStart --value org.gnome.Shell@wayland.service)
	inf "ExecStart in force: $effect"
	case "$1:$effect" in
	con:*--virtual-monitor\ $SIZE*) ok "the drop-in WITH monitor is in force" ;;
	senza:*--virtual-monitor*)
		ko "⛔ I asked for WITHOUT and systemd still says --virtual-monitor:"
		ko "   another drop-in wins over mine.  I do not measure."
		return 1 ;;
	senza:*) ok "the drop-in WITHOUT monitor is in force" ;;
	nudo:*--virtual-monitor*)
		ok "with no drop-in of mine the monitor is requested by the PERSISTENT"
		ok "configuration of the machine: it is what will be found at reboot" ;;
	nudo:*)
		expect "⚠ without this bench's drop-ins nobody asks for the monitor:"
		expect "  it is exactly what the machine does after a reboot" ;;
	*)
		ko "⛔ I asked for WITH $SIZE and systemd does not say so: my drop-in"
		ko "   does not win.  I do not measure — a bench that does not impose the scene"
		ko "   measures someone else's scene."
		return 1 ;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ «HEALTHY NOW» IS NOT «HEALTHY AFTER THE REBOOT» — and the difference is said every
#    time, not discovered.
#
# This bench's drop-in lives in `$XDG_RUNTIME_DIR`, which the reboot takes
# away together with the whole rootfs (which on NIC-OS sits in RAM).  If the session has
# the monitor only thanks to it, the machine is healthy **for this power-on** —
# and it is the same half truth as `LESSONS.md` §2.5-bis: a restore is proved
# by rebooting, not by rereading the script.
#
# ⇒ What makes the monitor persistent is `provision-server.sh` §4, which after every
#   reboot must be rerun anyway.  This function checks whether that line is there,
#   and if it is not it says so LOUDLY instead of letting you believe it is done.
# ---------------------------------------------------------------------------
tell_if_not_persistent()
{
	if [ ! -r "$PERSISTENT_DROPIN" ]; then
		expect "⚠ the persistent drop-in is not there or I cannot read it:"
		expect "  $PERSISTENT_DROPIN"
		expect "  ⇒ after a server reboot the session turns BLACK again."
		expect "  It is set right with: bash /media/REMOTIX/provision-server.sh monitor"
		return 1
	fi
	if grep -q -- '--virtual-monitor' "$PERSISTENT_DROPIN"; then
		ok "and it survives the reboot: --virtual-monitor is also in the persistent"
		inf "drop-in ($PERSISTENT_DROPIN), which provision-server.sh rewrites"
		return 0
	fi
	expect "⚠⚠ HEALTHY NOW, BLACK AT THE NEXT REBOOT."
	expect "  ONLY this bench's drop-in keeps the monitor up, and it sits"
	expect "  in \$XDG_RUNTIME_DIR and the reboot takes it away; the persistent one"
	expect "  ($PERSISTENT_DROPIN)"
	expect "  does NOT name --virtual-monitor — and it is the defect that kept this"
	expect "  machine black from 10 to 12 Aug (I7: the protection lives in the"
	expect "  program, not in a configuration line that can get lost)."
	expect "  It is cured with: bash /media/REMOTIX/provision-server.sh monitor"
	return 1
}

remove_dropin()
{
	rm -f "$DROPIN"
	rmdir "$DROPIN_DIR" 2>&1 | grep -v "Directory not empty" || true
	systemctl --user daemon-reload
}

# ⛔ THE COMMAND LINE IS FLAT, AND THE TWO FORMS ARE WRITTEN OUT IN FULL —
#    gap L3, 12 Aug 2026.
#
# There was an array: `local extra=(); [ -n "${2:-}" ] && extra=(--record "$2")`,
# and then `"${extra[@]}"` at the end of the call.  Two lines fewer, and ⛔ the
# call **out of reach of any static check**: `01-b0-chiamate.py` saw a single
# variable where argparse expects an option, could not know whether it
# carried a `--something` inside, and declared it UNKNOWN — neither red nor
# green.  It is the seam that has already made a healthy bench come out red twice:
# B6 on 10 Aug, B7 on the 11th (`01-b0-chiamate.py`, in the header).
#
# ⚠ Repeating the six common words is the price, and it is paid: two readable
#   lines are worth more than one line that no tool can read.
measure() # $1 = label of the scene; $2 = file to record it in (optional)
{
	if [ -n "${2:-}" ]; then
		python3 "$TOOL" --wait "$SIZE" --from-bus \
		    --label "$1" --outcomes "$OUTCOMES" --record "$2"
		return $?
	fi
	python3 "$TOOL" --wait "$SIZE" --from-bus \
	    --label "$1" --outcomes "$OUTCOMES"
	return $?
}

# ---------------------------------------------------------------------------
restart() # $1 = con|without ; $2 = label ; $3 = scene file (optional)
{
	log "I restart the session from scratch, drop-in «$1»"
	if viva; then
		stop_and_wait 60 || { ko "⛔ it did not stop within 60 s"; return 9; }
		ok "session stopped"
	else
		inf "there was no session to stop"
	fi
	write_dropin "$1" || return 9
	: >"$LOG"
	start_session
	if ! should_wait 60; then
		ko "⛔ the session did NOT start within 60 s.  Last lines:"
		tail -n 25 "$LOG" | sed 's/^/        /'
		return 9
	fi
	ok "session started: $(pgrep -a -u "$U" -x gnome-shell | head -1)"
	# ⚠ The Shell takes its name on the bus BEFORE `meta_context_start()`
	#   (`STUDIES.md` §gnome §3.2): the name is not a readiness indicator.  We wait
	#   for GetCurrentState to answer, which is the fact we need.
	sleep 3
	measure "$2" "${3:-}"
	local e=$?
	# ⛔ And it says AT ONCE whether this health is only for today: whoever has just read
	#    «HEALTHY» is exactly who must know that after the reboot it will not be any more.
	[ "$1" = con ] && tell_if_not_persistent
	return $e
}

# ---------------------------------------------------------------------------
# ⛔ WHEN THE VIRTUAL POINTER IS BORN — the question PLAN.md brings here.
#
# The fact measured by probe S7 on 10 Aug: in a GNOME session without
# physical input devices, a client started BEFORE the `libei` pointer
# exists receives nothing — no wheel, no buttons, not even motion.
# Started AFTER, it receives everything.  `[M]` on the ORDER; the CAUSE is `[?]`.
#
# ⭐ And reading Mutter 48.7 the rule becomes stricter than the plan
#    writes it: `ensure_virtual_device()` is called by the handlers of
#    `NotifyPointerMotion*` and `NotifyPointerButton(pressed)`, **not** by
#    `Start()` (`meta-remote-desktop-session.c:290-321, 780-800, 940-960` [R]).
#    ⇒ The pointer is not born when the RemoteDesktop session starts: it is born at
#      the FIRST INJECTED MOTION.  A bench that opened the application after
#      `Start()` but before the first motion would measure the wrong scene
#      believing it had respected the order.
#
# Here the CAUSE `[?]` is measured: does a Wayland client kept alive across the
# birth of the pointer receive a second `wl_seat.capabilities`, or not?
#   · if it does NOT receive it → the plan's explanation holds, and becomes `[M]`;
#   · if it receives it         → the explanation is wrong and the cause is elsewhere.
# The opposite case is written beforehand, as `LESSONS.md` §1.11 wants.
# ---------------------------------------------------------------------------
devices()
{
	local trace=$RUNTIME/f21-seat.log
	log "0. The starting state"
	measure "devices-start"; local e=$?
	if [ "$e" -ne 0 ]; then
		expect "the session is not healthy (exit $e): the device measurement is"
		expect "done anyway, but the number must be read knowing it."
	fi

	log "1. A live Wayland client, kept on ACROSS the birth of the pointer"
	# ⛔ It is the client «started BEFORE» of probe S7: it must stay alive for
	#    the whole measurement, or the order is not being measured — two
	#    different clients are.
	: >"$trace"
	WAYLAND_DEBUG=1 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR="$RUNTIME" \
	    timeout 90 foot -e sleep 85 >>"$trace" 2>&1 &
	local pid_client=$!
	sleep 6
	if ! kill -0 "$pid_client" 2>/dev/null; then
		ko "⛔ the client did not stay alive: without it I measure nothing"
		inf "last lines of the trace:"
		tail -n 15 "$trace" | sed 's/^/        /'
		return 3
	fi
	ok "client alive (pid $pid_client), trace in $trace"

	# ⛔ The three D-Bus steps are NOT done with three `gdbus call`: the
	#    RemoteDesktop session is tied to the CONNECTION that created it, and `gdbus`
	#    opens a new one every time.  Measured on 12 Aug 2026: `Start`
	#    answered «Object does not exist at path» and the pointer was never
	#    born — with step 3 giving NO on a scene that never happened.  The
	#    details are in the header of `02-session-devices.py`.
	python3 "$HERE/02-session-devices.py" --trace "$trace" --outcomes "$OUTCOMES"
	local outcome=$?

	kill "$pid_client" 2>/dev/null
	log "The traces stay in $trace and $trace.dopo"
	return $outcome
}

# ---------------------------------------------------------------------------
# ⛔ THE CERTIFICATION — healthy N → fault M → healed N, with the numbers
#    WRITTEN BEFOREHAND (mandate §3.3, and the rule born on 11 Aug: whoever writes a
#    bench certifies it in the same round).
#
#   expected healthy 0  (HEALTHY)
#   fault injected:     `--virtual-monitor` is removed from the drop-in — that is M9 of
#                       `STUDIES.md` §gnome §13, the fault made on purpose
#   expected fault   1  (BLACK: ZERO MONITORS)
#   expected healed  0
#
# ⛔ And the verdict is not «it turned red»: it must have turned red AT ITS
#    POINT — the mark «BLACK: ZERO MONITORS» and not another.  A bench that
#    turns red for another reason is not certified, it is lucky.
# ---------------------------------------------------------------------------
certify()
{
	local A_HEALTHY=0 A_FAULT=1 FAULT_MARK="BLACK: ZERO MONITORS"
	log "The expectations, WRITTEN BEFORE the round"
	inf "healthy: $A_HEALTHY (HEALTHY) · fault: $A_FAULT ($FAULT_MARK) · healed: $A_HEALTHY"
	inf "requested size: $SIZE"
	neighbors_before

	mkdir -p "$SCENE"

	log "1. The HEALTHY round — the session WITH the monitor"
	restart con "certify-healthy" "$SCENE/healthy.json"; local E_HEALTHY=$?
	log "2. The FAULT — the same session WITHOUT --virtual-monitor (M9)"
	restart senza "certify-fault" "$SCENE/black.json"; local E_FAULT=$?
	log "3. The HEALED — the monitor is put back"
	restart con "certify-healed" "$SCENE/sana-2.json"; local E_RESULT=$?

	log "The verdict, with the three numbers next to it"
	inf "healthy $E_HEALTHY · fault $E_FAULT · healed $E_RESULT"
	local leaks=0
	[ "$E_HEALTHY" -eq "$A_HEALTHY" ] && ok "the healthy one is the expected ($E_HEALTHY)" || {
		ko "⛔ the healthy one is $E_HEALTHY instead of $A_HEALTHY: the subject is broken, and a"
		ko "   bench whose subject is broken is NOT certified"
		leaks=$((leaks+1)); }
	[ "$E_FAULT" -eq "$A_FAULT" ] && ok "the fault is the expected ($E_FAULT = $FAULT_MARK)" || {
		ko "⛔ the fault is $E_FAULT instead of $A_FAULT: either the bench does not see it,"
		ko "   or it is red for another reason"
		leaks=$((leaks+1)); }
	[ "$E_RESULT" -eq "$A_HEALTHY" ] && ok "the healed one goes back to healthy ($E_RESULT)" || {
		ko "⛔ the healed one is $E_RESULT instead of $A_HEALTHY: the fault left"
		ko "   something behind, or the healthy one was not repeatable"
		leaks=$((leaks+1)); }

	neighbors_after || leaks=$((leaks+1))

	if [ "$leaks" -eq 0 ]; then
		printf '\n    \033[1;32m⭐ F2.1 IS CERTIFIED: healthy %s → fault %s (at its point) → healed %s\033[0m\n' \
		    "$E_HEALTHY" "$E_FAULT" "$E_RESULT"
		printf '    --  and it is not «the bench is right»: it is «the bench can see THIS defect».\n'
		return 0
	fi
	printf '\n    \033[1;31m⛔ F2.1 IS NOT CERTIFIED: %s things do not add up\033[0m\n' "$leaks"
	return 1
}

# ---------------------------------------------------------------------------
case "${1:-inspect}" in
inspect)
	# ⛔ Read only: it does not take the lock and touches nothing.
	log "Just looking — I touch nothing"
	neighbors_before
	measure "${2:-guarda}"
	e=$?
	tell_if_not_persistent
	exit $e
	;;
guard)
	# ⛔ The guard to put IN FRONT of someone else's measurement.  It sits in a file of
	#    its own because whoever uses it is not this bench: they are F2.2..F2.6, and they must
	#    be able to slip it in front of their own command without starting anything.
	shift
	exec bash "$HERE/02-session-guard.sh" "$@"
	;;
healthy)      take_lock || exit 2; neighbors_before; restart con "healthy" "${2:-}"; e=$?; neighbors_after || e=9; exit $e ;;
fault)    take_lock || exit 2; neighbors_before; restart senza "fault" "${2:-}"; e=$?; neighbors_after || e=9; exit $e ;;
as-at-boot)
	# ⭐ The PERSISTENCE test without rebooting the server: this bench's
	#    drop-ins are removed and the session is born again with only the
	#    configuration that would be there at reboot anyway.
	take_lock || exit 2
	neighbors_before
	restart nudo "as-at-boot" "${2:-}"; e=$?
	neighbors_after || e=9
	log "What this number says, and what it does NOT say"
	if [ "$e" -eq 0 ]; then
		ok "⭐ a newborn session WITHOUT any drop-in of this bench has"
		ok "   the monitor: the cure lives in the persistent configuration, and"
		ok "   survives the disappearance of \$XDG_RUNTIME_DIR."
	else
		ko "⛔ without this bench's drop-ins the session exits $e: after a"
		ko "   server reboot the machine goes back to this."
	fi
	expect "⚠ and it is NOT a reboot: that /media is remounted, that the rootfs comes back and"
	expect "  that someone reruns provision-server.sh stay [?] until a"
	expect "  real reboot touches them (LESSONS.md §2.5-bis)."
	exit $e
	;;
devices) take_lock || exit 2; devices; exit $? ;;
stop)     take_lock || exit 2; stop_and_wait && { ok "stopped"; exit 0; } || { ko "⛔ it did not stop"; exit 1; } ;;
certify) take_lock || exit 2; certify; exit $? ;;
clean)   remove_dropin; ok "F2.1 drop-in removed: the machine goes back to its own"; exit 0 ;;
*) echo "usage: $0 {guarda|healthy|fault|as-at-boot|devices|stop|certify|clean|guard [...]}" >&2; exit 2 ;;
esac
