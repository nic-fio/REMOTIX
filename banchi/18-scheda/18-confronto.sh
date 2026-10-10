#!/bin/bash
# 18-confronto.sh — old path (libavcodec) against new (direct libva), on the
# server, inside `enter.sh --root` (it needs access to the DRM nodes).
#
#   bash /media/REMOTIX/enter.sh --root 'bash /srv/src/f18-scheda/banchi/18-scheda/18-confronto.sh [costruisci|tutto|corto]'
#
# It expects in $TREE (default /srv/src/f18-scheda/albero):
#   src/                 the NEW source (codificatore.c, vadiretta.c, scrittore_bit.c, registro.c…)
#   prior/codificatore.c   the encoder of the starting commit (545ec55)
#   banchi/18-scheda/    this bench
# It writes in $OUTPUT (default /srv/src/f18-scheda/tmp/confronto): the streams, the
# logs, `esiti.jsonl` (one line per test) and the table (`18-tabella.py`).
set -u
TREE=${TREE:-/srv/src/f18-scheda/tree}
OUTPUT=${OUTPUT:-/srv/src/f18-scheda/tmp/comparison}
ACTION=${1:-overall}
FRAMES=${FRAMES:-120}
FPS=60
mkdir -p "$OUTPUT"
cd "$TREE" || exit 1

build() {
	local F="-std=gnu11 -O2 -g -D_GNU_SOURCE -I$TREE/src -Wall -Wno-unused-parameter"
	local INC LIBS
	INC=$(pkg-config --cflags libva libva-drm libavcodec libavutil libswscale gbm libdrm)
	LIBS=$(pkg-config --libs libva libva-drm libavcodec libavutil libswscale gbm)
	# ⭐ The NEW one is the product tree after the integration (phase 18): no
	#    ffmpeg — the colours are colori709.c.  ⛔ Phase 19: the software fallback
	#    (ripiego.c: OpenH264, SVT-AV1) is gone, and with it `--software`, which
	#    the encoder now refuses, saying so.  ⚠ libav* below serves
	#    ONLY the old one.
	echo "== building 18-confronto-nuovo"
	# ⭐ Phase 19 (graft, 1 Oct 2026): `codificatore.c` also carries the
	#    Vulkan path (`vulkanvideo.c`, `-lvulkan`); this bench asks for
	#    `h264_vaapi`/`hevc_vaapi` BY NAME, so it measures the VA-API path —
	#    «nothing worse than before» on the Intel and on the Radeon in VA-API.
	gcc $F $(pkg-config --cflags vulkan) $INC -Wno-missing-field-initializers -o "$OUTPUT/18-confronto-nuovo" \
		banchi/18-scheda/18-confronto.c \
		src/codificatore.c src/vadiretta.c src/vulkanvideo.c src/scrittore_bit.c src/colori709.c \
		src/registro.c $(pkg-config --libs libva libva-drm gbm vulkan) -lm || return 1
	if nm -u "$OUTPUT/18-confronto-nuovo" | grep -qE ' (av_|avcodec_|sws_)'; then
		echo "⛔ the NEW one still calls ffmpeg"; return 1
	fi
	echo "== building 18-confronto-vecchio"
	gcc $F $INC -o "$OUTPUT/18-confronto-vecchio" banchi/18-scheda/18-confronto.c \
		prior/codificatore.c src/registro.c $LIBS -lm || return 1
	echo "== built"
}

# prova NAME VERSION NODE CODEC DEPTH SIZE PATH [extra arguments…]
prova() {
	local label_name=$1 version_v=$2 node=$3 codec=$4 prof=$5 gauge=$6 route=$7; shift 7
	local flow="$OUTPUT/$label_name-$version_v.bin" logbook="$OUTPUT/$label_name-$version_v.logbook"
	local csv="$OUTPUT/$label_name-$version_v.csv" source="$OUTPUT/source-$gauge.bgrx"
	local extra_src=""
	[ -f "$source" ] || extra_src="--source-out $source"
	local t0 t1
	t0=$(date +%s.%N)
	"$OUTPUT/18-confronto-$version_v" --codec "$codec" --bit_depth "$prof" --gauge "$gauge" \
		--node "/dev/dri/renderD$node" --route "$route" --out_dir "$flow" \
		--frames "$FRAMES" --fps $FPS $extra_src "$@" > "$csv" 2> "$logbook"
	local code_v=$?
	t1=$(date +%s.%N)
	local json
	json=$(tail -1 "$csv")
	[ "${json:0:1}" = "{" ] || json='{"outcome":"nessuna row"}'
	# decoding with ffmpeg, frame by frame
	local fmt=$codec; [ "$codec" = hevc ] && fmt=hevc
	local decoded errors_dec
	errors_dec=$(ffmpeg -v error -f $fmt -i "$flow" -f null - 2>&1 | grep -c .)
	decoded=$(ffprobe -v error -f $fmt -count_frames -show_entries stream=nb_read_frames -of csv=p=0 "$flow" 2>/dev/null)
	local probe
	probe=$(ffprobe -v error -f $fmt -show_entries stream=profile,level,width,height,pix_fmt,color_range,color_space,color_transfer,color_primaries -of csv=p=0 "$flow" 2>/dev/null | head -1)
	# PSNR and SSIM against the source, only if the size did not change halfway
	local psnr="" ssim=""
	if [ -f "$source" ] && [ -z "$(echo "$@" | grep -o resize)" ]; then
		local pix=yuv420p; [ "$prof" = 10 ] && pix=yuv420p10le
		# ⚠ `-v info`: the two filters print the verdict at info level, with -v error they stay silent
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
		"$label_name" "$version_v" "$node" "$codec" "$prof" "$gauge" "$route" "$*" "$code_v" "$(awk "BEGIN{print $t1 - $t0}")" "${byte:-0}" "${decoded:-?}" "${errors_dec:-0}" "$probe" "$psnr" "$ssim" "$json" >> "$OUTPUT/esiti.jsonl"
	echo "   $label_name $version_v: code $code_v · ${byte:-0} bytes · decoded ${decoded:-?} · psnr ${psnr:-—} · ssim ${ssim:-—} · $probe"
}

matrix() {
	local nodes="128 129" measures="1920x1080 3840x2160" routes="mem_buf gpu_card"
	[ "$ACTION" = short_v ] && measures="1920x1080"
	for node in $nodes; do
		for cp in "h264 8" "hevc 8" "hevc 10"; do
			set -- $cp; local codec=$1 prof=$2
			for gauge in $measures; do
				for route in $routes; do
					local label_name="D$node-$codec$prof-$gauge-$route"
					echo "== $label_name"
					for version_v in prior fresh; do
						prova "$label_name" "$version_v" "$node" "$codec" "$prof" "$gauge" "$route"
					done
				done
			done
		done
	done
	# the three «hot» tests, 1080p, card path, H.264 and HEVC 8, on the two nodes
	for node in $nodes; do
		for codec in h264 hevc; do
			local base="D$node-${codec}8-1920x1080"
			echo "== $base key on request / new canvas / cap"
			for version_v in prior fresh; do
				prova "$base-chiave" "$version_v" "$node" "$codec" 8 1920x1080 gpu_card --key-at 40
				prova "$base-tela" "$version_v" "$node" "$codec" 8 1920x1080 gpu_card --resize-at 60:1280x720
				prova "$base-tetto" "$version_v" "$node" "$codec" 8 1920x1080 gpu_card --ceiling 20
			done
		done
	done
}

case "$ACTION" in
build) build ;;
overall|short_v)
	build || exit 1
	: > "$OUTPUT/esiti.jsonl"
	matrix
	python3 banchi/18-scheda/18-tabella.py "$OUTPUT/esiti.jsonl" | tee "$OUTPUT/tabella.txt"
	rm -f "$OUTPUT"/source-*.bgrx
	;;
*) echo "unknown action: $ACTION"; exit 2 ;;
esac
