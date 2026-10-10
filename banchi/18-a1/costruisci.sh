#!/bin/bash
#
# 18-a1 — builds and runs the old/new comparison of `audio.c`.
#
#   bash banchi/18-a1/costruisci.sh [output folder]
#
# ⚠ It needs libavcodec (for the OLD one, which is the reference) AND libopus:
#   inside `remotix-costruzione` or in the server's `devroot` both are there.
#   ⛔ The day the build image loses ffmpeg, this bench runs
#   only on the server — and that is right: it is the old one that needs ffmpeg.
#
# ⛔ The old one is RENAMED from the compile line and is not touched:
#    `audio-vecchio.c` is `src/audio.c` of commit 545ec55 to the letter, and a
#    reference that has been retouched no longer compares anything.  (10 Oct 2026,
#    §10.38: its comments and log lines are now in English, the CODE is unchanged
#    — the packets compare as before, the printed opening lines no longer match
#    the old ones word for word.)
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC=$QUI/../../src
FUORI=${1:-/tmp/18-a1}
mkdir -p "$FUORI"

CF="-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE -I$SRC"
RINOMINA="-Daudio_cod_apri=vecchio_cod_apri -Daudio_cod_chiudi=vecchio_cod_chiudi \
 -Daudio_cod_blocco=vecchio_cod_blocco -Daudio_cod_passa=vecchio_cod_passa \
 -Daudio_cod_conti=vecchio_cod_conti -Daudio_cod_taciuti=vecchio_cod_taciuti \
 -Daudio_silenzio_taci=vecchio_silenzio_taci \
 -Daudio_silenzio_acceso=vecchio_silenzio_acceso"

# shellcheck disable=SC2086
cc $CF $RINOMINA $(pkg-config --cflags libavcodec libavutil) \
   -c "$QUI/audio-vecchio.c" -o "$FUORI/audio-vecchio.o"
# shellcheck disable=SC2086
cc $CF $(pkg-config --cflags opus) -c "$SRC/audio.c" -o "$FUORI/audio-nuovo.o"
# shellcheck disable=SC2086
cc $CF $(pkg-config --cflags opus) -o "$FUORI/18-a1" \
   "$QUI/18-a1-opus-senza-ffmpeg.c" "$FUORI/audio-vecchio.o" "$FUORI/audio-nuovo.o" \
   $(pkg-config --libs libavcodec libavutil opus) -lm

# ⚠ The new one must NOT name libavcodec: we look at the object.
if nm -u "$FUORI/audio-nuovo.o" | grep -E ' (av_|avcodec_)'; then
	echo "⛔ the new object still calls libavcodec"
	exit 1
fi
echo "⭐ audio-nuovo.o: no undefined av_/avcodec_ symbol"
"$FUORI/18-a1" --scrivi "$FUORI"
