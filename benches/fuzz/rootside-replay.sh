#!/bin/bash
# rootside-replay.sh — REPLAY of the seeds of the rootside-proto and rootside-dispatch fuzz targets with gcc and the sanitizers, no libFuzzer (what the tablet has).
#   bash benches/fuzz/rootside-replay.sh [OUT_DIR]        run from anywhere; the tree is mounted read-only, OUT_DIR (default: a temp dir) gets objects and seeds.
# Repeatable: (1) `rootside_version.py sync` rewrites the version bytes of the two dictionaries from src/rootside_proto.h (RXR_VERSION) — nothing else carries a
# version: the rootside-proto seeds are ops the harness turns into packets with RXR_VERSION, and the rootside-dispatch gen_seeds.py reads the same header;
# (2) each target is built like its build-inner.txt (the REAL src/rootside.c, trap stubs for what it reaches outside) but with gcc and replay main(); (3) the seeds are generated and replayed.
# Exit 0 = both replays clean.  Needs podman and the image localhost/remotix-costruzione (gcc, python3, the build libraries).
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
OUT=${1:-$(mktemp -d)}
IMAGE=${IMAGE:-localhost/remotix-costruzione}
python3 "$HERE/rootside_version.py" sync || exit 2
mkdir -p "$OUT" || exit 2
podman image exists "$IMAGE" || { echo "image $IMAGE missing"; exit 3; }
podman run --rm --network=none --cpus=2 --memory=3g -v "$TREE:/albero:ro" -v "$OUT:/out" "$IMAGE" sh -c '
set -e
PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon"
F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -I/albero/src $(pkg-config --cflags $PK)"
L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm"
cd /out
# ---- rootside-proto
P=/albero/benches/fuzz/rootside-proto
gcc $F -I$P -c $P/stubs_log.c -o sl.o
gcc $F -I$P -DRXFUZZ_REAL_ROOTSIDE -c $P/fuzz_rootside_proto.c -o fp.o
gcc $F -I$P -c /albero/src/rootside.c -o rs.o
gcc $F -c /albero/benches/fuzz/rootside-replay.c -o rp.o
gcc -fsanitize=address,undefined fp.o rs.o sl.o rp.o $L -o p0 2> link1.log || true
{ echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u | while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB: rootside-proto reached $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > sm.c
gcc $F -c sm.c -o sm.o
gcc -fsanitize=address,undefined fp.o rs.o sl.o sm.o rp.o $L -o rootside-proto-replay
python3 -I $P/gen_seeds.py /out/seeds
echo "== rootside-proto: $(ls seeds/rootside-proto | wc -l) seeds"
./rootside-proto-replay seeds/rootside-proto/seed-*
# ---- rootside-dispatch
D=/albero/benches/fuzz/rootside-dispatch
gcc $F -I$D -c $D/stubs_log.c -o dl.o
gcc $F -I$D -c $D/fuzz_rootside_dispatch.c -o fd.o
gcc -fsanitize=address,undefined fd.o dl.o rp.o $L -o rootside-dispatch-replay
python3 -I $D/gen_seeds.py /out/seeds
echo "== rootside-dispatch: $(ls seeds/rootside-dispatch | wc -l) seeds"
./rootside-dispatch-replay seeds/rootside-dispatch/seed-*
'
