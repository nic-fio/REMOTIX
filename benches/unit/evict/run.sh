#!/bin/bash
# run.sh — builds and runs the two unit tests of this folder with a direct podman run (the recipe of the header of test_evict.c).
#   bash benches/unit/evict/run.sh            from the root of the tree
# Exit code 0 = both green.  Nothing under the tree is written (it is mounted read-only).
set -u
TREE=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
rc=0
for T in test_evict test_orphan; do
	echo "== $T"
	nice -n 19 ionice -c3 podman run --rm --cpus=2 --network=none -v "$TREE:/albero:ro" -e T="$T" localhost/remotix-fuzz sh -c '
	  cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
	  F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
	     -I/albero/src -I/albero/benches/fuzz/rcp-msg $(pkg-config --cflags $PK)" &&
	  L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
	  clang $F -c /albero/benches/unit/evict/$T.c -o t.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
	  { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
	  { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
	    while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
	  clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test' || rc=1
done
exit $rc
