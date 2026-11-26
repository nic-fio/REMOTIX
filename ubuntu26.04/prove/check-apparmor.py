#!/usr/bin/env python3
"""check-apparmor - the AppArmor profile of REMOTIX (remotix_network) covers everything the network side did since a given moment.

    RX_BANCO=vm python3 check-apparmor.py --box xfce|lxqt|gnome|kde [--since <epoch seconds of the box>]

Looks in the kernel journal of the box (and in /var/log/audit/audit.log if auditd is there) for lines with apparmor="DENIED" or apparmor="ALLOWED"
whose profile is remotix_network (or a child of it). The package installs the profile in COMPLAIN mode: what it does not cover is NOT blocked and
shows as ALLOWED; in enforce it would show as DENIED. Both are FAIL (the profile does not cover what the program did), and the line says which.
Lines of other programs' profiles are not looked at. If the log cannot be read: BLOCKED («AppArmor NOT checked»), never PASS.
Without --since: the whole current boot of the box. all.sh runs it last, with --since = the start of the round."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

NAME = "profile-coverage"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--since", default="0", help="epoch seconds (of the box clock); default 0 = the whole current boot")
    a = ap.parse_args()
    res = lib.Results([NAME])
    try:
        since = int(a.since)
        if since < 0:
            raise ValueError
    except ValueError:
        res.say(lib.BLOCKED, NAME, "AppArmor NOT checked: --since is not an epoch in seconds (\"%s\")" % a.since)
        return 1
    try:
        ok, lines, why = lib.Box(a.box).apparmor(since)
    except Exception as e:  # noqa: BLE001 - a broken tool step is BLOCKED, never a PASS
        res.say(lib.BLOCKED, NAME, "AppArmor NOT checked: " + lib.tool_error(e))
        return 1
    if not ok:
        res.say(lib.BLOCKED, NAME, "AppArmor NOT checked: " + why)
    elif lines:
        res.say(lib.FAIL, NAME, "AppArmor line(s) of the remotix_network profile since @%d: %s" % (since, lib.Box.apparmor_summary(lines)))
    else:
        res.say(lib.PASS, NAME, "no apparmor=\"ALLOWED\" or \"DENIED\" line of the remotix_network profile since @%d" % since)
    return res.code()


if __name__ == "__main__":
    sys.exit(main())
