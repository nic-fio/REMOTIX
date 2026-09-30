#!/bin/bash
#
# 18-a1 — costruisce e fa girare il confronto vecchio/nuovo di `audio.c`.
#
#   bash banchi/18-a1/costruisci.sh [cartella d'uscita]
#
# ⚠ Vuole libavcodec (per il VECCHIO, che e' il termine di paragone) E libopus:
#   dentro `remotix-costruzione` o nel `devroot` del server ci sono tutt'e due.
#   ⛔ Il giorno che l'immagine di costruzione perde ffmpeg, questo banco gira
#   solo sul server — ed e' giusto: e' il vecchio che ha bisogno di ffmpeg.
#
# ⛔ Il vecchio si RINOMINA dalla riga di compilazione e non si tocca:
#    `audio-vecchio.c` e' `src/audio.c` del commit 545ec55 alla lettera, e un
#    termine di paragone ritoccato non paragona piu' niente.
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

# ⚠ Il nuovo NON deve nominare libavcodec: si guarda l'oggetto.
if nm -u "$FUORI/audio-nuovo.o" | grep -E ' (av_|avcodec_)'; then
	echo "⛔ l'oggetto nuovo chiama ancora libavcodec"
	exit 1
fi
echo "⭐ audio-nuovo.o: nessun simbolo av_/avcodec_ indefinito"
"$FUORI/18-a1" --scrivi "$FUORI"
