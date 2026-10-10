#!/usr/bin/env python3
"""01-b9-letture.py — ⭐ B9: the points where `RCP.md` allowed TWO readings.

    python3 01-b9-letture.py                 the inventory, with the bytes compared
    python3 01-b9-letture.py --byte          and prints the hex in full
    python3 01-b9-letture.py --elenco        only the titles, without building anything

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
   ⛔ This file **verifies** it, entry by entry (`controlla_byte`), and an entry
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

  VOCI          how many times the document allowed two readings;
  CON APPIGLI   of those, how many could be **verified on the text** today;
  SUL FILO      of those, how many produce **different bytes** — that is how
                many a bench can go and look at;
  PROVATE       ⛔ of those, how many were measured **on the behaviour** of the
                test client instead of on its quotation.  It is the column born
                from finding A8 (11 Aug 2026): an anchor can be left standing
                while the behaviour changes, and for one night this bench was
                green on a client that had already changed reading.  The box is
                above `estrai_funzioni`.

⛔ The three never coincide, and printing only one of them would be the shape of
   `LEZIONI.md` §1.9: *«the verdict on zero things»* and *«the false
   denominator»*.  The entry **R3.27** is the one that proves it: it is a real
   ambiguity, and on the wire **no byte of the request changes** — what changes
   is *when* the `CONGEDO` arrives, and in the worst case *whether* it arrives.
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

  L11 the version in the `CIAO` when the path is `/rcp/1`: §9 orders declaring
      **the highest one can speak**, §2.2 says that a version different from the
      path is `VERSIONE_INCOMPATIBILE`.  For a client that spoke 1 **and** 2 the
      two lines order the opposite, and today it does not bite only because
      RCP/2 does not exist.
"""
import argparse
import ast
import hashlib
import os
import struct
import sys

QUI = os.path.dirname(os.path.abspath(__file__))


def cerca_in_su(nome, da):
    """Looks for `nome` walking up the folders.  ⛔ Returns None if it is not there.

    ⚠ It is not convenience: B12 runs a COPY of this bench inside
      `01-b12-copie/`, that is one folder further down — and a path computed
      with a single `dirname` would lead to an `RCP.md` that is not there.  The
      bench would exit «I could not read» **while B12 is measuring something
      else entirely**, and the certification would record a red with the wrong
      cause.
    """
    d = da
    for _ in range(6):
        p = os.path.join(d, nome)
        if os.path.exists(p):
            return p
        su = os.path.dirname(d)
        if su == d:
            break
        d = su
    return None


RADICE = os.path.dirname(QUI)
RCP_MD = cerca_in_su("RCP.md", QUI) or os.path.join(RADICE, "RCP.md")
CLIENTE = os.path.join(QUI, "01-b3-cliente.py")

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
# The bricks of the wire, rewritten HERE and not imported from the test client.
#
# ⛔ It is not duplication by distraction: if this file imported `inquadra()`
#    from the client, the two readings of §6.1 would **both** come out of the
#    client's reading, and entry L4 would compare the client with itself.
#    The bytes of the two readings are built by hand, from the document.
# ===========================================================================
def u16(v):
    return struct.pack("!H", v)


def u32(v):
    return struct.pack("!I", v)


def stringa(t):
    """§6.0: `u16 length` + `length` bytes of UTF-8, without terminator."""
    b = t.encode("utf-8") if isinstance(t, str) else t
    return u16(len(b)) + b


def inquadratura(tipo, corpo, lunghezza=None):
    """§6.1: `u16 type` · `u32 length` · body.

    `lunghezza` can be forced: it serves entry L4, where the point is precisely
    that the declared number and what the type expects do not coincide.
    """
    return u16(tipo) + u32(len(corpo) if lunghezza is None else lunghezza) + corpo


def capacita(voci):
    out = u16(len(voci))
    for n, v in voci:
        out += stringa(n) + stringa(v)
    return out


def ciao(versione=1, voci=None):
    voci = voci if voci is not None else [
        ("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
        ("audio.codec", "opus,pcm"), ("client.nome", "cliente-di-prova 0.1.0")]
    return inquadratura(0x0001, u16(versione) + capacita(voci))


def eccomi(voci):
    return inquadratura(0x0002, u16(1) + capacita(voci))


def capsula_chiusura(codice, larghezza=4, dentro_data=True):
    """The `CLOSE_WEBTRANSPORT_SESSION` capsule (0x2843), as the wire sees it.

    ⚠ The type and the length are QUIC variable-length integers: `0x2843` fits
      in two bytes with the two high bits at `01`, that is `0x68 0x43`.
    """
    corpo = codice.to_bytes(larghezza, "big")
    capsula = b"\x68\x43" + bytes([len(corpo)]) + corpo
    if not dentro_data:
        return capsula
    # RFC 9297: on the wire of the CONNECT the capsules travel inside DATA frames
    return b"\x00" + bytes([len(capsula)]) + capsula


# ===========================================================================
# THE INVENTORY.
#
# ⛔ Every entry declares its ANCHORS before declaring its thesis: a quotation
#    that can no longer be found is an entry that speaks of another document,
#    and it must be said instead of believed.
# ===========================================================================
VOCI = []


def voce(sigla, dove, domanda, lettura_a, lettura_b, scelta, morde,
         appigli_rcp=(), appigli_cliente=(), byte=None, nota=""):
    VOCI.append({
        "sigla": sigla, "dove": dove, "domanda": domanda,
        "a": lettura_a, "b": lettura_b, "scelta": scelta, "morde": morde,
        "appigli_rcp": list(appigli_rcp),
        "appigli_cliente": list(appigli_cliente),
        "byte": byte, "nota": nota,
    })


# ── L1 ──────────────────────────────────────────────────────────────────────
voce(
    "L1", "§4.3",
    "Does `ECCOMI` carry the server's LIST of codecs, or THE CHOICE?",
    "A — the list: §4.3 says «capabilities of the server», and the choice travels only "
    "in the server log and then in the `codec` field of the frame "
    "header (§6.2)",
    "B — the choice: §4.3 says «The one who chooses is the server», and the only place "
    "where the client could read it is this capability",
    "the test client **reads no capability of `ECCOMI`**: it reads the "
    "two bytes of the version and throws away the rest.  It is reading A by omission, "
    "that is the choice made without noticing it was making it",
    "in phase 2, on the first frame: a client that had read B "
    "would configure the decoder on the first element of the list and "
    "would guess right **as long as the server's order coincides with the intersection**. "
    "The symptom, far from here, is «the browser does not open the stream» — the same "
    "as finding O12 on `video.livello`",
    appigli_rcp=[
        "| **ECCOMI** | server → client. Chosen version, server capabilities |",
        "⛔ **The one who chooses is the server**, inside the intersection",
        "The choice **MUST** be written in the server log",
    ],
    appigli_cliente=['versione = struct.unpack("!H", corpo[:2])[0]'],
    byte=lambda: (
        eccomi([("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
                ("audio.codec", "opus,pcm")]),
        eccomi([("video.codec", "hevc"), ("video.profondita", "8"),
                ("audio.codec", "opus")]),
        "the value of `video.codec` inside `ECCOMI`: `0008 «hevc,av1»` against "
        "`0004 «hevc»` — and with it the u32 `lunghezza` of the framing",
    ),
)

# ── L2 ──────────────────────────────────────────────────────────────────────
voce(
    "L2", "§3.1 point 3",
    "How wide is the «application error code equal to the reason code», "
    "and does the bare reason go there or the mapped reason?",
    "A — the bare reason inside the 32 bits of the capsule: `00 00 00 0D`",
    "B — the reason transformed by the mapping that WebTransport over HTTP/3 "
    "imposes on error codes, which scatters the low values over the whole "
    "HTTP/3 space",
    "the test client reads **the last of the four bytes** and takes it for the "
    "reason (`_capsula_chiusura`, `return b[j + 3]`): it is reading A, **and on "
    "top it truncates** — a code above 255 would reach it as another reason, "
    "without a line saying so",
    "the day an implementation applied the mapping, the reason "
    "would arrive as a huge number and the reader would print its low "
    "byte: **a wrong reason instead of an error**, which is worse than a "
    "silence (§3.1: «The third point is the one that saves diagnoses»)",
    appigli_rcp=[
        "**MUST** close the **WebTransport session** with the application error "
        "code equal to the\n   **reason code** of §8.2",
    ],
    appigli_cliente=["return b[j + 3]      # the four bytes of the code, the lowest"],
    byte=lambda: (
        capsula_chiusura(0x0D),
        capsula_chiusura(0x52E4A40FA8DB + 0x0D, larghezza=8),
        "the bytes of the code inside the `0x2843` capsule: `00 00 00 0D` against "
        "eight bytes of a mapped value — and the capsule itself changes length",
    ),
    nota="⚠ `RCP.md` does not declare the width of the field anywhere: only "
         "the WebTransport format declares it, which RCP does not name.",
)

# ── L3 ──────────────────────────────────────────────────────────────────────
voce(
    "L3", "§3.1 point 2 against §4.2",
    "After the `CONGEDO`, does the control channel close with a FIN, or "
    "does only the session close?",
    "A — `CONGEDO` **with** the FIN on the control channel, then the closing "
    "of the session: §4.2 says that the FIN on that stream **is** the end "
    "of the session, so it is the most explicit way of saying it",
    "B — `CONGEDO` **without** FIN, and the end is declared only by the closing of the "
    "session (§3.1 point 3)",
    "the test client never sends a `CONGEDO`; and when it sends "
    "anything it uses `end_stream=False`, that is reading B.  ⛔ And on the side "
    "that receives it calls the FIN «the control channel has closed», which is "
    "a **different** outcome from «session closed by the server»",
    "whoever waits for the FIN to declare the session over stays hanging against "
    "whoever closes only the session; and whoever sends the FIN **before** the closing "
    "makes §4.2 trigger first, so the peer records «channel closed» instead "
    "of the reason.  It is the same family as finding R1.4, on the same point",
    appigli_rcp=[
        "⛔ **In bytes**: a FIN on that stream, from either of the two parties, "
        "closes the session.",
        "**MUST** send `CONGEDO` (§8) with the reason, on the control channel",
    ],
    appigli_cliente=[
        "self._quic.send_stream_data(self.controllo, dati, end_stream=False)",
        'self._cade("the control channel has closed")',
    ],
    byte=lambda: (
        inquadratura(0x000C, bytes([0x01]) + stringa("")) + b"<FIN>",
        inquadratura(0x000C, bytes([0x01]) + stringa("")),
        "the FIN bit of the STREAM frame carrying the `CONGEDO` — the same payload "
        "bytes, one transport bit more",
    ),
    nota="⚠ The `<FIN>` above is written in plain text because it is NOT a byte "
         "of the payload: it is a bit of the header of the QUIC STREAM frame, and "
         "pretending to be able to print it as payload would be a convenient lie.",
)

# ── L4 ──────────────────────────────────────────────────────────────────────
voce(
    "L4", "§6.1",
    "⭐ Extra bytes at the end of the body, with the `lunghezza` counting them: are they "
    "a violation or are they a reserve for future versions?",
    "A — violation: §6.1 wants `lunghezza` to be «the exact number of bytes "
    "of the body», and a body longer than what the type expects is «a "
    "length inconsistent with what the type provides for» ⇒ `ERRORE_PROTOCOLLO`",
    "B — reserve: `lunghezza` is authoritative, the fields the type "
    "declares are read and the rest is skipped.  It is the only way §9 could "
    "widen a message without changing the major version",
    "⛔ **Our two readers chose differently**: the test client "
    "reads `lunghezza` bytes and passes the body on as it is without ever checking "
    "that it consumed it all (reading B, tolerant); the B4 validator has "
    "a recording on purpose — `10-coda-di-spazzatura.rcpreg` — that is "
    "reading A",
    "it is the defect this bench exists to find: **the arbiter and the "
    "second reader do not read the same specification**.  As long as nobody sends "
    "extra bytes nothing happens; the day it happens, one of the two "
    "says compliant and the other closes the connection",
    appigli_rcp=[
        "⛔ `lunghezza` **MUST** be the exact number of bytes of the body.",
        "A receiver that reads a\nlength inconsistent with what the type provides "
        "for **MUST** close with `ERRORE_PROTOCOLLO`.",
    ],
    appigli_cliente=[
        'tipo, lung = struct.unpack("!HI", self.arrivati[:6])',
        "corpo = bytes(self.arrivati[6:6 + lung])",
    ],
    byte=lambda: (
        (lambda c: inquadratura(0x0001, c))(u16(1) + capacita(
            [("audio.codec", "opus,pcm"), ("video.profondita", "8")])),
        (lambda c: inquadratura(0x0001, c + b"\xDE\xAD\xBE\xEF"))(u16(1) + capacita(
            [("audio.codec", "opus,pcm"), ("video.profondita", "8")])),
        "four bytes at the tail of the body and the u32 `lunghezza` higher by "
        "four: `00000030` against `00000034`",
    ),
)

# ── L5 ──────────────────────────────────────────────────────────────────────
voce(
    "L5", "§4.3",
    "Is an **absent** capability an empty list or a thing not negotiated?",
    "A — absent = empty list: the intersection is empty, and §4.3 imposes "
    "`NIENTE_IN_COMUNE`",
    "B — absent = not negotiated: the line that obliges concerns only `pcm` and "
    "`8`, and for the rest whoever keeps quiet asked for nothing",
    "the test client **always** declares all eight capabilities, so "
    "⚠ **it did not choose: it avoided the question**.  And having avoided it means "
    "that none of its runs will ever make it come out",
    "the first foreign client that kept quiet about `video.codec` — because it does not decode "
    "video, for example a clipboard-only client — would receive `NIENTE_IN_COMUNE` "
    "or would get in, depending on who wrote the server, and neither of the two "
    "would be outside the specification",
    appigli_rcp=[
        "⛔ If the intersection of `video.codec` is **empty**, the server **MUST** "
        "send the farewell\n`NIENTE_IN_COMUNE`.",
        "⚠ But if **after discarding\n  the list remains empty**, the farewell is "
        "`NIENTE_IN_COMUNE`",
    ],
    # ⚠ The two anchors are the WHOLE list of `corpo_ciao()`, first and last
    #   line: it is the «all eight, always» the entry claims.  The values of
    #   `video.codec` and `video.profondita` come from the command line, so the
    #   anchor quotes the names, not the values (the default became `h264` on
    #   23 Aug 2026, and the old anchor quoted `hevc,av1`).
    appigli_cliente=[
        'voci = [("video.codec", video), ("video.profondita", prof),',
        '("input.tocco", "no"), ("client.nome", "cliente-di-prova 0.1.0")]',
    ],
    byte=lambda: (
        ciao(voci=[("video.codec", "h264"), ("video.profondita", "8,10"),
                   ("audio.codec", "opus,pcm")]),
        ciao(voci=[("video.profondita", "8,10"), ("audio.codec", "opus,pcm")]),
        "the `quante` field of the capability list: `0003` against `0002`, and "
        "nineteen bytes fewer",
    ),
)

# ── L6 ──────────────────────────────────────────────────────────────────────
voce(
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
    appigli_rcp=[
        "| ⭐ **opening of the control channel** *(the first bidirectional stream "
        "of the session)* | `CIAO` received | **5 s** |",
        "| ⭐ **opening of the WebTransport session** | **opening of the control "
        "channel** | **5 s**",
    ],
    byte=None,
    nota="⛔ **No byte changes**, and it must be said instead of inventing one: the "
         "two readings send the same `CIAO` (or the same silence).  What changes is "
         "**when** the `CONGEDO(TEMPO_SCADUTO)` arrives, and in the case of the "
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
voce(
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
    appigli_rcp=[
        "| **the session address** | `https://<host>:<porta>/rcp/1` |",
        "⛔ **The server MUST NOT accept a WebTransport session on a different "
        "path.**",
    ],
    appigli_cliente=['(b"origin", f"https://{autorita}".encode()),'],
    byte=lambda: (
        b":method CONNECT\n:protocol webtransport\n:path /rcp/1\n"
        b"origin https://192.168.0.2:7447\n",
        b":method CONNECT\n:protocol webtransport\n:path /rcp/1\n",
        "the `origin` field inside the header of the extended CONNECT — one "
        "more header line, compressed by QPACK",
    ),
    nota="⚠ The two blocks above are the fields **before** QPACK: printing them "
         "compressed would give two strings that depend on the dynamic table, "
         "that is two numbers that cannot be compared.",
)

# ── L8 ──────────────────────────────────────────────────────────────────────
voce(
    "L8", "§4.5",
    "A `desktop` outside the six names: is it an out-of-range field (§3) or is it "
    "a diagnostic string not to be looked at?",
    "A — §3 applies: «a field out of range» is in the list of §3, "
    "so the client closes with `ERRORE_PROTOCOLLO`",
    "B — it is not looked at: §4.5 says, in the same paragraph, that the client **MUST "
    "NOT** change behaviour based on its value",
    "the test client prints it and does not check it: reading B",
    "the day the server learned a seventh desktop — or wrote "
    "`plasma6` instead of `kde` — half of the implementations would close the "
    "session just opened.  ⚠ The two readings are in **six lines**, one "
    "under the other, and they are opposite",
    appigli_rcp=[
        "└── stringa desktop             one of: gnome · kde · xfce · lxqt · "
        "cinnamon · unknown",
        "The `desktop` field is for diagnosis: the client\n**MUST NOT** change "
        "behaviour based on its value",
    ],
    appigli_cliente=['desktop = corpo[11:11 + n].decode()'],
    byte=lambda: (
        inquadratura(0x0007, bytes([1]) + u32(1920) + u32(1080) + stringa("gnome")),
        inquadratura(0x0007, bytes([1]) + u32(1920) + u32(1080) + stringa("plasma6")),
        "the `desktop` string at the end of `SESSIONE`: `0005 «gnome»` against "
        "`0007 «plasma6»` — and the connection that survives or drops",
    ),
)

# ── L9 ──────────────────────────────────────────────────────────────────────
voce(
    "L9", "§11.1 against §6.0",
    "In the recording block, what is written in `stream` when "
    "the identifier is not known?",
    "A — the real identifier, always: §11.1 says «the identifier of the "
    "QUIC stream» and does not foresee a case in which it is missing",
    "B — zero, as «absent»",
    "⭐ the test client **now writes the REAL identifier** — the control channel "
    "one (`reg.stream = cli.apri_controllo()`), and the input and clipboard "
    "ones block by block — that is reading A, **and so it no longer meets "
    "the question**: nothing is recorded before the control channel exists.  "
    "⚠ Reading B is still there, latent: `Registratore.__init__` starts from "
    "`self.stream = 0`, and a block recorded before that line would carry "
    "the zero.  ⛔ And the document has NOT decided: §11.1 still declares no "
    "«absent» for `stream`, while §6.0 forbids the implicit one, and **zero is "
    "a legal stream identifier** (it is the one of the CONNECT)",
    "whoever reads the recording to understand on which stream a "
    "message passed reads zero and believes the zero.  ⚠ And the validator cannot "
    "notice: a field that is always zero and an absent field look the "
    "same — form E8",
    appigli_rcp=[
        " ├── u64      stream         the identifier of the QUIC stream",
        "⛔ **Every integer has a single meaning of «absent»**, and it must be "
        "declared where needed: there are no\nimplicit sentinel values.",
    ],
    appigli_cliente=[
        'out += struct.pack("!BBBIQIH", verso, canale, fine, ist, stream,',
        "reg.stream = cli.apri_controllo()",
        "self.stream = 0",
    ],
    byte=lambda: (
        struct.pack("!BBBIQIH", 1, 0x00, 0, 0, 4, 12, 0),
        struct.pack("!BBBIQIH", 1, 0x00, 0, 0, 0, 12, 0),
        "the eight bytes of `stream`, after `verso` · `canale` · `fine` · "
        "`istante_ms` (offset 7 of every block): "
        "`00 00 00 00 00 00 00 04` against `00 00 00 00 00 00 00 00`",
    ),
    nota="⚠ **The choice of the test client changed, the ambiguity did not.**  "
         "Until the recorder wrote a fixed `0` (block `!BBQIH`, magic `0x02`) "
         "this entry said «reading B, and against §6.0»; then the client was "
         "brought to the real stream (box in `Registratore.__init__`, finding "
         "R1.5), and the block grew to `!BBBIQIH` with magic `0x03` (§11.1, "
         "21 Aug 2026).  The anchors had stayed on the old line, and B9 "
         "reported them as `[?]` until 10 Oct 2026.  ⛔ Code and document now "
         "agree on what is written; they still do not say what to write when "
         "the identifier is NOT known.",
)

# ── L10 ─────────────────────────────────────────────────────────────────────
voce(
    "L10", "§8.1 against §4.4",
    "The client, when it closes, MUST send `CONGEDO`: and after a `RESPINTO`?",
    "A — yes, and it is the only thing it has left to say: the rule of §4.4 "
    "forbids **retrying**, not taking leave",
    "B — no: after `RESPINTO` the session is over for the server, and every byte "
    "that arrives afterwards is a byte too many",
    "the test client **never sends a `CONGEDO`, in any case**: it closes "
    "and that is it.  ⚠ It is not reading B — it is the third, «I do not apply §8.1 to "
    "myself», and it means that the second reader **never exercises** the obligation "
    "that §8.1 puts on whoever closes",
    "the case has already cost a red: the server counted as «bytes after the "
    "end» also the page's compliant farewell, and B11 put a red "
    "on the page while it was doing what §8.1 requires of it (§4.4, box "
    "of 10 Aug 2026)",
    appigli_rcp=[
        "⛔ **And after `RESPINTO` the client has only one thing left it may say: "
        "`CONGEDO`.**",
        "⛔ Whoever closes **MUST** send `CONGEDO` with a reason **before** closing "
        "the **WebTransport",
    ],
    byte=lambda: (
        inquadratura(0x000C, bytes([0x01]) + stringa("")),
        b"",
        "a framing of nine bytes against **nothing**: `000C 00000003 01 "
        "0000` against the silence",
    ),
)

# ── L11 ─────────────────────────────────────────────────────────────────────
voce(
    "L11", "§9 against §2.2",
    "⭐ Which version does a client that can speak TWO put in the `CIAO`, on a "
    "path `/rcp/1`?",
    "A — **2**: §9 says «`CIAO` carries the major version the client can "
    "speak», without conditions",
    "B — **1**: §2.2 says the two MUST coincide, and a `CIAO(2)` on "
    "`/rcp/1` is `VERSIONE_INCOMPATIBILE`",
    "the test client writes `1` by hand, because it can speak only one: "
    "⚠ **the question was never put to it**, and it will not put it to itself until RCP/2 "
    "exists",
    "the first client that speaks 1 and 2: following §9 it declares 2 on `/rcp/1` and gets "
    "sent away; following §2.2 it declares 1 and **will never be able to negotiate the "
    "highest version**, because the only place where it can ask for it is the "
    "path, which however is the one it is already using.  ⛔ The two lines do not "
    "quote each other, and it is the exact shape of finding R1.2",
    appigli_rcp=[
        "`CIAO` carries the major version the client can speak; `ECCOMI` the one "
        "chosen by the server.",
        "⛔ **And the two MUST coincide**: a `CIAO(versione=2)` on `/rcp/1` is "
        "`VERSIONE_INCOMPATIBILE`",
    ],
    appigli_cliente=['out = struct.pack("!HH", 1, len(voci))'],
    byte=lambda: (
        ciao(versione=2),
        ciao(versione=1),
        "the two bytes of `versione` at the head of the body of the `CIAO`: `0002` against "
        "`0001` — two bytes, and a connection that lives or dies",
    ),
)

# ── L12 ─────────────────────────────────────────────────────────────────────
voce(
    "L12", "§4.5 against §7.1",
    "Do the limits 320×240-7680×4320 and the parity also hold for `vista_*` "
    "inside `ATTACCA`?",
    "A — yes: §4.5 dictates the limits two lines away from the drawing that contains "
    "`vista_larghezza` and `vista_altezza`, and does not distinguish",
    "B — no: the view does not have the canvas constraints, «any size from 1×1 "
    "upwards is lawful, odd included»",
    "the test client sends **view = canvas** (`--larghezza`/`--altezza` for "
    "all four fields): ⚠ once again the question avoided, not "
    "answered",
    "a window narrowed to 300 pixels — the concrete case finding R1.17 "
    "describes — passes or makes the session drop depending on who wrote the "
    "server.  ⭐ **The answer exists** and it is B, but it is in §7.1, that is in the "
    "section of the `VISTA` message: whoever implements `ATTACCA` by reading §4.5 "
    "has no reason to go there",
    appigli_rcp=[
        "⛔ **The limits, and they are normative**: width and height of the "
        "**granted** canvas **MUST** be between",
        "⛔ **The view does not have the constraints of the canvas**",
    ],
    appigli_cliente=[
        'struct.pack("!IIII", a.larghezza, a.altezza,\n                                     a.larghezza, a.altezza)',
    ],
    byte=lambda: (
        inquadratura(0x0006, u32(1920) + u32(1080) + u32(1920) + u32(1080)
                     + stringa("it")),
        inquadratura(0x0006, u32(1920) + u32(1080) + u32(300) + u32(801)
                     + stringa("it")),
        "the eight bytes of `vista_larghezza` and `vista_altezza`: "
        "`00000780 00000438` against `0000012C 00000321` — below the minimum and "
        "odd",
    ),
    nota="⚠ This is an ambiguity of **placement**, not of content: the "
         "document decides, but it decides in another section.  It counts anyway, "
         "because whoever reads §4.5 does not know they have to look.",
)


# ===========================================================================
def leggi(percorso):
    """⛔ «I could not read» is not «it is not there» (`LEZIONI.md` §1.9)."""
    try:
        with open(percorso, encoding="utf-8") as f:
            return f.read(), None
    except OSError as e:
        return None, f"{type(e).__name__}: {e}"


def normalizza(t):
    """Removes line breaks and double spaces: an anchor must not fall because of
    a line wrapped at 100 columns instead of 98."""
    return " ".join(t.split())


def controlla_byte(v):
    """⛔ Two readings that produce the same bytes are not two readings.

    Returns (outcome, text).  `esito` is one of:
      "diversi"      the two readings show on the wire;
      "senza-byte"   the entry declares it changes no byte (L6);
      "UGUALI"       ⛔ defect OF THIS BENCH: the entry separates nothing.
    """
    if v["byte"] is None:
        return "senza-byte", "no byte changes — declared in the entry"
    a, b, che = v["byte"]()
    if a == b:
        return "UGUALI", ("⛔ the two readings produce the same bytes: the entry "
                          "separates nothing")
    return "diversi", che


def esadecimale(b, quanti=48):
    if not isinstance(b, (bytes, bytearray)):
        return str(b)
    t = b[:quanti].hex(" ")
    return t + (f"  … (+{len(b) - quanti} bytes)" if len(b) > quanti else "")


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
#     (`corpo = bytes(self.arrivati[6:6 + lung])`) and the truncation is added
#     in the following lines.
#
# ⛔ B9 stayed **green, 12 entries out of 12**, and kept printing *«⭐ SCELTO …
#    the test client reads `lunghezza` bytes and passes the body on as it is …
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
def estrai_funzioni(testo, nomi):
    """The indicated functions, taken from the source and made callable.

    Returns `(space, error)`: one of the two is always `None`.
    ⛔ If a function is no longer there one does NOT pretend to have tested it: it
       is the same third thing as the anchors — «the text changed under the bench»."""
    try:
        albero = ast.parse(testo)
    except SyntaxError as e:
        return None, f"the test client does not compile: {e}"
    # ⛔ ALL the top-level functions of the client are taken, not only those
    #    asked for: a function that calls another and does not find it would
    #    raise `NameError`, and a `NameError` has the same face as «the reader
    #    refused the framing» — that is the test would say «reading A» having
    #    measured my extraction instead of the client.  It is the common face of
    #    empty and forbidden, moved inside the bench.
    presi, visti = [], []
    for nodo in albero.body:
        if isinstance(nodo, ast.FunctionDef):
            presi.append(nodo)
            visti.append(nodo.name)
    for nodo in ast.walk(albero):
        if isinstance(nodo, ast.FunctionDef) and nodo.name in nomi \
                and nodo.name not in visti:
            presi.append(nodo)
            visti.append(nodo.name)
    persi = [n for n in nomi if n not in visti]
    if persi:
        return None, (f"I no longer find {persi} in the test client: the behaviour "
                      f"test cannot be done")
    modulo = ast.Module(body=presi, type_ignores=[])
    ast.fix_missing_locations(modulo)
    spazio = {"struct": struct}
    try:
        exec(compile(modulo, CLIENTE, "exec"), spazio)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        return None, f"the extracted functions do not compile: {e}"
    return spazio, None


class _Coda:
    """The minimum `_sfoglia` asks for: a `put_nowait`."""

    def __init__(self):
        self.dentro = []

    def put_nowait(self, x):
        self.dentro.append(x)


class _Finto:
    """The minimum `_sfoglia` asks of `self`: the bytes that arrived, the queue and the recorder."""

    def __init__(self, dati):
        self.arrivati = bytearray(dati)
        self.messaggi = _Coda()
        # ⛔ `_sfoglia` records on arrival since 21 Aug 2026 (`if self.reg is
        #    not None`): without this attribute the L4 test fell into «the
        #    extraction is incomplete» and stopped measuring the client.
        #    `None` = no recorder, which is the path the reading takes.
        self.reg = None


def prova_L4(sp):
    """The test client, in front of extra bytes at the tail of the body.

    ⛔ And the opposite case is written, as `LEZIONI.md` §1.11 wants:
       reading B (tolerant) ⇒ the delivered body is `lunghezza` long, tail
       included;  reading A ⇒ the delivered body is shorter, or no message
       arrives because the reader refused the framing."""
    dentro = u16(1) + capacita([("audio.codec", "opus,pcm"),
                                ("video.profondita", "8")])
    con_coda = dentro + b"\xDE\xAD\xBE\xEF"
    byte = inquadratura(0x0001, con_coda)
    c = _Finto(byte)
    try:
        sp["_sfoglia"](c)
    except (NameError, AttributeError) as e:
        # ⛔ These two are NOT «the reader refused»: they are «I did not bring
        #    the whole defendant into court».  Calling them reading A would mean
        #    giving a bench defect the face of a client defect — the seventh guise
        #    of `LEZIONI.md` §1.9.
        return "?", (f"the extraction is incomplete: `_sfoglia` calls something "
                     f"I did not take ({type(e).__name__}: {e})")
    except Exception as e:  # noqa: BLE001
        return "A", (f"the reader raised {type(e).__name__} on the extra "
                     f"bytes: it is reading A (violation), not B")
    if len(c.messaggi.dentro) != 1:
        return "?", (f"the reader delivered {len(c.messaggi.dentro)} "
                     f"messages instead of 1: it is neither A nor B, it is a third "
                     f"behaviour that neither of the two readings describes")
    _tipo, corpo, _grezzo = c.messaggi.dentro[0]
    if corpo == con_coda:
        return "B", (f"the delivered body is {len(corpo)} bytes long — "
                     f"whole `lunghezza`, tail included: **reading B**, "
                     f"tolerant, as written in the entry")
    return "A", (f"the delivered body is {len(corpo)} bytes long instead of "
                 f"{len(con_coda)}: the tail was CUT, that is **reading "
                 f"A** — and the entry says B")


def prova_L2(sp):
    """The test client, in front of a closing code wider than 4 bytes.

    ⛔ The opposite case: if one day it read wide codes in full, the line «and
       on top it truncates» of the entry would be false and would have to be rewritten."""
    stretto = sp["_capsula_chiusura"](capsula_chiusura(0x0D))
    largo_v = 0x52E4A40FA8DB + 0x0D
    largo = sp["_capsula_chiusura"](capsula_chiusura(largo_v, larghezza=8))
    if stretto[0] != 0x0D:
        return "?", (f"on a 4-byte code the reader returns {stretto[0]!r} "
                     f"instead of 13: it is no longer the reading A the entry "
                     f"describes")
    if largo[0] == largo_v:
        return "?", (f"on an 8-byte code the reader returns the WHOLE "
                     f"value ({largo_v:#x}): it no longer truncates, and the entry must be "
                     f"rewritten")
    return "A", (f"4-byte code → {stretto[0]:#04x} (right); 8-byte "
                 f"code {largo_v:#x} → {largo[0]:#04x} — ⛔ **a different "
                 f"reason**, which is the damage the entry describes")


# (code, which functions are needed, the test, what the entry declares)
PROVE = [
    ("L4", ("_sfoglia",), prova_L4, "B"),
    ("L2", ("_varint", "_capsula_chiusura"), prova_L2, "A"),
]


def principale(a):
    print("== ⭐ B9 — the points where `RCP.md` allowed TWO readings")
    print("   The most precious outcome of B9 is not «passes»: it is this list.")
    print("   (fasi/01-filo-nudo.md, B9 · PIANO.md §1.1)\n")

    if a.elenco:
        for v in VOCI:
            print(f"  {v['sigla']:4s} {v['dove']:22s} {v['domanda']}")
        print(f"\n  {len(VOCI)} entries.  Without --elenco the bytes are built.")
        return 0

    # ── B0.1: the initial state, which here is made of paper ───────────────
    print("== ⛔ The initial state (B0.1): the two texts this bench read")
    testi, mancanti = {}, []
    for nome, percorso in (("RCP.md", RCP_MD), ("01-b3-cliente.py", CLIENTE)):
        t, errore = leggi(percorso)
        if t is None:
            print(f"    {ROSSO}NO{GRIGIO}  {nome:18s} {errore}")
            mancanti.append(nome)
        else:
            imp = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
            print(f"    {VERDE}OK{GRIGIO}  {nome:18s} {len(t):7d} bytes · "
                  f"fingerprint {imp}")
            testi[nome] = t
    if mancanti:
        print(f"\n    {ROSSO}⛔ without the texts there is no inventory to "
              f"verify: it is not a red of the entries{GRIGIO}")
        return 4
    print(f"    --  the two paths: {RCP_MD}")
    print(f"                       {CLIENTE}")
    print("    ⚠ the fingerprints serve the next run: if they change and the entries")
    print("      do not, someone corrected the document and nobody reread\n")

    # ── THE ENTRIES ────────────────────────────────────────────────────────
    conti = {"entries of the inventory": [0, 0],
             "entries with ALL the anchors in place": [0, 0],
             "entries that change BYTES on the wire": [0, 0],
             "⛔ entries TESTED on the client's behaviour": [0, 0],
             "⛔ entries that really separate the two readings": [0, 0]}
    conti["entries of the inventory"] = [len(VOCI), len(VOCI)]
    scollegate, rotte, smentite, non_provate = [], [], [], []

    for v in VOCI:
        print(f"== {v['sigla']}  ·  {v['dove']}")
        print(f"   {v['domanda']}")
        print(f"     reading A   {v['a']}")
        print(f"     reading B   {v['b']}")
        print(f"     ⭐ CHOSEN   {v['scelta']}")
        print(f"     ⛔ BITES    {v['morde']}")

        # the anchors
        conti["entries with ALL the anchors in place"][1] += 1
        persi = []
        for testo, quali in ((testi["RCP.md"], v["appigli_rcp"]),
                             (testi["01-b3-cliente.py"], v["appigli_cliente"])):
            n_testo = normalizza(testo)
            for ap in quali:
                if normalizza(ap) not in n_testo:
                    persi.append(ap)
        if persi:
            scollegate.append((v["sigla"], persi))
            print(f"     {GIALLO}[?]{GRIGIO} {len(persi)} anchors out of "
                  f"{len(v['appigli_rcp']) + len(v['appigli_cliente'])} can no "
                  f"longer be found: the text changed under the bench")
            for ap in persi:
                print(f"          «{normalizza(ap)[:88]}»")
        else:
            conti["entries with ALL the anchors in place"][0] += 1
            n = len(v["appigli_rcp"]) + len(v["appigli_cliente"])
            print(f"     {VERDE}OK{GRIGIO}  {n} anchors out of {n} in place "
                  f"in the two texts")

        # the bytes
        esito, che = controlla_byte(v)
        conti["⛔ entries that really separate the two readings"][1] += 1
        if esito == "diversi":
            conti["entries that change BYTES on the wire"][0] += 1
            conti["entries that change BYTES on the wire"][1] += 1
            conti["⛔ entries that really separate the two readings"][0] += 1
            print(f"     {VERDE}BYTE{GRIGIO}  {che}")
            if a.byte:
                x, y, _ = v["byte"]()
                print(f"          A: {esadecimale(x)}")
                print(f"          B: {esadecimale(y)}")
        elif esito == "senza-byte":
            conti["entries that change BYTES on the wire"][1] += 1
            conti["⛔ entries that really separate the two readings"][0] += 1
            print(f"     {GIALLO}BYTE{GRIGIO}  {che}")
        else:
            rotte.append(v["sigla"])
            conti["entries that change BYTES on the wire"][1] += 1
            print(f"     {ROSSO}BYTE{GRIGIO}  {che}")
        if v["nota"]:
            print(f"     {v['nota']}")
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
    for sigla, funzioni, prova, dichiarata in PROVE:
        conti["⛔ entries TESTED on the client's behaviour"][1] += 1
        spazio, errore = estrai_funzioni(testi["01-b3-cliente.py"], funzioni)
        if spazio is None:
            non_provate.append((sigla, errore))
            print(f"   {GIALLO}[?]{GRIGIO} {sigla}: {errore}")
            continue
        vista, perche = prova(spazio)
        if vista == "?":
            # ⛔ «I could not measure it» is the third thing, and it has its colour.
            non_provate.append((sigla, perche))
            print(f"   {GIALLO}[?]{GRIGIO} {sigla}: {perche}")
        elif vista == dichiarata:
            conti["⛔ entries TESTED on the client's behaviour"][0] += 1
            print(f"   {VERDE}OK{GRIGIO}  {sigla}: the entry declares reading "
                  f"{dichiarata} and the client EXECUTES {vista}")
            print(f"          {perche}")
        else:
            smentite.append((sigla, dichiarata, vista, perche))
            print(f"   {ROSSO}NO{GRIGIO}  ⛔ {sigla}: the entry declares "
                  f"reading {dichiarata}, the client EXECUTES «{vista}»")
            print(f"          {perche}")
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
    GIUDIZIO = "⛔ entries that really separate the two readings"
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            print(f"    --  {che:46s} no case triggered it")
            continue
        if che in (GIUDIZIO, "⛔ entries TESTED on the client's behaviour"):
            col = VERDE if buoni == tot else ROSSO
        else:
            col = VERDE if buoni == tot else GIALLO
        print(f"    {col}{buoni:3d} out of {tot:3d}{GRIGIO}  {che}"
              + ("   (denominator, not a judgement)" if che != GIUDIZIO else ""))

    # ⛔ ZERO ENTRIES IS NOT «NO AMBIGUITY».
    if not VOCI:
        print(f"\n    {ROSSO}⛔ ZERO entries: this is not «RCP is without "
              f"ambiguity», it is an empty inventory{GRIGIO}")
        return 2

    print()
    # ⛔ AND THE REFUTED ONES COME BEFORE EVERYTHING, because they are the only red
    #    that says «what this file tells about the client is not true today».
    if smentite:
        print(f"    {ROSSO}⛔ B9: {len(smentite)} entries are REFUTED by the "
              f"behaviour of the test client{GRIGIO}")
        for sigla, dichiarata, vista, perche in smentite:
            print(f"       {sigla}: the entry says «reading {dichiarata}», the "
                  f"client executes «{vista}» — {perche}")
        print("       ⛔ It is not a defect of the document: it is that the entry "
              "describes a client")
        print("          that no longer exists.  It must be reread and rewritten BEFORE "
              "being believed,")
        print("          and the new choice must be brought into «what did NOT "
              "work».")
        return 1
    if non_provate:
        print(f"    {GIALLO}[?] B9: {len(non_provate)} entries could not be "
              f"tested on the behaviour{GRIGIO}")
        for sigla, errore in non_provate:
            print(f"       {sigla}: {errore}")
        print("       ⛔ «I could not test it» is not «passes»: without these "
              "lines the")
        print("          bench goes back to resting on the quotations alone, which is "
              "what")
        print("          finding A8 broke.")
        return 3
    if rotte:
        print(f"    {ROSSO}⛔ B9: {len(rotte)} entries separate nothing "
              f"({', '.join(rotte)}){GRIGIO}")
        print("       Two readings with the same bytes are not two readings:")
        print("       the defect is OF THIS BENCH, not of the document.")
        return 1
    if scollegate:
        print(f"    {GIALLO}[?] B9: the inventory is whole, but "
              f"{len(scollegate)} entries quote a text that is no longer there"
              f"{GRIGIO}")
        for sigla, persi in scollegate:
            print(f"       {sigla}: {len(persi)} anchors lost")
        print("       ⛔ It is not «the entry is wrong»: it is that RCP.md or the")
        print("          test client changed, and the entry must be reread")
        print("          before being believed.")
        return 3
    print(f"    {VERDE}⭐ B9: {len(VOCI)} points where the document did not "
          f"decide, all verified on today's text{GRIGIO}")
    print("       ⚠ And this does NOT mean they are the only ones: it means they are")
    print("         the ones found by reading RCP.md a second time.")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B9 — the points where RCP.md allowed two readings")
    p.add_argument("--byte", action="store_true",
                   help="print the hex of the two readings")
    p.add_argument("--elenco", action="store_true",
                   help="only the titles, without building anything")
    sys.exit(principale(p.parse_args()))
