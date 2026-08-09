#!/bin/bash
#
# 00-c1-wlroots.sh — la terza gamba della certificazione della fase 0.
#
#   bash 00-c1-wlroots.sh [sway|labwc] [larghezza] [altezza] [durata]
#
# ---------------------------------------------------------------------------
# PERCHE' SERVE, VISTO CHE MUTTER E KWIN SONO GIA' STATI MISURATI
#
# I banchi dei compositori sono TRE programmi, non uno:
#
#   misura-cattura   PipeWire — Mutter e KWin        ✅ certificato (C1: 58,92 su KWin)
#   nodo-kwin        il protocollo di KDE            ✅ usato dentro C1
#   misura-wlroots   wlr-screencopy — sway, labwc    ⛔ MAI PUNTATO SU NIENTE
#
# Il terzo e' stato ricompilato il 9 agosto 2026 e non ha mai misurato nulla:
# uno strumento che non ha mai trovato niente non e' uno strumento pulito, e'
# uno strumento non certificato (`LEZIONI.md` §1.9).  E serve alla fase 11.
#
# ⚠ E qui il modello e' DIVERSO, il che rende la certificazione piu' utile e non
#   meno: Mutter e KWin **spingono** i fotogrammi (PipeWire), wlroots li fa
#   **tirare** — una richiesta per fotogramma su `wlr-screencopy`.  Un numero
#   simile fra i due modelli non e' scontato: e' un'informazione.
#
# **L'atteso**: 61 fps a 1080p `[M]` v1 (`LEZIONI.md` §3, domanda 6).
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori
COMPOSITORE=${1:-labwc}
LARGHEZZA=${2:-1920}
ALTEZZA=${3:-1080}
DURATA=${4:-20}
ATTESO=61

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

pulisci()
{
	# ⛔ Mai `kill ${PID:-0}`: `kill 0` uccide il proprio gruppo di processi,
	#    shell del banco compresa (costato oggi, in `00-c1-kwin.sh`).
	for p in ${PID_SCENA:-}; do
		[ -n "$p" ] && [ "$p" -gt 0 ] 2>/dev/null && kill "$p" 2>/dev/null
	done
	pkill -x "$COMPOSITORE" 2>/dev/null
	for _ in $(seq 1 40); do
		pgrep -x "$COMPOSITORE" >/dev/null || break
		sleep 0.25
	done
}
trap pulisci EXIT

pulisci
case "$COMPOSITORE" in
sway)  ETICHETTA_MISURA="-${LARGHEZZA}x${ALTEZZA}"
       echo "== C1-wlroots: sway headless ${LARGHEZZA}x${ALTEZZA} ==" ;;
labwc) ETICHETTA_MISURA=""
       echo "== C1-wlroots: labwc headless, misura DECISA DA WLROOTS =="
       echo "   ⚠ labwc non accetta una misura: il backend headless nasce a 1280x720."
       echo "     La misura vera la stampa lo strumento, e non la dichiaro io." ;;
esac
echo "   atteso da LEZIONI.md §3 domanda 6: ~$ATTESO fps"

# I socket che ci sono GIA', per non confondere il nostro con quello di un'altra
# sessione: `wayland-0` e' di GNOME, `wayland-kwin` e' del banco di KWin.
PRIMA=$(ls "$XDG_RUNTIME_DIR"/wayland-* 2>/dev/null | grep -v '\.lock$' | sort)

# ⛔ E LA MISURA LA ONORA SOLO SWAY.
#
#    `labwc` non prende larghezza e altezza sulla riga di comando: il backend
#    headless di wlroots nasce a **1280x720** e li' resta.  Al primo giro del
#    9 agosto 2026 questo banco ha etichettato «1920x1080» una misura fatta a
#    720p — e il numero (61,16) era giusto per 720p, quindi niente sarebbe
#    sembrato storto.  Due misure diverse sotto la stessa etichetta, che e' la
#    forma d'errore **E2**: l'ha smascherata solo il fatto che `misura-wlroots`
#    stampa la misura VERA accanto al numero.
#
# ⚠ Da cui: con `labwc` l'etichetta non dichiara una misura che non abbiamo
#   chiesto, e chi vuole 1080p su wlroots usa `sway`.
case "$COMPOSITORE" in
sway)
	printf 'output HEADLESS-1 mode %sx%s\n' "$LARGHEZZA" "$ALTEZZA" >"$QUI/sway.conf"
	nohup setsid env WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 XDG_CURRENT_DESKTOP=sway \
	    sway -c "$QUI/sway.conf" >"$QUI/c1-wlr.log" 2>&1 </dev/null &
	;;
labwc)
	nohup setsid env WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 \
	    labwc >"$QUI/c1-wlr.log" 2>&1 </dev/null &
	;;
*) echo "compositore sconosciuto: $COMPOSITORE (sway | labwc)" >&2; exit 2 ;;
esac

# ⛔ Si aspetta un EVENTO — il socket NUOVO — non un tempo.  E si aspetta quello
#    nuovo, non «un socket qualunque»: con GNOME acceso ce ne sono gia' due, e
#    misurare il socket sbagliato darebbe un numero perfettamente plausibile di
#    un compositore diverso.
SOCKET=
for _ in $(seq 1 60); do
	DOPO=$(ls "$XDG_RUNTIME_DIR"/wayland-* 2>/dev/null | grep -v '\.lock$' | sort)
	NUOVO=$(comm -13 <(printf '%s\n' "$PRIMA") <(printf '%s\n' "$DOPO") | head -1)
	if [ -n "$NUOVO" ]; then SOCKET=$(basename "$NUOVO"); break; fi
	sleep 0.25
done
if [ -z "$SOCKET" ]; then
	echo "⛔ FALLITO: $COMPOSITORE non ha aperto un socket nuovo entro 15 s"
	echo "   ⚠ e NON e' «non consegna»: non e' proprio partito."
	tail -n 15 "$QUI/c1-wlr.log" | sed 's/^/    /'
	exit 1
fi
echo "  $COMPOSITORE in piedi, socket nuovo: $SOCKET"

WAYLAND_DISPLAY=$SOCKET stdbuf -oL weston-simple-egl -f -o >"$QUI/c1-wlr-scena.log" 2>&1 &
PID_SCENA=$!

# ⛔ E si verifica che la scena sia VIVA — non con `kill -0`, che riesce sugli
#    zombie, ma con lo stato in `ps` (costato oggi, in `banco.sh`).
sleep 2
STATO=$(ps -o stat= -p "$PID_SCENA" 2>/dev/null | tr -d ' ')
if [ -z "$STATO" ] || [ "${STATO#Z}" != "$STATO" ]; then
	echo "⛔ FALLITO: la scena non e' partita. Il suo registro dice:"
	sed 's/^/    /' "$QUI/c1-wlr-scena.log"
	exit 1
fi

WAYLAND_DISPLAY=$SOCKET "$QUI/misura-wlroots" --durata "$DURATA" --scarto 5 \
    --etichetta "c1-$COMPOSITORE$ETICHETTA_MISURA"
USCITA=$?

echo
echo "  ⭐ quanto ha disegnato il CLIENT (il controllo di LEZIONI.md §1.1):"
if [ -s "$QUI/c1-wlr-scena.log" ]; then
	grep -o '[0-9.]* fps' "$QUI/c1-wlr-scena.log" | tail -3 | sed 's/^/     /'
else
	echo "     ⚠ IGNOTO: la scena non ha stampato niente."
fi

echo
echo "USCITA_MISURA=$USCITA"
exit $USCITA
