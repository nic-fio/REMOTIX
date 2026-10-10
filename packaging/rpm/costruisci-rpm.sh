#!/usr/bin/env bash
# costruisci-rpm.sh — the REMOTIX .rpm package, inside the container of each target.
#
#     packaging/rpm/costruisci-rpm.sh                  # fedora44 alma10 tumbleweed leap16
#     packaging/rpm/costruisci-rpm.sh fedora44         # just one
#
# For each target (`fasi/17-l-installatore.md` §6.1-§6.2, T3):
#   1. the image `localhost/remotix-costruzione-<target>` from src/costruzione/
#      (made by `src/costruzione/costruisci-tutti.sh`; here it is used if present,
#      built if missing): it already contains static ngtcp2/nghttp3;
#   2. the source archive from the working tree (src/, banchi/rcp/,
#      packaging/rpm/) — including changes not yet in the repository;
#   3. in the container: rpm-build and rpmlint from the distribution's package manager,
#      `rpmbuild -ba`, then rpmlint on the packages and on the spec;
#   4. in $OUTPUT/rpm/<target>/: the .rpm files, rpmbuild.log, rpmlint.txt,
#      richieste.txt (Requires, automatic and written), file.txt, esito.txt;
#      and the two small checks of R13/R14 (blacklist of bench files,
#      bench options in the unit).
#
# ⚠ No /tmp: on the laptop it is almost full (like costruisci-tutti.sh).
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
OUTPUT=${OUTPUT:-$TREE/costruzione-uscita}
CACHE=${CACHE:-$OUTPUT/.work}
ALL=(fedora44 alma10 tumbleweed leap16)
# the version: the release one (RX_VERSION, packaging/rilascio.sh) or the spec default
VER=${RX_VERSION:-$(sed -n 's/^Version:.*!?rx_version:\([^}]*\)}.*/\1/p' "$HERE/remotix.spec")}

command -v podman >/dev/null 2>&1 || { echo "⛔ podman is missing"; exit 2; }
mkdir -p "$CACHE/tmp" "$OUTPUT/rpm"
export TMPDIR="$CACHE/tmp"
if [ $# -eq 0 ] || [ "$1" = all_v ]; then set -- "${ALL[@]}"; fi

# ⛔ R14 in small: nothing from the bench in the package (§6.4)
DENYLIST='provisiona|sudoers|gpu-udev|relaunch-|ld\.so\.conf|/prova|benches|\.py$|Contenitore|build'
# ⛔ R13 in small: the unit passes no bench options (§4.5)
BENCH_OPTIONS='--survey|--command-socket|--audio-test|--chatter|--unblock'

build_one()
{
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$OUTPUT/rpm/$1" lav="$CACHE/rpm-$1"
	local remark=""
	rm -rf "$u" "$lav"; mkdir -p "$u" "$lav"/{SOURCES,SPECS}

	if ! podman image exists "$imm"; then
		echo "== $b: the image is missing, building it"
		podman build -t "$imm" -f "$TREE/src/costruzione/Contenitore.$b" "$TREE/src/costruzione" \
			>"$u/immagine.log" 2>&1 || { echo "$b pack=NO bitmap=NO" | tee "$u/esito.txt"; return 1; }
	fi

	echo "== $b: sources"
	# ⛔ firewalld discards a service that is not well-formed XML, silently for
	#    whoever installs (`[M]` 29 Sep: `--` inside a comment).
	python3 -c 'import sys, xml.dom.minidom; xml.dom.minidom.parse(sys.argv[1])' "$HERE/remotix-firewalld.xml" \
		|| { echo "$b pack=NO remotix-firewalld.xml is not valid XML" | tee "$u/esito.txt"; return 1; }
	tar -C "$TREE" --transform "s,^,remotix-$VER/," \
		--exclude='*.o' --exclude='src/remotix' --exclude='*-client-protocol.h' --exclude='*-protocol.c' \
		-czf "$lav/SOURCES/remotix-$VER.tar.gz" src banchi/rcp packaging/rpm THIRD-PARTY-LICENSES LICENSE.md
	cp "$HERE/remotix.spec" "$lav/SPECS/"

	echo "== $b: rpmbuild (log in $u/rpmbuild.log)"
	podman run --rm -v "$lav:/work" "$imm" sh -c '
		if command -v dnf >/dev/null; then
			dnf -y -q install --setopt=install_weak_deps=False rpm-build rpmlint systemd-rpm-macros cpio selinux-policy-devel bzip2 >/dev/null 2>&1
		else
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
		  echo "## Provides"; rpm -qp --provides "$p"; } >/work/richieste.txt
		rpm -qplv "$p" >/work/file.txt
		rpm -qp --scripts "$p" >/work/scriptlet.txt
		rm -rf /work/estratto; mkdir /work/estratto; cd /work/estratto
		rpm2cpio "$p" | cpio -idm --quiet
		ldd usr/libexec/remotix/remotix >/work/ldd.txt 2>&1
		# R13: the bench-function sentence NOT in the package binary, and YES
		# in an rcp.o with BENCH_ON 1 (the positive check: without it, «not
		# found» could mean «I cannot search») — like the .deb line.
		sentence="the BENCH FUNCTION is ON"
		n=$(strings usr/libexec/remotix/remotix | grep -c "$sentence")
		rm -rf /work/positivo; mkdir /work/positivo; cd /work/positivo
		tar xzf /work/SOURCES/remotix-*.tar.gz --strip-components=1
		cd src; sed -i "s/^#define BENCH_ON 0\$/#define BENCH_ON 1/" rcp.c
		make TWIN=nobody rcp.o >/dev/null 2>&1
		p=$(strings rcp.o 2>/dev/null | grep -c "$sentence")
		echo "pack=$n positivo=$p" >/work/r13-binario.txt
	' >"$u/rpmbuild.log" 2>&1

	cp "$lav"/RPMS/*/*.rpm "$lav"/SRPMS/*.rpm "$u/" 2>/dev/null
	for f in rpmlint.txt richieste.txt file.txt scriptlet.txt ldd.txt r13-binario.txt; do
		[ -f "$lav/$f" ] && cp "$lav/$f" "$u/"
	done
	if ! ls "$u"/remotix-[0-9]*.x86_64.rpm >/dev/null 2>&1; then
		echo "$b pack=NO (see rpmbuild.log)" | tee "$u/esito.txt"
		return 1
	fi

	grep -q 'not found' "$u/ldd.txt" && remark="$remark ldd:not-found"
	grep -qE 'ngtcp2|nghttp3' "$u/ldd.txt" && remark="$remark ldd:quic-dinamiche"
	awk '{ print $NF }' "$u/file.txt" | grep -E "$DENYLIST" >"$u/r14.txt" && remark="$remark R14:RED"
	grep '^ExecStart' "$lav/estratto/usr/lib/systemd/system/remotix.service" | grep -E -- "$BENCH_OPTIONS" >"$u/r13.txt" \
		&& remark="$remark R13-unita:RED"
	grep -qx 'pack=0 positivo=[1-9][0-9]*' "$u/r13-binario.txt" 2>/dev/null \
		&& remark="$remark R13:green_v($(cat "$u/r13-binario.txt"))" \
		|| remark="$remark R13:RED($(cat "$u/r13-binario.txt" 2>/dev/null))"
	[ -s "$u/r14.txt" ] || remark="$remark R14:green_v"
	local lint
	lint=$(tail -1 "$u/rpmlint.txt")
	echo "$b pack=si $(ls "$u"/remotix-[0-9]*.x86_64.rpm | xargs -n1 basename) · rpmlint: $lint ·$remark" | tee "$u/esito.txt"
}

state=0
for b in "$@"; do build_one "$b" || state=1; done
printf '\n== summary (%s/rpm)\n' "$OUTPUT"
for b in "$@"; do cat "$OUTPUT/rpm/$b/esito.txt" 2>/dev/null || echo "$b (no outcome)"; done
exit $state
