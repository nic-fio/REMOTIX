#!/bin/bash
#
# 01-b2-lancia-impostazioni.sh — gira SUL SERVER.  Chiede alle due candidate,
#                                sul filo, se dichiarano WebTransport.
#
#   bash /media/REMOTIX/src/01-b2-lancia-impostazioni.sh
#
# ---------------------------------------------------------------------------
# ⛔ LA REGOLA NATA DALLE 333 RIGHE DI LSQUIC
#
# Si prova per prima **la cosa che puo' uccidere la candidata**, prima di
# scrivere il collante.  Per l'SNI e' costata una connessione e ha eliminato
# `lsquic`; qui la domanda e': **il server riesce a DICHIARARE WebTransport?**
# Senza quella dichiarazione un browser non apre la sessione, e non c'e' riga
# di codice nostro che rimedi — quel frame lo scrive la libreria.
#
# ⭐ E il controllo positivo e' `ngtcp2` col nostro strato innestato: li' le
#    due dichiarazioni CI SONO.  Se la sonda non le vedesse nemmeno li', il
#    verdetto non sarebbe sulle librerie: sarebbe sulla sonda.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
NGTCP2="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
QUICHE="$DENTRO/b2/quiche/quiche/examples/http3-server"
DIRQ="$CERT/quiche"
IND=${1:-192.168.0.2}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

porta_libera()
{
	local p=$1 chi
	chi=$(bash "$ENTRA" --root "ss -ulnp | grep ':$p '")
	if [ -n "$chi" ]; then
		ko "la porta $p e' gia' occupata:"
		printf '%s\n' "$chi" | sed 's/^/        /'
		return 1
	fi
	inf "porta $p libera"
	return 0
}

avvia()
{
	local et=$1; shift
	rm -f "$FUORI/b2-imp-$et.log" "$FUORI/b2-imp-$et.pid"
	bash "$ENTRA" --root \
		"nohup $* < /dev/null > $DENTRO/b2-imp-$et.log 2>&1 & echo \$! > $DENTRO/b2-imp-$et.pid"
	sleep 2
	local p=""
	[ -f "$FUORI/b2-imp-$et.pid" ] && p=$(cat "$FUORI/b2-imp-$et.pid")
	# ⚠ /proc e non `kill -0`: il server e' di root e questo script no.
	if [ -z "$p" ] || [ ! -d "/proc/$p" ]; then
		ko "$et non e' partito.  Il registro dice:"
		sed 's/^/        /' "$FUORI/b2-imp-$et.log"
		return 1
	fi
	local asc
	asc=$(bash "$ENTRA" --root "ss -ulnp | grep 'pid=$p,'")
	if [ -z "$asc" ]; then
		ko "$et e' vivo ma non tiene nessuna porta UDP"
		sed 's/^/        /' "$FUORI/b2-imp-$et.log"
		return 1
	fi
	ok "$et in ascolto, PID $p"
	return 0
}

ferma()
{
	local et=$1 p=""
	[ -f "$FUORI/b2-imp-$et.pid" ] && p=$(cat "$FUORI/b2-imp-$et.pid")
	[ -n "$p" ] && bash "$ENTRA" --root "kill $p || true"
	rm -f "$FUORI/b2-imp-$et.pid"
}

# ---------------------------------------------------------------------------
log "1. ⭐ ngtcp2 col nostro strato — IL CONTROLLO POSITIVO"
inf "atteso: DICHIARA.  Se non dichiarasse, la sonda non sa leggere un"
inf "        SETTINGS e nessun numero della gamba 2 varrebbe niente."
ferma bsslserver
porta_libera 7447 || exit 3
if avvia bsslserver "env LD_LIBRARY_PATH=$LIBS $NGTCP2 $IND 7447 $CERT/sessione.key $CERT/sessione.pem"; then
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-impostazioni.py --indirizzo $IND --porta 7447 --etichetta ngtcp2 --atteso si"
	ESITO_NG=$?
else
	ESITO_NG=4
fi
inf "sonda ngtcp2: uscita $ESITO_NG"
ferma bsslserver

# ---------------------------------------------------------------------------
log "2. quiche, con tutto quel che la sua API C permette"
inf "atteso: NON dichiara.  La previsione e' in 01-b2-quiche-wt-innesta.py,"
inf "        scritta dopo la lettura dell'FFI e PRIMA di questa esecuzione."
# ⚠ Il loro esempio legge ./cert.crt e ./cert.key dalla cartella corrente e
#   NON controlla di averli caricati: senza, parte lo stesso e fallisce ogni
#   stretta di mano.  Si mettono, e si controlla che ci siano.
PREP=$(bash "$ENTRA" --root "mkdir -p $DIRQ; cp -f $CERT/sessione.pem $DIRQ/cert.crt; cp -f $CERT/sessione.key $DIRQ/cert.key; ls $DIRQ")
case "$PREP" in
*cert.crt*) ;;
*) ko "cert.crt non e' finito in $DIRQ"; exit 3 ;;
esac
ferma http3-server
porta_libera 7449 || exit 3
if avvia http3-server "env -C $DIRQ $QUICHE $IND 7449"; then
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-impostazioni.py --indirizzo $IND --porta 7449 --etichetta quiche --atteso no"
	ESITO_QU=$?
else
	ESITO_QU=4
fi
inf "sonda quiche: uscita $ESITO_QU"
ferma http3-server

# ---------------------------------------------------------------------------
log "Riepilogo"
inf "ngtcp2 (controllo positivo): $([ "${ESITO_NG:-9}" -eq 0 ] && echo 'come atteso' || echo "NON come atteso (${ESITO_NG:-9})")"
inf "quiche:                      $([ "${ESITO_QU:-9}" -eq 0 ] && echo 'come atteso' || echo "NON come atteso (${ESITO_QU:-9})")"
if [ "${ESITO_NG:-9}" -ne 0 ]; then
	ko "⛔ il controllo positivo e' fallito: nessuna riga su §6.4 si scrive da qui"
	exit 5
fi
[ "${ESITO_QU:-9}" -eq 0 ]
exit $?
