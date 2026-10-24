#!/bin/bash
# ⚠ NOTE (25 Oct 2026): THIS LAUNCHER STILL DRIVES THE OLD CHUWI -> NIC-OS CONTAINER (enter.sh, sudo password, /srv/src) AND IS NOT
#   USED ANY MORE.  The bench runs on one machine, as root, with `02-pam-start.sh` and `02-pam-standstill.py` called directly:
#   see «HOW TO RUN» in the head of 02-pam-standstill.py (three scenes: free, unchecked, restart).
#
# 02-pam-launch.sh — ⛔ IT RUNS ON CHUWI.  The bench «how long whoever is NOT
# authenticating stands still» — `DECISIONS.md` §1.10.
#
#   bash benches/02-pam-launch.sh prediction     the expectation, BEFORE the round
#   bash benches/02-pam-launch.sh ship          copies src/ and the benches to NIC-OS
#   bash benches/02-pam-launch.sh build     copy + `make` in the container
#   bash benches/02-pam-launch.sh start
#   bash benches/02-pam-launch.sh measure <blocked|free|none> [rounds]
#   bash benches/02-pam-launch.sh log
#   bash benches/02-pam-launch.sh stop
#   bash benches/02-pam-launch.sh ports          counts 7448 and 7501
#
# ---------------------------------------------------------------------------
# ⛔ WHY THIS FILE EXISTS, AND NOT A RECIPE IN PROSE
#
# The same reason as `01-p5-accendi.sh`: a recipe written in words is
# copied by hand by whoever uses it, and on 11 Aug 2026 it was got wrong in two ways
# that a file would not have got wrong — the server started from the wrong folder
# (and its page not found), and an `&` inside three levels of quotes
# (`ssh` → `enter.sh` → `bash -c`) that does not land where it seems.
#
# ---------------------------------------------------------------------------
# ⛔ THE HOUSE RULES THIS FILE FOLLOWS, AND EACH ONE WAS PAID FOR
#
#   · NEVER a redirection AROUND `ssh` or `enter.sh` — `sudo`'s password
#     prompt goes to stderr, and a redirection swallows it:
#     the command hangs forever, SILENTLY.  ⛔ Paid for FOUR
#     times, two of them in the single night of 11 Aug 2026.  Here
#     `sudo`'s password enters through the **stdin** of `ssh` — which is the road
#     `enter.sh` documents — and the output is never redirected;
#   · the port is **7531**, this bench's and nobody else's, and ban,
#     socket, log, certificates and pid file carry the prefix
#     `pam2-7531`;
#   · **7448** and **7501** (and **7522** from another round) are not touched:
#     they are COUNTED before and after, with the `ports` step;
#   · the benches' password never goes through `argv` (defect **D12**):
#     a `0600` file written with `printf`, which is a shell builtin.
set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$HERE/.." && pwd)
SERVER=nicfio@192.168.0.2
ENTER=/media/REMOTIX/enter.sh
OUT=/media/REMOTIX/src
INSIDE=/srv/src
PORT=7531
PREFIX=pam2-7531
ACCOUNT=prova
BAD_USER=prova2
OUTCOMES_INSIDE=$INSIDE/02-pam-outcomes.jsonl

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ The `sudo` password sits in ~/SERVER.ssh and is read from there: writing it in
#    this file would put it in the repository.
PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
if [ -z "$PW" ]; then
	ko "⛔ I did not read the sudo password from ~/SERVER.ssh: it is not «empty», it is"
	ko "   «I did not find it».  Without it, every command inside the container"
	ko "   would hang waiting for it."
	exit 2
fi

# ⭐ A single function for getting in, so the form is not written twice in
#    two different ways.  ⚠ The password enters through ssh's STDIN, NEVER through argv.
inside() { printf '%s\n' "$PW" | ssh "$SERVER" "bash $ENTER --root \"$1\""; }
report()  { ssh "$SERVER" "$1"; }

ACTION=${1:-}

case "$ACTION" in
prediction)
	python3 "$HERE/02-pam-standstill.py" --prediction
	exit 0 ;;

ports)
	# ⛔ They are COUNTED, not touched.  And counted BEFORE and AFTER: «they were on»
	#    and «I left them on» are two different facts.
	log "The others' ports, counted"
	report "ss -tuln | grep -E ':(7447|7448|7501|7511|7522|7531)\b' | sort"
	exit 0 ;;

ship)
	log "1. This bench's files go to NIC-OS"
	scp -q "$HERE"/02-pam-standstill.py "$HERE"/02-pam-i3.py "$HERE"/02-pam-start.sh \
	       "$SERVER:$OUT/" \
		|| { ko "scp of the benches failed"; exit 2; }
	ok "02-pam-standstill.py and 02-pam-start.sh → $OUT/"
	log "2. And the product sources, in a folder of MINE"
	# ⛔ The folder is DELETED before copying it again: a file from yesterday left
	#    in there answers «I exist» just like a current one (LESSONS.md §1.9
	#    point 8), and `scp` alone removes nothing.  ⚠ And `rsync` on CHUWI
	#    IS NOT THERE — measured, not assumed: what is there gets used.
	report "rm -rf $OUT/02-pam-src && mkdir -p $OUT/02-pam-src" \
		|| { ko "I could not remake $OUT/02-pam-src"; exit 2; }
	scp -q "$ROOT"/src/* "$SERVER:$OUT/02-pam-src/" \
		|| { ko "scp of src/ failed"; exit 2; }
	ok "src/ → $OUT/02-pam-src/  ($(ls "$ROOT"/src | wc -l) files)"
	log "3. And the twin copy of rcp.c, which the Makefile compares (R12.3)"
	scp -q "$ROOT"/benches/rcp/* "$SERVER:$OUT/rcp/" \
		|| { ko "scp of benches/rcp/ failed"; exit 2; }
	ok "benches/rcp/ → $OUT/rcp/  (⛔ and if it diverged from src/, make stops)"
	exit 0 ;;

build)
	log "Copy and build, inside the container"
	inside "bash $INSIDE/02-pam-start.sh copy"
	exit $? ;;

fault)
	# ⛔ The fault is THE CURE REMOVED, and it is injected into the copy.  ⭐ It is healed with
	#    `build`, which remakes the copy from scratch from the real sources.
	log "Injecting the fault: the asynchronous hook NOT connected"
	inside "bash $INSIDE/02-pam-start.sh fault"
	exit $? ;;

start)
	log "This bench's target, on $PORT"
	inside "bash $INSIDE/02-pam-start.sh start"
	exit $? ;;

restart)
	# ⛔ Switches on again WITHOUT deleting the ban file: it is the step that
	#    proves invariant I7 (the ban survives the restart).
	log "Switching the target on again KEEPING the ban file (I7)"
	inside "bash $INSIDE/02-pam-start.sh restart"
	exit $? ;;

stop)
	log "Switching off MY target (and only that one)"
	inside "bash $INSIDE/02-pam-start.sh stop"
	exit $? ;;

log)
	inside "bash $INSIDE/02-pam-start.sh log"
	exit $? ;;

measure)
	WAIT=${2:-nessuna}
	ROUNDS=${3:-5}
	NOTE=${4:-}
	log "The measurement: expectation «$WAIT», $ROUNDS rounds"
	# ⛔ D12: the password in a 0600 file, written with `printf` (a builtin), and
	#    deleted right after.  Never in `argv`, which `/proc/<pid>/cmdline`
	#    shows to anyone.
	inside "umask 077; printf '%s\n' 'parola-di-prova' > $INSIDE/tmp/$PREFIX-parola; chmod 600 $INSIDE/tmp/$PREFIX-parola"
	inside "python3 $INSIDE/02-pam-standstill.py --port $PORT \
	        --user $ACCOUNT --password-file $INSIDE/tmp/$PREFIX-parola \
	        --bad-user $BAD_USER \
	        --socket $INSIDE/tmp/$PREFIX.sock \
	        --rounds $ROUNDS --wait $WAIT --outcomes $OUTCOMES_INSIDE --note '$NOTE'"
	OUTCOME=$?
	inside "rm -f $INSIDE/tmp/$PREFIX-parola"
	exit $OUTCOME ;;

i3)
	CASE=${2:?the case is needed: secondo|ban|ban-dopo-riavvio|morto|insieme|libera}
	log "I3 and §4.4-bis: the case «$CASE»"
	inside "umask 077; printf '%s\n' 'parola-di-prova' > $INSIDE/tmp/$PREFIX-parola; chmod 600 $INSIDE/tmp/$PREFIX-parola"
	inside "python3 $INSIDE/02-pam-i3.py --port $PORT --user $ACCOUNT \
	        --password-file $INSIDE/tmp/$PREFIX-parola \
	        --socket $INSIDE/tmp/$PREFIX.sock --case $CASE"
	OUTCOME=$?
	inside "rm -f $INSIDE/tmp/$PREFIX-parola"
	exit $OUTCOME ;;

kill-helper)
	# ⛔ The real work sits in `02-pam-start.sh`, which is a FILE inside the
	#    container: no `$(...)` passes through here, and the piece cannot
	#    die on the quotes while letting you believe it worked.
	log "Killing the target's PAM helper (and only its own)"
	inside "bash $INSIDE/02-pam-start.sh kill-helper"
	exit $? ;;

fetch-outcomes)
	scp -q "$SERVER:$OUT/02-pam-outcomes.jsonl" "$HERE/02-pam-outcomes.jsonl" \
		&& ok "outcomes collected in $HERE/02-pam-outcomes.jsonl" \
		|| { ko "I did not collect the outcomes"; exit 2; }
	exit 0 ;;

*)
	sed -n '2,15p' "$0"
	exit 2 ;;
esac
