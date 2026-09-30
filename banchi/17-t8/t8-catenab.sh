#!/bin/bash
# t8-catenab.sh — fase 17, T8, R17: la catena B (i pacchetti e i metadati dell'archivio, GPG) la
# verifica il GESTORE DI PACCHETTI. Per ogni guasto (t8-guasta.sh): un byte cambiato nei metadati,
# i metadati firmati da una chiave ESTRANEA, un byte cambiato nel pacchetto N+1 — il gestore deve
# rifiutare, e la versione non cambiare. Dopo D14 (DECISIONI §10.23) l'aggiornamento è quello del
# sistema (apt upgrade, dnf upgrade, pacman -Syu), ristretto ai pacchetti di REMOTIX per non
# aspettare il resto.
#
#   (sul server)  bash t8-catenab.sh <macchina>…     (ciascuna con la N installata e la N+1 in attesa)
set -uo pipefail
V=/media/REMOTIX/vm17; T8=$V/t8
vm() { bash $V/17-vm.sh ssh "$@"; }
fam() { case $1 in debian*) echo deb;; fedora*) echo rpm;; arch*) echo pacman;; esac; }
prova() {  # prova <guasto> <macchine…>
	local g=$1; shift
	bash $T8/t8-guasta.sh "$g" >/dev/null
	for m in "$@"; do
		local out v=ROSSO
		# niente pacchetti N+1 già in cache (quelli scaricati prima sono buoni, e il gestore li userebbe)
		# e niente elenchi dell'archivio già scaricati: con l'InRelease uguale apt non riscarica i Packages
		out=$(vm "$m" "sudo apt-get clean 2>/dev/null; sudo dnf clean packages >/dev/null 2>&1; sudo rm -f /var/cache/pacman/pkg/remotix-[0-9]*
sudo sh -c 'rm -f /var/lib/apt/lists/10.0.2.2:8717_* /var/lib/pacman/sync/remotix.*' 2>/dev/null
a=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
{ if command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y --only-upgrade remotix remotix-install;
  elif command -v dnf >/dev/null; then sudo dnf upgrade -y --refresh remotix remotix-install;
  else sudo pacman -Sy --noconfirm remotix; fi; } 2>&1 | grep -E 'Hash|firma|signature|NO_PUBKEY|not signed|invalid|corrupted|BADSIG|GPG|Err|Error|error' | head -4
b=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
echo \"remotix prima: \$a · dopo: \$b\"" 2>&1)
		# verde: la versione NON è cambiata, e il gestore ha detto il rifiuto
		a=$(echo "$out" | sed -n 's/.*remotix prima: \(.*\) · dopo: \(.*\)/\1|\2/p')
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
