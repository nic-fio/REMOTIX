#!/usr/bin/env python3
"""check-package - the PACKAGE check: install, first start, use then remove, purge, reinstall, the refusal of a person called
remotix, and what an install pulls in. On a box it may reset freely.

    python3 check-package.py --box xfce|lxqt|gnome|kde --deb /path/to/remotix_x.deb [--no-linger]

NOT part of all.sh: it resets the box at the start (and again for the refusal check) and at the end leaves the box FRESH with the
package installed and the service enabled (fresh.sh), so it must not run on a box somebody else is testing.
Runs ON THE DEV SERVER (drives ./boxes/box.sh). One line per check: `PASS|FAIL|BLOCKED <name> - evidence`, exit 0 only if all PASS.
  install       apt install on a fresh box: expected files only, service installed but NOT enabled and NOT running, system user
                remotix (nologin), nothing on 7447
  first-start   enable --now: active, TCP and UDP listening, certificates with safe modes, no error in the journal, the two
                processes run as the design says (root side root, network side remotix)
  apparmor      the profile of the network side loaded / enforcing (BLOCKED if the box has no AppArmor interface)
  remove        a test user logged in, then apt remove while the session is alive: sessions closed, desktop processes gone,
                group enrolments undone, /dev/dri grants taken back, service stopped, binary gone, configuration and
                /var/lib/remotix kept, no process left, nothing else touched
  purge         apt purge: everything the package or the program made is gone, the box is as before the install except for
                the dependencies apt pulled in
  reinstall     install after the purge and a base login (page, login, desktop)
  preinst       a PERSON account called remotix: the install is refused with preinst's message and the box stays clean
  recommends    informative: what the install pulled in as Recommends, and the size
  fresh-end     the box left fresh, package installed, service enabled
Snapshots (package-snap.py, run inside the box) compare /etc /usr /var/lib /run, users, groups and members, unit files, AppArmor
profiles, polkit rules, nft/ufw. Logs, apt outputs and the JSON diffs: log/package-<box>/."""
import argparse
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

NAMES = ("install", "first-start", "apparmor", "remove", "purge", "reinstall", "preinst", "recommends", "fresh-end")
# uids of the test users: the boxes share /dev/dri with the host, so ACL entries are by uid and must differ from box to box
UID_BASE = {"xfce": 3100, "lxqt": 3200, "gnome": 3300, "kde": 3400}
PW = "pk1pass2026"
RECOMMENDS = ("labwc", "wlr-randr", "xwayland", "va-driver-all", "mesa-vulkan-drivers", "dconf-cli", "fonts-dejavu-core")
EXPECT_PATHS = ("/var/lib/remotix", "/run/remotix",  # made by systemd-tmpfiles at install (debian/remotix.tmpfiles)
               "/etc/apparmor.d/local/remotix_network")  # made by the dh_apparmor snippet of postinst (must go at purge)
HERE = lib.HERE


class Ctx:
    def __init__(self, de, deb, linger=True):
        self.de, self.deb, self.box, self.linger = de, deb, lib.Box(de), linger
        self.port = lib.PORTS[de]
        self.log = os.path.join(HERE, "log", "package-" + de + ("" if linger else "-nolinger"))
        os.makedirs(self.log, exist_ok=True)
        self.new_pkgs, self.pre_pkgs, self.apt_install = [], {}, ""
        self.installed = False

    # --- the box
    def sh(self, cmd, timeout=90):
        # own call (not lib.Box.run): the output may hold half a UTF-8 character (cut -c), which must not break the tool
        try:
            r = subprocess.run([self.box.sh, "ssh", self.de, "LC_ALL=C; export LC_ALL; " + cmd], capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise ToolError("the box %s did not answer in %d s: %.80s" % (self.de, timeout, cmd))
        return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace").strip()

    def save(self, name, text):
        with open(os.path.join(self.log, name), "w") as f:
            f.write(text if text.endswith("\n") else text + "\n")

    def apt(self, tag, args, timeout=900):
        """apt-get <args> in the box (non-interactive); the whole output goes to log/<tag>.txt. Returns (rc, output)."""
        c, t = self.sh("cd /root && DEBIAN_FRONTEND=noninteractive apt-get %s 2>&1; echo RC=$?" % args, timeout=timeout)
        m = re.search(r"RC=(\d+)\s*$", t)
        rc = int(m.group(1)) if m else 255
        self.save(tag + ".txt", t)
        return rc, t

    def copy_in(self):
        """The helper and the package into /root of the box."""
        for src, dst in ((os.path.join(HERE, "package-snap.py"), "/root/package-snap.py"), (self.deb, "/root/x.deb")):
            with open(src, "rb") as f:
                r = subprocess.run([self.box.sh, "ssh", self.de, "cat > %s" % dst], stdin=f, capture_output=True, timeout=180)
            if r.returncode:
                raise ToolError("cannot copy %s into the box: %s" % (src, r.stderr[-150:]))

    def snap(self, name):
        c, t = self.sh("python3 /root/package-snap.py snap /root/snap-%s.json && echo done" % name, timeout=300)
        if "done" not in t:
            raise ToolError("snapshot %s failed: %s" % (name, t[-200:]))

    def diff(self, a, b):
        c, t = self.sh("python3 /root/package-snap.py diff /root/snap-%s.json /root/snap-%s.json" % (a, b), timeout=120)
        try:
            d = json.loads(t)
        except ValueError:
            raise ToolError("diff %s..%s unreadable: %s" % (a, b, t[-200:]))
        self.save("diff-%s-%s.json" % (a, b), json.dumps(d, indent=1))
        return d

    def pkgs(self):
        c, t = self.sh("dpkg-query -W -f='${Package} ${db:Status-Abbrev}\\n' | awk '$2 ~ /^i/ {print $1}'")
        return set(t.split())

    def reset_box(self):
        r = subprocess.run([self.box.sh, "reset", self.de], capture_output=True, text=True, timeout=400)
        self.save("reset.txt", r.stdout + r.stderr)
        if r.returncode:
            raise ToolError("box reset failed: %s" % (r.stdout + r.stderr)[-200:])
        # the image (like the Docker Ubuntu one) has /usr/sbin/policy-rc.d answering 101 «no»: dpkg then never stops or starts a
        # service. A real machine has none, so the box would not show what the package's scripts do. Box only, before the snapshot.
        self.sh("test -e /usr/sbin/policy-rc.d && rm -f /usr/sbin/policy-rc.d; true")
        c, t = self.sh("apt-get update -qq >/dev/null 2>&1; echo $?", timeout=200)
        if t.strip().splitlines()[-1] != "0":
            raise ToolError("apt-get update failed in the box")
        self.copy_in()

    def write_port(self):
        self.sh("mkdir -p /etc/remotix/remotix.conf.d && echo REMOTIX_PORT=%d > /etc/remotix/remotix.conf.d/10-box-port.conf" % self.port)

    def listening(self, port=None):
        """The set of protocols listening on the port (host-wide: the boxes share the network)."""
        c, t = self.sh("ss -H -tuln | awk '{print $1, $5}'")
        return sorted({l.split()[0] for l in t.splitlines() if l.strip().endswith(":%d" % (port or self.port))})

    def make_user(self, name, uid):
        self.sh("id %s >/dev/null 2>&1 || useradd -m -u %d -s /bin/bash %s" % (name, uid, name))
        self.box.ensure_user(name, PW)
        # the product must enrol the user itself in the card groups: take the memberships ensure_user gave away
        self.sh("gpasswd -d %s video >/dev/null 2>&1; gpasswd -d %s render >/dev/null 2>&1; id -nG %s" % (name, name, name))


def short(items, n=8, w=70):
    items = list(items)
    s = ", ".join(str(i)[:w] for i in items[:n])
    return s + (" (+%d more)" % (len(items) - n) if len(items) > n else "") if items else "none"


# 1.0.0: the line pam-auth-update writes into common-session for debian/remotix.pam-config (exit 0 = present)
PAM_HOOK_LINE = "grep -Eq '^[[:space:]]*session[[:space:]]+optional[[:space:]]+pam_exec\\.so.*remotix-local-login' /etc/pam.d/common-session"


def related(p):
    return "remotix" in p.lower()


def acl_of(ctx, uid):
    c, t = ctx.sh("for f in /dev/dri/renderD*; do getfacl -n -p $f 2>/dev/null | grep -E '^(user|group):%d:' | sed \"s|^|$f |\"; done; true" % uid)
    return t.strip()


# --------------------------------------------------------------------------------------------------------------- checks
def c_install(ctx):
    ctx.reset_box()
    ctx.pre_pkgs = ctx.pkgs()
    ctx.snap("before")
    c, t = ctx.sh("getent passwd remotix; systemctl list-unit-files remotix.service --no-legend; ls -d /etc/remotix /var/lib/remotix /run/remotix 2>&1 | grep -v 'No such'; true")
    if t.strip():
        raise ToolError("the box is not fresh: %s" % t[:150])
    rc, out = ctx.apt("install", "install -y ./x.deb")
    ctx.apt_install = out
    if rc != 0:
        raise Fail("apt-get install ./x.deb failed (rc=%d): %s" % (rc, " | ".join(out.strip().splitlines()[-4:])[:300]))
    ctx.installed = True
    ctx.new_pkgs = sorted(ctx.pkgs() - ctx.pre_pkgs)
    ctx.snap("installed")
    r = ctx.diff("before", "installed")
    bad, notes = [], []
    c, listing = ctx.sh("dpkg -L remotix")
    missing = [p for p in listing.split() if p.startswith("/") and not p.endswith("/") and
               ctx.sh("test -d %s || test -e %s" % (p, p))[0] != 0 and p != "/."]
    if missing:
        bad.append("package files missing: " + short(missing))
    c, ver = ctx.sh("dpkg -V remotix")
    if ver.strip():
        bad.append("dpkg -V remotix: " + short(ver.splitlines()))
    # 1.0.0: the local-login hook, its pam-auth-update profile, and the line pam-auth-update put in common-session (the line is NOT
    # owned by the package, so the checks above do not see it)
    if ctx.sh("test -x /usr/libexec/remotix/remotix-local-login && test -f /usr/share/pam-configs/remotix")[0] != 0:
        bad.append("remotix-local-login or /usr/share/pam-configs/remotix missing")
    if ctx.sh(PAM_HOOK_LINE)[0] != 0:
        bad.append("/etc/pam.d/common-session has no pam_exec line of remotix-local-login after install (pam-auth-update)")
    extra = [p for p in r["added_unowned"] if related(p) and p not in EXPECT_PATHS and not any(p.startswith(e + "/") for e in EXPECT_PATHS)]
    if extra:
        bad.append("unexpected files of the program/scripts: " + short(extra))
    exp_seen = [p for p in r["added_unowned"] if related(p)]
    en = ctx.sh("systemctl is-enabled remotix 2>&1")[1].strip()
    ac = ctx.sh("systemctl is-active remotix 2>&1")[1].strip()
    if en != "disabled":
        bad.append("remotix.service is \"%s\", not disabled" % en)
    if ac != "inactive":
        bad.append("remotix.service is \"%s\", not inactive" % ac)
    c, u = ctx.sh("getent passwd remotix")
    f = u.strip().split(":")
    if len(f) < 7 or not (0 < int(f[2]) < 1000) or not f[6].endswith(("nologin", "false")):
        bad.append("system user remotix wrong: \"%s\"" % u.strip())
    if ctx.listening(7447):
        bad.append("something listens on 7447: %s" % ctx.listening(7447))
    ctx.sh("true")
    newu = [x for x in r["users_added"]]
    if not any(x.startswith("remotix:") for x in newu):
        bad.append("users added: %s (remotix missing)" % short(newu))
    if [x for x in newu if not x.startswith("remotix:")]:
        notes.append("accounts added by dependencies: " + short([x for x in newu if not x.startswith("remotix:")]))
    if r["groups_added"] and not all(g.startswith("remotix(") for g in r["groups_added"]):
        pass  # groups of the dependencies are listed in the log
    if any(related(x) and "enabled" in x for x in r["units_changed"]):
        bad.append("enabled unit: " + short([x for x in r["units_changed"] if related(x)]))
    if bad:
        raise Fail("; ".join(bad))
    other = [p for p in r["added_unowned"] if not related(p)]
    return PASS, ("apt ok, %d new packages (%d files owned by them); %d package files present, dpkg -V clean; made by scripts: %s; "
                  "remotix.service %s/%s (as the package's policy); user %s; nothing on 7447; other unowned additions: %d (%s); "
                  "%slog %s" % (len(ctx.new_pkgs), r["added_owned"], len([p for p in listing.split() if p.startswith("/")]), short(exp_seen),
                              en, ac, u.strip(), len(other), short(other, 4), ("; ".join(notes) + "; ") if notes else "", ctx.log))


def c_first_start(ctx):
    if not ctx.installed:
        raise ToolError("install did not succeed")
    ctx.write_port()
    c, t = ctx.sh("systemctl enable --now remotix 2>&1")
    end, lp = time.time() + 40, []
    while time.time() < end:
        lp = ctx.listening()
        if len(lp) == 2 and ctx.sh("systemctl is-active remotix")[1].strip() == "active":
            break
        time.sleep(1)
    time.sleep(3)
    bad, facts = [], []
    ac = ctx.sh("systemctl is-active remotix")[1].strip()
    if ac != "active":
        bad.append("service is \"%s\" after enable --now: %s" % (ac, ctx.sh("journalctl -u remotix --no-pager -n 5 -o cat")[1][-300:]))
    if lp != ["tcp", "udp"]:
        bad.append("port %d listening: %s (needs tcp and udp)" % (ctx.port, lp))
    c, ps = ctx.sh("ps -eo user:14=,pid=,ppid=,args= | grep '[l]ibexec/remotix/remotix --'")
    roots, nets = [], []
    for l in ps.splitlines():
        f = l.split(None, 3)
        (nets if "--network-side" in f[3] else roots).append((f[0], f[1], f[2]))
    if len(roots) != 1 or roots[0][0] != "root":
        bad.append("root side: %s" % roots)
    if len(nets) != 1 or nets[0][0] != "remotix":
        bad.append("network side: %s (design: user remotix)" % nets)
    if nets:
        c, st = ctx.sh("grep -E '^(CapEff|NoNewPrivs|Seccomp):' /proc/%s/status | tr '\\n\\t' '  '" % nets[0][1])
        facts.append("network side pid %s as %s %s; root side pid %s as %s" % (nets[0][1], nets[0][0], st.strip(), roots[0][1] if roots else "?", roots[0][0] if roots else "?"))
    c, certs = ctx.sh("find /var/lib/remotix/net /run/remotix/net -printf '%m %u:%g %y %p\\n' | sort -k4")
    ctx.save("first-start-files.txt", certs)
    for l in certs.splitlines():
        mode, own, kind, path = l.split(None, 3)
        sec = path.endswith((".key", "-secret", "log-secret", "ban", "ban.new")) or kind == "d"
        if own != "remotix:remotix":
            bad.append("%s owner %s" % (path, own))
        if sec and not path.endswith(".key") and kind == "d" and mode != "700":
            bad.append("%s mode %s (dir: 700)" % (path, mode))
        if path.endswith((".key", "-secret", "log-secret", "ban", "ban.new")) and kind == "f" and mode != "600":
            bad.append("%s mode %s (secret: 600)" % (path, mode))
        if kind == "f" and int(mode, 8) & 0o007 and not path.endswith((".pem", ".ours")):
            bad.append("%s readable by others (%s)" % (path, mode))
    facts.append("files: " + "; ".join("%s %s %s" % (l.split()[0], l.split()[1], os.path.basename(l.split()[3])) for l in certs.splitlines() if l.split()[2] == "f"))
    c, jerr = ctx.sh("journalctl -u remotix -p err --no-pager -o cat | cut -c1-200")
    if jerr.strip() and "No entries" not in jerr:
        ls = jerr.splitlines()
        banner = [l for l in ls if "⛔" in l]
        bad.append("%d error-level (priority err) journal lines, %d of them with the ⛔ banner text and %d without: first %s" % (
            len(ls), len(banner), len(ls) - len(banner), short([re.sub(r"\s+", " ", l) for l in ls], 4, 90)))
    c, jx = ctx.sh("journalctl -u remotix --no-pager -o cat | grep -c '⛔'")
    c, jx1 = ctx.sh("journalctl -u remotix --no-pager -o cat | grep '⛔' | cut -c1-150 | head -3")
    facts.append("journal lines with ⛔: %s%s" % (jx.strip(), (" (" + " | ".join(jx1.splitlines()) + ")") if jx1.strip() else ""))
    if bad:
        raise Fail("; ".join(bad) + " | " + "; ".join(facts))
    return PASS, "active, tcp+udp on %d, " % ctx.port + "; ".join(facts)


def c_apparmor(ctx):
    if not ctx.installed:
        raise ToolError("install did not succeed")
    c, par = ctx.sh("apparmor_parser -Q -T -S /etc/apparmor.d/remotix_network >/dev/null 2>&1 && echo compiles || echo does-not-compile")
    c, modp = ctx.sh("cat /sys/module/apparmor/parameters/enabled 2>&1; test -d /sys/kernel/security/apparmor && echo iface-yes || echo iface-no")
    if "iface-yes" not in modp:
        return BLOCKED, ("AppArmor is not available in this box (securityfs /sys/kernel/security/apparmor is not mounted in the container; "
                         "kernel module parameter: %s): the profile cannot be loaded here, so loaded/enforcing cannot be told. "
                         "What can be told: profile text %s (apparmor_parser -Q); the shipped profile has flags=(complain)" % (
                             modp.splitlines()[0], par.strip()))
    c, prof = ctx.sh("grep -E '^remotix_network ' /sys/kernel/security/apparmor/profiles")
    c, pid = ctx.sh("ps -eo user:14=,pid=,args= | awk '$1==\"remotix\" && /--network-side/ {print $2}' | head -1")
    c, attr = ctx.sh("cat /proc/%s/attr/current 2>&1" % pid.strip()) if pid.strip() else (1, "no network-side process")
    if not prof.strip():
        raise Fail("profile remotix_network is not loaded (profiles file has no such line); network side attr: %s" % attr.strip())
    if "(enforce)" not in prof or "(enforce)" not in attr:
        raise Fail("profile loaded but not enforcing: \"%s\"; network side confined as \"%s\" (flags=complain in the shipped profile)" % (prof.strip(), attr.strip()))
    return PASS, "loaded: \"%s\"; network side confined as \"%s\"" % (prof.strip(), attr.strip())


def c_remove(ctx):
    if not ctx.installed:
        raise ToolError("install did not succeed")
    de = ctx.de
    user, uid = "pkg" + de[:2] + "1", UID_BASE[de] + 1
    ctx.make_user(user, uid)
    # a user manager (systemd --user) already running when the user is first enrolled in the card groups = the «stale user manager»
    # case of render_grant.c: on GNOME/KDE the product then grants the card by ACL instead of by group
    if ctx.linger:
        ctx.sh("loginctl enable-linger %s; sleep 3; systemctl is-active user@%d.service" % (user, uid))
    rig = lib.Rig(de, "chrome", user, PW, "pkgremove", cap=90)
    try:
        rig.start(make_user=False)
        rig.open_page()
        rig.login()
        d = rig.settle(90)
        ev = []
        c, sess = ctx.sh("for id in $(loginctl list-sessions --no-legend | awk '{print $1}'); do echo $id $(loginctl show-session $id -p Name -p Service -p Type -p State --value | tr '\\n' ' '); done")
        mine = [l for l in sess.splitlines() if " %s " % user in " " + l and "remotix" in l]
        procs = int(ctx.sh("pgrep -u %s | wc -l" % user)[1].strip() or 0)
        groups_in = ctx.sh("id -nG %s" % user)[1].strip()
        enr = ctx.sh("cat /var/lib/remotix/group-enrollments.jsonl 2>&1 | cut -c1-200; echo ---; cat /var/lib/remotix/render-grants 2>&1 | head -5")[1]
        acl_in = acl_of(ctx, uid)
        ev.append("alive: desktop up (%s); logind sessions of %s by remotix: %d, processes of the user: %d, groups: %s; enrolments file: %s; ACL on renderD*: %s" % (
            d["desc"][:40], user, len(mine), procs, groups_in, enr.replace("\n", " ")[:260], acl_in.replace("\n", "; ") or "none"))
        enrolled = [(m.group(1), m.group(2)) for m in re.finditer(r'"user":"([^"]*)".*?"group":"([^"]*)"', enr) if m.group(1) == user]
        ctx.save("remove-alive.txt", "sessions:\n%s\n\n%s\n" % (sess, enr))
        ctx.snap("alive")
        rc, out = ctx.apt("remove", "remove -y remotix")
        ctx.save("remove-apt.txt", out)
        time.sleep(3)
        bad = []
        if rc != 0:
            bad.append("apt-get remove failed rc=%d: %s" % (rc, " | ".join(out.strip().splitlines()[-3:])[:250]))
        warn = [l for l in out.splitlines() if "⚠" in l or "remotix:" in l]
        # what the remove must close: the REMOTIX session(s) of the user (logind Service=remotix) and the processes in its scope.
        # The lingering user manager (systemd --user, made by the tool's enable-linger) is not the product's and stays.
        # systemd ends a scope that ignores SIGTERM with SIGKILL after 90 s, so wait up to 130 s and say how long it took.
        in_scope = ("for p in $(pgrep -u %s); do grep -q 'session-c' /proc/$p/cgroup && echo $p $(tr '\\0' ' ' </proc/$p/cmdline | cut -c1-60); done; "
                    "for id in $(loginctl list-sessions --no-legend | awk '{print $1}'); do [ \"$(loginctl show-session $id -p Service --value)\" = remotix ] && echo session $id; done; true") % user
        t0 = time.time()
        while time.time() - t0 < 130 and ctx.sh(in_scope)[1].strip():
            time.sleep(3)
        closed_s = time.time() - t0
        procs2 = ctx.sh(in_scope)[1].strip()
        if procs2:
            bad.append("after %.0f s the REMOTIX session of %s is still there: %s" % (closed_s, user, short(procs2.splitlines(), 5, 70)))
        else:
            ev.append("session and desktop processes gone %.0f s after apt returned" % closed_s)
        if not mine:
            ev.append("⚠ no logind session with Service=remotix was seen before the remove")
        groups_out = ctx.sh("id -nG %s" % user)[1].strip().split()
        for u, g in enrolled:
            if g in groups_out:
                bad.append("enrolment in %s not undone (groups now: %s)" % (g, " ".join(groups_out)))
        if not enrolled:
            ev.append("⚠ the product recorded no group enrolment for %s although the user was not in video/render" % user)
        acl_out = acl_of(ctx, uid)
        if acl_out:
            bad.append("ACL grants still on /dev/dri: " + acl_out.replace("\n", "; "))
        c, st = ctx.sh("systemctl is-active remotix 2>&1; systemctl is-enabled remotix 2>&1; pgrep -fa '[l]ibexec/remotix' | cut -c1-90")
        if "inactive" not in st.splitlines()[0] and "unknown" not in st.splitlines()[0]:
            bad.append("service state after remove: %s" % st.replace("\n", " / "))
        rem = st.splitlines()[2:]
        if rem:
            bad.append("product processes left: %s" % short(rem))
        if ctx.sh("test -e /usr/libexec/remotix/remotix")[0] == 0:
            bad.append("binary still there")
        if ctx.sh(PAM_HOOK_LINE)[0] == 0:
            bad.append("/etc/pam.d/common-session still has the pam_exec line of remotix-local-login after remove")
        c, gone = ctx.sh("ls /usr/share/polkit-1/rules.d/*remotix* /usr/lib/systemd/system/remotix.service /usr/share/remotix 2>&1 | grep -v 'No such'")
        if gone.strip():
            bad.append("package files left: " + short(gone.splitlines()))
        c, kept = ctx.sh("ls -d /etc/remotix/denied-users /etc/pam.d/remotix /etc/apparmor.d/remotix_network /etc/ufw/applications.d/remotix "
                         "/var/lib/remotix/net/certificates/page.key /var/lib/remotix/group-enrollments.jsonl 2>&1 | sed 's/^ls: cannot access .\\(.*\\).: No such.*/MISSING \\1/'")
        miss = [l for l in kept.splitlines() if l.startswith("MISSING")]
        if any("denied-users" in m or "pam.d" in m or "certificates" in m for m in miss):
            bad.append("kept things missing: " + short(miss))
        c, unitleft = ctx.sh("find /etc/systemd -name '*remotix*' -printf '%p %y -> %l\\n'; systemctl is-enabled remotix 2>&1")
        c, dpk = ctx.sh("dpkg-query -W -f='${db:Status-Abbrev}' remotix")
        ctx.snap("removed")
        r = ctx.diff("installed", "removed")
        us_ok = [x for x in r["users_added"] if x.startswith(user + ":")]
        if len(r["users_added"]) != len(us_ok) or r["users_removed"]:
            bad.append("users changed: +%s -%s" % (short([x for x in r["users_added"] if x not in us_ok]), short(r["users_removed"])))
        gm = [x for x in r["group_members"] if user not in x]
        if gm or r["groups_removed"] or r["users_changed"]:
            bad.append("group/user state changed: %s %s %s" % (short(gm), short(r["groups_removed"]), short(r["users_changed"])))
        uchg = [x for x in r["units_changed"] if not related(x)]
        if uchg:
            bad.append("other units changed: " + short(uchg))
        if r["polkit"] and any(not related(x) for x in r["polkit"]):
            bad.append("polkit rules changed: " + short([x for x in r["polkit"] if not related(x)]))
        if r["nft_changed"] or r["ufw_changed"]:
            bad.append("firewall state changed (nft %s, ufw %s)" % (r["nft_changed"], r["ufw_changed"]))
        if r["apparmor"] and (r["apparmor"]["added"] or r["apparmor"]["removed"]):
            ev.append("AppArmor profiles changed: %s" % r["apparmor"])
        left = [p for p in r["added_unowned"] if related(p)]
        other_left = [p for p in r["added_unowned"] if not related(p) and user not in p and str(uid) not in p]
        chg = [p for p in r["changed"] if not user in p]
        if bad:
            c, dg = ctx.sh("echo '--- sessions'; loginctl list-sessions --no-legend; echo '--- processes (pid ppid user cgroup args)'; "
                           "for p in $(pgrep -u %s; pgrep -f '[l]ibexec/remotix'); do echo $p $(ps -o ppid= -o user= -p $p) $(cut -d: -f3 /proc/$p/cgroup) $(tr '\\0' ' ' </proc/$p/cmdline | cut -c1-90); done; "
                           "echo '--- journal remotix since 5 min'; journalctl -u remotix --no-pager -o cat --since -5min | tail -25 | cut -c1-200; "
                           "echo '--- dpkg log'; tail -8 /var/log/apt/term.log" % user)
            ctx.save("remove-diag.txt", dg)
            raise Fail("; ".join(bad) + " | " + " | ".join(ev) + " | diagnostics in %s/remove-diag.txt" % ctx.log)
        return PASS, ("%s | after remove: apt ok%s, user session and desktop processes gone, service %s, binary gone, dpkg state \"%s\", conf/state kept (%s), "
                      "kept-or-made by remotix: %d paths (%s); unit files: %s; unrelated unowned paths: %s; changed files: %s" % (
                          " | ".join(ev), (" (warnings: " + short(warn) + ")") if warn else "", st.splitlines()[0],
                          dpk.strip(), "all present" if not miss else "missing " + short(miss), len(left), short(left, 5, 55),
                          short(unitleft.splitlines(), 4, 90), short(other_left, 5), short(chg, 5)))
    finally:
        rig.stop()


def c_purge(ctx):
    if not ctx.installed:
        raise ToolError("install did not succeed")
    de = ctx.de
    user = "pkg" + de[:2] + "1"
    ctx.sh("rm -f /etc/remotix/remotix.conf.d/10-box-port.conf")  # the tool's own file (box.sh writes it); an administrator's file would stay
    log_before = ctx.sh("ls -la /home/%s/.local/state/remotix 2>&1 | tail -n +4 | awk '{print $1,$3,$5,$9}'" % user)[1].strip().replace("\n", "; ")
    rc, out = ctx.apt("purge", "purge -y remotix")
    bad = []
    if rc != 0:
        bad.append("apt-get purge failed rc=%d: %s" % (rc, " | ".join(out.strip().splitlines()[-3:])[:250]))
    warn = [l for l in out.splitlines() if "⚠" in l or l.startswith("remotix:")]
    checks = [("/var/lib/remotix", "state dir"), ("/run/remotix", "run dir"), ("/etc/remotix", "config dir"), ("/etc/pam.d/remotix", "pam"),
              ("/etc/apparmor.d/remotix_network", "profile"), ("/etc/ufw/applications.d/remotix", "ufw"), ("/usr/libexec/remotix", "binary dir"),
              ("/usr/share/remotix", "share"), ("/usr/share/polkit-1/rules.d/40-remotix-remote-sessions.rules", "polkit"),
              ("/usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules", "polkit"), ("/usr/lib/systemd/system/remotix.service", "unit"),
              ("/usr/lib/sysusers.d/remotix.conf", "sysusers"), ("/usr/lib/tmpfiles.d/remotix.conf", "tmpfiles"),
              ("/home/%s/.local/state/remotix" % user, "per-user session log dir")]
    for p, w in checks:
        if ctx.sh("test -e %s || test -L %s" % (p, p))[0] == 0:
            bad.append("%s left (%s)%s" % (p, w, (": " + ctx.sh("ls -la %s 2>&1 | tail -n +4 | awk '{print $1,$3,$9}' | head -6" % p)[1].replace("\n", "; ")) if "per-user" in w else ""))
    if ctx.sh(PAM_HOOK_LINE)[0] == 0:
        bad.append("/etc/pam.d/common-session still has the pam_exec line of remotix-local-login after purge")
    c, uleft = ctx.sh("find /etc/systemd /usr/lib/systemd /etc/polkit-1 /etc/apparmor.d /var/lib /run -iname '*remotix*' 2>/dev/null | grep -v '^/run/user\\|^/run/systemd'")
    if uleft.strip():
        bad.append("paths named remotix left: " + short(uleft.splitlines()))
    c, ent = ctx.sh("getent passwd remotix; getent group remotix")
    if ent.strip():
        bad.append("system user/group remotix left: " + ent.replace("\n", " "))
    c, dpk = ctx.sh("dpkg-query -W -f='${db:Status-Abbrev}' remotix 2>&1")
    if dpk.strip() not in ("un", "") and "no packages" not in dpk:
        bad.append("dpkg state \"%s\" (needs purged)" % dpk.strip())
    c, aa = ctx.sh("test -r /sys/kernel/security/apparmor/profiles && (grep -c '^remotix_network ' /sys/kernel/security/apparmor/profiles; true) || echo n/a")
    if aa.strip() not in ("n/a", "0"):
        bad.append("AppArmor profile still loaded")
    ctx.sh("loginctl disable-linger %s; loginctl terminate-user %s; sleep 2; pkill -KILL -u %s; sleep 1; userdel -r %s >/dev/null 2>&1; true" % (user, user, user, user))
    time.sleep(1)
    ctx.snap("purged")
    r = ctx.diff("before", "purged")
    left = [p for p in r["added_unowned"] if related(p)]
    if left:
        bad.append("unowned remotix paths vs before: " + short(left))
    ua = [x for x in r["users_added"] if x.split(":")[0] in ("remotix", user)]
    ga = [x for x in r["groups_added"] if x.split("(")[0] in ("remotix", user)]
    if ua or ga or r["users_removed"] or r["users_changed"] or r["groups_removed"] or r["group_members"]:
        bad.append("users/groups differ from before: +%s -%s ~%s groups +%s -%s members %s" % (
            short(ua), short(r["users_removed"]), short(r["users_changed"]), short(ga),
            short(r["groups_removed"]), short(r["group_members"])))
    dep_acc = [x for x in r["users_added"] + r["groups_added"] if x not in ua and x not in ga]
    ex = [x for x in r["units_changed"] if related(x)]
    pre = [x for x in r["units_changed"] if not x.split(": ")[1].startswith("-")]  # an existing unit file changed state
    if ex or pre:
        bad.append("unit state: " + short(ex + pre))
    pk = [x for x in r["polkit"] if related(x)]
    if pk:
        bad.append("polkit rules: " + short(pk))
    if r["apparmor"] and (r["apparmor"]["added"] or r["apparmor"]["removed"]):
        bad.append("AppArmor profiles differ: %s" % r["apparmor"])
    if r["nft_changed"] or r["ufw_changed"]:
        bad.append("firewall state differs (nft %s, ufw %s)" % (r["nft_changed"], r["ufw_changed"]))
    if r["removed"]:
        own = [ctx.sh("dpkg -S %s 2>&1 | cut -c1-60" % p)[1].strip() for p in r["removed"][:4]]
        bad.append("paths of the box that are gone after the purge: %s (dpkg -S: %s)" % (short(r["removed"], 6), short(own, 4, 60)))
    gone_pk = [p for p in r["gone_packages"]]
    if gone_pk:
        bad.append("packages gone: " + short(gone_pk))
    c, ar = ctx.sh("apt-get autoremove --purge -s 2>&1 | grep -E '^Remv' | wc -l")
    other = [p for p in r["added_unowned"] if not related(p)]
    if bad:
        raise Fail("; ".join(bad))
    return PASS, ("apt purge ok%s; per-user log dir before the purge: \"%s\"; box as before except: %d dependency packages (%s) owning %d files; "
                  "other unowned additions (not remotix): %d (%s); accounts/groups added by dependencies: %s; changed: %s; autoremove would remove %s (informative)" % (
                      (" (warnings: " + short(warn) + ")") if warn else "", log_before[:120], len(r["new_packages"]), short(r["new_packages"], 30, 28),
                      r["added_owned"], len(other), short(other, 6), short(dep_acc), short(r["changed"], 6), ar.strip()))


def c_reinstall(ctx):
    if not ctx.installed:
        raise ToolError("install did not succeed")
    de = ctx.de
    user, uid = "pkg" + de[:2] + "2", UID_BASE[de] + 2
    rc, out = ctx.apt("reinstall", "install -y ./x.deb")
    if rc != 0:
        raise Fail("reinstall after purge failed rc=%d: %s" % (rc, " | ".join(out.strip().splitlines()[-4:])[:300]))
    state = "%s/%s" % (ctx.sh("systemctl is-enabled remotix 2>&1")[1].strip(), ctx.sh("systemctl is-active remotix 2>&1")[1].strip())
    ctx.write_port()
    ctx.sh("systemctl enable --now remotix 2>&1")
    time.sleep(6)
    ctx.make_user(user, uid)
    rig = lib.Rig(de, "chrome", user, PW, "pkgre", cap=90)
    try:
        rig.start(make_user=False)
        f = rig.open_page()
        s = rig.login()
        d = rig.settle(90)
    finally:
        rig.stop()
    return PASS, "apt install ok, service after install %s (as policy), after enable page \"%s\" login \"%s\" desktop: %s%s" % (
        state, f.get("title"), s["outcome"].strip(), d["extra"], d["desc"][:60])


def c_preinst(ctx):
    ctx.reset_box()
    ctx.snap("before2")
    ctx.sh("useradd -m -u 1500 -s /bin/bash remotix")
    c, who = ctx.sh("getent passwd remotix")
    rc, out = ctx.apt("preinst", "install -y ./x.deb")
    bad = []
    if rc == 0:
        bad.append("apt-get install SUCCEEDED with a person's account called remotix")
    msg = [l for l in out.splitlines() if "an account named" in l]
    if not msg:
        bad.append("no refusal message of preinst in the output (tail: %s)" % " | ".join(out.strip().splitlines()[-3:])[:200])
    c, dpk = ctx.sh("dpkg-query -W -f='${db:Status-Abbrev}' remotix 2>&1; dpkg -L remotix 2>&1 | head -2")
    if dpk.strip().startswith(("ii", "iU", "iF", "hi", "ri", "Hi", "iH")):
        bad.append("dpkg state \"%s\"" % dpk.strip().splitlines()[0])
    c, files = ctx.sh("ls -d /usr/libexec/remotix /etc/remotix /var/lib/remotix /run/remotix /usr/lib/systemd/system/remotix.service /etc/pam.d/remotix 2>&1 | grep -v 'No such'")
    if files.strip():
        bad.append("files left: " + short(files.splitlines()))
    ctx.snap("preinst")
    r = ctx.diff("before2", "preinst")
    left = [p for p in r["added_unowned"] if related(p) and not p.startswith("/var/lib/AccountsService")]
    if left:
        bad.append("remotix paths made: " + short(left))
    if [x for x in r["users_added"] if not x.startswith("remotix:")] or r["users_removed"]:
        bad.append("users: +%s -%s" % (short(r["users_added"]), short(r["users_removed"])))
    ctx.sh("userdel -r remotix >/dev/null 2>&1; true")
    c, gone = ctx.sh("getent passwd remotix; getent group remotix; ls -d /home/remotix 2>&1 | grep -v 'No such'")
    if gone.strip():
        bad.append("test account not removed: %s" % gone.replace("\n", " "))
    if bad:
        raise Fail("; ".join(bad))
    return PASS, "apt rc=%d, message: \"%s\"; person: %s; dpkg state \"%s\", no remotix files, users unchanged except the account; account removed again" % (
        rc, msg[0].strip()[:150], who.strip(), dpk.strip().splitlines()[0] if dpk.strip() else "not installed")


def c_recommends(ctx):
    if not ctx.installed:
        raise ToolError("install did not succeed")
    new, pre = set(ctx.new_pkgs), set(ctx.pre_pkgs)
    pulled = [p for p in RECOMMENDS if p in new]
    had = [p for p in RECOMMENDS if p in pre]
    absent = [p for p in RECOMMENDS if p not in new and p not in pre]
    m = re.search(r"Need to get ([^\n]*)", ctx.apt_install)
    a = re.search(r"After this operation, ([^\n]*)", ctx.apt_install)
    return PASS, ("info: pulled in by this install: %s; already on the box: %s; NOT present: %s; %d new packages in all; download %s; installed %s" % (
        short(pulled, 9), short(had, 9), short(absent, 9), len(new), m.group(1)[:60] if m else "n/a", a.group(1)[:60] if a else "n/a"))


def c_fresh_end(ctx):
    r = subprocess.run([os.path.join(HERE, "fresh.sh"), ctx.de], env=dict(os.environ, DEB=ctx.deb), capture_output=True, text=True, timeout=900)
    ctx.save("fresh-end.txt", r.stdout + r.stderr)
    if r.returncode:
        raise ToolError("fresh.sh failed: %s" % (r.stdout + r.stderr)[-200:])
    c, t = ctx.sh("systemctl is-enabled remotix; systemctl is-active remotix; dpkg-query -W -f='${Version}' remotix")
    if t.split()[:2] != ["enabled", "active"]:
        raise Fail("the box is not left enabled/active: %s" % t.replace("\n", " "))
    return PASS, "fresh box, remotix %s installed, service enabled and active" % t.split()[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", required=True, choices=sorted(lib.PORTS))
    ap.add_argument("--deb", required=True)
    ap.add_argument("--no-linger", action="store_true", help="the remove check without a user manager running before the login (default: with one, "
                    "the stale-user-manager case that makes the product grant the card by ACL on GNOME/KDE)")
    a = ap.parse_args()
    if not os.path.isfile(a.deb):
        sys.exit("no such package: " + a.deb)
    ctx = Ctx(a.box, os.path.abspath(a.deb), not a.no_linger)
    res = lib.Results(NAMES)

    def flow():
        res.attempt("install", lambda: c_install(ctx))
        res.attempt("first-start", lambda: c_first_start(ctx))
        res.attempt("apparmor", lambda: c_apparmor(ctx))
        res.attempt("remove", lambda: c_remove(ctx))
        res.attempt("purge", lambda: c_purge(ctx))
        res.attempt("reinstall", lambda: c_reinstall(ctx))
        res.attempt("preinst", lambda: c_preinst(ctx))
        res.attempt("recommends", lambda: c_recommends(ctx))
        res.attempt("fresh-end", lambda: c_fresh_end(ctx))

    return res.sequence(flow, 3300)


if __name__ == "__main__":
    sys.exit(main())
