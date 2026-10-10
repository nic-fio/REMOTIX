#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-lucchetto — THE `netem` ON `lo` IS ONLY ONE, AND IT MUST BE OWNED IN TURN.

⛔⭐ WHY IT EXISTS.  The qdisc of `lo` is set with
    `tc qdisc replace dev lo root ...` and removed with `tc qdisc del dev lo
    root`: they are commands acting on the **root**, that is on the WHOLE
    interface.  Two benches breaking the network together do not share the
    work: **the second deletes the first one's root**, and the first keeps
    measuring believing it has a fault that is no longer there.
    ⚠ And it does not give red: it gives a plausible number.  It is exactly the wound of
    `LEZIONI.md` §1.26.

⭐ So: whoever wants to break `lo` takes ownership, and whoever does not manage to
   **waits or stops**, does not go ahead anyway.

⛔ OWNERSHIP IS TAKEN WITH `mkdir`, not with a file.  `mkdir` is atomic
   even over ssh: either it succeeds (and it is me) or it fails (and it is not me).  A file
   written with `>` always succeeds, even with two hands, and it is not a lock.

⭐ AND EVERY OWNERSHIP HAS AN EXPIRY written inside.  A bench that dies with the
   lock in hand would block all the others until tomorrow; with the
   expiry, the next one to arrive reads it, sees it has passed, and **breaks it open
   declaring so**.  ⚠ Breaking it open silently would be worse than the block.

Usage (from Python):
    import importlib.util, os
    luc = ...            # load this file
    luc.take("09-b76", seconds=900)     # raises if it does not manage
    try:  ...measure...
    finally: luc.release("09-b76")

Usage (from the command line, to look):
    python3 banchi/09-lucchetto.py state
    python3 banchi/09-lucchetto.py scassina     # ⛔ by hand only, and it shows
"""
import os, subprocess, sys, time

MACHINE = os.environ.get("MACHINE", "nicfio@192.168.0.2")
SUDO_PASSWORD = os.environ.get("SUDO_PASSWORD", "nicfio")
SLOT = os.environ.get("LOCK", "/media/REMOTIX/tmp/.lucchetto-netem.d")


class NotMine(Exception):
    """The lock belongs to someone else, and it has not expired."""


def _rem(command, ceiling=60):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACHINE, command],
                       capture_output=True, timeout=ceiling)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def _root(command, ceiling=60):
    return _rem("printf '%%s\\n' '%s' | sudo -S -p '' %s"
                % (SUDO_PASSWORD, command), ceiling)


def state():
    """(chi, scadenza_epoch) or (None, None) if free."""
    rc, out, _ = _root("cat %s/chi 2>/dev/null || true" % SLOT)
    row = out.strip()
    if not row:
        return (None, None)
    pieces = row.split(" ", 1)
    try:
        return (pieces[1] if len(pieces) > 1 else "?", float(pieces[0]))
    except ValueError:
        return (row, 0.0)


def take(chi, seconds=900, wait=0, report_it=True):
    """⛔ `wait` = how many seconds I am willing to wait for my turn.
       Zero means «now or I stop», which is the default: a bench
       that waits in silence looks like a stuck bench."""
    wait_deadline = time.time() + wait
    while True:
        # ⭐ The atomic act.  `mkdir` without `-p`: if it already exists, it fails.
        rc, _, _ = _root("mkdir %s 2>/dev/null" % SLOT)
        if rc == 0:
            exp = time.time() + seconds
            _root("bash -c \"printf '%%s %%s\\n' %d '%s' > %s/chi\""
                  % (int(exp), chi, SLOT))
            if report_it:
                print("   OK  netem lock taken by «%s» for %d s"
                      % (chi, seconds))
            return True

        other_one, exp = state()
        if exp is not None and exp > 0 and time.time() > exp:
            # ⛔⛔ BREAKING IT OPEN IS A RACE, AND IT MUST BE DONE BY COMPARING — 25 Aug 2026.
            #
            #   Between the `cat chi` of `state()` and this `rm -rf` hundreds
            #   of milliseconds of network go by.  In that window **another
            #   runner may already have broken it open and taken it**, and then this
            #   `rm -rf` would delete a **valid and fresh** lock, not
            #   the expired one we had seen.
            #
            #   `[M]` 25 August: a bench printed «BREAKING OPEN «10-e2», expired
            #   1 s ago» forty seconds after a `state` said «10-e4,
            #   expires in 1802 s».  ⛔ Nobody noticed at the time: two
            #   benches could have measured together, and the two numbers
            #   would have been **both plausible**.
            #
            # ⇒ The file is reread and deleted **only if it is still the same**
            #   byte for byte.  It is a compare-and-delete: the window does not
            #   close entirely (it is not atomic in the kernel), but it goes from
            #   «hundreds of ms» to «the time of one command».
            print("   ⚠   the lock belonged to «%s», expired %d s ago: BREAKING IT OPEN"
                  % (other_one, int(time.time() - exp)))
            expected_val = "%d %s" % (int(exp), other_one)
            # ⚠ The comparison is done by the machine, in one command: bringing it
            #   here would mean reopening the window we are closing.
            cmd = (r"""bash -c 'read=$(cat "SLOT/chi" 2>/dev/null); """
                   r"""if [ "$read" = "EXPECTED" ]; then rm -rf "SLOT"; exit 0; """
                   r"""else exit 4; fi'""")
            cmd = cmd.replace("SLOT", SLOT).replace("EXPECTED", expected_val)
            rc, _, _ = _root(cmd)
            if rc == 4:
                print("   ⭐  I do NOT break it open: meanwhile the lock has"
                      " CHANGED — it was someone else's, fresh.")
            continue

        if time.time() >= wait_deadline:
            raise NotMine("the netem on `lo` belongs to «%s» for %d more s: "
                         "I do NOT measure, because a fault that is not mine "
                         "would give a plausible and false number"
                         % (other_one, int((exp or 0) - time.time())))
        if report_it:
            print("   --  waiting for my turn (it belongs to «%s»)..." % other_one,
                  flush=True)
        time.sleep(5)


def release(chi, report_it=True):
    other_one, _ = state()
    if other_one not in (None, chi):
        print("   ⚠   I do NOT release: the lock now belongs to «%s», not me "
              "(I was broken open)" % other_one)
        return False
    _root("rm -rf %s" % SLOT)
    if report_it:
        print("   OK  lock released by «%s»" % chi)
    return True


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "state"
    if step == "state":
        chi, exp = state()
        if chi is None:
            print("free")
        else:
            print("held by «%s», expires in %d s" % (chi, int(exp - time.time())))
    elif step == "scassina":
        _root("rm -rf %s" % SLOT)
        print("broken open by hand")

    else:
        print(__doc__)
