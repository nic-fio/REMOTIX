#!/usr/bin/env python3
"""02-sessione-dispositivi.py — WHEN the virtual pointer is born, and who
notices.

  python3 02-sessione-dispositivi.py --traccia /run/user/1000/f21-seat.log

===========================================================================
⛔ WHY IT EXISTS — the question `PIANO.md` carries into phase 2
===========================================================================

`[M]` 10 Aug 2026, probe S7 (`web/rapporti/S-esiti-sonda.md` §8, item S.4):
in a GNOME session without physical input devices, if the client starts
**before** the virtual pointer exists it receives nothing — no wheel, no
buttons, **not even motion**.  If it starts **after**, it receives everything.
It is the ORDER that is measured; the CAUSE is `[?]`.

⇒ ⛔ The phase 2 bench must open the application AFTER, or it measures a scene
  the product will never have.

===========================================================================
⭐ AND READING MUTTER 48.7 THE RULE IS STRICTER THAN THE PLAN WRITES IT
===========================================================================

`ensure_virtual_device()` is called by the handlers of `NotifyPointerMotion*` and
`NotifyPointerButton(pressed)`, **not** by `Start()`
(`meta-remote-desktop-session.c:290-321`, `:780-800`, `:940-960` — read on
12 Aug 2026 `[R]`).

⇒ The pointer **is not born when the RemoteDesktop session starts: it is born at
  the FIRST INJECTED MOTION.**  A bench that opened the application after
  `Start()` but before the first motion would believe it had respected the order
  and would measure the wrong scene.

===========================================================================
⛔ THE BENCH DEFECT THIS FILE EXISTS NOT TO REPEAT — 12 Aug 2026
===========================================================================

The first draft did the three steps with three `gdbus call` in a row.  ⛔ It does
not work, and **it fails silently**: the session of `org.gnome.Mutter.
RemoteDesktop` is tied to the CONNECTION that created it, and `gdbus` opens a
new connection at every invocation and closes it on exit.  Measured result:

    CreateSession → '/org/gnome/Mutter/RemoteDesktop/Session/u1'   (exit 0)
    Start         → UnknownMethod: Object does not exist at path   (exit 1)

⇒ The pointer was **never** born, and the next step — «did the client started
  before receive a second announcement?» — answered NO and looked like a
  confirmation of the plan's explanation.  ⭐ It was a red on a scene that never
  happened: the most expensive form of error, because it **confirms** what was
  expected.  It was noticed only because the exit status of every `gdbus` was
  checked (`REVIEWER.md` §1 point 4).

⇒ Here the bus connection is **a single one** and stays alive for the whole
  measurement.

===========================================================================
⭐ THE POSITIVE CONTROL OF THE STEP THAT COUNTS
===========================================================================

«I injected a motion» is not «Mutter received it».  The control is
`org.gnome.Mutter.IdleMonitor.GetIdletime`, which **collapses** when an event
really arrives — the input we inject is not marked SYNTHETIC
(`STUDI.md` §gnome §7, `core/events.c:126-138`).  If the idle time does not
collapse, the motion did not arrive and **everything that follows is void**: the
outcome becomes `[?] scene never happened`, not a no.

===========================================================================
THE EXPECTATIONS, WRITTEN BEFORE THE ROUND
===========================================================================

  step 1  a live Wayland client sees  wl_seat.capabilities(0)   — no
          pointer, no keyboard.  `[M]` already seen on 12 Aug 2026
  step 2  after the first injected motion the idle time collapses below 5 s
  step 3  that SAME client receives — or does not receive — a second
          `wl_seat.capabilities` with the pointer bit:
            · it does NOT receive it ⇒ the plan's explanation holds, and the `[?]`
              becomes `[M]`
            · it receives it         ⇒ the explanation is wrong, the cause is elsewhere
                                       and must be looked for in the client, not in the compositor
  step 4  a NEW client, born after, sees capabilities with the pointer — it is the
          opposite case, and without it step 3 cannot tell «nobody told it»
          from «the tool cannot read the capabilities»

  exit 0  measured, and the earlier client receives NOTHING (plan confirmed)
  exit 1  measured, and the earlier client RECEIVES (plan to be rewritten)
  exit 2  ⛔ scene never happened: the pointer was not born, I do not judge
  exit 3  ⛔ the tool is blind: not even the new client sees the pointer
"""

import argparse
import os
import re
import subprocess
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

RD = "org.gnome.Mutter.RemoteDesktop"
IDLE = "org.gnome.Mutter.IdleMonitor"

VERDE, ROSSO, GIALLO, FINE = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def ok(t):
    print(f"    {VERDE}OK{FINE}  {t}")


def no(t):
    print(f"    {ROSSO}NO{FINE}  {t}")


def att(t):
    print(f"    {GIALLO}⚠{FINE}   {t}")


def inf(t):
    print(f"    --  {t}")


def titolo(t):
    print(f"\n\033[1m== {t}{FINE}")


def capacita(traccia):
    """The `wl_seat#N.capabilities(X)` lines seen so far in the trace.

    ⛔ Returns the LIST, not the count: two events with the same value and a
       single event are two different facts, and a count would mix them up."""
    try:
        with open(traccia) as f:
            testo = f.read()
    except OSError as err:
        raise RuntimeError(f"cannot read the trace {traccia}: {err}")
    return re.findall(r"wl_seat#\d+\.capabilities\((\d+)\)", testo)


def idletime(conn):
    r = conn.call_sync(IDLE, "/org/gnome/Mutter/IdleMonitor/Core", IDLE,
                       "GetIdletime", None, None, Gio.DBusCallFlags.NONE,
                       10000, None)
    return r.unpack()[0]


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--traccia", required=True,
                   help="the WAYLAND_DEBUG trace of the client kept alive")
    p.add_argument("--attesa-crollo", type=int, default=5000,
                   help="below how many ms the idle time must fall (expected, "
                        "written beforehand)")
    p.add_argument("--esiti", default=None)
    a = p.parse_args()
    fatti = {"traccia": a.traccia}

    titolo("The expectations, WRITTEN BEFOREHAND")
    inf("step 1: the live client sees capabilities(0) — no pointer")
    inf(f"step 2: after the first motion the idle time falls below "
        f"{a.attesa_crollo} ms")
    inf("step 3: and the SAME client receives, or does not receive, a second announcement")

    titolo("1. What the client started BEFORE has seen so far")
    try:
        prima = capacita(a.traccia)
    except RuntimeError as err:
        no(f"⛔ {err}")
        scrivi_esito(a, fatti, 3, '[?] blind tool')
        return 3
    inf(f"wl_seat.capabilities announcements so far: {prima}")
    fatti["capacita_prima"] = prima
    if not prima:
        no("⛔ ZERO announcements in the trace.  ⛔ It is not «zero capabilities»: it is «I")
        no("   read nothing».  The tool is blind, I do not judge.")
        scrivi_esito(a, fatti, 3, '[?] blind tool')
        return 3
    if prima[-1] != "0":
        att(f"⚠ the last announcement says {prima[-1]}, not 0: in this session a "
            "pointer is already there, and the scene is not the one I wanted")

    titolo("2. I make the pointer be born — ONE single connection, from start to end")
    conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    inf(f"my connection: {conn.get_unique_name()}  ⛔ and it stays alive to the end")

    r = conn.call_sync(RD, "/org/gnome/Mutter/RemoteDesktop", RD,
                       "CreateSession", None, None, Gio.DBusCallFlags.NONE,
                       15000, None)
    percorso = r.unpack()[0]
    ok(f"CreateSession → {percorso}")

    conn.call_sync(RD, percorso, RD + ".Session", "Start", None, None,
                   Gio.DBusCallFlags.NONE, 15000, None)
    ok("Start succeeded")

    # ⛔ AND HERE, and not before, the pointer is born: `ensure_virtual_device()` is
    #    inside the handler of NotifyPointerMotionRelative.
    idle_prima = idletime(conn)
    inf(f"idle time before the motion: {idle_prima} ms")
    conn.call_sync(RD, percorso, RD + ".Session", "NotifyPointerMotionRelative",
                   GLib.Variant("(dd)", (7.0, 5.0)), None,
                   Gio.DBusCallFlags.NONE, 15000, None)
    ok("NotifyPointerMotionRelative(7,5) accepted")
    time.sleep(1.0)
    idle_dopo = idletime(conn)
    inf(f"idle time after the motion:  {idle_dopo} ms")
    fatti["idle_prima_ms"] = idle_prima
    fatti["idle_dopo_ms"] = idle_dopo

    esito = 0
    if idle_dopo >= a.attesa_crollo:
        no(f"⛔ the idle time did NOT collapse ({idle_dopo} ms ≥ {a.attesa_crollo}):")
        no("   the motion did not reach Mutter, so the pointer was not")
        no("   born and the scene I wanted to measure NEVER HAPPENED.")
        no("   ⛔ I do not judge: a no on a scene that never happened is worse than nothing.")
        esito = 2
    else:
        ok(f"⭐ positive control passed: {idle_prima} → {idle_dopo} ms.  Mutter")
        ok("   really received the motion, so the pointer is there.")

    time.sleep(3.0)

    titolo("3. The same client as before: did it get a second announcement?")
    dopo = capacita(a.traccia)
    inf(f"announcements now: {dopo} (they were {prima})")
    fatti["capacita_dopo"] = dopo
    riceve = len(dopo) > len(prima)
    if esito == 2:
        att("⚠ the scene did not happen: what follows is not a verdict")
    elif riceve:
        ok(f"⭐ THE CLIENT STARTED BEFORE RECEIVES the announcement: {prima[-1]} → {dopo[-1]}")
        ok("   ⇒ the plan's explanation — «it never subscribes» — does NOT hold,")
        ok("     and the cause of S.4 must be looked for elsewhere.")
        esito = 1
    else:
        no("⛔ NOTHING new: the client started before is not told that")
        no("   there is now a pointer.  ⇒ The plan's explanation holds, and the")
        no("   `[?]` on the cause becomes `[M]`.")

    titolo("4. The opposite case: a NEW client, born AFTER the pointer")
    traccia2 = a.traccia + ".dopo"
    with open(traccia2, "w") as f:
        amb = dict(os.environ, WAYLAND_DEBUG="1", WAYLAND_DISPLAY="wayland-0")
        subprocess.run(["timeout", "25", "foot", "-e", "sleep", "6"],
                       stdout=f, stderr=subprocess.STDOUT, env=amb)
    nuovo = capacita(traccia2)
    inf(f"announcements of the new client: {nuovo}")
    fatti["capacita_client_nuovo"] = nuovo
    if not nuovo:
        no("⛔ zero announcements for the new client too: the tool does not see the")
        no("   seat, and the comparison of step 3 tells nothing apart.")
        scrivi_esito(a, fatti, 3, '[?] blind tool')
        return 3
    if nuovo[-1] == "0":
        no(f"⛔ the NEW client too sees capabilities({nuovo[-1]}): then it is not")
        no("   the order — the pointer does not appear in the Wayland seat at all.")
        no("   ⇒ The comparison of step 3 is not a comparison: I do not judge.")
        scrivi_esito(a, fatti, 3, '[?] blind tool')
        return 3
    ok(f"⭐ the new client sees capabilities({nuovo[-1]}): the pointer in the seat")
    ok("   is there, and so step 3 is comparing two real things")

    # ⛔ The RemoteDesktop session is closed here, on the connection that
    #    created it: leaving it on the graphical session would change the state
    #    for whoever measures next.
    conn.call_sync(RD, percorso, RD + ".Session", "Stop", None, None,
                   Gio.DBusCallFlags.NONE, 10000, None)
    inf("RemoteDesktop session closed")

    titolo("The verdict")
    frase = {0: "the client started BEFORE receives nothing — the plan holds",
             1: "the client started BEFORE receives — the plan must be rewritten",
             2: "[?] scene never happened",
             3: "[?] blind tool"}[esito]
    inf(frase)
    scrivi_esito(a, fatti, esito, frase)
    return esito


def scrivi_esito(a, fatti, esito, frase):
    if not a.esiti:
        return
    import json
    with open(a.esiti, "a") as f:
        f.write(json.dumps({
            "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "banco": "F2.1", "scena": "dispositivi-ordine",
            "uscita": esito, "marca": frase, **fatti,
        }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(principale())
