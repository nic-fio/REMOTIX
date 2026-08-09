#!/bin/bash
#
# banco.sh — quanto eroga il compositore, per risoluzione e per strada dei pixel.
#
# Risponde al compito posto dall'utente il 7 agosto 2026, e ne rispetta i cinque
# punti: si misura sul banco, la scena e' dichiarata e si muove sempre, si misura
# la SOLA cattura (niente RDP, niente codificatore), memoria contro DMA-BUF, e
# ogni cella dice anche quanti buffer distinti sono arrivati e quanto danno
# portavano — che e' l'unico modo di distinguere «il compositore non da'» da
# «noi tratteniamo».
#
#   bash banco.sh prepara          genera le scene video (una volta sola)
#   bash banco.sh cella <scena> <W> <H> <fps> <strada> <colore> <durata> <etichetta>
#   bash banco.sh mutter           l'intera tabella di Mutter
#
# Scene, tutte e tre dichiarate:
#   fermo   nessuna: e' il controllo, e deve dare zero
#   tetto   weston-simple-egl a schermo intero, opaco, sincronizzato al ridisegno
#           del compositore: UN commit per ogni repaint, e un costo di GPU
#           trascurabile.  E' il tetto vero — quel che il compositore riesce a
#           produrre quando qualcuno cambia lo schermo a ogni giro
#   video   un filmato 60 fps a schermo intero: il caso d'uso vero
#   carico  glmark2 a schermo intero, che rende a migliaia di fotogrammi al
#           secondo e satura la GPU.  NON e' il tetto: e' quanto resta al
#           compositore quando la sessione lavora davvero
#
set -uo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori
SCENE=$QUI/scene
MISURA=$QUI/misura-cattura

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
export XDG_CURRENT_DESKTOP=GNOME
export XDG_SESSION_TYPE=wayland
export LANG=C.UTF-8

MISURE=(1920x1080 2560x1440 3840x2160)

prepara()
{
	mkdir -p "$SCENE"
	for m in "${MISURE[@]}"; do
		[ -s "$SCENE/$m.mp4" ] && continue
		echo "genero la scena video $m…"
		ffmpeg -nostdin -loglevel error -y \
		       -f lavfi -i "testsrc2=size=$m:rate=60,format=yuv420p" \
		       -t 20 -c:v libx264 -preset ultrafast -tune zerolatency -g 60 \
		       "$SCENE/$m.mp4" || return 1
	done
	ls -la "$SCENE"
}

avvia_scena()
{
	local scena=$1 w=$2 h=$3

	case $scena in
	fermo) echo 0 ;;
	tetto)
		# ⛔ `stdbuf -oL`, e non e' un vezzo: senza, l'uscita del client verso un
		#    FILE e' bufferizzata a blocchi, e alla chiusura della scena i suoi
		#    fotogrammi al secondo si perdono nel buffer.  Il registro resta
		#    vuoto, e il controllo di `LEZIONI.md` §1.1 — «quanto disegna il
		#    client», l'unico che dice se il tetto e' del compositore o della
		#    scena — sembra dire «zero» quando in realta' non e' stato sentito.
		#    Trovato il 9 agosto 2026 alla fase 0, confrontando con
		#    `banco-altri.sh`, che lo `stdbuf` ce l'aveva gia'.
		stdbuf -oL weston-simple-egl -f -o >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	carico)
		glmark2-wayland --fullscreen --run-forever -b build \
		    >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	video)
		mpv --fs --loop=inf --no-audio --no-osc --no-input-default-bindings \
		    --really-quiet --profile=low-latency \
		    "$SCENE/${w}x${h}.mp4" >"$QUI/scena.log" 2>&1 &
		echo $!
		;;
	esac
}

cella()
{
	local scena=$1 w=$2 h=$3 fps=$4 strada=$5 colore=$6 durata=$7 etichetta=$8
	local opzioni=(--mutter --larghezza "$w" --altezza "$h" --fps "$fps"
	               --durata "$durata" --scarto 7 --etichetta "$etichetta")
	local pid_scena pid_misura stato_scena

	[ "$strada" = dmabuf ] && opzioni+=(--dmabuf)
	[ "$colore" = bgra ] && opzioni+=(--bgra)

	"$MISURA" "${opzioni[@]}" >"$QUI/uscita.txt" 2>"$QUI/misura.log" &
	pid_misura=$!

	# La scena si accende DOPO il monitor virtuale: senza uno schermo non c'e'
	# dove aprirsi.  I sette secondi di scarto del misuratore coprono l'avvio.
	sleep 2.5
	: >"$QUI/scena.log"
	pid_scena=$(avvia_scena "$scena" "$w" "$h")

	# ⛔ E SI VERIFICA CHE LA SCENA SIA VIVA, PRIMA DI CREDERE AL NUMERO.
	#
	#    Il 9 agosto 2026, al primo riavvio vero del server, questa cella ha
	#    stampato tre righe di misura con `fps=0.00` — che con la cattura attiva
	#    e' uno ZERO LEGITTIMO, cioe' «il compositore non ha niente da
	#    consegnare».  Era vero, e la ragione non era il compositore: mancava il
	#    pacchetto `weston`, e `weston-simple-egl` non esisteva affatto.  Il
	#    registro lo diceva («failed to run command»), ma la RIGA usciva lo
	#    stesso, e in una tabella avrebbe avuto l'aspetto di un compositore muto.
	#
	# ⚠ E' la terza faccia dello stesso difetto: `misura-cattura` ora distingue
	#   «flusso mai attivo» da «zero», ma «flusso attivo e SCENA MORTA» produce
	#   ancora uno zero che sembra una misura.  La scena e' parte dello strumento
	#   e va certificata come il resto (`LEZIONI.md` §1.2, §1.9).
	#
	# ⛔ E NON SI USA `kill -0`: un figlio morto subito resta ZOMBIE finche'
	#    nessuno lo raccoglie, e `kill -0` su uno zombie RIESCE — «il pid esiste»
	#    non e' «il processo e' vivo».  Provato il 9 agosto 2026: la guardia
	#    scritta con `kill -0` non e' scattata su una scena che non era mai
	#    partita.  Si guarda lo STATO in `ps`, che dice `Z` per gli zombie.
	sleep 1
	stato_scena=$(ps -o stat= -p "${pid_scena:-0}" 2>/dev/null | tr -d ' ')
	if [ "${pid_scena:-0}" != 0 ] && { [ -z "$stato_scena" ] || [ "${stato_scena#Z}" != "$stato_scena" ]; }; then
		kill $pid_misura 2>/dev/null
		wait $pid_misura 2>/dev/null
		echo "GUASTO	$etichetta	scena '$scena' morta subito dopo l'avvio"
		{
			echo "⛔ FALLITO (non «zero»): la scena non e' partita."
			echo "   Non c'e' nessun numero da leggere: non c'era niente da catturare."
			echo "   Il registro della scena dice:"
			sed 's/^/     /' "$QUI/scena.log"
		} >&2
		return 2
	fi

	wait $pid_misura
	[ "${pid_scena:-0}" != 0 ] && kill "$pid_scena" 2>/dev/null
	sleep 1.5

	cat "$QUI/misura.log" >&2
	grep '^RIGA' "$QUI/uscita.txt"
}

tabella_mutter()
{
	local d=${1:-20}

	echo "# etichetta misura colore fps_dichiarato strada tipo fps_misurati fotogrammi secondi buffer danno_pieno danno_parziale danno_assente salti fence_non_pronta min p50 p95 max"

	cella fermo 1920 1080 60 memoria bgrx 8 "controllo-desktop-fermo"

	for m in "${MISURE[@]}"; do
		w=${m%x*}; h=${m#*x}
		for strada in memoria dmabuf; do
			cella tetto "$w" "$h" 60 "$strada" bgrx "$d" "tetto-$m-$strada-60"
		done
	done

	# L'asse che risponde alla domanda vera: il tetto e' del compositore o e'
	# quello che gli abbiamo dichiarato noi?  REMOTIX dichiara 30.
	for f in 30 60 120; do
		cella tetto 1920 1080 "$f" dmabuf bgrx "$d" "dichiarato-1920x1080-dmabuf-$f"
	done
	for f in 30 60 120; do
		cella tetto 3840 2160 "$f" dmabuf bgrx "$d" "dichiarato-3840x2160-dmabuf-$f"
	done

	# La profondita' di colore: BGRx sono 24 bit di colore dentro 32, BGRA e' lo
	# stesso con l'alfa.  Sono le uniche due che la cattura offre.
	cella tetto 1920 1080 60 memoria bgra "$d" "colore-1920x1080-memoria-bgra"
	cella tetto 1920 1080 60 dmabuf bgra "$d" "colore-1920x1080-dmabuf-bgra"

	for m in "${MISURE[@]}"; do
		w=${m%x*}; h=${m#*x}
		for strada in memoria dmabuf; do
			cella video "$w" "$h" 60 "$strada" bgrx "$d" "video-$m-$strada-60"
		done
	done

	# Quanto resta al compositore quando la sessione lavora davvero.
	cella carico 1920 1080 60 dmabuf bgrx "$d" "carico-1920x1080-dmabuf-60"
	cella carico 3840 2160 60 dmabuf bgrx "$d" "carico-3840x2160-dmabuf-60"
}

case "${1:-}" in
prepara) prepara ;;
cella) shift; cella "$@" ;;
mutter) shift; tabella_mutter "$@" ;;
*) echo "uso: $0 {prepara|cella …|mutter [durata]}" >&2; exit 2 ;;
esac
