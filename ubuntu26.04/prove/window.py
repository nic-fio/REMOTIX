#!/usr/bin/python3
"""Test window of prove/: runs INSIDE the box, in the user's session. Fullscreen, one big text entry.
    window.py LOGFILE [HEXCOLOUR]
Writes one JSON line per event to LOGFILE: ready (size), motion/click (position as a fraction of the window, and the window
size w,h), text (the entry content). With HEXCOLOUR (e.g. d02020) the whole window is that one colour (check-multiuser);
without, a yellow entry on blue."""
import json
import sys

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

LOG = sys.argv[1]
COL = "#" + sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None


def say(**d):
    with open(LOG, "a") as f:
        f.write(json.dumps(d) + "\n")


def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    entry = Gtk.Entry(hexpand=True, vexpand=True, halign=Gtk.Align.FILL, valign=Gtk.Align.FILL)
    css = Gtk.CssProvider()
    css.load_from_string("window { background: %s; } entry { font-size: 96px; background: %s; color: %s; }"
                         % (COL or "#1030a0", COL or "#f0e060", "#fff" if COL else "#000"))
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    win.set_child(entry)

    def where(x, y):
        return dict(fx=round(x / max(1, win.get_width()), 3), fy=round(y / max(1, win.get_height()), 3), w=win.get_width(), h=win.get_height())

    mot = Gtk.EventControllerMotion()
    mot.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    mot.connect("motion", lambda c, x, y: say(ev="motion", **where(x, y)))
    win.add_controller(mot)
    clk = Gtk.GestureClick()
    clk.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    clk.connect("pressed", lambda g, n, x, y: (GLib.idle_add(entry.set_position, -1), say(ev="click", **where(x, y))))
    win.add_controller(clk)
    entry.connect("changed", lambda e: say(ev="text", text=e.get_text()))
    win.fullscreen()
    win.present()
    entry.grab_focus()
    GLib.timeout_add(1500, lambda: say(ev="ready", w=win.get_width(), h=win.get_height()) or False)


app = Gtk.Application(application_id="org.remotix.prove")
app.connect("activate", on_activate)
app.run(None)
