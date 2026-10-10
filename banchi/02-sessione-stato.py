#!/usr/bin/env python3
"""02-sessione-stato.py — the F2.1 tool: it says which state the graphical
session is in, and says it with a different exit code for each state.

  python3 02-sessione-stato.py --attesa 1920x1080 --dal-bus
  python3 02-sessione-stato.py --attesa 1920x1080 --da-scena scene/nera.json
  python3 02-sessione-stato.py --attesa 1920x1080 --dal-bus --registra scene/x.json

===========================================================================
⛔ WHY IT EXISTS — the defect this tool prevents
===========================================================================

A headless GNOME session without `--virtual-monitor` starts **alive, complete and
black** (`STUDI.md` §gnome §3.1: in headless `needs_outputs=false`).  Alive means
really alive: `IsSessionRunning` answers `true`, the bus has fifty names,
Nautilus and the Terminal are there.  Only one thing is missing — a monitor — and
since it is missing silently, whoever measures CAPTURE on that session reads zero
frames and goes looking for the defect inside PipeWire.  `PIANO.md` phase 2: *«you
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
⛔ THE EXIT CODES, WRITTEN BEFORE THE ROUND (`PIANO.md` §0.3 point 4)
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
PRODOTTO_CHIESTO = "MetaVirtualMonitor"
# And the one it sets by itself when a virtual ScreenCast wants one
# (`meta-screen-cast-virtual-stream-src.c:606-609` [R]).  They are TWO different
# strings, and it is the only thing that tells «mine» from «its own»: the size
# does not, because it can coincide.
PRODOTTO_DA_SE = "Virtual remote monitor"

MARCHE = {
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
PRECEDENZA = [5, 4, 7, 3, 2, 1, 6, 0]

VERDE = "\033[1;32m"
ROSSO = "\033[1;31m"
GIALLO = "\033[1;33m"
FINE = "\033[0m"


def ok(t):
    print(f"    {VERDE}OK{FINE}  {t}")


def no(t):
    print(f"    {ROSSO}NO{FINE}  {t}")


def inf(t):
    print(f"    --  {t}")


def att(t):
    print(f"    {GIALLO}⚠{FINE}   {t}")


def titolo(t):
    print(f"\n\033[1m== {t}{FINE}")


# ---------------------------------------------------------------------------
# Gathering the facts.  Every fact has three possible outcomes — it is there,
# it is not there, I could not read it — and the third is not mistaken for the second.
# ---------------------------------------------------------------------------
class Ignota(Exception):
    """I could not read.  ⛔ It is not «it is not there»."""


def processi_shell():
    """The pids of gnome-shell.  ⛔ `pgrep -x`: `comm` is truncated to 15 characters
    (`FASI.md` §00-ambiente B3.1), and «gnome-shell» has 11 — it fits.  But the
    exit status is checked: 0 found, 1 none, 2+ ERROR."""
    e = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "gnome-shell"],
                       capture_output=True, text=True)
    if e.returncode == 0:
        return [int(r) for r in e.stdout.split()]
    if e.returncode == 1:
        return []
    raise Ignota(f"pgrep exited with {e.returncode}: {e.stderr.strip()!r}")


def riga_comando(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return [a.decode("utf-8", "replace")
                    for a in f.read().split(b"\0") if a]
    except OSError as err:
        raise Ignota(f"cannot read /proc/{pid}/cmdline: {err}")


def ambiente_di(pid):
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            grezzo = f.read()
    except OSError as err:
        raise Ignota(f"cannot read /proc/{pid}/environ: {err}")
    amb = {}
    for voce in grezzo.split(b"\0"):
        if b"=" in voce:
            k, _, v = voce.partition(b"=")
            amb[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
    return amb


def pid_gnome_session():
    e = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f",
                        "gnome-session-binary"], capture_output=True, text=True)
    if e.returncode == 0:
        return int(e.stdout.split()[0])
    if e.returncode == 1:
        return None
    raise Ignota(f"pgrep gnome-session-binary exited with {e.returncode}")


def bus():
    try:
        return Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except GLib.Error as err:
        raise Ignota(f"cannot connect to the session bus: {err.message}")


def chiama(conn, dest, path, iface, metodo, args=None, tetto=15000):
    """Returns (value, None) or (None, error message).

    ⛔ The error is NOT lost and does NOT become an empty value: the caller decides
       whether it is «it is not there» or «I could not look», and the two cases end
       up in two different exit codes."""
    try:
        r = conn.call_sync(dest, path, iface, metodo, args, None,
                           Gio.DBusCallFlags.NONE, tetto, None)
        return r, None
    except GLib.Error as err:
        return None, err.message


def leggi_monitor(conn):
    """The monitors according to `org.gnome.Mutter.DisplayConfig.GetCurrentState`.

    The signature of the answer is
      (u serial, a((ssss) a(siiddada{sv}) a{sv}) monitors,
                 a(iiduba(ssss)a{sv}) logical, a{sv} props)
    where `(ssss)` is (connector, vendor, product, serial)
    and every mode is (id, width, height, refresh, preferred-scale,
                       supported-scales, properties) — and the mode IN USE carries
    `is-current` among its properties."""
    r, errore = chiama(conn, "org.gnome.Mutter.DisplayConfig",
                       "/org/gnome/Mutter/DisplayConfig",
                       "org.gnome.Mutter.DisplayConfig", "GetCurrentState")
    if errore is not None:
        raise Ignota(f"GetCurrentState: {errore}")
    serial, monitors, logical, props = r.unpack()
    elenco = []
    for (connettore, fornitore, prodotto, seriale), modi, mprops in monitors:
        corrente = None
        for m in modi:
            mid, larg, alt, refresh, scala, scale, mp = m
            if mp.get("is-current"):
                corrente = {"id": mid, "larghezza": larg, "altezza": alt,
                            "refresh": round(refresh, 3)}
        elenco.append({"connettore": connettore, "fornitore": fornitore,
                       "prodotto": prodotto, "seriale": seriale,
                       "modo_corrente": corrente, "modi": len(modi)})
    return {"serial": serial, "monitor": elenco, "logici": len(logical),
            "proprieta": {k: str(v) for k, v in props.items()}}


# ---------------------------------------------------------------------------
def raccogli_dal_bus():
    """Builds the SCENE: all the raw facts, without judging them.

    ⭐ Separating gathering from judging is not elegance: it is the only thing that
       lets the judgement be certified on RECORDED scenes, without having to
       break a real machine for every opposite case."""
    scena = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "macchina": os.uname().nodename, "ignote": []}

    try:
        pids = processi_shell()
        scena["shell_pid"] = pids
        scena["shell_riga"] = riga_comando(pids[0]) if pids else None
    except Ignota as e:
        scena["shell_pid"] = None
        scena["shell_riga"] = None
        scena["ignote"].append(str(e))

    try:
        p = pid_gnome_session()
        scena["gnome_session_pid"] = p
        if p:
            amb = ambiente_di(p)
            # ⛔ The trap of `STUDI.md` §gnome §3.1: `gnome-session.in:3-14`
            #    re-executes itself inside a LOGIN shell if `$SHELL` is in
            #    /etc/shells.  The real check is `[ -n "$SHELL" ]`, so
            #    ABSENT and EMPTY are both fine: they are recorded separately
            #    so as not to suggest they are the same thing.
            scena["shell_var"] = amb.get("SHELL", None)
            scena["shell_var_presente"] = "SHELL" in amb
            scena["xdg_session_type"] = amb.get("XDG_SESSION_TYPE")
        else:
            scena["shell_var"] = None
            scena["shell_var_presente"] = None
            scena["xdg_session_type"] = None
    except Ignota as e:
        scena["gnome_session_pid"] = None
        scena["shell_var_presente"] = None
        scena["ignote"].append(str(e))

    try:
        conn = bus()
    except Ignota as e:
        scena["ignote"].append(str(e))
        scena["sessione_gira"] = None
        scena["display"] = None
        scena["controllo_positivo"] = {"esito": False, "perche": str(e)}
        return scena

    r, errore = chiama(conn, "org.gnome.SessionManager", "/org/gnome/SessionManager",
                       "org.gnome.SessionManager", "IsSessionRunning")
    # ⛔ `ServiceUnknown` = the session is not there (a fact about the subject);
    #    any other error = I could not look (a fact about the tool).
    if errore is None:
        scena["sessione_gira"] = bool(r.unpack()[0])
        scena["sessione_errore"] = None
    elif "ServiceUnknown" in errore or "was not provided by any" in errore:
        scena["sessione_gira"] = False
        scena["sessione_errore"] = errore
    else:
        scena["sessione_gira"] = None
        scena["sessione_errore"] = errore
        scena["ignote"].append(f"IsSessionRunning: {errore}")

    try:
        scena["display"] = leggi_monitor(conn)
    except Ignota as e:
        scena["display"] = None
        scena["ignote"].append(str(e))

    scena["controllo_positivo"] = controllo_positivo(conn, scena)
    return scena


def controllo_positivo(conn, scena):
    """⭐ «Can this tool find something that is surely there?»"""
    esito = {"layout_mode": None, "idletime_1": None, "idletime_2": None,
             "esito": False, "perche": ""}

    d = scena.get("display")
    if d is not None:
        esito["layout_mode"] = d["proprieta"].get("layout-mode")

    for chiave in ("idletime_1", "idletime_2"):
        r, errore = chiama(conn, "org.gnome.Mutter.IdleMonitor",
                           "/org/gnome/Mutter/IdleMonitor/Core",
                           "org.gnome.Mutter.IdleMonitor", "GetIdletime")
        esito[chiave] = r.unpack()[0] if errore is None else None
        if errore is not None:
            esito["perche"] = f"GetIdletime: {errore}"
            return esito
        time.sleep(0.35)

    if esito["layout_mode"] is None:
        esito["perche"] = ("the answer of GetCurrentState has no «layout-mode», "
                           "which is always there: the parser is broken, not the session")
        return esito
    if esito["idletime_2"] is None or esito["idletime_1"] is None:
        esito["perche"] = "IdleMonitor did not answer"
        return esito
    if esito["idletime_2"] <= esito["idletime_1"]:
        esito["perche"] = (f"the idle time does not grow ({esito['idletime_1']} → "
                           f"{esito['idletime_2']}): I am reading a frozen answer")
        return esito
    esito["esito"] = True
    return esito


# ---------------------------------------------------------------------------
# The judgement: from the scene to the number.  No reading in here — so it can
# run on a recorded scene, and that is what makes the tool certifiable
# without breaking a real machine for every opposite case.
# ---------------------------------------------------------------------------
def giudica(scena, attesa_l, attesa_a):
    stati = set()
    detto = []

    def dice(t):
        detto.append(t)

    if scena.get("ignote"):
        stati.add(5)
        for i in scena["ignote"]:
            dice(f"⛔ UNKNOWN: {i}")
    cp = scena.get("controllo_positivo") or {}
    if not cp.get("esito"):
        stati.add(5)
        dice(f"⛔ the positive control did NOT pass: {cp.get('perche', 'unknown')}")

    pids = scena.get("shell_pid")
    if not pids:
        stati.add(4)
        dice("no gnome-shell process")
    if scena.get("sessione_gira") is False:
        stati.add(4)
        dice("IsSessionRunning answers no (or the name is not on the bus)")

    # ⛔ SHELL, and the two right ways of having it: absent or empty.
    if scena.get("gnome_session_pid"):
        if scena.get("shell_var_presente") and scena.get("shell_var"):
            stati.add(7)
            dice(f"⛔ SHELL={scena['shell_var']!r} in the environment of gnome-session: "
                 "it re-executed itself inside a login shell (STUDI.md §gnome §3.1)")
        else:
            dice("SHELL " + ("empty" if scena.get("shell_var_presente") else "absent")
                 + " in the environment of gnome-session: the §3.1 trap did not bite")

    # What the COMMAND LINE asks for.
    riga = scena.get("shell_riga") or []
    chiesto = None
    chiesto_headless = "--headless" in riga
    for i, a in enumerate(riga):
        m = re.match(r"^--virtual-monitor=(.+)$", a)
        if m:
            chiesto = m.group(1)
        elif a == "--virtual-monitor" and i + 1 < len(riga):
            chiesto = riga[i + 1]
    chiesto_wh = None
    if chiesto:
        m = re.match(r"^(\d+)x(\d+)", chiesto)
        if m:
            chiesto_wh = (int(m.group(1)), int(m.group(2)))

    # What the BUS says.
    d = scena.get("display")
    monitor = d["monitor"] if d else None

    if monitor is not None:
        dice(f"the bus declares {len(monitor)} monitors and {d['logici']} logical monitors")
        if len(monitor) == 0:
            stati.add(1)
            dice("⛔ ZERO monitors: the session can be alive and complete, and "
                 "there is NOTHING to draw (STUDI.md §gnome §3.1)")
        elif len(monitor) > 1:
            stati.add(3)
            dice(f"⛔ {len(monitor)} monitors: only one had been requested")
            # ⛔ AND IT SAYS WHO THEY ARE, one by one.  The first draft stopped
            #    at the count, and on 12 Aug 2026 it saw two monitors on a
            #    session that had requested one — without being able to say WHICH
            #    was the extra one, because it had not printed the name.
            #    A bench that counts and does not name sends you guessing.
            for i, m in enumerate(monitor):
                dice(f"⛔   [{i}] connector={m['connettore']!r} "
                     f"product={m['prodotto']!r} serial={m['seriale']!r} "
                     f"mode={m['modo_corrente']}")
        else:
            m0 = monitor[0]
            dice(f"monitor: connector={m0['connettore']!r} vendor={m0['fornitore']!r} "
                 f"product={m0['prodotto']!r} serial={m0['seriale']!r}")
            if m0["prodotto"] == PRODOTTO_DA_SE:
                stati.add(3)
                dice(f"⛔ the product is «{PRODOTTO_DA_SE}»: Mutter created this monitor "
                     "by itself for a ScreenCast, we did not request it "
                     "(E2 — a component that decides by itself)")
            elif m0["prodotto"] != PRODOTTO_CHIESTO:
                stati.add(3)
                dice(f"⛔ unexpected product {m0['prodotto']!r}: it is neither our "
                     f"«{PRODOTTO_CHIESTO}» nor the ScreenCast one")
            mc = m0["modo_corrente"]
            if mc is None:
                stati.add(2)
                dice("⛔ the monitor has no current mode")
            elif (mc["larghezza"], mc["altezza"]) != (attesa_l, attesa_a):
                stati.add(2)
                dice(f"⛔ size {mc['larghezza']}x{mc['altezza']}, expected "
                     f"{attesa_l}x{attesa_a}")
            else:
                dice(f"size {mc['larghezza']}x{mc['altezza']} at {mc['refresh']} Hz: "
                     "it is the requested one")

    # ⛔ THE DISAGREEMENT BETWEEN THE TWO READINGS — E1.
    if riga and monitor is not None:
        nostro = [m for m in monitor if m["prodotto"] == PRODOTTO_CHIESTO]
        if chiesto_wh and not nostro:
            dice(f"⚠ the command line asks for --virtual-monitor {chiesto} and on the bus "
                 f"there is no «{PRODOTTO_CHIESTO}» monitor")
            stati.add(6)
        if not chiesto_wh and nostro:
            dice(f"⚠ on the bus there is a «{PRODOTTO_CHIESTO}» and the command line does NOT "
                 "ask for it: someone put it there by another road")
            stati.add(6)
        if chiesto_wh and nostro and nostro[0]["modo_corrente"]:
            mc = nostro[0]["modo_corrente"]
            if (mc["larghezza"], mc["altezza"]) != chiesto_wh:
                dice(f"⚠ the line asks for {chiesto_wh[0]}x{chiesto_wh[1]} and the bus says "
                     f"{mc['larghezza']}x{mc['altezza']}")
                stati.add(6)
        if not chiesto_headless:
            dice("⚠ --headless is NOT on the command line: if headless is there it is "
                 "by accident (STUDI.md §gnome §1.2, DECISIONI.md §4.3-bis)")

    if not stati:
        stati.add(0)
    for c in PRECEDENZA:
        if c in stati:
            return c, sorted(stati), detto
    return 0, [], detto


# ---------------------------------------------------------------------------
def principale():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--attesa", default="1920x1080",
                   help="the REQUESTED size, written before the round")
    p.add_argument("--dal-bus", action="store_true")
    p.add_argument("--da-scena", metavar="FILE")
    p.add_argument("--registra", metavar="FILE")
    p.add_argument("--esiti", metavar="FILE", default=None)
    p.add_argument("--etichetta", default="senza-nome",
                   help="the declared SCENE, which goes next to the number")
    a = p.parse_args()

    m = re.match(r"^(\d+)x(\d+)$", a.attesa)
    if not m:
        print(f"⛔ --attesa {a.attesa!r} is not in the form WIDTHxHEIGHT")
        return 2
    attesa_l, attesa_a = int(m.group(1)), int(m.group(2))

    if a.da_scena and a.dal_bus:
        print("⛔ either --dal-bus or --da-scena, not both")
        return 2

    titolo(f"The expected, WRITTEN BEFORE looking — scene «{a.etichetta}»")
    inf(f"requested size: {attesa_l}x{attesa_a}")
    inf(f"expected product of the monitor: «{PRODOTTO_CHIESTO}»")
    inf(f"and the one that would mean E2: «{PRODOTTO_DA_SE}»")

    if a.da_scena:
        titolo(f"The scene, read from {a.da_scena}")
        try:
            with open(a.da_scena) as f:
                scena = json.load(f)
        except OSError as err:
            no(f"⛔ cannot read the scene: {err}")
            return 5
        inf(f"recorded on {scena.get('quando')} on {scena.get('macchina')}")
    else:
        titolo("The scene, read from the live bus")
        scena = raccogli_dal_bus()

    if a.registra:
        os.makedirs(os.path.dirname(os.path.abspath(a.registra)), exist_ok=True)
        with open(a.registra, "w") as f:
            json.dump(scena, f, indent=1, ensure_ascii=False)
        inf(f"scene recorded in {a.registra}")

    titolo("The facts, and the verdict")
    codice, tutti, detto = giudica(scena, attesa_l, attesa_a)
    for r in detto:
        (no if r.startswith("⛔") else att if r.startswith("⚠") else inf)(r)

    cp = scena.get("controllo_positivo") or {}
    titolo("⭐ The positive control, at the end as the house rule wants")
    # ⚠ On a RECORDED scene the positive control is the one from when the
    #   scene was taken, not from now: calling it «alive now» would be a measurement
    #   written as if it had been made now.  The two are kept apart.
    quando = ("is alive now" if not a.da_scena
              else f"was alive when the scene was taken ({scena.get('quando')})")
    if cp.get("esito"):
        ok(f"the parser finds «layout-mode» = {cp.get('layout_mode')}")
        ok(f"and the line to the compositor {quando}: idle time "
           f"{cp.get('idletime_1')} → {cp.get('idletime_2')} ms, growing")
        if a.da_scena:
            att("⚠ recorded scene: this positive control does NOT say that the "
                "compositor is answering at this moment")
    else:
        no(f"⛔ NOT passed: {cp.get('perche', 'unknown')}")
        no("   ⇒ any verdict above counts as «I could not read»")

    titolo("The verdict")
    inf(f"states recognised: {[MARCHE[c] for c in tutti]}")
    riga = f"exit {codice} — {MARCHE[codice]}"
    print(f"    {VERDE if codice == 0 else ROSSO}{riga}{FINE}")

    if a.esiti:
        with open(a.esiti, "a") as f:
            f.write(json.dumps({
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "banco": "F2.1", "scena": a.etichetta,
                "attesa": f"{attesa_l}x{attesa_a}",
                "uscita": codice, "marca": MARCHE[codice],
                "stati": [MARCHE[c] for c in tutti],
                "fonte": "scena:" + a.da_scena if a.da_scena else "bus",
                "controllo_positivo": bool(cp.get("esito")),
                "monitor": (scena.get("display") or {}).get("monitor"),
                "shell_riga": scena.get("shell_riga"),
            }, ensure_ascii=False) + "\n")
    return codice


if __name__ == "__main__":
    sys.exit(principale())
