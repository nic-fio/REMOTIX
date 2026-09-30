#!/usr/bin/env bash
# pubblica.sh — l'ARCHIVIO firmato di REMOTIX, per le tre famiglie (fasi/17 §6.1, §6.5 punti 5-6,
# §6.6.10; tappa T8), dai pacchetti già costruiti.
#
#   pubblica.sh aggiungi <canale> <bersaglio> FILE…   un pacchetto nel suo posto (deb, rpm, pacman)
#   pubblica.sh catalogo <canale> [FILE [SOTTOCHIAVE]] il catalogo del canale, firmato (catena A)
#   pubblica.sh revoche  <sequenza> [ID=motivo …]      l'elenco delle sottochiavi revocate (radice)
#   pubblica.sh motore   FILE FILE.firma               il motore per lo script d'ingresso
#   pubblica.sh script                                 install.sh (installatore/install.sh), firmato (catena A, «script»)
#   pubblica.sh rigenera                               indici, firme (catena B), SBOM (R24)
#
#   canale: stabile · candidato.  bersaglio: debian13, ubuntu2604, fedora44, alma10, arch, …
#
# Com'è fatto (servito così com'è da un server HTTP qualunque):
#   deb/pool/<bersaglio>-<canale>/*.deb, deb/dists/<bersaglio>-<canale>/{InRelease,Release,Release.gpg}
#        Origin/Label «REMOTIX», Valid-Until a 60 giorni (un archivio «congelato» scade: va rifirmato)
#   rpm/<canale>/<bersaglio>/*.rpm (firmati) + repodata/ (repomd.xml.asc: repo_gpgcheck=1)
#   pacman/<canale>/x86_64/*.pkg.tar.zst(.sig) + remotix.db(.sig): il database ha la versione più
#        nuova di ogni pacchetto; le VECCHIE restano come file (pacman -U, il ritorno indietro R11)
#   catalogo/<canale>/catalogo.json(.firma), catalogo/revoche.json(.firma)       — catena A
#   motore/remotix-install(.firma), chiavi/ (le due chiavi pubbliche), sbom/<pacchetto>.spdx.json
# ⭐ Le versioni vecchie non si cancellano mai da qui: tornare indietro (R11) vuol dire che ci sono.
# ⛔ Le due catene hanno chiavi DIVERSE: catena A (ed25519, installatore/strumenti/chiavi-a) per il
#    catalogo e il motore; catena B (GPG) per pacchetti e metadati. Le private stanno in $CHIAVI,
#    FUORI dal deposito e fuori dalla cartella servita. ⚠ T8: sono chiavi DI PROVA (D11).
#
# Ambiente: ARCHIVIO (predefinito costruzione-uscita/archivio), CHIAVI
# (~/.local/share/remotix-chiavi-di-prova: a/ per la catena A, b/firma per la catena B, che ha
# SOLO la sottochiave di firma: la madre GPG sta in b/radice, «fuori linea»), SOTTOCHIAVE_A (A-2026).
set -euo pipefail
export LC_ALL=C   # le date di Release (Valid-Until) in inglese, come apt le legge
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
INST=$ALBERO/installatore
ARCHIVIO=${ARCHIVIO:-$ALBERO/costruzione-uscita/archivio}
CHIAVI=${CHIAVI:-$HOME/.local/share/remotix-chiavi-di-prova}
SUB=${SOTTOCHIAVE_A:-A-2026}
GB=$CHIAVI/b/firma
FPR=$(cat "$CHIAVI/b/archivio.impronta")
LAV=$ARCHIVIO/../.lavoro-archivio
mkdir -p "$ARCHIVIO" "$LAV"
export TMPDIR=$LAV

gpgb() { gpg --homedir "$GB" --batch --yes --pinentry-mode loopback --passphrase '' -u "$FPR" "$@"; }

# la catena A: lo strumento chiavi-a nel contenitore di Go (le chiavi passano da .cache, poi via)
firmaA() {  # firmaA <sottochiave> <oggetto> <file>
	rm -rf "$INST/.cache/chiavi-firma" "$INST/.cache/da-firmare"; mkdir -p "$INST/.cache/da-firmare"
	cp -a "$CHIAVI/a" "$INST/.cache/chiavi-firma"
	cp "$3" "$INST/.cache/da-firmare/oggetto"
	"$INST/costruisci.sh" go run ./strumenti/chiavi-a firma /src/.cache/chiavi-firma "$1" "$2" /src/.cache/da-firmare/oggetto "$(date -u +%F)" >/dev/null
	cp "$INST/.cache/da-firmare/oggetto.firma" "$3.firma"
	rm -rf "$INST/.cache/chiavi-firma" "$INST/.cache/da-firmare"
}

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

catalogo() {
	local canale=$1 f=${2:-$INST/catalogo/catalogo.json} sub=${3:-$SUB}
	mkdir -p "$ARCHIVIO/catalogo/$canale"
	cp "$f" "$ARCHIVIO/catalogo/$canale/catalogo.json"
	firmaA "$sub" catalogo "$ARCHIVIO/catalogo/$canale/catalogo.json"
	echo "   catalogo $canale: $(grep -m1 '"versione"' "$f" | tr -d ' ,') firmato con $sub"
}

revoche() {
	local seq=$1; shift
	rm -rf "$INST/.cache/chiavi-firma"; cp -a "$CHIAVI/a" "$INST/.cache/chiavi-firma"
	"$INST/costruisci.sh" go run ./strumenti/chiavi-a revoche /src/.cache/chiavi-firma "$seq" "$(date -u +%F)" /src/.cache/revoche.json "$@"
	mkdir -p "$ARCHIVIO/catalogo"
	mv "$INST/.cache/revoche.json" "$INST/.cache/revoche.json.firma" "$ARCHIVIO/catalogo/"
	rm -rf "$INST/.cache/chiavi-firma"
}

motore() {
	mkdir -p "$ARCHIVIO/motore"
	cp "$1" "$ARCHIVIO/motore/remotix-install"; cp "$2" "$ARCHIVIO/motore/remotix-install.firma"
}

# lo script d'ingresso (T9), firmato con la catena A come oggetto «script», alla radice dell'archivio
script() {
	cp "$INST/install.sh" "$ARCHIVIO/install.sh"
	firmaA "$SUB" script "$ARCHIVIO/install.sh"
	echo "   install.sh firmato con $SUB"
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
			-o APT::FTPArchive::Release::Description="REMOTIX, archivio $s (fase 17 T8: chiavi DI PROVA)" \
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
	cp "$INST/chiavi/radice-A.pub" "$ARCHIVIO/chiavi/radice-A.pub"
	cat >"$ARCHIVIO/chiavi/LEGGIMI" <<EOF
Le chiavi PUBBLICHE di REMOTIX — ⚠ fase 17 T8: chiavi DI PROVA, generate apposta, non proteggono
niente di vero (la custodia delle chiavi vere è la decisione D11).
  remotix-archivio.asc  catena B (GPG): i pacchetti e i metadati dell'archivio. Madre $FPR
                        (solo certificazione, fuori linea); firma una sottochiave con scadenza.
  radice-A.pub          catena A (ed25519): il catalogo e il motore; scritta dentro il motore.
Le due catene non si autorizzano a vicenda.
EOF
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
catalogo) catalogo "$@" ;;
revoche)  revoche "$@" ;;
motore)   motore "$@" ;;
script)   script ;;
rigenera)
	echo "== deb";    rigenera_deb
	echo "== rpm";    rigenera_rpm
	echo "== pacman"; rigenera_pacman
	echo "== chiavi"; rigenera_chiavi
	echo "== SBOM";   rigenera_sbom
	;;
*) sed -n '2,12p' "$0"; exit 2 ;;
esac
