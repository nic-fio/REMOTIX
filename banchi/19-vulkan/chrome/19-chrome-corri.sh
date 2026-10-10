#!/bin/bash
# 19-chrome-corri.sh STREAM.bin [codec] [hw] [w] [h] — decodes an Annex-B stream
# (produced by 19-confronto) with Chrome's VideoDecoder, with the same
# configuration as the product's page, and writes for every frame the dominant
# colour: (0,136,0) = all-zero YUV frame (the green of F-002, 1 Oct 2026).
# Expects in $D a labwc of its own (wayland-0 in $D/run, WLR_BACKENDS=headless,
# WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128 — NEVER the suite's compositors) and
# `python3 19-chrome-servi.py 9401 $D $D/esito.tmp` with the page and the streams in $D.
D=/media/REMOTIX/src/f19-chrome
export XDG_RUNTIME_DIR=$D/run WAYLAND_DISPLAY=wayland-0
F=$1; C=${2:-hev1.1.6.L153.B0}; HW=${3:-no-preference}; L=${4:-3840}; A=${5:-2160}
P=$D/profilo-$$; rm -rf $P; mkdir -p $P
: > $D/esito.tmp
timeout 120 google-chrome --user-data-dir=$P --no-first-run --no-default-browser-check --disable-sync \
  --password-store=basic --window-size=1400,1000 --ozone-platform=wayland \
  --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling \
  --enable-logging=stderr --v=0 $CHROME_EXTRA \
  "http://127.0.0.1:9401/19-chrome-prova.html?f=$F&codec=$C&hw=$HW&l=$L&a=$A" > $D/chrome.log 2>&1 &
CP=$!
for i in $(seq 100); do [ -s $D/esito.tmp ] && break; sleep 1; done
kill $CP 2>/dev/null; sleep 2; pkill -f "user-data-dir=$P" 2>/dev/null; sleep 1
rm -rf $P
cat $D/esito.tmp
