#!/bin/bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
#
# 17-t4-motore.sh — phase 17, T4-T5: the COMPLETE engine run on a "customer" VM.
#
#   (on the server, as nicfio)
#   sg kvm -c 'bash 17-t4-motore.sh <machine> <remotix-install> <package>'
#     e.g. bash 17-t4-motore.sh debian13-gnome $T4/remotix-install $T4/remotix_…+deb13_amd64.deb
#
# The script of §7.3 with the ENGINE in place of the manual steps of T3 (17-t3-prova.sh):
#   0. "cliente" snapshot, power on; the person "prova", ALREADY in the card node's group (R33);
#   1. fingerprint "prima" (17-t3-impronta.sh);
#   2. remotix-install check; plan --install --package; approve; apply: the engine has the
#      manager install the package (resolved set, from the cache), enrolls in the groups, turns on
#      the belts, starts the service via D-Bus, and verifies; fingerprint "installato";
#   3. a REAL browser enters and sees the desktop (17-t1c-guarda.sh, Chrome);
#   4. R43: "prova" also opens an ssh session with a process that writes the time every second;
#   5. remotix-install uninstall --purge; approve; apply: the REMOTIX sessions are closed (only
#      those), the log is walked back; fingerprint "disinstallato" and comparison with "prima";
#      the ssh session's process must still be alive;
#   6. power off and back to "cliente" (even if the test crashes).
# Evidence in $T4/esiti/<machine>/.
set -uo pipefail
m=${1:?machine}; MOT=${2:?remotix-install}; PKG=${3:?package}
R=/media/REMOTIX/vm17
T4=${T4:-$R/t4}
QUI=$(cd "$(dirname "$0")" && pwd)
E=$T4/esiti/$m
V="bash $R/17-vm.sh"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
# the family decides the fingerprint; PIANO_OPZ adds to the plan (e.g. --deposito packman on openSUSE)
IMPRONTA=17-t3-impronta.sh
case $m in
debian13|debian13-*) n=1;; ubuntu2604|ubuntu2604-*) n=2;;
fedora44|fedora44-*) n=3; IMPRONTA=17-t3-impronta-rpm.sh;;
arch|arch-*) n=4; IMPRONTA=17-t3-impronta-arch.sh;;
tumbleweed|tumbleweed-*) n=5; IMPRONTA=17-t3-impronta-rpm.sh;;
leap16|leap16-*) n=6; IMPRONTA=17-t3-impronta-rpm.sh;;
alma10|alma10-*) n=7; IMPRONTA=17-t3-impronta-rpm.sh;;
*) echo "unknown machine: $m"; exit 2;;
esac
PIANO_OPZ=${PIANO_OPZ:-}
k=0  # the "bare" machine, without desktop: R38, the engine installs it (DESKTOP=lxqt … in the environment)
case $m in *-*) case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac ;; esac
DESKTOP=${DESKTOP:-}
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
CH=$R/ssh/id_ed25519
O="-i $CH -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
vm() { $V ssh "$m" "$@"; }
impronta() { vm 'sudo bash -s' <"$QUI/$IMPRONTA" >"$E/impronta-$1.txt" 2>"$E/impronta-$1.err"
             echo "   fingerprint \"$1\": $(wc -l <"$E/impronta-$1.txt") lines"; }
# the "bare" machine has no "cliente" snapshot: it is rebuilt from the image (azzera), before and after
torna() { if [ "$k" = 0 ]; then $V azzera "$m"; else $V torna "$m" cliente; fi; }
fine() { [ -n "${OROLOGIO:-}" ] && kill "$OROLOGIO" 2>/dev/null
         echo "==> powering off and back to how it was"; $V ferma "$m" >/dev/null 2>&1; torna >/dev/null 2>&1; }

mkdir -p "$E"; rm -f "$E"/*
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already running: someone else is using it"; exit 2; fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
trap fine EXIT
echo "==> $m: \"cliente\" snapshot, power on"
torna || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }

echo "==> the person \"prova\", already in the card node's group (R33); their ssh key for R43"
vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
sudo install -d -m 700 -o prova -g prova ~prova/.ssh
sudo install -m 600 -o prova -g prova ~/.ssh/authorized_keys ~prova/.ssh/authorized_keys
ls -l /dev/dri/; id prova" | tee "$E/persone-prima.txt"
impronta prima

echo "==> the engine and the package into the VM"
# shellcheck disable=SC2086
scp -q $O -P "$PSSH" "$MOT" "$PKG" nicfio@localhost:/tmp/ || exit 1
D=/tmp/$(basename "$PKG")
vm "sudo install -m 755 /tmp/remotix-install /root/remotix-install"

echo "==> 2. check, plan, approve, apply (as root)"
vm "sudo /root/remotix-install check" >"$E/verifica.txt" 2>&1; echo "   check: exit $?"
vm "cd /tmp && sudo /root/remotix-install plan --install --package $D --users prova $PIANO_OPZ --output /root/piano.json" >"$E/piano.txt" 2>&1
echo "   plan: exit $? — $(grep -c '^[0-9]*\. ' "$E/piano.txt") steps"
vm "sudo /root/remotix-install approve /root/piano.json ${DESKTOP:+--desktop $DESKTOP}" >>"$E/piano.txt" 2>&1
[ -n "$DESKTOP" ] && vm "echo target: \$(systemctl get-default); echo display manager: \$(systemctl is-enabled display-manager.service 2>&1) \$(systemctl is-active display-manager.service 2>&1)" | sed 's/^/   before: /' 
T0=$(date +%s)
vm "sudo /root/remotix-install apply /root/piano.json" >"$E/applica.txt" 2>&1
echo "   apply: exit $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/applica.txt")"
vm "echo service: \$(systemctl is-enabled remotix) \$(systemctl is-active remotix)
echo target: \$(systemctl get-default); for u in gdm3 sddm lightdm display-manager; do echo \"\$u: \$(systemctl is-enabled \$u.service 2>&1) \$(systemctl is-active \$u.service 2>&1)\"; done; ls /usr/sbin/policy-rc.d 2>&1
echo listening on 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')
id prova
systemd-analyze cat-config systemd/logind.conf | grep -c '^HandlePowerKey=ignore' | sed 's/^/key belt in force: /'
sudo cat /var/lib/remotix/installation.json
sudo sh -c 'cat /var/lib/remotix/operations/*/certificate.txt'
sudo sh -c 'grep -h COMMAND /var/lib/remotix/operations/*/log.jsonl' | sed 's/.*detail\":\"//; s/\"}//'" >"$E/installato.txt" 2>&1
sed 's/^/   /' "$E/installato.txt" | head -60
impronta installato

echo "==> 2b. certify (read only) on the healthy machine"
vm "sudo /root/remotix-install certify; echo exit \$?" >"$E/certifica.txt" 2>&1
sed 's/^/   /' "$E/certifica.txt" | grep -E 'Certification|exit|FAIL|UNKNOWN|C-'
if [ -n "${R29:-}" ]; then
	echo "==> R29: certification on a deliberately broken machine never says GREEN"
	# all in ONE sudo: a broken PAM stack would break the following sudos too
	vm "sudo bash -s" >"$E/r29.txt" 2>&1 <<'R29'
L=$(ls /usr/lib/x86_64-linux-gnu/libx264.so.* /usr/lib64/libx264.so.* /usr/lib/libx264.so.* 2>/dev/null | head -1)
P=$(ls /etc/pam.d/remotix /usr/lib/pam.d/remotix 2>/dev/null | head -1)
c() { /root/remotix-install certify | grep -E "Certification|$1"; }
echo "-- fault 1: the REMOTIX PAM stack names a module that does not exist"; cp -a $P /root/pam-via; echo "auth required pam_non_esiste.so" >> $P; c pam-resolved; cp -a /root/pam-via $P
echo "-- fault 2: no libx264 ($L) and no VA-API: encoding fails"; mv $L /root/x264-via; c encoding; mv /root/x264-via $L
echo "-- fault 3: the service stopped by someone else"; systemctl stop remotix; c service; systemctl start remotix; sleep 3
echo "-- back to how it was"; c Certification
R29

	sed 's/^/   /' "$E/r29.txt"
fi

echo "==> 3. the real browser (Chrome) on 127.0.0.1:$PRX"
T1C=$R/t1c bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser.log" 2>&1
echo "   exit $? — $(grep -E '^T1C ' "$E/browser.log" | cut -c1-300)"

echo "==> 4. R43: an ssh session of \"prova\" with a clock"
# shellcheck disable=SC2086
ssh $O -p "$PSSH" prova@localhost 'while :; do date +%s >> ~/orologio.txt; sleep 1; done' &
OROLOGIO=$!
sleep 4
vm "loginctl list-sessions --no-legend; for s in \$(loginctl list-sessions --no-legend | awk '{print \$1}'); do echo \"\$s \$(loginctl show-session \$s -p Service -p Name -p State --value | tr '\n' ' ')\"; done
echo processes of prova: \$(pgrep -u prova | wc -l)
ps -o pid,cgroup:70,comm -u prova" >"$E/sessioni-prima.txt" 2>&1
sed 's/^/   /' "$E/sessioni-prima.txt"

echo "==> 5. uninstall --purge, approve, apply"
vm "sudo /root/remotix-install uninstall --purge --output /root/disinstalla.json" >"$E/disinstalla-piano.txt" 2>&1
echo "   plan: exit $? — $(grep -c '^[0-9]*\. ' "$E/disinstalla-piano.txt") steps"
vm "sudo /root/remotix-install approve /root/disinstalla.json" >>"$E/disinstalla-piano.txt" 2>&1
T0=$(date +%s)
vm "sudo /root/remotix-install apply /root/disinstalla.json" >"$E/disinstalla.txt" 2>&1
echo "   apply: exit $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/disinstalla.txt")"
sleep 3
vm "for s in \$(loginctl list-sessions --no-legend | awk '{print \$1}'); do echo \"\$s \$(loginctl show-session \$s -p Service -p Name -p State --value | tr '\n' ' ')\"; done
a=\$(sudo tail -1 ~prova/orologio.txt); sleep 3; b=\$(sudo tail -1 ~prova/orologio.txt); echo ssh clock: \$a → \$b
echo processes of prova: \$(pgrep -u prova | wc -l); echo gnome-shell/kwin/labwc/plasmashell of prova: \$(pgrep -u prova -c -x 'gnome-shell|kwin_wayland|labwc|plasmashell|lxqt-panel|xfce4-panel')
sudo bash -c 'n=0; for p in \$(pgrep -u prova); do grep -q user@ /proc/\$p/cgroup 2>/dev/null && tr \"\\\\0\" \"\\\\n\" < /proc/\$p/environ 2>/dev/null | grep -qE \"^(WAYLAND_)?DISPLAY=\" && n=\$((n+1)); done; echo graphical processes in the user manager: \$n'
ps -o pid,cgroup:70,comm -u prova
echo service: \$(systemctl is-enabled remotix 2>&1) \$(systemctl is-active remotix 2>&1)
(dpkg -l remotix 2>/dev/null | tail -1 || true; rpm -q remotix 2>/dev/null; pacman -Q remotix 2>/dev/null); id prova
sudo ls /var/lib/remotix /var/lib/remotix/operations; sudo sh -c 'cat /var/lib/remotix/operations/*/certificate.txt' | grep -A30 'final state: CONFIRMED\$' | tail -30" >"$E/dopo.txt" 2>&1
sed 's/^/   /' "$E/dopo.txt" | head -60
kill "$OROLOGIO" 2>/dev/null; OROLOGIO=
vm "sudo rm -f ~prova/orologio.txt"
impronta disinstallato
diff "$E/impronta-prima.txt" "$E/impronta-disinstallato.txt" >"$E/diff-R6.txt"
echo "   R6: $(grep -c '^[<>]' "$E/diff-R6.txt") lines differ between \"prima\" and \"disinstallato\" (in $E/diff-R6.txt)"
