#!/bin/bash
#
# 01-b11-lancia.sh — ⚠ gira SULLA MACCHINA DI CHI GUARDA: i browser stanno qui.
#
#   bash banchi/01-b11-lancia.sh            controllo + i due motori
#   bash banchi/01-b11-lancia.sh firefox    controllo + un motore solo
#
# ---------------------------------------------------------------------------
# ⛔ B11 — LE PROVE DI VIOLAZIONE VERSO LA PAGINA (rilievo R4.1)
#
# La prima stesura del banco della fase 1 aveva **dodici violazioni verso il
# server e nessuna verso il client**.  Ma `RCP.md` §3 e' scritta su
# «un'implementazione RCP», e §9 ha un **DEVE esplicito del client**.
#
# ⭐ In un progetto che ha perso `mstsc` e che scrive `RCP.md` proprio per non
#    fidarsi di due programmi della stessa mano, **un client mai messo alla
#    prova e' il buco al posto dell'arbitro**.
#
# ---------------------------------------------------------------------------
# ⛔ IL CONTROLLO CHE DICE NO, E QUI E' PARTICOLARE
#
# Prima si gira la pagina contro il server **SANO**: i dodici casi devono
# fallire, perche' un server sano non manda niente di sbagliato.  ⚠ Senza
# questo giro, «dodici verdi» sarebbe compatibile con una pagina che dichiara
# conforme qualunque cosa — cioe' **un banco che approva se stesso**.
#
# Poi si accende il server **GUASTO**, e i dodici devono passare.
#
# ---------------------------------------------------------------------------
# ⛔ E IL SECONDO TESTIMONE
#
# Tre righe della tabella di B11 sono proprieta' **negative** della pagina, e
# una proprieta' negativa non si osserva da dentro chi la deve rispettare:
#
#   dopo `RESPINTO` non si riprova   → lo vede il REGISTRO DEL SERVER
#   `desktop` non cambia niente      → due giri, e i byte usciti a confronto
#   nessun battito applicativo       → si tace otto secondi e si conta
#
# Le ultime due le porta la pagina; la prima la conferma il registro, che si
# scarica alla fine e si legge qui.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
SSH="python3 $RADICE/v1/strumenti/sshpw.py"
PORTA_PAGINA=8899
IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7447}
TEMP=$(mktemp -d)

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

MOTORI=${1:-tutti}
ESITO=0
IMPRONTA=""

# ---------------------------------------------------------------------------
log "1. Il raccoglitore, su 127.0.0.1:$PORTA_PAGINA"
PRIMA=$(wc -l < "$QUI/b2-esiti.jsonl" 2>/dev/null || echo 0)
python3 "$QUI/01-b2-raccogli.py" "$PORTA_PAGINA" > "$TEMP/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "il raccoglitore non e' partito:"
	sed 's/^/        /' "$TEMP/racc.log"
	rm -rf "$TEMP"
	exit 5
fi
ok "raccoglitore in ascolto, PID $PID_RACC"

# ⛔ Il profilo usa-e-getta si BUTTA, e il server guasto si rimette SANO: sono
#    le due cose che il 10 agosto 2026 hanno lasciato strascichi (740 MB in
#    /tmp, e un server che mente).
ripulisci() {
	kill $PID_RACC 2>/dev/null
	$SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" >/dev/null 2>&1
	$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh spegni" 2>&1 | sed 's/^/        /'
	rm -rf "$TEMP"
}
trap ripulisci EXIT

# ---------------------------------------------------------------------------
# prova_motore <nome> <binario> <comando...>   — ATTESO nell'ambiente
PROVATI=0
prova_motore()
{
	local nome=$1 binario=$2; shift 2
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	if ! command -v "$1" >/dev/null; then
		inf "⚠ $1 non c'e' su questa macchina: si salta, E SI DICE"
		return 0
	fi
	PROVATI=$((PROVATI + 1))
	local url="http://127.0.0.1:$PORTA_PAGINA/01-b11-pagina.html?url=https://$IND:$PORTA/rcp/1&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$IMPRONTA")"
	rm -rf "$TEMP/$nome"
	mkdir -p "$TEMP/$nome"
	"$@" "$url" >"$TEMP/$nome.log" 2>&1 &
	local p=$!
	# ⚠ Il tetto e' generoso apposta: i dodici casi hanno dentro otto secondi
	#   di silenzio (§2.2) e qualche attesa di congedo.
	local atteso=$((PRIMA + 1)) i=0 ora=0
	while [ "$i" -lt 240 ]; do
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
		#    registrato» ha due cause opposte, e solo il registro del
		#    raccoglitore le distingue.
		printf '        richieste ricevute: %s\n' "$(grep -c '^richiesta: ' "$TEMP/racc.log")"
		tail -6 "$TEMP/racc.log" | sed 's/^/        /'
		tail -5 "$TEMP/$nome.log" | sed 's/^/        /'
		return 1
	fi
	local visto
	visto=$(python3 -c '
import json,sys
print(json.loads(open(sys.argv[1]).read().splitlines()[-1]).get("esito"))
' "$QUI/b2-esiti.jsonl")
	tail -1 "$QUI/b2-esiti.jsonl" | python3 -c '
import json,sys
d=json.loads(sys.stdin.read())
print("        esito  :", d.get("esito"), " punti che non passano:", d.get("guasti"))
print("        motore :", d.get("motore","")[:90])
for r in (d.get("dettaglio") or "").splitlines():
    print("        ", r)
'
	PRIMA=$((PRIMA + 1))
	if [ "$visto" != "${ATTESO:-CONFORME}" ]; then
		ko "$nome: esito $visto, atteso ${ATTESO:-CONFORME}"
		return 1
	fi
	ok "$nome: $visto, come atteso (dopo $i secondi)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
log "2. ⛔ IL CONTROLLO CHE DICE NO — la pagina contro il server SANO"
inf "atteso: NON-CONFORME.  Un server sano non manda niente di sbagliato,"
inf "        quindi nessuno dei dodici casi puo' passare."
inf "⚠ gira con UN motore solo, e si dichiara: quel che prova e' che la pagina"
inf "  sa dire di NO, e per quello un motore basta."
# ⛔ E PRIMA SI RIMETTE IL BINARIO SANO, sempre.
#
#    `01-b2-lancia-wt.sh accendi` accende **il binario che c'e' sul disco**, e
#    quello puo' essere il guasto di un giro precedente.  ⚠ Il controllo
#    direbbe CONFORME, il banco darebbe rosso, e il rosso sarebbe sul
#    controllo invece che sul server: la stessa forma del difetto trovato oggi
#    con `test -x`.
inf "si rimette il binario sano prima del controllo (puo' volerci un minuto)"
$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh spegni" 2>&1 | tail -3 | sed 's/^/        /'
if ! $SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh accendi $IND $PORTA" \
	> "$TEMP/sano.log" 2>&1; then
	ko "il server sano non si e' acceso: il controllo non parte"
	sed 's/^/        /' "$TEMP/sano.log"
	exit 3
fi
IMPRONTA=$(grep -oE '[A-Za-z0-9+/]{43}=' "$TEMP/sano.log" | tail -1)
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "l'impronta ha ${#IMPRONTA} caratteri invece di 44: e' tagliata"
	exit 4
fi
ok "server SANO acceso, impronta $IMPRONTA"

ATTESO=NON-CONFORME prova_motore controllo firefox xvfb-run -a firefox \
	--no-remote --profile "$TEMP/controllo" || ESITO=1
$SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" >/dev/null 2>&1

# ═══════════════════════════════════════════════════════════════════════════
log "3. Il server GUASTO, sull'altra macchina"
inf "⛔ e' un server che mente di proposito: si spegne alla fine, e con lui"
inf "   si rimette il sorgente sano"
if ! $SSH "bash /media/REMOTIX/src/01-b11-guasto.sh accendi" \
	> "$TEMP/acceso.log" 2>&1; then
	sed 's/^/        /' "$TEMP/acceso.log"
	ko "il server guasto non si e' acceso"
	exit 3
fi
sed 's/^/        /' "$TEMP/acceso.log" | tail -12
IMPRONTA=$(grep -oE '[A-Za-z0-9+/]{43}=' "$TEMP/acceso.log" | tail -1)
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "l'impronta ha ${#IMPRONTA} caratteri invece di 44"
	exit 4
fi
ok "impronta della sessione: $IMPRONTA"

log "4. I dodici casi, con i browser veri"
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = firefox ]; then
	prova_motore firefox firefox xvfb-run -a firefox --no-remote \
		--profile "$TEMP/firefox" || ESITO=1
fi
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = chrome ]; then
	prova_motore chrome google-chrome xvfb-run -a google-chrome \
		--no-first-run --user-data-dir="$TEMP/chrome" || ESITO=1
fi

# ---------------------------------------------------------------------------
log "5. ⛔ Il SECONDO TESTIMONE: il registro del server"
inf "«dopo RESPINTO la pagina non riprova» non si vede da dentro la pagina:"
inf "si vede da qui, e il server scrive ogni byte arrivato dopo la fine"
$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh registro" > "$TEMP/registro.txt" 2>&1
DOPO=$(grep -c "DOPO la fine" "$TEMP/registro.txt" || true)
SERVITI=$(grep -c "B11 GUASTO: guasto chiesto" "$TEMP/registro.txt" || true)
if [ "${SERVITI:-0}" -eq 0 ]; then
	ko "⛔ il server dice di non aver servito NESSUN guasto: la pagina non gli"
	ko "   ha mai chiesto niente, e i dodici esiti non hanno denominatore"
	ESITO=1
else
	ok "guasti serviti dal server: $SERVITI"
fi
if [ "${DOPO:-0}" -eq 0 ]; then
	ok "⭐ nessun byte e' arrivato dopo la fine della sessione (§4.2, §4.4)"
else
	ko "⛔ $DOPO volte la pagina ha spedito DOPO la fine della sessione:"
	grep "DOPO la fine" "$TEMP/registro.txt" | head -5 | sed 's/^/        /'
	ESITO=1
fi

# ⛔⭐ E IL TESTIMONE POSITIVO, che il 10 agosto 2026 mancava.
#
#    «zero byte dopo la fine» e' vero anche per una pagina che, davanti a un
#    server che sbaglia dopo `RESPINTO`, se ne va in silenzio — cioe' che viola
#    §8.1 invece di §4.4.  ⚠ E' la forma di verde piu' vuota che ci sia: quella
#    che non ha bisogno che qualcosa vada bene.
#
# ⭐ Il caso `respinto-poi-congedo` obbliga la pagina a un `CONGEDO` quando per
#    il server la sessione e' gia' finita, e il server lo scrive nominandolo.
#    Se ne aspetta UNO per ogni motore provato contro il GUASTO — cioe' tutti
#    tranne il controllo, che gira contro il server sano e li' quel messaggio
#    non arriva.
#
# ⛔ E SI CONTANO LE DUE STRADE DI §3.1, non una: il congedo puo' arrivare come
#    byte sul canale di controllo **oppure** dentro il codice di chiusura della
#    sessione — e il 10 agosto 2026 i due motori ne hanno usata una per uno.
#    ⚠ Pretendere la prima sola avrebbe scritto «Firefox non si congeda», che
#    e' falso: Firefox azzera il canale e mette il motivo nella capsula.
#
# ⛔ E SI CONTA DENTRO IL CASO, non su tutto il registro.  Un commiato in fondo
#    al giro non dice niente su QUEL caso: il registro e' in ordine, e ogni
#    «guasto chiesto» apre il blocco del suo.  ⚠ Contarli tutti insieme dava 15
#    con 2 attesi, ed era un numero senza significato.
ATTESI=$((PROVATI - 1))
eval "$(awk '
  /guasto chiesto dal client:/ { caso = $NF; if (caso == "respinto-poi-congedo") casi++; visto = 0 }
  /CONGEDO di commiato/ {
    if (caso == "respinto-poi-congedo" && !visto) {
      visto = 1; con++
      if (index($0, "seconda strada")) chiusura++; else canale++
    }
  }
  END { printf "CASI=%d CON=%d CANALE=%d CHIUSURA=%d\n", casi, con, canale, chiusura }
' "$TEMP/registro.txt")"
inf "il caso «respinto-poi-congedo» e' stato servito $CASI volte"
inf "commiato per il canale di controllo: $CANALE — per il codice di chiusura: $CHIUSURA"
if [ "$CASI" -ne "$ATTESI" ]; then
	ko "⛔ il caso e' stato servito $CASI volte, e i motori contro il guasto sono"
	ko "   $ATTESI: il conto qui sotto non avrebbe denominatore"
	ESITO=1
elif [ "$CON" -eq "$ATTESI" ]; then
	ok "⭐ il congedo di §8.1 arriva ogni volta: $CON su $ATTESI, e ⛔ per DUE"
	ok "   strade diverse — §3.1 punto 3 non e' ridondanza, e' l'altra strada"
else
	ko "⛔ solo $CON commiati su $ATTESI: c'e' un motore che chiude e NON dice"
	ko "   perche', ne' sul canale ne' nel codice di chiusura (§8.1)"
	ESITO=1
fi

log "Esito"
inf "motori effettivamente provati: $PROVATI (controllo compreso)"
if [ "$PROVATI" -eq 0 ]; then
	ko "⛔ NESSUN motore e' stato provato: questo non e' un esito"
	exit 6
fi
if [ "$ESITO" -eq 0 ]; then
	ok "⭐ B11: la pagina applica §3 anche quando a sbagliare e' il server,"
	ok "   e contro un server sano dice di no"
else
	ko "⛔ B11: qualcosa non passa"
fi
exit "$ESITO"
