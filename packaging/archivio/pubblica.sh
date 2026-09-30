#!/usr/bin/env bash
# pubblica.sh — l'ARCHIVIO firmato di REMOTIX, per le tre famiglie (fasi/17 §6.1, §6.5 punti 5-6,
# §6.6.10), dai pacchetti già costruiti. Lo chiama il comando di rilascio (packaging/rilascio.sh).
#
#   pubblica.sh aggiungi <canale> <bersaglio> FILE…   un pacchetto nel suo posto (deb, rpm, pacman)
#   pubblica.sh motore   FILE [FILE-GUI]               il motore (e la costruzione con la finestra) per
#                                                      install.sh, ognuno col suo .sha256 accanto
#   pubblica.sh script                                 install.sh alla radice, con lo sha256 dei due
#                                                      motori SCRITTO DENTRO, e install.sh.sha256
#   pubblica.sh rigenera                               indici e firme, SBOM (R24), licenze, SHA256SUMS
#
#   canale: stabile · candidato.  bersaglio: debian13, ubuntu2604, fedora44, alma10, arch, …
#
# Com'è fatto (servito così com'è da un server HTTP qualunque):
#   deb/pool/<bersaglio>-<canale>/*.deb, deb/dists/<bersaglio>-<canale>/{InRelease,Release,Release.gpg}
#        Origin/Label «REMOTIX», Valid-Until a 60 giorni (un archivio «congelato» scade: va rifirmato)
#   rpm/<canale>/<bersaglio>/*.rpm (firmati) + repodata/ (repomd.xml.asc: repo_gpgcheck=1)
#   pacman/<canale>/x86_64/*.pkg.tar.zst(.sig) + remotix.db(.sig): il database ha la versione più
#        nuova di ogni pacchetto; le VECCHIE restano come file (pacman -U, il ritorno indietro R11)
#   install.sh, install.sh.sha256, motore/remotix-install(-gui)(.sha256), chiavi/ (la chiave
#   pubblica), sbom/<pacchetto>.spdx.json, LICENZE-COMPONENTI.txt, SHA256SUMS
# ⭐ Le versioni vecchie non si cancellano mai da qui: tornare indietro (R11) vuol dire che ci sono.
# ⭐ UNA chiave sola (DECISIONI §10.21): quella che firma pacchetti e metadati, verificata dal gestore
#    di pacchetti. La privata sta in $CHIAVI, FUORI dal deposito e fuori dalla cartella servita.
#    ⚠ Fase 17: chiave DI PROVA (la vera, e dove si custodisce, con D10).
#
# Ambiente: ARCHIVIO (predefinito costruzione-uscita/archivio), CHIAVI
# (~/.local/share/remotix-chiavi-di-prova: b/firma è la cartella GPG con la sola sottochiave di
# firma; la madre GPG sta in b/radice, «fuori linea»).
set -euo pipefail
export LC_ALL=C   # le date di Release (Valid-Until) in inglese, come apt le legge
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
INST=$ALBERO/installatore
ARCHIVIO=${ARCHIVIO:-$ALBERO/costruzione-uscita/archivio}
CHIAVI=${CHIAVI:-$HOME/.local/share/remotix-chiavi-di-prova}
GB=$CHIAVI/b/firma
FPR=$(cat "$CHIAVI/b/archivio.impronta")
LAV=$ARCHIVIO/../.lavoro-archivio
mkdir -p "$ARCHIVIO" "$LAV"
export TMPDIR=$LAV

gpgb() { gpg --homedir "$GB" --batch --yes --pinentry-mode loopback --passphrase '' -u "$FPR" "$@"; }

aggiungi() {
	local canale=$1 bers=$2; shift 2
	case $canale in stabile|candidato) ;; *) echo "⛔ canale $canale"; exit 2;; esac
	for f in "$@"; do
		case $f in
		*.deb)         d=$ARCHIVIO/deb/pool/$bers-$canale ;;
		*.rpm)         d=$ARCHIVIO/rpm/$canale/$bers ;;
		*.pkg.tar.zst) d=$ARCHIVIO/pacman/$canale/x86_64 ;;
		*) echo "⛔ $f: non è un pacchetto"; exit 2 ;;
		esac
		mkdir -p "$d"
		if [ -e "$d/$(basename "$f")" ] && ! cmp -s "$f" "$d/$(basename "$f")"; then
			# ⛔ un pacchetto pubblicato non si cambia sotto lo stesso nome: si fa una revisione nuova
			case $f in *.rpm) ;; *) echo "⛔ $(basename "$f") c'è già, diverso: serve una revisione nuova"; exit 1;; esac
		fi
		cp -n "$f" "$d/" && echo "   + $d/$(basename "$f")"
	done
}

motore() {
	mkdir -p "$ARCHIVIO/motore"
	for f in "$@"; do
		n=$(basename "$f")
		case $n in remotix-install | remotix-install-gui) ;; *) echo "⛔ $n: il motore si chiama remotix-install(-gui)"; exit 2 ;; esac
		cp "$f" "$ARCHIVIO/motore/$n"
		(cd "$ARCHIVIO/motore" && sha256sum "$n" >"$n.sha256")
		echo "   motore/$n $(cut -c1-16 "$ARCHIVIO/motore/$n.sha256")…"
	done
}

# lo script d'ingresso: gli sha256 dei due motori SCRITTI DENTRO (l'amministratore verifica lo script
# con lo sha256 pubblicato sul sito, e lo script verifica il motore con quello che porta)
script() {
	local s g
	s=$(cut -d' ' -f1 "$ARCHIVIO/motore/remotix-install.sha256")
	g=$(cut -d' ' -f1 "$ARCHIVIO/motore/remotix-install-gui.sha256" 2>/dev/null || true)
	sed -e "s/^SHA256_MOTORE=''\$/SHA256_MOTORE='$s'/" -e "s/^SHA256_MOTORE_GUI=''\$/SHA256_MOTORE_GUI='$g'/" \
		"$INST/install.sh" >"$ARCHIVIO/install.sh"
	grep -q "^SHA256_MOTORE='$s'\$" "$ARCHIVIO/install.sh" || { echo "⛔ install.sh: la riga SHA256_MOTORE non c'è"; exit 1; }
	(cd "$ARCHIVIO" && sha256sum install.sh >install.sh.sha256)
	echo "   install.sh $(cut -d' ' -f1 "$ARCHIVIO/install.sh.sha256") (da pubblicare sul sito)"
}

rigenera_deb() {
	[ -d "$ARCHIVIO/deb/pool" ] || return 0
	cd "$ARCHIVIO/deb"
	for s in $(ls pool); do
		local d=dists/$s b=dists/$s/main/binary-amd64
		rm -rf "$d"; mkdir -p "$b"
		apt-ftparchive packages "pool/$s" >"$b/Packages"
		gzip -9nkf "$b/Packages"
		apt-ftparchive -o APT::FTPArchive::Release::Origin=REMOTIX -o APT::FTPArchive::Release::Label=REMOTIX \
			-o APT::FTPArchive::Release::Suite="$s" -o APT::FTPArchive::Release::Codename="$s" \
			-o APT::FTPArchive::Release::Architectures=amd64 -o APT::FTPArchive::Release::Components=main \
			-o APT::FTPArchive::Release::Description="REMOTIX, archivio $s (fase 17: chiave DI PROVA)" \
			release "$d" >"$LAV/Release"
		# Valid-Until: un archivio non rifirmato da 60 giorni apt lo rifiuta (difesa dal «congelamento»)
		awk -v v="Valid-Until: $(date -u -d '+60 days' '+%a, %d %b %Y %H:%M:%S UTC')" '{print} /^Date:/{print v}' "$LAV/Release" >"$d/Release"
		gpgb --clearsign -o "$d/InRelease" "$d/Release"
		gpgb --armor --detach-sign -o "$d/Release.gpg" "$d/Release"
		echo "   deb $s: $(grep -c '^Package:' "$b/Packages") pacchetti, InRelease firmato"
	done
	cd - >/dev/null
}

rigenera_rpm() {
	[ -d "$ARCHIVIO/rpm" ] || return 0
	rm -rf "$LAV/gnupg-b"; cp -a "$GB" "$LAV/gnupg-b"; rm -f "$LAV/gnupg-b"/S.* "$LAV/gnupg-b"/*.lock
	mkdir -p "$LAV/sbom-rpm"
	podman run --rm -v "$ARCHIVIO/rpm:/rpm:Z" -v "$LAV/gnupg-b:/g:Z" -v "$LAV/sbom-rpm:/sbom:Z" -e FPR="$FPR" \
		registry.fedoraproject.org/fedora:44 sh -c '
		set -e
		dnf -y -q install createrepo_c rpm-sign gnupg2 cpio >/dev/null 2>&1
		export GNUPGHOME=/g; chmod 700 /g
		for d in /rpm/*/*/; do
			for f in "$d"*.rpm; do
				rpmsign --addsign --define "_gpg_name $FPR" "$f" >/dev/null 2>&1 || { echo "⛔ rpmsign $f"; rpmsign --addsign --define "_gpg_name $FPR" "$f"; exit 1; }
				n=$(rpm -qp --qf "%{NAME}" "$f" 2>/dev/null)
				if [ "$n" = remotix ]; then
					b=$(basename "$f")
					rpm -qp --qf "%{NAME}\n%{VERSION}-%{RELEASE}\n" "$f" >"/sbom/$b.nv" 2>/dev/null
					rpm -qp --provides "$f" 2>/dev/null | grep bundled >"/sbom/$b.bundled" || true
					rpm -qp --requires "$f" 2>/dev/null >"/sbom/$b.richieste" || true
					rpm2cpio "$f" | cpio -i --quiet --to-stdout ./usr/share/remotix/incorporate.json >"/sbom/$b.incorporate" 2>/dev/null || true
				fi
			done
			rm -rf "$d/repodata"
			createrepo_c --quiet "$d"
			gpg --batch --yes -u "$FPR" --armor --detach-sign -o "$d/repodata/repomd.xml.asc" "$d/repodata/repomd.xml"
			echo "   rpm $d: $(ls "$d"*.rpm | wc -l) pacchetti firmati, repomd.xml.asc"
		done' | sed "s#/rpm/#$ARCHIVIO/rpm/#"
}

rigenera_pacman() {
	[ -d "$ARCHIVIO/pacman" ] || return 0
	for d in "$ARCHIVIO"/pacman/*/x86_64; do
		for f in "$d"/*.pkg.tar.zst; do
			[ -f "$f.sig" ] || gpgb --detach-sign --no-armor -o "$f.sig" "$f"
		done
		rm -f "$d"/remotix.db* "$d"/remotix.files*
		# l'elenco dei file (anche le versioni vecchie, che il database non ha): il ritorno indietro
		(cd "$d" && ls *.pkg.tar.zst) >"$d/remotix.versioni"
		podman run --rm -v "$d:/repo:Z" -w /repo docker.io/library/archlinux:latest sh -c \
			'for f in $(ls *.pkg.tar.zst | sort -V); do repo-add -q remotix.db.tar.gz "$f" || exit 1; done' >/dev/null
		for x in db files; do
			gpgb --detach-sign --no-armor -o "$d/remotix.$x.tar.gz.sig" "$d/remotix.$x.tar.gz"
			rm -f "$d/remotix.$x" "$d/remotix.$x.sig"
			cp "$d/remotix.$x.tar.gz" "$d/remotix.$x"     # copie, non collegamenti: un server qualunque le serve
			cp "$d/remotix.$x.tar.gz.sig" "$d/remotix.$x.sig"
		done
		echo "   pacman $d: $(ls "$d"/*.pkg.tar.zst | wc -l) pacchetti firmati, remotix.db firmato"
	done
}

rigenera_chiavi() {
	mkdir -p "$ARCHIVIO/chiavi"
	cp "$CHIAVI/b/archivio.asc" "$ARCHIVIO/chiavi/remotix-archivio.asc"
	rm -f "$ARCHIVIO/chiavi/radice-A.pub"
	cat >"$ARCHIVIO/chiavi/LEGGIMI" <<EOF
La chiave PUBBLICA di REMOTIX — l'unica (DECISIONI §10.21): firma i pacchetti e i metadati
dell'archivio, e la verifica il gestore di pacchetti. ⚠ Fase 17: chiave DI PROVA, generata apposta,
non protegge niente di vero (la vera, e dove si custodisce, con D10).
  remotix-archivio.asc  GPG, impronta $FPR
Lo script d'ingresso (install.sh) non è firmato: si verifica col suo sha256, pubblicato sul sito di
REMOTIX in HTTPS; lui verifica il motore con lo sha256 che porta scritto dentro.
EOF
}

# il file delle licenze dei componenti (DECISIONI §10.22): da SBOM e dal vendor/ del motore
rigenera_licenze() {
	# LICENZA_GO: la licenza di Go presa dal contenitore di costruzione (la passa rilascio.sh)
	python3 "$QUI/licenze.py" "$ARCHIVIO" "$INST" "${LICENZA_GO:-}" >"$ARCHIVIO/LICENZE-COMPONENTI.txt"
	echo "   LICENZE-COMPONENTI.txt: $(grep -c '^== ' "$ARCHIVIO/LICENZE-COMPONENTI.txt") componenti"
}

# SHA256SUMS: ogni file pubblicato (fuori dagli indici, che hanno le loro firme)
rigenera_somme() {
	(cd "$ARCHIVIO" && find . -type f ! -name SHA256SUMS ! -path './deb/dists/*' ! -path './*/repodata/*' \
		! -name 'remotix.db*' ! -name 'remotix.files*' -printf '%P\n' | LC_ALL=C sort | xargs -d '\n' sha256sum >SHA256SUMS)
	echo "   SHA256SUMS: $(wc -l <"$ARCHIVIO/SHA256SUMS") file"
}

# SBOM (R24): uno per ogni pacchetto del PRODOTTO, SPDX 2.3; ngtcp2 e nghttp3 con la versione
# COLLEGATA nel binario (usr/share/remotix/incorporate.json, scritto da pkg-config nel contenitore di
# costruzione), confrontata con quella che il pacchetto dichiara (Static-Built-Using, bundled()).
rigenera_sbom() {
	mkdir -p "$ARCHIVIO/sbom" "$LAV/sbom"
	local f b
	for f in "$ARCHIVIO"/deb/pool/*/remotix_*.deb; do
		[ -e "$f" ] || continue
		b=$(basename "$f")
		{ dpkg-deb -f "$f" Package; dpkg-deb -f "$f" Version; } >"$LAV/sbom/$b.nv"
		dpkg-deb -f "$f" Static-Built-Using >"$LAV/sbom/$b.bundled"
		dpkg-deb -f "$f" Depends >"$LAV/sbom/$b.richieste"
		dpkg-deb --fsys-tarfile "$f" | tar -xO ./usr/share/remotix/incorporate.json >"$LAV/sbom/$b.incorporate" 2>/dev/null || true
		echo "$f" >"$LAV/sbom/$b.file"
	done
	for f in "$LAV"/sbom-rpm/*.nv; do
		[ -e "$f" ] || continue
		b=$(basename "$f" .nv)
		cp "$LAV/sbom-rpm/$b".* "$LAV/sbom/"
		find "$ARCHIVIO/rpm" -name "$b" | head -1 >"$LAV/sbom/$b.file"
	done
	for f in "$ARCHIVIO"/pacman/*/x86_64/remotix-[0-9]*.pkg.tar.zst; do
		[ -e "$f" ] || continue
		b=$(basename "$f")
		tar --zstd -xOf "$f" .PKGINFO >"$LAV/sbom/$b.pkginfo"
		{ echo remotix; sed -n 's/^pkgver = //p' "$LAV/sbom/$b.pkginfo"; } >"$LAV/sbom/$b.nv"
		grep '^depend = ' "$LAV/sbom/$b.pkginfo" | sed 's/^depend = //' >"$LAV/sbom/$b.richieste"
		: >"$LAV/sbom/$b.bundled"
		tar --zstd -xOf "$f" usr/share/remotix/incorporate.json >"$LAV/sbom/$b.incorporate" 2>/dev/null || true
		echo "$f" >"$LAV/sbom/$b.file"
	done
	python3 "$QUI/sbom.py" "$LAV/sbom" "$ARCHIVIO/sbom"
}

cmd=${1:-}; shift || true
case $cmd in
aggiungi) aggiungi "$@" ;;
motore)   motore "$@" ;;
script)   script ;;
rigenera)
	echo "== deb";     rigenera_deb
	echo "== rpm";     rigenera_rpm
	echo "== pacman";  rigenera_pacman
	echo "== chiavi";  rigenera_chiavi
	echo "== SBOM";    rigenera_sbom
	echo "== licenze"; rigenera_licenze
	echo "== somme";   rigenera_somme
	;;
*) sed -n '2,12p' "$0"; exit 2 ;;
esac
