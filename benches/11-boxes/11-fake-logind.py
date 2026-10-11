#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
11-fake-logind.py — ⭐ a login1 and a gnome-session that say «yes», as on a
real machine (DECISIONS.md §10.49, 11 Oct 2026)

    python3 11-fake-logind.py --system-bus ADDRESS --session-bus ADDRESS

⛔ WHY: in the boxes logind answered «no»/«na» to CanPowerOff/CanSuspend (the
   polkit belts of §4.7 were put in, and a container is not a seat), so the
   desktops hid Power Off, Restart and Suspend BY THEMSELVES and the net was
   green with the defect inside.  On the director's tablet (the package, no
   belts — §10.36) logind answers «yes» and the three entries were THERE.
⇒ This fake answers like the tablet:
   · on the SYSTEM bus given, `org.freedesktop.login1` — CanPowerOff, CanReboot,
     CanSuspend, CanHibernate, CanHybridSleep, CanSuspendThenHibernate = «yes»;
   · on the SESSION bus given, `org.gnome.SessionManager` — CanShutdown = true.
⛔ And it REFUSES the acts: PowerOff, Reboot, Suspend… answer an error and
   nothing happens (it has no power to do anything anyway: it is a user
   process on a private bus).
⚠ Only for the private buses of a bench: it never owns a name on the
  machine's real system bus (it is not allowed to, and must not).
"""
import argparse
import sys

from gi.repository import Gio, GLib

LOGIN1 = """
<node><interface name="org.freedesktop.login1.Manager">
  <method name="CanPowerOff"><arg type="s" direction="out"/></method>
  <method name="CanReboot"><arg type="s" direction="out"/></method>
  <method name="CanSuspend"><arg type="s" direction="out"/></method>
  <method name="CanHibernate"><arg type="s" direction="out"/></method>
  <method name="CanHybridSleep"><arg type="s" direction="out"/></method>
  <method name="CanSuspendThenHibernate"><arg type="s" direction="out"/></method>
  <method name="PowerOff"><arg type="b" direction="in"/></method>
  <method name="Reboot"><arg type="b" direction="in"/></method>
  <method name="Suspend"><arg type="b" direction="in"/></method>
  <method name="Hibernate"><arg type="b" direction="in"/></method>
</interface></node>"""
SESSION = """
<node><interface name="org.gnome.SessionManager">
  <method name="CanShutdown"><arg type="b" direction="out"/></method>
  <method name="Shutdown"/>
  <method name="Reboot"/>
</interface></node>"""

asked = {}


def answer(conn, sender, path, iface, method, params, inv):
    asked[method] = asked.get(method, 0) + 1
    print(f"fake: {iface}.{method}", flush=True)
    if method.startswith("Can"):
        if iface == "org.gnome.SessionManager":
            inv.return_value(GLib.Variant("(b)", (True,)))
        else:
            inv.return_value(GLib.Variant("(s)", ("yes",)))
    else:
        inv.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied",
                              "REMOTIX bench: the fake does not power anything off")


def serve(address, name, path, xml):
    conn = Gio.DBusConnection.new_for_address_sync(
        address, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
        Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
    for iface in Gio.DBusNodeInfo.new_for_xml(xml).interfaces:
        conn.register_object(path, iface, answer, None, None)
    reply = conn.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus",
                           "org.freedesktop.DBus", "RequestName",
                           GLib.Variant("(su)", (name, 4)), None, 0, -1, None)
    if reply.unpack()[0] != 1:
        sys.exit(f"fake: {name} NOT owned on {address}")
    return conn


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--system-bus", required=True)
    a.add_argument("--session-bus", required=True)
    o = a.parse_args()
    keep = [serve(o.system_bus, "org.freedesktop.login1", "/org/freedesktop/login1", LOGIN1),
            serve(o.session_bus, "org.gnome.SessionManager", "/org/gnome/SessionManager",
                  SESSION)]
    print("fake: ready", flush=True)
    loop = GLib.MainLoop()
    # ⛔ it dies with the bench's buses: never a fake left behind
    for conn in keep:
        conn.connect("closed", lambda *_: loop.quit())
    loop.run()
    del keep


if __name__ == "__main__":
    main()
