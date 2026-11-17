#!/bin/bash
# all.sh <de> [--fresh <path-to.deb>] - every check of prove/ on ONE box, in sequence, one log per check, a final table.
#   <de>      xfce | lxqt | gnome | kde
#   --fresh   first a fresh box with that package (fresh.sh: reset, install, enable)
# Order: base (Chrome, Firefox), lifecycle, multiuser, desktop, media, resilience, audio (Chrome, Firefox), clipboard, input (Chrome, Firefox), phone, ban (LAST: it bans the test address
# of the box's service and unblocks it again at the end, see check-ban.py).
# Logs: log/<tag>/<check>.out, the table also in log/<tag>/summary.txt. <tag> = $TAG or <de>-<date>-<time>.
# Exit 0 only if every line of every check is PASS. Safe to run for the four desktops at the same time: the runs share
# nothing (own compositor, browser profile and ports per run, see lib.py; each box has its own users and files).
cd "$(dirname "$0")" || exit 2
usage() { echo "usage: $0 xfce|lxqt|gnome|kde [--fresh <path-to.deb>]"; exit 2; }
DE=${1:-}; [ $# -gt 0 ] && shift
case $DE in xfce|lxqt|gnome|kde) ;; *) usage ;; esac
FRESH=
while [ $# -gt 0 ]; do case $1 in --fresh) FRESH=${2:-}; [ -f "$FRESH" ] || usage; FRESH=$(readlink -f "$FRESH"); shift 2 ;; *) usage ;; esac; done
TAG=${TAG:-$DE-$(date +%y%m%d-%H%M%S)}
L=log/$TAG; mkdir -p "$L"
ROWS=(); CH=
trap '[ -n "$CH" ] && kill -TERM "$CH" 2>/dev/null; ABORT=1' TERM INT HUP

# run <label> <seconds> <command...>: the output goes to $L/<label>.out; one table row per verdict line of the check
run() {
	local label=$1 lim=$2 rc n=0 st name; shift 2
	[ -n "${ABORT:-}" ] && { ROWS+=("$label|BLOCKED (aborted)"); return; }
	timeout -k 20 "$lim" "$@" >"$L/$label.out" 2>&1 & CH=$!
	wait "$CH"; rc=$?; wait "$CH" 2>/dev/null; CH=
	echo "exit=$rc" >>"$L/$label.out"
	while read -r st name _; do ROWS+=("$label/$name|$st"); n=$((n+1)); done < <(grep -E '^(PASS|FAIL|BLOCKED) [^ ]+ - ' "$L/$label.out")
	[ "$rc" -eq 124 ] && ROWS+=("$label|BLOCKED (no answer in ${lim} s)")
	[ "$n" -eq 0 ] && [ "$rc" -ne 124 ] && ROWS+=("$label|BLOCKED (no verdict, exit $rc)")
	return 0
}

if [ -n "$FRESH" ]; then
	timeout -k 20 900 env DEB="$FRESH" ./fresh.sh "$DE" >"$L/fresh.out" 2>&1; rc=$?
	if [ $rc -eq 0 ]; then ROWS+=("fresh|PASS"); else ROWS+=("fresh|BLOCKED (fresh box failed, exit $rc: $(tail -1 "$L/fresh.out" | cut -c1-80))"); ABORT=1; fi
fi
run base-chrome 480 python3 check-base.py --box "$DE" --browser chrome
run base-firefox 480 python3 check-base.py --box "$DE" --browser firefox
run lifecycle 1650 python3 check-lifecycle.py --box "$DE"
run multiuser 960 python3 check-multiuser.py --box "$DE"
run desktop 2500 python3 check-desktop.py --box "$DE"
run media 1600 python3 check-media.py --box "$DE"
run resilience 2700 python3 check-resilience.py --box "$DE"
run audio-chrome 480 python3 check-audio.py --box "$DE" --browser chrome
run audio-firefox 480 python3 check-audio.py --box "$DE" --browser firefox
run clipboard 480 python3 check-clipboard.py --box "$DE"
run input-chrome 1500 python3 check-input.py --box "$DE" --browser chrome
run input-firefox 1500 python3 check-input.py --box "$DE" --browser firefox
run phone 1250 python3 check-phone.py --box "$DE"
run ban 900 python3 check-ban.py --box "$DE"

python3 -c "import lib,sys; sys.exit(lib.sweep('$DE'))" > "$L/sweep.out" 2>&1 || ROWS+=("sweep|BLOCKED (sessions left: $(cat "$L/sweep.out" | tail -1 | cut -c1-60))")
cat "$L/sweep.out"
{
	echo "== $DE  $TAG  ${FRESH:+(fresh box: $FRESH)}"
	printf '%-44s | %s\n' check result
	printf '%-44s-+-%s\n' "--------------------------------------------" "-------"
	bad=0
	for r in "${ROWS[@]}"; do
		printf '%-44s | %s\n' "${r%%|*}" "${r#*|}"; [ "${r#*|}" = PASS ] || bad=$((bad+1))
	done
	[ $bad -eq 0 ] && echo "ALL PASS" || echo "$bad line(s) not PASS (details: $L/*.out)"
} | tee "$L/summary.txt"
[ -z "${ABORT:-}" ] && ! grep -q 'not PASS' "$L/summary.txt" && grep -q 'ALL PASS' "$L/summary.txt"
