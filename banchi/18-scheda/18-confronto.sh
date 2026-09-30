#!/bin/bash
# 18-confronto.sh — vecchia strada (libavcodec) contro nuova (libva diretta), sul
# server, dentro `enter.sh --root` (serve l'accesso ai nodi DRM).
#
#   bash /media/REMOTIX/enter.sh --root 'bash /srv/src/f18-scheda/banchi/18-scheda/18-confronto.sh [costruisci|tutto|corto]'
#
# Si aspetta in $ALBERO (default /srv/src/f18-scheda/albero):
#   src/                 il sorgente NUOVO (codificatore.c, vadiretta.c, scrittore_bit.c, registro.c…)
#   vecchio/codificatore.c   il codificatore del commit di partenza (545ec55)
#   banchi/18-scheda/    questo banco
# Scrive in $USCITA (default /srv/src/f18-scheda/tmp/confronto): i flussi, i
# registri, `esiti.jsonl` (una riga per prova) e la tabella (`18-tabella.py`).
set -u
ALBERO=${ALBERO:-/srv/src/f18-scheda/albero}
USCITA=${USCITA:-/srv/src/f18-scheda/tmp/confronto}
AZIONE=${1:-tutto}
FOTOGRAMMI=${FOTOGRAMMI:-120}
FPS=60
mkdir -p "$USCITA"
cd "$ALBERO" || exit 1

costruisci() {
	local F="-std=gnu11 -O2 -g -D_GNU_SOURCE -I$ALBERO/src -Wall -Wno-unused-parameter"
	local INC LIBS
	INC=$(pkg-config --cflags libva libva-drm libavcodec libavutil libswscale gbm libdrm)
	LIBS=$(pkg-config --libs libva libva-drm libavcodec libavutil libswscale gbm)
	echo "== costruisco 18-confronto-nuovo"
	gcc $F $INC -o "$USCITA/18-confronto-nuovo" banchi/18-scheda/18-confronto.c \
		src/codificatore.c src/vadiretta.c src/scrittore_bit.c src/registro.c $LIBS -lm || return 1
	echo "== costruisco 18-confronto-vecchio"
	gcc $F $INC -o "$USCITA/18-confronto-vecchio" banchi/18-scheda/18-confronto.c \
		vecchio/codificatore.c src/registro.c $LIBS -lm || return 1
	echo "== costruiti"
}

# prova NOME VERSIONE NODO CODEC PROF MISURA STRADA [argomenti extra…]
prova() {
	local nome=$1 versione=$2 nodo=$3 codec=$4 prof=$5 misura=$6 strada=$7; shift 7
	local flusso="$USCITA/$nome-$versione.bin" registro="$USCITA/$nome-$versione.registro"
	local csv="$USCITA/$nome-$versione.csv" sorgente="$USCITA/sorgente-$misura.bgrx"
	local extra_src=""
	[ -f "$sorgente" ] || extra_src="--sorgente-out $sorgente"
	local t0 t1
	t0=$(date +%s.%N)
	"$USCITA/18-confronto-$versione" --codec "$codec" --profondita "$prof" --misura "$misura" \
		--nodo "/dev/dri/renderD$nodo" --strada "$strada" --uscita "$flusso" \
		--fotogrammi "$FOTOGRAMMI" --fps $FPS $extra_src "$@" > "$csv" 2> "$registro"
	local codice=$?
	t1=$(date +%s.%N)
	local json
	json=$(tail -1 "$csv")
	[ "${json:0:1}" = "{" ] || json='{"esito":"nessuna riga"}'
	# la decodifica con ffmpeg, fotogramma per fotogramma
	local fmt=$codec; [ "$codec" = hevc ] && fmt=hevc
	local decodificati errori_dec
	errori_dec=$(ffmpeg -v error -f $fmt -i "$flusso" -f null - 2>&1 | grep -c .)
	decodificati=$(ffprobe -v error -f $fmt -count_frames -show_entries stream=nb_read_frames -of csv=p=0 "$flusso" 2>/dev/null)
	local probe
	probe=$(ffprobe -v error -f $fmt -show_entries stream=profile,level,width,height,pix_fmt,color_range,color_space,color_transfer,color_primaries -of csv=p=0 "$flusso" 2>/dev/null | head -1)
	# PSNR e SSIM contro la sorgente, solo se la misura non e' cambiata a meta'
	local psnr="" ssim=""
	if [ -f "$sorgente" ] && [ -z "$(echo "$@" | grep -o ridimensiona)" ]; then
		local pix=yuv420p; [ "$prof" = 10 ] && pix=yuv420p10le
		# ⚠ `-v info`: i due filtri stampano il verdetto a livello info, con -v error tacciono
		psnr=$(ffmpeg -v info -f $fmt -r $FPS -i "$flusso" -f rawvideo -pix_fmt bgr0 -s "$misura" -r $FPS -i "$sorgente" \
			-lavfi "[1:v]scale=out_color_matrix=bt709:out_range=tv,format=$pix[r];[0:v]format=$pix[a];[a][r]psnr" -f null - 2>&1 \
			| grep -o 'PSNR y:[0-9.inf]* u:[0-9.inf]* v:[0-9.inf]* average:[0-9.inf]*' | tail -1 | sed 's/PSNR //')
		ssim=$(ffmpeg -v info -f $fmt -r $FPS -i "$flusso" -f rawvideo -pix_fmt bgr0 -s "$misura" -r $FPS -i "$sorgente" \
			-lavfi "[1:v]scale=out_color_matrix=bt709:out_range=tv,format=$pix[r];[0:v]format=$pix[a];[a][r]ssim" -f null - 2>&1 \
			| grep -o 'All:[0-9.]*' | tail -1 | cut -d: -f2)
	fi
	local byte
	byte=$(stat -c %s "$flusso" 2>/dev/null)
	printf '{"prova":"%s","versione":"%s","nodo":"renderD%s","codec":"%s","profondita":%s,"misura":"%s","strada":"%s","extra":"%s","codice":%s,"secondi":%.2f,"byte_flusso":%s,"decodificati":"%s","errori_decodifica":%s,"ffprobe":"%s","psnr":"%s","ssim":"%s","banco":%s}\n' \
		"$nome" "$versione" "$nodo" "$codec" "$prof" "$misura" "$strada" "$*" "$codice" "$(awk "BEGIN{print $t1 - $t0}")" "${byte:-0}" "${decodificati:-?}" "${errori_dec:-0}" "$probe" "$psnr" "$ssim" "$json" >> "$USCITA/esiti.jsonl"
	echo "   $nome $versione: codice $codice · ${byte:-0} byte · decodificati ${decodificati:-?} · psnr ${psnr:-—} · ssim ${ssim:-—} · $probe"
}

matrice() {
	local nodi="128 129" misure="1920x1080 3840x2160" strade="memoria scheda"
	[ "$AZIONE" = corto ] && misure="1920x1080"
	for nodo in $nodi; do
		for cp in "h264 8" "hevc 8" "hevc 10"; do
			set -- $cp; local codec=$1 prof=$2
			for misura in $misure; do
				for strada in $strade; do
					local nome="D$nodo-$codec$prof-$misura-$strada"
					echo "== $nome"
					for versione in vecchio nuovo; do
						prova "$nome" "$versione" "$nodo" "$codec" "$prof" "$misura" "$strada"
					done
				done
			done
		done
	done
	# le tre prove «a caldo», 1080p, strada della scheda, H.264 e HEVC 8, sui due nodi
	for nodo in $nodi; do
		for codec in h264 hevc; do
			local base="D$nodo-${codec}8-1920x1080"
			echo "== $base chiave a richiesta / tela nuova / tetto"
			for versione in vecchio nuovo; do
				prova "$base-chiave" "$versione" "$nodo" "$codec" 8 1920x1080 scheda --chiave-a 40
				prova "$base-tela" "$versione" "$nodo" "$codec" 8 1920x1080 scheda --ridimensiona-a 60:1280x720
				prova "$base-tetto" "$versione" "$nodo" "$codec" 8 1920x1080 scheda --tetto 20
			done
		done
	done
}

case "$AZIONE" in
costruisci) costruisci ;;
tutto|corto)
	costruisci || exit 1
	: > "$USCITA/esiti.jsonl"
	matrice
	python3 banchi/18-scheda/18-tabella.py "$USCITA/esiti.jsonl" | tee "$USCITA/tabella.txt"
	rm -f "$USCITA"/sorgente-*.bgrx
	;;
*) echo "azione ignota: $AZIONE"; exit 2 ;;
esac
