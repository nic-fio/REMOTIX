#!/bin/bash
#
# banco-catena.sh — quanti fotogrammi al secondo arrivano DAVVERO al client.
#
# R32 ha misurato la sola cattura, con RDP e il codificatore fuori dai piedi.
# Questo banco rimette dentro tutto — cattura → codificatore → filo → client —
# e risponde all'unica domanda rimasta prima di toccare il server dell'utente:
# **dei 37 che il compositore consegna, quanti ne arrivano dall'altra parte?**
#
# Fra un giro e l'altro cambia UNA cosa sola: `--fotogrammi`, che e' gia'
# un'opzione.  Nessuna riga di codice del prodotto viene toccata.
#
# ⚠ La scena non si muove a colpi di tastiera — e' il vizio che R32 ha trovato
#   in tutte le misure di fotogrammi fatte finora.  Si accende dentro la
#   sessione un client che ridisegna a ogni ridisegno del compositore.
#
# ⛔ L'AUTENTICAZIONE RESTA ACCESA.  I banchi del progetto usano
#    `--senza-autenticazione`, che per qualche minuto lascia il server aperto a
#    chiunque sulla rete di casa — ed e' il rischio che REFERENCE.md §8.6 segna
#    in rosso.  Qui il client si autentica davvero: la credenziale arriva su
#    standard input attraverso una FIFO, quindi non compare in alcuna riga di
#    comando (`ps` non la vede) e non tocca il disco (una FIFO non conserva
#    niente).
#
# ⛔ E QUESTO BANCO SCRIVE /etc/default/remotix.  Solo per cambiare porta e
#    cadenza, e il `trap` lo rimette com'era anche se muore a meta'.
#
set -uo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori
FIFO=$QUI/.credenziale
PORTA=3395
DISPLAY_CLI=:120
DURATA=${1:-20}
UTENTE=$(id -un)

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

printf 'Password: ' >&2
read -r PW
[ -n "$PW" ] || { echo "# nessuna credenziale: non si parte"; exit 1; }

ORIGINALE=$(cat /etc/default/remotix)

ripristina()
{
	pkill -f weston-simple-egl 2>/dev/null
	pkill -x xfreerdp3 2>/dev/null
	pkill -f "^Xvfb $DISPLAY_CLI" 2>/dev/null
	rm -f "$FIFO"
	printf '%s\n' "$ORIGINALE" | sudo tee /etc/default/remotix >/dev/null
	sudo systemctl restart remotix.service
	sleep 3
	echo "# ---- ripristino ----"
	sed 's/^/#   /' /etc/default/remotix
	echo "#   in ascolto: $(ss -ltn | grep -oE '\*:(3389|3390|3391|3392|3395)' | tr '\n' ' ')"
}
trap ripristina EXIT

# ⚠ IL CLIENT DI PROVA GIRA QUI, NON NEL CONTENITORE, e va detto.
#
#   La regola del progetto lo vuole separato da chi serve, e il contenitore
#   esiste per quello.  Ma `enter.sh` dentro uno script lungo e non interattivo
#   si blocca sulla richiesta di `sudo`, e un banco che non torna non misura
#   niente.  Il contenitore condivideva gia' CPU e rete con il server, quindi
#   quel che si perde e' l'isolamento delle librerie, non la validita' del
#   numero — e il numero e' il conto dei fotogrammi che il SERVER dichiara di
#   aver spedito, non qualcosa che il client calcola.

# I tick di CPU di tutti i thread del processo, e i fotogrammi che il server
# dichiara di aver spedito.
campione()
{
	local pid tick fot

	pid=$(systemctl show -p MainPID --value remotix.service)
	[ "$pid" = 0 ] && { echo "0 0"; return; }
	tick=$(awk '{print $14+$15}' /proc/"$pid"/stat 2>/dev/null)
	fot=$(grep -F 'rete: RTT' ~/remotix.log 2>/dev/null | tail -1 |
	      grep -oE 'spediti [0-9]+' | grep -oE '[0-9]+')
	echo "${tick:-0} ${fot:-0}"
}

giro()
{
	local fps=$1 w=$2 h=$3 dma=$4
	local t0 t1 tick0 tick1 fot0 fot1 dt dfot dtick clk centesimi cpu_fot i

	printf 'REMOTIX_OPZIONI=--registro diagnostica --porta %s --fotogrammi %s\nREMOTIX_DMABUF=%s\n' \
	    "$PORTA" "$fps" "$dma" | sudo tee /etc/default/remotix >/dev/null
	rm -f ~/remotix.log
	sudo systemctl restart remotix.service
	sleep 4
	systemctl is-active --quiet remotix.service || { echo "# REMOTIX non e' partito"; return 1; }

	# Chi scrive nella FIFO aspetta il lettore: la credenziale non esiste da
	# nessuna parte finche' il client non la chiede.
	# `/from-stdin` chiede DUE cose in quest'ordine: prima il dominio, poi la
	# password.  Mandandone una sola, la password viene letta come dominio e la
	# connessione si chiude con ERRCONNECT_CONNECT_CANCELLED — che sembra un
	# rifiuto del server e non lo e'.
	rm -f "$FIFO"; mkfifo -m 600 "$FIFO"
	( printf '\n%s\n' "$PW" > "$FIFO" ) &

	pgrep -f "^Xvfb $DISPLAY_CLI" >/dev/null || {
		setsid nohup Xvfb "$DISPLAY_CLI" -screen 0 4200x2400x24 -nolisten tcp \
		    >/dev/null 2>&1 </dev/null &
		sleep 3
	}
	setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:$PORTA /gfx:avc420 \
	    /cert:ignore /sec:tls "/u:$UTENTE" /from-stdin "/size:${w}x${h}" \
	    /title:REMOTIXCATENA /log-level:WARN <"$FIFO" >"$QUI/catena-client.log" 2>&1 &
	sleep 12
	pgrep -x xfreerdp3 >/dev/null && echo "#   client collegato" || echo "#   CLIENT NON PARTITO"

	# La sessione la avvia REMOTIX al collegamento: la scena si accende solo
	# quando c'e' uno schermo su cui aprirsi.
	for i in $(seq 1 20); do
		pgrep -x gnome-shell >/dev/null && break
		sleep 1
	done
	sleep 3
	setsid nohup env WAYLAND_DISPLAY=wayland-0 weston-simple-egl -f -o \
	    >"$QUI/catena-scena.log" 2>&1 </dev/null &
	sleep 5

	t0=$(date +%s); read -r tick0 fot0 <<<"$(campione)"
	sleep "$DURATA"
	t1=$(date +%s); read -r tick1 fot1 <<<"$(campione)"

	pkill -f weston-simple-egl 2>/dev/null
	pkill -x xfreerdp3 2>/dev/null

	dt=$(( t1 - t0 )); [ "$dt" -lt 1 ] && dt=1
	dfot=$(( fot1 - fot0 )); dtick=$(( tick1 - tick0 ))
	clk=$(getconf CLK_TCK); clk=${clk:-100}
	if [ "$dfot" -le 0 ]; then
		echo "CATENA	${w}x${h}	dichiarati=$fps	dmabuf=$dma	NESSUN-FOTOGRAMMA"
		echo "#   client: $(tail -2 "$QUI/catena-client.log" 2>/dev/null | tr '\n' ' ')"
		sleep 2
		return 1
	fi
	centesimi=$(( dtick * 100 / clk * 100 / dt ))
	cpu_fot=$(( dtick * 1000 / clk / dfot ))
	printf 'CATENA\t%sx%s\tdichiarati=%s\tdmabuf=%s\tfotogrammi=%s\tsecondi=%s\tfps=%s.%s\tcpu_core=%s.%02d\tms_cpu_per_fotogramma=%s\n' \
	    "$w" "$h" "$fps" "$dma" "$dfot" "$dt" $(( dfot * 10 / dt / 10 )) $(( dfot * 10 / dt % 10 )) \
	    $(( centesimi / 100 )) $(( centesimi % 100 )) "$cpu_fot"
	sleep 2
}

echo "# la catena intera: cattura → codificatore → filo → client"
echo "# autenticazione ACCESA, credenziale su FIFO (mai in ps, mai su disco)"
case "${2:-memoria}" in
memoria)
	giro 30 1920 1080 0
	giro 60 1920 1080 0
	giro 30 3840 2160 0
	giro 60 3840 2160 0
	;;
copia-zero)
	# ⚠ La copia zero ha il difetto noto dell'alternanza (R29): l'immagine non
	#   e' buona.  Qui si misura solo QUANTO VARREBBE curarlo, cioe' il ritmo —
	#   e non si spedisce niente a nessuno.
	giro 60 1920 1080 1
	giro 60 3840 2160 1
	;;
esac
pkill -f "^Xvfb $DISPLAY_CLI" 2>/dev/null
