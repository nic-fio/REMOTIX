#!/bin/sh
# quic-static.sh — nghttp3 and ngtcp2 from source, ONLY static, in /usr/local/lib (Fedora 45 build VM).
# Same recipe and versions as ../../ubuntu26.04/build/quic-static.sh (ngtcp2 1.25.0 with the ngtcp2_crypto_ossl bridge,
# nghttp3 1.18.0); Fedora's own ngtcp2 is 1.22.1, too old.  Only the .a files are installed: `-lngtcp2` in the Makefile cannot pick up
# a .so that is not there.  libdir fixed to `lib` (build-rpm.sh puts /usr/local/lib in LIBRARY_PATH and PKG_CONFIG_PATH).
# Run as root in the VM; needs network (git clone from GitHub), cmake, ninja-build, git, gcc, openssl-devel (the system's, 4.0).
set -eu

NGHTTP3_VER=${NGHTTP3_VER:-v1.18.0}
NGTCP2_VER=${NGTCP2_VER:-v1.25.0}
# fixed, not taken from the environment: it is followed by an rm -rf, as root
WORKDIR=/var/tmp/quic
rm -rf "$WORKDIR"; mkdir -p "$WORKDIR"

common="-GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DENABLE_LIB_ONLY=ON -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON"

git clone --depth 1 -b "$NGHTTP3_VER" --recursive https://github.com/ngtcp2/nghttp3 "$WORKDIR/nghttp3"
# shellcheck disable=SC2086
cmake -B "$WORKDIR/nghttp3/build" -S "$WORKDIR/nghttp3" $common
ninja -C "$WORKDIR/nghttp3/build" install

git clone --depth 1 -b "$NGTCP2_VER" --recursive https://github.com/ngtcp2/ngtcp2 "$WORKDIR/ngtcp2"
# shellcheck disable=SC2086
cmake -B "$WORKDIR/ngtcp2/build" -S "$WORKDIR/ngtcp2" $common -DENABLE_OPENSSL=ON
ninja -C "$WORKDIR/ngtcp2/build" install

rm -rf "$WORKDIR"

# The proof that they really are static only: a .so here would be picked up by the linker.
if ls /usr/local/lib/libngtcp2*.so* /usr/local/lib/libnghttp3*.so* 2>/dev/null; then
	echo "there are ngtcp2/nghttp3 .so files in /usr/local/lib: the binary would use them" >&2
	exit 1
fi
ls -l /usr/local/lib/libngtcp2*.a /usr/local/lib/libnghttp3*.a
