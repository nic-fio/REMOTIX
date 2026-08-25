#!/bin/bash
#
# 01-s1b-sito.sh — accende e spegne il sito di S1b.  ⚠ GIRA SUL SERVER.
#
#   bash 01-s1b-sito.sh accendi <indirizzo> <porta> <cartella-certificato>
#   bash 01-s1b-sito.sh spegni
#
# ---------------------------------------------------------------------------
# ⛔ IL CERTIFICATO SI GENERA UNA VOLTA SOLA, E QUESTO E' IL PUNTO
#
# L'eccezione che Chrome concede e' indicizzata sulla coppia (impronta del
# certificato, codice d'errore) `[R]` — `stateful_ssl_host_state_delegate.cc`.
# Rigenerare il certificato durante i sette giorni fa ricomparire l'avviso
# **subito**, e chi legge scrive «l'eccezione e' durata quattro giorni»: e'
# il rilievo R3.15, ed e' l'unico modo in cui questa misura puo' mentire senza
# che nessuno se ne accorga.
#
# Quindi: se il file c'e', NON si tocca.  E lo si dice, invece di rifarlo in
# silenzio.
#
# ⚠ E vive in una cartella SUA (`/media/REMOTIX/s1b-certificato`), non insieme
#   ai certificati di B2: quelli li rigenera `01-b2-certificati.sh` ogni volta
#   che qualcuno lancia il banco della libreria, cioe' anche tre volte al
#   giorno.  Condividere la cartella sarebbe stato condividere l'azzeramento.
#
# ---------------------------------------------------------------------------
# I VINCOLI DEL CERTIFICATO
#
#   durata   3650 giorni.  S1 §4.1: il certificato della PAGINA e' longevo e
#            stabile; e uno che scadesse dentro la finestra di misura farebbe
#            ricomparire l'avviso per scadenza invece che per l'eccezione.
#   nome     ⛔ `subjectAltName = IP:<indirizzo>`, non `DNS:`.  S1 §4.1 lo
#            mette fra i controlli che «evitano mezza giornata persa»: con
#            `DNS:192.168.0.2` il browser mostra un avviso DIVERSO, e alcuni
#            non offrono nemmeno il clic per proseguire — cioe' si
#            misurerebbe un altro errore.
#   chiave   ECDSA P-256, come tutto il resto del progetto (`RCP.md` §4.1).
# ---------------------------------------------------------------------------
set -uo pipefail

AZIONE=${1:-stato}
IND=${2:-192.168.0.2}
PORTA=${3:-7452}
DIR=${4:-/media/REMOTIX/s1b-certificato}
SRC=$(cd "$(dirname "$0")" && pwd)
PIDFILE=/tmp/01-s1b-sito.pid

case "$AZIONE" in
accendi)
	mkdir -p "$DIR" || exit 2
	if [ -f "$DIR/s1b-pagina.pem" ]; then
		echo "certificato GIA' presente: non lo tocco (e' quel che tiene in piedi la misura)"
	else
		echo "certificato assente: lo creo adesso, e questa e' l'unica volta"
		openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
			-keyout "$DIR/s1b-pagina.key" -out "$DIR/s1b-pagina.pem" \
			-days 3650 -nodes -subj "/CN=$IND" \
			-addext "subjectAltName=IP:$IND" >/dev/null 2>&1 || {
				echo "⛔ generazione fallita"; exit 3; }
		chmod 600 "$DIR/s1b-pagina.key"
	fi

	# ⛔ Il SAN si VERIFICA, non si spera: `-addext` viene ignorato in silenzio
	#    da certe versioni di openssl, e il sintomo sarebbe un avviso di tipo
	#    diverso — cioe' un'altra misura con lo stesso aspetto.
	if openssl x509 -in "$DIR/s1b-pagina.pem" -noout -text 2>/dev/null \
	   | grep -F "IP Address:$IND" >/dev/null; then
		echo "SAN verificato: IP Address:$IND"
	else
		echo "⛔ il SAN NON contiene «IP Address:$IND»:"
		openssl x509 -in "$DIR/s1b-pagina.pem" -noout -text 2>/dev/null \
		    | grep -A1 "Subject Alternative Name"
		exit 3
	fi
	echo -n "scade il: "
	openssl x509 -in "$DIR/s1b-pagina.pem" -noout -enddate 2>/dev/null

	if [ -f "$PIDFILE" ] && [ -d "/proc/$(cat "$PIDFILE")" ]; then
		echo "il sito e' gia' acceso (PID $(cat "$PIDFILE"))"
	else
		setsid nohup python3 -u "$SRC/01-s1b-servi.py" "$PORTA" "$DIR" \
			>/tmp/01-s1b-sito.log 2>&1 &
		echo $! >"$PIDFILE"
		sleep 2
	fi
	if [ ! -d "/proc/$(cat "$PIDFILE")" ]; then
		echo "⛔ il sito non e' partito:"
		tail -n 15 /tmp/01-s1b-sito.log
		exit 4
	fi
	echo "sito acceso su :$PORTA (PID $(cat "$PIDFILE"))"
	;;
spegni)
	if [ -f "$PIDFILE" ]; then
		# ⛔ Si uccide il PID che abbiamo scritto noi, mai `pkill -f`: quello
		#    prende per nome, e per nome si prendono anche i programmi di
		#    qualcun altro.
		kill "$(cat "$PIDFILE")" 2>/dev/null
		rm -f "$PIDFILE"
		echo "sito spento"
	else
		echo "nessun sito da spegnere"
	fi
	;;
stato)
	if [ -f "$PIDFILE" ] && [ -d "/proc/$(cat "$PIDFILE")" ]; then
		echo "acceso, PID $(cat "$PIDFILE")"
	else
		echo "spento"
	fi
	;;
*) echo "uso: $0 {accendi|spegni|stato}" >&2; exit 2 ;;
esac
