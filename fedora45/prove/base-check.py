#!/usr/bin/env python3
"""base-check - the small end-to-end check of a running REMOTIX box, with a real browser.

    python3 base-check.py [--box xfce] [--browser chrome|firefox] [--user prova] [--password prova2026]

Runs ON THE DEV SERVER (it drives ./boxes/box.sh and a headless labwc there). One line per check:
    PASS|FAIL|BLOCKED <name> - evidence
exit 0 only if all five PASS. Checks: page, login, desktop, mouse, keyboard.
  FAIL    = the product did not do it.   BLOCKED = the tool could not look (an earlier check failed, or a tool step broke).
Mouse and keyboard are proven INSIDE the box: a fullscreen GTK window in the user's session logs the events it receives.
Pictures go to <prove>/shots/ (one screenshot of the client page per run, plus the desktop canvas)."""
import argparse
import io
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import browserlib  # noqa: E402

PORTS = {"gnome": 8821, "kde": 8822, "xfce": 8823, "lxqt": 8824}  # boxes/box.sh header
if os.environ.get("RX_BANCO") == "vm":  # as in lib.py: the QEMU VMs (banco-vm/box.sh) instead of the containers
    PORTS = {"gnome": 8841, "kde": 8842, "xfce": 8843, "lxqt": 8844}
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
TYPED = "remotix2"

# JS bodies (page ids and counters as in src/page.html)
JS_FORM = ("const f=document.getElementById('signin-form'); const v=e=>!!e&&getComputedStyle(e).display!=='none'"
           "&&e.getBoundingClientRect().width>0; return {title:document.title, form:v(f), user:!!document.getElementById('username'),"
           " pw:!!document.getElementById('password'), btn:!!document.getElementById('signin-button'), remotix:!!window.REMOTIX,"
           " ready:document.readyState};")
JS_ENTER = ("const u=document.getElementById('username'),p=document.getElementById('password'),m=document.getElementById('signin-form');"
            "u.value=arguments[0]; p.value=arguments[1]; u.dispatchEvent(new Event('input',{bubbles:true}));"
            "p.dispatchEvent(new Event('input',{bubbles:true})); m.requestSubmit(document.getElementById('signin-button')); return 1;")
JS_STATE = ("const R=window.REMOTIX, s=R&&R.viewer, o=document.getElementById('outcome'), t=document.getElementById('viewer');"
            "const r=t?t.getBoundingClientRect():null; return {session:!!(s&&s.session), cls:o?o.className:'', outcome:o?o.textContent:'',"
            " painted:s&&s.counts?s.counts.painted:0, delivered:s&&s.counts?s.counts.delivered:0, input:!!window.REMOTIX_INPUT,"
            " rect:r?[r.left,r.top,r.width,r.height]:null, vw:innerWidth, vh:innerHeight,"
            " log:(document.getElementById('logbook')||{}).textContent||''};")


def say(results, status, name, evidence):
    results[name] = status
    print("%s %s — %s" % (status, name, evidence), flush=True)


def judge_pixel(png):
    """(degenerate, description). Degenerate = (nearly) one colour: black, grey, waiting colour. A real desktop has at
    least a panel or an icon: >= 6 distinct colours (5 bits per channel) on a 160x120 reduction."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    pic = im.resize((min(160, im.width), min(120, im.height)))
    count = {}
    for r, g, b in pic.getdata():
        k = (r >> 3, g >> 3, b >> 3)
        count[k] = count.get(k, 0) + 1
    dom = max(count.values()) / (pic.width * pic.height)
    return len(count) < 6, "%dx%d, %d distinct colours, dominant %.1f%%" % (im.width, im.height, len(count), 100 * dom)


# the desktop shell of each box must be running (and, on KDE, the splash screen gone) before the picture is judged
SHELL_UP = {"xfce": "pgrep -u %(u)s xfce4-panel", "lxqt": "pgrep -u %(u)s lxqt-panel", "gnome": "pgrep -u %(u)s gnome-shell",
            "kde": "pgrep -u %(u)s plasmashell && ! pgrep -u %(u)s ksplashqml"}


def settled(a, b):
    """True when two PNG pictures differ by less than 1 grey level on average (160x120 reduction): nothing is moving."""
    from PIL import Image, ImageChops, ImageStat
    x, y = (Image.open(io.BytesIO(p)).convert("L").resize((160, 120)) for p in (a, b))
    return ImageStat.Stat(ImageChops.difference(x, y)).mean[0] < 1.0


def selftest():
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (320, 200), (0, 0, 0)).save(b, "PNG")
    d, t = judge_pixel(b.getvalue())
    print("selftest: black picture is degenerate: %s (%s)" % (d, t))
    return 0 if d else 1


class Box:
    def __init__(self, a):
        self.name, self.sh = a.box, os.path.join(a.boxes, "box.sh")

    def run(self, cmd, stdin=None, timeout=60):
        r = subprocess.run([self.sh, "ssh", self.name, cmd], input=stdin, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()


def canvas_png(g, rect):
    if hasattr(g, "canvas_shot"):
        return g.canvas_shot("#viewer")
    return g.screenshot(clip=rect)


def wait_state(g, cond, cap):
    end, s = time.time() + cap, {}
    while time.time() < end:
        s = g.js(JS_STATE)
        if cond(s):
            return s, True
        time.sleep(0.4)
    return s, False


def leave_overview(g, box, user):
    """GNOME is born in the Activities Overview, which covers the desktop: ask the Shell, press a real ESC, verify."""
    q = ("u=$(id -u %s); runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus "
         "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.freedesktop.DBus.Properties.Get "
         "org.gnome.Shell OverviewActive 2>&1" % (user, user))
    for _ in range(3):
        c, t = box.run(q)
        if "<false>" in t:
            return "Overview off"
        g.js("const t=document.getElementById('viewer'); if(t&&t.focus) t.focus(); return 1;")
        g.press("Escape")
        time.sleep(2)
    return "Overview still on or unreadable: " + t[-80:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(PORTS))
    ap.add_argument("--browser", default="chrome", choices=("chrome", "firefox"))
    ap.add_argument("--user", default="prova")
    ap.add_argument("--password", default="prova2026")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--boxes", default=(os.path.join(HERE, "banco-vm") if os.environ.get("RX_BANCO") == "vm" else os.path.join(HERE, "boxes") if os.path.isdir(os.path.join(HERE, "boxes")) else os.path.join(HERE, "..", "boxes")), help="folder with box.sh")
    ap.add_argument("--cap", type=int, default=60, help="seconds allowed for login and first picture")
    ap.add_argument("--shots", default=os.path.join(HERE, "shots"))
    ap.add_argument("--work", default=os.path.join(HERE, "work"), help="browser profiles, compositor dir (persistent disk)")
    ap.add_argument("--selftest", action="store_true", help="check only that the picture judge can say 'degenerate'")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    os.makedirs(a.shots, exist_ok=True)
    os.makedirs(a.work, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    tag = os.path.join(a.shots, "base-%s-%s-%s" % (a.box, a.browser, stamp))
    url = "https://%s:%d/" % (a.host, PORTS[a.box])
    box, res, g, comp = Box(a), {}, None, os.path.join("/run/user", str(os.getuid()), "bc-" + stamp)
    names = ("page", "login", "desktop", "mouse", "keyboard")

    def blocked_from(first, why):
        for n in names[names.index(first):]:
            if n not in res:
                say(res, BLOCKED, n, why)

    try:
        r = subprocess.run([os.path.join(HERE, "headless-wayland.sh"), "start", comp], capture_output=True, text=True)
        if r.returncode:
            blocked_from("page", "no compositor for the browser: " + r.stderr.strip()[-200:])
            return 1
        env = dict(os.environ, XDG_RUNTIME_DIR=comp, WAYLAND_DISPLAY=r.stdout.strip(), XDG_SESSION_TYPE="wayland")
        env.pop("DISPLAY", None)
        g = (browserlib.Chrome if a.browser == "chrome" else browserlib.Firefox)(env, a.work)

        # 1. page
        g.navigate(url)
        end, f = time.time() + 30, {}
        while time.time() < end:
            f = g.js(JS_FORM)
            if f.get("form") and f.get("ready") == "complete":
                break
            time.sleep(0.5)
        if f.get("form") and f.get("user") and f.get("pw") and f.get("btn") and f.get("remotix"):
            say(res, PASS, "page", "%s loaded in %s, login form visible, title \"%s\"" % (url, g.version, f.get("title")))
        else:
            say(res, FAIL, "page", "%s in %s: form not usable: %s" % (url, g.version, f))
            blocked_from("login", "the page did not load")
            return 1

        # 2. login
        g.js(JS_ENTER, a.user, a.password)
        s, ok = wait_state(g, lambda s: (s["session"] and s["cls"] == "good") or s["cls"] == "bad", a.cap)
        if ok and s["session"] and s["cls"] == "good":
            say(res, PASS, "login", "user %s admitted: \"%s\"" % (a.user, s["outcome"].strip()))
        else:
            say(res, FAIL, "login", "user %s not admitted in %d s: outcome \"%s\" (%s); page log tail: %s" % (
                a.user, a.cap, s.get("outcome"), s.get("cls"), " | ".join(s.get("log", "").strip().splitlines()[-3:])[:250]))
            blocked_from("desktop", "no login")
            return 1

        # 3. desktop: decoded frames arrive AND the picture is not uniform
        s, ok = wait_state(g, lambda s: s["painted"] > 0, a.cap)
        if not ok:
            say(res, FAIL, "desktop", "no decoded frame painted in %d s (delivered=%s painted=%s)" % (a.cap, s["delivered"], s["painted"]))
            blocked_from("mouse", "no picture")
            return 1
        t_up, up = time.time(), False
        while time.time() - t_up < a.cap and not up:
            up = box.run(SHELL_UP[a.box] % {"u": a.user})[0] == 0
            time.sleep(1.5)
        shell_s = time.time() - t_up
        extra = leave_overview(g, box, a.user) + "; " if a.box == "gnome" else ""
        # the desktop is "up" when the picture is not uniform AND stays still for 3 shots 1.5 s apart (a splash animates)
        end, desc, still, prev, deg, t0 = time.time() + a.cap, "", 0, None, True, time.time()
        while time.time() < end:
            time.sleep(1.5)
            s = g.js(JS_STATE)
            if not s["rect"] or s["rect"][2] < 4:
                continue
            png = canvas_png(g, s["rect"])
            deg, desc = judge_pixel(png)
            still = still + 1 if (not deg and prev and settled(prev, png)) else 0
            prev = png
            if still >= 3:
                break
        settle = time.time() - t0
        deg = deg or still < 3 or not up
        open(tag + "-desktop.png", "wb").write(png)
        if not up:
            say(res, FAIL, "desktop", "frames painted=%d but the desktop shell (%s) is not up %d s after login; picture: %s"
                % (s["painted"], SHELL_UP[a.box] % {"u": a.user}, a.cap, desc))
            blocked_from("mouse", "no desktop to act on")
            return 1
        if deg:
            say(res, FAIL, "desktop", "frames painted=%d but the picture never became a settled non-uniform desktop in %d s (last: %s)" % (s["painted"], a.cap, desc))
            blocked_from("mouse", "no desktop to act on")
            return 1
        say(res, PASS, "desktop", "%sdecoded frames painted=%d (delivered=%d), picture not uniform and still (%s), shell up %.0f s and picture settled %.0f s after the first frame, saved %s-desktop.png"
            % (extra, s["painted"], s["delivered"], desc, shell_s, settle, os.path.basename(tag)))

        # 4/5. mouse and keyboard, seen from inside the box through the test window
        c, _ = box.run("cat > /tmp/bc-test-window.py", stdin=open(os.path.join(HERE, "test-window.py")).read())
        log = "/tmp/bc-events-%s.log" % stamp
        c, out = box.run(
            "u=$(id -u %s); d=$(ls /run/user/$u | grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] || { echo no wayland socket in /run/user/$u; exit 3; };"
            " rm -f %s; setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d GDK_BACKEND=wayland "
            "python3 /tmp/bc-test-window.py %s </dev/null >%s.err 2>&1 & sleep 0.5; echo started on $d"
            % (a.user, log, a.user, log, log))
        if c != 0:
            blocked_from("mouse", "could not start the test window in the box: " + out[-150:])
            return 1

        def events():
            c, t = box.run("cat %s 2>/dev/null; true" % log)
            import json
            return [json.loads(x) for x in t.splitlines() if x.startswith("{")]
        end = time.time() + 30
        while time.time() < end and not any(e["ev"] == "ready" for e in events()):
            time.sleep(1)
        if not any(e["ev"] == "ready" for e in events()):
            c, err = box.run("tail -c 300 %s.err" % log)
            blocked_from("mouse", "the test window never reported ready in the user's session (%s)" % err.replace("\n", " "))
            return 1
        time.sleep(1.5)  # let the desktop show the window to the client
        s = g.js(JS_STATE)
        L, T, W, H = s["rect"]
        px = lambda fx, fy: (L + W * fx, T + H * fy)  # noqa: E731
        # the pointer is tried again every 2 s for up to 20 s: dead the whole time = FAIL, late = PASS with the delay said
        t_m, tries = time.time(), 0
        while time.time() - t_m < 20 and not [e for e in events() if e["ev"] == "click"]:
            tries += 1
            g.move(*px(0.3, 0.3))
            time.sleep(0.3)
            g.move(*px(0.6, 0.5))
            time.sleep(0.3)
            g.click(*px(0.6, 0.5))
            time.sleep(1.5)
        ev = events()
        clicks, motions = [e for e in ev if e["ev"] == "click"], [e for e in ev if e["ev"] == "motion"]
        if clicks and abs(clicks[0]["fx"] - 0.6) < 0.08 and abs(clicks[0]["fy"] - 0.5) < 0.08:
            say(res, PASS, "mouse", "clicked at (0.60,0.50) of the canvas (attempt %d, %.0f s); the window in the box got %d motion events and a click at (%.2f,%.2f)"
                % (tries, time.time() - t_m, len(motions), clicks[0]["fx"], clicks[0]["fy"]))
        elif clicks:
            say(res, FAIL, "mouse", "click sent at (0.60,0.50) but the box saw it at (%.2f,%.2f)" % (clicks[0]["fx"], clicks[0]["fy"]))
        else:
            say(res, FAIL, "mouse", "click sent %d times in 20 s at (0.60,0.50), %d motion events and NO click reached the window in the box" % (tries, len(motions)))
        g.type_text(TYPED)
        end = time.time() + 8
        while time.time() < end and not [e for e in events() if e["ev"] == "text" and TYPED in e["text"]]:
            time.sleep(0.5)
        texts = [e["text"] for e in events() if e["ev"] == "text"]
        if texts and TYPED in texts[-1]:
            say(res, PASS, "keyboard", "typed \"%s\" in the browser, the window in the box holds \"%s\"" % (TYPED, texts[-1]))
        else:
            say(res, FAIL, "keyboard", "typed \"%s\" in the browser, the window in the box holds %s" % (TYPED, repr(texts[-1]) if texts else "nothing"))
        time.sleep(1)
    except Exception as e:  # noqa: BLE001 - a broken tool step is BLOCKED, never a PASS
        blocked_from("page", "tool error: %s: %s" % (type(e).__name__, str(e)[:250]))
    finally:
        if g:
            try:
                open(tag + "-page.png", "wb").write(g.screenshot())
                print("screenshot of the client page: %s-page.png" % tag)
            except Exception as e:  # noqa: BLE001
                print("no screenshot of the client page: %s" % str(e)[:150])
            g.close()
        box.run("pkill -f bc-test-window.py; true")
        subprocess.run([os.path.join(HERE, "headless-wayland.sh"), "stop", comp])
    return 0 if all(res.get(n) == PASS for n in names) else 1


if __name__ == "__main__":
    sys.exit(main())
