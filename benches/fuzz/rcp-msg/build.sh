#!/bin/bash
# build.sh — builds the `rcp-msg` fuzz harness (libFuzzer + ASan + UBSan) of the messages the server receives from the browser.
#   bash benches/fuzz/rcp-msg/build.sh [OUT_DIR]       default OUT_DIR: /media/REMOTIX-15/misure/fuzz/rcp-msg-build
# Same image and method as quic-conn/build.sh: compiles INSIDE `remotix-fuzz`, at `nice -n 19`, the REAL src/rcp.c
# (`#include`d by fuzz_rcp_msg.c, never modified; the tree is mounted read-only) + the log stub.
# Output: OUT/bin/rcp-msg, OUT/seeds/rcp-msg/seed-NN, OUT/rcp-msg.dict.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../../.." && pwd)
OUT=${1:-/media/REMOTIX-15/misure/fuzz/rcp-msg-build}
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
$LOW podman run --rm --cpus=2 --userns=keep-id -v "$TREE:/albero:ro" -v "$OUT:/out" -w /albero/benches/fuzz/rcp-msg "$IMAGE" sh -ec '
	F="-g -O1 -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -I. -I/albero/src"
	for s in stubs_log fuzz_rcp_msg; do clang $F -c $s.c -o /out/obj/$s.o; done
	clang -fsanitize=fuzzer,address,undefined /out/obj/fuzz_rcp_msg.o /out/obj/stubs_log.o -o /out/bin/rcp-msg
	python3 -I gen_seeds.py /out/seeds
	cp rcp-msg.dict /out/rcp-msg.dict' > "$OUT/build.log" 2>&1 \
	|| { echo "⛔ compile failed; last lines of $OUT/build.log:"; grep -E "error|undefined reference" "$OUT/build.log" | head -n 30; exit 4; }
echo "built $OUT/bin/rcp-msg ($(ls "$OUT/seeds/rcp-msg" | wc -l) seeds)"
