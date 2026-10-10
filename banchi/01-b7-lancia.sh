#!/bin/bash
#
# 01-b7-lancia.sh — runs ON THE SERVER.  B7: the farewell, from the receiving side.
#
#   BERSAGLIO=innesto  bash .../01-b7-lancia.sh              everything
#   BERSAGLIO=prodotto bash .../01-b7-lancia.sh solo tempo   a single case
#   BERSAGLIO=innesto  bash .../01-b7-lancia.sh elenco       the predictions
#   BERSAGLIO=prodotto bash .../01-b7-lancia.sh frasi        and the sentences of §8.2
#
# ⛔ `BERSAGLIO` IS MANDATORY — see `01-b0-bersaglio.sh`.
#
# ---------------------------------------------------------------------------
# ⛔⭐ WHAT CHANGES WHEN B7 IS POINTED AT THE PRODUCT — the prediction, written BEFORE
#
# | what | graft | product | why |
# |---|---|---|---|
# | ⭐ **the reasons that can be provoked** | **7** out of 15 | ⛔ **8** out of 15 | `src/main.c` says farewell to all the sessions with `SERVER_IN_CHIUSURA` `0x0C` before exiting, and WAITS up to 2 s for the bytes to go out.  The graft has no shutdown path (grep: zero occurrences in `01-b3-rcp-innesta.py`).  ⛔ **If B7 pointed at the product keeps saying «7 out of 7», the denominator is wrong and the bench is looking the other way** |
# | the `server-in-chiusura` case | does not exist | ⭐ exists, and **shuts the server down** | it runs last, in an invocation of its own, and B0.5 does not apply to it: the death of the server IS the thing proved |
# | where the exclusion of `0x0C` is measured | `rcp/rcp.c` + `01-b3-rcp-innesta.py`, expected **zero** | `main.c` + `trasporto.c` + `webtransport.c` + `rcp.c`, expected **more than zero** | ⛔ `rcp.c` is identical byte for byte in the two servers: looking for it there would say «zero» on both, and it is a denominator read where the thing does NOT happen |
# | `§3.1 point 1` in the log | line `REMOTIX B3: congedo motivo=0xNN` | line `HH:MM:SS.mmm rcp congedo motivo=0xNN` | ⛔ `rcp.c` writes it, the same — what changes is **the prefix**.  Looking for «REMOTIX B3: » would have given «point 1 absent» on ALL the product's cases |
# | the other six reasons | same | same | they are decided by `rcp.c`, identical |
# | `gia-attiva-remota` (0x0F) | the place is freed at the death of the CONNECTION | ⭐ it is freed at the closing of the **stream** | `src/webtransport.c` `wt_stream_chiuso()`.  ⚠ With the test client the two instants coincide, so here **no** difference is expected: a browser sees the difference (B11, `[M]` 7 «place DENIED» out of 9 with Chrome) |
# | the inactivity cap | 120 s, requested by us | ⛔ 30 s, **not chosen by us** | `IDLE_MS` in `src/trasporto.c`.  The `tempo-scaduto` case keeps quiet for 20 s: it fits under the 30, but the margin goes from 100 s to 10 s |
# | B2's echo on the streams | present | ⛔ not present | `scarta_stream_di_troppo()`: «the bytes are thrown away and NOT sent back».  B7 never waits for it, so it does not touch it — ⚠ but no new tool must wait for it |
#
# ⛔ WITH A FILTER THE RUN IS PARTIAL, AND IT SAYS SO.  The green outcome reads «the
#    selected cases pass», never «B7 passes».  ⚠ And a filter that matches no
#    name exits **2**, not 0: «I have nothing to measure» is not
#    «everything passed».
#
# ---------------------------------------------------------------------------
# ⛔ WHAT IT TESTS
#
# `RCP.md` §8.1: *«the farewell is verified from the side that receives it, never
# from the log of whoever sends it»*.  In v1, for **three phases**, the server wrote
# «farewell to the client» while the client wrote «network error»
# (`LEZIONI.md` §1.7).
#
# ⛔ And the roads are TWO (§3.1): the `CONGEDO` on the control channel **and** the
#    reason code in the closing of the WebTransport session.  They are counted
#    **separately**, with two denominators, because on 10 Aug 2026 the second
#    was missing in **fourteen cases out of thirty-six** and no bench had
#    noticed: it was enough for the first to arrive.
#
# ⛔ The fault of `FASI.md` §01-filo-nudo §C1 — «the sending of the `CONGEDO` is
#    removed and the code in the closing is left» — must turn this bench RED.
#    If it stays green it is doing an `||` where an `&&` is needed.
#
# ---------------------------------------------------------------------------
# ⛔ AND THE SERVER LOG IS READ AT TWO POINTS ONLY, DECLARED
#
#   · §3.1 **point 1** — the line «what I did not understand», which is by
#     definition a line of whoever closes: it is point 1 that asks for it;
#   · the **client→server** direction — where whoever receives IS the server.
#
# The reason the server SENDS is always and only judged by the two roads, read
# on the wire by the test client.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
UTENTE=prova
PAROLA=parola-di-prova

# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD NO LONGER GOES THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ HERE THE PASSWORD ended up inside the string that `bash $ENTRA --root "…"`
#    receives as an argument: that is in the `argv` of `bash`, in that of `sudo`
#    and in that of `python3`.  `/proc/<pid>/cmdline` on Linux is **readable by
#    anyone**, and a `ps` launched by another user during the run printed it in
#    full.  ⚠ And the benches on this machine run while others are working on
#    it.
#
# ⭐ THE ROAD IS THE ONE ALREADY IN THE HOUSE (`banchi/01-b10-lancia.sh`), and not
#    a second way: a `0600` file written with `printf` — a shell **builtin**, so
#    not even the writing goes through a process with the password in `argv` —
#    passed to the bench as `--parola-file`, and deleted with a `trap` even if
#    the run dies halfway.
#
# ⚠ What ends up in the `cmdline` is the PATH, not the password, and the file is
#   `0600`: whoever is not us does not open it.
# ⚠ And the name carries the bench's tag: two runs writing the same file would
#   delete each other's password — the same shape that gave birth to the
#   `PREFISSO` of `01-p5-accendi.sh`.
PAROLA_FUORI=$FUORI/tmp/b7-parola
PAROLA_DENTRO=$DENTRO/tmp/b7-parola

ripulisci_parola() { rm -f "$PAROLA_FUORI"; }
trap ripulisci_parola EXIT

# ⛔ `umask` IN A SUBSHELL — the line B10 paid for with a whole run:
#    a bare `umask 077` stays on everything that comes after, including the
#    commands sent inside the container, and there it makes root write files
#    that `nicfio` can then no longer read.
mkdir -p "$FUORI/tmp" \
	&& ( umask 077; : > "$PAROLA_FUORI" ) \
	&& chmod 600 "$PAROLA_FUORI" \
	|| { printf '    ⛔ cannot write %s: the run does not start\n' "$PAROLA_FUORI"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FUORI"

# ⛔ The target: a single shape for the four benches, in a single file.
SIGLA=b7

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"
IND=$B_IND
PORTA=$B_PORTA
# ⛔ The root of the sources from which the exclusion of 0x0C is measured: it
#    depends on the target, and it is NOT `rcp.c` alone.
DENTRO_SORG=$DENTRO

AZIONE=${1:-tutto}
FILTRO=${2:-}

log "Credentials for the container"
bash "$ENTRA" --root "true" || { ko "cannot enter the container"; exit 2; }
ok "sudo validated"

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b7-congedo.py --bersaglio $B_NOME --elenco"
	exit $?
fi

FRASI=
[ "$AZIONE" = frasi ] && FRASI=--frasi

# ---------------------------------------------------------------------------
# ⛔ 1. THE SERVER IS PREPARED — and the two roads are not the same.
#
#   innesto   the grafts are removed and put back, the mark is counted in the
#             sources, it is compiled looking at the builder's outcome, and then
#             the md5 fingerprint of the binary is taken;
#   prodotto  ⛔ it is NOT recompiled — `src/` does not belong to this bench, and a
#             bench that recompiles what it measures removes its own independent
#             witness — and one stops if the binary is older than a source.
#             `[M]` 11 Aug 2026: it was, by an hour.
#
# ⛔ NO REDIRECTION AROUND `enter.sh`: it would take away the sudo password
#    prompt, and the script would stay waiting for a question nobody sees.
#    The redirections go inside the quotes of the remote command (see
#    `01-b0-bersaglio.sh`).
bersaglio_pronto || exit 3

# ⛔ AND THE DEFERRED CLOSING MUST BE THERE, because it is precisely the cure of
#    the defect B7 exists to watch over: without it, the closing capsule does not
#    leave on any violation found at the first message — 14 cases out of 36, on
#    10 Aug 2026.  ⚠ Finding it absent is not a B7 red: it is the bench saying
#    «you are about to measure a server different from the one you believe».
# ⚠ And the file where it lives changes with the target: in the graft it is the
#   grafted codec, in the product it is `webtransport.c` (`chiudi_sessione()`).
if [ "$B_NOME" = innesto ]; then
	DOVE_RIMANDO=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
else
	DOVE_RIMANDO=$DENTRO/remotix/webtransport.c
fi
RIMANDO=$(bash "$ENTRA" --root "grep -c 'DEFERRED' $DOVE_RIMANDO" | tr -cd '0-9')
if [ "${RIMANDO:-0}" -ge 1 ]; then
	ok "the deferred closing (§3.1 point 3) is in $(basename "$DOVE_RIMANDO")"
else
	ko "⚠ the DEFERRED closing is not in $DOVE_RIMANDO: if the second"
	ko "  road turns out absent, the cause is THIS and not the RCP module"
fi

# ---------------------------------------------------------------------------
# ⛔ 2. THE INITIAL STATE OF THE BAN — B0.1, B0.2, B0.3.
#
# B7 fails **one** authentication attempt (B0.3 says so), that is it consumes
# one of the three of §4.4-bis: alone it does not ban, but added to a residue
# from another run it does.  ⛔ And on the product the ban is on FILE: a ban from
# yesterday would turn red everything that follows, with the red on the wrong
# defendant.
log "2. The initial state of the ban (B0.1, B0.2)"
bersaglio_butta_il_ban

# ---------------------------------------------------------------------------
log "3. The server starts"
inf "⚠ inactivity cap \$B_IDLE_LUNGO = $B_IDLE_LUNGO ms: the case"
inf "  «tempo-scaduto» keeps quiet for twenty seconds, and a shorter cap"
inf "  would close the connection on its own — the bench would read «it"
inf "  dropped» where nothing dropped, and on top of that WITHOUT a reason, that is"
inf "  precisely the shape B7 must be able to tell from a farewell"
if [ "$B_IDLE_SCELTA" = no ]; then
	inf "⛔ and on this target we do not choose that number (IDLE_MS in"
	inf "   src/trasporto.c): the margin above the 20 s goes from 100 s to 10 s"
fi
bersaglio_accendi filo "$B_IDLE_LUNGO" || exit 4
PID=$B_PID

inf "does the unblock command answer? (PING — the denominator of B0.3)"
bersaglio_ping || { ko "⛔ the unblock command does not answer: at the end I could not"
                    ko "   put the machine back in order"
                    bersaglio_spegni; exit 4; }

# ⛔ 3-bis. DID I MEASURE THE SERVER I DECLARED?
log "3-bis. The target's fingerprint (LEZIONI.md §1.9, corollary 5)"
bersaglio_impronta
case $? in
0) : ;;
*) ko "⛔ I stop: the numbers would end up on the wrong target"
   bersaglio_spegni; exit 6 ;;
esac

fermare() { bersaglio_spegni; }

# ---------------------------------------------------------------------------
log "4. The farewell, from the receiving side"
OPZ=$(bersaglio_opzioni_python)
COMUNE="--indirizzo $IND $OPZ --utente $UTENTE --parola-file $PAROLA_DENTRO \
	--registro $B_LOG --pagina $DENTRO/01-b11-pagina.html --dentro $DENTRO_SORG"
if [ -n "$FILTRO" ]; then
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py $COMUNE --solo $FILTRO"
else
	# ⛔ The normal run EXCLUDES `server-in-chiusura`, which shuts the server down:
	#    it runs afterwards, with the server restarted on purpose (point 7).
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py $COMUNE $FRASI --escludi server-in-chiusura"
fi
ESITO=$?

# ---------------------------------------------------------------------------
log "5. ⛔ Is the server still alive? — B0.5, from outside"
inf "the bench asks it at every case; this asks the SYSTEM, which is a"
inf "different witness: a process can answer and have already lost its children"
if [ -d "/proc/$PID" ]; then
	ok "process $PID is still there"
else
	ko "⛔ THE SERVER DIED during the bench"
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "6. The two roads, as the server wrote them"
inf "⚠ THIS IS NOT THE VERDICT — the verdict is that of point 4, read from the"
inf "  receiving side (§8.1).  Here one looks at the other half of the same story:"
inf "  if the two columns do not resemble each other, the log and the wire tell two"
inf "  different things, and it is the defect shape §3.1 point 3 exists to"
inf "  unmask"
if [ -f "$B_LOG_FUORI" ]; then
	# ⛔ It is counted and printed: a `grep -c` that says 0 and a file that cannot
	#    be read are two different facts, and the branch below keeps them apart.
	C1=$(grep -c "congedo motivo=" "$B_LOG_FUORI")
	C2=$(grep -c "closed the WebTransport session" "$B_LOG_FUORI")
	C3=$(grep -c "session closure DEFERRED" "$B_LOG_FUORI")
	inf "farewells sent (§3.1 point 2, from the sender's side): ${C1:-0}"
	inf "session closings that WENT OUT (§3.1 point 3):         ${C2:-0}"
	inf "closings only DEFERRED:                                ${C3:-0}"
	if [ "${C3:-0}" -gt "${C2:-0}" ]; then
		ko "⛔ ${C3} closings deferred and only ${C2} gone out: some capsule"
		ko "   never left — it is the defect of the 14 out of 36 of 10 August"
	fi
	grep "congedo motivo=" "$B_LOG_FUORI" | tail -8 | sed 's/^/        /'
else
	ko "⛔ THE LOG CANNOT BE READ: $B_LOG_FUORI does not exist"
	ko "   it is not the server that did not write — it is that it cannot be read"
	ko "   (volume not mapped? server never started? name changed?)"
	ESITO=1
fi

# ---------------------------------------------------------------------------
# ⭐⛔ 7. THE SHUTDOWN RUN — and on this target it exists, on the other it does not.
#
# `SERVER_IN_CHIUSURA` `0x0C` is not provoked with a crooked byte: a `SIGTERM`
# provokes it.  ⛔ So this case **shuts the server down**, runs last and in an
# invocation of its own, and B0.5 does not apply to it — the death of the server
# IS the thing proved, and the bench declares it instead of giving itself a red.
#
# ⚠ And the server is restarted on purpose: the one of point 3 is still alive, and
#   it is shut down first, properly, watching the port get freed.
log "7. ⭐ The shutdown run (SERVER_IN_CHIUSURA 0x0C)"
if [ "$B_SPEGNIMENTO" != si ]; then
	inf "⚠ SKIPPED: the target «$B_NOME» has no shutdown"
	inf "  path, and its reasons that can be provoked are SEVEN.  ⛔ This is not"
	inf "  a missing case: it is a case that does not exist on this server, and"
	inf "  the exclusion was MEASURED by the bench with grep, not by me with a comment"
elif [ -n "$FILTRO" ]; then
	inf "⚠ SKIPPED: partial run (filter «$FILTRO»)"
else
	fermare
	inf "the server is restarted: the previous one has already measured, and this"
	inf "case will shut it down"
	if bersaglio_accendi spegnimento "$B_IDLE_LUNGO"; then
		PID=$B_PID
		bersaglio_impronta || { ko "⛔ it is not the declared target"; ESITO=6; }
		if [ "${ESITO:-0}" -ne 6 ]; then
			OPZ2=$(bersaglio_opzioni_python)
			bash "$ENTRA" --root "python3 -u $DENTRO/01-b7-congedo.py \
				--indirizzo $IND $OPZ2 --utente $UTENTE --parola-file $PAROLA_DENTRO \
				--registro $B_LOG --pagina $DENTRO/01-b11-pagina.html \
				--dentro $DENTRO_SORG --pid-server $PID \
				--solo server-in-chiusura"
			ESITO_SPEGN=$?
			# ⛔ AND HERE THE SERVER MUST BE DEAD, not alive: it is the only point
			#    of the bench where B0.5 is read backwards.  ⚠ A server still
			#    alive after a SIGTERM is not «resilient»: it is a server that did
			#    not run the path being measured.
			#
			# ⛔⭐ BUT IT IS GIVEN THE TIME IT ITSELF DECLARES — 11 Aug 2026.
			#
			#     This line looked at `/proc/$PID` IMMEDIATELY, and until today it
			#     was right by accident: the server gave up after three tenths of
			#     a second.  ⛔ With the defect of §3.1 point 3 cured, `src/main.c`
			#     now waits up to **4 s** for the closing capsule to really go
			#     out — and this bench declared dead a server that was doing
			#     exactly the thing the case exists to prove.
			#
			# ⚠ The wait is BOUNDED and declared: 8 s, that is the server's budget
			#   plus twice the margin.  A bottomless wait would turn «it never
			#   dies» into «the bench froze».
			ATTESO_MORTE=8
			for _ in $(seq $((ATTESO_MORTE * 10))); do
				[ -d "/proc/$PID" ] || break
				sleep 0.1
			done
			if [ -d "/proc/$PID" ]; then
				ko "⛔ the server is STILL ALIVE after the SIGTERM: the shutdown"
				ko "   path of src/main.c was not run, and the"
				ko "   0x0C farewell the bench did (or did not) read does not come"
				ko "   from there.  ⚠ It is not a green: it is a measurement to redo"
				ESITO_SPEGN=1
				bersaglio_spegni
			else
				ok "the server disappeared after the SIGTERM, as it must"
				B_PID=""
			fi
			if [ "$ESITO_SPEGN" -ne 0 ] && [ "${ESITO:-0}" -eq 0 ]; then
				ESITO=$ESITO_SPEGN
			fi
		fi
	else
		ko "⛔ the server does not restart: the shutdown run was NOT"
		ko "   done, and this is not «passed»"
		[ "${ESITO:-0}" -eq 0 ] && ESITO=4
	fi
fi

# ---------------------------------------------------------------------------
# ⛔ 8. THE MACHINE IS PUT BACK IN ORDER, AND IT IS DECLARED — B0.3.
#    B7 fails one attempt: alone it does not ban, but the residue is removed and
#    it is said which of the three outcomes arrived.  ⚠ Here the expected is
#    «NON-BANNATO»: a «TOLTO» would mean something made three failures, and it
#    would be news about the initial state, not a clean-up.
log "8. The final unblock, declared (B0.3)"
if [ -n "${B_PID:-}" ]; then
	inf "⚠ expected «NON-BANNATO»: B7 fails ONE attempt out of three, and alone"
	inf "  it does not ban.  A «TOLTO» here would be news about the initial state"
	bersaglio_sblocca dopo-b7 "$IND" || \
		ko "⚠ the final unblock did not go through: look at the line above"
else
	# ⛔ And this is NOT «unblocked»: it is «I talked to nobody», which is the
	#    third outcome of `01-b8-sblocca.py` and the most important of the three.
	inf "⚠ NO UNBLOCK: the server is already off (the shutdown run turned it"
	inf "  off), so the command has nobody to talk to."
	inf "  ⛔ The ban stays as it was in the file «$B_BAN», which is B7's only and"
	inf "     is thrown away at the next run: no other bench reads it"
fi

fermare

log "Outcome"
# ⛔ FOUR OUTCOMES, NOT TWO.  `01-b7-congedo.py` exits 2 when the filter selected
#    nothing, and 3 when the TOOL did not certify itself: an uncertified bench
#    is not a server red, and it is the only way not to pass off a bench defect
#    as a product defect.
case "$ESITO" in
0)
	if [ -n "$FILTRO" ]; then
		ok "⭐ the cases «$FILTRO» pass against «$B_NOME»"
		inf "⚠ and this is NOT «B7 passes»: the run was partial"
	else
		ok "⭐ B7 passes against «$B_NOME» — $( [ "$B_SPEGNIMENTO" = si ] \
			&& printf 'EIGHT reasons that can be provoked' || printf 'SEVEN reasons that can be provoked' )"
		inf "⚠ and it is not «B7 passes»: the other target is another program,"
		inf "  with a different denominator, and this run says nothing about it"
	fi
	;;
2) ko "⛔ B7: there was nothing to measure (filter «$FILTRO»)" ;;
3)
	ko "⛔ B7 DID NOT MEASURE: the tool did not certify itself"
	ko "   ⚠ this is NOT a server red: it is the bench that"
	ko "     stopped before producing a number it does not answer for"
	;;
6) ko "⛔ B7: I DID NOT MEASURE — the target is not the declared one"
   ko "   ⚠ it is not a server red: it is the bench that stopped before"
   ko "     attributing numbers to the wrong program" ;;
*) ko "⛔ B7: something does not pass against «$B_NOME»" ;;
esac
inf "the full log stays in $B_LOG_FUORI"
exit "$ESITO"
