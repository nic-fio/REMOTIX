#!/bin/bash
# rinomina2-prova.sh — prove rinomina2.py on a COPY of the tree, never on the tree itself.
#
#   english-migration/rinomina2-prova.sh <copy> [--rilascio]
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
COPIA=$(cd "${1:?usage: rinomina2-prova.sh <copy> [--rilascio]}" && pwd)
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export CONTAINERS_CONF=${CONTAINERS_CONF:-/media/REMOTIX/src/full-english-uscite/rilascio-finale/rete-host.conf}
ROSSI=0
rosso() { echo "⛔ $*"; ROSSI=$((ROSSI + 1)); }
verde() { echo "✅ $*"; }

cd "$COPIA" || exit 2
git checkout -q -- . && git clean -qfd -e costruzione-uscita || exit 2
podman unshare rm -rf costruzione-uscita/rilasci costruzione-uscita/rilascio-* 2>/dev/null   # files of the build user namespace

# the benches' pure judges (--certifica: synthetic inputs, no terrain) on the tree as it is, once per
# commit: after the rename the same benches must give the same exit codes
certifica() {  # certifica <option> <out>
	local f
	for f in $(git ls-files 'banchi/*.py' | xargs grep -l -- "--certifica\|--$1" 2>/dev/null); do
		timeout 120 python3 "$f" "--$1" >/dev/null 2>&1 </dev/null
		echo "$? $f"
	done >"$2"
}
BASE=${TMPDIR:-/tmp}/rinomina2-certifica-$(git rev-parse --short HEAD).txt
if [ "${2:-}" = --rilascio ] || [ "${2:-}" = --certifica ]; then
	[ -s "$BASE" ] || { echo "== baseline: --certifica on the tree before the rename"; certifica certifica "$BASE"; }
fi
echo "== apply"
python3 "$QUI/rinomina2.py" apply --root "$COPIA" || exit 2
mapfile -t CAMBIATI < <(git diff --name-only)

echo "== 1. quotes, skipped files, protected lines"
python3 "$QUI/rinomina2.py" verify --root "$COPIA" && verde "quotes and protected regions unchanged" ||
	rosso "quotes or protected regions changed"

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
      if f.startswith(("src/", "banchi/")) and "/prodotto/" not in f and "rapporto" not in f]
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
G=$(printf '%s\n' "${CAMBIATI[@]}" | grep '^installatore/.*\.go$' | sed 's|^installatore/||')
if [ -n "$G" ]; then
	podman run --rm --network=none -v "$COPIA/installatore:/src:Z" -w /src docker.io/library/golang:1.25 \
		gofmt -w $G
fi
if (cd installatore && sh costruisci.sh prove) >"$COPIA/.rinomina2-go.log" 2>&1 &&
	! grep -qE '^(FAIL|gofmt:)' "$COPIA/.rinomina2-go.log"; then
	verde "installer: $(grep -c '^ok ' "$COPIA/.rinomina2-go.log") packages ok"
else
	rosso "installer"; grep -E '^(FAIL|gofmt:|#|vet:)|\.go:[0-9]+' "$COPIA/.rinomina2-go.log" | head -30
fi

echo "== 5. C: the server objects in the debian13 build image"
podman run --rm --network=none --userns=keep-id -v "$COPIA:/a" -w /a/src localhost/remotix-costruzione-debian13 \
	sh -c 'make -k -j8 GEMELLO=../banchi/rcp 2>&1' >"$COPIA/.rinomina2-c.log" 2>&1
ERR=$(grep -cE '(error|Error)[: ]' "$COPIA/.rinomina2-c.log")
OBJ=$(ls src/*.o 2>/dev/null | wc -l)
if [ "$ERR" = 0 ] && [ -x src/remotix ]; then
	verde "C: $OBJ objects, the server links, twins match"
else
	rosso "C build: $ERR error lines, $OBJ objects"; grep -E '(error|Error)[: ]' "$COPIA/.rinomina2-c.log" | head -30
fi
rm -f src/*.o src/*-protocol.c src/*-client-protocol.h

if [ "${2:-}" = --rilascio ] || [ "${2:-}" = --certifica ]; then
	echo "== 6. the benches' self-certification, against the same commit before the rename"
	OPT=$(python3 -c 'import json,sys; m=json.load(open(sys.argv[1]))["pairs"]
d={k.split("→")[0]:k.split("→")[1] for k in m}; print(d.get("certifica","certifica"))' "$COPIA/.rinomina2-applied.json")
	certifica "$OPT" "$COPIA/.rinomina2-certifica.txt"
	python3 - "$BASE" "$COPIA/.rinomina2-certifica.txt" "$COPIA/.rinomina2-applied.json" <<'EOF2' || ROSSI=$((ROSSI + 1))
import json, sys
a = dict(reversed(l.split(" ", 1)) for l in open(sys.argv[1]).read().split("\n") if l)
b = dict(reversed(l.split(" ", 1)) for l in open(sys.argv[2]).read().split("\n") if l)
same = [f for f in a if b.get(f) == a[f]]
diff = [(f, a[f], b.get(f)) for f in a if b.get(f) != a[f]]
green = sum(1 for f in a if a[f] == "0")
print("%s --certifica: %d benches, %d green before, same exit code after: %d" %
      ("✅" if not diff else "⛔", len(a), green, len(same)))
for f, x, y in diff:
    print("⛔ %s: %s before, %s after" % (f, x, y))
sys.exit(1 if diff else 0)
EOF2
fi

if [ "${2:-}" = --rilascio ]; then
	echo "== 7. packaging/rilascio.sh (debian13)"
	# the release script's own variables were renamed too: ask the applied table for their new names
	nuovo() { python3 -c 'import json,sys; m=json.load(open(sys.argv[1]))["pairs"]
d={k.split("→")[0]:k.split("→")[1] for k in m}; print(d.get(sys.argv[2], sys.argv[2]))' "$COPIA/.rinomina2-applied.json" "$1"; }
	env PATH=/media/REMOTIX/src/full-english-uscite/rilascio-finale/shim:$PATH "$(nuovo RX_SPORCO)=1" \
		"$(nuovo BERSAGLI)=debian13" "$(nuovo USCITA)=$COPIA/costruzione-uscita/rilasci" \
		bash packaging/rilascio.sh 0.99.0-1 >"$COPIA/.rinomina2-rilascio.log" 2>&1 &&
		verde "rilascio.sh debian13" || { rosso "rilascio.sh"; tail -25 "$COPIA/.rinomina2-rilascio.log"; }
fi
echo "== $ROSSI red"
exit $((ROSSI > 0))
