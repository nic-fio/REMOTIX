#!/bin/bash
set -u
NAME=rete11-kde; PORT=8512; PW=provanic2026; LOG=/var/lib/rete11/registro.log
cd /media/REMOTIX/rete11
X() { podman exec "$NAME" sh -c "$1"; }
bash 11-start.sh start kde >/dev/null 2>&1; bash 11-start.sh product kde >/dev/null 2>&1
podman cp /usr/bin/getfacl "$NAME":/usr/bin/getfacl
bash 11-start.sh server kde | tail -1
X "rm -f /var/lib/remotix/render-grants; userdel -r aclk 2>/dev/null; useradd -m -s /bin/bash aclk && echo aclk:$PW | chpasswd"
U=$(X "id -u aclk"); X "loginctl enable-linger aclk; systemctl start user@$U"
X "python3 /opt/remotix/01-b3-client.py --address 127.0.0.1 --port $PORT --user aclk --password $PW --stay 30 > /tmp/c.log 2>&1 &"
sleep 32
echo "ACL: $(X "getfacl -p /dev/dri/renderD128 | grep '^group:[^:]'")  grants: $(X 'cat /var/lib/remotix/render-grants')"
echo "dbus tools: $(X 'command -v qdbus6 qdbus gdbus busctl | tr "\n" " "')"
X "runuser -u aclk -- env XDG_RUNTIME_DIR=/run/user/$U DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$U/bus qdbus6 org.kde.Shutdown /Shutdown org.kde.Shutdown.logout" 2>&1 | head -3
sleep 20
echo "processes of aclk 20 s after logout: $(X 'pgrep -u aclk -a | cut -c1-60 | tr "\n" ";"')"
sleep 70
echo "processes of aclk 90 s after logout: $(X 'pgrep -u aclk -a | cut -c1-60 | tr "\n" ";"')"
X "grep -a 'aclk' $LOG | tail -8 | cut -c1-200"
X "grep -a -E 'REAPED|REMOVED|ended|Logout' $LOG | grep -a -i aclk | cut -c1-170 | tail -5"
echo "ACL after: $(X "getfacl -p /dev/dri/renderD128 | grep '^group:[^:]'")  grants: $(X 'cat /var/lib/remotix/render-grants')"
echo "manager: $(X "systemctl show -p MainPID --value user@$U")  kwin: $(X 'pgrep -u aclk -x kwin_wayland')"
X "loginctl disable-linger aclk; loginctl terminate-user aclk; sleep 1; userdel -r aclk"
podman stop -t 5 "$NAME" >/dev/null
