#!/bin/bash
# 15-f013-variants.sh — F-013 (video + sound) on Firefox at 4K, the page's video routes side by side
# (DECISIONS-11 §11.36 D: the worker route default on desktop Firefox; B1.13 of RELEASE-CHECKLIST-1.5).
#
#   (on the server, as nicfio)
#   bash 15-f013-variants.sh --box xfce [--port 9361] [--runs 3] [--routes "default main"] [--out DIR]
#                            [--client "NAME=ENV=VAL ..."]
#
# One run = `15-one.sh 15-f013-video.py --box B --browser firefox --video-route R --evidence DIR/…`.
# The routes are INTERLEAVED (round 1: every route, round 2: every route …), so a slow drift of the server
# or of the browser's machine does not fall on one route only.  With --client the whole matrix is repeated
# for every client setting: «fast=» (nothing added), «slow=ENV=VAL» puts ENV=VAL in the environment of the
# browser's run — e.g. the variable the box uses to put the client's browser on the Intel card (decoder
# downstream slower than the RX 6800's).  The caller says it: this script does not know the box's variables.
# Output: DIR/<client>-<route>-<n>/{log.txt,rc,evidence/}, and a table on stdout (rc 0 = PASS) with the
# F-013 lines of every run.  The numbers to read are in each run's f013-*.json (photos/min, age, queue).
#
# ⛔ It RUNS a real browser against a real box: never on the shared server while it measures, never on the
#    rete11 boxes (a private box only, as in the 16 Oct measurements).  Exit: 0 if every run passed, 1 otherwise,
#    2 usage.
HERE=$(cd "$(dirname "$0")" && pwd)
BOX=""; PORT=""; RUNS=3; ROUTES="default main"; OUT=""; CLIENTS="fast="
while [ $# -gt 0 ]; do
	case "$1" in
	--box) BOX=$2; shift 2 ;;
	--port) PORT=$2; shift 2 ;;
	--runs) RUNS=$2; shift 2 ;;
	--routes) ROUTES=$2; shift 2 ;;
	--out) OUT=$2; shift 2 ;;
	--client) CLIENTS=$2; shift 2 ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done
[ -n "$BOX" ] || { echo "usage: $0 --box gnome|kde|xfce|lxqt [--port P] [--runs N] [--routes \"default main worker\"] [--out DIR] [--client \"fast= slow=ENV=VAL\"]" >&2; exit 2; }
case "$RUNS" in ''|*[!0-9]*|0) echo "--runs wants a positive integer" >&2; exit 2 ;; esac
for r in $ROUTES; do case "$r" in default|worker|main) ;; *) echo "unknown route: $r" >&2; exit 2 ;; esac; done
[ -n "$OUT" ] || OUT=/media/REMOTIX-15/misure/f013-variants-$(date +%Y%m%d-%H%M%S)
mkdir -p "$OUT" || exit 2
bad=0
printf '%-10s %-8s %-3s %-4s %s\n' CLIENT ROUTE RUN RC F-013 | tee "$OUT/table.txt"
for n in $(seq 1 "$RUNS"); do
	for c in $CLIENTS; do
		name=${c%%=*}; envs=${c#*=}
		for r in $ROUTES; do
			d=$OUT/$name-$r-$n; mkdir -p "$d/evidence"
			# shellcheck disable=SC2086
			env $envs bash "$HERE/15-one.sh" 15-f013-video.py --box "$BOX" ${PORT:+--port "$PORT"} --browser firefox \
				--video-route "$r" --evidence "$d/evidence" > "$d/log.txt" 2>&1
			rc=$?; echo "$rc" > "$d/rc"
			[ "$rc" = 0 ] || bad=1
			line=$(grep -a -m1 "F-013" "$d/log.txt" | cut -c1-150)
			printf '%-10s %-8s %-3s %-4s %s\n' "$name" "$r" "$n" "$rc" "$line" | tee -a "$OUT/table.txt"
		done
	done
done
echo "outputs in $OUT"
exit $bad
