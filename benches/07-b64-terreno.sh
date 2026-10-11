#!/usr/bin/env bash
#
# ===========================================================================
# 07-b64-terreno — the ground of agent A8: user `provar7`, tree,
#                  server on 7801.
# ===========================================================================
#
# ⛔ ISOLATION, and for this bench it counts double because it touches the NETWORK:
#      port **7801** · tree `/media/REMOTIX/src/07-r-src` ·
#      work `/media/REMOTIX/tmp/07-r` · user **provar7** (uid 1018) ·
#      unit `remotix-7801.service`, its own ban-file, socket and certificates.
#
#    ⛔⛔ NOT TO BE TOUCHED: **7700**, **7730** (the user's server, and it is
#         on) and the user **`prova`**.  The ban of §4.4-bis is per ADDRESS and
#         lasts 12 hours: a bench that triggers it puts all the others
#         out of action, because they all start from the same address.
#
# ⛔ D12 — the password NEVER goes through the command line: it is written to
#    a `0600` file and given to `chpasswd` on stdin.
#
# ⛔ The **`render`** group: without it, the graphical session does not open the DRM node and
#    the symptom is «the desktop does not start», which looks like ten other things.
#
# ⛔ `enable-linger`, or the user manager dies with the last logind session and
#    `/run/user/<uid>` vanishes from under PipeWire's feet.
#
# Usage (from the laptop):
#     bash benches/07-b64-terreno.sh user
#     bash benches/07-b64-terreno.sh ship          # sources + build
#     bash benches/07-b64-terreno.sh start
#     bash benches/07-b64-terreno.sh stop
#     bash benches/07-b64-terreno.sh status
# ===========================================================================
set -uo pipefail

MACHINE=${MACHINE:-nicfio@192.168.0.2}
SUDO_PASSWORD=${SUDO_PASSWORD:-nicfio}
ADDR=${ADDR:-192.168.0.2}
PORT=${PORT:-7801}
ACCOUNT=${ACCOUNT:-provar7}
UID_B=${UID_B:-1018}
USER_PASSWORD=${USER_PASSWORD:-r7-audio-2026}
TREE=${TREE:-/media/REMOTIX/src/07-r-src}
WORKDIR=${WORKDIR:-/media/REMOTIX/tmp/07-r}
INSIDE_TREE=${INSIDE_TREE:-/srv/src/07-r-src}
INSIDE_WORK=${INSIDE_WORK:-/srv/remotix/tmp/07-r}
UNIT=${UNIT:-remotix-$PORT}

# ⛔ The ports that are NOT mine: they are COUNTED before and after, and never touched.
NEARBY_PORTS="7700 7710 7720 7730"

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE CARD GROUPS ARE GIVEN IN ONE PLACE ONLY — `tools-card-groups.sh`
#
# ⛔ Here there was `usermod -aG render,video` (or nothing at all), with the NAMES
#    HARD-CODED and without reading back: two defects in a single line.  The reason
#    why the cure lives in a separate file, and the numbers that justify it,
#    are in the box at the top of that file — ⛔ they are not copied here, or
#    they become ten places to diverge from (`LESSONS.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
CARD_GROUPS_SH=${CARD_GROUPS_SH:-$(cd "$(dirname "$0")" && pwd)/tools-card-groups.sh}
[ -f "$CARD_GROUPS_SH" ] || { ko "⛔ $CARD_GROUPS_SH is missing: without it, the tenant would be born BLIND"; exit 2; }
. "$CARD_GROUPS_SH"


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS ON THE TEST MACHINE, AS ROOT
# ═══════════════════════════════════════════════════════════════════════════
if [ "${1:-}" = "--on-server" ]; then
	STEP=${2:-stato}
	[ "$(id -u)" -eq 0 ] || { ko "⛔ «--on-server» must be run AS ROOT"; exit 2; }
	mkdir -p "$WORKDIR" 2>/dev/null

	neighbors() {
		local r="" p
		for p in $NEARBY_PORTS; do r="$r$p:$(ss -tuln 2>/dev/null | grep -c ":$p\b") "; done
		printf '%s— listeners NOT mine (counted, not touched)' "$r"
	}

	case "$STEP" in
	user)
		log "The bench user: $ACCOUNT (uid $UID_B)"
		inf "$(neighbors)"
		ALREADY_THERE=no
		if id "$ACCOUNT" >/dev/null 2>&1; then
			ALREADY_THERE=si
			ok "already there — I do not redo it"
		else
			useradd -m -u "$UID_B" -s /bin/bash "$ACCOUNT" || {
				ko "⛔ useradd did not succeed"; exit 2; }
			ok "created"
		fi
		# ⛔ D12: the password in a 0600 file, never in argv.  `chpasswd` reads it
		#    from stdin, and we delete the file right after.
		#
		# ⛔⛔ AND IT IS NOT REDONE FOR A USER THAT ALREADY EXISTS — 25 August 2026.
		#
		#   `[M]` In phase 10 the users are SHARED among several benches, and this
		#   step rewrote the password at every call: the last one to call
		#   `user` won, and the others read «wrong credentials» on a
		#   healthy machine.
		#   ⛔⛔ And every rejection uses up one of the THREE attempts of the per-ADDRESS
		#     ban (`RCP.md` §4.4-bis), which lasts TWELVE HOURS and puts out of
		#     action every other bench that starts from here.
		#
		#   ⇒ If the user was already there, the password is NOT touched.  Whoever really
		#     needs to set it again asks for it: `REDO_PASSWORD=1`.
		if [ "${ALREADY_THERE:-no}" = si ] && [ "${REDO_PASSWORD:-0}" != 1 ]; then
			ok "⭐ password NOT touched: the user was already there (REDO_PASSWORD=1 to force)"
		else
			( umask 077; printf '%s:%s\n' "$ACCOUNT" "$USER_PASSWORD" > "$WORKDIR/.chp" )
			chmod 600 "$WORKDIR/.chp"
			chpasswd < "$WORKDIR/.chp" || { ko "⛔ chpasswd failed"; rm -f "$WORKDIR/.chp"; exit 2; }
			rm -f "$WORKDIR/.chp"
			ok "password set (from stdin, never in argv — D12)"
		fi
		# ⛔ Here there were the two HARD-CODED names and no reading back.
		card_groups_give_to "$ACCOUNT" || exit 3
		ok "groups: $(id -nG "$ACCOUNT")"
		loginctl enable-linger "$ACCOUNT" || { ko "⛔ enable-linger failed"; exit 2; }
		ok "linger on: /run/user/$UID_B will live even with nobody connected"
		ls -ld "/run/user/$UID_B" 2>&1 | sed 's/^/        /'
		# The password the client needs, in a 0600 file inside the work directory.
		( umask 077; printf '%s\n' "$USER_PASSWORD" > "$WORKDIR/parola" )
		chmod 600 "$WORKDIR/parola"
		ok "the password is in $WORKDIR/parola, 0600 (the client reads it with --password-file)"
		exit 0 ;;

	start)
		log "The bench server, on $PORT — unit $UNIT.service"
		inf "$(neighbors)"
		mkdir -p "$WORKDIR/certificati" "$WORKDIR/rilievo"; chmod 1777 "$WORKDIR/rilievo"
		chmod 755 "$WORKDIR"   # ⚠ `provar7` must be able to read the tone file
		: > "$WORKDIR/registro.log"

		B2=/media/REMOTIX/src/b2
		export LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
		# ⛔ Trap 1 of `restart-7700.sh`: without this check the binary
		#    takes the system ngtcp2, starts just fine and ABORTS at the first one that
		#    connects.  It is checked BEFORE starting.
		MISSING=$(ldd "$TREE/src/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
		if [ "$MISSING" != "0" ]; then
			ko "⛔ I do NOT start: ngtcp2/nghttp3 would not come from $B2 —"
			ldd "$TREE/src/remotix" | grep -E 'ngtcp2|nghttp3' | sed 's/^/        /'
			exit 2
		fi
		ok "ldd: ngtcp2 and nghttp3 come from $B2"

		systemctl stop "$UNIT.service" 2>/dev/null
		systemctl reset-failed "$UNIT.service" 2>/dev/null
		i=0
		while ss -uln 2>/dev/null | grep -q ":$PORT " && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

		# ⛔ A SYSTEM unit, not `setsid` from this ssh: `pam_systemd` does not
		#    create a second logind session for the child and `/run/user/<uid>`
		#    does not exist — trap 4 of `restart-7700.sh`.
		# ⛔ And the TWO properties this bench measures: `LimitRTPRIO=20` and
		#    `LimitNICE=-11`.  ⚠ They can be removed from the launcher
		#    (NO_RT=1) — and that is the positive control of R26.
		# ⭐ `RTPRIO=` can be changed from the launcher, and it is the A/B of R26: 20 is
		#    what the unit grants today, 95 is what PipeWire would want.
		RT_PROP=(--property=LimitRTPRIO=${RTPRIO:-20} --property=LimitNICE=-11)
		if [ "${NO_RT:-0}" = 1 ]; then
			RT_PROP=(--property=LimitRTPRIO=0)
			inf "⛔ NO_RT=1: the unit does NOT grant real time (control of R26)"
		fi
		inf "the unit grants LimitRTPRIO=${NO_RT:+0}${RTPRIO:-20}"
		# ⭐ `--verbose`: the child without chatter KEEPS SILENT.
		# shellcheck disable=SC2086
		systemd-run \
			--unit="$UNIT" --collect --description="REMOTIX, bench 07-b64 (A8)" \
			--working-directory="$TREE/src" \
			--setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
			--property=StandardOutput=append:$WORKDIR/registro.log \
			--property=StandardError=append:$WORKDIR/registro.log \
			--property=KillMode=mixed \
			"${RT_PROP[@]}" \
			"$TREE/src/remotix" \
			--address 0.0.0.0 --name "$ADDR" --port "$PORT" \
			--certificates "$WORKDIR/certificati" \
			--page "$TREE/src/page.html" \
			--ban-file "$WORKDIR/ban" \
			--command-socket "$WORKDIR/command.sock" \
			--survey "$WORKDIR/rilievo" \
			${SERVER_OPTIONS:-} \
			--verbose >/dev/null || { ko "⛔ systemd-run refused"; exit 2; }

		i=0; PID=0
		while [ $i -lt 50 ]; do
			PID=$(systemctl show -p MainPID --value "$UNIT.service" 2>/dev/null || echo 0)
			[ "$PID" != "0" ] && [ -n "$PID" ] && break
			i=$((i+1)); sleep 0.1
		done
		if [ "$PID" = "0" ] || [ -z "$PID" ]; then
			ko "⛔ the server did not start — the last lines:"
			tail -20 "$WORKDIR/registro.log" | sed 's/^/        /'
			exit 2
		fi
		ok "server $PID on port $PORT"
		# ⛔⛔ AND THE LIMITS ARE READ AFTER THE `exec`, NOT AS SOON AS THERE IS A PID.
		#
		#     `[M]` 21 August 2026, and the bench lied twice before I
		#     noticed: `systemctl show -p MainPID` publishes the pid **of the
		#     fork**, and the unit's rlimits are applied by that child right
		#     BEFORE `execve`.  ⇒ Whoever reads `/proc/PID/limits` in that
		#     window sees **systemd**'s limits, that is `0 0`, and writes
		#     «the unit does not grant real time» on a unit that grants it.
		#     ⚠ It is a red on correct code, the form of `LESSONS.md` §2.3.
		#
		# ⇒ We wait until the pid is REALLY our binary, and only then
		#   do we read.  ⭐ And if it does not become so, we declare it instead of reading
		#   whatever happens to be there.
		i=0
		while [ $i -lt 50 ]; do
			case "$(readlink -f "/proc/$PID/exe" 2>/dev/null)" in
			*/remotix) break ;;
			esac
			i=$((i+1)); sleep 0.1
		done
		if [ $i -ge 50 ]; then
			ko "⚠ after 5 s /proc/$PID/exe is not yet «remotix»: I do NOT read the limits"
		else
			grep -E 'Max realtime|Max nice' "/proc/$PID/limits" | sed 's/^/        LIM /'
		fi
		# ⛔⛔ AND «ON» MEANS THAT SOMEONE IS LISTENING — 25 August 2026.
		#
		#   `[M]` With an option the binary does not know, the server prints its
		#   own help and exits: `systemd-run` has already published a MainPID,
		#   and this step said «OK server 1265806 on port 8260» **exiting
		#   ZERO**, with the unit already `inactive/success` and **no listener**.
		#
		#   ⛔ A bench that trusted that exit would say «on», then «the
		#     table does not fill up», and would end up BLAMING THE PRODUCT for a
		#     defect that was **a non-existent option**.  It is «silence instead of
		#     red» (`LESSONS.md` §1.29) one floor up: in the ground.
		#
		# ⇒ The ground does not declare on until it sees a LISTENER on the
		#   port.  If there is none, the last lines of the log are printed — which
		#   are the ones that say **why** — and we exit RED.
		i=0
		while [ $i -lt 50 ]; do
			ss -uln 2>/dev/null | grep -q ":$PORT " && break
			i=$((i+1)); sleep 0.1
		done
		if [ $i -ge 50 ]; then
			ko "⛔⛔ NOBODY IS LISTENING on $PORT after 5 s: the server is NOT on"
			inf "unit: $(systemctl is-active "$UNIT.service" 2>/dev/null) · the last lines:"
			tail -25 "$WORKDIR/registro.log" | sed 's/^/        /'
			exit 2
		fi
		ok "⭐ someone is listening on $PORT — this, not the pid, is «on»"
		inf "$(neighbors)"
		exit 0 ;;

	unblock)
		log "Unblocking the address — §4.4-bis"
		bash /media/REMOTIX/enter.sh --root \
			"python3 $INSIDE_TREE/benches/01-b8-unblock.py --socket $INSIDE_WORK/command.sock $ADDR"
		inf "unblock of $ADDR: exit $?"
		exit 0 ;;

	stop)
		log "Stopping $UNIT.service (and ONLY that one)"
		systemctl stop "$UNIT.service" 2>/dev/null
		systemctl reset-failed "$UNIT.service" 2>/dev/null
		ok "stopped · $(neighbors)"
		exit 0 ;;

	*)
		log "Status"
		inf "$(neighbors)"
		inf "unit: $(systemctl is-active "$UNIT.service" 2>/dev/null)"
		inf "load: $(uptime | sed 's/.*average/average/')"
		exit 0 ;;
	esac
fi

# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS ON THE LAPTOP
# ═══════════════════════════════════════════════════════════════════════════
HERE=$(cd "$(dirname "$0")/.." && pwd)
ON_SERVER="bash $TREE/benches/$(basename "$0") --on-server"

# ⛔ The remote script is a FILE already on the machine, and `sudo -S` receives only
#    the password: `printf … | sudo -S bash -s` would give bash an empty stdin, and
#    «it did nothing» would look the same as «it worked».
# ⛔ And no `</dev/null` at the end: that redirect wins over `sudo -S`, which then
#    no longer reads the password («no password was provided»).
remote() { ssh -o BatchMode=yes "$MACHINE" \
	"printf '%s\n' '$SUDO_PASSWORD' | sudo -S -p '' env $1 $ON_SERVER $2"; }

STEP=${1:-status}
case "$STEP" in
ship)
	log "1 · Carrying the sources to $TREE"
	# ⛔ WITHOUT `sudo`: `printf … | sudo -S` would eat stdin, which here IS the
	#    `tar` stream.  And it is not needed: /media/REMOTIX/src belongs to `nicfio`.
	# ⛔ `benches/rcp` is carried too: the Makefile refuses to build if it cannot
	#    compare the two copies of `rcp.c` (R12.3).
	# ⛔ And the laptop's objects and binary are EXCLUDED: if they were sent, `make`
	#    would find everything up to date and the laptop's binary would remain — the
	#    D5 form, «a stale binary stays green».
	tar -C "$HERE" --exclude='*.o' --exclude='src/remotix' -czf - \
		src benches/rcp \
		benches/01-b3-client.py benches/01-b8-unblock.py \
		benches/07-b42-judge.py \
		benches/tools-card-groups.sh benches/07-b64-terreno.sh benches/07-b64-scena.py benches/07-b64-orecchio.py | \
		ssh -o BatchMode=yes "$MACHINE" "mkdir -p $TREE && tar -C $TREE -xzf -" || {
		ko "⛔ the sources did not arrive"; exit 2; }
	ok "sources in $TREE"

	log "2 · Building inside the container"
	if ! ssh -o BatchMode=yes "$MACHINE" \
		"printf '%s\n' '$SUDO_PASSWORD' | sudo -S -p '' bash /media/REMOTIX/enter.sh --root \
		 'DEPS_PREFIX=/srv/src/b2/prefisso NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 \
		  bash $INSIDE_TREE/src/build.sh 2>&1 | tail -20'"; then
		ko "⛔ the build failed: I do NOT start anything"
		exit 2
	fi
	ok "built"
	exit 0 ;;
user)
	# ⛔ `REDO_PASSWORD` MUST CROSS THE ssh — 25 August 2026.
	#   This morning's cure (do not redo the password of a user that already
	#   exists) had been put in the half that runs ON THE SERVER, but the variable
	#   was not in this list: `REDO_PASSWORD=1` did not get over there and did
	#   nothing.  ⚠ And the way it failed is the usual one: no
	#   error, no line, the password simply was not redone.
	remote "ACCOUNT=$ACCOUNT UID_B=$UID_B USER_PASSWORD=$USER_PASSWORD WORKDIR=$WORKDIR REDO_PASSWORD=${REDO_PASSWORD:-0}" utente ;;
start)
	remote "PORT=$PORT ADDR=$ADDR TREE=$TREE WORKDIR=$WORKDIR UNIT=$UNIT NO_RT=${NO_RT:-0} RTPRIO=${RTPRIO:-20} SERVER_OPTIONS='${SERVER_OPTIONS:-}'" accendi ;;
unblock)
	remote "ADDR=$ADDR INSIDE_TREE=$INSIDE_TREE INSIDE_WORK=$INSIDE_WORK" sblocca ;;
stop)
	remote "PORT=$PORT WORKDIR=$WORKDIR UNIT=$UNIT" spegni ;;
*)
	remote "PORT=$PORT WORKDIR=$WORKDIR UNIT=$UNIT" stato ;;
esac
