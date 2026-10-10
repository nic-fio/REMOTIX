#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g3-comune — the common helper of the three tests of group G3 (F-005, F-006,
F-008): the meshes C21, C22, C23 of phase 14 inside the suite.

⛔ The meshes are IMPORTED, not copied: their observation and
   judgment functions (`C21.osserva`, `C22.prova_browser`, `C22.scansiona`,
   `C23.manda`, `C23.fotografa_e_leggi`, …) run as they are.  Only one
   thing must change: `osserva` and `prova_browser` start the browser BY THEMSELVES
   (`VERI.accendi_guida`) and close it at the end; in the suite the browser and
   the tenant are held by `suite.Sessione`.  ⇒ `guida_prestata()` lends the
   mesh the session's browser, with a `chiudi()` that does not close: the
   session stays alive for the fault pass and for the extra observations.
"""
import contextlib
import glob
import importlib.util as _iu
import os
import random
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _parola_sudo():
    """The server's sudo password: from REMOTIX_PAROLA_SUDO, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_PAROLA_SUDO")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"
sys.path.insert(0, QUI)
import suite as S                                                     # noqa: E402

SCATOLE = os.path.join(S.BANCHI, "11-scatole")


def pazienza_ssh(scatola_cls):
    """⚠ `[M]` 24 Sep 2026, 10 agents on the server: `Scatola.dentro` goes through an
    ssh from the server to itself, and sshd (MaxStartups 10:30:100) randomly closes
    the not yet authenticated connections («Connection closed by … port
    22»).  The command in that case did NOT start (it closes before
    the login) ⇒ it can be repeated.  It is retried up to 12 times (about two minutes)."""
    if getattr(scatola_cls, "_g3_pazienza", False):
        return
    originale = scatola_cls.dentro

    def dentro(self, riga, secondi=90):
        for i in range(12):
            c, t = originale(self, riga, secondi)
            if c is not None or "Connection closed by" not in (t or "") \
                    and "Connection reset" not in (t or ""):
                return c, t
            time.sleep(1 + 2 * min(i, 8) + 2 * random.random())
        return c, t
    scatola_cls.dentro = dentro
    scatola_cls._g3_pazienza = True


pazienza_ssh(S.C20V.Scatola)


def carica_maglia(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(SCATOLE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    pazienza_ssh(m.C20V.Scatola)
    return m


class Prestito:
    """The session's browser, lent to a mesh: everything goes through, except
    `chiudi()` (the Sessione closes it, on exit)."""

    def __init__(self, g):
        self.__dict__["_g"] = g

    def chiudi(self):
        return None

    def __getattr__(self, nome):
        return getattr(self.__dict__["_g"], nome)


@contextlib.contextmanager
def guida_prestata(veri, g):
    """Inside the block `veri.accendi_guida(...)` returns the session's browser `g`
    (on loan).  ⚠ `veri` is the `12-client-veri` module THAT THE
    MESH USES: every loaded mesh carries its own."""
    vecchia = veri.accendi_guida
    veri.accendi_guida = lambda nome, o: Prestito(g)
    try:
        yield
    finally:
        veri.accendi_guida = vecchia


def cura_della_cache(sc, chi):
    """⭐ The REAL `~/.cache` for the tenant — the cure of `src/provisiona.sh`, with
    the lines of `11-c8….applica_la_cura` (which runs INSIDE the box: here it is
    sent with `sc.dentro`), and the write test of `sa_scrivere_nella_cache`.

    `[M]` 24 Sep 2026, rete11-gnome: `/etc/skel/.cache -> /tmp` (the user's
    choice, `DECISIONI.md` §4.6-undecies, reproduced in the box) ⇒ the
    first tenant that opens `firefox-esr` takes `/tmp/mozilla` with mode 0700
    and all the others see «Your Firefox profile cannot be loaded».  C21-C23
    did not do it: in phase 14 they ran alone.  With ten agents on the
    same box the test window is no longer born ⇒ bench BLOCKED."""
    c = "/home/%s/.cache" % chi
    cod, t = sc.dentro(
        "[ -L %s ] && rm -f %s; mkdir -p %s; chown %s:%s %s; chmod 700 %s; "
        "su -s /bin/sh -c 'mkdir -p ~/.cache/mozilla/.prova-g3 && "
        "rmdir ~/.cache/mozilla/.prova-g3' %s && echo scrive"
        % (c, c, c, chi, chi, c, c, chi), 60)
    return cod == 0 and "scrive" in (t or ""), (t or "")[-200:]


def prepara_o(o, s):
    """The fields the meshes read from `o` and that `suite.argomenti` does not set;
    ⚠ the real `~/.cache` for the tenant is now given by `suite.Sessione` (25 Sep):
    `cura_della_cache` remains only as a diagnosis, it is no longer called."""
    o.parola = s.parola
    o.utente = s.chi
    o.salva = o.evidenze or ""
    if not hasattr(o, "attesa_finestra"):
        o.attesa_finestra = 60


def evidenze_nuove(o, prima):
    """The files that appeared in the evidence after `prima` (a set of paths)."""
    if not o.evidenze:
        return []
    return sorted(set(glob.glob(os.path.join(o.evidenze, "*"))) - set(prima))


def evidenze_ora(o):
    return set(glob.glob(os.path.join(o.evidenze, "*"))) if o.evidenze else set()


DA_ESITO_GUASTO = {S.VERDE: True, S.ROSSO: False, S.CIECO: None}


def argomenti_g3(a):
    # ⚠ `[M]` 25 Sep: with Chrome a photo at scale 1 in 4K (+ the search for the
    #   cyan) costs 10-20 s under load: in 60 s two STILL photos in a row do not
    #   always fit ⇒ BLOCKED «the window is not seen» with the window there.
    a.add_argument("--attesa-finestra", type=int, default=150,
                   help="how long to wait for the test window to appear still")


# ─────────────────────────────────────────────────────────────────────────────
#  IS THE SCENE STILL ALIVE?  (so as not to blame the product for the server)
# ─────────────────────────────────────────────────────────────────────────────
# `[M]` 24 Sep 2026, evening: ten agents on the server, 31 GB, no swap ⇒
#   the server's OOM-killer killed processes; in the same minute the
#   `firefox-esr` windows of two scenes vanished (F-006 and F-008, gnome).  A
#   red case with the scene dead is NOT a red of the product: it is BLOCKED.
def scena_viva(sc, chi):
    c, t = sc.dentro("pgrep -u %s -f '[f]irefox-esr' >/dev/null && echo viva || echo morta"
                     % chi, 30)
    return "viva" in (t or "")


def uccisi_dal_server():
    """The «Killed process» lines of the kernel log of the server (where the
    test runs): they are compared before and after.  [] if they cannot be read."""
    import subprocess
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "dmesg"], input=_parola_sudo(),
                           capture_output=True, text=True, timeout=20)
        return [x for x in r.stdout.splitlines() if "Killed process" in x]
    except Exception:                            # noqa: BLE001
        return []


def nuovi_uccisi(prima):
    dopo = uccisi_dal_server()
    return dopo[len(prima):] if len(dopo) >= len(prima) else dopo


def spiega_cieco(prima_oom):
    """One more sentence for a BLOCKED: did the OOM-killer work in the meantime?"""
    n = nuovi_uccisi(prima_oom)
    if not n:
        return ""
    return (" — ⚠ during the test the SERVER's OOM-killer killed %d processes (%s)"
            % (len(n), "; ".join(x.split("Killed process")[-1].split(" total-vm")[0].strip()
                                 for x in n[-3:])))


def traccia_la_ricerca(c21):
    """Diagnosis: every outcome of `trova_finestra` printed (cyan rectangle and
    right edge), to understand why two photos in a row do not come back still."""
    if getattr(c21, "_g3_traccia", False):
        return
    orig = c21.trova_finestra

    def trova(*a, **k):
        t0 = time.time()
        f, perche = orig(*a, **k)
        print("      [search %.1fs] %s" % (time.time() - t0, ("cyan %s right %s" % (
            f["ciano"], f["destro"])) if f else perche), flush=True)
        return f, perche
    c21.trova_finestra = trova
    c21._g3_traccia = True
