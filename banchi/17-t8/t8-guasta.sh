#!/bin/bash
# t8-guasta.sh — fase 17, T8: guasti APPOSTA nell'archivio servito (sul server), e il ripristino.
#
#   bash t8-guasta.sh <guasto>      prima di ogni guasto si salva l'archivio com'è (una volta sola)
#   bash t8-guasta.sh ripristina
#
#   (i guasti della catena A — catalogo, revoche, rotazione — sono spariti con lei: DECISIONI §10.21)
#   deb-byte | rpm-byte | pacman-byte     un byte dei metadati cambiato (R17)          ⇒ il gestore rifiuta
#   deb-firma | rpm-firma | pacman-firma  i metadati firmati da una chiave ESTRANEA (R17)
#   pacchetto-byte   un byte del pacchetto remotix N+1 cambiato (deb, rpm, pacman)
set -euo pipefail
V=/media/REMOTIX/vm17
A=$V/${DOVE:-archivio}; S=$V/t8/${DOVE:-archivio}-sano; E=$V/t8/estranea.gpg
ge() { gpg --homedir "$E" --batch --yes --pinentry-mode loopback --passphrase '' -u "$(gpg --homedir "$E" --list-keys --with-colons | awk -F: '/^fpr/{print $10; exit}')" "$@"; }
byte() {  # cambia un byte a metà del file
	python3 -c "import sys; p=sys.argv[1]; b=bytearray(open(p,'rb').read()); i=len(b)//2; b[i]^=0x20; open(p,'wb').write(bytes(b))" "$1"
}
[ "${1:-}" = ripristina ] || { [ -d "$S" ] || cp -a "$A" "$S"; }
case ${1:?guasto} in
ripristina)       [ -d "$S" ] && { rm -rf "$A"; cp -a "$S" "$A"; rm -rf "$S"; } ;;
deb-byte)         byte "$A/deb/dists/debian13-stabile/main/binary-amd64/Packages"; rm -f "$A/deb/dists/debian13-stabile/main/binary-amd64/Packages.gz" ;;
deb-firma)        d=$A/deb/dists/debian13-stabile; ge --clearsign -o "$d/InRelease" "$d/Release"; ge --armor --detach-sign -o "$d/Release.gpg" "$d/Release" ;;
rpm-byte)         byte "$A/rpm/stabile/fedora44/repodata/repomd.xml" ;;
rpm-firma)        ge --armor --detach-sign -o "$A/rpm/stabile/fedora44/repodata/repomd.xml.asc" "$A/rpm/stabile/fedora44/repodata/repomd.xml" ;;
pacman-byte)      byte "$A/pacman/stabile/x86_64/remotix.db" ;;
pacman-firma)     ge --detach-sign -o "$A/pacman/stabile/x86_64/remotix.db.sig" "$A/pacman/stabile/x86_64/remotix.db" ;;
pacchetto-byte)   # il remotix più nuovo di ogni famiglia (la N+1 in attesa)
	for f in $(ls -v "$A"/deb/pool/debian13-stabile/remotix_*.deb | tail -1) $(ls -v "$A"/rpm/stabile/fedora44/remotix-[0-9]*.rpm | tail -1) \
	         $(ls -v "$A"/pacman/stabile/x86_64/remotix-[0-9]*.pkg.tar.zst 2>/dev/null | tail -1); do byte "$f"; done ;;
*) sed -n 3,13p "$0"; exit 2 ;;
esac
echo "guasto: $1"
