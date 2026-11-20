#!/usr/bin/python3
"""Test window for prove/check-lifecycle.py (base-check's, plus the window size w,h in every motion/click event): runs INSIDE the box, in the user's session.
Fullscreen, one big text entry. Writes one JSON line per event to the log file given as argv[1]:
ready (size), motion/click (position as a fraction of the window), text (the entry content)."""
import json
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

LOG = sys.argv[1]


def say(**d):
    with open(LOG, "a") as f:
        f.write(json.dumps(d) + "\n")


def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    entry = Gtk.Entry(hexpand=True, vexpand=True, halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)
    css = Gtk.CssProvider()
    css.load_from_string("window { background: #1030a0; } entry { font-size: 96px; background: #f0e060; color: #000; }")
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    win.set_child(entry)

    def frac(x, y):
        return round(x / max(1, win.get_width()), 3), round(y / max(1, win.get_height()), 3)

    mot = Gtk.EventControllerMotion()
    mot.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    mot.connect("motion", lambda c, x, y: say(ev="motion", fx=frac(x, y)[0], fy=frac(x, y)[1], w=win.get_width(), h=win.get_height()))
    win.add_controller(mot)
    clk = Gtk.GestureClick()
    clk.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    clk.connect("pressed", lambda g, n, x, y: GLib.idle_add(entry.set_position, -1) and None or say(ev="click", fx=frac(x, y)[0], fy=frac(x, y)[1], w=win.get_width(), h=win.get_height()))
    win.add_controller(clk)
    entry.connect("changed", lambda e: say(ev="text", text=e.get_text()))
    win.fullscreen()
    win.present()
    entry.grab_focus()
    GLib.timeout_add(1500, lambda: say(ev="ready", w=win.get_width(), h=win.get_height()) or False)


app = Gtk.Application(application_id="org.remotix.lifecycle")
app.connect("activate", on_activate)
app.run(None)
