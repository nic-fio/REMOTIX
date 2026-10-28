#!/bin/bash
# 15-fschede-run.sh — F-SCHEDE over the scenarios, desktop by desktop: start the two-card box, ONE session, stop (always).
#
#   bash 15-fschede-run.sh --ramo <worktree> --label <name> [--desktops "xfce lxqt kde gnome"] [--browser chrome]
#                          [--scenarios "plain swap req-intel req-amd swap-req-amd"] [--build] [--no-fault]
#
#   plain          no option: the product's own choice
#   swap           the names renderD128/129 exchanged (must NOT change the chosen card)
#   req-intel|req-amd        --render-node on that card (secondary: only the encoder's fallback and its warning)
#   swap-req-intel|swap-req-amd   both
#   --build        compiles the worktree and assembles the stage first (11-two-cards.sh build + assemble); without it the stage
#                  must already be there (assemble) and is the product under test
# ⛔ Do NOT run while a measure or another suite round is using either card.  The boxes of the round are not touched.
# Output: /media/REMOTIX-15/log/fschede-<label>/  (one log + evidence per desktop×scenario; fschede.txt = the verdicts), rc 0 all PASS.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
RAMO=""; LABEL=""; DESKTOPS="xfce lxqt kde gnome"; BROWSER=chrome; SCEN="plain swap req-intel req-amd swap-req-amd"; BUILD=0; FAULT=--fault
while [ $# -gt 0 ]; do
	case $1 in
	--ramo) RAMO=$2; shift 2 ;; --label) LABEL=$2; shift 2 ;; --desktops) DESKTOPS=$2; shift 2 ;;
	--browser) BROWSER=$2; shift 2 ;; --scenarios) SCEN=$2; shift 2 ;; --build) BUILD=1; shift ;; --no-fault) FAULT=""; shift ;;
	*) echo "unknown argument: $1"; exit 2 ;;
	esac
done
[ -n "$RAMO" ] && [ -n "$LABEL" ] || { sed -n '2,/^set -uo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 2; }
RAMO=$(cd "$RAMO" && pwd) || exit 2
case $LABEL in ""|*[!a-z0-9-]*) echo "--label: lowercase letters, digits, dashes"; exit 2 ;; esac
TWO=$HERE/../11-boxes/11-two-cards.sh          # the bench's OWN script (the worktree under test may not have it); --ramo is only build/assemble's argument
STAGE=${REMOTIX_DUE_ROOT:-/media/REMOTIX-15/lavori/due-schede}/stage-$LABEL      # one stage per label
OUT=/media/REMOTIX-15/log/fschede-$LABEL
mkdir -p "$OUT" || exit 1
VERD=$OUT/fschede.txt; : > "$VERD"
STOP_LIST=""
finish() { for d in $STOP_LIST; do bash "$TWO" stop "$d" > /dev/null 2>&1; done; }
trap finish EXIT
trap 'exit 130' INT TERM HUP
if [ "$BUILD" = 1 ]; then
	bash "$TWO" build --ramo "$RAMO" > "$OUT/build.log" 2>&1 || { echo "build failed: $OUT/build.log"; exit 1; }
	bash "$TWO" assemble --ramo "$RAMO" --stage "$STAGE" > "$OUT/assemble.log" 2>&1 || { echo "assemble failed: $OUT/assemble.log"; exit 1; }
fi
# the product under test must BE the worktree's binary: refuse a stage left over from another build
M_STAGE=$(md5sum "$STAGE/prodotto/remotix" 2>/dev/null | cut -c1-32); M_RAMO=$(md5sum "$RAMO/src/remotix" 2>/dev/null | cut -c1-32)
{ echo "# stage $STAGE · prodotto/remotix md5 ${M_STAGE:-MISSING} · $RAMO/src/remotix md5 ${M_RAMO:-MISSING}"; } >> "$VERD"
if [ -z "$M_STAGE" ] || [ "$M_STAGE" != "$M_RAMO" ]; then
	echo "the stage ($STAGE) does not hold the binary of $RAMO/src/remotix (${M_STAGE:-missing} vs ${M_RAMO:-missing}): use --build"; exit 1
fi
BAD=0
for d in $DESKTOPS; do
	for sc in $SCEN; do
		opts=()
		case $sc in swap*) opts+=(--swap) ;; esac
		case $sc in *req-intel) opts+=(--render-node intel) ;; *req-amd) opts+=(--render-node amd) ;; esac
		case $sc in plain|swap|req-intel|req-amd|swap-req-intel|swap-req-amd) ;; *) echo "scenario «$sc»?"; BAD=1; continue ;; esac
		echo "=== $(date +%T) $d $sc"
		STOP_LIST="$d"
		if ! bash "$TWO" start "$d" --stage "$STAGE" "${opts[@]}" > "$OUT/$d-$sc-start.log" 2>&1; then
			echo "    box start FAILED ($OUT/$d-$sc-start.log)"; echo "$d $sc BOX-KO" >> "$VERD"; BAD=1
			bash "$TWO" stop "$d" > /dev/null 2>&1; STOP_LIST=""; continue
		fi
		timeout 900 bash "$HERE/15-one.sh" 15-fschede-two-cards.py --box "$d" --browser "$BROWSER" $FAULT \
			--evidence "$OUT/ev-$d-$sc" > "$OUT/$d-$sc.log" 2>&1
		rc=$?
		[ "$rc" -eq 0 ] || BAD=1
		echo "$d $sc rc=$rc $(grep -a '^SUITE ' "$OUT/$d-$sc.log" | grep -a '"pass": "healthy"' | grep -ao '"outcome": "[A-Z]*"\|"rationale": "[^"]*"\|"compositor_card": "[a-z?]*"' | tr '\n' ' ' | cut -c1-400)" | tee -a "$VERD"
		bash "$TWO" stop "$d" > /dev/null 2>&1; STOP_LIST=""
	done
done
echo "=== END, verdicts in $VERD"
exit $BAD
