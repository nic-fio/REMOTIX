#!/bin/bash
# rinomina2-prova.sh — prove rinomina2.py on a COPY of the tree, never on the tree itself.
#
#   english-migration/rinomina2-prova.sh <copy> [--fase-b | --fase-c] [--certifica | --rilascio]
#
# --fase-c proves step 2 (the file and folder names: fase_c.py and english-migration/fase-c-moves.tsv, or
# $FASE_C_MOVES): it applies the moves, regenerates the manual, runs `fase_c.py check` (every move done,
# no reference to an old path left outside the allowed list) and then every check below under the NEW
# paths (benches/, installer/, benches/rcp as the twin); 5b compares the server's strings with the old
# file names mapped to the new ones, 6 compares the benches' exit codes and outputs modulo the path
# names (fase_c.py map), 7 builds the debian13 release with the new R14 denylists, and 8 runs
# `docs/sources/build.py --controlla` (PYTHONPATH=$FASE_C_PYLIB, default /media/REMOTIX/strumenti/pylib).
#
# --fase-b proves phase B instead (fase_b.py, the table english-migration/fase-b-tabella.tsv or
# $FASE_B_TABLE, $FASE_B_SINCE = the commit the tables were written against): it applies the table,
# regenerates the manual when its sources changed, and replaces the phase-A-only checks — 1 by
# `fase_b.py check` (structure: only the table's names changed; leftovers listed), 5b by the strings
# of the server mapped through the table (.rodata legitimately differs), 6 by the same exit code and
# the same output once both are mapped through the table (fase_b.py map).
#
# <copy> is a git worktree (or archive) of the commit to rename.  The script resets it to its
# HEAD, applies the plan, reformats Go, and runs the checks RINOMINA.md §6 lists:
#   1. «…» quotes of every .md unchanged, skipped files unchanged, protected lines unchanged
#   2. bash -n on every shell script, compile() on every Python file
#   3. node --check on every <script> of the page and of the bench pages
#   4. the installer: gofmt, go vet, go test (installatore/costruisci.sh prove)
#   5. C: make of the server objects and the twin check in the debian13 build image
#   6. with --rilascio: packaging/rilascio.sh (debian13 only) into the copy's costruzione-uscita
# Exit 0 only if everything passes.  Needs podman; CONTAINERS_CONF is set to the host-network
# configuration of the release track.
set -u
COPIA=$(cd "${1:?usage: rinomina2-prova.sh <copy> [--fase-b] [--certifica | --rilascio]}" && pwd)
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
shift
FASEB=0 FASEC=0 CERT=0 RILASCIO=0
for a in "$@"; do
	case $a in
	--fase-b) FASEB=1 ;;
	--fase-c) FASEC=1 ;;
	--certifica) CERT=1 ;;
	--rilascio) CERT=1 RILASCIO=1 ;;
	*) echo "usage: rinomina2-prova.sh <copy> [--fase-b | --fase-c] [--certifica | --rilascio]" >&2; exit 2 ;;
	esac
done
[ "$FASEB$FASEC" = 11 ] && { echo "--fase-b and --fase-c: one at a time" >&2; exit 2; }
FC_MOVES=${FASE_C_MOVES:-$QUI/fase-c-moves.tsv}
fc() { python3 "$QUI/fase_c.py" "$@"; }
# the tree's own folders: old names before step 2, new ones after it (the baseline always runs on the old)
B=banchi INST=installatore
FB_TABLE=${FASE_B_TABLE:-$QUI/fase-b-tabella.tsv}
fb() { python3 "$QUI/fase_b.py" "$@"; }
# the phase-B spelling of a public name (the name itself when the table does not rename it)
fbnew() { if [ "$FASEB" = 1 ]; then fb new --table "$FB_TABLE" -- "$1"; else echo "$1"; fi; }
export CONTAINERS_CONF=${CONTAINERS_CONF:-/media/REMOTIX/src/full-english-uscite/rilascio-finale/rete-host.conf}
[ -f "$CONTAINERS_CONF" ] || { echo "⚠ $CONTAINERS_CONF is missing: podman's own configuration"; unset CONTAINERS_CONF; }
ROSSI=0
rosso() { echo "⛔ $*"; ROSSI=$((ROSSI + 1)); }
verde() { echo "✅ $*"; }

cd "$COPIA" || exit 2
git reset -q --hard && git clean -qfd -e costruzione-uscita || exit 2
# step 2 moves folders: what an earlier proof left under the new names (ignored files too) must go first
[ "$FASEC" = 1 ] && { git clean -qfdx -e costruzione-uscita || exit 2; }
podman unshare rm -rf costruzione-uscita/rilasci costruzione-uscita/rilascio-* 2>/dev/null   # files of the build user namespace

# the benches' pure judges (--certifica: synthetic inputs, no terrain) on the tree as it is, once per
# commit: after the rename the same benches must give the same exit code AND the same output (phase A
# changes no string, so the text they print is the same, digits aside).  The list is made once, on the
# tree before the rename, and the same files run after it: a bench whose option comes from a shared
# runner (15-suite: S.esegui) has no «--certifica» in its own text and was missed before (R07 F1).
# 12-client-veri and 12-c20-veri drive real browsers against a real server (default URL: the rete11
# box on 8511, R12 incident): never run here
certifica_list() {
	git ls-files 'banchi/*.py' | grep -v -e '^banchi/12-client-veri\.py$' -e '^banchi/12-c20-veri\.py$' | while read -r f; do
		if grep -q -- "--certifica" "$f" || { grep -q "S\.esegui" "$f" && grep -q "def certifica" "$f"; }; then
			echo "$f"
		fi
	done
}
certifica() {  # certifica <option> <list> <outdir>
	local f o
	mkdir -p "$3"
	while read -r f; do
		o=$3/$(echo "$f" | tr / _).out
		env -u REMOTIX_PAROLA -u "$PAROLA" timeout 120 python3 "$f" "--$1" >"$o" 2>&1 </dev/null
		echo "$? $f"
	done <"$2" >"$3/exit.txt"
}
PAROLA=REMOTIX_PAROLA
BASE=${TMPDIR:-/tmp}/rinomina2-certifica-$(git rev-parse --short HEAD)
if [ "$CERT" = 1 ]; then
	if [ ! -s "$BASE/exit.txt" ]; then
		echo "== baseline: --certifica on the tree before the rename"
		rm -rf "$BASE"; mkdir -p "$BASE"; certifica_list >"$BASE/list.txt"
		certifica certifica "$BASE/list.txt" "$BASE"
	fi
fi
if [ "$FASEC" = 1 ]; then
	echo "== apply (step 2: $FC_MOVES)"
	if ! fc apply --root "$COPIA" --moves "$FC_MOVES" >"$COPIA/.rinomina2-apply.log" 2>&1; then
		grep '^⛔' "$COPIA/.rinomina2-apply.log" | head -40; exit 2
	fi
	grep -E '^(✅|⚠|⛔)' "$COPIA/.rinomina2-apply.log" | head -20
	B=benches INST=installer
	# the manual is generated: regenerate it from the rewritten sources
	if PYTHONPATH=${FASE_C_PYLIB:-/media/REMOTIX/strumenti/pylib} \
		python3 docs/sources/build.py >"$COPIA/.rinomina2-docs.log" 2>&1; then
		verde "the manual regenerated"
	else rosso "the manual does not regenerate"; tail -5 "$COPIA/.rinomina2-docs.log"; fi
	mapfile -t CAMBIATI < <(git diff --name-only -M HEAD)
	echo "== 1. every move done, no reference to an old path left"
	fc check --root "$COPIA" --moves "$FC_MOVES" >"$COPIA/.rinomina2-check.log" 2>&1
	R1=$?
	grep -E '^(⛔|✅)' "$COPIA/.rinomina2-check.log" | head -30
	echo "   (the whole list: $COPIA/.rinomina2-check.log)"
	[ "$R1" = 0 ] || rosso "step 2 left old paths or missed a move"
elif [ "$FASEB" = 1 ]; then
	echo "== apply (phase B: $FB_TABLE)"
	if ! fb apply --root "$COPIA" --table "$FB_TABLE" ${FASE_B_SINCE:+--since "$FASE_B_SINCE"} >"$COPIA/.rinomina2-apply.log" 2>&1; then
		grep '^⛔' "$COPIA/.rinomina2-apply.log" | head -40; exit 2
	fi
	tail -2 "$COPIA/.rinomina2-apply.log"
	PAROLA=$(fbnew REMOTIX_PAROLA)
	# the manual is generated: regenerate it when its sources changed (pygments and Pillow live in
	# FASE_B_PYDEPS: the host has neither)
	if [ -n "$(git diff --name-only -- docs/sources)" ]; then
		if PYTHONPATH=${FASE_B_PYDEPS:-/media/REMOTIX/src/full-english-uscite/fase-b-pydeps} \
			python3 docs/sources/build.py >"$COPIA/.rinomina2-docs.log" 2>&1; then
			verde "the manual regenerated"
		else rosso "the manual does not regenerate"; tail -5 "$COPIA/.rinomina2-docs.log"; fi
	fi
	mapfile -t CAMBIATI < <(git diff --name-only)
	echo "== 1. structure (only the table's names changed) and leftovers"
	fb check --root "$COPIA" --table "$FB_TABLE" >"$COPIA/.rinomina2-check.log" 2>&1
	R1=$?
	grep -E '^(⛔|✅|⚠ leftovers)' "$COPIA/.rinomina2-check.log" | head -30
	echo "   (every leftover: $COPIA/.rinomina2-check.log)"
	[ "$R1" = 0 ] || rosso "phase B changed more than the table's names"
else
echo "== apply"
python3 "$QUI/rinomina2.py" apply --root "$COPIA" || exit 2
mapfile -t CAMBIATI < <(git diff --name-only)

echo "== 1. quotes, skipped files, protected lines"
python3 "$QUI/rinomina2.py" verify --root "$COPIA" && verde "quotes and protected regions unchanged" ||
	rosso "quotes or protected regions changed"

echo "== 1b. strings: every changed file keeps its string literals (phase A)"
python3 "$QUI/fase_a.py" check --root "$COPIA" || rosso "a string literal or more than a name changed"
fi

echo "== 2. shell and Python syntax"
n=0; while read -r f; do bash -n "$f" 2>/dev/null || { rosso "bash -n $f"; }; n=$((n + 1)); done < \
	<(git ls-files '*.sh' | grep -v '^fondamenta/')
verde "bash -n: $n scripts"
python3 - <<'EOF' || ROSSI=$((ROSSI + 1))
import subprocess, sys
fs = [f for f in subprocess.check_output(["git", "ls-files", "*.py"]).decode().split()
      if not f.startswith(("fondamenta/", "english-migration/"))]
bad = 0
for f in fs:
    try:
        compile(open(f, encoding="utf-8").read(), f, "exec")
    except SyntaxError as e:
        bad += 1
        print("⛔ python", f, e)
print("✅ python compile: %d files" % len(fs) if not bad else "⛔ python: %d failures" % bad)
sys.exit(1 if bad else 0)
EOF

echo "== 3. page JavaScript"
J=$COPIA/.rinomina2-js; rm -rf "$J"; mkdir -p "$J"
python3 - "$J" <<'EOF'
import re, subprocess, sys, os
out = sys.argv[1]
fs = [f for f in subprocess.check_output(["git", "ls-files", "*.html"]).decode().split()
      if f.startswith(("src/", "banchi/", "benches/")) and "/prodotto/" not in f and "rapporto" not in f]
for f in fs:
    t = open(f, encoding="utf-8").read()
    for i, m in enumerate(re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script\s*>", t, re.S | re.I)):
        body = m.group(1)
        if "__" in body and re.search(r"__[A-Z_]+__", body):
            body = re.sub(r"__[A-Z_]+__", "0", body)       # server-side placeholders
        open(os.path.join(out, f.replace("/", "__") + ".%d.js" % i), "w").write(body)
EOF
if podman run --rm --network=none -v "$J:/j:ro" docker.io/library/node:22 \
	sh -c 'r=0; for f in /j/*.js; do node --check "$f" 2>/tmp/e || { echo "⛔ $f"; head -5 /tmp/e; r=1; }; done; exit $r'; then
	verde "node --check: $(ls "$J" | wc -l) scripts"
else rosso "page JavaScript"; fi
rm -rf "$J"

echo "== 4. installer (gofmt -w on the changed Go files, then vet and test)"
G=$(printf '%s\n' "${CAMBIATI[@]}" | grep "^$INST/.*\.go\$" | sed "s|^$INST/||")
if [ -n "$G" ]; then
	podman run --rm --network=none -v "$COPIA/$INST:/src:Z" -w /src docker.io/library/golang:1.25 \
		gofmt -w $G
fi
if (cd "$INST" && sh "$([ -f costruisci.sh ] && echo costruisci.sh || echo build.sh)" prove) >"$COPIA/.rinomina2-go.log" 2>&1 &&
	! grep -qE '^(FAIL|gofmt:)' "$COPIA/.rinomina2-go.log"; then
	verde "installer: $(grep -c '^ok ' "$COPIA/.rinomina2-go.log") packages ok"
else
	rosso "installer"; grep -E '^(FAIL|gofmt:|#|vet:)|\.go:[0-9]+' "$COPIA/.rinomina2-go.log" | head -30
fi

echo "== 5. C: the server objects in the debian13 build image"
podman run --rm --network=none --userns=keep-id -v "$COPIA:/a" -w /a/src localhost/remotix-costruzione-debian13 \
	sh -c "make -k -j8 GEMELLO=../$B/rcp 2>&1" >"$COPIA/.rinomina2-c.log" 2>&1
ERR=$(grep -cE '(error|Error)[: ]' "$COPIA/.rinomina2-c.log")
OBJ=$(ls src/*.o 2>/dev/null | wc -l)
if [ "$ERR" = 0 ] && [ -x src/remotix ]; then
	verde "C: $OBJ objects, the server links, twins match"
else
	rosso "C build: $ERR error lines, $OBJ objects"; grep -E '(error|Error)[: ]' "$COPIA/.rinomina2-c.log" | head -30
fi
# 5b. phase A changes no string: the server's read-only data (.rodata: every literal, every format, the
# names assert() and g_return_if_fail() print) must be byte-identical to the binary built before the rename.
# Phase B renames strings, so there the .rodata legitimately differs: the strings of the two binaries,
# each mapped through the table to one canonical spelling, must be the same multiset (the strings of
# .rodata only: the rest of the binary holds the build directory)
R=$(mktemp -d); mkdir -p "$R/a"; git archive HEAD src banchi/rcp | tar -x -C "$R/a"
podman run --rm --network=none --userns=keep-id -v "$COPIA:/n" -v "$R:/r" localhost/remotix-costruzione-debian13 \
	sh -c 'cd /r/a/src && make -j8 GEMELLO=../banchi/rcp >/dev/null 2>&1;
	       objcopy -O binary --only-section=.rodata /r/a/src/remotix /r/prima.rodata &&
	       objcopy -O binary --only-section=.rodata /n/src/remotix /r/dopo.rodata &&
	       strings -a -n 4 /r/prima.rodata >/r/prima.str && strings -a -n 4 /r/dopo.rodata >/r/dopo.str' >/dev/null 2>&1
if [ "$FASEC" = 1 ]; then
	# step 2 changes the file names the binary holds (__FILE__, the page's name): the strings before,
	# with the old names mapped to the new ones, must be the strings after
	if [ -s "$R/prima.str" ] && [ -s "$R/dopo.str" ]; then
		fc map --root "$COPIA" <"$R/prima.str" | sort >"$R/prima.map"
		sort "$R/dopo.str" >"$R/dopo.map"
		# the linker merges a string into a longer one that ends with it (transport.c inside
		# webtransport.c): a string only before that is the tail of a string after is not a difference
		python3 - "$R/prima.map" "$R/dopo.map" <<'EOF3'
import sys, collections
a, b = (collections.Counter(open(f, errors="replace").read().split("\n")) for f in sys.argv[1:3])
only = a - b
dopo = list(b)
for s in list(only):
    if any(x.endswith(s) and x != s for x in dopo):
        a[s] -= only[s]
open(sys.argv[1], "w").write("\n".join(sorted(a.elements())))
open(sys.argv[2], "w").write("\n".join(sorted(b.elements())))
EOF3
		if cmp -s "$R/prima.map" "$R/dopo.map"; then
			verde "C: the server's strings, old file names mapped, are the ones before step 2 ($(wc -l <"$R/dopo.map"))"
		else
			rosso "C: the server's strings differ beyond the file names"
			diff "$R/prima.map" "$R/dopo.map" | grep '^[<>]' | head -20
		fi
	else rosso "C: the server before or after step 2 did not build"; fi
elif [ "$FASEB" = 1 ]; then
	if [ -s "$R/prima.str" ] && [ -s "$R/dopo.str" ]; then
		fb map --side before --table "$FB_TABLE" <"$R/prima.str" | sort >"$R/prima.map"
		fb map --side after --table "$FB_TABLE" <"$R/dopo.str" | sort >"$R/dopo.map"
		if cmp -s "$R/prima.map" "$R/dopo.map"; then
			verde "C: the server's strings, mapped through the table, are the ones of the binary before phase B ($(wc -l <"$R/dopo.map"))"
		else
			rosso "C: the server's strings differ beyond the table's names"
			diff "$R/prima.map" "$R/dopo.map" | grep '^[<>]' | head -20
		fi
	else rosso "C: the server before or after phase B did not build"; fi
elif [ -s "$R/prima.rodata" ] && cmp -s "$R/prima.rodata" "$R/dopo.rodata"; then
	verde "C: the server's .rodata is byte-identical to the one built before the rename ($(stat -c %s "$R/dopo.rodata") bytes)"
else rosso "C: the server's .rodata differs from the one built before the rename (or did not build)"; fi
podman unshare rm -rf "$R" 2>/dev/null || rm -rf "$R"
rm -f src/*.o src/*-protocol.c src/*-client-protocol.h

if [ "$CERT" = 1 ]; then
	echo "== 6. the benches' self-certification, against the same commit before the rename"
	if [ "$FASEB" = 1 ]; then
		OPT=$(fbnew --certifica); OPT=${OPT#--}
	elif [ "$FASEC" = 1 ]; then
		OPT=certifica
	else
		OPT=$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1]))["pairs"]
d={k.split("→")[0]:k.split("→")[1] for k in m}; print(d.get("certifica","certifica"))' "$COPIA/.rinomina2-applied.json")
	fi
	rm -rf "$COPIA/.rinomina2-certifica"
	LISTA=$BASE/list.txt
	if [ "$FASEC" = 1 ]; then          # the same benches, under their new paths
		LISTA=$COPIA/.rinomina2-certifica-list.txt
		fc map --root "$COPIA" --paths <"$BASE/list.txt" >"$LISTA"
	fi
	certifica "$OPT" "$LISTA" "$COPIA/.rinomina2-certifica"
	if [ "$FASEC" = 1 ]; then          # judged under the old names, outputs mapped: see out() below
		fc map --root "$COPIA" --paths --back <"$COPIA/.rinomina2-certifica/exit.txt" >"$COPIA/.rinomina2-certifica/exit.new"
		while read -r e f; do
			n=$(echo "$f" | fc map --root "$COPIA" --paths)
			mv "$COPIA/.rinomina2-certifica/$(echo "$n" | tr / _).out" "$COPIA/.rinomina2-certifica/$(echo "$f" | tr / _).out" 2>/dev/null
		done <"$COPIA/.rinomina2-certifica/exit.new"
		mv "$COPIA/.rinomina2-certifica/exit.new" "$COPIA/.rinomina2-certifica/exit.txt"
	fi
	python3 - "$BASE" "$COPIA/.rinomina2-certifica" "$([ "$FASEB" = 1 ] && echo "$FB_TABLE")" "$QUI" \
		"$([ "$FASEC" = 1 ] && echo "$COPIA")" <<'EOF2' || ROSSI=$((ROSSI + 1))
import os, re, sys
A, B = sys.argv[1], sys.argv[2]
ROWS = None
if sys.argv[3]:                         # phase B: both outputs mapped through the table
    sys.path.insert(0, sys.argv[4])
    import fase_b
    ROWS = fase_b.read_merged(sys.argv[3])
FC = None
if len(sys.argv) > 5 and sys.argv[5]:   # step 2: the output before, its old path names mapped to the new
    sys.path.insert(0, sys.argv[4])
    import fase_c
    FC = fase_c.Mapper(sys.argv[5])
def ex(d):
    return dict(reversed(l.split(" ", 1)) for l in open(os.path.join(d, "exit.txt")).read().split("\n") if l)
def out(d, f):
    t = open(os.path.join(d, f.replace("/", "_") + ".out"), errors="replace").read()
    if ROWS is not None:
        t = fase_b.map_text(t, ROWS, "before" if d == A else "after")
    if FC is not None:
        t = FC.text(t) if d == A else t
        t = re.sub(r"[ \t]+", " ", t)     # a longer name moves the padding of a column
    # a traceback quotes source lines and function names (renamed): keep only its last line
    t = re.sub(r"Traceback \(most recent call last\):\n(?:[ \t].*\n)*", "Traceback\n", t)
    return re.sub(r"[0-9]+", "0", re.sub(r"/tmp/[^\s'\"]*", "/tmp/X", t))
a, b = ex(A), ex(B)
bad = 0
for f in sorted(a):
    why = []
    if b.get(f) != a[f]:
        why.append("exit %s before, %s after" % (a[f], b.get(f)))
    oa, ob = out(A, f), out(B, f)
    if ob.count("Traceback") > oa.count("Traceback"):
        why.append("a Traceback after the rename")
    if oa != ob:
        la, lb = oa.split("\n"), ob.split("\n")
        d = next((i for i in range(max(len(la), len(lb))) if (la[i:i+1] or [None]) != (lb[i:i+1] or [None])), 0)
        why.append("output differs at line %d: %r / %r" % (d + 1, (la[d:d+1] or [""])[0][:90], (lb[d:d+1] or [""])[0][:90]))
    if why:
        bad += 1
        print("⛔ %s: %s" % (f, "; ".join(why)))
green = sum(1 for f in a if a[f] == "0")
print("%s --certifica: %d benches (%d green before); same exit code and same output after: %d" %
      ("✅" if not bad else "⛔", len(a), green, len(a) - bad))
sys.exit(1 if bad else 0)
EOF2
fi

if [ "$RILASCIO" = 1 ]; then
	echo "== 7. packaging/rilascio.sh (debian13)"
	REL=packaging/rilascio.sh
	if [ "$FASEC" = 1 ]; then
		[ -f "$COPIA/.rinomina2-applied.json" ] || echo '{"pairs": []}' >"$COPIA/.rinomina2-applied.json"
		REL=$(echo "$REL" | fc map --root "$COPIA" --paths)
	fi
	# the release script's own variables were renamed too: ask the applied table for their new names
	nuovo() { [ "$FASEB" = 1 ] && { fbnew "$1"; return; }; python3 -c 'import json,sys; m=json.load(open(sys.argv[1]))["pairs"]
d={k.split("→")[0]:k.split("→")[1] for k in m}; print(d.get(sys.argv[2], sys.argv[2]))' "$COPIA/.rinomina2-applied.json" "$1"; }
	env PATH=/media/REMOTIX/src/full-english-uscite/rilascio-finale/shim:$PATH "$(nuovo RX_SPORCO)=1" \
		"$(nuovo BERSAGLI)=debian13" "$(nuovo USCITA)=$COPIA/costruzione-uscita/rilasci" \
		bash "$REL" 0.99.0-1 >"$COPIA/.rinomina2-rilascio.log" 2>&1 &&
		verde "rilascio.sh debian13" || { rosso "rilascio.sh"; tail -25 "$COPIA/.rinomina2-rilascio.log"; }
fi
if [ "$FASEC" = 1 ]; then
	echo "== 8. the manual's own check (docs/sources/build.py --controlla)"
	if PYTHONPATH=${FASE_C_PYLIB:-/media/REMOTIX/strumenti/pylib} \
		python3 docs/sources/build.py --controlla >"$COPIA/.rinomina2-controlla.log" 2>&1; then
		verde "build.py --controlla"
	else rosso "build.py --controlla"; tail -15 "$COPIA/.rinomina2-controlla.log"; fi
fi
echo "== $ROSSI red"
exit $((ROSSI > 0))
