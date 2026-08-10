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
python3 "$RADICE/v1/strumenti/sshpw.py" \
	"bash /media/REMOTIX/src/01-b2-lancia-wt.sh accendi $IND $PORTA" > "$TEMP/acceso.log" 2>&1
STATO=$?
sed 's/^/        /' "$TEMP/acceso.log"
if [ "$STATO" -ne 0 ]; then
	ko "il server non si e' acceso: la misura non parte"
	exit 3
fi

spegni() {
	python3 "$RADICE/v1/strumenti/sshpw.py" \
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
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "l'impronta ha ${#IMPRONTA} caratteri invece di 44: e' tagliata"
	exit 4
fi
if [ -z "$IMPRONTA" ]; then
	ko "non ho l'impronta del certificato: senza, la pagina non puo' misurare"
	ko "la sessione — misurerebbe l'avviso del browser, che e' un'altra cosa"
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

URL="http://127.0.0.1:$PORTA_PAGINA/01-b2-sonda.html?avvia=1&url=https://$IND:$PORTA/rcp/1&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$IMPRONTA")"
inf "indirizzo della sonda:"
printf '        %s\n' "$URL"

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
	# La pagina si misura da se' e spedisce l'esito: si aspetta che il
	# registro cresca, non un tempo fisso.
	local atteso=$((PRIMA + 1)) i=0 ora=0
	while [ "$i" -lt 40 ]; do
		ora=$(wc -l < "$QUI/b2-esiti.jsonl" 2>/dev/null || echo 0)
		[ "$ora" -ge "$atteso" ] && break
		sleep 1
		i=$((i + 1))
	done
	kill "$p" 2>/dev/null
	wait "$p" 2>/dev/null
	if [ "$ora" -lt "$atteso" ]; then
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
		return 1
	fi
	# ⛔ «Registrato» non e' «aperta»: l'esito si legge e si confronta con
	#    l'atteso, e il confronto lo fa il banco.
	local visto
	visto=$(python3 -c '
import json,sys
print(json.loads(open(sys.argv[1]).read().splitlines()[-1]).get("esito"))
' "$QUI/b2-esiti.jsonl")
	if [ "$visto" != "${ATTESO:-APERTA}" ]; then
		ko "$nome: esito $visto, atteso ${ATTESO:-APERTA}"
		tail -1 "$QUI/b2-esiti.jsonl" | python3 -c '
import json,sys
d=json.loads(sys.stdin.read())
for r in d.get("dettaglio","").splitlines():
    print("        ", r)
'
		PRIMA=$((PRIMA + 1))
		return 1
	fi
	ok "$nome ha registrato il suo esito dopo $i secondi (atteso ${ATTESO:-APERTA}):"
	tail -1 "$QUI/b2-esiti.jsonl" | python3 -c '
import json,sys
d=json.loads(sys.stdin.read())
print("        esito  :", d.get("esito"))
print("        motore :", d.get("motore","")[:90])
for r in d.get("dettaglio","").splitlines():
    print("        ", r)
'
	PRIMA=$((PRIMA + 1))
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
