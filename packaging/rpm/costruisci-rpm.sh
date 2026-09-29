#!/usr/bin/env bash
# costruisci-rpm.sh — il pacchetto .rpm di REMOTIX, dentro il contenitore di ogni bersaglio.
#
#     packaging/rpm/costruisci-rpm.sh                  # fedora44 alma10 tumbleweed leap16
#     packaging/rpm/costruisci-rpm.sh fedora44         # uno solo
#
# Per ogni bersaglio (`fasi/17-l-installatore.md` §6.1-§6.2, T3):
#   1. l'immagine `localhost/remotix-costruzione-<bersaglio>` di src/costruzione/
#      (la fa `src/costruzione/costruisci-tutti.sh`; qui si usa se c'e', si
#      costruisce se manca): dentro ci sono gia' ngtcp2/nghttp3 statiche;
#   2. l'archivio dei sorgenti dall'albero di lavoro (src/, banchi/rcp/,
#      packaging/rpm/) — anche con modifiche non ancora nel deposito;
#   3. nel contenitore: rpm-build e rpmlint dal gestore della distribuzione,
#      `rpmbuild -ba`, poi rpmlint sui pacchetti e sullo spec;
#   4. in $USCITA/rpm/<bersaglio>/: i .rpm, rpmbuild.log, rpmlint.txt,
#      richieste.txt (Requires, automatiche e scritte), file.txt, esito.txt;
#      e i due controlli piccoli di R13/R14 (lista nera dei file del banco,
#      opzioni di banco nell'unita').
#
# ⚠ Niente /tmp: sul portatile e' quasi pieno (come costruisci-tutti.sh).
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
CACHE=${CACHE:-$USCITA/.lavoro}
TUTTI=(fedora44 alma10 tumbleweed leap16)
VER=$(awk '/^Version:/ { print $2 }' "$QUI/remotix.spec")

command -v podman >/dev/null 2>&1 || { echo "⛔ podman non c'e'"; exit 2; }
mkdir -p "$CACHE/tmp" "$USCITA/rpm"
export TMPDIR="$CACHE/tmp"
if [ $# -eq 0 ] || [ "$1" = tutti ]; then set -- "${TUTTI[@]}"; fi

# ⛔ R14 in piccolo: niente del banco nel pacchetto (§6.4)
LISTA_NERA='provisiona|sudoers|gpu-udev|riavvia-|ld\.so\.conf|/prova|banchi|\.py$|Contenitore|costruisci'
# ⛔ R13 in piccolo: l'unita' non passa opzioni di banco (§4.5)
OPZIONI_BANCO='--rilievo|--comando-socket|--audio-prova|--parlantina|--sblocca'

costruisci_uno()
{
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$USCITA/rpm/$1" lav="$CACHE/rpm-$1"
	local nota=""
	rm -rf "$u" "$lav"; mkdir -p "$u" "$lav"/{SOURCES,SPECS}

	if ! podman image exists "$imm"; then
		echo "== $b: l'immagine non c'e', la costruisco"
		podman build -t "$imm" -f "$ALBERO/src/costruzione/Contenitore.$b" "$ALBERO/src/costruzione" \
			>"$u/immagine.log" 2>&1 || { echo "$b pacchetto=NO immagine=NO" | tee "$u/esito.txt"; return 1; }
	fi

	echo "== $b: sorgenti"
	# ⛔ firewalld scarta un servizio che non e' XML ben fatto, in silenzio per
	#    chi installa (`[M]` 29 set: `--` dentro un commento).
	python3 -c 'import sys, xml.dom.minidom; xml.dom.minidom.parse(sys.argv[1])' "$QUI/remotix-firewalld.xml" \
		|| { echo "$b pacchetto=NO remotix-firewalld.xml non e' XML valido" | tee "$u/esito.txt"; return 1; }
	tar -C "$ALBERO" --transform "s,^,remotix-$VER/," \
		--exclude='*.o' --exclude='src/remotix' --exclude='*-client-protocol.h' --exclude='*-protocol.c' \
		-czf "$lav/SOURCES/remotix-$VER.tar.gz" src banchi/rcp packaging/rpm
	cp "$QUI/remotix.spec" "$lav/SPECS/"

	echo "== $b: rpmbuild (log in $u/rpmbuild.log)"
	podman run --rm -v "$lav:/lavoro" "$imm" sh -c '
		if command -v dnf >/dev/null; then
			dnf -y -q install --setopt=install_weak_deps=False rpm-build rpmlint systemd-rpm-macros cpio >/dev/null 2>&1
		else
			zypper -n -q install --no-recommends --force-resolution rpm-build rpmlint systemd-rpm-macros cpio >/dev/null 2>&1
		fi
		rpm -q rpm-build rpmlint | sed "s/^/strumenti: /"
		rpm --eval "dist=%{?dist} fedora=%{?fedora} rhel=%{?rhel} suse_version=%{?suse_version} pamvendor=%{?_pam_vendordir}"
		rpmbuild -ba --define "_topdir /lavoro" /lavoro/SPECS/remotix.spec 2>&1
		echo "rpmbuild-esito=$?"
		ls /lavoro/RPMS/*/*.rpm >/dev/null 2>&1 || exit 1
		rpmlint /lavoro/SPECS/remotix.spec /lavoro/RPMS/*/*.rpm /lavoro/SRPMS/*.rpm >/lavoro/rpmlint.txt 2>&1
		p=$(ls /lavoro/RPMS/x86_64/remotix-[0-9]*.rpm)
		{ echo "## Requires (automatiche + scritte)"; rpm -qpR "$p"
		  echo "## Recommends"; rpm -qp --recommends "$p"
		  echo "## Provides"; rpm -qp --provides "$p"; } >/lavoro/richieste.txt
		rpm -qplv "$p" >/lavoro/file.txt
		rpm -qp --scripts "$p" >/lavoro/scriptlet.txt
		rm -rf /lavoro/estratto; mkdir /lavoro/estratto; cd /lavoro/estratto
		rpm2cpio "$p" | cpio -idm --quiet
		ldd usr/libexec/remotix/remotix >/lavoro/ldd.txt 2>&1
		# R13: la frase della funzione di banco NON nel binario del pacchetto, e SI
		# in un rcp.o con BANCO_ACCESO 1 (il controllo positivo: senza, «non
		# trovata» potrebbe voler dire «non so cercare») — come la linea .deb.
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
		echo "$b pacchetto=NO (vedi rpmbuild.log)" | tee "$u/esito.txt"
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
printf '\n== riassunto (%s/rpm)\n' "$USCITA"
for b in "$@"; do cat "$USCITA/rpm/$b/esito.txt" 2>/dev/null || echo "$b (nessun esito)"; done
exit $stato
