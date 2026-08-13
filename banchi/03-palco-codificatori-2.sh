#!/bin/bash
# ⛔ SECONDO GIRO — il primo NON era un confronto, e il banco lo accusa da se':
#    VP9 ha consegnato 129 221 byte dove HEVC ne consegnava 3 893 620.
#    ⇒ TRENTA VOLTE meno: non e' lo stesso lavoro, e «piu' veloce» a un
#      trentesimo del bitrate non e' piu' veloce.  Qui si chiede a tutti la
#      STESSA cosa: 20 Mbit/s, e i fotogrammi in uscita si CONTANO.
set -u
D=/tmp/sonda-vp9
cd "$D" || exit 2

echo "== LA SCENA, DICHIARATA =="
echo -n "  carico:     "; uptime
echo -n "  porte 7xxx: "; ss -ltn 2>/dev/null | grep -oE ':7[0-9]{3}' | sort -u | tr '\n' ' '; echo
[ -s src.yuv ] || { echo "⛔ manca il sorgente"; exit 3; }
echo

giro () {
  nome="$1"; shift
  rm -f "out2-$nome"
  t0=$(date +%s.%N)
  "$@" >/dev/null 2>"err2-$nome.txt"
  rc=$?
  t1=$(date +%s.%N)
  by=$(stat -c%s "out2-$nome" 2>/dev/null || echo 0)
  # ⛔ i fotogrammi in uscita si CONTANO: un codificatore che ne butta 60 e'
  #    veloce il doppio, e il cronometro da solo non se ne accorge.
  fo=$(ffprobe -v error -count_frames -select_streams v:0 \
        -show_entries stream=nb_read_frames -of csv=p=0 "out2-$nome" 2>/dev/null)
  [ -z "$fo" ] && fo="?"
  awk -v a="$t0" -v b="$t1" -v n=120 -v nome="$nome" -v by="$by" -v rc="$rc" -v fo="$fo" \
     'BEGIN{ if (rc != 0 || by == 0) printf "  %-20s  ⛔ USCITA %s, %d byte — NON E'"'"' UN NUMERO\n", nome, rc, by;
             else if (fo != "120") printf "  %-20s  ⛔ %s fotogrammi su 120 in uscita — il numero NON VALE (%.2f ms, %d byte)\n", nome, fo, (b-a)*1000/n, by;
             else printf "  %-20s  uscita 0   %7.2f ms/fotogramma   %11d byte   %s fotogrammi\n", nome, (b-a)*1000/n, by, fo }'
  [ $rc -ne 0 ] && head -2 "err2-$nome.txt" | sed 's/^/       /'
  return 0
}

RAW=(-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -r 60 -i src.yuv)
Q=(-hide_banner -loglevel error -y)
B=(-b:v 20M -maxrate 20M -bufsize 40M)

for g in 1 2 3; do
  echo "== GIRO $g — tutti a 20 Mbit/s =="
  giro "svtav1-$g"     ffmpeg "${Q[@]}" "${RAW[@]}" -c:v libsvtav1 -preset 10 "${B[@]}" -f ivf "out2-svtav1-$g"
  giro "hevc_hw-$g"    ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
                          -vf 'format=p010,hwupload' -c:v hevc_vaapi "${B[@]}" -f hevc "out2-hevc_hw-$g"
  giro "vp9_hw-10b-$g" ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
                          -vf 'format=p010,hwupload' -c:v vp9_vaapi "${B[@]}" -f ivf "out2-vp9_hw-10b-$g"
  giro "vp9_hw-8b-$g"  ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
                          -vf 'format=nv12,hwupload' -c:v vp9_vaapi "${B[@]}" -f ivf "out2-vp9_hw-8b-$g"
  giro "h264_hw-$g"    ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
                          -vf 'format=nv12,hwupload' -c:v h264_vaapi "${B[@]}" -f h264 "out2-h264_hw-$g"
  echo
done

echo "== LA SCENA, RILETTA DOPO =="
echo -n "  carico:     "; uptime
