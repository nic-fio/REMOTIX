#!/bin/bash
# ===========================================================================
# 11-passo0.sh — ⛔⛔ STEP 0 OF PHASE 11
#
#   «Inside a container, does the piece of the system that keeps track of who is
#    logged in behave as on the real machine?»
#
#   It runs INSIDE the box, as administrator:
#       podman exec -it rete11-gnome bash /passo0/11-passo0.sh
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
#   the most serious finding of the two rounds.  `fasi/11-la-rete-di-sicurezza.md` §3.5.
#
# ---------------------------------------------------------------------------
# ⚠⚠ WHAT THIS BENCH IS **NOT**, and it must be read before its outcomes
#
# ⛔ **It does not test the product.**  It tests the ENVIRONMENT.  The product is not yet
#    in this box, and it does not need to be: the question of step 0 is whether the
#    box can host the conditions in which the product lives.
#
# ⛔ And in particular, point 7 starts the compositor with `--virtual-monitor`,
#    ⚠ which is **the opposite** of how the product starts it (`sessione.c:735`,
#    where that line was REMOVED on 14 August 2026 with a measurement behind it).
#    ⇒ Here it serves to ask *«can a Wayland compositor live in this
#      box and serve a client?»*.  ⛔ **Not** to ask *«is the REMOTIX
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
#    must not have it: `LEZIONI.md` §1.9, and the rule «None is not zero».
# ===========================================================================
set -uo pipefail

UTENTE=provanic
UID_UTENTE=4011
VERDE=0; ROSSO=0; NONSO=0

blu()  { printf '\n\033[1;34m=== %s\033[0m\n' "$*"; }
si()   { printf '  \033[1;32mSI \033[0m %s\n' "$*"; VERDE=$((VERDE+1)); }
no()   { printf '  \033[1;31mNO \033[0m %s\n' "$*"; ROSSO=$((ROSSO+1)); }
boh()  { printf '  \033[1;33m?  \033[0m %s\n' "$*"; NONSO=$((NONSO+1)); }
nota() { printf '       %s\n' "$*"; }

come_lui() { runuser -u "$UTENTE" -- "$@"; }

# ---------------------------------------------------------------------------
# ⭐⭐ THE ADAPTER — the answer to «how do we stay blind to the desktop»
#
# This bench does not know which desktop it has in front of it, and must not know.  Every box
# carries at the SAME path a file that says how its compositor is started.
# ⇒ The list of tests stays ONE; the «how» lives below (`fasi/11…` §3.7).
# ---------------------------------------------------------------------------
ADATTATORE=/usr/local/lib/rete11/adattatore.sh
if [ -r "$ADATTATORE" ]; then
	. "$ADATTATORE"
	DESK=$(adattatore_nome)
else
	DESK="(no adapter: $ADATTATORE is not there)"
fi

printf '\033[1m STEP 0 — does the box hold the system?\033[0m\n'
printf ' desktop: %s\n' "$DESK"
printf ' box: %s · kernel: %s · %s\n' \
       "$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown}")" \
       "$(uname -r)" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# ---------------------------------------------------------------------------
blu "0. Is the first process «systemd»?  (if not, the rest makes no sense)"
# ---------------------------------------------------------------------------
PRIMO=$(ps -p 1 -o comm= 2>/dev/null || echo '')
if [ "$PRIMO" = "systemd" ]; then
	si "process 1 is systemd"
else
	no "process 1 is «$PRIMO»: this box cannot answer the question"
	nota "⇒ I stop: without systemd points 1-6 cannot even be asked"
	exit 1
fi

# ⛔ `is-system-running` EXITS 1 when the state is «degraded», and with `pipefail`
#    the `if` read it as «I do not know».  ⇒ We capture the TEXT and judge
#    that: the exit status here is not the judgement, it is a detail.
#    `[M]` 25 August 2026, defect of this bench on its first run.
STATO_SIS=$(systemctl is-system-running 2>&1 | head -1)
case "$STATO_SIS" in
  running)
	si "the system has started (running)" ;;
  degraded)
	si "the system has started, with failed units (degraded)"
	nota "⚠ the failed units, which must be looked at one by one:"
	systemctl --failed --no-legend --plain 2>/dev/null | head -8 | sed 's/^/       ⚠ /' ;;
  starting)
	boh "the system is still starting: too early to judge" ;;
  *)
	boh "state not readable: $STATO_SIS" ;;
esac

# ---------------------------------------------------------------------------
blu "1. Does the user session EXIST, and is it of a type the product recognises?"
# ---------------------------------------------------------------------------
if ! command -v loginctl >/dev/null 2>&1; then
	boh "«loginctl» is not in the box: I cannot look"
elif ! systemctl is-active systemd-logind >/dev/null 2>&1; then
	no "systemd-logind is NOT active: $(systemctl is-active systemd-logind 2>&1)"
	nota "⇒ it is precisely the piece the product leans on"
	systemctl status systemd-logind --no-pager -l 2>&1 | tail -6 | sed 's/^/       /'
else
	si "systemd-logind is active"
	# ⛔⛔ AND HERE WE PREPARE BEFORE LOOKING, because it is what the PRODUCT does.
	#     On the first run this point judged while the user manager was
	#     still «activating», and gave a red that said «the box does not hold»
	#     when the truth was «I had not asked anything yet».
	#     ⇒ `[M]` 25 August 2026, second defect of this bench.
	#     ⚠ Preparing is not cheating: the product turns on linger and starts the
	#       user manager by itself.  Cheating would be **skipping** the check.
	loginctl enable-linger "$UTENTE" 2>/dev/null
	systemctl start "user@${UID_UTENTE}.service" 2>/dev/null
	for _ in $(seq 1 30); do
		loginctl show-user "$UTENTE" >/dev/null 2>&1 && break
		sleep 0.5
	done
	# ⛔ It is not enough that the service runs: it must be able to OPEN a session.
	#    We try to open a real one with a non-interactive login.
	if come_lui true 2>/dev/null; then
		SES=$(loginctl list-sessions --no-legend 2>/dev/null | wc -l)
		nota "sessions open now: $SES"
		if loginctl show-user "$UTENTE" >/dev/null 2>&1; then
			si "logind knows the user «$UTENTE»"
			loginctl show-user "$UTENTE" -p State -p Linger -p RuntimePath 2>/dev/null \
				| sed 's/^/       /'
		else
			no "logind does NOT know the user «$UTENTE»: $(loginctl show-user "$UTENTE" 2>&1 | head -1)"
			nota "⛔ this is the point where the box stops representing the product"
		fi
	else
		boh "I cannot even run a command as «$UTENTE»"
	fi
fi

# ---------------------------------------------------------------------------
blu "2. LINGER: do the user's services live without anyone having logged in?"
# ---------------------------------------------------------------------------
if loginctl enable-linger "$UTENTE" 2>/dev/null; then
	if [ "$(loginctl show-user "$UTENTE" -p Linger --value 2>/dev/null)" = "yes" ]; then
		si "linger turns on and stays on"
	else
		no "the command passes but linger does NOT show as on"
	fi
else
	no "linger cannot be turned on: $(loginctl enable-linger "$UTENTE" 2>&1 | head -1)"
	nota "⛔ without linger the graphical session does not survive the client detaching"
fi

if systemctl is-active "user@${UID_UTENTE}.service" >/dev/null 2>&1; then
	si "the user manager («user@${UID_UTENTE}») is alive without any interactive login"
else
	STATO=$(systemctl is-active "user@${UID_UTENTE}.service" 2>&1)
	if systemctl start "user@${UID_UTENTE}.service" 2>/dev/null; then
		si "the user manager starts on request (it was «$STATO»)"
	else
		no "the user manager does not start: it was «$STATO»"
		systemctl status "user@${UID_UTENTE}.service" --no-pager -l 2>&1 | tail -6 | sed 's/^/       /'
	fi
fi

# ---------------------------------------------------------------------------
blu "3. Can a service be started inside the user session?"
# ---------------------------------------------------------------------------
# ⚠ The product starts like this: a user unit, not a detached process.
#   Here we test the MECHANISM with a fake unit, because the product is not
#   in this box yet.
if come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
        systemd-run --user --quiet --unit=passo0-prova \
        --property=Type=oneshot /bin/true 2>/dev/null; then
	si "a user unit starts from inside the session"
	come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
	        systemctl --user reset-failed passo0-prova 2>/dev/null || true
else
	no "a user unit cannot be started"
	nota "⛔ it is the way the product starts the graphical session"
	come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
	        systemd-run --user --unit=passo0-prova --property=Type=oneshot /bin/true 2>&1 \
	        | tail -4 | sed 's/^/       /'
fi

# ---------------------------------------------------------------------------
blu "4. When the session ends, do the processes really DIE?"
# ---------------------------------------------------------------------------
# ⛔ The shape of the feared fault: a container in which processes stay
#    alive after closing ⇒ test C7 («nothing remains») would be green here
#    and red on the real machine, or vice versa.
if come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
        systemd-run --user --quiet --unit=passo0-dorme sleep 300 2>/dev/null; then
	sleep 1
	PID=$(pgrep -u "$UTENTE" -f 'slee[p] 300' | head -1)
	if [ -n "$PID" ]; then
		nota "the fake child is alive (pid $PID); now the user's session is closed"
		loginctl terminate-user "$UTENTE" 2>/dev/null || \
			come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
			        systemctl --user stop passo0-dorme 2>/dev/null
		sleep 2
		if pgrep -u "$UTENTE" -f 'slee[p] 300' >/dev/null 2>&1; then
			no "the child SURVIVED the closing of the session"
			nota "⛔ here the box behaves differently from the real machine"
		else
			si "the child died with the session, and nothing remained"
		fi
	else
		boh "I did not see the fake child being born: I cannot judge"
	fi
else
	boh "I could not start the fake child: I cannot judge"
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
#   reds for nothing gets switched off by whoever works (`fasi/11…` §4.3).
#
# ⇒ Whoever tests the closing has the duty to REOPEN, and to check that the
#   reopening succeeded before letting the others judge.
# ---------------------------------------------------------------------------
loginctl enable-linger "$UTENTE" 2>/dev/null
systemctl start "user@${UID_UTENTE}.service" 2>/dev/null
RIPRESO=0
for _ in $(seq 1 30); do
	if [ -S "/run/user/$UID_UTENTE/bus" ]; then RIPRESO=1; break; fi
	sleep 0.5
done
if [ "$RIPRESO" = 1 ]; then
	nota "⭐ session put back up after the closing test"
else
	boh "⛔ I could NOT put the session back up after point 4"
	nota "⚠ points 5, 6 and 7 below would run on a cleared field: I do NOT judge them"
	printf '\n  \033[1;33mI stop here\033[0m — better «I do not know» than three false reds.\n'
	exit 3
fi

# ---------------------------------------------------------------------------
blu "5. Is the user's private directory there, is it THEIRS, and is it writable?"
# ---------------------------------------------------------------------------
RTD="/run/user/$UID_UTENTE"
if [ -d "$RTD" ]; then
	PROP=$(stat -c '%U %a' "$RTD" 2>/dev/null)
	if come_lui test -w "$RTD"; then
		si "$RTD exists, it is writable by the user ($PROP)"
	else
		no "$RTD exists but the user can NOT write to it ($PROP)"
	fi
	# ⛔ And it must not be the same as another box's: we check that it is a
	#    mount OF THIS container, not a piece of the host passed inside.
	# ⚠ `findmnt` in here returns empty (logind made the mount after
	#   the container started, and the table it sees does not list it): we ask
	#   the kernel for the TYPE, which always answers.  `[M]` 25 August 2026.
	TIPO_RTD=$(stat -fc %T "$RTD" 2>/dev/null)
	if [ "$TIPO_RTD" = tmpfs ]; then
		si "and it is a directory of this box (tmpfs), not a piece of the host"
	else
		no "it is NOT a tmpfs of this box, it is «$TIPO_RTD»"
		nota "⛔ two boxes sharing this directory would step on each other's toes"
	fi
else
	no "$RTD does not exist: without it, no session socket is born"
fi

# ---------------------------------------------------------------------------
blu "6. Is the session message bus there, and does the desktop see it?"
# ---------------------------------------------------------------------------
if [ -S "$RTD/bus" ]; then
	si "the session bus is there ($RTD/bus)"
	if come_lui env XDG_RUNTIME_DIR="$RTD" \
	        DBUS_SESSION_BUS_ADDRESS="unix:path=$RTD/bus" \
	        busctl --user list --no-legend >/dev/null 2>&1; then
		si "and it can be talked to"
	else
		no "the socket is there but does not answer"
	fi
else
	no "the session bus is NOT there ($RTD/bus)"
	nota "⛔ without it, gnome-session does not start and the product has nobody to talk to"
fi

# ---------------------------------------------------------------------------
blu "7. Does a Wayland compositor live in here, and serve a client?"
# ---------------------------------------------------------------------------
# ⚠⚠ See the box at the top: here `--virtual-monitor` is used, which the product
#    does NOT use.  The question is about the ENVIRONMENT, not the product.
if ! command -v adattatore_avvia >/dev/null 2>&1 && ! type adattatore_avvia >/dev/null 2>&1; then
	boh "this box has no adapter: I do not know how the compositor is started"
else
	rm -f /tmp/passo0-shell.log
	SHELLPID=$(adattatore_avvia "$RTD" /tmp/passo0-shell.log)
	# We wait for the socket, not a fixed time: a clock-based wait is a
	# deadline that fires whenever it happens to (`LEZIONI.md`, the heartbeat rule).
	SOCK=''
	for _ in $(seq 1 40); do
		SOCK=$(come_lui sh -c "ls $RTD/wayland-* 2>/dev/null | grep -v lock | head -1" 2>/dev/null)
		[ -n "$SOCK" ] && break
		sleep 0.5
	done
	if [ -z "$SOCK" ]; then
		no "the compositor opened no socket in 20 s"
		tail -12 /tmp/passo0-shell.log 2>/dev/null | sed 's/^/       /'
	else
		si "the compositor is alive and has opened $(basename "$SOCK")"
		DISP=$(basename "$SOCK")
		# ⭐ THE YARDSTICK OF THE 25 AUGUST FAULT: how many outputs it ANNOUNCES.
		if command -v wayland-info >/dev/null 2>&1; then
			USCITE=$(come_lui env XDG_RUNTIME_DIR="$RTD" WAYLAND_DISPLAY="$DISP" \
			        wayland-info 2>/dev/null | grep -c 'interface:.*wl_output' || echo 0)
			if [ "${USCITE:-0}" -gt 0 ]; then
				si "and it ANNOUNCES $USCITE output(s) — a client can open a window"
			else
				no "⛔ it ANNOUNCES ZERO outputs: it is the shape of the 25 August fault"
				nota "⚠ here though I asked for the monitor myself: if it is zero, it is the box's"
			fi
		else
			boh "«wayland-info» is not there: I cannot count the outputs"
		fi
		# A real client that draws.
		if command -v weston-simple-shm >/dev/null 2>&1; then
			come_lui env XDG_RUNTIME_DIR="$RTD" WAYLAND_DISPLAY="$DISP" \
			        weston-simple-shm >/tmp/passo0-cliente.log 2>&1 &
			CLPID=$!
			sleep 3
			if kill -0 "$CLPID" 2>/dev/null; then
				si "a real Wayland client has attached and is drawing"
				kill "$CLPID" 2>/dev/null
			else
				no "the Wayland client died immediately"
				tail -6 /tmp/passo0-cliente.log 2>/dev/null | sed 's/^/       /'
			fi
		else
			boh "I have no minimal Wayland client in the box"
		fi
	fi
	kill "$SHELLPID" 2>/dev/null
	wait "$SHELLPID" 2>/dev/null
fi

# ---------------------------------------------------------------------------
blu "8. Can the graphics card and the hardware encoder be reached?"
# ---------------------------------------------------------------------------
if [ ! -e /dev/dri/renderD128 ]; then
	no "/dev/dri/renderD128 is not in the box: the card did not get in"
else
	si "/dev/dri/renderD128 is there"
	if come_lui test -r /dev/dri/renderD128 && come_lui test -w /dev/dri/renderD128; then
		si "and the user can read and write it"
	else
		no "it is there but the user can NOT write to it ($(stat -c '%U:%G %a' /dev/dri/renderD128))"
		nota "⛔ it is the «render» group: without it, encoding happens in software and the numbers change"
	fi
	if command -v vainfo >/dev/null 2>&1; then
		VA=$(come_lui env LIBVA_DRIVER_NAME=iHD vainfo --display drm --device /dev/dri/renderD128 2>&1)
		if echo "$VA" | grep -q 'VAProfileH264'; then
			si "the hardware encoder answers ($(echo "$VA" | grep -m1 'Driver version' | sed 's/^ *//'))"
			nota "H.264 encoding profiles found: $(echo "$VA" | grep -c 'VAProfileH264.*Enc')"
		else
			no "the hardware encoder does not answer"
			echo "$VA" | tail -6 | sed 's/^/       /'
		fi
	else
		boh "«vainfo» is not in the box"
	fi
fi

# ---------------------------------------------------------------------------
printf '\n\033[1m=========================  THE VERDICT  =========================\033[0m\n'
printf '  holds: %d   does not hold: %d   could not look: %d\n' "$VERDE" "$ROSSO" "$NONSO"
if [ "$ROSSO" -gt 0 ]; then
	printf '  \033[1;31m⛔ THE BOX DOES NOT HOLD\033[0m — the tests that depend on what\n'
	printf '     does not hold stay on the real machine, and we write down which.\n'
	exit 1
elif [ "$NONSO" -gt 0 ]; then
	printf '  \033[1;33m⚠ I DO NOT JUDGE\033[0m — %d things I could not look at.\n' "$NONSO"
	printf '     %s\n' "⛔ And this is NOT a green: it is an outcome of its own (§4.5)."
	exit 3
else
	printf '  \033[1;32m⭐ THE BOX HOLDS\033[0m on all the points the product uses.\n'
	exit 0
fi
