#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-rete — THE DATAGRAM WHEN THE NETWORK IS NOT IDEAL.

⛔ What was open (`fasi/07-audio-e-appunti.md` §8): *«1024/1214 bytes are
   taken **on cable**; the user's judgement is on the **home network**, and holds for
   that»*.

⭐ Here there are two measurements, and they are different:

   1. **`casa`** — the test client runs ON THE LAPTOP, which is on **WiFi**
      (`wlo1`, 192.168.0.3), and the server is on the test machine, on cable.
      ⇒ The datagram really crosses the air: it is the «home network», not a
      simulation.  ⛔ No `tc`, no rule: we just look.

   2. **`netem`** — the network is broken ON PURPOSE, in steps, to find the point
      where the experience breaks.  ⛔ And here there is a constraint worth more than the
      measurement: **the rule must touch neither the ssh session nor the user's
      7730**.
      ⇒ The fault is put on **`lo`** of the test machine (the client runs
        inside the container, so its traffic goes through there), with a
        four-band `prio` and **two `u32` filters on port 7801 only**:
        all the rest of the local traffic stays in the default bands.
        ⛔ `enp7s0` — which carries ssh and the 7730 — **is never touched**.
      ⚠ And the price of this choice is declared: on `lo` the MTU is 65536, ⇒
        **this half does NOT remeasure «how many bytes a datagram carries»**.  That
        question can only be closed by a real client on a real network, and it is
        measurement 1.

⛔ THE DEFUSING IS AUTOMATIC: before applying any rule a detached
   guardian is launched which, after N seconds, removes the qdisc **even if
   this script dies or ssh drops**.  A machine left with `netem` on
   `lo` is a fault the next bench would attribute to the product.
   ⚠ And for eight profiles out of nine **this file did not respect it**: see the
     box of `rimetti`, cure of 23 August 2026.

⛔⛔ FOUR DEFECTS CURED ON 23 AUGUST 2026, and all four have the
    same form — **silence instead of red**, that is a plausible and
    false number in place of an «I did not read» or a red:
      1. `rimetti()` disarmed the guardian from step `0-liscio`, the FIRST
         ⇒ the eight after it ran uncovered.  ⇒ `rimetti(dillo, disarma)`.
      2. `a_non_si_apre` (`ricevuti == 0`) could not give red: the client
         prints `[audio] ricevuti 0` even from the `except` branch.  ⇒ replaced by
         `a_resa_sul_filo`, which looks at BOTH ends.  And the `[M]` hanging
         on it was false (`banchi/09-b78-apertura.py`).
      3. `spediti_dal_server` at `None` («I did not read the log») went through to the
         predicate as if everything were fine ⇒ now it is MUTE.
      4. Closing a session is SLOW (`[M]` up to 29 s more with the
         pacer queued) ⇒ the server's count was **from another run**, and the
         slot of §4.4-bis was still taken.  ⇒ `registro_posato()`.
    ⚠ R13 had been declared closed on this file, and four more cases came
      out of it: the form is not a defect, it is a habit of the bench.

⭐ `[M]` 23 August 2026, full run after the cures — **9 steps, 0 red, 0
   mute**, and the loss step now measures the wire:
   `7-perdita-10` ⇒ received **4 077** / sent by the server **4 504** =
   **0.905**, against `1-p` = 0.901 with `p` = **9.91 %** read from `tc -s qdisc`.

Usage (from the laptop):
    python3 banchi/07-b64-rete.py casa   [--secondi 30]
    python3 banchi/07-b64-rete.py netem  [--secondi 25]
    python3 banchi/07-b64-rete.py rimetti          # ⛔ and it is checked
"""
import argparse, json, os, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7801"))
UTENTE = os.environ.get("UTENTE", "provar7")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
UID_B = int(os.environ.get("UID_B", "1018"))
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
                                "84687524-93d6-4003-8cd1-1ed07aa63454/scratchpad/r7")

# ⛔ The interface that is NOT touched, written here so it can be seen:
VIETATA = "enp7s0"          # ssh and the user's 7730 go through it
DEV = "lo"                  # only local traffic goes through it, that is mine

# The steps, from the mildest to the nastiest.  ⭐ The expectation is written FIRST.
# ⛔⛔ R13 — THE «EXPECTED» WERE PROSE: printed, archived, NEVER compared.
#      Nine sentences describing what should have happened, and not one
#      line checking whether it had.  ⚠ A bench like that cannot give
#      red: whatever number comes out, the sentence next to it stays true «on reading».
#
# ⭐ Now every step carries a PREDICATE — a function that receives the numbers
#    and returns `(passa, perche)` — and the bench's verdict is their sum.
#    The script's exit is 0 only if all pass.
#
# ⛔ And the predicates are written BEFORE running, like the expectations of `07-b43`:
#    they are the prediction, and when they are wrong it shows (`LEZIONI.md` §1.11).


def _p(cond, perche):
    return (bool(cond), perche)


def a_pulito(n):
    """The denominator: almost everything arrives, nothing is discarded, the tone is pure."""
    return _p(n["resa"] is not None and n["resa"] >= 0.99
              and n["vecchi"] == 0 and (n["purezza"] or 0) >= 0.80,
              "yield >= 0.99 · stale 0 · purity >= 0.80")


def a_come_pulito(n):
    """A fixed delay does not reorder: it must be indistinguishable from the smooth one."""
    return a_pulito(n)


def a_sorpassi(minimo):
    """Jitter makes datagrams overtake each other, and §6.3 throws them away: «stale» MUST rise."""
    def f(n):
        return _p(n["vecchi"] >= minimo,
                  "stale >= %d (jitter reorders and §6.3 discards)" % minimo)
    return f


def a_perdita(frazione, tolleranza=0.5):
    """Loss shows in the yield, and in proportion to what netem removes."""
    def f(n):
        if n["resa"] is None:
            return _p(False, "no yield to compare")
        atteso = 1.0 - frazione
        return _p(abs(n["resa"] - atteso) <= tolleranza * frazione + 0.02,
                  "yield ~ %.3f (loss %.0f%%), seen %.3f"
                  % (atteso, frazione * 100, n["resa"]))
    return f


def a_resa_sul_filo(frazione, tolleranza=0.35):
    """THE YIELD MEASURED AT BOTH ENDS: how many the SERVER sent, how many
    the CLIENT received — and the comparison is with the loss `netem`
    **really** applied, read from `tc -s qdisc`, not with the one requested.

    ⛔⛔ THIS PREDICATE REPLACES `a_non_si_apre`, WHICH COULD NOT GIVE
       RED.  It was:

           def a_non_si_apre(n): return _p(n["ricevuti"] == 0, ...)

       and `banchi/01-b3-cliente.py:1466` (`scrivi_audio`) prints
       `[audio] ricevuti 0` **even from the `except` branch**, before re-raising.
       ⇒ **Every** way of failing — a `CONGEDO`, an expired ceiling, a
       `NameError` in the bench — gave «ricevuti 0» and passed the step as
       **green**.  It did not measure *«it does not open»*: it measured *«I did not receive»*,
       and the two look the same (`LEZIONI.md` §1.9).
    ⛔ And the `[M]` hanging on it — *«the session does not open at all in
       25 s»* — was **false**.  `[M]` 23 August 2026, `banchi/09-b78-apertura.py`:
       at 10 % loss the session opens **10 times out of 10 in 1.1 s**
       (median), at 25 % 10/10 in 1.3 s; the network costs **285 ms** between 0 and
       25 %, and the second that could be seen was the fixed delay of §4.4-bis.

    ⚠⚠ AND THE EXPECTED-LOSS CALCULATION IS NOT WHAT IT SEEMS — whoever
       retunes it without this note retunes it the wrong way.
       The two `u32` filters of `guasta()` take **both directions** (`sport` and
       `dport`), so:
         · a network **round trip** (there and back) pays `1-(1-p)²`
           ⇒ **19 %** when `p` = 10 %;
         · a **datagram**, which goes **one way only**, pays `p`
           ⇒ **10 %** when `p` = 10 %.
       Here we look at a datagram, not a round trip: the expected yield is **`1-p`**.
       `[M]` 23 August 2026 at `p` = 10 %: received **3 235**, sent by the
       server **3 607** ⇒ yield **0.897**, which is `1-p` (0.90), **not**
       `1-(1-p)²` (0.81).

    ⚠ And this yield is NOT the judge's `resa_campioni`: that one also counts
      the blocks the server **never** sent (window closed —
      `[M]` 391 out of 3 607 at 10 %), and so it adds up «lost on the wire» and «never
      sent», which are two facts.  Here the denominator is `spediti`.
    """
    def f(n):
        ric, sped = n.get("ricevuti"), n.get("spediti_dal_server")
        # ⛔ `CODER.md` §3.10: «I did not read» is not «zero», and it is red.
        if ric is None or not sped:
            return _p(False, "one end of the count is missing: received=%s · "
                             "sent by the server=%s" % (ric, sped))
        resa = ric / float(sped)
        vera = n.get("perdita_vera")
        p = vera if vera is not None else frazione
        atteso = 1.0 - p
        larghezza = tolleranza * p + 0.02
        return _p(abs(resa - atteso) <= larghezza,
                  "yield on the wire %d/%d = %.3f · expected 1-p = %.3f "
                  "(p %s = %.3f, ±%.3f)"
                  % (ric, sped, resa, atteso,
                     "read from tc" if vera is not None else "REQUESTED (tc mute)",
                     p, larghezza))
    return f


PROFILI = [
    ("0-liscio", [], "no fault: it is the denominator, and it must be clean",
     a_pulito),
    ("1-ritardo-30", ["delay", "30ms"],
     "30 ms fixed, no jitter: they arrive late but in order -- nothing must change",
     a_come_pulito),
    ("2-jitter-2", ["delay", "20ms", "2ms", "distribution", "normal"],
     "jitter 2 ms, less than one PCM block (5 ms): overtakes must already be there",
     a_sorpassi(100)),
    ("3-jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"],
     "jitter 5 ms = one block: overtakes grow",
     a_sorpassi(500)),
    ("4-jitter-10", ["delay", "20ms", "10ms", "distribution", "normal"],
     "jitter 10 ms = two blocks", a_sorpassi(1000)),
    ("5-jitter-15", ["delay", "30ms", "15ms", "distribution", "normal"],
     "jitter 15 ms = three blocks: here listening is already broken",
     a_sorpassi(1500)),
    ("6-perdita-1", ["loss", "1%"], "1 datagram out of 100 lost",
     a_perdita(0.01)),
    # ⛔ THE PROSE OF THIS STEP WAS FALSE and must be read as a warning:
    #    it said «10 %: `[M]` the session does not open at all in 25 s».
    #    `[M]` 23 August 2026 (`banchi/09-b78-apertura.py`): the session opens
    #    **10 times out of 10, median 1.1 s**; at 25 % 10/10 in 1.3 s.  The old
    #    `[M]` was the reflection of a predicate that could not give red.
    ("7-perdita-10", ["loss", "10%"],
     "10 %: `[M]` 23 Aug 2026 the session DOES OPEN (10/10, median 1.1 s) and the "
     "wire yields 1-p ~ 0.90 — received/sent at both ends, not 1-(1-p)²",
     a_resa_sul_filo(0.10)),
    ("8-casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                        "loss", "2%"],
     "the mix that resembles a home with distant WiFi", a_sorpassi(500)),
]


def rem(comando, tetto=120):
    """⛔ No redirection AROUND ssh: the sudo prompt goes to stderr
       and a redirect would eat it — the command would hang in silence."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=120):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()


def perdita_vera():
    """⛔ THE LOSS `netem` REALLY APPLIED, **read** and not deduced.

    ⚠ «I asked for 10 %» and «it threw away 10 %» are two different facts:
      `netem` drops at random, and over a few thousand packets the true fraction
      drifts.  The predicate is tuned on THIS one, or it would give red to the network
      instead of the product.
    ⛔ It is read BEFORE moving to the next step: the `tc qdisc del` with which
       the next profile opens resets the counters.
    Returns `None` when there is no `netem` (smooth step) or when the
    line cannot be read — ⛔ and `None` is NOT zero.
    """
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV)
    import re as _re
    dentro = False
    for riga in out.split("\n"):
        s = riga.strip()
        if s.startswith("qdisc netem"):
            dentro = True
            continue
        if dentro and s.startswith("qdisc"):
            break
        if dentro and "Sent" in s:
            m = _re.search(r"Sent \d+ bytes (\d+) pkt \(dropped (\d+)", s)
            if not m:
                return None
            passati, buttati = int(m.group(1)), int(m.group(2))
            tot = passati + buttati
            return round(buttati / float(tot), 4) if tot else None
    return None



# ── ⛔ THE GUARDIAN IS ARMED AND DISARMED BY PID, NOT BY PATTERN ─────────
GUARDIANO = LAV + "/.guardiano.pid"


def guardiano_arma(secondi):
    """Born with `setsid`: it leads its own group, and the group is killed whole."""
    guardiano_disarma()
    # ⛔ The `&` and the `echo $!` must run INSIDE root's shell, or the
    #    redirect to `$LAV` (which belongs to root) fails and the pid is not written:
    #    `[M]` the first run printed «pid ?», that is a guardian that could not
    #    have been disarmed by pid — the cure without its other half.
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIANO)
    print("   OK  guardian armed for %d s (pid %s): the network goes back as it was "
          "EVEN if I die" % (secondi, out.strip() or "?"))


def guardiano_disarma():
    """⛔ The GROUP is killed, so `sh` never reaches the `tc` line."""
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True, disarma=True):
    """⛔ And it is CHECKED: «I removed it» and «it is no longer there» are two different facts.

    ⛔⭐ `disarma` IS NOT A CONVENIENCE, AND HERE IS WHY IT EXISTS — whoever reads it
       without the reason removes it, and the defect comes back.
       `[M]` 23 August 2026, rereading: the profile `0-liscio` is the **first**
       of the grid, and to «break with no rule» it called
       `rimetti(False)` — which disarmed the guardian armed **two lines earlier**
       in `principale()`.  ⇒ The **eight following profiles** ran without a
       safety net: a death of the script (or a dropped ssh) from there on
       left the machine with `netem` on it, and the next bench would have
       attributed **to the product** a fault of mine.  It is written in the header
       of this very file (§«THE DEFUSING IS AUTOMATIC»), and the file did not
       respect it: silence instead of red, like the predicates of R13.
       ⇒ Whoever removes the qdisc **inside** a run passes `disarma=False`;
         only whoever closes the run (the `finally`, and the `rimetti` step from the
         command line) really disarms.
    ⚠ The signature stays compatible: `rimetti()` and `rimetti(dillo=False)` — the two
      forms used by `09-b70`, `09-b76` and `09-b79` — behave as before.
    """
    # ⛔ First the guardian is disarmed, THEN the qdisc is removed: the
    #    other way round would leave a window in which the guardian can fire on
    #    a `netem` that someone else has put there in the meantime.
    if disarma:
        guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q
    if dillo:
        print("   %s the qdisc of «%s» is now: %s"
              % ("OK " if ok else "NO ", DEV, q or "(none)"))
        # ⛔ And we declare that the forbidden interface was NEVER touched.
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return ok


def guasta(regole):
    """The fault, and ONLY on my traffic."""
    if not regole:
        # ⛔ `disarma=False`: we are INSIDE the run, and the guardian belongs to the whole
        #    run (see the box of `rimetti`).  With `rimetti(False)` the
        #    step `0-liscio` uncovered the eight steps after it.
        rimetti(False, disarma=False)
        return True, "(no fault)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem %s"
        % (DEV, " ".join(regole)),
        # ⛔ TWO filters, and the port is MINE: one for the datagrams going down
        #    (sport 7801) and one for what comes back up (dport 7801).
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4" % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4" % (DEV, PORTA),
    ]
    # (the guardian is armed ONCE only, in `principale`: see the note there)
    for c in passi:
        rc, out, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc refused «%s»: %s" % (c[-60:], err[:200])
    return True, qdisc()


def innesca_sessione(secondi=8):
    """⛔ The «remotix» sink is created by the CHILD, and the child is born when a
       client comes in: on a freshly started server `pw-play --target remotix` binds
       to nothing.  ⇒ A short session is opened on purpose; the stage and the
       sink outlive it (I4)."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 180)
    return "SESSIONE" in (out + err)


def tono_fabbrica(hz=440, secondi=70, ampiezza=0.5):
    """⛔ The tone is built HERE if missing, and the amplitude is KNOWN: the expected RMS
       is a calculation (A/sqrt2), not an estimate.  ⚠ And the file must be readable
       by the session's user, who is not root."""
    f = "%s/tono-%d.wav" % (LAV, hz)
    rc, out, _ = root("test -s %s && stat -c %%s %s || echo 0" % (f, f))
    if out.strip().isdigit() and int(out.strip()) > 48000 * secondi * 2:
        return f
    root("mkdir -p %s && chmod 755 %s" % (LAV, LAV))
    copione = (
        "import math,struct,wave;"
        "w=wave.open('%s','wb');w.setnchannels(2);w.setsampwidth(2);"
        "w.setframerate(48000);d=bytearray();"
        "[d.extend(struct.pack('<hh',v,v)) for v in "
        "[int(%f*math.sin(2*math.pi*%d*n/48000)*32767) for n in range(48000*%d)]];"
        "w.writeframes(bytes(d));w.close()" % (f, ampiezza, hz, secondi))
    root("python3 -c \"%s\" && chmod 644 %s" % (copione, f), 300)
    return f


def tono_accendi():
    tono_fabbrica()
    """⛔ The tone must play INSIDE the session, or the judge measures silence
       and the bench reports «rms 0» as if it were a network fault.
       ⚠ It happened on the first «casa» run: 5993 perfect datagrams and rms 0.0.
       ⭐ And «started» is not «playing»: we check that the graph has the links."""
    # ⛔ THE TONE REPEATS IN A LOOP, and the first draft did not.
    #   The file lasts ~55 s; the run of the profiles lasts three hundred.  From the second
    #   profile on the judge read rms 0.0 and zero purity -- that is
    #   "silence" -- next to perfect transport counters.  The NETWORK number
    #   stayed good, but the half that LISTENS had vanished without
    #   saying so, which is precisely trap 1 of this phase.
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus "
         "sh -c 'while :; do pw-play --target remotix %s/tono-440.wav; done' "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, UID_B, LAV))
    for _ in range(25):
        time.sleep(0.4)
        rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/07-b64-scena.py grafo"
                          % (UTENTE, UID_B, LAV, ALB))
        try:
            if json.loads(out).get("legami_in_ingresso", 0) > 0:
                return True
        except Exception:
            pass
    return False


def tono_spegni():
    # ⛔ the LOOP is killed too, not only the player: killing pw-play
    #   inside a `while :` makes it restart at once, and it is the same form as the
    #   defect of 07-b43 (`kill` on the wrapper instead of on the player).
    root("pkill -u %d -f 'while :; do pw-play'; pkill -u %d -x pw-play; true"
         % (UID_B, UID_B))


def cliente(nome, dove, secondi):
    """dove = 'portatile' (real WiFi) or 'contenitore' (loopback + netem)."""
    j = os.path.join(FUORI, nome + ".jsonl")
    t = os.path.join(FUORI, nome + ".txt")
    for f in (j, t, os.path.join(FUORI, nome + ".segnale")):
        try: os.remove(f)
        except Exception: pass
    if dove == "portatile":
        pf = os.path.join(FUORI, ".parola")
        if not os.path.exists(pf):
            print("⛔ %s is missing (0600, with the password of %s): I do NOT put it in argv (D12)"
                  % (pf, UTENTE))
            return None
        cmd = [os.environ.get("PY", "python3"), "-u",
               os.path.join(QUI, "01-b3-cliente.py"),
               "--indirizzo", IND, "--porta", str(PORTA), "--utente", UTENTE,
               "--parola-file", pf, "--audio-codec", "pcm",
               "--audio-scrivi", j, "--segnale", os.path.join(FUORI, nome + ".segnale"),
               "--resta", str(secondi)]
        p = subprocess.run(cmd, capture_output=True, timeout=secondi + 120)
        uscita = p.stdout.decode("utf-8", "replace")
        open(t, "w").write(uscita + p.stderr.decode("utf-8", "replace"))
    else:
        dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
                  "--utente %s --parola-file %s/parola --audio-codec pcm "
                  "--audio-scrivi %s/rete-%s.jsonl --resta %d"
                  % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, DENTRO_LAV,
                     nome, secondi))
        rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                            secondi + 180)
        uscita = out + err
        open(t, "w").write(uscita)
        # the JSONL is brought back
        subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                       "cat %s/rete-%s.jsonl\" > %s"
                       % (MACCHINA, PAROLA_SUDO, LAV, nome, j), shell=True)
    conti = {}
    for r in uscita.splitlines():
        if "[audio] received" in r or "[audio] discarded" in r:
            conti[r.strip()[:9]] = r.strip()
    return {"uscita_coda": uscita[-1200:], "conti": conti,
            "jsonl": j, "byte_jsonl": os.path.getsize(j) if os.path.exists(j) else 0}


def conta_conti_finali():
    """How many «audio of …, final count» lines there are NOW in the log."""
    rc, out, _ = root("grep -ac 'audio of .*final count' %s/registro.log || true"
                      % LAV)
    try:
        return int(out.strip())
    except Exception:
        return -1


def registro_posato(tetto=90.0, quiete=3.0):
    """⛔⛔ WE WAIT FOR THE PREVIOUS SESSION TO HAVE FINISHED CLOSING, and
       this avoids two faults in one — `[M]` 23 August 2026,
       found by running the bench after tonight's cures:

       1. **THE SERVER'S COUNT WAS FROM ANOTHER RUN.**  Closing a
          session is SLOW when the pacer has a queue (`[M]` the profile
          `7-perdita-10` took **29 s** more than the others to write its
          «final count»).  ⇒ `riga0` of the next run was taken BEFORE
          the line of the previous run was written, and `conti_del_server` — which
          takes the LAST line after `riga0` — read the one **of the previous
          run**.  `[M]` profiles 6, 7 and 8 all three reported
          «sent 4999 · refused 3 · deferred 7410», which was the count of
          **6**; the true count of 7 was 4632.  ⚠ And the predicate gave us
          red on someone else's denominator: 4152/4999 = 0.831 (red) against
          4152/4632 = **0.896** (green, and it is `1-p`).  ⛔ It is the same form
          as the defects cured tonight — a plausible and false number in place of
          an «I did not read».
       2. **THE SLOT WAS STILL TAKEN.**  Until the previous session has
          closed, §4.4-bis refuses the new one with
          `CONGEDO 0x0F GIA_ATTIVA_REMOTA` (`banchi/09-b78-apertura.py` §4:
          the lock lasts until `SILENZIO` = 30 s).  `[M]` the profile
          `8-casa-cattiva` died like that, and the `[audio] ricevuti 0` that came
          out of it is exactly the number the old `a_non_si_apre`
          would have called **green**.

    ⇒ We wait until the count of «final count» lines stays STILL for
      `quiete` seconds, and that count is returned: it is the `n0` from which the new run
      demands a line **of its own**.
    """
    n = conta_conti_finali()
    fermo, scade = 0.0, time.time() + tetto
    while time.time() < scade and fermo < quiete:
        time.sleep(1.0)
        m = conta_conti_finali()
        fermo = (fermo + 1.0) if m == n else 0.0
        n = m
    return n


def conti_del_server(riga0, n0=None, tetto=90.0):
    """⛔⛔ R13 — WITHOUT THIS THE BENCH WAS BLIND BY CONSTRUCTION.

       The client can say how many datagrams it received; it can **not** say how many
       left.  ⇒ «the network lost it» and «the server never
       sent it» gave the same number, and in a bench that breaks the NETWORK
       on purpose it is the distinction that matters more than any other:
       without it, a server defect would be attributed to `netem`.

       ⭐ The product already has the count, when the session closes:
       «N blocks sent, N dropped, N refused by ngtcp2, N deferred».
       Here it is read, and read ONLY from `riga0` on, so it belongs to this
       run and not to the one before.

       ⛔⛔ AND «AFTER `riga0`» IS NOT ENOUGH: see the box of `registro_posato`.
          If the session of the PREVIOUS run writes its «final count» after
          `riga0` has been taken, that line falls inside the window and is
          read as if it were mine.  ⇒ `n0` = how many «final count» lines
          there were when this run began, and here we **wait** for one more
          to appear.  If it does not appear, «NIENTE DA LEGGERE» — which is now
          MUTE, not green."""
    if n0 is not None:
        scade = time.time() + tetto
        while conta_conti_finali() <= n0:
            if time.time() >= scade:
                return {"esito": "NIENTE DA LEGGERE — in %d s this run wrote "
                                 "no «final count» of its own (session "
                                 "refused? still closing?)" % int(tetto)}
            time.sleep(1.0)
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final count' "
                      "| tail -1" % (riga0 + 1, LAV))
    r = out.strip()
    if not r:
        # ⛔ `CODER.md` §3.10: «I did not read» is not «zero».
        return {"esito": "NIENTE DA LEGGERE — no «final count» in this run"}
    import re as _re
    m = _re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                   r"(\d+) DEFERRED", r)
    if not m:
        return {"esito": "line found but unreadable", "riga": r[:160]}
    fuori = {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
             "rifiutati": int(m.group(3)), "rimandati": int(m.group(4))}
    # ⭐ And since the log is open, the VIDEO count is read too:
    #    it is the line the product learned to write on 22 August, and
    #    it carries the two numbers that used to be confused.
    rc, out2, _ = root("tail -n +%d %s/registro.log | grep -a 'video of .*final count' "
                       "| tail -1" % (riga0 + 1, LAV))
    m2 = _re.search(r"(\d+) frames delivered.*?(\d+) NOT SENT.*?"
                    r"(\d+) sent on the wire.*?(\d+) abandoned.*?and (\d+) ANNOUNCEMENTS",
                    out2.strip())
    if m2:
        fuori["video"] = {"consegnati": int(m2.group(1)),
                          "non_spediti": int(m2.group(2)),
                          "spediti": int(m2.group(3)),
                          "abbandonati": int(m2.group(4)),
                          "annunci_tela": int(m2.group(5))}
    return fuori


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def giudica(nome):
    j = os.path.join(FUORI, nome + ".jsonl")
    if not os.path.exists(j) or os.path.getsize(j) == 0:
        return {"esito": "NIENTE DA GIUDICARE — no blocks"}
    p = subprocess.run(["python3", os.path.join(QUI, "07-b64-orecchio.py"), j,
                        "--hz", "440"], capture_output=True)
    try:
        d = json.loads(p.stdout.decode())["nostro"]
    except Exception as e:
        return {"esito": "the judge did not answer: %s" % e}
    s = d["scoppiettii"]
    return {"blocchi": d["blocchi"], "resa_campioni": d.get("resa_campioni"),
            "buchi_istante": d["buchi_istante"], "scoppiettii": s["scoppiettii"],
            "scoppiettii_al_s": s["al_secondo"], "tono": d["tono"]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["casa", "netem", "rimetti", "stato"])
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--solo", default="", help="one profile only, by name")
    p.add_argument("--controllo-rosso", action="store_true",
                   help="⭐ the positive control OF THE VERDICT: the jitter "
                        "expectation is stuck onto step «0-liscio» (perfect network), "
                        "and on a clean line it CANNOT pass.  "
                        "⛔ If the bench stays green, the bench is blind and none "
                        "of its other greens is to be believed")
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        print("== the test machine's network")
        return 0 if rimetti() else 2

    if a.passo == "casa":
        print("== 1 · THE REAL HOME NETWORK — the client runs on the laptop, on WiFi")
        print("   --  laptop 192.168.0.3 (wlo1) → server %s:%d (cable)" % (IND, PORTA))
        print("   ⛔ no tc rule: nothing is simulated")
        if not tono_accendi():
            print("   NO  the tone is NOT playing inside the session: I stop,"
                  " instead of measuring silence and calling it network")
            tono_spegni(); return 2
        print("   OK  the tone plays: the graph has incoming links to the sink")
        try:
            c = cliente("casa", "portatile", a.secondi)
        finally:
            tono_spegni()
        if c is None:
            return 2
        for r in c["conti"].values():
            print("   ", r)
        print("   ", json.dumps(giudica("casa"), ensure_ascii=False))
        return 0

    print("== 2 · THE NETWORK BROKEN ON PURPOSE — netem on «%s», port %d only" % (DEV, PORTA))
    print("   ⛔ «%s» (ssh + the user's 7730) is NOT touched" % VIETATA)
    prima = qdisc()
    print("   --  «%s» before: %s" % (DEV, prima or "(none)"))
    # ⛔⛔ THE GUARDIAN IS ARMED ONCE ONLY, AND FOR THE WHOLE RUN.
    #
    #     The first draft armed one **per profile**, each with its own
    #     wait: the guardian of the first profile would have fired **in the middle of the
    #     third**, removing netem without saying so.  ⇒ I would have measured a healthy
    #     network believing it broken, and written «10 % loss cannot be heard».
    #     ⚠ It is the worst form of bench defect: it makes the product look
    #     good.  Found by rereading, before running.
    totale = (a.secondi + 120) * len(PROFILI) + 300
    guardiano_arma(totale)
    esiti = []
    if a.controllo_rosso:
        # ⛔ The expectation of the first step is replaced with one that is impossible on a clean
        #    network: «at least 100 datagrams discarded because
        #    overtaken» where there is no fault at all.
        for i, (nome, regole, testo, _pred) in enumerate(PROFILI):
            if nome.startswith("0-"):
                PROFILI[i] = (nome, regole,
                              "⛔ RED CONTROL: impossible expectation on purpose "
                              "(100 overtakes on a network without faults)",
                              a_sorpassi(100))
        print("   ⛔ RED CONTROL on: step «0-liscio» MUST fail")
    print("   --  opening a short session to bring the stage and the sink to life")
    if not innesca_sessione():
        print("   NO  the session does not open: I do not measure")
        rimetti(); return 2
    if not tono_accendi():
        print("   NO  the tone does not play: I do not measure")
        tono_spegni(); rimetti(); return 2
    print("   OK  the tone plays inside the session")
    try:
        for nome, regole, atteso, predicato in PROFILI:
            if a.solo and a.solo not in nome:
                continue
            print("\n-- %s · %s" % (nome, atteso))
            # ⛔ FIRST OF ALL: the session of the previous run must really be closed,
            #    or we read its count and get its slot slammed in our
            #    face (`CONGEDO 0x0F`).  See the box of `registro_posato`.
            n0 = registro_posato()
            riga0 = righe_registro()
            ok, q = guasta(regole)
            if not ok:
                # ⛔ R13: the `break` exited and the script returned 0 all the same.
                print("   ", q)
                esiti.append({"profilo": nome, "passa": False,
                              "perche": "tc refused the rule"})
                break
            # ⛔ M3 is rechecked at EVERY profile.  "The tone was playing
            #   at the start" is not "the tone is playing now".
            rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/"
                              "07-b64-scena.py grafo" % (UTENTE, UID_B, LAV, ALB))
            try:
                leg = json.loads(out).get("legami_in_ingresso", 0)
            except Exception:
                leg = -1
            print("    M3: incoming links to the sink = %s" % leg)
            if leg <= 0:
                print("   NO  the tone no longer plays: I do NOT judge this profile")
                esiti.append({"profilo": nome, "passa": None,
                              "esito": "NIENTE DA GIUDICARE, the tone was silent"})
                continue
            print("    tc:", " ".join(q.split("\n")[:2])[:160])
            c = cliente(nome, "contenitore", a.secondi)
            # ⛔ The TRUE loss is read NOW: the next step resets the
            #    `netem` counters with its `tc qdisc del`.
            pv = perdita_vera()
            g = giudica(nome)
            sv = conti_del_server(riga0, n0)
            for r in (c or {}).get("conti", {}).values():
                print("   ", r)
            print("    SERVER:", json.dumps(sv, ensure_ascii=False))
            print("    judgement:", json.dumps(g, ensure_ascii=False))

            # ⭐ AND HERE THE EXPECTATION STOPS BEING PROSE: it is compared.
            #    ⚠ The numbers the predicate looks at come from TWO sides — the
            #    client and the server — so «lost on the wire» and «never sent»
            #    are not confused.
            conti = (c or {}).get("conti", {})
            import re as _re

            def daconti(chiave, testo):
                for x in conti.values():
                    if chiave in x:
                        m = _re.search(testo, x)
                        return int(m.group(1)) if m else None
                return None

            numeri = {
                "ricevuti": daconti("received", r"received (\d+)"),
                "vecchi": daconti("discarded", r"old (\d+)"),
                "resa": g.get("resa_campioni"),
                "purezza": (g.get("tono") or {}).get("purezza"),
                "spediti_dal_server": sv.get("spediti"),
                # ⚠ The loss READ from `tc -s qdisc`, not the one requested:
                #   `a_resa_sul_filo` is tuned on this one (see its box).
                "perdita_vera": pv,
            }
            print("    netem: loss really applied = %s"
                  % ("%.2f %%" % (pv * 100) if pv is not None
                     else "(no qdisc, or not read)"))
            # ⛔⛔ AND IF THE SERVER'S COUNT WAS NOT READ, THE STEP IS MUTE.
            #     `[M]` 23 August 2026 — third case of the same form as the two
            #     cured tonight: `sv.get("spediti")` returns `None` when the
            #     «final count» is not in the log, `None == 0` is **false**,
            #     and the step went straight to the predicate.  ⇒ The predicates that
            #     do not look at the server (`a_pulito`, `a_sorpassi`) gave
            #     **green** on a run in which the server's end had not been
            #     read at all.  `CODER.md` §3.10: «I did not read» is not
            #     «zero», and here it is not even «green».
            if numeri["spediti_dal_server"] is None:
                passa, perche = None, ("NIENTE DA GIUDICARE: the SERVER's count "
                                       "was not read (%s)"
                                       % sv.get("esito", "?"))
            elif numeri["spediti_dal_server"] == 0:
                # ⛔ And if the server sent nothing, the red is NOT the network's.
                passa, perche = False, ("the SERVER sent nothing: the red "
                                        "does not belong to the broken network, it is ours")
            else:
                passa, perche = predicato(numeri)
            print("    %s EXPECTED: %s"
                  % ("OK " if passa else ("⚠ MUTO" if passa is None else "⛔ NO"),
                     perche))
            esiti.append({"profilo": nome, "regole": regole, "atteso": atteso,
                          "conti": conti, "server": sv, "giudizio": g,
                          "numeri": numeri, "passa": passa, "perche": perche,
                          "esito": perche if passa is None else None})
    finally:
        tono_spegni()
        print("\n== ⛔ THE NETWORK IS PUT BACK AS IT WAS")
        guardiano_disarma()
        rimetti()
    json.dump(esiti, open(os.path.join(FUORI, "rete-esiti.json"), "w"),
              ensure_ascii=False, indent=1)

    # ⛔⛔ R13 — AND THE OUTCOME PROPAGATES.  Before, `principale()` returned 0 in every
    #      case, `break` included: a bench that cannot give red is not a
    #      bench, it is a report.
    rossi = [e for e in esiti if e.get("passa") is False]
    muti = [e for e in esiti if e.get("passa") is None]
    print("\n== THE VERDICT — %d steps, %d red, %d not judged"
          % (len(esiti), len(rossi), len(muti)))
    for e in rossi:
        print("   ⛔ %s: %s" % (e["profilo"], e.get("perche")))
    for e in muti:
        print("   ⚠  %s: %s" % (e["profilo"], e.get("esito")))
    if rossi:
        return 1
    if muti:
        return 2      # ⚠ «I did not measure» is an outcome of ITS OWN, not a green
    print("   ⭐ all the steps did what was written beforehand")

    return 0


if __name__ == "__main__":
    sys.exit(principale())
