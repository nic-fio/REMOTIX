#!/bin/sh
# The pure test of the page's decoder (D-006): the wasm EMBEDDED in
# src/pagina.html against native libopus, on the same packets.
# Needs: cc, libopus (-dev) and node.   sh src/opus-wasm/prova/prova.sh
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
sh "$HERE/../costruisci.sh" --verify
cc -O2 $(pkg-config --cflags opus) "$HERE/riferimento.c" $(pkg-config --libs opus) -lm -o "$T/reference"
"$T/reference" "$T/packets.bin" "$T/expected_vals.f32"
node "$HERE/confronta.mjs" "$HERE/../../pagina.html" "$T/packets.bin" "$T/expected_vals.f32"
