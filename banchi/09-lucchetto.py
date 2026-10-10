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
    luc.prendi("09-b76", secondi=900)     # raises if it does not manage
    try:  ...measure...
    finally: luc.molla("09-b76")

Usage (from the command line, to look):
    python3 banchi/09-lucchetto.py stato
    python3 banchi/09-lucchetto.py scassina     # ⛔ by hand only, and it shows
"""
import os, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
POSTO = os.environ.get("LUCCHETTO", "/media/REMOTIX/tmp/.lucchetto-netem.d")


class NonMio(Exception):
    """The lock belongs to someone else, and it has not expired."""


def _rem(comando, tetto=60):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def _root(comando, tetto=60):
    return _rem("printf '%%s\\n' '%s' | sudo -S -p '' %s"
                % (PAROLA_SUDO, comando), tetto)


def stato():
    """(chi, scadenza_epoch) or (None, None) if free."""
    rc, out, _ = _root("cat %s/chi 2>/dev/null || true" % POSTO)
    riga = out.strip()
    if not riga:
        return (None, None)
    pezzi = riga.split(" ", 1)
    try:
        return (pezzi[1] if len(pezzi) > 1 else "?", float(pezzi[0]))
    except ValueError:
        return (riga, 0.0)


def prendi(chi, secondi=900, attesa=0, dillo=True):
    """⛔ `attesa` = how many seconds I am willing to wait for my turn.
       Zero means «now or I stop», which is the default: a bench
       that waits in silence looks like a stuck bench."""
    fine_attesa = time.time() + attesa
    while True:
        # ⭐ The atomic act.  `mkdir` without `-p`: if it already exists, it fails.
        rc, _, _ = _root("mkdir %s 2>/dev/null" % POSTO)
        if rc == 0:
            scad = time.time() + secondi
            _root("bash -c \"printf '%%s %%s\\n' %d '%s' > %s/chi\""
                  % (int(scad), chi, POSTO))
            if dillo:
                print("   OK  netem lock taken by «%s» for %d s"
                      % (chi, secondi))
            return True

        altro, scad = stato()
        if scad is not None and scad > 0 and time.time() > scad:
            # ⛔⛔ BREAKING IT OPEN IS A RACE, AND IT MUST BE DONE BY COMPARING — 25 Aug 2026.
            #
            #   Between the `cat chi` of `stato()` and this `rm -rf` hundreds
            #   of milliseconds of network go by.  In that window **another
            #   runner may already have broken it open and taken it**, and then this
            #   `rm -rf` would delete a **valid and fresh** lock, not
            #   the expired one we had seen.
            #
            #   `[M]` 25 August: a bench printed «BREAKING OPEN «10-e2», expired
            #   1 s ago» forty seconds after a `stato` said «10-e4,
            #   expires in 1802 s».  ⛔ Nobody noticed at the time: two
            #   benches could have measured together, and the two numbers
            #   would have been **both plausible**.
            #
            # ⇒ The file is reread and deleted **only if it is still the same**
            #   byte for byte.  It is a compare-and-delete: the window does not
            #   close entirely (it is not atomic in the kernel), but it goes from
            #   «hundreds of ms» to «the time of one command».
            print("   ⚠   the lock belonged to «%s», expired %d s ago: BREAKING IT OPEN"
                  % (altro, int(time.time() - scad)))
            atteso = "%d %s" % (int(scad), altro)
            # ⚠ The comparison is done by the machine, in one command: bringing it
            #   here would mean reopening the window we are closing.
            cmd = (r"""bash -c 'letto=$(cat "POSTO/chi" 2>/dev/null); """
                   r"""if [ "$letto" = "ATTESO" ]; then rm -rf "POSTO"; exit 0; """
                   r"""else exit 4; fi'""")
            cmd = cmd.replace("POSTO", POSTO).replace("ATTESO", atteso)
            rc, _, _ = _root(cmd)
            if rc == 4:
                print("   ⭐  I do NOT break it open: meanwhile the lock has"
                      " CHANGED — it was someone else's, fresh.")
            continue

        if time.time() >= fine_attesa:
            raise NonMio("the netem on `lo` belongs to «%s» for %d more s: "
                         "I do NOT measure, because a fault that is not mine "
                         "would give a plausible and false number"
                         % (altro, int((scad or 0) - time.time())))
        if dillo:
            print("   --  waiting for my turn (it belongs to «%s»)..." % altro,
                  flush=True)
        time.sleep(5)


def molla(chi, dillo=True):
    altro, _ = stato()
    if altro not in (None, chi):
        print("   ⚠   I do NOT release: the lock now belongs to «%s», not me "
              "(I was broken open)" % altro)
        return False
    _root("rm -rf %s" % POSTO)
    if dillo:
        print("   OK  lock released by «%s»" % chi)
    return True


if __name__ == "__main__":
    passo = sys.argv[1] if len(sys.argv) > 1 else "stato"
    if passo == "stato":
        chi, scad = stato()
        if chi is None:
            print("free")
        else:
            print("held by «%s», expires in %d s" % (chi, int(scad - time.time())))
    elif passo == "scassina":
        _root("rm -rf %s" % POSTO)
        print("broken open by hand")

    else:
        print(__doc__)
