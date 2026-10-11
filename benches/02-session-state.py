#!/usr/bin/env python3
"""02-session-state.py — the F2.1 tool: it says which state the graphical
session is in, and says it with a different exit code for each state.

  python3 02-session-state.py --wait 1920x1080 --from-bus
  python3 02-session-state.py --wait 1920x1080 --from-scene scene/black.json
  python3 02-session-state.py --wait 1920x1080 --from-bus --record scene/x.json

===========================================================================
⛔ WHY IT EXISTS — the defect this tool prevents
===========================================================================

A headless GNOME session without `--virtual-monitor` starts **alive, complete and
black** (`STUDIES.md` §gnome §3.1: in headless `needs_outputs=false`).  Alive means
really alive: `IsSessionRunning` answers `true`, the bus has fifty names,
Nautilus and the Terminal are there.  Only one thing is missing — a monitor — and
since it is missing silently, whoever measures CAPTURE on that session reads zero
frames and goes looking for the defect inside PipeWire.  `PLAN.md` phase 2: *«you
search for half a day on the wrong side»*.

⭐ It is not a fear: on 12 Aug 2026, opening this round, the GNOME session alive
   on NIC-OS for two days was **exactly that one** — `GetCurrentState`
   answered with zero monitors and zero logical monitors.  `[M]`

===========================================================================
⛔ THE FOUR QUESTIONS, EACH WITH ITS OPPOSITE CASE
===========================================================================

| the question                        | the opposite case, written beforehand   |
|-------------------------------------|-----------------------------------------|
| is the session alive?               | the process is there but the bus is mute|
| does it have the monitor of the     | it has one it chose by itself (E2)      |
| REQUESTED size?                     |                                         |
| is it alive and black?              | it has a monitor, so it is not black    |
| is SHELL empty?                     | gnome-session restarted inside a shell  |

===========================================================================
⛔ THE EXIT CODES, WRITTEN BEFORE THE ROUND (`PLAN.md` §0.3 point 4)
===========================================================================

  0  HEALTHY                    a single monitor, product «MetaVirtualMonitor»,
                                of the requested size, and the command line asks for it
  1  BLACK: ZERO MONITORS       alive, and zero monitors: it is the M9 fault
  2  WRONG SIZE                 one monitor, but not of the requested size
  3  MONITOR CHOSEN BY ITSELF   product «Virtual remote monitor» (created by Mutter
                                for a ScreenCast), or more than one          ← E2
  4  SESSION DEAD               no gnome-shell, or the bus does not answer
  5  UNKNOWN READING            I could not read: denied, or unreadable      ← E8
  6  DISAGREEMENT               the command line and the bus do not say the same ← E1
  7  SHELL NOT EMPTY            gnome-session re-executed itself inside a login shell

⛔ The precedence, declared because two states can hold at once:

       5 > 4 > 7 > 3 > 2 > 1 > 6 > 0

   · «I could not read» (5) beats everything: if the tool is blind it has no
     right to give a verdict on the subject;
   · ⛔ **DISAGREEMENT (6) sits at the bottom, and it is a paid-for correction**.  In
     the first draft it sat high, right under 7 — and on 12 Aug 2026 the
     certification on the scenes showed that this way **two verdicts out of eight
     could never be reached**: a wrong size (2) and a monitor that Mutter chose
     by itself (3) *also* make the command line disagree with the bus, so both
     came out as 6.  ⇒ Disagreement is the **residual** verdict: it is given only
     when no more precise explanation holds.  Had the certification not found
     it, the E2 form — the monitor chosen by itself, which is exactly what this
     bench exists to see — would have been invisible under a generic label.

===========================================================================
⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS  (`REVIEWER.md` §1 point 4)
===========================================================================

No `2>/dev/null` and no `gdbus | grep`.  D-Bus is called from `Gio` and the
TYPED data are taken: «the answer is an empty list» and «the call failed»
arrive by two different roads and end up in two different codes
(1 and 5).  ⛔ On 12 Aug 2026 the difference paid off at once: on the same
session `org.gnome.Shell.Introspect.GetWindows` and `Shell.Screenshot` answer
**AccessDenied** to an arbitrary caller `[M]` — a bench that had read
«zero windows» would have written «empty session» where the real fact was «they
did not let me look».

===========================================================================
⛔ AND THE COMMAND LINE IS NOT ENOUGH, NOR IS THE BUS ALONE
===========================================================================

That the option is WRITTEN does not mean it is IN FORCE (E1: necessary taken for
sufficient).  So both are read — `/proc/<pid>/cmdline` and
`GetCurrentState` — and **disagreement is a verdict of its own** (6), not a
rounding toward one or the other.

===========================================================================
⭐ THE POSITIVE CONTROL, AT THE END OF EVERY RUN
===========================================================================

Two, and they serve two different purposes:

  1. **the parser can read**: the answer of `GetCurrentState` must contain
     the property `layout-mode`, which is ALWAYS there (`meta-monitor-manager.c`).
     If it is missing, the parser is broken, not the session — and the tool says
     so instead of printing «zero monitors»;
  2. **the line to the compositor is alive now**: `IdleMonitor.GetIdletime`
     called twice some time apart must give two DIFFERENT, growing numbers.
     A tool reading a frozen answer would give the same number.

⛔ If a positive control fails, the exit becomes 5 whatever the verdict said:
   it is the rule «a tool that has never found anything is not clean, it is
   uncertified» applied to itself.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

# The product Mutter gives the persistent monitor requested with
# `--virtual-monitor` (`meta-context-main.c:592-597`, read on 12 Aug 2026 [R]).
REQUESTED_PRODUCT = "MetaVirtualMonitor"
# And the one it sets by itself when a virtual ScreenCast wants one
# (`meta-screen-cast-virtual-stream-src.c:606-609` [R]).  They are TWO different
# strings, and it is the only thing that tells «mine» from «its own»: the size
# does not, because it can coincide.
SELF_CHOSEN_PRODUCT = "Virtual remote monitor"

MARKS = {
    0: "HEALTHY",
    1: "BLACK: ZERO MONITORS",
    2: "WRONG SIZE",
    3: "MONITOR CHOSEN BY ITSELF",
    4: "SESSION DEAD",
    5: "UNKNOWN READING",
    6: "DISAGREEMENT",
    7: "SHELL NOT EMPTY",
}
# From strongest to weakest.  ⛔ The 6 sits at the bottom on purpose: see the header.
PRECEDENCE = [5, 4, 7, 3, 2, 1, 6, 0]

GREEN = "\033[1;32m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
FINE = "\033[0m"


def ok(t):
    print(f"    {GREEN}OK{FINE}  {t}")


def no(t):
    print(f"    {RED}NO{FINE}  {t}")


def inf(t):
    print(f"    --  {t}")


def expect(t):
    print(f"    {YELLOW}⚠{FINE}   {t}")


def title(t):
    print(f"\n\033[1m== {t}{FINE}")


# ---------------------------------------------------------------------------
# Gathering the facts.  Every fact has three possible outcomes — it is there,
# it is not there, I could not read it — and the third is not mistaken for the second.
# ---------------------------------------------------------------------------
class Unknown(Exception):
    """I could not read.  ⛔ It is not «it is not there»."""


def shell_processes():
    """The pids of gnome-shell.  ⛔ `pgrep -x`: `comm` is truncated to 15 characters
    (`PHASES.md` §00-ambiente B3.1), and «gnome-shell» has 11 — it fits.  But the
    exit status is checked: 0 found, 1 none, 2+ ERROR."""
    e = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "gnome-shell"],
                       capture_output=True, text=True)
    if e.returncode == 0:
        return [int(r) for r in e.stdout.split()]
    if e.returncode == 1:
        return []
    raise Unknown(f"pgrep exited with {e.returncode}: {e.stderr.strip()!r}")


def command_line(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return [a.decode("utf-8", "replace")
                    for a in f.read().split(b"\0") if a]
    except OSError as err:
        raise Unknown(f"cannot read /proc/{pid}/cmdline: {err}")


def environment_of(pid):
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            raw = f.read()
    except OSError as err:
        raise Unknown(f"cannot read /proc/{pid}/environ: {err}")
    env = {}
    for entry in raw.split(b"\0"):
        if b"=" in entry:
            k, _, v = entry.partition(b"=")
            env[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
    return env


def pid_gnome_session():
    e = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f",
                        "gnome-session-binary"], capture_output=True, text=True)
    if e.returncode == 0:
        return int(e.stdout.split()[0])
    if e.returncode == 1:
        return None
    raise Unknown(f"pgrep gnome-session-binary exited with {e.returncode}")


def bus():
    try:
        return Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except GLib.Error as err:
        raise Unknown(f"cannot connect to the session bus: {err.message}")


def call(conn, dest, path, iface, method, args=None, cap=15000):
    """Returns (value, None) or (None, error message).

    ⛔ The error is NOT lost and does NOT become an empty value: the caller decides
       whether it is «it is not there» or «I could not look», and the two cases end
       up in two different exit codes."""
    try:
        r = conn.call_sync(dest, path, iface, method, args, None,
                           Gio.DBusCallFlags.NONE, cap, None)
        return r, None
    except GLib.Error as err:
        return None, err.message


def read_monitor(conn):
    """The monitors according to `org.gnome.Mutter.DisplayConfig.GetCurrentState`.

    The signature of the answer is
      (u serial, a((ssss) a(siiddada{sv}) a{sv}) monitors,
                 a(iiduba(ssss)a{sv}) logical, a{sv} props)
    where `(ssss)` is (connector, vendor, product, serial)
    and every mode is (id, width, height, refresh, preferred-scale,
                       supported-scales, properties) — and the mode IN USE carries
    `is-current` among its properties."""
    r, error = call(conn, "org.gnome.Mutter.DisplayConfig",
                       "/org/gnome/Mutter/DisplayConfig",
                       "org.gnome.Mutter.DisplayConfig", "GetCurrentState")
    if error is not None:
        raise Unknown(f"GetCurrentState: {error}")
    serial, monitors, logical, props = r.unpack()
    listing = []
    for (connector, vendor, product, serial), modes, mprops in monitors:
        current = None
        for m in modes:
            mid, wid, h, refresh, scale_factor, scale, mp = m
            if mp.get("is-current"):
                current = {"id": mid, "width": wid, "height": h,
                            "refresh": round(refresh, 3)}
        listing.append({"connector": connector, "vendor": vendor,
                       "product": product, "serial": serial,
                       "current_mode": current, "modes": len(modes)})
    return {"serial": serial, "monitor": listing, "logical": len(logical),
            "properties": {k: str(v) for k, v in props.items()}}


# ---------------------------------------------------------------------------
def collect_from_bus():
    """Builds the SCENE: all the raw facts, without judging them.

    ⭐ Separating gathering from judging is not elegance: it is the only thing that
       lets the judgement be certified on RECORDED scenes, without having to
       break a real machine for every opposite case."""
    scene = {"when": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "machine": os.uname().nodename, "unknown": []}

    try:
        pids = shell_processes()
        scene["shell_pid"] = pids
        scene["shell_line"] = command_line(pids[0]) if pids else None
    except Unknown as e:
        scene["shell_pid"] = None
        scene["shell_line"] = None
        scene["unknown"].append(str(e))

    try:
        p = pid_gnome_session()
        scene["gnome_session_pid"] = p
        if p:
            env = environment_of(p)
            # ⛔ The trap of `STUDIES.md` §gnome §3.1: `gnome-session.in:3-14`
            #    re-executes itself inside a LOGIN shell if `$SHELL` is in
            #    /etc/shells.  The real check is `[ -n "$SHELL" ]`, so
            #    ABSENT and EMPTY are both fine: they are recorded separately
            #    so as not to suggest they are the same thing.
            scene["shell_var"] = env.get("SHELL", None)
            scene["shell_var_present"] = "SHELL" in env
            scene["xdg_session_type"] = env.get("XDG_SESSION_TYPE")
        else:
            scene["shell_var"] = None
            scene["shell_var_present"] = None
            scene["xdg_session_type"] = None
    except Unknown as e:
        scene["gnome_session_pid"] = None
        scene["shell_var_present"] = None
        scene["unknown"].append(str(e))

    try:
        conn = bus()
    except Unknown as e:
        scene["unknown"].append(str(e))
        scene["session_running"] = None
        scene["display"] = None
        scene["positive_control"] = {"outcome": False, "why": str(e)}
        return scene

    r, error = call(conn, "org.gnome.SessionManager", "/org/gnome/SessionManager",
                       "org.gnome.SessionManager", "IsSessionRunning")
    # ⛔ `ServiceUnknown` = the session is not there (a fact about the subject);
    #    any other error = I could not look (a fact about the tool).
    if error is None:
        scene["session_running"] = bool(r.unpack()[0])
        scene["session_error"] = None
    elif "ServiceUnknown" in error or "was not provided by any" in error:
        scene["session_running"] = False
        scene["session_error"] = error
    else:
        scene["session_running"] = None
        scene["session_error"] = error
        scene["unknown"].append(f"IsSessionRunning: {error}")

    try:
        scene["display"] = read_monitor(conn)
    except Unknown as e:
        scene["display"] = None
        scene["unknown"].append(str(e))

    scene["positive_control"] = positive_control(conn, scene)
    return scene


def positive_control(conn, scene):
    """⭐ «Can this tool find something that is surely there?»"""
    outcome = {"layout_mode": None, "idletime_1": None, "idletime_2": None,
             "outcome": False, "why": ""}

    d = scene.get("display")
    if d is not None:
        outcome["layout_mode"] = d["properties"].get("layout-mode")

    for key in ("idletime_1", "idletime_2"):
        r, error = call(conn, "org.gnome.Mutter.IdleMonitor",
                           "/org/gnome/Mutter/IdleMonitor/Core",
                           "org.gnome.Mutter.IdleMonitor", "GetIdletime")
        outcome[key] = r.unpack()[0] if error is None else None
        if error is not None:
            outcome["why"] = f"GetIdletime: {error}"
            return outcome
        time.sleep(0.35)

    if outcome["layout_mode"] is None:
        outcome["why"] = ("the answer of GetCurrentState has no «layout-mode», "
                           "which is always there: the parser is broken, not the session")
        return outcome
    if outcome["idletime_2"] is None or outcome["idletime_1"] is None:
        outcome["why"] = "IdleMonitor did not answer"
        return outcome
    if outcome["idletime_2"] <= outcome["idletime_1"]:
        outcome["why"] = (f"the idle time does not grow ({outcome['idletime_1']} → "
                           f"{outcome['idletime_2']}): I am reading a frozen answer")
        return outcome
    outcome["outcome"] = True
    return outcome


# ---------------------------------------------------------------------------
# The judgement: from the scene to the number.  No reading in here — so it can
# run on a recorded scene, and that is what makes the tool certifiable
# without breaking a real machine for every opposite case.
# ---------------------------------------------------------------------------
def judge(scene, want_w, want_h):
    states = set()
    said = []

    def says(t):
        said.append(t)

    if scene.get("unknown"):
        states.add(5)
        for i in scene["unknown"]:
            says(f"⛔ UNKNOWN: {i}")
    cp = scene.get("positive_control") or {}
    if not cp.get("outcome"):
        states.add(5)
        says(f"⛔ the positive control did NOT pass: {cp.get('why', 'unknown')}")

    pids = scene.get("shell_pid")
    if not pids:
        states.add(4)
        says("no gnome-shell process")
    if scene.get("session_running") is False:
        states.add(4)
        says("IsSessionRunning answers no (or the name is not on the bus)")

    # ⛔ SHELL, and the two right ways of having it: absent or empty.
    if scene.get("gnome_session_pid"):
        if scene.get("shell_var_present") and scene.get("shell_var"):
            states.add(7)
            says(f"⛔ SHELL={scene['shell_var']!r} in the environment of gnome-session: "
                 "it re-executed itself inside a login shell (STUDIES.md §gnome §3.1)")
        else:
            says("SHELL " + ("empty" if scene.get("shell_var_present") else "absent")
                 + " in the environment of gnome-session: the §3.1 trap did not bite")

    # What the COMMAND LINE asks for.
    line = scene.get("shell_line") or []
    requested = None
    requested_headless = "--headless" in line
    for i, a in enumerate(line):
        m = re.match(r"^--virtual-monitor=(.+)$", a)
        if m:
            requested = m.group(1)
        elif a == "--virtual-monitor" and i + 1 < len(line):
            requested = line[i + 1]
    requested_wh = None
    if requested:
        m = re.match(r"^(\d+)x(\d+)", requested)
        if m:
            requested_wh = (int(m.group(1)), int(m.group(2)))

    # What the BUS says.
    d = scene.get("display")
    monitor = d["monitor"] if d else None

    if monitor is not None:
        says(f"the bus declares {len(monitor)} monitors and {d['logical']} logical monitors")
        if len(monitor) == 0:
            states.add(1)
            says("⛔ ZERO monitors: the session can be alive and complete, and "
                 "there is NOTHING to draw (STUDIES.md §gnome §3.1)")
        elif len(monitor) > 1:
            states.add(3)
            says(f"⛔ {len(monitor)} monitors: only one had been requested")
            # ⛔ AND IT SAYS WHO THEY ARE, one by one.  The first draft stopped
            #    at the count, and on 12 Aug 2026 it saw two monitors on a
            #    session that had requested one — without being able to say WHICH
            #    was the extra one, because it had not printed the name.
            #    A bench that counts and does not name sends you guessing.
            for i, m in enumerate(monitor):
                says(f"⛔   [{i}] connector={m['connector']!r} "
                     f"product={m['product']!r} serial={m['serial']!r} "
                     f"mode={m['current_mode']}")
        else:
            m0 = monitor[0]
            says(f"monitor: connector={m0['connector']!r} vendor={m0['vendor']!r} "
                 f"product={m0['product']!r} serial={m0['serial']!r}")
            if m0["product"] == SELF_CHOSEN_PRODUCT:
                states.add(3)
                says(f"⛔ the product is «{SELF_CHOSEN_PRODUCT}»: Mutter created this monitor "
                     "by itself for a ScreenCast, we did not request it "
                     "(E2 — a component that decides by itself)")
            elif m0["product"] != REQUESTED_PRODUCT:
                states.add(3)
                says(f"⛔ unexpected product {m0['product']!r}: it is neither our "
                     f"«{REQUESTED_PRODUCT}» nor the ScreenCast one")
            mc = m0["current_mode"]
            if mc is None:
                states.add(2)
                says("⛔ the monitor has no current mode")
            elif (mc["width"], mc["height"]) != (want_w, want_h):
                states.add(2)
                says(f"⛔ size {mc['width']}x{mc['height']}, expected "
                     f"{want_w}x{want_h}")
            else:
                says(f"size {mc['width']}x{mc['height']} at {mc['refresh']} Hz: "
                     "it is the requested one")

    # ⛔ THE DISAGREEMENT BETWEEN THE TWO READINGS — E1.
    if line and monitor is not None:
        our = [m for m in monitor if m["product"] == REQUESTED_PRODUCT]
        if requested_wh and not our:
            says(f"⚠ the command line asks for --virtual-monitor {requested} and on the bus "
                 f"there is no «{REQUESTED_PRODUCT}» monitor")
            states.add(6)
        if not requested_wh and our:
            says(f"⚠ on the bus there is a «{REQUESTED_PRODUCT}» and the command line does NOT "
                 "ask for it: someone put it there by another road")
            states.add(6)
        if requested_wh and our and our[0]["current_mode"]:
            mc = our[0]["current_mode"]
            if (mc["width"], mc["height"]) != requested_wh:
                says(f"⚠ the line asks for {requested_wh[0]}x{requested_wh[1]} and the bus says "
                     f"{mc['width']}x{mc['height']}")
                states.add(6)
        if not requested_headless:
            says("⚠ --headless is NOT on the command line: if headless is there it is "
                 "by accident (STUDIES.md §gnome §1.2, DECISIONS.md §4.3-bis)")

    if not states:
        states.add(0)
    for c in PRECEDENCE:
        if c in states:
            return c, sorted(states), said
    return 0, [], said


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--wait", default="1920x1080",
                   help="the REQUESTED size, written before the round")
    p.add_argument("--from-bus", action="store_true")
    p.add_argument("--from-scene", metavar="FILE")
    p.add_argument("--record", metavar="FILE")
    p.add_argument("--outcomes", metavar="FILE", default=None)
    p.add_argument("--label", default="senza-nome",
                   help="the declared SCENE, which goes next to the number")
    a = p.parse_args()

    m = re.match(r"^(\d+)x(\d+)$", a.wait)
    if not m:
        print(f"⛔ --wait {a.wait!r} is not in the form WIDTHxHEIGHT")
        return 2
    want_w, want_h = int(m.group(1)), int(m.group(2))

    if a.from_scene and a.from_bus:
        print("⛔ either --from-bus or --from-scene, not both")
        return 2

    title(f"The expected, WRITTEN BEFORE looking — scene «{a.label}»")
    inf(f"requested size: {want_w}x{want_h}")
    inf(f"expected product of the monitor: «{REQUESTED_PRODUCT}»")
    inf(f"and the one that would mean E2: «{SELF_CHOSEN_PRODUCT}»")

    if a.from_scene:
        title(f"The scene, read from {a.from_scene}")
        try:
            with open(a.from_scene) as f:
                scene = json.load(f)
        except OSError as err:
            no(f"⛔ cannot read the scene: {err}")
            return 5
        inf(f"recorded on {scene.get('when')} on {scene.get('machine')}")
    else:
        title("The scene, read from the live bus")
        scene = collect_from_bus()

    if a.record:
        os.makedirs(os.path.dirname(os.path.abspath(a.record)), exist_ok=True)
        with open(a.record, "w") as f:
            json.dump(scene, f, indent=1, ensure_ascii=False)
        inf(f"scene recorded in {a.record}")

    title("The facts, and the verdict")
    code, all_items, said = judge(scene, want_w, want_h)
    for r in said:
        (no if r.startswith("⛔") else expect if r.startswith("⚠") else inf)(r)

    cp = scene.get("positive_control") or {}
    title("⭐ The positive control, at the end as the house rule wants")
    # ⚠ On a RECORDED scene the positive control is the one from when the
    #   scene was taken, not from now: calling it «alive now» would be a measurement
    #   written as if it had been made now.  The two are kept apart.
    when = ("is alive now" if not a.from_scene
              else f"was alive when the scene was taken ({scene.get('when')})")
    if cp.get("outcome"):
        ok(f"the parser finds «layout-mode» = {cp.get('layout_mode')}")
        ok(f"and the line to the compositor {when}: idle time "
           f"{cp.get('idletime_1')} → {cp.get('idletime_2')} ms, growing")
        if a.from_scene:
            expect("⚠ recorded scene: this positive control does NOT say that the "
                "compositor is answering at this moment")
    else:
        no(f"⛔ NOT passed: {cp.get('why', 'unknown')}")
        no("   ⇒ any verdict above counts as «I could not read»")

    title("The verdict")
    inf(f"states recognised: {[MARKS[c] for c in all_items]}")
    line = f"exit {code} — {MARKS[code]}"
    print(f"    {GREEN if code == 0 else RED}{line}{FINE}")

    if a.outcomes:
        with open(a.outcomes, "a") as f:
            f.write(json.dumps({
                "when": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "bench": "F2.1", "scene": a.label,
                "wait": f"{want_w}x{want_h}",
                "exit": code, "mark": MARKS[code],
                "states": [MARKS[c] for c in all_items],
                "source": "scena:" + a.from_scene if a.from_scene else "bus",
                "positive_control": bool(cp.get("outcome")),
                "monitor": (scene.get("display") or {}).get("monitor"),
                "shell_line": scene.get("shell_line"),
            }, ensure_ascii=False) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
