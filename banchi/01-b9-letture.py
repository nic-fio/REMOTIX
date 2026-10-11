#!/usr/bin/env python3
"""01-b9-letture.py — ⭐ B9: the points where `RCP.md` allowed TWO readings.

    python3 01-b9-letture.py                 the inventory, with the bytes compared
    python3 01-b9-letture.py --byte          and prints the hex in full
    python3 01-b9-letture.py --list        only the titles, without building anything

⚠ It runs ANYWHERE: it does not touch the network and does not want a server.  It
  reads two files — `RCP.md` and `01-b3-cliente.py` — and builds bytes.  The piece
  that wants a server is another file, `01-b9-sonda.py`, and it says which of the
  two readings the SERVER chose.

===========================================================================
⛔ WHAT THIS BENCH IS, AND WHY IT HAS NO «PASS»

`FASI.md` §01-filo-nudo B9, last line of the table:

    ⚠ **the most precious outcome is not «passes»**: it is **every point where
      whoever writes it had to choose** because `RCP.md` allowed two readings.
      Those points go into «what did NOT work», and they are defects **of the
      document**.

⛔ Hence the shape of this file: **it is not a bench that promotes the test
   client**, it is a bench that **counts the points where the document did not
   decide**.  The number it delivers is that one, and the green below means only
   *«the inventory is whole and every entry holds»*, never *«RCP is without
   ambiguity»*.

⭐ And every entry carries **the byte that changes on the wire between the two
   readings**, not an explanation: if two readings produced the same bytes they
   would not be two readings, they would be two ways of saying the same thing.
   ⛔ This file **verifies** it, entry by entry (`check_byte`), and an entry
   whose two bytes match is a defect **of this bench** — it turns red.

===========================================================================
⛔ THE INITIAL STATE, AND HERE IT IS MADE OF PAPER (B0.1)

A bench that reads documents has as its initial state **the text it read**.
`RCP.md` and `01-b3-cliente.py` change under its feet — others write them, even
tonight — and an entry that quotes a line that has disappeared would be
describing a document that no longer exists.

⛔ Hence: every entry declares its **anchors** — exact pieces of text that must
   appear in the two files — and the bench looks for them **before** giving any
   verdict.  An anchor that is not found is NOT «the entry is wrong»: it is
   `[?]` **the document changed under the bench**, which is a third thing and
   has a different cure (rereading, not correcting).

⚠ And the two files are looked for **next to this one**, that is in the copy
  that is running: reading an `RCP.md` from another copy would speak of a
  document that is not the one the test client was written against.

===========================================================================
⛔ THE DENOMINATOR, AND THE FOUR COLUMNS THAT ARE NOT THE SAME THING

  ENTRIES          how many times the document allowed two readings;
  CON APPIGLI   of those, how many could be **verified on the text** today;
  SUL WIRE      of those, how many produce **different bytes** — that is how
                many a bench can go and look at;
  PROVATE       ⛔ of those, how many were measured **on the behaviour** of the
                test client instead of on its quotation.  It is the column born
                from finding A8 (11 Aug 2026): an anchor can be left standing
                while the behaviour changes, and for one night this bench was
                green on a client that had already changed reading.  The box is
                above `extract_functions`.

⛔ The three never coincide, and printing only one of them would be the shape of
   `LEZIONI.md` §1.9: *«the verdict on zero things»* and *«the false
   denominator»*.  The entry **R3.27** is the one that proves it: it is a real
   ambiguity, and on the wire **no byte of the request changes** — what changes
   is *when* the `FAREWELL` arrives, and in the worst case *whether* it arrives.
   It is declared that way, instead of being inflated with an invented byte to
   make the column add up.

===========================================================================
⛔ THE MECHANISM OF B9, AND THIS FILE CANNOT GUARANTEE IT

`FASI.md` §01-filo-nudo B9: the separation between whoever writes the test client
and whoever writes the server **must be a mechanism, not a rule** — *«whoever
writes the client receives `RCP.md` and its references, and not the tree of the
server and of the page»*.

⚠ **This file is not that mechanism and does not prove it.**  It only says what
  the test client chose, by reading the test client.  ⛔ If whoever wrote it had
  looked at `rcp/rcp.c`, the choices would match the server's **and this file
  would print the same lines**: the agreement could not tell «they read the same
  document» from «they copied».  It is fault **B9** that B12 builds on purpose
  (*«the test client that read the C»*), and without it this line stays a
  declaration.

===========================================================================
⭐ AND THE TWO ENTRIES THAT ARE WORTH MORE THAN THE OTHERS

  L4  the tail of bytes at the end of the body: the **test client** tolerates it
      and the **B4 validator** rejects it.  They are our two independent readers
      of §6.1, and they read **two different things** — that is exactly the
      object B9 exists to produce, found at home and not in theory;

  L11 the version in the `HELLO` when the path is `/rcp/1`: §9 orders declaring
      **the highest one can speak**, §2.2 says that a version different from the
      path is `INCOMPATIBLE_VERSION`.  For a client that spoke 1 **and** 2 the
      two lines order the opposite, and today it does not bite only because
      RCP/2 does not exist.
"""
import argparse
import ast
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def search_upward(name, da):
    """Looks for `name` walking up the folders.  ⛔ Returns None if it is not there.

    ⚠ It is not convenience: B12 runs a COPY of this bench inside
      `01-b12-copie/`, that is one folder further down — and a path computed
      with a single `dirname` would lead to an `RCP.md` that is not there.  The
      bench would exit «I could not read» **while B12 is measuring something
      else entirely**, and the certification would record a red with the wrong
      cause.
    """
    d = da
    for _ in range(6):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
        su = os.path.dirname(d)
        if su == d:
            break
        d = su
    return None


ROOT = os.path.dirname(HERE)
RCP_MD = search_upward("RCP.md", HERE) or os.path.join(ROOT, "RCP.md")
CLIENT = os.path.join(HERE, "01-b3-cliente.py")

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
# The bricks of the wire, rewritten HERE and not imported from the test client.
#
# ⛔ It is not duplication by distraction: if this file imported `wrap()`
#    from the client, the two readings of §6.1 would **both** come out of the
#    client's reading, and entry L4 would compare the client with itself.
#    The bytes of the two readings are built by hand, from the document.
# ===========================================================================
def u16(v):
    return struct.pack("!H", v)


def u32(v):
    return struct.pack("!I", v)


def string(t):
    """§6.0: `u16 length` + `length` bytes of UTF-8, without terminator."""
    b = t.encode("utf-8") if isinstance(t, str) else t
    return u16(len(b)) + b


def framing(kind, body, length=None):
    """§6.1: `u16 type` · `u32 length` · body.

    `length` can be forced: it serves entry L4, where the point is precisely
    that the declared number and what the type expects do not coincide.
    """
    return u16(kind) + u32(len(body) if length is None else length) + body


def capabilities(entries):
    out = u16(len(entries))
    for n, v in entries:
        out += string(n) + string(v)
    return out


def ciao(version=1, entries=None):
    entries = entries if entries is not None else [
        ("video.codec", "hevc,av1"), ("video.depth", "8,10"),
        ("audio.codec", "opus,pcm"), ("client.name", "test-client 0.1.0")]
    return framing(0x0001, u16(version) + capabilities(entries))


def here_i_am(entries):
    return framing(0x0002, u16(1) + capabilities(entries))


def closing_capsule(code, width=4, inside_data=True):
    """The `CLOSE_WEBTRANSPORT_SESSION` capsule (0x2843), as the wire sees it.

    ⚠ The type and the length are QUIC variable-length integers: `0x2843` fits
      in two bytes with the two high bits at `01`, that is `0x68 0x43`.
    """
    body = code.to_bytes(width, "big")
    capsule = b"\x68\x43" + bytes([len(body)]) + body
    if not inside_data:
        return capsule
    # RFC 9297: on the wire of the CONNECT the capsules travel inside DATA frames
    return b"\x00" + bytes([len(capsule)]) + capsule


# ===========================================================================
# THE INVENTORY.
#
# ⛔ Every entry declares its ANCHORS before declaring its thesis: a quotation
#    that can no longer be found is an entry that speaks of another document,
#    and it must be said instead of believed.
# ===========================================================================
ENTRIES = []


def entry(tag, dove, question, reading_a, reading_b, choice, bites,
         footholds_rcp=(), footholds_client=(), byte=None, note=""):
    ENTRIES.append({
        "tag": tag, "where": where, "question": question,
        "a": reading_a, "b": reading_b, "choice": choice, "bites": bites,
        "footholds_rcp": list(footholds_rcp),
        "footholds_client": list(footholds_client),
        "byte": byte, "note": note,
    })


# ── L1 ──────────────────────────────────────────────────────────────────────
entry(
    "L1", "§4.3",
    "Does `HERE_I_AM` carry the server's LIST of codecs, or THE CHOICE?",
    "A — the list: §4.3 says «capabilities of the server», and the choice travels only "
    "in the server log and then in the `codec` field of the frame "
    "header (§6.2)",
    "B — the choice: §4.3 says «The one who chooses is the server», and the only place "
    "where the client could read it is this capability",
    "the test client **reads no capability of `HERE_I_AM`**: it reads the "
    "two bytes of the version and throws away the rest.  It is reading A by omission, "
    "that is the choice made without noticing it was making it",
    "in phase 2, on the first frame: a client that had read B "
    "would configure the decoder on the first element of the list and "
    "would guess right **as long as the server's order coincides with the intersection**. "
    "The symptom, far from here, is «the browser does not open the stream» — the same "
    "as finding O12 on `video.level`",
    footholds_rcp=[
        "| **HERE_I_AM** | server → client. Chosen version, server capabilities |",
        "⛔ **The one who chooses is the server**, inside the intersection",
        "The choice **MUST** be written in the server log",
    ],
    footholds_client=['versione = struct.unpack("!H", corpo[:2])[0]'],
    byte=lambda: (
        here_i_am([("video.codec", "hevc,av1"), ("video.depth", "8,10"),
                ("audio.codec", "opus,pcm")]),
        here_i_am([("video.codec", "hevc"), ("video.depth", "8"),
                ("audio.codec", "opus")]),
        "the value of `video.codec` inside `HERE_I_AM`: `0008 «hevc,av1»` against "
        "`0004 «hevc»` — and with it the u32 `length` of the framing",
    ),
)

# ── L2 ──────────────────────────────────────────────────────────────────────
entry(
    "L2", "§3.1 point 3",
    "How wide is the «application error code equal to the reason code», "
    "and does the bare reason go there or the mapped reason?",
    "A — the bare reason inside the 32 bits of the capsule: `00 00 00 0D`",
    "B — the reason transformed by the mapping that WebTransport over HTTP/3 "
    "imposes on error codes, which scatters the low values over the whole "
    "HTTP/3 space",
    "the test client reads **the last of the four bytes** and takes it for the "
    "reason (`_closing_capsule`, `return b[j + 3]`): it is reading A, **and on "
    "top it truncates** — a code above 255 would reach it as another reason, "
    "without a line saying so",
    "the day an implementation applied the mapping, the reason "
    "would arrive as a huge number and the reader would print its low "
    "byte: **a wrong reason instead of an error**, which is worse than a "
    "silence (§3.1: «The third point is the one that saves diagnoses»)",
    footholds_rcp=[
        "**MUST** close the **WebTransport session** with the application error "
        "code equal to the\n   **reason code** of §8.2",
    ],
    footholds_client=["return b[j + 3]      # the four bytes of the code, the lowest"],
    byte=lambda: (
        closing_capsule(0x0D),
        closing_capsule(0x52E4A40FA8DB + 0x0D, width=8),
        "the bytes of the code inside the `0x2843` capsule: `00 00 00 0D` against "
        "eight bytes of a mapped value — and the capsule itself changes length",
    ),
    note="⚠ `RCP.md` does not declare the width of the field anywhere: only "
         "the WebTransport format declares it, which RCP does not name.",
)

# ── L3 ──────────────────────────────────────────────────────────────────────
entry(
    "L3", "§3.1 point 2 against §4.2",
    "After the `FAREWELL`, does the control channel close with a FIN, or "
    "does only the session close?",
    "A — `FAREWELL` **with** the FIN on the control channel, then the closing "
    "of the session: §4.2 says that the FIN on that stream **is** the end "
    "of the session, so it is the most explicit way of saying it",
    "B — `FAREWELL` **without** FIN, and the end is declared only by the closing of the "
    "session (§3.1 point 3)",
    "the test client never sends a `FAREWELL`; and when it sends "
    "anything it uses `end_stream=False`, that is reading B.  ⛔ And on the side "
    "that receives it calls the FIN «the control channel has closed», which is "
    "a **different** outcome from «session closed by the server»",
    "whoever waits for the FIN to declare the session over stays hanging against "
    "whoever closes only the session; and whoever sends the FIN **before** the closing "
    "makes §4.2 trigger first, so the peer records «channel closed» instead "
    "of the reason.  It is the same family as finding R1.4, on the same point",
    footholds_rcp=[
        "⛔ **In bytes**: a FIN on that stream, from either of the two parties, "
        "closes the session.",
        "**MUST** send `FAREWELL` (§8) with the reason, on the control channel",
    ],
    footholds_client=[
        "self._quic.send_stream_data(self.controllo, dati, end_stream=False)",
        'self._cade("the control channel has closed")',
    ],
    byte=lambda: (
        framing(0x000C, bytes([0x01]) + string("")) + b"<FIN>",
        framing(0x000C, bytes([0x01]) + string("")),
        "the FIN bit of the STREAM frame carrying the `FAREWELL` — the same payload "
        "bytes, one transport bit more",
    ),
    note="⚠ The `<FIN>` above is written in plain text because it is NOT a byte "
         "of the payload: it is a bit of the header of the QUIC STREAM frame, and "
         "pretending to be able to print it as payload would be a convenient lie.",
)

# ── L4 ──────────────────────────────────────────────────────────────────────
entry(
    "L4", "§6.1",
    "⭐ Extra bytes at the end of the body, with the `length` counting them: are they "
    "a violation or are they a reserve for future versions?",
    "A — violation: §6.1 wants `length` to be «the exact number of bytes "
    "of the body», and a body longer than what the type expects is «a "
    "length inconsistent with what the type provides for» ⇒ `PROTOCOL_ERROR`",
    "B — reserve: `length` is authoritative, the fields the type "
    "declares are read and the rest is skipped.  It is the only way §9 could "
    "widen a message without changing the major version",
    "⛔ **Our two readers chose differently**: the test client "
    "reads `length` bytes and passes the body on as it is without ever checking "
    "that it consumed it all (reading B, tolerant); the B4 validator has "
    "a recording on purpose — `10-coda-di-spazzatura.rcpreg` — that is "
    "reading A",
    "it is the defect this bench exists to find: **the arbiter and the "
    "second reader do not read the same specification**.  As long as nobody sends "
    "extra bytes nothing happens; the day it happens, one of the two "
    "says compliant and the other closes the connection",
    footholds_rcp=[
        "⛔ `length` **MUST** be the exact number of bytes of the body.",
        "A receiver that reads a\nlength inconsistent with what the type provides "
        "for **MUST** close with `PROTOCOL_ERROR`.",
    ],
    footholds_client=[
        'tipo, lung = struct.unpack("!HI", self.arrivati[:6])',
        "corpo = bytes(self.arrivati[6:6 + lung])",
    ],
    byte=lambda: (
        (lambda c: framing(0x0001, c))(u16(1) + capabilities(
            [("audio.codec", "opus,pcm"), ("video.depth", "8")])),
        (lambda c: framing(0x0001, c + b"\xDE\xAD\xBE\xEF"))(u16(1) + capabilities(
            [("audio.codec", "opus,pcm"), ("video.depth", "8")])),
        "four bytes at the tail of the body and the u32 `length` higher by "
        "four: `00000030` against `00000034`",
    ),
)

# ── L5 ──────────────────────────────────────────────────────────────────────
entry(
    "L5", "§4.3",
    "Is an **absent** capability an empty list or a thing not negotiated?",
    "A — absent = empty list: the intersection is empty, and §4.3 imposes "
    "`NOTHING_IN_COMMON`",
    "B — absent = not negotiated: the line that obliges concerns only `pcm` and "
    "`8`, and for the rest whoever keeps quiet asked for nothing",
    "the test client **always** declares all eight capabilities, so "
    "⚠ **it did not choose: it avoided the question**.  And having avoided it means "
    "that none of its runs will ever make it come out",
    "the first foreign client that kept quiet about `video.codec` — because it does not decode "
    "video, for example a clipboard-only client — would receive `NOTHING_IN_COMMON` "
    "or would get in, depending on who wrote the server, and neither of the two "
    "would be outside the specification",
    footholds_rcp=[
        "⛔ If the intersection of `video.codec` is **empty**, the server **MUST** "
        "send the farewell\n`NOTHING_IN_COMMON`.",
        "⚠ But if **after discarding\n  the list remains empty**, the farewell is "
        "`NOTHING_IN_COMMON`",
    ],
    # ⚠ The two anchors are the WHOLE list of `body_hello()`, first and last
    #   line: it is the «all eight, always» the entry claims.  The values of
    #   `video.codec` and `video.depth` come from the command line, so the
    #   anchor quotes the names, not the values (the default became `h264` on
    #   23 Aug 2026, and the old anchor quoted `hevc,av1`).
    footholds_client=[
        'voci = [("video.codec", video), ("video.depth", prof),',
        '("input.touch", "no"), ("client.name", "test-client 0.1.0")]',
    ],
    byte=lambda: (
        ciao(entries=[("video.codec", "h264"), ("video.depth", "8,10"),
                   ("audio.codec", "opus,pcm")]),
        ciao(entries=[("video.depth", "8,10"), ("audio.codec", "opus,pcm")]),
        "the `how_many` field of the capability list: `0003` against `0002`, and "
        "nineteen bytes fewer",
    ),
)

# ── L6 ──────────────────────────────────────────────────────────────────────
entry(
    "L6", "§4.6 lines 1 and 4  ·  the `[?]` R3.27 — ⭐ CLOSED on 11 Aug 2026",
    "From which instant does the first cap start: the end of TLS, the opening of the "
    "WebTransport session, or the opening of the control channel?",
    "A — the end of TLS, to the letter of §4.6 ⛔ **withdrawn from the document**",
    "B — the opening of the session, or of the channel: they are the instants the "
    "server can really observe, and between TLS and the session at least one "
    "network round trip passes",
    "⭐ **B, and now the document says it, not only the bench.**  §4.6 line 1 "
    "counts from the **opening of the control channel**, and line 4 — new — "
    "puts a 5 s cap also between session and channel.  ⚠ The test client "
    "still does not choose: it does not measure caps.  The one who had chosen was **B6**, "
    "and the bench's choice became the letter of the document",
    "a session open and a control channel **never opened**: to the letter "
    "of A the cap has already expired and the connection must be over; with "
    "reading B no cap sits on it and **it stays there**, which is precisely "
    "the thing §4.6 exists to prevent.  ⭐ And it is exactly the hole that "
    "line 4 was born to close: `DECISIONI.md` §7.17",
    footholds_rcp=[
        "| ⭐ **opening of the control channel** *(the first bidirectional stream "
        "of the session)* | `HELLO` received | **5 s** |",
        "| ⭐ **opening of the WebTransport session** | **opening of the control "
        "channel** | **5 s**",
    ],
    byte=None,
    note="⛔ **No byte changes**, and it must be said instead of inventing one: the "
         "two readings send the same `HELLO` (or the same silence).  What changes is "
         "**when** the `FAREWELL(TIMED_OUT)` arrives, and in the case of the "
         "session without a channel it changes **whether** it arrives.  It is the entry that keeps "
         "the «on the wire» column honest.\n"
         "  ⭐ **AND THIS ENTRY IS THE PROOF THAT B9 IS USEFUL, measured on 11 Aug "
         "2026.**  The anchor quoted here was the old line 1 of §4.6 — the one "
         "that started from the end of TLS — and B9 exited **3**: the anchor could "
         "no longer be found, because `RCP.md` had been corrected that very "
         "day, by us, on B6's measurement.  ⛔ No other bench would have "
         "noticed: the others would have become **greener**, not "
         "less.  ⚠ And the ambiguity has not «disappeared»: it has been **decided**, which "
         "is a different outcome and must be written as such.\n"
         "  ⛔ **AND THE FIRST DRAFT OF THIS NOTE QUOTED THE MARK IN FULL**, "
         "that is the sentence B12 looks for in the red output to attribute the "
         "red to the fault.  With that inside, the mark appeared **also in the "
         "healthy run** — and a mark that appears in both runs is not a "
         "mark, it is a way of certifying without looking (the same trap "
         "already written in the fault of C2).  ⭐ Caught by the certification run "
         "of 11 August, in which the bench bit whoever was certifying it.",
)

# ── L7 ──────────────────────────────────────────────────────────────────────
entry(
    "L7", "§2.2",
    "Must the extended CONNECT that opens the session carry an `origin`?",
    "A — yes: every browser sends it, and a server that checks it is compliant "
    "because RCP does not forbid it to check it",
    "B — no: §2.2 dictates the **path** and nothing else of the header, "
    "so the `origin` does not belong to RCP",
    "the test client **sends it**, copying the browser.  ⚠ It is a "
    "prudent choice that has a price: by sending it, the test client **can no longer "
    "find out** whether the server demands it — the arbiter adapted itself to the defendant",
    "the first client that is not a browser: if the server checks the `origin`, "
    "that client sees the CONNECT refused and the diagnosis that comes out of it is an "
    "HTTP status, that is outside RCP and outside all the reasons of §8.2",
    footholds_rcp=[
        "| **the session address** | `https://<host>:<porta>/rcp/1` |",
        "⛔ **The server MUST NOT accept a WebTransport session on a different "
        "path.**",
    ],
    footholds_client=['(b"origin", f"https://{autorita}".encode()),'],
    byte=lambda: (
        b":method CONNECT\n:protocol webtransport\n:path /rcp/1\n"
        b"origin https://192.168.0.2:7447\n",
        b":method CONNECT\n:protocol webtransport\n:path /rcp/1\n",
        "the `origin` field inside the header of the extended CONNECT — one "
        "more header line, compressed by QPACK",
    ),
    note="⚠ The two blocks above are the fields **before** QPACK: printing them "
         "compressed would give two strings that depend on the dynamic table, "
         "that is two numbers that cannot be compared.",
)

# ── L8 ──────────────────────────────────────────────────────────────────────
entry(
    "L8", "§4.5",
    "A `desktop` outside the six names: is it an out-of-range field (§3) or is it "
    "a diagnostic string not to be looked at?",
    "A — §3 applies: «a field out of range» is in the list of §3, "
    "so the client closes with `PROTOCOL_ERROR`",
    "B — it is not looked at: §4.5 says, in the same paragraph, that the client **MUST "
    "NOT** change behaviour based on its value",
    "the test client prints it and does not check it: reading B",
    "the day the server learned a seventh desktop — or wrote "
    "`plasma6` instead of `kde` — half of the implementations would close the "
    "session just opened.  ⚠ The two readings are in **six lines**, one "
    "under the other, and they are opposite",
    footholds_rcp=[
        "└── stringa desktop             one of: gnome · kde · xfce · lxqt · "
        "cinnamon · unknown",
        "The `desktop` field is for diagnosis: the client\n**MUST NOT** change "
        "behaviour based on its value",
    ],
    footholds_client=['desktop = corpo[11:11 + n].decode()'],
    byte=lambda: (
        framing(0x0007, bytes([1]) + u32(1920) + u32(1080) + string("gnome")),
        framing(0x0007, bytes([1]) + u32(1920) + u32(1080) + string("plasma6")),
        "the `desktop` string at the end of `SESSION`: `0005 «gnome»` against "
        "`0007 «plasma6»` — and the connection that survives or drops",
    ),
)

# ── L9 ──────────────────────────────────────────────────────────────────────
entry(
    "L9", "§11.1 against §6.0",
    "In the recording block, what is written in `stream` when "
    "the identifier is not known?",
    "A — the real identifier, always: §11.1 says «the identifier of the "
    "QUIC stream» and does not foresee a case in which it is missing",
    "B — zero, as «absent»",
    "⭐ the test client **now writes the REAL identifier** — the control channel "
    "one (`reg.stream = cli.open_control()`), and the input and clipboard "
    "ones block by block — that is reading A, **and so it no longer meets "
    "the question**: nothing is recorded before the control channel exists.  "
    "⚠ Reading B is still there, latent: `Recorder.__init__` starts from "
    "`self.stream = 0`, and a block recorded before that line would carry "
    "the zero.  ⛔ And the document has NOT decided: §11.1 still declares no "
    "«absent» for `stream`, while §6.0 forbids the implicit one, and **zero is "
    "a legal stream identifier** (it is the one of the CONNECT)",
    "whoever reads the recording to understand on which stream a "
    "message passed reads zero and believes the zero.  ⚠ And the validator cannot "
    "notice: a field that is always zero and an absent field look the "
    "same — form E8",
    footholds_rcp=[
        " ├── u64      stream         the identifier of the QUIC stream",
        "⛔ **Every integer has a single meaning of «absent»**, and it must be "
        "declared where needed: there are no\nimplicit sentinel values.",
    ],
    footholds_client=[
        'out += struct.pack("!BBBIQIH", verso, canale, fine, ist, stream,',
        "reg.stream = cli.open_control()",
        "self.stream = 0",
    ],
    byte=lambda: (
        struct.pack("!BBBIQIH", 1, 0x00, 0, 0, 4, 12, 0),
        struct.pack("!BBBIQIH", 1, 0x00, 0, 0, 0, 12, 0),
        "the eight bytes of `stream`, after `which_way` · `channel` · `fine` · "
        "`instant_ms` (offset 7 of every block): "
        "`00 00 00 00 00 00 00 04` against `00 00 00 00 00 00 00 00`",
    ),
    note="⚠ **The choice of the test client changed, the ambiguity did not.**  "
         "Until the recorder wrote a fixed `0` (block `!BBQIH`, magic `0x02`) "
         "this entry said «reading B, and against §6.0»; then the client was "
         "brought to the real stream (box in `Recorder.__init__`, finding "
         "R1.5), and the block grew to `!BBBIQIH` with magic `0x03` (§11.1, "
         "21 Aug 2026).  The anchors had stayed on the old line, and B9 "
         "reported them as `[?]` until 10 Oct 2026.  ⛔ Code and document now "
         "agree on what is written; they still do not say what to write when "
         "the identifier is NOT known.",
)

# ── L10 ─────────────────────────────────────────────────────────────────────
entry(
    "L10", "§8.1 against §4.4",
    "The client, when it closes, MUST send `FAREWELL`: and after a `REJECTED`?",
    "A — yes, and it is the only thing it has left to say: the rule of §4.4 "
    "forbids **retrying**, not taking leave",
    "B — no: after `REJECTED` the session is over for the server, and every byte "
    "that arrives afterwards is a byte too many",
    "the test client **never sends a `FAREWELL`, in any case**: it closes "
    "and that is it.  ⚠ It is not reading B — it is the third, «I do not apply §8.1 to "
    "myself», and it means that the second reader **never exercises** the obligation "
    "that §8.1 puts on whoever closes",
    "the case has already cost a red: the server counted as «bytes after the "
    "end» also the page's compliant farewell, and B11 put a red "
    "on the page while it was doing what §8.1 requires of it (§4.4, box "
    "of 10 Aug 2026)",
    footholds_rcp=[
        "⛔ **And after `REJECTED` the client has only one thing left it may say: "
        "`FAREWELL`.**",
        "⛔ Whoever closes **MUST** send `FAREWELL` with a reason **before** closing "
        "the **WebTransport",
    ],
    byte=lambda: (
        framing(0x000C, bytes([0x01]) + string("")),
        b"",
        "a framing of nine bytes against **nothing**: `000C 00000003 01 "
        "0000` against the silence",
    ),
)

# ── L11 ─────────────────────────────────────────────────────────────────────
entry(
    "L11", "§9 against §2.2",
    "⭐ Which version does a client that can speak TWO put in the `HELLO`, on a "
    "path `/rcp/1`?",
    "A — **2**: §9 says «`HELLO` carries the major version the client can "
    "speak», without conditions",
    "B — **1**: §2.2 says the two MUST coincide, and a `HELLO(2)` on "
    "`/rcp/1` is `INCOMPATIBLE_VERSION`",
    "the test client writes `1` by hand, because it can speak only one: "
    "⚠ **the question was never put to it**, and it will not put it to itself until RCP/2 "
    "exists",
    "the first client that speaks 1 and 2: following §9 it declares 2 on `/rcp/1` and gets "
    "sent away; following §2.2 it declares 1 and **will never be able to negotiate the "
    "highest version**, because the only place where it can ask for it is the "
    "path, which however is the one it is already using.  ⛔ The two lines do not "
    "quote each other, and it is the exact shape of finding R1.2",
    footholds_rcp=[
        "`HELLO` carries the major version the client can speak; `HERE_I_AM` the one "
        "chosen by the server.",
        "⛔ **And the two MUST coincide**: a `HELLO(version=2)` on `/rcp/1` is "
        "`INCOMPATIBLE_VERSION`",
    ],
    footholds_client=['out = struct.pack("!HH", 1, len(voci))'],
    byte=lambda: (
        ciao(version=2),
        ciao(version=1),
        "the two bytes of `version` at the head of the body of the `HELLO`: `0002` against "
        "`0001` — two bytes, and a connection that lives or dies",
    ),
)

# ── L12 ─────────────────────────────────────────────────────────────────────
entry(
    "L12", "§4.5 against §7.1",
    "Do the limits 320×240-7680×4320 and the parity also hold for `vista_*` "
    "inside `ATTACH`?",
    "A — yes: §4.5 dictates the limits two lines away from the drawing that contains "
    "`view_width` and `view_height`, and does not distinguish",
    "B — no: the view does not have the canvas constraints, «any size from 1×1 "
    "upwards is lawful, odd included»",
    "the test client sends **view = canvas** (`--width`/`--height` for "
    "all four fields): ⚠ once again the question avoided, not "
    "answered",
    "a window narrowed to 300 pixels — the concrete case finding R1.17 "
    "describes — passes or makes the session drop depending on who wrote the "
    "server.  ⭐ **The answer exists** and it is B, but it is in §7.1, that is in the "
    "section of the `VIEW` message: whoever implements `ATTACH` by reading §4.5 "
    "has no reason to go there",
    footholds_rcp=[
        "⛔ **The limits, and they are normative**: width and height of the "
        "**granted** canvas **MUST** be between",
        "⛔ **The view does not have the constraints of the canvas**",
    ],
    footholds_client=[
        'struct.pack("!IIII", a.larghezza, a.altezza,\n                                     a.larghezza, a.altezza)',
    ],
    byte=lambda: (
        framing(0x0006, u32(1920) + u32(1080) + u32(1920) + u32(1080)
                     + string("it")),
        framing(0x0006, u32(1920) + u32(1080) + u32(300) + u32(801)
                     + string("it")),
        "the eight bytes of `view_width` and `view_height`: "
        "`00000780 00000438` against `0000012C 00000321` — below the minimum and "
        "odd",
    ),
    note="⚠ This is an ambiguity of **placement**, not of content: the "
         "document decides, but it decides in another section.  It counts anyway, "
         "because whoever reads §4.5 does not know they have to look.",
)


# ===========================================================================
def load(fpath):
    """⛔ «I could not read» is not «it is not there» (`LEZIONI.md` §1.9)."""
    try:
        with open(fpath, encoding="utf-8") as f:
            return f.read(), None
    except OSError as e:
        return None, f"{type(e).__name__}: {e}"


def normalize(t):
    """Removes line breaks and double spaces: an anchor must not fall because of
    a line wrapped at 100 columns instead of 98."""
    return " ".join(t.split())


def check_byte(v):
    """⛔ Two readings that produce the same bytes are not two readings.

    Returns (outcome, text).  `outcome` is one of:
      "diversi"      the two readings show on the wire;
      "senza-byte"   the entry declares it changes no byte (L6);
      "UGUALI"       ⛔ defect OF THIS BENCH: the entry separates nothing.
    """
    if v["byte"] is None:
        return "senza-byte", "no byte changes — declared in the entry"
    a, b, desc = v["byte"]()
    if a == b:
        return "UGUALI", ("⛔ the two readings produce the same bytes: the entry "
                          "separates nothing")
    return "diversi", desc


def hex_text(b, amount=48):
    if not isinstance(b, (bytes, bytearray)):
        return str(b)
    t = b[:amount].hex(" ")
    return t + (f"  … (+{len(b) - amount} bytes)" if len(b) > amount else "")


# ===========================================================================
# ⛔⭐ THE BEHAVIOUR TEST — and it is born from finding A8, 11 Aug 2026
# ===========================================================================
# ⛔ WHAT WAS WRONG, AND IT MUST BE READ BEFORE TOUCHING THIS PART.
#
# Until tonight this bench verified its entries in one way only: the
# **anchors**, that is exact pieces of text that must appear in the two files.
# Review R12-A brought it to the opposite reading and left the quotation where
# it was:
#
#     the test client is changed to **reading A** — the extra tail is
#     CUT — but the string L4 quotes is left intact, line by line
#     (`body = bytes(self.incoming[6:6 + lung])`) and the truncation is added
#     in the following lines.
#
# ⛔ B9 stayed **green, 12 entries out of 12**, and kept printing *«⭐ SCELTO …
#    the test client reads `length` bytes and passes the body on as it is …
#    (reading B, tolerant)»* — which at that point was **false**.
#
# ⛔ So the fault B12 builds to certify B9 turned red because **it deleted a
#    quotation**, not because the second reader had aligned with the first: the
#    certification proved that B9 can see *a changed text* — which B9 openly
#    declares it can do — and **not** what B12's catalogue writes it certified.
#
# ⭐ THE CURE: for the entries in which the client's choice **shows on the wire**,
#    it is MEASURED instead of quoted.  The bytes of the two readings are built
#    here, given **to the real code of the test client**, and one looks at which
#    of the two comes out.  A quotation can be left standing while the behaviour
#    changes; a behaviour cannot.
#
# ⛔ AND WHY THIS DOES NOT CONTRADICT THE BOX AT THE TOP («the bricks of the wire
#    are rewritten here and not imported from the client»).  They are two
#    opposite uses: there the client would have been the **source** of the bytes,
#    and the entry would have compared the client with itself; here the client is
#    the **defendant**, and we bring it the bytes, built from the document.  A
#    bench that brings the defendant into court is not copying from the defendant.
#
# ⚠ And it is extracted without IMPORTING, because `01-b3-cliente.py` imports
#   `aioquic` and this bench «runs ANYWHERE: it does not touch the network and does
#   not want a server».  The needed functions are taken from the source and
#   compiled on their own.
def extract_functions(text, names):
    """The indicated functions, taken from the source and made callable.

    Returns `(space, error)`: one of the two is always `None`.
    ⛔ If a function is no longer there one does NOT pretend to have tested it: it
       is the same third thing as the anchors — «the text changed under the bench»."""
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return None, f"the test client does not compile: {e}"
    # ⛔ ALL the top-level functions of the client are taken, not only those
    #    asked for: a function that calls another and does not find it would
    #    raise `NameError`, and a `NameError` has the same face as «the reader
    #    refused the framing» — that is the test would say «reading A» having
    #    measured my extraction instead of the client.  It is the common face of
    #    empty and forbidden, moved inside the bench.
    grabbed, seen_items = [], []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            grabbed.append(node)
            seen_items.append(node.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in names \
                and node.name not in seen_items:
            grabbed.append(node)
            seen_items.append(node.name)
    lost = [n for n in names if n not in seen_items]
    if lost:
        return None, (f"I no longer find {lost} in the test client: the behaviour "
                      f"test cannot be done")
    module = ast.Module(body=grabbed, type_ignores=[])
    ast.fix_missing_locations(module)
    space = {"struct": struct}
    try:
        exec(compile(module, CLIENT, "exec"), space)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        return None, f"the extracted functions do not compile: {e}"
    return space, None


class _Queue:
    """The minimum `_browse` asks for: a `put_nowait`."""

    def __init__(self):
        self.inside = []

    def put_nowait(self, x):
        self.inside.append(x)


class _Fake:
    """The minimum `_browse` asks of `self`: the bytes that arrived, the queue and the recorder."""

    def __init__(self, data):
        self.incoming = bytearray(data)
        self.messages = _Queue()
        # ⛔ `_browse` records on arrival since 21 Aug 2026 (`if self.reg is
        #    not None`): without this attribute the L4 test fell into «the
        #    extraction is incomplete» and stopped measuring the client.
        #    `None` = no recorder, which is the path the reading takes.
        self.reg = None


def test_L4(sp):
    """The test client, in front of extra bytes at the tail of the body.

    ⛔ And the opposite case is written, as `LEZIONI.md` §1.11 wants:
       reading B (tolerant) ⇒ the delivered body is `lunghezza` long, tail
       included;  reading A ⇒ the delivered body is shorter, or no message
       arrives because the reader refused the framing."""
    inside = u16(1) + capabilities([("audio.codec", "opus,pcm"),
                                ("video.depth", "8")])
    with_queue = inside + b"\xDE\xAD\xBE\xEF"
    byte = framing(0x0001, with_queue)
    c = _Fake(byte)
    try:
        sp["_browse"](c)
    except (NameError, AttributeError) as e:
        # ⛔ These two are NOT «the reader refused»: they are «I did not bring
        #    the whole defendant into court».  Calling them reading A would mean
        #    giving a bench defect the face of a client defect — the seventh guise
        #    of `LEZIONI.md` §1.9.
        return "?", (f"the extraction is incomplete: `_browse` calls something "
                     f"I did not take ({type(e).__name__}: {e})")
    except Exception as e:  # noqa: BLE001
        return "A", (f"the reader raised {type(e).__name__} on the extra "
                     f"bytes: it is reading A (violation), not B")
    if len(c.messages.inside) != 1:
        return "?", (f"the reader delivered {len(c.messages.inside)} "
                     f"messages instead of 1: it is neither A nor B, it is a third "
                     f"behaviour that neither of the two readings describes")
    _type, body, _raw = c.messages.inside[0]
    if body == with_queue:
        return "B", (f"the delivered body is {len(body)} bytes long — "
                     f"whole `length`, tail included: **reading B**, "
                     f"tolerant, as written in the entry")
    return "A", (f"the delivered body is {len(body)} bytes long instead of "
                 f"{len(with_queue)}: the tail was CUT, that is **reading "
                 f"A** — and the entry says B")


def test_L2(sp):
    """The test client, in front of a closing code wider than 4 bytes.

    ⛔ The opposite case: if one day it read wide codes in full, the line «and
       on top it truncates» of the entry would be false and would have to be rewritten."""
    tight = sp["_capsula_chiusura"](closing_capsule(0x0D))
    largo_v = 0x52E4A40FA8DB + 0x0D
    largo = sp["_capsula_chiusura"](closing_capsule(largo_v, width=8))
    if tight[0] != 0x0D:
        return "?", (f"on a 4-byte code the reader returns {tight[0]!r} "
                     f"instead of 13: it is no longer the reading A the entry "
                     f"describes")
    if largo[0] == largo_v:
        return "?", (f"on an 8-byte code the reader returns the WHOLE "
                     f"value ({largo_v:#x}): it no longer truncates, and the entry must be "
                     f"rewritten")
    return "A", (f"4-byte code → {tight[0]:#04x} (right); 8-byte "
                 f"code {largo_v:#x} → {largo[0]:#04x} — ⛔ **a different "
                 f"reason**, which is the damage the entry describes")


# (code, which functions are needed, the test, what the entry declares)
PROVE = [
    ("L4", ("_browse",), test_L4, "B"),
    ("L2", ("_varint", "_capsula_chiusura"), test_L2, "A"),
]


def main(a):
    print("== ⭐ B9 — the points where `RCP.md` allowed TWO readings")
    print("   The most precious outcome of B9 is not «passes»: it is this list.")
    print("   (fasi/01-filo-nudo.md, B9 · PIANO.md §1.1)\n")

    if a.list:
        for v in ENTRIES:
            print(f"  {v['tag']:4s} {v['where']:22s} {v['domanda']}")
        print(f"\n  {len(ENTRIES)} entries.  Without --list the bytes are built.")
        return 0

    # ── B0.1: the initial state, which here is made of paper ───────────────
    print("== ⛔ The initial state (B0.1): the two texts this bench read")
    texts, missing_list = {}, []
    for name, fpath in (("RCP.md", RCP_MD), ("01-b3-cliente.py", CLIENT)):
        t, error = load(fpath)
        if t is None:
            print(f"    {RED}NO{GRAY}  {name:18s} {error}")
            missing_list.append(name)
        else:
            imp = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
            print(f"    {GREEN}OK{GRAY}  {name:18s} {len(t):7d} bytes · "
                  f"fingerprint {imp}")
            texts[name] = t
    if missing_list:
        print(f"\n    {RED}⛔ without the texts there is no inventory to "
              f"verify: it is not a red of the entries{GRAY}")
        return 4
    print(f"    --  the two paths: {RCP_MD}")
    print(f"                       {CLIENT}")
    print("    ⚠ the fingerprints serve the next run: if they change and the entries")
    print("      do not, someone corrected the document and nobody reread\n")

    # ── THE ENTRIES ────────────────────────────────────────────────────────
    counts = {"entries of the inventory": [0, 0],
             "entries with ALL the anchors in place": [0, 0],
             "entries that change BYTES on the wire": [0, 0],
             "⛔ entries TESTED on the client's behaviour": [0, 0],
             "⛔ entries that really separate the two readings": [0, 0]}
    counts["entries of the inventory"] = [len(ENTRIES), len(ENTRIES)]
    disconnected, broken, refuted, untried = [], [], [], []

    for v in ENTRIES:
        print(f"== {v['tag']}  ·  {v['where']}")
        print(f"   {v['domanda']}")
        print(f"     reading A   {v['a']}")
        print(f"     reading B   {v['b']}")
        print(f"     ⭐ CHOSEN   {v['scelta']}")
        print(f"     ⛔ BITES    {v['morde']}")

        # the anchors
        counts["entries with ALL the anchors in place"][1] += 1
        lost = []
        for text, which_ones in ((texts["RCP.md"], v["appigli_rcp"]),
                             (texts["01-b3-cliente.py"], v["appigli_cliente"])):
            n_text = normalize(text)
            for ap in which_ones:
                if normalize(ap) not in n_text:
                    lost.append(ap)
        if lost:
            disconnected.append((v["tag"], lost))
            print(f"     {YELLOW}[?]{GRAY} {len(lost)} anchors out of "
                  f"{len(v['appigli_rcp']) + len(v['appigli_cliente'])} can no "
                  f"longer be found: the text changed under the bench")
            for ap in lost:
                print(f"          «{normalize(ap)[:88]}»")
        else:
            counts["entries with ALL the anchors in place"][0] += 1
            n = len(v["appigli_rcp"]) + len(v["appigli_cliente"])
            print(f"     {GREEN}OK{GRAY}  {n} anchors out of {n} in place "
                  f"in the two texts")

        # the bytes
        outcome, desc = check_byte(v)
        counts["⛔ entries that really separate the two readings"][1] += 1
        if outcome == "diversi":
            counts["entries that change BYTES on the wire"][0] += 1
            counts["entries that change BYTES on the wire"][1] += 1
            counts["⛔ entries that really separate the two readings"][0] += 1
            print(f"     {GREEN}BYTE{GRAY}  {desc}")
            if a.byte:
                x, y, _ = v["byte"]()
                print(f"          A: {hex_text(x)}")
                print(f"          B: {hex_text(y)}")
        elif outcome == "senza-byte":
            counts["entries that change BYTES on the wire"][1] += 1
            counts["⛔ entries that really separate the two readings"][0] += 1
            print(f"     {YELLOW}BYTE{GRAY}  {desc}")
        else:
            broken.append(v["tag"])
            counts["entries that change BYTES on the wire"][1] += 1
            print(f"     {RED}BYTE{GRAY}  {desc}")
        if v["note"]:
            print(f"     {v['note']}")
        print()

    # ── ⛔ THE BEHAVIOUR TEST (A8) ──────────────────────────────────────────
    print("== ⛔ The BEHAVIOUR test: the test client put in front "
          "of the bytes")
    print("   ⭐ An anchor can be left standing while the behaviour "
          "changes: the")
    print("      review R12-A brought the client to the opposite reading "
          "leaving intact")
    print("      the string L4 quotes, and this bench stayed GREEN.  "
          "These lines")
    print("      measure which reading the client **executes**, not which "
          "quotation it carries.")
    for tag, functions, prova, declared in PROVE:
        counts["⛔ entries TESTED on the client's behaviour"][1] += 1
        space, error = extract_functions(texts["01-b3-cliente.py"], functions)
        if space is None:
            untried.append((tag, error))
            print(f"   {YELLOW}[?]{GRAY} {tag}: {error}")
            continue
        vista, why = prova(space)
        if vista == "?":
            # ⛔ «I could not measure it» is the third thing, and it has its colour.
            untried.append((tag, why))
            print(f"   {YELLOW}[?]{GRAY} {tag}: {why}")
        elif vista == declared:
            counts["⛔ entries TESTED on the client's behaviour"][0] += 1
            print(f"   {GREEN}OK{GRAY}  {tag}: the entry declares reading "
                  f"{declared} and the client EXECUTES {vista}")
            print(f"          {why}")
        else:
            refuted.append((tag, declared, vista, why))
            print(f"   {RED}NO{GRAY}  ⛔ {tag}: the entry declares "
                  f"reading {declared}, the client EXECUTES «{vista}»")
            print(f"          {why}")
    print(f"   --  functions taken from the client's source without importing it "
          f"(no aioquic): "
          f"{', '.join(sorted({f for _s, fs, _p, _d in PROVE for f in fs}))}")
    print()

    # ── THE DENOMINATOR ────────────────────────────────────────────────────
    print("    == what this run really looked at")
    # ⛔ Only the last line is a pass/fail.  The other three are
    #    DENOMINATORS, and a denominator that is not full is not a red:
    #    the line «change BYTES» will never be, because L6 declares it changes
    #    no byte.  Colouring it red would teach whoever reads that that red is
    #    normal — that is to no longer look at the reds.
    JUDGMENT = "⛔ entries that really separate the two readings"
    for desc, (good_n, tot) in counts.items():
        if tot == 0:
            print(f"    --  {desc:46s} no case triggered it")
            continue
        if desc in (JUDGMENT, "⛔ entries TESTED on the client's behaviour"):
            clr = GREEN if good_n == tot else RED
        else:
            clr = GREEN if good_n == tot else YELLOW
        print(f"    {clr}{good_n:3d} out of {tot:3d}{GRAY}  {desc}"
              + ("   (denominator, not a judgement)" if desc != JUDGMENT else ""))

    # ⛔ ZERO ENTRIES IS NOT «NO AMBIGUITY».
    if not ENTRIES:
        print(f"\n    {RED}⛔ ZERO entries: this is not «RCP is without "
              f"ambiguity», it is an empty inventory{GRAY}")
        return 2

    print()
    # ⛔ AND THE REFUTED ONES COME BEFORE EVERYTHING, because they are the only red
    #    that says «what this file tells about the client is not true today».
    if refuted:
        print(f"    {RED}⛔ B9: {len(refuted)} entries are REFUTED by the "
              f"behaviour of the test client{GRAY}")
        for tag, declared, vista, why in refuted:
            print(f"       {tag}: the entry says «reading {declared}», the "
                  f"client executes «{vista}» — {why}")
        print("       ⛔ It is not a defect of the document: it is that the entry "
              "describes a client")
        print("          that no longer exists.  It must be reread and rewritten BEFORE "
              "being believed,")
        print("          and the new choice must be brought into «what did NOT "
              "work».")
        return 1
    if untried:
        print(f"    {YELLOW}[?] B9: {len(untried)} entries could not be "
              f"tested on the behaviour{GRAY}")
        for tag, error in untried:
            print(f"       {tag}: {error}")
        print("       ⛔ «I could not test it» is not «passes»: without these "
              "lines the")
        print("          bench goes back to resting on the quotations alone, which is "
              "what")
        print("          finding A8 broke.")
        return 3
    if broken:
        print(f"    {RED}⛔ B9: {len(broken)} entries separate nothing "
              f"({', '.join(broken)}){GRAY}")
        print("       Two readings with the same bytes are not two readings:")
        print("       the defect is OF THIS BENCH, not of the document.")
        return 1
    if disconnected:
        print(f"    {YELLOW}[?] B9: the inventory is whole, but "
              f"{len(disconnected)} entries quote a text that is no longer there"
              f"{GRAY}")
        for tag, lost in disconnected:
            print(f"       {tag}: {len(lost)} anchors lost")
        print("       ⛔ It is not «the entry is wrong»: it is that RCP.md or the")
        print("          test client changed, and the entry must be reread")
        print("          before being believed.")
        return 3
    print(f"    {GREEN}⭐ B9: {len(ENTRIES)} points where the document did not "
          f"decide, all verified on today's text{GRAY}")
    print("       ⚠ And this does NOT mean they are the only ones: it means they are")
    print("         the ones found by reading RCP.md a second time.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B9 — the points where RCP.md allowed two readings")
    p.add_argument("--byte", action="store_true",
                   help="print the hex of the two readings")
    p.add_argument("--list", action="store_true",
                   help="only the titles, without building anything")
    sys.exit(main(p.parse_args()))
