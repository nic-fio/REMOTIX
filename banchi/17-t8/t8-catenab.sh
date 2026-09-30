#!/bin/bash
# t8-catenab.sh — fase 17, T8, R17: la catena B (i pacchetti e i metadati dell'archivio, GPG) la
# verifica il GESTORE DI PACCHETTI. Per ogni guasto (t8-guasta.sh): un byte cambiato nei metadati,
# i metadati firmati da una chiave ESTRANEA, un byte cambiato nel pacchetto N+1 — il gestore deve
# rifiutare, e il motore fermarsi senza cambiare versione.
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
		out=$(vm "$m" "sudo apt-get clean 2>/dev/null; sudo dnf clean packages >/dev/null 2>&1; sudo rm -f /var/cache/pacman/pkg/remotix-0.17.0-5*
sudo sh -c 'rm -f /var/lib/apt/lists/10.0.2.2:8717_* /var/lib/pacman/sync/remotix.*' 2>/dev/null
a=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
sudo /root/remotix-install aggiorna --applica --lingua it 2>&1 | grep -E '^operazione|RX-AGG|RX-PACCHETTI|FALLITA|Hash|firma|signature|NO_PUBKEY|not signed|invalid|corrupted|BADSIG|GPG' | head -4
b=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
echo \"remotix prima: \$a · dopo: \$b\"" 2>&1)
		# verde: la versione NON è cambiata, e c'è un rifiuto detto (RX-AGG-007 o un'operazione annullata)
		a=$(echo "$out" | sed -n 's/.*remotix prima: \(.*\) · dopo: \(.*\)/\1|\2/p')
		[ "${a%%|*}" = "${a#*|}" ] && echo "$out" | grep -qE 'RX-AGG-007|ANNULLATA|RX-PACCHETTI|FALLITA' && v=VERDE
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
