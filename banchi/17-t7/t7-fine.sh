#!/bin/bash
# t7-fine.sh — fase 17, T7: la prova dell'abbandono su un desktop ritrovato (col
# binario nuovo gia' nelle scatole), poi le scatole rimesse a 4fb3287d / d1734958.
#   bash t7-fine.sh [DESKTOP]   (predefinito gnome)
set -u
D=${1:-gnome}
T=/media/REMOTIX/tmp/t7
R=/media/REMOTIX/rete11
P=$R/prodotto
L=$R/.scatole.lock
PW=$(sed -n 's/^pass:[[:space:]]*//p' ~/SERVER.ssh | head -1)
S() { printf '%s\n' "$PW" | sudo -S -p '' "$@"; }
exec 9<>"$L"; flock 9; printf 't7-fine-fase17 pid %d' $$ > "$L"
export REMOTIX_SCATOLE_TENUTE=t7-fine-fase17
u=$(id -u)
env XDG_RUNTIME_DIR=/run/user/$u REMOTIX_SCHERMO_ANNIDATO=1 REMOTIX_SUL_SERVER=1 MOZ_ENABLE_WAYLAND=1 \
	WAYLAND_DISPLAY=$(cat /run/user/$u/15-compositori/$D) python3 -u $T/t7-abbandono.py $D 60 2>&1 | tee $T/$D-abbandono.log | tail -3
echo "$(date +%T) rimetto il binario 4fb3287d e il PAM d1734958"
rm -f $P/remotix; cp $P/remotix.4fb3287d $P/remotix
cp $T/remotix.pam.prima $P/remotix.pam
for d in gnome kde xfce lxqt; do
	S bash $R/11-accendi.sh prodotto $d 2>&1 | tail -1
	S bash $R/11-accendi.sh server $d 2>&1 | tail -1
	S podman exec rete11-$d sh -c 'md5sum /opt/remotix/remotix /etc/pam.d/remotix; cat /etc/remotix/utenti-negati; loginctl list-sessions --no-legend'
done
echo "$(date +%T) FINE — la serratura si libera"
