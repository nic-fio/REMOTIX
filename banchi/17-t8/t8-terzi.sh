#!/usr/bin/env bash
# t8-terzi.sh — fase 17, T8, R18: gli attrezzi della prova «la chiave vale solo per REMOTIX».
#
#   (sul portatile)   bash banchi/17-t8/t8-terzi.sh <uscita>
#
# Fa, con una chiave GPG «ESTRANEA» (usa e getta, di nessuno):
#   <uscita>/terzi/   un archivio DI TERZI (apt e dnf) col pacchetto «terzi-prova» 1.0, firmato dalla
#                     chiave estranea: la VM lo ha configurato PRIMA di REMOTIX; dopo, i suoi file e
#                     la sua chiave devono essere identici (R18);
#   <uscita>/intrusi/ «hello» 99.0 (.deb e .rpm): un pacchetto NON di REMOTIX, da pubblicare apposta
#                     nell'archivio di REMOTIX (firmato con la NOSTRA chiave, come se lo avessimo
#                     pubblicato per sbaglio o ce l'avesse messo un altro): dalla VM non deve essere
#                     installabile (apt: pin -1 sull'host; dnf: includepkgs);
#   <uscita>/estranea.gpg/  il portachiavi della chiave estranea (per R17: una firma sbagliata).
set -euo pipefail
U=$(realpath -m "${1:?uscita}")
mkdir -p "$U/terzi/deb/pool" "$U/terzi/rpm" "$U/intrusi" "$U/lavoro"
export TMPDIR=$U/lavoro LC_ALL=C
G=$U/estranea.gpg
if [ ! -d "$G" ]; then
	mkdir -p "$G"; chmod 700 "$G"
	gpg --homedir "$G" --batch --pinentry-mode loopback --passphrase '' \
		--quick-gen-key "chiave ESTRANEA di prova (T8, di nessuno)" ed25519 sign never
fi
FPR=$(gpg --homedir "$G" --list-keys --with-colons | awk -F: '/^fpr/{print $10; exit}')
gpg --homedir "$G" --armor --export "$FPR" >"$U/terzi/terzi.asc"
g() { gpg --homedir "$G" --batch --yes --pinentry-mode loopback --passphrase '' -u "$FPR" "$@"; }

deb() {  # deb <nome> <versione> <uscita>
	local d=$U/lavoro/$1-$2
	rm -rf "$d"; mkdir -p "$d/DEBIAN" "$d/usr/share/doc/$1"
	printf 'Package: %s\nVersion: %s\nArchitecture: all\nMaintainer: prova <prova@example.invalid>\nDescription: pacchetto di prova della fase 17 T8 (R18)\n' "$1" "$2" >"$d/DEBIAN/control"
	echo "prova T8" >"$d/usr/share/doc/$1/LEGGIMI"
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

# i due .rpm (terzi-prova firmato dalla chiave estranea; hello 99.0 lo firmerà pubblica.sh con la nostra)
rm -rf "$U/lavoro/g"; cp -a "$G" "$U/lavoro/g"; rm -f "$U/lavoro/g"/S.*
podman run --rm -v "$U:/u:Z" -e FPR="$FPR" registry.fedoraproject.org/fedora:44 sh -c '
	set -e
	dnf -y -q install rpm-build rpm-sign createrepo_c gnupg2 >/dev/null 2>&1
	export GNUPGHOME=/u/lavoro/g; chmod 700 $GNUPGHOME
	for p in "terzi-prova 1.0" "hello 99.0"; do
		set -- $p
		mkdir -p /r/SPECS
		printf "Name: %s\nVersion: %s\nRelease: 1\nSummary: prova T8 (R18)\nLicense: MIT\nBuildArch: noarch\n%%description\nprova\n%%files\n" "$1" "$2" >/r/SPECS/$1.spec
		rpmbuild -bb --define "_topdir /r" /r/SPECS/$1.spec >/dev/null 2>&1
	done
	cp /r/RPMS/noarch/terzi-prova-*.rpm /u/terzi/rpm/
	cp /r/RPMS/noarch/hello-*.rpm /u/intrusi/
	rpmsign --addsign --define "_gpg_name $FPR" /u/terzi/rpm/*.rpm >/dev/null
	createrepo_c --quiet /u/terzi/rpm
	gpg --batch --yes -u "$FPR" --armor --detach-sign -o /u/terzi/rpm/repodata/repomd.xml.asc /u/terzi/rpm/repodata/repomd.xml'
rm -rf "$U/lavoro"
find "$U" -type f | sort
