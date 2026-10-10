#!/bin/bash
#
# 02-sessione-guardia.sh — the GUARD that stands in front of every measurement that
# depends on the graphical session.  It starts nothing, stops nothing: it answers TWO
# questions instead of one, and if the second answers badly it does NOT let you measure.
#
#   bash 02-sessione-guardia.sh                          just answers
#   bash 02-sessione-guardia.sh -- <command...>          answers, and ONLY if the
#                                                        session is healthy runs the command
#   bash 02-sessione-guardia.sh --etichetta cattura-30s -- python3 misura.py
#
# ⛔ IT RUNS ON THE NIC-OS HOST, where the graphical session lives.  From CHUWI there
#    is no session bus to query, and the guard says so instead of
#    answering «there is no monitor» — which would be the E8 form in person.
#
# ===========================================================================
# ⛔ WHY IT EXISTS — two days of black session, and a question never asked
# ===========================================================================
#
# `[M]` 10 Aug 2026, 21:01 → 12 Aug 2026, 11:42.  For almost two days the
# GNOME session of NIC-OS was **alive, complete and BLACK**:
#
#     IsSessionRunning          → true
#     names on the bus          → 50, with Nautilus and the Terminal running
#     GetCurrentState           → **zero monitors, zero logical monitors**
#
# Nobody noticed, and the reason is not carelessness: it is that
#
#   ⛔ «the session is ALIVE» and «the session has a MONITOR» are TWO different
#      questions, and only one was asked — the one that answered yes.
#
# In headless mode Mutter sets `needs_outputs = false` (`STUDI.md` §gnome §3.1): without
# `--virtual-monitor` the session is born perfect and has nothing to draw.
# Whoever had measured capture on top of it would have read **zero frames** and
# gone looking for the defect inside PipeWire — `PIANO.md` phase 2, *«you
# search for half a day on the wrong side»*.
#
# ⇒ This guard exists so that the second question **asks itself**, and is asked
#   BEFORE, not after explaining a zero.
#
# ===========================================================================
# ⚠ AND HOW **NOT** TO CHECK WHETHER THERE IS A MONITOR — measured, and paid for
# ===========================================================================
#
# ⛔ NOT with `org.gnome.Shell.Screenshot`.  On a session with zero monitors
#    Mutter attempts a 0x0 texture:
#
#       CRITICAL : cogl_texture_2d_new_with_size: assertion 'width >= 1' failed
#       WARNING  : Failed to take screenshot: Failed to create 0x0 texture
#
#    gnome-shell dies, and since the unit carries
#    `OnFailure=gnome-session-shutdown.target` with `Restart=no`, **the whole
#    session** goes away `[M]` 12 Aug 2026.  ⇒ The check would destroy
#    the very thing it is checking, and it would do so only in the faulty case:
#    green when healthy, rubble when black.
#
# ⛔ Nor «the gnome-shell process is there», nor «IsSessionRunning answers
#    true», nor «the name org.gnome.Shell is on the bus»: all three are true
#    on the black session.  They are NECESSARY and not SUFFICIENT — the E1 form of
#    `REVIEWER.md` §2.
#
# ⭐ What is asked is `org.gnome.Mutter.DisplayConfig.GetCurrentState`, which answers
#    with the monitors one by one and hurts nobody.  It is done by
#    `02-sessione-stato.py`, which this guard merely puts in front of someone
#    else's command.
#
# ===========================================================================
# ⛔ THE EXIT CODES, WRITTEN BEFOREHAND — and they come in THREE bands, on purpose
# ===========================================================================
#
# A refusal by the guard and a failure of the command it watches CANNOT have
# the same number, or whoever reads the outcome does not know what went wrong
# (`REVIEWER.md` §1 point 4: zero and failure are two different things).
#
#   no command      0..7   the verdict of `02-sessione-stato.py`, as it is
#                          (0 HEALTHY · 1 BLACK: ZERO MONITORS · 2 WRONG SIZE ·
#                           3 MONITOR CHOSEN BY ITSELF · 4 SESSION DEAD ·
#                           5 UNKNOWN READING · 6 DISAGREEMENT · 7 SHELL NOT EMPTY)
#
#   with a command  70+v   ⛔ THE GUARD REFUSED, with v = the verdict:
#                          71 black, 74 dead, 75 I could not read…  The
#                          command was NOT run, and there is no
#                          number to attribute to anybody.
#                    79    ⛔ the session was healthy BEFORE and is NO LONGER AFTER:
#                          the scene fell under the measurement.  It counts more than
#                          the command's number — even if the command says 0.
#                          (A black session falls by itself at the first screenshot:
#                          it is not a textbook case.)
#                    other the command's exit, as it is
#
# ⚠ There is no option for «measure anyway».  A guard that can be skipped
#   gets skipped, and the day it is skipped is the day it was needed.  Whoever must
#   really measure on a faulty session — F2.1 when it injects M9 — does not pass
#   through here: they use `02-sessione-lancia.sh guasto`, which DECLARES the faulty scene.
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
	--attesa)    ATTESA=${2:?a size WIDTHxHEIGHT is needed}; shift 2 ;;
	--etichetta) ETICHETTA=${2:?a scene name is needed}; shift 2 ;;
	--esiti)     ESITI=${2:?a file is needed}; shift 2 ;;
	-h|--aiuto)  uso 0 ;;
	--)          shift; break ;;
	-*)          echo "⛔ unknown option: $1" >&2; uso 2 ;;
	*)           break ;;
	esac
done
COMANDO=("$@")
[ -n "$ETICHETTA" ] || ETICHETTA=${COMANDO[0]:-solo-guardia}

# ---------------------------------------------------------------------------
# ⛔ THE TWO QUESTIONS, READ FROM THE SCENE RECORDED BY `02-sessione-stato.py`.
#
# They are read from the same scene that produced the verdict, not from a second
# query: two readings at two different moments can tell about two different
# sessions, and then the guard would say one thing and the verdict another.
# ---------------------------------------------------------------------------
due_domande() # $1 = scene file
{
	python3 - "$1" <<'PY'
import json, sys

VERDE, ROSSO, GIALLO, FINE = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
try:
    with open(sys.argv[1]) as f:
        s = json.load(f)
except OSError as err:
    print(f"    {ROSSO}NO{FINE}  ⛔ cannot re-read the scene: {err}")
    sys.exit(1)

pid = s.get("shell_pid")
gira = s.get("sessione_gira")
viva = bool(pid) and gira is True
d = s.get("display")
monitor = d["monitor"] if d else None

def riga(n, domanda, risposta, buona):
    colore = VERDE if buona else ROSSO
    print(f"    {n}. {domanda:<44} {colore}{risposta}{FINE}")

riga(1, "is the session ALIVE?",
     ("yes, gnome-shell " + " ".join(str(p) for p in pid) +
      " and IsSessionRunning=true") if viva
     else f"NO (pid={pid}, IsSessionRunning={gira})", viva)

if monitor is None:
    riga(2, "does the session have a MONITOR?",
         "I COULD NOT ASK (GetCurrentState did not answer)", False)
elif not monitor:
    riga(2, "does the session have a MONITOR?", "NO — ZERO monitors", False)
else:
    nomi = ", ".join(f"{m['connettore']}/{m['prodotto']}" for m in monitor)
    riga(2, "does the session have a MONITOR?", f"{len(monitor)}: {nomi}", len(monitor) == 1)

# ⛔ The exact form of the 10-12 Aug defect: the first yes, the second no.
if viva and monitor is not None and not monitor:
    print(f"\n    {ROSSO}⛔⛔ ALIVE AND BLACK — it is the exact form of the defect lived for two"
          f" days{FINE}")
    print("        on this machine.  A bench that had asked only the first")
    print("        question would have written «session fine» and then blamed")
    print("        zero frames on PipeWire, on the encoding, or on its own code.")
    print(f"    {GIALLO}⚠{FINE}   And do not call a screenshot to check: on zero")
    print("        monitors `Shell.Screenshot` brings down the WHOLE session [M].")
PY
}

# ---------------------------------------------------------------------------
misura() # $1 = label ; $2 = scene file
{
	python3 "$STRUMENTO" --attesa "$ATTESA" --dal-bus \
	    --etichetta "$1" --esiti "$ESITI" --registra "$2"
	return $?
}

registra_giro() # $1 before  $2 after  $3 command exit  $4 guard exit
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
log "The session guard — TWO questions, not one"
inf "requested size: $ATTESA · scene: «$ETICHETTA»"
[ ${#COMANDO[@]} -gt 0 ] && inf "watched command: ${COMANDO[*]}" \
                         || inf "no command: I just answer"

log "Before the measurement"
misura "guardia-prima:$ETICHETTA" "$SCENA_PRIMA"
PRIMA=$?

log "⛔ The two questions, kept apart"
due_domande "$SCENA_PRIMA"

# ---------------------------------------------------------------------------
if [ ${#COMANDO[@]} -eq 0 ]; then
	registra_giro "$PRIMA" - - "$PRIMA"
	log "The verdict"
	if [ "$PRIMA" -eq 0 ]; then
		ok "session HEALTHY: whoever measures now measures their own link"
	else
		ko "⛔ session NOT healthy (verdict $PRIMA): it is not the moment to measure"
	fi
	exit "$PRIMA"
fi

if [ "$PRIMA" -ne 0 ]; then
	log "⛔ I DO NOT MEASURE"
	ko "⛔⛔ the guard REFUSES: the verdict on the session is $PRIMA."
	ko "   The command «${COMANDO[*]}» was NOT run, and there is"
	ko "   no number to attribute to anybody: any zero that came out now"
	ko "   would be a zero of the SESSION, not of your link."
	inf "this is how to set it right, and it takes a minute:"
	inf "    bash $QUI/02-sessione-lancia.sh sano"
	inf "and so that it does not turn black again at the next server reboot:"
	inf "    bash /media/REMOTIX/provision-server.sh monitor"
	registra_giro "$PRIMA" - - $((70 + PRIMA))
	exit $((70 + PRIMA))
fi

ok "session HEALTHY: running «${COMANDO[*]}»"
log "The watched measurement"
"${COMANDO[@]}"
E_COMANDO=$?
inf "the command exited with $E_COMANDO"

# ⛔ AND IT LOOKS AGAIN AFTER.  It is not fussiness: a headless session without a monitor
#    falls by itself at the first screenshot, and whoever saw it fall in the middle of a
#    measurement would go looking for the defect in their own code `[M]` 12 Aug 2026.
#    A number taken on a scene that fell midway is not a number.
log "After the measurement — is the scene still the one I declared?"
misura "guardia-dopo:$ETICHETTA" "$SCENA_DOPO"
DOPO=$?
due_domande "$SCENA_DOPO"

log "The verdict"
if [ "$DOPO" -ne 0 ]; then
	ko "⛔⛔ THE SESSION WAS HEALTHY BEFORE (0) AND NOW IT IS $DOPO."
	ko "   The scene changed UNDER the measurement: the command's number"
	ko "   ($E_COMANDO) was taken on a scene that is not the declared"
	ko "   one, and it does not count — not even if it is green."
	registra_giro "$PRIMA" "$DOPO" "$E_COMANDO" 79
	exit 79
fi
ok "session healthy before ($PRIMA) and after ($DOPO): the scene held for the whole measurement"
inf "the exit is the command's, as it is: $E_COMANDO"
registra_giro "$PRIMA" "$DOPO" "$E_COMANDO" "$E_COMANDO"
exit "$E_COMANDO"
