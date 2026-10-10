#!/usr/bin/env python3
"""02-figlio-prova.py — the bench of `DECISIONI.md` §1.10-bis: **one child per user**.

    python3 02-figlio-prova.py --previsione
    python3 02-figlio-prova.py --caso nasce --porta 7571 \\
        --pid-server 12345 --registro /srv/remotix/tmp/02-figlio/registro.log \\
        --utente nicfio --parola-file /srv/src/tmp/02-figlio-parola

⛔ IT RUNS INSIDE THE CONTAINER AND AS ROOT.  Inside because `aioquic` lives there; as
   root because half of the readings are on `/proc` of a root process — and
   ⛔ **«I could not read» is not «it was not there»** (`LEZIONI.md` §1.9), so
   a bench that cannot read exits **2** instead of printing a green.

⚠ `/proc` inside the container IS the host's (`enter.sh` mounts it), so
  the processes looked at are the server's real ones.

---------------------------------------------------------------------------
⛔ WHAT IT PROVES, AND WHY LOOKING AT THE LOG IS NOT ENOUGH

The product writes in the log *«I am the child of «nicfio»: uid 1000»*.  ⛔ A
bench that settled for that line **would prove nothing**: it is the
process declaring itself, and it is exactly the thing §1.10-bis says not to
believe — *«a child running as the wrong user is I3 violated
invisibly»*.

⇒ Here identity is ASKED OF THE KERNEL, in two independent ways:

  · `/proc/<pid>/status`, field `Uid:`, which carries **four** numbers — real,
    effective, saved, filesystem.  ⛔ All four are looked at: a
    process with `Uid: 1000 1000 0 1000` is a process that **can go back to
    root**, and it would be green for whoever reads only one;
  · the credentials the kernel stamps on every message (`SO_PASSCRED`), which
    the PARENT compares at every message — and which this bench puts to the test
    with the `cieco` fault, where they are the only wall left.

---------------------------------------------------------------------------
⛔ THE SIX TESTS, AND THE OPPOSITE CASE OF EACH

  | case          | what must happen                   | the opposite case      |
  |---------------|------------------------------------|------------------------|
  | `nasce`       | one child, the user's uid, with bus| no child, or the       |
  |               | and WITHOUT the server's port      | parent's bus           |
  | `due`         | two connections, ONE child (I2)    | two children           |
  | `distacco`    | the client leaves, the child LIVES | the child dies with    |
  |               | with the SAME pid (I4)             | the detach             |
  | `muore`       | child killed, the parent REAPS it   | a zombie that looks    |
  |               | and says so                         | the same as a live     |
  |               |                                     | process                |
  | `senza-palco` | user without `/run/user/<uid>`:    | the child takes        |
  |               | the child is born, SAYS SO, and has | someone else's stage   |
  |               | no stage                            |                        |
  | `guasto-uid`  | the child does not drop: it notices | runs as root and       |
  |               | BY ITSELF and dies (exit 42)        | delivers pixels        |
  | `guasto-cieco`| the child does not drop and does not| the parent trusts it   |
  |               | notice: THE PARENT takes it down, on| and delivers root's    |
  |               | the kernel's credentials            | pixels to who got in   |

---------------------------------------------------------------------------
⛔ THE B0 RULES THIS BENCH OWES

  B0.1 the initial state is declared **and checked**: the server pid, who
       owns it, how many children there already are, and the log from which offset;
  B0.3 this bench authenticates, so **it bans**: the ban file is its own, and
       failed attempts are counted.  ⚠ None are made on purpose here;
  B0.4 the expectation is compared by the bench: **0** all as expected · **1** at least
       one test gave something else · **2** it could not be measured;
  B0.7 markers, not `sleep`: the log is read from an **offset** taken
       before every test, so what is counted belongs to this round.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ The expectation is written BEFORE the round, and printed with `--previsione`: an expectation
#    written after seeing the number is not an expectation.
PREVISIONE = """
⛔ THE EXPECTATION, written before the round — `DECISIONI.md` §1.10-bis

 1. `nasce`  ⭐ after «nicfio» is AMMESSO there exists **one** child process of the
    server, and:
      · `/proc/<pid>/status` says `Uid: 1000 1000 1000 1000` — all four,
        because a saved-uid at 0 is a process that can go back to root;
      · its command line starts with `remotix-figlio --figlio-interno`;
      · ⛔ it has **4 descriptors** (0,1,2 and the socket to the parent) and has NO
        socket in common with the parent besides that one: it did not take port 7571
        along with it;
      · in the log there is «THE SESSION BUS IS MINE», and the parent has never
        written anything of the kind.
 2. `due`  ⭐ two connections of the same user ⇒ **a single child**, the
    same pid, and in the log «a second one is NOT born — invariant I2».
 3. `distacco`  ⭐ the client closes, and after 5 s the child is **still alive**,
    same pid, state NOT `Z`.  ⛔ If it died, I4 would be broken.
 4. `muore`  ⭐ `SIGKILL` to the child ⇒ the parent reaps it (the pid **disappears**
    from /proc, it does not stay `Z`), writes «is leaving», and a new connection makes
    a child be born with a **different** pid.
 5. `senza-palco`  ⭐ «prova» (uid 1001, without /run/user/1001) gets in: the child
    IS BORN as uid 1001 and writes «I do NOT have the session bus».  ⛔ And it does not see
    anybody else's desktop.
 6. `guasto-uid`  ⛔ with `setuid` removed, the child exits **42** and in the log
    there is «I AM NOT WHO I SHOULD BE».  No frame.
 7. `guasto-cieco`  ⛔ with `setuid` removed AND the child's check removed,
    it is the PARENT that takes it down: «MESSAGE REFUSED», with «the kernel says
    uid 0» inside.  ⛔ If this case were green without that line, it would mean that
    the parent trusts what the child declares.

⛔ THE OPPOSITE CASE OF THE WHOLE BENCH — what a product that does NOT
   do what §1.10-bis asks would look like: a child with `Uid: 0 0 0 0` that delivers
   frames anyway, and a log full of ⭐.  ⇒ That is why the bench reads
   `/proc` and not the log.
"""


def dico(t=""):
    print(t, flush=True)


def ok(t):
    dico(f"    \033[1;32mOK\033[0m  {t}")


def ko(t):
    dico(f"    \033[1;31mNO\033[0m  {t}")


def inf(t):
    dico(f"    --  {t}")


def titolo(t):
    dico(f"\n\033[1m== {t}\033[0m")


# ---------------------------------------------------------------------------
# The readings from the KERNEL.  ⛔ Each tells «it is not there» from «I could not
#    read», and the second is a `None` the caller must treat as an
#    «I did not measure» — never as a zero.


def leggi(percorso):
    try:
        with open(percorso, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return b""          # it is not there
    except PermissionError:
        return None         # ⛔ I could NOT read: it is a different fact
    except OSError:
        return None


def stato_proc(pid):
    """The four uids, the four gids and the state, asked of the kernel."""
    b = leggi(f"/proc/{pid}/status")
    if b is None:
        return None
    if not b:
        return {}
    fuori = {}
    for riga in b.decode("utf-8", "replace").splitlines():
        if riga.startswith("Uid:"):
            fuori["uid"] = [int(x) for x in riga.split()[1:5]]
        elif riga.startswith("Gid:"):
            fuori["gid"] = [int(x) for x in riga.split()[1:5]]
        elif riga.startswith("State:"):
            fuori["stato"] = riga.split()[1]
        elif riga.startswith("PPid:"):
            fuori["ppid"] = int(riga.split()[1])
    return fuori


def cmdline(pid):
    b = leggi(f"/proc/{pid}/cmdline")
    if b is None:
        return None
    return b.replace(b"\x00", b" ").decode("utf-8", "replace").strip()


def descrittori(pid):
    """{fd: target}.  ⛔ `None` = I could not look."""
    try:
        elenco = os.listdir(f"/proc/{pid}/fd")
    except (PermissionError, OSError):
        return None
    fuori = {}
    for n in elenco:
        try:
            fuori[int(n)] = os.readlink(f"/proc/{pid}/fd/{n}")
        except OSError:
            fuori[int(n)] = "(vanished while I was looking)"
    return fuori


def figli_di(pid_padre):
    """The server's «--figlio-interno» children, asked of /proc.

    ⛔ `pgrep remotix` is NOT used: it would also catch the servers of the other
       benches (7448, 7501, 7561), and a bench that counts someone
       else's processes measures the machine and not the product.
    """
    fuori = []
    for n in os.listdir("/proc"):
        if not n.isdigit():
            continue
        s = stato_proc(n)
        if not s or s.get("ppid") != int(pid_padre):
            continue
        riga = cmdline(n)
        if not riga or "--figlio-interno" not in riga:
            continue
        pezzi = riga.split()
        fuori.append({
            "pid": int(n),
            "argv": riga,
            "utente": pezzi[2] if len(pezzi) > 2 else "?",
            "uid": s.get("uid"),
            "gid": s.get("gid"),
            "stato": s.get("stato"),
            "fd": descrittori(n),
        })
    return fuori


class Registro:
    """The server's log, read from an OFFSET — B0.7.

    ⛔ Reading it from the start would count yesterday's lines.  And `dimensione()` is
       taken BEFORE every test, not after.
    """

    def __init__(self, percorso):
        self.percorso = percorso
        self.leggibile = os.path.exists(percorso)

    def offset(self):
        try:
            return os.path.getsize(self.percorso)
        except OSError:
            return None

    def da(self, off):
        if off is None:
            return None
        try:
            with open(self.percorso, "rb") as f:
                f.seek(off)
                return f.read().decode("utf-8", "replace")
        except OSError:
            return None


def aspetta(cond, secondi=15.0, passo=0.2):
    """Markers, not `sleep`: a CONDITION is waited for, and how long is said."""
    t0 = time.time()
    while time.time() - t0 < secondi:
        v = cond()
        if v:
            return v, time.time() - t0
        time.sleep(passo)
    return None, time.time() - t0


def cliente(a, attesa=6.0, utente=None, parola=None):
    """One round of the independent RCP client (`02-filo-cliente.py`).

    ⭐ A client is not rewritten: that one is already a certified referee of F2.4,
       and using it here means that «the session reaches SESSIONE» is said by a
       program that is not this bench.
    """
    parola_file = None
    if parola is not None:
        # ⛔ D12: the password never goes through `argv`.
        parola_file = os.path.join(a.lavoro, "parola-caso")
        vecchia = os.umask(0o077)
        try:
            with open(parola_file, "w") as f:
                f.write(parola)
        finally:
            os.umask(vecchia)
    cmd = [sys.executable, os.path.join(QUI, "02-filo-cliente.py"),
           "--indirizzo", a.indirizzo, "--porta", str(a.porta),
           "--utente", utente or a.utente,
           "--parola-file", parola_file or a.parola_file,
           # ⛔ `--codec 1`, and not 2: that number tells the judge **what to
           #    expect**, and the negotiation of §4.3 is done by the `CIAO` of
           #    `01-b3-cliente.py`, which declares two codecs and gets
           #    HEVC as the answer.  ⚠ `[M]` 12 Aug 2026, first round: with
           #    `--codec 2` the client said «ERRORE_PROTOCOLLO: codec 1, but
           #    2 had been negotiated» — that is a red pointed at the SERVER for one
           #    line of this bench.  It is the second time this client
           #    accuses the server (`P2-6-montaggio.md` §5.2), and the second time
           #    it was wrong.
           "--codec", "1", "--attesa", str(attesa)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=attesa + 90)
    if parola_file:
        try:
            os.unlink(parola_file)
        except OSError:
            pass
    return p


# ---------------------------------------------------------------------------
# The cases


def caso_nasce(a, reg, guai):
    titolo("1. `nasce` — one child, running AS THE USER (asked of the kernel)")
    off = reg.offset()
    prima = figli_di(a.pid_server)
    inf(f"children before: {len(prima)}")
    # ⛔ THE SCENE OF THIS CASE IS «A SERVER JUST STARTED», and it is CHECKED
    #    instead of hoped for: with a child already alive, I2 does the right thing —
    #    a second one is not born — and this case would see neither the
    #    introduction nor the bus line.  ⚠ It would be a RED on a healthy
    #    product, and it is the defect the bench can inflict on itself.
    if prima:
        ko(f"⛔ there is already {len(prima)} live child: this case wants a server "
           f"JUST STARTED.  I do not measure, and I do not print a green — redo "
           f"«riaccendi» and then «misura nasce».")
        guai.append("nasce: wrong scene (a child was already there)")
        return

    p = cliente(a)
    inf(f"the client exited {p.returncode}")
    for r in p.stdout.splitlines():
        if "SESSIONE" in r or "frames" in r or "ACCETTATO" in r:
            inf(r.strip())

    dopo, quanto = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not dopo:
        ko("⛔ NO child after an admitted login: §1.10-bis is not alive")
        guai.append("nasce: no child")
        return
    ok(f"{len(dopo)} child after {quanto:.1f} s")

    g = dopo[0]
    atteso = int(a.uid_atteso)
    if g["uid"] is None:
        ko("⛔ I COULD NOT read the child's uids: it is not a green and it is not")
        ko("   a red — it is «I did not measure».  Root is needed.")
        guai.append("nasce: uids not readable")
        return
    if g["uid"] == [atteso] * 4:
        ok(f"⭐ the kernel says Uid: {g['uid']} — real, effective, SAVED and fs, "
           f"all four at {atteso}")
    else:
        ko(f"⛔ Uid: {g['uid']}, expected [{atteso}]*4.  ⚠ A different saved-uid is "
           f"a process that can go back to root")
        guai.append(f"nasce: uid {g['uid']}")
    if g["gid"] == [int(a.gid_atteso)] * 4:
        ok(f"⭐ and Gid: {g['gid']}")
    else:
        ko(f"⛔ Gid: {g['gid']}, expected [{a.gid_atteso}]*4")
        guai.append(f"nasce: gid {g['gid']}")

    if g["argv"].split()[0].endswith("remotix-figlio"):
        ok(f"the command line declares it: «{g['argv'][:90]}»")
    else:
        ko(f"⛔ unexpected argv[0]: «{g['argv'][:90]}»")
        guai.append("nasce: argv")

    # ⛔ IT DID NOT TAKE THE PORT ALONG — and it is not a deduction.
    fdp = descrittori(a.pid_server)
    if g["fd"] is None or fdp is None:
        ko("⛔ I could not read the descriptors: I do not say the port is not "
           "there.  ⚠ «I did not look» is not «it was not there» (LEZIONI.md §1.9)")
        guai.append("nasce: fds not readable")
    else:
        inf(f"the parent has {len(fdp)} descriptors, the child {len(g['fd'])} "
            f"(⚠ NOW: after it has opened the stage)")
        for n, t in sorted(g["fd"].items())[:6]:
            inf(f"    fd {n} → {t}")
        comuni = set(g["fd"].values()) & set(fdp.values())
        # ⚠ 0,1,2 are the same log on purpose: it is what makes readable
        #   «who said what».  What must NOT be there is a socket
        #   of the parent — the port, or the unblock command socket.
        socket_comuni = {v for v in comuni if v.startswith("socket:")}
        if not socket_comuni:
            ok(f"⭐ ZERO sockets in common with the parent: it did NOT take port {a.porta} "
               f"along with it")
        else:
            ko(f"⛔ {len(socket_comuni)} sockets in common with the parent: "
               f"{sorted(socket_comuni)}")
            guai.append("nasce: sockets inherited from the parent")
        # ⛔⭐ AND THE NUMBER THAT COUNTS IS THE ONE AT BIRTH, NOT THE ONE NOW
        #     — defect of THIS BENCH, found in the first round, 12 Aug 2026.
        #
        #     The first draft required «≤ 4 descriptors» and gave a red to
        #     a healthy product: `[M]` the child had **34**, and the thirty
        #     extra were PipeWire, the bus, the eventfds and the memfds of
        #     `mutter-screen-cast` — that is **the stage**, that is exactly the
        #     thing this mandate exists to give it.
        #
        # ⇒ The real quantity is *«how many it had when it was born»*, and the
        #   product COUNTS it by itself right after the `exec`, before opening
        #   anything: the «N open descriptors» line of the message with which it
        #   introduces itself.  ⚠ It is `LEZIONI.md` §1.13: name the real quantity
        #   of the phenomenon, not the one that resembles it.
        m = re.search(r"introduces itself:.*?(\d+) open descriptors",
                      reg.da(off) or "")
        if not m:
            ko("⛔ the child did not say how many descriptors it had at birth: "
               "without that number «it did not take the port along» remains "
               "a hope")
            guai.append("nasce: no descriptor count at birth")
        elif int(m.group(1)) == 4:
            ok("⭐ and AT BIRTH it had 4: 0, 1, 2 and the socket to the "
               "parent.  ⛔ The parent has "
               f"{len(fdp)} — none of its own went across")
        else:
            ko(f"⛔ at birth it had {m.group(1)}, not 4: something of the "
               f"parent reached the child")
            guai.append(f"nasce: {m.group(1)} descriptors at birth")

    testo = reg.da(off) or ""
    if "THE SESSION BUS IS MINE" in testo:
        ok("⭐ and in the log: «THE SESSION BUS IS MINE» — the thing root "
           "cannot do")
    else:
        ko("⛔ the child did NOT say it has the bus.  The «figlio» lines:")
        for r in testo.splitlines():
            if " figlio " in r:
                inf(r.strip()[:160])
        guai.append("nasce: no bus")
    if "complete frame from" in testo:
        ok("⭐ and a frame arrived from the child to the parent")
    else:
        inf("⚠ no frame from the child in this window: look at the "
            "«figlio»/«video» lines above for the reason")


def caso_due(a, reg, guai):
    titolo("2. `due` — two connections of the same user, ONE single child (I2)")
    off = reg.offset()
    prima = figli_di(a.pid_server)
    if not prima:
        cliente(a)
        prima, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not prima:
        ko("⛔ not even the first child is there: I could not measure")
        guai.append("due: no first child")
        return
    pid1 = prima[0]["pid"]
    inf(f"the current child is pid {pid1}")

    p = cliente(a)
    inf(f"second connection: the client exited {p.returncode}")
    time.sleep(1.0)
    dopo = figli_di(a.pid_server)
    if len(dopo) == 1 and dopo[0]["pid"] == pid1:
        ok(f"⭐ a single child, and the SAME pid {pid1}: I2 holds, and the stage is "
           f"the same because it belongs to the session (I4)")
    else:
        ko(f"⛔ after the second connection the children are {len(dopo)}: "
           f"{[x['pid'] for x in dopo]}")
        guai.append("due: more than one child")
    testo = reg.da(off) or ""
    if "a second one is NOT born" in testo:
        ok("⭐ and the product says so: «a second one is NOT born — invariant I2»")
    else:
        ko("⛔ the product did not write the I2 line: the right behaviour "
           "without the line is a behaviour nobody can check")
        guai.append("due: I2 line missing")


def caso_distacco(a, reg, guai):
    titolo("3. `distacco` — the client leaves, the stage STAYS (I4)")
    prima = figli_di(a.pid_server)
    if not prima:
        cliente(a)
        prima, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not prima:
        ko("⛔ no child: I could not measure")
        guai.append("distacco: no child")
        return
    pid1 = prima[0]["pid"]
    inf(f"the child is pid {pid1}; the client has already disconnected "
        f"(its process has ended)")
    inf("waiting 6 s with NO live connection…")
    time.sleep(6.0)
    s = stato_proc(pid1)
    if s is None:
        ko("⛔ I could not read the child's state")
        guai.append("distacco: state not readable")
        return
    if not s:
        ko(f"⛔ the child {pid1} IS GONE after the detach: invariant I4 "
           f"is broken — the stage belonged to the connection")
        guai.append("distacco: the child died")
        return
    if s.get("stato") == "Z":
        ko(f"⛔ the child {pid1} is a ZOMBIE: «alive» and «dead» look the "
           f"same in /proc, and it is the defect already paid for with the helper")
        guai.append("distacco: zombie")
        return
    ok(f"⭐ the child {pid1} is still alive (state {s['stato']}), uid {s['uid']}: "
       f"the stage belongs to the SESSION, not to the connection (I4)")


def caso_muore(a, reg, guai):
    titolo("4. `muore` — child killed, the parent REAPS it and says so")
    off = reg.offset()
    prima = figli_di(a.pid_server)
    if not prima:
        cliente(a)
        prima, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not prima:
        ko("⛔ no child: I could not measure")
        guai.append("muore: no child")
        return
    pid1 = prima[0]["pid"]
    inf(f"killing the child {pid1} with SIGKILL — so it cannot say goodbye "
        f"to anyone and no handler can answer in its place")
    try:
        os.kill(pid1, signal.SIGKILL)
    except OSError as e:
        ko(f"⛔ I could not kill it: {e}")
        guai.append("muore: kill failed")
        return

    def sparito():
        s = stato_proc(pid1)
        if s is None:
            return None
        if not s:
            return "vanished"
        if s.get("stato") == "Z":
            return None      # ⛔ zombie: it is NOT «reaped»
        return None

    v, quanto = aspetta(sparito, 15)
    if v:
        ok(f"⭐ pid {pid1} vanished from /proc after {quanto:.1f} s: the parent "
           f"REAPED it, and «dead» no longer looks the same as «alive»")
    else:
        s = stato_proc(pid1) or {}
        ko(f"⛔ after {quanto:.1f} s pid {pid1} is still there, state "
           f"{s.get('stato')}: if it is `Z` it is an unreaped zombie")
        guai.append("muore: not reaped")

    testo = reg.da(off) or ""
    if "is leaving" in testo and "killed by signal 9" in testo:
        ok("⭐ and the log says so with the cause: «killed by signal 9»")
    else:
        ko("⛔ the log does not name the cause of death")
        guai.append("muore: cause not written")
    if "EMPTIED" in testo:
        ok("⭐ and the video store was EMPTIED: a user's image "
           "does not stay in the house after their stage has died")
    else:
        inf("⚠ no «EMPTIED»: either the store was not theirs, or it was not there")

    off2 = reg.offset()
    p = cliente(a)
    inf(f"new connection: the client exited {p.returncode}")
    nuovi, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not nuovi:
        ko("⛔ after the child's death no new one is born: the slot "
           "stayed occupied by a dead one")
        guai.append("muore: not reborn")
    elif nuovi[0]["pid"] != pid1:
        ok(f"⭐ a new one was born, pid {nuovi[0]['pid']} ≠ {pid1}")
    else:
        ko("⛔ the pid is the same: something does not add up")
        guai.append("muore: same pid")


def caso_senza_palco(a, reg, guai):
    titolo("5. `senza-palco` — a user who does NOT have the bus")
    off = reg.offset()
    p = cliente(a, utente=a.utente2, parola=a.parola2)
    inf(f"the client of «{a.utente2}» exited {p.returncode}")
    for r in p.stdout.splitlines():
        if "SESSIONE" in r or "frames" in r or "AMMESSO" in r:
            inf(r.strip())
    # ⛔⭐ THE TEST THAT COUNTS IN THIS CASE, and the first draft did NOT do it:
    #     «prova» must see **nothing**.  `[M]` 12 Aug 2026, first round:
    #     it saw ONE, conforming — and it was «nicfio»'s desktop, served from the
    #     PROCESS store of `webtransport.c`.  ⛔ Not «you receive nothing»:
    #     **you receive someone else's desktop**, which is I3 violated
    #     invisibly.  ⇒ This line is the only one that can see it.
    visti = 0
    for r in p.stdout.splitlines():
        m = re.search(r"(\d+) frames, all conforming", r)
        if m:
            visti = int(m.group(1))
    if visti == 0:
        ok(f"⭐⭐ «{a.utente2}» saw ZERO frames: «{a.utente}»'s desktop did NOT "
           f"reach them")
    else:
        ko(f"⛔⛔ «{a.utente2}» received {visti} frames, and their stage "
           f"did not produce even one ⇒ they belong to ANOTHER user.  "
           f"Invariant I3 violated invisibly.")
        guai.append("senza-palco: PIXEL LEAK between users")
    dopo, _ = aspetta(
        lambda: [x for x in figli_di(a.pid_server) if x["utente"] == a.utente2]
        or None, 20)
    if not dopo:
        ko(f"⛔ no child for «{a.utente2}»: the session was admitted and "
           f"the stage was not even ATTEMPTED")
        guai.append("senza-palco: no child")
        return
    g = dopo[0]
    ok(f"⭐ «{a.utente2}»'s child is there: pid {g['pid']}, Uid: {g['uid']}")
    if g["uid"] and g["uid"][0] != int(a.uid_atteso):
        ok(f"⭐ and it is NOT «{a.utente}»'s uid ({a.uid_atteso}): two users, two "
           f"identities — which is the whole mandate")
    else:
        ko("⛔ the two users have the same uid: this bench proves nothing")
        guai.append("senza-palco: same uid")
    testo = reg.da(off) or ""
    if "I do NOT have the session bus" in testo:
        ok("⭐ and the child SAYS it has no bus, instead of staying silent: «I could "
           "not look» is not «there is no session»")
    else:
        ko("⛔ the child did not declare the absence of the bus")
        guai.append("senza-palco: absence not declared")
    if "NON entra in deposito" in testo:
        ok("⭐ and had it delivered, someone else's store would have "
           "refused it (the guard of `main.c`)")

def caso_guasto(a, reg, guai, cieco):
    nome = "guasto-cieco" if cieco else "guasto-uid"
    titolo(f"{'7' if cieco else '6'}. `{nome}` — a child running as the "
           f"WRONG user")
    off = reg.offset()
    p = cliente(a)
    inf(f"the client exited {p.returncode}")
    time.sleep(3.0)
    vivi = figli_di(a.pid_server)
    testo = reg.da(off) or ""

    if vivi:
        s = vivi[0]["uid"]
        ko(f"⛔⛔ there is a LIVE child with Uid: {s} while the fault is injected: "
           f"neither of the two walls bit")
        guai.append(f"{nome}: live child")
    else:
        ok("⭐ no live child: the fault was stopped")

    if cieco:
        if "MESSAGE REFUSED" in testo and "the kernel says uid 0" in testo:
            ok("⭐⭐ and what stopped it was THE PARENT, on the credentials stamped "
               "by the kernel: «MESSAGE REFUSED … the kernel says uid 0»")
        else:
            ko("⛔ the parent did NOT refuse on the kernel's stamp: the check "
               "at every message did not bite, and this case is the only one that "
               "can see it")
            guai.append("guasto-cieco: no refusal by the parent")
    else:
        # ⛔ THE CHILD'S WALLS ARE TWO, and the bench accepts both: the
        #    same check — `getresuid()` — sits BEFORE the `exec` (exit
        #    35) and AFTER (exit 42).  `[M]` 12 Aug 2026: the one that bit was
        #    the first, and the bench required the words of the second.  ⚠ What
        #    counts is not WHICH wall: it is that the cause is NAMED — «it exited
        #    with 35» is not a diagnosis, «DID NOT DROP to the user» is.
        if "DID NOT DROP to the user" in testo or "IS NOT WHO IT SHOULD" in testo:
            ok("⭐ and what stopped it was the child itself, rereading its own "
               "uids from the kernel — and the parent wrote down the CAUSE, not the "
               "number")
        else:
            ko("⛔ the child did not notice it had not dropped, or the parent "
               "did not name the cause")
            guai.append("guasto-uid: no check by the child")
    for r in testo.splitlines():
        if " figlio " in r and ("⛔" in r or "NOT" in r):
            inf(r.strip()[:170])


CASI = {
    "nasce": caso_nasce,
    "due": caso_due,
    "distacco": caso_distacco,
    "muore": caso_muore,
    "senza-palco": caso_senza_palco,
    "guasto-uid": lambda a, r, g: caso_guasto(a, r, g, False),
    "guasto-cieco": lambda a, r, g: caso_guasto(a, r, g, True),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--previsione", action="store_true")
    p.add_argument("--caso", default="nasce")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7571)
    p.add_argument("--pid-server", type=int, default=0)
    # ⛔ THE PID IS READ FROM THE FILE, NOT FROM A SHELL SUBSTITUTION.
    #    ⚠ `p=$(cat …)` inside `ssh → enter.sh → bash -lc` crosses THREE
    #    levels of quotes and dies halfway: `[M]` 12 Aug 2026, this
    #    bench, first round — the `$(…)` arrived empty and `argparse` said
    #    «expected one argument».  It is the same form that has already run
    #    a case «the helper is dead» on a LIVE helper
    #    (`PAM-filo-unico.md` §6).  ⇒ A file has no levels of quotes.
    p.add_argument("--pid-file", default="")
    p.add_argument("--registro", default="")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--uid-atteso", default="1000")
    p.add_argument("--gid-atteso", default="1000")
    p.add_argument("--parola-file", default="")
    p.add_argument("--utente2", default="prova")
    p.add_argument("--parola2", default="parola-di-prova")
    p.add_argument("--lavoro", default="/srv/src/tmp")
    p.add_argument("--uscita", default="")
    a = p.parse_args()

    if a.previsione:
        dico(PREVISIONE)
        return 0

    if a.pid_file:
        try:
            with open(a.pid_file) as f:
                a.pid_server = int(f.read().strip())
        except (OSError, ValueError) as e:
            ko(f"⛔ the pid file «{a.pid_file}» cannot be read: {e}.  ⚠ It is not "
               f"«the server is not there»: it is «I could not look», and without the "
               f"pid every reading of /proc would be of a random process.")
            return 2

    titolo("0. The initial state, declared AND checked (B0.1)")
    if os.geteuid() != 0:
        ko("⛔ this bench wants root: half of the readings are on /proc of a "
           "root process, and «I could not read» is not «it was not there».")
        return 2
    s = stato_proc(a.pid_server)
    if not s:
        ko(f"⛔ pid {a.pid_server} does not exist: there is nothing to measure")
        return 2
    inf(f"the server is pid {a.pid_server}, Uid: {s.get('uid')}")
    if s.get("uid", [1])[1] != 0:
        ko("⛔ the server does NOT run as root: then it can neither check "
           "someone else's password nor make a child drop.  ⚠ This bench "
           "would be green by construction, so it exits 2 (vacuity).")
        return 2
    ok("⭐ the server is root: it is the §1.10-bis regime")
    inf(f"line: {(cmdline(a.pid_server) or '')[:150]}")
    reg = Registro(a.registro)
    if not reg.leggibile:
        ko(f"⛔ the log «{a.registro}» is not there: without it, half of the tests "
           f"have nowhere to look")
        return 2
    ok(f"log: {a.registro} ({reg.offset()} bytes so far)")
    prima = figli_di(a.pid_server)
    inf(f"children already alive: {len(prima)} {[x['pid'] for x in prima]}")

    guai = []
    casi = list(CASI) if a.caso == "tutti" else [a.caso]
    for c in casi:
        if c not in CASI:
            ko(f"unknown case: {c}")
            return 2
        CASI[c](a, reg, guai)

    titolo("The verdict")
    if not guai:
        dico("    \033[1;32m⭐ all as expected\033[0m")
        esito = 0
    else:
        dico(f"    \033[1;31m⛔ {len(guai)} tests gave something else\033[0m")
        for g in guai:
            ko(g)
        esito = 1

    if a.uscita:
        try:
            with open(a.uscita, "a") as f:
                f.write(json.dumps({
                    "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "banco": "02-figlio",
                    "casi": casi,
                    "porta": a.porta,
                    "pid_server": a.pid_server,
                    "utente": a.utente,
                    "guai": guai,
                    "esito": esito,
                }, ensure_ascii=False) + "\n")
        except OSError as e:
            ko(f"⚠ the outcome was not written to {a.uscita}: {e}")
    return esito


if __name__ == "__main__":
    sys.exit(main())
