#!/bin/bash
#
# 01-b5-lancia.sh — gira SUL SERVER.  B5: le prove di violazione.
#
#   bash /media/REMOTIX/src/01-b5-lancia.sh              tutto
#   bash /media/REMOTIX/src/01-b5-lancia.sh solo tela    un pezzo solo
#   bash /media/REMOTIX/src/01-b5-lancia.sh elenco       le previsioni, senza misurare
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA PROVA, E LA META' CHE SI DIMENTICA
#
# `RCP.md` §3 e' la regola di rigore: quel che non si capisce non si ignora, la
# connessione cade, col motivo.  ⭐ Ma **una regola di rigore non si prova
# facendo le cose giuste**: un server che non controlla niente passa tutti i
# giri di B3 e cade il giorno in cui qualcuno gli manda un byte storto.
#
# ⛔ E dopo ogni violazione si controlla che **il server sia ancora li'**
#    (B0.5).  Un server ucciso dal nucleo «fa cadere la connessione» esattamente
#    come uno che congeda — e si porta via **le sessioni di tutti gli altri**.
#
# ---------------------------------------------------------------------------
# ⛔ E IL REGISTRO DEL SERVER SI GUARDA, MA NON E' L'ARBITRO
#
# Il motivo lo verifica **il lato che riceve** (§8.1): il registro del server e'
# la stessa mano che ha scritto il codice.  ⚠ Due cose pero' esistono SOLO nel
# registro, perche' §4.3 le impone li': la **scelta del codec** e lo **scarto**
# delle voci sconosciute.  Quelle si leggono di la', ed e' dichiarato.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
IND=192.168.0.2
PORTA=7447

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-tutto}
FILTRO=${2:-}

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b5-violazioni.py --elenco"
	exit 0
fi

# ---------------------------------------------------------------------------
log "1. Il server si ricostruisce — rcp.c e' cambiato"
inf "⛔ gli innesti si TOLGONO e si rimettono: applicarne uno sopra l'altro"
inf "   lascerebbe due copie dello stesso codice, e la seconda non si vede"
# ⚠ Nessuna redirezione attorno a enter.sh — vedi il riquadro piu' sotto.
bash "$ENTRA" --root "python3 $DENTRO/01-b3-rcp-innesta.py --togli > /dev/null"
bash "$ENTRA" --root "python3 $DENTRO/01-b2-ngtcp2-wt-innesta.py --togli > /dev/null"
bash "$ENTRA" --root "python3 $DENTRO/01-b2-ngtcp2-wt-innesta.py" \
	| grep -E "appiglio|righe|CODICE" | sed 's/^/        /'
bash "$ENTRA" --root "python3 $DENTRO/01-b3-rcp-innesta.py" \
	| grep -E "appiglio|NO |file nostri" | sed 's/^/        /'
# ⛔ Un innesto che non trova un appiglio stampa «NO» e VA AVANTI: senza questo
#    controllo si compilerebbe un server a cui manca un pezzo, e il banco
#    darebbe rosso su una regola che il server non ha mai avuto occasione di
#    applicare.
SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
QUANTI=$(bash "$ENTRA" --root "grep -c 'REMOTIX B5' $SORG" | tr -cd '0-9')
if [ "${QUANTI:-0}" -ge 3 ]; then
	ok "l'innesto di B5 e' nel sorgente ($QUANTI righe)"
else
	ko "⛔ l'innesto di B5 NON e' nel sorgente (righe: ${QUANTI:-0})"
	ko "   si compilerebbe un server a cui manca il controllo degli stream,"
	ko "   e il rosso finirebbe su una regola mai applicata"
	exit 3
fi

# ⛔ LA REDIREZIONE STA DENTRO IL CONTENITORE, NON FUORI.
#
#    `bash enter.sh --root "..." > file 2>&1` si porta via **la richiesta di
#    password di sudo**, e lo script resta ad aspettare una domanda che nessuno
#    vede: nessun figlio, nessun compilatore, un registro vuoto e un processo
#    fermo per sempre.  ⚠ E' successo di nuovo il 10 agosto 2026 su questo
#    stesso file, quattro giri dopo che la lezione era stata scritta — la
#    trappola non e' `>/dev/null`, e' **qualunque redirezione attorno a
#    enter.sh**.
#
# ⭐ Dentro le virgolette la redirezione e' del comando remoto, e la richiesta
#    di password resta sul filo dove qualcuno la vede.
if ! bash "$ENTRA" --root \
	"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b5-compila.log 2>&1"; then
	ko "la compilazione e' fallita:"
	tail -25 "$FUORI/b5-compila.log" | sed 's/^/        /'
	exit 3
fi
ok "compilato"

# ---------------------------------------------------------------------------
log "2. La porta"
CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")
if [ -n "$CHI" ]; then
	ko "la porta $PORTA e' gia' occupata:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "fermalo per PID (mai con pkill -f) e rilancia"
	exit 3
fi
ok "porta $PORTA libera"

# ---------------------------------------------------------------------------
log "3. Il server si accende"
rm -f "$FUORI/b5-server.log" "$FUORI/b5-server.pid"
# ⚠ `--timeout=120s`: alcuni casi aspettano fino a dodici secondi per essere
#   sicuri che il congedo NON arrivi, e il tetto d'inattivita' predefinito
#   chiuderebbe la connessione per conto suo — il banco leggerebbe «e' caduta»
#   dove non e' caduto niente.  E' lo stesso ragionamento di R3.19.
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b5-server.log 2>&1 & echo \$! > $DENTRO/b5-server.pid"
sleep 2
PID=$(cat "$FUORI/b5-server.pid" 2>/dev/null)
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server non e' partito.  Il registro dice:"
	sed 's/^/        /' "$FUORI/b5-server.log"
	exit 4
fi
ok "in ascolto, PID $PID"

fermare() { bash "$ENTRA" --root "kill $PID 2>/dev/null || true"; rm -f "$FUORI/b5-server.pid"; }

# ---------------------------------------------------------------------------
log "4. Le violazioni"
if [ -n "$FILTRO" ]; then
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b5-violazioni.py --indirizzo $IND --porta $PORTA --solo $FILTRO"
else
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b5-violazioni.py --indirizzo $IND --porta $PORTA"
fi
ESITO=$?

# ---------------------------------------------------------------------------
log "5. ⛔ Il server e' ancora vivo? — B0.5, dal di fuori"
inf "il banco lo chiede a ogni caso; questo lo chiede al SISTEMA, che e' un"
inf "testimone diverso: un processo puo' rispondere e avere gia' perso i figli"
if [ -d "/proc/$PID" ]; then
	ok "il processo $PID c'e' ancora"
else
	ko "⛔ IL SERVER E' MORTO durante il banco"
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "6. Le due righe che vivono solo nel registro (§4.3)"
inf "la SCELTA del codec, e lo SCARTO delle voci sconosciute"
if grep -q "negoziato video.codec=hevc" "$FUORI/b5-server.log"; then
	ok "la scelta e' scritta:"
	grep -m2 "negoziato video.codec" "$FUORI/b5-server.log" | sed 's/^/        /'
else
	ko "⛔ la scelta del codec NON e' nel registro: §4.3 la impone"
	ESITO=1
fi
if grep -q "scartate voci sconosciute" "$FUORI/b5-server.log"; then
	ok "e lo scarto anche:"
	grep -m2 "scartate voci sconosciute" "$FUORI/b5-server.log" | sed 's/^/        /'
else
	ko "⛔ lo scarto di vp9 NON e' nel registro: una negoziazione riuscita"
	ko "   con dentro il contrario di quel che si voleva si vede solo se"
	ko "   qualcuno la scrive (trappola 4 di LEZIONI.md §4)"
	ESITO=1
fi

log "7. E che cosa ha scritto il server, in breve"
grep -c "REMOTIX B3\|REMOTIX B5" "$FUORI/b5-server.log" \
	| sed 's/^/        righe di registro: /'
grep "congedo motivo" "$FUORI/b5-server.log" | tail -5 | sed 's/^/        /'

fermare

log "Esito"
if [ "$ESITO" -eq 0 ]; then
	ok "⭐ B5 passa"
else
	ko "⛔ B5: qualcosa non passa"
fi
inf "il registro completo resta in $FUORI/b5-server.log"
exit "$ESITO"
