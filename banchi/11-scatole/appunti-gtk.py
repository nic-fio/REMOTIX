#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
appunti-gtk — THE CLIPBOARD ARBITER THAT WORKS ON GNOME TOO
===========================================================================

    python3 appunti-gtk.py copia «text» [seconds]    puts the text and STAYS
    python3 appunti-gtk.py incolla                   prints what is there

⛔ WHY IT EXISTS — `[M]` 19-20 September 2026, phase 12.  `wl-clipboard`
   (`wl-copy`, `wl-paste`) speaks `zwlr_data_control_manager_v1`: KWin has it,
   ⛔ **Mutter does not**.  On GNOME the two commands stay HUNG until the `timeout`
   (exit 124) — they wait for a focus that a session without a screen does not give —
   and the C17 clipboard mesh could not look (outcome 3).

⭐ THE RIGHT ROAD IS THE APPLICATIONS' ONE: `wl_data_device`, that is the
   clipboard used by Firefox, the terminal and everything else.  Here we get there
   with GTK (`python3-gi`), which **is not ours** and has never heard
   of RCP: it is an external arbiter, as the bench wants.
⛔ And it needs a REAL WINDOW, presented and focused: the Wayland clipboard
   is granted to whoever has the focus, and a window that does not show itself does not have it.

⚠ It holds on GNOME **and** on KDE: where `wl-clipboard` exists you can keep
  using that, but the difference between the two desktops stops being a wall.
"""
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402


def finestra(app):
    """A real window, small and presented: without focus, no clipboard."""
    f = Gtk.ApplicationWindow(application=app, title="REMOTIX clipboard")
    f.set_default_size(160, 60)
    f.set_child(Gtk.Label(label="clipboard"))
    f.present()
    return f


def al_fuoco(f, fatto):
    """⭐⭐ WE WAIT FOR THE FOCUS, AND DO NOTHING BEFORE — 20 Sep 2026.

    ⛔ `[M]` On GNOME the clipboard is granted to whoever has the ACTIVE window, and in
       a remote session nobody clicks: the window is there and the focus is not, so
       copy and paste fail silently.  ⇒ The bench really sends the click,
       going through REMOTIX (like C4 with the key), and here we wait for it to
       arrive: `is-active` is Mutter saying «now it is you».
    ⚠ On KWin the focus reaches the only window by itself: the same line holds for
      both desktops.
    """
    if f.is_active():
        fatto()
        return
    f.connect("notify::is-active", lambda *_: f.is_active() and fatto())


def copia(testo, secondi):
    """Puts the text on the clipboard WHEN it has the focus, and STAYS alive to serve it.

    ⛔ We do not exit right away: on Wayland the selection is served by the process that
       offers it — whoever exits takes it away, and that is the defect that makes a desktop
       that no longer has anything say «copied».
    """
    def avviato(app):
        f = finestra(app)

        def adesso():
            Gdk.Display.get_default().get_clipboard().set(testo)
            print("copied WITH FOCUS: %d characters, staying alive %g s"
                  % (len(testo), secondi), flush=True)

        print("window open, waiting for focus", flush=True)
        al_fuoco(f, adesso)
        GLib.timeout_add_seconds(int(secondi), lambda: (app.quit(), False)[1])

    app = Gtk.Application(application_id="org.remotix.appunti.copia")
    app.connect("activate", avviato)
    return app.run([])


def incolla():
    """Reads the session clipboard and prints it (nothing = empty line)."""
    esito = {"testo": ""}

    def avviato(app):
        f = finestra(app)

        def letto(clip, ris):
            try:
                esito["testo"] = clip.read_text_finish(ris) or ""
            except GLib.Error as e:
                print("⛔ could not read: %s" % e.message, file=sys.stderr)
            app.quit()

        def adesso():
            Gdk.Display.get_default().get_clipboard().read_text_async(None, letto)

        print("window open, waiting for focus", file=sys.stderr, flush=True)
        al_fuoco(f, adesso)
        GLib.timeout_add_seconds(25, lambda: (app.quit(), False)[1])

    app = Gtk.Application(application_id="org.remotix.appunti.incolla")
    app.connect("activate", avviato)
    app.run([])
    print(esito["testo"], end="")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "copia":
        sys.exit(copia(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 60))
    if len(sys.argv) >= 2 and sys.argv[1] == "incolla":
        sys.exit(incolla())
    print(__doc__)
    sys.exit(2)
