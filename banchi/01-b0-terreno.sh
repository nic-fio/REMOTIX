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
#
# ---------------------------------------------------------------------------
# ⛔⭐ E QUESTO FILE HA AVUTO ADDOSSO PROPRIO IL DIFETTO CHE ESISTE PER
#     IMPEDIRE — difetto **D5**, 12 agosto 2026.
#
# La riga 235 cercava il binario del prodotto in `remotix/build/remotix`, che
# **non e' mai esistito**: `src/Makefile` dichiara `NOME := remotix` e lo
# costruisce accanto ai sorgenti, e `src/costruisci.sh` fa `make -C "$QUI"`
# dopo aver cancellato `"$QUI/remotix"`.  ⇒ Il `[ -f ... ]` cadeva **sempre**
# nel ramo «non lo giudico», e quel controllo era un **IGNOTO fisso**: non
# controllava niente, e nessuno lo leggeva piu'.
#
# ⛔ E' la forma **E8** — «vuoto» e «proibito» hanno lo stesso aspetto —
#    applicata allo strumento che dovrebbe impedirla agli altri.  Il percorso
#    non e' stato indovinato una seconda volta: e' letto in `src/Makefile` e
#    in `src/costruisci.sh`, ed e' lo stesso che dichiara gia'
#    `01-b0-bersaglio.sh` (`B_ESE="$B0_DENTRO/remotix/remotix"`).
#
# ⭐ Da cui le quattro cose che questo giro ha cambiato, e ognuna risponde a
#    «quale ingresso lo farebbe diventare ROSSO?»:
#
#   1. il percorso vero, `$SORG/remotix`             ⇒ rosso se il binario e'
#                                                       piu' vecchio di un .c
#   2. il binario che MANCA e' un **guaio**, non un ignoto — il ramo che lo
#      scusava e' sparito, e giudica `piu_nuovo()` come sull'innesto
#   3. si confronta con **tutti** i sorgenti compilati, non col solo `rcp.c`:
#      con `rcp.c` da solo un `main.c` piu' nuovo del binario restava VERDE
#   4. ⚠ **il posto e' uno solo per albero, ma gli alberi NON sono uno**:
#      `[M]` 12 agosto 2026, cinque `remotix` eseguibili sotto `/media/REMOTIX/src`
#      (il prodotto di casa, `01-p5-copia-7522`, `01-b12-copie/p1-remotix`,
#      `01-b12-copie/p5-remotix`, `coder-r12/src`).  ⇒ l'albero si **dichiara**
#      con `SORG=`, e se dentro l'albero i binari fossero due il controllo lo
#      **dice** invece di sceglierne uno.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
ESEMPI=$FUORI/b2/ngtcp2/examples
BINARIO_INNESTO=$FUORI/b2/ngtcp2/build/examples/bsslserver

# ⛔ L'albero del prodotto si DICHIARA, come in `01-p1-prodotto.sh` (SORG):
#    il binario sta sempre accanto ai suoi sorgenti, ma di alberi ce n'e' piu'
#    d'uno su questa macchina e il bersaglio «prodotto» e' quello di casa,
#    cioe' il server della 7448.  Chi vuole giudicarne un altro lo nomina.
SORG=${SORG:-$FUORI/remotix}
BINARIO_PRODOTTO=$SORG/remotix

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

# ⛔ IL POSTO E' UNO SOLO?  E' l'altra meta' della cura di D5: sapere DOVE sta
#    il binario non basta se il binario puo' stare in due posti.
#
#    Dentro UN albero il posto e' uno per costruzione — `src/Makefile` mette
#    `$(NOME)` accanto ai sorgenti e `costruisci.sh` cancella quello vecchio
#    prima — ⛔ ma un `build/remotix` lasciato li' da una costruzione fuori
#    albero, o una copia dimenticata, rimetterebbe in piedi esattamente la
#    domanda che D5 ha pagato: *quale dei due sta girando?*
#    ⭐ Qui non si sceglie: si contano e si dicono.  L'ESISTENZA la giudica
#       `piu_nuovo()`; questo controlla soltanto che non ce ne sia PIU' D'UNO.
posto_unico() # $1 = albero, $2 = il binario che sto per giudicare
{
	local albero=$1 atteso=$2 trovati s n
	GUARDATI=$((GUARDATI + 1))
	if [ ! -d "$albero" ]; then
		dub "⛔ l'albero del prodotto non c'e': $albero"
		dub "   ⚠ e «non ho potuto guardare» non e' «va bene»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	# ⚠ Niente `2>/dev/null`: se `find` non ha potuto guardare lo dice, e un
	#   «non ho potuto» non deve avere la faccia di un «ce n'e' uno solo».
	trovati=$(find "$albero" -maxdepth 2 -type f -name remotix -perm -u+x)
	s=$?
	if [ "$s" -ne 0 ]; then
		dub "⛔ non ho potuto elencare i binari sotto «$albero» (find: $s)"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	if [ -z "$trovati" ]; then n=0; else n=$(printf '%s\n' "$trovati" | wc -l); fi
	if [ "$n" -le 1 ]; then
		ok "un solo posto dove puo' stare il binario: $atteso"
		[ "$n" -eq 0 ] && inf "(oggi non c'e' nessun binario: lo giudica il controllo qui sotto)"
	else
		ko "⛔ $n binari «remotix» dentro lo stesso albero:"
		printf '        %s\n' $trovati
		ko "   ⇒ non so quale sta girando, e sceglierne uno sarebbe D5 daccapo."
		ko "   Si butta quello di troppo, o si dichiara l'albero con SORG=."
		GUAI=$((GUAI + 1))
	fi
}

# ===========================================================================
# ⛔⭐ I GUASTI DI B12 SI CERCANO DOVE B12 LI METTE — lacuna L2, 12 agosto 2026.
#
# ⛔ QUEL CHE C'ERA PRIMA, E PERCHE' ERA PEGGIO DI NIENTE.
#
# Questo file aveva quattro righe scritte a mano:
#
#     nessuno "guasti di B12 nel codec"        examples/http3_server_proto_codec.cc
#     nessuno "guasti di B12 in rcp.c"         examples/rcp.c
#     nessuno "guasti di B12 in server.cc"     examples/server.cc
#     nessuno "guasti di B12 in remotix/rcp.c" remotix/rcp.c        ← ⛔ QUESTA
#
# L'ultima **non poteva diventare rossa in nessun caso**: `01-b12-guasti.py`
# non innesta in `remotix/rcp.c` e non ci ha mai innestato — per progetto
# dichiarato, perche' *«non si guasta mai un originale»* (la sua §«LA CARTELLA
# DELLE COPIE»).  ⇒ Un controllo verde per costruzione, che GUARDATI contava
# come uno dei controlli fatti.  ⛔ E' peggio di un controllo assente: chi
# legge «nessuna traccia» crede che qualcuno abbia guardato.
#
# ⚠ E le prime tre erano vere ma **parziali**: dei quindici guasti del catalogo
#   ne coprivano cinque.  I posti che nessuno guardava — `[M]` 12 agosto 2026,
#   letti dal catalogo, non dedotti — erano `01-b12-copie/p1-remotix/pagina.c`,
#   `01-b12-copie/p5-remotix/pagina.c`, `sera-b10-remotix/autenticazione.c`,
#   le tre copie di banchi in `01-b12-copie/` e `01-p5-copia-7522/pagina.html`.
#
# ⭐ LA CURA: l'elenco non si ricopia, SI CHIEDE AL CATALOGO.  Un guasto nuovo
#    con un bersaglio nuovo entra qui dentro da solo; una riga ricopiata a mano
#    invecchia in silenzio, ed e' la forma esatta di R12-A.45 — il file che uno
#    script rimetteva com'era e che nessun altro guardava.
#
# ⚠ E la marca si legge di la' anche lei (`MARCA`): cercare una stringa
#   ricopiata qui vorrebbe dire che il giorno in cui B12 la cambia questo
#   controllo non trova piu' niente **e diventa verde**.
# ===========================================================================
CATALOGO=$QUI/01-b12-guasti.py

# Ritorna: prima riga = la MARCA · righe dopo = «SIGLE<TAB>percorso».
posti_dei_guasti()
{
	python3 - "$CATALOGO" <<'PY'
import importlib.util
import os
import sys

s = importlib.util.spec_from_file_location("b12", sys.argv[1])
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
print(m.MARCA)
ordine, di_chi = [], {}
for sigla in sorted(m.GUASTI):
    g = m.GUASTI[sigla]
    # ⛔ `copia-di-file` (oggi: B13) SOVRASCRIVE un file intero — un certificato
    #    PEM — e non ci lascia dentro nessuna stringa da cercare.  Li' il
    #    residuo lo giudica l'impronta che `--togli` rimette, non questo
    #    setaccio: cercarci la marca sarebbe un controllo verde per
    #    costruzione, cioe' il difetto che questa cura toglie.
    if g["costa"] == "copia-di-file":
        continue
    d = os.path.realpath(m.risolvi(g["dove"]))
    if d not in di_chi:
        ordine.append(d)
        di_chi[d] = []
    di_chi[d].append(sigla)
for d in ordine:
    print("%s\t%s" % (",".join(di_chi[d]), d))
PY
}

guasti_rimasti_addosso()
{
	local righe s marca n riga sigle percorso
	local posti=0 guardati=0 sporchi=0 assenti=0

	righe=$(posti_dei_guasti)
	s=$?
	# ⛔ Niente `2>/dev/null` qui sopra: se il catalogo non si carica, l'errore
	#    di Python si vede, e questo controllo si dichiara IGNOTO invece di
	#    setacciare zero file e chiamarlo «nessuna traccia».
	if [ "$s" -ne 0 ] || [ -z "$righe" ]; then
		GUARDATI=$((GUARDATI + 1))
		dub "⛔ non ho potuto chiedere a 01-b12-guasti.py dove innesta (uscita $s)"
		dub "   ⚠ e zero file setacciati non e' «nessun guasto rimasto addosso»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	marca=$(printf '%s\n' "$righe" | head -1)

	# ⭐ IL CONTROLLO POSITIVO, SULLO STESSO STRUMENTO (`LEZIONI.md` §1.9
	#    regola 2).  `conta()` sa trovare la marca in un file che ce l'ha di
	#    sicuro?  Se non la trova, ogni «nessuna traccia» qui sotto vale zero —
	#    ed e' la stessa mattina in cui una ricerca non trovava nemmeno le 133
	#    applicazioni di sistema.
	GUARDATI=$((GUARDATI + 1))
	local finto
	finto=$(mktemp) || { dub "⛔ nessun file temporaneo: setaccio non certificato"; IGNOTI=$((IGNOTI + 1)); return; }
	printf 'una riga qualunque\n/* %s prova */\n' "$marca" >"$finto"
	n=$(conta "$finto" "$marca")
	rm -f "$finto"
	if [ "$n" = "?" ] || [ "$n" -lt 1 ]; then
		dub "⛔ il setaccio NON trova la marca «$marca» in un file che ce l'ha:"
		dub "   ogni «nessuna traccia» qui sotto sarebbe un verde vuoto."
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	ok "il setaccio sa trovare «$marca» dove c'e' (controllo positivo)"

	while IFS=$'\t' read -r sigle percorso; do
		[ -n "${percorso:-}" ] || continue
		posti=$((posti + 1))
		if [ ! -e "$percorso" ]; then
			# ⛔ ASSENTE NON E' IGNOTO, E QUI LA DIFFERENZA E' DIMOSTRABILE.
			#    I bersagli di B12 sono COPIE che `prepara_copia()` rifa' da
			#    zero a ogni giro: finche' la copia non esiste, non puo'
			#    portare addosso niente.  ⇒ non e' «non ho potuto guardare»,
			#    e non deve costare un IGNOTO che fermerebbe ogni giro.
			assenti=$((assenti + 1))
			continue
		fi
		GUARDATI=$((GUARDATI + 1))
		guardati=$((guardati + 1))
		n=$(conta "$percorso" "$marca")
		if [ "$n" = "?" ]; then
			dub "⛔ non ho potuto leggere «$percorso» (guasti $sigle)"
			dub "   ⚠ e «non ho potuto guardare» non e' «va bene»"
			IGNOTI=$((IGNOTI + 1))
			continue
		fi
		if [ "$n" -ne 0 ]; then
			ko "⛔ $n tracce di guasto RIMASTE ADDOSSO a «$percorso»"
			ko "   e' il bersaglio di: $sigle"
			ko "   Un guasto dimenticato avvelena ogni misura successiva, e"
			ko "   nessuno sapra' che c'era.  Si toglie con:"
			ko "     python3 $CATALOGO --togli ${sigle%%,*}"
			GUAI=$((GUAI + 1))
			sporchi=$((sporchi + 1))
		fi
	done <<< "$(printf '%s\n' "$righe" | tail -n +2)"

	# ⛔ IL DENOMINATORE (`LEZIONI.md` §1.9 regola 4): «nessuna traccia» non e'
	#    un dato finche' non dice DENTRO QUANTI FILE.
	if [ "$sporchi" -eq 0 ] && [ "$guardati" -gt 0 ]; then
		ok "nessun guasto di B12 rimasto addosso: $guardati file setacciati su"
		ok "   $posti bersagli dichiarati dal catalogo ($assenti non esistono oggi)"
	elif [ "$guardati" -eq 0 ]; then
		dub "⛔ nessuno dei $posti bersagli del catalogo esiste su questa macchina:"
		dub "   questo controllo non ha guardato niente, e non e' un verde"
		IGNOTI=$((IGNOTI + 1))
	fi
	inf "i bersagli assenti sono copie che 01-b12-guasti.py rifa' a ogni giro:"
	inf "  una copia che non c'e' non puo' portarsi addosso un guasto"
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

	# ⚠ I guasti di **B12** non stanno piu' qui: li setaccia
	#   `guasti_rimasti_addosso()`, in fondo a questo file, chiedendo al
	#   catalogo dove vanno davvero — e i suoi bersagli non sono tre, sono
	#   nove (lacuna L2, 12 agosto 2026).  Quelli di **B11** restano scritti a
	#   mano perche' li innesta un altro programma,
	#   `01-b11-guasto-innesta.py`, che di catalogo non ne ha uno.
	nessuno "guasti di B11 nel codec"  "$ESEMPI/http3_server_proto_codec.cc" "REMOTIX B11 GUASTO"
	nessuno "guasti di B11 in rcp.c"   "$ESEMPI/rcp.c"                       "REMOTIX B11 GUASTO"
	# ⛔ ⭐ E IL TERZO FILE DI B11, che fino al 12 agosto 2026 non guardava
	#    nessuno: `01-b11-guasto-innesta.py` scrive in TRE file — `rcp.c`,
	#    `http3_server_proto_codec.cc` e `http3_server_proto_codec.h` (il
	#    membro `bool b11_fatto_{false}; // ⚠ REMOTIX B11 GUASTO`).  Un
	#    `--togli` che lasciasse indietro l'intestazione era invisibile a
	#    questo strumento: la stessa forma di R12-A.45, che e' il motivo per
	#    cui questo file esiste.
	nessuno "guasti di B11 nell'intestazione del codec" \
		"$ESEMPI/http3_server_proto_codec.h" "REMOTIX B11 GUASTO"

	# ⛔ Le INTESTAZIONI stanno fra i sorgenti che il binario dichiara: senza,
	#    un `touch examples/rcp.h` — o l'intestazione del codec riscritta da
	#    `--togli` — lasciava questo controllo VERDE su un binario stantio.
	#    E' lo stesso difetto di D5 sull'altro bersaglio, dove si confrontava
	#    il solo `rcp.c`.
	piu_nuovo "$BINARIO_INNESTO" \
		"$ESEMPI/http3_server_proto_codec.cc" "$ESEMPI/http3_server_proto_codec.h" \
		"$ESEMPI/server.cc" \
		"$ESEMPI/rcp.c" "$ESEMPI/rcp.h" "$ESEMPI/autenticazione.c"
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
	# ⛔ QUI C'ERA `nessuno "guasti di B12 in remotix/rcp.c"`, E NON POTEVA
	#    DIVENTARE ROSSA: `01-b12-guasti.py` non innesta negli originali, per
	#    progetto dichiarato.  La ragione per esteso sta accanto a
	#    `guasti_rimasti_addosso()`, che adesso setaccia i bersagli VERI — e li
	#    setaccia su tutt'e due i bersagli di questo script, perche' un guasto
	#    dimenticato avvelena le misure di chiunque, non solo quelle
	#    dell'innesto.

	# ── ⛔ IL BINARIO DEL PRODOTTO — la cura di D5 ───────────────────────
	inf "albero del prodotto: $SORG   (si cambia con SORG=<percorso>)"
	posto_unico "$SORG" "$BINARIO_PRODOTTO"

	# ⛔ TUTTI i sorgenti che entrano nel binario, non il solo `rcp.c`:
	#    `src/Makefile` ne compila DIECI, e con il solo `rcp.c` un `main.c`
	#    piu' nuovo del binario lasciava il controllo VERDE.  Le
	#    intestazioni ci stanno perche' il Makefile le dichiara come
	#    prerequisiti degli oggetti.
	#
	# ⚠ `pagina.html` e `remotix.pam` NON ci stanno, e la ragione va detta:
	#    il server li legge all'AVVIO (`pagina_apri()`), non li compila
	#    dentro.  Uno di loro piu' nuovo del binario non e' un binario
	#    stantio, e metterlo qui sarebbe un rosso puntato sull'imputato
	#    sbagliato.
	#
	# ⛔ E il binario che MANCA e' un GUAIO, non un ignoto — e' il ramo che
	#    D5 usava per non guardare niente.  `piu_nuovo()` lo sa dire da se',
	#    ed e' quel che gia' fa sul bersaglio «innesto».
	piu_nuovo "$BINARIO_PRODOTTO" \
		"$SORG"/*.c "$SORG"/*.h "$SORG/Makefile"
fi

# ── ⛔ I GUASTI DI B12, CERCATI DOVE B12 LI METTE (lacuna L2) ───────────────
#    Fuori dall'if apposta: il bersaglio dice quale SERVER si sta per usare,
#    non quali file possono essere sporchi.
guasti_rimasti_addosso

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
