#!/bin/bash
#
# 01-b2-lancia-sonda.sh — ⚠ gira SULLA MACCHINA DI CHI GUARDA, non sul server.
#
#   bash banchi/01-b2-lancia-sonda.sh            i due motori
#   bash banchi/01-b2-lancia-sonda.sh firefox    uno solo
#
# ---------------------------------------------------------------------------
# PERCHE' QUI E NON SUL SERVER
#
# ⛔ I browser stanno qui.  Sul server c'e' solo Firefox, e Chrome non c'e'
#    affatto: le misure del 9 agosto — Chrome 151 e Firefox 140, tutt'e due
#    «X11; Linux x86_64» — sono state fatte da questa parte del filo.  ⭐ Ed e'
#    anche la posizione giusta: il prodotto ha il browser su una macchina e il
#    server su un'altra, e una misura fatta tutta dentro il server non
#    proverebbe la parte di rete.
#
# La pagina si serve da **127.0.0.1**: WebTransport pretende un contesto
# sicuro, e `localhost` lo e' senza certificati.  Cosi' quel che si misura e'
# la SESSIONE, non il clic dell'utente su un avviso.
#
# ---------------------------------------------------------------------------
# CHE COSA MISURA, E CHE COSA NON MISURA
#
# ⭐ **Il criterio di B2**: la sessione WebTransport si apre da un browser
#    vero, verso il nostro server minimo su `ngtcp2`, con l'impronta del
#    certificato pubblicata nella pagina e **nessun avviso**.
#
# ⚠ Non misura il percorso sbagliato: quello lo fa `01-b2-lancia-wt.sh` col
#   cliente di prova, e li' il controllo che dice NO c'e'.
#
# ⛔ E l'esito NON lo legge chi guarda: la pagina lo spedisce da se' a
#    `01-b2-raccogli.py`, che lo scrive in `b2-esiti.jsonl` con l'ora e **la
#    versione del motore** — il campo che una trascrizione a mano dimentica
#    sempre (S1 §4.5).
#
# ⛔ E quel campo adesso si CONFRONTA, non si stampa soltanto: il registro e'
#    condiviso con B11 e non si tronca mai, quindi «l'ultima riga» non e'
#    «la riga di questo motore» (rilievo R8.10, e la funzione `cerca_riga`).
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
PORTA_PAGINA=8899
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7447}
TEMP=$(mktemp -d)

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

MOTORI=${1:-tutti}

# ---------------------------------------------------------------------------
log "1. Il server minimo, sull'altra macchina"
inf "si accende e RESTA acceso finche' questo script non ha finito"
python3 "$RADICE/fondamenta/strumenti/sshpw.py" \
	"bash /media/REMOTIX/src/01-b2-lancia-wt.sh accendi $IND $PORTA" > "$TEMP/acceso.log" 2>&1
STATO=$?
sed 's/^/        /' "$TEMP/acceso.log"
if [ "$STATO" -ne 0 ]; then
	ko "il server non si e' acceso: la misura non parte"
	exit 3
fi

spegni() {
	python3 "$RADICE/fondamenta/strumenti/sshpw.py" \
		"bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" >/dev/null 2>&1
}
trap spegni EXIT

# ⛔ L'impronta si prende dal certificato VERO, adesso, e non si ricopia.
#    Il 9 agosto `01-b2-certificati.sh` ne ha stampata una; se qualcuno
#    rigenera i certificati, quella riga invecchia in silenzio e il sintomo e'
#    «WebTransport non si connette» senza che niente nomini l'impronta
#    (rilievo R1.14 di RCP.md).
# ⛔ 43, non 42.  Un SHA-256 in base64 e' 43 cifre piu' il riempimento: il
#    primo giro del 10 agosto ne chiedeva 42, ha preso l'impronta SENZA LA
#    PRIMA CIFRA, e la pagina avrebbe misurato un certificato che non
#    combacia — cioe' «ngtcp2 non parla coi browser» invece di «il banco ha
#    tagliato una lettera».  Il controllo qui sotto la conta.
IMPRONTA=$(grep -oE '[A-Za-z0-9+/]{43}=' "$TEMP/acceso.log" | tail -1)
# ⛔ `IMPRONTA_FORZATA` serve al quinto giro di B3: si punta la pagina a una
#    impronta VECCHIA e la sessione NON deve aprirsi.  Senza quel controllo,
#    «funziona con l'impronta nuova» non dimostra che il browser la guardi.
if [ -n "${IMPRONTA_FORZATA:-}" ]; then
	IMPRONTA=$IMPRONTA_FORZATA
	inf "⚠ impronta FORZATA dal chiamante (controllo negativo)"
fi
# ⛔ PRIMA «non ce l'ho», POI «e' tagliata» — rilievo R8.16, ed era l'ordine
#    contrario.  La regex produce per costruzione stringhe di 44 caratteri o
#    niente, quindi il test sulla lunghezza era vero se e solo se l'impronta era
#    VUOTA: il ramo qui sotto non si poteva raggiungere, e il caso in cui il
#    server non si accende usciva con la diagnosi dell'altro difetto — «e'
#    tagliata» al posto di «non ho l'impronta».  Due cause opposte, il nome
#    della seconda.
# ⚠ E resta detto quel che non e' cambiato: `tail -1` sceglie l'ULTIMA stringa
#   base64 del registro, non l'impronta per nome.  Finche' il registro d'avvio
#   ne porta una sola regge; il giorno che ne porta due, si sceglie per nome.
if [ -z "$IMPRONTA" ]; then
	ko "non ho l'impronta del certificato: senza, la pagina non puo' misurare"
	ko "la sessione — misurerebbe l'avviso del browser, che e' un'altra cosa"
	exit 4
fi
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "l'impronta ha ${#IMPRONTA} caratteri invece di 44: e' tagliata"
	exit 4
fi
ok "impronta della sessione: $IMPRONTA"

# ---------------------------------------------------------------------------
log "2. Il raccoglitore, su 127.0.0.1:$PORTA_PAGINA"
PRIMA=$(wc -l < "$QUI/b2-esiti.jsonl" 2>/dev/null || echo 0)
inf "esiti gia' registrati: $PRIMA"
python3 "$QUI/01-b2-raccogli.py" "$PORTA_PAGINA" > "$TEMP/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$TEMP/racc.log"
	exit 5
fi
ok "raccoglitore in ascolto, PID $PID_RACC"
# ⛔ E il profilo usa-e-getta si BUTTA davvero.  Il 10 agosto sei esecuzioni
#    hanno lasciato in /tmp 740 MB di profili di Chrome e Firefox — il disco
#    e' arrivato al 99% e si e' fermato un `git commit`.  «Usa-e-getta» era
#    solo la prima meta'.
trap 'kill $PID_RACC 2>/dev/null; spegni; rm -rf "$TEMP"' EXIT

# ⚠ L'indirizzo della sessione si tiene in una variabile perche' serve DUE
#   volte: nella pagina, e come firma della riga che quella pagina scrivera' nel
#   registro (vedi `cerca_riga`).
SESSIONE="https://$IND:$PORTA/rcp/1"
URL="http://127.0.0.1:$PORTA_PAGINA/01-b2-sonda.html?avvia=1&url=$SESSIONE&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$IMPRONTA")"
inf "indirizzo della sonda:"
printf '        %s\n' "$URL"

# ---------------------------------------------------------------------------
# ⛔ CHI HA SCRITTO L'ULTIMA RIGA — rilievo R8.10, ed e' il cuore di questo file.
#
# L'esito si leggeva dall'ULTIMA riga del registro, e l'attesa era soddisfatta
# da «una riga qualunque» apparsa dopo il conteggio iniziale.  Il campo `motore`
# si stampava e non si confrontava con niente.  ⛔ Tre strade concrete
# infilavano li' dentro la riga di un altro:
#
#   a) il ramo di fallimento non faceva avanzare il segnaposto, e la POST
#      tardiva del browser precedente — che `kill` sull'involucro `xvfb-run` non
#      uccide — arrivava mentre girava il motore dopo;
#   b) `b2-esiti.jsonl` e' CONDIVISO con B11: stesso file, stesso raccoglitore,
#      stessa porta 8899.  Nel file ci sono gia' righe `CONFORME` che con B2
#      non c'entrano;
#   c) il registro non si tronca mai, quindi due esecuzioni sovrapposte si
#      rubano le righe a vicenda.
#
# ⭐ La cura non chiede nessuno strumento nuovo: i campi per riconoscere la riga
#    sono gia' nel file.  Si cerca l'ULTIMA riga che, dopo il segnaposto, porta
#    insieme **il marchio del motore in prova** e **l'indirizzo della sessione
#    che gli abbiamo dato** — e le righe di B11, che portano `banco`, si
#    scartano per nome.  Se quella riga non c'e', non c'e' esito: e' diverso da
#    «c'e' ed e' rosso».
#
# Stampa «indice<TAB>esito<TAB>si|no», dove l'ultimo campo dice se i byte sono
# tornati identici (serve al controllo di R8.7).  Esce 1 se non trova niente.
cerca_riga() # $1 = segnaposto, $2 = marchio del motore, $3 = indirizzo atteso
{
	python3 -c '
import json, os, sys
percorso, prima, marchio, indirizzo = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
if not os.path.exists(percorso):
    sys.exit(1)
righe = open(percorso, encoding="utf-8").read().splitlines()
for n in range(len(righe), prima, -1):
    try:
        d = json.loads(righe[n - 1])
    except Exception:
        continue
    if d.get("banco"):            # riga di un altro banco: B11 scrive qui dentro
        continue
    if marchio not in (d.get("motore") or ""):
        continue
    if d.get("indirizzo") != indirizzo:
        continue
    byte = "si" if "i byte tornano identici" in (d.get("dettaglio") or "") else "no"
    print(n, d.get("esito"), byte, sep="\t")
    sys.exit(0)
sys.exit(1)
' "$QUI/b2-esiti.jsonl" "$1" "$2" "$3"
}

mostra_riga() # $1 = indice, $2 = «tutto» o «dettaglio»
{
	python3 -c '
import json, sys
righe = open(sys.argv[1], encoding="utf-8").read().splitlines()
d = json.loads(righe[int(sys.argv[2]) - 1])
if sys.argv[3] == "tutto":
    print("        esito  :", d.get("esito"))
    print("        motore :", (d.get("motore") or "")[:90])
for r in (d.get("dettaglio") or "").splitlines():
    print("        ", r)
' "$QUI/b2-esiti.jsonl" "$1" "$2"
}

conta_righe()
{
	wc -l < "$QUI/b2-esiti.jsonl" 2>/dev/null || echo 0
}

# ---------------------------------------------------------------------------
# prova_motore <nome> <binario del browser> <comando...>
#
# ⚠ Il binario da verificare si passa a parte: il comando comincia con
#   `xvfb-run`, e il primo giro controllava l'esistenza di «-a».
PROVATI=0
prova_motore()
{
	local nome=$1 binario=$2; shift 2
	log "3. $nome"
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	if ! command -v "$1" >/dev/null; then
		inf "⚠ $1 non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	# ⛔ IL MARCHIO CON CUI SI RICONOSCE LA RIGA — rilievo R8.10.
	#
	#    Un motore che non si sa riconoscere non si prova: senza il marchio si
	#    tornerebbe a contare le righe, che e' il difetto curato qui sotto.
	local marchio
	case "$nome" in
	firefox) marchio="Firefox/" ;;
	chrome)  marchio="Chrome/" ;;
	*)
		ko "non so con che marchio riconoscere «$nome» nel registro:"
		ko "   senza, il suo esito sarebbe indistinguibile da quello altrui"
		return 1
		;;
	esac
	PROVATI=$((PROVATI + 1))
	# ⛔ La cartella del profilo si CREA prima.  Con `--profile` su una
	#   cartella che non esiste, Firefox si ferma sul suo gestore dei profili
	#   e non chiede mai la pagina: al raccoglitore arrivano ZERO richieste e
	#   nel registro del browser non c'e' NIENTE.  Un silenzio su tutt'e due i
	#   lati, e per una cartella mancante (`[M]` 10 agosto 2026).
	mkdir -p "$TEMP/$nome"
	inf "profilo usa-e-getta in $TEMP/$nome — non si tocca il profilo di nessuno"
	"$@" >"$TEMP/$nome.log" 2>&1 &
	local p=$!
	# La pagina si misura da se' e spedisce l'esito: si aspetta la SUA riga,
	# non un tempo fisso e non «una riga qualunque».
	local i=0 trovata=""
	while [ "$i" -lt 40 ]; do
		trovata=$(cerca_riga "$PRIMA" "$marchio" "$SESSIONE") && break
		sleep 1
		i=$((i + 1))
	done
	kill "$p" 2>/dev/null
	wait "$p" 2>/dev/null
	if [ -z "$trovata" ]; then
		ko "$nome non ha registrato niente in $i secondi"
		# ⛔ IL DENOMINATORE: il browser ha almeno CHIESTO la pagina?  «non ha
		#    registrato» ha due cause opposte — non e' partito, oppure e'
		#    partito e la prova e' fallita in un modo che non spedisce nulla —
		#    e il registro del raccoglitore le distingue in una riga.
		inf "che cosa ha chiesto al raccoglitore:"
		# ⚠ Si contano le righe che il raccoglitore scrive per OGNI richiesta,
		#   non le occorrenze del nome del file: quello compare anche nel suo
		#   banner d'avvio, e il primo giro del 10 agosto ha stampato
		#   «richieste: 1» quando erano ZERO.
		printf '        richieste ricevute: %s\n' "$(grep -c '^richiesta: ' "$TEMP/racc.log")"
		tail -6 "$TEMP/racc.log" | sed 's/^/        /'
		inf "il suo registro dice:"
		tail -5 "$TEMP/$nome.log" | sed 's/^/        /'
		# ⛔ E il segnaposto avanza LO STESSO — rilievo R8.10, strada (a).
		#    Il ramo di fallimento non lo toccava: la POST tardiva di questo
		#    browser (che `kill` sull'involucro `xvfb-run` non uccide) arrivava
		#    mentre girava il motore successivo, e gliel'avrebbe accreditata.
		PRIMA=$(conta_righe)
		return 1
	fi
	# ⛔ «Registrato» non e' «aperta»: l'esito si legge e si confronta con
	#    l'atteso, e il confronto lo fa il banco.
	local indice visto byte
	IFS=$'\t' read -r indice visto byte <<< "$trovata"
	if [ "$visto" != "${ATTESO:-APERTA}" ]; then
		ko "$nome: esito $visto, atteso ${ATTESO:-APERTA}"
		mostra_riga "$indice" dettaglio
		PRIMA=$(conta_righe)
		return 1
	fi
	# ⛔ E «APERTA» NON VUOL DIRE CHE I BYTE TORNANO — rilievo R8.7.
	#
	#    La pagina avvolge l'andata e ritorno in un `try/catch` suo: se lo
	#    stream fallisce scrive una riga nel dettaglio e prosegue a registrare
	#    `APERTA` lo stesso.  Il lanciatore guardava solo il campo `esito`, e ⛔
	#    la prova che questo produce un verde falso e' nel registro versionato:
	#    il 10 agosto 2026 alle 09:36:16 (Firefox 140) e 09:36:32 (Chrome)
	#    tutt'e due `"esito": "APERTA"` e tutt'e due «sessione aperta ma lo
	#    stream non ha funzionato: WebTransportError» — e il banco stampo' OK.
	#
	# ⚠ Vale solo quando l'atteso e' `APERTA`: nel controllo negativo del
	#   quinto giro di B3 la sessione non deve aprirsi affatto, e li' non c'e'
	#   nessun byte da far tornare.
	if [ "${ATTESO:-APERTA}" = APERTA ] && [ "$byte" != si ]; then
		ko "$nome: sessione APERTA ma i byte NON tornano identici — e' la"
		ko "   forma di verde che questo banco esiste per non produrre"
		mostra_riga "$indice" dettaglio
		PRIMA=$(conta_righe)
		return 1
	fi
	ok "$nome ha registrato il suo esito dopo $i secondi (atteso ${ATTESO:-APERTA}):"
	mostra_riga "$indice" tutto
	PRIMA=$(conta_righe)
	return 0
}

# ═══ ⛔ PERCHE' `xvfb-run` E NON `--headless` ═════════════════════════════════
#
# `[M]` 10 agosto 2026, e sono due fatti diversi:
#
#   - **Firefox headless su questa macchina non carica affatto la pagina.**
#     Parte, scrive «RenderCompositorSWGL failed mapping default framebuffer»,
#     e al raccoglitore arrivano **zero richieste**.  Non e' un difetto della
#     misura: e' un motore che non rende.
#   - ⚠ **Chrome headless invece funziona, e proprio per questo inganna**: la
#     sessione si apre (22,2 ms), ma si dichiara `HeadlessChrome/151` — cioe'
#     un motore DIVERSO da quello del 9 agosto.  Un numero confrontato con
#     l'altro sarebbe un confronto fra due cose che non hanno lo stesso nome.
#
# ⭐ Con uno schermo finto vero (`xvfb-run`) tutt'e due i motori girano come
#    girano davvero, dichiarano la versione normale, e i numeri dei due giorni
#    si possono mettere in colonna.  E non si apre nessuna finestra sulla
#    scrivania di chi sta lavorando.
ESITO=0
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = firefox ]; then
	prova_motore firefox firefox xvfb-run -a firefox --no-remote \
		--profile "$TEMP/firefox" "$URL" || ESITO=1
fi
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = chrome ]; then
	prova_motore chrome google-chrome xvfb-run -a google-chrome --no-first-run \
		--user-data-dir="$TEMP/chrome" "$URL" || ESITO=1
fi

log "Esito"
# ⛔ IL CONTROLLO CHE IL PRIMO GIRO NON AVEVA, e che ha stampato un VERDE su
#    ZERO misure: se nessun motore e' stato provato, non c'e' niente da
#    approvare.  «Tutti quelli provati sono andati bene» e' vero anche quando
#    i provati sono zero, ed e' la forma di verde piu' vuota che ci sia.
inf "motori effettivamente provati: $PROVATI"
if [ "$PROVATI" -eq 0 ]; then
	ko "⛔ NESSUN motore e' stato provato: questo non e' un esito, e' un banco"
	ko "   che non ha misurato niente."
	exit 6
fi
if [ "$ESITO" -eq 0 ]; then
	ok "i $PROVATI motori provati hanno registrato il loro esito in banchi/b2-esiti.jsonl"
else
	ko "almeno un motore non ha registrato: vedi sopra"
fi
inf "⛔ «registrato» non e' «aperta»: l'esito di ogni riga si legge, non si"
inf "   presume.  Una sessione NON-APERTA e' un esito registrato anche lei."
exit "$ESITO"
