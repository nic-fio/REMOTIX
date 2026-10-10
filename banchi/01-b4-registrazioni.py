#!/usr/bin/env python3
"""01-b4-registrazioni.py — the B4 recordings, and what the validator MUST say.

    python3 01-b4-registrazioni.py [folder]     default: ./b4-registrazioni

⛔ **How many there are is not written here**: `costruisci()` builds them, the
   program counts them and prints them together with the manifest.  A number
   written by hand in a comment is the number nobody recomputes.

---------------------------------------------------------------------------
⛔ ONE COMPLIANT, AND THE OTHERS ARE THE FOUR WAYS OF NOT BEING SO

`FASI.md` §01-filo-nudo B4: without the **compliant** recording, «6 out of 6» is
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
one could break `Malformata` — turn it into a `NonConforme` — and this bench
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

*`fasi/06-la-tela-e-la-vista.md` §0 point 6: `ADATTA_TELA` (0x000B), `TELA`
(0x000E) and `VISTA` (0x0008) had been in the protocol for a week and **no
recording carried them**.  The seven rules that §7.1 writes in capital letters
were rules that no input triggered.*

| | |
|---|---|
| `22-tela-non-sollecitata` | **T1** §7.1 — it is also the ⏳ line that §7.1 declares missing: *«what the server does when the stage changes size by itself»* |
| `23-tela-doppia` | **T2** §6.2 — *«the n-th `TELA` answers the n-th `ADATTA_TELA`»* |
| `24` · `24bis` | **T3** §7.1 — the silence, by its two paths: the `CONGEDO` and the server's FIN |
| `24ter` | ⭐ the same scene that is **not** accused: the session is alive, and the trace merely ended earlier |
| `25` · `26` | outcome and reason outside the declared values |
| `27-tela-rifiutata-cambia` | **T5** §7.1 — every field is valid and the **relation** between the fields lies |
| `28` · `29` | **T6** §4.5 — the **granted** canvas odd, and out of bounds |
| `30-vista-cambia-tela` | **V3** §7.1 — *«`VISTA` MUST NOT change the canvas»* |
| `31-vista-legale` | ⭐ **V2** — 1x1, odd, 300x800, 9000x5000: finding **R1.17**, which must not come back in from the arbiter's side |
| `32-vista-zero` | **V1** §7.1 — *«from 1x1 up»* |
| `33-adatta-fuori-limiti-rifiutata` | ⭐ the impossible request is **lawful**: §7.1 devotes `MISURA_FUORI_LIMITI` to it |
| `34` · `35` | ⭐ the full round, and two requests in flight together |
| `36` · `37` | the order of the handshake, and the two types of 15 August (`TERMINA_SESSIONE`, `CONGEDO(0x10)`) |
| `38`-`45` | ⛔ **the eight not written by whoever wrote the arbiter** — see the box next to the code |

---------------------------------------------------------------------------
⚠ AND THE PASSWORD IS NOT THERE

The compliant recording contains a real `CREDENZIALI`, with the password
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
#      `Registrazione.scostamento()` computes them from `BLOCCO_BYTE`.  An
#      expected value written by hand would have required thirteen fixes, and it
#      would have been the time one gets forgotten.
MAGIA = b"RCPREG\x00\x03"
MAGIA_V1 = b"RCPREG\x00\x01"
MAGIA_V2 = b"RCPREG\x00\x02"
MAGIA_VECCHIA = MAGIA_V1        # ⚠ the old name stays for whoever imports it
RIEMPIMENTO = 0x2A
CLIENT, SERVER = 1, 2

# The block of §11.1: direction, channel, end, stream, length, quanti_oscurati.
BLOCCO = "!BBBIQIH"        # ⭐ +`istante_ms` since 21 Aug 2026: 21 bytes
BLOCCO_BYTE = struct.calcsize(BLOCCO)

# ⛔ `fine` — «how the stream was closed AFTER this block» (§11.1).
CONTINUA, FIN, RESET = 0, 1, 2

VIDEO = 0x03
CHIAVE, DELTA = 0x0301, 0x0302      # §6.2

# The four outcomes of `01-b4-validatore.py`, with their name — written here
# once so that the manifest carries them in full and not by number.
ESITI = {0: "compliant", 1: "non-compliant", 2: "broken-recording",
         3: "nothing-to-judge"}


# ---------------------------------------------------------------------------
def s(testo):
    """RCP.md §6.0: u16 length + UTF-8, without terminator."""
    b = testo.encode("utf-8") if isinstance(testo, str) else testo
    return struct.pack("!H", len(b)) + b


def cap(coppie):
    out = struct.pack("!H", len(coppie))
    for n, v in coppie:
        out += s(n) + s(v)
    return out


def msg(tipo, corpo, lunghezza=None):
    """The framing of §6.1: u16 type, u32 length, body."""
    n = len(corpo) if lunghezza is None else lunghezza
    return struct.pack("!HI", tipo, n) + corpo


CIAO = msg(0x0001, struct.pack("!H", 1) + cap([
    ("video.codec", "hevc,av1"),
    ("video.profondita", "8,10"),
    ("audio.codec", "opus,pcm"),
    ("video.livello", "5.1"),
    ("video.misura_massima", "3840x2160"),
    ("appunti.testo", "si"),
    ("input.tocco", "no"),
    ("client.nome", "cliente-di-prova 0.1.0"),
]))
ECCOMI = msg(0x0002, struct.pack("!H", 1) + cap([
    ("video.codec", "hevc"),
    ("video.profondita", "8,10"),
    ("audio.codec", "opus,pcm"),
    ("appunti.testo", "si"),
    ("banco.marca", "no"),
]))
AMMESSO = msg(0x0004, b"")
ATTACCA = msg(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080) + s("it"))
SESSIONE = msg(0x0007, struct.pack("!B", 1) + struct.pack("!II", 1920, 1080) + s("gnome"))

UTENTE, PAROLA = "prova", "parola-di-prova"


def credenziali():
    """The body of CREDENZIALI, and where the password falls inside the body.

    ⛔ It also returns the interval to obscure: the real recorder will do
       the same thing, and the fact that the computation is ONE ONLY is the
       reason §11.1 says «the format is one only, written once».
    """
    u, p = UTENTE.encode(), PAROLA.encode()
    corpo = s(u) + s(p)
    inizio_parola = 2 + len(u) + 2      # inside the message body
    return corpo, inizio_parola, len(p), hashlib.sha256(p).digest()


# ---------------------------------------------------------------------------
class Registrazione:
    """Builds the file of §11.1 keeping track of the offsets."""

    def __init__(self):
        self.blocchi = []
        # ⛔ The three ways of breaking the FILE instead of the wire, and they
        #    live here because a malformed recording is built **on purpose**:
        #    without them outcome 2 of the validator has no positive control
        #    (finding R7.13).
        self.dichiarate = {}    # index -> DECLARED length, different from the true one
        self.dichiara_quanti = None   # `quanti_blocchi` different from those written
        self.coda = b""         # bytes after the last block
        # ⛔ And the fourth: yesterday's MAGIC, `RCPREG 0x00 0x01`, with the
        #    16-byte block.  It serves one thing only, and it is the one §11.1
        #    asks for by name: *«an old validator must REJECT the new format»*.
        #    ⚠ A format that can only write its own version cannot certify that
        #      it knows how to reject the others.
        self.magia = MAGIA
        # ⛔ `orologio` of §11.1: 1 = the times are the client's.  The BUILT
        #    recordings declare it client because it is the direction in which
        #    the arbiter can conclude — declaring it «server» would make the
        #    rule of the second unaccusable, and a bench that takes away its
        #    own chance to fail is not a bench.
        self.orologio = 1
        self.orologio_falso = None   # for the deliberately malformed recording

    def blocco(self, verso, carico, canale=0x00, stream=0, oscurati=(),
               fine=CONTINUA, istante=0):
        """⛔ `fine` defaults to CONTINUA, and it is not laziness.

        The control channel lives on **a single stream for the whole session**
        (§2.5): inside a recording of the handshake that stream never closes,
        so `0` — «continues» — is the true value.
        ⚠ Putting `1` there to please a reader would say the session closed at
          every message.
        """
        self.blocchi.append((verso, canale, stream, carico, list(oscurati),
                             fine, istante))
        return self

    def scostamento(self, indice_blocco, dentro):
        """The ABSOLUTE offset in the file of byte `dentro` of the given block.

        ⛔ It rests on `BLOCCO_BYTE`, never on a 16 written by hand: that is what
           made the move to `0x00 0x02` a single line instead of thirteen
           expected values to fix.
        """
        p = 16
        for i, b in enumerate(self.blocchi):
            carico, osc = b[3], b[4]
            p += BLOCCO_BYTE + 40 * len(osc)
            if i == indice_blocco:
                return p + dentro
            p += len(carico)
        raise IndexError(indice_blocco)

    def byte(self):
        quanti = (len(self.blocchi) if self.dichiara_quanti is None
                  else self.dichiara_quanti)
        oro = (self.orologio if self.orologio_falso is None
               else self.orologio_falso)
        out = bytearray(self.magia
                        + struct.pack("!IBBBB", quanti, oro, 0, 0, 0))
        for i, (verso, canale, stream, carico, osc, fine, ist) in enumerate(
                self.blocchi):
            lung = self.dichiarate.get(i, len(carico))
            if self.magia == MAGIA_V1:
                out += struct.pack("!BBQIH", verso, canale, stream, lung,
                                   len(osc))
            elif self.magia == MAGIA_V2:
                out += struct.pack("!BBBQIH", verso, canale, fine, stream,
                                   lung, len(osc))
            else:
                out += struct.pack(BLOCCO, verso, canale, fine, ist, stream,
                                   lung, len(osc))
            for ini, qua, imp in osc:
                out += struct.pack("!II", ini, qua) + imp
            out += carico
        return bytes(out) + self.coda


def conforme():
    """The whole handshake, with the password obscured."""
    corpo, ini, qua, imp = credenziali()
    cred = msg(0x0003, corpo)
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    # the obscured interval is inside the block's PAYLOAD: 6 bytes of
    # framing, then the body
    r.blocco(CLIENT, cred[:6 + ini] + bytes([RIEMPIMENTO]) * qua + cred[6 + ini + qua:],
             oscurati=[(6 + ini, qua, imp)])
    r.blocco(SERVER, AMMESSO)
    r.blocco(CLIENT, ATTACCA)
    r.blocco(SERVER, SESSIONE)
    return r


# ---------------------------------------------------------------------------
def costruisci():
    """Each with its expected value: `(nome, registrazione, uscita, atteso, che)`.

    ⛔ `uscita` is the code the validator MUST return — 0 compliant,
       1 non-compliant, 2 broken recording, 3 nothing to judge — and
       `atteso` carries rule and byte **only** when the exit code is 1.  Before,
       there were two outcomes out of four here, and the two missing ones were
       exactly those the validator declares it has so as not to confuse a bench
       defect with a protocol defect (finding R7.13).
    """
    casi = []

    # ── 7. the compliant one — built first because it is the base of the others
    casi.append(("conforme", conforme(), 0, None,
                 "the whole handshake, with the password obscured"))

    # ── 1. length inconsistent with the type (§6.1) ─────────────────────────
    #    `ATTACCA` declares 4 bytes fewer than its fields want: the body ends
    #    while the view is being read.
    corpo_a = struct.pack("!IIII", 1920, 1080, 1920, 1080) + s("it")
    r = conforme()
    r.blocchi[4] = (CLIENT, 0x00, 0, msg(0x0006, corpo_a[:-6],
                                        len(corpo_a) - 6), [], CONTINUA, 0)
    # ⛔ The offending byte is where the MISSING field would have begun — here
    #    `vista_altezza`, after the first three u32 — not the end of the body.
    #    ⚠ The first expected value written on 10 August said «the end of the
    #      body», and the validator answered two bytes earlier.  It was right:
    #      the byte to show whoever diagnoses is the one from which reading
    #      cannot go on, not the one where the data ends.  It is the third time
    #      in a day that the EXPECTED is wrong and the tool is not.
    casi.append(("1-lunghezza-incoerente", r, 1,
                 ("RCP.md §6.1", r.scostamento(4, 6 + 12)),
                 "ATTACCA declares fewer bytes than its fields want"))

    # ── 2. invalid UTF-8 (§6.0) ──────────────────────────────────────────────
    #    A capability value with a broken sequence: 0xC3 without the second
    #    byte.  It is the case in which a careless receiver accepts and then
    #    shows a mangled name in a log.
    guasto = b"remotix\xc3\x28prova"
    corpo_c = struct.pack("!H", 1) + cap([("video.codec", "hevc")])
    # the list is rebuilt by hand to know WHERE the broken byte falls
    voci = [(b"video.codec", b"hevc"), (b"client.nome", guasto)]
    corpo_c = struct.pack("!HH", 1, len(voci))
    # ⚠ The offset accumulates over ALL the entries that come before, not only
    #   over the faulty one: the first run of 10 August computed it from the
    #   start of the list and accused a byte 19 positions further back.
    #   ⛔ It is the error this bench exists to catch — only this time it was
    #      in the EXPECTED, not in the validator.
    scost = None
    for n, v in voci:
        if v is guasto:
            scost = len(corpo_c) + 2 + len(n) + 2 + 7  # up to byte 0xC3
        corpo_c += s(n) + s(v)
    r = conforme()
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [], CONTINUA, 0)
    casi.append(("2-utf8-non-valido", r, 1,
                 ("RCP.md §6.0", r.scostamento(0, 6 + scost)),
                 "client.nome contains a broken UTF-8 sequence"))

    # ── 3. repeated capability name (§4.3) ──────────────────────────────────
    voci = [(b"video.codec", b"hevc"), (b"video.profondita", b"8"),
            (b"video.codec", b"av1")]
    corpo_c = struct.pack("!HH", 1, len(voci))
    scost = None
    for k, (n, v) in enumerate(voci):
        if k == 2:
            scost = len(corpo_c)
        corpo_c += s(n) + s(v)
    r = conforme()
    r.blocchi[0] = (CLIENT, 0x00, 0, msg(0x0001, corpo_c), [], CONTINUA, 0)
    casi.append(("3-capacita-ripetuta", r, 1,
                 ("RCP.md §4.3", r.scostamento(0, 6 + scost)),
                 "video.codec appears twice"))

    # ── 4. high byte outside the five channels (§2.5) ───────────────────────
    #    A type 0x0701: the high byte is 7, and the channels are five.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0701, b""), [], CONTINUA, 0)
    casi.append(("4-canale-sconosciuto", r, 1,
                 ("RCP.md §2.5", r.scostamento(3, 0)),
                 "a type whose high byte is not one of the five channels"))

    # ── 5. message in the wrong state (§4) ──────────────────────────────────
    #    ATTACCA before CREDENZIALI.
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(CLIENT, ATTACCA)
    casi.append(("5-stato-sbagliato", r, 1,
                 ("RCP.md §4 (the handshake order)", r.scostamento(2, 0)),
                 "ATTACCA before CREDENZIALI"))

    # ── 6. ⭐ right body but ALIGNED (§6.0) ──────────────────────────────────
    #    `AMMESSO` has an empty body; here it declares four bytes of padding —
    #    exactly what a C struct aligned to 4 would do.
    #    ⛔ And there is another message after it: a validator that does not
    #       know §6.0 would misread THAT one, and give red on the wrong byte.
    r = conforme()
    r.blocchi[3] = (SERVER, 0x00, 0, msg(0x0004, b"\x00\x00\x00\x00"), [],
                    CONTINUA, 0)
    casi.append(("6-riempimento", r, 1,
                 ("RCP.md §6.0", r.scostamento(3, 6)),
                 "AMMESSO with four bytes of padding, and a message after it"))

    # ── 7. ⛔ ODD canvas (§4.5) — the family no recording exercised, and it
    #        is the one in which the validator accused the wrong byte:
    #        `le.base, 0`, that is the start of the BODY as absolute and ZERO
    #        as relative — two different bytes for the same fault, while §11.1
    #        asks for two ways of saying the SAME byte (finding R7.12).
    #        The expected is the first byte of `tela_larghezza`, which sits at
    #        the start of the body of ATTACCA, that is six bytes after the
    #        start of the block.
    r = conforme()
    r.blocchi[4] = (CLIENT, 0x00, 0,
                    msg(0x0006, struct.pack("!IIII", 1921, 1080, 1920, 1080)
                        + s("it")), [], CONTINUA, 0)
    casi.append(("7-tela-dispari", r, 1,
                 ("RCP.md §4.5", r.scostamento(4, 6)),
                 "ATTACCA with tela_larghezza = 1921, odd"))

    # ── 8. ⛔ the TRUNCATED payload — positive control of outcome 2.
    #        The block declares more bytes than it carries: it is the file
    #        that is broken, not the wire that is non-compliant, and the two
    #        things want two different sentences.  ⚠ If `Malformata` became a
    #        `NonConforme`, this recording shouts it; before, none shouted it,
    #        and B4 kept printing «it is certified».
    r = conforme()
    r.dichiarate[5] = len(r.blocchi[5][3]) + 8
    casi.append(("8-carico-troncato", r, 2, None,
                 "the last block declares eight bytes that are not there"))

    # ── 9. ⛔ two obscured intervals that OVERLAP — §11.1 names it in full,
    #        and no recording exercised it.
    r = conforme()
    v, c, st, carico, osc, fine, ist = r.blocchi[2]
    ini_osc = osc[0][0]
    r.blocchi[2] = (v, c, st, carico,
                    [(ini_osc, 4, osc[0][2]), (ini_osc + 2, 4, osc[0][2])],
                    fine, ist)
    casi.append(("9-oscurati-sovrapposti", r, 2, None,
                 "two obscured intervals that overlap by two bytes"))

    # ── 10. ⛔ a TAIL after the last declared block.
    r = conforme()
    r.coda = b"\xff" * 16
    casi.append(("10-coda-di-spazzatura", r, 2, None,
                 "sixteen bytes after the last block: they are not part of the format"))

    # ── 11. ⛔ `quanti_blocchi` UNDER-DECLARED, and it is the most insidious:
    #         the file stays valid for every other line of §11.1, and the two
    #         trailing blocks are never read.  Here the fifth block carries an
    #         ATTACCA with the odd canvas — that is a real violation — which
    #         vanishes from the judgement by under-declaring.
    r = conforme()
    r.blocchi[4] = (CLIENT, 0x00, 0,
                    msg(0x0006, struct.pack("!IIII", 1921, 1080, 1920, 1080)
                        + s("it")), [], CONTINUA, 0)
    r.dichiara_quanti = 4
    casi.append(("11-quanti-sotto-dichiarato", r, 2, None,
                 "quanti_blocchi says 4 and the blocks are 6: the violation "
                 "is in the fifth"))

    # ── 12. ⛔ NOTHING TO JUDGE — outcome 3.  A well-formed file in which
    #         there is nothing this validator knows how to judge:
    #         «compliant» here would be true and empty (LEZIONI.md §1.9).
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
    r = Registrazione()
    r.blocco(CLIENT, msg(0x0201, b"\x00" * 8), canale=0x02, stream=6)
    casi.append(("12-niente-da-giudicare", r, 3, None,
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
    def con_video(*blocchi_video, base=None):
        """The whole handshake, and then the video.  ⛔ In this order.

        `SESSIONE` is the sixth block of `conforme()`, so every frame added
        here comes **after**, which is what §2.5 demands (P1).
        """
        r = conforme() if base is None else base
        for b in blocchi_video:
            # ⭐ the fifth element, optional, is the block's `istante_ms`:
            #    T4 needs it, and without it «how much time has passed» is not there.
            r.blocco(*b[:2], canale=VIDEO, stream=b[2], fine=b[3],
                     istante=(b[4] if len(b) > 4 else 0))
        return r

    def intestazione(tipo=CHIAVE, codec=1, lar=1920, alt=1080, num=1, ist=0,
                     inp=0):
        """The 28 bytes of §6.2, in network order and without padding.

        ⚠ Retraced here and not imported: this file **builds** the bytes, and
          whoever judges them is another program.  If they built and judged
          with the same function, an error in the structure would cancel
          itself out — which is the silent defect of `RCP.md` §0 inside a bench.
        """
        return struct.pack("!HHIIIQI", tipo, codec, lar, alt, num, ist, inp)

    # ── 13. ⭐ the frame that phase 2 exists to deliver ─────────────────────
    r = con_video((SERVER, intestazione() + b"\x00" * 512, 7, FIN))
    casi.append(("13-video-conforme", r, 0, None,
                 "⭐ a 1920x1080 key frame number 1 after SESSIONE, closed with "
                 "FIN: it respects all six lines of 12 August"))

    # ── 14. P1 — §2.5: no video stream before `SESSIONE` ───────────────────
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(SERVER, intestazione() + b"\x00" * 64, canale=VIDEO, stream=7,
             fine=FIN)
    casi.append(("14-video-prima-di-sessione", r, 1,
                 ("RCP.md §2.5", r.scostamento(2, 0)),
                 "⛔ P1 — a video stream opens before SESSIONE has "
                 "passed: the client knows neither the size nor the codec"))

    # ── 15. P3 — §2.5: a `0x03` on the control channel ──────────────────────
    #    ⛔ And it is written on STREAM 0, which is the control channel's: it
    #       is the only place where the server can go wrong, given that §2.5
    #       forbids it to open bidirectional streams.
    r = con_video((SERVER, intestazione() + b"\x00" * 64, 0, CONTINUA))
    casi.append(("15-video-sul-controllo", r, 1,
                 ("RCP.md §2.5", r.scostamento(6, 0)),
                 "⛔ P3 — the 28-byte header written on the stream of the "
                 "control channel"))

    # ── 16. P2 — §6.2: `numero` starts at 1, 0 is reserved ──────────────────
    r = con_video((SERVER, intestazione(num=0) + b"\x00" * 64, 7, FIN))
    casi.append(("16-video-numero-zero", r, 1,
                 ("RCP.md §6.2", r.scostamento(6, 12)),
                 "⛔ P2 — `numero = 0`, which §7.1 uses for «no frame»"))

    # ── 17. P5 — §6.2: the size MUST equal the granted canvas ───────────────
    #    ⛔ And the granted canvas is 1920x1080, and it sits in the `SESSIONE` of
    #       `conforme()`: it is not a number written in the validator.
    r = con_video((SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 64, 7,
                   FIN))
    casi.append(("17-video-misura-diversa", r, 1,
                 ("RCP.md §6.2", r.scostamento(6, 4)),
                 "⛔ P5 — a 1280x720 frame on a granted canvas of "
                 "1920x1080"))

    # ── 17-bis. ⭐⛔ P5 RESPECTED, AND IT IS THE RECORDING THAT CORRECTED
    #            `RCP.md` — §6.2 against §7.1.
    #
    #    The **very same bytes** as 17, but between `SESSIONE` and the frame a
    #    `TELA(ADATTATA, 1280, 720)` passes.  ⛔ With the first draft of P5 —
    #    *«the canvas granted in `SESSIONE`»* — this recording exited **1**:
    #    the client killed the session because the user had dragged a window,
    #    which is **exactly** the scene that §7.1 protects with its exception
    #    4.  ⭐ Corrected the same day into «the canvas **in force**», and this
    #    is the proof that holds it.
    #    ⚠ Without it the new rule would be as strict as the wrong one.
    #
    # ⛔⛔ AND ON 16 AUG 2026 THIS RECORDING CHANGED — sub-phase 6.6, and the
    #     change is **a measurement**, not maintenance.
    #
    #     As written on 12 August, it carried the `TELA(ADATTATA, 1280, 720)`
    #     **without any `ADATTA_TELA` before it**.  ⚠ That is, the recording
    #     that corrected `RCP.md` §6.2 staged a wire that §7.1 **forbids**: an
    #     unsolicited `TELA`, which §6.2 declares makes one *«close a healthy
    #     session»*.  Nobody had noticed because no arbiter counted the
    #     requests in flight — and it is error form E8 inside a bench: the
    #     right scene and the forbidden one looked the same.
    #
    # ⭐ Now the `ADATTA_TELA(1280, 720)` is there, and the recording says what
    #    it always meant to say: **the user dragged the window**.
    r = conforme()
    r.blocco(CLIENT, msg(0x000B, struct.pack("!II", 1280, 720)))
    r.blocco(SERVER, msg(0x000E, struct.pack("!BBII", 1, 0, 1280, 720)))
    r = con_video((SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 64, 7,
                   FIN), base=r)
    casi.append(("17bis-video-dopo-adatta-tela", r, 0, None,
                 "⭐ P5 — 1280x720 after ADATTA_TELA + TELA(ADATTATA, 1280, "
                 "720): the canvas in force is no longer that of SESSIONE, and "
                 "the frame is compliant"))

    # ── 18. P6 — §5.2: the first frame after `SESSIONE` MUST be a key frame
    r = con_video((SERVER, intestazione(tipo=DELTA) + b"\x00" * 64, 7, FIN))
    casi.append(("18-video-primo-delta", r, 1,
                 ("RCP.md §5.2", r.scostamento(6, 0)),
                 "⛔ P6 — the first frame of the session is a delta: "
                 "«the desktop appears in pieces», and nobody is wrong"))

    # ── 19. P4 — §6.2: FIN before the 28 bytes ──────────────────────────────
    r = con_video((SERVER, intestazione()[:12], 7, FIN))
    casi.append(("19-video-fin-corto", r, 1,
                 ("RCP.md §6.2", r.scostamento(6, 12)),
                 "⛔ P4 — the stream closes with FIN after 12 bytes: it is not a "
                 "short frame, it is a length that does not add up"))

    # ── 20. ⭐ P7 — §11.1: the `fine` field tells ABANDONMENT from error
    #    ⛔ It exits **0**, and that is the point: §5.1 allows the server to
    #       abandon a frame, the client throws it away and **the session
    #       holds**.  ⚠ Without the `fine` field this recording was identical
    #       to 19 — a payload that ends earlier than expected — and the arbiter
    #       had to choose between accusing a legal abandonment and acquitting a
    #       real truncation.
    r = con_video((SERVER, intestazione(), 7, CONTINUA),
                  (SERVER, b"\x00" * 4096, 7, RESET))
    casi.append(("20-video-abbandonato", r, 0, None,
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
    r = conforme()
    r.magia = MAGIA_VECCHIA
    casi.append(("21-formato-vecchio", r, 2, None,
                 "⛔ a «RCPREG 0x00 0x01» recording, compliant in all the "
                 "rest: it is REJECTED, not misread"))

    # =======================================================================
    # ⭐⛔ 22-37 — THE CANVAS AND THE VIEW, sub-phase 6.6, 16 Aug 2026
    #
    # ⛔ `fasi/06-la-tela-e-la-vista.md` §0 point 6: *«neither of the two sends
    #    an `ADATTA_TELA`»*.  ⇒ `ADATTA_TELA` (0x000B), `TELA` (0x000E) and
    #    `VISTA` (0x0008) had been in the protocol for a week and **no
    #    recording carried them**: the seven rules of §7.1 on the canvas were
    #    rules that no input triggered.
    #
    # ⛔ And here too **two per rule**: the one that violates it and the one that
    #    respects it.  The positive ones are not a courtesy — an arbiter strict
    #    on the canvas is exactly what would kill healthy sessions, and it is
    #    the defect §7.1 has already made once (finding R1.17, the view with
    #    the canvas limits).
    #
    # The offsets inside the body of `TELA`, counted from the start of the
    # message: 6 = outcome · 7 = reason · 8 = tela_larghezza · 12 = tela_altezza.
    # Inside `VISTA` and `ADATTA_TELA`: 6 = width · 10 = height.
    # =======================================================================
    def tela(esito, motivo, lar, alt):
        return msg(0x000E, struct.pack("!BBII", esito, motivo, lar, alt))

    def adatta(lar, alt):
        return msg(0x000B, struct.pack("!II", lar, alt))

    def vista(lar, alt):
        return msg(0x0008, struct.pack("!II", lar, alt))

    # ── 22. ⛔ T1 §7.1 — an UNSOLICITED `TELA` ──────────────────────────────
    #    ⚠ It is the case that the ⏳ missing line of §7.1 describes in full:
    #      *«what the server does when the stage changes size without any
    #      `ADATTA_TELA` having asked for it»*.  §6.2 answers for it: the
    #      client has no way of accepting it, and **closes a healthy
    #      session**.  Until that line exists, this is the verdict.
    r = conforme()
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("22-tela-non-sollecitata", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 0)),
                 "⛔ T1 — TELA(ADATTATA) without any ADATTA_TELA: the server "
                 "changes the canvas by itself"))

    # ── 23. ⛔ T2 §6.2 — TWO `TELA` for a single `ADATTA_TELA` ──────────────
    #    ⛔ The accused byte is that of the **second**: the first is right, and
    #       accusing it would send one looking for the defect in a correct
    #       answer.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("23-tela-doppia", r, 1,
                 ("RCP.md §6.2", r.scostamento(8, 0)),
                 "⛔ T2 — two TELA for a single ADATTA_TELA: from here on "
                 "the n-th TELA answers the (n+1)-th request"))

    # ── 24. ⛔ T3 §7.1 — `ADATTA_TELA` WITHOUT ANSWER, and then the CONGEDO ──
    #    ⛔ The accused byte is that of the REQUEST, not of the farewell: it is
    #       the request that was left hanging, and that is where whoever
    #       diagnoses must look.  ⚠ *«The symptom is "the application froze"»*.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, msg(0x000C, struct.pack("!B", 0x01) + s("")))
    casi.append(("24-adatta-senza-risposta", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 0)),
                 "⛔ T3 — ADATTA_TELA, then a CONGEDO and no TELA: the server "
                 "had TELA(RIFIUTATA, NON_ORA) even while closing"))

    # ── 24-bis. ⛔ T3 by the other path: the control channel CLOSES ─────────
    #    No farewell, but a FIN from the server side: the answer can no longer
    #    arrive, and the fact is in the bytes — it is the `fine` field of §11.1.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, b"", fine=FIN)
    casi.append(("24bis-adatta-senza-risposta-fin", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 0)),
                 "⛔ T3 — ADATTA_TELA and then the server closes the control "
                 "stream with FIN without answering"))

    # ── 24-ter. ⭐ THE SAME SCENE THAT IS **NOT** ACCUSED ───────────────────
    #    ⛔ Identical to 24 except the end: the stream continues, no farewell.
    #       The TELA can still arrive, and the recording merely **ended
    #       earlier**.  ⚠ Every trace of `01-b3-cliente.py` is of this kind —
    #       the client detaches by itself — and an arbiter that accused here
    #       would give a **perpetual false red** on every B3 run.
    #    ⭐ It is the recording that keeps T3 honest, as 17bis keeps P5
    #       honest: without it, «accuse the silence» and «accuse the end of the
    #       file» have the same colour.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    casi.append(("24ter-adatta-in-volo-traccia-viva", r, 0, None,
                 "⭐ T3 — an ADATTA_TELA in flight with the session still alive: "
                 "it is not accused, it is DECLARED as not judged"))

    # ── 25. ⛔ §7.1 — the outcome outside the two declared values ───────────
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(3, 0, 1280, 720))
    casi.append(("25-tela-esito-fuori", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 6)),
                 "⛔ TELA with outcome 3: §7.1 defines two, 1 = ADATTATA and "
                 "2 = RIFIUTATA"))

    # ── 26. ⛔ §7.1 — the reason outside the three declared ─────────────────
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(2, 4, 1920, 1080))
    casi.append(("26-tela-motivo-fuori", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 7)),
                 "⛔ TELA(RIFIUTATA) with reason 4: §7.1 defines three — "
                 "COMPOSITORE_INCAPACE, MISURA_FUORI_LIMITI, NON_ORA"))

    # ── 27. ⛔ T5 §7.1 — the REFUSAL that CHANGES the canvas ────────────────
    #    ⛔ The most insidious of the seven: the message is well formed, outcome
    #       and reason are lawful, and **every field taken alone is valid**.
    #       It is the relation between the fields that lies — the server says
    #       «I did not adapt» and declares in force a canvas that was not in
    #       force.  ⚠ And §6.2 ties the size of every following frame to it:
    #       from here on the client throws away the good frames.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(2, 3, 1280, 720))
    casi.append(("27-tela-rifiutata-cambia", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 8)),
                 "⛔ T5 — TELA(RIFIUTATA, NON_ORA) declaring 1280x720 in force "
                 "while the canvas was 1920x1080"))

    # ── 28. ⛔ T6 §4.5 — the GRANTED canvas with an ODD side ────────────────
    #    ⚠ And the REQUEST is even and within the limits — 1280x720 — on
    #      purpose: if the request were odd too, the accused byte would be
    #      right for two reasons at once, and one would not know which of the
    #      two holds.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1281, 720))
    casi.append(("28-tela-concessa-dispari", r, 1,
                 ("RCP.md §4.5", r.scostamento(7, 8)),
                 "⛔ T6 — TELA(ADATTATA) grants 1281x720: the odd side gets "
                 "rounded by the encoder, silently"))

    # ── 29. ⛔ T6 §4.5 — the GRANTED canvas out of bounds ───────────────────
    #    ⛔ And the HEIGHT, not the width: if the arbiter always accused the
    #       first field the byte would be right by chance.
    r = conforme()
    r.blocco(CLIENT, adatta(1920, 240))     # ⚠ the request is within the limits
    r.blocco(SERVER, tela(1, 0, 1920, 200))
    casi.append(("29-tela-concessa-fuori-limiti", r, 1,
                 ("RCP.md §4.5", r.scostamento(7, 12)),
                 "⛔ T6 — TELA(ADATTATA) grants a height of 200, below the "
                 "minimum of 240"))

    # ── 30. ⛔ V3 §7.1 — the `VISTA` that CHANGES THE CANVAS ────────────────
    #    *«VISTA MUST NOT change the canvas … the only message that changes
    #    the canvas is ADATTA_TELA»*.  On the wire it looks like this: the
    #    client resizes the window, sends `VISTA`, and the server **adapts the
    #    desktop** — which is precisely the behaviour that `?adatta=segui`
    #    must be able to keep OFF.
    r = conforme()
    r.blocco(CLIENT, vista(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("30-vista-cambia-tela", r, 1,
                 ("RCP.md §7.1", r.scostamento(7, 0)),
                 "⛔ V3 — the server answers a VISTA with a TELA: the view "
                 "must not change the canvas"))

    # ── 31. ⭐ V2 §7.1 — the 1x1 view IS LEGAL, and is not accused ──────────
    #    ⛔ *«Any size from 1x1 up is legal, odd included»*, and the canvas
    #       limits **do not apply** to the view: it is finding R1.17, and this
    #       recording exists so that it does not come back in from the
    #       arbiter's side.  ⚠ With the old line the client had three choices,
    #       all bad — and one was «get the session closed because it resized
    #       a window».
    r = conforme()
    r.blocco(CLIENT, vista(1, 1))
    r.blocco(CLIENT, vista(393, 851))       # a phone, odd sides
    r.blocco(CLIENT, vista(300, 800))       # below the canvas minimum
    r.blocco(CLIENT, vista(9000, 5000))     # above the canvas maximum
    casi.append(("31-vista-legale", r, 0, None,
                 "⭐ V2 — 1x1, 393x851 odd, 300x800 below the canvas "
                 "minimum and 9000x5000 above the maximum: all legal (§7.1, "
                 "R1.17)"))

    # ── 32. ⛔ V1 §7.1 — the view with a ZERO side ──────────────────────────
    #    «From 1x1 up»: zero is not «up», and §6.0 forbids implicit sentinel
    #    values — so it is not even «absent».
    r = conforme()
    r.blocco(CLIENT, vista(1280, 0))
    casi.append(("32-vista-zero", r, 1,
                 ("RCP.md §7.1", r.scostamento(6, 10)),
                 "⛔ V1 — VISTA with height 0: §7.1 says «from 1x1 up»"))

    # ── 33. ⭐ §7.1 — the OUT-OF-BOUNDS `ADATTA_TELA` is LAWFUL ─────────────
    #    ⛔ It is the most important non-strictness control of the series: §7.1
    #       devotes a refusal reason by name to the impossible size —
    #       `MISURA_FUORI_LIMITI` — and a reason exists to be reached.  An
    #       arbiter that rejected the request would make **unreachable** a
    #       branch the specification names, and no bench could exercise it
    #       any more.
    #    ⚠ And the refusal leaves the canvas where it was: 1920x1080, unchanged.
    r = conforme()
    r.blocco(CLIENT, adatta(8000, 4320))
    r.blocco(SERVER, tela(2, 2, 1920, 1080))
    casi.append(("33-adatta-fuori-limiti-rifiutata", r, 0, None,
                 "⭐ ADATTA_TELA(8000x4320) — outside the limits of §4.5 — and "
                 "TELA(RIFIUTATA, MISURA_FUORI_LIMITI) with the canvas unchanged: "
                 "it is the path §7.1 provides"))

    # ── 34. ⭐ THE FULL ROUND OF THE CANVAS, which must come out COMPLIANT ──
    #    ⛔ Without this, «sixteen out of sixteen» is compatible with an arbiter
    #       that rejects **every** ADATTA_TELA — and it would be green on all
    #       the violations.  In here: the request at attach, the answer, the
    #       frame at the NEW size (§6.2), a view that changes by itself, a
    #       second adaptation during the session, and an honest refusal.
    r = conforme()
    r.blocco(CLIENT, adatta(1264, 800))
    r.blocco(SERVER, tela(1, 0, 1264, 800))
    r.blocco(CLIENT, vista(1264, 800))
    r = con_video((SERVER, intestazione(lar=1264, alt=800) + b"\x00" * 256, 7,
                   FIN), base=r)
    r.blocco(CLIENT, adatta(1920, 1080))
    r.blocco(SERVER, tela(2, 1, 1264, 800))   # COMPOSITORE_INCAPACE
    r.blocco(CLIENT, vista(640, 401))
    casi.append(("34-tela-giro-pieno", r, 0, None,
                 "⭐ the full round: ADATTA_TELA → TELA(ADATTATA, 1264x800) → a "
                 "frame at the new size → a second request "
                 "refused with COMPOSITORE_INCAPACE, canvas unchanged"))

    # ── 35. ⭐ §6.2 — TWO REQUESTS IN FLIGHT TOGETHER, and the count holds ──
    #    *«Whoever drags a window sends two of them without the count getting
    #    lost»*.  ⛔ The two answers arrive in order, and the second declares
    #    the final canvas: an arbiter that paired by SIZE instead of by ORDER
    #    would fail here, because the first answer grants a size the client
    #    never asked for (§4.5 allows it).
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(CLIENT, adatta(1600, 900))
    r.blocco(SERVER, tela(1, 0, 1264, 800))   # ⚠ granted DIFFERENT from requested
    r.blocco(SERVER, tela(1, 0, 1600, 900))
    casi.append(("35-due-richieste-in-volo", r, 0, None,
                 "⭐ two ADATTA_TELA in flight together and two TELA in order, with "
                 "the first granting a size never asked for (§4.5)"))

    # ── 36. ⛔ §4 — `ADATTA_TELA` BEFORE `SESSIONE` ─────────────────────────
    #    It is not a canvas rule: it is the handshake.  It sits here because
    #    an arbiter that learned the canvas by putting `ADATTA_TELA` outside the
    #    state machine would open this hole without noticing.
    r = Registrazione()
    r.blocco(CLIENT, CIAO)
    r.blocco(SERVER, ECCOMI)
    r.blocco(CLIENT, adatta(1280, 720))
    casi.append(("36-adatta-prima-di-sessione", r, 1,
                 ("RCP.md §4 (the handshake order)",
                  r.scostamento(2, 0)),
                 "⛔ ADATTA_TELA before the session exists"))

    # ── 37. ⭐ §7.6 and §8.2 — `TERMINA_SESSIONE` and the `CONGEDO(0x10)` ───
    #    ⛔ Two types that entered on **15 Aug 2026** which this arbiter did
    #       not know: `TERMINA_SESSIONE` (0x0011) would have been accused as
    #       «unknown type» and the reason `0x10 SESSIONE_TERMINATA` as
    #       «unknown reason».  ⚠ That is, the arbiter gave red to the server
    #       doing the only thing §7.6 allows it, on the message with which the
    #       user leaves the desktop.  This recording keeps that door closed.
    r = conforme()
    r.blocco(CLIENT, msg(0x0011, b""))
    r.blocco(SERVER, msg(0x000C, struct.pack("!B", 0x10) + s("uscita")),
             fine=FIN)
    casi.append(("37-termina-sessione", r, 0, None,
                 "⭐ TERMINA_SESSIONE (0x0011) and CONGEDO(0x10 "
                 "SESSIONE_TERMINATA): the two types of 15 August"))

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

    # ── 38. ⛔ §4.5 — `SESSIONE` beyond `video.misura_massima` ──────────────
    #    §4.5 puts in the same sentence the limits, the parity **and** this
    #    cap.  The arbiter applied two thirds of it.  ⚠ And the cap is not a
    #    preference: the client declares it because beyond it **it does not
    #    decode**.  The `CIAO` of `conforme()` declares 3840x2160.
    r = conforme()
    #    ⭐ 4096x2304 and not 7680x4320 (since 1 Oct 2026 the maximum of §4.5 is
    #      4096x2304): the size is WITHIN the normative limits, so what the
    #      arbiter accuses is ONLY the cap declared by the client.
    r.blocchi[5] = (SERVER, 0x00, 0,
                    msg(0x0007, struct.pack("!B", 1)
                        + struct.pack("!II", 4096, 2304) + s("gnome")),
                    [], CONTINUA, 0)
    casi.append(("38-sessione-oltre-misura-massima", r, 1,
                 ("RCP.md §4.5", r.scostamento(5, 7)),
                 "⛔ SESSIONE grants 4096x2304 to a client that declared "
                 "video.misura_massima = 3840x2160"))

    # ── 39. ⛔ §4.5 — and the same sentence holds for the canvas granted by `TELA`
    #    ⚠ If it did not, `ADATTA_TELA` would be the door through which one
    #      exceeds a cap the client declared so as not to be left in the dark.
    r = conforme()
    r.blocco(CLIENT, adatta(4096, 2304))
    r.blocco(SERVER, tela(1, 0, 4096, 2304))
    casi.append(("39-concessa-oltre-misura-massima", r, 1,
                 ("RCP.md §4.5", r.scostamento(7, 8)),
                 "⛔ TELA(ADATTATA) grants 4096x2304 (within §4.5) beyond the "
                 "video.misura_massima declared in CIAO"))

    # ── 40. ⛔ §8.1 — the `TELA` sent AFTER its own `CONGEDO` ───────────────
    #    ⭐ It is the recording that resolved a **contradiction of the arbiter
    #       with itself**: it accused `ADATTA_TELA · CONGEDO` (no answer
    #       possible) and acquitted `ADATTA_TELA · CONGEDO · TELA`, that is it
    #       said at once that the answer could no longer arrive **and** that it
    #       had arrived.  §8.1 chooses: the farewell goes *«before closing the
    #       session»*, so it is the last message from that side.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, msg(0x000C, struct.pack("!B", 0x01) + s("")))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("40-tela-dopo-il-congedo", r, 1,
                 ("RCP.md §4 (the handshake order)",
                  r.scostamento(8, 0)),
                 "⛔ the server sends a TELA after its own CONGEDO: §8.1 wants "
                 "it «before closing the session»"))

    # ── 41. ⛔ §11.1 — the DECLARED `canale` that is not the type's high byte
    #    ⭐ Two bytes were enough to make a violation invisible: the same
    #       bytes as 22 — an unsolicited `TELA` — with the block declared
    #       `canale = 0x02`, came out ⭐ **compliant**.  §11.1 does not describe
    #       that field, it **defines** it: *«canale: the high byte of tipo»*.
    #    ⚠ It is the same shape as `11-quanti-sotto-dichiarato`: wire that
    #      vanishes from the judgement with a file valid for every other line.
    r = conforme()
    r.blocco(SERVER, tela(1, 0, 1280, 720), canale=0x02, stream=9)
    casi.append(("41-canale-dichiarato-falso", r, 2, None,
                 "⛔ an unsolicited TELA inside a block that declares itself "
                 "«clipboard»: the judgement skipped it"))

    # ── 42. ⛔ §11.1 — an obscured interval over a NUMERIC field ────────────
    #    ⭐ **A defect born and dead the same day**: the new rule T6 read
    #       inside the interval and accused *«grants tela_larghezza =
    #       707406378»* — and 707406378 is `0x2A2A2A2A`, the padding of §11.1
    #       read as a size.  ⛔ A protocol red on bytes the format declares it
    #       has replaced sends one looking for a server defect inside a choice
    #       of the recorder.
    r = conforme()
    corpo_t = struct.pack("!BBII", 1, 0, 1280, 720)
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER,
             msg(0x000E, corpo_t[:2] + bytes([RIEMPIMENTO]) * 4 + corpo_t[6:]),
             oscurati=[(6 + 2, 4, hashlib.sha256(corpo_t[2:6]).digest())])
    casi.append(("42-oscurato-su-un-numero", r, 2, None,
                 "⛔ an obscured interval over tela_larghezza of TELA: §11.1 "
                 "exists for the password, and that field is not judged"))

    # ── 43. ⭐ §6.2 — THE FRAME AT THE NEW SIZE **BEFORE** ITS `TELA`
    #
    #    ⛔ *«A frame at the NEW size may arrive BEFORE the `TELA` that grants
    #       it … the client MUST NOT close: it holds the frame»*, and the
    #       condition is *«as long as an `ADATTA_TELA` the client sent
    #       remains»*.
    #    ⭐ Until 16 Aug 2026 this recording exited **1**: B4 built the
    #       judge's context **without declaring any request in flight**, and
    #       the grace of §6.2 — written, imported, and naming
    #       `01-b4-validatore.py` in full — was unreachable.
    #       ⇒ The arbiter closed *«a session in which nobody made a mistake»*.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, intestazione(lar=1280, alt=720) + b"\x00" * 128,
             canale=VIDEO, stream=7, fine=FIN)
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    casi.append(("43-fotogramma-prima-del-tela", r, 0, None,
                 "⭐ §6.2 — 1280x720 while an ADATTA_TELA is unanswered: "
                 "it is held, not closed"))

    # ── 44. ⭐ §6.2 / D14 — THE FRAME AT THE **OLD** SIZE AFTER THE `TELA`
    #    The other direction of the same scene: the `TELA(ADATTATA)` has passed
    #    and the frames already in flight **legitimately** carry the old size.
    #    ⛔ It exited 1 for a second reason, different from 43: B4 called
    #       `adatta_tela()` on a context **already** at the new size, and the
    #       judge has an early return when the size does not change — for it
    #       nothing had happened, and the queue did not open.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720))
    r.blocco(SERVER, tela(1, 0, 1280, 720))
    r.blocco(SERVER, intestazione(lar=1920, alt=1080) + b"\x00" * 128,
             canale=VIDEO, stream=7, fine=FIN)
    casi.append(("44-fotogramma-vecchio-dopo-il-tela", r, 0, None,
                 "⭐ §6.2 D14 — 1920x1080 right after TELA(ADATTATA, 1280x720): "
                 "it was already in flight, and it is painted rescaled"))

    # ── 45. ⭐⛔ THE CONTRADICTION BETWEEN §7.1 AND §4.2, DECLARED AND NOT CHOSEN
    #    The client sends `ADATTA_TELA` and **closes** the channel.  §7.1 requires
    #    the server to answer; §4.2 forbids it to send after a FIN *«from either
    #    of the two parties»*.  ⇒ The two `MUST`s exclude each other, and it is
    #    not a lab case: it is the user who resizes the window and closes the
    #    tab in the same gesture.
    #    ⛔ It exits **0** because there is nothing to accuse — but the verdict
    #       **names** the contradiction, instead of filling it in silently.
    r = conforme()
    r.blocco(CLIENT, adatta(1280, 720), fine=FIN)
    casi.append(("45-adatta-poi-fin-del-client", r, 0, None,
                 "⭐ ADATTA_TELA and then the CLIENT's FIN: §7.1 and §4.2 "
                 "contradict each other, and the arbiter says so instead of choosing"))

    # =======================================================================
    # ⭐⛔ 46-52 — WHAT `RCPREG 0x00 0x03` MAKES ARBITRABLE — 21 Aug 2026
    #
    # The `istante_ms` field was not added for completeness: it was added for
    # TWO rules that no recording could trigger — the grace second of §7.1 and
    # T4.  ⛔ And if these cases were not there, the field would be a cost paid
    # and never collected.
    # =======================================================================

    # ── 46. ⛔ the format of 12 August, `0x00 0x02`: it is REJECTED ─────────
    #    ⚠ Rejecting `0x01` is not enough: that is case 21, and the line that
    #      rejects `0x02` is ANOTHER line.  Without this case one could delete
    #      it and the bench would stay green — and it is exactly the shape in
    #      which the defect of 12 August lived for four days.
    r = conforme()
    r.magia = MAGIA_V2
    casi.append(("46-formato-del-12-agosto", r, 2, None,
                 "⛔ «RCPREG 0x00 0x02», compliant in all the rest: the block "
                 "is 17 bytes instead of 21 and it is REJECTED — misread, "
                 "every block would slip by four bytes"))

    # ── 47. ⛔ `orologio` not declared ──────────────────────────────────────
    r = conforme()
    r.orologio_falso = 0
    casi.append(("47-orologio-non-dichiarato", r, 2, None,
                 "⛔ `orologio` = 0: §11.1 defines two (1 client, 2 "
                 "server), and without knowing WHOSE the times are the rule of "
                 "the grace second is not judgeable at all"))

    # ── 48. ⛔ the clock that goes backwards ────────────────────────────────
    r = conforme()
    r.blocchi[3] = r.blocchi[3][:6] + (5000,)
    r.blocchi[4] = r.blocchi[4][:6] + (200,)
    casi.append(("48-istante-che-torna-indietro", r, 2, None,
                 "⛔ an `istante_ms` smaller than the previous block: §11.1 "
                 "wants a MONOTONIC clock, and with `time.time()` instead of "
                 "`time.monotonic()` an NTP adjustment makes a PUNTATORE "
                 "arrive «before» the TELA that precedes it on the wire"))

    # ── 49-50. ⭐⛔ THE GRACE SECOND OF §7.1, both directions ────────────────
    def con_grazia(dt_ms):
        """The canvas drops to 1280x720, and then a PUNTATORE valid on the OLD one.

        ⛔ (1900,1000) lies inside 1920x1080 and outside 1280x720: it is exactly
           the coordinate that §7.1 makes saturate **for one second** and
           reject afterwards.
        """
        r = conforme()
        r.blocco(CLIENT, adatta(1280, 720), istante=500)
        r.blocco(SERVER, tela(1, 0, 1280, 720), istante=1000)
        corpo_p = struct.pack("!IQII", 1, 0, 1900, 1000)
        r.blocco(CLIENT, msg(0x0101, corpo_p), canale=0x01, stream=9,
                 istante=1000 + dt_ms)
        # ⛔ And the server MUST have closed: here instead it keeps serving, and
        #    the proof is that it answers another request.  ⚠ Without this block
        #    the recording would end «with the session alive» and the arbiter
        #    would say — rightly — that it is not judged.
        r.blocco(CLIENT, adatta(1600, 900), istante=1000 + dt_ms + 100)
        r.blocco(SERVER, tela(1, 0, 1600, 900), istante=1000 + dt_ms + 150)
        return r

    r = con_grazia(1500)
    casi.append(("49-grazia-scaduta", r, 1,
                 ("RCP.md §7.1", r.scostamento(8, 0)),
                 "⛔ a PUNTATORE on the OLD canvas 1500 ms after the "
                 "TELA(ADATTATA) — beyond the second of §7.1 — and the server "
                 "keeps serving instead of closing.  ⭐ It is the [?] that "
                 "`istante_ms` exists to close"))

    r = con_grazia(800)
    casi.append(("50-grazia-dentro-il-secondo", r, 0, None,
                 "⭐ the same wire at 800 ms: the arbiter does NOT accuse, and ⛔ SAYS "
                 "it is not judgeable — the times are the client's, and "
                 "the server's true interval is longer than this"))

    # ── 51-52. ⭐⛔ T4 — «COMPLIANT IS NOT WORKS» ───────────────────────────
    def con_t4(misura_fotogrammi):
        r = conforme()
        r.blocco(CLIENT, adatta(1264, 800), istante=50)
        r.blocco(SERVER, tela(1, 0, 1264, 800), istante=100)
        for i, (l, a, ist, sid) in enumerate(misura_fotogrammi):
            r.blocco(SERVER, intestazione(lar=l, alt=a, num=i + 1) + b"\x00" * 64,
                     canale=VIDEO, stream=sid, fine=FIN, istante=ist)
        return r

    r = con_t4([(1920, 1080, 500, 7), (1920, 1080, 2000, 11),
                (1920, 1080, 4000, 15)])
    # ⛔ The accused byte is `tela_larghezza` of the `TELA(ADATTATA)`, that is 8
    #    bytes inside the message (6 of framing + outcome + reason): it is the
    #    field that declares the size the stage never had.
    casi.append(("51-t4-tela-finta", r, 1, ("RCP.md §7.1", r.scostamento(7, 8)),
                 "⛔⛔ T4 — the server answers TELA(ADATTATA, 1264x800) and for "
                 "four seconds sends 1920x1080 frames: it stated the canvas and "
                 "did NOT touch the stage.  ⭐ It is the declared crack "
                 "of the whole of 6.6, and before `istante_ms` no arbiter "
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
    casi.append(("52-t4-il-palco-e-stato-toccato", r, 0, None,
                 "⭐ the same wire, but the second frame declares 1264x800 "
                 "BEYOND the cap: the stage was really touched.  ⛔ And the "
                 "FIRST stays 1920x1080 and is LEGAL — §6.2, the frame already "
                 "in flight — which is the reason T4 wants a cap in "
                 "TIME and not a count"))

    # ── 53. ⭐⛔ TWO FRAMES AFTER THE SAME `TELA` — the scene that the
    #        arbiter declared NON-COMPLIANT until 21 Aug 2026.
    #
    #    ⛔ It is the most ordinary scene there is: the canvas changes, the key
    #       frame at the new size arrives (§5.2 paid), the delta arrives after.
    #    ⚠ No recording in the repository carried TWO video streams after the
    #      same `TELA`, and the test client did not record the video: ⇒ the
    #      defect waited for the first real run with the video inside, and then
    #      it accused **the product** of something the product was doing right.
    r = conforme()
    r.blocco(CLIENT, adatta(1264, 800), istante=50)
    r.blocco(SERVER, tela(1, 0, 1264, 800), istante=100)
    r.blocco(SERVER, intestazione(lar=1264, alt=800, num=1) + b"\x00" * 64,
             canale=VIDEO, stream=7, fine=FIN, istante=200)
    r.blocco(SERVER, intestazione(tipo=DELTA, lar=1264, alt=800, num=2)
             + b"\x00" * 64, canale=VIDEO, stream=11, fine=FIN, istante=300)
    casi.append(("53-due-fotogrammi-dopo-il-tela", r, 0, None,
                 "⭐ TELA(ADATTATA, 1264x800), then the KEY frame at the new size "
                 "and then a DELTA: §5.2 is paid by the key frame, and the delta is "
                 "legal.  ⛔ The arbiter replayed the canvas change at EVERY "
                 "stream and accused the second — it would have declared "
                 "every real session non-compliant"))

    return casi


def main():
    dove = sys.argv[1] if len(sys.argv) > 1 else "b4-registrazioni"
    os.makedirs(dove, exist_ok=True)
    casi = costruisci()
    manifesto = []
    # ⛔ The count per outcome, COMPUTED: «thirteen recordings» does not say
    #    how many different outcomes they cover, and it is the coverage that counts.
    per_esito = {}
    print(f"== the {len(casi)} recordings of B4  ->  {dove}/")
    for nome, r, uscita, atteso, che in casi:
        percorso = os.path.join(dove, f"{nome}.rcpreg")
        with open(percorso, "wb") as f:
            f.write(r.byte())
        manifesto.append({
            "file": f"{nome}.rcpreg",
            "che": che,
            "uscita": uscita,
            "atteso": ESITI[uscita],
            "regola": None if atteso is None else atteso[0],
            "byte": None if atteso is None else atteso[1],
        })
        per_esito[uscita] = per_esito.get(uscita, 0) + 1
        if atteso is None:
            print(f"   {nome:<26s} expected exit {uscita} = {ESITI[uscita]:<20s} — {che}")
        else:
            print(f"   {nome:<26s} expected exit {uscita}, byte {atteso[1]:<5} "
                  f"{atteso[0]:<28s} — {che}")
    print()
    for u in sorted(ESITI):
        print(f"   exit {u} = {ESITI[u]:<20s} covered by "
              f"{per_esito.get(u, 0)} recordings"
              + ("   ⛔ NONE" if not per_esito.get(u) else ""))
    with open(os.path.join(dove, "manifesto.json"), "w") as f:
        json.dump(manifesto, f, indent=1, ensure_ascii=False)
    print(f"\n   the manifest — that is the EXPECTED, written here and not in the head of")
    print(f"   whoever is watching — is in {dove}/manifesto.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
