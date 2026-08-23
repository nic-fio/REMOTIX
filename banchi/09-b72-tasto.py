#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b72-tasto — ⭐ MANDA UN TASTO NELLA SESSIONE.  Gira SULLA MACCHINA, da root.

⛔⛔ ESISTE PER UN GUASTO DEL BANCO CHE HA RETTO MEZZA GIORNATA, e va scritto
   prima del codice perche' e' la ragione del file:

   **La sessione headless di GNOME sta nella VISTA D'INSIEME** (l'Overview di
   `Attivita'`), e ci resta: nessuno ha mai premuto un tasto dentro.  ⇒ le
   finestre non sono finestre, sono **anteprime rimpicciolite** in mezzo allo
   schermo, con la barra in alto e il cassetto in basso.
   `[M]` 23 agosto 2026, 08:08, guardato nei pixel della cattura: la scena
   `--movimento pieno`, che si dichiara «a schermo intero», occupava
   **un riquadro di anteprima**, non lo schermo.
   ⇒ ⛔ **«a schermo intero» nei banchi di stamattina non era a schermo
     intero**, e ogni numero preso li' e' il numero di una frazione.

⭐ E LA PORTA PER USCIRNE E' QUELLA CHE USA IL PRODOTTO: `org.gnome.Mutter.
   RemoteDesktop`.  ⛔ Le due strade piu' comode sono chiuse, e le ho provate:
     · `org.gnome.Shell.Eval` → `(false, '')` — spento senza «unsafe mode»;
     · `org.gnome.Shell.FocusApp` → `AccessDenied: FocusApp is not allowed`.
   ⇒ resta l'input vero, cioe' esattamente il canale che il prodotto apre per
     i tasti dell'utente.  ⚠ Non e' un trucco per il banco: e' **quel che
     succede quando l'utente preme un tasto**.

Uso (da root, sulla macchina):
    python3 09-b72-tasto.py --uid 1002 --tasti 1        # 1 = ESC (evdev)
    python3 09-b72-tasto.py --uid 1002 --tasti 1,1
"""
import argparse, os, pwd, sys

os.environ.setdefault("GI_TYPELIB_PATH", "/usr/lib/x86_64-linux-gnu/girepository-1.0")
import gi
from gi.repository import Gio, GLib


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--uid", type=int, default=1002)
    p.add_argument("--tasti", default="1", help="codici evdev separati da virgola (1 = ESC)")
    p.add_argument("--pausa", type=float, default=0.12)
    a = p.parse_args()

    # ⛔ Si scende all'utente PRIMA di toccare il bus: il bus di sessione e'
    #    suo, e da root con il solo indirizzo giusto Mutter rifiuta.
    ute = pwd.getpwuid(a.uid).pw_name
    os.environ["XDG_RUNTIME_DIR"] = "/run/user/%d" % a.uid
    os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/%d/bus" % a.uid
    os.environ["HOME"] = "/home/%s" % ute
    if os.getuid() == 0:
        os.setgroups([])
        os.setgid(a.uid)
        os.setuid(a.uid)

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    rd = Gio.DBusProxy.new_sync(
        bus, Gio.DBusProxyFlags.NONE, None, "org.gnome.Mutter.RemoteDesktop",
        "/org/gnome/Mutter/RemoteDesktop", "org.gnome.Mutter.RemoteDesktop", None)
    percorso = rd.call_sync("CreateSession", None,
                            Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
    ses = Gio.DBusProxy.new_sync(
        bus, Gio.DBusProxyFlags.NONE, None, "org.gnome.Mutter.RemoteDesktop",
        percorso, "org.gnome.Mutter.RemoteDesktop.Session", None)
    ses.call_sync("Start", None, Gio.DBusCallFlags.NONE, -1, None)
    try:
        for t in [int(x) for x in a.tasti.split(",") if x.strip()]:
            for premuto in (True, False):
                ses.call_sync("NotifyKeyboardKeycode",
                              GLib.Variant("(ub)", (t, premuto)),
                              Gio.DBusCallFlags.NONE, -1, None)
                GLib.usleep(int(a.pausa * 1e6 / 2))
        print("TASTI MANDATI: %s" % a.tasti)
    finally:
        ses.call_sync("Stop", None, Gio.DBusCallFlags.NONE, -1, None)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
