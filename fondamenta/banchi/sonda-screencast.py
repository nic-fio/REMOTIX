#!/usr/bin/env python3
"""Sonda: apre una sessione ScreenCast su Mutter e ne ricava il nodo PipeWire.

Non e' codice di REMOTIX: serve solo a dimostrare che la catena D-Bus
funziona su una sessione GNOME senza monitor, prima di scrivere il vero
modulo di cattura in Rust.

La sessione ScreenCast vive quanto la connessione al bus di chi l'ha
creata: per questo serve un processo che resti vivo, e non una sequenza
di comandi gdbus separati.
"""

import sys
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

SC = "org.gnome.Mutter.ScreenCast"
SC_PATH = "/org/gnome/Mutter/ScreenCast"

bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)


def chiama(percorso, interfaccia, metodo, parametri=None):
    return bus.call_sync(
        SC, percorso, interfaccia, metodo, parametri, None,
        Gio.DBusCallFlags.NONE, 15000, None,
    )


def introspeziona(percorso, nome):
    xml = chiama(percorso, "org.freedesktop.DBus.Introspectable", "Introspect").unpack()[0]
    dentro = False
    print(f"--- {nome} ---")
    for riga in xml.splitlines():
        if "<interface name=\"org.gnome.Mutter.ScreenCast" in riga:
            dentro = True
        if dentro:
            print(riga)
        if dentro and "</interface>" in riga:
            dentro = False
    print()


# 1. la sessione
sessione = chiama(SC_PATH, SC, "CreateSession", GLib.Variant("(a{sv})", ({},))).unpack()[0]
print(f"sessione creata: {sessione}\n")
introspeziona(sessione, "Session")

# 2. il flusso sul monitor virtuale
IF_SESSIONE = "org.gnome.Mutter.ScreenCast.Session"
connettore = sys.argv[1] if len(sys.argv) > 1 else "Meta-0"
opzioni = {"cursor-mode": GLib.Variant("u", 1)}  # 1 = cursore composto nell'immagine
try:
    flusso = chiama(
        sessione, IF_SESSIONE, "RecordMonitor",
        GLib.Variant("(sa{sv})", (connettore, opzioni)),
    ).unpack()[0]
except GLib.Error as e:
    print(f"RecordMonitor('{connettore}') fallito: {e.message}")
    sys.exit(1)

print(f"flusso creato: {flusso}\n")
introspeziona(flusso, "Stream")

# 3. il nodo PipeWire arriva con un segnale, quindi lo si aspetta PRIMA di Start
ciclo = GLib.MainLoop()


def su_segnale(_conn, _mittente, _perc, _if, segnale, parametri):
    if segnale == "PipeWireStreamAdded":
        print(f"NODO PIPEWIRE: {parametri.unpack()[0]}")
        print("la sessione resta aperta; Ctrl-C per chiudere")


bus.signal_subscribe(
    SC, "org.gnome.Mutter.ScreenCast.Stream", None, flusso, None,
    Gio.DBusSignalFlags.NONE, su_segnale,
)

chiama(sessione, IF_SESSIONE, "Start")
print("sessione avviata, attendo il nodo PipeWire...\n")

GLib.timeout_add_seconds(int(sys.argv[2]) if len(sys.argv) > 2 else 20, ciclo.quit)
ciclo.run()
