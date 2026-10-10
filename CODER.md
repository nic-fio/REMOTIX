# CODER — The rules of whoever writes

The rules to follow while writing code, so that the product gets closer
to the declared numbers and does not drift away from what the user sees.

⛔ **Binding rule.** Not a single line of code is written without first having
read this document and the sections of **`SPECIFICHE.md`** that the area touches — and
**`RCP.md`** if the wire is touched. It is the same rule that in v1 belonged to `⟨v1⟩ REFERENCE.md`
§7.0, extended to all the work and not only to the protocol.

> ⚠ **The old names you find below.** This document came from v1 and still cites
> `⟨v1⟩ SPECIFICA.md` and `⟨v1⟩ REFERENCE.md`, which are the papers of the **superseded
> product**: they are in `fondamenta/documenti/` and here they carry the mark **⟨v1⟩**.
> ⛔ **They no longer govern anything**: what applies today is `SPECIFICHE.md` and `RCP.md`.
> They are read to understand *why* a rule exists, not to know what to do.
> The full table is in §0.

---

## 0. How to read this document

This document says **what to build and how to build it**. It does not contain the measurement
method — that is in `LEZIONI.md`, which is the shared foundation and must be read
before starting. Here are the operational rules, as short as possible, with
the reason for each beside it.

The relationship with the other document: every rule written here has a corresponding
check in `REVIEWER.md`. If a rule exists here but not there, it is an unchecked
rule. If a check exists there but not here, it is checking something that
nobody said to do. Both cases are a defect of the pair.

The shared foundation, recalled here but not rewritten:
- `LEZIONI.md` — the method: how to measure, how to test, how to learn.
- `SPECIFICHE.md` §3.1 — the two numbers every technical choice must bring closer.
- `RCP.md` — the protocol, for whoever touches the wire. *(In v1 it was `⟨v1⟩ REFERENCE.md`.)*

> ## ⛔ Where the cited documents are — read before going to look for them
>
> *Added on 9 Aug 2026: this document came from v1 **without renumbering**, like
> `LEZIONI.md`, and like that one it cites the old names. Whoever looked for `SPECIFICA.md` in the
> V2 folder would not find it, and it is precisely the first document §0 obliges them to read.*
>
> | Cited here as | Is in | How much it counts in V2 |
> |---|---|---|
> | `SPECIFICA.md` | `fondamenta/documenti/SPECIFICA.md` | ⛔ **read `SPECIFICHE.md`**, at the V2 level, which replaces it entirely. The §x.y cited below point to the old one, and the correspondence must be looked for by topic |
> | `REFERENCE.md` | `fondamenta/documenti/REFERENCE.md` | they were the compatibility rules with other people's RDP clients. **In V2 it lapses almost entirely**: the clients are ours and the arbiter is `RCP.md`. The citations remain valid as **history of the price paid**, not as rules to apply |
> | v1's `PIANO.md` | `fondamenta/documenti/PIANO.md` | closed at phase 11. The live plan is `PIANO.md` at the V2 level |
>
> ⚠ **And the three documents that did not exist at all in V2**, and that are not cited here because they were
> born afterwards: `RCP.md` (the arbiter of the wire), `DECISIONI.md` (the why of every choice, with the
> date and who made it) and `SPECIFICHE.md`. Whoever touches the wire reads `RCP.md`, not `REFERENCE.md`.

When a new measurement contradicts this document, the document is updated at the
same moment, with the date and the source. A reference that ages silently is
worse than no reference.

---

## 1. The founding principle: the numbers are set by the user

> «Technical solutions must be chosen according to these constraints,
> not the other way round.» — `⟨v1⟩ SPECIFICA.md` §3.1

|         | Value                                     |
|---------|--------------------------------------------|
| MINIMUM  | 25 fps at 480p, colour depth 24 bit    |
| DESIRED | 60 fps at 4K, 10 bit per channel          |

> ⚠ **The minimum was lowered on 8 Aug 2026, by decision of the user.** It said
> «30 fps at 1080p», and it was v1's number. The change is not only of value, it is of
> **nature**: at 1080p30 the minimum was a goal to chase — and v1 already exceeded it,
> with 37 frames delivered by Mutter's capture and 60 by KWin. At 480p25 it becomes
> a **service guarantee**: the level below which we do not go and do not disconnect, however
> bad the line is.

> ⚠ **And the colour was rewritten the same day.** The desired one said «colour depth
> 32 bit», which is not an existing quantity: 32 bpp are 24 bits of colour plus 8
> of alpha, and alpha is not transmitted. The user's intention was «massima qualità»,
> and under that word there were **two distinct levers** that the number confused:
>
> | Lever | What defect it cures | Price |
> |---|---|---|
> | **10 bit per channel** | banding on soft gradients | almost nothing, and in hardware everywhere — Android decoder included |
> | **4:4:4** (full-resolution colour) | fringed coloured text — the defect measured in v1, `⟨v1⟩ SPECIFICA.md` §5.2 | ~50 % of bandwidth, **no Android decoder in hardware**: it would put the phone back into software, that is the wall V2 was born to knock down |
>
> **10 bit chosen** — the highest quality achievable on both clients together, in
> hardware, without compromises.
>
> ⚠ **4:4:4 remains a `[?]`, not a promise.** It would be an option for the Linux client
> only on capable GPUs (NVIDIA yes, Intel sometimes, AMD no), but **nobody has measured how much
> the difference really shows** on the user's desktop. `LEZIONI.md` §2.3-quater applies —
> an unmeasured reason makes the decision half-taken — and §2.4: it sits behind a
> switch that stays off until the user has looked at it. It is decided on a bench that puts
> the two images side by side, and he is the judge (§7.3).

From this follows the working rule that governs everything else. It must be read in **two
steps**, because a bar that every choice clears no longer filters anything:

**Upwards it is the desired that filters: a technical choice is justified by showing that
it brings 60 fps at 4K closer. A choice that leaves that number where it is is not made, however
elegant the gain it brings elsewhere.**

**Downwards it is the minimum that binds: a choice is not made if it can take the user below
480p at 25 fps — nor if, to avoid going below, it takes the session away from them. A
bad session is worth more than a closed session.**

### 1-bis. The third number: the delay

*Set by the user on 9 Aug 2026, and before that day it did not exist: neither
`SPECIFICHE.md` nor v1's specification named latency.*

|         | From the input arriving to the frame leaving |
|---------|------------------------------------------------|
| CEILING   | **50 ms** — not to be exceeded                      |
| TARGET | **40 ms** — where we aim                    |

⛔ **Only the piece that is ours is measured, and it is not a trick: it is the only way to
have a defensible requirement.** The network is not ours and changes from one minute
to the next; a «100 ms end-to-end» requirement is failed while standing still, because of
a tunnel, and a requirement that can be failed without having done anything wrong **is
measured by nobody**. The total the user feels is this plus the network:
it is **declared**, not promised.

⚠ **And the delay weighs more than the frames**: 30 frames per second with 40 ms are
perfectly usable, 60 with 200 ms are unbearable. A technical choice that raises the
rate while worsening the delay **is not made**, and it is the kind of trade that comes up
all the time — every intermediate buffer you add buys smoothness and sells responsiveness.

And the declared bandwidth is a **floor, not a budget**. It is spent, not saved:
unspent bandwidth is no use to anyone, and lost quality shows.
(`LEZIONI.md` §7.2 — optimising in the wrong direction is worse than not optimising.)

⭐ **And since 23 Aug 2026 the floor has a number: 30 Mbit/s** (it was 20 in the morning, raised at night — `DECISIONI.md` §3.1-sexies)**.** *«Al di sotto di questo limite
l'utente nemmeno riesce a navigare, figuriamoci usare remotix»* — the user, `DECISIONI.md`
§3.1-bis. ⇒ Below 30 Mbit/s **nothing is promised and nothing is measured as a requirement**;
⚠ the ban on disconnecting stays whole all the same. Whoever tuned a threshold on a 2 Mbit/s line
would be tuning on a case the product **no longer serves**.

> ### ⛔⛔ WHERE THE MEASUREMENT ENDS — *13 Aug 2026, and it is worth 11 ms out of 50*
>
> **The delay measurement ends at the FINISHED DRAWING, not at the decoder callback.**
>
> ⛔ It is not a nuance of method: the first draft of the meter closed at the **callback**, and gave
> itself **~11 ms** — ours, measurable, and inside the ceiling. With the boundary moved, the number
> went up from **63.8 to 74.6 ms** and it was left to go up.
>
> ⇒ ⭐ **The rule for whoever writes a meter: the boundary moves in the UNCOMFORTABLE direction.** Every
> boundary has two defensible positions, and the one that favours whoever measures picks itself if
> nobody names it. Name it, and pick the other.
>
> ⚠ **And what stays outside is declared even when it cannot be measured**: between the finished drawing
> and the lit pixel pass `[?]` **16-40 ms** that no API exposes. They are estimated and written
> beside the number — ⛔ **but not on Xvfb, where that piece does not exist** (`STUDI.md` §web §6.2).
>
> ⛔ **The measured number, and the ceiling is exceeded**: `[M]` median **74.58 ms** capture → glass, which
> with the blind piece makes **90-115 ms** on the user's screen. ⛔⛔ **And 78 % is ours**:
> Mutter gets 22 %, the rest is almost all in the software encoder (`SPECIFICHE.md` §3.2).
>
> ### ⭐⭐ And on 15 Aug 2026 it turned out there was a SECOND ring, and nobody was measuring it
>
> The number above is **capture → glass** on a **moving** scene. ⛔ The ring the user
> feels when they **click** is another one — *input received → frame leaving* — and it is measured on a
> **still** scene, which is the condition in which one clicks. No bench was looking at it.
>
> `[M]` Measured on the user's real clicks: **median 136 ms, worst 502**. The cause was a single
> line (`MOVIMENTO_ATTESA_S 0.25`): the child's loop reads the parent's messages **before**
> the frame wait, and whatever arrives during the wait pays all of it.
> ⇒ Brought to 8 ms: **median 41 ms, worst 47** — inside the ceiling.
>
> ⚠ **The lesson is about method, not numbers**: a wait sized for one ring becomes the
> delay of every other ring passing through the same loop (`LEZIONI.md` §6.2-bis, `REVIEWER.md`
> **E13**). And the log line that explained it — *«3 attese a vuoto al secondo»* — had been printed for
> a day (§6.2-ter).

---

## 2. The invariants to protect

These are not negotiable. They are the product's properties that the code must not
break. If a change touches them, it stops and is reported — even if the code is
logically correct.

| # | Invariant | Where it is written |
|---|-----------|------------------|
| I1 | The rate never drops out of caution, to save, or because the scene is still: it drops **only** when the measurement shows that the line does not carry, and every drop is declared in the log. Below the minimum we keep dropping **frames** — never blurring the image, and **never disconnecting**. | `SPECIFICHE.md`, decided on 8 Aug 2026 |
| I2 | A single graphical session per user; the local session wins over RDP; the second connection is refused with an explicit message. | `⟨v1⟩ SPECIFICA.md` §3.4 |
| I3 | The authentication guard starts from denied. Whoever does not pass through the validator receives not a pixel and controls nothing. | `⟨v1⟩ REFERENCE.md` R14 |
| I4 | The stage (capture, control, virtual monitor) belongs to the session, not to the connection. It survives disconnection. | `⟨v1⟩ SPECIFICA.md` §3.3-ter |
| I5 | The volume belongs to the session. Whoever connects finds the level at maximum; a slider left low does not survive reconnection. | `⟨v1⟩ REFERENCE.md` §7.5 |
| I6 | Whatever changes what is SEEN sits behind a switch that stays off until the user looks at it. | `LEZIONI.md` §2.4 |
| I7 | The protection against a known defect lives in the program, not in a configuration line that can be lost. | `LEZIONI.md` §2.5, `⟨v1⟩ REFERENCE.md` R29 |
| I8 | The yardstick is what the user sees, not the number that comes out of the bench. | `LEZIONI.md` §0.5, §7.3 |

---

## 2-bis. ⭐ The cures of phase 9 are ON — *24 Aug 2026*

`DECISIONI.md` §3.1-septies. ⛔ **Whoever touches the transport or the audio must know that these
behaviours are the default**, not a bench option:

| cure | default | turned off **only** with |
|---|---|---|
| audio silence | on | `--niente-audio-silenzio` |
| threshold on the video queue | **100 ms** | `--sgombra-soglia-ms 0` |
| rate regulator | on | `--niente-ritmo-adattivo` |
| dead line | on (stall 5 s · silence 10 s) | `--niente-linea-morta` |
| eviction of the ghost | **15 000 ms** | `--sfratto-ms 0` |

⛔ **One road only for each**: no environment variables, no compile-time
switches. Two ways of turning on the same cure are **two numbers that diverge**, and this
project has already paid for that once.

⚠ **And the price must be kept in mind when measuring**: threshold + regulator add `[M]` up to
**+160 ms** of drift on a bad network (**zero** on the healthy line). ⇒ A bench that compares with the
past must **turn them off by hand** and say so.

## 3. The measurement rules

The project has never got stuck on a hard problem. It got stuck, every time,
on a measurement that did not measure what we believed. (`LEZIONI.md` §10.) These are
the rules that prevent it. They are recalled here because the coder measures while
developing; the detail and the price of each are in `LEZIONI.md` §1 and §2.

### 3.1 Before optimising a ring, measure how much enters the chain
A ring faster than what reaches it produces nothing. The 18 frames that
seemed a limit of the machine were a constant written in our code.
Measure the delivery, not only the processing.

### 3.2 The scene is declared, and always moves
A compositor sends a frame only when something changes. A measurement without a
declared and always-moving scene measures the scene, not the code.

### 3.3 The bench is certified before the measurement
Make sure the bench can produce the expected result before pointing it
at the unknown. Otherwise a negative outcome is ambiguous between «the unknown does not work»
and «the bench was not working».

### 3.3-bis ⭐⭐ A bench is not finished until it has been seen giving RED

⛔ `[M]` Phase 9, 23-24 Aug 2026: **nine bench defects, and none of them made a bench fail** —
all nine made it **stay silent or give green**. ⇒ Every predicate must have in `--certifica` the
case that makes it **fail**, and that case must be **run**, not imagined.

And three corollaries, each one paid for:
1. ⛔ **`None` is not zero.** «I could not read» and «nothing happened» must not have the
   same face: whoever did not measure returns `None`, and the bench **refuses to judge**;
2. ⛔ **The guard goes where the number IS CONSUMED**, not where it is produced — if another bench replaces
   your function with its own, the guard inside yours no longer runs;
3. ⭐ **Do not look for a word inside a text**: `"ACCESA" in dettaglio` is true even when the
   detail says *«nasce accesa, ed è spenta»*.

### 3.3-ter ⛔⛔ Count how much stress ARRIVED, before asking for a judgement

`[M]` Phase 9: three tests in a row produced a user judgement **valid as a sentence and empty
as a measurement** — one with frames of **242 bytes** (the loss had nothing to break), one with
**221 packets and 18 dropped** inside the fault. ⛔ **Eighteen packets are not a test.**

⇒ Before asking the user *«how was it?»*, measure **how much fault really went through** and **how much
the scene was asking for**. ⚠ And remember that the step is not decided by the fault: it is decided by **how much the scene
asks for** — between a bench that demands 40 frames/s of continuous change and a real desktop that
changes in jerks `[M]` there is **an order of magnitude**.

### 3.3-quater ⭐ Bring the MECHANISM beside the SYMPTOM, always

`[M]` Phase 9: the keyframe spiral starts at the **first lost packet** (0.10 % loss), the drop
in frames/s that the user **sees** comes at **0.53-0.75 %**. ⇒ A bench that looked only at
frames/s would give **green up to 0.5 %**. The symptom says when the user notices; **the
mechanism says when it started**, and between the two there can be a factor of five.

### 3.3-quinquies ⛔ An irreversible threshold goes ABOVE the centre, and the margin is written on both sides

When a threshold decides something that **cannot be remedied** — closing a session, throwing
someone out — ⛔ **the two errors do not cost the same**: erring on the cautious side costs a few seconds,
erring on the other **throws out whoever was working**. ⇒ Take the worst case that **holds**
and the best that **does not hold**, declare **both margins**, and choose **above** the
centre. ⚠ And the tight side is anchored to the **worst case observed**, not the most convenient: a margin
written on the lucky number is not a margin.

### 3.4 A bench that does NOT reproduce is not a proof of correctness
It is the reverse of 3.3, and it is more insidious because the bench is green. If the defect is
alive in real use and the bench stays green, the fix written on that bench gets
shipped to the user and makes things worse. First the bench that makes the defect appear,
then the fix.

### 3.5 A sample taken at start-up says nothing about the steady state
The first frames are the start-up, when everything is repainted. The distribution of the
damage in the steady state is different from that at start-up. Measure in the steady state.

### 3.6 Isolate ONE function only, and call it from outside
When the chain is already narrowed to two rings, do not do another bench run:
write the minimal program that calls only the suspect function on a known input.
It costs less and closes sooner.

### 3.7 The sender is not deduced: it is asked of the kernel
When a process dies, or a permission is denied, do not deduce who or what. Ask.
A signal handler that records who sent it, or the log of the component that
denies, are worth more than three diagnoses by deduction.

### 3.8 Verify from the side that must receive
The sender's log says it called a function, not that the byte arrived.
A farewell, a frame, a volume level are verified from the side that consumes them.

### 3.9 When a component can decide by itself, tell it what to do
A component that chooses autonomously produces two different measurements under the same
label, which is worse than not measuring. Ask for the component by name, and verify
that it obeyed. If it does not obey, declare the failure: do not fall back silently.

### 3.10 A denied read is not a read that says zero
«Empty» and «forbidden» look the same. A measurement that can say «zero» must
be able to tell zero from failure: look at the exit status, or print
count and error, not one of the two. And every measurement wants a positive control on the
same tool: «can this tool find something that is certainly there?»

### 3.11 When code read and measurement contradict each other, suspicion goes first to the measurement
Code has no environment: the measurement does, and the environment is where the errors are.

---

## 4. The writing rules

These govern the form of the code, regardless of what it measures.

### 4.1 Depend, do not rewrite
Every component we write is a component to maintain forever. We use the
existing system mechanisms. (`⟨v1⟩ SPECIFICA.md` §2.)

### 4.1-bis We depend on the compositor, not on its surroundings
*Set by the user on 8 Aug 2026: «voglio evitare di smettere di correre dietro ai
compositor e cominciare a dover inseguire i display manager».*

4.1 says to rely on the mechanisms that exist. This one says **which ones**, because
taken literally together they contradict each other.

**The compositor has to be chased**: only it delivers the frames and accepts
input. `mutter.c` and `kwin.c` exist for this, and will go on existing.

**The surroundings do not.** Screen lockers, idle daemons, power managers,
display managers: they do the same thing in four different ways, with four
different configurations that rewrite themselves. Chasing them is a tax paid
forever that buys nothing we cannot do ourselves once.

**The test to do, before relying on a mechanism:**

> *How many different implementations of this thing would I have to chase, and how much does it cost me
> to do it myself?*

Four divergent implementations and a small cost of our own ⇒ **we do it ourselves, once.**
A single implementation, or one standard across desktops ⇒ 4.1 applies in full.

⚠ **And this is not a permission to rewrite.** `logind`, PAM, PipeWire, `libei`,
`xkbcommon`, QUIC: only one of each, the same everywhere. There 4.1 applies without discounts, and
writing our own would be the defect 4.1 forbids.

*Applied in `DECISIONI.md` §4.3 (the lock is ours), where the count was: four different
cures — and three of the four were configuration lines, that is I7 — against a
counter and a farewell.*

### 4.2 Degrade, do not fail
Every missing dependency has a fallback. The service works anyway, with less.
But the fallback is declared: a silent fallback produces two behaviours under the
same label. (`⟨v1⟩ SPECIFICA.md` §2, rule 3.9.)

### 4.3 Talk directly to the compositor
The portal is avoided when it implies on-screen authorisation requests,
unacceptable for an unattended service. (`⟨v1⟩ SPECIFICA.md` §2.)

### 4.4 Never wait inside the asynchronous loop
Neither explicitly, nor in a destructor that waits for a thread to end. A hidden
wait stops all the connections entrusted to that thread, not only its own.
(`LEZIONI.md` §5, `⟨v1⟩ SPECIFICA.md` §5.7 rule 7.)

### 4.5 A session's environment is composed from scratch, one variable at a time
Whoever starts a session gives it their whole environment, including the variables that
have nothing to do with it. A wrong locale inherited from a script can stop all the
applications from starting. Do not pass your environment: compose it. (`LEZIONI.md` §5,
`⟨v1⟩ SPECIFICA.md` §5.9-bis.)

### 4.6 Silence is not zero, and green is not true
A green bench while the defect is alive is the worst of tests, because it gives confidence.
If a check counts something, make sure it can see the defect you are looking for —
not only its number. (`LEZIONI.md` §2.2.)

---

## 4-bis. ⭐ The two traps of SCRIPTS, and both got through `bash -n`

*Written on 25 Aug 2026, and each of them cost a run in phase 10.*

### ⛔⛔ No apostrophes inside `${…:?…}` and inside double-quoted strings

```bash
U=${1:?serve l'utente}            # ⛔ the apostrophe OPENS a quote…
PROFILO=${2:?serve il profilo}    # …and this line ends up INSIDE the string
```

`[M]` The apostrophe of *«l'utente»* ate **four lines**, up to the next `'` — which was
in a comment (`E'`). ⇒ `PROFILO=` **was never executed**, and the script died much further on
with *«PROFILO: unbound variable»*, on a line **that had nothing to do with it**.

⛔ **And `bash -n` passed**: the syntax **was** valid, it just did not mean what it seemed to.

⭐ This project already writes `e'` and `puo'` in comments; ⛔ **inside `${…}` and strings that
convention is not stylistic: it is mandatory.**

### ⛔ A syntax check is NOT a test

⭐ `bash -n` says *«it can be read»*, not *«it does what you think»*. ⇒ **A new script is run at least
once before trusting it**, and ⛔ **you look at what it PRODUCED**, not that it exited with zero.

⚠ And the worst case is the one that happened: a script that **starts, prints its
success lines, and does not do its job**. `[M]` The scene bench declared *«⭐ palco aperto»* and
*«⭐ parto»* on a **completely empty** scene — ⇒ ⭐ **only the stimulus measurement caught it**
(the compositor at **0.0 %**), which is §3 of this document applied to the bench itself.

## 5. The duty to update

When a measurement contradicts this document, or `⟨v1⟩ SPECIFICA.md`, or `⟨v1⟩ REFERENCE.md`,
the document is updated **at the same moment**, with the date and the mark of the source.

The marks:
| Mark | Meaning |
|-------|-------------|
| `[M]` | Measured by us, in the field. Date given. |
| `[R]` | Read in a reference's code. |
| `[S]` | Read in the specification. |
| `[?]` | Hypothesised, not yet measured. |

A decision that rests on a `[?]` must be written as provisional. An unmeasured
reason in a decision is a half-taken decision. (`LEZIONI.md` §2.3-quater.)

---

## 6. The relationship with the reviewer

The reviewer looks for contradictions, not truths. Their verdict is always «this
contradicts X», never «this is right». Their work does not replace the measurement:
it precedes and prepares it.

The coder must not:
- ask the reviewer to measure in their place — measuring is the coder's, on the hardware;
- treat a green review as an acquittal — it is only «I found nothing»;
- rewrite the code on a `[?]` finding without first measuring it.

The coder must:
- make the code verifiable: every invariant of §2 must have a point where
  the reviewer can read whether it is respected or violated;
- declare fallbacks and degradations in the log, so that the reviewer can
  tell an intended behaviour from an accidental one;
- hand the reviewer, together with the code, the measurement that goes with it and the scene
  that produced it.

When the reviewer reports an `[R]` contradiction — confirmed by a rule already
written — it is fixed. When they report a `[?]` suspicion, it is measured before
deciding. The measurement closes the circle, not the review.
