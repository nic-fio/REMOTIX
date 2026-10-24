#!/bin/bash
# build.sh — builds the `child-msg` fuzz harness (libFuzzer + ASan + UBSan) of the messages the parent receives from the child.
#   bash benches/fuzz/child-msg/build.sh [OUT_DIR]       default OUT_DIR: /media/REMOTIX-15/misure/fuzz/child-msg-build
# Same image and method as rcp-msg/build.sh: compiles INSIDE `remotix-fuzz`, at `nice -n 19`, the REAL src/child.c
# (`#include`d by fuzz_child_msg.c, never modified; the tree is mounted read-only) + the log stub.  The product modules
# child.c calls (capture, encoder, session, input, mutter, kwin ...) are not linked: build-inner.txt generates a stub for
# each undefined symbol that TRAPS if the parser reaches it (OUT/stubs_missing.c).
# Output: OUT/bin/child-msg, OUT/seeds/child-msg/seed-NN, OUT/child-msg.dict.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../../.." && pwd)
OUT=${1:-/media/REMOTIX-15/misure/fuzz/child-msg-build}
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
$LOW podman run --rm --cpus=2 --userns=keep-id -v "$TREE:/albero:ro" -v "$OUT:/out" -w /albero/benches/fuzz/child-msg "$IMAGE" \
	sh /albero/benches/fuzz/child-msg/build-inner.txt > "$OUT/build.log" 2>&1 \
	|| { echo "⛔ compile failed; last lines of $OUT/build.log:"; grep -E "error|undefined reference" "$OUT/build.log" | head -n 30; exit 4; }
echo "built $OUT/bin/child-msg ($(ls "$OUT/seeds/child-msg" | wc -l) seeds, $(grep -c '^void' "$OUT/stubs_missing.c") trapping stubs)"
