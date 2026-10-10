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
#   4. in $USCITA/rpm/<target>/: the .rpm files, rpmbuild.log, rpmlint.txt,
#      richieste.txt (Requires, automatic and written), file.txt, esito.txt;
#      and the two small checks of R13/R14 (blacklist of bench files,
#      bench options in the unit).
#
# ⚠ No /tmp: on the laptop it is almost full (like costruisci-tutti.sh).
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
CACHE=${CACHE:-$USCITA/.lavoro}
TUTTI=(fedora44 alma10 tumbleweed leap16)
# the version: the release one (RX_VERSIONE, packaging/rilascio.sh) or the spec default
VER=${RX_VERSIONE:-$(sed -n 's/^Version:.*!?rx_versione:\([^}]*\)}.*/\1/p' "$QUI/remotix.spec")}

command -v podman >/dev/null 2>&1 || { echo "⛔ podman is missing"; exit 2; }
mkdir -p "$CACHE/tmp" "$USCITA/rpm"
export TMPDIR="$CACHE/tmp"
if [ $# -eq 0 ] || [ "$1" = tutti ]; then set -- "${TUTTI[@]}"; fi

# ⛔ R14 in small: nothing from the bench in the package (§6.4)
LISTA_NERA='provisiona|sudoers|gpu-udev|riavvia-|ld\.so\.conf|/prova|banchi|\.py$|Contenitore|costruisci'
# ⛔ R13 in small: the unit passes no bench options (§4.5)
OPZIONI_BANCO='--rilievo|--comando-socket|--audio-prova|--parlantina|--sblocca'

costruisci_uno()
{
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$USCITA/rpm/$1" lav="$CACHE/rpm-$1"
	local nota=""
	rm -rf "$u" "$lav"; mkdir -p "$u" "$lav"/{SOURCES,SPECS}

	if ! podman image exists "$imm"; then
		echo "== $b: the image is missing, building it"
		podman build -t "$imm" -f "$ALBERO/src/costruzione/Contenitore.$b" "$ALBERO/src/costruzione" \
			>"$u/immagine.log" 2>&1 || { echo "$b pacchetto=NO immagine=NO" | tee "$u/esito.txt"; return 1; }
	fi

	echo "== $b: sources"
	# ⛔ firewalld discards a service that is not well-formed XML, silently for
	#    whoever installs (`[M]` 29 Sep: `--` inside a comment).
	python3 -c 'import sys, xml.dom.minidom; xml.dom.minidom.parse(sys.argv[1])' "$QUI/remotix-firewalld.xml" \
		|| { echo "$b pacchetto=NO remotix-firewalld.xml is not valid XML" | tee "$u/esito.txt"; return 1; }
	tar -C "$ALBERO" --transform "s,^,remotix-$VER/," \
		--exclude='*.o' --exclude='src/remotix' --exclude='*-client-protocol.h' --exclude='*-protocol.c' \
		-czf "$lav/SOURCES/remotix-$VER.tar.gz" src banchi/rcp packaging/rpm THIRD-PARTY-LICENSES
	cp "$QUI/remotix.spec" "$lav/SPECS/"

	echo "== $b: rpmbuild (log in $u/rpmbuild.log)"
	podman run --rm -v "$lav:/lavoro" "$imm" sh -c '
		if command -v dnf >/dev/null; then
			dnf -y -q install --setopt=install_weak_deps=False rpm-build rpmlint systemd-rpm-macros cpio selinux-policy-devel bzip2 >/dev/null 2>&1
		else
			zypper -n -q install --no-recommends --force-resolution rpm-build rpmlint systemd-rpm-macros cpio selinux-policy-devel bzip2 >/dev/null 2>&1
		fi
		rpm -q rpm-build rpmlint | sed "s/^/tools: /"
		rpm --eval "dist=%{?dist} fedora=%{?fedora} rhel=%{?rhel} suse_version=%{?suse_version} pamvendor=%{?_pam_vendordir}"
		rpmbuild -ba --define "_topdir /lavoro" --define "rx_versione '"$VER"'" --define "rx_rilascio '"${RX_REVISIONE:-1}"'" '"${RX_SELINUX_PERMISSIVO:+--define \"rx_selinux_permissivo 1\"}"' /lavoro/SPECS/remotix.spec 2>&1
		echo "rpmbuild-esito=$?"
		ls /lavoro/RPMS/*/*.rpm >/dev/null 2>&1 || exit 1
		rpmlint /lavoro/SPECS/remotix.spec /lavoro/RPMS/*/*.rpm /lavoro/SRPMS/*.rpm >/lavoro/rpmlint.txt 2>&1
		p=$(ls /lavoro/RPMS/x86_64/remotix-[0-9]*.rpm)
		{ echo "## Requires (automatic + written)"; rpm -qpR "$p"
		  echo "## Recommends"; rpm -qp --recommends "$p"
		  echo "## Provides"; rpm -qp --provides "$p"; } >/lavoro/richieste.txt
		rpm -qplv "$p" >/lavoro/file.txt
		rpm -qp --scripts "$p" >/lavoro/scriptlet.txt
		rm -rf /lavoro/estratto; mkdir /lavoro/estratto; cd /lavoro/estratto
		rpm2cpio "$p" | cpio -idm --quiet
		ldd usr/libexec/remotix/remotix >/lavoro/ldd.txt 2>&1
		# R13: the bench-function sentence NOT in the package binary, and YES
		# in an rcp.o with BANCO_ACCESO 1 (the positive check: without it, «not
		# found» could mean «I cannot search») — like the .deb line.
		frase="FUNZIONE DI BANCO e'"'"' ACCESA"
		n=$(strings usr/libexec/remotix/remotix | grep -c "$frase")
		rm -rf /lavoro/positivo; mkdir /lavoro/positivo; cd /lavoro/positivo
		tar xzf /lavoro/SOURCES/remotix-*.tar.gz --strip-components=1
		cd src; sed -i "s/^#define BANCO_ACCESO 0\$/#define BANCO_ACCESO 1/" rcp.c
		make GEMELLO=nessuno rcp.o >/dev/null 2>&1
		p=$(strings rcp.o 2>/dev/null | grep -c "$frase")
		echo "pacchetto=$n positivo=$p" >/lavoro/r13-binario.txt
	' >"$u/rpmbuild.log" 2>&1

	cp "$lav"/RPMS/*/*.rpm "$lav"/SRPMS/*.rpm "$u/" 2>/dev/null
	for f in rpmlint.txt richieste.txt file.txt scriptlet.txt ldd.txt r13-binario.txt; do
		[ -f "$lav/$f" ] && cp "$lav/$f" "$u/"
	done
	if ! ls "$u"/remotix-[0-9]*.x86_64.rpm >/dev/null 2>&1; then
		echo "$b pacchetto=NO (see rpmbuild.log)" | tee "$u/esito.txt"
		return 1
	fi

	grep -q 'not found' "$u/ldd.txt" && nota="$nota ldd:not-found"
	grep -qE 'ngtcp2|nghttp3' "$u/ldd.txt" && nota="$nota ldd:quic-dinamiche"
	awk '{ print $NF }' "$u/file.txt" | grep -E "$LISTA_NERA" >"$u/r14.txt" && nota="$nota R14:ROSSO"
	grep '^ExecStart' "$lav/estratto/usr/lib/systemd/system/remotix.service" | grep -E -- "$OPZIONI_BANCO" >"$u/r13.txt" \
		&& nota="$nota R13-unita:ROSSO"
	grep -qx 'pacchetto=0 positivo=[1-9][0-9]*' "$u/r13-binario.txt" 2>/dev/null \
		&& nota="$nota R13:verde($(cat "$u/r13-binario.txt"))" \
		|| nota="$nota R13:ROSSO($(cat "$u/r13-binario.txt" 2>/dev/null))"
	[ -s "$u/r14.txt" ] || nota="$nota R14:verde"
	local lint
	lint=$(tail -1 "$u/rpmlint.txt")
	echo "$b pacchetto=si $(ls "$u"/remotix-[0-9]*.x86_64.rpm | xargs -n1 basename) · rpmlint: $lint ·$nota" | tee "$u/esito.txt"
}

stato=0
for b in "$@"; do costruisci_uno "$b" || stato=1; done
printf '\n== summary (%s/rpm)\n' "$USCITA"
for b in "$@"; do cat "$USCITA/rpm/$b/esito.txt" 2>/dev/null || echo "$b (no outcome)"; done
exit $stato
