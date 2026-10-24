#!/bin/bash
# build.sh — builds the `quic-conn` fuzz harness (libFuzzer + ASan + UBSan) of the QUIC connection limits (§11.40).
#   bash benches/fuzz/quic-conn/build.sh [OUT_DIR]       default OUT_DIR: /media/REMOTIX-15/misure/fuzz/quic-conn-build
# What it does: builds (once) the image `remotix-fuzz` from benches/fuzz/Containerfile.fuzz (FROM the product's build image
# + clang-19, libFuzzer and sanitizer runtimes, llvm-symbolizer), then compiles INSIDE it, at `nice -n 19`, the REAL
# src/transport.c (`#include`d by fuzz_quic_conn.c, never modified) over the played ngtcp2 of stubs_quic.c.  The tree is mounted
# read-only.  Output: OUT/bin/quic-conn, OUT/seeds/quic-conn/seed-NN, OUT/quic-conn.dict.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../../.." && pwd)
OUT=${1:-/media/REMOTIX-15/misure/fuzz/quic-conn-build}
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
$LOW podman run --rm --cpus=2 --memory=3g --network=none --pull=never --userns=keep-id -v "$TREE:/albero:ro" -v "$OUT:/out" -w /albero/benches/fuzz/quic-conn "$IMAGE" sh -ec '
	F="-g -O1 -fno-omit-frame-pointer -fsanitize=fuzzer-no-link,address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -I. -I/albero/src"
	for s in stubs_log stubs_quic fuzz_quic_conn; do clang $F -c $s.c -o /out/obj/$s.o; done
	clang -fsanitize=fuzzer,address,undefined /out/obj/fuzz_quic_conn.o /out/obj/stubs_quic.o /out/obj/stubs_log.o -o /out/bin/quic-conn
	python3 -I gen_seeds.py /out/seeds
	cp quic-conn.dict /out/quic-conn.dict' > "$OUT/build.log" 2>&1 \
	|| { echo "⛔ compile failed; last lines of $OUT/build.log:"; grep -E "error|undefined reference" "$OUT/build.log" | head -n 30; exit 4; }
echo "built $OUT/bin/quic-conn ($(ls "$OUT/seeds/quic-conn" | wc -l) seeds)"
