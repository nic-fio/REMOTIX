#!/bin/sh
# costruisci-labwc.sh — OUR labwc, the hidden compositor that hosts KWin (DECISIONI §10.43).
#
#     sh packaging/labwc/costruisci-labwc.sh SOURCES WORK DEST
#
#   SOURCES  the folder with the two upstream tarballs named in VERSIONI (packaging/labwc/scarica.sh
#            fetches and verifies them; the package recipes copy them next to REMOTIX's sources)
#   WORK     an empty work folder (removed and re-made here)
#   DEST     the file to write: the labwc binary, e.g. debian/remotix/usr/lib/remotix/labwc
#
# Runs where the package is built (debian/rules, remotix.spec, PKGBUILD), with the distribution's
# compiler and libraries: wlroots is linked STATICALLY into labwc, everything else (wayland,
# pixman, xkbcommon, libdrm, gbm/EGL/GLES, libinput, libseat, libudev, libdisplay-info, cairo, pango,
# glib, libxml2, libpng) is the
# distribution's, dynamic — so the package manager states those dependencies by itself.
#
# ⛔ What it does NOT do: download (meson --wrap-mode=nodownload; the sources are only the two
#    tarballs, checked again here against VERSIONI), patch (labwc is built exactly as released:
#    a patch, if ever needed, is published under GPL-2.0 — DECISIONI §10.43), install anything
#    but the one binary.
# ⭐ The build is cut where labwc allows it: no Xwayland, no Vulkan, no colour management, no
#    libliftoff; labwc with no Xwayland, no icons, no SVG, no translations, no man pages.
#    ⚠ The DRM and libinput backends and the session (libseat) stay compiled in: labwc 0.9.8 calls
#    them unconditionally (`[M]` 11 Oct 2026, built without them: undefined wlr_output_is_drm,
#    wlr_libinput_get_device_handle, wlr_session_change_vt…), and we do not patch labwc.  They are
#    never OPENED: REMOTIX starts it with WLR_BACKENDS=headless (`src/kwin.c`), and wlroots opens a
#    session only for the drm/libinput backends.
set -eu

[ $# -eq 3 ] || { sed -n '4,8p' "$0"; exit 2; }
SRC=$1 LAV=$2 DEST=$3
QUI=$(cd "$(dirname "$0")" && pwd)

campo() { # campo <name> <column>: from VERSIONI («name version tarball sha256 url»)
	awk -v n="$1" -v c="$2" '$1 == n { print $c }' "$QUI/VERSIONI"
}
LABWC_TGZ=$(campo labwc 3) WLR_TGZ=$(campo wlroots 3) WLR_VER=$(campo wlroots 2)
for c in labwc wlroots; do
	t=$(campo "$c" 3) s=$(campo "$c" 4)
	echo "$s  $SRC/$t" | sha256sum -c - >/dev/null 2>&1 ||
		{ echo "⛔ $SRC/$t: missing, or its sha256 is not the one in VERSIONI ($s)" >&2; exit 1; }
done

rm -rf "$LAV"; mkdir -p "$LAV"
tar -C "$LAV" -xzf "$SRC/$LABWC_TGZ"
L=$(cd "$LAV"/labwc-* && pwd)
# wlroots as labwc's own subproject: unpacked in the directory its wrap names, so meson uses it as
# it is and never reaches for the network (--wrap-mode=nodownload refuses anyway)
rm -f "$L/subprojects/libsfdo.wrap"
mkdir -p "$L/subprojects/wlroots"
tar -C "$L/subprojects/wlroots" --strip-components=1 -xzf "$SRC/$WLR_TGZ"

# ⭐ --buildtype=plain: the compiler flags are the distribution's packaging flags, which
#    dpkg-buildpackage, rpm (%set_build_flags) and makepkg put in CFLAGS/LDFLAGS (hardening,
#    -g for the debug packages, -ffile-prefix-map for the reproducible .deb); -O2 when alone.
export CFLAGS="${CFLAGS:--O2 -g}"
meson setup "$LAV/b" "$L" \
	--buildtype=plain --wrap-mode=nodownload --force-fallback-for="wlroots-${WLR_VER%.*}" \
	-Dxwayland=disabled -Dicon=disabled -Dsvg=disabled -Dnls=disabled -Dman-pages=disabled \
	-Dwlroots:default_library=static -Dwlroots:examples=false \
	-Dwlroots:backends=drm,libinput -Dwlroots:session=enabled -Dwlroots:xwayland=disabled \
	-Dwlroots:renderers=gles2 -Dwlroots:allocators=gbm \
	-Dwlroots:color-management=disabled -Dwlroots:libliftoff=disabled
meson compile -C "$LAV/b" labwc
mkdir -p "$(dirname "$DEST")"
cp "$LAV/b/labwc" "$DEST"
chmod 0755 "$DEST"
"$DEST" --version
