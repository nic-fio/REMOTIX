#!/bin/bash
#
# 01-b12-lancia.sh — gira SUL SERVER.  B12: la certificazione dei banchi.
#
#   bash /media/REMOTIX/src/01-b12-lancia.sh              i guasti leggeri
#   bash /media/REMOTIX/src/01-b12-lancia.sh B4 B9 C2     solo questi
#   bash /media/REMOTIX/src/01-b12-lancia.sh tutti        anche quelli che
#                                                         ricostruiscono
#   bash /media/REMOTIX/src/01-b12-lancia.sh elenco       il catalogo
#   bash /media/REMOTIX/src/01-b12-lancia.sh registro     chi e' certificato
#
# ---------------------------------------------------------------------------
# ⛔ IL GIRO E' TRE ESECUZIONI, NON UNA — e l'ordine non e' negoziabile
#
#   1. SANO    il banco gira sul codice buono e **dev'essere verde**.  ⛔ Senza
#              questo passo, «e' diventato rosso» non vuol dire niente: un banco
#              gia' rosso lo sarebbe anche col guasto, e la certificazione
#              sarebbe una tautologia;
#   2. GUASTO  si innesta il guasto e il banco **deve diventare rosso**, ⛔ **e
#              la sua uscita deve nominare la cosa giusta**: un guasto che rompe
#              la compilazione rende rosso qualunque banco e certifica ZERO;
#   3. RISANO  si toglie il guasto e il banco **deve tornare verde**.  ⛔ Senza,
#              «il banco vede il guasto» e «il banco e' rimasto rotto» hanno lo
#              stesso aspetto — e il guasto resta addosso al codice per il
#              prossimo che passa.
#
# ⭐ Il VERDETTO non sta qui: sta in `01-b12-guasti.py --giudica`, che vede i
#    tre passi insieme.  Questo script raccoglie **numeri**, non giudizi (B0.4).
#
# ---------------------------------------------------------------------------
# ⛔ LE USCITE SI CATTURANO DENTRO LE VIRGOLETTE, MAI ATTORNO A `enter.sh`
#
# Serve leggere l'uscita del banco per cercarci la marca.  ⛔ E una redirezione
# **attorno** a `enter.sh` si porta via la richiesta di password di sudo, e lo
# script resta ad aspettare una domanda che nessuno vede — tre volte in una sera
# il 10 agosto 2026.  Quindi ogni banco si lancia come
# `enter.sh --root "python3 … > file 2>&1"`, e il file lo si legge dopo.
#
# ⚠ Da cui una conseguenza: i banchi si lanciano **chiamando il loro programma**,
#   non il loro `01-bX-lancia.sh` — quelli girano fuori dal contenitore e non si
#   possono redirigere.  L'accensione del server la fa questo script, con la
#   stessa riga di comando che usano loro.
#
# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE (B0.1, B0.3)
#
#  · la porta 7447 dev'essere libera all'inizio;
#  · ⛔ **B12 accende e spegne il server a ogni passo**, e questo azzera il conto
#    di §4.4-bis, che vive nel processo.  ⚠ Il comando di sblocco **esiste**
#    (`01-b8-sblocca.py` su `--comando-socket`) e B12 **non lo chiama**: lo
#    dichiara qui, perche' B0.3 vuole che si sappia quale delle due cure ha
#    rimesso in piedi la macchina;
#  · ⚠ e il guasto si toglie **anche se il giro muore**: il `trap` lo rimette a
#    posto e ricostruisce, perche' un server che mente non deve sopravvivere.
#    ⛔ *Fino all'11 agosto 2026 questa riga era falsa e il rilievo R12-A.6 l'ha
#    misurata: `ripulisci()` faceva `spegni` e `--togli` e **non chiamava mai
#    `ricostruisci`**.  Ctrl-C durante il passo 2/3 di B7 rimetteva a posto
#    `examples/rcp.c` e lasciava `build/examples/bsslserver` compilato col
#    `CONGEDO` tolto: sorgente sano e **binario bugiardo**.  Il banco dopo —
#    B6, che confronta i `#define` fra sorgente e copia compilata — li trovava
#    d'accordo e misurava un server che mente.  E' la trappola «il file c'e'» /
#    «il file e' quello che ho appena costruito», gia' pagata su B11.*
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
ESITI=$DENTRO/b12-esiti.jsonl
ESITI_FUORI=$FUORI/b12-esiti.jsonl
GUASTI=$DENTRO/01-b12-guasti.py

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ---------------------------------------------------------------------------
# ⛔ LA SENTINELLA: «vuoto» non e' «zero» — rilievo R12-A.7, e la cura era gia'
#    scritta in questa stessa cartella, in `01-b11-guasto.sh:92-129`.
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` diceva «porta
# libera» in tre casi opposti: la porta e' davvero libera · `ss` non c'e' nel
# contenitore · `enter.sh` non ha eseguito il comando.  ⛔ E in questo file
# quella riga stava **venticinque righe sotto il commento che descrive quella
# stessa trappola** — una sostituzione di comando attorno a `enter.sh`, che si
# porta via la richiesta di password di sudo, dentro il banco che esiste per
# certificare gli altri.
#
# ⭐ Qui il comando remoto stampa da se' il proprio stato d'uscita: se la riga
#    `B12-FINE` non arriva, il comando non e' arrivato in fondo — e questo si
#    distingue da «e' andato e non ha trovato niente».
#
# ⚠ E LA SOSTITUZIONE DI COMANDO RESTA, ED E' LECITA SOLO QUI SOTTO: la prima
#   chiamata di questo script — `bash "$ENTRA" --root "true"`, qui sopra — e'
#   quella che si prende la richiesta di password, e da li' in poi le
#   credenziali di sudo sono valide.  ⛔ Il divieto vale per le REDIREZIONI
#   attorno a `enter.sh` e per qualunque cattura fatta **prima** di quella
#   riga; catturare dopo e' quel che fa anche `01-b11-guasto.sh`.
# ⚠ E cosi' la misura non poggia piu' sul fatto che `enter.sh` propaghi il
#   codice d'uscita del comando che esegue, che nessuno ha mai verificato
#   (rilievo R5.21, ancora aperto).
USCITA=""
dentro() # $1 = comando remoto.  Uscita in $USCITA, stato = quello del comando
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB12-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B12-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B12-FINE=')
	if [ -z "$stato" ]; then
		return 125   # il comando non e' arrivato in fondo: non e' uno zero
	fi
	return "$stato"
}

# Chi tiene la porta.  0 = occupata (le righe in $CHI) · 1 = libera · 2 = non
# si sa, e ⛔ «non si sa» non si arrotonda a «libera».
CHI=""
chi_tiene_la_porta() # $1 = "-ulnp" (UDP) oppure "-tlnp" (TCP)
{
	local opz=${1:--ulnp} st
	dentro "ss $opz"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss $opz» non ha risposto dentro il contenitore (uscita $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO: `ss` stampa sempre almeno la
	#    propria intestazione.  Se non stampa niente non ha guardato niente, e
	#    uno strumento che non sa vedere quel che c'e' non puo' dire che manchi
	#    qualcosa (`REVIEWER.md` §1 domanda 5).
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss $opz» non ha stampato NIENTE, nemmeno l'intestazione:"
		ko "   lo strumento e' muto, e il suo silenzio non e' una porta libera"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

case "${1:-leggeri}" in
elenco)   bash "$ENTRA" --root "python3 $GUASTI --elenco"; exit 0 ;;
registro) bash "$ENTRA" --root "python3 $GUASTI --registro"; exit 0 ;;
leggeri)  SIGLE="C2 B13" ;;
tutti)    SIGLE="C2 B13 B7" ;;
*)        SIGLE="$*" ;;
esac
inf "sigle da provare: $SIGLE"
# ⛔ E B9 E B4 NON SONO IN QUESTO ELENCO, e va detto invece di essere
#    dimenticato.
#
#    `01-b9-letture.py` legge `RCP.md`, e ⛔ **su questa macchina `RCP.md` non
#    c'e'**: qui arrivano i banchi, non i documenti.  Lanciandolo di qui esce 4
#    — «non ho potuto leggere i testi» — e la certificazione registrerebbe un
#    rosso della causa sbagliata, cioe' esattamente quel che B12 esiste per
#    impedire.
#
# ⛔ E B4 e' lo stesso caso, scoperto l'11 agosto 2026: `01-b4-lancia.py` e
#    `01-b4-registrazioni.py` **non stanno in `/srv/src`**, quindi
#    `prepara_copia()` non trova gli originali e il giro sano esce 2 —
#    «python3: can't open file».  *E' esattamente quel che il registro delle
#    21:19 ha annotato come «B4 non certificato»: un rosso che non parlava del
#    banco.*  ⭐ Tutt'e due si certificano **sulla macchina dove stanno i
#    documenti e i loro banchi**, con lo stesso `01-b12-guasti.py`:
#
#      python3 banchi/01-b12-guasti.py --verifica B9
#      python3 banchi/01-b12-copie/01-b9-letture.py      # dev'essere 0
#      python3 banchi/01-b12-guasti.py --applica  B9
#      python3 banchi/01-b12-copie/01-b9-letture.py      # dev'essere 3
#      python3 banchi/01-b12-guasti.py --togli    B9
#
#    e per B4, con `01-b12-copie/01-b4-lancia.py 01-b12-copie/b4-registrazioni`
#    al posto del lettore (0 → 1 → 0).
inf "⚠ B9 e B4 non sono fra queste: si certificano dove stanno i loro file"

# ---------------------------------------------------------------------------
# ⛔⭐ RILIEVO R12-A.31, 11 agosto 2026 — L'AVVERTENZA QUI SOPRA ERA UN
#     CONSIGLIO, E CHI LA IGNORAVA OTTENEVA UN ROSSO PULITO.
#
# `bash 01-b12-lancia.sh B4 B9 C2` stampava la riga qui sopra e **poi lanciava
# B9 lo stesso**.  `[M]` 11 agosto: B9 e' uscito **4** — «senza i testi non c'e'
# nessun inventario da verificare», perche' `RCP.md` **su questa macchina non
# esiste** — e il verdetto ha scritto **«B9 NON certificato»**.
#
# ⛔ E' la forma opposta del falso verde, ed e' altrettanto cara: un banco sano
#    marchiato come non certificato manda a cercare un difetto che non c'e', e
#    intanto tiene il conto delle certificazioni fermo per una ragione che non
#    e' del banco.  ⚠ Il registro se lo porta dietro con una data, e chi lo
#    rilegge fra un mese non ha modo di sapere che quel rosso parlava di un file
#    mancante.
#
# ⭐ La cura non e' ripetere l'avvertenza piu' forte: e' **guardare se i file su
#    cui la certificazione poggia ci sono**, e rifiutarsi.  «Non posso provarlo
#    qui» e «l'ho provato e non passa» sono due fatti diversi, e B12 esiste per
#    non confonderli — e' il rilievo R12-A.4 applicato a se stesso.
# ---------------------------------------------------------------------------
RIFIUTATE=""
RESTA=""
for S in $SIGLE; do
	MANCA=$(bash "$ENTRA" --root \
	    "python3 $GUASTI --provabile $S 2>/dev/null" 2>/dev/null \
	    | tr -d '\r' | sed -n 's/^MANCA //p' | tr '\n' ' ')
	if [ -n "$MANCA" ]; then
		ko "⛔ «$S» NON si prova qui: manca $MANCA"
		ko "   Non e' «non certificato»: e' «non certificabile su questa"
		ko "   macchina».  Si certifica dove stanno i suoi file."
		RIFIUTATE="$RIFIUTATE $S"
	else
		RESTA="$RESTA $S"
	fi
done
if [ -n "$RIFIUTATE" ]; then
	inf "⛔ rifiutate qui:$RIFIUTATE   ·   restano:${RESTA:- —}"
	SIGLE=$RESTA
fi
if [ -z "${SIGLE// /}" ]; then
	ko "⛔ nessuna sigla provabile su questa macchina: non lancio niente."
	ko "   ⚠ E NON scrivo nel registro: un giro che non ha provato niente"
	ko "   non e' un giro con zero certificati."
	exit 0
fi

rm -f "$ESITI_FUORI"

PID=""
accendi() # $1 = base del certificato (sessione | pagina), $2 = etichetta
{
	local base=$1 et=$2
	rm -f "$FUORI/b12-$et.log" "$FUORI/b12-$et.pid"
	bash "$ENTRA" --root \
		"nohup env LD_LIBRARY_PATH=$LIBS $SERVER --timeout=120s $IND $PORTA $CERT/$base.key $CERT/$base.pem < /dev/null > $DENTRO/b12-$et.log 2>&1 & echo \$! > $DENTRO/b12-$et.pid"
	sleep 2
	PID=$(cat "$FUORI/b12-$et.pid" 2>/dev/null)
	# ⛔ `/proc`, non `kill -0`: il server e' di root e questo script no.
	if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
		ko "il server non e' partito ($base):"
		[ -f "$FUORI/b12-$et.log" ] && sed 's/^/        /' "$FUORI/b12-$et.log"
		PID=""
		return 1
	fi
	ok "server acceso col certificato «$base», PID $PID"
	return 0
}

spegni()
{
	[ -n "$PID" ] || return 0
	bash "$ENTRA" --root "kill $PID 2>/dev/null || true"
	local g=0
	while [ -d "/proc/$PID" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g + 1)); done
	PID=""
}

ricostruisci()
{
	rm -f "$FUORI/b12-compila.log"
	if ! bash "$ENTRA" --root \
		"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b12-compila.log 2>&1"; then
		ko "⛔ la compilazione e' fallita:"
		[ -f "$FUORI/b12-compila.log" ] && tail -20 "$FUORI/b12-compila.log" | sed 's/^/        /'
		# ⛔ E questo NON e' «il banco e' diventato rosso»: e' che non c'e'
		#    nessun binario da provare.  Chi non distingue le due cose
		#    certifica dodici banchi con una compilazione rotta.
		return 1
	fi
	ok "ricostruito"
	return 0
}

# ⛔ La ripulitura vale piu' del verdetto: un guasto lasciato addosso al codice
#    avvelena ogni misura successiva, e nessuno sapra' che c'era.
#
# ⛔ E RIMETTERE IL SORGENTE NON BASTA: VA RICOSTRUITO — rilievo R12-A.6.
#
#    `--togli` rimette a posto `examples/rcp.c`; il binario in
#    `build/examples/bsslserver` resta quello **compilato col guasto dentro**.
#    Sorgente sano e binario bugiardo e' peggio di tutt'e due guasti: il banco
#    successivo legge il sorgente, lo trova pulito — B6 confronta proprio i
#    `#define` fra sorgente e copia compilata e li trova d'accordo — e misura
#    un server che mente.  ⚠ E' la stessa forma pagata su B11 il 10 agosto
#    2026: «il file c'e'» e «il file e' quello che ho appena costruito».
SIGLA_APERTA=""
COSTA_APERTA=""
# ⛔ E LE DUE VARIABILI SI AZZERANO SOLO QUANDO IL LAVORO E' FATTO: una
#    ripulitura che si dichiara riuscita e' peggio di una che non c'e', perche'
#    il `trap` non ci riprova.  ⭐ Questa funzione e' anche il passo 3/3 del
#    giro: la ripulitura e il ritorno al sano sono la stessa operazione, e
#    tenerne due copie voleva dire che una delle due sarebbe invecchiata.
ripulisci()
{
	spegni
	[ -n "$SIGLA_APERTA" ] || return 0
	local st=0
	log "⛔ Si toglie il guasto «$SIGLA_APERTA»"
	bash "$ENTRA" --root "python3 $GUASTI --togli $SIGLA_APERTA --certificati $CERT"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ IL GUASTO NON E' STATO TOLTO: si rilancia a mano"
		ko "   ⛔ e il binario resta quello col guasto dentro: NON SI MISURA"
		ko "     niente su questa macchina finche' non e' rimesso a posto"
		return "$st"
	fi
	# ⛔ E ADESSO IL BINARIO.  Senza questa riga il commento in cima a questo
	#    file era falso, e lo e' stato per un giorno intero.
	if [ "$COSTA_APERTA" = ricostruisce ]; then
		inf "⚠ il sorgente e' sano ma il binario e' ancora quello col guasto:"
		inf "  si ricostruisce, o resta un server che mente"
		if ricostruisci; then
			ok "⭐ sorgente sano E binario ricostruito: niente sopravvive al giro"
		else
			ko "⛔ LA RICOSTRUZIONE E' FALLITA: il binario in"
			ko "   $SERVER porta ancora il guasto «$SIGLA_APERTA»."
			ko "   ⛔ Ogni misura fatta su questa macchina da adesso e' avvelenata."
			return 1
		fi
	fi
	SIGLA_APERTA=""; COSTA_APERTA=""
	return 0
}
trap ripulisci EXIT

# ---------------------------------------------------------------------------
# gira <sigla> <passo>   → scrive una riga in $ESITI
#
# ⛔ Ogni banco ha la sua riga di comando, e ciascuna e' quella che il banco
#    userebbe da se': un banco lanciato in modo diverso da come vive non e'
#    quel banco.
gira()
{
	local sigla=$1 passo=$2 u=0 marca="" uscita_file="$DENTRO/b12-uscita.txt"
	local fuori_file="$FUORI/b12-uscita.txt"
	rm -f "$fuori_file"
	case "$sigla" in
	B4)
		bash "$ENTRA" --root \
			"python3 $DENTRO/01-b12-copie/01-b4-lancia.py $DENTRO/01-b12-copie/b4-registrazioni > $uscita_file 2>&1"
		u=$? ;;
	B9)
		bash "$ENTRA" --root \
			"python3 $DENTRO/01-b12-copie/01-b9-letture.py > $uscita_file 2>&1"
		u=$? ;;
	C2)
		# ⚠ C2 vuole il server acceso per due scene e spento per due: il suo
		#   `01-c2-lancia.sh` lo sa fare, e gira FUORI dal contenitore.  Qui si
		#   accetta di non poter redirigere e si legge la marca dagli esiti su
		#   file, che C2 scrive per conto suo.
		bash "$FUORI/01-c2-lancia.sh" tutto "$DENTRO/01-b12-copie/01-c2-diagnosi.py"
		u=$?
		cp -f "$FUORI/c2-esiti.json" "$fuori_file" 2>/dev/null ;;
	B13)
		# ⛔ QUI C'ERA `[ "$passo" = guasto ] && base=pagina`, ED ERA CODICE
		#    MORTO — rilievi R12-A.1 e R12-A.2.  Morto due volte:
		#      · non ci si arrivava mai (il guasto era di tipo
		#        `riga-di-comando`, `--applica` lo rifiutava e il giro faceva
		#        `continue` prima del passo 2/3);
		#      · e se ci si fosse arrivati avrebbe costruito **il guasto
		#        sbagliato**: `proprieta_1` confronta le impronte dei due FILE
		#        su disco, non il certificato presentato sul filo, quindi
		#        accendere il server con `pagina.pem` non le avrebbe fatte
		#        combaciare e la marca non sarebbe uscita mai.
		# ⭐ Adesso il guasto e' sui due file (tipo `copia-di-file`) e il server
		#    si accende sempre con `sessione`, come vive.
		accendi sessione "b13-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b13-proprieta.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --certificati $CERT --prodotti $DENTRO > $uscita_file 2>&1"
			u=$?
		fi
		spegni ;;
	B6)
		# ⛔⭐ B6 SI PUO' CERTIFICARE, E L'OBIEZIONE IN CATALOGO NON REGGEVA
		#     — rilievo R12-A.32, 11 agosto 2026.
		#
		# La nota diceva: *«il guasto va innestato in `rcp/rcp.c` e non nella
		# copia di `examples/` — `01-b6-lancia.sh` ricopia il sorgente a ogni
		# giro e cancellerebbe il guasto, e il confronto fra i due `#define`
		# che B6 fa al passo 2 lo vedrebbe comunque»*.
		#
		# ⭐ Tutt'e due le meta' parlano di `01-b6-lancia.sh`, e **B12 non lo
		#    usa**: qui i banchi si chiamano dal loro programma (la ragione sta
		#    in testa a questo file — le uscite vanno catturate dentro le
		#    virgolette di `enter.sh`).  Ne' la ricopiatura ne' il confronto
		#    fra i `#define` girano da questa parte.
		#
		# ⚠ E VA DETTO CHE COSA QUESTA CERTIFICAZIONE **NON** COPRE, invece di
		#   lasciarlo credere: certifica `01-b6-tetti.py`, cioe' i casi sul
		#   filo.  Il confronto sorgente/binario e il richiamo allo sblocco di
		#   §4.4-bis stanno nel lanciatore e restano **non certificati**.
		#
		# ⛔ E i tetti del codice si LEGGONO, non si scrivono a mano: passare
		#    5000 al passo col guasto sarebbe mentire al banco proprio dove il
		#    guasto vive.
		local tc="" nome b
		for coppia in "CIAO:TETTO_CIAO" "CREDENZIALI:TETTO_CREDENZIALI" "ATTACCA:TETTO_ATTACCA"; do
			nome=${coppia%%:*}
			b=$(sed -n "s/^#define ${coppia##*:}[[:space:]]\{1,\}\([0-9]\{1,\}\).*/\1/p" \
			    "$FUORI/b2/ngtcp2/examples/rcp.c" | head -1)
			[ -n "$b" ] && tc="$tc${tc:+,}$nome=$b"
		done
		inf "tetti letti dal sorgente compilato: ${tc:-⛔ NESSUNO}"
		if [ -z "$tc" ]; then
			ko "⛔ non ho letto nessun tetto da examples/rcp.c: non lancio B6"
			ko "   ⚠ con i tetti ignoti il banco misurerebbe contro niente"
			u=99
		else
			accendi sessione "b6-$passo" || { u=99; }
			if [ "$u" -eq 0 ]; then
				bash "$ENTRA" --root \
					"python3 -u $DENTRO/01-b6-tetti.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --fase sani --idle 120000 --tetti-codice $tc > $uscita_file 2>&1"
				u=$?
			fi
			spegni
		fi ;;
	B7)
		accendi sessione "b7-$passo" || { u=99; }
		if [ "$u" -eq 0 ]; then
			bash "$ENTRA" --root \
				"python3 -u $DENTRO/01-b7-congedo.py --bersaglio innesto --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registro $DENTRO/b12-b7-$passo.log --pagina $DENTRO/01-b11-pagina.html > $uscita_file 2>&1"
			u=$?
		fi
		spegni ;;
	*)
		ko "⛔ non so come lanciare il banco «$sigla»: il guasto e' catalogato"
		ko "   ma non eseguito, e va detto invece di contarlo"
		return 9 ;;
	esac

	# ⛔ L'uscita del banco si mostra sempre, anche quando e' verde: un giro di
	#    certificazione in cui si vede solo il numero non permette a nessuno di
	#    accorgersi che il rosso era di un'altra causa.
	if [ -f "$fuori_file" ]; then
		tail -25 "$fuori_file" | sed 's/^/        /'
	else
		inf "⚠ nessuna uscita catturata per «$sigla» passo «$passo»: la marca"
		inf "  non si potra' cercare, e la certificazione lo contera'"
	fi
	printf '%s\n' "$u" > "$FUORI/b12-ultima-uscita.txt"
	inf "«$sigla» passo «$passo»: uscita $u"
	return "$u"
}

# ---------------------------------------------------------------------------
# ⛔ La marca si cerca QUI, in un posto solo, e con un `grep` che sa fallire.
# ⛔ E QUESTE DUE DOMANDE NON PASSANO DA `enter.sh`, ED E' LA TRAPPOLA CHE
#    QUESTO STESSO FILE DESCRIVE IN CIMA — pagata di nuovo il 10 agosto 2026,
#    dentro il banco che esiste per certificare gli altri.
#
#    `X=$(bash enter.sh --root "…")` e' una **sostituzione di comando attorno a
#    enter.sh**: si porta via la richiesta di password di sudo, e il giro resta
#    appeso per sempre su una domanda che nessuno vede.  Il giro delle 22:50 si
#    e' fermato esattamente li', subito dopo aver innestato il guasto — cioe'
#    **col guasto addosso al codice**, che e' il peggior punto in cui fermarsi.
#
# ⭐ La cura: il catalogo si interroga **fuori dal contenitore**.  `01-b12-*` e i
#    file di `$FUORI` sono gli stessi di `$DENTRO`, e python3 c'e' anche qui.
# ⛔ E LA MARCA SI CERCA IN TUTT'E TRE I PASSI, NON SOLO NEL GUASTO —
#    rilievo R12-A.3.  Il criterio ha due meta':
#
#      · l'uscita ROSSA deve nominare la marca;
#      · ⛔ e il giro SANO **non la deve gia' nominare**.
#
#    Qui la seconda meta' non c'era: `annota "$S" sano "$U" false` scriveva
#    `false` **a mano**, cioe' dichiarava senza guardare.  Cosi' B7, la cui
#    marca era «CONGEDO» — 37 volte nell'uscita sana — e' stato certificato il
#    10 agosto alle 21:19 senza che nessuno avesse verificato niente.
#    ⭐ La riga che chiude il buco esiste, scritta la stessa notte, in
#    `01-b8-cronometro.py:1571`: `gia = frase in testo_sano`.  Qui il confronto
#    lo fa `--giudica`, che vede i tre passi insieme (B0.4): questo script
#    raccoglie il fatto — «la marca c'era, si' o no» — per ciascun passo.
marca_vista() # $1 = sigla
{
	local ago
	ago=$(python3 "$FUORI/01-b12-guasti.py" --marca "$1" 2>/dev/null | tr -d '\r' | tail -1)
	if [ -z "$ago" ]; then
		# ⚠ Nessuna marca dichiarata: «non l'ho vista» sarebbe una risposta a
		#   una domanda che non e' stata posta.  Il rifiuto lo scrive
		#   `--giudica`, che sa che il campo e' vuoto.
		echo "false"
		return
	fi
	if [ -f "$FUORI/b12-uscita.txt" ] && grep -qF "$ago" "$FUORI/b12-uscita.txt"; then
		echo "true"
	else
		echo "false"
	fi
}

annota() # $1 = sigla, $2 = passo, $3 = uscita, $4 = marca_vista
{
	printf '{"sigla":"%s","passo":"%s","uscita":%s,"marca_vista":%s}\n' \
		"$1" "$2" "$3" "$4" >> "$ESITI_FUORI"
}

# ⛔ E IL BANCO CHE NON SI E' POTUTO LANCIARE HA UNA RIGA SUA — R12-A.4.
#    Senza, finiva in `set(GUASTI) - set(per_sigla)`, cioe' fra i «mai
#    provati»: e «non ho una riga di comando per lanciarlo» e «nessuno l'ha mai
#    guardato» hanno due cure diverse.
annota_saltato() # $1 = sigla, $2 = perche'
{
	printf '{"sigla":"%s","passo":"saltato","uscita":9,"marca_vista":false,"perche":"%s"}\n' \
		"$1" "$2" >> "$ESITI_FUORI"
}

# ---------------------------------------------------------------------------
log "Lo stato iniziale: la porta $PORTA"
chi_tiene_la_porta -ulnp
case $? in
0)	ko "la porta $PORTA e' gia' occupata:"
	printf '%s\n' "$CHI" | sed 's/^/        /'
	ko "   Fermalo per PID (mai con pkill -f) e rilancia."
	exit 3 ;;
1)	ok "porta $PORTA libera (e «ss» ha parlato: non e' un silenzio)" ;;
*)	ko "⛔ non si e' potuto sapere chi tiene la porta $PORTA:"
	ko "   e «non si sa» non si arrotonda a «libera» — dodici certificazioni"
	ko "   poggerebbero su un server che potrebbe non essere il nostro"
	exit 3 ;;
esac

for S in $SIGLE; do
	# ⛔ LA VERIFICA DELL'APPIGLIO VIENE PRIMA DEL GIRO SANO, E NON E' UN
	#    DETTAGLIO D'ORDINE.  Due ragioni, e la seconda l'ho pagata:
	#      · non ha senso spendere un giro sano per un guasto che non si
	#        potrebbe innestare;
	#      · ⛔ e' `--verifica` a costruire le COPIE dei banchi in
	#        `01-b12-copie/`.  Chiamandola dopo, il giro sano cercava un file
	#        che non esisteva ancora e usciva 2 — «python3: can't open file» —
	#        cioe' un rosso che non parlava ne' del banco ne' del guasto.
	log "=== $S — 0/3  lo stato di partenza che il guasto vuole"
	bash "$ENTRA" --root "python3 $GUASTI --verifica $S --certificati $CERT"
	COSTA=$(python3 "$FUORI/01-b12-guasti.py" --costa "$S" | tr -d '\r' | tail -1)
	# ⚠ Niente apostrofi dentro un `${…:-…}`: la shell li tratta come apici e
	#   il resto del file finisce dentro una stringa aperta.  E' la quinta
	#   veste della trappola delle shell annidate, gia' pagata in
	#   `01-b6-lancia.sh` su una riga d'errore che nessuno provava.
	inf "costa: ${COSTA:-NON LETTO}"

	log "=== $S — 1/3  il giro SANO (dev'essere verde)"
	gira "$S" sano; U=$?
	if [ "$U" -eq 9 ]; then
		inf "«$S» saltato: nessuna riga di comando — resta NON CERTIFICATO"
		annota_saltato "$S" "questo orchestratore non ha una riga di comando per lanciare il banco: catalogato e non eseguito"
		continue
	fi
	# ⛔ E LA MARCA SI GUARDA ANCHE QUI, invece di scrivere `false` a mano.
	#    Un `false` dichiarato senza guardare e' la stessa forma del rosso
	#    dichiarato senza misurare — e su B7 e' costato una certificazione
	#    finta (R12-A.3).
	M_SANO=$(marca_vista "$S")
	annota "$S" sano "$U" "$M_SANO"
	if [ "$M_SANO" = true ]; then
		ko "⛔ IL GIRO SANO DICE GIA' LA MARCA DI «$S»: qualunque cosa succeda"
		ko "   nel passo 2/3, vedere quella stringa nel rosso non provera'"
		ko "   niente.  Il verdetto lo scrivera' --giudica; il giro prosegue"
		ko "   perche' il resto delle misure vale lo stesso."
	fi

	log "=== $S — 2/3  si innesta il guasto"
	bash "$ENTRA" --root "python3 $GUASTI --applica $S --certificati $CERT"
	if [ $? -ne 0 ]; then
		ko "⛔ il guasto «$S» non si e' innestato: il passo non si fa"
		ko "   ⚠ e NON si annota un rosso: un guasto non innestato lascia il"
		ko "     banco verde, e chi legge concluderebbe l'opposto"
		continue
	fi
	SIGLA_APERTA=$S
	COSTA_APERTA=$COSTA
	if [ "$COSTA" = ricostruisce ]; then
		ricostruisci || { ko "⛔ senza binario non si misura niente"; ripulisci; continue; }
	fi
	gira "$S" guasto; U=$?
	annota "$S" guasto "$U" "$(marca_vista "$S")"

	log "=== $S — 3/3  si toglie il guasto e si torna al SANO"
	if ! ripulisci; then
		ko "⛔ il guasto «$S» non e' stato tolto (o il binario non e' stato"
		ko "   ricostruito): il terzo passo non vale, e ⛔ IL GIRO SI FERMA QUI."
		ko "   ⚠ Non e' prudenza: qualunque banco misurato dopo starebbe"
		ko "     guardando un codice che porta ancora il guasto di «$S», e il"
		ko "     suo rosso — o il suo verde — parlerebbe di un altro."
		break
	fi
	gira "$S" risano; U=$?
	annota "$S" risano "$U" "$(marca_vista "$S")"
done

# ---------------------------------------------------------------------------
log "Il verdetto — e lo da' chi vede i tre passi insieme (B0.4)"
bash "$ENTRA" --root "python3 $GUASTI --giudica $ESITI"
E=$?
inf "gli esiti restano in $ESITI_FUORI"
exit "$E"
