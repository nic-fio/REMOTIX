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
case "${LARGHEZZA}x${ALTEZZA}" in
3840x2160) ATTESO="~40" ;;   # LEZIONI.md §3 domanda 6: «61 (40 a 4K, per il costo della copia)»
*)         ATTESO="~61" ;;
esac

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
echo "   atteso da LEZIONI.md §3 domanda 6: $ATTESO fps"
if [ "$COMPOSITORE" = labwc ]; then
	echo "   ⚠ e per labwc quell'atteso viene da una misura a 720p: non e' un atteso a 1080p"
fi

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

# ---------------------------------------------------------------------------
# ⭐ IL RIPIEGO E' FINITO: `misura-wlroots` ADESSO SA DIRE DI NO DA SE'.
#
# ⛔ COM'ERA, dal 9 agosto al 12 agosto 2026.  La revisione avversariale trovo'
#    leggendo il sorgente che `misura-wlroots` **ritornava 0 in ogni percorso
#    che arrivasse alla stampa**: compositore che rifiuta la copia, compositore
#    che muore a meta', pentola non allocata — si usciva dal ciclo, si stampava
#    una RIGA coi numeri parziali e si tornava **0**.  ⇒ Il verdetto lo
#    costruiva questo script, cioe' la protezione di un difetto noto stava
#    **fuori dal programma**: l'invariante **I7** al contrario, e chi avesse
#    lanciato quel binario da un'altra riga di comando non l'avrebbe avuta.
#
# ⭐ CURATO il 12 agosto 2026 (lacuna L1), nella stessa forma del gemello
#    `misura-cattura.c`: al posto della RIGA esce `GUASTO<TAB>etichetta<TAB>la
#    ragione`, e lo stato d'uscita e' **2**.  I due ingressi costruiti, `[M]`
#    su NIC-OS con labwc headless:
#
#      `--durata 0 --scarto 0`        prima: `RIGA … 0x0 … 0.00` uscita **0**
#                                     dopo:  `GUASTO … nessun formato mai
#                                            negoziato` uscita **2**
#      labwc ucciso al 3° secondo     prima: `RIGA … 1280x720 … 0.00` uscita
#      di una cella da 20 s                  **0** (185 fotogrammi arrivati e
#                                            buttati, sotto l'etichetta di una
#                                            cella intera)
#                                     dopo:  `GUASTO … la connessione al
#                                            compositore e' caduta durante la
#                                            misura` uscita **2**
#
# ⚠ E LE TRE DOMANDE QUI SOTTO RESTANO, ma cambiano di natura: non sono piu' il
#   ripiego che supplisce a uno stato d'uscita che non c'era — sono le domande
#   sulla SCENA, che lo strumento non puo' fare perche' non la conosce.  «Zero
#   fotogrammi» su una scena dichiarata in movimento e' un rosso di questo
#   banco; per `misura-wlroots`, da solo, resta uno zero legittimo.
# ---------------------------------------------------------------------------
USCITA_FILE=$(mktemp)
WAYLAND_DISPLAY=$SOCKET "$QUI/misura-wlroots" --durata "$DURATA" --scarto 5 \
    --etichetta "c1-$COMPOSITORE$ETICHETTA_MISURA" | tee "$USCITA_FILE"
USCITA=$?

# ⛔ E LO STATO D'USCITA DELLO STRUMENTO SI LEGGE PER PRIMO, adesso che c'e':
#    se lui si e' gia' dichiarato guasto, il verdetto e' suo e questo banco non
#    ci mette sopra una diagnosi propria.  Leggerlo dopo le tre domande
#    sarebbe rimettere il ripiego davanti alla cura.
GUASTO_DETTO=$(awk -F'\t' '/^GUASTO/{print $3}' "$USCITA_FILE" | head -1)
FPS=$(awk -F'\t' '/^RIGA/{print $8}' "$USCITA_FILE" | head -1)
rm -f "$USCITA_FILE"

if [ "$USCITA" -ne 0 ] || [ -n "$GUASTO_DETTO" ]; then
	echo "⛔ FALLITO: lo strumento si e' dichiarato guasto (uscita $USCITA)."
	echo "   ragione: ${GUASTO_DETTO:-non l'ha scritta, e questo e' un difetto suo}"
	echo "   ⚠ e NON e' «il compositore non consegna»: non c'e' stata una misura."
	USCITA=2
# Tre domande sulla SCENA, che lo strumento non puo' fare perche' non la conosce.
elif [ -z "$FPS" ]; then
	echo "⛔ FALLITO: nessuna RIGA di misura."
	USCITA=2
elif awk -v f="${FPS:-0}" 'BEGIN{exit !(f+0 <= 0)}'; then
	echo "⛔ FALLITO: $FPS fotogrammi al secondo."
	echo "   Non e' «il compositore non consegna»: e' che non c'e' stata una misura."
	USCITA=2
elif ! pgrep -x "$COMPOSITORE" >/dev/null; then
	echo "⛔ FALLITO: $COMPOSITORE non e' piu' vivo alla fine della misura."
	echo "   Il numero qui sopra copre solo il tratto prima che cadesse."
	USCITA=2
fi

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
