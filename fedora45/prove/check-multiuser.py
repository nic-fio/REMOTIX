#!/usr/bin/env python3
"""check-multiuser - SEVERAL USERS at once on a running REMOTIX box, with real browsers (SPECS 5.1 and 5.5).

    python3 check-multiuser.py [--box xfce] [--browser chrome] [--password Mu-test-2026]

Runs ON THE DEV SERVER (drives ./boxes/box.sh and one headless labwc per browser, see lib.py). The users mu1 mu2 mu3 are made
here (a fresh box has none); a login with a user that may not exist is never tried (a wrong login counts for the ban).
One line per check:  PASS|FAIL|BLOCKED <name> - evidence ;  exit 0 only if all PASS.
  two-users   : mu1 and mu2 attached together; each canvas shows ITS OWN colour (red / green) and not the other's;
                mouse clicks and typed text of each reach only its own session (a test window in each session logs them).
  three-users : the same with mu1, mu2, mu3 (red / green / blue).
  same-user   : mu1 attached in browser A, browser B logs in as mu1: B must be refused (0x0F, SPECS 5.1) while A stays in and
                usable; then A leaves, B gets in and finds A's session again (same window, same text) and can use it.
FAIL = the product did not do it.  BLOCKED = the tool could not look.  Pictures go to <prove>/shots/multi-*.png.
The desktop is looked at only after the shell is up (on KDE: plasmashell running and the splash gone), as check-base does."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED, frac  # noqa: E402

USERS = ["mu1", "mu2", "mu3"]
PASSWORD = "Mu-test-2026"
COLOURS = [("red", (208, 32, 32)), ("green", (32, 176, 32)), ("blue", (32, 32, 208))]
WORDS = ["alfa", "bravo", "charlie"]
POINTS = [(0.25, 0.25), (0.75, 0.75), (0.5, 0.9)]


class Client:
    """One browser (own compositor, own profile) logged in as one user."""

    def __init__(self, a, user, idx, tag):
        self.a, self.user, self.idx, self.notes = a, user, idx, []
        self.rig = lib.Rig(a.box, "chrome", user, PASSWORD, "%s-%d" % (tag, idx), cap=a.cap)
        try:
            self.rig.start(make_user=False)  # the users were made in main()
        except BaseException:
            self.rig.stop()
            raise
        self.box, self.g = self.rig.box, self.rig.g

    def login(self, retry_taken=False):
        """(admitted, state). With retry_taken, a 'slot taken' refusal is tried again for up to 32 s (the previous client of
        the same user has just left: SPECS 5.1 'try again in a few seconds')."""
        self.rig.open_page()
        t0 = time.time()
        ok, s = self.rig.try_login(retry=32 if retry_taken else 0)
        if ok and time.time() - t0 > 6:
            self.notes.append("%s needed %.0f s (slot still taken)" % (self.user, time.time() - t0))
        return ok, s

    def desktop_up(self):
        """Wait for the shell (KDE: splash gone) and, on GNOME, leave the Overview. Returns seconds waited."""
        w, up = self.rig.shell_up()
        if not up:
            raise lib.Fail("%s: desktop shell not up %d s after login" % (self.user, self.a.cap))
        if self.a.box == "gnome":
            self.rig.leave_overview()
        return w

    def state(self):
        return self.rig.state()

    def events(self):
        return self.rig.events()

    def canvas(self):
        return self.rig.canvas_png()

    def px(self, fx, fy):
        return self.rig.px(fx, fy)

    def start_window(self, colour_hex):
        self.rig.start_window(colour_hex)

    def stop(self):
        self.rig.stop()


def journal(box):
    """The slot story of mu1..mu3 in the remotix journal of the box, last 4 minutes."""
    t = box.run("journalctl -u remotix --since '-4min' --no-pager -o cat | grep -E 'rcp +\\[mu[123]\\] (admitted|slot|the client takes|SESSION to|.*already|.*refus|.*dismiss)' | tail -12")[1]
    return " | ".join(l[:140] for l in t.splitlines())[-900:]


def bring_up(a, box, users, tag, cs):
    """Log the users in (all stay attached), wait for their desktops, put a coloured test window in each. Returns notes."""
    notes = []
    for i, u in enumerate(users):
        c = Client(a, u, i, tag)
        cs.append(c)
        t0 = time.time()
        ok, s = c.login(retry_taken=True)
        if not ok:
            raise lib.Fail("login of %s refused or failed: outcome \"%s\" (%s); remotix journal: %s" % (u, s["outcome"].strip(), s["cls"], journal(box)))
        notes.append("%s in %.0fs" % (u, time.time() - t0))
    for c in cs:
        w = c.desktop_up()
        c.start_window("%02x%02x%02x" % COLOURS[c.idx][1])
        notes.append("%s shell %.0fs" % (c.user, w))
    return notes


def check_several(a, box, n, tag):
    users, cs = USERS[:n], []
    try:
        notes = bring_up(a, box, users, tag, cs)
        time.sleep(2)
        # own colour: each canvas must become mostly its own colour and show none of the others
        bad, seen = [], []
        for c in cs:
            end, own, others = time.time() + a.cap, 0, {}
            while time.time() < end:
                png = c.canvas()
                own = frac(png, COLOURS[c.idx][1])
                others = {COLOURS[j][0]: frac(png, COLOURS[j][1]) for j in range(n) if j != c.idx}
                if own >= 0.6 and max(others.values(), default=0) < 0.02:
                    break
                time.sleep(2)
            lib.save_png("multi-%s-%s-%s.png" % (a.box, tag, c.user), png)
            seen.append("%s %s %.0f%%" % (c.user, COLOURS[c.idx][0], 100 * own))
            if own < 0.6 or max(others.values(), default=0) >= 0.02:
                bad.append("%s: ITS OWN %s covers %.1f%%, foreign %s" % (c.user, COLOURS[c.idx][0], 100 * own,
                           ", ".join("%s %.1f%%" % kv for kv in others.items())))
        if bad:
            return FAIL, "%s; %s; journal: %s" % ("; ".join(bad), ", ".join(notes), journal(box))
        # mouse: every user clicks its own point (interleaved); the log of each window holds only that point
        for rnd in range(10):
            for c in cs:
                if not [e for e in c.events() if e["ev"] == "click"]:
                    c.g.move(*c.px(*POINTS[c.idx]))
                    time.sleep(0.2)
                    c.g.click(*c.px(*POINTS[c.idx]))
            time.sleep(1.5)
            if all([e for e in c.events() if e["ev"] == "click"] for c in cs):
                break
        bad = []
        for c in cs:
            ck = [e for e in c.events() if e["ev"] == "click"]
            px, py = POINTS[c.idx]
            if not ck:
                bad.append("%s: its click never reached its own window" % c.user)
            elif any(abs(e["fx"] - px) > 0.08 or abs(e["fy"] - py) > 0.08 for e in ck):
                bad.append("%s: a click not its own arrived (%s)" % (c.user, [(e["fx"], e["fy"]) for e in ck]))
        if bad:
            return FAIL, "mouse: %s; journal: %s" % ("; ".join(bad), journal(box))
        # keyboard: one character per user in turn, then each log must hold exactly that user's word
        for k in range(max(len(WORDS[c.idx]) for c in cs)):
            for c in cs:
                if k < len(WORDS[c.idx]):
                    c.g.type_text(WORDS[c.idx][k])
        end = time.time() + 10
        while time.time() < end and not all(([e for e in c.events() if e["ev"] == "text"] or [{"text": ""}])[-1]["text"] == WORDS[c.idx] for c in cs):
            time.sleep(1)
        got = {c.user: ([e["text"] for e in c.events() if e["ev"] == "text"] or [""])[-1] for c in cs}
        bad = ["%s typed \"%s\" and its window holds \"%s\"" % (c.user, WORDS[c.idx], got[c.user]) for c in cs if got[c.user] != WORDS[c.idx]]
        if bad:
            return FAIL, "keyboard: %s; journal: %s" % ("; ".join(bad), journal(box))
        return PASS, "%d users attached together; canvases %s, no foreign colour (<2%%); clicks and words stayed in own session (%s); %s" % (
            n, ", ".join(seen), ", ".join("%s \"%s\"" % kv for kv in got.items()), ", ".join(notes + sum((c.notes for c in cs), [])))
    finally:
        for c in cs:
            c.stop()


def check_same_user(a, box, tag):
    cs = []
    try:
        A = Client(a, "mu1", 0, tag)
        cs.append(A)
        ok, s = A.login(retry_taken=True)
        if not ok:
            return FAIL, "A (mu1) not admitted: \"%s\"; journal: %s" % (s["outcome"].strip(), journal(box))
        w = A.desktop_up()
        A.start_window("d02020")
        time.sleep(2)
        B = Client(a, "mu1", 1, tag)
        cs.append(B)
        B.rig.open_page()
        ok, sb = B.rig.try_login()
        if ok:
            return FAIL, "B (second browser, same user) GOT IN while A was attached and alive (SPECS 5.1: refused, 0x0F); journal: %s" % journal(box)
        if "taken by another client" not in sb["outcome"]:
            return FAIL, "B not admitted but not with the 0x0F sentence: \"%s\" (%s); journal: %s" % (sb["outcome"].strip(), sb["cls"], journal(box))
        refused = sb["outcome"].strip()
        sa = A.state()
        if not (sa["session"] and sa["cls"] == "good"):
            return FAIL, "B's refusal threw A out: A says \"%s\" (%s); journal: %s" % (sa["outcome"].strip(), sa["cls"], journal(box))
        c0 = len(A.events())
        A.g.click(*A.px(0.5, 0.5))
        time.sleep(0.5)
        A.g.type_text("alfa")
        end = time.time() + 10
        while time.time() < end and ([e["text"] for e in A.events() if e["ev"] == "text"] or [""])[-1] != "alfa":
            time.sleep(1)
        t = ([e["text"] for e in A.events() if e["ev"] == "text"] or [""])[-1]
        if t != "alfa":
            return FAIL, "after B's refusal A is no longer usable: typed \"alfa\", its window holds \"%s\" (%d new events)" % (t, len(A.events()) - c0)
        B.rig.g.close()
        B.rig.g = None
        # A leaves; B (a new browser) must get in and find the same session: the same window, the same text
        A.rig.g.close()
        A.rig.g = None
        B2 = Client(a, "mu1", 2, tag)
        cs.append(B2)
        ok, s2 = B2.login(retry_taken=True)
        if not ok:
            return FAIL, "after A left, mu1 does not get in again: \"%s\"; journal: %s" % (s2["outcome"].strip(), journal(box))
        end, own = time.time() + a.cap, 0
        while time.time() < end:
            png = B2.canvas()
            own = frac(png, (208, 32, 32))
            if own >= 0.6:
                break
            time.sleep(2)
        lib.save_png("multi-%s-%s-mu1-again.png" % (a.box, tag), png)
        if own < 0.6:
            return FAIL, "B got in after A left but does NOT find A's session again: A's red window covers %.1f%%; %s" % (100 * own, " ".join(B2.notes))
        B2.g.click(*B2.px(0.5, 0.5))
        time.sleep(0.5)
        B2.g.type_text("bc")
        end = time.time() + 10
        while time.time() < end and ([e["text"] for e in A.events() if e["ev"] == "text"] or [""])[-1] != "alfabc":
            time.sleep(1)
        t = ([e["text"] for e in A.events() if e["ev"] == "text"] or [""])[-1]
        if t != "alfabc":
            return FAIL, "found the session again but typing there gives \"%s\" instead of \"alfabc\"" % t
        return PASS, "A (shell %.0fs) in; B refused with \"%s\"; A stayed in and typed \"alfa\"; after A left B got in, saw A's red window (%.0f%%), same text, typed on to \"%s\"%s" % (
            w, refused[:60], 100 * own, t, ("; " + "; ".join(B2.notes)) if B2.notes else "")
    finally:
        for c in cs:
            c.stop()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--cap", type=int, default=60, help="seconds allowed for a login or a picture")
    ap.add_argument("--only", default="", help="comma list of checks to run")
    a = ap.parse_args()
    box, stamp = lib.Box(a.box), time.strftime("%H%M%S") + "-" + a.box
    names = ("two-users", "three-users", "same-user")
    res = lib.Results([n for n in names if not a.only or n in a.only.split(",")])
    fns = {"two-users": lambda t: check_several(a, box, 2, t), "three-users": lambda t: check_several(a, box, 3, t),
           "same-user": lambda t: check_same_user(a, box, t)}
    lib.guard(900)
    try:
        # the users are made here (a fresh box has none): never log in with a user that may not exist
        for u in USERS:
            box.ensure_user(u, PASSWORD)
    except Exception as e:  # noqa: BLE001
        res.rest(lib.BLOCKED, lib.tool_error(e))
        return 1
    for n in res.names:
        res.attempt(n, lambda: fns[n]("%s-%s" % (stamp, n)))
    return res.code()


if __name__ == "__main__":
    sys.exit(main())
