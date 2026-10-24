#!/bin/bash
# grant-test.sh <desktop> — ON THE TEST SERVER as root.  The product with
# render_grant (1.5, DECISIONS §11.4), in a box:
#   acle  first connection with a stale manager: enrol, grant, close nothing; then the desktop ends → removed
#   aclx  primary group shared (users): no grant, desktop born anyway
#   acls  grant, then the server is KILLED and the desktop ends: the next start-up sweeps it
set -u
D=$1; NAME=rete11-$D
case "$D" in gnome) PORT=8511;; kde) PORT=8512;; xfce) PORT=8513;; lxqt) PORT=8514;; esac
PW=provanic2026
OUT=/media/REMOTIX/rete11/acl-test/grant-$D.txt
cd /media/REMOTIX/rete11
# 24 Oct 2026: acl-probe.sh was never in the repository; it now lives next to this script and is
# copied into the box directory (the box mounts it read-only as /rete11).  The box images
# (rete11/<desktop>:p0) are ROOT containers: run this script as root (sudo), like 11-start.sh,
# or rootless podman does not see them.  prodotto/ must hold the binary of the branch under test (BENCH=1).
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p acl-test
cp "$HERE/acl-probe.sh" acl-probe.sh
X() { podman exec "$NAME" sh -c "$1"; }
P() { podman exec --privileged "$NAME" sh /rete11/acl-probe.sh "$1"; }
LOG=/var/lib/rete11/registro.log
state() { # user
	echo "    render node ACL: $(X "getfacl -p /dev/dri/renderD128 2>/dev/null | grep '^group:[^:]' | tr '\n' ' '")"
	echo "    render-grants: $(X "cat /var/lib/remotix/render-grants 2>/dev/null | tr '\n' ';'")"
}
login() { # user
	X "python3 /opt/remotix/01-b3-client.py --address 127.0.0.1 --port $PORT --user $1 --password $PW --stay 30 > /tmp/client-$1.log 2>&1 &"
	sleep 32
	echo "    client: $(X "grep -E 'SESSION' /tmp/client-$1.log | tail -1")"
}
stale() { # user [useradd options]
	U=$1; shift
	X "userdel -r $U 2>/dev/null; useradd -m -s /bin/bash $* $U && echo $U:$PW | chpasswd"
	UID_=$(X "id -u $U")
	X "loginctl enable-linger $U; systemctl start user@$UID_"
	M=$(X "systemctl show -p MainPID --value user@$UID_")
	echo "--- $U: $(X "id $U") — manager $M $(X "grep Groups /proc/$M/status" | tr -d '\t')"
}
end_desktop() { # user
	X "pkill -u $1 -x 'gnome-session-b|startplasma-way|labwc'"
	sleep 15
}
{
echo "=== $D grant-test  $(date -Is)  product: $(cat prodotto/VERSIONE.render_grant 2>/dev/null)"
bash 11-start.sh start "$D" >/dev/null 2>&1 || { echo "start FAILED"; exit 1; }
bash 11-start.sh product "$D" >/dev/null 2>&1 || { echo "product FAILED"; exit 1; }
podman cp /usr/bin/getfacl "$NAME":/usr/bin/getfacl
bash 11-start.sh server "$D" | tail -1
X "rm -f /var/lib/remotix/render-grants"

stale acle
login acle
echo "    manager after: $(X "systemctl show -p MainPID --value user@$UID_") (was $M)"
P acle; state
X "grep -a -E 'FIRST CONNECTION|enrolled in|CARD GRANT|NO card grant|stale|was born without' $LOG | grep acle | cut -c1-200"
echo "    → the desktop ends"
end_desktop acle
X "grep -a -E 'REAPED|REMOVED' $LOG | grep acle | cut -c1-160"
state

stale aclx -g users
X "usermod -aG video,render aclx"
login aclx
echo "    manager after: $(X "systemctl show -p MainPID --value user@$UID_") (was $M)"
P aclx; state
X "grep -a -E 'CARD GRANT|NO card grant' $LOG | grep aclx | cut -c1-220"
end_desktop aclx

stale acls
login acls
P acls | grep -E 'gnome-shell|kwin'; state
echo "    → the server is KILLED (a crash), then the desktop ends, then the server starts again"
X "systemctl kill -s KILL rete11-server"; sleep 2
end_desktop acls
state
bash 11-start.sh server "$D" | tail -1
X "grep -a -E 'card grant' $LOG | cut -c1-200"
state

echo "--- cleanup"
for U in acle aclx acls; do X "loginctl disable-linger $U; loginctl terminate-user $U; sleep 1; userdel -r $U 2>/dev/null"; done
state
podman stop -t 5 "$NAME" >/dev/null
} 2>&1 | tee "$OUT"
