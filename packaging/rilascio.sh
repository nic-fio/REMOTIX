#!/usr/bin/env bash
# rilascio.sh — IL comando di rilascio di REMOTIX (DECISIONI §10.23): a ogni versione, uno solo.
#
#     packaging/rilascio.sh X.Y.Z-R          per esempio  packaging/rilascio.sh 0.17.0-7
#
# X.Y.Z è la versione di REMOTIX, R la revisione del pacchetto (una ricostruzione: 0.17.0-7 → 0.17.0-8).
# La stessa versione va a tutto: remotix, remotix-install (il motore, che la dice con `versione`),
# remotix-archive-keyring. Che cosa fa, in ordine, e si ferma al primo errore:
#   1. l'albero è quello di un commit (niente modifiche non committate in src/, packaging/,
#      installatore/, banchi/rcp/): i pacchetti dicono da quale commit vengono;
#   2. il MOTORE: le prove (installatore/costruisci.sh prove, tutte verdi), poi la costruzione
#      statica con la versione del rilascio (la finestra è stata tolta: DECISIONI §10.31); il
#      catalogo sta dentro (DECISIONI §10.21);
#   3. i pacchetti del PRODOTTO per le tre famiglie, con gli script che ci sono: .deb (Debian 13,
#      Ubuntu 26.04: src/costruzione/costruisci-deb.sh), .rpm (Fedora 44, Alma 10, Tumbleweed, Leap 16:
#      packaging/rpm/costruisci-rpm.sh), Arch (packaging/arch/costruisci.sh);
#   4. i pacchetti del MOTORE e della CHIAVE (packaging/archivio/pacchetti-motore.sh);
#   5. l'ARCHIVIO (packaging/archivio/pubblica.sh): i pacchetti al loro posto, firmati con l'UNICA
#      chiave (quella DI PROVA in .chiavi/ del progetto, ignorata da git finché D10 non dà la vera);
#      il motore col suo sha256; install.sh con lo sha256 del motore scritti dentro, e il suo
#      sha256; indici e firme, SBOM, il file delle licenze dei componenti, SHA256SUMS;
#   6. il riassunto: la riga per RILASCI.txt dell'archivio, lo sha256 di install.sh da pubblicare
#      sul sito, e il comando per caricare l'archivio (D10 aperta: l'indirizzo è un segnaposto).
#
# La cartella dell'archivio ($ARCHIVIO, predefinita costruzione-uscita/archivio) CRESCE a ogni
# rilascio: le versioni vecchie restano (il ritorno indietro coi comandi del gestore, R11). È pronta
# da caricare così com'è.
#
# Ambiente:
#   BERSAGLI   quali (predefinito: debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch)
#   CANALE     stabile (predefinito) · candidato
#   ARCHIVIO   la cartella dell'archivio;  CHIAVI  la cartella delle chiavi (la privata, fuori dal deposito)
#   RX_SPORCO=1  solo per prova: accetta un albero con modifiche non committate (i pacchetti lo dicono)
# ⚠ Niente /tmp: sul portatile è quasi pieno; tutto sotto costruzione-uscita/.
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
CANALE=${CANALE:-stabile}
export ARCHIVIO=${ARCHIVIO:-$ALBERO/costruzione-uscita/archivio}
export CHIAVI=${CHIAVI:-$(dirname "$(git -C "$(dirname "$0")" rev-parse --path-format=absolute --git-common-dir)")/.chiavi}
# D10 aperta: dove si carica l'archivio (il VPS). Quando c'è, qui l'indirizzo.
DESTINAZIONE=${DESTINAZIONE:-'<D10: indirizzo del VPS, per esempio remotix@archivio.example:/srv/remotix/>'}
LAV=$ALBERO/costruzione-uscita/rilascio-$VERSIONE
# i contenitori (rpm) lasciano file di un altro uid dello spazio utente: si tolgono da lì dentro
podman unshare rm -rf "$LAV"; mkdir -p "$LAV/tmp"
export TMPDIR=$LAV/tmp
REG=$LAV/rilascio.log
passo() { printf '\n== %s\n' "$*" | tee -a "$REG"; }
case $CANALE in stabile | candidato) ;; *) echo "⛔ canale $CANALE"; exit 2 ;; esac
[ -r "$CHIAVI/b/archivio.impronta" ] || { echo "⛔ la chiave dell'archivio non c'è in $CHIAVI/b"; exit 1; }

passo "1. l'albero ($VERSIONE, canale $CANALE, bersagli: $BERSAGLI)"
COMMIT=$(git -C "$ALBERO" rev-parse HEAD)
SPORCO=$(git -C "$ALBERO" status --porcelain -- src packaging installatore banchi/rcp)
if [ -n "$SPORCO" ]; then
	[ "${RX_SPORCO:-}" = 1 ] || { echo "⛔ modifiche non committate:"; echo "$SPORCO"; exit 1; }
	echo "⚠ RX_SPORCO=1: albero con modifiche non committate (solo per prova)" | tee -a "$REG"
fi
echo "commit $COMMIT" | tee -a "$REG"
# ⛔ la stessa versione non si pubblica due volte con contenuto diverso (pubblica.sh lo rifiuta
#    pacchetto per pacchetto); qui ci si ferma prima di costruire
if [ -e "$ARCHIVIO/RILASCI.txt" ] && grep -q "^$VERSIONE " "$ARCHIVIO/RILASCI.txt"; then
	echo "⛔ $VERSIONE è già nell'archivio (RILASCI.txt): serve una revisione nuova"; exit 1
fi

passo "2. il motore: le prove e la costruzione ($V)"
"$INST/costruisci.sh" prove >"$LAV/prove-motore.log" 2>&1 || { tail -30 "$LAV/prove-motore.log"; echo "⛔ le prove del motore"; exit 1; }
if grep -qE '^(FAIL|gofmt:)' "$LAV/prove-motore.log"; then tail -30 "$LAV/prove-motore.log"; echo "⛔ le prove del motore"; exit 1; fi
grep -E '^ok ' "$LAV/prove-motore.log" | tee -a "$REG"
RX_VERSIONE=$V "$INST/costruisci.sh" >>"$REG" 2>&1
mkdir -p "$LAV/motore-bin"
cp "$INST/uscita/remotix-install" "$LAV/motore-bin/"
[ "$("$LAV/motore-bin/remotix-install" versione | awk '{print $1}')" = "$V" ] || { echo "⛔ il motore non dice $V"; exit 1; }
"$LAV/motore-bin/remotix-install" catalogo | head -1 | tee -a "$REG"

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

passo "4. i pacchetti del motore e della chiave"
RX_VERSIONE=$V RX_REVISIONE=$R MOTORE=$LAV/motore-bin/remotix-install \
	"$ALBERO/packaging/archivio/pacchetti-motore.sh" "$LAV/motore" >>"$REG" 2>&1 || { tail -20 "$REG"; exit 1; }

passo "5. l'archivio ($ARCHIVIO)"
PUB="bash $ALBERO/packaging/archivio/pubblica.sh"
M=$LAV/motore
for b in "${deb[@]}"; do
	$PUB aggiungi "$CANALE" "$b" "$P/deb-$b"/remotix_*.deb "$M/remotix-install_${V}-${R}_amd64.deb" "$M/remotix-archive-keyring_${V}-${R}_all.deb"
done
for b in "${rpm[@]}"; do
	$PUB aggiungi "$CANALE" "$b" $(ls "$P/rpm/$b"/*.rpm | grep -vE '\.src\.rpm$|-debug(info|source)-') "$M"/remotix-install-"$V"-"$R".x86_64.rpm
done
if [ $arch = 1 ]; then
	$PUB aggiungi "$CANALE" arch "$P/arch"/remotix-"$V"-"$R"-x86_64.pkg.tar.zst "$M"/remotix-install-"$V"-"$R"-x86_64.pkg.tar.zst
fi
$PUB motore "$LAV/motore-bin/remotix-install"
$PUB script
podman run --rm docker.io/library/golang:1.25 cat /usr/local/go/LICENSE >"$LAV/LICENSE-go"
LICENZA_GO=$LAV/LICENSE-go $PUB rigenera 2>&1 | tee -a "$REG"

passo "6. il riassunto"
SHA_IS=$(cut -d' ' -f1 "$ARCHIVIO/install.sh.sha256")
printf '%s %s commit %s canale %s bersagli %s install.sh %s\n' "$VERSIONE" "$(date -u +%FT%TZ)" "$COMMIT" "$CANALE" \
	"$(echo $BERSAGLI | tr ' ' ',')" "$SHA_IS" >>"$ARCHIVIO/RILASCI.txt"
cat <<EOF | tee -a "$REG"
REMOTIX $VERSIONE — pronto in $ARCHIVIO
  install.sh sha256 (da pubblicare sul sito, in HTTPS):
      $SHA_IS
  motore:      $(cut -c1-64 "$ARCHIVIO/motore/remotix-install.sha256")
  caricarlo (D10 aperta, l'indirizzo è un segnaposto) — senza --delete: le versioni vecchie restano:
      rsync -a "$ARCHIVIO/" $DESTINAZIONE
  il giornale del rilascio: $REG
EOF
