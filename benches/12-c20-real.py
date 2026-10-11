#!/usr/bin/env python3
"""12-c20-real — C20 WITH REAL BROWSERS: after "Log out" and a new login from
the same page, the screen does not flicker.

    python3 benches/12-c20-real.py --box gnome [--browser firefox,chrome]
        [--visible] [--save DIR] [--wait-reentry 3]

⛔ WHY IT EXISTS.  `11-c20-…py` (the network mesh) uses the Python client,
   and on 23 Sep 2026, evening, on gnome it gave "I could not look": the
   second login is ADMITTED and one second later it is the CLIENT that closes
   the connection (in the server log the closing is silent, that is, in
   draining: the other side asked for it).  Then the mesh, giving up, runs
   `loginctl terminate-user` — and that is the signal 15 that was read in the
   journal.  ⇒ The Python client can point where to look, ⛔ but it cannot
   certify nor clear: the user, 23 Sep 2026, *"tests must be done with
   real browsers, not with emulators"*.

⭐ WHAT IT DOES, for each browser (Firefox with Marionette, Chrome with CDP, the
   drivers are those of `12-real-clients.py`, ⛔ not a copy):
     1  opens the page, logs in, waits for the first non-degenerate frame
     2  inside the session, the "Log out" gesture OF THE MENU (C20's table)
     3  waits for the product to declare the session over (C20's two
        forms) and looks at what the PAGE does: back to the form? with which sentence?
     4  after `--wait-reentry` seconds it logs in again FROM THE SAME PAGE, as
        the user does — and if the form is not there, it reloads (and says so)
     5  first frame, then it starts C20's scene in the session (constant
        light, scrolling bands) and photographs the canvas for `--watch-s`
     6  judges the luminances with C20's judge (⛔ the same one, imported):
        a flicker between desktop, logout screen and black is RED
   Outcomes: 0 green · 1 red · 3 I could not look, with the reason.

⚠ The box is entered with `fondamenta/strumenti/sshpw.py` and `sudo podman
  exec rete11-<scatola>`: it is the same route as `11-hook.sh remote`.
⚠ The tenant is `c20u7<n>`, inside the network's namespace: if this bench
  died halfway, the hook clears it out and C19 sees it.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SSHPW = os.path.join(ROOT, "fondamenta", "strumenti", "sshpw.py")
LOG = "/var/lib/rete11/registro.log"
SCENE_INSIDE = "/opt/remotix/11-c20-scene.html"
PORTS = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}


def _load(name, file):
    s = _iu.spec_from_file_location(name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


VERI = _load("client_veri", os.path.join(HERE, "12-real-clients.py"))
C20 = _load("c20", os.path.join(HERE, "11-boxes",
                                  "11-c20-rebirth-brings-no-ghosts.py"))
GREEN, RED, BLIND = VERI.GREEN, VERI.RED, VERI.BLIND


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE BOX
# ═══════════════════════════════════════════════════════════════════════════
class Box:
    def __init__(self, name):
        self.name = name
        self.container = "rete11-%s" % name

    def inside(self, line, seconds=90):
        """(code, output) of `line` run as root in the box.

        ⚠ The line travels in base64: no quote to escape across three
          shells (tablet → ssh → sudo → podman → sh)."""
        b = base64.b64encode(line.encode()).decode()
        remote = ("sudo -S -p 'Password sudo: ' podman exec %s sh -c "
                  "\"$(echo %s | base64 -d)\"; echo \"@@code=$?\""
                  % (self.container, b))
        try:
            r = subprocess.run([sys.executable, SSHPW, remote], capture_output=True,
                               text=True, errors="replace", timeout=seconds)
        except subprocess.TimeoutExpired:
            return None, "(no answer in %d s)" % seconds
        text = "\n".join(x for x in r.stdout.splitlines()
                          if not x.startswith("tput:") and "Password sudo" not in x)
        code = None
        if "@@code=" in text:
            text, _, c = text.rpartition("@@code=")
            try:
                code = int(c.strip())
            except ValueError:
                code = None
        return code, text.strip()

    def log_line_list(self):
        c, t = self.inside("wc -l < %s" % LOG, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError):
            return None

    def log_from(self, sign, chi):
        _c, t = self.inside("tail -n +%d %s | grep -a -- '%s'" % (sign + 1, LOG, chi),
                            60)
        return t.splitlines()

    def exit_gesture(self):
        """(desktop, gesture) — the same question as C20, asked inside."""
        for name, required_cmd, unwanted, gesture in C20.DESKTOPS_AND_GESTURES:
            c, _ = self.inside("command -v %s >/dev/null 2>&1" % required_cmd, 30)
            if c != 0:
                continue
            if unwanted:
                c2, _ = self.inside("command -v %s >/dev/null 2>&1" % unwanted, 30)
                if c2 == 0:
                    continue
            return name, gesture
        return None, None

    def as_user(self, chi, command, seconds=60):
        return self.inside(
            "u=$(id -u %s) && runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus %s 2>&1"
            % (chi, chi, command), seconds)

    def turn_on_scene(self, chi):
        c, t = self.inside(
            "u=$(id -u %s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
            "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
            "[ -f %s ] || { echo 'missing %s'; exit 2; }; "
            "setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
            "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
            "firefox-esr --kiosk file://%s < /dev/null > /home/%s/.c20v-scena.log 2>&1 & "
            "for i in $(seq 1 40); do pgrep -u %s -f firefox-esr >/dev/null && "
            "{ echo started; exit 0; }; sleep 0.25; done; echo 'it was not seen'; exit 1"
            % (chi, SCENE_INSIDE, SCENE_INSIDE, chi, chi, SCENE_INSIDE, chi, chi), 60)
        return c == 0, t

    def create(self, chi, password):
        return self.inside(
            "useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
            % (chi, chi, password), 60)

    def clear_out(self, chi):
        # ⛔ `[c]20u7…`: `pkill -f` would catch the shell that runs it.
        self.inside("loginctl terminate-user %s >/dev/null 2>&1; "
                    "pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null; "
                    "pkill -KILL -u %s >/dev/null 2>&1; sleep 0.5; "
                    "userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1; "
                    "rm -rf /home/%s"
                    % (chi, chi[0], chi[1:], chi, chi, chi, chi), 90)


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def luminance(png):
    """The mean luminance of the canvas photograph, or None."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("L").resize(
            (C20.WIDTH, C20.ALTEZZA))
        px = list(im.getdata())
        return sum(px) // len(px)
    except Exception:                            # noqa: BLE001
        return None


def desktop_dark_but_alive(e, m, s):
    """⭐ (outcome, reason) of the first frame, with the 4K tolerance.

    ⛔ `[M]` 23 Sep 2026, xfce in 4K: the box's background is BLACK, and at
       3840x2160 panel, icons and clock cover 2.7 % ⇒ the judge of
       `12-real-clients` (dominant >= 97 %) called it "degenerate" — but the
       photograph showed the real desktop.  ⇒ Here a desktop with painted
       frames and AT LEAST 40 distinct colours is alive: the real judgement of
       this bench is the scene started afterwards, not the first frame."""
    if e == GREEN:
        return e, m
    import re
    c = re.search(r"distinct colours (\d+)", m or "")
    if (s or {}).get("painted") and c and int(c.group(1)) >= 40:
        return GREEN, "dark but alive desktop (%s distinct colours): %s" % (c.group(1), m)
    return e, m


def wait_line(sc, sign, chi, shapes, cap):
    fine = time.time() + cap
    while time.time() < fine:
        for r in sc.log_from(sign, chi):
            for f in shapes:
                if f in r:
                    return f, r
        time.sleep(2)
    return None, None


def resize_to(g, name, largo, alto):
    """⭐ The window at the size of the specification (4K), and it is READ BACK.

    ⚠ The drivers of `12-real-clients.py` are born at 1400x1000; here the size is
      asked afterwards, and what counts is `innerWidth` read from the page."""
    try:
        if name == "firefox":
            g.m.call("WebDriver:SetWindowRect",
                       {"x": 0, "y": 0, "width": largo, "height": alto})
        elif name == "chrome":
            # ⚠ `[M]` 23 Sep 2026, inside labwc: the size asked with numbers
            #   Chrome ignores (it stayed 1376x888); the "maximised" state is
            #   honoured by the compositor.  That is asked first, then the numbers.
            w = g.cdp.call("Browser.getWindowForTarget")
            wid = w.get("windowId") if isinstance(w, dict) else None
            if wid is None and isinstance(w, dict):
                wid = (w.get("result") or {}).get("windowId")
            g.cdp.call("Browser.setWindowBounds", windowId=wid,
                         bounds={"windowState": "maximized"})
    except Exception as e:                       # noqa: BLE001
        return "⚠ size not changed: %s" % str(e)[:120]
    time.sleep(1)
    try:
        return "window %sx%s (dpr %s)" % tuple(g.js(
            "return [innerWidth, innerHeight, devicePixelRatio]"))
    except Exception as e:                       # noqa: BLE001
        return "⚠ size not read back: %s" % str(e)[:120]


def un_browser(name, o, sc, chi, gesture):
    print("\n══ %s ══════════════════════════════" % name.upper(), flush=True)
    outcome = {"browser": name}
    g = VERI.turn_on_driver(name, o)
    try:
        print("   stage: %s" % g.stage(), flush=True)
        if o.width:
            outcome["window"] = resize_to(g, name, o.width, o.height)
            print("   %s" % outcome["window"], flush=True)
        pr = VERI.Test(g, o, o.url, o.password)

        # ── 1. the first login ─────────────────────────────────────────────
        ok, m = pr.do_open()
        if not ok:
            return dict(outcome, outcome=BLIND, why="the page does not open: " + m)
        e, m, s = pr.enter(o.password)
        if e != GREEN:
            return dict(outcome, outcome=BLIND, why="first login: " + m)
        e, m, s = pr.first_frame()
        e, m = desktop_dark_but_alive(e, m, s)
        print("   ⭐ first login: %s" % m, flush=True)
        if e != GREEN:
            return dict(outcome, outcome=BLIND, why="first login without image: " + m)
        time.sleep(o.first_s)

        # ── 2. "Log out", the menu gesture ───────────────────────────────
        sign = sc.log_line_list()
        if sign is None:
            return dict(outcome, outcome=BLIND, why="I cannot read the server log")
        c, t = sc.as_user(chi, gesture)
        if c != 0:
            return dict(outcome, outcome=BLIND, why="the «Log out» gesture did not answer "
                        "(code %s): %s" % (c, t[-300:]))
        t_exit = time.time()
        shape, line = wait_line(sc, sign, chi, [p for p, _d in C20.FINISHED_LINES],
                                   o.wait_exit)
        if not shape:
            return dict(outcome, outcome=BLIND, why="%d s after «Log out» the product has not "
                        "declared the session over" % o.wait_exit)
        print("   ⭐ «Log out»: after %.1f s the product says «%s»"
              % (time.time() - t_exit, shape), flush=True)

        # ── 3. what the PAGE does ──────────────────────────────────────────
        form, page = False, {}
        fine = time.time() + 30
        while time.time() < fine:
            try:
                mm = g.js(VERI.JS_MODULE)
                if mm and mm.get("form") and mm.get("visible"):
                    form = True
                    break
            except Exception:                    # noqa: BLE001
                pass
            time.sleep(0.5)
        page = pr.state()
        print("   %s the page after «Log out»: form %s · outcome «%s»"
              % ("⭐" if form else "⚠", "VISIBLE" if form else "NOT visible",
                 (page.get("outcome") or "")[:120]), flush=True)
        outcome["pagina_dopo_esci"] = {"form": form, "outcome": page.get("outcome")}

        # ── 4. the new login, FROM THE SAME PAGE ───────────────────────────
        time.sleep(o.wait_reentry)
        mark2 = sc.log_line_list() or sign
        if not form:
            print("   ⚠ the form is not there: reloading, as the user would", flush=True)
            g.reload()
            ok, m = pr.open_after_reload()
            if not ok:
                return dict(outcome, outcome=BLIND, why="after the reload: " + m)
        e, m, s = pr.enter(o.password)
        if e != GREEN:
            # ⛔ Here the red is the PRODUCT's: after "Log out" the user cannot get back in.
            queue = [x for x in (s or {}).get("log", "").splitlines() if x.strip()][-6:]
            return dict(outcome, outcome=RED, why="after «Log out» it does NOT GET BACK IN: %s" % m,
                        page=queue, server=sc.log_from(mark2, chi)[-25:])
        e, m, s = pr.first_frame()
        e, m = desktop_dark_but_alive(e, m, s)
        print("   %s second login: %s" % ("⭐" if e == GREEN else "⛔", m), flush=True)
        if e != GREEN:
            return dict(outcome, outcome=RED if e == RED else BLIND,
                        why="second login without image: " + m,
                        server=sc.log_from(mark2, chi)[-25:])

        # ── 5. the scene, and the canvas photographed ──────────────────────
        enabled, t = sc.turn_on_scene(chi)
        if not enabled:
            return dict(outcome, outcome=BLIND, why="the scene does not start: %s" % t[-160:])
        print("   ⭐ scene started (%s)" % os.path.basename(SCENE_INSIDE), flush=True)
        lum, d0 = [], (pr.state().get("painted") or 0)
        fine = time.time() + o.watch_s
        while time.time() < fine:
            try:
                png, _p = g.snapshot_canvas()
            except Exception:                    # noqa: BLE001
                png = None
            if png:
                v = luminance(png)
                if v is not None:
                    lum.append(v)
                if o.save and len(lum) % 10 == 1:
                    with open(os.path.join(o.save, "%s-%03d.png" % (name, len(lum))),
                              "wb") as f:
                        f.write(png)
            time.sleep(o.step_s)
        s = pr.state()
        d1 = s.get("painted") or 0
        print("   luminances (%d photographs, %d frames painted): %s"
              % (len(lum), d1 - d0, " ".join(str(x) for x in lum[:80])), flush=True)
        ep, jumps, why = C20.judge_the_pixels(lum)
        server = sc.log_from(mark2, chi)
        interesting = [r for r in server if any(k in r for k in (
            "child spawned", "REAPED", "IS OVER", "has gone", "throwing away",
            "RESTARTING THE CAPTURE", "farewell", "closed"))]
        return dict(outcome, outcome=ep, why=why, jumps=jumps, snapshots=len(lum),
                    painted=d1 - d0, server=interesting[-20:])
    finally:
        try:
            g.close()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--box", default="gnome", choices=sorted(PORTS))
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visible", action="store_true")
    a.add_argument("--save", default="")
    a.add_argument("--first-s", type=float, default=5.0,
                   help="how long the first login stays before «Log out»")
    a.add_argument("--wait-exit", type=float, default=120.0)
    a.add_argument("--wait-reentry", type=float, default=3.0,
                   help="seconds between the session ending and the new login")
    a.add_argument("--watch-s", type=float, default=30.0)
    a.add_argument("--step-s", type=float, default=0.2)
    a.add_argument("--cap-s", type=int, default=45)
    a.add_argument("--base-port", type=int, default=2951)
    # ⭐ The specification is 4K (the user, 23 Sep 2026): the window is brought to
    #   3840x2160.  `--width 0` leaves the drivers' size (1400x1000).
    a.add_argument("--width", type=int, default=3840)
    a.add_argument("--height", type=int, default=2160)
    o = a.parse_args()
    # ⚠ the fields that the drivers and `Test` of 12-real-clients expect
    o.url = "https://%s:%d/" % (o.host, PORTS[o.box])
    o.password = C20.PASSWORD
    o.scene, o.continuity_s, o.log_cmd = "alive", 8, ""
    o.leave_running = False
    if o.save:
        os.makedirs(o.save, exist_ok=True)
    sc = Box(o.box)
    desktop, gesture = sc.exit_gesture()
    if not gesture:
        print("⛔ I do not know how to say «Log out» in %s ⇒ 3" % sc.container)
        return 3
    chi = "c20u7%02d" % random.randint(0, 99)
    o.user = chi
    print("⭐ 12-c20-real · %s (%s) · %s · tenant %s · browser %s · %s"
          % (sc.container, desktop, o.url, chi, o.browser,
             "real windows" if o.visible else "HEADLESS"))
    print("   «Log out» is said: %s" % gesture)
    lines = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.clear_out(chi)
        c, t = sc.create(chi, o.password)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = un_browser(b, o, sc, chi, gesture)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "outcome": BLIND, "why": "the bench fell over: %r" % e}
        finally:
            sc.clear_out(chi)
        print("   ▶ %s: %s — %s" % (b, {0: "GREEN", 1: "RED", 3: "I COULD NOT LOOK"}
                                   .get(r["outcome"], r["outcome"]), r.get("why")))
        for x in r.get("server") or []:
            print("      server: %s" % x[:200])
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        lines.append(r)
    v = [r["outcome"] for r in lines]
    return 1 if 1 in v else (3 if 3 in v else 0)


if __name__ == "__main__":
    sys.exit(main())
