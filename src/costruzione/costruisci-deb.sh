#!/usr/bin/env bash
# costruisci-deb.sh — il pacchetto .deb di REMOTIX, dentro il contenitore del bersaglio.
#
#     src/costruzione/costruisci-deb.sh debian13            # uno
#     src/costruzione/costruisci-deb.sh debian13 ubuntu2604 # tutti e due
#     DUE=1 src/costruzione/costruisci-deb.sh debian13      # e la prova R23
#
# Per ogni bersaglio (fasi/17-l-installatore.md §6.1-§6.4, tappa T3):
#   1. l'immagine localhost/remotix-costruzione-<bersaglio> (Contenitore.<bersaglio>,
#      con lo strato degli attrezzi .deb in coda);
#   2. una COPIA dell'albero: src/, banchi/rcp/ (il gemello che il Makefile
#      confronta) e packaging/debian/ come debian/; debian/changelog si SCRIVE
#      qui, con la versione e la data del commit (la data diventa
#      SOURCE_DATE_EPOCH: stessa fonte, stesso pacchetto — R23);
#   3. `dpkg-buildpackage -b` nel contenitore, poi lintian;
#   4. i controlli sul pacchetto FINITO, non sull'albero:
#        R13  la funzione di banco non c'e' nel binario estratto dal .deb, e
#             c'e' in un rcp.o costruito con BANCO_ACCESO 1 (il controllo
#             positivo: senza, «non trovata» potrebbe voler dire «non so cercare»);
#             e l'unita' non passa opzioni di banco;
#        R14  nessun file del banco nell'elenco del pacchetto;
#        R4   `ldd` del binario estratto nel contenitore: niente «not found»,
#             niente ngtcp2/nghttp3 dinamiche;
#        R23  con DUE=1 una seconda costruzione in una seconda copia pulita:
#             il .deb dev'essere identico byte per byte.
#
# Uscita in $USCITA/deb-<bersaglio>/: il .deb, il .buildinfo, costruzione.log,
# lintian.txt, controlli.txt (una riga per controllo, SI/NO).
# ⚠ Niente /tmp (sul portatile e' quasi pieno): tutto sotto $CACHE.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
CACHE=${CACHE:-$USCITA/.lavoro}
command -v podman >/dev/null 2>&1 || { echo "⛔ podman non c'e'"; exit 2; }
mkdir -p "$CACHE/tmp" "$USCITA"
export TMPDIR="$CACHE/tmp"
[ $# -gt 0 ] || set -- debian13 ubuntu2604

HASH=$(git -C "$ALBERO" rev-parse --short=7 HEAD)
DATA_R=$(git -C "$ALBERO" log -1 --format=%cD HEAD)
GIORNO=$(git -C "$ALBERO" log -1 --date=format:%Y%m%d --format=%cd HEAD)
SPORCO=""
if [ -n "$(git -C "$ALBERO" status --porcelain -- src packaging banchi/rcp)" ]; then
	SPORCO=".modificato"
	echo "⚠ l'albero ha modifiche non committate in src/ packaging/ banchi/rcp/:"
	echo "  la versione porta «$SPORCO» e il pacchetto NON corrisponde a $HASH"
fi

prepara_copia() {  # prepara_copia <cartella> <bersaglio>
	local c=$1 b=$2 suff dist
	case $b in
	debian13)   suff=+deb13;       dist=trixie ;;
	ubuntu2604) suff=+ubuntu26.04; dist=resolute ;;
	*) echo "⛔ $b: non e' un bersaglio .deb"; return 2 ;;
	esac
	rm -rf "$c"; mkdir -p "$c/remotix/banchi"
	cp -a "$ALBERO/src" "$c/remotix/src"
	cp -a "$ALBERO/banchi/rcp" "$c/remotix/banchi/rcp"
	cp -a "$ALBERO/packaging/debian" "$c/remotix/debian"
	rm -f "$c/remotix/src/remotix" "$c/remotix/src"/*.o \
	      "$c/remotix/src"/*-protocol.c "$c/remotix/src"/*-client-protocol.h
	# T8: RX_VERSIONE e RX_REVISIONE danno la versione di un RILASCIO dell'archivio
	#     (0.17.0-2+deb13: la revisione cresce a ogni ricostruzione di manutenzione);
	#     senza, quella di prova col commit, come in T3.
	if [ -n "${RX_VERSIONE:-}" ]; then
		VERSIONE="$RX_VERSIONE$SPORCO-${RX_REVISIONE:-1}$suff"
	else
		VERSIONE="0.17.0~git$GIORNO.$HASH$SPORCO-1$suff"
	fi
	cat >"$c/remotix/debian/changelog" <<EOF
remotix ($VERSIONE) $dist; urgency=medium

  * Costruito da $HASH$SPORCO (fase 17, T3).

 -- nicfio <nicfio@gmail.com>  $DATA_R
EOF
}

costruisci_in() {  # costruisci_in <copia> <immagine> <log>
	podman run --rm --userns=keep-id -v "$1:/lavoro" -w /lavoro/remotix "$2" \
		sh -c 'dpkg-buildpackage -b -us -uc' >"$3" 2>&1
}

uno() {
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$USCITA/deb-$1"
	local c1="$CACHE/deb-$1-a" c2="$CACHE/deb-$1-b" deb esito=0
	rm -rf "$u"; mkdir -p "$u"
	printf '== %s: immagine\n' "$b"
	podman build -t "$imm" -f "$QUI/Contenitore.$b" "$QUI" >"$u/immagine.log" 2>&1 \
		|| { echo "⛔ $b: immagine (vedi $u/immagine.log)"; return 1; }

	printf '== %s: pacchetto\n' "$b"
	prepara_copia "$c1" "$b" || return 1
	if ! costruisci_in "$c1" "$imm" "$u/costruzione.log"; then
		echo "⛔ $b: dpkg-buildpackage fallito (vedi $u/costruzione.log)"; tail -20 "$u/costruzione.log"
		return 1
	fi
	deb=$(cd "$c1" && ls remotix_*.deb | head -1)
	cp "$c1/$deb" "$c1"/remotix_*.buildinfo "$u/"
	echo "   $deb"

	printf '== %s: lintian e controlli\n' "$b"
	podman run --rm -v "$u:/u:ro" "$imm" lintian -I --pedantic --no-tag-display-limit "/u/$deb" \
		>"$u/lintian.txt" 2>&1
	# R13 positivo: rcp.o con BANCO_ACCESO 1, stessi flag del Makefile
	rm -rf "$c1/positivo"; cp -a "$c1/remotix/src" "$c1/positivo"
	sed -i 's/^#define BANCO_ACCESO 0$/#define BANCO_ACCESO 1/' "$c1/positivo/rcp.c"
	podman run --rm --userns=keep-id -v "$c1:/lavoro" -w /lavoro/positivo "$imm" \
		sh -c 'make GEMELLO=nessuno rcp.o >/dev/null 2>&1' >/dev/null 2>&1
	podman run --rm -v "$u:/u:ro" -v "$c1:/c:ro" "$imm" sh -c '
		set -u
		d=$(mktemp -d); dpkg-deb -x /u/'"$deb"' "$d"
		bin=$d/usr/libexec/remotix/remotix
		frase="FUNZIONE DI BANCO e'"'"' ACCESA"
		n=$(strings "$bin" | grep -c "$frase")
		p=$(strings /c/positivo/rcp.o 2>/dev/null | grep -c "$frase")
		[ "$n" = 0 ] && [ "$p" -ge 1 ] && r=SI || r=NO
		echo "R13 banco-nel-binario $r (pacchetto: $n, controllo positivo rcp.o con BANCO_ACCESO 1: $p)"
		o=$(grep "^ExecStart" $d/usr/lib/systemd/system/remotix.service | \
		     grep -oE -- "--(rilievo|comando-socket|audio-prova|parlantina|sblocca)" | sort -u | tr "\n" " ")
		[ -z "$o" ] && echo "R13 opzioni-di-banco-nell-unita SI (nessuna)" \
		            || echo "R13 opzioni-di-banco-nell-unita NO ($o)"
		nere=$(dpkg-deb -c /u/'"$deb"' | awk "{print \$NF}" | \
		       grep -E "prova|sudoers|gpu-udev|riavvia-|ld\.so\.conf|provisiona|banchi|/opt/|\.pem$|\.key$" || true)
		[ -z "$nere" ] && echo "R14 file-del-banco SI (nessuno)" \
		               || echo "R14 file-del-banco NO: $nere"
		l=$(ldd "$bin")
		if printf "%s\n" "$l" | grep -q "not found"; then echo "R4 ldd NO (not found)";
		elif printf "%s\n" "$l" | grep -qE "ngtcp2|nghttp3"; then echo "R4 ldd NO (ngtcp2/nghttp3 dinamiche)";
		else echo "R4 ldd SI ($(printf "%s\n" "$l" | wc -l) librerie, nessuna mancante)"; fi
		echo "Depends:    $(dpkg-deb -f /u/'"$deb"' Depends)"
		echo "Recommends: $(dpkg-deb -f /u/'"$deb"' Recommends)"
		echo "Statiche:   $(dpkg-deb -f /u/'"$deb"' Static-Built-Using)"
		echo "Conffiles:"; dpkg-deb --ctrl-tarfile /u/'"$deb"' | tar -xO ./conffiles | sed "s/^/  /"
	' >"$u/controlli.txt" 2>&1
	dpkg-deb -c "$u/$deb" >"$u/elenco.txt"

	if [ "${DUE:-0}" = 1 ]; then
		printf '== %s: seconda costruzione (R23)\n' "$b"
		prepara_copia "$c2" "$b" || return 1
		if costruisci_in "$c2" "$imm" "$u/costruzione-2.log"; then
			if cmp -s "$c1/$deb" "$c2/$deb"; then
				echo "R23 riproducibile SI ($(sha256sum <"$u/$deb" | cut -c1-16)… uguale in due copie pulite)" >>"$u/controlli.txt"
			else
				echo "R23 riproducibile NO (i due .deb differiscono)" >>"$u/controlli.txt"
				cp "$c2/$deb" "$u/seconda-$deb"
			fi
		else
			echo "R23 riproducibile NO (seconda costruzione fallita)" >>"$u/controlli.txt"
		fi
	fi
	grep -q ' NO' "$u/controlli.txt" && esito=1
	sed 's/^/   /' "$u/controlli.txt"
	printf '   lintian: %s\n' "$(grep -cE '^[EWIP]: ' "$u/lintian.txt") righe (E=$(grep -c '^E: ' "$u/lintian.txt") W=$(grep -c '^W: ' "$u/lintian.txt"))"
	return $esito
}

stato=0
for b in "$@"; do uno "$b" || stato=1; done
exit $stato
