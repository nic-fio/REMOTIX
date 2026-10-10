#!/bin/bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
#
# 17-t4-alma.sh — phase 17, T4-T5: the engine FOR REAL on Alma 10 from the ISO (firewalld on with
# 7447 closed, §7.2), one VM only:
#   A. test plan with a THIRD-PARTY repository (EPEL + CRB, dnf), a package from there (htop, via
#      dnf: resolved set, our own folder, gpgcheck), the files, a unit, the port in the firewall
#      (firewalld over D-Bus, runtime and permanent) and LAST a group with a user that does not exist:
#      everything is done, the last step fails, and the operation is ROLLED BACK entirely (R28 for real).
#      Fingerprints of /etc, of the packages and of the firewall before and after;
#   B. the same plan with a real user: CONFIRMED, and from outside the port open, runtime and permanent.
#
#   (on the server)  sg kvm -c 'bash 17-t4-alma.sh alma10-gnome-iso <remotix-install>'
set -uo pipefail
m=${1:?macchina}; MOT=${2:?remotix-install}
R=/media/REMOTIX/vm17
T4=${T4:-$R/t4}
E=$T4/esiti/$m
V="bash $R/17-vm.sh"
FOTO=${FOTO:-iso}
vm() { $V ssh "$m" "$@"; }
fine() { echo "==> powering off and back to \"$FOTO\""; $V ferma "$m" >/dev/null 2>&1; $V torna "$m" "$FOTO" >/dev/null 2>&1; }
mkdir -p "$E"; rm -f "$E"/*
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already running"; exit 2; fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
trap fine EXIT
echo "==> $m: \"$FOTO\" snapshot, power on"
$V torna "$m" "$FOTO" || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
$V ssh "$m" "cat > /tmp/remotix-install" <"$MOT"
vm "sudo install -m 755 /tmp/remotix-install /root/remotix-install; rpm -q dnf; firewall-cmd --state"

impronta() {
	vm "sudo sh -c 'find /etc -xdev -type f -exec sha256sum {} + | sort; rpm -qa | sort; firewall-cmd --list-all; firewall-cmd --permanent --list-all; ls /etc/yum.repos.d'" >"$E/impronta-$1.txt" 2>&1
	echo "   fingerprint \"$1\": $(wc -l <"$E/impronta-$1.txt") lines"
}
impronta prima

echo "==> A. EPEL repository + htop + file + unit + firewall, then an impossible group: everything is rolled back"
vm "cd /tmp && sudo /root/remotix-install check" >"$E/verifica.txt" 2>&1; echo "   check: exit $?"
grep -E 'firewall|RX-FW|deposito' "$E/verifica.txt" | head -8 | sed 's/^/   /'
vm "cd /tmp && sudo /root/remotix-install plan --extra-repos epel --packages htop --open-firewall --users nessuno-si-chiama-cosi --output /root/piano-a.json && sudo /root/remotix-install approve /root/piano-a.json" >"$E/piano-a.txt" 2>&1
echo "   plan: exit $? — $(grep -c '^[0-9]*\. ' "$E/piano-a.txt") steps"
T0=$(date +%s)
vm "sudo /root/remotix-install apply /root/piano-a.json" >"$E/applica-a.txt" 2>&1
echo "   apply: exit $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/applica-a.txt")"
grep -E ': (DONE|FAILED|ROLLED_BACK|ROLLBACK_FAILED)' "$E/applica-a.txt" | cut -c1-160 | sed 's/^/   /'
vm "sudo sh -c 'grep -h COMMAND /var/lib/remotix/operations/*/log.jsonl' | sed 's/.*detail\":\"//; s/\"}//' | cut -c1-200" >"$E/comandi-a.txt" 2>&1
sed 's/^/   /' "$E/comandi-a.txt"
impronta dopo-a
diff "$E/impronta-prima.txt" "$E/impronta-dopo-a.txt" >"$E/diff-a.txt"
echo "   R28: $(grep -c '^[<>]' "$E/diff-a.txt") lines differ between \"before\" and \"after the rollback\":"
grep '^[<>]' "$E/diff-a.txt" | cut -c1-160 | head -30 | sed 's/^/      /'

echo "==> B. the same plan with a real user: CONFIRMED, and the port open from outside"
vm "cd /tmp && sudo /root/remotix-install plan --extra-repos epel --packages htop --open-firewall --users nicfio --output /root/piano-b.json && sudo /root/remotix-install approve /root/piano-b.json" >"$E/piano-b.txt" 2>&1
vm "sudo /root/remotix-install apply /root/piano-b.json" >"$E/applica-b.txt" 2>&1
echo "   apply: exit $? — $(grep -E '^operation ' "$E/applica-b.txt")"
vm "echo runtime: \$(sudo firewall-cmd --query-port=7447/tcp) \$(sudo firewall-cmd --query-port=7447/udp); echo permanent: \$(sudo firewall-cmd --permanent --query-port=7447/tcp) \$(sudo firewall-cmd --permanent --query-port=7447/udp); rpm -q htop epel-release; dnf repolist --enabled | grep -E 'crb|epel'; systemctl is-enabled remotix-prova-motore.service; id nicfio" >"$E/b-fuori.txt" 2>&1
sed 's/^/   /' "$E/b-fuori.txt"
