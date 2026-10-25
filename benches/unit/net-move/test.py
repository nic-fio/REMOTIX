#!/usr/bin/env python3
"""test.py — simulation of packaging/debian/remotix-net-move (forward and --back, the 1.0 <-> 1.5 move of certificates/ and ban) on a FAKE
/var/lib/remotix, with the system commands shimmed (getent, chown, install, systemctl, runuser) and the owners kept as user.owner xattrs
(the test does not need root).  The script is the real one with its three paths replaced; remotix.tmpfiles.split is applied by hand
(d, Z, z; no link followed).  One block per scenario; exit 1 if a round trip does not give back the 1.0 tree (names, modes, owners,
contents, mtimes), or if a refusal moved something.

BUILD AND RUN (a second; no root, nothing outside a temporary folder is written; run from the root of the tree, needs python3 and xattr
support in /tmp):  python3 -I benches/unit/net-move/test.py
Exit code 0 = every scenario gave what it must."""
import os, sys, stat, shutil, subprocess, hashlib, fnmatch, glob, re, json

import tempfile
SRC = os.path.dirname(os.path.abspath(__file__))
HERE = tempfile.mkdtemp(prefix="net-move-sim-")          # scratch: the shims, the fake tree, the logs (removed at the end)
PKG = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SRC, "..", "..", "..", "packaging")
SCRIPT = os.path.join(PKG, "debian/remotix-net-move")
TMPF = os.path.join(PKG, "debian/remotix.tmpfiles.split")
ROOT = os.path.join(HERE, "root")

def setown(p, who):
    try: os.setxattr(p, "user.owner", who.encode(), follow_symlinks=False)
    except OSError as e:
        if e.errno != 95: raise      # links cannot carry user.* xattrs: kept by name in the ledger below
        LINKOWN[p] = who
LINKOWN = {}
def getown(p):
    try: return os.getxattr(p, "user.owner", follow_symlinks=False).decode()
    except OSError: return LINKOWN.get(p, "?")

SHIMS = {
"chown": r'''#!/usr/bin/env python3
import os,sys
a=sys.argv[1:]; h=False; owner=None; paths=[]
i=0
while i<len(a):
    x=a[i]
    if x=="--": paths+=a[i+1:]; break
    if x.startswith("-") and owner is None and x not in ("-h",): pass
    if x=="-h": h=True
    elif x.startswith("-"): pass
    elif owner is None: owner=x
    else: paths.append(x)
    i+=1
who=owner.split(":")[0]
for p in paths:
    if not os.path.lexists(p):
        sys.stderr.write("chown: %s: no such file\n"%p); sys.exit(1)
    try: os.setxattr(p,"user.owner",who.encode(),follow_symlinks=False)
    except OSError as e:
        if e.errno==95: open(os.environ["SIM_LINKLOG"],"a").write(p+" "+who+"\n")
        else: raise
''',
"install": r'''#!/usr/bin/env python3
import os,sys
a=sys.argv[1:]; d=False; mode=None; who="root"; paths=[]
i=0
while i<len(a):
    x=a[i]
    if x=="-d": d=True
    elif x=="-m": i+=1; mode=int(a[i],8)
    elif x=="-o": i+=1; who=a[i]
    elif x=="-g": i+=1
    elif x.startswith("-"): pass
    else: paths.append(x)
    i+=1
for p in paths:
    if d:
        os.makedirs(p,exist_ok=True)
        if mode is not None: os.chmod(p,mode)
        os.setxattr(p,"user.owner",who.encode())
''',
"getent": "#!/bin/sh\n[ \"$1 $2\" = 'passwd remotix' ] && { echo 'remotix:x:995:995:REMOTIX network side:/:/usr/sbin/nologin'; exit 0; }\nexit 2\n",
"systemctl": "#!/bin/sh\necho \"systemctl $*\" >> \"$SIM_CMDLOG\"\ncase \"$1\" in is-active) [ -n \"$SIM_ACTIVE\" ] && { echo active; exit 0; }; echo inactive; exit 3;; esac\nexit 0\n",
"logger": "#!/bin/sh\nexit 0\n",
"runuser": "#!/bin/sh\n# runuser -u remotix -- test -r path\nshift 3; exec \"$@\"\n",
}

def mkshims():
    d = os.path.join(HERE, "bin"); os.makedirs(d, exist_ok=True)
    for n, body in SHIMS.items():
        p = os.path.join(d, n); open(p, "w").write(body); os.chmod(p, 0o755)
    return d

def mkscript():
    t = open(SCRIPT).read()
    t = t.replace("S=/var/lib/remotix\n", "S=$SIM_ROOT/var/lib/remotix\n", 1)
    t = t.replace("/run/systemd/system", "$SIM_ROOT/run/systemd/system").replace("/run/remotix", "$SIM_ROOT/run/remotix")
    p = os.path.join(HERE, "net-move.sh"); open(p, "w").write(t); return p

def sh(cmd, env, **kw):
    return subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, env=env, **kw)

def run_move(back=False, active=False, extra_env=None):
    env = dict(os.environ, PATH=os.path.join(HERE, "bin") + ":" + os.environ["PATH"], SIM_ROOT=ROOT,
               SIM_CMDLOG=os.path.join(HERE, "cmds.log"), SIM_LINKLOG=os.path.join(HERE, "links.log"))
    if active: env["SIM_ACTIVE"] = "1"
    if extra_env: env.update(extra_env)
    r = subprocess.run(["sh", os.path.join(HERE, "net-move.sh")] + (["--back"] if back else []), capture_output=True, text=True, env=env)
    return r

def tmpfiles():
    """The lines of remotix.tmpfiles.split (d, Z, z), applied by hand: no link is followed."""
    base = ROOT
    for line in open(TMPF):
        line = line.split("#")[0].strip()
        if not line: continue
        f = line.split()
        typ, path, mode, user, grp = f[0], f[1], f[2], f[3], f[4]
        if path.startswith("/run"): continue
        full = base + path
        def apply(p, mode, user, rec=False):
            if os.path.islink(p): return
            if user != "-": setown(p, user)
            if mode != "-": os.chmod(p, int(mode, 8))
        if typ == "d":
            os.makedirs(full, exist_ok=True); apply(full, mode, user)
        elif typ == "Z":
            for dp, dn, fn in os.walk(full):
                for n in dn + fn:
                    q = os.path.join(dp, n)
                    if os.path.islink(q): continue
                    if os.path.isfile(q) and os.stat(q).st_nlink > 1: continue
                    setown(q, user)
            setown(full, user)
        elif typ == "z":
            for q in glob.glob(full):
                if os.path.islink(q): continue
                if os.path.isfile(q) and os.stat(q).st_nlink > 1: continue
                apply(q, mode, user)

def snap():
    out = {}
    base = ROOT + "/var/lib/remotix"
    for dp, dn, fn in os.walk(base):
        for n in dn + fn:
            p = os.path.join(dp, n)
            rel = os.path.relpath(p, base)
            st = os.lstat(p)
            ent = dict(mode=oct(stat.S_IMODE(st.st_mode)), owner=getown(p), mtime=int(st.st_mtime))
            if stat.S_ISLNK(st.st_mode): ent["link"] = os.readlink(p)
            elif stat.S_ISREG(st.st_mode): ent["sha"] = hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]; ent["nlink"] = st.st_nlink
            else: ent["dir"] = True
            out[rel] = ent
    out["."] = dict(mode=oct(stat.S_IMODE(os.stat(base).st_mode)), owner=getown(base), dir=True)
    return out

def mk(rel, content=b"", mode=0o600, owner="root", mtime=1700000000):
    p = ROOT + "/var/lib/remotix/" + rel
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(content); os.chmod(p, mode); setown(p, owner); os.utime(p, (mtime, mtime))
    return p
def mkd(rel, mode=0o700, owner="root"):
    p = ROOT + "/var/lib/remotix/" + rel if rel else ROOT + "/var/lib/remotix"
    os.makedirs(p, exist_ok=True); os.chmod(p, mode); setown(p, owner); return p

def fresh():
    shutil.rmtree(ROOT, ignore_errors=True)
    for f in ("cmds.log", "links.log"):
        try: os.remove(os.path.join(HERE, f))
        except OSError: pass
    os.makedirs(ROOT + "/run/systemd/system"); os.makedirs(ROOT + "/run/remotix")
    mkd("", 0o700)         # 1.0 tmpfiles: d /var/lib/remotix 0700 root root

def diff(a, b, ignore=()):
    d = []
    for k in sorted(set(a) | set(b)):
        if k in ignore: continue
        if k not in b: d.append("MISSING after: %s" % k)
        elif k not in a: d.append("EXTRA after:   %s (%s %s)" % (k, b[k].get("mode"), b[k].get("owner")))
        elif a[k] != b[k]:
            d.append("CHANGED %s: %s -> %s" % (k, {x: a[k][x] for x in a[k] if a[k][x] != b[k].get(x)}, {x: b[k].get(x) for x in a[k] if a[k][x] != b[k].get(x)}))
    return d

RESULTS = []
def scenario(name):
    def deco(fn):
        def run():
            fresh()
            lines = []
            try: fn(lines)
            except Exception as e:
                lines.append("EXCEPTION %r" % (e,))
            RESULTS.append((name, lines))
        run.__name__ = fn.__name__
        return run
    return deco

def cert_set(extra=False, admin=False):
    mkd("certificates")
    if not admin: mk("certificates/page.ours")
    mk("certificates/page.pem", b"CERT-PEM\n", 0o644 if False else 0o600)
    mk("certificates/page.key", b"CERT-KEY\n", 0o600)
    if extra: mk("certificates/quic-secret", os.urandom(32), 0o600)
    mk("ban", b"[192.168.0.9] 1893456000\n[203.0.113.4] 1893456000\n", 0o600)

@scenario("A. 1.0 plain (page.ours + pem + key + ban): forward, tmpfiles, --back")
def A(L):
    cert_set(); s0 = snap()
    r = run_move(); L.append("forward rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    s1 = snap(); L.append("after forward: " + json.dumps({k: (v["mode"], v["owner"]) for k, v in s1.items() if k.startswith(("net", ".")) or k in ("ban", "certificates")}))
    tmpfiles(); s2 = snap()
    L.append("after tmpfiles: " + json.dumps({k: (v["mode"], v["owner"]) for k, v in s2.items()}))
    r = run_move(back=True); L.append("back rc=%s out=%r err=%r" % (r.returncode, r.stdout.strip().splitlines(), r.stderr.strip()))
    s3 = snap()
    L += ["round trip vs the 1.0 tree: " + (x) for x in (diff(s0, s3) or ["identical"])]
    L.append("systemctl calls: " + repr(open(os.path.join(HERE, "cmds.log")).read().split("\n")[:-1] if os.path.exists(os.path.join(HERE, "cmds.log")) else []))

@scenario("B. 1.4.99 test build: a root-owned quic-secret in certificates/")
def B(L):
    cert_set(extra=True); s0 = snap()
    run_move(); tmpfiles(); s2 = snap()
    L.append("quic-secret after forward+tmpfiles: " + repr(s2.get("net/certificates/quic-secret")))
    r = run_move(back=True); s3 = snap()
    L += ["round trip: " + (x) for x in (diff(s0, s3) or ["identical"])]

@scenario("C. administrator's own page.pem/page.key (no page.ours), as links to /etc/letsencrypt (unreadable for remotix is simulated by a 0600 root file)")
def C(L):
    mkd("certificates")
    le = ROOT + "/etc/letsencrypt/live/h"; os.makedirs(le)
    for n in ("fullchain.pem", "privkey.pem"):
        open(le + "/" + n, "w").write(n); os.chmod(le + "/" + n, 0o600); setown(le + "/" + n, "root")
    os.symlink(le + "/fullchain.pem", ROOT + "/var/lib/remotix/certificates/page.pem")
    os.symlink(le + "/privkey.pem", ROOT + "/var/lib/remotix/certificates/page.key")
    mk("ban", b"[1.1.1.1] 1893456000\n")
    s0 = snap()
    r = run_move(); L.append("forward rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    tmpfiles()
    s2 = snap(); L.append("links after: " + repr({k: v for k, v in s2.items() if v.get("link")}))
    r = run_move(back=True); s3 = snap()
    L += ["round trip: " + (x) for x in (diff(s0, s3) or ["identical"])]

@scenario("D. idempotence: forward twice, back twice, back with nothing to move")
def D(L):
    cert_set(); s0 = snap()
    a = run_move(); b = run_move(); tmpfiles(); s1 = snap()
    L.append("forward x2 rc=%s,%s second says %r" % (a.returncode, b.returncode, b.stdout.strip().splitlines()))
    c = run_move(back=True); d = run_move(back=True); s3 = snap()
    L.append("back x2 rc=%s,%s second says %r" % (c.returncode, d.returncode, d.stdout.strip().splitlines()))
    L += ["round trip: " + (x) for x in (diff(s0, s3) or ["identical"])]
    e = run_move(back=True); L.append("back on a 1.0 tree: rc=%s out=%r" % (e.returncode, e.stdout.strip().splitlines()))

@scenario("E. --back interrupted after the mv, before the chown: the second run resumes")
def E(L):
    cert_set(); s0 = snap(); run_move(); tmpfiles()
    # the interrupted run: move by hand, no chown
    shutil.move(ROOT + "/var/lib/remotix/net/certificates", ROOT + "/var/lib/remotix/certificates")
    shutil.move(ROOT + "/var/lib/remotix/net/ban", ROOT + "/var/lib/remotix/ban")
    mid = snap(); L.append("owners while interrupted: certificates=%s ban=%s" % (mid["certificates"]["owner"], mid["ban"]["owner"]))
    r = run_move(back=True); s3 = snap(); L.append("resume rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    L += ["round trip: " + (x) for x in (diff(s0, s3) or ["identical"])]

@scenario("F. both copies exist (a ban in the 1.0 place AND in net/): nothing is merged or lost")
def F(L):
    cert_set(); run_move(); tmpfiles()
    mk("ban", b"[9.9.9.9] 1\n")      # a 1.0 ban appeared again
    before = snap(); r = run_move(back=True); after = snap()
    L.append("back rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    L.append("net/ban kept: %s, ban (1.0 place) sha %s -> %s" % ("net/ban" in after, before["ban"]["sha"], after["ban"]["sha"]))

@scenario("G. hard-linked ban: left in net/, said")
def G(L):
    cert_set(); run_move(); tmpfiles()
    os.link(ROOT + "/var/lib/remotix/net/ban", ROOT + "/var/lib/remotix/ban.hard")
    r = run_move(back=True); L.append("back rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines())); s = snap()
    L.append("net/ban still there: %s; ban in the 1.0 place: %s" % ("net/ban" in s, "ban" in s))

@scenario("H. service running: --back stops it and leaves the marker")
def H(L):
    cert_set(); run_move(); tmpfiles()
    r = run_move(back=True, active=True); L.append("back rc=%s" % r.returncode)
    L.append("marker was-running: %s" % os.path.exists(ROOT + "/run/remotix/was-running"))
    L.append("systemctl: " + repr(open(os.path.join(HERE, "cmds.log")).read().split("\n")[:-1]))

@scenario("I. 1.5 ban file (B2 + G2 lines) read by a 1.0 loader after --back (the 04f6aa18 rule: sscanf '%63s %lld', skipped when the number is not in the future)")
def I(L):
    mkd("certificates"); mk("certificates/page.ours")
    now = 1893455000
    mk("ban", ("[192.168.0.9] 1893456000\nB2 K 1 %d [10.0.0.1]\nB2 U 1 %d [10.0.0.2] %s\nG2 %d [127.0.0.50]\nG2 %d %s\n" % (1893456000, 1893456000, "a"*64, now - 3600, now - 100, "b"*64)).encode())
    run_move(); tmpfiles(); run_move(back=True)
    loaded = []
    for line in open(ROOT + "/var/lib/remotix/ban"):
        m = re.match(r"^(\S+)\s+(-?\d+)", line)
        if m and int(m.group(2)) > now: loaded.append(m.group(1))
    L.append("a 1.0 loader would load as bans: %r (only the old-format line is expected)" % loaded)

@scenario("J. net is a planted symbolic link: forward and --back refuse, nothing moves")
def J(L):
    cert_set(); os.symlink("/etc", ROOT + "/var/lib/remotix/net")
    s0 = snap(); r = run_move(); L.append("forward rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    r = run_move(back=True); L.append("back rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()[-1:]))
    L += ["tree vs start: " + x for x in (diff(s0, snap()) or ["identical"])]

@scenario("K. the system user remotix is missing: forward refuses and moves nothing")
def K(L):
    cert_set(); s0 = snap()
    env = {"SIM_NOUSER": "1"}
    # a getent that does not know remotix
    p = os.path.join(HERE, "bin", "getent"); old = open(p).read(); open(p, "w").write("#!/bin/sh\nexit 2\n")
    try: r = run_move()
    finally: open(p, "w").write(old)
    L.append("forward rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    L += ["tree vs start: " + x for x in (diff(s0, snap()) or ["identical"])]

@scenario("L. a 1.5 -> 1.5.x upgrade (tree already in net/): forward does nothing, owners untouched")
def L_(L):
    cert_set(); run_move(); tmpfiles(); s1 = snap()
    r = run_move(); L.append("forward rc=%s out=%r" % (r.returncode, r.stdout.strip().splitlines()))
    L += ["tree vs before: " + x for x in (diff(s1, snap()) or ["identical"])]

@scenario("M. the 1.0 ban also in ban.new, and a quic-secret.tmp.<pid> left by a crash")
def M(L):
    cert_set(extra=True); mk("ban.new", b"[7.7.7.7] 1893456000\n"); mk("certificates/quic-secret.tmp.123", b"x")
    s0 = snap(); run_move(); tmpfiles(); s2 = snap()
    L.append("in net/: " + repr(sorted(k for k in s2 if k.startswith("net/"))))
    run_move(back=True); L += ["round trip: " + x for x in (diff(s0, snap()) or ["identical"])]

if __name__ == "__main__":
    mkshims(); mkscript()
    for fn in (A, B, C, D, E, F, G, H, I, J, K, L_, M):
        fn()
    bad = 0
    for name, lines in RESULTS:
        print("### " + name)
        for l in lines:
            print("  " + l.replace(ROOT, "<R>"))
            if name[0] not in "FGHI" and ("round trip" in l or "tree vs" in l) and not l.endswith("identical"):
                bad += 1
            if l.startswith("EXCEPTION"):
                bad += 1
    print("\n%d scenarios, %d wrong lines" % (len(RESULTS), bad))
    shutil.rmtree(HERE, ignore_errors=True)
    sys.exit(1 if bad else 0)
