#!/bin/bash
# 19-nv-prova-contenitore.sh — the NVIDIA bench tested ON THE LAPTOP, in a podman container
# with systemd and WITHOUT a GPU: all the steps that do not touch the GPU, for real.
#
#   bash banchi/19-nvidia/19-nv-prova-contenitore.sh [debian13|ubuntu2604]
#
# What to expect (without a GPU this is correct):
#   controlli   RED ("no NVIDIA card"), but the snapshot of the machine is taken
#   dipendenze  GREEN: XFCE, labwc, tools, Firefox ESR, Chrome, the bench user
#   remotix     the installer REFUSES (RX-GPU-003: no card) ⇒ the .deb with the package manager,
#               the server starts and listens (it declares it cannot encode)
#   codifica    RED: "none", code 3
#   19-confronto: it COMPILES (the run needs the GPU)
#   suite       NOT LOOKED AT (no NVIDIA node)
#   raccogli    the archive comes back to the laptop
#   pulisci     the packages and /etc/apt go back as before: it is compared
# Needs the suitcase (`19-nvidia.sh prepara`).  The container stays on at the end to look
# inside (`podman exec -it rxnv-prova-<target> bash`); remove it with `podman rm -f`.
set -u
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
B=${1:-debian13}
case $B in
debian13) BASE=docker.io/library/debian:13 ;;
ubuntu2604) BASE=docker.io/library/ubuntu:26.04 ;;
*) echo "target: debian13 or ubuntu2604"; exit 2 ;;
esac
IMM=localhost/remotix-nv-prova-$B
NOME=rxnv-prova-$B
export CONTENITORE=$NOME
D=$QUI/19-nvidia.sh
M=/opt/remotix-nv/albero/banchi/19-nvidia/19-nv-macchina.sh

if ! podman image exists "$IMM"; then
	printf 'FROM %s\nENV DEBIAN_FRONTEND=noninteractive\nRUN apt-get update && apt-get install -y --no-install-recommends systemd systemd-sysv dbus ca-certificates iproute2 && rm -rf /var/lib/apt/lists/*\nSTOPSIGNAL SIGRTMIN+3\nCMD ["/sbin/init"]\n' "$BASE" \
		| podman build -q -t "$IMM" -f - "$QUI" >/dev/null || { echo "image not built"; exit 1; }
fi
podman rm -f "$NOME" >/dev/null 2>&1
podman run -d --name "$NOME" --systemd=always --cap-add=AUDIT_WRITE,AUDIT_CONTROL "$IMM" >/dev/null || exit 1
for _ in $(seq 1 30); do
	s=$(podman exec "$NOME" systemctl is-system-running 2>/dev/null)
	[ "$s" = running ] || [ "$s" = degraded ] && break
	sleep 1
done
echo "== $NOME: systemd $s"
x() { podman exec -i "$NOME" bash -c "$1"; }

bash "$D" manda || exit 1
x "dpkg-query -W -f='\${db:Status-Abbrev} \${Package}\n' | awk '\$1==\"ii\"{print \$2}' | sort > /root/pacchetti-inizio.txt; tar -C / -cf /root/apt-inizio.tar etc/apt"
for p in controlli dipendenze remotix codifica; do
	echo; echo "######## $p"
	x "bash $M $p"; echo ">> $p: exit $?"
done
echo; echo "######## 19-confronto: build only"
x "ALBERO=/opt/remotix-nv/albero USCITA=/var/lib/remotix-nv/confronto bash /opt/remotix-nv/albero/banchi/19-vulkan/19-confronto.sh costruisci 2>&1 | tail -n 4"
echo ">> build: exit $?"
echo; echo "######## suite"
x "bash $M suite"; echo ">> suite: exit $?"
echo; echo "######## the server, seen from inside"
x "ss -ltnu | grep -E ':7447 ' ; grep -a -E 'CANNOT ENCODE|ready' /var/lib/remotix-nv/registro.log | head -4"
bash "$D" raccogli
echo; echo "######## pulisci"
bash "$D" pulisci
echo; echo "######## the comparison with the start"
x "dpkg-query -W -f='\${db:Status-Abbrev} \${Package}\n' | awk '\$1==\"ii\"{print \$2}' | sort > /root/pacchetti-fine.txt; \
	echo \"extra packages: \$(comm -13 /root/pacchetti-inizio.txt /root/pacchetti-fine.txt | tr '\n' ' ')\"; \
	echo \"missing packages: \$(comm -23 /root/pacchetti-inizio.txt /root/pacchetti-fine.txt | tr '\n' ' ')\"; \
	mkdir -p /root/a && tar -C /root/a -xf /root/apt-inizio.tar && diff -r /root/a/etc/apt /etc/apt && echo '/etc/apt: same as before'; \
	id rxbanco 2>&1 | head -1; ls /opt/remotix-nv /var/lib/remotix-nv /etc/remotix 2>&1 | head -3"
