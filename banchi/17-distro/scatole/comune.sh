#!/bin/sh
# comune.sh — i passi uguali per tutte le ricette Contenitore.* (eseguito UNA volta, alla costruzione):
#   comune.sh <porta ssh> <unità di sshd>
# avvio in multi-user (niente gestore d'accesso: la scatola non ha un monitor), sshd su 127.0.0.1 e
# sulla porta della scatola, la cartella della chiave, l'allineamento dei gruppi della scheda.
set -eu
PORTA=$1; SSHD=$2
systemctl set-default multi-user.target
mkdir -p /etc/ssh/sshd_config.d /root/.ssh
chmod 700 /root/.ssh
printf 'Port %s\nListenAddress 127.0.0.1\nPermitRootLogin prohibit-password\n' "$PORTA" > /etc/ssh/sshd_config.d/t17.conf
# Arch e openSUSE non hanno l'Include di sshd_config.d in tutte le versioni: lo si aggiunge se manca
grep -q '^Include /etc/ssh/sshd_config.d/\*.conf' /etc/ssh/sshd_config 2>/dev/null \
	|| { [ -f /etc/ssh/sshd_config ] && sed -i '1i Include /etc/ssh/sshd_config.d/*.conf' /etc/ssh/sshd_config; } \
	|| printf 'Include /etc/ssh/sshd_config.d/*.conf\n' > /etc/ssh/sshd_config
ssh-keygen -A
cat > /usr/local/sbin/t10-gruppi <<'GRUPPI'
#!/bin/sh
# t10-gruppi — allinea i gruppi `video` e `render` della scatola ai gruppi dei NODI dell'ospite
# (card0, renderD128). Sulla macchina vera i nodi nascono coi gruppi locali (udev); in una scatola
# entrano coi numeri dell'ospite, e senza questo passo nessun gruppo della scatola li possiede —
# e l'installatore, che legge i gruppi DAI NODI (DECISIONI §7.21), non saprebbe a chi iscrivere.
# I nodi che entrano anche col nome vero (renderD129…, la Radeon) hanno gli stessi numeri: seguono.
set -eu
allinea() {  # allinea <nodo> <gruppo>
	N=$1; GR=$2
	[ -e "$N" ] || { echo "t10: $N non c'e', la scheda non e' entrata"; return 0; }
	G=$(stat -c %g "$N")
	A=$(getent group "$G" | cut -d: -f1 || true)
	if [ "$A" = "$GR" ]; then echo "t10: $GR e' gia' $G"; return 0; fi
	if [ -n "$A" ]; then
		groupmod -g "1$G" "$A" || true
		find / -xdev -gid "$G" -exec chgrp "1$G" {} + 2>/dev/null || true
		echo "t10: i file del gruppo $A hanno seguito il gruppo a 1$G"
	fi
	groupmod -g "$G" "$GR" 2>/dev/null || groupadd -g "$G" "$GR"
	echo "t10: $GR allineato a $G (era di ${A:-nessuno})"
}
allinea /dev/dri/card0 video
allinea /dev/dri/renderD128 render
GRUPPI
chmod 755 /usr/local/sbin/t10-gruppi
cat > /etc/systemd/system/t10-gruppi.service <<'UNITA'
[Unit]
Description=T17 — allinea il gruppo della scheda grafica a quello dell'ospite
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
