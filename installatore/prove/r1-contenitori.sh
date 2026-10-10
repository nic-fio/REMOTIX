#!/bin/sh
# R1 (fasi/17 §8) in the containers, one family at a time: the fingerprint of /etc before and after
# «remotix-install verifica» (text and --json) must be IDENTICAL — names, permissions, owners,
# sizes, modification times, contents. (The trial run plan → approve → apply that followed was
# removed on 10 Oct 2026: those commands no longer exist, DECISIONI §10.36.)
#
#   prove/r1-contenitori.sh [immagine...]
#
# ⚠ A container is not the customer's machine (no systemd running, no card, no
# firewall): R1 here proves that the check does not write in /etc; the VMs of §7 remain the real test.
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
		/opt/rx/remotix-install check > /tmp/verifica.txt 2>&1; echo "check: exit $?"
		/opt/rx/remotix-install check --json > /tmp/verifica.json 2>&1; echo "check --json: exit $?"
		/opt/rx/impronta /etc > /tmp/dopo
		if /opt/rx/impronta -confronta /tmp/prima /tmp/dopo > /tmp/diff; then echo "R1 PASS: /etc identical ($(grep -c . /tmp/prima) entries)"; else echo "R1 FAIL"; head -20 /tmp/diff; fi
		echo "---- check (text)"; cat /tmp/verifica.txt
	' > "$esiti/$nome.txt" 2>&1 || true
	grep -E '^(R1|check)' "$esiti/$nome.txt" | sed 's/^/   /'
	grep -q '^R1 PASS' "$esiti/$nome.txt" || rosso=1
done
echo "full results in $esiti/"
exit $rosso
