"""avlib - what check-audio.py and check-clipboard.py share: own user in the box, compositor + browser, a REAL login (real
mouse and keyboard events through the driver), waiting for a settled desktop, real key chords. Reuses browserlib and the
page ids / JS bodies of base-check.py (imported, not modified)."""
import importlib.util
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import browserlib  # noqa: E402

_spec = importlib.util.spec_from_file_location("base_check", os.path.join(HERE, "base-check.py"))
BC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BC)

PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
PORTS = BC.PORTS
USER, PASSWORD = "ac1", "acpass7391"  # alphanumeric: browserlib.type_text types a-z, 0-9
SLOT = {"xfce": 0, "lxqt": 1, "gnome": 2, "kde": 3}


def say(results, status, name, evidence):
    results[name] = status
    print("%s %s - %s" % (status, name, evidence), flush=True)


class Box:
    def __init__(self, name, boxes):
        self.name, self.sh = name, os.path.join(boxes, "box.sh")

    def run(self, cmd, stdin=None, timeout=90):
        r = subprocess.run([self.sh, "ssh", self.name, cmd], input=stdin, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()

    def ensure_user(self):
        c, t = self.run("id %s >/dev/null 2>&1 || { useradd -m -s /bin/bash %s && echo '%s:%s' | chpasswd; }; id %s"
                        % (USER, USER, USER, PASSWORD, USER))
        return c == 0, t

    def in_session(self, cmd):
        """Run `cmd` detached as the user, inside the user's graphical session environment."""
        return self.run(
            "u=$(id -u %s); d=$(ls /run/user/$u | grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] || { echo no wayland socket; exit 3; };"
            " setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d GDK_BACKEND=wayland "
            "bash -c %s </dev/null >/dev/null 2>&1 & sleep 0.5; echo started" % (USER, USER, _q(cmd)))


PULSE_SCRIPT = r"""
id acs >/dev/null 2>&1 || useradd -m -s /bin/bash acs
u=$(id -u acs); install -d -o acs -g acs -m700 /run/user/$u
mkdir -p /home/acs/.config/pipewire/pipewire-pulse.conf.d
cat > /home/acs/.config/pipewire/pipewire-pulse.conf.d/tcp.conf <<'CONF'
pulse.properties = { server.address = [ "unix:native" { address = "tcp:127.0.0.1:4713" client.access = "unrestricted" } ] }
pulse.cmd = [ { cmd = "load-module" args = "module-null-sink sink_name=ac_null" flags = [ ] } ]
CONF
chown -R acs: /home/acs/.config
R="setsid runuser -u acs -- env XDG_RUNTIME_DIR=/run/user/$u"
pgrep -u acs -x pipewire >/dev/null || $R bash -c "pipewire" </dev/null >/tmp/acs-pw.log 2>&1 &
sleep 1; pgrep -u acs -x pipewire-pulse >/dev/null || $R bash -c "pipewire-pulse" </dev/null >/tmp/acs-pp.log 2>&1 &
sleep 1; pgrep -u acs -x wireplumber >/dev/null || $R bash -c "wireplumber" </dev/null >/tmp/acs-wp.log 2>&1 &
for i in 1 2 3 4 5 6 7 8; do PULSE_SERVER=tcp:127.0.0.1:4713 pactl info 2>/dev/null | grep -q 'Default Sink: ac_null' && { echo pulse-ok; exit 0; }; sleep 1; done
echo pulse-not-ready
"""


def ensure_pulse(boxes):
    """Firefox needs a sound server to start any AudioContext, and the dev server has none: a private PipeWire+pulse with a
    null sink, run by user `acs` inside the lxqt box, reachable on tcp 127.0.0.1:4713 (boxes share the host network).
    Uses only what the box image already has; idempotent."""
    c, t = Box("lxqt", boxes).run("bash -s", stdin=PULSE_SCRIPT, timeout=60)
    return "pulse-ok" in t, t[-150:]


def _q(s):
    return "'" + s.replace("'", "'\\''") + "'"


class FirefoxPrefs(browserlib.Firefox):
    """browserlib.Firefox with extra preferences written into user.js before launch (browserlib itself is not modified)."""

    def __init__(self, env, tmp, port, prefs):
        import json, shutil, socket, tempfile  # noqa: E401
        self.profile = tempfile.mkdtemp(prefix="ff-", dir=tmp)
        p = {"browser.startup.homepage_override.mstone": "ignore", "datareporting.policy.firstRunURL": "",
             "browser.aboutwelcome.enabled": False, "browser.shell.checkDefaultBrowser": False, "marionette.port": port,
             "startup.homepage_welcome_url": "", "browser.startup.page": 0}
        p.update(prefs)
        with open(self.profile + "/user.js", "w") as f:
            for k, v in p.items():
                f.write('user_pref("%s", %s);\n' % (k, json.dumps(v)))
        self.p = subprocess.Popen([shutil.which("firefox-esr"), "--marionette", "--no-remote", "--profile", self.profile, "--width",
                                   "1400", "--height", "900"], env=dict(env, MOZ_ENABLE_WAYLAND="1"),
                                  stdout=open(self.profile + "/out.log", "wb"), stderr=subprocess.STDOUT)
        end = time.time() + 60
        while True:
            try:
                self.s = socket.create_connection(("127.0.0.1", port), timeout=120)
                break
            except OSError:
                if time.time() > end:
                    raise RuntimeError("Marionette did not open port %d" % port)
                time.sleep(0.5)
        self.s.settimeout(180)
        self.buf, self.n = b"", 0
        self._read()
        caps = self.call("WebDriver:NewSession", {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}},
                                                  "acceptInsecureCerts": True})
        self.version = "Firefox " + caps.get("capabilities", {}).get("browserVersion", "?")
        self.call("WebDriver:SetTimeouts", {"script": 60000, "pageLoad": 60000})


class Rig:
    """compositor + browser + real login + settled desktop."""

    def __init__(self, a, tag):
        self.a, self.box, self.g, self.comp = a, Box(a.box, a.boxes), None, None
        self.stamp = "%s-%s-%d" % (tag, time.strftime("%H%M%S"), os.getpid())

    def start(self):
        a = self.a
        os.makedirs(a.work, exist_ok=True)
        self.comp = os.path.join("/run/user", str(os.getuid()), "av-" + self.stamp)
        r = subprocess.run([os.path.join(HERE, "headless-wayland.sh"), "start", self.comp], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("no compositor for the browser: " + r.stderr.strip()[-200:])
        env = dict(os.environ, XDG_RUNTIME_DIR=self.comp, WAYLAND_DISPLAY=r.stdout.strip(), XDG_SESSION_TYPE="wayland")
        env.pop("DISPLAY", None)
        n = SLOT[a.box] + 10 * (a.browser == "firefox")
        if a.browser == "chrome":
            self.g = browserlib.Chrome(env, a.work, port=9500 + n)
        else:
            # the dev server has no sound server, and Firefox then never starts any AudioContext (even a bare one in a click
            # handler): it gets the private pulse server of ensure_pulse() (Chrome has its own fake sink)
            ok, t = ensure_pulse(a.boxes)
            if not ok:
                raise RuntimeError("no sound server for Firefox: " + t)
            env["PULSE_SERVER"] = "tcp:127.0.0.1:4713"
            prefs = {}
            if getattr(a, "firefox_autoplay_pref", False):
                prefs["media.autoplay.default"] = 0
            self.g = FirefoxPrefs(env, a.work, 2900 + n, prefs)
        self.is_chrome = a.browser == "chrome"
        return self.g.version

    def stop(self):
        if self.g:
            self.g.close()
        self.box.run("pkill -u %s -f 'ac-test-window|ac-tone' ; true" % USER)
        if self.comp:
            subprocess.run([os.path.join(HERE, "headless-wayland.sh"), "stop", self.comp])
            time.sleep(0.5)
            subprocess.run(["rm", "-rf", self.comp])  # our own private compositor dir

    # --- real input -------------------------------------------------------------------------------------------
    def center(self, elem_id):
        r = self.g.js("const e=document.getElementById(arguments[0]); const b=e.getBoundingClientRect();"
                      "return [b.left+b.width/2, b.top+b.height/2];", elem_id)
        return r

    def chord(self, key, ctrl=False, cmd=None):
        """One real key (a-z, Enter, Backspace, Delete), optionally with Ctrl. cmd: Chrome editing command (e.g. 'paste')."""
        g = self.g
        if self.is_chrome:
            named = {"Enter": ("Enter", "Enter", 13, "\r"), "Backspace": ("Backspace", "Backspace", 8, None),
                     "Delete": ("Delete", "Delete", 46, None)}
            k, code, vk, text = named[key] if key in named else (key, "Key" + key.upper(), ord(key.upper()), None)
            mod = 2 if ctrl else 0
            if ctrl:
                g.call("Input.dispatchKeyEvent", type="rawKeyDown", key="Control", code="ControlLeft", windowsVirtualKeyCode=17, modifiers=2)
                time.sleep(0.06)
            extra = {"commands": [cmd]} if cmd else {}
            g.call("Input.dispatchKeyEvent", type="keyDown" if text else "rawKeyDown", key=k, code=code, windowsVirtualKeyCode=vk,
                   modifiers=mod, **({"text": text} if text else {}), **extra)
            time.sleep(0.08)
            g.call("Input.dispatchKeyEvent", type="keyUp", key=k, code=code, windowsVirtualKeyCode=vk, modifiers=mod)
            if ctrl:
                time.sleep(0.06)
                g.call("Input.dispatchKeyEvent", type="keyUp", key="Control", code="ControlLeft", windowsVirtualKeyCode=17, modifiers=0)
        else:
            val = {"Enter": "", "Backspace": "", "Delete": ""}.get(key, key)
            acts = ([{"type": "keyDown", "value": ""}, {"type": "pause", "duration": 60}] if ctrl else [])
            acts += [{"type": "keyDown", "value": val}, {"type": "pause", "duration": 80}, {"type": "keyUp", "value": val}]
            acts += ([{"type": "pause", "duration": 60}, {"type": "keyUp", "value": ""}] if ctrl else [])
            g._actions([{"type": "key", "id": "kbd", "actions": acts}])
        time.sleep(0.2)

    def real_login(self):
        """Click the user field, type, click the password field, type, press Enter: what a person does."""
        g = self.g
        g.click(*self.center("username"))
        g.type_text(USER)
        g.click(*self.center("password"))
        g.type_text(PASSWORD)
        self.chord("Enter")

    def wait_state(self, cond, cap):
        return BC.wait_state(self.g, cond, cap)

    def open_and_form(self):
        url = "https://%s:%d/" % (self.a.host, PORTS[self.a.box])
        g = self.g
        g.navigate(url)
        end, f = time.time() + 30, {}
        while time.time() < end:
            f = g.js(BC.JS_FORM)
            if f.get("form") and f.get("ready") == "complete":
                return True, url
            time.sleep(0.5)
        return False, "%s: form not usable: %s" % (url, f)

    def settle_desktop(self, cap=60):
        """Shell process up (+ GNOME overview left) and the picture still: returns (ok, description)."""
        box, g = self.box, self.g
        end, up = time.time() + cap, False
        while time.time() < end and not up:
            up = box.run(BC.SHELL_UP[self.a.box] % {"u": USER})[0] == 0
            time.sleep(1.5)
        if not up:
            return False, "the desktop shell is not up %d s after login" % cap
        if self.a.box == "gnome":
            BC.leave_overview(g, box, USER)
        end, still, prev = time.time() + cap, 0, None
        while time.time() < end and still < 3:
            time.sleep(1.5)
            s = g.js(BC.JS_STATE)
            if not s["rect"] or s["rect"][2] < 4:
                continue
            png = BC.canvas_png(g, s["rect"])
            deg, _ = BC.judge_pixel(png)
            still = still + 1 if (not deg and prev and BC.settled(prev, png)) else 0
            prev = png
        return still >= 3, "shell up, picture %s" % ("still" if still >= 3 else "never settled")

    def start_test_window(self, tag):
        """The fullscreen text-entry window of test-window.py, in the user's session. Returns (ok, log path)."""
        log = "/tmp/ac-%s.log" % tag
        self.box.run("cat > /tmp/ac-test-window.py", stdin=open(os.path.join(HERE, "test-window.py")).read())
        self.box.run("rm -f %s; chmod 644 /tmp/ac-test-window.py" % log)
        c, out = self.box.in_session("python3 /tmp/ac-test-window.py %s" % log)
        if c:
            return False, out
        self.log = log
        end = time.time() + 30
        while time.time() < end:
            if any(e["ev"] == "ready" for e in self.events()):
                time.sleep(1.5)
                return True, log
            time.sleep(1)
        return False, "the test window never reported ready"

    def events(self):
        import json
        c, t = self.box.run("cat %s 2>/dev/null; true" % self.log)
        return [json.loads(x) for x in t.splitlines() if x.startswith("{")]

    def canvas_click(self, fx, fy):
        s = self.g.js(BC.JS_STATE)
        L, T, W, H = s["rect"]
        self.g.click(L + W * fx, T + H * fy)
