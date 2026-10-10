#!/bin/bash
#
# 17-t1c-installa.sh — phase 17, step T1c: REMOTIX installed BY HAND in a VM
# from `17-vm.sh`, family by family, and started as a service on 7447.
#
#   (on the server, as nicfio)
#   bash 17-t1c-installa.sh <machine> <target> [prodotto|diag]
#     <machine>    debian13-gnome, ubuntu2604-gnome, fedora44-gnome, arch-kde, …
#     <target>     the binary's folder in $T1C/bin/ (debian13, ubuntu2604,
#                  fedora44, arch, tumbleweed, leap16, alma10)
#     diag         the DIAGNOSTIC binary in $T1C/diag/<target>: the same
#                  source with -DCOPIA_ZERO=0 (see below).  ⛔ It is NOT the product.
#
# ⭐ This is not the installer (T4-T5): it is the LIST of manual steps that the
#    ported product wants, written in one place only, and which T3 turns into
#    the package dependencies.  Every `case` below is a line of §13.2.
# ⛔ `src/provisiona.sh` is NOT used: it is a BENCH provisioner (§4.4) and, outside
#    Debian, breaks silently — it always installs `remotix.pam` (Debian,
#    `@include`) in /etc/pam.d, and its check only looks for
#    "pam_systemd", so it says "⭐ the machine is in the state the product
#    expects" on Fedora and Arch where nobody would get in.  `[M]` 29 Sep.
#
# ⚠ The diagnostic binary: in the VMs the GPU is `virtio_gpu` without 3D and
#   Mutter/KWin render in software.  The product first asks for the GPU
#   path (DMA-BUF with mandatory modifier, `cattura.c:1487`), the
#   compositor has no modifiers to offer, the PipeWire negotiation dies
#   with "no more input formats" and the fallback to MEMORY kicks in only AFTER a
#   frame (`figlio.c:5362`) — which never arrives.  `[M]` 29 Sep, the same
#   on Debian 13 (GNOME 48), Ubuntu 26.04 (GNOME 50) and Arch (KDE).  With the
#   diagnostic binary (memory from the start) the rest of the chain can be tested.
set -euo pipefail
m=${1:?machine}; b=${2:?target}; q=${3:-prodotto}
R=/media/REMOTIX/vm17
T1C=${T1C:-$R/t1c}
VM="bash $R/17-vm.sh ssh $m"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}

case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
tumbleweed-*) n=5;; leap16-*) n=6;; alma10-*) n=7;; *) echo "unknown machine: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PORTA_SSH=$((2300 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
if [ "$q" = diag ]; then BIN=$T1C/diag/$b/remotix; else BIN=$T1C/bin/$b/remotix; fi

echo "==> $m: copying binary ($q), page and system files"
$VM 'mkdir -p /tmp/t1c'
# shellcheck disable=SC2086
scp -q $O -P "$PORTA_SSH" "$BIN" "$T1C/pagina.html" "$T1C"/remotix.pam* \
	"$T1C/remotix-niente-spegnimento.rules" "$T1C/remotix-tasti.conf" nicfio@localhost:/tmp/t1c/

# ── 1. the runtime dependencies, family by family ────────────────────────────
echo "==> $m: runtime dependencies"
case $m in
debian13-*)
	: ;;   # the desktop group already brings libavcodec61 (with libx264), pipewire, libei
ubuntu2604-*)
	# ubuntu-desktop does not bring libavcodec; and "vanilla" GNOME (session `gnome`,
	# which REMOTIX starts) is in the gnome-session package (§4.6, D8)
	$VM 'sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q libavcodec62 libswscale9 libavutil60' ;;
fedora44-*)
	: ;;   # the Workstation group already brings libavcodec-free (WITHOUT libx264/libx265)
alma10-*)
	# ffmpeg-free is in EPEL 10 (with CRB), not in AppStream
	$VM 'sudo dnf -y -q install epel-release && sudo dnf config-manager --set-enabled crb && sudo dnf -y -q install libavcodec-free libavutil-free libswscale-free' ;;
arch-*)
	: ;;
tumbleweed-*)
	$VM 'sudo zypper -n install libavcodec63 libavutil61 libswscale10' ;;
leap16-*)
	$VM 'sudo zypper -n install libavcodec61 libavutil59 libswscale8 libpipewire-0_3-0 libva2 libei1' ;;
esac
# firewalld: ON after the desktop group on Fedora/Alma (public zone, port closed)
$VM 'if systemctl is-active -q firewalld; then sudo firewall-cmd -q --permanent --add-port=7447/tcp --add-port=7447/udp && sudo firewall-cmd -q --reload; fi'
case $m in
*-xfce|*-lxqt)
	case $m in
	debian13-*|ubuntu2604-*) $VM 'sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q labwc' ;;
	fedora44-*) $VM 'sudo dnf -y -q install labwc' ;;
	arch-*) $VM 'sudo pacman -S --noconfirm --needed labwc' ;;
	# ⚠ xfce4-session 4.20 is X11: under labwc it wants Xwayland, and the xfce pattern
	#   of Leap 16 does not bring it (`[M]` 29 Sep: "Cannot find Xwayland binary")
	tumbleweed-*|leap16-*) $VM 'sudo zypper -n install labwc xwayland' ;;
	esac ;;
esac
MANCANO=$($VM "ldd /tmp/t1c/remotix | grep 'not found' || true")
if [ -n "$MANCANO" ]; then echo "⛔ missing libraries:"; echo "$MANCANO"; exit 1; fi

# ── 2. the product, the family's PAM file, the denied users ─────────────────
echo "==> $m: product and PAM"
case $m in
debian13-*|ubuntu2604-*) PAM=remotix.pam;        DOVE=/etc/pam.d/remotix ;;
fedora44-*|alma10-*)     PAM=remotix.pam.fedora; DOVE=/etc/pam.d/remotix ;;
arch-*)                  PAM=remotix.pam.arch;   DOVE=/etc/pam.d/remotix ;;
tumbleweed-*|leap16-*)   PAM=remotix.pam.suse;   DOVE=/usr/lib/pam.d/remotix ;;
esac
$VM "sudo systemctl stop remotix-t1c 2>/dev/null; sudo loginctl terminate-user prova 2>/dev/null; true
sudo install -D -m 755 /tmp/t1c/remotix /opt/remotix/remotix
sudo install -D -m 644 /tmp/t1c/pagina.html /opt/remotix/pagina.html
sudo install -D -m 644 /tmp/t1c/$PAM $DOVE
[ -f /etc/remotix/utenti-negati ] || { sudo install -D -m 644 /dev/null /etc/remotix/utenti-negati; echo root | sudo tee /etc/remotix/utenti-negati >/dev/null; }
command -v restorecon >/dev/null && sudo restorecon -R /opt/remotix /etc/remotix $DOVE || true"

# ── 3. polkit, logind, sleep: the three belts of provisiona.sh §3 ────────────
echo "==> $m: polkit, logind, sleep"
$VM 'sudo install -D -m 644 /tmp/t1c/remotix-niente-spegnimento.rules /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
sudo install -D -m 644 /tmp/t1c/remotix-tasti.conf /etc/systemd/logind.conf.d/remotix-tasti.conf
sudo mkdir -p /etc/systemd/sleep.conf.d
printf "[Sleep]\nAllowSuspend=no\nAllowHibernation=no\nAllowSuspendThenHibernate=no\nAllowHybridSleep=no\n" | sudo tee /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf >/dev/null
sudo systemctl restart polkit 2>/dev/null || true
sudo systemctl reload systemd-logind 2>/dev/null || true'

# ── 4. the test user, in the groups READ BY THE GPU NODES ────────────────────
echo "==> $m: test user"
$VM "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card* /dev/dri/renderD*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | paste -sd,)
[ -n \"\$G\" ] && sudo usermod -aG \"\$G\" prova
sudo loginctl enable-linger prova
id prova"

# ── 5. the service: transient system unit, like src/riavvia-7900.sh ─────────
echo "==> $m: REMOTIX as a service on 7447"
$VM 'sudo mkdir -p /var/lib/remotix
sudo systemd-run --unit=remotix-t1c --collect --working-directory=/opt/remotix \
  --property=KillMode=mixed --property=LimitRTPRIO=20 --property=LimitNICE=-11 \
  /opt/remotix/remotix --indirizzo 0.0.0.0 --nome localhost --porta 7447 \
  --certificati /var/lib/remotix/certificati --pagina /opt/remotix/pagina.html \
  --ban-file /var/lib/remotix/ban >/dev/null
sleep 2; systemctl is-active remotix-t1c; sudo journalctl -u remotix-t1c -o cat --no-pager | grep -E "ready:|PAM" | tail -2'
