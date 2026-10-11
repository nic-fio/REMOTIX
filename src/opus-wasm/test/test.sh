#!/bin/sh
# The pure test of the page's decoder (D-006): the wasm EMBEDDED in
# src/page.html against native libopus, on the same packets.
# Needs: cc, libopus (-dev) and node.   sh src/opus-wasm/test/test.sh
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
sh "$HERE/../build.sh" --verify
cc -O2 $(pkg-config --cflags opus) "$HERE/reference.c" $(pkg-config --libs opus) -lm -o "$T/riferimento"
"$T/riferimento" "$T/pacchetti.bin" "$T/attesi.f32"
node "$HERE/compare.mjs" "$HERE/../../page.html" "$T/pacchetti.bin" "$T/attesi.f32"
