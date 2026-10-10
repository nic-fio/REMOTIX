# RCP — Remotix Control Protocol, version 1

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio stay, because the new stream is identical (comparison of 30 Sep 2026). User's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

*Written on 9 Aug 2026, before any line of code.*
*Completed on 9 Aug 2026, after the census of §0-bis — still before any line of code.*

> ## 0. ⛔ Why this document exists, and why it comes first
>
> *⚠ The number dates from 10 Aug 2026, finding **R11.18**: four lines of this document
> (§3, §5.2, §7.5, §11.1) and one of `FASI.md` §01-filo-nudo cited «§0» as the load-bearing argument,
> and §0 did not exist — the numbering started from §0-bis. Now it exists, and it does not change a word
> of the text.*
>
> In v1 the referee was **mstsc**: if it drew, it was right. When our server misunderstood
> the RDP specification, someone else's client said so at once, for free.
>
> In V2 client and server are **ours**. If the server emits nonsense, our client will
> gladly accept it — because the same misunderstanding is compiled into both. **Two
> programs written by the same hand that agree with each other confirm nothing**: they repeat the
> same assumption.
>
> Hence the job of this document: **it is the referee**. It does not describe what the code does,
> it establishes what the code must do, and it is written precisely enough to be able to **prove wrong**
> an implementation. If a line here is ambiguous, it is a defect of this file, not
> an interpretation for the programmer.
>
> **What is normative**: everything written with **MUST**, **MUST NOT**, **MAY**. The rest is
> explanation, and does not bind.

---

## 0-bis. ⭐ The census of 9 Aug, and what it closed

*Done at the opening of phase 1, rereading the document with a single question: **do two people who
read it on their own write the same byte?***

The answer was **no**, and not by a nuance. The first draft defined **the frame** (28
bytes exactly) and **the audio datagram** (12), that is the two things that carry the pixels and the sound — and of
the **twenty control, input and clipboard messages** it gave the **name** and a description in words.
The channel that carries the handshake, that is the one phase 1 must write, was the least
specified of all.

| | Before | Now |
|---|---|---|
| message bodies defined byte by byte | 2 of 22 | **26 of 26** (§6, §7) — ⚠ *it said «22 of 22», and the count was from the first draft: the two types added on 9 Aug brought the total to 24, and the **two of the bench function** (§7.5, the night of the 9th) to **26**. Corrected by finding **R1.29**, and it is not pedantry — that cell is **the only proof the document carries of being complete**, and whoever checked it by counting found more* |
| elementary types (numbers, strings, lists) | — | §6.0 |
| how to recognise which channel a stream belongs to | — | §2.5 |
| what the transport demands (windows, streams, migration, 0-RTT) | 3 parameters | §2.3 |
| the port | — | §2.4 |
| what an implementation does after `ERRORE_PROTOCOLLO` | «closes» | §3.1 |
| recovery after an abandoned frame | ⛔ **did not exist** | §5.2 |
| the audio format | «Opus, PCM» | §5.3 |
| rate limiting of attempts | `[?]` in `SPECIFICHE.md` §4.2 | §4.4-bis |

⛔ **And a hole that was not a gap but a design defect**: §5.1 allows the server to
**abandon** a frame with `RESET_STREAM`, and the video is compressed with prediction between
frames. Abandoning one on which the following ones depend leaves the decoder broken **until
a keyframe arrives** — and there was no way either to say that a frame is a keyframe, or to
ask for one. The cure is in §5.2 and costs **zero bytes** in the header: it fits in the values of the
`tipo` field, which were undefined.

⚠ **The closures are marked 🔸 in `DECISIONI.md` §1.5**: they are consequences written by me, not
pronounced by the user, and they are corrected without discussion. What deliberately stays open is
in §12, declared instead of forgotten.

> ### ⭐ Seven lines that came in on **12 Aug 2026**, from sub-phase F2.4 of phase 2
>
> *Found while writing the bench of the video channel **before** the product, and proposed in
> `fasi/rapporti/F2-4-filo.md` with the text ready; applied here by the
> coordinator. ⛔ **None adds a message type, a farewell reason or a field to an
> existing message**: the clause of §9 has been spent since 10 Aug, and every line stays inside that
> prohibition.*
>
> ⚠ **Four are true double readings** — two conforming implementations produce **different bytes for
> the same input** — and **three are derived rules**, which follow from §1 and §3 but which no
> line writes. Confusing them would inflate the count: a derived rule does not make two careful
> implementations diverge, a double reading does.
>
> | | Where | What it closes |
> |---|---|---|
> | ⭐ **P2** | §6.2 `numero` | *double reading, the most serious*: the counter did not say **where it starts**, and §7.1 gives `0` the meaning «no frame» ⇒ `RICHIEDI_CHIAVE(0)` meant **two things** — the implicit sentinel value that §6.0 forbids |
> | ⭐ **P6** | §5.2 | *double reading, and it bites in phase 2*: a **delta at the opening** conformed to every line, and the client **had no way to notice** — no hole in the `numero` values, and the decoder raises no errors |
> | ⭐ **P5** | §6.2 `largh.`/`altezza` | *double reading*: *«it is always that of the canvas»* **describes** and does not command, and no line said what **the receiver** of a different size does — close or rescale |
> | ⭐ **P3** | §2.5 row `0x03` | *double reading*: §2.5 forbids by name control on a unidirectional stream and audio on a stream, but **for video it did not say which stream it lives on** |
> | **P1** | §2.5 row «video» | *derived*: for the **receiver** it follows from §1 and §3; for the **sender** it followed from nowhere — and it is invariant **I3** left without a line on the wire |
> | **P4** | §6.2 | *derived*: a **FIN before the 28 bytes** is not a short frame, it is a length that does not add up |
> | ⭐ **P7** | §11.1 | *found by the **mechanical referee***, not by a rereading: the recording did not carry **how the stream was closed**, and without that byte an abandoned frame and one truncated by mistake are identical — form **E8**, back in through the window |
>
> ### ⛔⛔ And two hours later, TWO OF THESE SEVEN WERE WRONG — corrected the same day
>
> *And it was not a rereading that found them: they were found by **whoever had to enforce them**, that is the agent that
> was propagating the seven lines to the two referees. Applying a rule is a way of reading it that rereading it
> is not.*
>
> ⛔ **P5 killed a healthy session.** The line wrote *«MUST be the canvas granted in `SESSIONE`»*, ⚠ but §7.1 has `ADATTA_TELA`, and `TELA` answers with *«the canvas in force **after** this message»*. ⇒ `SESSIONE` grants 1920×1080 · the user drags the window · the client sends
> `ADATTA_TELA(1280,720)` · the server answers `TELA(ADATTATA…)` and captures at that size · the
> frame carries `largh. = 1280` · ⛔ **and the client rejects it and closes**. A server conforming to §7.1
> killed by a client conforming to §6.2 — and it is **exactly the scene that §7.1 protects** with its
> exception 4: *«the user who drags a window badly must not lose the session»*. ⭐ The cure is
> **one word**: «the canvas **in force**» in place of «the canvas granted in `SESSIONE`».
>
> ⚠ **And P2 put back into circulation the value it had just reserved.** The arithmetic of `numero` is
> **modulo 2³²** and §6.2 declares that a session can last more than one wrap of the counter: at the wrap,
> `0xFFFFFFFF` goes to **`0`**, which P2 had reserved two hours before, and no line said to
> skip it. Cured: **from `0xFFFFFFFF` it goes to `1`**.
>
> ⇒ ⭐ **Five lines of seven were right, two were not — and the cost of finding out was writing their
> bench.** It is moment 1 of `PIANO.md` §0.4 working in the direction nobody expects: the
> bench did not find a defect in the product, it found **a defect in the referee**.

⛔ **And the window to do it IS CLOSED**: §9 forbids adding message types within a
major version, and that prohibition protects the existing implementations. **Now they exist.** From here
on this document is touched **only** as §9 says, with no discounts.

> ⚠ *This line said* «⭐ **And the window to do it is now** … that prohibition protects the existing implementations, and **today none exists**» — *and §9 said the same thing with the
> same words. It was true until 10 Aug 2026; the first byte was written that day, and the
> two lines were left behind. **Whoever had read them afterwards would have added a message type
> with the written blessing of the referee**, that is the breach that §12 declares it has closed.
> Corrected on 11 Aug 2026, finding **R12C.2**.*
>
> ⛔ **The implementations of RCP/1 that exist, counted on 11 Aug 2026** `[M]` (`wc -l`,
> `md5sum`):
> · `src/rcp.c` + `rcp.h` — `[M]` **12 Aug 2026: 2,764 / 239 lines** (they were 2,592 / 197 on the 11th);
> · `banchi/rcp/rcp.c` + `rcp.h` — **identical byte for byte** (`md5` `6d858886…` and `62415feb…`,
>   they were `1adce15b…` and `0458f154…`);
>
> ⚠ *The numbers grew because of the cure of `DECISIONI.md` §1.10 — the PAM check off the single
> thread — and ⛔ **the wire has not changed by one byte**: this is a **census** cell, not a
> normative line, and it must be realigned when the code grows or it becomes a measurement that describes
> yesterday's code. Realigned on 12 Aug 2026, on a report from the agent that made the cure.*
>   ⚠ *`rcp.c` said **2,566 lines** and `md5` `cb7af778…`: they changed late in the evening of 11
>   Aug 2026, for the log line of the **attach slot left** on the farewell path — the cure
>   is in the code, commented. ⛔ And the two numbers are updated **together**, or the line that declares
>   the identity of the two copies becomes a promise nobody checks: what enforces it is the
>   `Makefile`, which compares `src/` with `banchi/rcp/` and stops if they diverge.*
> · `banchi/01-b3-cliente.py` — **the second reader**, in another language;
> · `src/pagina.html` — the third, in JavaScript;
> · and two that read the format without speaking it: `banchi/01-b4-validatore.py` (the mechanical referee)
>   and `banchi/01-b11-pagina.html`.

---

## 1. The model, on one page

```
        CLIENT                                            SERVER
          │                                                 │
          │  ⓪  the PAGE, over TCP       port 7447           │
          │◀──── and here the user sees the warning, once ───│
          │                                                 │
          │  ①  WebTransport over HTTP/3   UDP 7447          │
          │────────────────────────────────────────────────▶│
          │  ② the BROWSER checks the fingerprint that       │
          │     the page declared to it                      │
          │                                                 │
          │  ③  CIAO  (version, client capabilities)         │
          │────────────────────────────────────────────────▶│
          │◀──── ECCOMI (version, server capabilities) ──────│
          │                                                 │
          │  ④  CREDENZIALI                        ── PAM ──▶│
          │◀──── AMMESSO  /  RESPINTO(reason) ───────────────│
          │                                                 │
          │  ⑤  ATTACCA (canvas, layout, view)               │
          │◀──── SESSIONE (state, granted canvas) ───────────│
          │                                                 │
          │        ══════ from here the channels flow ══════ │
          │◀═══ video: one stream per frame ════════════════ │
          │◀═══ audio: datagrams ═══════════════════════════ │
          │═══▶ input: one reserved stream ═════════════════ │
          │◀══▶ control · clipboard ════════════════════════ │
```

Three things this drawing says and that must be read:

1. **the server proves who it is before the password leaves** — invariant I3 applied
   to the order (`SPECIFICHE.md` §4.1);
2. **authentication precedes attaching**: whoever is not admitted does not even name a session;
3. **the canvas is agreed at attach**, and from there it does not change while the client stays
   (`SPECIFICHE.md` §6.1).

⛔ **The order of the five steps admits no permutations.** A message that arrives in a state in which
it is not expected is `ERRORE_PROTOCOLLO` (§3). It is trap 1 of `LEZIONI.md` §4, where every permutation
was punished with a different error and nobody said «you got the order wrong»: here it is said.

---

## 2. The transport

**WebTransport over HTTP/3**, that is **QUIC** version 1 (RFC 9000) with **TLS 1.3 mandatory**. There
is no cleartext mode, and RCP never flows over TCP.

> ### ⭐ Changed on 9 Aug 2026 — and the protocol did not lose a line
>
> `DECISIONI.md` §1.6: **no dedicated clients, the client is the browser**. A page cannot
> open a bare QUIC connection, but **WebTransport gives it the same bricks** on which §5.1 had
> been designed: independent unidirectional streams, the abandonment of a stream, datagrams,
> connection migration.
>
> ⭐ **What changes is all in this chapter and in §4.1**: how the connection is reached and
> who trusts whom. **The messages, the framing, the channels and the bodies do not change by one byte** —
> §3 and §5 onwards hold identically.
>
> ⚠ **And the server takes on a job**: before it listened to QUIC and that was all, now **it also serves the
> page**. They are two listeners with the same port number — **UDP** for HTTP/3 and WebTransport,
> **TCP** for the first load — because a browser that opens `https://…` starts over TCP and moves to
> QUIC only if the server announces it with `Alt-Svc`.

### 2.1 How the pieces of QUIC are used

QUIC is not «TCP that goes faster»: it carries four things that this protocol uses
deliberately, and that must be used **instead of** reimplementing them (`SPECIFICHE.md` §2 point 3,
*«depend, do not rewrite»* — ⚠ *this line cited a «§2.3» that does not exist in `SPECIFICHE.md`:
§2 has no subsections. Corrected on 10 Aug 2026, finding **R11.18***).

| Piece of QUIC | What it is for here |
|---|---|
| **independent streams** | a late frame does not block the next one: head-of-line blocking is per stream, not per connection |
| **`RESET_STREAM`** | ⭐ **abandoning a frame** that is no longer needed, instead of sending it late |
| **datagrams** | audio, which is small and prefers losing a packet to waiting for it |
| **connection migration** | the phone moves from WiFi to mobile network without the session noticing |
| **congestion control** | the measure of how much the line carries, which in v1 had to be worked out by hand |
| **idle timeout** | the 30 seconds of silence of `SPECIFICHE.md` §5.3 |

### 2.2 Mandatory parameters

| Parameter | Value | Why |
|---|---|---|
| `max_idle_timeout` | **30 s**, set by the server | it is the silence clock: once it expires, the client is detached |
| datagrams | **MUST** be enabled on the HTTP/3 connection | audio |
| ALPN | `h3` | ⛔ the browser negotiates it, not us: a page does not choose the ALPN |
| **the session address** | `https://<host>:<porta>/rcp/1` | ⭐ **this is where the identity of the protocol lives**, in place of the ALPN: the number after the slash is the **major version** |

⛔ **The server MUST NOT accept a WebTransport session on a different path.** An unknown path
is refused with the HTTP refusal status, and is written in the log: it is §3 applied to the
first byte, even before RCP begins.

⚠ **Why the version is in the path and not only in `CIAO`.** With the ALPN the refusal arrived
before spending a connection; here the ALPN is `h3` and is not ours, so the most upstream place in
which we can say «I do not speak this version» is the path. ⛔ The version check in `CIAO`/`ECCOMI` (§9)
remains mandatory all the same: **the path does not replace it** — a path can
be typed by hand, and a check that can be bypassed by typing is not a check.

⛔ **And the two MUST coincide**: a `CIAO(versione=2)` on `/rcp/1` is `VERSIONE_INCOMPATIBILE`, not
a negotiation to resolve. An unknown path is refused with **404**.

> ⚠ *The two lines above are from the evening of 9 Aug 2026, finding **R1.24**.* The document
> said that the path «does not replace» the check, and **did not say that the two had to
> agree**: §9 makes the server choose the highest version that does not exceed that of `CIAO`,
> so a `CIAO(2)` on `/rcp/1` produced three outcomes all defensible — `ECCOMI(2)`,
> `ERRORE_PROTOCOLLO`, `VERSIONE_INCOMPATIBILE`. And the HTTP status of the refusal was not written: 404,
> 400 and 421 were all lawful, and the page does not tell them apart.

⛔ **There MUST NOT be an application-level heartbeat.** The QUIC idle timeout already does that
job, and a second mechanism would produce two truths about the same fact.

### 2.3 ⭐ Stream credit, and what we can no longer demand

*Added on 9 Aug 2026 and rewritten the same day, after `DECISIONI.md` §1.6.*

⛔ **The first draft of this paragraph dictated the QUIC transport parameters to the client** —
how many streams, how much window, no 0-RTT, no `disable_active_migration`. **With a browser
it cannot be done: it chooses those parameters**, and no line of this document changes them for it. What
stays normative is what falls to **us** — the server — and what must be **measured instead of
demanded**.

| | |
|---|---|
| **the server MUST grant credit** to the client for its unidirectional streams: at least **16** available at any moment — ⛔ **that is at least 19 declared at the QUIC level** (see the box) | the client opens one input stream and one for each clipboard transfer. If the credit ran out, **input would not leave at all** and the symptom would be «the desktop does not respond» |

> ### ⛔ The 16 are **available to RCP**, not declared on the wire — and the difference is three
>
> *Added on 11 Aug 2026, finding **A** of point 4 of the session. The line above said
> «at least 16» and that was all: ⛔ **whoever implemented it to the letter wrote `initial_max_streams_uni = 16`
> and conformed to the document while violating its reason.** It is defect **B-12**, found
> in the product on the night of 10 Aug and cured there — and the referee did not say it.*
>
> ⛔ **WebTransport has no credit of its own.** In drafts ≤ 07 every unidirectional stream of
> WebTransport **is** a unidirectional QUIC stream, on the same counter as HTTP/3. And HTTP/3
> takes **three** of them as soon as the connection is born — its control stream and the two of QPACK —
> and ⛔ **never closes them**.
>
> ⇒ **16 declared = 13 available to RCP**, and the three missing streams are lost in silence: the
> symptom is not an error but *«the desktop does not respond»*, that is the symptom this line exists to
> prevent.
>
> | | |
> |---|---|
> | what the server **declares** in `initial_max_streams_uni` | ⛔ **at least 19** |
> | what remains to RCP after the three of HTTP/3 | **16**, which is the normative number |
> | ⚠ and the count **is not believed, it is measured** | the transport probe counts the unidirectional streams the peer has really opened and judges `dichiarati − contati ≥ 16`. `[?]` **on a browser the three could be more** — a *grease* stream, for instance — and nobody has measured it |
>
> ⚠ **And the right number is 19 even when it looks generous**: the two words that decide in this
> line are **«available»** — not «declared» — and **«at any moment»**. The reading that saves the
> 16 makes both of them dead words.
| **the server MUST withstand the refusal to open a stream** instead of considering it a fatal error | video consumes **one stream per frame**: at 60 per second, the credit the browser grants is consumed fast |

> ### ⛔ «Credit is renewed as the streams close» — **FALSE, and measured**
>
> *13 Aug 2026, phase 3. The line above ended like that, and whoever read it drew a
> guarantee from it: close the streams and the room comes back. ⛔ **It does not necessarily come back.***
>
> ⛔ **The renewal of credit is THE PEER'S POLICY, not a consequence of closing.** Closing a
> stream gives nothing back by itself: the limit rises **only** when the peer decides to send a
> higher `MAX_STREAMS`, and **when** it sends it is its decision. `[M]` **with the peer's renewal
> switched off, the credit stays still even with all streams closed.** ⇒ The old line did not describe the
> protocol: it described a kind peer.
>
> ⇒ **What stays normative, and does not change**: the server **MUST withstand the refusal** to open a
> stream (line above) and **MUST** throw away the frame — never a keyframe (line below). ⛔ What
> falls is the **reassurance**: no code is written that *waits* for the room counting on the renewal,
> because the renewal is not ours and may not arrive.
>
> ⛔⛔ **And it is NOT written that the product falls over under low credit: it is not measured.** *A run of 13
> Aug produced a `STREAM_LIMIT_ERROR`, and for a few hours it looked like a defect of the product.
> It was not: the **bench** announced the credit **after** the handshake — something RFC 9000 §4.6
> forbids — so the `6` **was never announced on the wire**. The server had **128 slots
> granted** and opened **14**. ⇒ **`ngtcp2` violated nothing, and there the product has no
> defect.** What holds from that day is the line above, which is another matter.*
>
> ⭐ **And while looking for the false defect a real one came out, and it was worse: `B-18`.** One of the three
> paths of abandoning a delta — precisely the one **for lack of room** — **did not switch on the
> keyframe request**. ⛔ **A single delta skipped for exhausted credit wrecked the picture for
> good and in silence**, and the chain of silence is this: the frame was never sent
> ⇒ the `numero` **is not consumed** (§6.2) ⇒ **no hole** in the sequence ⇒ the client has nothing
> to notice and **cannot ask for the keyframe** ⇒ and with an infinite GOP none arrives any more on its
> own. ⇒ **This is the reason the line below obliges the server to produce the keyframe by itself**:
> in this case the client has no way of asking for it.
| ⛔ **and when credit is lacking the frame is thrown away — but NEVER a keyframe** | waiting for a free slot is a queue, and every queue **buys smoothness and sells responsiveness** (`SPECIFICHE.md` §3.2). An old **delta** is no longer needed: a new one is already arriving. ⛔ A **keyframe** instead is waited for, because it is the only thing that puts the decoder back on its feet (§5.2). And in both cases **it is written in the log** |

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.9**, and the sequence that broke it is this.*
> The line gets worse, the server abandons a delta and — as §5.2 requires — immediately prepares a
> **keyframe**. At that moment the credit is exhausted, because it is the same condition that produced
> the abandonment. The old line ordered to **throw away**: the frame thrown away was the keyframe, which
> §5.2 forbids abandoning with a ⛔. Two opposite normative lines, and neither cited the other.
>
> ⚠ And the case closed back on itself: the client asks for a keyframe, the server produces it, the
> credit is still lacking, it throws it away again — **frozen screen, and no line in the log saying
> why**, because the log obligation of §5.1 speaks of *abandonment* and there the stream had never
> been born. Now the obligation covers both cases.
| **the server MUST NOT offer 0-RTT** | 0-RTT data can be **replayed**, and the second message is `CREDENZIALI`. The gain is one network round trip on a session that lasts hours |
| **the server MUST NOT disable migration** | it is the reason QUIC was chosen (`SPECIFICHE.md` §8.4): the phone that moves from WiFi to mobile network |

`[?]` **How many streams per second each browser really withstands nobody knows**, and it is not read:
it is measured. ⚠ It is the form of defect a short bench **does not see** — it works for the first seconds and
stops afterwards (`LEZIONI.md` §1.4) — and that is why §11 has a dedicated bench, which keeps the
session alive **beyond the first 256 frames**.

### 2.4 🔸 The port

**7447**, and they are **two listeners with the same number**: **UDP** for HTTP/3 and WebTransport,
**TCP** for the first load of the page. It is the default value, and it **MAY** be changed
by the server configuration: the user types `https://indirizzo:7447` in the browser, and then user
and password in the page.

> ⛔ **Corrected on 9 Aug 2026 by measurement S1** — this line said: *«the server MUST announce `Alt-Svc: h3=":7447"` on the TCP response, or the browser will never move to QUIC»*. **It is false**, and it
> was mine: **WebTransport does not use `Alt-Svc` at all** — zero occurrences in the three specifications, with
> a positive control `[S]`. A WebTransport session opens **its own** HTTP/3 connection towards
> the address it is given, without discovery and without upstream negotiation.
>
> ⭐ **And it removes a danger I had declared**: the silent fallback to TCP — «the page opens and the desktop never arrives» — **cannot happen**, because there is no fallback
> to make.

⚠ **TCP serves only to deliver the page**, and HTTP/1.1 is enough for it. From there on the browser opens
the WebTransport session on its own, over UDP.

⚠ Chosen on 9 Aug 2026 after checking that it is free in `/etc/services` of Debian Trixie `[M]`.
`[?]` **The IANA registration has not been checked**: if one day a registered number were needed,
this line is changed without touching anything else.

### 2.5 ⛔ The streams: who opens what, and how they are recognised

*This paragraph closes the most insidious hole of the census: whoever receives a unidirectional
stream must know **what** is inside before reading it, and it was not written
anywhere.*

| Stream | Who opens it | How many |
|---|---|---|
| **control** — the **first** bidirectional stream of the session | the client | only one, for the whole session |
| **video** — unidirectional | the server | one **per frame**, ⛔ and **none before having sent `SESSIONE`**. ⚠ The prohibition binds **the sender**: the receiver cannot measure it on the order in which things reach it, because the control channel and the stream of the frame are **two independent QUIC streams** and nothing orders their delivery (§6.2). ⇒ The client declares `ERRORE_PROTOCOLLO` **only** if it has not yet sent `ATTACCA`: §4.5 makes `SESSIONE` the answer to `ATTACCA`, so there the server **cannot** have sent it, and the client knows it **without looking at the network**. ⛔ If `ATTACCA` has left and `SESSIONE` has not yet arrived the client **MUST NOT close**: it **holds back** the frame and writes it in the log, and judges it when `SESSIONE` arrives — which necessarily arrives, because the control channel is reliable and ordered and §4.5 forbids the server to answer with a silence. ⚠ And invariant **I3** stays whole: whoever has sent `ATTACCA` has already passed through `AMMESSO`, that is through the validator |

> ### ⛔ The line above was rewritten on **13 Aug 2026** — finding **P20**
>
> *It said:* «*whoever receives one before closes with `ERRORE_PROTOCOLLO`*». ⛔ **And «whoever receives one before» is a substitute quantity**: the receiver has nothing to measure other than the order in which its
> own network layer delivers events to it, and the two streams are independent. ⇒ It was enough to
> **lose the packet that carries `SESSIONE`** for a conforming client to kill a session in
> which the server had done everything right — **I1 broken because the line loses packets**, that is the
> condition I1 exists to protect.
>
> ⚠ *It is the **sixth** of the family* **P8 → P11 → P13 → P14 → P19 → P20** *(`LEZIONI.md` §1.13, and
> ⭐ the **seventh** is of 24 Aug 2026 — see the box just below). And
> even the first cure proposed — «only if, when the frame arrives, the bytes of `SESSIONE` have not yet arrived» — remained a substitute: it moves the measurement from the wake-up of the coroutine to the bytes, and
> **the bytes are delayed by the network**. It would have been the seventh draft.*
>
> ⭐ **The true quantity is what the client has sent ITSELF** — `ATTACCA` — and it is the general form
> of the `numero` field of P14: **local, monotonic, independent of delivery**.
>
> ### ⭐⭐ **P21** — *24 Aug 2026, phase 9*: the seventh, and this time the family struck **the server**
>
> ⛔ The first draft of the cure *«declare dead a line that loses too much»* used
> ngtcp2's **`pkt_lost / pkt_sent`** within a window: two counters **local to the sender**, which
> seemed to respect the family's rule to the letter.
>
> ⛔⛔ **And it ordered the two cases backwards.** `[M]` A line that **holds** for ten minutes (jitter
> 40±20 ms, 2 % of true loss) declared **512‰** of it; one that **does not hold** **123‰**. ⇒
> No threshold could separate them. The reason is the same as always: **ngtcp2 counts an overtaken
> packet as lost**, so on a line that reorders, that fraction **measures the reordering**,
> not the loss. It was a **substitute quantity**, and it did not show because it is local and monotonic.
>
> ⭐ **The true quantity is what the server knows it has NOT done**: *how long a frame has not
> left although it has some to send* — the **output stall**. `[M]` It separates the two cases by
> sixty times (0.50 s against 30.06 s), and it is local, monotonic and independent of delivery as
> the family asks.
>
> ⇒ ⚠ **The lesson P21 adds to the six before**: *«local and monotonic»* **is not enough**. A
> quantity must be tested **on the two known extremes**, and must **order them in the right direction** — if it does
> not, it is not a calibration to redo: it is the wrong quantity (`LEZIONI.md` §1.33). ⛔ And it was not found
> by a rereading: it was found by the **test client** on its first run against a server that
> really sends.
| **input** — unidirectional | the client | **only one**, opened ⛔ **after having received `SESSIONE`** and kept open |
| **clipboard** — unidirectional | both | one **per transfer** |

⛔ **The client MUST NOT open bidirectional streams beyond 0. The server MUST NOT open bidirectional
streams.** Whoever receives one closes with `ERRORE_PROTOCOLLO`.

> ### ⛔⛔ Before reading: **the «first two bytes» are not the first bytes of the stream** — finding P18
>
> *12 Aug 2026. Found by the **test client**, on its first live run, and not by a
> rereading: `[M]` the run ended red with «canale di controllo mai aperto», and the cause was that
> the client applied this line **to the letter**.*
>
> ⛔ On WebTransport every stream carries a **preamble**: the stream type (`0x54` for
> unidirectional, `0x41` for bidirectional, in variable-length encoding — on the wire `40 54` and `40 41`)
> followed by the **session number**. ⇒ Whoever reads the «first two bytes» **of the stream** derives
> channel `0x40`, which is none of the five, and **closes every frame with
> `ERRORE_PROTOCOLLO`**.
>
> ⇒ **The two bytes are the first of the RCP payload**, that is what remains **after** the WebTransport
> preamble, which the transport layer consumes and does not deliver.
>
> ⚠ **And this is the silent defect that §0 of this document exists to prevent.** The server and the
> page agreed **because the same hand wrote them**: neither of the two read this
> line, and the line was false. ⭐ What found it was **the only reader that read RCP.md without
> looking at the code** — that is precisely the piece of referee that `PIANO.md` §1.1 says it
> bought in place of `mstsc`, and that here paid back its own cost on the first run.

⭐ **How the channel is recognised**: one reads the **first two bytes of the RCP payload** — that is what
remains **after** the WebTransport preamble (§2.4), which the transport consumes — and they are in any
case a `tipo` field (§6). The high byte says the channel:

| High byte of `tipo` | Channel | What follows |
|---|---|---|
| `0x00` | control | the framing of §6.1 — and on a unidirectional stream it is `ERRORE_PROTOCOLLO`: control lives only on the **first bidirectional stream of the session** (§4.2) |
| `0x01` | input | the framing of §6.1, one message after another |
| `0x02` | clipboard | the framing of §6.1 |
| `0x03` | video | the 28-byte header of §6.2, **without** framing — ⛔ and **only on a unidirectional stream opened by the server**: a `0x03` on the control channel is `ERRORE_PROTOCOLLO`, as is a `0x00` on a unidirectional stream |
| `0x04` | audio | ⛔ only on datagrams (§6.3). On a stream it is `ERRORE_PROTOCOLLO` |

⛔ A high byte other than these five is `ERRORE_PROTOCOLLO`. And a channel used **in the wrong
direction** — a `0x01` that arrives from the server, a `0x03` that arrives from the client — is one in its
turn.

> ⛔ *Corrected on 10 Aug 2026, finding **R11.9**: the `0x00` row said «control lives only on **stream 0**», and it was the remainder of the bare-QUIC draft that §4.2 had already removed on the
> evening of 9 Aug (finding R1.5). Finding R1.5 named **this section too**, and the cure
> had been applied to only one of the two places.*
>
> ⛔ **The channel is recognised by the high byte of `tipo`, never by the stream number**, and the second
> answer to the same question had remained in here — that is in the section that §0-bis presents as
> the cure of the «most insidious hole». Whoever implemented §2.5 to the letter wrote a receiver that
> looks for the control channel by number, and the diagnosis that came out was *«the client does not open the channel»* **while the client had opened it**. ⚠ *The same word survived in the table of
> §5, and it was removed there together with this one.*

---

## 3. ⛔ The rigor rule

> **An RCP implementation that receives something it does not understand MUST close the connection with
> `ERRORE_PROTOCOLLO` and write in the log what it did not understand. It MUST NOT ignore it, MUST NOT
> guess, MUST NOT carry on.**

It applies to: an unknown message type, a length that does not add up, a field out of range,
a message arrived in the wrong state of the machine, a channel used in the wrong direction.

**Why it is written as the first rule and not among the notes.** A lenient parser is very convenient the
first day and poisonous forever: if the server starts emitting a wrong field and the client
politely ignores it, the defect **does not show** — and since there is no longer someone else's client to
protest (§0), nobody will see it until it produces a distant and incomprehensible symptom.

It is `REVIEWER.md` §5 applied to the wire: *«the leniency that hides is exactly what you must remove»*.

⚠ **The exceptions are eight, and they are all here.** Outside this list none are invented:

| # | Where | What is tolerated, and why |
|---|---|---|
| 1 | §4.3 | an unknown **capability** — name or value — is ignored: it is the mechanism by which future versions understand each other. ⚠ It is ignoring *an offer*, not *a command* |
| 2 | §6.3 | a corrupted or too short **datagram** is discarded instead of closing: it is unreliable by definition, and punishing it would punish the network |
| 3 | §7.1 | after a canvas change, **one second of grace** on the old coordinates: it is the only moment in which the two sides legitimately have two truths |
| 4 | §7.1 | an **out-of-limits** size in `ADATTA_TELA` is refused with `TELA(MISURA_FUORI_LIMITI)` instead of closing — ⭐ since 1 Oct 2026 only **below the minimum**: above the maximum it is granted reduced (§4.5). ⚠ *It was not declared (finding **R1.10**): the same out-of-range value kills the connection in `ATTACCA` and not in `ADATTA_TELA`, and the difference is intended — **the user who drags a window badly must not lose the session*** |
| 5 | §5.2 and §7.4 | a `RICHIEDI_CHIAVE` repeated within 200 ms **may be ignored**, and an `APPUNTI_CHIEDI` out of time **is served** instead of being an error. ⚠ *These were not declared either (finding **R1.15**)* |
| 6 | §6.2 | after a canvas change, frames are tolerated that carry **a size that has been in force since the queue started to drain**, and the tolerance ends when **the first keyframe at the new size** arrives (§5.2), not by the clock. They left before the `TELA` arrived, and the streams are independent. ⚠ *It is exception 3 written for the other direction of the wire — that one covers the coordinates going up, this one the frames coming down. Without it, the cure of **P5** of 12 Aug 2026 makes the client close in front of a server conforming to §7.1* |
| 7 | §2.5 | a **video stream arrived before `SESSIONE`** when the `ATTACCA` has already left **does not close**: it is **held back** and judged when `SESSIONE` arrives. ⚠ *The order between two QUIC streams is not that of the wire, and one lost packet was enough for a conforming client to kill a healthy session — finding **P20*** |
| 8 | §6.2 | a frame whose size **no canvas has ever had** **does not close** as long as there is an **`ADATTA_TELA` without answer**: it is **held back** and judged again when the `TELA` arrives, successful or refused. ⚠ *Because §4.5 allows the server to grant a canvas **different from the one asked** — finding **P21*** |

> ⛔ **Rows 7 and 8 came in on 13 Aug 2026, finding P22 — and they were already commanded elsewhere.**
> §2.5 and §6.2 ordered those two tolerances while **this list declared that the exceptions
> were six and that outside here none are invented**. ⇒ A client written by reading §3 **closed**
> precisely the healthy sessions that the other two lines saved.
> ⚠ *It is the second time this list has been left behind: the first was **P12**, on 12 Aug. ⭐ Hence
> the rule: **whoever writes a tolerance elsewhere adds the row here at the same moment**, or the two
> halves separate — and it is the form this document pays most often.*

⛔ **And every tolerance must be written in the log.** A silent tolerance is indistinguishable from a
defect, and it is precisely the leniency this section exists to remove.

### 3.1 What «close» means, in bytes

*Added on 9 Aug 2026: «closes the connection» admitted at least three different implementations,
and two of them make the reason disappear exactly when it is needed.*

Whoever detects the violation, **in this order**:

1. **MUST** write in the log *what* it did not understand — the type received, the length, the
   state it was in. Not «protocol error»;
2. **MUST** send `CONGEDO` (§8) with the reason, on the control channel, **if the control
   channel is still usable**;
3. **MUST** close the **WebTransport session** with the application error code equal to the
   **reason code** of §8.2.

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.4**.* This line said «the QUIC connection with an application-type `CONNECTION_CLOSE`». **A page cannot do it**: the API exposes the
> closing *of the session*, with its own code, not that of the HTTP/3 connection underneath — which
> may carry other things. They were two different planes, and §8.1 imposed the rule on the client too, that is on whoever
> does not have the API. One programmer closed the session and declared the rule fulfilled; the other
> looked for the connection API, did not find it, and left point 3 unimplemented — **and was
> as conforming to the text as the first**.

⭐ **The third point is the one that saves diagnoses**: if the farewell does not arrive — because the stream
was broken, because the message was unreadable — the reason travels all the same, inside the closing
of the session. In v1 the server wrote «farewell to the client» and the client read «network error»
for **three phases** (`LEZIONI.md` §1.7): here the two sides have two roads to tell each other the same thing, and
the acceptance test of §11 checks **from the receiving side** that at least one of the two has arrived.

⚠ Code **0** means «closing without reason» and **MUST NOT** be used: every closing has
a reason from §8.2.

---

## 4. The handshake

### 4.1 Even before: the certificate

> ### ⭐ Rewritten twice on 9 Aug 2026 — and the second time by a measurement
>
> **First draft**: four steps the client had to implement — compute the fingerprint,
> compare it with the remembered one, stop if it changes, accept silently if there is none.
>
> **Second**: «the browser already does those steps, it is no longer our code».
>
> ⛔ **Third, and it is the good one**: for loading the **page** it is true, for the
> **WebTransport** session it is not — the user's exception does not cover it on Chrome or on Firefox `[R]`
> (measurement **S1**, `web/rapporti/S1-certificato.md`). So the certificate of the session
> **is declared**, and the place to declare it is the page.

**What stays normative, and it is all on the server side:**

| | |
|---|---|
| **the key** | **MUST** be **ECDSA P-256**. ⛔ Not Ed25519 and **never RSA**: P-256 is the only one that also keeps open the road of `serverCertificateHashes` `[S]`, and a key chosen today for convenience would close that door without anyone noticing |
| **the generation** | the server generates it at installation, and keeps the private key with permissions `0600` |
| **the name** | the certificate **MUST** carry as `subjectAltName` the address on which the server answers — name or IP address. ⚠ A browser that finds a `SAN` that does not match shows **a different warning**, and some do not even offer the click to proceed |
| **the real certificate** | if the administrator installs one issued by an authority, the server **MUST** use it and **MUST NOT** regenerate its own. It is the road without warnings (`SPECIFICHE.md` §4.1) |

⛔ **And two certificates, not one** — the rule is in §4.1-bis, and it must be read before writing the
server.

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.2**.* Here it was written, with a ⛔, that *«the page and the WebTransport session must present **the same** certificate»*, while §4.1-bis
> imposes **two** of them with another ⛔. Two normative lines that contradict each other, and neither cited
> the other: whoever obeyed this one served the page a certificate that the other obliges to
> regenerate every fourteen days, **making the warning reappear every two weeks** — that is
> the symptom §4.1-bis declares as the consequence of the opposite mistake.
>
> ⭐ **The fact that unties the knot** was already in the house, in `web/rapporti/S1-certificato.md`: with
> `serverCertificateHashes` the browser **does not look at the exception**, it looks at the fingerprint. So the two
> certificates must not be «the same» — they must be **declared in two different ways**, and
> the user sees only one warning, the page's.

`[?]` **What remains to be measured is only Safari**: whether there the exception is enough by itself, that is whether
publishing the fingerprint can be done without. ⚠ *The general question that stood here — «does the exception cover WebTransport?» — **already has an answer for two engines out of three**, and it is no: the box at the top
of this section gives it. Keeping it open made people plan a measurement already done (finding **R1.25**).*

### 4.1-bis ⛔ `serverCertificateHashes` — **the normal road**, not a safety net

*Promoted from safety net to main road on the evening of 9 Aug 2026, after measurement S1:
it was not an alternative, it is **the only mechanism** browsers expose for a server without a
domain.*

> ⛔ *Corrected on the night of 9 Aug 2026, finding **R4.4** of the review of the phase 1 bench.*
> The row «who stays out» said *«`[S]` WebKit does not implement it: on Safari, iPhone and iPad the road is the exception»*. **It has been false since October 2025**, and `STUDI.md` §web §3.1 and `DECISIONI.md` §1.7 had
> already been corrected **on the same 9 Aug**: this document had not.
>
> ⛔ **And the damage was of the kind that makes no noise, because this file is the referee.** Whoever
> read it to the letter wrote the branch *«on Safari the fingerprint is not needed, one goes by exception or by real certificate»* — and wrote it **conforming to the specification**, while whoever read `STUDI.md` §web
> published the fingerprint for all three. Two diverging implementations, both in the right.
> ⚠ And a bench that had applied the criterion *«a library that works with Chrome and not with Safari is not a library that works»* would have **failed both candidates**.

| | |
|---|---|
| **what it is** | the SHA-256 fingerprint of the session certificate travels **inside the page**, and the browser accepts without warnings. It is our trust model, made with the lever browsers offer on purpose. ⛔ **Of the DER bytes of the certificate** — not of the public key and not of the PEM bytes. ⚠ *DER was missing here and was in `DECISIONI.md` §1.5 row 7 since 9 Aug (finding R1.14): aligned on the night of 10 Aug 2026, and it is the same damage as then — whoever computes the fingerprint on the wrong envelope gets a comparison that **never matches**, with the symptom «WebTransport does not connect» and no error naming the fingerprint* |
| ⭐ **and it is no longer `[S]`** | `[M]` **9 Aug 2026**, on **two independent engines**: a WebTransport session towards a **self-signed ECDSA P-256 certificate of 13 days**, with the fingerprint published in the page and **no warning**, opened on **Chrome 151** (30.2 ms) and on **Firefox 140** (52.0 ms), and the bytes came back identical from both. Bench `banchi/01-b2-*`, document `FASI.md` §01-filo-nudo |
| ⚠ **and what the two engines DO NOT prove** | they are two teams that do not know us, so their agreement counts — ⛔ **but what served was `aioquic`, not an implementation of ours**: this measures **the trust model**, not the server. And **Safari stays out by decision** (`DECISIONI.md` §1.8) |
| **the constraint** | `[S]` certificate valid **less than 14 days**, **ECDSA P-256** key, no RSA, **SHA-256** fingerprint, and `allowPooling` at `false` |
| ⭐ **why the rotation does not show** | it is **the server itself that serves the page**: it regenerates the certificate before it expires and writes the current fingerprint into it. The user touches nothing and does not know it exists |
| ⛔ **what it does not cover** | **loading the page**, which is a TCP connection of its own. There the warning with the click remains — or the real certificate, for whoever has a domain |
| ⭐ **and the same road is AVAILABLE on all three engines** | `[R]` **WebKit implemented it on 2 Oct 2025** (bug 300057, `NetworkTransportSessionCocoa.mm`) and it ships in **Safari 26.4**: iPhone and iPad have **the same** road as the other two, not one to be rescued. ⛔ **Available, not verified**: on Safari nobody has tried it (row above, `DECISIONI.md` §1.8), and *«holds on»* would be a claim of working supported by `[R]`, that is by reading a commit — form **E1**. ⚠ *Corrected on 10 Aug 2026, finding **R11.16**: this row and the one above said, in the same table, that it holds on three engines and that Safari stays out. This file is the **referee**, that is the place where a deduction weighs more than in the product documentation* |

⛔ **Hence two certificates, and they must be kept distinct in the code**: a **long-lived** one for the page, which
is the one on which the user grants the exception and which therefore **must not change** more often than
necessary; a **short-lived** one for the session, which rotates by itself. ⚠ Confusing them makes the warning
reappear every two weeks, and nobody would connect the two things.

⛔ **And the fingerprint the page holds grows old.** A tab left open for two weeks
holds the fingerprint of a certificate that has meanwhile been rotated: on reconnection the browser
refuses, and the symptom is *«it no longer connects and does not say why»*. The two cures, and **the second is
the one chosen**:

| | |
|---|---|
| reloading the page | it works and throws away the state: the user loses what they were looking at |
| ⭐ **asking for the current fingerprint** | ⛔ **and it does not go through RCP**: the session is not yet open, so there is no channel on which to ask. The page fetches it **from the server that served it**, with an ordinary request, and tries again |

⚠ *Brought over on the evening of 9 Aug 2026 from report S1 (finding **O6**), which declared it as
«where this update lives in RCP must be decided». The answer is: **outside** RCP.*

⚠ **And the consequence on acceptance testing, which holds in any case**: a bench that tests trust **MUST**
also test the **second** connection, and a third with the key changed. The
single-connection test stays green forever (`LEZIONI.md` §2.1).

### 4.2 The control channel

The client opens the **first bidirectional stream of the WebTransport session**. That is the control
channel, it stays open for the whole session, and its closing **is** the end of the session.

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.5**: here there was «(identifier 0)», and it is a
> remainder of the bare-QUIC draft.* In an HTTP/3 connection QUIC stream number 0 is already
> taken — it is that of the request that **establishes the WebTransport session itself** — and the API
> exposes no number: it opens a stream and returns an object. Whoever read «0» to the letter
> looked for the control channel where it will never arrive, with the diagnosis «the client does not open the channel» **while the client has opened it**.

⛔ **In bytes**: a FIN on that stream, from either of the two parties, closes the session.
Whoever receives it **MUST** consider it finished; it **MUST NOT** keep sending **on any channel,
including the control one**.

> ### ✅ Decided on 11 Aug 2026 by the user: **silence** — `DECISIONI.md` §7.14
>
> *Until today this line forbade sending «on the other channels» and was silent about control. On a
> bidirectional stream the `FIN` of one party does not close the direction of the other, so whoever received it
> **could** send the `CONGEDO` that §8.1 imposes on whoever closes: **different bytes for the same
> input** — nine against zero — and two diverging implementations without either being wrong
> (finding **R11.22**).*
>
> ⛔ **Whoever receives the `FIN` sends nothing more, not even on the control channel.** The reason
> travels by the **second road** of §3.1 point 3 — the application error code of the closing
> of the session — which does not need a live channel.
>
> ⭐ **And what decided was a measurement, not a reading.** `[M]` 10 Aug 2026, defect 2 of B11:
> **Chrome throws away a message sent just before closing the session.** The `CONGEDO`
> of the other reading would be **a MUST that one engine out of two cannot honour** — the form that
> finding R1.4 has already declared a defect. The second road of §3.1, instead, worked on
> both engines.
>
> ⚠ **The price is paid in §8.1**, not here: that section imposes the farewell on «whoever closes», and from
> today it carries written that **whoever has received a `FIN` is not «whoever closes»**. Without that sentence this
> decision would leave the contradiction standing instead of closing it.
>
> ⛔ **And a premise that was false must be stated, because it is the one with which the decision was taken**:
> *«the server never strikes first on its own initiative»*. It does strike, and it is the most measured behaviour
> of phase 1 — the three ceilings of §4.6 seen to trip by **B6** (5.0 · 60.1 · 10.0 s), the **36
> violations out of 36** of **B5** after each of which the server closes, `RESPINTO`,
> `TROPPI_TENTATIVI` and `GIA_ATTIVA_REMOTA`. ⭐ The decision **does not change**: precisely because the
> server closes often, what the receiver does matters — and it is the measurement on Chrome that chooses, not
> the rarity of the case.

### 4.3 `CIAO` and `ECCOMI`

| | |
|---|---|
| **CIAO** | client → server. Major version of the protocol, client capabilities |
| **ECCOMI** | server → client. Chosen version, server capabilities |

**The body, in bytes** (the elementary types are in §6.0):

```
CIAO / ECCOMI
 ├── u16   versione
 └── list of capabilities:
       u16  quante
       for each:  stringa nome  ·  stringa valore
```

In `CIAO` the `versione` is **the highest the client can speak**; in `ECCOMI` it is **the one chosen
by the server** (§9). RCP/1 is **1**.

The **capabilities** are name-value pairs. An unknown name is ignored (§3, exception). The names
defined in RCP/1:

| Name | Who declares it | Values |
|---|---|---|
| `video.codec` | both | list among `hevc`, `h264`, in order of preference. ⛔ **`av1` left on 20 Aug 2026** (`DECISIONI.md` §1.13-ter): the name stays defined and its number stays **2** forever, but it is no longer negotiated |
| `video.profondita` | both | list among `8`, `10` |
| `video.livello` | client | the maximum level it can decode, e.g. `5.1`. ⛔ The server **MUST** emit a stream of level not higher, and **does not guess it**: a level declared too low does not give a network error, **it makes the decoder refuse the configuration** and the symptom is «the browser does not open the stream» *(finding **O12**)* |
| `video.misura_massima` | client | `LARGHEZZAxALTEZZA` it can decode, e.g. `3840x2160` |
| `audio.codec` | both | list among `opus`, `pcm` |
| `input.tocco` | client | `si`, `no` — reserved, in RCP/1 it is always `no` |
| `appunti.testo` | both | `si`, `no` |
| `client.nome` | client | free text for the log, e.g. `remotix-linux 0.1.0` |
| `banco.marca` | server | `si`, `no` — ⭐ *new, night of 9 Aug*: the **bench function** of §7.5 is on. ⛔ It is `no` in every normal installation, and a server that declared it `si` by mistake **writes it in the log at every start** |

⛔ **The form of names and values is constrained**, or «ignoring what is not known» becomes
«guessing»:

- a **name** is made of `a-z`, `0-9`, `.` and `_`, from 1 to 64 bytes;

> ### ⛔⭐ The underscore is from 10 Aug 2026, and it was found by **the validator**
>
> This line said *«`a-z`, `0-9` and `.`»* — and three lines below, the table defines
> **`video.misura_massima`**, which contains that character. ⛔ **The specification contradicted
> itself**: an implementation that had applied the rule to the letter would have closed with
> `ERRORE_PROTOCOLLO` a capability **defined by this very document**, and the symptom — *«the client drops as soon as it sends `CIAO`»* — would have named neither the rule nor the name.
>
> ⭐ **It was found by `banchi/01-b4-validatore.py` on its first run**, that is a program
> written by reading only this file, before a byte of server existed. It is precisely the
> job §11 assigns to it: *«client and server are not tested against each other»*.
>
> ⚠ **Of the two cures this one was chosen**, and it is 🔸 derived: admitting `_` instead of renaming the
> capability. Renaming would touch a name already cited in `STUDI.md` §web and in `SPECIFICHE.md`, and the
> underscore is the convention the rest of the document uses in field names
> (`tela_larghezza`, `max_idle_timeout`).
- a **value** is printable UTF-8 text, at most 256 bytes;
- a **list** inside a value is written separated by commas, without spaces: `hevc,av1`;
- ⛔ **a name repeated twice is `ERRORE_PROTOCOLLO`.** «The last one wins» and «the first one wins» are
  two different implementations of the same document, which is precisely what this document
  exists to prevent;
- ⛔ an **empty** value is `ERRORE_PROTOCOLLO`: whoever has nothing to say does not send the capability;
- ⛔ **an unknown entry INSIDE a list is discarded**, as an unknown name is discarded: a
  `video.codec` that is `hevc,vp9` is read as `hevc`. It is the same exception of §3, and it is the
  mechanism by which a client of tomorrow will speak to a server of today. ⚠ But if **after discarding
  the list remains empty**, the farewell is `NIENTE_IN_COMUNE`;
- ⛔ **a capability sent by the wrong side** — `video.misura_massima` arriving from the server — is
  `ERRORE_PROTOCOLLO`: the name is known, so the exception for names does not cover it;
- ⛔ and whoever **does not declare** `pcm` or `8`, which §4.3 imposes on both, gets the farewell
  `NIENTE_IN_COMUNE`, not `ERRORE_PROTOCOLLO`: it did not write wrongly, it has nothing to
  speak about.

> ⚠ *The last three lines are from the evening of 9 Aug 2026, finding **R1.12**.* The rule said
> «an unknown **name** is ignored» and was silent on everything else: an unknown value inside a
> known name had **two readings both defensible** — it is discarded, or it is a field out of
> range and the connection drops — and the two produce **different bytes on the wire for the same
> input**. The day an RCP/2 exists that speaks a new codec, the old server either
> carries on or drops, and the document did not say which.

⛔ If the intersection of `video.codec` is **empty**, the server **MUST** send the farewell
`NIENTE_IN_COMUNE`. It MUST NOT fall back on an undeclared codec. The same holds for
`video.profondita` and for `audio.codec`.

⚠ `pcm` **MUST** be declared by both: it is the base always available, and it serves as positive
control when Opus is not negotiated. In the same way `8` **MUST** appear in
`video.profondita` of both.

⛔ **The one who chooses is the server**, inside the intersection, following the order of preference **of the
client**. The choice **MUST** be written in the server log: a successful negotiation with
the opposite of what was wanted inside is trap 4 of `LEZIONI.md` §4, and it shows only if
someone writes it.

⚠ `video.misura_massima` does **not** change the canvas: it is a ceiling the server **MUST** respect
when it grants the canvas (§4.5). It exists because a phone's decoder has limits that its
screen does not declare.

### 4.4 The credentials

A single `CREDENZIALI` message with user and password. The server passes them to PAM.

```
CREDENZIALI
 ├── stringa utente         from 1 to 256 bytes     ⛔ empty = ERRORE_PROTOCOLLO
 └── stringa parola         from 1 to 1024 bytes    ⛔ empty = ERRORE_PROTOCOLLO

AMMESSO      empty body
RESPINTO
 └── u8      motivo         (from the reason space of §8.2)
```

| Outcome | Message |
|---|---|
| admitted | `AMMESSO` |
| rejected | `RESPINTO` with reason |

⛔ The server **MUST NOT** distinguish in the reason between «nonexistent user» and «wrong password»: both are `CREDENZIALI_ERRATE`. And it **MUST** apply **the address ban**
before answering (§4.4-bis). ⚠ *This line said «the **rate limiting** of attempts», which was the form replaced on 10 Aug 2026 by `DECISIONI.md` §1.9: one does not get out of the ban
by waiting a few seconds, and calling it rate made people write a wait where a
refusal must be written. Aligned on the night of 10 Aug, as §8.2 row `0x08` already was.*

⛔ **`RESPINTO` is the farewell of authentication.** After sending it the server **MUST** close
the **WebTransport session** as §3.1 says — with the same reason in the **application error
code of the closing**, not in a transport `CONNECTION_CLOSE` — and **MUST NOT** send
`CONGEDO` as well. The client **MUST NOT** retry on the same connection: for a second
attempt a new one is opened.

⛔ **And after `RESPINTO` the client has only one thing left it may say: `CONGEDO`.** The prohibition of §4.4
is on **retrying**, not on saying farewell. If the server errs *after* having sent `RESPINTO` — another
message on the same control channel — the client applies §3 and closes, and §8.1
**REQUIRES** it to say why: that `CONGEDO` is **conforming**, even if for the server the session was already
over. ⛔ Any **other** message, and in particular a second `CREDENZIALI`, is the violation
§4.4 forbids.

> ⛔ 🔸 *Clarified on 10 Aug 2026 by bench **B11**, and the form is mine: it is corrected without
> discussion.* The rule was already decidable by reading §4.4 and §8.1 together — but the **server** did not
> read it that way: it counted as «bytes sent after the end» **everything** that arrived, and the case
> `respinto-poi-congedo` put a red on the page **while it was doing what §8.1
> requires of it**. ⚠ The control channel had no `FIN`: §4.2 was not in play, and the only rule
> that was speaks of **attempts**, not of leave-takings. ⭐ Now the server names the two things
> separately, and B11 demands the farewell **once per engine** instead of merely not
> finding excess bytes — *an absence is not a proof* (`LEZIONI.md` §1.9).

> ⚠ *Clarified on 9 Aug 2026.* The first draft had `RESPINTO(motivo)` in §4.4 and
> `CREDENZIALI_ERRATE` among the farewell reasons of §8.2, without saying whether after the first the
> second arrived too. Two implementations could guess differently — or, worse, **guess the same
> because written by the same hand**, which is the silent defect against which this document exists.

> ⚠ *The ranges are from the evening of 9 Aug 2026, finding **R1.28**: §6.0 declares the empty string
> lawful, so `CREDENZIALI` with user and password of zero bytes was **conforming**. The two
> readings — «it goes to PAM and consumes an attempt» against «it is a protocol error and the connection drops» — give two different robustness profiles, because in the second an attacker
> who sends empty credentials **does not increment the count** of §4.4-bis. ⚠ *It said «neither of the two counters», and they were the two of the previous form: since 10 Aug 2026 the count is **only one**, on the
> address alone. The reasoning does not change — the number does.*

⚠ **A note that is not normative and that is worth the time of writing it**: the password is in
cleartext in the memory of whoever receives it. It must be zeroed as soon as PAM has answered, and **must not** appear
in any log at any level — not even in `traccia`, which in v1 is a keystroke recorder
(`fondamenta/remotix-c/src/registro.h`).

### 4.4-bis ✅ The address ban — three attempts, then twelve hours

*Decided by the user on 10 Aug 2026, in two steps. First: «se l'utente sbaglia la password per
3 volte consecutive, non vengono più accettate connessioni da quell'IP per 12 ore (ban)». Then, stricter:
«3 tentativi di connessione fallita (perché user sbagliato o perché password sbagliata)
causano il ban di quell'IP».*

> ⛔ **It entirely replaces the previous form**, which was 🔸 mine and pronounced by nobody: 5
> attempts in 5 minutes, then a 30-second window that doubled up to 15 minutes, with **two**
> counters — one per user name and one per address — and reset on a successful login.
> The **per-user-name** counter no longer exists: the count looks at the address and nothing else.
>
> ⭐ **And the wire does not change by one byte**: `TROPPI_TENTATIVI` (`0x08`) already exists in §8.2, no new
> type, no exception to the rule of §9.

| | |
|---|---|
| **the count** | **three** failed authentications from the same **source address**, ⛔ **within a 5-minute window**. Outside the five minutes the ban does not trip: whoever mistypes now and then is not whoever is trying passwords. ⛔ And the user name **does not count**: three different names count three |
| **the consequence** | that address is **banned for 12 hours** |
| **what resets the count** | a **successful** authentication from that address — and the passing of time: ⚠ the window is **sliding**, that is one looks at the time of the **last three** failures, one does not start over at the first. Anchoring it to the first, three failures at 0:00 · 4:59 · 5:01 would restart the count from one, and whoever tries at a pace just slower than the window would **never** be stopped |
| ⛔ **the key of the count** | **the address alone, without the port.** ⚠ It is the defect bench **B5** found in the previous form: the key contained the port, and since §4.4 admits **only one attempt per connection** the port changes at each attempt — that counter was **always 1**. Code present, that read well, and that did nothing |

⛔ **What counts as a failed attempt, and what does not.** **Only** authentication counts: a
`CREDENZIALI` to which the server answers `RESPINTO(CREDENZIALI_ERRATE)`. ⭐ And note that the count
**does not know** whether the name did not exist or the password was wrong — §4.4 forbids the server to
distinguish them — which is exactly the thing this rule has decided to count as one.

**They do NOT count**, and the list is normative because each of these would ban someone who has not
done anything wrong:

| | |
|---|---|
| `ERRORE_PROTOCOLLO` · `VERSIONE_INCOMPATIBILE` · `NIENTE_IN_COMUNE` | they are faults of the **bytes**, and can arise from a defect **of ours** or from a tab left open on an old version (§13 of `PIANO.md`). A server defect that banned the user for twelve hours would be the worst diagnosis this project could produce |
| `TEMPO_SCADUTO` · connections that drop halfway through the handshake | they measure a slow network or a person who types slowly (§4.6), not an attempt |
| ⛔ **`GIA_ATTIVA_REMOTA`** (`0x0F`) | it is what the **second device of the same user** receives (§8.2): counting it would mean that whoever tries to reattach three times from the phone **bans themselves**, while their session is alive |

⛔ **What a banned address sees** *(decided by the user: «viene visualizzata una pagina di
login rifiutato»)*:

1. **the page is served all the same**, and shows the refusal — *«tentativi esauriti»*. ⛔ Not a network
   error, not a silence: whoever has been banned by mistake is almost always the owner, and must
   be able to understand what happened to them instead of facing a server that looks dead for
   half a day;
2. **the WebTransport session is refused**, with `TROPPI_TENTATIVI` in the application error code
   of the closing (§3.1 point 3). ⚠ It serves the **tab already open**, which does not reload the page and
   would otherwise remain waiting;
3. 🔸 the page also says **how many hours are left**. *Derived, correctable without discussion*: it is the
   difference between a piece of information and half a day of mystery.

⛔ **The ban survives a server restart** *(decided by the user)*: address and expiry time on
file. A ban that resets on restart is a protection that **gets lost by itself** — invariant **I7** — and
whoever restarts the server for another reason would not know they had removed it.

⛔ **And there are two ways out, not one** *(decided by the user: «comando di sblocco oppure il trascorrere
delle 12 ore»)*: the natural expiry, or an **unlock command on the server**. The latter is the
way out for whoever bans themselves from their own phone, and it asks for the only key that case admits —
access to the machine. ⛔ **Every unlock is written in the log**, or a ban removed and a ban that never
tripped look the same.

> ⚠ **The unlock command is NOT part of RCP, and it must be said here so that nobody looks for it on the wire.** Not
> one byte of the session passes: it is a mechanism of the server, and this document only dictates
> *that it exists*, *that it answers distinguishing «removed» from «was not banned»* and *that it writes in the log*.
> ⛔ **The form is not indifferent, and it has been paid for**: `remotix --sblocca IND` as a **second
> process** does not work — the ban lives in the memory of the serving process, a second process can
> only rewrite the file, the server would keep answering `TROPPI_TENTATIVI` until the restart, and
> **whoever gave the command sees it exit with zero**. Since the night of 10 Aug 2026 the two
> implementations speak the same protocol of **one line on a Unix socket `0600`** — `SBLOCCA
> <indirizzo>` → `TOLTO` / `NON-BANNATO`, and `PING` → `PONG` to say *«the command is there»*. The full
> account is in `FASI.md` §01-filo-nudo («What did NOT work»), not here.

⭐ **The fixed delay stays, and it is not redundant with the ban.** The server **MUST NOT** answer
`CREDENZIALI` before **one second** has passed since reception, **even when the answer is
`AMMESSO`**. The ban removes whoever guesses; the fixed second removes **timing** as a
channel — without it, «nonexistent user» answers in a millisecond and «wrong password» in fifty,
and the distinction that §4.4 forbids writing in the reason can be read with a stopwatch.

> ⚠ **And on this there is a measurement that does not add up, declared instead of hidden.** `[M]` 10 Aug
> 2026, bench **B8**: the median of the rejected attempts is **2636 ms** over 42 samples, where this
> line wants ~1000. ⛔ What governs the times is not our delay: it is **PAM**. As long as that delay
> is not constant, the fixed second **does not hide what it declares it hides** — that is whether a
> user name exists. It stays `[?]`, and **the ban does not close it**: they are two different properties.

⛔ **And the refusal of a banned address also leaves NOT BEFORE ONE SECOND.** The *decision* is
taken without querying PAM — it looks only at the address, and no secret enters it — but **the answer
waits like all the others**: `RESPINTO(TROPPI_TENTATIVI)` on the control channel, after the fixed
second.

> ⛔ *Corrected on the night of 10 Aug 2026, and bench **B8** found it while it was being rewritten.*
> This paragraph said *«the refusal of a banned address **does not go** through the fixed second: it is decided **before** `CREDENZIALI`»*. ⛔ **They are two incompatible lines in the same section**: a
> refusal decided *before* `CREDENZIALI` has no `RESPINTO` to send, because `RESPINTO` is the
> answer to a message that has not yet arrived — and §8.2 has `TROPPI_TENTATIVI` travel precisely
> inside a `RESPINTO`.
>
> ⛔ **And it reopened a contradiction that finding R11.10 had closed that same day**, for the
> reason that still holds: *«an immediate refusal inside the window and a delayed one outside put **timing** back as a channel, from the side opposite to the one the fixed delay removes»*. An address
> that receives the answer in a millisecond knows it is banned before even reading the reason.
>
> ⚠ It is the form this project pays most often — **a cure applied in one place only** — and
> this time it was committed by whoever wrote the new rule, a few hours after having cured an identical one.

⛔ **The refusal page is served with HTTP status `200`**, not with a 4xx. ⚠ *Chosen on the night of 10
Aug 2026, 🔸 derived:* with an error status an intermediary or the browser itself can
**replace the body** with its own error page, and the sentence the owner **must**
read — *«tentativi esauriti, restano N ore»* — would disappear precisely in the case it exists for.

⚠ **And the key of the count has a canonical form**, which must be stated because it is in a single place of the
code and no document declared it: the address travels between **square brackets even when it is
IPv4** — `[192.168.0.2]` — because that is how the host writes it. ⛔ Whoever types `192.168.0.2` to the
unlock command **must arrive at the same key**: normalisation is the server's job, not the
commander's. Without it, the command answers *«was not banned»* for every address, **forever and without
symptom**.

⚠ **The price, declared — and it is not paid by whoever guesses:**

| | |
|---|---|
| **behind a NAT addresses are shared** | three mistakes by **one** person close the door to all the others for twelve hours. The per-user-name counter of the previous form existed precisely for this, and **it was removed knowing it**: the choice is to give the address only three attempts instead of distinguishing who makes mistakes |
| **the first to trip on it is the owner** | long password, phone keyboard, automatic capitals. This is where the obligation comes from of the page that **says** what happened and of the unlock command: without those two, the rule would be indistinguishable from a fault |
| ⛔ **and the password remains the only key** | three attempts **per address** raise the cost for whoever guesses a lot, and do not close the game: a network of ten thousand addresses still gets thirty thousand attempts on a single account. That one is closed by the strong authentication postponed to the end of the project (`DECISIONI.md` §1.7) |

⭐ **And one thing this rule cannot do**, written so that nobody attributes it to it: nobody
can get **someone else's** address banned. To reach `CREDENZIALI` one must have
completed the QUIC handshake, which demands that the packets really come back to that address:
the sender cannot be forged. The ban hits only whoever has really knocked.

⚠ **And a consequence on acceptance testing, which bites at once**: the benches all start **from the same
address**, and the one that tests this rule fails on purpose. With twelve hours, «one waits for the expiry» is not a cure — the bench uses the unlock command, and the limiter bench **does not
call it within its own run**, or it no longer tests anything. The detail is in
`FASI.md` §01-filo-nudo, rule **B0.3** and bench **B8**.

### 4.5 `ATTACCA`

```
ATTACCA
 ├── u32     tela_larghezza
 ├── u32     tela_altezza
 ├── u32     vista_larghezza
 ├── u32     vista_altezza
 └── stringa disposizione        (≤ 64 bytes)
```

| Field | | |
|---|---|---|
| `tela_larghezza`, `tela_altezza` | pixels | the size the client asks for |
| `disposizione` | string | the keyboard layout, e.g. `it` |
| `vista_larghezza`, `vista_altezza` | pixels | the size at which the client will draw |

⛔ **The limits, and they are normative**: width and height of the **granted** canvas **MUST** be between
**320×240** and **4096×2304**, and **both MUST be even**.

- **Below the minimum**, or with an **odd** side, the canvas asked for in `ATTACCA` is `ERRORE_PROTOCOLLO`
  (in `ADATTA_TELA`, below the minimum, `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)` — §7.1).
- ⛔ **Above the maximum it is NOT an error**: the server **MUST** grant the canvas with the side that exceeds
  brought **to the maximum** and the other unchanged (5120×2880 → 4096×2304, 5120×1440 → 4096×1440), and
  **MUST** write it in the log. It holds identically in `ATTACCA` and in `ADATTA_TELA` (which answers
  `TELA(ADATTATA)` with the reduced size). It is a case of the rule below — *the granted canvas can
  be different from the one asked for* — and the client **MUST** adapt by laying out with bars
  (`SPECIFICHE.md` §6.2), without distorting. ⭐ A client **SHOULD** all the same not ask beyond the
  maximum: our page already brings the side to the maximum itself (`tela_da_chiedere()`), with the same
  rule, so server and client arrive at the same number.

> ⛔ *Until 1 Oct 2026 the maximum was **7680×4320**, and beyond it was `ERRORE_PROTOCOLLO`.* Lowered
> by the user's decision (phase 19: *«4096 max di larghezza va benissimo, non ho mai preteso di
> più»*). ⚠ **The reason is video, not capture**: `[M]` 22 Aug 2026 H.264 on the Intel card
> (VA-API, `EncSliceLP`) accepts **32–4096 px per side** (4096×2160 yes, 4112×2160 no), and Firefox on
> Linux receives only H.264 — a wider canvas had video only in HEVC, that is only on Chrome.
> **2304** is 16:9 at 4096 (DCI 4096×2160 fits), and 4096×2304 is **36 864 macroblocks**, the
> exact `MaxFS` of H.264 levels 5.1 and 5.2 — beyond that level 6 would be needed. ⭐ The change is
> **compatible**: no new or reused number, and a client that asked for up to 7680×4320 receives
> a smaller canvas — something §4.5 already required it to be able to receive.

⭐ **The even-number constraint is not pedantry**: video encoders work on blocks, and an
odd size is rounded **by whoever encodes, in silence** — two different sizes under the
same label, that is error form **E2** of `REVIEWER.md`. Better to refuse it here, where one
can say why.

⚠ The `disposizione` **MUST** be an XKB layout name, optionally with the variant in
parentheses: `it`, `us`, `de(neo)`. The server **MUST** refuse with `ERRORE_PROTOCOLLO` a string
that does not have this form, and **MUST** send the farewell `SESSIONE_NON_SERVIBILE` for a well-
formed layout the system does not know — they are two different faults, and must be distinguished.

⚠ **The form, in full**: `[A-Za-z0-9_-]+` optionally followed by `(` `[A-Za-z0-9_-]+` `)`.
⛔ **Capitals** and the **underscore** are in it because the system really uses them — `[M]`
21 Aug 2026, asked of the system *through the product*: of **589** layout/variant pairs
that a Debian machine compiles, **9 have a capital** (`de(T3)`, `jp(OADG109A)`, `ua(macOS)`,
`ru(phonetic_YAZHERTY)`, `ie(CloGaelach)`…) and **102 an underscore**. A narrower alphabet would
refuse them with `ERRORE_PROTOCOLLO`, that is **accusing the client of a fault of the machine** — which
is worse than a farewell, because it sends people looking for the defect on the other side of the wire.
⛔ And the **empty variant** — `it()` — is **out of form**: `ERRORE_PROTOCOLLO`, not
`SESSIONE_NON_SERVIBILE`.

The server answers `SESSIONE`:

```
SESSIONE
 ├── u8      stato               1 = NUOVA, 2 = RIPRESA
 ├── u32     tela_larghezza      ⚠ the GRANTED canvas
 ├── u32     tela_altezza
 └── stringa desktop             one of: gnome · kde · xfce · lxqt · cinnamon · unknown
```

⭐ **The granted canvas can be different from the one asked for**, and it is the case of the fallback on KDE
< 6.8 (`SPECIFICHE.md` §6.3): the session was already alive with another size and cannot change it. The
client **MUST** adapt by rescaling, and the server **MUST** have written the fallback in the log.

⛔⛔ **And the second reason is the common one, not the exception: the canvas OUTLIVES the session.**
The stage stays at the size at which the previous client left it, and `SESSIONE` grants
**that one**, not the one asked for in `ATTACCA`. ⇒ A client that attaches after another **of the same
user** — the graphical session is one per user, and multi-tenant does not exist — receives a canvas
it did not ask for and whose **origin it does not know**, and has no way to tell it apart from a
fallback. ⚠ **It is not «someone else's window»**: it is the size its own previous connection
left (`DECISIONI.md` §5.0-septies, where the wrong sentence is recounted).

⚠ **Asking for a canvas in `ATTACCA` does not obtain it**: `tela_larghezza`/`tela_altezza` are a
**preference**, and the only message that changes the canvas is `ADATTA_TELA` (§7.1). ⇒ A client that wants
its own size **MUST** send an `ADATTA_TELA` after `SESSIONE` — and it is what
`DECISIONI.md` §5.0-sexies already makes it do at every attach.

`[M]` 21 Aug 2026, real product: three attaches in a row with `ATTACCA(1920×1080)` received
`SESSIONE` with **1920×1080**, **1264×800** and **1600×900** — that is, each time, **what the run
before had left**.

⛔ **And this line loosens nothing**: the granted canvas stays subject to the limits, to evenness and to
`video.misura_massima`. It only says **where it comes from** when the client did not ask for it.

⚠ The granted canvas **MUST** respect `video.misura_massima` if the client declared it, and
respect in any case the limits and the evenness above. The `desktop` field is for diagnosis: the client
**MUST NOT** change behaviour based on its value, or a per-desktop compatibility gets written that nobody asked
for and no bench tests.

If the attach cannot be served, the server sends a farewell with one of the reasons of §8.2 — never with a
silence, never with a half session.

### 4.6 ⛔ The handshake deadlines

*Added on 9 Aug 2026: a connection that stops halfway through the handshake holds a slot and
declares it to nobody.*

| From | To | Ceiling |
|---|---|---|
| ⭐ **opening of the control channel** *(the first bidirectional stream of the session)* | `CIAO` received | **5 s** |
| `ECCOMI` sent | `CREDENZIALI` received | **60 s** — it is the time in which a person types the password |
| `AMMESSO` sent | `ATTACCA` received | **10 s** |
| ⭐ **opening of the WebTransport session** | **opening of the control channel** | **5 s** — ✅ decided on 11 Aug 2026, `DECISIONI.md` §7.17 |

> ### ⭐ The row that was missing, and a measurement found it — ✅ 11 Aug 2026
>
> *The table started from `CIAO`, and before `CIAO` there was a state in which the server counted
> nothing: whoever opened the session and never opened the channel **had no ceiling on them at all**.
> Found by bench **B6** (finding **R12-A.25**), decided by the user the same day.*
>
> ⛔ **When the 5 s expire, the server closes with `TEMPO_SCADUTO`** `0x0D`. ⚠ The control channel does not
> exist, so the `CONGEDO` **is not sent** (§8.1, the condition decided in `DECISIONI.md` §7.15):
> the reason travels **only** in the application error code of the closing of the session (§3.1
> point 3). ⭐ And it is the first place where the decisions of 11 Aug fit together: without §7.15
> this line would impose a byte on a channel that was never born.
>
> ⭐ **Why 5 s, that is the same number as the row below**: opening the control channel is the
> **first mandatory act** of the session (§2.5), it does not depend on how fast a person
> types and does not depend on the network more than `CIAO` does.
>
> ⛔ **And what it really closes**: it was the last way, in this phase, to **occupy a slot without
> saying who one is**. The QUIC idle timeout did not cover it: that one counts **silence**, and
> a session that writes on another stream is not silent — it held the slot
> indefinitely.
>
> ⚠ **No new message type is needed**, and it matters: the window of §9 has been closed since 10 Aug
> 2026. `TEMPO_SCADUTO` was already there.

> ### ⭐ The first row changed by one word, and the second answer says it is not enough
>
> ⚠ *The first row said* **«TLS handshake finished»** *since 9 Aug 2026. It was `[?]` **R3.27**
> — «"TLS handshake finished" is not an instant the two sides share»: in WebTransport the
> HTTP/3 connection and the session are two separate things, and between the two instants at least one network
> round trip passes. Corrected on 11 Aug 2026 on a measurement of bench **B6**, findings **R12C.11** and
> **R12-A.25**.*
>
> **The first answer of B6, and it changes one word.** The stopwatch of the first ceiling starts
> from the **opening of the control channel**: it is the instant the server really observes, and it is what
> `src/rcp.c` does (the RCP session is born when the channel opens, and the ceiling is counted from there). ⛔ The
> end of TLS is **not** usable: a second session on a reused connection would start
> **with the budget already consumed**, that is it would see itself sent a farewell for a time it did not have.
>
> ⛔ **And the second answer of B6 is more serious, because it says that curing the word DOES NOT CLOSE the
> hole.** If the stopwatch starts from the opening of the channel, whoever opens the WebTransport **session** and
> **never opens the channel** has **no ceiling** on them: it stays there, alive and without expiry — that is
> exactly the connection that *«holds a slot and declares it to nobody»*, which is the first line
> of this section. The table starts from `CIAO`, and **before `CIAO` there is a state in which the
> server counts nothing**.
>
> ⚠ **What covers it today, and why it is not enough**: only the QUIC idle timeout, which is **30
> seconds of silence** — but whoever keeps the session open by sending anything on another stream
> is not silent, and never expires. ⛔ **What the right ceiling is, and from what instant, is an open
> question and not an oversight**: it is in `DECISIONI.md` §7.17, with the two readings and the concrete case. Here
> the hole is declared instead of being filled with a number nobody chose.

⛔ When a ceiling expires, the server **MUST** send the farewell `TEMPO_SCADUTO`. It **MUST NOT** wait for the 30
seconds of the QUIC idle timeout: that one measures the **silence of the network**, this one measures a
**client that does not do its job**, and confusing them makes a slow network look like a defect of ours.

> ⛔ **And the 60 seconds of the password were unreachable** — finding **R1.8**. While
> the user types, **nothing** passes on the wire: §2.2 forbids an application heartbeat and there is
> no other active channel before the attach. At the thirtieth second the QUIC idle timeout
> trips and **the connection dies in silence**, without reason, before the ceiling of
> 60 can ever expire. The bench of §11 would have measured 30 where the document says 60, and the
> programmer would have blamed the bench.
>
> ⛔ **The cure, and it is the server's**: while it waits for the credentials, the server **MUST** keep the
> connection alive with the **transport PINGs**, which are not an application heartbeat — they carry no
> information, have no answer to interpret, and do not create a second truth about silence
> (§2.2). ⚠ Without this line one implementation sends them and the other does not, and the second **loses the
> users who type slowly**: an intermittent defect, the worst to diagnose.

---

## 5. The channel map

| Channel | Transport | Direction | Reliable? |
|---|---|---|---|
| **control** | the **first** bidirectional stream of the session (§4.2) | ↔ | yes |
| **video** | **one unidirectional stream per frame** | server → client | yes, but abandonable |
| **audio** | datagrams | server → client, and ↑ for the microphone | no |
| **input** | one reserved unidirectional stream | client → server | yes |
| **clipboard** | one unidirectional stream per transfer | ↔ | yes |
| **cursor** | on the control channel | server → client | yes |

⚠ The microphone is in the table because the direction is foreseen, **but RCP/1 does not define it**: see §12.

### 5.1 ⭐ Why a frame is a stream

It is the most important design choice of the protocol.

If video travelled on **a single** stream, a slow frame would block all the ones after it —
head-of-line blocking — and on a mobile network the session would pile up its own
past. If it travelled on **datagrams**, we would have to rewrite fragmentation and retransmission, that is
redo QUIC inside QUIC.

With one stream per frame: the streams are independent, so a late frame does not
touch the following ones; and above all the server **MAY** call `RESET_STREAM` on a frame that
is no longer needed — because a more recent one has already left — and the bytes not yet sent do not leave
at all.

⛔ **This is how invariant I1 is honoured without betraying it**: one does not *reduce quality* out of prudence,
one *throws away the past* when it is past. And every abandonment **MUST** be written in the log:
a frame lost in silence and one abandoned on purpose look the same from the receiving
side.

> ### ⛔ Abandonment has **TWO observable forms**, not one — *13 Aug 2026, `[M]`*
>
> *This paragraph, and §6.2 with it, described a single form: the **reset** stream. At phase
> 3 a second one was seen, and a client written on the first **does not recognise it**.*
>
> | form | what the client sees | when it happens |
> |---|---|---|
> | **A — the reset stream** | an open stream that ends with `RESET_STREAM` instead of FIN | the server had already **let out at least one byte** of that frame |
> | ⛔ **B — the hole in the `numero` values** | **no stream**, and the next `numero` skips by one | the server had **consumed the `numero`** and then abandoned **before a byte left** |
>
> ⛔ **Which of the two the client sees depends on a detail neither side controls:
> whether a byte had already left.** It is not a choice of the server and it is not information the protocol
> carries — it is the moment the abandonment falls relative to the writing.
>
> ⇒ **The consequences, and they are normative:**
>
> - the client **MUST** treat **both** forms as a hole, and in both send
>   `RICHIEDI_CHIAVE` (§5.2). ⛔ A client that looks only at `RESET_STREAM` **loses form B in
>   silence**, and the symptom is the one §5.2 exists to avoid: pictures more and more wrecked
>   without any error raised by anyone;
> - the server **MUST** write **both** in the log, and distinguish them: they are the same
>   decision, but on the receiving side they have **different appearances**, and a log that names only one
>   does not explain what the client saw;
> - ⚠ and a bench that injects abandonment **must be able to produce both**, or it certifies half of the
>   rule believing it certifies all of it.
>
> ### ⛔⛔ And there is a third case, which is **not observable at all** — and it is the most dangerous
>
> A frame **thrown away for lack of credit** (§2.3) is neither of the two forms: no stream
> is opened **and the `numero` is not consumed**, because §6.2 makes it grow only for the
> frames the server **decides to send**. ⇒ ⛔ **No stream, no hole, no signal:
> on the receiving side nothing has happened.**
>
> ⛔ **So the client cannot notice it, and cannot ask for the keyframe.** If the server does not
> produce it **by itself**, the picture is wrecked **forever and in silence** — with a long GOP none
> arrives any more on its own. It is defect **B-18**, found on 13 Aug 2026.
> ⇒ ⭐ **This is the reason why the obligation of §5.2 — «when the server abandons a delta it MUST send a keyframe as soon as it can, without waiting for the client to ask for it» — is not a prudence: in this
> case it is the only thing that exists.** The client has no question to ask.

### 5.2 ⛔ The price of abandonment, and how it is paid

*Added on 9 Aug 2026, and it is the design defect the census found — not a
writing gap.*

The video is compressed **with prediction between frames**: a *delta* frame is the difference from
the previous ones. Abandoning one, or losing one, does not ruin **that** frame: it ruins **all
the ones that come after**, until a **keyframe** arrives — which decodes on its own.

§5.1 allows abandonment and said neither how a keyframe is recognised, nor how one is
asked for. The two things, and the first costs **zero bytes**:

1. ⛔ **the type of the frame is said by the header**: `0x0301` is a **keyframe**,
   `0x0302` a **delta** (§6.2). The `tipo` field was already there and its values were not defined;
2. ⛔ **the client asks for a keyframe** with `RICHIEDI_CHIAVE` (`0x000D`, §7.1) on the control
   channel.

**The rules:**

- ⛔ **the first frame the server sends after `SESSIONE` MUST be a keyframe**
  (`0x0301`). ⚠ Without this line a delta at the opening is conforming, and the client has no way to
  notice it: there is no hole in the sequence of `numero` values, and the decoder raises no
  errors. The symptom would be *«the desktop appears in pieces»*, and it would name neither the protocol nor
  the keyframe;
- ⛔ **and the same holds at every canvas change**: the first frame sent at the **new size**,
  after a `TELA(ADATTATA…)` (§7.1), **MUST** be a keyframe (`0x0301`) — and **MUST** be a
  *true* keyframe, that is carry with it everything needed to decode it on its own: for HEVC its
  VPS/SPS/PPS in front of the IDR. ⚠ Without this line a delta at the new size is **conforming**, and the
  client has no way to notice it: there is no hole in the `numero` values, and — `[M]` 12 Aug 2026,
  Chrome 151 on Linux with VA-API, bench `banchi/02-pagina-tela-*` — **the HEVC decoder raises
  no error**: it keeps emitting frames at the **old** size and paints
  a wrecked picture, different at each run. The symptom would be *«the desktop tears when I resize the window»*, and it would name neither the protocol nor the canvas. ⛔ And the same test on
  **AV1** gives `EncodingError` on Chrome and on Firefox `[M]`: ⇒ **the rule is needed because on the
  main codec the symptom is silent**, and a rule is not written on the codec that behaves well;
- ⛔ **and the client reconfigures the decoder on the first KEYFRAME at the new size, not on the
  `TELA`.** ⚠ *Without this line the two cures of 12 Aug contradict each other on the same frame:
  §6.2 says that a frame in flight at the previous size **MUST** be accepted and painted,
  the line below says that one at the wrong size **is thrown away** — and whoever had reconfigured
  on the `TELA` (the natural reading of §7.1, «the canvas in force **after** this message») would
  find the two rules commanding the opposite. The document did not say **anywhere**
  when to reconfigure, and the two readings were both conforming and diverged on the wire. Finding
  **P10**, found by applying the cure of a few hours before.* ⭐ And it costs zero: `[M]` the true keyframe works
  **both** reconfiguring **and** without;
- ⛔ the client, for its part, **MUST NOT** hand to the decoder a frame whose size
  is neither the one the decoder is configured for **nor the one tolerated by §6.2**: it throws it away and
  treats it as a hole. ⚠ And it is not an extra prudence: `[M]` a `VideoDecoder` reconfigured at the new size demands a keyframe
  (`DataError: a key frame is required after configure()`), so without the line above that
  keyframe would never arrive and the canvas change would cost a `RICHIEDI_CHIAVE` and a freeze
  **every time**. ⭐ With the line above, `[M]` the same keyframe works **both** reconfiguring
  **and** without: 8 cells out of 8 on HEVC and on AV1, on Chrome and on Firefox, in both directions;
- ⛔ the server **MUST NOT** abandon a **keyframe**. Abandoning the cure is not a cure;
- ⛔ when the server abandons a delta, it **MUST** send a keyframe **as soon as it can** —
  without waiting for the client to ask, because the client notices it one network round trip later.
  ⭐ **And this obligation is not a prudence: it is the only cure we have** `[S]` — on a missing delta
  the decoder **raises no error**, it merely produces pictures more and more
  wrecked until the next keyframe. `[?]` The real alternative would be **temporal
  sub-layers**, which allow throwing away certain frames without breaking anything: whether Intel's `EncSliceLP`
  can produce them — ✅ **MEASURED on 22 Aug 2026, and it is NO**: `[M]` the driver does not
  declare `EncRateControlExt` on **7 profiles out of 7**, while it declares it for **VP9 on the same
  entrypoint** and for H.264/HEVC on **AMD `EncSlice`** — ⭐ two positive controls; and in the bytes that
  come out **6 cells out of 6** give `sps_max_sub_layers = 1` with all `temporal_id = 0`.
  ⇒ ⭐ **«Every abandonment costs a keyframe» stays in force, and now it has a measurement under it instead of
  a `[?]`.** ⚠ And the nearby road is closed by **delay**, not by bandwidth: `[M]` with `-bf 1`
  **59 droppable pictures out of 120** come out at unchanged quality (−0.065 dB) and **−16 % bandwidth**, ⛔ but
  **67 ms of reordering** — on its own beyond the 50 ms given to *the whole* of our piece. `[?]` It stays open
  whether a VA-API encoder written by us could build them all the same: `EncPackedHeaders = 0x1f`
  says that the headers are packed by **the application**. 📖 `fasi/08-l-anello.md` §4-D;
- ⛔ the client **MUST** send `RICHIEDI_CHIAVE` when it notices a **hole** in the sequence
  of `numero` values, or when the decoder refuses a frame;
- ⛔ until a keyframe arrives, the client **MUST NOT** show frames it knows to be incomplete:
  it keeps the last good one. A wrecked picture is worse than a picture frozen for a tenth of a second;
- ⚠ the server **MAY** ignore a `RICHIEDI_CHIAVE` that arrives within **200 ms of the last keyframe
  it sent** — ⛔ not of the last request received, and the difference is not a nuance:
  counting from requests, two insistent clients move the clock forever and the keyframe never
  leaves. During a burst of losses requests arrive by the dozen, and every keyframe costs
  ten times a delta: indulging them would worsen exactly the condition that caused them.
  ⭐ **It is exception 5 of §3, and it is declared there.**
  ⛔ **The grace holds only for duplicates** (22 Sep 2026): a `RICHIEDI_CHIAVE` whose
  `ultimo_numero` is equal to or newer than the last keyframe sent says that the client has already
  decoded that keyframe — the hole came after — and the server **MUST** accept it. `[M]` Ignoring it
  left the page frozen forever with a heavy video, on Firefox and on Chrome;
- ⛔ the client sends **one** `RICHIEDI_CHIAVE` per hole; if the keyframe does not arrive within **1 s** it
  sends another (22 Sep 2026). One per second, not one per frame: the spiral stays closed;
- ⛔ as long as a **keyframe** is still in the output queue, the server does **NOT** abandon the deltas that
  come behind it because of the queue threshold (§5.1): they would not shorten it, and every abandoned delta
  opens a hole that asks for another keyframe (22 Sep 2026, `[M]` the spiral seen with a 4K video).

⚠ **And a consequence that touches phase 9**: if the line is so bad as to cause abandonment
continuously, the remedy is **not** sending keyframes continuously — it is **lowering the frame rate**,
as `SPECIFICHE.md` §8.3 says. A keyframe for every abandoned delta is the spiral.

### 5.3 Audio: the format is fixed, not negotiated

*Added on 9 Aug 2026: «Opus, with PCM as the base» says the codec and does not say the format, and two
implementations that choose two different sample rates produce a noise that looks like a network
defect.*

| | |
|---|---|
| sample rate | **48 000 Hz**, always, for both codecs |
| channels | **2**, interleaved |
| **Opus** | one Opus packet per datagram, blocks of **20 ms** |
| **PCM** | samples **s16, little-endian**, ⛔ **5 ms per datagram** — 480 samples, **960 bytes**, which with the 12 of the header make **972** |

> ### ⛔ Corrected on the evening of 9 Aug 2026 — finding **R1.1**, the most serious of the review
>
> This line said **20 ms for PCM too**: 1920 samples, **3840 bytes**, plus 12 of
> header = **3852**. ⛔ A QUIC datagram **cannot be fragmented** — it must fit in a single
> packet — and on a real path the available payload is **~1200 bytes** `[S]`.
>
> **So PCM audio would never have left, on any network.** And the damage was double, because
> §4.3 makes PCM **the positive control of Opus**: the day Opus is not negotiated, one
> falls back on a road that does not exist — and the bench would look for the defect in Opus.
>
> ⚠ **The form of the error is that of `LEZIONI.md` §2.2**, where the bench counted the blocks while
> the audio was full-scale noise. Here not even the noise would have arrived.
>
> ⭐⭐ **MEASURED — `[M]` 17 Aug 2026, and the estimate was optimistic by a fifth.**
>
> | | Chrome 151 | Firefox 140esr |
> |---|---|---|
> | right after `ready` | **1024** bytes | **1024** bytes |
> | after 800 ms | **1024** bytes | ⭐ **1214** bytes |
>
> ⇒ The PCM of this paragraph (972 bytes, header included) **fits**, but on Chrome by
> **52 bytes** — that is by less than 6 %. ⛔ The line that opened the `[?]` — *«if the number were lower than 972, PCM goes down further»* — **does not trip**, and the 5 ms stay.
>
> ⚠ And the two engines give neither the same number nor the same number over time: Firefox starts from 1024
> and **grows to 1214** once it has measured the path. ⇒ Whoever sized the blocks by reading
> `maxDatagramSize` **only once** would take the worst number without knowing it.
>
> `[?]` **The non-local path stays open**: this measurement is on a local network, wired. On a mobile
> network the path may carry less, and PCM is the road **without margin** — precisely the one
> fallen back on when Opus is not negotiated. The probe is `banchi/07-b40`.

⛔ **The little-endian of PCM is the only exception to the network order of §6, and it is deliberate**: they are
a payload, like the bytes of HEVC, not a protocol field. Written here because an undeclared exception
is a silent divergence between two implementations.

⚠ The volume **does not travel**: it belongs to the session and is at maximum (invariant I5,
`SPECIFICHE.md` §10).

### 5.4 The clipboard: the limits

| | |
|---|---|
| ceiling of one transfer | **1 000 000 bytes** ⚠ — not 1 MiB: the message that carries it has six bytes of framing and four of length, and a ceiling equal to that of the message (§6.1) would make **text exactly as large as the ceiling illegal** |
| larger text | ⛔ **it is not announced at all**, and the sender **writes it in the log**. It MUST NOT be truncated: truncated text pasted in a terminal is worse than missing text |
| type | ⛔ only `text/plain;charset=utf-8`, and the text **MUST** be valid UTF-8 |

### 5.5 The cursor: the limits

| | |
|---|---|
| maximum size | **256×256** |
| format | **premultiplied BGRA**, row by row without padding: `larghezza × altezza × 4` bytes |
| hidden cursor | ⛔ `larghezza = 0` **and** `altezza = 0`, both, and no image bytes. Only one of the two at zero is `ERRORE_PROTOCOLLO` |
| the hotspot | ⛔ **MUST** be inside the image: `0 ≤ attivo_x < larghezza`, `0 ≤ attivo_y < altezza`. ⛔ **Only exception, the hidden cursor**: with `larghezza = altezza = 0` the range is empty, and then `attivo_x` and `attivo_y` **MUST** be `0`; any other value is `ERRORE_PROTOCOLLO`. ⚠ *The type stays `i16` and the line «may be negative» has fallen: without a range, `attivo_x = -32768` was lawful according to every line of the document, and two clients would have drawn the pointer in two different places (finding **R1.21**)* |

> ⛔ *The exception is from 10 Aug 2026, finding **R11.11**, and it is 🔸 derived: it is corrected without
> discussion.* The row above declares `larghezza = 0` **and** `altezza = 0` **mandatory** for the
> hidden cursor; the row below demands `0 ≤ attivo_x < larghezza`, and with `larghezza = 0`
> that range is **empty**: no value of an `i16` satisfies it. ⛔ **A `CURSORE_FORMA` of a
> hidden cursor always violated the adjacent row, whatever the sender put in it** — and a
> receiver that applied §5.5 to the letter closed with `ERRORE_PROTOCOLLO` every time the
> pointer disappears, with the symptom *«the session drops when I enter a text field»*, which
> names neither the cursor nor the rule.
>
> ⚠ It is the same form as the underscore of §4.3 found by the validator of B4: **a rule that
> forbids a case the document itself defines**. And R1.21 declared it had closed precisely
> this — *«width 0 with height other than 0, and a hotspot without a range»*: the range
> had been added **without excepting the case the adjacent row makes mandatory**.

---

## 6. The message format

**Byte order: network (big-endian).** No variable-length field outside those
declared with an explicit length.

### 6.0 The elementary types

*Added on 9 Aug 2026. They were used throughout the document and defined nowhere.*

| Type | | |
|---|---|---|
| `u8`, `u16`, `u32`, `u64` | unsigned integers, big-endian | |
| `i16`, `i32` | signed integers, **two's complement**, big-endian | |
| **stringa** | `u16 lunghezza` + exactly `lunghezza` bytes of **UTF-8**, **without terminator** | ⛔ invalid UTF-8 is `ERRORE_PROTOCOLLO`. An empty string is `lunghezza = 0` |
| **elenco** | `u16 quante` + the elements in a row | |

⛔ **No field is aligned and no padding is admitted.** Fields are read and written in
sequence, one after the other. An extra byte that «makes the numbers add up» in a C structure is the exact
form of the defect corrected in §6.2 on 9 Aug.

⛔ **Every integer has a single meaning of «absent»**, and it must be declared where needed: there are no
implicit sentinel values.

### 6.1 On the reliable channels — control, input, clipboard

```
 0        2        6                    6+lunghezza
 ├────────┼────────┼─────────────────────┤
 │ tipo   │ lungh. │ corpo               │
 │ u16    │ u32    │                     │
```

⛔ `lunghezza` **MUST** be the exact number of bytes of the body. A receiver that reads a
length inconsistent with what the type provides for **MUST** close with `ERRORE_PROTOCOLLO`.

⛔ A message **MUST NOT** exceed **1 MiB**. Whoever announces a larger one violates the protocol.

⛔ **And the length is checked before allocating.** A receiver that allocates `lunghezza` bytes and then
checks has already given away a megabyte to anyone who can write six bytes.

### 6.2 On the video streams

One stream, one frame. No length: **the end of the stream is the end of the frame** —
⛔ **but only if the stream finished with a FIN**.

> ⛔ *Two words added on the evening of 9 Aug 2026, finding **R1.7**, and without them the document
> was broken exactly where §5.1 allows abandoning.* The server opens the stream of frame 101,
> sends the header and 40 KB out of 60, then **resets** it because 102 has left. The client has in
> hand 40 KB and a «finished» stream: handing them to the decoder it gets a refusal or — worse —
> half a picture. **An abandoned frame and a complete one looked the same**, and it is
> error form **E8**.

⛔ **The rule, in two lines:**

- a stream closed with **FIN** carries a **complete** frame;
- a **reset** stream (`RESET_STREAM`) carries an **incomplete** frame: the client **MUST**
  throw away what it has received, **MUST NOT** hand it to the decoder, and **MUST** treat it
  as a hole (§5.2);
- a stream closed with **FIN before the 28 bytes** of the header is `ERRORE_PROTOCOLLO`: it is not a
  short frame, it is a length that does not add up (§3);
- ⛔ **and an abandoned frame may not present itself as a stream at all**: if the server has
  consumed the `numero` and abandoned **before a byte left**, the client sees no
  stream — it sees a **hole in the sequence of `numero` values**. It is **form B** of abandonment, and it must be
  treated as a hole exactly like the reset (§5.1, the box of the two forms).

```
 0        2        4        8        12       16       24       28   28+…
 ├────────┼────────┼────────┼────────┼────────┼────────┼────────┼─────┤
 │ tipo   │ codec  │ largh. │ altezza│ numero │ istante│ input  │ dati│
 │ u16    │ u16    │ u32    │ u32    │ u32    │ u64    │ u32    │     │
```

⛔ **The header is exactly 28 bytes, without padding**, and the frame data start
at offset 28. No field is aligned: it is read and written in sequence.

> ⚠ *Corrected on 9 Aug 2026, before any implementation.* The drawing gave `… 24 │ 32`,
> that is eight bytes to a field declared `u32`: four undeclared padding bytes, and two
> implementations that could guess the same without anyone noticing — the silent
> defect against which this document was written (§0). **28** chosen by the user: padding
> must be justified, and here nothing justified it.

| Field | |
|---|---|
| `tipo` | ⭐ `0x0301` **keyframe**, `0x0302` **delta frame** (§5.2). Other values: `ERRORE_PROTOCOLLO` |
| `codec` | `1` = HEVC, `2` = AV1, ⭐ `3` = **H.264** (since 20 Aug 2026). **MUST** be the one negotiated in §4.3. ⛔ **A number is never reused**: `2` stays AV1 even now that AV1 is no longer negotiated, because an old client that heard «2» and received something else **would paint garbage without an error**. ⚠ And the maximum defined number is in **a single place** in the code (`RCP_CODEC_VIDEO_MAX`): the day 3 came in, three different guards carried the number written by hand and one was left behind — **every H.264 frame was thrown away in silence** |
| `largh.`, `altezza` | the size of **this** frame. ⛔ In RCP/1 they **MUST** be the **canvas in force** — the one granted in `SESSIONE` (§4.5), **or** the last one granted by `TELA` if meanwhile it has been adapted (§7.1) — and whoever receives others closes with `ERRORE_PROTOCOLLO`: the client rescales to the **view**, not to the canvas (`SPECIFICHE.md` §6.1). The field exists all the same because on the day it were decided to encode smaller when the window is small — `DECISIONI.md` §5.0-ter, which is a `[?]` deliberately outside the model — **the protocol does not change**: this row would change |
| `numero` | ⛔ counter of the frames **the server decides to send**, which grows by one for each — **including those it then abandons**, and ⛔ **NOT** for those it does not send at all. ⚠ *It said «of the **captured** frames» and at the same time «that the server decides to send»: **two readings in the same sentence**, and at phase 3 they separate — lowering the frame rate when the line does not carry (I1, §8.3), the first reading would open **a hole for every skip**, hence a `RICHIEDI_CHIAVE` for each, that is **the spiral §5.2 exists to avoid** precisely when the line is bad. Corrected on 12 Aug 2026, finding **P16**, found while writing the product.* A hole in the sequence is therefore normal and **means something**: it is the signal on which §5.2 has a keyframe asked for. ⛔ **The first frame of a session carries `numero = 1`, and `0` is reserved**: it means «no frame», which is the meaning §7.1 gives it in `RICHIEDI_CHIAVE`. ⚠ It is the same convention as the `id` of input (§7.3), and for the same reason: without it, `RICHIEDI_CHIAVE(0)` means two things and the server cannot choose — that is the implicit sentinel value §6.0 forbids. ⛔ **And at the wrap of the counter `0` is skipped**: the arithmetic is modulo 2³², a session can last more than one wrap, and from `0xFFFFFFFF` it goes to **`1`** — without this line the reserved value would come back into circulation by itself |
| `istante` | microseconds of the **server's monotonic clock** at capture |
| `input` | ⭐ **the identifier of the last input injected before capture**; **0** if none |

⛔ **The ceiling binds the sender first of all**: the server **MUST NOT** produce a frame
longer than **16 MiB**. If encoding produced a larger one, it **MUST** re-encode it at
lower quality and **write it in the log** — never send it. Whoever receives a longer one closes
with `ERRORE_PROTOCOLLO` instead of continuing to accumulate.

> ⚠ *The first half is from the evening of 9 Aug 2026, finding **R1.23**: the ceiling bound only the
> **receiver**, that is it was a punishment for whoever suffers.* A 7680×4320 canvas is lawful (§4.5) and the
> desired depth is 10 bits: a keyframe of a complex scene at that size can exceed
> 16 MiB. The client would have detached the session because the server did something §4.5
> allows it — and §5.2 also forbids it to abandon keyframes, so it had no way out.
>
> ✅ **MEASURED on 22 Aug 2026** — `[M]`, 📖 `fasi/08-l-anello.md` §4-D:
> - ⭐ **at the user's canvas the ceiling is unreachable**: 2560×1080, **404 true keyframes**, maximum
>   **21 433 bytes = 0.13 %**, margin **782×**. Not even uniform noise gets there (15.1 %);
> - ⛔ **at 7680×4320 it really breaks through**: uniform noise **28.9 MiB, 8 out of 8** above the ceiling, and
>   strong grain reaches **94.9 %**. *(The measurement of the software fallback, `libx264` going through
>   libavcodec, no longer holds after phase 18.)*;
> - ⚠ and the **10 bits here are eight promoted** — `DECISIONI.md` §2.3-ter. Indeed `[M]` the label
>   `main10` at 8K costs **933 bytes LESS** than `main`: it carries no information that is not there;
> - ⛔⛔ **the form defect however is not the one believed.** The **re-encoding ladder is
>   one rung short** — the last attempt leaves **16.654 MiB**, the fourth would have made it,
>   and it is lost by **4 %** — and when it gives up the encoder **throws away the frame even if it is
>   a keyframe**, which **§5.2 forbids**. ⇒ It is the spiral: the client stays broken, and every
>   `RICHIEDI_CHIAVE` costs three re-encodings that produce nothing. ⭐ The cure already has its
>   number: `[M]` **QP 51 gives 1.771 MiB at 8K**, so a keyframe **always fits**.

⛔ **The order, and who puts it back in place.** The streams are independent, so frames
**can arrive out of order**. The client:

- **MUST** discard a frame whose `numero` is **earlier** than the last one already handed to the
  decoder;
- **MUST** treat `numero` as **modulo 2³²** arithmetic, comparing signed differences —
  at 60 frames per second the counter wraps after two years and two months, and a session can last
  longer;
- **MUST** recognise a **hole** and ask for a keyframe (§5.2).

⛔ **And there is the opposite direction, which is the fifth of the same family**: a frame at the **new**
size can arrive **before** the `TELA` that grants it — the `TELA` travels on the control
channel, the frame on a stream of its own, and **nothing orders their delivery**. ⇒ The client that
received a size that «has never been in force» would close **a session in which nobody has
erred**.

⛔ **The client MUST NOT close: it holds back the frame**, and writes it in the log. ⭐ **And how long
it holds it back is not a number: it is a condition** — as long as there is an `ADATTA_TELA` that **the
client has sent** and to which no `TELA` has yet answered. Once that `TELA` has arrived, the
held-back frame **is judged again** against the canvas that `TELA` declares in force, and from there it is a
frame like all the others: first the order rule, then the size rule. ⛔ **And if
no `ADATTA_TELA` is without answer nothing is held back**: a size the client has
no reason to expect is `ERRORE_PROTOCOLLO` at once.

⚠ **And the `TELA` necessarily arrives**, which is the reason this is an end and not an open
wait: §7.1 imposes *«to every `ADATTA_TELA` the server MUST answer with a `TELA`, successful or not»*,
and the control channel is **only one, reliable and ordered** (§4.2) ⇒ the n-th `TELA` answers
the n-th `ADATTA_TELA`, and whoever drags a window sends two without the count getting lost.
⛔ A `TELA(RIFIUTATA)` closes the wait as much as a `TELA(ADATTATA)`: the held-back frame is judged again against
the canvas that remained in force, and as a rule **it is `ERRORE_PROTOCOLLO`** — the server has sent a size it
never had.

⭐ **And the quantity is «a request in flight», not «the size the client asked for»**: §4.5 says
that *«the granted canvas can be different from the one asked for»* — on KWin < 6.8 it is the normal road
(`SPECIFICHE.md` §6.3) and the negotiation of §6.4 grants the mode the compositor **has**. ⇒ A
client that held back only the numbers it named would close a session in which the server has
done exactly what §7.1 allows it. ⚠ It is the same quantity as **P20** — *what the
client has sent itself*: local, monotonic, independent of delivery.

> ⚠ *This paragraph said «holds back **until it can decide**», and beside it carried a box
> `[?]` that declared open the question «until when». The product closed it with **eight
> frames** — an observable bound instead of a clock, which was already the lesson of P13, ⛔ but still
> **a substitute quantity**. Closed on 13 Aug 2026, finding **P21**. ⭐ And the first cure
> proposed — «the size the client named» — was **failed by a case**: §4.5 allows
> the server to grant a canvas different from the one asked for, so it would have been the eighth draft.*

> ### ⛔ And holding back **has no ceiling in bytes** — the line was missing
>
> *13 Aug 2026. The paragraph above says until **when** one holds back, and does not say **how much**.
> They are two different questions, and the second had no answer anywhere.*
>
> ⛔ **The end condition is correct and not enough.** §7.1 obliges the server to answer every
> `ADATTA_TELA` with a `TELA`, successful or not — and it is the reason the condition «as long as an `ADATTA_TELA` is without answer» **ends**. ⛔ But a server that **does not answer** does not violate a
> rule the client can enforce: it makes the client's queue grow **without limit**, and the
> conforming client keeps holding back as long as memory holds. ⇒ The defect is not the client's:
> **it is a line missing from this document.**
>
> ⇒ **The two rules:**
>
> - ⛔ the client **MUST** have a ceiling on what is held back, and exceeding it is **NOT `ERRORE_PROTOCOLLO`**:
>   the server has not done anything wrong in a way the client can prove. The oldest is thrown away,
>   **it is written in the log**, and it is treated as a hole (§5.2). A freeze with
>   a log line is better than a session that runs out of memory in silence;
> - ⛔ **and the ceiling is counted in FRAMES, not in requests in flight.** ⚠ The paragraph above did not
>   say it, and they are two different quantities: the requests in flight say **whether** one holds back, the
>   frames say **how much**. ⭐ And a frame is counted **only once even if it is
>   judged again twice** — a held-back frame that does not resolve at the first `TELA` and stays waiting for the
>   second **is not two frames**. *The product already did it right; the document did not say it.*
>
> ⏳ `[?]` **What the number is is not decided here**: it depends on the device's memory and on the weight
> of a keyframe (§6.2 admits 16 MiB), and choosing it at random would redo the mistake of §1.13 —
> a substitute quantity in place of the true one. ⛔ But *«there is no ceiling»* is not an answer, and
> it was what the document said by keeping silent.

⛔ **And the order rule applies BEFORE the size rule**: a frame whose `numero`
is earlier than the last one already delivered **is discarded**, and its size is not even looked at.
⚠ *Without this precedence the two lines of this same section contradict each other, and the more
severe wins on a scene in which nobody has erred: the keyframe that closes the tolerance **overtakes** the
frames in flight — not by chance, but because the old one is **the biggest** (§5.2 forbids
abandoning a keyframe) and the new one is smaller. Finding **P14**, 12 Aug 2026, and the same
family had already moved one step three times: **P8 → P11 → P13 → P14**.*

⚠ **The canvas change and the frames in flight.** After receiving a `TELA(ADATTATA)` (§7.1) the
client **MUST** accept the frames whose size is **a canvas that has been in force since
the queue started to drain**, painting them rescaled to the view and writing it in the log.
⛔ **And the tolerance does not end by the clock: it ends when the first keyframe at the new
size arrives**, which §5.2 guarantees to it. From that frame on an old size is
`ERRORE_PROTOCOLLO`; and **at once** so is a size that has never been in force in that window
⛔ **and that no `ADATTA_TELA` without answer can still grant**: if there is one, the frame
**is held back** instead of causing a close (the paragraph above).

> ⚠ *It said «the **previous** canvas», in the singular, and ⛔ **whoever drags a window sends two**:
> 1920×1080 → `TELA(1600,900)` → `TELA(1280,720)`, and the keyframe opened before everything — the
> biggest, the slowest, and the one §5.2 forbids the server to abandon — carries 1920×1080, which is
> neither the one in force nor the previous one. The healthy session dropped all the same, **one step further**
> than the scene the cure had just closed. Corrected on 12 Aug 2026, finding **P11**.*
⭐ It is the **sixth** exception declared in §3, and it is the third written for the direction in which it was missing: §7.1
already gives it to the input coordinates, for the same reason — the canvas change is the only moment in
which the two sides legitimately have two different truths. ⛔ Without it, a conforming client **kills a
healthy session**: the streams are independent, the frame opened before the `ADATTA_TELA`
reached the server legitimately carries the previous size, and §5.2 forbids the server to abandon
a keyframe — that is to clear the pipe of precisely the biggest frames, which are the most likely
to be in flight. ⇒ **On the server side it is not curable**, and that is why the line is the client's.

> ⛔⛔ *And the first draft of this line said «**for one second**», with a clock — corrected two
> hours later, finding **P13**. The reason is that **the second was the wrong quantity**: what
> must drain is a **queue**, and how long an already-in-flight frame takes depends on **bandwidth**,
> not on the clock. A 1920×1080 keyframe can weigh a few MiB (§6.2 admits 16) and on a bad
> line — which is **inside** the model, the declared minimum is 480p at 25 — it arrives **after** the
> second. ⇒ The client would have closed on a frame sent when it was lawful, and which §5.2 forbade the
> server to abandon: it is not only a healthy session that drops, it is invariant **I1** — «never detach» — broken **because the line is slow**, that is in the exact condition I1 exists to
> protect. ⭐ And lengthening the second would have moved the defect instead of removing it: the
> tolerance ends on a **fact observable on the wire** — the first keyframe at the new size — which
> §5.2 guarantees exists.*
>
> ⚠ *Added on 12 Aug 2026, defect **D14**, and the label is neither of the two this
> document used: it is not a **double reading** and it is not a **derived rule** — it is an
> **internal contradiction**. Two conforming and careful implementations here **do not diverge**:
> they produce the same byte, the closing, and it is wrong. ⛔ It is the species no comparison between two
> implementations can find, and it is the same one the first draft of **P5** had for two hours
> that morning.*

⚠ **What the `input` field really says**, and it must be written here so that nobody attributes more to it:
it says which input had been **injected**, not which had been **drawn**. That the
compositor had already rendered it is guaranteed by nobody. It is a useful and free estimate — not the
measurement of the delay. That is given by the closed-loop bench of `DECISIONI.md` §2.6.

⚠ **And `istante` is not a time of day**: it is a monotonic clock that starts from an arbitrary point. The client
**MUST NOT** compare it with its own: only with other `istante` values of the same server.

### 6.3 On datagrams — audio

```
 0        2        4        12                12+…
 ├────────┼────────┼────────┼──────────────────┤
 │ tipo   │ codec  │ istante│ campioni         │
 │ u16    │ u16    │ u64    │                  │
```

| Field | |
|---|---|
| `tipo` | `0x0401` — the only one defined in RCP/1 |
| `codec` | `1` = Opus, `2` = PCM (§5.3) |
| `istante` | microseconds of the server's monotonic clock, of the **first** sample of the block |

One datagram, one block of Opus (or of PCM). No retransmission, no reordering: the receiver
discards datagrams arrived late relative to those already consumed.

⛔ A datagram shorter than 12 bytes, or with a `tipo` other than `0x0401`, **is discarded and written
in the log**: ⚠ and it is the second exception declared in §3, because a datagram is by definition
unreliable and closing the connection for a corrupted packet would be a punishment of the network,
not of the sender.

---

## 7. The messages

### 7.1 Control

| Type | Name | Direction | |
|---|---|---|---|
| `0x0001` | `CIAO` | → | version and capabilities of the client |
| `0x0002` | `ECCOMI` | ← | version and capabilities of the server |
| `0x0003` | `CREDENZIALI` | → | user, password |
| `0x0004` | `AMMESSO` | ← | |
| `0x0005` | `RESPINTO` | ← | reason |
| `0x0006` | `ATTACCA` | → | canvas, layout, view |
| `0x0007` | `SESSIONE` | ← | state, granted canvas, desktop |
| `0x0008` | `VISTA` | → | the view has changed: new width and height |
| `0x0009` | `DISPOSIZIONE` | → | the keyboard layout has changed |
| `0x000A` | `CURSORE_FORMA` | ← | shape and hotspot of the pointer |
| `0x000B` | `ADATTA_TELA` | → | «fit the desktop to this window» — ⚠ from our client **only at attach and reattach** (§7.1); the protocol admits it with the session open from anyone |
| `0x000C` | `CONGEDO` | ↔ | reason |
| `0x000D` | `RICHIEDI_CHIAVE` | → | ⭐ *new, 9 Aug*: a keyframe is needed (§5.2) |
| `0x000E` | `TELA` | ← | ⭐ *new, 9 Aug*: the outcome of `ADATTA_TELA` |
| `0x000F` | `BANCO_MARCA` | → | ⭐ *new, night of 9 Aug*: **bench function** — changes the mark, with a known delay (§7.5) |
| `0x0010` | `BANCO_ESITO` | ← | ⭐ *new, night of 9 Aug*: the outcome of `BANCO_MARCA` (§7.5) |
| `0x0011` | `TERMINA_SESSIONE` | → | ⭐ *new, 15 Aug*: **the user wants to log out** — the graphical session ends and its programs close (§7.6) |

**The bodies** (`CIAO`, `ECCOMI`, `CREDENZIALI`, `AMMESSO`, `RESPINTO`, `ATTACCA`, `SESSIONE` are
in §4.3-4.5):

```
VISTA
 ├── u32 larghezza
 └── u32 altezza

DISPOSIZIONE
 └── stringa disposizione            (the form is that of §4.5)

ADATTA_TELA
 ├── u32 larghezza
 └── u32 altezza

TELA
 ├── u8  esito        1 = ADATTATA, 2 = RIFIUTATA
 ├── u8  motivo       0 if adapted; otherwise:
 │                      1 = COMPOSITORE_INCAPACE
 │                      2 = MISURA_FUORI_LIMITI
 │                      3 = NON_ORA
 ├── u32 tela_larghezza      ⚠ the canvas in force AFTER this message
 └── u32 tela_altezza

RICHIEDI_CHIAVE
 └── u32 ultimo_numero        the last frame decoded, 0 if none

CONGEDO
 ├── u8      motivo           §8.2
 └── stringa dettaglio        for the log, not for the user; may be empty
```

⛔ **`DISPOSIZIONE` with the session open: a well-formed but unknown layout does NOT close the
session.** The server **MUST** write it in the log and **MUST** keep the previous one in force.
⚠ It is different from `ATTACCA` (§4.5), where the farewell `SESSIONE_NON_SERVIBILE` is right because there is
no session to save: here the previous keyboard still works, and taking away from the user the
open work would cost **more than the fault** (`SPECIFICHE.md` §8.3, «never detach»).

⚠ `VISTA` **MUST NOT** make the canvas change, and ⛔ **in RCP/1 it does not even change the size of what
is encoded**: the frames stay at the size of the canvas and the client rescales
(`SPECIFICHE.md` §6.1). It serves two things — choosing how many bits to spend, because a small window
looked at on a small screen does not deserve as many as a large one; and making free the
day `DECISIONI.md` §5.0-ter were closed. The only message that changes the canvas is
`ADATTA_TELA`.

> ⛔ **Here it also said «and it is an explicit choice of the user», and since 15 Aug 2026 it is no
> longer true.** `DECISIONI.md` §5.0-sexies — decided by the user on 14 Aug — makes the client ask for
> **the canvas of its own window at the attach of every session**, by itself. ⇒ `ADATTA_TELA` remains
> the only message that changes the canvas, but it is no longer certain that behind it there is a finger: there may be
> the attach. ⚠ For the referee nothing changes — the message, the checks and the answer are the
> same — and the line is corrected because **a document that describes a client that no longer exists
> stops being the referee**.
>
> ### ⛔⛔ And SINCE 17 AUG 2026 THERE IS **NEVER** A FINGER BEHIND IT — `DECISIONI.md` §5.1-bis
>
> Live resizing has left the product (*«non voglio mettere delle eccezioni nel
> progetto»*): **our page sends `ADATTA_TELA` only at attach and reattach**, and
> resizing the window produces none.
>
> ⛔⭐ **But this is a choice of OUR client, not a rule of the protocol, and the two are not
> confused**: RCP/1 keeps admitting `ADATTA_TELA` **at any moment with the session
> open**, and the server **MUST** keep answering with a `TELA` to anyone who sends it. ⚠ A
> referee that wrote «the client does not send it during the session» would declare **non-conforming
> a conforming client** — and the first to lose out would be ours, the day the decision
> changed. The line is here because it describes **who sends it today**, not what is lawful.
>
> ⏳ **And there remains a line to write**, found while refuting on the night of 15 Aug: *what the
> server does when the stage changes size **without any `ADATTA_TELA` having asked it*** — a
> remount of the graphical session after a crash, for example. §6.2 gives the client only one way to
> accept an unexpected size (holding back while a request is without answer), so an unsolicited `TELA`
> **makes a healthy session close**: the server today does not send it, and instead ASKS
> the stage to go back to the canvas in force, with a growing wait. It works, ⚠ but it is a rule of the
> product the referee does not name.
>
> ### ⭐ THE LINE, WRITTEN ON 22 SEP 2026 — and the request is not always enough
>
> ⛔ The server **MAY** send **one** unsolicited `TELA(ADATTATA)`, and **only** when in that
> session **no frame has yet left**: there the client has not seen one pixel at that
> canvas, has none in flight, and there is no race between streams to referee — the `TELA` is
> the only truth it will ever have had. ⛔ **After the first frame it stays forbidden**, and the rule
> above holds: one asks the stage, with a growing wait.
>
> ⚠ *Why it is needed, and it is not an abstraction*: `[M]` 22 Sep 2026, manual test by the user on KDE.
> The server restarts, the Plasma session **outlives** it (I4) with the stage at 2544×926, and the client
> comes back from a window of another size asking for 2560×962. The table of the stages' canvases
> lives in the process ⇒ with the restart it is reset, and the fallback of §4.5 — «what the stage **has** is granted» — has nothing to grant. Canvas in force 2560×962, stage 2544×926, §6.2 forbids
> sending a frame of different size: **black screen forever**, because **KWin `--virtual`
> does not resize** and the request cannot succeed either today or in an hour. ⇒ «Asking the stage»
> is a cure that presupposes a stage capable of obeying, and this line says what to do when it
> is not.

> ⚠ *Clarified on 9 Aug 2026, and it was not a nuance.* This line said «it serves the server to know **at what size to encode**», and there are two entries of `DECISIONI.md` that contradict each other
> on the same point: §5.2 says that *«the encoder works at the size of the window, not of the canvas»*, §5.0-ter says that *«the server keeps encoding the whole canvas and the client shrinks it»* and puts the opposite **deliberately outside the model**, as `[?]`. The
> second wins, because it is the one that holds together with `SPECIFICHE.md` §6.1 and §6.3 — where the fallback on
> KDE *«does not cost one more line, because it is the same code as the point during the session»*, and
> that code is the **rescaling in the client**. The correction is in `DECISIONI.md` §5.2.

⛔ If the compositor cannot resize, the server **MUST** answer `ADATTA_TELA` with
`TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, and the client **MUST** show the item as off. It MUST
NOT pretend it succeeded.

⛔ **To every `ADATTA_TELA` the server MUST answer with a `TELA`**, successful or not. A silence
leaves the client waiting forever for an answer that will not arrive, and the symptom is
«the application has hung».

⛔ **The view does not have the constraints of the canvas**, and it must be said because the previous line said the
opposite: any size from **1×1 upwards** is lawful, odd included.

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.17**.* Here it was written that the view must
> be between 320×240 and 7680×4320 **with even sides**, that is the limits of the canvas — and the limits of the
> canvas exist for a reason that **does not apply** to the view: the blocks of the encoder. In
> RCP/1 the view **touches no encoder** (this same section says so two lines above).
>
> The concrete case: the user narrows the browser window to 300 pixels, or opens the page
> side by side on the phone. With the old line the client had three choices, all bad — send
> `VISTA(300×800)` and **have the session closed because it resized a window**; lie
> by rounding to 320, which is error form **E2**; or keep silent, and let the server spend bits
> for a view that no longer exists. ⚠ On a phone with scale factor 2.75 no
> rounding is innocent: 393 logical pixels are 1080.75 physical.

⚠ The view has no proportion constraint with the canvas: if the proportions do not match, it is
laid out with bars (`SPECIFICHE.md` §6.2).

⚠ **The canvas change and the coordinates in flight.** After sending `TELA(ADATTATA)` the server
**MUST** accept for **one second** input coordinates valid on the **previous** canvas,
saturating them to the new one and writing it in the log; once that second has passed, they are
`ERRORE_PROTOCOLLO`. ⭐ It is the third exception declared in §3, and it exists because the canvas change is
the only moment in which the two sides legitimately have two different truths: the inputs that left before
the answer arrived are not a defect of the client.

### 7.2 Cursor

`CURSORE_FORMA` carries the shape the client must draw:

```
CURSORE_FORMA
 ├── u16 larghezza          0 with altezza 0 = hidden cursor (§5.5)
 ├── u16 altezza
 ├── i16 attivo_x           the point that «points», inside the image — ⛔ 0 if hidden (§5.5)
 ├── i16 attivo_y
 └── immagine               larghezza × altezza × 4 bytes, premultiplied BGRA
```

⛔ `larghezza` and `altezza` **MUST NOT** exceed 256 (§5.5), and the length of the message **MUST**
be exactly `8 + larghezza × altezza × 4`. A length that does not add up is
`ERRORE_PROTOCOLLO`: it is the case in which «I read what is there and go on» produces a cursor made
of someone else's memory.

⚠ **The position never travels in this direction.** The position of the pointer belongs to the client, which
draws it by itself (`SPECIFICHE.md` §7.1). Here only the **shape** travels, and the delay of one network
round trip on the shape is the accepted compromise.

### 7.3 Input

| Type | Name | |
|---|---|---|
| `0x0101` | `PUNTATORE` | absolute position on the **canvas**, not on the view |
| `0x0102` | `PULSANTE` | which one, pressed or released |
| `0x0103` | `ROTELLA` | axes, in notches |
| `0x0104` | `LETTERA` | a Unicode character |
| `0x0105` | `POSIZIONE_TASTO` | position code, pressed or released |

⛔ **Every input message starts with the same two fields**, and then has its own:

```
 ├── u32 id             increasing, starts from 1.  ⛔ 0 is reserved and means «no input»
 └── u64 istante        microseconds of the CLIENT's monotonic clock

PUNTATORE          + u32 x  · u32 y            coordinates on the canvas
PULSANTE           + u16 codice · u8 premuto   1 = pressed, 0 = released
ROTELLA            + i32 asse_x · i32 asse_y   units of 120 per notch
LETTERA            + u32 carattere             Unicode scalar value
POSIZIONE_TASTO    + u16 codice · u8 premuto
```

| | |
|---|---|
| **the codes of buttons and keys** | ⛔ they are those of **evdev** (`linux/input-event-codes.h`): `BTN_LEFT` = `0x110`, `KEY_A` = `30`. ⭐ It is not a choice of convenience: `libei` — that is the only way we have to inject input into a Wayland compositor — works in evdev, and any other convention would add a translation table that errs in silence |
| **the wheel** | ⛔ units of **120 per notch**, ⚠ and half notches exist: `60` is half a notch and **MUST NOT** be rounded to zero. ⭐ **The sign is MEASURED** *(10 Aug 2026, on Mutter)*: the client sends `+120` when the user turns the wheel **up**, and ⛔ **the server MUST invert the vertical axis** before passing it to `libei` — see the box |
| **the character** | ⛔ a **Unicode scalar value**: from `0` to `0x10FFFF`, excluding the surrogates `0xD800`-`0xDFFF`. Out of range is `ERRORE_PROTOCOLLO` |
| **the identifier** | ⛔ grows by **at least one** at every message, over the whole input channel — not one per type. It is what comes back in the `input` field of the frames (§6.2), and with separate counters nothing would add up |
| **the `istante`** | ⚠ **no rule of this document consumes it**: the delay is measured by the closed loop of `DECISIONI.md` §2.6, and the frame carries back the `id`, not the instant. It stays because it is the only way to know **when the user moved their hand** instead of when the byte arrived, and it serves diagnosis. ⛔ The client writes **true microseconds** and **MUST NOT** make believe in a precision it does not have *(finding **R1.27**)*. ⚠ ⛔ **And the premise of this row was FALSE — corrected on 14 Aug 2026, on a measurement of the loop of the classic mode of phase 4**: it said *«the monotonic clock is in milliseconds and its granularity is deliberately coarsened: the client writes `millisecondi × 1000`»*. `[M]` on **Chrome 151**, cross-origin-isolated page, `performance.now()` has a granularity of **5 µs** — **two hundred times** finer than what was written. ⇒ ⭐ **The rule survives the premise that produced it** (*one writes what one knows*), ⛔ but a client that multiplied milliseconds by a thousand would throw away **199 parts out of 200** of a measurement it already has in hand. ⚠ And the granularity **depends on cross-origin isolation**: where it is missing, it becomes coarse again — so one writes the one one has and **declares it**, instead of fixing one in the document |

> ### ⭐ The sign of the wheel — finding **R1.26**, and it is MEASURED
>
> ⚠ *This box ended, until 11 Aug 2026, with* «**Until it is measured, this line stays `[?]`**» *— and the measurement had been taken on the night of the 10th, without anyone bringing it here
> (finding **R12C.7**, and the probe had written it on its own in* `web/rapporti/S-esiti-sonda.md` *§9,
> entry S.7). Whoever had written the input injection at phase 4 by reading this line would have
> chosen the sign at random, and the symptom is* «the wheel goes backwards» *— that is form **E11** that
> this box exists to avoid.*
>
> **Why the question existed.** This line said *«positive upwards and leftwards. It is the unit of `wl_pointer.axis_value120`, so nothing is converted»*. ⛔ **The two halves cite
> two conventions with opposite signs**: in evdev the wheel is positive upwards, in `wl_pointer`
> the value is positive in the direction in which **the content scrolls**, that is downwards. And «positive leftwards» corresponds to neither. ⛔ And `libei` **does not untie it**:
> `ei_device_scroll_discrete` documents *«the y scroll distance in fractions or multiples of 120»* —
> **it declares the magnitude and not the direction**. The convention is not in the API, it is in the compositor.
>
> ⭐ **THE MEASUREMENT — `[M]` 10 Aug 2026, 20:59:27→20:59:57 UTC.**
>
> | | |
> |---|---|
> | **what was seen** | `ei_device_scroll_discrete(0, **+120**)` → the page's `wheel` event carries **`deltaY = +114`** (`deltaMode = 0`, pixels) and the page **goes down** by 114 px, that is it goes **towards the end of the document**. With **−120**, `deltaY = −114` and the page **goes up** |
> | **the scene, in full** | test machine **192.168.0.2**; GNOME session without monitor from `banchi/00-sessione-gnome.sh` — `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; the page in **Firefox 140.13.0esr** in `--kiosk` full screen on the virtual monitor, `dpr` 1 |
> | **where to check again** | `banchi/01-s7-esiti.jsonl` (two runs, `7sd0u7jv` and `oq7jqrdv`), and the report `web/rapporti/S-esiti-sonda.md` §1 |
>
> ⛔ **The consequence, and it is the server's**: positive `deltaY` means that the content goes **towards the
> end** of the document, that is that the user turned the wheel **down**; this section fixes
> the other half — the client sends `+120` when the user turns **up**. The two conventions are
> **opposite**, so **the server MUST invert the sign of the vertical axis** before passing it to
> `ei_device_scroll_discrete`. Injecting the value as it is, the remote screen would scroll
> backwards for **every** user.
>
> ⭐ **And the comparison is honest because the two sides speak the same language**: `deltaY` is exactly
> the quantity the client reads when the user turns the real wheel. Two worlds are not
> compared: the same instrument is measured twice.
>
> **The controls, and what each is worth** *(the recount of 11 Aug, `S-esiti-sonda.md` §0-bis,
> separated what is in the log from what was only on screen — and here the separation is reported,
> not only the outcome)*:
>
> | Control | Outcome | `[M]` or `[?]` |
> |---|---|---|
> | ⛔ **the opposite sign** — `−120` is injected too | ✅ `+120 → +114`, `−120 → −114`: **the sign** is measured, not «that something moves» | `[M]`, in the log |
> | ⛔ **the two instruments agree** — the `wheel` event and the real movement of `scrollY` | ✅ they agree on all tests | `[M]`, in the log |
> | ⛔ **`natural-scroll` in its two states**, with the device rebuilt from scratch | ✅ **the sign does NOT change**: `+120 → +114` in both runs | ⚠ **half**: `[M]` that two independent runs give the same sign; `[?]` **that they were the two states** — the label was only in the launcher's on-screen output |
> | **silence** — ten seconds without injecting | ✅ no notch | ⚠ it is an **absence** of lines: consistent with the timestamps, not proved by them |
> | *in addition* — does `ei_device_scroll_delta` have the same direction? | ✅ yes | ⛔ **not traceable**: no log line carries it. It stays a thing seen, not a delivered measurement |
>
> ⚠ **One more fact, for whoever will write the injection**: one notch (120 units) translates into **114
> pixels** on Firefox+Mutter, that is three lines. It is the conversion factor of that pair, **not a
> constant of the protocol**: it is not written here and not put in any formula.
>
> ⛔ **And what is NOT closed, because «not closed» and «not measured» are two different states.** The
> measurement is on **Mutter**, and this section binds **five** desktops. If `libei` normalises,
> the number holds everywhere; if the compositor normalises, the KDE phase (11) will find a different sign on KWin.
> `[?]` **stays for the other four**, and the bench can be rerun on KWin without changing a line
> of the page (`banchi/01-s7-rotella.sh` + `01-s7-pagina.html`).
>
> ⚠ *The precedent this line cited was wrong, and it was corrected on the night of 9 Aug
> 2026 (finding **R4.15**): it said that «in v1 this exact conversion table cost the wheel bench». `LEZIONI.md` §2.3 says something else — the wheel bench looked for
> `asse dy=-10` while the log wrote `asse dx=0 dy=-10`: **red, with the correct code**. It is
> a string searched badly, not a conversion with the wrong sign, and citing the wrong lesson
> loses it at the point where it would apply.*

⛔ **The coordinates are on the canvas, and they are pixel indices**: `0 ≤ x < tela_larghezza`,
`0 ≤ y < tela_altezza`. On a 1920×1080 canvas the bottom-right corner is **1919, 1079**. The client
knows the canvas (§4.5) and knows where its view is inside it: the conversion is its own, **rounding
down**. The server **MUST NOT** apply any transformation to the received coordinates, and
**MUST** refuse with `ERRORE_PROTOCOLLO` an out-of-range coordinate — except for the second of
grace of §7.1, where it saturates to the last valid pixel.

> ⚠ *The range was missing, and the line said only «outside the canvas» (finding **R1.16**). A page
> that divides the mouse position by the scale factor and rounds up produces 1920 on
> a canvas of 1920: one reading injects it, the other **closes the session**. And closing the session
> for a rounding is the thing `SPECIFICHE.md` §8.3 forbids — «never detach».*

⛔ **`LETTERA` is used when text is typed; `POSIZIONE_TASTO` when a command
modifier is pressed** — Ctrl, Alt, Super. Shift and AltGr **do not** count as command: they serve
to make the letter, and stay in the path of `LETTERA` (`SPECIFICHE.md` §7.3).

⛔ If a `LETTERA` cannot be produced in the layout of the session, the server **MUST**
write it in the log and **MUST NOT** send a different character nor keep silent.

⛔ **On detach everything is released.** When a connection ends — by farewell, by silence,
by error — the server **MUST** release **every key and every button that is pressed**.
⭐ It is trap 11 of `LEZIONI.md` §4 in its worst form: a Ctrl left down in a session
that outlives the client makes the desktop unusable at reattach, and nobody connects the two things.

### 7.4 Clipboard

| Type | Name | |
|---|---|---|
| `0x0201` | `APPUNTI_ANNUNCIO` | «I have new text» |
| `0x0202` | `APPUNTI_CHIEDI` | «send it to me» |
| `0x0203` | `APPUNTI_TESTO` | UTF-8 |

```
APPUNTI_ANNUNCIO
 ├── u32 trasferimento       ⭐ the identifier, chosen by whoever announces
 └── u32 lunghezza           how many bytes the available text has

APPUNTI_CHIEDI
 └── u32 trasferimento       that of the announcement being answered

APPUNTI_TESTO
 ├── u32 trasferimento       that of the request being served
 └── byte                    up to the end of the stream, valid UTF-8
```

> ### ⛔ Two corrections of the evening of 9 Aug 2026 — findings **R1.11** and **R1.20**
>
> **The identifier was missing altogether.** The rule *«every transfer goes on its own stream»* could not
> be satisfied: the three messages travel in **two directions** and the streams are **unidirectional**,
> so a transfer occupies at least two of them. And without a field binding them, with two announcements
> open in the two directions — *the user copies here while pasting there* — the two implementations
> pair the requests with the announcements **in a different order and swap the texts**.
>
> ⛔ Each side numbers **its own** transfers, from 1 upwards. An `APPUNTI_CHIEDI` with an
> identifier that corresponds to no live announcement is `ERRORE_PROTOCOLLO`.
>
> **And the second length has been removed.** `APPUNTI_TESTO` carried `u32 lunghezza` *inside* a
> message that already has its length in the framing of §6.1: two truths about the same fact,
> that is the defect §2.2 forbids with those words. ⚠ With a consequence on the implementation:
> the text is read **up to the end of the message**, and the ceiling is that of §5.4.

Bidirectional. One announces and asks, instead of pushing: whoever copies a whole document does not
send it to anyone until someone pastes.

⛔ **The content is always and only plain text in UTF-8**, and there is no field declaring a
type: it does not exist because there is nothing to choose. ⚠ *This line said «a different type is `ERRORE_PROTOCOLLO`», and no message carried a type field — a rule no
implementation could violate and no bench see fail, and that invited the reader to add
a nonexistent field (finding **R1.20**).*

⛔ **Every transfer has its own identifier**, and messages of different transfers do not
mix. ⚠ An `APPUNTI_CHIEDI` that arrives when the announcement has already been superseded by a more
recent one is served **with the current text**, and the sender writes it in the log: it is the normal race
between two people copying, not an error. ⭐ **And it is the fifth exception declared in §3** — see
the list there.

⛔ An `APPUNTI_TESTO` nobody asked for is `ERRORE_PROTOCOLLO`: the clipboard is pulled, not
pushed.

### 7.5 ⭐ The bench function: the mark, and the known delay

*Added on the night of 9 Aug 2026, finding **R3.4** of the review of the phase 1 bench, and
**before the first byte of code** — §9 closes the window for new types from there on, and the clause
that kept it open was that then no implementation existed. ⛔ **The first byte is from
10 Aug 2026 and the window is closed** (§0-bis, §9): these two types came in with the last
opportunity, and there is no second one. ⚠* It said «*the clause that keeps it open is that **today** no implementation exists*», *in the present tense — corrected on 11 Aug 2026, finding **R12C.2***.

⚠ **Its mark stays 🔸, not ✅**, and it is recorded where decisions live: `DECISIONI.md` §1.5
row 26. The question *«was it a decision of the user?»* — finding **R11.15** — **was closed
on 11 Aug 2026**: no, it was not, and it stays removable without going back to him.

> ### ⛔⭐ And FROM TODAY IT DOES NOT ENTER THE DELIVERED PRODUCT — ✅ 11 Aug 2026
>
> *`DECISIONI.md` §7.16, from the user: «l'utente deve vedere il desktop senza artefatti, come se
> fosse davanti al monitor del PC … si tiene quello che serve per i test, ma poi nel prodotto
> finale si fa pulizia».*
>
> ⛔ **This is a BENCH function, and in the binary that gets installed it MUST NOT be there.** Not switched off:
> **absent** — not compiled, not reachable, and ⛔ **not findable by searching for its marks inside the
> binary**. On the screen of whoever connects nothing ever appears that is not their desktop.
>
> ⚠ **«Off» was the previous form, and it is no longer enough.** The function is born off and
> `banchi/01-b5-violazioni.py` checks that with the function off the server refuses with
> `FUNZIONE_SPENTA`: that behaviour **stays**, and it is right — but it holds for the **test
> build**, which is the only one in which these two types exist.
>
> ⛔ **And the difference is measured, or it is a good intention**: *«it is not there»* and *«it is there and it is off»* look
> the same from outside. They are separated **by searching for the marks inside the delivered binary** — the
> same technique with which `banchi/01-p1-prodotto.sh` tells a new binary from an old one. The
> bench belongs to **phase 13**, where the package is born.
>
> ⭐ **Why the function survives all the same**: calibration of the delay stopwatch at phase 3 —
> a known delay is injected and one checks that the median rises by exactly that. Removing it
> altogether would have left the 50 ms ceiling **without a way of knowing whether the number is true**.

> ### ⛔⛔ 13 Aug 2026 — **the bench function DOES NOT give the known delay**, and did not give it at phase 3
>
> *This paragraph is normative and describes a mechanism that **is not there** in the product. It must be written
> here, or whoever reads this section believes they have in hand an instrument that does not exist.*
>
> | | state `[R]` |
> |---|---|
> | the function | `BANCO_ACCESO 0` — born off, as §7.5 wants |
> | ⛔ **the `ACCETTATA` branch** | **is a stub**: it does not paint, does not wait for the `ritardo_ms`, does not produce the `istante` the message promises |
>
> ⇒ ⛔ **P1, the decisive control of the delay loop, at phase 3 did NOT pass through here.**
> The injection of the known delay was made **outside the product**, and it came out `[M]` green
> (N = 25 → **+25.08 ms**; N = 60 → **+58.58 ms**).
>
> ⭐ **And the injection outside the product is not a fallback: it is better.** The clock anchor of the meter
> **does not pass** through the injected path — if it did, **P1 would pass even with the bench broken**,
> because the N milliseconds would add up identically on both sides. A decisive control
> that can no longer fail has stopped being a control (`LEZIONI.md` §1.2).
>
> ⇒ ⏳ **What remains to be decided, and is not decided here**: whether the `ACCETTATA` branch must be completed or
> whether the two messages must be removed from the protocol, given that their only declared reason —
> «calibrating the delay stopwatch» — has been satisfied **without them**. ⚠ As long as they stay
> written here and do not exist in the code, this section describes a thing that is not there: it is the species
> of defect against which §0 exists.

⚠ **And the two types consumed the clause of §9** that §12 declares to have been *«the last opportunity»* to add message types: they stay in the document, ⛔ but from now on as a
**declared bench function**, not as a function of the product.

> ⛔ **Why a bench function is in the protocol and not in the test code.** The delay
> loop of `DECISIONI.md` §2.6 measures **from the receiving side**: the client causes an unmistakable visual
> change and watches the frames it decodes until it sees it. For that number
> to count, the bench must be able to **inject a known delay** and check that the median rises by
> exactly that — ⛔ *«a bench that does not do it does not know it is measuring»*
> (`web/rapporti/S4-ritardo-disegno.md` §4.2, control P1).
>
> That command **crosses the wire**. Improvising it in the test code means two
> implementations that invent it differently, that is the silent defect against which §0 exists — and S4
> §5.3 says it with these words: *«it must be written in `RCP.md` as a bench function, not improvised in the test code»*.

**The two messages, in bytes:**

```
BANCO_MARCA                                          client → server
 ├── u32 id            ⛔ grows by at least one at every message; 0 is reserved
 ├── u32 colore        0x00RRGGBB — the colour to bring the mark to
 └── u32 ritardo_ms    ⛔ the KNOWN delay the server MUST wait before
                       painting. 0 = at once. It is the control of the bench

BANCO_ESITO                                          server → client
 ├── u32 id            that of BANCO_MARCA
 ├── u8  esito         1 = ACCETTATA, 2 = RIFIUTATA
 ├── u8  motivo        0 if accepted; otherwise:
 │                       1 = FUNZIONE_SPENTA
 │                       2 = RITARDO_FUORI_LIMITI
 └── u64 istante       microseconds of the server's monotonic clock, of the moment
                       the mark was painted. ⛔ 0 if refused, and it is
                       the only meaning of «absent» for this field (§6.0)
```

**Where the mark is, and who paints it:**

| | |
|---|---|
| **the size** | **16×16 pixels of the canvas**, in the top-left corner: from `0,0` to `15,15` |
| ⛔ **why 16 and not 1** | the video is encoded in **4:2:0**, so chroma is at half resolution, and encoders work in blocks. A small square or one straddling a block boundary gets **smeared**, and the bench would read a colour that was not sent. ⚠ And the receiver **MUST** read the **median** of the 256 pixels, with tolerance, not the central pixel |
| ⛔ **who paints it** | **the server**, in the frame it is about to encode — **after capture**. ⚠ *So the measurement that comes out of it **excludes the compositor**, and this must be declared next to every number: it is the delay of* encoding → wire → decoding → drawing*, not the one the user feels. The compositor's piece is measured by the complete loop of `DECISIONI.md` §2.6, which goes through the real input* |
| ⚠ **and in the canvas, not in the view** | the client rescales: if view and canvas do not coincide, the 16×16 of the canvas become another size on its drawing, and **the computation is its own** |

**The rules, and they are five:**

1. ⛔ **The function is OFF unless the administrator switches it on in the server
   configuration.** It is invariant **I6** to the letter — *what changes what is seen stays behind a
   switch that is off by itself* — and here it literally paints over someone's desktop;
2. ⛔ **off, the server answers `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`. It MUST NOT keep silent and MUST NOT
   close**: a silence leaves the bench waiting forever, and it is the same defect that
   §7.1 forbids for `ADATTA_TELA`. A client that asks for a function that is off has violated nothing;
3. ⛔ **the server MUST declare it**: the capability `banco.marca` of §4.3. A client that asks for it
   without it having been declared gets `FUNZIONE_SPENTA` all the same, not a protocol error;
4. `ritardo_ms` **MUST** be between **0 and 10 000**; outside it is `BANCO_ESITO(RIFIUTATA,
   RITARDO_FUORI_LIMITI)` — ⚠ **not** `ERRORE_PROTOCOLLO`: it is a wrong bench parameter, and making
   the session drop for the bench being calibrated is the same bad idea as §7.1 for out-of-limit
   sizes;
5. ⛔ **every switch-on and every `BANCO_MARCA` served are written in the server log.** A
   session that paints coloured squares on a person's desktop **must be able to prove it
   from the log**, or the day someone complains about it there will be no way of knowing whether it was
   switched on.

⚠ **And `istante` is not for measuring the delay**: it serves the bench to **distinguish the delay it
asked for from the one it found**. The delay is measured by the client, from the receiving side, as
`DECISIONI.md` §2.6 says — this field only says when the server obeyed.

---

### 7.6 ⭐ `TERMINA_SESSIONE` — the only message with which the client closes the SESSION

*Born on 15 Aug 2026 with the user's decision `DECISIONI.md` §4.1-ter.*

```
TERMINA_SESSIONE
 └── (empty body)
```

⛔ **It is not «close the connection»**: that is done with `CONGEDO`, and leaves the session alive
(invariant I4). This one says *«I am done»*: the graphical session ends and **the user's programs
close**. They are the two exits of `DECISIONI.md` §4.1-ter, and the protocol must be able to
distinguish them — a client with only one way would force the user to choose between never logging out and
losing their work.

| | |
|---|---|
| **who sends it** | the client, and **only** after an explicit gesture of the user: the shortcut `Ctrl+Alt+Fine` with its confirmation. ⚠ The item «Esci…» of the desktop menu **does not pass through here** — the desktop executes that one, and the server notices it by itself |
| **when it is valid** | ⛔ only with the session **attached**. Before `ATTACCA` there is no session to terminate, and §3 gives no discounts: whoever sends it out of place gets `ERRORE_PROTOCOLLO` |
| **the answer** | ⛔ a `CONGEDO` with reason **`0x10 SESSIONE_TERMINATA`**, and it **MUST leave before** the graphical session finishes dying: when the compositor falls, the stage falls with it and the channel is no longer needed. A `0x10` sent late is finding **B-7** with a new name |
| **and to the others** | ⛔ the farewell goes to **all** the sessions of that user, not only to whoever asked: the graphical session is only one (I2), and whoever watched it from a second device would be left with a frozen screen forever |

⚠ **And there is no «I am terminating» answer**: the outcome is the farewell. An intermediate message
would be a deduction in place of a fact (`LEZIONI.md` §7.5), and the only fact that counts is that the
session is over.

---

## 8. The farewell

### 8.1 It is said, and checked from the receiving side

⛔ Whoever closes **MUST** send `CONGEDO` with a reason **before** closing the **WebTransport
session** — ⛔ **if the control channel is still usable** (§3.1 point 2) — and **MUST**
repeat the reason in the application error code of the closing (§3.1 point 3). ⭐ **Point 3
has no conditions and needs none**: it travels in the closing itself, and leaves even when the
channel is dead.

> ⛔ *Corrected on 10 Aug 2026, finding **R11.8**: here there was «before closing the **QUIC connection**», and in §4.4 «with the same reason in the **`CONNECTION_CLOSE`**». They are the two remainders the
> correction R1.4 of §3.1 had not reached, and §8.1 is the paragraph that dictates the obligation to **whoever
> closes** — which is often the page, that is the side R1.4 declares **unable** to close the
> HTTP/3 connection underneath.*
>
> ⛔ **It is the same input with two different bytes** — a transport `CONNECTION_CLOSE` against a
> `CLOSE_WEBTRANSPORT_SESSION` — that is the exact form R1.4 declared it had closed: *«one programmer closed the session and declared the rule fulfilled; the other looked for the connection API, did not find it, and left point 3 unimplemented — and was as conforming to the text as the first»*. ⚠ And §4.4 imposed it precisely on the `RESPINTO` path, the one B11
> reopened on 10 Aug.

⚠ **And this line has a price already paid.** In v1, for **three phases**, the server dutifully wrote
«farewell to the client» while the client, at the same time, wrote «network error»: a
second library call nobody suspected was missing (`LEZIONI.md` §1.7). Hence the
acceptance-test obligation: **the farewell is checked from the side that receives it**, never from the log of whoever sends it.

⚠ **The only exception is `RESPINTO`** (§4.4), which *is* the farewell of authentication.

> ### ⛔ And «whoever closes» is not whoever received a `FIN` — ✅ 11 Aug 2026
>
> *The exception the decision of `DECISIONI.md` §7.14 demands, written here because it is here that
> the obligation is dictated. Without this sentence §4.2 forbids sending on the control channel after a
> `FIN` and §8.1 keeps **imposing** precisely that byte: the decision would have moved the
> contradiction instead of closing it.*
>
> ⛔ **Whoever receives a `FIN` on the control channel is not «whoever closes», and sends no
> `CONGEDO`.** It was the other party that closed; the reason for that closing comes from it, and the
> only thing owed by the receiver is **to consider the session finished** (§4.2).
>
> ⭐ **The bytes of point 3 of §3.1 remain owed** — the application error code — when it is
> **this** side that closes the WebTransport session first. The exception concerns the `CONGEDO`
> on the channel, not the reason in the closing.

> ### ✅ The condition, decided by the user on 11 Aug 2026 — `DECISIONI.md` §7.15
>
> *Until today this line set no conditions, while §3.1 point 2 says «**if the control channel is still usable**»: ⛔ **an implementation conforming to §3.1 was in violation of
> §8.1**, and two normative sections of the same document gave two verdicts on the same input
> — the violation that arrives on a unidirectional stream with control already finished (finding
> **R11.23**).*
>
> ⛔ **The condition wins.** The obligation of the `CONGEDO` on the channel **falls when the channel is not
> usable**; what never falls is the reason inside the closing code (§3.1 point 3).
>
> ⭐ **The reason, in the user's words**: *«se una connessione cade nessuno può dire al server
> "chiudo perché ho finito"»*. A `DEVE` that cannot be respected is not a rule: it is a defect
> of this file, and §0 says that the defects of this file belong to this file.
>
> ⚠ **And it does not weaken `DECISIONI.md` §4.1-bis**, decided the same day — *every closing by the
> server has a reason it can explain*: the reason arrives all the same, by the second road. ⛔ What
> is lost is **only the byte on the dead channel**, that is a byte that would not have left.
>
> ⭐ **And it closes a red on correct code**: **B5 and B11 already applied the conditional of §3.1**
> (`FASI.md` §01-filo-nudo, finding R3.3), and a bench written on the absolute form **would have failed
> a correct server** every time the violation arrives on a unidirectional stream.
>
> ⛔ **And the two decisions of 11 Aug do not replace each other.** §7.15 says *when* the obligation falls;
> §7.14 says *who* is not bound at all. After a `FIN` received, the channel, in the direction of whoever
> received it, **is still usable**: without §7.14 the condition of §7.15 would not save it.

### 8.2 The reasons

| Code | Name | When |
|---|---|---|
| `0x01` | `CHIUSO_DALL_UTENTE` | the user closed the client |
| `0x02` | `INATTIVITA` | 30 minutes without input (`SPECIFICHE.md` §5.3) |
| `0x03` | `SESSIONE_ABBANDONATA` | ⭐ **60 minutes without input** (`SPECIFICHE.md` §5.3, `DECISIONI.md` §4.8). ⚠ *It said «6 hours without attaches»: changed on 16 Aug 2026 — the ceiling **and** the criterion change, because whoever watches without touching renews nothing. The code and the name stay* |
| `0x04` | `SESSIONE_LOCALE_PREVALSA` | the user opened a local graphical session |
| `0x05` | `GIA_ATTIVA_LOCALE` | there is already a local graphical session |
| `0x06` | `BUDGET_PIENO` | ⭐ **the machine has no more COMPOSITION capacity** — ⚠ *it said «of encoding»: corrected on 24 Aug 2026, `DECISIONI.md` §4.6-nonies, because `[M]` the bottleneck is `rcs0` at **0.97 Gpixel/s**, **half** of the encoder. ⛔ And until phase 10 this code **was never sent by any line of the server**: from phase 10 it really leaves* |
| `0x07` | `CREDENZIALI_ERRATE` | |
| `0x08` | `TROPPI_TENTATIVI` | ⭐ **the address is banned**: three failed authentications, twelve hours (§4.4-bis). ⚠ *It said «rate limiting», and it was the previous form: since 10 Aug 2026 it is no longer a rate, it is a ban* |
| `0x09` | `NIENTE_IN_COMUNE` | no shared codec |
| `0x0A` | `VERSIONE_INCOMPATIBILE` | |
| `0x0B` | `ERRORE_PROTOCOLLO` | §3 |
| `0x0C` | `SERVER_IN_CHIUSURA` | |
| `0x0D` | `TEMPO_SCADUTO` | ⭐ *new, 9 Aug*: a ceiling of §4.6 has expired |
| `0x0E` | `SESSIONE_NON_SERVIBILE` | ⭐ *new, 9 Aug*: the attach is well formed but cannot be served — a compositor that does not start, a layout the system does not know. It **MUST** carry the detail in the body |
| `0x0F` | `GIA_ATTIVA_REMOTA` | ⭐ *new, evening of 9 Aug*: **there is already a client attached to this session**, and this connection is **refused** |
| `0x10` | `SESSIONE_TERMINATA` | ⭐ *new, 15 Aug*: **the user has logged out of the desktop** («Esci/logout» from the system menu). The graphical session is over and its programs are closed ⇒ ⛔ **there is nothing to reattach to**, and the page goes back to the **login form** (`DECISIONI.md` §4.1-quater) |

> ### ⛔ Why `0x10` is not a duplicate of `0x01` — 15 Aug 2026
>
> The two codes describe **two gestures of the user with opposite outcomes**, and `DECISIONI.md` §4.1-ter
> separates them: `0x01 CHIUSO_DALL_UTENTE` is the **wire that drops** — tab closed, browser closed, the user's
> PC switched off or restarted — and carries the promise *«reattach and you find everything again»*. `0x10` is the
> **logout**, and there that promise is **false**.
>
> ⛔ **The constraint this code carries is on the order, not on the content**: when the compositor
> falls the stage falls with it, and the channel is no longer needed. `0x10` **MUST** leave **before** the
> graphical session has finished dying. A `0x10` defined and sent too late is finding
> **B-7** with a new name.
>
> ⚠ **And whoever receives a `0x10` must not reattach**: a client that retried would open a **new**
> session, it would not find the old one again — which is exactly what the user asked to close.

> ### ⛔ Why `0x0F` was added, and why now — finding **R1.3**
>
> The fourteen previous reasons covered **local against remote** (`SPECIFICHE.md` §5.1) and not
> **remote against remote**: you are attached from the laptop and open the same session from the phone.
>
> **The choice, the user's, on 9 Aug 2026**: *«se un utente ha già una sessione grafica remota
> attiva, e ne vuole attivare una seconda da un secondo device, la seconda connessione viene
> rifiutata»*. ⭐ It is invariant **I2** applied to the letter — *«the second connection is refused with an explicit message»* — and `0x0F` is the remote twin of `0x05 GIA_ATTIVA_LOCALE`.
>
> ⛔ **The one refused is whoever arrives, not whoever was there.** No attached and live client is ever
> ousted by another.
>
> ⚠ **And the boundary with `DECISIONI.md` §4.4 must be read carefully**, because the two rules seem to clash and
> do not: *«whoever is silent is detached, whoever arrives gets in»* speaks of the **ghost** client — the phone
> dead in a tunnel. A client **silent for 30 seconds** (`SPECIFICHE.md` §5.3) is no longer
> attached, so it occupies nothing and the new one gets in. A **live** client occupies, and the new one is
> refused. ⛔ The discriminant is **the silence clock**, not the intention of whoever arrives.
>
> ⚠ **The price, declared**: if the laptop switches off abruptly without a farewell, from the phone one
> gets in **after thirty seconds**, not at once.
>
> ⚠ And the window to add a reason closed right after: §9 forbids it within a major
> version, and the clause that allowed it was that then no implementation existed.
> ⛔ **Since 10 Aug 2026 they exist** (§0-bis), and this road is no longer there. ⚠ *It said «the clause that allows it is that **today** no implementation exists», in the present tense: corrected on 11
> Aug 2026, finding **R12C.2**.*

⛔ Every reason **MUST** be showable to the user in an understandable sentence. `BUDGET_PIENO`
is not «error 6».

> ⭐ **And the sentence the client really shows, since 25 Aug 2026** (`src/pagina.html`):
>
> > *«questo server non ha più capacità per un altro desktop: le sessioni già aperte continuano,
> > e un posto si libera appena qualcuno esce — riprova fra un momento, e se si ripete chiedi a
> > chi amministra il server»*
>
> ⛔⛔ **And what it does NOT say, by choice: «make the window smaller».** It had it, and it was
> **false**: at the gate the canvas **is not yet decided**, and the only number in the server's hands is
> `video.misura_massima`, which is the ceiling of the client's **DECODER** — not of the window.
> ⇒ Whoever shrank the window and retried got **the very same no**.
> ⭐ *A sentence that promises a gesture the product does not offer is worse than silence: it sends
> the user looking for a command that does not exist.*

⛔ **The sentence is built by the client**, from the code. The `dettaglio` field **MUST NOT** be
shown to the user: it is for the log, and it contains what whoever diagnoses needs.

---

## 9. The versions

`CIAO` carries the major version the client can speak; `ECCOMI` the one chosen by the server.
If there is no common version, `VERSIONE_INCOMPATIBILE`.

⛔ **Concretely**: the server chooses the highest version it can speak that does not exceed that
of `CIAO`, ⛔ **among those the path admits (§2.2)**. If it has none, it sends the farewell. The
client **MUST** check that the version of `ECCOMI` is one it can speak, and send the farewell
`VERSIONE_INCOMPATIBILE` if it is not — a server that answers with a version higher than the one
asked for is erring, and accepting it in silence is the leniency §3 forbids.

> ### ⛔⭐ The seven words of §2.2 are from 10 Aug 2026, and **B5** found them
>
> ⚠ *The section number was corrected the same day, finding **R11.18-bis** (R11.2): these
> three lines pointed to **§2.4**, which is «The port» — 7447, TCP and UDP — and names neither paths
> nor versions. The rule lives in **§2.2**, rows «the session address … the number after the slash is the major version» and «the two MUST coincide», and it is there that R1.24 wrote it.*
> ⛔ **Whoever read §9 and went to §2.4 as told found the port, no constraint, and
> came back to §9** — that is reconstructed exactly the reading that had produced the first draft of
> `banchi/rcp/rcp.c`. The cure of a contradiction between two sections pointed to a third.
>
> This paragraph said only *«the highest that does not exceed that of `CIAO`»*. §2.2 says that
> a `CIAO(versione=2)` on `/rcp/1` is `VERSIONE_INCOMPATIBILE`. ⛔ **The two rules give different bytes
> on the wire for the same input** — `ECCOMI(1)` against `CONGEDO(0x0A)` — and **neither
> of the two cited the other**.
>
> ⚠ It is not a textbook case: whoever writes the server reads §9, which is the paragraph titled *«The versions»*, and writes `if (versione < LA_MIA) congeda;`. It is exactly what happened — the
> first draft of `banchi/rcp/rcp.c` **accepted a `CIAO(2)`** and answered `ECCOMI(1)`, and it was
> conforming to §9 to the letter.
>
> ⭐ **§2.2 wins**, because it is the more specific and because it was written to resolve precisely this
> case (finding R1.24). This line now names it, so whoever reads only one of the two finds
> the other.
>
> ⚠ It is the **second** internal contradiction found by a bench in two days: the first was the
> underscore of §4.3, found by the validator of B4. ⭐ Both were found by
> programs that read **only this document**, and neither by whoever reread it.

**Within a major version one grows only by capabilities** (§4.3), never adding fields to
existing messages nor new types the old one would have to ignore — because ignoring is forbidden
(§3). A new mandatory type is a new major version.

⚠ **In practice, as long as client and server are updated together, the version is of little use.** It is needed the
day a phone stays behind — and that day either it has been written well, or one discovers that the
extra field had been added «it is compatible anyway».

⛔ **And the window in which this document could still be completed IS CLOSED**: the prohibition
above protects the existing implementations, and **now they exist** — the list, counted, is in
§0-bis. **Since 10 Aug 2026, first byte of code, the rule holds with no discounts.**

⛔ **How much the window was used, before closing: FOUR types, not two.**
`RICHIEDI_CHIAVE` (`0x000D`) and `TELA` (`0x000E`) on 9 Aug; ⭐ **`BANCO_MARCA` (`0x000F`) and
`BANCO_ESITO` (`0x0010`) on the night of the 9th** (§7.5). Plus **three** farewell reasons (`TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`). The count is in `DECISIONI.md` §1.5, and §12 declares
that the one of the two of the bench function was *«the last opportunity»*.

> ⚠ *This line said* «The **two** types added on 9 Aug (`0x000D`, `0x000E`) came in under this clause», *and declared the window open. The two of the bench function had been
> added the same night and had never been brought here: the cure of finding **R11.13** had
> reached `DECISIONI.md` and not the line that keeps the count of the clause — that is whoever checked
> how much a non-repeatable window had been used, counting from here, found half of it. Corrected
> on 11 Aug 2026, finding **R12C.3**.*

---

## 10. What RCP does not do

| | Where it is written |
|---|---|
| it does not carry files, disks, printers, ports | `SPECIFICHE.md` §12 |
| it does not carry images in the clipboard | §7.4 |
| it has no channel for the **relative** pointer | reserved, not defined in RCP/1 |
| it has no channel for the stylus nor for multi-finger touch | `input.tocco` exists as a capability and is always `no` |
| it does not carry **microphone audio** | the direction is foreseen in §5, the format is not defined: `SPECIFICHE.md` §10 considers it not urgent |
| it has no compression of its own | the codec does it, and QUIC encrypts |
| it has no application heartbeat | §2.2 |
| it has no cleartext mode | §2 |
| it does not carry the volume | it belongs to the session, invariant I5 |
| it does not describe more than **one screen** | multi-monitor is out of scope as a function (`SPECIFICHE.md` §6.5); the canvas is only one, and larger than the view |

---

## 11. How to test against this specification

The point that makes all the rest useful. **Client and server are NOT tested against each
other**: they are tested against this document.

| Bench | What it tests |
|---|---|
| **the wire validator** | a third program that reads a recording of the connection and says which byte is not conforming. It is the only external referee we will have |
| **the handshake on two connections** | ⛔ **two, never one**: in v1 a shared certificate killed the server **at the second** connection, and a single-connection test stays green forever (`LEZIONI.md` §2.1) |
| **the farewell** | checked **from the receiving side**, for each of the reasons **that travel in a `CONGEDO`** — and for each one **the code in the closing of the session** is checked **too** (§3.1). ⚠ *It said «for each of the fourteen»: but `CREDENZIALI_ERRATE` and `TROPPI_TENTATIVI` travel in `RESPINTO`, which §4.4 forbids to be followed by a farewell — the bench would have failed on two reasons by construction, and whoever wrote it would have thought they had made the mistake (finding **R1.18**)* |
| ⭐ **releasing the keys on detach** | a connection is detached **with a key pressed** and reattached to check it has not stayed down (§7.3). ⛔ **It is the rule with the highest damage/cost ratio in the document**: a Ctrl left pressed makes unusable a session that outlives the client, and nobody connects the two things |
| ⭐ **audio, listened to** | a datagram is opened and the bytes are looked at: sample rate, channels, byte order of the PCM. ⛔ A server that sent 44 100 Hz, or big-endian PCM, would stay **green on all the other benches** — and the symptom, as in v1, «it looks like a network defect» (`LEZIONI.md` §2.2) |
| ⭐ **the clipboard** | the three messages, the transfer identifier, and **two transfers open together in the two directions**: it is the case in which without an identifier the texts got swapped |
| ⭐ **the fixed second** | the answer to `CREDENZIALI` is timed — **even the successful one** (§4.4-bis). It is a security property no other bench sees, and a regression that removed it would make nothing fail |
| ⭐ **the address ban** | three failed authentications, and ⛔ **the fourth attempt is refused even with the RIGHT password** (§4.4-bis) — which is the test that tells a ban from a counter. ⛔ And with **three different user names**, or one is not testing the decided rule but the old one. ⚠ Then three controls that say *no*: **another** address gets in all the same · a **successful** login resets the count (two failed, one successful, two failed: the third does **not** ban) · and the ban **survives the restart** of the server |
| **the delay loop** | the client sends an input that changes the colour of the screen and watches the decoded frames until it sees it (`DECISIONI.md` §2.6) |
| ⭐ **the known delay** | `BANCO_MARCA` is asked with `ritardo_ms = N` and **the median MUST rise by exactly N** (§7.5). ⛔ *It is the control that makes every delay number of this project credible: a bench that does not do it does not know it is measuring* |
| ⭐ **the bench function off** | ⛔ with `banco.marca = no`, a `BANCO_MARCA` **MUST** receive `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — **not a silence and not a closing**. ⚠ And it is checked **from the receiving side**: a server that keeps silent leaves the bench waiting forever, and the symptom is «the bench has hung» |
| **rigor** | an unknown type, a wrong length, a message in the wrong state are sent on purpose: ⛔ **the connection must drop every time**. A bench that does not try to violate the protocol does not test the protocol |
| ⭐ **the abandoned frame** | a delta is abandoned on purpose and one checks that **a keyframe arrives** and that the client shows nothing broken meanwhile (§5.2). ⚠ Without this bench abandonment is tested only on a bad network, that is when nobody is watching it |
| ⭐ **stream credit** | a session is kept alive **beyond the first 256 frames** — that is beyond the first four seconds — and one checks that the video does not stop (§2.3) |
| ⭐ **the handshake deadlines** | a connection is opened and kept silent, for each of the three ceilings of §4.6 |

⚠ **And the positive control, which here is easy to forget**: before concluding that the
validator finds no errors, it is given a recording **with an error inside** and one checks that
it sees it. An instrument that has never found anything is not a clean instrument: it is an
uncertified instrument (`LEZIONI.md` §1.9).

### 11.1 ⛔ The recording format

*Written on 10 Aug 2026, **before** the recorder — finding R3.6. The format is **only one**:
two recorders, one in the C and one in the page, that wrote the same fact in two ways
would be the silent defect against which §0 was written.*

⛔ **The problem this format solves.** Recording the bytes as they were would put the
password in cleartext in a file, which §4.4 forbids *«at any level»*. Replacing it while leaving the
`lunghezza` would give a body that no longer matches, that is **a perpetual false red** on every trace
with a successful handshake. Replacing it **and** rewriting the length would make the
validator validate a document rewritten by the bench — and then it is no longer a referee.

⭐ **The fourth road**: one records **the true length**, replaces only the secret bytes with
as many filler bytes, and the format **declares which ranges are redacted**, with
the fingerprint of what was there. The length adds up, the validator knows where it must not look, the
password is not there.

```
header (16 bytes)
 ├── 8 bytes  magia          "RCPREG" 0x00 0x03
 ├── u32      quanti_blocchi
 ├── u8       orologio       1 = the times are the CLIENT's, 2 = the SERVER's
 └── u8[3]    riservato      MUST be 0

then `quanti_blocchi` blocks, each:
 ├── u8       verso          1 = client → server, 2 = server → client
 ├── u8       canale         the high byte of `tipo` (§2.5)
 ├── u8       fine           ⛔ how the stream was closed AFTER this block:
 │                             0 = continues · 1 = FIN · 2 = RESET_STREAM
 ├── u32      istante_ms     ⛔ milliseconds from the FIRST block, from the
 │                             MONOTONIC clock of whoever records. The first block is 0.
 │                             ⛔ Never a wall-clock time: §4.4 forbids secrets in the
 │                             file, and an absolute date says WHEN and FROM WHERE
 │                             a user connected
 ├── u64      stream         the identifier of the QUIC stream
 ├── u32      lunghezza      how many payload bytes follow — ⛔ the TRUE length
 ├── u16      quanti_oscurati
 │     for each:
 │       ├── u32   inizio        offset inside the payload of this block
 │       ├── u32   quanti        ⛔ the TRUE length of the replaced bytes
 │       └── 32 B  impronta      SHA-256 of the true bytes
 └── `lunghezza` bytes of payload
```

### ⛔ The recorded time belongs to WHOEVER RECORDS, and the rule of the second belongs to the SERVER

*The `istante_ms` field came in on 21 Aug 2026 with magic `0x03`, and without this paragraph
it would do more damage than the hole it closes.*

A recording taken **at the client** sees *«when the `TELA` arrived»* and *«when the `PUNTATORE` left»*: an interval **shorter** than the one the server measured, by half a network round trip
per side. ⇒ The validator can conclude **in one direction only**:

- if `istante_ms(PUNTATORE) − istante_ms(TELA) > 1000` with `orologio = 1`, the server's interval
  was **even longer** ⇒ the server **MUST** have refused, and if it did not it is `NON CONFORME`;
- if it is `≤ 1000`, **nothing is concluded**, and the validator **SAYS** so: *«non giudicabile da questa
  registrazione»*.

⭐ The direction gained is the one that matters: **a lenient server**, which accepts the old
coordinates forever. ⚠ And a referee that keeps silent about what it does not know is a referee that **acquits**: the
sentence «non giudicabile» is mandatory, not polite.

⛔ **And the magic changes because the block grows**: an old validator in front of a new file
**MUST refuse**, not read it askew. `[M]` 21 Aug, in both directions: today's referee
in front of the file of 12 Aug exits **2**; yesterday's referee — built on purpose by putting a copy back
at `0x02` — in front of today's file exits **2**. ⚠ It is the `0x01`/`0x02` defect of 12 Aug, which
**neither of the two files showed on its own**: here the change was made in **a single commit**, with all
four readers and writers together.

⚠ **Three benches are declared late** on this format — `banchi/02-filo-cliente.py`,
`banchi/02-filo-validatore.py`, `banchi/04-b20-desktop-vero.py`. Today they are a **coherent island**
(they write and read among themselves), ⛔ but as long as they stay at `0x02` the tree carries **two live formats under
a single specification**, which is the condition of the defect of 12 Aug writ large.

### T4 — a `TELA(ADATTATA)` that no frame obeys

*It is the referee's grip on «conforming is not working», and without `istante_ms` it did not exist.*

After a `TELA(ADATTATA, LxA)`, §5.2 wants the first frame at the new size to be a
**keyframe**, and §6.2 binds the 28 bytes to the canvas in force. ⇒ If frames pass for more than a ceiling in
**time** and **none** carries the granted size, the server answered **without touching the stage**.

⛔ **Not «the first»**: §6.2 admits the frame already in flight at the old size. ⇒ A ceiling in
time is needed, not a count — ⭐ and the difference is **proved, not asserted**: the mutation
*«counts instead of timing»* survived as long as the case that was to kill it had a window
too short.

⭐ `[M]` 21 Aug, on the **real product** (port 7721, five runs out of five): after
`TELA(ADATTATA, 1264x800)` the frame **declares 1264x800**. The stage was touched, and now a
referee says so instead of a line of reasoning.

> ### ⛔ The `fine` field is not a luxury — added on **12 Aug 2026**, proposal **P7** of F2.4
>
> *And it was not found by a rereading: it was found by `banchi/02-filo-validatore.py` **trying to
> judge a conforming recording**, and not managing to say whether the frame was complete.*
>
> Without `fine`, an **abandoned** frame (§5.1, lawful — the client throws it away and asks for a keyframe) and
> one **truncated by mistake** (§3 — the connection drops) **look the same** in the
> recording: the validator cannot apply the line §6.2 added on purpose on 9 Aug
> 2026 — *«but only if the stream finished with a FIN»*, finding **R1.7** — and it is form **E8**
> back in through the window. `[M]` on the conforming test recording the referee declared *«di 1
> su 1 NON si è potuta giudicare la completezza»*.
>
> ⚠ **The magic goes to `0x00 0x02`** because the block changes size: an old validator must
> **refuse** the new format, not read it askew.
>
> ⭐ **And it does not touch §9**: a recording block **is not a message**, and the format already carries its
> own version in the magic.

⛔ **The redacted ranges contain `0x2A` repeated**, not zeros: a zero is a value the
fields can really have, and a range of zeros that «by chance» matches a legitimate body
is a way of not noticing that the redaction is there.

⛔ **The validator MUST NOT read inside a redacted range**, and **MUST** refuse a
recording in which a redacted range falls outside the payload or overlaps another: a
malformed recording and a non-conforming wire are two different things, and must be said with two different
sentences.

⛔ **And the validator reports the offset of the offending byte in two ways**: absolute in the file, and
relative to the payload of the block. The first serves whoever looks at the file with an editor, the second whoever
reads this specification.

---

## 12. ⏳ What RCP/1 leaves open, declared

*They are not holes: they are things that are not closed now, and the reason why they are not closed.*

⛔ **And a status line, because it changes what can still be done in here**: since **10 Aug
2026** — first byte of code — the clause of §9 is **spent**. What is not closed in RCP/1
stays open **until RCP/2**, or is closed without adding message types (§0-bis, §9).

| | Why not now | When |
|---|---|---|
| ⭐ ~~**the ceiling of the session without control channel**~~ — ✅ **CLOSED** | **five seconds**, decided by the user on **11 Aug 2026**: `DECISIONI.md` §7.17, and the normative line is in **§4.6**. ⚠ *This cell still said* «❓ open … when the user has answered» *while §4.6 of the same file carries the line with the ✅ and the date: **two sections of the referee gave two different states to the same question**, and whoever had trusted §12 would have written a server without that ceiling while remaining convinced of being conforming. Corrected on the evening of 11 Aug 2026, at the opening reread* | ⛔ **it remains to be MEASURED**: `B6` wants a fourth case — open the session, do not open the channel, and check that at 5 s `0x0D` arrives **in the closing code**, not on the channel. *Decided ≠ measured.* ⭐ No new type: `TEMPO_SCADUTO` was already there |
| **the microphone** | the direction is foreseen, the format is not. Closing it now would mean writing a negotiation nobody exercises | when `SPECIFICHE.md` §10 stops calling it «not urgent» — and it will be a **new major version**, because it is one more channel (§9) |
| **the relative pointer** | it serves remote applications that **capture** the pointer, and that case is signalled by the server. It is not the case of `Pointer Capture` on Android, which is already covered (`DECISIONI.md` §5-bis.8) | when an application turns up that asks for it |
| **multi-finger touch** | `input.tocco` exists and is `no`. A reserved slot costs nothing; a definition never exercised costs a constraint | phase A4, if native touch is really needed |
| **4:4:4** | it is one more capability (`video.sottocampionamento`), and the product decision is `[?]` (`DECISIONI.md` §2.3) | when the user has looked at the two pictures |
| **more screens** | the canvas is only one. The form of multi-monitor is «two views on the same canvas», which the protocol already supports for the canvas; it would only be missing to say **where** each view is | never, as long as it stays out of scope |
| `[?]` **the IANA registration of the port** | §2.4 | if and when a registered number is needed |
| ~~the bench function of the delay loop~~ | ⭐ **closed on the night of 9 Aug 2026, a few hours after being opened** by finding **R3.4**: it is **§7.5**, two new types — `BANCO_MARCA` and `BANCO_ESITO` | ⭐ *It came in under the clause of §9 — «today no implementation exists» — and **that was the last opportunity**: from the first byte of code on it would have been an exception, that is the first breach made by us to a rule of ours* |

⛔ **And one thing that is not open and must be said so that it is not reopened by distraction**: the
**application heartbeat** is not missing, it is **forbidden** (§2.2). Whoever finds it absent and thinks of adding it
is about to create two truths about the same fact.
