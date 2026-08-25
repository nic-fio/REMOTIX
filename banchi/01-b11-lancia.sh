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
# Prima si gira la pagina contro il server **SANO**.  ⚠ Senza questo giro,
# «tutti verdi» sarebbe compatibile con una pagina che dichiara conforme
# qualunque cosa — cioe' **un banco che approva se stesso**.
#
# ⛔ E non basta che l'esito aggregato dica NON-CONFORME: si guarda CASO PER
#    CASO.  I casi che si aspettano un `congedo:` sono quelli che un server
#    sano **non puo'** provocare, e devono cadere tutti; i casi che si
#    aspettano «prosegue» invece passano, perche' un server sano fa proprio
#    quel che chiedono.  ⚠ La prima stesura diceva «nessuno dei dodici casi
#    puo' passare», ed era falso (rilievo R5.3).
#
# Poi si accende il server **GUASTO**, e allora devono passare tutti.
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
#
# ⛔⭐ E LA RIPULITURA CHE FALLISCE DEVE ENTRARE NEL CODICE D'USCITA.
#
#    `01-b11-guasto.sh spegni` ha un esito di fallimento vero e proprio — esce
#    5 con «RESTANO N righe di B11» — e qui attraversava un `2>&1 | sed` senza
#    che nessuno lo provasse.  Bastava una riga `REMOTIX B11 GUASTO` rimasta
#    nel sorgente (il difetto noto n.1 del mandato: un `--togli` che non
#    toglie) perche' il banco stampasse «⭐ B11: la pagina applica §3 …»,
#    uscisse **0**, e lasciasse la segnalazione della ripulitura fallita sotto
#    la riga verde, affidata all'occhio di chi legge — cioe' esattamente quel
#    che la regola B0.4 vieta: *l'atteso lo confronta il banco, non chi legge*
#    (rilievo R5.2).
#
# ⭐ E si chiama PRIMA del verdetto, non solo dal `trap`: una ripulitura che
#    fallisce dopo la riga verde e' una riga verde sbagliata.  Il `trap` resta
#    per le uscite anticipate, e non la ripete.
RIPULITO=0
ripulisci()
{
	local st esito=0
	[ "$RIPULITO" -eq 0 ] || return 0
	RIPULITO=1
	kill $PID_RACC 2>/dev/null
	$SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" \
		> "$TEMP/rip-sano.log" 2>&1
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ non si e' potuto spegnere il server SANO (uscita $st):"
		tail -5 "$TEMP/rip-sano.log" | sed 's/^/        /'
		esito=1
	fi
	$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh spegni" \
		> "$TEMP/rip-guasto.log" 2>&1
	st=$?
	sed 's/^/        /' "$TEMP/rip-guasto.log"
	if [ "$st" -ne 0 ]; then
		ko "⛔ IL SERVER GUASTO NON E' STATO RIMESSO SANO (uscita $st)."
		ko "   Un interruttore che fa mentire il server non deve sopravvivere"
		ko "   alla fase: si rilancia «01-b11-guasto.sh spegni» sul server."
		esito=1
	fi
	rm -rf "$TEMP"
	return "$esito"
}
uscendo()
{
	local u=$?
	# ⚠ La ripulitura puo' solo peggiorare un esito, mai migliorarlo.
	ripulisci || { [ "$u" -eq 0 ] && u=7; }
	exit "$u"
}
trap uscendo EXIT

# ---------------------------------------------------------------------------
# ⛔ IL RECORD CHE SI LEGGE DEV'ESSERE DI QUESTO GIRO E DI QUESTO MOTORE.
#
#    L'attesa era su un CONTEGGIO di righe di `b2-esiti.jsonl` e il verdetto si
#    leggeva dall'ultima riga dello stesso file: niente legava le due cose allo
#    stesso record, e il record porta il campo `motore` che nessuno guardava.
#    ⚠ `b2-esiti.jsonl` e' il registro CONDIVISO di tutto B2 — una sonda
#      qualunque che scriva li' durante il giro fa uscire l'attesa su una riga
#      altrui — e `kill "$p"` uccide `xvfb-run`, non il browser che `xvfb-run`
#      ha avviato: un browser sopravvissuto al giro precedente puo' depositare
#      il suo POST dopo.  In tutt'e due i casi il banco stampava «chrome:
#      CONFORME, come atteso (dopo 0 secondi)» leggendo l'esito **di un altro
#      giro** (rilievo R5.6).
#
# ⭐ I due campi che lo legano ci sono gia': `motore` (la stringa del browser) e
#    `ora` (la mette il raccoglitore, che gira su questa stessa macchina).  Si
#    cerca il record piu' recente che sia dello stesso motore e non piu' vecchio
#    dell'istante in cui questo giro e' partito.
cerca_esito() # $1 = marca del motore, $2 = istante d'inizio
{
	python3 - "$QUI/b2-esiti.jsonl" "$1" "$2" "$TEMP/ultimo.json" <<'FINE'
import json, sys
registro, marca, inizio, dove = sys.argv[1:5]
try:
    righe = open(registro, encoding="utf-8").read().splitlines()
except FileNotFoundError:
    sys.exit(1)
for r in reversed(righe):
    try:
        d = json.loads(r)
    except Exception:
        continue
    if marca not in (d.get("motore") or ""):
        continue
    if (d.get("ora") or "") < inizio:
        break                      # da qui in giu' sono giri di prima
    open(dove, "w", encoding="utf-8").write(r + "\n")
    sys.exit(0)
sys.exit(1)
FINE
}

# prova_motore <nome> <binario> <comando...>   — ATTESO nell'ambiente
PROVATI=0
SALTATI=0
# ⛔ ESEGUITO dice se l'ultima chiamata ha GIRATO o ha SALTATO.  Il salto
#    restituiva 0 e non lasciava nessuna traccia: ne' `ESITO` ne' alcun
#    conteggio ne prendevano nota, e i motori mancanti finivano lo stesso nel
#    denominatore (rilievo R5.16).
ESEGUITO=0
prova_motore()
{
	local nome=$1 binario=$2; shift 2
	local marca=""
	ESEGUITO=0
	rm -f "$TEMP/ultimo.json"
	case "$binario" in
	*chrome*|*chromium*) marca=Chrome ;;
	*firefox*)           marca=Firefox ;;
	esac
	if [ -z "$marca" ]; then
		ko "⛔ «$binario» non si sa riconoscere dentro il campo «motore» del"
		ko "   record: senza, l'esito letto non sarebbe legato a questo motore"
		return 1
	fi
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario non c'e' su questa macchina: si salta, E SI DICE"
		SALTATI=$((SALTATI + 1))
		return 0
	fi
	if ! command -v "$1" >/dev/null; then
		inf "⚠ $1 non c'e' su questa macchina: si salta, E SI DICE"
		SALTATI=$((SALTATI + 1))
		return 0
	fi
	PROVATI=$((PROVATI + 1))
	ESEGUITO=1
	local url="http://127.0.0.1:$PORTA_PAGINA/01-b11-pagina.html?url=https://$IND:$PORTA/rcp/1&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$IMPRONTA")"
	rm -rf "$TEMP/$nome"
	mkdir -p "$TEMP/$nome"
	local inizio
	inizio=$(date +%Y-%m-%dT%H:%M:%S)
	"$@" "$url" >"$TEMP/$nome.log" 2>&1 &
	local p=$!
	# ⚠ Il tetto e' generoso apposta: i casi hanno dentro otto secondi di
	#   silenzio (§2.2) e qualche attesa di congedo.  ⚠ Che sia generoso
	#   ABBASTANZA e' un'ipotesi e non un conto: il tetto peggiore della pagina
	#   si calcola dai suoi tempi, e non lo si e' mai fatto (rilievo R5.20,
	#   `[?]`, da misurare prima di toccare questo numero).
	local i=0 trovato=0
	while [ "$i" -lt 240 ]; do
		if cerca_esito "$marca" "$inizio"; then trovato=1; break; fi
		sleep 1
		i=$((i + 1))
	done
	kill "$p" 2>/dev/null
	wait "$p" 2>/dev/null
	if [ "$trovato" -ne 1 ]; then
		ko "$nome non ha registrato niente in $i secondi"
		# ⛔ IL DENOMINATORE: il browser ha almeno CHIESTO la pagina?  «non ha
		#    registrato» ha due cause opposte, e solo il registro del
		#    raccoglitore le distingue.
		printf '        richieste ricevute: %s\n' "$(grep -c '^richiesta: ' "$TEMP/racc.log")"
		tail -6 "$TEMP/racc.log" | sed 's/^/        /'
		tail -5 "$TEMP/$nome.log" | sed 's/^/        /'
		return 1
	fi
	python3 -c '
import json,sys
d=json.loads(open(sys.argv[1]).read())
print("        esito  :", d.get("esito"), " punti che non passano:", d.get("guasti"))
print("        motore :", d.get("motore","")[:90])
for r in (d.get("dettaglio") or "").splitlines():
    print("        ", r)
' "$TEMP/ultimo.json"
	local visto
	visto=$(python3 -c '
import json,sys
print(json.loads(open(sys.argv[1]).read()).get("esito"))
' "$TEMP/ultimo.json")
	if [ "$visto" != "${ATTESO:-CONFORME}" ]; then
		ko "$nome: esito $visto, atteso ${ATTESO:-CONFORME}"
		return 1
	fi
	ok "$nome: $visto, come atteso (dopo $i secondi)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
log "2. ⛔ IL CONTROLLO CHE DICE NO — la pagina contro il server SANO"
inf "atteso: NON-CONFORME, e non basta l'etichetta: i casi che si aspettano un"
inf "        «congedo:» devono essere caduti TUTTI, e nessun caso deve essere"
inf "        finito in «errore:», che vorrebbe dire che la pagina non ha parlato"
inf "⚠ gira con UN motore solo, e si dichiara: quel che prova e' che la pagina"
inf "  sa dire di NO, e per quello un motore basta."
# ⛔ E PRIMA SI RIMETTE IL BINARIO SANO, sempre.
#
#    `01-b2-lancia-wt.sh accendi` accende **il binario che c'e' sul disco**, e
#    quello puo' essere il guasto di un giro precedente.  ⚠ Il controllo
#    direbbe CONFORME, il banco darebbe rosso, e il rosso sarebbe sul
#    controllo invece che sul server: la stessa forma del difetto trovato oggi
#    con `test -x`.
# ⛔ E QUI LO STATO SI PROVA, perche' e' il punto in cui il rosso finirebbe
#    sull'imputato sbagliato: era in una pipeline (`| tail -3 | sed`) e non lo
#    guardava nessuno (rilievo R5.2).
inf "si rimette il binario sano prima del controllo (puo' volerci un minuto)"
$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh spegni" > "$TEMP/sano-prima.log" 2>&1
ST=$?
tail -3 "$TEMP/sano-prima.log" | sed 's/^/        /'
if [ "$ST" -ne 0 ]; then
	ko "⛔ il binario sano non si e' potuto rimettere (uscita $ST): il controllo"
	ko "   girerebbe contro un binario che non si sa quale sia"
	exit 3
fi
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
CONTROLLO=$ESEGUITO
# ⛔ «NON-CONFORME» DA SOLO NON PROVA NIENTE, ed e' il buco piu' grande di
#    questo banco.
#
#    La pagina scrive NON-CONFORME non appena un punto qualunque non passa, e
#    con un'impronta stantia nel `?impronta=` — basta che `01-b2-certificati.sh`
#    abbia ruotato la chiave nel frattempo — nessuna sessione WebTransport si
#    apre, la pagina non legge un byte di RCP, tutti i casi finiscono in
#    `errore:WebTransportError` e il banco stampava «OK controllo:
#    NON-CONFORME, come atteso».  ⛔ Cioe': il controllo che deve provare «la
#    pagina sa dire di NO» era soddisfatto da una pagina che non ha detto
#    niente (rilievo R5.3, forma E8).
#
# ⭐ Il dato che distingue i due casi c'era gia' e non lo guardava nessuno: la
#    pagina spedisce `casi: [{nome, atteso, fatto, ok}, …]`, e il banco leggeva
#    solo `.esito`.
if [ "$CONTROLLO" -eq 1 ] && [ -f "$TEMP/ultimo.json" ]; then
	python3 - "$TEMP/ultimo.json" <<'FINE'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read())
casi = d.get("casi") or []
if not casi:
    print("        ⛔ il record non porta l'elenco dei casi: senza, «NON-CONFORME»")
    print("           e' compatibile con una pagina che non ha parlato col server")
    sys.exit(1)
# ⭐ I due conti si CALCOLANO dal record, non si scrivono a mano: aggiungere un
#    caso alla pagina non deve lasciare qui un numero vecchio.
errori = [c["nome"] for c in casi if str(c.get("fatto", "")).startswith("errore:")]
# Un `congedo:` la pagina lo manda solo quando il server ha violato §3: un
# server SANO non puo' provocarlo, quindi questi casi devono cadere tutti.
devono = [c for c in casi if str(c.get("atteso", "")).startswith("congedo:")]
caduti = [c for c in devono if not c.get("ok")]
print(f"        casi nel record: {len(casi)}")
print(f"        casi che un server SANO non puo' soddisfare: {len(devono)}"
      f" — caduti: {len(caduti)}")
print(f"        casi finiti in «errore:…»: {len(errori)}  (attesi 0)")
male = 0
if errori:
    print("        ⛔ la pagina non ha parlato RCP in", len(errori), "casi:",
          ", ".join(errori[:5]))
    print("           un controllo soddisfatto da una sessione che non si apre")
    print("           non prova che la pagina sappia dire di no")
    male = 1
if len(caduti) != len(devono):
    passati = [c["nome"] for c in devono if c.get("ok")]
    print("        ⛔ contro un server SANO sono PASSATI casi che pretendono una")
    print("           violazione del server:", ", ".join(passati))
    male = 1
sys.exit(male)
FINE
	if [ $? -ne 0 ]; then
		ko "⛔ il controllo che dice NO non ha detto NO per la ragione giusta"
		ESITO=1
	else
		ok "⭐ il controllo dice NO caso per caso, e la pagina ha parlato RCP"
	fi
elif [ "$CONTROLLO" -eq 1 ]; then
	ko "⛔ il controllo non ha lasciato nessun record da guardare"
	ESITO=1
fi
$SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" > "$TEMP/sano-dopo.log" 2>&1
ST=$?
if [ "$ST" -ne 0 ]; then
	ko "⛔ il server SANO non si e' spento (uscita $ST): il server guasto non"
	ko "   troverebbe la porta libera, e il rosso finirebbe su di lui"
	tail -5 "$TEMP/sano-dopo.log" | sed 's/^/        /'
	exit 3
fi

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

# ⭐ Quanti casi la pagina dichiara di aver girato, motore per motore: e' il
#    denominatore dei «guasti serviti» piu' avanti, e lo dichiara LA PAGINA —
#    qui non si scrive «tredici», che invecchierebbe al primo caso aggiunto.
MOTORI_GUASTO=0
CASI_ATTESI=0
conta_i_casi()
{
	local n
	[ "$ESEGUITO" -eq 1 ] || return 0
	MOTORI_GUASTO=$((MOTORI_GUASTO + 1))
	[ -f "$TEMP/ultimo.json" ] || return 0
	n=$(python3 -c '
import json,sys
print(len(json.loads(open(sys.argv[1]).read()).get("casi") or []))
' "$TEMP/ultimo.json")
	CASI_ATTESI=$((CASI_ATTESI + n))
}

log "4. I casi della pagina, con i browser veri"
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = firefox ]; then
	prova_motore firefox firefox xvfb-run -a firefox --no-remote \
		--profile "$TEMP/firefox" || ESITO=1
	conta_i_casi
fi
if [ "$MOTORI" = tutti ] || [ "$MOTORI" = chrome ]; then
	prova_motore chrome google-chrome xvfb-run -a google-chrome \
		--no-first-run --user-data-dir="$TEMP/chrome" || ESITO=1
	conta_i_casi
fi

# ---------------------------------------------------------------------------
log "5. ⛔ Il SECONDO TESTIMONE: il registro del server"
inf "«dopo RESPINTO la pagina non riprova» non si vede da dentro la pagina:"
inf "si vede da qui, e il server scrive ogni byte arrivato dopo la fine"
# ⛔ E LO STATO DI QUESTA LETTURA SI PROVA.
#
#    `> "$TEMP/registro.txt"` catturava l'uscita e buttava lo stato: un
#    registro mancante, un server mai partito, un contenitore che non risponde
#    arrivavano tutti come «zero righe» — che ha la stessa faccia di «nessuna
#    violazione».  ⭐ `registro` adesso esce non-zero quando non ha potuto
#    leggere, e dichiara quante righe ha filtrato: le due cose insieme
#    distinguono lo zero dal fallimento (rilievo R5.15, forma E8).
$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh registro" > "$TEMP/registro.txt" 2>&1
ST=$?
if [ "$ST" -ne 0 ]; then
	ko "⛔ il registro del server non si e' potuto leggere (uscita $ST):"
	tail -5 "$TEMP/registro.txt" | sed 's/^/        /'
	ko "   senza il secondo testimone le proprieta' NEGATIVE della pagina non"
	ko "   le osserva nessuno, e questo non e' un verde"
	ESITO=1
fi
# ⭐ E IL DENOMINATORE DEL TRASPORTO: quante righe ha filtrato il server, e
#    quante ne sono arrivate qui.  Un troncamento — della finestra, dell'SSH,
#    di chiunque — si vede, invece di somigliare a un silenzio.  ⚠ Il `tail
#    -600` che c'era di la' scartava le righe piu' VECCHIE, cioe' quelle del
#    primo motore: una «byte arrivati DOPO la fine» del primo motore usciva
#    dalla finestra molto prima che il conto dei casi se ne accorgesse
#    (rilievo R5.9).
DICHIARATE=$(sed -n 's/^== RIGHE-DEL-REGISTRO-FILTRATE: \([0-9][0-9]*\)$/\1/p' \
	"$TEMP/registro.txt" | tail -1)
RICEVUTE=$(grep -Ec "B11|DOPO la fine|CONGEDO di commiato|congedo motivo|canale di controllo aperto" \
	"$TEMP/registro.txt")
if [ -z "$DICHIARATE" ]; then
	ko "⛔ il server non ha dichiarato quante righe ha filtrato: quel che e'"
	ko "   arrivato qui non ha denominatore"
	ESITO=1
elif [ "$DICHIARATE" -ne "$RICEVUTE" ]; then
	ko "⛔ il server ne ha filtrate $DICHIARATE e qui ne sono arrivate $RICEVUTE:"
	ko "   qualcosa ha tagliato il registro per strada"
	ESITO=1
else
	inf "righe del registro: $RICEVUTE, tutte quelle che il server ha filtrato"
fi
DOPO=$(grep -c "DOPO la fine" "$TEMP/registro.txt" || true)
SERVITI=$(grep -c "B11 GUASTO: guasto chiesto" "$TEMP/registro.txt" || true)
# ⛔ IL DENOMINATORE DEI GUASTI SERVITI, E NON E' LO ZERO.
#
#    Il banco conosce il numero esatto che deve trovare — i casi della pagina
#    per i motori girati contro il guasto — e lo confrontava **solo con zero**:
#    un giro in cui la pagina abbandonasse dopo il primo caso dava SERVITI=1,
#    «ok guasti serviti: 1», e via verso il verde.  ⚠ E' lo stesso contatore
#    che il 10 agosto 2026 e' stato colto a mentire (26 invece di 21) senza che
#    nessuno se ne accorgesse: la bugia e' passata perche' quel numero non si
#    confrontava con niente (rilievo R5.4, `LEZIONI.md` §1.9 quarta regola).
if [ "$MOTORI_GUASTO" -eq 0 ] || [ "$CASI_ATTESI" -eq 0 ]; then
	ko "⛔ nessun caso e' stato chiesto da nessun motore: non c'e' niente da"
	ko "   dividere, e questo non e' un esito"
	ESITO=1
elif [ "$SERVITI" -ne "$CASI_ATTESI" ]; then
	ko "⛔ il server ha servito $SERVITI guasti, e i $MOTORI_GUASTO motori ne hanno"
	ko "   dichiarati $CASI_ATTESI: i casi che mancano non sono mai arrivati al"
	ko "   server, e il loro esito non e' un giudizio sulla pagina"
	ESITO=1
else
	ok "guasti serviti dal server: $SERVITI su $CASI_ATTESI attesi, da $MOTORI_GUASTO motori"
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
# ⛔ E LE DUE STRADE SI CONTANO TUTT'E DUE, anche quando arrivano insieme.
#    L'`awk` guardava **solo la prima** riga «CONGEDO di commiato» del caso
#    (`&& !visto`) e la classificava su chi arrivava primo: un motore che usi
#    tutt'e due le strade produce due righe distinte — quella di `rcp.c` (il
#    CONGEDO sul canale) e quella di `01-b3-rcp-innesta.py` (il codice di
#    chiusura) — e la seconda veniva scartata.  ⚠ Con quella struttura il banco
#    non poteva, in linea di principio, osservare «due strade per lo stesso
#    motore» (rilievo R5.7).
#
# ⛔ E SI CONTA DENTRO IL CASO, non su tutto il registro.  Un commiato in fondo
#    al giro non dice niente su QUEL caso: il registro e' in ordine, e ogni
#    «guasto chiesto» apre il blocco del suo.  ⚠ Contarli tutti insieme dava 15
#    con 2 attesi, ed era un numero senza significato.
#
# ⛔ E IL DENOMINATORE SONO I MOTORI CHE HANNO GIRATO, contati uno per uno.
#    Era `PROVATI - 1`, cioe' «le chiamate a prova_motore meno il controllo» —
#    ma il controllo puo' essere SALTATO (chiama `firefox` a prescindere da
#    `$MOTORI`), e su una macchina con Chrome e senza Firefox `ATTESI`
#    diventava 0: il banco stampava «il caso e' stato servito 1 volte, e i
#    motori contro il guasto sono 0» addossando alla pagina la propria
#    aritmetica, e nel ramo verde «il congedo arriva ogni volta: 0 su 0»
#    (rilievi R5.16 e R5.5).
ATTESI=$MOTORI_GUASTO
eval "$(awk '
  function chiudi_caso() { if (aperto && (canale_visto || chiusura_vista)) con++ }
  /guasto chiesto dal client:/ {
    chiudi_caso()
    caso = $NF
    aperto = (caso == "respinto-poi-congedo")
    canale_visto = 0; chiusura_vista = 0
    if (aperto) casi++
  }
  /CONGEDO di commiato/ {
    if (aperto) {
      if (index($0, "seconda strada")) {
        if (!chiusura_vista) { chiusura_vista = 1; chiusura++ }
      } else {
        if (!canale_visto) { canale_visto = 1; canale++ }
      }
    }
  }
  END { chiudi_caso(); printf "CASI=%d CON=%d CANALE=%d CHIUSURA=%d\n", casi, con, canale, chiusura }
' "$TEMP/registro.txt")"
inf "il caso «respinto-poi-congedo» e' stato servito $CASI volte"
inf "commiato per il canale di controllo: $CANALE — per il codice di chiusura: $CHIUSURA"
if [ "$CONTROLLO" -ne 1 ]; then
	# ⛔ Il controllo che dice NO non e' un accessorio: senza, il giro arriva a
	#    un verdetto senza che nessuno abbia provato che la pagina sappia dire
	#    di no (`REVIEWER.md` §1 domanda 2).
	ko "⛔ IL CONTROLLO CHE DICE NO NON E' STATO ESEGUITO: manca il browser che"
	ko "   lo gira.  Questo giro non e' un verdetto su B11."
	ESITO=1
fi
if [ "$ATTESI" -eq 0 ]; then
	ko "⛔ nessun motore ha girato contro il server guasto: «$CON su $ATTESI»"
	ko "   sarebbe un controllo positivo superato con zero osservazioni"
	ESITO=1
elif [ "$CASI" -ne "$ATTESI" ]; then
	ko "⛔ il caso e' stato servito $CASI volte, e i motori contro il guasto sono"
	ko "   $ATTESI: il conto qui sotto non avrebbe denominatore"
	ESITO=1
elif [ "$CON" -ne "$ATTESI" ]; then
	ko "⛔ solo $CON commiati su $ATTESI: c'e' un motore che chiude e NON dice"
	ko "   perche', ne' sul canale ne' nel codice di chiusura (§8.1)"
	ESITO=1
else
	ok "⭐ il congedo di §8.1 arriva ogni volta: $CON su $ATTESI"
	# ⛔ E le due strade si DICHIARANO contate, non si dichiarano viste.  Il
	#    ramo verde affermava «e ⛔ per DUE strade diverse» sulla sola
	#    condizione `CON -eq ATTESI`, con `CANALE` e `CHIUSURA` calcolati e mai
	#    provati: due motori che si congedassero tutt'e due sul canale davano
	#    CANALE=2, CHIUSURA=0, e il banco affermava in verde una cosa che i
	#    suoi stessi numeri smentivano nella riga sopra (rilievo R5.5).
	if [ "$CANALE" -ge 1 ] && [ "$CHIUSURA" -ge 1 ]; then
		ok "⭐ e per DUE strade diverse ($CANALE sul canale, $CHIUSURA nel codice"
		ok "   di chiusura): §3.1 punto 3 non e' ridondanza, e' l'altra strada"
	else
		inf "⚠ tutti per la stessa strada ($CANALE sul canale, $CHIUSURA nel"
		inf "  codice di chiusura): §3.1 e' rispettata, ma questo giro NON ha"
		inf "  visto la seconda strada — e con un motore solo non puo' vederla"
	fi
fi

# ---------------------------------------------------------------------------
# ⭐ La ripulitura PRIMA del verdetto: se fallisce, il verdetto lo sa.
ripulisci || ESITO=1

log "Esito"
inf "motori girati: $PROVATI (controllo compreso) — saltati: $SALTATI"
inf "motori contro il server guasto: $MOTORI_GUASTO — controllo eseguito: $CONTROLLO"
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
