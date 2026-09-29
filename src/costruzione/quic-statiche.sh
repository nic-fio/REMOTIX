#!/bin/sh
# quic-statiche.sh — nghttp3 e ngtcp2 dai sorgenti, SOLO statiche, in /usr/local/lib.
#
# Lo chiamano tutti i Contenitore.<bersaglio> di questa cartella, uguale per
# ogni distribuzione (fasi/17-l-installatore.md §6.3: «dentro, statiche,
# versione fissata»).  Perche' da sorgente anche dove la distribuzione le ha:
#   · serve ngtcp2 >= 1.25.0 (i flag NGTCP2_STREAM_CLOSE2_FLAG_* di trasporto.c)
#     con il ponte ngtcp2_crypto_ossl, e quasi nessuna distribuzione li ha;
#   · Arch e Tumbleweed la hanno (1.25), ma una versione fissata e uguale per
#     tutti vuol dire un solo comportamento del trasporto da provare.
#
# Perche' statiche: il binario non si porta dietro librerie fuori dai percorsi
# di sistema, e `ld.so.conf.d` (provisiona.sh) sparisce.  Solo la .a e' installata:
# `-lngtcp2` nel Makefile non puo' prendere una .so che non c'e'.
#
# Il libdir e' fisso a `lib` (non lib64 ne' x86_64-linux-gnu): il Contenitore
# mette /usr/local/lib in LIBRARY_PATH, e il Makefile non va toccato.
set -eu

NGHTTP3_VER=${NGHTTP3_VER:-v1.18.0}
NGTCP2_VER=${NGTCP2_VER:-v1.25.0}
LAVORO=/var/tmp/quic
mkdir -p "$LAVORO"

comune="-GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DENABLE_LIB_ONLY=ON -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON"

git clone --depth 1 -b "$NGHTTP3_VER" --recursive \
    https://github.com/ngtcp2/nghttp3 "$LAVORO/nghttp3"
# shellcheck disable=SC2086
cmake -B "$LAVORO/nghttp3/build" -S "$LAVORO/nghttp3" $comune
ninja -C "$LAVORO/nghttp3/build" install

git clone --depth 1 -b "$NGTCP2_VER" --recursive \
    https://github.com/ngtcp2/ngtcp2 "$LAVORO/ngtcp2"
# shellcheck disable=SC2086
cmake -B "$LAVORO/ngtcp2/build" -S "$LAVORO/ngtcp2" $comune -DENABLE_OPENSSL=ON
ninja -C "$LAVORO/ngtcp2/build" install

rm -rf "$LAVORO"

# La prova che sono davvero solo statiche: una .so qui la prenderebbe il linker.
if ls /usr/local/lib/libngtcp2*.so* /usr/local/lib/libnghttp3*.so* 2>/dev/null; then
	echo "⛔ ci sono .so di ngtcp2/nghttp3 in /usr/local/lib: il binario le userebbe" >&2
	exit 1
fi
ls -l /usr/local/lib/libngtcp2*.a /usr/local/lib/libnghttp3*.a
