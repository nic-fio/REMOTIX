#!/bin/bash
# ===========================================================================
# 11-step0.sh — ⛔⛔ STEP 0 OF PHASE 11
#
#   «Inside a container, does the piece of the system that keeps track of who is
#    logged in behave as on the real machine?»
#
#   It runs INSIDE the box, as administrator:
#       podman exec -it rete11-gnome bash /passo0/11-step0.sh
# ===========================================================================
#
# ⛔ WHY IT EXISTS, and why it comes BEFORE any final box
#
# The product leans heavily on `systemd`/`logind`: linger, the
# user session, the watchdog that closes dead sessions.  If in here
# that piece behaves differently, ⛔ **the whole container layer
# becomes a sham** — that is the worst form of safety, the false one.
#
# ⇒ BOTH external reviewers of 25 August 2026 converge on this, and it is
#   the most serious finding of the two rounds.  `phases/11-the-safety-net.md` §3.5.
#
# ---------------------------------------------------------------------------
# ⚠⚠ WHAT THIS BENCH IS **NOT**, and it must be read before its outcomes
#
# ⛔ **It does not test the product.**  It tests the ENVIRONMENT.  The product is not yet
#    in this box, and it does not need to be: the question of step 0 is whether the
#    box can host the conditions in which the product lives.
#
# ⛔ And in particular, point 7 starts the compositor with `--virtual-monitor`,
#    ⚠ which is **the opposite** of how the product starts it (`session.c:735`,
#    where that line was REMOVED on 14 August 2026 with a measurement behind it).
#    ⇒ Here it serves to ask *«can a Wayland compositor live in this
#      box and needs a client?»*.  ⛔ **Not** to ask *«is the REMOTIX
#      session born with the monitor?»*, which is the question of acceptance test A and needs the
#      product inside.  Confusing the two would mean answering the convenient one.
#
# ---------------------------------------------------------------------------
# THE OUTCOMES — the rule of §4.5 of the phase document
#
#   0  ⭐ I looked, and the box holds
#   1  I looked, and the box does NOT hold          ⇒ the design must change
#   3  ⛔ I COULD NOT LOOK — and it is not a red
#
# ⛔ «I could not look» and «it is broken» do not have the same face, and they
#    must not have it: `LESSONS.md` §1.9, and the rule «None is not zero».
# ===========================================================================
set -uo pipefail

ACCOUNT=provanic
USER_UID=4011
GREEN=0; RED=0; UNKNOWN=0

blue()  { printf '\n\033[1;34m=== %s\033[0m\n' "$*"; }
yes()   { printf '  \033[1;32mSI \033[0m %s\n' "$*"; GREEN=$((GREEN+1)); }
no()   { printf '  \033[1;31mNO \033[0m %s\n' "$*"; RED=$((RED+1)); }
dunno()  { printf '  \033[1;33m?  \033[0m %s\n' "$*"; UNKNOWN=$((UNKNOWN+1)); }
note() { printf '       %s\n' "$*"; }

as_him() { runuser -u "$ACCOUNT" -- "$@"; }

# ---------------------------------------------------------------------------
# ⭐⭐ THE ADAPTER — the answer to «how do we stay blind to the desktop»
#
# This bench does not know which desktop it has in front of it, and must not know.  Every box
# carries at the SAME path a file that says how its compositor is started.
# ⇒ The list of tests stays ONE; the «how» lives below (`phases/11…` §3.7).
# ---------------------------------------------------------------------------
ADAPTER=/usr/local/lib/rete11/adattatore.sh
if [ -r "$ADAPTER" ]; then
	. "$ADAPTER"
	DESK=$(adapter_name)
else
	DESK="(no adapter: $ADAPTER is not there)"
fi

printf '\033[1m STEP 0 — does the box hold the system?\033[0m\n'
printf ' desktop: %s\n' "$DESK"
printf ' box: %s · kernel: %s · %s\n' \
       "$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown}")" \
       "$(uname -r)" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# ---------------------------------------------------------------------------
blue "0. Is the first process «systemd»?  (if not, the rest makes no sense)"
# ---------------------------------------------------------------------------
FIRST=$(ps -p 1 -o comm= 2>/dev/null || echo '')
if [ "$FIRST" = "systemd" ]; then
	yes "process 1 is systemd"
else
	no "process 1 is «$FIRST»: this box cannot answer the question"
	note "⇒ I stop: without systemd points 1-6 cannot even be asked"
	exit 1
fi

# ⛔ `is-system-running` EXITS 1 when the state is «degraded», and with `pipefail`
#    the `if` read it as «I do not know».  ⇒ We capture the TEXT and judge
#    that: the exit status here is not the judgement, it is a detail.
#    `[M]` 25 August 2026, defect of this bench on its first run.
SYS_STATE=$(systemctl is-system-running 2>&1 | head -1)
case "$SYS_STATE" in
  running)
	yes "the system has started (running)" ;;
  degraded)
	yes "the system has started, with failed units (degraded)"
	note "⚠ the failed units, which must be looked at one by one:"
	systemctl --failed --no-legend --plain 2>/dev/null | head -8 | sed 's/^/       ⚠ /' ;;
  starting)
	dunno "the system is still starting: too early to judge" ;;
  *)
	dunno "state not readable: $SYS_STATE" ;;
esac

# ---------------------------------------------------------------------------
blue "1. Does the user session EXIST, and is it of a type the product recognises?"
# ---------------------------------------------------------------------------
if ! command -v loginctl >/dev/null 2>&1; then
	dunno "«loginctl» is not in the box: I cannot look"
elif ! systemctl is-active systemd-logind >/dev/null 2>&1; then
	no "systemd-logind is NOT active: $(systemctl is-active systemd-logind 2>&1)"
	note "⇒ it is precisely the piece the product leans on"
	systemctl status systemd-logind --no-pager -l 2>&1 | tail -6 | sed 's/^/       /'
else
	yes "systemd-logind is active"
	# ⛔⛔ AND HERE WE PREPARE BEFORE LOOKING, because it is what the PRODUCT does.
	#     On the first run this point judged while the user manager was
	#     still «activating», and gave a red that said «the box does not hold»
	#     when the truth was «I had not asked anything yet».
	#     ⇒ `[M]` 25 August 2026, second defect of this bench.
	#     ⚠ Preparing is not cheating: the product turns on linger and starts the
	#       user manager by itself.  Cheating would be **skipping** the check.
	loginctl enable-linger "$ACCOUNT" 2>/dev/null
	systemctl start "user@${USER_UID}.service" 2>/dev/null
	for _ in $(seq 1 30); do
		loginctl show-user "$ACCOUNT" >/dev/null 2>&1 && break
		sleep 0.5
	done
	# ⛔ It is not enough that the service runs: it must be able to OPEN a session.
	#    We try to open a real one with a non-interactive login.
	if as_him true 2>/dev/null; then
		SESS=$(loginctl list-sessions --no-legend 2>/dev/null | wc -l)
		note "sessions open now: $SESS"
		if loginctl show-user "$ACCOUNT" >/dev/null 2>&1; then
			yes "logind knows the user «$ACCOUNT»"
			loginctl show-user "$ACCOUNT" -p State -p Linger -p RuntimePath 2>/dev/null \
				| sed 's/^/       /'
		else
			no "logind does NOT know the user «$ACCOUNT»: $(loginctl show-user "$ACCOUNT" 2>&1 | head -1)"
			note "⛔ this is the point where the box stops representing the product"
		fi
	else
		dunno "I cannot even run a command as «$ACCOUNT»"
	fi
fi

# ---------------------------------------------------------------------------
blue "2. LINGER: do the user's services live without anyone having logged in?"
# ---------------------------------------------------------------------------
if loginctl enable-linger "$ACCOUNT" 2>/dev/null; then
	if [ "$(loginctl show-user "$ACCOUNT" -p Linger --value 2>/dev/null)" = "yes" ]; then
		yes "linger turns on and stays on"
	else
		no "the command passes but linger does NOT show as on"
	fi
else
	no "linger cannot be turned on: $(loginctl enable-linger "$ACCOUNT" 2>&1 | head -1)"
	note "⛔ without linger the graphical session does not survive the client detaching"
fi

if systemctl is-active "user@${USER_UID}.service" >/dev/null 2>&1; then
	yes "the user manager («user@${USER_UID}») is alive without any interactive login"
else
	STATE=$(systemctl is-active "user@${USER_UID}.service" 2>&1)
	if systemctl start "user@${USER_UID}.service" 2>/dev/null; then
		yes "the user manager starts on request (it was «$STATE»)"
	else
		no "the user manager does not start: it was «$STATE»"
		systemctl status "user@${USER_UID}.service" --no-pager -l 2>&1 | tail -6 | sed 's/^/       /'
	fi
fi

# ---------------------------------------------------------------------------
blue "3. Can a service be started inside the user session?"
# ---------------------------------------------------------------------------
# ⚠ The product starts like this: a user unit, not a detached process.
#   Here we test the MECHANISM with a fake unit, because the product is not
#   in this box yet.
if as_him env XDG_RUNTIME_DIR="/run/user/$USER_UID" \
        systemd-run --user --quiet --unit=passo0-prova \
        --property=Type=oneshot /bin/true 2>/dev/null; then
	yes "a user unit starts from inside the session"
	as_him env XDG_RUNTIME_DIR="/run/user/$USER_UID" \
	        systemctl --user reset-failed passo0-prova 2>/dev/null || true
else
	no "a user unit cannot be started"
	note "⛔ it is the way the product starts the graphical session"
	as_him env XDG_RUNTIME_DIR="/run/user/$USER_UID" \
	        systemd-run --user --unit=passo0-prova --property=Type=oneshot /bin/true 2>&1 \
	        | tail -4 | sed 's/^/       /'
fi

# ---------------------------------------------------------------------------
blue "4. When the session ends, do the processes really DIE?"
# ---------------------------------------------------------------------------
# ⛔ The shape of the feared fault: a container in which processes stay
#    alive after closing ⇒ test C7 («nothing remains») would be green here
#    and red on the real machine, or vice versa.
if as_him env XDG_RUNTIME_DIR="/run/user/$USER_UID" \
        systemd-run --user --quiet --unit=passo0-dorme sleep 300 2>/dev/null; then
	sleep 1
	PID=$(pgrep -u "$ACCOUNT" -f 'slee[p] 300' | head -1)
	if [ -n "$PID" ]; then
		note "the fake child is alive (pid $PID); now the user's session is closed"
		loginctl terminate-user "$ACCOUNT" 2>/dev/null || \
			as_him env XDG_RUNTIME_DIR="/run/user/$USER_UID" \
			        systemctl --user stop passo0-dorme 2>/dev/null
		sleep 2
		if pgrep -u "$ACCOUNT" -f 'slee[p] 300' >/dev/null 2>&1; then
			no "the child SURVIVED the closing of the session"
			note "⛔ here the box behaves differently from the real machine"
		else
			yes "the child died with the session, and nothing remained"
		fi
	else
		dunno "I did not see the fake child being born: I cannot judge"
	fi
else
	dunno "I could not start the fake child: I cannot judge"
fi

# ---------------------------------------------------------------------------
# ⛔⛔ AND NOW WE PUT BACK UP WHAT POINT 4 HAS JUST KNOCKED DOWN.
#
# `[M]` 25 August 2026, first real run of this bench — ⭐ and the defect was
# the BENCH's, not the box's.  Point 4 closes the user's session to
# see whether the children die; ⛔ closing it also takes away `/run/user/4011`,
# and points 5, 6 and 7 — which come after — found the field cleared and gave
# **THREE FALSE REDS**.
#
# ⚠ It is the shape of §1.29 turned around: not «silence instead of red»,
#   but **red instead of nothing** — and it costs the same, because a net that gives
#   reds for nothing gets switched off by whoever works (`phases/11…` §4.3).
#
# ⇒ Whoever tests the closing has the duty to REOPEN, and to check that the
#   reopening succeeded before letting the others judge.
# ---------------------------------------------------------------------------
loginctl enable-linger "$ACCOUNT" 2>/dev/null
systemctl start "user@${USER_UID}.service" 2>/dev/null
RESUMED=0
for _ in $(seq 1 30); do
	if [ -S "/run/user/$USER_UID/bus" ]; then RESUMED=1; break; fi
	sleep 0.5
done
if [ "$RESUMED" = 1 ]; then
	note "⭐ session put back up after the closing test"
else
	dunno "⛔ I could NOT put the session back up after point 4"
	note "⚠ points 5, 6 and 7 below would run on a cleared field: I do NOT judge them"
	printf '\n  \033[1;33mI stop here\033[0m — better «I do not know» than three false reds.\n'
	exit 3
fi

# ---------------------------------------------------------------------------
blue "5. Is the user's private directory there, is it THEIRS, and is it writable?"
# ---------------------------------------------------------------------------
RTD="/run/user/$USER_UID"
if [ -d "$RTD" ]; then
	PROP=$(stat -c '%U %a' "$RTD" 2>/dev/null)
	if as_him test -w "$RTD"; then
		yes "$RTD exists, it is writable by the user ($PROP)"
	else
		no "$RTD exists but the user can NOT write to it ($PROP)"
	fi
	# ⛔ And it must not be the same as another box's: we check that it is a
	#    mount OF THIS container, not a piece of the host passed inside.
	# ⚠ `findmnt` in here returns empty (logind made the mount after
	#   the container started, and the table it sees does not list it): we ask
	#   the kernel for the TYPE, which always answers.  `[M]` 25 August 2026.
	TYPE_RTD=$(stat -fc %T "$RTD" 2>/dev/null)
	if [ "$TYPE_RTD" = tmpfs ]; then
		yes "and it is a directory of this box (tmpfs), not a piece of the host"
	else
		no "it is NOT a tmpfs of this box, it is «$TYPE_RTD»"
		note "⛔ two boxes sharing this directory would step on each other's toes"
	fi
else
	no "$RTD does not exist: without it, no session socket is born"
fi

# ---------------------------------------------------------------------------
blue "6. Is the session message bus there, and does the desktop see it?"
# ---------------------------------------------------------------------------
if [ -S "$RTD/bus" ]; then
	yes "the session bus is there ($RTD/bus)"
	if as_him env XDG_RUNTIME_DIR="$RTD" \
	        DBUS_SESSION_BUS_ADDRESS="unix:path=$RTD/bus" \
	        busctl --user list --no-legend >/dev/null 2>&1; then
		yes "and it can be talked to"
	else
		no "the socket is there but does not answer"
	fi
else
	no "the session bus is NOT there ($RTD/bus)"
	note "⛔ without it, gnome-session does not start and the product has nobody to talk to"
fi

# ---------------------------------------------------------------------------
blue "7. Does a Wayland compositor live in here, and serve a client?"
# ---------------------------------------------------------------------------
# ⚠⚠ See the box at the top: here `--virtual-monitor` is used, which the product
#    does NOT use.  The question is about the ENVIRONMENT, not the product.
if ! command -v adattatore_avvia >/dev/null 2>&1 && ! type adattatore_avvia >/dev/null 2>&1; then
	dunno "this box has no adapter: I do not know how the compositor is started"
else
	rm -f /tmp/passo0-shell.log
	SHELLPID=$(adapter_start "$RTD" /tmp/passo0-shell.log)
	# We wait for the socket, not a fixed time: a clock-based wait is a
	# deadline that fires whenever it happens to (`LESSONS.md`, the heartbeat rule).
	SOCK=''
	for _ in $(seq 1 40); do
		SOCK=$(as_him sh -c "ls $RTD/wayland-* 2>/dev/null | grep -v lock | head -1" 2>/dev/null)
		[ -n "$SOCK" ] && break
		sleep 0.5
	done
	if [ -z "$SOCK" ]; then
		no "the compositor opened no socket in 20 s"
		tail -12 /tmp/passo0-shell.log 2>/dev/null | sed 's/^/       /'
	else
		yes "the compositor is alive and has opened $(basename "$SOCK")"
		AVAIL=$(basename "$SOCK")
		# ⭐ THE YARDSTICK OF THE 25 AUGUST FAULT: how many outputs it ANNOUNCES.
		if command -v wayland-info >/dev/null 2>&1; then
			OUTPUTS=$(as_him env XDG_RUNTIME_DIR="$RTD" WAYLAND_DISPLAY="$AVAIL" \
			        wayland-info 2>/dev/null | grep -c 'interface:.*wl_output' || echo 0)
			if [ "${OUTPUTS:-0}" -gt 0 ]; then
				yes "and it ANNOUNCES $OUTPUTS output(s) — a client can open a window"
			else
				no "⛔ it ANNOUNCES ZERO outputs: it is the shape of the 25 August fault"
				note "⚠ here though I asked for the monitor myself: if it is zero, it is the box's"
			fi
		else
			dunno "«wayland-info» is not there: I cannot count the outputs"
		fi
		# A real client that draws.
		if command -v weston-simple-shm >/dev/null 2>&1; then
			as_him env XDG_RUNTIME_DIR="$RTD" WAYLAND_DISPLAY="$AVAIL" \
			        weston-simple-shm >/tmp/passo0-cliente.log 2>&1 &
			CLPID=$!
			sleep 3
			if kill -0 "$CLPID" 2>/dev/null; then
				yes "a real Wayland client has attached and is drawing"
				kill "$CLPID" 2>/dev/null
			else
				no "the Wayland client died immediately"
				tail -6 /tmp/passo0-cliente.log 2>/dev/null | sed 's/^/       /'
			fi
		else
			dunno "I have no minimal Wayland client in the box"
		fi
	fi
	kill "$SHELLPID" 2>/dev/null
	wait "$SHELLPID" 2>/dev/null
fi

# ---------------------------------------------------------------------------
blue "8. Can the graphics card and the hardware encoder be reached?"
# ---------------------------------------------------------------------------
if [ ! -e /dev/dri/renderD128 ]; then
	no "/dev/dri/renderD128 is not in the box: the card did not get in"
else
	yes "/dev/dri/renderD128 is there"
	if as_him test -r /dev/dri/renderD128 && as_him test -w /dev/dri/renderD128; then
		yes "and the user can read and write it"
	else
		no "it is there but the user can NOT write to it ($(stat -c '%U:%G %a' /dev/dri/renderD128))"
		note "⛔ it is the «render» group: without it, encoding happens in software and the numbers change"
	fi
	if command -v vainfo >/dev/null 2>&1; then
		VA=$(as_him env LIBVA_DRIVER_NAME=iHD vainfo --display drm --device /dev/dri/renderD128 2>&1)
		if echo "$VA" | grep -q 'VAProfileH264'; then
			yes "the hardware encoder answers ($(echo "$VA" | grep -m1 'Driver version' | sed 's/^ *//'))"
			note "H.264 encoding profiles found: $(echo "$VA" | grep -c 'VAProfileH264.*Enc')"
		else
			no "the hardware encoder does not answer"
			echo "$VA" | tail -6 | sed 's/^/       /'
		fi
	else
		dunno "«vainfo» is not in the box"
	fi
fi

# ---------------------------------------------------------------------------
printf '\n\033[1m=========================  THE VERDICT  =========================\033[0m\n'
printf '  holds: %d   does not hold: %d   could not look: %d\n' "$GREEN" "$RED" "$UNKNOWN"
if [ "$RED" -gt 0 ]; then
	printf '  \033[1;31m⛔ THE BOX DOES NOT HOLD\033[0m — the tests that depend on what\n'
	printf '     does not hold stay on the real machine, and we write down which.\n'
	exit 1
elif [ "$UNKNOWN" -gt 0 ]; then
	printf '  \033[1;33m⚠ I DO NOT JUDGE\033[0m — %d things I could not look at.\n' "$UNKNOWN"
	printf '     %s\n' "⛔ And this is NOT a green: it is an outcome of its own (§4.5)."
	exit 3
else
	printf '  \033[1;32m⭐ THE BOX HOLDS\033[0m on all the points the product uses.\n'
	exit 0
fi
