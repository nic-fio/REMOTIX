#!/bin/bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
# t8-catenab.sh — phase 17, T8, R17: chain B (the archive's packages and metadata, GPG) is
# verified by the PACKAGE MANAGER. For each fault (t8-guasta.sh): one byte changed in the metadata,
# the metadata signed by a FOREIGN key, one byte changed in package N+1 — the manager must
# refuse, and the version must not change. After D14 (DECISIONI §10.23) the upgrade is the
# system's (apt upgrade, dnf upgrade, pacman -Syu), restricted to the REMOTIX packages so as not
# to wait for the rest.
#
#   (on the server)  bash t8-catenab.sh <machine>…     (each with N installed and N+1 pending)
set -uo pipefail
V=/media/REMOTIX/vm17; T8=$V/t8
vm() { bash $V/17-vm.sh ssh "$@"; }
fam() { case $1 in debian*) echo deb;; fedora*) echo rpm;; arch*) echo pacman;; esac; }
prova() {  # prova <fault> <machines…>
	local g=$1; shift
	bash $T8/t8-guasta.sh "$g" >/dev/null
	for m in "$@"; do
		local out v=ROSSO
		# no N+1 packages already in cache (those downloaded before are good, and the manager would use them)
		# and no archive lists already downloaded: with the same InRelease apt does not download Packages again
		out=$(vm "$m" "sudo apt-get clean 2>/dev/null; sudo dnf clean packages >/dev/null 2>&1; sudo rm -f /var/cache/pacman/pkg/remotix-[0-9]*
sudo sh -c 'rm -f /var/lib/apt/lists/10.0.2.2:8717_* /var/lib/pacman/sync/remotix.*' 2>/dev/null
a=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
{ if command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y --only-upgrade remotix remotix-install;
  elif command -v dnf >/dev/null; then sudo dnf upgrade -y --refresh remotix remotix-install;
  else sudo pacman -Sy --noconfirm remotix; fi; } 2>&1 | grep -E 'Hash|firma|signature|NO_PUBKEY|not signed|invalid|corrupted|BADSIG|GPG|Err|Error|error' | head -4
b=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
echo \"remotix before: \$a · after: \$b\"" 2>&1)
		# green: the version has NOT changed, and the manager stated the refusal
		a=$(echo "$out" | sed -n 's/.*remotix before: \(.*\) · after: \(.*\)/\1|\2/p')
		[ "${a%%|*}" = "${a#*|}" ] && echo "$out" | grep -qiE 'hash|signature|NO_PUBKEY|BADSIG|GPG|invalid|corrupted|error' && v=VERDE
		printf '%-6s %-15s %-16s\n' "$v" "$g" "$m"
		echo "$out" | sed 's/^/         /' | cut -c1-300
	done
	bash $T8/t8-guasta.sh ripristina >/dev/null
}
ms=("$@")
f=$(fam "${ms[0]}")
for g in "$f-byte" "$f-firma" pacchetto-byte; do
	prova "$g" "${ms[@]}"
done
