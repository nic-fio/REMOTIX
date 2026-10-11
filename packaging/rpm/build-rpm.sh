#!/usr/bin/env bash
# build-rpm.sh — the REMOTIX .rpm package, inside the container of each target.
#
#     packaging/rpm/build-rpm.sh                  # fedora44 alma10 tumbleweed leap16
#     packaging/rpm/build-rpm.sh fedora44         # just one
#
# For each target (`phases/17-the-installer.md` §6.1-§6.2, T3):
#   1. the image `localhost/remotix-costruzione-<target>` from src/build-targets/
#      (made by `src/build-targets/build-all.sh`; here it is used if present,
#      built if missing): it already contains static ngtcp2/nghttp3;
#   2. the source archive from the working tree (src/, benches/rcp/,
#      packaging/rpm/) — including changes not yet in the repository;
#   3. in the container: rpm-build and rpmlint from the distribution's package manager,
#      `rpmbuild -ba`, then rpmlint on the packages and on the spec;
#   4. in $OUTPUT/rpm/<target>/: the .rpm files, rpmbuild.log, rpmlint.txt,
#      requires.txt (Requires, automatic and written), file.txt, outcome.txt;
#      and the two small checks of R13/R14 (blacklist of bench files,
#      bench options in the unit).
#
# ⚠ No /tmp: on the laptop it is almost full (like build-all.sh).
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
OUTPUT=${OUTPUT:-$TREE/costruzione-uscita}
CACHE=${CACHE:-$OUTPUT/.lavoro}
ALL=(fedora44 alma10 tumbleweed leap16)
# the version: the release one (RX_VERSION, packaging/release.sh) or the spec default
VER=${RX_VERSION:-$(sed -n 's/^Version:.*!?rx_version:\([^}]*\)}.*/\1/p' "$HERE/remotix.spec")}

command -v podman >/dev/null 2>&1 || { echo "⛔ podman is missing"; exit 2; }
mkdir -p "$CACHE/tmp" "$OUTPUT/rpm"
export TMPDIR="$CACHE/tmp"
if [ $# -eq 0 ] || [ "$1" = all ]; then set -- "${ALL[@]}"; fi

# ⛔ R14 in small: nothing from the bench in the package (§6.4)
DENYLIST='provision|sudoers|gpu-udev|restart-|ld\.so\.conf|/test|benches|\.py$|Containerfile|build(-[a-z]+)?\.sh'
# ⛔ R13 in small: the unit passes no bench options (§4.5)
BENCH_OPTIONS='--survey|--command-socket|--audio-test|--verbose'

build_one()
{
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$OUTPUT/rpm/$1" workdir="$CACHE/rpm-$1"
	local note=""
	rm -rf "$u" "$workdir"; mkdir -p "$u" "$workdir"/{SOURCES,SPECS}

	if ! podman image exists "$imm"; then
		echo "== $b: the image is missing, building it"
		podman build -t "$imm" -f "$TREE/src/build-targets/Containerfile.$b" "$TREE/src/build-targets" \
			>"$u/image.log" 2>&1 || { echo "$b package=NO image=NO" | tee "$u/outcome.txt"; return 1; }
	fi

	echo "== $b: sources"
	# ⛔ firewalld discards a service that is not well-formed XML, silently for
	#    whoever installs (`[M]` 29 Sep: `--` inside a comment).
	python3 -c 'import sys, xml.dom.minidom; xml.dom.minidom.parse(sys.argv[1])' "$HERE/remotix-firewalld.xml" \
		|| { echo "$b package=NO remotix-firewalld.xml is not valid XML" | tee "$u/outcome.txt"; return 1; }
	tar -C "$TREE" --transform "s,^,remotix-$VER/," \
		--exclude='*.o' --exclude='src/remotix' --exclude='*-client-protocol.h' --exclude='*-protocol.c' \
		-czf "$workdir/SOURCES/remotix-$VER.tar.gz" src benches/rcp packaging/rpm THIRD-PARTY-LICENSES LICENSE.md
	# ⭐ DECISIONI §10.43: RHEL / Alma 10 only — the upstream source of OUR labwc (Source1),
	#    fetched once and verified at every build (sha256 + Fedora's sha512)
	if [ "$b" = alma10 ]; then
		LABWC_SOURCES=${LABWC_SOURCES:-$TREE/costruzione-uscita/labwc-sources}
		"$HERE/labwc/fetch.sh" "$LABWC_SOURCES" ||
			{ echo "$b package=NO the labwc source" | tee "$u/outcome.txt"; return 1; }
		install -m 0644 "$LABWC_SOURCES"/labwc-*.tar.gz "$workdir/SOURCES/"
	fi
	cp "$HERE/remotix.spec" "$workdir/SPECS/"

	echo "== $b: rpmbuild (log in $u/rpmbuild.log)"
	podman run --rm -v "$workdir:/work" "$imm" sh -c '
		if command -v dnf >/dev/null; then
			dnf -y -q install --setopt=install_weak_deps=False rpm-build rpmlint systemd-rpm-macros cpio selinux-policy-devel bzip2 >/dev/null 2>&1
		else
			zypper -n -q refresh -f >/dev/null 2>&1  # Tumbleweed rolls: stale metadata in the image
			zypper -n -q install --no-recommends --force-resolution rpm-build rpmlint systemd-rpm-macros cpio selinux-policy-devel bzip2 >/dev/null 2>&1
		fi
		rpm -q rpm-build rpmlint | sed "s/^/tools: /"
		rpm --eval "dist=%{?dist} fedora=%{?fedora} rhel=%{?rhel} suse_version=%{?suse_version} pamvendor=%{?_pam_vendordir}"
		rpmbuild -ba --define "_topdir /work" --define "rx_version '"$VER"'" --define "rx_release '"${RX_REVISION:-1}"'" '"${RX_SELINUX_PERMISSIVE:+--define \"rx_selinux_permissive 1\"}"' /work/SPECS/remotix.spec 2>&1
		echo "rpmbuild-outcome=$?"
		ls /work/RPMS/*/*.rpm >/dev/null 2>&1 || exit 1
		rpmlint /work/SPECS/remotix.spec /work/RPMS/*/*.rpm /work/SRPMS/*.rpm >/work/rpmlint.txt 2>&1
		p=$(ls /work/RPMS/x86_64/remotix-[0-9]*.rpm)
		{ echo "## Requires (automatic + written)"; rpm -qpR "$p"
		  echo "## Recommends"; rpm -qp --recommends "$p"
		  echo "## Provides"; rpm -qp --provides "$p"; } >/work/requires.txt
		rpm -qplv "$p" >/work/file.txt
		rpm -qp --scripts "$p" >/work/scriptlet.txt
		rm -rf /work/estratto; mkdir /work/estratto; cd /work/estratto
		rpm2cpio "$p" | cpio -idm --quiet
		ldd usr/libexec/remotix/remotix >/work/ldd.txt 2>&1
		# ⭐ §10.43 (Alma): our labwc — the version, and no library missing
		[ -e usr/lib/remotix/labwc ] && { usr/lib/remotix/labwc --version; ldd usr/lib/remotix/labwc; } >/work/ldd-labwc.txt 2>&1
		# R13: the bench-function sentence NOT in the package binary, and YES
		# in an rcp.o with BENCH_ON 1 (the positive check: without it, «not
		# found» could mean «I cannot search») — like the .deb line.
		frase="the BENCH FUNCTION is ON"
		n=$(strings usr/libexec/remotix/remotix | grep -c "$frase")
		rm -rf /work/positive; mkdir /work/positive; cd /work/positive
		tar xzf /work/SOURCES/remotix-*.tar.gz --strip-components=1
		cd src; sed -i "s/^#define BENCH_ON 0\$/#define BENCH_ON 1/" rcp.c
		make TWIN=none rcp.o >/dev/null 2>&1
		p=$(strings rcp.o 2>/dev/null | grep -c "$frase")
		echo "package=$n positive=$p" >/work/r13-binario.txt
	' >"$u/rpmbuild.log" 2>&1

	cp "$workdir"/RPMS/*/*.rpm "$workdir"/SRPMS/*.rpm "$u/" 2>/dev/null
	for f in rpmlint.txt requires.txt file.txt scriptlet.txt ldd.txt ldd-labwc.txt r13-binario.txt; do
		[ -f "$workdir/$f" ] && cp "$workdir/$f" "$u/"
	done
	if ! ls "$u"/remotix-[0-9]*.x86_64.rpm >/dev/null 2>&1; then
		echo "$b package=NO (see rpmbuild.log)" | tee "$u/outcome.txt"
		return 1
	fi

	grep -q 'not found' "$u/ldd.txt" && note="$note ldd:not-found"
	grep -qE 'ngtcp2|nghttp3' "$u/ldd.txt" && note="$note ldd:quic-dinamiche"
	if [ "$b" = alma10 ]; then
		if grep -q '^labwc ' "$u/ldd-labwc.txt" 2>/dev/null && ! grep -q 'not found' "$u/ldd-labwc.txt"; then
			note="$note labwc:verde($(head -1 "$u/ldd-labwc.txt" | cut -d' ' -f2))"
		else
			note="$note labwc:ROSSO"
		fi
	fi
	awk '{ print $NF }' "$u/file.txt" | grep -E "$DENYLIST" >"$u/r14.txt" && note="$note R14:RED"
	grep '^ExecStart' "$workdir/estratto/usr/lib/systemd/system/remotix.service" | grep -E -- "$BENCH_OPTIONS" >"$u/r13.txt" \
		&& note="$note R13-unita:RED"
	grep -qx 'package=0 positive=[1-9][0-9]*' "$u/r13-binario.txt" 2>/dev/null \
		&& note="$note R13:green($(cat "$u/r13-binario.txt"))" \
		|| note="$note R13:RED($(cat "$u/r13-binario.txt" 2>/dev/null))"
	[ -s "$u/r14.txt" ] || note="$note R14:green"
	local lint
	lint=$(tail -1 "$u/rpmlint.txt")
	echo "$b package=yes $(ls "$u"/remotix-[0-9]*.x86_64.rpm | xargs -n1 basename) · rpmlint: $lint ·$note" | tee "$u/outcome.txt"
}

state=0
for b in "$@"; do build_one "$b" || state=1; done
printf '\n== summary (%s/rpm)\n' "$OUTPUT"
for b in "$@"; do cat "$OUTPUT/rpm/$b/outcome.txt" 2>/dev/null || echo "$b (no outcome)"; done
exit $state
