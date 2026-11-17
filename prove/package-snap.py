#!/usr/bin/env python3
"""package-snap - runs INSIDE a box (stdlib only), for check-package.py.

    python3 package-snap.py snap OUT.json            take a snapshot of the box
    python3 package-snap.py diff BEFORE.json AFTER.json   print the difference as JSON

A snapshot: every path under /etc /usr /var/lib /run (type, mode, owner, link target, sha256 of files in /etc up to 1 MB),
users, groups with their members, the state of every unit file (system and --global), installed packages with versions,
the loaded AppArmor profiles (null if the kernel interface is not mounted), polkit rules, the nft ruleset.
Paths that are only noise of the system running are left out (SKIP). The diff tells, for what appeared or went away, whether a
package owns it (any package: the dependencies apt pulled in own their files; what nobody owns was made by a script or by the
program) and lists the changes of users, groups, units, profiles and rules."""
import glob
import hashlib
import json
import os
import pwd
import grp
import subprocess
import sys

ROOTS = ("/etc", "/usr", "/var/lib", "/run")
SKIP = ("/var/lib/dpkg", "/var/lib/apt", "/var/lib/systemd", "/var/lib/ucf", "/var/lib/private", "/run/user", "/run/systemd",
        "/run/log", "/run/lock", "/run/utmp", "/run/udev", "/run/credentials", "/run/initctl", "/run/motd.dynamic",
        "/run/sshd", "/run/sshd.pid", "/run/dbus", "/run/dmeventd-client", "/run/dmeventd-server", "/run/shm", "/run/mount",
        "/run/agetty.reload", "/run/sudo", "/run/pam", "/run/console", "/run/nologin", "/run/tmpfiles.d", "/run/lvm",
        "/run/blkid", "/run/utmp", "/run/wtmp", "/run/ConsoleKit", "/run/rpcbind", "/run/avahi-daemon", "/run/cups",
        "/run/NetworkManager", "/run/lightdm", "/run/gdm3", "/run/sddm", "/run/accounts-daemon", "/run/polkit", "/run/libvirt",
        "/run/pcscd", "/run/lightdm.pid", "/run/gdm3.pid", "/run/wpa_supplicant", "/run/sm-notify.pid", "/run/lock",
        "/run/udisks2", "/run/upower", "/run/rtkit", "/run/media", "/run/pipewire", "/run/bluetooth", "/run/colord")
# the databases the users/groups comparison reads directly, and caches the system rewrites by itself
NOISE_CHANGED = ("/etc/passwd", "/etc/group", "/etc/shadow", "/etc/gshadow", "/etc/subuid", "/etc/subgid", "/etc/.pwd.lock",
                 "/etc/ld.so.cache", "/etc/alternatives/", "/etc/mailcap", "/etc/shells", "/etc/machine-id", "/etc/resolv.conf",
                 "/etc/hosts", "/etc/hostname", "/etc/mtab", "/etc/ssl/certs/", "/etc/ca-certificates.conf", "/etc/mime.types",
                 "/etc/fonts/conf.d/", "/etc/udev/hwdb.bin", "/etc/dconf/db/", "/etc/gconf/", "/etc/xml/", "/etc/sgml/",
                 "/etc/ssh/ssh_host", "/etc/inittab", "/etc/localtime", "/etc/timezone", "/etc/systemd/journald.conf.d/")


def skipped(p):
    return any(p == s or p.startswith(s + "/") for s in SKIP)


def uname(u):
    try:
        return pwd.getpwuid(u).pw_name
    except KeyError:
        return str(u)


def gname(g):
    try:
        return grp.getgrgid(g).gr_name
    except KeyError:
        return str(g)


def sha(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read(1 << 20)).hexdigest()[:16]
    except OSError:
        return "?"


def sh(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        return (r.stdout + ("\n" + r.stderr if r.returncode and r.stderr else "")).strip()
    except Exception as e:  # noqa: BLE001
        return "(error: %s)" % e


def snap():
    files = {}
    for root in ROOTS:
        for d, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = sorted(x for x in dirs if not skipped(os.path.join(d, x)))
            for n in [""] + sorted(names):
                p = os.path.join(d, n) if n else d
                if skipped(p):
                    continue
                try:
                    st = os.lstat(p)
                except OSError:
                    continue
                kind = "d" if os.path.isdir(p) and not os.path.islink(p) else ("l" if os.path.islink(p) else "f")
                link = os.readlink(p) if kind == "l" else ""
                h = sha(p) if (kind == "f" and p.startswith("/etc/") and st.st_size <= 1 << 20) else ""
                files[p] = [kind, "%o" % (st.st_mode & 0o7777), uname(st.st_uid) + ":" + gname(st.st_gid), link, h]
    passwd = sorted(sh("getent passwd").splitlines())
    groups = sorted(sh("getent group").splitlines())
    units = {}
    for tag, cmd in (("system", "systemctl list-unit-files --no-legend --no-pager --plain"),
                     ("global", "systemctl --global list-unit-files --no-legend --no-pager --plain")):
        for line in sh(cmd).splitlines():
            f = line.split()
            if len(f) >= 2 and f[1] != "transient":
                units["%s:%s" % (tag, f[0])] = f[1]
    pk = {}
    for line in sh("dpkg-query -W -f='${Package} ${Version} ${db:Status-Abbrev}\\n'").splitlines():
        f = line.split()
        if len(f) >= 3 and f[2].startswith("i"):
            pk[f[0]] = f[1]
    ap = None
    if os.path.exists("/sys/kernel/security/apparmor/profiles"):
        try:
            ap = sorted(open("/sys/kernel/security/apparmor/profiles").read().splitlines())
        except OSError as e:
            ap = ["(unreadable: %s)" % e]
    polkit = {p: sha(p) for pat in ("/etc/polkit-1/rules.d/*", "/usr/share/polkit-1/rules.d/*", "/etc/polkit-1/localauthority/*/*",
                                    "/var/lib/polkit-1/localauthority/*/*") for p in glob.glob(pat)}
    nft = sh("nft list ruleset") if os.path.exists("/usr/sbin/nft") else None
    ufw = sh("ufw status verbose") if os.path.exists("/usr/sbin/ufw") else None
    return {"files": files, "passwd": passwd, "groups": groups, "units": units, "packages": pk, "apparmor": ap, "polkit": polkit,
            "nft": nft, "ufw": ufw}


def owned_set():
    own = set()
    for l in glob.glob("/var/lib/dpkg/info/*.list"):
        try:
            for line in open(l, errors="replace"):
                p = line.rstrip("\n")
                for a in ("/bin", "/sbin", "/lib", "/lib64"):
                    if p == a or p.startswith(a + "/"):
                        p = "/usr" + p
                        break
                own.add(p)
        except OSError:
            pass
    return own


def noisy(p):
    return any(p.startswith(n) for n in NOISE_CHANGED)


def members(lines):
    d = {}
    for l in lines:
        f = l.split(":")
        if len(f) >= 4:
            d[f[0]] = (f[2], sorted(x for x in f[3].split(",") if x))
    return d


def diff(a, b):
    own = owned_set()
    A, B = a["files"], b["files"]
    added = sorted(p for p in B if p not in A)
    removed = sorted(p for p in A if p not in B)
    changed = sorted(p for p in B if p in A and B[p] != A[p] and not noisy(p))
    r = {
        "added_owned": sum(1 for p in added if p in own),
        "added_unowned": [p for p in added if p not in own],
        "removed": removed,
        "changed": [p for p in changed],
        "new_packages": sorted(set(b["packages"]) - set(a["packages"])),
        "gone_packages": sorted(set(a["packages"]) - set(b["packages"])),
    }
    pa, pb = {l.split(":")[0]: l for l in a["passwd"]}, {l.split(":")[0]: l for l in b["passwd"]}
    r["users_added"] = sorted(pb[u] for u in pb if u not in pa)
    r["users_removed"] = sorted(pa[u] for u in pa if u not in pb)
    r["users_changed"] = sorted("%s -> %s" % (pa[u], pb[u]) for u in pa if u in pb and pa[u] != pb[u])
    ga, gb = members(a["groups"]), members(b["groups"])
    r["groups_added"] = sorted("%s(%s) members %s" % (g, gb[g][0], ",".join(gb[g][1])) for g in gb if g not in ga)
    r["groups_removed"] = sorted(g for g in ga if g not in gb)
    mc = []
    for g in gb:
        if g in ga and ga[g] != gb[g]:
            plus, minus = sorted(set(gb[g][1]) - set(ga[g][1])), sorted(set(ga[g][1]) - set(gb[g][1]))
            mc.append("%s: +%s -%s%s" % (g, ",".join(plus), ",".join(minus), "" if ga[g][0] == gb[g][0] else " (gid changed)"))
    r["group_members"] = sorted(mc)
    ua, ub = a["units"], b["units"]
    r["units_changed"] = sorted("%s: %s -> %s" % (u, ua.get(u, "-"), ub.get(u, "-")) for u in set(ua) | set(ub) if ua.get(u) != ub.get(u))
    r["apparmor"] = None if a["apparmor"] is None or b["apparmor"] is None else {
        "added": sorted(set(b["apparmor"]) - set(a["apparmor"])), "removed": sorted(set(a["apparmor"]) - set(b["apparmor"]))}
    r["polkit"] = sorted("%s: %s -> %s" % (p, a["polkit"].get(p, "-"), b["polkit"].get(p, "-"))
                         for p in set(a["polkit"]) | set(b["polkit"]) if a["polkit"].get(p) != b["polkit"].get(p))
    r["nft_changed"] = a["nft"] != b["nft"]
    r["ufw_changed"] = a["ufw"] != b["ufw"]
    return r


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "snap":
        json.dump(snap(), open(sys.argv[2], "w"))
    elif len(sys.argv) == 4 and sys.argv[1] == "diff":
        print(json.dumps(diff(json.load(open(sys.argv[2])), json.load(open(sys.argv[3]))), indent=1))
    else:
        sys.exit(__doc__)
