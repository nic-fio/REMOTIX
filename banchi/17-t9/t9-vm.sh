#!/bin/bash
#
# ⛔ STORIA (10 ott 2026, DECISIONI §10.36): questo banco prova un installatore che non c'è più —
#   piano/approva/applica separati, archivio firmato e install.sh, archivi di terzi, firewall e
#   cinture messi dal motore, file di risposte. Oggi: un .run, `install` con la domanda [y/N], e
#   REMOTIX che non modifica il sistema. Resta come storia delle prove del 29 set - 1 ott 2026; il giro
#   vero è banchi/17-distro/17-t10.sh. Non si lancia.
#
# t9-vm.sh — fase 17, T9: SENZA DOMANDE (R21, R31) e SENZA RETE (R22), su una VM «cliente», un passo
# per chiamata.
#
#   (sul server, come nicfio)   sg kvm -c 'bash t9-vm.sh <macchina> <passo> [argomenti]'
#
#   accendi [rete|senza-rete]  foto «cliente», accensione. senza-rete: la rete TOLTA (restrict=on) e
#                              ogni pacchetto della scheda catturato in esiti/<m>/rete.pcap
#   motore                     il motore dall'archivio di T9 (collegata) o dal server (senza rete),
#                              e i file di risposte, in /root
#   cmd "<comando>"            un comando da root nella VM (il motore è /root/remotix-install)
#   prepara <risposte>         (collegata) prepara-fuori-linea; il pacchetto torna sul server in
#                              esiti/<m>/fuori-linea.tar
#   fuori-linea <risposte>     (senza rete) il pacchetto dentro, e installa --fuori-linea --risposte
#   r21 <risposte>             foto «cliente», un seme di cloud-init NUOVO (cloud-init-r21.yaml: utente
#                              prova, file di risposte, curl install.sh | sh), accensione; nessuno la
#                              tocca finché cloud-init non ha finito; poi il registro dell'installazione
#   guarda                     un Chrome vero entra e guarda il desktop (17-t1c-guarda.sh, labwc suo)
#   rete                       la cattura: ogni flusso che la VM ha mandato, e se ha raggiunto qualcosa
#   spegni                     spegne e torna a «cliente»
#
# ⛔ Al massimo 2 VM di questo banco e 4 in tutto; non spegne una macchina accesa da altri.
# Evidenze in /media/REMOTIX/vm17/t9/esiti/<macchina>/.
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
T9=$R/t9
E=$T9/esiti/$m
V="bash $R/17-vm.sh"
ARCH=http://10.0.2.2:8727
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
*) echo "macchina sconosciuta: $m"; exit 2;;
esac
k=0; case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PRX=$((7500 + 10 * n + k))
mkdir -p "$E"
vm() { $V ssh "$m" "$@"; }
t() { date +%H:%M:%S; }
limite() {
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m è già accesa"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ già 4 VM accese"; exit 2; }
}

case $passo in
accendi)
	modo=${1:-rete}
	limite
	rm -f "$E/rete.pcap"
	$V torna "$m" cliente >/dev/null || exit 1
	if [ "$modo" = senza-rete ]; then
		RX_VM_RETE=,restrict=on RX_VM_CATTURA=$E/rete.pcap $V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	else
		$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	fi
	vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
echo \"prova: \$(id prova)\"
curl -s -m 5 -o /dev/null -w 'archivio di T9: HTTP %{http_code}\n' $ARCH/install.sh || echo 'archivio di T9: NON raggiungibile'" | tee "$E/accendi-$modo.txt"
	;;
motore)
	for f in $T9/archivio/engine/remotix-install $T9/archivio/engine/remotix-install.sha256 $T9/risposte-*.conf; do
		vm "sudo tee /root/$(basename "$f") >/dev/null" <"$f"
	done
	# D11 semplificata (DECISIONI §10.21): il motore si verifica con lo sha256 pubblicato
	vm "sudo chmod 755 /root/remotix-install; cd /root && sudo sha256sum -c remotix-install.sha256; sudo /root/remotix-install version" | tee "$E/motore.txt"
	;;
cmd)
	vm "sudo sh -c '$*'" 2>&1 | tee -a "$E/comandi.txt"
	;;
prepara)
	r=${1:-risposte-debian.conf}
	T0=$(date +%s)
	vm "sudo rm -rf /root/fuori-linea; sudo /root/remotix-install prepare-offline --archive $ARCH --answers /root/$r --output /root/fuori-linea" 2>&1 | tee "$E/prepara.txt"
	echo "   prepara: $(( $(date +%s) - T0 )) s"
	vm "sudo tar -C /root -cf - fuori-linea" >"$E/fuori-linea.tar"
	echo "   pacchetto: $(du -h "$E/fuori-linea.tar" | cut -f1) in $E/fuori-linea.tar"
	;;
fuori-linea)
	r=${1:-risposte-debian.conf}
	pac=${PACCHETTO:-$E/fuori-linea.tar}
	vm "sudo rm -rf /root/fuori-linea && sudo tar -C /root -xf -" <"$pac"
	T0=$(date +%s); date -u +%T >"$E/finestra.txt"
	vm "sudo /root/remotix-install install --offline /root/fuori-linea --answers /root/$r" >"$E/installa.txt" 2>&1
	u=$?; date -u +%T >>"$E/finestra.txt"
	echo "   installa: uscita $u in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/installa.txt")"
	grep -E 'BLOCKED|FAILED|RX-(FUORI|RISPOSTE|PIANO)' "$E/installa.txt" | head -6 | sed 's/^/   /'
	;;
r21)
	r=${1:-risposte-debian.conf}
	limite
	S=$E/seme; rm -rf "$S"; mkdir -p "$S"
	printf 'instance-id: remotix-t9-%s-%s\nlocal-hostname: rx-%s\n' "$m" "$(date +%s)" "$m" >"$S/meta-data"
	risposte=$(sed 's/^/      /' "$T9/$r")
	python3 - "$T9/cloud-init-r21.yaml" "$S/user-data" "$m" "$(cat $R/ssh/id_ed25519.pub)" "$PAROLA" "$ARCH" "$risposte" <<'PY'
import sys
t = open(sys.argv[1]).read()
for k, v in zip(["@MACCHINA@", "@CHIAVE@", "@PAROLA@", "@ARCHIVIO@", "@RISPOSTE@"], sys.argv[3:]):
    t = t.replace(k, v)
open(sys.argv[2], "w").write(t)
PY
	genisoimage -quiet -output "$S/seme.iso" -volid cidata -joliet -rock "$S/user-data" "$S/meta-data" || exit 1
	$V torna "$m" cliente >/dev/null || exit 1
	T0=$(date +%s)
	# 17-vm.sh avvia aspetta ssh E la fine di cloud-init (cloud-init status --wait): nessuno tocca
	# la macchina prima
	RX_VM_SEME=$S/seme.iso $V avvia "$m" >"$E/avvia-r21.log" 2>&1 || { tail "$E/avvia-r21.log"; exit 1; }
	echo "   cloud-init finito in $(( $(date +%s) - T0 )) s (dall'accensione)"
	vm "sudo cloud-init status --long | head -8; echo ---; sudo cat /var/log/remotix-installa.log; echo ---; sudo grep -E 'remotix|runcmd' /var/log/cloud-init-output.log | tail -5" >"$E/r21.txt" 2>&1
	grep -E 'status:|install.sh: uscita|^operation |VERIFIED|RX-RISPOSTE|BLOCKED' "$E/r21.txt" | sed 's/^/   /'
	;;
guarda)
	mkdir -p "$T9/t1c"
	T1C=$T9/t1c T1C_EVIDENZE=$E/browser bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/guarda.txt" 2>&1
	echo "   guarda: uscita $?"; tail -4 "$E/guarda.txt" | cut -c1-300 | sed 's/^/   /'
	;;
rete)
	# la finestra dell'installazione (UTC, l'orologio del server: lo stesso della cattura), scritta
	# dal passo fuori-linea
	[ -f "$E/rete.pcap" ] || { echo "nessuna cattura"; exit 2; }
	set -- $(cat "$E/finestra.txt" 2>/dev/null)
	python3 "$T9/t9-rete.py" "$E/rete.pcap" ${1:+DAL $1 AL ${2:-$1}} | tee "$E/rete.txt"
	;;
spegni)
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; echo "   $m spenta, tornata a «cliente»"
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
