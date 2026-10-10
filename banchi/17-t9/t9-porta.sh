#!/usr/bin/env bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
# t9-porta.sh — phase 17, T9: the new engine and the entry script, with their sha256 (simplified D11,
# DECISIONI §10.21: no signatures of their own), in a test archive of ITS OWN on the server, and the
# T9 bench. (A real release is made by packaging/rilascio.sh.)
#
#   (on the laptop)   bash banchi/17-t9/t9-porta.sh
#
#   builds installatore/uscita/remotix-install(-gui); writes their sha256 next to them and inside
#   install.sh (like packaging/archivio/pubblica.sh script);
#   /media/REMOTIX/vm17/t9/archivio/ = copy of the T8 archive + this engine + install.sh,
#   served on 127.0.0.1:8727 (from the VM: 10.0.2.2:8727). ⚠ The T8 archive (8717) is not touched:
#   other benches use it.
#   /media/REMOTIX/vm17/t9/: t9-vm.sh, the answer files, the cloud-init template; and 17-vm.sh
#   updated (RX_VM_SEME, RX_VM_RETE, RX_VM_CATTURA: without them, it does what it used to).
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
INST=$ALBERO/installatore
S=nicfio@192.168.0.2
V=/media/REMOTIX/vm17
U=$INST/uscita

"$INST/costruisci.sh" >/dev/null
# the build with the window (DECISIONI §10.19): same source, "gui" tag
"$INST/costruisci.sh" gui >/dev/null
(cd "$U" && sha256sum remotix-install >remotix-install.sha256 && sha256sum remotix-install-gui >remotix-install-gui.sha256)
sed -e "s/^SHA256_MOTORE=''\$/SHA256_MOTORE='$(cut -d' ' -f1 "$U/remotix-install.sha256")'/" \
	-e "s/^SHA256_MOTORE_GUI=''\$/SHA256_MOTORE_GUI='$(cut -d' ' -f1 "$U/remotix-install-gui.sha256")'/" "$INST/install.sh" >"$U/install.sh"
(cd "$U" && sha256sum install.sh >install.sh.sha256)
echo "engine $(cut -c1-16 "$U/remotix-install.sha256")…, install.sh $(cut -c1-16 "$U/install.sh.sha256")…"

ssh -o BatchMode=yes $S "mkdir -p $V/t9 && rm -rf $V/t9/archivio && cp -a $V/archivio $V/t9/archivio" 2>&1 | grep -v tput || true
scp -q "$U/remotix-install" "$U/remotix-install.sha256" "$U/remotix-install-gui" "$U/remotix-install-gui.sha256" $S:$V/t9/archivio/motore/
scp -q "$U/install.sh" "$U/install.sh.sha256" $S:$V/t9/archivio/
scp -q "$QUI/t9-vm.sh" "$QUI/t9-rete.py" "$QUI"/risposte-*.conf "$QUI/cloud-init-r21.yaml" "$QUI/t9-gui.sh" $S:$V/t9/
# atomically: other benches may be reading 17-vm.sh right now (bash reads it in pieces)
scp -q "$ALBERO/banchi/17-distro/17-vm.sh" $S:$V/.17-vm.sh.nuovo
ssh -o BatchMode=yes $S "chmod 755 $V/.17-vm.sh.nuovo && mv $V/.17-vm.sh.nuovo $V/17-vm.sh" 2>&1 | grep -v tput || true
# ⚠ two separate ssh calls: with the start on the same line, pkill -f finds ssh's shell (which contains
# "http.server 8727") and kills it; [h] keeps it from finding itself
ssh -o BatchMode=yes $S "pkill -f '[h]ttp.server 8727'" || true
ssh -o BatchMode=yes $S "
(setsid nohup python3 -m http.server 8727 --bind 127.0.0.1 --directory $V/t9/archivio >$V/t9/http-8727.log 2>&1 </dev/null &)
sleep 1
curl -s -o /dev/null -w 'T9 archive: %{http_code}\n' http://127.0.0.1:8727/install.sh" 2>&1 | grep -v tput
