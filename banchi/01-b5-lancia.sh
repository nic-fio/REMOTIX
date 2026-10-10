#!/bin/bash
#
# 01-b5-lancia.sh — runs ON THE SERVER.  B5: the violation tests.
#
#   BERSAGLIO=innesto  bash /media/REMOTIX/src/01-b5-lancia.sh            everything
#   BERSAGLIO=prodotto bash /media/REMOTIX/src/01-b5-lancia.sh solo tela  one piece only
#   BERSAGLIO=innesto  bash /media/REMOTIX/src/01-b5-lancia.sh elenco     the predictions
#
# ⛔ `BERSAGLIO` IS MANDATORY — see `01-b0-bersaglio.sh`, which is the only
#    place where the two servers are described.
#
# ---------------------------------------------------------------------------
# ⛔ WHAT CHANGES WHEN B5 IS POINTED AT THE PRODUCT — the prediction, written BEFORE
#
# | what | graft | product | why |
# |---|---|---|---|
# | the reasons on the wire (`ERRORE_PROTOCOLLO`, `NIENTE_IN_COMUNE`, …) | same | same | ⭐ they are decided by `rcp.c`, which is **identical byte for byte** in the two servers (md5 `cb7af778…`) |
# | the codec choice and the discard in the log (§4.3) | present | present | same lines, same `rcp.c` |
# | `0x01` input and `0x02` clipboard on a unidirectional stream | «violation» | ⭐ **lawful**, the session stays alive | `src/webtransport.c` `smista_uni()`: *«in the graft both were marked as violations, and a compliant client that opened the input channel saw EVERY byte discarded forever»*.  ⚠ B5 today **does not test them**: it is a hole, not an expected difference |
# | the **echo** on the streams opened by the bench | present (30 bytes, it is B2's «byte that comes back») | ⛔ **NOT present** | `src/webtransport.c` `scarta_stream_di_troppo()`: *«the bytes are thrown away, and NOT sent back»*.  ⚠ No tool must **wait** for it: whoever does stays hanging, and it is the red that on 10 August was diagnosed for hours as a certificate defect |
# | the inactivity cap | 120 s, requested by us | ⛔ **30 s, not chosen by us** | `IDLE_MS` in `src/trasporto.c`, and no option touches it.  The B5 cases wait at most 12 s: they fit, but the margin goes from 108 s to 18 s |
# | the summary line «REMOTIX B3\|B5» | present | ⛔ not present | the product writes `HH:MM:SS.mmm <area>`: the target's fingerprint is counted, not the graft's |
# | the limiter (7 failed) | bans in memory, dies with the process | bans **on file** | the ban file is per bench and is thrown away at the start, and at the end it is unblocked **declaring it** (B0.3) |
#
# ⛔ WITH A FILTER THE RUN IS PARTIAL, AND IT SAYS SO.  The measurements that do not
#    depend on the selected cases — the path, the full run, the limiter, and the
#    two log lines of §4.3 — are NOT run, and the green outcome reads
#    «the selected cases pass», never «B5 passes».  ⚠ And a filter that
#    matches no name exits **2**, not 0: «I have nothing to measure»
#    is not «everything passed» (finding R7.15).
#
# ---------------------------------------------------------------------------
# ⛔ WHAT IT TESTS, AND THE HALF THAT GETS FORGOTTEN
#
# `RCP.md` §3 is the strictness rule: what is not understood is not ignored, the
# connection drops, with the reason.  ⭐ But **a strictness rule is not tested
# by doing the right things**: a server that checks nothing passes all the
# B3 runs and falls the day someone sends it a crooked byte.
#
# ⛔ And after every violation it is checked that **the server is still there**
#    (B0.5).  A server killed by the kernel «drops the connection» exactly
#    like one that says farewell — and it takes away **everyone else's sessions**.
#
# ---------------------------------------------------------------------------
# ⛔ AND THE SERVER LOG IS LOOKED AT, BUT IT IS NOT THE ARBITER
#
# The reason is verified by **the receiving side** (§8.1): the server log is
# the same hand that wrote the code.  ⚠ Two things however exist ONLY in the
# log, because §4.3 requires them there: the **codec choice** and the **discard**
# of the unknown entries.  Those are read over there, and it is declared.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⛔ The target: a single shape for the four benches, in a single file.
SIGLA=b5
# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"
IND=$B_IND
PORTA=$B_PORTA

AZIONE=${1:-tutto}
FILTRO=${2:-}

log "Credentials for the container"
bash "$ENTRA" --root "true" || { ko "cannot enter the container"; exit 2; }
ok "sudo validated"

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b5-violazioni.py --bersaglio $B_NOME --elenco"
	exit 0
fi

bersaglio_dichiara

# ---------------------------------------------------------------------------
# ⛔ 1. THE SERVER IS PREPARED — and the two roads are not the same.
#
#   innesto   the grafts are removed and put back, the mark is counted in the
#             sources and it is compiled looking at the builder's outcome;
#   prodotto  ⛔ it is NOT recompiled: `src/` does not belong to this bench, and a
#             bench that recompiles what it measures removes its own independent
#             witness.  It is only verified that the binary is there and is newer
#             than every source — `[M]` 11 Aug 2026, the product binary was an
#             hour older than `trasporto.c`, and the log of the last start
#             carried a wording from two generations before.
#
# ⚠ And in both cases the **md5 fingerprint of the binary** is taken, which ends
#   up in this run's log: it is the only way to know, six hours later, whether two
#   runs measured the same program.
#
# ⛔ NO REDIRECTION AROUND `enter.sh` — it would take away the sudo password
#    prompt, and the script would stay waiting for a question that nobody
#    sees.  It happened again on 10 Aug 2026 on THIS file, four runs after the
#    lesson had been written.  The redirections go inside the quotes of the
#    remote command (see `01-b0-bersaglio.sh`).
bersaglio_pronto || exit 3

# ---------------------------------------------------------------------------
# ⛔ 2. THE INITIAL STATE OF THE BAN — B0.1 and B0.2.
#
# B5 does **seven failed authentications in a row** (`limitatore()`), so it
# bans itself: it is intended, and it is what the per-address counter tests.
# ⛔ But the product's ban is on FILE, and a ban from yesterday would turn red
#    everything that follows with the red on the wrong defendant.  The file
#    belongs to this bench only — `01-b0-bersaglio.sh` gives one per bench and
#    per target — and it is thrown away here.
log "2. The initial state of the ban (B0.1, B0.2)"
bersaglio_butta_il_ban
inf "⚠ and this bench does 7 FAILED authentications in a row: it bans itself,"
inf "  and it is the thing it tests.  The unblock is at the end, declared (B0.3)"

# ---------------------------------------------------------------------------
log "3. The server starts"
inf "⚠ the inactivity cap is \$B_IDLE_LUNGO = $B_IDLE_LUNGO ms: some cases"
inf "  wait up to twelve seconds to be sure that the farewell does NOT"
inf "  arrive, and a shorter cap would close the connection on its own —"
inf "  the bench would read «it dropped» where nothing dropped (R3.19)"
if [ "$B_IDLE_SCELTA" = no ]; then
	inf "⛔ and on this target we do NOT choose that number: it is IDLE_MS"
	inf "   in src/trasporto.c.  The margin above the 12 s goes from 108 s to 18 s"
fi
bersaglio_accendi filo "$B_IDLE_LUNGO" || exit 4
PID=$B_PID

# ⛔ AND THE UNBLOCK COMMAND MUST BE ALIVE **BEFORE**, not at the end: the `PING`
#    is the denominator of B0.3.  Without it, «the ban did not trigger» and «the
#    unblock never reached anyone» look the same again — and one would find out
#    at the end, with the measurements done.
inf "does the unblock command answer? (PING — the denominator of B0.3)"
bersaglio_ping || { ko "⛔ the unblock command does not answer: at the end I could not"
                    ko "   put the machine back in order, and I would notice"
                    ko "   with the measurements done.  I stop now."
                    bersaglio_spegni; exit 4; }

fermare() { bersaglio_spegni; }

# ---------------------------------------------------------------------------
# ⛔ 3-bis. DID I MEASURE THE SERVER I DECLARED? — and the server log is asked,
#    not the command line I wrote myself.
log "3-bis. The target's fingerprint (LEZIONI.md §1.9, corollary 5)"
bersaglio_impronta
case $? in
0) : ;;
1) ko "⛔ I stop: the numbers would end up on the wrong target"; fermare; exit 6 ;;
*) ko "⛔ I stop: I do not know what I am about to measure"; fermare; exit 6 ;;
esac

# ---------------------------------------------------------------------------
log "4. The violations"
OPZ=$(bersaglio_opzioni_python)
if [ -n "$FILTRO" ]; then
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b5-violazioni.py --indirizzo $IND $OPZ --solo $FILTRO"
else
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b5-violazioni.py --indirizzo $IND $OPZ"
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
log "6. The two lines that live only in the log (§4.3)"
inf "the CHOICE of the codec, and the DISCARD of the unknown entries"
#
# ⛔ TWO CHECKS THAT USED TO ALWAYS RUN, AND GAVE RED ON A RULE THAT NOBODY
#    HAD ASKED THE SERVER TO APPLY.
#
#    The discard of `vp9` is triggered by two cases only — `hevc-e-vp9` and
#    `capacita-sconosciuta`.  With `01-b5-lancia.sh solo tela` those cases do
#    not run, the `grep` finds nothing, and the bench accused the server of not
#    having written a line that nobody had given it the chance to write.
#    It is exactly the defect this same script declares it fears for the
#    graft, twenty lines further up (finding R7.15).
#
# ⛔ And `grep -q` on a file that is NOT THERE exits 2, not 1: «the line is
#    missing» and «the log cannot be read» ended up in the same `else` branch,
#    that is form E8.  The file is looked at first, and it is said which of the
#    two things happened.
riga_nel_registro() {   # $1 = searched pattern, $2 = sentence if absent
	if [ ! -f "$B_LOG_FUORI" ]; then
		ko "⛔ THE LOG CANNOT BE READ: $B_LOG_FUORI does not exist"
		ko "   it is not the server that did not write — it is that it cannot be read."
		ko "   (volume not mapped? server never started? name changed?)"
		ESITO=1
		return
	fi
	if grep -q "$1" "$B_LOG_FUORI"; then
		ok "present:"
		grep -m2 "$1" "$B_LOG_FUORI" | sed 's/^/        /'
	else
		ko "$2"
		ESITO=1
	fi
}

if [ -n "$FILTRO" ]; then
	inf "⚠ SKIPPED: filter «$FILTRO» active.  These two lines are produced by"
	inf "  the cases hevc-e-vp9 and capacita-sconosciuta, which may not"
	inf "  have been selected: a red here would be a red on a"
	inf "  rule the server never had the chance to apply"
else
	riga_nel_registro "negoziato video.codec=hevc" \
		"⛔ the codec choice is NOT in the log: §4.3 requires it"
	riga_nel_registro "discarded unknown entries" \
		"⛔ the discard of vp9 is NOT in the log: a successful negotiation with the opposite of what was wanted inside it is seen only if someone writes it (trap 4 of LEZIONI.md §4)"
fi

log "7. And what the server wrote, in short"
if [ -f "$B_LOG_FUORI" ]; then
	# ⛔ The TARGET's fingerprint is counted, not the graft's: the
	#    product does not write «REMOTIX B3» on any line, and a count of
	#    zero would be read as «the server wrote nothing».
	grep -cE "$B_IMPRONTA" "$B_LOG_FUORI" \
		| sed 's/^/        log lines (target fingerprint): /'
	grep "congedo motivo" "$B_LOG_FUORI" | tail -5 | sed 's/^/        /'
else
	inf "⛔ no log to summarise: the file is not there"
fi

# ---------------------------------------------------------------------------
# ⛔ 8. THE MACHINE IS PUT BACK IN ORDER, AND IT IS DECLARED — rule B0.3.
#
# ⛔ The unblock is HERE and nowhere else: inside the run it would make the
#    limiter pass by construction — «an unblock called inside the run makes
#    everything else pass» — and B5 tests the limiter.
#
# ⚠ And it is declared which of the THREE outcomes arrived.  `TOLTO` means the
#   ban really was there, that is the limiter worked: it is an independent
#   confirmation, read from the HOST's side instead of from the wire.
#   `NON-BANNATO` after seven failures would be news, not a clean-up.
#   «I talked to nobody» is neither one nor the other.
log "8. The final unblock, declared (B0.3)"
inf "⛔ never before: inside the run it would make the limiter pass by construction"
inf "⚠ expected «TOLTO» on the bench's address: after seven failures the ban"
inf "  is there, and a «NON-BANNATO» here would be news about the limiter, not a"
inf "  successful clean-up"
bersaglio_sblocca dopo-b5 "$IND" || {
	ko "⚠ the final unblock did not go through: the address may stay out"
	ko "  for twelve hours on the ban file of THIS bench ($B_BAN)"
	ko "  — not on the others', which have one each"
}

fermare

log "Outcome"
# ⛔ THREE OUTCOMES, NOT TWO.  `01-b5-violazioni.py` exits 2 when the filter
#    selected no case: «I have nothing to measure» is not «passes», and a typo
#    in the filter must not have the colour of green.
if [ "$ESITO" -eq 2 ]; then
	ko "⛔ B5: there was nothing to measure (filter «$FILTRO»)"
elif [ "$ESITO" -eq 0 ]; then
	if [ -n "$FILTRO" ]; then
		ok "⭐ the cases «$FILTRO» pass against «$B_NOME»"
		inf "⚠ and this is NOT «B5 passes»: the run was partial"
	else
		ok "⭐ B5 passes against «$B_NOME»"
		inf "⚠ and it is not «B5 passes»: it is «B5 passes against $B_NOME».  The other"
		inf "  target is another program, and this run says nothing about it"
	fi
elif [ "$ESITO" -eq 6 ]; then
	ko "⛔ B5: I DID NOT MEASURE — the target is not the declared one"
	ko "   ⚠ this is not a red of the server: it is the bench that stopped"
	ko "     before attributing numbers to the wrong program"
else
	ko "⛔ B5: something does not pass against «$B_NOME»"
fi
inf "the full log stays in $B_LOG_FUORI"
exit "$ESITO"
