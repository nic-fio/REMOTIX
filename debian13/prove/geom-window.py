#!/usr/bin/python3
"""Geometry test windows of prove/ (check-desktop.py): run INSIDE the box, in the user's session.
    geom-window.py frame LOGFILE   fullscreen: four coloured quadrants (TL red, TR green, BL blue, BR yellow), a 6 px white frame
                                   on the very edge, a black cross; logs {ev:"size", w, h} at every size the window gets
    geom-window.py scene LOGFILE   a normal window of 1800x1000 filled cyan with an 8 px red border (the old F-018b scene);
                                   logs {ev:"size"} too
Painted with Gtk.Snapshot flat rectangles at integer pixels: what the browser shows can be compared pixel by pixel."""
import json
import sys
import time

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

MODE, LOG = sys.argv[1], sys.argv[2]


def say(**d):
    d["t"] = time.time()
    with open(LOG, "a") as f:
        f.write(json.dumps(d) + "\n")


def draw_frame(f, w, h):
    f.rect(0, 0, w // 2, h // 2, (0.82, 0.12, 0.12))
    f.rect(w // 2, 0, w - w // 2, h // 2, (0.12, 0.7, 0.12))
    f.rect(0, h // 2, w // 2, h - h // 2, (0.12, 0.12, 0.82))
    f.rect(w // 2, h // 2, w - w // 2, h - h // 2, (0.9, 0.85, 0.1))
    f.rect(w // 2 - 3, 0, 6, h, (0, 0, 0))
    f.rect(0, h // 2 - 3, w, 6, (0, 0, 0))
    for r in ((0, 0, w, 6), (0, h - 6, w, 6), (0, 0, 6, h), (w - 6, 0, 6, h)):
        f.rect(*r, (1, 1, 1))


def draw_scene(f, w, h):
    f.rect(0, 0, w, h, (0.9, 0.1, 0.1))
    f.rect(8, 8, w - 16, h - 16, (0.0, 1.0, 1.0))


def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    area = Canvas(draw_frame if MODE == "frame" else draw_scene)
    area.on_size = lambda w, h: say(ev="size", w=w, h=h)
    win.set_child(area)
    if MODE == "frame":
        win.fullscreen()
    else:
        win.set_default_size(1800, 1000)
    win.present()
    GLib.timeout_add(1500, lambda: say(ev="ready", w=area.get_width(), h=area.get_height()) or False)


app = Gtk.Application(application_id="org.remotix.prove.geom")
app.connect("activate", on_activate)
app.run(None)
