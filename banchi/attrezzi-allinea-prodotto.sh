#!/bin/bash
#
# attrezzi-allinea-prodotto.sh — ⛔ RUNS ON CHUWI, where the repository is.
# Brings the PRODUCT tree (`src/`) into the test machine, and
# REBUILDS.  It is the twin of `attrezzi-allinea-innesto.sh`, for the other
# of the two servers.
#
#   bash banchi/attrezzi-allinea-prodotto.sh guarda   just tells
#   bash banchi/attrezzi-allinea-prodotto.sh allinea  copy + build + terrain
#   bash banchi/attrezzi-allinea-prodotto.sh prova    ⭐ the positive check:
#                                                     builds a divergence
#                                                     on a copy and demands
#                                                     that `guarda` sees it
#
# Exits 0 if aligned · 1 if not (or if the alignment did not finish)
# 2 if it could not look · 3 if a step failed.
# ⛔ And «I could not look» is NOT «all good»: these are four outcomes, not two.
#
# ---------------------------------------------------------------------------
# ⛔ WHY IT EXISTS — NOBODY DID THE PROPAGATION
#
# `README.md`, box of the night between 11 and 12 Aug 2026, written
# right after the graft cure:
#
#     ⚠ And no tool does that propagation — the benches only check
#       it: that is why the misalignment stayed there for half a
#       day.
#
# ⛔ And the next day the same shape showed up again on the other tree.
# `[M]` 12 Aug 2026, evening: `/media/REMOTIX/src/remotix/rcp.c` was
# `1adce15b…` while the repository's `src/rcp.c` was `6d858886…`; `main.c`,
# `trasporto.c`, `webtransport.c`, `rcp.h`, `trasporto.h`, `webtransport.h` and
# the `Makefile` were old; and `aiutante.c` and `aiutante.h` — the two NEW files
# of the PAM cure — **were not on the server at all**.
#
# ⇒ The product running on 7448 ran without the PAM cure, and anyone who
#   had queried it would have measured yesterday's server believing they were measuring
#   today's.  It is the same shape already paid for twice: the misaligned
#   graft (six certifications saved by a hair by the terrain
#   check) and the house server that for thirteen hours ran on a deleted
#   binary (`01-casa-7448.sh`, box at the top).
#
# ⇒ The checks say WHAT is wrong; this file says HOW to put it back.
#
# ---------------------------------------------------------------------------
# ⛔⭐ THE TREE IS COPIED WHOLE, AND THE LIST IS NOT WRITTEN BY HAND
#
# It is the lesson this defect teaches more than any other: the two files that
# were missing **entirely** were the two NEW files.  A list copied by hand
# — `rcp.c rcp.h autenticazione.c`, as in the graft tool, where the
# files to bring are three by construction — would have brought the old ones here and
# forgotten the new ones, i.e. it would have left standing exactly the defect
# it must cure.  ⚠ It is the shape of **R12-A.45** and of gap **L2** of the
# terrain: a copied line ages in silence.
#
# ⭐ So: we enumerate `src/` and bring **everything that is there**, whatever
#    it is.  A new file gets in by itself.
#
# ⛔ And what is over there and not over here **is declared and not deleted**:
#    `remotix` and the `.o` files are the product of the build and must stay;
#    anything else is a finding for whoever reads, not something to throw away
#    on the quiet.
#
# ---------------------------------------------------------------------------
# ⛔ AND IT REFUSES IF THERE IS A GRAFTED FAULT — ON BOTH SIDES
#
# `attrezzi-allinea-innesto.sh` looks for the fault only in the target, and there it is
# right: B11 and B12 graft right inside `examples/`.  ⛔ Here the direction that
# matters most is **the other one**: if a fault ended up in the source tree
# (`01-p5-guasto-ritiro.py` takes `--pagina <path>` and nobody stops it
# from pointing at `src/pagina.html`; the fault catalogue names its targets
# by path, and a wrong path already cost R12-A.45) this
# tool would **propagate it into the house product** and rebuild it into
# the binary everybody queries.
#
# ⇒ Both trees are checked, and in both a finding stops
#   the round.  ⚠ And the mark **is not copied**: we ask `01-b12-guasti.py` for it,
#   because the day the catalogue changes it a needle copied here
#   would stop finding anything **and would turn green** (it is the cure
#   that `01-b0-terreno.sh` already applied to gap L2).
#
# ---------------------------------------------------------------------------
# ⛔⭐ AND «IDENTICAL» IS NOT ENOUGH, TWICE
#
#  1. **the binary must be newer than the sources.**  After the copy the files
#     carry the date of now: a binary built before is old even if
#     the content matches.  If the round stopped between the copy and the
#     build — for whoever wrote the graft tool a `timeout`
#     stopped it — a scene would remain in which the fingerprints match, `guarda`
#     would say «aligned», and the terrain would still reject it.  ⇒ We look
#     at the clock too.
#
#  2. ⛔ **the live process must be the one on disk.**  Aligned sources and a
#     rebuilt binary still leave the 7448 server running
#     on the old binary — which is **precisely** the thirteen-hour
#     defect.  ⇒ `allinea` ends by asking `01-casa-7448.sh stato`, and if the
#     answer is no **it does not declare itself finished**: it exits 1 and names the cure.
#
# ⛔ AND IT DOES NOT RESTART BY ITSELF.  On 7448 there may be other people's rounds, and
#    shutting the server down under whoever is measuring it is the damage this whole
#    family of tools exists to avoid.  ⇒ This file **propagates and
#    declares**; restarting is up to whoever holds the port, with the house file.
#
# ---------------------------------------------------------------------------
# ⛔ NEVER A REDIRECTION **AROUND** `ssh` OR `enter.sh`
#
# `FASI.md` §00-ambiente B3.3, paid for **five** times — the fifth on 12 Aug
# 2026 inside `attrezzi-allinea-innesto.sh`, i.e. in the file taken as a model
# here: `sudo -v -S -p` stuck **5 minutes and 28 seconds in silence**, with the sources
# already copied and the binary still old, i.e. the worst scene.
#
# ⭐ Hence the TWO carriers, which are the house rule (`01-p5-lancia.sh`):
#
#     SSH       reads — key, `BatchMode`, no `sudo`, clean stdout:
#               its stdout can be captured because there is no
#               question that can get lost;
#     SSH_ROOT  commands — `sshpw.py`, which types the password on a pty
#               because `enter.sh --root` calls `sudo`.  ⛔ Its stdout is NOT
#               captured and NOT redirected: the redirection goes **inside** the
#               quotes, to a file on the server, and the file is brought back with
#               `--get` and read here.
#
# ⛔ And we look at the OUTCOME of the builder, not at the binary being there afterwards:
#    `LEZIONI.md` §1.9 point 8 — a binary from two hours earlier answers «I exist»
#    just like one from now.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")

IND=${IND:-192.168.0.2}
UTE=${UTE:-nicfio}

# ⛔ The trees are DECLARED, like `SORG=` in `01-b0-terreno.sh`: there are five
#    `remotix` trees on that machine, and guessing which one is
#    the house one is the question D5 already paid for.
FONTE=${FONTE:-$RADICE/src}                    # here, on CHUWI
DEST=${DEST:-/media/REMOTIX/src/remotix}       # over there, seen from the HOST
CASA=${CASA:-/srv/src/01-casa-7448.sh}         # inside the container
TERRENO=${TERRENO:-/media/REMOTIX/src/01-b0-terreno.sh}
ENTRA=${ENTRA:-/media/REMOTIX/enter.sh}
# ⚠ The build log has a name of ITS OWN: two tools that
#   wrote the same file would read each other's outcome.  ⛔ And it is
#   named TWICE, because the same file has two names: `/media/REMOTIX/src`
#   on the host and `/srv/src` inside the container (`enter.sh` mounts it there).
#   Deriving one from the other with a substitution would be a
#   guessed path, and a guessed path changes one day.
LOG_LA=${LOG_LA:-/media/REMOTIX/src/attrezzi-allinea-prodotto-costr.log}
LOG_DENTRO=${LOG_DENTRO:-/srv/src/attrezzi-allinea-prodotto-costr.log}

SSH="ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new $UTE@$IND"
SCP="scp -q -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new"
SSH_ROOT=${SSH_ROOT:-python3 $RADICE/fondamenta/strumenti/sshpw.py}

VERDE=$'\033[1;32m'; ROSSO=$'\033[1;31m'; GIALLO=$'\033[1;33m'; GRIGIO=$'\033[0m'
ok()  { printf '    %sOK%s  %s\n' "$VERDE" "$GRIGIO" "$*"; }
ko()  { printf '    %sNO%s  %s\n' "$ROSSO" "$GRIGIO" "$*"; }
dub() { printf '    %s??%s  %s\n' "$GIALLO" "$GRIGIO" "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

AZIONE=${1:-guarda}
case "$AZIONE" in guarda|allinea|prova) ;;
*) echo "usage: $0 [guarda|allinea|prova]"; exit 2 ;; esac

T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

# ===========================================================================
# `prova` steps aside right away: it builds its own scene and calls `guarda` again
# on a COPY.  It sits at the bottom of the file, here there is only the jump.
if [ "$AZIONE" = prova ]; then
	PROVA=1
else
	PROVA=0
fi

# ---------------------------------------------------------------------------
log "0. The trees, declared (B0.1: declare AND verify)"
inf "source (CHUWI): $FONTE"
inf "product (NIC-OS): $DEST"
if [ ! -d "$FONTE" ]; then
	ko "⛔ the source tree is not there: $FONTE"
	exit 2
fi
# ⛔ The denominator: how many files I am about to compare.  «All the ones looked at
#    match» is true even when the ones looked at are zero (LEZIONI.md §1.9
#    rule 6).
FILE=$(cd "$FONTE" && find . -maxdepth 1 -type f -printf '%f\n' | sort)
N_QUI=$(printf '%s\n' "$FILE" | grep -c . )
# ⛔ And the same list with SPACES, so we can ask it «is it in there?».
#    ⚠ The first draft queried the newline one with `case " $FILE " in *" $n "*`,
#    which can never match: between one name and the next there is a newline, not a
#    space.  ⇒ The date check skipped EVERY file and the declaration of the
#    «only over there» files listed them ALL — two checks that checked
#    nothing, i.e. the D5 shape.  The first real round found it.
ELENCO=" $(printf '%s ' $FILE)"
if [ "$N_QUI" -eq 0 ]; then
	ko "⛔ there is no file in $FONTE: I align nothing and I do not say it is fine"
	exit 2
fi
ok "$N_QUI files in the source tree"

if [ "$PROVA" -eq 1 ]; then
	# --- the test scene is built before looking at anything
	SCRATCH=${SCRATCH:-/media/REMOTIX/src/tmp/prova-allinea-prodotto}
	SPORCA=${SPORCA:-Makefile}
	log "P. ⭐ THE POSITIVE CHECK — «can this tool say NO?»"
	inf "⛔ A tool that always said «aligned» would be worse than no"
	inf "   tool: it would give confidence (CODER.md §4.6).  Here the divergence is"
	inf "   BUILT, on a copy that belongs to nobody, and the expected result is"
	inf "   compared by the program — not by whoever reads (B0.4)."
	inf "test copy: $SCRATCH   ·   file to dirty: $SPORCA"

	$SSH "rm -rf $SCRATCH && mkdir -p $(dirname "$SCRATCH") && cp -R --preserve=timestamps $DEST $SCRATCH" || {
		ko "⛔ I could not make the test copy"; exit 2; }
	ok "copy made"

	printf '\n  ---- round 1: the two trees MATCH, and it is expected to stay silent\n'
	DEST=$SCRATCH bash "$0" guarda
	G1=$?
	printf '\n  ---- round 2: ONE file dirtied, and it is expected to say so\n'
	$SSH "printf '\n# line added by the test of attrezzi-allinea-prodotto.sh\n' >> $SCRATCH/$SPORCA" || {
		ko "⛔ I could not dirty $SPORCA"; $SSH "rm -rf $SCRATCH"; exit 2; }
	DEST=$SCRATCH bash "$0" guarda > "$T/giro2.txt" 2>&1
	G2=$?
	cat "$T/giro2.txt"

	$SSH "rm -rf $SCRATCH" || dub "⚠ the test copy was not deleted: $SCRATCH"

	log "P. The verdict of the test"
	FALLE=0
	if [ "$G1" -eq 0 ]; then
		ok "round 1: exit 0 — with identical trees it STAYS SILENT"
	else
		ko "⛔ round 1: exit $G1 instead of 0.  Either the trees were not aligned"
		ko "   before the test, or the tool says no even when there is"
		ko "   nothing to say — and then its «no»s are worth nothing."
		FALLE=$((FALLE+1))
	fi
	if [ "$G2" -eq 1 ]; then
		ok "round 2: exit 1 — it saw the built divergence"
	else
		ko "⛔ round 2: exit $G2 instead of 1: it did NOT see a changed file"
		FALLE=$((FALLE+1))
	fi
	if grep -q "DIFFERENT" "$T/giro2.txt" && grep -q "^.*$SPORCA DIFFERENT" "$T/giro2.txt"; then
		ok "and it says it of the RIGHT file: «$SPORCA DIFFERENT» appears in the output"
	else
		ko "⛔ it turned red but does not name «$SPORCA»: it is red for another"
		ko "   reason, and this is not a positive check"
		FALLE=$((FALLE+1))
	fi
	# ⛔ And ONLY ONE: a tool that declared ALL the files different would be
	#    red all the same, and could not point at anything.
	N_DIV=$(grep -c ' DIFFERENT — ' "$T/giro2.txt")
	if [ "$N_DIV" -eq 1 ]; then
		ok "and it names ONLY ONE ($N_DIV): it can tell apart, not just protest"
	else
		ko "⛔ it declares $N_DIV different files, and I dirtied one: it does not tell apart"
		FALLE=$((FALLE+1))
	fi
	if [ "$FALLE" -eq 0 ]; then
		printf '\n    %s⭐ THE POSITIVE CHECK PASSES: silent when they match, and when%s\n' "$VERDE" "$GRIGIO"
		printf '    %s   they diverge it says so, and says which.%s\n' "$VERDE" "$GRIGIO"
		exit 0
	fi
	printf '\n    %s⛔ THE POSITIVE CHECK DOES NOT PASS: %s things out of 4 do not add up.%s\n' "$ROSSO" "$FALLE" "$GRIGIO"
	printf '    %s   ⇒ the verdicts of this tool are worthless until it adds up.%s\n' "$ROSSO" "$GRIGIO"
	exit 1
fi

# ---------------------------------------------------------------------------
log "1. The fingerprints, file by file"

# ⛔ The stdout of `$SSH` is captured, and it can be: the key asks for nothing and
#    there is no `sudo` in between.  It is the carrier that READS.
if ! $SSH "find $DEST -maxdepth 1 -type f -exec md5sum {} +" > "$T/la-md5.txt" 2>"$T/la-md5.err"; then
	# ⛔ Three outcomes, not two: the tree is not there · it is there and empty · I could
	#    not look.  And the third does not wear the face of the second.
	if [ ! -s "$T/la-md5.txt" ] && grep -q 'No such file' "$T/la-md5.err"; then
		ko "⛔ the product tree is not there over there: $DEST"
	else
		dub "⛔ I could not read the fingerprints over there:"
		sed 's/^/        /' "$T/la-md5.err"
	fi
	exit 2
fi
$SSH "find $DEST -maxdepth 1 -type f -printf '%T@ %f\n'" > "$T/la-ore.txt" || {
	dub "⛔ I could not read the dates over there"; exit 2; }

DIVERSI=""
NUOVI=""
UGUALI=0
for f in $FILE; do
	a=$(md5sum "$FONTE/$f" | cut -d' ' -f1)
	b=$(awk -v n="$DEST/$f" '$2==n{print $1}' "$T/la-md5.txt")
	if [ -z "$b" ]; then
		ko "⛔ $f is NOT THERE over there — $a"
		NUOVI="$NUOVI $f"
		continue
	fi
	if [ "$a" = "$b" ]; then
		UGUALI=$((UGUALI+1))
	else
		ko "⛔ $f DIFFERENT — here $a · there $b"
		# ⭐ And we say HOW MANY lines differ: «different» and «different by a whole
		#    cure» send you to look in two different places.
		if $SCP "$UTE@$IND:$DEST/$f" "$T/la-$f"; then
			inf "   lines that change: $(diff "$FONTE/$f" "$T/la-$f" | grep -c '^[<>]')"
		else
			inf "   ⚠ I could not bring back the copy from over there: I do not count the lines"
		fi
		DIVERSI="$DIVERSI $f"
	fi
done
[ "$UGUALI" -gt 0 ] && ok "$UGUALI files out of $N_QUI already identical"

# ⛔ And what is over there and not over here is DECLARED — not deleted.
SOLO_LA=""
while read -r _imp per; do
	n=$(basename "$per")
	case "$ELENCO" in *" $n "*) continue ;; esac
	case "$n" in *.o|remotix) continue ;; esac   # the product of the build
	SOLO_LA="$SOLO_LA $n"
done < "$T/la-md5.txt"
if [ -n "$SOLO_LA" ]; then
	dub "⚠ over there there are files that do not exist here, and I do NOT touch them:$SOLO_LA"
	dub "   (I do not delete them: deleting on the quiet is like copying on the quiet)"
fi

# ---------------------------------------------------------------------------
log "2. Is the binary newer than the sources?"
BIN_ORA=$(awk '$2=="remotix"{print $1}' "$T/la-ore.txt")
VECCHIO=""
if [ -z "$BIN_ORA" ]; then
	ko "⛔ over there there is no «remotix» binary: the product has never been"
	ko "   built in $DEST"
	VECCHIO=" (binary missing)"
else
	while read -r ora nome; do
		[ "$nome" = remotix ] && continue
		case "$nome" in *.o) continue ;; esac
		case "$ELENCO" in *" $nome "*) ;; *) continue ;; esac
		if awk -v a="$ora" -v b="$BIN_ORA" 'BEGIN{exit !(a>b)}'; then
			VECCHIO="$VECCHIO $nome"
		fi
	done < "$T/la-ore.txt"
	# ⚠ And the files that are not over there yet count as «newer»: a
	#   binary that never compiled them is old by definition.
	[ -n "$NUOVI" ] && VECCHIO="$VECCHIO$NUOVI"
	if [ -n "$VECCHIO" ]; then
		ko "⛔ the binary is OLDER than:$VECCHIO"
		inf "   remotix: $(date -d "@${BIN_ORA%.*}" '+%Y-%m-%d %H:%M:%S %Z')  (CHUWI clock)"
		inf "   ⇒ it must be rebuilt even if the fingerprints match"
	else
		ok "the binary is newer than all the sources ($(date -d "@${BIN_ORA%.*}" '+%Y-%m-%d %H:%M:%S %Z'), CHUWI clock)"
	fi
fi

if [ -z "$DIVERSI" ] && [ -z "$NUOVI" ] && [ -z "$VECCHIO" ]; then
	ok "⭐ the product over there is already aligned with the sources, and the binary comes after"
	[ "$AZIONE" = guarda ] && exit 0
	inf "nothing to copy and nothing to rebuild: straight to the terrain"
fi

# ---------------------------------------------------------------------------
log "3. ⛔ Is there a grafted fault in one of the two trees?"
# ⚠ The mark is asked of the catalogue, not copied: if `01-b12-guasti.py`
#   changes it, a needle copied here would stop finding anything and this
#   check would turn GREEN.  It is the cure of gap L2 of the terrain.
MARCA12=$(python3 - "$QUI/01-b12-guasti.py" <<'PY'
import importlib.util, sys
s = importlib.util.spec_from_file_location("b12", sys.argv[1])
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
print(m.MARCA)
PY
)
if [ -z "$MARCA12" ]; then
	dub "⛔ I could not read the mark from 01-b12-guasti.py: I do NOT say that"
	dub "   there are no faults — I say I did not look"
	exit 2
fi
MARCA11=$(grep -m1 '^MARCA = ' "$QUI/01-b11-guasto-innesta.py" | cut -d'"' -f2)
[ -n "$MARCA11" ] || { dub "⛔ B11 mark not read: I do not look halfway"; exit 2; }
inf "needles read from the catalogues: «$MARCA12» · «$MARCA11»"

TROVATI=0
# --- over here (the tree we copy from): the direction that matters most
# ⛔ The status of `grep` is THREE facts and not two — `LEZIONI.md` §1.9 rule 1:
#    0 = found · 1 = not there (which is an ANSWER) · ≥2 = I could not
#    look (which is not an answer).  Only the third is a «??».
for m in "$MARCA12" "$MARCA11"; do
	grep -rlF -e "$m" "$FONTE" > "$T/qua-guasti.txt"
	s=$?
	if [ "$s" -eq 0 ]; then
		ko "⛔ «$m» appears IN THE SOURCE TREE:"
		sed 's/^/        /' "$T/qua-guasti.txt"
		TROVATI=$((TROVATI+1))
	elif [ "$s" -gt 1 ]; then
		dub "⛔ I could not search for «$m» in $FONTE (grep: $s)"
		exit 2
	else
		ok "no trace of «$m» in $FONTE"
	fi
done
# --- over there (the tree we write on)
for m in "$MARCA12" "$MARCA11"; do
	$SSH "grep -lF -e '$m' -- $DEST/*" > "$T/la-guasti.txt"
	s=$?
	if [ "$s" -eq 0 ]; then
		ko "⛔ «$m» appears IN THE PRODUCT over there:"
		sed 's/^/        /' "$T/la-guasti.txt"
		TROVATI=$((TROVATI+1))
	elif [ "$s" -gt 1 ]; then
		dub "⛔ I could not search for «$m» in $DEST (exit $s)"
		exit 2
	else
		ok "no trace of «$m» in $DEST"
	fi
done
if [ "$TROVATI" -gt 0 ]; then
	ko "⛔ I TOUCH NOTHING: there is a grafted fault."
	ko "   If it is in the SOURCE tree, copying it would put it into the product that"
	ko "   everybody queries; if it is in the PRODUCT, copying over it would"
	ko "   remove it FROM UNDER whoever is measuring it — and that round would say «the"
	ko "   bench did not turn red» of a bench whose"
	ko "   accused was taken out of its hands."
	ko "   ⇒ Wait for the round to finish, or remove it with «--togli»."
	exit 3
fi

if [ "$AZIONE" = guarda ]; then
	inf "«guarda» stops here: to copy and rebuild, «allinea»"
	exit 1
fi

# ---------------------------------------------------------------------------
if [ -n "$DIVERSI" ] || [ -n "$NUOVI" ]; then
	log "4. Copying the sources into the product"
	for f in $DIVERSI $NUOVI; do
		$SCP "$FONTE/$f" "$UTE@$IND:$DEST/$f" || {
			ko "⛔ copying «$f» failed"; exit 3; }
		a=$(md5sum "$FONTE/$f" | cut -d' ' -f1)
		$SSH "md5sum $DEST/$f" > "$T/dopo.txt" || {
			ko "⛔ «$f» copied but I could not read it back"; exit 3; }
		b=$(cut -d' ' -f1 < "$T/dopo.txt")
		if [ "$a" = "$b" ]; then
			ok "$f copied, and the fingerprints now match ($a)"
		else
			ko "⛔ $f copied but the fingerprints do NOT match: $a ≠ $b"
			exit 3
		fi
	done
fi

# ---------------------------------------------------------------------------
log "5. Rebuilding — with the house file, and looking at the OUTCOME"
# ⭐ The build is not rewritten: `01-casa-7448.sh costruisci` already does it,
#    and it knows where the tree is, which twin to compare, and that the outcome is
#    read from `costruisci.sh` and not from `test -x` (CODER.md §4.1, depending).
#
# ⛔⭐ AND THE REDIRECTION GOES **INSIDE** THE QUOTES.  `enter.sh --root` calls
#     `sudo`, the question goes out on stderr, and a redirection placed around it
#     swallows it: the command hangs forever, in silence — and the symptom
#     is not an error, it is a «slow» tool.  `FASI.md` §00-ambiente B3.3,
#     paid for five times, the last one right in the file taken as a model here.
$SSH "rm -f $LOG_LA" || dub "⚠ I could not remove the old log: what I read might be from before"
$SSH_ROOT "bash $ENTRA --root \"bash $CASA costruisci > $LOG_DENTRO 2>&1\""
S_COSTR=$?
$SCP "$UTE@$IND:$LOG_LA" "$T/costr.log" || dub "⚠ the build log could not be brought back"
if [ "$S_COSTR" -eq 0 ]; then
	ok "⭐ remotix rebuilt"
	[ -f "$T/costr.log" ] && tail -3 "$T/costr.log" | sed 's/^/        /'
else
	ko "⛔ the build FAILED (exit $S_COSTR): the binary that is there is"
	ko "   the old one, and now the sources have changed under it —"
	ko "   i.e. the WORST scene.  The error:"
	if [ -f "$T/costr.log" ]; then
		tail -30 "$T/costr.log" | sed 's/^/        /'
	else
		ko "   ⛔ and there is not even the log: I read nothing"
	fi
	exit 3
fi

# ---------------------------------------------------------------------------
log "6. ⛔ And the terrain says it, not me"
# ⚠ ON THE HOST, not inside the container: `01-b0-terreno.sh` reads
#   `/media/REMOTIX/...`, which inside the chroot has another name.
$SSH "bash $TERRENO prodotto"
S_TERR=$?

# ---------------------------------------------------------------------------
log "7. ⛔ And is the live process running the new binary?"
inf "aligned sources and a rebuilt binary are NOT enough: the running server"
inf "still runs the old one, and that is the thirteen-hour defect."
$SSH_ROOT "bash $ENTRA --root \"bash $CASA stato\""
S_STATO=$?

printf '\n'
if [ "$S_TERR" -ne 0 ]; then
	printf '    %s⛔ the terrain does NOT hold (exit %s): do not launch benches.%s\n' "$ROSSO" "$S_TERR" "$GRIGIO"
	exit 1
fi
if [ "$S_STATO" -ne 0 ]; then
	printf '    %s⛔ the SOURCES are aligned and the binary is from now, but the%s\n' "$ROSSO" "$GRIGIO"
	printf '    %s   running server is NOT executing that binary (exit %s).%s\n' "$ROSSO" "$S_STATO" "$GRIGIO"
	printf '       ⇒ The cure, by whoever holds the port:\n'
	printf '            bash %s --root "bash %s riaccendi"\n' "$ENTRA" "$CASA"
	printf '       ⚠ I do not do it: on 7448 there may be rounds by other people,\n'
	printf '         and shutting a server down under whoever is measuring it is the damage that\n'
	printf '         this family of tools exists to avoid.\n'
	exit 1
fi
printf '    %s⭐ product aligned: sources, binary and process say the same thing.%s\n' "$VERDE" "$GRIGIO"
exit 0
