#!/bin/bash
#
# 01-b8-launch.sh — runs ON THE SERVER.  B8: the fixed second, and THE BAN of the address.
#
#   TARGET=graft  bash .../01-b8-launch.sh             10 blocks
#   TARGET=product bash .../01-b8-launch.sh 3           a short run
#   TARGET=product bash .../01-b8-launch.sh prediction  without measuring
#   TARGET=graft  bash .../01-b8-launch.sh build  puts the grafts back
#
# ⛔ `TARGET` IS MANDATORY — see `01-b0-target.sh`.
#
# ---------------------------------------------------------------------------
# ⛔⭐ WHAT CHANGES WHEN B8 IS POINTED AT THE PRODUCT — the prediction, written BEFORE
#
# | what | graft | product | why |
# |---|---|---|---|
# | the fixed second and the three medians | same | same | they are governed by `rcp.c` + `authentication.c` + PAM.  ⚠ `rcp.c` is identical byte for byte; `authentication.c` is **not**, and it is the only point where a difference would be REAL and not of measurement |
# | ⚠ the PAM `[?]` (median 2636 ms on the refused) | open | ⛔ **expected the same**, and the run against the product does NOT close it | it is PAM that governs the times, not us: changing server does not change the PAM stack |
# | the ban: threshold 3, window 5 min, 12 hours | same | same | `rcp.c`, identical |
# | ⛔ **the start-up line about the ban** | `REMOTIX B3: ban caricati: N` | `HH:MM:SS.mmm startup  ban: <file>, N addresses caricati` | ⛔ two different strings.  Looking for the first against the product would have given «the server said NOTHING about the ban at start-up» — full red on a server that does say it |
# | ⛔ **unreadable ban file** | the server starts and writes it | ⛔ the server **DOES NOT START** | `src/main.c`: *«it is not "zero bans", it is the protection of §4.4-bis switched off.  One does not start.»*  ⚠ On this target that case is not observed as a line: it is observed as «the server did not start», and the bench declares it |
# | the ban page | `page TCP a …` | `GET / da … (address BANNED)` | ⭐ and the four anchors B8 reads — `data-banned`, `data-remaining-ms`, «attempts esauriti», `id="hours"`/`id="minutes"` — ARE THERE in the product: finding R12.2 put them there on purpose, after realising that without them the bench would have given three reds on a server that does ban |
# | the unblock command | `UNBLOCK` / `PING`, same protocol | ⭐ identical, `src/command.c` | ⛔ **and it is the half nobody ever did**: `01-b8-unblock.py` has never been pointed at the product |
# | the two addresses (127.0.0.1 and 192.168.0.2) | ok on 0.0.0.0 | ok on 0.0.0.0 | ⚠ the product's certificate carries the SAN `192.168.0.2`, but the test client does not verify (`ssl.CERT_NONE`): the SAN does not bite here |
# | the inactivity cap | 120 s | 30 s | ⚠ B8 never keeps quiet for more than a few seconds: it does not touch it |
#
# ---------------------------------------------------------------------------
# ⛔ WHAT IT MEASURES — and the long explanation is in `01-b8-stopwatch.py`
#
# `RCP.md` §4.4 forbids distinguishing in the REASON between «user does not exist»
# and «wrong password».  §4.4-bis imposes the **fixed delay of one second** so that
# that distinction cannot be read with the **stopwatch**, and — since 10 Aug 2026,
# by the user's decision — **the ban of the address**: three failed
# authentications from the same address within five minutes, and that address is
# out for twelve hours.
#
# ---------------------------------------------------------------------------
# ⛔ TWO LIVES OF THE SERVER, NOT TWELVE — and this is the biggest difference
#
# The previous form of this bench turned the process off and on again **at
# every block**, and wrote it at the top of the file: *«the only way to start
# again from reset counters is a new process — `rcp_reset_session_log()`
# exists but nobody calls it»*.  ⭐ Now someone calls it: §4.4-bis wants an
# **unblock command**, on 11 Aug 2026 it was born on the host side, and
# `01-b8-unblock.py` is the side of whoever commands.
#
# The two lives that remain each have a reason:
#
#   the first    the samples of the fixed second, and the whole ban run;
#   the second   ⛔ **only** to prove that the ban SURVIVES the restart —
#                invariant I7, and without that line the ban lives in memory and
#                a package update gives three attempts to anyone.
#
# ⛔ AND THE UNBLOCK IS NEVER CALLED INSIDE THE BAN RUN (rule B0.3): the
#    unblocks of this bench are in three places, all declared and all printed —
#    before starting, between one block of samples and the next, and at the
#    end, where the unblock is not a tool but **the thing proved**.
#
# ---------------------------------------------------------------------------
# ⛔ AND WHY THE SERVER STARTS ON 0.0.0.0
#
# The count of §4.4-bis is **per source address**.  On `0.0.0.0` the same machine
# reaches the server as `127.0.0.1` and as `192.168.0.2`: two different keys, two
# failures each per block, and the margin below the threshold of three.  ⭐ And it
# is not taken at its word: the server log writes `from=<address>:<port>`, and
# the verdict **counts how many distinct addresses the server saw**
# (`LESSONS.md` §1.9: a denominator is read where the thing happens).
#
# ⛔ No redirection AROUND `enter.sh` (it would take away the sudo password
#    prompt) and no background subshell: the rule of 10 Aug 2026, paid for four
#    times.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTER=/media/REMOTIX/enter.sh
OUT=/media/REMOTIX/src
INSIDE=/srv/src
SRC=$INSIDE/b2/ngtcp2/examples/http3_server_proto_codec.cc
SRC_MAIN=$INSIDE/b2/ngtcp2/examples/server.cc
PER_CASE=2          # triplets per block: 2 failures per address, threshold 3
# ⛔ AND THE CREDENTIALS ARE HERE, IN CLEAR AND NEXT TO THOSE OF THE OTHER
#    BENCHES.  Until 11 Aug 2026 this bench carried its own default value
#    inside — `prova` — while `01-b3-lancia.sh`, `01-b6-launch.sh` and
#    `01-b7-launch.sh` all three use `parola-di-prova`: no B8 authentication
#    ever succeeded, and the «right» case was a copy of the «wrong» case.
#    ⚠ A default value hidden in another file is a value nobody compares.
ACCOUNT=prova
PASSWORD=parola-di-prova

# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD NO LONGER GOES THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ HERE THE PASSWORD ended up inside the string that `bash $ENTER --root "…"`
#    receives as an argument: that is in the `argv` of `bash`, in that of `sudo`
#    and in that of `python3`.  `/proc/<pid>/cmdline` on Linux is **readable by
#    anyone**, and a `ps` launched by another user during the run printed it in
#    full.  ⚠ And the benches on this machine run while others are working on
#    it.
#
# ⭐ THE ROAD IS THE ONE ALREADY IN THE HOUSE (`benches/01-b10-lancia.sh`), and not
#    a second way: a `0600` file written with `printf` — a shell **builtin**, so
#    not even the writing goes through a process with the password in `argv` —
#    passed to the bench as `--password-file`, and deleted with a `trap` even if
#    the run dies halfway.
#
# ⚠ What ends up in the `cmdline` is the PATH, not the password, and the file is
#   `0600`: whoever is not us does not open it.
# ⚠ And the name carries the bench's tag: two runs writing the same file would
#   delete each other's password — the same shape that gave birth to the
#   `PREFIX` of `01-p5-accendi.sh`.
PASSWORD_OUTSIDE=$OUT/tmp/b8-parola
PASSWORD_INSIDE=$INSIDE/tmp/b8-parola

clean_up_password() { rm -f "$PASSWORD_OUTSIDE"; }
trap clean_up_password EXIT

# ⛔ `umask` IN A SUBSHELL — the line B10 paid for with a whole run:
#    a bare `umask 077` stays on everything that comes after, including the
#    commands sent inside the container, and there it makes root write files
#    that `nicfio` can then no longer read.
mkdir -p "$OUT/tmp" \
	&& ( umask 077; : > "$PASSWORD_OUTSIDE" ) \
	&& chmod 600 "$PASSWORD_OUTSIDE" \
	|| { printf '    ⛔ cannot write %s: the run does not start\n' "$PASSWORD_OUTSIDE"; exit 2; }
printf '%s\n' "$PASSWORD" > "$PASSWORD_OUTSIDE"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ The target: a single shape for the four benches, in a single file.
TAG=b8
# shellcheck source=01-b0-target.sh
. "$OUT/01-b0-target.sh"

# ---------------------------------------------------------------------------
# ⛔⭐ THE SCENE CAN BE MOVED, AND IT SERVES ONE THING ONLY: RUNNING THIS
#     BENCH UNDER B12 WITHOUT THE TWO STEPPING ON EACH OTHER'S TOES — 11 Aug 2026.
#
# `01-b12-lancia.sh` now certifies B8 **by calling this file** instead of
# rewriting its sequence by hand (it was the root of its healthy run not being
# green: it lacked the two lives, the page and the unblock on a real ban).  ⛔ But
# a certification run cannot take port 7447 and the target's ban file, which
# belong to anyone else measuring at that moment.
#
# ⚠ AND THE THREE VARIABLES HAVE NO MOVED DEFAULT: if they are not passed, the
#   scene stays EXACTLY that of the profile (`01-b0-target.sh`), that is a
#   run by hand does not change by one byte.  A different default here would be
#   the most convenient way of measuring on a scene nobody declared.
# ⛔ And it is PRINTED, always: a scene moved silently is a number that tomorrow
#    nobody knows any more where it was taken.
if [ -n "${B8_PORT:-}${B8_BAN:-}${B8_COMMAND:-}" ]; then
	B_PORT=${B8_PORT:-$B_PORT}
	B_BAN=${B8_BAN:-$B_BAN}
	B_COMMAND=${B8_COMMAND:-$B_COMMAND}
	printf '\n    --  ⚠ SCENE MOVED (B8_PORT/B8_BAN/B8_COMMAND):\n'
	printf '        port %s · ban %s · command %s\n' "$B_PORT" "$B_BAN" "$B_COMMAND"
fi
PORT=$B_PORT
BIND=$B_BIND
ADDRESSES=$B_ADDRESSES
BAN_FILE=$B_BAN
COMMAND=$B_COMMAND
ROUND=$B_ROUND

ACTION=${1:-10}

# ---------------------------------------------------------------------------
log "Credentials for the container"
bash "$ENTER" --root "true" || { ko "cannot enter the container"; exit 2; }
ok "sudo validated"

if [ "$ACTION" = prediction ]; then
	bash "$ENTER" --root "python3 $INSIDE/01-b8-stopwatch.py --target $B_NAME --port $PORT --prediction"
	exit 0
fi

# ---------------------------------------------------------------------------
# ⛔ `build` — and it is here because on 11 Aug 2026 the graft changed: the
#    host-side ban lives in `server.cc`, which until yesterday this graft did
#    not touch.  A binary from yesterday has neither the TCP page nor the
#    unblock command, and the symptom would be «the bench cannot unblock» — that
#    is the red on the wrong defendant.
if [ "$ACTION" = build ] && [ "$B_NAME" != graft ]; then
	ko "⛔ «build» exists only for the graft: the product is not recompiled"
	ko "   by this bench.  ⛔ A bench that recompiles what it measures removes its own"
	ko "   independent witness.  It is redone with:"
	ko "     bash $ENTER --root \"bash $INSIDE/remotix/build.sh\""
	exit 2
fi
if [ "$ACTION" = build ]; then
	log "1. The grafts are removed and put back"
	inf "⛔ applying one on top of the other would leave two copies of the same"
	inf "   code, and the second one cannot be seen"
	bash "$ENTER" --root "python3 $INSIDE/01-b3-graft-rcp.py --remove > /dev/null"
	bash "$ENTER" --root "python3 $INSIDE/01-b2-graft-ngtcp2-wt.py --remove > /dev/null"
	bash "$ENTER" --root "python3 $INSIDE/01-b2-graft-ngtcp2-wt.py" \
		| grep -E "foothold|lines|CODE" | sed 's/^/        /'
	bash "$ENTER" --root "python3 $INSIDE/01-b3-graft-rcp.py" \
		| grep -E "foothold|NO |our files" | sed 's/^/        /'
	# ⛔ And the graft is COUNTED in the two files, before compiling: a graft that
	#    does not find an anchor prints «NO» and goes on.
	COUNT=$(bash "$ENTER" --root "grep -c 'REMOTIX B3' $SRC_MAIN" | tr -cd '0-9')
	if [ "${COUNT:-0}" -lt 5 ]; then
		ko "⛔ the host-side ban is NOT in server.cc («REMOTIX B3» lines: ${COUNT:-0})"
		ko "   one would compile a server without the TCP page and without the unblock"
		ko "   command, and B8 would give red on things the server never had"
		exit 3
	fi
	ok "the host-side ban is in server.cc ($COUNT «REMOTIX B3» lines)"
	log "2. It is compiled"
	rm -f "$OUT/b8-compila.log"
	if ! bash "$ENTER" --root \
		"ninja -C $INSIDE/b2/ngtcp2/build bsslserver > $INSIDE/b8-compila.log 2>&1"; then
		ko "the build failed:"
		if [ -f "$OUT/b8-compila.log" ]; then
			tail -30 "$OUT/b8-compila.log" | sed 's/^/        /'
		else
			ko "   ⛔ and the build log DOES NOT EXIST: it is not ninja that"
			ko "      kept quiet, it is that it never got as far as launching it"
		fi
		exit 3
	fi
	ok "compiled — now run «01-b8-launch.sh <blocks>» again"
	exit 0
fi

case "$ACTION" in
	''|*[!0-9]*)
		ko "unknown argument: «$ACTION»  (a number | prediction | build)"
		exit 2 ;;
esac
BLOCKS=$ACTION
if [ "$BLOCKS" -lt 1 ]; then
	ko "zero blocks: there is nothing to measure, and it is not «everything passed»"
	exit 2
fi

# ---------------------------------------------------------------------------
# ⛔ THE INITIAL STATE IS DECLARED AND VERIFIED — B0.1.
#
#    ⛔ And here the state that survives longest is THE BAN FILE: since 10 Aug
#       2026 it is on disk, so it survives even the server restart (B0.2).
#       A ban from yesterday would turn red everything that follows, and the red
#       would end up on the wrong defendant — so the file is THROWN AWAY, and it
#       is said.  ⚠ It is a bench: in production throwing away that file is
#       removing the protection from everyone.
log "1. The initial state"
rm -f "$B_OUTCOMES_OUT" "$OUT/b8-$B_NAME-server.log" "$OUT/b8-stato.txt"
target_drop_ban
inf "run: $ROUND  ·  target: $B_NAME  ·  binary md5 ${B_MD5:-unknown}"
inf "blocks: $BLOCKS  ·  samples kept per case: $((BLOCKS * PER_CASO))"

inf "⚠ server lives: 2 (one for the samples and the ban, one for persistence)"
inf "⚠ duration of the order of $(( BLOCCHI * 6 * 4 / 60 + 2 ))–$(( BLOCCHI * 6 * 6 / 60 + 4 )) minutes"
inf "⚠ and it does $((BLOCCHI * 4 + 9)) FAILED authentications on the test user: if one"
inf "  day the PAM stack had a pam_faillock, that user would get locked"

# ⛔ WHICH SERVER IT IS THAT I AM ABOUT TO START — and on the graft the files are TWO.
#    A binary without the RCP graft would not answer `HELLO`; one without the
#    host-side ban would needs no TCP page and would open no command socket.
#    ⚠ A binary OLDER than the grafted source is a binary that does not have
#    that graft (`LESSONS.md` §1.9, eighth guise), and `target_ready`
#    verifies it for both targets also taking the md5 fingerprint.
# ⛔⭐ AND THERE IS A CASE IN WHICH PUTTING THE GRAFTS BACK AND RECOMPILING IS THE
#     DEFECT, NOT THE CURE — 11 Aug 2026, and it is the reason B6 was in the
#     catalogue as «not runnable».
#
# `target_ready`, on the graft, REMOVES and puts back the two grafts (which
# recopy `rcp/rcp.c` into `examples/`) and then compiles.  ⛔ Under B12, at
# step 2/3, the fault lives precisely in `examples/rcp.c`: putting the grafts back
# would delete it, the build would produce a HEALTHY binary, and the bench would
# stay green.  ⇒ The certification would say «B8 does not see the fault» of a
# fault that was no longer there — a false red that accuses the bench instead of
# the orchestrator.
#
# ⭐ With `B8_NO_REBUILD=1` the binary THAT IS THERE is measured, and nothing
#    that counts is lost: the real verification stays whole —
#    `b0_binary_and_sources` takes the md5 fingerprint and ⛔ **refuses a binary
#    older than a source**, which is precisely the trap of R12-A.6.
#    ⚠ It is the same rule this file already applies to the product: «a bench
#      that recompiles what it measures removes its own independent witness».
if [ "${B8_NO_REBUILD:-0}" = 1 ]; then
	log "1-ter. ⚠ The grafts are not put back and nothing is compiled"
	inf "⛔ B8_NO_REBUILD=1: the binary that is there is measured — under B12"
	inf "   putting the grafts back would delete the fault from examples/rcp.c"
	inf "   and the bench would be green on a server that does not have the fault"
	inf "⚠ the check that counts stays: md5 of the binary, and the binary must NOT"
	inf "  be older than any source"
	if [ "$B_NAME" = graft ]; then
		# ⚠ The glob is the same as `target_ready`: it is a copy, and it is
		#   declared.  The day a source is added to the graft it must be added in
		#   both places.
		b0_binary_and_sources \
			"$INSIDE/b2/ngtcp2/examples/*.cc $INSIDE/b2/ngtcp2/examples/*.c $INSIDE/rcp/rcp.c" \
			|| exit 3
	else
		b0_binary_and_sources "$INSIDE/remotix/*.c $INSIDE/remotix/*.h" || exit 3
	fi
else
	target_ready || exit 3
fi

# ⛔ And under B12 the count of the «REMOTIX B3» lines below stays, and it is right
#    that it stays: it says the server I am about to start has the RCP layer and
#    the host-side ban.  The B12 fault does not touch those lines.
if [ "$B_NAME" = graft ]; then
	bash "$ENTER" --root \
		"{ grep -c 'REMOTIX B3' $SRC; grep -c 'REMOTIX B3' $SRC_MAIN; } > $INSIDE/b8-stato.txt 2>&1"
	if [ ! -f "$OUT/b8-stato.txt" ]; then
		ko "I could not look at the state of the server: the file is not there"
		exit 2
	fi
	GRAFT=$(sed -n 1p "$OUT/b8-stato.txt")
	GUEST=$(sed -n 2p "$OUT/b8-stato.txt")
	case "$GRAFT$GUEST" in
		''|*[!0-9]*) ko "I could not count the RCP graft in the sources:"
		             sed 's/^/        /' "$OUT/b8-stato.txt"; exit 2 ;;
	esac
	if [ "$GRAFT" -lt 3 ]; then
		ko "⛔ the RCP graft is NOT in the codec ($GRAFT «REMOTIX B3» lines)"
		ko "   this server does not speak RCP: «01-b8-launch.sh build»"
		exit 3
	fi
	if [ "$GUEST" -lt 5 ]; then
		ko "⛔ the HOST-SIDE BAN is not in server.cc ($GUEST lines)"
		ko "   no TCP page and no unblock command:"
		ko "   «TARGET=graft ... 01-b8-launch.sh build»"
		exit 3
	fi
	ok "the graft is in the two files (codec $GRAFT lines · host $GUEST)"
else
	# ⭐ On the product the equivalent piece is the command socket, and it is
	#    MEASURED in the source before starting: without it, every unblock of this
	#    run would exit 3 and the symptom would be «the bench cannot unblock»,
	#    that is the red on the wrong defendant.
	# ⛔ And this is «the half nobody did» of B0.3: pointing `01-b8-unblock.py` at
	#    the product, which has never been tried as of today.
	COUNT=$(bash "$ENTER" --root "grep -c 'UNBLOCK ' $INSIDE/remotix/command.c" | tr -cd '0-9')
	if [ "${COUNT:-0}" -ge 1 ]; then
		ok "the unblock command is in command.c ($COUNT «UNBLOCK » lines)"
		inf "⛔ and this is the FIRST time 01-b8-unblock.py is pointed at the"
		inf "   product: if the PING further down does not answer, the first suspicion"
		inf "   is on this seam, not on the ban"
	else
		ko "⛔ «UNBLOCK » does not appear in command.c: this product does not have the"
		ko "   unblock command, and B0.3 would stay without its tool"
		exit 3
	fi
fi

# ---------------------------------------------------------------------------
# ⛔ 1-bis. THE CERTIFICATION THE WIRE CANNOT DO, AND IT IS DONE **FIRST**.
#
# `01-b8-ban-test.c` tests the three pieces of the ban that on the wire would be
# seen only by waiting twelve hours, rebooting a machine or breaking the
# permissions of a file run by root — where root ignores permissions.
#
# ⛔ FINDING A20, 11 Aug 2026: until tonight `grep -rn "01-b8-ban-test"` on the
#    whole tree found **no caller**.  A certification that nobody runs is not a
#    certification: it is a file that says it is a test.  Now this run calls it,
#    and its exit status counts.
#
# ⛔ And it is run as a NORMAL USER, not inside the container: section 4 —
#    «zero bans» against «I could not read» — as root would be green by
#    construction, and it is precisely the emptiest check of all.  The file
#    knows it and turns itself red if launched as root.
log "1-bis. ⛔ The certification off the wire (LESSONS.md §1.2: FIRST)"
# ⛔ WHERE IT RUNS, and the distinction was paid for on 11 Aug 2026.
#
#    This step ran on the HOST, and the comment above said «outside the
#    container».  ⛔ But the real constraint is «as a NORMAL USER» — section 4
#    tells «zero bans» from «I could not read», and as root it would be green by
#    construction — while «outside the container» was only the place where it
#    happened to be.
#
#    And on the host `gcc` IS NOT THERE: `[M]` 11 Aug 2026, the run stopped here
#    with exit 3.  ⭐ The bench declared it well — «it did not pass: it is a piece
#    of B8 nobody tested» — but it stayed not run.
#
# ⭐ The cure keeps both constraints: inside the container, where gcc is there,
#    and WITHOUT `--root`, where one is a normal user (id 1000).  The file turns
#    itself red if launched as root, so the constraint stays watched over by it
#    and not by this comment.
# ⛔⭐ AND HERE THERE WAS THE TRAP THIS VERY FILE FORBIDS AT THE TOP — measured
#     on 11 Aug 2026, evening, at the first non-interactive run.
#
# The line was `bash "$ENTER" "gcc …" 2>"$OUT/b8-prova-ban.log"`: a
# redirection **AROUND** `enter.sh`.  ⛔ `enter.sh` calls `sudo -v -S -p
# Password`, which prints the prompt on **stderr** and reads from stdin: with
# stderr diverted to a file, the prompt does not reach whoever is watching, ⇒
# nobody answers, ⇒ the run hangs forever on a question that cannot be seen.
# `[M]` `ps` on the server: `sudo -v -S -p Password sudo:` stuck, and the bench
# stuck with it at step 1-bis.
#
# ⚠ AND IT HAD NEVER BEEN SEEN because from a real terminal the prompt had
#   already been satisfied by the first line of the bench, and sudo's timestamp
#   covered the rest of the run: the defect appears only when that credit has
#   expired — that is on long runs and on those launched from another machine.
#   ⛔ It is the fourth guise of the same trap, inside the file that describes it.
# ⭐ The cure is the one written at the top of `01-b12-lancia.sh`: the
#    redirection goes INSIDE the quotes, and the file is read afterwards.
PB=/srv/src/tmp/b8-prova-ban.$$
rm -f "$OUT/b8-prova-ban.log"
if ! bash "$ENTER" "gcc -std=c11 -Wall -Wextra -I$INSIDE/rcp -o $PB \
	$INSIDE/01-b8-ban-test.c $INSIDE/rcp/rcp.c > $INSIDE/b8-prova-ban.log 2>&1"; then
	ko "⛔ 01-b8-ban-test.c does not compile against $INSIDE/rcp/rcp.c:"
	tail -20 "$OUT/b8-prova-ban.log" | sed 's/^/        /'
	ko "   ⚠ and «does not compile» is NOT «passes»: the eighth guise of LESSONS.md §1.9"
	ko "   says to look at the builder's outcome, not at the presence of the file"
	exit 3
fi
bash "$ENTER" "$PB"
TEST_BAN=$?
# ⛔ And here too the redirection goes INSIDE: `>/dev/null 2>&1` around
#    `enter.sh` hides the password prompt exactly as above.
bash "$ENTER" "rm -f $PB > /dev/null 2>&1"
if [ "$TEST_BAN" -ne 0 ]; then
	ko "⛔ the certification off the wire does NOT pass (exit $TEST_BAN):"
	ko "   as long as it is red, the three pieces of the ban the wire does not see are"
	ko "   proved by nothing, and the green of the run below is worth less"
	exit 3
fi
ok "certification off the wire: passed (it prints the denominator itself)"

# ---------------------------------------------------------------------------
# ⛔ And the prediction is printed BEFORE the numbers, or it is not a prediction.
log "2. What I expect, before measuring"
# ⛔ FINDING R12-A.33, 11 Aug 2026, found by `01-b0-chiamate.py`.
#    This line called the stopwatch **without `--target` and without
#    `--port`**, which are mandatory since the shared profile exists.
#    `[M]` on the server: *«error: the following arguments are required: --port,
#    --target»*.  ⇒ The prediction **was never printed**, and the step this
#    bench calls «before measuring» had been, for days, an argparse usage line.
#    ⚠ And it made nothing fail: the run went on.
#    ⭐ The right line already existed twenty lines further up (the `prediction` action).
bash "$ENTER" --root "python3 $INSIDE/01-b8-stopwatch.py --target $B_NAME --port $PORT --prediction" \
	|| ko "⚠ the prediction was not printed: the run goes on, but without it"

# ---------------------------------------------------------------------------
# ⛔ `target_options_python` carries with it --target, --port, --output,
#    --md5 and --round: the same five as B5, B6 and B7, in a single place.
CHRONO="python3 -u $INSIDE/01-b8-stopwatch.py $(target_options_python) \
	--addresses $ADDRESSES --command $COMMAND \
	--user $ACCOUNT --password-file $PASSWORD_INSIDE"

TURN_ON() # $1 = why
{
	# ⛔ The start lives in `target_turn_on`: it passes `--ban-file` and
	#    `--command-socket` in the syntax that target understands
	#    (`--ban-file=X` for the graft, `--ban-file X` for the product),
	#    checks the port first, and refuses a cap it cannot give.
	if ! target_turn_on "$(printf '%s' "$1" | tr ' ' '-')" "$B_IDLE_LONG"; then
		ko "the server did not start for «$1»"
		if [ "$B_NAME" = product ]; then
			ko "   ⛔ and on this target «does not start» has one more cause:"
			ko "   if «$BAN_FILE» is there and cannot be read, the product REFUSES to"
			ko "   start on purpose (src/main.c).  It is not «zero bans»."
		fi
		return 4
	fi
	PID=$B_PID
	# ⛔ AND RIGHT AWAY THE FINGERPRINT: is it the server I declared?
	target_fingerprint || return 4
	# ⛔ And one looks at what it SAID at start-up about the ban: «zero bans» and
	#    «I could not read the file» are two different facts, and the line that
	#    tells them apart is the only proof that persistence is on.
	#
	# ⛔ FINDING A21, 11 Aug 2026: until tonight this part PRINTED and compared
	#    nothing — «it is printed *and* compared, and the exit status is that of
	#    the comparison» (B0.4) — and if the log had not existed `grep` would
	#    have written on stderr and the script would have gone on without a word.
	#    That is, the start declared, in the comment two lines above, a check it
	#    did not do: the two things that comment says it tells apart stayed
	#    indistinct precisely there.
	#    ⚠ The verdict then looks at them (`read_log`), but whoever reads the
	#      run live believes this line, and it is an hour earlier.
	inf "what it said about the ban at start-up (printed AND compared — B0.4):"
	if [ ! -f "$B_LOG_OUT" ]; then
		ko "⛔ the server log DOES NOT EXIST ($B_LOG_OUT): it is not «the"
		ko "   server said nothing about the ban», it is that I could not look"
		return 4
	fi
	grep -E "$B_R_BAN_LOADED|$B_R_BAN_UNREADABLE|host-side ban|the page is served|$B_R_PAGE|unblock command" \
		"$B_LOG_OUT" | sed 's/^/        /'
	# ⛔⭐ AND THE TWO LINES ARE WRITTEN DIFFERENTLY IN THE TWO SERVERS — they come
	#     from the profile, not from here.
	#       innesto   «bans loaded: N»  ·  «COULD NOT READ the ban file»
	#       product  «ban: <file>, N addresses loaded»  ·  «exists and could
	#                 NOT be read»  — ⛔ and in that case the product does NOT
	#                 START at all, so one does not even get here.
	LOADS=$(grep -c "$B_R_BAN_LOADED" "$B_LOG_OUT")
	UNREADABLE=$(grep -c "$B_R_BAN_UNREADABLE" "$B_LOG_OUT")
	SOCKET=$(grep -c "the unblock command listens on" "$B_LOG_OUT")
	if [ "$UNREADABLE" -gt 0 ]; then
		ko "⛔ the server declares it could NOT read the ban file."
		ko "   ⛔ This is NOT «zero bans»: the persistence of §4.4-bis starts from"
		ko "   an unknown state, and every line about the ban that follows is worth less than zero"
		return 4
	fi
	if [ "$LOADS" -eq 0 ]; then
		ko "⛔ the server said NOTHING about the ban at start-up (no"
		ko "   «bans loaded» line and no «COULD NOT READ» line)."
		ko "   ⛔ It is precisely the pair this check exists to separate:"
		ko "   without one of the two, «zero bans» and «I could not look» have"
		ko "   the same face (LESSONS.md §1.9 rule 1)"
		return 4
	fi
	ok "the server declared the state of the ban: $LOADS «bans loaded» lines"
	ok "   and 0 «could not read» lines — they are two facts, and they are distinct"
	if [ "$SOCKET" -eq 0 ]; then
		ko "⛔ the unblock command is NOT listening: «$COMMAND» was not born."
		ko "   Without it, every unblock of this run exits 3 and B0.3 does not apply —"
		ko "   and the symptom, further on, would be «the bench cannot"
		ko "   unblock», that is the red on the wrong defendant"
		return 4
	fi
	ok "the unblock command is listening (B0.3 has the tool it demands)"
	return 0
}

TURN_OFF()
{
	printf '\n===== %s =====\n' "$1" >> "$OUT/b8-$B_NAME-server.log"
	if [ -f "$B_LOG_OUT" ]; then
		cat "$B_LOG_OUT" >> "$OUT/b8-$B_NAME-server.log"
	else
		printf '(no log for this life)\n' >> "$OUT/b8-$B_NAME-server.log"
	fi
	target_turn_off
}

ALIVE() # ⛔ B0.5: after every test the server must still be there
{
	if [ -n "${PID:-}" ] && [ -d "/proc/$PID" ]; then
		ok "the server is still alive after «$1» (PID $PID)"
		return 0
	fi
	ko "⛔ THE SERVER DIED during «$1»"
	return 4
}

# ---------------------------------------------------------------------------
log "3. The FIRST life of the server — the samples and the ban run"
TURN_ON "first life" || exit 4

log "3.0  The initial state, declared AND verified (B0.1)"
inf "⛔ and this unblock is BEFORE the run, not inside it (B0.3)"
bash "$ENTER" --root "$CHRONO --initial-state"
if [ $? -ne 0 ]; then
	ko "⛔ the initial state is not the declared one: I stop"
	ko "   measuring from an unknown state means measuring the machine's history"
	TURN_OFF "first life (initial state failed)"
	exit 2
fi

# ⛔ THE WARM-UP IS A WHOLE BLOCK, NUMBER ZERO — form E9.
#    The first connections of a process's life pay for the cold cache, the PAM
#    modules being opened, the malloc arenas growing.  ⚠ Here it is not left to
#    chance: block 0 is a triplet — **one per case**, so the success road *and*
#    the failure road — and it is discarded **by a rule written before**, never
#    afterwards.  ⭐ And it is printed anyway, with its times: discarding silently
#    is the most convenient way of hiding an awkward number.
log "3.0b  the WARM-UP — a triplet, discarded by a rule written before (E9)"
bash "$ENTER" --root "$CHRONO --samples --block 0 --per-case 1"
ALIVE "the warm-up" || exit 4
bash "$ENTER" --root "$CHRONO --unblock $ADDRESSES --why dopo-la-scaldata"

b=1
while [ "$b" -le "$BLOCKS" ]; do
	log "3.$b  block $b of $BLOCKS — $((PER_CASO * 3)) attempts"
	bash "$ENTER" --root "$CHRONO --samples --block $b --per-case $PER_CASE"
	OUTCOME=$?
	ALIVE "block $b" || exit 4
	if [ "$OUTCOME" -eq 2 ]; then
		ko "⛔ block $b did not start (plan or initial state): I stop"
		ko "   better no samples than samples taken outside the balance"
		TURN_OFF "first life (block $b did not start)"
		exit 2
	fi
	if [ "$OUTCOME" -ne 0 ]; then
		ko "block $b ended badly (exit $OUTCOME): I stop"
		TURN_OFF "first life (block $b failed)"
		exit "$OUTCOME"
	fi
	# ⛔ THE UNBLOCK BETWEEN ONE BLOCK AND THE NEXT, AND IT IS DECLARED — B0.3.
	#    It is this bench's choice between the two B8 allows: «vary the source
	#    address» or «unblock between one block and the next».
	#    ⚠ It changes what the measurement is measuring, and that is why it is
	#      printed: the samples are ALWAYS taken with the count below threshold.
	if [ "$b" -lt "$BLOCKS" ]; then
		bash "$ENTER" --root "$CHRONO --unblock $ADDRESSES --why fra-i-blocchi"
	fi
	b=$((b + 1))
done

# ---------------------------------------------------------------------------
# ⛔ AND NOW THE BAN RUN — with an unblock BEFORE, and none inside.
log "4. ⛔ The ban run — and from here on NOBODY unblocks anything (B0.3)"
inf "the unblock below is the LAST before the run: it serves to start from a"
inf "reset count, and it is declared.  ⚠ If it failed, the ban run would notice"
inf "   anyway — the balance of the blocks keeps every address at"
inf "   two failures, that is one below the threshold"
bash "$ENTER" --root "$CHRONO --unblock $ADDRESSES --why prima-del-giro-del-ban"
bash "$ENTER" --root "$CHRONO --ban before"
OUTCOME_BAN=$?
ALIVE "the ban run" || exit 4
if [ "$OUTCOME_BAN" -eq 2 ]; then
	ko "⛔ the ban run did not start: the verdict would be blind"
	TURN_OFF "first life (ban run did not start)"
	exit 2
fi

TURN_OFF "first life"

# ---------------------------------------------------------------------------
# ⛔ THE SECOND LIFE — and it serves ONE thing only: invariant I7.
log "5. ⭐ The SECOND life of the server — does the ban survive the restart?"
inf "⛔ the ban file is NOT touched: it is the only road by which the ban can"
inf "   come back, and throwing it away here would mean proving the opposite of"
inf "   what one wants to prove"
TURN_ON "second life" || exit 4
bash "$ENTER" --root "$CHRONO --ban after"
OUTCOME_AFTER=$?
ALIVE "persistence and the unblock" || exit 4

# ⛔ And the machine is put back in order BEFORE the verdict, and it is declared:
#    B0.3 says every bench that unblocks declares it.  Without this line the
#    next bench would find an address out for twelve hours.
log "6. The machine is put back in order (B0.3)"
bash "$ENTER" --root "$CHRONO --unblock $ADDRESSES --why pulizia-finale"
TURN_OFF "second life"

# ---------------------------------------------------------------------------
log "7. The verdict — the bench compares it, not whoever reads (B0.4)"
# ⛔ AND THE VERDICT IS ALSO WRITTEN TO A FILE, inside the quotes of `enter.sh` —
#    never a redirection AROUND it, which would take away the password prompt.
#    ⭐ It serves whoever certifies this bench: `01-b12-lancia.sh` must be able to
#    look for the fault's MARK in the output, and the output of a launcher that
#    runs OUTSIDE the container cannot be captured (it is the same solution C2
#    has always used: the bench writes, the orchestrator reads).
# ⚠ And it is printed anyway, line by line: a verdict that ends up only in a
#   file is a verdict nobody reads live.
VERDICT_FILE="$OUT/b8-verdetto-$B_NAME.txt"
rm -f "$VERDICT_FILE"
bash "$ENTER" --root "$CHRONO --verdict --log $INSIDE/b8-$B_NAME-server.log > $INSIDE/b8-verdetto-$B_NAME.txt 2>&1"
OUTCOME=$?
if [ -f "$VERDICT_FILE" ]; then
	cat "$VERDICT_FILE"
else
	ko "⛔ the verdict did NOT write its file ($VERDICT_FILE): it is not"
	ko "   «it said nothing», it is that one never got as far as reading it"
fi

# ---------------------------------------------------------------------------
# ⛔ AND THE BENCH CERTIFIES ITSELF — `LESSONS.md` §1.2, and it is done AFTER
#    because what the run has just produced is what gets broken.  One fault at a
#    time, built by hand, and the verdict must turn red **at that point**: a
#    bench that does not reproduce is not a proof of correctness (§1.3).
log "8. ⛔ The certification: the fault is built and the red is demanded"
bash "$ENTER" --root "$CHRONO --certify --log $INSIDE/b8-$B_NAME-server.log"
CERT=$?
if [ "$CERT" -ne 0 ]; then
	ko "⛔ the certification of the JUDGE does not pass: as long as it is red, a green"
	ko "   of B8 means nothing"
fi

log "Outcome"
# ⛔ FOUR OUTCOMES, NOT TWO.  «They do not separate» and «I did not look enough to
#    be able to say it» are two facts with two different cures, and giving them
#    the same colour is form E8 applied to a verdict.
# ⛔ FIVE OUTCOMES, NOT TWO.  «They do not separate», «I did not look enough to be
#    able to say it», «they separate but the culprit is PAM» and «the ban does not
#    work» are four facts with four different cures, in four different files:
#    giving them the same colour is form E8 applied to a verdict.
case "$OUTCOME" in
	0) ok "⭐ B8 passes against «$B_NAME» — and the resolutions above say how far"
	   ok "   it looked.  ⚠ The other target is another program" ;;
	5) ko "⛔ B8: the BAN passes in full, but the medians DO SEPARATE"
	   inf "⛔ and outcome 5 is given ONLY when the defendant has been MEASURED and is"
	   inf "PAM: the verdict above prints the two numbers from the server log"
	   inf "that support it (how long it waited beyond the fixed second"
	   inf "on the refused and on the admitted) and which case is the slowest on the wire."
	   inf "The cure is in benches/rcp/authentication.c and in the PAM stack: it is the"
	   inf "[?] that RCP.md §4.4-bis has already declared, and that the ban does not close."
	   inf "⚠ If the defendant had been another — or not measurable — this"
	   inf "run would have exited 1, not 5: the leniency is written for PAM." ;;
	3) ko "⚠ B8 SUSPENDED: run again with more blocks (now $BLOCKS)" ;;
	2) ko "⛔ B8: there was nothing to judge" ;;
	*) ko "⛔ B8: something does not pass" ;;
esac
if [ "$OUTCOME_AFTER" -ne 0 ]; then
	ko "⚠ and the persistence phase exited $OUTCOME_AFTER: the verdict"
	ko "  above says which lines are missing"
fi
# ⛔ And the certification enters the outcome, instead of staying a line read
#    in passing: an uncertified bench promotes nothing.
if [ "$CERT" -ne 0 ] && [ "$OUTCOME" -eq 0 ]; then
	ko "⛔ ...but the bench is NOT certified: the outcome becomes red"
	OUTCOME=1
fi
inf "the facts, one per line: $B_OUTCOMES_OUT  (every line carries the target)"
inf "the server log, both lives: $OUT/b8-$B_NAME-server.log"
inf "the ban file: $BAN_FILE (⚠ it stays there on purpose, to look at it)"
exit "$OUTCOME"
