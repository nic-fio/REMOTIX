#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c17 — ⭐ «THE CLIPBOARD GOES BOTH WAYS»
===========================================================================

    python3 11-c17-gli-appunti-vanno-nei-due-versi.py --port 8512
    python3 11-c17-gli-appunti-vanno-nei-due-versi.py --port 8512 --no-copy

    what must be true         : a text copied on the device is pasted in the
                                desktop, and one copied in the desktop reaches the
                                device — even whoever REATTACHES
    where it starts from      : a new session, a new tenant
    what it looks at          : three facts, each with its own name
      A  device → session         `wl-paste` in the session reads the text
                                  the client announced
      B  session → device         `wl-copy` in the session, and the server
                                  ANNOUNCES it to the attached client (§7.4)
      R  whoever reattaches       a new client on the same child
                                  receives it whole, without anyone copying again
    how I know it can give red: `--no-copy` — nobody copies anything, on
                                either side ⇒ three reds

⭐ Born in phase 12 (19 Sep 2026): the KDE clipboard was tested only by hand
   (`07-b54`), and this mesh puts it in the net.  And at the first run it
   found a REAL defect, of all desktops: the text copied in the session
   before the RCP session was open was kept and never announced
   (`src/rcp.c`, `announce_kept`) ⇒ fact R.

⛔ Two implementations on the two sides, and neither is the server: `01-b3-cliente.py`
   (which has read only `RCP.md`) and **GTK** (`appunti-gtk.py`), which is not ours
   and has never heard of RCP.
⭐⭐ AND THE ARBITER IS THE SAME ON BOTH DESKTOPS — 20 Sep 2026.  Before they were
   `wl-copy`/`wl-paste`, which speak `zwlr_data_control_manager_v1`: KWin has
   it, ⛔ Mutter does not, and on GNOME the mesh exited 3 («I could not
   look»).  ⇒ Now we do what a PERSON does: a real window is opened,
   ⭐ **it is given the focus with a click sent through the product**
   (`01-b3-cliente.py --click`), and from then on the clipboard is touched — on
   GNOME as on KDE.  ⚠ And if the click did not arrive, the red would be the
   product's for not delivering the input: it is the same road as C4.

Outcomes: 0 green · 1 red · 3 I could not look (⛔ it is NOT a red).
⛔ With `--no-copy` it reads the other way round: 0 = the fault was SEEN.
"""
import argparse
import importlib.util
import json
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(HERE, "01-b3-cliente.py")
PASSWORD = "provanic2026"
# ⭐ The external arbiter: GTK, that is `wl_data_device` — the clipboard of
#    real applications.  ⛔ It wants the FOCUS, and the focus is given by the
#    client's click (`--click`).  It sits next to this mesh inside the box.
# ⚠ Where the arbiter reports its copy: the bench READS it instead of sleeping
#   a fixed time — with GTK the copy starts when the focus arrives, and the focus
#   arrives with the client's click (every 4 s), not at a time decided by us.
#
# ⛔⛔ AND THE FILE BELONGS TO THE TENANT, not one for all — 21 Sep 2026.
#   Here there was `PROVA_COPIA = "/tmp/remotix-arbitro-copia.log"`: ONE fixed name,
#   written and deleted BY THE TENANT (the script runs with `runuser -u chi`),
#   and ⛔ never removed at the end.  `[R]` from the code, and the same shape as
#   `/tmp/mozilla` (C2): the first `c17uNNN` creates it, `userdel` leaves it to a
#   nameless uid, and `/tmp` has the «sticky» bit ⇒ a tenant with ANOTHER uid
#   can neither remove it (`rm -f` fails silently) nor rewrite it
#   (`>` refused) ⇒ the shell does not run the copy command ⇒ ⛔ **B and R
#   red, that is «the server does not announce the copy made in the desktop»**, while
#   nobody had copied anything.
#   ⚠ And it bites ONLY in an old box: as long as the users stay the same
#     `useradd` gives every `c17u` the same uid again (4012) and the file stays its own;
#     ⛔ one tenant left over from a dead run is enough (`[M]` 21 Sep: in kde
#     `user@4024` and `user@4025` failed, that is uids well beyond 4012) and C17's
#     uid shifts.  `[?]` the direct link was not measured inside the
#     old box: it is the only write shared between different tenants
#     that C17 does, and it matches the bisection (new box ⇒ green 2 out of 2).
# ⭐ Now the name carries the tenant, like `outcome_a` and `outcome_r`, and it is removed
#   at the end: no run leaves anything to the next run.
def test_copy(chi):
    return "/tmp/%s-arbitro-copia.log" % chi


ARBITER_GTK = ("env GDK_BACKEND=wayland python3 " +
               os.path.join(HERE, "appunti-gtk.py"))


def arbiter(chi):
    """⭐ The arbiter THIS desktop allows — and it is ASKED, not guessed.

    ⛔ `[M]` 20 Sep 2026, measured on both boxes:
      · where `zwlr_data_control_manager_v1` exists (KWin) `wl-clipboard` reads and
        writes without needing the focus, and it is the shortest road;
      · where it does not (Mutter) `wl-copy` and `wl-paste` stay HUNG, and the only
        road is that of real applications: GTK plus the focus, which arrives
        with the click sent by the client (`--click`).
    ⚠ The difference is the BENCH's, not the product's: the product on both
      desktops does the same thing, and the two roads lead to the same judgement.
    """
    listing = in_session(chi, "wayland-info 2>/dev/null | grep -c -E "
                                 "'zwlr_data_control_manager_v1|"
                                 "ext_data_control_manager_v1'") or "0"
    if listing.strip().lstrip("0"):
        return {"label_name": "wl-clipboard",
                "paste": "timeout 8 wl-paste -n 2>/dev/null",
                "copia": "pkill -x wl-copy; printf %%s '%s' | timeout 90 wl-copy "
                         ">" + test_copy(chi) + " 2>&1 &",
                "attesa_copia": 3, "says": ""}
    return {"label_name": "GTK with focus (the client's click)",
            "paste": ARBITER_GTK + " paste 2>/dev/null",
            "copia": ARBITER_GTK + " copia '%s' 60 >" + test_copy(chi) + " 2>&1 &",
            "attesa_copia": 30, "says": "copied WITH FOCUS"}


def load_c1():
    """From C1 come the admission and the card groups: one place only (§1.47)."""
    for p in (os.path.join(HERE, "11-c1-nasce-e-si-vede.py"),):
        if os.path.exists(p):
            spec = importlib.util.spec_from_file_location("c1", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if callable(getattr(m, "was_admitted", None)) and \
               callable(getattr(m, "ensure_groups", None)):
                return m
    print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me ⇒ I could not look")
    sys.exit(3)


def run_loop(argv, time_limit=30, **kw):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=time_limit, **kw)
    except subprocess.TimeoutExpired:
        return None


def clear_out(chi):
    run_loop(["loginctl", "terminate-user", chi], 15)
    for _ in range(40):
        r = run_loop(["pgrep", "-u", chi], 5)
        if r is None or r.returncode != 0:
            break
        time.sleep(0.25)
    run_loop(["pkill", "-KILL", "-u", chi], 5)
    run_loop(["userdel", "-r", chi], 15)


def socket_wayland(chi):
    """The socket of the tenant's compositor, or `None` if it is not there yet."""
    r = run_loop(["id", "-u", chi], 5)
    run = "/run/user/%s" % (r.stdout.strip() if r else "")
    if not os.path.isdir(run):
        return None
    names = sorted(f for f in os.listdir(run)
                  if f.startswith("wayland-") and f[8:].isdigit())
    return names[0] if names else None


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ A MISSING TOOL IS NOT A RED — 21 Sep 2026, phase 13.
#
# `[R]` Here the script's `stdout` was taken without looking at the exit
#   code.  ⇒ In the xfce box (and lxqt), where `wl-clipboard` was not there,
#   `wl-paste: command not found` became `""`, A's guard (which looks at
#   `None`) did not fire, and the mesh printed **RED**: a defect of the BENCH
#   with the face of a defect of the product (§1.51).
# ⛔ And with the injected fault it was worse: A, B and R all «NO» for lack
#   of tools ⇒ «THE INJECTED FAULT WAS SEEN», outcome 0 ⇒ a
#   certification for C13 that had looked at nothing.
# ⇒ Two nets, one under the other:
#   1. ⭐ a POSITIVE check before starting (`missing_tool`):
#      every piece the chosen arbiter will use is ASKED of the session;
#   2. and here, for what slips through: the shell that exits 126/127 (command not
#      found / not executable) does not give a stdout, it gives `MissingTool`.
# ⚠ And the rest does NOT change: a tool present that answers `""` (empty
#   clipboard) stays a «NO», as before — it is the case the mesh must see.
# ═══════════════════════════════════════════════════════════════════════════
class MissingTool(Exception):
    """A piece of the BENCH is missing in the session ⇒ outcome 3, never 1 and never 0."""


# `[R]` POSIX, «Command Search and Execution»: 127 = not found, 126 =
#   found but not executable.  `timeout` and `env` pass them on unchanged.
NOT_FOUND = (126, 127)


def in_session_rc(chi, script, time_limit=15):
    """Like `in_session`, but returns `(code, stdout)`.  `None` = it is not there."""
    uid = run_loop(["id", "-u", chi], 5).stdout.strip()
    run = "/run/user/%s" % uid
    socket = sorted(f for f in os.listdir(run)
                    if f.startswith("wayland-") and f[8:].isdigit()) if os.path.isdir(run) else []
    if not socket:
        return None
    r = run_loop(["runuser", "-u", chi, "--", "env", "XDG_RUNTIME_DIR=" + run,
               "WAYLAND_DISPLAY=" + socket[0], "sh", "-c", script], time_limit)
    return None if r is None else (r.returncode, r.stdout)


def in_session(chi, script, time_limit=15):
    """A script inside the tenant's Wayland session.  `None` = it is not there.

    ⛔ If the shell says «command not found» (126/127) it raises
       `MissingTool` instead of returning an empty stdout (see above).
    """
    r = in_session_rc(chi, script, time_limit)
    if r is None:
        return None
    code_v, out_dir = r
    if code_v in NOT_FOUND:
        raise MissingTool("«%s» exits %d (command not found or not executable)"
                               % (script, code_v))
    return out_dir


# ⭐ The pieces each arbiter uses — and how one ASKS whether they are there.
#   ⚠ `wayland-info` is in both: it is the one that CHOOSES the arbiter, and if
#     it were missing the choice would fall on GTK silently (`grep -c` answers «0»).
#   ⚠ For GTK `command -v` is not enough: `python3` is always there, it is `import gi`
#     with GTK 4 that is missing ⇒ it is really imported, as `appunti-gtk.py` does.
COMMON_TOOLS = [
    ("wayland-info (wayland-utils)", "command -v wayland-info"),
]
TOOLS = {
    "wl-clipboard": [
        ("wl-paste (wl-clipboard)", "command -v wl-paste"),
        ("wl-copy (wl-clipboard)", "command -v wl-copy"),
    ],
    "GTK": [
        ("appunti-gtk.py", "test -r " + os.path.join(HERE, "appunti-gtk.py")),
        ("python3-gi + gir1.2-gtk-4.0",
         "python3 -c 'import gi; gi.require_version(\"Gtk\", \"4.0\"); "
         "gi.require_version(\"Gdk\", \"4.0\"); "
         "from gi.repository import Gdk, Gtk'"),
    ],
}


def missing_tool(chi, listing):
    """⭐ The POSITIVE check: returns the name of the first missing piece, or `None`.

    ⛔ A piece the session does not answer about (no socket, time out)
       counts as missing: I do not know whether it is there, and so I do not look.
    """
    for label_name, prova in listing:
        r = in_session_rc(chi, prova + " >/dev/null 2>&1", 30)
        if r is None or r[0] != 0:
            return label_name
    return None


def client(chi, port, *other_one):
    return ["python3", "-u", CLIENT, "--address", "127.0.0.1", "--port", str(port),
            "--username", chi, "--password", PASSWORD] + list(other_one)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--no-copy", action="store_true",
                   help="⛔ THE INJECTED FAULT: nobody copies anything ⇒ three reds")
    p.add_argument("--wait", type=float, default=20.0)
    a = p.parse_args()
    c1 = load_c1()

    chi = "c17u%d" % random.randint(100, 999)
    mark = random.randint(10000, 99999)
    text_a = "C17-A-àèìòù-%d" % mark
    text_b = "C17-B-€ß→%d" % mark
    outcome_a = "/tmp/%s-a.json" % chi
    outcome_r = "/tmp/%s-r.json" % chi
    signal_v = "/tmp/%s-segnale" % chi
    print("== C17 — the clipboard goes both ways (%s, port %d)%s"
          % (chi, a.port, "  ⛔ INJECTED FAULT: --no-copy" if a.no_copy else ""))

    clear_out(chi)
    if run_loop(["useradd", "-m", "-s", "/bin/bash", chi]).returncode != 0:
        print("⛔ I could not create the tenant ⇒ I could not look")
        return 3
    run_loop(["chpasswd"], input="%s:%s\n" % (chi, PASSWORD))
    e_gr, reason_text = c1.ensure_groups(chi)
    if e_gr != 0:
        print("⛔ %s ⇒ I could not look" % reason_text)
        clear_out(chi)
        return 3
    for f in (outcome_a, outcome_r, signal_v, test_copy(chi)):
        if os.path.exists(f):
            os.unlink(f)

    first = None
    try:
        # ── the first client: announces A, stays, and listens to the announcements ─
        # ⭐ `--click`: the focus to the arbiter's windows, and it is REDONE every 4 s
        #    because the windows are two, one after the other (read, copy).
        argv = client(chi, a.port, "--signal_v", signal_v, "--stays", "75",
                       "--click", "960,540", "--click-after", "3", "--click-every", "4",
                       "--clipboard-write", outcome_a)
        if not a.no_copy:
            argv += ["--clipboard-copy", text_a]
        first = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True)
        fine = time.time() + 60
        while not os.path.exists(signal_v) and time.time() < fine and first.poll() is None:
            time.sleep(0.25)
        if not os.path.exists(signal_v):
            out_dir = first.communicate(timeout=30)[0] if first.poll() is None else first.stdout.read()
            accepted = c1.was_admitted(out_dir)
            print("⛔ the client did not attach (admitted: %s) ⇒ I could not look" % accepted)
            return 3

        # ⭐ THE CLIENT SENDS THE CLICK (`--click`): here we only wait for
        #    the arbiter's window to be up and focused.
        # A — device → session
        # ⚠ One single generous call, not a round of calls: the arbiter
        #   opens its window and WAITS for the focus (which arrives with the
        #   client's click, every 4 s), then reads.  Calling it ten times would mean
        #   ten windows stealing the focus from each other.
        t0 = time.time()
        # ⛔ First the SOCKET: the client's signal says «I am attached», not
        #    «the graphical session is there».  Asking for the arbiter before the
        #    compositor would give «None» and a red that is not the product's.
        while time.time() - t0 < 90 and socket_wayland(chi) is None:
            time.sleep(1)
        if socket_wayland(chi) is None:
            print("   ⚠ no Wayland socket in 90 s: the session is not there"
                  " ⇒ I could not look")
            return 3
        # ⚠ A few attempts, one at a time: the product's offer to the
        #   session arrives when the clipboard opens, which is after the stage.
        #   ⛔ Not in parallel: two windows would steal the focus from each other.
        # ⛔ FIRST we ask whether the tools are there (see `MissingTool`):
        #    one that is missing is «I could not look», ⛔ never a red.
        missing = missing_tool(chi, COMMON_TOOLS)
        arb = arbiter(chi) if missing is None else None
        if arb is not None:
            print("   the arbiter of this desktop: %s" % arb["label_name"])
            key_id = "wl-clipboard" if arb["label_name"] == "wl-clipboard" else "GTK"
            missing = missing_tool(chi, TOOLS[key_id])
        if missing is not None:
            print("   ⛔ «%s» is missing in the session: it is a tool of the BENCH, not of the"
                  " product ⇒ I could not look" % missing)
            if first.poll() is None:
                first.kill()
            return 3
        seen_v = None
        for _ in range(5):
            seen_v = in_session(chi, arb["paste"], 60)
            if seen_v == text_a:
                break
            time.sleep(4)
        ok_a = seen_v == text_a
        print("   A  device → session       : %s  (expected «%s», the session pastes «%s», %.0f s)"
              % ("⭐ YES" if ok_a else "⛔ NO", text_a, seen_v, time.time() - t0))
        if seen_v is None:
            print("   ⚠ no Wayland socket: the session is not there ⇒ I could not look")
            return 3

        # B — session → device, with the client attached
        if not a.no_copy:
            in_session(chi, "rm -f " + test_copy(chi))
            in_session(chi, arb["copia"] % text_b)
            # ⚠ We wait for the copy to HAVE HAPPENED, not a fixed time: with GTK
            #   it starts when the focus arrives, and the focus arrives with the
            #   client's click.  ⛔ A clock-based wait gave an intermittent red
            #   (`[M]` 20 Sep 2026, the net: B and R red, the same runs green
            #   by hand a minute before).
            t1 = time.time()
            while time.time() - t1 < arb["attesa_copia"]:
                time.sleep(1)
                if not arb["says"]:
                    break
                said = in_session(chi, "cat " + test_copy(chi) + " 2>/dev/null") or ""
                if arb["says"] in said:
                    print("   the copy in the session happened after %.0f s"
                          % (time.time() - t1))
                    break
            else:
                if arb["says"]:
                    print("   ⚠ in %d s the arbiter did not say «%s»: the copy "
                          "in the session did not start"
                          % (arb["attesa_copia"], arb["says"]))
            time.sleep(2)
        # ⚠ The ceiling is wider than the client's `--stays` (75 s), or it
        #   would expire waiting for a client that is doing its job.
        out_dir = first.communicate(timeout=150)[0]
        # ⚠ From the client's output and not from its file: it writes the file BEFORE
        #   staying attached (`write_clipboard` comes before `--stays`), and
        #   B's announcement arrives after.
        announcements = [(int(m.group(1)), int(m.group(2))) for m in re.finditer(
            r"the server announces transfer (\d+), (\d+) bytes", out_dir)]
        len_b = len(text_b.encode("utf-8"))
        ok_b = any(n == len_b for _, n in announcements)
        print("   B  session → device       : %s  (server announcements: %s, expected one of %d bytes)"
              % ("⭐ YES" if ok_b else "⛔ NO", announcements, len_b))

        # R — whoever reattaches receives the session's text
        r = run_loop(client(chi, a.port, "--clipboard-wait", "15", "--clipboard-write", outcome_r), 60)
        try:
            received_one = json.load(open(outcome_r))["received_one"]
        except (OSError, ValueError, KeyError):
            received_one = None
        ok_r = received_one == text_b
        print("   R  whoever reattaches     : %s  (expected «%s», received «%s»)"
              % ("⭐ YES" if ok_r else "⛔ NO", text_b, received_one))
        if r is not None and c1.was_admitted(r.stdout) is False:
            print("   ⛔ the second client was REJECTED ⇒ I could not look")
            return 3

        # ⛔ With the injected fault the outcome reads THE OTHER WAY ROUND, as in the whole
        #    net (C8 `--no-fix`): 0 = the fault was SEEN.  `[M]` 19
        #    Sep 2026, the first run in the net: it exited 1 on three reds, and the
        #    hook said «fault not seen» — it was right.
        if a.no_copy:
            if not (ok_a or ok_b or ok_r):
                print("⭐ THE INJECTED FAULT WAS SEEN: A, B and R all red")
                return 0
            print("⛔⛔ the injected fault was NOT seen: something is green without copies")
            return 1
        if ok_a and ok_b and ok_r:
            print("⭐ GREEN — both ways, and whoever reattaches too")
            return 0
        print("⛔⛔ RED — %s" % ", ".join(n for n, v in (("A", ok_a), ("B", ok_b), ("R", ok_r)) if not v))
        return 1
    except MissingTool as e:
        # ⛔ The second net: a tool that slipped past the earlier check.
        #    ⇒ 3, even with the injected fault (where otherwise it would have been 0).
        print("   ⛔ a tool of the BENCH is missing in the session: %s"
              " ⇒ I could not look" % e)
        if first is not None and first.poll() is None:
            first.kill()
        return 3
    finally:
        clear_out(chi)
        for f in (outcome_a, outcome_r, signal_v, test_copy(chi)):
            if os.path.exists(f):
                os.unlink(f)


if __name__ == "__main__":
    sys.exit(main())
