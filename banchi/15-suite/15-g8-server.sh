#!/bin/bash
# 15-g8-server.sh — the SECOND product server of group G8, inside a box.
#
#   bash 15-g8-server.sh accendi|spegni|sblocca|stato <gnome|kde|xfce|lxqt>
#
# Same binary /opt/remotix/remotix, unit `rete15-g8`, port 8621 gnome ·
# 8622 kde · 8623 xfce · 8624 lxqt, and ITS OWN ban-file, command socket, survey and
# log in /var/lib/rete15-g8/ (model: 11-accendi.sh, case `server`).
#
# ⛔ It serves everything that gets the password wrong (F-027, F-028, N-1, N-4): three
#    failed attempts ban 192.168.0.2 for 12 hours, and on the box's server
#    (8511-8514) they would stop the whole suite.  The ban lives in the memory
#    of THIS process and in ITS file (/var/lib/rete15-g8/ban): the 85xx does not
#    see it — `stato` shows the two ban files side by side.
# ⛔ `sblocca` talks to the command socket (src/comando.c: «SBLOCCA <indirizzo>»).
# ⚠ Stopping the unit closes the sessions born in it (KillMode=mixed):
#    they are only our tenants c15027u*.
#
# From the tablet it goes through ssh; on the server (REMOTIX_SUL_SERVER=1 or from the tree
# /media/REMOTIX/src/controllo) it runs directly.
QUI=$(cd "$(dirname "$0")" && pwd)
if [ -z "${REMOTIX_SUL_SERVER:-}" ] && [ ! -d /media/REMOTIX/src/controllo ]; then
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"REMOTIX_SUL_SERVER=1 bash ${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-g8-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi
exec python3 "$QUI/15-g8-comune.py" "$@"
