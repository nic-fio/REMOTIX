#!/bin/bash
# 19-confronto.sh — Vulkan Video (`src/vulkanvideo.c`) contro VA-API (il prodotto,
# `src/codificatore.c` + `src/vadiretta.c`) sulla STESSA scheda, sul server,
# dentro `enter.sh --root` (serve l'accesso ai nodi DRM).
#
#   bash /media/REMOTIX/enter.sh --root 'bash /srv/src/f19-vulkan/albero/banchi/19-vulkan/19-confronto.sh [costruisci|tutto|corto|capacita|intel]'
#
# Si aspetta in $ALBERO (default /srv/src/f19-vulkan/albero) l'albero del
# worktree (src/ e banchi/).  Scrive in $USCITA (default /srv/src/f19-vulkan/tmp/confronto):
# i flussi, i registri, `esiti.jsonl` (una riga per prova) e la tabella (`19-tabella.py`).
#
# ⚠ ffmpeg/ffprobe qui sono SOLO strumenti di misura (decodifica, PSNR/SSIM,
#   profilo/livello): non entrano nel prodotto.
set -u
ALBERO=${ALBERO:-/srv/src/f19-vulkan/albero}
USCITA=${USCITA:-/srv/src/f19-vulkan/tmp/confronto}
AZIONE=${1:-tutto}
FOTOGRAMMI=${FOTOGRAMMI:-120}
NODO_RADEON=${NODO_RADEON:-129}
NODO_INTEL=${NODO_INTEL:-128}
FPS=60
mkdir -p "$USCITA"
cd "$ALBERO" || exit 1

costruisci() {
	local F="-std=gnu11 -O2 -g -D_GNU_SOURCE -I$ALBERO/src -Wall -Wextra -Wno-unused-parameter -Wno-missing-field-initializers"
	bash banchi/19-vulkan/19-shader.sh || return 1
	echo "== costruisco 19-confronto"
	local RIPIEGO="" RIPIEGO_LIBS=""
	if [ -f src/ripiego.c ]; then
		# l'albero di partenza (fase-10-cure) ha ancora il ripiego software: si collega per compilare il prodotto
		RIPIEGO="src/ripiego.c $(pkg-config --cflags openh264 SvtAv1Enc)"
		RIPIEGO_LIBS="$(pkg-config --libs SvtAv1Enc) -ldl"
	fi
	gcc $F $(pkg-config --cflags libva libva-drm gbm libdrm vulkan) -o "$USCITA/19-confronto" \
		banchi/19-vulkan/19-confronto.c \
		src/vulkanvideo.c src/codificatore.c src/vadiretta.c src/scrittore_bit.c src/colori709.c \
		src/registro.c $RIPIEGO $(pkg-config --libs libva libva-drm gbm vulkan) $RIPIEGO_LIBS -lm || return 1
	if nm -u "$USCITA/19-confronto" | grep -qE ' (av_|avcodec_|sws_)'; then
		echo "⛔ il banco chiama ffmpeg"; return 1
	fi
	echo "== costruito"
}

# prova NOME MOTORE NODO CODEC PROF MISURA STRADA [argomenti extra…]
prova() {
	local nome=$1 motore=$2 nodo=$3 codec=$4 prof=$5 misura=$6 strada=$7; shift 7
	local flusso="$USCITA/$nome-$motore.bin" registro="$USCITA/$nome-$motore.registro"
	local csv="$USCITA/$nome-$motore.csv" sorgente="$USCITA/sorgente-$misura.bgrx"
	local extra_src=""
	[ -f "$sorgente" ] || extra_src="--sorgente-out $sorgente"
	local t0 t1
	t0=$(date +%s.%N)
	"$USCITA/19-confronto" --motore "$motore" --codec "$codec" --profondita "$prof" --misura "$misura" \
		--nodo "/dev/dri/renderD$nodo" --strada "$strada" --uscita "$flusso" \
		--fotogrammi "$FOTOGRAMMI" --fps $FPS $extra_src "$@" > "$csv" 2> "$registro"
	local codice=$?
	t1=$(date +%s.%N)
	local json
	json=$(tail -1 "$csv")
	[ "${json:0:1}" = "{" ] || json='{"esito":"nessuna riga"}'
	local fmt=$codec
	local decodificati errori_dec
	errori_dec=$(ffmpeg -v error -f $fmt -i "$flusso" -f null - 2>&1 | grep -c .)
	decodificati=$(ffprobe -v error -f $fmt -count_frames -show_entries stream=nb_read_frames -of csv=p=0 "$flusso" 2>/dev/null)
	local probe
	probe=$(ffprobe -v error -f $fmt -show_entries stream=profile,level,width,height,pix_fmt,color_range,color_space,color_transfer,color_primaries -of csv=p=0 "$flusso" 2>/dev/null | head -1)
	local psnr="" ssim=""
	if [ -f "$sorgente" ] && [ -z "$(echo "$@" | grep -o ridimensiona)" ]; then
		local pix=yuv420p; [ "$prof" = 10 ] && pix=yuv420p10le
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
		"$nome" "$motore" "$nodo" "$codec" "$prof" "$misura" "$strada" "$*" "$codice" "$(awk "BEGIN{print $t1 - $t0}")" "${byte:-0}" "${decodificati:-?}" "${errori_dec:-0}" "$probe" "$psnr" "$ssim" "$json" >> "$USCITA/esiti.jsonl"
	echo "   $nome $motore: codice $codice · ${byte:-0} byte · decodificati ${decodificati:-?} · psnr ${psnr:-—} · ssim ${ssim:-—} · $probe"
}

matrice() {
	local nodo=$NODO_RADEON misure="1920x1080 3840x2160" strade="memoria scheda"
	[ "$AZIONE" = corto ] && misure="1920x1080"
	for cp in "h264 8" "hevc 8" "hevc 10"; do
		set -- $cp; local codec=$1 prof=$2
		for misura in $misure; do
			for strada in $strade; do
				local nome="D$nodo-$codec$prof-$misura-$strada"
				echo "== $nome"
				for motore in vaapi vulkan; do
					prova "$nome" "$motore" "$nodo" "$codec" "$prof" "$misura" "$strada"
				done
			done
		done
	done
	# a caldo: chiave a richiesta, tela nuova, tetto di banda, qualita' nuova
	for codec in h264 hevc; do
		local base="D$nodo-${codec}8-1920x1080"
		echo "== $base chiave a richiesta / tela nuova / tetto / qualita'"
		for motore in vaapi vulkan; do
			prova "$base-chiave" "$motore" "$nodo" "$codec" 8 1920x1080 scheda --chiave-a 40
			prova "$base-tela" "$motore" "$nodo" "$codec" 8 1920x1080 scheda --ridimensiona-a 60:1280x720
			prova "$base-tetto" "$motore" "$nodo" "$codec" 8 1920x1080 scheda --tetto 20
			# un tetto che MORDE: 2 Mbit/s (filo 1,6, punto 1,2) su una scena che a QP 26 ne costa ~8
			prova "$base-tetto2" "$motore" "$nodo" "$codec" 8 1920x1080 scheda --tetto 2
		done
		prova "$base-qualita" vulkan "$nodo" "$codec" 8 1920x1080 scheda --qualita-a 60:36
	done
}

# ⚠ L'ESPERIMENTO Intel: ANV codifica solo dietro `ANV_DEBUG=video-encode`
# (sperimentale, non di serie): si dichiara, non si promette.
intel() {
	local nodo=$NODO_INTEL
	echo "== capacita' Intel senza e con ANV_DEBUG=video-encode"
	"$USCITA/19-confronto" --capacita /dev/dri/renderD$nodo | tee "$USCITA/capacita-intel.json"
	ANV_DEBUG=video-encode "$USCITA/19-confronto" --capacita /dev/dri/renderD$nodo | tee "$USCITA/capacita-intel-anv-debug.json"
	for codec in h264 hevc; do
		local nome="D$nodo-${codec}8-1920x1080-scheda-ANV"
		echo "== $nome"
		ANV_DEBUG=video-encode prova "$nome" vulkan "$nodo" "$codec" 8 1920x1080 scheda
		prova "$nome" vaapi "$nodo" "$codec" 8 1920x1080 scheda
	done
}

case "$AZIONE" in
costruisci) costruisci ;;
capacita)
	for n in $NODO_RADEON $NODO_INTEL; do
		"$USCITA/19-confronto" --capacita /dev/dri/renderD$n | tee "$USCITA/capacita-renderD$n.json"
	done ;;
intel) intel ;;
tutto|corto)
	costruisci || exit 1
	: > "$USCITA/esiti.jsonl"
	"$USCITA/19-confronto" --capacita /dev/dri/renderD$NODO_RADEON | tee "$USCITA/capacita-renderD$NODO_RADEON.json"
	matrice
	python3 banchi/19-vulkan/19-tabella.py "$USCITA/esiti.jsonl" | tee "$USCITA/tabella.txt"
	rm -f "$USCITA"/sorgente-*.bgrx
	;;
*) echo "azione ignota: $AZIONE"; exit 2 ;;
esac
