#!/bin/bash
# ⭐ SONDA VP9 — la codifica VP9 in hardware esiste su questa macchina?
#
# ⛔ E' una misura di TEMPO ⇒ §0-bis: la scena si DICHIARA e si verifica di
#    essere soli, o il numero e' quello della contesa.
# ⚠ E' la stessa forma del confronto del 13 agosto: 120 fotogrammi 1920x1080
#   a 10 bit, contenuto SINTETICO, portata in blocco e pipelined di ffmpeg
#   — NON il ritardo per fotogramma del cammino seriale del prodotto.
# ⭐ `hevc_vaapi` c'e' dentro APPOSTA: e' il CONTROLLO. Se non torna intorno
#   ai 2,85 ms del 13, il banco non e' confrontabile e il numero di VP9 non
#   si legge.
set -u

D=/tmp/sonda-vp9
mkdir -p "$D" || exit 2
cd "$D" || exit 2

echo "== LA SCENA, DICHIARATA =="
echo -n "  carico:     "; uptime
echo -n "  porte 7xxx: "; ss -ltn 2>/dev/null | grep -oE ':7[0-9]{3}' | sort -u | tr '\n' ' '; echo
echo "  i cinque processi piu' affamati:"
ps -eo pcpu,pid,comm --sort=-pcpu | head -6 | sed 's/^/    /'
echo

echo "== IL SORGENTE — 120 fotogrammi 1920x1080 10 bit, sintetici =="
if [ ! -s src.yuv ]; then
  ffmpeg -hide_banner -loglevel error -y -f lavfi -i testsrc2=size=1920x1080:rate=60 \
     -frames:v 120 -pix_fmt yuv420p10le -f rawvideo src.yuv || { echo "⛔ sorgente non fatto"; exit 3; }
fi
ATTESI=$((1920*1080*3*120))
VERI=$(stat -c%s src.yuv)
echo "  src.yuv: $VERI byte (attesi $ATTESI)"
[ "$VERI" = "$ATTESI" ] || { echo "⛔ il sorgente non ha la taglia attesa"; exit 4; }
echo

giro () {
  nome="$1"; shift
  rm -f "out-$nome"
  t0=$(date +%s.%N)
  "$@" >/dev/null 2>"err-$nome.txt"
  rc=$?
  t1=$(date +%s.%N)
  by=$(stat -c%s "out-$nome" 2>/dev/null || echo 0)
  awk -v a="$t0" -v b="$t1" -v n=120 -v nome="$nome" -v by="$by" -v rc="$rc" \
     'BEGIN{ if (rc != 0 || by == 0) printf "  %-20s  ⛔ USCITA %s, %d byte — NON E'"'"' UN NUMERO\n", nome, rc, by;
             else printf "  %-20s  uscita %s   %7.2f ms/fotogramma   %11d byte\n", nome, rc, (b-a)*1000/n, by }'
  [ $rc -ne 0 ] && head -3 "err-$nome.txt" | sed 's/^/       /'
  return 0
}

RAW=(-f rawvideo -pix_fmt yuv420p10le -s 1920x1080 -r 60 -i src.yuv)
Q=(-hide_banner -loglevel error -y)

for g in 1 2 3; do
  echo "== GIRO $g =="

  giro "svtav1-p10-$g" ffmpeg "${Q[@]}" "${RAW[@]}" \
      -c:v libsvtav1 -preset 10 -f ivf "out-svtav1-p10-$g"

  giro "hevc_vaapi128-$g" ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
      -vf 'format=p010,hwupload' -c:v hevc_vaapi -f hevc "out-hevc_vaapi128-$g"

  giro "vp9_vaapi128-10b-$g" ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
      -vf 'format=p010,hwupload' -c:v vp9_vaapi -f ivf "out-vp9_vaapi128-10b-$g"

  giro "vp9_vaapi128-8b-$g" ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
      -vf 'format=nv12,hwupload' -c:v vp9_vaapi -f ivf "out-vp9_vaapi128-8b-$g"

  giro "av1_vaapi128-$g" ffmpeg "${Q[@]}" -vaapi_device /dev/dri/renderD128 "${RAW[@]}" \
      -vf 'format=p010,hwupload' -c:v av1_vaapi -f ivf "out-av1_vaapi128-$g"
  echo
done

echo "== LA SCENA, RILETTA DOPO =="
echo -n "  carico:     "; uptime
echo -n "  porte 7xxx: "; ss -ltn 2>/dev/null | grep -oE ':7[0-9]{3}' | sort -u | tr '\n' ' '; echo
