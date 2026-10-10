#!/bin/bash
# t7-campagna.sh — phase 17, T7: upgrading without closing the desktops, on the four
# boxes.  On the server, as nicfio.
#
#   bash t7-campagna.sh BINARY [DESKTOP...]   (default: gnome kde xfce lxqt)
#     BINARY   the cured remotix (built for debian13)
#   env: SUITE=0 skips the short suite · LASCIA=1 does not put 4fb3287d back at the end
#        MODI="aggiornamento riavvio" (default)
#
# For each desktop: t7-aggiorna.py aggiornamento (desktops born with 4fb3287d, then
# new binary and restart with --tetto-sessioni 2) and t7-aggiorna.py riavvio
# (desktops born with the new one).  Then the short suite (f001 f003 f004 f011 f016 f018,
# chrome and firefox) with the new binary; then the 4fb3287d binary and the previous PAM.
# The boxes' lock is held for the whole round.
set -u
BIN=$1; shift
DESKTOP=${*:-gnome kde xfce lxqt}
T=/media/REMOTIX/tmp/t7
R=/media/REMOTIX/rete11
P=$R/prodotto
L=$R/.scatole.lock
PW=$(sed -n 's/^pass:[[:space:]]*//p' ~/SERVER.ssh | head -1)
S() { printf '%s\n' "$PW" | sudo -S -p '' "$@"; }
cd "$T" || exit 1

exec 9<>"$L"
echo "$(date +%T) waiting for the lock (now: $(cat "$L"))"
flock 9
printf 't7-fase17 pid %d' $$ > "$L"
echo "$(date +%T) lock TAKEN"
export REMOTIX_SCATOLE_TENUTE=t7-fase17

[ -f $P/remotix.4fb3287d ] || { echo "⛔ missing $P/remotix.4fb3287d"; exit 1; }
[ -f $T/remotix.pam.prima ] || cp $P/remotix.pam $T/remotix.pam.prima
[ "$(md5sum < $T/remotix.pam.prima | cut -c1-8)" = d1734958 ] || { echo "⛔ remotix.pam.prima is not d1734958"; exit 1; }
NUOVO=$(md5sum < "$BIN" | cut -c1-8)
cp "$BIN" $P/remotix.$NUOVO
echo "new binary: $NUOVO"
export T7_NUOVO=$NUOVO

u=$(id -u)
declare -A WL
for d in gnome kde xfce lxqt; do WL[$d]=$(cat /run/user/$u/15-compositori/$d); done
ORDINE=(gnome kde xfce lxqt gnome kde)
for d in $DESKTOP; do
	for i in 0 1 2 3; do [ "${ORDINE[$i]}" = "$d" ] && k=$i; done
	for m in ${MODI:-aggiornamento riavvio}; do
		echo "$(date +%T) ===== $d $m"
		env XDG_RUNTIME_DIR=/run/user/$u REMOTIX_SCHERMO_ANNIDATO=1 REMOTIX_SUL_SERVER=1 \
			REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland" MOZ_ENABLE_WAYLAND=1 \
			T7_WL_FIREFOX=${WL[$d]} T7_WL_CHROME=${WL[${ORDINE[$((k+1))]}]} \
			T7_WL_TERZO=${WL[${ORDINE[$((k+2))]}]} WAYLAND_DISPLAY=${WL[$d]} \
			python3 -u $T/t7-aggiorna.py "$d" "$m" 2>&1 | tee $T/$d-$m.log | grep -a "^T7 \|re-enters\|found again:\|third\|⛔\|Traceback"
	done
done

if [ "${SUITE:-1}" = 1 ]; then
	echo "$(date +%T) ===== the short suite with the binary $NUOVO"
	rm -f $P/remotix; cp $P/remotix.$NUOVO $P/remotix; cp $T/remotix.pam $P/remotix.pam
	for d in gnome kde xfce lxqt; do
		S bash $R/11-accendi.sh prodotto $d 2>&1 | tail -1
		S bash $R/11-accendi.sh server $d 2>&1 | tail -1
		S podman exec rete11-$d md5sum /opt/remotix/remotix /etc/pam.d/remotix
	done
	python3 /media/REMOTIX/src/controllo/banchi/15-suite/15-giro.py --giro 17-t7 \
		--prove ${PROVE:-f001,f003,f004,f011,f016,f018} 2>&1 | tail -60 | tee $T/suite.log
fi

if [ "${LASCIA:-0}" != 1 ]; then
	echo "$(date +%T) putting back the 4fb3287d binary and the d1734958 PAM"
	rm -f $P/remotix; cp $P/remotix.4fb3287d $P/remotix
	cp $T/remotix.pam.prima $P/remotix.pam
	for d in gnome kde xfce lxqt; do
		S bash $R/11-accendi.sh prodotto $d 2>&1 | tail -1
		S bash $R/11-accendi.sh server $d 2>&1 | tail -1
		S podman exec rete11-$d sh -c 'md5sum /opt/remotix/remotix /etc/pam.d/remotix; cat /etc/remotix/utenti-negati'
	done
fi
echo "$(date +%T) END — the lock is released"
