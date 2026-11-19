#!/bin/bash
#
# box.sh (banco VM) - the same face as boxes/box.sh for the checks of prove/, but the "box" is one of the four QEMU virtual
# machines of server/vm-radeon.sh (Ubuntu really installed, a real display manager, AppArmor, snap). Chosen with RX_BANCO=vm
# (lib.py then looks for box.sh HERE instead of in boxes/). The checks keep saying gnome|kde|xfce|lxqt:
#   gnome=ubuntu (ssh 2341, REMOTIX 8841)  kde=kubuntu (2342, 8842)  xfce=xubuntu (2343, 8843)  lxqt=lubuntu (2344, 8844)
#
#   ssh <de> [cmd...]       a command inside the VM AS ROOT, by ssh as root with the bench key (no sudo: sudo would write every command line,
#                           typed secrets of the checks included, into the VM's journal). stdin goes through to the command.
#   rootkey <de>            ONCE per VM: puts vmkey.pub in /root/.ssh/authorized_keys (through `prova` + sudo, the only use of sudo here).
#                           Idempotent; says "bench key installed for root" when it had to write it. The key STAYS in the VM.
#   install <de> <x.deb>    copy the .deb in and `apt-get install -y --reinstall` it. No 10-box-port.conf: the VM keeps 7447
#                           inside and the host forwards 884x to it.
#   status                  the four VMs: is the VM process running (vm-radeon.sh stato)
#   reset <de>              NOT AVAILABLE on the VMs (see fresh-vm.sh for the way to a clean state inside a running VM)
#
# Only ONE VM is switched on with the Radeon at a time: the others do not answer. Env: VM_ROOT (default /media/REMOTIX-UBUNTU/vm-radeon),
# VM_PASS (default prova2026).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
VM_ROOT=${VM_ROOT:-/media/REMOTIX-UBUNTU/vm-radeon}
PASS=${VM_PASS:-prova2026}

ok()  { printf 'OK   %s\n' "$*"; }
die() { printf 'FAIL %s\n' "$*"; exit 1; }

choose() {  # sets DE, NAME, PSSH, PRX
	DE=${1:-}
	case $DE in
	gnome) NAME=ubuntu;  PSSH=2341; PRX=8841 ;;
	kde)   NAME=kubuntu; PSSH=2342; PRX=8842 ;;
	xfce)  NAME=xubuntu; PSSH=2343; PRX=8843 ;;
	lxqt)  NAME=lubuntu; PSSH=2344; PRX=8844 ;;
	*) die "desktop \"$DE\": xfce|lxqt|gnome|kde" ;;
	esac
}
ssh_root() {
	ssh -i "$VM_ROOT/$NAME/vmkey" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
		-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR root@127.0.0.1 "$@"
}
ssh_vm() {
	ssh -i "$VM_ROOT/$NAME/vmkey" -p "$PSSH" -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
		-o UserKnownHostsFile=/dev/null -o LogLevel=ERROR prova@127.0.0.1 "$@"
}
# as_root <cmd>: `bash -c <cmd>` as root; stdin of this script (or nothing, if it is a terminal) goes to the command
as_root() {
	local q; q=$(printf '%q' "$1")
	if [ -t 0 ]; then exec </dev/null; fi
	ssh_root "bash -c $q"
}

verb=${1:-}; [ -n "$verb" ] || die "usage: box.sh ssh|install|status|reset ..."; shift

if [ "$verb" = status ]; then
	for d in gnome kde xfce lxqt; do
		choose "$d"
		s=$("$VM_ROOT/vm-radeon.sh" stato "$NAME" 2>&1 | head -1 || true)
		printf '%-9s %-40s ssh %s  REMOTIX %s\n' "$NAME" "${s:-?}" "$PSSH" "$PRX"
	done
	ok "status"; exit 0
fi

choose "${1:-}"; shift

case $verb in
rootkey)
	if ssh_root true 2>/dev/null; then ok "root key already there in $NAME"; exit 0; fi
	pub=$(cat "$VM_ROOT/$NAME/vmkey.pub")
	printf '%s\n' "$PASS" | ssh_vm "sudo -S -p '' sh -c 'install -d -m 700 /root/.ssh && touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys && { [ -z \"\$(tail -c1 /root/.ssh/authorized_keys)\" ] || echo >> /root/.ssh/authorized_keys; } && { grep -qxF \"$pub\" /root/.ssh/authorized_keys || echo \"$pub\" >> /root/.ssh/authorized_keys; }'" >/dev/null 2>&1 \
		|| die "cannot install the bench key for root in $NAME (prova + sudo)"
	ssh_root true 2>/dev/null || die "root ssh does not work in $NAME after installing the key (sshd PermitRootLogin?)"
	ok "bench key installed for root in $NAME" ;;
ssh)
	[ $# -gt 0 ] || die "ssh: a command is needed"
	as_root "$*" ;;
install)
	deb=${1:?path to .deb}; [ -f "$deb" ] || die "no such file: $deb"
	f=/tmp/$(basename "$deb")
	ssh_root "cat > $f" < "$deb" || die "cannot copy $deb into $NAME"
	if as_root "apt-get update -qq >/dev/null 2>&1; DEBIAN_FRONTEND=noninteractive apt-get install -y --reinstall $f" </dev/null 2>&1 | tail -n 25 | sed 's/^/     /' \
		&& [ "${PIPESTATUS[0]}" -eq 0 ]; then
		ok "$(basename "$deb") installed in $NAME (the service is as the package leaves it)"
	else die "apt install of $(basename "$deb") failed in $NAME"; fi ;;
reset) die "reset does not exist on the VMs (vm-radeon.sh ripristina needs the VM off and drops its state): use prove/banco-vm/fresh-vm.sh $DE" ;;
*) die "unknown verb: $verb" ;;
esac
