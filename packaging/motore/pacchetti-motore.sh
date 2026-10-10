#!/usr/bin/env bash
# pacchetti-motore.sh — i pacchetti del MOTORE, per il pacchetto unico di REMOTIX (il .run).
#
#     RX_VERSIONE=X.Y.Z RX_REVISIONE=R packaging/motore/pacchetti-motore.sh [uscita]
#                                                  (predefinito costruzione-uscita/motore)
#
# Lo chiama il comando di rilascio (packaging/rilascio.sh), DOPO aver costruito il motore statico
# con la versione del rilascio (installatore/costruisci.sh con RX_VERSIONE). Il motore si
# impacchetta così com'è, per le tre famiglie:
#   · remotix-install_<V>-<R>_amd64.deb           (dpkg-deb: nessuna libreria da calcolare)
#   · remotix-install-<V>-<R>.x86_64.rpm          (rpmbuild nel contenitore fedora:44)
#   · remotix-install-<V>-<R>-x86_64.pkg.tar.zst  (makepkg nel contenitore di Arch)
# Il catalogo sta dentro il motore (DECISIONI §10.21). Il pacchetto resta sulla macchina dopo
# l'installazione (status, uninstall); a ogni cambio di versione gli script chiamano
# `remotix-install post-upgrade`. Niente chiave d'archivio: l'archivio non c'è più (§10.36).
#
# Ambiente: RX_VERSIONE (obbligatoria: quella del motore deve essere lei), RX_REVISIONE (1), MOTORE
# (installatore/uscita/remotix-install).
# ⚠ Niente /tmp: sul portatile è quasi pieno.
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
U=${1:-$ALBERO/costruzione-uscita/motore}
V=${RX_VERSIONE:?RX_VERSIONE: la versione del rilascio}
R=${RX_REVISIONE:-1}
MOTORE=${MOTORE:-$ALBERO/installatore/uscita/remotix-install}
M=$ALBERO/packaging/motore
mkdir -p "$U"
L=$U/.lavoro; rm -rf "$L"; mkdir -p "$L"
export TMPDIR=$L

vm=$("$MOTORE" version | awk '{print $1}')
[ "$vm" = "$V" ] || { echo "⛔ il motore $MOTORE dice $vm, il rilascio è $V"; exit 1; }
cp "$MOTORE" "$L/remotix-install"
cp "$M/README" "$L/"
echo "== il motore $V-$R ($(sha256sum "$L/remotix-install" | cut -c1-16)…)"

echo "== .deb del motore"
D=$L/deb; mkdir -p "$D/DEBIAN" "$D/usr/bin" "$D/usr/share/remotix-install"
install -m 755 "$L/remotix-install" "$D/usr/bin/"
install -m 644 "$L/README" "$D/usr/share/remotix-install/"
cat >"$D/DEBIAN/control" <<EOF
Package: remotix-install
Version: $V-$R
Architecture: amd64
Maintainer: nicfio <nicfio@gmail.com>
Section: admin
Priority: optional
Depends: systemd
Description: il motore d'installazione di REMOTIX
 Installa, verifica, certifica e disinstalla REMOTIX. Porta dentro di sé il
 catalogo delle combinazioni supportate, che si aggiorna con questo pacchetto.
 REMOTIX si aggiorna col sistema (apt upgrade): niente timer.
EOF
cat >"$D/DEBIAN/postinst" <<'EOF'
#!/bin/sh
# dopo un aggiornamento: il motore annota le versioni e dice se l'installazione è ancora certificata
# (DECISIONI §10.12 punto 4, §10.23). Non fa mai fallire apt.
set -e
if [ "$1" = configure ] && [ -n "${2:-}" ]; then
	/usr/bin/remotix-install post-upgrade || true
fi
exit 0
EOF
chmod 755 "$D/DEBIAN/postinst"
SOURCE_DATE_EPOCH=$(git -C "$ALBERO" log -1 --format=%ct) \
	dpkg-deb --root-owner-group -Zxz --build "$D" "$U/remotix-install_${V}-${R}_amd64.deb" >/dev/null

echo "== .rpm del motore (fedora:44)"
P=$L/rpm; mkdir -p "$P/SOURCES" "$P/SPECS"
cp "$L/remotix-install" "$L/README" "$P/SOURCES/"
cp "$M/remotix-install.spec" "$P/SPECS/"
podman run --rm -v "$P:/lavoro:Z" registry.fedoraproject.org/fedora:44 sh -c "
	dnf -y -q install rpm-build systemd-rpm-macros >/dev/null 2>&1
	rpmbuild -bb --define '_topdir /lavoro' --define 'rx_versione $V' --define 'rx_rilascio $R' /lavoro/SPECS/remotix-install.spec" >"$U/rpmbuild.log" 2>&1 \
	|| { tail -20 "$U/rpmbuild.log"; exit 1; }
cp "$P"/RPMS/x86_64/remotix-install-*.rpm "$U/"

echo "== pacchetto Arch del motore"
A=$L/arch; mkdir -p "$A"
cp "$L/remotix-install" "$L/README" "$M/PKGBUILD" "$M/remotix-install.install" "$A/"
podman run --rm --userns=keep-id -v "$A:/pkg" -w /pkg -e HOME=/pkg -e RX_VERSIONE="$V" -e RX_RILASCIO="$R" \
	-e SOURCE_DATE_EPOCH="$(git -C "$ALBERO" log -1 --format=%ct)" localhost/remotix-costruzione-arch \
	makepkg -f --noconfirm --nodeps >"$U/makepkg.log" 2>&1 || { tail -20 "$U/makepkg.log"; exit 1; }
cp "$A"/remotix-install-*-x86_64.pkg.tar.zst "$U/"

ls -l "$U"
