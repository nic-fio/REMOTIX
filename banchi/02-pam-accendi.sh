#!/bin/bash
#
# 02-pam-accendi.sh — ⛔ IT RUNS INSIDE THE CONTAINER.  It switches on THIS BENCH'S
# TARGET: a copy of the product on port 7531, with ban, socket,
# certificates, log and pid file all of its own.
#
#   bash /srv/src/02-pam-accendi.sh copia     remakes the copy and rebuilds it
#   bash /srv/src/02-pam-accendi.sh accendi
#   bash /srv/src/02-pam-accendi.sh spegni
#   bash /srv/src/02-pam-accendi.sh registro  prints the target's log
#
# ---------------------------------------------------------------------------
# ⛔ WHY A TARGET OF MY OWN AND NOT THE HOUSE ONE
#
# On NIC-OS, on 12 Aug 2026, already running are: **7448** (the house product),
# **7501** and **7522** (the targets of P5, from another round).  ⛔ They are
# on on purpose and are not touched.  ⚠ And the rule «a parallel bench has
# its OWN port, ban file and socket» is not zeal: the attempt count of
# §4.4-bis is **per address**, and all the benches of this machine start
# from the same address — whoever shares a ban file with another round locks
# that one out for twelve hours too.
#
# ⭐ The perimeter sits in ONE variable (`PREFISSO`), as in `01-p5-accendi.sh`:
#    so no piece of it can be forgotten.  It is the cure born on 12 Aug
#    2026 when ban, socket, log, certificate and **pid file** were
#    written out literally, and a second target would have deleted those of the
#    first — including the `.pid`, that is `spegni` would have killed the wrong
#    process.
#
# ---------------------------------------------------------------------------
# ⛔ THE FAULT IS INJECTED INTO THE COPY, NEVER INTO THE HOUSE PRODUCT
#
# The certification of this bench wants the round `sano -> guasto -> risanato`,
# and the fault is **the cure removed**: the asynchronous hook not connected, that is
# exactly the state of the server before 12 Aug 2026.  ⛔ Injecting it into the
# product of `/srv/src/remotix` would put it under the feet of anyone else
# who is using it.
#
# ⛔ B0.7: MARKERS, NOT `sleep`.  «The process is alive» and «the port answers»
#    are two different facts, and the measurement needs the second.
set -uo pipefail

SORG=${SORG:-/srv/src/02-pam-src}
D=${D:-/srv/src/02-pam-bersaglio}
GEMELLO=${GEMELLO:-/srv/src/rcp}
TMP=/srv/src/tmp
PORTA=${PORTA:-7531}
IND=${IND:-192.168.0.2}
PREFISSO=${PREFISSO:-pam2-7531}

CERT=$TMP/$PREFISSO-cert
BAN=$TMP/$PREFISSO-ban
SOCK=$TMP/$PREFISSO.sock
LOG=$TMP/$PREFISSO.log
PIDF=$TMP/$PREFISSO.pid

mkdir -p "$TMP"

case "${1:-accendi}" in
spegni)
	if [ -f "$PIDF" ]; then
		pid=$(cat "$PIDF")
		# ⛔ By PID and only its own: `pkill -f remotix` would take away
		#    7448, 7501 and 7522, which belong to others.
		kill "$pid" 2>/dev/null
		g=0
		while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
		[ -d "/proc/$pid" ] && printf 'NO  pid %s did not die\n' "$pid" \
		                    || printf 'OK  switched off (pid %s)\n' "$pid"
		rm -f "$PIDF"
	else
		printf -- '--  no %s: nothing of mine was on\n' "$PIDF"
	fi
	rm -f "$SOCK"
	exit 0 ;;
registro)
	[ -f "$LOG" ] || { echo "NO  ⛔ $LOG is not there"; exit 2; }
	cat "$LOG"
	exit 0 ;;
ammazza-aiutante)
	# ⛔⭐ IT SITS IN A FILE, AND NOT INSIDE THREE LEVELS OF QUOTES — 12 Aug
	#     2026, and the lesson was already written in `01-p5-accendi.sh`: «a file
	#     has no levels of quotes».  ⚠ Written inside `ssh → enter.sh →
	#     bash -c`, this piece died on a `$(...)`  — and the trouble was not
	#     the error: it was that the case «the helper is dead» ran
	#     anyway, on a LIVE helper, and gave a red to a healthy server.
	#
	# ⛔ And the pid is read from the log OF THIS target: a `pgrep` on
	#    «remotix» would also find 7448, 7501 and 7522, which belong to
	#    others.  ⚠ «I killed it» and «I killed one» are two different
	#    facts.
	[ -f "$LOG" ] || { echo "NO  ⛔ $LOG is not there: I killed nothing"; exit 2; }
	p=$(sed -n 's/.*PAM helper started: pid \([0-9]*\).*/\1/p' "$LOG" | tail -1)
	if [ -z "$p" ]; then
		echo "NO  ⛔ no helper pid in the log: it is not «it died»,"
		echo "    it is «it was never born», and they are two different things."
		exit 2
	fi
	# ⛔⭐ «ALIVE» AND «ZOMBIE» ARE NOT THE SAME THING, AND IN /proc THEY LOOK ALIKE
	#     — 12 Aug 2026, and this check has already given a wrong NO.
	#
	# `[ -d /proc/$p ]` answers «yes» also for a process already dead that its
	# parent has not reaped yet.  ⛔ The bench said «the helper is still
	# alive after SIGKILL» while it had been dead for a second, and the diagnosis pointed
	# at the product.  ⭐ The real state is in the third field of /proc/<pid>/stat:
	# `Z` is a zombie, that is dead.
	vivo() # $1 = pid.  0 = really alive, 1 = dead (absent or zombie)
	{
		[ -r "/proc/$1/stat" ] || return 1
		s=$(awk '{print $3}' "/proc/$1/stat" 2>/dev/null)
		[ "$s" = Z ] && return 1
		return 0
	}
	if ! vivo "$p"; then
		echo "NO  ⛔ pid $p is not alive ALREADY NOW: the case that follows"
		echo "    would measure a scene I did not prepare."
		exit 2
	fi
	kill -9 "$p"
	sleep 1
	if vivo "$p"; then
		echo "NO  ⛔ pid $p is still ALIVE after SIGKILL (state $(awk '{print $3}' "/proc/$p/stat"))"
		exit 3
	fi
	echo "OK  helper $p killed with SIGKILL: it could not write anything,"
	echo "    and no handler could answer in its place"
	exit 0 ;;
copia)
	[ -d "$SORG" ] || { echo "NO  ⛔ $SORG is not there"; exit 2; }
	# ⛔ The copy is remade from scratch: an old copy answers «I exist» just like
	#    a current one (LEZIONI.md §1.9 point 8).
	rm -rf "$D"
	mkdir -p "$(dirname "$D")"
	cp -a "$SORG" "$D"
	rm -f "$D"/*.o "$D/remotix"
	printf -- '--  copy: %s → %s\n' "$SORG" "$D"
	GEMELLO="$GEMELLO" bash "$D/costruisci.sh" || exit 3
	exit 0 ;;
guasto)
	# ⛔⭐ THE FAULT IS THE CURE REMOVED, AND NOT AN INVENTED DEFECT — 12 Aug
	#     2026.  It is the best form an injected fault can have: the
	#     state of the server BEFORE §1.10, that is a defect that really
	#     existed and that was really measured (`[M]` B8, 11 Aug:
	#     1.0-2.2 s per attempt).
	#
	# ⛔ What it proves: that `02-pam-fermo.py` **can see** the blocking.  A
	#    bench that stayed green with this fault inside would not prove that
	#    the cure works — it would prove that the ruler is blind, and every later
	#    green would be the worst of proofs (`CODER.md` §4.6).
	#
	# ⚠ It is injected into the COPY (`$D`), never into the product of `/srv/src/remotix`,
	#   which belongs to anyone else who is using it.
	[ -f "$D/webtransport.c" ] || { echo "NO  ⛔ $D/webtransport.c is not there"; exit 2; }
	python3 - "$D/webtransport.c" <<'FINE'
import sys
p = sys.argv[1]
t = open(p).read()
appiglio = "\tif (w->aiuto)\n\t\tg.chiedi_verifica = gancio_chiedi;\n"
if t.count(appiglio) != 1:
    print("NO  ⛔ the anchor is not unique (%d times): I inject nothing"
          % t.count(appiglio))
    sys.exit(2)
guasto = ("\t/* REMOTIX 02-PAM GUASTO — the asynchronous hook NOT connected,\n"
          "\t * that is the server as it was before DECISIONI.md §1.10.  rcp.c\n"
          "\t * will fall back on the SYNCHRONOUS check and the wire will stall.\n"
          "\t * If 02-pam-fermo.py stays green with this inside, it is blind. */\n")
open(p, "w").write(t.replace(appiglio, guasto, 1))
print("OK  fault injected: the asynchronous hook is no longer connected")
FINE
	[ $? -eq 0 ] || exit 3
	GEMELLO="$GEMELLO" bash "$D/costruisci.sh" >/dev/null 2>&1 \
		|| { echo "NO  ⛔ the rebuild with the fault failed"; exit 3; }
	# ⛔ And it is CHECKED that the fault is in the binary, not only in the source:
	#    «I wrote it» and «it is inside what runs» are two different facts, and
	#    it is the defect with which B11 switched on the healthy server believing it faulty.
	if grep -a -F -q "REMOTIX 02-PAM GUASTO" "$D/webtransport.c" \
	   && ! grep -a -F -q "g.chiedi_verifica = gancio_chiedi" "$D/webtransport.c"; then
		echo "OK  ⛔ rebuilt WITH the fault: $(sha256sum "$D/remotix" | cut -c1-16)…"
	else
		echo "NO  ⛔ the fault is not where it should be"
		exit 3
	fi
	exit 0 ;;
accendi) TIENI_BAN=0 ;;
riaccendi)
	# ⛔⭐ AND THIS STEP EXISTS BECAUSE OF A RED THE BENCH HAD GIVEN ITSELF
	#     — 12 Aug 2026, and the first suspect was the bench (`REVIEWER.md` §1).
	#
	# `accendi` deletes the ban file, and rightly so: a round must start from
	# a KNOWN state, and a ban inherited from the previous round would make it measure
	# `TROPPI_TENTATIVI` where PAM was meant to be measured.  ⛔ But the case
	# «the ban survives the restart» (invariant **I7**) is proved by SWITCHING OFF AND
	# ON AGAIN, and with that `rm` it always said no — **full red on a
	# product that does keep the ban**.
	#
	# ⚠ It is the form of `LEZIONI.md` §1.9: the bench was measuring its own leg and
	#   the diagnosis pointed at the server.  ⭐ Now the two steps are two, and the
	#   name says which state is being asked for.
	TIENI_BAN=1 ;;
*) echo "usage: $0 [copia|guasto|accendi|riaccendi|spegni|registro|ammazza-aiutante]"; exit 2 ;;
esac

command -v ss >/dev/null || { echo "NO  ⛔ «ss» is not there: I did not look at the port, and I do not call it free"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ port $PORTA is already taken ($n lines): it is not mine, I do not touch it"
	ss -tuln | grep ":$PORTA\b"
	exit 2
fi
echo "OK  port $PORTA free (ss looked and printed $n lines about it)"

[ -x "$D/remotix" ] || { echo "NO  ⛔ $D/remotix is not there or not executable — the «copia» step is missing"; exit 2; }
[ -f "$D/pagina.html" ] || { echo "NO  ⛔ $D/pagina.html is not there: the server would serve nothing"; exit 2; }
echo "--  binary   : $(sha256sum "$D/remotix" | cut -c1-16)…  $(stat -c '%y' "$D/remotix")"

# ⛔ AND BEFORE DELETING ANYTHING, IT CHECKS WHETHER IT BELONGS TO SOMEONE ELSE ALIVE.
if [ -f "$PIDF" ] && [ -d "/proc/$(cat "$PIDF" 2>/dev/null)" ]; then
	echo "NO  ⛔ «$PIDF» says pid $(cat "$PIDF"), and it is ALIVE: another target"
	echo "    with this same prefix («$PREFISSO») is already on."
	exit 2
fi
if [ "${TIENI_BAN:-0}" = 1 ]; then
	rm -f "$LOG" "$PIDF" "$SOCK"
	echo "--  ⚠ the ban file is NOT deleted: it is the «riaccendi» step, and"
	echo "    that file IS the thing to prove (I7, §4.4-bis)"
	[ -f "$BAN" ] && echo "--  bans before the restart: $(wc -l < "$BAN") lines in $BAN" \
	              || echo "--  ⛔ $BAN IS NOT THERE: it is not «zero bans», it is «there was nothing to keep»"
else
	rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.nuovo"
fi
mkdir -p "$CERT"
# ⭐ It is started FROM INSIDE its folder: the product looks for `pagina.html`
#    next to itself.
cd "$D" || exit 3
nohup ./remotix --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" \
      --ban-file "$BAN" --comando-socket "$SOCK" --parlantina \
      > "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ the server died at once.  The log says:"
	sed 's/^/        /' "$LOG"
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$righe" -lt 2 ]; then
	echo "NO  ⛔ process $pid is alive but on :$PORTA there are $righe listeners."
	echo "    §2.4 wants TWO — UDP for RCP, TCP for the page."
	sed 's/^/        /' "$LOG"
	exit 3
fi
# ⛔ And the PAM service is checked in the server's LOG, not from memory: without
#    /etc/pam.d/remotix every right password is refused, and this bench
#    would measure a scene in which NOBODY gets in — that is a green number because
#    there was nothing to block.
if grep -q "DOES NOT EXIST" "$LOG"; then
	echo "NO  ⛔ the server says /etc/pam.d/remotix is not there: every right"
	echo "    password would be refused, and this bench's scene does not exist."
	exit 3
fi
echo "OK  on, pid $pid, $righe listeners on :$PORTA after $((g/2)) s of waiting"
echo "--  log: $LOG · ban: $BAN · socket: $SOCK"
