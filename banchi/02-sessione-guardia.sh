#!/bin/bash
#
# 02-sessione-guardia.sh — la GUARDIA che sta davanti a ogni misura che dipende
# dalla sessione grafica.  Non avvia niente, non ferma niente: risponde a DUE
# domande invece che a una, e se la seconda risponde male NON lascia misurare.
#
#   bash 02-sessione-guardia.sh                          risponde e basta
#   bash 02-sessione-guardia.sh -- <comando...>          risponde, e SOLO se e'
#                                                        sana esegue il comando
#   bash 02-sessione-guardia.sh --etichetta cattura-30s -- python3 misura.py
#
# ⛔ GIRA SULL'HOST DI NIC-OS, dove vive la sessione grafica.  Da CHUWI non c'e'
#    nessun bus di sessione da interrogare, e la guardia lo dice invece di
#    rispondere «non c'e' nessun monitor» — che sarebbe la forma E8 in persona.
#
# ===========================================================================
# ⛔ PERCHE' ESISTE — due giorni di sessione nera, e una domanda mai fatta
# ===========================================================================
#
# `[M]` 10 agosto 2026, 21:01 → 12 agosto 2026, 11:42.  Per quasi due giorni la
# sessione GNOME di NIC-OS e' stata **viva, completa e NERA**:
#
#     IsSessionRunning          → true
#     nomi sul bus              → 50, con Nautilus e il Terminale accesi
#     GetCurrentState           → **zero monitor, zero monitor logici**
#
# Nessuno se n'e' accorto, e la ragione non e' distrazione: e' che
#
#   ⛔ «la sessione e' VIVA» e «la sessione ha un MONITOR» sono DUE domande
#      diverse, e se ne faceva una sola — quella che rispondeva di si'.
#
# In headless Mutter mette `needs_outputs = false` (`gnome.md` §3.1): senza
# `--virtual-monitor` la sessione nasce perfetta e non ha niente da disegnare.
# Chi avesse misurato la cattura la' sopra avrebbe letto **zero fotogrammi** e
# sarebbe andato a cercare il difetto dentro PipeWire — `PIANO.md` fase 2, *«si
# cerca per mezza giornata dalla parte sbagliata»*.
#
# ⇒ Questa guardia esiste perche' la seconda domanda **si faccia da sola**, e si
#   faccia PRIMA, non dopo aver spiegato uno zero.
#
# ===========================================================================
# ⚠ E COME **NON** SI CONTROLLA SE C'E' UN MONITOR — misurato, e pagato
# ===========================================================================
#
# ⛔ NON con `org.gnome.Shell.Screenshot`.  Su una sessione a zero monitor
#    Mutter tenta una texture 0x0:
#
#       CRITICAL : cogl_texture_2d_new_with_size: assertion 'width >= 1' failed
#       WARNING  : Failed to take screenshot: Failed to create 0x0 texture
#
#    gnome-shell muore, e siccome l'unita' porta
#    `OnFailure=gnome-session-shutdown.target` con `Restart=no`, se ne va
#    **tutta la sessione** `[M]` 12 ago 2026.  ⇒ Il controllo distruggerebbe
#    proprio la cosa che sta controllando, e lo farebbe solo nel caso guasto:
#    verde quando e' sana, macerie quando e' nera.
#
# ⛔ E nemmeno «c'e' il processo gnome-shell», ne' «IsSessionRunning risponde
#    true», ne' «il nome org.gnome.Shell e' sul bus»: sono tutte e tre vere
#    sulla sessione nera.  Sono NECESSARIE e non SUFFICIENTI — la forma E1 di
#    `REVIEWER.md` §2.
#
# ⭐ Si chiede `org.gnome.Mutter.DisplayConfig.GetCurrentState`, che risponde
#    con i monitor uno per uno e non fa male a nessuno.  Lo fa
#    `02-sessione-stato.py`, che questa guardia si limita a mettere davanti al
#    comando altrui.
#
# ===========================================================================
# ⛔ I NUMERI D'USCITA, SCRITTI PRIMA — e sono di TRE bande, apposta
# ===========================================================================
#
# Un rifiuto della guardia e un fallimento del comando che sorveglia NON possono
# avere lo stesso numero, o chi legge l'esito non sa che cosa e' andato storto
# (`REVIEWER.md` §1 punto 4: zero e fallimento sono due cose diverse).
#
#   senza comando   0..7   il verdetto di `02-sessione-stato.py`, tale e quale
#                          (0 SANA · 1 NERA: ZERO MONITOR · 2 MISURA SBAGLIATA ·
#                           3 MONITOR SCELTO DA SE · 4 SESSIONE MORTA ·
#                           5 LETTURA IGNOTA · 6 DISACCORDO · 7 SHELL NON VUOTA)
#
#   con un comando  70+v   ⛔ LA GUARDIA HA RIFIUTATO, con v = il verdetto:
#                          71 nera, 74 morta, 75 non ho potuto leggere…  Il
#                          comando NON e' stato eseguito, e non c'e' nessun
#                          numero da attribuire a nessuno.
#                    79    ⛔ la sessione era sana PRIMA e non lo e' PIU' DOPO:
#                          la scena e' caduta sotto la misura.  Vale piu' del
#                          numero del comando — anche se il comando dice 0.
#                          (Una sessione nera cade da sola al primo screenshot:
#                          non e' un caso di scuola.)
#                    altro l'uscita del comando, tale e quale
#
# ⚠ Non c'e' un'opzione per «misura lo stesso».  Una guardia che si puo' saltare
#   si salta, e il giorno in cui la si salta e' quello in cui serviva.  Chi deve
#   davvero misurare su una sessione guasta — F2.1 quando innesta M9 — non passa
#   di qui: usa `02-sessione-lancia.sh guasto`, che la scena guasta la DICHIARA.
#
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
STRUMENTO=${STRUMENTO:-$QUI/02-sessione-stato.py}
ESITI=${ESITI:-$QUI/02-sessione-esiti.jsonl}
ATTESA=${MISURA:-1920x1080}
ETICHETTA=""

U=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$U}
SCENA_PRIMA=$RUNTIME/f21-guardia-prima.json
SCENA_DOPO=$RUNTIME/f21-guardia-dopo.json

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
att() { printf '    \033[1;33m⚠\033[0m   %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

uso()
{
	sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
	exit "${1:-2}"
}

# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
	case "$1" in
	--attesa)    ATTESA=${2:?serve una misura LARGHEZZAxALTEZZA}; shift 2 ;;
	--etichetta) ETICHETTA=${2:?serve un nome di scena}; shift 2 ;;
	--esiti)     ESITI=${2:?serve un file}; shift 2 ;;
	-h|--aiuto)  uso 0 ;;
	--)          shift; break ;;
	-*)          echo "⛔ opzione ignota: $1" >&2; uso 2 ;;
	*)           break ;;
	esac
done
COMANDO=("$@")
[ -n "$ETICHETTA" ] || ETICHETTA=${COMANDO[0]:-solo-guardia}

# ---------------------------------------------------------------------------
# ⛔ LE DUE DOMANDE, LETTE DALLA SCENA REGISTRATA DA `02-sessione-stato.py`.
#
# Si leggono dalla stessa scena che ha prodotto il verdetto, non da una seconda
# interrogazione: due letture in due momenti diversi possono raccontare due
# sessioni diverse, e allora la guardia direbbe una cosa e il verdetto un'altra.
# ---------------------------------------------------------------------------
due_domande() # $1 = file della scena
{
	python3 - "$1" <<'PY'
import json, sys

VERDE, ROSSO, GIALLO, FINE = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
try:
    with open(sys.argv[1]) as f:
        s = json.load(f)
except OSError as err:
    print(f"    {ROSSO}NO{FINE}  ⛔ non rileggo la scena: {err}")
    sys.exit(1)

pid = s.get("shell_pid")
gira = s.get("sessione_gira")
viva = bool(pid) and gira is True
d = s.get("display")
monitor = d["monitor"] if d else None

def riga(n, domanda, risposta, buona):
    colore = VERDE if buona else ROSSO
    print(f"    {n}. {domanda:<44} {colore}{risposta}{FINE}")

riga(1, "la sessione e' VIVA?",
     ("si', gnome-shell " + " ".join(str(p) for p in pid) +
      " e IsSessionRunning=true") if viva
     else f"NO (pid={pid}, IsSessionRunning={gira})", viva)

if monitor is None:
    riga(2, "la sessione ha un MONITOR?",
         "NON L'HO POTUTO CHIEDERE (GetCurrentState non ha risposto)", False)
elif not monitor:
    riga(2, "la sessione ha un MONITOR?", "NO — ZERO monitor", False)
else:
    nomi = ", ".join(f"{m['connettore']}/{m['prodotto']}" for m in monitor)
    riga(2, "la sessione ha un MONITOR?", f"{len(monitor)}: {nomi}", len(monitor) == 1)

# ⛔ La forma esatta del difetto del 10-12 agosto: la prima si', la seconda no.
if viva and monitor is not None and not monitor:
    print(f"\n    {ROSSO}⛔⛔ VIVA E NERA — e' la forma esatta del difetto vissuto due"
          f" giorni{FINE}")
    print("        su questa macchina.  Un banco che avesse fatto solo la prima")
    print("        domanda avrebbe scritto «sessione a posto» e poi attribuito")
    print("        zero fotogrammi a PipeWire, alla codifica, o al proprio codice.")
    print(f"    {GIALLO}⚠{FINE}   E non chiamarle uno screenshot per verificare: su zero")
    print("        monitor `Shell.Screenshot` fa cadere TUTTA la sessione [M].")
PY
}

# ---------------------------------------------------------------------------
misura() # $1 = etichetta ; $2 = file scena
{
	python3 "$STRUMENTO" --attesa "$ATTESA" --dal-bus \
	    --etichetta "$1" --esiti "$ESITI" --registra "$2"
	return $?
}

registra_giro() # $1 prima  $2 dopo  $3 uscita comando  $4 uscita guardia
{
	python3 - "$ESITI" "$1" "$2" "$3" "$4" "$ETICHETTA" "${COMANDO[*]:-}" <<'PY'
import json, sys, time
esiti, prima, dopo, ecom, eguardia, etichetta, comando = sys.argv[1:8]
with open(esiti, "a") as f:
    f.write(json.dumps({
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "banco": "F2.1-guardia",
        "scena": etichetta,
        "comando_sorvegliato": comando or None,
        "verdetto_prima": int(prima),
        "verdetto_dopo": None if dopo == "-" else int(dopo),
        "uscita_comando": None if ecom == "-" else int(ecom),
        "uscita_guardia": int(eguardia),
    }, ensure_ascii=False) + "\n")
PY
}

# ---------------------------------------------------------------------------
log "La guardia della sessione — DUE domande, non una"
inf "misura chiesta: $ATTESA · scena: «$ETICHETTA»"
[ ${#COMANDO[@]} -gt 0 ] && inf "comando sorvegliato: ${COMANDO[*]}" \
                         || inf "nessun comando: rispondo e basta"

log "Prima della misura"
misura "guardia-prima:$ETICHETTA" "$SCENA_PRIMA"
PRIMA=$?

log "⛔ Le due domande, separate"
due_domande "$SCENA_PRIMA"

# ---------------------------------------------------------------------------
if [ ${#COMANDO[@]} -eq 0 ]; then
	registra_giro "$PRIMA" - - "$PRIMA"
	log "Il verdetto"
	if [ "$PRIMA" -eq 0 ]; then
		ok "sessione SANA: chi misura adesso misura il proprio anello"
	else
		ko "⛔ sessione NON sana (verdetto $PRIMA): non e' il momento di misurare"
	fi
	exit "$PRIMA"
fi

if [ "$PRIMA" -ne 0 ]; then
	log "⛔ NON MISURO"
	ko "⛔⛔ la guardia RIFIUTA: il verdetto sulla sessione e' $PRIMA."
	ko "   Il comando «${COMANDO[*]}» NON e' stato eseguito, e non c'e'"
	ko "   nessun numero da attribuire a nessuno: qualunque zero uscito adesso"
	ko "   sarebbe uno zero della SESSIONE, non del vostro anello."
	inf "si rimette cosi', ed e' un minuto:"
	inf "    bash $QUI/02-sessione-lancia.sh sano"
	inf "e perche' non torni nera al prossimo riavvio del server:"
	inf "    bash /media/REMOTIX/provision-server.sh monitor"
	registra_giro "$PRIMA" - - $((70 + PRIMA))
	exit $((70 + PRIMA))
fi

ok "sessione SANA: eseguo «${COMANDO[*]}»"
log "La misura sorvegliata"
"${COMANDO[@]}"
E_COMANDO=$?
inf "il comando e' uscito con $E_COMANDO"

# ⛔ E SI RIGUARDA DOPO.  Non e' pignoleria: una sessione headless senza monitor
#    cade da sola al primo screenshot, e chi la vedesse cadere a meta' di una
#    misura andrebbe a cercare il difetto nel proprio codice `[M]` 12 ago 2026.
#    Un numero preso su una scena caduta a meta' non e' un numero.
log "Dopo la misura — la scena e' ancora quella che ho dichiarato?"
misura "guardia-dopo:$ETICHETTA" "$SCENA_DOPO"
DOPO=$?
due_domande "$SCENA_DOPO"

log "Il verdetto"
if [ "$DOPO" -ne 0 ]; then
	ko "⛔⛔ LA SESSIONE ERA SANA PRIMA (0) E ADESSO E' $DOPO."
	ko "   La scena e' cambiata SOTTO la misura: il numero del comando"
	ko "   ($E_COMANDO) e' stato preso su una scena che non e' quella"
	ko "   dichiarata, e non vale — nemmeno se e' verde."
	registra_giro "$PRIMA" "$DOPO" "$E_COMANDO" 79
	exit 79
fi
ok "sessione sana prima ($PRIMA) e dopo ($DOPO): la scena ha retto tutta la misura"
inf "l'uscita e' quella del comando, tale e quale: $E_COMANDO"
registra_giro "$PRIMA" "$DOPO" "$E_COMANDO" "$E_COMANDO"
exit "$E_COMANDO"
