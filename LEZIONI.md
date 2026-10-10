# LEZIONI — what GNOME taught us, and what the next desktop needs

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without a card and colour conversion with swscale; the ones on card encoding and on audio stay, because the new stream is identical (comparison of 30 Sep 2026). The user's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

*Written on 7 Aug 2026, closing GNOME support (phases 0–10), before opening phase 11.*

> ## ⛔ Brought into REMOTIX on 8 Aug 2026 — read before everything else
>
> This is the **shared foundation** of [`CODER.md`](CODER.md) and [`REVIEWER.md`](REVIEWER.md), which
> cite it **29 times across 20 different sections**. It arrives here **without a single renumbering**: every
> `§x.y` cited elsewhere still points where it pointed.
>
> **What stays true, and it is almost everything.** V2 changes the wire — our own protocol (**RCP**) in
> place of RDP, no Windows, no FreeRDP, HEVC and AV1 in place of H.264, and the only two clients
> are ours. It changes **nothing** about how we measure. Sections 1 and 2, which are the heart, speak
> of declared scenes, certified benches, positive controls and senders asked rather than deduced:
> a bench that is green while the defect is alive lies the same way whatever protocol runs over
> it. And section 10 holds word for word — the project did not stall on the hard problems,
> it stalled on measurements that did not measure what we believed, and changing protocol
> grants no immunity.
>
> **What changes shape** is marked where it happens, with the date, and there are only three points: the
> three-client rule (§2.1), two of the dead ends (§8) and the count of the Android client (§7.4).
>
> **Where the cited documents are.** The v1 project lives under `fondamenta/`, and the references below must be
> read with this table beside them:
>
> | Cited as | Lives in | What it is worth in V2 |
> |---|---|---|
> | `REFERENCE.md` | `fondamenta/documenti/REFERENCE.md` | it was the rules of compatibility with other people's RDP clients. **In V2 it lapses almost entirely**, because the clients are ours. The citations stay valid as **the history of the price paid**, not as rules to apply |
> | `PIANO.md`, `SPECIFICA.md` | `fondamenta/documenti/` | the plan and the specification of v1, closed at phase 11 |
> | `kde.md`, `gnome.md`, `xfce.md`, `lxqt.md` — and `cinnamon.md`, `web.md`, `xpra.md`, `gnome-remote-desktop.md` | ⭐ **chapters of `STUDI.md`**, at V2 level: sewn into a single document on 16 Aug 2026, ⛔ without removing a line | intact: they speak of compositors, not of protocol. ⚠ They are cited as `STUDI.md` §kde, §gnome, §xfce, §lxqt — **the keys are the names the files had** |
> | the benches and the measuring programs | `fondamenta/banchi/` | intact, and they are the most reusable thing v1 leaves |
>
> ⚠ **And a warning about reuse**, which is §1.11 turned on ourselves: that a lesson is written here does not
> mean it has been verified on RCP. A **method** lesson is reused without rediscussing it;
> a lesson that names a number, a client or a codec is `[M]` **on v1**, and in V2 it goes back to `[?]`
> until someone measures it again.

## Why this document exists, and how it differs from the others

`REFERENCE.md` says **what to do with Mutter**: it is a list of rules, and when we change
compositor half of those rules will no longer hold. This document keeps the other half: **what
stays true when the compositor changes**, and that is not found by rereading the code because it is not in the
code — it is in how we got to writing it.

Every lesson has three parts:

| | |
|---|---|
| **the lesson** | in one line, written to be remembered |
| **what it cost** | because a lesson without its price convinces nobody, not even whoever paid it |
| **where the detail is** | the reference, so as not to repeat here what is already written elsewhere |

> ⚠ **Method lessons are worth more than technical ones**, and this is not a polite phrase: the
> first nine sections of this document produced all the others. The project never got
> stuck on a hard problem — it got stuck, every time, on a **measurement that did not measure
> what we believed**.

---

## 0. The five that are worth more than all the others

If the next desktop is opened by someone who has ten minutes, let them read only this section.

| # | The lesson | The price |
|---|---|---|
| **1** | **Before optimising what is processed, measure what is DELIVERED.** | A whole phase (the 9th) spent bringing the CPU milliseconds per frame from 41 to 6, while the frames delivered were 18 and nobody had ever counted them. The ceiling was a constant in our `main.c` |
| **2** | **The scene is declared, and it always moves.** A compositor sends a frame only when something changes: a still scene, or one moved by keystrokes, measures the scene and not the compositor | **All** the frames-per-second measurements taken between phase 3 and phase 9 were thrown away |
| **3** | **A green test on the wrong client is worth nothing**, and that holds for benches too: a test that does not reproduce the defect **is not a test of correctness** | A fix written on a green bench, shipped to the user, made worse the defect it was meant to cure |
| **4** | **Don't deduce: ask.** The sender of a signal, the path a buffer took, what the client really received | Three wrong diagnoses in a row about who was killing the server, and a phase postponed wrongly. Asking the kernel cost twenty lines and a single run |
| **5** | **The yardstick is what the user sees**, not the number that comes out of the bench | A change validated with PSNR, SSIM and the developer's eye: the user's judgement on the real desktop, *«siamo tornati indietro»*, and the phase reset to zero |

---

## 1. How to measure

### 1.1 The scene is declared, and it always moves

A Wayland compositor delivers a frame **only when something changes**. It follows that
any frames-per-second measurement depends on the scene as much as on the compositor, and that a
measurement without a declared scene **is not a measurement**.

And it is not enough that it moves: it must move **at every redraw**. The scene moved by typing keys — which the
project used from phase 3 to phase 9 — produces bursts and pauses, and the number that comes out has no
meaning.

**The right form**, and it must be kept: a full-screen, opaque client that redraws at every *frame
callback* of the compositor. Beside it, **how much the client draws must be counted**: it is the check that says
whether the ceiling belongs to the compositor or to the scene. Without that check, on 7 Aug we would have attributed to
Mutter a ceiling that belonged to the scene — and vice versa.

> ⛔ *Here `weston-simple-egl -f -o` was named as «does exactly this, and costs nothing in
> GPU». **It must be removed as an operational reference**, for two reasons: `[M]` **on 13 Aug 2026 it is not
> installed** on the test machine (rootfs in RAM, §2.5-bis) — so whoever followed this line
> found a command that does not exist; and the sentence **carried no mark**, so it passed for a
> verified fact.*
>
> ⇒ ⭐ **The rest form of phase 3 is the scene written by us**: `banchi/03-scena.c`
> (`wl_shm` + `xdg-shell`, 144-bit mark, four counts among which the **waits**, verification of
> `wl_surface.enter`) and `banchi/03-b14-scena.c` (the EGL variant). ⚠ **Two of them exist**, and it is an
> open decision whether only one survives.
>
> > ⛔ ⚠ *This line ended with: «where the cross-check was done, they agree **within
> > 4 %**, with **0 waits** on both sides». **It must be narrowed**: the 4 % holds on the low
> > and high cells and on the positive control, **not on cell D** — the result the cross-check
> > was needed for. In `banchi/03-b14-esiti-scena2.jsonl` cell D carries `scena_sul_mio_monitor: false`,
> > `palco_stabile: false` and **1 frame in 25 s**, and that scene's return check does not
> > add up (52.84 against 80.28). **Corrected on 13 Aug 2026**, a finding of the phase 3
> > coordinator.*

⛔ **And there is a third point, which was not written here and costs as much as the first two: the scene must
be on the MONITOR BEING CAPTURED.** On a stage with virtual monitors that is not the user's
monitor, and it is not even «the first»: the virtual monitors were **four**, and a scene opened on
the wrong one produces a bench that runs, does not fail, and **measures someone else's stage**.
⛔ The symptom is the worst possible — **zero frames, or frames of a scene that is not
ours** — and it looks like a product defect.
⇒ **The scene declares which monitor it is on, and the bench verifies it** instead of taking it for granted.
*Price: **four rounds thrown away** in a single day — two at step 3 and two at step 1 of
phase 3.*

> ## ⛔⛔⛔ And the same day the trap came back to bite **the result that cited it** — §1.1-bis
>
> *13 Aug 2026, evening. The line above had been written in the morning, after throwing away four
> rounds. In the afternoon, Mutter's «grid law» was declared **verified on 13
> points** and written into **nine documents**. The grid cells were **two**, and both of them
> carried `scena_sul_mio_monitor: **false**`.*
>
> ⭐⭐ **THE BENCH HAD WRITTEN IT IN ITS OWN FILE.** It did not hide it, did not get it wrong, did not
> keep quiet about it: it printed the field `scena_sul_mio_monitor: false` beside every cell, it counted
> those cells as **contaminated**, and on the verdict it wrote out in full *«⛔ la legge NON regge su
> 0 punti su 0: la spiegazione della quantizzazione va riscritta»*. ⛔ **And nobody looked: the
> number was read, and not the line beside it.**
>
> | | |
> |---|---|
> | ⛔ **the lesson** | **A bench that declares its own invalidity is useless, if whoever reads it looks only at the result.** The field that saves the day and the line that throws it away are in the **same file**, two centimetres from each other |
> | ⇒ **the rule** | before copying a number into a document, read **the bench's verdict**, not the cell. If the bench has a validity field, **that field is cited together with the number**, or the number is not cited |
> | ⚠ **and the form of the error** | it is not inattention: it is that **a plausible number raises no suspicion**. The 13 points were plausible, the bench really had a way to produce them, and the explanation added up. ⇒ The check cannot be «looks right» |
> | 💰 **the price** | four rounds thrown away in the morning, and **one false line in nine documents** in the afternoon — written by the same project that had just written the lesson to avoid it |
>
> ⭐ **And the thing that makes it a lesson and not an anecdote**: the trap did not come back on a new bench
> or on a new piece. It came back **on the result that cited it**, within the same day, with the
> lesson already written. ⇒ A written lesson protects from nothing until it becomes **a field
> that someone is obliged to read**.

*Price of the whole lesson: all the rate measurements of phases 3-9. Detail: `REFERENCE.md`
R32.*

### 1.2 The bench is certified before the measurement

Make sure the bench can produce the expected result **before** pointing it at the unknown.
Otherwise a negative outcome is ambiguous between «the unknown does not work» and «the bench was not working».

Done twice, and twice it saved the day: in phase 0, certifying with an instrumented client
that the stream really contained RemoteFX Progressive **before** connecting the phone;
in phase 4, counting the decoded frames before saying «the client does not draw».

*Detail: `PIANO.md` phase 0, `REFERENCE.md` §10 n.2.*

> ### ⛔⛔ And a certification can be **green because it tests the judge in the wrong unit**
>
> *13 Aug 2026, phase 3. It is the most insidious way of failing this lesson, because the lesson
> **was applied**: the judge was certified before the measurement, and the green was true.*
>
> ⛔ **The green said «the judge can tell apart», and the question was «tell WHAT apart».** The
> certification exercised the judge in the unit of the **reader** — the one in which the datum is
> read back — instead of in that of the **acquisition**, that is the unit in which the phenomenon to be measured
> really shows up. They are two different units, the judge treats them as identical, and the test passes in
> both cases.
>
> ⇒ ⭐ **The question missing from §1.2, which must be asked together with «can the bench produce the expected
> result?»**: *«in which unit did I make it produce it, and is it the one in which the real phenomenon
> arrives?»* A positive control built in the convenient unit — the one in which the bench already reads —
> **certifies the reader, not the measurement**.
>
> ⚠ **And it is recognised by one symptom only**: the certification is easier to write than it
> should be. If building the positive case cost nothing, suspect that it was
> built from the wrong side of the instrument. *(The same form, from the side of the test instead
> of the certification, is §2.2.)*

### 1.3 A bench that does NOT reproduce is not a test of correctness

It is the reverse of 1.2, and it is more insidious because the bench is **green**.

Two reproductions of the zero-copy defect — client in a container on loopback, client on
another machine on the LAN — stayed green while the defect was alive in real use. The fix
written on that basis was shipped to the user and **made things worse**.

What found it was a bench of a different form: **the ring**, that is one frame in ten recorded
continuously with the time, which asks nobody to be present at the right instant.

*Price: half a day of the user's, and a fix to withdraw. Detail: `REFERENCE.md` R29.*

### 1.4 A sample taken at startup says nothing about the steady state

Looking at the **first ten** frames of a capture, the damage came out as «covers everything» in nine cases
out of ten, and the right suspicion was discarded. The first ten are the startup, when everything is
repainted. Over three hundred, the ratio flips: **282 out of 300 had partial damage**.

The same form of error had already shown up on the bandwidth measurement, which weighed nothing because the
markers all ended before the frame.

*Detail: `REFERENCE.md` R29 and R19.*

### 1.5 Isolate ONE function only, and call it from outside

When the chain is already narrowed to two links, don't do another bench round: write the
minimal program that calls **only the suspect function** on a known input.

Forty lines closed in half an hour a question open for a day — the DSP that flipped the
sign of every PCM sample — after five layers had been suspected in turn.

*Detail: `REFERENCE.md` R24.*

### 1.6 Don't deduce the sender: ask the kernel

When a process dies and nobody admits to having killed it, **don't deduce**. Three concordant measurements
on three different cgroups seemed to prove that it was systemd; they were true and proved nothing,
because the sender had never been *asked*.

A signal handler that records `si_pid`, `si_uid`, `si_code` and the stack: twenty lines, a single
run, and the answer was that the server **was killing itself** inside a library.

*Price: three wrong diagnoses and a phase postponed wrongly. Detail: `REFERENCE.md` §7.4.*

### 1.7 Verify from the side that must receive

The sender's log says it **called a function**, not that the byte arrived.

For three phases the server politely wrote «farewell to the client» while the client, at the same time,
wrote «network error»: a second library call that nobody suspected was missing. And the
same rule settled the question of the *scaled output*: the answer came from **a
photograph of the client's screen**, not from our log.

*Detail: `REFERENCE.md` R12 and §10.2.*

### 1.8 When a component can decide by itself, you must tell it what to do

A component that chooses autonomously produces **two different measurements under the same label**, which
is worse than not measuring.

The same mistake twice: the hardware encoder that silently fell back to the CPU believing itself
on the GPU, and the driver that deduced the bitrate control mode from how two fields were filled —
constant bandwidth, without anyone having chosen it and without a line of log.

**Corollary**: when a component is asked for **by name**, don't fall back to another one. Fail
by declaring it.

*Detail: `REFERENCE.md` R27 and R31.*

### 1.9 ⭐ A denied read is not a read that says zero

*Learnt on 7 Aug 2026, and it cost a wrong line in a reference document for half a
day.*

The measurement said: **«KWin without a monitor opens no DRM node and loads no GL library,
so it composes in software»**. It was false. The command was `ls -l /proc/<pid>/fd | grep dri`, and it
printed nothing — but not because there were no DRM nodes: because **the kernel denied the whole
directory**. `/usr/bin/kwin_wayland` carries the extended attribute `security.capability`, and a binary with
file capabilities is **not dumpable**: `/proc/<pid>/fd` and `/proc/<pid>/maps` become readable only
by root, **even for the user who started it**.

⛔ **The defect of form is that «empty» and «forbidden» look the same.** A list filtered with
`grep` loses the command's exit status, the error goes to stderr — where nobody looks — and the
result enters the document as a measured fact.

**The three rules that follow, and they hold for any measurement:**

1. **A measurement that can say «zero» must be able to tell zero from failure.** Look at the
   exit status, or print the count *and* the error, not one of the two.
2. **Every measurement wants a positive control, on the same instrument.** The same morning a
   second measurement searched for a string inside KDE's binary index and did not find it: the
   conclusion «the file is not indexed» would have been false, because that search did not find
   **even the 133 system applications** (the index keeps strings in UTF-16). The positive
   control — *«can this instrument find something that is surely there?»* — cost ten seconds and
   prevented the second wrong line. It is §1.2 applied to every single instrument, not only to the
   bench.
3. **When read code and measurement contradict each other, suspicion goes first to the measurement.** Code
   has no environment: the measurement does, and the environment is where the errors are.

*Detail: `REFERENCE.md` R32 (the closing box) and `STUDI.md` §kde §5.1.*

> ### ⭐ The fourth rule, and phase 1 imposed it by repeating the error three times in one hour
>
> *9 Aug 2026, first day of V2 benches. The three rules above were written, read and
> cited — and the defect came back **three times in the same evening**, always in the bench, never in the
> product:*
>
> | | What the bench said | What it was |
> |---|---|---|
> | 1 | «0 symbols out of 4» | `grep -q` with `pipefail`: the **successful match** read as a failure |
> | 2 | «exit 0» on a failed clone | a `\| tail` at the end of the command: the exit status was `tail`'s |
> | 3 | «no trace: the prediction holds» | two trees passed as **one** string: grep searched **nowhere at all** |
>
> ⛔ **The third is the worst, because it printed a green**: *«the prediction holds»* from a search
> never run, with `2>/dev/null` hiding the «No such file or directory» that would have said so.
>
> 4. ⛔ **A measurement MUST declare what it looked at — the denominator, not only the
>    result.** «Zero occurrences» is not a datum until it comes with *«inside 447 files of
>    2 trees»* and with a check that searches for **something that must be there** (*«"nghttp3" found in 110
>    files»*). A count without a denominator is not a measurement: it is a hope with a number
>    in front.
>
> ⚠ **And the reason this rule is born here and not earlier**: the first three speak of how a result is
> *interpreted*. This one says that **the result must come with what makes it
> readable**, and it applies when the instrument is written by whoever measures — that is always, in a
> project where the benches are ours. In all three cases the cure was **the same**: make the
> instrument say what it was looking at, and in all three it found the defect in a minute.

> ### ⭐ The corollary, which arrived the next day: a denominator is read where the thing happens
>
> *10 Aug 2026, the SNI test of B2. The fourth rule was applied — the probe **declared** its
> denominator, at every leg — and the denominator was **false**.*
>
> The probe had to answer *«does the server serve the certificate to whoever sends no SNI?»*, and it printed
> `server_name spedito: '192.168.0.2'` reading it from the **configuration** of `aioquic`. Two lines
> of that library, in two different files:
>
> | | |
> |---|---|
> | `asyncio/client.py:66-67` | if the field is empty it puts the host there — **even if it is an IP address** |
> | `tls.py:1551-1556` | and then, writing the ClientHello, if that value is an IP address it **throws it away** |
>
> ⛔ **So the configuration said `'192.168.0.2'` and nothing went on the wire** — and the leg
> «with SNI», which used the address, sent **exactly what the other one sent**. The two legs
> measured the same thing while the probe declared they were opposite.
>
> 5. ⛔ **A denominator is read where the thing happens** — on the wire, not in the configuration; in the
>    process, not in the intention. And when it cannot be read there, have it **confirmed by a
>    program that is not ours**: here the log of `lsquic` did it, writing *«SNI is not
>    set»* while looking at the same wire from the other end.
>
> ⚠ **Why it is more insidious than the rule it extends**: a false denominator is **worse** than
> no denominator, because it gives the measurement the air of having already been checked. Nobody
> verifies twice the line that says *«here is what I looked at»*.
>
> ### ⛔ And the corollary of the corollary, which holds for **verdicts** and not for measurements
>
> *Same day, the measurement with the browser.* The bench printed **`OK — i motori provati hanno
> registrato il loro esito`**, and the engines tried were **zero**: the presence check looked at
> the wrong argument and skipped both of them, saying so in a warning line that the final
> verdict contradicted.
>
> ⛔ ***«All those tried went well» is true even when those tried are zero.*** And it is the
> most insidious form of green of all, because **it does not need something to go wrong**: the
> others are born from an error, this one is born from an empty set. A bench that measures nothing
> passes any criterion written as *«all results are good»*.
>
> 6. ⛔ **A verdict too has a denominator, and it is how many things it approved.** It is printed beside
>    the outcome, and if it is zero no outcome is given.
>
> ⚠ **And the same evening, the first rule came back in a new guise**: the bench declared
> **dead** two servers that were listening, because it checked them with `kill -0` as a normal
> user on **root** processes — where the answer is *«operation not permitted»*, that is an error,
> not *«does not exist»*. ⛔ **Empty and forbidden with the same face**, for the third time in four
> days, this time on a sanity check: the cure is `[ -d /proc/<pid> ]`, which everyone can
> read.

> ### ⛔⭐ And the seventh guise, which points the finger at the wrong defendant
>
> *10 Aug 2026, evening, bench B3.* The bench declared that the server violated an invariant:
> it accepted a second connection it should have refused. **The server had been right from the
> first instant.**
>
> The bench waited for a word in the first client's log to know when it was attached — and
> **Python buffers stdout when it is redirected to a file**. That line appeared only
> at the process's exit, that is **at the exact instant the client detached**. The check
> printed *«the first one is attached»* reading a truth that had just expired.
>
> ⛔ **It is not a false red: it is a red pointed at the wrong culprit.** The other six guises of
> this defect stop the work or bless it wrongly; this one sends you to search in a place where
> there is nothing, and the more plausible the place — an invariant just written, a module just
> born — the longer you stay there.
>
> 7. ⛔ **When a bench accuses the code, the first suspicion stays on the measurement** (§1.9 point 3), and
>    the way to remove it is **to ask the instrument for the instant, not the fact**: who took the
>    slot, when, and how many remain. Two lines of instrumentation and the transport timestamps
>    closed the case in one round.
>
> ⭐ **And the practical rule**: *a file written and closed is a fact; a printed line is a hope
> about the moment someone will see it.* A bench that synchronises two processes must not do it
> by reading logs.

> ### ⛔ 8. «The file is there» and «the file is the one I just built» are two different questions
>
> *The eighth guise, of 10 Aug 2026, and this one had already started the wrong server.*
>
> The bench of B11 built a server **faulty on purpose** and then checked that it could
> start it: `test -x bsslserver`. The compilation had **failed** — one `struct` too many in front
> of a typedef — but the binary from two hours earlier was still on disk, executable. ⛔ **The bench
> started the HEALTHY server declaring that it had started the faulty one**, and all twelve cases
> would have failed with the red on the **page**, which had nothing to do with it.
>
> ⚠ The form is that of §1.9 point 1 — *a measurement that can say «zero» must be able to tell
> zero from failure* — applied to an **artefact instead of a number**. A file from yesterday
> answers «yes» to *does it exist?* exactly like one from now.
>
> ⭐ **The rule**: after building something, look at **the builder's outcome**, not the
> presence of the result. And when the result has a mark — here `REMOTIX B11` in the source —
> check **that too**, because it answers the right question: *is inside it what had to
> be there?*
>
> ⚠ **And a smoke test found it**, not the bench: eight connections that asked for eight
> faults and printed the bytes of the `ECCOMI`. They were **all identical**, including the one that asked for
> «no fault». *A bench that compares every case with a control case identical to itself
> tells «the fault is not there» from «the page does not see it» before accusing anyone.*

> ### ⛔ 9. Truncating a log that someone holds open does not reset it: it digs a hole in it
>
> *The ninth guise, of the night between 11 and 12 Aug 2026, and it produced a **false red** on a
> round in which all four legs were COMPLIANT.*
>
> `: > registro.log` on a file the server holds open brings it to zero length, ⛔ **but does not
> move the offset of whoever writes to it**: at the next line the kernel fills with NULs everything that lies
> before. `[M]` the log of P5 ended up with **37,120 NUL bytes at the head out of 66,289**, and the
> real text starting right after.
>
> ⛔ **And the way it blinds is silent, which is the part worth the lesson**: `grep` that
> meets a NUL stops printing the lines and says `binary file matches` — ⛔ **with the same
> exit status 0**. So `grep -c` went on counting, and the bench's *positive control of the reading
> channel* said «healthy»; it was `grep | sed` that received that sentence instead of the line.
> The bench read «I could not find out with which address the server sees us» and sent the
> unlock command for **192.168.0.2, that is the server itself** — which answered *«was not
> banned»*, as it always will. ⚠ A true statement about the wrong subject.
>
> ⚠ **And the defect lived in a single instrument**: what segmented the same log was a Python
> program, which the hole does not stop — so the legs passed. *Two instruments reading the same
> file can see two different things in it, and the one that keeps quiet is not the one that is right.*
>
> ⭐ **Three rules, not one**:
> 1. **a log is reset where it really resets** — when nobody holds it open (at
>    shutdown, or restarting), and whoever offers an «empty» command makes it **refuse** with the process
>    alive, explaining why;
> 2. **`grep -a` on every file a verdict depends on**: the cost is nil, and without it, a single byte
>    out of place turns a test line into a sentence about itself;
> 3. ⭐ **and the hole is declared instead of being worked around** (§1.9 rule 4): the bench now counts the
>    NULs and writes them, so «the log does not say» and «I could not read the log» remain
>    two different sentences.

> ### ⛔⛔ 10. **«It did not show up» is not «it holds»** — and the tenth guise is the most elegant
>
> *13 Aug 2026, phase 3 step 5, check **P5** of the delay ring.*
>
> The bench had to prove that the ring holds **out-of-order** frames. After **three** different
> injectors the count of the overtaken ones was **0**, and the bench printed **green**.
>
> ⛔ **Zero overtakings does not say «the ring holds them»: it says «the phenomenon did not show up».**
> They are two different sentences, and the first is a **property of the product** while the second is a
> **property of the afternoon**. The bench had proved nothing: it had described its own
> failure to provoke the case, and had written it in green.
>
> ⭐ **And the cure is not one more check: it is that the bench SAYS it.** Now P5 is declared **NOT
> RUN**, which is the true outcome. ⛔ An honest `[?]` is worth more than a green: the green enters a
> catalogue and every measurement that comes after it **leans on it**, because it inspires trust (§1.3).
>
> ⚠ **And the reason the injector could not get there is as instructive as the rule**: out of
> order is not born (only) from the network, ⛔ **it is born from the SIZE of the frame** — the event fires
> at the *completion* of the stream, so the arrival order is the order of the **sizes**, and a
> big keyframe is overtaken by the deltas that leave after it. ⇒ Whoever delayed the packets was
> acting on the wrong quantity: it is §1.13, from the side of whoever **provokes** instead of whoever tolerates.
>
> 10. ⛔ **A check that did not see the phenomenon MUST declare itself not run**, never green. And the
>     question that unmasks it is that of §1.11 rule 1: *«what would the opposite case look like?»* —
>     if a broken ring would give **the same zero**, that zero proves nothing.

> ### ⛔⛔ 11. A bench can accuse the product of not holding a condition that **it created itself, and illegally**
>
> *13 Aug 2026, phase 3. It is the eleventh guise, and it is related to the seventh — the finger pointed
> at the wrong defendant — but worse: here **the defendant does not exist**, because the contested fact
> never happened on the wire.*
>
> The bench had to prove that the product holds a low stream credit. It announced
> `initial_max_streams_uni = 6`, the round ended with `STREAM_LIMIT_ERROR`, and for a few hours
> the defendant was the product.
>
> ⛔ **The `6` was never announced.** The bench wrote it **after** the handshake — something
> that **RFC 9000 §4.6 forbids** — so it never passed on the wire. `[M]` **the server had 128 slots
> granted and opened 14 of them.** ⇒ **The library violated nothing and the product did not have that
> defect.**
>
> ⚠ **Why it is more insidious than the other ten**: the others falsify the **reading** of a true
> fact. This one **manufactures the fact**, and manufactures it **by violating the specification the product respects**
> — so the product reacts correctly to an impossible condition, and its correct
> reaction is read as the defect. ⛔ **The more sophisticated the bench, the more capable it is of building
> conditions that do not exist on the real wire.**
>
> 11. ⛔ **A bench that simulates a condition of the peer MUST comply with the peer's specification**,
>     and the compliance must be **verified on the wire, not in the intention** (rule 5). The question is: *«what
>     I wanted to announce, did it **arrive**, and at the moment the specification allows it to be said?»*
>     ⭐ And it is answered **by counting from the receiving side**: 128 granted against 6 declared is a
>     difference that shows in one line, and closes the case without touching the product.
>
> ⭐⭐ **And the sequel is worth as much as the lesson**: hunting the false defect, a **real and
> worse** one came out — **B-18**, a delta thrown away for lack of a slot that **did not trigger the keyframe
> request**, and that wrecked the image forever **silently**. ⇒ *A hunt started from a
> wrong suspicion is not time lost, as long as it ends by looking at the code instead of the verdict.*

> ### ⭐⭐ The fifth rule: a number that cannot be known is not printed — 16 Aug 2026
>
> *The rule with the highest damage/cost ratio of `RCP.md` — «at detach every pressed key is
> released» — had a single witness in the log, and that witness said **always zero**.*
>
> The hook `input_rilascia_tutto` promised, in its contract: *«returns how many it released,
> so that the bench can count them»*. ⛔ **In the real product that count cannot exist
> there**: whoever holds the map of the pressed keys is **another process**, and the answer does not come
> back. Whoever stitched it answered `0` meaning *«the request has left»*; whoever printed wrote
> *«0 among keys and buttons were pressed»*.
>
> `[M]` Four detaches with the key and the button really down: the line said `0`, and the child —
> **ten milliseconds further down, in the same file** — said `2`.
>
> 5. ⛔ **When whoever answers cannot know the number, the answer MUST be a value that says
>    «I don't know», not a zero.** A zero is a measurement; «I don't know» is something else, and the two must
>    not be able to have the same form. ⭐ The cure cost three lines: the real count, `SENZA_CONTO`
>    (*«done, and someone else knows the number: look for it there»*), `IMPOSSIBILE` (*«it could not be asked:
>    if something was pressed, it stays pressed»*).
>
> ⚠ **And the reason this is the worst of the five**: the other four make a measurement be read
> wrongly. This one makes **a protection that might not be there look fine** — and the way the
> protection fails and what the log declared had **exactly the same look**.
> ⛔ The comment that explained everything was written, correct, and two functions away from the one that
> printed: **a true comment in the wrong place is not a defence.**

### 1.10 A permission can depend on an environment variable that nobody documents

The capture gate on KWin is a field in a `.desktop` file (§3 of `STUDI.md` §kde) — and for five
tests in a row it denied, with the file written right, in the right place, with the right path. The
cause was **`XDG_MENU_PREFIX`**: without that variable KDE's service index is built
**empty**, and no `.desktop` is found — not even the system ones. In a desktop session
the variable is there, because the desktop itself sets it; in an environment composed by us, it is not.

**The general lesson**: when an authorisation mechanism consults an **index**, the question
is not only *«is my file written well?»* but *«who builds that index, and with which environment?»*.
And before trying variants of your own file, **turn on the log of the component that denies**: here
the decisive line was in a different category from the obvious one (`KWIN_UTILS`, not `kwin_core`) and
told apart in one word two causes with opposite cures — «I did not find the file» against «I found it
and the field is empty». Five bench starts to guess, three seconds to have it told.

*Detail: `STUDI.md` §kde §3.3-bis.*

### 1.11 ⭐ An indirect test proves what it proves, not what we hope

*Learnt on 8 Aug 2026, correcting two tests written the day before.*

To know whether a compositor renders on the GPU or in software we had two «structural» tests, chosen
because they do not depend on what the compositor *declares* — which is the right criterion (§1.8). But
both prove **less** than we had attributed to them:

| Test | We had attributed to it | It really proves |
|---|---|---|
| the process opened a **render node** | «renders on the GPU» | ⛔ **nothing**: KWin opens it in the backend's constructor, **even when it then renders in QPainter** |
| the capture stream delivers **MemFd** and not DMA-BUF | «the compositor is in software» | ⛔ **nothing about the compositor**: it depends on what the **client** asked for. With a client that asks for DMA-BUF, the same compositor delivers it |

**The form of the error is always the same**: a **necessary** condition is used as if it were
**sufficient**. The open render node is necessary for the GPU, not sufficient; DMA-BUF is
possible only with an EGL backend, but its *opposite* says nothing unless it was asked for.

**The two rules:**

1. **For every indirect test, write what the opposite case would show.** If you cannot say how
   a software compositor would look, the test does not distinguish and must be changed.
2. **If the component can answer, ask it.** On KWin the exact answer — driver and chip — is
   one line of D-Bus (`org.kde.KWin.supportInformation`, `STUDI.md` §kde §5.3-bis). Half a day of indirect
   tests for a datum the compositor gives away.

⚠ And the corollary that ties this lesson to §1.8: `KWIN_COMPOSE=O2` — the switch that
was meant to *guarantee* the GPU — **is inert** (measured). So «telling the component what to do» is not enough:
you must also **verify that it obeyed**, and with a test that can tell the difference.

*Detail: `STUDI.md` §kde §5.1, §5.3-bis, §5.4 and `REFERENCE.md` R32.*

> ### ⛔ The third case, from the browser: **`Emulation.setDeviceMetricsOverride` measures the emulation, not the browser**
>
> *13 Aug 2026, phase 3. Same form, different instrument, and it is the one all our browser
> benches hold in hand.*
>
> ⛔ **`Emulation.setDeviceMetricsOverride` changes `clientWidth` without emitting `resize`.** The
> geometry moves, the number the bench reads changes, and **the event the product lives on never
> arrives**. ⇒ A bench that relies on that command to prove *«the page reacts to
> resizing»* proves that **the emulation changed a field**, not that the browser
> resized anything.
>
> ⚠ **The form is that of this section**: a **necessary** condition — the size changed —
> used as if it were **sufficient** — so the page received the resize. And the
> opposite case, which rule 1 requires being able to describe, has **the same look**: a page
> that ignores resizing entirely sees `clientWidth` change in exactly the same way.
>
> ⇒ ⭐ **The cure is rule 2**: what you want to know is whether **the event** arrived, and the event
> can be counted. The bench counts the events and declares them; and if the resize did not arrive
> it says *«the stage, not the product»* and stops — instead of giving a verdict on the product.

### 1.12 Hardening a service can break a permission, and silently

To make the compositor choose the right GPU, the obvious way was `InaccessiblePaths=` in its systemd
unit — one line, no code. Effect: the right GPU, and **the capture permission denied**, with
the usual symptom «this compositor does not expose the protocol». Measured: **0 log lines on the
permission query against 13** in the same configuration without that line; and it is not the visibility
of the files, which inside the namespace is intact.

**The general lesson**: systemd's hardening options (`InaccessiblePaths`, `PrivateTmp`,
`ProtectHome`, everything that implies `PrivateMounts`) change **the view of the world** of a process,
and an authorisation mechanism that inspects *other processes* or the environment can stop
working. When you harden a service that grants or receives permissions, **the test that the
permission still works must be redone** — it is not implicit.

*Detail: `STUDI.md` §kde §3.3-bis and §5.6.*

### 1.13 ⭐⭐ A tolerance is written on the **true quantity of the phenomenon**, or it moves one step at every rereading

*Written on 12 Aug 2026, after **the same line of `RCP.md` was corrected four times in
one evening** — P8 → P11 → P13 → P14 — and every cure moved the defect instead of removing it.*
*⛔ **Reopened on 13 Aug 2026**: the times are **seven** — P8 → P11 → P13 → P14 → P19 → P20 → P21
— and ⛔ **P14 did not «hold»**. The quantity held (the `numero` field); what had remained a substitute
was everything around it. The sequel is at the end of this section, and whoever cites this
lesson **refers here instead of copying the succession** (finding **R13.6**).*

**The scene.** The protocol needed to tolerate the frames **already in flight** when the canvas
changes mid-session. The first three drafts described that phenomenon with a **substitute
quantity**, and each was exact in the scene that had motivated it and **wrong by one step
just outside**:

| # | The quantity chosen | Where it broke |
|---|---|---|
| **P8** | *«the size is that of the previous canvas»* | ⛔ whoever drags a window sends **two** canvas changes, and the third size is neither one nor the other |
| **P11** | *«a canvas in force within the second just passed»* | ⛔ a **clock** where what must drain is a **queue**: on a slow line the frame arrives later, and invariant I1 falls — *never detach* — precisely in the condition I1 exists to protect |
| **P13** | *«ends at the first keyframe at the new size»* | ⛔ that keyframe **overtakes** the frames in flight, and not by chance: the old one is the biggest and §5.2 forbids abandoning it |
| ⭐ **P14** | **`numero`** — the field the protocol already carries | *(holds)* |

⭐ **What should have been looked at the first time: the field the protocol already carries.** The question
*«was this frame captured before the canvas change?»* had **an exact answer inside
the 28 bytes of the header for three days**: the counter `numero`. And a frame in flight has
**always** a lower number than the first one captured after the change — not «almost always»: **always**,
because the counter grows at capture.

> ⛔ **The rule.** When you write a tolerance, name **the true quantity of the phenomenon being
> tolerated** and look at whether the protocol — or the format, or the API — **already carries it**. If you are about
> to write a **substitute** — a size, a time, an event — that tolerance will move by
> one step at the first hostile rereading.

⚠ **And the second half belongs to the bench, and is worth as much as the first.** All four defects came out
building the scene **at the edge of the cure just written** — two changes instead of one, the slow line
instead of the fast one, the arrival order inverted — and **none** by building the scene the cure
described. ⇒ The case that counts is not the one the rule describes: it is the one **just outside**.

⭐ And it is worth noting **who** found them, all four: not whoever reread the document, but
whoever had to **enforce the rule** by writing the referee that judges it. *Applying a rule is
a way of reading it that rereading it is not.*

#### ⛔⛔ The sequel of 13 Aug: the times are seven, and the lesson also holds **on the boundary**

| # | The quantity chosen | Where it broke |
|---|---|---|
| **P19-P20** | §2.5: *«whoever receives a frame **before `SESSIONE`** closes with `ERRORE_PROTOCOLLO`»* | ⛔ **«whoever receives one before» is a substitute quantity**: the two QUIC streams are independent and nothing orders their delivery. It was enough to **lose the packet carrying `SESSIONE`** for a compliant client to kill a healthy session — I1 broken *because the line loses packets*, that is the condition I1 exists to protect. ⭐ The true quantity is **`ATTACCA`**, that is what the client sent **itself** |
| **P21** | *«the size the client named»* | ⛔ **§4.5 allows the server to grant a canvas DIFFERENT from the one asked for** — on KWin < 6.8 it is the normal path. Whoever asks for 1366×768 and receives the 1280×720 that is about to be granted **would close a healthy session**. ⭐ The true quantity is **«an `ADATTA_TELA` without an answer»**, not the numbers it carried |
| ⛔⛔ **P22 — and it is not a quantity: it is the BOUNDARY** | §3 declared *«the exceptions are six, and outside this list none are invented»* | ⛔ while §2.5 and §6.2 **mandated two that were not there**. ⇒ A client written by reading §3 **closed precisely the healthy sessions the other two lines saved**. Now they are **eight** |

> ⭐ **The rule widens.** It is not enough to write the tolerance on the true quantity: **the list of
> exceptions is part of the tolerance**, and it ages by itself. Whoever writes one elsewhere **adds the
> line to the list at the same moment**, or the document contradicts itself — and it is the same species
> as P12, that is a defect **of whoever writes the specification**, not of whoever implements it.

⭐ **And the common form of the three cures is the same as P14**: *what the client sent itself* —
**local, monotonic, independent of delivery**. The `numero` field was the first case; `ATTACCA` and
«a request in flight» are the same principle applied to two different phenomena.

⚠ **And one agent rejected its own first proposal, and one turned down that of whoever sent it**:
*«only if the bytes of `SESSIONE` have not arrived yet»* moved the measure from the wake-up of the
coroutine **to the bytes, which the network delays** — it would have been the seventh draft of the same
family; and *«the size the client named»* would have been the eighth.

*Detail: `fasi/rapporti/F2-4-filo.md`, and the lines in the box at the head of `RCP.md`.*

#### ⛔ And the same lesson, from the side of the BENCH: **P1 in blocks confuses delay with drift**

*13 Aug 2026, phase 3 step 5. It is not a protocol tolerance: it is a **measurement** tolerance,
and it moves the same way.*

**P1 is the decisive check of the delay ring**: the server delays by **N known milliseconds**
and the median **must rise by exactly N**. A bench that does not pass it does not know it is measuring
(`STUDI.md` §web §6.3).

⛔ **The defect: running it IN BLOCKS** — first a block of samples without delay, then a block
with delay N. The difference between the two medians contains **two things added together**: the delay that was
injected, and the **drift** the two clocks accumulated in the time separating the two blocks.
The bench reads them as one.

⚠ **And the cure that comes to mind first is the wrong one**: *widen the tolerance* until the
check passes. It is the exact form of §1.13 — a tolerance written on a substitute quantity —
and it has the extra defect of **making the check blind precisely to what it must find**: a P1 with
a wide tolerance stops telling «the median rose by N» from «the median rose».

⭐ **The real cure: INTERLEAVE.** The samples with delay and those without alternate in the same
time window, instead of being in two consecutive blocks. That way the drift acts **in the same
way on the two groups** and subtracts itself, and what remains in the difference is only the delay.
⇒ **The true quantity was not the tolerance: it was the TIME SEPARATING THE TWO GROUPS**, and it is brought
to zero instead of tolerated.

`[M]` **P1 green interleaved**: N = 25 → **+25.08 ms**; N = 60 → **+58.58 ms**.
⭐ **And the injection is OUTSIDE the product, with the clock anchor not passing through it** — if it
passed through it, P1 would pass **even with a broken bench**, which is the way a decisive check stops
being one without anyone seeing it.

### 1.14 ⛔⛔ A check that accepts **«one of the two paths»** hides a path broken forever

*Written on 13 Aug 2026, after a defect passed **under the certifications** for two days.*

`RCP.md` §3.1 makes a session close by **two paths**, and the bench judging them accepted
*«one of the two»*. ⇒ ⛔ **One of the two could have been broken all along and the bench stayed green**, because
the other passed — and that is what happened: `[M]` the path lost was always the same one, and the red
appeared only on the day when the one that fell was **the other**.

⛔ **And the defect was older than the code that brought it to the surface**: whoever looked for it suspected
the evening's rewrite, and the bytes said it had been there for two days.

> **The rule.** A criterion in the form *«at least one of N»* is written **only** if the N are
> really interchangeable for whoever receives them. If each has an effect of its own — and two closing
> paths do, because the reason that reaches the server is different — then the right criterion is
> **«each one when its turn comes»**, and the bench must say **which** one it saw, not how many.

⚠ And the corollary that costs most: **a check like that never fails for the defect it should
catch**, so it is not discovered even by certifying it — the injected faults find it green
before and green after.

*Detail: commit `d722460` carries the attribution in full — the bytes, the 33 ms against the 3-6 of the
healthy rounds, and the proof that the server **reads** that zero instead of synthesising it. The story of the
cure of 11 Aug is in `README.md`. ⚠ This line cited a report that **does not exist**: corrected
on 13 Aug 2026, on the report of the agent that went looking for it.*

### 1.15 ⛔⛔ **On Xvfb `requestAnimationFrame` NEVER runs** — and it holds for all browser benches

*Written on 13 Aug 2026, phase 3. ⛔ It is not a peculiarity of one bench: it is a property of the
stage on which **all** the browser benches of this project run.*

`[M]` **0 frames in 3 seconds**, with GPU and without, with `visibilityState` at **«visible»**. The browser
declares nothing anomalous — the page believes itself visible — and the frames simply do not
arrive, because without a screen there is nothing to pace them.

⇒ ⛔ **Every product path that goes behind a frame is DEAD CODE on the bench.** Not
«slow», not «rare»: **not run**, ever, and with the bench staying green because nobody asked
whether that branch had been taken.

> ### ⛔⛔ And the second half, which is the one that really bit
>
> **In Blink the `resize` event is delivered INSIDE the rendering cycle** ⇒ without frames **it never
> arrives**. A whole piece of the product — the one that follows the user's window — was unreachable
> on the bench, and the bench declared it green.
>
> ⛔ **What woke the pipeline was `Page.captureScreenshot`, called only `if args.copia`**: that is
> **a printing convenience option**, with an undeclared side effect. The same bench,
> on the same **healthy** product, gave:
>
> | | outcome |
> |---|---|
> | **without** `--copia` | ⛔ **RED, 5 claims fallen** — among them *«the canvas was RECOMPOSED (1 → 1)»* |
> | with `--copia` | green (1 → 3) |
>
> ⛔⛔ **And the green was not false on the merits: it was produced by the INSTRUMENT**, and it had never been
> proven capable of turning red. A printing option decided the outcome of a certification.

⭐ **The three cures, and they hold for any browser bench:**

1. ⛔ **the frame is ticked on purpose, a fixed number of times** — not «until it turns green», which is
   a criterion that adapts to the result instead of measuring it;
2. ⭐ **judge THE STAGE FIRST, before the product**: a probe counts frames and events, and if the
   `resize` did not arrive the bench says *«THE STAGE, NOT THE PRODUCT»* and **stops**, instead of
   issuing a verdict on someone;
3. ⛔ **and the limit is written at the head of the bench**: today that bench measures *«given a frame, the
   product follows the window»*, and ⏳ `[?]` **it remains open** whether the frame arrives **by itself** when
   the user drags a real window — on Xvfb no frame is produced, so there it is not
   measurable by construction.

⚠ **And the trap is armed elsewhere without having sprung yet**: a second bench holds only
because **none of its claims passes through a frame**. Whoever adds one falls into it, and falls in
green. ⇒ *A stage that cannot produce a phenomenon must be declared at the head of the bench, or the next
one who writes a claim has no way to know.*

> ### ⏳ `[?]` And two measurements from the same day must be kept SIDE BY SIDE, because they pull in opposite directions
>
> | | `[M]` 13 Aug, same stage |
> |---|---|
> | `requestAnimationFrame` in the main thread | ⛔ **0 frames in 3 s** — it never runs |
> | an `OffscreenCanvas` transferred to a worker | ⛔ it stops at **56.4 paints/s ≈ the 60 Hz frame**, with **13.4-21.7 ms** of extra cost per frame (`STUDI.md` §web §6.1) |
>
> ⇒ ⏳ `[?]` **On the same Xvfb one path sees no frame and the other pays the full frame.**
> They are two different mechanisms and both can be true — ⛔ **but until it is known which
> clock paces the second, it is not even known how much of the worker's penalty belongs to the stage and
> how much to the mechanism.** ⇒ It is the technical reason why `STUDI.md` §web §6.1 **is not buried without
> redoing the count on real hardware**: if that penalty belongs to the stage, on a GPU it changes sign.
> ⚠ *Written as an open question and not as a conclusion: neither of the two numbers is in question, it is
> putting them side by side that has no explanation yet.*

### 1.16 ⛔⛔⭐ **`getImageData` reads the store, not the screen** — and for two days it said everything was fine

*Written on 17 Aug 2026, phase 6. ⛔ It is the most expensive lesson of the project so far: two days of
hunting, seven hypotheses killed, and the defendant was **after** the last point a program can
read.*

The user saw **rectangular 64×192 blocks** on the remote desktop. Every instrument said
they were not there: the page's counters (`video 23→23`, zero holes, zero errors), the stream fed back to
`libdav1d`, `copyTo()` on the `VideoFrame` — ⭐ and `getImageData()` **on the same canvas and at the same
instants**: **0 superblocks out of place out of 180 000**.

⛔ **Then the canvas was photographed with a mobile phone, and the rectangles were there.**

⇒ ⭐⭐ **Between the canvas's store and the lit pixel there is a stretch that no API crosses** —
composition, driver, panel. A bench that reads the canvas back with `getImageData` is green **by
construction** over that whole stretch: it does not «get it wrong», **it does not get there**.

**The three rules that come out of it, and they do not hold only for the canvas:**

1. ⛔ **A bench declares how far it gets to look.** «I reread the pixels» is not «I saw what
   the user sees», and the difference must be written **beside the green**, not discovered afterwards;
2. ⭐ **When the user sees a defect and every instrument is green, the defendant is where the instruments
   do not reach** — not «the user is mistaken». It is I8 in its most uncomfortable form: the yardstick is their
   eye, and here it was **the only instrument that saw**;
3. ⭐ **And then the bench changes job**: `07-b49` measures nothing. It keeps the scene in view
   with **one** variable changed and asks the user to look. ⚠ A bench that does not measure is
   legitimate — as long as it declares that the judgement is the user's (§1.9 in reverse: here it is the *green* that
   looked at nothing).

⚠ **And the blind piece was already written**, in `STUDI.md` §web §6.3: *16-40 ms between drawing and the lit
pixel, which no API sees*. ⛔ It had been written as a **delay** and nobody had thought that in the
same stretch the **pixels** could break too. ⇒ A blind piece declared for one number is
blind **for all** numbers.

### 1.17 ⛔⛔⭐ **A new number goes into FIVE places, and one always stays behind**

*Written on 20 Aug 2026, adding codec **3** (H.264) to a protocol that had two.
⛔ The defects all came out in the same half hour, and none of the three was in the piece being
written.*

| where | what it did | how it showed up |
|---|---|---|
| ⛔⛔ **four per-codec arrays of length `[3]`** | codec 3 wrote **out of bounds** | *«il padre ha negoziato 8 bit (prima **1**)»* repeated: **a memory defect disguised as a negotiation defect** |
| ⛔ **a ceiling written by hand** in the child | it refused 3 | at least **it said so** — and it is the only one of the three that was found by reading the log |
| ⛔⛔ **a SILENT guard** in the parent | it threw away every frame of the new codec | **nothing**: session alive, encoder working (5 940 bytes, 1.6 ms), counters at zero, and not a line |

**The three rules that come out of it:**

1. ⭐ **The maximum number lives in ONE place only, and in the one that defines the fact** — here
   `rcp.h`, because it is the protocol that says how many codecs exist, not the three modules that read it.
   ⛔ Three equal constants written by hand are not redundancy: they are **three occasions to diverge**,
   and the one that diverges is always the one nobody rereads;
2. ⛔ **A `return` without a log is a defect paid for in gold.** The silent guard
   cost half an hour with all instruments green, ⚠ and it was written *well*: it refused a value it
   did not know. It lacked a single line. ⇒ **Every discard is declared** — once per cause,
   not once per frame (`LEZIONI.md` §1.9 and the 30.8 GB of §6);
3. ⚠ **An array indexed by a protocol value is sized on the protocol**, and the name
   of the constant says so (`CODEC_MAX`). ⛔ A `[3]` with «the codecs are two anyway» inside is a
   comment nobody rereads when a third one arrives.

⭐ **And the line that holds them together**: when a value is added to an enumeration that crosses
a boundary — of module, of process, of protocol — **search for the old value, not the file**:
`grep -n "codec != 1 && codec != 2"` would have found in one second the guard that cost the
half hour. It is the same line as §1.2 on the `keyint=1` copied into two benches: *search for the line, not the
file*.

---

### 1.20 ⛔⛔⭐ **A bench prints a number and does not compare it** — the most common form of defect we have

*Born from the adversarial review of the six benches of phase 6, 21 Aug 2026: twenty-two findings on
six benches, and **twenty-one have the same form**. 📖 `fasi/06-la-tela-e-la-vista.md` §5.5.*

⛔ **We were looking for the wrong thing.** From `04-b31` onwards the hunt was for the **expired anchor**: the
fault that no longer injects because the source underneath has changed. It is a real form — and in six
benches it showed up **only once**. The other twenty-one were all this:

> **the measurement is right, the number is there, and nobody compares it with anything.**

The faces it took, all `[R]` on the source:

| the face | the example |
|---|---|
| the **exit status** captured and printed | `local e=$?` … `echo "$e"`, and never an `if` |
| the **expected value declared beforehand** and printed | `giro()` receives the expected value, writes it on screen, never uses it again |
| the **denominator** the referee prints | *«0 coppie chiuse»* is in the output, and whoever reads it does not look at it |
| the **counter** printed with `inf` instead of with `ko` | the number is there, the verdict is not |
| **membership** in place of equality | `case " $R " in *" $CASO "*` — an all-red round «confirms» any fault |
| the **block that dies** and the loop that does not enter | `while … done < elenco.tsv` on a file never written: zero rounds, `stato` 0, *«tutti i guasti diventano rossi»* |
| the **normalisation that erases the phenomenon** | the offset is subtracted *before* measuring the offset |

⚠ **And why it is more insidious than the expired anchor**: a dead anchor leaves a trace — the
certifier prints `??`, the count of faults drops. ⛔ An uncompared number **leaves
nothing**: the bench does all the right work, collects the real datum, and then throws it away. Whoever reads
the output **sees the right number printed** and concludes it was checked.

⭐ **The two questions that find it**, and they cost one rereading:
1. for every number the bench **prints**: which line **compares** it? If none, either it becomes a
   verdict or it is removed from the output — because printed it looks checked;
2. for every `$?`, every `return`, every count: **is there a case in which it is zero and the bench stays
   green?** If yes, that is the defect.

⛔ And the corollary, which holds for whoever writes the bench before the product: **a bench without an exit
bit worth something is not a bench.** Three of the six exited `0` in every case — even with cases
all red.

### 1.21 ⛔⛔⭐ **A diagnostic instrument that breaks under load lies precisely when it is needed**

*21 Aug 2026, `fasi/06-la-tela-e-la-vista.md` §5.6.*

`registro.c` composed each line with **three calls** on an unbuffered `stderr`. Parent and
child append to the same file ⇒ under concurrency the writes interleave and lines are born
**without a timestamp**. `[M]` with six processes writing together: **2 464 orphan lines out of
4 800**, and a count looking for a family of lines lost **42 %** of them. With a single `write(2)`
per line: **zero**.

⛔ **Why it is a lesson and not just any defect**, and there are three things:

1. **the log is our main diagnostic instrument** (§2.7: *«there is no better diagnostic
   instrument than monitoring a real session, byte by byte»*) — and it broke **under load**, that is
   in the only scene in which it is really queried. With the machine idle it does not reproduce;
2. **the symptom was very far from the cause**: a bench tool that died with `ValueError`. The
   defect was looked for in Python for a whole round. ⚠ When a tool that reads data dies on
   real data, **the first defendant is the data**, not the reader;
3. ⛔ **and the case that makes nothing die is the worst**: a count that loses 3.8 % of the lines —
   the share measured on a real log — **stays plausible**. Nobody looks at it twice.

⭐ **The practical rule**: a diagnostic channel written by **several processes** wants an
**atomic** write — a single `write(2)`, under `PIPE_BUF` — and whatever exceeds the buffer must be **truncated with a
sign**: *a cut line shows, an interleaved line does not*.

⚠ And the corollary for whoever reads: **every tool that counts log lines must declare how many
it discarded**. A reader that silently skips the lines it does not understand is the same family as
[[1.20]] — a number nobody compares.

### 1.22 ⛔⛔⭐ **A systemd drop-in wins by NAME, and ours loses** — `zz-r` comes before `zz-s`

*22 Aug 2026, found by running `04-b20` in full. `fasi/04`, and it concerns `src/sessione.c` · `scrivi_dropin()`.*

`[M]` The product writes its drop-in into `zz-remotix-monitor.conf`. In the same folder five
benches of **other links** (`04-b31`, `04-b32`, `06-b33`, `06-b34`, `06-b35`) leave
`zz-senza-monitor.conf` — and ⛔ **`zz-s` comes after `zz-r`**, so the other one wins: the `ExecStart` in
force stays `--headless --no-x11`, and the session is born **without** a virtual monitor.

⭐ **The bench did not lie**, and it is the part that saves the story: the check *«written is not in
force»* (E1) **refused to measure**. ⛔ Without that check a session *without* a monitor would have been measured
believing it was *with* one, and **the red round would have come out green**.

⚠ **It is not a defect for the user** — nobody has that file on a real machine — **but the fuse is
in the product**, not only in the benches: the name `sessione.c` chooses loses against a name
that comes later alphabetically, and anyone who writes `zz-z…` tomorrow falls into it again.

⛔ **The rule**: a drop-in that must **win** is not called `zz-<nome>` hoping; either the
name is chosen for the order (`zzz-`), or one **verifies afterwards** that the `ExecStart` in force is one's own. ⭐ And
verifying is the only way that does not expire: next time the neighbour will be called `zzzz-`.

### 1.23 ⛔ **A scene is shut down by counting to zero, not by killing whoever opened it**

*22 Aug 2026, found **twice in the same night** by two agents who were not talking to each other —
`06-b35` and `06-b42`. It is not one agent's slip: it is a way of going wrong of the repository.*

> `pkill -f <titolo>` does not touch the process that **moves** the scene: in its `argv` the title **is not
> there** (it is in the terminal that opened it). ⇒ It survives, the next start puts **a
> second one beside it**, and the bench measures a scene nobody declared: **plausible, invisible,
> and twice as fast**.

`[M]` **Two cycles** after a single stop/restart. ⚠ On a bench that measures milliseconds, a double
scene **is not the declared scene** — and it does not give an error: it gives better numbers.

⛔ **And the guard that should have seen it asked for `> 0`**, that is *«there is at least one»* — which
**lets two through**. ⇒ The two right rules are:

- **shutting down**: demand **zero** survivors, and count to verify it;
- **starting**: demand **exactly one**, not «at least one».

⭐ The general form is that of [[1.20]]: a count looked at only to say *«it is there»* is not a
count, it is a boolean in disguise — and a boolean cannot tell **one** from **two**.

### 1.24 ⛔⛔ **Two benches on the same port kill each other silently — and the ban hits the innocent**

*22 Aug 2026, and the fault is the coordinator's: the same port assigned to two agents.*

The name of the system unit is derived from **the port alone**, and the template everyone copies did
`systemctl stop remotix-<porta>` **without looking at whose it was**. `[M]` One bench stopped another's
unit and put its own there, **truncating a thirty-minute measurement at 745 seconds**.

⛔⛔ **And the real damage came afterwards**: the robbed bench's probe went on knocking at the
**wrong** server with its own credentials, and the defence against guessed passwords banned
**the address** — which on a bench machine **is the same for everyone**. ⇒ **Twelve hours of ban
on whoever had done nothing wrong**, and the symptom for them would have been «too many attempts» on
every bench of theirs.

⭐ **The defence worked exactly as it must**: the defect is not its own. It is that **the unit of measure
of the ban is the address, and the unit of work is the port**.

⇒ Two rules, and the second is worth more than the first:
1. **look at whose unit it is before stopping it** — the description says whose it is, and whoever really wants
   to take the port declares it (`RUBA_PORTA=si`). ⭐ Put into the template, and tested: **it refuses to
   stop the user's port**;
2. ⭐ **a probe that insists is a weapon**: it must stop by itself on rejected credentials or on three
   errors in a row. ⚠ The file's comment said *«this probe cannot trigger the ban»* — **it was
   false**, and what discovered it was the ban.

### 1.25 ⭐⭐ **A cure is sought wherever it holds, not where it was found** — the forgotten twin

*22 Aug 2026. The lesson is not about counters: it is about how a cure is applied.*

On **17 Aug** a closing line was written that brings out the real counters of the **audio**, and its
reason was already `LEZIONI.md` §1.20: *a number nobody reads is not a number*. ⛔ **Five
days later it was discovered that the twin function of the video — `wt_video_conti()` — was defined,
declared, and nobody called it.** Zero callers in the whole source.

⇒ The cure had been applied to **one of the two twins**, and nobody had looked at the other.

⛔ **And the price of those five days can be measured**: the only number the benches could read was that
of the **announcements** — and it was called «not sent». `[M]` with an injected fault: **1 017 frames
not sent against 4 announcements**, that is **a factor of 254**. A bench that believed it counted frames
counted log lines.

⭐ **And the same lesson repeated an hour later, in reverse**: the new line **broke a
reader** of a bench, which searched for «conto finale» and from that moment found **two** — audio and
video — taking the last one and declaring it unreadable. ⚠ *A reader that searches for words also finds
someone else's* — it is §1.20 again, from the side of whoever reads.

⇒ **The question to ask every time something is cured**: *does this thing have a twin?* A counter,
a path, a function, a log message. ⭐ And if it has one, the cure holds for both of them
**in the same commit** — which is already the rule written for the recording format, and holds
the same here.

### 1.26 ⛔⛔⛔ **Two benches on the same MACHINE falsify each other silently** — and §1.24 was too narrow

*22 Aug 2026, phase 8. The coordinator launches five agents in parallel, each with its mandate,
its port, its ban file and its socket — that is applying §1.24 to the letter. ⛔ **And §1.24 was not
enough**, because it speaks of what kills itself. This one speaks of what does **not** kill itself.*

⛔ **The case, and the number hurts.** An agent measures the `input → vetro` ring and breaks down the
client's stretch. One of the sub-stretches comes out `[M]` **17.48 ms** — **19 %** of the ring — with an
honest denominator, the boundaries moved in the uncomfortable direction and a bench certified 53 out of 53. The
number is promoted to **target of the phase**, with a dedicated agent.

⭐ That agent comes back saying **there was nothing to cure**: `[M]` the same stretch is worth between
**0.39 and 2.80 ms**, with three independent benches, **and also on the same drawing path** as the
first. A third agent, who knew nothing of the first two, gets there on its own: `[M]`
**0.71 ms**, confirmed by **three readers** that agree within **0.005 ms**.

> #### ⛔⛔ AND HERE A CORRECTION MUST BE PUT, BECAUSE A FOURTH AGENT DISPROVED **THIS VERY LESSON** WHILE IT WAS BEING WRITTEN
>
> `[M]` On **its** stage, **with the machine idle**, the same stretch 9 measures **17.64 ms** (n=241) —
> and **with the machine loaded 15.37**. ⇒ ⛔ **Contention LOWERED it.** The 17.48 ms **was not contention**.
>
> ⇒ ⭐ **What remains standing of this lesson, and holds on its own**: contention **exists and is
> measured directly** — the four rounds below, same bench and same everything, give 8-17 ms of
> difference. ⛔ **What falls is the attribution**: that *that* number was *that* defect.
>
> ⛔ **And the real reason is more interesting, and it is §1.28**: the two benches **did not measure the same
> quantity**. One measures **the response** (how long the consequence of an input takes to arrive),
> the other **the age of what is on the screen**. Stretch 9 of the one contains a **wait**
> that does not exist in the other.
>
> ⚠ **The second-order moral, and it is worth more than the first**: *«it is contention»* is a convenient
> explanation, and once contention is measured it **becomes the good candidate for every number that does not
> add up**. ⛔ **I attributed to it a number that did not belong to it**, and I wrote it in a lesson
> — which is the place where an error lasts longest. A measured candidate **is not a licence for
> attribution**: every number must be attributed **on its own**.

⛔⛔ **The cause, measured directly** — four rounds, same bench, same stage, same scene,
same binary, **only who else is working on the machine changes**:

| | `input → vetro` |
|---|---|
| ⭐ **alone** | **74.08** and **75.81 ms** |
| ⛔ **with another agent's bench on top** | **84.22** and **90.87 ms** |

⇒ `[M]` **From 8 to 17 ms on the same ring**, for a bench that has nothing to do with it. And the threshold is
lower than it seems: `[M]` **a single round already holds ~3.7 cores out of 4 and ~29 Chrome processes**;
the one that produced the 17.48 had **56, plus five Xvfb**.

## ⭐⭐ Why it is WORSE than the defect of §1.24, and must be written in one line

| | §1.24 — the same port | ⛔ **§1.26 — the same machine** |
|---|---|---|
| what happens | a bench **dies** or **bans** the other | both **finish** |
| what you see | ⭐ **a red**, and you go looking | ⛔ **a plausible number** |
| who notices | anyone | ⛔ **nobody, until a second agent redoes the measurement** |

⇒ ⛔⛔ **A defect that shows up as a red is a lucky defect.** This one shows up as
a measurement, with its `[M]` mark, its denominator and its certified bench — and it led to
**promoting to target of the phase a stretch worth one twentieth** of what it said, and to
writing in the document a sentence (*«the user's eye and the instrument agree within 7 %»*)
that was the most cited line of the day **and that was an artefact of the orchestration**.

## ⭐ The three rules that come out of it

1. ⛔ **The load is declared beside the number, like the stage** (§2.0). Cores, load, how many
   browser processes, how many fake screens, **and which other benches are running on which ports**. A
   number without the load beside it cannot be cited;
2. ⭐ **And the bench goes RED if the machine is not idle**, instead of measuring anyway. It is the
   difference between declaring a condition and **demanding it**: the first is read in the record that
   nobody opens, the second stops the measurement;
3. ⛔ **Measurements are not parallelised on the same iron.** You can develop in parallel, you can
   read in parallel, you can **write** a bench in parallel — ⛔ **but the final rounds are
   taken in turn**, and whoever orchestrates must **coordinate the quiet window** instead of hoping for it.
   ⭐ The way that worked: an agent **killed its own round halfway** to free the
   machine for another, at the coordinator's request.

⛔ **And one thing this lesson does NOT authorise saying**: `[M]` on the detach bench
(`08-b67`) the load **inflates nothing** — 70.7 ms median with the machine loaded against **70.3** with the
machine idle. ⇒ *«The whole first wave is contaminated»* is **false**, and believing it would throw away
good measurements. **Contention hits some benches and not others, and which ones is measured instead of
deduced.**

⚠ **And the ALTERNATED before/after (A-B-A-B on the same tree) survives all this**, and it is the
reason it is demanded: the load hits both branches the same way, so **the difference
holds even when the absolute values are a ceiling**. ⛔ Whoever does «three rounds before, then three rounds after»
to save time loses exactly this protection.

## ⛔ And the count is not only of ports: **user, uid and shm name**

`[M]` On the same day, two agents asked for the same test user. The second one's terrain said
*«it is already there»* — ⛔ **and then reset its password and rewrote the systemd
drop-in**, that is it laid hands on the terrain of a live agent. ⇒ §1.24 must be read like this: **port,
ban file, socket, working directory, tree, user, uid and shm name are counted beforehand, not
only the port.**

### 1.27 ⛔⛔⭐ **The average colour is blind: a bench that looks at averages says green on a wrong image**

*22 Aug 2026, phase 8, and the agent's sentence is worth as much as the measurement: **«the milliseconds were already
beautiful while the image was wrong»**.*

⛔ **The case.** With zero copy turned on, the iHD driver **does not honour a stride that is not a multiple of 64
bytes**: it reads the rows at a stride of its own and the desktop comes out **slanted by a few pixels per row**,
**without raising any error**. `[M]`

| canvas | stride | %64 | is the mark read? |
|---|---|---|---|
| 1920×1080 | 7680 | 0 | ⭐ yes, contrast 1.000 |
| 1552×888 | 6208 | 0 | ⭐ yes, contrast 1.000 |
| 1544×888 | 6176 | 32 | ⛔ **no** |
| 1560×888 | 6240 | 32 | ⛔ **no** |

⛔ **1552 and 1544 are EIGHT pixels apart and give opposite verdicts.**

## ⭐⭐⭐ And the part that is worth more than the defect

`[M]` **The per-channel averages of the two streams match within 0.17 levels out of 255** — while the mark
**is not read on 0 frames out of 903**. Negative control (R↔B swapped): deviation **33** ⇒ the
averages instrument **works**, it simply **does not look at the thing that counts**.

⇒ ⛔⛔ **An image can be wrong at every row and have the same statistics as the right
one.** Averages, histograms and standard deviation are **invariant to the sliding of the
rows**: the defect moves the pixels without changing any of them.

## ⭐ The rule

⛔ **A check on the image must read something that can go WRONG, not something that can be
averaged.** A positioned mark, a contrast between two known zones, a per-row fingerprint — something
that **falls** if the pixels move. ⭐ And like every check, it must be proven with a **negative
control** that makes it fall (here: R↔B swapped, deviation 33) — or it is not known whether it is looking.

⚠ **And there is a corollary that holds beyond images**: it is §1.20 applied to pixels. *The measurement is
good and the judgement is detached from it* — here the measurement is good (the averages are right) **and does not touch
the property we care about**. Before trusting a check, ask: **which fault makes it
fall?** If there is no answer, it is not a check.

### 1.28 ⭐⭐⭐ **Two benches that do not agree can both be right: they are measuring two different quantities**

*22 Aug 2026, phase 8. For a whole day two benches of ours gave incompatible numbers
on the same phenomenon, and the coordinator looked for **who was lying**. ⛔ Nobody was lying.*

⛔ **The case.** The user reports by eye a gap of **0.50 title bars**. Bench `A`
says **0.47**, bench `B` **0.28**. Then it turns out that `A`'s number was inflated, it is
corrected, and `A` drops to **0.35**: ⇒ the two benches get closer **but the user stays outside both
of them**, and in the **uncomfortable direction** — they see more gap than the instruments measure.

⭐⭐ **The solution was not a defect: it was a definition.**

| | what it measures | |
|---|---|---|
| bench `A` | ⭐ **the RESPONSE** — how long the consequence of an input takes to arrive on the screen | contains **the wait** for a frame to be produced |
| bench `B` | ⭐ **the AGE** of what is on the screen — the echo always names the freshest event | does not contain that wait |

`[M]` On the same machine, the same day: stretch `1a` **11.55** against **0.165 ms**; stretch `3`
**28.74** against **6.3-10.4** ⇒ **−30…−34 ms** of **structural** difference, with a `[?]` residue
of 6-10 ms. ⇒ **The two numbers are not subtracted and not compared: they answer two questions.**

⛔ **And the multiplication that seemed to work added up by COMPENSATION**: `99,07 ms × 3 400 px/s
= 337 px = 0,47 barre` put **the delay of one quantity next to the speed of the other**, and the
result looked like the truth because **two errors cancelled out**. ⚠ A count that adds up is not a
right count: **the units must be named before the result.**

## ⭐⭐⭐ And the part that is worth most: **the user's eye was right, and the instruments looked at less than the truth**

Having excluded **by measurement** the three convenient explanations — the pixels (`[M]` **0.301 · 0.294 · 0.301 bars**
at 1560 · 1920 · 2560: **twice the pixels, zero slope**), the speed of the hand, the width
of the bar — the fourth remained, the one that always proves whoever measures right: *«the user estimated by
eye, they must have been mistaken»*.

⛔ **It was not needed.** Adding up what the bench **does not see**:

```
70.3 [M] + 11.6 [M] (the browser's event queue: in the bench it is 0.165 ms
                     because the hand is SYNTHETIC)
       + [?] 4-12 (hand → event)  + [?] 16-40 (drawing → lit pixel)
     = 102-134 ms  ⇒  0.48-0.63 bars
```

⭐ **The user reported 0.50: the low edge of the interval.**

⇒ ⛔⛔ **The bench was not wrong: it looked at a piece shorter than the real ring**, and the missing piece
was invisible **precisely because the bench's hand is fake**. A synthetic hand does not queue in the
browser's event queue; a real hand does, `[M]` **for 11.6 ms**.

## ⭐ The three rules

1. ⛔ **Before asking which bench lies, write what each one measures** — opening
   boundary, closing boundary, and **the name of the quantity**. Two numbers with the same label and
   different boundaries are not comparable, and nobody notices until they are subtracted;
2. ⛔⛔ **The explanation «the user must have been mistaken» is used LAST, and only after excluding the
   others by measurement.** It is the candidate that acquits whoever measures, so it chooses itself if nobody
   names it (`CODER.md` §1-bis, the boundary that moves in the convenient direction);
3. ⭐ **What the bench cannot see is ADDED, not ignored.** The declared blind pieces
   serve this purpose: here the sum of the blind pieces fully explained a 30 % gap that seemed
   a defect.

⚠ **And the explanation must be left falsifiable**: `[M]` after zero copy the bench gives **0.16
bars** ⇒ the prediction on the user's screen is **0.31-0.46**. ⛔ **If the user still said
«metà barra», this lesson is wrong** — and it is written here so that it can be said.

## 2. How to test

### 2.0 ⛔⛔ A bench that says «no» must say WITH WHICH STAGE it said no

*13 Aug 2026, evening. ⛔ **It cost a whole lane of a plan**, and it is the most expensive form
met so far, because the bench **did not break**: it answered, with precision, the wrong
question.*

A probe asked Chrome whether it could decode HEVC. It answered **no**, five times out of five,
with the firmness of a repeated measurement. Every now and then a **yes** came out, and it was filed as
*«a non-reproducible anomaly»*.

⛔ **The probe launched Chrome with `--disable-gpu`.** It asked a blinded browser whether it could see.

| Chrome on the same Xvfb | webgl | HEVC |
|---|---|---|
| **without** the flag | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
| **with** the flag | `niente webgl` | no |

On that «no» a conclusion had been written — *«it is not a codec problem, it is a
STAGE problem»* — and on the conclusion **a lane of work**, declared *«the one the
session starts from»*. The «yes» discarded as an anomaly was **the only right round**.

> ⛔⛔ **The lesson, and it is not technical**: *«it is not there»* and *«I could not look»* **look
> the same**, and the second is more frequent than the first. ⇒ **A bench that answers NO must write
> beside the answer the scene from which it gave it** — which stage, which flags, which visible hardware
> — exactly as `§1.1` demands the scene beside a number. **A no without the declared scene
> is not a no: it is an absence of information disguised as information.**

⭐ **And the signal was already there, in the record**: an outcome that fails to reproduce **once in six** is not
noise, it is an **undeclared variable**. ⇒ *When a bench gives two different outcomes on the same
question, the thing to look for is not which of the two is true: it is **what changed between the two rounds**.*

> ### ⛔⛔⛔ AND THE CURE OF THIS LESSON FELL INTO THE SAME LESSON, an hour later
>
> *The explanation above — «it was the flag, not the stage» — is **half false**, and the one who found it
> was another group. It is left written because **the way it fell is the real lesson**.*
>
> `[M]` with a counter-test that **does not go through the browser** — `xlsclients`, that is who is really
> attached to that screen:
>
> | how Chrome is launched | clients **on the Xvfb** | `screen` | webgl | HEVC |
> |---|---|---|---|---|
> | **as the bench launched it** | ⛔ **0** | **2560×1080** | GPU | true |
> | `--ozone-platform=x11` | ⭐ **1** | 1280×1024 | *nothing* | **false** |
>
> ⛔⛔ **Chrome ignores `DISPLAY` and chooses Wayland from `XDG_SESSION_TYPE`.** ⇒ The browser **had never
> been on the fake screen**, in neither of the two arms of the A/B: it was **on the user's
> desktop**. The flag mattered; the stage was already the real one.
>
> ⇒ ⭐ **The lesson grows stronger instead of weaker, and widens**: whoever wrote the cure
> declared a scene — *«Xvfb :85»* — **which they believed instead of verifying**, and wrote it in the
> record beside the number. **Exactly the defect they were curing.**
>
> > ⛔ **The complete form, and it holds for every browser bench of this project**: *declaring a stage
> > is not having it*. The stage is **verified from the other end** — who is attached to the screen, what
> > size the screen the page sees has, what hardware it names — and not from how the process was **launched**.
> > **An intention written in a command line is not a measurement.**
>
> ⚠ And the operational consequence is bigger than the codec it started from: **the browser benches of this
> project measure on the user's desktop believing they are on a fake screen** ⇒ undeclared
> contention, and every record that says «Xvfb» says something that is not so.

⚠ **Three younger sisters, paid for the same day and of the same family:**

| | |
|---|---|
| ⛔ **a comparison that was not a comparison** | two encoders timed **at free bitrate**: the one that looked competitive delivered **thirty times fewer bytes**. ⇒ *«Faster» at a thirtieth of the work is not faster* — **fix the work, and COUNT the output frames** |
| ⛔ **a list believed instead of run** | `av1_vaapi` **appears** among the encoders of `ffmpeg`, and in use it exits **218**: the hardware does not have the entrypoint. ⇒ *A list says the code is there, not that the machine can do it* |
| ⛔⛔ **a declaration in agreement with itself and at odds with the bytes** | see §2.0-bis below: **it cost the codec of the whole product** |

### ⛔⛔ 2.0-bis Asking for a format is not having it — reread what was PRODUCED

*13 Aug 2026, night. ⛔ **The product encoded in software for days because of one line of a
bench**, and the remarkable thing is that **every piece of the chain answered correctly the question
it had been asked**.*

A probe generator asked libx265 for the profile by name — `-profile:v main10` — and two lines
later passed `-x265-params …:**keyint=1**:…`. ⛔ **`keyint=1` makes it emit «Main 10 Intra», that is
`Rext`, `profile_idc = 4`, cancelling the profile asked for — and without an error.**

Those probes ended up inside the product's page, which used them to decide which codecs to
declare to the server:

| who | what it said | and it was **right** |
|---|---|---|
| the **string** | `hev1.1.6…` — profile **1** | yes, for what it declared |
| the **bytes** | `profile_idc = **4**` | ⛔ and nobody read them |
| `isConfigSupported` | **true** | yes: it answers **to the string** |
| the decoder | `EncodingError` **on the bytes** | yes |
| the page | *«this codec does not reach the pixel»* | yes, given what it saw |
| the server | negotiates **the other codec** | yes: it takes the client's first entry |

⇒ **Nobody was wrong, and the result was wrong.** A defect like this is not found by whoever rereads
the code: it is found by **whoever reads the bytes produced**.

> ⛔ **The rule**: `CODER.md` §3.9 says *«when a component is asked for by name, verify that
> it obeyed»* — and so far it has been applied **at the input**. ⇒ **It holds at the OUTPUT too**: when
> a format is declared, **reread the stream and compare it with the declaration**. A string and
> a stream that do not look each other in the face **are not two checks: they are zero**.

⭐ **And the cost of the missing check was two lines**: `ffprobe` on the stream just produced. The
bench that now does it (`banchi/02-pagina-sonda-verifica.py`) reads the probes **from the product's
file** instead of copying them, and **counts the frames** instead of asking.

### ⛔⛔ 2.0-ter Two measurements taken at different POSITIONS inside the same page are not compared

*13 Aug 2026, night. ⭐ A bench was about to deliver **«Firefox is 44 % slower than Chrome»**,
and the 44 % was not Firefox's.*

A bench tried several configurations **in a row, in the same page**, and compared their times. The
gap was stable and reproducible — **2.5 ms**, always in the same direction. ⛔ **It was the POSITION
in the sequence**: reversing the order of the cases, the three configurations gave the same number.

⛔⛔ **And the part that makes the trap nasty**: the effect **pulls in opposite directions on the two engines**.

| | whoever runs **first** |
|---|---|
| **Chrome** | is the **fastest** (7.9 ms) |
| **Firefox** | is the **slowest** (11.5 ms) |

⇒ A bench that always tried the cases in the same order — that is **any bench written in a
natural way** — would measure a difference between the two engines **that does not exist**, and would measure it
**stable**, that is with every appearance of a fact.

> ⛔ **The rule**: *when N configurations are compared inside the same process, the order is
> a variable* — and like every variable it must be **declared and reversed**. ⭐ The check costs **one
> more round**: redo the sequence backwards, and if the numbers move, what was being
> measured was the sequence.

⚠ **And there is a sister, found the same night, that concerns exclusive windows**: a bench that
measures N configurations in a row **is its own neighbour** — the one-minute load is an average, and
the configuration just finished presents itself as contention to the next one. `[M]` **5 refusals out of 8** with
*«other people's browsers: 0»*. ⛔ **The cure is not raising the threshold** — that would be switching off the referee — but
**waiting for one's own wake to die down** before asking for permission.

### 2.1 The three-client rule, and its insidious forms

No client covers the cases of the others. A defect seen **only** on one is almost always
a piece of information the server omitted, not an anomaly of the client — and the lenient client
supplies it, hiding it.

But the rule has at least three forms, and we paid for all of them:

| Form | How it showed up |
|---|---|
| on the **type** of client | two days for a missing `MapSurfaceToOutput`: two clients out of three drew all the same |
| on the **number** of connections | a shared TLS certificate killed the server **at the second** connection; a single-connection test stays green forever |
| on **who does the acceptance test** | a fix validated on a bench that did not show the defect, and given to the user to test |

> ⚠ **In V2 this rule changes form, not value** *(8 Aug 2026)*. The reference clients are
> no longer three and no longer other people's: they are **two, and ours** — Linux and Android, on top of the same
> `librcp`. The lenient client that silently supplies a piece of information omitted by the
> server disappears, and that is the form that produced the worst defects.
>
> ⛔ **But the free warning disappears too, and this is the loss to watch.** When two
> clients written by the same hand, on the same protocol code, agree, **they are not
> confirming anything**: they are repeating the same assumption. In v1 the disagreement between mstsc and
> `xfreerdp3` was a defect that declared itself; in V2 that defect stays mute.
>
> Hence, concretely: the other two forms of the rule — on the **number** of connections and on **who does the
> acceptance test** — stay intact and must be weighed more; and where the protocol leaves a choice, it is
> tested **against the written specification**, not against our other client.

### 2.2 A test can be green for the whole time the defect is alive

And it is the worst of tests, because it inspires trust.

| The bench counted | The defect changed |
|---|---|
| frames sent and blocks matched | **the samples**, not their number: the audio was full-scale noise |
| that the client process died | **when** it died, and why: the Android client stayed there |
| frames delivered | **which ones**: two whole screens alternating |

Hence the rule: **a bench that counts is not enough**. It must *listen* to what the client plays and
*look* at what the client shows — two frames delivered some time apart must be different
when the scene has changed, and the same when it has not.

> ⛔ **And there is a fourth row of that table, found on 13 Aug 2026, which does not concern what
> the bench looks at but the unit in which it looks at it**: a test can be green for the whole time
> the defect is alive because it exercises the judge in the unit of the **reader** instead of in
> that of the **acquisition**. The bench looks at the right thing, counts it well, and counts it **in the
> wrong quantity**. ⇒ The remedy is in §1.2, and it is one more question at the moment of
> certification, not one more check at the moment of measurement.

### 2.3 A test that fails the right code costs as much as one that passes the wrong one

The scroll-wheel bench looked for `asse dy=-10` while the log wrote `asse dx=0 dy=-10`: red,
with correct code. Another time an unexpanded `$1` made `grep` find anything, and
the checks turned green or red at random.

*Detail: `PIANO.md` phase 4, `REFERENCE.md` R29.*

### 2.3-quinquies ⭐ Two sides synchronised by time fail the right code

A bench that drives **two environments** — the session on this side, the client on that side — cannot coordinate them with
`sleep`s: the two clocks start when they start, and it is enough for one of the two to take a few seconds
more for the steps to overlap. At the KDE clipboard bench the two sides were out of step by
**thirteen seconds**: the client copied *before* the session had copied, the session pasted
its own stuff, and the check said red on code that worked — something seen only
by reading the log line by line.

**They are synchronised with markers**: a file the first touches and the second waits for. It costs three lines
and removes a whole class of false reds — and of false greens, which are worse.

⚠ And a corollary that holds for the clipboard and for every shared state: **what is left from the previous
round must be emptied at the start**. The client's clipboard still contained the string of the previous
test, it was announced at connection, and it looked like a result.

### 2.3-bis ⭐ The bench goes wrong where the system truncates, and lies in both directions

*Learnt on 8 Aug 2026, opening KDE capture, and they are three bench defects in one afternoon —
none of the three in the product's code.*

| The bench's defect | How it showed up | The general form |
|---|---|---|
| `pgrep -x weston-simple-egl` | **«the scene did not start»** while the capture delivered 58 frames per second | `comm` is truncated to **15 characters** and that name has 17: the exact comparison fails **always**. Use `pgrep -f` |
| `-sec-nla` passed to `xfreerdp3` | the client printed the help page and exited; the bench read «zero frames» and blamed the **server** | a rejected option is not a defect of the target. Copy the line from a bench that works, instead of remembering it |
| `2>/dev/null` on a command containing `sudo` | the bench stayed **hung forever, silently** | it is the trap of phase 1, and in one afternoon I paid for it again **three times**: the password prompt goes to stderr, and whoever must supply it never sees it |

⛔ **The rule that holds them together**: when a bench check is red and the thing it measures
*seems* to work, **the first suspect is the check** — it is §1.9 applied to the bench instead of to the
measurement. And when it is green, §2.2 holds.

⚠ **And the third row is the most instructive, because the lesson was already written.** Knowing that `2>&1` on a
`sudo` hangs is not enough: it is rewritten out of habit, every time you want to «remove the noise»
from a command. The antidote is not remembering it, it is **never putting `sudo` inside a command whose
stderr is redirected**.

### 2.3-ter A bench that rebuilds the same environment twice fails the second time

*Learnt on 8 Aug 2026: the Plasma session started at the first round and not at the second.*

Killing the compositor queues on systemd a *stop* job for its unit; asking to
start the session before that job is finished makes **the whole transaction be refused**, and the
message the user reads is only «Could not start Plasma session».

**The general form**: between «I killed the process» and «the service manager knows it» there is an interval,
and a bench that restarts in that interval behaves differently from the first run. You
stop the unit and **wait for it to be inactive**, instead of killing and restarting.

*Corollary, which is the real reason it must be written here*: **a bench must be run twice in a
row** before believing it. One that passes only from a clean machine is not a bench, it is a demonstration.

### 2.3-quater ⭐ A decision taken citing an unmeasured behaviour is taken by half

*Learnt on 8 Aug 2026, and the user found it in the first minute of real use.*

The decision «size fixed at connection» had been written with the reason beside it: *«the image
is scaled in the client»*. That sentence **had never been measured**, and the client scales nothing —
it opens a window as large as the canvas. The symptom, from the side of whoever looks: *«non riesco a
vedere tutto lo schermo, la risoluzione sembra ignorata»*.

⛔ **And the refutation was already in the house**, measured the day before and on another page: client-side
scaling goes through `MAPSURFACETOSCALEDOUTPUT`, rendered by **one client out of three**.

**The two rules:**

1. **In a decision, the reason is marked like everything else.** If it says «the client will do X» and
   nobody has seen the client do X, it is a `[?]` — and a decision that rests on a `[?]` must be
   written as provisional.
2. **Before writing a reason, search whether the project has already measured it.** Here it was enough to
   reread §10.2 of `REFERENCE.md`, which is the document of rules. The cost of not having done it
   was not the code — which was right — but **the user's time**, spent wondering why their
   resolution was being ignored.

### 2.4 What changes what is SEEN is not shipped validated only on the bench

The bench can say the image is better — with PSNR, SSIM and a frame looked at by eye — and
the user can look at it and say *«siamo tornati indietro»*. The yardstick is them.

Whatever changes the image stays **behind a switched-off switch** until they have looked at it.

*Price: a whole phase reset to zero. Detail: `PIANO.md` phase 10.*

### 2.5 At the start of every session: the state of the machine against what the documents declare

An environment file had been **read** at the start of the day, and the line that kept a
defective path switched off was no longer there — lost when the file had been rewritten for another reason.
Nobody compared what was there with what the documents said to expect, and the user
found a known defect in their face.

**And the general rule that follows, which is more important than the check**: the protection against a
known defect **is not entrusted to a configuration line that can be lost**. It lives in the program,
where removing it takes wanting to. It holds for protections and it holds for the values on which what
is seen depends: on 7 Aug the 60 cadence was put in `main.c` for this reason, not in a file.

*Detail: `REFERENCE.md` R29 at the end.*

### 2.5-bis ⭐ A machine that restores itself is not a machine that restores itself *complete*

The server's restore was written in three commands, and for a whole day it was enough. The first
real reboot showed that **two pieces** were missing, and neither was in the documents:

- **the disk does not mount by itself** — `/media` empty, `/etc/fstab` without lines, and the sources live
  there. Without that step the first of the three commands does not even exist as a file;
- **the benches depend on packages the provisioning does not install** (`pulseaudio-utils`, and for
  another bench `wl-clipboard`): they were there because someone had put them in by hand months before, and the
  provisioning inherited them without declaring them.

⛔ **Hence the rule**: a restore is tested **by rebooting**, not by rereading the script. Dependencies
installed by hand become invisible within a day, and the moment you notice
is always the one in which you need the machine to start again.

⚠ And the corollary that concerns measurements: **a measurement taken on a machine that has been grinding other things
for a day is worth less**. The user asked for the GNOME volume regression **from a machine
just rebooted**, and was right to ask — the numbers came out the same, but that was
the information, not the assumption.

### 2.6 The user is not the bench

Every hypothesis that asks «connect and tell me» costs one intervention of theirs. Hence:

1. **as soon as the cure is there, apply it and declare it**: «it works, the rest is optimisation» — and the
   choice *continue or postpone* is put before the user **at once**, not after five rounds;
2. **put a ceiling on the hunt**, declared at the start;
3. the tests are done by the bench; the user is asked for **the judgement**, which is the only thing the bench cannot
   give.

### 2.7 ⭐⭐⭐ There is no better diagnostic instrument than monitoring a REAL session, byte by byte

*Said by the user on 17 Aug 2026, at the end of a hunt that lasted an afternoon — and their
sentence is the title because it is their word: «proviamo a riprodurre un video da YouTube, tu monitora
la sessione su ogni singolo byte, così risolviamo una volta per tutte».*

⛔ **It is that gesture that broke the stalemate, and nothing else.** Before it there were: five bench rounds
**green**, a judge certified on six cases, an adversarial review with thirteen findings, and
**eight cures** of which six were real defects that were not what the user heard. None of
those things found the cause.

⭐ **A real session found it, watched while it happened.** Thirty seconds of YouTube with the
log open gave the number: the child produces **50 blocks per second**, the server
refuses **25**. Exactly half.

**Why it works, and why the bench does not.** The bench is a scene **you chose**: it contains the
defects you could imagine. A real session contains those you did not — and on top of that it
puts them **all together**, which is the condition in which they live. ⚠ Here the five greens were honest: the
bench measured the **content** (frequency, amplitude, purity) and the defect was in the **rhythm**.

**The three conditions for «monitoring» to be diagnosis and not contemplation:**

| | |
|---|---|
| ⛔ **all the links, on the same line** | here they were four — who produces, who encodes, who sends, **who listens** — and nothing was known of the fourth. As long as that is so, every cure seems confirmed by reasoning and none by measurement |
| ⛔ **record BEFORE it starts** | the recording is turned on and *then* the user is told «go»: a defect lasting thirty seconds cannot be captured again |
| ⭐ **look at the SHAPE of the number, not only the value** | the loss was *exactly* half. A network loss is never exactly half; **an arithmetic is**. A ratio that is too round accuses a count, not the world |

**And the thing that cost the most**: the fourth link — the side that **listens** — had no
place to speak. The page has a diagnostics box, ⛔ but with the desktop on it is full
screen and **not reachable**: asking the user to read it is asking them for something that cannot
be done. ⭐ The cure cost **thirty lines** — an endpoint (`/diario`) on which the client
writes its numbers, which end up in the **server's log** beside the other three.

⇒ ⭐ With the four links on the same line the diagnosis took **one pass**: *50 produced →
40 delivered → deficit 20 % → cushion 250 ms → a hole every 1.25 s*. Measured: **23 in 30
seconds**. The count closed to the decimal and **acquitted three defendants in one go**.

⚠ **And it contradicts neither §1.1 nor the value of benches**: the bench serves to *repeat* and to *certify*.
But when the user says «fa schifo» and the bench says green, ⛔ **you do not cure in the dark: you watch a
real session**. It is `CODER.md` §3.8 — *«verify from the side that must receive»* — applied to the
whole session instead of to one link.

---

### 2.8 ⭐⭐⭐ A SECOND ENGINE IS A SECOND READER — and it brings out the defects the only reader could not see

*17 Aug 2026, evening, the user's words after an hour on Firefox: «Firefox sta facendo emergere una
serie di bug nascosti davvero grossa».*

`PIANO.md` §0.4 says that two pieces of ours that agree **confirm nothing**, and for the
protocol the project paid the price of a second reader: `01-b3-cliente.py`, written in
another language reading **only** `RCP.md`.

⛔ **For the PRODUCT that price had never been paid.** Everything — video, input, clipboard,
shortcuts — had been measured on **a single engine**, of the Chrome family, and on **a single
system**. A browser that confirms itself is exactly the same thing as two pieces of ours talking
to each other.

**What came out in an hour, opening the same page on Firefox:**

| # | the defect | why it was not seen |
|---|---|---|
| 1 | ⛔ the **declared depth was 8 and 10 went on the wire** — `figlio.c` had `r.profondita = 10` written by hand, and the negotiated number **did not cross the process boundary** | ⚠ **it was there on both browsers**: HEVC carries its parameters in the stream (VPS/SPS) and Chrome's decoder reconfigured itself. AV1 does not — the page configures `av01.…08` and dav1d trusts it |
| 2 | ⛔ `Ctrl+Alt+Fine` **never reached the page**: on the Linux laptop that combination is taken by the local desktop | chosen and tested on Windows, where nobody grabs it |
| 3 | ⛔ the `preventDefault()` on `Ctrl+V` **prevented the `paste` event from being born**, that is it switched off the only path Firefox leaves to the clipboard | on Chrome the text arrives from **watching** (`clipboardchange`), which does not go through the keys |
| 4 | ⚠ **AV1 runs in software** on this iron, and it shows: the desktop is slow | nobody had ever negotiated AV1 — Chrome chooses HEVC, which here is in hardware |

#### ⏳ And the fifth — the artefacts on Firefox — is still open, but four hypotheses are DEAD

*Written so that nobody redoes them: a hypothesis eliminated by a measurement is worth as much as a confirmed one.*

| the hypothesis | how it died |
|---|---|
| ⛔ «the AV1 stream we send is broken» | **false.** Six frames taken **from the wire** and given to **libdav1d** — the same decoder Firefox uses — give a **perfect** image: smooth background, sharp terminal text, no blocks |
| ⛔ «SVT-AV1 aligns 962 to 968 and the count does not add up» | **false, and measured separately**: 2560×**962** encoded and decoded again comes back **exactly 2560×962**. The encoder pads inside and writes the display size; dav1d crops correctly. *(The quality measured then, SVT-AV1 going through libavcodec, no longer holds after phase 18.)* |
| ⛔ «the page receives a size different from the declared one» | **false.** The page says it by itself: *codificato 2560×962 · mostrato 2560×962 · tela in vigore 2560×962* |
| ⛔ «the browser's decoder gets it wrong and says so» | **false**: zero errors reported, and the filter that would have carried them to the server worked |

⇒ **One piece only remains, and it had never been put to the test**: the page's **drawing**
path. ⚠ The clean capture uses the Python client, which paints nothing — and on Chrome that
path has never had an independent witness.

⭐ **The new datum to start again from**: the page declares `formato BGRX`. A frame decoded
from AV1 comes out in `I420`; Firefox delivers it **already converted to RGB**. ⏳ And the second drawing
path — `?video=worker` — **does not paint at all** on Firefox: the page loads and the probe
runs, then nothing. `VideoDecoder` inside a `Worker` on Firefox 140 ESR is the suspect, and it has not
been verified.

#### ⛔⛔ The sequel of 17 Aug, second round: **COUNT THE LINKS, AND THEN COUNT THEM AGAIN**

The four hypotheses above left only one standing — «the page's DRAWING path remains» — and **that one
died too**, measured: a witness that drives the **real Firefox** with the
Marionette protocol (`banchi/07-b46-testimone-disegno.py`) pulled down **the canvas as PNG** on
three geometries, 2 800 frames, `dipinti == consegnati`, `saltati_coda 0`, `buchi 0`, and
the image is **sharp at 1:1**, terminal text included.

⛔ **And in doing so a link nobody had counted popped out**: the laptop's graphical session
is not local, it is **xrdp** (`Xorg :10`, `got RFX capture` = **RemoteFX**, a **tile**
codec). ⇒ Between our canvas and the user's eyes there was a **fifth** link, whose typical
faults are precisely «rectangular blocks» and «over time it stops updating».

⚠ **And it was not the culprit** — put to the test with a check of the same form of damage (whole window
repainted twenty times a second), the user's eyes, clean. ⭐ But the lesson is not
the verdict, it is that **for two days we reasoned on a four-link chain that had
five**, and no document said so. §2.7 says «ALL the links are needed»: the hard part
is not measuring them, it is **knowing how many there are**. ⇒ Before attributing a **visual** defect, write
the whole chain — including how the user is *looking*.

⭐ **And the counter that moved the hunt**: since the page also reports
`consegnati→dipinti · salt · buchi · ord · mis · err`, the user's real session **while
seeing the artefact** said `23→23` and five zeros. ⇒ No frame is missing: **the pixels inside
the ones that arrive are corrupted**. A defect no counter can see is
looked for in one way only — **by looking at the wrong image**, not at the numbers.

⭐ **And defect 1 is the one that teaches the most**: it was not a defect *of Firefox*, it was a defect
**of ours and universal** that a lenient engine absorbed. ⇒ The second reader does not find the defects
of the other: it finds **its own**, which had always been there.

⛔ **The rule that follows**: a function tested on one engine only is as tested as a protocol
read by one implementation only. ⚠ And «it works on Firefox too» is not enough: what must be tested is **the direction
that engine travels differently** — which is case 3, where the two paths are two whole code
paths.

---

## 3. What to ask a new compositor

This is the list that for GNOME we put together over eight phases. For the next desktop it is done in an
afternoon, before writing a line. Where we already know the answer, it is in the table.

| # | The question | Mutter 48.7 | KWin 6.3.6 | wlroots (sway 1.10, labwc 0.8) |
|---|---|---|---|---|
| 1 | **How is capture asked for without the portal?** | D-Bus `org.gnome.Mutter.ScreenCast` | Wayland protocol `zkde_screencast_unstable_v1` ✅ **written and measured, 8 Aug** | neither of the two: `zwlr_screencopy_manager_v1` |
| 2 | **Does it push the frames or make you pull them?** | pushes (PipeWire) | pushes (PipeWire) | **makes you pull**: one request per frame |
| 3 | **Is the protocol behind a permission?** | no | **yes** — a field of a `.desktop` file: `X-KDE-Wayland-Interfaces` [R], **plus `XDG_MENU_PREFIX=plasma-` in the environment** [M, 7 Aug] | no |
| 4 | **Without a monitor, does it draw on the GPU?** | **yes** | **yes** [M, 8 Aug]: `OpenGL renderer string` says it plainly via D-Bus — and **this** is the proof, not the open render node (§1.11) | **yes** |
| 9-bis | **Does the zero-copy buffer arrive with the fence ready?** | **no** | **no** [M, 8 Aug]: 830 out of 830 with drawing in progress. KWin does `glFlush`, not `glFinish` — so the fence is there and must be **waited for** | to be measured |
| 12-bis | ⭐ **Is the cursor INSIDE the captured image?** | no | **yes with `--virtual`** [M, 8 Aug]: no cursor plane ⇒ software cursor painted in the framebuffer being captured. The screencast's cursor mode **has nothing to do with it**, and there is no lever to prevent it. ⭐ **But the cure is not hiding it: it is making it INVISIBLE** — an `XCURSOR_THEME` theme with a 1×1 cursor at zero alpha, and the pointer goes back to being the client's, as on Mutter | to be measured |
| 10-bis | **What does resolution really cost?** | nothing up to 4K | **nothing at zero copy** (59 fps from 720p to 4K on an integrated Intel), **everything in memory** (49.6 → 27.0) [M, 8 Aug] | at 4K yes |
| 5 | **Can a virtual screen of the wanted size be asked for?** | yes, `RecordVirtual` | ⛔ **NO, and the code said yes** [M, 8 Aug]: `stream_virtual_output` with the `--virtual` backend answers **`Could not find output`**, for every size. And `--drm`, which has the real outputs, does not start from a seatless session. The output is created by the compositor's command line, and we attach to it | yes, headless backend |
| 6 | **How much does it deliver, with a scene that changes at every redraw?** | ⛔ **the question is ill-posed, `[M]` 13 Aug**: it depends on **how** you ask. Asking 60 of a monitor at 60: **31.5** (v1's «~37» **does not reproduce**). Asking **90 of a monitor at 120**: **61.4**. ⇒ See question 7, not this one | **59–60** | **61** (40 at 4K, because of the cost of the copy) |
| 7 | **How does the declared cadence behave?** | ⭐ `[M]` **13 Aug**: **it depends on how you ask**, and decoupling — monitor **120**, brake **90** — you get **61.4**; the «six tenths» **do not reproduce** (the low cell gives **0.50 clean**). ⚠ **The why is `[R]`, not `[M]`**: `maxFramerate` does two jobs together — capture brake *and* frequency of the virtual monitor — and in the code the brake computes `min_interval_us = 10⁶/maxFramerate` **truncated to an integer** against a tick of 16666.67 µs ⇒ whoever falls below **would lose a whole tick**: a **grid**, not a beat. ⛔ *This cell gave the grid as `[M]` «on 13 points»: false, corrected on 13 Aug evening — see the box under the table.* | **fixed refused here too** (`framerate` must be `0/1`); the ceiling is `maxFramerate`, and **the server honours it** [R] | to be measured |
| 8 | **Does it deliver whole frames or «diffs»?** | ⛔ **whole even at zero copy** — `[R]` **9 Aug**, and for two years we believed the opposite: the blit copies the **whole** view framebuffer, Cogl **deliberately empties** the clip stack, and for a virtual CRTC the view is a **single and persistent** `CoglOffscreen`, not a swapchain. The four buffers were asked for by us | **whole, always**, on 2–4 buffers, with the damage declared separately [R] | to be measured |
| 9 | **Does the buffer arrive already drawn?** | **no**: at zero copy 100 % arrive with drawing in progress | **yes**: KWin does `glFlush()`, and `glFinish()` on NVidia and llvmpipe [R] | to be measured |
| 10 | **What does resolution cost?** | **nothing** up to 4K | nothing | at 4K yes, and it is the copy in memory |
| 11 | **What does colour depth cost?** | **nothing**, and there is no packed 24-bit path | — | — |

| **13** *(new)* | ⭐ **Is a virtual screen RESIZED live?** | **yes**: the size is agreed in the PipeWire negotiation, changing it is a renegotiation | ⛔ **no on 6.3.6**: the mode is `const`, the list is fixed in the constructor, and `kde_output_management_v2` can only *choose* among the announced modes. Solved upstream (`kwin!7932`, milestone **6.8**) — **and by our same path**, the PipeWire negotiation | `wlr_output_state_set_custom_mode` exists and the headless backend already uses it [reading, **to be measured**] |
| **14** *(new)* | ⭐ **Whose is the clipboard?** | ⚠ **the compositor's here too** — it is `MetaSelection` `[R]` **9 Aug**. Only the **door** belongs to the remote session (`EnableClipboard`), and ⛔ **without a session the clipboard exists all the same**: the X11 bridge is unconditional in both directions, `xclip` works | **the compositor's**: `zwlr_data_control_manager_v1` v2, **no permission**, and it is there even if REMOTIX is not | the same protocol: `appunti_wlr.c` **is already written for this family** |
| **15** *(new)* | ⭐ **Is there a state in which the compositor REVOKES what it has already granted, and who has their finger on that button?** | ⛔ **yes, and it is the only one of the three**: entering the unlock dialog gnome-shell calls `inhibit_remote_access()` and Mutter closes ScreenCast, RemoteDesktop and InputCapture **refusing to recreate them**. The exception is `is_headless()` `[R]` — our condition, and **we did not ask for it** (`STUDI.md` §gnome §4) | `[?]` to be verified | `[?]` to be verified |

> ⭐ **15 is the question this list did not have**, and it came from the study of GNOME
> *(`STUDI.md` §gnome §14, where it is called «question 16» counting the `-bis` rows; here it takes the first
> free number, because in this document **nothing is renumbered**)*. Question 3 asks whether a
> permission exists; this one asks whether the permission **can be withdrawn live**, which is a different and
> more dangerous thing: you go and ask for the permission only once, at the start, and nobody goes back to
> look. It is asked together with 3.

> ## ⛔⛔ ~~Mutter's six tenths~~ → **MEASURED on 13 Aug: it is not a beat, it is a grid**
>
> *This box, written on 9 Aug 2026 reading `STUDI.md` §gnome §8.2, said: «`maxFramerate` is the
> capture brake and at the same time the frequency of the virtual monitor. **Two clocks at the same number
> beat against each other, and the beat is worth 0.61**. It costs three cells and zero product lines, and if it
> succeeds it brings 60 to GNOME». It was `[R]`, and carried its own reservation beside it: «until it is
> measured it stays a `[?]`; an explanation that adds up is not a cure that works» (§1.11).*
>
> ⭐ **The reservation was the right one, and the measurement proved it right twice: the cure works, and the
> explanation was wrong all the same.**
>
> ⭐ **THE FACT, `[M]`**: monitor at **120**, brake at **90**, and GNOME delivers **61.4** — cell **D**
> of `banchi/03-b14-esiti.jsonl`, clean, with the three checks closing.
>
> ⚠ **THE CAUSE, `[R]`**: read in Mutter's code, `maxFramerate` does not look like a continuous ceiling but
> a **GRID**. The brake computes `min_interval_us = 10⁶/maxFramerate` **truncated to an integer** —
> 16666 for 60 — against a tick of **16666.67 µs**: whoever falls below **loses a whole tick**. Not a
> **beat** between two clocks, a **quantisation**. ⭐ **It is the best explanation we
> have**, and it is consistent with cell D. ⛔ **But it is a reading, not a measurement.**
>
> > ⛔⛔ ⚠ *This line said: «`[M]` law verified on **13 points**: 8 confirm it, **0
> > disprove it**». **IT IS FALSE.** The grid's outcomes file,
> > `banchi/03-b14-esiti-griglia.jsonl`, carries **three lines**: the terrain and **two cells**
> > (`griglia-apertura-120`, `griglia-freno-90`), **both with `scena_sul_mio_monitor: false`**
> > ⇒ refused by the bench itself, which prints «⛔ la legge NON regge su **0 punti su 0**». The thirteen
> > points do not exist in any outcomes file. **Corrected on 13 Aug 2026**, a finding of the phase 3
> > coordinator, verified on the two outcomes files. ⇒ The quantisation goes back to `[R]`; the
> > table below stays `[M]`, because it all comes from `03-b14-esiti.jsonl`, seven cells all with
> > `scena_sul_mio_monitor: true`.*
>
> | monitor | brake | delivered | median | p99 |
> |---|---|---|---|---|
> | 60 | 60 | 31.5 | 33.31 ms | 35.53 |
> | 120 | 60 | 46.13 | 24.12 ms | 29.23 |
> | ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61.4** (60.04) | ⭐ **16.66 ms** | 20.43 |
>
> ⛔ **And the «six tenths» do not reproduce**: the low cell gives **0.50 clean and deterministic** —
> which is what a grid produces, and a beat does not.
>
> ⭐ **The cure succeeds**: monitor 120, brake 90, and GNOME delivers **61.4**. ⛔ **But the product today
> cannot ask for it** — `MOVIMENTO_FPS 60` is a compile-time constant, `RecordVirtual` does not take
> the frequency, and the virtual monitors are all @60. It is `[M]` **on the bench** and **zero in production**.
>
> > ### ⭐⭐ And the lesson, which is worth more than the number
> >
> > **An explanation that adds up, that explains all the data we have and that even points to a cure that
> > then works, can still be false** — and nobody notices, because the cure,
> > by working, confirms it. Here the beat explained the 0.61, pointed to decoupling, and
> > decoupling brought the 60: three confirmations in a row for a wrong cause.
> >
> > ⛔ **What took it apart was not the cure: it was the CELL JUST OUTSIDE** — the low cell, which the
> > beat wants at **0.61** and which gives **0.50 clean and deterministic**. The beat and the
> > quantisation **predict the same thing on the cell one wanted to cure**, and different things
> > **outside**. ⇒ It is §1.13 in its general form: *the case that tells two explanations apart is not
> > the one that produced them, it is the one just outside* — and the cell that tells them apart costs as much as
> > the one that confirms them.
> >
> > > ⛔⛔ ⚠ *This paragraph said: «What took it apart was not the cure: it was the **BLANKET
> > > MEASUREMENT** — **13 points** instead of the three needed to show that it works». **It is false, and
> > > the blanket measurement never existed**: its only two cells are refused by the bench itself
> > > (box above). What took the beat apart was **one** clean cell, A. **Corrected
> > > on 13 Aug 2026**, a finding of the phase 3 coordinator.* ⇒ ⭐ **And the lesson comes out of it stronger,
> > > not weaker**: the blanket was not needed, **the case just outside was enough** — as long as it is
> > > valid.

> ⚠ **The wlroots column was filled in later** *(8 Aug 2026)*. The «to be measured» cells above
> have an answer in **`STUDI.md` §xfce §12**, which redoes these fourteen questions with the wlroots
> column full, and in **`STUDI.md` §lxqt §4** for the case in which we choose the compositor ourselves. This
> table was deliberately not rewritten: the two readings sit well beside each other, and
> each carries the date of its own measurement.

⭐ **13 and 14 are the same question in two guises: *who owns the thing?***  It is the difference
that decided half the work on KDE — not «how is it done», but «whose is it». Where the thing belongs to the
compositor instead of to our session, who is in command changes: the size we **undergo**, the
clipboard we find **already there**. It is asked first, together with 4 and 6.

**Questions 4 and 6 must be asked first**, and together: without 4 you do not know whether the number of 6 is
comparable. The way to answer 4 is to look at which DRM nodes the process has opened and which
libraries it has loaded — not to trust what the compositor writes in its own log.

> ## ⚠ The KWin column was filled in by reading the code, on 7 Aug 2026
>
> The study is in **[`STUDI.md` §kde](STUDI.md#kde)**, and it is the proof that this list works: **eleven questions
> out of eleven have an answer before writing a line**. But three things must be said, and they are lessons
> in their turn.
>
> **1. A code reading is not a measurement, and does not replace it.** The cells marked `[R]` say
> what the compositor *can* do, not what it *does* on our machine. Row 4 was the borderline
> case: the measurement said «software», the code said GPU. ✅ **The evening of the same day the
> measurement was redone, and the code was right**: it was the *measurement* that was wrong (§1.9).
>
> **2. Question 4 must be asked with the right instrument, and on KWin there is a better one**: the **type of
> buffer** the capture stream manages to offer. DMA-BUF is possible *only* with an
> EGL backend, so it answers question 4 without asking the compositor anything — while «which DRM nodes
> it opened» requires looking at the right process at the right moment, which is precisely where
> our measurement stumbled. ⚠ **But watch the direction**: the test holds only if **the client
> offers** DMA-BUF. On the bench of 7 Aug the stream negotiated `MemFd` with a compositor that
> was **on the GPU** — because the limit was our client's. «Only MemFd ⇒ CPU» can be concluded
> **only after** verifying that DMA-BUF was asked for.
>
> **3. The list lacked a question, and on KDE it is the one that costs the most of all:**
> **«can the size of the virtual screen be changed with capture live?»** On Mutter yes
> (`pw_stream_update_params`), and phase 6 built dynamic resolution on it. On KWin
> **no**: a virtual output has a single, immutable mode, and it must be closed and recreated (`STUDI.md` §kde §8). It is the
> **twelfth question**, and whoever opens the next desktop should ask it together with the fifth.

**The instruments to answer already exist** and are in `fondamenta/banchi/banco-compositori/` — brought
here from the server on 8 Aug 2026, when the test machine was cleaned up: sources, scripts and
binaries already compiled, outside the product:

| | |
|---|---|
| `misura-cattura` | a PipeWire consumer that counts the frames and reports buffer type, damage, recycled buffers, whether drawing was finished, and the distribution of the intervals. It can set up Mutter's virtual screen by itself, or hook onto any node |
| `nodo-kwin` | a client of KWin's protocol; with `--elenca` it prints all the protocols a compositor announces |
| `misura-wlroots` | a `wlr-screencopy` client that makes the same measurement on the pull model |
| `banco.sh`, `banco-altri.sh`, `banco-catena.sh` | capture alone, the other compositors, and the whole chain up to the client |

---

## 4. The compositor's traps, in order of when they bite

They are Mutter's, but the **form** will show up again: the names will change, not the ways of failing.

| # | The trap | The general form, which is the useful part |
|---|---|---|
| 1 | The session creation sequence admits no permutations | **every permutation is punished with a different error**, and neither of them says «you got the order wrong» |
| 2 | Subscribe to the node announcement **before** starting the stream | an announcement that arrives *during* a call: whoever subscribes afterwards waits forever for something already gone |
| 3 | Metadata **is asked for**, or it does not arrive | and asking does not oblige giving: whoever reads must cope with its absence |
| 4 | The buffer type is agreed in **two** places | declaring only one makes the negotiation **succeed** with the opposite of what was wanted inside it |
| 5 | The *stride* is read from the buffer, never computed | the producer aligns the rows as suits it; deducing it gives slanted images |
| 6 | The compositor must draw on the **right card** | a buffer from another card is not importable, and the symptom is software composition without an error |
| 7 | systemd's session manager **does not update the groups** of an already living process | the compositor does not open `/dev/dri`, draws in software, and nobody says so |
| 8 | A frame arrives **only if something changes** | the last one must be kept and resent, or whoever connects to a still desktop stays black **until something moves** — and then it corrects itself, which makes it look like a startup delay |
| 9 | After a size change the first frame is **partial** | you do not wait for a silence: you wait for an **event**, and two are enough |
| 10 | Resize requests **echo** | every system that answers with latency to someone who does not yet know the answer chases itself; it needs settling **plus** a guard on the echo |
| 11 | Resizing **must not** redo the capture | redoing it drags along the control, the input devices and the state of the pressed keys |

---

## 5. The traps that are not the compositor's, but wait for you right beside it

| | The lesson |
|---|---|
| **The session bus** | does not survive a logout: the old object gives no error, **it gives silence**. And on the shared connection the library can call `raise(SIGTERM)` on your behalf |
| **The environment** | whoever starts a session **gives it its whole own environment**, including the variables that have nothing to do with it: a wrong locale inherited from a script prevented all applications from starting. It is composed from scratch, one variable at a time |
| **The asynchronous loop** | you never wait inside it: neither explicitly, nor in a destructor that waits for a thread to end |
| **Priority** | the audio path wants real time, and it must be **granted by the system unit**: a process without that permission cannot ask for it, and the symptom is audio that crackles *when the desktop is working* |
| **Whoever survives the logout** | reuses **nothing** of the dead session |
| **Volume, and where the tap is** | ⭐ an audio node applies the volume **downstream of the monitor tap**: whoever captures the monitor receives the signal at full scale whatever the slider says, **mute included**. The property that moves the tap exists but is `false` by default, and the PulseAudio compatibility modules set it in your place — so **a test done on a sink created with `pactl` acquits code that creates the sink by hand**. Measure on your own, not on an equivalent one |

---

## 6. The lessons on performance

### 6.1 The ceiling was a number we had written ourselves

For two months the missing frames were looked for in the encoder, in the protocol, in the network and
in the phone. They were in the maximum cadence we declared to the capture: asking for 30,
18 arrived; asking for 60, 37 arrive.

**The rule that follows**: before optimising a link, measure **how much enters** that
chain. A link faster than what reaches it produces nothing.

> ⭐⭐ **And on 13 Aug 2026 the lesson came true a second time, on the number this
> section cites.** *«Asking for 60, 37 arrive»* is not a ceiling: `[M]` **it does not reproduce
> at all** — at the cadence we asked for **31.5** arrive, and asking for **90 of a monitor at
> 120** **61.4** arrive. ⚠ **The why is `[R]`**: in Mutter's code the brake computes
> `min_interval_us = 10⁶/maxFramerate` **truncated to an integer** (16666 for 60) against a tick of
> 16666.67 µs ⇒ whoever falls below **would lose a whole tick** — the remainder of a **truncated
> division**. *On the evening of 13 Aug this explanation was written here as measured: it is not,
> see the box of §3 question 7 and `STUDI.md` §gnome §8.2.*
>
> ⇒ ⛔ **The ceiling was again a number we had written ourselves, and this time it was written twice**:
> once in the cadence we asked for, and once **in the way the compositor converts it**. The general
> form of the lesson widens: it is not enough to ask *«which number did we declare?»*, one must
> ask **«what does whoever receives it do with it?»** — because a truncation is visible neither in our
> code nor in the number we wrote.

### 6.2 CPU milliseconds per frame and frames per second are two different quantities

And they can move in opposite directions. Measured twice:

| | CPU per frame | frames per second |
|---|---|---|
| removing encoding from the CPU (phase 9) | 41 → 20 | 29 → **22.7** |
| turning on zero copy (phase 9, then verified on the whole chain) | 16 → **3** | 32.4 → **31.5** |

**A gain paid for in smoothness is not a gain**, and it must be said instead of showing only the
CPU number. Zero copy is worth five times on consumption and **zero** on the rate: whoever takes it up again
should do it for that.

> ### ⛔⛔ And on 13 Aug 2026 **the reverse case** arrived: the rate rises, the delay **does not move**
>
> *The two rows above have the same sign: the CPU improves and the rate gets worse. They served to
> prevent selling a CPU gain as a smoothness gain. ⛔ **The opposite case is missing, and
> in phase 3 we almost fell for it.***
>
> | the lever | the rate | the delay |
> |---|---|---|
> | decoupled cadence (monitor 120, brake 90) | ⭐ **from 31.5 to 61.4/s** | ⛔ **still** |
>
> ⛔ **Doubling the frames per second did not take a millisecond off the delay**, and the reason is
> that the bottleneck was elsewhere: most of the delay was ours, almost all of it in the software
> encoder. *(The milliseconds measured then depended on libavcodec's encoding without a card and no
> longer hold after phase 18.)*
> The 60 frames **remove an obstacle**; the number the user feels is made by the delay.
>
> ⇒ ⭐ **The lesson, in the form it lacked: they are THREE quantities, not two.** CPU milliseconds
> per frame · frames per second · **delay**. They move independently, and each
> pair has already produced a wrong line in a document of this project.
>
> ### ⛔⛔ And the same evening came the case that makes them say OPPOSITE things — the page in the worker
>
> *It had been decided to keep the canvas on the main thread (`DECISIONI.md` §2.8); the measurements, taken with
> software encoding, no longer hold after phase 18 and the table is removed. The direction remains.* *→ the software chain, redone in 4K: `fasi/18-senza-ffmpeg.md` §5.4.*
>
> ⛔ **On the real chain the worker painted more and seemed better. At saturation it was by far
> worse. And the delay said it was worse anyway.** ⇒ ⚠ **Which conclusion you take home depends on which quantity
> you chose first** — which is the most polite way in which a measurement can lie.
>
> ⭐ **The practical rule**: when a lever touches the video path, the three quantities are
> **measured and written, all three**, even those that are of no interest. A table with a
> single column is not a short measurement: it is an **oriented** measurement.
>
> ⚠ **And the real chain's number had an explanation, which is the third thing to look at**: the
> worker painted more because **there was the queue**. An advantage that exists only as long as the system
> is not at its limit is an advantage that vanishes **on the day it is needed** (`STUDI.md` §web §6.1).

### 6.2-bis ⭐⭐ A wait that protects one link is a delay for all the others

*15 Aug 2026. Found because the user said «riduci di qualche decimo di secondo il tempo fra
il clic e l'evento» — that is for a number no bench looked at.*

The child's loop did, in this order: **read what the parent says** (without waiting),
then **wait for a frame** up to 250 ms. Sensible: the child is another process, there one can
wait, and a quarter of a second keeps consumption low on a still desktop.

⛔ But the parent's input arrives **during** that wait, and whatever arrives a millisecond after the start
stays still for the remaining 249 ms. `[M]` On the user's real clicks: **median 136 ms**, and the
spread from 0 to 502 — the signature of a random wait, not of a slow network. Bringing the wait to
8 ms: **median 41 ms**, all samples between 34 and 47.

> **A wait sized on one link (the frames) becomes the delay of every other link that
> goes through the same loop (the input). And the second link appears in no count, because the
> loop was written looking at the first.**

⚠ The question that unmasks it is asked **before** writing the loop, and costs one line: *«what else
comes in from here, and how long do I make it wait?»*.

### 6.2-ter ⛔ The number that explains everything may have been in the log for a day

*Same night, and the second time in two days.*

The cause of the 136 ms was printed **once a second**, in a line nobody connected:

> `ciclo: 4 fotogrammi consegnati, 3 attese a vuoto …`

Three-four empty waits per second means four loops per second, that is 250 ms per loop. ⛔ The
line had been written to answer **another question** — «is the scene still, or is the loop
still?» — and it contained the answer to this one without its author knowing.

⚠ It is the same form as 14 Aug (*213 movements recorded by the server while the user saw
zero*, `dex-mouse-aperto`): the log already had the fact, and for two days nobody read it
because **they were looking for something else**.

> ⇒ When a number does not add up, before adding a measurement reread the log **looking for
> that number**, not the defect: the summary lines are written for one question only, and they often
> answer two.

### 6.3 The rate is decided by the client, if the link is fast

The regulator grants `MAX(2, rtt·fps/10⁶ + 2)` unacknowledged frames: on a fast link
it makes **2**, so the throughput becomes that with which the client acknowledges. It is correct — a slow
client is not flooded — but it has a consequence on **method**: a bench whose client decodes in software
measures the client, not us. It happened, and the 4K number was withdrawn for this reason.

**Before attributing a ceiling to the server, look at how much it works**: 0.08 cores with the queue full
means the server is waiting.

### 6.4 What does NOT cost

At capture neither **resolution** (4K performs like 1080p) nor **colour depth** costs.
So the fallback ladder 4K → 2K → 1080p serves the encoder and the bandwidth, **not** gaining
frames. Knowing what does not cost is worth as much as knowing what costs: it gets rid of the levers that
move nothing.

### 6.5 ⭐⭐ An optimisation that reasons on the **steady state** is blind to the **tail** — and the tail is what the user looks at

*15 Aug 2026, phase 5. Found from a symptom of the user's, and the cause was in a **comment
of ours** that explained why it was right.*

`cattura.c` delivered the frame **only if someone was waiting for it at that instant**, and the
line justifying it said: *«copying 8 MB for nobody would be work inside the real-time
callback, done for nothing»*. ⭐ **True in steady state**: if the frames flow, the one thrown away is
immediately replaced by the next and nobody notices.

⛔ **False in the tail**, and it is the only case that shows: a window that closes produces a
burst; we take the first frame and spend ~20 ms compressing it; those arriving in the
meantime are thrown away, **including the last one** — and after the last **none arrives**, because the
scene is still and the compositor sends only when something changes. ⇒ The user is left looking at the
**first** frame of a change that is already over, until some gesture produces
another.

**The symptom, as it arrived**: *«do `exit` e il terminale sembra congelato: appena muovo il mouse
si chiude»*. ⭐ **That sentence is the diagnosis**: if any frame at all aligns the screen, the
right one had been produced and not delivered.

**The three rules that remain:**

1. ⛔ **In a bursty chain, the last element is not one like the others**: it is the one that stays
   on the screen. An optimisation that discards «another one will arrive anyway» must be reread asking
   *«and what if this were the last?»*;
2. ⚠ **the real gain was bigger than the cure**: not only the last one was lost — **all**
   of those of every burst were lost, so every movement was jerkier than necessary, and nobody
   had ever noticed because the defect showed only in the tail. ⇒ *A defect that shows in
   a borderline case can cost in all the others, silently*;
3. ⭐ **and the feared cost was not there**: always keeping the last one **reuses** the buffer, and the
   real-time callback does a `memcpy` instead of an 8 MB `malloc`+`free` per frame.
   *The optimisation that defended itself with cost was also the most expensive.*

⚠ And the confirmation is the user's, not a bench's: *«ora il terminale si chiude subito… il sistema mi
sembra tremendamente responsivo, i tempi di risposta sono istantanei anche su Android»* — §7.3, the
yardstick is what is seen.

---

## 7. The lessons on direction

### 7.1 The numbers are set by the user, and technique serves them

Until 7 Aug a technical path was chosen and then what came out of it was measured. From that day
the order is reversed: **a technical choice is justified by showing that it brings one of the declared
numbers closer**; if it does not move them, it is not done, however elegant the gain it brings elsewhere.

### 7.2 Optimising in the wrong direction is worse than not optimising

Half the measurements of phase 10 were correct and answered the wrong question: «spending less
bandwidth» was considered a gain, while for this product the declared bandwidth is a **floor,
not a budget**. Before optimising a quantity, **have someone tell you whether that quantity is to be minimised
or spent**.

### 7.3 The yardstick is what is seen

A performance number nobody perceives does not justify the user's time. And, conversely:
when the user says it is fine, **it is fine** — phase 10 was closed like that, without being redone.

### 7.4 Predictions do not count, measurements do — and that holds for ours too

On 7 Aug it had been predicted that the Android client would gain nothing from the new
cadence, with a correct and documented reasoning: it receives a codec decoded in software, and
which costs the server two and a half times H.264. The user's judgement was *«performance
eccellenti»*.

The reasoning was right and the conclusion was not, because it started from an assumption never verified — that
one of the two sides was at its limit. Neither was: **the number we
declared was.**

> ⚠ **And in V2 the assumption must be redone from scratch** *(8 Aug 2026)*. The side that here had not been
> verified — «one of the two sides is at its limit» — changes completely: `aFreeRDP` decoded in
> software a codec nobody would have chosen, while the V2 client is ours and calls MediaCodec
> on HEVC. **The v1 number was not a ceiling of Android: it was the ceiling of that client.** It holds both for
> the wrong prediction and for the judgement that disproved it — neither of the two is inherited.

### 7.5 ⭐⭐ A deduction in place of a message is a defect that is waiting

*15 Aug 2026, night. Found by refuting the cure just written, and it holds for the architecture, not
for one line.*

The chain that carries the window's size up to the compositor was written and worked. The
parent asked the child to resize, and then **deduced the outcome from the frames**: *«if one of a
different size arrives, the stage has obeyed»*. It was faithful to a right rule of this
project — *«the truth is told by the frame, not by the outcome of the request»* — and it passed all the cases
I had in mind.

⛔ **Three agents sent to disprove it found three cases I did not have in mind**, and they are all
common:

| the case | what the parent deduced |
|---|---|
| the stage **already** has that size | «it has not obeyed yet» ⇒ three seconds of waiting for something already done |
| the stage **is not there** or did not make it | «it is still trying» ⇒ three seconds for news that was there at once |
| **two chained requests** (the user drags the edge) | the frame of the FIRST taken for the answer to the SECOND ⇒ desktop of the wrong size, **with the message counts in order** |

⇒ The cure was not «more checks», and it is the part that counts: it was **one more message**, from the
process that knew to the process that decided — carrying *which question it answers* and *what really
happened*.

> **When one piece must deduce something another piece already knows, the deduction is not a
> saving: it is a defect waiting for the case you did not think of.**

⚠ And the signal that tells it apart from a legitimate deduction is **always the same**: the deduction
holds as long as events come one at a time, and falls as soon as two overlap. If the case «two
requests in flight» has no obvious answer, the deduction must be replaced by a message.

---

## 8. The dead ends already walked — not to be redone

| What | Outcome |
|---|---|
| Limiting the server to a lower EGFX version for comparison with mstsc | dead end: on that version mstsc switches off H.264 |
| Giving more threads to colour conversion on the CPU | noise: 13.8 ms against 12.5. That time is not computation, it is memory |
| Waiting for the implicit *fence* of the DMA-BUF | changes nothing: it is the wrong one. The explicit one travels in a metadata item we were not asking for. ⚠ **Corrected on 9 Aug**: this row covers half the contract — the *acquire*. What is missing is the **release**, and it is on the other side (see the box below) |
| Adapting the **resolution** to the bandwidth | not feasible: scaled output is rendered by one client out of three, and resizing the virtual monitor rearranges the user's windows |
| Declaring to the capture a **fixed** cadence instead of «when it changes» | Mutter refuses it: no negotiated format, zero frames |
| Raising the declared cadence **above 60** | gives nothing: 120 declared, 37 delivered as with 60. ⚠ **It does not close the cadence path**: raising the number *only once* raises both clocks together, and it is the beat that eats the gain. The candidate of §3 is another move — **renegotiating the cadence alone, with the monitor still** |
| Looking for the frames bottleneck in the encoder, in the protocol or in the network | it was in our constant |

⚠ **Two of these rows belonged to RDP, not to the problem** *(8 Aug 2026)*, and they must be read with
care because the other five still hold in full.

| Row | In V2 |
|---|---|
| the EGFX version lowered for mstsc | **lapses**: neither EGFX nor mstsc exist |
| adapting the **resolution** to the bandwidth | **lapses by half**. The first reason was that *scaled output* was rendered by one client out of three — and the clients are now ours, so client-side scaling can be had. The **second reason stays whole**: resizing the virtual monitor rearranges the user's windows, and no protocol changes that |
| the other five | **stay**: they speak of threads, of *fences*, of Mutter and of our constant — none of them named RDP |

⛔ **And no row is deleted.** A documented dead end costs less than a rediscovered one: the
day someone proposes again «let's adapt the resolution to the bandwidth», this table will say that
in v1 it could not be done and **will oblige them to prove that in V2 it can** — which is exactly the work
the row must make them do.

> ## ⭐ A dead end that was not a dead end: the phase 9 hunt, in the wrong place
>
> *Written on 9 Aug 2026 from `STUDI.md` §gnome §1.3 and §8.1. `[R]`, and it reopens a hunt closed badly.*
>
> The two alternating screens were chased for two phases as an **acquire**
> problem: the buffer arrives with drawing in progress, so you wait for the fence. The code
> reading says the defect is on the other side, and it is a **release**: `can_reuse_pw_buffer` —
> the only point where Mutter waits for us — **gives up at the first line** if
> `SPA_META_SyncTimeline` is missing, and reuses the buffer **while VA-API is still reading it**.
>
> ⛔ **And it explains why the cure made things worse**: the accumulation surface copied only the
> damaged rectangles from a buffer that **already contained the whole frame** (question 8).
>
> **Two candidate cures, both small**: asking for `SPA_META_SyncTimeline` — which Mutter
> **offers**, and which today we do not ask for — or **holding** the `pw_buffer` until reading is
> finished, which is what the reference does, that is the opposite of what we had concluded.
>
> ⚠ **It is a reading, not a measurement**, and it is lesson 4 of `STUDI.md` §gnome §14: *a right measurement
> with an invented explanation is more dangerous than a wrong measurement*, because nobody
> questions it again. R29 stayed standing for two phases because of this.

---

## 9. The recipe, for opening support for a new desktop

In order, and each step is a lesson of the previous sections put in a row.

0. **Look for whoever has already done it — outside what has already been cloned.** *Added on 7 Aug 2026,
   and paid for the same day*: the KDE study concluded «in KDE there is no trace of RDP» after having
   searched **inside the eight repositories I had chosen myself**. The main reference — `KRdp`, KDE's RDP
   server, same library, same compositor, 4 200 lines — was in a ninth repository,
   and what found it was a question from the user. **The right question is not «is it in the repos I have?» but
   «who, in the world, does this thing on this desktop?»** — and it is asked before reading, not after.
1. **Answer the fifteen questions of section 3**, with the instruments that already exist. An
   afternoon, before writing a line of product. Questions 4 and 6 first, and 3 together
   with 15 — *«is there a permission?»* and *«can it be withdrawn live?»* are the same investigation.
   *(It said «eleven»: they were those of 7 Aug, before the studies added four —
   9 Aug 2026.)*
2. **Establish how it draws without a monitor** (GPU or software): it decides whether its numbers are
   comparable with GNOME's, and whether that desktop can be served on a server machine.
3. **Find the direct path to the compositor**, without the portal — and find out at once whether it is behind a
   permission, because the symptom is «this compositor does not have the protocol» and it wastes an
   afternoon for whoever does not expect it. ⭐ **And when it denies, the first move is not trying variants: it is
   turning on the log of the component that denies and having it tell you the cause** (§1.10). On KWin it takes three
   seconds, and the two possible lines have opposite cures.
4. **Measure capture alone**, with the declared scene and the count of how much the client draws.
   Only afterwards put the encoder and the wire back in.
5. **Reuse the benches of the phases that cross the same path**: a phase that touches a
   shared path is closed by re-running the benches of whoever already crossed that path.
6. **Test on the three clients**, and on at least two connections in a row.
7. **Have the user judge**, on what is seen, before declaring anything closed.
8. **Update the documents at the same moment** a measurement disproves them, with date and source.
   A reference that ages silently is worse than no reference.

### 9-bis ⭐⭐⭐ What does NOT belong to the desktop, and waits for you all the same

*Written on 15 Aug 2026, at the end of a night in which the remote desktop disappeared three times.
⛔ **Of everything it cost, almost nothing was GNOME's**: it was the system underneath — logind, PAM,
udev, Mesa, PipeWire. ⇒ On KDE, XFCE, LXQt and Cinnamon these rows **are paid again exactly as they are**, and
this section exists so that they are not paid twice.*

| the fact | how portable it is | where it is written |
|---|---|---|
| ⛔ **The compositor wants a logind SESSION of class `user`** — `/run/user/<uid>` is not enough, the bus is not enough, **linger is not enough** (it gives a scope of class `manager`). Mutter asks `sd_pid_get_session()`, gets the answer **ENXIO** and dies | ⭐⭐⭐ **total**: that call is made by **every** Wayland compositor, not by Mutter. It is the first thing to verify on a new desktop, and the symptom — *«it does not start and does not say why»* — is identical everywhere | `DECISIONI.md` §1.10-ter |
| ⛔ **The server must not run inside a user session**: `pam_systemd`, if the caller is already in a session, **does not create a second one and does not say so**. A server started by hand from `ssh` puts the children in the session of whoever started it | ⭐⭐⭐ **total**, and it is insidious because in production (system unit) it is never seen: it bites **only in testing**, that is where the new desktop is studied | `DECISIONI.md` §1.10-ter |
| ⛔ **Without a seat there are no `uaccess` ACLs** ⇒ the user **cannot open the GPU** and Mesa falls back to llvmpipe **without an error**. On a normal desktop access is given by logind with an ACL to whoever sits at the seat; we do not have the seat **on purpose** | ⭐⭐⭐ **total**, and it is the **price of headless**: it holds for any compositor run without a seat. ⚠ The symptom is «slow», not «broken» | `FASI.md` §05-la-sessione, `DECISIONI.md` §4.6-quinquies |
| ⛔ **With two cards, which one the compositor uses is decided by chance** if there is no udev rule | ⭐⭐ **total** — and on KWin it was already known (`STUDI.md` §kde §5.6: `findRenderDevice()` takes the first one that opens). ⇒ It was not a quirk of KDE: **it was the general rule, seen from one side only** | `DECISIONI.md` §4.6-ter and §4.6-quinquies |
| ⛔ **The `XDG_*` variables are not invented: `pam_systemd` sets them and they are read.** Composing them by hand means declaring a value instead of having it — and an asserted `XDG_RUNTIME_DIR` is the defect that does not show as long as the directory exists | ⭐⭐⭐ **total** | `DECISIONI.md` §1.10-ter |
| ⛔ **The tail of the burst**: the frame discarded «another one will arrive anyway» is **the last**, and after the last nothing arrives | ⭐⭐⭐ **total**: it is in `cattura.c`, which is **the same code for all four** desktops | §6.5 |

⭐ **And the consequence for method, which is worth more than the list**: when on a new desktop something does not
start or is slow, ⛔ **the first question is not «what is this compositor doing that is strange»** — it is
*«is the environment underneath the one the compositor expects?»*: session, seat, groups, card,
variables. `[M]` On GNOME, on the night of 15 Aug, the answer was **four times out of five
the environment** and once our code — and every time the symptom pointed elsewhere.

⚠ **And the reverse, for honesty**: what instead **is** GNOME's and does not carry over — `--headless
--no-x11`, the drop-in of the Shell's unit, `is_headless()`, the lockdown keys,
`always-show-log-out`, the twelve `switch-to-session-*` — must be looked for again on each desktop, and
for that the fifteen questions of section 3 are needed.

---

## 9-bis. ⛔⛔⭐ §1.18 — Four green benches that measured **the same path**

⛔ On 20 Aug four benches declared the clipboard green in both directions, on both
engines. On 21 Aug the user wrote: *«funziona l'incolla con ctrl+v, ma non con il mouse e
scegliendo dal menu la voce "incolla"»*. ⇒ All four pressed **`Ctrl+V`**.

⚠ They were not wrong benches: they were **four copies of the same bench**, with four different names.
The redundancy gave the impression of coverage and did not add a millimetre of it.

⭐ **The question that would have unmasked them in a minute**: *«what is the GESTURE that starts this
path, and is there more than one?»* For the clipboard the gestures are two — a key on the browser and a menu
item **inside the video** — and they are two paths **that never meet**: the first is born in the
browser, the second is born on the other side of the wire and comes back as a question from the server.

⇒ One bench per **entry path**, not one bench per function. And when a new bench turns
green at the first try, the right suspicion is not «well done us»: it is *«am I redoing a bench that already
exists?»*.

⚠ And the same day, on the same defect, **two defects of the bench would have declared broken a
healthy product**: Chrome attaching to the real graphical session instead of to the bench's screen
(`--ozone-platform=x11`), and a click given seconds before the measurement, when the browser's transient
activation had already expired. ⇒ §1.2 again, and it is no accident: the bench that discovers a
new path is **young**, and must be certified before believing it — in both directions.

## 9-ter. ⛔ §1.19 — **Whoever opens, closes**: the benches work on a person's desktop

*21 Aug 2026, from the user, looking at their screen: «Che diavolo succede? È come se si
aprissero terminali infiniti».*

⛔ It was the benches. A still desktop sends no frames, so to measure the video you need
something that moves: a scrolling terminal. ⚠ I turned it on **by hand** at every round, and nobody
turned it off — after ten rounds, **ten terminals and ten infinite loops on someone's desktop**.

⇒ The rule, and it holds for every bench that touches the test session:

| | |
|---|---|
| **whoever opens closes** | the scene is turned on by the bench and turned off by the bench, in a `finally` — even if the bench has fallen |
| **turn off what is SEEN, not only what runs** | ⛔ `pkill` on the process that was writing left standing the window that showed it |
| **the slot is freed** | the bench's session keeps the only slot busy, and the next bench would measure a page that could not connect |

⚠ And there is one more reason why this is not pedantry: the test session is **the same** one
the user looks at. A bench that leaves rubbish in there does not dirty a test environment — it dirties a
person's workplace, and makes them waste time figuring out what it was.

## 10. And one single lesson on everything else

The project never stopped on a hard problem.

It stopped, every time, on **a measurement that did not measure what we believed**: a green bench with
the defect alive, a counter that weighed nothing, a sample taken at startup, a scene that did not
move, a sender deduced instead of asked, a ceiling attributed to the compositor that was a
constant of ours.

The time spent certifying the instrument has always been less than the time spent chasing its
lies.

---

### 1.29 ⛔⛔⛔ **«Silence instead of red»: the form that NINE bench defects out of nine have**

*23-24 Aug 2026, phase 9. In two days nine defects were found in the benches. ⛔ **Not one
of them made a bench fail**: all nine made it **keep quiet, or give green**, and none
would ever have drawn attention by itself.*

| where | what |
|---|---|
| `07-b64` | `a_non_si_apre` looked at `ricevuti == 0` — but the client prints *«ricevuti 0»* **also from the `except` branch** ⇒ **every** way of failing gave **green** |
| `07-b64` | the first profile of the grid **disarmed the guardian** ⇒ the eight after it ran without a safety net |
| `07-b64` | `spediti_dal_server` at `None`: `None == 0` is **false** ⇒ green on a round in which the server's end had not been read |
| ⛔ `07-b64` | the «final count» line arrives **up to 29 s late** when the pacer has a queue ⇒ the next round reads **the count of the round before**. `[M]` Three profiles in a row reported **exactly the same numbers**, and a predicate gave **red on someone else's denominator** |
| `09-b70` | `sudo -S` covers only the **first** link of the chain ⇒ the trace reader **was not written** |
| ⛔ `09-b70` | a trailing `< file` **steals stdin from `sudo -S`** ⇒ the function returns **0 silently**, and the counter becomes **cumulative since power-on**: `[M]` 4 041 instead of 1 604 |
| `09-b70` | a file not sent by the terrain ⇒ empty journal ⇒ **red on a session alive for 797 frames** |
| `09-b76` | the predicate measured **the duration of the delivery** and called it **«stacco»** |
| `09-b84` | the line of the **off** state contained the word `ACCESA` (in *«dal 24 agosto nasce ACCESA»*) ⇒ the bench would have read **on for an arm that was off**, and that predicate was **the only belt** |

⭐⭐ **The rule that comes out of it, and it is not «write better benches»:**

> ⛔ **A bench is not finished until it has been seen giving RED.** Every predicate must have, in
> `--certifica`, the case that makes it fail — and that case must be **run**, not imagined.

And three corollaries, each one paid for:

1. ⛔ **`None` is not zero, and «I did not read» is not «nothing happened».** Half of the nine are born
   from this confusion. A function that could not measure must return **`None`** and the bench
   must **refuse to judge**, never carry straight on with a zero;
2. ⛔ **The guard goes where the number IS CONSUMED**, not where it is produced: if another bench replaces
   your function with its own, the guard put inside yours **no longer runs**;
3. ⭐ **Searching for a word inside a text is fragile**: `"ACCESA" in dettaglio` is true even when the
   detail explains that it is *born* on **and is off**. Anchor to the **state sentences**, not to the
   words.

### 1.30 ⛔⛔⭐ **A test that does not bite gives a judgement that looks like a result** — and it is unmasked by counting

*24 Aug 2026, phase 9. Three tests in a row produced a user judgement **valid as a
sentence and empty as a measurement**, and none of the three declared it.*

| the test | the judgement | ⛔ why it was not valid |
|---|---|---|
| 1 % loss, real desktop | *«mi sembra ok»* | `[M]` its frames weighed **242-283 bytes**: the loss **had nothing to break** |
| dragging a window | — | `[M]` peak **3 801 bytes**, against the **25 000** at which the bench collapsed |
| 5 % loss | *«è tutto fluido»* | `[M]` **221 packets, 18 thrown away** had passed inside the fault. **Eighteen packets are not a test** |

⭐ **The remedy is trivial and must be put BEFORE asking for the judgement**: count **how much
stress really arrived**. Here: the packets passed through `netem` and the bytes per frame.
`[M]` Redone with thirty seconds of continuous movement, the same test gave **7 596 packets,
423 thrown away, frames up to 77 KB** — and then the *«è tutto fluido»* became a result.

⛔⛔ **And the corollary that is worth more than the lesson**: the step is not decided by **the fault**, it is decided by
**how much the scene asks**. A bench that demands 40 frames/s of continuous change and a
real desktop that changes in jolts **are not the same stress**, and `[M]` between the two there is **an
order of magnitude**: the bench put the collapse at 0.9 % loss, the user found it between
5 and 10 %.

### 1.31 ⭐⭐⭐ **The defect does not begin where it shows — and the column that warns is not the one being looked at**

*24 Aug 2026, phase 9.* `[M]` The keyframe spiral starts between **0.00 % and 0.10 %** loss
— that is **at the first lost packet** — while the frames per second stay good up to
**0.53-0.75 %**.

⇒ ⛔ **A bench that looked only at frames per second would have given green up to 0.5 %**, with
the product meanwhile degenerating into keyframes only — that is degrading **in space and in time
together**, which the specification forbids.

⭐ **The rule**: when a phenomenon is measured with a **mechanism** and a **symptom**, bring the
mechanism's column **beside** the symptom's, always. The symptom says when the user
notices; **the mechanism says when it began**, and between the two here there is a factor of **five**.

### 1.32 ⭐⭐⭐ **«Sometimes it happens» often means «it always happens, it is just waiting for the moment»**

*24 Aug 2026, phase 9.* A phenomenon appeared **bistable**: same input, same binary, same
terrain, and twenty minutes apart **`0 chiavi · 40,16/s`** or **`24 chiavi · 33,84/s`**.

⛔ **Looking for its cause in the first ten seconds gave 43 negative tests out of 43** — and the reason was
that **5 triggers out of 13 fell after the tenth second**: in that window there was nothing to
find.

⭐⭐ **The right form was a different one**: not two branches, but **a one-way trigger with constant
risk**. `[M]` Tested at two durations — at **10 s** it happens in **35 %** of rounds (expected 31 %), at
**50 s** in **90 %** (expected 92 %) — with λ = **0.053 per second** and median **13 s**.

> ⛔⛔ **And the count that follows touches every measurement**: the benches run **twenty-five seconds**, the
> user's sessions last **hours**. ⇒ Every number taken near the edge **underestimates**, and not by
> a little: what at the bench seems *«sometimes»*, in a real session is **certain**.

⭐ **The test that tells the two readings apart costs an hour**: repeat the same cell at **two
durations** and look at whether the fraction follows the exposure. If it follows it, «bistable» is the wrong
word — and with it every conclusion drawn from short rounds.

### 1.33 ⛔⛔ **The yardstick must be calibrated FIRST, and the two errors do not cost the same**

*24 Aug 2026, phase 9. Two measurements of the same day, and the difference between them is all here.*

⭐ **The one that went well**: before measuring the audio-video offset, **seven known delays were injected**
and it was verified that the method found them again — on the file, then resampled, then ⭐ **through the
real product**. `[M]` Slope **0.9988**, constant **−11.6 ms**. ⇒ From that moment every number
had a declared error, and the measurement was able to **disprove** the previous reading.

⛔ **The one that went badly**: a threshold chosen on a quantity **never put to the test on the extreme
cases**. `[M]` `pkt_lost/pkt_sent` ordered the two cases **the wrong way round** — a line that **holds**
declared **512‰** against the **123‰** of one that **does not hold**, because ngtcp2 counts an
**overtaken** packet as lost. ⇒ **No threshold could separate them**: it was not a calibration to
redo, it was the wrong quantity.

⭐⭐ **And the rule on asymmetry, which is the transferable part:**

> ⛔ When a threshold decides something **irreversible** — closing a session, throwing
> someone out — **the two errors do not cost the same**. Erring on the cautious side costs a few seconds
> more; erring on the other **throws out whoever was working**. ⇒ The threshold is put **above** the
> centre between the two measured extremes, and the margin is written **on both sides**.

⚠ And the margin is anchored to the **worst case that holds**, not to the most convenient: `[M]` the narrow side was
taken on the **shorter** of the two stalls observed, because a margin written on the
lucky number is not a margin.


---

### 1.34 ⭐⭐⭐ **A quantity that saturates stops informing — and then you look at the DEMAND, not the supply**

*24 Aug 2026, phase 10.*

⛔ The card's video engine was measured at **99.5 %** in all three collapses. ⇒ The
column said *«full»* — ⛔ **and from then on it said nothing more**: full at the first collapse and
full at the third, with **three different loads** and three different ceilings behind them.

⭐⭐ **The cure is to change the end of the measurement**: not *«how busy is the engine»* — which stops at
a hundred — but ⭐ **how many pixels per second were ASKED of it**. That quantity **does not saturate**, and
it goes on ordering the cases even beyond the point at which the other one flattened.

`[M]` **With demand in place of supply the three collapses lined up within 0.6 %**
(1855.9 · 1865.8 Mpixel/s at two different resolutions), where the frames per second differed by
**74.9 %**. ⇒ ⭐ **The right currency makes comparable scenes that seemed incomparable.**

> ⚠ **And the trap right beside it**: a saturated column invites you to **extrapolate the straight line** from the
> light-load points. ⛔ That line **does not pass through the collapse**: in the same phase
> the extrapolation gave **~46 sessions** where the measured value gave **11**, that is **four times
> off**. A number extrapolated beyond the last measured point **is not reported**.

⭐ The general form: **when a witness hits its maximum, it is no longer a witness.**
Look for one that does not have that maximum.

---

### 1.35 ⛔⛔⭐ **A DEDUCED defect can get the mechanism right and the consequence wrong**

*24 Aug 2026, phase 10. And it is a lesson on the way of writing findings, not on the defect.*

⭐ **The mechanism was right**: a guardian called **inside** the loop that delivers the frames
narrows the frontier **as 1/N**, and with N tenants it eats the 300 ms the code allows itself.
Deduced by reading the code, ⭐ and **confirmed by measurement**.

⛔ **The consequence was wrong.** The finding said *«and so the tenants get evicted»*.
`[M]` **It is not the ordinary outcome**: the ordinary outcome is that **every desktop collapses to 1.3 fr/s and not
a single log line is written** — that is ⛔ **a silent degradation**, which is **worse** than an eviction,
because the eviction at least leaves a trace.

> ⭐⭐ **The rule**: a finding deduced from the code has **two halves** — *«how it happens»* and *«what is
> seen»*. ⛔ **The first can be deduced; the second cannot.** It must be measured, or declared `[?]`.
>
> ⚠ And when the deduced consequence is **more conspicuous** than the real one, the real defect risks
> going unnoticed: you go looking for the eviction, you do not find it, and you file the finding — ⛔
> **while the silent degradation is still there**.

---

### 1.36 ⛔⛔⛔ **The layer that coordinates the benches is a bench too — and nobody certifies it**

*24-25 Aug 2026, phase 10. `[M]` **Six defects**, all in the layer that runs the benches, not
in the benches.*

⭐ The project certifies the benches with `--certifica`: a known fault is injected and it is verified that the
bench sees it. ⛔ **But the GPU lock, the terrain, the scripts that start the server and the
module they share do NOT have a `--certifica`** — and they are **the floor on which every
measurement rests**.

`[M]` **What it cost, concretely:**

| | |
|---|---|
| **146 benches without the execute bit** | an `exec "$0"` on a non-executable file killed a campaign **after** it had won the GPU lock: ⛔ **an hour lost**, and the lock held for nothing |
| **the terrain said «on» looking at the PID** | ⛔ a server with the process alive and **nobody listening on the port** passed for on. Now «on» means **someone is listening** |
| **the terrain rewrote the password** of a user that already existed | ⛔ and killed the sessions of another bench in parallel |
| ⛔⛔ **the global `pkill`** inside two benches | on a machine with benches in parallel, one **kills the work of the others** |
| **the expired lock was forced without looking** | now it **compares before deleting**: `[M]` expired ⇒ forces it; changed underneath ⇒ ⭐ **does NOT force it, and the fresh one survives** |

> ⭐⭐ **The rule**: *everything a measurement depends on is something to certify* — and **the fact
> that it produces no numbers does not exempt it**. A lock forced the wrong way and a bench that
> counts badly produce **the same damage**: a number nobody knows is false.

⚠ **And the warning light to recognise**: when a fault hits **different benches in the same way**, it does not
belong to the benches. It belongs to what is underneath.

---

### 1.37 ⛔⛔⛔⭐ **A test that cannot be LOOKED AT is worth zero — and calling someone to judge it is worse than not testing**

*25 Aug 2026, phase 10. ⛔ It is the most expensive lesson of the phase, and it was not taught by a measurement:
it was taught by **the director, out of patience**.*

⛔ The product was built, stitched together, measured on **eleven real desktops**, and the numbers were
good. ⇒ The director was asked to look. ⛔ **And the browser, inside the remote desktop, did not
open.** Three times, until he stopped:

> *«Io non faccio più niente, Firefox continua a non funzionare e io non posso fare test in queste
> condizioni.»* · *«Senza Firefox nessun test di rilievo ha senso, quindi non chiamarmi se non
> funziona.»*

⛔⛔ **And the serious part is not that the browser did not work: it is that nobody knew.** **Four paths**
were tried to see the image of that desktop — the internal snapshot, the photograph
of the screen, the canvas read by the page, the count of frames — and ⛔ **none gave the
picture**. ⇒ The scene was declared ready **without anyone having looked at it**.

> ⭐⭐⭐ **The rule, in one line: the scene is prepared and LOOKED AT before calling whoever must
> judge it.**
>
> ⛔ And the counter **does not count as looking**. *«493 frames have passed»* and *«a
> desktop with an open browser can be seen»* are **two different statements**, and the first does not imply the
> second: 493 black frames are 493 frames.

⚠ **And there is a cost that is not technical.** Whoever judges has a finite patience, ⛔ **and every empty
call consumes a piece of it**. The user's judgement is invariant **I8**, that is the ultimate yardstick of the
product: ⇒ ⭐ **wasting it is wasting the only instrument that cannot be rebuilt.**

⭐ **The remedy is a piece of equipment, not an intention**: a witness that pulls down
**the image** of what the user would see, ⛔ **calibrated like every other yardstick** (§1.33) — with the
recognisable mark it must find again, and the negative control that must say *«black»* when it is
black. ⇒ And ⛔ **if it could not look it must return «I don't know», never an empty image**: *«I did not
look»* is not *«it is black»*.

---

### 1.38 ⛔⛔⛔⭐ **A check that SHARES the factor it must exclude checks nothing**

*25 Aug 2026, phase 10 — and it refutes a conclusion of phase 9 that carried a ✅.*

⛔ **The wrong conclusion**: *«Firefox is broken on this machine for everyone, inside and outside
REMOTIX. It is not a defect of the product.»* Closed, ticked, and repeated twice in `README.md`.

⭐ **And the check that seemed to close it was one of the good ones**: **everything** was removed — no
REMOTIX session, no Wayland, no monitor — and the browser was launched **from another user**.
It failed the same way. ⇒ *«So it is not the session.»*

⛔⛔ **And instead the two sides shared the cause.** `~/.cache` is a link to `/tmp` for
**all** the users of that machine, the check's user included; and the browser profile
lives under `~/.cache/mozilla`, that is **`/tmp/mozilla`** — ⛔ **a single folder, which the first to arrive
had taken with mode `0700` two days earlier.**

> ⚠ **And a clarification that does not change the lesson, but changes whose fault it is** *(25 Aug 2026,
> corrected by the user)*: ⛔ **that link is not a fault** — *«`.cache` che punta a `/tmp` è
> una mia scelta voluta»*, and it is a decision about **their** operating system. ⇒ The shared factor
> was a **legitimate configuration**, not a defect — ⭐ and this makes the lesson **stronger**,
> not weaker: *the factor a check shares has no need whatsoever to look like a
> fault in order to ruin it.* The defect is **ours**: it is we who create ten users who all end up
> in the same folder (`DECISIONI.md` §4.6-undecies).

⇒ ⭐ **The check showed the same fault for the SAME reason, not for a different reason.**

| | phase 9 | ⭐ after removing that single factor |
|---|---|---|
| the headless browser, from the check's user | ⛔ **hangs, killed at 60 s, empty profile** | ⭐ **`rc=0`**, and a **5.5 MB** snapshot |

> ### ⭐⭐ The rule, and it is not «do more checks»
>
> ⛔ **Before trusting a check, name the factor it must exclude and verify that the
> check does NOT have it.** A check is chosen for what it does **not** have in common with the case — and
> that *«not»* must be **looked at**, not taken for granted because the environment is different.
>
> ⚠ **The warning light**: a check that *«fails the same way»* is **suspicious**, not reassuring. If removing
> everything does not change the symptom by a millimetre, the simplest explanation is not *«the cause is
> elsewhere»*: it is ⛔ **«there is something I did not remove»**.

⭐ **And what the project had already written right**, at the end of the same section and ignored:
*«the defect is there, the diagnosis is not»*. ⇒ ⛔ **That sentence and a ✅ cannot stand in the same
section**: if the diagnosis is not there, the section is not closed.

⚠ And the cost, to be honest all the way: that conclusion kept the director **two phases**
in front of a browser that would not start, with the explanation *«it is not ours»* — which is the explanation that
⛔ **does not ask to keep looking**.

---

### 1.39 ⛔⛔⛔⭐ **One always starts again from the same point, and that point was already fine**

*25 Aug 2026, phase 10. ⛔ It is the most costly method error of the project so far, and it was not
discovered by measuring: it was discovered because the director asked for a test that **forced
starting from zero**.*

⛔ **The defect**: on a remote session **just born**, the compositor announces no
monitor ⇒ **no application can open a window**. It stayed invisible for days.

⭐⭐ **And it was not subtle.** It was invisible for one reason only:

> ⛔ **All the tests — those of the product and those of the benches — reused sessions ALREADY OPEN**, which
> had the monitor. The piece of scene that broke **was never crossed**.

#### ⛔ And the defect has a form that repeats — three times in the same phase

| | hidden for | ⛔ why |
|---|---|---|
| the session without a monitor | days | ⛔ one started again from a session already alive |
| the browser that is not born for the users after the first ⚠ *(the shared `~/.cache` is a **choice** of the user's, not a fault)* | **two phases** | ⛔ and **the check that «closed the question» was in the same condition** (§1.38) |
| five benches that counted zero frames | one round | ⛔ a cure to the log had broken their expressions |

⇒ ⭐⭐⭐ **All three are the same error seen from three sides**: you look **always at the same piece of
scene**, and you look at **the process instead of the pixel**.

> ### ⭐⭐ The two rules, and they are short
>
> 1. ⛔ **At least one test must start from ZERO**: clean machine, new user, new session — and
>    end with **an image**. A test that reuses a state that worked **cannot find a
>    defect of birth**, by construction.
> 2. ⛔ **Do not count the process: look at the pixel.** `[M]` The process count said **1** both
>    with the window and without — ⭐ **window or no window, the same number.**

⚠ **And the countermeasure is not «more tests».** There were already more than a hundred, ⛔ **and the three defects
passed right through them.** The problem is not quantity: it is **where they start from** and **what they
look at**. ⇒ That is why the user decided on a dedicated phase — `DECISIONI.md` §4.6-duodecies,
the **safety net** — before the new desktops.

---

### 1.40 ⚠⭐ **`bash -n` passes on a script that does not do what it seems**

*25 Aug 2026, and it costs something to declare it because it happened while building the bench.*

```bash
U=${1:?serve l'utente}      # ⛔ the apostrophe OPENS a quote…
PROFILO=${2:?serve il profilo}   # …and this line ends up INSIDE the string
```

`[M]` The apostrophe of *«l'utente»* swallowed **four lines**, up to the next `'` — which was
in a comment (`E'`). ⇒ `PROFILO=` **was never executed**, and the script died much further
on with *«PROFILO: unbound variable»* on a line that had nothing to do with it.

⛔⛔ **And `bash -n` passed.** The syntax **was** valid: it just did not mean what it seemed.

> ⭐ **The rule**: `bash -n` says *«it can be read»*, not *«it does what you believe»*. ⇒ A syntax
> check **is not a test**, and a new script must be **run** at least once before
> trusting it. ⚠ And inside `${…:?…}` and double-quoted strings, **no apostrophes**: this
> project already writes `e'` and `puo'` in comments, ⛔ and in there that convention is **mandatory**,
> not stylistic.

> ### ⛔ AND ON 26 AUG 2026 IT HAPPENED AGAIN — *twenty-four hours later, in the same project*
>
> `[M]` An apostrophe inside a **comment** in a `sh -c '…'` block closed the string halfway, and
> the shell ran the remaining pieces as commands: `MANCA: unbound variable`, `grep: dentro: No
> such file or directory`, `sed: invalid option -- '8'`. ⛔ **`bash -n` passed this time too.**
>
> ⇒ ⭐⭐ **The cure is not remembering it**: comments are written **outside** the quoted block. Inside a
> `sh -c '…'` there is no room for prose — only commands.

---

### 1.41 ⛔⛔⭐ **The reverse of «silence instead of red»: RED INSTEAD OF NOTHING**

*26 Aug 2026, phase 11, first round of the bench that validates the environment.*

⛔ §1.29 says that nine bench defects out of nine had the form *«silence instead of red»*.
⭐ **This one has the opposite form, and costs the same.**

`[M]` The bench had eight checks. The **fourth** closes the user's session to see whether the
children really die — and by closing it, it also takes away the session's private folder.
⇒ ⛔ **Checks 5, 6 and 7, which come after, found the field cleared and gave THREE FALSE
REDS**: *«the folder is not there»*, *«the channel is not there»*, *«the compositor does not start»*.

The verdict said **«THE BOX DOES NOT HOLD»**, and the box held perfectly well.

> ### ⭐⭐ Why it is as serious as silence
>
> ⛔ **A net that gives empty reds gets switched off by whoever is working** — and then there is no
> net any more. ⇒ The damage is not the wrong red: it is that **the next red, the real one, nobody
> will look at.**
>
> ⭐ **The rule**: *whoever tests the closing has the duty to REOPEN, and to verify that the
> reopening succeeded before letting the others judge.* ⚠ And if it does not manage, the outcome is not
> red: it is **«I don't know»**, and it stops there.

⚠ **And the younger brother, the same night**: a check judged while the piece it was
measuring was still `activating`. ⇒ It said *«does not hold»* where the truth was *«I had not yet
asked anything»*. ⭐ **Prepare** as the product does, wait for the event, **then** judge —
and ⛔ **preparing is not cheating: cheating would be skipping the check.**

---

### 1.42 ⛔⛔⛔ **Same name, same apparent version, DIFFERENT THING — and the symptom comes out on the wrong side**

*26 Aug 2026, phase 11, putting the product inside the box.*

`[M]` The binary copied was **the right one**, verified with the fingerprint. The libraries were
taken from the machine's `/lib`: `libngtcp2.so.16`. ⛔ **But the real server does not use that one**: it uses
the one built separately, and the two are **16.2.9** against **16.11.0** — *same file name, same
format version number, two different programs*.

| | |
|---|---|
| the server | ⭐ **started**: certificates generated, startup lines complete, port listening |
| ⛔ at the **first client** | it died with `ngtcp2_settingslen_version: Unreachable` |
| ⛔⛔ and the client | saw only **«Idle timeout»** |

> ### ⛔⛔ The two teachings, and the second is worth more than the first
>
> 1. **A fingerprint of the binary is not enough**: two machines with the same binary and different libraries
>    are two different machines. ⇒ Alignment is verified **on the binary AND on what lies
>    beneath it**.
> 2. ⭐⭐ **The symptom came out on the wrong side.** Whoever looked at the client saw *«the network does not
>    answer»* — a diagnosis that sends you looking in the wrong place for hours. The real line was
>    in the **server's** log, and it was reached only because someone went to read it.
>    ⇒ It is `CODER.md` §3.8 in reverse: *verify from the side that must receive*, ⛔ **but when
>    something does not arrive, go and read the side that sends.**

⚠ **And the same family, twice more in the same night**: two pieces worked because
someone else dragged them along, and they disappeared as soon as the recipe changed. ⇒ ⭐ **What is needed
is declared; what arrives by chance, by chance goes away.**

---

### 1.43 ⛔⛔ **An environment that FALLS BACK SILENTLY produces worse numbers and no red**

*26 Aug 2026, phase 11, first start of the box.*

`[M]` The graphics card node entered the container with the host's group **number**,
⛔ but inside, that number belonged to **another group**. The tenant was left out, and the
compositor wrote two lines nobody was reading:

```
libEGL warning: failed to open /dev/dri/renderD128: Permission denied
libmutter-Message: Created surfaceless renderer without GPU
```

⇒ ⛔⛔ **A bench that measures SOFTWARE encoding believing it is measuring the hardware.** No error,
no red: **only worse numbers**, which someone would have attributed to the desktop or to the new code.

> ⭐ **The rule** — it is `CODER.md` §3.9 applied to the **environment** instead of to a component:
> *ask for the piece by name, and verify that it obeyed.* ⇒ Here: after starting the box,
> **reread from the node** that the tenant really is in the card's group, and if it is not, **say so**.
>
> ⚠ And the cure does not nail the number down: it **reads** it from the node and aligns to it, declaring it. ⛔ A
> nailed-down number would have made something that works on this machine and **keeps quiet** on another.


---

### 1.44 ⛔⛔⛔ **The predicate that could not give red, and looked like one that passes**

*26 Aug 2026, phase 11, first draft of C8.*

The defect to catch: ten tenants with `~/.cache` all pointing to the same place, and the
browser that from the **second** onwards no longer makes its profile. The predicate written to verify it —
and written **well**, according to rule E1 *«don't look at the link, try to WRITE»* —
was:

```
mkdir -p ~/.cache/.prova && rmdir ~/.cache/.prova
```

⛔ **It could never fail.** With the link, `~/.cache` **is `/tmp`**, and `/tmp` is writable by
anyone (mode `1777`). ⇒ The predicate said **«can write: yes»** even for the tenant whose
browser could not open it.

⭐ **The place that bites was one level further down**: `~/.cache/**mozilla**`, which the **first** tenant
takes with mode `0700`. And it was already written, with its measurement, inside `src/provisiona.sh`: *«from
`provanic3`, `mkdir -p ~/.cache/mozilla` → Permission denied»*.

> ### ⛔ The rule, and it holds beyond this case
>
> **Applying E1 is not enough: it must be applied IN THE PLACE THAT BITES.** A predicate that tests the right
> thing one level too high ⛔ **looks exactly like a predicate that passes** —
> and it is worse than not having it, because it reassures.
>
> ⇒ ⭐ **The counter-test that would have caught it in ten seconds**: run the predicate **with the fault
> injected** and demand that it gives red. It is the same thing this phase asks of every mesh
> (`--certifica`), ⛔ and it holds for the single predicate inside a mesh too, not only for the mesh.

---

### 1.45 ⛔⛔ **The ceiling of one test lent to another — and the red that no longer distinguishes anything**

*26 Aug 2026, phase 11, first real round of C8.*

C8 does two things with very different times: **waiting for a page to appear on an already running desktop**
(~25 s) and **starting Firefox for the first time in a cold box** (which creates the profile, and
well exceeds the 25 s). ⛔ The first draft used **the same ceiling** for both.

`[M]` Outcome: **red for both tenants, with the cure and without.**

⇒ ⛔⛔ **And the real damage is not the false red: it is that the ACCEPTANCE TEST stops being valid.** The meaning of
`--senza-cura` is *«with the fault injected it must turn red»*; ⚠ if it is red **even without**, that
comparison no longer proves anything, and a mesh that cannot tell the fault from its own ceiling
⛔ **is indistinguishable from a broken mesh**.

> ⭐ **The rule**: every wait has **its own name** and **its own value**, and the value is justified by
> what is being waited for. ⛔ Reusing a ceiling because «it is there and more or less fine» is the same
> form of error as reusing a number measured in another condition.
>
> ⚠ And the signal that should have raised suspicion at once: **all red**. A fault that hits
> *«from the second onwards»* and instead hits **the first too** is not that fault — ⇒ and now it is
> C8 itself that says so, instead of leaving it to be deduced.

---

### 1.46 ⛔⛔⛔ **The bench that did not run at all — and said «succeeded»**

*26 Aug 2026, phase 11.*

A command nested **three times** — `ssh` → `systemd-run … /bin/bash -c "…"` → `podman exec … sh -c
"cd … && python3 …"` — lost its quotes along the way. ⛔ **It ran nothing**, it
printed nothing, and it returned **`0`**.

⇒ ⛔⛔ **A green with no measurement underneath**, and which from the side of whoever reads the log has
**exactly the same look** as a successful round. ⚠ It is the worse reverse of §1.41: there the bench
shouted red without having looked; here it **keeps quiet and says yes**.

> ### ⭐ The two rules, and the second is worth more than the first
>
> 1. ⛔ **No shells in between**: the program is called **by absolute path**, without `sh -c`
>    inside `podman exec` inside `systemd-run` inside `ssh`. Every level of quotes is a place
>    where the command can vanish.
> 2. ⭐⭐ **A bench that produced NO line is not «succeeded»**: whoever launches it must
>    demand to see the header and the final count, ⛔ and treat silence as *«I did not
>    look»* (outcome 3) — never as green. `LEZIONI.md` §1.30 says it for the stress; here
>    it holds for the bench itself.

### 1.47 ⛔⛔ **A comparison between values nobody can give is GREEN, and has looked at nothing**

*26 Aug 2026, phase 11, first draft of C11.*

C11 compares thirteen things across the four boxes and says *«they are aligned»* if every item has the
**same value** everywhere. ⛔ Three items asked for packages with the wrong name —
`libssl3` and `libpipewire-0.3-0`, which in Debian 13 are called `libssl3t64` and
`libpipewire-0.3-0t64`. ⇒ All four boxes answered **`?`**.

⭐⭐ **And `?` equal to `?` is equal.** The three items **passed the comparison**, and passed every time,
forever. ⛔ Three checks out of thirteen were looking at nothing, and the green said
*«aligned»* with the same face as when it really looked.

> ### ⭐ The rule
>
> ⛔ **A comparison needs at least one party able to answer.** An item **nobody** answers
> is not «equal for all»: it is **mute**, and it must be stated separately.
>
> ⇒ C11 now counts them and **prints** them: *«N items no box can answer — and a mute
> item passes the comparison without having looked at anything»*.
>
> ⚠ **It is the same form of error as §1.44** (the predicate that could not fail) seen from another
> side: there the predicate always said yes, here the comparison always says equal. ⭐ In both
> cases the signal is the same — **a check that has never given red in its life must be looked in the
> face**, not celebrated.

### 1.48 ⛔⛔ **The options loop swallowed the argument — and the message said «succeeded»**

*26 Aug 2026, phase 11, the hook.*

`11-gancio.sh installa pre-commit` ⛔ **installed `pre-push`**, and calmly printed that it had
gone well. The loop that reads the options consumed the argument and passed it to nobody; the
confirmation message repeated **what had been asked**, not what had been done.

⇒ ⭐⭐ **And this is the rule, and it is wider than the bug**: a success message that repeats
the intention **is not a verification, it is an echo**. `CODER.md` §3.9 says *ask for the piece by name, and
verify that it obeyed*: here the piece was yourself.

> ⛔ **The confirmation message is built by REREADING the result**, not by copying the request.
> «Installed in `<percorso letto adesso dal disco>`», not «installed `<quello che mi hai chiesto>`».
>
> ⚠ It is the same family as §1.46 — there the command had not been run at all and the exit code
> said `0`; here it was run **on a different target** and the message said yes. ⇒ In both
> cases the defect lies in the **point where it is reported**, not in the point where it is done.

---

### 1.49 ⛔ **A red that cannot be made green is worse than no mesh at all**

*26 Aug 2026, phase 11, C12.*

C12 checks that the hook is installed, and to find it used `git --git-path`. ⛔ That command
returns a path **relative to the folder given to `-C`**, not to the root of the repository. ⇒ The mesh
looked for the hook in a place that does not exist, and would have said **«not installed» forever**, even
right after installing it.

⭐ **A perpetual red is not caution: it is noise.** And noise, in a safety net, always ends
the same way — §1.3 of the phase document: *«a net that gives empty reds gets switched off by
whoever is working»*.

> ### ⭐ How it is caught, and it costs ten seconds
>
> ⛔ **Try to make the mesh turn GREEN.** A check must be switched on in both directions: you
> inject the fault and demand red (which the project already does, `--certifica`), ⚠ **and you remove
> the fault and demand green**. The second half is forgotten, and it is the one that catches this.

---

### 1.50 ⛔⛔ **The ceiling governed the EXIT, not the work — and the comment described something else**

*26 Aug 2026, phase 11 — found by the bench of C14, not by the one the defect belonged to.*

C8 has the browser take a photograph with a time ceiling, and the comment beside it said it
was needed because *«the first start in a cold box does not fit inside it»*.

`[M]` With the ceiling set to **one second**: Firefox is killed, exits with **124**, ⛔ **and the PNG is there all the
same, 30 135 bytes.** ⇒ It writes the image and **then** lingers on closing: that ceiling did not limit the
snapshot, it limited **the browser's leave-taking**.

⭐⭐ **And the judgement survived for the right reason, which is worth isolating:**

> ### ⛔ Judge the RESULT, not the exit code.
>
> C8 looks at **the file**, not at how the program died — *a browser that has drawn has drawn,
> even if it was then killed while taking its leave*. ⚠ A mesh that had believed the `124`
> would have given red on a **completed** job.

⚠ **And the thing to correct was not the code: it was the comment.** A comment that describes a
quantity different from the one the code governs ⛔ is a trap for whoever comes later to calibrate that
number — and calibrating in the dark is exactly how a day is lost.

⭐ **And that ANOTHER bench found it is the most important fact of all**: none of the four
false reds of §1.44–1.47 had noticed this, because they all looked at C8 **from inside**.

---

### 1.51 ⛔⛔ **«Text file busy» — the red that comes from the ORDER of the commands, not from the product**

`[M]` 26 Aug 2026, stitching the four new meshes into the net. The action `11-accendi.sh prodotto`
copies the binary into the box. With the **server running**, `cp` answers:

```
cp: cannot create regular file '/opt/remotix/remotix': Text file busy
  NO  non sono riuscito a mettere il prodotto dentro
```

⇒ The action failed **entirely** on all four boxes, and the message that remained was
*«non sono riuscito a mettere il prodotto dentro»* — which looks exactly like a fault of the
product or of the box, while it is ⛔ **a fault of the order in which the commands are given**.

> ⭐ **The form of error**: a bench that fails for a reason of its own and leaves a message that
> accuses what it is testing. It is the same family as §1.46 and §1.48 — only here the outcome is a
> red instead of a green, and for that reason it is **less** poisonous: at least it shows.

⛔ **And the first cure was worse than the disease.** The obvious idea — stopping the server before copying — was
tried and **measured**: `systemctl stop rete11-server` inside the box **does not return** (over
two minutes, then the command was killed from outside). ⇒ The action no longer failed: **it hung**, which
is the worse form, because a hung bench says nothing to anyone.

⭐ **The right cure was of another nature, and the operating system states it**: *overwriting* an
executable in use is forbidden, **removing** an executable in use is allowed. ⇒ `rm -f` and then `cp`. The
old server keeps running with its inode until the next `11-accendi.sh server`, and it is
declared in the file instead of discovered by someone six months from now.

> ⚠ **The general lesson**: when a bench fails, the first question is not *«what is wrong with the
> product»* but ⭐ *«could this command succeed, in the state in which I left the machine?»*.

---

### 1.52 ⛔⛔⛔ **The mesh with the injected fault exited with the raw verdict — and precisely in the red round it would have written «the fault was NOT seen»**

`[M]` 26 Aug 2026, first round of the wiring of the four new meshes. `11-gancio.sh` reads an
injected mesh **the other way round**: it exits `0` when the fault **was seen**, and what ends up
in the log is not the raw outcome but the fact — `ha_visto_il_guasto`. It is from there that C13 can tell whether the
net is still capable of giving red.

⛔ **C9 exited with the raw verdict** (`1`, that is red). ⇒ In the round with the injected fault the hook
would have written `ha_visto_il_guasto: false` **precisely when the fault had been seen perfectly well**, and
C13 would have started saying *«the net can no longer give red»* while it could.

> ⭐ **And no certification caught it, of either of the two meshes.** The certification of
> C9 tested **the judge** (16 cases out of 16, all right); that of C13 tested **the reading of the
> log**. ⛔ The defect lay in the **joint** between the two: in the exit code, which belongs to
> neither of the two jobs. ⇒ It was seen only **by running the real wiring**, and it is the same
> family as §1.46 and §1.40: `bash -n` passes, the certification passes, and the thing does not work.

⭐⭐ **And the cure was not inverting the outcome — that would have been the second trap.** C9 today is
red **even without a fault** (the two lines of `src/tastiera.c`, ⇒ `DECISIONI.md` §4.6-duoetvicies). A
simple *«red ⇒ seen»* would have said «the fault was seen» **even if the injection had
done nothing**: a predicate that cannot fail, that is §1.44 again, and this time holding up the
certification of the whole net.

⇒ **Two** things are demanded together: the verdict is red, **and** the nameless lines are more than
those the real defect had left. `[M]` without a fault: 4 · with the `tutto` fault: 5 490.

> ⛔ **The rule**: when a mesh carries with it a **real and already known** defect, its injected
> fault is not measured on the colour of the verdict — it is measured on the **difference** the injection
> produced. Otherwise the net certifies itself on a fault of the product instead of on its own.

---

### 1.53 ⛔⛔⛔ **A red that could not turn green blocked five tests and postponed a phase**

`[M]` 27 Aug 2026. Mesh C1 — *«the session is born and can be seen»* — said **ten blind sessions out of
ten**. On that verdict rested: five tests of the net declared «blocked» (C2, C3, C4, C6,
C8b), the postponement of phase 12, a defect open in phase 10, and a work list.

⛔ **C1 read the wrong line.** `sessione [chi] ⛔ ZERO MONITOR` is written by the product **in the
mandatory passage of a SUCCESSFUL birth** (`src/sessione.c:345-348`): since 14 Aug *«zero
monitors of its own»* is **the intended state** — the monitor is mounted by **capture**, afterwards.
⛔ And the green branch was **unreachable**: `sessione_stato()` is no longer called after the
stage is taken, so `monitor N/N: connettore` **never** appears in a healthy birth.

> ⇒ ⭐⭐ **C1 could only say «BLIND» or «I don't know». It never said green, and it could not.**
> `[M]` The counter-test, on the cured box: `formato negoziato` appears **8** times, the stage says
> `monitor «Meta-0» (0 prima, **1** dopo) 1920x1080`, `monitor …: connettore` appears **0** times —
> **and C1 still said BLIND**.

⛔⛔ **And the certification did not catch it because it imposed the defect as a requirement**: two of its
cases (`11-c1…py:148-151`) had as their log **precisely that of a healthy birth**, and demanded
that the verdict be red. ⇒ The certification did not test the judge: it **froze its error**.

> ⭐ **The rule that comes out of it, and it holds for every mesh**: ⛔ **a certification without a case that
> ends GREEN starting from healthy data is not a certification.** It is §1.44 applied one level up:
> the predicate that cannot fail, this time protected by a bench that proves it right.
>
> ⚠ And the second: when a **red** verdict has held for days and nobody manages to make it turn
> green, ⛔ the first question is not *«why is the product broken»* but **«can this mesh say
> green?»**. It costs ten minutes and here it cost quite a lot more.

---

### 1.54 ⛔⛔ **The repair of one thing opened the fault of another — and the fault looked like the product's**

`[M]` 27 Aug 2026. Inside the boxes, a session took **~97 seconds** to become useful.
It looked like the birth defect: Mutter not answering, no window, zero frames.

The real chain, and it has three links:
1. the box must give the tenant the **graphics card's group**, otherwise the compositor
   falls back to software and the numbers are false. ⇒ The recipe **moves** the `polkitd` group from 991 to
   1991 to free that number;
2. ⛔ **`groupmod -g` does not carry the files along.** `/etc/polkit-1/rules.d` stayed `root:991` ⇒
   `polkitd` could no longer read it, and died;
3. `gnome-shell` calls `polkit` and `upower` **synchronously** at startup ⇒ it took **four
   25 000 ms timeouts in a row**.

> ⇒ ⭐⭐ **The repair of the graphics card opened the polkit fault, and the polkit fault
> looked like a defect of the product.**

⭐ The cure lies entirely in the **recipe**, and it required no new permission: whoever moves the number
makes the files follow (`find -gid … -exec chgrp`), and the groups unit takes `Before=polkit.service`.
⚠ `[M]` With `chgrp` alone polkit still died, **beaten by 97 thousandths of a second**.
`[M]` Afterwards: three new sessions negotiate the format in **1.105 s · 0.998 s · 0.957 s** — from 97
seconds to **one**.

> ⚠ **The lesson**: when a system identifier is changed to make room for another, ⛔ the
> question is not *«has the number changed?»* but **«what belonged to that number?»**. And when an
> environment built by us behaves badly, ⭐ **the first suspect is the environment**, not the
> product — because we did not write the product last night, the recipe we did.

---

### 1.55 ⛔⛔ **The number read for months was uninitialised memory**

`[M]` 27 Aug 2026. Phase 10 §7.4 described a *«third state»* of the stage — the line
`(0 prima, **2** dopo)` — and treated it as a fact: two monitors appeared.

⛔ **It was garbage.** `src/figlio.c` · `codifica_e_manda()` sent the structure to the parent **before** the `memset` at
`:5311`. `[M]` Proven in two ways: that line appears even on boxes where **no monitor can
have been born** (there the product cannot even start the desktop), always and only on the branch *«waiting for the
client's canvas»*, with obvious garbage beside it (`stride 958311266`, `stride 306537694`); and in the
machine code the old branch sent **328 bytes** having written **32**.

> ⭐ **And the damage is not the defect: it is the diagnosis.** That `2` fed for months a hypothesis —
> *«sometimes two monitors appear»* — that steered the hunt. ⛔ A number never written is worse
> than a missing number, because **it looks like a datum**.
>
> ⚠ The rule: a structure that crosses a boundary (process, socket, network) is zeroed **at the top
> of the function**, before any early exit — not «before use», which is a place that
> moves with every change.

---

### 1.56 ⛔⛔ **The bench tested four desktops, and the product drove one**

`[M]` 27 Aug 2026. The net has four boxes — GNOME, KDE, XFCE, LXQt — and the phase
presented them as the proof that *«the same tests run on different desktops without a line changed»*.

⛔ Then C1 was run **ten times per box** on the other three, and the count was:
**0 healthy · 0 blind · 30 «I could not look»**. The reason is stated by the product's log:
*«Mutter non espone RemoteDesktop»* — ⛔ **the product can start only GNOME** (`src/sessione.c` · `scrivi_dropin()`,
all of `src/mutter.c`), and in the other three boxes `gnome-shell` is not even there.

⭐ **What the other three really test is real but smaller**: the environment (step 0), the
sound (C5, which does not go through the desktop), the leftovers (C7), the log (C9), the alignment (C11). ⛔ They do not
prove that the **product** holds on those desktops, because there the product does not run.

> ⚠ **The lesson**: ⛔ *«the test runs on four environments»* and *«the test says something about four
> environments»* are two different sentences, and the second must be **measured**, not deduced from the first. The sign
> that tells them apart is outcome **3**: a mesh that on three environments out of four never reaches a
> judgement is not testing them — it is **visiting** them.

---

### 1.57 ⚠ **The rebuilt binary wanted a library the bench did not carry — and the bench said so**

`[M]` 27 Aug 2026. Having put back into the four boxes the product rebuilt with the day's
cures, `11-accendi.sh prodotto` answered on all four:

```
  NO  1 librerie non si risolvono: il server morira e non si sapra perche
  NO  il server non ha detto di essere pronto in 20 s
```

⇒ `ldd` inside the box: **`libngtcp2_crypto_ossl.so.0 => not found`**. The build container
on the laptop had moved — the new binary links to a library the old one
did not use — and the bench carried inside only the old supply.

> ⭐ **And this is good news, not a fault**: it is exactly the check `11-accendi.sh`
> does **on purpose** after every delivery (`ldd | grep -c "not found"`), written when it was learnt that
> ⛔ *«the binary was right and the libraries were not, and the symptom was on the wrong side»* (phase 11
> §7-bis.4). ⇒ The defect was **named in two seconds** instead of showing up three hours later
> as «the server dies and nobody knows why».
>
> ⚠ **The lesson that remains**: it is rule R2 — *«versions are declared, never «the latest
> available»»* — that gave way on the side of the **build container**, not on that of the
> boxes. ⛔ An undeclared build environment is a dependency that changes by itself, and the
> net notices it **downstream**, when the damage is already inside the image.
