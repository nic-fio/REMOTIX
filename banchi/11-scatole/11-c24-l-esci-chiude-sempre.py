#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c24 — ⭐⭐ «"LOG OUT" CLOSES THE SESSION, ALWAYS — not 19 times out of 20»
===========================================================================

    python3 11-c24-l-esci-chiude-sempre.py --porta 8514              # 10 runs
    python3 11-c24-l-esci-chiude-sempre.py --porta 8514 --giri 20
    python3 11-c24-l-esci-chiude-sempre.py --porta 8514 --rientra-subito
    python3 11-c24-l-esci-chiude-sempre.py --certifica

    what must be true         : the user chooses «Log out» from the desktop menu
                                ⇒ the session ENDS and ⛔ IS NOT REBORN by itself
                                — every time, whatever the moment in which
                                the user chooses it
    where it starts from      : for every run a NEW tenant (`c24u<n>`),
                                the Python client watching, the birth made
                                by the child, K seconds of session, and the
                                «Log out» gesture of the MENU (C20's table
                                `DESKTOP_E_GESTO`, ⛔ imported and not copied)
    what it looks at          : the PRODUCT'S LOG and the CLIENT, for T
                                seconds after the gesture
      F  over      the product declares the session over (one of C20's two
                   forms, `RIGHE_FINITA`) or the client is dismissed
                   with 0x10
      N  birth     ⛔ for THIS tenant, after the gesture, «I AM
                   MAKING IT BE BORN» does NOT appear, nor a second «negotiated format»
    how I know it can give red: `--rientra-subito` (see the fault
                                box): after «Log out» a client is reattached
                                for the same tenant ⇒ a session IS really BORN
                                inside the window of T seconds, and the
                                mesh MUST say red

---------------------------------------------------------------------------
⛔⛔ THE DEFECT THIS MESH WATCHES — 24 September 2026
---------------------------------------------------------------------------

On LXQt «Log out» made the session BE REBORN instead of closing it.  `[M]` 16
times out of 20 with yesterday's binary, **1 out of 20** with this morning's: it is a
RACE, and the outcome depends on the moment in which the user chooses «Log out».

`[R]` `src/figlio.c`, «IT WAS THERE AND NOW IT IS NOT ANY MORE»: the child tells a
session that was NEVER there (⇒ it makes it be born) from one that was there and the user
closed (⇒ ⛔ it does NOT redo it, it sends away whoever watches with 0x10).  The distinction
lies entirely in `vista_viva`: if the session dies BEFORE the child has
seen it alive, for it «it was never there», and it writes «I AM MAKING IT BE BORN».
⇒ It is a window of time, and the user's gesture can fall into it.

⛔⛔ AND WHY C20 WAS NOT ENOUGH: C20 does «Log out» **ONCE** per box, always
    at the same moment.  A race of 1 in 20 passes it by 19 times out of 20
    ⇒ the net was green with the defect inside.  ⭐ Here the runs are N (default
    10) and the moment of the gesture CHANGES at every run (`ATTESE_K`: 8, 10, 12, 15 s
    in rotation), because the window of the race is in TIME.
⚠ 10 runs are not a guarantee against a race of 1 in 20 (they catch it with
  probability ~40%): they are the net's time ceiling (5 minutes per
  box).  ⭐ For a real hunt: `--giri 40`.  And YESTERDAY's race (16 out of 20)
  10 runs catch with practical certainty.

---------------------------------------------------------------------------
⛔⛔ THE INJECTED FAULT — and why it is NOT «killing the compositor»
---------------------------------------------------------------------------

The first idea was: instead of the gesture, SIGKILL to the tenant's compositor
⇒ the stage falls without the user having closed it ⇒ «it must be reborn».
⛔ **It is wrong, and it is the product that says so.**  `src/figlio.c`, in the same
box «IT WAS THERE AND NOW IT IS NOT ANY MORE»:

    «⚠ And the same holds if the compositor DIED by itself: from our side
     it is indistinguishable from a logout, and the right behaviour is the same
     — telling whoever watches instead of making a desktop reappear that the user
     had closed.»

⇒ With the compositor killed the HEALTHY product does **not** get reborn: the mesh would say
  green, and the injected fault «not seen» would accuse the mesh of a
  behaviour that is a decision of the product.  A fault that the healthy
  product cannot produce proves nothing.

⭐ The fault chosen: `--rientra-subito`.  The run is identical (real «Log out»
  gesture, same wait K), and as soon as the product has declared the session
  over the mesh REATTACHES a second client for the same tenant.  For
  the product it is a new attach ⇒ it makes a session be born (and rightly so:
  `DECISIONI.md` §4.1-quater, «the next one is born at the next attach») ⇒ in the
  log, for that tenant and inside the window of T seconds, there appear
  **exactly the lines of the defect**: «I AM MAKING IT BE BORN» and a second
  «negotiated format».
  ⚠ What it proves and what not, said clearly: it proves that the judge READS the
    rebirth after «Log out» and calls it red.  It does not prove it can tell
    a spontaneous rebirth from a requested one — ⭐ and it must not know: in the
    healthy run the mesh NEVER reattaches inside the window, ⇒ every birth that
    appears there is the product's.
  ⚠ And it recompiles nothing: the real defect lies in a variable of the child, and
    from outside it cannot be put back.

---------------------------------------------------------------------------
⚠ THE NUMBERS, and where they come from
---------------------------------------------------------------------------

  · **T = 10 s** of guard after the gesture.  `[M]` 24 Sep 2026 on rete11-lxqt
    (binary 6e29da97, without the cure): the rebirth appears within a few
    seconds of the gesture — the child reads the session state at every
    stage attempt, and at the first one that finds it DEAD it makes it be born.
    ⚠ To be measured again if the cadence of the attempts changes.
  · **birth ceiling 60 s**: it is the start of every run, and if it is not born the
    mesh has nothing to judge ⇒ 3.
  · ⛔ **5 minutes per box** is the net's ceiling: `durata_prevista()`
    computes it BEFORE starting and prints it, and afterwards prints how long it took.

---------------------------------------------------------------------------
⭐ THE MEASUREMENTS THAT HOLD IT UP — 25 September 2026 (phase 15, G10)
---------------------------------------------------------------------------

  · CURRENT binary 7dfd6a96, page 87268f13, 10 runs:
      rete11-lxqt  GREEN 10 out of 10 (234 s) · rete11-xfce  GREEN 10 out of 10 (236 s)
  · ⛔ COUNTER-TEST with the OLD binary 6e29da97 (without the cure 43345ea), on the
    development box rete15-lxqt (8534, same lxqt image c9f631cb,
    started on purpose and switched off again): RED — reborn 6 times out of 10 (5 at the second
    login, 1 at the first; one run «?»), 265 s.
  · injected fault `--rientra-subito` on rete11-lxqt, current binary:
    SEEN, reborn 2 out of 2 (45 s).
  ⚠ On the shared boxes the mesh runs from a copy in the box's /tmp
    (the client and C20 are also looked for in /opt/remotix): ⛔ /opt/remotix is
    the product, and it is not touched to run a bench.

Outcomes: 0 green (N out of N) · 1 red (even ONE rebirth) · 3 I could not
look (⛔ it is NOT a red).
⛔ With `--rientra-subito` it reads THE OTHER WAY ROUND: 0 = the fault is SEEN.
"""
import argparse
import importlib.util
import os
import random
import re
import signal
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
# ⚠ The client is looked for like C20 and C1: next to me, then where the box
#   puts them (`/opt/remotix`).  So the mesh also runs from a copy outside
#   `/opt/remotix` (⛔ the product of the shared boxes is not touched).
CLIENTE = next((os.path.join(b, "01-b3-cliente.py")
                for b in (QUI, os.path.dirname(QUI), "/opt/remotix", "/rete11/prodotto")
                if os.path.exists(os.path.join(b, "01-b3-cliente.py"))),
               os.path.join(QUI, "01-b3-cliente.py"))
REGISTRO = "/var/lib/rete11/registro.log"
PAROLA = "provanic2026"


def _carica(nome_file):
    """⭐ C20 and C1 are IMPORTED: the table of gestures, the lines of the end, the
    clear-out and the card groups are there, and a copy here would be one
    more place to diverge from (§1.47)."""
    for base in (QUI, os.path.dirname(QUI), "/opt/remotix", "/rete11"):
        perc = os.path.join(base, nome_file)
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location(
            "importato_" + re.sub(r"\W", "_", nome_file), perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        return m
    return None


C20 = _carica("11-c20-la-rinascita-non-porta-fantasmi.py")

# ⭐ The product lines this mesh reads, in one place only.
#   ⛔ The BIRTH is recognised in two ways, and each is enough on its own:
#     «I AM MAKING IT BE BORN»  the child decides to make it be born  src/figlio.c
#     «negotiated format»       the capture has started               src/cattura.c
#   ⇒ After the gesture neither of the two must appear for this tenant.
RIGA_FACCIO_NASCERE = "I AM MAKING IT BE BORN"
RIGA_NASCITA = "negotiated format"
# ⭐ The farewell as the client prints it (`01-b3-cliente.py`, «session closed
#   by the server, code 0x10»).  It is the second witness of the end: the one
#   whoever WATCHES sees, not what the product tells about itself.
RIGA_CONGEDO = re.compile(r"code 0x10\b")

# ⭐ The moment of the gesture CHANGES at every run.
ATTESE_K = (8.0, 10.0, 12.0, 15.0)
GUARDIA_T = 10.0
TETTO_NASCITA = 60.0
TETTO_SCATOLA = 300.0
# ⭐ How many «Log out» in a row each tenant does (see `un_inquilino`).
ACCESSI = 2
# ⚠ What it costs besides K and T, `[M]` 24 Sep 2026 on the four boxes:
#   a login (birth + waiting for the dismissed client to leave) and a
#   tenant (creation, groups, clear-out).  They serve ONLY to declare the
#   duration before starting: the real ceilings are TETTO_NASCITA and the 15 s
#   of the client's exit.
SPESA_ACCESSO = 3.0
SPESA_INQUILINO = 3.0


def attesa_del_giro(n, attese=None):
    """⭐ K of run n (from 0): in rotation over `ATTESE_K`."""
    attese = attese or ATTESE_K
    return attese[n % len(attese)]


def durata_prevista(giri, guardia=GUARDIA_T, accessi=ACCESSI, attese=None,
                    spesa_accesso=SPESA_ACCESSO,
                    spesa_inquilino=SPESA_INQUILINO):
    """⭐ The seconds of N runs («Log out»), declared before starting — pure."""
    inquilini = -(-giri // max(1, accessi))
    return (sum(spesa_accesso + attesa_del_giro(n, attese) + guardia
                for n in range(giri)) + inquilini * spesa_inquilino)


def e_di(riga, chi):
    """⚠ The name is in square brackets in the lines tagged per tenant, and
    in angle quotes in the parent's ones and in the «I AM MAKING IT BE BORN» one."""
    return ("[%s]" % chi) in riga or ("«%s»" % chi) in riga


def righe_finita():
    """The two forms of the end, from C20 — or those written here if C20 is missing
    (and then `main()` exits 3 before using them)."""
    if C20 is not None:
        return [p for p, _d in C20.RIGHE_FINITA]
    return []


def giudica_il_giro(fetta, chi, detto_dal_cliente, finite=None):
    """⭐ (esito, perche) of ONE run, from the log lines written AFTER the
    gesture and from what the client printed — pure.

      · a BIRTH for this tenant after the gesture        ⇒ 1, RED
      · the end declared (log) or the farewell 0x10      ⇒ 0, GREEN
      · neither one nor the other                        ⇒ 3

    ⛔ The birth is looked at BEFORE the end: in the measured defect the two
       can both be there (the product says «it is over» and then, at the
       next attempt, «I am making it be born»), and a green read on the first
       line would be exactly the defect slipping through.
    """
    if finite is None:
        finite = righe_finita()
    if fetta is None:
        return 3, "I could not read the server log"
    mie = [r for r in fetta if e_di(r, chi)]
    nascite = [r for r in mie
               if RIGA_FACCIO_NASCERE in r or RIGA_NASCITA in r]
    if nascite:
        return 1, ("after «Log out» the session of «%s» IS REBORN (%d lines; the "
                   "first: %s)" % (chi, len(nascite), nascite[0].strip()[:110]))
    finita = next((p for p in finite if any(p in r for r in mie)), None)
    congedo = bool(RIGA_CONGEDO.search(detto_dal_cliente or ""))
    if finita or congedo:
        return 0, ("over%s%s, and no birth after"
                   % ((" («%s»)" % finita) if finita else "",
                      " · the client dismissed with 0x10" if congedo else ""))
    return 3, ("after «Log out» the product did not declare the session over, "
               "the client was not dismissed, and it was not reborn: I do not know "
               "what happened")


def esito_dei_giri(esiti):
    """⭐ The mesh's outcome from the runs' outcomes — pure.

    ⛔ Even ONE rebirth is red: the race is caught once in twenty, and
       asking for two would be asking the race to show itself twice.
    ⚠ A 3 does not become green: if a run could not look, N out of N is not
      there ⇒ 3 (except for a red, which stays red: a rebirth SEEN is worth more
      than a run not looked at).
    """
    if not esiti:
        return 3
    if 1 in esiti:
        return 1
    if 3 in esiti:
        return 3
    return 0


def esito_col_guasto(esito):
    """⛔ With the injected fault it reads the other way round — pure."""
    return {1: 0, 0: 1}.get(esito, 3)


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    guai = 0

    def p(nome, ottenuto, atteso):
        nonlocal guai
        if ottenuto != atteso:
            guai += 1
        print("  %s %-66s %s (expected %s)"
              % ("OK " if ottenuto == atteso else "NO ", nome, ottenuto, atteso))

    print("== C24 — certification of the judgements (⛔ without touching the machine)")
    fin = ["IS OVER", "has gone ⇒ the graphical session is over"]
    finita_f = ["figlio  ⭐ §7.6: the graphical session of «c24u1» IS OVER "
                "(no client asked for it)"]
    finita_p = ["padre  ⭐ §7.6: the stage of «c24u1» has gone ⇒ the "
                "graphical session is over: sent away 1 clients with 0x10"]
    rinasce = ["figlio  [c24u1] ⭐ no graphical session for «c24u1»: I AM "
               "MAKING IT BE BORN (canvas 1920x1080)"]
    negozia = ["cattura [c24u1] ⭐ negotiated format: 1920x1080 BGRx"]
    congedo = "   [wt]   session closed by the server, code 0x10 = ?"
    g = lambda f, c="": giudica_il_giro(f, "c24u1", c, fin)[0]
    p("⭐ over (the child says so) ⇒ GREEN", g(finita_f), 0)
    p("⭐ over (the parent says so, GNOME) ⇒ GREEN", g(finita_p), 0)
    p("⭐ nothing in the log but the client dismissed 0x10 ⇒ GREEN",
      g([], congedo), 0)
    p("⛔ over AND then «I AM MAKING IT BE BORN» ⇒ RED", g(finita_f + rinasce), 1)
    p("⛔ over AND then a second «negotiated format» ⇒ RED",
      g(finita_p + negozia, congedo), 1)
    p("⛔ reborn without ever saying over ⇒ RED", g(rinasce), 1)
    p("⚠ the rebirth belongs to ANOTHER tenant ⇒ GREEN for this one",
      g(finita_f + [r.replace("c24u1", "c24u9") for r in rinasce]), 0)
    p("⚠ «c24u1» is not «c24u10» ⇒ the rebirth of c24u10 does not count",
      g(finita_f + [r.replace("c24u1", "c24u10") for r in rinasce]), 0)
    p("⚠ nothing at all ⇒ 3, ⛔ never a green", g([]), 3)
    p("⚠ the log cannot be read ⇒ 3", g(None), 3)
    p("⚠ a code 0x100 is not 0x10 ⇒ 3",
      g([], "session closed by the server, code 0x100"), 3)

    p("⭐ 10 greens ⇒ 0", esito_dei_giri([0] * 10), 0)
    p("⛔ 9 greens and ONE rebirth ⇒ 1", esito_dei_giri([0] * 9 + [1]), 1)
    p("⚠ 9 greens and a 3 ⇒ 3, ⛔ not a green", esito_dei_giri([0] * 9 + [3]), 3)
    p("⛔ a red and a 3 ⇒ 1: the rebirth seen stays",
      esito_dei_giri([3, 1, 0]), 1)
    p("⚠ no run ⇒ 3", esito_dei_giri([]), 3)
    p("⛔ fault seen (1) ⇒ 0", esito_col_guasto(1), 0)
    p("⛔ fault NOT seen (0) ⇒ 1", esito_col_guasto(0), 1)
    p("⚠ fault not looked at (3) ⇒ 3", esito_col_guasto(3), 3)

    p("⭐ K in rotation: 8, 10, 12, 15, 8",
      [attesa_del_giro(n) for n in range(5)], [8.0, 10.0, 12.0, 15.0, 8.0])
    p("⭐ 10 runs at 2 logins are 5 tenants", -(-10 // ACCESSI), 5)
    p("⛔ 10 runs fit in the ceiling of %d s" % TETTO_SCATOLA,
      durata_prevista(10) <= TETTO_SCATOLA, True)
    p("⭐ C20 is imported, and its table has the four desktops",
      (C20 is not None and len(C20.DESKTOP_E_GESTO) == 4), True)
    p("⭐ and the two forms of the end come from C20", len(righe_finita()), 2)
    print()
    if guai:
        print("⛔ %d cases do NOT give what they must" % guai)
        return 1
    print("⭐ the judge says green, red and «I do not know» where it must — and ⛔ a "
          "rebirth after\n   the declared end is red, not green")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def attacca(porta, chi, resta, uscita, tela=(1920, 1080)):
    """⭐ The Python client that watches: a process of ours, which is stopped with
    its `Popen` (⛔ no `pkill -f` with the name: it would catch itself)."""
    f = open(uscita, "w")
    return subprocess.Popen(
        ["python3", "-u", CLIENTE, "--indirizzo", "127.0.0.1", "--porta",
         str(porta), "--utente", chi, "--parola", PAROLA, "--resta",
         str(resta), "--larghezza", str(tela[0]), "--altezza", str(tela[1])],
        stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT,
        start_new_session=True)


def ferma(proc):
    if proc is None:
        return
    try:
        proc.kill()
        proc.wait(10)
    except (OSError, subprocess.TimeoutExpired):
        pass


def leggi_testo(percorso):
    try:
        with open(percorso, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def un_accesso(i, k, chi, a, gesto, desktop, dove, clienti):
    """⭐ (esito, perche) of ONE login: attach, birth, K seconds, «Log out»,
    T seconds of guard."""
    uscita = os.path.join(dove, "%s-%d.txt" % (chi, i))
    righe = C20.leggi(a.registro)
    segno = len(righe) if righe is not None else 0
    cli = attacca(a.porta, chi, TETTO_NASCITA + k + a.guardia + 30, uscita,
                  a.tela)
    clienti.append(cli)
    nato, _ = C20.aspetta_la_riga(a.registro, segno, chi, RIGA_NASCITA,
                                  TETTO_NASCITA)
    if not nato:
        return 3, ("in %d s the session of %s (login %d) was not born: %s"
                   % (TETTO_NASCITA, chi, i + 1, C20.coda_di(uscita)))

    # ── K seconds of session, then «Log out» from the menu ────────────────
    time.sleep(k)
    righe = C20.leggi(a.registro)
    segno = len(righe) if righe is not None else 0
    rtd, _ = C20.il_socket_di(chi)
    t_gesto = time.time()
    r = C20.sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s "
               "DBUS_SESSION_BUS_ADDRESS=unix:path=%s/bus %s"
               % (chi, rtd, rtd, gesto), 20)
    if r is None or r.returncode != 0:
        return 3, ("the «Log out» gesture of %s did not answer: %s"
                   % (desktop, ((r.stderr or r.stdout).strip()
                                .replace("\n", " ")[:100]) if r else
                      "no answer"))

    # ── T seconds of guard (⛔ all of them: green is an ABSENCE) ──────────
    #    ⛔ With the injected fault, as soon as the end is declared a client
    #       is reattached for the same tenant, INSIDE the window.
    if a.rientra_subito:
        finita, _ = C20.aspetta_la_riga(a.registro, segno, chi,
                                        righe_finita(), a.guardia - 2)
        if finita:
            clienti.append(attacca(a.porta, chi, a.guardia + 10,
                                   uscita + ".guasto", a.tela))
            print("      ⛔ injected fault: end declared, reattaching %s "
                  "after %.1f s" % (chi, time.time() - t_gesto))
    resto = a.guardia - (time.time() - t_gesto)
    if resto > 0:
        time.sleep(resto)
    fetta = C20.leggi(a.registro)
    fetta = fetta[segno:] if fetta is not None else None
    return giudica_il_giro(fetta, chi, leggi_testo(uscita))


def un_inquilino(primo, quanti, a, gesto, desktop, dove):
    """⭐ [(esito, perche, secondi)] of ONE new tenant, which does `quanti`
    «Log out» in a row — the runs `primo`, `primo+1`, … of the mesh.

    ⛔⛔ AND THE LOGINS PER TENANT ARE TWO, and the second is the one that counts
        most — `[M]` 24 Sep 2026 on rete11-lxqt (binary without the cure):
        with ONE login per tenant **16 «Log out» out of 16 green**; with two,
        **5 rebirths out of 5 tenants** (4 at the second login, 1 at the first).
        The first login is born in a NEW child; the second is born in the child
        that SURVIVED the previous «Log out» — the user who logs out and comes back — and
        it is there that the mount reads the DEAD session and leaves «vista
        viva» off (the box at the top).
    ⚠ After a non-green run the tenant is dropped: its session is in a
      state the next run would not know where to pick up.
    """
    t0 = time.time()
    chi = "c24u%d" % random.randint(100, 999)
    clienti = []
    fuori = []
    try:
        C20.sgombera(chi)
        r = C20.sh("useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                   % (chi, chi, PAROLA), 60)
        if r is None or r.returncode != 0:
            return [(3, "I could not create the tenant %s" % chi,
                     time.time() - t0)]
        c1 = _carica("11-c1-nasce-e-si-vede.py")
        if c1 is None or not callable(getattr(c1, "garantisci_i_gruppi", None)):
            return [(3, "I cannot find `11-c1-nasce-e-si-vede.py`: without the card "
                        "groups the session is born blind", time.time() - t0)]
        eg, perche_g = c1.garantisci_i_gruppi(chi, "      ")
        if eg != 0:
            return [(3, perche_g, time.time() - t0)]
        for i in range(quanti):
            k = attesa_del_giro(primo + i, a.attese)
            esito, perche = un_accesso(i, k, chi, a, gesto, desktop, dove,
                                       clienti)
            fuori.append((esito, "%s login %d · K=%.0f s · %s"
                          % (chi, i + 1, k, perche), time.time() - t0))
            t0 = time.time()
            if esito != 0:
                break
            # ⚠ The previous client was dismissed: we wait for it to have really
            #   left, or the next login arrives while the
            #   first is still inside (C20, 23 Sep 2026).
            C20.aspetta_che_il_cliente_se_ne_vada(a.porta, chi, 15)
        return fuori
    finally:
        for c in clienti:
            ferma(c)
        C20.sgombera(chi)
        for f in os.listdir(dove):
            if f.startswith(chi + "-"):
                try:
                    os.unlink(os.path.join(dove, f))
                except OSError:
                    pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--giri", type=int, default=0,
                   help="how many «Log out» (default 10; 2 with the fault)")
    p.add_argument("--guardia", type=float, default=GUARDIA_T,
                   help="T: the seconds after the gesture in which nothing must be "
                        "born")
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--accessi", type=int, default=2,
                   help="how many «Log out» in a row per tenant (the second is born "
                        "in the child that survived the first)")
    p.add_argument("--attese", default="",
                   help="K in rotation, in seconds: «5,6,8,10»")
    p.add_argument("--tela", default="1920x1080",
                   help="the client's canvas, WxH")
    p.add_argument("--rientra-subito", action="store_true",
                   help="⛔ THE INJECTED FAULT: after the declared end a "
                        "client is reattached ⇒ the session is really reborn "
                        "in the window, and the mesh MUST give red")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    try:
        a.tela = tuple(int(x) for x in a.tela.lower().split("x", 1))
        a.attese = tuple(float(x) for x in a.attese.split(",") if x.strip())
    except ValueError:
        print("⛔ `--tela` wants WxH and `--attese` some seconds ⇒ I could not "
              "look")
        return 3
    # ⛔ A SIGTERM (the hook's `timeout`) must go through the `finally`s: without it,
    #    the run's tenant stays alive in the box with its session —
    #    `[M]` 24 Sep 2026, rete11-xfce, a `c24u` left after the ceiling.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(3))
    if C20 is None:
        print("⛔ I cannot find `11-c20-la-rinascita-non-porta-fantasmi.py` next "
              "to me: the table of «Log out» gestures is there ⇒ I could not look")
        return 3
    if not a.porta:
        print("⛔ it wants `--porta` ⇒ I could not look")
        return 3
    if os.geteuid() != 0:
        print("⛔ it wants the administrator (it creates the tenants) ⇒ I could not "
              "look")
        return 3
    giri = a.giri or (2 if a.rientra_subito else 10)

    desktop, gesto = C20.come_si_esce()
    if desktop is None:
        print("⛔ %s ⇒ I could not look" % gesto)
        return 3
    if C20.leggi(a.registro) is None:
        print("⛔ I cannot read %s ⇒ I could not look" % a.registro)
        return 3
    accessi = max(1, a.accessi)
    previsti = durata_prevista(giri, a.guardia, accessi, a.attese)
    print("== C24 — «Log out» closes the session, always (%s, port %d, %d runs)%s"
          % (desktop, a.porta, giri,
             " ⛔ INJECTED FAULT: --rientra-subito" if a.rientra_subito
             else ""))
    print("   «Log out» is said like this: %s" % gesto)
    print("   expected duration: ~%.0f s (%d runs = %d tenants × %d logins; "
          "every run %.0f s + K + T=%.0f s)%s"
          % (previsti, giri, -(-giri // accessi), accessi, SPESA_ACCESSO,
             a.guardia,
                  "" if previsti <= TETTO_SCATOLA else
                  "  ⚠ BEYOND the net's ceiling of %.0f s" % TETTO_SCATOLA))

    dove = "/tmp/c24.%d" % os.getpid()
    os.makedirs(dove, exist_ok=True)
    t0 = time.time()
    esiti = []
    try:
        while len(esiti) < giri:
            for e, perche, s in un_inquilino(len(esiti),
                                             min(accessi, giri - len(esiti)),
                                             a, gesto, desktop, dove):
                esiti.append(e)
                print("   run %2d  %-5s %4.0f s  %s"
                      % (len(esiti), {0: "VERDE", 1: "ROSSO", 3: "?"}[e], s,
                         perche), flush=True)
    finally:
        # ⚠ No browser is started here ⇒ no `/tmp/mozilla` to
        #   remove: every run has already cleared out the tenants.
        try:
            os.rmdir(dove)
        except OSError:
            pass

    esito = esito_dei_giri(esiti)
    rinate, verdi = esiti.count(1), esiti.count(0)
    print()
    print("   duration: %.0f s (expected ~%.0f s)" % (time.time() - t0, previsti))
    if a.rientra_subito:
        fuori = esito_col_guasto(esito)
        if fuori == 0:
            print("⭐ THE INJECTED FAULT WAS SEEN — reborn %d times out of "
                  "%d: this mesh CAN give red" % (rinate, giri))
        elif fuori == 1:
            print("⛔⛔ THE INJECTED FAULT WAS NOT SEEN: the session was "
                  "really reborn\n   (a new attach) and the mesh said "
                  "green")
        else:
            print("⚠ with the injected fault I could NOT look ⇒ 3")
        return fuori
    if esito == 0:
        print("⭐ GREEN — «Log out» closed the session %d times out of %d, and it was not "
              "reborn" % (verdi, giri))
    elif esito == 1:
        print("⛔⛔ RED — after «Log out» the session was REBORN %d times out of %d"
              % (rinate, giri))
    else:
        print("⚠ I could not look — %d runs out of %d without an outcome"
              % (esiti.count(3), giri))
    return esito


if __name__ == "__main__":
    sys.exit(main())
