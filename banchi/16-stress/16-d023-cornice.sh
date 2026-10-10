#!/bin/bash
# 16-d023-cornice.sh — the test of D-023, inside a box with the card to be tested.
#
#   (on the test machine, built beforehand with enter.sh — see fasi/16 §17)
#   sudo podman exec rete11-gnome bash /media/REMOTIX/src/controllo/banchi/16-stress/16-d023-cornice.sh \
#        /path/16-d023-cornice [/dev/dri/renderD128]
#
# For every codec and every size (the REAL canvases of Chrome in phase 16, none
# a multiple of 64): encodes 10 frames with two keyframes with the PRODUCT's
# encoder, then
#   1. `ffprobe` must read in the stream the size of the CANVAS (not the multiple of 64);
#   2. decoded against the source, PSNR >= 40 dB: the image inside is that one, 1:1
#      (a scaling or a shift by one column would bring it below 25).
# ⛔ Without the cure, on the Radeon: hevc 2544x1344 → the stream declares 2560, and the
#    product does not send it (0 frames) — PASS impossible.
set -u
PROVA=${1:?usage: 16-d023-cornice.sh /path/16-d023-cornice [node]}
NODO=${2:-/dev/dri/renderD128}
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
esito=0
for codec in hevc h264; do
	for m in 3824x2064 3184x1712 2544x1344 1904x1080; do
		ffmpeg -v error -f lavfi -i "testsrc2=s=$m:r=30" -frames:v 1 -pix_fmt bgr0 -f rawvideo -y "$T/s.bgrx"
		if ! "$PROVA" --codec $codec --misura $m --nodo "$NODO" --sorgente "$T/s.bgrx" \
			--uscita "$T/f.$codec" >"$T/esito" 2>"$T/registro"; then
			echo "FAIL $codec $m: the product did not send ($(grep -m1 '⛔' "$T/registro" | cut -c1-160))"
			esito=1; continue
		fi
		letta=$(ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x "$T/f.$codec")
		psnr=$(ffmpeg -hide_banner -f $codec -i "$T/f.$codec" -f rawvideo -pix_fmt bgr0 -s $m -i "$T/s.bgrx" \
			-lavfi "[0:v]format=yuv420p[a];[1:v]format=yuv420p,loop=-1:1[b];[a][b]psnr=shortest=1" -f null - 2>&1 \
			| grep -o 'average:[0-9.inf]*' | cut -d: -f2)
		cornice=$(grep -c 'D-023' "$T/registro")
		if [ "$letta" = "$m" ] && awk "BEGIN{exit !(\"$psnr\"==\"inf\" || $psnr+0 >= 40)}"; then
			echo "PASS $codec $m: the stream declares $letta · PSNR $psnr dB · D-023 lines $cornice · $(cat "$T/esito")"
		else
			echo "FAIL $codec $m: the stream declares $letta · PSNR $psnr dB · D-023 lines $cornice"
			esito=1
		fi
	done
done
exit $esito
