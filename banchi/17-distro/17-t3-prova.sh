#!/bin/bash
#
# 17-t3-prova.sh — phase 17, T3: the NATIVE package on a "customer" VM, R4 R5 R6 in small.
#
#   (on the server, as nicfio)
#   sg kvm -c 'bash 17-t3-prova.sh <machine> <file.deb>'
#     e.g.  bash 17-t3-prova.sh debian13-gnome /media/REMOTIX/vm17/t3/remotix_…+deb13_amd64.deb
#
# The script of §7.3, without the installer (which belongs to T4-T5): the package
# manager, and the "engine steps" done BY HAND and declared as such.
# ⛔ DECISIONI §10.12: the package brings only INERT pieces (R40).
#   0. back to the "cliente" snapshot and power on;
#   1. a person on the machine, `prova`, ALREADY in the group of the cardN node
#      (usually `video`): so we see whether anyone touches it;
#   2. fingerprint "prima" (17-t3-impronta.sh);
#   3. `apt-get install ./remotix_….deb` and NOTHING ELSE (R4); fingerprint.  R40:
#      service neither enabled nor active, nothing listening on 7447, groups
#      and belts in force unchanged;
#   4. R40: `systemctl start remotix` must REFUSE with RX-INST-001;
#   5. ⚠ THE ENGINE STEPS, BY HAND (they belong to T4-T5, here only to show the
#      desktop): `prova` in the node groups, the three belts copied from
#      /usr/share/remotix/cinture/ to /etc/{polkit-1/rules.d,systemd/logind.conf.d,
#      systemd/sleep.conf.d}/, the marker /var/lib/remotix/installazione-confermata,
#      `systemctl enable --now remotix`;
#   6. a real browser enters and must see the desktop (17-t1c-guarda.sh, Chrome,
#      127.0.0.1); fingerprint;
#   7. reinstall (`--reinstall`): fingerprint equal to that of step 6 (R5);
#   8. the engine steps UNDONE by hand, then `apt-get purge remotix`: fingerprint;
#      then `apt-get autoremove --purge`: fingerprint.  The comparisons with "prima" are
#      CLASSIFIED in the report (DIRECT, INDIRECT, PRE-EXISTING: §6.6.4);
#   9. power off and back to the "cliente" snapshot.
# Evidence in $T3/esiti/<machine>/.
# ⚠ One VM only (fasi/17 §7.1): the machine is powered off even if the test crashes.
set -uo pipefail
m=${1:?machine}; DEB=${2:?.deb file}
R=/media/REMOTIX/vm17
T3=${T3:-$R/t3}
QUI=$(cd "$(dirname "$0")" && pwd)
E=$T3/esiti/$m
V="bash $R/17-vm.sh"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}

case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; *) echo ".deb family only: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
vm() { $V ssh "$m" "$@"; }
impronta() { vm 'sudo bash -s' <"$QUI/17-t3-impronta.sh" >"$E/impronta-$1.txt" 2>"$E/impronta-$1.err"
             echo "   fingerprint \"$1\": $(wc -l <"$E/impronta-$1.txt") lines"; }
fine() { echo "==> powering off and back to \"cliente\""; $V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; }
trap fine EXIT

mkdir -p "$E"; rm -f "$E"/*
# ⛔ A machine already running belongs to someone else: it is not powered off, we stop.
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then
	trap - EXIT; echo "⛔ $m is already running: someone else is using it"; exit 2
fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { trap - EXIT; echo "⛔ 4 VMs already running"; exit 2; }
echo "==> $m: \"cliente\" snapshot, power on"
$V torna "$m" cliente || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }

echo "==> the person \"prova\", already in the card node's group (R33)"
vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
ls -l /dev/dri/; id prova; id nicfio" | tee "$E/persone-prima.txt"
impronta prima

echo "==> apt-get install ./$(basename "$DEB")"
# shellcheck disable=SC2086
scp -q $O -P "$PSSH" "$DEB" nicfio@localhost:/tmp/ || exit 1
D=/tmp/$(basename "$DEB")
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $D" >"$E/installa.log" 2>&1
echo "   exit $? — $(grep -E '^[0-9]+ (upgraded|aggiornati)' "$E/installa.log")"
vm "echo enabled: \$(systemctl is-enabled remotix 2>&1); echo active: \$(systemctl is-active remotix 2>&1)
echo listening on 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')
id prova; id nicfio
systemd-analyze cat-config systemd/logind.conf | grep -c '^HandlePowerKey=ignore' | sed 's/^/key belt in force: /'
systemd-analyze cat-config systemd/sleep.conf | grep -c '^AllowSuspend=no' | sed 's/^/suspend belt in force: /'
ls /etc/polkit-1/rules.d /usr/share/polkit-1/rules.d | grep -c remotix | sed 's/^/polkit rule in force: /'
sudo ls -la /var/lib/remotix
sudo -u prova env -i LD_TRACE_LOADED_OBJECTS=1 /usr/libexec/remotix/remotix | grep -c 'not found' | sed 's/^/missing libraries (as prova, empty environment): /'" \
	>"$E/R40-installato.txt" 2>&1
sed 's/^/   /' "$E/R40-installato.txt"
impronta installato

echo "==> R40: systemctl start remotix, without installer"
vm "sudo systemctl start remotix; echo exit \$?; sleep 3; echo active: \$(systemctl is-active remotix)
echo listening on 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')
sudo journalctl -u remotix -o cat --no-pager | grep -E 'RX-INST|Failed|exit' | tail -4
echo starts: \$(systemctl show remotix -p NRestarts --value) restarts
sudo systemctl reset-failed remotix" >"$E/R40-start.txt" 2>&1
sed 's/^/   /' "$E/R40-start.txt"

echo "==> ⚠ THE ENGINE STEPS, done BY HAND (T4-T5): groups, belts, marker, enable --now"
vm "G=\$(for x in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u)
for g in \$G; do id -nG prova | tr ' ' '\\n' | grep -qx \$g || { sudo gpasswd -a prova \$g >/dev/null; echo \"group: prova + \$g\"; }; done
for d in /etc/polkit-1/rules.d /etc/systemd/logind.conf.d /etc/systemd/sleep.conf.d; do [ -d \$d ] || echo \"new folder: \$d\"; done
sudo install -D -m 644 /usr/share/remotix/cinture/50-remotix-niente-spegnimento.rules /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
sudo install -D -m 644 /usr/share/remotix/cinture/remotix-tasti.conf /etc/systemd/logind.conf.d/remotix-tasti.conf
sudo install -D -m 644 /usr/share/remotix/cinture/remotix-niente-sospensione.conf /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf
sudo systemctl reload systemd-logind; echo belts: 3 files in /etc
sudo touch /var/lib/remotix/installazione-confermata; echo marker: installazione-confermata
sudo systemctl enable --now remotix 2>&1 | tail -1; sleep 2; echo active: \$(systemctl is-active remotix)
echo listening on 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')" >"$E/passi-motore.txt" 2>&1
sed 's/^/   /' "$E/passi-motore.txt"
impronta motore

echo "==> the real browser (Chrome) on 127.0.0.1:$PRX"
T1C=$R/t1c bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser.log" 2>&1
echo "   exit $? — $(grep -E '^T1C ' "$E/browser.log" | cut -c1-300)"
vm "sudo journalctl -u remotix -o cat --no-pager | tail -40" >"$E/journal-browser.txt" 2>&1
impronta browser

echo "==> reinstall (R5)"
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --reinstall $D" >"$E/reinstalla.log" 2>&1
echo "   exit $?"
impronta reinstallato
diff "$E/impronta-browser.txt" "$E/impronta-reinstallato.txt" >"$E/diff-R5.txt"
echo "   R5: $(grep -c '^[<>]' "$E/diff-R5.txt") lines differ between \"browser\" and \"reinstallato\""

echo "==> ⚠ the engine steps UNDONE by hand, then apt-get purge remotix (R6)"
NUOVE=$(sed -n 's/^new folder: //p' "$E/passi-motore.txt" | tr '\n' ' ')
vm "sudo systemctl disable --now remotix 2>&1 | tail -1
sudo rm -f /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules /etc/systemd/logind.conf.d/remotix-tasti.conf /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf
for d in $NUOVE; do sudo rmdir \$d && echo removed folder \$d; done
sudo systemctl reload systemd-logind
sudo rm -f /var/lib/remotix/installazione-confermata" >"$E/passi-disfatti.txt" 2>&1
for g in $(sed -n 's/^group: prova + //p' "$E/passi-motore.txt"); do vm "sudo gpasswd -d prova $g >/dev/null && echo 'undone: prova - $g'"; done >>"$E/passi-disfatti.txt" 2>&1
sed 's/^/   /' "$E/passi-disfatti.txt"
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y remotix" >"$E/purge.log" 2>&1
echo "   exit $?"; grep -E '^remotix:' "$E/purge.log" | sed 's/^/   /'
vm "id prova; id nicfio; ls -la /var/lib/remotix /etc/remotix 2>&1" | tee "$E/persone-dopo.txt" | sed 's/^/   /'
impronta purge
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove --purge -y" >"$E/autoremove.log" 2>&1
impronta autoremove
for x in installato motore purge autoremove; do
	diff "$E/impronta-prima.txt" "$E/impronta-$x.txt" >"$E/diff-prima-$x.txt"
	echo "   prima → $x: $(grep -c '^[<>]' "$E/diff-prima-$x.txt") lines differ"
done
