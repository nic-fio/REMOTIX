#!/usr/bin/env python3
"""01-b7-congedo.py — ⛔ B7: the farewell, read FROM THE RECEIVING SIDE.

    python3 01-b7-congedo.py --indirizzo 192.168.0.2 --porta 7447 \\
                             --registro /srv/src/b7-server.log \\
                             --pagina /srv/src/01-b11-pagina.html
    python3 01-b7-congedo.py --solo tempo-scaduto      (a single case)
    python3 01-b7-congedo.py --elenco                  (the predictions, without measuring)

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
    point 2   one sends `CONGEDO` with the reason **on the control channel**,
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
the `CONGEDO` to arrive.  The cure is there (the keep-alive armed in
`wt_chiudi_sessione`); **the permanent witness is this file**.

⛔ Hence the shape of the verdict, which is the reason B7 exists:

    for every case, the right reason by BOTH declared roads —
    an `&&`, never an `||`

`FASI.md` §01-filo-nudo §C1 builds the fault on purpose: *«the sending of the
`CONGEDO` is removed and the code in the closing is left: if B7 stays green it
is doing an `||` where an `&&` is needed»*.  With an `||` point 2 would
disappear and the bench would stay green.  Here point 2 and point 3 have **two
counters, two denominators and two red lines**.

===========================================================================
⛔ AND THE TWO ENGINES USE TWO DIFFERENT ROADS — `[M]` 10 Aug 2026, from B11

When **the page** is the one closing:

    Chrome    sends the `CONGEDO` on the control channel **and** closes the
              session with the code: both roads;
    Firefox   **resets** the control channel and throws away the `CONGEDO`
              already queued: the reason arrives **only** in the closing code.

⚠ **A bench that confused them would say «Firefox does not say farewell», which
  is false**: it is §3.1 point 2 that is *conditional* — «if the channel is still
  usable» — and on Firefox it no longer is.  Point 3, instead, is an
  **unconditional** MUST, and there Firefox is present.

⭐ That is why the two behaviours are **two distinct cases**, each with its
   roads DECLARED BEFORE measuring, and the denominators do not mix.  The
   «Firefox-style» case takes nothing away from the `CONGEDO` counter, and the
   «Chrome-style» case gives nothing to the closing one.

===========================================================================
⛔ WHICH REASONS CAN REALLY BE PROVOKED, AND WHY THE NUMBER IS «N OUT OF M»

§8.2 has **fifteen** reasons.  ⛔ Printing «8 out of 8» choosing the eight one
knows how to provoke is true **by construction**, and it is the emptiest form
of green there is: the denominator must be **declared**, with the list of what
was excluded and why.  Here those that can be provoked are **seven**, and the
other eight are in the `ESCLUSI` table with the reason for each — ⭐ and the
exclusion of `SERVER_IN_CHIUSURA` is not an opinion: it is **measured**, with
the `grep` of §«the measured exclusions», because an asserted exclusion is a
hole nobody rechecks.

⚠ Two exclusions are worth repeating here, because a bench that ignored them
  would **fail by construction**: `CREDENZIALI_ERRATE` and `TROPPI_TENTATIVI`
  do not travel in a `CONGEDO` — §4.4 puts them in `RESPINTO`, and §4.4 forbids
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
     `SESSIONE`.  ⛔ Without it, the `GIA_ATTIVA_REMOTA` case would be **green
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
    *reason* `TEMPO_SCADUTO` by both roads, and **prints** how long it waited:
    the five seconds are measured by **B6**, and duplicating a threshold here
    would give two different verdicts on the same property;
  · **the client→server direction, on the wire.**  There whoever receives is
    the server, and the only witness is its log.  ⚠ It is not the violation of
    §8.1: §8.1 forbids reading the farewell from the log of **whoever sends
    it**.  Here whoever sends is the bench.  ⭐ And so as not to rest on a single
    leg, those two cases verify **also on the wire** an observable consequence:
    that the place was left (§8.2 `0x0F`), with a new connection that gets to
    `SESSIONE`.
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

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ The B3 client is IMPORTED, not copied.  Inside it is the line that
#    prevents it from handing the control-channel events to aioquic's HTTP/3
#    layer — without which the connection dies at the hand of the CLIENT (10
#    Aug 2026) — and there is `_capsula_chiusura`, that is the reader of the
#    second road of §3.1.  A diverging copy would bring those defects back here
#    disguised as server defects.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

# ⛔ And the TARGET's profile: the differences between the two servers are in a
#    single file, and the four benches read them instead of discovering them anew.
_spec_b0 = importlib.util.spec_from_file_location(
    "b0bersaglio", os.path.join(QUI, "01-b0-bersaglio.py"))
b0 = importlib.util.module_from_spec(_spec_b0)
_spec_b0.loader.exec_module(b0)

s, inquadra = b3.s, b3.inquadra

CONGEDO, RESPINTO = 0x000C, 0x0005

# ⛔ §8.2 IN FULL, rewritten from `RCP.md` and imported from nobody.
#
#    `01-b3-cliente.py` knows eight of them: that is enough for it.  Here all
#    fifteen are needed, because B7's denominator is the whole of §8.2 — and
#    because this table is the **second reader** with which the page's one is
#    judged.
#    ⚠ Two tables written by the same hand confirm nothing: this one comes
#      from §8.2, that one from whoever wrote the page.
MOTIVI = {
    0x01: "CHIUSO_DALL_UTENTE", 0x02: "INATTIVITA",
    0x03: "SESSIONE_ABBANDONATA", 0x04: "SESSIONE_LOCALE_PREVALSA",
    0x05: "GIA_ATTIVA_LOCALE", 0x06: "BUDGET_PIENO",
    0x07: "CREDENZIALI_ERRATE", 0x08: "TROPPI_TENTATIVI",
    0x09: "NIENTE_IN_COMUNE", 0x0A: "VERSIONE_INCOMPATIBILE",
    0x0B: "ERRORE_PROTOCOLLO", 0x0C: "SERVER_IN_CHIUSURA",
    0x0D: "TEMPO_SCADUTO", 0x0E: "SESSIONE_NON_SERVIBILE",
    0x0F: "GIA_ATTIVA_REMOTA",
}

CHIUSO_DALL_UTENTE = 0x01
NIENTE_IN_COMUNE = 0x09
VERSIONE_INCOMPATIBILE = 0x0A
ERRORE_PROTOCOLLO = 0x0B
SERVER_IN_CHIUSURA = 0x0C
TEMPO_SCADUTO = 0x0D
SESSIONE_NON_SERVIBILE = 0x0E
GIA_ATTIVA_REMOTA = 0x0F

# ===========================================================================
# ⛔ THE DENOMINATOR, DECLARED — «N out of M that can be provoked», and M is here.
#
#    Every line of `ESCLUSI` carries the reason why phase 1 cannot produce it.
#    ⚠ Whoever adds a reason to those that can be provoked must remove it from
#    here: the two tables together must make fifteen, and
#    `certifica_denominatore()` verifies it instead of trusting.
# ===========================================================================
ESCLUSI = [
    (0x02, "30 minutes without INPUT: the input channel is born in phase 4 and "
           "the clock in phase 5"),
    (0x03, "6 hours without attaches: it is a clock of the SESSION, phase 5"),
    (0x04, "it wants a real LOCAL graphical session that prevails: the stage "
           "is born in phase 2"),
    (0x05, "likewise: to say it, the server must be able to look at the "
           "machine's local sessions (phase 2)"),
    (0x06, "it wants the encoding capacity, which is born in phase 3"),
    (0x07, "⛔ it does NOT travel in a CONGEDO: §4.4 puts it in RESPINTO, and forbids "
           "sending both.  Looking for it here would fail by construction "
           "— B5 and B8 measure it"),
    (0x08, "likewise, RESPINTO (§4.4-bis) — ⛔ and provoking it would block this "
           "address for at least 30 s, that is it would poison B8 and B10 (B0.3)"),
    (0x0C, "⛔ the GRAFT has no shutdown path: "
           "`RCP_SERVER_IN_CHIUSURA` appears on no line of "
           "`01-b3-rcp-innesta.py`.  ⚠ MEASURED below with grep, not "
           "assumed.  ⭐ And on `--bersaglio prodotto` this line DISAPPEARS: "
           "`src/main.c` says farewell to everyone with SERVER_IN_CHIUSURA before "
           "exiting, and those that can be provoked become EIGHT"),
]


# ⛔⭐ THE DENOMINATOR DEPENDS ON THE TARGET — and it is the difference between
#     the two servers that shows from a NUMBER instead of from a behaviour.
#
#       innesto    SEVEN that can be provoked + eight excluded = 15
#       prodotto   EIGHT that can be provoked + seven excluded = 15
#
# ⛔ *«The number to write next to an outcome is that of the target that was
#    started»* (`FASI.md` §01-filo-nudo B7).  ⚠ And if B7 pointed at the product
#    kept saying «seven out of seven», the denominator would be wrong and the
#    bench would be looking the other way: it would be a green by construction,
#    the emptiest form there is.
def esclusi_di(bersaglio):
    if b0.profilo(bersaglio)["spegnimento"]:
        return [(c, perche) for c, perche in ESCLUSI if c != SERVER_IN_CHIUSURA]
    return list(ESCLUSI)


def casi_di(bersaglio, tutti=None):
    """The cases THIS target can produce.

    ⛔ `server-in-chiusura` exists only against the product: against the graft
       it would stay waiting for a farewell no line of code can send, and its
       red would accuse the server of not doing something nobody ever taught
       it."""
    fuori = []
    for c in (tutti if tutti is not None else CASI):
        if c[1] == SERVER_IN_CHIUSURA and not b0.profilo(bersaglio)["spegnimento"]:
            continue
        fuori.append(c)
    return fuori


# ---------------------------------------------------------------------------
# The bytes, written by hand.
def capacita(voci, versione=1):
    out = struct.pack("!HH", versione, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


BUONE = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
         ("audio.codec", "opus,pcm"), ("client.nome", "banco-b7 0.1.0")]


def ciao(voci=None, versione=1):
    return inquadra(0x0001, capacita(BUONE if voci is None else voci, versione))


def attacca(tl=1920, ta=1080, vl=1920, va=1080, disp="it"):
    return inquadra(0x0006, struct.pack("!IIII", tl, ta, vl, va) + s(disp))


def congedo(motivo, dettaglio):
    """§7.1: `CONGEDO` = `u8 motivo` + `stringa dettaglio`."""
    return inquadra(CONGEDO, bytes([motivo]) + s(dettaglio))


def capsula_chiusura(motivo):
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
                  4, 0, 0, 0, motivo])  # length, and the code on 4 bytes


class Cliente(b3.Cliente):
    """The B3 client, plus the two ways of CLOSING (§3.1, §8.1)."""

    def chiudi_sessione(self, motivo):
        """§3.1 point 3 from the client's side: the capsule with the reason, then the FIN."""
        self._quic.send_stream_data(self.sessione, capsula_chiusura(motivo),
                                    end_stream=True)
        self.transmit()

    def azzera_controllo(self, codice=0):
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
        self._quic.reset_stream(self.controllo, codice)
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
class Registro:
    def __init__(self, percorso):
        self.percorso = percorso
        self.errore = None

    def leggibile(self):
        """⛔ «There is nothing» and «it cannot be read» look the same."""
        if not self.percorso:
            return False, "no log declared (--registro)"
        if not os.path.exists(self.percorso):
            return False, f"{self.percorso} DOES NOT EXIST"
        try:
            with open(self.percorso, "rb") as f:
                f.read(1)
        except OSError as e:
            return False, f"{self.percorso} cannot be read: {e}"
        return True, ""

    def finestra(self):
        """The tick mark from which to look: how long the file was now.

        ⭐ It is a marker, not a `sleep` (B0.7): what is judged are the bytes
           written AFTER this instant, and the lines of the previous cases can
           no longer enter a verdict that is not theirs.
        """
        try:
            return os.path.getsize(self.percorso)
        except OSError:
            return None

    def da(self, inizio):
        """The text written after the marker.  `None` if it cannot be read."""
        if inizio is None:
            return None
        try:
            with open(self.percorso, "rb") as f:
                f.seek(inizio)
                return f.read().decode("utf-8", "replace")
        except OSError as e:
            self.errore = str(e)
            return None

    async def attendi(self, inizio, frase, entro=6.0):
        """Waits for a line to appear, and says whether it appeared.

        ⚠ One waits because the log is written by another process and the two
          do not share a clock: reading at the exact instant one sent would
          measure our hurry.  ⛔ The window is declared and bounded: if it
          expires, the answer is «not within N s», not «it is not there».
        """
        fine = asyncio.get_event_loop().time() + entro
        while True:
            testo = self.da(inizio)
            if testo is None:
                return False, "the log cannot be read"
            if frase in testo:
                return True, ""
            if asyncio.get_event_loop().time() >= fine:
                return False, f"did not appear within {entro:.0f} s"
            await asyncio.sleep(0.05)

    def righe_nostre(self, inizio, quante=14):
        """The RCP lines written in the window — for the diagnosis, not for the
        verdict.  ⚠ ngtcp2's traffic is filtered out, here it is noise."""
        testo = self.da(inizio)
        if testo is None:
            return ["(the log cannot be read)"]
        righe = [r for r in testo.splitlines() if "REMOTIX" in r]
        return righe[-quante:] if righe else ["(no RCP line)"]


# ===========================================================================
# ⭐ THE PHRASES OF §8.2 — «BUDGET_PIENO is not "error 6"»
#
# §8.2: *«every reason MUST be showable to the user in an understandable
# phrase … and the phrase is built by the client, from the code»*.  ⛔ And the
# `dettaglio` is NOT shown: it is for the log.
#
# ⛔ «Fifteen out of fifteen» is not enough, and it is finding R3.20: a `switch`
#    with the default branch — `mostra("Error " + codice)` — produces fifteen
#    non-empty strings **all distinct from each other**.  The user reads «Error
#    14» for `SESSIONE_NON_SERVIBILE`, which §8.2 forbids with a ⛔ and an almost
#    identical example.  That is why the criteria are four, and the second is
#    the one that unmasks the `switch`.
# ===========================================================================
ANCORA_TABELLA = "const MOTIVO = new Map(["
VOCE = re.compile(r'\[\s*0x([0-9A-Fa-f]{1,2})\s*,\s*\[\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\]')


def leggi_tabella(testo):
    """Extracts {code: (name, phrase)} from the client's table.

    ⛔ It returns `(None, why)` when the table was not read: «zero phrases» and
       «I did not find the table» are two different facts, and confusing them
       would give a red to the client for a defect of the bench.
    """
    i = testo.find(ANCORA_TABELLA)
    if i < 0:
        return None, f"the anchor «{ANCORA_TABELLA}» is not in this file"
    j = testo.find("]);", i)
    if j < 0:
        return None, "the table starts and does not end: «]);» is missing"
    voci = {}
    for m in VOCE.finditer(testo[i:j]):
        voci[int(m.group(1), 16)] = (m.group(2), m.group(3))
    if not voci:
        return None, "the anchor is there but no entry matches the expected shape"
    return voci, ""


def giudica_frasi(voci):
    """The four criteria, one at a time, with the reason for the no.

    Returns [(code, ok, why)] for all fifteen reasons of §8.2.
    """
    fuori = []
    viste = {}
    for c in sorted(MOTIVI):
        nome_atteso = MOTIVI[c]
        if c not in voci:
            fuori.append((c, False, "⛔ the reason is not in the client's "
                                    "table: there is no phrase to show"))
            continue
        nome, frase = voci[c]
        f = frase.strip()
        chiave = " ".join(f.lower().split())
        if nome != nome_atteso:
            fuori.append((c, False, f"the name says «{nome}», §8.2 says "
                                    f"«{nome_atteso}»"))
            continue
        # 1. a phrase, not a label
        if len(f.split()) < 3:
            fuori.append((c, False, f"«{f}» is not a phrase ({len(f.split())} "
                                    f"words): §8.2 wants something "
                                    f"showable to the user"))
            continue
        # 2. ⛔ no number of the reason, and no «error N» — the switch with
        #    the default branch dies here.
        if re.search(r"(?<![0-9])%d(?![0-9])" % c, f) or \
           re.search(r"0x0?%x" % c, f, re.I) or \
           re.search(r"error\s*[:\-]?\s*[0-9]", f, re.I):
            fuori.append((c, False, f"⛔ «{f}» contains the NUMBER of the reason: "
                                    f"§8.2 forbids «error {c}»"))
            continue
        # 3. the name of the reason is not a phrase for the user
        if nome.lower() in f.lower() or nome in f:
            fuori.append((c, False, f"⛔ «{f}» is the NAME of the reason, not a "
                                    f"phrase: it is a number written in letters"))
            continue
        # 4. distinct from each other
        if chiave in viste:
            fuori.append((c, False, f"⛔ the same phrase as "
                                    f"{MOTIVI[viste[chiave]]}: two different "
                                    f"reasons saying the same thing"))
            continue
        viste[chiave] = c
        fuori.append((c, True, f))
    return fuori


# ---------------------------------------------------------------------------
# ⭐ THE FAKE TABLES — the positive control AND the one that says NO.
#
# ⚠ The good phrases contain NO digit, on purpose: criterion 2 looks for the
#   reason's number, and a test phrase that happened to carry one would make
#   the positive control fail, blaming the reader.
def _tabella_finta(frase_di):
    return {c: (MOTIVI[c], frase_di(c)) for c in MOTIVI}


def _buone():
    return _tabella_finta(
        lambda c: f"this is phrase {chr(96 + c)} to show to the user")


def certifica_frasi():
    """⭐ The tool that judges the phrases can say yes, and can say no.

    ⛔ Without this, «fifteen out of fifteen» is compatible with a reader that
       approves anything — and it is the defect B11 had to cure on the page,
       here applied to whoever reads.

    ⚠ The most important broken table is the second: the `switch` with the
      default branch produces fifteen non-empty strings **all distinct**, that
      is it passes every criterion except the one R3.20 had to write on purpose.
    """
    doppia = _buone()
    doppia[0x03] = (MOTIVI[0x03], doppia[0x04][1])
    mancante = _buone()
    del mancante[0x0E]
    # ⚠ The broken ones are written as someone in good faith would write them —
    #   whole phrases, long, distinct — because a too clumsy broken one would be
    #   rejected by the WRONG criterion, and the check would prove nothing about
    #   the criterion that matters.
    prove = [
        ("a good table", _buone(), True),
        ("⛔ the switch with the default branch",
         _tabella_finta(lambda c: f"Error {c} while connecting to the "
                                  f"server"), False),
        ("⛔ and the same thing written in hexadecimal",
         _tabella_finta(lambda c: f"the session closed with code "
                                  f"0x{c:02x}, try again"), False),
        ("⛔ two reasons with the same phrase", doppia, False),
        ("⛔ the phrase that carries the NAME of the reason",
         _tabella_finta(lambda c: f"the server answered {MOTIVI[c]} to "
                                  f"this request"), False),
        ("⛔ a reason missing altogether", mancante, False),
        ("⛔ a label instead of a phrase",
         _tabella_finta(lambda c: "not servable"), False),
    ]
    fuori = []
    for nome, voci, atteso in prove:
        esiti = giudica_frasi(voci)
        passa = all(ok for _, ok, _ in esiti)
        fuori.append((nome, passa == atteso,
                      "passed" if passa else
                      "rejected: " + next(p for _, ok, p in esiti
                                          if not ok)[:78]))
    return fuori


def certifica_lettori():
    """⭐ THE TWO READERS OF THE TWO ROADS, called from outside on known bytes.

    `CODER.md` §3.6: when the chain is already narrowed, one does not do another
    bench run — one calls the single suspect function on a known input.  ⛔ And
    without this, a «the reason did not arrive» stays ambiguous between «the
    server did not send it» and «the bench cannot read it» — that is exactly the
    defect B7 exists not to commit.
    """
    prove = []

    # ── road 2: the closing capsule ────────────────────────────────────────
    c, nuda = b3._capsula_chiusura(capsula_chiusura(0x0B))
    prove.append(("the capsule inside the DATA frame", (c, nuda) == (0x0B, False),
                  f"read {c!r}, bare={nuda}  (expected 11, False)"))
    c, nuda = b3._capsula_chiusura(capsula_chiusura(0x0B)[2:])
    prove.append(("⛔ the BARE capsule is read AND declared",
                  (c, nuda) == (0x0B, True),
                  f"read {c!r}, bare={nuda}  (expected 11, True)"))
    c, nuda = b3._capsula_chiusura(b"\x99\x99\x99\x99")
    prove.append(("⛔ and on random bytes it says NOTHING, not zero", c is None,
                  f"read {c!r}  (expected None — «0» would be the code that "
                  f"§3.1 forbids)"))

    # ── road 1: the framing of the CONGEDO ─────────────────────────────────
    #    The REAL `_sfoglia`, the one that runs on the wire, is called from outside.
    class Finto:
        def __init__(self):
            self.arrivati = bytearray()
            self.messaggi = asyncio.Queue()

    f = Finto()
    f.arrivati += congedo(0x0E, "disposizione sconosciuta: zz")
    b3.Cliente._sfoglia(f)
    try:
        tipo, corpo, _ = f.messaggi.get_nowait()
        ok = (tipo == CONGEDO and corpo[0] == 0x0E)
        det = struct.unpack("!H", corpo[1:3])[0]
        ok = ok and corpo[3:3 + det].decode() == "disposizione sconosciuta: zz"
        prove.append(("the CONGEDO is parsed, reason and detail", ok,
                      f"tipo={tipo:#06x} motivo={corpo[0]:#04x}"))
    except asyncio.QueueEmpty:
        prove.append(("the CONGEDO is parsed, reason and detail", False,
                      "no message from the reader"))

    f = Finto()
    f.arrivati += congedo(0x0E, "tronco")[:-3]
    b3.Cliente._sfoglia(f)
    prove.append(("⛔ and a truncated CONGEDO does NOT become a reason",
                  f.messaggi.empty(),
                  "the reader produced a message from incomplete bytes"
                  if not f.messaggi.empty() else "nothing, as it must"))
    return prove


def certifica_denominatore(casi, esclusi_lista=None):
    """⛔ M + the excluded must make fifteen, and the count is done by the program.

    A number written by hand in a comment is the number nobody recomputes:
    finding R7.14 found three of them in B5, and none of the three matched the
    file.
    """
    provocabili = {c[1] for c in casi}
    esclusi = {c for c, _ in (esclusi_lista if esclusi_lista is not None
                              else ESCLUSI)}
    doppi = provocabili & esclusi
    tutti = provocabili | esclusi
    if doppi:
        return False, ("these reasons can be provoked AND are excluded: "
                       + " ".join(MOTIVI[c] for c in sorted(doppi)))
    if tutti != set(MOTIVI):
        manca = set(MOTIVI) - tutti
        return False, ("§8.2 has 15 reasons and this bench names "
                       f"{len(tutti)}: missing "
                       + " ".join(MOTIVI[c] for c in sorted(manca)))
    return True, (f"{len(provocabili)} that can be provoked + {len(esclusi)} excluded "
                  f"= {len(MOTIVI)} reasons of §8.2")


# ===========================================================================
# ⛔ THE EXCLUSIONS ARE MEASURED — that of `SERVER_IN_CHIUSURA` above all.
# ===========================================================================
def esclusione_misurata(sorgenti):
    """How many times `RCP_SERVER_IN_CHIUSURA` appears in the sources OF THE TARGET.

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

    ⭐ The positive control stays on the same line: `RCP_TEMPO_SCADUTO` is surely
       there, and if the reader did not find even that one its «zero» would be
       worth nothing.

    Returns `(quanti, testo)`, with `quanti = None` if it could not be looked at.
    """
    quanti, controllo, letti, mancati = 0, 0, [], []
    for sorgente in sorgenti:
        try:
            with open(sorgente, encoding="utf-8", errors="replace") as f:
                testo = f.read()
        except OSError as e:
            mancati.append(f"{os.path.basename(sorgente)} ({e.strerror})")
            continue
        quanti += testo.count("RCP_SERVER_IN_CHIUSURA")
        controllo += testo.count("RCP_TEMPO_SCADUTO")
        letti.append(os.path.basename(sorgente))
    if mancati:
        return None, (f"⛔ {len(mancati)} sources out of {len(sorgenti)} cannot be "
                      f"read ({', '.join(mancati)}): the exclusion would stay "
                      f"ASSERTED instead of measured")
    if controllo == 0:
        return None, ("⛔ the reader does not find even `RCP_TEMPO_SCADUTO`, "
                      "which is surely there: its «zero» is worth nothing")
    return quanti, (f"`RCP_SERVER_IN_CHIUSURA`: {quanti} occurrences in "
                    f"{len(letti)} files ({', '.join(letti)})  ·  positive "
                    f"control `RCP_TEMPO_SCADUTO`: {controllo}")


# ===========================================================================
# What happened, from the receiving side.
# ===========================================================================
class Esito:
    def __init__(self, verso=None):
        self.verso = verso
        self.motivo = None        # from the CONGEDO — NEVER deduced, NEVER from the log
        self.tipo_motivo = None   # ⛔ in WHICH message (§11, §4.4)
        self.dettaglio = ""
        self.codice_wt = None     # §3.1 point 3, read on the wire
        self.riga_registro = None # §3.1 point 1
        self.al_server = {}       # the client→server direction, from the log
        self.posto_libero = None  # the observable consequence on the wire
        self.messaggi = []
        self.provocato = False    # ⛔ did the provocation really leave?
        self.fase = "opening"
        self.attesa_ms = None
        self.errore = None

    def __str__(self):
        p = []
        if not self.provocato:
            p.append(f"⛔ provocation NEVER LEFT (stopped in «{self.fase}»)")
        # ⚠ The first two entries say what THIS process received: they make
        #   sense only when the server is the one closing.  In the other
        #   direction whoever receives is the server, and printing them «absent»
        #   would invite reading a silence as a fault.
        if self.verso != VERSO_CS:
            if self.motivo is not None:
                p.append(f"CONGEDO={self.motivo:#04x}="
                         f"{MOTIVI.get(self.motivo, '?')} in {self.tipo_motivo}")
            elif self.tipo_motivo is not None:
                p.append(f"{self.tipo_motivo} without a readable reason")
            else:
                p.append("CONGEDO=(absent)")
            p.append("chiusura-WT=" + ("(absent)" if self.codice_wt is None
                                       else f"{self.codice_wt:#04x}"))
        for k, v in self.al_server.items():
            p.append(f"{k}={'yes' if v else 'NO'}")
        if self.posto_libero is not None:
            p.append("place=" + ("free" if self.posto_libero else "TAKEN"))
        if self.attesa_ms is not None:
            p.append(f"after {self.attesa_ms:.0f} ms")
        if self.errore:
            p.append(f"errore={self.errore}")
        return "  ".join(p)


async def osserva(cli, es, attesa, grazia=3.0):
    """⛔ The two roads, and BOTH are waited for — even when the first is missing.

    The `CONGEDO` travels on the control channel, the closing of the session is
    a capsule on the CONNECT stream: they are two roads and they arrive at two
    different moments.  ⭐ The server spaces them on purpose by five write
    passes (half a second), because otherwise the browser processes the capsule
    before the bytes of the stream and **nobody sees the `CONGEDO`**.

    ⛔ And the grace is waited for EVEN if the `CONGEDO` did not arrive: it is the
       case of the §C1 fault — farewell removed, code left — and a bench that
       stopped looking at the second road when the first is missing could not
       say WHICH of the two is missing.
    """
    orologio = asyncio.get_event_loop().time
    t0 = orologio()
    scadenza = t0 + attesa
    while True:
        resta = scadenza - orologio()
        if resta <= 0:
            break
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            break
        if m is None:            # connection terminated, or FIN on control
            break
        tipo, corpo, _ = m
        es.messaggi.append(tipo)
        if tipo in (CONGEDO, RESPINTO):
            es.tipo_motivo = "CONGEDO" if tipo == CONGEDO else "RESPINTO"
            es.attesa_ms = (orologio() - t0) * 1000
            # ⛔ An EMPTY body is not «no reason»: §7.1 wants the reason byte,
            #    and §3.1 forbids code 0.  With `corpo[0] if corpo` a server
            #    that closes BADLY would be easier to let through than one that
            #    closes well (finding R7.2).
            if not corpo:
                es.errore = (f"{es.tipo_motivo} with an EMPTY body: §7.1 wants "
                             "at least the reason byte")
                break
            es.motivo = corpo[0]
            if tipo == CONGEDO and len(corpo) >= 3:
                n = struct.unpack("!H", corpo[1:3])[0]
                es.dettaglio = corpo[3:3 + n].decode("utf-8", "replace")
            break
    fine = orologio() + grazia
    while cli.codice_chiusura is None and orologio() < fine:
        await asyncio.sleep(0.02)
    es.codice_wt = cli.codice_chiusura


# ===========================================================================
# The field: the connections of a case, and their closing.
# ===========================================================================
class Campo:
    def __init__(self, a, pila, registro, inizio):
        self.a = a
        self.pila = pila
        self.registro = registro
        self.inizio = inizio      # the marker in the server log

    async def apri(self, percorso="/rcp/1"):
        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536)
        conf.verify_mode = ssl.CERT_NONE
        autorita = f"{self.a.indirizzo}:{self.a.porta}"
        gestore = connect(self.a.indirizzo, self.a.porta, configuration=conf,
                          create_protocol=Cliente)
        cli = await gestore.__aenter__()
        self.pila.push_async_callback(chiudi_piano, gestore)
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            raise RuntimeError(f"the extended CONNECT answered {stato}")
        return cli

    async def eccomi(self, cli, corpo=None):
        cli.apri_controllo()
        cli.manda(corpo if corpo is not None else ciao())
        return await b3.attendi(cli, "ECCOMI")

    async def ammesso(self, cli):
        await self.eccomi(cli)
        cli.manda(inquadra(0x0003, s(self.a.utente) + s(self.a.parola)))
        return await b3.attendi(cli, "AMMESSO", attesa=20)

    async def sessione(self, cli, disp="it"):
        await self.ammesso(cli)
        cli.manda(attacca(disp=disp))
        return await b3.attendi(cli, "SESSIONE")


async def chiudi_piano(gestore):
    try:
        await gestore.__aexit__(None, None, None)
    except Exception:  # noqa: BLE001
        pass


# ===========================================================================
# ⛔ THE CASES.  Each declares BEFORE measuring: the expected reason, the
#    direction, and **which roads of §3.1 are enforceable** — which is the
#    declaration that prevents saying «Firefox does not say farewell».
# ===========================================================================
CASI = []
VERSO_SC, VERSO_CS = "server→client", "client→server"


def caso(nome, motivo, verso, strade, spiega):
    def dec(f):
        CASI.append((nome, motivo, verso, strade, spiega, f))
        return f
    return dec


# ── the server→client direction: both roads are demanded ───────────────────
#
# ⛔ In ALL these cases the control channel is open and usable at the instant
#    the server takes leave — the bench opens it, and the server does not take
#    leave before it exists.  So here the conditional of §3.1 point 2 **does not
#    bite**, and demanding the `CONGEDO` is not giving red to right code (which
#    was the fear of finding R3.3).  The case where the conditional bites is in
#    the other direction, and it is `chiuso-dall-utente-alla-firefox`.
@caso("errore-protocollo", ERRORE_PROTOCOLLO, VERSO_SC, ("congedo", "chiusura"),
      "a type that does not exist on the control channel: §3 forbids ignoring it")
async def _(campo, es):
    cli = await campo.apri()
    await campo.eccomi(cli)
    es.fase = "provocation"
    cli.manda(inquadra(0x00FF, b""))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("versione-incompatibile", VERSIONE_INCOMPATIBILE, VERSO_SC,
      ("congedo", "chiusura"),
      "CIAO(versione=2) on /rcp/1: §2.2 wants the two to coincide")
async def _(campo, es):
    cli = await campo.apri()
    cli.apri_controllo()
    es.fase = "provocation"
    cli.manda(ciao(versione=2))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("niente-in-comune", NIENTE_IN_COMUNE, VERSO_SC, ("congedo", "chiusura"),
      "`audio.codec = opus` without `pcm`: §4.3 requires it on both sides, and "
      "whoever does not declare it takes leave with NIENTE_IN_COMUNE — not with "
      "ERRORE_PROTOCOLLO: it did not misspell, it has nothing to talk about")
async def _(campo, es):
    cli = await campo.apri()
    cli.apri_controllo()
    es.fase = "provocation"
    cli.manda(ciao([("video.codec", "hevc"), ("video.profondita", "8"),
                    ("audio.codec", "opus")]))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("tempo-scaduto", TEMPO_SCADUTO, VERSO_SC, ("congedo", "chiusura"),
      "the control channel is opened and ONE KEEPS QUIET: §4.6, the cap for the CIAO. "
      "⚠ B7 demands the REASON, not the value of the cap: B6 measures the seconds")
async def _(campo, es):
    cli = await campo.apri()
    cli.apri_controllo()
    # ⛔⭐ AND HERE ONE PUSHES, BECAUSE SILENCE DOES NOT SEND ITSELF.
    #
    #    `create_webtransport_stream` writes the stream header —
    #    `0x41` plus the session identifier — but `aioquic` sends nothing until
    #    it is told `transmit()`.  ⚠ Without this line the server would see
    #    **no** stream, would open no RCP session, and the clock of the §4.6 cap
    #    would never start: the bench would wait twenty seconds and write
    #    «TEMPO_SCADUTO does not arrive» on a server that never knew it had to
    #    count.
    #
    # ⭐ From here on the provocation IS the silence, and it has left: the
    #    channel exists on the server's side, and the bench sends nothing more.
    cli.transmit()
    es.fase = "provocation"
    es.provocato = True
    await osserva(cli, es, attesa=20)


@caso("sessione-non-servibile", SESSIONE_NON_SERVIBILE, VERSO_SC,
      ("congedo", "chiusura", "dettaglio"),
      "ATTACCA with layout `zz`: WELL FORMED and unknown to the machine "
      "(§4.5 wants two different faults).  ⛔ And §8.2 requires the `dettaglio` in "
      "the body — which is written in the log and NOT shown to the user")
async def _(campo, es):
    cli = await campo.apri()
    await campo.ammesso(cli)
    es.fase = "provocation"
    cli.manda(attacca(disp="zz"))
    es.provocato = True
    await osserva(cli, es, attesa=12)


@caso("gia-attiva-remota", GIA_ATTIVA_REMOTA, VERSO_SC, ("congedo", "chiusura"),
      "two clients of the same user: the SECOND gets 0x0F (I2, §8.2). "
      "⛔ And the first must have reached SESSIONE, or the red and the green "
      "would mean the same thing")
async def _(campo, es):
    primo = await campo.apri()
    await campo.sessione(primo)          # ⛔ if this fails, `provocato`
    es.fase = "provocation"              #    stays false: it is not a failed
    secondo = await campo.apri()         #    test, it is a test not done
    await campo.ammesso(secondo)
    secondo.manda(attacca())
    es.provocato = True
    await osserva(secondo, es, attesa=12)


# ── the client→server direction: whoever receives is the server, and the roads are two ──
async def guarda_il_posto(campo, es):
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
    libero, perche = await stretta_intera(campo.a)
    es.posto_libero = libero
    if not libero:
        es.errore = (es.errore or "") + f" · the place is NOT free: {perche}"



@caso("chiuso-dall-utente-alla-chrome", CHIUSO_DALL_UTENTE, VERSO_CS,
      ("congedo", "chiusura", "posto"),
      "what Chrome does: `CONGEDO(0x01)` on the channel **and** the session closed "
      "with code 0x01.  §8.1 requires both of whoever closes")
async def _(campo, es):
    cli = await campo.apri()
    await campo.sessione(cli)
    es.fase = "provocation"
    cli.manda(congedo(CHIUSO_DALL_UTENTE, "il banco B7 chiude, come farebbe "
                                          "l'utente"))
    await asyncio.sleep(0.3)   # ⚠ the two bytes must not leave in the same
    cli.chiudi_sessione(CHIUSO_DALL_UTENTE)   # flight: it is the race B11
    es.provocato = True                       # found, here from the client's side
    await asyncio.sleep(0.5)
    await guarda_il_posto(campo, es)


@caso("chiuso-dall-utente-alla-firefox", CHIUSO_DALL_UTENTE, VERSO_CS,
      ("chiusura", "posto"),
      "⛔ what Firefox does: the session closes with code 0x01 and the control "
      "channel gets RESET, without any CONGEDO. §3.1 point 2 is "
      "conditional — «if the channel is still usable» — and here it is not: "
      "⚠ calling it «does not say farewell» would be false, the reason arrives the other way")
async def _(campo, es):
    cli = await campo.apri()
    await campo.sessione(cli)
    es.fase = "provocation"
    cli.chiudi_sessione(CHIUSO_DALL_UTENTE)
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
    cli.azzera_controllo()
    es.provocato = True
    await asyncio.sleep(0.5)
    await guarda_il_posto(campo, es)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⛔ THE CASE THAT EXISTS ONLY AGAINST THE PRODUCT — `SERVER_IN_CHIUSURA` 0x0C.
#
# *«And `0x0C` changed subject on the night of 10 August, and it is the first
# place where the two servers diverge visibly: the product now has a shutdown
# path — `src/main.c` says farewell to everyone with `SERVER_IN_CHIUSURA`
# before exiting — while the graft does not.»*
# (`FASI.md` §01-filo-nudo B7.)
#
# ⛔ It is the eighth reason that can be provoked, and without it B7 pointed at
#    the product would say «seven out of seven» **looking the other way**.
#
# ---------------------------------------------------------------------------
# ⛔ HOW IT IS PROVOKED, AND WHY THE BENCH KILLS ITS OWN SERVER
#
# `SERVER_IN_CHIUSURA` is not provoked with a crooked byte: a `SIGTERM` to the
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
@caso("server-in-chiusura", SERVER_IN_CHIUSURA, VERSO_SC,
      ("congedo", "chiusura"),
      "⭐ ONLY AGAINST THE PRODUCT: session open, then SIGTERM to the server. "
      "§8.1 forbids closing with a silence, and src/main.c says farewell to everyone with "
      "0x0C and WAITS for the bytes to go out before exiting.  ⛔ Against the graft "
      "this case does not exist: it would wait for a farewell no line can "
      "send")
async def _(campo, es):
    a = campo.a
    pid = getattr(a, "pid_server", 0)
    if not pid:
        es.fase = ("⛔ no --pid-server: I have nobody to send the "
                   "signal to.  Test NOT DONE, not test failed")
        return
    # ⛔ Who is that PID?  The kernel is asked, it is not deduced (CODER.md §3.7).
    try:
        with open(f"/proc/{pid}/comm", encoding="utf-8") as fp:
            comm = fp.read().strip()
    except OSError as e:
        es.fase = (f"⛔ /proc/{pid}/comm cannot be read ({e.strerror}): the "
                   f"process is no longer there, or it is not mine.  Test NOT "
                   f"DONE — and I send no signal in the dark")
        return
    if comm != "remotix":
        es.fase = (f"⛔ PID {pid} is now «{comm}», not «remotix»: I send it "
                   f"NOTHING.  PIDs get reused (R8.13), and a SIGTERM to a "
                   f"system process is not a measurement")
        return

    cli = await campo.apri()
    # ⛔ It gets to SESSIONE and not to AMMESSO: the farewell of §8.1 must
    #    reach a LIVE session, and a half handshake could drop because of a
    #    §4.6 cap while we wait.
    await campo.sessione(cli)
    es.fase = "provocation: SIGTERM to the server"
    os.kill(pid, signal.SIGTERM)
    es.provocato = True
    # ⚠ The wait is 12 s and not 3: `main.c` waits up to **two seconds** for the
    #   bytes of the farewell to really go out, and `wt_batti` lets the capsule
    #   of §3.1 point 3 mature half a second after the queue emptied.  A bench
    #   that stopped looking right away would read «no closing» on a server that
    #   is still talking.
    await osserva(cli, es, attesa=12)


# ===========================================================================
async def ancora_vivo(a):
    """⛔ B0.5 — after every case, the server must still be there.

    A server killed by the kernel «drops the connection» exactly like one that
    says farewell, and takes away everyone else's sessions.  ⚠ It gets to
    `ECCOMI` and not to `SESSIONE`: the second would cost the fixed second of
    §4.4-bis at every case, and the place is verified by whoever needs it.
    """
    async with contextlib.AsyncExitStack() as pila:
        campo = Campo(a, pila, None, None)
        try:
            cli = await campo.apri()
            await campo.eccomi(cli)
            return True, ""
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


async def stretta_intera(a, disp="it"):
    """The good handshake, whole, up to `SESSIONE` — and then it takes leave.

    ⭐ It is three things in one: the **initial state** declared and verified (B0.1),
       the **check that says yes** (a server that took leave of everything would
       give seven reasons out of seven and no session), and the proof that **the
       place is free** — without which `gia-attiva-remota` would be green for the
       wrong reason (B0.2).
    """
    async with contextlib.AsyncExitStack() as pila:
        campo = Campo(a, pila, None, None)
        try:
            cli = await campo.apri()
            _, corpo, _ = await campo.sessione(cli, disp)
            stato = corpo[0]
            lar, alt = struct.unpack("!II", corpo[1:9])
            # ⛔ One takes leave properly, instead of letting the connection
            #    drop: that way the place is free **immediately** for the next
            #    case, and not «when the transport has finished tearing down».
            cli.manda(congedo(CHIUSO_DALL_UTENTE, "controllo dello stato "
                                                  "iniziale di B7"))
            await asyncio.sleep(0.3)
            cli.chiudi_sessione(CHIUSO_DALL_UTENTE)
            await asyncio.sleep(0.4)
            return True, f"SESSIONE stato={stato} tela={lar}x{alt}"
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}"


async def gira_caso(a, registro, inizio, motivo, verso, f):
    es = Esito(verso)
    async with contextlib.AsyncExitStack() as pila:
        campo = Campo(a, pila, registro, inizio)
        try:
            await f(campo, es)
        except Exception as e:  # noqa: BLE001
            es.errore = f"{type(e).__name__}: {e}"
            # ⛔ AND THE REASON IS NOT SCRAPED FROM THE EXCEPTION TEXT.
            #    `b3.attendi` raises `RuntimeError("CONGEDO invece di …:
            #    motivo 0x0b = ERRORE_PROTOCOLLO")` even when what drops is the
            #    PREPARATION, and that string contains the name of the expected
            #    reason: the more broken the server is upstream, the more green
            #    the case would become (finding R7.1).  The reason is written
            #    only by `osserva`, from a message that arrived on the wire.
    # ── §3.1 point 1, and the client→server direction: from the server log ──
    if inizio is not None:
        if verso == VERSO_SC:
            # ⛔ WITHOUT THE PREFIX, and it is not laziness — 11 Aug 2026.
            #
            #    Here there was `f"REMOTIX B3: congedo motivo=…"`, that is the
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
            #    `congedo motivo=0xNN` is what the two servers have in common,
            #    and it is exactly the part §3.1 point 1 demands — the rest is
            #    the header of whoever writes the log, which is not part of the
            #    protocol.
            trovata, perche = await registro.attendi(
                inizio, f"congedo motivo={motivo:#04x}", entro=6)
            es.riga_registro = (trovata, perche)
        else:
            for chiave, frase in (
                    ("congedo-al-server",
                     f"the client takes its farewell, motivo={motivo:#04x}"),
                    ("chiusura-al-server",
                     f"the page closed the session, reason {motivo:#04x}")):
                trovata, _ = await registro.attendi(inizio, frase, entro=6)
                es.al_server[chiave] = trovata
    return es


def esigenze(strade, es, motivo, verso):
    """⛔ The verdict per road, and each with its own line.

    Returns [(label, enforceable, arrived, text)].  ⚠ `esigibile = False` does
    not mean «it is not looked at»: it is looked at and printed, but it does not
    enter the denominator of that road.  It is the difference between «Firefox
    does not say farewell» and «on Firefox point 2 is not enforceable».
    """
    fuori = []
    if verso == VERSO_SC:
        fuori.append((
            "§3.1 point 1 — the «what» line in the log of whoever closes",
            es.riga_registro is not None,
            bool(es.riga_registro and es.riga_registro[0]),
            "" if not es.riga_registro else (es.riga_registro[1] or "present")))
        fuori.append((
            "§3.1 point 2 — the reason in the CONGEDO on the channel",
            "congedo" in strade,
            es.motivo == motivo and es.tipo_motivo == "CONGEDO",
            "absent" if es.motivo is None
            else f"{es.motivo:#04x} in {es.tipo_motivo}"))
        fuori.append((
            "§3.1 point 3 — the reason in the closing of the session",
            "chiusura" in strade,
            es.codice_wt == motivo,
            "absent" if es.codice_wt is None else f"{es.codice_wt:#04x}"))
        # ⛔ §11 is counted only if a reason DID arrive: «in which message» is
        #    not a question one can ask a silence, and counting it failed twice
        #    would inflate the red of road 2.
        fuori.append((
            "§11 — the reason in the right message (CONGEDO, not RESPINTO)",
            es.motivo is not None,
            es.tipo_motivo == "CONGEDO",
            f"arrived in {es.tipo_motivo}" if es.motivo is not None
            else "no reason arrived: the question «in which message» "
                 "has no object"))
        if "dettaglio" in strade:
            fuori.append((
                "§8.2 — the `dettaglio` in the body (for the log, not for "
                "the user)", True, bool(es.dettaglio),
                es.dettaglio or "absent"))
    else:
        fuori.append((
            "§3.1 point 2 — the reason in the CONGEDO on the channel",
            "congedo" in strade,
            bool(es.al_server.get("congedo-al-server")),
            "the server wrote it"
            if es.al_server.get("congedo-al-server")
            else ("absent — and it is expected: the channel is reset"
                  if "congedo" not in strade else "absent")))
        fuori.append((
            "§3.1 point 3 — the reason in the closing of the session",
            "chiusura" in strade,
            bool(es.al_server.get("chiusura-al-server")),
            "the server wrote it"
            if es.al_server.get("chiusura-al-server") else "absent"))
        if "posto" in strade:
            fuori.append((
                "and the place is freed, observed ON THE WIRE", True,
                bool(es.posto_libero), "free" if es.posto_libero
                else "TAKEN: §8.2 0x0F to whoever has no session"))
    return fuori


VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def riga(ok, nome, testo):
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
          f"{nome:34s} {testo}")


def inf(testo):
    print(f"    --  {testo}")


async def principale(a):
    registro = Registro(a.registro)
    # ⛔ The cases and the excluded are those OF THE TARGET: against the product
    #    `server-in-chiusura` is there and 0x0C leaves the excluded; against the
    #    graft it is the opposite.  ⭐ The number B7 prints next to an outcome is
    #    that of the target that was started, not that of the document.
    TUTTI = casi_di(a.bersaglio)
    ESCL = esclusi_di(a.bersaglio)
    casi = [c for c in TUTTI if not a.solo or a.solo in c[0]]
    if a.escludi:
        prima = len(casi)
        casi = [c for c in casi if a.escludi not in c[0]]
        a.esclusi_a_mano = prima - len(casi)
    else:
        a.esclusi_a_mano = 0

    # ── --elenco: the predictions, and the denominator, without measuring ──
    if a.elenco:
        print(f"== B7 — the farewell from the receiving side\n")
        print(f"   ⛔ {len({c[1] for c in TUTTI})} reasons THAT CAN BE PROVOKED out of "
              f"{len(MOTIVI)} of §8.2, in {len(TUTTI)} cases.  Every line is a "
              f"PREDICTION written before measuring\n")
        for nome, motivo, verso, strade, spiega, _ in TUTTI:
            print(f"  {nome:34s} {motivo:#04x} {MOTIVI[motivo]}  [{verso}]")
            print(f"  {'':34s}   enforceable roads: {', '.join(strade)}")
            print(f"  {'':34s}   {spiega}")
        print(f"\n   ⛔ AND THE {len(ESCL)} EXCLUDED, with the why — without "
              f"this list «7 out of 7» would be true by construction:\n")
        for c, perche in ESCL:
            print(f"  {MOTIVI[c]:26s} {c:#04x}  {perche}")
        ok, testo = certifica_denominatore(TUTTI, ESCL)
        print(f"\n   {'⭐' if ok else '⛔'} {testo}")
        return 0 if ok else 3

    # ⛔ THE RUN'S LOG — and the first line says against what one measures.
    #    Until 11 Aug 2026 B7 had none.
    a.reg = b0.Registro(a.uscita, a.bersaglio, a.porta, a.giro or None,
                        a.md5 or None)
    a.reg.apri_giro(
        "B7", "one case per reason, each on a new connection; the "
              "farewell is read ON THE WIRE from the receiving side, never from the log "
              "of whoever sends it",
        extra={"casi": len(casi), "casi_del_bersaglio": len(TUTTI),
               "provocabili": len({c[1] for c in TUTTI}),
               "esclusi": len(ESCL), "filtro": a.solo,
               # ⛔ THE NUMBER THAT CHANGES WITH THE TARGET, written BEFORE
               #    measuring: seven against the graft, eight against the product.
               "attesi_provocabili": b0.profilo(a.bersaglio)["motivi_provocabili"],
               "pid_server": getattr(a, "pid_server", 0)})
    print("== B7 — the farewell, verified FROM THE RECEIVING SIDE (§8.1)")
    print(f"   ⛔ TARGET: {a.bersaglio} · port {a.porta} · binary md5 "
          f"{(a.md5 or 'unknown')[:12]}…")
    atteso_prov = b0.profilo(a.bersaglio)["motivi_provocabili"]
    visti_prov = len({c[1] for c in TUTTI})
    if visti_prov != atteso_prov:
        print(f"   {ROSSO}⛔ the reasons that can be provoked on this target should be "
              f"{atteso_prov} and the cases cover {visti_prov}{GRIGIO}")
        print(f"      ⛔ It is not a server red: it is the bench that cannot "
              f"count what it is about to measure.")
        return 3
    print(f"   ⛔ {visti_prov} reasons that can be provoked out of {len(MOTIVI)} of §8.2 — and "
          f"the number is the TARGET's, not the document's")
    print("   ⛔ for every reason: the CONGEDO on the channel **and** the code in the "
          "closing")
    print("      of the session — two roads, two counters, one `&&`\n")

    # ═══ THE CERTIFICATION, BEFORE MEASURING ═══════════════════════════════
    print("== ⭐ The bench certifies itself before pointing at the unknown "
          "(CODER.md §3.3)")
    guasti_cert = 0
    ok, testo = certifica_denominatore(TUTTI, ESCL)
    riga(ok, "the denominator adds up", testo)
    guasti_cert += 0 if ok else 1
    for nome, ok, testo in certifica_lettori():
        riga(ok, nome, testo)
        guasti_cert += 0 if ok else 1
    for nome, ok, testo in certifica_frasi():
        riga(ok, nome, testo)
        guasti_cert += 0 if ok else 1
    if a.registro:
        ok, perche = registro.leggibile()
        riga(ok, "the server log can be read", perche or a.registro)
        guasti_cert += 0 if ok else 1
    else:
        inf("⚠ no --registro: §3.1 point 1 and the client→server direction are NOT")
        inf("  measured, and the run will be declared PARTIAL")

    print("\n== ⭐ The initial state, declared and verified (B0.1, B0.2)")
    inf("a whole handshake: if the place were already occupied by the previous")
    inf("run, `gia-attiva-remota` would be green for the wrong reason")
    marca = registro.finestra() if a.registro else None
    ok, testo = await stretta_intera(a)
    riga(ok, "stretta-di-mano-intera", testo)
    guasti_cert += 0 if ok else 1
    if a.registro and ok:
        # ⭐ The positive control of the log READER, on the line that must
        #    surely be there — and the negative one on one that is not.
        trovata, perche = await registro.attendi(
            marca, f"admitted utente={a.utente}", entro=6)
        riga(trovata, "⭐ the log reader finds",
             f"«admitted utente={a.utente}»" if trovata else perche)
        guasti_cert += 0 if trovata else 1
        testo_finestra = registro.da(marca) or ""
        finta = "congedo motivo=0xff" not in testo_finestra
        riga(finta, "⛔ and does not find what is not there",
             "«congedo motivo=0xff» is not there, as it must")
        guasti_cert += 0 if finta else 1

    if guasti_cert:
        print(f"\n    {ROSSO}⛔ B7 DOES NOT MEASURE: the tool is not certified "
              f"({guasti_cert} checks failed){GRIGIO}")
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
    if not a.registro:
        prima = len(casi)
        casi = [c for c in casi if c[2] != VERSO_CS]
        if prima != len(casi):
            print(f"    {GIALLO}⚠{GRIGIO} without --registro the {prima - len(casi)}"
                  f" client→server cases are NOT run: the witness is missing")

    # ═══ THE CASES  ═════════════════════════════════════════════════════════
    if not casi:
        print(f"\n    {ROSSO}⛔ «--solo {a.solo}» selected ZERO cases out of "
              f"{len(TUTTI)}: there is nothing to measure{GRIGIO}")
        print("       This is NOT a green.  The names are read with --elenco.")
        return 2

    print(f"\n== The cases: {len(casi)} out of {len(TUTTI)}, "
          f"{len({c[1] for c in casi})} reasons out of "
          f"{len({c[1] for c in TUTTI})} that can be provoked")
    if a.solo:
        print(f"    {GIALLO}⚠ PARTIAL RUN{GRIGIO}: the green outcome reads «the "
              f"selected cases pass», never «B7 passes»")
    if a.esclusi_a_mano:
        print(f"    {GIALLO}⚠{GRIGIO} {a.esclusi_a_mano} cases removed by "
              f"«--escludi {a.escludi}»: the run is PARTIAL, and the green outcome "
              f"does not cover them")

    conti = {
        "§3.1 point 1 — the «what» line in the log of whoever closes": [0, 0],
        "§3.1 point 2 — the reason in the CONGEDO on the channel": [0, 0],
        "§3.1 point 3 — the reason in the closing of the session": [0, 0],
        "§11 — the reason in the right message (CONGEDO, not RESPINTO)": [0, 0],
        "§8.2 — the `dettaglio` in the body (for the log, not for the user)": [0, 0],
        "and the place is freed, observed ON THE WIRE": [0, 0],
        "⛔ the server is still there after the case (B0.5)": [0, 0],
        "§8.2 — a distinct, showable phrase, never a number": [0, 0],
    }
    guasti, morto = 0, False
    # ⛔ A reason counts as «proved» only if ALL its cases pass.
    #    `CHIUSO_DALL_UTENTE` has two — Chrome-style and Firefox-style — and
    #    counting it full because one of the two went well would be mistaking
    #    «one engine out of two» for «the reason is covered».
    motivi_visti, motivi_rotti = set(), set()

    for nome, motivo, verso, strade, spiega, f in casi:
        inizio = registro.finestra() if a.registro else None
        es = await gira_caso(a, registro, inizio, motivo, verso, f)
        motivi_visti.add(motivo)
        # ⚠ The place is looked at by the CASE, with its connection still open
        #   (see `guarda_il_posto`): looking at it from here, with the connection
        #   closed, would find it free even with the farewell ignored.
        prove = esigenze(strade, es, motivo, verso)
        buono = es.provocato and es.errore is None
        for etichetta, esigibile, arrivata, testo in prove:
            if not esigibile:
                continue
            # ⚠ `setdefault`: a new label is added to the summary with its
            #   denominator instead of bringing the bench down — and so whoever
            #   adds a road does not have to remember two places.
            conto = conti.setdefault(etichetta, [0, 0])
            conto[1] += 1
            conto[0] += int(arrivata)
            buono = buono and arrivata
        riga(buono, nome, str(es))
        if not buono:
            motivi_rotti.add(motivo)
            guasti += 1
            print(f"        expected: {motivo:#04x} {MOTIVI[motivo]}  "
                  f"[{verso}]  enforceable roads: {', '.join(strade)}")
            print(f"        {spiega}")
            if not es.provocato:
                print(f"        ⛔ and the provocation NEVER LEFT (stopped "
                      f"in «{es.fase}»): it is not a failed test, it is a "
                      f"test not done")
            for etichetta, esigibile, arrivata, testo in prove:
                if esigibile and not arrivata:
                    print(f"        {ROSSO}⛔{GRIGIO} {etichetta}: {testo}")
            if a.registro and inizio is not None:
                print("        the server log, in that window:")
                for r in registro.righe_nostre(inizio):
                    print(f"          {r[:150]}")
        # ⚠ The roads that are not enforceable are PRINTED anyway: it is the line
        #   that prevents reading «absent» as «broken».
        for etichetta, esigibile, arrivata, testo in prove:
            if not esigibile:
                print(f"        {GIALLO}~{GRIGIO} {etichetta}: {testo} "
                      f"(not enforceable in this case, and it does not enter the count)")
        if es.dettaglio:
            print(f"        detail from the body: «{es.dettaglio}»  "
                  f"⚠ it goes to the log, NOT to the user (§8.2)")

        # ⛔ And the fact goes into the log BEFORE any conclusion: a case that
        #    brings the bench down must have left its own line, or the log would
        #    only tell about the runs that went well.
        a.reg.scrivi({"tipo": "caso", "nome": nome, "esito": bool(buono),
                      "motivo_atteso": motivo, "verso": verso,
                      "strade_esigibili": list(strade),
                      "motivo_visto": es.motivo, "tipo_motivo": es.tipo_motivo,
                      "codice_wt": es.codice_wt, "provocato": es.provocato,
                      "fase": es.fase, "errore": es.errore,
                      "dettaglio": es.dettaglio,
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
        if motivo == SERVER_IN_CHIUSURA:
            inf("⚠ B0.5 does NOT apply to this case: I turned the server off,")
            inf("  and it is the thing proved.  The count does not touch it, and this line")
            inf("  exists so that «skipped» and «passed» do not have the same")
            inf("  face")
            a.reg.scrivi({"tipo": "b0.5-saltato", "nome": nome,
                          "perche": "the case shuts the server down on purpose"})
            morto = True
            break
        conto = conti["⛔ the server is still there after the case (B0.5)"]
        conto[1] += 1
        vivo, perche = await ancora_vivo(a)
        conto[0] += int(vivo)
        if not vivo:
            riga(False, "", f"⛔ THE SERVER NO LONGER ANSWERS after «{nome}»: "
                            f"{perche}")
            guasti += 1
            morto = True
            break

    # ═══ THE PHRASES (§8.2) ═════════════════════════════════════════════════
    #
    # ⚠ This section and the next do NOT depend on the selected cases and do not
    #   touch the server: they run even under a filter, and it is said.  (In B5
    #   the independent sections are skipped because there they really depended
    #   on the cases — here it is not so, and skipping them would hide a free
    #   measurement.)
    if not morto:
        print(f"\n== ⭐ The phrases of §8.2 — «BUDGET_PIENO is not \"error 6\"»")
        inf(f"the client's TABLE is read, not the screen: whether the phrase")
        inf(f"reaches the user's eyes is the user's judgement (I8)")
        try:
            with open(a.pagina, encoding="utf-8", errors="replace") as fp:
                testo = fp.read()
            voci, perche = leggi_tabella(testo)
        except OSError as e:
            voci, perche = None, f"{a.pagina} cannot be read: {e}"
        if voci is None:
            riga(False, "the table can be read", f"⛔ {perche}")
            inf("⛔ and this is NOT «zero phrases»: it is «the table was not")
            inf("   read».  The count below stays without a denominator")
            guasti += 1
        else:
            esiti = giudica_frasi(voci)
            conti["§8.2 — a distinct, showable phrase, never a number"][1] = \
                len(esiti)
            for c, ok, testo in esiti:
                conti["§8.2 — a distinct, showable phrase, never a "
                      "number"][0] += int(ok)
                if not ok:
                    riga(False, MOTIVI[c], testo)
                    guasti += 1
                elif a.frasi:
                    riga(True, MOTIVI[c], f"«{testo}»")
            if all(ok for _, ok, _ in esiti):
                riga(True, "the 15 phrases", f"distinct, without numbers, from the file "
                                          f"{os.path.basename(a.pagina)}")
                inf("(--frasi prints them all)")

        # ═══ THE MEASURED EXCLUSION — AND THE SIGN FLIPS WITH THE TARGET ═══
        #
        # ⛔ Against the GRAFT the grep must say **zero**: the reason is excluded,
        #    and the exclusion is measured instead of asserted.
        # ⭐ Against the PRODUCT it must say **more than zero**: the path exists,
        #    and it is the eighth reason that can be provoked.  ⚠ A zero here would
        #    mean I am measuring a binary **from before** that night, and the
        #    `server-in-chiusura` case would be red for the wrong reason.
        atteso_positivo = b0.profilo(a.bersaglio)["spegnimento"]
        sorgenti = b0.sorgenti_spegnimento(a.bersaglio, a.dentro)
        print(f"\n== ⛔ The exclusion that is MEASURED: SERVER_IN_CHIUSURA (0x0C)")
        inf(f"one looks WHERE THE THING HAPPENS, and on «{a.bersaglio}» that is "
            f"{len(sorgenti)} files — ⛔ not `rcp.c` alone, which is identical "
            f"in the two servers and does not know a process exists")
        quanti, testo = esclusione_misurata(sorgenti)
        if quanti is None:
            riga(False, "the sources can be read", testo)
            guasti += 1
        elif atteso_positivo:
            riga(quanti > 0, "⭐ SERVER_IN_CHIUSURA IS producible", testo)
            if quanti > 0:
                inf("⭐ and indeed those that can be provoked here are EIGHT, not seven: it is the "
                    "first")
                inf("  visible difference between the two servers (fasi/01-filo-nudo.md B7)")
            else:
                inf("⛔ ZERO occurrences on a target that should have them: either")
                inf("  I am measuring a binary from BEFORE the night of 10")
                inf("  August, or the sources are not those it was")
                inf("  built from.  ⚠ It is not «the product does not say farewell»: it is that")
                inf("  I am not looking at the product I believe")
                guasti += 1
        else:
            riga(quanti == 0, "SERVER_IN_CHIUSURA is not producible", testo)
            if quanti == 0:
                inf("⚠ and `FASI.md` §01-filo-nudo B7 listed it among «the eight")
                inf("  reasons this phase can produce»: against the graft")
                inf("  they are seven")
            else:
                inf("⭐ the path now exists in the graft too: it must be removed")
                inf("  from the excluded and a case written for it, or B7 counts one")
                inf("  reason fewer than the true number")
                guasti += 1

    # ═══ THE SUMMARY ═══════════════════════════════════════════════════════
    print("\n    == what this run really looked at")
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            # ⛔ A zero denominator is DECLARED: «nobody looked» and «all
            #    passed» look the same if one keeps quiet.
            print(f"    --  {che:62s} no case triggered it")
            continue
        col = VERDE if buoni == tot else ROSSO
        print(f"    {col}{buoni:3d} out of {tot:3d}{GRIGIO}  {che}")

    motivi_pieni = motivi_visti - motivi_rotti
    print()
    print(f"    ⛔ the reasons: {len(motivi_pieni)} out of {len(motivi_visti)} "
          f"proved in this run, and those THAT CAN BE PROVOKED by phase 1 are "
          f"{len({c[1] for c in TUTTI})} out of {len(MOTIVI)} of §8.2")
    print(f"       the other {len(ESCL)} are excluded, each with its "
          f"why (--elenco), and the exclusion of")
    print(f"       SERVER_IN_CHIUSURA is measured, not asserted")

    if morto and any(c[1] == SERVER_IN_CHIUSURA for c in casi):
        # ⭐ The server died because I asked it to: it is the
        #    `server-in-chiusura` case, and the sections that follow (the phrases,
        #    the measured exclusion) do not touch the server — they run anyway.
        print(f"\n    ⚠ the server is off because this run turned it off "
              f"on purpose: the run is PARTIAL by construction")
        a.reg.scrivi({"tipo": "verdetto", "guasti": guasti, "parziale": True,
                      "perche": "shutdown run"})
        print(f"    --  {a.reg.riassunto()}")
        return 1 if guasti else 0
    if morto:
        print(f"\n    {ROSSO}⛔ the bench stopped: without a server there is "
              f"nothing to measure{GRIGIO}")
        a.reg.scrivi({"tipo": "verdetto", "guasti": guasti, "parziale": True,
                      "perche": "the server died without my asking it to"})
        return 1
    a.reg.scrivi({"tipo": "verdetto", "guasti": guasti,
                  "parziale": bool(a.solo or not a.registro
                                   or a.esclusi_a_mano),
                  "motivi_pieni": sorted(motivi_pieni),
                  "provocabili": len({c[1] for c in TUTTI}),
                  "conti": {k: v for k, v in conti.items()}})
    print(f"\n    --  {a.reg.riassunto()}")
    if guasti:
        print(f"\n    {ROSSO}⛔ B7: {guasti} points do not pass against "
              f"«{a.bersaglio}»{GRIGIO}")
        return 1
    if a.solo or not a.registro or a.esclusi_a_mano:
        print(f"\n    {VERDE}⭐ the measured points pass against "
              f"«{a.bersaglio}»{GRIGIO} — ⚠ and this is NOT «B7 passes»: the run "
              f"was partial")
        return 0
    print(f"\n    {VERDE}⭐ B7 passes: {len(motivi_pieni)} out of "
          f"{len({c[1] for c in TUTTI})} reasons that can be provoked, by BOTH "
          f"roads of §3.1,{GRIGIO}")
    print(f"    {VERDE}      and 15 distinct phrases out of 15 — and the numbers above "
          f"say on what{GRIGIO}")
    return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT GO THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ `--parola` ends up in the process `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` launched by another user
#    during the run prints it in full.
#
# ⭐ The good road already existed in the house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600` file
#    that the launcher writes with `printf` — a shell **builtin**, so not even
#    the writing goes through a process with the password in `argv` — and
#    deletes with a `trap`.
#
# ⚠ And `--parola` was NOT removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse than
#   the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is form
#   **E2** — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--parola` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written
#   in the code is in no command line, and telling it otherwise would be an
#   alarm one learns to ignore.
def parola_dagli_argomenti(a):
    """The password: from `--parola-file` if present, from `--parola` otherwise.

    ⛔ And the three ways of failing are told apart: «cannot be read», «is
    readable by others» and «is empty» have three different cures, and an empty
    file is NOT an empty password — it is «the launcher did not write it»
    (`LEZIONI.md` §1.9).
    """
    percorso = getattr(a, "parola_file", "") or ""
    if percorso:
        try:
            modo = os.stat(percorso).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ the password file «{percorso}» cannot be read: {e}")
            sys.exit(2)
        if modo:
            print(f"   ⚠ «{percorso}» is readable by others (bits {modo:o}): the "
                  f"secret is not protected")
        try:
            with open(percorso, encoding="utf-8") as f:
                parola = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ the password cannot be read from «{percorso}»: {e}")
            sys.exit(2)
        if not parola:
            print(f"   ⛔ the password file «{percorso}» is EMPTY.  It is not")
            print("      «the password is empty»: it is «the launcher did not write it».")
            sys.exit(2)
        return parola
    if any(x == "--parola" or x.startswith("--parola=") for x in sys.argv[1:]):
        print("   ⚠ D12: the password arrived from `--parola`, that is from the")
        print("     COMMAND LINE: it is in `/proc/<pid>/cmdline` and anyone who")
        print("     runs `ps` on this machine sees it.  The run goes on — the caller")
        print("     has not been cured — but it is not a private run.")
        print("     ⭐ The cure: `--parola-file <0600 file>`, as in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B7 — the farewell, verified from the receiving side")
    p.add_argument("--indirizzo", default="192.168.0.2")
    # ⛔ No default that names a target: 7447 is the graft and 7448 the
    #    product, and a default here would mean that «--bersaglio prodotto»
    #    without «--porta» measures the graft while declaring the product.
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--parola` if
    #    both are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--parola-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--dentro", default=QUI,
                   help="the root of the sources from which the exclusion "
                        "of SERVER_IN_CHIUSURA is measured (depends on the target)")
    # ⛔ The server's PID, for the `server-in-chiusura` case only.  Zero means
    #    «they did not tell me», and that case is declared NOT DONE instead of
    #    sending a signal in the dark.
    p.add_argument("--pid-server", type=int, default=0,
                   help="the server's PID, to provoke SERVER_IN_CHIUSURA")
    p.add_argument("--registro", default="",
                   help="the server log: needed for §3.1 point 1 and for the "
                        "client→server direction")
    p.add_argument("--pagina", default=os.path.join(QUI, "01-b11-pagina.html"),
                   help="the file where the table of the §8.2 phrases lives")
    p.add_argument("--solo", default="",
                   help="run only the cases that contain this")
    # ⛔ `--escludi` and not «--solo everything except»: `server-in-chiusura` SHUTS
    #    the server DOWN, so the normal run leaves it out and the launch script
    #    calls it afterwards, with the server restarted on purpose.  ⚠ A filter
    #    that removed a case silently would make «N out of N» true by construction:
    #    here the removed case is printed, and the denominator stays the target's.
    p.add_argument("--escludi", default="",
                   help="does NOT run the cases that contain this, and declares it")
    p.add_argument("--frasi", action="store_true",
                   help="print all fifteen phrases of §8.2")
    p.add_argument("--elenco", action="store_true",
                   help="print the predictions and the denominator, without measuring")
    b0.aggiungi_argomenti(p)
    # ⚠ `--elenco` does not measure and does not need a port.
    if "--elenco" in sys.argv:
        for _az in p._actions:
            if _az.dest == "porta":
                _az.required = False
    a = p.parse_args()
    a.parola = parola_dagli_argomenti(a)
    sys.exit(asyncio.run(principale(a)))
