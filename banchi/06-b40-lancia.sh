#!/bin/bash
#
# 06-b40-lancia.sh — ⭐ IL CLIENTE DI PROVA, PER DAVVERO, SUL PORTATILE.
#
#   VENV=... CERTIFICATI=... LAV=... bash banchi/06-b40-lancia.sh
#
#   uscita 0  tutti i casi hanno dato l'esito dichiarato PRIMA del giro
#   uscita 1  ⛔ almeno uno no — e si dice quale, e che cosa ha dato invece
#   uscita 2  il banco non si e' potuto far girare (ambiente)
#
# ---------------------------------------------------------------------------
# ⛔ LA `[?]` CHE QUESTO BANCO CHIUDE, E QUELLA CHE NON CHIUDE
#
# `fasi/06-la-tela-e-la-vista.md` §7.2: *«`aioquic` non e' installato sul
# portatile (il cliente si prova in locale solo con surrogati, e il banco lo
# dichiara)»*.  ⇒ Con `aioquic` in un ambiente virtuale e uno **specchio**
# locale (`06-b40-specchio.py`), il cliente si esercita per davvero: QUIC vero,
# HTTP/3 vero, WebTransport vero, i byte in una socket.
#
# ⛔ E quel che NON chiude, che va letto per primo: **lo specchio non e' il
#    prodotto**.  Nessun numero preso qui dice qualcosa sul server in C.  Qui
#    l'imputato e' il **cliente** — e l'arbitro e' `01-b4-validatore.py`, che
#    e' certificato da solo (49 registrazioni + 19 mutazioni) e non ha bisogno
#    di nessun server.
#
# ---------------------------------------------------------------------------
# ⛔ OGNI CASO DICHIARA IL SUO ATTESO PRIMA, E DICHIARA **CHI** LO DEVE VEDERE
#
# Un guasto che nessuno dei due — cliente o arbitro — vedesse sarebbe un buco,
# e senza scrivere chi lo deve vedere non ci si accorgerebbe di averlo.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV=${VENV:?serve VENV=/percorso/dell/ambiente-virtuale (con aioquic)}
CERTIFICATI=${CERTIFICATI:?serve CERTIFICATI=/percorso/dei/certificati}
LAV=${LAV:-/tmp/06-b40}
PORTA=${PORTA:-7742}
PY=$VENV/bin/python

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
BENE=0
FATTI=0
GIUSTI=0

# ---------------------------------------------------------------------------
log "0. Il terreno — si VERIFICA, non si spera"
[ -x "$PY" ] || { ko "manca l'interprete «$PY»"; exit 2; }
V=$("$PY" -c 'import aioquic,sys;print(aioquic.__version__)' 2>&1) \
  || { ko "aioquic non si importa da «$PY»: $V"; exit 2; }
inf "aioquic $V   ($PY)"
for f in sessione.pem sessione.key; do
	[ -r "$CERTIFICATI/$f" ] || { ko "manca $CERTIFICATI/$f"; exit 2; }
done
inf "certificati: $CERTIFICATI"
n=$(ss -uln 2>/dev/null | grep -c ":$PORTA\b")
[ "$n" -eq 0 ] || { ko "la porta UDP $PORTA e' gia' occupata"; exit 2; }
mkdir -p "$LAV" || exit 2
inf "carico: $(uptime | sed 's/.*average/media/')"
ok "ambiente a posto — porta $PORTA libera, lavoro in $LAV"

PID=
ferma() { [ -n "$PID" ] && kill "$PID" 2>/dev/null; PID=; sleep 0.3; }
trap 'ferma' EXIT

# ---------------------------------------------------------------------------
# caso <nome> <guasto> <uscita-cliente> <uscita-arbitro> <regola> <chi> <atteso> -- <opzioni del cliente>
#
# ⛔ `regola` NON e' un lusso: «l'arbitro dice rosso» non e' un atteso.  Il
#    banco pretende **quale regola** e' stata accusata, o un rosso preso per la
#    ragione sbagliata passerebbe per un verde del banco — che e' la forma con
#    cui `04-b31` aveva perso G8 (l'ancora scaduta).  Vuoto = non si pretende.
caso()
{
	local nome=$1 guasto=$2 uc=$3 ua=$4 regola=$5 chi=$6 atteso=$7; shift 8
	log "$nome"
	inf "⛔ ATTESO, dichiarato prima: $atteso"
	inf "   lo deve vedere: $chi   (cliente=$uc · arbitro=$ua)"
	FATTI=$((FATTI + 1))

	rm -f "$LAV/$nome.rcpreg" "$LAV/$nome.txt" "$LAV/$nome-specchio.txt"
	CERTIFICATI="$CERTIFICATI" "$PY" "$QUI/06-b40-specchio.py" \
	    --porta "$PORTA" --guasto "$guasto" \
	    > "$LAV/$nome-specchio.txt" 2>&1 &
	PID=$!
	sleep 1

	if ! kill -0 "$PID" 2>/dev/null; then
		ko "lo specchio non si e' acceso — il suo registro:"
		sed 's/^/    | /' "$LAV/$nome-specchio.txt"
		BENE=1
		return
	fi

	timeout 60 "$PY" -u "$QUI/01-b3-cliente.py" \
	    --indirizzo 127.0.0.1 --porta "$PORTA" \
	    --utente prova --parola parola-di-prova \
	    --registra "$LAV/$nome.rcpreg" "$@" \
	    > "$LAV/$nome.txt" 2>&1
	local e=$?
	sed 's/^/    | /' "$LAV/$nome.txt"
	ferma

	local g=99
	if [ -f "$LAV/$nome.rcpreg" ]; then
		"$PY" "$QUI/01-b4-validatore.py" "$LAV/$nome.rcpreg" \
		    > "$LAV/$nome-arbitro.txt" 2>&1
		g=$?
		sed -n '/^   /p' "$LAV/$nome-arbitro.txt" | tail -6 | sed 's/^/    > /'
	else
		ko "nessuna traccia: l'arbitro non ha niente da giudicare"
	fi

	local reg_ok=0
	if [ -n "$regola" ]; then
		if grep -qF "$regola" "$LAV/$nome-arbitro.txt" 2>/dev/null; then
			inf "la regola accusata e' «$regola», come dichiarato"
		else
			ko "⛔ l'arbitro NON ha accusato «$regola»: rosso per la ragione sbagliata"
			reg_ok=1
		fi
	fi

	if [ "$e" = "$uc" ] && [ "$g" = "$ua" ] && [ "$reg_ok" -eq 0 ]; then
		ok "⭐ cliente $e · arbitro $g — come dichiarato"
		GIUSTI=$((GIUSTI + 1))
	else
		ko "⛔ cliente $e (atteso $uc) · arbitro $g (atteso $ua)"
		BENE=1
	fi
}

# ---------------------------------------------------------------------------
# ⭐ IL CASO SANO — e va per primo, o i guasti non hanno un metro
caso "1-sano" sano 0 0 "" "nessuno: dev'essere pulito" \
     "il giro pieno CIAO→ECCOMI→CREDENZIALI→(1 s)→AMMESSO→ATTACCA→SESSIONE→ADATTA_TELA→TELA(ADATTATA,1264x800)→VISTA, e l'arbitro dice CONFORME" -- \
     --adatta 1264x800 --vista 640x400 --resta 1

caso "2-tela-a-caldo" sano 0 0 "" "nessuno: dev'essere pulito" \
     "due coppie ADATTA_TELA/TELA in ordine, la seconda a sessione viva" -- \
     --adatta 1264x800 --adatta 1600x900@1 --resta 1

caso "3-fuori-limiti" sano 0 0 "" "nessuno: e' la strada che §7.1 prevede" \
     "ADATTA_TELA(8000x4320) e TELA(RIFIUTATA, MISURA_FUORI_LIMITI), tela invariata" -- \
     --adatta 8000x4320 --resta 1

# ---------------------------------------------------------------------------
# ⛔ I GUASTI — uno per volta, e ciascuno con il suo giudice dichiarato
caso "4-ammesso-subito" ammesso-subito 1 0 "" "il CLIENTE (§4.4-bis)" \
     "AMMESSO in meno di un secondo: il cliente esce 1 e lo dice.  ⚠ L'arbitro NON lo vede — §11.1 non registra il tempo, ed e' la [?] delle coordinate in volo vista da un'altra faccia" -- \
     --adatta 1264x800 --resta 1

caso "5-tela-muta" tela-muta 5 0 "" "il CLIENTE (uscita 5)" \
     "nessun TELA all'ADATTA_TELA: il cliente esce 5.  ⚠ E l'arbitro dice CONFORME, perche' una richiesta senza risposta e' «in volo», non una violazione" -- \
     --adatta 1264x800 --attesa-tela 2 --resta 1

# ⛔ E QUESTI TRE NON MANDANO NESSUN `ADATTA_TELA`, ed e' la parte che conta:
#    T1 di §7.1 dice «nessuna ADATTA_TELA e' senza risposta», e con una coppia
#    gia' chiusa l'arbitro accuserebbe **T2** (§6.2) — un rosso giusto per la
#    regola sbagliata.  ⇒ Le due regole si esercitano in due casi diversi.
caso "6-tela-non-sollecitata" tela-non-sollecitata 0 1 "TELA non sollecitato" \
     "l'ARBITRO (T1, §7.1)" \
     "un TELA spontaneo, a sessione viva e senza nessuna ADATTA_TELA: T1.  ⛔ E' il caso che PRIMA DEL 21 AGOSTO non poteva esistere — il cliente non registrava i messaggi che nessuno aspettava" -- \
     --resta 3

caso "7-tela-dispari" tela-dispari 0 1 "dispari" "l'ARBITRO (T6, §4.5)" \
     "TELA(ADATTATA, 1281x800): il lato dispari e' vietato dai limiti normativi di §4.5" -- \
     --adatta 1264x800 --resta 1

caso "8-tela-oltre-massima" tela-oltre-massima 0 1 "video.misura_massima" \
     "l'ARBITRO (§4.5)" \
     "TELA(ADATTATA, 7680x4320) a un client che ha dichiarato video.misura_massima 3840x2160" -- \
     --adatta 1264x800 --resta 1

caso "9-tela-dopo-vista" tela-dopo-vista 0 1 "subito dopo una VISTA" \
     "l'ARBITRO (V3, §7.1)" \
     "un TELA dopo la VISTA, senza nessuna ADATTA_TELA: §7.1 dice che la VISTA NON DEVE far cambiare la tela" -- \
     --vista 640x400 --resta 3

caso "10-tela-in-piu" tela-in-piu 0 1 "secondo TELA per una sola ADATTA_TELA" \
     "l'ARBITRO (T2, §6.2)" \
     "due TELA per una sola ADATTA_TELA: §6.2 vuole che «l'n-esimo TELA risponda all'n-esima ADATTA_TELA»" -- \
     --adatta 1264x800 --resta 1

# ---------------------------------------------------------------------------
log "Esito"
inf "⛔ e si rilegge: lo SPECCHIO non e' il prodotto.  Qui l'imputato e' il"
inf "   CLIENTE, e quel che si e' chiuso e' «aioquic non c'e' sul portatile»."
inf "$GIUSTI su $FATTI casi con l'esito dichiarato prima"
if [ "$BENE" -eq 0 ]; then
	ok "⭐ il cliente di prova gira per davvero in locale, e ogni guasto"
	ok "   e' visto da chi era stato dichiarato prima del giro"
else
	ko "⛔ almeno un caso non ha dato l'esito dichiarato"
fi
exit "$BENE"
