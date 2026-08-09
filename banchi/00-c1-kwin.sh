#!/bin/bash
#
# 00-c1-kwin.sh — la certificazione C1 del banco della fase 0.
#
#   bash 00-c1-kwin.sh [larghezza] [altezza] [durata] [memoria|dmabuf]
#
# ⛔ E LA STRADA DEI PIXEL VA DETTA, perche' sono due numeri diversi e il primo
#    giro del 9 agosto 2026 ha confrontato la colonna sbagliata: `kde.md` §5.7
#    misura 1080p a **59,2 a copia zero** e **43,3 in memoria**.  Misurato in
#    memoria e confrontato col 59, il banco sembrava sbagliare di dieci
#    fotogrammi mentre stava rispondendo giusto a un'altra domanda.
#
# ---------------------------------------------------------------------------
# CHE COSA PROVA, E PERCHE' NON BASTAVA IL NUMERO DI MUTTER
#
# Alla fase 0 il banco ha riprodotto i ~37 fotogrammi di Mutter.  Ma «lo
# strumento ripete il numero che ci aspettiamo» e «lo strumento misura» sono la
# stessa cosa fino a che non lo si punta su qualcosa di DIVERSO con una risposta
# nota: KWin, dove v1 ha misurato 59-60 l'8 agosto 2026.
#
# ⛔ Se qui uscissero ancora ~37, il banco starebbe misurando se stesso.
#    E' `LEZIONI.md` §1.2 — il banco si certifica prima della misura — nella sua
#    forma piu' severa: non «sa dare un numero», ma «sa dare un numero DIVERSO
#    quando la cosa misurata e' diversa».
#
# ⭐ E porta il controllo che alla cella di Mutter mancava: QUANTO DISEGNA IL
#    CLIENT.  Senza, un tetto della scena si attribuisce al compositore e
#    viceversa (`LEZIONI.md` §1.1).  `weston-simple-egl` stampa da se' i propri
#    fotogrammi al secondo: si legge da li'.
#
# ⚠ E si ricorda che KWin col backend virtuale disegna IN SOFTWARE (`kde.md`):
#   il suo 59-60 e il 37 di Mutter non dicono «KWin e' piu' veloce», dicono che
#   i due consegnano in modo diverso.  Il paragone che conta e' con se stessi.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori
LARGHEZZA=${1:-1920}
ALTEZZA=${2:-1080}
DURATA=${3:-20}
STRADA_NOME=${4:-memoria}
SOCKET=wayland-kwin

case "$STRADA_NOME" in
memoria) STRADA= ;;
dmabuf)  STRADA=--dmabuf ;;
*) echo "strada sconosciuta: $STRADA_NOME (memoria | dmabuf)" >&2; exit 2 ;;
esac

# L'atteso, da `kde.md` §5.7 [M] 8 agosto 2026 — scritto qui perche' il banco
# dica da se' se ha risposto o no, invece di lasciarlo giudicare a memoria.
case "${LARGHEZZA}x${ALTEZZA}-$STRADA_NOME" in
1280x720-dmabuf)   ATTESO="59,4" ;;
1920x1080-dmabuf)  ATTESO="59,2" ;;
2560x1440-dmabuf)  ATTESO="59,3" ;;
3840x2160-dmabuf)  ATTESO="59,0" ;;
1280x720-memoria)  ATTESO="49,6" ;;
1920x1080-memoria) ATTESO="43,3" ;;
2560x1440-memoria) ATTESO="37,0" ;;
3840x2160-memoria) ATTESO="27,0" ;;
*) ATTESO="(non in tabella)" ;;
esac

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

pulisci()
{
	# ⛔ MAI `kill ${PID:-0}`: `kill 0` non e' «non uccidere niente», e'
	#    «uccidi TUTTO IL MIO GRUPPO DI PROCESSI» — cioe' anche la shell che sta
	#    eseguendo questo banco.  Costato il 9 agosto 2026: il banco terminava
	#    senza stampare una sola riga, e da fuori aveva l'aspetto di un comando
	#    che non parte.  Si uccide solo quel che esiste davvero.
	for p in ${PID_SCENA:-} ${PID_NODO:-}; do
		[ -n "$p" ] && [ "$p" -gt 0 ] 2>/dev/null && kill "$p" 2>/dev/null
	done
	pkill -x kwin_wayland 2>/dev/null
	# ⛔ Si aspetta che sia morto davvero: fra «ho ucciso» e «e' sparito» c'e'
	#    un intervallo, e il giro dopo ci cascherebbe dentro (LEZIONI.md §2.3-ter).
	for _ in $(seq 1 40); do
		pgrep -x kwin_wayland >/dev/null || break
		sleep 0.25
	done
	rm -f "$XDG_RUNTIME_DIR/$SOCKET" "$XDG_RUNTIME_DIR/$SOCKET.lock" 2>/dev/null
}
trap pulisci EXIT

# ⛔ Non si aspetta un tempo: si aspetta un EVENTO, con un tetto dichiarato.
attendi_file()
{
	local file=$1 scadenza=$((SECONDS + ${2:-30}))

	while [ $SECONDS -lt $scadenza ]; do
		[ -e "$file" ] && return 0
		sleep 0.25
	done
	return 1
}

pulisci
echo "== C1: KWin --virtual ${LARGHEZZA}x${ALTEZZA}, $STRADA_NOME, stessa scena di Mutter =="
echo "   atteso da kde.md §5.7: $ATTESO fps"

# `KWIN_WAYLAND_NO_PERMISSION_CHECKS` scavalca il cancello del file .desktop:
# qui si misura la cattura, non il permesso (quello e' `kde.md` §3.3-bis).
nohup setsid env KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
    kwin_wayland --virtual --width "$LARGHEZZA" --height "$ALTEZZA" \
                 --no-lockscreen --socket="$SOCKET" \
    >"$QUI/c1-kwin.log" 2>&1 </dev/null &

if ! attendi_file "$XDG_RUNTIME_DIR/$SOCKET" 30; then
	echo "⛔ FALLITO: KWin non ha aperto il socket $SOCKET entro 30 s"
	tail -n 15 "$QUI/c1-kwin.log" | sed 's/^/    /'
	exit 1
fi
echo "  KWin in piedi, socket $SOCKET"

# Il nodo PipeWire si CHIEDE al compositore col suo protocollo, non si indovina.
: >"$QUI/c1-nodo.txt"
WAYLAND_DISPLAY=$SOCKET "$QUI/nodo-kwin" >"$QUI/c1-nodo.txt" 2>"$QUI/c1-nodo.log" &
PID_NODO=$!

NODO=
for _ in $(seq 1 40); do
	NODO=$(tr -dc '0-9' <"$QUI/c1-nodo.txt")
	[ -n "$NODO" ] && break
	sleep 0.25
done
if [ -z "$NODO" ]; then
	echo "⛔ FALLITO: nessun nodo dal protocollo di KWin."
	echo "   ⚠ e NON e' «KWin non consegna»: e' «non abbiamo un nodo su cui guardare»."
	tail -n 10 "$QUI/c1-nodo.log" | sed 's/^/    /'
	exit 1
fi
echo "  nodo PipeWire $NODO"

# La scena, identica a quella di Mutter.
WAYLAND_DISPLAY=$SOCKET stdbuf -oL weston-simple-egl -f -o >"$QUI/c1-scena.log" 2>&1 &
PID_SCENA=$!
sleep 2

"$QUI/misura-cattura" --nodo "$NODO" --larghezza "$LARGHEZZA" --altezza "$ALTEZZA" \
    --fps 60 --durata "$DURATA" --scarto 5 $STRADA --etichetta "c1-kwin-${LARGHEZZA}x${ALTEZZA}-${4:-memoria}"
USCITA=$?

echo
echo "  ⭐ quanto ha disegnato il CLIENT (il controllo di LEZIONI.md §1.1):"
if [ -s "$QUI/c1-scena.log" ]; then
	grep -o '[0-9.]* fps' "$QUI/c1-scena.log" | tail -3 | sed 's/^/     /'
else
	echo "     ⚠ IGNOTO: la scena non ha stampato niente ($QUI/c1-scena.log vuoto)."
	echo "       Non e' «ha disegnato zero»: e' «non lo abbiamo sentito»."
fi

echo
echo "USCITA_MISURA=$USCITA"
exit $USCITA
