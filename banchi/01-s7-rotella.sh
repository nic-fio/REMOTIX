#!/bin/bash
#
# 01-s7-rotella.sh — S7: which way the wheel turns.  `RCP.md` §7.3
#
#   bash 01-s7-rotella.sh            the whole measurement, and puts the machine back as it was
#   bash 01-s7-rotella.sh --tieni    the same, but leaves the virtual monitor standing
#
# ⚠ IT RUNS ON THE SERVER (192.168.0.2), inside the user's session.  The browser
#   of this measurement is NOT the laptop's: the page must be **inside** the
#   compositor into which we inject, or it does not measure the compositor.
#
# ---------------------------------------------------------------------------
# WHAT IT MEASURES
#
# `RCP.md` §7.3 keeps the SIGN of the wheel `[?]`: the client sends `+120`
# because the user turned the wheel **up**, and nobody knows whether the server
# should inject `+120` or `-120` to make the remote screen go the same way.
# This bench injects with `libei` — the product's road — and looks at what
# reaches the page.
#
# ⭐ And the page is the RIGHT instrument, not a convenient one: `deltaY` of the
#    `wheel` event is the same quantity the RCP client reads when the user
#    really turns the wheel.  The comparison is between two uses of the same
#    convention, not between two worlds.
#
# ---------------------------------------------------------------------------
# ⛔ THE THREE CHECKS, AND TWO OF THEM ARE THE ONES THAT SAY *NO*
#
#   1. THE OPPOSITE SIGN.  `-120` is injected too.  If the page goes the
#      same way, one is not measuring the sign: one is measuring that
#      «something moves».  ⭐ It is the check the first draft of the bench
#      had already written right.
#
#   2. `natural-scroll` IN BOTH STATES.  If the sign changes with the gsetting,
#      the number that would end up in `RCP.md` §7.3 would be **the sign of the
#      configuration of THIS desktop**, and the symptom for the user would be
#      «the wheel goes backwards» on half of the installations — form E11.
#      ⛔ It is the check that was missing (finding R3.25).
#
#      ⛔ AND THE INJECTOR IS REDONE FROM SCRATCH AT EVERY STATE.  A compositor can
#         read the device preferences **when the device is born**: changing the
#         gsetting under a device already alive, the check would say «the sign
#         does not change» even in a world where it changes — that is it would be
#         blind precisely in the case it must see.
#
#   3. THE SILENCE.  At the end one stays still for ten seconds without injecting
#      anything and verifies that the page does NOT record clicks.  Without it,
#      «the page saw a click» does not prove that we sent it.
#
# And two positive controls on the instrument, before all of them: the page
# declares it placed itself 8 000 pixels from the edge (if the document does not
# scroll, every «it did not move» that follows would mean nothing — `LEZIONI.md`
# §1.9 rule 2), and it declares the size of the screen it sees, which must be
# that of the virtual monitor we asked for.
#
# ---------------------------------------------------------------------------
# ⛔ THE INITIAL STATE, DECLARED AND VERIFIED (B0.1)
#
#   - a live, headless GNOME session (`00-sessione-gnome.sh stato`);
#   - ⛔ **a monitor**.  A `--headless` Shell without `--virtual-monitor` has
#     ZERO logical monitors (`[M]` 10 Aug 2026: `GetCurrentState` answers
#     `[]`), and without a monitor there is no window to send a click to.
#     ⚠ And `RecordVirtual` alone is NOT enough: measured, the monitors stay zero
#     until a PipeWire consumer negotiates the size.  So here
#     `--virtual-monitor` is added to the Shell's unit, it is restarted, **and it
#     is verified on the process's command line** that the option is in
#     force — not that it is written in the file (`LEZIONI.md` §1.11);
#   - the two starting `natural-scroll` values (mouse and touchpad), which are put back.
#
# ⛔ AND EVERYTHING THAT IS CHANGED IS DECLARED AND PUT BACK: the systemd
#    drop-in, the gsettings, the session.  A state that survives the test
#    falsifies the next test — rule B0.2, written for the certificate exception
#    but true for a desktop too.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
PORTA=${PORTA:-8877}
REGISTRO=$QUI/01-s7-esiti.jsonl
SESSIONE_SH=${SESSIONE_SH:-/media/REMOTIX/tmp/00-sessione-gnome.sh}
DROPIN_DIR=$HOME/.config/systemd/user/org.gnome.Shell@wayland.service.d
# ⛔ `zz-`, and the name is NOT aesthetics: `[M]` 10 Aug 2026.  systemd orders the
#    drop-ins **by file name**, mixing the folders — not by precedence of the
#    folder.  Phase 0 put its own in
#    `/etc/systemd/user/…/remotix-headless.conf`, and a file called
#    `99-s7-…` ends up BEFORE it: the first run of this bench wrote the
#    drop-in, restarted the session, and found the Shell still without
#    `--virtual-monitor`.  ⭐ The B0.1 check said so — «it is verified on the
#    process's command line, not on the file» — instead of measuring for
#    half an hour a window that did not exist.
DROPIN=$DROPIN_DIR/zz-s7-monitor-virtuale.conf
TELA=${TELA:-1920x1080}
PAROLA=${PAROLA:-nicfio}
TIENI=0
[ "${1:-}" = --tieni ] && TIENI=1

export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}

# ---------------------------------------------------------------------------
# ⛔ `--pulisci`, and it serves to close a hole this bench opened by itself.
#
#    `[M]` 10 Aug 2026: with `--tieni` the drop-in stays.  The next run finds
#    the Shell **already** with `--virtual-monitor`, concludes «I did not put it» and
#    does not remove it: the state stays on everyone's machine, and neither of the
#    two runs did anything wrong.  It is rule B0.2 seen from the side of
#    whoever leaves the state instead of finding it.
# ---------------------------------------------------------------------------
if [ "${1:-}" = --pulisci ]; then
	if [ -f "$DROPIN" ]; then
		rm -f "$DROPIN"
		systemctl --user daemon-reload
		printf 'removed %s: restarting the session\n' "$DROPIN"
		bash "$SESSIONE_SH" ferma
		bash "$SESSIONE_SH" avvia
		printf 'gnome-shell now: %s\n' \
		    "$(tr '\0' ' ' < "/proc/$(pgrep -u "$(id -u)" -x gnome-shell | head -1)/cmdline")"
	else
		printf 'no S7 drop-in to remove\n'
	fi
	exit 0
fi

T=$(mktemp -d)
log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0
DROPIN_NOSTRO=0
MOUSE_PRIMA=
TOUCH_PRIMA=
PID_FF=
PID_INI=
PID_RACC=

ferma_iniettore()
{
	[ -z "$PID_INI" ] && return 0
	exec 9>&- 2>/dev/null
	kill "$PID_INI" 2>/dev/null
	wait "$PID_INI" 2>/dev/null
	PID_INI=
}

congedo()
{
	printf '\n\033[1m== The farewell\033[0m\n'
	[ -n "$PID_FF" ]   && { kill "$PID_FF"   2>/dev/null; wait "$PID_FF"   2>/dev/null; }
	ferma_iniettore
	[ -n "$PID_RACC" ] && { kill "$PID_RACC" 2>/dev/null; wait "$PID_RACC" 2>/dev/null; }
	if [ -n "$MOUSE_PRIMA" ]; then
		gsettings set org.gnome.desktop.peripherals.mouse natural-scroll "$MOUSE_PRIMA"
		gsettings set org.gnome.desktop.peripherals.touchpad natural-scroll "$TOUCH_PRIMA"
		inf "natural-scroll put back: mouse=$MOUSE_PRIMA touchpad=$TOUCH_PRIMA"
	fi
	if [ "$DROPIN_NOSTRO" = 1 ] && [ "$TIENI" = 0 ]; then
		rm -f "$DROPIN"
		systemctl --user daemon-reload
		inf "removed the drop-in $DROPIN: the session goes back to how it was"
		bash "$SESSIONE_SH" ferma
		bash "$SESSIONE_SH" avvia
	elif [ "$DROPIN_NOSTRO" = 1 ]; then
		inf "⚠ THE DROP-IN STAYS ($DROPIN): the session still has a virtual monitor"
	fi
	rm -rf "$T"
}
trap congedo EXIT

# ---------------------------------------------------------------------------
log "1. The initial state (B0.1)"

bash "$SESSIONE_SH" stato
if ! pgrep -u "$(id -u)" -x gnome-shell >/dev/null; then
	inf "there is no session: I start it"
	bash "$SESSIONE_SH" avvia || { ko "the session does not start: the measurement does not begin"; exit 2; }
fi

riga_shell() { tr '\0' ' ' < "/proc/$(pgrep -u "$(id -u)" -x gnome-shell | head -1)/cmdline"; }

RIGA=$(riga_shell)
inf "gnome-shell: $RIGA"
case "$RIGA" in
*--virtual-monitor*)
	ok "the Shell already has a virtual monitor: I do not touch the unit"
	;;
*)
	inf "no virtual monitor: I add the drop-in and restart the session"
	mkdir -p "$DROPIN_DIR"
	cat >"$DROPIN" <<CONF
[Service]
ExecStart=
ExecStart=/usr/bin/gnome-shell --headless --no-x11 --virtual-monitor $TELA
CONF
	DROPIN_NOSTRO=1
	systemctl --user daemon-reload
	bash "$SESSIONE_SH" ferma || { ko "the session did not stop"; exit 2; }
	bash "$SESSIONE_SH" avvia || { ko "the session did not start again"; exit 2; }
	RIGA=$(riga_shell)
	inf "gnome-shell now: $RIGA"
	# ⛔ It is verified on the PROCESS'S COMMAND LINE, not on the file: that
	#    the option is written is not that it is in force.
	case "$RIGA" in
	*--virtual-monitor*) ok "the virtual monitor is in force" ;;
	*)  ko "the drop-in had no effect: the Shell runs without --virtual-monitor"; exit 2 ;;
	esac
	;;
esac
sleep 2
gdbus call --session -d org.gnome.Mutter.DisplayConfig -o /org/gnome/Mutter/DisplayConfig \
    -m org.gnome.Mutter.DisplayConfig.GetCurrentState >"$T/monitor.txt" 2>&1
inf "DisplayConfig says (first 300 characters):"
printf '        %s\n' "$(cut -c1-300 "$T/monitor.txt")"

MOUSE_PRIMA=$(gsettings get org.gnome.desktop.peripherals.mouse natural-scroll)
TOUCH_PRIMA=$(gsettings get org.gnome.desktop.peripherals.touchpad natural-scroll)
inf "starting natural-scroll: mouse=$MOUSE_PRIMA touchpad=$TOUCH_PRIMA (put back at the end)"

# ---------------------------------------------------------------------------
log "2. The injector"

BIN=/media/REMOTIX/tmp/01-s7-rotella
inf "compiling in the devroot (gcc and the libei headers live there, not on the system)"
printf '%s\n' "$PAROLA" | bash /media/REMOTIX/enter.sh \
    "gcc -O1 -Wall -o /srv/src/01-s7-rotella-bin /srv/src/01-s7-rotella.c \
     \$(pkg-config --cflags --libs libei-1.0 gio-2.0 gio-unix-2.0)"
if [ ! -x /media/REMOTIX/src/01-s7-rotella-bin ]; then
	ko "the injector did not compile: see above"
	exit 3
fi
cp /media/REMOTIX/src/01-s7-rotella-bin "$BIN"
ok "injector compiled: $BIN"

# ---------------------------------------------------------------------------
log "3. The collector"

python3 -u "$QUI/01-s7-raccogli.py" "$PORTA" >"$T/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "the collector did not start:"
	sed 's/^/        /' "$T/racc.log"
	exit 4
fi
ok "collector on 127.0.0.1:$PORTA"

systemctl --user show-environment >"$T/ambiente.txt" 2>&1
WD=$(sed -n 's/^WAYLAND_DISPLAY=//p' "$T/ambiente.txt" | head -1)
if [ -z "$WD" ]; then
	ko "the session does not publish WAYLAND_DISPLAY: the browser would not find the compositor"
	exit 4
fi
inf "WAYLAND_DISPLAY=$WD"
URL="http://127.0.0.1:$PORTA/01-s7-pagina.html"

# ---------------------------------------------------------------------------
# The log reader.
#
# ⛔ THE PLACEHOLDER IS THE LINE NUMBER OF THE FILE, NOT THE PAGE'S COUNTER.
#
#    `[M]` 10 Aug 2026, second run of this bench: the page's counter starts
#    again from 1 at every load.  The log already contained a line `n=1` from
#    the previous run, the placeholder was 1, and the new line — `n=1` too —
#    was never «greater than the placeholder».  The bench printed «the page did
#    not say PRONTA in 45 s» **while the collector was writing it**: a red on a
#    healthy instrument, and the real cause was the way of searching.
#
#    Now the placeholder is the position in the file (which always grows) and
#    the line is recognised ALSO by the mark of the round, which the page draws
#    at every load.  They are the two halves of B2's finding R8.10 together.
#
# Prints: line<TAB>round<TAB>deltaY<TAB>scroll<TAB>start<TAB>screen<TAB>engine
leggi_riga() # $1 = minimum line (exclusive), $2 = type, $3 = mark of the round (or empty)
{
	python3 - "$REGISTRO" "$1" "$2" "${3:-}" <<'PY'
import json, os, sys
percorso, minimo, tipo, giro = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
if not os.path.exists(percorso):
    sys.exit(1)
righe = open(percorso, encoding="utf-8").read().splitlines()
for i in range(minimo, len(righe)):
    try:
        d = json.loads(righe[i])
    except Exception:
        continue
    if d.get("tipo") != tipo:
        continue
    if giro and d.get("giro") != giro:
        continue
    print(i + 1, d.get("giro"), d.get("deltaY"), d.get("scorrimento"), d.get("partenza"),
          d.get("schermo"), (d.get("motore") or "")[:120], sep="\t")
    sys.exit(0)
sys.exit(1)
PY
}

attendi_riga() # $1 = minimum line, $2 = type, $3 = seconds, $4 = round
{
	local i=0 trovata=""
	while [ "$i" -lt "${3:-20}" ]; do
		trovata=$(leggi_riga "$1" "$2" "${4:-}") && { printf '%s\n' "$trovata"; return 0; }
		sleep 1
		i=$((i + 1))
	done
	return 1
}

# ---------------------------------------------------------------------------
# ⛔⛔ THE ORDER BETWEEN INJECTOR AND BROWSER, AND IT IS THE MOST EXPENSIVE THING LEARNED HERE.
#
# `[M]` 10 Aug 2026, after three empty runs:
#
#   - browser started BEFORE the injector  ⇒ NOTHING reaches the page:
#     neither wheel, nor buttons, **nor the movement of the pointer**;
#   - injector started BEFORE the browser  ⇒ everything arrives.
#
# And in both cases Mutter receives the injection: the inactivity clock
# (`org.gnome.Mutter.IdleMonitor.GetIdletime`) drops from 35 952 ms to
# 1 013 ms at the first movement.  That is the compositor takes it and does not
# deliver it to the window.
#
# ⚠ The plausible explanation — a session without physical devices announces
#   a `wl_seat` **without a pointer**, and the client that starts first never
#   subscribes — stays `[?]`: we have not verified it.  What is `[M]` is
#   the order.
#
# ⭐ AND IT IS NOT A BENCH DETAIL: in the product the graphical session is born
#    without any input device, and the applications opened **before** a
#    client connects could find themselves in the same state — the user
#    moves the mouse and that window does not answer.  It is a question for
#    phases 2 and 6, and it must be asked there instead of being rediscovered by a user.
# ---------------------------------------------------------------------------
avvia_iniettore()
{
	mkfifo "$T/comandi.$$"
	"$BIN" <"$T/comandi.$$" >>"$T/iniettore.log" 2>&1 &
	PID_INI=$!
	exec 9>"$T/comandi.$$"
	rm -f "$T/comandi.$$"
	# ⛔ One waits for the ABSOLUTE device — whole line, not prefix:
	#    «PRONTO» is the start of «PRONTO-RELATIVO», and with the relative one the
	#    pointer ends up wherever.  Only if it does not arrive after twenty seconds
	#    does one settle for the relative one, AND IT IS SAID.
	local i=0
	while [ "$i" -lt 20 ]; do
		if grep -x "S7: PRONTO" "$T/iniettore.log" >/dev/null 2>&1; then
			return 0
		fi
		sleep 1
		i=$((i + 1))
	done
	if grep -x "S7: PRONTO-RELATIVO" "$T/iniettore.log" >/dev/null 2>&1; then
		inf "⚠ no ABSOLUTE device: one goes relative, and the position of the"
		inf "  pointer is not guaranteed"
		return 0
	fi
	return 1
}

avvia_browser()
{
	mkdir -p "$T/profilo"
	cat >"$T/profilo/user.js" <<'PREF'
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("general.smoothScroll", false);
PREF
	N=$(wc -l < "$REGISTRO" 2>/dev/null || echo 0)
	MOZ_ENABLE_WAYLAND=1 WAYLAND_DISPLAY="$WD" \
		firefox --kiosk --no-remote --profile "$T/profilo" "$URL" >"$T/firefox.log" 2>&1 &
	PID_FF=$!
	local pronta
	pronta=$(attendi_riga "$N" PRONTA 45)
	if [ -z "$pronta" ]; then
		ko "the page did not say PRONTA in 45 s."
		# ⛔ THE DENOMINATOR: did the browser at least ASK for the page?
		inf "requests that reached the collector: $(grep -c '^request: ' "$T/racc.log")"
		inf "Firefox log:"
		tail -6 "$T/firefox.log" | sed 's/^/        /'
		return 1
	fi
	local partenza schermo motore
	IFS=$'\t' read -r N GIRO _ _ partenza schermo motore <<< "$pronta"
	ok "page alive (round «$GIRO»).  engine: $motore"
	# ⛔ POSITIVE CONTROL 1 — does the document really scroll?
	if [ "$partenza" = 8000 ]; then
		ok "the document scrolls: the page placed itself $partenza px from the edge"
	else
		ko "the page placed itself at «$partenza» instead of 8000: the document does NOT scroll,"
		ko "   and every «it did not move» that follows would mean nothing"
		return 1
	fi
	# ⛔ POSITIVE CONTROL 2 — the screen the page sees is our monitor.
	if [ "$schermo" = "$TELA" ]; then
		ok "the page sees a $schermo screen, that is the virtual monitor asked for"
	else
		inf "⚠ the page sees a $schermo screen, asked for $TELA: the measurement of the sign"
		inf "  holds anyway, but the scene is different from the declared one"
	fi
	return 0
}

ferma_browser()
{
	[ -z "$PID_FF" ] && return 0
	kill "$PID_FF" 2>/dev/null
	wait "$PID_FF" 2>/dev/null
	PID_FF=
	sleep 2
}

# ---------------------------------------------------------------------------
ESITI=$T/esiti.tsv
: >"$ESITI"

giro() # $1 = label, $2... = command for the injector
{
	local etichetta=$1; shift
	local riga n delta scorrimento

	printf 'centro\n' >&9
	sleep 1
	printf '%s\n' "$*" >&9
	riga=$(attendi_riga "$N" SCATTO 15 "$GIRO")
	if [ -z "$riga" ]; then
		ko "$etichetta: the page recorded NOTHING"
		inf "the injector says:"
		tail -3 "$T/iniettore.log" | sed 's/^/        /'
		printf '%s\tNIENTE\tNIENTE\n' "$etichetta" >>"$ESITI"
		ESITO=1
		return 1
	fi
	IFS=$'\t' read -r n _ delta scorrimento _ _ _ <<< "$riga"
	N=$n
	printf '%s\t%s\t%s\n' "$etichetta" "$delta" "$scorrimento" >>"$ESITI"
	ok "$etichetta: deltaY=$delta  scorrimento=$scorrimento px"
	sleep 1
	return 0
}

# ⛔ THE DENOMINATOR, BEFORE EVERY SERIES: is the road from the injector to the
#    page open?  The pointer is moved to three points and one looks whether the
#    page sees it.  Without it, «it did not see the click» and «the input does not
#    arrive at all» look the same — and it is exactly the defect that ate three
#    runs of this bench.
#    ⚠ `org.gnome.Shell.Introspect.GetWindows` would be the short road to
#      know whether there is a window, but it answers «GetWindows is not allowed»
#      (`[M]` 10 Aug 2026): it is reserved to the Shell.
il_puntatore_arriva()
{
	local prima
	prima=$(wc -l < "$REGISTRO" 2>/dev/null || echo 0)
	printf 'muovi 400 300\n' >&9; sleep 1
	printf 'muovi 960 540\n' >&9; sleep 1
	printf 'muovi 500 700\n' >&9; sleep 1
	if leggi_riga "$prima" PUNTATORE "$GIRO" >/dev/null; then
		ok "the page SEES the pointer move: the road is open"
		return 0
	fi
	ko "the page does not even see the POINTER move: what follows would not"
	ko "   measure the sign of the wheel, it would measure that the input does not arrive"
	return 1
}

for STATO in false true; do
	log "4. The scene, with natural-scroll = $STATO"
	gsettings set org.gnome.desktop.peripherals.mouse natural-scroll "$STATO"
	gsettings set org.gnome.desktop.peripherals.touchpad natural-scroll "$STATO"
	inf "read back: mouse=$(gsettings get org.gnome.desktop.peripherals.mouse natural-scroll) touchpad=$(gsettings get org.gnome.desktop.peripherals.touchpad natural-scroll)"
	sleep 1
	# ⛔ Order: FIRST the injector, THEN the browser.  And the scene is redone whole
	#    at every state, so the device too is born with the gsetting already
	#    changed — a compositor that reads the preferences at the birth of the
	#    device would make blind a check done with the device alive.
	printf '\n--- injector, natural-scroll=%s ---\n' "$STATO" >>"$T/iniettore.log"
	if ! avvia_iniettore; then
		ko "the injector did not get a device:"
		sed 's/^/        /' "$T/iniettore.log"
		exit 6
	fi
	sed -n '/^--- injector, natural-scroll='"$STATO"'/,$p' "$T/iniettore.log" | sed 's/^/        /'
	if ! avvia_browser; then
		ferma_iniettore
		exit 5
	fi
	if ! il_puntatore_arriva; then
		ESITO=1
	fi
	giro "scatto+120/$STATO" "scatto 0 120"
	giro "scatto-120/$STATO" "scatto 0 -120"
	if [ "$STATO" = false ]; then
		# On top: smooth scrolling.  The product uses the clicks, but if
		# `ei_device_scroll_delta` had the opposite sign, the day
		# someone used it the defect would be born mute.
		giro "liscio+120/$STATO" "liscio 0 120"
	fi
	# ---------------------------------------------------------------------
	log "4-bis. The silence check (natural-scroll = $STATO)"
	inf "ten seconds without injecting anything: the page must NOT record clicks"
	PRIMA_SILENZIO=$N
	sleep 10
	if leggi_riga "$PRIMA_SILENZIO" SCATTO "$GIRO" >/dev/null; then
		ko "the page recorded a click that NOBODY sent:"
		ko "   then «the page saw a click» does not prove that we sent it"
		leggi_riga "$PRIMA_SILENZIO" SCATTO "$GIRO" | sed 's/^/        /'
		ESITO=1
	else
		ok "silence: the recorded clicks are the injected ones"
	fi
	ferma_browser
	ferma_iniettore
done

# ---------------------------------------------------------------------------
log "5. The verdict — the bench computes it, not whoever reads (B0.4)"
python3 - "$ESITI" <<'PY'
import sys

esiti = {}
for riga in open(sys.argv[1], encoding="utf-8"):
    parti = riga.rstrip("\n").split("\t")
    if len(parti) == 3:
        esiti[parti[0]] = parti[1:]

def segno(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return 0 if v == 0 else (1 if v > 0 else -1)

for nome in ("scatto+120/false", "scatto-120/false", "liscio+120/false",
             "scatto+120/true", "scatto-120/true"):
    d, s = esiti.get(nome, ("NIENTE", "NIENTE"))
    print(f"     {nome:20s} deltaY={d:>10}  scorrimento={s:>8}")

guasti = 0

def controlla(condizione, testo_ok, testo_no):
    global guasti
    if condizione:
        print("    \033[1;32mOK\033[0m ", testo_ok)
    else:
        print("    \033[1;31mNO\033[0m ", testo_no)
        guasti += 1

def d(nome):  return segno(esiti.get(nome, [None, None])[0])
def s(nome):  return segno(esiti.get(nome, [None, None])[1])

piu_f, meno_f = d("scatto+120/false"), d("scatto-120/false")
piu_t, meno_t = d("scatto+120/true"),  d("scatto-120/true")

print()
controlla(piu_f is not None and meno_f is not None and piu_f != 0 and piu_f == -meno_f,
          "+120 and -120 send the page in OPPOSITE directions: the sign is being measured",
          "+120 and -120 give the same direction (or zero): the sign is NOT being measured, "
          "and the number below must not be written anywhere")

controlla(s("scatto+120/false") is not None and s("scatto+120/false") == piu_f
          and s("scatto-120/false") == meno_f,
          "the `wheel` event and the real movement of the page say the same thing",
          "the `wheel` event and the real movement do NOT agree: one of the two instruments "
          "is looking at something else")

controlla(piu_f is not None and piu_t is not None and piu_f == piu_t and meno_f == meno_t,
          "the sign does NOT change with `natural-scroll`: it is a property of the path, "
          "not of the test desktop",
          "⛔ THE SIGN CHANGES WITH `natural-scroll`: the number would be the sign of a "
          "gsetting, and the symptom for the user «the wheel goes backwards» on half "
          "of the installations — form E11")

controlla(d("liscio+120/false") is None or d("liscio+120/false") == piu_f,
          "`scroll_delta` and `scroll_discrete` agree on the direction",
          "⚠ `ei_device_scroll_delta` has the OPPOSITE direction to `ei_device_scroll_discrete`: "
          "the product uses the second, but whoever used the first would be born with the wrong "
          "sign and without a symptom")

print()
if piu_f == -1:
    print("    READING: ei_device_scroll_discrete(0, +120) gives NEGATIVE deltaY, that is it sends")
    print("             the content towards the START of the document: +120 of libei == wheel")
    print("             turned UP, the same convention as the client's `+120` (RCP §7.3).")
    print("    ⇒ the RCP server injects the client's value AS IT IS.")
elif piu_f == +1:
    print("    READING: ei_device_scroll_discrete(0, +120) gives POSITIVE deltaY, that is it sends")
    print("             the content towards the END of the document: +120 of libei == wheel")
    print("             turned DOWN, the opposite of the client's `+120` (RCP §7.3).")
    print("    ⇒ the RCP server must INVERT the sign of the vertical axis.")
else:
    print("    READING: none, and it is not a number to write anywhere.")

sys.exit(1 if guasti else 0)
PY
[ $? -ne 0 ] && ESITO=1

log "Outcome"
if [ "$ESITO" -eq 0 ]; then
	ok "S7 measured, with the checks"
else
	ko "S7: at least one check failed — see above.  ⛔ The number is NOT written"
	ko "   in RCP.md §7.3 until the checks are green"
fi
inf "the line-by-line detail is in $REGISTRO"
exit "$ESITO"
