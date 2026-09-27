#!/bin/bash
# 16-d023-cornice.sh — la prova di D-023, dentro una scatola con la scheda da provare.
#
#   (sulla macchina di prova, costruito prima con enter.sh — vedi fasi/16 §17)
#   sudo podman exec rete11-gnome bash /media/REMOTIX/src/controllo/banchi/16-stress/16-d023-cornice.sh \
#        /percorso/16-d023-cornice [/dev/dri/renderD128]
#
# Per ogni codec e ogni misura (le tele VERE di Chrome nella fase 16, nessuna
# multipla di 64): codifica 10 fotogrammi con due chiavi col codificatore del
# PRODOTTO, poi
#   1. `ffprobe` deve leggere nel flusso la misura della TELA (non il multiplo di 64);
#   2. decodificato contro la sorgente, PSNR >= 40 dB: l'immagine dentro e' quella, 1:1
#      (una scala o uno spostamento di una colonna la porterebbero sotto 25).
# ⛔ Senza la cura, sulla Radeon: hevc 2544x1344 → il flusso dichiara 2560, e il
#    prodotto non lo spedisce (0 fotogrammi) — PASS impossibile.
set -u
PROVA=${1:?uso: 16-d023-cornice.sh /percorso/16-d023-cornice [nodo]}
NODO=${2:-/dev/dri/renderD128}
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
esito=0
for codec in hevc h264; do
	for m in 3824x2064 3184x1712 2544x1344 1904x1080; do
		ffmpeg -v error -f lavfi -i "testsrc2=s=$m:r=30" -frames:v 1 -pix_fmt bgr0 -f rawvideo -y "$T/s.bgrx"
		if ! "$PROVA" --codec $codec --misura $m --nodo "$NODO" --sorgente "$T/s.bgrx" \
			--uscita "$T/f.$codec" >"$T/esito" 2>"$T/registro"; then
			echo "FAIL $codec $m: il prodotto non ha spedito ($(grep -m1 '⛔' "$T/registro" | cut -c1-160))"
			esito=1; continue
		fi
		letta=$(ffprobe -v error -show_entries stream=width,height -of csv=p=0:s=x "$T/f.$codec")
		psnr=$(ffmpeg -hide_banner -f $codec -i "$T/f.$codec" -f rawvideo -pix_fmt bgr0 -s $m -i "$T/s.bgrx" \
			-lavfi "[0:v]format=yuv420p[a];[1:v]format=yuv420p,loop=-1:1[b];[a][b]psnr=shortest=1" -f null - 2>&1 \
			| grep -o 'average:[0-9.inf]*' | cut -d: -f2)
		cornice=$(grep -c 'D-023' "$T/registro")
		if [ "$letta" = "$m" ] && awk "BEGIN{exit !(\"$psnr\"==\"inf\" || $psnr+0 >= 40)}"; then
			echo "PASS $codec $m: il flusso dichiara $letta · PSNR $psnr dB · righe D-023 $cornice · $(cat "$T/esito")"
		else
			echo "FAIL $codec $m: il flusso dichiara $letta · PSNR $psnr dB · righe D-023 $cornice"
			esito=1
		fi
	done
done
exit $esito
