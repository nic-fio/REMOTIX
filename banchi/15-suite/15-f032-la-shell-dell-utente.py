#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f032 — F-032 IL TERMINALE APRE LA SHELL DELL'UTENTE (D-022, fase 16)

    python3 15-f032-la-shell-dell-utente.py --scatola lxqt --browser firefox [--guasto]
    python3 15-f032-la-shell-dell-utente.py --certifica

ATTESO: fuori da GNOME la sessione porta `SHELL` = la shell della riga di passwd
        dell'utente (letta nell'ambiente del pannello del desktop); su GNOME
        `SHELL` e' VUOTA di proposito (la trappola di `gnome-session`, `src/sessione.c`).
        ⭐ Su LXQt, dove il difetto si vedeva: `qterminal` lanciato nella sessione
        fa partire come figlio la shell di passwd (`bash`), non `sh`/`dash`.

PERCHE' (anomalia A2 della fase 16, D-022): `[M]` 27-28 set 2026 le sessioni
        XFCE e LXQt nascevano SENZA `SHELL`; qtermwidget ripiegava su `/bin/sh`.

GUASTO: lo stesso giudice con l'atteso sbagliato — fuori da GNOME la shell attesa
        `/bin/sh` al posto di quella di passwd, su GNOME il giudice di XFCE (che vuole
        la shell piena): sui fatti letti nella passata sana deve dare ROSSO.
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
    """(esito, ragione).  `amb_shell` None = variabile ASSENTE; `figlio_terminale`
    None = non guardato (desktop diverso da LXQt)."""
    if desktop == "gnome":
        if amb_shell == "":
            return S.PASS, "GNOME: SHELL vuota, come vuole la cura della trappola di gnome-session"
        return S.FAIL, "GNOME: SHELL=%r, attesa VUOTA (trappola di gnome-session)" % (amb_shell,)
    if amb_shell != shell_passwd:
        return S.FAIL, "SHELL della sessione %r, passwd dice %r" % (amb_shell, shell_passwd)
    if figlio_terminale is not None and figlio_terminale != os.path.basename(shell_passwd):
        return S.FAIL, "qterminal ha aperto %r, passwd dice %r" % (figlio_terminale, shell_passwd)
    return S.PASS, "SHELL=%s%s" % (shell_passwd, "" if figlio_terminale is None
                                   else ", qterminal apre %s" % figlio_terminale)


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
    print("CERTIFICA %s — %d su %d" % ("PASS" if not ko else "FAIL", len(casi) - ko, len(casi)))
    return 1 if ko else 0


def corpo(o, E):
    with S.Sessione(o, "032", E) as s:
        ok, perche = s.entra()
        if not ok:
            raise S.Bloccata("la sessione non e' nata: %s" % perche)
        c, t = s.sc.dentro("getent passwd %s | cut -d: -f7" % s.chi, 30)
        shell = t.strip()
        if c != 0 or not shell:
            raise S.Bloccata("la riga di passwd dell'inquilino non si legge: %s" % t[-200:])
        processo = PANNELLO[o.scatola]
        amb = {}
        for _ in range(30):                     # il pannello nasce qualche secondo dopo
            amb = G1B.ambiente_di(s, processo)
            if amb:
                break
            time.sleep(1)
        if not amb:
            raise S.Bloccata("nessun processo «%s» dell'inquilino da leggere" % processo)
        amb_shell = amb.get("SHELL")
        figlio = None
        if o.scatola == "lxqt":
            # ⛔ come dal MENU: qterminal con l'ambiente del pannello (il processo da cui
            #    l'utente lo lancia), non con quello di `nella_sessione` — che e' del banco
            #    e avrebbe misurato il banco (la prima versione di questa prova lo faceva).
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
                raise S.Bloccata("qterminal non ha aperto nessun processo figlio in 20 s")
        esito, ragione = giudica(o.scatola, shell, amb_shell, figlio)
        E.metti("F-032", esito, ragione if esito != S.PASS else "",
                atteso="SHELL della sessione = passwd (%s) fuori da GNOME, vuota su GNOME; "
                       "su LXQt qterminal apre %s" % (shell, os.path.basename(shell)),
                osservato=ragione, evidenze=[s.salva_console()])
        if o.guasto:
            # il guasto: il giudice con l'atteso sbagliato — /bin/sh fuori da GNOME, e su
            # GNOME il giudice di un altro desktop (che vuole la shell, non la vuota)
            if o.scatola == "gnome":
                eg, rg = giudica("xfce", shell, amb_shell, figlio)
            else:
                eg, rg = giudica(o.scatola, "/bin/sh", amb_shell, figlio)
            E.guasto("F-032", eg == S.FAIL,
                     "col giudice sbagliato: %s — %s" % (eg, rg),
                     atteso="rosso", osservato=eg)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
