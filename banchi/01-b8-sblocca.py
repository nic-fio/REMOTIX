#!/usr/bin/env python3
"""01-b8-sblocca.py — ⛔ THE UNBLOCK COMMAND of `RCP.md` §4.4-bis, from the side of
whoever commands.

    python3 01-b8-sblocca.py --socket /srv/src/remotix-command.sock 192.168.0.2
    python3 01-b8-sblocca.py --socket /srv/src/b8-command.sock --ping
    python3 01-b8-sblocca.py --socket ... --expect REMOVED 127.0.0.1
    python3 01-b8-sblocca.py --socket ... --expect-name remotix \\
                             --ban-file /srv/src/remotix-ban 192.168.0.2

===========================================================================
⛔ WHAT IT IS FOR, AND WHY IT IS NOT ONLY B8'S

`RCP.md` §4.4-bis: «one gets out in two ways, not one — the natural expiry, or
an **unblock command on the server**».  And `FASI.md` §01-filo-nudo rule **B0.3**
makes it the **hardest constraint of the chapter**: the count of attempts is per
address, all the benches start from the same address, and ⛔ *«B7 fails one
attempt, B8 fails three, and from there on every bench of that machine is out
for twelve hours — including B10, B11 and whoever is developing»*.

⭐ So this file is **the tool of B0.3**, not a piece of B8: it is called by
   whoever has to put the machine back on its feet between one bench and the
   next.  ⛔ And whoever calls it **declares it**, or «the ban did not trigger»
   and «someone removed it» look the same — which is the reason this program
   always prints **which of the two** answers it received, and not a plain
   «done».

===========================================================================
⛔ THREE OUTCOMES, NOT TWO

    REMOVED         the ban was there, and now it is no longer
    NOT-BANNED   there was nothing to remove
    (none)        ⛔ I could not talk to the command

⛔ The third is the one that counts most, and it is the one a program written in
   a hurry confuses with the second: a missing socket, a server off, a wrong path
   **are not** «it was not banned».  Whoever confused them would declare «the
   machine is clean» after having talked to nobody — `LEZIONI.md` §1.9, and the
   common face of empty and forbidden.

⛔⭐ AND THE THIRD OUTCOME HAS A FOURTH FACE, FOUND ON 11 AUG 2026 — the most
     insidious, because it is the only one that answers:

    **I talked to a server, but not to THAT one** — that is the ban is still alive
    in the process that serves, and I have just received a «NOT-BANNED» from another.

⚠ It is not a textbook case: on this machine the **two** servers exist together
  — the graft `bsslserver` on 7447 and the product `remotix` on 7448 — and until
  today the default of `--socket` was the **graft's** socket.  Whoever unblocked
  «for the product» without writing the path talked to the other one, received
  `PONG` and `NOT-BANNED`, and exited **0** declaring clean a machine that was
  still out for twelve hours.  ⛔ The `PING` does not see it: it says *«someone
  answers»*, not *«the right one answers»*.

The three cures, and they are independent of each other:

    1. ⛔ `--socket` NO LONGER HAS A DEFAULT.  The path is written, always.
       A default that points to one of the two servers is a choice made by whoever
       wrote the tool in place of whoever measures, and made silently.
    2. ⭐ WHO ANSWERED IS ASKED OF THE KERNEL, not of the server: `SO_PEERCRED` on
       a Unix domain socket hands over **pid, uid and gid of the process at the
       other end**, and from there `/proc/<pid>/comm` says whether it is called
       `remotix` or `bsslserver`.  ⛔ It is `CODER.md` §3.7 — *«the sender is not
       deduced: it is asked of the kernel»* — and it is worth more than any answer
       the server could send by itself: a string in the protocol is written by
       the server, the pid is written by the kernel.  ⚠ That is why NO new verb
       was added to the protocol: `RCP.md` §4.4-bis and `FASI.md` §01-filo-nudo
       promise that the two servers speak **the same protocol byte for byte**,
       and a verb only one of the two understands would have been form **E2** of
       `REVIEWER.md` — two behaviours under the same label.  The protocol has not
       changed by one byte.
    3. ⭐ `--ban-file` LOOKS AT THE OTHER HALF OF §4.4-bis: the ban lives in two
       places — the memory of the process that serves and the file that survives
       the restart — and so far this tool queried **one** of them.  With
       `--ban-file` the file is read **before and after**, and the two readings
       are compared.

===========================================================================
⛔ WHAT IS DEMANDED, AND WHAT SAYS NO  (rule B0.4)

*«The expected is compared by the bench, not by whoever reads»*: it is printed **and** compared.

    --expect REMOVED|NOT-BANNED   the outcome of the unblock
    --expect-name NOME            the name of the process that answered
                                   (`remotix` for the product, `bsslserver` for
                                   the graft): substring of `/proc/<pid>/comm`
                                   or of the command line
    --expect-pid N               the exact pid — ⭐ it is the hardest form, and
                                   it is the one used when the server was started
                                   by the script that calls this command and the
                                   pid was noted down
    --ban-file PATH                the ban file to look at before and after

⭐ And the check that says **no**, on the ban file: if before the unblock the key
   in the file **was not there**, then «after it is not there» proves nothing —
   the reader never found anything, so one does not know whether it can find
   (`LEZIONI.md` §1.9 rule 2, the positive control on the same tool).
   This program says so instead of keeping quiet, and does not call that run green.

===========================================================================
⛔ THE EXIT STATUSES — each is a different fact

    0   I talked, and the outcome is the expected one (or I demanded none)
    2   wrong usage: `--socket` is missing, or the address is missing
    3   ⛔ I TALKED TO NOBODY — the third outcome, the one that counts
    4   I talked, but the outcome (or who answered) is not the one demanded — B0.4
    5   ⛔ memory and ban file CONTRADICT each other: the unblock did not last, or
        the server I unblocked is not the one that writes that file
    6   ⚠ I could not read the ban file: the check on file **was not done**, and
        it is not a «clean»

⚠ When more than one of these facts is true together, **all** the lines are on
  screen and the exit status carries the most serious: the ban file (5, 6) wins
  over the comparison with the expected (4), because it says the ban is still
  there and not only that it was not what I expected.

===========================================================================
⭐ WHAT OF THIS FILE WAS MEASURED, AND WITH WHAT DENOMINATOR

`[M]` **11 Aug 2026, on CHUWI** — ⛔ **not** against the running product, which is
the run still to be done.  The bench was `src/comando.c` **really compiled**
(`gcc -std=gnu11 -D_GNU_SOURCE -Wall -Wextra`) and linked to a fake `rcp` of
forty lines, in which `rcp_key_address()` is the **exact copy** of that
of `src/rcp.c` and `rcp_unblock()` removes from a list and rewrites a file in the
same format.  ⚠ What that bench does NOT prove is the real ban: that the one
banning is `mark_failed()` and that the table is that of the process that serves.

Seventeen cases, each with its expected outcome:

    PING → PONG · UNBLOCK → REMOVED · again → NOT-BANNED · `--expect` that
    says NO (exits 4) · `--expect-name` on the right server and on the wrong
    server (0 and 4) · `--expect-pid` (0 and 4) · missing socket · abandoned
    socket (nobody listening) · file that is not a socket · ⭐ **folder that
    cannot be traversed** · server answering in another language · server that
    accepts and keeps quiet · empty line · `UNBLOCK` without address · `UNBLOCK`
    with only spaces · `\r\n` instead of `\n` · `[192.168.0.2]` instead of
    `192.168.0.2`

⭐ And the two checks that say **no**, because a list of green cases is not a
   proof: *(1)* the unblock given to the **wrong** server — two processes running
   together, the ban on one and the command to the other — is the only case that
   without `--ban-file` and without `--expect-name` exits **0** saying «it was
   not banned»; with the first it exits **5**, with the second **4**.  *(2)* The
   key typed in two forms (`192.168.0.2` and `[192.168.0.2]`) reaches the **same**
   entry: the first command answers `REMOVED`, the second `NOT-BANNED`.

===========================================================================
⚠ WHERE IT IS CALLED FROM, AND WHAT KEY IT ASKS FOR

The socket lives in the filesystem with permissions **0600** and belongs to
whoever started the server — which in the benches is **root inside the
container**.  ⭐ It is intended: §4.4-bis says this command *«asks for the only
key that case allows — access to the machine»*, and a socket readable by anyone
would make it «access to any user of the machine», which is a different and
easier key.

In practice:

    the product, from   bash /media/REMOTIX/enter.sh --root \\
    the container         "python3 /srv/src/01-b8-sblocca.py \\
                           --socket /srv/src/remotix-command.sock \\
                           --expect-name remotix \\
                           --ban-file /srv/src/remotix-ban 192.168.0.2"

    the graft           as above, but --socket /srv/src/b8-command.sock and
                        --expect-name bsslserver

    from the server,    the same paths are seen as
    outside             /media/REMOTIX/src/…, ⚠ but sudo is needed: as a normal
                        user the socket is root's 0600

⛔ And a «permission denied» **is not a «it was not banned»**: here it exits with 3
   and says so, because it is exactly the common face of empty and forbidden.

⚠ And the address is typed **as a person types it** (`192.168.0.2`): the real key
  carries square brackets — `[192.168.0.2]`, because that is how the host's
  `util::straddr()` writes it — and the one putting them is `rcp_key_address()`
  inside the server.  Here no key is built: if this file built one too, the day
  the two forms diverged the command would answer «it was not banned» to every
  address, silently and forever.

⭐ And the key needed to look at the ban file **is taken from the answer**, not
   built: the server answers `REMOVED [192.168.0.2]`, and that is its key,
   pronounced by it.  ⛔ If one day it answered without a key, this program says
   that it could not do the check on file (exits 6) instead of inventing one.
"""
import argparse
import os
import socket
import stat as statmod
import struct
import sys

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# The two sockets that exist on this machine, and they needs only to write them in
# the error message for whoever forgot `--socket`.  ⛔ They are not defaults:
# see the box «the third outcome has a fourth face».
KNOWN_SOCKETS = (
    ("the product  (src/, port 7448)", "/srv/src/remotix-command.sock", "remotix"),
    ("the graft    (bsslserver, 7447)", "/srv/src/b8-command.sock", "bsslserver"),
)


# ===========================================================================
# ⛔ Who is at the other end — and the KERNEL says it, not the server
# ===========================================================================
def who_listens(s):
    """The credentials of the process at the other end of the socket, from `SO_PEERCRED`.

    ⭐ `CODER.md` §3.7: *«the sender is not deduced: it is asked of the kernel»*.
       A Unix domain socket carries with it pid, uid and gid of whoever listens,
       and the kernel has no reason to lie — while a string in the protocol is
       chosen by the server, that is precisely the piece whose identity one wants
       to know.

    Returns a dictionary that always declares **why** a field is missing:
    ⛔ «I could not read it» and «it is not there» are two different facts
    (`LEZIONI.md` §1.9 rule 1), and this is exactly the point where the previous
    version of this file confused them."""
    chi = {"pid": None, "uid": None, "gid": None, "name": None,
           "line": None, "fault": None}
    try:
        raw = s.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                              struct.calcsize("3i"))
        chi["pid"], chi["uid"], chi["gid"] = struct.unpack("3i", raw)
    except (OSError, AttributeError, struct.error) as e:
        chi["fault"] = (f"I could not ask the kernel who is listening "
                         f"(SO_PEERCRED): {type(e).__name__}: {e}")
        return chi
    if not chi["pid"]:
        chi["fault"] = ("the kernel gave pid 0: the process that was listening is "
                         "no longer reachable from this pid namespace")
        return chi
    proc = f"/proc/{chi['pid']}"
    if not os.path.isdir(proc):
        # ⛔ The process died between the `connect` and this line: it is a fact, and
        #    it is not «I could not read it».
        chi["fault"] = (f"{proc} is not there: process {chi['pid']} that "
                         f"answered is already dead")
        return chi
    for field, dove, clean_up in (("name", "comm", lambda t: t.strip()),
                                   ("line", "cmdline",
                                    lambda t: " ".join(t.split("\0")).strip())):
        try:
            with open(f"{proc}/{dove}", "r", errors="replace") as f:
                chi[field] = clean_up(f.read()) or None
        except OSError as e:
            # ⛔ `/proc/<pid>/cmdline` of a binary with file capabilities is
            #    unreadable even for whoever started it (`LEZIONI.md` §1.9): an
            #    empty field here does NOT mean «process without a name».
            chi["fault"] = (f"I could not read {proc}/{dove}: "
                             f"{type(e).__name__}: {e}")
    return chi


def describe_who(chi):
    """The line that is always printed, even when it could not be known."""
    if chi is None:
        return "⚠ I did not ask who is listening"
    pieces = []
    if chi["pid"]:
        pieces.append(f"pid {chi['pid']}")
    if chi["name"]:
        pieces.append(f"«{chi['name']}»")
    if chi["uid"] is not None:
        pieces.append(f"uid {chi['uid']}")
    if not pieces:
        return f"⚠ who answered: UNKNOWN — {chi['fault']}"
    queue = f" — ⚠ {chi['fault']}" if chi["fault"] else ""
    return "answered by " + " ".join(pieces) + queue


def who_matches(chi, expected):
    """`(true, detail)`.  ⛔ A comparison that could not look is NOT a
    successful comparison: it returns false and says why.

    ⛔ AND `comm` IS COMPARED, IN FULL, NOT THE COMMAND LINE.  It seemed more
       generous to look for the word in both, and instead it was a measurable
       trap: the **graft's** command line names the product —
       `bsslserver … --ban-file /srv/src/remotix-ban` contains «remotix» — and
       `--expect-name remotix` would have been **green on the wrong server**,
       that is the check that exists to find that case would have covered it.
       ⚠ `/proc/<pid>/comm` is the program's name, it fits in 15 characters, and
       `remotix` and `bsslserver` both fit.
    ⚠ The command line stays as a DECLARED FALLBACK for the sole case in which
      `comm` could not be read, and then it is said that the comparison is
      weaker (`CODER.md` §4.2: the fallback is declared)."""
    if chi is None:
        return False, "I did not ask who answered"
    if chi["name"]:
        if chi["name"] == expected:
            return True, f"/proc/{chi['pid']}/comm says exactly «{expected}»"
        return False, (f"/proc/{chi['pid']}/comm says «{chi['name']}», not "
                       f"«{expected}»")
    if chi["line"]:
        if expected in chi["line"]:
            return True, (f"⚠ WEAK comparison (comm unreadable: "
                          f"{chi['fault']}): «{expected}» appears in the command "
                          f"line «{chi['line']}» — but it would also appear in "
                          f"another program that names that path")
        return False, f"«{expected}» is not in the command line «{chi['line']}»"
    return False, ("I do not know who answered, so I cannot say it is "
                   f"«{expected}»: {chi['fault']}")


# ===========================================================================
# The socket, the line, the answer
# ===========================================================================
def look_socket(fpath):
    """`(ok, detail)` on the socket file alone, before talking to it.

    ⛔⭐ HERE LAY A DEFECT OF THIS VERY FILE, and it is the one the file
         preaches not to commit — found on 11 Aug 2026.  The line was
         `if not os.path.exists(percorso)` with the message *«the socket does
         not exist: either the server is not running, or it was started without
         --command-socket»*.  ⚠ But `os.path.exists()` **swallows the error**: on
         `PermissionError` — that is when the folder containing the socket
         cannot be traversed by the caller, which is the NORMAL case for a root
         socket looked at by an ordinary user — it returns `False` exactly as
         when the file is not there.  ⛔ Empty and forbidden with the same face,
         inside the program whose header says they must not have it:
         `LEZIONI.md` §1.9, first rule.  Here `errno` is looked at."""
    try:
        st = os.stat(fpath)
    except FileNotFoundError:
        if os.path.lexists(fpath):
            return False, (f"«{fpath}» is a link pointing to nothing: "
                           f"the socket it refers to is not there")
        return False, (f"the socket «{fpath}» does not exist: either the server is not "
                       f"running, or it was started without --command-socket — and in "
                       f"both cases the ban CANNOT be removed")
    except PermissionError as e:
        return False, (f"⛔ I do not have permission to LOOK at «{fpath}» ({e}): "
                       f"this is NOT «the socket is not there».  The socket is 0600 "
                       f"of whoever started the server (usually root in the "
                       f"container): call it again with sudo, or from inside the "
                       f"container with --root")
    except OSError as e:
        return False, (f"I could not look at «{fpath}»: "
                       f"{type(e).__name__}: {e}")
    if not statmod.S_ISSOCK(st.st_mode):
        return False, (f"«{fpath}» is there but is NOT a socket "
                       f"(mode {statmod.filemode(st.st_mode)}): I am looking at the "
                       f"wrong file")
    mode = st.st_mode & 0o777
    if mode != 0o600:
        # ⚠ It is not a fault: one talks anyway, but §4.4-bis says the key of
        #   this command is «access to the machine», and with a wider socket the
        #   key is another.  It is declared.
        return True, (f"⚠ the socket is {mode:04o} and not 0600: §4.4-bis assumes "
                      f"«access to the machine», and this is access for more "
                      f"people than that")
    return True, None


def swap(fpath, line, wait=5.0):
    """One line to the control socket, and everything that is known about it.

    Returns a dictionary with `response` **or** `fault` (never both), plus
    `chi` — who answered according to the kernel — and `avviso`.
    ⛔ A fault is NOT an answer: the caller must not be able to confuse them, and
       that is why there is no fallback value."""
    r = {"risposta": None, "fault": None, "who": None, "warning": None}
    if not fpath:
        r["fault"] = "no socket path: I talked to nobody"
        return r
    va, detail = look_socket(fpath)
    if not va:
        r["fault"] = detail
        return r
    r["warning"] = detail
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(wait)
    try:
        s.connect(fpath)
        # ⭐ Who is listening is asked BEFORE sending the line: if the server
        #    then dies, one still knows whom one was talking to.
        r["who"] = who_listens(s)
        s.sendall((line + "\n").encode())
        # ⚠ A single read is enough: the answer is a short line and the server
        #   closes right away.  If one day it became longer, this is the point
        #   to change — and it would show, because the answer would arrive
        #   truncated instead of absent.
        data = s.recv(4096)
    except OSError as e:
        r["fault"] = f"I could not talk to the command: {type(e).__name__}: {e}"
        return r
    finally:
        s.close()
    if not data:
        r["fault"] = "the command closed without answering anything"
        return r
    r["risposta"] = data.decode(errors="replace").strip()
    return r


def speaks(fpath, line, wait=5.0):
    """⚠ The old form, `(answer, fault)` — one of the two is always `None`.
    It stays because `01-b8-cronometro.py` imports it; the rest uses `swap()`."""
    r = swap(fpath, line, wait)
    return r["risposta"], r["fault"]


def extended_ping(fpath, wait=5.0):
    """⭐ «Is the command there and does it answer?» — and it touches no ban.

    It is the denominator of B0.3: a bench that unblocks between one test and the
    next must be able to say it **talked to someone**, or its «removed» and its
    silence have the same value.

    ⛔ And it says **with whom**: `PONG` alone proves that someone answers, not
       that the server whose ban is being measured answers."""
    r = swap(fpath, "PING", wait)
    r["vivo"] = (r["risposta"] == "PONG")
    return r


def ping(fpath, wait=5.0):
    """⚠ The old form, `(alive, what)`, for `01-b8-cronometro.py`."""
    r = extended_ping(fpath, wait)
    return r["vivo"], (r["risposta"] or r["fault"])


def unblock_extended(fpath, address, wait=5.0):
    """Adds to `swap()` the `outcome` in REMOVED · NOT-BANNED · None, and the
    `key` **as the server pronounced it**."""
    r = swap(fpath, f"UNBLOCK {address}", wait)
    r["outcome"] = None
    r["key"] = None
    if r["risposta"] is None:
        return r
    pieces = r["risposta"].split(" ", 1)
    if pieces[0] not in ("REMOVED", "NOT-BANNED"):
        r["fault"] = f"an answer I do not know: «{r['risposta']}»"
        r["risposta"] = None
        return r
    r["outcome"] = pieces[0]
    if len(pieces) > 1 and pieces[1].strip():
        r["key"] = pieces[1].strip()
    return r


def unblock(fpath, address, wait=5.0):
    """⚠ The old form, `(outcome, detail)`, for `01-b8-cronometro.py`."""
    r = unblock_extended(fpath, address, wait)
    if r["outcome"] is None:
        return None, r["fault"]
    return r["outcome"], (r["risposta"] or r["outcome"])


# ===========================================================================
# ⛔ THE OTHER HALF OF §4.4-bis: the file, which survives the restart
# ===========================================================================
def read_ban_file(fpath):
    """`(lines, fault)` — one of the two is always `None`.

    ⛔ The WHOLE file is read and nothing is searched yet: the key is pronounced
       by the server in its answer, and the answer arrives **after** the
       unblock.  Taking the two snapshots — before and after — the search is
       done on both when the key is known, and then the «before» becomes the
       positive control of the reader instead of another question without an
       answer.

    ⛔ «The key is not in the file» and «I could not read the file» are two
       different facts, and the second is NOT a «clean» (`LEZIONI.md` §1.9).
    ⛔ And «the file does not exist» is not «no ban»: it means the server is
       running without `--ban-file`, that is that NO ban survives the restart —
       invariant **I7**, and §4.4-bis forbids it."""
    try:
        with open(fpath, "r", errors="replace") as f:
            return [r for r in f.read().splitlines() if r.strip()], None
    except FileNotFoundError:
        return None, (
            f"the ban file «{fpath}» does not exist: ⛔ it is not «no ban», it is "
            f"that the server is running without --ban-file and no ban survives "
            f"the restart (§4.4-bis, invariant I7)")
    except PermissionError as e:
        return None, (f"⛔ I do not have permission to read the ban file "
                      f"«{fpath}» ({e}): it is not «the ban is not there»")
    except OSError as e:
        return None, (f"I could not read the ban file «{fpath}»: "
                      f"{type(e).__name__}: {e}")


def inside(lines, key):
    """⚠ The FIRST field of the line is compared, not `chiave in riga`: the file
    carries «[192.168.0.2] 1786000000», and a substring would say yes also
    for «[192.168.0.20]»."""
    return any(r.split(" ", 1)[0] == key for r in lines)


# ===========================================================================
def main():
    p = argparse.ArgumentParser(
        description="The unblock command of RCP.md §4.4-bis (fasi/01-filo-nudo.md B0.3)")
    p.add_argument("address", nargs="?", default=None,
                   help="the address to unblock, as a person types it")
    # ⛔ NO DEFAULT, and the reason is in the box «the third outcome has a
    #    fourth face»: the previous default was the graft's socket, and whoever
    #    used it against the product received PONG and NOT-BANNED from the wrong
    #    server, exiting 0.
    p.add_argument("--socket", default=None,
                   help="⛔ mandatory: the command's 0600 Unix socket")
    p.add_argument("--ping", action="store_true",
                   help="only asks whether the command exists, and touches nothing")
    p.add_argument("--expect", choices=("REMOVED", "NOT-BANNED"), default=None,
                   help="⛔ and the bench COMPARES (B0.4): exits 4 if the outcome is another")
    p.add_argument("--expect-name", default=None, metavar="NAME",
                   help="the name of the process that MUST answer "
                        "(«remotix» the product, «bsslserver» the graft): exits 4")
    p.add_argument("--expect-pid", type=int, default=None, metavar="N",
                   help="the exact pid that MUST answer: exits 4")
    p.add_argument("--ban-file", default=None, metavar="PATH",
                   help="also look at the ban file, before and after")
    p.add_argument("--wait", type=float, default=5.0)
    a = p.parse_args()

    if not a.socket:
        print(f"    {RED}NO{GRAY}  ⛔ --socket is missing, and there is no longer a "
              f"default: on this machine the servers are TWO, and unblocking "
              f"the wrong one exits 0 saying the machine is clean")
        for chi, dove, name in KNOWN_SOCKETS:
            print(f"        {chi}  --socket {dove} --expect-name {name}")
        return 2

    if a.ping:
        r = extended_ping(a.socket, a.wait)
        if r["warning"]:
            print(f"        {r['warning']}")
        if not r["vivo"]:
            print(f"    {RED}NO{GRAY}  ⛔ the unblock command does NOT answer: "
                  f"{r['risposta'] or r['fault']}")
            return 3
        print(f"    {GREEN}OK{GRAY}  the unblock command answers («PONG») on "
              f"«{a.socket}» — and it touched no ban")
        print(f"        ⭐ {describe_who(r['who'])}")
        return judge_who(a, r["who"])

    if not a.address:
        print(f"    {RED}NO{GRAY}  ⛔ the address to unblock is missing "
              f"(or --ping)")
        return 2

    # ── the snapshot of the ban file BEFORE ───────────────────────────────
    # ⛔ It is read before, and not out of curiosity: without the «before», the
    #    sentence «after, the key is not there» has no positive control — a reader
    #    that cannot find ANYTHING would say exactly the same thing
    #    (`LEZIONI.md` §1.9 rule 2).
    before, before_fault = (None, None)
    if a.ban_file:
        before, before_fault = read_ban_file(a.ban_file)

    r = unblock_extended(a.socket, a.address, a.wait)
    if r["warning"]:
        print(f"        {r['warning']}")
    if r["outcome"] is None:
        print(f"    {RED}NO{GRAY}  ⛔ I removed nothing, and not because it was "
              f"not there: {r['fault']}")
        return 3

    print(f"        ⭐ {describe_who(r['who'])}")
    if r["outcome"] == "REMOVED":
        print(f"    {GREEN}OK{GRAY}  ⛔ UNBLOCKED «{a.address}» — the ban was there "
              f"and it has been removed  ({r['risposta']})")
    else:
        print(f"    {YELLOW}--{GRAY}  «{a.address}» was NOT banned: I removed "
              f"nothing  ({r['risposta']})")
        # ⛔ This line was a BELIEF until 11 Aug 2026 (finding A22): nobody
        #    verified it, and the whole sampling strategy of B8 («unblocking
        #    between one block and the next») rests on it.
        #    Now it is measured, and it says WHERE — because a fact without
        #    provenance is a hope with a number in front.
        print(f"        ⚠ and the attempt count of that address restarts "
              f"from zero anyway — `[M]` 11 Aug 2026, measured by "
              f"`01-b8-prova-ban.c` section 5: two failures, an unblock that "
              f"answers «it was not banned», two more failures, and the ban does "
              f"NOT trigger")

    code = judge_who(a, r["who"])
    if a.expect and r["outcome"] != a.expect:
        print(f"    {RED}NO{GRAY}  ⛔ expected «{a.expect}», arrived "
              f"«{r['outcome']}»: they are two different facts and this bench tells them apart")
        code = code or 4

    if a.ban_file:
        # ⚠ And the ban file WINS over the comparison with the expected: 4 says
        #   «it is not the outcome I expected», 5 says «the ban is still there».
        #   The lines on screen all stay; the exit status carries the most serious fact.
        code = look_two_halves(a, r, before, before_fault) or code
    return code


def judge_who(a, chi):
    """B0.4 applied to *who answered*: it is printed and compared."""
    code = 0
    if a.expect_pid is not None:
        if chi is None or chi["pid"] != a.expect_pid:
            real = chi["pid"] if chi else None
            print(f"    {RED}NO{GRAY}  ⛔ expected pid {a.expect_pid}, "
                  f"{real} answered: I talked to a server, but not to THAT one "
                  f"— the ban I wanted to remove is still where it was")
            code = 4
    if a.expect_name:
        va, detail = who_matches(chi, a.expect_name)
        if not va:
            print(f"    {RED}NO{GRAY}  ⛔ expected «{a.expect_name}» at the other "
                  f"end: {detail}.  On this machine the servers are two, and "
                  f"an unblock given to the wrong one answers perfectly well")
            code = 4
        else:
            print(f"        {GREEN}OK{GRAY}  and it is the right server: {detail}")
    return code


def look_two_halves(a, r, before, before_fault):
    """⛔ §4.4-bis lives in TWO places — the memory of the process that serves and
    the file that survives the restart — and an unblock that convinces only one
    of them is not an unblock: at the restart the ban comes back, and whoever gave
    the command saw it exit with zero (finding R12.1, and it is the defect
    `src/comando.c` exists to remove).  Here the two halves are compared instead
    of taking one as good."""
    if not r["key"]:
        print(f"    {YELLOW}??{GRAY}  ⚠ the server answered without the key "
              f"(«{r['risposta']}»): I cannot look at the ban file without "
              f"building a key myself, and building it is precisely what "
              f"§4.4-bis forbids to whoever commands")
        return 6
    key = r["key"]
    after, after_fault = read_ban_file(a.ban_file)

    # ⛔ The denominator, always (`LEZIONI.md` §1.9 rule 4): «absent» is not a
    #    datum until one knows on how many lines one looked.
    for label, lines, fault in (("before", before, before_fault),
                                     ("after ", after, after_fault)):
        if fault:
            print(f"        {YELLOW}??{GRAY}  ban file {label}: {fault}")
        else:
            print(f"        --  ban file {label}: «{key}» "
                  f"{'PRESENT' if inside(lines, key) else 'absent'} "
                  f"({len(lines)} lines in «{a.ban_file}»)")

    if after_fault:
        print(f"    {YELLOW}??{GRAY}  ⚠ the check on FILE was not done: "
              f"I only know that the process memory says «{r['outcome']}».  ⛔ It is not "
              f"a «clean»")
        return 6

    c_after = inside(after, key)
    c_before = inside(before, key) if before is not None else None

    if r["outcome"] == "REMOVED" and c_after:
        print(f"    {RED}NO{GRAY}  ⛔ the process says REMOVED and the ban file "
              f"still contains «{key}»: the unblock did NOT reach the disk, "
              f"and at the first restart the ban comes back (§4.4-bis, invariant I7)")
        return 5
    if r["outcome"] == "NOT-BANNED" and c_after:
        print(f"    {RED}NO{GRAY}  ⛔ the process says NOT-BANNED and the ban "
              f"file contains «{key}»: the two halves of §4.4-bis do not "
              f"agree, and the possible readings are two — ⛔ either I talked to "
              f"a server DIFFERENT from the one that writes «{a.ban_file}» (and then "
              f"the ban I wanted to remove is still alive), or that server "
              f"started without rereading the file")
        return 5
    if r["outcome"] == "REMOVED":
        print(f"    {GREEN}OK{GRAY}  ⭐ memory and file agree: the process "
              f"removed «{key}», and it is no longer in the file")
        # ⛔ And the check that says NO is declared: if the key was not in the
        #    file even BEFORE, «now it is not there» would be said identically by
        #    a reader that cannot find anything.
        if c_before:
            print(f"        {GREEN}OK{GRAY}  ⭐ and the positive control of the "
                  f"reader is there: before, I found «{key}» in that file")
        elif before_fault:
            print(f"        ⚠ positive control ABSENT: I could not read the «before», "
                  f"so I do not know whether this reader can "
                  f"find a key that is there (`LEZIONI.md` §1.9 rule 2)")
        else:
            print(f"        ⚠ positive control ABSENT: «{key}» was not in the file "
                  f"EVEN BEFORE, while the process says the ban in "
                  f"memory was there.  ⛔ The two halves of §4.4-bis do not agree "
                  f"in the other direction: that ban would not have survived the "
                  f"restart")
            return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
