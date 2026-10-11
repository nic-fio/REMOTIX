#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
11-fake-logind.py — ⭐ a login1 and a gnome-session that say «yes», as on a
real machine (DECISIONS.md §10.49, 11 Oct 2026)

    python3 11-fake-logind.py --login1 ADDRESS
    python3 11-fake-logind.py --gnome-session ADDRESS

⛔ WHY: in the boxes logind answered «no»/«na» to CanPowerOff/CanSuspend (the
   polkit belts of §4.7 were put in, and a container is not a seat), so the
   desktops hid Power Off, Restart and Suspend BY THEMSELVES and the net was
   green with the defect inside.  On the director's tablet (the package, no
   belts — §10.36) logind answers «yes» and the three entries were THERE.
⇒ This fake answers like the tablet:
   · `--login1 ADDRESS`: owns `org.freedesktop.login1` on that (private) system
     bus — every Can* says «yes»;
   · `--gnome-session ADDRESS`: owns `org.gnome.SessionManager` on that session
     bus, and `CanShutdown` is computed AS gnome-session 48 does (`[R]`
     gsm-manager.c:2713-2717, gsm-systemd.c): true if logind, asked on the
     system bus of ITS environment (`DBUS_SYSTEM_BUS_ADDRESS`), says «yes» or
     «challenge» to CanPowerOff, CanReboot, CanSuspend or CanHibernate.  ⭐ So
     the fake gnome-session goes through the product's filter exactly as the real
     one would, when the bench starts it through it.
⛔ And it REFUSES the acts: PowerOff, Reboot, Suspend… answer an error and
   nothing happens (it has no power to do anything anyway: it is a user
   process on a private bus).  Every call is printed, «fake: <iface>.<method>»:
   that is how the bench knows whether an act REACHED logind.
⚠ Only for the private buses of a bench: it never owns a name on the
  machine's real system bus (it is not allowed to, and must not).
"""
import argparse
import sys

from gi.repository import Gio, GLib

CAN = ["CanPowerOff", "CanReboot", "CanHalt", "CanSuspend", "CanHibernate", "CanHybridSleep",
       "CanSuspendThenHibernate", "CanSleep", "CanRebootToFirmwareSetup",
       "CanRebootToBootLoaderMenu"]
ACTS = ["PowerOff", "Reboot", "Halt", "Suspend", "Hibernate", "HybridSleep",
        "SuspendThenHibernate"]
LOGIN1 = ('<node><interface name="org.freedesktop.login1.Manager">' +
          "".join(f'<method name="{m}"><arg type="s" direction="out"/></method>' for m in CAN) +
          "".join(f'<method name="{m}"><arg type="b" direction="in"/></method>' for m in ACTS) +
          "".join(f'<method name="{m}WithFlags"><arg type="t" direction="in"/></method>'
                  for m in ACTS) +
          "</interface></node>")
SESSION = """
<node><interface name="org.gnome.SessionManager">
  <method name="CanShutdown"><arg type="b" direction="out"/></method>
  <method name="CanRebootToFirmwareSetup"><arg type="b" direction="out"/></method>
  <method name="Shutdown"/>
  <method name="Reboot"/>
</interface></node>"""


def login1_says(method):
    """What logind answers to the gnome-session that asks — through ITS system bus."""
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        r = bus.call_sync("org.freedesktop.login1", "/org/freedesktop/login1",
                          "org.freedesktop.login1.Manager", method, None,
                          GLib.VariantType("(s)"), 0, 5000, None)
        return r.unpack()[0]
    except GLib.Error as e:
        print(f"fake: gnome-session asked login1.{method}: error {e.message}", flush=True)
        return "na"


def answer(conn, sender, path, iface, method, params, inv):
    print(f"fake: {iface}.{method}", flush=True)
    if iface == "org.gnome.SessionManager":
        if method == "CanShutdown":
            says = {m: login1_says(m) for m in
                    ("CanPowerOff", "CanReboot", "CanSuspend", "CanHibernate")}
            print(f"fake: gnome-session heard from login1 {says}", flush=True)
            inv.return_value(GLib.Variant("(b)", (any(v in ("yes", "challenge")
                                                      for v in says.values()),)))
        elif method.startswith("Can"):
            inv.return_value(GLib.Variant("(b)", (False,)))
        else:
            inv.return_dbus_error("org.freedesktop.DBus.Error.AccessDenied",
                                  "REMOTIX bench: the fake does not power anything off")
    elif method.startswith("Can"):
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
    a.add_argument("--login1", metavar="SYSTEM_BUS_ADDRESS")
    a.add_argument("--gnome-session", metavar="SESSION_BUS_ADDRESS")
    o = a.parse_args()
    if not o.login1 and not o.gnome_session:
        a.error("--login1 and/or --gnome-session")
    keep = []
    if o.login1:
        keep.append(serve(o.login1, "org.freedesktop.login1", "/org/freedesktop/login1",
                          LOGIN1))
    if o.gnome_session:
        keep.append(serve(o.gnome_session, "org.gnome.SessionManager",
                          "/org/gnome/SessionManager", SESSION))
    print("fake: ready", flush=True)
    loop = GLib.MainLoop()
    # ⛔ it dies with the bench's buses: never a fake left behind
    for conn in keep:
        conn.connect("closed", lambda *_: loop.quit())
    loop.run()
    del keep


if __name__ == "__main__":
    main()
