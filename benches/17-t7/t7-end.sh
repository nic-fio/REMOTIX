#!/bin/bash
# t7-end.sh — phase 17, T7: the abandonment test on a desktop found again (with the
# new binary already in the boxes), then the boxes put back to 4fb3287d / d1734958.
#   bash t7-end.sh [DESKTOP]   (default gnome)
set -u
D=${1:-gnome}
T=/media/REMOTIX/tmp/t7
R=/media/REMOTIX/rete11
P=$R/prodotto
L=$R/.scatole.lock
PW=$(sed -n 's/^pass:[[:space:]]*//p' ~/SERVER.ssh | head -1)
S() { printf '%s\n' "$PW" | sudo -S -p '' "$@"; }
exec 9<>"$L"; flock 9; printf 't7-fine-fase17 pid %d' $$ > "$L"
export REMOTIX_KEPT_BOXES=t7-fine-fase17
u=$(id -u)
env XDG_RUNTIME_DIR=/run/user/$u REMOTIX_NESTED_SCREEN=1 REMOTIX_ON_SERVER=1 MOZ_ENABLE_WAYLAND=1 \
	WAYLAND_DISPLAY=$(cat /run/user/$u/15-compositori/$D) python3 -u $T/t7-abandonment.py $D 60 2>&1 | tee $T/$D-abbandono.log | tail -3
echo "$(date +%T) putting back the 4fb3287d binary and the d1734958 PAM"
rm -f $P/remotix; cp $P/remotix.4fb3287d $P/remotix
cp $T/remotix.pam.prima $P/remotix.pam
for d in gnome kde xfce lxqt; do
	S bash $R/11-start.sh product $d 2>&1 | tail -1
	S bash $R/11-start.sh server $d 2>&1 | tail -1
	S podman exec rete11-$d sh -c 'md5sum /opt/remotix/remotix /etc/pam.d/remotix; cat /etc/remotix/denied-users; loginctl list-sessions --no-legend'
done
echo "$(date +%T) END — the lock is released"
