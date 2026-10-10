#!/bin/sh
# R1 (fasi/17 §8) nei contenitori, una famiglia per volta: l'impronta di /etc prima e dopo
# «remotix-install verifica» (testo e --json) deve essere IDENTICA — nomi, permessi, proprietari,
# dimensioni, ore di modifica, contenuti. (Il giro di prova piano → approva → applica che seguiva è
# stato tolto il 10 ott 2026: quei comandi non ci sono più, DECISIONI §10.36.)
#
#   prove/r1-contenitori.sh [immagine...]
#
# ⚠ Un contenitore non è la macchina del cliente (niente systemd acceso, niente scheda, niente
# firewall): R1 qui prova che il controllo non scrive in /etc; le VM di §7 restano la prova vera.
set -eu
qui=$(cd "$(dirname "$0")/.." && pwd)
"$qui/costruisci.sh" >/dev/null
"$qui/costruisci.sh" go build -trimpath -o uscita/impronta ./prove/impronta
esiti="$qui/uscita/r1"
mkdir -p "$esiti"
immagini=${*:-"docker.io/library/debian:13 registry.fedoraproject.org/fedora:44 docker.io/library/archlinux:latest registry.opensuse.org/opensuse/tumbleweed:latest"}
rosso=0
for img in $immagini; do
	nome=$(echo "$img" | sed 's|.*/||; s|:|-|')
	echo "== $img"
	podman run --rm -v "$qui/uscita:/opt/rx:ro,Z" "$img" sh -c '
		/opt/rx/impronta /etc > /tmp/prima
		/opt/rx/remotix-install check > /tmp/verifica.txt 2>&1; echo "verifica: uscita $?"
		/opt/rx/remotix-install check --json > /tmp/verifica.json 2>&1; echo "verifica --json: uscita $?"
		/opt/rx/impronta /etc > /tmp/dopo
		if /opt/rx/impronta -confronta /tmp/prima /tmp/dopo > /tmp/diff; then echo "R1 PASS: /etc identica ($(grep -c . /tmp/prima) voci)"; else echo "R1 FAIL"; head -20 /tmp/diff; fi
		echo "---- verifica (testo)"; cat /tmp/verifica.txt
	' > "$esiti/$nome.txt" 2>&1 || true
	grep -E '^(R1|verifica)' "$esiti/$nome.txt" | sed 's/^/   /'
	grep -q '^R1 PASS' "$esiti/$nome.txt" || rosso=1
done
echo "esiti completi in $esiti/"
exit $rosso
