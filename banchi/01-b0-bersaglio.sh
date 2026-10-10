#!/bin/bash
#
# 01-b0-bersaglio.sh — ⛔ THE SINGLE FORM WITH WHICH B5, B6, B7 AND B8 CHOOSE
#                        WHICH SERVER THEY MEASURE AGAINST.
#
#   BERSAGLIO=innesto  bash 01-b5-lancia.sh
#   BERSAGLIO=prodotto bash 01-b5-lancia.sh
#
# ⛔ **MANDATORY, AND WITHOUT A DEFAULT VALUE.**  The three legitimate values are
#    `innesto`, `prodotto` and `controllo`, and it is the same form with which the
#    transport probe chooses its own target: two different conventions for the
#    same thing are the defect of the seams that the review of 11 Aug
#    2026 has already found once.  ⚠ A default here would be **the most
#    convenient way to measure the wrong server**: whoever relaunches a bench from
#    memory does not type the variable, and the round would end up against the graft with
#    the word "prodotto" only in the head of whoever is watching.
#
# It is not a bench: it is the piece the four benches have in common, and it is in a
# single file for a reason paid for on 11 Aug 2026 (finding R12C.5).  The
# five-minute window of §4.4-bis was **copied** into four documents
# instead of referenced, and the four copies were not the same: a bench written from
# one of the wrong copies would have given red on the right code.  ⛔ Four
# copies of this profile inside four launch scripts are the same defect
# in new clothes — and this time they would be copies of code, which diverge
# even faster than those of a document.
#
# ---------------------------------------------------------------------------
# ⛔⭐ THE TWO SERVERS, AND WHY THEY ARE NOT THE SAME PROGRAM
#
#   innesto    `bsslserver`, port **7447**.  It is the ngtcp2 example server
#              with `01-b2-ngtcp2-wt-innesta.py` (WebTransport) and
#              `01-b3-rcp-innesta.py` (RCP + the host-side ban) inside.  It is what
#              all benches turned on until 11 Aug 2026, and it is
#              the only place where certain measurements have already been taken: ⛔ it is
#              not thrown away and not replaced.
#
#   prodotto   the `remotix` binary from `src/`, port **7448**.  It is what
#              the user will install.
#
# ⛔ `src/rcp.c` and `banchi/rcp/rcp.c` are IDENTICAL byte for byte (fingerprint
#    `cb7af778…`, verified on 11 Aug 2026).  ⚠ But **everything around them
#    was written twice, by two hands that did not talk to each other**:
#    the WebTransport layer, the transport, the page, the unblock command, the
#    shutdown path.  And at the points where the two drafts diverge, one
#    carries written proof that the other did not work — the comments of
#    `src/webtransport.c` quote it eight times, always in the form "in the graft
#    this was missing / here the connection died".
#
# ⛔⭐ HENCE THE DUTY OF THIS FILE, and it is not zeal: the first time a
#     bench is pointed at the product **it will give reds on a server that does
#     the things**.  This project's precedent says that when a bench is red
#     and the code seems to work, one searches in the code for hours before
#     suspecting the measurement (`LEZIONI.md` §1.9 point 3, and the seventh guise).
#     So every red a bench can give **must be able to say by itself whether
#     it accuses the product or accuses its own leg**, and the three cures are here:
#
#       1. the target is DECLARED and written into the log of every round;
#       2. the target is VERIFIED on the wire and in the server log —
#          `bersaglio_impronta` —, because "I declared it" and "it is that one" are
#          two different facts (`LEZIONI.md` §1.9, corollary 5: a denominator
#          is read where the thing happens);
#       3. the known differences between the two servers are **in this file**, in a
#          table, and the benches read them instead of discovering them anew.
#
# ---------------------------------------------------------------------------
# ⛔ WHY AN ENVIRONMENT VARIABLE, AND NOT AN ARGUMENT
#
# The four benches have four different argument grammars, already full:
#
#   01-b5-lancia.sh  [tutto|elenco|solo] [filtro]
#   01-b6-lancia.sh  [tutto|sani|ping|elenco]
#   01-b7-lancia.sh  [tutto|elenco|frasi|solo] [filtro]
#   01-b8-lancia.sh  [<number of blocks>|previsione|costruisci]
#
# ⛔ There is no free position that would mean the same thing in all
#    four, and slipping it into different positions would be **four forms**, that is
#    the opposite of what is needed.  `BERSAGLIO=` stands in front of all four
#    command lines, the same.
#
# ⚠ And it is NOT inherited inside the container: `enter.sh` does `env -i` and wipes
#   the environment.  So every launch script reads it HERE, outside, and passes it to the
#   Python benches as `--bersaglio <name>` on the command line — where it can be
#   seen, instead of as a variable someone believes they passed.
#
# ---------------------------------------------------------------------------
# ⛔ AND AN UNKNOWN VALUE DOES NOT FALL BACK ON «innesto»
#
# `BERSAGLIO=produtto` (with the typo) would measure the graft
# while declaring the product, and the log of the round would carry the right word
# on the wrong server.  ⭐ It exits **2**, and states the two legitimate values.
# ---------------------------------------------------------------------------

# ⚠ This file is included with `.` or `source`, not executed.  If someone
#   launches it by itself, it says so instead of silently doing nothing.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	printf '    \033[1;31mNO\033[0m  ⛔ 01-b0-bersaglio.sh is not executed: it is included.\n'
	printf '        SIGLA=b5 . /media/REMOTIX/src/01-b0-bersaglio.sh\n'
	exit 2
fi

# ---------------------------------------------------------------------------
# The places, and they are the same for all benches.
B0_ENTRA=/media/REMOTIX/enter.sh
B0_FUORI=/media/REMOTIX/src          # as the server sees it
B0_DENTRO=/srv/src                   # the same place, as the container sees it

# ⛔ The code of the bench that includes this file: it goes into the names of the
#    ban file, the command socket and the logs.  Without it, two different benches
#    would write over each other — and it is the kind of state surviving between one bench
#    and the next that B0.2 lists first.
B0_SIGLA=${SIGLA:-b0}

b0_ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
b0_ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
b0_inf() { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ THE PROFILE.  One line per difference, and every difference has a reason
#    readable in the code of the two servers.
# ---------------------------------------------------------------------------
# ⛔ NO `${BERSAGLIO:-innesto}`: the variable is mandatory.
if [ -z "${BERSAGLIO:-}" ]; then
	b0_ko "⛔ BERSAGLIO is missing, and I have no default value."
	b0_ko "   The three values are «innesto», «prodotto» and «controllo»:"
	b0_ko "     BERSAGLIO=innesto  bash .../01-${B0_SIGLA}-lancia.sh …"
	b0_ko "     BERSAGLIO=prodotto bash .../01-${B0_SIGLA}-lancia.sh …"
	b0_ko "   ⛔ A default here would be the most convenient way to measure the"
	b0_ko "      wrong server: whoever relaunches from memory does not type the"
	b0_ko "      variable, and the round would end up against the graft with"
	b0_ko "      the word «prodotto» only in the head of whoever is watching."
	exit 2
fi
B_NOME=$BERSAGLIO

case "$B_NOME" in
innesto)
	B_PORTA=7447
	B_IND=192.168.0.2
	B_LEGAME=0.0.0.0
	B_INDIRIZZI=127.0.0.1,192.168.0.2
	B_CERT=/media/REMOTIX/b2-certificati      # ⚠ path INSIDE the container
	B_ESE="$B0_DENTRO/b2/ngtcp2/build/examples/bsslserver"
	B_LIBS="$B0_DENTRO/b2/ngtcp2/build/lib"
	B_COMM=bsslserver                         # expected /proc/<pid>/comm
	# ⛔ The fingerprint: EVERY log line of this server starts with
	#    «REMOTIX B3: » or «REMOTIX B5: » (the graft puts them there), or it is a
	#    line of the ngtcp2 example.  It is enough that there are some.
	B_IMPRONTA='REMOTIX B[35]:'
	B_CONTROLLO='REMOTIX B3'
	# ⭐ The transport idle cap CAN BE CHOSEN: the ngtcp2 example
	#    takes `--timeout=Ns`.
	B_IDLE_SCELTA=si
	B_IDLE_LUNGO=120000     # above all three caps of §4.6: only RCP closes
	B_IDLE_CORTO=15000      # below the 60 s of the credentials: the «ping» phase
	# ⛔ Where a shutdown path can live, for B7.  The denominator
	#    is read WHERE THE THING HAPPENS: in `rcp.c` it will never be, because
	#    `rcp.c` does not know a process exists.
	B_SORGENTI="$B0_DENTRO/rcp/rcp.c,$B0_DENTRO/01-b3-rcp-innesta.py"
	B_SPEGNIMENTO=no        # ⇒ B7 has SEVEN reasons that can be provoked
	# The lines the host-side ban writes at startup (B8 compares them).
	B_R_BAN_CARICATI='bans loaded:'
	B_R_BAN_ILLEGGIBILE='COULD NOT READ the ban file'
	B_R_COMANDO_VIVO="the unblock command listens on"
	B_R_PAGINA='TCP page at'
	B_BAN_ILLEGGIBILE_PARTE=si  # the graft starts all the same and writes so
	;;
prodotto)
	B_PORTA=7448
	B_IND=192.168.0.2
	B_LEGAME=0.0.0.0
	B_INDIRIZZI=127.0.0.1,192.168.0.2
	B_CERT="$B0_DENTRO/remotix-cert"
	B_ESE="$B0_DENTRO/remotix/remotix"
	B_LIBS=""
	B_COMM=remotix
	# ⛔ The product's fingerprint: `registro.c` writes «HH:MM:SS.mmm <area> …»,
	#    with the area among avvio·quic·wt·rcp·pagina·cert.  No line carries
	#    «REMOTIX B3», and no line of the graft carries this form: the two
	#    fingerprints exclude each other, and that is what makes them useful.
	B_IMPRONTA='^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9][0-9][0-9] (avvio|quic|wt|rcp|pagina|cert) '
	B_CONTROLLO='REMOTIX — phase 1, the bare wire'
	# ⛔ THE IDLE CAP CANNOT BE CHOSEN: `src/trasporto.c` has
	#    `#define IDLE_MS 30000` and no option touches it (verified with
	#    grep on 11 Aug 2026: no `getenv` in all of `src/`).  ⚠ Asking the product
	#    for 120 s is a request that CANNOT be granted, and
	#    `bersaglio_accendi` refuses instead of turning on something different
	#    from what it was asked (`CODER.md` §3.9: if it does not obey,
	#    declare the failure, do not silently fall back).
	B_IDLE_SCELTA=no
	B_IDLE_LUNGO=30000
	B_IDLE_CORTO=30000
	# ⛔ The product's shutdown path is NOT in `rcp.c`: it is in
	#    `main.c` (which dismisses everyone before exiting), in `trasporto.c`
	#    (`trasporto_congeda_tutte`) and in `webtransport.c` (`wt_congeda`).
	#    Searching for it in `rcp.c` — which is identical in the two servers — would say "zero"
	#    on both targets, and it is a denominator read where the thing does NOT
	#    happen.
	B_SORGENTI="$B0_DENTRO/remotix/rcp.c,$B0_DENTRO/remotix/main.c,$B0_DENTRO/remotix/trasporto.c,$B0_DENTRO/remotix/webtransport.c"
	B_SPEGNIMENTO=si        # ⇒ B7 has EIGHT reasons that can be provoked
	B_R_BAN_CARICATI='addresses loaded'
	B_R_BAN_ILLEGGIBILE="exists and could NOT be read"
	B_R_COMANDO_VIVO="the unblock command listens on"
	B_R_PAGINA='listening over TCP on'
	# ⛔⭐ AND HERE THE TWO SERVERS DO TWO OPPOSITE THINGS: if the ban file exists and
	#     cannot be read, the product **DOES NOT START** (`src/main.c`: "it is not «zero
	#     bans», it is the protection of §4.4-bis turned off.  Not starting."), while
	#     the graft starts and writes so.  ⚠ So on this target that case
	#     is not observed as "a line in the log": it is observed as "the
	#     server did not turn on", and a bench that looked for the line would give
	#     red on a server that does **more** than what it is asked.
	B_BAN_ILLEGGIBILE_PARTE=no
	;;
controllo)
	# ⛔ THE THIRD VALUE EXISTS IN THE GRAMMAR AND NOT IN THESE FOUR
	#    BENCHES — and we say so, instead of letting it fall onto «innesto».
	#
	# `controllo` is the target that MUST turn the bench red: the
	# server faulty on purpose, that is the certification of `LEZIONI.md` §1.2
	# done on a whole process instead of on a fact built by hand.  For
	# B5, B6, B7 and B8 that server today **does not exist**: `01-b11-guasto-innesta.py`
	# breaks the server towards the PAGE (B11), not towards the wire, and B8 does its own
	# certification elsewhere (`--certifica`, on facts built by hand).
	#
	# ⚠ Writing it here, and exiting 2, is the difference between "it is not there" and "it is there and
	#   does nothing": whoever launches `BERSAGLIO=controllo` must read a line, not
	#   get a green of the graft.
	b0_ko "⛔ BERSAGLIO=controllo: the grammar provides for it, these four"
	b0_ko "   benches do not have it yet."
	b0_ko "   It would be the server FAULTY ON PURPOSE, the one against which the bench"
	b0_ko "   must turn red (LEZIONI.md §1.2).  Today it exists only towards the"
	b0_ko "   page (01-b11-guasto-innesta.py), not towards the wire."
	b0_ko "   ⛔ And I do not fall back on «innesto»: a check that in reality measures"
	b0_ko "      the healthy case is worse than an absent check, because it prints"
	b0_ko "      a green."
	exit 2
	;;
*)
	b0_ko "⛔ BERSAGLIO=«$B_NOME» does not exist."
	b0_ko "   The three values are «innesto», «prodotto» and «controllo»."
	b0_ko "   ⛔ And I do not fall back on any: I would measure one server while declaring"
	b0_ko "      another, and the log of the round would carry the right word on the"
	b0_ko "      wrong server."
	exit 2
	;;
esac

# ⛔ One per bench, and per BERSAGLIO.  Two benches never share a ban file
#    nor a socket: the count of §4.4-bis lives in the serving process, and
#    giving it one per bench is the only isolation that does not depend on who
#    remembers to unblock.  ⚠ And it must be DECLARED, because it changes what
#    a green of B0.3 means: in production the file is a single one.
B_BAN="$B0_DENTRO/${B0_SIGLA}-${B_NOME}-ban.txt"
B_COMANDO="$B0_DENTRO/${B0_SIGLA}-${B_NOME}-comando.sock"
# The bench's log of facts, one per target: two rounds against two different
# servers never end up in the same file, and every line repeats it anyway.
B_ESITI="$B0_DENTRO/${B0_SIGLA}-esiti-${B_NOME}.jsonl"
B_ESITI_FUORI="$B0_FUORI/${B0_SIGLA}-esiti-${B_NOME}.jsonl"

B_PID=""
B_LOG=""
B_LOG_FUORI=""
# ⛔ The md5 fingerprint of the MEASURED binary, and its time and that of the most
#    recent source.  `bersaglio_pronto` fills them, and they end up in the log of every
#    round: `LEZIONI.md` §1.9 eighth guise — "the file is there" and "the file is the one
#    I just built" are two different questions, and yesterday's binary
#    answers "yes" to the first.  ⚠ `[M]` 11 Aug 2026: the product binary
#    on the server was from 21:08 and `trasporto.c` from 22:10, and the log
#    of the last start carried a wording from TWO generations before.
B_MD5=""
B_BIN_QUANDO=""
B_SORG_PIU_RECENTE=""
# The identifier of the round: the same for all lines of the log, and for
# all programs this round launches.
B_GIRO=$(date +%Y%m%d-%H%M%S)

# ---------------------------------------------------------------------------
# ⛔ THE DECLARATION, and it must be printed BEFORE any number.
bersaglio_dichiara()
{
	printf '\n\033[1m== The target\033[0m\n'
	b0_ok "BERSAGLIO=$B_NOME  ·  $B_ESE  ·  port $B_PORTA"
	b0_inf "ban: $B_BAN"
	b0_inf "unblock command: $B_COMANDO"
	b0_inf "log of facts: $B_ESITI_FUORI"
	b0_inf "transport idle cap: ${B_IDLE_LUNGO} ms$(
		[ "$B_IDLE_SCELTA" = no ] && printf ' ⛔ NOT CHOSEN BY US (IDLE_MS in trasporto.c)')"
	b0_inf "shutdown path (SERVER_IN_CHIUSURA 0x0C): $B_SPEGNIMENTO"
	b0_inf "md5 fingerprint of the binary: ${B_MD5:-⛔ not taken yet}"
	b0_inf "binary from $(date -d "@${B_BIN_QUANDO:-0}" '+%d %b %H:%M:%S' 2>/dev/null || echo '—')\
 · most recent source: ${B_SORG_PIU_RECENTE:-—}"
	if [ "$B_NOME" = prodotto ]; then
		b0_inf "⚠ it is the first time this bench measures the product: a red"
		b0_inf "  below must be read first as «my leg does not hold on the"
		b0_inf "  new target» and then as «the product is wrong» (LEZIONI.md"
		b0_inf "  §1.9 point 3).  The differences already known are in"
		b0_inf "  01-b0-bersaglio.sh and in the prediction of every bench."
	fi
}

# ---------------------------------------------------------------------------
# ⛔ WHO HOLDS THE PORT — and "unknown" is not rounded to "free".
#
# Taken from `01-b6-lancia.sh` (findings R12-A.7 and R12-A.23), which is the strongest
# draft of the four: the remote command prints its own exit status
# by itself, and there is the positive control of the tool — `ss` always prints
# at least its own header, and if it prints nothing it has looked at nothing.
#
# ⛔ And both UDP **and** TCP are looked at: both servers listen on the same
#    port with two protocols (`RCP.md` §2.4), and a bench that looked only at
#    UDP would say "free" with the page of another round still listening.
B0_USCITA=""
b0_dentro() # $1 = remote command.  Output in $B0_USCITA, status = that of the command
{
	local tutto stato
	tutto=$(bash "$B0_ENTRA" --root "$1"'; printf "\nB0-FINE=%s\n" $?')
	stato=$(printf '%s\n' "$tutto" | sed -n 's/^B0-FINE=\([0-9][0-9]*\)$/\1/p' | tail -1)
	B0_USCITA=$(printf '%s\n' "$tutto" | grep -v '^B0-FINE=')
	if [ -z "$stato" ]; then
		return 125   # it did not reach the end: it is not a zero
	fi
	return "$stato"
}

B_CHI=""
bersaglio_porta() # 0 = taken ($B_CHI) · 1 = free · 2 = unknown
{
	local st
	b0_dentro "ss -ulnp; ss -tlnp"
	st=$?
	if [ "$st" -ne 0 ]; then
		b0_ko "⛔ «ss» did not answer inside the container (exit $st):"
		printf '%s\n' "$B0_USCITA" | tail -5 | sed 's/^/        /'
		return 2
	fi
	if [ -z "$B0_USCITA" ]; then
		b0_ko "⛔ «ss» printed NOTHING, not even the header:"
		b0_ko "   the tool is mute, and its silence is not a free port"
		return 2
	fi
	B_CHI=$(printf '%s\n' "$B0_USCITA" | grep ":$B_PORTA ")
	[ -n "$B_CHI" ]
}

# ---------------------------------------------------------------------------
# ⛔ IS THE BINARY I AM ABOUT TO TURN ON THE ONE I BELIEVE? — `LEZIONI.md` §1.9,
#    eighth guise: "the file is there" and "the file is the one I just built"
#    are two different questions, and yesterday's binary answers "yes" to the first.
#
# ⚠ The two roads are different on purpose:
#     innesto   the grafts are removed and put back, the mark is COUNTED in the
#               two sources, and then it is compiled looking at the
#               builder's outcome;
#     prodotto  ⛔ THIS FILE DOES NOT COMPILE THE PRODUCT.  `src/` belongs to
#               no bench, and a bench that recompiles what it measures
#               takes away its own independent witness.  It only VERIFIES — the
#               binary is there, and it is more recent than every `.c` — and if it is not
#               it says how to redo it and stops.
#
# ⛔⭐ AND THE REAL VERIFICATION IS A SINGLE ONE, FOR BOTH TARGETS:
#     the md5 fingerprint of the binary, its time, and the time of the most recent source.
#     If the binary is older, **nothing is measured**.
#
#     `[M]` 11 Aug 2026 — and it is not a hypothesis: the product binary on the
#     server was from 21:08 and `trasporto.c` from 22:10.  The log
#     of the last start carried a wording from **two generations
#     before**, and anyone who had measured that process would have attributed to
#     tonight's code the behaviour of last evening.
b0_binario_e_sorgenti() # $1 = list of source globs, already quoted for the remote shell
{
	local glob=$1 f="$B0_FUORI/${B0_SIGLA}-${B_NOME}-binario.txt"
	rm -f "$f"
	bash "$B0_ENTRA" --root \
		"{ md5sum $B_ESE 2>/dev/null | cut -d' ' -f1 || echo x; \
		   stat -c %Y $B_ESE 2>/dev/null || echo x; \
		   ls -t $glob 2>/dev/null | head -1; \
		   stat -c %Y \$(ls -t $glob 2>/dev/null | head -1) 2>/dev/null || echo x; \
		 } > $B0_DENTRO/${B0_SIGLA}-${B_NOME}-binario.txt 2>&1"
	if [ ! -f "$f" ]; then
		b0_ko "⛔ I could not look at the binary: the file was not"
		b0_ko "   written.  It is not «it is old», it is that nobody looked"
		return 3
	fi
	B_MD5=$(sed -n 1p "$f")
	B_BIN_QUANDO=$(sed -n 2p "$f")
	B_SORG_PIU_RECENTE=$(sed -n 3p "$f")
	local t_src
	t_src=$(sed -n 4p "$f")
	case "$B_MD5" in
	''|*[!0-9a-f]*)
		b0_ko "⛔ the binary «$B_ESE» is not there or cannot be read:"
		sed 's/^/        /' "$f"
		return 3 ;;
	esac
	case "$B_BIN_QUANDO" in
	''|*[!0-9]*) b0_ko "⛔ I could not read the time of the binary"; return 3 ;;
	esac
	case "$t_src" in
	''|*[!0-9]*)
		b0_ko "⛔ I could not read the time of the most recent source."
		b0_ko "   ⛔ And this is NOT «the binary is up to date»: it is that I could"
		b0_ko "      not know (LEZIONI.md §1.9 rule 1)"
		return 3 ;;
	esac
	if [ "$B_BIN_QUANDO" -lt "$t_src" ]; then
		b0_ko "⛔ THE BINARY IS OLDER THAN THE SOURCE «$B_SORG_PIU_RECENTE»."
		b0_ko "   Inside it there is not what one reads in the .c, and every red of"
		b0_ko "   this round would accuse code that the server has never"
		b0_ko "   executed.  ⛔ I do not measure."
		if [ "$B_NOME" = prodotto ]; then
			b0_ko "   Redo it with:"
			b0_ko "     bash $B0_ENTRA --root \"bash $B0_DENTRO/remotix/costruisci.sh\""
		else
			b0_ko "   Redo it by relaunching this same bench: the graft"
			b0_ko "   recompiles by itself (but here the compilation has already passed,"
			b0_ko "   so check whether someone is holding an old binary)"
		fi
		return 3
	fi
	b0_ok "binary verified: md5 ${B_MD5:0:12}… · more recent than every"\
"source (the most recent is «$B_SORG_PIU_RECENTE»)"
	return 0
}

bersaglio_pronto()
{
	if [ "$B_NOME" = innesto ]; then
		local sorg="$B0_DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc"
		local main="$B0_DENTRO/b2/ngtcp2/examples/server.cc"
		printf '\n\033[1m== The graft server is put back and recompiled\033[0m\n'
		b0_inf "⛔ the grafts are REMOVED and put back: applying one on top of"
		b0_inf "   the other would leave two copies of the same code"
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b3-rcp-innesta.py --togli > /dev/null"
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b2-ngtcp2-wt-innesta.py --togli > /dev/null"
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b2-ngtcp2-wt-innesta.py" \
			| grep -E "foothold|lines|CODE" | sed 's/^/        /'
		bash "$B0_ENTRA" --root "python3 $B0_DENTRO/01-b3-rcp-innesta.py" \
			| grep -E "foothold|NO |our files" | sed 's/^/        /'
		local q o
		q=$(bash "$B0_ENTRA" --root "grep -c 'REMOTIX B3' $sorg" | tr -cd '0-9')
		o=$(bash "$B0_ENTRA" --root "grep -c 'REMOTIX B3' $main" | tr -cd '0-9')
		if [ "${q:-0}" -lt 3 ]; then
			b0_ko "⛔ the RCP layer is NOT in the codec («REMOTIX B3» lines: ${q:-0})"
			return 3
		fi
		if [ "${o:-0}" -lt 5 ]; then
			b0_ko "⛔ the host-side ban is NOT in server.cc (lines: ${o:-0}):"
			b0_ko "   no TCP page and no unblock command"
			return 3
		fi
		b0_ok "the graft is in the two files (codec $q lines · host $o)"
		rm -f "$B0_FUORI/${B0_SIGLA}-compila.log"
		if ! bash "$B0_ENTRA" --root \
			"ninja -C $B0_DENTRO/b2/ngtcp2/build bsslserver > $B0_DENTRO/${B0_SIGLA}-compila.log 2>&1"; then
			b0_ko "the compilation failed:"
			if [ -f "$B0_FUORI/${B0_SIGLA}-compila.log" ]; then
				tail -25 "$B0_FUORI/${B0_SIGLA}-compila.log" | sed 's/^/        /'
			else
				b0_ko "   ⛔ and the compilation log DOES NOT EXIST: it is not"
				b0_ko "      ninja that kept quiet, it is that we never got as far as"
				b0_ko "      launching it"
			fi
			return 3
		fi
		b0_ok "compiled"
		# ⛔ And here too the BUILDER's outcome is looked at and then the binary:
		#    `ninja` can exit 0 without having redone anything, and the grafted
		#    sources have just changed.
		b0_binario_e_sorgenti \
			"$B0_DENTRO/b2/ngtcp2/examples/*.cc $B0_DENTRO/b2/ngtcp2/examples/*.c $B0_DENTRO/rcp/rcp.c" \
			|| return 3
		return 0
	fi

	# ── the product ────────────────────────────────────────────────────────
	printf '\n\033[1m== The product — VERIFIED, not recompiled\033[0m\n'
	b0_inf "⛔ a bench that recompiles what it measures takes away its own"
	b0_inf "   independent witness: here only the binary is looked at, and if it is not more"
	b0_inf "   recent than the sources we stop"
	b0_binario_e_sorgenti "$B0_DENTRO/remotix/*.c $B0_DENTRO/remotix/*.h" || return 3
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ TURNING ON.  A single form, two different commands — and the bench asks for the
#    idle cap it needs, not the one the target grants it.
#
#   bersaglio_accendi <label> <idle_ms> [extra options]
#
# ⛔ If the target cannot grant the request, it does NOT turn on: it exits 5.  A
#    server turned on with a cap different from the one asked would measure another
#    thing under the same label — `CODER.md` §3.9, form E2.
bersaglio_accendi()
{
	local et=$1 idle=$2
	shift 2
	B_LOG="$B0_DENTRO/${B0_SIGLA}-${B_NOME}-${et}.log"
	B_LOG_FUORI="$B0_FUORI/${B0_SIGLA}-${B_NOME}-${et}.log"
	rm -f "$B_LOG_FUORI" "$B0_FUORI/${B0_SIGLA}-${B_NOME}-${et}.pid"

	if [ "$B_IDLE_SCELTA" = no ] && [ "$idle" != "$B_IDLE_LUNGO" ]; then
		b0_ko "⛔ the target «$B_NOME» CANNOT turn on with an idle"
		b0_ko "   cap of $idle ms: `IDLE_MS` in src/trasporto.c is"
		b0_ko "   $B_IDLE_LUNGO ms and no option touches it."
		b0_ko "   ⛔ And I do not turn on anyway declaring $idle: it would be measuring"
		b0_ko "      one thing under the label of another (CODER.md §3.9)."
		b0_ko "   The bench must ask for \$B_IDLE_LUNGO / \$B_IDLE_CORTO, which on"
		b0_ko "   this target are both $B_IDLE_LUNGO."
		return 5
	fi

	# ⛔ AND THE PORT IS LOOKED AT BEFORE EVERY TURNING ON, not once at the start
	#    of the bench: between the first phase and the second there is room for another server.
	#    ⚠ "Unknown" is not rounded to "free": a second server on top of the
	#      first would measure the server of another round, and the red would land
	#      on the wrong suspect (findings R8.15, R12-A.7, R12-A.23).
	bersaglio_porta
	case $? in
	0)	b0_ko "⛔ port $B_PORTA is ALREADY TAKEN: I turn on nothing."
		printf '%s\n' "$B_CHI" | sed 's/^/        /'
		b0_ko "   stop it by PID (never with pkill -f) and relaunch"
		return 5 ;;
	1)	: ;;
	*)	b0_ko "⛔ it could not be known who holds port $B_PORTA, and"
		b0_ko "   «unknown» is not rounded to «free»: I do not turn on"
		return 5 ;;
	esac

	local ts=$((idle / 1000))
	if [ "$B_NOME" = innesto ]; then
		bash "$B0_ENTRA" --root \
			"nohup env LD_LIBRARY_PATH=$B_LIBS $B_ESE --timeout=${ts}s --ban-file=$B_BAN --comando-socket=$B_COMANDO $* $B_LEGAME $B_PORTA $B_CERT/sessione.key $B_CERT/sessione.pem < /dev/null > $B_LOG 2>&1 & echo \$! > $B0_DENTRO/${B0_SIGLA}-${B_NOME}-${et}.pid"
	else
		bash "$B0_ENTRA" --root \
			"nohup $B_ESE --indirizzo $B_LEGAME --nome $B_IND --porta $B_PORTA --certificati $B_CERT --pagina $B0_DENTRO/remotix/pagina.html --ban-file $B_BAN --comando-socket $B_COMANDO $* < /dev/null > $B_LOG 2>&1 & echo \$! > $B0_DENTRO/${B0_SIGLA}-${B_NOME}-${et}.pid"
	fi
	sleep 2
	B_PID=$(cat "$B0_FUORI/${B0_SIGLA}-${B_NOME}-${et}.pid" 2>/dev/null)
	# ⛔ `/proc`, not `kill -0`: the server belongs to root and this script does not, and as
	#    a normal user `kill -0` answers "operation not permitted", which is not
	#    "does not exist" (LEZIONI.md §1.9, sixth guise).
	if [ -z "$B_PID" ] || [ ! -d "/proc/$B_PID" ]; then
		b0_ko "⛔ the server «$B_NOME» did not start.  The log says:"
		if [ -f "$B_LOG_FUORI" ]; then
			tail -20 "$B_LOG_FUORI" | sed 's/^/        /'
		else
			b0_ko "   ⛔ and the log DOES NOT EXIST: it is not the server that"
			b0_ko "      kept quiet, it is that we never got as far as launching it"
		fi
		if [ "$B_NOME" = prodotto ] && [ "$B_BAN_ILLEGGIBILE_PARTE" = no ]; then
			b0_inf "⚠ and on this target «does not start» has one more cause that"
			b0_inf "  the graft does not have: if «$B_BAN» exists and cannot be read, the"
			b0_inf "  product REFUSES to start on purpose (src/main.c).  Look at"
			b0_inf "  the line «could NOT be read» above before"
			b0_inf "  searching elsewhere"
		fi
		return 4
	fi
	b0_ok "turned on «$B_NOME» (PID $B_PID · port $B_PORTA · cap ${ts}s) — log $B_LOG_FUORI"
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ SHUTTING DOWN IS NOT SENDING A `kill` — finding R12-A.24.  Between the death
#    of the process and the release of the port there is an instant that, if not
#    waited for, makes the next phase find a port still held and blame
#    itself.
#
# ⚠ And for the product it counts double: `SIGTERM` is not the end, it is the START of a
#   path — `main.c` dismisses all sessions with `SERVER_IN_CHIUSURA` and
#   waits up to two seconds for the bytes to leave.  A bench that expected
#   immediate death would read "it does not die" where there is a server doing
#   its job.
bersaglio_spegni()
{
	local giri=0
	[ -n "${B_PID:-}" ] || return 0
	bash "$B0_ENTRA" --root "kill $B_PID 2>/dev/null || true"
	while [ -d "/proc/$B_PID" ] && [ "$giri" -lt 20 ]; do
		sleep 0.5
		giri=$((giri + 1))
	done
	if [ -d "/proc/$B_PID" ]; then
		b0_ko "⛔ process $B_PID is still alive after 10 s"
		B_PID=""
		return 1
	fi
	b0_inf "process $B_PID is gone (after $giri half seconds)"
	B_PID=""
	bersaglio_porta
	case $? in
	0)	b0_ko "⛔ port $B_PORTA is still held after shutdown:"
		printf '%s\n' "$B_CHI" | sed 's/^/        /'
		return 1 ;;
	1)	b0_inf "port $B_PORTA is free again" ; return 0 ;;
	*)	b0_ko "⛔ it could not be known whether port $B_PORTA was released"
		return 1 ;;
	esac
}

# ---------------------------------------------------------------------------
# ⛔⭐ THE FINGERPRINT: DID I MEASURE THE SERVER I DECLARED?
#
# `LEZIONI.md` §1.9, corollary 5: *a denominator is read where the thing
# happens — on the wire, not in the configuration; in the process, not
# in the intention.*  ⛔ And the concrete case this function prevents has already
# happened at home: the SNI probe of B2 declared `server_name spedito:
# '192.168.0.2'` reading it from the CONFIGURATION, and nothing went on the wire.
#
# Here the analogue would be: `BERSAGLIO=prodotto` with port 7448 already held by
# a graft of a previous round, or a `remotix` binary that did not
# start and a `bsslserver` from yesterday still listening.  The server log
# says it in one line, and the two fingerprints exclude each other.
#
#   bersaglio_impronta   0 = it is it · 1 = it is the OTHER · 2 = it could not be said
bersaglio_impronta()
{
	local mie altrui altra
	if [ ! -f "$B_LOG_FUORI" ]; then
		b0_ko "⛔ the server log cannot be read ($B_LOG_FUORI):"
		b0_ko "   it is not «the server wrote nothing», it is that nobody looks"
		return 2
	fi
	altra='REMOTIX B[35]:'
	[ "$B_NOME" = innesto ] && \
		altra='^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.[0-9][0-9][0-9] (avvio|quic|wt|rcp|pagina|cert) '
	mie=$(grep -cE "$B_IMPRONTA" "$B_LOG_FUORI")
	altrui=$(grep -cE "$altra" "$B_LOG_FUORI")
	if [ "${mie:-0}" -eq 0 ] && [ "${altrui:-0}" -eq 0 ]; then
		b0_ko "⛔ the log carries NEITHER of the two fingerprints:"
		b0_ko "   neither that of «$B_NOME» nor that of the other server."
		b0_ko "   ⛔ It is the case in which it is not known what was measured, which is not"
		b0_ko "      «it is the right one»: I stop before the numbers."
		tail -5 "$B_LOG_FUORI" | sed 's/^/        /'
		return 2
	fi
	if [ "${altrui:-0}" -gt 0 ] && [ "${mie:-0}" -eq 0 ]; then
		b0_ko "⛔⭐ I DECLARED «$B_NOME» AND THE LOG IS THE OTHER SERVER'S"
		b0_ko "   ($altrui lines with the other fingerprint, 0 with mine)."
		b0_ko "   ⛔ Every number of this round would be attributed to the wrong"
		b0_ko "      target: I stop here.  Look at who holds port $B_PORTA."
		return 1
	fi
	# ⭐ And the positive control, on the same tool: the startup line that
	#    that server certainly writes.  Without it, "I found my fingerprint"
	#    could be a file of a previous round left there.
	if ! grep -qF "$B_CONTROLLO" "$B_LOG_FUORI"; then
		b0_ko "⛔ the fingerprint is there ($mie lines) but the startup line «$B_CONTROLLO»"
		b0_ko "   is NOT there: this log may be from a previous round."
		b0_ko "   ⛔ The positive control exists on purpose (LEZIONI.md §1.9,"
		b0_ko "      second rule): without it, my «I recognised it» is worth nothing"
		return 2
	fi
	b0_ok "⭐ the log is «$B_NOME»'s: $mie lines with its fingerprint, "\
"$altrui with the other's, and the startup line is there"
	return 0
}

# ---------------------------------------------------------------------------
# ⛔ THE UNBLOCK, AND ITS DECLARATION — rule B0.3.
#
# *"Every bench that calls it declares it, or "the ban did not fire" and "someone
# removed it" look the same."*  ⛔ And the `PING` **is the denominator of
# this rule**: without it, "the ban did not fire" and "the unblock never
# reached anyone" have the same face again.
#
#   bersaglio_ping                       is the command there and does it answer?
#   bersaglio_sblocca <why> [addr…]      removes, and prints which of the three outcomes
#
# ⛔ NEVER INSIDE THE BAN ROUND OF B8 (B0.3): there the unblock is not a tool,
#    it is the thing tested, and calling it first would make everything else pass by
#    construction.  This function does not know it: whoever calls it knows, and that is
#    why `<why>` is mandatory and ends up printed.
bersaglio_ping()
{
	bash "$B0_ENTRA" --root \
		"python3 $B0_DENTRO/01-b8-sblocca.py --socket $B_COMANDO --ping"
}

bersaglio_sblocca() # $1 = why · $2… = addresses (default: $B_INDIRIZZI)
{
	local perche=$1
	shift
	local elenco=${*:-}
	[ -n "$elenco" ] || elenco=$(printf '%s' "$B_INDIRIZZI" | tr ',' ' ')
	local ind esito=0
	for ind in $elenco; do
		printf '    --  unblocking «%s» (why: %s):\n' "$ind" "$perche"
		bash "$B0_ENTRA" --root \
			"python3 $B0_DENTRO/01-b8-sblocca.py --socket $B_COMANDO $ind" \
			|| esito=$?
	done
	return "$esito"
}

# ⛔ The initial state of the ban is declared AND verified — B0.1 and B0.2, where the
#    ban file is "the state that survives longest of all, server reboot
#    included".  A ban from yesterday would turn red everything that follows, and
#    the red would land on the wrong suspect.
# ⚠ It is a bench: in production throwing away that file is removing the protection from
#   everyone.
bersaglio_butta_il_ban()
{
	bash "$B0_ENTRA" --root "rm -f $B_BAN $B_BAN.nuovo $B_COMANDO"
	b0_inf "⛔ threw away the ban file «$B_BAN» and the socket «$B_COMANDO»"
	b0_inf "   (B0.2: it is the state that survives longest of all)"
}

# ⛔ The options every bench passes to its own Python program.  A single
#    line, so that the day one is added it is added in one place
#    only — and so that the target ends up in the log of EVERY round without
#    four benches having to remember it.
bersaglio_opzioni_python()
{
	printf -- '--bersaglio %s --porta %s --uscita %s --md5 %s --giro %s' \
		"$B_NOME" "$B_PORTA" "$B_ESITI" "${B_MD5:-ignota}" "${B_GIRO:-$(date +%Y%m%d-%H%M%S)}"
}
