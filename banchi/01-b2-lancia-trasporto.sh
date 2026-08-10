#!/bin/bash
#
# 01-b2-lancia-trasporto.sh — gira SUL SERVER.  Le proprieta' di trasporto che
#                             restavano a B2, lette dal pari.
#
#   bash /media/REMOTIX/src/01-b2-lancia-trasporto.sh
#
# ---------------------------------------------------------------------------
# DUE GIRI, E IL SECONDO E' PER B3
#
#   1. il server com'e' (tetto d'inattivita' predefinito)  -> atteso 30 000 ms
#   2. il server con `--timeout=10s`                       -> atteso 10 000 ms
#
# ⛔ Il secondo giro non e' un doppione: `fasi/01-filo-nudo.md` chiede che il
#    banco **possa cambiare `max_idle_timeout`** (rilievo R3.19).  Senza,
#    quando B3 misurera' i suoi trenta secondi non potra' distinguere il tetto
#    del protocollo da quello del trasporto — e una prova che non distingue
#    due cause non e' una prova.
#
# ⭐ E si misura, non si legge dal `--help`: «l'opzione esiste» e «l'opzione
#    cambia quel che arriva al pari» sono due affermazioni diverse.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
IND=${1:-192.168.0.2}
PORTA=7447

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ⚠ L'etichetta passata alla sonda e' una parola sola, SENZA apostrofi: il
#   primo giro del 10 agosto le mandava una frase che conteneva «proprieta'»,
#   e l'apostrofo ha chiuso le virgolette attraverso le tre shell annidate —
#   «unexpected EOF while looking for matching quote».  E' la stessa famiglia
#   del difetto del 9 agosto: le righe di comando si mettono in un file, e i
#   valori che le attraversano si tengono semplici.
giro()
{
	# $1 = etichetta breve, $2 = tetto atteso in ms, $3.. = opzioni in piu'
	local ETICHETTA=$1 atteso=$2; shift 2
	local et="$ETICHETTA"
	log "$et"
	local chi
	chi=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")
	if [ -n "$chi" ]; then
		ko "la porta $PORTA e' occupata:"
		printf '%s\n' "$chi" | sed 's/^/        /'
		return 3
	fi
	rm -f "$FUORI/b2-tra.log" "$FUORI/b2-tra.pid"
	bash "$ENTRA" --root \
		"nohup env LD_LIBRARY_PATH=$LIBS $SERVER $* $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b2-tra.log 2>&1 & echo \$! > $DENTRO/b2-tra.pid"
	sleep 2
	local p=""
	[ -f "$FUORI/b2-tra.pid" ] && p=$(cat "$FUORI/b2-tra.pid")
	# ⚠ /proc e non `kill -0`: il server e' di root, questo script no.
	if [ -z "$p" ] || [ ! -d "/proc/$p" ]; then
		ko "il server non e' partito.  Il registro dice:"
		sed 's/^/        /' "$FUORI/b2-tra.log"
		return 4
	fi
	ok "in ascolto, PID $p   (opzioni: ${*:-nessuna})"
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-trasporto.py --indirizzo $IND --porta $PORTA --etichetta $ETICHETTA --idle-atteso $atteso"
	local e=$?
	bash "$ENTRA" --root "kill $p || true"
	rm -f "$FUORI/b2-tra.pid"
	sleep 1
	return "$e"
}

giro tetto-predefinito 30000
E1=$?
inf "primo giro: uscita $E1"

giro tetto-cambiato 10000 --timeout=10s
E2=$?
inf "secondo giro: uscita $E2"

log "Riepilogo"
inf "tetto predefinito (30 s): $([ "$E1" -eq 0 ] && echo 'tutti i controlli passano' || echo "qualcosa non passa (uscita $E1)")"
inf "tetto cambiato (10 s):    $([ "$E2" -eq 0 ] && echo 'tutti i controlli passano' || echo "qualcosa non passa (uscita $E2)")"
if [ "$E2" -eq 0 ]; then
	ok "⭐ il banco PUO' cambiare max_idle_timeout, e il pari lo vede: B3 potra'"
	ok "   distinguere il tetto del protocollo da quello del trasporto"
fi
[ "$E1" -eq 0 ] && [ "$E2" -eq 0 ]
exit $?
