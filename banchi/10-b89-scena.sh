#!/bin/sh
# 10-b89-scena.sh — le tre scene del banco del COSTO DI UNA SESSIONE.
#
# ⛔ ESISTE PERCHE' UN FILE NON HA LIVELLI DI VIRGOLETTE — la stessa ragione di
#    `09-b68-scena.sh`: `ssh -> sudo -S -> setsid ... > $LAV/log` farebbe il
#    redirect con la shell di `nicfio`, che in una cartella di root non puo'
#    scrivere, e il processo morirebbe con il registro VUOTO.
#
# ⛔⛔ E LO `shm` E' MIO, non `09-b68`.  `/dev/shm` e' UNO su tutta la macchina:
#      due agenti che usassero lo stesso nome si leggerebbero i disegni a
#      vicenda, e nessuno dei due darebbe rosso.  Qui: **`/10-b89`**.
#
#   sh 10-b89-scena.sh finestre                     apre nautilus + il terminale
#   sh 10-b89-scena.sh continuo <monitor>           scena a schermo intero, `pieno`
#   sh 10-b89-scena.sh strappi  <monitor>           scena in FINESTRA, `pieno`
#   sh 10-b89-scena.sh -- spegni                    spegne tutto quel che ho aperto
#   sh 10-b89-scena.sh -- conta                     dice che cosa e' vivo
#
# ⛔ Gira DA ROOT: `setpriv` fa scendere all'uid della sessione, che e' l'unico
#    che possa parlare col suo compositore.
set -u
UID_B=${UID_B:-1100}
UTENTE=${UTENTE:-provadec1}
SCENA=${SCENA:-/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena}
LAV=${LAV:-/media/REMOTIX/tmp/10a3}
FINESTRA=${FINESTRA:-1280x720}
LOG=$LAV/b89-scena.log

# ⛔⭐ L'AMBIENTE STA IN UN POSTO SOLO — 25 agosto 2026.
#     Era scritto a mano qui, e in altri tre posti, e ⛔ mancavano a tutt'e
#     quattro le tre variabili senza cui **Nautilus non parte affatto**.  Il
#     riquadro con i numeri sta in `10-ambiente-sessione.sh`.
# ⚠ Il file dev'essere accanto a questo sulla macchina: lo porta `prepara()` di
#   `10-b89-costo-sessione.py`, insieme a tutti gli altri copioni.
. "$(dirname "$0")/10-ambiente-sessione.sh"

giu() {
	# ⚠ `$(ambiente_di …)` NON si quota: e' una lista di parole (setpriv, env, e
	#   le variabili), non un argomento solo.  ⛔ Nessuna di quelle parole puo'
	#   contenere spazi — l'uid e' un numero e il nome utente e' un nome utente.
	# shellcheck disable=SC2046
	setsid nohup $(ambiente_di "$UID_B" "$UTENTE") "$@" >>"$LOG" 2>&1 &
}

PASSO=$1
case "$PASSO" in
finestre)
	: > "$LOG"
	chmod 666 "$LOG"
	APERTE=""
	for a in nautilus gnome-terminal; do
		if command -v "$a" >/dev/null 2>&1; then
			giu "$a"
			APERTE="$APERTE $a"
		fi
	done
	sleep 6
	# ⛔ Non si dichiara «aperte» perche' il comando e' partito: si CONTA chi
	#    e' vivo.  Un'applicazione che muore subito e una che non c'e' hanno la
	#    stessa faccia finche' non si guarda (`LEZIONI.md` §1.9).
	VIVE=$(pgrep -u "$UID_B" -c -f 'nautilu[s]|gnome-termina[l]' 2>/dev/null)
	[ -n "$VIVE" ] || VIVE=0
	echo "FINESTRE CHIESTE:$APERTE VIVE:$VIVE"
	[ "$VIVE" -gt 0 ] || { echo "⛔ nessuna finestra viva — il registro:"; tail -20 "$LOG"; exit 1; }
	exit 0 ;;

continuo|strappi)
	USCITA=$2
	pkill -u "$UID_B" -f 04-b30-scena 2>/dev/null
	sleep 0.4
	: > "$LOG"
	chmod 666 "$LOG"
	if [ "$PASSO" = continuo ]; then
		giu "$SCENA" --uscita "$USCITA" --movimento pieno \
			--shm /10-b89 --giro b89c
	else
		# ⭐ In FINESTRA: la scena non ruba lo schermo, e accanto restano le
		#    finestre vere — che e' quel che «desktop vero» vuol dire.
		giu "$SCENA" --finestra "$FINESTRA" --movimento pieno \
			--shm /10-b89 --giro b89s
	fi
	sleep 2.5
	if pgrep -u "$UID_B" -f '04-b30-scen[a]' >/dev/null; then
		echo "SCENA ACCESA $PASSO ($USCITA / $FINESTRA)"
		exit 0
	fi
	echo "SCENA NON PARTITA — il suo registro:"
	cat "$LOG"
	exit 1 ;;

--)
	case "${2:-conta}" in
	spegni)
		pkill -u "$UID_B" -f 04-b30-scena 2>/dev/null
		pkill -u "$UID_B" -f 'nautilus|gnome-terminal' 2>/dev/null
		i=0
		while [ $i -lt 20 ]; do
			pgrep -u "$UID_B" -f '04-b30-scen[a]|nautilu[s]|gnome-termina[l]' >/dev/null 2>&1 || {
				echo "SPENTO TUTTO"; exit 0; }
			i=$((i + 1))
			sleep 0.5
		done
		echo "⛔ NON MORTI: $(pgrep -au "$UID_B" -f '04-b30-scen[a]|nautilu[s]|gnome-termina[l]' | head -5)"
		exit 1 ;;
	*)
		N=$(pgrep -u "$UID_B" -c -f '04-b30-scen[a]|nautilu[s]|gnome-termina[l]' 2>/dev/null)
		[ -n "$N" ] || N=0
		echo "VIVI: $N"
		exit 0 ;;
	esac ;;
*)
	echo "passo «$PASSO» sconosciuto"; exit 2 ;;
esac
