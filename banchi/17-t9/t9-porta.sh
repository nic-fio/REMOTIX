#!/usr/bin/env bash
# t9-porta.sh — fase 17, T9: il motore nuovo e lo script d'ingresso, FIRMATI (catena A, chiavi DI
# PROVA), in un archivio di prova SUO sul server, e il banco di T9.
#
#   (sul portatile)   bash banchi/17-t9/t9-porta.sh
#
#   costruisce installatore/uscita/remotix-install; firma il motore e install.sh con la sottochiave
#   A-2026 (le private in ~/.local/share/remotix-chiavi-di-prova, fuori dal deposito);
#   /media/REMOTIX/vm17/t9/archivio/ = copia dell'archivio di T8 + questo motore + install.sh,
#   servito su 127.0.0.1:8727 (dalla VM: 10.0.2.2:8727). ⚠ L'archivio di T8 (8717) non si tocca:
#   altri banchi lo usano.
#   /media/REMOTIX/vm17/t9/: t9-vm.sh, i file di risposte, il modello di cloud-init; e 17-vm.sh
#   aggiornato (RX_VM_SEME, RX_VM_RETE, RX_VM_CATTURA: senza, fa quel che faceva).
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
INST=$ALBERO/installatore
CHIAVI=${CHIAVI:-$HOME/.local/share/remotix-chiavi-di-prova}
SUB=${SOTTOCHIAVE_A:-A-2026}
S=nicfio@192.168.0.2
V=/media/REMOTIX/vm17
U=$INST/uscita

"$INST/costruisci.sh" >/dev/null
# la costruzione con la finestra (DECISIONI §10.19): stesso sorgente, etichetta «gui»
"$INST/costruisci.sh" gui >/dev/null
firma() { # firma <oggetto> <file>
	rm -rf "$INST/.cache/chiavi-firma" "$INST/.cache/da-firmare"; mkdir -p "$INST/.cache/da-firmare"
	cp -a "$CHIAVI/a" "$INST/.cache/chiavi-firma"
	cp "$2" "$INST/.cache/da-firmare/oggetto"
	"$INST/costruisci.sh" go run ./strumenti/chiavi-a firma /src/.cache/chiavi-firma "$SUB" "$1" /src/.cache/da-firmare/oggetto "$(date -u +%F)" >/dev/null
	cp "$INST/.cache/da-firmare/oggetto.firma" "$2.firma"
	rm -rf "$INST/.cache/chiavi-firma" "$INST/.cache/da-firmare"
}
cp "$INST/install.sh" "$U/install.sh"
firma motore "$U/remotix-install"
firma motore "$U/remotix-install-gui"
firma script "$U/install.sh"
echo "motore $(sha256sum "$U/remotix-install" | cut -c1-16)… e install.sh firmati con $SUB"

ssh -o BatchMode=yes $S "mkdir -p $V/t9 && rm -rf $V/t9/archivio && cp -a $V/archivio $V/t9/archivio" 2>&1 | grep -v tput || true
scp -q "$U/remotix-install" "$U/remotix-install.firma" "$U/remotix-install-gui" "$U/remotix-install-gui.firma" $S:$V/t9/archivio/motore/
scp -q "$U/install.sh" "$U/install.sh.firma" $S:$V/t9/archivio/
scp -q "$QUI/t9-vm.sh" "$QUI/t9-rete.py" "$QUI"/risposte-*.conf "$QUI/cloud-init-r21.yaml" "$QUI/t9-gui.sh" $S:$V/t9/
# in modo atomico: altri banchi possono star leggendo 17-vm.sh proprio adesso (bash lo legge a pezzi)
scp -q "$ALBERO/banchi/17-distro/17-vm.sh" $S:$V/.17-vm.sh.nuovo
ssh -o BatchMode=yes $S "chmod 755 $V/.17-vm.sh.nuovo && mv $V/.17-vm.sh.nuovo $V/17-vm.sh" 2>&1 | grep -v tput || true
# ⚠ due ssh separati: con l'accensione nella stessa riga, pkill -f trova la shell di ssh (che contiene
# «http.server 8727») e la uccide; [h] evita che trovi sé stesso
ssh -o BatchMode=yes $S "pkill -f '[h]ttp.server 8727'" || true
ssh -o BatchMode=yes $S "
(setsid nohup python3 -m http.server 8727 --bind 127.0.0.1 --directory $V/t9/archivio >$V/t9/http-8727.log 2>&1 </dev/null &)
sleep 1
curl -s -o /dev/null -w 'archivio di T9: %{http_code}\n' http://127.0.0.1:8727/install.sh" 2>&1 | grep -v tput
