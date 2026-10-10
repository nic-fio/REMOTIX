#!/bin/bash
#
# 01-b11-lancia.sh — ⚠ runs ON THE MACHINE OF WHOEVER IS WATCHING: the browsers are here.
#
#   bash banchi/01-b11-lancia.sh            control + the two engines
#   bash banchi/01-b11-lancia.sh firefox    control + one engine only
#
# ---------------------------------------------------------------------------
# ⛔ B11 — THE VIOLATION TESTS TOWARDS THE PAGE (finding R4.1)
#
# The first draft of the phase 1 bench had **twelve violations towards the
# server and none towards the client**.  But `RCP.md` §3 is written about
# "an RCP implementation", and §9 has an **explicit MUST of the client**.
#
# ⭐ In a project that lost `mstsc` and that writes `RCP.md` precisely so as not to
#    trust two programs by the same hand, **a client never put to the
#    test is the hole in place of the referee**.
#
# ---------------------------------------------------------------------------
# ⛔ THE CHECK THAT SAYS NO, AND HERE IT IS PECULIAR
#
# First the page is run against the **HEALTHY** server.  ⚠ Without this round,
# "all green" would be compatible with a page that declares conforming
# anything — that is **a bench that approves itself**.
#
# ⛔ And it is not enough that the aggregate outcome says NON-CONFORME: we look CASE BY
#    CASE.  The cases that expect a `congedo:` are those that a healthy
#    server **cannot** provoke, and they must all fall; the cases that
#    expect "goes on" instead pass, because a healthy server does exactly
#    what they ask.  ⚠ The first draft said "none of the twelve cases
#    can pass", and it was false (finding R5.3).
#
# Then the **FAULTY** server is turned on, and then they must all pass.
#
# ---------------------------------------------------------------------------
# ⛔ AND THE SECOND WITNESS
#
# Three lines of the B11 table are **negative** properties of the page, and
# a negative property cannot be observed from inside whoever must respect it:
#
#   after `RESPINTO` it does not retry  → the SERVER LOG sees it
#   `desktop` changes nothing           → two rounds, and the bytes out compared
#   no application heartbeat            → stay quiet eight seconds and count
#
# The last two are carried by the page; the first is confirmed by the log, which is
# downloaded at the end and read here.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
SSH="python3 $RADICE/fondamenta/strumenti/sshpw.py"
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
log "1. The collector, on 127.0.0.1:$PORTA_PAGINA"
python3 "$QUI/01-b2-raccogli.py" "$PORTA_PAGINA" > "$TEMP/racc.log" 2>&1 &
PID_RACC=$!
sleep 1
if [ ! -d "/proc/$PID_RACC" ]; then
	ko "the collector did not start:"
	sed 's/^/        /' "$TEMP/racc.log"
	rm -rf "$TEMP"
	exit 5
fi
ok "collector listening, PID $PID_RACC"

# ⛔ The throwaway profile is THROWN AWAY, and the faulty server is put back HEALTHY: they are
#    the two things that on 10 Aug 2026 left leftovers behind (740 MB in
#    /tmp, and a server that lies).
#
# ⛔⭐ AND THE CLEANUP THAT FAILS MUST GO INTO THE EXIT CODE.
#
#    `01-b11-guasto.sh spegni` has a real failure outcome — it exits
#    5 with "N lines of B11 REMAIN" — and here it went through a `2>&1 | sed` without
#    anyone testing it.  It was enough for a `REMOTIX B11 GUASTO` line to remain
#    in the source (known defect no. 1 of the mandate: a `--togli` that does not
#    remove) for the bench to print "⭐ B11: the page applies §3 …",
#    exit **0**, and leave the report of the failed cleanup under
#    the green line, entrusted to the eye of whoever reads — that is exactly what
#    rule B0.4 forbids: *the bench compares against the expected, not the reader*
#    (finding R5.2).
#
# ⭐ And it is called BEFORE the verdict, not only from the `trap`: a cleanup that
#    fails after the green line is a wrong green line.  The `trap` stays
#    for early exits, and does not repeat it.
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
		ko "⛔ the HEALTHY server could not be turned off (exit $st):"
		tail -5 "$TEMP/rip-sano.log" | sed 's/^/        /'
		esito=1
	fi
	$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh spegni" \
		> "$TEMP/rip-guasto.log" 2>&1
	st=$?
	sed 's/^/        /' "$TEMP/rip-guasto.log"
	if [ "$st" -ne 0 ]; then
		ko "⛔ THE FAULTY SERVER WAS NOT PUT BACK HEALTHY (exit $st)."
		ko "   A switch that makes the server lie must not survive"
		ko "   the phase: relaunch «01-b11-guasto.sh spegni» on the server."
		esito=1
	fi
	rm -rf "$TEMP"
	return "$esito"
}
uscendo()
{
	local u=$?
	# ⚠ The cleanup can only worsen an outcome, never improve it.
	ripulisci || { [ "$u" -eq 0 ] && u=7; }
	exit "$u"
}
trap uscendo EXIT

# ---------------------------------------------------------------------------
# ⛔ THE RECORD THAT IS READ MUST BE OF THIS ROUND AND OF THIS ENGINE.
#
#    The wait was on a COUNT of lines of `b2-esiti.jsonl` and the verdict was
#    read from the last line of the same file: nothing tied the two things to the
#    same record, and the record carries the `motore` field that nobody looked at.
#    ⚠ `b2-esiti.jsonl` is the SHARED log of all of B2 — any probe
#      writing there during the round makes the wait exit on someone else's
#      line — and `kill "$p"` kills `xvfb-run`, not the browser that `xvfb-run`
#      started: a browser surviving from the previous round can deposit
#      its POST afterwards.  In both cases the bench printed "chrome:
#      CONFORME, as expected (after 0 seconds)" reading the outcome **of another
#      round** (finding R5.6).
#
# ⭐ The two fields that tie it are already there: `motore` (the browser string) and
#    `ora` (put by the collector, which runs on this same machine).  We
#    look for the most recent record that is of the same engine and not older
#    than the instant this round started.
cerca_esito() # $1 = engine mark, $2 = start instant
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
        break                      # from here down they are earlier rounds
    open(dove, "w", encoding="utf-8").write(r + "\n")
    sys.exit(0)
sys.exit(1)
FINE
}

# prova_motore <name> <binary> <command...>   — ATTESO in the environment
PROVATI=0
SALTATI=0
# ⛔ ESEGUITO says whether the last call RAN or was SKIPPED.  The skip
#    returned 0 and left no trace: neither `ESITO` nor any
#    count took note of it, and the missing engines ended up in the
#    denominator all the same (finding R5.16).
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
		ko "⛔ «$binario» cannot be recognised inside the «motore» field of the"
		ko "   record: without it, the outcome read would not be tied to this engine"
		return 1
	fi
	if ! command -v "$binario" >/dev/null; then
		inf "⚠ $binario is not on this machine: skipped, AND SAID SO"
		SALTATI=$((SALTATI + 1))
		return 0
	fi
	if ! command -v "$1" >/dev/null; then
		inf "⚠ $1 is not on this machine: skipped, AND SAID SO"
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
	# ⚠ The cap is generous on purpose: the cases have eight seconds of
	#   silence inside (§2.2) and some farewell waits.  ⚠ That it is generous
	#   ENOUGH is a hypothesis and not a calculation: the page's worst cap
	#   is computed from its timings, and that has never been done (finding R5.20,
	#   `[?]`, to be measured before touching this number).
	local i=0 trovato=0
	while [ "$i" -lt 240 ]; do
		if cerca_esito "$marca" "$inizio"; then trovato=1; break; fi
		sleep 1
		i=$((i + 1))
	done
	kill "$p" 2>/dev/null
	wait "$p" 2>/dev/null
	if [ "$trovato" -ne 1 ]; then
		ko "$nome recorded nothing in $i seconds"
		# ⛔ THE DENOMINATOR: did the browser at least REQUEST the page?  "it did not
		#    record" has two opposite causes, and only the collector's
		#    log tells them apart.
		printf '        requests received: %s\n' "$(grep -c '^request: ' "$TEMP/racc.log")"
		tail -6 "$TEMP/racc.log" | sed 's/^/        /'
		tail -5 "$TEMP/$nome.log" | sed 's/^/        /'
		return 1
	fi
	python3 -c '
import json,sys
d=json.loads(open(sys.argv[1]).read())
print("        outcome:", d.get("esito"), " points not passing:", d.get("guasti"))
print("        engine :", d.get("motore","")[:90])
for r in (d.get("dettaglio") or "").splitlines():
    print("        ", r)
' "$TEMP/ultimo.json"
	local visto
	visto=$(python3 -c '
import json,sys
print(json.loads(open(sys.argv[1]).read()).get("esito"))
' "$TEMP/ultimo.json")
	if [ "$visto" != "${ATTESO:-CONFORME}" ]; then
		ko "$nome: outcome $visto, expected ${ATTESO:-CONFORME}"
		return 1
	fi
	ok "$nome: $visto, as expected (after $i seconds)"
	return 0
}

# ═══════════════════════════════════════════════════════════════════════════
log "2. ⛔ THE CHECK THAT SAYS NO — the page against the HEALTHY server"
inf "expected: NON-CONFORME, and the label is not enough: the cases that expect a"
inf "          «congedo:» must have ALL fallen, and no case must have"
inf "          ended in «errore:», which would mean the page did not speak"
inf "⚠ runs with ONE engine only, and says so: what it proves is that the page"
inf "  can say NO, and for that one engine is enough."
# ⛔ AND FIRST THE HEALTHY BINARY IS PUT BACK, always.
#
#    `01-b2-lancia-wt.sh accendi` turns on **the binary that is on disk**, and
#    that may be the faulty one of a previous round.  ⚠ The control would
#    say CONFORME, the bench would give red, and the red would be on the
#    control instead of on the server: the same form as the defect found today
#    with `test -x`.
# ⛔ AND HERE THE STATUS IS TESTED, because it is the point where the red would land
#    on the wrong suspect: it was in a pipeline (`| tail -3 | sed`) and nobody
#    looked at it (finding R5.2).
inf "the healthy binary is put back before the control (it may take a minute)"
$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh spegni" > "$TEMP/sano-prima.log" 2>&1
ST=$?
tail -3 "$TEMP/sano-prima.log" | sed 's/^/        /'
if [ "$ST" -ne 0 ]; then
	ko "⛔ the healthy binary could not be put back (exit $ST): the control"
	ko "   would run against a binary nobody knows"
	exit 3
fi
if ! $SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh accendi $IND $PORTA" \
	> "$TEMP/sano.log" 2>&1; then
	ko "the healthy server did not turn on: the control does not start"
	sed 's/^/        /' "$TEMP/sano.log"
	exit 3
fi
IMPRONTA=$(grep -oE '[A-Za-z0-9+/]{43}=' "$TEMP/sano.log" | tail -1)
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "the fingerprint has ${#IMPRONTA} characters instead of 44: it is truncated"
	exit 4
fi
ok "HEALTHY server on, fingerprint $IMPRONTA"

ATTESO=NON-CONFORME prova_motore controllo firefox xvfb-run -a firefox \
	--no-remote --profile "$TEMP/controllo" || ESITO=1
CONTROLLO=$ESEGUITO
# ⛔ "NON-CONFORME" ALONE PROVES NOTHING, and it is the biggest hole of
#    this bench.
#
#    The page writes NON-CONFORME as soon as any point does not pass, and
#    with a stale fingerprint in `?impronta=` — it is enough that `01-b2-certificati.sh`
#    rotated the key in the meantime — no WebTransport session
#    opens, the page reads not one byte of RCP, all the cases end in
#    `errore:WebTransportError` and the bench printed "OK controllo:
#    NON-CONFORME, as expected".  ⛔ That is: the check that must prove "the
#    page can say NO" was satisfied by a page that said
#    nothing (finding R5.3, form E8).
#
# ⭐ The datum that tells the two cases apart was already there and nobody looked at it: the
#    page sends `casi: [{nome, atteso, fatto, ok}, …]`, and the bench read
#    only `.esito`.
if [ "$CONTROLLO" -eq 1 ] && [ -f "$TEMP/ultimo.json" ]; then
	python3 - "$TEMP/ultimo.json" <<'FINE'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read())
casi = d.get("casi") or []
if not casi:
    print("        ⛔ the record does not carry the list of cases: without it, «NON-CONFORME»")
    print("           is compatible with a page that did not speak with the server")
    sys.exit(1)
# ⭐ The two counts are COMPUTED from the record, not written by hand: adding a
#    case to the page must not leave an old number here.
errori = [c["nome"] for c in casi if str(c.get("fatto", "")).startswith("errore:")]
# The page sends a `congedo:` only when the server has violated §3: a
# HEALTHY server cannot provoke it, so these cases must all fall.
devono = [c for c in casi if str(c.get("atteso", "")).startswith("congedo:")]
caduti = [c for c in devono if not c.get("ok")]
print(f"        cases in the record: {len(casi)}")
print(f"        cases a HEALTHY server cannot satisfy: {len(devono)}"
      f" — fallen: {len(caduti)}")
print(f"        cases ended in «errore:…»: {len(errori)}  (expected 0)")
male = 0
if errori:
    print("        ⛔ the page did not speak RCP in", len(errori), "cases:",
          ", ".join(errori[:5]))
    print("           a control satisfied by a session that does not open")
    print("           does not prove that the page can say no")
    male = 1
if len(caduti) != len(devono):
    passati = [c["nome"] for c in devono if c.get("ok")]
    print("        ⛔ against a HEALTHY server cases PASSED that demand a")
    print("           violation by the server:", ", ".join(passati))
    male = 1
sys.exit(male)
FINE
	if [ $? -ne 0 ]; then
		ko "⛔ the check that says NO did not say NO for the right reason"
		ESITO=1
	else
		ok "⭐ the control says NO case by case, and the page spoke RCP"
	fi
elif [ "$CONTROLLO" -eq 1 ]; then
	ko "⛔ the control left no record to look at"
	ESITO=1
fi
$SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" > "$TEMP/sano-dopo.log" 2>&1
ST=$?
if [ "$ST" -ne 0 ]; then
	ko "⛔ the HEALTHY server did not turn off (exit $ST): the faulty server would not"
	ko "   find the port free, and the red would land on it"
	tail -5 "$TEMP/sano-dopo.log" | sed 's/^/        /'
	exit 3
fi

# ═══════════════════════════════════════════════════════════════════════════
log "3. The FAULTY server, on the other machine"
inf "⛔ it is a server that lies on purpose: it is turned off at the end, and with it"
inf "   the healthy source is put back"
if ! $SSH "bash /media/REMOTIX/src/01-b11-guasto.sh accendi" \
	> "$TEMP/acceso.log" 2>&1; then
	sed 's/^/        /' "$TEMP/acceso.log"
	ko "the faulty server did not turn on"
	exit 3
fi
sed 's/^/        /' "$TEMP/acceso.log" | tail -12
IMPRONTA=$(grep -oE '[A-Za-z0-9+/]{43}=' "$TEMP/acceso.log" | tail -1)
if [ ${#IMPRONTA} -ne 44 ]; then
	ko "the fingerprint has ${#IMPRONTA} characters instead of 44"
	exit 4
fi
ok "session fingerprint: $IMPRONTA"

# ⭐ How many cases the page declares it ran, engine by engine: it is the
#    denominator of the "faults served" further on, and THE PAGE declares it —
#    here we do not write "thirteen", which would age at the first case added.
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

log "4. The page's cases, with the real browsers"
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
log "5. ⛔ The SECOND WITNESS: the server log"
inf "«after RESPINTO the page does not retry» cannot be seen from inside the page:"
inf "it is seen from here, and the server writes every byte arrived after the end"
# ⛔ AND THE STATUS OF THIS READ IS TESTED.
#
#    `> "$TEMP/registro.txt"` captured the output and threw away the status: a
#    missing log, a server never started, a container not answering
#    all arrived as "zero lines" — which has the same face as "no
#    violation".  ⭐ `registro` now exits non-zero when it could not
#    read, and declares how many lines it filtered: the two things together
#    tell zero from failure (finding R5.15, form E8).
$SSH "bash /media/REMOTIX/src/01-b11-guasto.sh registro" > "$TEMP/registro.txt" 2>&1
ST=$?
if [ "$ST" -ne 0 ]; then
	ko "⛔ the server log could not be read (exit $ST):"
	tail -5 "$TEMP/registro.txt" | sed 's/^/        /'
	ko "   without the second witness the NEGATIVE properties of the page"
	ko "   are observed by nobody, and this is not a green"
	ESITO=1
fi
# ⭐ AND THE DENOMINATOR OF THE TRANSPORT: how many lines the server filtered, and
#    how many arrived here.  A truncation — of the window, of SSH,
#    of anyone — can be seen, instead of looking like a silence.  ⚠ The `tail
#    -600` that was over there discarded the OLDEST lines, that is those of the
#    first engine: a "bytes arrived AFTER the end" of the first engine left
#    the window long before the count of the cases noticed
#    (finding R5.9).
DICHIARATE=$(sed -n 's/^== RIGHE-DEL-REGISTRO-FILTRATE: \([0-9][0-9]*\)$/\1/p' \
	"$TEMP/registro.txt" | tail -1)
RICEVUTE=$(grep -Ec "B11|AFTER the end|parting CONGEDO|congedo motivo|control channel opened" \
	"$TEMP/registro.txt")
if [ -z "$DICHIARATE" ]; then
	ko "⛔ the server did not declare how many lines it filtered: what"
	ko "   arrived here has no denominator"
	ESITO=1
elif [ "$DICHIARATE" -ne "$RICEVUTE" ]; then
	ko "⛔ the server filtered $DICHIARATE of them and $RICEVUTE arrived here:"
	ko "   something cut the log along the way"
	ESITO=1
else
	inf "log lines: $RICEVUTE, all those the server filtered"
fi
DOPO=$(grep -c "AFTER the end" "$TEMP/registro.txt" || true)
SERVITI=$(grep -c "B11 GUASTO: fault requested" "$TEMP/registro.txt" || true)
# ⛔ THE DENOMINATOR OF THE FAULTS SERVED, AND IT IS NOT ZERO.
#
#    The bench knows the exact number it must find — the page's cases
#    for the engines run against the faulty server — and compared it **only with zero**:
#    a round in which the page gave up after the first case gave SERVITI=1,
#    "ok faults served: 1", and off towards green.  ⚠ It is the same counter
#    that on 10 Aug 2026 was caught lying (26 instead of 21) without
#    anyone noticing: the lie passed because that number was not
#    compared with anything (finding R5.4, `LEZIONI.md` §1.9 fourth rule).
if [ "$MOTORI_GUASTO" -eq 0 ] || [ "$CASI_ATTESI" -eq 0 ]; then
	ko "⛔ no case was requested by any engine: there is nothing to"
	ko "   divide, and this is not an outcome"
	ESITO=1
elif [ "$SERVITI" -ne "$CASI_ATTESI" ]; then
	ko "⛔ the server served $SERVITI faults, and the $MOTORI_GUASTO engines"
	ko "   declared $CASI_ATTESI: the missing cases never reached the"
	ko "   server, and their outcome is not a judgement on the page"
	ESITO=1
else
	ok "faults served by the server: $SERVITI of $CASI_ATTESI expected, from $MOTORI_GUASTO engines"
fi
if [ "${DOPO:-0}" -eq 0 ]; then
	ok "⭐ no byte arrived after the end of the session (§4.2, §4.4)"
else
	ko "⛔ $DOPO times the page sent AFTER the end of the session:"
	grep "AFTER the end" "$TEMP/registro.txt" | head -5 | sed 's/^/        /'
	ESITO=1
fi

# ⛔⭐ AND THE POSITIVE WITNESS, which on 10 Aug 2026 was missing.
#
#    "zero bytes after the end" is true even for a page that, in front of a
#    server that gets it wrong after `RESPINTO`, leaves silently — that is, that violates
#    §8.1 instead of §4.4.  ⚠ It is the emptiest form of green there is: the one
#    that does not need anything to go right.
#
# ⭐ The `respinto-poi-congedo` case obliges the page to a `CONGEDO` when for
#    the server the session is already over, and the server writes it naming it.
#    ONE is expected for every engine tested against the FAULTY server — that is all
#    except the control, which runs against the healthy server and there that message
#    does not arrive.
#
# ⛔ AND THE TWO ROADS OF §3.1 ARE COUNTED, not one: the farewell can arrive as
#    bytes on the control channel **or** inside the close code of the
#    session — and on 10 Aug 2026 the two engines used one each.
#    ⚠ Demanding the first only would have written "Firefox does not say farewell", which
#    is false: Firefox resets the channel and puts the reason in the capsule.
#
# ⛔ AND BOTH ROADS ARE COUNTED, even when they arrive together.
#    The `awk` looked **only at the first** "parting CONGEDO" line of the case
#    (`&& !visto`) and classified it by whoever arrived first: an engine that uses
#    both roads produces two distinct lines — that of `rcp.c` (the
#    CONGEDO on the channel) and that of `01-b3-rcp-innesta.py` (the close
#    code) — and the second was discarded.  ⚠ With that structure the bench
#    could not, in principle, observe "two roads for the same
#    engine" (finding R5.7).
#
# ⛔ AND IT IS COUNTED INSIDE THE CASE, not over the whole log.  A farewell at the end
#    of the round says nothing about THAT case: the log is in order, and every
#    "fault requested" opens the block of its own.  ⚠ Counting them all together gave 15
#    with 2 expected, and it was a number without meaning.
#
# ⛔ AND THE DENOMINATOR IS THE ENGINES THAT RAN, counted one by one.
#    It was `PROVATI - 1`, that is "the calls to prova_motore minus the control" —
#    but the control can be SKIPPED (it calls `firefox` regardless of
#    `$MOTORI`), and on a machine with Chrome and without Firefox `ATTESI`
#    became 0: the bench printed "the case was served 1 times, and the
#    engines against the faulty server are 0" pinning its own
#    arithmetic on the page, and in the green branch "the farewell arrives every time: 0 of 0"
#    (findings R5.16 and R5.5).
ATTESI=$MOTORI_GUASTO
eval "$(awk '
  function chiudi_caso() { if (aperto && (canale_visto || chiusura_vista)) con++ }
  /fault requested by the client:/ {
    chiudi_caso()
    caso = $NF
    aperto = (caso == "respinto-poi-congedo")
    canale_visto = 0; chiusura_vista = 0
    if (aperto) casi++
  }
  /parting CONGEDO/ {
    if (aperto) {
      if (index($0, "second road")) {
        if (!chiusura_vista) { chiusura_vista = 1; chiusura++ }
      } else {
        if (!canale_visto) { canale_visto = 1; canale++ }
      }
    }
  }
  END { chiudi_caso(); printf "CASI=%d CON=%d CANALE=%d CHIUSURA=%d\n", casi, con, canale, chiusura }
' "$TEMP/registro.txt")"
inf "the «respinto-poi-congedo» case was served $CASI times"
inf "farewell via the control channel: $CANALE — via the close code: $CHIUSURA"
if [ "$CONTROLLO" -ne 1 ]; then
	# ⛔ The check that says NO is not an accessory: without it, the round reaches
	#    a verdict without anyone having proved that the page can say
	#    no (`REVIEWER.md` §1 question 2).
	ko "⛔ THE CHECK THAT SAYS NO WAS NOT EXECUTED: the browser that runs it"
	ko "   is missing.  This round is not a verdict on B11."
	ESITO=1
fi
if [ "$ATTESI" -eq 0 ]; then
	ko "⛔ no engine ran against the faulty server: «$CON of $ATTESI»"
	ko "   would be a positive control passed with zero observations"
	ESITO=1
elif [ "$CASI" -ne "$ATTESI" ]; then
	ko "⛔ the case was served $CASI times, and the engines against the faulty server are"
	ko "   $ATTESI: the count below would have no denominator"
	ESITO=1
elif [ "$CON" -ne "$ATTESI" ]; then
	ko "⛔ only $CON farewells of $ATTESI: there is an engine that closes and does NOT say"
	ko "   why, neither on the channel nor in the close code (§8.1)"
	ESITO=1
else
	ok "⭐ the farewell of §8.1 arrives every time: $CON of $ATTESI"
	# ⛔ And the two roads are DECLARED counted, not declared seen.  The
	#    green branch asserted "and ⛔ by TWO different roads" on the sole
	#    condition `CON -eq ATTESI`, with `CANALE` and `CHIUSURA` computed and never
	#    tested: two engines that both said farewell on the channel gave
	#    CANALE=2, CHIUSURA=0, and the bench asserted in green something its
	#    own numbers contradicted in the line above (finding R5.5).
	if [ "$CANALE" -ge 1 ] && [ "$CHIUSURA" -ge 1 ]; then
		ok "⭐ and by TWO different roads ($CANALE on the channel, $CHIUSURA in the close"
		ok "   code): §3.1 point 3 is not redundancy, it is the other road"
	else
		inf "⚠ all by the same road ($CANALE on the channel, $CHIUSURA in the"
		inf "  close code): §3.1 is respected, but this round did NOT"
		inf "  see the second road — and with one engine only it cannot see it"
	fi
fi

# ---------------------------------------------------------------------------
# ⭐ The cleanup BEFORE the verdict: if it fails, the verdict knows.
ripulisci || ESITO=1

log "Outcome"
inf "engines run: $PROVATI (control included) — skipped: $SALTATI"
inf "engines against the faulty server: $MOTORI_GUASTO — control executed: $CONTROLLO"
if [ "$PROVATI" -eq 0 ]; then
	ko "⛔ NO engine was tested: this is not an outcome"
	exit 6
fi
if [ "$ESITO" -eq 0 ]; then
	ok "⭐ B11: the page applies §3 even when it is the server that gets it wrong,"
	ok "   and against a healthy server it says no"
else
	ko "⛔ B11: something does not pass"
fi
exit "$ESITO"
