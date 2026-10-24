#!/bin/sh
# acl-probe.sh <user> — INSIDE a box, privileged (podman exec --privileged).
# For every desktop process of <user>: pid, name, supplementary groups, and the
# /dev/dri nodes it holds open — the evidence of grant-test.sh (DECISIONS-11 §11.4).
# Output format, one line per process, as in the grant-*.txt of 13 Oct 2026:
#   <pid> <name> [<gids> ] dri: <count> <node>   ("dri: none" when no fd on /dev/dri)
U=$1
UIDN=$(id -u "$U" 2>/dev/null) || exit 1
for d in /proc/[0-9]*; do
	pid=${d#/proc/}
	[ "$(awk '/^Uid:/ {print $2}' "$d/status" 2>/dev/null)" = "$UIDN" ] || continue
	name=$(cat "$d/comm" 2>/dev/null)
	case "$name" in remotix|gnome-shell|kwin_wayland|kwin_x11|plasmashell|labwc|Xwayland) ;; *) continue ;; esac
	groups=$(awk '/^Groups:/ {$1=""; print}' "$d/status" | sed 's/^ //')
	nodes=$(ls -l "$d/fd" 2>/dev/null | sed -n 's/.* -> \(\/dev\/dri\/[a-zA-Z0-9]*\)$/\1/p' | sort | uniq -c | sed 's/^ *//')
	if [ -z "$nodes" ]; then
		printf '      %s %s [%s ] dri: none\n' "$pid" "$name" "$groups"
	else
		echo "$nodes" | while read -r n node; do
			printf '      %s %s [%s ] dri: %2s %s\n' "$pid" "$name" "$groups" "$n" "$node"
		done
	fi
done
