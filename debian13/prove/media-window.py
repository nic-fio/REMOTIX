#!/usr/bin/python3
"""Media test windows of prove/ (check-media.py): run INSIDE the box, in the user's session, fullscreen, flat rectangles at integer pixels.
    media-window.py count RATE LOG     a counter n, binary-coded (20 cells of 20x20 px, top left, bit 0 on the left, white=1) and in
                                       big digits. RATE = changes per second; 0 = one per frame (the frame clock). Every change is
                                       logged: {"ev":"n","n":..,"t":..} with t = the clock when the frame was drawn
    media-window.py bursts LOG         the same counter, 60 Hz for 1.5 s, then still for 2.5 s, 9 times; each stop is logged
                                       {"ev":"final","n":..,"t":..} (what the client must show 1 s later: not an older picture)
    media-window.py video LOG          (starts when the file LOG.go exists) a bar moving at 240 px/s, and every second k=1..10 a white flash cell (top left, 160x160) for
                                       300 ms; the beeps (1 kHz, 80 ms) are in a WAV played by pw-play, started at the same instant as
                                       the animation clock. A recorder on the default sink's monitor measures when each beep REALLY
                                       sounds in the box; {"ev":"flash","k":..,"t":..} and {"ev":"beep","k":..,"t":..} are the
                                       box's own truth to compare with what the browser sees and hears
    media-window.py pattern LOG        the sharpness pattern (stripes 1/2/4 px, edge, checker; PATTERN below), grey elsewhere
PATTERN: (name, x, y, w, h) in window pixels; check-media.py holds a copy of it."""
import json
import math
import os
import struct
import subprocess
import sys
import threading
import time
import wave

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, Gdk, GLib, Graphene  # noqa: E402


class Canvas(Gtk.Widget):
    """A widget that paints with Gtk.Snapshot only (python3-gi-cairo, needed for a cairo draw function, is not in the boxes).
    Every edge is an integer pixel and every colour a flat rectangle, so the picture is pixel-exact at scale 1."""
    __gtype_name__ = "RxProveCanvas"

    def __init__(self, draw):
        super().__init__(hexpand=True, vexpand=True)
        self.draw, self.last_size = draw, None
        self.on_size = None

    def do_snapshot(self, snap):
        w, h = self.get_width(), self.get_height()
        if self.last_size != (w, h):
            self.last_size = (w, h)
            if self.on_size:
                self.on_size(w, h)
        self.draw(Fill(snap), w, h)


def rgba(r, g, b):
    c = Gdk.RGBA()
    c.red, c.green, c.blue, c.alpha = r, g, b, 1.0
    return c


class Fill:
    def __init__(self, snap):
        self.snap = snap

    def rect(self, x, y, w, h, rgb):
        if w > 0 and h > 0:
            r = Graphene.Rect()
            r.init(x, y, w, h)
            self.snap.append_color(rgba(*rgb), r)

PATTERN = (("v1", 16, 16, 256, 128), ("v2", 16, 160, 256, 128), ("v4", 16, 304, 256, 128), ("h2", 300, 16, 256, 128),
           ("edge", 300, 160, 256, 128), ("check8", 300, 304, 256, 128), ("rb2", 600, 16, 256, 128))
BITS, CELL = 20, 20
MODE = sys.argv[1]
LOG = sys.argv[-1]
buf, lock = [], threading.Lock()


def say(**d):
    d.setdefault("t", time.time())
    with lock:
        buf.append(json.dumps(d))


def flush():
    with lock:
        out, buf[:] = buf[:], []
    if out:
        with open(LOG, "a") as f:
            f.write("\n".join(out) + "\n")
    return True


class State:
    n, last_logged = 0, -1
    t0 = None
    flash_k = None


S = State()
LABEL = []


def draw_count(f, w, h):
    f.rect(0, 0, w, h, (0.5, 0.5, 0.5))
    n = S.n
    for i in range(BITS):
        v = float((n >> i) & 1)
        f.rect(8 + i * CELL, 8, CELL, CELL, (v, v, v))
    f.rect((n * 7) % max(1, w - 60), h - 120, 60, 60, (0.9, 0.2, 0.2))  # moves with n over the whole width: frames really differ
    if n != S.last_logged:
        S.last_logged = n
        say(ev="n", n=n)


def bump(area):
    S.n += 1
    if LABEL:
        LABEL[0].set_text("%07d" % S.n)
    area.queue_draw()


def draw_video(f, w, h):
    f.rect(0, 0, w, h, (0.1, 0.1, 0.4))
    el = time.time() - S.t0 if S.t0 else -1
    k = int(el) if el >= 1 and (el - int(el)) < 0.3 and int(el) <= 10 else None
    v = 1.0 if k else 0.0
    f.rect(0, 0, 160, 160, (v, v, v))
    if k and k != S.flash_k:
        S.flash_k = k
        say(ev="flash", k=k)
    if not k:
        S.flash_k = None
    f.rect(int((max(el, 0) * 240) % max(1, w - 80)), h // 2, 80, 160, (0.95, 0.8, 0.1))


def draw_pattern(f, w, h):
    f.rect(0, 0, w, h, (0.5, 0.5, 0.5))
    for name, x, y, rw, rh in PATTERN:
        if name in ("v1", "v2", "v4"):
            s = int(name[1])
            for i in range(0, rw, 2 * s):
                f.rect(x + i, y, s, rh, (1, 1, 1))
                f.rect(x + i + s, y, s, rh, (0, 0, 0))
        elif name == "h2":
            for j in range(0, rh, 4):
                f.rect(x, y + j, rw, 2, (1, 1, 1))
                f.rect(x, y + j + 2, rw, 2, (0, 0, 0))
        elif name == "edge":
            f.rect(x, y, rw // 2, rh, (0, 0, 0))
            f.rect(x + rw // 2, y, rw // 2, rh, (1, 1, 1))
        elif name == "check8":
            for j in range(0, rh, 8):
                for i in range(0, rw, 8):
                    v = float(((i // 8) + (j // 8)) % 2)
                    f.rect(x + i, y + j, 8, 8, (v, v, v))
        elif name == "rb2":
            for i in range(0, rw, 4):
                f.rect(x + i, y, 2, rh, (1, 0, 0))
                f.rect(x + i + 2, y, 2, rh, (0, 0, 1))


def make_beeps(path):
    with wave.open(path, "wb") as wv:
        wv.setnchannels(2), wv.setsampwidth(2), wv.setframerate(48000)
        data = bytearray()
        for i in range(48000 * 12):
            t = i / 48000.0
            k = round(t)
            v = 0
            if 1 <= k <= 10 and 0 <= t - k < 0.08:
                v = int(20000 * math.sin(2 * math.pi * 1000 * t))
            data += struct.pack("<hh", v, v)
        wv.writeframes(bytes(data))


def monitor_thread():
    """Record the default sink's monitor; log when each beep begins (a chunk above the threshold, 0.5 s after the previous one)."""
    try:
        p = subprocess.Popen(["pw-record", "-P", "stream.capture.sink=true", "--rate", "48000", "--channels", "1", "--format", "s16", "-"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError as e:
        say(ev="monitor-error", err=str(e))
        return
    say(ev="monitor-started")
    k, last = 0, 0.0
    while True:  # beeps before the animation clock + 0.5 s are not the file's (a start-up click of the recorder is ignored)
        chunk = p.stdout.read(960 * 2)  # 20 ms
        if not chunk:
            break
        now = time.time()
        n = len(chunk) // 2
        peak = max(abs(v) for v in struct.unpack("<%dh" % n, chunk[:n * 2])) if n else 0
        if peak > 4000 and now - last > 0.5 and S.t0 is not None and now > S.t0 + 0.5:
            last = now
            k += 1
            say(ev="beep", k=k, t=now - n / 48000.0)


def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    area = Canvas({"count": draw_count, "bursts": draw_count, "video": draw_video, "pattern": draw_pattern}[MODE])
    if MODE in ("count", "bursts"):
        ov = Gtk.Overlay()
        ov.set_child(area)
        lab = Gtk.Label(halign=Gtk.Align.START, valign=Gtk.Align.CENTER, margin_start=40)
        css = Gtk.CssProvider()
        css.load_from_string("label { font-size: 160px; font-weight: bold; color: #ffff33; font-family: monospace; }")
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        ov.add_overlay(lab)
        LABEL.append(lab)
        win.set_child(ov)
    else:
        win.set_child(area)
    win.fullscreen()
    if MODE == "count":
        rate = float(sys.argv[2])
        if rate <= 0:
            def tick(w_, clock):
                bump(area)
                return True
            area.add_tick_callback(tick)
        else:
            def step():
                bump(area)
                return True
            GLib.timeout_add(int(1000 / rate), step)
    elif MODE == "bursts":
        st = {"phase": "run", "until": time.time() + 1.5, "cycle": 0}

        def tick(w_, clock):
            now = time.time()
            if st["phase"] == "run":
                bump(area)
                if now >= st["until"]:
                    st.update(phase="still", until=now + 2.5)
                    GLib.timeout_add(80, lambda: say(ev="final", n=S.n) or False)
            elif now >= st["until"] and st["cycle"] < 9:
                st.update(phase="run", until=now + 1.5, cycle=st["cycle"] + 1)
            return True
        area.add_tick_callback(tick)
    elif MODE == "video":
        wav = "/tmp/rx-beeps-%d.wav" % os.getpid()
        make_beeps(wav)

        def go():
            threading.Thread(target=monitor_thread, daemon=True).start()
            time.sleep(0.4)
            S.t0 = time.time()
            subprocess.Popen(["pw-play", wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            say(ev="start")
            area.add_tick_callback(lambda w_, c: (area.queue_draw(), True)[1])
            return False
        GLib.timeout_add(100, lambda: (go(), False)[1] if os.path.exists(LOG + ".go") else True)  # waits for the checker's touch of LOG.go
    win.present()
    GLib.timeout_add(1500, lambda: say(ev="ready", w=area.get_width(), h=area.get_height()) or False)
    GLib.timeout_add(500, flush)


app = Gtk.Application(application_id="org.remotix.prove.media")
app.connect("activate", on_activate)
app.run(None)
