#!/bin/sh
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): it uses the plan/approve/apply commands and the engine's
#   trial plan, which no longer exist on the command line. The same actions (D-Bus, gpasswd) are tested by
#   go test and the real run (banchi/17-distro/17-t10.sh). Do not launch it.
# The engine's run FOR REAL in a Fedora 44 with systemd running (prove/Contenitore.systemd): the
# actions that talk over D-Bus (systemd1: GetUnitFileState, EnableUnitFiles, DisableUnitFiles,
# Reload) and gpasswd from the closed list. (firewalld does not start in the rootless container: see
# Contenitore.systemd.)
#   1. plan with a user → approve → apply: CONFERMATA; from outside: unit enabled, user in
#      «video», and the programs launched recorded in the log;
#   2. a plan that fails halfway (the user to put in «video» does not exist, and the step comes
#      AFTER the two files and the enabled unit): ANNULLATA, and /etc identical to before (fingerprint of the
#      contents: the folders' modification time changes anyway, adding and removing a file).
# The interruption tests (process killed at every point) are in go test: here we test that the
# engine really talks with systemd and with gpasswd.
set -u
qui=$(cd "$(dirname "$0")/.." && pwd)
"$qui/costruisci.sh" >/dev/null
"$qui/costruisci.sh" go build -trimpath -o uscita/impronta ./prove/impronta
podman image exists remotix-motore-systemd || podman build -q -t remotix-motore-systemd -f "$qui/prove/Contenitore.systemd" "$qui/prove"
podman rm -f rx-motore >/dev/null 2>&1
podman run -d --name rx-motore --systemd=always --cap-add NET_ADMIN,NET_RAW -v "$qui/uscita:/opt/rx:ro,Z" remotix-motore-systemd >/dev/null
for i in $(seq 1 30); do
	s=$(podman exec rx-motore systemctl is-system-running 2>/dev/null)
	[ "$s" = running ] || [ "$s" = degraded ] && break
	sleep 1
done
echo "system: $s"
x() { podman exec rx-motore sh -c "$1"; }

echo "== 1. trial installation, CONFERMATA expected"
x 'cd /root && /opt/rx/remotix-install plan --users provamotore --state-dir /root/op >/dev/null && /opt/rx/remotix-install approve plan-engine-test.json && /opt/rx/remotix-install apply plan-engine-test.json --state-dir /root/op | tail -8; echo "apply: exit $?"'
echo "-- seen from outside:"
x 'echo "unit: $(systemctl is-enabled remotix-engine-test.service)"; echo "video: $(getent group video)"; echo "programs launched (log):"; grep -h "\"COMMAND\"" /root/op/*/log.jsonl | sed "s/.*detail\":\"//; s/\"}//"; cat /root/op/*/certificate.txt | head -20'

echo "== 2. a step fails halfway (non-existent user, after files and unit): ANNULLATA expected, /etc as it was"
podman rm -f rx-motore >/dev/null
podman run -d --name rx-motore --systemd=always --cap-add NET_ADMIN,NET_RAW -v "$qui/uscita:/opt/rx:ro,Z" remotix-motore-systemd >/dev/null
for i in $(seq 1 30); do
	s=$(podman exec rx-motore systemctl is-system-running 2>/dev/null)
	[ "$s" = running ] || [ "$s" = degraded ] && break
	sleep 1
done
x 'cd /root && /opt/rx/impronta -contenuti /etc > prima && /opt/rx/remotix-install plan --users nessuno-si-chiama-cosi --state-dir /root/op >/dev/null && /opt/rx/remotix-install approve plan-engine-test.json >/dev/null && /opt/rx/remotix-install apply plan-engine-test.json --state-dir /root/op | tail -14; /opt/rx/impronta -contenuti /etc > dopo; if /opt/rx/impronta -confronta prima dopo; then echo "/etc: identical to before (contents, permissions, owners; not the times of the folders)"; else echo "/etc: DIFFERENT"; fi; echo "unit: $(systemctl is-enabled remotix-engine-test.service 2>&1)"'
podman rm -f rx-motore >/dev/null
