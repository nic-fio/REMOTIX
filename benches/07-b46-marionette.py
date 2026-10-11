#!/usr/bin/env python3
"""A minimal Marionette client — the protocol Firefox speaks by itself,
without geckodriver.  It serves ONE purpose: driving the user's REAL Firefox
(140 ESR) against the product, and extracting what the page has in hand.

⛔ It is not a bench: it is a diagnosis tool.  The verdict comes from the
   comparison between what the page PAINTS and what the wire CARRIES."""
import json, os, shutil, socket, subprocess, tempfile, time


class Marionette:
    def __init__(self, port=2828, host="127.0.0.1"):
        self.s = socket.create_connection((host, port), timeout=120)
        self.s.settimeout(180)
        self.buf = b""
        self.n = 0
        self._read()                      # the server's greeting

    # the frame is «length:json»
    def _read(self):
        while b":" not in self.buf:
            self.buf += self.s.recv(65536)
        head, rest = self.buf.split(b":", 1)
        amount = int(head)
        while len(rest) < amount:
            rest += self.s.recv(65536)
        self.buf = rest[amount:]
        return json.loads(rest[:amount])

    def call(self, command, parameters=None):
        self.n += 1
        body = json.dumps([0, self.n, command, parameters or {}]).encode()
        self.s.sendall(str(len(body)).encode() + b":" + body)
        while True:
            m = self._read()
            if isinstance(m, list) and len(m) == 4 and m[0] == 1 and m[1] == self.n:
                if m[2] is not None:
                    raise RuntimeError("%s: %s" % (command, json.dumps(m[2])[:600]))
                return m[3]

    def session(self, insecure=True):
        return self.call("WebDriver:NewSession",
                           {"capabilities": {"alwaysMatch":
                            {"acceptInsecureCerts": insecure}}})

    def navigate(self, url):
        return self.call("WebDriver:Navigate", {"url": url})

    def js(self, code, args=None):
        return self.call("WebDriver:ExecuteScript",
                           {"script": code, "args": args or []})

    def js_async(self, code, args=None, timeout=120000):
        self.call("WebDriver:SetTimeouts", {"script": timeout})
        return self.call("WebDriver:ExecuteAsyncScript",
                           {"script": code, "args": args or []})

    def measure(self, l, a):
        return self.call("WebDriver:SetWindowRect", {"width": l, "height": a})

    def screenshot(self):
        return self.call("WebDriver:TakeScreenshot", {"full": False})


def screen_in_foreground():
    """⭐ Who is in front of the screen?  Returns `(va_bene, spiegazione)`.

    ⛔ On Wayland a NEW window is not mapped if the graphical session in
       the foreground on the seat is not ours: Firefox starts, opens the
       Marionette port, and then **stops answering** — `WebDriver:NewSession` stays
       hung until the socket ceiling (180 s).

    `[M]` 23 September 2026, CHUWI laptop, two conditions compared in the
    same quarter of an hour, Firefox 140.16 ESR:
      · `nicfio`'s session in the foreground  →  NewSession in **1.39 s**;
      · ANOTHER user's session in the foreground →  **3 attempts out of 3
        timed out**, and meanwhile the same Firefox `--headless` answered in
        1.40 s and the same VISIBLE Firefox on `Xvfb :99` in **1.63 s**.
    ⇒ It is not Firefox, it is not memory: it is the screen.

    ⚠ The comparison is on the USER, not on the session number: a bench launched
      from `ssh` sits in a session without a seat, and the number would never
      match.  When in doubt we say yes, so as not to stop what was working.

    ⭐ And with the NESTED compositor the question has no object: `[M]` 23 Sep 2026,
      night, a `labwc` without a screen (`WLR_BACKENDS=headless`) on the tablet
      while the user «user» was in the foreground — four 20-minute sessions
      with Firefox and Chrome VISIBLE inside it, windows mapped and
      counters full.  ⇒ Whoever launches DECLARES it with
      `REMOTIX_NESTED_SCREEN=1` (and `WAYLAND_DISPLAY` on its socket)."""
    if os.environ.get("REMOTIX_NESTED_SCREEN") == "1" and os.environ.get("WAYLAND_DISPLAY"):
        return True, ""
    try:
        def _ask(*a):
            return subprocess.run(["loginctl"] + list(a) + ["--value"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL,
                                  timeout=5).stdout.decode().strip()
        active = _ask("show-seat", "seat0", "-p", "ActiveSession")
        if not active:
            return True, ""
        di_chi = _ask("show-session", active, "-p", "User")
        if not di_chi or di_chi == str(os.getuid()):
            return True, ""
        name = _ask("show-session", active, "-p", "Name") or di_chi
        return False, ("in the foreground is session %s of user «%s», "
                       "not yours" % (active, name))
    except Exception:                          # noqa: BLE001
        return True, ""                        # I cannot tell: I do not get in the way


def turn_on(profile_prefs=None, headless=True, port=2828, largo=1400, alto=1000,
            screen=None):
    """⭐ `screen=":99"` starts a REAL Firefox on a virtual screen.

    ⛔ It is needed because `--headless` is NOT a real browser where it matters: `[M]` 20
    August 2026, the `paste` event arrives in headless even without an editable
    element in focus, and on a browser with a screen it does NOT.  ⇒ A clipboard
    defect the user sees can only be measured here."""
    """Starts a Firefox with a new profile and Marionette open."""
    # ⭐ The bench looks at the scene BEFORE starting: a real window on the
    #   user's desktop wants that desktop in the foreground.  Better a
    #   verdict in zero seconds than three minutes of blind waiting.
    if not headless and not screen:
        ok, why = screen_in_foreground()
        if not ok:
            raise RuntimeError(
                "⛔ VISIBLE Firefox cannot start: %s.  On Wayland the "
                "window is not mapped and `WebDriver:NewSession` does not answer "
                "(ceiling 180 s).  ⇒ three roads: go back to your graphical "
                "session; or start a virtual screen (`Xvfb :99 "
                "-screen 0 1600x1200x24` and then `screen=\":99\"`); or "
                "`headless=True` where it is enough." % why)
    profile = tempfile.mkdtemp(prefix="remotix-ff-")
    prefs = {
        "browser.startup.homepage_override.mstone": "ignore",
        "datareporting.policy.firstRunURL": "",
        "browser.aboutwelcome.enabled": False,
        "browser.shell.checkDefaultBrowser": False,
        "marionette.port": port,
        # ⚠ the console log: it serves to collect the decoder
        #   faults the page does not carry to the server
        "devtools.console.stdout.content": True,
    }
    prefs.update(profile_prefs or {})
    # ⭐ `REMOTIX_FF_PREFS='{"pref": value}'`: extra preferences for the bench's
    #   Firefox, without touching the guides (e.g. `media.hardware-video-decoding.
    #   enabled` to compare hardware and software decoding, phase 16).
    #   Empty or absent: no effect.
    prefs.update(json.loads(os.environ.get("REMOTIX_FF_PREFS") or "{}"))
    with open(os.path.join(profile, "user.js"), "w") as f:
        for k, v in prefs.items():
            f.write('user_pref("%s", %s);\n' % (k, json.dumps(v)))
    # ⭐ `-remote-allow-system-access` opens the **chrome** context to Marionette:
    #   it serves whoever has to look at — or click — what Firefox draws OUTSIDE
    #   the document, for example the little «Paste» button of §9 (`07-b56`).
    #   ⚠ It is a BENCH flag: no user's Firefox starts like this.
    cmd = ["firefox", "--marionette", "--no-remote", "-remote-allow-system-access",
           "--profile", profile, "--width", str(largo), "--height", str(alto)]
    if headless:
        cmd.append("--headless")
    log = open(os.path.join(profile, "uscita.log"), "wb")
    env = dict(os.environ)
    if screen:
        env["DISPLAY"] = screen
        # ⛔ On a Wayland session, `DISPLAY` alone is not enough: Firefox
        #    would take Wayland anyway and ignore the virtual screen.
        env.pop("WAYLAND_DISPLAY", None)
        env["MOZ_ENABLE_WAYLAND"] = "0"
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
    for _ in range(120):
        try:
            m = Marionette(port)
            return p, m, profile
        except OSError:
            time.sleep(0.5)
    p.kill()
    raise RuntimeError("Marionette did not open port %d" % port)


def turn_off(p, profile):
    try:
        p.terminate()
        p.wait(15)
    except Exception:
        p.kill()
    shutil.rmtree(profile, ignore_errors=True)
