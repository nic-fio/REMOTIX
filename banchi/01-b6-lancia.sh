#!/bin/bash
#
# 01-b6-lancia.sh — runs ON THE SERVER.  B6: the three caps of the handshake.
#
#   BERSAGLIO=innesto  bash .../01-b6-lancia.sh          everything (two phases)
#   BERSAGLIO=prodotto bash .../01-b6-lancia.sh sani     only the «sani» phase
#   BERSAGLIO=prodotto bash .../01-b6-lancia.sh ping     only the «ping» phase
#   BERSAGLIO=innesto  bash .../01-b6-lancia.sh elenco   the predictions
#
# ⛔ `BERSAGLIO` IS MANDATORY — see `01-b0-bersaglio.sh`.
#
# ---------------------------------------------------------------------------
# ⛔⭐ WHAT CHANGES WHEN B6 IS POINTED AT THE PRODUCT — the prediction, written BEFORE
#
# | what | graft | product | why |
# |---|---|---|---|
# | the three caps (5 · 60 · 10 s) | same | same | they are the `#define TETTO_*` of `rcp.c`, **identical byte for byte** in the two servers |
# | ⛔ **the TRANSPORT cap** | chosen: 120 s / 15 s | ⛔ **30 s fixed** | `#define IDLE_MS 30000` in `src/trasporto.c`, and no option touches it (no `getenv` in all of `src/`) |
# | ⛔ **the two phases** | independent | ⛔ **NOT independent** | 30 s is below the 60 s of the credentials: `credenziali-tetto` (sani) and `credenziali-tetto-sotto-il-trasporto` (ping) measure THE SAME THING.  ⚠ CIAO (5 s) and ATTACCA (10 s) stay clean — 30 > 10.  ⛔ Counting them as two confirmations would be counting the same measurement twice |
# | `cert-morte-silenziosa` | dies at 15 s | dies at **30 s** | it is the transport cap, read from the peer |
# | `credenziali-presto` (silent for 42 s) | passes under a 120 s cap | ⭐ passes **only if the PINGs are there** | 42 s > 30 s: on the product this case becomes a **second test of the PINGs**, for free, and it is a gain — not a loss |
# | the stopwatch of the first cap | armed from the opening of the channel | same | `src/webtransport.c` `rcp_avvia()` arms `regola_battito()` on the same line as `rcp_apri()`.  ⚠ The comment says *«in the graft this was missing»*: if `ciao-tetto` gave «nothing» on the graft and 5 s on the product, the difference is **this**, not §4.6 |
# | `ciao-senza-controllo` (R3.27, second answer) | stays hanging up to 120 s | ⚠ dies at **30 s** — from INACTIVITY, not from a cap | it is the same «there is no cap», with a shorter QUIC time on top.  ⛔ The bench must read it as `morte-silenziosa`, not as «cap expired»: R3.27 stays OPEN on both targets |
# | the ban | lives in the process, dies with the restart | ⛔ lives **on file** | restarting is no longer enough (I7): B6's ban file is thrown away at the start, and unblocked BEFORE the run, declaring it |
# | the log | ⛔ **did not exist** | ⛔ **did not exist** | ⚠ the three numbers of 10 August — 5.0 · 60.1 · 10.0 s — cannot be re-verified by anyone.  From this run there is `b6-esiti-<bersaglio>.jsonl` |
#
# ⛔ WITH A FILTER THE RUN IS PARTIAL, AND IT SAYS SO.  The «sani» phase measures the
#    three caps; the «ping» phase measures **the cure of §4.6**, that is that the
#    server keeps the connection alive with the transport PINGs.  A green on only
#    one of the two reads «that half passes», never «B6 passes».
#
# ---------------------------------------------------------------------------
# ⛔ WHAT IT MEASURES, IN ONE USER'S LINE
#
# *«How long it takes to tell you it did not make it, instead of staying there
# hanging.»*  `RCP.md` §4.6 puts three caps on the handshake — 5 s on the
# `CIAO`, 60 s on the `CREDENZIALI`, 10 s on the `ATTACCA` — and once a cap has
# expired the server MUST take leave with `TEMPO_SCADUTO` `0x0D`, by the two
# roads of §3.1.
#
# ⛔ **Not before, not after, and with the right reason**: the bench tests all
#    three things, and «not before» is the half nobody writes (see the
#    `-presto` cases in `01-b6-tetti.py`).
#
# ---------------------------------------------------------------------------
# ⛔ WHY TWO PHASES, AND WHY THE SECOND IS THE ONE THAT TESTS SOMETHING
#
# `RCP.md` §4.6, box of finding R1.8: the 60 seconds of the password were
# **unreachable**, because while the user types nothing passes on the wire and
# at the thirtieth second QUIC's idle timeout triggers — the connection dies
# **silently, without a reason**, before the 60 s cap can expire.  The cure is
# the server's: the **transport PINGs**.
#
#   «sani» phase  the transport cap is raised to **120 s**, above all three
#                 protocol caps: here the three numbers read clean, because
#                 only RCP can be the one closing.
#                 ⚠ But with 120 s **even a server that sends no PING** would
#                 give 60 s: this phase alone would bless the violation that
#                 §4.6 exists to cure — `LEZIONI.md` §1.3, and it is the same
#                 shape as finding R3.19 on B3.
#
#   «ping» phase  ⭐ the transport cap is brought **BELOW** the protocol cap:
#                 `TETTO_PING`, that is 15 s against 60.  If the PINGs are
#                 there, `TEMPO_SCADUTO` arrives **all the same at 60 s**, after
#                 having crossed the transport cap four times.  If they are
#                 not, the connection dies around 15 s **without a reason** —
#                 the signature §4.6 describes, with a number that cannot be
#                 confused with any of the three caps.
#
# ⛔ AND THE TRANSPORT CAP IS READ FROM THE PEER, NOT TAKEN AS SET — it is
#    finding R8.3, paid for on `01-b3-quarto-giro.sh`: until 10 Aug 2026 the
#    premise was written in a comment and nobody started the server with the
#    option.  Here B2's probe asks the wire for it before every phase, and if it
#    is not the expected number **the phase does not start**.
#
# ---------------------------------------------------------------------------
# ⛔ THE THREE NUMBERS THIS BENCH COMPARES, AND THE DATED FACT
#
#   the DOCUMENT   `RCP.md` §4.6 — written by hand in `01-b6-tetti.py`;
#   the CODE       the `#define TETTO_*`, read below **from the copy that was
#                  compiled** (`examples/rcp.c`) and compared with the source
#                  (`rcp/rcp.c`), because a stale copy would give a number
#                  that is not in the binary;
#   the MEASUREMENT  what arrives on the wire.
#
# ⛔ On 10 Aug 2026, finding R9.9, `TETTO_ATTACCA` was brought from
#    **60 000 to 10 000 ms** on the sole reading of §4.6, **without anybody
#    measuring it**, and the comment in the code declares it: *«no bench saw
#    it: B6 is not written yet»*.  ⭐ This bench is the first witness of that
#    number.  If document and code do not agree it says so, and does not adapt
#    to either of the two.
#
# ---------------------------------------------------------------------------
# ⛔ AND THE SERVER LOG IS LOOKED AT, BUT IT IS NOT THE ARBITER
#
# The reason is verified by **the receiving side** (§8.1): the server log is
# the same hand that wrote the code.  The lines «scaduto il tetto per …» are
# printed at the end as a **diagnosis**, and it is declared.
#
# ---------------------------------------------------------------------------
# ⛔ THE INITIAL STATE (B0.1, B0.2, B0.3)
#
#  · the server is **rebuilt and restarted** at every phase: it is also the only
#    way to reset the two counters of §4.4-bis and the session registry.
#    ⚠ `rcp_azzera_registro_sessioni()` exists in `rcp.c` **but has no grafted
#      caller**: it cannot be called from outside, and whoever reads the line
#      in `rcp.h` believes the bench uses it.  It does not: it restarts;
#  · the source address is the same as all the other benches, and since 10
#    Aug 2026 the count of §4.4-bis is **a single one, on the address only**,
#    and leads to a **twelve-hour ban** (B0.3).  ⚠ The old line said «per name
#    and per address», and it was the previous shape.  The first check of
#    `01-b6-tetti.py` is a whole handshake: if `TROPPI_TENTATIVI` comes back,
#    the bench **stops with exit 5** and says the ban belongs to another bench,
#    instead of giving red to the caps.
#
# ⭐ AND THE DECLARATION THAT B0.3 DEMANDS, BECAUSE «it did not trigger» AND
#    «someone removed it» LOOK THE SAME:
#
#      ⛔ **B6 does not call the unblock command, and says why.**  The command
#         exists — `01-b8-sblocca.py`, which talks to the server on a command
#         socket (`--comando-socket`) — but it wants a server **started with
#         that option**, and B6 starts its own without it.  ⭐ The cure B6 uses
#         is stronger: **it restarts the server at every phase**, and the count
#         of §4.4-bis lives in the process, so it starts again from zero.
#         ⚠ *Until tonight this line said the command «does not exist».  It was
#         true when it was written and stopped being so within an hour: it is
#         form **E5**, a fact that was a deduction never re-verified.*
#
#      ⭐ **And B6 never fails an authentication**: all its cases use the good
#         credentials, or stop before `CREDENZIALI`.  So it **does not consume
#         the count** and does not leave a ban on the benches that come after.
#         It is the only way this bench has to respect B0.3 without a cure that
#         does not exist.
#
# ---------------------------------------------------------------------------
# ⛔ NO REDIRECTION AROUND `enter.sh`
#
#    `bash enter.sh --root "..." > file 2>&1` takes away **the sudo password
#    prompt**, and the script stays waiting for a question nobody sees.
#    ⚠ It is not `>/dev/null`: it is **any** redirection around `enter.sh`
#    (10 Aug 2026, on `01-b5-lancia.sh`).  The redirections go INSIDE the
#    quotes of the remote command.
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
PAROLA_FUORI=$FUORI/tmp/b6-parola
PAROLA_DENTRO=$DENTRO/tmp/b6-parola

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
SIGLA=b6

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# shellcheck source=01-b0-bersaglio.sh
. "$FUORI/01-b0-bersaglio.sh"
IND=$B_IND
PORTA=$B_PORTA
# ⛔ The two transport caps come from the PROFILE, not from here.  On the graft
#    they are 120 000 and 15 000 ms; on the product they are both 30 000,
#    because `IDLE_MS` does not move — and when they coincide the two phases are
#    NOT independent, and the bench declares it instead of counting them twice.
TETTO_SANI=$B_IDLE_LUNGO
TETTO_PING=$B_IDLE_CORTO

AZIONE=${1:-tutto}
case "$AZIONE" in
	tutto|sani|ping|elenco) ;;
	*) ko "unknown action: $AZIONE  (tutto | sani | ping | elenco)"; exit 2 ;;
esac

log "Credentials for the container"
bash "$ENTRA" --root "true" || { ko "cannot enter the container"; exit 2; }
ok "sudo validated"

# ---------------------------------------------------------------------------
# ⛔ THE SENTINEL: «empty» is not «zero» — findings R12-A.7 and R12-A.23, and the
#    cure was already written in the same folder, in `01-b11-guasto.sh:92-129`.
#
# `CHI=$(bash "$ENTRA" --root "ss -ulnp | grep ':$PORTA '")` said «port free»
# in three opposite cases: the port really is free · `ss` is not in the
# container · `enter.sh` did not run the command.  ⛔ And here the aggravating
# factor was that that reading happened **only once, at the start**: B6 was
# the only one of the four benches not to recheck the port between the two
# phases.
#
# ⭐ The remote command prints its own exit status by itself, and on top there
#    is the positive control of the tool: `ss` always prints at least its own
#    header, and if it prints nothing it has looked at nothing.
# ⚠ Command substitution is lawful from here on and not before: the line
#   `--root "true"` above is the one that takes the password prompt.  The ban
#   at the top of this file concerns the REDIRECTIONS around `enter.sh`, which
#   would take that question away.
USCITA=""
dentro() # $1 = remote command.  Output in $USCITA, status = the command's
{
	local tutto stato
	tutto=$(bash "$ENTRA" --root "$1"'; printf "\nB6-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B6-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	USCITA=$(printf '%s\n' "$tutto" | grep -v '^B6-FINE=')
	if [ -z "$stato" ]; then
		return 125   # it did not get to the end: it is not a zero
	fi
	return "$stato"
}

# Who holds the UDP port.  0 = taken (the lines in $CHI) · 1 = free ·
# 2 = unknown, and ⛔ «unknown» is not rounded to «free».
CHI=""
chi_tiene_la_porta()
{
	local st
	dentro "ss -ulnp"
	st=$?
	if [ "$st" -ne 0 ]; then
		ko "⛔ «ss -ulnp» did not answer inside the container (exit $st):"
		printf '%s\n' "$USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	if [ -z "$USCITA" ]; then
		ko "⛔ «ss -ulnp» printed NOTHING, not even the header:"
		ko "   the tool is mute, and its silence is not a free port"
		return 2
	fi
	CHI=$(printf '%s\n' "$USCITA" | grep ":$PORTA ")
	[ -n "$CHI" ]
}

if [ "$AZIONE" = elenco ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b6-tetti.py --bersaglio $B_NOME --elenco"
	exit 0
fi

# ---------------------------------------------------------------------------
# ⛔ 1. THE SERVER IS PREPARED — and the two roads are not the same (see
#    `01-b0-bersaglio.sh`).  ⚠ On the graft the piece that counts is the one that
#    makes TIME FLOW: without `rcp_tempo()` in the write path no cap ever
#    expires, and B6 would print three reds against an intact module.
#    On the product that piece is `wt_battito_ns()`/`wt_batti()`, which the
#    `main.c` loop always calls: there is no graft that could be missing.
bersaglio_pronto || exit 3

if [ "$B_NOME" = innesto ]; then
	SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
	QUANTI=$(bash "$ENTRA" --root "grep -c 'rcp_tempo(rcp_' $SORG" | tr -cd '0-9')
	if [ "${QUANTI:-0}" -ge 1 ]; then
		ok "the call to rcp_tempo() is in the source ($QUANTI)"
	else
		ko "⛔ the call to rcp_tempo() is NOT in the source: RCP's time"
		ko "   would not flow, no cap would expire, and the three reds"
		ko "   would be the bench's"
		exit 3
	fi
else
	# ⭐ The equivalent check on the product, and it is MEASURED like the other.
	QUANTI=$(bash "$ENTRA" --root "grep -c 'wt_batti(' $DENTRO/remotix/trasporto.c" | tr -cd '0-9')
	if [ "${QUANTI:-0}" -ge 1 ]; then
		ok "the product loop calls wt_batti() ($QUANTI): RCP's time flows"
	else
		ko "⛔ `wt_batti()` does not appear in trasporto.c: without it, RCP's"
		ko "   clock does not advance and no cap of §4.6 ever expires.  The three reds"
		ko "   would be the bench's, not §4.6's"
		exit 3
	fi
fi

# ---------------------------------------------------------------------------
# ⛔ 1-bis. THE INITIAL STATE OF THE BAN — B0.1, B0.2, B0.3.
#
# ⭐ B6 NEVER fails an authentication: all its cases use the good credentials
#    or stop before `CREDENZIALI`.  So it does not consume the count and does
#    not leave a ban on whoever comes after.
# ⛔ But it can FIND one: the product's ban is on file and survives the restart
#    (I7), so «restarting the server» — which was B6's cure — is no longer
#    enough.  B6's ban file is its own only, and it is thrown away here.
log "1-bis. The initial state of the ban (B0.1, B0.2, B0.3)"
bersaglio_butta_il_ban
inf "⭐ and B6 never fails an authentication: it does not consume the count, and"
inf "   leaves a ban on nobody"

# ⛔ THE CAPS WRITTEN IN THE CODE, READ FROM THE COPY THAT GETS COMPILED.
#
#    `01-b3-rcp-innesta.py` COPIES `rcp/rcp.c` into `examples/`: it is that copy
#    that ends up in the binary.  Reading only the source would give a number
#    that might not be in the running server — it is the same shape as the old
#    build log (E8: «old» and «absent» look the same).  Here both are read and
#    they are required to match.
#
# ⛔ And «I could not read» is not «zero»: if the `grep` does not find the line
#    it is declared, and the document/code comparison **is not done** instead of
#    being done with an invented number.
leggi_tetto() # $1 = file, $2 = name of the define
{
	local f=$1 n=$2 v=""
	[ -r "$f" ] || return 1
	v=$(grep -E "^#define[[:space:]]+$n[[:space:]]+[0-9]+" "$f" \
		| head -1 | awk '{print $3}')
	[ -n "$v" ] || return 1
	printf '%s' "$v"
}

log "2. The caps written in the CODE — and the number changed on 10 August"
# ⛔ THE TWO FILES DEPEND ON THE TARGET, and the comparison is the same.
#
#   innesto   `01-b3-rcp-innesta.py` COPIES `rcp/rcp.c` into `examples/`: it is
#             that copy that ends up in the binary, and reading only the source
#             would give a number that might not be in the running server.
#   prodotto  ⭐ there is no copy: the Makefile compiles `src/rcp.c` in
#             place.  ⚠ The comparison is done anyway, between `src/rcp.c` and
#             `banchi/rcp/rcp.c` — which MUST stay identical byte for byte
#             (md5 `cb7af778…`): the day they diverged, the benches and the
#             product would measure two different protocols with the same name.
if [ "$B_NOME" = innesto ]; then
	SORGENTE_RCP=$FUORI/rcp/rcp.c
	COMPILATO_RCP=$FUORI/b2/ngtcp2/examples/rcp.c
else
	SORGENTE_RCP=$FUORI/rcp/rcp.c
	COMPILATO_RCP=$FUORI/remotix/rcp.c
fi
TETTI_CODICE=""
LETTURA_OK=si
for coppia in "CIAO:TETTO_CIAO" "CREDENZIALI:TETTO_CREDENZIALI" "ATTACCA:TETTO_ATTACCA"; do
	NOME=${coppia%%:*}
	DEF=${coppia##*:}
	A=$(leggi_tetto "$SORGENTE_RCP" "$DEF") || A=""
	B=$(leggi_tetto "$COMPILATO_RCP" "$DEF") || B=""
	if [ -z "$A" ] || [ -z "$B" ]; then
		ko "⛔ $DEF cannot be read (source «${A:-—}», compiled copy «${B:-—}»)"
		ko "   It is not «it is zero»: it is that it could not be looked at."
		LETTURA_OK=no
		continue
	fi
	if [ "$A" != "$B" ]; then
		ko "⛔ $DEF: «$SORGENTE_RCP» says $A and «$COMPILATO_RCP» says $B"
		if [ "$B_NOME" = innesto ]; then
			ko "   The graft did not recopy rcp.c: the binary does not have the"
			ko "   number you believe you changed."
		else
			ko "   ⛔ src/rcp.c and banchi/rcp/rcp.c are NO longer identical: from"
			ko "      here on the benches and the product speak two different"
			ko "      protocols with the same name, and no comparison between the two"
			ko "      targets means anything any more."
		fi
		LETTURA_OK=no
		continue
	fi
	ok "$DEF = $B ms  (source and compiled copy match)"
	TETTI_CODICE="$TETTI_CODICE${TETTI_CODICE:+,}$NOME=$B"
done
if [ "$LETTURA_OK" != si ]; then
	ko "⛔ without the numbers of the code the bench would measure against the"
	ko "   document alone, and the comparison B6 exists to make would not be made"
	exit 3
fi
inf "⚠ TETTO_ATTACCA went from 60 000 to 10 000 ms on 10 Aug 2026"
inf "  (R9.9) on the sole reading of §4.6, without measurement: this run is"
inf "  its first witness"

# ---------------------------------------------------------------------------
# ⛔ THE BUILD LOG IS DELETED BEFORE, not after: if the build does not start at
#    all, a `tail` would show the previous run's log and the diagnosis would
#    start from an error that did not happen today.
rm -f "$FUORI/b6-compila.log"
if ! bash "$ENTRA" --root \
	"ninja -C $DENTRO/b2/ngtcp2/build bsslserver > $DENTRO/b6-compila.log 2>&1"; then
	ko "the build failed:"
	if [ -f "$FUORI/b6-compila.log" ]; then
		tail -25 "$FUORI/b6-compila.log" | sed 's/^/        /'
	else
		ko "   ⛔ and the build log DOES NOT EXIST: it is not ninja that"
		ko "      kept quiet, it is that it never got as far as launching it"
	fi
	exit 3
fi
ok "compiled"

# ---------------------------------------------------------------------------
log "3. The port — `bersaglio_accendi` looks at it, before every start"
inf "⛔ and not only once at the start: between the first phase and the second"
inf "   another server can fit, and «unknown» is not rounded to «free»"

# ---------------------------------------------------------------------------
PID=""

accendi() # $1 = inactivity cap in ms, $2 = label
{
	local tms=$1 et=$2
	# ⛔ The start, the port check and the refusal to start with a cap the
	#    target cannot give all live in `bersaglio_accendi`: a single place for
	#    the two servers.
	bersaglio_accendi "$et" "$tms" || return 1
	PID=$B_PID
	# ⛔ AND RIGHT AWAY THE FINGERPRINT: did I start the server I declared?
	bersaglio_impronta || return 1
	return 0
}

# ⛔ SHUTTING DOWN IS NOT SENDING A `kill` — finding R12-A.24.
#
#    `spegni()` sent the signal and reset `PID` **immediately**; `fase ping`
#    called `accendi` a few milliseconds later, on the same port.  The symptom
#    would have been «the server did not start» at the beginning of the `ping`
#    phase, that is an exit 4 — «the tool is not certified» — on a healthy
#    server: the red pointed at the wrong defendant.
#
# ⭐ The cure was already written, the same night, in `01-c2-lancia.sh:139-155`,
#    and even the why: *«between the death of the process and the release of
#    the port there is an instant that, if one does not wait, makes scene 1
#    measure a port still held»*.  Two hands on the same problem; here the
#    stronger is taken.
# ⛔ `/proc`, not `kill -0`: on a root process `kill -0` from a normal user
#    says «forbidden», which is not «dead».
spegni()
{
	# ⛔ The shutdown lives in `bersaglio_spegni`: it waits for the process to
	#    disappear from `/proc` AND for the port to be freed, which are two
	#    different things (finding R12-A.24).  ⚠ On the product it counts double:
	#    `SIGTERM` is not the end but the START of a path — `main.c` says farewell
	#    to all the sessions with `SERVER_IN_CHIUSURA` and waits up to two
	#    seconds for the bytes to go out.  A bench that demanded immediate death
	#    would read «it does not die» on a server that is doing its job.
	bersaglio_spegni
}

# ⛔ THE CAP IS MEASURED, NOT TAKEN AS SET — finding R8.3.
#    B2's probe takes the transport parameters **where they arrive**, that is
#    from the peer, instead of from the configuration of whoever sends them.
#
# ⛔ AND `--bersaglio` IS MANDATORY — seam broken and repaired on 11 Aug 2026.
#    This line called the probe without telling it against whom it was
#    measuring, while the same day the probe made that argument mandatory and
#    without a default, precisely so that a run could not measure the wrong
#    server by distraction.  Two files, two authors, neither of them wrong
#    alone: it is the «seams» shape of the 10 August review.
# ⭐ And it was seen because the bench REFUSED to measure — «I could not read
#    max_idle_timeout from the peer: the phase does not start» — instead of
#    going on with a missing number.  The branch that tells «empty» from
#    «forbidden» did exactly its job.
# ⚠ Its exit code is not looked at: the probe judges six properties and here
#   only one is of interest.  The NUMBER is read, and «I read nothing» has a
#   branch of its own — «empty» and «forbidden» do not look the same.
tetto_dal_pari() # $1 = expected in ms, $2 = label
{
	local atteso=$1 et=$2 letto=""
	rm -f "$FUORI/b6-$B_NOME-$et-tetto.log"
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-trasporto.py --bersaglio $B_NOME --indirizzo $IND --porta $PORTA --etichetta b6-$et --idle-atteso $atteso > $DENTRO/b6-$B_NOME-$et-tetto.log 2>&1"
	if [ ! -f "$FUORI/b6-$B_NOME-$et-tetto.log" ]; then
		ko "the probe wrote nothing: it could not be looked at"
		return 2
	fi
	letto=$(grep -m1 'max_idle_timeout *=' "$FUORI/b6-$B_NOME-$et-tetto.log" | tr -dc '0-9')
	if [ -z "$letto" ]; then
		ko "I could not read max_idle_timeout from the peer: the phase does not start"
		ko "   (without the cap one does not know who will close — R8.3)"
		tail -6 "$FUORI/b6-$B_NOME-$et-tetto.log" | sed 's/^/        /'
		return 2
	fi
	if [ "$letto" -ne "$atteso" ]; then
		ko "⛔ the inactivity cap on the wire is $letto ms, not $atteso"
		ko "   With this cap one does not know whether RCP or QUIC will close,"
		ko "   and the numbers of §4.6 could not be attributed to anyone."
		return 2
	fi
	ok "⭐ inactivity cap measured on the wire: $letto ms — the premise holds"
	return 0
}

ESITO=0
FATTE=""

fase() # $1 = name (sani|ping), $2 = transport cap in ms
{
	local nome=$1 tms=$2 e=0
	log "Phase «$nome» — transport cap ${tms} ms"
	if [ "$nome" = ping ]; then
		inf "⭐ the TRANSPORT cap is BELOW the PROTOCOL cap"
		inf "  (${tms} ms against 60 000): if TEMPO_SCADUTO arrives all the same at"
		inf "  60 s, the PINGs of §4.6 are there; if it dies around ${tms} ms"
		inf "  without a reason, they are missing — and it is the signature §4.6 describes"
	else
		inf "the TRANSPORT cap is above all three"
		inf "protocol caps: here only RCP can be the one closing"
		inf "⚠ and that is why this phase, ALONE, does not test the PINGs"
	fi
	accendi "$tms" "$nome" || { ESITO=4; return 4; }
	if ! tetto_dal_pari "$tms" "$nome"; then
		spegni
		ESITO=5
		return 5
	fi
	bash "$ENTRA" --root \
		"python3 -u $DENTRO/01-b6-tetti.py --indirizzo $IND $(bersaglio_opzioni_python) --utente $UTENTE --parola-file $PAROLA_DENTRO --fase $nome --idle $tms --tetti-codice $TETTI_CODICE"
	e=$?

	# ⛔ B0.5, from outside.  The bench asks it at every case by opening a new
	#    connection; this asks the SYSTEM, which is a different witness: a
	#    process can answer and have already lost its children.
	if [ -d "/proc/$PID" ]; then
		ok "process $PID is still there (B0.5, from the system)"
	else
		ko "⛔ THE SERVER DIED during phase «$nome»"
		e=1
	fi

	# ⚠ The server log: diagnosis, NOT arbiter (§8.1 wants the farewell
	#   verified from the receiving side).
	log "What the server wrote in phase «$nome» — diagnosis, not proof"
	if [ -f "$B_LOG_FUORI" ]; then
		# ⛔ The TARGET's fingerprint is counted: the product does not write
		#    «REMOTIX B3» anywhere, and a zero would be read as «the server
		#    wrote nothing».
		grep -cE "$B_IMPRONTA" "$B_LOG_FUORI" \
			| sed 's/^/        log lines: /'
		if grep -q "scaduto il tetto per" "$B_LOG_FUORI"; then
			grep "scaduto il tetto per" "$B_LOG_FUORI" | sed 's/^/        /'
		else
			inf "no «scaduto il tetto per» line: the server does not declare"
			inf "it let any cap expire in this phase"
		fi
	else
		inf "⛔ no log to summarise: $B_LOG_FUORI is not there"
		inf "   (volume not mapped? server never started? name changed?)"
	fi

	# ⛔ AND THE SHUTDOWN ENTERS THE OUTCOME — finding R12-A.24.  If the server
	#    did not die or the port was not freed, the next phase would measure a
	#    state nobody verified, and its red would not be the caps'.
	if ! spegni; then
		ko "⛔ phase «$nome» did not leave the machine as it found it"
		if [ "$e" -eq 0 ]; then e=5; fi
	fi
	FATTE="$FATTE $nome"
	# ⛔ Three different outcomes from the bench, and they are kept: 1 = the
	#    server is wrong, 3 = the server does what the CODE says but the
	#    DOCUMENT says something else, 5 = the initial state was not clean (B0.3).
	if [ "$e" -ne 0 ]; then
		if [ "$ESITO" -eq 0 ] || [ "$e" -eq 1 ]; then
			ESITO=$e
		fi
	fi
	return "$e"
}

# ⛔⭐ AND IF THE TWO CAPS COINCIDE, THE TWO PHASES ARE NOT INDEPENDENT.
#     On the product both are 30 000 ms, because `IDLE_MS` does not move:
#     `credenziali-tetto` (sani) and `credenziali-tetto-sotto-il-trasporto`
#     (ping) then measure THE SAME THING, and counting them as two
#     confirmations would be counting the same measurement twice.
if [ "$TETTO_SANI" = "$TETTO_PING" ]; then
	log "⛔ The two phases against «$B_NOME» are NOT independent"
	inf "the transport cap is $TETTO_SANI ms in both: it is IDLE_MS"
	inf "in src/trasporto.c, and no option touches it."
	inf "⚠ CIAO (5 s) and ATTACCA (10 s) stay clean — 30 s > 10 s — and their"
	inf "  two numbers are worth what they were worth."
	inf "⛔ CREDENZIALI (60 s) does not: 30 s < 60 s, so in the «sani» phase what"
	inf "  keeps the connection alive is already the PINGs, exactly as in «ping»."
	inf "⭐ The gain: «credenziali-presto», which keeps quiet for 42 s, becomes a"
	inf "  SECOND test of the PINGs instead of a check that passes anyway."
fi

if [ "$AZIONE" = tutto ] || [ "$AZIONE" = sani ]; then
	fase sani "$TETTO_SANI"
fi
if [ "$AZIONE" = tutto ] || [ "$AZIONE" = ping ]; then
	fase ping "$TETTO_PING"
fi

# ---------------------------------------------------------------------------
# ⛔ B0.3 — THE DECLARATION ON THE UNBLOCK, and now it is a TRUE declaration.
#
# ⚠ This section said «B6 does not call the unblock command, and says why»,
#   and the reason was that the command «wants a server started with that
#   option, and B6 starts its own without it».  ⭐ Now it starts it WITH it:
#   `bersaglio_accendi` always passes `--comando-socket`, and the socket is
#   B6's only.
# ⛔ B6 in any case unblocks nothing INSIDE the run, and does not need to: it
#    never fails an authentication.  Here it is only said that the machine stays
#    as it found it, and it is verified instead of believed.
log "B0.3 — what this run leaves behind"
inf "⭐ B6 failed no authentication: no count consumed,"
inf "   no ban left on whoever comes after"
inf "⛔ and its ban file is «$B_BAN», which no other bench reads"

log "Outcome"
inf "target: $B_NOME  ·  binary md5 ${B_MD5:-unknown}"
inf "phases run:${FATTE:- none}"
case "$ESITO" in
0)
	if [ "$AZIONE" = tutto ]; then
		ok "⭐ B6 passes: the three caps expire with the right reason, not before and"
		ok "   not after, and the PINGs of §4.6 hold under a transport shorter"
		ok "   than the protocol"
	else
		ok "⭐ phase «$AZIONE» passes"
		inf "⚠ and this is NOT «B6 passes»: the run was partial"
	fi
	;;
3)
	ko "⛔ B6: the wire behaves as the CODE says, but the DOCUMENT says"
	ko "   something else.  The cure is in RCP.md, not in the server — and it must"
	ko "   be written with the date and the source (CODER.md §5)."
	;;
4)
	ko "⛔ B6: the tool is not certified, or the server does not start:"
	ko "   nothing was measured"
	;;
5)
	ko "⛔ B6: the initial state was not the one needed (B0.1/B0.3), or"
	ko "   the transport cap on the wire is not the one requested (R8.3),"
	ko "   or the shutdown was not verified (R12-A.24)."
	ko "   It is not a red of the caps."
	;;
6)
	# ⛔ THE FOURTH OUTCOME, AND IT IS NOT ZEAL — finding R12-A.25.  A case the
	#    bench could not classify ended up among the proofs that the DOCUMENT is
	#    wrong, and exited 3: the cure was sent to `RCP.md` for a symptom that
	#    could be the server's.
	ko "⛔ B6: a case produced an outcome the bench CANNOT CLASSIFY."
	ko "   It is not «the server is wrong» and it is not «the document is wrong»: it is a"
	ko "   measurement to redo, and R3.27 stays open."
	;;
*)
	ko "⛔ B6: something does not pass"
	;;
esac
inf "the server logs: $FUORI/b6-$B_NOME-sani.log and $FUORI/b6-$B_NOME-ping.log"
inf "⭐ and the FACTS of this run, one per line: $B_ESITI_FUORI"
inf "   (until 11 Aug 2026 B6 had no log, and its three"
inf "    numbers — 5.0 · 60.1 · 10.0 s — cannot be re-verified by anyone)"
exit "$ESITO"
