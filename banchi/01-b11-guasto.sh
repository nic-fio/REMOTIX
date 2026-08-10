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
#
# ⛔ E LO VERIFICA DAI TRE LATI, dal 10 agosto 2026.  Prima guardava **solo il
#    sorgente `.cc`**, cioe' il lato che non conta: quel che sopravvive alla
#    fase e' il binario e il processo, non il testo.  Adesso si verifica
#
#      il PROCESSO   e' davvero morto?  (prima il `kill` non aveva testimoni)
#      la PORTA      risponde ancora qualcuno sulla 7447?  ⭐ e' il lato che
#                    RICEVE, l'unico che sappia dire «e' rimasto acceso»
#      i TRE FILE    i guasti stanno in `rcp.c`, nel `.cc` e nel `.h`
#
#    (rilievi R5.10 e R5.18 della revisione avversariale del 10 agosto 2026.)
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
# ⛔ I GUASTI VIVONO IN TRE FILE, NON IN UNO.
#
#    `01-b11-guasto-innesta.py` innesta in `rcp.c`, in
#    `http3_server_proto_codec.cc` e nel `.h`, e **otto innesti su undici**
#    stanno in `rcp.c`.  Decidere «i guasti ci sono» guardando il solo `.cc` e'
#    la forma E1 — necessario preso per sufficiente: bastava che saltasse un
#    innesto di `rcp.c` perche' il banco stampasse «costruito, e i guasti ci
#    sono» e i casi che quel guasto doveva provocare cadessero col rosso
#    puntato sulla PAGINA, che non c'entra niente.
SORGENTI=(
	"$DENTRO/b2/ngtcp2/examples/rcp.c"
	"$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc"
	"$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.h"
)
IND=192.168.0.2
PORTA=7447
FILTRO="B11|DOPO la fine|CONGEDO di commiato|congedo motivo|canale di controllo aperto"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-accendi}
MARCHE_ATTESE=""

# ⛔ Nessuna redirezione ATTORNO a enter.sh: si porterebbe via la richiesta di
#    password di sudo, e lo script resterebbe fermo su una domanda che nessuno
#    vede.  Dentro le virgolette invece e' del comando remoto.  ⭐ Questa prima
#    chiamata e' quella che la chiede, e da qui in poi le credenziali sono
#    valide: le letture che seguono possono catturare l'uscita.
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }

# ---------------------------------------------------------------------------
# ⛔ LA SENTINELLA: «vuoto» non e' «zero» (`REVIEWER.md` §1 domanda 4, forma E8)
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` diceva «porta
# libera» in tre casi opposti: la porta e' davvero libera, `ss` non c'e' nel
# contenitore, `enter.sh` non ha eseguito il comando.  Il terzo caso accendeva
# un SECONDO server sulla porta di uno gia' acceso, il primo continuava a
# rispondere, e B11 misurava **il server sbagliato** — che poteva essere quello
# SANO, cioe' esattamente il difetto che il commento di `01-b11-lancia.sh`
# dichiara di voler evitare.
#
# ⭐ Qui il comando remoto stampa da se' il proprio stato d'uscita.  Se la riga
#    `B11-FINE` non arriva, il comando non e' arrivato in fondo — e questo si
#    distingue da «e' andato e non ha trovato niente».
# ⚠ E cosi' la misura non poggia piu' sul fatto che `enter.sh` propaghi il
#   codice d'uscita del comando che esegue, che nessuno ha mai verificato
#   (rilievo R5.21, ancora aperto: si chiude con
#   `bash /media/REMOTIX/enter.sh --root "exit 7"; echo $?`).
USCITA=""
dentro() # $1 = comando remoto.  Uscita in $USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB11-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B11-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B11-FINE=')
	if [ -z "$stato" ]; then
		return 125   # il comando non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

# Chi tiene la porta.  0 = occupata (le righe in $CHI) · 1 = libera · 2 = non
# si sa, e «non si sa» non si arrotonda a «libera».
CHI=""
chi_tiene_la_porta()
{
	local st
	dentro "ss -ulnp"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss -ulnp» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO: `ss -ulnp` stampa sempre almeno
	#    la propria intestazione.  Se non stampa niente non ha guardato niente,
	#    e uno strumento che non sa vedere quel che c'e' non puo' dire che
	#    manchi qualcosa (`REVIEWER.md` §1 domanda 5).
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss -ulnp» non ha stampato NIENTE, nemmeno l'intestazione:"
		ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

# Quante marche di B11 ci sono in un file.  Il conto in $N; 2 = non si e'
# potuto contare.  ⚠ `grep -c` esce 1 quando il conto e' zero e >=2 quando non
# ha potuto leggere: sono due cose diverse e qui restano diverse.
N=0
marche()
{
	local st
	dentro "grep -c 'REMOTIX B11 GUASTO' $1"
	st=$?
	if [ "$st" -gt 1 ]; then
		ko "⛔ non si e' potuto contare le marche in $1 (uscita $st):"
		printf '%s\n' "$USCITA" | tail -3 | sed 's/^/        /'
		return 2
	fi
	N=$(printf '%s' "$USCITA" | tr -cd '0-9')
	if [ -z "$N" ]; then
		ko "⛔ il conteggio delle marche in $1 non ha prodotto un numero"
		return 2
	fi
	return 0
}

ricostruisci() # $1 = "con-guasti" | "sano"
{
	local passo st
	# ⛔ E OGNI PASSO SI PROVA.
	#
	#    Le quattro invocazioni avevano tutte `> /dev/null` e **nessuna prova
	#    dello stato d'uscita**.  Bastava far fallire il `git checkout --
	#    examples` di `01-b2-ngtcp2-wt-innesta.py --togli` (albero non pulito,
	#    permessi, `git` assente): la marca `REMOTIX B3` restava nel `.cc`,
	#    `01-b3-rcp-innesta.py` prendeva il cortocircuito «l'innesto c'e'
	#    gia'» — che restituisce **0** — e usciva PRIMA di ricopiare `rcp.c`.
	#    ⚠ La ricostruzione del sorgente sano, cioe' l'unica cosa che impedisce
	#      al server bugiardo di sopravvivere alla fase, non aveva nessun
	#      testimone (rilievo R5.8).
	for passo in "01-b3-rcp-innesta.py --togli" \
	             "01-b2-ngtcp2-wt-innesta.py --togli" \
	             "01-b2-ngtcp2-wt-innesta.py" \
	             "01-b3-rcp-innesta.py"; do
		dentro "python3 $DENTRO/$passo"
		st=$?
		if [ "$st" -ne 0 ]; then
			ko "⛔ «$passo» e' fallito (uscita $st):"
			printf '%s\n' "$USCITA" | tail -20 | sed 's/^/        /'
			return 1
		fi
	done
	if [ "$1" = con-guasti ]; then
		dentro "python3 $DENTRO/01-b11-guasto-innesta.py"
		st=$?
		printf '%s\n' "$USCITA" | sed 's/^/        /'
		if [ "$st" -ne 0 ]; then
			ko "⛔ l'innesto dei guasti di B11 e' fallito (uscita $st)"
			return 1
		fi
		# ⭐ IL DENOMINATORE LO CALCOLA CHI INNESTA, e lo stampa.  Qui non si
		#    scrive a mano nessun numero: invecchierebbe col primo innesto che
		#    qualcuno aggiunge alla tabella.
		MARCHE_ATTESE=$(printf '%s\n' "$USCITA" \
			| sed -n 's/^== B11-MARCHE-ATTESE: \([0-9][0-9]*\)$/\1/p' | tail -1)
		if [ -z "$MARCHE_ATTESE" ]; then
			ko "⛔ l'innesto non ha dichiarato quante marche ci si aspetta:"
			ko "   senza quel numero il controllo qui sotto non ha denominatore"
			return 1
		fi
	fi
	# ⛔ E SI RESTITUISCE L'ESITO DI NINJA.
	#
	#    Il primo giro del 10 agosto 2026 non lo guardava: si limitava a
	#    controllare che `bsslserver` **esistesse ed fosse eseguibile**.  La
	#    compilazione era fallita, il binario di due ore prima era ancora li',
	#    e il banco ha acceso **il server SANO dichiarando di aver acceso quello
	#    guasto**.  ⚠ Tutti i casi di B11 sarebbero falliti, e il rosso sarebbe
	#    finito sulla PAGINA — che non c'entrava niente.
	#
	# ⭐ «Il file c'e'» e «il file e' quello che ho appena costruito» sono due
	#    domande diverse, e solo la seconda ha un denominatore.
	dentro "ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b11-compila.log 2>&1"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ la compilazione e' FALLITA (uscita $st).  Il registro dice:"
		dentro "grep -m6 -n error $DENTRO/b11-compila.log"
		printf '%s\n' "$USCITA" | sed 's/^/        /'
		return 1
	fi
	return 0
}

# Le marche di B11 su tutti e tre i sorgenti.  Il totale in $TOTALE.
TOTALE=0
conta_le_marche()
{
	local f
	TOTALE=0
	for f in "${SORGENTI[@]}"; do
		marche "$f" || return 2
		inf "$(basename "$f"): $N marche «REMOTIX B11 GUASTO»"
		TOTALE=$((TOTALE + N))
	done
	return 0
}

case "$AZIONE" in
registro)
	# ⛔ Il registro del server e' il SECONDO TESTIMONE di B11: due delle
	#    righe della tabella sono proprieta' NEGATIVE della pagina — «dopo
	#    RESPINTO non riprova», «nessun battito applicativo» — e una proprieta'
	#    negativa non si vede da dentro la pagina.
	# ⭐ E il «CONGEDO di commiato» viaggia con loro: e' il testimone POSITIVO
	#    della stessa regola — senza, «zero byte dopo la fine» sarebbe vero
	#    anche per una pagina che non si e' mai congedata.
	#
	# ⛔⭐ E IL TAGLIO IN CODA E' UN DENOMINATORE CHE MENTE, in tutt'e due i
	#    versi, e per questo non c'e' piu'.
	#
	#    Era `tail -60`.  Il 10 agosto 2026, aggiungendo UNA riga in piu' a
	#    questo filtro, i «guasti serviti» sono passati da 26 a 21 — e il
	#    server non aveva cambiato niente: erano le righe vecchie, spinte
	#    fuori dalla finestra dalle nuove.  ⚠ Il `tail -600` che l'aveva
	#    sostituito aveva lo stesso difetto piu' in la': scarta le righe **piu'
	#    vecchie**, cioe' quelle del PRIMO motore, e una riga «byte arrivati
	#    DOPO la fine» del primo motore esce dalla finestra molto prima che il
	#    conto dei casi se ne accorga — «zero byte dopo la fine» diventa il
	#    verde piu' vuoto che ci sia (rilievo R5.9).
	#
	# ⭐ Al posto del tetto c'e' il CONTO: quante righe il filtro ha trovato si
	#    dichiara qui, e chi legge di la' confronta con quante gliene sono
	#    arrivate.  Un troncamento, da qualunque parte venga, si vede.
	if [ ! -f "$FUORI/b11-server.log" ]; then
		ko "⛔ $FUORI/b11-server.log non c'e'."
		ko "   Non e' «zero righe»: e' una lettura che non si e' potuta fare, e"
		ko "   il secondo testimone di B11 non ha niente da dire (forma E8)."
		exit 7
	fi
	QUANTE=$(grep -Ec "$FILTRO" "$FUORI/b11-server.log")
	ST=$?
	if [ "$ST" -gt 1 ]; then
		ko "⛔ non si e' potuto leggere il registro (grep e' uscito $ST)"
		exit 7
	fi
	grep -E "$FILTRO" "$FUORI/b11-server.log"
	printf '== RIGHE-DEL-REGISTRO-FILTRATE: %s\n' "$QUANTE"
	exit 0
	;;
spegni)
	log "1. ⛔ Si ferma il server GUASTO, e si verifica che sia MORTO"
	# ⛔ Quel che va verificato e' IL PROCESSO, non il sorgente (forma E7).
	#
	#    Le tre righe di prima buttavano l'esito tre volte: `cat … 2>/dev/null`
	#    (file dei PID assente ⇒ `P` vuoto ⇒ non si uccide niente), `[ -n "$P" ]
	#    &&` senza ramo `else` (l'assenza del PID non era un errore), `kill $P
	#    2>/dev/null || true`.  E il file dei PID veniva rimosso comunque,
	#    portandosi via la traccia del processo superstite.
	#    ⚠ Con `b11-server.pid` cancellato mentre il server gira, `spegni` non
	#      uccideva niente, ricostruiva il sorgente sano, trovava il grep pulito
	#      e stampava «⭐ il server e' quello vero» uscendo 0 — **con il server
	#      bugiardo ancora acceso sulla 7447** (rilievo R5.18).
	P=""
	if [ -f "$FUORI/b11-server.pid" ]; then
		P=$(cat "$FUORI/b11-server.pid")
	else
		inf "⚠ $FUORI/b11-server.pid non c'e': non si sa QUALE processo fermare,"
		inf "  e allora lo si chiede alla porta, che e' il lato che riceve"
	fi
	if [ -n "$P" ]; then
		dentro "kill $P"
		ST=$?
		[ "$ST" -eq 0 ] || inf "⚠ «kill $P» ha risposto $ST: forse era gia' morto"
		I=0
		STATO=0
		while [ "$I" -lt 10 ]; do
			dentro "test -d /proc/$P"
			STATO=$?
			[ "$STATO" -eq 0 ] || break
			sleep 1
			I=$((I + 1))
		done
		case "$STATO" in
		1) ok "il processo $P e' morto (dopo $I secondi)" ;;
		0) ko "⛔ il server guasto (PID $P) e' ANCORA VIVO dopo $I secondi."
		   ko "   Non si prosegue: la fase resterebbe con un server che mente"
		   ko "   acceso, e il prossimo che lo trova non sapra' da dove viene."
		   exit 6 ;;
		*) ko "⛔ non si e' potuto sapere se il PID $P sia vivo (uscita $STATO)"
		   exit 6 ;;
		esac
	fi
	chi_tiene_la_porta
	ST=$?
	case "$ST" in
	1) ok "la porta $PORTA e' libera: non risponde piu' nessuno" ;;
	0) ko "⛔ la porta $PORTA e' ANCORA TENUTA da qualcuno:"
	   printf '%s\n' "$CHI" | sed 's/^/        /'
	   ko "   ⚠ puo' essere il server SANO di B2 rimasto acceso: il PID e' li'"
	   ko "   sopra.  In tutt'e due i casi la ripulitura non e' finita, e"
	   ko "   dirlo adesso costa meno che scoprirlo al prossimo «accendi»."
	   exit 6 ;;
	*) exit 6 ;;
	esac
	# ⭐ Solo adesso si butta il file dei PID: e' la traccia del processo, e si
	#    perde per ultima.
	rm -f "$FUORI/b11-server.pid"

	log "2. ⛔ Si rimette il server SANO"
	# ⛔ E L'ESITO DELLA RICOSTRUZIONE SI LEGGE.
	#
	#    `ricostruisci sano` era una istruzione nuda: lo stesso stato d'uscita
	#    che `accendi` prova (`if ! ricostruisci con-guasti`) qui veniva
	#    buttato.  Bastava far fallire la ricostruzione del server sano perche'
	#    sul disco restasse **il binario guasto** mentre il sorgente tornava
	#    pulito: il grep qui sotto era verde, si stampava «il server e' quello
	#    vero», e il prossimo `01-b2-lancia-wt.sh accendi` accendeva quel
	#    binario (rilievo R5.1).
	if ! ricostruisci sano; then
		ko "⛔ LA RICOSTRUZIONE DEL SERVER SANO E' FALLITA."
		ko "   Sul disco puo' esserci ancora il binario GUASTO, e il sorgente"
		ko "   pulito non lo dice: si rimettono a mano gli innesti di B2 e B3."
		exit 5
	fi
	conta_le_marche || exit 5
	if [ "$TOTALE" -eq 0 ]; then
		ok "⭐ nessuna traccia di B11 nei ${#SORGENTI[@]} sorgenti, e il binario"
		ok "   e' quello appena ricostruito: il server e' quello vero"
	else
		ko "⛔ RESTANO $TOTALE righe di B11 nei sorgenti."
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
chi_tiene_la_porta
ST=$?
case "$ST" in
1) ok "porta $PORTA libera — e lo dice «ss», non il silenzio" ;;
0) ko "la porta $PORTA e' occupata:"
   printf '%s\n' "$CHI" | sed 's/^/        /'
   exit 3 ;;
*) exit 3 ;;
esac

log "2. Il server guasto si costruisce"
if ! ricostruisci con-guasti; then
	ko "   e NON si accende niente: il binario vecchio e' ancora sul disco, e"
	ko "   accenderlo vorrebbe dire misurare un server SANO credendolo guasto"
	exit 4
fi
conta_le_marche || exit 4
if [ "$TOTALE" -ne "$MARCHE_ATTESE" ]; then
	ko "⛔ sul disco ci sono $TOTALE marche di B11, e chi le ha innestate ne"
	ko "   dichiara $MARCHE_ATTESE: i guasti che il banco crede di misurare non sono"
	ko "   quelli che il server ha dentro, e il rosso finirebbe sulla PAGINA"
	exit 4
fi
ok "costruito, e i guasti ci sono tutti: $TOTALE su $MARCHE_ATTESE attese, in ${#SORGENTI[@]} file"

log "3. Si accende"
rm -f "$FUORI/b11-server.log" "$FUORI/b11-server.pid"
# ⚠ `--timeout=120s`: il caso «silenzio» tace otto secondi per provare che la
#   pagina non manda un battito applicativo (§2.2).  Col tetto predefinito a
#   30 s la connessione reggerebbe lo stesso, ma i casi in fila su una sola
#   pagina no.
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b11-server.log 2>&1 & echo \$! > $DENTRO/b11-server.pid"
sleep 2
PID=$(cat "$FUORI/b11-server.pid" 2>/dev/null)
# ⚠ `/proc/$PID` si legge di qui e non da dentro, ed e' corretto: quello di
#   `enter.sh` e' un `chroot` (`v1/banco/enter.sh`), che condivide lo spazio dei
#   PID dell'ospite — non un contenitore con un suo spazio.
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server guasto non e' partito:"
	sed 's/^/        /' "$FUORI/b11-server.log"
	exit 4
fi
# ⛔ «VIVO» NON E' «IN ASCOLTO», ed e' la forma E1 in una riga sola.
#
#    `01-b2-lancia-wt.sh` fa questa stessa verifica e spiega perche': «il
#    server e' vivo ma non tiene nessuna porta UDP».  B11 ne conservava la
#    meta' e buttava l'altra: un server ancora vivo a 2 s ma che avesse gia'
#    fallito il `bind` faceva stampare «ok server GUASTO in ascolto», e tutti i
#    casi cadevano col rosso sulla PAGINA (rilievo R5.13).
chi_tiene_la_porta
ST=$?
if [ "$ST" -ne 0 ]; then
	ko "il server e' vivo (PID $PID) ma sulla porta $PORTA non c'e' nessuno:"
	sed 's/^/        /' "$FUORI/b11-server.log"
	exit 4
fi
ASC=$(printf '%s\n' "$CHI" | grep "pid=$PID,")
if [ -z "$ASC" ]; then
	ko "⛔ la porta $PORTA e' tenuta da un ALTRO processo, non dal nostro $PID:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "   B11 misurerebbe il server sbagliato — che potrebbe essere quello SANO"
	exit 4
fi
ok "server GUASTO in ascolto, PID $PID"
printf '%s\n' "$ASC" | sed 's/^/        /'
inf "⛔ e' un server che mente di proposito: si spegne con «spegni», che"
inf "   rimette anche il sorgente sano"
inf "l'impronta del certificato della sessione, per la pagina:"
bash "$ENTRA" --root \
	"openssl x509 -in $CERT/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0" \
	| tail -1 | sed 's/^/        /'
exit 0
