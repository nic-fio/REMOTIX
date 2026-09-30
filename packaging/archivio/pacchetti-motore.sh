#!/usr/bin/env bash
# pacchetti-motore.sh — i pacchetti del MOTORE e della CHIAVE per l'archivio di REMOTIX (T8).
#
#     packaging/archivio/pacchetti-motore.sh [uscita]      (predefinito costruzione-uscita/motore)
#
# Il motore (installatore/, Go statico) si costruisce UNA volta e si impacchetta per le tre famiglie:
#   · remotix-install_<V>-<R>_amd64.deb       (dpkg-deb: nessuna libreria da calcolare)
#   · remotix-install-<V>-<R>.x86_64.rpm      (rpmbuild nel contenitore fedora:44, packaging/motore/*.spec)
#   · remotix-install-<V>-<R>-x86_64.pkg.tar.zst (makepkg nel contenitore di Arch, packaging/motore/PKGBUILD)
#   · remotix-archive-keyring_<data>-1_all.deb (la chiave della catena B in /usr/share/keyrings)
# Ognuno porta il motore, la sua FIRMA della catena A (/usr/share/remotix-install/remotix-install.firma)
# e il timer degli aggiornamenti SPENTO.
#
# Ambiente: CHIAVI (predefinito ~/.local/share/remotix-chiavi-di-prova: le chiavi DI PROVA, fuori dal
# deposito), SOTTOCHIAVE_A (A-2026), RX_RILASCIO (1).
# ⚠ Niente /tmp: sul portatile è quasi pieno.
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
INST=$ALBERO/installatore
U=${1:-$ALBERO/costruzione-uscita/motore}
CHIAVI=${CHIAVI:-$HOME/.local/share/remotix-chiavi-di-prova}
SUB=${SOTTOCHIAVE_A:-A-2026}
R=${RX_RILASCIO:-1}
M=$ALBERO/packaging/motore
mkdir -p "$U"
L=$U/.lavoro; rm -rf "$L"; mkdir -p "$L"
export TMPDIR=$L

echo "== il motore (installatore/costruisci.sh)"
"$INST/costruisci.sh" >/dev/null
V=$("$INST/uscita/remotix-install" versione | awk '{print $1}')
cp "$INST/uscita/remotix-install" "$L/"
echo "   versione $V"

echo "== la firma della catena A ($SUB)"
rm -rf "$INST/.cache/chiavi-firma"; cp -a "$CHIAVI/a" "$INST/.cache/chiavi-firma"
cp "$L/remotix-install" "$INST/.cache/remotix-install-da-firmare"
"$INST/costruisci.sh" go run ./strumenti/chiavi-a firma /src/.cache/chiavi-firma "$SUB" motore /src/.cache/remotix-install-da-firmare
mv "$INST/.cache/remotix-install-da-firmare.firma" "$L/remotix-install.firma"
rm -rf "$INST/.cache/chiavi-firma" "$INST/.cache/remotix-install-da-firmare"
cp "$M/remotix-aggiorna.service" "$M/remotix-aggiorna.timer" "$M/LEGGIMI" "$L/"

echo "== .deb del motore"
D=$L/deb; mkdir -p "$D/DEBIAN" "$D/usr/bin" "$D/usr/share/remotix-install" "$D/usr/lib/systemd/system" "$D/usr/share/doc/remotix-install"
install -m 755 "$L/remotix-install" "$D/usr/bin/"
install -m 644 "$L/remotix-install.firma" "$L/LEGGIMI" "$D/usr/share/remotix-install/"
install -m 644 "$L/remotix-aggiorna.service" "$L/remotix-aggiorna.timer" "$D/usr/lib/systemd/system/"
cat >"$D/DEBIAN/control" <<EOF
Package: remotix-install
Version: $V-$R
Architecture: amd64
Maintainer: nicfio <nicfio@gmail.com>
Section: admin
Priority: optional
Depends: systemd
Description: il motore d'installazione di REMOTIX
 Installa, aggiorna senza chiudere i desktop, disinstalla e certifica REMOTIX.
 Porta il timer degli aggiornamenti automatici, SPENTO: lo accende il motore
 all'installazione, col consenso (DECISIONI §10.12).
EOF
cat >"$D/DEBIAN/prerm" <<'EOF'
#!/bin/sh
# alla sola disinstallazione: il timer non resta acceso su un motore che se ne va
set -e
if [ "$1" = remove ] && [ -d /run/systemd/system ]; then
	systemctl disable --now remotix-aggiorna.timer >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 755 "$D/DEBIAN/prerm"
dpkg-deb --root-owner-group -Zxz --build "$D" "$U/remotix-install_${V}-${R}_amd64.deb" >/dev/null

echo "== .deb della chiave (remotix-archive-keyring)"
K=$L/keyring; KV=$(date -u +%Y.%m.%d)
mkdir -p "$K/DEBIAN" "$K/usr/share/keyrings"
install -m 644 "$CHIAVI/b/archivio.asc" "$K/usr/share/keyrings/remotix-archive-keyring.asc"
cat >"$K/DEBIAN/control" <<EOF
Package: remotix-archive-keyring
Version: $KV-$R
Architecture: all
Maintainer: nicfio <nicfio@gmail.com>
Section: misc
Priority: optional
Description: la chiave dell'archivio di REMOTIX (catena B)
 La chiave pubblica che firma l'archivio apt di REMOTIX, in
 /usr/share/keyrings/remotix-archive-keyring.asc: la nomina solo la sorgente
 di REMOTIX (Signed-By), mai trusted.gpg.d.  Aggiornandosi segue la rotazione
 della sottochiave.  ⚠ Fase 17 T8: chiave DI PROVA.
EOF
dpkg-deb --root-owner-group -Zxz --build "$K" "$U/remotix-archive-keyring_${KV}-${R}_all.deb" >/dev/null

echo "== .rpm del motore (fedora:44)"
P=$L/rpm; mkdir -p "$P/SOURCES" "$P/SPECS"
cp "$L/remotix-install" "$L/remotix-install.firma" "$L/remotix-aggiorna.service" "$L/remotix-aggiorna.timer" "$L/LEGGIMI" "$P/SOURCES/"
cp "$M/remotix-install.spec" "$P/SPECS/"
podman run --rm -v "$P:/lavoro:Z" registry.fedoraproject.org/fedora:44 sh -c "
	dnf -y -q install rpm-build systemd-rpm-macros >/dev/null 2>&1
	rpmbuild -bb --define '_topdir /lavoro' --define 'rx_versione $V' --define 'rx_rilascio $R' /lavoro/SPECS/remotix-install.spec" >"$U/rpmbuild.log" 2>&1 \
	|| { tail -20 "$U/rpmbuild.log"; exit 1; }
cp "$P"/RPMS/x86_64/remotix-install-*.rpm "$U/"

echo "== pacchetto Arch del motore"
A=$L/arch; mkdir -p "$A"
cp "$L/remotix-install" "$L/remotix-install.firma" "$L/remotix-aggiorna.service" "$L/remotix-aggiorna.timer" "$L/LEGGIMI" "$M/PKGBUILD" "$A/"
podman run --rm --userns=keep-id -v "$A:/pkg" -w /pkg -e HOME=/pkg -e RX_VERSIONE="$V" -e RX_RILASCIO="$R" \
	-e SOURCE_DATE_EPOCH="$(git -C "$ALBERO" log -1 --format=%ct)" localhost/remotix-costruzione-arch \
	makepkg -f --noconfirm --nodeps >"$U/makepkg.log" 2>&1 || { tail -20 "$U/makepkg.log"; exit 1; }
cp "$A"/remotix-install-*-x86_64.pkg.tar.zst "$U/"

cp "$L/remotix-install" "$L/remotix-install.firma" "$U/"
ls -l "$U"
