#!/bin/bash
# ===========================================================================
# 10-f2-accendi.sh — accende il server dell'incarico F2 sulla porta 8420.
#
# ⛔ E' `src/riavvia-7900.sh` ridotto all'osso e portato sul MIO isolamento:
#    porta 8420, albero `/media/REMOTIX/src/10f2-src`, lavoro
#    `/media/REMOTIX/tmp/10f2`, unita' `remotix-8420`.  ⚠ Non tocca nulla di
#    altri: ne' la 8400 del coordinamento, ne' `provanic1` di F1.
#
# ⭐ Le due verifiche di `riavvia-7900.sh` restano, perche' sono quelle che
#    hanno gia' fatto perdere una giornata a qualcuno:
#      · le librerie si leggono da `/proc/PID/maps`, cioe' da quel che il
#        processo VIVO ha aperto, non da un file scritto la volta scorsa;
#      · ⛔ A6: il cgroup del server non deve contenere `user@` ne' `session-`,
#        o `pam_systemd` non creera' la sessione dei figli e il desktop non
#        partira' — con la faccia di «il browser non funziona».
#
# uso (da root, sulla macchina):  bash 10-f2-accendi.sh [opzioni in piu']
# ===========================================================================
set -eu

LAV=/media/REMOTIX/tmp/10f2
SRC=/media/REMOTIX/src/10f2-src/src
B2=/media/REMOTIX/src/b2
UNITA=remotix-8420
PORTA=8420

mkdir -p "$LAV"

LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

systemctl stop   "$UNITA.service" 2>/dev/null || true
systemctl reset-failed "$UNITA.service" 2>/dev/null || true
i=0
while ss -uln 2>/dev/null | grep -q ":$PORTA " && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

systemd-run \
	--unit="$UNITA" --collect --description="REMOTIX_V2 — F2, il browser dentro il desktop remoto" \
	--working-directory="$SRC" \
	--setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
	--property=StandardOutput=append:"$LAV/registro.log" \
	--property=StandardError=append:"$LAV/registro.log" \
	--property=KillMode=mixed \
	--property=LimitRTPRIO=20 \
	--property=LimitNICE=-11 \
	"$SRC/remotix" \
	--indirizzo 0.0.0.0 --nome 192.168.0.2 --porta "$PORTA" \
	--certificati "$LAV/certificati" \
	--pagina "$SRC/pagina.html" \
	--ban-file "$LAV/ban" \
	--comando-socket "$LAV/comando.sock" \
	--rilievo "$LAV/rilievo" \
	--parlantina "$@" >/dev/null

i=0; NUOVO=""
while [ $i -lt 50 ]; do
	NUOVO=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null || echo 0)
	[ -n "$NUOVO" ] && [ "$NUOVO" != "0" ] && break
	i=$((i+1)); sleep 0.1
done
if [ -z "$NUOVO" ] || [ "$NUOVO" = "0" ]; then
	echo "⛔ il server non e' partito — le ultime righe del registro:"
	tail -15 "$LAV/registro.log"
	exit 1
fi
echo "$NUOVO" > "$LAV/pid"

# ⛔ Le librerie del processo VIVO, e si aspetta che il caricatore abbia finito.
i=0; LIBS=""
while [ $i -lt 50 ]; do
	LIBS=$(grep -oE '/[^ ]*(libngtcp2|libnghttp3)[^ ]*' "/proc/$NUOVO/maps" 2>/dev/null | sort -u)
	if echo "$LIBS" | grep -q libngtcp2 && echo "$LIBS" | grep -q libnghttp3; then break; fi
	i=$((i+1)); sleep 0.1
done
if ! echo "$LIBS" | grep -q libngtcp2 || ! echo "$LIBS" | grep -q libnghttp3; then
	echo "⛔ librerie non mappate dopo 5 s: il processo non e' quello che credo"; exit 1
fi

# ⛔ A6 — la trappola silenziosa: il server dentro una sessione utente.
CG=$(cat "/proc/$NUOVO/cgroup" 2>/dev/null || echo "")
case "$CG" in
	*user@*|*session-*)
		echo "⛔⛔ IL SERVER STA DENTRO UNA SESSIONE UTENTE (A6): $CG"; exit 1 ;;
esac

echo "⭐ server $NUOVO su :$PORTA, unita' $UNITA.service, cgroup $CG"
