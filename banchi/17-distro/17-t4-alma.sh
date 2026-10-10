#!/bin/bash
#
# ⛔ STORIA (10 ott 2026, DECISIONI §10.36): questo banco prova un installatore che non c'è più —
#   piano/approva/applica separati, archivio firmato e install.sh, archivi di terzi, firewall e
#   cinture messi dal motore, file di risposte. Oggi: un .run, `install` con la domanda [y/N], e
#   REMOTIX che non modifica il sistema. Resta come storia delle prove del 29 set - 1 ott 2026; il giro
#   vero è banchi/17-distro/17-t10.sh. Non si lancia.
#
# 17-t4-alma.sh — fase 17, T4-T5: il motore DAL VERO su Alma 10 dall'ISO (firewalld acceso con
# la 7447 chiusa, §7.2), una VM sola:
#   A. piano di prova con un deposito di TERZI (EPEL + CRB, dnf), un pacchetto da lì (htop, via
#      dnf: insieme risolto, cartella nostra, gpgcheck), i file, un'unità, la porta nel firewall
#      (firewalld sul D-Bus, vive e permanenti) e per ULTIMO un gruppo con un utente che non esiste:
#      tutto si fa, l'ultimo passo fallisce, e l'operazione si ANNULLA per intero (R28 dal vero).
#      Impronte di /etc, dei pacchetti e del firewall prima e dopo;
#   B. lo stesso piano con un utente vero: CONFERMATA, e da fuori la porta aperta vive e permanente.
#
#   (sul server)  sg kvm -c 'bash 17-t4-alma.sh alma10-gnome-iso <remotix-install>'
set -uo pipefail
m=${1:?macchina}; MOT=${2:?remotix-install}
R=/media/REMOTIX/vm17
T4=${T4:-$R/t4}
E=$T4/esiti/$m
V="bash $R/17-vm.sh"
FOTO=${FOTO:-iso}
vm() { $V ssh "$m" "$@"; }
fine() { echo "==> spengo e torno a «$FOTO»"; $V ferma "$m" >/dev/null 2>&1; $V torna "$m" "$FOTO" >/dev/null 2>&1; }
mkdir -p "$E"; rm -f "$E"/*
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m e' gia' accesa"; exit 2; fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ gia' 4 VM accese"; exit 2; }
trap fine EXIT
echo "==> $m: foto «$FOTO», accensione"
$V torna "$m" "$FOTO" || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
$V ssh "$m" "cat > /tmp/remotix-install" <"$MOT"
vm "sudo install -m 755 /tmp/remotix-install /root/remotix-install; rpm -q dnf; firewall-cmd --state"

impronta() {
	vm "sudo sh -c 'find /etc -xdev -type f -exec sha256sum {} + | sort; rpm -qa | sort; firewall-cmd --list-all; firewall-cmd --permanent --list-all; ls /etc/yum.repos.d'" >"$E/impronta-$1.txt" 2>&1
	echo "   impronta «$1»: $(wc -l <"$E/impronta-$1.txt") righe"
}
impronta prima

echo "==> A. deposito EPEL + htop + file + unità + firewall, poi un gruppo impossibile: si annulla tutto"
vm "cd /tmp && sudo /root/remotix-install check" >"$E/verifica.txt" 2>&1; echo "   verifica: uscita $?"
grep -E 'firewall|RX-FW|deposito' "$E/verifica.txt" | head -8 | sed 's/^/   /'
vm "cd /tmp && sudo /root/remotix-install plan --extra-repos epel --packages htop --open-firewall --users nessuno-si-chiama-cosi --output /root/piano-a.json && sudo /root/remotix-install approve /root/piano-a.json" >"$E/piano-a.txt" 2>&1
echo "   piano: uscita $? — $(grep -c '^[0-9]*\. ' "$E/piano-a.txt") passi"
T0=$(date +%s)
vm "sudo /root/remotix-install apply /root/piano-a.json" >"$E/applica-a.txt" 2>&1
echo "   applica: uscita $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/applica-a.txt")"
grep -E ': (FATTA|FALLITA|ANNULLATA|ANNULLAMENTO_FALLITO)' "$E/applica-a.txt" | cut -c1-160 | sed 's/^/   /'
vm "sudo sh -c 'grep -h COMMAND /var/lib/remotix/operations/*/log.jsonl' | sed 's/.*detail\":\"//; s/\"}//' | cut -c1-200" >"$E/comandi-a.txt" 2>&1
sed 's/^/   /' "$E/comandi-a.txt"
impronta dopo-a
diff "$E/impronta-prima.txt" "$E/impronta-dopo-a.txt" >"$E/diff-a.txt"
echo "   R28: $(grep -c '^[<>]' "$E/diff-a.txt") righe diverse fra «prima» e «dopo l'annullamento»:"
grep '^[<>]' "$E/diff-a.txt" | cut -c1-160 | head -30 | sed 's/^/      /'

echo "==> B. lo stesso piano con un utente vero: CONFERMATA, e la porta aperta da fuori"
vm "cd /tmp && sudo /root/remotix-install plan --extra-repos epel --packages htop --open-firewall --users nicfio --output /root/piano-b.json && sudo /root/remotix-install approve /root/piano-b.json" >"$E/piano-b.txt" 2>&1
vm "sudo /root/remotix-install apply /root/piano-b.json" >"$E/applica-b.txt" 2>&1
echo "   applica: uscita $? — $(grep -E '^operation ' "$E/applica-b.txt")"
vm "echo vive: \$(sudo firewall-cmd --query-port=7447/tcp) \$(sudo firewall-cmd --query-port=7447/udp); echo permanente: \$(sudo firewall-cmd --permanent --query-port=7447/tcp) \$(sudo firewall-cmd --permanent --query-port=7447/udp); rpm -q htop epel-release; dnf repolist --enabled | grep -E 'crb|epel'; systemctl is-enabled remotix-prova-motore.service; id nicfio" >"$E/b-fuori.txt" 2>&1
sed 's/^/   /' "$E/b-fuori.txt"
