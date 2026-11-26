#!/usr/bin/env bash
# build-deb-vm.sh — builds REMOTIX's .deb for Ubuntu 26.04 (resolute) on the `costruzione` VM (no containers).
#
#     build/build-deb-vm.sh [label]
#     TWICE=1 build/build-deb-vm.sh label        # builds a second time and checks the .deb is byte-identical
#
# Run it from any machine that has the tree and ssh access to the server `nicfio@192.168.0.2` (the tablet does NOT compile: all the
# work happens in the VM).  If the VM is off the script turns it on (virtual only, never the Radeon) and turns it off again at the end;
# set KEEP_VM=1 to leave it on.  The older build/build-deb.sh (podman) stays as it is.
#
# What it does:
#   1. makes a COPY of the tree (src/, debian/, build/labwc-ospite/ as labwc-ospite/, LICENSE.md, THIRD-PARTY-LICENSES), writes
#      debian/changelog and appends LICENSE.md to debian/copyright (as build-deb.sh does);
#   2. fetches (curl, here, a few MB) and VERIFIES against build/labwc-ospite/VERSIONS the two upstream tarballs of OUR labwc
#      (labwc 0.9.3, wlroots 0.19.2) with labwc-ospite/fetch.sh: they travel with the copy, so that the VM needs no network for them
#      (debian/rules reads them from LABWC_SOURCES, here <work folder>/labwc-sources);
#   3. copies everything to the VM, in ~/debwork/<label>; installs the build dependencies there (apt: the list of build/Containerfile,
#      the build tools of labwc/wlroots and the packaging tools);
#   4. builds static ngtcp2 1.25.0 / nghttp3 1.18.0 into /usr/local with build/quic-static.sh, once (skipped if already there);
#   5. runs `dpkg-buildpackage -b -us -uc` (it builds our labwc too), then lintian and the checks of build-deb.sh on the FINISHED package
#      (R13 bench function not in the binary + positive control, R13 no bench option in the unit, R14 no bench file in the package,
#      R4 ldd of the binary and R4 ldd-labwc of /usr/libexec/remotix/labwc; R23 with TWICE=1): any NO, or a missing line, fails the script;
#   6. builds here the corresponding source of OUR labwc, remotix-<version>-labwc-source.tar.gz (GPL-2.0: to be published with the
#      package, LICENSE.md section 8), deterministic, checked (7 files, sha256 of the tarballs) = «labwc-source»; with TWICE=1 it is
#      built again and compared = «R23 labwc-source-riproducibile»;
#   7. brings the .deb, the .buildinfo, the .sha256, the labwc source archive and the logs to $OUTDIR on the server.
# <label>: only [A-Za-z0-9._-], not «.» nor «..»; if the folder on the server exists already the script stops (a previous package is
# never overwritten).  On a failure the logs go to <OUTDIR>-fallita-<time>/ on the server, and the VM's work folder stays for inspection.
#
# Environment (all optional):
#   OUTPUT        results folder on the server           (default /media/REMOTIX-UBUNTU/pacchetti/<label>)
#   RX_VERSION    upstream version                       (default 1.2.0~dev; a release passes RX_VERSION=1.2.0)  RX_REVISION  Debian revision (default 1)
#   SOURCE_DATE_EPOCH  build date, for a reproducible .deb (default: the newest mtime in src/, debian/, build/labwc-ospite/)
#   TWICE=1       second build + byte comparison         KEEP_VM=1  do not turn the VM off at the end
#   RX_LABWC_SOURCES  a folder here where the two labwc tarballs are kept between runs (default: a temporary one, fetched each time)
#   RX_SERVER     (default nicfio@192.168.0.2)           RX_GUEST_PORT  the guest's ssh port on the server (default 2345)
#   RX_VMSCRIPT   the VM manager on the server           (default /media/REMOTIX-UBUNTU/vm-radeon/vm-radeon.sh)
# The complete output of the build is in $OUTDIR/costruzione.log (and apt/quic logs); this script's own lines go to the screen.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/.." && pwd)
LABEL=${1:-$(date +%Y%m%d-%H%M)}
case "$LABEL" in
""|.|..|*[!A-Za-z0-9._-]*) echo "label \"$LABEL\": only letters, digits, dot, underscore and dash, and not . or .." >&2; exit 2 ;;
esac
SERVER=${RX_SERVER:-nicfio@192.168.0.2}
GUESTPORT=${RX_GUEST_PORT:-2345}
VMSCRIPT=${RX_VMSCRIPT:-/media/REMOTIX-UBUNTU/vm-radeon/vm-radeon.sh}
OUTDIR=${OUTPUT:-/media/REMOTIX-UBUNTU/pacchetti/$LABEL}
VERSION_UP=${RX_VERSION:-1.2.0~dev}
REVISION=${RX_REVISION:-1}
VERSION="$VERSION_UP-$REVISION+ubuntu26.04"
SSHOPT=(-o BatchMode=yes -o StrictHostKeyChecking=no)
GKEY=/media/REMOTIX-UBUNTU/vm-radeon/costruzione/vmkey
GSSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=no -i $GKEY -p $GUESTPORT prova@127.0.0.1"
# guest <command>: a command in the VM (through the server); the whole command line is quoted once
guest() { ssh "${SSHOPT[@]}" "$SERVER" "export TERM=dumb; $GSSH $(printf '%q' "$*")"; }
WORK="~/debwork/$LABEL"
STARTED=0

vm_off() {
	[ "$STARTED" = 1 ] && [ "${KEEP_VM:-0}" != 1 ] || return 0
	echo "== turning the VM off"
	ssh "${SSHOPT[@]}" "$SERVER" "TERM=dumb $VMSCRIPT spegni costruzione" >/dev/null 2>&1 || echo "   (the VM did not turn off: run $VMSCRIPT spegni costruzione)" >&2
}

# the parent folder only (never the label's: its existence is the check below)
ssh "${SSHOPT[@]}" "$SERVER" "mkdir -p '$(dirname "$OUTDIR")'" || exit 2
if ssh "${SSHOPT[@]}" "$SERVER" "test -e '$OUTDIR'"; then
	echo "$OUTDIR exists already on the server: choose another label (a previous package is never overwritten)" >&2
	exit 2
fi

stage=$(mktemp -d "${TMPDIR:-/tmp}/rx-deb.XXXXXX") || exit 2
trap 'rm -rf "$stage"; vm_off' EXIT

# the build date: fixed by the caller, or derived from the files (same source, same package)
if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
	SOURCE_DATE_EPOCH=$(find "$TREE/src" "$TREE/debian" "$TREE/build/labwc-ospite" "$TREE/LICENSE.md" "$TREE/THIRD-PARTY-LICENSES" -type f -printf '%T@\n' | sort -n | tail -1 | cut -d. -f1)
fi
export SOURCE_DATE_EPOCH
DATE_RFC=$(date -R -u -d "@$SOURCE_DATE_EPOCH")

# OUR labwc: the two upstream tarballs, fetched and checked against VERSIONS (fetch.sh checks even when the files are already there)
LSOURCES=${RX_LABWC_SOURCES:-$stage/labwc-sources}
echo "== labwc and wlroots sources (checked against build/labwc-ospite/VERSIONS)"
"$HERE/labwc-ospite/fetch.sh" "$LSOURCES" || { echo "the labwc/wlroots tarballs are missing or their sha256 differs from VERSIONS" >&2; exit 2; }

# the copy of the tree (as build-deb.sh's prepare_copy)
pack=$stage/pack
mkdir -p "$pack/remotix"
cp -a "$TREE/src" "$pack/remotix/src"
cp -a "$TREE/debian" "$pack/remotix/debian"
# OUR labwc: the recipe and the patch (debian/rules runs labwc-ospite/build.sh)
cp -a "$HERE/labwc-ospite" "$pack/remotix/labwc-ospite"
cp "$TREE/THIRD-PARTY-LICENSES" "$pack/remotix/"
# the licence text goes into debian/copyright, as «License: LicenseRef-REMOTIX» continuation lines (« .» = empty line)
sed -e 's/^$/./' -e 's/^/ /' "$TREE/LICENSE.md" >>"$pack/remotix/debian/copyright"
# leftovers of a local build must not enter the package
rm -f "$pack/remotix/src/remotix" "$pack/remotix/src"/*.o "$pack/remotix/src"/*-protocol.c "$pack/remotix/src"/*-client-protocol.h
cat >"$pack/remotix/debian/changelog" <<EOF
remotix ($VERSION) resolute; urgency=medium

  * Ubuntu 26.04 build.

 -- nicfio <remotix@nicfio.it>  $DATE_RFC
EOF
cp "$HERE/quic-static.sh" "$pack/"
mkdir -p "$pack/labwc-sources"
cp -p "$LSOURCES"/labwc-*.tar.gz "$LSOURCES"/wlroots-*.tar.gz "$pack/labwc-sources/"

# the script that runs INSIDE the VM (quoted heredoc: nothing is expanded here)
cat >"$pack/guest-build.sh" <<'GUEST'
#!/bin/bash
# runs in the build VM, in the work folder; arguments: none; environment: SOURCE_DATE_EPOCH, TWICE
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")" || exit 1
W=$PWD
SUDO() { echo prova2026 | sudo -S -p "" "$@"; }
export DEBIAN_FRONTEND=noninteractive
export LIBRARY_PATH=/usr/local/lib PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
# OUR labwc: the two tarballs brought with the copy (debian/rules: LABWC_SOURCES ?= ..., so the environment wins)
export LABWC_SOURCES=$W/labwc-sources

echo "== dependencies"
DEPS="build-essential pkg-config git ca-certificates cmake ninja-build libssl-dev libpam0g-dev libglib2.0-dev libpipewire-0.3-dev libdrm-dev libva-dev libopus-dev zlib1g-dev libei-dev libxkbcommon-dev libgbm-dev libwayland-dev libvulkan-dev curl meson patch hwdata wayland-protocols libegl-dev libgles-dev libinput-dev libpixman-1-dev libseat-dev libudev-dev libdisplay-info-dev libxml2-dev libcairo2-dev libpango1.0-dev libpng-dev debhelper dh-apparmor dpkg-dev fakeroot lintian binutils"
if ! SUDO apt-get -y install --no-install-recommends $DEPS >apt.log 2>&1; then
	SUDO apt-get update >>apt.log 2>&1
	SUDO apt-get -y install --no-install-recommends $DEPS >>apt.log 2>&1 || { echo "apt failed"; tail -20 apt.log; exit 1; }
fi

echo "== static ngtcp2/nghttp3"
if ! { test "$(pkg-config --modversion libngtcp2 2>/dev/null)" = 1.25.0 && test "$(pkg-config --modversion libnghttp3 2>/dev/null)" = 1.18.0 && test -f /usr/local/lib/libngtcp2_crypto_ossl.a; }; then
	SUDO sh "$W/quic-static.sh" >quic.log 2>&1 || { echo "quic-static failed"; tail -30 quic.log; exit 1; }
fi

echo "== labwc/wlroots sources (sha256 against VERSIONS)"
bash "$W/remotix/labwc-ospite/fetch.sh" "$LABWC_SOURCES" || { echo "labwc/wlroots tarballs: sha256 differs from VERSIONS"; exit 1; }

build_in() {  # build_in <copy> <log>
	( cd "$1/remotix" && dpkg-buildpackage -b -us -uc ) >"$2" 2>&1
}

mkdir -p a
cp -a remotix a/remotix
echo "== package"
build_in "$W/a" "$W/costruzione.log" || { echo "dpkg-buildpackage failed"; tail -20 "$W/costruzione.log"; exit 1; }
deb=$(cd a && ls remotix_*.deb | head -1)
[ -n "$deb" ] || { echo "no .deb produced"; exit 1; }
cp "a/$deb" a/remotix_*.buildinfo "$W/"
echo "   $deb"
dpkg-deb -c "$deb" >elenco.txt
sha256sum "$deb" >"$deb.sha256"

echo "== lintian and checks"
lintian -I --pedantic --no-tag-display-limit "$deb" >lintian.txt 2>&1
# R13 positive control: rcp.o built with BENCH_ON 1, same flags as the Makefile
cd "$W" || exit 1
rm -rf positivo; cp -a a/remotix/src positivo
sed -i 's/^#define BENCH_ON 0$/#define BENCH_ON 1/' positivo/rcp.c
( cd positivo && make TWIN=none BENCH=1 rcp.o >/dev/null 2>&1 ) >/dev/null 2>&1
{
	set -u
	d=$(mktemp -d); dpkg-deb -x "$deb" "$d"
	bin=$d/usr/libexec/remotix/remotix
	frase="the BENCH FUNCTION is ON"
	n=$(strings "$bin" | grep -c "$frase")
	p=$(strings positivo/rcp.o 2>/dev/null | grep -c "$frase")
	[ "$n" = 0 ] && [ "$p" -ge 1 ] && r=SI || r=NO
	echo "R13 banco-nel-binario $r (package: $n, positive control rcp.o with BENCH_ON 1: $p)"
	o=$(grep "^ExecStart" "$d/usr/lib/systemd/system/remotix.service" | \
	     grep -oE -- "--(survey|command-socket|audio-test|verbose)" | sort -u | tr "\n" " ")
	[ -z "$o" ] && echo "R13 opzioni-di-banco-nell-unita SI (none)" \
	            || echo "R13 opzioni-di-banco-nell-unita NO ($o)"
	nere=$(dpkg-deb -c "$deb" | awk '{print $NF}' | \
	       grep -E "/test|sudoers|gpu-udev|restart-|ld\.so\.conf|provision|benches|/opt/|\.pem$|\.key$" || true)
	[ -z "$nere" ] && echo "R14 file-del-banco SI (none)" \
	               || echo "R14 file-del-banco NO: $nere"
	l=$(ldd "$bin")
	if printf "%s\n" "$l" | grep -q "not found"; then echo "R4 ldd NO (not found)";
	elif printf "%s\n" "$l" | grep -qE "ngtcp2|nghttp3"; then echo "R4 ldd NO (dynamic ngtcp2/nghttp3)";
	else echo "R4 ldd SI ($(printf "%s\n" "$l" | wc -l) libraries, none missing)"; fi
	lw=$d/usr/libexec/remotix/labwc
	if [ ! -x "$lw" ]; then echo "R4 ldd-labwc NO (usr/libexec/remotix/labwc is not in the package)";
	else ll=$(ldd "$lw")
		if printf "%s\n" "$ll" | grep -q "not found"; then echo "R4 ldd-labwc NO (not found)";
		elif printf "%s\n" "$ll" | grep -q wlroots; then echo "R4 ldd-labwc NO (a libwlroots is linked)";
		else echo "R4 ldd-labwc SI (no libwlroots, none missing; $("$lw" --version | head -1))"; fi
	fi
	echo "Depends:    $(dpkg-deb -f "$deb" Depends)"
	echo "Recommends: $(dpkg-deb -f "$deb" Recommends)"
	echo "Static:     $(dpkg-deb -f "$deb" Static-Built-Using)"
	echo "Conffiles:"; dpkg-deb --ctrl-tarfile "$deb" | tar -xO ./conffiles | sed "s/^/  /"
	rm -rf "$d"
} >controlli.txt 2>&1

if [ "${TWICE:-0}" = 1 ]; then
	echo "== second build (R23)"
	mkdir -p b; cp -a remotix b/remotix
	if build_in "$W/b" "$W/costruzione-2.log"; then
		if cmp -s "a/$deb" "b/$deb"; then
			echo "R23 riproducibile SI ($(cut -c1-16 <"$deb.sha256")... identical in two clean copies)" >>controlli.txt
		else
			echo "R23 riproducibile NO (the two .deb files differ)" >>controlli.txt
			cp "b/$deb" "seconda-$deb"
		fi
	else
		echo "R23 riproducibile NO (second build failed)" >>controlli.txt
	fi
fi
printf 'lintian: E=%s W=%s\n' "$(grep -c '^E: ' lintian.txt)" "$(grep -c '^W: ' lintian.txt)" >>controlli.txt
cd "$W" || exit 1
rm -rf a b positivo remotix
echo "== done"
GUEST
chmod +x "$pack/guest-build.sh"

echo "== VM"
if ! guest hostname >/dev/null 2>&1; then
	echo "   turning it on (virtual)"
	ssh "${SSHOPT[@]}" "$SERVER" "TERM=dumb $VMSCRIPT accendi costruzione virtuale" || { echo "the VM did not start" >&2; exit 2; }
	STARTED=1
fi
hn=$(guest hostname) || { echo "the build VM does not answer" >&2; exit 2; }
case "$hn" in rx-ub-costruzione) echo "   $hn" ;; *) echo "unexpected guest name: $hn" >&2; exit 2 ;; esac
# a work folder left in the VM by a failed run is kept for inspection: never removed here
if guest "test -e $WORK"; then
	echo "the work folder $WORK exists already in the VM (left by an earlier run, kept for inspection): choose another label" >&2
	exit 2
fi
guest "mkdir -p $WORK" || exit 1
tar -C "$pack" -cf - . | ssh "${SSHOPT[@]}" "$SERVER" "$GSSH 'tar -C $WORK -xf -'" || { echo "copy failed" >&2; exit 1; }

echo "== build in the VM (log: $WORK/*.log in the guest; brought back at the end)"
guest "cd $WORK && SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH TWICE=${TWICE:-0} ./guest-build.sh" 2>&1 | tee "$stage/guest.out" | sed 's/^/   /'
rc=${PIPESTATUS[0]}
ctl=$(guest "cat $WORK/controlli.txt 2>/dev/null") || ctl=

# the corresponding source of OUR labwc, to be published with the package (LICENSE.md section 8): built here, from the files of the tree
# and the two verified tarballs; deterministic (fixed order, owner, mtime, no write bit for group/others, no name/date in the gzip header)
lsrc=remotix-$VERSION_UP-labwc-source.tar.gz
lname=remotix-$VERSION_UP-labwc-source
lok=SI; lwhy=
lsrc_build() {  # lsrc_build <work folder> <output file>
	rm -rf "$1"; mkdir -p "$1/$lname"
	cp -a "$HERE/labwc-ospite/." "$1/$lname/" || return 1
	cp -p "$LSOURCES"/labwc-*.tar.gz "$LSOURCES"/wlroots-*.tar.gz "$1/$lname/" || return 1
	tar -C "$1" --sort=name --owner=0 --group=0 --numeric-owner --mode=go-w --mtime="@$SOURCE_DATE_EPOCH" \
		-cf - "$lname" | gzip -n >"$2" && [ "${PIPESTATUS[0]}" = 0 ]
}
lsrc_build "$stage/lsrc1" "$stage/$lsrc" || { lok=NO; lwhy="tar of the sources failed"; }
if [ "$lok" = SI ]; then
	n=$(tar tzf "$stage/$lsrc" | grep -cE '/(labwc-[0-9.]+\.tar\.gz|wlroots-[0-9.]+\.tar\.gz|wlroots-[0-9.]+-remotix-presented-root\.patch|VERSIONS|fetch\.sh|build\.sh|README)$')
	[ "$n" = 7 ] || { lok=NO; lwhy="the archive has $n of the 7 expected files"; }
fi
if [ "$lok" = SI ]; then
	(cd "$stage" && sha256sum "$lsrc" >"$lsrc.sha256")
	lines="labwc-source SI ($lsrc, $(cut -c1-16 <"$stage/$lsrc.sha256")..., 7 files, tarballs verified against VERSIONS)"
	if [ "${TWICE:-0}" = 1 ]; then
		if lsrc_build "$stage/lsrc2" "$stage/lsrc2.tar.gz" && cmp -s "$stage/lsrc2.tar.gz" "$stage/$lsrc"; then
			lines="$lines
R23 labwc-source-riproducibile SI (same .sha256 twice)"
		else
			lines="$lines
R23 labwc-source-riproducibile NO (the two source archives differ)"
		fi
	fi
else
	rm -f "$stage/$lsrc" "$stage/$lsrc.sha256"
	lines="labwc-source NO ($lwhy)"
fi
ctl="$ctl
$lines"

fail=0
[ "$rc" = 0 ] || fail=1
# the lines R13 (twice), R14, R4 (binary and labwc) and labwc-source must be there and say SI: a failure of dpkg-deb or ldd leaves
# a line missing, which fails here
for k in 'R13 banco-nel-binario SI' 'R13 opzioni-di-banco-nell-unita SI' 'R14 file-del-banco SI' 'R4 ldd SI' 'R4 ldd-labwc SI' 'labwc-source SI'; do
	printf '%s\n' "$ctl" | grep -q "^$k" || { echo "line missing or NO: $k" >&2; fail=1; }
done
printf '%s\n' "$ctl" | grep -qE '^(R[0-9]+|labwc-source) ([^ ]+ )*NO( |$)' &&{ echo "a check says NO" >&2; fail=1; }
# a lintian ERROR fails the build as well (warnings are only shown)
printf '%s\n' "$ctl" | grep -q '^lintian: E=0 ' || { echo "lintian reports errors (or its line is missing)" >&2; fail=1; }
printf '%s\n' "$ctl" | grep -E '^(R[0-9]+ |labwc-source|lintian:)' | sed 's/^/   /'

if [ "$fail" != 0 ]; then
	FAILDIR="$OUTDIR-fallita-$(date +%H%M%S)"
	echo "FAILED: logs go to $FAILDIR on the server; no package is brought back (it stays in the guest, $WORK)" >&2
	ssh "${SSHOPT[@]}" "$SERVER" "mkdir '$FAILDIR' && $GSSH 'cd $WORK && tar -cf - *.log *.txt 2>/dev/null' | tar -xf - -C '$FAILDIR'" || true
	printf '%s\n' "$(cat "$stage/guest.out")" | ssh "${SSHOPT[@]}" "$SERVER" "cat > '$FAILDIR/costruzione-vm.log'" || true
	exit 1
fi

echo "== back to the server: $OUTDIR"
ssh "${SSHOPT[@]}" "$SERVER" "mkdir '$OUTDIR' && $GSSH 'cd $WORK && tar -cf - *.deb *.sha256 *.buildinfo *.log *.txt' | tar -xf - -C '$OUTDIR' && cd '$OUTDIR' && ls -l" \
	|| { echo "bringing the package back failed" >&2; exit 1; }
# the labwc source archive and the checks done here (appended to controlli.txt, as build-deb.sh does)
cat "$stage/$lsrc" | ssh "${SSHOPT[@]}" "$SERVER" "cat > '$OUTDIR/$lsrc'" || { echo "bringing the labwc source archive failed" >&2; exit 1; }
cat "$stage/$lsrc.sha256" | ssh "${SSHOPT[@]}" "$SERVER" "cat > '$OUTDIR/$lsrc.sha256'" || { echo "bringing the labwc source sha256 failed" >&2; exit 1; }
printf '%s\n' "$lines" | ssh "${SSHOPT[@]}" "$SERVER" "cat >> '$OUTDIR/controlli.txt'" || true
cat "$stage/guest.out" | ssh "${SSHOPT[@]}" "$SERVER" "cat > '$OUTDIR/costruzione-vm.log'" || true
exit 0
