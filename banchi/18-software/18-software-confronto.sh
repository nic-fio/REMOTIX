#!/bin/bash
#
# 18-software-confronto.sh — phase 18, V-software line: the bench that compares
# the OLD fallback (libx264/libsvtav1 via libavcodec + sws_scale) with the NEW one
# (OpenH264, SVT-AV1 direct, colori709), on the same desktop scene.
#
# It runs ON THE TEST MACHINE, inside the development environment:
#
#   bash /media/REMOTIX/enter.sh "bash /srv/src/f18-software/banchi/18-software/18-software-confronto.sh [step]"
#
# steps: prepare | build | colors | encode | events | refusals | all (default)
# The OpenH264 settings to calibrate go through the environment (RIPIEGO_H264_*),
# read only because the bench compiles with -DRIPIEGO_BANCO.
#
# ⚠ Times depend on the load: the `uptime` line goes at the top of every result,
#   because other agents use the machine in parallel.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
# ⚠ The host's /media/REMOTIX/tmp is not visible from inside: the work sits next
#   to the sources, in our own folder.
WORKDIR=${F18_WORK:-$TREE/lavoro}
N=${N:-120}
STEP=${1:-all}
BENCH=$WORKDIR/18-software-confronto
mkdir -p "$WORKDIR"

load() { printf '⏱ load: %s\n' "$(uptime | sed 's/.*load average/load average/')"; }

prepare() {
	local l a k dl da fs
	[ -f "$WORKDIR/l1.png" ] || { echo "⛔ $WORKDIR/l1.png is missing (the real wallpaper)"; exit 2; }
	expand -t 8 "$TREE/src/codificatore.c" | sed -n '1,420p' > "$WORKDIR/testo.txt"
	for m in 1920x1080 3840x2160; do
		l=${m%x*}; a=${m#*x}
		[ -f "$WORKDIR/sfondo_${m}.bgr0" ] || ffmpeg -v error -y -i "$WORKDIR/l1.png" \
			-vf "scale=${l}:${a}:flags=lanczos" -pix_fmt bgr0 -f rawvideo "$WORKDIR/sfondo_${m}.bgr0"
		k=$((l / 1920))
		dl=$(( (1092 * k) & ~1 )); da=$(( ((780 + 18 * 70) * k) & ~1 )); fs=$((15 * k))
		[ -f "$WORKDIR/doc_${dl}x${da}.bgr0" ] || ffmpeg -v error -y -f lavfi \
			-i "color=c=0xfdfdfd:s=${dl}x${da}" -vf \
"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:textfile=$WORKDIR/testo.txt:fontsize=${fs}:fontcolor=0x202020:expansion=none:x=$((8 * k)):y=$((6 * k))" \
			-frames:v 1 -pix_fmt bgr0 -f rawvideo "$WORKDIR/doc_${dl}x${da}.bgr0"
	done
	ls -la "$WORKDIR"/*.bgr0
}

build() {
	# ⛔ Phase 19 (1 Oct 2026): `src/ripiego.c` has left the product.  The bench
	#    stays as HISTORY, and takes the fallback from the last commit that
	#    had it (6bacca7) — it needs a git tree; the rest is today's.
	local HISTORY=$WORKDIR/storia-ripiego f
	mkdir -p "$HISTORY"
	for f in ripiego.c ripiego.h; do
		[ -s "$HISTORY/$f" ] || git -C "$TREE" show "6bacca7:src/$f" > "$HISTORY/$f" \
			|| { echo "⛔ $f is no longer in the product (phase 19) and cannot be extracted from git 6bacca7"; exit 2; }
	done
	gcc -O2 -g -std=gnu11 -D_GNU_SOURCE -DRIPIEGO_BANCO -Wall -Wextra \
		-I"$HISTORY" -I"$TREE/src" \
		-o "$BENCH" "$HERE/18-software-confronto.c" "$HISTORY/ripiego.c" \
		"$TREE/src/colori709.c" "$TREE/src/registro.c" \
		$(pkg-config --cflags openh264) \
		$(pkg-config --cflags --libs libavcodec libavutil libswscale SvtAv1Enc) \
		-lyuv -ldl -lm && echo "built: $BENCH"
	# the same, with the conversion in plain C: the bytes must match
	gcc -O2 -std=gnu11 -D_GNU_SOURCE -DRIPIEGO_BANCO -DCOLORI709_SENZA_SIMD \
		-I"$HISTORY" -I"$TREE/src" \
		-o "$BENCH-c" "$HERE/18-software-confronto.c" "$HISTORY/ripiego.c" \
		"$TREE/src/colori709.c" "$TREE/src/registro.c" \
		$(pkg-config --cflags openh264) \
		$(pkg-config --cflags --libs libavcodec libavutil libswscale SvtAv1Enc) \
		-lyuv -ldl -lm && echo "built: $BENCH-c (without SIMD)"
}

# averages and minimums from the ffmpeg statistics files
summarize() { # $1 psnr.log $2 ssim.log $3 rgb.log
	awk '{for(i=1;i<=NF;i++){split($i,kv,":"); if(kv[1]=="psnr_y"){y+=kv[2]; if(!n||kv[2]<my)my=kv[2]} if(kv[1]=="psnr_avg"){s+=kv[2]}} n++}
	     END{printf "PSNR-Y avg %.2f min %.2f · PSNR-YUV avg %.2f", y/n, my, s/n}' "$1"
	awk '{for(i=1;i<=NF;i++){split($i,kv,":"); if(kv[1]=="All"){s+=kv[2]; if(!n||kv[2]<m)m=kv[2]}} n++}
	     END{printf " · SSIM avg %.5f min %.5f", s/n, m}' "$2"
	awk '{for(i=1;i<=NF;i++){split($i,kv,":"); if(kv[1]=="psnr_avg"){s+=kv[2]; if(!n||kv[2]<m)m=kv[2]}} n++}
	     END{printf " · PSNR-RGB avg %.2f min %.2f\n", s/n, m}' "$3"
}

analyze() { # $1 stream $2 fmt(h264|obu) $3 source.raw $4 l $5 a
	local f=$1 fmt=$2 src=$3 l=$4 a=$5
	ffprobe -v error -f "$fmt" -count_frames -select_streams v:0 \
		-show_entries stream=codec_name,profile,level,width,height,pix_fmt,color_space,color_range,color_primaries,color_transfer,nb_read_frames \
		-of compact=p=0 "$f"
	local errors
	errors=$(ffmpeg -v error -f "$fmt" -i "$f" -f null - 2>&1 | wc -l)
	echo "decoder error lines: $errors"
	ffmpeg -v error -y -f rawvideo -pix_fmt bgr0 -s "${l}x${a}" -r 60 -i "$src" -f "$fmt" -r 60 -i "$f" -lavfi \
"[0:v]scale=out_color_matrix=bt709:out_range=tv:flags=bilinear,format=yuv420p,split[r1][r2];[1:v]format=yuv420p,split[d1][d2];[d1][r1]psnr=stats_file=$f.psnr;[d2][r2]ssim=stats_file=$f.ssim" \
		-f null -
	ffmpeg -v error -y -f rawvideo -pix_fmt bgr0 -s "${l}x${a}" -r 60 -i "$src" -f "$fmt" -r 60 -i "$f" -lavfi \
"[0:v]format=gbrp[r];[1:v]scale=in_color_matrix=bt709:in_range=tv:flags=bilinear,format=gbrp[d];[d][r]psnr=stats_file=$f.rgb" \
		-f null -
	summarize "$f.psnr" "$f.ssim" "$f.rgb"
}

encode() {
	local m l a
	for m in ${SIZES:-1920x1080 3840x2160}; do
		l=${m%x*}; a=${m#*x}
		[ -f "$WORKDIR/sorgente_${m}.raw" ] || "$BENCH" source "$l" "$a" "$WORKDIR" "$N" "$WORKDIR/sorgente_${m}.raw"
		for c in ${CODEC:-h264 av1}; do
			for s in ${ROUTES:-vecchia fixed new}; do
				[ "$c" = av1 ] && [ "$s" = fixed ] && continue
				local ext=h264 fmt=h264
				[ "$c" = av1 ] && { ext=obu; fmt=obu; }
				local out="$WORKDIR/${c}-${s}-${m}${RUN_LABEL:-}.$ext"
				echo "── $c $s $m ${RUN_LABEL:-}"
				load
				"$BENCH" encode "$c" "$s" "$l" "$a" "$WORKDIR" "$N" "$out" 45 || continue
				analyze "$out" "$fmt" "$WORKDIR/sorgente_${m}.raw" "$l" "$a"
			done
		done
	done
}

events() {
	local m l a
	for m in ${SIZES:-1920x1080 3840x2160}; do
		l=${m%x*}; a=${m#*x}
		for c in ${CODEC:-h264 av1}; do
			for s in ${ROUTES:-vecchia fixed new}; do
				[ "$c" = av1 ] && [ "$s" = fixed ] && continue
				local ext=h264 fmt=h264
				[ "$c" = av1 ] && { ext=obu; fmt=obu; }
				local out="$WORKDIR/events-${c}-${s}-${m}.$ext"
				echo "── events $c $s $m"
				load
				"$BENCH" events "$c" "$s" "$l" "$a" "$WORKDIR" "$out" || continue
				echo "  decoded by ffmpeg: $(ffmpeg -v error -f "$fmt" -i "$out" -f framemd5 - 2>/dev/null | grep -vc '^#') out of 30 · error lines: $(ffmpeg -v error -f "$fmt" -i "$out" -f null - 2>&1 | wc -l)"
				ffprobe -v error -f "$fmt" -show_frames -show_entries frame=width,height,key_frame -of csv=p=0 "$out" | uniq -c | tr '\n' ';'; echo
			done
		done
	done
}

# ⭐ The OpenH264 calibration: one line per combination of settings, on the same
#    scene.  TUNINGS="RIPIEGO_H264_FILI=1,RIPIEGO_H264_CABAC=0 RIPIEGO_H264_FILI=4 …"
calibration() {
	local m=${SIZES:-1920x1080} l a t
	l=${m%x*}; a=${m#*x}
	[ -f "$WORKDIR/sorgente_${m}.raw" ] || "$BENCH" source "$l" "$a" "$WORKDIR" "$N" "$WORKDIR/sorgente_${m}.raw"
	load
	for t in $TUNINGS; do
		local out="$WORKDIR/taratura.h264"
		printf '%s → ' "$t"
		env $(echo "$t" | tr ',' ' ') "$BENCH" encode h264 new "$l" "$a" "$WORKDIR" "$N" "$out" 45 2>/dev/null | sed 's/.*opening /opening /'
		printf '    '
		analyze "$out" h264 "$WORKDIR/sorgente_${m}.raw" "$l" "$a" | tail -1
	done
	load
}

# ⭐ The ffmpeg fingerprints (sum of the luma of each frame) for the
#    comparison with Chrome: `18-software-webcodecs.py` runs on the HOST (where
#    google-chrome is) and reads these .ffmpeg.json.
fingerprints() {
	local f fmt l a
	for f in ${STREAMS:?}; do
		fmt=h264; [ "${f##*.}" = obu ] && fmt=obu
		l=$(ffprobe -v error -f $fmt -show_entries stream=width -of csv=p=0 "$WORKDIR/$f")
		a=$(ffprobe -v error -f $fmt -show_entries stream=height -of csv=p=0 "$WORKDIR/$f")
		ffmpeg -v error -f $fmt -i "$WORKDIR/$f" -f rawvideo -pix_fmt yuv420p - | python3 -c "
import sys, json
n = $l * $a; s = []
while True:
    b = sys.stdin.buffer.read(n * 3 // 2)
    if len(b) < n * 3 // 2: break
    s.append(sum(b[:n]))
json.dump(s, open('$WORKDIR/$f.ffmpeg.json', 'w'))
print('$f', len(s), 'frames')"
	done
}

case "$STEP" in
calibration) calibration ;;
fingerprints) fingerprints ;;
prepare) prepare ;;
build) build ;;
colors) load; for m in ${SIZES:-1920x1080 3840x2160}; do "$BENCH" colors "${m%x*}" "${m#*x}" "$WORKDIR" 24
	echo "  … and in plain C:"; "$BENCH-c" colors "${m%x*}" "${m#*x}" "$WORKDIR" 24 | grep "fingerprint\|time"; done ;;
encode) encode ;;
events) events ;;
refusals) load; mkdir -p "$WORKDIR/refusals"; DUMP_DIR=$WORKDIR/refusals "$BENCH" refusals
	for f in "$WORKDIR"/refusals/*; do echo "$f: $(ffprobe -v error -show_entries stream=profile,level,width,height -of compact=p=0 "$f")"; done ;;
all) prepare && build && bash "$0" colors && bash "$0" encode && bash "$0" events && bash "$0" refusals ;;
*) echo "unknown step: $STEP"; exit 2 ;;
esac
