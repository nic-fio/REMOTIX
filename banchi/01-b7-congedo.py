#!/usr/bin/env python3
"""01-b7-congedo.py — ⛔ B7: the farewell, read FROM THE RECEIVING SIDE.

    python3 01-b7-congedo.py --address 192.168.0.2 --port 7447 \\
                             --log /srv/src/b7-server.log \\
                             --page /srv/src/01-b11-pagina.html
    python3 01-b7-congedo.py --only tempo-scaduto      (a single case)
    python3 01-b7-congedo.py --list                  (the predictions, without measuring)

⚠ It runs INSIDE the container: aioquic lives there, and so does the server log.

===========================================================================
⛔ WHY THIS BENCH EXISTS

`RCP.md` §8.1: *«the farewell is verified from the side that receives it, never
from the log of whoever sends it»*.  ⚠ And the price has already been paid: in
v1, for **three phases**, the server dutifully wrote «farewell to the client»
while the client, at the same time, wrote «network error» (`LEZIONI.md` §1.7).
The sender's log says it called a function, not that the byte arrived.

⛔ **And the roads are TWO, not one** — `RCP.md` §3.1, which says in bytes what
«closing» means:

    point 1   one WRITES in the log **what** was not understood;
    point 2   one sends `FAREWELL` with the reason **on the control channel**,
              *«if the control channel is still usable»*;
    point 3   one closes the **WebTransport session** with the application
              error code equal to the **reason code** of §8.2.

⭐ Point 3 is the one §3.1 calls *«the one that saves the diagnoses»*: if the
   farewell does not arrive — broken stream, unreadable message — the reason
   still travels inside the closing of the session.

===========================================================================
⛔ THE TWO ROADS ARE COUNTED SEPARATELY, AND THE WHY IS A MEASUREMENT

`[M]` **10 Aug 2026**: «§3.1 point 3 — reason in the WT closing» gave **22 out
of 36** in B5, and the fourteen missing were all violations found at the
**first** message: the closing capsule **did not leave at all**, because the
deferred work hung on a condition nobody made happen any more.  ⛔ And no bench
had noticed **because nobody counted that road separately**: it was enough for
the `FAREWELL` to arrive.  The cure is there (the keep-alive armed in
`wt_chiudi_sessione`); **the permanent witness is this file**.

⛔ Hence the shape of the verdict, which is the reason B7 exists:

    for every case, the right reason by BOTH declared roads —
    an `&&`, never an `||`

`FASI.md` §01-filo-nudo §C1 builds the fault on purpose: *«the sending of the
`FAREWELL` is removed and the code in the closing is left: if B7 stays green it
is doing an `||` where an `&&` is needed»*.  With an `||` point 2 would
disappear and the bench would stay green.  Here point 2 and point 3 have **two
counters, two denominators and two red lines**.

===========================================================================
⛔ AND THE TWO ENGINES USE TWO DIFFERENT ROADS — `[M]` 10 Aug 2026, from B11

When **the page** is the one closing:

    Chrome    sends the `FAREWELL` on the control channel **and** closes the
              session with the code: both roads;
    Firefox   **resets** the control channel and throws away the `FAREWELL`
              already queued: the reason arrives **only** in the closing code.

⚠ **A bench that confused them would say «Firefox does not say farewell», which
  is false**: it is §3.1 point 2 that is *conditional* — «if the channel is still
  usable» — and on Firefox it no longer is.  Point 3, instead, is an
  **unconditional** MUST, and there Firefox is present.

⭐ That is why the two behaviours are **two distinct cases**, each with its
   roads DECLARED BEFORE measuring, and the denominators do not mix.  The
   «Firefox-style» case takes nothing away from the `FAREWELL` counter, and the
   «Chrome-style» case gives nothing to the closing one.

===========================================================================
⛔ WHICH REASONS CAN REALLY BE PROVOKED, AND WHY THE NUMBER IS «N OUT OF M»

§8.2 has **fifteen** reasons.  ⛔ Printing «8 out of 8» choosing the eight one
knows how to provoke is true **by construction**, and it is the emptiest form
of green there is: the denominator must be **declared**, with the list of what
was excluded and why.  Here those that can be provoked are **seven**, and the
other eight are in the `EXCLUDED` table with the reason for each — ⭐ and the
exclusion of `SERVER_CLOSING` is not an opinion: it is **measured**, with
the `grep` of §«the measured exclusions», because an asserted exclusion is a
hole nobody rechecks.

⚠ Two exclusions are worth repeating here, because a bench that ignored them
  would **fail by construction**: `WRONG_CREDENTIALS` and `TOO_MANY_ATTEMPTS`
  do not travel in a `FAREWELL` — §4.4 puts them in `REJECTED`, and §4.4 forbids
  sending both.  Looking for them here would be looking for a message the
  protocol forbids.

⛔ And B7 **never gets a password wrong**: it moves neither of the two counters
   of §4.4-bis, so it does not block the address on B8 and B10.
   It is the isolation **B0.3** asks for, obtained by removing the case instead
   of resetting a counter.

===========================================================================
⭐ THE POSITIVE CONTROL, AND WHERE IT IS

`LEZIONI.md` §1.9 second rule: *«can this tool find something that is surely
there?»*.  B7 has **four** positive controls, and they run BEFORE measuring:

  1. ⭐ **the two readers of the two roads, called from outside** on known bytes
     (`CODER.md` §3.6): the well-formed closing capsule must give `0x0b`,
     the **bare** one must give `0x0b` **and say it is bare**, and a pile of
     random bytes must give **nothing** — ⛔ not «zero»;
  2. ⭐ **the phrase reader can say NO**: it is fed four broken tables — the
     `switch` with the default branch («Error 14»), two equal phrases, the
     phrase that is the reason's name, a missing reason — and it must reject
     them all, after having passed the good one;
  3. ⭐ **the server log reader can find a line that is there** (and not find
     one that is not), verified on the whole handshake;
  4. ⭐ **the initial state** (B0.1, B0.2): a whole handshake up to
     `SESSION`.  ⛔ Without it, the `ALREADY_ACTIVE_REMOTELY` case would be **green
     for the wrong reason** — a place left occupied by the previous run makes
     anyone get `0x0F`, and the bench would read it as skill.

⛔ If one of the four fails the bench exits **3** and measures nothing: a
   negative outcome with an uncertified tool is ambiguous between «the server
   does not work» and «the bench did not work» (`CODER.md` §3.3).

===========================================================================
⛔ WHAT B7 DOES NOT TEST, AND IT MUST BE SAID

  · **that the phrase really reaches the user's eyes.**  Here the client's
    **table** is read, not the screen: «the bench looks at the screen» is not
    executable, and the only thing an automatic test can do is read the DOM —
    which wants a browser.  ⛔ The judgement on what is SEEN stays with the
    user (**I8**), and it goes into the judgement, not into this table;
  · **the value of the caps of §4.6.**  The `tempo-scaduto` case demands the
    *reason* `TIMED_OUT` by both roads, and **prints** how long it waited:
    the five seconds are measured by **B6**, and duplicating a threshold here
    would give two different verdicts on the same property;
  · **the client→server direction, on the wire.**  There whoever receives is
    the server, and the only witness is its log.  ⚠ It is not the violation of
    §8.1: §8.1 forbids reading the farewell from the log of **whoever sends
    it**.  Here whoever sends is the bench.  ⭐ And so as not to rest on a single
    leg, those two cases verify **also on the wire** an observable consequence:
    that the place was left (§8.2 `0x0F`), with a new connection that gets to
    `SESSION`.
"""
import argparse
import asyncio
import contextlib
import importlib.util
import os
import re
import signal
import ssl
import struct
import sys

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio import connect

HERE = os.path.dirname(os.path.abspath(__file__))

# ⛔ The B3 client is IMPORTED, not copied.  Inside it is the line that
#    prevents it from handing the control-channel events to aioquic's HTTP/3
#    layer — without which the connection dies at the hand of the CLIENT (10
#    Aug 2026) — and there is `_closing_capsule`, that is the reader of the
#    second road of §3.1.  A diverging copy would bring those defects back here
#    disguised as server defects.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(HERE, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

# ⛔ And the TARGET's profile: the differences between the two servers are in a
#    single file, and the four benches read them instead of discovering them anew.
_spec_b0 = importlib.util.spec_from_file_location(
    "b0bersaglio", os.path.join(HERE, "01-b0-bersaglio.py"))
b0 = importlib.util.module_from_spec(_spec_b0)
_spec_b0.loader.exec_module(b0)

s, wrap = b3.s, b3.wrap

FAREWELL, REJECTED = 0x000C, 0x0005

# ⛔ §8.2 IN FULL, rewritten from `RCP.md` and imported from nobody.
#
#    `01-b3-cliente.py` knows eight of them: that is enough for it.  Here all
#    fifteen are needed, because B7's denominator is the whole of §8.2 — and
#    because this table is the **second reader** with which the page's one is
#    judged.
#    ⚠ Two tables written by the same hand confirm nothing: this one comes
#      from §8.2, that one from whoever wrote the page.
REASONS = {
    0x01: "CLOSED_BY_USER", 0x02: "INACTIVITY",
    0x03: "SESSION_ABANDONED", 0x04: "LOCAL_SESSION_PREVAILED",
    0x05: "ALREADY_ACTIVE_LOCALLY", 0x06: "BUDGET_FULL",
    0x07: "WRONG_CREDENTIALS", 0x08: "TOO_MANY_ATTEMPTS",
    0x09: "NOTHING_IN_COMMON", 0x0A: "INCOMPATIBLE_VERSION",
    0x0B: "PROTOCOL_ERROR", 0x0C: "SERVER_CLOSING",
    0x0D: "TIMED_OUT", 0x0E: "SESSION_UNSERVABLE",
    0x0F: "ALREADY_ACTIVE_REMOTELY",
}

CLOSED_BY_USER = 0x01
NOTHING_IN_COMMON = 0x09
INCOMPATIBLE_VERSION = 0x0A
PROTOCOL_ERROR = 0x0B
SERVER_CLOSING = 0x0C
TIMED_OUT = 0x0D
SESSION_UNSERVABLE = 0x0E
ALREADY_ACTIVE_REMOTELY = 0x0F

# ===========================================================================
# ⛔ THE DENOMINATOR, DECLARED — «N out of M that can be provoked», and M is here.
#
#    Every line of `EXCLUDED` carries the reason why phase 1 cannot produce it.
#    ⚠ Whoever adds a reason to those that can be provoked must remove it from
#    here: the two tables together must make fifteen, and
#    `certify_denominator()` verifies it instead of trusting.
# ===========================================================================
EXCLUDED = [
    (0x02, "30 minutes without INPUT: the input channel is born in phase 4 and "
           "the clock in phase 5"),
    (0x03, "6 hours without attaches: it is a clock of the SESSION, phase 5"),
    (0x04, "it wants a real LOCAL graphical session that prevails: the stage "
           "is born in phase 2"),
    (0x05, "likewise: to say it, the server must be able to look at the "
           "machine's local sessions (phase 2)"),
    (0x06, "it wants the encoding capacity, which is born in phase 3"),
    (0x07, "⛔ it does NOT travel in a FAREWELL: §4.4 puts it in REJECTED, and forbids "
           "sending both.  Looking for it here would fail by construction "
           "— B5 and B8 measure it"),
    (0x08, "likewise, REJECTED (§4.4-bis) — ⛔ and provoking it would block this "
           "address for at least 30 s, that is it would poison B8 and B10 (B0.3)"),
    (0x0C, "⛔ the GRAFT has no shutdown path: "
           "`RCP_SERVER_CLOSING` appears on no line of "
           "`01-b3-rcp-innesta.py`.  ⚠ MEASURED below with grep, not "
           "assumed.  ⭐ And on `--target product` this line DISAPPEARS: "
           "`src/main.c` says farewell to everyone with SERVER_CLOSING before "
           "exiting, and those that can be provoked become EIGHT"),
]


# ⛔⭐ THE DENOMINATOR DEPENDS ON THE TARGET — and it is the difference between
#     the two servers that shows from a NUMBER instead of from a behaviour.
#
#       innesto    SEVEN that can be provoked + eight excluded = 15
#       product   EIGHT that can be provoked + seven excluded = 15
#
# ⛔ *«The number to write next to an outcome is that of the target that was
#    started»* (`FASI.md` §01-filo-nudo B7).  ⚠ And if B7 pointed at the product
#    kept saying «seven out of seven», the denominator would be wrong and the
#    bench would be looking the other way: it would be a green by construction,
#    the emptiest form there is.
def excluded_of(target):
    if b0.profile(target)["spegnimento"]:
        return [(c, why) for c, why in EXCLUDED if c != SERVER_CLOSING]
    return list(EXCLUDED)


def cases_of(target, all_items=None):
    """The cases THIS target can produce.

    ⛔ `server-in-chiusura` exists only against the product: against the graft
       it would stay waiting for a farewell no line of code can send, and its
       red would accuse the server of not doing something nobody ever taught
       it."""
    report = []
    for c in (all_items if all_items is not None else CASES):
        if c[1] == SERVER_CLOSING and not b0.profile(target)["spegnimento"]:
            continue
        report.append(c)
    return report


# ---------------------------------------------------------------------------
# The bytes, written by hand.
def capabilities(entries, version=1):
    out = struct.pack("!HH", version, len(entries))
    for n, v in entries:
        out += s(n) + s(v)
    return out


GOOD = [("video.codec", "hevc,av1"), ("video.depth", "8,10"),
         ("audio.codec", "opus,pcm"), ("client.name", "bench-b7 0.1.0")]


def ciao(entries=None, version=1):
    return wrap(0x0001, capabilities(GOOD if entries is None else entries, version))


def attach(tl=1920, ta=1080, vl=1920, va=1080, avail="it"):
    return wrap(0x0006, struct.pack("!IIII", tl, ta, vl, va) + s(avail))


def farewell(reason, detail):
    """§7.1: `FAREWELL` = `u8 motivo` + `string detail`."""
    return wrap(FAREWELL, bytes([reason]) + s(detail))


def closing_capsule(reason):
    """The nine bytes with which a WebTransport session is closed (§3.1 point 3).

    ⛔ The `CLOSE_WEBTRANSPORT_SESSION` capsule (type `0x2843`) goes **inside an
       HTTP/3 `DATA` frame** (RFC 9297): on the wire of the extended CONNECT the
       body is a stream of capsules, and in HTTP/3 the body travels in `DATA`.
       Written bare, `0x68 0x43 …` reads as an unknown HTTP/3 frame type, and
       RFC 9114 §9 requires **ignoring it**: the reason disappears and only the
       `FIN` remains, which counts as «closing without a reason», that is code
       **0** which §3.1 forbids.  ⚠ It is the defect the server had until 10 Aug
       2026 (finding R10.1), here from the client's side.
    """
    return bytes([0x00, 7,             # DATA frame, 7 bytes of capsule
                  0x68, 0x43,          # 0x2843 as a variable-length integer
                  4, 0, 0, 0, reason])  # length, and the code on 4 bytes


class Client(b3.Client):
    """The B3 client, plus the two ways of CLOSING (§3.1, §8.1)."""

    def close_session(self, reason):
        """§3.1 point 3 from the client's side: the capsule with the reason, then the FIN."""
        self._quic.send_stream_data(self.session, closing_capsule(reason),
                                    end_stream=True)
        self.transmit()

    def reset_control(self, code=0):
        """⛔ What Firefox does: the control channel gets RESET.

        From that instant §3.1 point 2 is no longer enforceable — «if the
        control channel is still usable» —, and the reason can travel only by
        the second road.  ⚠ If `aioquic` could not reset a stream the case would
        imitate nothing: it is DECLARED instead of falling back silently
        (`CODER.md` §4.2).
        """
        if not hasattr(self._quic, "reset_stream"):
            raise RuntimeError(
                "this aioquic has no `reset_stream`: the «Firefox-style» case "
                "cannot be imitated, and pretending to have done it would be a "
                "green without proof")
        self._quic.reset_stream(self.check, code)
        self.transmit()


# ===========================================================================
# ⛔ THE SERVER LOG — where it is read, and where it is NOT read.
#
#    §8.1: *«the farewell is verified from the side that receives it, never from
#    the log of whoever sends it»*.  Here the server log is used for two things
#    only, and neither of the two is the verdict on the reason the server SENDS:
#
#      · **§3.1 point 1** — the line «what I did not understand».  It is by
#        definition a line of whoever closes: it is point 1 that asks for it;
#      · **the client→server direction** — where whoever receives IS the server,
#        and its log is the receiving side.
#
#    ⛔ The reason the server sends is always and only judged by the two roads,
#       read on the wire by this process.
# ===========================================================================
class Log:
    def __init__(self, fpath):
        self.fpath = fpath
        self.error = None

    def readable(self):
        """⛔ «There is nothing» and «it cannot be read» look the same."""
        if not self.fpath:
            return False, "no log declared (--log)"
        if not os.path.exists(self.fpath):
            return False, f"{self.fpath} DOES NOT EXIST"
        try:
            with open(self.fpath, "rb") as f:
                f.read(1)
        except OSError as e:
            return False, f"{self.fpath} cannot be read: {e}"
        return True, ""

    def window(self):
        """The tick mark from which to look: how long the file was now.

        ⭐ It is a marker, not a `sleep` (B0.7): what is judged are the bytes
           written AFTER this instant, and the lines of the previous cases can
           no longer enter a verdict that is not theirs.
        """
        try:
            return os.path.getsize(self.fpath)
        except OSError:
            return None

    def da(self, start):
        """The text written after the marker.  `None` if it cannot be read."""
        if start is None:
            return None
        try:
            with open(self.fpath, "rb") as f:
                f.seek(start)
                return f.read().decode("utf-8", "replace")
        except OSError as e:
            self.error = str(e)
            return None

    async def should_wait(self, start, sentence, within=6.0):
        """Waits for a line to appear, and says whether it appeared.

        ⚠ One waits because the log is written by another process and the two
          do not share a clock: reading at the exact instant one sent would
          measure our hurry.  ⛔ The window is declared and bounded: if it
          expires, the answer is «not within N s», not «it is not there».
        """
        fine = asyncio.get_event_loop().time() + within
        while True:
            text = self.da(start)
            if text is None:
                return False, "the log cannot be read"
            if sentence in text:
                return True, ""
            if asyncio.get_event_loop().time() >= fine:
                return False, f"did not appear within {within:.0f} s"
            await asyncio.sleep(0.05)

    def our_lines(self, start, how_many=14):
        """The RCP lines written in the window — for the diagnosis, not for the
        verdict.  ⚠ ngtcp2's traffic is filtered out, here it is noise."""
        text = self.da(start)
        if text is None:
            return ["(the log cannot be read)"]
        lines = [r for r in text.splitlines() if "REMOTIX" in r]
        return lines[-how_many:] if lines else ["(no RCP line)"]


# ===========================================================================
# ⭐ THE PHRASES OF §8.2 — «BUDGET_FULL is not "error 6"»
#
# §8.2: *«every reason MUST be showable to the user in an understandable
# phrase … and the phrase is built by the client, from the code»*.  ⛔ And the
# `detail` is NOT shown: it is for the log.
#
# ⛔ «Fifteen out of fifteen» is not enough, and it is finding R3.20: a `switch`
#    with the default branch — `show_cmd("Error " + code)` — produces fifteen
#    non-empty strings **all distinct from each other**.  The user reads «Error
#    14» for `SESSION_UNSERVABLE`, which §8.2 forbids with a ⛔ and an almost
#    identical example.  That is why the criteria are four, and the second is
#    the one that unmasks the `switch`.
# ===========================================================================
TABLE_ANCHOR = "const REASON_TEXT = {"
# ⚠ Since the page's table became an object literal — `0x07: "phrase",`, with
#   long phrases split as `"…" + "…"` and comments between the entries — it
#   carries the PHRASE only, not the name: the name is the one §8.2 gives to
#   the code (`REASONS`), and criterion 3 still checks that the phrase is not it.
ENTRY = re.compile(r'(?<![0-9A-Za-z_])0x([0-9A-Fa-f]{1,2})\s*:\s*'
                  r'((?:"(?:[^"\\\n]|\\.)*"\s*\+?\s*)+)')
PIECE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
COMMENT = re.compile(r'/\*.*?\*/|^\s*//[^\n]*', re.S | re.M)


def read_table(text):
    """Extracts {code: (name, phrase)} from the client's table.

    ⛔ It returns `(None, why)` when the table was not read: «zero phrases» and
       «I did not find the table» are two different facts, and confusing them
       would give a red to the client for a defect of the bench.
    """
    i = text.find(TABLE_ANCHOR)
    if i < 0:
        return None, f"the anchor «{TABLE_ANCHOR}» is not in this file"
    j = text.find("\n};", i)
    if j < 0:
        return None, "the table starts and does not end: «};» is missing"
    # ⛔ The comments go first: they quote old phrases in quotes ("silence
    #    too long") and would be read as entries.
    body = COMMENT.sub("", text[i + len(TABLE_ANCHOR):j])
    entries = {}
    for m in ENTRY.finditer(body):
        c = int(m.group(1), 16)
        sentence = "".join(PIECE.findall(m.group(2)))
        entries[c] = (REASONS.get(c, f"0x{c:02X}"), sentence)
    if not entries:
        return None, "the anchor is there but no entry matches the expected shape"
    return entries, ""


def judge_sentences(entries):
    """The four criteria, one at a time, with the reason for the no.

    Returns [(code, ok, why)] for all fifteen reasons of §8.2.
    """
    report = []
    views = {}
    for c in sorted(REASONS):
        expected_name = REASONS[c]
        if c not in entries:
            report.append((c, False, "⛔ the reason is not in the client's "
                                    "table: there is no phrase to show"))
            continue
        name, sentence = entries[c]
        f = sentence.strip()
        key = " ".join(f.lower().split())
        if name != expected_name:
            report.append((c, False, f"the name says «{name}», §8.2 says "
                                    f"«{expected_name}»"))
            continue
        # 1. a phrase, not a label
        if len(f.split()) < 3:
            report.append((c, False, f"«{f}» is not a phrase ({len(f.split())} "
                                    f"words): §8.2 wants something "
                                    f"showable to the user"))
            continue
        # 2. ⛔ no number of the reason, and no «error N» — the switch with
        #    the default branch dies here.
        if re.search(r"(?<![0-9])%d(?![0-9])" % c, f) or \
           re.search(r"0x0?%x" % c, f, re.I) or \
           re.search(r"error\s*[:\-]?\s*[0-9]", f, re.I):
            report.append((c, False, f"⛔ «{f}» contains the NUMBER of the reason: "
                                    f"§8.2 forbids «error {c}»"))
            continue
        # 3. the name of the reason is not a phrase for the user
        if name.lower() in f.lower() or name in f:
            report.append((c, False, f"⛔ «{f}» is the NAME of the reason, not a "
                                    f"phrase: it is a number written in letters"))
            continue
        # 4. distinct from each other
        if key in views:
            report.append((c, False, f"⛔ the same phrase as "
                                    f"{REASONS[views[key]]}: two different "
                                    f"reasons saying the same thing"))
            continue
        views[key] = c
        report.append((c, True, f))
    return report


# ---------------------------------------------------------------------------
# ⭐ THE FAKE TABLES — the positive control AND the one that says NO.
#
# ⚠ The good phrases contain NO digit, on purpose: criterion 2 looks for the
#   reason's number, and a test phrase that happened to carry one would make
#   the positive control fail, blaming the reader.
def _fake_table(sentence_of):
    return {c: (REASONS[c], sentence_of(c)) for c in REASONS}


def _good():
    return _fake_table(
        lambda c: f"this is phrase {chr(96 + c)} to show to the user")


def certify_sentences():
    """⭐ The tool that judges the phrases can say yes, and can say no.

    ⛔ Without this, «fifteen out of fifteen» is compatible with a reader that
       approves anything — and it is the defect B11 had to cure on the page,
       here applied to whoever reads.

    ⚠ The most important broken table is the second: the `switch` with the
      default branch produces fifteen non-empty strings **all distinct**, that
      is it passes every criterion except the one R3.20 had to write on purpose.
    """
    double = _good()
    double[0x03] = (REASONS[0x03], double[0x04][1])
    missing_one = _good()
    del missing_one[0x0E]
    # ⚠ The broken ones are written as someone in good faith would write them —
    #   whole phrases, long, distinct — because a too clumsy broken one would be
    #   rejected by the WRONG criterion, and the check would prove nothing about
    #   the criterion that matters.
    prove = [
        ("a good table", _good(), True),
        ("⛔ the switch with the default branch",
         _fake_table(lambda c: f"Error {c} while connecting to the "
                                  f"server"), False),
        ("⛔ and the same thing written in hexadecimal",
         _fake_table(lambda c: f"the session closed with code "
                                  f"0x{c:02x}, try again"), False),
        ("⛔ two reasons with the same phrase", double, False),
        ("⛔ the phrase that carries the NAME of the reason",
         _fake_table(lambda c: f"the server answered {REASONS[c]} to "
                                  f"this request"), False),
        ("⛔ a reason missing altogether", missing_one, False),
        ("⛔ a label instead of a phrase",
         _fake_table(lambda c: "not servable"), False),
    ]
    report = []
    for name, entries, expected in prove:
        outcomes = judge_sentences(entries)
        passes = all(ok for _, ok, _ in outcomes)
        report.append((name, passes == expected,
                      "passed" if passes else
                      "rejected: " + next(p for _, ok, p in outcomes
                                          if not ok)[:78]))
    return report


def certify_readers():
    """⭐ THE TWO READERS OF THE TWO ROADS, called from outside on known bytes.

    `CODER.md` §3.6: when the chain is already narrowed, one does not do another
    bench run — one calls the single suspect function on a known input.  ⛔ And
    without this, a «the reason did not arrive» stays ambiguous between «the
    server did not send it» and «the bench cannot read it» — that is exactly the
    defect B7 exists not to commit.
    """
    prove = []

    # ── road 2: the closing capsule ────────────────────────────────────────
    c, bare = b3._closing_capsule(closing_capsule(0x0B))
    prove.append(("the capsule inside the DATA frame", (c, bare) == (0x0B, False),
                  f"read {c!r}, bare={bare}  (expected 11, False)"))
    c, bare = b3._closing_capsule(closing_capsule(0x0B)[2:])
    prove.append(("⛔ the BARE capsule is read AND declared",
                  (c, bare) == (0x0B, True),
                  f"read {c!r}, bare={bare}  (expected 11, True)"))
    c, bare = b3._closing_capsule(b"\x99\x99\x99\x99")
    prove.append(("⛔ and on random bytes it says NOTHING, not zero", c is None,
                  f"read {c!r}  (expected None — «0» would be the code that "
                  f"§3.1 forbids)"))

    # ── road 1: the framing of the FAREWELL ─────────────────────────────────
    #    The REAL `_browse`, the one that runs on the wire, is called from outside.
    class Fake:
        def __init__(self):
            self.incoming = bytearray()
            self.messages = asyncio.Queue()

    f = Fake()
    f.incoming += farewell(0x0E, "disposizione sconosciuta: zz")
    b3.Client._browse(f)
    try:
        kind, body, _ = f.messages.get_nowait()
        ok = (kind == FAREWELL and body[0] == 0x0E)
        det = struct.unpack("!H", body[1:3])[0]
        ok = ok and body[3:3 + det].decode() == "disposizione sconosciuta: zz"
        prove.append(("the FAREWELL is parsed, reason and detail", ok,
                      f"kind={kind:#06x} reason={body[0]:#04x}"))
    except asyncio.QueueEmpty:
        prove.append(("the FAREWELL is parsed, reason and detail", False,
                      "no message from the reader"))

    f = Fake()
    f.incoming += farewell(0x0E, "tronco")[:-3]
    b3.Client._browse(f)
    prove.append(("⛔ and a truncated FAREWELL does NOT become a reason",
                  f.messages.empty(),
                  "the reader produced a message from incomplete bytes"
                  if not f.messages.empty() else "nothing, as it must"))
    return prove


def certify_denominator(cases, excluded_list=None):
    """⛔ M + the excluded must make fifteen, and the count is done by the program.

    A number written by hand in a comment is the number nobody recomputes:
    finding R7.14 found three of them in B5, and none of the three matched the
    file.
    """
    provokable = {c[1] for c in cases}
    excluded = {c for c, _ in (excluded_list if excluded_list is not None
                              else EXCLUDED)}
    duplicates = provokable & excluded
    all_items = provokable | excluded
    if duplicates:
        return False, ("these reasons can be provoked AND are excluded: "
                       + " ".join(REASONS[c] for c in sorted(duplicates)))
    if all_items != set(REASONS):
        missing = set(REASONS) - all_items
        return False, ("§8.2 has 15 reasons and this bench names "
                       f"{len(all_items)}: missing "
                       + " ".join(REASONS[c] for c in sorted(missing)))
    return True, (f"{len(provokable)} that can be provoked + {len(excluded)} excluded "
                  f"= {len(REASONS)} reasons of §8.2")


# ===========================================================================
# ⛔ THE EXCLUSIONS ARE MEASURED — that of `SERVER_CLOSING` above all.
# ===========================================================================
def measured_exclusion(sources):
    """How many times `RCP_SERVER_CLOSING` appears in the sources OF THE TARGET.

    ⛔⭐ AND THE SOURCES ARE NOT `rcp.c`, or not only.  Until 11 Aug 2026
        this function looked at `rcp.c` and that was it — and `rcp.c` is
        **identical byte for byte in the two servers** (md5 `cb7af778…`).
        Pointed at the product it would have said «zero occurrences», that is it
        would have declared NOT producible a reason the product produces, and B7
        would have printed «7 out of 7» on a server that does eight.
        ⚠ It is `LEZIONI.md` §1.9 corollary 5 in our own house: *a denominator is
        read where the thing happens*.  A shutdown path cannot live in `rcp.c`,
        which does not even know a process exists: on the product it lives in
        `main.c`, `trasporto.c` and `webtransport.c`.

    ⭐ The positive control stays on the same line: `RCP_TIMED_OUT` is surely
       there, and if the reader did not find even that one its «zero» would be
       worth nothing.

    Returns `(quanti, testo)`, with `quanti = None` if it could not be looked at.
    """
    amount, check, readings, missed = 0, 0, [], []
    for source in sources:
        try:
            with open(source, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            missed.append(f"{os.path.basename(source)} ({e.strerror})")
            continue
        amount += text.count("RCP_SERVER_CLOSING")
        check += text.count("RCP_TIMED_OUT")
        readings.append(os.path.basename(source))
    if missed:
        return None, (f"⛔ {len(missed)} sources out of {len(sources)} cannot be "
                      f"read ({', '.join(missed)}): the exclusion would stay "
                      f"ASSERTED instead of measured")
    if check == 0:
        return None, ("⛔ the reader does not find even `RCP_TIMED_OUT`, "
                      "which is surely there: its «zero» is worth nothing")
    return amount, (f"`RCP_SERVER_CLOSING`: {amount} occurrences in "
                    f"{len(readings)} files ({', '.join(readings)})  ·  positive "
                    f"control `RCP_TIMED_OUT`: {check}")


# ===========================================================================
# What happened, from the receiving side.
# ===========================================================================
class Outcome:
    def __init__(self, which_way=None):
        self.which_way = which_way
        self.reason = None        # from the FAREWELL — NEVER deduced, NEVER from the log
        self.reason_type = None   # ⛔ in WHICH message (§11, §4.4)
        self.detail = ""
        self.code_wt = None     # §3.1 point 3, read on the wire
        self.log_line = None # §3.1 point 1
        self.al_server = {}       # the client→server direction, from the log
        self.slot_free = None  # the observable consequence on the wire
        self.messages = []
        self.caused = False    # ⛔ did the provocation really leave?
        self.phase = "opening"
        self.wait_ms = None
        self.error = None

    def __str__(self):
        p = []
        if not self.caused:
            p.append(f"⛔ provocation NEVER LEFT (stopped in «{self.phase}»)")
        # ⚠ The first two entries say what THIS process received: they make
        #   sense only when the server is the one closing.  In the other
        #   direction whoever receives is the server, and printing them «absent»
        #   would invite reading a silence as a fault.
        if self.which_way != DIR_CS:
            if self.reason is not None:
                p.append(f"FAREWELL={self.reason:#04x}="
                         f"{REASONS.get(self.reason, '?')} in {self.reason_type}")
            elif self.reason_type is not None:
                p.append(f"{self.reason_type} without a readable reason")
            else:
                p.append("FAREWELL=(absent)")
            p.append("chiusura-WT=" + ("(absent)" if self.code_wt is None
                                       else f"{self.code_wt:#04x}"))
        for k, v in self.al_server.items():
            p.append(f"{k}={'yes' if v else 'NO'}")
        if self.slot_free is not None:
            p.append("place=" + ("free" if self.slot_free else "TAKEN"))
        if self.wait_ms is not None:
            p.append(f"after {self.wait_ms:.0f} ms")
        if self.error:
            p.append(f"error={self.error}")
        return "  ".join(p)


async def observe(cli, es, wait, grace=3.0):
    """⛔ The two roads, and BOTH are waited for — even when the first is missing.

    The `FAREWELL` travels on the control channel, the closing of the session is
    a capsule on the CONNECT stream: they are two roads and they arrive at two
    different moments.  ⭐ The server spaces them on purpose by five write
    passes (half a second), because otherwise the browser processes the capsule
    before the bytes of the stream and **nobody sees the `FAREWELL`**.

    ⛔ And the grace is waited for EVEN if the `FAREWELL` did not arrive: it is the
       case of the §C1 fault — farewell removed, code left — and a bench that
       stopped looking at the second road when the first is missing could not
       say WHICH of the two is missing.
    """
    clock = asyncio.get_event_loop().time
    t0 = clock()
    expiry = t0 + wait
    while True:
        stays = expiry - clock()
        if stays <= 0:
            break
        try:
            m = await asyncio.wait_for(cli.messages.get(), timeout=stays)
        except asyncio.TimeoutError:
            break
        if m is None:            # connection terminated, or FIN on control
            break
        kind, body, _ = m
        es.messages.append(kind)
        if kind in (FAREWELL, REJECTED):
            es.reason_type = "FAREWELL" if kind == FAREWELL else "REJECTED"
            es.wait_ms = (clock() - t0) * 1000
            # ⛔ An EMPTY body is not «no reason»: §7.1 wants the reason byte,
            #    and §3.1 forbids code 0.  With `body[0] if body` a server
            #    that closes BADLY would be easier to let through than one that
            #    closes well (finding R7.2).
            if not body:
                es.error = (f"{es.reason_type} with an EMPTY body: §7.1 wants "
                             "at least the reason byte")
                break
            es.reason = body[0]
            if kind == FAREWELL and len(body) >= 3:
                n = struct.unpack("!H", body[1:3])[0]
                es.detail = body[3:3 + n].decode("utf-8", "replace")
            break
    fine = clock() + grace
    while cli.close_code is None and clock() < fine:
        await asyncio.sleep(0.02)
    es.code_wt = cli.close_code


# ===========================================================================
# The field: the connections of a case, and their closing.
# ===========================================================================
class Field:
    def __init__(self, a, stack, log, start):
        self.a = a
        self.stack = stack
        self.log = log
        self.start = start      # the marker in the server log

    async def do_open(self, fpath="/rcp/1"):
        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536)
        conf.verify_mode = ssl.CERT_NONE
        authority = f"{self.a.address}:{self.a.port}"
        handler = connect(self.a.address, self.a.port, configuration=conf,
                          create_protocol=Client)
        cli = await handler.__aenter__()
        self.stack.push_async_callback(close_plan, handler)
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.open_session(authority, fpath)
        state = await asyncio.wait_for(cli.accepted, timeout=8)
        if state != "200":
            raise RuntimeError(f"the extended CONNECT answered {state}")
        return cli

    async def here_i_am(self, cli, body=None):
        cli.open_control()
        cli.send_msg(body if body is not None else ciao())
        return await b3.should_wait(cli, "HERE_I_AM")

    async def admitted(self, cli):
        await self.here_i_am(cli)
        cli.send_msg(wrap(0x0003, s(self.a.user) + s(self.a.password)))
        return await b3.should_wait(cli, "ADMITTED", wait=20)

    async def session(self, cli, avail="it"):
        await self.admitted(cli)
        cli.send_msg(attach(avail=avail))
        return await b3.should_wait(cli, "SESSION")


async def close_plan(handler):
    try:
        await handler.__aexit__(None, None, None)
    except Exception:  # noqa: BLE001
        pass


# ===========================================================================
# ⛔ THE CASES.  Each declares BEFORE measuring: the expected reason, the
#    direction, and **which roads of §3.1 are enforceable** — which is the
#    declaration that prevents saying «Firefox does not say farewell».
# ===========================================================================
CASES = []
DIR_SC, DIR_CS = "server→client", "client→server"


def test_case(name, reason, which_way, routes, explain):
    def dec(f):
        CASES.append((name, reason, which_way, routes, explain, f))
        return f
    return dec


# ── the server→client direction: both roads are demanded ───────────────────
#
# ⛔ In ALL these cases the control channel is open and usable at the instant
#    the server takes leave — the bench opens it, and the server does not take
#    leave before it exists.  So here the conditional of §3.1 point 2 **does not
#    bite**, and demanding the `FAREWELL` is not giving red to right code (which
#    was the fear of finding R3.3).  The case where the conditional bites is in
#    the other direction, and it is `chiuso-dall-utente-alla-firefox`.
@test_case("errore-protocollo", PROTOCOL_ERROR, DIR_SC, ("congedo", "closure"),
      "a type that does not exist on the control channel: §3 forbids ignoring it")
async def _(field, es):
    cli = await field.do_open()
    await field.here_i_am(cli)
    es.phase = "provocation"
    cli.send_msg(wrap(0x00FF, b""))
    es.caused = True
    await observe(cli, es, wait=12)


@test_case("versione-incompatibile", INCOMPATIBLE_VERSION, DIR_SC,
      ("congedo", "closure"),
      "HELLO(version=2) on /rcp/1: §2.2 wants the two to coincide")
async def _(field, es):
    cli = await field.do_open()
    cli.open_control()
    es.phase = "provocation"
    cli.send_msg(ciao(version=2))
    es.caused = True
    await observe(cli, es, wait=12)


@test_case("niente-in-comune", NOTHING_IN_COMMON, DIR_SC, ("congedo", "closure"),
      "`audio.codec = opus` without `pcm`: §4.3 requires it on both sides, and "
      "whoever does not declare it takes leave with NOTHING_IN_COMMON — not with "
      "PROTOCOL_ERROR: it did not misspell, it has nothing to talk about")
async def _(field, es):
    cli = await field.do_open()
    cli.open_control()
    es.phase = "provocation"
    cli.send_msg(ciao([("video.codec", "hevc"), ("video.depth", "8"),
                    ("audio.codec", "opus")]))
    es.caused = True
    await observe(cli, es, wait=12)


@test_case("tempo-scaduto", TIMED_OUT, DIR_SC, ("congedo", "closure"),
      "the control channel is opened and ONE KEEPS QUIET: §4.6, the cap for the HELLO. "
      "⚠ B7 demands the REASON, not the value of the cap: B6 measures the seconds")
async def _(field, es):
    cli = await field.do_open()
    cli.open_control()
    # ⛔⭐ AND HERE ONE PUSHES, BECAUSE SILENCE DOES NOT SEND ITSELF.
    #
    #    `create_webtransport_stream` writes the stream header —
    #    `0x41` plus the session identifier — but `aioquic` sends nothing until
    #    it is told `transmit()`.  ⚠ Without this line the server would see
    #    **no** stream, would open no RCP session, and the clock of the §4.6 cap
    #    would never start: the bench would wait twenty seconds and write
    #    «TIMED_OUT does not arrive» on a server that never knew it had to
    #    count.
    #
    # ⭐ From here on the provocation IS the silence, and it has left: the
    #    channel exists on the server's side, and the bench sends nothing more.
    cli.transmit()
    es.phase = "provocation"
    es.caused = True
    await observe(cli, es, wait=20)


@test_case("sessione-non-servibile", SESSION_UNSERVABLE, DIR_SC,
      ("congedo", "closure", "detail"),
      "ATTACH with layout `zz`: WELL FORMED and unknown to the machine "
      "(§4.5 wants two different faults).  ⛔ And §8.2 requires the `detail` in "
      "the body — which is written in the log and NOT shown to the user")
async def _(field, es):
    cli = await field.do_open()
    await field.admitted(cli)
    es.phase = "provocation"
    cli.send_msg(attach(avail="zz"))
    es.caused = True
    await observe(cli, es, wait=12)


@test_case("gia-attiva-remota", ALREADY_ACTIVE_REMOTELY, DIR_SC, ("congedo", "closure"),
      "two clients of the same user: the SECOND gets 0x0F (I2, §8.2). "
      "⛔ And the first must have reached SESSION, or the red and the green "
      "would mean the same thing")
async def _(field, es):
    first = await field.do_open()
    await field.session(first)          # ⛔ if this fails, `caused`
    es.phase = "provocation"              #    stays false: it is not a failed
    second = await field.do_open()         #    test, it is a test not done
    await field.admitted(second)
    second.send_msg(attach())
    es.caused = True
    await observe(second, es, wait=12)


# ── the client→server direction: whoever receives is the server, and the roads are two ──
async def look_slot(field, es):
    """⛔ THE PLACE IS LOOKED AT WHILE THE CONNECTION IS STILL ALIVE.

    §4.2 and §8.2 `0x0F`: whoever takes leave leaves the place **immediately**,
    because the session is over — not «when the transport has finished
    tearing down».

    ⚠ And this is the difference the measurement makes.  If the place were
      looked at after having closed the connection, the connection's destructor
      would free it and the line would be green **even with the farewell
      ignored**: it is exactly the defect B11 found on 10 Aug 2026 with Chrome —
      *«a BROWSER closes the session and keeps the connection alive, and from
      that moment the place stays occupied by a session that no longer
      exists»*, seven `posto NEGATO` out of nine.  ⭐ Here the case's connection
      is still open, so only the farewell can have freed the place.
    """
    free_slot, why = await full_handshake(field.a)
    es.slot_free = free_slot
    if not free_slot:
        es.error = (es.error or "") + f" · the place is NOT free: {why}"



@test_case("chiuso-dall-utente-alla-chrome", CLOSED_BY_USER, DIR_CS,
      ("congedo", "closure", "posto"),
      "what Chrome does: `FAREWELL(0x01)` on the channel **and** the session closed "
      "with code 0x01.  §8.1 requires both of whoever closes")
async def _(field, es):
    cli = await field.do_open()
    await field.session(cli)
    es.phase = "provocation"
    cli.send_msg(farewell(CLOSED_BY_USER, "bench B7 closes, as the user "
                                          "would"))
    await asyncio.sleep(0.3)   # ⚠ the two bytes must not leave in the same
    cli.close_session(CLOSED_BY_USER)   # flight: it is the race B11
    es.caused = True                       # found, here from the client's side
    await asyncio.sleep(0.5)
    await look_slot(field, es)


@test_case("chiuso-dall-utente-alla-firefox", CLOSED_BY_USER, DIR_CS,
      ("closure", "posto"),
      "⛔ what Firefox does: the session closes with code 0x01 and the control "
      "channel gets RESET, without any FAREWELL. §3.1 point 2 is "
      "conditional — «if the channel is still usable» — and here it is not: "
      "⚠ calling it «does not say farewell» would be false, the reason arrives the other way")
async def _(field, es):
    cli = await field.do_open()
    await field.session(cli)
    es.phase = "provocation"
    cli.close_session(CLOSED_BY_USER)
    # ⚠ AND HERE THERE IS A DECLARED WAIT, with what it costs.
    #
    #    Firefox sends the two things in the same flight, and in that flight
    #    the order in which the server processes them decides whether the reason
    #    arrives: the reset of the channel makes the session be freed, and a
    #    capsule processed afterwards would no longer find anyone to tell.  ⛔ That
    #    race is NOT tested here — the test with the real engines is B11's — and
    #    testing it by chance, without declaring it, would give a red that changes
    #    colour at every run.  ⚠ It stays an open `[?]`, and it is written here
    #    so that someone picks it up instead of rediscovering it.
    await asyncio.sleep(0.2)
    cli.reset_control()
    es.caused = True
    await asyncio.sleep(0.5)
    await look_slot(field, es)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⛔ THE CASE THAT EXISTS ONLY AGAINST THE PRODUCT — `SERVER_CLOSING` 0x0C.
#
# *«And `0x0C` changed subject on the night of 10 August, and it is the first
# place where the two servers diverge visibly: the product now has a shutdown
# path — `src/main.c` says farewell to everyone with `SERVER_CLOSING`
# before exiting — while the graft does not.»*
# (`FASI.md` §01-filo-nudo B7.)
#
# ⛔ It is the eighth reason that can be provoked, and without it B7 pointed at
#    the product would say «seven out of seven» **looking the other way**.
#
# ---------------------------------------------------------------------------
# ⛔ HOW IT IS PROVOKED, AND WHY THE BENCH KILLS ITS OWN SERVER
#
# `SERVER_CLOSING` is not provoked with a crooked byte: a `SIGTERM` to the
# process provokes it.  ⚠ So this case **shuts the server down**, and from it
# on there is nothing more to measure: it runs last, in an invocation of its
# own, and the launch script restarts the server on purpose before calling it.
#
# ⛔ And B0.5 — «after every test the server must still be there» — does NOT
#    apply here, and it is not a convenient exemption: it is the only case in
#    which the death of the server IS the thing proved.  It is declared, instead
#    of letting the B0.5 check give a red on a server that did what it had to.
#
# ---------------------------------------------------------------------------
# ⛔ AND THE SIGNAL IS SENT TO A VERIFIED PID, not to a number
#
# `/proc/<pid>/comm` says the program's name.  ⚠ The PID file may be from a
# previous run, PIDs get reused, and this server's rootfs lives in RAM: at
# reboot the numbers start again from low and that number points to **a system
# process** (finding R8.13, already paid for on `01-b2-lancia-wt.sh`).
# ⛔ If the name is not the expected one, the case sends NOTHING and declares
#    «test not done» — which is not «test failed».
@test_case("server-in-chiusura", SERVER_CLOSING, DIR_SC,
      ("congedo", "closure"),
      "⭐ ONLY AGAINST THE PRODUCT: session open, then SIGTERM to the server. "
      "§8.1 forbids closing with a silence, and src/main.c says farewell to everyone with "
      "0x0C and WAITS for the bytes to go out before exiting.  ⛔ Against the graft "
      "this case does not exist: it would wait for a farewell no line can "
      "send")
async def _(field, es):
    a = field.a
    pid = getattr(a, "pid_server", 0)
    if not pid:
        es.phase = ("⛔ no --pid-server: I have nobody to send the "
                   "signal to.  Test NOT DONE, not test failed")
        return
    # ⛔ Who is that PID?  The kernel is asked, it is not deduced (CODER.md §3.7).
    try:
        with open(f"/proc/{pid}/comm", encoding="utf-8") as fp:
            comm = fp.read().strip()
    except OSError as e:
        es.phase = (f"⛔ /proc/{pid}/comm cannot be read ({e.strerror}): the "
                   f"process is no longer there, or it is not mine.  Test NOT "
                   f"DONE — and I send no signal in the dark")
        return
    if comm != "remotix":
        es.phase = (f"⛔ PID {pid} is now «{comm}», not «remotix»: I send it "
                   f"NOTHING.  PIDs get reused (R8.13), and a SIGTERM to a "
                   f"system process is not a measurement")
        return

    cli = await field.do_open()
    # ⛔ It gets to SESSION and not to ADMITTED: the farewell of §8.1 must
    #    reach a LIVE session, and a half handshake could drop because of a
    #    §4.6 cap while we wait.
    await field.session(cli)
    es.phase = "provocation: SIGTERM to the server"
    os.kill(pid, signal.SIGTERM)
    es.caused = True
    # ⚠ The wait is 12 s and not 3: `main.c` waits up to **two seconds** for the
    #   bytes of the farewell to really go out, and `wt_beat` lets the capsule
    #   of §3.1 point 3 mature half a second after the queue emptied.  A bench
    #   that stopped looking right away would read «no closing» on a server that
    #   is still talking.
    await observe(cli, es, wait=12)


# ===========================================================================
async def still_alive(a):
    """⛔ B0.5 — after every case, the server must still be there.

    A server killed by the kernel «drops the connection» exactly like one that
    says farewell, and takes away everyone else's sessions.  ⚠ It gets to
    `HERE_I_AM` and not to `SESSION`: the second would cost the fixed second of
    §4.4-bis at every case, and the place is verified by whoever needs it.
    """
    async with contextlib.AsyncExitStack() as stack:
        field = Field(a, stack, None, None)
        try:
            cli = await field.do_open()
            await field.here_i_am(cli)
            return True, ""
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


async def full_handshake(a, avail="it"):
    """The good handshake, whole, up to `SESSION` — and then it takes leave.

    ⭐ It is three things in one: the **initial state** declared and verified (B0.1),
       the **check that says yes** (a server that took leave of everything would
       give seven reasons out of seven and no session), and the proof that **the
       place is free** — without which `gia-attiva-remota` would be green for the
       wrong reason (B0.2).
    """
    async with contextlib.AsyncExitStack() as stack:
        field = Field(a, stack, None, None)
        try:
            cli = await field.do_open()
            _, body, _ = await field.session(cli, avail)
            state = body[0]
            lar, h = struct.unpack("!II", body[1:9])
            # ⛔ One takes leave properly, instead of letting the connection
            #    drop: that way the place is free **immediately** for the next
            #    case, and not «when the transport has finished tearing down».
            cli.send_msg(farewell(CLOSED_BY_USER, "check of B7's initial "
                                                  "state"))
            await asyncio.sleep(0.3)
            cli.close_session(CLOSED_BY_USER)
            await asyncio.sleep(0.4)
            return True, f"SESSION state={state} canvas={lar}x{h}"
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


async def run_case(a, log, start, reason, which_way, f):
    es = Outcome(which_way)
    async with contextlib.AsyncExitStack() as stack:
        field = Field(a, stack, log, start)
        try:
            await f(field, es)
        except Exception as e:  # noqa: BLE001
            es.error = f"{type(e).__name__}: {e}"
            # ⛔ AND THE REASON IS NOT SCRAPED FROM THE EXCEPTION TEXT.
            #    `b3.should_wait` raises `RuntimeError("FAREWELL invece di …:
            #    reason 0x0b = PROTOCOL_ERROR")` even when what drops is the
            #    PREPARATION, and that string contains the name of the expected
            #    reason: the more broken the server is upstream, the more green
            #    the case would become (finding R7.1).  The reason is written
            #    only by `observe`, from a message that arrived on the wire.
    # ── §3.1 point 1, and the client→server direction: from the server log ──
    if start is not None:
        if which_way == DIR_SC:
            # ⛔ WITHOUT THE PREFIX, and it is not laziness — 11 Aug 2026.
            #
            #    Here there was `f"REMOTIX B3: farewell reason=…"`, that is the
            #    GRAFT's prefix.  The product writes the same line preceded by
            #    `HH:MM:SS.mmm rcp `, so against it this wait NEVER found
            #    anything: ⛔ §3.1 point 1 declared absent on EVERY case, that is
            #    a full red on a server that does write that line — measured
            #    today, 8 cases out of 8.
            #
            # ⚠ And the finding had already been written (R-A2) and declared
            #   cured: the cure had reached the launcher and not this line.  It
            #   is the shape «a cure applied in one place only», which this
            #   project pays for more often than any other.
            #
            # ⭐ The right cure is not a second prefix: it is NO prefix.
            #    `farewell reason=0xNN` is what the two servers have in common,
            #    and it is exactly the part §3.1 point 1 demands — the rest is
            #    the header of whoever writes the log, which is not part of the
            #    protocol.
            found_at, why = await log.should_wait(
                start, f"farewell reason={reason:#04x}", within=6)
            es.log_line = (found_at, why)
        else:
            for key, sentence in (
                    ("congedo-al-server",
                     f"the client takes its farewell, reason={reason:#04x}"),
                    ("chiusura-al-server",
                     f"the page closed the session, reason {reason:#04x}")):
                found_at, _ = await log.should_wait(start, sentence, within=6)
                es.al_server[key] = found_at
    return es


def needs(routes, es, reason, which_way):
    """⛔ The verdict per road, and each with its own line.

    Returns [(label, enforceable, arrived, text)].  ⚠ `esigibile = False` does
    not mean «it is not looked at»: it is looked at and printed, but it does not
    enter the denominator of that road.  It is the difference between «Firefox
    does not say farewell» and «on Firefox point 2 is not enforceable».
    """
    report = []
    if which_way == DIR_SC:
        report.append((
            "§3.1 point 1 — the «what» line in the log of whoever closes",
            es.log_line is not None,
            bool(es.log_line and es.log_line[0]),
            "" if not es.log_line else (es.log_line[1] or "present")))
        report.append((
            "§3.1 point 2 — the reason in the FAREWELL on the channel",
            "congedo" in routes,
            es.reason == reason and es.reason_type == "FAREWELL",
            "absent" if es.reason is None
            else f"{es.reason:#04x} in {es.reason_type}"))
        report.append((
            "§3.1 point 3 — the reason in the closing of the session",
            "closure" in routes,
            es.code_wt == reason,
            "absent" if es.code_wt is None else f"{es.code_wt:#04x}"))
        # ⛔ §11 is counted only if a reason DID arrive: «in which message» is
        #    not a question one can ask a silence, and counting it failed twice
        #    would inflate the red of road 2.
        report.append((
            "§11 — the reason in the right message (FAREWELL, not REJECTED)",
            es.reason is not None,
            es.reason_type == "FAREWELL",
            f"arrived in {es.reason_type}" if es.reason is not None
            else "no reason arrived: the question «in which message» "
                 "has no object"))
        if "detail" in routes:
            report.append((
                "§8.2 — the `detail` in the body (for the log, not for "
                "the user)", True, bool(es.detail),
                es.detail or "absent"))
    else:
        report.append((
            "§3.1 point 2 — the reason in the FAREWELL on the channel",
            "congedo" in routes,
            bool(es.al_server.get("congedo-al-server")),
            "the server wrote it"
            if es.al_server.get("congedo-al-server")
            else ("absent — and it is expected: the channel is reset"
                  if "congedo" not in routes else "absent")))
        report.append((
            "§3.1 point 3 — the reason in the closing of the session",
            "closure" in routes,
            bool(es.al_server.get("chiusura-al-server")),
            "the server wrote it"
            if es.al_server.get("chiusura-al-server") else "absent"))
        if "posto" in routes:
            report.append((
                "and the place is freed, observed ON THE WIRE", True,
                bool(es.slot_free), "free" if es.slot_free
                else "TAKEN: §8.2 0x0F to whoever has no session"))
    return report


GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def line(ok, name, text):
    print(f"    {GREEN if ok else RED}{'OK' if ok else 'NO'}{GRAY}  "
          f"{name:34s} {text}")


def inf(text):
    print(f"    --  {text}")


async def main(a):
    log = Log(a.log)
    # ⛔ The cases and the excluded are those OF THE TARGET: against the product
    #    `server-in-chiusura` is there and 0x0C leaves the excluded; against the
    #    graft it is the opposite.  ⭐ The number B7 prints next to an outcome is
    #    that of the target that was started, not that of the document.
    ALL = cases_of(a.target)
    EXCL = excluded_of(a.target)
    cases = [c for c in ALL if not a.only or a.only in c[0]]
    if a.exclude:
        before = len(cases)
        cases = [c for c in cases if a.exclude not in c[0]]
        a.manually_excluded = before - len(cases)
    else:
        a.manually_excluded = 0

    # ── --list: the predictions, and the denominator, without measuring ──
    if a.list:
        print(f"== B7 — the farewell from the receiving side\n")
        print(f"   ⛔ {len({c[1] for c in ALL})} reasons THAT CAN BE PROVOKED out of "
              f"{len(REASONS)} of §8.2, in {len(ALL)} cases.  Every line is a "
              f"PREDICTION written before measuring\n")
        for name, reason, which_way, routes, explain, _ in ALL:
            print(f"  {name:34s} {reason:#04x} {REASONS[reason]}  [{which_way}]")
            print(f"  {'':34s}   enforceable roads: {', '.join(routes)}")
            print(f"  {'':34s}   {explain}")
        print(f"\n   ⛔ AND THE {len(EXCL)} EXCLUDED, with the why — without "
              f"this list «7 out of 7» would be true by construction:\n")
        for c, why in EXCL:
            print(f"  {REASONS[c]:26s} {c:#04x}  {why}")
        ok, text = certify_denominator(ALL, EXCL)
        print(f"\n   {'⭐' if ok else '⛔'} {text}")
        return 0 if ok else 3

    # ⛔ THE RUN'S LOG — and the first line says against what one measures.
    #    Until 11 Aug 2026 B7 had none.
    a.reg = b0.Log(a.output, a.target, a.port, a.round or None,
                        a.md5 or None)
    a.reg.open_round(
        "B7", "one case per reason, each on a new connection; the "
              "farewell is read ON THE WIRE from the receiving side, never from the log "
              "of whoever sends it",
        extra={"cases": len(cases), "casi_del_bersaglio": len(ALL),
               "provocabili": len({c[1] for c in ALL}),
               "esclusi": len(EXCL), "filter": a.only,
               # ⛔ THE NUMBER THAT CHANGES WITH THE TARGET, written BEFORE
               #    measuring: seven against the graft, eight against the product.
               "attesi_provocabili": b0.profile(a.target)["motivi_provocabili"],
               "pid_server": getattr(a, "pid_server", 0)})
    print("== B7 — the farewell, verified FROM THE RECEIVING SIDE (§8.1)")
    print(f"   ⛔ TARGET: {a.target} · port {a.port} · binary md5 "
          f"{(a.md5 or 'unknown')[:12]}…")
    expected_provocable = b0.profile(a.target)["motivi_provocabili"]
    seen_orig = len({c[1] for c in ALL})
    if seen_orig != expected_provocable:
        print(f"   {RED}⛔ the reasons that can be provoked on this target should be "
              f"{expected_provocable} and the cases cover {seen_orig}{GRAY}")
        print(f"      ⛔ It is not a server red: it is the bench that cannot "
              f"count what it is about to measure.")
        return 3
    print(f"   ⛔ {seen_orig} reasons that can be provoked out of {len(REASONS)} of §8.2 — and "
          f"the number is the TARGET's, not the document's")
    print("   ⛔ for every reason: the FAREWELL on the channel **and** the code in the "
          "closing")
    print("      of the session — two roads, two counters, one `&&`\n")

    # ═══ THE CERTIFICATION, BEFORE MEASURING ═══════════════════════════════
    print("== ⭐ The bench certifies itself before pointing at the unknown "
          "(CODER.md §3.3)")
    cert_faults = 0
    ok, text = certify_denominator(ALL, EXCL)
    line(ok, "the denominator adds up", text)
    cert_faults += 0 if ok else 1
    for name, ok, text in certify_readers():
        line(ok, name, text)
        cert_faults += 0 if ok else 1
    for name, ok, text in certify_sentences():
        line(ok, name, text)
        cert_faults += 0 if ok else 1
    if a.log:
        ok, why = log.readable()
        line(ok, "the server log can be read", why or a.log)
        cert_faults += 0 if ok else 1
    else:
        inf("⚠ no --log: §3.1 point 1 and the client→server direction are NOT")
        inf("  measured, and the run will be declared PARTIAL")

    print("\n== ⭐ The initial state, declared and verified (B0.1, B0.2)")
    inf("a whole handshake: if the place were already occupied by the previous")
    inf("run, `gia-attiva-remota` would be green for the wrong reason")
    mark = log.window() if a.log else None
    ok, text = await full_handshake(a)
    line(ok, "stretta-di-mano-intera", text)
    cert_faults += 0 if ok else 1
    if a.log and ok:
        # ⭐ The positive control of the log READER, on the line that must
        #    surely be there — and the negative one on one that is not.
        found_at, why = await log.should_wait(
            mark, f"admitted user={a.user}", within=6)
        line(found_at, "⭐ the log reader finds",
             f"«admitted user={a.user}»" if found_at else why)
        cert_faults += 0 if found_at else 1
        window_text = log.da(mark) or ""
        fake = "farewell reason=0xff" not in window_text
        line(fake, "⛔ and does not find what is not there",
             "«farewell reason=0xff» is not there, as it must")
        cert_faults += 0 if fake else 1

    if cert_faults:
        print(f"\n    {RED}⛔ B7 DOES NOT MEASURE: the tool is not certified "
              f"({cert_faults} checks failed){GRAY}")
        print("       A negative outcome with an uncertified tool is")
        print("       ambiguous between «the server does not work» and «the bench")
        print("       did not work» — and this is NOT a server red.")
        return 3

    # ⛔ WITHOUT THE LOG, THE client→server CASES ARE NOT RUN.
    #
    #    There whoever receives is the server, and its log is the only witness:
    #    running them without being able to read that file would give two reds
    #    for a lack of the BENCH, and they would be reds indistinguishable from a
    #    server that ignores farewells.  ⚠ Better one measurement less, declared,
    #    than a measurement that accuses the wrong defendant.
    if not a.log:
        before = len(cases)
        cases = [c for c in cases if c[2] != DIR_CS]
        if before != len(cases):
            print(f"    {YELLOW}⚠{GRAY} without --log the {before - len(cases)}"
                  f" client→server cases are NOT run: the witness is missing")

    # ═══ THE CASES  ═════════════════════════════════════════════════════════
    if not cases:
        print(f"\n    {RED}⛔ «--only {a.only}» selected ZERO cases out of "
              f"{len(ALL)}: there is nothing to measure{GRAY}")
        print("       This is NOT a green.  The names are read with --list.")
        return 2

    print(f"\n== The cases: {len(cases)} out of {len(ALL)}, "
          f"{len({c[1] for c in cases})} reasons out of "
          f"{len({c[1] for c in ALL})} that can be provoked")
    if a.only:
        print(f"    {YELLOW}⚠ PARTIAL RUN{GRAY}: the green outcome reads «the "
              f"selected cases pass», never «B7 passes»")
    if a.manually_excluded:
        print(f"    {YELLOW}⚠{GRAY} {a.manually_excluded} cases removed by "
              f"«--exclude {a.exclude}»: the run is PARTIAL, and the green outcome "
              f"does not cover them")

    counts = {
        "§3.1 point 1 — the «what» line in the log of whoever closes": [0, 0],
        "§3.1 point 2 — the reason in the FAREWELL on the channel": [0, 0],
        "§3.1 point 3 — the reason in the closing of the session": [0, 0],
        "§11 — the reason in the right message (FAREWELL, not REJECTED)": [0, 0],
        "§8.2 — the `detail` in the body (for the log, not for the user)": [0, 0],
        "and the place is freed, observed ON THE WIRE": [0, 0],
        "⛔ the server is still there after the case (B0.5)": [0, 0],
        "§8.2 — a distinct, showable phrase, never a number": [0, 0],
    }
    faults, dead = 0, False
    # ⛔ A reason counts as «proved» only if ALL its cases pass.
    #    `CLOSED_BY_USER` has two — Chrome-style and Firefox-style — and
    #    counting it full because one of the two went well would be mistaking
    #    «one engine out of two» for «the reason is covered».
    seen_reasons, broken_reasons = set(), set()

    for name, reason, which_way, routes, explain, f in cases:
        start = log.window() if a.log else None
        es = await run_case(a, log, start, reason, which_way, f)
        seen_reasons.add(reason)
        # ⚠ The place is looked at by the CASE, with its connection still open
        #   (see `look_slot`): looking at it from here, with the connection
        #   closed, would find it free even with the farewell ignored.
        prove = needs(routes, es, reason, which_way)
        good = es.caused and es.error is None
        for label, due, landed, text in prove:
            if not due:
                continue
            # ⚠ `setdefault`: a new label is added to the summary with its
            #   denominator instead of bringing the bench down — and so whoever
            #   adds a road does not have to remember two places.
            tally = counts.setdefault(label, [0, 0])
            tally[1] += 1
            tally[0] += int(landed)
            good = good and landed
        line(good, name, str(es))
        if not good:
            broken_reasons.add(reason)
            faults += 1
            print(f"        expected: {reason:#04x} {REASONS[reason]}  "
                  f"[{which_way}]  enforceable roads: {', '.join(routes)}")
            print(f"        {explain}")
            if not es.caused:
                print(f"        ⛔ and the provocation NEVER LEFT (stopped "
                      f"in «{es.phase}»): it is not a failed test, it is a "
                      f"test not done")
            for label, due, landed, text in prove:
                if due and not landed:
                    print(f"        {RED}⛔{GRAY} {label}: {text}")
            if a.log and start is not None:
                print("        the server log, in that window:")
                for r in log.our_lines(start):
                    print(f"          {r[:150]}")
        # ⚠ The roads that are not enforceable are PRINTED anyway: it is the line
        #   that prevents reading «absent» as «broken».
        for label, due, landed, text in prove:
            if not due:
                print(f"        {YELLOW}~{GRAY} {label}: {text} "
                      f"(not enforceable in this case, and it does not enter the count)")
        if es.detail:
            print(f"        detail from the body: «{es.detail}»  "
                  f"⚠ it goes to the log, NOT to the user (§8.2)")

        # ⛔ And the fact goes into the log BEFORE any conclusion: a case that
        #    brings the bench down must have left its own line, or the log would
        #    only tell about the runs that went well.
        a.reg.write({"type": "case", "name": name, "outcome": bool(good),
                      "motivo_atteso": reason, "which_way": which_way,
                      "strade_esigibili": list(routes),
                      "motivo_visto": es.reason, "reason_type": es.reason_type,
                      "code_wt": es.code_wt, "caused": es.caused,
                      "phase": es.phase, "error": es.error,
                      "detail": es.detail,
                      "prove": [[e_, bool(x_), bool(y_)]
                                for e_, x_, y_, _ in prove]})

        # ⛔ B0.5 — «after every test the server must still be there» — AND THE
        #    CASE THAT IS THE EXCEPTION, declared instead of forgotten.
        #
        #    `server-in-chiusura` **shuts the server down on purpose**: it is the
        #    only case in which the death of the server IS the thing proved.
        #    ⚠ Running B0.5 here would give a red on a server that did exactly
        #    what §8.1 asks of it, and it would be the red on the wrong defendant
        #    inside the bench that quotes that lesson.
        if reason == SERVER_CLOSING:
            inf("⚠ B0.5 does NOT apply to this case: I turned the server off,")
            inf("  and it is the thing proved.  The count does not touch it, and this line")
            inf("  exists so that «skipped» and «passed» do not have the same")
            inf("  face")
            a.reg.write({"type": "b0.5-saltato", "name": name,
                          "why": "the case shuts the server down on purpose"})
            dead = True
            break
        tally = counts["⛔ the server is still there after the case (B0.5)"]
        tally[1] += 1
        alive, why = await still_alive(a)
        tally[0] += int(alive)
        if not alive:
            line(False, "", f"⛔ THE SERVER NO LONGER ANSWERS after «{name}»: "
                            f"{why}")
            faults += 1
            dead = True
            break

    # ═══ THE PHRASES (§8.2) ═════════════════════════════════════════════════
    #
    # ⚠ This section and the next do NOT depend on the selected cases and do not
    #   touch the server: they run even under a filter, and it is said.  (In B5
    #   the independent sections are skipped because there they really depended
    #   on the cases — here it is not so, and skipping them would hide a free
    #   measurement.)
    if not dead:
        print(f"\n== ⭐ The phrases of §8.2 — «BUDGET_FULL is not \"error 6\"»")
        inf(f"the client's TABLE is read, not the screen: whether the phrase")
        inf(f"reaches the user's eyes is the user's judgement (I8)")
        try:
            with open(a.page, encoding="utf-8", errors="replace") as fp:
                text = fp.read()
            entries, why = read_table(text)
        except OSError as e:
            entries, why = None, f"{a.page} cannot be read: {e}"
        if entries is None:
            line(False, "the table can be read", f"⛔ {why}")
            inf("⛔ and this is NOT «zero phrases»: it is «the table was not")
            inf("   read».  The count below stays without a denominator")
            faults += 1
        else:
            outcomes = judge_sentences(entries)
            counts["§8.2 — a distinct, showable phrase, never a number"][1] = \
                len(outcomes)
            for c, ok, text in outcomes:
                counts["§8.2 — a distinct, showable phrase, never a "
                      "number"][0] += int(ok)
                if not ok:
                    line(False, REASONS[c], text)
                    faults += 1
                elif a.phrases:
                    line(True, REASONS[c], f"«{text}»")
            if all(ok for _, ok, _ in outcomes):
                line(True, "the 15 phrases", f"distinct, without numbers, from the file "
                                          f"{os.path.basename(a.page)}")
                inf("(--phrases prints them all)")

        # ═══ THE MEASURED EXCLUSION — AND THE SIGN FLIPS WITH THE TARGET ═══
        #
        # ⛔ Against the GRAFT the grep must say **zero**: the reason is excluded,
        #    and the exclusion is measured instead of asserted.
        # ⭐ Against the PRODUCT it must say **more than zero**: the path exists,
        #    and it is the eighth reason that can be provoked.  ⚠ A zero here would
        #    mean I am measuring a binary **from before** that night, and the
        #    `server-in-chiusura` case would be red for the wrong reason.
        expected_positive = b0.profile(a.target)["spegnimento"]
        sources = b0.sources_shutdown(a.target, a.inside)
        print(f"\n== ⛔ The exclusion that is MEASURED: SERVER_CLOSING (0x0C)")
        inf(f"one looks WHERE THE THING HAPPENS, and on «{a.target}» that is "
            f"{len(sources)} files — ⛔ not `rcp.c` alone, which is identical "
            f"in the two servers and does not know a process exists")
        amount, text = measured_exclusion(sources)
        if amount is None:
            line(False, "the sources can be read", text)
            faults += 1
        elif expected_positive:
            line(amount > 0, "⭐ SERVER_CLOSING IS producible", text)
            if amount > 0:
                inf("⭐ and indeed those that can be provoked here are EIGHT, not seven: it is the "
                    "first")
                inf("  visible difference between the two servers (fasi/01-filo-nudo.md B7)")
            else:
                inf("⛔ ZERO occurrences on a target that should have them: either")
                inf("  I am measuring a binary from BEFORE the night of 10")
                inf("  August, or the sources are not those it was")
                inf("  built from.  ⚠ It is not «the product does not say farewell»: it is that")
                inf("  I am not looking at the product I believe")
                faults += 1
        else:
            line(amount == 0, "SERVER_CLOSING is not producible", text)
            if amount == 0:
                inf("⚠ and `FASI.md` §01-filo-nudo B7 listed it among «the eight")
                inf("  reasons this phase can produce»: against the graft")
                inf("  they are seven")
            else:
                inf("⭐ the path now exists in the graft too: it must be removed")
                inf("  from the excluded and a case written for it, or B7 counts one")
                inf("  reason fewer than the true number")
                faults += 1

    # ═══ THE SUMMARY ═══════════════════════════════════════════════════════
    print("\n    == what this run really looked at")
    for desc, (good_n, tot) in counts.items():
        if tot == 0:
            # ⛔ A zero denominator is DECLARED: «nobody looked» and «all
            #    passed» look the same if one keeps quiet.
            print(f"    --  {desc:62s} no case triggered it")
            continue
        clr = GREEN if good_n == tot else RED
        print(f"    {clr}{good_n:3d} out of {tot:3d}{GRAY}  {desc}")

    full_reasons = seen_reasons - broken_reasons
    print()
    print(f"    ⛔ the reasons: {len(full_reasons)} out of {len(seen_reasons)} "
          f"proved in this run, and those THAT CAN BE PROVOKED by phase 1 are "
          f"{len({c[1] for c in ALL})} out of {len(REASONS)} of §8.2")
    print(f"       the other {len(EXCL)} are excluded, each with its "
          f"why (--list), and the exclusion of")
    print(f"       SERVER_CLOSING is measured, not asserted")

    if dead and any(c[1] == SERVER_CLOSING for c in cases):
        # ⭐ The server died because I asked it to: it is the
        #    `server-in-chiusura` case, and the sections that follow (the phrases,
        #    the measured exclusion) do not touch the server — they run anyway.
        print(f"\n    ⚠ the server is off because this run turned it off "
              f"on purpose: the run is PARTIAL by construction")
        a.reg.write({"type": "verdict", "faults": faults, "partial": True,
                      "why": "shutdown run"})
        print(f"    --  {a.reg.summary()}")
        return 1 if faults else 0
    if dead:
        print(f"\n    {RED}⛔ the bench stopped: without a server there is "
              f"nothing to measure{GRAY}")
        a.reg.write({"type": "verdict", "faults": faults, "partial": True,
                      "why": "the server died without my asking it to"})
        return 1
    a.reg.write({"type": "verdict", "faults": faults,
                  "partial": bool(a.only or not a.log
                                   or a.manually_excluded),
                  "full_reasons": sorted(full_reasons),
                  "provocabili": len({c[1] for c in ALL}),
                  "counts": {k: v for k, v in counts.items()}})
    print(f"\n    --  {a.reg.summary()}")
    if faults:
        print(f"\n    {RED}⛔ B7: {faults} points do not pass against "
              f"«{a.target}»{GRAY}")
        return 1
    if a.only or not a.log or a.manually_excluded:
        print(f"\n    {GREEN}⭐ the measured points pass against "
              f"«{a.target}»{GRAY} — ⚠ and this is NOT «B7 passes»: the run "
              f"was partial")
        return 0
    print(f"\n    {GREEN}⭐ B7 passes: {len(full_reasons)} out of "
          f"{len({c[1] for c in ALL})} reasons that can be provoked, by BOTH "
          f"roads of §3.1,{GRAY}")
    print(f"    {GREEN}      and 15 distinct phrases out of 15 — and the numbers above "
          f"say on what{GRAY}")
    return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT GO THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ `--password` ends up in the process `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` launched by another user
#    during the run prints it in full.
#
# ⭐ The good road already existed in the house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600` file
#    that the launcher writes with `printf` — a shell **builtin**, so not even
#    the writing goes through a process with the password in `argv` — and
#    deletes with a `trap`.
#
# ⚠ And `--password` was NOT removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse than
#   the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is form
#   **E2** — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--password` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written
#   in the code is in no command line, and telling it otherwise would be an
#   alarm one learns to ignore.
def password_from_args(a):
    """The password: from `--password-file` if present, from `--password` otherwise.

    ⛔ And the three ways of failing are told apart: «cannot be read», «is
    readable by others» and «is empty» have three different cures, and an empty
    file is NOT an empty password — it is «the launcher did not write it»
    (`LEZIONI.md` §1.9).
    """
    fpath = getattr(a, "password_file", "") or ""
    if fpath:
        try:
            mode = os.stat(fpath).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ the password file «{fpath}» cannot be read: {e}")
            sys.exit(2)
        if mode:
            print(f"   ⚠ «{fpath}» is readable by others (bits {mode:o}): the "
                  f"secret is not protected")
        try:
            with open(fpath, encoding="utf-8") as f:
                password = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ the password cannot be read from «{fpath}»: {e}")
            sys.exit(2)
        if not password:
            print(f"   ⛔ the password file «{fpath}» is EMPTY.  It is not")
            print("      «the password is empty»: it is «the launcher did not write it».")
            sys.exit(2)
        return password
    if any(x == "--password" or x.startswith("--password=") for x in sys.argv[1:]):
        print("   ⚠ D12: the password arrived from `--password`, that is from the")
        print("     COMMAND LINE: it is in `/proc/<pid>/cmdline` and anyone who")
        print("     runs `ps` on this machine sees it.  The run goes on — the caller")
        print("     has not been cured — but it is not a private run.")
        print("     ⭐ The cure: `--password-file <0600 file>`, as in B10.")
    return a.password


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B7 — the farewell, verified from the receiving side")
    p.add_argument("--address", default="192.168.0.2")
    # ⛔ No default that names a target: 7447 is the graft and 7448 the
    #    product, and a default here would mean that «--target product»
    #    without «--port» measures the graft while declaring the product.
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--user", default="prova")
    p.add_argument("--password", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--password` if
    #    both are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--password-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--inside", default=HERE,
                   help="the root of the sources from which the exclusion "
                        "of SERVER_CLOSING is measured (depends on the target)")
    # ⛔ The server's PID, for the `server-in-chiusura` case only.  Zero means
    #    «they did not tell me», and that case is declared NOT DONE instead of
    #    sending a signal in the dark.
    p.add_argument("--pid-server", type=int, default=0,
                   help="the server's PID, to provoke SERVER_CLOSING")
    p.add_argument("--log", default="",
                   help="the server log: needed for §3.1 point 1 and for the "
                        "client→server direction")
    p.add_argument("--page", default=os.path.join(HERE, "01-b11-pagina.html"),
                   help="the file where the table of the §8.2 phrases lives")
    p.add_argument("--only", default="",
                   help="run only the cases that contain this")
    # ⛔ `--exclude` and not «--only everything except»: `server-in-chiusura` SHUTS
    #    the server DOWN, so the normal run leaves it out and the launch script
    #    calls it afterwards, with the server restarted on purpose.  ⚠ A filter
    #    that removed a case silently would make «N out of N» true by construction:
    #    here the removed case is printed, and the denominator stays the target's.
    p.add_argument("--exclude", default="",
                   help="does NOT run the cases that contain this, and declares it")
    p.add_argument("--phrases", action="store_true",
                   help="print all fifteen phrases of §8.2")
    p.add_argument("--list", action="store_true",
                   help="print the predictions and the denominator, without measuring")
    b0.add_arguments(p)
    # ⚠ `--list` does not measure and does not need a port.
    if "--list" in sys.argv:
        for _az in p._actions:
            if _az.dest == "port":
                _az.required = False
    a = p.parse_args()
    a.password = password_from_args(a)
    sys.exit(asyncio.run(main(a)))
