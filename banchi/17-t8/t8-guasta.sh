#!/bin/bash
# t8-guasta.sh — fase 17, T8: guasti APPOSTA nell'archivio servito (sul server), e il ripristino.
#
#   bash t8-guasta.sh <guasto>      prima di ogni guasto si salva l'archivio com'è (una volta sola)
#   bash t8-guasta.sh ripristina
#
#   catalogo-byte    un byte del catalogo dello stabile cambiato (la firma resta)     ⇒ RX-TRUST-007
#   catalogo-scaduto il catalogo sequenza 6 scaduto, firmato bene                     ⇒ RX-TRUST-002
#   revoca           le revoche 2: A-2026 revocata                                   ⇒ RX-TRUST-010
#   rotazione        revoche 2 + catalogo 7 firmato con A-2027                         ⇒ si procede
#   deb-byte | rpm-byte | pacman-byte     un byte dei metadati cambiato (R17)          ⇒ il gestore rifiuta
#   deb-firma | rpm-firma | pacman-firma  i metadati firmati da una chiave ESTRANEA (R17)
#   pacchetto-byte   un byte del pacchetto remotix N+1 cambiato (deb, rpm, pacman)
set -euo pipefail
V=/media/REMOTIX/vm17
A=$V/archivio; S=$V/t8/archivio-sano; G=$V/t8/guasti; E=$V/t8/estranea.gpg
ge() { gpg --homedir "$E" --batch --yes --pinentry-mode loopback --passphrase '' -u "$(gpg --homedir "$E" --list-keys --with-colons | awk -F: '/^fpr/{print $10; exit}')" "$@"; }
byte() {  # cambia un byte a metà del file
	python3 -c "import sys; p=sys.argv[1]; b=bytearray(open(p,'rb').read()); i=len(b)//2; b[i]^=0x20; open(p,'wb').write(bytes(b))" "$1"
}
[ "${1:-}" = ripristina ] || { [ -d "$S" ] || cp -a "$A" "$S"; }
case ${1:?guasto} in
ripristina)       [ -d "$S" ] && { rm -rf "$A"; cp -a "$S" "$A"; rm -rf "$S"; } ;;
catalogo-byte)    byte "$A/catalogo/stabile/catalogo.json" ;;
catalogo-scaduto) cp "$G/scaduto/"* "$A/catalogo/stabile/" ;;
revoca)           cp "$G/revoca/"* "$A/catalogo/" ;;
rotazione)        cp "$G/rotazione/revoche.json"* "$A/catalogo/"; cp "$G/rotazione/catalogo.json"* "$A/catalogo/stabile/" ;;
deb-byte)         byte "$A/deb/dists/debian13-stabile/main/binary-amd64/Packages"; rm -f "$A/deb/dists/debian13-stabile/main/binary-amd64/Packages.gz" ;;
deb-firma)        d=$A/deb/dists/debian13-stabile; ge --clearsign -o "$d/InRelease" "$d/Release"; ge --armor --detach-sign -o "$d/Release.gpg" "$d/Release" ;;
rpm-byte)         byte "$A/rpm/stabile/fedora44/repodata/repomd.xml" ;;
rpm-firma)        ge --armor --detach-sign -o "$A/rpm/stabile/fedora44/repodata/repomd.xml.asc" "$A/rpm/stabile/fedora44/repodata/repomd.xml" ;;
pacman-byte)      byte "$A/pacman/stabile/x86_64/remotix.db" ;;
pacman-firma)     ge --detach-sign -o "$A/pacman/stabile/x86_64/remotix.db.sig" "$A/pacman/stabile/x86_64/remotix.db" ;;
pacchetto-byte)
	for f in "$A"/deb/pool/debian13-stabile/remotix_0.17.0-2+deb13_amd64.deb "$A"/rpm/stabile/fedora44/remotix-0.17.0-2.fc44.x86_64.rpm \
	         "$A"/pacman/stabile/x86_64/remotix-0.17.0-5-x86_64.pkg.tar.zst; do byte "$f"; done ;;
*) sed -n 3,16p "$0"; exit 2 ;;
esac
echo "guasto: $1"
