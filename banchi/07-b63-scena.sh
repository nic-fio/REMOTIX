#!/usr/bin/env bash
#
# 07-b63-scena.sh — la SCENA IN MOVIMENTO nella sessione di `provav7`.
#
#   bash banchi/07-b63-scena.sh avvia    accende la scena sul monitor del MIO palco
#   bash banchi/07-b63-scena.sh conta    quanti fotogrammi ha disegnato
#   bash banchi/07-b63-scena.sh ferma    ⛔ e si ferma SEMPRE, alla fine di ogni giro
#
# ⛔ `CODER.md` §3.2: la scena si dichiara e si muove sempre.  `[M]` 21 agosto
#    2026, primo giro di questo banco: sul desktop VUOTO di `provav7` la pagina
#    ha dipinto **13 fotogrammi in 30 s e poi piu' niente** — Mutter consegna
#    solo quando qualcosa cambia.  Un confronto worker/non-worker su quella
#    scena avrebbe misurato **13 contro 13** e non avrebbe voluto dire niente.
#
# ⛔ IL BINARIO NON SI RISCRIVE: e' `03-scena` dello step 2 della fase 3, gia'
#    costruito in `/media/REMOTIX/src/03-b17-scena/03-scena` e gia' certificato
#    (marca a 144 bit).  ⚠ Un secondo generatore di scena vorrebbe dire due
#    scene con lo stesso nome, e i numeri di due giri non si confronterebbero.
#
# ⛔ E IL MONITOR NON SI SCRIVE A MANO: si legge dal registro del MIO server.
#    `[M]` 13 agosto 2026 (`03-b17-accendi.sh`): una scena finita sul monitor di
#    un altro banco ha prodotto **zero fotogrammi per dieci secondi con la
#    catena perfettamente funzionante**.  Su questa macchina i monitor virtuali
#    sono piu' d'uno — 7700 e 7730 sono dell'utente.
#
# ⛔ E LA SCENA SI SPEGNE.  «I banchi aprivano sul desktop dell'utente e non
#    chiudevano» e' il difetto del 21 agosto: qui la scena e' nella sessione di
#    `provav7`, ma un processo lasciato acceso tiene la GPU occupata per tutti
#    gli altri nove banchi.
set -uo pipefail

MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
UID_B=${UID_B:-1017}
LAV=${LAV:-/media/REMOTIX/tmp/07-v}
SCENA=${SCENA:-/media/REMOTIX/src/03-b17-scena/03-scena}
SHM=${SHM:-remotix-07-b63}
MOVIMENTO=${MOVIMENTO:-barra}

remoto() {
	local f
	f=$(mktemp)
	cat > "$f"
	scp -q -o BatchMode=yes "$f" "$MACCHINA:/tmp/07-b63-scena-remoto.sh"
	rm -f "$f"
	ssh -o BatchMode=yes "$MACCHINA" \
		"printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash /tmp/07-b63-scena-remoto.sh; rc=\$?; rm -f /tmp/07-b63-scena-remoto.sh; exit \$rc"
}

case "${1:-stato}" in
avvia)
	remoto <<FINE
set -u
LAV=$LAV
[ -x $SCENA ] || { echo "    NO  la scena non c'e': $SCENA"; exit 2; }
[ -S /run/user/$UID_B/wayland-0 ] || { echo "    NO  /run/user/$UID_B/wayland-0 non c'e': nessuna sessione"; exit 2; }
# ⛔ Il monitor si LEGGE dal registro del mio server, non si indovina.
USCITA=\$(grep -ao 'monitor «[^»]*»' \$LAV/registro.log 2>/dev/null | grep -v '«»' | tail -1 | sed 's/monitor «//; s/»//')
if [ -z "\$USCITA" ]; then
	echo "    NO  il MIO registro non nomina nessun monitor: non accendo la scena"
	echo "    --  (serve che qualcuno sia ENTRATO: il monitor virtuale nasce col figlio)"
	exit 2
fi
echo "    --  il palco del MIO prodotto e' il monitor «\$USCITA» (letto, non dedotto)"
if [ -f \$LAV/scena.pid ] && [ -d /proc/\$(cat \$LAV/scena.pid) ]; then
	echo "    OK  la scena e' gia' viva (pid \$(cat \$LAV/scena.pid))"; exit 0
fi
: >> \$LAV/scena.log; chmod 666 \$LAV/scena.log
setpriv --reuid=$UID_B --regid=$UID_B --init-groups \
	env XDG_RUNTIME_DIR=/run/user/$UID_B WAYLAND_DISPLAY=wayland-0 \
	    HOME=/home/provav7 USER=provav7 \
	    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID_B/bus \
	nohup stdbuf -oL -eL $SCENA --uscita "\$USCITA" \
	    --movimento $MOVIMENTO --danno preciso --shm $SHM \
	    --giro "b63-\$(date +%H%M%S)" --loquace \
	    >> \$LAV/scena.log 2>&1 &
pid=\$!
echo \$pid > \$LAV/scena.pid
g=0
while [ \$g -lt 60 ]; do
	[ -d /proc/\$pid ] || break
	grep -q 'scena: giro' \$LAV/scena.log 2>/dev/null && break
	sleep 0.25; g=\$((g+1))
done
if [ ! -d /proc/\$pid ]; then
	echo "    NO  la scena e' morta subito:"; tail -20 \$LAV/scena.log | sed 's/^/        /'; exit 3
fi
# ⛔ «viva» NON e' «disegna» (LEZIONI.md §1.9), e questa scena NON stampa un
#    conteggio periodico: qui si puo' dire soltanto «viva, e attaccata al
#    monitor che volevo».  ⇒ Chi disegna davvero lo dice il contatore
#    \`consegnati\` della pagina, e \`07-b63-worker.py\` si RIFIUTA di pubblicare
#    un numero se quel contatore non e' cresciuto.
if grep -q 'scena: giro' \$LAV/scena.log 2>/dev/null; then
	echo "    OK  scena viva sul monitor «\$USCITA» (pid \$pid) — «disegna» lo dira' la pagina"
	tail -4 \$LAV/scena.log | sed 's/^/        /'
else
	echo "    NO  viva ma non ha nemmeno annunciato il giro: non mi fido"
	exit 3
fi
FINE
	;;

conta)
	ssh -o BatchMode=yes "$MACCHINA" "tail -3 $LAV/scena.log" 2>/dev/null
	;;

ferma)
	remoto <<FINE
if [ -f $LAV/scena.pid ]; then
	p=\$(cat $LAV/scena.pid)
	kill \$p 2>/dev/null && echo "    OK  scena \$p fermata" || echo "    --  non era viva"
	rm -f $LAV/scena.pid
fi
pkill -u $UID_B -f 03-scena 2>/dev/null && echo "    OK  ripulito" || true
rm -f /dev/shm/$SHM 2>/dev/null || true
FINE
	;;
*) echo "uso: $0 <avvia|conta|ferma>"; exit 2 ;;
esac
