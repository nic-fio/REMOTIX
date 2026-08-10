#!/bin/bash
#
# 01-b7-lancia.sh — gira SUL SERVER.  B7: il congedo, dal lato che riceve.
#
#   bash /media/REMOTIX/src/01-b7-lancia.sh                  tutto
#   bash /media/REMOTIX/src/01-b7-lancia.sh solo tempo       un caso solo
#   bash /media/REMOTIX/src/01-b7-lancia.sh elenco           le previsioni, senza misurare
#   bash /media/REMOTIX/src/01-b7-lancia.sh frasi            e stampa tutte le frasi di §8.2
#
# ⛔ CON UN FILTRO IL GIRO E' PARZIALE, E LO DICE.  L'esito verde si legge «i
#    casi selezionati passano», mai «B7 passa».  ⚠ E un filtro che non combacia
#    con nessun nome esce **2**, non 0: «non ho niente da misurare» non e'
#    «tutto passato».
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA PROVA
#
# `RCP.md` §8.1: *«il congedo si verifica dal lato che lo riceve, mai dal
# registro di chi lo manda»*.  In v1, per **tre fasi**, il server scriveva
# «congedo il client» mentre il client scriveva «errore di rete»
# (`LEZIONI.md` §1.7).
#
# ⛔ E le strade sono DUE (§3.1): il `CONGEDO` sul canale di controllo **e** il
#    codice del motivo nella chiusura della sessione WebTransport.  Si contano
#    **separatamente**, con due denominatori, perche' il 10 agosto 2026 la
#    seconda mancava in **quattordici casi su trentasei** e nessun banco se
#    n'era accorto: bastava che arrivasse la prima.
#
# ⛔ Il guasto di `fasi/01-filo-nudo.md` §C1 — «si toglie la spedizione del
#    `CONGEDO` e si lascia il codice nella chiusura» — deve far diventare
#    ROSSO questo banco.  Se resta verde sta facendo una `||` dove serve una
#    `&&`.
#
# ---------------------------------------------------------------------------
# ⛔ E IL REGISTRO DEL SERVER SI LEGGE IN DUE PUNTI SOLI, DICHIARATI
#
#   · §3.1 **punto 1** — la riga «che cosa non ho capito», che e' per
#     definizione una riga di chi chiude: e' il punto 1 a chiederla;
#   · il verso **client→server** — dove chi riceve E' il server.
#
# Il motivo che il server MANDA lo giudicano sempre e solo le due strade, lette
# sul filo dal cliente di prova.
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
UTENTE=prova
PAROLA=parola-di-prova

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
	bash "$ENTRA" --root "python3 $DENTRO/01-b7-congedo.py --elenco"
	exit $?
fi

FRASI=
[ "$AZIONE" = frasi ] && FRASI=--frasi

# ---------------------------------------------------------------------------
log "1. Il server si ricostruisce — rcp.c puo' essere cambiato"
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
#    controllo si compilerebbe un server a cui manca il pezzo che B7 misura, e
#    il banco darebbe rosso su una regola che il server non ha mai avuto
#    occasione di applicare.
SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
QUANTI=$(bash "$ENTRA" --root "grep -c 'REMOTIX B3' $SORG" | tr -cd '0-9')
if [ "${QUANTI:-0}" -ge 3 ]; then
	ok "lo strato RCP e' nel sorgente ($QUANTI righe «REMOTIX B3»)"
else
	ko "⛔ lo strato RCP NON e' nel sorgente (righe: ${QUANTI:-0})"
	ko "   si compilerebbe un server senza il congedo, e il rosso finirebbe"
	ko "   su una regola mai applicata"
	exit 3
fi

# ⛔ E LA CHIUSURA RIMANDATA DEV'ESSERCI, perche' e' precisamente la cura del
#    difetto che B7 esiste per sorvegliare: senza il keep-alive armato in
#    `wt_chiudi_sessione`, la capsula di chiusura non parte su nessuna
#    violazione trovata al primo messaggio — 14 casi su 36, il 10 agosto 2026.
#    ⚠ Trovarlo assente non e' un rosso di B7: e' il banco che dice «stai per
#      misurare un server diverso da quello che credi».
RIMANDO=$(bash "$ENTRA" --root "grep -c 'RIMANDATA' $SORG" | tr -cd '0-9')
if [ "${RIMANDO:-0}" -ge 1 ]; then
	ok "la chiusura rimandata (§3.1 punto 3) e' innestata"
else
	ko "⚠ la chiusura RIMANDATA non c'e' nel sorgente: se la seconda strada"
	ko "  risultera' assente, la causa e' QUESTA e non il modulo RCP"
fi

# ⛔ LA REDIREZIONE STA DENTRO IL CONTENITORE, NON FUORI.
#
#    `bash enter.sh --root "..." > file 2>&1` si porta via **la richiesta di
#    password di sudo**, e lo script resta ad aspettare una domanda che nessuno
#    vede: nessun figlio, nessun compilatore, un registro vuoto e un processo
#    fermo per sempre.  ⚠ La trappola non e' `>/dev/null`: e' **qualunque
#    redirezione attorno a enter.sh**.
#
# ⛔ E IL REGISTRO DI COMPILAZIONE SI CANCELLA **PRIMA**, non dopo: se la
#    compilazione fallisce prima di scriverlo, il `tail` mostrerebbe il registro
#    del giro PRECEDENTE e la diagnosi partirebbe da un errore che oggi non e'
#    successo — «vecchio» e «assente» hanno lo stesso aspetto.
rm -f "$FUORI/b7-compila.log"
if ! bash "$ENTRA" --root \
	"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b7-compila.log 2>&1"; then
	ko "la compilazione e' fallita:"
	if [ -f "$FUORI/b7-compila.log" ]; then
		tail -25 "$FUORI/b7-compila.log" | sed 's/^/        /'
	else
		ko "   ⛔ e il registro di compilazione NON ESISTE: non e' ninja che"
		ko "      ha taciuto, e' che non si e' arrivati a lanciarlo"
	fi
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
# ⛔ IL REGISTRO SI CANCELLA PRIMA, e qui vale doppio: B7 **legge questo file**
#    per §3.1 punto 1 e per il verso client→server.  Un registro del giro
#    precedente contiene i congedi di ieri, con gli stessi motivi — e ogni caso
#    troverebbe la sua riga senza che il server abbia scritto niente oggi.
#    ⚠ Il banco si difende da solo con i marcatori di posizione, ma un file
#      vecchio non deve nemmeno esistere.
rm -f "$FUORI/b7-server.log" "$FUORI/b7-server.pid"
# ⚠ `--timeout=120s`: il caso `tempo-scaduto` sta zitto per venti secondi, e il
#   tetto d'inattivita' predefinito (30 s) chiuderebbe la connessione per conto
#   suo — il banco leggerebbe «e' caduta» dove non e' caduto niente, e per
#   giunta **senza motivo**, cioe' proprio la forma che B7 deve saper
#   distinguere da un congedo.
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b7-server.log 2>&1 & echo \$! > $DENTRO/b7-server.pid"
sleep 2
PID=$(cat "$FUORI/b7-server.pid" 2>/dev/null)
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server non e' partito.  Il registro dice:"
	sed 's/^/        /' "$FUORI/b7-server.log"
	exit 4
fi
ok "in ascolto, PID $PID"

fermare() { bash "$ENTRA" --root "kill $PID 2>/dev/null || true"; rm -f "$FUORI/b7-server.pid"; }

# ---------------------------------------------------------------------------
log "4. Il congedo, dal lato che riceve"
if [ -n "$FILTRO" ]; then
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registro $DENTRO/b7-server.log --pagina $DENTRO/01-b11-pagina.html --sorgente $DENTRO/rcp/rcp.c --solo $FILTRO"
else
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registro $DENTRO/b7-server.log --pagina $DENTRO/01-b11-pagina.html --sorgente $DENTRO/rcp/rcp.c $FRASI"
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
log "6. Le due strade, come le ha scritte il server"
inf "⚠ QUESTO NON E' IL VERDETTO — il verdetto e' quello del punto 4, letto dal"
inf "  lato che riceve (§8.1).  Qui si guarda l'altra meta' della stessa storia:"
inf "  se le due colonne non si somigliano, il registro e il filo raccontano due"
inf "  cose diverse, ed e' la forma di difetto che §3.1 punto 3 esiste per"
inf "  smascherare"
if [ -f "$FUORI/b7-server.log" ]; then
	# ⛔ Si conta e si stampa: un `grep -c` che dice 0 e un file che non si
	#    legge sono due fatti diversi, e il ramo qui sotto li tiene separati.
	C1=$(grep -c "congedo motivo=" "$FUORI/b7-server.log")
	C2=$(grep -c "chiusa la sessione WebTransport" "$FUORI/b7-server.log")
	C3=$(grep -c "chiusura della sessione RIMANDATA" "$FUORI/b7-server.log")
	inf "congedi spediti (§3.1 punto 2, dal lato di chi manda): ${C1:-0}"
	inf "chiusure di sessione USCITE (§3.1 punto 3):             ${C2:-0}"
	inf "chiusure soltanto RIMANDATE:                            ${C3:-0}"
	if [ "${C3:-0}" -gt "${C2:-0}" ]; then
		ko "⛔ ${C3} chiusure rimandate e solo ${C2} uscite: qualche capsula"
		ko "   non e' mai partita — e' il difetto delle 14 su 36 del 10 agosto"
	fi
	grep "congedo motivo=" "$FUORI/b7-server.log" | tail -8 | sed 's/^/        /'
else
	ko "⛔ IL REGISTRO NON SI LEGGE: $FUORI/b7-server.log non esiste"
	ko "   non e' il server che non ha scritto — e' che non si legge"
	ko "   (volume non mappato? server mai partito? nome cambiato?)"
	ESITO=1
fi

fermare

log "Esito"
# ⛔ QUATTRO ESITI, NON DUE.  `01-b7-congedo.py` esce 2 quando il filtro non ha
#    selezionato niente, e 3 quando lo STRUMENTO non si e' certificato: un
#    banco non certificato non e' un rosso del server, ed e' l'unico modo di
#    non far passare per difetto del prodotto un difetto del banco.
case "$ESITO" in
0)
	if [ -n "$FILTRO" ]; then
		ok "⭐ i casi «$FILTRO» passano"
		inf "⚠ e questo NON e' «B7 passa»: il giro era parziale"
	else
		ok "⭐ B7 passa"
	fi
	;;
2) ko "⛔ B7: non c'e' stato niente da misurare (filtro «$FILTRO»)" ;;
3)
	ko "⛔ B7 NON HA MISURATO: lo strumento non si e' certificato"
	ko "   ⚠ questo NON e' un rosso del server: e' il banco che si e'"
	ko "     fermato prima di produrre un numero di cui non risponde"
	;;
*) ko "⛔ B7: qualcosa non passa" ;;
esac
inf "il registro completo resta in $FUORI/b7-server.log"
exit "$ESITO"
