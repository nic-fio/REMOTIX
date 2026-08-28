#!/bin/bash
# Registra il monitor del sink «uscita».  $1 = secondi, $2 = file
set -u
export XDG_RUNTIME_DIR=/tmp/rt
rm -f "$2"
timeout "$1" parec -d uscita.monitor --rate=44100 --channels=2 --format=s16le --raw > "$2" 2>/dev/null
