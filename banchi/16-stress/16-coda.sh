#!/bin/bash
# 16-coda.sh — la CODA delle salite della fase 16: gira da sola, sul server, fino in fondo.
#
#   (sul server, come nicfio)
#   sudo systemd-run --unit=r16-coda --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \
#        -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue \
#        bash /media/REMOTIX/src/controllo/banchi/16-stress/16-coda.sh intel gnome kde xfce lxqt
#
# ⛔ OOMPolicy=continue NON e' facoltativo: [M] 26 set 02:02, XFCE 4K a 12 utenti, la
#    macchina (che fa girare anche i browser-cliente) ha finito la RAM e il kernel ha
#    ucciso un Chrome; con la politica di serie (stop) systemd ha fermato TUTTA la coda.
#    Un processo ucciso per memoria e' un gradino rosso da misurare, non la fine della notte.
# ⛔ TimeoutStopSec=1200 e KillMode=mixed NON sono facoltativi: lo sgombero di una salita
#    (attori fino a 120 s, inquilini, compositori, il server rimesso) dura ben piu' dei 90 s
#    predefiniti, e con KillMode=control-group il SIGTERM arriverebbe INSIEME a tutti
#    (attori, browser, sudo dello sgombero).  Con «mixed» lo riceve solo questa coda, che
#    lo passa alla salita in corso e aspetta che abbia sgomberato; il SIGKILL a tutto il
#    gruppo solo dopo 1200 s.
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
#    Per fermarla subito: `sudo systemctl stop r16-coda` (la coda passa il SIGTERM alla
#    salita in corso, che chiude il livello come INTERROTTO — anche a meta' del controllo
#    corto — e sgombera; poi la coda esce senza lanciarne altre).
#
# ⭐ Nel registro, accanto al codice, l'ultimo livello GREEN VERO della salita (da
#    salita.jsonl): «buono» per la salita comprende i DEGRADED non significativi (la
#    regola di non-prosecuzione), il GREEN vero e' un'altra cosa e si scrive a parte.
#
# ⭐ fasi/20 §7.0 (9 ott 2026, l'utente: «mi aspetto che l'intera suite duri meno dei 3 giorni
#    di remotix»): dopo ogni salita la coda scrive in campagna.log il PREVENTIVO delle ore
#    rimaste — fra il caso migliore (ogni desktop che manca regge alla prima misura) e il
#    peggiore (scende per tutta la scala), con la durata media delle salite fatte;
#    REMOTIX_16_DESKTOP_DOPO dice quanti desktop restano nelle campagne dopo questa.
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
# ⭐ A5 (29 set): il file quadruplo (4 giri concatenati senza ricodifica, 42 min) — col file
#   da 10,5 min il lettore ricominciava dentro le finestre di giudizio e fermava l'immagine 1-3 s.
VIDEO=${REMOTIX_16_VIDEO:-$MISURE_DIR/video/bbb_sunflower_2160p_30fps_x4.mp4}
FPS=${REMOTIX_16_FPS:-30}
SCALA=${REMOTIX_16_MISURE:-4k 3k 2k fhd}
LOG=$MISURE_DIR/coda-$SCHEDA.log
STATO=$MISURE_DIR/coda-$SCHEDA.jsonl
mkdir -p "$MISURE_DIR"
FATTE=0; SECONDI=0
DOPO=${REMOTIX_16_DESKTOP_DOPO:-0}
# preventivo <desktop corrente> <misure rimaste per lui> <desktop rimasti dopo di lui>
preventivo() {
	python3 - "$FATTE" "$SECONDI" "$2" "$3" "$DOPO" "$(echo $SCALA | wc -w)" <<'PY' >>"$MISURE_DIR/campagna.log"
import sys, datetime
f, s, qui, resto, dopo, scala = map(int, sys.argv[1:])
m = s / f if f else 0
lo = (qui + resto + dopo) * m if qui else (resto + dopo) * m
hi = (qui + (resto + dopo) * scala) * m
print("%s   preventivo: %d salite fatte, media %.0f min · restano fra %.1f e %.1f ore (fine fra il %s e il %s)" % (
    datetime.datetime.now().strftime("%F %T"), f, m / 60, lo / 3600, hi / 3600,
    (datetime.datetime.now() + datetime.timedelta(seconds=lo)).strftime("%d/%m %H:%M"),
    (datetime.datetime.now() + datetime.timedelta(seconds=hi)).strftime("%d/%m %H:%M")))
PY
}

dice() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
segna() {  # desktop misura campagna codice ultimo_green
	printf '{"t":"%s","scheda":"%s","desktop":"%s","misura":"%s","campagna":"%s","codice":%s,"ultimo_green":%s}\n' \
		"$(date -Is)" "$SCHEDA" "$1" "$2" "$3" "$4" "${5:-null}" >>"$STATO"
}
# l'ultimo livello GREEN vero di una campagna (il piu' alto con classe GREEN in salita.jsonl)
ultimo_green() {
	python3 - "$MISURE_DIR/$1/salita.jsonl" <<'PY' 2>/dev/null || echo null
import json, sys
g = []
for r in open(sys.argv[1], encoding="utf-8", errors="replace"):
    try:
        d = json.loads(r)
    except ValueError:
        continue
    if d.get("classe") == "GREEN" and not d.get("interrotto"):
        g.append(int(d.get("livello") or 0))
print(max(g) if g else "null")
PY
}

# ⭐ il SIGTERM (systemctl stop, KillMode=mixed) arriva SOLO qui: lo si passa alla salita
#   in corso e si aspetta che sgomberi; poi nessuna salita nuova
FERMATA=0
figlio=""
ferma() {
	FERMATA=1
	dice "⚠ segnale: lo passo alla salita in corso (${figlio:-nessuna}) e aspetto che sgomberi"
	[ -n "$figlio" ] && kill -TERM "$figlio" 2>/dev/null
}
trap ferma TERM INT

dice "▶ coda $SCHEDA: desktop «$DESKTOP» · scala «$SCALA» · video $VIDEO (f=$FPS)"
[ -f "$VIDEO" ] || { dice "⛔ il video non c'e': $VIDEO"; exit 2; }

N_DESKTOP=$(echo $DESKTOP | wc -w); I_DESKTOP=0
for d in $DESKTOP; do
	I_DESKTOP=$((I_DESKTOP + 1))
	I_MISURA=0
	for m in $SCALA; do
		I_MISURA=$((I_MISURA + 1))
		if [ -e "$MISURE_DIR/FERMA" ]; then dice "⏹ FERMA trovato: mi fermo"; exit 0; fi
		esito=""
		for tentativo in 1 2; do
			camp="$SCHEDA-$m-$d"
			[ "$tentativo" = 2 ] && camp="$camp-r2"
			[ -e "$MISURE_DIR/$camp/salita.jsonl" ] && camp="$camp-$(date +%H%M)"
			dice "── salita $camp (tentativo $tentativo)"
			# shellcheck disable=SC2086
			T_SALITA=$(date +%s)
			python3 "$QUI/16-salita.py" --scatola "$d" --campagna "$camp" --misura "$m" \
				--video "$VIDEO" --fps-video "$FPS" ${REMOTIX_16_IN_PIU:-} \
				>>"$MISURE_DIR/coda-$SCHEDA-salite.log" 2>&1 </dev/null &
			figlio=$!
			# ⚠ `wait` torna presto se arriva un segnale: si riaspetta finche' c'e'
			wait "$figlio"; c=$?
			while kill -0 "$figlio" 2>/dev/null; do wait "$figlio"; c=$?; done
			figlio=""
			FATTE=$((FATTE + 1)); SECONDI=$((SECONDI + $(date +%s) - T_SALITA))
			verde=$(ultimo_green "$camp")
			segna "$d" "$m" "$camp" "$c" "$verde"
			dice "   $camp: codice $c ($(python3 -c "import json,sys; s=json.load(open(sys.argv[1])); print('buono', s.get('ultimo_buono'), '· rottura', s.get('rottura'), '·', s.get('fase'))" "$MISURE_DIR/$camp/stato.json" 2>/dev/null || echo 'stato illeggibile')) · ultimo GREEN vero: $verde"
			if [ "$FERMATA" = 1 ]; then dice "⏹ fermata da fuori: la salita ha sgomberato, esco"; exit 0; fi
			if [ "$c" = 3 ] && [ "$tentativo" = 1 ]; then
				dice "   ⚠ BLOCKED o interrotta: riprovo fra 2 minuti"
				sleep 120 &
				figlio=$!; wait "$figlio"; figlio=""
				if [ "$FERMATA" = 1 ]; then dice "⏹ fermata da fuori: esco"; exit 0; fi
				continue
			fi
			esito=$c
			break
		done
		restano_qui=$(( $(echo $SCALA | wc -w) - I_MISURA ))
		case "$esito" in
		1) ;;
		*) restano_qui=0 ;;
		esac
		preventivo "$d" "$restano_qui" "$((N_DESKTOP - I_DESKTOP))"
		case "$esito" in
		0) dice "✅ $d regge 16 utenti a $m (ultimo GREEN vero: $verde)"; break ;;
		1) dice "↘ $d cede a $m (ultimo GREEN vero: $verde): scendo di misura" ;;
		*) dice "⛔ $d a $m: due volte BLOCKED — passo al desktop dopo"; break ;;
		esac
	done
done
dice "⏹ coda $SCHEDA finita"
