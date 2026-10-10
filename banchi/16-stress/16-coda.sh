#!/bin/bash
# 16-coda.sh — the QUEUE of the phase 16 climbs: it runs by itself, on the server, to the end.
#
#   (on the server, as nicfio)
#   sudo systemd-run --unit=r16-coda --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \
#        -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue \
#        bash /media/REMOTIX/src/controllo/banchi/16-stress/16-coda.sh intel gnome kde xfce lxqt
#
# ⛔ OOMPolicy=continue is NOT optional: [M] 26 Sep 02:02, XFCE 4K at 12 users, the
#    machine (which also runs the client browsers) ran out of RAM and the kernel
#    killed a Chrome; with the default policy (stop) systemd stopped the WHOLE queue.
#    A process killed for memory is a red rung to measure, not the end of the night.
# ⛔ TimeoutStopSec=1200 and KillMode=mixed are NOT optional: the clean-up of a climb
#    (actors up to 120 s, tenants, compositors, the server put back) lasts well over the
#    default 90 s, and with KillMode=control-group the SIGTERM would arrive TOGETHER to all
#    (actors, browsers, the sudo of the clean-up).  With «mixed» only this queue receives it, and
#    it passes it to the climb in progress and waits for it to have cleaned up; the SIGKILL to the whole
#    group only after 1200 s.
#
# ⭐ Why a queue and not a Claude session that launches the climbs: the campaign lasts
#    the night (fasi/16 §6, the user's decision of 25 Sep: «without any intervention of mine»), and
#    must not depend on whoever watches it.  If the watcher stops, the server goes on.
#
# For each desktop, the ladder of sizes (§8): 4K; if the climb finds a break
# (code 1), the next size starts again from 1 user; if it reaches 16 (code 0), next
# desktop.  Code 3 (BLOCKED or stopped from outside): it retries ONCE after 2 minutes
# with a new name (§14: the evidence of the first stays), then it moves on, declared.
#
# ⛔ To stop it between one climb and the next: `touch /media/REMOTIX/misure/fase16/FERMA`.
#    To stop it at once: `sudo systemctl stop r16-coda` (the queue passes the SIGTERM to the
#    climb in progress, which closes the level as INTERROTTO — even in the middle of the short
#    check — and cleans up; then the queue exits without launching others).
#
# ⭐ In the log, beside the code, the last TRUE GREEN level of the climb (from
#    salita.jsonl): «good» for the climb includes the non-significant DEGRADED (the
#    no-continuation rule), the true GREEN is something else and is written separately.
#
# ⭐ fasi/20 §7.0 (9 Oct 2026, the user: «I expect the whole suite to last less than the 3 days
#    of remotix»): after every climb the queue writes in campagna.log the ESTIMATE of the hours
#    left — between the best case (every missing desktop holds at the first size) and the
#    worst (it goes down the whole ladder), with the mean duration of the climbs done;
#    REMOTIX_16_DESKTOP_DOPO says how many desktops remain in the campaigns after this one.
#
# Variables: REMOTIX_16_VIDEO (the file of profile D), REMOTIX_16_FPS (its f),
#            REMOTIX_16_MISURE (the ladder, default «4k 3k 2k fhd»),
#            REMOTIX_16_IN_PIU (extra options for 16-salita.py, e.g. «--scheda amd»).
set -u
SCHEDA=${1:?usage: 16-coda.sh intel|amd desktop...}
shift
DESKTOP=${*:-gnome kde xfce lxqt}
QUI=$(cd "$(dirname "$0")" && pwd)
MISURE_DIR=/media/REMOTIX/misure/fase16
# ⭐ A5 (29 Sep): the fourfold file (4 loops concatenated without re-encoding, 42 min) — with the
#   10.5 min file the player started over inside the judgement windows and froze the image 1-3 s.
VIDEO=${REMOTIX_16_VIDEO:-$MISURE_DIR/video/bbb_sunflower_2160p_30fps_x4.mp4}
FPS=${REMOTIX_16_FPS:-30}
SCALA=${REMOTIX_16_MISURE:-4k 3k 2k fhd}
LOG=$MISURE_DIR/coda-$SCHEDA.log
STATO=$MISURE_DIR/coda-$SCHEDA.jsonl
mkdir -p "$MISURE_DIR"
FATTE=0; SECONDI=0
DOPO=${REMOTIX_16_DESKTOP_DOPO:-0}
# preventivo <current desktop> <sizes left for it> <desktops left after it>
preventivo() {
	python3 - "$FATTE" "$SECONDI" "$2" "$3" "$DOPO" "$(echo $SCALA | wc -w)" <<'PY' >>"$MISURE_DIR/campagna.log"
import sys, datetime
f, s, qui, resto, dopo, scala = map(int, sys.argv[1:])
m = s / f if f else 0
lo = (qui + resto + dopo) * m if qui else (resto + dopo) * m
hi = (qui + (resto + dopo) * scala) * m
print("%s   estimate: %d climbs done, mean %.0f min · between %.1f and %.1f hours left (end between %s and %s)" % (
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
# the last true GREEN level of a campaign (the highest with class GREEN in salita.jsonl)
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

# ⭐ the SIGTERM (systemctl stop, KillMode=mixed) arrives ONLY here: it is passed to the climb
#   in progress and we wait for it to clean up; then no new climb
FERMATA=0
figlio=""
ferma() {
	FERMATA=1
	dice "⚠ signal: passing it to the climb in progress (${figlio:-none}) and waiting for it to clean up"
	[ -n "$figlio" ] && kill -TERM "$figlio" 2>/dev/null
}
trap ferma TERM INT

dice "▶ queue $SCHEDA: desktop «$DESKTOP» · ladder «$SCALA» · video $VIDEO (f=$FPS)"
[ -f "$VIDEO" ] || { dice "⛔ the video is not there: $VIDEO"; exit 2; }

N_DESKTOP=$(echo $DESKTOP | wc -w); I_DESKTOP=0
for d in $DESKTOP; do
	I_DESKTOP=$((I_DESKTOP + 1))
	I_MISURA=0
	for m in $SCALA; do
		I_MISURA=$((I_MISURA + 1))
		if [ -e "$MISURE_DIR/FERMA" ]; then dice "⏹ FERMA found: stopping"; exit 0; fi
		esito=""
		for tentativo in 1 2; do
			camp="$SCHEDA-$m-$d"
			[ "$tentativo" = 2 ] && camp="$camp-r2"
			[ -e "$MISURE_DIR/$camp/salita.jsonl" ] && camp="$camp-$(date +%H%M)"
			dice "── climb $camp (attempt $tentativo)"
			# shellcheck disable=SC2086
			T_SALITA=$(date +%s)
			python3 "$QUI/16-salita.py" --scatola "$d" --campagna "$camp" --misura "$m" \
				--video "$VIDEO" --fps-video "$FPS" ${REMOTIX_16_IN_PIU:-} \
				>>"$MISURE_DIR/coda-$SCHEDA-salite.log" 2>&1 </dev/null &
			figlio=$!
			# ⚠ `wait` returns early if a signal arrives: wait again while it is there
			wait "$figlio"; c=$?
			while kill -0 "$figlio" 2>/dev/null; do wait "$figlio"; c=$?; done
			figlio=""
			FATTE=$((FATTE + 1)); SECONDI=$((SECONDI + $(date +%s) - T_SALITA))
			verde=$(ultimo_green "$camp")
			segna "$d" "$m" "$camp" "$c" "$verde"
			dice "   $camp: code $c ($(python3 -c "import json,sys; s=json.load(open(sys.argv[1])); print('good', s.get('ultimo_buono'), '· break', s.get('rottura'), '·', s.get('fase'))" "$MISURE_DIR/$camp/stato.json" 2>/dev/null || echo 'state unreadable')) · last true GREEN: $verde"
			if [ "$FERMATA" = 1 ]; then dice "⏹ stopped from outside: the climb has cleaned up, exiting"; exit 0; fi
			if [ "$c" = 3 ] && [ "$tentativo" = 1 ]; then
				dice "   ⚠ BLOCKED or interrupted: retrying in 2 minutes"
				sleep 120 &
				figlio=$!; wait "$figlio"; figlio=""
				if [ "$FERMATA" = 1 ]; then dice "⏹ stopped from outside: exiting"; exit 0; fi
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
		0) dice "✅ $d holds 16 users at $m (last true GREEN: $verde)"; break ;;
		1) dice "↘ $d gives way at $m (last true GREEN: $verde): going down a size" ;;
		*) dice "⛔ $d at $m: BLOCKED twice — moving to the next desktop"; break ;;
		esac
	done
done
dice "⏹ queue $SCHEDA finished"
