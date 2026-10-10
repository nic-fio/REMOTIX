#!/bin/sh
# The pure test of the page's decoder (D-006): the wasm EMBEDDED in
# src/pagina.html against native libopus, on the same packets.
# Needs: cc, libopus (-dev) and node.   sh src/opus-wasm/prova/prova.sh
set -eu
QUI=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
sh "$QUI/../costruisci.sh" --verifica
cc -O2 $(pkg-config --cflags opus) "$QUI/riferimento.c" $(pkg-config --libs opus) -lm -o "$T/riferimento"
"$T/riferimento" "$T/pacchetti.bin" "$T/attesi.f32"
node "$QUI/confronta.mjs" "$QUI/../../pagina.html" "$T/pacchetti.bin" "$T/attesi.f32"
