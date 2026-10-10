#!/usr/bin/env bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
# t8-terzi.sh — phase 17, T8, R18: the tools of the test "the key is valid only for REMOTIX".
#
#   (on the laptop)   bash banchi/17-t8/t8-terzi.sh <output>
#
# Builds, with a "FOREIGN" GPG key (throwaway, nobody's):
#   <output>/terzi/   a THIRD-PARTY archive (apt and dnf) with the package "terzi-prova" 1.0, signed by the
#                     foreign key: the VM configured it BEFORE REMOTIX; afterwards, its files and
#                     its key must be identical (R18);
#   <output>/intrusi/ "hello" 99.0 (.deb and .rpm): a package NOT from REMOTIX, to be published on purpose
#                     in the REMOTIX archive (signed with OUR key, as if we had
#                     published it by mistake or someone else had put it there): from the VM it must not be
#                     installable (apt: pin -1 on the host; dnf: includepkgs);
#   <output>/estranea.gpg/  the keyring of the foreign key (for R17: a wrong signature).
set -euo pipefail
U=$(realpath -m "${1:?output}")
mkdir -p "$U/terzi/deb/pool" "$U/terzi/rpm" "$U/intrusi" "$U/lavoro"
export TMPDIR=$U/lavoro LC_ALL=C
G=$U/estranea.gpg
if [ ! -d "$G" ]; then
	mkdir -p "$G"; chmod 700 "$G"
	gpg --homedir "$G" --batch --pinentry-mode loopback --passphrase '' \
		--quick-gen-key "FOREIGN test key (T8, nobody's)" ed25519 sign never
fi
FPR=$(gpg --homedir "$G" --list-keys --with-colons | awk -F: '/^fpr/{print $10; exit}')
gpg --homedir "$G" --armor --export "$FPR" >"$U/terzi/terzi.asc"
g() { gpg --homedir "$G" --batch --yes --pinentry-mode loopback --passphrase '' -u "$FPR" "$@"; }

deb() {  # deb <name> <version> <output>
	local d=$U/lavoro/$1-$2
	rm -rf "$d"; mkdir -p "$d/DEBIAN" "$d/usr/share/doc/$1"
	printf 'Package: %s\nVersion: %s\nArchitecture: all\nMaintainer: prova <prova@example.invalid>\nDescription: test package of phase 17 T8 (R18)\n' "$1" "$2" >"$d/DEBIAN/control"
	echo "T8 test" >"$d/usr/share/doc/$1/LEGGIMI"
	dpkg-deb --root-owner-group --build "$d" "$3/${1}_${2}_all.deb" >/dev/null
}
deb terzi-prova 1.0-1 "$U/terzi/deb/pool"
deb hello 99.0-1 "$U/intrusi"
(cd "$U/terzi/deb" && mkdir -p dists/terzi/main/binary-amd64 && apt-ftparchive packages pool >dists/terzi/main/binary-amd64/Packages \
	&& apt-ftparchive -o APT::FTPArchive::Release::Origin=terzi -o APT::FTPArchive::Release::Suite=terzi \
	   -o APT::FTPArchive::Release::Codename=terzi -o APT::FTPArchive::Release::Components=main \
	   -o APT::FTPArchive::Release::Architectures=amd64 release dists/terzi >"$U/lavoro/Release" \
	&& cp "$U/lavoro/Release" dists/terzi/Release)
g --clearsign -o "$U/terzi/deb/dists/terzi/InRelease" "$U/terzi/deb/dists/terzi/Release"

# the two .rpm (terzi-prova signed by the foreign key; hello 99.0 will be signed by pubblica.sh with ours)
rm -rf "$U/lavoro/g"; cp -a "$G" "$U/lavoro/g"; rm -f "$U/lavoro/g"/S.*
podman run --rm -v "$U:/u:Z" -e FPR="$FPR" registry.fedoraproject.org/fedora:44 sh -c '
	set -e
	dnf -y -q install rpm-build rpm-sign createrepo_c gnupg2 >/dev/null 2>&1
	export GNUPGHOME=/u/lavoro/g; chmod 700 $GNUPGHOME
	for p in "terzi-prova 1.0" "hello 99.0"; do
		set -- $p
		mkdir -p /r/SPECS
		printf "Name: %s\nVersion: %s\nRelease: 1\nSummary: T8 test (R18)\nLicense: MIT\nBuildArch: noarch\n%%description\ntest\n%%files\n" "$1" "$2" >/r/SPECS/$1.spec
		rpmbuild -bb --define "_topdir /r" /r/SPECS/$1.spec >/dev/null 2>&1
	done
	cp /r/RPMS/noarch/terzi-prova-*.rpm /u/terzi/rpm/
	cp /r/RPMS/noarch/hello-*.rpm /u/intrusi/
	rpmsign --addsign --define "_gpg_name $FPR" /u/terzi/rpm/*.rpm >/dev/null
	createrepo_c --quiet /u/terzi/rpm
	gpg --batch --yes -u "$FPR" --armor --detach-sign -o /u/terzi/rpm/repodata/repomd.xml.asc /u/terzi/rpm/repodata/repomd.xml'
rm -rf "$U/lavoro"
find "$U" -type f | sort
