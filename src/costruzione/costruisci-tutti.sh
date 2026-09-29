#!/usr/bin/env bash
# costruisci-tutti.sh — costruisce REMOTIX per un bersaglio, per alcuni, o per tutti.
#
#     src/costruzione/costruisci-tutti.sh                 # tutti
#     src/costruzione/costruisci-tutti.sh fedora44 arch   # solo questi
#
# Per ogni bersaglio (fasi/17-l-installatore.md §6.2):
#   1. l'immagine `localhost/remotix-costruzione-<bersaglio>` da Contenitore.<bersaglio>
#      (la prima volta qualche minuto: ci si costruiscono nghttp3 e ngtcp2 statiche);
#   2. una COPIA dell'albero (src/ e banchi/rcp/) in $CACHE/albero-<bersaglio>:
#      `make` scrive .o e binario accanto ai sorgenti, e otto bersagli sullo
#      stesso src/ si pesterebbero i piedi — e sporcherebbero il src/remotix
#      di chi lavora;
#   3. `make pulisci tutto` dentro il contenitore;
#   4. nella cartella d'uscita $USCITA/<bersaglio>/:
#        remotix          il binario (se compila)
#        immagine.log     il registro della costruzione dell'immagine
#        compilazione.log il registro di make
#        versioni.txt     OpenSSL, libavcodec, libei, pipewire, glib trovate
#        ldd.txt          `ldd remotix` DENTRO il contenitore del bersaglio
#        esito.txt        una riga: compila sì/no, ldd pulito sì/no
#
# ⚠ Niente /tmp: sul portatile e' quasi pieno.  TMPDIR di podman e copie
#   dell'albero stanno in $CACHE (predefinito $USCITA/.lavoro, sul disco):
#   su questo portatile ~/.cache e' un collegamento a /tmp.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
CACHE=${CACHE:-$USCITA/.lavoro}
TUTTI=(debian13 ubuntu2604 ubuntu2404 fedora44 alma10 arch tumbleweed leap16)

command -v podman >/dev/null 2>&1 || { echo "⛔ podman non c'e'"; exit 2; }
mkdir -p "$CACHE/tmp" "$USCITA"
export TMPDIR="$CACHE/tmp"

if [ $# -eq 0 ] || [ "$1" = tutti ]; then set -- "${TUTTI[@]}"; fi

costruisci_uno()
{
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$USCITA/$1" copia="$CACHE/albero-$1"
	local compila=no ldd_ok=- nota=""

	[ -f "$QUI/Contenitore.$b" ] || { echo "⛔ $b: manca Contenitore.$b"; return 2; }
	rm -rf "$u"; mkdir -p "$u"
	printf '== %s: immagine\n' "$b"
	if ! podman build -t "$imm" -f "$QUI/Contenitore.$b" "$QUI" >"$u/immagine.log" 2>&1; then
		echo "$b compila=no immagine=NO (vedi immagine.log)" | tee "$u/esito.txt"
		return 1
	fi

	podman run --rm "$imm" sh -c '
		for m in openssl libavcodec libei-1.0 libpipewire-0.3 glib-2.0; do
			printf "%-18s %s\n" "$m" "$(pkg-config --modversion $m 2>&1)"
		done
		printf "%-18s %s\n" gcc "$(cc -dumpfullversion 2>&1)"
		printf "%-18s %s\n" ngtcp2 "$(pkg-config --modversion libngtcp2 2>&1) (nostra, statica)"
		printf "%-18s %s\n" nghttp3 "$(pkg-config --modversion libnghttp3 2>&1) (nostra, statica)"
	' >"$u/versioni.txt" 2>&1

	printf '== %s: compilazione\n' "$b"
	rm -rf "$copia"; mkdir -p "$copia/banchi"
	cp -a "$ALBERO/src" "$copia/src"
	cp -a "$ALBERO/banchi/rcp" "$copia/banchi/rcp"
	rm -f "$copia/src/remotix" "$copia/src"/*.o
	podman run --rm --userns=keep-id -v "$copia:/albero" -w /albero/src "$imm" \
		sh -c 'make pulisci >/dev/null && make tutto' >"$u/compilazione.log" 2>&1
	if [ -x "$copia/src/remotix" ]; then
		compila=si
		cp "$copia/src/remotix" "$u/remotix"
		podman run --rm -v "$u:/u:ro" "$imm" ldd /u/remotix >"$u/ldd.txt" 2>&1
		ldd_ok=si
		grep -q 'not found' "$u/ldd.txt" && { ldd_ok=no; nota="$nota librerie-mancanti"; }
		grep -qE 'ngtcp2|nghttp3' "$u/ldd.txt" && { ldd_ok=no; nota="$nota ngtcp2/nghttp3-dinamiche"; }
	else
		nota=" errori: $(grep -cE 'error:|Error [0-9]' "$u/compilazione.log") righe (vedi compilazione.log)"
	fi
	echo "$b compila=$compila ldd-pulito=$ldd_ok$nota" | tee "$u/esito.txt"
	[ $compila = si ] && [ $ldd_ok = si ]
}

stato=0
for b in "$@"; do costruisci_uno "$b" || stato=1; done
printf '\n== riassunto (%s)\n' "$USCITA"
for b in "$@"; do cat "$USCITA/$b/esito.txt" 2>/dev/null || echo "$b (nessun esito)"; done
exit $stato
