#!/usr/bin/env bash
# ===========================================================================
# 10-e1-lucchetto — prendi/molla il lucchetto della GPU per l'incarico 10-e1.
#
# ⛔ NON riscrive `09-lucchetto.py` (e' di tutti) ne' il corridore
#    `10-b9d-corri-al-lucchetto.sh`: li CHIAMA.  ⭐ Esiste solo perche' le
#    quattro campagne di questo incarico prendono e mollano il lucchetto
#    quattro volte, e la corsa va corsa **sulla macchina** (§7.3, prima
#    trappola: `prendi()` ritenta ogni 5 s e perde i passaggi di mano).
#
# Uso:
#     bash banchi/10-e1-lucchetto.sh prendi <secondi>
#     bash banchi/10-e1-lucchetto.sh molla
#     bash banchi/10-e1-lucchetto.sh stato
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)
MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
LAV=${LAV:-/media/REMOTIX/tmp/10e1}
CHI=${CHI:-10-e1}

case "${1:-stato}" in
prendi)
	SEC=${2:-3600}
	b64=$(base64 -w0 "$QUI/banchi/10-b9d-corri-al-lucchetto.sh")
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c '
	     mkdir -p $LAV && printf %s $b64 | base64 -d > $LAV/corri.sh
	     chmod +x $LAV/corri.sh'" >/dev/null 2>&1 || {
		echo "⛔ il corridore non e' arrivato"; exit 2; }
	# ⛔ `attesa=21600`: sei ore, com'e' scritto nell'incarico.  ⚠ Passo 0,5 s
	#    — «ritenta fitto», `[M]` 47 ms dopo il rilascio (10-b9d).
	out=$(ssh -o BatchMode=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=1000 \
	  "$MACCHINA" "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' \
	   $LAV/corri.sh '$LUCCHETTO' '$CHI' $SEC 21600 0.5" 2>&1 | grep -v '^tput')
	printf '%s\n' "$out"
	case "$out" in
	PRESO*|SCASSINO*) exit 0 ;;
	MIO*)
		# ⛔ Il lucchetto porta gia' il mio nome: `prendi()` aspetterebbe SE
		#    STESSO.  Lo si adotta solo se nessun altro corridore mio e' vivo.
		if [ "$(ssh -o BatchMode=yes "$MACCHINA" \
		        "pgrep -f '[c]orri.sh .* $CHI ' | wc -l" 2>/dev/null)" != "0" ]; then
			echo "⛔ lucchetto a nome mio E un altro corridore vivo: NON misuro"
			exit 2
		fi
		echo "⭐ adottato (nessun altro corridore mio e' vivo)"; exit 0 ;;
	*) echo "⛔ non ho il lucchetto"; exit 2 ;;
	esac ;;
molla)
	LUCCHETTO=$LUCCHETTO python3 -c "
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('luc', '$QUI/banchi/09-lucchetto.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.molla('$CHI')
" ;;
stato)
	LUCCHETTO=$LUCCHETTO python3 "$QUI/banchi/09-lucchetto.py" stato ;;
esac
