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
*«one of the two»*. ⇒ ⛔ **One of the two could have been broken forever and the bench stayed green**, because
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
70,3 [M] + 11,6 [M] (the browser's event queue: in the bench it is 0,165 ms
                     because the hand is SYNTHETIC)
       + [?] 4-12 (hand → event)  + [?] 16-40 (drawing → lit pixel)
     = 102-134 ms  ⇒  0,48-0,63 bars
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

## 2. Come si prova

### 2.0 ⛔⛔ Un banco che dice «no» deve dire CON CHE PALCO ha detto no

*13 agosto 2026, sera. ⛔ **È costata una corsia intera di un piano**, ed è la forma più cara
incontrata finora, perché il banco **non si è rotto**: ha risposto, con precisione, alla domanda
sbagliata.*

Una sonda chiedeva a Chrome se sapesse decodificare HEVC. Rispondeva **no**, cinque volte su cinque,
con la fermezza di una misura ripetuta. Ogni tanto usciva un **sì**, e veniva archiviato come
*«anomalia non riproducibile»*.

⛔ **La sonda lanciava Chrome con `--disable-gpu`.** Chiedeva a un browser accecato se vedesse.

| Chrome sullo stesso Xvfb | webgl | HEVC |
|---|---|---|
| **senza** la bandiera | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
| **con** la bandiera | `niente webgl` | no |

Sul quel «no» era stata scritta una conclusione — *«non è un problema di codec, è un problema di
PALCO»* — e sulla conclusione **una corsia di lavoro**, dichiarata *«quella da cui comincia la
sessione»*. Il «sì» scartato come anomalia era **l'unico giro giusto**.

> ⛔⛔ **La lezione, e non è tecnica**: *«non c'è»* e *«non ho potuto guardare»* **hanno lo stesso
> aspetto**, e il secondo è più frequente del primo. ⇒ **Un banco che risponde NO deve scrivere
> accanto alla risposta la scena da cui l'ha data** — che palco, che bandiere, che hardware visibile
> — esattamente come `§1.1` pretende la scena accanto a un numero. **Un no senza la scena dichiarata
> non è un no: è un'assenza di informazione travestita da informazione.**

⭐ **E il segnale c'era già, nel verbale**: un esito che non si riproduce **una volta su sei** non è
rumore, è una **variabile non dichiarata**. ⇒ *Quando un banco dà due esiti diversi sulla stessa
domanda, la cosa da cercare non è quale dei due è vero: è **che cosa è cambiato fra i due giri**.*

> ### ⛔⛔⛔ E LA CURA DI QUESTA LEZIONE È CADUTA NELLA STESSA LEZIONE, un'ora dopo
>
> *La spiegazione qui sopra — «era la bandiera, non il palco» — è **mezza falsa**, e a trovarlo è
> stato un altro gruppo. Si lascia scritta perché **il modo in cui è caduta è la lezione vera**.*
>
> `[M]` con una controprova che **non passa dal browser** — `xlsclients`, cioè chi è davvero
> attaccato a quello schermo:
>
> | come si lancia Chrome | clienti **sull'Xvfb** | `screen` | webgl | HEVC |
> |---|---|---|---|---|
> | **come lo lanciava il banco** | ⛔ **0** | **2560×1080** | GPU | true |
> | `--ozone-platform=x11` | ⭐ **1** | 1280×1024 | *niente* | **false** |
>
> ⛔⛔ **Chrome ignora `DISPLAY` e sceglie Wayland da `XDG_SESSION_TYPE`.** ⇒ Il browser **non era
> mai stato sullo schermo finto**, in nessuno dei due bracci dell'A/B: era **sul desktop
> dell'utente**. La bandiera contava; il palco era già quello vero.
>
> ⇒ ⭐ **La lezione si rafforza invece di indebolirsi, e si allarga**: chi ha scritto la cura ha
> dichiarato una scena — *«Xvfb :85»* — **che ha creduto invece di verificare**, e l'ha scritta nel
> verbale accanto al numero. **Esattamente il difetto che stava curando.**
>
> > ⛔ **La forma completa, e vale per ogni banco browser di questo progetto**: *dichiarare un palco
> > non è averlo*. Il palco si **verifica dall'altro capo** — chi è attaccato allo schermo, che
> > misura ha lo schermo che la pagina vede, che hardware nomina — e non da come si è **lanciato** il
> > processo. **Un'intenzione scritta in una riga di comando non è una misura.**
>
> ⚠ E la conseguenza operativa è più grossa del codec da cui è partita: **i banchi browser di questo
> progetto misurano sul desktop dell'utente credendo di essere su uno schermo finto** ⇒ contesa non
> dichiarata, e ogni verbale che dice «Xvfb» dice una cosa che non è.

⚠ **Tre sorelle minori, pagate lo stesso giorno e della stessa famiglia:**

| | |
|---|---|
| ⛔ **un confronto che non era un confronto** | due codificatori cronometrati **a bitrate libero**: quello che sembrava concorrenziale consegnava **trenta volte meno byte**. ⇒ *«Più veloce» a un trentesimo del lavoro non è più veloce* — **si fissa il lavoro, e i fotogrammi in uscita si CONTANO** |
| ⛔ **un elenco creduto invece che girato** | `av1_vaapi` **compare** fra i codificatori di `ffmpeg`, e all'uso esce **218**: l'hardware l'entrypoint non ce l'ha. ⇒ *Un elenco dice che il codice c'è, non che la macchina lo sa fare* |
| ⛔⛔ **una dichiarazione d'accordo con sé stessa e discorde dai byte** | vedi §2.0-bis qui sotto: **è costata il codec dell'intero prodotto** |

### ⛔⛔ 2.0-bis Chiedere un formato non è averlo — si rilegge quel che si è PRODOTTO

*13 agosto 2026, notte. ⛔ **Il prodotto ha codificato in software per giorni per una riga di un
banco**, e la cosa notevole è che **ogni pezzo della catena rispondeva correttamente alla domanda
che gli era stata fatta**.*

Un generatore di sonde chiedeva a libx265 il profilo per nome — `-profile:v main10` — e due righe
dopo passava `-x265-params …:**keyint=1**:…`. ⛔ **`keyint=1` fa emettere «Main 10 Intra», cioè
`Rext`, `profile_idc = 4`, annullando il profilo chiesto — e senza un errore.**

Quelle sonde finivano dentro la pagina del prodotto, che le usava per decidere quali codec
dichiarare al server:

| chi | che cosa diceva | ed era **giusto** |
|---|---|---|
| la **stringa** | `hev1.1.6…` — profilo **1** | sì, per quel che dichiarava |
| i **byte** | `profile_idc = **4**` | ⛔ e nessuno li leggeva |
| `isConfigSupported` | **true** | sì: risponde **alla stringa** |
| il decodificatore | `EncodingError` **sui byte** | sì |
| la pagina | *«questo codec non arriva al pixel»* | sì, dato quel che vedeva |
| il server | negozia **l'altro codec** | sì: prende la prima voce del client |

⇒ **Nessuno ha sbagliato, e il risultato era sbagliato.** Un difetto così non lo trova chi rilegge
il codice: lo trova **chi legge i byte prodotti**.

> ⛔ **La regola**: `CODER.md` §3.9 dice *«quando si chiede un componente per nome, si verifica che
> abbia obbedito»* — e finora è stata applicata **all'ingresso**. ⇒ **Vale anche all'USCITA**: quando
> si dichiara un formato, **si rilegge il flusso e si confronta con la dichiarazione**. Una stringa e
> un flusso che non si guardano in faccia **non sono due controlli: sono zero**.

⭐ **E il costo del controllo mancante era due righe**: `ffprobe` sul flusso appena prodotto. Il
banco che adesso lo fa (`banchi/02-pagina-sonda-verifica.py`) legge le sonde **dal file del
prodotto** invece di ricopiarle, e **conta i fotogrammi** invece di chiedere.

### ⛔⛔ 2.0-ter Due misure prese in POSIZIONI diverse dentro la stessa pagina non si confrontano

*13 agosto 2026, notte. ⭐ Un banco stava per consegnare **«Firefox è il 44 % più lento di Chrome»**,
e il 44 % non era di Firefox.*

Un banco provava più configurazioni **di fila, nella stessa pagina**, e ne confrontava i tempi. Lo
scarto era stabile e riproducibile — **2,5 ms**, sempre nello stesso verso. ⛔ **Era la POSIZIONE
nella sequenza**: rovesciando l'ordine dei casi, le tre configurazioni davano lo stesso numero.

⛔⛔ **E la parte che rende la trappola cattiva**: l'effetto **tira in versi opposti sui due motori**.

| | chi corre **per primo** |
|---|---|
| **Chrome** | è il **più veloce** (7,9 ms) |
| **Firefox** | è il **più lento** (11,5 ms) |

⇒ Un banco che provasse i casi sempre nello stesso ordine — cioè **qualunque banco scritto in modo
naturale** — misurerebbe una differenza fra i due motori **che non esiste**, e la misurerebbe
**stabile**, cioè con tutta l'aria di un fatto.

> ⛔ **La regola**: *quando si confrontano N configurazioni dentro uno stesso processo, l'ordine è
> una variabile* — e come ogni variabile va **dichiarata e rovesciata**. ⭐ Il controllo costa **un
> giro in più**: si rifà la sequenza al contrario, e se i numeri si spostano, quel che si stava
> misurando era la sequenza.

⚠ **E c'è una sorella, trovata la stessa notte, che riguarda le finestre esclusive**: un banco che
misura N configurazioni di fila **è il vicino di sé stesso** — il carico a un minuto è una media, e
la configurazione appena finita si presenta come contesa a quella dopo. `[M]` **5 rifiuti su 8** con
*«browser altrui: 0»*. ⛔ **La cura non è alzare la soglia** — sarebbe spegnere l'arbitro — ma
**aspettare che la propria scia si spenga** prima di chiedere il permesso.

### 2.1 La regola dei tre client, e le sue forme insidiose

Nessun client copre i casi degli altri. Un difetto che si vede **solo** su uno è quasi sempre
un'informazione che il server ha omesso, non un'anomalia del client — e il client indulgente la
supplisce, nascondendola.

Ma la regola ha almeno tre forme, e le abbiamo pagate tutte:

| Forma | Come si è presentata |
|---|---|
| sul **tipo** di client | due giorni per un `MapSurfaceToOutput` mancante: due client su tre disegnavano lo stesso |
| sul **numero** di connessioni | un certificato TLS condiviso uccideva il server **alla seconda** connessione; una prova a connessione singola resta verde per sempre |
| su **chi collauda** | una correzione validata su un banco che il difetto non mostrava, e fatta collaudare all'utente |

> ⚠ **In V2 questa regola cambia forma, non valore** *(8 agosto 2026)*. I client di riferimento non
> sono piu' tre e non sono piu' di altri: sono **due, e nostri** — Linux e Android, sopra lo stesso
> `librcp`. Sparisce il client indulgente che supplisce in silenzio un'informazione omessa dal
> server, ed e' la forma che ha prodotto i difetti peggiori.
>
> ⛔ **Ma sparisce anche l'avvertimento gratis, e questa e' la perdita da sorvegliare.** Quando due
> client scritti dalla stessa mano, sullo stesso codice di protocollo, sono d'accordo, **non stanno
> confermando niente**: stanno ripetendo lo stesso presupposto. In v1 il disaccordo fra mstsc e
> `xfreerdp3` era un difetto che si dichiarava da solo; in V2 quel difetto resta muto.
>
> Da cui, in concreto: le altre due forme della regola — sul **numero** di connessioni e su **chi
> collauda** — restano intatte e vanno pesate di piu'; e dove il protocollo lascia una scelta, la si
> prova **contro la specifica scritta**, non contro l'altro nostro client.

### 2.2 Una prova può essere verde per tutto il tempo in cui il difetto è vivo

Ed è la peggiore delle prove, perché dà fiducia.

| Il banco contava | Il difetto cambiava |
|---|---|
| fotogrammi spediti e blocchi riscontrati | **i campioni**, non il loro numero: l'audio era rumore a fondo scala |
| che il processo del client morisse | **quando** moriva, e perché: il client Android restava lì |
| fotogrammi consegnati | **quali**: due schermate intere che si alternavano |

Da cui la regola: **un banco che conta non basta**. Deve *ascoltare* quel che il client suona e
*guardare* quel che il client mostra — due fotogrammi consegnati a distanza devono essere diversi
quando la scena è cambiata, e uguali quando non lo è.

> ⛔ **E c'è una quarta riga di quella tabella, trovata il 13 agosto 2026, che non riguarda quel che
> il banco guarda ma l'unità in cui lo guarda**: una prova può essere verde per tutto il tempo
> in cui il difetto è vivo perché esercita il giudice nell'unità del **lettore** invece che in
> quella dell'**acquisizione**. Il banco guarda la cosa giusta, la conta bene, e la conta **nella
> grandezza sbagliata**. ⇒ Il rimedio sta in §1.2, ed è una domanda in più al momento della
> certificazione, non un controllo in più al momento della misura.

### 2.3 Una prova che boccia il codice giusto costa quanto una che promuove quello sbagliato

Il banco della rotella cercava `asse dy=-10` mentre il registro scriveva `asse dx=0 dy=-10`: rosso,
con il codice corretto. Un'altra volta un `$1` non espanso faceva trovare a `grep` qualunque cosa, e
i controlli diventavano verdi o rossi a caso.

*Dettaglio: `PIANO.md` fase 4, `REFERENCE.md` R29.*

### 2.3-quinquies ⭐ Due lati sincronizzati a tempo bocciano il codice giusto

Un banco che pilota **due ambienti** — la sessione di qua, il client di là — non può coordinarli con
i `sleep`: i due orologi partono quando partono, e basta che uno dei due impieghi qualche secondo in
più perché i passi si accavallino. Al banco degli appunti di KDE i due lati erano sfasati di
**tredici secondi**: il client copiava *prima* che la sessione avesse copiato, la sessione incollava
la propria roba, e il controllo diceva rosso su un codice che funzionava — cosa che si è vista solo
leggendo il registro riga per riga.

**Si sincronizzano con marcatori**: un file che il primo tocca e il secondo aspetta. Costa tre righe
e toglie di mezzo un'intera classe di falsi rossi — e di falsi verdi, che sono peggio.

⚠ E un corollario che vale per la clipboard e per ogni stato condiviso: **quel che resta dal giro
prima va svuotato all'inizio**. La clipboard del client conteneva ancora la stringa della prova
precedente, veniva annunciata alla connessione, e sembrava un risultato.

### 2.3-bis ⭐ Il banco sbaglia dove il sistema tronca, e mente in tutte e due le direzioni

*Imparata l'8 agosto 2026, aprendo la cattura di KDE, e sono tre difetti di banco in un pomeriggio —
nessuno dei tre nel codice del prodotto.*

| Il difetto del banco | Come si è presentato | La forma generale |
|---|---|---|
| `pgrep -x weston-simple-egl` | **«la scena non è partita»** mentre la cattura consegnava 58 fotogrammi al secondo | `comm` è troncato a **15 caratteri** e quel nome ne ha 17: il confronto esatto fallisce **sempre**. Si usa `pgrep -f` |
| `-sec-nla` passato a `xfreerdp3` | il client stampava la pagina d'aiuto e usciva; il banco leggeva «zero fotogrammi» e dava la colpa al **server** | un'opzione rifiutata non è un difetto del bersaglio. Si copia la riga da un banco che funziona, invece di ricordarla |
| `2>/dev/null` su un comando che contiene `sudo` | il banco restava **appeso per sempre, in silenzio** | è la trappola della fase 1, e in un pomeriggio l'ho ripagata **tre volte**: la richiesta di password va sullo stderr, e chi la deve fornire non la vede mai |

⛔ **La regola che le tiene insieme**: quando un controllo di banco è rosso e la cosa che misura
*sembra* funzionare, **il primo sospetto è il controllo** — è §1.9 applicata al banco invece che alla
misura. E quando è verde, vale §2.2.

⚠ **E la terza riga è la più istruttiva, perché la lezione era già scritta.** Sapere che `2>&1` su un
`sudo` appende non basta: la si riscrive per abitudine, ogni volta che si vuole «togliere il rumore»
da un comando. L'antidoto non è ricordarsela, è **non mettere mai `sudo` dentro un comando di cui si
redirige lo stderr**.

### 2.3-ter Un banco che rifà lo stesso ambiente due volte fallisce la seconda

*Imparata l'8 agosto 2026: la sessione Plasma partiva al primo giro e non al secondo.*

Uccidere il compositore mette in coda su systemd un lavoro di *stop* per la sua unità; chiedere di
far partire la sessione prima che quel lavoro sia finito fa **rifiutare l'intera transazione**, e il
messaggio che l'utente legge è soltanto «Could not start Plasma session».

**La forma generale**: fra «ho ucciso il processo» e «il gestore di servizi lo sa» c'è un intervallo,
e un banco che riparte in quell'intervallo si comporta in modo diverso dalla prima esecuzione. Si
ferma l'unità e si **aspetta che sia inattiva**, invece di uccidere e ripartire.

*Corollario, che è la vera ragione per cui va scritto qui*: **un banco va eseguito due volte di
fila** prima di crederci. Uno che passa solo da macchina pulita non è un banco, è una dimostrazione.

### 2.3-quater ⭐ Una decisione presa citando un comportamento non misurato è presa a metà

*Imparata l'8 agosto 2026, e l'ha trovata l'utente al primo minuto di uso vero.*

La decisione «misura fissa alla connessione» era stata scritta con accanto la ragione: *«l'immagine
si scala nel client»*. Quella frase **non era mai stata misurata**, e il client non scala niente —
apre una finestra grande quanto la tela. Il sintomo, dalla parte di chi guarda: *«non riesco a
vedere tutto lo schermo, la risoluzione sembra ignorata»*.

⛔ **E la smentita era già in casa**, misurata il giorno prima e su un'altra pagina: la scalatura
lato client passa da `MAPSURFACETOSCALEDOUTPUT`, resa da **un client su tre**.

**Le due regole:**

1. **In una decisione, la ragione va marcata come tutto il resto.** Se dice «il client farà X» e
   nessuno ha visto il client fare X, è una `[?]` — e una decisione che poggia su una `[?]` va
   scritta come provvisoria.
2. **Prima di scrivere una ragione, si cerca se il progetto l'ha già misurata.** Qui bastava
   rileggere §10.2 di `REFERENCE.md`, che è il documento delle regole. Il costo di non averlo fatto
   non è stato il codice — che era giusto — ma **il tempo dell'utente**, speso a chiedersi perché la
   sua risoluzione venisse ignorata.

### 2.4 Ciò che cambia quel che si VEDE non si spedisce validato solo sul banco

Il banco può dire che l'immagine è migliore — con PSNR, SSIM e un fotogramma guardato a occhio — e
l'utente può guardarla e dire *«siamo tornati indietro»*. Il metro è lui.

Quel che cambia l'immagine sta **dietro un interruttore spento** finché non l'ha guardato.

*Prezzo: una fase intera azzerata. Dettaglio: `PIANO.md` fase 10.*

### 2.5 All'inizio di ogni sessione: lo stato della macchina contro quel che i documenti dichiarano

Un file d'ambiente era stato **letto** all'inizio della giornata, e la riga che teneva spenta una
strada difettosa non c'era più — persa quando il file era stato riscritto per un altro motivo.
Nessuno ha confrontato quel che c'era con quel che i documenti dicevano di aspettarsi, e l'utente si
è ritrovato in faccia un difetto noto.

**E la regola generale che ne discende, che è più importante del controllo**: la protezione di un
difetto noto **non si affida a una riga di configurazione che si può perdere**. Sta nel programma,
dove per toglierla bisogna volerlo. Vale per le protezioni e vale per i valori da cui dipende quel
che si vede: il 7 agosto la cadenza a 60 è stata messa in `main.c` per questo, non in un file.

*Dettaglio: `REFERENCE.md` R29 in fondo.*

### 2.5-bis ⭐ Una macchina che si rimette da sé non è una macchina che si rimette *completa*

Il ripristino del server era scritto in tre comandi, e per un giorno intero è bastato. Il primo
riavvio vero ha mostrato che mancavano **due pezzi**, e nessuno dei due era nei documenti:

- **il disco non si monta da solo** — `/media` vuota, `/etc/fstab` senza righe, e i sorgenti stanno
  lì. Senza quel passo il primo dei tre comandi non esiste nemmeno come file;
- **i banchi dipendono da pacchetti che il provisioning non installa** (`pulseaudio-utils`, e per un
  altro banco `wl-clipboard`): c'erano perché qualcuno li aveva messi a mano mesi prima, e il
  provisioning li ereditava senza dichiararli.

⛔ **Da cui la regola**: un ripristino si prova **riavviando**, non rileggendo lo script. Le
dipendenze installate a mano diventano invisibili nel giro di un giorno, e il momento in cui te ne
accorgi è sempre quello in cui hai bisogno che la macchina riparta.

⚠ E il corollario che riguarda le misure: **una misura presa su una macchina che ha macinato altro
per un giorno vale meno**. La regressione del volume su GNOME l'ha chiesta l'utente **da macchina
appena riavviata**, e aveva ragione a chiederlo — i numeri sono venuti uguali, ma quella era
l'informazione, non il presupposto.

### 2.6 L'utente non è il banco

Ogni ipotesi che chiede «collegati e dimmi» costa un suo intervento. Da cui:

1. **appena la cura c'è, si applica e si dichiara**: «funziona, il resto è ottimizzazione» — e la
   scelta *continuo o rinvio* si mette davanti all'utente **subito**, non dopo cinque giri;
2. **si mette un tetto alla caccia**, dichiarato in partenza;
3. le prove le fa il banco; all'utente si chiede **il giudizio**, che è l'unica cosa che il banco non
   sa dare.

### 2.7 ⭐⭐⭐ Non c'è miglior strumento di diagnosi che monitorare una sessione VERA, byte per byte

*Detta dall'utente il 17 agosto 2026, alla fine di una caccia durata un pomeriggio — e la sua
frase è il titolo perché è la sua parola: «proviamo a riprodurre un video da YouTube, tu monitora
la sessione su ogni singolo byte, così risolviamo una volta per tutte».*

⛔ **È quel gesto che ha rotto lo stallo, e nient'altro.** Prima c'erano: cinque giri di banco
**verdi**, un giudice certificato su sei casi, una revisione avversariale con tredici rilievi, e
**otto cure** di cui sei erano difetti veri che non erano quello che l'utente sentiva. Nessuna di
quelle cose ha trovato la causa.

⭐ **L'ha trovata una sessione vera, guardata mentre succedeva.** Trenta secondi di YouTube con il
registro aperto hanno dato il numero: il figlio produce **50 blocchi al secondo**, il server ne
rifiuta **25**. Esattamente la metà.

**Perché funziona, e perché il banco no.** Il banco è una scena che **hai scelto tu**: contiene i
difetti che sapevi immaginare. Una sessione vera contiene quelli che non sapevi — e in più li
mette **tutti insieme**, che è la condizione in cui vivono. ⚠ Qui i cinque verdi erano onesti: il
banco misurava il **contenuto** (frequenza, ampiezza, purezza) e il difetto era nel **ritmo**.

**Le tre condizioni perché «monitorare» sia diagnosi e non contemplazione:**

| | |
|---|---|
| ⛔ **tutti gli anelli, sulla stessa riga** | qui erano quattro — chi produce, chi codifica, chi spedisce, **chi ascolta** — e del quarto non si sapeva niente. Finché è così, ogni cura sembra confermata dal ragionamento e nessuna dalla misura |
| ⛔ **si registra PRIMA che parta** | la registrazione si accende e *poi* si dice all'utente «vai»: un difetto che dura trenta secondi non si riprende |
| ⭐ **si guarda la FORMA del numero, non solo il valore** | la perdita era *esattamente* la metà. Una perdita di rete non è mai esattamente la metà; **un'aritmetica sì**. Un rapporto troppo tondo accusa un conteggio, non il mondo |

**E la cosa che è costata di più**: il quarto anello — il lato che **ascolta** — non aveva un
posto dove parlare. La pagina ha un riquadro di diagnostica, ⛔ ma col desktop acceso è a tutto
schermo e **non è raggiungibile**: chiederne la lettura all'utente è chiedergli una cosa che non
si può fare. ⭐ La cura è costata **trenta righe** — un endpoint (`/diario`) su cui il client
scrive i suoi numeri, che finiscono nel **registro del server** accanto agli altri tre.

⇒ ⭐ Con i quattro anelli sulla stessa riga la diagnosi è durata **un passaggio**: *50 prodotti →
40 consegnati → deficit 20 % → cuscino 250 ms → un buco ogni 1,25 s*. Misurati: **23 in 30
secondi**. Il conto ha chiuso al decimale e ha **assolto tre imputati in un colpo**.

⚠ **E non contraddice §1.1 né il valore dei banchi**: il banco serve a *ripetere* e a *certificare*.
Ma quando l'utente dice «fa schifo» e il banco dice verde, ⛔ **non si cura al buio: si guarda una
sessione vera**. È `CODER.md` §3.8 — *«si verifica dal lato che deve ricevere»* — applicata alla
sessione intera invece che a un anello.

---

### 2.8 ⭐⭐⭐ UN SECONDO MOTORE È UN SECONDO LETTORE — e fa emergere i difetti che l'unico lettore non poteva vedere

*17 agosto 2026, sera, parole dell'utente dopo un'ora su Firefox: «Firefox sta facendo emergere una
serie di bug nascosti davvero grossa».*

`PIANO.md` §0.4 dice che due pezzi nostri che vanno d'accordo **non confermano niente**, e per il
protocollo il progetto ha pagato il prezzo di un secondo lettore: `01-b3-cliente.py`, scritto in un
altro linguaggio leggendo **solo** `RCP.md`.

⛔ **Per il PRODOTTO quel prezzo non era mai stato pagato.** Tutto — video, input, appunti,
scorciatoie — era stato misurato su **un motore solo**, della famiglia di Chrome, e su **un sistema
solo**. Un browser che conferma se stesso è esattamente la stessa cosa di due nostri pezzi che si
parlano.

**Che cosa è venuto fuori in un'ora, aprendo la stessa pagina su Firefox:**

| # | il difetto | perché non si vedeva |
|---|---|---|
| 1 | ⛔ la **profondità dichiarata era 8 e sul filo ne andavano 10** — `figlio.c` aveva `r.profondita = 10` scritto a mano, e il numero negoziato **non attraversava il confine di processo** | ⚠ **c'era su tutt'e due i browser**: HEVC porta i suoi parametri nel flusso (VPS/SPS) e il decodificatore di Chrome si riconfigurava da sé. AV1 no — la pagina configura `av01.…08` e dav1d si fida |
| 2 | ⛔ `Ctrl+Alt+Fine` **non arrivava mai alla pagina**: sul portatile Linux quella combinazione se la prende il desktop locale | scelta e provata su Windows, dove non la aggancia nessuno |
| 3 | ⛔ il `preventDefault()` sul `Ctrl+V` **impediva all'evento `paste` di nascere**, cioè spegneva l'unica strada che Firefox lascia agli appunti | su Chrome il testo arriva dalla **sorveglianza** (`clipboardchange`), che non passa dai tasti |
| 4 | ⚠ **AV1 gira in software** su questo ferro, e si vede: il desktop è lento | nessuno aveva mai negoziato AV1 — Chrome sceglie HEVC, che qui è in hardware |

#### ⏳ E il quinto — gli artefatti su Firefox — è ancora aperto, ma quattro ipotesi sono MORTE

*Scritto perché nessuno le rifaccia: un'ipotesi eliminata da una misura vale quanto una confermata.*

| l'ipotesi | come è morta |
|---|---|
| ⛔ «il flusso AV1 che spediamo è rotto» | **falsa.** Sei fotogrammi presi **dal filo** e dati a **libdav1d** — lo stesso decodificatore che usa Firefox — danno un'immagine **perfetta**: sfondo liscio, testo del terminale nitido, nessun blocco |
| ⛔ «SVT-AV1 allinea 962 a 968 e il conto non torna» | **falsa, e misurata a parte**: 2560×**962** codificato e ridecodificato torna **2560×962 esatti**. L'encoder riempie dentro e scrive la misura di resa; dav1d ritaglia giusto. *(La qualità misurata allora, SVT-AV1 passando da libavcodec, non vale più dopo la fase 18.)* |
| ⛔ «la pagina riceve una misura diversa da quella dichiarata» | **falsa.** La pagina lo dice da sé: *codificato 2560×962 · mostrato 2560×962 · tela in vigore 2560×962* |
| ⛔ «il decodificatore del browser sbaglia e lo dice» | **falso**: zero errori riportati, e il filtro che li avrebbe portati al server funzionava |

⇒ **Resta un pezzo solo, e non era mai stato messo alla prova**: il percorso di **disegno** della
pagina. ⚠ La cattura pulita usa il cliente Python, che non dipinge niente — e su Chrome quel
percorso non ha mai avuto un testimone indipendente.

⭐ **Il dato nuovo da cui ripartire**: la pagina dichiara `formato BGRX`. Un fotogramma decodificato
da AV1 esce in `I420`; Firefox lo consegna **già convertito in RGB**. ⏳ E il secondo percorso di
disegno — `?video=worker` — **non dipinge affatto** su Firefox: la pagina si carica e la sonda
gira, poi niente. `VideoDecoder` dentro un `Worker` su Firefox 140 ESR è la sospettata, e non è
stata verificata.

#### ⛔⛔ Il seguito del 17 agosto, secondo giro: **CONTA GLI ANELLI, E POI CONTALI DI NUOVO**

Le quattro ipotesi di sopra ne lasciavano una sola in piedi — «resta il percorso di DISEGNO della
pagina» — e anche **quella è morta**, misurata: un testimone che guida il **Firefox vero** col
protocollo Marionette (`banchi/07-b46-testimone-disegno.py`) ha tirato giù **la tela in PNG** su
tre geometrie, 2 800 fotogrammi, `dipinti == consegnati`, `saltati_coda 0`, `buchi 0`, e
l'immagine è **nitida a 1:1**, testo del terminale compreso.

⛔ **E nel farlo è saltato fuori un anello che nessuno aveva contato**: la sessione grafica del
portatile non è locale, è **xrdp** (`Xorg :10`, `got RFX capture` = **RemoteFX**, un codec **a
tessere**). ⇒ Fra la nostra tela e gli occhi dell'utente c'era un **quinto** anello, con per
guasti tipici proprio «blocchi rettangolari» e «col tempo non si aggiorna più».

⚠ **E non era lui** — messo alla prova con un controllo della stessa forma di danno (finestra
intera ridipinta venti volte al secondo), gli occhi dell'utente, pulito. ⭐ Ma la lezione non è
il verdetto, è che **per due giorni si è ragionato su una catena a quattro anelli che ne aveva
cinque**, e nessun documento lo diceva. §2.7 dice «servono TUTTI gli anelli»: la parte difficile
non è misurarli, è **sapere quanti sono**. ⇒ Prima di attribuire un difetto **visivo**, si scrive
la catena per intero — compreso come l'utente sta *guardando*.

⭐ **E il contatore che ha spostato la caccia**: da quando la pagina racconta anche
`consegnati→dipinti · salt · buchi · ord · mis · err`, la sessione vera dell'utente **mentre
vedeva l'artefatto** ha detto `23→23` e cinque zeri. ⇒ Non manca nessun fotogramma: **sono
corrotti i pixel dentro quelli che arrivano**. Un difetto che nessun contatore può vedere si
cerca in un modo solo — **guardando l'immagine sbagliata**, non i numeri.

⭐ **E il difetto 1 è quello che insegna di più**: non era un difetto *di Firefox*, era un difetto
**nostro e universale** che un motore indulgente assorbiva. ⇒ Il secondo lettore non trova i difetti
dell'altro: trova **i propri**, che erano lì da sempre.

⛔ **La regola che ne segue**: una funzione provata su un motore solo è provata quanto un protocollo
letto da una sola implementazione. ⚠ E non basta «funziona anche su Firefox»: va provato **il verso
che quel motore percorre diversamente** — che è il caso 3, dove le due strade sono due percorsi di
codice interi.

---

## 3. Che cosa chiedere a un compositore nuovo

Questa è la lista che a GNOME abbiamo composto in otto fasi. Al prossimo desktop si fa in un
pomeriggio, prima di scrivere una riga. Dove la risposta la conosciamo già, è in tabella.

| # | La domanda | Mutter 48.7 | KWin 6.3.6 | wlroots (sway 1.10, labwc 0.8) |
|---|---|---|---|---|
| 1 | **Come si chiede la cattura senza portale?** | D-Bus `org.gnome.Mutter.ScreenCast` | protocollo Wayland `zkde_screencast_unstable_v1` ✅ **scritto e misurato, 8 ago** | nessuna delle due: `zwlr_screencopy_manager_v1` |
| 2 | **Spinge i fotogrammi o li fa tirare?** | spinge (PipeWire) | spinge (PipeWire) | **fa tirare**: una richiesta per fotogramma |
| 3 | **Il protocollo è dietro un permesso?** | no | **sì** — un campo di un file `.desktop`: `X-KDE-Wayland-Interfaces` [R], **più `XDG_MENU_PREFIX=plasma-` nell'ambiente** [M, 7 ago] | no |
| 4 | **Senza monitor, disegna sulla GPU?** | **sì** | **sì** [M, 8 ago]: `OpenGL renderer string` lo dice a chiare lettere via D-Bus — e **questa** è la prova, non il render node aperto (§1.11) | **sì** |
| 9-bis | **Il buffer a copia zero arriva con la fence pronta?** | **no** | **no** [M, 8 ago]: 830 su 830 col disegno in corso. KWin fa `glFlush`, non `glFinish` — quindi la fence c'è e va **aspettata** | da misurare |
| 12-bis | ⭐ **Il cursore è DENTRO l'immagine catturata?** | no | **sì con `--virtual`** [M, 8 ago]: nessun piano cursore ⇒ cursore software dipinto nel framebuffer che si cattura. Il modo cursore dello screencast **non c'entra**, e non c'è leva per impedirlo. ⭐ **Ma la cura non è nasconderlo: è renderlo INVISIBILE** — un tema `XCURSOR_THEME` con un cursore 1×1 ad alfa zero, e il puntatore torna a essere quello del client, come su Mutter | da misurare |
| 10-bis | **Che cosa costa la risoluzione, per davvero?** | niente fino a 4K | **niente a copia zero** (59 fps da 720p a 4K su una Intel integrata), **tutto in memoria** (49,6 → 27,0) [M, 8 ago] | a 4K sì |
| 5 | **Si può chiedere uno schermo virtuale della misura voluta?** | sì, `RecordVirtual` | ⛔ **NO, e il codice diceva di sì** [M, 8 ago]: `stream_virtual_output` col backend `--virtual` risponde **`Could not find output`**, per ogni misura. E `--drm`, che gli output veri ce l'ha, da una sessione senza seat non parte. L'output lo crea la riga di comando del compositore, e noi ci attacchiamo | sì, backend headless |
| 6 | **Quanto consegna, con una scena che cambia a ogni ridisegno?** | ⛔ **la domanda è mal posta, `[M]` 13 ago**: dipende da **come** si chiede. Chiedendo 60 a un monitor a 60: **31,5** (il «~37» di v1 **non si riproduce**). Chiedendo **90 a un monitor a 120**: **61,4**. ⇒ Alla domanda 7, e non a questa | **59–60** | **61** (40 a 4K, per il costo della copia) |
| 7 | **La cadenza dichiarata come si comporta?** | ⭐ `[M]` **13 ago**: **dipende da come si chiede**, e disaccoppiando — monitor **120**, freno **90** — se ne ottengono **61,4**; i «sei decimi» **non si riproducono** (la cella bassa dà **0,50 pulito**). ⚠ **Il perché è `[R]`, non `[M]`**: `maxFramerate` fa due mestieri insieme — freno della cattura *ed* frequenza del monitor virtuale — e nel codice il freno calcola `min_interval_us = 10⁶/maxFramerate` **troncato a intero** contro un tick da 16666,67 µs ⇒ chi cade sotto **perderebbe un tick intero**: una **griglia**, non un battimento. ⛔ *Questa cella dava la griglia come `[M]` «su 13 punti»: falso, corretto il 13 ago sera — vedi il riquadro sotto la tabella.* | **fissa rifiutata anche qui** (`framerate` deve valere `0/1`); il tetto è `maxFramerate`, e lo **onora il server** [R] | da misurare |
| 8 | **Consegna fotogrammi interi o «diff»?** | ⛔ **interi anche a copia zero** — `[R]` **9 ago**, e per due anni abbiamo creduto il contrario: il blit copia l'**intero** framebuffer di vista, Cogl **svuota deliberatamente** lo stack di clip, e per un CRTC virtuale la vista è un `CoglOffscreen` **singolo e persistente**, non uno swapchain. I quattro buffer li chiedevamo noi | **interi, sempre**, su 2–4 buffer, con il danno dichiarato a parte [R] | da misurare |
| 9 | **Il buffer arriva già disegnato?** | **no**: a copia zero il 100 % arriva con il disegno in corso | **sì**: KWin fa `glFlush()`, e `glFinish()` su NVidia e llvmpipe [R] | da misurare |
| 10 | **Che cosa costa la risoluzione?** | **niente** fino a 4K | niente | a 4K sì, ed è la copia in memoria |
| 11 | **Che cosa costa la profondità di colore?** | **niente**, e non esiste un percorso a 24 bit impacchettati | — | — |

| **13** *(nuova)* | ⭐ **Uno schermo virtuale si RIDIMENSIONA a caldo?** | **sì**: la misura si concorda nella negoziazione PipeWire, cambiarla è una rinegoziazione | ⛔ **no su 6.3.6**: il modo è `const`, l'elenco è fissato nel costruttore, e `kde_output_management_v2` sa solo *scegliere* fra i modi annunciati. Risolto a monte (`kwin!7932`, milestone **6.8**) — **e per la stessa strada nostra**, la negoziazione PipeWire | `wlr_output_state_set_custom_mode` esiste e il backend headless la usa già [lettura, **da misurare**] |
| **14** *(nuova)* | ⭐ **La clipboard di chi è?** | ⚠ **del compositore anche qui** — è `MetaSelection` `[R]` **9 ago**. Della sessione remota è solo la **porta** (`EnableClipboard`), e ⛔ **senza sessione la clipboard esiste lo stesso**: la sponda X11 è incondizionata nei due versi, `xclip` funziona | **del compositore**: `zwlr_data_control_manager_v1` v2, **nessun permesso**, e c'è anche se REMOTIX non c'è | lo stesso protocollo: `appunti_wlr.c` **è già scritto per questa famiglia** |
| **15** *(nuova)* | ⭐ **C'è uno stato in cui il compositore REVOCA quel che ha già concesso, e chi ha il dito su quel pulsante?** | ⛔ **sì, ed è l'unico dei tre**: entrando nel dialogo di sblocco gnome-shell chiama `inhibit_remote_access()` e Mutter chiude ScreenCast, RemoteDesktop e InputCapture **rifiutando di ricrearli**. L'eccezione è `is_headless()` `[R]` — la nostra condizione, e **non l'abbiamo chiesta** (`STUDI.md` §gnome §4) | `[?]` da verificare | `[?]` da verificare |

> ⭐ **La 15 è la domanda che questa lista non aveva**, ed è arrivata dallo studio di GNOME
> *(`STUDI.md` §gnome §14, dove è chiamata «la domanda 16» contando le righe `-bis`; qui prende il primo
> numero libero, perché in questo documento **non si rinumera**)*. La 3 chiede se esiste un
> permesso; questa chiede se il permesso **può essere ritirato a caldo**, che è una cosa diversa e
> più pericolosa: si va a chiedere il permesso una volta sola, all'inizio, e nessuno torna a
> guardare. Si fa insieme alla 3.

> ## ⛔⛔ ~~I sei decimi di Mutter~~ → **MISURATO il 13 agosto: non è un battimento, è una griglia**
>
> *Questo riquadro, scritto il 9 agosto 2026 leggendo `STUDI.md` §gnome §8.2, diceva: «`maxFramerate` è il
> freno della cattura e insieme la frequenza del monitor virtuale. **Due orologi allo stesso numero
> battono fra loro, e il battimento vale 0,61**. Costa tre celle e zero righe di prodotto, e se
> riesce porta i 60 su GNOME». Era `[R]`, e portava accanto la propria riserva: «finché non è
> misurata resta una `[?]`; una spiegazione che torna non è una cura che funziona» (§1.11).*
>
> ⭐ **La riserva era quella giusta, e la misura le ha dato ragione due volte: la cura funziona, e la
> spiegazione era sbagliata lo stesso.**
>
> ⭐ **IL FATTO, `[M]`**: monitor a **120**, freno a **90**, e GNOME consegna **61,4** — cella **D**
> di `banchi/03-b14-esiti.jsonl`, pulita, coi tre controlli che chiudono.
>
> ⚠ **LA CAUSA, `[R]`**: letta nel codice di Mutter, `maxFramerate` non sembra un tetto continuo ma
> una **GRIGLIA**. Il freno calcola `min_interval_us = 10⁶/maxFramerate` **troncato a intero** —
> 16666 per 60 — contro un tick da **16666,67 µs**: chi cade sotto **perde un tick intero**. Non un
> **battimento** fra due orologi, una **quantizzazione**. ⭐ **È la spiegazione migliore che
> abbiamo**, ed è coerente con la cella D. ⛔ **Ma è una lettura, non una misura.**
>
> > ⛔⛔ ⚠ *Questa riga diceva: «`[M]` legge verificata su **13 punti**: 8 la confermano, **0 la
> > smentiscono**». **È FALSA.** Il file degli esiti della griglia,
> > `banchi/03-b14-esiti-griglia.jsonl`, porta **tre righe**: il terreno e **due celle**
> > (`griglia-apertura-120`, `griglia-freno-90`), **tutt'e due con `scena_sul_mio_monitor: false`**
> > ⇒ rifiutate dal banco stesso, che stampa «⛔ la legge NON regge su **0 punti su 0**». I tredici
> > punti non esistono in nessun file di esiti. **Corretta il 13 agosto 2026**, rilievo del
> > coordinatore della fase 3, verificato sui due file di esiti. ⇒ La quantizzazione torna `[R]`; la
> > tabella qui sotto resta `[M]`, perché viene tutta da `03-b14-esiti.jsonl`, sette celle tutte con
> > `scena_sul_mio_monitor: true`.*
>
> | monitor | freno | consegnati | mediana | p99 |
> |---|---|---|---|---|
> | 60 | 60 | 31,5 | 33,31 ms | 35,53 |
> | 120 | 60 | 46,13 | 24,12 ms | 29,23 |
> | ⭐⭐ **120** | ⭐⭐ **90** | ⭐⭐ **61,4** (60,04) | ⭐ **16,66 ms** | 20,43 |
>
> ⛔ **E i «sei decimi» non si riproducono**: la cella bassa dà **0,50 pulito e deterministico** —
> che è quel che una griglia produce, e un battimento no.
>
> ⭐ **La cura riesce**: monitor 120, freno 90, e GNOME consegna **61,4**. ⛔ **Ma il prodotto oggi
> non sa chiederla** — `MOVIMENTO_FPS 60` è una costante di compilazione, `RecordVirtual` non prende
> la frequenza, e i monitor virtuali sono tutti @60. È `[M]` **sul banco** e **zero in produzione**.
>
> > ### ⭐⭐ E la lezione, che vale più del numero
> >
> > **Una spiegazione che torna, che spiega tutti i dati che abbiamo e che indica pure una cura che
> > poi funziona, può essere comunque falsa** — e non se ne accorge nessuno, perché la cura
> > funzionando la conferma. Qui il battimento spiegava lo 0,61, indicava il disaccoppiamento, e il
> > disaccoppiamento ha portato i 60: tre conferme di fila per una causa sbagliata.
> >
> > ⛔ **A smontarla non è stata la cura: è stata la CELLA APPENA FUORI** — la cella bassa, che il
> > battimento vuole a **0,61** e che dà **0,50 pulito e deterministico**. Il battimento e la
> > quantizzazione **prevedono la stessa cosa sulla cella che si voleva curare**, e cose diverse
> > **fuori**. ⇒ È §1.13 nella sua forma generale: *il caso che distingue due spiegazioni non è
> > quello che le ha prodotte, è quello appena fuori* — e la cella che le distingue costa quanto
> > quella che le conferma.
> >
> > > ⛔⛔ ⚠ *Questo capoverso diceva: «A smontarla non è stata la cura: è stata la **MISURA A
> > > TAPPETO** — **13 punti** invece dei tre che servivano a dimostrare che funziona». **È falso, e
> > > la misura a tappeto non c'è mai stata**: le sue due sole celle sono rifiutate dal banco stesso
> > > (riquadro qui sopra). A smontare il battimento è stata **una** cella pulita, la A. **Corretto
> > > il 13 agosto 2026**, rilievo del coordinatore della fase 3.* ⇒ ⭐ **E la lezione ne esce più
> > > forte, non più debole**: non serviva il tappeto, **bastava il caso appena fuori** — purché sia
> > > valido.

> ⚠ **La colonna wlroots e' stata riempita dopo** *(8 agosto 2026)*. Le celle «da misurare» qui sopra
> hanno una risposta in **`STUDI.md` §xfce §12**, che rifa' queste quattordici domande con la colonna
> wlroots piena, e in **`STUDI.md` §lxqt §4** per il caso in cui il compositore lo scegliamo noi. Questa
> tabella non e' stata riscritta di proposito: le due letture stanno bene una accanto all'altra, e
> ciascuna porta la data della propria misura.

⭐ **La 13 e la 14 sono la stessa domanda in due vesti: *chi possiede la cosa?***  È la differenza
che ha deciso metà del lavoro su KDE — non «come si fa», ma «di chi è». Dove la cosa appartiene al
compositore invece che alla nostra sessione, cambia chi comanda: la misura la **subiamo**, la
clipboard la troviamo **già lì**. Si chiede per prima, insieme alla 4 e alla 6.

**Le domande 4 e 6 vanno fatte per prime**, e insieme: senza la 4 non si sa se il numero della 6 è
confrontabile. Il modo di rispondere alla 4 è guardare quali nodi DRM il processo ha aperto e quali
librerie ha caricato — non fidarsi di quel che il compositore scrive nel proprio registro.

> ## ⚠ La colonna di KWin è stata riempita leggendo il codice, il 7 agosto 2026
>
> Lo studio sta in **[`STUDI.md` §kde](STUDI.md#kde)**, ed è la prova che questa lista funziona: **undici domande
> su undici hanno una risposta prima di scrivere una riga**. Ma tre cose vanno dette, e sono lezioni
> a loro volta.
>
> **1. Una lettura di codice non è una misura, e non la sostituisce.** Le celle marcate `[R]` dicono
> che cosa il compositore *può* fare, non che cosa *fa* sulla nostra macchina. La riga 4 era il caso
> limite: la misura diceva «software», il codice diceva GPU. ✅ **La sera dello stesso giorno la
> misura è stata rifatta, e il codice aveva ragione**: era la *misura* a essere sbagliata (§1.9).
>
> **2. La domanda 4 va posta con lo strumento giusto, e su KWin ce n'è uno migliore**: il **tipo di
> buffer** che il flusso di cattura riesce a offrire. Il DMA-BUF è possibile *solo* con un backend
> EGL, quindi risponde alla domanda 4 senza chiedere niente al compositore — mentre «quali nodi DRM
> ha aperto» richiede di guardare il processo giusto nel momento giusto, che è precisamente dove la
> nostra misura è inciampata. ⚠ **Ma attenzione al verso**: la prova vale solo se **il cliente
> offre** il DMA-BUF. Sul banco del 7 agosto il flusso ha negoziato `MemFd` con un compositore che
> era **in GPU** — perché il limite era del nostro cliente. «Solo MemFd ⇒ CPU» si può concludere
> **solo dopo** aver verificato che il DMA-BUF sia stato chiesto.
>
> **3. Alla lista mancava una domanda, e su KDE è quella che costa più di tutte:**
> **«si può cambiare la misura dello schermo virtuale a cattura viva?»** Su Mutter sì
> (`pw_stream_update_params`), e la fase 6 ci ha costruito sopra la risoluzione dinamica. Su KWin
> **no**: un output virtuale ha un solo modo, immutabile, e va chiuso e ricreato (`STUDI.md` §kde §8). È la
> **dodicesima domanda**, e chi apre il prossimo desktop la faccia insieme alla quinta.

**Gli strumenti per rispondere esistono già** e stanno in `fondamenta/banchi/banco-compositori/` — portati
qui dal server l'8 agosto 2026, quando la macchina di prova è stata ripulita: sorgenti, script e
binari già compilati, fuori dal prodotto:

| | |
|---|---|
| `misura-cattura` | consumatore PipeWire che conta i fotogrammi e dice tipo di buffer, danno, buffer riciclati, se il disegno era finito, e la distribuzione degli intervalli. Sa montare da sé lo schermo virtuale di Mutter, oppure agganciarsi a un nodo qualunque |
| `nodo-kwin` | client del protocollo di KWin; con `--elenca` stampa tutti i protocolli che un compositore annuncia |
| `misura-wlroots` | client `wlr-screencopy` che fa la stessa misura sul modello a tiro |
| `banco.sh`, `banco-altri.sh`, `banco-catena.sh` | la cattura sola, gli altri compositori, e la catena intera fino al client |

---

## 4. Le trappole del compositore, in ordine di quando mordono

Sono di Mutter, ma la **forma** si ripresenterà: cambieranno i nomi, non i modi di fallire.

| # | La trappola | La forma generale, che è la parte utile |
|---|---|---|
| 1 | La sequenza di creazione della sessione non ammette permute | **ogni permuta è punita con un errore diverso**, e nessuno dei due dice «hai sbagliato l'ordine» |
| 2 | Ci si iscrive all'annuncio del nodo **prima** di avviare il flusso | un annuncio che arriva *durante* una chiamata: chi si iscrive dopo aspetta per sempre qualcosa di già passato |
| 3 | I metadati **si chiedono**, o non arrivano | e chiedere non obbliga a dare: chi legge deve reggere la loro assenza |
| 4 | Il tipo di buffer si concorda in **due** posti | dichiararne uno solo fa **riuscire** la negoziazione con dentro il contrario di quel che si voleva |
| 5 | Lo *stride* si legge dal buffer, mai calcolato | il produttore allinea le righe come gli conviene; dedurlo dà immagini oblique |
| 6 | Il compositore deve disegnare sulla **scheda giusta** | un buffer di un'altra scheda non è importabile, e il sintomo è composizione in software senza un errore |
| 7 | Il gestore di sessione di systemd **non aggiorna i gruppi** di un processo già vivo | il compositore non apre `/dev/dri`, disegna in software, e nessuno lo dice |
| 8 | Un fotogramma arriva **solo se qualcosa cambia** | l'ultimo va conservato e rispedito, o chi si collega a un desktop fermo resta al nero **finché non si muove qualcosa** — e allora si corregge da sé, il che lo fa sembrare un ritardo d'avvio |
| 9 | Dopo un cambio di misura il primo fotogramma è **parziale** | non si aspetta un silenzio: si aspetta un **evento**, e ne bastano due |
| 10 | Le richieste di ridimensionamento **fanno eco** | ogni sistema che risponde con latenza a chi non conosce ancora la risposta si rincorre da solo; serve assestamento **più** una guardia sull'eco |
| 11 | Ridimensionare **non deve** rifare la cattura | rifarla trascina con sé il controllo, i dispositivi di input e lo stato dei tasti premuti |

---

## 5. Le trappole che non sono del compositore, ma ti aspettano lì accanto

| | La lezione |
|---|---|
| **Il bus di sessione** | non sopravvive a un logout: l'oggetto vecchio non dà errore, **dà silenzio**. E sulla connessione condivisa la libreria può chiamare `raise(SIGTERM)` per conto tuo |
| **L'ambiente** | chi avvia una sessione **le regala tutto il proprio ambiente**, comprese le variabili che non c'entrano: una locale sbagliata ereditata da uno script ha impedito a tutte le applicazioni di partire. Si compone da zero, una variabile per volta |
| **Il ciclo asincrono** | non si aspetta mai dentro: né esplicitamente, né in un distruttore che aspetta la fine di un thread |
| **La priorità** | il percorso audio vuole tempo reale, e va **concesso dall'unità** di sistema: un processo senza quel permesso non può chiederlo, e il sintomo è audio che scoppietta *quando il desktop lavora* |
| **Chi sopravvive al logout** | non riusa **niente** della sessione morta |
| **Il volume, e dove sta la presa** | ⭐ un nodo audio applica il volume **a valle della presa del monitor**: chi cattura il monitor riceve il segnale a fondo scala qualunque cosa dica il cursore, **mute compreso**. La proprietà che sposta la presa esiste ma vale `false` di suo, e i moduli di compatibilità PulseAudio la mettono al posto tuo — quindi **una prova fatta su un sink creato con `pactl` assolve un codice che crea il sink a mano**. Si misura sul proprio, non su uno equivalente |

---

## 6. Le lezioni sulle prestazioni

### 6.1 Il tetto era un numero che avevamo scritto noi

Per due mesi i fotogrammi mancanti sono stati cercati nel codificatore, nel protocollo, nella rete e
nel telefono. Erano nella cadenza massima che dichiaravamo alla cattura: chiedendone 30 ne
arrivavano 18, chiedendone 60 ne arrivano 37.

**La regola che ne discende**: prima di ottimizzare un anello, misurare **quanto entra** in quella
catena. Un anello più veloce di quel che gli arriva non produce niente.

> ⭐⭐ **E il 13 agosto 2026 la lezione si è avverata una seconda volta, sul numero che questa
> sezione cita.** *«Chiedendone 60 ne arrivano 37»* non è un tetto: `[M]` **non si riproduce
> affatto** — alla cadenza che chiedevamo ne arrivano **31,5**, e chiedendone **90 a un monitor a
> 120** ne arrivano **61,4**. ⚠ **Il perché è `[R]`**: nel codice di Mutter il freno calcola
> `min_interval_us = 10⁶/maxFramerate` **troncato a intero** (16666 per 60) contro un tick da
> 16666,67 µs ⇒ chi cade sotto **perderebbe un tick intero** — il resto di una **divisione
> troncata**. *La sera del 13 agosto questa spiegazione era scritta qui come misurata: non lo è,
> vedi il riquadro di §3 domanda 7 e `STUDI.md` §gnome §8.2.*
>
> ⇒ ⛔ **Il tetto era di nuovo un numero che avevamo scritto noi, e stavolta era scritto due volte**:
> una nella cadenza che chiedevamo, e una **nel modo in cui il compositore la converte**. La forma
> generale della lezione si allarga: non basta chiedersi *«quale numero abbiamo dichiarato?»*, va
> chiesto **«che cosa ne fa chi lo riceve?»** — perché un troncamento non si vede né nel nostro
> codice né nel numero che abbiamo scritto.

### 6.2 Millisecondi di CPU per fotogramma e fotogrammi al secondo sono due grandezze diverse

E possono muoversi in direzioni opposte. Misurato due volte:

| | CPU per fotogramma | fotogrammi al secondo |
|---|---|---|
| togliendo la codifica dalla CPU (fase 9) | 41 → 20 | 29 → **22,7** |
| accendendo la copia zero (fase 9, poi verificata sulla catena intera) | 16 → **3** | 32,4 → **31,5** |

**Un guadagno che si paga in fluidità non è un guadagno**, e va detto invece di mostrare il solo
numero della CPU. La copia zero vale cinque volte sul consumo e **zero** sul ritmo: chi la riprende
lo faccia per quello.

> ### ⛔⛔ E il 13 agosto 2026 è arrivato **il caso rovescio**: il ritmo sale, il ritardo **non si muove**
>
> *Le due righe qui sopra sono dello stesso segno: la CPU migliora e il ritmo peggiora. Servivano a
> impedire di vendere un guadagno di CPU come un guadagno di fluidità. ⛔ **Manca il caso opposto, e
> alla fase 3 ci si è quasi cascati.***
>
> | la leva | il ritmo | il ritardo |
> |---|---|---|
> | la cadenza disaccoppiata (monitor 120, freno 90) | ⭐ **da 31,5 a 61,4/s** | ⛔ **fermo** |
>
> ⛔ **Raddoppiare i fotogrammi al secondo non ha tolto un millisecondo al ritardo**, e la ragione è
> che il collo era altrove: la gran parte del ritardo era nostra, quasi tutta nel codificatore in
> software. *(I millisecondi misurati allora dipendevano dalla codifica senza scheda di libavcodec e non
> valgono più dopo la fase 18.)*
> I 60 fotogrammi **tolgono un ostacolo**; il numero che l'utente sente lo fa il ritardo.
>
> ⇒ ⭐ **La lezione, nella forma che le mancava: sono TRE grandezze, non due.** Millisecondi di CPU
> per fotogramma · fotogrammi al secondo · **ritardo**. Si muovono indipendentemente, e ciascuna
> coppia ha già prodotto una riga sbagliata in un documento di questo progetto.
>
> ### ⛔⛔ E la stessa sera è arrivato il caso che le fa dire cose OPPOSTE — la pagina nel worker
>
> *Si era deciso di tenere la tela sul thread principale (`DECISIONI.md` §2.8); le misure, prese con la
> codifica in software, non valgono più dopo la fase 18 e la tabella è tolta. Resta il verso.* *→ la catena in software, rifatta in 4K: `fasi/18-senza-ffmpeg.md` §5.4.*
>
> ⛔ **Sulla catena vera il worker dipingeva di più e sembrava migliore. A saturazione era di gran lunga
> peggiore. E il ritardo diceva che era peggiore comunque.** ⇒ ⚠ **Quale conclusione si porta a casa dipende da quale grandezza
> si è scelta per prima** — che è il modo più educato in cui una misura può mentire.
>
> ⭐ **La regola pratica**: quando una leva tocca il percorso del video, le tre grandezze si
> **misurano e si scrivono tutte e tre**, anche quelle che non interessano. Una tabella con una
> colonna sola non è una misura corta: è una misura **orientata**.
>
> ⚠ **E il numero della catena vera aveva una spiegazione, che è la terza cosa da guardare**: il
> worker dipingeva di più perché **c'era la coda**. Un vantaggio che esiste solo finché il sistema
> non è al limite è un vantaggio che sparisce **il giorno in cui serve** (`STUDI.md` §web §6.1).

### 6.2-bis ⭐⭐ Un'attesa che protegge un anello è un ritardo per tutti gli altri

*15 agosto 2026. Trovata perché l'utente ha detto «riduci di qualche decimo di secondo il tempo fra
il clic e l'evento» — cioè per un numero che nessun banco guardava.*

Il ciclo del figlio faceva, in quest'ordine: **leggi quel che dice il padre** (senza aspettare),
poi **aspetta un fotogramma** fino a 250 ms. Sensato: il figlio è un altro processo, lì si può
aspettare, e un quarto di secondo tiene basso il consumo su un desktop fermo.

⛔ Ma l'input del padre arriva **durante** quell'attesa, e chi arriva un millisecondo dopo l'inizio
resta fermo per i 249 ms che restano. `[M]` Sui clic veri dell'utente: **mediana 136 ms**, e la
dispersione da 0 a 502 — la firma di un'attesa casuale, non di una rete lenta. Portando l'attesa a
8 ms: **mediana 41 ms**, tutti i campioni fra 34 e 47.

> **Un'attesa dimensionata su un anello (i fotogrammi) diventa il ritardo di ogni altro anello che
> passa dallo stesso ciclo (l'input). E il secondo anello non compare in nessun conto, perché il
> ciclo è stato scritto guardando il primo.**

⚠ La domanda che lo smaschera si fa **prima** di scrivere il ciclo, e costa una riga: *«che altro
entra da qui, e quanto lo faccio aspettare?»*.

### 6.2-ter ⛔ Il numero che spiega tutto può essere nel registro da un giorno

*Stessa notte, e la seconda volta in due giorni.*

La causa dei 136 ms era stampata **una volta al secondo**, in una riga che nessuno collegava:

> `ciclo: 4 fotogrammi consegnati, 3 attese a vuoto …`

Tre-quattro attese a vuoto al secondo vuol dire quattro giri al secondo, cioè 250 ms per giro. ⛔ La
riga era stata scritta per rispondere a **un'altra domanda** — «la scena è ferma, o il ciclo è
fermo?» — e conteneva la risposta a questa senza che il suo autore lo sapesse.

⚠ È la stessa forma del 14 agosto (*213 movimenti registrati dal server mentre l'utente ne vedeva
zero*, `dex-mouse-aperto`): il registro aveva già il fatto, e per due giorni nessuno l'ha letto
perché **cercava un'altra cosa**.

> ⇒ Quando un numero non torna, prima di aggiungere una misura si rilegge il registro **cercando
> quel numero**, non il difetto: le righe di riassunto sono scritte per una domanda sola, e ne
> rispondono spesso a due.

### 6.3 Il ritmo lo decide il client, se il collegamento è veloce

Il regolatore concede `MAX(2, rtt·fps/10⁶ + 2)` fotogrammi non riscontrati: su un collegamento veloce
fa **2**, quindi la portata diventa quella con cui il client riscontra. È corretto — non si somurge
un client lento — ma ha una conseguenza sul **metodo**: un banco il cui client decodifica in software
misura il client, non noi. È successo, e il numero del 4K è stato ritirato per questo.

**Prima di attribuire un tetto al server, guardare quanto lavora**: 0,08 core con la coda piena
significa che il server sta aspettando.

### 6.4 Che cosa NON costa

Alla cattura non costano **la risoluzione** (4K rende come 1080p) né **la profondità di colore**.
Quindi la scala di ripiego 4K → 2K → 1080p serve al codificatore e alla banda, **non** a guadagnare
fotogrammi. Sapere che cosa non costa vale quanto sapere che cosa costa: toglie di mezzo le leve che
non muovono niente.

### 6.5 ⭐⭐ Un'ottimizzazione che ragiona sul **regime** è cieca alla **coda** — e la coda è quel che l'utente guarda

*15 agosto 2026, fase 5. Trovata da un sintomo dell'utente, e la causa stava in un **commento
nostro** che spiegava perché era giusta.*

`cattura.c` consegnava il fotogramma **solo se qualcuno lo stava aspettando in quell'istante**, e la
riga che lo giustificava diceva: *«copiare 8 MB per nessuno sarebbe lavoro dentro la richiamata di
tempo reale, fatto per niente»*. ⭐ **Vero a regime**: se i fotogrammi scorrono, quello buttato è
subito rimpiazzato dal prossimo e nessuno se ne accorge.

⛔ **Falso nella coda**, ed è l'unico caso che si vede: una finestra che si chiude produce una
raffica; noi prendiamo il primo fotogramma e passiamo ~20 ms a comprimerlo; quelli che arrivano nel
frattempo si buttano, **compreso l'ultimo** — e dopo l'ultimo **non ne arriva nessuno**, perché la
scena è ferma e il compositore manda solo quando cambia qualcosa. ⇒ L'utente resta a guardare il
**primo** fotogramma di un cambiamento che è già finito, finché un gesto qualunque non ne produce un
altro.

**Il sintomo, com'è arrivato**: *«do `exit` e il terminale sembra congelato: appena muovo il mouse
si chiude»*. ⭐ **Quella frase è la diagnosi**: se un fotogramma qualunque allinea lo schermo, quello
giusto era stato prodotto e non consegnato.

**Le tre regole che ne restano:**

1. ⛔ **In una catena a raffiche, l'ultimo elemento non è uno come gli altri**: è quello che resta
   sullo schermo. Un'ottimizzazione che scarta «tanto ne arriva un altro» va riletta chiedendosi
   *«e se questo fosse l'ultimo?»*;
2. ⚠ **il guadagno vero è stato più grande della cura**: non si perdeva solo l'ultimo — si perdevano
   **tutti** quelli di ogni raffica, quindi ogni movimento era più a scatti del necessario, e nessuno
   l'aveva mai notato perché il difetto si vedeva solo nella coda. ⇒ *Un difetto che si manifesta in
   un caso limite può costare in tutti gli altri, in silenzio*;
3. ⭐ **e il costo temuto non c'era**: tenendo sempre l'ultimo si **riusa** il buffer, e la
   richiamata di tempo reale fa una `memcpy` invece di una `malloc`+`free` da 8 MB per fotogramma.
   *L'ottimizzazione che si difendeva col costo era anche la più cara.*

⚠ E la conferma è dell'utente, non di un banco: *«ora il terminale si chiude subito… il sistema mi
sembra tremendamente responsivo, i tempi di risposta sono istantanei anche su Android»* — §7.3, il
metro è quel che si vede.

---

## 7. Le lezioni sulla direzione

### 7.1 I numeri li pone l'utente, e la tecnica li serve

Fino al 7 agosto si sceglieva una strada tecnica e poi si misurava che cosa ne usciva. Da quel giorno
l'ordine è rovesciato: **una scelta tecnica si giustifica mostrando che avvicina uno dei numeri
dichiarati**; se non li muove, non si fa, per quanto sia elegante il guadagno che porta altrove.

### 7.2 Ottimizzare nella direzione sbagliata è peggio che non ottimizzare

Metà delle misure della fase 10 erano corrette e rispondevano alla domanda sbagliata: «spendere meno
banda» era considerato un guadagno, mentre per questo prodotto la banda dichiarata è un **pavimento,
non un budget**. Prima di ottimizzare una grandezza, **farsi dire se quella grandezza va minimizzata
o spesa**.

### 7.3 Il metro è quel che si vede

Un numero di prestazione che nessuno percepisce non giustifica il tempo dell'utente. E, all'opposto:
quando l'utente dice che va bene, **va bene** — la fase 10 è stata chiusa così, senza essere rifatta.

### 7.4 Le previsioni non contano, le misure sì — e vale anche per le nostre

Il 7 agosto era stato previsto che il client Android non avrebbe guadagnato niente dalla cadenza
nuova, con un ragionamento corretto e documentato: riceve un codec che si decodifica in software, e
che al server costa due volte e mezzo l'H.264. Il giudizio dell'utente è stato *«performance
eccellenti»*.

Il ragionamento era giusto e la conclusione no, perché partiva da un presupposto mai verificato — che
qualcuno dei due lati fosse al limite. Non lo era nessuno dei due: **lo era il numero che
dichiaravamo.**

> ⚠ **E in V2 il presupposto va rifatto da capo** *(8 agosto 2026)*. Il lato che qui non era stato
> verificato — «qualcuno dei due lati e' al limite» — cambia del tutto: `aFreeRDP` decodificava in
> software un codec che nessuno avrebbe scelto, mentre il client di V2 e' nostro e chiama MediaCodec
> su HEVC. **Il numero di v1 non era un tetto di Android: era il tetto di quel client.** Vale sia per
> la previsione sbagliata sia per il giudizio che l'ha smentita — nessuno dei due si eredita.

### 7.5 ⭐⭐ Una deduzione al posto di un messaggio è un difetto che aspetta

*15 agosto 2026, notte. Trovata refutando la cura appena scritta, e vale per l'architettura, non
per una riga.*

La catena che porta la misura della finestra fino al compositore era scritta e funzionava. Il
padre chiedeva al figlio di ridimensionare, e poi **deduceva l'esito dai fotogrammi**: *«se ne
arriva uno di misura diversa, il palco ha obbedito»*. Era fedele a una regola giusta di questo
progetto — *«la verità la dice il fotogramma, non l'esito della richiesta»* — e passava tutti i casi
che avevo in mente.

⛔ **Tre agenti mandati a smentirla hanno trovato tre casi che non avevo in mente**, e sono tutti
comuni:

| il caso | che cosa deduceva il padre |
|---|---|
| il palco ha **già** quella misura | «non ha ancora obbedito» ⇒ tre secondi di attesa per una cosa già fatta |
| il palco **non c'è** o non ce l'ha fatta | «sta ancora provando» ⇒ tre secondi per una notizia che c'era subito |
| **due richieste incatenate** (l'utente trascina il bordo) | il fotogramma della PRIMA preso per la risposta della SECONDA ⇒ desktop della misura sbagliata, **coi conti dei messaggi in ordine** |

⇒ La cura non è stata «più controlli», ed è la parte che conta: è stata **un messaggio in più**, dal
processo che sapeva al processo che decideva — con dentro *a quale domanda risponde* e *che cosa è
successo davvero*.

> **Quando un pezzo deve dedurre qualcosa che un altro pezzo sa già, la deduzione non è un
> risparmio: è un difetto che aspetta il caso a cui non hai pensato.**

⚠ E il segnale che la distingue da una deduzione legittima è **sempre lo stesso**: la deduzione
regge finché gli eventi sono uno per volta, e cade appena se ne accavallano due. Se il caso «due
richieste in volo» non ha una risposta ovvia, la deduzione va sostituita da un messaggio.

---

## 8. I vicoli ciechi già percorsi — da non rifare

| Che cosa | Esito |
|---|---|
| Limitare il server a una versione EGFX più bassa per confronto con mstsc | vicolo cieco: su quella versione mstsc spegne l'H.264 |
| Dare più thread alla conversione di colore in CPU | rumore: 13,8 ms contro 12,5. Quel tempo non è di calcolo, è di memoria |
| Aspettare la *fence* implicita del DMA-BUF | non cambia niente: è quella sbagliata. La esplicita viaggia in un metadato che non chiedevamo. ⚠ **Corretta il 9 agosto**: questa riga copre metà del contratto — l'*acquire*. Quel che manca è il **release**, e sta dall'altra parte (vedi il riquadro qui sotto) |
| Adattare la **risoluzione** alla banda | non realizzabile: lo scaled output lo rende un client su tre, e ridimensionare il monitor virtuale ridispone le finestre dell'utente |
| Dichiarare alla cattura una cadenza **fissa** invece di «quando cambia» | Mutter la rifiuta: nessun formato negoziato, zero fotogrammi |
| Alzare la cadenza dichiarata **oltre 60** | non dà niente: 120 dichiarati, 37 consegnati come con 60. ⚠ **Non chiude la strada della cadenza**: alzare il numero *una volta sola* alza tutt'e due gli orologi insieme, ed è il battimento a mangiare il guadagno. Il candidato di §3 è un'altra mossa — **rinegoziare la sola cadenza, a monitor fermo** |
| Cercare il collo di bottiglia dei fotogrammi nel codificatore, nel protocollo o nella rete | era nella nostra costante |

⚠ **Due di queste righe erano di RDP, non del problema** *(8 agosto 2026)*, e vanno lette con
attenzione perche' le altre cinque valgono ancora per intero.

| Riga | In V2 |
|---|---|
| la versione EGFX abbassata per mstsc | **decade**: non esiste ne' EGFX ne' mstsc |
| adattare la **risoluzione** alla banda | **decade a meta'**. Il primo motivo era che lo *scaled output* lo rendeva un client su tre — e i client ora sono nostri, quindi la scalatura lato client si puo' avere. Il **secondo motivo resta intero**: ridimensionare il monitor virtuale ridispone le finestre dell'utente, e quello non lo cambia nessun protocollo |
| le altre cinque | **restano**: parlano di thread, di *fence*, di Mutter e della nostra costante — nessuna di loro nominava RDP |

⛔ **E nessuna riga si cancella.** Un vicolo cieco documentato costa meno di uno riscoperto: il
giorno in cui qualcuno riproporra' «adattiamo la risoluzione alla banda», questa tabella dira' che
in v1 non si poteva e **obblighera' a dimostrare che in V2 si puo'** — che e' esattamente il lavoro
che la riga deve far fare.

> ## ⭐ Un vicolo cieco che non era un vicolo cieco: la caccia della fase 9, nel posto sbagliato
>
> *Scritto il 9 agosto 2026 da `STUDI.md` §gnome §1.3 e §8.1. `[R]`, e riapre una caccia chiusa male.*
>
> Le due schermate che si alternavano sono state inseguite per due fasi come un problema di
> **acquire**: il buffer arriva col disegno in corso, quindi si aspetta la fence. La lettura del
> codice dice che il difetto è dall'altra parte, ed è un **release**: `can_reuse_pw_buffer` —
> l'unico punto in cui Mutter aspetta noi — **si arrende alla prima riga** se manca
> `SPA_META_SyncTimeline`, e riusa il buffer **mentre VA-API lo sta ancora leggendo**.
>
> ⛔ **E spiega perché la cura peggiorava le cose**: la superficie di accumulo copiava i soli
> rettangoli danneggiati da un buffer che conteneva **già il fotogramma intero** (domanda 8).
>
> **Due cure candidate, entrambe piccole**: chiedere `SPA_META_SyncTimeline` — che Mutter
> **offre**, e che oggi non chiediamo — oppure **trattenere** il `pw_buffer` fino a lettura
> finita, che è quel che fa il riferimento, cioè il contrario di quel che avevamo concluso.
>
> ⚠ **È una lettura, non una misura**, ed è la lezione 4 di `STUDI.md` §gnome §14: *una misura giusta
> con una spiegazione inventata è più pericolosa di una misura sbagliata*, perché nessuno la
> rimette in discussione. R29 è rimasta in piedi due fasi per questo.

---

## 9. La ricetta, per aprire il supporto a un desktop nuovo

Nell'ordine, e ogni passo è una lezione delle sezioni precedenti messa in fila.

0. **Cercare chi l'ha già fatto — fuori da quel che si è già clonato.** *Aggiunta il 7 agosto 2026,
   e pagata lo stesso giorno*: lo studio di KDE ha concluso «in KDE non c'è traccia di RDP» dopo aver
   cercato **dentro gli otto repository che avevo scelto io**. Il riferimento principale — `KRdp`, il
   server RDP di KDE, stessa libreria, stesso compositore, 4 200 righe — stava in un nono repository,
   e a trovarlo è stata una domanda dell'utente. **La domanda giusta non è «c'è nei repo che ho?» ma
   «chi, al mondo, fa questa cosa su questo desktop?»** — e si fa prima di leggere, non dopo.
1. **Rispondere alle quindici domande della sezione 3**, con gli strumenti che ci sono già. Un
   pomeriggio, prima di scrivere una riga di prodotto. Le domande 4 e 6 per prime, e la 3 insieme
   alla 15 — *«c'è un permesso?»* e *«può essere ritirato a caldo?»* sono la stessa indagine.
   *(Diceva «undici»: erano quelle del 7 agosto, prima che gli studi ne aggiungessero quattro —
   9 agosto 2026.)*
2. **Accertare come disegna senza monitor** (GPU o software): decide se i suoi numeri sono
   confrontabili con quelli di GNOME, e se quel desktop è servibile su una macchina da server.
3. **Trovare la strada diretta al compositore**, senza portale — e scoprire subito se è dietro un
   permesso, perché il sintomo è «questo compositore non ha il protocollo» e fa perdere un
   pomeriggio a chi non se l'aspetta. ⭐ **E quando nega, la prima mossa non è provare varianti: è
   accendere il registro del componente che nega e farsi dire la causa** (§1.10). Su KWin sono tre
   secondi, e le due righe possibili hanno cure opposte.
4. **Misurare la sola cattura**, con la scena dichiarata e il conteggio di quanto disegna il client.
   Solo dopo rimettere dentro il codificatore e il filo.
5. **Riusare i banchi delle fasi che attraversano lo stesso percorso**: una fase che tocca un
   percorso condiviso si chiude rieseguendo i banchi di chi quel percorso lo attraversava già.
6. **Provare sui tre client**, e su almeno due connessioni di fila.
7. **Far giudicare l'utente**, su quel che si vede, prima di dichiarare chiuso qualunque cosa.
8. **Aggiornare i documenti nello stesso momento** in cui una misura li smentisce, con data e fonte.
   Un riferimento che invecchia in silenzio è peggio di nessun riferimento.

### 9-bis ⭐⭐⭐ Quel che NON è del desktop, e ti aspetta lo stesso

*Scritta il 15 agosto 2026, alla fine di una notte in cui il desktop remoto è sparito tre volte.
⛔ **Di tutto quel che è costato, quasi niente era di GNOME**: era del sistema sotto — logind, PAM,
udev, Mesa, PipeWire. ⇒ Su KDE, XFCE, LXQt e Cinnamon queste righe **si ripagano tali e quali**, e
questa sezione esiste perché non si ripaghino due volte.*

| il fatto | quanto è portabile | dove sta scritto |
|---|---|---|
| ⛔ **Il compositore vuole una SESSIONE logind di classe `user`** — non basta `/run/user/<uid>`, non basta il bus, **non basta il linger** (che dà uno scope di classe `manager`). Mutter chiede `sd_pid_get_session()`, si sente rispondere **ENXIO** e muore | ⭐⭐⭐ **totale**: quella chiamata la fa **ogni** compositore Wayland, non Mutter. È la prima cosa da verificare su un desktop nuovo, e il sintomo — *«non parte e non dice perché»* — è identico ovunque | `DECISIONI.md` §1.10-ter |
| ⛔ **Il server non deve girare dentro una sessione utente**: `pam_systemd`, se chi chiama sta già in una sessione, **non ne crea una seconda e non lo dice**. Un server avviato a mano da `ssh` mette i figli nella sessione di chi l'ha avviato | ⭐⭐⭐ **totale**, ed è insidiosa perché in produzione (unità di sistema) non si vede mai: morde **solo in prova**, cioè dove si studia il desktop nuovo | `DECISIONI.md` §1.10-ter |
| ⛔ **Senza seat non ci sono le ACL di `uaccess`** ⇒ l'utente **non può aprire la GPU** e Mesa ripiega su llvmpipe **senza un errore**. Su un desktop normale l'accesso lo dà logind con un'ACL a chi è seduto al seat; noi il seat non ce l'abbiamo **di proposito** | ⭐⭐⭐ **totale**, ed è il **prezzo dell'headless**: vale per qualunque compositore si faccia girare senza seat. ⚠ Il sintomo è «lento», non «rotto» | `FASI.md` §05-la-sessione, `DECISIONI.md` §4.6-quinquies |
| ⛔ **Con due schede, quale usa il compositore lo decide il caso** se non c'è la regola udev | ⭐⭐ **totale** — e su KWin era già noto (`STUDI.md` §kde §5.6: `findRenderDevice()` prende la prima che si apre). ⇒ Non era una stranezza di KDE: **era la regola generale, vista da una parte sola** | `DECISIONI.md` §4.6-ter e §4.6-quinquies |
| ⛔ **Le variabili `XDG_*` non si inventano: le mette `pam_systemd` e si leggono.** Comporle a mano vuol dire dichiarare un valore al posto di averlo — e `XDG_RUNTIME_DIR` asserito è il difetto che non si vede finché la directory c'è | ⭐⭐⭐ **totale** | `DECISIONI.md` §1.10-ter |
| ⛔ **La coda della raffica**: il fotogramma scartato «tanto ne arriva un altro» è **l'ultimo**, e dopo l'ultimo non arriva niente | ⭐⭐⭐ **totale**: sta in `cattura.c`, che è **lo stesso codice per tutti e quattro** i desktop | §6.5 |

⭐ **E la conseguenza di metodo, che vale più dell'elenco**: quando su un desktop nuovo qualcosa non
parte o va lento, ⛔ **la prima domanda non è «che cosa fa di strano questo compositore»** — è
*«l'ambiente sotto è quello che il compositore si aspetta?»*: sessione, seat, gruppi, scheda,
variabili. `[M]` Su GNOME, la notte del 15 agosto, la risposta è stata **quattro volte su cinque
l'ambiente** e una volta il nostro codice — e ogni volta il sintomo puntava altrove.

⚠ **E il rovescio, per onestà**: quel che invece **è** di GNOME e non si trasporta — `--headless
--no-x11`, il drop-in dell'unità della Shell, `is_headless()`, le chiavi di lockdown,
`always-show-log-out`, le dodici `switch-to-session-*` — va cercato di nuovo su ciascun desktop, e
per quello servono le quindici domande della sezione 3.

---

## 9-bis. ⛔⛔⭐ §1.18 — Quattro banchi verdi che misuravano **la stessa strada**

⛔ Il 20 agosto quattro banchi dichiaravano verde la clipboard nei due versi, su tutti e due i
motori. Il 21 agosto l'utente ha scritto: *«funziona l'incolla con ctrl+v, ma non con il mouse e
scegliendo dal menu la voce "incolla"»*. ⇒ Tutti e quattro battevano **`Ctrl+V`**.

⚠ Non erano banchi sbagliati: erano **quattro copie dello stesso banco**, con quattro nomi diversi.
La ridondanza dava l'impressione della copertura e non ne aggiungeva un millimetro.

⭐ **La domanda che li avrebbe smascherati in un minuto**: *«qual è il GESTO che fa partire questa
strada, e ce n'è più d'uno?»* Per gli appunti i gesti sono due — un tasto sul browser e una voce di
menu **dentro il video** — e sono due strade **che non si incontrano mai**: la prima nasce nel
browser, la seconda nasce dall'altra parte del filo e torna indietro come una domanda del server.

⇒ Un banco per **strada d'ingresso**, non un banco per funzione. E quando un banco nuovo diventa
verde al primo colpo, il sospetto giusto non è «bravi noi»: è *«sto rifacendo un banco che c'è
già?»*.

⚠ E lo stesso giorno, sullo stesso difetto, **due difetti del banco avrebbero dichiarato rotto un
prodotto sano**: Chrome che si attacca alla sessione grafica vera invece che allo schermo del banco
(`--ozone-platform=x11`), e un clic dato secondi prima della misura, quando l'attivazione
transitoria del browser era già scaduta. ⇒ §1.2 di nuovo, e non è un caso: il banco che scopre una
strada nuova è **giovane**, e va certificato prima di credergli — in tutt'e due i versi.

## 9-ter. ⛔ §1.19 — **Chi apre, chiude**: i banchi lavorano sul desktop di una persona

*21 agosto 2026, dall'utente, guardando il suo schermo: «Che diavolo succede? È come se si
aprissero terminali infiniti».*

⛔ Erano i banchi. Un desktop fermo non manda fotogrammi, quindi per misurare il video serve
qualcosa che si muova: un terminale che scorre. ⚠ Lo accendevo **a mano** a ogni giro, e nessuno lo
spegneva — dopo dieci giri, **dieci terminali e dieci cicli infiniti sul desktop di qualcuno**.

⇒ La regola, e vale per ogni banco che tocchi la sessione di prova:

| | |
|---|---|
| **chi apre chiude** | la scena la accende il banco e la spegne il banco, in un `finally` — anche se il banco è caduto |
| **si spegne quel che si VEDE, non solo quel che gira** | ⛔ `pkill` sul processo che scriveva lasciava in piedi la finestra che lo mostrava |
| **il posto si libera** | la sessione del banco tiene occupato l'unico posto, e il banco dopo misurerebbe una pagina che non si è potuta collegare |

⚠ E c'è una ragione in più perché questa non è pignoleria: la sessione di prova è **la stessa** che
l'utente guarda. Un banco che lascia rifiuti lì dentro non sporca un ambiente di prova — sporca il
posto di lavoro di una persona, e le fa perdere tempo a capire che cosa sia stato.

## 10. E una lezione sola su tutto il resto

Il progetto non si è mai fermato su un problema difficile.

Si è fermato, ogni volta, su **una misura che non misurava quello che credevamo**: un banco verde con
il difetto vivo, un contatore che pesava il nulla, un campione preso all'avvio, una scena che non si
muoveva, un mittente dedotto invece che chiesto, un tetto attribuito al compositore che era una
nostra costante.

Il tempo speso a certificare lo strumento è sempre stato meno di quello speso a inseguire le sue
bugie.

---

### 1.29 ⛔⛔⛔ **«Silenzio invece di rosso»: la forma che hanno NOVE difetti di banco su nove**

*23-24 agosto 2026, fase 9. In due giorni sono stati trovati nove difetti nei banchi. ⛔ **Non uno
di essi faceva fallire un banco**: tutti e nove lo facevano **tacere, o dare verde**, e nessuno
avrebbe mai attirato l'attenzione da solo.*

| dove | che cosa |
|---|---|
| `07-b64` | `a_non_si_apre` guardava `ricevuti == 0` — ma il cliente stampa *«ricevuti 0»* **anche dal ramo `except`** ⇒ **ogni** modo di fallire dava **verde** |
| `07-b64` | il primo profilo della griglia **disarmava il guardiano** ⇒ gli otto dopo giravano senza rete di sicurezza |
| `07-b64` | `spediti_dal_server` a `None`: `None == 0` è **falso** ⇒ verde su un giro in cui il capo del server non era stato letto |
| ⛔ `07-b64` | la riga di «conto finale» arriva **fino a 29 s tardi** quando il pacer ha coda ⇒ il giro dopo legge **il conto del giro prima**. `[M]` Tre profili di fila hanno riferito **gli stessi identici numeri**, e un predicato ha dato **rosso su un denominatore altrui** |
| `09-b70` | `sudo -S` copre solo il **primo** anello della catena ⇒ il lettore della traccia **non si scriveva** |
| ⛔ `09-b70` | un `< file` in coda **ruba lo stdin a `sudo -S`** ⇒ la funzione torna **0 in silenzio**, e il contatore diventa **cumulativo dall'accensione**: `[M]` 4 041 invece di 1 604 |
| `09-b70` | un file non spedito dal terreno ⇒ giornale vuoto ⇒ **rosso su una sessione viva da 797 fotogrammi** |
| `09-b76` | il predicato misurava **la durata della consegna** e la chiamava **«stacco»** |
| `09-b84` | la riga dello stato **spento** conteneva la parola `ACCESA` (in *«dal 24 agosto nasce ACCESA»*) ⇒ il banco avrebbe letto **acceso su un braccio spento**, e quel predicato era **l'unica cintura** |

⭐⭐ **La regola che ne esce, e non è «scrivete meglio i banchi»:**

> ⛔ **Un banco non è finito finché non lo si è visto dare ROSSO.** Ogni predicato deve avere, in
> `--certifica`, il caso che lo fa fallire — e quel caso va **fatto girare**, non immaginato.

E tre corollari, ciascuno pagato:

1. ⛔ **`None` non è zero, e «non ho letto» non è «non è successo niente».** Metà dei nove nascono
   da questa confusione. Una funzione che non ha potuto misurare deve tornare **`None`** e il banco
   deve **rifiutarsi di giudicare**, mai tirare dritto con uno zero;
2. ⛔ **La guardia va dove il numero SI CONSUMA**, non dove si produce: se un altro banco sostituisce
   la tua funzione con la sua, la guardia messa dentro la tua **non gira più**;
3. ⭐ **Cercare una parola dentro un testo è fragile**: `"ACCESA" in dettaglio` è vero anche quando il
   dettaglio spiega che *nasce* accesa **ed è spenta**. Ci si àncora alle **frasi di stato**, non alle
   parole.

### 1.30 ⛔⛔⭐ **Una prova che non morde dà un giudizio che sembra un risultato** — e si smaschera contando

*24 agosto 2026, fase 9. Tre prove di fila hanno prodotto un giudizio dell'utente **valido come
frase e vuoto come misura**, e nessuna delle tre lo dichiarava.*

| la prova | il giudizio | ⛔ perché non valeva |
|---|---|---|
| perdita all'1 %, desktop vero | *«mi sembra ok»* | `[M]` i suoi fotogrammi pesavano **242-283 byte**: la perdita **non aveva niente da rompere** |
| trascinare una finestra | — | `[M]` picco **3 801 byte**, contro i **25 000** su cui il banco crollava |
| perdita al 5 % | *«è tutto fluido»* | `[M]` dentro il guasto erano passati **221 pacchetti, 18 buttati**. **Diciotto pacchetti non sono una prova** |

⭐ **Il rimedio è banale e va messo PRIMA di chiedere il giudizio**: contare **quanta
sollecitazione è davvero arrivata**. Qui: i pacchetti passati nel `netem` e i byte per fotogramma.
`[M]` Rifatta con trenta secondi di movimento continuo, la stessa prova ha dato **7 596 pacchetti,
423 buttati, fotogrammi fino a 77 KB** — e allora il *«è tutto fluido»* è diventato un risultato.

⛔⛔ **E il corollario che vale più della lezione**: il gradino non lo decide **il guasto**, lo decide
**quanto la scena chiede**. Un banco che pretende 40 fotogrammi/s di cambiamento continuo e un
desktop vero che cambia a strappi **non sono la stessa sollecitazione**, e `[M]` fra i due c'è **un
ordine di grandezza**: il banco metteva il crollo allo 0,9 % di perdita, l'utente lo ha trovato fra
il 5 e il 10 %.

### 1.31 ⭐⭐⭐ **Il difetto non comincia dove si vede — e la colonna che avvisa non è quella che si guarda**

*24 agosto 2026, fase 9.* `[M]` La spirale di chiavi parte fra lo **0,00 % e lo 0,10 %** di perdita
— cioè **al primo pacchetto perso** — mentre i fotogrammi al secondo restano buoni fino allo
**0,53-0,75 %**.

⇒ ⛔ **Un banco che guardasse solo i fotogrammi al secondo avrebbe dato verde fino allo 0,5 %**, con
il prodotto che nel frattempo degenerava in sole chiavi — cioè degradava **nello spazio e nel tempo
insieme**, che la specifica vieta.

⭐ **La regola**: quando si misura un fenomeno con un **meccanismo** e un **sintomo**, si porta la
colonna del meccanismo **accanto** a quella del sintomo, sempre. Il sintomo dice quando l'utente se
ne accorge; **il meccanismo dice quando è cominciato**, e fra i due qui c'è un fattore **cinque**.

### 1.32 ⭐⭐⭐ **«A volte succede» spesso vuol dire «succede sempre, aspetta solo il momento»**

*24 agosto 2026, fase 9.* Un fenomeno appariva **bistabile**: stesso ingresso, stesso binario, stesso
terreno, e a venti minuti di distanza **`0 chiavi · 40,16/s`** oppure **`24 chiavi · 33,84/s`**.

⛔ **Cercarne la causa nei primi dieci secondi ha dato 43 prove negative su 43** — e la ragione era
che **5 accensioni su 13 cadevano dopo il decimo secondo**: in quella finestra non c'era niente da
trovare.

⭐⭐ **La forma giusta era un'altra**: non due rami, ma **un innesco a senso unico con rischio
costante**. `[M]` Provato a due durate — a **10 s** succede nel **35 %** dei giri (atteso 31 %), a
**50 s** nel **90 %** (atteso 92 %) — con λ = **0,053 al secondo** e mediana **13 s**.

> ⛔⛔ **E il conto che ne segue tocca ogni misura**: i banchi girano **venticinque secondi**, le
> sessioni dell'utente durano **ore**. ⇒ Ogni numero preso vicino al bordo **sottostima**, e non di
> poco: quel che al banco sembra *«a volte»*, in una sessione vera è **certo**.

⭐ **La prova che distingue le due letture costa un'ora**: si ripete la stessa casella a **due
durate** e si guarda se la frazione segue l'esposizione. Se la segue, «bistabile» è la parola
sbagliata — e con essa ogni conclusione tratta da giri corti.

### 1.33 ⛔⛔ **Il metro va tarato PRIMA, e i due errori non costano uguale**

*24 agosto 2026, fase 9. Due misure della stessa giornata, e la differenza fra loro è tutta qui.*

⭐ **Quella andata bene**: prima di misurare lo sfalso audio-video, si sono **iniettati sette ritardi
noti** e verificato che il metodo li ritrovasse — sul file, poi ricampionato, poi ⭐ **attraverso il
prodotto vero**. `[M]` Pendenza **0,9988**, costante **−11,6 ms**. ⇒ Da quel momento ogni numero
aveva un errore dichiarato, e la misura ha potuto **smentire** la lettura precedente.

⛔ **Quella andata male**: una soglia scelta su una grandezza **mai messa alla prova sui casi
estremi**. `[M]` `pkt_lost/pkt_sent` ordinava i due casi **al contrario** — una linea che **regge**
ne dichiarava il **512‰** contro il **123‰** di una che **non regge**, perché ngtcp2 conta un
pacchetto **sorpassato** come perso. ⇒ **Nessuna soglia poteva separarli**: non era una taratura da
rifare, era la grandezza sbagliata.

⭐⭐ **E la regola sull'asimmetria, che è la parte trasferibile:**

> ⛔ Quando una soglia decide qualcosa di **irreversibile** — chiudere una sessione, buttare fuori
> qualcuno — **i due errori non costano uguale**. Sbagliare dal lato prudente costa qualche secondo
> in più; sbagliare dall'altro **butta fuori chi stava lavorando**. ⇒ La soglia si mette **sopra** il
> centro fra i due estremi misurati, e il margine si scrive **da tutt'e due i lati**.

⚠ E il margine si àncora al **caso peggiore che regge**, non al più comodo: `[M]` il lato stretto è
stato preso sul **più corto** dei due stalli osservati, perché un margine scritto sul numero
fortunato non è un margine.


---

### 1.34 ⭐⭐⭐ **Una grandezza che satura smette di informare — e allora si guarda la DOMANDA, non l'offerta**

*24 agosto 2026, fase 10.*

⛔ Il motore video della scheda è stato misurato al **99,5 %** in tutti e tre i cedimenti. ⇒ La
colonna diceva *«pieno»* — ⛔ **e da lì in poi non ha più detto niente**: pieno al primo cedimento e
pieno al terzo, con **tre carichi diversi** e tre soffitti diversi dietro.

⭐⭐ **La cura è cambiare capo alla misura**: non *«quanto è occupato il motore»* — che si ferma a
cento — ma ⭐ **quanti pixel al secondo gli sono stati CHIESTI**. Quella grandezza **non satura**, e
continua a ordinare i casi anche oltre il punto in cui l'altra si è appiattita.

`[M]` **Con la domanda al posto dell'offerta i tre cedimenti si sono allineati entro lo 0,6 %**
(1855,9 · 1865,8 Mpixel/s a due risoluzioni diverse), dove i fotogrammi al secondo differivano del
**74,9 %**. ⇒ ⭐ **La moneta giusta rende confrontabili scene che sembravano incomparabili.**

> ⚠ **E il tranello che ci sta accanto**: una colonna satura invita a **estrapolare la retta** dai
> punti di carico leggero. ⛔ Quella retta **non passa per il cedimento**: nella stessa fase
> l'estrapolazione dava **~46 sessioni** dove il misurato ne dava **11**, cioè **quattro volte
> fuori**. Un numero estrapolato oltre l'ultimo punto misurato **non si riferisce**.

⭐ La forma generale: **quando un testimone sbatte contro il suo massimo, non è più un testimone.**
Se ne cerca uno che quel massimo non ce l'ha.

---

### 1.35 ⛔⛔⭐ **Un difetto DEDOTTO può azzeccare il meccanismo e sbagliare la conseguenza**

*24 agosto 2026, fase 10. Ed è una lezione sul modo di scrivere i rilievi, non sul difetto.*

⭐ **Il meccanismo era giusto**: un guardiano chiamato **dentro** il ciclo che consegna i fotogrammi
restringe la frontiera **come 1/N**, e con N inquilini si mangia i 300 ms che il codice si concede.
Dedotto leggendo il codice, ⭐ e **confermato dalla misura**.

⛔ **La conseguenza era sbagliata.** Il rilievo diceva *«e quindi gli inquilini vengono sfrattati»*.
`[M]` **Non è l'esito ordinario**: l'esito ordinario è che **ogni desktop crolla a 1,3 fot/s e non
si scrive una riga di registro** — cioè ⛔ **un degrado silenzioso**, che è **peggio** di uno sfratto,
perché lo sfratto almeno lascia una traccia.

> ⭐⭐ **La regola**: un rilievo dedotto dal codice ha **due metà** — *«come succede»* e *«che cosa si
> vede»*. ⛔ **La prima si può dedurre; la seconda no.** Va misurata, o dichiarata `[?]`.
>
> ⚠ E quando la conseguenza dedotta è **più vistosa** di quella vera, il difetto vero rischia di
> passare inosservato: si va a cercare lo sfratto, non lo si trova, e si archivia il rilievo — ⛔
> **mentre il degrado silenzioso è ancora lì**.

---

### 1.36 ⛔⛔⛔ **Lo strato che coordina i banchi è un banco anche lui — e nessuno lo certifica**

*24-25 agosto 2026, fase 10. `[M]` **Sei difetti**, tutti nello strato che fa girare i banchi, non
nei banchi.*

⭐ Il progetto certifica i banchi con `--certifica`: si inietta un guasto noto e si verifica che il
banco lo veda. ⛔ **Ma il lucchetto della GPU, il terreno, gli script che accendono il server e il
modulo che li accomuna NON hanno un `--certifica`** — e sono **il pavimento su cui poggia ogni
misura**.

`[M]` **Quel che è costato, in concreto:**

| | |
|---|---|
| **146 banchi senza il bit di esecuzione** | un `exec "$0"` su un file non eseguibile ha ucciso una campagna **dopo** che aveva vinto il lucchetto della GPU: ⛔ **un'ora persa**, e il lucchetto tenuto per niente |
| **il terreno diceva «acceso» guardando il PID** | ⛔ un server con il processo vivo e **nessuno in ascolto sulla porta** passava per acceso. Ora «acceso» vuol dire **qualcuno ascolta** |
| **il terreno riscriveva la parola d'ordine** di un utente che esisteva già | ⛔ e ammazzava le sessioni di un altro banco in parallelo |
| ⛔⛔ **il `pkill` globale** dentro due banchi | su una macchina con banchi in parallelo, uno **ammazza il lavoro degli altri** |
| **il lucchetto scaduto si scassinava senza guardare** | ora **confronta prima di cancellare**: `[M]` scaduto ⇒ scassina; cambiato sotto ⇒ ⭐ **NON scassina, e il fresco sopravvive** |

> ⭐⭐ **La regola**: *ogni cosa da cui dipende una misura è una cosa da certificare* — e **il fatto
> che non produca numeri non la esenta**. Un lucchetto che si scassina di traverso e un banco che
> conta male producono **lo stesso danno**: un numero che nessuno sa che è falso.

⚠ **E la spia da riconoscere**: quando un guasto colpisce **banchi diversi allo stesso modo**, non è
dei banchi. È di sotto.

---

### 1.37 ⛔⛔⛔⭐ **Una prova che non si può GUARDARE vale zero — e chiamare qualcuno a giudicarla è peggio che non provare**

*25 agosto 2026, fase 10. ⛔ È la lezione più cara della fase, e non l'ha insegnata una misura:
l'ha insegnata **il regista, spazientito**.*

⛔ Il prodotto è stato costruito, cucito, misurato su **undici desktop veri**, e i numeri erano
buoni. ⇒ È stato chiesto al regista di guardare. ⛔ **E il browser, dentro il desktop remoto, non si
apriva.** Tre volte, finché lui ha smesso:

> *«Io non faccio più niente, Firefox continua a non funzionare e io non posso fare test in queste
> condizioni.»* · *«Senza Firefox nessun test di rilievo ha senso, quindi non chiamarmi se non
> funziona.»*

⛔⛔ **E la parte grave non è che il browser non funzionasse: è che non si sapeva.** Sono state
provate **quattro strade** per vedere l'immagine di quel desktop — lo scatto interno, la fotografia
dello schermo, la tela letta dalla pagina, il conteggio dei fotogrammi — e ⛔ **nessuna ha dato il
quadro**. ⇒ La scena è stata dichiarata pronta **senza che nessuno l'avesse guardata**.

> ⭐⭐⭐ **La regola, in una riga: la scena si prepara e si GUARDA prima di chiamare chi deve
> giudicarla.**
>
> ⛔ E il contatore **non conta come guardare**. *«Sono passati 493 fotogrammi»* e *«si vede un
> desktop con un browser aperto»* sono **due affermazioni diverse**, e la prima non implica la
> seconda: 493 fotogrammi neri sono 493 fotogrammi.

⚠ **E c'è un costo che non è tecnico.** Chi giudica ha una pazienza finita, ⛔ **e ogni chiamata a
vuoto ne consuma un pezzo**. Il giudizio dell'utente è l'invariante **I8**, cioè il metro ultimo del
prodotto: ⇒ ⭐ **sprecarlo è sprecare l'unico strumento che non si può ricostruire.**

⭐ **Il rimedio è un pezzo di attrezzatura, non un proposito**: un testimone che tira giù
**l'immagine** di quel che l'utente vedrebbe, ⛔ **tarato come ogni altro metro** (§1.33) — con la
marca riconoscibile che deve ritrovare, e il controllo negativo che deve dire *«nero»* quando è
nero. ⇒ E ⛔ **se non ha potuto guardare deve tornare «non lo so», mai un'immagine vuota**: *«non ho
guardato»* non è *«è nero»*.

---

### 1.38 ⛔⛔⛔⭐ **Un controllo che CONDIVIDE il fattore che deve escludere non controlla niente**

*25 agosto 2026, fase 10 — e refuta una conclusione della fase 9 che portava un ✅.*

⛔ **La conclusione sbagliata**: *«Firefox è rotto su questa macchina per tutti, dentro e fuori
REMOTIX. Non è un difetto del prodotto.»* Chiusa, spuntata, e ripetuta due volte nel `README.md`.

⭐ **E il controllo che sembrava chiuderla era di quelli buoni**: si toglieva **tutto** — nessuna
sessione REMOTIX, nessun Wayland, nessun monitor — e si lanciava il browser **da un altro utente**.
Falliva uguale. ⇒ *«Allora non è la sessione.»*

⛔⛔ **E invece i due lati condividevano la causa.** `~/.cache` è un collegamento a `/tmp` per
**tutti** gli utenti di quella macchina, l'utente del controllo compreso; e il profilo del browser
sta sotto `~/.cache/mozilla`, cioè **`/tmp/mozilla`** — ⛔ **una sola cartella, che il primo arrivato
si era presa a modo `0700` due giorni prima.**

> ⚠ **E una precisazione che non cambia la lezione, ma cambia di chi è la colpa** *(25 agosto 2026,
> corretto dall'utente)*: ⛔ **quel collegamento non è un guasto** — *«`.cache` che punta a `/tmp` è
> una mia scelta voluta»*, ed è una decisione sul **suo** sistema operativo. ⇒ Il fattore condiviso
> era una **configurazione legittima**, non un difetto — ⭐ e questo rende la lezione **più forte**,
> non più debole: *il fattore che un controllo condivide non ha nessun bisogno di somigliare a un
> guasto per rovinarlo.* Il difetto è **nostro**: siamo noi a creare dieci utenti che finiscono
> tutti nella stessa cartella (`DECISIONI.md` §4.6-undecies).

⇒ ⭐ **Il controllo mostrava lo stesso guasto per la STESSA ragione, non per una ragione diversa.**

| | fase 9 | ⭐ dopo aver tolto quel solo fattore |
|---|---|---|
| il browser headless, dall'utente del controllo | ⛔ **si pianta, ucciso a 60 s, profilo vuoto** | ⭐ **`rc=0`**, e uno scatto da **5,5 MB** |

> ### ⭐⭐ La regola, e non è «fai più controlli»
>
> ⛔ **Prima di fidarsi di un controllo, si nomina il fattore che deve escludere e si verifica che il
> controllo NON ce l'abbia.** Un controllo si sceglie per quel che **non** ha in comune col caso — e
> quel *«non»* va **guardato**, non dato per scontato perché l'ambiente è diverso.
>
> ⚠ **La spia**: un controllo che *«fallisce uguale»* è **sospetto**, non rassicurante. Se togliendo
> tutto il sintomo non cambia di un millimetro, la spiegazione più semplice non è *«la causa è
> altrove»*: è ⛔ **«c'è qualcosa che non ho tolto»**.

⭐ **E quel che il progetto aveva già scritto giusto**, in fondo alla stessa sezione e ignorato:
*«il difetto c'è, la diagnosi no»*. ⇒ ⛔ **Quella frase e un ✅ non possono stare nella stessa
sezione**: se la diagnosi non c'è, la sezione non è chiusa.

⚠ E il costo, per essere onesti fino in fondo: quella conclusione ha tenuto il regista **due fasi**
davanti a un browser che non partiva, con la spiegazione *«non è nostro»* — che è la spiegazione che
⛔ **non chiede di continuare a cercare**.

---

### 1.39 ⛔⛔⛔⭐ **Si riparte sempre dallo stesso punto, e quel punto era già a posto**

*25 agosto 2026, fase 10. ⛔ È l'errore di metodo più costoso del progetto finora, e non è stato
scoperto misurando: è stato scoperto perché il regista ha chiesto una prova che **obbligava a
partire da zero**.*

⛔ **Il difetto**: su una sessione remota **appena nata**, il compositore non annuncia nessun
monitor ⇒ **nessuna applicazione può aprire una finestra**. È rimasto invisibile per giorni.

⭐⭐ **E non era sottile.** Era invisibile per una ragione sola:

> ⛔ **Tutte le prove — quelle del prodotto e quelle dei banchi — riusavano sessioni GIÀ APERTE**, che
> il monitor ce l'avevano. Il pezzo di scena che si rompeva **non veniva mai attraversato**.

#### ⛔ E il difetto ha una forma che si ripete — tre volte nella stessa fase

| | nascosto per | ⛔ perché |
|---|---|---|
| la sessione senza monitor | giorni | ⛔ si ripartiva da una sessione già viva |
| il browser che non nasce agli utenti dopo il primo ⚠ *(la `~/.cache` condivisa è una **scelta** dell'utente, non un guasto)* | **due fasi** | ⛔ e **il controllo che «chiudeva la questione» era nella stessa condizione** (§1.38) |
| cinque banchi che contavano zero fotogrammi | un giro | ⛔ una cura al registro ne aveva rotto le espressioni |

⇒ ⭐⭐⭐ **Tutti e tre sono lo stesso errore visto da tre lati**: si guarda **sempre lo stesso pezzo di
scena**, e si guarda **il processo invece del pixel**.

> ### ⭐⭐ Le due regole, e sono corte
>
> 1. ⛔ **Almeno una prova deve partire da ZERO**: macchina pulita, utente nuovo, sessione nuova — e
>    finire con **un'immagine**. Una prova che riusa uno stato che funzionava **non può trovare un
>    difetto della nascita**, per costruzione.
> 2. ⛔ **Non si conta il processo: si guarda il pixel.** `[M]` Il conto dei processi diceva **1** sia
>    con la finestra sia senza — ⭐ **finestra o non finestra, lo stesso numero.**

⚠ **E la contromisura non è «più prove».** Ce n'erano già più di cento, ⛔ **e i tre difetti sono
passati in mezzo a loro.** Il problema non è la quantità: è **da dove partono** e **che cosa
guardano**. ⇒ È per questo che l'utente ha deciso una fase apposta — `DECISIONI.md` §4.6-duodecies,
la **rete di sicurezza** — prima dei desktop nuovi.

---

### 1.40 ⚠⭐ **`bash -n` passa su uno script che non fa quel che sembra**

*25 agosto 2026, e costa dichiararlo perché è successo mentre si costruiva il banco.*

```bash
U=${1:?serve l'utente}      # ⛔ l'apostrofo APRE una virgoletta…
PROFILO=${2:?serve il profilo}   # …e questa riga finisce DENTRO la stringa
```

`[M]` L'apostrofo di *«l'utente»* si è mangiato **quattro righe**, fino al `'` successivo — che stava
in un commento (`E'`). ⇒ `PROFILO=` **non è mai stata eseguita**, e lo script è morto molto più in
là con *«PROFILO: unbound variable»* su una riga che non c'entrava.

⛔⛔ **E `bash -n` è passato.** La sintassi **era** valida: solo, non voleva dire quel che sembrava.

> ⭐ **La regola**: `bash -n` dice *«si può leggere»*, non *«fa quel che credi»*. ⇒ Un controllo di
> sintassi **non è una prova**, e uno script nuovo va **eseguito** almeno una volta prima di
> fidarsene. ⚠ E dentro `${…:?…}` e le stringhe fra virgolette doppie, **niente apostrofi**: questo
> progetto scrive già `e'` e `puo'` nei commenti, ⛔ e lì dentro quella convenzione è **obbligatoria**,
> non stilistica.

> ### ⛔ E IL 26 AGOSTO 2026 È SUCCESSO DI NUOVO — *ventiquattr'ore dopo, nello stesso progetto*
>
> `[M]` Un apostrofo dentro un **commento** in un blocco `sh -c '…'` ha chiuso la stringa a metà, e
> la shell ha eseguito i pezzi rimasti come comandi: `MANCA: unbound variable`, `grep: dentro: No
> such file or directory`, `sed: invalid option -- '8'`. ⛔ **`bash -n` è passato anche stavolta.**
>
> ⇒ ⭐⭐ **La cura non è ricordarsene**: i commenti si scrivono **fuori** dal blocco citato. Dentro un
> `sh -c '…'` non ci va prosa — ci vanno comandi.

---

### 1.41 ⛔⛔⭐ **Il rovescio di «silenzio invece di rosso»: ROSSO INVECE DI NIENTE**

*26 agosto 2026, fase 11, primo giro del banco che valida l'ambiente.*

⛔ §1.29 dice che nove difetti di banco su nove avevano la forma *«silenzio invece di rosso»*.
⭐ **Questo ha la forma opposta, e costa uguale.**

`[M]` Il banco aveva otto verifiche. La **quarta** chiude la sessione dell'utente per vedere se i
figli muoiono davvero — e chiudendola si porta via anche la cartella privata della sessione.
⇒ ⛔ **Le verifiche 5, 6 e 7, che vengono dopo, trovavano il campo sgombro e davano TRE ROSSI
FALSI**: *«la cartella non c'è»*, *«il canale non c'è»*, *«il compositore non parte»*.

Il verdetto diceva **«LA SCATOLA NON REGGE»**, e la scatola reggeva benissimo.

> ### ⭐⭐ Perché è grave quanto il silenzio
>
> ⛔ **Una rete che dà rossi a vuoto viene spenta da chi lavora** — e allora non c'è più nessuna
> rete. ⇒ Il danno non è il rosso sbagliato: è che **il prossimo rosso, quello vero, nessuno lo
> guarderà.**
>
> ⭐ **La regola**: *chi prova la chiusura ha il dovere di RIAPRIRE, e di verificare che la
> riapertura sia riuscita prima di lasciar giudicare gli altri.* ⚠ E se non ci riesce, l'esito non è
> rosso: è **«non lo so»**, e si ferma lì.

⚠ **E il fratello minore, la stessa notte**: una verifica giudicava mentre il pezzo che stava
misurando era ancora `activating`. ⇒ Diceva *«non regge»* dove la verità era *«non avevo ancora
chiesto niente»*. ⭐ Si **prepara** come fa il prodotto, si aspetta l'evento, **poi** si giudica —
e ⛔ **preparare non è barare: barare sarebbe saltare la verifica.**

---

### 1.42 ⛔⛔⛔ **Stesso nome, stessa versione apparente, COSA DIVERSA — e il sintomo esce dalla parte sbagliata**

*26 agosto 2026, fase 11, mettendo il prodotto dentro la scatola.*

`[M]` Il binario copiato era **quello giusto**, verificato con l'impronta. Le librerie sono state
prese da `/lib` della macchina: `libngtcp2.so.16`. ⛔ **Ma il server vero non usa quella**: usa
quella costruita a parte, e le due sono **16.2.9** contro **16.11.0** — *stesso nome di file, stesso
numero di versione del formato, due programmi diversi*.

| | |
|---|---|
| il server | ⭐ **è partito**: certificati generati, righe d'avvio complete, porta in ascolto |
| ⛔ al **primo cliente** | è morto con `ngtcp2_settingslen_version: Unreachable` |
| ⛔⛔ e il cliente | ha visto soltanto **«Idle timeout»** |

> ### ⛔⛔ I due insegnamenti, e il secondo vale più del primo
>
> 1. **Un'impronta del binario non basta**: due macchine con lo stesso binario e librerie diverse
>    sono due macchine diverse. ⇒ L'allineamento si verifica **sul binario E su quel che gli sta
>    sotto**.
> 2. ⭐⭐ **Il sintomo è uscito dalla parte sbagliata.** Chi guardava il cliente vedeva *«la rete non
>    risponde»* — una diagnosi che manda a cercare nel posto sbagliato per ore. La riga vera stava
>    nel registro **del server**, e ci è arrivata solo perché la si è andata a leggere.
>    ⇒ È `CODER.md` §3.8 al rovescio: *si verifica dal lato che deve ricevere*, ⛔ **ma quando
>    qualcosa non arriva, si va a leggere il lato che manda.**

⚠ **E la stessa famiglia, due volte ancora nella stessa notte**: due pezzi funzionavano perché
qualcun altro se li tirava dietro, e sono spariti appena la ricetta è cambiata. ⇒ ⭐ **Quel che serve
si dichiara; quel che arriva per caso, per caso se ne va.**

---

### 1.43 ⛔⛔ **Un ambiente che RIPIEGA IN SILENZIO produce numeri peggiori e nessun rosso**

*26 agosto 2026, fase 11, primo avvio della scatola.*

`[M]` Il nodo della scheda grafica è entrato nel contenitore con il **numero** di gruppo dell'ospite,
⛔ ma dentro quel numero apparteneva a un **altro gruppo**. L'inquilino è rimasto fuori, e il
compositore ha scritto due righe che nessuno stava leggendo:

```
libEGL warning: failed to open /dev/dri/renderD128: Permission denied
libmutter-Message: Created surfaceless renderer without GPU
```

⇒ ⛔⛔ **Un banco che misura la codifica in SOFTWARE credendo di misurare l'hardware.** Nessun errore,
nessun rosso: **solo numeri peggiori**, che qualcuno avrebbe attribuito al desktop o al codice nuovo.

> ⭐ **La regola** — è `CODER.md` §3.9 applicata all'**ambiente** invece che a un componente:
> *chiedi il pezzo per nome, e verifica che l'abbia obbedito.* ⇒ Qui: dopo aver acceso la scatola si
> **rilegge dal nodo** che l'inquilino sia davvero nel gruppo della scheda, e se non lo è **si dice**.
>
> ⚠ E la cura non inchioda il numero: lo **legge** dal nodo e vi si allinea, dichiarandolo. ⛔ Un
> numero inchiodato avrebbe fatto una cosa che funziona su questa macchina e **tace** su un'altra.


---

### 1.44 ⛔⛔⛔ **Il predicato che non poteva dare rosso, e aveva l'aspetto di uno che passa**

*26 agosto 2026, fase 11, prima stesura di C8.*

Il difetto da prendere: dieci inquilini con `~/.cache` che punta tutta allo stesso posto, e il
browser che dal **secondo** in poi non fa più il suo profilo. Il predicato scritto per verificarlo —
e scritto **bene**, secondo la regola E1 *«non si guarda il collegamento, si prova a SCRIVERE»* —
era:

```
mkdir -p ~/.cache/.prova && rmdir ~/.cache/.prova
```

⛔ **Non poteva fallire mai.** Con il collegamento, `~/.cache` **è `/tmp`**, e `/tmp` è scrivibile da
chiunque (modo `1777`). ⇒ Il predicato diceva **«sa scrivere: sì»** anche all'inquilino che il
browser non riusciva ad aprirlo.

⭐ **Il posto che morde era un livello più sotto**: `~/.cache/**mozilla**`, che il **primo** inquilino
si prende a modo `0700`. Ed era già scritto, con la sua misura, dentro `src/provisiona.sh`: *«da
`provanic3`, `mkdir -p ~/.cache/mozilla` → Permission denied»*.

> ### ⛔ La regola, e vale oltre questo caso
>
> **Applicare E1 non basta: bisogna applicarlo NEL POSTO CHE MORDE.** Un predicato che prova la cosa
> giusta un livello troppo in alto ⛔ **ha esattamente lo stesso aspetto di un predicato che passa** —
> ed è peggio di non averlo, perché rassicura.
>
> ⇒ ⭐ **La contro-prova che lo avrebbe preso in dieci secondi**: far girare il predicato **col guasto
> innestato** e pretendere che dia rosso. È la stessa cosa che questa fase chiede a ogni maglia
> (`--certifica`), ⛔ e vale anche per il singolo predicato dentro una maglia, non solo per la maglia.

---

### 1.45 ⛔⛔ **Il tetto di una prova prestato a un'altra — e il rosso che non distingue più niente**

*26 agosto 2026, fase 11, primo giro vero di C8.*

C8 fa due cose con tempi diversissimi: **aspettare che una pagina compaia su un desktop già acceso**
(~25 s) e **far partire Firefox per la prima volta in una scatola fredda** (che crea il profilo, e
passa abbondantemente i 25 s). ⛔ La prima stesura usava **lo stesso tetto** per tutt'e due.

`[M]` Esito: **rosso a tutt'e due gli inquilini, con la cura e senza.**

⇒ ⛔⛔ **E il danno vero non è il rosso falso: è che il COLLAUDO smette di valere.** Il senso di
`--senza-cura` è *«col guasto innestato deve diventare rosso»*; ⚠ se è rosso **anche senza**, quel
confronto non dimostra più niente, e una maglia che non sa distinguere il guasto dal proprio tetto
⛔ **è indistinguibile da una maglia rotta**.

> ⭐ **La regola**: ogni attesa ha un **nome suo** e un **valore suo**, e il valore si giustifica con
> quel che si sta aspettando. ⛔ Riusare un tetto perché «è lì e più o meno va bene» è la stessa
> forma d'errore di riusare un numero misurato in un'altra condizione.
>
> ⚠ E il segnale che avrebbe dovuto insospettire subito: **tutti rossi**. Un guasto che colpisce
> *«dal secondo in poi»* e che invece colpisce **anche il primo** non è quel guasto — ⇒ e adesso è
> C8 stessa a dirlo, invece di lasciarlo dedurre.

---

### 1.46 ⛔⛔⛔ **Il banco che non ha girato affatto — e ha detto «riuscito»**

*26 agosto 2026, fase 11.*

Un comando annidato **tre volte** — `ssh` → `systemd-run … /bin/bash -c "…"` → `podman exec … sh -c
"cd … && python3 …"` — ha perso le virgolette per strada. ⛔ **Non ha eseguito niente**, non ha
stampato niente, e ha restituito **`0`**.

⇒ ⛔⛔ **Un verde che non ha nessuna misura sotto**, e che dal lato di chi legge il registro ha
**esattamente lo stesso aspetto** di un giro riuscito. ⚠ È il rovescio peggiore di §1.41: là il banco
gridava rosso senza avere guardato; qui **tace e dice sì**.

> ### ⭐ Le due regole, e la seconda vale più della prima
>
> 1. ⛔ **Niente gusci in mezzo**: il programma si chiama **per percorso assoluto**, senza `sh -c`
>    dentro `podman exec` dentro `systemd-run` dentro `ssh`. Ogni livello di virgolette è un posto
>    dove il comando può sparire.
> 2. ⭐⭐ **Un banco che non ha prodotto NESSUNA riga non è «riuscito»**: chi lo lancia deve
>    pretendere di vedere l'intestazione e il conto finale, ⛔ e trattare il silenzio come *«non ho
>    guardato»* (esito 3) — mai come verde. `LEZIONI.md` §1.30 lo dice per la sollecitazione; qui
>    vale per il banco stesso.

### 1.47 ⛔⛔ **Un confronto fra valori che nessuno sa dare è VERDE, e non ha guardato niente**

*26 agosto 2026, fase 11, prima stesura di C11.*

C11 confronta tredici cose fra le quattro scatole e dice *«sono allineate»* se ogni voce ha lo
**stesso valore** dappertutto. ⛔ Tre voci chiedevano pacchetti con il nome sbagliato —
`libssl3` e `libpipewire-0.3-0`, che in Debian 13 si chiamano `libssl3t64` e
`libpipewire-0.3-0t64`. ⇒ Tutte e quattro le scatole rispondevano **`?`**.

⭐⭐ **E `?` uguale a `?` è uguale.** Le tre voci **passavano il confronto**, e passavano ogni volta,
per sempre. ⛔ Tre controlli su tredici non stavano guardando niente, e il verde diceva
*«allineate»* con la stessa faccia di quando le guardava davvero.

> ### ⭐ La regola
>
> ⛔ **Un confronto ha bisogno che almeno uno sappia rispondere.** Una voce a cui **nessuno** risponde
> non è «uguale per tutti»: è **muta**, e va detta a parte.
>
> ⇒ C11 adesso le conta e le **stampa**: *«N voci a cui nessuna scatola sa rispondere — e una voce
> muta passa il confronto senza aver guardato niente»*.
>
> ⚠ **È la stessa forma d'errore di §1.44** (il predicato che non poteva fallire) vista da un'altra
> parte: là il predicato diceva sempre sì, qui il confronto dice sempre uguale. ⭐ In tutt'e due i
> casi il segnale è lo stesso — **un controllo che non ha mai dato rosso in vita sua va guardato in
> faccia**, non festeggiato.

### 1.48 ⛔⛔ **Il ciclo delle opzioni si è mangiato l'argomento — e il messaggio ha detto «riuscito»**

*26 agosto 2026, fase 11, il gancio.*

`11-gancio.sh installa pre-commit` ⛔ **installava `pre-push`**, e stampava tranquillamente che era
andata bene. Il ciclo che legge le opzioni consumava l'argomento e non lo passava a nessuno; il
messaggio di conferma ripeteva **quel che era stato chiesto**, non quel che era stato fatto.

⇒ ⭐⭐ **E questa è la regola, ed è più larga del bug**: un messaggio di riuscita che ripete
l'intenzione **non è una verifica, è un'eco**. `CODER.md` §3.9 dice *chiedi il pezzo per nome, e
verifica che l'abbia obbedito*: qui il pezzo eri tu stesso.

> ⛔ **Il messaggio di conferma si costruisce RILEGGENDO il risultato**, non ricopiando la richiesta.
> «Installato in `<percorso letto adesso dal disco>`», non «installato `<quello che mi hai chiesto>`».
>
> ⚠ È la stessa famiglia di §1.46 — là il comando non era stato eseguito affatto e il codice d'uscita
> diceva `0`; qui è stato eseguito **su un bersaglio diverso** e il messaggio diceva sì. ⇒ In tutt'e
> due i casi il difetto sta nel **punto in cui si riferisce**, non nel punto in cui si fa.

---

### 1.49 ⛔ **Un rosso che non si può far diventare verde è peggio di nessuna maglia**

*26 agosto 2026, fase 11, C12.*

C12 controlla che il gancio sia installato, e per trovarlo usava `git --git-path`. ⛔ Quel comando
torna un percorso **relativo alla cartella data a `-C`**, non alla radice del deposito. ⇒ La maglia
cercava il gancio in un posto che non esiste, e avrebbe detto **«non installato» per sempre**, anche
subito dopo averlo installato.

⭐ **Un rosso perpetuo non è prudenza: è rumore.** E il rumore, in una rete di sicurezza, finisce
sempre allo stesso modo — §1.3 del documento di fase: *«una rete che dà rosso a vuoto viene spenta da
chi lavora»*.

> ### ⭐ Come si prende, e costa dieci secondi
>
> ⛔ **Prova a far diventare VERDE la maglia.** Un controllo va acceso in tutt'e due i versi: si
> innesta il guasto e si pretende il rosso (che il progetto già fa, `--certifica`), ⚠ **e si toglie
> il guasto e si pretende il verde**. La seconda metà si dimentica, ed è quella che prende questo.

---

### 1.50 ⛔⛔ **Il tetto governava l'USCITA, non il lavoro — e il commento descriveva un'altra cosa**

*26 agosto 2026, fase 11 — trovata dal banco di C14, non da quello a cui apparteneva il difetto.*

C8 fa scattare una fotografia al browser con un tetto di tempo, e il commento accanto diceva che
serviva perché *«il primo avvio in una scatola fredda non ci sta dentro»*.

`[M]` Messo il tetto a **un secondo**: Firefox viene ucciso, esce con **124**, ⛔ **e il PNG c'è lo
stesso, 30 135 byte.** ⇒ Scrive l'immagine e **poi** indugia a chiudersi: quel tetto non limitava lo
scatto, limitava **l'accomiatarsi del browser**.

⭐⭐ **E il giudizio è sopravvissuto per la ragione giusta, che vale la pena isolare:**

> ### ⛔ Si giudica il RISULTATO, non il codice d'uscita.
>
> C8 guarda **il file**, non come è morto il programma — *un browser che ha disegnato ha disegnato,
> anche se poi è stato ucciso mentre si accomiatava*. ⚠ Una maglia che avesse creduto al `124`
> avrebbe dato rosso su un lavoro **compiuto**.

⚠ **E la cosa da correggere non era il codice: era il commento.** Un commento che descrive una
grandezza diversa da quella che il codice governa ⛔ è una trappola per chi verrà dopo a tarare quel
numero — e taratura al buio è esattamente come si perde una giornata.

⭐ **E che l'abbia trovata un ALTRO banco è il fatto più importante di tutti**: nessuno dei quattro
rossi falsi di §1.44–1.47 si era accorto di questo, perché tutti guardavano C8 **da dentro**.

---

### 1.51 ⛔⛔ **«Text file busy» — il rosso che viene dall'ORDINE dei comandi, non dal prodotto**

`[M]` 26 agosto 2026, cucendo le quattro maglie nuove nella rete. L'azione `11-accendi.sh prodotto`
copia il binario dentro la scatola. Con il **server acceso**, `cp` risponde:

```
cp: cannot create regular file '/opt/remotix/remotix': Text file busy
  NO  non sono riuscito a mettere il prodotto dentro
```

⇒ L'azione falliva **tutt'intera** su tutte e quattro le scatole, e il messaggio che restava era
*«non sono riuscito a mettere il prodotto dentro»* — che ha esattamente l'aria di un guasto del
prodotto o della scatola, mentre è ⛔ **un guasto dell'ordine in cui si danno i comandi**.

> ⭐ **La forma d'errore**: un banco che fallisce per una ragione sua e lascia un messaggio che
> accusa quel che sta provando. È la stessa famiglia di §1.46 e §1.48 — solo che qui l'esito è un
> rosso invece di un verde, e per questo è **meno** velenoso: almeno si vede.

⛔ **E la prima cura era peggio del male.** L'idea ovvia — spegnere il server prima di copiare — è
stata provata e **misurata**: `systemctl stop rete11-server` dentro la scatola **non torna** (oltre
due minuti, poi il comando è stato ucciso da fuori). ⇒ L'azione non falliva più: **si piantava**, che
è la forma peggiore, perché un banco appeso non dice niente a nessuno.

⭐ **La cura giusta era di un'altra natura, e la dice il sistema operativo**: *sovrascrivere* un
eseguibile in uso è vietato, **togliere** un eseguibile in uso è permesso. ⇒ `rm -f` e poi `cp`. Il
server vecchio continua a girare col suo inode fino al prossimo `11-accendi.sh server`, ed è
dichiarato nel file invece che scoperto da qualcuno fra sei mesi.

> ⚠ **La lezione generale**: quando un banco fallisce, la prima domanda non è *«che cos'ha il
> prodotto»* ma ⭐ *«questo comando poteva riuscire, nello stato in cui ho lasciato la macchina?»*.

---

### 1.52 ⛔⛔⛔ **La maglia col guasto innestato usciva col verdetto grezzo — e proprio nel giro del rosso avrebbe scritto «il guasto NON è stato visto»**

`[M]` 26 agosto 2026, primo giro del cablaggio delle quattro maglie nuove. `11-gancio.sh` legge una
maglia innestata **al contrario**: esce `0` quando il guasto **è stato visto**, e quello che finisce
nel registro non è l'esito grezzo ma il fatto — `ha_visto_il_guasto`. È da lì che C13 sa dire se la
rete è ancora capace di dare rosso.

⛔ **C9 usciva col verdetto grezzo** (`1`, cioè rosso). ⇒ Nel giro col guasto innestato il gancio
avrebbe scritto `ha_visto_il_guasto: false` **proprio quando il guasto era stato visto benissimo**, e
C13 avrebbe cominciato a dire *«la rete non sa più dare rosso»* mentre lo sapeva fare.

> ⭐ **E non l'ha preso nessuna certificazione, di nessuna delle due maglie.** La certificazione di
> C9 provava **il giudice** (16 casi su 16, tutti giusti); quella di C13 provava **la lettura del
> registro**. ⛔ Il difetto stava nel **giunto** fra le due: nel codice d'uscita, che non è di
> nessuno dei due mestieri. ⇒ Si è visto solo **facendo girare il cablaggio vero**, ed è la stessa
> famiglia di §1.46 e §1.40: `bash -n` passa, la certificazione passa, e la cosa non funziona.

⭐⭐ **E la cura non era invertire l'esito — quella sarebbe stata la seconda trappola.** C9 oggi è
rossa **anche senza guasto** (le due righe di `src/tastiera.c`, ⇒ `DECISIONI.md` §4.6-duoetvicies). Un
semplice *«rosso ⇒ visto»* avrebbe detto «il guasto è stato visto» **anche se l'iniezione non avesse
fatto niente**: un predicato che non può fallire, cioè §1.44 di nuovo, e stavolta a reggere la
certificazione di tutta la rete.

⇒ Si pretendono **due** cose insieme: il verdetto è rosso, **e** le righe senza nome sono di più di
quante ne aveva lasciate il difetto vero. `[M]` senza guasto: 4 · col guasto `tutto`: 5 490.

> ⛔ **La regola**: quando una maglia porta con sé un difetto **vero e già noto**, il suo guasto
> innestato non si misura sul colore del verdetto — si misura sulla **differenza** che l'iniezione
> ha prodotto. Altrimenti la rete si certifica su un guasto del prodotto invece che sul proprio.

---

### 1.53 ⛔⛔⛔ **Un rosso che non poteva diventare verde ha bloccato cinque prove e rinviato una fase**

`[M]` 27 agosto 2026. La maglia C1 — *«la sessione nasce e si vede»* — diceva **dieci sessioni cieche su
dieci**. Su quel verdetto poggiavano: cinque prove della rete dichiarate «bloccate» (C2, C3, C4, C6,
C8b), il rinvio della fase 12, un difetto aperto nella fase 10, e una lista di lavoro.

⛔ **C1 leggeva la riga sbagliata.** `sessione [chi] ⛔ ZERO MONITOR` il prodotto la scrive **nel
passaggio obbligatorio di una nascita RIUSCITA** (`src/sessione.c:345-348`): dal 14 agosto *«zero
monitor propri»* è **lo stato voluto** — il monitor lo monta la **cattura**, dopo.
⛔ E il ramo verde era **irraggiungibile**: `sessione_stato()` non viene più chiamata dopo che il
palco è preso, quindi `monitor N/N: connettore` non compare **mai** in una nascita sana.

> ⇒ ⭐⭐ **C1 poteva dire soltanto «CIECA» o «non lo so». Non ha mai detto verde, e non poteva.**
> `[M]` La controprova, sulla scatola curata: `formato negoziato` compare **8** volte, il palco dice
> `monitor «Meta-0» (0 prima, **1** dopo) 1920x1080`, `monitor …: connettore` compare **0** volte —
> **e C1 diceva ancora CIECA**.

⛔⛔ **E la certificazione non l'ha preso perché imponeva il difetto come requisito**: due dei suoi
casi (`11-c1…py:148-151`) avevano per registro **proprio quello di una nascita sana**, e pretendevano
che il verdetto fosse rosso. ⇒ La certificazione non provava il giudice: ne **congelava l'errore**.

> ⭐ **La regola che ne esce, e vale per ogni maglia**: ⛔ **una certificazione senza un caso che
> finisce VERDE partendo da dati sani non è una certificazione.** È §1.44 applicata un livello sopra:
> il predicato che non può fallire, stavolta protetto da un banco che gli dà ragione.
>
> ⚠ E la seconda: quando un verdetto **rosso** regge da giorni e nessuno riesce a farlo tornare
> verde, ⛔ la prima domanda non è *«perché il prodotto è rotto»* ma **«questa maglia sa dire
> verde?»**. Costa dieci minuti e qui ne è costati parecchi di più.

---

### 1.54 ⛔⛔ **La riparazione di una cosa apriva il guasto di un'altra — e il guasto sembrava del prodotto**

`[M]` 27 agosto 2026. Dentro le scatole, una sessione impiegava **~97 secondi** a diventare utile.
Sembrava il difetto della nascita: Mutter che non risponde, nessuna finestra, zero fotogrammi.

La catena vera, e ha tre anelli:
1. la scatola deve dare all'inquilino il **gruppo della scheda grafica**, altrimenti il compositore
   ripiega sul software e i numeri sono falsi. ⇒ La ricetta **sposta** il gruppo `polkitd` da 991 a
   1991 per liberare quel numero;
2. ⛔ **`groupmod -g` non si porta dietro i file.** `/etc/polkit-1/rules.d` restava `root:991` ⇒
   `polkitd` non poteva più leggerla, e moriva;
3. `gnome-shell` chiama `polkit` e `upower` in modo **sincrono** all'avvio ⇒ incassava **quattro
   scadenze da 25 000 ms in fila**.

> ⇒ ⭐⭐ **La riparazione della scheda grafica apriva il guasto di polkit, e il guasto di polkit
> aveva l'aspetto di un difetto del prodotto.**

⭐ La cura sta tutta nella **ricetta**, e non ha chiesto nessun permesso nuovo: chi sposta il numero
fa seguire i file (`find -gid … -exec chgrp`), e l'unità dei gruppi prende `Before=polkit.service`.
⚠ `[M]` Col solo `chgrp` polkit moriva ancora, **battuto di 97 millesimi di secondo**.
`[M]` Dopo: tre sessioni nuove negoziano il formato in **1,105 s · 0,998 s · 0,957 s** — da 97
secondi a **uno**.

> ⚠ **La lezione**: quando si cambia un identificatore di sistema per far posto a un altro, ⛔ la
> domanda non è *«il numero è cambiato?»* ma **«che cosa apparteneva a quel numero?»**. E quando un
> ambiente costruito da noi si comporta male, ⭐ **il primo sospettato è l'ambiente**, non il
> prodotto — perché il prodotto non lo abbiamo scritto stanotte, la ricetta sì.

---

### 1.55 ⛔⛔ **Il numero letto per mesi era memoria non inizializzata**

`[M]` 27 agosto 2026. La fase 10 §7.4 descriveva un *«terzo stato»* del palco — la riga
`(0 prima, **2** dopo)` — e lo trattava come un fatto: due monitor comparsi.

⛔ **Era spazzatura.** `src/figlio.c` · `codifica_e_manda()` spediva la struttura al padre **prima** del `memset` di
`:5311`. `[M]` Provato in due modi: quella riga compare anche su scatole dove **nessun monitor può
essere nato** (lì il prodotto non sa nemmeno avviare il desktop), sempre e solo sul ramo *«aspetto la
tela del cliente»*, con spazzatura evidente accanto (`stride 958311266`, `stride 306537694`); e nel
codice macchina il vecchio ramo spediva **328 byte** avendone scritti **32**.

> ⭐ **E il danno non è il difetto: è la diagnosi.** Quel `2` ha alimentato per mesi un'ipotesi —
> *«a volte due monitor compaiono»* — che ha orientato la caccia. ⛔ Un numero mai scritto è peggio
> di un numero mancante, perché **ha l'aria di essere un dato**.
>
> ⚠ La regola: una struttura che attraversa un confine (processo, socket, rete) si azzera **in cima
> alla funzione**, prima di qualunque uscita anticipata — non «prima dell'uso», che è un posto che
> si sposta a ogni modifica.

---

### 1.56 ⛔⛔ **Il banco provava quattro desktop, e il prodotto ne guidava uno**

`[M]` 27 agosto 2026. La rete ha quattro scatole — GNOME, KDE, XFCE, LXQt — e la fase le ha
presentate come la prova che *«le stesse prove girano su desktop diversi senza una riga cambiata»*.

⛔ Poi C1 è stata fatta girare **dieci volte per scatola** sulle altre tre, e il conto è stato:
**0 sane · 0 cieche · 30 «non ho potuto guardare»**. Il motivo lo dice il registro del prodotto:
*«Mutter non espone RemoteDesktop»* — ⛔ **il prodotto sa avviare solo GNOME** (`src/sessione.c` · `scrivi_dropin()`,
tutto `src/mutter.c`), e nelle altre tre scatole `gnome-shell` non c'è nemmeno.

⭐ **Quel che le altre tre provano davvero è reale ma più piccolo**: l'ambiente (il passo 0), il
suono (C5, che non passa dal desktop), i residui (C7), il registro (C9), l'allineamento (C11). ⛔ Non
provano che il **prodotto** regga su quei desktop, perché lì il prodotto non ci gira.

> ⚠ **La lezione**: ⛔ *«la prova gira su quattro ambienti»* e *«la prova dice qualcosa su quattro
> ambienti»* sono due frasi diverse, e la seconda va **misurata**, non dedotta dalla prima. Il segno
> che le distingue è l'esito **3**: una maglia che su tre ambienti su quattro non arriva mai a un
> giudizio non li sta provando — li sta **visitando**.

---

### 1.57 ⚠ **Il binario ricostruito voleva una libreria che il banco non portava — e il banco l'ha detto**

`[M]` 27 agosto 2026. Rimesso nelle quattro scatole il prodotto ricostruito con le cure della
giornata, `11-accendi.sh prodotto` ha risposto su tutte e quattro:

```
  NO  1 librerie non si risolvono: il server morira e non si sapra perche
  NO  il server non ha detto di essere pronto in 20 s
```

⇒ `ldd` dentro la scatola: **`libngtcp2_crypto_ossl.so.0 => not found`**. Il contenitore di
costruzione sul portatile si era mosso — il binario nuovo si lega a una libreria che quello vecchio
non usava — e il banco portava dentro solo la provvista vecchia.

> ⭐ **E questa è una buona notizia, non un guasto**: è esattamente il controllo che `11-accendi.sh`
> fa **apposta** dopo ogni consegna (`ldd | grep -c "not found"`), scritto quando si è imparato che
> ⛔ *«il binario era giusto e le librerie no, e il sintomo era dalla parte sbagliata»* (fase 11
> §7-bis.4). ⇒ Il difetto è stato **nominato in due secondi** invece di presentarsi tre ore dopo
> come «il server muore e non si sa perché».
>
> ⚠ **La lezione che resta**: è la regola R2 — *«le versioni si dichiarano, mai «l'ultima
> disponibile»»* — che ha ceduto dal lato del **contenitore di costruzione**, non da quello delle
> scatole. ⛔ Un ambiente di costruzione non dichiarato è una dipendenza che cambia da sola, e la
> rete se ne accorge **a valle**, quando il danno è già dentro l'immagine.
