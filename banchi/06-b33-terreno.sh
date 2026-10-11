#!/bin/bash
#
# 06-b33-terreno.sh — ⛔ RUNS ON THE SERVER (NIC-OS), **OUTSIDE** the container and
# **AS ROOT**.  The ground of SUB-PHASE 6.1 — *the reattach that commands*.
#
#   sudo bash .../06-b33-terreno.sh user        creates `provai6` (uid 1006)
#   sudo bash .../06-b33-terreno.sh session      GNOME **without** --virtual-monitor
#   sudo bash .../06-b33-terreno.sh start       the server on 7781
#   sudo bash .../06-b33-terreno.sh stop
#   sudo bash .../06-b33-terreno.sh witness LxA the Wayland window that RECEIVES
#   sudo bash .../06-b33-terreno.sh witness-off
#   sudo bash .../06-b33-terreno.sh lines         how many lines it has seen so far
#   sudo bash .../06-b33-terreno.sh tail <n>      the last n lines seen
#   sudo bash .../06-b33-terreno.sh terminal     ⭐ THE APPLICATION OPENED BEFORE
#   sudo bash .../06-b33-terreno.sh terminal-off
#   sudo bash .../06-b33-terreno.sh enters         how many «Enter» it has received
#   sudo bash .../06-b33-terreno.sh monitor       how many screens, and of what size
#   sudo bash .../06-b33-terreno.sh load        ⚠ uptime: every time measurement carries it
#   sudo bash .../06-b33-terreno.sh log <n>  the tail of the server log
#   sudo bash .../06-b33-terreno.sh count <str>   how many times <str> is in the log
#   sudo bash .../06-b33-terreno.sh injector-start <LxA>  ⛔⛔ §7.1: the
#                                                 wake-up of the capture, without
#                                                 any FIT_CANVAS
#   sudo bash .../06-b33-terreno.sh injector-do "<command>"
#   sudo bash .../06-b33-terreno.sh injector-says <n>   only the B33R lines
#   sudo bash .../06-b33-terreno.sh injector-stop
#   sudo bash .../06-b33-terreno.sh clean
#
# ===========================================================================
# ⛔ IT IS AN ADAPTED COPY of `04-b31-terreno.sh`, not a rewrite
# ===========================================================================
#
# That file has already paid for three things that are not paid again here: the
# THREE roads that do NOT bring a killed session back up, the drop-in that
# `terminate-user` takes away with `/run/user/<uid>`, and the monitor count
# **divided by two** (`GetCurrentState` lists every screen twice).  ⇒ We copy
# and adapt.
#
# ⭐ AND WHAT THIS ONE ADDS, which was not needed there: the **witness inside the
#    session** (`CODER.md` §3.8 — the log of the sender says it called a
#    function, not that the desktop received) in two forms, both opened
#    **BEFORE the detach**:
#
#      · `witness`   the Wayland window of `06-b33-testimone.c`: one JSON
#                      line for every event the compositor delivers to it.
#                      The INSTRUMENT — it counts, and tells «zero» from «I did
#                      not look» because the line number always grows;
#      · `terminal`   a `gnome-terminal` with the loop the user would judge:
#                      `while IFS= read -r _; do date +%s%N >> …; done`.
#                      THE REAL APPLICATION — a Wayland client **started before**
#                      the input devices of this run exist, which is
#                      exactly point 3 of the mandate.
#
# ⛔ And they are NOT switched on together: the fullscreen window takes the
#    focus, and the terminal underneath would not receive a key.  They are TWO
#    SCENES, and the launcher does them one at a time, declaring which.
#
# ===========================================================================
# ⛔ `prova` AND 7700 ARE NOT TOUCHED — nor the ports that are not mine
# ===========================================================================
#
# 7448 · 7501 · 7561 · 7571 · 7601 · 7691 · 7700 · 7711-7715 · 7721-7725 ·
# 7731-7735 · 7751-7755 · 7761-7765.  They are COUNTED before and after, and not touched.
# ⚠ Bans, command socket, certificates and log are OUR OWN: two servers that
#   shared the ban file would put each other out of action
#   (`RCP.md` §4.4-bis).
set -uo pipefail

PORT=${PORT:-7781}
ADDR=${ADDR:-192.168.0.2}
ACCOUNT=${ACCOUNT:-provai6}
UID_B=${UID_B:-1006}
PASSWORD=${PASSWORD:-provai6-2026}
D=${D:-/media/REMOTIX/src/06-i-src/src}
WORKDIR=${WORKDIR:-/media/REMOTIX/tmp/06-i}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
UNIT=org.gnome.Shell@wayland.service

CERT=$WORKDIR/certificati
BAN=$WORKDIR/ban
SOCK=$WORKDIR/command.sock
LOG=$WORKDIR/registro.log
PIDF=$WORKDIR/pid
SURVEY=$WORKDIR/rilievo
SEEN=$WORKDIR/visto.jsonl
ENTERS=$WORKDIR/invii.txt
WITNESS=$WORKDIR/06-b33-testimone
INJECTOR=$WORKDIR/06-b33-risveglio
INJECTOR_LOG=$WORKDIR/06-b33-risveglio.log
INJECTOR_FIFO=$WORKDIR/06-b33-risveglio.fifo

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE CARD GROUPS ARE GIVEN IN ONE PLACE ONLY — `attrezzi-gruppi-scheda.sh`
#
# ⛔ Here there was `usermod -aG render,video` (or nothing at all), with the NAMES
#    HARD-CODED and without reading back: two defects in a single line.  The reason
#    why the cure lives in a separate file, and the numbers that justify it,
#    are in the box at the top of that file — ⛔ they are not copied here, or
#    they become ten places to diverge from (`LEZIONI.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
CARD_GROUPS_SH=${CARD_GROUPS_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$CARD_GROUPS_SH" ] || { ko "⛔ $CARD_GROUPS_SH is missing: without it, the tenant would be born BLIND"; exit 2; }
. "$CARD_GROUPS_SH"


neighbors() {
	local r=""
	for p in 7448 7501 7561 7571 7601 7691 7700 7711 7721 7731 7751 7761; do
		r="$r$p:$(ss -tuln 2>/dev/null | grep -c ":$p\b") "
	done
	printf '%s— listeners (NOT mine)\n' "$r"
}

# ⛔ Everything that must be done INSIDE the user's session goes through here: uid,
#    gid, environment built from scratch (`CODER.md` §4.5).
as_user() {
	setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
		env -i \
		HOME="/home/$ACCOUNT" USER="$ACCOUNT" SHELL= LANG=C.UTF-8 \
		PATH=/usr/local/bin:/usr/bin:/bin \
		XDG_RUNTIME_DIR="/run/user/$UID_B" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_B/bus" \
		XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome \
		XDG_SESSION_TYPE=wayland \
		"$@"
}

my_pid() {
	local p
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--port $PORT" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⭐ The child of THIS server, and not any child: on the same machine
#    the servers of the other six sub-phases run.
my_child() {
	local s f
	s=$(my_pid) || return 1
	for f in $(pgrep -P "$s" 2>/dev/null); do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)" in
		*--internal-child*) echo "$f"; return 0 ;;
		esac
	done
	return 1
}

[ "$(id -u)" -eq 0 ] || { ko "⛔ it must be launched AS ROOT"; exit 2; }
mkdir -p "$WORKDIR"

case "${1:-status}" in
user)
	log "The user of sub-phase 6.1: $ACCOUNT (uid $UID_B)"
	inf "$(neighbors)"
	if id "$ACCOUNT" >/dev/null 2>&1; then
		ok "already there — I do not redo it (one session per user, I2)"
	else
		useradd -m -u "$UID_B" -s /bin/bash "$ACCOUNT" || {
			ko "⛔ useradd did not succeed"; exit 2; }
		ok "created"
	fi
	printf '%s:%s\n' "$ACCOUNT" "$PASSWORD" | chpasswd || {
		ko "⛔ the password was not set: PAM will always say no"
		exit 2; }
	ok "password set"
	# ⭐ `render` AND `video`, or the encoder falls back to software: `[M]` 4.8 ms
	#    → 100 ms per frame, and the bench would measure the fallback.
	# ⛔ Here there were the two names HARD-CODED, and a failed `usermod` stopped
	#    nothing: the bench went straight on and measured a blind session.
	card_groups_give_to "$ACCOUNT" || exit 3
	inf "groups: $(id -nG "$ACCOUNT")"
	loginctl enable-linger "$ACCOUNT" || { ko "⛔ enable-linger failed"; exit 2; }
	ok "linger on: /run/user/$UID_B will live even with nobody connected"
	exit 0 ;;

session)
	log "The GNOME session of $ACCOUNT — ⭐ WITHOUT --virtual-monitor"
	inf "$(neighbors)"
	id "$ACCOUNT" >/dev/null 2>&1 || { ko "⛔ the user is not there: do «user»"; exit 2; }

	DIR="/run/user/$UID_B/systemd/user.control/$UNIT.d"
	FILE="$DIR/zz-senza-monitor.conf"
	install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ I did not make $DIR"; exit 2; }
	# ⛔⭐ `MUTTER_DEBUG` — 21 August 2026, and it serves to turn into `[M]` a
	#     chain that until now was all `[R]` inside Mutter.
	#
	#     With `MUTTER_DEBUG=eis,input` the compositor prints by itself the two lines
	#     that decide the diagnosis of §7.1:
	#       ✅ `Dropping repeated press of button 0x110, count 2`
	#          ⇒ the SEAT's count stayed down (`meta-seat-impl.c:899-908`)
	#       ⛔ `Releasing pressed buttons while destroying virtual input device`
	#          ⇒ if it APPEARED, Mutter would have a net that releases by itself, and
	#            the whole reading of the source would have to be redone.
	#
	# ⚠ It is set as `Environment=` in the drop-in because the session is launched by
	#   `gnome-session`, not by us: a variable exported here would not arrive.
	#   ⛔ And it is OFF by default: the chatter of `input` on a
	#   live session fills the journal, and a bench that changes the load of the
	#   machine measures that too.
	if [ -n "${MUTTER_DEBUG:-}" ]; then
		printf '[Service]\nEnvironment=MUTTER_DEBUG=%s\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' \
			"$MUTTER_DEBUG" > "$FILE"
		inf "⭐ MUTTER_DEBUG=$MUTTER_DEBUG in the drop-in"
	else
		printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
	fi
	chown "$UID_B:$UID_B" "$FILE"
	inf "wrote $FILE"

	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		# ⛔ And we SAY that the new drop-in is NOT in force: `gnome-shell` has
		#    read its environment at startup, and rewriting the file changes
		#    nothing for a process already started.  ⚠ Whoever wants `MUTTER_DEBUG` must
		#    go through `session-off` — and without this line would believe they
		#    had turned it on.
		[ -n "${MUTTER_DEBUG:-}" ] && \
			ko "⚠ BUT the session is already alive: MUTTER_DEBUG is NOT in force. Do «session-off» first"
		ok "there is already a live session — I do not redo it"
		exec bash "$0" monitor
	fi

	# ⛔⭐ The three roads that do NOT work are measured in `04-b31-terreno.sh`
	#     (14 August 2026): `systemctl --user start org.gnome.Shell@wayland`
	#     refuses *«may be requested by dependency only»*, the session manager
	#     does the same, and a new `gnome-session` with the manager still **active**
	#     exits **silently**.  ⇒ We wait for `inactive` and then start.
	inf "the session is not there: I wait for the manager to be inactive"
	as_user systemctl --user reset-failed >/dev/null 2>&1
	g=0
	while [ $g -lt 40 ]; do
		as_user systemctl --user is-active gnome-session-manager@gnome.service \
			>/dev/null 2>&1 || break
		sleep 0.5; g=$((g+1))
	done
	if as_user systemctl --user is-active gnome-session-manager@gnome.service >/dev/null 2>&1; then
		ko "⚠ the manager does not go away: LAST RESORT — I tear everything down"
		loginctl terminate-user "$ACCOUNT" >/dev/null 2>&1
		sleep 3
		pkill -9 -u "$UID_B" 2>/dev/null
		sleep 1
		loginctl enable-linger "$ACCOUNT" >/dev/null 2>&1
		g=0
		while [ $g -lt 60 ]; do
			[ -S "/run/user/$UID_B/bus" ] && break
			sleep 0.5; g=$((g+1))
		done
		[ -S "/run/user/$UID_B/bus" ] || { ko "⛔ the bus did not come back"; exit 3; }
		# ⛔ And the drop-in is rewritten: `terminate-user` took away
		#    `/run/user/<uid>` with `user.control` inside, and without this line
		#    the `ExecStart` in force goes back to the SYSTEM one, with
		#    `--virtual-monitor`.
		install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ I did not remake $DIR"; exit 2; }
		if [ -n "${MUTTER_DEBUG:-}" ]; then
			printf '[Service]\nEnvironment=MUTTER_DEBUG=%s\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' \
				"$MUTTER_DEBUG" > "$FILE"
		else
			printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
		fi
		chown "$UID_B:$UID_B" "$FILE"
	else
		ok "the session manager is inactive: gnome-session can start again"
	fi

	as_user systemctl --user daemon-reload || { ko "⛔ daemon-reload"; exit 2; }
	as_user systemctl --user reset-failed >/dev/null 2>&1
	as_user systemctl --user start pipewire.socket pipewire-pulse.socket >/dev/null 2>&1
	as_user systemctl --user start pipewire.service wireplumber.service >/dev/null 2>&1
	if as_user systemctl --user is-active pipewire.service >/dev/null 2>&1; then
		ok "PipeWire is alive: without it, the capture would have no node"
	else
		ko "⚠ PipeWire is NOT alive: the capture will find no node"
	fi
	# ⛔ WRITTEN IS NOT IN FORCE (form E1): we read it back from the manager.
	IN_EFFECT=$(as_user systemctl --user show -p ExecStart --value "$UNIT")
	inf "ExecStart in force: $IN_EFFECT"
	case "$IN_EFFECT" in *--no-x11*) ok "«--no-x11» is there" ;;
		*) ko "⛔ «--no-x11» is NOT there: another drop-in wins over mine"; exit 3 ;;
	esac
	case "$IN_EFFECT" in *--virtual-monitor*)
		ko "⛔ «--virtual-monitor» is still there: the scene is not the one I believe"
		exit 3 ;;
	*) ok "and «--virtual-monitor» is NOT there" ;;
	esac

	as_user setsid --fork sh -c \
		"exec >>/run/user/$UID_B/remotix-session.log 2>&1; exec gnome-session --session=gnome"
	g=0
	while [ $g -lt 120 ]; do
		if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 \
		   && as_user busctl --user list 2>/dev/null | grep -q org.gnome.Shell; then
			break
		fi
		sleep 0.5; g=$((g+1))
	done
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || {
		ko "⛔ the session did not start in $((g/2)) s"
		tail -20 "/run/user/$UID_B/remotix-session.log" 2>&1 | sed 's/^/        /'
		exit 3; }
	ok "session alive after $((g/2)) s"
	for p in $(pgrep -u "$UID_B" -x gnome-shell); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	exec bash "$0" monitor ;;

session-off)
	log "⛔ I kill the graphical session of $ACCOUNT"
	as_user gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 4
	pkill -u "$UID_B" -x gnome-shell 2>/dev/null
	g=0
	while [ $g -lt 30 ]; do
		pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || break
		sleep 0.5; g=$((g+1))
	done
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 && \
		{ pkill -9 -u "$UID_B" -x gnome-shell 2>/dev/null; sleep 2; }
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 \
		&& { ko "⛔ the session did not die"; exit 3; } || ok "the graphical session is dead"
	exit 0 ;;

# ---------------------------------------------------------------------------
# ⭐ THE WITNESS — the Wayland window that RECEIVES
# ---------------------------------------------------------------------------
witness)
	# ⛔ It is opened **BEFORE the detach**, and its size is that of the canvas in
	#    force NOW: it picks the `wl_output` by size, and if there is none it exits
	#    saying so instead of ending up on the wrong screen (form E2).
	M=${2:?the size is needed, e.g. 1264x800}
	log "The Wayland witness on monitor $M"
	[ -x "$WITNESS" ] || { ko "⛔ $WITNESS is not there: do «costruisci»"; exit 2; }
	pkill -u "$UID_B" -f 06-b33-testimone 2>/dev/null; sleep 1
	# ⛔ The file is NOT reset at every reopening, nor is it kept forever:
	#    it is reset HERE, at opening, and the line number restarts from 1 with the
	#    process.  ⚠ Whoever compares two runs must read the count, not the file.
	: > "$SEEN"; chmod 666 "$SEEN"
	as_user setsid --fork sh -c \
		"exec >>'$SEEN' 2>&1; exec '$WITNESS' --size $M"
	g=0
	while [ $g -lt 40 ]; do
		grep -q '"type":"READY"' "$SEEN" 2>/dev/null && break
		grep -q '"type":"ERRORE"' "$SEEN" 2>/dev/null && break
		sleep 0.25; g=$((g+1))
	done
	if grep -q '"type":"READY"' "$SEEN" 2>/dev/null; then
		ok "open: $(grep '"tipo":"PRONTA"' "$SEEN" | tail -1)"
		exit 0
	fi
	ko "⛔ the witness did NOT open:"
	tail -12 "$SEEN" 2>/dev/null | sed 's/^/        /'
	exit 3 ;;

witness-off)
	pkill -u "$UID_B" -f 06-b33-testimone 2>/dev/null
	ok "witness off"
	exit 0 ;;

lines)
	# ⛔ The COUNTER, not «I found lines»: «zero events» and «I did not look»
	#    look the same without a denominator that grows.
	printf 'RIGHE %s\n' "$(wc -l < "$SEEN" 2>/dev/null || echo 0)"
	exit 0 ;;

tail)
	tail -n "${2:-20}" "$SEEN" 2>/dev/null
	exit 0 ;;

after)
	# the lines with n > $2 — that is, what arrived FROM an instant onwards
	awk -v s="${2:-0}" -F'"n":' '{split($2,a,","); if (a[1]+0 > s) print}' \
		"$SEEN" 2>/dev/null
	exit 0 ;;

# ---------------------------------------------------------------------------
# ⭐⭐ THE APPLICATION OPENED BEFORE — the terminal with the `read` loop
# ---------------------------------------------------------------------------
terminal)
	# ⛔ It is point 3 of the mandate made into a scene: a Wayland client started
	#    **before** the input devices of this run exist.  `[M]` 10
	#    August 2026 (bench S7): *witness before the injector ⇒ NOTHING
	#    arrives*.  On reattach the devices are destroyed and recreated under
	#    applications **that nobody will restart** — and this is one of those.
	#
	# ⚠ Every `Enter` that REACHES THE DESKTOP writes a line in nanoseconds.  An
	#   empty desktop testifies nothing (trap 9 of the phase document).
	log "The terminal with the witness — the application nobody will restart"
	# ⛔ THE MARK GOES INSIDE THE LOOP, NOT IN THE TITLE — `[M]` 16 August 2026, and
	#    the bench fell for it: `gnome-terminal` is a THIN client that passes
	#    the request to `gnome-terminal-server` and **exits**.  ⇒ The process that
	#    carries `--title=b33-invii` on its command line disappears after an
	#    instant, and the real loop is a child of the server with a command
	#    line that does not have that title.  A `pgrep -f b33-invii` never
	#    finds it, and the bench stays hung waiting for something that is there.
	as_user pkill -f 'b33-ciclo-invii' >/dev/null 2>&1; sleep 1
	rm -f "$ENTERS"; : > "$ENTERS"; chmod 666 "$ENTERS"
	as_user setsid --fork gnome-terminal --title=b33-invii -- \
		bash -c "# b33-ciclo-invii
			while IFS= read -r _; do date +%s%N >> '$ENTERS'; done" \
		>/dev/null 2>&1
	g=0
	while [ $g -lt 40 ]; do
		pgrep -u "$UID_B" -f 'b33-ciclo-invii' >/dev/null 2>&1 && \
			pgrep -u "$UID_B" -f 'gnome-terminal-server' >/dev/null 2>&1 && break
		sleep 0.5; g=$((g+1))
	done
	n=$(pgrep -u "$UID_B" -f 'b33-ciclo-invii' 2>/dev/null | wc -l)
	m=$(pgrep -u "$UID_B" -f 'gnome-terminal-server' 2>/dev/null | wc -l)
	inf "processes «b33-ciclo-invii»: $n · gnome-terminal-server: $m"
	if [ "$n" -gt 0 ] && [ "$m" -gt 0 ]; then
		ok "the terminal is open, and the loop waits for the Enters"
	else
		ko "⛔ the terminal did NOT open: what follows measures nothing"
		exit 3
	fi
	exit 0 ;;

terminal-off)
	as_user pkill -f 'b33-ciclo-invii' 2>/dev/null
	ok "terminal off"
	exit 0 ;;

enters)
	printf 'ENTERS %s\n' "$(wc -l < "$ENTERS" 2>/dev/null || echo 0)"
	exit 0 ;;

# ---------------------------------------------------------------------------
# ⛔⛔ THE INJECTOR OF §7.1 — the second door of the dying click
# ---------------------------------------------------------------------------
injector-start)
	# sudo bash 06-b33-terreno.sh injector-start <LxA>
	#
	# ⛔ It runs INSIDE the session of `provai6`, as him: it opens a `RemoteDesktop`
	#    session of its own, mounts a virtual monitor of its own and calls
	#    `capture_wake()` — the product's function.  ⚠ It is NOT the server:
	#    here there is no QUIC and no `rcp.c`, and that is intended (`CODER.md` §3.6).
	#
	# ⛔ And it is NOT switched on together with the 7781 server: two
	#    `RemoteDesktop` sessions on the same user mount two monitors, and the witness
	#    would end up on the wrong one — that is, it would measure a silence.
	#
	# ⛔⛔ STDIN IS A FIFO OPENED FOR READING **AND WRITING** (`exec 3<>`), and
	#      it is not a quirk: a fifo opened read-only gives **EOF** every
	#      time the last writer closes, that is after EVERY command — and the
	#      program would exit with 5 («stdin closed without fine») on the first round.
	#      The symptom would be «the injector dies by itself», and nobody would
	#      connect it to the fifo.
	M=${2:-1264x800}
	log "The wake-up injector, canvas $M"
	[ -x "$INJECTOR" ] || { ko "⛔ $INJECTOR is not there: do «06-b33-risveglio-costruisci.sh»"; exit 2; }
	if pid=$(my_pid); then
		ko "⛔ the $PORT server is on (pid $pid): switch it off, or there are two sessions"
		exit 2
	fi
	pkill -u "$UID_B" -f 06-b33-risveglio 2>/dev/null; sleep 1
	rm -f "$INJECTOR_FIFO"; mkfifo -m 666 "$INJECTOR_FIFO" || { ko "⛔ the fifo cannot be created"; exit 2; }
	: > "$INJECTOR_LOG"; chmod 666 "$INJECTOR_LOG"
	as_user setsid --fork sh -c \
		"exec >>'$INJECTOR_LOG' 2>&1; exec 3<>'$INJECTOR_FIFO'; exec '$INJECTOR' --canvas $M <&3"
	g=0
	while [ $g -lt 120 ]; do
		grep -qa '^B33R: PRONTO' "$INJECTOR_LOG" 2>/dev/null && break
		grep -qa '^B33R: ERRORE' "$INJECTOR_LOG" 2>/dev/null && break
		sleep 0.5; g=$((g+1))
	done
	if grep -qa '^B33R: PRONTO' "$INJECTOR_LOG" 2>/dev/null; then
		ok "the injector is READY after $((g/2)) s"
		grep -a '^B33R: ' "$INJECTOR_LOG" | sed 's/^/        /'
		exit 0
	fi
	ko "⛔ the injector is NOT ready:"
	tail -25 "$INJECTOR_LOG" 2>/dev/null | sed 's/^/        /'
	exit 3 ;;

injector-do)
	# sudo bash 06-b33-terreno.sh injector-do "pulsante 272 1"
	shift
	pgrep -u "$UID_B" -f 06-b33-risveglio >/dev/null 2>&1 || {
		ko "⛔ the injector is not alive: nobody reads the command «$*»"; exit 3; }
	printf '%s\n' "$*" > "$INJECTOR_FIFO"
	exit 0 ;;

injector-stop)
	if pgrep -u "$UID_B" -f 06-b33-risveglio >/dev/null 2>&1; then
		printf 'fine\n' > "$INJECTOR_FIFO" 2>/dev/null
		g=0
		while [ $g -lt 20 ]; do
			pgrep -u "$UID_B" -f 06-b33-risveglio >/dev/null 2>&1 || break
			sleep 0.5; g=$((g+1))
		done
		pkill -9 -u "$UID_B" -f 06-b33-risveglio 2>/dev/null
	fi
	rm -f "$INJECTOR_FIFO"
	ok "injector off"
	exit 0 ;;

journal)
	# ⛔⭐ WHAT MUTTER SAYS ABOUT ITSELF — the voice of the compositor, which is
	#     neither ours nor the witness's.  Useful only with
	#     `MUTTER_DEBUG` on (see «session»).
	#
	#   sudo bash 06-b33-terreno.sh journal [da-quando] [pattern]
	journalctl _UID="$UID_B" --since "${2:--3 min}" --no-pager -o cat 2>/dev/null \
		| grep -Ea "${3:-Dropping repeated|Releasing pressed buttons|Updating viewports|Counting release}"
	exit 0 ;;

journal-all)
	journalctl _UID="$UID_B" --since "${2:--3 min}" --no-pager -o cat 2>/dev/null | tail -n "${3:-200}"
	exit 0 ;;

injector-log)
	tail -n "${2:-80}" "$INJECTOR_LOG" 2>/dev/null
	exit 0 ;;

injector-says)
	# ⛔ Only the injector's lines, not the product's log: they are two
	#    different voices and mixing them is the way to believe the sender.
	grep -a '^B33R: ' "$INJECTOR_LOG" 2>/dev/null | tail -n "${2:-40}"
	exit 0 ;;

# ---------------------------------------------------------------------------
monitor)
	# ⛔ The count is DIVIDED BY TWO: `GetCurrentState` lists every screen twice
	#    (found by A1 on 14 August 2026).
	n=$(as_user busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>/dev/null | tr ' ' '\n' | grep -c '"Meta-')
	printf 'MONITOR %s\n' "$((n / 2))"
	as_user busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>&1 | tr ' ' '\n' \
		| grep -E '^"(Meta-[0-9]+|MetaVirtualMonitor|Virtual)' | sed 's/^/        /'
	exit 0 ;;

load)
	# ⚠ Every time measurement carries the load next to it: five benches run on the
	#   same machine, and a number taken under load and not declared as such is
	#   a false number (phase document §0-bis).
	printf 'CARICO %s\n' "$(uptime | sed 's/.*load average: //')"
	printf 'ORA %s\n' "$(date +%H:%M:%S)"
	printf 'SESSIONI_GNOME %s\n' "$(pgrep -c -x gnome-shell 2>/dev/null || echo 0)"
	printf 'REMOTIX_VIVI %s\n' "$(pgrep -c -x remotix 2>/dev/null || echo 0)"
	exit 0 ;;

start)
	log "The server of sub-phase 6.1, on $PORT — AS ROOT"
	inf "$(neighbors)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix is not there"; exit 2; }
	[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html is not there"; exit 2; }
	n=$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")
	[ "$n" -eq 0 ] || { ko "⛔ $PORT is already taken"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix is not there"; exit 2; }
	mkdir -p "$CERT" "$SURVEY"; chmod 1777 "$SURVEY"
	# ⛔ The log is reset at every start: a GROWTH measurement on a
	#    file that carried yesterday's run inside it is not a measurement.
	: > "$LOG"
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	ldd "$D/remotix" | grep -q 'not found' && {
		ko "⛔ a library is missing:"; ldd "$D/remotix" | grep 'not found' | sed 's/^/        /'
		exit 2; }
	# ⛔ `--verbose`: without it, `log_detail()` of `figlio.c` and of
	#    `input.c` ends up in nothing and the branches look «not triggered».  A
	#    diagnostic that stays silent is not neutral: it lies (trap 1).
	nohup "$D/remotix" --address 0.0.0.0 --name "$ADDR" --port "$PORT" \
		--certificates "$CERT" --page "$D/pagina.html" \
		--ban-file "$BAN" --command-socket "$SOCK" \
		--survey "$SURVEY" --verbose >> "$LOG" 2>&1 &
	pid=$!; echo "$pid" > "$PIDF"
	g=0
	while [ $g -lt 60 ]; do
		[ -d "/proc/$pid" ] || break
		[ "$(ss -tuln 2>/dev/null | grep -c ":$PORT\b")" -ge 2 ] && break
		sleep 0.5; g=$((g+1))
	done
	[ -d "/proc/$pid" ] || { ko "⛔ the server died at once:"; tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
	ok "on, pid $pid, $(ss -tuln | grep -c ":$PORT\b") listeners"
	exit 0 ;;

log)
	tail -n "${2:-60}" "$LOG" 2>/dev/null
	exit 0 ;;

count)
	printf 'CONTA %s\n' "$(grep -c -- "${2:-input}" "$LOG" 2>/dev/null || echo 0)"
	exit 0 ;;

search)
	grep -n -- "${2:-input}" "$LOG" 2>/dev/null | tail -n "${3:-25}"
	exit 0 ;;

log-bytes)
	printf 'REGISTRO_BYTE %s\n' "$(stat -c %s "$LOG" 2>/dev/null || echo 0)"
	printf 'REGISTRO_RIGHE %s\n' "$(wc -l < "$LOG" 2>/dev/null || echo 0)"
	exit 0 ;;

stop)
	log "I switch off $PORT"
	if ! pid=$(my_pid); then ok "there was nothing on $PORT"; exit 0; fi
	my=""
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--internal-child*) my="$my $f" ;;
		esac
	done
	kill "$pid" 2>/dev/null
	g=0; while [ -d "/proc/$pid" ] && [ $g -lt 30 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && kill -9 "$pid" 2>/dev/null
	rm -f "$PIDF"
	remain=""
	for f in $my; do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--internal-child*) remain="$remain $f" ;;
		esac
	done
	if [ -z "$remain" ]; then ok "off, and no child of MINE was left orphaned"
	else ko "⛔ orphaned children of MINE:$remain"; for f in $remain; do kill -9 "$f" 2>/dev/null; done; fi
	inf "$(neighbors)"
	exit 0 ;;

clean)
	log "I remove the user of sub-phase 6.1"
	bash "$0" stop
	as_user gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 3
	loginctl disable-linger "$ACCOUNT" 2>/dev/null
	pkill -u "$UID_B" 2>/dev/null; sleep 2; pkill -9 -u "$UID_B" 2>/dev/null
	userdel -r "$ACCOUNT" 2>&1 | sed 's/^/        /'
	ok "done"
	inf "$(neighbors)"
	exit 0 ;;

status|*)
	log "State"
	inf "$(neighbors)"
	inf "user $ACCOUNT: $(id "$ACCOUNT" 2>&1)"
	for p in $(pgrep -u "$UID_B" -x gnome-shell 2>/dev/null); do
		inf "gnome-shell $p: $(tr '\0' ' ' < /proc/$p/cmdline)"
	done
	if pid=$(my_pid); then inf "server $PORT: pid $pid"; else inf "server $PORT: off"; fi
	if f=$(my_child); then inf "child: $f"; else inf "child: none"; fi
	inf "log: $(stat -c %s "$LOG" 2>/dev/null || echo 0) bytes"
	inf "witness: $(pgrep -u "$UID_B" -f 06-b33-testimone | wc -l) alive, $(wc -l < "$SEEN" 2>/dev/null || echo 0) lines seen"
	inf "terminal: $(pgrep -u "$UID_B" -f b33-ciclo-invii | wc -l) alive, $(wc -l < "$ENTERS" 2>/dev/null || echo 0) Enters received"
	inf "$(uptime)"
	exit 0 ;;
esac
