#!/bin/bash
#
# 01-b2-lancia-trasporto.sh — gira SUL SERVER.  Le proprieta' di trasporto che
#                             restavano a B2, lette dal pari.
#
#   bash /media/REMOTIX/src/01-b2-lancia-trasporto.sh --bersaglio controllo
#   bash /media/REMOTIX/src/01-b2-lancia-trasporto.sh --bersaglio innesto
#   bash /media/REMOTIX/src/01-b2-lancia-trasporto.sh --bersaglio prodotto
#   bash /media/REMOTIX/src/01-b2-lancia-trasporto.sh --bersaglio tutti
#
# ---------------------------------------------------------------------------
# ⛔⭐ TRE BERSAGLI, E NEL REGISTRO C'E' SCRITTO QUALE — 11 agosto 2026
#
# Le sei proprieta' di B2 sono `[M]` sull'INNESTO.  Il PRODOTTO e' un altro
# server, e di cinque delle sei non le ha lette nessuno.  ⛔ Sei numeri letti
# su due server diversi, se il registro non dice quale, sono sei numeri che non
# si possono mettere in fila: da qui `--bersaglio`, obbligatorio, che finisce
# dentro ogni riga di `b2-trasporto-esiti.jsonl` insieme all'IMPRONTA del
# binario misurato.
#
#   bersaglio   che cosa e'                          porta   attesi
#   ---------   -----------------------------------  -----   -------------------
#   innesto     bsslserver + gli innesti di B2        7447   30 s · 16 · due bozze
#   prodotto    `remotix`, il server vero             7448   30 s · 16 · due bozze
#   controllo   `aioquic` che fa da server            7449   60 s · 125 · una bozza
#
# ⭐ IL CONTROLLO NON E' UN DOPPIONE, ED E' IL PEZZO CHE MANCAVA.
#
#   1. e' il CONTROLLO POSITIVO DELLA SONDA: aioquic dichiara 60 000 ms e 128
#      stream unidirezionali, cioe' numeri DIVERSI da quelli degli altri due.
#      Se la sonda leggesse gli stessi numeri dappertutto starebbe stampando
#      costanti, e i verdi sul prodotto non varrebbero niente (`LEZIONI.md`
#      §1.9 punto 2: «questo strumento sa trovare qualcosa che c'e' di
#      sicuro?»).
#   2. e' il CONTROLLO NEGATIVO delle due bozze di WebTransport: aioquic 1.2
#      conosce la bozza 02 e NON la 07 `[R]`.  Il controllo delle due bozze
#      deve saper dire di NO, e qui e' l'unico posto in cui lo dimostra.
#
# ⛔ Quindi il controllo si esegue PER PRIMO.  Un rosso sul prodotto, con il
#    controllo mai fatto, e' ambiguo fra «il prodotto sbaglia» e «la sonda non
#    sa leggere» — che e' `LEZIONI.md` §1.2, il banco si certifica prima della
#    misura.
#
# ---------------------------------------------------------------------------
# ⚠ IL SECONDO GIRO DELL'INNESTO, E PERCHE' SUL PRODOTTO NON C'E'
#
#   1. il server com'e' (tetto d'inattivita' predefinito)  -> atteso 30 000 ms
#   2. il server con `--timeout=10s`                       -> atteso 10 000 ms
#
# ⛔ Il secondo giro non e' un doppione: `FASI.md` §01-filo-nudo chiede che il
#    banco **possa cambiare `max_idle_timeout`** (rilievo R3.19).  Senza,
#    quando B3 misurera' i suoi trenta secondi non potra' distinguere il tetto
#    del protocollo da quello del trasporto — e una prova che non distingue
#    due cause non e' una prova.
#
# ⭐ E si misura, non si legge dal `--help`: «l'opzione esiste» e «l'opzione
#    cambia quel che arriva al pari» sono due affermazioni diverse.
#
# ⛔ Sul PRODOTTO quel giro NON si fa, e non e' una dimenticanza: `IDLE_MS` e'
#    una costante di compilazione in `src/trasporto.c` e `src/main.c` non ha
#    nessuna opzione per il tetto.  Cioe' il prodotto **non sa** cambiare
#    `max_idle_timeout` da riga di comando.  E' informazione, non un buco: si
#    dichiara qui, e chi scrivera' il B3 del prodotto sa gia' che gli manca la
#    leva che l'innesto gli dava.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati   # ⚠ percorso DENTRO il contenitore
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
SERVER_FUORI="$FUORI/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"

# Il prodotto: la riga d'accensione e' la STESSA di
# `banchi/prodotto/avvia-server.sh` — se le due divergono, i due giri misurano
# due server diversi con lo stesso nome.
PROD_DIR_FUORI="$FUORI/remotix"
PROD_DIR="$DENTRO/remotix"
PROD_BIN_FUORI="$PROD_DIR_FUORI/remotix"

BERSAGLIO=innesto
IND=192.168.0.2
while [ $# -gt 0 ]; do
	case "$1" in
	--bersaglio) BERSAGLIO=${2:-}; shift 2 ;;
	--bersaglio=*) BERSAGLIO=${1#*=}; shift ;;
	-*) echo "opzione sconosciuta: $1"; exit 2 ;;
	*) IND=$1; shift ;;
	esac
done

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ⛔ L'IMPRONTA DI CIO' CHE SI MISURA, e non e' un vezzo: un binario
#    ricostruito e' un altro bersaglio con lo stesso nome, e due righe di
#    registro con lo stesso `bersaglio` e numeri diversi sarebbero
#    inspiegabili.  Se non si riesce a calcolarla si scrive «ignota», che e'
#    un'informazione — non si inventa.
impronta_di()
{
	local f=$1 h
	h=$(md5sum "$f" 2>/dev/null | cut -d' ' -f1)
	[ -n "$h" ] && printf 'md5:%s' "$h" || printf 'ignota'
}

# ⚠ L'etichetta passata alla sonda e' una parola sola, SENZA apostrofi: il
#   primo giro del 10 agosto le mandava una frase che conteneva «proprieta'»,
#   e l'apostrofo ha chiuso le virgolette attraverso le tre shell annidate —
#   «unexpected EOF while looking for matching quote».  E' la stessa famiglia
#   del difetto del 9 agosto: le righe di comando si mettono in un file, e i
#   valori che le attraversano si tengono semplici.
# ⛔ «PORTA LIBERA» E «NON HO POTUTO GUARDARE» NON SONO LA STESSA COSA — R8.15.
#
# `chi=$(bash enter.sh --root "ss | grep …")` cattura solo lo standard output:
# `enter.sh` fallito su un mount o su una credenziale scaduta, `ss` assente nel
# chroot, `grep` che non trova e la porta davvero libera davano tutt'e quattro
# la stessa stringa vuota, e il banco leggeva «non ho potuto guardare» come
# «non c'e' niente».
#
# ⚠ La redirezione sta DENTRO le virgolette del comando remoto: attorno a
#   `enter.sh` si porterebbe via la richiesta di password di sudo.
# Esce 0 = occupata · 1 = libera · 2 = non ho potuto guardare.
guarda_porta()
{
	local p=$1
	rm -f "$FUORI/b2-tra-porte.txt" "$FUORI/b2-tra-porte.stato"
	bash "$ENTRA" --root \
		"ss -ulnp > $DENTRO/b2-tra-porte.txt 2>&1; echo \$? > $DENTRO/b2-tra-porte.stato"
	local entrata=$?
	if [ "$entrata" -ne 0 ]; then
		ko "non si e' potuto guardare le porte: enter.sh e' uscito $entrata"
		return 2
	fi
	if [ ! -f "$FUORI/b2-tra-porte.stato" ] || [ ! -f "$FUORI/b2-tra-porte.txt" ]; then
		ko "non si e' potuto guardare le porte: l'elenco non e' stato scritto"
		return 2
	fi
	local stato_ss
	stato_ss=$(cat "$FUORI/b2-tra-porte.stato")
	if [ "$stato_ss" != 0 ]; then
		ko "«ss» dentro il contenitore e' uscito $stato_ss:"
		sed 's/^/        /' "$FUORI/b2-tra-porte.txt"
		return 2
	fi
	grep ":$p " "$FUORI/b2-tra-porte.txt" | sed 's/^/        /' && return 0
	return 1
}

# La sonda, con il bersaglio e l'impronta dentro.
# $1 bersaglio · $2 etichetta · $3 porta · $4 impronta · $5 idle atteso
# $6 credito atteso · $7 bozze attese
sonda()
{
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-trasporto.py --bersaglio $1 --etichetta $2 \
		 --indirizzo $IND --porta $3 --impronta $4 --idle-atteso $5 \
		 --credito-atteso $6 --bozze-attese $7"
}

# ---------------------------------------------------------------------------
# 1. IL CONTROLLO — si fa per primo, e certifica la sonda prima della misura.
giro_controllo()
{
	local PORTA=7449
	log "controllo della sonda — aioquic fa da server su $PORTA"
	inf "atteso: idle 60 000 ms · 128 uni dichiarati (125 a RCP) · SOLO la bozza 02"
	inf "⛔ un ROSSO sulla bozza 07 qui e' l'esito GIUSTO: dimostra che il"
	inf "   controllo delle due bozze sa dire di no"
	guarda_porta "$PORTA"
	local libera=$?
	[ "$libera" -eq 2 ] && return 3
	if [ "$libera" -eq 0 ]; then
		ko "la porta $PORTA e' occupata (l'elenco e' qui sopra)"
		return 3
	fi
	rm -f "$FUORI/b2-tra-controllo.log" "$FUORI/b2-tra-controllo.pid"
	bash "$ENTRA" --root \
		"nohup python3 $DENTRO/01-b2-controllo-aioquic.py $PORTA < /dev/null \
		 > $DENTRO/b2-tra-controllo.log 2>&1 & echo \$! > $DENTRO/b2-tra-controllo.pid"
	sleep 2
	local p=""
	[ -f "$FUORI/b2-tra-controllo.pid" ] && p=$(cat "$FUORI/b2-tra-controllo.pid")
	if [ -z "$p" ] || [ ! -d "/proc/$p" ]; then
		ko "il controllo non e' partito.  Il registro dice:"
		sed 's/^/        /' "$FUORI/b2-tra-controllo.log"
		return 4
	fi
	ok "controllo in ascolto, PID $p"
	# ⚠ 125 = 128 dichiarati da aioquic meno i 3 che HTTP/3 si prende: e' lo
	#   stesso conto che si fa sul prodotto, applicato a un numero diverso.
	#   Se la sonda leggesse 19 anche qui, starebbe stampando una costante.
	sonda controllo aioquic-1.2.0 "$PORTA" \
		"$(impronta_di /media/REMOTIX/devroot/usr/lib/python3/dist-packages/aioquic/quic/connection.py)" \
		60000 125 02
	local e=$?
	bash "$ENTRA" --root "kill $p || true"
	rm -f "$FUORI/b2-tra-controllo.pid"
	sleep 1
	return "$e"
}

# ---------------------------------------------------------------------------
# 2. L'INNESTO — quel che questo banco misurava fino al 10 agosto.
giro_innesto()
{
	# $1 = etichetta breve, $2 = tetto atteso in ms, $3.. = opzioni in piu'
	local ETICHETTA=$1 atteso=$2; shift 2
	local PORTA=7447
	log "innesto — $ETICHETTA"
	guarda_porta "$PORTA"
	local libera=$?
	[ "$libera" -eq 2 ] && return 3
	if [ "$libera" -eq 0 ]; then
		ko "la porta $PORTA e' occupata (l'elenco e' qui sopra)"
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
	# ⛔ 16 disponibili: l'innesto ne dichiara 16 come TOTALE, quindi dopo i 3
	#    di HTTP/3 gliene restano 13 e QUESTO CONTROLLO DEVE DIVENTARE ROSSO.
	#    Non e' un guasto del banco: e' il rilievo B-12 che si ripresenta dove
	#    non e' stato curato — l'innesto e' fermo alla riga vecchia, il
	#    prodotto no.
	sonda innesto "$ETICHETTA" "$PORTA" "$(impronta_di "$SERVER_FUORI")" \
		"$atteso" 16 02,07
	local e=$?
	bash "$ENTRA" --root "kill $p || true"
	rm -f "$FUORI/b2-tra.pid"
	sleep 1
	return "$e"
}

# ---------------------------------------------------------------------------
# 3. IL PRODOTTO — il punto per cui questo file e' stato riaperto.
giro_prodotto()
{
	local PORTA=7448
	log "prodotto — remotix su $PORTA"

	if [ ! -x "$PROD_BIN_FUORI" ]; then
		ko "il binario del prodotto non c'e': $PROD_BIN_FUORI"
		return 3
	fi

	# ⛔⭐ IL BINARIO PIU' VECCHIO DEI SORGENTI NON SI MISURA.
	#
	#    L'11 agosto 2026 `remotix` era delle 21:08 e `trasporto.c` delle
	#    22:10 (ora del server): misurarlo avrebbe prodotto sei numeri
	#    attribuiti a un codice che nessuno di quei numeri ha mai eseguito.
	#    E' la forma piu' silenziosa di **E2** — due cose diverse sotto la
	#    stessa etichetta — perche' il verdetto sembra a posto.
	#
	# ⚠ Il banco NON ricostruisce da se': ricostruire e' un'altra decisione,
	#   con altri rischi, e la prende chi lancia.  Qui ci si ferma e si dice
	#   che cosa manca.
	local nuovi
	nuovi=$(find "$PROD_DIR_FUORI" -maxdepth 1 \( -name '*.c' -o -name '*.h' \) \
		-newer "$PROD_BIN_FUORI" -printf '%f ' 2>/dev/null)
	if [ -n "$nuovi" ]; then
		ko "il binario e' PIU' VECCHIO dei sorgenti: $nuovi"
		ko "⛔ non si misura.  Prima si ricostruisce, con lo script del prodotto"
		ko "   (non con un `make` a mano: `costruisci.sh` guarda l'ESITO del"
		ko "   costruttore, non la presenza del file — LEZIONI.md §1.9):"
		inf "   bash $ENTRA --root \"bash $PROD_DIR/costruisci.sh\""
		inf "   (e poi si rilancia questo banco)"
		return 3
	fi
	ok "il binario e' piu' recente di tutti i sorgenti"

	guarda_porta "$PORTA"
	local libera=$?
	[ "$libera" -eq 2 ] && return 3
	if [ "$libera" -eq 0 ]; then
		ko "la porta $PORTA e' occupata (l'elenco e' qui sopra)"
		ko "⛔ non si misura: sarebbe la misura del server di qualcun altro"
		return 3
	fi

	rm -f "$FUORI/b2-tra-prod.log" "$FUORI/b2-tra-prod.pid"
	# ⚠ La riga e' quella di `banchi/prodotto/avvia-server.sh`, con due sole
	#   differenze DICHIARATE: il file del pid e il registro portano un nome
	#   proprio di questo banco, per non pestare i piedi a chi ha acceso il
	#   prodotto per un'altra ragione.
	bash "$ENTRA" --root \
		"nohup $PROD_DIR/remotix --indirizzo 0.0.0.0 --nome $IND --porta $PORTA \
		 --certificati $DENTRO/remotix-cert --pagina $PROD_DIR/pagina.html \
		 --ban $DENTRO/remotix-ban < /dev/null > $DENTRO/b2-tra-prod.log 2>&1 & \
		 echo \$! > $DENTRO/b2-tra-prod.pid"
	sleep 2
	local p=""
	[ -f "$FUORI/b2-tra-prod.pid" ] && p=$(cat "$FUORI/b2-tra-prod.pid")
	if [ -z "$p" ] || [ ! -d "/proc/$p" ]; then
		ko "il prodotto non e' partito.  Il registro dice:"
		sed 's/^/        /' "$FUORI/b2-tra-prod.log"
		return 4
	fi
	ok "prodotto in ascolto, PID $p"

	sonda prodotto remotix "$PORTA" "$(impronta_di "$PROD_BIN_FUORI")" \
		30000 16 02,07
	local e=$?

	# ⛔ Quel che il PRODOTTO dice DI SE' si stampa accanto, e NON e' la
	#    misura: serve a vedere se le due versioni concordano.  Se il registro
	#    del server dicesse 19 e il pari leggesse 16, il difetto starebbe fra
	#    la riga e il filo — ed e' esattamente la coppia che il 10 agosto
	#    nessuno aveva confrontato.
	inf "quel che il prodotto scrive nel PROPRIO registro (per confronto, non e' la misura):"
	grep -a "ascolto UDP" "$FUORI/b2-tra-prod.log" | sed 's/^/        /'

	bash "$ENTRA" --root "kill $p || true"
	rm -f "$FUORI/b2-tra-prod.pid"
	sleep 1
	return "$e"
}

# ---------------------------------------------------------------------------
EC=0; E1=0; E2=0; EP=0
case "$BERSAGLIO" in
controllo)
	giro_controllo; EC=$?
	;;
innesto)
	giro_innesto tetto-predefinito 30000; E1=$?
	giro_innesto tetto-cambiato 10000 --timeout=10s; E2=$?
	;;
prodotto)
	giro_prodotto; EP=$?
	;;
tutti)
	giro_controllo; EC=$?
	giro_innesto tetto-predefinito 30000; E1=$?
	giro_innesto tetto-cambiato 10000 --timeout=10s; E2=$?
	giro_prodotto; EP=$?
	;;
*)
	echo "bersaglio sconosciuto: $BERSAGLIO (innesto | prodotto | controllo | tutti)"
	exit 2
	;;
esac

log "Riepilogo"
case "$BERSAGLIO" in
controllo|tutti)
	inf "controllo (aioquic):      uscita $EC"
	inf "⚠ qui ci si aspetta un ROSSO sulla bozza 07 e nient'altro: e' il"
	inf "  controllo negativo.  Un verde pieno vorrebbe dire che il controllo"
	inf "  delle due bozze non sa dire di no."
	;;
esac
case "$BERSAGLIO" in
innesto|tutti)
	inf "innesto, tetto 30 s:      uscita $E1"
	inf "innesto, tetto 10 s:      uscita $E2"
	inf "⚠ sull'innesto il credito uni e' atteso ROSSO (dichiara 16 come"
	inf "  TOTALE, cioe' 13 a RCP): il rilievo B-12 e' stato curato nel"
	inf "  prodotto e non qui."
	;;
esac
case "$BERSAGLIO" in
prodotto|tutti)
	inf "prodotto (remotix):       uscita $EP"
	;;
esac
inf "il registro con dentro il bersaglio: $FUORI/b2-trasporto-esiti.jsonl"

case "$BERSAGLIO" in
prodotto) exit "$EP" ;;
innesto)  [ "$E1" -eq 0 ] && [ "$E2" -eq 0 ]; exit $? ;;
controllo) exit "$EC" ;;
*) exit 0 ;;
esac
