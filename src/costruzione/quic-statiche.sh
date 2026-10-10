#!/bin/sh
# quic-statiche.sh — nghttp3 and ngtcp2 from source, ONLY static, in /usr/local/lib.
#
# Called by all the Contenitore.<target> files of this folder, the same for
# every distribution (fasi/17-l-installatore.md §6.3: "inside, static,
# pinned version").  Why from source even where the distribution has them:
#   · ngtcp2 >= 1.25.0 is needed (the NGTCP2_STREAM_CLOSE2_FLAG_* flags of trasporto.c)
#     with the ngtcp2_crypto_ossl bridge, and almost no distribution has them;
#   · Arch and Tumbleweed have it (1.25), but a version pinned and the same for
#     everyone means a single transport behaviour to test.
#
# Why static: the binary carries no libraries outside the system
# paths, and `ld.so.conf.d` (provisiona.sh) goes away.  Only the .a is installed:
# `-lngtcp2` in the Makefile cannot pick up a .so that is not there.
#
# The libdir is fixed to `lib` (not lib64 nor x86_64-linux-gnu): the Contenitore
# puts /usr/local/lib in LIBRARY_PATH, and the Makefile need not be touched.
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

# The proof that they really are static only: a .so here would be picked up by the linker.
if ls /usr/local/lib/libngtcp2*.so* /usr/local/lib/libnghttp3*.so* 2>/dev/null; then
	echo "⛔ there are ngtcp2/nghttp3 .so files in /usr/local/lib: the binary would use them" >&2
	exit 1
fi
ls -l /usr/local/lib/libngtcp2*.a /usr/local/lib/libnghttp3*.a
