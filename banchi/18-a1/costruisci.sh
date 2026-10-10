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
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC=$HERE/../../src
OUT=${1:-/tmp/18-a1}
mkdir -p "$OUT"

CF="-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE -I$SRC"
RENAMES="-Daudio_cod_apri=old_enc_open -Daudio_cod_chiudi=old_enc_close \
 -Daudio_cod_blocco=vecchio_cod_blocco -Daudio_cod_passa=old_enc_pass \
 -Daudio_cod_conti=vecchio_cod_conti -Daudio_cod_taciuti=old_enc_silenced \
 -Daudio_silenzio_taci=old_silence_hush \
 -Daudio_silenzio_acceso=vecchio_silenzio_acceso"

# shellcheck disable=SC2086
cc $CF $RENAMES $(pkg-config --cflags libavcodec libavutil) \
   -c "$HERE/audio-vecchio.c" -o "$OUT/audio-vecchio.o"
# shellcheck disable=SC2086
cc $CF $(pkg-config --cflags opus) -c "$SRC/audio.c" -o "$OUT/audio-nuovo.o"
# shellcheck disable=SC2086
cc $CF $(pkg-config --cflags opus) -o "$OUT/18-a1" \
   "$HERE/18-a1-opus-senza-ffmpeg.c" "$OUT/audio-vecchio.o" "$OUT/audio-nuovo.o" \
   $(pkg-config --libs libavcodec libavutil opus) -lm

# ⚠ The new one must NOT name libavcodec: we look at the object.
if nm -u "$OUT/audio-nuovo.o" | grep -E ' (av_|avcodec_)'; then
	echo "⛔ the new object still calls libavcodec"
	exit 1
fi
echo "⭐ audio-nuovo.o: no undefined av_/avcodec_ symbol"
"$OUT/18-a1" --put_out "$OUT"
