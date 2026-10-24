#!/usr/bin/env python3
"""02-pam-i3.py — ⛔ THE THREE THINGS THE §1.10 CURE MUST NOT HAVE BROKEN.

    python3 02-pam-i3.py --case <secondo|ban|ban-dopo-riavvio|morto|insieme|libera>

===========================================================================
⛔ WHY IT EXISTS, SEPARATE FROM `02-pam-standstill.py`

`02-pam-standstill.py` measures **how long whoever is not authenticating stands still**, and it is the
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

   · **the fixed second** of §4.4-bis — `wait-verdict` now waits for TWO
     things instead of one (the clock and the answer), and the order between the two is
     not guaranteed;
   · **the per-address count** of §4.4-bis — `mark_failed()` has
     **moved**, from `handle_credentials()` to `rcp_verdict()`, because it is
     there that the fact «an attempt failed» now exists.  ⚠ A
     move is precisely the kind of change that reads well and does
     nothing — the form that bench **B5** has already found once, with
     the counter that was always 1.

===========================================================================
⛔ THE SIX CASES, AND THE EXPECTATION OF EACH, WRITTEN BEFOREHAND

  secondo            RIGHT password         -> `ADMITTED`, and **>= 1000 ms**
                     WRONG password         -> `REJECTED(0x07)`, and **>= 1000 ms**
                     ⛔ the second holds for the admitted one too, or the distinction
                        that §4.4 forbids writing in the reason would be read
                        with the stopwatch

  ban                three wrong passwords with **three different user names**
                     (§4.4-bis: the name does not matter, three names count three), then
                     the fourth attempt with the **RIGHT** password
                     -> ⛔ `REJECTED(0x08 TOO_MANY_ATTEMPTS)`.
                     ⭐ It is the proof that tells a ban from a counter: whoever
                        has the right password would get in, if it were a counter

  ban-dopo-riavvio   after the server has been switched off and on again, the
                     RIGHT password -> ⛔ still `0x08`.  Invariant **I7**: the
                     protection lives in the program, not in a memory that a
                     restart takes away

  morto              ⛔ the helper has been KILLED, and the **RIGHT** password
                     is presented -> `REJECTED(0x0E)` must arrive, never
                     `ADMITTED` (0x0E: the check was not made, §11.39).
                     ⚠ It is the case this file exists for

  insieme            ⛔ TWO wrong passwords at the SAME instant — and they are two
                     and not three, because at the third the ban would trigger.  If the two
                     grandchildren work in parallel the wall lasts as long as the
                     SLOWEST (~2 s); if they queued it would last the SUM
                     (~4 s).  ⭐ It closes the `[?]` that `helper.h` declares

  libera             the unblock (§4.4-bis, the second way out) and an
                     entry with the right password: ⭐ it is the **positive
                     control** of all the cases above — «can the tool
                     let someone in?»  Without it, a `REJECTED` everywhere
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

HERE = os.path.dirname(os.path.abspath(__file__))
# ⚠ The file name has hyphens, so it is not a module name: it is loaded
#   from its path.  ⛔ And it loads ITS OWN bench, not someone else's:
#   a dependency on `01-b3-client.py` would tie the certification of this
#   file to bytes that are not mine.
_spec = importlib.util.spec_from_file_location(
    "pamfermo", os.path.join(HERE, "02-pam-standstill.py"))
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)


async def attempt(a, user, password):
    """One connection, one `CREDENTIALS`, and what comes back.

    Returns (name, reason, ms).  ⛔ It does not raise on `REJECTED`: the refusal
    is the measurement, not an accident."""
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as stack:
        cli = await F.do_open(stack, a.address, a.port, "/rcp/1")
        await F.until_here_i_am(cli)
        t0 = time.monotonic()
        cli.send_msg(F.wrap(F.T["CREDENTIALS"], F.s(user) + F.s(password)))
        try:
            name, body = await F.should_wait(cli, None, wait=40)
        except (F.Drop, asyncio.TimeoutError) as e:
            return ("CADUTA", None, (time.monotonic() - t0) * 1000, str(e))
        ms = (time.monotonic() - t0) * 1000
        reason = body[0] if (name == "REJECTED" and body) else None
        return (name, reason, ms, None)


def report_it(ok, text):
    print(f"   {'⭐ OK' if ok else '⛔ NO'}  {text}")
    return 0 if ok else 1


async def main(a, password):
    male = 0
    reason_name = F.REASONS

    if a.case == "second":
        print("== the fixed second of §4.4-bis, and it holds ALSO for the admitted one")
        n, m, ms, err = await attempt(a, a.user, password)
        male += report_it(n == "ADMITTED" and ms >= 1000,
                      f"RIGHT password -> {n} in {ms:.0f} ms "
                      f"(expected ADMITTED, >= 1000)")
        await asyncio.sleep(0.5)
        n, m, ms, err = await attempt(a, a.user, "questa-e-sbagliata")
        male += report_it(n == "REJECTED" and m == 0x07 and ms >= 1000,
                      f"WRONG password -> {n}"
                      f"({reason_name.get(m, m)}) in {ms:.0f} ms "
                      f"(expected REJECTED 0x07, >= 1000)")
        # ⛔ And it cleans up: a failure left as inheritance to the next case
        #    would skew the count of whoever comes next.
        print(f"   ⚠ unblock DECLARED: {F.unblock(a.socket, a.address)}")

    elif a.case == "ban":
        print("== §4.4-bis: three failures from the same address, with THREE DIFFERENT "
              "NAMES")
        print(f"   ⚠ unblock DECLARED, to start from a known state: "
              f"{F.unblock(a.socket, a.address)}")
        for i, u in enumerate(("prova", "prova2", "nessuno-di-questi"), 1):
            n, m, ms, err = await attempt(a, u, "questa-e-sbagliata")
            print(f"   -- failure {i}/3 (user «{u}»): {n}"
                  f"({reason_name.get(m, m)}) in {ms:.0f} ms")
            male += report_it(n == "REJECTED" and m == 0x07,
                          f"   number {i} is a WRONG_CREDENTIALS, not already a ban")
            await asyncio.sleep(0.4)
        print("== and the FOURTH, with the RIGHT password")
        n, m, ms, err = await attempt(a, a.user, password)
        male += report_it(n == "REJECTED" and m == 0x08,
                      f"RIGHT password -> {n}({reason_name.get(m, m)}) in "
                      f"{ms:.0f} ms  (expected REJECTED 0x08 TOO_MANY_ATTEMPTS: "
                      f"⭐ it is the proof that tells a ban from a counter)")

    elif a.case == "ban-after-restart":
        print("== I7: the ban survives the server restart")
        n, m, ms, err = await attempt(a, a.user, password)
        male += report_it(n == "REJECTED" and m == 0x08,
                      f"after the restart, RIGHT password -> {n}"
                      f"({reason_name.get(m, m)})  (expected 0x08)")

    elif a.case == "dead":
        print("== ⛔ I3: the helper is dead, and the RIGHT password is presented")
        print("   ⚠ If ADMITTED appeared here, the cure would have bought "
              "speed with the guard.")
        n, m, ms, err = await attempt(a, a.user, password)
        # DECISIONS.md §11.39 (15 Oct 2026): a check the server could not
        # make is REJECTED(0x0E SESSION_UNSERVABLE), not 0x07.
        male += report_it(n == "REJECTED" and m == 0x0E,
                      f"RIGHT password with the helper dead -> {n}"
                      f"({reason_name.get(m, m)}) in {ms:.0f} ms  "
                      f"(expected REJECTED 0x0E SESSION_UNSERVABLE, NEVER "
                      f"ADMITTED)")
        male += report_it(ms >= 1000,
                      f"   and the fixed second is there anyway ({ms:.0f} ms): an "
                      f"instant refusal would say with the stopwatch what the "
                      f"reason does not say")

    elif a.case == "together":
        # ⛔⭐ TWO WHO GET THE PASSWORD WRONG AT THE SAME INSTANT.
        #
        # `helper.h` declares a second gain beyond the one measured by
        # `02-pam-standstill.py`: **two who log in together do not queue**,
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
              f"{F.unblock(a.socket, a.address)}")
        t0 = time.monotonic()
        r1, r2 = await asyncio.gather(
            attempt(a, "prova", "questa-e-sbagliata"),
            attempt(a, "prova2", "questa-e-sbagliata"))
        tot = (time.monotonic() - t0) * 1000
        print(f"   -- the first: {r1[0]}({reason_name.get(r1[1], r1[1])}) in {r1[2]:.0f} ms")
        print(f"   -- the second:{r2[0]}({reason_name.get(r2[1], r2[1])}) in {r2[2]:.0f} ms")
        slower = max(r1[2], r2[2])
        total_sum = r1[2] + r2[2]
        male += report_it(r1[1] == 0x07 and r2[1] == 0x07,
                      "both are WRONG_CREDENTIALS (0x07): PAM was really "
                      "queried twice")
        male += report_it(tot < total_sum * 0.75,
                      f"the total wall is {tot:.0f} ms — the slower of the two "
                      f"is {slower:.0f}, the sum would be {total_sum:.0f}.  "
                      f"⭐ In parallel, not queued")
        print(f"   ⚠ unblock DECLARED, so as not to leave the field dirty: "
              f"{F.unblock(a.socket, a.address)}")

    elif a.case == "free":
        print("== the positive control: the unblock (§4.4-bis) and a real entry")
        r = F.unblock(a.socket, a.address)
        print(f"   -- unblock: {r}")
        male += report_it(r.startswith("REMOVED") or r.startswith("NOT-BANNED"),
                      f"the unblock command answered: {r}")
        n, m, ms, err = await attempt(a, a.user, password)
        male += report_it(n == "ADMITTED",
                      f"and with the RIGHT password you get in: {n} in {ms:.0f} ms  "
                      f"⭐ without this, every REJECTED above would be green "
                      f"for the wrong reason")

    print(f"\n== {'⭐ all as expected' if male == 0 else f'⛔ {male} checks out of place'}")
    return 0 if male == 0 else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--address", default="192.168.0.2")
    p.add_argument("--port", type=int, default=7531)
    p.add_argument("--user", default="prova")
    p.add_argument("--password-file", required=True)
    p.add_argument("--socket", default="")
    p.add_argument("--case", required=True,
                   choices=["second", "ban", "ban-after-restart", "dead",
                            "insieme", "libera"])
    a = p.parse_args()
    if F.AIOQUIC:
        print(f"   ⛔ «aioquic» is not there: {F.AIOQUIC}")
        sys.exit(2)
    password = F.password_from_file(a.password_file)
    try:
        sys.exit(asyncio.run(main(a, password)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
