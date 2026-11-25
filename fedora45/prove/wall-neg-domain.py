#!/usr/bin/python3
# wall-neg-domain.py: negative test of the wall, run INSIDE the domain remotix_net_t as uid 0 WITH ALL CAPABILITIES (so that the Unix permissions
# and the capabilities of the process say YES to everything: only SELinux can say no) against targets any Unix user could reach (files of root,
# sockets made 0666 by the harness).  Each attempt prints one JSON line {n, label, t0, t1, outcome, errno}; wall-selinux.sh then looks in the
# journal for an AVC of this process between t0 and t1 for EVERY attempt that must be refused.
import errno, json, os, signal, socket, subprocess, sys, time

n = 0
# the results go to stdout, which must be the one the ssh session gave (a pipe made by the shell is not writable by remotix_net_t, and as root
# without CAP_DAC_OVERRIDE the domain cannot even open a file in its own 0700 folder)
OUT = sys.stdout
PHASE = os.environ.get("RXNEG_PHASE", "denied")   # "denied": uid 0 with all capabilities; "allowed": the uid remotix, the way the real network side runs
def attempt(label, fn, want_denied=True):
    global n
    if (PHASE == "denied") != want_denied:
        return
    n += 1
    t0 = time.time(); out = "allowed"; en = 0
    try:
        fn()
    except OSError as e:
        en = e.errno; out = "denied" if e.errno in (errno.EACCES, errno.EPERM) else "other:" + errno.errorcode.get(e.errno, str(e.errno))
    except Exception as e:
        out = "exception:" + repr(e)[:60]
    t1 = time.time()
    time.sleep(0.6)   # one attempt per window: the checker looks for the AVC between t0 and t1 of THIS attempt only
    print(json.dumps({"n": n, "label": label, "t0": t0, "t1": t1, "want": "denied" if want_denied else "allowed", "outcome": out, "errno": en}), file=OUT, flush=True)

E = os.environ
attempt("read /etc/shadow (root's file)", lambda: open("/etc/shadow").read(1))
attempt("list a user's home", lambda: os.listdir(E.get("RXNEG_HOME", "/home/prova")))
attempt("read a user's .bashrc", lambda: open(E.get("RXNEG_HOME", "/home/prova") + "/.bashrc").read(1))
attempt("read a file of the root side's state (/var/lib/remotix)", lambda: open("/var/lib/remotix/render-grants.negtest").read(1))
attempt("write the root side's runtime folder /run/remotix/prelocal", lambda: open("/run/remotix/prelocal/negtest", "w"))
attempt("execve /bin/sh", lambda: subprocess.run(["/bin/sh", "-c", "id"], check=True))
attempt("execve /usr/bin/id", lambda: subprocess.run(["/usr/bin/id"], check=True))
attempt("write /etc/rx-negtest", lambda: open("/etc/rx-negtest", "w"))
attempt("create /usr/libexec/remotix/rx-negtest", lambda: open("/usr/libexec/remotix/rx-negtest", "w"))
attempt("write /var/lib/remotix/escape (parent of its folder)", lambda: open("/var/lib/remotix/escape", "w"))
attempt("create a TCP socket", lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM))
attempt("create a UDP socket (to open another port)", lambda: socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
attempt("create an IPv6 UDP socket", lambda: socket.socket(socket.AF_INET6, socket.SOCK_DGRAM))
attempt("create a raw socket", lambda: socket.socket(socket.AF_INET, socket.SOCK_RAW))
attempt("create a packet socket", lambda: socket.socket(socket.AF_PACKET, socket.SOCK_RAW))
attempt("connect to an X socket (0666, listening: /tmp/.X11-unix/X77)", lambda: socket.socket(socket.AF_UNIX).connect("/tmp/.X11-unix/X77"))
attempt("connect to a user's socket in /run/user (0666, listening)", lambda: socket.socket(socket.AF_UNIX).connect(E["RXNEG_USERSOCK"]))
attempt("connect to /run/systemd/private (PID 1's private socket)", lambda: socket.socket(socket.AF_UNIX).connect("/run/systemd/private"))
attempt("read memory of pid 1 (/proc/1/environ)", lambda: open("/proc/1/environ").read(1))
attempt("signal a root-side process (SIGURG to the service's main pid)", lambda: os.kill(int(E["RXNEG_ROOTPID"]), signal.SIGURG))
attempt("ptrace-style access: read /proc/<root side>/mem", lambda: open("/proc/%s/mem" % E["RXNEG_ROOTPID"], "rb").read(1))

# D-Bus: logind is the one thing it may ask (the allowed one runs in the phase "allowed", as uid remotix); anything else on the system bus is refused by the bus (SELinux user_avc)
def dbus_call(dest, path, iface, method):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib
    c = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    try:
        c.call_sync(dest, path, iface, method, None, None, Gio.DBusCallFlags.NONE, 3000, None)
    except GLib.Error as e:
        raise OSError(errno.EACCES if "SELinux" in e.message or "denied" in e.message.lower() or "Rejected" in e.message else errno.EIO, e.message)
attempt("D-Bus: ListSessions on logind (allowed: the net side asks it)", lambda: dbus_call("org.freedesktop.login1", "/org/freedesktop/login1", "org.freedesktop.login1.Manager", "ListSessions"), want_denied=False)
attempt("D-Bus: ListUnits on systemd1 (a service other than logind)", lambda: dbus_call("org.freedesktop.systemd1", "/org/freedesktop/systemd1", "org.freedesktop.systemd1.Manager", "ListUnits"))
attempt("D-Bus: Ping to polkit (another service)", lambda: dbus_call("org.freedesktop.PolicyKit1", "/", "org.freedesktop.DBus.Peer", "Ping"))

# the one place it may write
def okwrite():
    p = "/var/lib/remotix/net/ok-test"; open(p, "w").close(); os.unlink(p)
attempt("write /var/lib/remotix/net (its own folder)", okwrite, want_denied=False)
