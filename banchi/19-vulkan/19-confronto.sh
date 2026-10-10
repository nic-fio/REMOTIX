#!/bin/bash
# 19-confronto.sh — Vulkan Video (`src/vulkanvideo.c`) against VA-API (the product,
# `src/codificatore.c` + `src/vadiretta.c`) on the SAME card, on the server,
# inside `enter.sh --root` (access to the DRM nodes is needed).  ⭐ Since the graft (1 Oct
# 2026) there is the third engine `gpu_card`: the integrated product that chooses by
# capability (on the Radeon: Vulkan inside codificatore.c).
#
#   bash /media/REMOTIX/enter.sh --root 'bash /srv/src/f19-vulkan/albero/banchi/19-vulkan/19-confronto.sh [costruisci|tutto|corto|capacita|intel]'
#
# Expects in $TREE (default /srv/src/f19-vulkan/albero) the worktree's
# tree (src/ and banchi/).  Writes to $OUTPUT (default /srv/src/f19-vulkan/tmp/confronto):
# the streams, the logs, `esiti.jsonl` (one line per test) and the table (`19-tabella.py`).
#
# ⚠ ffmpeg/ffprobe here are ONLY measuring tools (decoding, PSNR/SSIM,
#   profile/level): they do not go into the product.
set -u
TREE=${TREE:-/srv/src/f19-vulkan/tree}
OUTPUT=${OUTPUT:-/srv/src/f19-vulkan/tmp/comparison}
ACTION=${1:-overall}
FRAMES=${FRAMES:-120}
RADEON_NODE=${RADEON_NODE:-129}
INTEL_NODE=${INTEL_NODE:-128}
# ⭐ the engines of the comparison (phase 19, NVIDIA bench): on NVIDIA VA-API does not encode, and the
#    bench `banchi/19-nvidia/` asks for ENGINES="vulkan gpu_card"
ENGINES=${ENGINES:-vaapi vulkan gpu_card}
FPS=60
mkdir -p "$OUTPUT"
cd "$TREE" || exit 1

build() {
	local F="-std=gnu11 -O2 -g -D_GNU_SOURCE -I$TREE/src -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers"
	bash banchi/19-vulkan/19-shader.sh || return 1
	echo "== building 19-confronto"
	local FALLBACK="" FALLBACK_LIBS=""
	if [ -f src/ripiego.c ]; then
		# the starting tree (fase-10-cure) still has the software fallback: it is linked to compile the product
		FALLBACK="src/ripiego.c $(pkg-config --cflags openh264 SvtAv1Enc)"
		FALLBACK_LIBS="$(pkg-config --libs SvtAv1Enc) -ldl"
	fi
	gcc $F $(pkg-config --cflags libva libva-drm gbm libdrm vulkan) -o "$OUTPUT/19-confronto" \
		banchi/19-vulkan/19-confronto.c \
		src/vulkanvideo.c src/codificatore.c src/vadiretta.c src/scrittore_bit.c src/colori709.c \
		src/registro.c $FALLBACK $(pkg-config --libs libva libva-drm gbm vulkan) $FALLBACK_LIBS -lm || return 1
	if nm -u "$OUTPUT/19-confronto" | grep -qE ' (av_|avcodec_|sws_)'; then
		echo "⛔ the bench calls ffmpeg"; return 1
	fi
	echo "== built"
}

# prova NAME ENGINE NODE CODEC DEPTH SIZE PATH [extra arguments…]
prova() {
	local label_name=$1 motore=$2 node=$3 codec=$4 prof=$5 gauge=$6 route=$7; shift 7
	local flow="$OUTPUT/$label_name-$motore.bin" logbook="$OUTPUT/$label_name-$motore.logbook"
	local csv="$OUTPUT/$label_name-$motore.csv" source="$OUTPUT/source-$gauge.bgrx"
	local extra_src=""
	[ -f "$source" ] || extra_src="--source-out $source"
	local t0 t1
	t0=$(date +%s.%N)
	"$OUTPUT/19-confronto" --motore "$motore" --codec "$codec" --bit_depth "$prof" --gauge "$gauge" \
		--node "/dev/dri/renderD$node" --route "$route" --out_dir "$flow" \
		--frames "$FRAMES" --fps $FPS $extra_src "$@" > "$csv" 2> "$logbook"
	local code_v=$?
	t1=$(date +%s.%N)
	local json
	json=$(tail -1 "$csv")
	[ "${json:0:1}" = "{" ] || json='{"outcome":"nessuna row"}'
	local fmt=$codec
	local decoded errors_dec
	errors_dec=$(ffmpeg -v error -f $fmt -i "$flow" -f null - 2>&1 | grep -c .)
	decoded=$(ffprobe -v error -f $fmt -count_frames -show_entries stream=nb_read_frames -of csv=p=0 "$flow" 2>/dev/null)
	local probe
	probe=$(ffprobe -v error -f $fmt -show_entries stream=profile,level,width,height,pix_fmt,color_range,color_space,color_transfer,color_primaries -of csv=p=0 "$flow" 2>/dev/null | head -1)
	local psnr="" ssim=""
	if [ -f "$source" ] && [ -z "$(echo "$@" | grep -o -E "resize|cycle")" ]; then
		local pix=yuv420p; [ "$prof" = 10 ] && pix=yuv420p10le
		psnr=$(ffmpeg -v info -f $fmt -r $FPS -i "$flow" -f rawvideo -pix_fmt bgr0 -s "$gauge" -r $FPS -i "$source" \
			-lavfi "[1:v]scale=out_color_matrix=bt709:out_range=tv,format=$pix[r];[0:v]format=$pix[a];[a][r]psnr" -f null - 2>&1 \
			| grep -o 'PSNR y:[0-9.inf]* u:[0-9.inf]* v:[0-9.inf]* average:[0-9.inf]*' | tail -1 | sed 's/PSNR //')
		ssim=$(ffmpeg -v info -f $fmt -r $FPS -i "$flow" -f rawvideo -pix_fmt bgr0 -s "$gauge" -r $FPS -i "$source" \
			-lavfi "[1:v]scale=out_color_matrix=bt709:out_range=tv,format=$pix[r];[0:v]format=$pix[a];[a][r]ssim" -f null - 2>&1 \
			| grep -o 'All:[0-9.]*' | tail -1 | cut -d: -f2)
	fi
	local byte
	byte=$(stat -c %s "$flow" 2>/dev/null)
	printf '{"prova":"%s","version_v":"%s","node":"renderD%s","codec":"%s","bit_depth":%s,"gauge":"%s","route":"%s","extra":"%s","code_v":%s,"seconds":%.2f,"byte_flusso":%s,"decoded":"%s","errori_decodifica":%s,"ffprobe":"%s","psnr":"%s","ssim":"%s","bench":%s}\n' \
		"$label_name" "$motore" "$node" "$codec" "$prof" "$gauge" "$route" "$*" "$code_v" "$(awk "BEGIN{print $t1 - $t0}")" "${byte:-0}" "${decoded:-?}" "${errors_dec:-0}" "$probe" "$psnr" "$ssim" "$json" >> "$OUTPUT/esiti.jsonl"
	echo "   $label_name $motore: code $code_v · ${byte:-0} bytes · decoded ${decoded:-?} · psnr ${psnr:-—} · ssim ${ssim:-—} · $probe"
}

matrix() {
	local node=$RADEON_NODE measures="1920x1080 3840x2160" routes="mem_buf gpu_card"
	[ "$ACTION" = short_v ] && measures="1920x1080"
	for cp in "h264 8" "hevc 8" "hevc 10"; do
		set -- $cp; local codec=$1 prof=$2
		for gauge in $measures; do
			for route in $routes; do
				local label_name="D$node-$codec$prof-$gauge-$route"
				echo "== $label_name"
				# ⭐ since the graft: `gpu_card` = the integrated product (by capability: Vulkan on the Radeon)
				for motore in $ENGINES; do
					prova "$label_name" "$motore" "$node" "$codec" "$prof" "$gauge" "$route"
				done
			done
		done
	done
	# hot: key on request, new canvas, bandwidth cap, new quality
	for codec in h264 hevc; do
		local base="D$node-${codec}8-1920x1080"
		echo "== $base key on request / new canvas / cap / quality"
		for motore in $ENGINES; do
			prova "$base-chiave" "$motore" "$node" "$codec" 8 1920x1080 gpu_card --key-at 40
			prova "$base-tela" "$motore" "$node" "$codec" 8 1920x1080 gpu_card --resize-at 60:1280x720
			prova "$base-tetto" "$motore" "$node" "$codec" 8 1920x1080 gpu_card --ceiling 20
			# a cap that BITES: 2 Mbit/s (wire 1.6, target 1.2) on a scene that at QP 26 costs ~8
			prova "$base-tetto2" "$motore" "$node" "$codec" 8 1920x1080 gpu_card --ceiling 2
		done
		prova "$base-qualita" vulkan "$node" "$codec" 8 1920x1080 gpu_card --quality-at 60:36
		# ⭐ the canvas in a CYCLE (the Radeon defect, F-018/P-C: 4K→2560→4K): every 20 frames
		#   the size changes (the list starts from the initial size: the first change goes to the second),
		#   five changes in 120; with PRODUCT_ORDER=1 the slabs are remade BEFORE
		#   the encoder reopens, as in `wlroots.c`
		for motore in $ENGINES; do
			prova "D$node-${codec}8-3840x2160-ciclo" "$motore" "$node" "$codec" 8 3840x2160 gpu_card \
				--cycle 20:3840x2160,2560x1440
		done
	done
}

# ⚠ The Intel EXPERIMENT: ANV encodes only behind `ANV_DEBUG=video-encode`
# (experimental, not default): it is declared, not promised.
intel() {
	local node=$INTEL_NODE
	echo "== Intel capabilities without and with ANV_DEBUG=video-encode"
	"$OUTPUT/19-confronto" --capabilities /dev/dri/renderD$node | tee "$OUTPUT/capacita-intel.json"
	ANV_DEBUG=video-encode "$OUTPUT/19-confronto" --capabilities /dev/dri/renderD$node | tee "$OUTPUT/capacita-intel-anv-debug.json"
	for codec in h264 hevc; do
		local label_name="D$node-${codec}8-1920x1080-scheda-ANV"
		echo "== $label_name"
		ANV_DEBUG=video-encode prova "$label_name" vulkan "$node" "$codec" 8 1920x1080 gpu_card
		prova "$label_name" vaapi "$node" "$codec" 8 1920x1080 gpu_card
	done
}

case "$ACTION" in
build) build ;;
capabilities)
	for n in $RADEON_NODE $INTEL_NODE; do
		"$OUTPUT/19-confronto" --capabilities /dev/dri/renderD$n | tee "$OUTPUT/capacita-renderD$n.json"
	done ;;
intel) intel ;;
overall|short_v)
	build || exit 1
	: > "$OUTPUT/esiti.jsonl"
	"$OUTPUT/19-confronto" --capabilities /dev/dri/renderD$RADEON_NODE | tee "$OUTPUT/capacita-renderD$RADEON_NODE.json"
	matrix
	python3 banchi/19-vulkan/19-tabella.py "$OUTPUT/esiti.jsonl" | tee "$OUTPUT/tabella.txt"
	rm -f "$OUTPUT"/source-*.bgrx
	;;
*) echo "unknown action: $ACTION"; exit 2 ;;
esac
