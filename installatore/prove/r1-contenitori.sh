#!/bin/sh
# R1 (fasi/17 §8) in the containers, one family at a time: the fingerprint of /etc before and after
# «remotix-install check» (text and --json) must be IDENTICAL — names, permissions, owners,
# sizes, modification times, contents. (The trial run plan → approve → apply that followed was
# removed on 10 Oct 2026: those commands no longer exist, DECISIONI §10.36.)
#
#   prove/r1-contenitori.sh [bitmap...]
#
# ⚠ A container is not the customer's machine (no systemd running, no card, no
# firewall): R1 here proves that the check does not write in /etc; the VMs of §7 remain the real test.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
"$here/costruisci.sh" >/dev/null
"$here/costruisci.sh" go build -trimpath -o uscita/fingerprint ./prove/fingerprint
outcomes="$here/uscita/r1"
mkdir -p "$outcomes"
images=${*:-"docker.io/library/debian:13 registry.fedoraproject.org/fedora:44 docker.io/library/archlinux:latest registry.opensuse.org/opensuse/tumbleweed:latest"}
red=0
for img in $images; do
	name=$(echo "$img" | sed 's|.*/||; s|:|-|')
	echo "== $img"
	podman run --rm -v "$here/uscita:/opt/rx:ro,Z" "$img" sh -c '
		/opt/rx/fingerprint /etc > /tmp/prima
		/opt/rx/remotix-install check > /tmp/verifica.txt 2>&1; echo "check: exit $?"
		/opt/rx/remotix-install check --json > /tmp/verifica.json 2>&1; echo "check --json: exit $?"
		/opt/rx/fingerprint /etc > /tmp/dopo
		if /opt/rx/fingerprint -compare /tmp/prima /tmp/dopo > /tmp/diff; then echo "R1 PASS: /etc identical ($(grep -c . /tmp/prima) entries)"; else echo "R1 FAIL"; head -20 /tmp/diff; fi
		echo "---- check (text)"; cat /tmp/verifica.txt
	' > "$outcomes/$name.txt" 2>&1 || true
	grep -E '^(R1|check)' "$outcomes/$name.txt" | sed 's/^/   /'
	grep -q '^R1 PASS' "$outcomes/$name.txt" || red=1
done
echo "full results in $outcomes/"
exit $red
