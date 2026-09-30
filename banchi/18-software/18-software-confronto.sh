#!/bin/bash
#
# 18-software-confronto.sh — fase 18, linea V-software: il banco che confronta
# il ripiego VECCHIO (libx264/libsvtav1 via libavcodec + sws_scale) col NUOVO
# (OpenH264, SVT-AV1 diretta, colori709), sulla stessa scena di desktop.
#
# Si lancia SULLA MACCHINA DI PROVA, dentro l'ambiente di sviluppo:
#
#   bash /media/REMOTIX/enter.sh "bash /srv/src/f18-software/banchi/18-software/18-software-confronto.sh [passo]"
#
# passi: prepara | costruisci | colori | codifica | eventi | rifiuti | tutto (predefinito)
# Le regole di OpenH264 da tarare passano per l'ambiente (RIPIEGO_H264_*),
# lette solo perche' il banco compila con -DRIPIEGO_BANCO.
#
# ⚠ I tempi dipendono dal carico: la riga `uptime` va in testa a ogni risultato,
#   perche' altri agenti usano la macchina in parallelo.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
# ⚠ /media/REMOTIX/tmp dell'host non si vede da dentro: il lavoro sta accanto
#   ai sorgenti, nella cartella nostra.
LAVORO=${F18_LAVORO:-$ALBERO/lavoro}
N=${N:-120}
PASSO=${1:-tutto}
BANCO=$LAVORO/18-software-confronto
mkdir -p "$LAVORO"

carico() { printf '⏱ carico: %s\n' "$(uptime | sed 's/.*load average/load average/')"; }

prepara() {
	local l a k dl da fs
	[ -f "$LAVORO/l1.png" ] || { echo "⛔ manca $LAVORO/l1.png (lo sfondo vero)"; exit 2; }
	expand -t 8 "$ALBERO/src/codificatore.c" | sed -n '1,420p' > "$LAVORO/testo.txt"
	for m in 1920x1080 3840x2160; do
		l=${m%x*}; a=${m#*x}
		[ -f "$LAVORO/sfondo_${m}.bgr0" ] || ffmpeg -v error -y -i "$LAVORO/l1.png" \
			-vf "scale=${l}:${a}:flags=lanczos" -pix_fmt bgr0 -f rawvideo "$LAVORO/sfondo_${m}.bgr0"
		k=$((l / 1920))
		dl=$(( (1092 * k) & ~1 )); da=$(( ((780 + 18 * 70) * k) & ~1 )); fs=$((15 * k))
		[ -f "$LAVORO/doc_${dl}x${da}.bgr0" ] || ffmpeg -v error -y -f lavfi \
			-i "color=c=0xfdfdfd:s=${dl}x${da}" -vf \
"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:textfile=$LAVORO/testo.txt:fontsize=${fs}:fontcolor=0x202020:expansion=none:x=$((8 * k)):y=$((6 * k))" \
			-frames:v 1 -pix_fmt bgr0 -f rawvideo "$LAVORO/doc_${dl}x${da}.bgr0"
	done
	ls -la "$LAVORO"/*.bgr0
}

costruisci() {
	gcc -O2 -g -std=gnu11 -D_GNU_SOURCE -DRIPIEGO_BANCO -Wall -Wextra \
		-o "$BANCO" "$QUI/18-software-confronto.c" "$ALBERO/src/ripiego.c" \
		"$ALBERO/src/colori709.c" "$ALBERO/src/registro.c" \
		$(pkg-config --cflags openh264) \
		$(pkg-config --cflags --libs libavcodec libavutil libswscale SvtAv1Enc) \
		-lyuv -ldl -lm && echo "costruito: $BANCO"
	# la stessa, con la conversione in C semplice: i byte devono coincidere
	gcc -O2 -std=gnu11 -D_GNU_SOURCE -DRIPIEGO_BANCO -DCOLORI709_SENZA_SIMD \
		-o "$BANCO-c" "$QUI/18-software-confronto.c" "$ALBERO/src/ripiego.c" \
		"$ALBERO/src/colori709.c" "$ALBERO/src/registro.c" \
		$(pkg-config --cflags openh264) \
		$(pkg-config --cflags --libs libavcodec libavutil libswscale SvtAv1Enc) \
		-lyuv -ldl -lm && echo "costruito: $BANCO-c (senza SIMD)"
}

# medie e minimi dai file di statistica di ffmpeg
riassumi() { # $1 psnr.log $2 ssim.log $3 rgb.log
	awk '{for(i=1;i<=NF;i++){split($i,kv,":"); if(kv[1]=="psnr_y"){y+=kv[2]; if(!n||kv[2]<my)my=kv[2]} if(kv[1]=="psnr_avg"){s+=kv[2]}} n++}
	     END{printf "PSNR-Y media %.2f min %.2f · PSNR-YUV media %.2f", y/n, my, s/n}' "$1"
	awk '{for(i=1;i<=NF;i++){split($i,kv,":"); if(kv[1]=="All"){s+=kv[2]; if(!n||kv[2]<m)m=kv[2]}} n++}
	     END{printf " · SSIM media %.5f min %.5f", s/n, m}' "$2"
	awk '{for(i=1;i<=NF;i++){split($i,kv,":"); if(kv[1]=="psnr_avg"){s+=kv[2]; if(!n||kv[2]<m)m=kv[2]}} n++}
	     END{printf " · PSNR-RGB media %.2f min %.2f\n", s/n, m}' "$3"
}

analizza() { # $1 flusso $2 formato(h264|obu) $3 sorgente.raw $4 l $5 a
	local f=$1 fmt=$2 src=$3 l=$4 a=$5
	ffprobe -v error -f "$fmt" -count_frames -select_streams v:0 \
		-show_entries stream=codec_name,profile,level,width,height,pix_fmt,color_space,color_range,color_primaries,color_transfer,nb_read_frames \
		-of compact=p=0 "$f"
	local errori
	errori=$(ffmpeg -v error -f "$fmt" -i "$f" -f null - 2>&1 | wc -l)
	echo "righe d'errore del decodificatore: $errori"
	ffmpeg -v error -y -f rawvideo -pix_fmt bgr0 -s "${l}x${a}" -r 60 -i "$src" -f "$fmt" -r 60 -i "$f" -lavfi \
"[0:v]scale=out_color_matrix=bt709:out_range=tv:flags=bilinear,format=yuv420p,split[r1][r2];[1:v]format=yuv420p,split[d1][d2];[d1][r1]psnr=stats_file=$f.psnr;[d2][r2]ssim=stats_file=$f.ssim" \
		-f null -
	ffmpeg -v error -y -f rawvideo -pix_fmt bgr0 -s "${l}x${a}" -r 60 -i "$src" -f "$fmt" -r 60 -i "$f" -lavfi \
"[0:v]format=gbrp[r];[1:v]scale=in_color_matrix=bt709:in_range=tv:flags=bilinear,format=gbrp[d];[d][r]psnr=stats_file=$f.rgb" \
		-f null -
	riassumi "$f.psnr" "$f.ssim" "$f.rgb"
}

codifica() {
	local m l a
	for m in ${MISURE:-1920x1080 3840x2160}; do
		l=${m%x*}; a=${m#*x}
		[ -f "$LAVORO/sorgente_${m}.raw" ] || "$BANCO" sorgente "$l" "$a" "$LAVORO" "$N" "$LAVORO/sorgente_${m}.raw"
		for c in ${CODEC:-h264 av1}; do
			for s in ${STRADE:-vecchia corretta nuova}; do
				[ "$c" = av1 ] && [ "$s" = corretta ] && continue
				local ext=h264 fmt=h264
				[ "$c" = av1 ] && { ext=obu; fmt=obu; }
				local out="$LAVORO/${c}-${s}-${m}${ETICHETTA:-}.$ext"
				echo "── $c $s $m ${ETICHETTA:-}"
				carico
				"$BANCO" codifica "$c" "$s" "$l" "$a" "$LAVORO" "$N" "$out" 45 || continue
				analizza "$out" "$fmt" "$LAVORO/sorgente_${m}.raw" "$l" "$a"
			done
		done
	done
}

eventi() {
	local m l a
	for m in ${MISURE:-1920x1080 3840x2160}; do
		l=${m%x*}; a=${m#*x}
		for c in ${CODEC:-h264 av1}; do
			for s in ${STRADE:-vecchia corretta nuova}; do
				[ "$c" = av1 ] && [ "$s" = corretta ] && continue
				local ext=h264 fmt=h264
				[ "$c" = av1 ] && { ext=obu; fmt=obu; }
				local out="$LAVORO/eventi-${c}-${s}-${m}.$ext"
				echo "── eventi $c $s $m"
				carico
				"$BANCO" eventi "$c" "$s" "$l" "$a" "$LAVORO" "$out" || continue
				echo "  decodificati da ffmpeg: $(ffmpeg -v error -f "$fmt" -i "$out" -f framemd5 - 2>/dev/null | grep -vc '^#') su 30 · righe d'errore: $(ffmpeg -v error -f "$fmt" -i "$out" -f null - 2>&1 | wc -l)"
				ffprobe -v error -f "$fmt" -show_frames -show_entries frame=width,height,key_frame -of csv=p=0 "$out" | uniq -c | tr '\n' ';'; echo
			done
		done
	done
}

# ⭐ La taratura di OpenH264: una riga per combinazione di regole, sulla stessa
#    scena.  TARATURE="RIPIEGO_H264_FILI=1,RIPIEGO_H264_CABAC=0 RIPIEGO_H264_FILI=4 …"
taratura() {
	local m=${MISURE:-1920x1080} l a t
	l=${m%x*}; a=${m#*x}
	[ -f "$LAVORO/sorgente_${m}.raw" ] || "$BANCO" sorgente "$l" "$a" "$LAVORO" "$N" "$LAVORO/sorgente_${m}.raw"
	carico
	for t in $TARATURE; do
		local out="$LAVORO/taratura.h264"
		printf '%s → ' "$t"
		env $(echo "$t" | tr ',' ' ') "$BANCO" codifica h264 nuova "$l" "$a" "$LAVORO" "$N" "$out" 45 2>/dev/null | sed 's/.*apertura/apertura/'
		printf '    '
		analizza "$out" h264 "$LAVORO/sorgente_${m}.raw" "$l" "$a" | tail -1
	done
	carico
}

# ⭐ Le impronte di ffmpeg (somma della luma di ogni fotogramma) per il
#    confronto con Chrome: `18-software-webcodecs.py` gira sull'HOST (dove c'e'
#    google-chrome) e legge questi .ffmpeg.json.
impronte() {
	local f fmt l a
	for f in ${FLUSSI:?}; do
		fmt=h264; [ "${f##*.}" = obu ] && fmt=obu
		l=$(ffprobe -v error -f $fmt -show_entries stream=width -of csv=p=0 "$LAVORO/$f")
		a=$(ffprobe -v error -f $fmt -show_entries stream=height -of csv=p=0 "$LAVORO/$f")
		ffmpeg -v error -f $fmt -i "$LAVORO/$f" -f rawvideo -pix_fmt yuv420p - | python3 -c "
import sys, json
n = $l * $a; s = []
while True:
    b = sys.stdin.buffer.read(n * 3 // 2)
    if len(b) < n * 3 // 2: break
    s.append(sum(b[:n]))
json.dump(s, open('$LAVORO/$f.ffmpeg.json', 'w'))
print('$f', len(s), 'fotogrammi')"
	done
}

case "$PASSO" in
taratura) taratura ;;
impronte) impronte ;;
prepara) prepara ;;
costruisci) costruisci ;;
colori) carico; for m in ${MISURE:-1920x1080 3840x2160}; do "$BANCO" colori "${m%x*}" "${m#*x}" "$LAVORO" 24
	echo "  … e in C semplice:"; "$BANCO-c" colori "${m%x*}" "${m#*x}" "$LAVORO" 24 | grep "impronta\|tempo"; done ;;
codifica) codifica ;;
eventi) eventi ;;
rifiuti) carico; mkdir -p "$LAVORO/rifiuti"; SCRIVI=$LAVORO/rifiuti "$BANCO" rifiuti
	for f in "$LAVORO"/rifiuti/*; do echo "$f: $(ffprobe -v error -show_entries stream=profile,level,width,height -of compact=p=0 "$f")"; done ;;
tutto) prepara && costruisci && bash "$0" colori && bash "$0" codifica && bash "$0" eventi && bash "$0" rifiuti ;;
*) echo "passo ignoto: $PASSO"; exit 2 ;;
esac
