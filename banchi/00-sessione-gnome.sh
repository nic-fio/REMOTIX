#!/bin/bash
#
# 00-sessione-gnome.sh — starts a GNOME session with no monitor, and VERIFIES that
# it is headless instead of hoping so.
#
#   bash 00-sessione-gnome.sh avvia    composes the environment and starts the session
#   bash 00-sessione-gnome.sh stato    is it there? and is it headless?
#   bash 00-sessione-gnome.sh ferma    closes it
#
# ---------------------------------------------------------------------------
# WHY IT EXISTS, GIVEN THAT THE PRODUCT WILL KNOW HOW TO DO IT ITSELF
#
# At phase 0 the product does not exist yet, and the positive control of the whole
# project — Mutter's ~37 frames — needs a live session.  This bench
# does the minimum to get one, with the same recipe that `fondamenta/remotix-c/src/sessione.c`
# uses in the product: the environment is COMPOSED from scratch, one variable at a time.
#
# ---------------------------------------------------------------------------
# ⛔ THE CHECK THAT IS THE REAL REASON FOR THIS FILE
#
# On GNOME, when entering the unlock dialog, Mutter closes capture, control and
# input and REFUSES to recreate them.  The only exception is `is_headless()`.
#
# And we are headless BY ACCIDENT: Mutter puts itself there when the
# logind session it attaches to has no seat
# (`meta-backend-native.c:759-764`, read on 9 Aug 2026).  None of our lines
# asks for it.  `DECISIONI.md` §4.3-bis says this must be treated as a
# REQUIREMENT: it is declared, verified after startup, and if it is missing we fail
# saying so.
#
# ⭐ The observable signal is a sentence from Mutter itself — «No seat assigned,
#    running headlessly» — i.e. we ASK the component instead of deducing
#    (`LEZIONI.md` §1.6 and §1.11 rule 2).  Looking at «it opened a render node»
#    or «the session is there» would be error form E1: necessary taken for
#    sufficient.
#
# ---------------------------------------------------------------------------
set -uo pipefail

UID_UTENTE=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$UID_UTENTE}
REGISTRO=$RUNTIME/remotix-sessione.log
REGISTRO_SHELL=$RUNTIME/mutter.log
COMANDO="exec gnome-session --session=gnome"

# ---------------------------------------------------------------------------
# ⛔ WHERE WHAT MUTTER SAYS ENDS UP, AND WHY IT IS NOT WHERE IT SEEMS
#
# `gnome-session` does NOT launch gnome-shell: it starts the user unit
# `org.gnome.Shell@wayland.service`.  So the Shell does not inherit our
# redirection, and its messages go to the journal — i.e. elsewhere.
#
# ⛔ And on this machine the journal is not a way: `journalctl --user`
#    answers «No journal files were found» (the rootfs lives in RAM).  On the first
#    round, 9 Aug 2026, it answered worse — «insufficient permissions» —
#    and a `grep` that found nothing would have passed for «Mutter did not
#    say it».  A DENIED read that looks like an EMPTY read: `LEZIONI.md` §1.9.
#
# ⭐ The cure needs no root: the unit is a USER unit, so a drop-in in
#    ~/.config/systemd/user wins over the system one, and we can send
#    the Shell's output to a file of our own.
# ---------------------------------------------------------------------------
registro_shell()
{
	local cartella=$HOME/.config/systemd/user/org.gnome.Shell@wayland.service.d

	mkdir -p "$cartella"
	cat >"$cartella/00-registro.conf" <<CONF
[Service]
StandardOutput=append:$REGISTRO_SHELL
StandardError=append:$REGISTRO_SHELL
CONF
	systemctl --user daemon-reload
}

# ---------------------------------------------------------------------------
# The environment, composed from scratch.
#
# ⛔ EMPTY SHELL, and it is not pedantry: `gnome-session.in:3-14` RE-EXECUTES itself
#    inside a login shell if `$SHELL` is in /etc/shells — i.e. it
#    drags back in `~/.profile` and everything written there.  It is the
#    trap of `LEZIONI.md` §5 and it is in `STUDI.md` §gnome §3.1.
#
# ⛔ XDG_SESSION_TYPE=wayland IS NEEDED: the Shell unit carries
#    `ConditionEnvironment=XDG_SESSION_TYPE=wayland`, and without it the compositor is
#    not started at all — the session starts crippled and nobody explains why.
# ---------------------------------------------------------------------------
ambiente()
{
	printf '%s\n' \
	    "HOME=$HOME" \
	    "USER=$(id -un)" \
	    "PATH=/usr/local/bin:/usr/bin:/bin" \
	    "SHELL=" \
	    "LANG=C.UTF-8" \
	    "XDG_RUNTIME_DIR=/run/user/$UID_UTENTE" \
	    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID_UTENTE/bus" \
	    "XDG_CURRENT_DESKTOP=GNOME" \
	    "XDG_SESSION_DESKTOP=gnome" \
	    "XDG_SESSION_TYPE=wayland"
}

viva()
{
	pgrep -u "$UID_UTENTE" -x gnome-shell >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# ⛔ THE UNIT IS STOPPED AND WE WAIT FOR IT TO BE INACTIVE — no kill and restart.
#
# `LEZIONI.md` §2.3-ter, paid for on Plasma on 8 Aug 2026 and paid again here on the 9th
# on GNOME: between «I killed the process» and «the service manager knows it» there is an
# interval, and a bench that restarts inside that interval behaves
# differently from the first run.
#
# ⭐ On GNOME the symptom is worse than on KDE, because THERE IS NO ERROR: on the
#    first round `pkill gnome-session` left `gnome-session-manager@gnome`
#    ACTIVE with the Shell dead, and the restart did nothing at all — the
#    session was «already started» for a manager that no longer had a
#    compositor.  Forty seconds of waiting and not one line saying why.
# ---------------------------------------------------------------------------
# ⛔ AND THE FAREWELL IS `Logout(2)`, not `systemctl --user stop`.
#
#    Tried on 9 Aug 2026: stopping `gnome-session.target` leaves
#    `gnome-session-manager@gnome.service` ACTIVE — `gnome-session` does not exit after
#    starting the target, it opens a fifo and sleeps, exiting once the session is torn down
#    (`STUDI.md` §gnome §3.2).  `Logout(1)` is not enough: it shows the dialog if there is an
#    inhibitor, and in an unattended session nobody sees it.
ferma_e_aspetta()
{
	local scadenza=$((SECONDS + ${1:-45}))
	local stato

	gdbus call --session -d org.gnome.SessionManager -o /org/gnome/SessionManager \
	    -m org.gnome.SessionManager.Logout 2 >/dev/null 2>&1

	while [ $SECONDS -lt $scadenza ]; do
		stato=$(systemctl --user is-active gnome-session-manager@gnome.service)
		# ⛔ WE WAIT FOR `inactive`, NOT «different from active».
		#
		#    `is-active` goes through `deactivating`, which is not `active` — and a
		#    guard written as `!= active` lets the bench restart INSIDE
		#    the teardown interval, i.e. exactly the defect this
		#    function exists to remove.  Measured on 9 Aug: the wrong
		#    condition unblocked after half a second, with systemd still at
		#    work.
		case "$stato" in
		inactive|failed|unknown)
			if ! viva; then
				# Failed units stay failed and block the next round.
				systemctl --user reset-failed 2>/dev/null
				return 0
			fi
			;;
		esac
		sleep 0.5
	done
	return 1
}

# ⛔ We do not wait for a silence: we wait for an EVENT, with a declared ceiling.
attendi()
{
	local scadenza=$((SECONDS + ${1:-40}))

	while [ $SECONDS -lt $scadenza ]; do
		if viva && busctl --user list 2>/dev/null | grep -q org.gnome.Shell; then
			return 0
		fi
		sleep 0.5
	done
	return 1
}

# ---------------------------------------------------------------------------
# The headless check.
#
# Three distinct outcomes, and the third is the one `LEZIONI.md` §1.9 demands:
# «empty» and «forbidden» must not look the same.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⛔ AND THE PROOF HAS TWO SIDES, BECAUSE HEADLESS IS REACHED IN TWO WAYS.
#
# Read in `meta-backend-native.c:748-764` on 9 Aug 2026:
#
#     if (priv->mode == META_BACKEND_NATIVE_MODE_HEADLESS || …)
#       return TRUE;                       ← ASKED: returns at once, NO message
#     launcher = meta_launcher_new (…);
#     if (!meta_launcher_get_seat_id (launcher))
#       { priv->mode = HEADLESS;
#         g_message ("No seat assigned, running headlessly"); }   ← UNDERGONE: it says so
#
# ⭐ So the sentence «No seat assigned» appears ONLY on the accidental path.
#    The first draft of this bench looked for that — and on a healthy session,
#    started with `--headless` as `DECISIONI.md` §4.3-bis wants, it would have given
#    RED FOREVER.  It is `LEZIONI.md` §1.11: for every indirect proof one must
#    write what the opposite case would look like, or the proof does not discriminate.
#
# ⚠ And we read the command line of the PROCESS, not the drop-in file: that
#   the option is written does not mean it is in force (§1.11 again, and §1.8).
# ---------------------------------------------------------------------------
headless()
{
	local pid cmdline

	pid=$(pgrep -u "$UID_UTENTE" -x gnome-shell | head -1)
	if [ -z "$pid" ]; then
		echo "UNKNOWN: there is no gnome-shell to ask"
		return 2
	fi

	cmdline=$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null)
	if [ -z "$cmdline" ]; then
		echo "UNKNOWN: I cannot read /proc/$pid/cmdline (read denied?)"
		return 2
	fi

	case "$cmdline" in
	*--headless*)
		echo "YES, and it is ASKED FOR: gnome-shell runs with --headless"
		echo "    command line: $cmdline"
		return 0
		;;
	esac

	# We did not ask for it: then the only hope is the accidental path,
	# and to know it we need the log.
	if [ ! -s "$REGISTRO_SHELL" ]; then
		echo "UNKNOWN: --headless is not on the command line, and Mutter's log"
		echo "        is empty ($REGISTRO_SHELL).  It is not «Mutter did not"
		echo "        say it»: it is «we did not hear it»."
		return 2
	fi
	if grep -q "No seat assigned, running headlessly" "$REGISTRO_SHELL"; then
		echo "YES, but by ACCIDENT: Mutter says «No seat assigned, running headlessly»."
		echo "    ⚠ It works, but none of our lines asks for it — DECISIONI.md §4.3-bis"
		echo "      says it must be declared, not inherited from the lack of a seat."
		return 0
	fi

	echo "NO: neither asked for nor accidental."
	echo "    With a seat assigned the screen lock REVOKES capture and input"
	echo "    (STUDI.md §gnome §4, DECISIONI.md §4.3-bis).  The logind sessions:"
	loginctl list-sessions --no-legend | sed 's/^/    /'
	return 1
}

case "${1:-stato}" in
avvia)
	# ⛔ «There is no gnome-shell» does not mean «there is no session»: the
	#    manager can be alive with the compositor dead, and then the command
	#    below does nothing and nobody says so.  We start clean.
	if [ "$(systemctl --user is-active gnome-session-manager@gnome.service)" = active ] \
	   && ! viva
	then
		echo "session manager alive but without a compositor: stopping everything and restarting"
		ferma_e_aspetta || { echo "⛔ it did not stop in time"; exit 1; }
	fi

	if viva; then
		echo "there is already a session: $(pgrep -u "$UID_UTENTE" -x gnome-shell | tr '\n' ' ')"
	else
		registro_shell
		: >"$REGISTRO"; : >"$REGISTRO_SHELL"
		# `setsid --fork` detaches it from our process group: closing
		# the ssh does not take it away.
		env -i $(ambiente) setsid --fork sh -c "exec >>'$REGISTRO' 2>&1; $COMANDO"
		if ! attendi 40; then
			echo "⛔ the session did NOT start within 40 s.  Last lines:"
			tail -n 25 "$REGISTRO" | sed 's/^/    /'
			exit 1
		fi
		echo "session started"
	fi
	echo -n "headless? "; headless
	;;
stato)
	if viva; then
		echo "gnome-shell:  $(pgrep -u "$UID_UTENTE" -c -x gnome-shell) process(es)"
	else
		echo "gnome-shell:  none"
	fi
	echo -n "headless?     "; headless
	;;
ferma)
	ferma_e_aspetta && echo "stopped" || { echo "⛔ it did not stop in time"; exit 1; }
	;;
registro) tail -n "${2:-40}" "$REGISTRO" ;;
*) echo "usage: $0 {avvia|stato|ferma|registro [n]}" >&2; exit 2 ;;
esac
