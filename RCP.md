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
| message bodies defined byte by byte | 2 of 22 | **26 of 26** (§6, §7) — ⚠ *it said «22 su 22», and the count was from the first draft: the two types added on 9 Aug brought the total to 24, and the **two of the bench function** (§7.5, the night of the 9th) to **26**. Corrected by finding **R1.29**, and it is not pedantry — that cell is **the only proof the document carries of being complete**, and whoever checked it by counting found more* |
| elementary types (numbers, strings, lists) | — | §6.0 |
| how to recognise which channel a stream belongs to | — | §2.5 |
| what the transport demands (windows, streams, migration, 0-RTT) | 3 parameters | §2.3 |
| the port | — | §2.4 |
| what an implementation does after `ERRORE_PROTOCOLLO` | «chiude» | §3.1 |
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
> | ⭐ **P2** | §6.2 `numero` | *double reading, the most serious*: the counter did not say **where it starts**, and §7.1 gives `0` the meaning «nessun fotogramma» ⇒ `RICHIEDI_CHIAVE(0)` meant **two things** — the implicit sentinel value that §6.0 forbids |
> | ⭐ **P6** | §5.2 | *double reading, and it bites in phase 2*: a **delta at the opening** conformed to every line, and the client **had no way to notice** — no hole in the `numero` values, and the decoder raises no errors |
> | ⭐ **P5** | §6.2 `largh.`/`altezza` | *double reading*: *«è sempre quella della tela»* **describes** and does not command, and no line said what **the receiver** of a different size does — close or rescale |
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
> ⛔ **P5 killed a healthy session.** The line wrote *«DEVONO valere la tela concessa in
> `SESSIONE`»*, ⚠ but §7.1 has `ADATTA_TELA`, and `TELA` answers with *«la tela in vigore **dopo** questo
> messaggio»*. ⇒ `SESSIONE` grants 1920×1080 · the user drags the window · the client sends
> `ADATTA_TELA(1280,720)` · the server answers `TELA(ADATTATA…)` and captures at that size · the
> frame carries `largh. = 1280` · ⛔ **and the client rejects it and closes**. A server conforming to §7.1
> killed by a client conforming to §6.2 — and it is **exactly the scene that §7.1 protects** with its
> exception 4: *«l'utente che trascina male una finestra non deve perdere la sessione»*. ⭐ The cure is
> **one word**: «la tela **in vigore**» (the canvas in force) in place of «la tela concessa in `SESSIONE`».
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

> ⚠ *This line said* «⭐ **E la finestra per farlo è adesso** … quel divieto protegge le
> implementazioni esistenti, e **oggi non ne esiste nessuna**» — *and §9 said the same thing with the
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
was punished with a different error and nobody said «hai sbagliato l'ordine»: here it is said.

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

QUIC is not «TCP che va più veloce»: it carries four things that this protocol uses
deliberately, and that must be used **instead of** reimplementing them (`SPECIFICHE.md` §2 point 3,
*«dipendere, non riscrivere»* — ⚠ *this line cited a «§2.3» that does not exist in `SPECIFICHE.md`:
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
which we can say «questa versione non la parlo» is the path. ⛔ The version check in `CIAO`/`ECCOMI` (§9)
remains mandatory all the same: **the path does not replace it** — a path can
be typed by hand, and a check that can be bypassed by typing is not a check.

⛔ **And the two MUST coincide**: a `CIAO(versione=2)` on `/rcp/1` is `VERSIONE_INCOMPATIBILE`, not
a negotiation to resolve. An unknown path is refused with **404**.

> ⚠ *The two lines above are from the evening of 9 Aug 2026, finding **R1.24**.* The document
> said that the path «non sostituisce» the check, and **did not say that the two had to
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
| **the server MUST grant credit** to the client for its unidirectional streams: at least **16** available at any moment — ⛔ **that is at least 19 declared at the QUIC level** (see the box) | the client opens one input stream and one for each clipboard transfer. If the credit ran out, **input would not leave at all** and the symptom would be «il desktop non risponde» |

> ### ⛔ The 16 are **available to RCP**, not declared on the wire — and the difference is three
>
> *Added on 11 Aug 2026, finding **A** of point 4 of the session. The line above said
> «almeno 16» and that was all: ⛔ **whoever implemented it to the letter wrote `initial_max_streams_uni = 16`
> and conformed to the document while violating its reason.** It is defect **B-12**, found
> in the product on the night of 10 Aug and cured there — and the referee did not say it.*
>
> ⛔ **WebTransport has no credit of its own.** In drafts ≤ 07 every unidirectional stream of
> WebTransport **is** a unidirectional QUIC stream, on the same counter as HTTP/3. And HTTP/3
> takes **three** of them as soon as the connection is born — its control stream and the two of QPACK —
> and ⛔ **never closes them**.
>
> ⇒ **16 declared = 13 available to RCP**, and the three missing streams are lost in silence: the
> symptom is not an error but *«il desktop non risponde»*, that is the symptom this line exists to
> prevent.
>
> | | |
> |---|---|
> | what the server **declares** in `initial_max_streams_uni` | ⛔ **at least 19** |
> | what remains to RCP after the three of HTTP/3 | **16**, which is the normative number |
> | ⚠ and the count **is not believed, it is measured** | the transport probe counts the unidirectional streams the peer has really opened and judges `dichiarati − contati ≥ 16`. `[?]` **on a browser the three could be more** — a *grease* stream, for instance — and nobody has measured it |
>
> ⚠ **And the right number is 19 even when it looks generous**: the two words that decide in this
> line are **«disponibili»** (available) — not «dichiarati» (declared) — and **«in ogni momento»** (at any moment). The reading that saves the
> 16 makes both of them dead words.
| **the server MUST withstand the refusal to open a stream** instead of considering it a fatal error | video consumes **one stream per frame**: at 60 per second, the credit the browser grants is consumed fast |

> ### ⛔ «Il credito viene rinnovato mano a mano che gli stream si chiudono» — **FALSE, and measured**
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

> ⛔ **Corrected on 9 Aug 2026 by measurement S1** — this line said: *«il server DEVE annunciare
> `Alt-Svc: h3=":7447"` sulla risposta TCP, o il browser non passerà mai a QUIC»*. **It is false**, and it
> was mine: **WebTransport does not use `Alt-Svc` at all** — zero occurrences in the three specifications, with
> a positive control `[S]`. A WebTransport session opens **its own** HTTP/3 connection towards
> the address it is given, without discovery and without upstream negotiation.
>
> ⭐ **And it removes a danger I had declared**: the silent fallback to TCP — «la
> pagina si apre e il desktop non arriva mai» — **cannot happen**, because there is no fallback
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
> *It said:* «*chi ne riceve uno prima chiude con `ERRORE_PROTOCOLLO`*». ⛔ **And «chi ne riceve uno
> prima» is a substitute quantity**: the receiver has nothing to measure other than the order in which its
> own network layer delivers events to it, and the two streams are independent. ⇒ It was enough to
> **lose the packet that carries `SESSIONE`** for a conforming client to kill a session in
> which the server had done everything right — **I1 broken because the line loses packets**, that is the
> condition I1 exists to protect.
>
> ⚠ *It is the **sixth** of the family* **P8 → P11 → P13 → P14 → P19 → P20** *(`LEZIONI.md` §1.13, and
> ⭐ the **seventh** is of 24 Aug 2026 — see the box just below). And
> even the first cure proposed — «solo se, quando il fotogramma arriva, i byte di `SESSIONE` non sono
> ancora arrivati» — remained a substitute: it moves the measurement from the wake-up of the coroutine to the bytes, and
> **the bytes are delayed by the network**. It would have been the seventh draft.*
>
> ⭐ **The true quantity is what the client has sent ITSELF** — `ATTACCA` — and it is the general form
> of the `numero` field of P14: **local, monotonic, independent of delivery**.
>
> ### ⭐⭐ **P21** — *24 Aug 2026, phase 9*: the seventh, and this time the family struck **the server**
>
> ⛔ The first draft of the cure *«dichiara morta una linea che perde troppo»* used
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
> ⇒ ⚠ **The lesson P21 adds to the six before**: *«locale e monotona»* **is not enough**. A
> quantity must be tested **on the two known extremes**, and must **order them in the right direction** — if it does
> not, it is not a calibration to redo: it is the wrong quantity (`LEZIONI.md` §1.33). ⛔ And it was not found
> by a rereading: it was found by the **test client** on its first run against a server that
> really sends.
| **input** — unidirectional | the client | **only one**, opened ⛔ **after having received `SESSIONE`** and kept open |
| **clipboard** — unidirectional | both | one **per transfer** |

⛔ **The client MUST NOT open bidirectional streams beyond 0. The server MUST NOT open bidirectional
streams.** Whoever receives one closes with `ERRORE_PROTOCOLLO`.

> ### ⛔⛔ Before reading: **the «primi due byte» are not the first bytes of the stream** — finding P18
>
> *12 Aug 2026. Found by the **test client**, on its first live run, and not by a
> rereading: `[M]` the run ended red with «canale di controllo mai aperto», and the cause was that
> the client applied this line **to the letter**.*
>
> ⛔ On WebTransport every stream carries a **preamble**: the stream type (`0x54` for
> unidirectional, `0x41` for bidirectional, in variable-length encoding — on the wire `40 54` and `40 41`)
> followed by the **session number**. ⇒ Whoever reads the «primi due byte» **of the stream** derives
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

> ⛔ *Corrected on 10 Aug 2026, finding **R11.9**: the `0x00` row said «il controllo vive
> solo sullo **stream 0**», and it was the remainder of the bare-QUIC draft that §4.2 had already removed on the
> evening of 9 Aug (finding R1.5). Finding R1.5 named **this section too**, and the cure
> had been applied to only one of the two places.*
>
> ⛔ **The channel is recognised by the high byte of `tipo`, never by the stream number**, and the second
> answer to the same question had remained in here — that is in the section that §0-bis presents as
> the cure of the «buco più insidioso». Whoever implemented §2.5 to the letter wrote a receiver that
> looks for the control channel by number, and the diagnosis that came out was *«il client non apre il
> canale»* **while the client had opened it**. ⚠ *The same word survived in the table of
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

It is `REVIEWER.md` §5 applied to the wire: *«l'indulgenza che nasconde è esattamente ciò che devi
togliere»*.

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

### 3.1 What «chiudere» means, in bytes

*Added on 9 Aug 2026: «chiude la connessione» admitted at least three different implementations,
and two of them make the reason disappear exactly when it is needed.*

Whoever detects the violation, **in this order**:

1. **MUST** write in the log *what* it did not understand — the type received, the length, the
   state it was in. Not «errore di protocollo»;
2. **MUST** send `CONGEDO` (§8) with the reason, on the control channel, **if the control
   channel is still usable**;
3. **MUST** close the **WebTransport session** with the application error code equal to the
   **reason code** of §8.2.

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.4**.* This line said «la connessione QUIC
> con `CONNECTION_CLOSE` di tipo applicativo». **A page cannot do it**: the API exposes the
> closing *of the session*, with its own code, not that of the HTTP/3 connection underneath — which
> may carry other things. They were two different planes, and §8.1 imposed the rule on the client too, that is on whoever
> does not have the API. One programmer closed the session and declared the rule fulfilled; the other
> looked for the connection API, did not find it, and left point 3 unimplemented — **and was
> as conforming to the text as the first**.

⭐ **The third point is the one that saves diagnoses**: if the farewell does not arrive — because the stream
was broken, because the message was unreadable — the reason travels all the same, inside the closing
of the session. In v1 the server wrote «congedo il client» and the client read «errore di rete»
for **three phases** (`LEZIONI.md` §1.7): here the two sides have two roads to tell each other the same thing, and
the acceptance test of §11 checks **from the receiving side** that at least one of the two has arrived.

⚠ Code **0** means «chiusura senza motivo» and **MUST NOT** be used: every closing has
a reason from §8.2.

---

## 4. The handshake

### 4.1 Even before: the certificate

> ### ⭐ Rewritten twice on 9 Aug 2026 — and the second time by a measurement
>
> **First draft**: four steps the client had to implement — compute the fingerprint,
> compare it with the remembered one, stop if it changes, accept silently if there is none.
>
> **Second**: «quei passi li fa già il browser, non è più codice nostro».
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

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.2**.* Here it was written, with a ⛔, that *«la
> pagina e la sessione WebTransport devono presentare **lo stesso** certificato»*, while §4.1-bis
> imposes **two** of them with another ⛔. Two normative lines that contradict each other, and neither cited
> the other: whoever obeyed this one served the page a certificate that the other obliges to
> regenerate every fourteen days, **making the warning reappear every two weeks** — that is
> the symptom §4.1-bis declares as the consequence of the opposite mistake.
>
> ⭐ **The fact that unties the knot** was already in the house, in `web/rapporti/S1-certificato.md`: with
> `serverCertificateHashes` the browser **does not look at the exception**, it looks at the fingerprint. So the two
> certificates must not be «lo stesso» — they must be **declared in two different ways**, and
> the user sees only one warning, the page's.

`[?]` **What remains to be measured is only Safari**: whether there the exception is enough by itself, that is whether
publishing the fingerprint can be done without. ⚠ *The general question that stood here — «l'eccezione
copre WebTransport?» — **already has an answer for two engines out of three**, and it is no: the box at the top
of this section gives it. Keeping it open made people plan a measurement already done (finding **R1.25**).*

### 4.1-bis ⛔ `serverCertificateHashes` — **the normal road**, not a safety net

*Promoted from safety net to main road on the evening of 9 Aug 2026, after measurement S1:
it was not an alternative, it is **the only mechanism** browsers expose for a server without a
domain.*

> ⛔ *Corrected on the night of 9 Aug 2026, finding **R4.4** of the review of the phase 1 bench.*
> The row «chi resta fuori» said *«`[S]` WebKit non lo implementa: su Safari, iPhone e iPad la
> strada è l'eccezione»*. **It has been false since October 2025**, and `STUDI.md` §web §3.1 and `DECISIONI.md` §1.7 had
> already been corrected **on the same 9 Aug**: this document had not.
>
> ⛔ **And the damage was of the kind that makes no noise, because this file is the referee.** Whoever
> read it to the letter wrote the branch *«su Safari l'impronta non serve, si va di eccezione o di
> certificato vero»* — and wrote it **conforming to the specification**, while whoever read `STUDI.md` §web
> published the fingerprint for all three. Two diverging implementations, both in the right.
> ⚠ And a bench that had applied the criterion *«una libreria che va con Chrome e non con Safari
> non è una libreria che va»* would have **failed both candidates**.

| | |
|---|---|
| **what it is** | the SHA-256 fingerprint of the session certificate travels **inside the page**, and the browser accepts without warnings. It is our trust model, made with the lever browsers offer on purpose. ⛔ **Of the DER bytes of the certificate** — not of the public key and not of the PEM bytes. ⚠ *DER was missing here and was in `DECISIONI.md` §1.5 row 7 since 9 Aug (finding R1.14): aligned on the night of 10 Aug 2026, and it is the same damage as then — whoever computes the fingerprint on the wrong envelope gets a comparison that **never matches**, with the symptom «WebTransport non si connette» and no error naming the fingerprint* |
| ⭐ **and it is no longer `[S]`** | `[M]` **9 Aug 2026**, on **two independent engines**: a WebTransport session towards a **self-signed ECDSA P-256 certificate of 13 days**, with the fingerprint published in the page and **no warning**, opened on **Chrome 151** (30.2 ms) and on **Firefox 140** (52.0 ms), and the bytes came back identical from both. Bench `banchi/01-b2-*`, document `FASI.md` §01-filo-nudo |
| ⚠ **and what the two engines DO NOT prove** | they are two teams that do not know us, so their agreement counts — ⛔ **but what served was `aioquic`, not an implementation of ours**: this measures **the trust model**, not the server. And **Safari stays out by decision** (`DECISIONI.md` §1.8) |
| **the constraint** | `[S]` certificate valid **less than 14 days**, **ECDSA P-256** key, no RSA, **SHA-256** fingerprint, and `allowPooling` at `false` |
| ⭐ **why the rotation does not show** | it is **the server itself that serves the page**: it regenerates the certificate before it expires and writes the current fingerprint into it. The user touches nothing and does not know it exists |
| ⛔ **what it does not cover** | **loading the page**, which is a TCP connection of its own. There the warning with the click remains — or the real certificate, for whoever has a domain |
| ⭐ **and the same road is AVAILABLE on all three engines** | `[R]` **WebKit implemented it on 2 Oct 2025** (bug 300057, `NetworkTransportSessionCocoa.mm`) and it ships in **Safari 26.4**: iPhone and iPad have **the same** road as the other two, not one to be rescued. ⛔ **Available, not verified**: on Safari nobody has tried it (row above, `DECISIONI.md` §1.8), and *«vale su»* would be a claim of working supported by `[R]`, that is by reading a commit — form **E1**. ⚠ *Corrected on 10 Aug 2026, finding **R11.16**: this row and the one above said, in the same table, that it holds on three engines and that Safari stays out. This file is the **referee**, that is the place where a deduction weighs more than in the product documentation* |

⛔ **Hence two certificates, and they must be kept distinct in the code**: a **long-lived** one for the page, which
is the one on which the user grants the exception and which therefore **must not change** more often than
necessary; a **short-lived** one for the session, which rotates by itself. ⚠ Confusing them makes the warning
reappear every two weeks, and nobody would connect the two things.

⛔ **And the fingerprint the page holds grows old.** A tab left open for two weeks
holds the fingerprint of a certificate that has meanwhile been rotated: on reconnection the browser
refuses, and the symptom is *«non si collega più e non dice perché»*. The two cures, and **the second is
the one chosen**:

| | |
|---|---|
| reloading the page | it works and throws away the state: the user loses what they were looking at |
| ⭐ **asking for the current fingerprint** | ⛔ **and it does not go through RCP**: the session is not yet open, so there is no channel on which to ask. The page fetches it **from the server that served it**, with an ordinary request, and tries again |

⚠ *Brought over on the evening of 9 Aug 2026 from report S1 (finding **O6**), which declared it as
«va deciso dove sta questo aggiornamento in RCP». The answer is: **outside** RCP.*

⚠ **And the consequence on acceptance testing, which holds in any case**: a bench that tests trust **MUST**
also test the **second** connection, and a third with the key changed. The
single-connection test stays green forever (`LEZIONI.md` §2.1).

### 4.2 The control channel

The client opens the **first bidirectional stream of the WebTransport session**. That is the control
channel, it stays open for the whole session, and its closing **is** the end of the session.

> ⛔ *Corrected on the evening of 9 Aug 2026, finding **R1.5**: here there was «(identificatore 0)», and it is a
> remainder of the bare-QUIC draft.* In an HTTP/3 connection QUIC stream number 0 is already
> taken — it is that of the request that **establishes the WebTransport session itself** — and the API
> exposes no number: it opens a stream and returns an object. Whoever read «0» to the letter
> looked for the control channel where it will never arrive, with the diagnosis «il client non apre il
> canale» **while the client has opened it**.

⛔ **In bytes**: a FIN on that stream, from either of the two parties, closes the session.
Whoever receives it **MUST** consider it finished; it **MUST NOT** keep sending **on any channel,
including the control one**.

> ### ✅ Decided on 11 Aug 2026 by the user: **silence** — `DECISIONI.md` §7.14
>
> *Until today this line forbade sending «sugli altri canali» and was silent about control. On a
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
> ⚠ **The price is paid in §8.1**, not here: that section imposes the farewell on «chi chiude», and from
> today it carries written that **whoever has received a `FIN` is not «chi chiude»**. Without that sentence this
> decision would leave the contradiction standing instead of closing it.
>
> ⛔ **And a premise that was false must be stated, because it is the one with which the decision was taken**:
> *«il server non attacca mai di sua iniziativa»*. It does, and it is the most measured behaviour
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
| `video.livello` | client | the maximum level it can decode, e.g. `5.1`. ⛔ The server **MUST** emit a stream of level not higher, and **does not guess it**: a level declared too low does not give a network error, **it makes the decoder refuse the configuration** and the symptom is «il browser non apre il flusso» *(finding **O12**)* |
| `video.misura_massima` | client | `LARGHEZZAxALTEZZA` it can decode, e.g. `3840x2160` |
| `audio.codec` | both | list among `opus`, `pcm` |
| `input.tocco` | client | `si`, `no` — reserved, in RCP/1 it is always `no` |
| `appunti.testo` | both | `si`, `no` |
| `client.nome` | client | free text for the log, e.g. `remotix-linux 0.1.0` |
| `banco.marca` | server | `si`, `no` — ⭐ *new, night of 9 Aug*: the **bench function** of §7.5 is on. ⛔ It is `no` in every normal installation, and a server that declared it `si` by mistake **writes it in the log at every start** |

⛔ **The form of names and values is constrained**, or «ignorare quel che non si conosce» becomes
«indovinare»:

- a **name** is made of `a-z`, `0-9`, `.` and `_`, from 1 to 64 bytes;

> ### ⛔⭐ The underscore is from 10 Aug 2026, and it was found by **the validator**
>
> This line said *«`a-z`, `0-9` e `.`»* — and three lines below, the table defines
> **`video.misura_massima`**, which contains that character. ⛔ **The specification contradicted
> itself**: an implementation that had applied the rule to the letter would have closed with
> `ERRORE_PROTOCOLLO` a capability **defined by this very document**, and the symptom — *«il
> client cade appena manda `CIAO`»* — would have named neither the rule nor the name.
>
> ⭐ **It was found by `banchi/01-b4-validatore.py` on its first run**, that is a program
> written by reading only this file, before a byte of server existed. It is precisely the
> job §11 assigns to it: *«client e server non si collaudano l'uno contro l'altro»*.
>
> ⚠ **Of the two cures this one was chosen**, and it is 🔸 derived: admitting `_` instead of renaming the
> capability. Renaming would touch a name already cited in `STUDI.md` §web and in `SPECIFICHE.md`, and the
> underscore is the convention the rest of the document uses in field names
> (`tela_larghezza`, `max_idle_timeout`).
- a **value** is printable UTF-8 text, at most 256 bytes;
- a **list** inside a value is written separated by commas, without spaces: `hevc,av1`;
- ⛔ **a name repeated twice is `ERRORE_PROTOCOLLO`.** «Vince l'ultimo» and «vince il primo» are
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
> «un **nome** sconosciuto si ignora» and was silent on everything else: an unknown value inside a
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

⛔ The server **MUST NOT** distinguish in the reason between «utente inesistente» and «parola d'ordine
sbagliata»: both are `CREDENZIALI_ERRATE`. And it **MUST** apply **the address ban**
before answering (§4.4-bis). ⚠ *This line said «la **limitazione della frequenza** dei
tentativi», which was the form replaced on 10 Aug 2026 by `DECISIONI.md` §1.9: one does not get out of the ban
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
> read it that way: it counted as «byte spediti dopo la fine» **everything** that arrived, and the case
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
> readings — «si passa a PAM e si consuma un tentativo» against «è errore di protocollo e la
> connessione cade» — give two different robustness profiles, because in the second an attacker
> who sends empty credentials **does not increment the count** of §4.4-bis. ⚠ *It said «nessuno dei due
> contatori», and they were the two of the previous form: since 10 Aug 2026 the count is **only one**, on the
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
> *that it exists*, *that it answers distinguishing «tolto» from «non era bannato»* and *that it writes in the log*.
> ⛔ **The form is not indifferent, and it has been paid for**: `remotix --sblocca IND` as a **second
> process** does not work — the ban lives in the memory of the serving process, a second process can
> only rewrite the file, the server would keep answering `TROPPI_TENTATIVI` until the restart, and
> **whoever gave the command sees it exit with zero**. Since the night of 10 Aug 2026 the two
> implementations speak the same protocol of **one line on a Unix socket `0600`** — `SBLOCCA
> <indirizzo>` → `TOLTO` / `NON-BANNATO`, and `PING` → `PONG` to say *«il comando c'è»*. The full
> account is in `FASI.md` §01-filo-nudo («Che cosa NON ha funzionato»), not here.

⭐ **The fixed delay stays, and it is not redundant with the ban.** The server **MUST NOT** answer
`CREDENZIALI` before **one second** has passed since reception, **even when the answer is
`AMMESSO`**. The ban removes whoever guesses; the fixed second removes **timing** as a
channel — without it, «utente inesistente» answers in a millisecond and «parola sbagliata» in fifty,
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
> This paragraph said *«il rifiuto di un indirizzo bannato **non passa** dal secondo fisso: si
> decide **prima** di `CREDENZIALI`»*. ⛔ **They are two incompatible lines in the same section**: a
> refusal decided *before* `CREDENZIALI` has no `RESPINTO` to send, because `RESPINTO` is the
> answer to a message that has not yet arrived — and §8.2 has `TROPPI_TENTATIVI` travel precisely
> inside a `RESPINTO`.
>
> ⛔ **And it reopened a contradiction that finding R11.10 had closed that same day**, for the
> reason that still holds: *«un rifiuto immediato dentro la finestra e uno ritardato fuori rimettono
> il **tempismo** come canale, dal lato opposto a quello che il ritardo fisso toglie»*. An address
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
commander's. Without it, the command answers *«non era bannato»* for every address, **forever and without
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
address**, and the one that tests this rule fails on purpose. With twelve hours, «si aspetta la
scadenza» is not a cure — the bench uses the unlock command, and the limiter bench **does not
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
 └── stringa desktop             one of: gnome · kde · xfce · lxqt · cinnamon · sconosciuto
```

⭐ **The granted canvas can be different from the one asked for**, and it is the case of the fallback on KDE
< 6.8 (`SPECIFICHE.md` §6.3): the session was already alive with another size and cannot change it. The
client **MUST** adapt by rescaling, and the server **MUST** have written the fallback in the log.

⛔⛔ **And the second reason is the common one, not the exception: the canvas OUTLIVES the session.**
The stage stays at the size at which the previous client left it, and `SESSIONE` grants
**that one**, not the one asked for in `ATTACCA`. ⇒ A client that attaches after another **of the same
user** — the graphical session is one per user, and multi-tenant does not exist — receives a canvas
it did not ask for and whose **origin it does not know**, and has no way to tell it apart from a
fallback. ⚠ **It is not «la finestra di un altro»**: it is the size its own previous connection
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
> ⚠ *The first row said* **«stretta di mano TLS finita»** *since 9 Aug 2026. It was `[?]` **R3.27**
> — «"stretta di mano TLS finita" non è un istante che i due lati condividono»: in WebTransport the
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
> exactly the connection that *«tiene un posto e non lo dichiara a nessuno»*, which is the first line
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

## 5. Il quadro dei canali

| Canale | Trasporto | Verso | Affidabile? |
|---|---|---|---|
| **controllo** | il **primo** stream bidirezionale della sessione (§4.2) | ↔ | sì |
| **video** | **uno stream unidirezionale per fotogramma** | server → client | sì, ma abbandonabile |
| **audio** | datagram | server → client, e ↑ per il microfono | no |
| **input** | uno stream unidirezionale riservato | client → server | sì |
| **appunti** | uno stream unidirezionale per trasferimento | ↔ | sì |
| **cursore** | sul canale di controllo | server → client | sì |

⚠ Il microfono è nella tabella perché il verso è previsto, **ma RCP/1 non lo definisce**: vedi §12.

### 5.1 ⭐ Perché un fotogramma è uno stream

È la scelta di disegno più importante del protocollo.

Se il video viaggiasse su **un solo** stream, un fotogramma lento bloccherebbe tutti quelli dopo —
il blocco di testa — e su una rete mobile la sessione si accumulerebbe addosso il proprio
passato. Se viaggiasse su **datagram**, dovremmo riscrivere frammentazione e ritrasmissione, cioè
rifare QUIC dentro QUIC.

Con uno stream per fotogramma: gli stream sono indipendenti, quindi un fotogramma in ritardo non
tocca i successivi; e soprattutto il server **PUÒ** chiamare `RESET_STREAM` su un fotogramma che
non serve più — perché ne è già partito uno più recente — e i byte non ancora spediti non partono
affatto.

⛔ **È così che si onora l'invariante I1 senza tradirla**: non si *riduce la qualità* per prudenza,
si *butta il passato* quando è passato. E ogni abbandono **DEVE** essere scritto nel registro:
un fotogramma perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto dal lato che
riceve.

> ### ⛔ L'abbandono ha **DUE forme osservabili**, non una — *13 agosto 2026, `[M]`*
>
> *Questo paragrafo, e §6.2 con lui, descrivevano una forma sola: lo stream **azzerato**. Alla fase
> 3 se n'è vista una seconda, e un client scritto sulla prima **non la riconosce**.*
>
> | forma | che cosa vede il client | quando succede |
> |---|---|---|
> | **A — lo stream azzerato** | uno stream aperto che finisce con `RESET_STREAM` invece che con FIN | il server aveva già **fatto uscire almeno un byte** di quel fotogramma |
> | ⛔ **B — il buco nei `numero`** | **nessuno stream**, e il `numero` successivo salta di uno | il server aveva **consumato il `numero`** e poi ha abbandonato **prima che un byte uscisse** |
>
> ⛔ **Quale delle due il client veda dipende da un dettaglio che nessuno dei due lati controlla:
> se un byte era già uscito.** Non è una scelta del server e non è un'informazione che il protocollo
> porti — è il momento in cui l'abbandono cade rispetto alla scrittura.
>
> ⇒ **Le conseguenze, e sono normative:**
>
> - il client **DEVE** trattare **tutt'e due** le forme come un buco, e in tutt'e due mandare
>   `RICHIEDI_CHIAVE` (§5.2). ⛔ Un client che guardi i soli `RESET_STREAM` **perde la forma B in
>   silenzio**, e il sintomo è quello che §5.2 esiste per evitare: immagini via via più sfasciate
>   senza nessun errore sollevato da nessuno;
> - il server **DEVE** scrivere nel registro **tutt'e due**, e distinguerle: sono la stessa
>   decisione, ma dal lato che riceve hanno **aspetti diversi**, e un registro che ne nomina una
>   sola non spiega quel che il client ha visto;
> - ⚠ e un banco che innesta l'abbandono **deve saper produrre tutt'e due**, o certifica metà della
>   regola credendo di certificarla tutta.
>
> ### ⛔⛔ E c'è un terzo caso, che **non è osservabile affatto** — ed è il più pericoloso
>
> Un fotogramma **buttato per mancanza di credito** (§2.3) non è nessuna delle due forme: non si apre
> nessuno stream **e il `numero` non viene consumato**, perché §6.2 lo fa crescere solo per i
> fotogrammi che il server **decide di spedire**. ⇒ ⛔ **Nessuno stream, nessun buco, nessun segnale:
> dal lato che riceve non è successo niente.**
>
> ⛔ **Quindi il client non può accorgersene, e non può chiedere la chiave.** Se il server non la
> produce **da sé**, l'immagine si sfascia **per sempre e in silenzio** — con un GOP lungo non ne
> arriva più una da sola. È il difetto **B-18**, trovato il 13 agosto 2026.
> ⇒ ⭐ **È la ragione per cui l'obbligo di §5.2 — «quando il server abbandona un delta DEVE mandare
> una chiave appena può, senza aspettare che il client la chieda» — non è una prudenza: in questo
> caso è l'unica cosa che esiste.** Il client non ha una domanda da fare.

### 5.2 ⛔ Il prezzo dell'abbandono, e come si paga

*Aggiunta il 9 agosto 2026, ed è il difetto di disegno che il censimento ha trovato — non una
lacuna di scrittura.*

Il video è compresso **con predizione fra fotogrammi**: un fotogramma *delta* è la differenza da
quelli precedenti. Abbandonarne uno, o perderne uno, non rovina **quel** fotogramma: rovina **tutti
quelli che vengono dopo**, finché non arriva un fotogramma **chiave** — che si decodifica da solo.

§5.1 concede l'abbandono e non diceva né come si riconosce un fotogramma chiave, né come se ne
chiede uno. Le due cose, e la prima costa **zero byte**:

1. ⛔ **il tipo del fotogramma lo dice l'intestazione**: `0x0301` è un fotogramma **chiave**,
   `0x0302` un **delta** (§6.2). Il campo `tipo` c'era già e i suoi valori non erano definiti;
2. ⛔ **il client chiede una chiave** con `RICHIEDI_CHIAVE` (`0x000D`, §7.1) sul canale di
   controllo.

**Le regole:**

- ⛔ **il primo fotogramma che il server spedisce dopo `SESSIONE` DEVE essere una chiave**
  (`0x0301`). ⚠ Senza questa riga un delta in apertura è conforme, e il client non ha modo di
  accorgersene: non c'è nessun buco nella successione dei `numero`, e il decodificatore non solleva
  errori. Il sintomo sarebbe *«il desktop compare a pezzi»*, e non nominerebbe né il protocollo né
  la chiave;
- ⛔ **e lo stesso vale a ogni cambio di tela**: il primo fotogramma spedito alla **misura nuova**,
  dopo un `TELA(ADATTATA…)` (§7.1), **DEVE** essere una chiave (`0x0301`) — e **DEVE** essere una
  chiave *vera*, cioè portare con sé tutto quel che serve a decodificarla da sola: per HEVC i suoi
  VPS/SPS/PPS davanti all'IDR. ⚠ Senza questa riga un delta alla misura nuova è **conforme**, e il
  client non ha modo di accorgersene: non c'è nessun buco nei `numero`, e — `[M]` 12 agosto 2026,
  Chrome 151 su Linux con VA-API, banco `banchi/02-pagina-tela-*` — **il decodificatore HEVC non
  solleva nessun errore**: continua a emettere fotogrammi alla misura **vecchia** e dipinge
  un'immagine sfasciata, diversa a ogni giro. Il sintomo sarebbe *«il desktop si strappa quando
  ridimensiono la finestra»*, e non nominerebbe né il protocollo né la tela. ⛔ E la stessa prova su
  **AV1** dà `EncodingError` su Chrome e su Firefox `[M]`: ⇒ **la regola serve perché sul codec
  principale il sintomo è muto**, e una regola non si scrive sul codec che si comporta bene;
- ⛔ **e il client riconfigura il decodificatore sulla prima CHIAVE alla misura nuova, non sul
  `TELA`.** ⚠ *Senza questa riga le due cure del 12 agosto si contraddicono sullo stesso fotogramma:
  §6.2 dice che un fotogramma in volo alla misura precedente **DEVE** essere accettato e dipinto,
  questa riga qui sotto dice che uno alla misura sbagliata **si butta** — e chi avesse riconfigurato
  sul `TELA` (la lettura naturale di §7.1, «la tela in vigore **dopo** questo messaggio») si
  troverebbe le due regole a comandare il contrario. Il documento non diceva **in nessun punto**
  quando si riconfigura, e le due letture erano tutt'e due conformi e divergevano sul filo. Rilievo
  **P10**, trovato applicando la cura di poche ore prima.* ⭐ E costa zero: `[M]` la chiave vera va
  bene **sia** riconfigurando **sia** senza;
- ⛔ il client, dal canto suo, **NON DEVE** consegnare al decodificatore un fotogramma la cui misura
  non è quella per cui il decodificatore è configurato **né quella tollerata da §6.2**: lo butta e lo
  tratta come un buco. ⚠ E non è una prudenza in più: `[M]` un `VideoDecoder` riconfigurato alla misura nuova pretende una chiave
  (`DataError: a key frame is required after configure()`), quindi senza la riga qui sopra quella
  chiave non arriverebbe mai e il cambio di tela costerebbe un `RICHIEDI_CHIAVE` e un fermo-immagine
  **ogni volta**. ⭐ Con la riga qui sopra, `[M]` la stessa chiave va bene **sia** riconfigurando
  **sia** senza: 8 celle su 8 su HEVC e su AV1, su Chrome e su Firefox, in tutt'e due i versi;
- ⛔ il server **NON DEVE** abbandonare un fotogramma **chiave**. Abbandonare la cura non è una cura;
- ⛔ quando il server abbandona un delta, **DEVE** mandare un fotogramma chiave **appena può** —
  senza aspettare che il client lo chieda, perché il client se ne accorge un giro di rete più tardi.
  ⭐ **E questo obbligo non è una prudenza: è l'unica cura che abbiamo** `[S]` — a un delta mancante
  il decodificatore **non solleva nessun errore**, si limita a produrre immagini via via più
  sfasciate fino alla chiave successiva. `[?]` L'alternativa vera sarebbero i **sotto-livelli
  temporali**, che permettono di buttare certi fotogrammi senza rompere niente: se `EncSliceLP`
  dell'Intel li sappia produrre — ✅ **MISURATO il 22 agosto 2026, ed è NO**: `[M]` il driver non
  dichiara `EncRateControlExt` su **7 profili su 7**, mentre lo dichiara per **VP9 sullo stesso
  entrypoint** e per H.264/HEVC su **AMD `EncSlice`** — ⭐ due controlli positivi; e nei byte che
  escono **6 celle su 6** danno `sps_max_sub_layers = 1` con tutti i `temporal_id = 0`.
  ⇒ ⭐ **«Ogni abbandono costa una chiave» resta in vigore, e adesso ha una misura sotto invece di
  una `[?]`.** ⚠ E la strada vicina è chiusa dal **ritardo**, non dalla banda: `[M]` con `-bf 1`
  escono **59 figure buttabili su 120** a qualità invariata (−0,065 dB) e **−16 % di banda**, ⛔ ma
  **67 ms di riordino** — da solo oltre i 50 ms dati a *tutto* il pezzo nostro. `[?]` Resta aperto
  se un codificatore VA-API scritto da noi potrebbe costruirli lo stesso: `EncPackedHeaders = 0x1f`
  dice che le intestazioni le impacchetta **l'applicazione**. 📖 `fasi/08-l-anello.md` §4-D;
- ⛔ il client **DEVE** mandare `RICHIEDI_CHIAVE` quando si accorge di un **buco** nella successione
  dei `numero`, o quando il decodificatore rifiuta un fotogramma;
- ⛔ finché non arriva una chiave, il client **NON DEVE** mostrare fotogrammi che sa incompleti:
  tiene l'ultimo buono. Un'immagine sfasciata è peggio di un'immagine ferma per un decimo di secondo;
- ⚠ il server **PUÒ** ignorare una `RICHIEDI_CHIAVE` che arrivi entro **200 ms dall'ultima chiave
  che ha spedito** — ⛔ non dall'ultima richiesta ricevuta, e la differenza non è una sfumatura:
  contando dalle richieste, due client insistenti spostano l'orologio all'infinito e la chiave non
  parte mai. Durante una raffica di perdite le richieste arrivano a decine, e ogni chiave costa
  dieci volte un delta: assecondarle peggiorerebbe esattamente la condizione che le ha provocate.
  ⭐ **È l'eccezione 5 di §3, ed è dichiarata lì.**
  ⛔ **La grazia vale solo per i doppioni** (22 set 2026): una `RICHIEDI_CHIAVE` il cui
  `ultimo_numero` è uguale o più nuovo dell'ultima chiave spedita dice che il client quella chiave
  l'ha già decodificata — il buco è venuto dopo — e il server **DEVE** accoglierla. `[M]` Ignorarla
  lasciava la pagina ferma per sempre con un video pesante, su Firefox e su Chrome;
- ⛔ il client manda **una** `RICHIEDI_CHIAVE` per buco; se la chiave non arriva entro **1 s** ne
  manda un'altra (22 set 2026). Una al secondo, non una per fotogramma: la spirale resta chiusa;
- ⛔ finché una **chiave** è ancora nella coda d'uscita, il server **NON** abbandona i delta che le
  vengono dietro per la soglia della coda (§5.1): non la accorcerebbero, e ogni delta abbandonato
  apre un buco che chiede un'altra chiave (22 set 2026, `[M]` la spirale vista con un video 4K).

⚠ **E una conseguenza che tocca la fase 9**: se la linea è così cattiva da far abbandonare in
continuazione, il rimedio **non** è mandare chiavi in continuazione — è **calare i fotogrammi**,
come dice `SPECIFICHE.md` §8.3. Un fotogramma chiave per ogni delta abbandonato è la spirale.

### 5.3 L'audio: il formato è fisso, non negoziato

*Aggiunta il 9 agosto 2026: «Opus, con PCM come base» dice il codec e non dice il formato, e due
implementazioni che scelgono due frequenze diverse producono un rumore che sembra un difetto di
rete.*

| | |
|---|---|
| frequenza | **48 000 Hz**, sempre, per entrambi i codec |
| canali | **2**, interlacciati |
| **Opus** | un pacchetto Opus per datagram, blocchi da **20 ms** |
| **PCM** | campioni **s16, little-endian**, ⛔ **5 ms per datagram** — 480 campioni, **960 byte**, che con i 12 dell'intestazione fanno **972** |

> ### ⛔ Corretto la sera del 9 agosto 2026 — rilievo **R1.1**, il più grave della revisione
>
> Questa riga diceva **20 ms anche per il PCM**: 1920 campioni, **3840 byte**, più 12 di
> intestazione = **3852**. ⛔ Un datagram QUIC **non è frammentabile** — deve stare in un pacchetto
> solo — e su un percorso vero il carico utile disponibile è **~1200 byte** `[S]`.
>
> **Quindi l'audio PCM non sarebbe partito mai, su nessuna rete.** E il danno era doppio, perché
> §4.3 fa del PCM **il controllo positivo di Opus**: il giorno in cui Opus non si negozia, si
> ripiega su una strada che non esiste — e il banco cercherebbe il difetto in Opus.
>
> ⚠ **La forma dell'errore è quella di `LEZIONI.md` §2.2**, dove il banco contava i blocchi mentre
> l'audio era rumore a fondo scala. Qui non sarebbe arrivato nemmeno il rumore.
>
> ⭐⭐ **MISURATO — `[M]` 17 agosto 2026, e la stima era ottimista di un quinto.**
>
> | | Chrome 151 | Firefox 140esr |
> |---|---|---|
> | subito dopo `ready` | **1024** byte | **1024** byte |
> | dopo 800 ms | **1024** byte | ⭐ **1214** byte |
>
> ⇒ Il PCM di questo paragrafo (972 byte, intestazione compresa) **ci sta**, ma su Chrome per
> **52 byte** — cioè per meno del 6 %. ⛔ La riga che apriva la `[?]` — *«se il numero fosse più
> basso di 972, il PCM scende ancora»* — **non scatta**, e i 5 ms restano.
>
> ⚠ E i due motori non danno lo stesso numero né lo stesso numero nel tempo: Firefox parte da 1024
> e **cresce a 1214** quando ha misurato il percorso. ⇒ Chi dimensionasse i blocchi leggendo
> `maxDatagramSize` **una volta sola** prenderebbe il numero peggiore senza saperlo.
>
> `[?]` **Resta aperto il percorso non locale**: questa misura è su rete locale, via cavo. Su rete
> mobile il percorso può portare meno, e il PCM è la strada **senza margine** — proprio quella su
> cui si ripiega quando Opus non si negozia. La sonda è `banchi/07-b40`.

⛔ **Il little-endian del PCM è l'unica eccezione all'ordine di rete di §6, ed è deliberata**: sono
un carico utile, come i byte di HEVC, non un campo di protocollo. Scritta qui perché un'eccezione
non dichiarata è una divergenza silenziosa fra due implementazioni.

⚠ Il volume **non viaggia**: appartiene alla sessione ed è al massimo (invariante I5,
`SPECIFICHE.md` §10).

### 5.4 Gli appunti: i limiti

| | |
|---|---|
| tetto di un trasferimento | **1 000 000 byte** ⚠ — non 1 MiB: il messaggio che lo porta ha sei byte di inquadratura e quattro di lunghezza, e un tetto uguale a quello del messaggio (§6.1) renderebbe **illegale il testo grande esattamente quanto il tetto** |
| testo più grande | ⛔ **non si annuncia affatto**, e il mittente lo **scrive nel registro**. NON DEVE essere troncato: un testo troncato incollato in un terminale è peggio di un testo mancante |
| tipo | ⛔ solo `text/plain;charset=utf-8`, e il testo **DEVE** essere UTF-8 valido |

### 5.5 Il cursore: i limiti

| | |
|---|---|
| misura massima | **256×256** |
| formato | **BGRA premoltiplicato**, riga per riga senza riempimento: `larghezza × altezza × 4` byte |
| cursore nascosto | ⛔ `larghezza = 0` **e** `altezza = 0`, tutt'e due, e nessun byte d'immagine. Una sola delle due a zero è `ERRORE_PROTOCOLLO` |
| il punto attivo | ⛔ **DEVE** stare dentro l'immagine: `0 ≤ attivo_x < larghezza`, `0 ≤ attivo_y < altezza`. ⛔ **Unica eccezione, il cursore nascosto**: con `larghezza = altezza = 0` l'intervallo è vuoto, e allora `attivo_x` e `attivo_y` **DEVONO** valere `0`; qualunque altro valore è `ERRORE_PROTOCOLLO`. ⚠ *Il tipo resta `i16` e la riga «può essere negativo» è caduta: senza un intervallo, `attivo_x = -32768` era legale secondo ogni riga del documento, e due client avrebbero disegnato il puntatore in due posti diversi (rilievo **R1.21**)* |

> ⛔ *L'eccezione è del 10 agosto 2026, rilievo **R11.11**, ed è 🔸 derivata: si corregge senza
> discussione.* La riga sopra dichiara **obbligatorio** `larghezza = 0` **e** `altezza = 0` per il
> cursore nascosto; la riga sotto pretende `0 ≤ attivo_x < larghezza`, e con `larghezza = 0`
> quell'intervallo è **vuoto**: nessun valore di un `i16` lo soddisfa. ⛔ **Un `CURSORE_FORMA` di
> cursore nascosto violava la riga accanto sempre, qualunque cosa il mittente ci mettesse** — e un
> ricevente che applicasse §5.5 alla lettera chiudeva con `ERRORE_PROTOCOLLO` ogni volta che il
> puntatore sparisce, con il sintomo *«la sessione cade quando entro in un campo di testo»*, che
> non nomina né il cursore né la regola.
>
> ⚠ È la stessa forma del trattino basso di §4.3 trovato dal validatore di B4: **una regola che
> vieta un caso che il documento stesso definisce**. E R1.21 dichiarava di aver chiuso proprio
> questo — *«larghezza 0 con altezza diversa da 0, e un punto attivo senza intervallo»*: l'intervallo
> era stato aggiunto **senza eccettuare il caso che la riga accanto rende obbligatorio**.

---

## 6. Il formato dei messaggi

**Ordine dei byte: rete (big-endian).** Nessun campo a lunghezza variabile fuori da quelli
dichiarati con una lunghezza esplicita.

### 6.0 I tipi elementari

*Aggiunta il 9 agosto 2026. Erano usati in tutto il documento e definiti da nessuna parte.*

| Tipo | | |
|---|---|---|
| `u8`, `u16`, `u32`, `u64` | interi senza segno, big-endian | |
| `i16`, `i32` | interi con segno, **complemento a due**, big-endian | |
| **stringa** | `u16 lunghezza` + esattamente `lunghezza` byte di **UTF-8**, **senza terminatore** | ⛔ UTF-8 non valido è `ERRORE_PROTOCOLLO`. Una stringa vuota è `lunghezza = 0` |
| **elenco** | `u16 quante` + gli elementi in fila | |

⛔ **Nessun campo è allineato e nessun riempimento è ammesso.** I campi si leggono e si scrivono in
sequenza, uno dopo l'altro. Un byte in più che «fa tornare i conti» in una struttura C è la forma
esatta del difetto corretto in §6.2 il 9 agosto.

⛔ **Ogni intero ha un solo significato di «assente»**, e va dichiarato dove serve: non esistono
valori sentinella impliciti.

### 6.1 Sui canali affidabili — controllo, input, appunti

```
 0        2        6                    6+lunghezza
 ├────────┼────────┼─────────────────────┤
 │ tipo   │ lungh. │ corpo               │
 │ u16    │ u32    │                     │
```

⛔ `lunghezza` **DEVE** essere il numero esatto dei byte del corpo. Un ricevente che legge una
lunghezza incoerente con quel che il tipo prevede **DEVE** chiudere con `ERRORE_PROTOCOLLO`.

⛔ Nessun messaggio **DEVE** superare **1 MiB**. Chi ne annuncia uno più grande viola il protocollo.

⛔ **E la lunghezza si controlla prima di allocare.** Un ricevente che alloca `lunghezza` byte e poi
verifica ha già regalato un megabyte a chiunque sappia scrivere sei byte.

### 6.2 Sugli stream del video

Uno stream, un fotogramma. Nessuna lunghezza: **la fine dello stream è la fine del fotogramma** —
⛔ **ma solo se lo stream è finito con un FIN**.

> ⛔ *Aggiunte due parole la sera del 9 agosto 2026, rilievo **R1.7**, e senza di esse il documento
> era rotto proprio dove §5.1 concede di abbandonare.* Il server apre lo stream del fotogramma 101,
> spedisce l'intestazione e 40 KB su 60, poi lo **azzera** perché è partito il 102. Il client ha in
> mano 40 KB e uno stream «finito»: consegnandoli al decodificatore ottiene un rifiuto o — peggio —
> mezza immagine. **Un fotogramma abbandonato e uno completo avevano lo stesso aspetto**, ed è la
> forma d'errore **E8**.

⛔ **La regola, in due righe:**

- uno stream chiuso con **FIN** porta un fotogramma **completo**;
- uno stream **azzerato** (`RESET_STREAM`) porta un fotogramma **incompleto**: il client **DEVE**
  buttare quel che ha ricevuto, **NON DEVE** consegnarlo al decodificatore, e **DEVE** trattarlo
  come un buco (§5.2);
- uno stream chiuso con **FIN prima dei 28 byte** dell'intestazione è `ERRORE_PROTOCOLLO`: non è un
  fotogramma corto, è una lunghezza che non torna (§3);
- ⛔ **e un fotogramma abbandonato può non presentarsi come stream affatto**: se il server ha
  consumato il `numero` e ha abbandonato **prima che un byte uscisse**, il client non vede nessuno
  stream — vede un **buco nella successione dei `numero`**. È la **forma B** dell'abbandono, e va
  trattata come un buco esattamente come l'azzeramento (§5.1, il riquadro delle due forme).

```
 0        2        4        8        12       16       24       28   28+…
 ├────────┼────────┼────────┼────────┼────────┼────────┼────────┼─────┤
 │ tipo   │ codec  │ largh. │ altezza│ numero │ istante│ input  │ dati│
 │ u16    │ u16    │ u32    │ u32    │ u32    │ u64    │ u32    │     │
```

⛔ **L'intestazione è di 28 byte esatti, senza riempimento**, e i dati del fotogramma cominciano
all'offset 28. Nessun campo è allineato: si legge e si scrive in sequenza.

> ⚠ *Corretta il 9 agosto 2026, prima di qualunque implementazione.* Il disegno dava `… 24 │ 32`,
> cioè otto byte a un campo dichiarato `u32`: quattro byte di riempimento non dichiarati, e due
> implementazioni che potevano indovinare uguale senza che nessuno se ne accorgesse — il difetto
> muto contro cui questo documento è stato scritto (§0). Scelto **28** dall'utente: un riempimento
> va giustificato, e qui non lo giustificava niente.

| Campo | |
|---|---|
| `tipo` | ⭐ `0x0301` **fotogramma chiave**, `0x0302` **fotogramma delta** (§5.2). Altri valori: `ERRORE_PROTOCOLLO` |
| `codec` | `1` = HEVC, `2` = AV1, ⭐ `3` = **H.264** (dal 20 agosto 2026). **DEVE** essere quello negoziato in §4.3. ⛔ **Un numero non si riusa mai**: il `2` resta AV1 anche adesso che AV1 non si negozia più, perché un client vecchio che sentisse «2» e ricevesse altro **dipingerebbe spazzatura senza un errore**. ⚠ E il numero massimo definito sta in **un posto solo** nel codice (`RCP_CODEC_VIDEO_MAX`): il giorno in cui è entrato il 3, tre guardie diverse portavano il numero scritto a mano e una è rimasta indietro — **ogni fotogramma H.264 è stato buttato in silenzio** |
| `largh.`, `altezza` | la misura di **questo** fotogramma. ⛔ In RCP/1 **DEVONO** valere la **tela in vigore** — quella concessa in `SESSIONE` (§4.5), **oppure** l'ultima concessa da `TELA` se nel frattempo è stata adattata (§7.1) — e chi ne riceve altre chiude con `ERRORE_PROTOCOLLO`: il client riscala alla **vista**, non alla tela (`SPECIFICHE.md` §6.1). Il campo esiste lo stesso perché il giorno in cui si decidesse di codificare più piccolo quando la finestra è piccola — `DECISIONI.md` §5.0-ter, che è una `[?]` volutamente fuori dal modello — **il protocollo non cambia**: cambierebbe questa riga |
| `numero` | ⛔ contatore dei fotogrammi **che il server decide di spedire**, che cresce di uno per ciascuno — **compresi quelli che poi abbandona**, e ⛔ **NON** per quelli che non spedisce affatto. ⚠ *Diceva «dei fotogrammi **catturati**» e insieme «che il server decide di spedire»: **due letture nella stessa frase**, e alla fase 3 si separano — calando i fotogrammi quando la linea non porta (I1, §8.3), la prima lettura aprirebbe **un buco per ogni salto**, quindi una `RICHIEDI_CHIAVE` per ognuno, cioè **la spirale che §5.2 esiste per evitare** proprio quando la linea è cattiva. Corretto il 12 agosto 2026, rilievo **P16**, trovato scrivendo il prodotto.* Un buco nella successione è quindi normale e **significa qualcosa**: è il segnale su cui §5.2 fa chiedere una chiave. ⛔ **Il primo fotogramma di una sessione porta `numero = 1`, e lo `0` è riservato**: vuol dire «nessun fotogramma», che è il significato che §7.1 gli dà in `RICHIEDI_CHIAVE`. ⚠ È la stessa convenzione dell'`id` dell'input (§7.3), e per la stessa ragione: senza, `RICHIEDI_CHIAVE(0)` vuol dire due cose e il server non può scegliere — cioè il valore sentinella implicito che §6.0 vieta. ⛔ **E al giro del contatore lo `0` si salta**: l'aritmetica è modulo 2³², una sessione può durare più di un giro, e da `0xFFFFFFFF` si passa a **`1`** — senza questa riga il valore riservato tornerebbe in circolo da solo |
| `istante` | microsecondi dell'orologio **monotono del server** alla cattura |
| `input` | ⭐ **l'identificatore dell'ultimo input iniettato prima della cattura**; **0** se nessuno |

⛔ **Il tetto vincola prima di tutto chi spedisce**: il server **NON DEVE** produrre un fotogramma
più lungo di **16 MiB**. Se la codifica ne producesse uno più grande, **DEVE** ricodificarlo a
qualità inferiore e **scriverlo nel registro** — mai spedirlo. Chi ne riceve uno più lungo chiude
con `ERRORE_PROTOCOLLO` invece di continuare ad accumulare.

> ⚠ *La prima metà è della sera del 9 agosto 2026, rilievo **R1.23**: il tetto vincolava solo il
> **ricevente**, cioè era una punizione per chi subisce.* Una tela 7680×4320 è legale (§4.5) e il
> desiderato è a 10 bit: un fotogramma chiave di una scena complessa a quella misura può superare i
> 16 MiB. Il client avrebbe staccato la sessione perché il server ha fatto una cosa che §4.5 gli
> permette — e §5.2 gli vieta pure di abbandonare le chiavi, quindi non aveva vie d'uscita.
>
> ✅ **MISURATO il 22 agosto 2026** — `[M]`, 📖 `fasi/08-l-anello.md` §4-D:
> - ⭐ **alla tela dell'utente il tetto è irraggiungibile**: 2560×1080, **404 chiavi vere**, massimo
>   **21 433 byte = 0,13 %**, margine **782×**. Nemmeno il rumore uniforme ci arriva (15,1 %);
> - ⛔ **a 7680×4320 si sfonda davvero**: rumore uniforme **28,9 MiB, 8 su 8** sopra il tetto, e la
>   grana forte arriva al **94,9 %**. *(La misura del ripiego in software, `libx264` passando da
>   libavcodec, non vale più dopo la fase 18.)*;
> - ⚠ e i **10 bit qui sono otto promossi** — `DECISIONI.md` §2.3-ter. Infatti `[M]` l'etichetta
>   `main10` a 8K costa **933 byte in MENO** di `main`: non porta informazione che non ci sia;
> - ⛔⛔ **il difetto di forma però non è quello che si credeva.** La **scala delle ricodifiche è
>   corta di uno scalino** — l'ultimo tentativo lascia **16,654 MiB**, il quarto ce l'avrebbe fatta,
>   e si perde per il **4 %** — e quando si arrende il codificatore **butta il fotogramma anche se è
>   una chiave**, che **§5.2 vieta**. ⇒ È la spirale: il client resta rotto, e ogni
>   `RICHIEDI_CHIAVE` costa tre ricodifiche che non producono niente. ⭐ La cura ha già il suo
>   numero: `[M]` **QP 51 dà 1,771 MiB a 8K**, quindi una chiave **entra sempre**.

⛔ **L'ordine, e chi lo rimette a posto.** Gli stream sono indipendenti, quindi i fotogrammi
**possono arrivare fuori ordine**. Il client:

- **DEVE** scartare un fotogramma il cui `numero` è **precedente** all'ultimo già consegnato al
  decodificatore;
- **DEVE** trattare `numero` come aritmetica **modulo 2³²**, confrontando le differenze con segno —
  a 60 fotogrammi al secondo il contatore gira dopo due anni e due mesi, e una sessione può durare
  di più;
- **DEVE** riconoscere un **buco** e chiedere una chiave (§5.2).

⛔ **E c'è il verso opposto, che è il quinto della stessa famiglia**: un fotogramma alla misura
**nuova** può arrivare **prima** del `TELA` che la concede — il `TELA` viaggia sul canale di
controllo, il fotogramma su uno stream suo, e **niente ne ordina la consegna**. ⇒ Il client che
ricevesse una misura che «non è mai stata in vigore» chiuderebbe **una sessione in cui nessuno ha
sbagliato**.

⛔ **Il client NON DEVE chiudere: trattiene il fotogramma**, e lo scrive nel registro. ⭐ **E fino a
quando lo trattiene non è un numero: è una condizione** — finché resta una `ADATTA_TELA` che **il
client ha spedito** e a cui nessun `TELA` ha ancora risposto. Arrivato quel `TELA`, il fotogramma
trattenuto **si rigiudica** contro la tela che quel `TELA` dichiara in vigore, e da lì è un
fotogramma come tutti gli altri: prima la regola dell'ordine, poi quella della misura. ⛔ **E se
nessuna `ADATTA_TELA` è senza risposta non si trattiene niente**: una misura che il client non ha
nessun motivo di aspettarsi è `ERRORE_PROTOCOLLO` subito.

⚠ **E il `TELA` arriva per forza**, che è la ragione per cui questa è una fine e non un'attesa
aperta: §7.1 impone *«a ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`, riuscito o no»*,
e il canale di controllo è **uno solo, affidabile e ordinato** (§4.2) ⇒ l'n-esimo `TELA` risponde
all'n-esima `ADATTA_TELA`, e chi trascina una finestra ne manda due senza che il conto si perda.
⛔ Un `TELA(RIFIUTATA)` chiude l'attesa quanto un `TELA(ADATTATA)`: il trattenuto si rigiudica contro
la tela rimasta in vigore, e di norma **è `ERRORE_PROTOCOLLO`** — il server ha spedito una misura che
non ha mai avuto.

⭐ **E la grandezza è «una richiesta in volo», non «la misura che il client ha chiesto»**: §4.5 dice
che *«la tela concessa può essere diversa da quella chiesta»* — su KWin < 6.8 è la strada normale
(`SPECIFICHE.md` §6.3) e la negoziazione di §6.4 concede il modo che il compositore **ha**. ⇒ Un
client che trattenesse solo i numeri che ha nominato chiuderebbe una sessione in cui il server ha
fatto esattamente quel che §7.1 gli permette. ⚠ È la stessa grandezza di **P20** — *quel che il
client ha spedito lui*: locale, monotona, indipendente dalla consegna.

> ⚠ *Questo paragrafo diceva «trattiene **finché non sa decidere**», e accanto portava un riquadro
> `[?]` che dichiarava aperta la domanda «fino a quando». Il prodotto la chiudeva con **otto
> fotogrammi** — un fondo osservabile invece di un orologio, che era già la lezione di P13, ⛔ ma pur
> sempre **una grandezza sostitutiva**. Chiusa il 13 agosto 2026, rilievo **P21**. ⭐ E la prima cura
> proposta — «la misura che il client ha nominato» — è stata **bocciata da un caso**: §4.5 permette
> al server di concedere una tela diversa da quella chiesta, quindi sarebbe stata l'ottava stesura.*

> ### ⛔ E il trattenimento **non ha tetto in byte** — la riga mancava
>
> *13 agosto 2026. Il paragrafo qui sopra dice fino a **quando** si trattiene, e non dice **quanto**.
> Sono due domande diverse, e la seconda non aveva risposta da nessuna parte.*
>
> ⛔ **La condizione di fine è corretta e non basta.** §7.1 obbliga il server a rispondere a ogni
> `ADATTA_TELA` con un `TELA`, riuscito o no — ed è la ragione per cui la condizione «finché una
> `ADATTA_TELA` è senza risposta» **finisce**. ⛔ Ma un server che **non risponde** non viola una
> regola che il client possa far rispettare: fa crescere la coda del client **senza limite**, e il
> client conforme continua a trattenere finché la memoria regge. ⇒ Il difetto non è del client:
> **è una riga che manca a questo documento.**
>
> ⇒ **Le due regole:**
>
> - ⛔ il client **DEVE** avere un tetto al trattenuto, e superarlo **NON è `ERRORE_PROTOCOLLO`**:
>   il server non ha sbagliato niente in un modo che il client possa dimostrare. Si butta il più
>   vecchio, **lo si scrive nel registro**, e si tratta come un buco (§5.2). Un fermo-immagine con
>   una riga di registro è meglio di una sessione che finisce la memoria in silenzio;
> - ⛔ **e il tetto si conta in FOTOGRAMMI, non in richieste in volo.** ⚠ Il paragrafo qui sopra non
>   lo diceva, e sono due grandezze diverse: le richieste in volo dicono **se** si trattiene, i
>   fotogrammi dicono **quanto**. ⭐ E un fotogramma si conta **una volta sola anche se viene
>   rigiudicato due volte** — un trattenuto che al primo `TELA` non si risolve e resta in attesa del
>   secondo **non è due fotogrammi**. *Il prodotto lo faceva già giusto; il documento non lo diceva.*
>
> ⏳ `[?]` **Quale sia il numero non è deciso qui**: dipende dalla memoria del dispositivo e dal peso
> di una chiave (§6.2 ne ammette 16 MiB), e sceglierlo a caso rifarebbe l'errore di §1.13 —
> una grandezza sostitutiva al posto di quella vera. ⛔ Ma *«non c'è tetto»* non è una risposta, ed
> era quel che il documento diceva tacendo.

⛔ **E la regola dell'ordine si applica PRIMA di quella della misura**: un fotogramma il cui `numero`
è precedente all'ultimo già consegnato **si scarta**, e la sua misura non si guarda nemmeno.
⚠ *Senza questa precedenza le due righe di questa stessa sezione si contraddicono, e vince la più
severa su una scena in cui nessuno ha sbagliato: la chiave che chiude la tolleranza **scavalca** i
fotogrammi in volo — non per caso, ma perché quello vecchio è **il più grosso** (§5.2 vieta di
abbandonare una chiave) e quello nuovo è più piccolo. Rilievo **P14**, 12 agosto 2026, e la stessa
famiglia si era già spostata di un passo tre volte: **P8 → P11 → P13 → P14**.*

⚠ **Il cambio di tela e i fotogrammi in volo.** Dopo aver ricevuto un `TELA(ADATTATA)` (§7.1) il
client **DEVE** accettare i fotogrammi la cui misura vale **una tela che è stata in vigore da quando
la coda ha cominciato a svuotarsi**, dipingendoli riscalati alla vista e scrivendolo nel registro.
⛔ **E la tolleranza non finisce a orologio: finisce quando arriva la prima chiave alla misura
nuova**, che §5.2 gli garantisce. Da quel fotogramma in poi una misura vecchia è
`ERRORE_PROTOCOLLO`; e lo è **subito** una misura che non è mai stata in vigore in quella finestra
⛔ **e che nessuna `ADATTA_TELA` senza risposta può ancora concedere**: se una c'è, il fotogramma
**si trattiene** invece di far chiudere (il paragrafo qui sopra).

> ⚠ *Diceva «la tela **precedente**», al singolare, e ⛔ **chi trascina una finestra ne manda due**:
> 1920×1080 → `TELA(1600,900)` → `TELA(1280,720)`, e la chiave aperta prima di tutto — la più
> grossa, la più lenta, e quella che §5.2 vieta al server di abbandonare — porta 1920×1080, che non
> è né quella in vigore né la precedente. La sessione sana cadeva lo stesso, **un passo più in là**
> della scena che la cura aveva appena chiuso. Corretto il 12 agosto 2026, rilievo **P11**.*
⭐ È la **sesta** eccezione dichiarata a §3, ed è la terza scritta per il verso in cui mancava: §7.1
la dà già alle coordinate di input, per la stessa ragione — il cambio di tela è l'unico momento in
cui i due lati hanno legittimamente due verità diverse. ⛔ Senza, un client conforme **uccide una
sessione sana**: gli stream sono indipendenti, il fotogramma aperto prima che l'`ADATTA_TELA`
arrivasse al server porta legittimamente la misura di prima, e §5.2 vieta al server di abbandonare
una chiave — cioè di sgombrare il tubo proprio dei fotogrammi più grossi, che sono i più probabili
a essere in volo. ⇒ **Dal lato server non è curabile**, e per questo la riga è del client.

> ⛔⛔ *E la prima stesura di questa riga diceva «**per un secondo**», con un orologio — corretta due
> ore dopo, rilievo **P13**. La ragione è che **il secondo era la grandezza sbagliata**: quel che
> deve svuotarsi è una **coda**, e quanto ci mette un fotogramma già in volo dipende dalla **banda**,
> non dall'orologio. Una chiave 1920×1080 può pesare qualche MiB (§6.2 ne ammette 16) e su una linea
> cattiva — che è **dentro** il modello, il minimo dichiarato è 480p a 25 — arriva **dopo** il
> secondo. ⇒ Il client avrebbe chiuso un fotogramma spedito quando era legale, e che §5.2 vietava al
> server di abbandonare: non è solo una sessione sana che cade, è l'invariante **I1** — «mai a
> staccare» — rotta **perché la linea è lenta**, cioè nella condizione esatta che I1 esiste per
> proteggere. ⭐ E allungare il secondo avrebbe spostato il difetto invece di toglierlo: la
> tolleranza finisce su un **fatto osservabile sul filo** — la prima chiave alla misura nuova — che
> §5.2 garantisce esistere.*
>
> ⚠ *Aggiunta il 12 agosto 2026, difetto **D14**, e la marca non è nessuna delle due che questo
> documento usava: non è una **lettura doppia** e non è una **regola derivata** — è una
> **contraddizione interna**. Due implementazioni conformi e attente qui **non divergono**:
> producono lo stesso byte, la chiusura, ed è sbagliato. ⛔ È la specie che nessun confronto fra due
> implementazioni può trovare, ed è la stessa che la prima stesura di **P5** ha avuto per due ore
> quella mattina.*

⚠ **Che cosa il campo `input` dice davvero**, e va scritto qui perché nessuno gli attribuisca di
più: dice quale input era stato **iniettato**, non quale era stato **disegnato**. Che il
compositore l'avesse già reso non è garantito da nessuno. È una stima utile e gratuita — non la
misura del ritardo. Quella la dà il banco ad anello chiuso di `DECISIONI.md` §2.6.

⚠ **E `istante` non è un'ora**: è un orologio monotono che parte da un punto qualunque. Il client
**NON DEVE** confrontarlo con il proprio: solo con altri `istante` dello stesso server.

### 6.3 Sui datagram — l'audio

```
 0        2        4        12                12+…
 ├────────┼────────┼────────┼──────────────────┤
 │ tipo   │ codec  │ istante│ campioni         │
 │ u16    │ u16    │ u64    │                  │
```

| Campo | |
|---|---|
| `tipo` | `0x0401` — l'unico definito in RCP/1 |
| `codec` | `1` = Opus, `2` = PCM (§5.3) |
| `istante` | microsecondi dell'orologio monotono del server, del **primo** campione del blocco |

Un datagram, un blocco di Opus (o di PCM). Nessuna ritrasmissione, nessun riordino: chi riceve
scarta i datagram arrivati in ritardo rispetto a quelli già consumati.

⛔ Un datagram più corto di 12 byte, o con un `tipo` diverso da `0x0401`, si **scarta scrivendolo
nel registro**: ⚠ ed è la seconda eccezione dichiarata a §3, perché un datagram è per definizione
inaffidabile e chiudere la connessione per un pacchetto corrotto sarebbe una punizione della rete,
non del mittente.

---

## 7. I messaggi

### 7.1 Controllo

| Tipo | Nome | Verso | |
|---|---|---|---|
| `0x0001` | `CIAO` | → | versione e capacità del client |
| `0x0002` | `ECCOMI` | ← | versione e capacità del server |
| `0x0003` | `CREDENZIALI` | → | utente, parola d'ordine |
| `0x0004` | `AMMESSO` | ← | |
| `0x0005` | `RESPINTO` | ← | motivo |
| `0x0006` | `ATTACCA` | → | tela, disposizione, vista |
| `0x0007` | `SESSIONE` | ← | stato, tela concessa, desktop |
| `0x0008` | `VISTA` | → | la vista è cambiata: nuove larghezza e altezza |
| `0x0009` | `DISPOSIZIONE` | → | la disposizione di tastiera è cambiata |
| `0x000A` | `CURSORE_FORMA` | ← | forma e punto attivo del puntatore |
| `0x000B` | `ADATTA_TELA` | → | «adatta il desktop a questa finestra» — ⚠ dal nostro client **solo all'attacco e al riattacco** (§7.1); il protocollo lo ammette a sessione aperta da chiunque |
| `0x000C` | `CONGEDO` | ↔ | motivo |
| `0x000D` | `RICHIEDI_CHIAVE` | → | ⭐ *nuovo, 9 ago*: serve un fotogramma chiave (§5.2) |
| `0x000E` | `TELA` | ← | ⭐ *nuovo, 9 ago*: l'esito di `ADATTA_TELA` |
| `0x000F` | `BANCO_MARCA` | → | ⭐ *nuovo, 9 ago notte*: **funzione di banco** — cambia la marca, con un ritardo noto (§7.5) |
| `0x0010` | `BANCO_ESITO` | ← | ⭐ *nuovo, 9 ago notte*: l'esito di `BANCO_MARCA` (§7.5) |
| `0x0011` | `TERMINA_SESSIONE` | → | ⭐ *nuovo, 15 ago*: **l'utente vuole uscire** — la sessione grafica finisce e i suoi programmi si chiudono (§7.6) |

**I corpi** (`CIAO`, `ECCOMI`, `CREDENZIALI`, `AMMESSO`, `RESPINTO`, `ATTACCA`, `SESSIONE` stanno
in §4.3-4.5):

```
VISTA
 ├── u32 larghezza
 └── u32 altezza

DISPOSIZIONE
 └── stringa disposizione            (la forma è quella di §4.5)

ADATTA_TELA
 ├── u32 larghezza
 └── u32 altezza

TELA
 ├── u8  esito        1 = ADATTATA, 2 = RIFIUTATA
 ├── u8  motivo       0 se adattata; altrimenti:
 │                      1 = COMPOSITORE_INCAPACE
 │                      2 = MISURA_FUORI_LIMITI
 │                      3 = NON_ORA
 ├── u32 tela_larghezza      ⚠ la tela in vigore DOPO questo messaggio
 └── u32 tela_altezza

RICHIEDI_CHIAVE
 └── u32 ultimo_numero        l'ultimo fotogramma decodificato, 0 se nessuno

CONGEDO
 ├── u8      motivo           §8.2
 └── stringa dettaglio        per il registro, non per l'utente; può essere vuota
```

⛔ **`DISPOSIZIONE` a sessione aperta: una disposizione ben formata ma sconosciuta NON chiude la
sessione.** Il server **DEVE** scriverlo nel registro e **DEVE** tenere in vigore quella di prima.
⚠ È diverso da `ATTACCA` (§4.5), dove il congedo `SESSIONE_NON_SERVIBILE` è giusto perché non c'è
nessuna sessione da salvare: qui la tastiera di prima funziona ancora, e togliere all'utente il
lavoro aperto costerebbe **più del guasto** (`SPECIFICHE.md` §8.3, «mai staccare»).

⚠ `VISTA` **NON DEVE** far cambiare la tela, e ⛔ **in RCP/1 non cambia nemmeno la misura di quel
che si codifica**: i fotogrammi restano della misura della tela e il client riscala
(`SPECIFICHE.md` §6.1). Serve a due cose — a scegliere quanti bit spendere, perché una finestra
piccola guardata su uno schermo piccolo non ne merita quanti una grande; e a rendere gratuito il
giorno in cui `DECISIONI.md` §5.0-ter venisse chiusa. L'unico messaggio che cambia la tela è
`ADATTA_TELA`.

> ⛔ **Qui c'era scritto anche «ed è una scelta esplicita dell'utente», e dal 15 agosto 2026 non è
> più vero.** `DECISIONI.md` §5.0-sexies — decisa dall'utente il 14 agosto — fa chiedere al client
> **la tela della propria finestra all'attacco di ogni sessione**, da sé. ⇒ `ADATTA_TELA` resta
> l'unico messaggio che cambia la tela, ma non è più detto che dietro ci sia un dito: può esserci
> l'attacco. ⚠ Per l'arbitro non cambia niente — il messaggio, i controlli e la risposta sono gli
> stessi — e la riga si corregge perché **un documento che descrive un client che non esiste più
> smette di essere l'arbitro**.
>
> ### ⛔⛔ E DAL 17 AGOSTO 2026 DIETRO NON C'È **MAI** UN DITO — `DECISIONI.md` §5.1-bis
>
> Il ridimensionamento a caldo è uscito dal prodotto (*«non voglio mettere delle eccezioni nel
> progetto»*): **la nostra pagina manda `ADATTA_TELA` solo all'attacco e al riattacco**, e
> ridimensionare la finestra non ne produce nessuno.
>
> ⛔⭐ **Ma questa è una scelta del NOSTRO client, non una regola del protocollo, e le due non si
> confondono**: RCP/1 continua ad ammettere `ADATTA_TELA` **in qualunque momento a sessione
> aperta**, e il server **DEVE** continuare a rispondere con un `TELA` a chiunque lo mandi. ⚠ Un
> arbitro che scrivesse «il client non lo manda durante la sessione» dichiarerebbe **non conforme
> un client conforme** — e il primo a rimetterci sarebbe il nostro, il giorno in cui la decisione
> cambiasse. La riga sta qui perché descrive **chi lo manda oggi**, non che cosa è lecito.
>
> ⏳ **E resta una riga da scrivere**, trovata refutando la notte del 15 agosto: *che cosa fa il
> server quando il palco cambia misura **senza che nessun `ADATTA_TELA` gliel'abbia chiesto*** — un
> rimontaggio della sessione grafica dopo una caduta, per esempio. §6.2 dà al client un solo modo di
> accettare una misura inattesa (trattenere finché una richiesta è senza risposta), quindi un `TELA`
> non sollecitato **fa chiudere una sessione sana**: il server oggi non lo manda, e RICHIEDE invece
> al palco di tornare alla tela in vigore, con un'attesa che cresce. Funziona, ⚠ ma è una regola del
> prodotto che l'arbitro non nomina.
>
> ### ⭐ LA RIGA, SCRITTA IL 22 SETTEMBRE 2026 — e la richiesta non basta sempre
>
> ⛔ Il server **PUÒ** mandare **un** `TELA(ADATTATA)` non sollecitato, e **solo** quando in quella
> sessione **non è ancora uscito nessun fotogramma**: lì il client non ha visto un pixel a quella
> tela, non ne ha nessuno in volo, e non c'è nessuna corsa fra stream da arbitrare — il `TELA` è
> l'unica verità che avrà mai avuto. ⛔ **Dopo il primo fotogramma resta vietato**, e vale la regola
> di sopra: si richiede al palco, con un'attesa che cresce.
>
> ⚠ *Perché serve, e non è un'astrazione*: `[M]` 22 settembre 2026, prova a mano dell'utente su KDE.
> Il server si riavvia, la sessione Plasma gli **sopravvive** (I4) col palco a 2544×926, e il client
> rientra da una finestra di un'altra misura chiedendo 2560×962. La tabella delle tele dei palchi
> vive nel processo ⇒ col riavvio si azzera, e il ripiego di §4.5 — «si concede quel che il palco
> **ha**» — non ha niente da concedere. Tela in vigore 2560×962, palco 2544×926, §6.2 vieta di
> spedire un fotogramma di misura diversa: **schermo nero per sempre**, perché **KWin `--virtual`
> non ridimensiona** e la richiesta non può riuscire né oggi né fra un'ora. ⇒ «Richiedere al palco»
> è una cura che presuppone un palco capace di obbedire, e questa riga dice che cosa fare quando non
> lo è.

> ⚠ *Chiarito il 9 agosto 2026, e non era una sfumatura.* Questa riga diceva «serve al server per
> sapere **a che misura codificare**», e ci sono due voci di `DECISIONI.md` che si contraddicono
> sullo stesso punto: §5.2 dice che *«il codificatore lavora alla misura della finestra, non della
> tela»*, §5.0-ter dice che *«il server continua a codificare la tela intera e il client la
> rimpicciolisce»* e mette il contrario **volutamente fuori dal modello**, come `[?]`. Vince la
> seconda, perché è quella che regge insieme a `SPECIFICHE.md` §6.1 e §6.3 — dove il ripiego su
> KDE *«non costa una riga in più, perché è lo stesso codice del punto durante la sessione»*, e
> quel codice è la **riscalatura nel client**. La correzione è in `DECISIONI.md` §5.2.

⛔ Se il compositore non sa ridimensionare, il server **DEVE** rispondere ad `ADATTA_TELA` con
`TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, e il client **DEVE** mostrare la voce come spenta. NON
DEVE fingere che sia riuscito.

⛔ **A ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`**, riuscito o no. Un silenzio
lascia il client ad aspettare per sempre una risposta che non arriverà, e il sintomo è
«l'applicazione si è piantata».

⛔ **La vista non ha i vincoli della tela**, e va detto perché la riga precedente diceva il
contrario: qualunque misura da **1×1 in su** è legale, dispari compresa.

> ⛔ *Corretto la sera del 9 agosto 2026, rilievo **R1.17**.* Qui c'era scritto che la vista deve
> stare fra 320×240 e 7680×4320 **con i lati pari**, cioè i limiti della tela — e i limiti della
> tela esistono per una ragione che alla vista **non si applica**: i blocchi del codificatore. In
> RCP/1 la vista **non tocca nessun codificatore** (lo dice questa stessa sezione due righe sopra).
>
> Il caso concreto: l'utente stringe la finestra del browser a 300 pixel, o apre la pagina
> affiancata sul telefono. Con la riga vecchia il client aveva tre scelte, tutte cattive — mandare
> `VISTA(300×800)` e **farsi chiudere la sessione perché ha ridimensionato una finestra**; mentire
> arrotondando a 320, che è la forma d'errore **E2**; o tacere, e lasciare che il server spenda bit
> per una vista che non esiste più. ⚠ Su un telefono con fattore di scala 2,75 nessun
> arrotondamento è innocente: 393 pixel logici valgono 1080,75 fisici.

⚠ La vista non ha nessun vincolo di proporzione con la tela: se le proporzioni non combaciano, si
impagina con le bande (`SPECIFICHE.md` §6.2).

⚠ **Il cambio di tela e le coordinate in volo.** Dopo aver mandato `TELA(ADATTATA)` il server
**DEVE** accettare per **un secondo** coordinate di input valide sulla tela **precedente**,
saturandole alla nuova e scrivendolo nel registro; passato quel secondo, sono
`ERRORE_PROTOCOLLO`. ⭐ È la terza eccezione dichiarata a §3, e c'è perché il cambio di tela è
l'unico momento in cui i due lati hanno legittimamente due verità diverse: gli input partiti prima
che la risposta arrivasse non sono un difetto del client.

### 7.2 Cursore

`CURSORE_FORMA` porta la forma che il client deve disegnare:

```
CURSORE_FORMA
 ├── u16 larghezza          0 con altezza 0 = cursore nascosto (§5.5)
 ├── u16 altezza
 ├── i16 attivo_x           il punto che «punta», dentro l'immagine — ⛔ 0 se nascosto (§5.5)
 ├── i16 attivo_y
 └── immagine               larghezza × altezza × 4 byte, BGRA premoltiplicato
```

⛔ `larghezza` e `altezza` **NON DEVONO** superare 256 (§5.5), e la lunghezza del messaggio **DEVE**
valere esattamente `8 + larghezza × altezza × 4`. Una lunghezza che non torna è
`ERRORE_PROTOCOLLO`: è il caso in cui «leggo quel che c'è e vado avanti» produce un cursore fatto
di memoria altrui.

⚠ **La posizione non viaggia mai in questo verso.** La posizione del puntatore è del client, che
lo disegna da sé (`SPECIFICHE.md` §7.1). Qui viaggia solo la **forma**, e il ritardo di un giro di
rete sulla forma è il compromesso accettato.

### 7.3 Input

| Tipo | Nome | |
|---|---|---|
| `0x0101` | `PUNTATORE` | posizione assoluta sulla **tela**, non sulla vista |
| `0x0102` | `PULSANTE` | quale, premuto o rilasciato |
| `0x0103` | `ROTELLA` | assi, in scatti |
| `0x0104` | `LETTERA` | un carattere Unicode |
| `0x0105` | `POSIZIONE_TASTO` | codice di posizione, premuto o rilasciato |

⛔ **Ogni messaggio di input comincia con gli stessi due campi**, e poi ha i suoi:

```
 ├── u32 id             crescente, comincia da 1.  ⛔ 0 è riservato e vuol dire «nessun input»
 └── u64 istante        microsecondi dell'orologio monotono del CLIENT

PUNTATORE          + u32 x  · u32 y            coordinate sulla tela
PULSANTE           + u16 codice · u8 premuto   1 = premuto, 0 = rilasciato
ROTELLA            + i32 asse_x · i32 asse_y   unità da 120 per scatto
LETTERA            + u32 carattere             valore scalare Unicode
POSIZIONE_TASTO    + u16 codice · u8 premuto
```

| | |
|---|---|
| **i codici dei pulsanti e dei tasti** | ⛔ sono quelli di **evdev** (`linux/input-event-codes.h`): `BTN_LEFT` = `0x110`, `KEY_A` = `30`. ⭐ Non è una scelta di comodo: `libei` — cioè l'unico modo che abbiamo di iniettare input in un compositore Wayland — lavora in evdev, e ogni altra convenzione aggiungerebbe una tabella di traduzione che sbaglia in silenzio |
| **la rotella** | ⛔ unità da **120 per scatto**, ⚠ e i mezzi scatti esistono: `60` è mezzo scatto e **non DEVE** essere arrotondato a zero. ⭐ **Il segno è MISURATO** *(10 agosto 2026, su Mutter)*: il client manda `+120` quando l'utente gira la rotella **in su**, e ⛔ **il server DEVE invertire l'asse verticale** prima di passarlo a `libei` — vedi il riquadro |
| **il carattere** | ⛔ un **valore scalare Unicode**: da `0` a `0x10FFFF`, esclusi i surrogati `0xD800`-`0xDFFF`. Fuori intervallo è `ERRORE_PROTOCOLLO` |
| **l'identificatore** | ⛔ cresce di **almeno uno** a ogni messaggio, su tutto il canale di input — non uno per tipo. È quello che torna nel campo `input` dei fotogrammi (§6.2), e con contatori separati non tornerebbe niente |
| **l'`istante`** | ⚠ **nessuna regola di questo documento lo consuma**: il ritardo lo misura l'anello chiuso di `DECISIONI.md` §2.6, e il fotogramma porta indietro l'`id`, non l'istante. Resta perché è l'unico modo di sapere **quando l'utente ha mosso la mano** invece di quando il byte è arrivato, e serve alla diagnosi. ⛔ Il client scrive **microsecondi veri** e **NON DEVE** far credere a una precisione che non ha *(rilievo **R1.27**)*. ⚠ ⛔ **E la premessa di questa riga era FALSA — corretta il 14 agosto 2026, su misura dell'anello del modo classico della fase 4**: diceva *«l'orologio monotono è in millisecondi e la sua grana è deliberatamente ingrossata: il client scrive `millisecondi × 1000`»*. `[M]` su **Chrome 151**, pagina isolata fra origini, `performance.now()` ha grana **5 µs** — **duecento volte** più fine di quel che c'era scritto. ⇒ ⭐ **La regola sopravvive alla premessa che l'aveva prodotta** (*si scrive quel che si sa*), ⛔ ma un client che moltiplicasse i millisecondi per mille butterebbe via **199 parti su 200** di una misura che ha già in mano. ⚠ E la grana **dipende dall'isolamento fra origini**: dove non c'è, torna grossa — quindi si scrive quella che si ha e **si dichiara**, invece di fissarne una nel documento |

> ### ⭐ Il segno della rotella — rilievo **R1.26**, ed è MISURATO
>
> ⚠ *Questo riquadro finiva, fino all'11 agosto 2026, con* «**Finché non è misurata, questa riga
> resta `[?]`**» *— e la misura era stata presa la notte del 10, senza che nessuno la portasse qui
> (rilievo **R12C.7**, e la sonda lo aveva scritto di suo in* `web/rapporti/S-esiti-sonda.md` *§9,
> voce S.7). Chi avesse scritto l'iniezione dell'input alla fase 4 leggendo questa riga avrebbe
> scelto il segno a caso, e il sintomo è* «la rotella va al contrario» *— cioè la forma **E11** che
> questo riquadro esiste per evitare.*
>
> **Perché la domanda esisteva.** Questa riga diceva *«positive verso l'alto e verso sinistra. È
> l'unità di `wl_pointer.axis_value120`, quindi non si converte niente»*. ⛔ **Le due metà citano
> due convenzioni con segni opposti**: in evdev la rotella è positiva verso l'alto, in `wl_pointer`
> il valore è positivo nel verso in cui **scorre il contenuto**, cioè verso il basso. E «positive
> verso sinistra» non corrisponde a nessuna delle due. ⛔ E `libei` **non la scioglie**:
> `ei_device_scroll_discrete` documenta *«the y scroll distance in fractions or multiples of 120»* —
> **dichiara la grandezza e non il verso**. La convenzione non sta nell'API, sta nel compositore.
>
> ⭐ **LA MISURA — `[M]` 10 agosto 2026, 20:59:27→20:59:57 UTC.**
>
> | | |
> |---|---|
> | **che cosa si è visto** | `ei_device_scroll_discrete(0, **+120**)` → l'evento `wheel` della pagina porta **`deltaY = +114`** (`deltaMode = 0`, pixel) e la pagina **scende** di 114 px, cioè va **verso la fine del documento**. Con **−120**, `deltaY = −114` e la pagina **sale** |
> | **la scena, per intero** | macchina di prova **192.168.0.2**; sessione GNOME senza monitor da `banchi/00-sessione-gnome.sh` — `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; la pagina in **Firefox 140.13.0esr** in `--kiosk` a schermo pieno sul monitor virtuale, `dpr` 1 |
> | **dove si ricontrolla** | `banchi/01-s7-esiti.jsonl` (due giri, `7sd0u7jv` e `oq7jqrdv`), e il rapporto `web/rapporti/S-esiti-sonda.md` §1 |
>
> ⛔ **La conseguenza, ed è del server**: `deltaY` positivo vuol dire che il contenuto va **verso la
> fine** del documento, cioè che l'utente ha girato la rotella **in giù**; questa sezione fissa
> l'altra metà — il client manda `+120` quando l'utente gira **in su**. Le due convenzioni sono
> **opposte**, quindi **il server DEVE invertire il segno dell'asse verticale** prima di passarlo a
> `ei_device_scroll_discrete`. Iniettando il valore così com'è, lo schermo remoto scorrerebbe al
> contrario per **ogni** utente.
>
> ⭐ **E il confronto è onesto perché i due lati parlano la stessa lingua**: `deltaY` è esattamente
> la grandezza che il client legge quando l'utente gira la rotella vera. Non si confrontano due
> mondi: si misura due volte lo stesso strumento.
>
> **I controlli, e quel che ciascuno vale** *(la ricontata dell'11 agosto, `S-esiti-sonda.md` §0-bis,
> ha separato quel che è nel registro da quel che stava solo a schermo — e qui si riporta la
> separazione, non solo l'esito)*:
>
> | Controllo | Esito | `[M]` o `[?]` |
> |---|---|---|
> | ⛔ **il segno opposto** — si inietta anche `−120` | ✅ `+120 → +114`, `−120 → −114`: si misura **il segno**, non «che qualcosa si muove» | `[M]`, nel registro |
> | ⛔ **i due strumenti concordano** — l'evento `wheel` e lo spostamento vero di `scrollY` | ✅ concordano su tutte le prove | `[M]`, nel registro |
> | ⛔ **`natural-scroll` nei due stati**, col dispositivo rifatto da capo | ✅ **il segno NON cambia**: `+120 → +114` in tutt'e due i giri | ⚠ **metà**: `[M]` che due giri indipendenti danno lo stesso segno; `[?]` **che fossero i due stati** — l'etichetta stava solo nell'uscita a schermo del lanciatore |
> | **il silenzio** — dieci secondi senza iniettare | ✅ nessuno scatto | ⚠ è un'**assenza** di righe: coerente coi timbri, non provata da loro |
> | *in più* — `ei_device_scroll_delta` ha lo stesso verso? | ✅ sì | ⛔ **non ritrovabile**: nessuna riga del registro lo porta. Resta cosa vista, non misura consegnata |
>
> ⚠ **Un fatto in più, per chi scriverà l'iniezione**: uno scatto (120 unità) si traduce in **114
> pixel** su Firefox+Mutter, cioè tre righe. È il fattore di conversione di quella coppia, **non una
> costante del protocollo**: non si scrive qui e non si mette in nessuna formula.
>
> ⛔ **E che cosa NON è chiuso, perché «non chiuso» e «non misurato» sono due stati diversi.** La
> misura è su **Mutter**, e questa sezione vincola **cinque** desktop. Se a normalizzare è `libei`,
> il numero vale ovunque; se normalizza il compositore, la fase di KDE (la 11) troverà un segno diverso su KWin.
> `[?]` **resta per gli altri quattro**, e il banco è rieseguibile su KWin senza cambiare una riga
> della pagina (`banchi/01-s7-rotella.sh` + `01-s7-pagina.html`).
>
> ⚠ *Il precedente che questa riga citava era sbagliato, ed è stato corretto la notte del 9 agosto
> 2026 (rilievo **R4.15**): diceva che «in v1 questa esatta tabella di conversione è costata il
> banco della rotella». `LEZIONI.md` §2.3 dice un'altra cosa — il banco della rotella cercava
> `asse dy=-10` mentre il registro scriveva `asse dx=0 dy=-10`: **rosso, col codice corretto**. È
> una stringa cercata male, non una conversione col segno sbagliato, e citando la lezione sbagliata
> la si perde nel punto in cui si applicherebbe.*

⛔ **Le coordinate sono sulla tela, e sono indici di pixel**: `0 ≤ x < tela_larghezza`,
`0 ≤ y < tela_altezza`. Su una tela 1920×1080 l'angolo in basso a destra è **1919, 1079**. Il client
conosce la tela (§4.5) e sa dov'è la sua vista dentro di essa: la conversione è sua, **arrotondando
per difetto**. Il server **NON DEVE** applicare nessuna trasformazione alle coordinate ricevute, e
**DEVE** rifiutare con `ERRORE_PROTOCOLLO` una coordinata fuori intervallo — salvo il secondo di
grazia di §7.1, dove satura all'ultimo pixel valido.

> ⚠ *L'intervallo mancava, e la riga diceva solo «fuori dalla tela» (rilievo **R1.16**). Una pagina
> che divide la posizione del mouse per il fattore di scala e arrotonda per eccesso produce 1920 su
> una tela di 1920: una lettura lo inietta, l'altra **chiude la sessione**. E chiudere la sessione
> per un arrotondamento è la cosa che `SPECIFICHE.md` §8.3 vieta — «mai staccare».*

⛔ **`LETTERA` si usa quando si scrive del testo; `POSIZIONE_TASTO` quando è premuto un
modificatore di comando** — Ctrl, Alt, Super. Maiusc e AltGr **non** contano come comando: servono
a fare la lettera, e restano nel percorso di `LETTERA` (`SPECIFICHE.md` §7.3).

⛔ Se una `LETTERA` non è producibile nella disposizione della sessione, il server **DEVE**
scriverlo nel registro e **NON DEVE** mandare un carattere diverso né tacere.

⛔ **Al distacco si rilascia tutto.** Quando una connessione finisce — per congedo, per silenzio,
per errore — il server **DEVE** rilasciare **ogni tasto e ogni pulsante che risultano premuti**.
⭐ È la trappola 11 di `LEZIONI.md` §4 nella sua forma peggiore: un Ctrl rimasto giù in una sessione
che sopravvive al client rende il desktop inservibile al riattacco, e nessuno collega le due cose.

### 7.4 Appunti

| Tipo | Nome | |
|---|---|---|
| `0x0201` | `APPUNTI_ANNUNCIO` | «ho del testo nuovo» |
| `0x0202` | `APPUNTI_CHIEDI` | «mandamelo» |
| `0x0203` | `APPUNTI_TESTO` | UTF-8 |

```
APPUNTI_ANNUNCIO
 ├── u32 trasferimento       ⭐ l'identificatore, scelto da chi annuncia
 └── u32 lunghezza           quanti byte ha il testo disponibile

APPUNTI_CHIEDI
 └── u32 trasferimento       quello dell'annuncio a cui si risponde

APPUNTI_TESTO
 ├── u32 trasferimento       quello della richiesta che si sta servendo
 └── byte                    fino alla fine dello stream, UTF-8 valido
```

> ### ⛔ Due correzioni della sera del 9 agosto 2026 — rilievi **R1.11** e **R1.20**
>
> **L'identificatore mancava del tutto.** La regola *«ogni trasferimento va sul suo stream»* non era
> soddisfacibile: i tre messaggi viaggiano in **due versi** e gli stream sono **unidirezionali**,
> quindi un trasferimento ne occupa almeno due. E senza un campo che li leghi, con due annunci
> aperti nei due versi — *l'utente copia di qua mentre incolla di là* — le due implementazioni
> appaiano le richieste agli annunci **in ordine diverso e si scambiano i testi**.
>
> ⛔ Ciascun lato numera **i propri** trasferimenti, da 1 e crescendo. Un `APPUNTI_CHIEDI` con un
> identificatore che non corrisponde a nessun annuncio vivo è `ERRORE_PROTOCOLLO`.
>
> **E la seconda lunghezza è stata tolta.** `APPUNTI_TESTO` portava `u32 lunghezza` *dentro* un
> messaggio che ha già la sua lunghezza nell'inquadratura di §6.1: due verità sullo stesso fatto,
> cioè il difetto che §2.2 vieta con quelle parole. ⚠ Con una conseguenza sull'implementazione:
> il testo si legge **fino alla fine del messaggio**, e il tetto è quello di §5.4.

Bidirezionale. Si annuncia e si chiede, invece di spingere: chi copia un documento intero non lo
spedisce a nessuno finché qualcuno non incolla.

⛔ **Il contenuto è sempre e solo testo semplice in UTF-8**, e non c'è nessun campo che dichiari un
tipo: non esiste perché non c'è niente da scegliere. ⚠ *Questa riga diceva «un tipo diverso è
`ERRORE_PROTOCOLLO`», e nessun messaggio portava un campo di tipo — una regola che nessuna
implementazione poteva violare e nessun banco vedere fallire, e che invitava chi legge ad aggiungere
un campo inesistente (rilievo **R1.20**).*

⛔ **Ogni trasferimento ha il suo identificatore**, e i messaggi di trasferimenti diversi non si
mescolano. ⚠ Un `APPUNTI_CHIEDI` che arriva quando l'annuncio è già stato superato da uno più
recente si serve **con il testo attuale**, e il mittente lo scrive nel registro: è la corsa normale
fra due persone che copiano, non un errore. ⭐ **Ed è la quinta eccezione dichiarata a §3** — vedi
l'elenco lì.

⛔ Un `APPUNTI_TESTO` che nessuno ha chiesto è `ERRORE_PROTOCOLLO`: gli appunti si tirano, non si
spingono.

### 7.5 ⭐ La funzione di banco: la marca, e il ritardo noto

*Aggiunta la notte del 9 agosto 2026, rilievo **R3.4** della revisione del banco della fase 1, e
**prima del primo byte di codice** — §9 chiude la finestra dei tipi nuovi da lì in poi, e la clausola
che la teneva aperta era che allora non esistesse nessuna implementazione. ⛔ **Il primo byte è del
10 agosto 2026 e la finestra è chiusa** (§0-bis, §9): questi due tipi sono entrati con l'ultima
occasione, e non ce n'è una seconda. ⚠* Diceva «*la clausola che la tiene aperta è che **oggi** non
esiste nessuna implementazione*», *al presente — corretta l'11 agosto 2026, rilievo **R12C.2***.

⚠ **La sua marca resta 🔸, non ✅**, ed è registrata dove le decisioni stanno: `DECISIONI.md` §1.5
riga 26. La domanda *«era una decisione dell'utente?»* — rilievo **R11.15** — **è stata chiusa
l'11 agosto 2026**: no, non lo era, e resta togliibile senza tornare da lui.

> ### ⛔⭐ E DA OGGI NON ENTRA NEL PRODOTTO CONSEGNATO — ✅ 11 agosto 2026
>
> *`DECISIONI.md` §7.16, dall'utente: «l'utente deve vedere il desktop senza artefatti, come se
> fosse davanti al monitor del PC … si tiene quello che serve per i test, ma poi nel prodotto
> finale si fa pulizia».*
>
> ⛔ **Questa è una funzione di BANCO, e nel binario che si installa NON DEVE esserci.** Non spenta:
> **assente** — non compilata, non raggiungibile, e ⛔ **non trovabile cercandone le marche dentro il
> binario**. Sullo schermo di chi si collega non compare mai niente che non sia il suo desktop.
>
> ⚠ **«Spenta» era la forma di prima, e non basta più.** La funzione nasce spenta e
> `banchi/01-b5-violazioni.py` verifica che a funzione spenta il server rifiuti con
> `FUNZIONE_SPENTA`: quel comportamento **resta**, ed è giusto — ma vale per la **costruzione di
> prova**, che è la sola in cui questi due tipi esistano.
>
> ⛔ **E la differenza si misura, o è una buona intenzione**: *«non c'è»* e *«c'è ed è spenta»* hanno
> lo stesso aspetto da fuori. Si separano **cercando le marche dentro il binario consegnato** — la
> stessa tecnica con cui `banchi/01-p1-prodotto.sh` distingue un binario nuovo da uno vecchio. Il
> banco è della **fase 13**, dove il pacchetto nasce.
>
> ⭐ **Perché la funzione sopravvive comunque**: taratura del cronometro del ritardo alla fase 3 —
> si inietta un ritardo noto e si verifica che la mediana salga di esattamente quello. Toglierla del
> tutto avrebbe lasciato il tetto dei 50 ms **senza un modo di sapere se il numero è vero**.

> ### ⛔⛔ 13 agosto 2026 — **la funzione di banco NON dà il ritardo noto**, e non l'ha dato alla fase 3
>
> *Questo paragrafo è normativo e descrive un meccanismo che nel prodotto **non c'è**. Va scritto
> qui, o chi legge questa sezione crede di avere in mano uno strumento che non esiste.*
>
> | | stato `[R]` |
> |---|---|
> | la funzione | `BANCO_ACCESO 0` — nasce spenta, come §7.5 vuole |
> | ⛔ **il ramo `ACCETTATA`** | **è uno stub**: non dipinge, non aspetta il `ritardo_ms`, non produce l'`istante` che il messaggio promette |
>
> ⇒ ⛔ **P1, il controllo decisivo dell'anello del ritardo, alla fase 3 NON è passato di qui.**
> L'iniezione del ritardo noto è stata fatta **fuori dal prodotto**, ed è risultata `[M]` verde
> (N = 25 → **+25,08 ms**; N = 60 → **+58,58 ms**).
>
> ⭐ **E l'iniezione fuori dal prodotto non è un ripiego: è meglio.** L'ancora d'orologio del metro
> **non passa** per il percorso iniettato — se ci passasse, **P1 passerebbe anche a banco rotto**,
> perché i N millisecondi si sommerebbero identici da tutt'e due le parti. Un controllo decisivo
> che non sa più fallire ha smesso di essere un controllo (`LEZIONI.md` §1.2).
>
> ⇒ ⏳ **Che cosa resta da decidere, e non si decide qui**: se il ramo `ACCETTATA` vada completato o
> se i due messaggi vadano tolti dal protocollo, visto che la loro sola ragione dichiarata —
> «tarare il cronometro del ritardo» — è stata soddisfatta **senza di loro**. ⚠ Finché stanno
> scritti qui e non esistono nel codice, questa sezione descrive una cosa che non c'è: è la specie
> di difetto contro cui §0 esiste.

⚠ **E i due tipi hanno consumato la clausola di §9** che §12 dichiara essere stata *«l'ultima
occasione»* per aggiungere tipi di messaggio: restano nel documento, ⛔ ma d'ora in poi come
**funzione di banco dichiarata**, non come funzione del prodotto.

> ⛔ **Perché una funzione di banco sta nel protocollo e non nel codice di prova.** L'anello del
> ritardo di `DECISIONI.md` §2.6 misura **dal lato che riceve**: il client provoca un cambiamento
> visivo inequivocabile e guarda i fotogrammi che decodifica finché non lo vede. Perché quel numero
> valga, il banco deve poter **iniettare un ritardo noto** e verificare che la mediana salga di
> esattamente quello — ⛔ *«un banco che non lo fa non sa di misurare»*
> (`web/rapporti/S4-ritardo-disegno.md` §4.2, controllo P1).
>
> Quel comando **attraversa il filo**. Improvvisarlo nel codice di prova significa due
> implementazioni che se lo inventano diverso, cioè il difetto muto contro cui §0 esiste — e S4
> §5.3 lo dice con queste parole: *«va scritto in `RCP.md` come funzione di banco, non improvvisato
> nel codice di prova»*.

**I due messaggi, in byte:**

```
BANCO_MARCA                                          client → server
 ├── u32 id            ⛔ cresce di almeno uno a ogni messaggio; 0 è riservato
 ├── u32 colore        0x00RRGGBB — il colore a cui portare la marca
 └── u32 ritardo_ms    ⛔ il ritardo NOTO che il server DEVE aspettare prima di
                       dipingere. 0 = subito. È il controllo del banco

BANCO_ESITO                                          server → client
 ├── u32 id            quello di BANCO_MARCA
 ├── u8  esito         1 = ACCETTATA, 2 = RIFIUTATA
 ├── u8  motivo        0 se accettata; altrimenti:
 │                       1 = FUNZIONE_SPENTA
 │                       2 = RITARDO_FUORI_LIMITI
 └── u64 istante       microsecondi dell'orologio monotono del server, del momento
                       in cui la marca è stata dipinta. ⛔ 0 se rifiutata, ed è
                       l'unico significato di «assente» per questo campo (§6.0)
```

**Dove sta la marca, e chi la dipinge:**

| | |
|---|---|
| **la misura** | **16×16 pixel della tela**, nell'angolo in alto a sinistra: da `0,0` a `15,15` |
| ⛔ **perché 16 e non 1** | il video è codificato in **4:2:0**, quindi la crominanza è a metà risoluzione, e i codificatori lavorano a blocchi. Un quadratino piccolo o a cavallo di un bordo di blocco viene **spalmato**, e il banco leggerebbe un colore che non è stato mandato. ⚠ E chi riceve **DEVE** leggere la **mediana** dei 256 pixel, con tolleranza, non il pixel centrale |
| ⛔ **chi la dipinge** | **il server**, nel fotogramma che sta per codificare — **dopo la cattura**. ⚠ *Quindi la misura che ne esce **esclude il compositore**, e questo va dichiarato accanto a ogni numero: è il ritardo di* codifica → filo → decodifica → disegno*, non quello che l'utente sente. Il pezzo del compositore lo misura l'anello completo di `DECISIONI.md` §2.6, che passa dall'input vero* |
| ⚠ **e nella tela, non nella vista** | il client riscala: se vista e tela non coincidono, i 16×16 della tela diventano un'altra misura sul suo disegno, e **il calcolo è suo** |

**Le regole, e sono cinque:**

1. ⛔ **La funzione è SPENTA salvo che l'amministratore non l'accenda nella configurazione del
   server.** È l'invariante **I6** alla lettera — *ciò che cambia quel che si vede sta dietro un
   interruttore spento di suo* — e qui letteralmente dipinge sopra il desktop di qualcuno;
2. ⛔ **spenta, il server risponde `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`. NON DEVE tacere e NON
   DEVE chiudere**: un silenzio lascia il banco ad aspettare per sempre, ed è lo stesso difetto che
   §7.1 vieta per `ADATTA_TELA`. Un client che chiede una funzione spenta non ha violato niente;
3. ⛔ **il server DEVE dichiararla**: la capacità `banco.marca` di §4.3. Un client che la chiede
   senza che sia stata dichiarata riceve comunque `FUNZIONE_SPENTA`, non un errore di protocollo;
4. `ritardo_ms` **DEVE** stare fra **0 e 10 000**; fuori è `BANCO_ESITO(RIFIUTATA,
   RITARDO_FUORI_LIMITI)` — ⚠ **non** `ERRORE_PROTOCOLLO`: è un parametro di banco sbagliato, e far
   cadere la sessione al banco che si sta tarando è la stessa cattiva idea di §7.1 per le misure
   fuori limite;
5. ⛔ **ogni accensione e ogni `BANCO_MARCA` servito si scrivono nel registro del server.** Una
   sessione che dipinge quadratini colorati sul desktop di una persona **deve poterlo dimostrare
   dal registro**, o il giorno in cui qualcuno se ne lamenterà non ci sarà modo di sapere se è
   stata accesa.

⚠ **E `istante` non serve a misurare il ritardo**: serve al banco per **distinguere il ritardo che
ha chiesto lui da quello che ha trovato**. Il ritardo lo misura il client, dal lato che riceve, come
dice `DECISIONI.md` §2.6 — questo campo dice soltanto quando il server ha obbedito.

---

### 7.6 ⭐ `TERMINA_SESSIONE` — l'unico messaggio con cui il client chiude la SESSIONE

*Nato il 15 agosto 2026 con la decisione dell'utente `DECISIONI.md` §4.1-ter.*

```
TERMINA_SESSIONE
 └── (corpo vuoto)
```

⛔ **Non è «chiudi la connessione»**: quello si fa col `CONGEDO`, e lascia la sessione viva
(invariante I4). Questo dice *«ho finito»*: la sessione grafica finisce e **i programmi dell'utente
si chiudono**. Sono le due uscite di `DECISIONI.md` §4.1-ter, e il protocollo deve poterle
distinguere — un client con un modo solo costringerebbe l'utente a scegliere fra non uscire mai e
perdere il lavoro.

| | |
|---|---|
| **chi lo manda** | il client, e **solo** dopo un gesto esplicito dell'utente: la scorciatoia `Ctrl+Alt+Fine` con la sua conferma. ⚠ La voce «Esci…» del menu del desktop **non passa di qui** — quella la esegue il desktop, e il server se ne accorge da sé |
| **quando è valido** | ⛔ solo a sessione **attaccata**. Prima dell'`ATTACCA` non c'è nessuna sessione da terminare, e §3 non fa sconti: chi lo manda fuori posto riceve `ERRORE_PROTOCOLLO` |
| **la risposta** | ⛔ un `CONGEDO` con motivo **`0x10 SESSIONE_TERMINATA`**, e **DEVE partire prima** che la sessione grafica finisca di morire: quando il compositore cade, il palco cade con lui e il canale non serve più. Un `0x10` spedito tardi è il rilievo **B-7** con un nome nuovo |
| **e agli altri** | ⛔ il congedo va a **tutte** le sessioni di quell'utente, non solo a chi ha chiesto: la sessione grafica è una sola (I2), e chi la guardasse da un secondo dispositivo resterebbe con uno schermo fermo per sempre |

⚠ **E non esiste una risposta «sto terminando»**: l'esito è il congedo. Un messaggio intermedio
sarebbe una deduzione al posto di un fatto (`LEZIONI.md` §7.5), e l'unico fatto che conta è che la
sessione sia finita.

---

## 8. Il congedo

### 8.1 Si dice, e si verifica dal lato che riceve

⛔ Chi chiude **DEVE** mandare `CONGEDO` con un motivo **prima** di chiudere la **sessione
WebTransport** — ⛔ **se il canale di controllo è ancora utilizzabile** (§3.1 punto 2) — e **DEVE**
ripetere il motivo nel codice d'errore applicativo della chiusura (§3.1 punto 3). ⭐ **Il punto 3
non ha condizioni e non ne ha bisogno**: viaggia nella chiusura stessa, e parte anche quando il
canale è morto.

> ⛔ *Corretto il 10 agosto 2026, rilievo **R11.8**: qui c'era «prima di chiudere la **connessione
> QUIC**», e in §4.4 «con lo stesso motivo nel **`CONNECTION_CLOSE`**». Sono i due resti che la
> correzione R1.4 di §3.1 non aveva raggiunto, e §8.1 è il paragrafo che detta l'obbligo a **chi
> chiude** — che è spesso la pagina, cioè il lato che R1.4 dichiara **incapace** di chiudere la
> connessione HTTP/3 sotto.*
>
> ⛔ **È lo stesso ingresso con due byte diversi** — un `CONNECTION_CLOSE` di trasporto contro una
> `CLOSE_WEBTRANSPORT_SESSION` — cioè la forma esatta che R1.4 dichiarava di aver chiuso: *«un
> programmatore chiudeva la sessione e dichiarava assolta la regola; l'altro cercava l'API della
> connessione, non la trovava, e lasciava il punto 3 non implementato — ed era conforme al testo
> quanto il primo»*. ⚠ E §4.4 lo imponeva proprio sul percorso `RESPINTO`, quello che B11 ha
> riaperto il 10 agosto.

⚠ **E questa riga ha un prezzo già pagato.** In v1, per **tre fasi**, il server scriveva compìto
«congedo il client» mentre il client, alla stessa ora, scriveva «errore di rete»: mancava una
seconda chiamata di libreria che nessuno sospettava (`LEZIONI.md` §1.7). Da cui l'obbligo di
collaudo: **il congedo si verifica dal lato che lo riceve**, mai dal registro di chi lo manda.

⚠ **L'unica eccezione è `RESPINTO`** (§4.4), che *è* il congedo dell'autenticazione.

> ### ⛔ E «chi chiude» non è chi ha ricevuto un `FIN` — ✅ 11 agosto 2026
>
> *L'eccezione che la decisione di `DECISIONI.md` §7.14 pretende, scritta qui perché è qui che
> l'obbligo è dettato. Senza questa frase §4.2 vieta di spedire sul canale di controllo dopo un
> `FIN` e §8.1 continua a **imporre** proprio quel byte: la decisione avrebbe spostato la
> contraddizione invece di chiuderla.*
>
> ⛔ **Chi riceve un `FIN` sul canale di controllo non è «chi chiude», e non manda nessun
> `CONGEDO`.** A chiudere è stata l'altra parte; il motivo di quella chiusura arriva da lei, e la
> sola cosa dovuta a chi riceve è **considerare la sessione finita** (§4.2).
>
> ⭐ **Restano dovuti i byte del punto 3 di §3.1** — il codice d'errore applicativo — quando è
> **questo** lato a chiudere la sessione WebTransport per primo. L'eccezione riguarda il `CONGEDO`
> sul canale, non il motivo nella chiusura.

> ### ✅ La condizione, decisa dall'utente l'11 agosto 2026 — `DECISIONI.md` §7.15
>
> *Fino a oggi questa riga non poneva condizioni, mentre §3.1 punto 2 dice «**se il canale di
> controllo è ancora utilizzabile**»: ⛔ **un'implementazione conforme a §3.1 era in violazione di
> §8.1**, e due sezioni normative dello stesso documento davano due verdetti sullo stesso ingresso
> — la violazione che arriva su uno stream unidirezionale col controllo già finito (rilievo
> **R11.23**).*
>
> ⛔ **Vince la condizione.** L'obbligo del `CONGEDO` sul canale **cade quando il canale non è
> utilizzabile**; quel che non cade mai è il motivo dentro il codice di chiusura (§3.1 punto 3).
>
> ⭐ **La ragione, con le parole dell'utente**: *«se una connessione cade nessuno può dire al server
> "chiudo perché ho finito"»*. Un `DEVE` che non si può rispettare non è una regola: è un difetto
> di questo file, e §0 dice che i difetti di questo file sono di questo file.
>
> ⚠ **E non indebolisce `DECISIONI.md` §4.1-bis**, decisa lo stesso giorno — *ogni chiusura del
> server ha un motivo che sa spiegare*: il motivo arriva comunque, per la seconda strada. ⛔ Quel
> che si perde è **solo il byte sul canale morto**, cioè un byte che non partiva.
>
> ⭐ **E chiude un rosso su codice giusto**: **B5 e B11 applicavano già il condizionale di §3.1**
> (`FASI.md` §01-filo-nudo, rilievo R3.3), e un banco scritto sulla forma assoluta **avrebbe bocciato
> un server corretto** ogni volta che la violazione arriva su uno stream unidirezionale.
>
> ⛔ **E le due decisioni dell'11 agosto non si sostituiscono.** §7.15 dice *quando* l'obbligo cade;
> §7.14 dice *chi* non è tenuto affatto. Dopo un `FIN` ricevuto il canale, nel verso di chi lo ha
> ricevuto, **è ancora utilizzabile**: senza §7.14 la condizione di §7.15 non lo salverebbe.

### 8.2 I motivi

| Codice | Nome | Quando |
|---|---|---|
| `0x01` | `CHIUSO_DALL_UTENTE` | l'utente ha chiuso il client |
| `0x02` | `INATTIVITA` | 30 minuti senza input (`SPECIFICHE.md` §5.3) |
| `0x03` | `SESSIONE_ABBANDONATA` | ⭐ **60 minuti senza input** (`SPECIFICHE.md` §5.3, `DECISIONI.md` §4.8). ⚠ *Diceva «6 ore senza attacchi»: cambiato il 16 agosto 2026 — cambia il tetto **e** il criterio, perché chi guarda senza toccare non rinnova niente. Il codice e il nome restano* |
| `0x04` | `SESSIONE_LOCALE_PREVALSA` | l'utente ha aperto una sessione grafica locale |
| `0x05` | `GIA_ATTIVA_LOCALE` | c'è già una sessione grafica locale |
| `0x06` | `BUDGET_PIENO` | ⭐ **la macchina non ha più capacità di COMPOSIZIONE** — ⚠ *diceva «di codifica»: corretto il 24 agosto 2026, `DECISIONI.md` §4.6-nonies, perché `[M]` il collo è `rcs0` a **0,97 Gpixel/s**, la **metà** del codificatore. ⛔ E fino alla fase 10 questo codice **non è mai stato mandato da nessuna riga del server**: dalla fase 10 parte davvero* |
| `0x07` | `CREDENZIALI_ERRATE` | |
| `0x08` | `TROPPI_TENTATIVI` | ⭐ **l'indirizzo è bannato**: tre autenticazioni fallite, dodici ore (§4.4-bis). ⚠ *Diceva «limitazione della frequenza», ed era la forma precedente: dal 10 agosto 2026 non è più una frequenza, è un ban* |
| `0x09` | `NIENTE_IN_COMUNE` | nessun codec condiviso |
| `0x0A` | `VERSIONE_INCOMPATIBILE` | |
| `0x0B` | `ERRORE_PROTOCOLLO` | §3 |
| `0x0C` | `SERVER_IN_CHIUSURA` | |
| `0x0D` | `TEMPO_SCADUTO` | ⭐ *nuovo, 9 ago*: un tetto di §4.6 è scaduto |
| `0x0E` | `SESSIONE_NON_SERVIBILE` | ⭐ *nuovo, 9 ago*: l'attacco è ben formato ma non si può servire — un compositore che non parte, una disposizione che il sistema non conosce. **DEVE** portare il dettaglio nel corpo |
| `0x0F` | `GIA_ATTIVA_REMOTA` | ⭐ *nuovo, 9 ago sera*: **c'è già un client attaccato a questa sessione**, e questa connessione viene **rifiutata** |
| `0x10` | `SESSIONE_TERMINATA` | ⭐ *nuovo, 15 ago*: **l'utente è uscito dal desktop** («Esci/logout» dal menu di sistema). La sessione grafica è finita e i suoi programmi sono chiusi ⇒ ⛔ **non c'è niente a cui riattaccarsi**, e la pagina torna al **modulo di accesso** (`DECISIONI.md` §4.1-quater) |

> ### ⛔ Perché `0x10` non è un doppione di `0x01` — 15 agosto 2026
>
> I due codici descrivono **due gesti dell'utente con esiti opposti**, e `DECISIONI.md` §4.1-ter li
> separa: `0x01 CHIUSO_DALL_UTENTE` è il **filo che cade** — scheda chiusa, browser chiuso, il PC
> dell'utente spento o riavviato — e porta la promessa *«riattacca e ritrovi tutto»*. `0x10` è il
> **logout**, e quella promessa lì è **falsa**.
>
> ⛔ **Il vincolo che questo codice porta è sull'ordine, non sul contenuto**: quando il compositore
> cade il palco cade con lui, e il canale non serve più. `0x10` **DEVE** partire **prima** che la
> sessione grafica sia finita di morire. Un `0x10` definito e spedito troppo tardi è il rilievo
> **B-7** con un nome nuovo.
>
> ⚠ **E chi riceve un `0x10` non deve riattaccare**: un client che ritentasse aprirebbe una sessione
> **nuova**, non ritroverebbe la vecchia — che è esattamente ciò che l'utente ha chiesto di chiudere.

> ### ⛔ Perché `0x0F` è stato aggiunto, e perché adesso — rilievo **R1.3**
>
> I quattordici motivi precedenti coprivano **locale contro remoto** (`SPECIFICHE.md` §5.1) e non
> **remoto contro remoto**: sei attaccato dal portatile e apri la stessa sessione dal telefono.
>
> **La scelta, dell'utente, il 9 agosto 2026**: *«se un utente ha già una sessione grafica remota
> attiva, e ne vuole attivare una seconda da un secondo device, la seconda connessione viene
> rifiutata»*. ⭐ È l'invariante **I2** applicata alla lettera — *«la seconda connessione è rifiutata
> con messaggio esplicito»* — e `0x0F` è il gemello remoto di `0x05 GIA_ATTIVA_LOCALE`.
>
> ⛔ **Chi viene rifiutato è chi arriva, non chi c'era.** Nessun client attaccato e vivo viene mai
> spodestato da un altro.
>
> ⚠ **E il confine con `DECISIONI.md` §4.4 va letto bene**, perché le due regole sembrano cozzare e
> non cozzano: *«chi tace è staccato, chi arriva entra»* parla del client **fantasma** — il telefono
> morto in galleria. Un client **silenzioso da 30 secondi** (`SPECIFICHE.md` §5.3) non è più
> attaccato, quindi non occupa niente e il nuovo entra. Un client **vivo** occupa, e il nuovo è
> rifiutato. ⛔ Il discrimine è **l'orologio del silenzio**, non l'intenzione di chi arriva.
>
> ⚠ **Il prezzo, dichiarato**: se il portatile si spegne di colpo senza congedarsi, dal telefono si
> entra **dopo trenta secondi**, non subito.
>
> ⚠ E la finestra per aggiungere un motivo si è chiusa subito dopo: §9 lo vieta dentro una versione
> maggiore, e la clausola che lo permetteva era che allora non esistesse nessuna implementazione.
> ⛔ **Dal 10 agosto 2026 esistono** (§0-bis), e questa strada non c'è più. ⚠ *Diceva «la clausola
> che lo permette è che **oggi** non esiste nessuna implementazione», al presente: corretta l'11
> agosto 2026, rilievo **R12C.2**.*

⛔ Ogni motivo **DEVE** essere mostrabile all'utente in una frase comprensibile. `BUDGET_PIENO`
non è «errore 6».

> ⭐ **E la frase che il client mostra davvero, dal 25 agosto 2026** (`src/pagina.html`):
>
> > *«questo server non ha più capacità per un altro desktop: le sessioni già aperte continuano,
> > e un posto si libera appena qualcuno esce — riprova fra un momento, e se si ripete chiedi a
> > chi amministra il server»*
>
> ⛔⛔ **E quel che NON dice, per scelta: «rimpicciolisci la finestra».** Ce l'aveva, ed era
> **falsa**: al cancello la tela **non è ancora decisa**, e l'unico numero in mano al server è
> `video.misura_massima`, che è il tetto del **DECODIFICATORE** del client — non della finestra.
> ⇒ Chi rimpiccioliva e riprovava riceveva **lo stesso identico no**.
> ⭐ *Una frase che promette un gesto che il prodotto non offre è peggio del silenzio: manda
> l'utente a cercare un comando che non esiste.*

⛔ **La frase la costruisce il client**, dal codice. Il campo `dettaglio` **NON DEVE** essere
mostrato all'utente: è per il registro, e contiene quel che serve a chi diagnostica.

---

## 9. Le versioni

`CIAO` porta la versione maggiore che il client sa parlare; `ECCOMI` quella scelta dal server.
Se non c'è una versione comune, `VERSIONE_INCOMPATIBILE`.

⛔ **In concreto**: il server sceglie la versione più alta che sa parlare e che non superi quella
del `CIAO`, ⛔ **fra quelle che il percorso ammette (§2.2)**. Se non ne ha nessuna, congeda. Il
client **DEVE** verificare che la versione di `ECCOMI` sia una che sa parlare, e congedare con
`VERSIONE_INCOMPATIBILE` se non lo è — un server che risponde con una versione più alta di quella
chiesta sta sbagliando, e accettarla in silenzio è l'indulgenza che §3 vieta.

> ### ⛔⭐ Le sette parole di §2.2 sono del 10 agosto 2026, e le ha trovate **B5**
>
> ⚠ *Il numero di sezione è stato corretto lo stesso giorno, rilievo **R11.18-bis** (R11.2): queste
> tre righe mandavano a **§2.4**, che è «La porta» — 7447, TCP e UDP — e non nomina né i percorsi
> né le versioni. La regola vive in **§2.2**, righe «l'indirizzo della sessione … il numero dopo la
> barra è la versione maggiore» e «le due DEVONO coincidere», ed è lì che R1.24 l'ha scritta.*
> ⛔ **Chi leggeva §9 e andava a §2.4 come gli si diceva trovava la porta, nessun vincolo, e
> tornava a §9** — cioè ricostruiva esattamente la lettura che aveva prodotto la prima stesura di
> `banchi/rcp/rcp.c`. La cura di una contraddizione fra due sezioni mandava a una terza.
>
> Questo paragrafo diceva soltanto *«la più alta che non superi quella del `CIAO`»*. §2.2 dice che
> un `CIAO(versione=2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`. ⛔ **Le due regole danno byte
> diversi sul filo per lo stesso ingresso** — `ECCOMI(1)` contro `CONGEDO(0x0A)` — e **nessuna
> delle due citava l'altra**.
>
> ⚠ Non è un caso di scuola: chi scrive il server legge §9, che è il paragrafo intitolato *«Le
> versioni»*, e scrive `if (versione < LA_MIA) congeda;`. È esattamente quel che è successo — la
> prima stesura di `banchi/rcp/rcp.c` **accettava un `CIAO(2)`** e rispondeva `ECCOMI(1)`, ed era
> conforme a §9 alla lettera.
>
> ⭐ **Vince §2.2**, perché è la più specifica e perché è stata scritta per risolvere proprio questo
> caso (rilievo R1.24). Questa riga adesso la nomina, così chi legge solo una delle due trova
> l'altra.
>
> ⚠ È la **seconda** contraddizione interna trovata da un banco in due giorni: la prima fu il
> trattino basso di §4.3, trovato dal validatore di B4. ⭐ Tutt'e due sono state trovate da
> programmi che leggevano **solo questo documento**, e nessuna delle due da chi lo rileggeva.

**Dentro una versione maggiore si cresce solo per capacità** (§4.3), mai aggiungendo campi a
messaggi esistenti né tipi nuovi che il vecchio dovrebbe ignorare — perché ignorare è vietato
(§3). Un tipo nuovo obbligatorio è una versione maggiore nuova.

⚠ **In pratica, finché client e server si aggiornano insieme, la versione serve a poco.** Serve il
giorno in cui un telefono resta indietro — e quel giorno o si è scritta bene, o si scopre che il
campo in più lo si era aggiunto «tanto è compatibile».

⛔ **E la finestra in cui questo documento si poteva ancora completare È CHIUSA**: il divieto qui
sopra protegge le implementazioni esistenti, e **adesso esistono** — l'elenco, contato, sta in
§0-bis. **Dal 10 agosto 2026, primo byte di codice, vale la regola senza sconti.**

⛔ **Quanto è stata usata la finestra, prima di chiudersi: QUATTRO tipi, non due.**
`RICHIEDI_CHIAVE` (`0x000D`) e `TELA` (`0x000E`) il 9 agosto; ⭐ **`BANCO_MARCA` (`0x000F`) e
`BANCO_ESITO` (`0x0010`) la notte del 9** (§7.5). Più **tre** motivi di congedo (`TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`). Il conto sta in `DECISIONI.md` §1.5, e §12 dichiara
che quella dei due della funzione di banco è stata *«l'ultima occasione»*.

> ⚠ *Questa riga diceva* «I **due** tipi aggiunti il 9 agosto (`0x000D`, `0x000E`) sono entrati sotto
> questa clausola», *e la finestra la dichiarava aperta. I due della funzione di banco erano stati
> aggiunti nella stessa notte e non erano mai stati portati qui: la cura del rilievo **R11.13** era
> arrivata a `DECISIONI.md` e non alla riga che tiene il conto della clausola — cioè chi verificava
> quanto era stata usata una finestra irripetibile, contando da qui, ne trovava la metà. Corretta
> l'11 agosto 2026, rilievo **R12C.3**.*

---

## 10. Che cosa RCP non fa

| | Dove sta scritto |
|---|---|
| non trasporta file, dischi, stampanti, porte | `SPECIFICHE.md` §12 |
| non trasporta immagini negli appunti | §7.4 |
| non ha un canale per il puntatore **relativo** | riservato, non definito in RCP/1 |
| non ha un canale per lo stilo né per il tocco multi-dito | `input.tocco` esiste come capacità e vale sempre `no` |
| non porta l'**audio del microfono** | il verso è previsto in §5, il formato non è definito: `SPECIFICHE.md` §10 lo dà per non urgente |
| non ha compressione propria | la fa il codec, e QUIC cifra |
| non ha un battito applicativo | §2.2 |
| non ha modalità in chiaro | §2 |
| non trasporta il volume | è della sessione, invariante I5 |
| non descrive più di **uno schermo** | il multi-monitor è fuori scope come funzione (`SPECIFICHE.md` §6.5); la tela è una sola, e più grande della vista |

---

## 11. Come si collauda contro questa specifica

Il punto che rende utile tutto il resto. **Client e server NON si collaudano l'uno contro
l'altro**: si collaudano contro questo documento.

| Banco | Che cosa prova |
|---|---|
| **il validatore del filo** | un terzo programma che legge una registrazione della connessione e dice quale byte non è conforme. È l'unico arbitro esterno che avremo |
| **la stretta di mano su due connessioni** | ⛔ **due, mai una**: in v1 un certificato condiviso uccideva il server **alla seconda** connessione, e una prova a connessione singola resta verde per sempre (`LEZIONI.md` §2.1) |
| **il congedo** | verificato **dal lato che riceve**, per ciascuno dei motivi **che viaggiano in un `CONGEDO`** — e per ciascuno si verifica **anche il codice nella chiusura della sessione** (§3.1). ⚠ *Diceva «per ciascuno dei quattordici»: ma `CREDENZIALI_ERRATE` e `TROPPI_TENTATIVI` viaggiano in `RESPINTO`, che §4.4 vieta di far seguire da un congedo — il banco sarebbe fallito su due motivi per costruzione, e chi lo scriveva avrebbe pensato di aver sbagliato lui (rilievo **R1.18**)* |
| ⭐ **il rilascio dei tasti al distacco** | si stacca una connessione **con un tasto premuto** e si riattacca a verificare che non sia rimasto giù (§7.3). ⛔ **È la regola con il rapporto danno/costo più alto del documento**: un Ctrl rimasto premuto rende inservibile una sessione che sopravvive al client, e nessuno collega le due cose |
| ⭐ **l'audio, ascoltato** | si apre un datagram e si guardano i byte: frequenza, canali, ordine dei byte del PCM. ⛔ Un server che spedisse 44 100 Hz, o PCM big-endian, resterebbe **verde su tutti gli altri banchi** — e il sintomo, come in v1, «sembra un difetto di rete» (`LEZIONI.md` §2.2) |
| ⭐ **gli appunti** | i tre messaggi, l'identificatore di trasferimento, e **due trasferimenti aperti insieme nei due versi**: è il caso in cui senza identificatore i testi si scambiavano |
| ⭐ **il secondo fisso** | si cronometra la risposta a `CREDENZIALI` — **anche quella riuscita** (§4.4-bis). È una proprietà di sicurezza che nessun altro banco vede, e una regressione che la togliesse non farebbe fallire niente |
| ⭐ **il ban dell'indirizzo** | tre autenticazioni fallite, e ⛔ **il quarto tentativo è rifiutato anche con la parola d'ordine GIUSTA** (§4.4-bis) — che è la prova che distingue un ban da un contatore. ⛔ E con **tre nomi utente diversi**, o non si sta provando la regola decisa ma quella vecchia. ⚠ Poi tre controlli che dicono *no*: un **altro** indirizzo entra lo stesso · un accesso **riuscito** azzera il conto (due falliti, uno riuscito, due falliti: il terzo **non** banna) · e il ban **sopravvive al riavvio** del server |
| **l'anello del ritardo** | il client manda un input che cambia colore allo schermo e guarda i fotogrammi decodificati finché non lo vede (`DECISIONI.md` §2.6) |
| ⭐ **il ritardo noto** | si chiede `BANCO_MARCA` con `ritardo_ms = N` e **la mediana DEVE salire di esattamente N** (§7.5). ⛔ *È il controllo che rende credibile ogni numero di ritardo di questo progetto: un banco che non lo fa non sa di misurare* |
| ⭐ **la funzione di banco spenta** | ⛔ con `banco.marca = no`, un `BANCO_MARCA` **DEVE** ricevere `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — **non un silenzio e non una chiusura**. ⚠ E si verifica **dal lato che riceve**: un server che tace lascia il banco ad aspettare per sempre, e il sintomo è «il banco si è piantato» |
| **il rigore** | si manda di proposito un tipo sconosciuto, una lunghezza sbagliata, un messaggio nello stato sbagliato: ⛔ **la connessione deve cadere ogni volta**. Un banco che non prova a violare il protocollo non prova il protocollo |
| ⭐ **il fotogramma abbandonato** | si abbandona un delta di proposito e si verifica che **arrivi una chiave** e che il client non mostri niente di rotto nel frattempo (§5.2). ⚠ Senza questo banco l'abbandono si prova solo su una rete cattiva, cioè quando non lo si sta guardando |
| ⭐ **il credito degli stream** | si tiene una sessione viva **oltre i primi 256 fotogrammi** — cioè oltre i primi quattro secondi — e si verifica che il video non si fermi (§2.3) |
| ⭐ **i tempi della stretta di mano** | si apre una connessione e si tace, per ciascuno dei tre tetti di §4.6 |

⚠ **E il controllo positivo, che qui è facile da dimenticare**: prima di concludere che il
validatore non trova errori, gli si dà una registrazione **con un errore dentro** e si verifica che
lo veda. Uno strumento che non ha mai trovato niente non è uno strumento pulito: è uno strumento
non certificato (`LEZIONI.md` §1.9).

### 11.1 ⛔ Il formato della registrazione

*Scritto il 10 agosto 2026, **prima** del registratore — rilievo R3.6. Il formato è **uno solo**:
due registratori, uno nel C e uno nella pagina, che scrivessero lo stesso fatto in due modi
sarebbero il difetto muto contro cui §0 è stato scritto.*

⛔ **Il problema che questo formato risolve.** Registrare i byte com'erano metterebbe la parola
d'ordine in chiaro in un file, che §4.4 vieta *«a nessun livello»*. Sostituirla lasciando la
`lunghezza` darebbe un corpo che non combacia più, cioè **un falso rosso perpetuo** su ogni traccia
con una stretta di mano riuscita. Sostituirla **e** riscrivere la lunghezza farebbe convalidare al
validatore un documento riscritto dal banco — e allora non è più un arbitro.

⭐ **La quarta strada**: si registra **la lunghezza vera**, si sostituiscono i soli byte segreti con
altrettanti byte di riempimento, e il formato **dichiara quali intervalli sono oscurati**, con
l'impronta di quel che c'era. La lunghezza torna, il validatore sa dove non deve guardare, la
parola non c'è.

```
intestazione (16 byte)
 ├── 8 byte   magia          "RCPREG" 0x00 0x03
 ├── u32      quanti_blocchi
 ├── u8       orologio       1 = i tempi sono del CLIENT, 2 = del SERVER
 └── u8[3]    riservato      DEVE essere 0

poi `quanti_blocchi` blocchi, ciascuno:
 ├── u8       verso          1 = client → server, 2 = server → client
 ├── u8       canale         il byte alto di `tipo` (§2.5)
 ├── u8       fine           ⛔ come si è chiuso lo stream DOPO questo blocco:
 │                             0 = continua · 1 = FIN · 2 = RESET_STREAM
 ├── u32      istante_ms     ⛔ millisecondi dal PRIMO blocco, dall'orologio
 │                             MONOTONO di chi registra. Il primo blocco vale 0.
 │                             ⛔ Mai un'ora del mondo: §4.4 vieta i segreti nel
 │                             file, e una data assoluta dice QUANDO e DA DOVE
 │                             un utente si è collegato
 ├── u64      stream         l'identificatore dello stream QUIC
 ├── u32      lunghezza      quanti byte di carico seguono — ⛔ la lunghezza VERA
 ├── u16      quanti_oscurati
 │     per ciascuno:
 │       ├── u32   inizio        scostamento dentro il carico di questo blocco
 │       ├── u32   quanti        ⛔ la lunghezza VERA dei byte sostituiti
 │       └── 32 B  impronta      SHA-256 dei byte veri
 └── `lunghezza` byte di carico
```

### ⛔ Il tempo registrato è di CHI REGISTRA, e la regola del secondo è del SERVER

*Il campo `istante_ms` è entrato il 21 agosto 2026 con la magia `0x03`, e senza questo capoverso
farebbe più danno del buco che chiude.*

Una registrazione presa **al client** vede *«quando è arrivato il `TELA`»* e *«quando è partito il
`PUNTATORE`»*: un intervallo **più corto** di quello che il server ha misurato, di mezzo giro di rete
per lato. ⇒ Il validatore può concludere **in un verso solo**:

- se `istante_ms(PUNTATORE) − istante_ms(TELA) > 1000` con `orologio = 1`, l'intervallo del server
  era **anche più lungo** ⇒ il server **DEVE** aver rifiutato, e se non l'ha fatto è `NON CONFORME`;
- se è `≤ 1000`, **non si conclude niente**, e il validatore lo **DICE**: *«non giudicabile da questa
  registrazione»*.

⭐ Il verso che si guadagna è quello che conta: **un server indulgente**, che accetta per sempre le
coordinate vecchie. ⚠ E un arbitro che tace su quel che non sa è un arbitro che **assolve**: la
frase «non giudicabile» è obbligatoria, non gentile.

⛔ **E la magia cambia perché il blocco cresce**: un validatore vecchio davanti a un file nuovo
**DEVE rifiutare**, non leggere di traverso. `[M]` 21 agosto, nei due sensi: l'arbitro di oggi
davanti al file del 12 agosto esce **2**; l'arbitro di ieri — fabbricato apposta rimettendo una copia
a `0x02` — davanti al file di oggi esce **2**. ⚠ È il difetto `0x01`/`0x02` del 12 agosto, che
**nessuno dei due file mostrava da solo**: qui il cambio si è fatto in **un commit solo**, con tutti
e quattro i lettori e scrittori insieme.

⚠ **Tre banchi sono in ritardo dichiarato** su questo formato — `banchi/02-filo-cliente.py`,
`banchi/02-filo-validatore.py`, `banchi/04-b20-desktop-vero.py`. Oggi sono un'**isola coerente**
(scrivono e leggono fra loro), ⛔ ma finché restano a `0x02` l'albero porta **due formati vivi sotto
una specifica sola**, che è la condizione del difetto del 12 agosto in grande.

### T4 — un `TELA(ADATTATA)` a cui nessun fotogramma obbedisce

*È la presa dell'arbitro su «conforme non è funziona», e senza `istante_ms` non esisteva.*

Dopo un `TELA(ADATTATA, LxA)`, §5.2 vuole che il primo fotogramma alla misura nuova sia una
**chiave**, e §6.2 lega i 28 byte alla tela in vigore. ⇒ Se passano fotogrammi per più di un tetto in
**tempo** e **nessuno** porta la misura concessa, il server ha risposto **senza toccare il palco**.

⛔ **Non «il primo»**: §6.2 ammette il fotogramma già in volo alla misura vecchia. ⇒ Serve un tetto in
tempo, non un conteggio — ⭐ e la differenza è **provata, non affermata**: la mutazione
*«conta invece di cronometrare»* sopravviveva finché il caso che doveva ucciderla aveva la finestra
troppo corta.

⭐ `[M]` 21 agosto, sul **prodotto vero** (porta 7721, cinque giri su cinque): dopo
`TELA(ADATTATA, 1264x800)` il fotogramma **dichiara 1264x800**. Il palco è stato toccato, e adesso lo
dice un arbitro invece di un ragionamento.

> ### ⛔ Il campo `fine` non è un lusso — aggiunto il **12 agosto 2026**, proposta **P7** di F2.4
>
> *E non l'ha trovato una rilettura: l'ha trovato `banchi/02-filo-validatore.py` **provando a
> giudicare una registrazione conforme**, e non riuscendo a dire se il fotogramma fosse completo.*
>
> Senza `fine`, un fotogramma **abbandonato** (§5.1, legale — il client butta e chiede una chiave) e
> uno **troncato per errore** (§3 — la connessione cade) hanno lo **stesso aspetto** nella
> registrazione: il validatore non può applicare la riga che §6.2 ha aggiunto apposta il 9 agosto
> 2026 — *«ma solo se lo stream è finito con un FIN»*, rilievo **R1.7** — ed è la forma **E8**
> rientrata dalla finestra. `[M]` sulla registrazione di prova conforme l'arbitro dichiarava *«di 1
> su 1 NON si è potuta giudicare la completezza»*.
>
> ⚠ **La magia passa a `0x00 0x02`** perché il blocco cambia misura: un validatore vecchio deve
> **rifiutare** il formato nuovo, non leggerlo di traverso.
>
> ⭐ **E non tocca §9**: un blocco di registrazione **non è un messaggio**, e il formato porta già la
> propria versione nella magia.

⛔ **Gli intervalli oscurati contengono `0x2A` ripetuto**, non zeri: uno zero è un valore che i
campi possono avere davvero, e un intervallo di zeri che «per caso» combacia con un corpo legittimo
è un modo di non accorgersi che l'oscuramento c'è.

⛔ **Il validatore NON DEVE leggere dentro un intervallo oscurato**, e **DEVE** rifiutare una
registrazione in cui un intervallo oscurato cade fuori dal carico o si sovrappone a un altro: una
registrazione malformata e un filo non conforme sono due cose diverse, e vanno dette con due frasi
diverse.

⛔ **E il validatore riferisce lo scostamento del byte offensivo in due modi**: assoluto nel file, e
relativo al carico del blocco. Il primo serve a chi guarda il file con un editor, il secondo a chi
legge questa specifica.

---

## 12. ⏳ Quel che RCP/1 lascia aperto, dichiarato

*Non sono buchi: sono cose che non si chiudono adesso, e il motivo per cui non si chiudono.*

⛔ **E una riga di stato, perché cambia che cosa si può ancora fare qui dentro**: dal **10 agosto
2026** — primo byte di codice — la clausola di §9 è **consumata**. Quel che non è chiuso in RCP/1
resta aperto **fino a RCP/2**, o si chiude senza aggiungere tipi di messaggio (§0-bis, §9).

| | Perché non ora | Quando |
|---|---|---|
| ⭐ ~~**il tetto della sessione senza canale di controllo**~~ — ✅ **CHIUSA** | **cinque secondi**, decisi dall'utente l'**11 agosto 2026**: `DECISIONI.md` §7.17, e la riga normativa sta in **§4.6**. ⚠ *Questa casella diceva ancora* «❓ aperta … quando l'utente avrà risposto» *mentre §4.6 dello stesso file porta la riga con il ✅ e la data: **due sezioni dell'arbitro davano due stati diversi alla stessa domanda**, e chi si fosse fidato di §12 avrebbe scritto un server senza quel tetto restando convinto di essere conforme. Corretta la sera dell'11 agosto 2026, alla rilettura d'apertura* | ⛔ **resta da MISURARE**: `B6` vuole un quarto caso — apri la sessione, non aprire il canale, e verifica che a 5 s arrivi `0x0D` **nel codice di chiusura**, non sul canale. *Decisa ≠ misurata.* ⭐ Nessun tipo nuovo: `TEMPO_SCADUTO` c'era già |
| **il microfono** | il verso è previsto, il formato no. Chiuderlo adesso significherebbe scrivere una negoziazione che nessuno esercita | quando `SPECIFICHE.md` §10 smetterà di dirlo «non urgente» — e sarà una **versione maggiore nuova**, perché è un canale in più (§9) |
| **il puntatore relativo** | serve alle applicazioni remote che **catturano** il puntatore, e quel caso lo segnala il server. Non è il caso di `Pointer Capture` su Android, che è già coperto (`DECISIONI.md` §5-bis.8) | quando si presenta un'applicazione che lo chiede |
| **il tocco multi-dito** | `input.tocco` esiste e vale `no`. Un posto riservato costa niente; una definizione mai esercitata costa un vincolo | fase A4, se il tocco nativo servirà davvero |
| **il 4:4:4** | è una capacità in più (`video.sottocampionamento`), e la decisione di prodotto è `[?]` (`DECISIONI.md` §2.3) | quando l'utente avrà guardato le due immagini |
| **più schermi** | la tela è una sola. La forma del multi-monitor è «due viste sulla stessa tela», che il protocollo già regge per la tela; mancherebbe solo dire **dove** sta ciascuna vista | mai, finché resta fuori scope |
| `[?]` **la registrazione IANA della porta** | §2.4 | se e quando servirà un numero registrato |
| ~~la funzione di banco dell'anello del ritardo~~ | ⭐ **chiusa la notte del 9 agosto 2026, poche ore dopo essere stata aperta** dal rilievo **R3.4**: è **§7.5**, due tipi nuovi — `BANCO_MARCA` e `BANCO_ESITO` | ⭐ *È entrata sotto la clausola di §9 — «oggi non esiste nessuna implementazione» — e **quella era l'ultima occasione**: dal primo byte di codice in poi sarebbe stata una deroga, cioè il primo strappo fatto da noi a una regola nostra* |

⛔ **E una cosa che non è aperta e va detta perché non venga riaperta per distrazione**: il
**battito applicativo** non manca, è **vietato** (§2.2). Chi lo trova assente e pensa di aggiungerlo
sta per creare due verità sullo stesso fatto.
