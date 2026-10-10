#!/usr/bin/env python3
"""02-pam-i3.py — ⛔ THE THREE THINGS THE §1.10 CURE MUST NOT HAVE BROKEN.

    python3 02-pam-i3.py --caso <secondo|ban|ban-dopo-riavvio|morto|insieme|libera>

===========================================================================
⛔ WHY IT EXISTS, SEPARATE FROM `02-pam-fermo.py`

`02-pam-fermo.py` measures **how long whoever is not authenticating stands still**, and it is the
number the cure is made for.  ⛔ But a cure that made that number collapse
**by breaking authentication** would be the worst possible trade, and the
mandate names it first:

    «A helper that answers "yes" for a lost message, a timeout
     or a dead process is **I3 violated**, and it is the worst defect this
     work could produce.  Design it so that **failure is a no**, not
     a maybe.»

⇒ This file takes **the concrete case** instead of the argument: the helper
  is killed and the **RIGHT** password is presented.

⛔ And it also takes the two things §1.10 requires not to move, because the cure
   touched both of them in the code:

   · **the fixed second** of §4.4-bis — `attesa-verdetto` now waits for TWO
     things instead of one (the clock and the answer), and the order between the two is
     not guaranteed;
   · **the per-address count** of §4.4-bis — `segna_fallito()` has
     **moved**, from `tratta_credenziali()` to `rcp_verdetto()`, because it is
     there that the fact «an attempt failed» now exists.  ⚠ A
     move is precisely the kind of change that reads well and does
     nothing — the form that bench **B5** has already found once, with
     the counter that was always 1.

===========================================================================
⛔ THE SIX CASES, AND THE EXPECTATION OF EACH, WRITTEN BEFOREHAND

  secondo            RIGHT password         -> `AMMESSO`, and **>= 1000 ms**
                     WRONG password         -> `RESPINTO(0x07)`, and **>= 1000 ms**
                     ⛔ the second holds for the admitted one too, or the distinction
                        that §4.4 forbids writing in the reason would be read
                        with the stopwatch

  ban                three wrong passwords with **three different user names**
                     (§4.4-bis: the name does not matter, three names count three), then
                     the fourth attempt with the **RIGHT** password
                     -> ⛔ `RESPINTO(0x08 TROPPI_TENTATIVI)`.
                     ⭐ It is the proof that tells a ban from a counter: whoever
                        has the right password would get in, if it were a counter

  ban-dopo-riavvio   after the server has been switched off and on again, the
                     RIGHT password -> ⛔ still `0x08`.  Invariant **I7**: the
                     protection lives in the program, not in a memory that a
                     restart takes away

  morto              ⛔ the helper has been KILLED, and the **RIGHT** password
                     is presented -> `RESPINTO` must arrive, never `AMMESSO`.
                     ⚠ It is the case this file exists for

  insieme            ⛔ TWO wrong passwords at the SAME instant — and they are two
                     and not three, because at the third the ban would trigger.  If the two
                     grandchildren work in parallel the wall lasts as long as the
                     SLOWEST (~2 s); if they queued it would last the SUM
                     (~4 s).  ⭐ It closes the `[?]` that `aiutante.h` declares

  libera             the unblock (§4.4-bis, the second way out) and an
                     entry with the right password: ⭐ it is the **positive
                     control** of all the cases above — «can the tool
                     let someone in?»  Without it, a `RESPINTO` everywhere
                     would be green for the wrong reason

⛔ And every case prints `OK`/`NO` with the number it read next to it, not a
   judgement: whoever rereads the log must be able to redo the count.
"""
import argparse
import asyncio
import importlib.util
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
# ⚠ The file name has hyphens, so it is not a module name: it is loaded
#   from its path.  ⛔ And it loads ITS OWN bench, not someone else's:
#   a dependency on `01-b3-cliente.py` would tie the certification of this
#   file to bytes that are not mine.
_spec = importlib.util.spec_from_file_location(
    "pamfermo", os.path.join(QUI, "02-pam-fermo.py"))
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)


async def tentativo(a, utente, parola):
    """One connection, one `CREDENZIALI`, and what comes back.

    Returns (name, reason, ms).  ⛔ It does not raise on `RESPINTO`: the refusal
    is the measurement, not an accident."""
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as pila:
        cli = await F.apri(pila, a.indirizzo, a.porta, "/rcp/1")
        await F.fino_a_eccomi(cli)
        t0 = time.monotonic()
        cli.manda(F.inquadra(F.T["CREDENZIALI"], F.s(utente) + F.s(parola)))
        try:
            nome, corpo = await F.attendi(cli, None, attesa=40)
        except (F.Caduta, asyncio.TimeoutError) as e:
            return ("CADUTA", None, (time.monotonic() - t0) * 1000, str(e))
        ms = (time.monotonic() - t0) * 1000
        motivo = corpo[0] if (nome == "RESPINTO" and corpo) else None
        return (nome, motivo, ms, None)


def dillo(ok, testo):
    print(f"   {'⭐ OK' if ok else '⛔ NO'}  {testo}")
    return 0 if ok else 1


async def principale(a, parola):
    male = 0
    nome_motivo = F.MOTIVI

    if a.caso == "secondo":
        print("== the fixed second of §4.4-bis, and it holds ALSO for the admitted one")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "AMMESSO" and ms >= 1000,
                      f"RIGHT password -> {n} in {ms:.0f} ms "
                      f"(expected AMMESSO, >= 1000)")
        await asyncio.sleep(0.5)
        n, m, ms, err = await tentativo(a, a.utente, "questa-e-sbagliata")
        male += dillo(n == "RESPINTO" and m == 0x07 and ms >= 1000,
                      f"WRONG password -> {n}"
                      f"({nome_motivo.get(m, m)}) in {ms:.0f} ms "
                      f"(expected RESPINTO 0x07, >= 1000)")
        # ⛔ And it cleans up: a failure left as inheritance to the next case
        #    would skew the count of whoever comes next.
        print(f"   ⚠ unblock DECLARED: {F.sblocca(a.socket, a.indirizzo)}")

    elif a.caso == "ban":
        print("== §4.4-bis: three failures from the same address, with THREE DIFFERENT "
              "NAMES")
        print(f"   ⚠ unblock DECLARED, to start from a known state: "
              f"{F.sblocca(a.socket, a.indirizzo)}")
        for i, u in enumerate(("prova", "prova2", "nessuno-di-questi"), 1):
            n, m, ms, err = await tentativo(a, u, "questa-e-sbagliata")
            print(f"   -- failure {i}/3 (user «{u}»): {n}"
                  f"({nome_motivo.get(m, m)}) in {ms:.0f} ms")
            male += dillo(n == "RESPINTO" and m == 0x07,
                          f"   number {i} is a CREDENZIALI_ERRATE, not already a ban")
            await asyncio.sleep(0.4)
        print("== and the FOURTH, with the RIGHT password")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "RESPINTO" and m == 0x08,
                      f"RIGHT password -> {n}({nome_motivo.get(m, m)}) in "
                      f"{ms:.0f} ms  (expected RESPINTO 0x08 TROPPI_TENTATIVI: "
                      f"⭐ it is the proof that tells a ban from a counter)")

    elif a.caso == "ban-dopo-riavvio":
        print("== I7: the ban survives the server restart")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "RESPINTO" and m == 0x08,
                      f"after the restart, RIGHT password -> {n}"
                      f"({nome_motivo.get(m, m)})  (expected 0x08)")

    elif a.caso == "morto":
        print("== ⛔ I3: the helper is dead, and the RIGHT password is presented")
        print("   ⚠ If AMMESSO appeared here, the cure would have bought "
              "speed with the guard.")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "RESPINTO",
                      f"RIGHT password with the helper dead -> {n}"
                      f"({nome_motivo.get(m, m)}) in {ms:.0f} ms  "
                      f"(expected RESPINTO, NEVER AMMESSO)")
        male += dillo(ms >= 1000,
                      f"   and the fixed second is there anyway ({ms:.0f} ms): an "
                      f"instant refusal would say with the stopwatch what the "
                      f"reason does not say")

    elif a.caso == "insieme":
        # ⛔⭐ TWO WHO GET THE PASSWORD WRONG AT THE SAME INSTANT.
        #
        # `aiutante.h` declares a second gain beyond the one measured by
        # `02-pam-fermo.py`: **two who log in together do not queue**,
        # because the grandchildren are two processes.  ⚠ Something declared and not
        # measured is a `[?]`, and this case closes it or leaves it open.
        #
        # ⛔ The expectation, written beforehand: if the two run in parallel the wall lasts
        #    as long as the SLOWER of the two (~2 s); if they queue it lasts the
        #    SUM (~4 s).  The two numbers cannot be confused.
        # ⚠ And they are TWO and not three: at the third the ban would trigger (§4.4-bis), and
        #   an instant refusal would be measured instead of PAM.
        print("== two wrong passwords at the same instant: queue or parallel?")
        print(f"   ⚠ unblock DECLARED, to start from a known state: "
              f"{F.sblocca(a.socket, a.indirizzo)}")
        t0 = time.monotonic()
        r1, r2 = await asyncio.gather(
            tentativo(a, "prova", "questa-e-sbagliata"),
            tentativo(a, "prova2", "questa-e-sbagliata"))
        tot = (time.monotonic() - t0) * 1000
        print(f"   -- the first: {r1[0]}({nome_motivo.get(r1[1], r1[1])}) in {r1[2]:.0f} ms")
        print(f"   -- the second:{r2[0]}({nome_motivo.get(r2[1], r2[1])}) in {r2[2]:.0f} ms")
        piu_lento = max(r1[2], r2[2])
        somma = r1[2] + r2[2]
        male += dillo(r1[1] == 0x07 and r2[1] == 0x07,
                      "both are CREDENZIALI_ERRATE (0x07): PAM was really "
                      "queried twice")
        male += dillo(tot < somma * 0.75,
                      f"the total wall is {tot:.0f} ms — the slower of the two "
                      f"is {piu_lento:.0f}, the sum would be {somma:.0f}.  "
                      f"⭐ In parallel, not queued")
        print(f"   ⚠ unblock DECLARED, so as not to leave the field dirty: "
              f"{F.sblocca(a.socket, a.indirizzo)}")

    elif a.caso == "libera":
        print("== the positive control: the unblock (§4.4-bis) and a real entry")
        r = F.sblocca(a.socket, a.indirizzo)
        print(f"   -- unblock: {r}")
        male += dillo(r.startswith("TOLTO") or r.startswith("NON-BANNATO"),
                      f"the unblock command answered: {r}")
        n, m, ms, err = await tentativo(a, a.utente, parola)
        male += dillo(n == "AMMESSO",
                      f"and with the RIGHT password you get in: {n} in {ms:.0f} ms  "
                      f"⭐ without this, every RESPINTO above would be green "
                      f"for the wrong reason")

    print(f"\n== {'⭐ all as expected' if male == 0 else f'⛔ {male} checks out of place'}")
    return 0 if male == 0 else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7531)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola-file", required=True)
    p.add_argument("--socket", default="")
    p.add_argument("--caso", required=True,
                   choices=["secondo", "ban", "ban-dopo-riavvio", "morto",
                            "insieme", "libera"])
    a = p.parse_args()
    if F.AIOQUIC:
        print(f"   ⛔ «aioquic» is not there: {F.AIOQUIC}")
        sys.exit(2)
    parola = F.parola_dal_file(a.parola_file)
    try:
        sys.exit(asyncio.run(principale(a, parola)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
