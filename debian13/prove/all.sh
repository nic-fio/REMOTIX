#!/bin/bash
# all.sh <de> [--fresh <path-to.deb>] - every check of prove/ on ONE box, in sequence, one log per check, a final table.
#   <de>      xfce | lxqt | gnome | kde
#   --fresh   first a fresh box with that package (fresh.sh: reset, install, enable)
# Order: base (Chrome, Firefox), lifecycle, multiuser, desktop, media, resilience, audio (Chrome, Firefox), clipboard, input (Chrome, Firefox), phone, prelocal, ban (LAST: it bans the test address
# of the box's service and unblocks it again at the end, see check-ban.py).
# Logs: log/<tag>/<check>.out, the table also in log/<tag>/summary.txt. <tag> = $TAG or <de>-<date>-<time>.
# RX_BANCO=vm: the bench is ONE of the four QEMU VMs (banco-vm/), not a container: fresh = fresh-vm.sh, ports 884x, RX_TEMPO=2 (deadlines x2);
#   --clean (VM only) = the same clean-up without installing a package. WITHOUT --fresh/--clean the VM is NOT cleaned (as the container was not).
#   what has no meaning there is listed as SKIP with the reason (never PASS) and does not make the run fail; see the skip lines below.
# Exit 0 only if every line of every check is PASS. Safe to run for the four desktops at the same time: the runs share
# nothing (own compositor, browser profile and ports per run, see lib.py; each box has its own users and files).
cd "$(dirname "$0")" || exit 2
usage() { echo "usage: $0 xfce|lxqt|gnome|kde [--fresh <path-to.deb>] [--clean (VM only: clean state, keep the installed package)] [--only label,label (a SUBSET of the checks: partial run, said in the summary, exit 3 when green)]"; exit 2; }
DE=${1:-}; [ $# -gt 0 ] && shift
case $DE in xfce|lxqt|gnome|kde) ;; *) usage ;; esac
FRESH=; CLEAN=; ONLY=
while [ $# -gt 0 ]; do case $1 in --fresh) FRESH=${2:-}; [ -f "$FRESH" ] || usage; FRESH=$(readlink -f "$FRESH"); shift 2 ;; --clean) [ "${RX_BANCO:-}" = vm ] || usage; CLEAN=1; shift ;; --only) ONLY=,${2:-},; [ "$ONLY" != ,, ] || usage; shift 2 ;; *) usage ;; esac; done
LABELS="base-chrome base-firefox lifecycle multiuser desktop media resilience audio-chrome audio-firefox clipboard input-chrome input-firefox phone prelocal ban package"
[ -z "$ONLY" ] || [ -n "$(echo "$ONLY" | tr -d ,)" ] || { echo "--only: no label given. Valid labels: $LABELS"; exit 2; }
if [ -n "$ONLY" ]; then for l in $(echo "$ONLY" | tr ',' ' '); do case " $LABELS " in *" $l "*) ;; *) echo "--only: \"$l\" is not a check. Valid labels: $LABELS"; exit 2 ;; esac; done; fi
case ${RX_TEMPO-1} in ''|*[!0-9]*|0*) echo "RX_TEMPO must be an integer >= 1, no leading zero (got \"${RX_TEMPO:-}\")"; exit 2 ;; esac
TAG=${TAG:-$DE-$(date +%y%m%d-%H%M%S)}
L=log/$TAG; mkdir -p "$L"
ROWS=(); CH=
[ "${RX_BANCO:-}" = vm ] && export RX_TEMPO=${RX_TEMPO:-2}
T=${RX_TEMPO-1}
trap '[ -n "$CH" ] && kill -TERM "$CH" 2>/dev/null; ABORT=1' TERM INT HUP

# run <label> <seconds> <command...>: the output goes to $L/<label>.out; one table row per verdict line of the check
run() {
	local label=$1 lim=$2 rc n=0 st name; shift 2
	lim=$((lim * T))
	[ -n "$ONLY" ] && case $ONLY in *",$label,"*) ;; *) return 0 ;; esac  # --only: the other checks are not run (the summary says so)
	[ -n "${ABORT:-}" ] && { ROWS+=("$label|BLOCKED (aborted)"); return; }
	timeout -k 20 "$lim" "$@" >"$L/$label.out" 2>&1 </dev/null & CH=$!
	wait "$CH"; rc=$?; wait "$CH" 2>/dev/null; CH=
	echo "exit=$rc" >>"$L/$label.out"
	while read -r st name _; do ROWS+=("$label/$name|$st"); n=$((n+1)); done < <(grep -E '^(PASS|FAIL|BLOCKED) [^ ]+ - ' "$L/$label.out")
	[ "$rc" -eq 124 ] && ROWS+=("$label|BLOCKED (no answer in ${lim} s)")
	[ "$n" -eq 0 ] && [ "$rc" -ne 124 ] && ROWS+=("$label|BLOCKED (no verdict, exit $rc)")
	return 0
}

if [ "${RX_BANCO:-}" = vm ]; then
	rk=$(./banco-vm/box.sh rootkey "$DE" 2>&1 </dev/null) || { echo "FAIL $rk" | tee "$L/summary.txt"; exit 1; }
	case $rk in *installed*) ROWS+=("bench-key/note|NOTE (bench key installed for root in the VM: /root/.ssh/authorized_keys keeps it)") ;; esac
	# the checks run in the VM as root by ssh with the bench key: what is sent on stdin must reach the command intact
	head -c 300000 /dev/urandom > "$L/stdin-test.bin"
	[ "$(stat -c %s "$L/stdin-test.bin")" = 300000 ] || { echo "FAIL the test file for the stdin check is not 300000 bytes" | tee "$L/summary.txt"; exit 1; }
	want=$(md5sum < "$L/stdin-test.bin" | cut -d' ' -f1); got=$(./banco-vm/box.sh ssh "$DE" md5sum < "$L/stdin-test.bin" 2>/dev/null | grep -Eo '^[0-9a-f]{32}' | head -1 || true)  # stdout only, first 32 hex digits (md5sum prints "<md5>  -")
	rm -f "$L/stdin-test.bin"
	[ "$want" = "$got" ] || { echo "FAIL the VM of $DE: stdin through the root ssh is not intact (md5 $want, got \"$got\"): the run does not start" | tee "$L/summary.txt"; exit 1; }
fi
if [ -n "$FRESH" ] || [ -n "$CLEAN" ]; then
	timeout -k 20 900 env DEB="$FRESH" ./fresh.sh "$DE" >"$L/fresh.out" 2>&1 </dev/null; rc=$?
	grep -q 'Welcome Center hidden' "$L/fresh.out" && ROWS+=("fresh/note|NOTE (Welcome Center hidden in /etc/skel by the test bench: it stays for users made by hand too)")
	if [ $rc -eq 0 ]; then ROWS+=("fresh|PASS"); else ROWS+=("fresh|BLOCKED (fresh box failed, exit $rc: $(tail -1 "$L/fresh.out" | cut -c1-80))"); ABORT=1; fi
fi
skip() { [ -n "$ONLY" ] && case $ONLY in *",${1%%/*},"*) ;; *) return 0 ;; esac; ROWS+=("$1|SKIP ($2)"); }  # skip <label> <reason>: shown in the table, not counted as a failure, never as PASS
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
run prelocal 2400 python3 check-prelocal.py --box "$DE"
run ban 900 python3 check-ban.py --box "$DE"
if [ "${RX_BANCO:-}" = vm ]; then
	skip prelocal/real-greeter "the real graphical login of the display manager (GDM/SDDM/LightDM) cannot be automated: by hand; the hook itself is checked above by calling it"
	skip ban/other-addresses "all clients reach the VM as 10.0.2.2, so only the ban of that one address is tried (the key); the 127.0.0.1 case of the containers does not exist"
	skip package "check-package.py is not part of this run (it never was) and needs box.sh reset, which a VM cannot do"
fi

python3 -c "import lib,sys; sys.exit(lib.sweep('$DE'))" > "$L/sweep.out" 2>&1 </dev/null || ROWS+=("sweep|BLOCKED (sessions left: $(cat "$L/sweep.out" | tail -1 | cut -c1-60))")
cat "$L/sweep.out"
{
	echo "== $DE  $TAG  ${FRESH:+(fresh box: $FRESH)}${ONLY:+  PARTIAL RUN, only: ${ONLY//,/ }}"
	printf '%-44s | %s\n' check result
	printf '%-44s-+-%s\n' "--------------------------------------------" "-------"
	bad=0; sk=0; np=0; nf=0; nb=0; nn=0
	for r in "${ROWS[@]}"; do
		printf '%-44s | %s\n' "${r%%|*}" "${r#*|}"
		case ${r#*|} in
		PASS) [ "${r%%|*}" = fresh ] || np=$((np+1)) ;;
		SKIP*) sk=$((sk+1)) ;;
		NOTE*) nn=$((nn+1)) ;;
		FAIL*) nf=$((nf+1)); bad=$((bad+1)) ;;
		*) nb=$((nb+1)); bad=$((bad+1)) ;;
		esac
	done
	echo "lines of the checks: $np PASS, $nf FAIL, $nb BLOCKED/other, $sk SKIP, $nn NOTE"
	if [ $bad -ne 0 ]; then echo "$bad line(s) not PASS (details: $L/*.out)"
	elif [ $np -eq 0 ]; then echo "NO CHECK PRODUCED A PASS: nothing proven (not ALL green)"
	elif [ -n "$ONLY" ]; then echo "ALL PASS OF A PARTIAL RUN (only: ${ONLY//,/ }): not a full run"
	elif [ $sk -eq 0 ]; then echo "ALL PASS"
	else echo "ALL PASS ($sk SKIP with the reason in the table, none of them a PASS)"; fi
} | tee "$L/summary.txt"
# exit: 0 = a FULL run, all PASS; 3 = all PASS but a PARTIAL run (--only): a caller that tests "== 0" cannot take it for a full green; 1 = not green
if [ -z "${ABORT:-}" ] && ! grep -q 'not PASS' "$L/summary.txt" && grep -q 'ALL PASS' "$L/summary.txt"; then [ -n "$ONLY" ] && exit 3; exit 0; fi
exit 1
