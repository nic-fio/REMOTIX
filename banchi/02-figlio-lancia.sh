#!/bin/bash
#
# 02-figlio-lancia.sh — ⛔ IT RUNS ON CHUWI.  The bench «one child per user» —
# `DECISIONI.md` §1.10-bis.
#
#   bash banchi/02-figlio-lancia.sh prediction   the expectation, BEFORE the round
#   bash banchi/02-figlio-lancia.sh ports        counts 7448 · 7501 · 7561
#   bash banchi/02-figlio-lancia.sh ship        copies src/ and the benches to NIC-OS
#   bash banchi/02-figlio-lancia.sh build   `make` in the container
#   bash banchi/02-figlio-lancia.sh terrain      the test password, 0600
#   bash banchi/02-figlio-lancia.sh bus          root does NOT reach it, the user does
#   bash banchi/02-figlio-lancia.sh start      the server AS ROOT on 7571
#   bash banchi/02-figlio-lancia.sh measure [test_case]
#   bash banchi/02-figlio-lancia.sh fault <uid|blind>   injects + rebuilds
#   bash banchi/02-figlio-lancia.sh log
#   bash banchi/02-figlio-lancia.sh stop
#
# ---------------------------------------------------------------------------
# ⛔ THE HOUSE RULES THIS FILE FOLLOWS, AND EACH ONE WAS PAID FOR
#
#   · ⛔ **NEVER a redirection AROUND `ssh` or `enter.sh`** — paid for SIX
#     times.  `sudo`'s password prompt goes to stderr, and a
#     redirection swallows it: the command hangs forever, silently.
#     ⇒ Here we go through `fondamenta/strumenti/sshpw.py`, which writes the password on the
#     pty **only when someone asks for it**, and nothing is redirected;
#   · ⛔ **a file has no levels of quotes**: what must run inside
#     the container sits in a script on the server, not inside `ssh → enter.sh →
#     bash -c`.  A `$(...)` that dies halfway has already run a case
#     «the helper is dead» on a live helper (`PAM-filo-unico.md` §6);
#   · the port is **7571**, this bench's and nobody else's.  ⛔ 7448,
#     7501 and **7561 — where the user is watching their own desktop** —
#     are COUNTED before and after, and are not touched;
#   · the source tree is **02-figlio-src**, not the one the other three servers
#     run from: a fault injected here cannot reach them;
#   · the password never goes through `argv` (defect **D12**).
set -uo pipefail

HERE=$(cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(cd -- "$HERE/.." && pwd)
SSHPW="$ROOT/fondamenta/strumenti/sshpw.py"
OUT=/media/REMOTIX/src
TREE=$OUT/02-figlio-src
INSIDE=/srv/src
PORT=7571
WORKDIR=/media/REMOTIX/tmp/02-figlio
WORK_INSIDE=/srv/remotix/tmp/02-figlio
ACCOUNT=${ACCOUNT:-nicfio}
ACCOUNT2=${ACCOUNT2:-prova}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

report()  { timeout 900 python3 "$SSHPW" "$1"; }
inside() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
put()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }

ACTION=${1:-}

case "$ACTION" in
prediction)
	python3 "$HERE/02-figlio-prova.py" --prediction
	exit 0 ;;

ports)
	log "The others' ports, counted — they are NOT touched"
	report "ss -tuln | grep -E ':(7448|7501|7561|7571)\b' | sort"
	exit 0 ;;

ship)
	log "1. The product sources, in a tree of MINE"
	# ⛔ The folder is DELETED before copying it again: a file from yesterday left
	#    in there answers «I exist» just like a current one.  ⚠ And on CHUWI `rsync`
	#    is not there — measured, not assumed.
	report "rm -rf $TREE/src $TREE/banchi && mkdir -p $TREE/src $TREE/banchi/rcp" \
		|| { ko "I could not remake $TREE"; exit 2; }
	tar czf /tmp/02-figlio-src.tgz -C "$ROOT" src banchi/rcp \
		|| { ko "tar failed"; exit 2; }
	put /tmp/02-figlio-src.tgz "$TREE/src.tgz" || { ko "scp failed"; exit 2; }
	report "cd $TREE && tar xzf src.tgz && ls src/figlio.c banchi/rcp/rcp.c" \
		|| { ko "the tree did not unpack"; exit 2; }
	log "2. And the benches, next to the others"
	for f in 02-figlio-prova.py 02-figlio-accendi.sh 02-filo-cliente.py \
	         01-b3-cliente.py 02-filo-fotogramma.py; do
		put "$HERE/$f" "$OUT/$f" || { ko "scp of $f failed"; exit 2; }
	done
	ok "five benches → $OUT/"
	exit 0 ;;

build)
	log "make, inside the container, in the 02-figlio-src tree"
	# ⛔ `costruisci.sh` throws away the old binary BEFORE building, compares
	#    `rcp.c` with the twin copy and checks the marks inside the binary.
	inside "cd $INSIDE/02-figlio-src/src && bash costruisci.sh"
	exit $? ;;

terrain)
	log "The test password, in a 0600 file (defect D12)"
	# ⛔ It is written with a shell builtin: not even the writing goes through a
	#    process, so it does not appear in `ps`.  ⚠ It is the PUBLIC password of the
	#    benches for «prova»; for «nicfio» it is the one in ~/SERVER.ssh, which this
	#    file NEVER prints.
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	[ -n "$PW" ] || { ko "⛔ I did not read the password from ~/SERVER.ssh"; exit 2; }
	umask 077
	printf '%s' "$PW" > /tmp/02-figlio-parola
	put /tmp/02-figlio-parola "$OUT/tmp/02-figlio-parola" || exit 2
	rm -f /tmp/02-figlio-parola
	printf '%s' "parola-di-prova" > /tmp/02-figlio-parola2
	put /tmp/02-figlio-parola2 "$OUT/tmp/02-figlio-parola2" || exit 2
	rm -f /tmp/02-figlio-parola2
	report "chmod 600 $OUT/tmp/02-figlio-parola $OUT/tmp/02-figlio-parola2 && ls -l $OUT/tmp/02-figlio-parola*"
	ok "the two passwords are on NIC-OS, 0600, and never in an argv"
	exit 0 ;;

bus)
	log "⛔ The check that holds up the whole mandate, measured again now"
	report "sudo -S -p 'Password sudo: ' bash $OUT/02-figlio-accendi.sh bus"
	exit $? ;;

start)
	log "The server AS ROOT on $PORT"
	report "sudo -S -p 'Password sudo: ' bash $OUT/02-figlio-accendi.sh start"
	exit $? ;;

restart)
	report "sudo -S -p 'Password sudo: ' bash $OUT/02-figlio-accendi.sh restart"
	exit $? ;;

stop)
	report "sudo -S -p 'Password sudo: ' bash $OUT/02-figlio-accendi.sh stop"
	exit $? ;;

status)
	report "sudo -S -p 'Password sudo: ' bash $OUT/02-figlio-accendi.sh status"
	exit $? ;;

fault)
	CASE=${2:-uid}
	log "⛔ Injecting the fault «$CASE» INTO THE COPY, and rebuilding"
	report "sudo -S -p 'Password sudo: ' bash $OUT/02-figlio-accendi.sh fault $CASE" || exit 2
	inside "cd $INSIDE/02-figlio-src/src && bash costruisci.sh"
	exit $? ;;

measure)
	CASE=${2:-tutti}
	log "The measurement — case «$CASE»"
	# ⛔ The server pid is read from this bench's PID FILE, not from
	#    `pgrep remotix`: that would also find the servers of the other three.
	inside "python3 $INSIDE/02-figlio-prova.py --case $CASE --port $PORT --pid-file $WORK_INSIDE/pid --log $WORK_INSIDE/registro.log --user $ACCOUNT --password-file $INSIDE/tmp/02-figlio-parola --user2 $ACCOUNT2 --workdir $INSIDE/tmp --output $INSIDE/02-figlio-esiti.jsonl"
	exit $? ;;

log)
	log "The server's «child» and «video» lines"
	report "grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (child|video|startup) ' $WORKDIR/registro.log | tail -60"
	exit 0 ;;

*)
	sed -n '2,20p' "$0"
	exit 2 ;;
esac
