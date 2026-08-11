#!/bin/bash
#
# 01-b13-lancia.sh — gira SUL SERVER.  B13: le sei cose che nessun banco guardava.
#
#   bash /media/REMOTIX/src/01-b13-lancia.sh            il giro intero
#   bash /media/REMOTIX/src/01-b13-lancia.sh elenco     le sei previsioni
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA MISURA, IN UNA RIGA D'UTENTE
#
# *«Le cose che il server produce di contorno e che nessuno guarda finche' non
# ti mordono»*: i due certificati, la parola d'ordine nei registri, i permessi
# della chiave, la pagina, il credito degli stream, e un ramo di codice mai
# provato.  Rilievo **R3.24**.
#
# ---------------------------------------------------------------------------
# ⛔ NON RICOSTRUISCE, E LO CONTROLLA
#
# B5, B6 e B7 ricostruiscono il server a ogni giro perche' misurano il
# comportamento del CODICE, e una copia stantia darebbe un numero che nel
# binario non c'e'.  ⛔ B13 no: la proprieta' 6 confronta il **sorgente**
# `rcp/rcp.c` con quel che arriva sul filo, e ricostruire non la renderebbe piu'
# vera.
#
# ⚠ Ma allora il binario puo' essere piu' VECCHIO del sorgente, e la proprieta'
#   6 confronterebbe due cose di due epoche — la forma E8 in versione «vecchio
#   e assente hanno lo stesso aspetto».  Quindi il confronto delle date **si fa
#   e si dichiara**, ed e' il controllo che fa uscire 3 invece di misurare.
#
# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE (B0.1, B0.2, B0.3)
#
#  · la porta 7447 dev'essere libera: un server di un altro banco risponderebbe
#    con un altro certificato e con un altro codice, e le sei righe parlerebbero
#    di quello;
#  · ⭐ **B13 non fallisce nessuna autenticazione**: usa sempre le credenziali
#    buone, quindi non consuma il conto di §4.4-bis.  ⚠ Il comando di sblocco
#    **esiste** (`01-b8-sblocca.py`, su `--comando-socket`) e B13 **non lo
#    chiama**: accende un server suo, e il conto vive nel processo.  Dichiarato,
#    perche' B0.3 vuole che si dica quale delle due cure si e' usata.  Se
#    all'inizio arriva `TROPPI_TENTATIVI`, il ban e' di un altro banco: B13 si
#    ferma con l'uscita 5 e lo dice;
#  · il server si accende e si spegne **qui dentro**, e questo azzera il
#    registro delle sessioni e i contatori: cosi' la proprieta' 6 vede una
#    sessione davvero NUOVA e non l'eco del giro precedente (B0.2).
#
# ---------------------------------------------------------------------------
# ⛔ NESSUNA REDIREZIONE ATTORNO A `enter.sh` — si porta via la richiesta di
#    password di sudo e lo script resta appeso per sempre.  Le redirezioni
#    vanno DENTRO le virgolette del comando remoto.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERTDIR=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
# ⛔ Lo stesso file visto da FUORI dal contenitore.  Le due viste dello
#    stesso volume hanno due percorsi, e questo script gira FUORI: un `-f`
#    sul percorso di dentro dice sempre «non c'e'» — cioe' accusa il
#    binario di non essere mai stato costruito mentre e' li'.
SERVER_FUORI="$FUORI/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
IND=192.168.0.2
PORTA=7447
UTENTE=prova
PAROLA=parola-di-prova

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ RILIEVO A7 (e R8.15 prima di lui): `CHI=$(bash "$ENTRA" --root "ss … | grep")`
#    fa avere a «porta libera» e a «il comando non e' stato eseguito» LA STESSA
#    STRINGA VUOTA.  ⚠ E la cura era gia' scritta in questa stessa cartella, da
#    una revisione precedente — `01-b11-guasto.sh:92-129` — e quattro banchi
#    nuovi hanno riscritto la forma non curata.  Qui si copia quella.
#
# ⛔ E si fa stampare lo stato d'uscita DAL COMANDO REMOTO, invece di fidarsi
#    che `enter.sh` lo propaghi: nessuno ha mai verificato che lo faccia
#    (rilievo R5.21, ancora aperto).
USCITA=""
dentro() # $1 = comando remoto.  Uscita in $USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB13-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B13-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B13-FINE=')
	if [ -z "$stato" ]; then
		return 125   # il comando non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

# Chi tiene la porta.  0 = occupata (le righe in $CHI) · 1 = libera · 2 = non
# si sa — e ⛔ «non si sa» non si arrotonda a «libera».
CHI=""
chi_tiene_la_porta() # $1 = -ulnp (UDP) oppure -tlnp (TCP)
{
	local st
	dentro "ss $1"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss $1» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO: `ss` stampa sempre almeno la
	#    propria intestazione.  Se non stampa niente non ha guardato niente, e
	#    uno strumento che non sa vedere quel che c'e' non puo' dire che manchi
	#    qualcosa (`REVIEWER.md` §1 domanda 5).
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss $1» non ha stampato NIENTE, nemmeno l'intestazione:"
		ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

AZIONE=${1:-tutto}
case "$AZIONE" in tutto|elenco) ;; *)
	ko "azione sconosciuta: $AZIONE  (tutto | elenco)"; exit 2 ;;
esac

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b13-proprieta.py --elenco"
	exit 0
fi

# ---------------------------------------------------------------------------
log "1. ⛔ Il binario e' piu' nuovo del sorgente?"
inf "la proprieta' 6 confronta rcp.c con il filo: se il binario e' di ieri,"
inf "sta confrontando due epoche e non due implementazioni"
if [ ! -f "$SERVER_FUORI" ]; then
	ko "⛔ il binario non c'e': $SERVER_FUORI"
	ko "   Non e' «vecchio», e' che non e' mai stato costruito."
	exit 3
fi
if [ "$FUORI/rcp/rcp.c" -nt "$SERVER_FUORI" ]; then
	ko "⛔ il sorgente rcp/rcp.c e' PIU' NUOVO del binario:"
	ls -la --time-style=+%F\ %T "$FUORI/rcp/rcp.c" "$SERVER_FUORI" | sed 's/^/        /'
	ko "   La proprieta' 6 leggerebbe un sorgente che il server non esegue."
	ko "   Cura: bash 01-b5-lancia.sh (o B6, o B7): ricostruiscono."
	exit 3
fi
ok "il binario e' piu' nuovo del sorgente"

# ⛔ E LE DATE NON BASTANO — rilievi A16 e R12.5, 11 agosto 2026.
#
#    «Il file c'e'» e «il file e' quello che ho appena costruito» sono due
#    domande diverse (`LEZIONI.md` §1.9, ottava veste), e le DATE rispondono
#    alla prima.  Caso concreto: si esegue `01-b3-rcp-innesta.py --togli` —
#    cosa che `01-b6-lancia.sh:170` e `01-b8-lancia.sh:112` fanno a ogni giro —
#    e poi si ricompila.  Il binario e' **piu' nuovo** di `rcp/rcp.c` e non
#    contiene una riga di `rcp/rcp.c`: la data dice di si', il contenuto dice
#    di no.
#
# ⭐ Il banco gemello — `01-b6-lancia.sh:197-206`, stessa mano, stessa notte —
#    per la stessa domanda legge TUTT'E DUE le copie e pretende che combacino.
#    Qui si fa lo stesso, e le due copie si passano a `01-b13-proprieta.py`,
#    che le confronta sul campo che la proprieta' 6 giudica.
SORGENTE_RCP=$FUORI/rcp/rcp.c
COMPILATO_RCP=$FUORI/b2/ngtcp2/examples/rcp.c
if [ ! -r "$COMPILATO_RCP" ]; then
	ko "⛔ la COPIA COMPILATA di rcp.c non si legge: $COMPILATO_RCP"
	ko "   Non e' «non c'e' nessun ramo RIPRESA»: e' che la proprieta' 6"
	ko "   giudicherebbe un file che il server non esegue (R12.5)."
	exit 3
fi
IMP_SORG=$(sha256sum "$SORGENTE_RCP" | cut -d' ' -f1)
IMP_COMP=$(sha256sum "$COMPILATO_RCP" | cut -d' ' -f1)
inf "sorgente        $SORGENTE_RCP"
inf "                sha256 ${IMP_SORG:0:16}…"
inf "copia compilata $COMPILATO_RCP"
inf "                sha256 ${IMP_COMP:0:16}…"
if [ "$IMP_SORG" != "$IMP_COMP" ]; then
	inf "⚠ le due copie di rcp.c NON sono identiche.  Non e' un rosso da qui —"
	inf "  l'innesto puo' aggiungere righe alla copia — ma la proprieta' 6 le"
	inf "  confronta sul campo che giudica, e li' devono dire la stessa cosa."
else
	ok "le due copie di rcp.c sono identiche (impronta ${IMP_SORG:0:16}…)"
fi
inf "⚠ l'impronta si annota: fra sei mesi «rcp.c» da solo non dice quale (B0.6)"

# ---------------------------------------------------------------------------
# ⛔ 1-bis.  IL BANCO SI CERTIFICA PRIMA DELLA MISURA — `LEZIONI.md` §1.2.
#
#    E si certifica DA SE': `01-b12-guasti.py` non ci arriva (rilievo A1, il suo
#    guasto per B13 e' di tipo `riga-di-comando` e `--applica` lo rifiuta), e il
#    guasto che ha in catalogo non e' nemmeno quello giusto (rilievo A2).
#    ⚠ Quei due rilievi restano aperti in `01-b12-guasti.py`, che non e' di
#      questo autore: qui si toglie la conseguenza, non la causa.
log "1-bis. ⛔ La certificazione di B13 (guasti costruiti a mano, su copie)"
bash "$ENTRA" --root "python3 -u $DENTRO/01-b13-proprieta.py --certifica \
	--indirizzo $IND --parola $PAROLA"
CERT_ESITO=$?
if [ "$CERT_ESITO" -ne 0 ]; then
	ko "⛔ B13 NON e' certificato (uscita $CERT_ESITO): finche' e' rossa,"
	ko "   un verde delle sei proprieta' non vuol dire niente (LEZIONI.md §1.3)"
	exit 3
fi
ok "B13 e' certificato: i guasti costruiti a mano lo fanno cambiare colore"

# ---------------------------------------------------------------------------
log "2. La porta — tre esiti, non due (occupata · libera · non si sa)"
chi_tiene_la_porta -ulnp
case $? in
0)	ko "la porta $PORTA e' gia' occupata (UDP):"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "fermalo per PID (mai con pkill -f) e rilancia"
	exit 3 ;;
2)	ko "⛔ non so chi tiene la porta $PORTA in UDP, e «non si so» non si"
	ko "   arrotonda a «libera»: misurare da uno stato ignoto vuol dire"
	ko "   misurare la storia della macchina (B0.1)"
	exit 3 ;;
esac
ok "porta $PORTA libera (UDP), e lo strumento ha guardato davvero"

# ⛔ E la TCP si guarda ADESSO, prima di accendere: se qualcuno ascoltasse gia'
#    in TCP su 7447, la proprieta' 4 lo prenderebbe per il nostro server.
#
# ⛔ RILIEVO A14, 11 agosto 2026: qui il ramo «c'e' qualcuno» usava `inf` — una
#    nota — invece di `ko`+`exit`, e IL GIRO PROSEGUIVA.  La proprieta' 4 apre
#    una connessione TCP a questo indirizzo, chiede `GET /` e, se un altro
#    processo risponde, stampa «la pagina si carica: stato 200, N byte» e poi
#    giudica se contiene l'impronta corrente: ⛔ il rosso o il verde che ne
#    esce **parla del server di un altro banco**.  Il caso era nominato — nel
#    commento qui sopra, per esteso — e non fermato: e' la forma «l'indulgenza
#    che nasconde» di `REVIEWER.md` §5.  Nominare un caso non e' verificarlo
#    (B0.1: si dichiara **e** si verifica).
chi_tiene_la_porta -tlnp
case $? in
0)	ko "⛔ qualcuno ascolta gia' in TCP su $PORTA, e NON e' il nostro server:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "   La proprieta' 4 lo prenderebbe per il nostro: caricherebbe la SUA"
	ko "   pagina e giudicherebbe la SUA impronta.  Il verde e il rosso che ne"
	ko "   uscirebbero parlerebbero del server di un altro banco."
	ko "   Fermalo per PID (mai con pkill -f) e rilancia."
	exit 3 ;;
2)	ko "⛔ non so chi ascolta in TCP su $PORTA, e non si arrotonda a «nessuno»"
	exit 3 ;;
esac
ok "nessuno in ascolto in TCP su $PORTA prima dell'accensione"

# ---------------------------------------------------------------------------
log "3. Il server"
rm -f "$FUORI/b13-server.log" "$FUORI/b13-server.pid"
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERTDIR/sessione.key $CERTDIR/sessione.pem < /dev/null > $DENTRO/b13-server.log 2>&1 & echo \$! > $DENTRO/b13-server.pid"
sleep 2
PID=$(cat "$FUORI/b13-server.pid" 2>/dev/null)
# ⛔ `/proc`, non `kill -0`: da utente normale `kill -0` su un processo di root
#    risponde «operazione non permessa», cioe' un errore — e «proibito» non e'
#    «morto».
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server non e' partito.  Il registro dice:"
	[ -f "$FUORI/b13-server.log" ] && sed 's/^/        /' "$FUORI/b13-server.log"
	exit 4
fi
ok "in ascolto, PID $PID"

spegni()
{
	[ -n "${PID:-}" ] || return 0
	bash "$ENTRA" --root "kill $PID 2>/dev/null || true"
}

# ---------------------------------------------------------------------------
log "4. Le sei proprieta'"
inf "⚠ la proprieta' 2 cerca la parola d'ordine in TUTTI i file sotto $DENTRO,"
inf "  compresi i registri lasciati dagli altri banchi: e' voluto — B13.2 dice"
inf "  «tutti i file prodotti dal giro», e il giro e' la fase, non questo script"
bash "$ENTRA" --root \
	"python3 -u $DENTRO/01-b13-proprieta.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --certificati $CERTDIR --prodotti $DENTRO --codice $DENTRO/rcp/rcp.c --codice-compilato $DENTRO/b2/ngtcp2/examples/rcp.c"
E=$?

# ⛔ B0.5, dal SISTEMA: un processo che risponde puo' aver gia' perso i figli,
#    e un processo morto e' un'altra cosa ancora.
if [ -d "/proc/$PID" ]; then
	ok "il processo $PID c'e' ancora (B0.5, dal sistema)"
else
	ko "⛔ IL SERVER E' MORTO durante il giro"
	E=1
fi
spegni

# ---------------------------------------------------------------------------
log "Esito"
case "$E" in
0) ok "⭐ B13: sei proprieta' su sei" ;;
1) ko "⛔ B13: qualche proprieta' NON passa" ;;
2) ko "⛔ B13: il banco ha guardato zero cose — non e' un verde" ;;
3) ko "⛔ B13: alcune proprieta' non si possono giudicare (manca l'imputato,"
   ko "   oppure non si e' potuto guardare).  Vanno nel documento come [?]." ;;
5) ko "⛔ B13: l'indirizzo e' bannato (§4.4-bis) — non e' un rosso delle sei" ;;
*) ko "⛔ B13: uscita $E" ;;
esac
inf "il registro del server resta in $FUORI/b13-server.log"
exit "$E"
