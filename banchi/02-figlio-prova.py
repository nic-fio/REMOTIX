#!/usr/bin/env python3
"""02-figlio-prova.py — the bench of `DECISIONI.md` §1.10-bis: **one child per user**.

    python3 02-figlio-prova.py --prediction
    python3 02-figlio-prova.py --case_v nasce --port 7571 \\
        --pid-server 12345 --logbook /srv/remotix/tmp/02-figlio/registro.log \\
        --username nicfio --password-file /srv/src/tmp/02-figlio-parola

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
    with the `blind` fault, where they are the only wall left.

---------------------------------------------------------------------------
⛔ THE SIX TESTS, AND THE OPPOSITE CASE OF EACH

  | case          | what must happen                   | the opposite case      |
  |---------------|------------------------------------|------------------------|
  | `nasce`       | one child, the user's uid, with bus| no child, or the       |
  |               | and WITHOUT the server's port      | parent's bus           |
  | `due`         | two connections, ONE child (I2)    | two children           |
  | `distacco`    | the client leaves, the child LIVES | the child dies with    |
  |               | with the SAME pid (I4)             | the detach             |
  | `dies`       | child killed, the parent REAPS it   | a zombie that looks    |
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

HERE = os.path.dirname(os.path.abspath(__file__))

# ⛔ The expectation is written BEFORE the round, and printed with `--prediction`: an expectation
#    written after seeing the number is not an expectation.
PREDICTION = """
⛔ THE EXPECTATION, written before the round — `DECISIONI.md` §1.10-bis

 1. `nasce`  ⭐ after «nicfio» is ADMITTED there exists **one** child process of the
    server, and:
      · `/proc/<pid>/status` says `Uid: 1000 1000 1000 1000` — all four,
        because a saved-uid at 0 is a process that can go back to root;
      · its command line starts with `remotix-figlio --internal-child`;
      · ⛔ it has **4 descriptors** (0,1,2 and the socket to the parent) and has NO
        socket in common with the parent besides that one: it did not take port 7571
        along with it;
      · in the log there is «THE SESSION BUS IS MINE», and the parent has never
        written anything of the kind.
 2. `due`  ⭐ two connections of the same user ⇒ **a single child**, the
    same pid, and in the log «a second one is NOT born — invariant I2».
 3. `distacco`  ⭐ the client closes, and after 5 s the child is **still alive**,
    same pid, state NOT `Z`.  ⛔ If it died, I4 would be broken.
 4. `dies`  ⭐ `SIGKILL` to the child ⇒ the parent reaps it (the pid **disappears**
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


def say(t=""):
    print(t, flush=True)


def ok(t):
    say(f"    \033[1;32mOK\033[0m  {t}")


def ko(t):
    say(f"    \033[1;31mNO\033[0m  {t}")


def inf(t):
    say(f"    --  {t}")


def heading(t):
    say(f"\n\033[1m== {t}\033[0m")


# ---------------------------------------------------------------------------
# The readings from the KERNEL.  ⛔ Each tells «it is not there» from «I could not
#    read», and the second is a `None` the caller must treat as an
#    «I did not measure» — never as a zero.


def read_it(fpath):
    try:
        with open(fpath, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return b""          # it is not there
    except PermissionError:
        return None         # ⛔ I could NOT read: it is a different fact
    except OSError:
        return None


def proc_state(pid):
    """The four uids, the four gids and the state, asked of the kernel."""
    b = read_it(f"/proc/{pid}/status")
    if b is None:
        return None
    if not b:
        return {}
    outside = {}
    for row in b.decode("utf-8", "replace").splitlines():
        if row.startswith("Uid:"):
            outside["uid"] = [int(x) for x in row.split()[1:5]]
        elif row.startswith("Gid:"):
            outside["gid"] = [int(x) for x in row.split()[1:5]]
        elif row.startswith("State:"):
            outside["state"] = row.split()[1]
        elif row.startswith("PPid:"):
            outside["ppid"] = int(row.split()[1])
    return outside


def cmdline(pid):
    b = read_it(f"/proc/{pid}/cmdline")
    if b is None:
        return None
    return b.replace(b"\x00", b" ").decode("utf-8", "replace").strip()


def descriptors(pid):
    """{fd: target}.  ⛔ `None` = I could not look."""
    try:
        listing = os.listdir(f"/proc/{pid}/fd")
    except (PermissionError, OSError):
        return None
    outside = {}
    for n in listing:
        try:
            outside[int(n)] = os.readlink(f"/proc/{pid}/fd/{n}")
        except OSError:
            outside[int(n)] = "(vanished while I was looking)"
    return outside


def children_of(pid_padre):
    """The server's «--internal-child» children, asked of /proc.

    ⛔ `pgrep remotix` is NOT used: it would also catch the servers of the other
       benches (7448, 7501, 7561), and a bench that counts someone
       else's processes measures the machine and not the product.
    """
    outside = []
    for n in os.listdir("/proc"):
        if not n.isdigit():
            continue
        s = proc_state(n)
        if not s or s.get("ppid") != int(pid_padre):
            continue
        row = cmdline(n)
        if not row or "--internal-child" not in row:
            continue
        pieces = row.split()
        outside.append({
            "pid": int(n),
            "argv": row,
            "username": pieces[2] if len(pieces) > 2 else "?",
            "uid": s.get("uid"),
            "gid": s.get("gid"),
            "state": s.get("state"),
            "fd": descriptors(n),
        })
    return outside


class Log:
    """The server's log, read from an OFFSET — B0.7.

    ⛔ Reading it from the start would count yesterday's lines.  And `size()` is
       taken BEFORE every test, not after.
    """

    def __init__(self, fpath):
        self.fpath = fpath
        self.readable = os.path.exists(fpath)

    def offset(self):
        try:
            return os.path.getsize(self.fpath)
        except OSError:
            return None

    def da(self, off):
        if off is None:
            return None
        try:
            with open(self.fpath, "rb") as f:
                f.seek(off)
                return f.read().decode("utf-8", "replace")
        except OSError:
            return None


def wait_for(cond, seconds=15.0, step=0.2):
    """Markers, not `sleep`: a CONDITION is waited for, and how long is said."""
    t0 = time.time()
    while time.time() - t0 < seconds:
        v = cond()
        if v:
            return v, time.time() - t0
        time.sleep(step)
    return None, time.time() - t0


def client(a, wait=6.0, username=None, password=None):
    """One round of the independent RCP client (`02-filo-cliente.py`).

    ⭐ A client is not rewritten: that one is already a certified referee of F2.4,
       and using it here means that «the session reaches SESSION» is said by a
       program that is not this bench.
    """
    password_file = None
    if password is not None:
        # ⛔ D12: the password never goes through `argv`.
        password_file = os.path.join(a.work, "parola-caso")
        old = os.umask(0o077)
        try:
            with open(password_file, "w") as f:
                f.write(password)
        finally:
            os.umask(old)
    cmd = [sys.executable, os.path.join(HERE, "02-filo-cliente.py"),
           "--address", a.address, "--port", str(a.port),
           "--username", username or a.username,
           "--password-file", password_file or a.password_file,
           # ⛔ `--codec 1`, and not 2: that number tells the judge **what to
           #    expect**, and the negotiation of §4.3 is done by the `HELLO` of
           #    `01-b3-cliente.py`, which declares two codecs and gets
           #    HEVC as the answer.  ⚠ `[M]` 12 Aug 2026, first round: with
           #    `--codec 2` the client said «ERRORE_PROTOCOLLO: codec 1, but
           #    2 had been negotiated» — that is a red pointed at the SERVER for one
           #    line of this bench.  It is the second time this client
           #    accuses the server (`P2-6-montaggio.md` §5.2), and the second time
           #    it was wrong.
           "--codec", "1", "--wait", str(wait)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=wait + 90)
    if password_file:
        try:
            os.unlink(password_file)
        except OSError:
            pass
    return p


# ---------------------------------------------------------------------------
# The cases


def case_born(a, reg, troubles):
    heading("1. `nasce` — one child, running AS THE USER (asked of the kernel)")
    off = reg.offset()
    before = children_of(a.pid_server)
    inf(f"children before: {len(before)}")
    # ⛔ THE SCENE OF THIS CASE IS «A SERVER JUST STARTED», and it is CHECKED
    #    instead of hoped for: with a child already alive, I2 does the right thing —
    #    a second one is not born — and this case would see neither the
    #    introduction nor the bus line.  ⚠ It would be a RED on a healthy
    #    product, and it is the defect the bench can inflict on itself.
    if before:
        ko(f"⛔ there is already {len(before)} live child: this case wants a server "
           f"JUST STARTED.  I do not measure, and I do not print a green — redo "
           f"«turn_on_again» and then «gauge nasce».")
        troubles.append("nasce: wrong scene (a child was already there)")
        return

    p = client(a)
    inf(f"the client exited {p.returncode}")
    for r in p.stdout.splitlines():
        if "SESSION" in r or "frames" in r or "ACCEPTED" in r:
            inf(r.strip())

    after, how_much = wait_for(lambda: children_of(a.pid_server) or None, 20)
    if not after:
        ko("⛔ NO child after an admitted login: §1.10-bis is not alive")
        troubles.append("nasce: no child")
        return
    ok(f"{len(after)} child after {how_much:.1f} s")

    g = after[0]
    expected_val = int(a.expected_uid)
    if g["uid"] is None:
        ko("⛔ I COULD NOT read the child's uids: it is not a green and it is not")
        ko("   a red — it is «I did not measure».  Root is needed.")
        troubles.append("nasce: uids not readable")
        return
    if g["uid"] == [expected_val] * 4:
        ok(f"⭐ the kernel says Uid: {g['uid']} — real, effective, SAVED and fs, "
           f"all four at {expected_val}")
    else:
        ko(f"⛔ Uid: {g['uid']}, expected [{expected_val}]*4.  ⚠ A different saved-uid is "
           f"a process that can go back to root")
        troubles.append(f"nasce: uid {g['uid']}")
    if g["gid"] == [int(a.expected_gid)] * 4:
        ok(f"⭐ and Gid: {g['gid']}")
    else:
        ko(f"⛔ Gid: {g['gid']}, expected [{a.expected_gid}]*4")
        troubles.append(f"nasce: gid {g['gid']}")

    if g["argv"].split()[0].endswith("remotix-figlio"):
        ok(f"the command line declares it: «{g['argv'][:90]}»")
    else:
        ko(f"⛔ unexpected argv[0]: «{g['argv'][:90]}»")
        troubles.append("nasce: argv")

    # ⛔ IT DID NOT TAKE THE PORT ALONG — and it is not a deduction.
    fdp = descriptors(a.pid_server)
    if g["fd"] is None or fdp is None:
        ko("⛔ I could not read the descriptors: I do not say the port is not "
           "there.  ⚠ «I did not look» is not «it was not there» (LEZIONI.md §1.9)")
        troubles.append("nasce: fds not readable")
    else:
        inf(f"the parent has {len(fdp)} descriptors, the child {len(g['fd'])} "
            f"(⚠ NOW: after it has opened the stage)")
        for n, t in sorted(g["fd"].items())[:6]:
            inf(f"    fd {n} → {t}")
        common = set(g["fd"].values()) & set(fdp.values())
        # ⚠ 0,1,2 are the same log on purpose: it is what makes readable
        #   «who said what».  What must NOT be there is a socket
        #   of the parent — the port, or the unblock command socket.
        shared_sockets = {v for v in common if v.startswith("socket:")}
        if not shared_sockets:
            ok(f"⭐ ZERO sockets in common with the parent: it did NOT take port {a.port} "
               f"along with it")
        else:
            ko(f"⛔ {len(shared_sockets)} sockets in common with the parent: "
               f"{sorted(shared_sockets)}")
            troubles.append("nasce: sockets inherited from the parent")
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
            troubles.append("nasce: no descriptor count at birth")
        elif int(m.group(1)) == 4:
            ok("⭐ and AT BIRTH it had 4: 0, 1, 2 and the socket to the "
               "parent.  ⛔ The parent has "
               f"{len(fdp)} — none of its own went across")
        else:
            ko(f"⛔ at birth it had {m.group(1)}, not 4: something of the "
               f"parent reached the child")
            troubles.append(f"nasce: {m.group(1)} descriptors at birth")

    body_text = reg.da(off) or ""
    if "THE SESSION BUS IS MINE" in body_text:
        ok("⭐ and in the log: «THE SESSION BUS IS MINE» — the thing root "
           "cannot do")
    else:
        ko("⛔ the child did NOT say it has the bus.  The «child» lines:")
        for r in body_text.splitlines():
            if " child " in r:
                inf(r.strip()[:160])
        troubles.append("nasce: no bus")
    if "complete frame from" in body_text:
        ok("⭐ and a frame arrived from the child to the parent")
    else:
        inf("⚠ no frame from the child in this window: look at the "
            "«child»/«video» lines above for the reason")


def case_two(a, reg, troubles):
    heading("2. `due` — two connections of the same user, ONE single child (I2)")
    off = reg.offset()
    before = children_of(a.pid_server)
    if not before:
        client(a)
        before, _ = wait_for(lambda: children_of(a.pid_server) or None, 20)
    if not before:
        ko("⛔ not even the first child is there: I could not measure")
        troubles.append("due: no first child")
        return
    pid1 = before[0]["pid"]
    inf(f"the current child is pid {pid1}")

    p = client(a)
    inf(f"second connection: the client exited {p.returncode}")
    time.sleep(1.0)
    after = children_of(a.pid_server)
    if len(after) == 1 and after[0]["pid"] == pid1:
        ok(f"⭐ a single child, and the SAME pid {pid1}: I2 holds, and the stage is "
           f"the same because it belongs to the session (I4)")
    else:
        ko(f"⛔ after the second connection the children are {len(after)}: "
           f"{[x['pid'] for x in after]}")
        troubles.append("due: more than one child")
    body_text = reg.da(off) or ""
    if "a second one is NOT born" in body_text:
        ok("⭐ and the product says so: «a second one is NOT born — invariant I2»")
    else:
        ko("⛔ the product did not write the I2 line: the right behaviour "
           "without the line is a behaviour nobody can check")
        troubles.append("due: I2 line missing")


def detach_case(a, reg, troubles):
    heading("3. `distacco` — the client leaves, the stage STAYS (I4)")
    before = children_of(a.pid_server)
    if not before:
        client(a)
        before, _ = wait_for(lambda: children_of(a.pid_server) or None, 20)
    if not before:
        ko("⛔ no child: I could not measure")
        troubles.append("distacco: no child")
        return
    pid1 = before[0]["pid"]
    inf(f"the child is pid {pid1}; the client has already disconnected "
        f"(its process has ended)")
    inf("waiting 6 s with NO live connection…")
    time.sleep(6.0)
    s = proc_state(pid1)
    if s is None:
        ko("⛔ I could not read the child's state")
        troubles.append("distacco: state not readable")
        return
    if not s:
        ko(f"⛔ the child {pid1} IS GONE after the detach: invariant I4 "
           f"is broken — the stage belonged to the connection")
        troubles.append("distacco: the child died")
        return
    if s.get("state") == "Z":
        ko(f"⛔ the child {pid1} is a ZOMBIE: «alive» and «dead» look the "
           f"same in /proc, and it is the defect already paid for with the helper")
        troubles.append("distacco: zombie")
        return
    ok(f"⭐ the child {pid1} is still alive (state {s['state']}), uid {s['uid']}: "
       f"the stage belongs to the SESSION, not to the connection (I4)")


def case_dies(a, reg, troubles):
    heading("4. `dies` — child killed, the parent REAPS it and says so")
    off = reg.offset()
    before = children_of(a.pid_server)
    if not before:
        client(a)
        before, _ = wait_for(lambda: children_of(a.pid_server) or None, 20)
    if not before:
        ko("⛔ no child: I could not measure")
        troubles.append("dies: no child")
        return
    pid1 = before[0]["pid"]
    inf(f"killing the child {pid1} with SIGKILL — so it cannot say goodbye "
        f"to anyone and no handler can answer in its place")
    try:
        os.kill(pid1, signal.SIGKILL)
    except OSError as e:
        ko(f"⛔ I could not kill it: {e}")
        troubles.append("dies: kill failed")
        return

    def vanished():
        s = proc_state(pid1)
        if s is None:
            return None
        if not s:
            return "vanished"
        if s.get("state") == "Z":
            return None      # ⛔ zombie: it is NOT «reaped»
        return None

    v, how_much = wait_for(vanished, 15)
    if v:
        ok(f"⭐ pid {pid1} vanished from /proc after {how_much:.1f} s: the parent "
           f"REAPED it, and «dead» no longer looks the same as «alive»")
    else:
        s = proc_state(pid1) or {}
        ko(f"⛔ after {how_much:.1f} s pid {pid1} is still there, state "
           f"{s.get('state')}: if it is `Z` it is an unreaped zombie")
        troubles.append("dies: not reaped")

    body_text = reg.da(off) or ""
    if "is leaving" in body_text and "killed by signal 9" in body_text:
        ok("⭐ and the log says so with the cause: «killed by signal 9»")
    else:
        ko("⛔ the log does not name the cause of death")
        troubles.append("dies: cause not written")
    if "EMPTIED" in body_text:
        ok("⭐ and the video store was EMPTIED: a user's image "
           "does not stay in the house after their stage has died")
    else:
        inf("⚠ no «EMPTIED»: either the store was not theirs, or it was not there")

    off2 = reg.offset()
    p = client(a)
    inf(f"new connection: the client exited {p.returncode}")
    newcomers, _ = wait_for(lambda: children_of(a.pid_server) or None, 20)
    if not newcomers:
        ko("⛔ after the child's death no new one is born: the slot "
           "stayed occupied by a dead one")
        troubles.append("dies: not reborn")
    elif newcomers[0]["pid"] != pid1:
        ok(f"⭐ a new one was born, pid {newcomers[0]['pid']} ≠ {pid1}")
    else:
        ko("⛔ the pid is the same: something does not add up")
        troubles.append("dies: same pid")


def no_stage_case(a, reg, troubles):
    heading("5. `senza-palco` — a user who does NOT have the bus")
    off = reg.offset()
    p = client(a, username=a.user2, password=a.password2)
    inf(f"the client of «{a.user2}» exited {p.returncode}")
    for r in p.stdout.splitlines():
        if "SESSION" in r or "frames" in r or "ADMITTED" in r:
            inf(r.strip())
    # ⛔⭐ THE TEST THAT COUNTS IN THIS CASE, and the first draft did NOT do it:
    #     «prova» must see **nothing**.  `[M]` 12 Aug 2026, first round:
    #     it saw ONE, conforming — and it was «nicfio»'s desktop, served from the
    #     PROCESS store of `webtransport.c`.  ⛔ Not «you receive nothing»:
    #     **you receive someone else's desktop**, which is I3 violated
    #     invisibly.  ⇒ This line is the only one that can see it.
    seen_items = 0
    for r in p.stdout.splitlines():
        m = re.search(r"(\d+) frames, all conforming", r)
        if m:
            seen_items = int(m.group(1))
    if seen_items == 0:
        ok(f"⭐⭐ «{a.user2}» saw ZERO frames: «{a.username}»'s desktop did NOT "
           f"reach them")
    else:
        ko(f"⛔⛔ «{a.user2}» received {seen_items} frames, and their stage "
           f"did not produce even one ⇒ they belong to ANOTHER user.  "
           f"Invariant I3 violated invisibly.")
        troubles.append("senza-palco: PIXEL LEAK between users")
    after, _ = wait_for(
        lambda: [x for x in children_of(a.pid_server) if x["username"] == a.user2]
        or None, 20)
    if not after:
        ko(f"⛔ no child for «{a.user2}»: the session was admitted and "
           f"the stage was not even ATTEMPTED")
        troubles.append("senza-palco: no child")
        return
    g = after[0]
    ok(f"⭐ «{a.user2}»'s child is there: pid {g['pid']}, Uid: {g['uid']}")
    if g["uid"] and g["uid"][0] != int(a.expected_uid):
        ok(f"⭐ and it is NOT «{a.username}»'s uid ({a.expected_uid}): two users, two "
           f"identities — which is the whole mandate")
    else:
        ko("⛔ the two users have the same uid: this bench proves nothing")
        troubles.append("senza-palco: same uid")
    body_text = reg.da(off) or ""
    if "I do NOT have the session bus" in body_text:
        ok("⭐ and the child SAYS it has no bus, instead of staying silent: «I could "
           "not look» is not «there is no session»")
    else:
        ko("⛔ the child did not declare the absence of the bus")
        troubles.append("senza-palco: absence not declared")
    # ⚠ the old check «NON entra in deposito» (the store guard of `main.c`) is
    #   gone: commit 92105b5 (13 Aug 2026) removed the process store altogether
    #   (one stream per frame, per session), so there is no guard line to look for.

def fault_case(a, reg, troubles, blind):
    label_name = "guasto-cieco" if blind else "guasto-uid"
    heading(f"{'7' if blind else '6'}. `{label_name}` — a child running as the "
           f"WRONG user")
    off = reg.offset()
    p = client(a)
    inf(f"the client exited {p.returncode}")
    time.sleep(3.0)
    living = children_of(a.pid_server)
    body_text = reg.da(off) or ""

    if living:
        s = living[0]["uid"]
        ko(f"⛔⛔ there is a LIVE child with Uid: {s} while the fault is injected: "
           f"neither of the two walls bit")
        troubles.append(f"{label_name}: live child")
    else:
        ok("⭐ no live child: the fault was stopped")

    if blind:
        if "MESSAGE REFUSED" in body_text and "the kernel says uid 0" in body_text:
            ok("⭐⭐ and what stopped it was THE PARENT, on the credentials stamped "
               "by the kernel: «MESSAGE REFUSED … the kernel says uid 0»")
        else:
            ko("⛔ the parent did NOT refuse on the kernel's stamp: the check "
               "at every message did not bite, and this case is the only one that "
               "can see it")
            troubles.append("guasto-cieco: no refusal by the parent")
    else:
        # ⛔ THE CHILD'S WALLS ARE TWO, and the bench accepts both: the
        #    same check — `getresuid()` — sits BEFORE the `exec` (exit
        #    35) and AFTER (exit 42).  `[M]` 12 Aug 2026: the one that bit was
        #    the first, and the bench required the words of the second.  ⚠ What
        #    counts is not WHICH wall: it is that the cause is NAMED — «it exited
        #    with 35» is not a diagnosis, «DID NOT DROP to the user» is.
        if "DID NOT DROP to the user" in body_text or "IS NOT WHO IT SHOULD" in body_text:
            ok("⭐ and what stopped it was the child itself, rereading its own "
               "uids from the kernel — and the parent wrote down the CAUSE, not the "
               "number")
        else:
            ko("⛔ the child did not notice it had not dropped, or the parent "
               "did not name the cause")
            troubles.append("guasto-uid: no check by the child")
    for r in body_text.splitlines():
        if " child " in r and ("⛔" in r or "NOT" in r):
            inf(r.strip()[:170])


CASES = {
    "nasce": case_born,
    "due": case_two,
    "distacco": detach_case,
    "dies": case_dies,
    "senza-palco": no_stage_case,
    "guasto-uid": lambda a, r, g: fault_case(a, r, g, False),
    "guasto-cieco": lambda a, r, g: fault_case(a, r, g, True),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prediction", action="store_true")
    p.add_argument("--case_v", default="nasce")
    p.add_argument("--address", default="192.168.0.2")
    p.add_argument("--port", type=int, default=7571)
    p.add_argument("--pid-server", type=int, default=0)
    # ⛔ THE PID IS READ FROM THE FILE, NOT FROM A SHELL SUBSTITUTION.
    #    ⚠ `p=$(cat …)` inside `ssh → enter.sh → bash -lc` crosses THREE
    #    levels of quotes and dies halfway: `[M]` 12 Aug 2026, this
    #    bench, first round — the `$(…)` arrived empty and `argparse` said
    #    «expected one argument».  It is the same form that has already run
    #    a case «the helper is dead» on a LIVE helper
    #    (`PAM-filo-unico.md` §6).  ⇒ A file has no levels of quotes.
    p.add_argument("--pid-file", default="")
    p.add_argument("--logbook", default="")
    p.add_argument("--username", default="nicfio")
    p.add_argument("--expected-uid", default="1000")
    p.add_argument("--expected-gid", default="1000")
    p.add_argument("--password-file", default="")
    p.add_argument("--user2", default="prova")
    p.add_argument("--password2", default="parola-di-prova")
    p.add_argument("--work", default="/srv/src/tmp")
    p.add_argument("--out_dir", default="")
    a = p.parse_args()

    if a.prediction:
        say(PREDICTION)
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

    heading("0. The initial state, declared AND checked (B0.1)")
    if os.geteuid() != 0:
        ko("⛔ this bench wants root: half of the readings are on /proc of a "
           "root process, and «I could not read» is not «it was not there».")
        return 2
    s = proc_state(a.pid_server)
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
    reg = Log(a.logbook)
    if not reg.readable:
        ko(f"⛔ the log «{a.logbook}» is not there: without it, half of the tests "
           f"have nowhere to look")
        return 2
    ok(f"log: {a.logbook} ({reg.offset()} bytes so far)")
    before = children_of(a.pid_server)
    inf(f"children already alive: {len(before)} {[x['pid'] for x in before]}")

    troubles = []
    cases = list(CASES) if a.case_v == "all_v" else [a.case_v]
    for c in cases:
        if c not in CASES:
            ko(f"unknown case: {c}")
            return 2
        CASES[c](a, reg, troubles)

    heading("The verdict")
    if not troubles:
        say("    \033[1;32m⭐ all as expected\033[0m")
        outcome = 0
    else:
        say(f"    \033[1;31m⛔ {len(troubles)} tests gave something else\033[0m")
        for g in troubles:
            ko(g)
        outcome = 1

    if a.out_dir:
        try:
            with open(a.out_dir, "a") as f:
                f.write(json.dumps({
                    "when": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "bench": "02-figlio",
                    "cases": cases,
                    "port": a.port,
                    "pid_server": a.pid_server,
                    "username": a.username,
                    "troubles": troubles,
                    "outcome": outcome,
                }, ensure_ascii=False) + "\n")
        except OSError as e:
            ko(f"⚠ the outcome was not written to {a.out_dir}: {e}")
    return outcome


if __name__ == "__main__":
    sys.exit(main())
