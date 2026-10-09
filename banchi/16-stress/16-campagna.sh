#!/bin/bash
# 16-campagna.sh — le DUE campagne della fase 16 in fila, da sole, sul server (§11).
#
#   (sul server, come nicfio)
#   sudo systemd-run --unit=r16-coda --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \
#        -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue \
#        bash /media/REMOTIX/src/controllo/banchi/16-stress/16-campagna.sh intel-b amd
#
# Ogni argomento e' un'etichetta di campagna: il nome delle salite e dei registri
# (`<etichetta>-<misura>-<desktop>`, `coda-<etichetta>.log`).  Un'etichetta che comincia
# con «amd» accende la Radeon (`--scheda amd`), le altre restano sulla Intel.
# ⭐ «intel-b»: la campagna Intel RIFATTA col prodotto del 26 set (binario 45d048c8,
#   pagina fb9a18f3 — WebGL, DECISIONI §9.4); quella della notte («intel») resta nel
#   registro come il «prima».
# Il SIGTERM (systemctl stop) si passa alla coda in corso, che lo passa alla salita.
# ⭐ fasi/20 §7.0: REMOTIX_16_SISTEMA=xrdp ⇒ ogni salita con `--sistema xrdp` (il confronto
#   con xrdp: campagne intel-x20 amd-x20, unita' r20-xrdp, con -p OOMScoreAdjust=-900);
#   la coda riceve quanti desktop restano dopo di lei, per il preventivo delle ore.
set -u
QUI=$(cd "$(dirname "$0")" && pwd)
M=/media/REMOTIX/misure/fase16
figlio=""; ferma=0
trap 'ferma=1; [ -n "$figlio" ] && kill -TERM "$figlio"' TERM INT
TUTTE=$#; I=0
for etichetta in "$@"; do
	I=$((I + 1))
	[ "$ferma" = 1 ] && break
	[ -e "$M/FERMA" ] && break
	extra=""
	case "$etichetta" in amd*) extra="--scheda amd" ;; esac
	[ "${REMOTIX_16_SISTEMA:-}" = xrdp ] && extra="$extra --sistema xrdp"
	echo "$(date '+%F %T') ▶ campagna $etichetta ($extra)" >> "$M/campagna.log"
	REMOTIX_16_IN_PIU="$extra" REMOTIX_16_DESKTOP_DOPO=$(( (TUTTE - I) * 4 )) \
		bash "$QUI/16-coda.sh" "$etichetta" gnome kde xfce lxqt &
	figlio=$!
	wait "$figlio"; while kill -0 "$figlio" 2>/dev/null; do wait "$figlio"; done
	figlio=""
	echo "$(date '+%F %T') ⏹ campagna $etichetta finita" >> "$M/campagna.log"
done
