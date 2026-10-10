#!/bin/bash
#
# 01-b0-terreno.sh — ⛔ IS THE SERVER THE ONE I BELIEVE?  Runs ON THE SERVER.
#
#   bash 01-b0-terreno.sh innesto     before a bench against :7447
#   bash 01-b0-terreno.sh prodotto    before a bench against :7448
#
# Exits 0 if the terrain holds, 1 if not, 2 if it could not look.
# ⛔ And "I could not look" is NOT "all good": there are three outcomes, not two.
#
# ---------------------------------------------------------------------------
# ⛔ WHY IT EXISTS — twice in one day, on 11 Aug 2026
#
# `B0.1` says the initial state is **declared and verified**.  This file
# was born because twice, on the same day, a bench was **green on a
# terrain that was not the one we believed** — and in both cases the bench
# had no reason whatsoever to notice.
#
#   `[M]` **R12-A.45** · `01-b2-ngtcp2-wt-innesta.py --togli` puts back as they were
#         the **tracked** files of `examples/`, and among them there is
#         `http3_server_proto_codec.cc`, where the **RCP graft of B3** lives.
#         ⇒ Removing the B2 graft takes B3 away too, silently.  The server
#         ran for an hour **without RCP**, sending back the client's bytes,
#         and ⛔ **the certification of B2 passed all the same**: its
#         probe reads the QUIC parameters and knows nothing of RCP.
#         ⭐ I caught it BY CHANCE, while testing something else.
#
#   `[M]` **R12-A.44** · the user `prova`, on which four benches rest, was not
#         created by any script: it had been made by hand.
#
# ⭐ The form is a single one, and it has a name in the project: **the file is there** versus
#    **the file is the one I just built** — already paid for on B11 on 10
#    Aug, and on B6 with the binary compiled with the `CONGEDO` removed (R12-A.6).
#
# ---------------------------------------------------------------------------
# ⚠ WHAT THIS CHECK DOES **NOT** PROVE, said first
#
# That the server is CORRECT.  It proves that it is **the one declared**: the pieces
# that must be there are there, the binary is newer than the sources it
# says it comes from, and no certification fault has been left on it.
# ⛔ A server can pass all of this and be full of defects: that is what
#    the benches look for.  Here we only check that they look in the right
#    place.
#
# ---------------------------------------------------------------------------
# ⛔⭐ AND THIS FILE CARRIED EXACTLY THE DEFECT IT EXISTS TO
#     PREVENT — defect **D5**, 12 Aug 2026.
#
# Line 235 looked for the product binary in `remotix/build/remotix`, which
# **never existed**: `src/Makefile` declares `NOME := remotix` and
# builds it next to the sources, and `src/costruisci.sh` does `make -C "$QUI"`
# after deleting `"$QUI/remotix"`.  ⇒ The `[ -f ... ]` **always** fell
# into the "I do not judge it" branch, and that check was a **fixed UNKNOWN**: it did not
# check anything, and nobody read it any more.
#
# ⛔ It is form **E8** — "empty" and "forbidden" look the same —
#    applied to the tool that should prevent it for the others.  The path
#    was not guessed a second time: it is read in `src/Makefile` and
#    in `src/costruisci.sh`, and it is the same one already declared by
#    `01-b0-bersaglio.sh` (`B_ESE="$B0_DENTRO/remotix/remotix"`).
#
# ⭐ Hence the four things this round changed, and each answers
#    "which input would turn it RED?":
#
#   1. the real path, `$SORG/remotix`                ⇒ red if the binary is
#                                                       older than a .c
#   2. the binary that is MISSING is a **trouble**, not an unknown — the branch that
#      excused it is gone, and `piu_nuovo()` judges as on the graft
#   3. the comparison is with **all** the compiled sources, not with `rcp.c` alone:
#      with `rcp.c` alone a `main.c` newer than the binary stayed GREEN
#   4. ⚠ **the place is a single one per tree, but the trees are NOT one**:
#      `[M]` 12 Aug 2026, five executable `remotix` under `/media/REMOTIX/src`
#      (the home product, `01-p5-copia-7522`, `01-b12-copie/p1-remotix`,
#      `01-b12-copie/p5-remotix`, `coder-r12/src`).  ⇒ the tree is **declared**
#      with `SORG=`, and if inside the tree there were two binaries the check
#      **says so** instead of picking one.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
ESEMPI=$FUORI/b2/ngtcp2/examples
BINARIO_INNESTO=$FUORI/b2/ngtcp2/build/examples/bsslserver

# ⛔ The product tree is DECLARED, as in `01-p1-prodotto.sh` (SORG):
#    the binary always sits next to its sources, but there is more than one tree
#    on this machine and the «prodotto» target is the home one,
#    that is the 7448 server.  Whoever wants to judge another names it.
SORG=${SORG:-$FUORI/remotix}
BINARIO_PRODOTTO=$SORG/remotix

BERSAGLIO=${1:-}
case "$BERSAGLIO" in
innesto|prodotto) ;;
*) echo "usage: $0 {innesto|prodotto}" >&2; exit 2 ;;
esac

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'
GRIGIO=$'\033[0m'; NETTO=$'\033[1m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }

GUAI=0
IGNOTI=0
GUARDATI=0

# ⛔ conta() distinguishes THREE outcomes: the file is not there · it is there and the count is N ·
#    I could not read it.  It prints the number, or "?".
#
# ⛔⭐ AND THE FIRST DRAFT WAS WRONG RIGHT HERE, in the same form cured
#     this morning on S1b (finding A31): `grep -c` exits **1** when it finds
#     nothing — which is not an error, it is the answer "zero" — and my
#     `|| printf '?'` stuck a `?` AFTER the zero already printed.
#     Out came the string "0\n?", and every "must not be there" check
#     declared fault traces on a clean file: five false reds in one
#     go, inside the file that exists to prevent false reds.
#     ⭐ The exit status of `grep` must be read: 0 = found · 1 = not found ·
#        ≥2 = I could not read.  They are three, and only the third is "?".
conta() # $1 = file, $2 = needle
{
	local n s
	if [ ! -f "$1" ]; then printf '?\n'; return; fi
	n=$(grep -c -F -- "$2" "$1" 2>/dev/null)
	s=$?
	if [ "$s" -ge 2 ] || [ -z "$n" ]; then printf '?\n'; else printf '%s\n' "$n"; fi
}

# almeno() # $1 = description, $2 = file, $3 = needle, $4 = minimum
almeno()
{
	local n
	GUARDATI=$((GUARDATI + 1))
	n=$(conta "$2" "$3")
	if [ "$n" = "?" ]; then
		dub "⛔ $1: I could not read «$(basename "$2")»"
		dub "   ⚠ and «I could not look» is not «all good»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	if [ "$n" -ge "$4" ]; then
		ok "$1: $n occurrences (expected ≥ $4)"
	else
		ko "⛔ $1: $n occurrences, at least $4 are needed"
		GUAI=$((GUAI + 1))
	fi
}

# nessuno() — a needle that must NOT be there (the certification faults)
nessuno()
{
	local n
	GUARDATI=$((GUARDATI + 1))
	n=$(conta "$2" "$3")
	if [ "$n" = "?" ]; then
		dub "⛔ $1: I could not read «$(basename "$2")»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	if [ "$n" -eq 0 ]; then
		ok "$1: no trace"
	else
		ko "⛔ $1: $n traces LEFT ON the code"
		ko "   A forgotten fault poisons every later measurement, and"
		ko "   nobody will know it was there."
		GUAI=$((GUAI + 1))
	fi
}

# ⛔ IS THE BINARY NEWER THAN THE SOURCES?  It is the other half of "the file is there":
#    a cured source and an old binary are the trap of R12-A.6, where
#    the source was healthy and the binary a liar.
piu_nuovo() # $1 = binary, $2.. = sources
{
	local bin=$1; shift
	local vecchi=0 f
	GUARDATI=$((GUARDATI + 1))
	if [ ! -f "$bin" ]; then
		ko "⛔ the binary is not there: $bin"
		GUAI=$((GUAI + 1))
		return
	fi
	for f in "$@"; do
		[ -f "$f" ] || continue
		if [ "$f" -nt "$bin" ]; then
			ko "⛔ «$(basename "$f")» is NEWER than the binary:"
			ko "   the running server does not contain that source"
			vecchi=$((vecchi + 1))
		fi
	done
	if [ "$vecchi" -eq 0 ]; then
		ok "the binary is newer than all the sources it declares"
	else
		GUAI=$((GUAI + 1))
	fi
}

# ⛔ IS THE PLACE A SINGLE ONE?  It is the other half of the cure of D5: knowing WHERE
#    the binary is is not enough if the binary can be in two places.
#
#    Inside ONE tree the place is one by construction — `src/Makefile` puts
#    `$(NOME)` next to the sources and `costruisci.sh` deletes the old one
#    first — ⛔ but a `build/remotix` left there by an out-of-tree build,
#    or a forgotten copy, would raise again exactly the
#    question D5 paid for: *which of the two is running?*
#    ⭐ Here we do not choose: we count them and say so.  EXISTENCE is judged by
#       `piu_nuovo()`; this only checks that there is not MORE THAN ONE.
posto_unico() # $1 = tree, $2 = the binary I am about to judge
{
	local albero=$1 atteso=$2 trovati s n
	GUARDATI=$((GUARDATI + 1))
	if [ ! -d "$albero" ]; then
		dub "⛔ the product tree is not there: $albero"
		dub "   ⚠ and «I could not look» is not «all good»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	# ⚠ No `2>/dev/null`: if `find` could not look it says so, and an
	#   "I could not" must not have the face of a "there is only one".
	trovati=$(find "$albero" -maxdepth 2 -type f -name remotix -perm -u+x)
	s=$?
	if [ "$s" -ne 0 ]; then
		dub "⛔ I could not list the binaries under «$albero» (find: $s)"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	if [ -z "$trovati" ]; then n=0; else n=$(printf '%s\n' "$trovati" | wc -l); fi
	if [ "$n" -le 1 ]; then
		ok "a single place where the binary can be: $atteso"
		[ "$n" -eq 0 ] && inf "(today there is no binary: the check below judges it)"
	else
		ko "⛔ $n «remotix» binaries inside the same tree:"
		printf '        %s\n' $trovati
		ko "   ⇒ I do not know which one is running, and picking one would be D5 all over again."
		ko "   Throw away the extra one, or declare the tree with SORG=."
		GUAI=$((GUAI + 1))
	fi
}

# ===========================================================================
# ⛔⭐ THE B12 FAULTS ARE LOOKED FOR WHERE B12 PUTS THEM — gap L2, 12 Aug 2026.
#
# ⛔ WHAT WAS THERE BEFORE, AND WHY IT WAS WORSE THAN NOTHING.
#
# This file had four lines written by hand:
#
#     nessuno "guasti di B12 nel codec"        examples/http3_server_proto_codec.cc
#     nessuno "guasti di B12 in rcp.c"         examples/rcp.c
#     nessuno "guasti di B12 in server.cc"     examples/server.cc
#     nessuno "guasti di B12 in remotix/rcp.c" remotix/rcp.c        ← ⛔ THIS ONE
#
# The last one **could not turn red in any case**: `01-b12-guasti.py`
# does not graft into `remotix/rcp.c` and never has — by declared
# design, because *"an original is never broken"* (its §"LA CARTELLA
# DELLE COPIE").  ⇒ A check green by construction, which GUARDATI counted
# as one of the checks done.  ⛔ It is worse than an absent check: whoever
# reads "no trace" believes someone looked.
#
# ⚠ And the first three were true but **partial**: of the fifteen faults of the catalogue
#   they covered five.  The places nobody looked at — `[M]` 12 Aug 2026,
#   read from the catalogue, not deduced — were `01-b12-copie/p1-remotix/pagina.c`,
#   `01-b12-copie/p5-remotix/pagina.c`, `sera-b10-remotix/autenticazione.c`,
#   the three copies of benches in `01-b12-copie/` and `01-p5-copia-7522/pagina.html`.
#
# ⭐ THE CURE: the list is not copied, IT IS ASKED OF THE CATALOGUE.  A new fault
#    with a new target comes in here by itself; a line copied by hand
#    ages silently, and it is the exact form of R12-A.45 — the file that a
#    script put back as it was and that nobody else looked at.
#
# ⚠ And the mark is read from there too (`MARCA`): searching for a string
#   copied here would mean that the day B12 changes it this
#   check no longer finds anything **and turns green**.
# ===========================================================================
CATALOGO=$QUI/01-b12-guasti.py

# Returns: first line = the MARCA · following lines = «CODES<TAB>path».
posti_dei_guasti()
{
	python3 - "$CATALOGO" <<'PY'
import importlib.util
import os
import sys

s = importlib.util.spec_from_file_location("b12", sys.argv[1])
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
print(m.MARCA)
ordine, di_chi = [], {}
for sigla in sorted(m.GUASTI):
    g = m.GUASTI[sigla]
    # ⛔ `copia-di-file` (today: B13) OVERWRITES a whole file — a PEM
    #    certificate — and leaves no string inside it to look for.  There
    #    the residue is judged by the fingerprint that `--togli` puts back, not by this
    #    sieve: looking for the mark there would be a check green by
    #    construction, that is the defect this cure removes.
    if g["costa"] == "copia-di-file":
        continue
    d = os.path.realpath(m.risolvi(g["dove"]))
    if d not in di_chi:
        ordine.append(d)
        di_chi[d] = []
    di_chi[d].append(sigla)
for d in ordine:
    print("%s\t%s" % (",".join(di_chi[d]), d))
PY
}

guasti_rimasti_addosso()
{
	local righe s marca n riga sigle percorso
	local posti=0 guardati=0 sporchi=0 assenti=0

	righe=$(posti_dei_guasti)
	s=$?
	# ⛔ No `2>/dev/null` above: if the catalogue does not load, the Python
	#    error is seen, and this check declares itself UNKNOWN instead of
	#    sieving zero files and calling it "no trace".
	if [ "$s" -ne 0 ] || [ -z "$righe" ]; then
		GUARDATI=$((GUARDATI + 1))
		dub "⛔ I could not ask 01-b12-guasti.py where it grafts (exit $s)"
		dub "   ⚠ and zero files sieved is not «no fault left on»"
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	marca=$(printf '%s\n' "$righe" | head -1)

	# ⭐ THE POSITIVE CONTROL, ON THE SAME TOOL (`LEZIONI.md` §1.9
	#    rule 2).  Can `conta()` find the mark in a file that certainly
	#    has it?  If it does not find it, every "no trace" below is worth zero —
	#    and it is the same morning in which a search did not even find the 133
	#    system applications.
	GUARDATI=$((GUARDATI + 1))
	local finto
	finto=$(mktemp) || { dub "⛔ no temporary file: sieve not certified"; IGNOTI=$((IGNOTI + 1)); return; }
	printf 'una riga qualunque\n/* %s prova */\n' "$marca" >"$finto"
	n=$(conta "$finto" "$marca")
	rm -f "$finto"
	if [ "$n" = "?" ] || [ "$n" -lt 1 ]; then
		dub "⛔ the sieve does NOT find the mark «$marca» in a file that has it:"
		dub "   every «no trace» below would be an empty green."
		IGNOTI=$((IGNOTI + 1))
		return
	fi
	ok "the sieve can find «$marca» where it is (positive control)"

	while IFS=$'\t' read -r sigle percorso; do
		[ -n "${percorso:-}" ] || continue
		posti=$((posti + 1))
		if [ ! -e "$percorso" ]; then
			# ⛔ ABSENT IS NOT UNKNOWN, AND HERE THE DIFFERENCE CAN BE PROVED.
			#    The targets of B12 are COPIES that `prepara_copia()` redoes from
			#    scratch at every round: as long as the copy does not exist, it cannot
			#    carry anything on it.  ⇒ it is not "I could not look",
			#    and it must not cost an UNKNOWN that would stop every round.
			assenti=$((assenti + 1))
			continue
		fi
		GUARDATI=$((GUARDATI + 1))
		guardati=$((guardati + 1))
		n=$(conta "$percorso" "$marca")
		if [ "$n" = "?" ]; then
			dub "⛔ I could not read «$percorso» (faults $sigle)"
			dub "   ⚠ and «I could not look» is not «all good»"
			IGNOTI=$((IGNOTI + 1))
			continue
		fi
		if [ "$n" -ne 0 ]; then
			ko "⛔ $n fault traces LEFT ON «$percorso»"
			ko "   it is the target of: $sigle"
			ko "   A forgotten fault poisons every later measurement, and"
			ko "   nobody will know it was there.  It is removed with:"
			ko "     python3 $CATALOGO --togli ${sigle%%,*}"
			GUAI=$((GUAI + 1))
			sporchi=$((sporchi + 1))
		fi
	done <<< "$(printf '%s\n' "$righe" | tail -n +2)"

	# ⛔ THE DENOMINATOR (`LEZIONI.md` §1.9 rule 4): "no trace" is not
	#    a datum until it says INSIDE HOW MANY FILES.
	if [ "$sporchi" -eq 0 ] && [ "$guardati" -gt 0 ]; then
		ok "no B12 fault left on: $guardati files sieved out of"
		ok "   $posti targets declared by the catalogue ($assenti do not exist today)"
	elif [ "$guardati" -eq 0 ]; then
		dub "⛔ none of the $posti targets of the catalogue exists on this machine:"
		dub "   this check looked at nothing, and it is not a green"
		IGNOTI=$((IGNOTI + 1))
	fi
	inf "the absent targets are copies that 01-b12-guasti.py redoes at every round:"
	inf "  a copy that is not there cannot carry a fault on it"
}

printf '\n%s== ⛔ The terrain: is the server «%s» the one I believe?%s\n' \
	"$NETTO" "$BERSAGLIO" "$GRIGIO"

if [ "$BERSAGLIO" = innesto ]; then
	# ── The two grafts, and BOTH of them live in server.cc ───────────────
	# ⚠ It is the point where they stepped on each other's toes: the `--togli` of one
	#   puts back as it was a file the other had written.
	almeno "RCP graft (B3) in the codec"    "$ESEMPI/http3_server_proto_codec.cc" "rcp_"        20
	almeno "WebTransport graft (B2) in the codec" "$ESEMPI/http3_server_proto_codec.cc" "REMOTIX B2" 5
	almeno "the host-side ban (B3) in server.cc" "$ESEMPI/server.cc"            "REMOTIX B3"  5
	almeno "the transport parameters (B2) in server.cc" "$ESEMPI/server.cc"      "REMOTIX B2"  1

	# ── The three files B3 copies into examples/ ─────────────────────────
	for f in rcp.c rcp.h autenticazione.c; do
		GUARDATI=$((GUARDATI + 1))
		if [ -f "$ESEMPI/$f" ]; then
			ok "examples/$f is there"
		else
			ko "⛔ examples/$f is MISSING: the RCP graft is not complete"
			GUAI=$((GUAI + 1))
		fi
	done

	# ── ⭐ And the copy must be THE SOURCE, not a stale copy ─────────────
	GUARDATI=$((GUARDATI + 1))
	if [ -f "$ESEMPI/rcp.c" ] && [ -f "$FUORI/rcp/rcp.c" ]; then
		A=$(md5sum "$ESEMPI/rcp.c" | cut -d' ' -f1)
		B=$(md5sum "$FUORI/rcp/rcp.c" | cut -d' ' -f1)
		if [ "$A" = "$B" ]; then
			ok "examples/rcp.c is identical to rcp/rcp.c ($A)"
		else
			ko "⛔ examples/rcp.c is NOT rcp/rcp.c:"
			ko "   compiled: $A"
			ko "   source  : $B"
			ko "   ⇒ the server measures a version nobody is reading"
			GUAI=$((GUAI + 1))
		fi
	else
		dub "⛔ I could not compare rcp.c: one of the two is not there"
		IGNOTI=$((IGNOTI + 1))
	fi

	# ⚠ The **B12** faults are no longer here: they are sieved by
	#   `guasti_rimasti_addosso()`, at the bottom of this file, asking the
	#   catalogue where they really go — and its targets are not three, they are
	#   nine (gap L2, 12 Aug 2026).  Those of **B11** stay written by
	#   hand because another program grafts them,
	#   `01-b11-guasto-innesta.py`, which has no catalogue.
	nessuno "B11 faults in the codec"  "$ESEMPI/http3_server_proto_codec.cc" "REMOTIX B11 GUASTO"
	nessuno "B11 faults in rcp.c"      "$ESEMPI/rcp.c"                       "REMOTIX B11 GUASTO"
	# ⛔ ⭐ AND THE THIRD FILE OF B11, which until 12 Aug 2026 nobody
	#    looked at: `01-b11-guasto-innesta.py` writes into THREE files — `rcp.c`,
	#    `http3_server_proto_codec.cc` and `http3_server_proto_codec.h` (the
	#    member `bool b11_fatto_{false}; // ⚠ REMOTIX B11 GUASTO`).  A
	#    `--togli` that left the header behind was invisible to
	#    this tool: the same form as R12-A.45, which is the reason
	#    this file exists.
	nessuno "B11 faults in the codec header" \
		"$ESEMPI/http3_server_proto_codec.h" "REMOTIX B11 GUASTO"

	# ⛔ The HEADERS are among the sources the binary declares: without them,
	#    a `touch examples/rcp.h` — or the codec header rewritten by
	#    `--togli` — left this check GREEN on a stale binary.
	#    It is the same defect as D5 on the other target, where only
	#    `rcp.c` was compared.
	piu_nuovo "$BINARIO_INNESTO" \
		"$ESEMPI/http3_server_proto_codec.cc" "$ESEMPI/http3_server_proto_codec.h" \
		"$ESEMPI/server.cc" \
		"$ESEMPI/rcp.c" "$ESEMPI/rcp.h" "$ESEMPI/autenticazione.c"
else
	# ── The product ─────────────────────────────────────────────────────
	# ⛔ `src/rcp.c` and `banchi/rcp/rcp.c` MUST stay identical byte for
	#    byte: it is the invariant on which the fact rests that the two servers
	#    speak the same protocol.
	GUARDATI=$((GUARDATI + 1))
	if [ -f "$FUORI/remotix/rcp.c" ] && [ -f "$FUORI/rcp/rcp.c" ]; then
		A=$(md5sum "$FUORI/remotix/rcp.c" | cut -d' ' -f1)
		B=$(md5sum "$FUORI/rcp/rcp.c" | cut -d' ' -f1)
		if [ "$A" = "$B" ]; then
			ok "remotix/rcp.c is identical to rcp/rcp.c ($A)"
		else
			ko "⛔ the two rcp.c are NO longer identical — the invariant is broken"
			ko "   product: $A"
			ko "   benches: $B"
			GUAI=$((GUAI + 1))
		fi
	else
		dub "⛔ I could not compare the two rcp.c"
		IGNOTI=$((IGNOTI + 1))
	fi
	# ⛔ HERE THERE WAS `nessuno "guasti di B12 in remotix/rcp.c"`, AND IT COULD NOT
	#    TURN RED: `01-b12-guasti.py` does not graft into the originals, by
	#    declared design.  The reason at length is next to
	#    `guasti_rimasti_addosso()`, which now sieves the REAL targets — and
	#    sieves them on both targets of this script, because a forgotten
	#    fault poisons anyone's measurements, not only those
	#    of the graft.

	# ── ⛔ THE PRODUCT BINARY — the cure of D5 ───────────────────────────
	inf "product tree: $SORG   (changed with SORG=<path>)"
	posto_unico "$SORG" "$BINARIO_PRODOTTO"

	# ⛔ ALL the sources that go into the binary, not `rcp.c` alone:
	#    `src/Makefile` compiles TEN of them, and with `rcp.c` alone a `main.c`
	#    newer than the binary left the check GREEN.  The
	#    headers are in because the Makefile declares them as
	#    prerequisites of the objects.
	#
	# ⚠ `pagina.html` and `remotix.pam` are NOT in, and the reason must be said:
	#    the server reads them at STARTUP (`pagina_apri()`), it does not compile them
	#    in.  One of them newer than the binary is not a stale
	#    binary, and putting it here would be a red pointed at the wrong
	#    suspect.
	#
	# ⛔ And the binary that is MISSING is a TROUBLE, not an unknown — it is the branch that
	#    D5 used to look at nothing.  `piu_nuovo()` can say so by itself,
	#    and it is what it already does on the «innesto» target.
	piu_nuovo "$BINARIO_PRODOTTO" \
		"$SORG"/*.c "$SORG"/*.h "$SORG/Makefile"
fi

# ── ⛔ THE B12 FAULTS, LOOKED FOR WHERE B12 PUTS THEM (gap L2) ──────────────
#    Outside the if on purpose: the target says which SERVER is about to be used,
#    not which files can be dirty.
guasti_rimasti_addosso

# ---------------------------------------------------------------------------
# ⛔ THE DENOMINATOR — `LEZIONI.md` §1.9 rule 6.  "All those tested
#    went well" is true even when those tested are zero.
printf '\n    == what this check really looked at\n'
inf "checks done:          $GUARDATI"
printf '    %s%3d%s  ⛔ troubles\n' "$ROSSO" "$GUAI" "$GRIGIO"
printf '    %s%3d%s  ⚠ UNKNOWN (I could not look)\n' "$GIALLO" "$IGNOTI" "$GRIGIO"

if [ "$GUARDATI" -eq 0 ]; then
	ko "⛔ ZERO checks: this round says nothing, and «good terrain»"
	ko "   would be a lie"
	exit 2
fi
if [ "$GUAI" -gt 0 ]; then
	printf '\n    %s⛔ THE TERRAIN DOES NOT HOLD: do not launch benches on this server.%s\n' \
		"$ROSSO" "$GRIGIO"
	ko "What would come out of it would not speak about the product."
	exit 1
fi
if [ "$IGNOTI" -gt 0 ]; then
	printf '\n    %s⚠ the terrain holds ON WHAT I COULD LOOK AT%s\n' \
		"$GIALLO" "$GRIGIO"
	inf "$IGNOTI checks could not be done: they are not a green"
	exit 1
fi
printf '\n    %s⭐ the terrain holds: %d checks of %d%s\n' \
	"$VERDE" "$GUARDATI" "$GUARDATI" "$GRIGIO"
exit 0
