#!/bin/bash
# t8-fiducia.sh — fase 17, T8: la catena A sulle VM. Per ogni guasto dell'archivio (t8-guasta.sh)
# l'amministratore chiede l'aggiornamento (aggiorna --applica, con una N+1 in attesa): l'operazione
# deve fermarsi BLOCCATA col suo codice RX-TRUST-…, e le versioni restare quelle di prima.
#
#   (sul server)  bash t8-fiducia.sh <macchina>…
set -uo pipefail
V=/media/REMOTIX/vm17; T8=$V/t8
vm() { bash $V/17-vm.sh ssh "$@"; }
prova() {  # prova <guasto> <codice atteso> <macchine…>
	local g=$1 c=$2; shift 2
	bash $T8/t8-guasta.sh "$g" >/dev/null
	for m in "$@"; do
		local out
		out=$(vm "$m" "a=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
sudo /root/remotix-install aggiorna --applica --lingua it 2>&1 | grep -E '^operazione|RX-TRUST|BLOCCATA' | head -4
b=\$( (dpkg-query -W -f='\${Version}' remotix; rpm -q remotix; pacman -Q remotix) 2>/dev/null | tr '\n' ' ')
op=\$(sudo ls -t /var/lib/remotix/operazioni | head -1); echo \"stato: \$(sudo cat /var/lib/remotix/operazioni/\$op/stato) · remotix prima: \$a · dopo: \$b\"" 2>&1)
		local v=ROSSO
		echo "$out" | grep -q "$c" && echo "$out" | grep -q "stato: BLOCCATA" && v=VERDE
		[ "$c" = "-" ] && echo "$out" | grep -q "stato: CONFERMATA" && v=VERDE
		printf '%-6s %-17s %-16s atteso %s\n' "$v" "$g" "$m" "$c"
		echo "$out" | sed 's/^/         /' | cut -c1-260
	done
	bash $T8/t8-guasta.sh ripristina >/dev/null
}
prova catalogo-byte    RX-TRUST-007 "$@"
prova catalogo-scaduto RX-TRUST-002 "$@"
prova revoca           RX-TRUST-010 "$@"
# fuori linea, dato esplicitamente: scaduto ⇒ BLOCCATA anche senza rete (§6.6.12)
for m in "$@"; do
	cat $T8/guasti/scaduto/catalogo.json | vm "$m" "cat >/tmp/scaduto.json"
	cat $T8/guasti/scaduto/catalogo.json.firma | vm "$m" "cat >/tmp/scaduto.json.firma"
	out=$(vm "$m" "sudo /root/remotix-install disinstalla --uscita /tmp/d.json --lingua it >/dev/null 2>&1; sudo /root/remotix-install approva /tmp/d.json >/dev/null 2>&1
sudo /root/remotix-install applica /tmp/d.json --catalogo /tmp/scaduto.json --lingua it 2>&1 | grep -E 'RX-TRUST|^operazione' | head -4
sudo systemctl is-active remotix" 2>&1)
	v=ROSSO; echo "$out" | grep -q RX-TRUST-002 && echo "$out" | grep -q BLOCCATA && echo "$out" | grep -qx active && v=VERDE
	printf '%-6s %-17s %-16s atteso RX-TRUST-002, niente toccato\n' "$v" "fuori-linea-scad" "$m"
	echo "$out" | sed 's/^/         /' | cut -c1-260
done
