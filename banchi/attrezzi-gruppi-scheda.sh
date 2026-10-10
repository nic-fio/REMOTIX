#!/bin/bash
#
# attrezzi-gruppi-scheda.sh — ⭐ THE ONLY PLACE where a bench puts a
# tenant into the card's groups, and ⭐ THE ONLY ONE where it VERIFIES they are there.
#
#   . banchi/attrezzi-gruppi-scheda.sh      # and then: gruppi_scheda_dai_a USER
#   bash banchi/attrezzi-gruppi-scheda.sh USER        # as a program
#   bash banchi/attrezzi-gruppi-scheda.sh --testo       # ⭐ it PRINTS itself, for whoever
#                                                       #   runs elsewhere
#
# ---------------------------------------------------------------------------
# ⛔⛔⭐ THE DEFECT THIS FILE CURES — «the session that is born blind»
#
# `fasi/10-multi-tenant-e-il-budget.md` §7.4: no application manages to
# open a window, zero frames, ever — `provanic4/5/6` on **98 · 55 · 50**
# attempts.  It blocked five tests of the anti-regression net and postponed
# a whole phase.
#
# ⭐ THE CAUSE, measured on the real machine on 27 Aug 2026: the tenant is not
#    in the groups of the `/dev/dri` nodes (here `video` and `render`).
#
#   | tenants WITH the two groups | `[M]` **17 out of 17** see (1.92-2.10 s) |
#   | WITHOUT                     | `[M]` **0 out of 4**, never in 90 s, zero frames |
#   | ⭐ counter-test             | groups given to the same tenant ⇒ 2.04 s |
#
# ⛔⛔ AND THE BENCHES CREATED BLIND TENANTS ON THEIR OWN.  A bench that measures
#    a session that does not see, believing it healthy, is WORSE than a bench that does not
#    run: it writes a number and does not declare which product it belongs to.
#
# ⭐ WHY ONE FILE, AND NOT A LINE IN EVERY TERRAIN (`LEZIONI.md` §1.47):
#    ten copies of the same line are ten places to diverge from, and they had
#    already diverged — `src/provisiona.sh` gave the groups, `attrezzi-utenti.sh`
#    did not, and neither of the two said so.
#
# ⛔ THE GROUP IS READ FROM THE NODE, NEVER FROM A HARD-CODED NAME.  `video` and `render`
#    are the names of THIS distribution: inside the `enter.sh` chroot (which
#    has `/dev` in rbind but an `/etc/group` all of its own) the same gid may have
#    another name, or none.  ⇒ we start from the **gid** of the `stat`, and the name
#    is ASKED of `getent`.
#
# ⚠ AND ALL THE NODES ARE SCANNED, not `renderD128`: `renderD128` and `renderD129`
#   swap between two boots (`src/provisiona.sh` already says so), and `cardN` and
#   `renderDN` have DIFFERENT groups that are both needed.
#
# ⭐ AND THE VERIFICATION COMPARES THE NUMBERS, not the names (E1, «written is not in
#   force»): the old `id -nG | grep -qw render` would have said OK on a
#   machine where the node belongs to another group.
# ---------------------------------------------------------------------------

# ═══ CORPO-INIZIO ═══  ⛔ From here to CORPO-FINE is what `--testo` prints:
#     nothing in here must depend on this file or on this machine.

# The gids of the card's nodes, one per line, without duplicates.
gruppi_scheda_gid() {
	_gs_n=; _gs_g=
	for _gs_n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$_gs_n" ] || continue
		_gs_g=$(stat -c %g "$_gs_n" 2>/dev/null) || continue
		[ -n "$_gs_g" ] && printf '%s\n' "$_gs_g"
	done | sort -un
}

# The name of a gid, or empty if /etc/group has none.
gruppi_scheda_nome() { getent group "$1" 2>/dev/null | cut -d: -f1; }

# Which node has that gid — needed only to write a message that makes sense.
gruppi_scheda_nodo() {
	_gs_n=
	for _gs_n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$_gs_n" ] || continue
		[ "$(stat -c %g "$_gs_n" 2>/dev/null)" = "$1" ] && { printf '%s' "$_gs_n"; return 0; }
	done
	printf '/dev/dri'
}

# Is the tenant in the group of that gid?  ⭐ The NUMBERS are compared.
gruppi_scheda_ci_sta() {
	_gs_x=
	for _gs_x in $(id -G "$1" 2>/dev/null); do
		[ "$_gs_x" = "$2" ] && return 0
	done
	return 1
}

# The gids of the nodes that the tenant is MISSING, separated by spaces.
gruppi_scheda_mancanti() {
	_gs_g=; _gs_m=
	for _gs_g in $(gruppi_scheda_gid); do
		gruppi_scheda_ci_sta "$1" "$_gs_g" || _gs_m="${_gs_m:+$_gs_m }$_gs_g"
	done
	printf '%s' "$_gs_m"
}

# ⭐⭐ THE WORK: puts the tenant into the nodes' groups and VERIFIES they are there.
#
#   0  ⭐ really in (or nothing to do)
#   3  ⛔ NOT in after the attempt — the caller MUST stop
#   4  ⛔ the groups were added but the user manager was ALREADY ALIVE:
#         written yes, in force no — the caller MUST stop
#   5  ⛔ a gid of the nodes has no name in /etc/group
#
# ⛔ It does not shut anything down by itself: `loginctl terminate-user` also takes down the
#    server's child, and in phase 10/11 tenants are SHARED among benches
#    that are measuring (I2).  ⇒ it SAYS so, and stops.
gruppi_scheda_dai_a() {
	_gs_u=$1
	_gs_pref=${GRUPPI_SCHEDA_PREFISSO:-    }
	_gs_gid=$(gruppi_scheda_gid)

	if [ -z "$_gs_gid" ]; then
		printf '%s\033[1;31m⛔\033[0m  no `cardN`/`renderDN` node in /dev/dri: on this\n' "$_gs_pref"
		printf '%s    machine the compositor will draw in SOFTWARE, and no group\n' "$_gs_pref"
		printf '%s    can fix that.  ⚠ The number this bench will measure is NOT\n' "$_gs_pref"
		printf '%s    that of the product in hardware.\n' "$_gs_pref"
		return 0
	fi

	# 1. The names. ⛔ A gid without a name is not invented and not created from here.
	_gs_nomi=
	for _gs_g in $_gs_gid; do
		_gs_nome=$(gruppi_scheda_nome "$_gs_g")
		if [ -z "$_gs_nome" ]; then
			printf '%s\033[1;31m⛔⛔\033[0m gid %s (of %s) has NO name in /etc/group here:\n' \
				"$_gs_pref" "$_gs_g" "$(gruppi_scheda_nodo "$_gs_g")"
			printf '%s    the tenant «%s» cannot join it, and their session WILL BE BORN\n' "$_gs_pref" "$_gs_u"
			printf '%s    BLIND.  ⭐ The cure, as root: `groupadd -g %s scheda%s`\n' "$_gs_pref" "$_gs_g" "$_gs_g"
			return 5
		fi
		case " $_gs_nomi " in *" $_gs_nome "*) continue ;; esac
		_gs_nomi="${_gs_nomi:+$_gs_nomi }$_gs_nome"
	done

	# 2. What is missing BEFORE — needed to know whether we are changing something.
	_gs_prima=$(gruppi_scheda_mancanti "$_gs_u")

	if [ -n "$_gs_prima" ]; then
		# ⚠ `usermod -aG` wants the names separated by commas.
		_gs_virgole=$(printf '%s' "$_gs_nomi" | tr ' ' ',')
		usermod -aG "$_gs_virgole" "$_gs_u" || {
			printf '%s\033[1;31m⛔\033[0m  `usermod -aG %s %s` did NOT succeed\n' \
				"$_gs_pref" "$_gs_virgole" "$_gs_u"
			return 3; }
	fi

	# 3. ⭐ READ IT BACK — E1: written is not in force.
	_gs_dopo=$(gruppi_scheda_mancanti "$_gs_u")
	if [ -n "$_gs_dopo" ]; then
		for _gs_g in $_gs_dopo; do
			printf '%s\033[1;31m⛔⛔\033[0m «%s» IS NOT IN THE CARD GROUP «%s» (gid %s, the group\n' \
				"$_gs_pref" "$_gs_u" "$(gruppi_scheda_nome "$_gs_g")" "$_gs_g"
			printf '%s    of %s)\n' "$_gs_pref" "$(gruppi_scheda_nodo "$_gs_g")"
		done
		printf '%s    ⛔ ITS SESSION WOULD BE BORN AND SEE NOTHING: zero frames,\n' "$_gs_pref"
		printf '%s    no window opens, and the loop goes round and round between «BLACK: ZERO MONITORS»\n' "$_gs_pref"
		printf '%s    and «virtual monitor mounted» (phase 10 §7.4 — [M] 0 out of 4 without, 17 out of 17 with).\n' "$_gs_pref"
		printf '%s    ⛔ THIS BENCH MUST NOT MEASURE: it would measure a product that does not exist.\n' "$_gs_pref"
		return 3
	fi

	if [ -z "$_gs_prima" ]; then
		printf '%s\033[1;32mOK\033[0m  ⭐ «%s» was already in the groups of the card nodes (%s): their\n' \
			"$_gs_pref" "$_gs_u" "$_gs_nomi"
		printf '%s    session can see in hardware\n' "$_gs_pref"
		return 0
	fi

	printf '%s\033[1;32mOK\033[0m  ⭐ «%s» put into the groups READ FROM THE NODES: %s (gid %s)\n' \
		"$_gs_pref" "$_gs_u" "$_gs_nomi" "$(printf '%s' "$_gs_gid" | tr '\n' ' ')"

	# 4. ⛔⛔ WRITTEN YES, IN FORCE NO — and this is the misleading case.
	#    The groups reach the compositor only when the user manager is
	#    BORN AGAIN: if one was already alive, the session that is running is
	#    still blind, and a bench measuring now would measure darkness.
	if pgrep -u "$_gs_u" >/dev/null 2>&1; then
		printf '%s\033[1;31m⛔⛔\033[0m the groups were ADDED JUST NOW, but «%s» already had\n' \
			"$_gs_pref" "$_gs_u"
		printf '%s    live processes: a process keeps the groups it had when it was BORN.\n' "$_gs_pref"
		printf '%s    ⇒ The session that is running is STILL BLIND.\n' "$_gs_pref"
		printf '%s    ⭐ The cure, as root, and then redo this step:\n' "$_gs_pref"
		printf '%s        loginctl terminate-user %s\n' "$_gs_pref" "$_gs_u"
		printf '%s    ⚠ I do NOT do it: it would also take down the session of another bench (I2).\n' "$_gs_pref"
		return 4
	fi
	return 0
}
# ═══ CORPO-FINE ═══

# ---------------------------------------------------------------------------
# ⭐ AS A PROGRAM — and ⭐ `--testo`, which is what keeps the cure in ONE
#    place even for whoever cannot `.` this file:
#
#   · `banchi/attrezzi-utenti.sh` sends the commands INSIDE the chroot with
#     `enter.sh --root "…"`, and in there this file does not exist;
#   · `banchi/07-b63-terreno.sh` ships a script to the test machine.
#
#   ⚠ The text goes into an already expanded string (`"$TESTO"`, `$(cat …)`):
#     the shell does NOT re-expand the result of an expansion, so the `$`s that
#     are in here arrive over there intact.
# ---------------------------------------------------------------------------
# ⚠ The check on the name of `$0` tells «executed» from «sourced with `.`»:
#   when a terrain does `. attrezzi-gruppi-scheda.sh`, `$0` stays the name of the
#   TERRAIN, and nothing happens below — not even if the terrain had been
#   called itself with an argument.
if [ "$(basename "$0")" = "attrezzi-gruppi-scheda.sh" ]; then
	case "${1:-}" in
	--testo)
		sed -n '/^# ═══ CORPO-INIZIO/,/^# ═══ CORPO-FINE/p' "$0"
		exit 0 ;;
	"")
		printf 'usage: bash %s USER   |   bash %s --testo\n' "$0" "$0"
		exit 2 ;;
	*)
		[ "$(id -u)" -eq 0 ] || { printf '    ⛔ must be run AS ROOT\n'; exit 2; }
		gruppi_scheda_dai_a "$1"
		exit $? ;;
	esac
fi
