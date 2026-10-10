#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c13 — ⭐⭐ «THE CERTIFICATION IS RECENT» — the mesh that looks at THE NET
===========================================================================

    python3 11-c13-la-certificazione-e-recente.py
    python3 11-c13-la-certificazione-e-recente.py --certifica
    python3 11-c13-la-certificazione-e-recente.py --ultimi 40

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — and `fasi/11…` §4.2 says it better than I would
---------------------------------------------------------------------------

  ⛔ *«a net that is no longer able to give red LOOKS EXACTLY LIKE
       a net that finds nothing.»*

⚠ And it is the hardest fault to see in the whole phase, because **it has no
  symptoms**.  All green, every day, for weeks.  ⇒ And the difference between
  *«there is nothing wrong»* and *«I no longer look»* cannot be read from outside: it
  can be read **only** by injecting a fault and demanding that it be seen.

⭐ §3.6 declares it as part of the net, not as a courtesy:
  ⛔ *«every test of the list has, mandatorily, its injected fault, and
     that case must be run, NOT IMAGINED»* — and ⇒ *«the log of what
     was injected, when, and with what outcome, is part of the net (C13)»*.

---------------------------------------------------------------------------
⭐ WHAT IT LOOKS AT — and the three outcomes it can tell apart
---------------------------------------------------------------------------

It reads the hook's log and, in the last **N real runs**, looks for **at least one
mesh** that carries both things:

    "guasto_innestato": true    ⇒ a fault was injected into it
    "ha_visto_il_guasto": true  ⇒ and it SAW it

⛔⛔ AND THE TWO THINGS MUST BE IN THE SAME MESH, not in the same run.
   ⚠ If *«in this run there was an injected fault AND someone gave
     red»* were enough, the red could come from **another mesh** — for example from
     C1, which really has a real fault — ⇒ and this mesh would say *«the
     net can give red»* having looked at a test that has nothing to do with it.
     ⛔ It would be a check that cannot give red: the error shape of
     `LEZIONI.md` §1.44.

⚠ And the field is called `ha_visto_il_guasto` and not `esito` for a reason: on an
  injected run **the outcome reads the other way round** (C8 `--senza-cura` exits **0**
  when the fault was seen).  ⭐ That inversion lives in one place only —
  inside the hook — and here there is no need to know it.

The three distinct cases, and they really are three different things:

  ⛔ **nothing ever injected**   the net runs and nobody puts it to the test
  ⛔⛔ **injected and NOT seen**  the worst case: the net had a fault
                                under its nose and said green
  ⭐ **injected and seen**       the net is still able to give red

---------------------------------------------------------------------------
⚠ THE YARDSTICK, declared and printed in every outcome
---------------------------------------------------------------------------

  `[?]` **last 20 real runs.**  ⛔ Chosen, not measured.
  ⚠ DRY runs (`--secco`) do not count: a run that executed nothing
    cannot have seen anything.

⛔ And the criterion is **by COUNTS, not by days** — because that is how §4.2 asks for it
   (*«in the last N runs»*).  ⚠ It has a declared hole: if the hook ran once
   a month, «the last twenty runs» would cover two years.  ⇒ The age
   of the last certification is **always printed**, and with `--giorni N` it becomes
   a judgement too.  ⭐ Off by default: this mesh does what the
   document asks of it, and does not invent policy on its own.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ in the last N runs a fault was injected and IT WAS SEEN
  1  ⛔ no fault injected, or injected and not seen ⇒ red
  3  ⛔ I could not look — no real run to examine, or the log
     cannot be read.  ⛔ And it is NOT a red: that the hook has never
     run is said by **C12**, and two meshes giving red for the same fact
     make what happened once look twice as serious
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import json
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
REGISTRO = os.path.join(QUI, "11-gancio-registro.jsonl")

ULTIMI_PREDEFINITI = 20


def leggi_il_registro(percorso):
    """Returns (giri, guaio) — ⛔ and the cases are three, as in C12.

       (None, "assente")     the file is not there
       (None, "illeggibile") it is there and does not open, or it is all malformed
       ([...], None)         the runs, in order of writing
    """
    if not os.path.exists(percorso):
        return None, "assente"
    try:
        with open(percorso, "r", errors="replace") as f:
            righe = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    giri, storte = [], 0
    for r in righe:
        r = r.strip()
        if not r:
            continue
        try:
            giri.append(json.loads(r))
        except ValueError:
            storte += 1
    if not giri and storte:
        return None, "illeggibile"
    return giri, None


def giudica(giri, ultimi):
    """Says whether the net is still able to give red.

    ⛔ Returns `None` for «I could not look» (no real run to look at),
       otherwise a dictionary:

         esaminati       how many real runs it looked at
         innestati       how many meshes had a fault injected
         viste           how many of those SAW it
         mancate         the list (run, mesh) of those that did NOT see it
         ultima          the run in which the last certification succeeded
    """
    if giri is None:
        return None
    # ⛔ Dry runs are thrown away BEFORE counting the last N: counting them
    #    would mean that twenty `--secco` in a row push out of the window
    #    the last real certification, and the mesh turns red for nothing.
    veri = [g for g in giri if not g.get("secco")]
    if not veri:
        return None
    fetta = veri[-ultimi:]

    innestati = 0
    viste = 0
    mancate = []
    ultima = None
    for g in fetta:
        for m in g.get("maglie") or []:
            if not m.get("guasto_innestato"):
                continue
            innestati += 1
            # ⛔ The key must be there AND be true.  ⚠ An ABSENT key is not
            #   «seen»: it is a log older than the field, that is «I do not
            #   know» — and here it counts as «not seen», because a certification
            #   whose outcome is unknown certifies nothing.
            if m.get("ha_visto_il_guasto") is True:
                viste += 1
                ultima = g
            else:
                mancate.append((g.get("istante"), m.get("nome"),
                                m.get("ha_visto_il_guasto")))
    return {"esaminati": len(fetta), "innestati": innestati, "viste": viste,
            "mancate": mancate, "ultima": ultima, "totali": len(veri),
            "a_vuoto": len(giri) - len(veri)}


def eta_in_giorni(istante, adesso):
    """⛔ Returns `None` if it cannot tell — never zero, never an invented number."""
    if not istante:
        return None
    try:
        import datetime
        t = datetime.datetime.fromisoformat(istante)
        if t.tzinfo is None:
            t = t.astimezone()
        return (adesso - t.timestamp()) / 86400.0
    except (ValueError, TypeError, OverflowError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ We prove that the judge CAN give red, green, and «I do not know»."""

    def giro(maglie, secco=False, istante="2026-08-26T05:00:00+02:00"):
        return {"istante": istante, "secco": secco, "maglie": maglie}

    def m(nome, guasto=False, visto=None, esito=0):
        d = {"nome": nome, "esito": esito, "guasto_innestato": guasto}
        if visto is not None:
            d["ha_visto_il_guasto"] = visto
        return d

    casi = [
        ("⭐ a fault injected, and the net SAW it",
         [giro([m("C1"), m("C8 guasto", guasto=True, visto=True)])], "verde"),

        ("⛔ twenty runs and no fault ever injected",
         [giro([m("C1"), m("C11")]) for _ in range(20)], "ROSSO"),

        ("⛔⛔ injected and NOT seen — the worst case",
         [giro([m("C8 guasto", guasto=True, visto=False, esito=1)])], "ROSSO"),

        # ⭐⭐ THE CASE THAT HOLDS UP THE WHOLE MESH.
        ("⭐⭐ red from ANOTHER mesh certifies nothing",
         [giro([m("C1", esito=1),
                m("C8 guasto", guasto=True, visto=False, esito=1)])], "ROSSO"),

        ("⚠ injected, and nothing is known of its outcome (field absent)",
         [giro([m("C8 guasto", guasto=True)])], "ROSSO"),

        ("one successful certification among twenty normal runs ⇒ green",
         [giro([m("C1")]) for _ in range(19)]
         + [giro([m("C8 guasto", guasto=True, visto=True)])], "verde"),

        ("⛔ the certification slid OUT of the window of twenty",
         [giro([m("C8 guasto", guasto=True, visto=True)])]
         + [giro([m("C1")]) for _ in range(20)], "ROSSO"),

        # ⛔ And dry runs must not push out a real certification.
        ("⭐ twenty DRY runs do not push out the real certification",
         [giro([m("C8 guasto", guasto=True, visto=True)])]
         + [giro([m("C1")], secco=True) for _ in range(20)], "verde"),

        ("⛔ all the runs are dry ⇒ «I do not know», not red",
         [giro([m("C8 guasto", guasto=True, visto=True)], secco=True)], "non lo so"),

        ("⛔ no run ⇒ «I do not know» — that it has never run is said by C12",
         [], "non lo so"),

        ("⛔ unreadable log ⇒ «I do not know», not red",
         None, "non lo so"),
    ]

    print("== certification of the C13 judge ==")
    print("   window in force: last %d REAL runs · dry runs do not count"
          % ULTIMI_PREDEFINITI)
    guai = 0
    for nome, giri, atteso in casi:
        r = giudica(giri, ULTIMI_PREDEFINITI)
        if r is None:
            ottenuto = "non lo so"
        elif r["viste"] >= 1:
            ottenuto = "verde"
        else:
            ottenuto = "ROSSO"
        ok = ottenuto == atteso
        print("  %s  %-58s  ⇒ %-9s (expected %s)"
              % ("OK " if ok else "NO ", nome, ottenuto, atteso))
        if not ok:
            guai += 1
            print("        (the judge said: %r)" % (r,))

    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d wrong cases" % guai)
        return 1
    print("⭐ the judge tells apart the three things that count: never injected ·")
    print("   injected and not seen · injected and seen")
    print("⭐⭐ and ⛔ it does NOT let itself be certified by a red coming from another mesh")
    print("⚠ and this certification covers THE JUDGEMENT, not the injected faults:")
    print("  that they are the RIGHT ones is decided by §3.6, not by me")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--ultimi", type=int, default=ULTIMI_PREDEFINITI,
                   help="how many real runs to look back. `[?]` chosen, not measured")
    p.add_argument("--giorni", type=int, default=0,
                   help="⚠ if > 0, the age of the last certification becomes "
                        "a JUDGEMENT too. Off by default: §4.2 asks for a "
                        "criterion by counts, not by days")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    giri, guaio = leggi_il_registro(a.registro)

    print("== C13 — is the certification recent? ==")
    print("   ⛔ the fault it looks for: a net that is no longer able to give")
    print("      red LOOKS THE SAME as a net that finds nothing")
    print("   yardstick: last %d REAL runs  `[?]`  ·  dry runs do not count"
          % a.ultimi)
    if a.giorni:
        print("   ⚠ and in addition: the last certification within %d days" % a.giorni)
    print()

    if guaio == "assente":
        print("⛔ the log is not there: %s" % a.registro)
        print("   ⇒ I could not look — ⛔ and it is NOT a red.")
        print("     That the hook has never run is said by C12, and it is right")
        print("     that ONE mesh only says it.")
        return 3
    if guaio == "illeggibile":
        print("⛔ the log is there and cannot be read: %s" % a.registro)
        print("   ⇒ I could not look")
        return 3

    r = giudica(giri, a.ultimi)
    if r is None:
        print("⛔ no REAL run to look at (%d lines, all dry or none)"
              % len(giri or []))
        print("   ⇒ I could not look — ⛔ and it is NOT a red")
        return 3

    print("   runs in the log   : %d real, %d dry" % (r["totali"], r["a_vuoto"]))
    print("   looked at         : the last %d" % r["esaminati"])
    print("   injected faults   : %d" % r["innestati"])
    print("   ⭐ seen            : %d" % r["viste"])
    adesso = time.time()
    if r["ultima"]:
        eta = eta_in_giorni(r["ultima"].get("istante"), adesso)
        print("   last successful   : %s  (%s)"
              % (r["ultima"].get("istante"),
                 "age unknown" if eta is None else "%.1f days ago" % eta))
    print()

    if r["mancate"]:
        print("⛔⛔ AND THESE MESHES HAD A FAULT UNDER THEIR NOSE AND DID NOT")
        print("    SEE IT:")
        for quando, nome, visto in r["mancate"]:
            print("   · %s  ·  %s  (ha_visto_il_guasto=%r)" % (quando, nome, visto))
        print()

    if r["viste"] >= 1:
        vecchia = False
        if a.giorni and r["ultima"]:
            eta = eta_in_giorni(r["ultima"].get("istante"), adesso)
            if eta is not None and eta > a.giorni:
                vecchia = True
                print("⛔ RED — the last successful certification is from %.1f days"
                      " ago, and the threshold asked is %d" % (eta, a.giorni))
        if not vecchia:
            print("⭐ in the last %d runs a fault was injected and IT WAS"
                  " SEEN %d times" % (r["esaminati"], r["viste"]))
            print("⚠ and this says the net can still give red ON THE FAULTS IT")
            print("  KNOWS. ⛔ §3.6: the injected faults are faults already known, and")
            print("  every new desktop must come in with **a fault of its own**.")
            if r["mancate"]:
                print("⚠ ⛔ but above there is a list of MISSED certifications: they must")
                print("  be looked at, even if this mesh is green.")
            return 0
        return 1

    if r["innestati"] == 0:
        print("⛔⛔ RED — in the last %d runs **no fault was ever"
              " injected**." % r["esaminati"])
        print("   ⇒ the net runs, and nobody puts it to the test. ⛔ From outside it is")
        print("     indistinguishable from a net that works perfectly.")
        print("   ⚠ And the cure is not touching this mesh: it is running the")
        print("     `tutto` family, which has the injected fault inside it.")
        return 1

    print("⛔⛔ RED — %d faults were injected and **none was seen**."
          % r["innestati"])
    print("   ⇒ ⛔ it is the worst case of the three: the net is no longer able to")
    print("     give red, and it keeps saying green with the same face.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
