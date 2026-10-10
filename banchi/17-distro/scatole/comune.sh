#!/bin/sh
# comune.sh — the steps common to all the Contenitore.* recipes (run ONCE, at build time):
#   comune.sh <ssh port> <sshd unit>
# boot into multi-user (no display manager: the box has no monitor), sshd on 127.0.0.1 and
# on the box's port, the key folder, the alignment of the GPU groups.
set -eu
PORTA=$1; SSHD=$2
systemctl set-default multi-user.target
mkdir -p /etc/ssh/sshd_config.d /root/.ssh
chmod 700 /root/.ssh
printf 'Port %s\nListenAddress 127.0.0.1\nPermitRootLogin prohibit-password\n' "$PORTA" > /etc/ssh/sshd_config.d/t17.conf
# Arch and openSUSE do not have the sshd_config.d Include in all versions: it is added if missing
grep -q '^Include /etc/ssh/sshd_config.d/\*.conf' /etc/ssh/sshd_config 2>/dev/null \
	|| { [ -f /etc/ssh/sshd_config ] && sed -i '1i Include /etc/ssh/sshd_config.d/*.conf' /etc/ssh/sshd_config; } \
	|| printf 'Include /etc/ssh/sshd_config.d/*.conf\n' > /etc/ssh/sshd_config
ssh-keygen -A
cat > /usr/local/sbin/t10-gruppi <<'GRUPPI'
#!/bin/sh
# t10-gruppi — aligns the box's `video` and `render` groups to the groups of the host's NODES
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
chmod 755 /usr/local/sbin/t10-gruppi
cat > /etc/systemd/system/t10-gruppi.service <<'UNITA'
[Unit]
Description=T17 — align the graphics card group to the host's
Before=systemd-logind.service basic.target polkit.service
DefaultDependencies=no
After=sysinit.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/t10-gruppi

[Install]
WantedBy=sysinit.target
UNITA
systemctl enable t10-gruppi.service "$SSHD"
