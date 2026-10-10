#!/bin/bash
#
# 02-sessione-lancia.sh — the bench of sub-phase F2.1: the headless GNOME session
# is born, and is born WITH a virtual monitor of the requested size.
#
#   bash 02-sessione-lancia.sh guarda        just looks: touches nothing
#   bash 02-sessione-lancia.sh sano          starts it WITH --virtual-monitor
#   bash 02-sessione-lancia.sh guasto        starts it WITHOUT — the M9 test
#   bash 02-sessione-lancia.sh dispositivi   when the virtual pointer is born
#   bash 02-sessione-lancia.sh ferma         Logout(2)
#   bash 02-sessione-lancia.sh certifica     healthy → fault → healed
#   bash 02-sessione-lancia.sh come-al-riavvio  makes it be born again WITHOUT any
#                                            drop-in of this bench: as it is
#                                            after a server reboot
#   bash 02-sessione-lancia.sh guardia [...] the guard to put in front of someone
#                                            else's measurement (→ 02-sessione-guardia.sh)
#
# ⛔ IT RUNS ON THE NIC-OS HOST, not inside the container: the graphical session
#    lives there, with real logind, systemd --user and /dev/dri.
#
# ===========================================================================
# ⛔ WHY IT EXISTS, AND IT IS NOT «TO START A SESSION»
# ===========================================================================
#
# Starting a session is something `banchi/00-sessione-gnome.sh`, from phase 0,
# already does.  What that bench does NOT do, and which is the whole reason for this
# file, is ask for the MONITOR:
#
#   ⛔ `00-sessione-gnome.sh` never names `--virtual-monitor`, nor even
#      `--headless`: it relies on the drop-in that `fondamenta/banco/provision-server.sh`
#      (lines 224-231) writes in /etc/systemd/user, which sets `--headless
#      --no-x11` and **nothing else**.  ⇒ Every session started that way is BLACK.
#
#   ⭐ And it is not a deduction.  `[M]` 12 Aug 2026, opening this round: the
#      GNOME session alive on NIC-OS for two days — gnome-shell 214465,
#      IsSessionRunning true, fifty names on the bus, Nautilus and the Terminal
#      running — answered GetCurrentState with **zero monitors and zero logical
#      monitors**.  The fault of `STUDI.md` §gnome §13 M9 did not need injecting: it
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
# the command line a drop-in is needed — and that is what `src/sessione.c:671` does
# **only for KWin** (read on 12 Aug 2026: the line is exactly
# `if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(...))`, and on the GNOME branch
# nobody reads `larghezza` and `altezza`).
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
# ⭐ And this bench's port, **7511**, does not serve to talk to anybody:
#    it is the LOCK.  A graphical session is one per user (invariant I2):
#    two copies of this bench cycling it together would give two different
#    measurements under the same label.  Whoever cannot take 7511 does not
#    start.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
STRUMENTO=${STRUMENTO:-$QUI/02-sessione-stato.py}
ESITI=${ESITI:-$QUI/02-sessione-esiti.jsonl}
SCENE=${SCENE:-$QUI/02-sessione-scene}

MISURA=${MISURA:-1920x1080}
PORTA_LUCCHETTO=${PORTA_LUCCHETTO:-7511}
PORTE_DA_NON_TOCCARE=${PORTE_DA_NON_TOCCARE:-"7448 7501"}

U=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$U}
REGISTRO=$RUNTIME/remotix-sessione.log
REGISTRO_SHELL=$RUNTIME/mutter.log
DROPIN_DIR=$RUNTIME/systemd/user.control/org.gnome.Shell@wayland.service.d
DROPIN=$DROPIN_DIR/zz-f21-monitor.conf
# ⛔ The PERSISTENT drop-in, the one written by `fondamenta/banco/provision-server.sh`.
#    Ours lives in $XDG_RUNTIME_DIR and disappears by itself at reboot — which is
#    right for a bench, and is exactly why this other one must be looked at
#    too: if ONLY ours keeps the monitor up, the machine
#    turns black at the first reboot and the defect starts all over again.
DROPIN_PERSISTENTE=${DROPIN_PERSISTENTE:-/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
att() { printf '    \033[1;33m⚠\033[0m   %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ THE LOCK ON 7511 — not a listener, a RIGHT TO CYCLE.
# It is held by an `nc`/python process that occupies the port while it lives.
# ---------------------------------------------------------------------------
PID_LUCCHETTO=""
prendi_lucchetto()
{
	python3 -c "
import socket, sys, time
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
try:
    s.bind(('127.0.0.1', $PORTA_LUCCHETTO))
except OSError as e:
    print('busy: %s' % e); sys.exit(1)
s.listen(1)
print('taken')
sys.stdout.flush()
time.sleep(86400)
" &
	PID_LUCCHETTO=$!
	sleep 1
	if ! kill -0 "$PID_LUCCHETTO" 2>/dev/null; then
		ko "⛔ port $PORTA_LUCCHETTO is already taken: another copy of this"
		ko "   bench is cycling the session.  I do not start: two cycles together"
		ko "   would give two different measurements under the same label."
		return 1
	fi
	ok "lock taken on $PORTA_LUCCHETTO (pid $PID_LUCCHETTO)"
	return 0
}
molla_lucchetto()
{
	[ -n "$PID_LUCCHETTO" ] && kill "$PID_LUCCHETTO" 2>/dev/null
	PID_LUCCHETTO=""
}
trap molla_lucchetto EXIT

# ---------------------------------------------------------------------------
conta_ascoltatori() # $1 = port
{
	ss -tuln | grep -c ":$1\b"
}

vicini_prima()
{
	VICINI=""
	for p in $PORTE_DA_NON_TOCCARE; do
		VICINI="$VICINI $p:$(conta_ascoltatori "$p")"
	done
	inf "the neighbours I do not touch, before:$VICINI"
}

vicini_dopo()
{
	local guai=0 p n atteso
	for p in $PORTE_DA_NON_TOCCARE; do
		atteso=$(echo "$VICINI" | tr ' ' '\n' | grep "^$p:" | cut -d: -f2)
		n=$(conta_ascoltatori "$p")
		if [ "$n" -lt "${atteso:-0}" ]; then
			ko "⛔ on $p the listeners went from $atteso to $n:"
			ko "   I touched something that was not mine.  STOPPING EVERYTHING."
			guai=1
		fi
	done
	[ "$guai" -eq 0 ] && ok "the two wanted servers are both still up"
	return $guai
}

# ---------------------------------------------------------------------------
# The environment, built from scratch — the recipe of `sessione.c:componi_ambiente`.
#
# ⛔ EMPTY SHELL: `gnome-session.in:3-14` re-executes itself inside a LOGIN shell
#    if `$SHELL` is non-empty and is in /etc/shells, and pulls in
#    `~/.profile`.  The real check is `[ -n "$SHELL" ]`, so empty and
#    absent are both fine — and v1 leaves it ABSENT, because it builds
#    the environment from scratch and does not set SHELL (zero occurrences in `sessione.c`).
#    Here it is set EMPTY, which is the same thing and shows in `/proc/…/environ`.
#
# ⛔ XDG_SESSION_TYPE=wayland IS NEEDED: the Shell unit carries
#    `ConditionEnvironment=XDG_SESSION_TYPE=wayland` (checked in the file
#    installed on NIC-OS on 12 Aug 2026), and without it the compositor does not
#    start at all — a crippled session, and no line saying why.
avvia_sessione()
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
		setsid --fork sh -c "exec >>'$REGISTRO' 2>&1; exec gnome-session --session=gnome"
}

viva() { pgrep -u "$U" -x gnome-shell >/dev/null; }

# ⛔ The farewell is `Logout(2)`, not `systemctl --user stop`: `gnome-session` does not
#    exit after starting the target, it opens a fifo and sleeps (`STUDI.md` §gnome §3.2),
#    and `Logout(1)` shows the dialog if an inhibitor exists — in an unattended
#    session nobody answers it.
# ⛔ And it waits for `inactive`, NOT «other than active»: `is-active` passes through
#    `deactivating`, and restarting in there is another first execution
#    (`FASI.md` §00-ambiente, defect 4 of phase 0).
ferma_e_aspetta()
{
	local scadenza=$((SECONDS + ${1:-60})) stato
	gdbus call --session -d org.gnome.SessionManager -o /org/gnome/SessionManager \
	    -m org.gnome.SessionManager.Logout 2 >/dev/null
	while [ $SECONDS -lt $scadenza ]; do
		stato=$(systemctl --user is-active gnome-session-manager@gnome.service)
		case "$stato" in
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

attendi() # waits for an EVENT, with a declared ceiling
{
	local scadenza=$((SECONDS + ${1:-60}))
	while [ $SECONDS -lt $scadenza ]; do
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
#   senza  this bench's drop-in does NOT ask for it            → the M9 fault
#   nudo   ⭐ NO drop-in of this bench: the session is born with only the
#          PERSISTENT configuration of the machine, that is **as it is after a
#          reboot**.  It is the only way to measure the outcome of a reboot without
#          rebooting the server — which cannot be done, because inside the
#          container two wanted servers run (7448, 7501) and the rootfs lives
#          in RAM.
#
#   ⛔ And «nudo» IS NOT A REBOOT, and it must be said every time: it does not prove that /media
#      is remounted, that the rootfs comes back, that someone reruns
#      `provision-server.sh`.  It proves the LAST link — given the persistent
#      configuration, does a newborn session have the monitor? — which is
#      precisely the link that gave way on 10 Aug.  The other links
#      stay `[?]` until a real reboot touches them.
scrivi_dropin() # $1 = "con" | "senza" | "nudo"
{
	case "$1" in
	con)
		mkdir -p "$DROPIN_DIR"
		cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor $MISURA
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
	local vigore
	vigore=$(systemctl --user show -p ExecStart --value org.gnome.Shell@wayland.service)
	inf "ExecStart in force: $vigore"
	case "$1:$vigore" in
	con:*--virtual-monitor\ $MISURA*) ok "the drop-in WITH monitor is in force" ;;
	senza:*--virtual-monitor*)
		ko "⛔ I asked for WITHOUT and systemd still says --virtual-monitor:"
		ko "   another drop-in wins over mine.  I do not measure."
		return 1 ;;
	senza:*) ok "the drop-in WITHOUT monitor is in force" ;;
	nudo:*--virtual-monitor*)
		ok "with no drop-in of mine the monitor is requested by the PERSISTENT"
		ok "configuration of the machine: it is what will be found at reboot" ;;
	nudo:*)
		att "⚠ without this bench's drop-ins nobody asks for the monitor:"
		att "  it is exactly what the machine does after a reboot" ;;
	*)
		ko "⛔ I asked for WITH $MISURA and systemd does not say so: my drop-in"
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
# and it is the same half truth as `LEZIONI.md` §2.5-bis: a restore is proved
# by rebooting, not by rereading the script.
#
# ⇒ What makes the monitor persistent is `provision-server.sh` §4, which after every
#   reboot must be rerun anyway.  This function checks whether that line is there,
#   and if it is not it says so LOUDLY instead of letting you believe it is done.
# ---------------------------------------------------------------------------
dilo_se_non_persiste()
{
	if [ ! -r "$DROPIN_PERSISTENTE" ]; then
		att "⚠ the persistent drop-in is not there or I cannot read it:"
		att "  $DROPIN_PERSISTENTE"
		att "  ⇒ after a server reboot the session turns BLACK again."
		att "  It is set right with: bash /media/REMOTIX/provision-server.sh monitor"
		return 1
	fi
	if grep -q -- '--virtual-monitor' "$DROPIN_PERSISTENTE"; then
		ok "and it survives the reboot: --virtual-monitor is also in the persistent"
		inf "drop-in ($DROPIN_PERSISTENTE), which provision-server.sh rewrites"
		return 0
	fi
	att "⚠⚠ HEALTHY NOW, BLACK AT THE NEXT REBOOT."
	att "  ONLY this bench's drop-in keeps the monitor up, and it sits"
	att "  in \$XDG_RUNTIME_DIR and the reboot takes it away; the persistent one"
	att "  ($DROPIN_PERSISTENTE)"
	att "  does NOT name --virtual-monitor — and it is the defect that kept this"
	att "  machine black from 10 to 12 Aug (I7: the protection lives in the"
	att "  program, not in a configuration line that can get lost)."
	att "  It is cured with: bash /media/REMOTIX/provision-server.sh monitor"
	return 1
}

togli_dropin()
{
	rm -f "$DROPIN"
	rmdir "$DROPIN_DIR" 2>&1 | grep -v "Directory not empty" || true
	systemctl --user daemon-reload
}

# ⛔ THE COMMAND LINE IS FLAT, AND THE TWO FORMS ARE WRITTEN OUT IN FULL —
#    gap L3, 12 Aug 2026.
#
# There was an array: `local extra=(); [ -n "${2:-}" ] && extra=(--registra "$2")`,
# and then `"${extra[@]}"` at the end of the call.  Two lines fewer, and ⛔ the
# call **out of reach of any static check**: `01-b0-chiamate.py` saw a single
# variable where argparse expects an option, could not know whether it
# carried a `--something` inside, and declared it UNKNOWN — neither red nor
# green.  It is the seam that has already made a healthy bench come out red twice:
# B6 on 10 Aug, B7 on the 11th (`01-b0-chiamate.py`, in the header).
#
# ⚠ Repeating the six common words is the price, and it is paid: two readable
#   lines are worth more than one line that no tool can read.
misura() # $1 = label of the scene; $2 = file to record it in (optional)
{
	if [ -n "${2:-}" ]; then
		python3 "$STRUMENTO" --attesa "$MISURA" --dal-bus \
		    --etichetta "$1" --esiti "$ESITI" --registra "$2"
		return $?
	fi
	python3 "$STRUMENTO" --attesa "$MISURA" --dal-bus \
	    --etichetta "$1" --esiti "$ESITI"
	return $?
}

# ---------------------------------------------------------------------------
riparti() # $1 = con|senza ; $2 = label ; $3 = scene file (optional)
{
	log "I restart the session from scratch, drop-in «$1»"
	if viva; then
		ferma_e_aspetta 60 || { ko "⛔ it did not stop within 60 s"; return 9; }
		ok "session stopped"
	else
		inf "there was no session to stop"
	fi
	scrivi_dropin "$1" || return 9
	: >"$REGISTRO"
	avvia_sessione
	if ! attendi 60; then
		ko "⛔ the session did NOT start within 60 s.  Last lines:"
		tail -n 25 "$REGISTRO" | sed 's/^/        /'
		return 9
	fi
	ok "session started: $(pgrep -a -u "$U" -x gnome-shell | head -1)"
	# ⚠ The Shell takes its name on the bus BEFORE `meta_context_start()`
	#   (`STUDI.md` §gnome §3.2): the name is not a readiness indicator.  We wait
	#   for GetCurrentState to answer, which is the fact we need.
	sleep 3
	misura "$2" "${3:-}"
	local e=$?
	# ⛔ And it says AT ONCE whether this health is only for today: whoever has just read
	#    «HEALTHY» is exactly who must know that after the reboot it will not be any more.
	[ "$1" = con ] && dilo_se_non_persiste
	return $e
}

# ---------------------------------------------------------------------------
# ⛔ WHEN THE VIRTUAL POINTER IS BORN — the question PIANO.md brings here.
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
# The opposite case is written beforehand, as `LEZIONI.md` §1.11 wants.
# ---------------------------------------------------------------------------
dispositivi()
{
	local traccia=$RUNTIME/f21-seat.log
	log "0. The starting state"
	misura "dispositivi-partenza"; local e=$?
	if [ "$e" -ne 0 ]; then
		att "the session is not healthy (exit $e): the device measurement is"
		att "done anyway, but the number must be read knowing it."
	fi

	log "1. A live Wayland client, kept on ACROSS the birth of the pointer"
	# ⛔ It is the client «started BEFORE» of probe S7: it must stay alive for
	#    the whole measurement, or the order is not being measured — two
	#    different clients are.
	: >"$traccia"
	WAYLAND_DEBUG=1 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR="$RUNTIME" \
	    timeout 90 foot -e sleep 85 >>"$traccia" 2>&1 &
	local pid_client=$!
	sleep 6
	if ! kill -0 "$pid_client" 2>/dev/null; then
		ko "⛔ the client did not stay alive: without it I measure nothing"
		inf "last lines of the trace:"
		tail -n 15 "$traccia" | sed 's/^/        /'
		return 3
	fi
	ok "client alive (pid $pid_client), trace in $traccia"

	# ⛔ The three D-Bus steps are NOT done with three `gdbus call`: the
	#    RemoteDesktop session is tied to the CONNECTION that created it, and `gdbus`
	#    opens a new one every time.  Measured on 12 Aug 2026: `Start`
	#    answered «Object does not exist at path» and the pointer was never
	#    born — with step 3 giving NO on a scene that never happened.  The
	#    details are in the header of `02-sessione-dispositivi.py`.
	python3 "$QUI/02-sessione-dispositivi.py" --traccia "$traccia" --esiti "$ESITI"
	local esito=$?

	kill "$pid_client" 2>/dev/null
	log "The traces stay in $traccia and $traccia.dopo"
	return $esito
}

# ---------------------------------------------------------------------------
# ⛔ THE CERTIFICATION — healthy N → fault M → healed N, with the numbers
#    WRITTEN BEFOREHAND (mandate §3.3, and the rule born on 11 Aug: whoever writes a
#    bench certifies it in the same round).
#
#   expected healthy 0  (HEALTHY)
#   fault injected:     `--virtual-monitor` is removed from the drop-in — that is M9 of
#                       `STUDI.md` §gnome §13, the fault made on purpose
#   expected fault   1  (BLACK: ZERO MONITORS)
#   expected healed  0
#
# ⛔ And the verdict is not «it turned red»: it must have turned red AT ITS
#    POINT — the mark «BLACK: ZERO MONITORS» and not another.  A bench that
#    turns red for another reason is not certified, it is lucky.
# ---------------------------------------------------------------------------
certifica()
{
	local A_SANO=0 A_GUASTO=1 MARCA_GUASTO="BLACK: ZERO MONITORS"
	log "The expectations, WRITTEN BEFORE the round"
	inf "healthy: $A_SANO (HEALTHY) · fault: $A_GUASTO ($MARCA_GUASTO) · healed: $A_SANO"
	inf "requested size: $MISURA"
	vicini_prima

	mkdir -p "$SCENE"

	log "1. The HEALTHY round — the session WITH the monitor"
	riparti con "certifica-sano" "$SCENE/sana.json"; local E_SANO=$?
	log "2. The FAULT — the same session WITHOUT --virtual-monitor (M9)"
	riparti senza "certifica-guasto" "$SCENE/nera.json"; local E_GUASTO=$?
	log "3. The HEALED — the monitor is put back"
	riparti con "certifica-risanato" "$SCENE/sana-2.json"; local E_RIS=$?

	log "The verdict, with the three numbers next to it"
	inf "healthy $E_SANO · fault $E_GUASTO · healed $E_RIS"
	local falle=0
	[ "$E_SANO" -eq "$A_SANO" ] && ok "the healthy one is the expected ($E_SANO)" || {
		ko "⛔ the healthy one is $E_SANO instead of $A_SANO: the subject is broken, and a"
		ko "   bench whose subject is broken is NOT certified"
		falle=$((falle+1)); }
	[ "$E_GUASTO" -eq "$A_GUASTO" ] && ok "the fault is the expected ($E_GUASTO = $MARCA_GUASTO)" || {
		ko "⛔ the fault is $E_GUASTO instead of $A_GUASTO: either the bench does not see it,"
		ko "   or it is red for another reason"
		falle=$((falle+1)); }
	[ "$E_RIS" -eq "$A_SANO" ] && ok "the healed one goes back to healthy ($E_RIS)" || {
		ko "⛔ the healed one is $E_RIS instead of $A_SANO: the fault left"
		ko "   something behind, or the healthy one was not repeatable"
		falle=$((falle+1)); }

	vicini_dopo || falle=$((falle+1))

	if [ "$falle" -eq 0 ]; then
		printf '\n    \033[1;32m⭐ F2.1 IS CERTIFIED: healthy %s → fault %s (at its point) → healed %s\033[0m\n' \
		    "$E_SANO" "$E_GUASTO" "$E_RIS"
		printf '    --  and it is not «the bench is right»: it is «the bench can see THIS defect».\n'
		return 0
	fi
	printf '\n    \033[1;31m⛔ F2.1 IS NOT CERTIFIED: %s things do not add up\033[0m\n' "$falle"
	return 1
}

# ---------------------------------------------------------------------------
case "${1:-guarda}" in
guarda)
	# ⛔ Read only: it does not take the lock and touches nothing.
	log "Just looking — I touch nothing"
	vicini_prima
	misura "${2:-guarda}"
	e=$?
	dilo_se_non_persiste
	exit $e
	;;
guardia)
	# ⛔ The guard to put IN FRONT of someone else's measurement.  It sits in a file of
	#    its own because whoever uses it is not this bench: they are F2.2..F2.6, and they must
	#    be able to slip it in front of their own command without starting anything.
	shift
	exec bash "$QUI/02-sessione-guardia.sh" "$@"
	;;
sano)      prendi_lucchetto || exit 2; vicini_prima; riparti con "sano" "${2:-}"; e=$?; vicini_dopo || e=9; exit $e ;;
guasto)    prendi_lucchetto || exit 2; vicini_prima; riparti senza "guasto" "${2:-}"; e=$?; vicini_dopo || e=9; exit $e ;;
come-al-riavvio)
	# ⭐ The PERSISTENCE test without rebooting the server: this bench's
	#    drop-ins are removed and the session is born again with only the
	#    configuration that would be there at reboot anyway.
	prendi_lucchetto || exit 2
	vicini_prima
	riparti nudo "come-al-riavvio" "${2:-}"; e=$?
	vicini_dopo || e=9
	log "What this number says, and what it does NOT say"
	if [ "$e" -eq 0 ]; then
		ok "⭐ a newborn session WITHOUT any drop-in of this bench has"
		ok "   the monitor: the cure lives in the persistent configuration, and"
		ok "   survives the disappearance of \$XDG_RUNTIME_DIR."
	else
		ko "⛔ without this bench's drop-ins the session exits $e: after a"
		ko "   server reboot the machine goes back to this."
	fi
	att "⚠ and it is NOT a reboot: that /media is remounted, that the rootfs comes back and"
	att "  that someone reruns provision-server.sh stay [?] until a"
	att "  real reboot touches them (LEZIONI.md §2.5-bis)."
	exit $e
	;;
dispositivi) prendi_lucchetto || exit 2; dispositivi; exit $? ;;
ferma)     prendi_lucchetto || exit 2; ferma_e_aspetta && { ok "stopped"; exit 0; } || { ko "⛔ it did not stop"; exit 1; } ;;
certifica) prendi_lucchetto || exit 2; certifica; exit $? ;;
pulisci)   togli_dropin; ok "F2.1 drop-in removed: the machine goes back to its own"; exit 0 ;;
*) echo "usage: $0 {guarda|sano|guasto|come-al-riavvio|dispositivi|ferma|certifica|pulisci|guardia [...]}" >&2; exit 2 ;;
esac
