#!/bin/sh
# common.sh — one-time build steps of the box (Ubuntu 26.04):
#   common.sh <ssh port> <sshd unit>
# boot into multi-user (no display manager: the box has no monitor), sshd on 127.0.0.1 and
# on the box's port, the key folder, the alignment of the GPU groups, the persistent journal.
set -eu
PORT=$1; SSHD=$2
systemctl set-default multi-user.target
mkdir -p /etc/ssh/sshd_config.d /root/.ssh
chmod 700 /root/.ssh
printf 'Port %s\nListenAddress 127.0.0.1\nPermitRootLogin prohibit-password\n' "$PORT" > /etc/ssh/sshd_config.d/box.conf
ssh-keygen -A
# journal on persistent storage, size bounded
mkdir -p /var/log/journal /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=persistent\nSystemMaxUse=512M\n' > /etc/systemd/journald.conf.d/box.conf
cat > /usr/local/sbin/box-gruppi <<'GRUPPI'
#!/bin/sh
# box-gruppi — aligns the box's `video` and `render` groups to the groups of the host's NODES
# (card0, renderD128). On the real machine the nodes are born with the local groups (udev); in a box
# they come in with the host's numbers, and without this step no group of the box owns them —
# and the installer, which reads the groups FROM THE NODES (DECISIONI §7.21), would not know whom to enroll.
# The nodes that also come in with their real name (renderD129…, the Radeon) have the same numbers: they follow.
set -eu
allinea() {  # allinea <node> <group>
	N=$1; GR=$2
	[ -e "$N" ] || { echo "t10: $N is missing, the GPU did not come in"; return 0; }
	G=$(stat -c %g "$N")
	A=$(getent group "$G" | cut -d: -f1 || true)
	if [ "$A" = "$GR" ]; then echo "t10: $GR is already $G"; return 0; fi
	if [ -n "$A" ]; then
		groupmod -g "1$G" "$A" || true
		find / -xdev -gid "$G" -exec chgrp "1$G" {} + 2>/dev/null || true
		echo "t10: the files of group $A followed the group to 1$G"
	fi
	groupmod -g "$G" "$GR" 2>/dev/null || groupadd -g "$G" "$GR"
	echo "t10: $GR aligned to $G (it belonged to ${A:-nobody})"
}
allinea /dev/dri/card0 video
allinea /dev/dri/renderD128 render
GRUPPI
chmod 755 /usr/local/sbin/box-gruppi
cat > /etc/systemd/system/box-gruppi.service <<'UNITA'
[Unit]
Description=Box — align the graphics card group to the host's
Before=systemd-logind.service basic.target polkit.service
DefaultDependencies=no
After=sysinit.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/box-gruppi

[Install]
WantedBy=sysinit.target
UNITA
systemctl enable box-gruppi.service "$SSHD"
