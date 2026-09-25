#!/bin/sh
# La prova pura del decodificatore della pagina (D-006): il wasm INCASTONATO in
# src/pagina.html contro libopus nativo, sugli stessi pacchetti.
# Serve: cc, libopus (-dev) e node.   sh src/opus-wasm/prova/prova.sh
set -eu
QUI=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
sh "$QUI/../costruisci.sh" --verifica
cc -O2 $(pkg-config --cflags opus) "$QUI/riferimento.c" $(pkg-config --libs opus) -lm -o "$T/riferimento"
"$T/riferimento" "$T/pacchetti.bin" "$T/attesi.f32"
node "$QUI/confronta.mjs" "$QUI/../../pagina.html" "$T/pacchetti.bin" "$T/attesi.f32"
