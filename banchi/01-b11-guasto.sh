#!/bin/bash
#
# 01-b11-guasto.sh — gira SUL SERVER.  Accende e spegne il server GUASTO di B11.
#
#   bash /media/REMOTIX/src/01-b11-guasto.sh accendi
#   bash /media/REMOTIX/src/01-b11-guasto.sh registro
#   bash /media/REMOTIX/src/01-b11-guasto.sh spegni     ⛔ e RIMETTE il server sano
#
# ---------------------------------------------------------------------------
# ⛔ «SPEGNI» NON E' SOLO SPEGNERE
#
# I guasti di B11 sono righe che fanno **mentire il server**.  Un interruttore
# cosi', se sopravvive alla fase, un giorno lo trova acceso qualcuno che non
# sapeva esistesse — e il sintomo sarebbe «il server dichiara una versione che
# non parla», due mesi dopo, senza che niente lo colleghi a un banco.
#
# ⭐ Per questo `spegni` ferma il processo **e ricostruisce il server sano**, e
#    lo verifica: se dopo `spegni` la marca `REMOTIX B11` e' ancora nel
#    sorgente, questo script lo dice a voce alta.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
IND=192.168.0.2
PORTA=7447

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-accendi}

# ⛔ Nessuna redirezione ATTORNO a enter.sh: si porterebbe via la richiesta di
#    password di sudo, e lo script resterebbe fermo su una domanda che nessuno
#    vede.  Dentro le virgolette invece e' del comando remoto.
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }

ricostruisci() # $1 = "con-guasti" | "sano"
{
	bash "$ENTRA" --root "python3 $DENTRO/01-b3-rcp-innesta.py --togli > /dev/null"
	bash "$ENTRA" --root "python3 $DENTRO/01-b2-ngtcp2-wt-innesta.py --togli > /dev/null"
	bash "$ENTRA" --root "python3 $DENTRO/01-b2-ngtcp2-wt-innesta.py > /dev/null"
	bash "$ENTRA" --root "python3 $DENTRO/01-b3-rcp-innesta.py > /dev/null"
	if [ "$1" = con-guasti ]; then
		bash "$ENTRA" --root "python3 $DENTRO/01-b11-guasto-innesta.py" \
			| sed 's/^/        /'
	fi
	# ⛔ E SI RESTITUISCE L'ESITO DI NINJA.
	#
	#    Il primo giro del 10 agosto 2026 non lo guardava: si limitava a
	#    controllare che `bsslserver` **esistesse ed fosse eseguibile**.  La
	#    compilazione era fallita, il binario di due ore prima era ancora li',
	#    e il banco ha acceso **il server SANO dichiarando di aver acceso quello
	#    guasto**.  ⚠ Tutti e dodici i casi di B11 sarebbero falliti, e il rosso
	#    sarebbe finito sulla PAGINA — che non c'entrava niente.
	#
	# ⭐ «Il file c'e'» e «il file e' quello che ho appena costruito» sono due
	#    domande diverse, e solo la seconda ha un denominatore.
	bash "$ENTRA" --root \
		"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b11-compila.log 2>&1"
}

case "$AZIONE" in
registro)
	# ⛔ Il registro del server e' il SECONDO TESTIMONE di B11: due delle
	#    dodici righe sono proprieta' NEGATIVE della pagina — «dopo RESPINTO
	#    non riprova», «nessun battito applicativo» — e una proprieta'
	#    negativa non si vede da dentro la pagina.
	grep -E "B11|DOPO la fine|congedo motivo|canale di controllo aperto" \
		"$FUORI/b11-server.log" 2>/dev/null | tail -60
	exit 0
	;;
spegni)
	P=$(cat "$FUORI/b11-server.pid" 2>/dev/null)
	[ -n "$P" ] && bash "$ENTRA" --root "kill $P 2>/dev/null || true"
	rm -f "$FUORI/b11-server.pid"
	log "⛔ Si rimette il server SANO"
	ricostruisci sano
	QUANTI=$(bash "$ENTRA" --root "grep -c 'REMOTIX B11 GUASTO' $SORG || true" | tr -cd '0-9')
	if [ "${QUANTI:-0}" -eq 0 ]; then
		ok "⭐ nessuna traccia di B11 nel sorgente: il server e' quello vero"
	else
		ko "⛔ RESTANO $QUANTI righe di B11 nel sorgente."
		ko "   Un server che mente di proposito NON deve sopravvivere alla fase."
		exit 5
	fi
	exit 0
	;;
accendi) ;;
*) ko "azione sconosciuta: $AZIONE  (accendi | registro | spegni)"; exit 2 ;;
esac

# ---------------------------------------------------------------------------
log "1. La porta"
CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")
if [ -n "$CHI" ]; then
	ko "la porta $PORTA e' occupata:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	exit 3
fi
ok "porta $PORTA libera"

log "2. Il server guasto si costruisce"
if ! ricostruisci con-guasti; then
	ko "⛔ la compilazione e' FALLITA.  Il registro dice:"
	bash "$ENTRA" --root "grep -m6 -n error $DENTRO/b11-compila.log" | sed 's/^/        /'
	ko "   e NON si accende niente: il binario vecchio e' ancora sul disco, e"
	ko "   accenderlo vorrebbe dire misurare un server SANO credendolo guasto"
	exit 4
fi
QUANTI=$(bash "$ENTRA" --root "grep -c 'REMOTIX B11 GUASTO' $SORG || true" | tr -cd '0-9')
if [ "${QUANTI:-0}" -lt 1 ]; then
	ko "⛔ i guasti NON sono nel sorgente: il banco misurerebbe un server sano"
	ko "   e tutti e dodici i casi fallirebbero per la ragione sbagliata"
	exit 4
fi
ok "costruito, e i guasti ci sono"

log "3. Si accende"
rm -f "$FUORI/b11-server.log" "$FUORI/b11-server.pid"
# ⚠ `--timeout=120s`: il caso «silenzio» tace otto secondi per provare che la
#   pagina non manda un battito applicativo (§2.2).  Col tetto predefinito a
#   30 s la connessione reggerebbe lo stesso, ma i dodici casi in fila su una
#   sola pagina no.
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b11-server.log 2>&1 & echo \$! > $DENTRO/b11-server.pid"
sleep 2
PID=$(cat "$FUORI/b11-server.pid" 2>/dev/null)
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server guasto non e' partito:"
	sed 's/^/        /' "$FUORI/b11-server.log"
	exit 4
fi
ok "server GUASTO in ascolto, PID $PID"
inf "⛔ e' un server che mente di proposito: si spegne con «spegni», che"
inf "   rimette anche il sorgente sano"
inf "l'impronta del certificato della sessione, per la pagina:"
bash "$ENTRA" --root \
	"openssl x509 -in $CERT/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0" \
	| tail -1 | sed 's/^/        /'
exit 0
