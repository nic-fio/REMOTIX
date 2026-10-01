#!/bin/bash
# 19-shader.sh — compila lo shader di conversione in SPIR-V e lo scrive come
# intestazione C (`src/vulkanvideo_rgb_nv12_spv.h`), che si CONSERVA nel
# deposito: il prodotto non ha bisogno del compilatore di shader, solo chi
# cambia lo shader.
#
#   bash banchi/19-vulkan/19-shader.sh            (dalla radice dell'albero)
#
# Serve `glslc` (pacchetto `glslc`, shaderc) o `glslangValidator`
# (`glslang-tools`); nel devroot del server ci sono tutt'e due.
set -eu
ALBERO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SORGENTE=$ALBERO/src/vulkanvideo_rgb_nv12.comp
USCITA=$ALBERO/src/vulkanvideo_rgb_nv12_spv.h
if command -v glslc >/dev/null; then
	glslc -O --target-env=vulkan1.3 -fshader-stage=compute -mfmt=c -o "$USCITA.tmp" "$SORGENTE"
	{
		echo "/* generato da banchi/19-vulkan/19-shader.sh da src/vulkanvideo_rgb_nv12.comp: non si tocca a mano */"
		# glslc scrive `{0x..,0x..,}`: si tolgono le graffe, cosi' l'intestazione sta dentro un inizializzatore
		sed -e 's/^{//' -e 's/}$//' "$USCITA.tmp"
	} > "$USCITA"
	rm -f "$USCITA.tmp"
elif command -v glslangValidator >/dev/null; then
	glslangValidator -V --target-env vulkan1.3 -S comp -o "$USCITA.spv" "$SORGENTE"
	{
		echo "/* generato da banchi/19-vulkan/19-shader.sh da src/vulkanvideo_rgb_nv12.comp: non si tocca a mano */"
		od -An -v -t x4 -w16 "$USCITA.spv" | sed 's/ \([0-9a-f]\{8\}\)/0x\1,/g'
	} > "$USCITA"
	rm -f "$USCITA.spv"
else
	echo "⛔ ne' glslc ne' glslangValidator" >&2
	exit 1
fi
echo "scritto $USCITA ($(wc -c < "$USCITA") byte)"
