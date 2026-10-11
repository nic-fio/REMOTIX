#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f032 — F-032 THE TERMINAL OPENS THE USER'S SHELL (D-022, phase 16)

    python3 15-f032-la-shell-dell-utente.py --box lxqt --browser firefox [--fault]
    python3 15-f032-la-shell-dell-utente.py --certify

EXPECTED: outside GNOME the session carries `SHELL` = the shell of the user's passwd
        line (read in the environment of the desktop's panel); on GNOME
        `SHELL` is EMPTY on purpose (the `gnome-session` trap, `src/sessione.c`).
        ⭐ On LXQt, where the defect showed: `qterminal` launched in the session
        starts as a child the passwd shell (`bash`), not `sh`/`dash`.

WHY (anomaly A2 of phase 16, D-022): `[M]` 27-28 Sep 2026 the XFCE and LXQt
        sessions were born WITHOUT `SHELL`; qtermwidget fell back on `/bin/sh`.

FAULT: the same judge with the wrong expectation — outside GNOME the expected shell
        `/bin/sh` instead of the passwd one, on GNOME XFCE's judge (which wants
        the full shell): on the facts read in the healthy pass it must give RED.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._load("g1b", os.path.join(S.HERE, "15-g1b-comune.py"))
FUNCTIONS = ("F-032",)
PANEL = {"gnome": "gnome-shell", "kde": "plasmashell", "xfce": "xfce4-panel",
            "lxqt": "lxqt-panel"}


def judge(desktop, shell_passwd, env_shell, child_terminal):
    """(outcome, reason).  `env_shell` None = variable ABSENT; `child_terminal`
    None = not looked at (desktop other than LXQt)."""
    if desktop == "gnome":
        if env_shell == "":
            return S.PASS, "GNOME: SHELL empty, as the cure of the gnome-session trap wants"
        return S.FAIL, "GNOME: SHELL=%r, expected EMPTY (gnome-session trap)" % (env_shell,)
    if env_shell != shell_passwd:
        return S.FAIL, "the session's SHELL %r, passwd says %r" % (env_shell, shell_passwd)
    if child_terminal is not None and child_terminal != os.path.basename(shell_passwd):
        return S.FAIL, "qterminal opened %r, passwd says %r" % (child_terminal, shell_passwd)
    return S.PASS, "SHELL=%s%s" % (shell_passwd, "" if child_terminal is None
                                   else ", qterminal opens %s" % child_terminal)


def certify():
    cases = [
        (("lxqt", "/bin/bash", "/bin/bash", "bash"), S.PASS),
        (("lxqt", "/bin/bash", None, "sh"), S.FAIL),
        (("lxqt", "/bin/bash", "/bin/bash", "dash"), S.FAIL),
        (("xfce", "/bin/bash", "/bin/bash", None), S.PASS),
        (("kde", "/bin/bash", "", None), S.FAIL),
        (("gnome", "/bin/bash", "", None), S.PASS),
        (("gnome", "/bin/bash", "/bin/bash", None), S.FAIL),
    ]
    ko = 0
    for a, expected in cases:
        e, r = judge(*a)
        ok = e == expected
        ko += not ok
        print("  %s %s → %s (%s)" % ("✅" if ok else "⛔", a, e, r))
    print("CERTIFICA %s — %d of %d" % ("PASS" if not ko else "FAIL", len(cases) - ko, len(cases)))
    return 1 if ko else 0


def body(o, E):
    with S.Session(o, "032", E) as s:
        ok, why = s.enter()
        if not ok:
            raise S.Blocked("the session was not born: %s" % why)
        c, t = s.sc.inside("getent passwd %s | cut -d: -f7" % s.chi, 30)
        shell = t.strip()
        if c != 0 or not shell:
            raise S.Blocked("the tenant's passwd line cannot be read: %s" % t[-200:])
        process = PANEL[o.box]
        env = {}
        for _ in range(30):                     # the panel is born a few seconds later
            env = G1B.environment_of(s, process)
            if env:
                break
            time.sleep(1)
        if not env:
            raise S.Blocked("no «%s» process of the tenant to read" % process)
        env_shell = env.get("SHELL")
        child = None
        if o.box == "lxqt":
            # ⛔ as from the MENU: qterminal with the panel's environment (the process from which
            #    the user launches it), not with that of `in_session` — which is the bench's
            #    and would have measured the bench (the first version of this test did so).
            s.sc.inside("p=$(pgrep -u %(c)s -x lxqt-panel | head -1); [ -n \"$p\" ] || exit 4; "
                        "setsid runuser -u %(c)s -- xargs -0 -a /proc/$p/environ "
                        "sh -c 'exec env -i \"$@\" qterminal' sh </dev/null >/dev/null 2>&1 &"
                        % {"c": s.chi}, 30)
            for _ in range(20):
                time.sleep(1)
                c, t = s.sc.inside("p=$(pgrep -u %s -x qterminal | head -1); [ -n \"$p\" ] || exit 4; "
                                   "for k in $(pgrep -P $p); do ps -o comm= -p $k; done" % s.chi, 30)
                names = [x.strip() for x in t.splitlines() if x.strip()]
                if c == 0 and names:
                    child = names[0]
                    break
            s.photo("qterminal")
            s.sc.inside("pkill -u %s -x qterminal" % s.chi, 30)
            if child is None:
                raise S.Blocked("qterminal did not open any child process in 20 s")
        outcome, rationale = judge(o.box, shell, env_shell, child)
        E.put("F-032", outcome, rationale if outcome != S.PASS else "",
                expected="the session's SHELL = passwd (%s) outside GNOME, empty on GNOME; "
                       "on LXQt qterminal opens %s" % (shell, os.path.basename(shell)),
                observed=rationale, evidence=[s.save_console()])
        if o.fault:
            # the fault: the judge with the wrong expectation — /bin/sh outside GNOME, and on
            # GNOME another desktop's judge (which wants the shell, not the empty one)
            if o.box == "gnome":
                eg, rg = judge("xfce", shell, env_shell, child)
            else:
                eg, rg = judge(o.box, "/bin/sh", env_shell, child)
            E.fault("F-032", eg == S.FAIL,
                     "with the wrong judge: %s — %s" % (eg, rg),
                     expected="red", observed=eg)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
