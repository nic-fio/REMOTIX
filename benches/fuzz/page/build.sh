#!/bin/bash
# build.sh — builds the `page` fuzz harness (libFuzzer + ASan + UBSan) of the HTTP listener src/page.c.
#   bash benches/fuzz/page/build.sh [OUT_DIR]       default OUT_DIR: /media/REMOTIX-15/misure/fuzz/page-build
# Same image and method as rcp-msg/child-msg: compiles INSIDE `remotix-fuzz`, at `nice -n 19`, the REAL src/page.c (`#include`d by
# fuzz_page.c, never modified) and src/rcp.c (linked, for rcp_key_address) over the played sockets and OpenSSL of fuzz_page.c; the tree
# is mounted read-only.  Whatever else rcp.c needs becomes a stub that traps (OUT/stubs_missing.c).  zlib is the real one.
# Output: OUT/bin/page, OUT/seeds/page/seed-NN, OUT/page.dict.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../../.." && pwd)
OUT=${1:-/media/REMOTIX-15/misure/fuzz/page-build}
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
$LOW podman run --rm --cpus=2 --memory=3g --network=none --pull=never --userns=keep-id -v "$TREE:/albero:ro" -v "$OUT:/out" -w /albero/benches/fuzz/page "$IMAGE" \
	sh /albero/benches/fuzz/page/build-inner.txt > "$OUT/build.log" 2>&1 \
	|| { echo "⛔ compile failed; last lines of $OUT/build.log:"; grep -E "error|undefined reference" "$OUT/build.log" | head -n 30; exit 4; }
echo "built $OUT/bin/page ($(ls "$OUT/seeds/page" | wc -l) seeds, $(grep -c '^void' "$OUT/stubs_missing.c") trapping stubs)"
