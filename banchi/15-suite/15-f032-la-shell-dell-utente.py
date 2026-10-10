#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f032 — F-032 THE TERMINAL OPENS THE USER'S SHELL (D-022, phase 16)

    python3 15-f032-la-shell-dell-utente.py --scatola lxqt --browser firefox [--guasto]
    python3 15-f032-la-shell-dell-utente.py --certifica

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

G1B = S._carica("g1b", os.path.join(S.QUI, "15-g1b-comune.py"))
FUNZIONI = ("F-032",)
PANNELLO = {"gnome": "gnome-shell", "kde": "plasmashell", "xfce": "xfce4-panel",
            "lxqt": "lxqt-panel"}


def giudica(desktop, shell_passwd, amb_shell, figlio_terminale):
    """(outcome, reason).  `amb_shell` None = variable ABSENT; `figlio_terminale`
    None = not looked at (desktop other than LXQt)."""
    if desktop == "gnome":
        if amb_shell == "":
            return S.PASS, "GNOME: SHELL empty, as the cure of the gnome-session trap wants"
        return S.FAIL, "GNOME: SHELL=%r, expected EMPTY (gnome-session trap)" % (amb_shell,)
    if amb_shell != shell_passwd:
        return S.FAIL, "the session's SHELL %r, passwd says %r" % (amb_shell, shell_passwd)
    if figlio_terminale is not None and figlio_terminale != os.path.basename(shell_passwd):
        return S.FAIL, "qterminal opened %r, passwd says %r" % (figlio_terminale, shell_passwd)
    return S.PASS, "SHELL=%s%s" % (shell_passwd, "" if figlio_terminale is None
                                   else ", qterminal opens %s" % figlio_terminale)


def certifica():
    casi = [
        (("lxqt", "/bin/bash", "/bin/bash", "bash"), S.PASS),
        (("lxqt", "/bin/bash", None, "sh"), S.FAIL),
        (("lxqt", "/bin/bash", "/bin/bash", "dash"), S.FAIL),
        (("xfce", "/bin/bash", "/bin/bash", None), S.PASS),
        (("kde", "/bin/bash", "", None), S.FAIL),
        (("gnome", "/bin/bash", "", None), S.PASS),
        (("gnome", "/bin/bash", "/bin/bash", None), S.FAIL),
    ]
    ko = 0
    for a, atteso in casi:
        e, r = giudica(*a)
        ok = e == atteso
        ko += not ok
        print("  %s %s → %s (%s)" % ("✅" if ok else "⛔", a, e, r))
    print("CERTIFICA %s — %d of %d" % ("PASS" if not ko else "FAIL", len(casi) - ko, len(casi)))
    return 1 if ko else 0


def corpo(o, E):
    with S.Sessione(o, "032", E) as s:
        ok, perche = s.entra()
        if not ok:
            raise S.Bloccata("the session was not born: %s" % perche)
        c, t = s.sc.dentro("getent passwd %s | cut -d: -f7" % s.chi, 30)
        shell = t.strip()
        if c != 0 or not shell:
            raise S.Bloccata("the tenant's passwd line cannot be read: %s" % t[-200:])
        processo = PANNELLO[o.scatola]
        amb = {}
        for _ in range(30):                     # the panel is born a few seconds later
            amb = G1B.ambiente_di(s, processo)
            if amb:
                break
            time.sleep(1)
        if not amb:
            raise S.Bloccata("no «%s» process of the tenant to read" % processo)
        amb_shell = amb.get("SHELL")
        figlio = None
        if o.scatola == "lxqt":
            # ⛔ as from the MENU: qterminal with the panel's environment (the process from which
            #    the user launches it), not with that of `nella_sessione` — which is the bench's
            #    and would have measured the bench (the first version of this test did so).
            s.sc.dentro("p=$(pgrep -u %(c)s -x lxqt-panel | head -1); [ -n \"$p\" ] || exit 4; "
                        "setsid runuser -u %(c)s -- xargs -0 -a /proc/$p/environ "
                        "sh -c 'exec env -i \"$@\" qterminal' sh </dev/null >/dev/null 2>&1 &"
                        % {"c": s.chi}, 30)
            for _ in range(20):
                time.sleep(1)
                c, t = s.sc.dentro("p=$(pgrep -u %s -x qterminal | head -1); [ -n \"$p\" ] || exit 4; "
                                   "for k in $(pgrep -P $p); do ps -o comm= -p $k; done" % s.chi, 30)
                nomi = [x.strip() for x in t.splitlines() if x.strip()]
                if c == 0 and nomi:
                    figlio = nomi[0]
                    break
            s.foto("qterminal")
            s.sc.dentro("pkill -u %s -x qterminal" % s.chi, 30)
            if figlio is None:
                raise S.Bloccata("qterminal did not open any child process in 20 s")
        esito, ragione = giudica(o.scatola, shell, amb_shell, figlio)
        E.metti("F-032", esito, ragione if esito != S.PASS else "",
                atteso="the session's SHELL = passwd (%s) outside GNOME, empty on GNOME; "
                       "on LXQt qterminal opens %s" % (shell, os.path.basename(shell)),
                osservato=ragione, evidenze=[s.salva_console()])
        if o.guasto:
            # the fault: the judge with the wrong expectation — /bin/sh outside GNOME, and on
            # GNOME another desktop's judge (which wants the shell, not the empty one)
            if o.scatola == "gnome":
                eg, rg = giudica("xfce", shell, amb_shell, figlio)
            else:
                eg, rg = giudica(o.scatola, "/bin/sh", amb_shell, figlio)
            E.guasto("F-032", eg == S.FAIL,
                     "with the wrong judge: %s — %s" % (eg, rg),
                     atteso="red", osservato=eg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
