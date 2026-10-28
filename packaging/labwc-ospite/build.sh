#!/usr/bin/env bash
# build.sh — builds OUR labwc (hosts the nested KWin >= 6.5), PIANO.md «Correzione B».
#
#     packaging/labwc-ospite/build.sh SRCDIR DESTDIR
#
# SRCDIR: the folder with the two tarballs of VERSIONS (fetch.sh fills it; the sha256 is checked
# AGAIN here).  DESTDIR: the binary lands in DESTDIR/usr/lib/remotix/labwc.
# wlroots 0.19.2 + our patch go into labwc's subprojects/ and are linked STATICALLY: the binary
# depends on no libwlroots, so the distribution's wlroots (0.18/0.19/0.20) does not matter.
# The build flags come from the environment (CFLAGS, LDFLAGS: the distribution's); BUILD_DIR
# (default: a folder next to DESTDIR) holds the work; JOBS limits the compile jobs.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRCDIR=$(cd "${1:?usage: build.sh SRCDIR DESTDIR}" && pwd)
mkdir -p "${2:?usage: build.sh SRCDIR DESTDIR}"
DESTDIR=$(cd "$2" && pwd)
BUILD_DIR=${BUILD_DIR:-$DESTDIR.labwc-build}

ver() { awk -v n="$1" '$1 == n { print $2 }' "$HERE/VERSIONS"; }
LV=$(ver labwc); WV=$(ver wlroots)
PATCH=$HERE/wlroots-$WV-remotix-presented-root.patch
[ -n "$LV" ] && [ -n "$WV" ] && [ -f "$PATCH" ] || { echo "⛔ VERSIONS or the patch for wlroots $WV is missing"; exit 1; }
for n in labwc wlroots; do
	read -r _n _v FILE SHA _u < <(awk -v n="$n" '$1 == n' "$HERE/VERSIONS")
	echo "$SHA  $SRCDIR/$FILE" | sha256sum -c --quiet - || { echo "⛔ $SRCDIR/$FILE: sha256 is not the one in VERSIONS"; exit 1; }
done

rm -rf "$BUILD_DIR"; mkdir -p "$BUILD_DIR"
tar -C "$BUILD_DIR" -xzf "$SRCDIR/labwc-$LV.tar.gz"
S=$BUILD_DIR/labwc-$LV
# no downloads: the upstream wraps go, and a wrap of our own (no URL) maps the dependency
# `wlroots-0.19` that labwc asks for to the folder subprojects/wlroots (OUR wlroots)
rm -f "$S"/subprojects/*.wrap
printf '[wrap-file]\ndirectory = wlroots\n\n[provide]\ndependency_names = wlroots-0.19\n' >"$S/subprojects/wlroots.wrap"
tar -C "$S/subprojects" -xzf "$SRCDIR/wlroots-$WV.tar.gz"
mv "$S/subprojects/wlroots-$WV" "$S/subprojects/wlroots"
rm -f "$S"/subprojects/wlroots/subprojects/*.wrap
patch -d "$S/subprojects/wlroots" -p1 --forward --no-backup-if-mismatch <"$PATCH"
grep -q 'REMOTIX (KWin >= 6.5 nested in labwc)' "$S/subprojects/wlroots/types/scene/surface.c" \
	|| { echo "⛔ the wlroots patch is not in types/scene/surface.c"; exit 1; }
echo "   wlroots $WV patched ($(basename "$PATCH"))"

# labwc: only what a screenless host of KWin needs (no SVG, icons, man pages, Xwayland, NLS).
# wlroots: static, drm + libinput backends (labwc uses both APIs; the headless backend is always
# there), no x11 backend, no Xwayland, gles2 + pixman renderers, gbm allocator, no examples.
# Vulkan renderer, libliftoff, colour management: off (nothing here needs them).
# werror off: wlroots 0.19.2 is built with -Werror, and a newer libinput/compiler than the one it was
# written for (Ubuntu 26.04: LIBINPUT_SWITCH_KEYPAD_SLIDE not handled) would stop the build for a warning.
meson setup "$BUILD_DIR/b" "$S" --buildtype=plain -Db_pie=true --wrap-mode=nodownload \
	--force-fallback-for=wlroots-0.19 \
	-Dxwayland=disabled -Dsvg=disabled -Dicon=disabled -Dnls=disabled -Dman-pages=disabled \
	-Dwlroots:default_library=static -Dwlroots:xwayland=disabled -Dwlroots:examples=false \
	-Dwlroots:backends=drm,libinput -Dwlroots:renderers=gles2 -Dwlroots:allocators=gbm \
	-Dwlroots:session=enabled -Dwlroots:libliftoff=disabled -Dwlroots:color-management=disabled \
	-Dwlroots:xcb-errors=disabled -Dwerror=false -Dwlroots:werror=false
meson compile -C "$BUILD_DIR/b" ${JOBS:+-j "$JOBS"} labwc
"$BUILD_DIR/b/labwc" --version
install -D -m 0755 "$BUILD_DIR/b/labwc" "$DESTDIR/usr/lib/remotix/labwc"
# no libwlroots in the binary: wlroots must be OUR static one, never a system wlroots 0.19
# (--force-fallback-for above); checked here for every package
if ldd "$DESTDIR/usr/lib/remotix/labwc" | grep -q wlroots; then
	echo "⛔ $DESTDIR/usr/lib/remotix/labwc is linked to a libwlroots"; exit 1
fi
echo "   labwc $LV + wlroots $WV (static, patched) -> $DESTDIR/usr/lib/remotix/labwc"
