#!/bin/bash
#
# 02-pam-lancia.sh — ⛔ IT RUNS ON CHUWI.  The bench «how long whoever is NOT
# authenticating stands still» — `DECISIONI.md` §1.10.
#
#   bash banchi/02-pam-lancia.sh previsione     the expectation, BEFORE the round
#   bash banchi/02-pam-lancia.sh porta          copies src/ and the benches to NIC-OS
#   bash banchi/02-pam-lancia.sh costruisci     copy + `make` in the container
#   bash banchi/02-pam-lancia.sh accendi
#   bash banchi/02-pam-lancia.sh misura <bloccato|libero|nessuna> [giri]
#   bash banchi/02-pam-lancia.sh registro
#   bash banchi/02-pam-lancia.sh spegni
#   bash banchi/02-pam-lancia.sh porte          counts 7448 and 7501
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
#     they are COUNTED before and after, with the `porte` step;
#   · the benches' password never goes through `argv` (defect **D12**):
#     a `0600` file written with `printf`, which is a shell builtin.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SERVER=nicfio@192.168.0.2
ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
PORTA=7531
PREFISSO=pam2-7531
UTENTE=prova
UTENTE_CATTIVO=prova2
ESITI_DENTRO=$DENTRO/02-pam-esiti.jsonl

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
dentro() { printf '%s\n' "$PW" | ssh "$SERVER" "bash $ENTRA --root \"$1\""; }
fuori()  { ssh "$SERVER" "$1"; }

AZIONE=${1:-}

case "$AZIONE" in
previsione)
	python3 "$QUI/02-pam-fermo.py" --previsione
	exit 0 ;;

porte)
	# ⛔ They are COUNTED, not touched.  And counted BEFORE and AFTER: «they were on»
	#    and «I left them on» are two different facts.
	log "The others' ports, counted"
	fuori "ss -tuln | grep -E ':(7447|7448|7501|7511|7522|7531)\b' | sort"
	exit 0 ;;

porta)
	log "1. This bench's files go to NIC-OS"
	scp -q "$QUI"/02-pam-fermo.py "$QUI"/02-pam-i3.py "$QUI"/02-pam-accendi.sh \
	       "$SERVER:$FUORI/" \
		|| { ko "scp of the benches failed"; exit 2; }
	ok "02-pam-fermo.py and 02-pam-accendi.sh → $FUORI/"
	log "2. And the product sources, in a folder of MINE"
	# ⛔ The folder is DELETED before copying it again: a file from yesterday left
	#    in there answers «I exist» just like a current one (LEZIONI.md §1.9
	#    point 8), and `scp` alone removes nothing.  ⚠ And `rsync` on CHUWI
	#    IS NOT THERE — measured, not assumed: what is there gets used.
	fuori "rm -rf $FUORI/02-pam-src && mkdir -p $FUORI/02-pam-src" \
		|| { ko "I could not remake $FUORI/02-pam-src"; exit 2; }
	scp -q "$RADICE"/src/* "$SERVER:$FUORI/02-pam-src/" \
		|| { ko "scp of src/ failed"; exit 2; }
	ok "src/ → $FUORI/02-pam-src/  ($(ls "$RADICE"/src | wc -l) files)"
	log "3. And the twin copy of rcp.c, which the Makefile compares (R12.3)"
	scp -q "$RADICE"/banchi/rcp/* "$SERVER:$FUORI/rcp/" \
		|| { ko "scp of banchi/rcp/ failed"; exit 2; }
	ok "banchi/rcp/ → $FUORI/rcp/  (⛔ and if it diverged from src/, make stops)"
	exit 0 ;;

costruisci)
	log "Copy and build, inside the container"
	dentro "bash $DENTRO/02-pam-accendi.sh copia"
	exit $? ;;

guasto)
	# ⛔ The fault is THE CURE REMOVED, and it is injected into the copy.  ⭐ It is healed with
	#    `costruisci`, which remakes the copy from scratch from the real sources.
	log "Injecting the fault: the asynchronous hook NOT connected"
	dentro "bash $DENTRO/02-pam-accendi.sh guasto"
	exit $? ;;

accendi)
	log "This bench's target, on $PORTA"
	dentro "bash $DENTRO/02-pam-accendi.sh accendi"
	exit $? ;;

riaccendi)
	# ⛔ Switches on again WITHOUT deleting the ban file: it is the step that
	#    proves invariant I7 (the ban survives the restart).
	log "Switching the target on again KEEPING the ban file (I7)"
	dentro "bash $DENTRO/02-pam-accendi.sh riaccendi"
	exit $? ;;

spegni)
	log "Switching off MY target (and only that one)"
	dentro "bash $DENTRO/02-pam-accendi.sh spegni"
	exit $? ;;

registro)
	dentro "bash $DENTRO/02-pam-accendi.sh registro"
	exit $? ;;

misura)
	ATTESA=${2:-nessuna}
	GIRI=${3:-5}
	NOTA=${4:-}
	log "The measurement: expectation «$ATTESA», $GIRI rounds"
	# ⛔ D12: the password in a 0600 file, written with `printf` (a builtin), and
	#    deleted right after.  Never in `argv`, which `/proc/<pid>/cmdline`
	#    shows to anyone.
	dentro "umask 077; printf '%s\n' 'parola-di-prova' > $DENTRO/tmp/$PREFISSO-parola; chmod 600 $DENTRO/tmp/$PREFISSO-parola"
	dentro "python3 $DENTRO/02-pam-fermo.py --porta $PORTA \
	        --utente $UTENTE --parola-file $DENTRO/tmp/$PREFISSO-parola \
	        --utente-cattivo $UTENTE_CATTIVO \
	        --socket $DENTRO/tmp/$PREFISSO.sock \
	        --giri $GIRI --attesa $ATTESA --esiti $ESITI_DENTRO --nota '$NOTA'"
	ESITO=$?
	dentro "rm -f $DENTRO/tmp/$PREFISSO-parola"
	exit $ESITO ;;

i3)
	CASO=${2:?the case is needed: secondo|ban|ban-dopo-riavvio|morto|insieme|libera}
	log "I3 and §4.4-bis: the case «$CASO»"
	dentro "umask 077; printf '%s\n' 'parola-di-prova' > $DENTRO/tmp/$PREFISSO-parola; chmod 600 $DENTRO/tmp/$PREFISSO-parola"
	dentro "python3 $DENTRO/02-pam-i3.py --porta $PORTA --utente $UTENTE \
	        --parola-file $DENTRO/tmp/$PREFISSO-parola \
	        --socket $DENTRO/tmp/$PREFISSO.sock --caso $CASO"
	ESITO=$?
	dentro "rm -f $DENTRO/tmp/$PREFISSO-parola"
	exit $ESITO ;;

ammazza-aiutante)
	# ⛔ The real work sits in `02-pam-accendi.sh`, which is a FILE inside the
	#    container: no `$(...)` passes through here, and the piece cannot
	#    die on the quotes while letting you believe it worked.
	log "Killing the target's PAM helper (and only its own)"
	dentro "bash $DENTRO/02-pam-accendi.sh ammazza-aiutante"
	exit $? ;;

ritira-esiti)
	scp -q "$SERVER:$FUORI/02-pam-esiti.jsonl" "$QUI/02-pam-esiti.jsonl" \
		&& ok "outcomes collected in $QUI/02-pam-esiti.jsonl" \
		|| { ko "I did not collect the outcomes"; exit 2; }
	exit 0 ;;

*)
	sed -n '2,15p' "$0"
	exit 2 ;;
esac
