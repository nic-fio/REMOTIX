#!/bin/bash
# 16-coda.sh — la CODA delle salite della fase 16: gira da sola, sul server, fino in fondo.
#
#   (sul server, come nicfio)
#   sudo systemd-run --unit=r16-coda --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \
#        bash /media/REMOTIX/src/controllo/banchi/16-stress/16-coda.sh intel gnome kde xfce lxqt
#
# ⭐ Perche' una coda e non una sessione di Claude che lancia le salite: la campagna dura
#    la notte (fasi/16 §6, decisione dell'utente del 25 set: «senza un mio intervento»), e
#    non deve dipendere da chi la sorveglia.  Se chi sorveglia si ferma, il server continua.
#
# Per ogni desktop, la scala delle misure (§8): 4K; se la salita trova una rottura
# (codice 1), la misura dopo riparte da 1 utente; se arriva a 16 (codice 0), desktop
# successivo.  Codice 3 (BLOCKED o fermata da fuori): si riprova UNA volta dopo 2 minuti
# con un nome nuovo (§14: le evidenze della prima restano), poi si passa oltre, dichiarato.
#
# ⛔ Per fermarla fra una salita e l'altra: `touch /media/REMOTIX/misure/fase16/FERMA`.
#    Per fermarla subito: `sudo systemctl stop r16-coda` (la salita in corso riceve
#    SIGTERM, chiude il livello come INTERROTTO e sgombera).
#
# Variabili: REMOTIX_16_VIDEO (il file del profilo D), REMOTIX_16_FPS (la sua f),
#            REMOTIX_16_MISURE (la scala, predefinita «4k 3k 2k fhd»),
#            REMOTIX_16_IN_PIU (opzioni in piu' per 16-salita.py, es. «--scheda amd»).
set -u
SCHEDA=${1:?uso: 16-coda.sh intel|amd desktop...}
shift
DESKTOP=${*:-gnome kde xfce lxqt}
QUI=$(cd "$(dirname "$0")" && pwd)
MISURE_DIR=/media/REMOTIX/misure/fase16
VIDEO=${REMOTIX_16_VIDEO:-$MISURE_DIR/video/bbb_sunflower_2160p_30fps_normal.mp4}
FPS=${REMOTIX_16_FPS:-30}
SCALA=${REMOTIX_16_MISURE:-4k 3k 2k fhd}
LOG=$MISURE_DIR/coda-$SCHEDA.log
STATO=$MISURE_DIR/coda-$SCHEDA.jsonl
mkdir -p "$MISURE_DIR"

dice() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
segna() {  # desktop misura campagna codice
	printf '{"t":"%s","scheda":"%s","desktop":"%s","misura":"%s","campagna":"%s","codice":%s}\n' \
		"$(date -Is)" "$SCHEDA" "$1" "$2" "$3" "$4" >>"$STATO"
}

dice "▶ coda $SCHEDA: desktop «$DESKTOP» · scala «$SCALA» · video $VIDEO (f=$FPS)"
[ -f "$VIDEO" ] || { dice "⛔ il video non c'e': $VIDEO"; exit 2; }

for d in $DESKTOP; do
	for m in $SCALA; do
		if [ -e "$MISURE_DIR/FERMA" ]; then dice "⏹ FERMA trovato: mi fermo"; exit 0; fi
		esito=""
		for tentativo in 1 2; do
			camp="$SCHEDA-$m-$d"
			[ "$tentativo" = 2 ] && camp="$camp-r2"
			[ -e "$MISURE_DIR/$camp/salita.jsonl" ] && camp="$camp-$(date +%H%M)"
			dice "── salita $camp (tentativo $tentativo)"
			# shellcheck disable=SC2086
			python3 "$QUI/16-salita.py" --scatola "$d" --campagna "$camp" --misura "$m" \
				--video "$VIDEO" --fps-video "$FPS" ${REMOTIX_16_IN_PIU:-} \
				>>"$MISURE_DIR/coda-$SCHEDA-salite.log" 2>&1
			c=$?
			segna "$d" "$m" "$camp" "$c"
			dice "   $camp: codice $c ($(python3 -c "import json,sys; s=json.load(open(sys.argv[1])); print('buono', s.get('ultimo_buono'), '· rottura', s.get('rottura'), '·', s.get('fase'))" "$MISURE_DIR/$camp/stato.json" 2>/dev/null || echo 'stato illeggibile'))"
			if [ "$c" = 3 ] && [ "$tentativo" = 1 ]; then
				dice "   ⚠ BLOCKED o interrotta: riprovo fra 2 minuti"
				sleep 120
				continue
			fi
			esito=$c
			break
		done
		case "$esito" in
		0) dice "✅ $d regge 16 utenti a $m"; break ;;
		1) dice "↘ $d cede a $m: scendo di misura" ;;
		*) dice "⛔ $d a $m: due volte BLOCKED — passo al desktop dopo"; break ;;
		esac
	done
done
dice "⏹ coda $SCHEDA finita"
