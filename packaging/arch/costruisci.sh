#!/usr/bin/env bash
# costruisci.sh — il pacchetto Arch di REMOTIX, dal deposito, nel contenitore.
#
#     packaging/arch/costruisci.sh [commit]        (predefinito: HEAD)
#
# 1. PKGBUILD, remotix.install e il tarball (src/, banchi/rcp/, packaging/arch/)
#    escono dallo STESSO commit (`git archive`): cio' che non e' committato non
#    entra, e il pacchetto dice da quale commit viene (sorgente.txt).
# 2. makepkg dentro `localhost/remotix-costruzione-arch`
#    (src/costruzione/Contenitore.arch; la costruisce costruisci-tutti.sh arch),
#    come utente, senza -s: le dipendenze di costruzione ci sono gia'.
# 3. namcap su PKGBUILD e pacchetto, in un contenitore usa-e-getta (namcap.txt).
# 4. R14: l'elenco dei file del pacchetto contro la lista nera dei banchi.
#
# Uscita in $USCITA (predefinito costruzione-uscita/pacchetto-arch, ignorata
# da git).  ⚠ Niente /tmp: sul portatile e' quasi pieno.
set -euo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
COMMIT=$(git -C "$ALBERO" rev-parse "${1:-HEAD}")
USCITA=${USCITA:-$ALBERO/costruzione-uscita/pacchetto-arch}
IMM=${IMM:-localhost/remotix-costruzione-arch}
LAV="$USCITA/.lavoro"
PKGVER=$(git -C "$ALBERO" show "$COMMIT:packaging/arch/PKGBUILD" | sed -n 's/^pkgver=//p')
# il rilascio (packaging/rilascio.sh): RX_VERSIONE = pkgver, RX_REVISIONE = pkgrel
PKGVER=${RX_VERSIONE:-$PKGVER}

rm -rf "$LAV"; mkdir -p "$LAV/tmp"
export TMPDIR="$LAV/tmp"

git -C "$ALBERO" archive "$COMMIT" packaging/arch/PKGBUILD packaging/arch/remotix.install \
	| tar -x -C "$LAV" --strip-components=2
# T8: RX_REVISIONE = il pkgrel di un rilascio di manutenzione (una ricostruzione)
[ -n "${RX_REVISIONE:-}" ] && sed -i "s/^pkgrel=.*/pkgrel=$RX_REVISIONE/" "$LAV/PKGBUILD"
sed -i "s/^pkgver=.*/pkgver=$PKGVER/" "$LAV/PKGBUILD"
git -C "$ALBERO" archive --format=tar.gz --prefix="remotix-$PKGVER/" \
	-o "$LAV/remotix-$PKGVER.tar.gz" "$COMMIT" src banchi/rcp packaging/arch
{
	echo "commit $COMMIT"
	echo "tarball $(sha256sum "$LAV/remotix-$PKGVER.tar.gz" | cut -d' ' -f1)  remotix-$PKGVER.tar.gz"
	echo "immagine $(podman image inspect -f '{{.Id}}' "$IMM" | cut -c1-12)"
} >"$LAV/sorgente.txt"

echo "== makepkg ($COMMIT)"
# R23: SOURCE_DATE_EPOCH = la data del commit.  `[M]` 29 set: senza, due
# costruzioni danno lo stesso binario (sha256 uguale) e pacchetti diversi
# solo per `builddate` in .PKGINFO/.BUILDINFO e le date di .MTREE.
SDE=$(git -C "$ALBERO" log -1 --format=%ct "$COMMIT")
podman run --rm --userns=keep-id -v "$LAV:/pkg" -w /pkg -e HOME=/pkg/tmp \
	-e SOURCE_DATE_EPOCH="$SDE" "$IMM" \
	makepkg -f --noconfirm >"$LAV/makepkg.log" 2>&1 \
	|| { tail -30 "$LAV/makepkg.log"; echo "⛔ makepkg fallito (vedi $LAV/makepkg.log)"; exit 1; }
PKG=$(cd "$LAV" && ls remotix-"$PKGVER"-*-x86_64.pkg.tar.zst)

echo "== namcap"
podman run --rm -v "$LAV:/pkg:ro" "$IMM" sh -c \
	"pacman -Sy --noconfirm --needed namcap >/dev/null 2>&1 && cd /pkg && echo '# PKGBUILD' && namcap PKGBUILD; echo '# $PKG' && namcap -i $PKG" \
	>"$LAV/namcap.txt" 2>&1 || true

echo "== R14: file dei banchi nel pacchetto?"
tar -tf "$LAV/$PKG" >"$LAV/elenco.txt"
if grep -E 'provisiona|gpu-udev|riavvia-|sudoers|ld\.so\.conf|banchi|/opt/' "$LAV/elenco.txt"; then
	echo "⛔ R14 ROSSO"; exit 1
fi
echo "R14 verde: $(grep -vc '/$' "$LAV/elenco.txt") voci, nessuna della lista nera"

mkdir -p "$USCITA"
cp "$LAV/$PKG" "$LAV/sorgente.txt" "$LAV/namcap.txt" "$LAV/makepkg.log" "$LAV/elenco.txt" "$USCITA/"
tar -xOf "$LAV/$PKG" .PKGINFO >"$USCITA/PKGINFO.txt"
echo "== pronto: $USCITA/$PKG"
cat "$USCITA/namcap.txt"
