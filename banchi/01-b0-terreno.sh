#!/bin/bash
#
# 01-b0-terreno.sh — ⛔ IL SERVER E' QUELLO CHE CREDO?  Gira SUL SERVER.
#
#   bash 01-b0-terreno.sh innesto     prima di un banco contro :7447
#   bash 01-b0-terreno.sh prodotto    prima di un banco contro :7448
#
# Esce 0 se il terreno regge, 1 se no, 2 se non ha potuto guardare.
# ⛔ E «non ho potuto guardare» NON e' «va bene»: sono tre esiti, non due.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — due volte in una giornata, l'11 agosto 2026
#
# `B0.1` dice che lo stato iniziale si **dichiara e si verifica**.  Questo file
# nasce perche' due volte, nello stesso giorno, un banco e' stato **verde su un
# terreno che non era quello che credevamo** — e in tutt'e due i casi il banco
# non aveva nessun motivo di accorgersene.
#
#   `[M]` **R12-A.45** · `01-b2-ngtcp2-wt-innesta.py --togli` rimette com'erano
#         i file **tracciati** di `examples/`, e fra quelli c'e'
#         `http3_server_proto_codec.cc`, dove vive l'innesto **RCP di B3**.
#         ⇒ Togliere l'innesto B2 porta via anche B3, in silenzio.  Il server
#         ha girato per un'ora **senza RCP**, rimandando indietro i byte del
#         client, e ⛔ **la certificazione di B2 e' passata lo stesso**: la sua
#         sonda legge i parametri QUIC e di RCP non sa niente.
#         ⭐ L'ho preso PER CASO, provando un'altra cosa.
#
#   `[M]` **R12-A.44** · l'utente `prova`, su cui poggiano quattro banchi, non
#         lo creava nessuno script: era stato fatto a mano.
#
# ⭐ La forma e' una sola, e ha un nome nel progetto: **il file c'e'** contro
#    **il file e' quello che ho appena costruito** — gia' pagata su B11 il 10
#    agosto, e su B6 col binario compilato col `CONGEDO` tolto (R12-A.6).
#
# ---------------------------------------------------------------------------
# ⚠ CHE COSA QUESTO CONTROLLO **NON** DIMOSTRA, detto prima
#
# Che il server sia CORRETTO.  Dimostra che e' **quello dichiarato**: i pezzi
# che devono esserci ci sono, il binario e' piu' nuovo dei sorgenti da cui
# dice di venire, e nessun guasto di certificazione e' rimasto addosso.
# ⛔ Un server puo' passare tutto questo ed essere pieno di difetti: e' quel
#    che i banchi cercano.  Qui si controlla soltanto che cerchino nel posto
#    giusto.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
ESEMPI=$FUORI/b2/ngtcp2/examples
BINARIO_INNESTO=$FUORI/b2/ngtcp2/build/examples/bsslserver

BERSAGLIO=${1:-}
case "$BERSAGLIO" in
innesto|prodotto) ;;
*) echo "uso: $0 {innesto|prodotto}" >&2; exit 2 ;;
esac

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'
GRIGIO=$'\033[0m'; NETTO=$'\033[1m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }

GUAI=0
IGNOTI=0
GUARDATI=0

# ⛔ conta() distingue TRE esiti: il file non c'e' · c'e' e il conto e' N ·
#    non ho potuto leggerlo.  Stampa il numero, oppure «?».
#
# ⛔⭐ E LA PRIMA STESURA SBAGLIAVA PROPRIO QUI, nella stessa forma curata
#     stamattina su S1b (rilievo A31): `grep -c` esce **1** quando non trova
#     niente — che non e' un errore, e' la risposta «zero» — e il mio
#     `|| printf '?'` ci appiccicava un `?` DOPO lo zero gia' stampato.
#     Usciva la stringa «0\n?», e ogni controllo «non deve esserci»
#     dichiarava tracce di guasto su un file pulito: cinque falsi rossi in un
#     colpo, dentro il file che esiste per impedire i falsi rossi.
#     ⭐ Lo stato d'uscita di `grep` va letto: 0 = trovato · 1 = non trovato ·
#        ≥2 = non ho potuto leggere.  Sono tre, e solo il terzo e' «?».
conta() # $1 = file, $2 = ago
{
	local n s
	if [ ! -f "$1" ]; then printf '?\n'; return; fi
	n=$(grep -c -F -- "$2" "$1" 2>/dev/null)
	s=$?
	if [ "$s" -ge 2 ] || [ -z "$n" ]; then printf '?\n'; else printf '%s\n' "$n"; fi
}

# almeno() # $1 = descrizione, $2 = file, $3 = ago, $4 = minimo
almeno()
{
	local n
	GUARDATI=$((GUARDATI + 1))
	n=$(conta "$2" "$3")
	if [ "$n" = "?" ]; then
		dub "⛔ $1: non ho potuto leggere «$(basename "$2")»"
		dub "   ⚠ e «non ho potuto guardare» non e' «va bene»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	if [ "$n" -ge "$4" ]; then
		ok "$1: $n occorrenze (attese ≥ $4)"
	else
		ko "⛔ $1: $n occorrenze, ne servono almeno $4"
		GUAI=$((GUAI + 1))
	fi
}

# nessuno() — un ago che NON deve esserci (i guasti di certificazione)
nessuno()
{
	local n
	GUARDATI=$((GUARDATI + 1))
	n=$(conta "$2" "$3")
	if [ "$n" = "?" ]; then
		dub "⛔ $1: non ho potuto leggere «$(basename "$2")»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	if [ "$n" -eq 0 ]; then
		ok "$1: nessuna traccia"
	else
		ko "⛔ $1: $n tracce RIMASTE ADDOSSO al codice"
		ko "   Un guasto dimenticato avvelena ogni misura successiva, e"
		ko "   nessuno sapra' che c'era."
		GUAI=$((GUAI + 1))
	fi
}

# ⛔ IL BINARIO E' PIU' NUOVO DEI SORGENTI?  E' l'altra meta' di «il file c'e'»:
#    un sorgente curato e un binario vecchio sono la trappola di R12-A.6, dove
#    il sorgente era sano e il binario bugiardo.
piu_nuovo() # $1 = binario, $2.. = sorgenti
{
	local bin=$1; shift
	local vecchi=0 f
	GUARDATI=$((GUARDATI + 1))
	if [ ! -f "$bin" ]; then
		ko "⛔ il binario non c'e': $bin"
		GUAI=$((GUAI + 1))
		return
	fi
	for f in "$@"; do
		[ -f "$f" ] || continue
		if [ "$f" -nt "$bin" ]; then
			ko "⛔ «$(basename "$f")» e' PIU' NUOVO del binario:"
			ko "   il server in esecuzione non contiene quel sorgente"
			vecchi=$((vecchi + 1))
		fi
	done
	if [ "$vecchi" -eq 0 ]; then
		ok "il binario e' piu' nuovo di tutti i sorgenti che dichiara"
	else
		GUAI=$((GUAI + 1))
	fi
}

printf '\n%s== ⛔ Il terreno: il server «%s» e'"'"' quello che credo?%s\n' \
	"$NETTO" "$BERSAGLIO" "$GRIGIO"

if [ "$BERSAGLIO" = innesto ]; then
	# ── I due innesti, e vivono TUTT'E DUE in server.cc ──────────────────
	# ⚠ E' il punto in cui si sono pestati i piedi: `--togli` dell'uno
	#   rimette com'era un file che l'altro aveva scritto.
	almeno "innesto RCP (B3) nel codec"    "$ESEMPI/http3_server_proto_codec.cc" "rcp_"        20
	almeno "innesto WebTransport (B2) nel codec" "$ESEMPI/http3_server_proto_codec.cc" "REMOTIX B2" 5
	almeno "il ban lato ospite (B3) in server.cc" "$ESEMPI/server.cc"            "REMOTIX B3"  5
	almeno "i parametri di trasporto (B2) in server.cc" "$ESEMPI/server.cc"      "REMOTIX B2"  1

	# ── I tre file che B3 copia dentro examples/ ─────────────────────────
	for f in rcp.c rcp.h autenticazione.c; do
		GUARDATI=$((GUARDATI + 1))
		if [ -f "$ESEMPI/$f" ]; then
			ok "examples/$f c'e'"
		else
			ko "⛔ examples/$f MANCA: l'innesto RCP non e' completo"
			GUAI=$((GUAI + 1))
		fi
	done

	# ── ⭐ E la copia dev'essere IL SORGENTE, non una copia stantia ──────
	GUARDATI=$((GUARDATI + 1))
	if [ -f "$ESEMPI/rcp.c" ] && [ -f "$FUORI/rcp/rcp.c" ]; then
		A=$(md5sum "$ESEMPI/rcp.c" | cut -d' ' -f1)
		B=$(md5sum "$FUORI/rcp/rcp.c" | cut -d' ' -f1)
		if [ "$A" = "$B" ]; then
			ok "examples/rcp.c e' identico a rcp/rcp.c ($A)"
		else
			ko "⛔ examples/rcp.c NON e' rcp/rcp.c:"
			ko "   compilato: $A"
			ko "   sorgente : $B"
			ko "   ⇒ il server misura una versione che nessuno sta leggendo"
			GUAI=$((GUAI + 1))
		fi
	else
		dub "⛔ non ho potuto confrontare rcp.c: uno dei due non c'e'"
		IGNOTI=$((IGNOTI + 1))
	fi

	nessuno "guasti di B12 nel codec"  "$ESEMPI/http3_server_proto_codec.cc" "REMOTIX B12 GUASTO"
	nessuno "guasti di B12 in rcp.c"   "$ESEMPI/rcp.c"                       "REMOTIX B12 GUASTO"
	nessuno "guasti di B12 in server.cc" "$ESEMPI/server.cc"                 "REMOTIX B12 GUASTO"
	nessuno "guasti di B11 nel codec"  "$ESEMPI/http3_server_proto_codec.cc" "REMOTIX B11 GUASTO"
	nessuno "guasti di B11 in rcp.c"   "$ESEMPI/rcp.c"                       "REMOTIX B11 GUASTO"

	piu_nuovo "$BINARIO_INNESTO" \
		"$ESEMPI/http3_server_proto_codec.cc" "$ESEMPI/server.cc" \
		"$ESEMPI/rcp.c" "$ESEMPI/autenticazione.c"
else
	# ── Il prodotto ─────────────────────────────────────────────────────
	# ⛔ `src/rcp.c` e `banchi/rcp/rcp.c` DEVONO restare identici byte per
	#    byte: e' l'invariante su cui poggia il fatto che i due server
	#    parlino lo stesso protocollo.
	GUARDATI=$((GUARDATI + 1))
	if [ -f "$FUORI/remotix/rcp.c" ] && [ -f "$FUORI/rcp/rcp.c" ]; then
		A=$(md5sum "$FUORI/remotix/rcp.c" | cut -d' ' -f1)
		B=$(md5sum "$FUORI/rcp/rcp.c" | cut -d' ' -f1)
		if [ "$A" = "$B" ]; then
			ok "remotix/rcp.c e' identico a rcp/rcp.c ($A)"
		else
			ko "⛔ i due rcp.c NON sono piu' identici — l'invariante e' rotta"
			ko "   prodotto: $A"
			ko "   banchi  : $B"
			GUAI=$((GUAI + 1))
		fi
	else
		dub "⛔ non ho potuto confrontare i due rcp.c"
		IGNOTI=$((IGNOTI + 1))
	fi
	nessuno "guasti di B12 in remotix/rcp.c" "$FUORI/remotix/rcp.c" "REMOTIX B12 GUASTO"
	# ⚠ Il binario del prodotto lo costruisce il suo Makefile: qui si
	#   controlla solo che non sia piu' vecchio del sorgente.
	if [ -f "$FUORI/remotix/build/remotix" ]; then
		piu_nuovo "$FUORI/remotix/build/remotix" "$FUORI/remotix/rcp.c"
	else
		dub "⚠ il binario del prodotto non e' dove lo cercavo: non lo giudico"
		IGNOTI=$((IGNOTI + 1))
	fi
fi

# ---------------------------------------------------------------------------
# ⛔ IL DENOMINATORE — `LEZIONI.md` §1.9 regola 6.  «Tutti quelli provati sono
#    andati bene» e' vero anche quando i provati sono zero.
printf '\n    == quel che questo controllo ha davvero guardato\n'
inf "controlli fatti:      $GUARDATI"
printf '    %s%3d%s  ⛔ guai\n' "$ROSSO" "$GUAI" "$GRIGIO"
printf '    %s%3d%s  ⚠ IGNOTI (non ho potuto guardare)\n' "$GIALLO" "$IGNOTI" "$GRIGIO"

if [ "$GUARDATI" -eq 0 ]; then
	ko "⛔ ZERO controlli: questo giro non dice niente, e «terreno buono»"
	ko "   sarebbe una bugia"
	exit 2
fi
if [ "$GUAI" -gt 0 ]; then
	printf '\n    %s⛔ IL TERRENO NON REGGE: non lanciare banchi su questo server.%s\n' \
		"$ROSSO" "$GRIGIO"
	ko "Quel che ne uscirebbe non parlerebbe del prodotto."
	exit 1
fi
if [ "$IGNOTI" -gt 0 ]; then
	printf '\n    %s⚠ il terreno regge SU QUEL CHE HO POTUTO GUARDARE%s\n' \
		"$GIALLO" "$GRIGIO"
	inf "$IGNOTI controlli non si sono potuti fare: non sono un verde"
	exit 1
fi
printf '\n    %s⭐ il terreno regge: %d controlli su %d%s\n' \
	"$VERDE" "$GUARDATI" "$GUARDATI" "$GRIGIO"
exit 0
