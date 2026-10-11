#!/usr/bin/env python3
"""01-b4-recordings.py — the B4 recordings, and what the validator MUST say.

    python3 01-b4-recordings.py [folder]     default: ./b4-registrazioni

⛔ **How many there are is not written here**: `costruisci()` builds them, the
   program counts them and prints them together with the manifest.  A number
   written by hand in a comment is the number nobody recomputes.

---------------------------------------------------------------------------
⛔ ONE COMPLIANT, AND THE OTHERS ARE THE FOUR WAYS OF NOT BEING SO

`PHASES.md` §01-filo-nudo B4: without the **compliant** recording, «6 out of 6» is
compatible with a validator that **rejects everything** — it is enough to read
`lunghezza` as `u16` instead of `u32`, two characters, and from that moment the
arbiter declares every trace non-compliant with the diagnosis pointing at
`RCP.md` §6.1 while the defect is in the tool (finding R3.5).

⛔ **And it declares WHICH byte**, not only that it must be red.  Every fault
   below carries the exact offset of the offending byte, computed while it is
   built.  A validator that gave red on the wrong byte — typical of one that
   does not know §6.0 and misreads the NEXT message — would pass a bench that
   only looked at the colour.

---------------------------------------------------------------------------
⛔ AND THE OUTCOMES ARE FOUR, SO THE POSITIVE CONTROLS ARE FOUR

*Added on 10 Aug 2026, findings R7.12 and R7.13.*

The validator declares four outcomes — compliant, non-compliant, broken
recording, nothing to judge — and up to here the recordings exercised **two**
of them.  ⚠ The outcome that the validator declares to be *the reason the
outcomes are not two* had never been observed by the bench that certifies it:
one could break `Malformata` — turn it into a `NotCompliant` — and this bench
kept printing «it is certified», because no recording was broken.

The new ones, and each covers a declared hole:

| | |
|---|---|
| `7-tela-dispari` | ⛔ **no recording exercised §4.5**, and that is exactly where the validator accused the wrong byte — `le.base, 0`, two offsets that point at two different bytes.  The bench that exists to catch «right red, wrong byte» did not cover the family where the defect actually was (R7.12) |
| `8-carico-troncato` | the first positive control of **outcome 2** |
| `9-oscurati-sovrapposti` | the case that §11.1 names in full: *«MUST reject a recording in which an obscured interval … overlaps another»* |
| `10-coda-di-spazzatura` | bytes after the last declared block |
| `11-quanti-sotto-dichiarato` | ⛔ the most insidious: 4 is written where the blocks are 6, and the file stays **valid for every other line of §11.1** while two blocks vanish from the judgement |
| `12-niente-da-giudicare` | **outcome 3**: ⚠ *it said «video blocks only»*, and since **12 Aug 2026** it carries only **clipboard** blocks — because the validator now judges the video, and that file would exit **1** |

---------------------------------------------------------------------------
⭐⛔ AND SINCE 12 AUG 2026 THERE ARE ALSO THE **VIDEO** RECORDINGS

*The seven lines of F2.4 entered `RCP.md` (§2.5, §5.2, §6.2, §11.1), and six of
them are rules on the video channel that **no arbiter knew how to judge**.*

⛔ The recording format moved to **`RCPREG 0x00 0x02`** and the block carries
one more field — `fine`: *0 continues · 1 FIN · 2 RESET_STREAM* — without which
*«an abandoned frame and one truncated by mistake look the same in the
recording»* (§11.1, error form **E8**).

The new recordings, **two for each line**: the one that violates it and the one
that respects it, which here is `13-video-conforme` for five lines out of six.

| | |
|---|---|
| `13-video-conforme` | ⭐ the key frame that phase 2 exists to deliver: it **respects** P1, P2, P4, P5, P6 in one go.  Without it, a validator that rejected every frame would be green on all the violations |
| `14-video-prima-di-sessione` | **P1** §2.5 |
| `15-video-sul-controllo` | **P3** §2.5 |
| `16-video-numero-zero` | **P2** §6.2 |
| `17-video-misura-diversa` | **P5** §6.2 |
| `18-video-primo-delta` | **P6** §5.2 |
| `19-video-fin-corto` | **P4** §6.2 |
| `20-video-abbandonato` | ⭐ **P7** §11.1 — exit **0**: `fine = 2` says the server abandoned **on purpose**, the frame is thrown away and the session holds (§5.1).  ⛔ It is the recording that shows what the new field is for: without it, it was identical to `19` |

---------------------------------------------------------------------------
⭐⛔ AND SINCE 16 AUG 2026 THERE ARE THE **CANVAS** RECORDINGS — sub-phase 6.6

*`phases/06-the-canvas-and-the-view.md` §0 point 6: `FIT_CANVAS` (0x000B), `CANVAS`
(0x000E) and `VIEW` (0x0008) had been in the protocol for a week and **no
recording carried them**.  The seven rules that §7.1 writes in capital letters
were rules that no input triggered.*

| | |
|---|---|
| `22-tela-non-sollecitata` | **T1** §7.1 — it is also the ⏳ line that §7.1 declares missing: *«what the server does when the stage changes size by itself»* |
| `23-tela-doppia` | **T2** §6.2 — *«the n-th `CANVAS` answers the n-th `FIT_CANVAS`»* |
| `24` · `24bis` | **T3** §7.1 — the silence, by its two paths: the `FAREWELL` and the server's FIN |
| `24ter` | ⭐ the same scene that is **not** accused: the session is alive, and the trace merely ended earlier |
| `25` · `26` | outcome and reason outside the declared values |
| `27-tela-rifiutata-cambia` | **T5** §7.1 — every field is valid and the **relation** between the fields lies |
| `28` · `29` | **T6** §4.5 — the **granted** canvas odd, and out of bounds |
| `30-vista-cambia-tela` | **V3** §7.1 — *«`VIEW` MUST NOT change the canvas»* |
| `31-vista-legale` | ⭐ **V2** — 1x1, odd, 300x800, 9000x5000: finding **R1.17**, which must not come back in from the arbiter's side |
| `32-vista-zero` | **V1** §7.1 — *«from 1x1 up»* |
| `33-adatta-fuori-limiti-rifiutata` | ⭐ the impossible request is **lawful**: §7.1 devotes `SIZE_OUT_OF_RANGE` to it |
| `34` · `35` | ⭐ the full round, and two requests in flight together |
| `36` · `37` | the order of the handshake, and the two types of 15 August (`TERMINATE_SESSION`, `FAREWELL(0x10)`) |
| `38`-`45` | ⛔ **the eight not written by whoever wrote the arbiter** — see the box next to the code |

---------------------------------------------------------------------------
⚠ AND THE PASSWORD IS NOT THERE

The compliant recording contains a real `CREDENTIALS`, with the password
**obscured** according to `RCP.md` §11.1: true length, bytes replaced with
`0x2A`, fingerprint of what was there.  It is the case the format exists to
serve, and it must be exercised here — not on the first real trace.
"""
import hashlib
import json
import os
import struct
import sys

# ⛔ THE MAGIC IS `0x00 0x02` SINCE 12 AUG 2026 — `RCP.md` §11.1, proposal P7.
#
#    The block carries one more field, `fine`, and therefore **changes size**: 17
#    bytes instead of 16.  §11.1: *«the magic moves to 0x00 0x02 because the
#    block changes size: an old validator must REJECT the new format, not
#    misread it»*.
#    ⚠ And the expected offsets of all the recordings shift by one byte per
#      block: ⭐ **there is not a single number to fix by hand**, because
#      `Recording.deviation()` computes them from `BLOCK_BYTES`.  An
#      expected value written by hand would have required thirteen fixes, and it
#      would have been the time one gets forgotten.
MAGIC = b"RCPREG\x00\x03"
MAGIC_V1 = b"RCPREG\x00\x01"
MAGIC_V2 = b"RCPREG\x00\x02"
OLD_MAGIC = MAGIC_V1        # ⚠ the old name stays for whoever imports it
FILL = 0x2A
CLIENT, SERVER = 1, 2

# The block of §11.1: direction, channel, end, stream, length, obscured_count.
BLOCK = "!BBBIQIH"        # ⭐ +`instant_ms` since 21 Aug 2026: 21 bytes
BLOCK_BYTES = struct.calcsize(BLOCK)

# ⛔ `fine` — «how the stream was closed AFTER this block» (§11.1).
CONTINUE, FIN, RESET = 0, 1, 2

VIDEO = 0x03
CHIAVE, DELTA = 0x0301, 0x0302      # §6.2

# The four outcomes of `01-b4-validator.py`, with their name — written here
# once so that the manifest carries them in full and not by number.
ESITI = {0: "compliant", 1: "non-compliant", 2: "broken-recording",
         3: "nothing-to-judge"}


# ---------------------------------------------------------------------------
def s(text):
    """RCP.md §6.0: u16 length + UTF-8, without terminator."""
    b = text.encode("utf-8") if isinstance(text, str) else text
    return struct.pack("!H", len(b)) + b


def cap(pairs):
    out = struct.pack("!H", len(pairs))
    for n, v in pairs:
        out += s(n) + s(v)
    return out


def msg(kind, body, length=None):
    """The framing of §6.1: u16 type, u32 length, body."""
    n = len(body) if length is None else length
    return struct.pack("!HI", kind, n) + body


HELLO = msg(0x0001, struct.pack("!H", 1) + cap([
    ("video.codec", "hevc,av1"),
    ("video.depth", "8,10"),
    ("audio.codec", "opus,pcm"),
    ("video.level", "5.1"),
    ("video.max_size", "3840x2160"),
    ("clipboard.text", "yes"),
    ("input.touch", "no"),
    ("client.name", "test-client 0.1.0"),
]))
HERE_I_AM = msg(0x0002, struct.pack("!H", 1) + cap([
    ("video.codec", "hevc"),
    ("video.depth", "8,10"),
    ("audio.codec", "opus,pcm"),
    ("clipboard.text", "yes"),
    ("bench.mark", "no"),
]))
ADMITTED = msg(0x0004, b"")
ATTACH = msg(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080) + s("it"))
SESSION = msg(0x0007, struct.pack("!B", 1) + struct.pack("!II", 1920, 1080) + s("gnome"))

UTENTE, PASSWORD = "prova", "parola-di-prova"


def credentials():
    """The body of CREDENTIALS, and where the password falls inside the body.

    ⛔ It also returns the interval to obscure: the real recorder will do
       the same thing, and the fact that the computation is ONE ONLY is the
       reason §11.1 says «the format is one only, written once».
    """
    u, p = UTENTE.encode(), PASSWORD.encode()
    body = s(u) + s(p)
    word_start = 2 + len(u) + 2      # inside the message body
    return body, word_start, len(p), hashlib.sha256(p).digest()


# ---------------------------------------------------------------------------
class Recording:
    """Builds the file of §11.1 keeping track of the offsets."""

    def __init__(self):
        self.blocks = []
        # ⛔ The three ways of breaking the FILE instead of the wire, and they
        #    live here because a malformed recording is built **on purpose**:
        #    without them outcome 2 of the validator has no positive control
        #    (finding R7.13).
        self.declared = {}    # index -> DECLARED length, different from the true one
        self.declare_how_many = None   # `block_count` different from those written
        self.queue = b""         # bytes after the last block
        # ⛔ And the fourth: yesterday's MAGIC, `RCPREG 0x00 0x01`, with the
        #    16-byte block.  It serves one thing only, and it is the one §11.1
        #    asks for by name: *«an old validator must REJECT the new format»*.
        #    ⚠ A format that can only write its own version cannot certify that
        #      it knows how to reject the others.
        self.magic = MAGIC
        # ⛔ `clock` of §11.1: 1 = the times are the client's.  The BUILT
        #    recordings declare it client because it is the direction in which
        #    the arbiter can conclude — declaring it «server» would make the
        #    rule of the second unaccusable, and a bench that takes away its
        #    own chance to fail is not a bench.
        self.clock = 1
        self.fake_clock = None   # for the deliberately malformed recording

    def block(self, which_way, load, channel=0x00, stream=0, obscured=(),
               fine=CONTINUE, instant=0):
        """⛔ `fine` defaults to CONTINUA, and it is not laziness.

        The control channel lives on **a single stream for the whole session**
        (§2.5): inside a recording of the handshake that stream never closes,
        so `0` — «continues» — is the true value.
        ⚠ Putting `1` there to please a reader would say the session closed at
          every message.
        """
        self.blocks.append((which_way, channel, stream, load, list(obscured),
                             fine, instant))
        return self

    def deviation(self, block_index, inside):
        """The ABSOLUTE offset in the file of byte `inside` of the given block.

        ⛔ It rests on `BLOCK_BYTES`, never on a 16 written by hand: that is what
           made the move to `0x00 0x02` a single line instead of thirteen
           expected values to fix.
        """
        p = 16
        for i, b in enumerate(self.blocks):
            load, osc = b[3], b[4]
            p += BLOCK_BYTES + 40 * len(osc)
            if i == block_index:
                return p + inside
            p += len(load)
        raise IndexError(block_index)

    def byte(self):
        amount = (len(self.blocks) if self.declare_how_many is None
                  else self.declare_how_many)
        gold = (self.clock if self.fake_clock is None
               else self.fake_clock)
        out = bytearray(self.magic
                        + struct.pack("!IBBBB", amount, gold, 0, 0, 0))
        for i, (which_way, channel, stream, load, osc, fine, ist) in enumerate(
                self.blocks):
            lung = self.declared.get(i, len(load))
            if self.magic == MAGIC_V1:
                out += struct.pack("!BBQIH", which_way, channel, stream, lung,
                                   len(osc))
            elif self.magic == MAGIC_V2:
                out += struct.pack("!BBBQIH", which_way, channel, fine, stream,
                                   lung, len(osc))
            else:
                out += struct.pack(BLOCK, which_way, channel, fine, ist, stream,
                                   lung, len(osc))
            for ini, here, imp in osc:
                out += struct.pack("!II", ini, here) + imp
            out += load
        return bytes(out) + self.queue


def compliant():
    """The whole handshake, with the password obscured."""
    body, ini, here, imp = credentials()
    cred = msg(0x0003, body)
    r = Recording()
    r.block(CLIENT, HELLO)
    r.block(SERVER, HERE_I_AM)
    # the obscured interval is inside the block's PAYLOAD: 6 bytes of
    # framing, then the body
    r.block(CLIENT, cred[:6 + ini] + bytes([FILL]) * here + cred[6 + ini + here:],
             obscured=[(6 + ini, here, imp)])
    r.block(SERVER, ADMITTED)
    r.block(CLIENT, ATTACH)
    r.block(SERVER, SESSION)
    return r


# ---------------------------------------------------------------------------
def build():
    """Each with its expected value: `(nome, registrazione, exit_code, atteso, che)`.

    ⛔ `exit_code` is the code the validator MUST return — 0 compliant,
       1 non-compliant, 2 broken recording, 3 nothing to judge — and
       `atteso` carries rule and byte **only** when the exit code is 1.  Before,
       there were two outcomes out of four here, and the two missing ones were
       exactly those the validator declares it has so as not to confuse a bench
       defect with a protocol defect (finding R7.13).
    """
    cases = []

    # ── 7. the compliant one — built first because it is the base of the others
    cases.append(("compliant", compliant(), 0, None,
                 "the whole handshake, with the password obscured"))

    # ── 1. length inconsistent with the type (§6.1) ─────────────────────────
    #    `ATTACH` declares 4 bytes fewer than its fields want: the body ends
    #    while the view is being read.
    body_a = struct.pack("!IIII", 1920, 1080, 1920, 1080) + s("it")
    r = compliant()
    r.blocks[4] = (CLIENT, 0x00, 0, msg(0x0006, body_a[:-6],
                                        len(body_a) - 6), [], CONTINUE, 0)
    # ⛔ The offending byte is where the MISSING field would have begun — here
    #    `view_height`, after the first three u32 — not the end of the body.
    #    ⚠ The first expected value written on 10 August said «the end of the
    #      body», and the validator answered two bytes earlier.  It was right:
    #      the byte to show whoever diagnoses is the one from which reading
    #      cannot go on, not the one where the data ends.  It is the third time
    #      in a day that the EXPECTED is wrong and the tool is not.
    cases.append(("1-lunghezza-incoerente", r, 1,
                 ("RCP.md §6.1", r.deviation(4, 6 + 12)),
                 "ATTACH declares fewer bytes than its fields want"))

    # ── 2. invalid UTF-8 (§6.0) ──────────────────────────────────────────────
    #    A capability value with a broken sequence: 0xC3 without the second
    #    byte.  It is the case in which a careless receiver accepts and then
    #    shows a mangled name in a log.
    fault = b"remotix\xc3\x28prova"
    body_c = struct.pack("!H", 1) + cap([("video.codec", "hevc")])
    # the list is rebuilt by hand to know WHERE the broken byte falls
    entries = [(b"video.codec", b"hevc"), (b"client.name", fault)]
    body_c = struct.pack("!HH", 1, len(entries))
    # ⚠ The offset accumulates over ALL the entries that come before, not only
    #   over the faulty one: the first run of 10 August computed it from the
    #   start of the list and accused a byte 19 positions further back.
    #   ⛔ It is the error this bench exists to catch — only this time it was
    #      in the EXPECTED, not in the validator.
    offs = None
    for n, v in entries:
        if v is fault:
            offs = len(body_c) + 2 + len(n) + 2 + 7  # up to byte 0xC3
        body_c += s(n) + s(v)
    r = compliant()
    r.blocks[0] = (CLIENT, 0x00, 0, msg(0x0001, body_c), [], CONTINUE, 0)
    cases.append(("2-utf8-non-valido", r, 1,
                 ("RCP.md §6.0", r.deviation(0, 6 + offs)),
                 "client.name contains a broken UTF-8 sequence"))

    # ── 3. repeated capability name (§4.3) ──────────────────────────────────
    entries = [(b"video.codec", b"hevc"), (b"video.depth", b"8"),
            (b"video.codec", b"av1")]
    body_c = struct.pack("!HH", 1, len(entries))
    offs = None
    for k, (n, v) in enumerate(entries):
        if k == 2:
            offs = len(body_c)
        body_c += s(n) + s(v)
    r = compliant()
    r.blocks[0] = (CLIENT, 0x00, 0, msg(0x0001, body_c), [], CONTINUE, 0)
    cases.append(("3-capacita-ripetuta", r, 1,
                 ("RCP.md §4.3", r.deviation(0, 6 + offs)),
                 "video.codec appears twice"))

    # ── 4. high byte outside the five channels (§2.5) ───────────────────────
    #    A type 0x0701: the high byte is 7, and the channels are five.
    r = compliant()
    r.blocks[3] = (SERVER, 0x00, 0, msg(0x0701, b""), [], CONTINUE, 0)
    cases.append(("4-canale-sconosciuto", r, 1,
                 ("RCP.md §2.5", r.deviation(3, 0)),
                 "a type whose high byte is not one of the five channels"))

    # ── 5. message in the wrong state (§4) ──────────────────────────────────
    #    ATTACH before CREDENTIALS.
    r = Recording()
    r.block(CLIENT, HELLO)
    r.block(SERVER, HERE_I_AM)
    r.block(CLIENT, ATTACH)
    cases.append(("5-stato-sbagliato", r, 1,
                 ("RCP.md §4 (the handshake order)", r.deviation(2, 0)),
                 "ATTACH before CREDENTIALS"))

    # ── 6. ⭐ right body but ALIGNED (§6.0) ──────────────────────────────────
    #    `ADMITTED` has an empty body; here it declares four bytes of padding —
    #    exactly what a C struct aligned to 4 would do.
    #    ⛔ And there is another message after it: a validator that does not
    #       know §6.0 would misread THAT one, and give red on the wrong byte.
    r = compliant()
    r.blocks[3] = (SERVER, 0x00, 0, msg(0x0004, b"\x00\x00\x00\x00"), [],
                    CONTINUE, 0)
    cases.append(("6-riempimento", r, 1,
                 ("RCP.md §6.0", r.deviation(3, 6)),
                 "ADMITTED with four bytes of padding, and a message after it"))

    # ── 7. ⛔ ODD canvas (§4.5) — the family no recording exercised, and it
    #        is the one in which the validator accused the wrong byte:
    #        `le.base, 0`, that is the start of the BODY as absolute and ZERO
    #        as relative — two different bytes for the same fault, while §11.1
    #        asks for two ways of saying the SAME byte (finding R7.12).
    #        The expected is the first byte of `canvas_width`, which sits at
    #        the start of the body of ATTACH, that is six bytes after the
    #        start of the block.
    r = compliant()
    r.blocks[4] = (CLIENT, 0x00, 0,
                    msg(0x0006, struct.pack("!IIII", 1921, 1080, 1920, 1080)
                        + s("it")), [], CONTINUE, 0)
    cases.append(("7-tela-dispari", r, 1,
                 ("RCP.md §4.5", r.deviation(4, 6)),
                 "ATTACH with canvas_width = 1921, odd"))

    # ── 8. ⛔ the TRUNCATED payload — positive control of outcome 2.
    #        The block declares more bytes than it carries: it is the file
    #        that is broken, not the wire that is non-compliant, and the two
    #        things want two different sentences.  ⚠ If `Malformed` became a
    #        `NotCompliant`, this recording shouts it; before, none shouted it,
    #        and B4 kept printing «it is certified».
    r = compliant()
    r.declared[5] = len(r.blocks[5][3]) + 8
    cases.append(("8-carico-troncato", r, 2, None,
                 "the last block declares eight bytes that are not there"))

    # ── 9. ⛔ two obscured intervals that OVERLAP — §11.1 names it in full,
    #        and no recording exercised it.
    r = compliant()
    v, c, st, load, osc, fine, ist = r.blocks[2]
    ini_osc = osc[0][0]
    r.blocks[2] = (v, c, st, load,
                    [(ini_osc, 4, osc[0][2]), (ini_osc + 2, 4, osc[0][2])],
                    fine, ist)
    cases.append(("9-oscurati-sovrapposti", r, 2, None,
                 "two obscured intervals that overlap by two bytes"))

    # ── 10. ⛔ a TAIL after the last declared block.
    r = compliant()
    r.queue = b"\xff" * 16
    cases.append(("10-coda-di-spazzatura", r, 2, None,
                 "sixteen bytes after the last block: they are not part of the format"))

    # ── 11. ⛔ `block_count` UNDER-DECLARED, and it is the most insidious:
    #         the file stays valid for every other line of §11.1, and the two
    #         trailing blocks are never read.  Here the fifth block carries an
    #         ATTACH with the odd canvas — that is a real violation — which
    #         vanishes from the judgement by under-declaring.
    r = compliant()
    r.blocks[4] = (CLIENT, 0x00, 0,
                    msg(0x0006, struct.pack("!IIII", 1921, 1080, 1920, 1080)
                        + s("it")), [], CONTINUE, 0)
    r.declare_how_many = 4
    cases.append(("11-quanti-sotto-dichiarato", r, 2, None,
                 "block_count says 4 and the blocks are 6: the violation "
                 "is in the fifth"))

    # ── 12. ⛔ NOTHING TO JUDGE — outcome 3.  A well-formed file in which
    #         there is nothing this validator knows how to judge:
    #         «compliant» here would be true and empty (LESSONS.md §1.9).
    #
    #    ⚠ ⛔ THIS RECORDING CHANGED ON 12 AUG 2026, and it must be said
    #      because the change is the MEASURE of what the validator has
    #      learned.  Before, it carried **a video block**, and exited 3 for the
    #      reason its line 521 declared: *«video channel — not judged by this
    #      validator»*.  ⭐ Now it judges the video, and that file would exit
    #      **1**.  ⇒ To keep the positive control of outcome 3 alive a channel
    #      that neither arbiter judges is needed, and it is the **clipboard**
    #      (`0x02`, §7.4): there «I did not look» stays a true fact, and stays
    #      declared instead of acquitted.
    r = Recording()
    r.block(CLIENT, msg(0x0201, b"\x00" * 8), channel=0x02, stream=6)
    cases.append(("12-niente-da-giudicare", r, 3, None,
                 "a single CLIPBOARD block: zero control messages and zero "
                 "video streams"))

    # =======================================================================
    # ⭐⛔ 13-20 — THE VIDEO CHANNEL, AND THE SIX LINES THAT ENTERED `RCP.md`
    #             ON 12 AUG 2026 (§2.5, §5.2, §6.2)
    #
    # ⛔ Before today no B4 recording carried a judgeable frame, and it was
    #    not an oversight: the validator did not look at the video.  ⭐ Now it
    #    looks at it, and **an arbiter that knows a rule and lacks the input
    #    that triggers it does not enforce it**: these eight recordings are
    #    that input.
    #
    # ⛔ And each of the six lines has TWO recordings, not one: the one that
    #    violates it and the one that respects it.  Without the second, a
    #    validator that rejected **every** frame would be green on all the
    #    violations.  The recording that respects all six together is 13.
    # =======================================================================
    def con_video(*blocks_video, base=None):
        """The whole handshake, and then the video.  ⛔ In this order.

        `SESSION` is the sixth block of `compliant()`, so every frame added
        here comes **after**, which is what §2.5 demands (P1).
        """
        r = compliant() if base is None else base
        for b in blocks_video:
            # ⭐ the fifth element, optional, is the block's `instant_ms`:
            #    T4 needs it, and without it «how much time has passed» is not there.
            r.block(*b[:2], channel=VIDEO, stream=b[2], fine=b[3],
                     instant=(b[4] if len(b) > 4 else 0))
        return r

    def header(kind=CHIAVE, codec=1, lar=1920, h=1080, num=1, ist=0,
                     inp=0):
        """The 28 bytes of §6.2, in network order and without padding.

        ⚠ Retraced here and not imported: this file **builds** the bytes, and
          whoever judges them is another program.  If they built and judged
          with the same function, an error in the structure would cancel
          itself out — which is the silent defect of `RCP.md` §0 inside a bench.
        """
        return struct.pack("!HHIIIQI", kind, codec, lar, h, num, ist, inp)

    # ── 13. ⭐ the frame that phase 2 exists to deliver ─────────────────────
    r = con_video((SERVER, header() + b"\x00" * 512, 7, FIN))
    cases.append(("13-video-conforme", r, 0, None,
                 "⭐ a 1920x1080 key frame number 1 after SESSION, closed with "
                 "FIN: it respects all six lines of 12 August"))

    # ── 14. P1 — §2.5: no video stream before `SESSION` ───────────────────
    r = Recording()
    r.block(CLIENT, HELLO)
    r.block(SERVER, HERE_I_AM)
    r.block(SERVER, header() + b"\x00" * 64, channel=VIDEO, stream=7,
             fine=FIN)
    cases.append(("14-video-prima-di-sessione", r, 1,
                 ("RCP.md §2.5", r.deviation(2, 0)),
                 "⛔ P1 — a video stream opens before SESSION has "
                 "passed: the client knows neither the size nor the codec"))

    # ── 15. P3 — §2.5: a `0x03` on the control channel ──────────────────────
    #    ⛔ And it is written on STREAM 0, which is the control channel's: it
    #       is the only place where the server can go wrong, given that §2.5
    #       forbids it to open bidirectional streams.
    r = con_video((SERVER, header() + b"\x00" * 64, 0, CONTINUE))
    cases.append(("15-video-sul-controllo", r, 1,
                 ("RCP.md §2.5", r.deviation(6, 0)),
                 "⛔ P3 — the 28-byte header written on the stream of the "
                 "control channel"))

    # ── 16. P2 — §6.2: `nr` starts at 1, 0 is reserved ──────────────────
    r = con_video((SERVER, header(num=0) + b"\x00" * 64, 7, FIN))
    cases.append(("16-video-numero-zero", r, 1,
                 ("RCP.md §6.2", r.deviation(6, 12)),
                 "⛔ P2 — `numero = 0`, which §7.1 uses for «no frame»"))

    # ── 17. P5 — §6.2: the size MUST equal the granted canvas ───────────────
    #    ⛔ And the granted canvas is 1920x1080, and it sits in the `SESSION` of
    #       `compliant()`: it is not a number written in the validator.
    r = con_video((SERVER, header(lar=1280, h=720) + b"\x00" * 64, 7,
                   FIN))
    cases.append(("17-video-misura-diversa", r, 1,
                 ("RCP.md §6.2", r.deviation(6, 4)),
                 "⛔ P5 — a 1280x720 frame on a granted canvas of "
                 "1920x1080"))

    # ── 17-bis. ⭐⛔ P5 RESPECTED, AND IT IS THE RECORDING THAT CORRECTED
    #            `RCP.md` — §6.2 against §7.1.
    #
    #    The **very same bytes** as 17, but between `SESSION` and the frame a
    #    `CANVAS(FITTED, 1280, 720)` passes.  ⛔ With the first draft of P5 —
    #    *«the canvas granted in `SESSION`»* — this recording exited **1**:
    #    the client killed the session because the user had dragged a window,
    #    which is **exactly** the scene that §7.1 protects with its exception
    #    4.  ⭐ Corrected the same day into «the canvas **in force**», and this
    #    is the proof that holds it.
    #    ⚠ Without it the new rule would be as strict as the wrong one.
    #
    # ⛔⛔ AND ON 16 AUG 2026 THIS RECORDING CHANGED — sub-phase 6.6, and the
    #     change is **a measurement**, not maintenance.
    #
    #     As written on 12 August, it carried the `CANVAS(FITTED, 1280, 720)`
    #     **without any `FIT_CANVAS` before it**.  ⚠ That is, the recording
    #     that corrected `RCP.md` §6.2 staged a wire that §7.1 **forbids**: an
    #     unsolicited `CANVAS`, which §6.2 declares makes one *«close a healthy
    #     session»*.  Nobody had noticed because no arbiter counted the
    #     requests in flight — and it is error form E8 inside a bench: the
    #     right scene and the forbidden one looked the same.
    #
    # ⭐ Now the `FIT_CANVAS(1280, 720)` is there, and the recording says what
    #    it always meant to say: **the user dragged the window**.
    r = compliant()
    r.block(CLIENT, msg(0x000B, struct.pack("!II", 1280, 720)))
    r.block(SERVER, msg(0x000E, struct.pack("!BBII", 1, 0, 1280, 720)))
    r = con_video((SERVER, header(lar=1280, h=720) + b"\x00" * 64, 7,
                   FIN), base=r)
    cases.append(("17bis-video-dopo-adatta-tela", r, 0, None,
                 "⭐ P5 — 1280x720 after FIT_CANVAS + CANVAS(FITTED, 1280, "
                 "720): the canvas in force is no longer that of SESSION, and "
                 "the frame is compliant"))

    # ── 18. P6 — §5.2: the first frame after `SESSION` MUST be a key frame
    r = con_video((SERVER, header(kind=DELTA) + b"\x00" * 64, 7, FIN))
    cases.append(("18-video-primo-delta", r, 1,
                 ("RCP.md §5.2", r.deviation(6, 0)),
                 "⛔ P6 — the first frame of the session is a delta: "
                 "«the desktop appears in pieces», and nobody is wrong"))

    # ── 19. P4 — §6.2: FIN before the 28 bytes ──────────────────────────────
    r = con_video((SERVER, header()[:12], 7, FIN))
    cases.append(("19-video-fin-corto", r, 1,
                 ("RCP.md §6.2", r.deviation(6, 12)),
                 "⛔ P4 — the stream closes with FIN after 12 bytes: it is not a "
                 "short frame, it is a length that does not add up"))

    # ── 20. ⭐ P7 — §11.1: the `fine` field tells ABANDONMENT from error
    #    ⛔ It exits **0**, and that is the point: §5.1 allows the server to
    #       abandon a frame, the client throws it away and **the session
    #       holds**.  ⚠ Without the `fine` field this recording was identical
    #       to 19 — a payload that ends earlier than expected — and the arbiter
    #       had to choose between accusing a legal abandonment and acquitting a
    #       real truncation.
    r = con_video((SERVER, header(), 7, CONTINUE),
                  (SERVER, b"\x00" * 4096, 7, RESET))
    cases.append(("20-video-abbandonato", r, 0, None,
                 "⭐ P7 — a stream RESET halfway: the frame is thrown away "
                 "and the session holds (§5.1).  It is `fine = 2` that says so"))

    # ── 21. ⛔⛔ YESTERDAY'S FORMAT, which MUST be rejected — §11.1.
    #
    #    *«The magic moves to 0x00 0x02 because the block changes size: an old
    #    validator must REJECT the new format, not misread it»* — and it holds
    #    in both directions.  ⛔ Without this recording, the line that rejects
    #    `0x00 0x01` would be **a branch that nobody runs**: one could delete
    #    it and the bench would stay green, because all the other twenty are
    #    written with the new magic.
    #    ⚠ And the content is the **compliant** recording: so the only thing
    #      that gets it rejected is the version, not a defect of the wire.
    r = compliant()
    r.magic = OLD_MAGIC
    cases.append(("21-formato-vecchio", r, 2, None,
                 "⛔ a «RCPREG 0x00 0x01» recording, compliant in all the "
                 "rest: it is REJECTED, not misread"))

    # =======================================================================
    # ⭐⛔ 22-37 — THE CANVAS AND THE VIEW, sub-phase 6.6, 16 Aug 2026
    #
    # ⛔ `phases/06-the-canvas-and-the-view.md` §0 point 6: *«neither of the two sends
    #    an `FIT_CANVAS`»*.  ⇒ `FIT_CANVAS` (0x000B), `CANVAS` (0x000E) and
    #    `VIEW` (0x0008) had been in the protocol for a week and **no
    #    recording carried them**: the seven rules of §7.1 on the canvas were
    #    rules that no input triggered.
    #
    # ⛔ And here too **two per rule**: the one that violates it and the one that
    #    respects it.  The positive ones are not a courtesy — an arbiter strict
    #    on the canvas is exactly what would kill healthy sessions, and it is
    #    the defect §7.1 has already made once (finding R1.17, the view with
    #    the canvas limits).
    #
    # The offsets inside the body of `CANVAS`, counted from the start of the
    # message: 6 = outcome · 7 = reason · 8 = canvas_width · 12 = canvas_height.
    # Inside `VIEW` and `FIT_CANVAS`: 6 = width · 10 = height.
    # =======================================================================
    def canvas(outcome, reason, lar, h):
        return msg(0x000E, struct.pack("!BBII", outcome, reason, lar, h))

    def fit(lar, h):
        return msg(0x000B, struct.pack("!II", lar, h))

    def vista(lar, h):
        return msg(0x0008, struct.pack("!II", lar, h))

    # ── 22. ⛔ T1 §7.1 — an UNSOLICITED `CANVAS` ──────────────────────────────
    #    ⚠ It is the case that the ⏳ missing line of §7.1 describes in full:
    #      *«what the server does when the stage changes size without any
    #      `FIT_CANVAS` having asked for it»*.  §6.2 answers for it: the
    #      client has no way of accepting it, and **closes a healthy
    #      session**.  Until that line exists, this is the verdict.
    r = compliant()
    r.block(SERVER, canvas(1, 0, 1280, 720))
    cases.append(("22-tela-non-sollecitata", r, 1,
                 ("RCP.md §7.1", r.deviation(6, 0)),
                 "⛔ T1 — CANVAS(FITTED) without any FIT_CANVAS: the server "
                 "changes the canvas by itself"))

    # ── 23. ⛔ T2 §6.2 — TWO `CANVAS` for a single `FIT_CANVAS` ──────────────
    #    ⛔ The accused byte is that of the **second**: the first is right, and
    #       accusing it would send one looking for the defect in a correct
    #       answer.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, canvas(1, 0, 1280, 720))
    r.block(SERVER, canvas(1, 0, 1280, 720))
    cases.append(("23-tela-doppia", r, 1,
                 ("RCP.md §6.2", r.deviation(8, 0)),
                 "⛔ T2 — two CANVAS for a single FIT_CANVAS: from here on "
                 "the n-th CANVAS answers the (n+1)-th request"))

    # ── 24. ⛔ T3 §7.1 — `FIT_CANVAS` WITHOUT ANSWER, and then the FAREWELL ──
    #    ⛔ The accused byte is that of the REQUEST, not of the farewell: it is
    #       the request that was left hanging, and that is where whoever
    #       diagnoses must look.  ⚠ *«The symptom is "the application froze"»*.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, msg(0x000C, struct.pack("!B", 0x01) + s("")))
    cases.append(("24-adatta-senza-risposta", r, 1,
                 ("RCP.md §7.1", r.deviation(6, 0)),
                 "⛔ T3 — FIT_CANVAS, then a FAREWELL and no CANVAS: the server "
                 "had CANVAS(REFUSED, NOT_NOW) even while closing"))

    # ── 24-bis. ⛔ T3 by the other path: the control channel CLOSES ─────────
    #    No farewell, but a FIN from the server side: the answer can no longer
    #    arrive, and the fact is in the bytes — it is the `fine` field of §11.1.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, b"", fine=FIN)
    cases.append(("24bis-adatta-senza-risposta-fin", r, 1,
                 ("RCP.md §7.1", r.deviation(6, 0)),
                 "⛔ T3 — FIT_CANVAS and then the server closes the control "
                 "stream with FIN without answering"))

    # ── 24-ter. ⭐ THE SAME SCENE THAT IS **NOT** ACCUSED ───────────────────
    #    ⛔ Identical to 24 except the end: the stream continues, no farewell.
    #       The CANVAS can still arrive, and the recording merely **ended
    #       earlier**.  ⚠ Every trace of `01-b3-client.py` is of this kind —
    #       the client detaches by itself — and an arbiter that accused here
    #       would give a **perpetual false red** on every B3 run.
    #    ⭐ It is the recording that keeps T3 honest, as 17bis keeps P5
    #       honest: without it, «accusations the silence» and «accusations the end of the
    #       file» have the same colour.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    cases.append(("24ter-adatta-in-volo-traccia-viva", r, 0, None,
                 "⭐ T3 — an FIT_CANVAS in flight with the session still alive: "
                 "it is not accused, it is DECLARED as not judged"))

    # ── 25. ⛔ §7.1 — the outcome outside the two declared values ───────────
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, canvas(3, 0, 1280, 720))
    cases.append(("25-tela-esito-fuori", r, 1,
                 ("RCP.md §7.1", r.deviation(7, 6)),
                 "⛔ CANVAS with outcome 3: §7.1 defines two, 1 = FITTED and "
                 "2 = REFUSED"))

    # ── 26. ⛔ §7.1 — the reason outside the three declared ─────────────────
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, canvas(2, 4, 1920, 1080))
    cases.append(("26-tela-motivo-fuori", r, 1,
                 ("RCP.md §7.1", r.deviation(7, 7)),
                 "⛔ CANVAS(REFUSED) with reason 4: §7.1 defines three — "
                 "COMPOSITOR_UNABLE, SIZE_OUT_OF_RANGE, NOT_NOW"))

    # ── 27. ⛔ T5 §7.1 — the REFUSAL that CHANGES the canvas ────────────────
    #    ⛔ The most insidious of the seven: the message is well formed, outcome
    #       and reason are lawful, and **every field taken alone is valid**.
    #       It is the relation between the fields that lies — the server says
    #       «I did not adapt» and declares in force a canvas that was not in
    #       force.  ⚠ And §6.2 ties the size of every following frame to it:
    #       from here on the client throws away the good frames.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, canvas(2, 3, 1280, 720))
    cases.append(("27-tela-rifiutata-cambia", r, 1,
                 ("RCP.md §7.1", r.deviation(7, 8)),
                 "⛔ T5 — CANVAS(REFUSED, NOT_NOW) declaring 1280x720 in force "
                 "while the canvas was 1920x1080"))

    # ── 28. ⛔ T6 §4.5 — the GRANTED canvas with an ODD side ────────────────
    #    ⚠ And the REQUEST is even and within the limits — 1280x720 — on
    #      purpose: if the request were odd too, the accused byte would be
    #      right for two reasons at once, and one would not know which of the
    #      two holds.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, canvas(1, 0, 1281, 720))
    cases.append(("28-tela-concessa-dispari", r, 1,
                 ("RCP.md §4.5", r.deviation(7, 8)),
                 "⛔ T6 — CANVAS(FITTED) grants 1281x720: the odd side gets "
                 "rounded by the encoder, silently"))

    # ── 29. ⛔ T6 §4.5 — the GRANTED canvas out of bounds ───────────────────
    #    ⛔ And the HEIGHT, not the width: if the arbiter always accused the
    #       first field the byte would be right by chance.
    r = compliant()
    r.block(CLIENT, fit(1920, 240))     # ⚠ the request is within the limits
    r.block(SERVER, canvas(1, 0, 1920, 200))
    cases.append(("29-tela-concessa-fuori-limiti", r, 1,
                 ("RCP.md §4.5", r.deviation(7, 12)),
                 "⛔ T6 — CANVAS(FITTED) grants a height of 200, below the "
                 "minimum of 240"))

    # ── 30. ⛔ V3 §7.1 — the `VIEW` that CHANGES THE CANVAS ────────────────
    #    *«VIEW MUST NOT change the canvas … the only message that changes
    #    the canvas is FIT_CANVAS»*.  On the wire it looks like this: the
    #    client resizes the window, sends `VIEW`, and the server **adapts the
    #    desktop** — which is precisely the behaviour that `?fit=segui`
    #    must be able to keep OFF.
    r = compliant()
    r.block(CLIENT, vista(1280, 720))
    r.block(SERVER, canvas(1, 0, 1280, 720))
    cases.append(("30-vista-cambia-tela", r, 1,
                 ("RCP.md §7.1", r.deviation(7, 0)),
                 "⛔ V3 — the server answers a VIEW with a CANVAS: the view "
                 "must not change the canvas"))

    # ── 31. ⭐ V2 §7.1 — the 1x1 view IS LEGAL, and is not accused ──────────
    #    ⛔ *«Any size from 1x1 up is legal, odd included»*, and the canvas
    #       limits **do not apply** to the view: it is finding R1.17, and this
    #       recording exists so that it does not come back in from the
    #       arbiter's side.  ⚠ With the old line the client had three choices,
    #       all bad — and one was «get the session closed because it resized
    #       a window».
    r = compliant()
    r.block(CLIENT, vista(1, 1))
    r.block(CLIENT, vista(393, 851))       # a phone, odd sides
    r.block(CLIENT, vista(300, 800))       # below the canvas minimum
    r.block(CLIENT, vista(9000, 5000))     # above the canvas maximum
    cases.append(("31-vista-legale", r, 0, None,
                 "⭐ V2 — 1x1, 393x851 odd, 300x800 below the canvas "
                 "minimum and 9000x5000 above the maximum: all legal (§7.1, "
                 "R1.17)"))

    # ── 32. ⛔ V1 §7.1 — the view with a ZERO side ──────────────────────────
    #    «From 1x1 up»: zero is not «up», and §6.0 forbids implicit sentinel
    #    values — so it is not even «absent».
    r = compliant()
    r.block(CLIENT, vista(1280, 0))
    cases.append(("32-vista-zero", r, 1,
                 ("RCP.md §7.1", r.deviation(6, 10)),
                 "⛔ V1 — VIEW with height 0: §7.1 says «from 1x1 up»"))

    # ── 33. ⭐ §7.1 — the OUT-OF-BOUNDS `FIT_CANVAS` is LAWFUL ─────────────
    #    ⛔ It is the most important non-strictness control of the series: §7.1
    #       devotes a refusal reason by name to the impossible size —
    #       `SIZE_OUT_OF_RANGE` — and a reason exists to be reached.  An
    #       arbiter that rejected the request would make **unreachable** a
    #       branch the specification names, and no bench could exercise it
    #       any more.
    #    ⚠ And the refusal leaves the canvas where it was: 1920x1080, unchanged.
    r = compliant()
    r.block(CLIENT, fit(8000, 4320))
    r.block(SERVER, canvas(2, 2, 1920, 1080))
    cases.append(("33-adatta-fuori-limiti-rifiutata", r, 0, None,
                 "⭐ FIT_CANVAS(8000x4320) — outside the limits of §4.5 — and "
                 "CANVAS(REFUSED, SIZE_OUT_OF_RANGE) with the canvas unchanged: "
                 "it is the path §7.1 provides"))

    # ── 34. ⭐ THE FULL ROUND OF THE CANVAS, which must come out COMPLIANT ──
    #    ⛔ Without this, «sixteen out of sixteen» is compatible with an arbiter
    #       that rejects **every** FIT_CANVAS — and it would be green on all
    #       the violations.  In here: the request at attach, the answer, the
    #       frame at the NEW size (§6.2), a view that changes by itself, a
    #       second adaptation during the session, and an honest refusal.
    r = compliant()
    r.block(CLIENT, fit(1264, 800))
    r.block(SERVER, canvas(1, 0, 1264, 800))
    r.block(CLIENT, vista(1264, 800))
    r = con_video((SERVER, header(lar=1264, h=800) + b"\x00" * 256, 7,
                   FIN), base=r)
    r.block(CLIENT, fit(1920, 1080))
    r.block(SERVER, canvas(2, 1, 1264, 800))   # COMPOSITOR_UNABLE
    r.block(CLIENT, vista(640, 401))
    cases.append(("34-tela-giro-pieno", r, 0, None,
                 "⭐ the full round: FIT_CANVAS → CANVAS(FITTED, 1264x800) → a "
                 "frame at the new size → a second request "
                 "refused with COMPOSITOR_UNABLE, canvas unchanged"))

    # ── 35. ⭐ §6.2 — TWO REQUESTS IN FLIGHT TOGETHER, and the count holds ──
    #    *«Whoever drags a window sends two of them without the count getting
    #    lost»*.  ⛔ The two answers arrive in order, and the second declares
    #    the final canvas: an arbiter that paired by SIZE instead of by ORDER
    #    would fail here, because the first answer grants a size the client
    #    never asked for (§4.5 allows it).
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(CLIENT, fit(1600, 900))
    r.block(SERVER, canvas(1, 0, 1264, 800))   # ⚠ granted DIFFERENT from requested
    r.block(SERVER, canvas(1, 0, 1600, 900))
    cases.append(("35-due-richieste-in-volo", r, 0, None,
                 "⭐ two FIT_CANVAS in flight together and two CANVAS in order, with "
                 "the first granting a size never asked for (§4.5)"))

    # ── 36. ⛔ §4 — `FIT_CANVAS` BEFORE `SESSION` ─────────────────────────
    #    It is not a canvas rule: it is the handshake.  It sits here because
    #    an arbiter that learned the canvas by putting `FIT_CANVAS` outside the
    #    state machine would open this hole without noticing.
    r = Recording()
    r.block(CLIENT, HELLO)
    r.block(SERVER, HERE_I_AM)
    r.block(CLIENT, fit(1280, 720))
    cases.append(("36-adatta-prima-di-sessione", r, 1,
                 ("RCP.md §4 (the handshake order)",
                  r.deviation(2, 0)),
                 "⛔ FIT_CANVAS before the session exists"))

    # ── 37. ⭐ §7.6 and §8.2 — `TERMINATE_SESSION` and the `FAREWELL(0x10)` ───
    #    ⛔ Two types that entered on **15 Aug 2026** which this arbiter did
    #       not know: `TERMINATE_SESSION` (0x0011) would have been accused as
    #       «unknown type» and the reason `0x10 SESSION_TERMINATED` as
    #       «unknown reason».  ⚠ That is, the arbiter gave red to the server
    #       doing the only thing §7.6 allows it, on the message with which the
    #       user leaves the desktop.  This recording keeps that door closed.
    r = compliant()
    r.block(CLIENT, msg(0x0011, b""))
    r.block(SERVER, msg(0x000C, struct.pack("!B", 0x10) + s("exit")),
             fine=FIN)
    cases.append(("37-termina-sessione", r, 0, None,
                 "⭐ TERMINATE_SESSION (0x0011) and FAREWELL(0x10 "
                 "SESSION_TERMINATED): the two types of 15 August"))

    # =======================================================================
    # ⭐⛔ 38-45 — THE EIGHT RECORDINGS I DID NOT WRITE
    #
    # ⛔ On the evening of 16 Aug 2026, right after the sixteen above came out
    #    **41 out of 41 on the first run**, an agent was sent to **refute**
    #    this arbiter by reading `RCP.md` and not the validator.  It built 36
    #    counterexamples and found **14 divergent** ones.
    #
    # ⚠ «41 out of 41 on the first run» was true and did not mean what it
    #   seemed: the recordings and the rules had been written **in the same
    #   hour, by the same hand**, and it is the state `README.md` calls «two
    #   programs that agree and confirm nothing».  ⛔ The number that counts
    #   is not how many a bench written by whoever wrote the arbiter passes:
    #   it is how many it passes **after** someone has tried to break it.
    #
    # ⭐ These eight are those divergences, brought here so that they do not
    #    reopen.  The others — those outside the canvas mandate — are declared
    #    in the sub-phase report and stay `[?]`.
    # =======================================================================

    # ── 38. ⛔ §4.5 — `SESSION` beyond `video.max_size` ──────────────
    #    §4.5 puts in the same sentence the limits, the parity **and** this
    #    cap.  The arbiter applied two thirds of it.  ⚠ And the cap is not a
    #    preference: the client declares it because beyond it **it does not
    #    decode**.  The `HELLO` of `compliant()` declares 3840x2160.
    r = compliant()
    #    ⭐ 4096x2304 and not 7680x4320 (since 1 Oct 2026 the maximum of §4.5 is
    #      4096x2304): the size is WITHIN the normative limits, so what the
    #      arbiter accuses is ONLY the cap declared by the client.
    r.blocks[5] = (SERVER, 0x00, 0,
                    msg(0x0007, struct.pack("!B", 1)
                        + struct.pack("!II", 4096, 2304) + s("gnome")),
                    [], CONTINUE, 0)
    cases.append(("38-sessione-oltre-misura-massima", r, 1,
                 ("RCP.md §4.5", r.deviation(5, 7)),
                 "⛔ SESSION grants 4096x2304 to a client that declared "
                 "video.max_size = 3840x2160"))

    # ── 39. ⛔ §4.5 — and the same sentence holds for the canvas granted by `CANVAS`
    #    ⚠ If it did not, `FIT_CANVAS` would be the door through which one
    #      exceeds a cap the client declared so as not to be left in the dark.
    r = compliant()
    r.block(CLIENT, fit(4096, 2304))
    r.block(SERVER, canvas(1, 0, 4096, 2304))
    cases.append(("39-concessa-oltre-misura-massima", r, 1,
                 ("RCP.md §4.5", r.deviation(7, 8)),
                 "⛔ CANVAS(FITTED) grants 4096x2304 (within §4.5) beyond the "
                 "video.max_size declared in HELLO"))

    # ── 40. ⛔ §8.1 — the `CANVAS` sent AFTER its own `FAREWELL` ───────────────
    #    ⭐ It is the recording that resolved a **contradiction of the arbiter
    #       with itself**: it accused `FIT_CANVAS · FAREWELL` (no answer
    #       possible) and acquitted `FIT_CANVAS · FAREWELL · CANVAS`, that is it
    #       said at once that the answer could no longer arrive **and** that it
    #       had arrived.  §8.1 chooses: the farewell goes *«before closing the
    #       session»*, so it is the last message from that side.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, msg(0x000C, struct.pack("!B", 0x01) + s("")))
    r.block(SERVER, canvas(1, 0, 1280, 720))
    cases.append(("40-tela-dopo-il-congedo", r, 1,
                 ("RCP.md §4 (the handshake order)",
                  r.deviation(8, 0)),
                 "⛔ the server sends a CANVAS after its own FAREWELL: §8.1 wants "
                 "it «before closing the session»"))

    # ── 41. ⛔ §11.1 — the DECLARED `channel` that is not the type's high byte
    #    ⭐ Two bytes were enough to make a violation invisible: the same
    #       bytes as 22 — an unsolicited `CANVAS` — with the block declared
    #       `channel = 0x02`, came out ⭐ **compliant**.  §11.1 does not describe
    #       that field, it **defines** it: *«channel: the high byte of kind»*.
    #    ⚠ It is the same shape as `11-quanti-sotto-dichiarato`: wire that
    #      vanishes from the judgement with a file valid for every other line.
    r = compliant()
    r.block(SERVER, canvas(1, 0, 1280, 720), channel=0x02, stream=9)
    cases.append(("41-canale-dichiarato-falso", r, 2, None,
                 "⛔ an unsolicited CANVAS inside a block that declares itself "
                 "«clipboard»: the judgement skipped it"))

    # ── 42. ⛔ §11.1 — an obscured interval over a NUMERIC field ────────────
    #    ⭐ **A defect born and dead the same day**: the new rule T6 read
    #       inside the interval and accused *«grants canvas_width =
    #       707406378»* — and 707406378 is `0x2A2A2A2A`, the padding of §11.1
    #       read as a size.  ⛔ A protocol red on bytes the format declares it
    #       has replaced sends one looking for a server defect inside a choice
    #       of the recorder.
    r = compliant()
    body_t = struct.pack("!BBII", 1, 0, 1280, 720)
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER,
             msg(0x000E, body_t[:2] + bytes([FILL]) * 4 + body_t[6:]),
             obscured=[(6 + 2, 4, hashlib.sha256(body_t[2:6]).digest())])
    cases.append(("42-oscurato-su-un-numero", r, 2, None,
                 "⛔ an obscured interval over canvas_width of CANVAS: §11.1 "
                 "exists for the password, and that field is not judged"))

    # ── 43. ⭐ §6.2 — THE FRAME AT THE NEW SIZE **BEFORE** ITS `CANVAS`
    #
    #    ⛔ *«A frame at the NEW size may arrive BEFORE the `CANVAS` that grants
    #       it … the client MUST NOT close: it holds the frame»*, and the
    #       condition is *«as long as an `FIT_CANVAS` the client sent
    #       remains»*.
    #    ⭐ Until 16 Aug 2026 this recording exited **1**: B4 built the
    #       judge's context **without declaring any request in flight**, and
    #       the grace of §6.2 — written, imported, and naming
    #       `01-b4-validator.py` in full — was unreachable.
    #       ⇒ The arbiter closed *«a session in which nobody made a mistake»*.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, header(lar=1280, h=720) + b"\x00" * 128,
             channel=VIDEO, stream=7, fine=FIN)
    r.block(SERVER, canvas(1, 0, 1280, 720))
    cases.append(("43-fotogramma-prima-del-tela", r, 0, None,
                 "⭐ §6.2 — 1280x720 while an FIT_CANVAS is unanswered: "
                 "it is held, not closed"))

    # ── 44. ⭐ §6.2 / D14 — THE FRAME AT THE **OLD** SIZE AFTER THE `CANVAS`
    #    The other direction of the same scene: the `CANVAS(FITTED)` has passed
    #    and the frames already in flight **legitimately** carry the old size.
    #    ⛔ It exited 1 for a second reason, different from 43: B4 called
    #       `fit_canvas()` on a context **already** at the new size, and the
    #       judge has an early return when the size does not change — for it
    #       nothing had happened, and the queue did not open.
    r = compliant()
    r.block(CLIENT, fit(1280, 720))
    r.block(SERVER, canvas(1, 0, 1280, 720))
    r.block(SERVER, header(lar=1920, h=1080) + b"\x00" * 128,
             channel=VIDEO, stream=7, fine=FIN)
    cases.append(("44-fotogramma-vecchio-dopo-il-tela", r, 0, None,
                 "⭐ §6.2 D14 — 1920x1080 right after CANVAS(FITTED, 1280x720): "
                 "it was already in flight, and it is painted rescaled"))

    # ── 45. ⭐⛔ THE CONTRADICTION BETWEEN §7.1 AND §4.2, DECLARED AND NOT CHOSEN
    #    The client sends `FIT_CANVAS` and **closes** the channel.  §7.1 requires
    #    the server to answer; §4.2 forbids it to send after a FIN *«from either
    #    of the two parties»*.  ⇒ The two `MUST`s exclude each other, and it is
    #    not a lab case: it is the user who resizes the window and closes the
    #    tab in the same gesture.
    #    ⛔ It exits **0** because there is nothing to accusations — but the verdict
    #       **names** the contradiction, instead of filling it in silently.
    r = compliant()
    r.block(CLIENT, fit(1280, 720), fine=FIN)
    cases.append(("45-adatta-poi-fin-del-client", r, 0, None,
                 "⭐ FIT_CANVAS and then the CLIENT's FIN: §7.1 and §4.2 "
                 "contradict each other, and the arbiter says so instead of choosing"))

    # =======================================================================
    # ⭐⛔ 46-52 — WHAT `RCPREG 0x00 0x03` MAKES ARBITRABLE — 21 Aug 2026
    #
    # The `instant_ms` field was not added for completeness: it was added for
    # TWO rules that no recording could trigger — the grace second of §7.1 and
    # T4.  ⛔ And if these cases were not there, the field would be a cost paid
    # and never collected.
    # =======================================================================

    # ── 46. ⛔ the format of 12 August, `0x00 0x02`: it is REJECTED ─────────
    #    ⚠ Rejecting `0x01` is not enough: that is case 21, and the line that
    #      rejects `0x02` is ANOTHER line.  Without this case one could delete
    #      it and the bench would stay green — and it is exactly the shape in
    #      which the defect of 12 August lived for four days.
    r = compliant()
    r.magic = MAGIC_V2
    cases.append(("46-formato-del-12-agosto", r, 2, None,
                 "⛔ «RCPREG 0x00 0x02», compliant in all the rest: the block "
                 "is 17 bytes instead of 21 and it is REJECTED — misread, "
                 "every block would slip by four bytes"))

    # ── 47. ⛔ `clock` not declared ──────────────────────────────────────
    r = compliant()
    r.fake_clock = 0
    cases.append(("47-orologio-non-dichiarato", r, 2, None,
                 "⛔ `clock` = 0: §11.1 defines two (1 client, 2 "
                 "server), and without knowing WHOSE the times are the rule of "
                 "the grace second is not judgeable at all"))

    # ── 48. ⛔ the clock that goes backwards ────────────────────────────────
    r = compliant()
    r.blocks[3] = r.blocks[3][:6] + (5000,)
    r.blocks[4] = r.blocks[4][:6] + (200,)
    cases.append(("48-istante-che-torna-indietro", r, 2, None,
                 "⛔ an `instant_ms` smaller than the previous block: §11.1 "
                 "wants a MONOTONIC clock, and with `time.time()` instead of "
                 "`time.monotonic()` an NTP adjustment makes a POINTER "
                 "arrive «before» the CANVAS that precedes it on the wire"))

    # ── 49-50. ⭐⛔ THE GRACE SECOND OF §7.1, both directions ────────────────
    def with_grace(dt_ms):
        """The canvas drops to 1280x720, and then a POINTER valid on the OLD one.

        ⛔ (1900,1000) lies inside 1920x1080 and outside 1280x720: it is exactly
           the coordinate that §7.1 makes saturate **for one second** and
           reject afterwards.
        """
        r = compliant()
        r.block(CLIENT, fit(1280, 720), instant=500)
        r.block(SERVER, canvas(1, 0, 1280, 720), instant=1000)
        body_p = struct.pack("!IQII", 1, 0, 1900, 1000)
        r.block(CLIENT, msg(0x0101, body_p), channel=0x01, stream=9,
                 instant=1000 + dt_ms)
        # ⛔ And the server MUST have closed: here instead it keeps serving, and
        #    the proof is that it answers another request.  ⚠ Without this block
        #    the recording would end «with the session alive» and the arbiter
        #    would say — rightly — that it is not judged.
        r.block(CLIENT, fit(1600, 900), instant=1000 + dt_ms + 100)
        r.block(SERVER, canvas(1, 0, 1600, 900), instant=1000 + dt_ms + 150)
        return r

    r = with_grace(1500)
    cases.append(("49-grazia-scaduta", r, 1,
                 ("RCP.md §7.1", r.deviation(8, 0)),
                 "⛔ a POINTER on the OLD canvas 1500 ms after the "
                 "CANVAS(FITTED) — beyond the second of §7.1 — and the server "
                 "keeps serving instead of closing.  ⭐ It is the [?] that "
                 "`instant_ms` exists to close"))

    r = with_grace(800)
    cases.append(("50-grazia-dentro-il-secondo", r, 0, None,
                 "⭐ the same wire at 800 ms: the arbiter does NOT accuse, and ⛔ SAYS "
                 "it is not judgeable — the times are the client's, and "
                 "the server's true interval is longer than this"))

    # ── 51-52. ⭐⛔ T4 — «COMPLIANT IS NOT WORKS» ───────────────────────────
    def con_t4(measure_frames):
        r = compliant()
        r.block(CLIENT, fit(1264, 800), instant=50)
        r.block(SERVER, canvas(1, 0, 1264, 800), instant=100)
        for i, (l, a, ist, sid) in enumerate(measure_frames):
            r.block(SERVER, header(lar=l, h=a, num=i + 1) + b"\x00" * 64,
                     channel=VIDEO, stream=sid, fine=FIN, instant=ist)
        return r

    r = con_t4([(1920, 1080, 500, 7), (1920, 1080, 2000, 11),
                (1920, 1080, 4000, 15)])
    # ⛔ The accused byte is `canvas_width` of the `CANVAS(FITTED)`, that is 8
    #    bytes inside the message (6 of framing + outcome + reason): it is the
    #    field that declares the size the stage never had.
    cases.append(("51-t4-tela-finta", r, 1, ("RCP.md §7.1", r.deviation(7, 8)),
                 "⛔⛔ T4 — the server answers CANVAS(FITTED, 1264x800) and for "
                 "four seconds sends 1920x1080 frames: it stated the canvas and "
                 "did NOT touch the stage.  ⭐ It is the declared crack "
                 "of the whole of 6.6, and before `instant_ms` no arbiter "
                 "saw it"))

    # ⛔ AND THE SECOND FRAME ARRIVES AT 3500 ms, NOT AT 900 — 21 Aug 2026,
    #    and it was the mutation `t4-conta-invece-di-cronometrare` that said so.
    #
    #    With the pair (500, 900) the window is 800 ms, that is BELOW the cap:
    #    a T4 that looked at the FIRST frame instead of the window still came
    #    out «not judgeable», and this recording **did not tell counting from
    #    timing** — that is it did not prove the thing its own line declares
    #    it proves.  ⚠ It is the third time tonight that a fault written on
    #    purpose finds a case that was believed in.
    r = con_t4([(1920, 1080, 500, 7), (1264, 800, 3500, 11)])
    cases.append(("52-t4-il-palco-e-stato-toccato", r, 0, None,
                 "⭐ the same wire, but the second frame declares 1264x800 "
                 "BEYOND the cap: the stage was really touched.  ⛔ And the "
                 "FIRST stays 1920x1080 and is LEGAL — §6.2, the frame already "
                 "in flight — which is the reason T4 wants a cap in "
                 "TIME and not a count"))

    # ── 53. ⭐⛔ TWO FRAMES AFTER THE SAME `CANVAS` — the scene that the
    #        arbiter declared NON-COMPLIANT until 21 Aug 2026.
    #
    #    ⛔ It is the most ordinary scene there is: the canvas changes, the key
    #       frame at the new size arrives (§5.2 paid), the delta arrives after.
    #    ⚠ No recording in the repository carried TWO video streams after the
    #      same `CANVAS`, and the test client did not record the video: ⇒ the
    #      defect waited for the first real run with the video inside, and then
    #      it accused **the product** of something the product was doing right.
    r = compliant()
    r.block(CLIENT, fit(1264, 800), instant=50)
    r.block(SERVER, canvas(1, 0, 1264, 800), instant=100)
    r.block(SERVER, header(lar=1264, h=800, num=1) + b"\x00" * 64,
             channel=VIDEO, stream=7, fine=FIN, instant=200)
    r.block(SERVER, header(kind=DELTA, lar=1264, h=800, num=2)
             + b"\x00" * 64, channel=VIDEO, stream=11, fine=FIN, instant=300)
    cases.append(("53-due-fotogrammi-dopo-il-tela", r, 0, None,
                 "⭐ CANVAS(FITTED, 1264x800), then the KEY frame at the new size "
                 "and then a DELTA: §5.2 is paid by the key frame, and the delta is "
                 "legal.  ⛔ The arbiter replayed the canvas change at EVERY "
                 "stream and accused the second — it would have declared "
                 "every real session non-compliant"))

    return cases


def main():
    dove = sys.argv[1] if len(sys.argv) > 1 else "b4-registrazioni"
    os.makedirs(dove, exist_ok=True)
    cases = build()
    manifesto = []
    # ⛔ The count per outcome, COMPUTED: «thirteen recordings» does not say
    #    how many different outcomes they cover, and it is the coverage that counts.
    per_outcome = {}
    print(f"== the {len(cases)} recordings of B4  ->  {dove}/")
    for name, r, exit_code, expected, what in cases:
        fpath = os.path.join(dove, f"{name}.rcpreg")
        with open(fpath, "wb") as f:
            f.write(r.byte())
        manifesto.append({
            "file": f"{name}.rcpreg",
            "what": what,
            "exit": exit_code,
            "expected": ESITI[exit_code],
            "rule": None if expected is None else expected[0],
            "byte": None if expected is None else expected[1],
        })
        per_outcome[exit_code] = per_outcome.get(exit_code, 0) + 1
        if expected is None:
            print(f"   {name:<26s} expected exit {exit_code} = {ESITI[exit_code]:<20s} — {what}")
        else:
            print(f"   {name:<26s} expected exit {exit_code}, byte {expected[1]:<5} "
                  f"{expected[0]:<28s} — {what}")
    print()
    for u in sorted(ESITI):
        print(f"   exit {u} = {ESITI[u]:<20s} covered by "
              f"{per_outcome.get(u, 0)} recordings"
              + ("   ⛔ NONE" if not per_outcome.get(u) else ""))
    with open(os.path.join(dove, "manifesto.json"), "w") as f:
        json.dump(manifesto, f, indent=1, ensure_ascii=False)
    print(f"\n   the manifest — that is the EXPECTED, written here and not in the head of")
    print(f"   whoever is watching — is in {dove}/manifesto.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
