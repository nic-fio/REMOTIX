#!/bin/bash
#
# 01-c2-lancia.sh — gira SUL SERVER.  C2: tre modi di guastare il collegamento,
#                   tre diagnosi diverse.
#
#   bash /media/REMOTIX/src/01-c2-lancia.sh            le quattro scene
#   bash /media/REMOTIX/src/01-c2-lancia.sh elenco     le scene e le attese
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' QUESTO SCRIPT ESISTE, VISTO CHE IL BANCO E' IN PYTHON
#
# Una cosa sola: **spegnere il server fra le due fasi**.  Le scene 1 e 2 vogliono
# la porta libera, e un programma non puo' spegnere il server che gli serve per
# la scena 0 senza perdere la scena 0.  ⭐ Il VERDETTO invece resta tutto dentro
# `01-c2-diagnosi.py`, che le vede tutt'e quattro: se il confronto lo facesse
# questo script, sarebbe `bash` a decidere quanti nomi diversi sono usciti — ed
# e' esattamente la forma che la regola **B0.4** vieta.
#
# ---------------------------------------------------------------------------
# ⛔ L'ORDINE DELLE SCENE NON E' LIBERO
#
#   1. con il server acceso: `sano` e `impronta-non-corrente` — sono la stessa
#      scena, e cambia solo l'impronta che teniamo in mano;
#   2. si spegne, e si VERIFICA che sia spento (lo rifa' anche il python: due
#      testimoni, uno di sistema e uno dal filo);
#   3. senza server: `nessuno-in-ascolto`, poi `udp-filtrato`.
#
# ⚠ Se si invertissero, `nessuno-in-ascolto` troverebbe le prese della scena 2
#   ancora aperte e riceverebbe la diagnosi dell'altra: due scene che si
#   contaminano danno **due nomi giusti per la ragione sbagliata**.
#
# ---------------------------------------------------------------------------
# ⛔ E LE PRESE DELLA SCENA 2 NON SOPRAVVIVONO AL GIRO
#
# La scena «UDP filtrato» si costruisce con due prese sulla 7447, non con una
# regola di firewall (il perche' sta in cima a `01-c2-diagnosi.py`).  ⛔ Alla
# fine questo script **verifica che la porta sia tornata libera**: una presa
# lasciata li' farebbe fallire l'accensione del prossimo banco, e la diagnosi
# sarebbe «la porta e' occupata» — un guasto di C2 addosso a un altro.
#
# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE (B0.1, B0.3)
#
#  · la porta 7447 dev'essere libera all'inizio, UDP e TCP;
#  · ⭐ **C2 non manda mai `CREDENZIALI`**: non consuma il conto di §4.4-bis e
#    non lascia ban addosso a nessuno.  ⚠ E **non chiama il comando di sblocco**
#    — che esiste, `01-b8-sblocca.py` su `--comando-socket` — perche' non ne ha
#    bisogno.  Dichiarato: B0.3 vuole che si dica quale delle due si e' fatta.
#
# ⛔ NESSUNA REDIREZIONE ATTORNO A `enter.sh`.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
SERVER_FUORI="$FUORI/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
IND=192.168.0.2
PORTA=7447
ESITI=$DENTRO/c2-esiti.json
ESITI_FUORI=$FUORI/c2-esiti.json

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-tutto}
# ⛔ Il diagnosta si puo' scambiare, ed e' B12 a servirsene: certifica C2
#    facendo girare una COPIA accecata su una delle due sonde.  ⚠ Il valore
#    predefinito e' il diagnosta vero, e quale sia si STAMPA: un banco che gira
#    contro una copia guasta senza dirlo e' peggio di uno che non gira.
DIAGNOSTA=${2:-$DENTRO/01-c2-diagnosi.py}
case "$AZIONE" in tutto|elenco) ;; *)
	ko "azione sconosciuta: $AZIONE  (tutto | elenco)"; exit 2 ;;
esac

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"
inf "il diagnosta in uso: $DIAGNOSTA"

# ---------------------------------------------------------------------------
# ⛔ LA SENTINELLA: «vuoto» non e' «zero» — rilievo R12-A.7, e la cura era gia'
#    scritta nella stessa cartella, in `01-b11-guasto.sh:92-129`.
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` diceva «porta
# libera» in tre casi opposti: la porta e' davvero libera · `ss` non c'e' nel
# contenitore · `enter.sh` non ha eseguito il comando.  In questo file la forma
# cieca stava in cinque punti, e ⛔ **il quinto era la ripulitura finale** —
# l'unica cosa che impedisce a C2 di lasciare due prese sulla 7447 addosso al
# banco successivo.  Se `ss` non rispondeva, C2 stampava «la porta e' tornata
# libera» e usciva 0, e il banco dopo dava la colpa a se stesso.
#
# ⭐ Qui il comando remoto stampa da se' il proprio stato d'uscita, e in piu'
#    c'e' il controllo positivo dello strumento: `ss` stampa sempre almeno la
#    propria intestazione, e se non stampa niente non ha guardato niente.
# ⚠ La sostituzione di comando e' lecita da qui in poi e non prima: la riga
#   `--root "true"` qui sopra e' quella che si prende la richiesta di password
#   di sudo.  Il divieto riguarda le REDIREZIONI attorno a `enter.sh`.
USCITA=""
dentro() # $1 = comando remoto.  Uscita in $USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nC2-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^C2-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^C2-FINE=')
	if [ -z "$stato" ]; then
		return 125   # non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

# Chi tiene la porta.  0 = occupata (le righe in $CHI) · 1 = libera · 2 = non
# si sa, e ⛔ «non si sa» non si arrotonda a «libera».
CHI=""
chi_tiene_la_porta() # $1 = -ulnp (UDP) | -tlnp (TCP)
{
	local opz=$1 st
	dentro "ss $opz"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss $opz» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss $opz» non ha stampato NIENTE, nemmeno l'intestazione:"
		ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

# ⭐ E la domanda «la porta e' libera su TUTT'E DUE i trasporti?» si pone in un
#    posto solo: 0 = libera · 1 = occupata (le righe in $TENUTA) · 2 = non si sa.
TENUTA=""
porta_libera()
{
	local sa=0
	TENUTA=""
	chi_tiene_la_porta -ulnp
	case $? in
	0) TENUTA="$CHI" ;;
	2) sa=1 ;;
	esac
	chi_tiene_la_porta -tlnp
	case $? in
	0) TENUTA="$TENUTA
$CHI" ;;
	2) sa=1 ;;
	esac
	[ -n "$(printf '%s' "$TENUTA" | tr -d '[:space:]')" ] && return 1
	[ "$sa" -eq 1 ] && return 2
	return 0
}

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DIAGNOSTA --elenco"
	exit 0
fi

# ---------------------------------------------------------------------------
log "1. Lo stato iniziale: la porta $PORTA, UDP e TCP"
porta_libera
case $? in
0)	ok "porta $PORTA libera, UDP e TCP (e «ss» ha parlato: non e' un silenzio)" ;;
1)	ko "la porta $PORTA e' gia' occupata:"
	printf '%s\n' "$TENUTA" | sed '/^$/d;s/^/        /'
	ko "⛔ le quattro scene misurerebbero il server di un altro banco."
	ko "   Fermalo per PID (mai con pkill -f) e rilancia."
	exit 3 ;;
*)	ko "⛔ non si e' potuto sapere chi tiene la porta $PORTA:"
	ko "   e «non si sa» non si arrotonda a «libera» (B0.1)"
	exit 3 ;;
esac

if [ ! -f "$SERVER_FUORI" ]; then
	ko "⛔ il binario non c'e': $SERVER_FUORI"
	ko "   Senza, la scena 0 — il controllo che dice NO — non esiste,"
	ko "   e senza quella «tre diagnosi diverse» non prova niente."
	exit 3
fi
ok "il binario c'e'"

# ---------------------------------------------------------------------------
log "2. Il server acceso — scene 0 «sano» e 3 «impronta-non-corrente»"
rm -f "$FUORI/c2-server.log" "$FUORI/c2-server.pid" "$ESITI_FUORI"
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/c2-server.log 2>&1 & echo \$! > $DENTRO/c2-server.pid"
sleep 2
PID=$(cat "$FUORI/c2-server.pid" 2>/dev/null)
# ⛔ `/proc`, non `kill -0`: su un processo di root `kill -0` da utente normale
#    dice «proibito», che non e' «morto».
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server non e' partito.  Il registro dice:"
	[ -f "$FUORI/c2-server.log" ] && sed 's/^/        /' "$FUORI/c2-server.log"
	exit 4
fi
ok "in ascolto, PID $PID"

# ⛔ SPEGNERE E' UNA COSA SOLA, E SI FA IN UN POSTO SOLO — rilievo R12-A.11.
#
#    La strada d'errore faceva `kill $PID` e **usciva subito**, senza aspettare
#    che il processo morisse e senza controllare che la porta si fosse
#    liberata, mentre il cammino normale lo faceva con cura.  Il banco
#    successivo trovava la 7447 occupata — e per A.7 poteva non vederlo.
#    ⭐ Due copie della stessa operazione, e una delle due invecchia sempre:
#    qui ce n'e' una.
spegni_e_verifica()
{
	local giri=0
	bash "$ENTRA" --root "kill $PID 2>/dev/null || true"
	# ⛔ Non si va avanti finche' il processo non e' sparito davvero: un `kill`
	#    e' una richiesta, non un fatto.  E fra la morte del processo e il
	#    rilascio della porta passa un istante che, se non si aspetta, fa
	#    misurare alla scena 1 una porta ancora tenuta.
	# ⛔ `/proc`, non `kill -0`: su un processo di root `kill -0` da utente
	#    normale dice «proibito», che non e' «morto».
	while [ -d "/proc/$PID" ] && [ "$giri" -lt 20 ]; do
		sleep 0.5
		giri=$((giri + 1))
	done
	if [ -d "/proc/$PID" ]; then
		ko "⛔ il processo $PID e' ancora vivo dopo 10 s"
		return 1
	fi
	ok "il processo $PID e' sparito (dopo $giri mezzi secondi)"
	porta_libera
	case $? in
	0)	ok "la porta $PORTA e' libera, UDP e TCP" ; return 0 ;;
	1)	ko "⛔ la porta $PORTA e' ancora tenuta da qualcuno:"
		printf '%s\n' "$TENUTA" | sed '/^$/d;s/^/        /'
		return 1 ;;
	*)	ko "⛔ non si e' potuto sapere se la porta si e' liberata:"
		ko "   e «non si sa» non si arrotonda a «libera»"
		return 1 ;;
	esac
}

bash "$ENTRA" --root \
	"python3 -u $DIAGNOSTA --indirizzo $IND --porta $PORTA --certificati $CERT --fase con-server --esiti $ESITI"
E1=$?
if [ "$E1" -ne 0 ]; then
	ko "⛔ la fase «con-server» esce $E1: le scene 0 e 3 non sono state misurate"
	# ⛔ E SI SPEGNE CON LA STESSA CURA DEL CAMMINO BUONO (R12-A.11): uscire
	#    subito dopo il `kill` lasciava il server a morire per conto suo e la
	#    porta addosso al banco successivo, che avrebbe dato la colpa a se'.
	log "Si spegne — anche uscendo per un errore"
	if ! spegni_e_verifica; then
		ko "⛔ e il server di C2 sopravvive a questo giro: fermalo per PID"
		ko "   (mai con pkill -f) prima di lanciare qualunque altro banco"
	fi
	exit "$E1"
fi

# ---------------------------------------------------------------------------
log "3. Si spegne — e lo si verifica dal SISTEMA, non solo dal filo"
if ! spegni_e_verifica; then
	ko "⛔ le scene 1 e 2 non si possono costruire, e misurarle lo stesso"
	ko "   darebbe due nomi giusti per la ragione sbagliata"
	exit 4
fi

# ---------------------------------------------------------------------------
log "4. Senza server — scene 1 «nessuno-in-ascolto» e 2 «udp-filtrato»"
inf "⛔ e il VERDETTO di tutte e quattro lo da' questa chiamata: e' l'unico"
inf "   posto che le vede insieme (B0.4)"
bash "$ENTRA" --root \
	"python3 -u $DIAGNOSTA --indirizzo $IND --porta $PORTA --certificati $CERT --fase senza-server --esiti $ESITI"
E=$?

# ---------------------------------------------------------------------------
log "5. ⛔ Le prese della scena 2 non devono sopravvivere al giro"
# ⛔ QUESTA E' LA LETTURA CHE CONTA PIU' DI TUTTE — rilievo R12-A.7.
#    E' l'unica cosa che impedisce a C2 di lasciare due prese sulla 7447
#    addosso al banco successivo; con la forma cieca, se `ss` non rispondeva
#    C2 stampava «la porta e' tornata libera» e usciva 0.
porta_libera
case $? in
0)	ok "la porta $PORTA e' tornata libera, UDP e TCP (e «ss» ha parlato)" ;;
1)	ko "⛔ QUALCOSA TIENE ANCORA LA PORTA $PORTA:"
	printf '%s\n' "$TENUTA" | sed '/^$/d;s/^/        /'
	ko "   Il prossimo banco troverebbe «la porta e' occupata» e darebbe la"
	ko "   colpa a se stesso.  ⚠ La ripulitura che fallisce entra nell'esito."
	[ "$E" -eq 0 ] && E=6 ;;
*)	ko "⛔ NON SI SA se le prese della scena 2 siano state chiuse:"
	ko "   lo strumento non ha risposto, e il suo silenzio non e' una porta"
	ko "   libera.  ⚠ Una ripulitura non verificata vale come non fatta:"
	ko "   entra nell'esito invece di sparire."
	[ "$E" -eq 0 ] && E=6 ;;
esac

# ---------------------------------------------------------------------------
log "Esito"
case "$E" in
0) ok "⭐ C2: quattro guasti, quattro diagnosi diverse"
   ok "   compresa quella che il giorno del certificato scaduto non dira'"
   ok "   «il server non risponde»" ;;
1) ko "⛔ C2: qualche scena riceve la diagnosi sbagliata — e' il difetto che"
   ko "   C2 esiste per trovare" ;;
2) ko "⛔ C2: zero scene misurate — non e' un verde" ;;
3) ko "⛔ C2: giro PARZIALE, meno di quattro scene" ;;
4) ko "⛔ C2: lo strumento non e' certificato (impronte illeggibili o uguali)" ;;
5) ko "⛔ C2: lo stato iniziale non era quello che serve (B0.1)" ;;
6) ko "⛔ C2: le scene passano ma la ripulitura no" ;;
*) ko "⛔ C2: uscita $E" ;;
esac
inf "gli esiti restano in $ESITI_FUORI, il registro in $FUORI/c2-server.log"
exit "$E"
