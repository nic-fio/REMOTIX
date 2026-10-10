#!/usr/bin/env bash
# rilascio.sh — IL comando di rilascio di REMOTIX: a ogni versione, uno solo.
#
#     packaging/rilascio.sh X.Y.Z-R          per esempio  packaging/rilascio.sh 0.17.0-7
#
# X.Y.Z è la versione di REMOTIX, R la revisione del pacchetto (una ricostruzione: 0.17.0-7 → 0.17.0-8).
# La stessa versione va a tutto: remotix e remotix-install (il motore, che la dice con `version`).
# Il prodotto si consegna come UN file, remotix-X.Y.Z-R.run (il pacchetto unico, DECISIONI §10.36):
# niente archivio da aggiungere al sistema, niente chiavi. Che cosa fa, in ordine, e si ferma al
# primo errore:
#   1. l'albero è quello di un commit (niente modifiche non committate in src/, packaging/,
#      installatore/, banchi/rcp/): i pacchetti dicono da quale commit vengono;
#   2. il MOTORE: le prove (installatore/costruisci.sh prove, tutte verdi), poi la costruzione
#      statica con la versione del rilascio; il catalogo sta dentro (DECISIONI §10.21);
#   3. i pacchetti del PRODOTTO per le tre famiglie: .deb (Debian 13, Ubuntu 26.04:
#      src/costruzione/costruisci-deb.sh), .rpm (Fedora 44, Alma 10, Tumbleweed, Leap 16:
#      packaging/rpm/costruisci-rpm.sh), Arch (packaging/arch/costruisci.sh);
#   4. i pacchetti del MOTORE (packaging/motore/pacchetti-motore.sh): resta sulla macchina
#      (status, uninstall, post-upgrade);
#   5. il .RUN: l'intestazione installatore/run.sh (con la versione e lo sha256 del carico scritti
#      dentro) e sotto il tar.gz con il motore e packages/<bersaglio>/ (prodotto + motore per ogni
#      distribuzione); accanto il suo .sha256, da pubblicare sul sito.
#
# Ambiente:
#   BERSAGLI   quali (predefinito: debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch)
#   USCITA     dove va il .run (predefinito costruzione-uscita/rilasci)
#   RX_SPORCO=1  solo per prova: accetta un albero con modifiche non committate (i pacchetti lo dicono)
# ⚠ Niente /tmp: sul portatile è quasi pieno; tutto sotto costruzione-uscita/.
# ⏳ Le licenze dei componenti di terzi (THIRD-PARTY-LICENSES) le faceva l'archivio
#    (archivio/sbom.py, archivio/licenze.py): vanno rimesse nel .run (DECISIONI §10.36, punto aperto).
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/.." && pwd)
INST=$ALBERO/installatore

VERSIONE=${1:-}
if ! [[ $VERSIONE =~ ^([0-9]+\.[0-9]+\.[0-9]+)-([0-9]+)$ ]]; then
	sed -n '2,6p' "$0"; exit 2
fi
V=${BASH_REMATCH[1]} R=${BASH_REMATCH[2]}
BERSAGLI=${BERSAGLI:-debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch}
USCITA=${USCITA:-$ALBERO/costruzione-uscita/rilasci}
LAV=$ALBERO/costruzione-uscita/rilascio-$VERSIONE
# i contenitori (rpm) lasciano file di un altro uid dello spazio utente: si tolgono da lì dentro
podman unshare rm -rf "$LAV"; mkdir -p "$LAV/tmp"
export TMPDIR=$LAV/tmp
REG=$LAV/rilascio.log
passo() { printf '\n== %s\n' "$*" | tee -a "$REG"; }
RUN=$USCITA/remotix-$VERSIONE.run

passo "1. l'albero ($VERSIONE, bersagli: $BERSAGLI)"
COMMIT=$(git -C "$ALBERO" rev-parse HEAD)
SPORCO=$(git -C "$ALBERO" status --porcelain -- src packaging installatore banchi/rcp)
if [ -n "$SPORCO" ]; then
	[ "${RX_SPORCO:-}" = 1 ] || { echo "⛔ modifiche non committate:"; echo "$SPORCO"; exit 1; }
	echo "⚠ RX_SPORCO=1: albero con modifiche non committate (solo per prova)" | tee -a "$REG"
fi
echo "commit $COMMIT" | tee -a "$REG"
# ⛔ la stessa versione non si pubblica due volte con contenuto diverso: serve una revisione nuova
[ ! -e "$RUN" ] || { echo "⛔ $RUN c'è già: serve una revisione nuova"; exit 1; }

passo "2. il motore: le prove e la costruzione ($V)"
"$INST/costruisci.sh" prove >"$LAV/prove-motore.log" 2>&1 || { tail -30 "$LAV/prove-motore.log"; echo "⛔ le prove del motore"; exit 1; }
if grep -qE '^(FAIL|gofmt:)' "$LAV/prove-motore.log"; then tail -30 "$LAV/prove-motore.log"; echo "⛔ le prove del motore"; exit 1; fi
grep -E '^ok ' "$LAV/prove-motore.log" | tee -a "$REG"
RX_VERSIONE=$V "$INST/costruisci.sh" >>"$REG" 2>&1
mkdir -p "$LAV/motore-bin"
cp "$INST/uscita/remotix-install" "$LAV/motore-bin/"
[ "$("$LAV/motore-bin/remotix-install" version | awk '{print $1}')" = "$V" ] || { echo "⛔ il motore non dice $V"; exit 1; }
"$LAV/motore-bin/remotix-install" catalog | head -1 | tee -a "$REG"

passo "3. i pacchetti del prodotto"
P=$LAV/prodotto
deb=() rpm=() arch=0
for b in $BERSAGLI; do
	case $b in
	debian13 | ubuntu2604) deb+=("$b") ;;
	fedora44 | alma10 | tumbleweed | leap16) rpm+=("$b") ;;
	arch) arch=1 ;;
	*) echo "⛔ bersaglio sconosciuto: $b"; exit 2 ;;
	esac
done
if [ ${#deb[@]} -gt 0 ]; then
	USCITA=$P CACHE=$LAV/cache RX_VERSIONE=$V RX_REVISIONE=$R "$ALBERO/src/costruzione/costruisci-deb.sh" "${deb[@]}" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ .deb"; exit 1; }
fi
if [ ${#rpm[@]} -gt 0 ]; then
	USCITA=$P CACHE=$LAV/cache RX_VERSIONE=$V RX_REVISIONE=$R "$ALBERO/packaging/rpm/costruisci-rpm.sh" "${rpm[@]}" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ .rpm"; exit 1; }
	for b in "${rpm[@]}"; do grep -q ' pacchetto=si ' "$P/rpm/$b/esito.txt" || { cat "$P/rpm/$b/esito.txt"; exit 1; }; done
fi
if [ $arch = 1 ]; then
	USCITA=$P/arch RX_VERSIONE=$V RX_REVISIONE=$R "$ALBERO/packaging/arch/costruisci.sh" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ Arch"; exit 1; }
fi
find "$P" -maxdepth 3 \( -name 'remotix_*.deb' -o -name 'remotix-*.rpm' -o -name 'remotix-*.pkg.tar.zst' \) ! -name '*.src.rpm' ! -name '*-debug*' ! -path '*/.lavoro/*' ! -name 'seconda-*' -printf '   %P\n' | sort | tee -a "$REG"

passo "4. i pacchetti del motore"
M=$LAV/motore
RX_VERSIONE=$V RX_REVISIONE=$R MOTORE=$LAV/motore-bin/remotix-install \
	"$ALBERO/packaging/motore/pacchetti-motore.sh" "$M" >>"$REG" 2>&1 || { tail -20 "$REG"; exit 1; }

passo "5. il .run ($RUN)"
C=$LAV/carico
mkdir -p "$C/packages"
cp "$LAV/motore-bin/remotix-install" "$C/"
for b in "${deb[@]}"; do
	mkdir -p "$C/packages/$b"
	cp "$P/deb-$b"/remotix_*.deb "$M/remotix-install_${V}-${R}_amd64.deb" "$C/packages/$b/"
done
for b in "${rpm[@]}"; do
	mkdir -p "$C/packages/$b"
	cp $(ls "$P/rpm/$b"/*.rpm | grep -vE '\.src\.rpm$|-debug(info|source)-') "$M"/remotix-install-"$V"-"$R".x86_64.rpm "$C/packages/$b/"
done
if [ $arch = 1 ]; then
	mkdir -p "$C/packages/arch"
	cp "$P/arch"/remotix-"$V"-"$R"-x86_64.pkg.tar.zst "$M"/remotix-install-"$V"-"$R"-x86_64.pkg.tar.zst "$C/packages/arch/"
fi
(cd "$C" && find . -type f | sort | sed 's|^\./|   |') | tee -a "$REG"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime="@$(git -C "$ALBERO" log -1 --format=%ct)" \
	-C "$C" -cf - . | gzip -n -9 >"$LAV/carico.tar.gz"
SHA_CARICO=$(sha256sum "$LAV/carico.tar.gz" | cut -d' ' -f1)
mkdir -p "$USCITA"
sed -e "s/^VERSIONE=''\$/VERSIONE='$VERSIONE'/" -e "s/^PAYLOAD_SHA256=''\$/PAYLOAD_SHA256='$SHA_CARICO'/" \
	"$INST/run.sh" >"$RUN.parziale"
grep -q "^PAYLOAD_SHA256='$SHA_CARICO'\$" "$RUN.parziale" || { echo "⛔ l'intestazione non ha preso lo sha256"; exit 1; }
cat "$LAV/carico.tar.gz" >>"$RUN.parziale"
mv "$RUN.parziale" "$RUN"
(cd "$USCITA" && sha256sum "$(basename "$RUN")" >"$(basename "$RUN").sha256")
sh "$RUN" version | tee -a "$REG"

passo "6. il riassunto"
printf '%s %s commit %s bersagli %s sha256 %s\n' "$VERSIONE" "$(date -u +%FT%TZ)" "$COMMIT" \
	"$(echo $BERSAGLI | tr ' ' ',')" "$(cut -d' ' -f1 "$RUN.sha256")" >>"$USCITA/RELEASES.txt"
cat <<EOF | tee -a "$REG"
REMOTIX $VERSIONE — pronto: $RUN ($(du -h "$RUN" | cut -f1))
  sha256 (da pubblicare sul sito, in HTTPS, accanto al file):
      $(cut -d' ' -f1 "$RUN.sha256")
  si installa con:  sudo sh $(basename "$RUN")
  il giornale del rilascio: $REG
EOF
