#!/bin/sh
# wall-selinux.sh BOX - the NEGATIVE test of the SELinux wall (step 5, D3): the network side's domain remotix_net_t refuses what it must refuse.
# Run ON THE DEV SERVER, from prove/, with the VM BOX on (virtual video is enough), the package installed, SELinux enforcing.
# How: a COPY of python3 is labelled remotix_exec_t (the entry point of remotix_net_t) and started in that domain with `runcon`, as ROOT with all its
# capabilities — so the Unix permissions and the capabilities say yes to everything and only SELinux can say no — against targets any user could reach
# (root's files, sockets made 0666).  wall-neg-domain.py TRIES each action and prints one JSON line; the checker below (run in the VM, outside the
# domain) reports PASS for an action that must be refused only if it WAS refused (EACCES/EPERM) AND the journal holds an AVC (or a user_avc of the bus)
# of remotix_net_t inside the window of THAT attempt: a refusal by the Unix permissions would leave no such line.
# Everything is kept: the full output goes to $LOGDIR (default ./log-selinux/<box>-<time>/): probe.out, checks.out, avc.txt (every AVC of remotix_net_t
# since the start), policy-facts.txt (the rules of the loaded policy, if the build VM is on: see wall-sesearch.sh).  The copy of python3 and the fixture
# files are the test's own and are removed at the end.
BOX=${1:?usage: wall-selinux.sh xfce|lxqt|gnome|kde}
cd "$(dirname "$0")" || exit 2
export RX_BANCO=vm
LOGDIR=${LOGDIR:-log-selinux/$BOX-$(date +%y%m%d-%H%M%S)}; mkdir -p "$LOGDIR"
GS() { timeout 180 banco-vm/box.sh ssh "$BOX" "$@"; }
T0=$(GS 'date +%s.%N' | tail -1)
cat wall-neg-domain.py | GS 'cat >/var/tmp/rx-neg-domain.py'
GS 'cp /usr/bin/python3 /var/tmp/rxpy && chcon -t remotix_exec_t /var/tmp/rxpy && echo x >/var/lib/remotix/render-grants.negtest'
# two LISTENING sockets of the test's own, mode 0666 (reachable by anybody as far as Unix goes): an X socket and one in a user'"'"'s /run/user folder
GS 'U=$(ls /run/user | grep -v "^0$" | head -1); [ -n "$U" ] || U=0
    echo "$U" >/var/tmp/rx-neg-uid
    cat >/var/tmp/rx-neg-listen.py <<PY
import os, socket, time
ps = ["/tmp/.X11-unix/X77", "/run/user/$U/rx-neg-user.sock"]
ss = []
for p in ps:
    s = socket.socket(socket.AF_UNIX); s.bind(p); os.chmod(p, 0o666); s.listen(1); ss.append(s)
time.sleep(90)
for p in ps: os.unlink(p)
PY
    (setsid python3 /var/tmp/rx-neg-listen.py >/dev/null 2>&1 &) ; sleep 1; ls -l /tmp/.X11-unix/X77 /run/user/$U/rx-neg-user.sock'
# (the file name differs from the real one so that a real file of the root side is never touched)  Two runs: uid 0 for what must be refused, uid remotix for what must be allowed.
GS 'sed -i "s#/var/lib/remotix/render-grants\"#/var/lib/remotix/render-grants.negtest\"#" /var/tmp/rx-neg-domain.py
    H=$(getent passwd prova | cut -d: -f6); [ -d "$H" ] || H=/root
    RXNEG_PHASE=denied RXNEG_HOME=$H RXNEG_ROOTPID=$(systemctl show -p MainPID --value remotix) RXNEG_USERSOCK=/run/user/$(cat /var/tmp/rx-neg-uid)/rx-neg-user.sock \
      runcon -u system_u -r system_r -t remotix_net_t -l s0 -- /var/tmp/rxpy -c "$(cat /var/tmp/rx-neg-domain.py)" 2>&1
    RXNEG_PHASE=allowed RXNEG_USERSOCK=x \
      setpriv --reuid=remotix --regid=remotix --clear-groups runcon -u system_u -r system_r -t remotix_net_t -l s0 -- /var/tmp/rxpy -c "$(cat /var/tmp/rx-neg-domain.py)" 2>&1
    true' >"$LOGDIR/probe.out" 2>&1
GS 'cat > /var/tmp/rx-check.py' <<'PY'
import json, subprocess, sys
bad = 0
for line in open("/var/tmp/rx-probe.out"):
    line = line.strip()
    if not line.startswith("{"):
        print("NOTE probe says:", line[:200]); continue
    r = json.loads(line)
    j = subprocess.run(["journalctl", "--no-pager", "-o", "cat", "--since", "@%.3f" % (r["t0"] - 0.05), "--until", "@%.3f" % (r["t1"] + 0.45), "-g", "avc:"],
                       capture_output=True, text=True).stdout
    avc = [l for l in j.splitlines() if "denied" in l and "remotix_net_t" in l]
    if r["want"] == "denied":
        ok = r["outcome"] == "denied" and len(avc) >= 1
        why = "refused (%s) and %d AVC line(s) of remotix_net_t in its window" % (r["outcome"], len(avc))
    else:
        ok = r["outcome"] == "allowed"
        why = "allowed, as it must be"
    bad += not ok
    print(("PASS " if ok else "FAIL ") + "%2d %s - %s" % (r["n"], r["label"], why))
print("SUMMARY: %d FAIL" % bad)
PY
GS 'cat >/var/tmp/rx-probe.out; python3 /var/tmp/rx-check.py' <"$LOGDIR/probe.out" | tee "$LOGDIR/checks.out"
GS "journalctl -b --no-pager -o cat -g 'avc:' --since @$T0 | grep -a remotix_net_t" >"$LOGDIR/avc.txt" 2>&1
GS "ausearch -m avc,user_avc,selinux_err -ts $(date -d @${T0%.*} +%H:%M:%S) 2>&1 | grep -a remotix_net_t | head -300" >>"$LOGDIR/avc.txt" 2>&1
# (the files first, the kill last: the command line of this very shell names rx-neg-listen.py, and pkill -f would end it before the rm)
GS 'rm -f /var/tmp/rxpy /var/tmp/rx-neg-domain.py /var/tmp/rx-neg-listen.py /var/tmp/rx-neg-uid /var/tmp/rx-probe.out /var/tmp/rx-check.py /var/lib/remotix/render-grants.negtest /run/remotix/prelocal/negtest /tmp/.X11-unix/X77 /run/user/*/rx-neg-user.sock; pkill -f "[r]x-neg-listen.py"; true'
echo "full output in $LOGDIR"
