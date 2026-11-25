#!/usr/bin/python3
"""Input test window of prove/ (check-input.py, check-phone.py): runs INSIDE the box, in the user's session. Does NOT replace
window.py (which the other checks use unchanged).
    window-input.py LOGFILE MODE [HEXCOLOUR]
MODE  input  fullscreen. Top: one big text entry (the text cursor must show there). Below: a plain coloured area (the arrow).
      edge   a normal 640x440 window (cyan, with decoration from the desktop), one small entry: its edges can be grabbed.
One JSON line per event, appended to LOGFILE:
  ready   w,h                                   the window is up
  motion  fx,fy,w,h                             pointer position as a fraction of the window, and the window size (via=enter: the pointer came in)
  leave                                         the pointer left the window
  press   button(1 left,2 middle,3 right), n (1 single, 2 double...), fx,fy,w,h
  release button, fx,fy,w,h                     taken from the raw GDK event (see below), so n is not given
  scroll  dx,dy (GTK: up is negative, down positive), fx,fy
  key     name,code(hardware),char,mods(list),down(true/false)     every key the application receives, captured before the entry
  text    text                                  the entry content
  sel     start,end,text                        the selection of the entry
  active  yes(bool)                             the window got / lost focus
  size    w,h                                   the window size changed (also the first size)"""
import json
import sys
import time

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

LOG, MODE = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "input"
COL = "#" + sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None


def say(**d):
    d["t"] = round(time.time(), 3)
    with open(LOG, "a") as f:
        f.write(json.dumps(d) + "\n")


def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    entry = Gtk.Entry(hexpand=True, halign=Gtk.Align.FILL)
    area = Gtk.Label(label="", hexpand=True, vexpand=True)
    if MODE == "edge":
        bg, area_bg, size = COL or "#00e0e0", COL or "#00e0e0", 28
    else:
        bg, area_bg, size = COL or "#1030a0", COL or "#2a8a2a", 96
    css = Gtk.CssProvider()
    css.load_from_string("window { background: %s; } entry { font-size: %dpx; background: #f0e060; color: #000; }"
                         " label { background: %s; }" % (bg, size, area_bg))
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    if MODE == "edge":
        entry.set_margin_top(20)
        entry.set_margin_start(20)
        entry.set_margin_end(20)
        box.append(entry)
        box.append(area)
        win.set_default_size(640, 440)
    else:
        entry.set_size_request(-1, 170)
        box.append(entry)
        box.append(area)
    win.set_child(box)

    def where(x, y):
        return dict(fx=round(x / max(1, win.get_width()), 4), fy=round(y / max(1, win.get_height()), 4), w=win.get_width(), h=win.get_height())

    mot = Gtk.EventControllerMotion()
    mot.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    mot.connect("motion", lambda c, x, y: say(ev="motion", **where(x, y)))
    mot.connect("enter", lambda c, x, y: say(ev="motion", via="enter", **where(x, y)))
    mot.connect("leave", lambda c: say(ev="leave"))
    win.add_controller(mot)

    clk = Gtk.GestureClick()
    clk.set_button(0)  # every button
    clk.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    clk.connect("pressed", lambda g, n, x, y: say(ev="press", button=g.get_current_button(), n=n, **where(x, y)))
    win.add_controller(clk)

    # The release is NOT taken from the gesture: with GTK 4.22 the entry claims the sequence (text selection by dragging) and the
    # claim denies this capture gesture on the window, which then never emits "released" (GTK 4.18 did not deny ancestors). A legacy
    # controller sees every raw button event, whoever claims the sequence, so a release that really reached the client is always logged.
    def raw_release(c, _ev):
        e = c.get_current_event()
        if e is None or e.get_event_type() != Gdk.EventType.BUTTON_RELEASE:
            return False
        ok, sx, sy = e.get_position()
        if not ok:
            return False
        tx, ty = win.get_surface_transform()  # the event is in surface coordinates, `where` wants window ones
        say(ev="release", button=e.get_button(), **where(sx - tx, sy - ty))
        return False
    raw = Gtk.EventControllerLegacy()
    raw.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    raw.connect("event", raw_release)
    win.add_controller(raw)

    sc = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
    sc.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    sc.connect("scroll", lambda c, dx, dy: (say(ev="scroll", dx=round(dx, 3), dy=round(dy, 3)), False)[1])
    win.add_controller(sc)

    def mods(state):
        m = []
        for name, mask in (("shift", Gdk.ModifierType.SHIFT_MASK), ("ctrl", Gdk.ModifierType.CONTROL_MASK), ("alt", Gdk.ModifierType.ALT_MASK),
                           ("super", Gdk.ModifierType.SUPER_MASK), ("caps", Gdk.ModifierType.LOCK_MASK)):
            if state & mask:
                m.append(name)
        return m

    def key(down):
        def f(c, keyval, keycode, state):
            u = Gdk.keyval_to_unicode(keyval)
            say(ev="key", name=Gdk.keyval_name(keyval), code=keycode, char=chr(u) if u > 31 else "", mods=mods(state), down=down)
            return False
        return f

    kc = Gtk.EventControllerKey()
    kc.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    kc.connect("key-pressed", key(True))
    kc.connect("key-released", lambda c, kv, kcode, st: key(False)(c, kv, kcode, st))
    win.add_controller(kc)

    entry.connect("changed", lambda e: say(ev="text", text=e.get_text()))

    lastsel = [None]

    def sel(*_):
        r = entry.get_selection_bounds()
        ok, st, en = (bool(r[0]), r[1], r[2]) if len(r) == 3 else ((True, r[0], r[1]) if len(r) == 2 else (False, entry.get_position(), entry.get_position()))
        cur = (st if ok else entry.get_position(), en if ok else entry.get_position())
        if cur != lastsel[0]:
            lastsel[0] = cur
            say(ev="sel", start=cur[0], end=cur[1], text=entry.get_text()[cur[0]:cur[1]] if ok else "")
        return True
    GLib.timeout_add(80, sel)
    win.connect("notify::is-active", lambda w, p: say(ev="active", yes=bool(w.is_active())))

    if MODE != "edge":
        win.fullscreen()
    last = [0, 0]

    def poll():
        s = (win.get_width(), win.get_height())
        if s != tuple(last) and s[0] > 0:
            last[:] = s
            say(ev="size", w=s[0], h=s[1])
        return True
    GLib.timeout_add(250, poll)
    win.present()
    entry.grab_focus()
    GLib.timeout_add(1500, lambda: say(ev="ready", w=win.get_width(), h=win.get_height()) or False)


app = Gtk.Application(application_id="org.remotix.proveinput%s" % ((COL or "").strip("#") or "x"))
app.connect("activate", on_activate)
app.run(None)
