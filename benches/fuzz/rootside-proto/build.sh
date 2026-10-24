#!/bin/bash
# build.sh — builds the `rootside-proto` fuzz harness (libFuzzer + ASan + UBSan) the root side's pure API (the packet validator, the AUTH bounds, the grants).
#   bash benches/fuzz/rootside-proto/build.sh [OUT_DIR]       default OUT_DIR: /media/REMOTIX-15/misure/fuzz/rootside-proto-build
# Same image and method as child-msg/build.sh: compiles INSIDE `remotix-fuzz`, at `nice -n 19`, the REAL src/rootside.c
# (the tree is mounted read-only) + the log stub.  What rootside.c calls out of itself (child_birth, helper_*_root,
# render_grant_remotix_session ... phase D of the split, not in this tree yet) is not linked: build-inner.txt interposes it
# (dispatch) or generates a stub per undefined symbol that TRAPS if reached (proto, OUT/stubs_missing.c).
# Output: OUT/bin/rootside-proto, OUT/seeds/rootside-proto/seed-NN, OUT/rootside-proto.dict.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../../.." && pwd)
OUT=${1:-/media/REMOTIX-15/misure/fuzz/rootside-proto-build}
IMAGE=${IMAGE:-localhost/remotix-fuzz}
BASE=${BASE:-localhost/remotix-costruzione}
LOW="nice -n 19 ionice -c3"
podman image exists "$BASE" || { echo "⛔ image $BASE missing (src/build-in-container.sh)"; exit 3; }
mkdir -p "$OUT/bin" "$OUT/obj" "$OUT/seeds" || exit 2
if ! podman image exists "$IMAGE"; then
	echo "== building image $IMAGE (apt: clang-19, libFuzzer)"
	$LOW podman build --memory=4g -t "$IMAGE" --build-arg BASE="$BASE" -f "$HERE/../Containerfile.fuzz" "$HERE/.." > "$OUT/image-build.log" 2>&1 \
		|| { echo "⛔ image build failed:"; tail -n 20 "$OUT/image-build.log"; exit 3; }
fi
echo "== compiling (clang, address+undefined, libFuzzer)"
$LOW podman run --rm --cpus=2 --userns=keep-id -v "$TREE:/albero:ro" -v "$OUT:/out" -w /albero/benches/fuzz/rootside-proto "$IMAGE" \
	sh /albero/benches/fuzz/rootside-proto/build-inner.txt > "$OUT/build.log" 2>&1 \
	|| { echo "⛔ compile failed; last lines of $OUT/build.log:"; grep -E "error|undefined reference" "$OUT/build.log" | head -n 30; exit 4; }
echo "built $OUT/bin/rootside-proto ($(ls "$OUT/seeds/rootside-proto" | wc -l) seeds, $(grep -c '^void' "$OUT/stubs_missing.c" 2>/dev/null || echo 0) trapping stubs)"
