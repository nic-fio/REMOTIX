#!/bin/bash
#
# 02-figlio-lancia.sh — ⛔ IT RUNS ON CHUWI.  The bench «one child per user» —
# `DECISIONI.md` §1.10-bis.
#
#   bash banchi/02-figlio-lancia.sh previsione   the expectation, BEFORE the round
#   bash banchi/02-figlio-lancia.sh porte        counts 7448 · 7501 · 7561
#   bash banchi/02-figlio-lancia.sh porta        copies src/ and the benches to NIC-OS
#   bash banchi/02-figlio-lancia.sh costruisci   `make` in the container
#   bash banchi/02-figlio-lancia.sh terreno      the test password, 0600
#   bash banchi/02-figlio-lancia.sh bus          root does NOT reach it, the user does
#   bash banchi/02-figlio-lancia.sh accendi      the server AS ROOT on 7571
#   bash banchi/02-figlio-lancia.sh misura [caso]
#   bash banchi/02-figlio-lancia.sh guasto <uid|cieco>   injects + rebuilds
#   bash banchi/02-figlio-lancia.sh registro
#   bash banchi/02-figlio-lancia.sh spegni
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

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/fondamenta/strumenti/sshpw.py"
FUORI=/media/REMOTIX/src
ALBERO=$FUORI/02-figlio-src
DENTRO=/srv/src
PORTA=7571
LAV=/media/REMOTIX/tmp/02-figlio
LAV_DENTRO=/srv/remotix/tmp/02-figlio
UTENTE=${UTENTE:-nicfio}
UTENTE2=${UTENTE2:-prova}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 python3 "$SSHPW" "$1"; }
dentro() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
metti()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }

AZIONE=${1:-}

case "$AZIONE" in
previsione)
	python3 "$QUI/02-figlio-prova.py" --previsione
	exit 0 ;;

porte)
	log "The others' ports, counted — they are NOT touched"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|7571)\b' | sort"
	exit 0 ;;

porta)
	log "1. The product sources, in a tree of MINE"
	# ⛔ The folder is DELETED before copying it again: a file from yesterday left
	#    in there answers «I exist» just like a current one.  ⚠ And on CHUWI `rsync`
	#    is not there — measured, not assumed.
	fuori "rm -rf $ALBERO/src $ALBERO/banchi && mkdir -p $ALBERO/src $ALBERO/banchi/rcp" \
		|| { ko "I could not remake $ALBERO"; exit 2; }
	tar czf /tmp/02-figlio-src.tgz -C "$RADICE" src banchi/rcp \
		|| { ko "tar failed"; exit 2; }
	metti /tmp/02-figlio-src.tgz "$ALBERO/src.tgz" || { ko "scp failed"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && ls src/figlio.c banchi/rcp/rcp.c" \
		|| { ko "the tree did not unpack"; exit 2; }
	log "2. And the benches, next to the others"
	for f in 02-figlio-prova.py 02-figlio-accendi.sh 02-filo-cliente.py \
	         01-b3-cliente.py 02-filo-fotogramma.py; do
		metti "$QUI/$f" "$FUORI/$f" || { ko "scp of $f failed"; exit 2; }
	done
	ok "five benches → $FUORI/"
	exit 0 ;;

costruisci)
	log "make, inside the container, in the 02-figlio-src tree"
	# ⛔ `costruisci.sh` throws away the old binary BEFORE building, compares
	#    `rcp.c` with the twin copy and checks the marks inside the binary.
	dentro "cd $DENTRO/02-figlio-src/src && bash costruisci.sh"
	exit $? ;;

terreno)
	log "The test password, in a 0600 file (defect D12)"
	# ⛔ It is written with a shell builtin: not even the writing goes through a
	#    process, so it does not appear in `ps`.  ⚠ It is the PUBLIC password of the
	#    benches for «prova»; for «nicfio» it is the one in ~/SERVER.ssh, which this
	#    file NEVER prints.
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	[ -n "$PW" ] || { ko "⛔ I did not read the password from ~/SERVER.ssh"; exit 2; }
	umask 077
	printf '%s' "$PW" > /tmp/02-figlio-parola
	metti /tmp/02-figlio-parola "$FUORI/tmp/02-figlio-parola" || exit 2
	rm -f /tmp/02-figlio-parola
	printf '%s' "parola-di-prova" > /tmp/02-figlio-parola2
	metti /tmp/02-figlio-parola2 "$FUORI/tmp/02-figlio-parola2" || exit 2
	rm -f /tmp/02-figlio-parola2
	fuori "chmod 600 $FUORI/tmp/02-figlio-parola $FUORI/tmp/02-figlio-parola2 && ls -l $FUORI/tmp/02-figlio-parola*"
	ok "the two passwords are on NIC-OS, 0600, and never in an argv"
	exit 0 ;;

bus)
	log "⛔ The check that holds up the whole mandate, measured again now"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh bus"
	exit $? ;;

accendi)
	log "The server AS ROOT on $PORTA"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh accendi"
	exit $? ;;

riaccendi)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh riaccendi"
	exit $? ;;

spegni)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh spegni"
	exit $? ;;

stato)
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh stato"
	exit $? ;;

guasto)
	CASO=${2:-uid}
	log "⛔ Injecting the fault «$CASO» INTO THE COPY, and rebuilding"
	fuori "sudo -S -p 'Password sudo: ' bash $FUORI/02-figlio-accendi.sh guasto $CASO" || exit 2
	dentro "cd $DENTRO/02-figlio-src/src && bash costruisci.sh"
	exit $? ;;

misura)
	CASO=${2:-tutti}
	log "The measurement — case «$CASO»"
	# ⛔ The server pid is read from this bench's PID FILE, not from
	#    `pgrep remotix`: that would also find the servers of the other three.
	dentro "python3 $DENTRO/02-figlio-prova.py --caso $CASO --porta $PORTA --pid-file $LAV_DENTRO/pid --registro $LAV_DENTRO/registro.log --utente $UTENTE --parola-file $DENTRO/tmp/02-figlio-parola --utente2 $UTENTE2 --lavoro $DENTRO/tmp --uscita $DENTRO/02-figlio-esiti.jsonl"
	exit $? ;;

registro)
	log "The server's «figlio» and «video» lines"
	fuori "grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (figlio|video|avvio) ' $LAV/registro.log | tail -60"
	exit 0 ;;

*)
	sed -n '2,20p' "$0"
	exit 2 ;;
esac
