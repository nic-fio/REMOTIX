#!/bin/sh
# 17-t3-gruppi.sh — phase 17, T3 line C: the ENGINE STEP "people in the
# GPU groups", done by hand in the test VM, and its undo.
#
#   (INSIDE the VM, as root)  sh 17-t3-gruppi.sh iscrivi | annulla
#
# ⭐ `DECISIONI.md` §10.12: the package does not touch groups; the engine does
#    (`installatore/motore`, action `aggiungi-utente-a-gruppo`, with its
#    log).  Until the engine installs the packages, the tests do the same
#    gesture here, with the same criterion, and record it as "engine step".
#
# ⭐ `DECISIONI.md` §7.21: a remote session has no seat, so logind's ACL
#    on the /dev/dri nodes never arrives; ONLY the groups remain.  At
#    install time the people already on the machine are enrolled: UID_MIN..UID_MAX
#    from login.defs, and only those with a real shell (not service accounts).
#    The group names are asked of the NODES (`stat -c %g`), not hard-coded.
#
# ⭐ `fasi/17-l-installatore.md` §6.4 and §6.6.4 (R6, R33): every
#    person-group pair is recorded in the log with its ORIGIN:
#        c-era  <person> <group>   was already there  ⇒ PRE-EXISTING, never touched
#        messo  <person> <group>   the package put it ⇒ DIRECT, `annulla` removes it
#    A pair already recorded is not recorded again: installing twice
#    changes nothing (R5), and an upgrade does not turn a "messo" into a "c-era".
#
# ⚠ What this log does NOT see: the people the PRODUCT enrolls at
#   their first connection (`figlio.c`, `iscrivi_ai_gruppi_della_scheda`).
#   Today those go only to the journal; ⇒ uninstalling does not remove them.
#   The same holds for the engine: noted in §13.1 as "to do".
#
# ⚠ Always exits with 0: a failed enrollment is SAID.
set -u

REGISTRO=/var/tmp/remotix-t3-gruppi.registro

# login.defs: on openSUSE it lives in /usr/etc (and /etc overrides it if present).
leggi_defs()
{
	v=""
	for f in /usr/etc/login.defs /etc/login.defs; do
		[ -r "$f" ] || continue
		x=$(awk -v k="$1" '$1 == k { print $2 }' "$f")
		[ -n "$x" ] && v=$x
	done
	printf '%s' "${v:-$2}"
}

gruppi_della_scheda()
{
	for n in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do
		[ -e "$n" ] || continue
		g=$(stat -c %g "$n" 2>/dev/null) || continue
		[ "$g" = 0 ] && continue       # root: nobody goes into root's group
		getent group "$g" | cut -d: -f1
	done | sort -u
}

# already there (as supplementary or primary group)?
membro()
{
	id -nG "$1" 2>/dev/null | tr ' ' '\n' | grep -qx "$2"
}

annotata()
{
	[ -f "$REGISTRO" ] && grep -qE "^(c-era|messo) $1 $2\$" "$REGISTRO"
}

iscrivi()
{
	min=$(leggi_defs UID_MIN 1000)
	max=$(leggi_defs UID_MAX 60000)
	gruppi=$(gruppi_della_scheda)
	if [ -z "$gruppi" ]; then
		echo "remotix: no /dev/dri node on this machine: no GPU group to give"
		return 0
	fi
	[ -f "$REGISTRO" ] || { : >"$REGISTRO"; chmod 0600 "$REGISTRO"; }
	persone=$(awk -F: -v a="$min" -v b="$max" \
		'$3 >= a && $3 <= b && $7 !~ /(nologin|false)$/ { print $1 }' /etc/passwd)
	for p in $persone; do
		for g in $gruppi; do
			annotata "$p" "$g" && continue
			if membro "$p" "$g"; then
				echo "c-era $p $g" >>"$REGISTRO"
			elif gpasswd -a "$p" "$g" >/dev/null 2>&1; then
				echo "messo $p $g" >>"$REGISTRO"
				echo "remotix: $p enrolled in $g (the remote session has no seat: without it, blank page)"
			else
				echo "remotix: ⛔ $p NOT enrolled in $g (gpasswd refused)"
			fi
		done
	done
	return 0
}

annulla()
{
	[ -f "$REGISTRO" ] || return 0
	grep '^messo ' "$REGISTRO" | while read -r _ p g; do
		getent passwd "$p" >/dev/null || continue
		if membro "$p" "$g" && gpasswd -d "$p" "$g" >/dev/null 2>&1; then
			echo "remotix: $p removed from $g (the engine step had put it there)"
		fi
	done
	rm -f "$REGISTRO"
	return 0
}

case ${1:-} in
iscrivi) iscrivi ;;
annulla) annulla ;;
*) echo "usage: $0 iscrivi|annulla" >&2; exit 2 ;;
esac
