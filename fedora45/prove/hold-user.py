"""hold-user.py - like hold.py, but the user is made by US (the SELinux step's tests, 22 Nov 2026): no card groups added by the harness
(the product's own enrolment at the first connection must do it), and the SELinux user mapped as asked.
    RX_BANCO=vm RX_BOX=gnome RX_USER=en1 RX_PASS=en1pass2026 RX_SELUSER=staff_u|user_u|unconfined_u|- [RX_NOEND=1] python3 hold-user.py [seconds]
Writes /tmp/hold-ready when the desktop has arrived.  RX_NOEND=1: the user's existing sessions/manager are NOT ended first (a stale user manager
for the card grant).  The orphan test is this plus `pkill -9 -u <user> -x remotix` and a look at the journal: «no orphan desktops»."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

user, password, sel = os.environ["RX_USER"], os.environ["RX_PASS"], os.environ.get("RX_SELUSER", "-")

def eu(self, u, p):
    key = (self.name, u)
    if key not in lib._made:
        lib._made.add(key)
        if not os.environ.get('RX_NOEND'):
            self.end_users([u])
        lib._register_cleanup()
    cmd = ("id %s >/dev/null 2>&1 || useradd -m -s /bin/bash %s; echo '%s:%s' | chpasswd; "
           "gpasswd -d %s video >/dev/null 2>&1; gpasswd -d %s render >/dev/null 2>&1; " % (u, u, u, p, u, u))
    if sel != "-":
        cmd += "semanage login -m -s %s %s 2>/dev/null || semanage login -a -s %s %s; " % (sel, u, sel, u)
    cmd += "id %s; semanage login -l | grep -w %s" % (u, u)
    c, t = self.run(cmd)
    print("user made:", t.strip().replace("\n", " | ")[:300], flush=True)

lib.Box.ensure_user = eu
rig = lib.Rig(os.environ.get("RX_BOX", "gnome"), "chrome", user, password, "hold", cap=60)
try:
    rig.start()
    rig.open_page()
    try:
        s = rig.login()
    except Exception as e:  # noqa: BLE001
        print("login NOT admitted:", type(e).__name__, str(e)[:400], flush=True)
        raise SystemExit(3)
    print("login:", s["outcome"].strip(), flush=True)
    try:
        d = rig.settle(60)
    except lib.Fail as e:   # a desktop that does not come up is an answer too: the processes are looked at all the same
        print("desktop NOT settled:", str(e)[:200], flush=True)
    print("desktop ok, holding", flush=True)
    open("/tmp/hold-ready", "w").write("1")
    time.sleep(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
finally:
    rig.stop()
    print("stopped", flush=True)
