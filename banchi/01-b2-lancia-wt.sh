#!/bin/bash
#
# 01-b2-lancia-wt.sh — gira SUL SERVER, e misura il server minimo di B2.
#
#   bash /media/REMOTIX/src/01-b2-lancia-wt.sh
#
# ---------------------------------------------------------------------------
# CHE COSA MISURA
#
# `fasi/01-filo-nudo.md`, gruppo 2: **una sessione WebTransport su `/rcp/1`,
# e un byte che torna**.  Qui la si prova senza browser, col cliente di prova
# — che e' necessario e NON sufficiente (`LEZIONI.md`: e' E10, la prova verde
# sul client sbagliato).  Il browser viene dopo, e con la pagina.
#
# ⛔ E CON IL CONTROLLO CHE DICE NO, che nelle due revisioni del 9 agosto
#    cadeva ogni volta: `RCP.md` §2.2 impone che il server **NON DEVE**
#    accettare una sessione su un percorso diverso, e che il rifiuto sia
#    **404** (rilievo R1.24).  Un banco che prova solo il percorso giusto non
#    distingue «il server controlla il percorso» da «il server accetta
#    qualunque cosa».
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⚠ Tre azioni, e servono perche' la misura col BROWSER ha bisogno che il
#   server resti in piedi mentre la conduce un altro script, sull'altra
#   macchina.  «misura» accende, prova col cliente di prova e spegne.
AZIONE=${1:-misura}
IND=${2:-192.168.0.2}
PORTA=${3:-7447}
# ⚠ Le opzioni in piu' del server: servono a B3, che alza `max_idle_timeout` a
#   120 s per distinguere «il server sa che una sessione e' staccata» da «QUIC
#   ha chiuso da se'» (rilievo R3.19).
# ⛔ `shift 3` con MENO di tre argomenti non sposta niente e non fallisce in
#    modo utile: `$*` restava «accendi», il server riceveva il nome
#    dell'azione come opzione e moriva con «port: invalid port number».
#    Visto il 10 agosto 2026 — e il sintomo era un cliente che «non si
#    collega», cioe' il rosso di nuovo sull'imputato sbagliato.
if [ $# -gt 3 ]; then
	shift 3
	OPZIONI="$*"
else
	OPZIONI=""
fi

if [ "$AZIONE" = spegni ]; then
	P=$(cat /media/REMOTIX/src/b2-wt.pid 2>/dev/null)
	if [ -n "$P" ]; then
		bash "$ENTRA" --root "kill $P || true"
		rm -f /media/REMOTIX/src/b2-wt.pid
		printf '    --  fermato il server (PID %s)\n' "$P"
	else
		printf '    --  nessun server da fermare\n'
	fi
	exit 0
fi
if [ "$AZIONE" != misura ] && [ "$AZIONE" != accendi ]; then
	ko "azione sconosciuta: $AZIONE  (misura | accendi | spegni)"
	exit 2
fi

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ---------------------------------------------------------------------------
log "La porta"
CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")
if [ -n "$CHI" ]; then
	ko "la porta $PORTA e' gia' occupata:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "fermalo per PID (mai con pkill -f) e rilancia"
	exit 3
fi
ok "porta $PORTA libera"

# ---------------------------------------------------------------------------
log "Il server minimo (l'esempio di ngtcp2 con lo strato WebTransport innestato)"
rm -f "$FUORI/b2-wt.log" "$FUORI/b2-wt.pid"
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER $OPZIONI $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b2-wt.log 2>&1 & echo \$! > $DENTRO/b2-wt.pid"
sleep 2
PID=$(cat "$FUORI/b2-wt.pid" 2>/dev/null)
# ⛔ `/proc`, non `kill -0`: il server e' di root e questo script no — e da
#    utente normale `kill -0` risponde «operazione non permessa», cioe' un
#    errore, non «non esiste» (10 agosto 2026).
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server non e' partito.  Il registro dice:"
	sed 's/^/        /' "$FUORI/b2-wt.log"
	exit 4
fi
ASC=$(bash "$ENTRA" --root "ss -ulnp | grep 'pid=$PID,'")
if [ -z "$ASC" ]; then
	ko "il server e' vivo ma non tiene nessuna porta UDP:"
	sed 's/^/        /' "$FUORI/b2-wt.log"
	exit 4
fi
ok "in ascolto, PID $PID"
printf '%s\n' "$ASC" | sed 's/^/        /'
inf "quel che ha detto all'avvio:"
grep "REMOTIX B2" "$FUORI/b2-wt.log" | head -4 | sed 's/^/        /'

fermare() {
	bash "$ENTRA" --root "kill $PID || true"
	rm -f "$FUORI/b2-wt.pid"
}

if [ "$AZIONE" = accendi ]; then
	ok "il server resta acceso: fermalo con «01-b2-lancia-wt.sh spegni»"
	inf "l'impronta del certificato della sessione, per la pagina:"
	bash "$ENTRA" --root \
		"openssl x509 -in $CERT/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0" \
		| tail -1 | sed 's/^/        /'
	exit 0
fi

# ---------------------------------------------------------------------------
log "1. Il percorso GIUSTO — /rcp/1"
inf "atteso: :status 200, e i byte tornano identici"
bash "$ENTRA" --root \
	"python3 $DENTRO/01-b2-cliente-aioquic.py https://$IND:$PORTA/rcp/1"
ESITO_SI=$?
inf "cliente di prova: uscita $ESITO_SI"

# ---------------------------------------------------------------------------
log "2. ⛔ Il percorso SBAGLIATO — /rcp/9, il controllo che dice NO"
inf "atteso: NON 200.  RCP.md §2.2: un percorso sconosciuto si rifiuta, e"
inf "        il rilievo R1.24 ha scelto 404 fra i tre stati che erano leciti."
bash "$ENTRA" --root \
	"python3 $DENTRO/01-b2-cliente-aioquic.py https://$IND:$PORTA/rcp/9"
ESITO_NO=$?
inf "cliente di prova: uscita $ESITO_NO (atteso: DIVERSA da 0)"

# ---------------------------------------------------------------------------
log "Che cosa ha visto il server"
grep "REMOTIX B2" "$FUORI/b2-wt.log" | sed 's/^/        /'

fermare

log "Esito"
BENE=0
if [ "$ESITO_SI" -eq 0 ]; then
	ok "/rcp/1: sessione aperta e byte tornati"
else
	ko "/rcp/1: NON ha funzionato (uscita $ESITO_SI)"
	BENE=1
fi
if [ "$ESITO_NO" -ne 0 ]; then
	ok "/rcp/9: RIFIUTATO, come impone §2.2"
else
	ko "⛔ /rcp/9 e' stato ACCETTATO: il server non controlla il percorso."
	ko "   E' una violazione di RCP.md §2.2, non un dettaglio del banco."
	BENE=1
fi
inf "il registro completo resta in $FUORI/b2-wt.log"
exit "$BENE"
