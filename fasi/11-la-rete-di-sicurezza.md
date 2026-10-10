# Phase 11 — The safety net

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision.*

*Opened on **25 Aug 2026**. Closed on —*

> ### 📋 THIS DOCUMENT IS WRITTEN ALSO FOR WHOEVER DOES NOT KNOW THE PROJECT
>
> It is the design of REMOTIX's anti-regression net. ⇒ **§0** the minimum context, **§1-§5** the
> design, **§6** what the net does **not** catch, **§7** the work plan, **§8** the questions and the
> answers received.
>
> **The marks used everywhere in the project**, and they must be read:
> `[M]` measured by us, on the hardware, with the date · `[R]` read in the code of a reference ·
> `[S]` read in a specification · `[?]` **hypothesised, not yet measured**.
> ⛔ A decision that rests on a `[?]` is a decision half taken, and it must be written as
> provisional.

> ## ⭐⭐⭐ REVIEWED BY TWO EXTERNAL REVIEWERS — *25 Aug 2026, evening*
>
> The **first draft** of this document was submitted to two independent external reviewers
> (**Qwen** and **Gemini**), at the user's request: *«meglio quattro occhi che due»*.
>
> ⭐ **This is the second draft**, which integrates the findings accepted. The two reviews
> converge on five points — ⛔ and the convergence of two readers who did not talk to each other is worth more
> than a single finding (`PIANO.md` §0.4: *two programs written by the same hand that agree
> confirm nothing*).
>
> | the finding | who | outcome |
> |---|---|---|
> | **`logind` in the container must be tested BEFORE building** | both | ✅ **accepted**: it becomes **step 0**, and it is a precondition, not an option (§3.5) |
> | **the mark alone is not enough** | both | ✅ **accepted** (§4.2), in Qwen's **poor** form |
> | **C8 is the most important test and the most fragile** | both | ⚠ **finding accepted, the cure waits for the user** (§4.4) |
> | **the red policy is missing** | Qwen | ✅ **accepted** (§5.2) |
> | **the net does not check itself over time** | Qwen | ✅ **accepted**: C11-C13 (§4) |
> | **tests blind to the desktop = common list + adapters** | both | ✅ **accepted** (§3.7) |
> | **fast family under 3 minutes** | both | ✅ accepted as a **provisional cap** to be measured (§5.1) |
> | **micro virtual machines (Firecracker) if the container does not hold** | Gemini | ⛔ **rejected**, §3.5-bis: it takes away the graphics card, that is the reason virtual machines had already been discarded |
> | **image comparison with SSIM / computer vision** | Gemini | ⛔ **rejected**, §4.2: weight and new dependencies for a problem that is closed with a **tolerance** |
> | remarks on the test machine's environment | Qwen §3.11 | ⛔ **off target**, excluded by the user |

---

# §0 · The minimum context

## 0.1 What REMOTIX is

A remote desktop for Linux: **one server**, **no client to install** — a modern browser
is enough — and a protocol of our own that travels over WebTransport/QUIC.

The server runs on a Linux machine and, when someone connects, **switches on for them a graphical
session of their own**: a private Wayland compositor, without a physical monitor, captured and encoded in
hardware, sent to the browser. Several people can each have their own, on the same machine and
on the same graphics card.

| | |
|---|---|
| **the product** | ~53 000 lines of C in `src/` (24 files) |
| **the client** | a web page served by the server itself |
| **the test hardware** | i5-13500T · 31 GB · **integrated Intel UHD 730** — ⛔ not a powerful card, and every number of this project must be read knowing it |

## 0.2 Where it stands

**Ten phases closed.** The last one (multi-tenant) closed on 25 Aug 2026 on the user's
judgement: a **4K** video inside the remote desktop, with his tablet's bandwidth throttled to
**10 Mbit/s** — *«audio e video fluidi e in sync»*.

`[M]` **Six sessions** at the same time on the saturated scene, **at least eleven** on the real desktop (there the
ceiling was not found: the users ran out, not the machine).

**Today only one desktop works: GNOME.** The next three phases add **KDE (Plasma)**,
**XFCE** and **LXQt**. ⛔ **This phase sits in between, and it was decided by the user precisely to sit
in between.**

## 0.3 ⛔ Why this phase exists — three real faults, not a generic fear

All three found **on the same day**, 25 Aug 2026:

| the fault | hidden for | ⛔ why it was invisible |
|---|---|---|
| **the session that is born blind** | days | the compositor, on a **newborn** session, announces no monitor ⇒ **no application can open a window**. ⛔ Invisible because **nobody ever opened a NEW session**: all the tests reused sessions already open, which did have the monitor |
| **the browser that does not start for the users after the first** | **two phases** | on the machine the users' cache folder points to a shared folder — ⭐ **a deliberate choice of the owner, not a fault**. ⛔ But **it is our product** that creates ten users who all end up writing there: the first takes the folder, and for the other nine the browser is not born |
| **five benches that counted zero frames** | one round | a cure to the log had broken their expressions, and the function returned **0 instead of «I don't know»** |

> ### ⛔⛔ AND ALL THREE ARE THE SAME ERROR SEEN FROM THREE SIDES
>
> 1. **One always restarted from the same point**, and that point was already in order. A test that reuses
>    a state that worked **cannot find a birth fault**, by construction.
> 2. **One counted the process instead of looking at the pixel.** `[M]` The process count said
>    **1** both with the window and without — **window or no window, the same number.**
>
> ⚠ **And the countermeasure is not «more tests».** There were already **more than a hundred**, and the three faults
> passed **through the middle of them**. ⇒ The problem is not the quantity: it is **where the tests start from** and
> **what they look at**.

## 0.4 ⛔ And the reason it must be done NOW

From here on every phase adds a desktop, and every desktop is added **by touching the common
code**. Whoever touches it at that moment is looking at the new desktop, and has no reason to
suspect having just broken the old one — because the old one worked.

⇒ ⛔ **A fault that today is found once, with four desktops will be found four times — and in the
worst case on three it will not be found at all**, because nobody thinks of retesting the first.

⭐ **And the real cost of a fault is not repairing it: it is the distance between when it came in and when it is
found.** The browser fault, once understood, was cured in an afternoon. It cost two
phases because it was **old**, and because it carried a wrong explanation — *«non è nostro»* —
which is the explanation that **does not ask to keep looking**.

---

# §1 · The mandate, and the meter

## 1.1 What it must produce

**A way of noticing by ourselves that something has broken, before the user discovers it.**

The user sees nothing new on the screen — ⭐ **and that is the point**: he sees that the things that
worked keep working when the new desktops arrive.

## 1.2 ⛔⛔ The meter of the phase, and it is not «how many tests run»

> ### The meter is one only: **what the net CATCHES.**

⛔ **The acceptance test is already written, and it is severe.** The net is pointed at the code of 25 Aug 2026 and
**must turn red by itself on both faults**, ⛔ **without anyone having told it where
to look**:

| | |
|---|---|
| **acceptance test A** | the **session that is born blind** |
| **acceptance test B** | the **browser that does not start for the second user** |

⇒ ⛔ **If it does not catch them, it is not a net: it is a ritual.** And if in the end it has caught nothing that
the eye would not have caught, **the phase has failed and it must be said**.

## 1.3 ⚠ The danger of this phase, declared at the opening

A phase like this is **precisely** the kind of work that can swell until it eats the project it
was meant to protect. ⇒ The three guards we put on ourselves:

1. ⛔ **Few tests, short.** A net with a hundred meshes that nobody reads is ceremony, and ceremony
   costs time exactly like defects.
2. ⛔ **Every test is justified on a REAL fault**, already happened or that would have happened. Not on a
   fear.
3. ⛔ **The tests that catch nothing are thrown away**, and it is written that they were thrown away.

⚠ **And the external review added thirteen things.** ⛔ **They were not all accepted**, and the
non-accepted ones are written at the head with the reason — because *«the reviewer said so»* is not a reason
to make a net grow that must stay short.

---

# §2 · The decisions already taken — ⚠ **they are not under discussion**

*Taken by the user on 25 Aug 2026, discussing this phase.*

| # | the decision | the reason, as it was given |
|---|---|---|
| **D1** | **One container per desktop**, not virtual machines | ⛔ the virtual machine takes away the **real graphics card**, and all our numbers come from there. The container sits on the same machine and really uses it |
| **D2** | ⭐ **CORRECTED on 26 Aug 2026**: a box can have **up to ten** tenants — *«è un dato già misurato con GNOME»*. ⇒ The net uses **two** | the constraint was on **capacity**, which is not redone; ⛔ not on **correctness with several tenants**, which is another question. `DECISIONI.md` §4.6-terdecies ⇒ **§4.4 is closed: C8 sits in a box** |
| **D3** | **4K · 60 frames/s is the target for ALL desktops** | *«è il tetto che chiediamo a tutti»*. No tailor-made target per compositor |
| **D4** | ⛔ **No exceptions per compositor** | *«non voglio mettere delle eccezioni nel progetto»*. ⚠ **It concerns the PRODUCT**: §3.7 explains why the bench's adapters do not violate it |
| **D5** | **The containers must be kept aligned** | *«se sul container GNOME abbiamo remotix v1 e sul container KDE remotix v1.2 andiamo a sbattere»* |
| **D6** | The things of «later» do not come in here | they go into `MASTERPLAN.md`, with written **what it costs never to do them** |

⚠ **And a constraint that is not a decision but a fact**: `[M]` **the graphics card is ONE**. Four
containers can be switched on together, but **they cannot measure together**.

---

# §3 · The design

## 3.1 The net is made of three pieces, and the containers are only one

| | | |
|---|---|---|
| **WHERE** one tests | the four containers + the real machine | §3.2 |
| **WHAT** is checked | the short list — ⭐ **this is the real net** | §4 |
| **WHEN** it starts | the hook that makes it run by itself | §5 |

## 3.2 The containers — and the three rules that keep them honest

**Four containers, one per desktop, on the same machine, with access to the real graphics
card.** Inside each: a desktop, a user, and the server.

> ### ⛔ R1 · **One single binary, compiled once, copied into all four**
>
> ⛔ **Not compiled inside each container**: if every box compiles its own, one has
> four different binaries and the comparisons are worth nothing (D5).

> ### ⛔ R2 · **The container recipes declare the exact versions**
>
> ⛔ *«l'ultima disponibile»* **is a date disguised as a version**. A box built on Tuesday and
> one built on Thursday differ even with the same code of ours, because in between the
> package store moved. ⇒ Then one sees a worse number on XFCE and blames XFCE, while
> the blame was **Thursday's**.

> ### ⛔ R3 · **The alignment is VERIFIED, not taken for granted**
>
> Every container declares **the fingerprint of the binary AND of its own recipe**; the net compares them
> **before** believing any number, and **stops, declaring it**, if they do not match.
> ⭐ **And the recipe counts as much as the binary**: if a box is rebuilt and pulls in a
> newer version of the desktop, ⛔ the binary's fingerprint **matches all the same** and the net
> reassures while the environment has changed underneath. ⇒ It is check **C11**.
> ⚠ In the project there is already the precedent: a check that verifies that *«quello che misuro è quello
> che leggo»*, born from this same wound.

## 3.3 ⭐⭐ The rule of comparisons: **one thing moves at a time**

⛔ It is not true that the boxes must always be identical: if they were, the net would be good for
nothing — the whole point is comparing **before** and **after** a change.

| the comparison | what changes | what question it answers |
|---|---|---|
| **same desktop, two versions of our code** | our code | *«did the change break something?»* — ⭐ **it is the anti-regression net** |
| **same version of our code, four desktops** | the desktop | *«does this desktop behave differently?»* — needed when a new one arrives |

⛔ **What is never done is moving both together.** New code on KDE against old code
on GNOME **answers nothing, and seems to answer.**

> ### ⚠ And the day a new desktop arrives, «one thing at a time» becomes hard
>
> *Qwen's finding §3.6, accepted.* Adding KDE means **two changes together**: one touches the
> common code **and** a new box is born. ⇒ The rule is saved **by splitting into three steps**:
>
> 1. the changes to the **common code**, tested on the desktops **already existing** — ⛔ **before** the
>    new box comes into play. This is where the regression is caught;
> 2. the desktop's **new code**, which the old ones do not go through;
> 3. the **switching on** of the new box.
>
> ⛔ If the first step cannot be separated, **it must be declared in the phase document**: from that
> moment a red has two suspects instead of one, and whoever reads must know it.

## 3.4 ⭐⭐ The two families of tests — and only one gains from parallelism

| family | what it asks | how it runs | how much it costs |
|---|---|---|---|
| ⭐ **FUNZIONA** | yes/no answers: the session is born, the window opens, it is seen, the key arrives, the sound is there | **all four together** | minutes |
| ~~**VA VELOCE**~~ | ⛔ **does not exist, and is not done** — see the box below | | |

> ### ⛔ And «VA VELOCE» was a contradiction, resolved on 27 Aug 2026
>
> This table declared **two** families; ⛔ **§6 declares that the net is not a performance
> net**; and `[M]` in the hook that family **never existed**: there are `funziona`,
> `rete`, `rete-intera`, `tutto`, `desktop-nuovo`.
>
> ⇒ ⭐ **§6 is right, and the family must not be created.** The fifteen meshes are all yes/no; a
> family of numbers would duplicate the ~40 benches of phases 9 and 10 **outside the conditions in which
> those numbers hold**, and it would be the first thing someone would stop running.
> ⇒ ⚠ What stays true of this row is **how the measurements run when they are done**: ⛔ one box
> at a time, in a queue, with the card's lock. And it is a rule about the **lock**, not a catalogue.
> ⇒ ⛔ **The hole that remains is declared in §6**: *no bench compares yesterday with today.*

⭐ **And the good news lies in the division**: the fast family is the one needed **often**, and the
three faults of yesterday were **all** its own — none was a speed problem, they were all *«nothing
can be seen»*.

⛔ **But «the four boxes do not disturb each other» is asserted, not proved** — Qwen's finding §3.10,
accepted. ⇒ It must be **measured** once: the same tests alone and in parallel must give the same
outcome, and the time must not explode. It is check **C14**, and until it has run the word stays
`[?]`.

## 3.5 ⛔⛔ STEP 0 — **the container must be validated BEFORE building**

*A finding on which **both reviewers** converge, and the most serious of the two rounds.*

The product leans heavily on the piece of the system that keeps count of who is connected
(`systemd`/`logind`: linger, user sessions, the guardian that closes dead sessions). ⛔ Inside
a container that piece **may behave differently**.

> ⛔⛔ **The risk is not «a wrong test»: it is that the whole container layer becomes a
> simulacrum** — that is **the worst form of safety, the false one.**

⚠ **And the first draft was optimistic**, and the correction is accepted: it said *«if it does not hold, that
single test goes back to the real machine»*. ⛔ If that piece does not hold, what goes back is not **one**
test: it is **a family of behaviours**.

### ✅ The rule that replaces the `[?]`

> **The container is valid only if it passes step 0.** If step 0 fails, the tests that
> depend on that behaviour **stay on the real machine**, and it is written down.
> ⛔ **It is not an option: it is a precondition.** No final box is built before.

### The eight things step 0 verifies — *half a day, no more*

| # | | must turn out |
|---|---|---|
| 1 | the user session **exists** and is of the right type | as on the real machine |
| 2 | **linger** works: the user's services live without anyone having logged in | same |
| 3 | the **server starts inside the user session**, without tricks that could not be done on the real machine | same |
| 4 | when the session ends, ⛔ **the processes really die** and are not left orphaned | same |
| 5 | the user's private folder for sockets exists, is writable, ⛔ **and is not shared between containers** | same |
| 6 | the session's message channel exists and the desktop sees it | same |
| 7 | the **compositor is born, sees an output**, and an application manages to open a window | same |
| 8 | **capture and the hardware encoder** are reachable, and the frames come out | same |

⇒ ⛔ **The container is acceptable only if all eight behave as on the real machine**
for the points the product really uses. **The outcome becomes `[M]`, with the date.**

## 3.5-bis ⛔ The fallback route, if step 0 fails — **and it is not the one proposed**

Gemini proposes **micro virtual machines** (Firecracker). ⛔ **Rejected**: a virtual machine takes
away the **real graphics card**, which is exactly the reason virtual machines had
already been discarded (D1). On an **integrated** card passing the GPU through to a virtual machine
is not a practicable route, and without the card the numbers of `VA VELOCE` are worth nothing.

⭐ **The two real fallback routes, in this order:**

1. a **system** container instead of an application one (⭐ **suggested by Gemini itself**, and it is
   its good advice on this point): same graphics card, but a real boot inside;
2. ⚠ those tests **stay on the real machine**, and the boxes keep only the rest — with written
   **which** tests were left out and why.

## 3.6 ⛔⛔ The net is a bench too, and it must be certified

`[M]` In phase 10 **six defects were found in the layer that coordinates the benches** — not in the
benches: in the floor they rest on. Among them: a lock with which one could **wait for oneself**
(⛔ 80 minutes of graphics card blocked for five tests, **and no red line anywhere**),
and a global cleanup command that risked **killing the work of another test in progress**.

> ⭐⭐ **The rule: everything a measurement depends on is something to certify — and the fact that it does not
> produce numbers does not exempt it.**

⇒ The net has a `--certifica` of its own: a known fault is injected, and one verifies that the net **sees it**.
⛔ **Every test of the list has, compulsorily, its injected fault** (column «how I know it can
give red» in §4), **and that case must be run, not imagined**.

> ### ⚠ And Qwen's finding (§3.8), accepted: **this way the net is certified against the PAST**
>
> The faults that are injected are faults **already known**. ⛔ But the new desktops will bring faults **of their own**:
> the typical one of GNOME is not necessarily the typical one of KDE.
>
> ⇒ ⭐ **Rule added**: every new desktop comes in with **at least one fault of its own, invented and
> run** — it need not have already happened, it must be **plausible** and the net must see it.
> And the log of what was injected, when, and with what outcome, **is part of the net** (C13).

## 3.7 ⭐⭐⭐ How one stays blind to the desktop — **common list, adapters underneath**

*The two reviewers' convergent answer to the hardest question.*

⛔ **The danger, as Gemini put it**: so as not to write four lists one ends up with **one single list
full of «if the desktop is KDE then…»**, which is the same thing in disguise.

⭐ **The shape that holds — three levels:**

| level | what it says | holds for |
|---|---|---|
| **1 · exists** | the session is born, there is an output, the image is not degenerate | ⭐ **all four, identical** |
| **2 · is seen** | the mark is there, the window is seen, input changes the pixels | ⭐ **all four, identical** |
| **3 · how it is done** | how this compositor is started, which capture protocol, where the mark is put | ⛔ **specific**, and it sits in an **adapter** per desktop |

> ⭐⭐ **The net does not need to know everything about every desktop: it needs to know what to ASK.**
> The main list (C1-C14) stays **one**; every desktop carries a small adapter that answers
> the same four questions.

⚠ **And this does NOT violate D4**, and it must be said because the confusion is easy: D4 forbids exceptions **in the
product** — a KDE branch different from the GNOME branch inside `src/`. ⛔ Here we are in the **bench**, and a bench
that did not know how a compositor is started could not test it at all. ⇒ **The border**: if an
adapter starts to contain *product behaviour* instead of *a way of starting it and
looking at it*, ⛔ **it is a disguised exception**, and it must be removed.

---

# §4 · The list — ⭐ **it is the real net**

⚠ **The two columns that are usually missing are the third and the fourth**, and they are the ones that explain the
three faults of yesterday: *where it starts from* and *what it looks at*.

## 4.1 The product tests

| # | what must be true | ⭐ where it starts from | ⭐ what it looks at | ⛔ how I know it can give red | where it runs |
|---|---|---|---|---|---|
| **C1** | ⭐⭐ **the session is born and is SEEN** | ⛔ **from zero**: user never used, new session, never reused | an image: ⭐ **mark present** *and* **image not degenerate** (§4.2) | (a) session **without monitor** ⇒ red, ⛔ distinguishing *«black»* from *«I did not look»* · (b) ⭐ **image with colours shifted on purpose** ⇒ **must stay GREEN**, or the threshold is too tight and the net gets thrown away in two weeks | boxes |
| **C2** | ⭐⭐ **a window opens** | from zero, new session | ⛔ **the pixel**: the window must be SEEN — the process is not counted | application that dies at once ⇒ red. ⚠ And the check that the process count is **not** enough: `[M]` it said 1 in both cases | boxes |
| **C3** | **the frames arrive, and the scene CHANGES** | new session, **declared and moving scene** | ⭐ **anti-death canary**: frames > 0 · **not collapsed** compared with a rough reference · ⛔ **consecutive frames differ from each other** | the encoder is stopped ⇒ red · ⭐ **the same frame repeated** is sent ⇒ red (frozen image). ⚠ And *«still scene»* must **not** give red | boxes |
| **C4** | **the key gets all the way to the screen** | new session | ⛔ **the pixel, before and after**: image · key · image, and the pixels **of the expected area** must change | the input path is cut off ⇒ red | boxes |
| **C5** | **the sound is there and is not silence** | new session | the bytes that arrive at the client, and that they **are not silence** | the source is removed ⇒ red | boxes |
| **C6** | **it detaches and finds itself again** | session **already alive** (⚠ here that is right) | after the re-attach: same session, same windows, **seen in the image** | the session is killed ⇒ red | boxes |
| **C7** | **everything closes, and nothing remains** | after a finished session | orphan processes, sockets, locks, graphics card back at rest | a process is left on purpose ⇒ red | boxes |
| **C8a** | ⭐⭐⭐ **the SECOND user opens the browser** | ⛔ **from zero, and with TWO users** | ⛔ the pixel: the browser **renders a page** (`#FF00FF`, declared tolerance) | ✅ **measured on 26 Aug 2026**: the provisioning cure is undone ⇒ ⛔ the **second** gives red, the first does not | ⭐ **any box** — it does not go through the product |
| **C8b** | and the same page **is seen FROM THE CLIENT** | as above | the pixel, through the product | ⭐ **measured on 27 Aug 2026**: the verdict is a **difference** — first frame without the page, last with it. Black desktop ⇒ `3`, page already present ⇒ `3`, ⛔ never a free green | ⭐ **gnome**, and only there |
| **C9** | **the log says WHOM it is talking about** | any | every log line has the tenant | the name is removed ⇒ red | boxes |
| **C10** | **the two twin copies of the protocol match** | before compiling | the two files | one of them is changed ⇒ red. ⚠ **it already exists**, and only needs hooking up | everywhere |

### ⭐⭐⭐ What of this list EXISTS, as of 27 Aug 2026 — **all of it**

| | |
|---|---|
| the **product** tests | **C1 · C2 · C3 · C4 · C5 · C6 · C7 · C8a · C8b · C9 · C10** — ⭐ **eleven out of eleven** |
| the tests that look at **the net** | **C11 · C12 · C13 · C14** — and ⭐ **C15**, which was not in the list and was needed |

⛔ **Nothing is blocked any more**, and the reason must be told because it is the story of the day: the five tests
declared «blocked by the blind sessions» **were not blocked**. `[M]` The monitor of a headless session
is born **when a consumer hooks onto the stream** ⇒ **while a client is attached, the
screen is there**, which is exactly the condition in which those five work. ⇒ §7-bis.19.

## 4.2 ⭐⭐ The tests that look at the NET, not at the product

*Qwen's finding §3.12, accepted: **the net can keep running and stop being credible.***

| # | what it verifies | ⛔ the fault it catches |
|---|---|---|
| **C11** | ⭐ **the alignment**: same binary fingerprint in all boxes, recipe declared and dated, ⛔ **no box built with «l'ultima disponibile»** | it is the fault of D5, the one the user saw first: *«remotix v1 su una scatola e v1.2 sull'altra»* |
| **C12** | **the hook is alive**: it exists, it is executable, and there is a trace of the last time it ran | ⛔ **the hook switched off silently** — the way these nets die |
| **C13** | **the certification is recent**: in the last N rounds at least one fault was injected and the net gave red | a net that is no longer able to give red **looks exactly like a net that finds nothing** |
| **C14** | ⭐ **the boxes do not disturb each other**: the same tests alone and in parallel give the same outcome | §3.4 **asserts** it; this **measures** it |
| **C15** | ⭐⭐ **the remote half really runs**: the hook has two halves on two machines, and this one checks that the one with the boxes has not stopped | ⛔ **the fault none of the others catches**: test machine switched off for good, and `[M]` **C12 and C13 stay green**. The sign is not the machine's name: it is **a mesh that wants a box and reaches a judgement instead of a `3`** |

⚠ **They are four, and no more, on purpose.** They are all almost zero-cost and none switches on a
session.

## 4.3 ⭐⭐⭐ How to look at an image without building a fragile test

⛔ **Pixel-by-pixel comparison with a reference image rots within a week**: a
font changes, the background changes, and the test turns red without anything being broken. ⇒ A test that
gives red for nothing **gets switched off by whoever is working**, and it is worse than no test.

### ⛔ And the mark alone is not enough — *finding accepted, both reviewers*

The mark says *«something is there»*, ⛔ **it does not say «what is there is right»**. The cases that would pass:

| | |
|---|---|
| half the screen black, and the mark is in the other half | ⛔ green |
| everything ruined around the mark | ⛔ green |
| **frozen** image: the mark is there, but nothing updates | ⛔ green |

### ⭐ The accepted shape — **three poor checks**, and none knows what a desktop looks like

1. **the mark**, with ⛔ **a declared tolerance** — not the exact colour. *Gemini's finding,
   accepted*: compositors apply colour profiles and rescalings, and an `#FF00FF` can come back
   slightly different. ⛔ A test that demands the exact colour is already dead;
2. **the image is not degenerate**: not all black, not all one colour, varied enough. ⭐ It is a
   **sanity** check, not an aesthetic one, and it does not require knowing how any desktop is made;
3. **the expected area changes** when it must change (C4) and **consecutive frames differ**
   when the scene moves (C3).

⛔ **Computer vision rejected** (SSIM, shape recognition) as proposed by Gemini: it brings
dependencies and weight for a problem that is closed with a **tolerance** and a histogram. ⚠ If the
tolerance were not enough, ⭐ **then** that route comes back on the table — and it will be a decision with a
measurement underneath, not an anticipation.

### ⚠ And the meter must be calibrated before being believed

The mark must be **found when it is there** and **not found when it is not**. ⭐ And the witness
already exists: it attaches to the session with the test client, has the frames given to it from the wire and draws
an image out of them — **with the third outcome distinct**: `0` I looked and it holds · `1` I looked and it does not
hold · ⛔ **`3` I could not look**, which is not a red.

## 4.4 ❓ **THE QUESTION THAT REMAINS FOR THE USER** — C8 and the meaning of D2

⛔ **Both reviewers say the same thing, and it is the most serious finding**: C8 is **the most
important test** — it is half the acceptance test — **and it is the hardest to run**. ⇒ *A test that is costly to
prepare gets run less; a test run less leaves the fault hidden longer.*

⭐⭐ **And they bring a distinction the first draft did not make:**

| kind of test | question | D2 |
|---|---|---|
| **capacity** | *how many users fit together?* | ⛔ **already measured**, not redone |
| ⭐ **correctness with several users** | *does the second user manage to do what they must?* | ⚠ **it is not capacity**, and D2 does not speak of this |

> ## ✅⭐⭐ THE USER'S ANSWER — *26 Aug 2026*
>
> > *«Per quanto mi riguarda un container può anche avere 10 utenti, è un dato già misurato con
> > GNOME.»*
>
> ⇒ ⭐ **C8 sits in a box**, with two tenants — not ten, because the question is correctness,
> not capacity. ⛔ The route «C8 on the real machine with a rebuild script» falls: the
> most important test **will not also be the hardest to run**, which was the two
> reviewers' finding.
> ⚠ And the other half of the finding stays standing, **postponed on purpose**: making three of them (browser ·
> window · input) is evaluated **only after** the first has caught something.

⇒ *(the question that had been asked, and its answer is above:)*

> **Does D2 forbid a container with TWO users devoted to correctness alone?**
>
> | if D2 is **absolute** | C8 stays on the real machine, ⛔ and then **a script is needed that rebuilds the state from zero** — users, folders, the condition that generates the fault, the first user, the second, and the judgement on the image. ⚠ Without that script, C8 is not a test: it is something only whoever was there knows how to do |
> |---|---|
> | if D2 concerns **capacity** | ⭐ a special box with two users, ⛔ **two users and that is all — not ten**, and it does not go back to measuring capacity |

⚠ **And in both cases**, the finding of turning C8 into **three tests** (browser · window ·
input) is ⛔ **postponed**: the phase must stay short, and the third guard of §1.3 holds against the
reviewers too. ⇒ One starts with **one**, and the others are added **only if that one catches something**.

## 4.5 ⛔ The rule on outcomes, which holds for every test of the list

| exit | means | redone? |
|---|---|---|
| 0 / 1 | ⭐ **a judgement** — holds / does not hold | ⛔ **never** |
| **3** | *«non giudico»*: it measured, and some piece could not speak | ⛔ **never** |
| 2 | the terrain does not hold, or the use is wrong | ⛔ never — **a bad terrain is LOOKED AT** |
| **4** | ⭐ **the turn never came** (the card's lock) | ✅ **yes** |

⛔⛔ **And the `3` is NOT put back in the queue, on purpose**: it is the exact route to **measuring twice
until the number one likes comes out**. In a project that has already withdrawn two conclusions for this
reason, the temptation is closed with a rule, not with good will.

---

# §5 · When it starts, and what happens when it says red

⛔ **The three times yesterday when nobody retested the old, nobody was distracted: there simply
was no hook.**

## 5.1 The hook — ⛔ defined by path, not by good will

| when | what runs |
|---|---|
| ⭐ **`src/` is touched** (the product) | the **FUNZIONA** family, on all four boxes together |
| **the benches or the net** are touched | C11-C14 (the net's tests) |
| **before closing a phase** | everything, **VA VELOCE** included, one box at a time |
| **when a new desktop comes in** | everything on the new one, ⭐ **plus the regression on the old ones** — and without rewriting one line of the list |

⚠ **The time cap**, and the two reviewers converge: **under 3 minutes** for the fast family.
Above 5 the risk that it gets switched off begins; above 10 it is almost certain. ⛔ And if the real time
exceeds it **tests are cut**, the cap is not raised.

> ### ⭐ AND NOW THE CAP IS MEASURED — *`[M]` 26 Aug 2026*
>
> The fast family, really run: **153 seconds out of 180**. ⛔ **The cap is full**: any
> extra mesh must be **swapped** with something that goes out, not added.
>
> **C11 + two rounds of C1** fit, and that is all. ⇒ What was left out, and what it costs:
>
> | cut | ⛔ what it costs |
> |---|---|
> | ⛔⛔ **C8, both tests** | **the most expensive cut**: the most important mesh of the list **is not looked at at every change**. It stays in the complete round |
> | **C1 from the third round on** | today it does not bite — `[M]` 10 sessions out of 10 are born blind, and two rounds are enough to notice. ⚠ **The day the defect is cured and becomes rare again, two rounds will not be enough** |
> | **step 0** | it looks at the environment, which does not change when `src/` changes. ⭐ And a box rebuilt behind our back is caught by **C11**, which is in the fast family — that is why it is there |
>
> ⭐ And the hook **skips** the mesh that does not fit instead of truncating it, and **writes in the log what
> it skipped and why**: ⛔ truncating would give a red that does not belong to the product (`LEZIONI.md` §1.45).

### ⚠ Two things about the hook that were decided while writing it

1. ⭐ **It hooks in BEFORE SENDING** (`pre-push`), not at every save. ⛔ Three minutes at every
   commit are exactly the thing this section says gets a hook **switched off**. Whoever wants
   `pre-commit` asks for it by name.
2. ⚠ *«Before closing a phase»* **is not a path**: it is a decision, and it is asked for by name
   (`--famiglia tutto`). ⛔ Pretending that a path can guess it would mean a rule that
   never triggers and nobody notices it has not triggered. ⭐ The arrival of a **new
   desktop** instead is: it shows from a `Contenitore.<nome>` that appears.

## 5.2 ⭐⭐ The red policy — *Qwen's finding §3.7, accepted in full*

⛔ **The document explained very well how to find the red and did not say what happens next.** And the
first important red will generate a discussion, ⇒ **and the discussion costs more than the repair.**

| the case | the rule |
|---|---|
| **red in FUNZIONA** | ⛔ **it blocks**: it is repaired before going on. It is not filed as *«poi vediamo»* |
| **red in VA VELOCE** | it must be understood **before closing the phase**. If confirmed, it blocks the closing; if it belongs to the environment, it is written why |
| ⛔ **intermittent red** | ⛔ **it is a red.** The test is not repeated hoping for green: *«a volte succede»* often means *«succede sempre, aspetta solo il momento»* |
| **repeated outcome 3** | the single `3` is neutral; ⛔ **a frequent `3` is a bench fault**, not an outcome |
| **false alarm** | it can be declared **only after understanding it**, and **it is written down**. ⛔ A test that gives repeated false alarms **is repaired or thrown away** |
| **test that catches nothing** | ⛔ **it is removed, and it is written why.** It is not left to die of disuse |

---

# §6 · ⛔ WHAT THE NET does **NOT** CATCH — *and it must be written, or someone will trust it too much*

*Qwen's finding §3.2-E and Q1, accepted.*

> ⭐ **The net is made against birth faults, visibility faults, basic functioning faults and
> correctness faults between two users.** ⛔ **It is not** a performance net, it is not a compatibility net
> across browsers, and it is not a long-duration test.

| class | why it stays out |
|---|---|
| **subtle visual regressions** — slightly different colours, slightly crooked text, non-degenerate graphical defects | ⛔ by construction: the checks are **poor** on purpose, or they rot (§4.3) |
| **slow memory leaks** — opening and closing a hundred sessions | it needs a long-duration test, which is another job |
| **races between events** that depend on timing | the net runs in quiet conditions |
| **degraded network** — loss, delay, reordering | ⭐ **it is the whole theme of phase 9**, which has its own benches. Here it would be duplicated |
| **different browsers** | the page runs on three engines; the net uses **one** |
| **fine quality of audio and video** | it is the user's judgement (I8), not a bench's |
| **desktop updates** | ⚠ **covered only halfway**: C11 sees that the recipe changed, ⛔ not that the new desktop behaves worse |
| **thermal degradation** | off target |
| ⛔⛔ **PERFORMANCE regressions** | ⭐ declared on 27 Aug 2026: **no bench compares yesterday with today**. A frame that becomes slower without anything stopping working **passes**. ⇒ §3.4 |
| ⛔⛔ **the product on the other three desktops** | `[M]` 27 Aug: the product **can start only GNOME** (`src/sessione.c` · `scrivi_dropin()`) ⇒ on KDE, XFCE and LXQt the net tests **the environment, the sound, the leftovers, the log and the alignment**, ⛔ **not the product**. It is matter for phase 12 |
| ⛔ **the choices never made** | nothing **broke**: that stuff is in `MASTERPLAN.md` (D6), and the net will never catch it — **and that is right** |

> ### ⛔⛔⛔ AND TODAY THERE IS ONE MORE THING THE NET DOES NOT CATCH, and not by choice — *26 Aug 2026*
>
> **The net cannot look at ANY pixel through the product**, and not because it is badly
> written: `[M]` **ten new GNOME sessions out of ten are born without a monitor** (§7-bis.13), that is there
> is nothing to look at. ⇒ ⛔ **C2, C3, C4, C6 and half B of C8** stay out — that is the part
> of the net that should say *«it is seen»* instead of *«it was born»*.
>
> ⭐ **What holds all the same**: C1 (which CATCHES that defect, and it is its job) and **C8a**,
> which looks at the pixel **without going through the product** — and that is the reason it was split in
> two instead of being postponed.
>
> ⚠ **And this is NOT a hole in the net: it is a defect of the product**, opened by phase 10. ⛔ The
> difference counts: a hole is plugged by writing another mesh, this one is plugged **by curing the
> product**, and as long as it is there phase 12 would start with no way of seeing whether GNOME still holds.

---

# §7 · The work plan

⛔ **One single box first, not four.** ⭐ And before that, step 0.

| # | | why in this order |
|---|---|---|
| **0** | ⛔⛔ **STEP 0** (§3.5): half a day, and the `[?]` on `logind` becomes `[M]` | ⛔ **precondition.** Discovering after four boxes that the environment is not the real one is the worst way to spend this phase |
| **1** | the **list** (§4) and the three open decisions | ⛔ the shape of the box depends on what must be tested inside it |
| **2** | **one** box, for GNOME: recipe with the versions, single binary, fingerprint, mark, witness, readable log | |
| **3** | ⭐⭐ **it is pointed at the code of 25 Aug**, and one looks at whether **C1 turns red by itself** | ⛔ **it is the point of no return.** If it catches, the shape is right. **If it does not catch, the others are not built: one understands why** |
| **3-bis** | ⭐ **the WRONG red is tested too**: image with colours shifted on purpose ⇒ **must stay green** | ⛔ *Gemini's finding, accepted*: if the mark falls for a minimal colour deviation, **the net gets thrown away in two weeks** |
| **4** | **acceptance test B** (C8), in the form the user will have chosen (§4.4) | the other half of the acceptance test |
| **5** | the other three boxes, from the mould | ⛔ only now |
| **6** | the net's tests (C11-C14) | |
| **7** | the **hook** (§5.1) | ⚠ last, and **only after the net has caught at least one real fault**: hooking up a net that catches nothing is the fastest way to turn it into ceremony |

---

# §7-bis · ⭐⭐⭐⭐⭐ WHAT WAS DONE — *the night of 25-26 Aug 2026*

> ## ⭐ IN ONE LINE, FOR WHOEVER READS ONLY THIS
>
> | the plan of §7 | where we are |
> |---|---|
> | **0** step 0 | ✅ `[M]` **18/18**, and not on one box: **on all four** |
> | **1** the list and the open decisions | ✅ the list exists; ⭐ the last open question (C8) was closed by the user |
> | **2** one box | ✅ ⭐ **four** — GNOME, Plasma, XFCE, LXQt |
> | **3** ⭐⭐ **acceptance test A** | ✅ **red by itself**, `[M]` 10 blind sessions out of 10 |
> | **3-bis** the wrong red | ✅ in C8's certification: colour shifted ⇒ **stays green** |
> | **4** ⭐⭐ **acceptance test B** | ✅ **caught**: with the fault injected the **second** tenant does not open the browser, the first does |
> | **5** the other three boxes | ✅ done, and ⭐ **without rewriting one line of the list** |
> | **6** the net's tests | ✅ ⭐ **all four**: C11 green · C12 and C13 run · C14 green and measured |
> | **7** the hook | ✅ ⭐ **it exists, and it has already really run**: `[M]` **153 s** on a cap of 180 |
>
> ⛔ **And the thing that weighs most is none of these**: `[M]` **ten new GNOME sessions out of
> ten are born without a monitor** ⇒ half the net — all the meshes that want to look at a pixel
> **through the product** — has nothing to look at. ⚠ It is not a hole in the net: it is the **open** defect
> of phase 10 §7.4. ⇒ §7-bis.13, and the question to the user in §11.

> ## ⭐⭐⭐⭐⭐ ACCEPTANCE TEST A HAS PASSED — **the net turned red by itself**
>
> `[M]` **25 Aug 2026, 22:42 UTC**, the very first round. Pointed at the code of 25
> Aug, inside a box, on **six new users**, mesh C1 said:
>
> ```
>   giro  1/6  NO   CIECA          giro  4/6  ?    NON-LO-SO
>   giro  2/6  ?    NON-LO-SO      giro  5/6  NO   CIECA
>   giro  3/6  NO   CIECA          giro  6/6  ?    NON-LO-SO
>
>   nate con un monitor: 0   ⛔ CIECHE: 3   non giudicate: 3
>   ⛔⛔ ROSSO — 3 sessioni su 6 sono nate CIECHE.
> ```
>
> ⚠ *This is the **first** round. On 26 Aug, with ten users and the bench cured, the number
> became **10 blind out of 10 and zero not judged** — ⇒ §7-bis.13.*
>
> ⛔ **Nobody had told it where to look.** It opens a new session, reads what the product
> says about itself, and judges. ⇒ **The line that triggered it**, taken from the server log:
>
> ```
> 22:42:15.826 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva: e' la sessione
>                                «viva, completa e NERA» di STUDI.md §gnome §3.1
> 22:39:18.145 figlio  ⛔ il palco di «c1u1»: monitor «» (0 prima, 2 dopo), 0x0 stride 0 a 0 bit
> ```
>
> ⭐ And the **third state** of `fasi/10…` §7.4 — *«una volta per utente ne nascono due, senza nome»* —
> ⭐ **reproduced identically**: `monitor «» (0 prima, **2** dopo)`.
>
> ⇒ ⛔ **The fault of 25 Aug lives inside the box.** Which is the second piece of news, and not a lesser one:
> it means the box **does not hide it**, that is, it is the right place to stretch the net.

## 7-bis.1 ⭐ STEP 0 HAS PASSED — `[M]` **18 greens, 0 reds, 0 «I don't know»**

*The heaviest `[?]` of the document has become an `[M]`.*

| # | | outcome |
|---|---|---|
| 0 | the first process is `systemd`, the system starts | ⭐ **yes** (with one single failed unit, `polkit`, declared) |
| 1 | `logind` knows the user, session open | ⭐ **yes** |
| 2 | **linger** switches on and the user manager lives without login | ⭐ **yes** |
| 3 | a user unit starts from inside the session | ⭐ **yes** |
| 4 | session closed, ⛔ **the children really die** | ⭐ **yes** |
| 5 | the private folder is there, is theirs, and belongs **to this box** (tmpfs) | ⭐ **yes** |
| 6 | the session's message channel is there and answers | ⭐ **yes** |
| 7 | the compositor lives, **announces an output**, and a real client draws | ⭐ **yes** |
| 8 | ⭐⭐ **the graphics card and the hardware encoder** | ⭐ **yes**: `iHD 25.2.3`, **3 H.264 encoding profiles** |

> ### ⛔⛔ AND THE PRICE, MEASURED PERMISSION BY PERMISSION — *not one out of habit*
>
> ⛔ **`--privileged` was not used.** A generic permission would have let everything through and
> would have taught nothing. ⇒ What the product **really** asks for:
>
> | permission | ⛔ what breaks without it |
> |---|---|
> | `--device /dev/dri` | ⭐ **the real card.** It is the reason for D1 |
> | ⛔ **`--cap-add=AUDIT_CONTROL`** | `[M]` `pam_loginuid.so`, which in Debian is **`required`**, fails with *«Cannot make/remove an entry for the specified session»* ⇒ ⛔ **the user manager does not start at all**: no session, no channel, no desktop |
> | `--cap-add=AUDIT_WRITE` | goes with the previous one in the same chain |
> | ⚠ `--network=host` | ⛔ **it is not a choice**: `netavark` on this machine does not apply the rules (*«nft did not return successfully»*). ⇒ **Declared price**: four boxes together share the host's ports, so each one has its own (8511-8514) — and it remains to be reviewed at **C14** |
>
> ⭐ **And the discarded route**: removing `pam_loginuid` from the PAM chain would have let everything through
> without extra permissions — ⛔ **and it would have tested a PAM chain different from the one delivered**, that is
> exactly the simulacrum §3.5 exists to prevent.

## 7-bis.2 ⛔⛔ THE FAULT NEITHER OF THE TWO REVIEWERS HAD FORESEEN — **the card's group**

`[M]` At the first round the node `/dev/dri/renderD128` entered the box with the host's group
**number** (991), ⛔ **but inside Debian that number belongs to another group** (`polkitd`).
⇒ The tenant stayed out, and the compositor fell back:

```
libEGL warning: failed to open /dev/dri/renderD128: Permission denied
libmutter-Message: Created surfaceless renderer without GPU
```

> ⛔⛔ **A box that measures SOFTWARE encoding believing it is measuring the hardware** — and
> **no red anywhere**: only worse numbers, which someone would have attributed to the
> desktop. ⭐ It is the shape of *«silence instead of red»* applied to an environment instead of to a
> bench.

⭐ **The cure, and it is not nailing down 991**: a unit inside the box **reads the number from the node**
at startup and aligns the `render` group to it, **declaring it**. ⇒ Nailing down the number would have made
a box that works on this machine and **stays silent** on another.

## 7-bis.3 ⛔ AND TWICE THE DEFECT WAS IN THE BENCH, not in the box

*`REVIEWER.md` §1: the bench is the first suspect. Confirmed twice in one night.*

| | ⛔ what it did | the cure |
|---|---|---|
| **point 4 knocked down the field for the others** | it closes the session to see whether the children die ⇒ it takes away `/run/user/…` ⇒ **points 5, 6 and 7 gave THREE FALSE REDS** | whoever tests the close has the duty to **reopen and verify** before letting the others judge |
| **point 1 judged before having asked** | it read while the user manager was still `activating` ⇒ *«the box does not hold»* when the truth was *«I had not asked anything yet»* | one **prepares** as the product does, waits for the event, **then** judges |

> ⭐⭐ **And the new lesson is the reverse of the known one.** `LEZIONI.md` §1.29 says *«silence instead
> of red»*. ⛔ Here it was **red instead of nothing** — and it costs the same: *a net that gives reds for
> nothing gets switched off by whoever is working*, and then there is no net any more.

## 7-bis.4 ⛔⛔ THE BINARY WAS RIGHT AND THE LIBRARIES WERE NOT — **and the symptom was on the wrong side**

`[M]` The product was put into the box with the libraries taken from the host's `/lib`:
`libngtcp2.so.16` **version 16.2.9**. ⛔ But the real server runs with the one built in
`src/b2/ngtcp2/build/lib`, **16.11.0**. ⇒ **Same name, same `so.16`, different thing.**

| | |
|---|---|
| the server | **started**, said all its startup lines, generated the certificates, began listening |
| ⛔ at the **first client** | it died with `ngtcp2_settingslen_version: Unreachable` |
| ⛔⛔ and the client | saw only **«Idle timeout»** |

> ⭐⭐ **It is the fault the user had named first** — *«se sul container GNOME abbiamo
> remotix v1 e sul container KDE remotix v1.2 andiamo a sbattere»* (D5) — ⛔ **arrived however through a
> door nobody was watching**: not two versions of the product, **two versions of a library with the
> same name.** ⇒ R1 must be read like this: *one single binary **and its libraries**, taken where the
> real server takes them.*

⚠ **And the same family, twice more**: `libei1` and `python3-aioquic` worked because
someone else pulled them along. ⇒ Now the libraries the product asks for are **declared
in the recipe**, line by line, instead of being inherited by chance.

## 7-bis.5 ⭐ THE PRODUCT RUNS INSIDE THE BOX — and the proof is a real client

`[M]` 26 Aug 2026: the test client attached to the server **inside the box**, and was
**ADMITTED in 1004 ms**, with `SESSIONE: stato=1 tela=1920x1080`, staying attached for 30 s without
anything dropping. ⇒ ⭐ The `logind` guardian connected to the system bus **inside the
container**, which was the `[?]` of Q2.

⚠ **And one session, that time, was born with the monitor**: `monitor 1/1: connettore «Meta-0» …
1920x1080@60`. ⛔ **It is not a refutation of the red above: it is the intermittence**, the same that on the
hardware gave `provanic3` **2 successes and 6 failures**.

## 7-bis.6 ⛔ AND TWO THINGS THAT REMAIN OPEN, written down instead of forgotten

| | |
|---|---|
| ⛔ **the box does not switch itself off** | `[M]` a normal `podman rm -f` stayed hung **over four minutes** waiting for an orderly shutdown that did not come, blocking the following commands too. For now it is killed (`-t 0`). ⚠ **It does not touch step 0** (the box is disposable) ⛔ **but it touches C7** — *«everything closes and nothing remains»* — and there that question becomes the target |
| ⚠ **three rounds out of six did not judge** | the stage takes ~13 s to be born and sometimes is not born at all; the declared wait is 45 s. ⇒ They stay **«I don't know»**, ⛔ **and they do not become green** |

## 7-bis.7 ⭐⭐⭐⭐ THE SECOND BOX — **and the same tests run on PLASMA without one line changed**

`[M]` **26 Aug 2026, 04:05 UTC.** A second box was built with **KWin** in place of Mutter,
and the **very same eight checks** said:

> ### ⭐ `regge: 18 · non regge: 0 · non ho potuto guardare: 0`

⛔ **Not one line of the list was rewritten.** Every box carries at the same path an
**adapter** — a short file that answers three questions: *what is your name · what package do you come from ·
how do I switch you on*. ⇒ It is the shape on which **both reviewers** had answered the same thing (Q3,
§3.7), and ⭐ **now it is measured instead of believed**.

### ⛔⛔ And the second desktop at once asked for something the first did not ask for — **twice**

| | ⛔ what happened | ⭐ what it teaches |
|---|---|---|
| **the card's group did not exist** | in the GNOME box `render` was already there: it was brought by a package that `gnome-shell` pulls along. ⛔ In the Plasma one **it does not exist**, and the recipe died with `usermod: group 'render' does not exist` | the first desktop was not «right»: it was **generous**, and it hid a dependency nobody had declared |
| ⛔⛔ **KWin did not start at all** | `env: 'kwin_wayland': Operation not permitted`. ⇒ `/usr/bin/kwin_wayland` carries `cap_sys_nice=ep`, and **a program with a permission written on the file does not start** if that permission is not in the box's set | ⭐ a new desktop can ask for **permissions** the first did not ask for — and the symptom looks nothing like the cause |

⭐ **The cure is per desktop and declared**: `SYS_NICE` goes **only** to the Plasma box. ⛔ Giving it to
all of them would mean testing GNOME in an environment different from the one in which it really runs — that is
moving the box away from the product for our own convenience.

> ### ⭐⭐⭐ AND THIS IS THE THESIS OF THE PHASE, HAPPENING AT THE FIRST ATTEMPT
>
> Two things the second desktop brought out **in ten minutes**, and which inside phase 12 —
> in the middle of the new code, with Plasma to make work — would have cost half a day **and a
> wrong diagnosis**: they would have looked like defects of our KDE code.
>
> ⇒ ⛔ **It is exactly the reason the user put this phase BEFORE the new desktops.**

⚠ **And what this box does NOT do, today**: the product cannot yet switch on KDE (it is phase 12),
so in there **only** the environment checks run. The net's meshes that want the
product — C1 and the others — run for now **only on GNOME**.

## 7-bis.9 ⭐⭐⭐⭐⭐ THE THIRD AND THE FOURTH BOX — **and all four are standing**

`[M]` **26 Aug 2026, 03:5x UTC.** The **XFCE** and **LXQt** boxes were built, and the very
same list of eight checks — ⛔ **not one line changed, again** — said:

> ### ⭐ XFCE `regge: 18 · non regge: 0 · non ho potuto guardare: 0`
> ### ⭐ LXQt `regge: 18 · non regge: 0 · non ho potuto guardare: 0`

⇒ ⭐⭐ **Four boxes, four desktops, one single list of tests.** The desktop blindness of §3.7
is no longer a proposal: it is `[M]` on four compositors, and the cost of adding one is **an
adapter of forty lines**.

### ⛔ And an uncomfortable thing, said before someone discovers it by counting wrong

**The boxes are four; the compositors are THREE.** XFCE and LXQt do not bring a compositor of their own
on Wayland: they bring a **session** and lean on one of the `wlroots` family — and the choice, for
both, is **labwc**. ⛔ It is not a convenience of this phase: `DECISIONI.md` has already measured
resizing under the label **«labwc (XFCE, LXQt)»** (`[M]` 5.1 ms, 0 frames lost out of
25), and `PIANO.md` phase 13 says it in one line — *«il terzo e il quarto desktop, che condividono
wlroots e quindi quasi tutto»*.

⇒ ⚠ **What the fourth box really puts to the test**: a fourth **session**, a fourth
**recipe**, different dependencies, and an idle daemon that `DECISIONI.md` already takes as **different**
from XFCE's. ⛔ **Not** a fourth compositor. Whoever reads the results should count this way.

### ⭐ And the third desktop asked for nothing new — *and it is a result, not a non-event*

⛔ The second desktop had asked for **two** things the first did not ask for (§7-bis.7). The third and the
fourth: **zero**. `labwc` carries no permissions written on the file, does not demand groups that are not there,
and is born without a screen with `WLR_BACKENDS=headless` — the third different word for the same thing, after
Mutter's `--headless` and KWin's `--virtual`, ⭐ **and it all sits in the adapter.**

⚠ And it must be read for what it is: **not** *«so the new boxes are free»*. It is **one** desktop that
asked for nothing after **one** that had asked for two things — that is the reason the question
is asked of each one instead of generalising from the first.

## 7-bis.10 ⭐⭐⭐⭐⭐ ACCEPTANCE TEST B HAS PASSED — *C8 catches the defect, and catches it from the SECOND*

⛔ It was the open question of the phase (§4.4), closed by the user on 26 Aug: **C8 sits in a box,
with two tenants.** ⇒ It is written, it is certified, ⭐ **and it caught the fault.**

> ### `[M]` 26 Aug 2026 — the two lines that are worth the phase
>
> **with the provisioning cure:**
> `c8u1 ⭐ la pagina copre il 98,7 % · c8u2 ⭐ la pagina copre il 98,7 %`
>
> **without the cure** (the fault injected, that is the code of 25 Aug):
> `c8u1 ⭐ la pagina copre il 98,7 %` · ⛔ `c8u2 NO — profilo: è di «c8u1» · sa scrivere in ~/.cache/mozilla: NO`

⭐⭐ **And the asymmetry is the right one**: the **first** opens the browser, the **second** does not. ⛔ A red on
both would not have been the defect of §4.6-undecies — it would have been the bench — and ⭐ **now it is
C8 itself that says so**, instead of leaving it to be deduced by whoever reads (§7-bis.12).

### ⛔⛔ AND C8 HAD TO BE SPLIT IN TWO — *the reason must be read before the numbers*

| | what it looks at | today |
|---|---|---|
| ⭐ **A · the browser renders the page** | Firefox photographs itself, as the user, on the machine as it is configured. ⛔ The judgement stays **in the pixel** | ✅ **it is measured**, and it is what caught the fault |
| **B · and the page is seen FROM THE CLIENT** | the same page, looked at **through the product** | ⚠ **today it is not measured** |

⛔⛔ **Why B is not measured**: `[M]` 26 Aug 2026, inside the box **no new GNOME session
is born with a monitor** — it is the **OPEN** defect of phase 10 §7.4, *«la sessione che nasce cieca»*,
which sits **upstream** of C8. ⇒ ⭐ **A black desktop does not testify about the browser**: calling that «C8's
red» would mean blaming the browser for something that happened **before the browser existed**.
⚠ So B says *«I could not look»* and **names the why**, and it never becomes a green.

⭐ **And the split has a gain that was not foreseen**: test A **does not go through the product**, and
so it runs in **any** box — even in one where the product is not even present. ⛔ The acceptance test
above ran inside the **PLASMA** box.

### ⭐ The bench choices that count

| | |
|---|---|
| ⭐ **it prepares its terrain itself** | it puts `/etc/skel/.cache -> /tmp`, that is **it reproduces the configuration of the real machine** — which is an **owner's choice**, not a fault. ⛔ Testing on a clean skeleton would answer an easier question than the real one |
| ⭐ **the tenants are born as the product makes them** | `useradd -m`, which copies the skeleton. ⛔ A cleaner route here would test a product different from the one delivered |
| ⭐⭐ **the target in the pixels is a COLOUR** | the page is `#FF00FF` full screen, and one measures **how much of the image has become that colour** — tolerance **±48 per channel**, at least **25 %**. ⛔ No desktop puts that colour on by itself: the meter does not need to know what GNOME looks like |
| ⛔ **the reason next to the symptom** | «it did not draw» on its own hides three faults: the browser dead, the profile never born, the page not full screen. It tells them apart and prints them — ⭐ and that is how one reads *«profilo: è di «c8u1»»* |
| ⛔ **and it does not look at the link** | looking at the cause we believe we know instead of the effect we care about would mean a test that goes silent the day the cure changes |

### ⭐ The judge's certification — `[M]` **8 cases out of 8**

| the case | why it is there |
|---|---|
| full page · desktop without browser · black screen | the minimum: it sees when it is there, it does not see when it is not |
| ⭐ **colour shifted by (−30, +30, −30) ⇒ must stay GREEN** | compositors apply colour profiles and the chain goes through a **4:2:0** H.264, which subsamples precisely the chroma. ⛔ A test that demands the exact colour is already dead (§4.3, Gemini's finding) |
| colour shifted **too much** ⇒ must stay RED | or the tolerance no longer separates anything |
| a small stain is not a page | a window that opens and does not draw |
| ⛔ **the file that is not there and the empty file ⇒ «I don't know», not zero** | *«I did not look»* and *«I looked and it was not there»* are two different things |

⚠ **And the certification is declared for what it covers**: the **pixel reader**. ⛔ It does not cover that the
browser really started — that is said by `--senza-cura` on the real thing, and it is the acceptance test above.

## 7-bis.11 ⛔⛔⛔ **FOUR TIMES THE DEFECT WAS IN THE BENCH** — *and the four lessons*

⚠ **It must be written, and written in full**: before catching the real fault, the bench got it wrong
**four times** — three false reds and ⛔ **one false green**. ⭐ Each one is a form of error this
phase exists not to repeat, and all four ended up in `LEZIONI.md`.

| | ⛔ what happened | ⭐ the lesson |
|---|---|---|
| **the predicate that could not fail** | *«try to write in `~/.cache`»* — ⛔ but with the link `~/.cache` **is `/tmp`**, writable by anyone (`1777`). ⇒ It said **yes** even for the tenant whose browser would not open | `LEZIONI.md` §1.44 — **applying E1 is not enough: one must apply it IN THE PLACE THAT BITES** (`~/.cache/mozilla`), or the predicate ⛔ looks the same as one that passes |
| **the borrowed cap** | Firefox's first start in a cold box goes over 25 s, and the bench gave it the cap meant for another wait ⇒ ⛔ **red for both, with the cure and without** | `LEZIONI.md` §1.45 — ⛔ and the real damage is not the false red: it is that **the acceptance test stops counting**, because it no longer tells the fault from the bench |
| **the bench that gave itself red** | the working folder belongs to `root` with mode `0755`, and Firefox runs **as the user** ⇒ it could not write the image there, and the bench read *«the browser did not draw»* | ⭐ the cure: **it takes the snapshot in its own home**, and `root` takes care of bringing the image out afterwards |
| ⛔⛔ **and a FOURTH, which is worse than a red** | a command nested three times (`ssh` → `systemd-run` → `podman exec sh -c`) lost its quotes, **executed nothing** and returned **`0`** | `LEZIONI.md` §1.46 — ⛔ **a green without any measurement underneath**, identical to a successful round. ⇒ No shells in between, and **a bench that prints nothing has not «succeeded»** |

> ### ⭐⭐ And the thing that holds them together
>
> The first three gave **red**, and they belonged **to the bench**. ⛔ In a phase that builds a safety
> net this is danger number one of §1.3: *«a net that gives red for nothing gets switched off by
> whoever is working»*. ⇒ ⭐ **The injected fault caught all three**, and in ten minutes: without
> `--senza-cura` they would have passed for «the defect is there, look at that red».
>
> ⛔⛔ **The fourth did not**, and that is why it stands apart: a **green** is caught by no injected fault,
> because the injected fault serves to check that one can give red. ⇒ ⭐ Against that one needs
> the other rule: **demand to see the lines**. A mute bench is not a happy bench.

## 7-bis.12 ⛔ AND A NEW GUARD, BORN FROM THOSE REDS: **«the FIRST failed too»**

The fault of §4.6-undecies bites **from the second tenant on**. ⇒ ⭐ If with the fault injected
**the first** gives red too, what is being measured **is not that fault**.

⛔ C8 now says it by itself, and in that case **exits 1 instead of 0** — that is *«the acceptance test does not count»*, and
not *«the acceptance test succeeded»*. ⚠ It is the exact reverse of the trap: a mesh that celebrates a
red without looking at **whose** it is.

## 7-bis.13 ⛔⛔⛔ **TEN NEW SESSIONS, ZERO WITH A MONITOR** — *and the bench that now judges all ten*

`[M]` 26 Aug 2026, C1 inside the GNOME box, **ten** new tenants, stage wait
raised to **90 s**. Two rounds, and the second after a cure to the bench:

| | outcome |
|---|---|
| first round | `nate con un monitor: 0 · ⛔ CIECHE: 5 · **non giudicate: 5**` |
| ⭐ second round, with the bench cured | `nate con un monitor: 0 · ⛔ **CIECHE: 10** · non giudicate: **0**` |

⭐ **The red is the expected one**, and it is acceptance test A holding: the mesh points at the code of 25 Aug
and turns red on the defect of phase 10 §7.4. ⛔ **And the number is worse than what the phase
document let one hope**: not «intermittent», but **ten out of ten**. ⚠ It is consistent with the measurement on the
hardware (`provanic4/5/6`: **never**, over 98 · 55 · 50 attempts) — ⇒ for a **new** user the fault is not
rare: **it is the rule**.

> ⛔⛔ **And this is the fact that blocks half of C8** (§7-bis.10, test B), and not only: it blocks **all**
> the meshes that want to look at a pixel through the product — C2, C3, C4, C6.
> ⇒ ⚠ **And the fact, without advice**: starting phase 12 with this open would mean making
> KDE work **with no way of seeing whether GNOME keeps working**. ⭐ The choice is
> the user's, and it is in §11.

### ⭐⭐ The bench's cure: **the five «I don't know» alternated, and it was the clearing**

⛔ The first round had given `? NO ? NO ? NO ? NO ? NO` — **one yes and one no, ten rounds in a row**. ⚠ A
perfect alternation is not chance: it is **a state that survives the round**.

⇒ ⭐ **It was the clearing**: `loginctl terminate-user` plus `pkill` return **at once**, and the next round
started while the previous one was still dying — the new compositor could not even manage to be
born, and the log said neither «monitor» nor «blind». The round after that found the field
free and judged.

⛔ **The cure is the usual rule: one waits for the EVENT, not for the clock.** Now C1 waits
until the previous round's tenant has **neither session nor processes**, and if it has not gone within the
declared time **it says so**, instead of starting while pretending not to know.

> ### ⭐ And the result is the difference between a bench and a bench that is useful
>
> `non giudicate: 5` ⇒ `non giudicate: **0**`. ⚠ None of the five was a red — the mesh had the
> decency not to judge (§4.5) — ⛔ **but a test that judges half the time is worth half.**

### ⚠ And the TIME, measured instead of estimated — *criterion §9.9*

`[M]` The ten rounds lasted **12 minutes and 20 seconds**: ⭐ **74 seconds per round**.

⇒ ⛔ **The 3-minute cap for the fast family fits only TWO rounds.** ⚠ And this is a
number taken **with the defect open**: every round spends the whole stage wait (90 s cap) and
then the clearing. ⭐ With healthy sessions the round will be much shorter — ⛔ but until it is, the
hook cannot run ten rounds of C1 at every change: **tests are cut, the cap is not
raised** (§5.1).

## 7-bis.14 ⭐⭐⭐ **C11 IS ALIVE AND SAYS GREEN** — *the mesh that looks at the net, not at the product*

⭐ It is the fault the user named **first**, in his own words: *«se sul container gnome
abbiamo remotix v1 e sul container kde remotix v1.2 andiamo a sbattere»* (D5). ⇒ Now there is a
mesh that goes looking for it, and `[M]` **26 Aug 2026**:

> ### ⭐ `le 4 scatole accese sono allineate su tutte le 13 voci dichiarate`

| ⭐ must be equal | ⛔ must be different |
|---|---|
| the base (`13.6`) · mesa · libva · pipewire · libavcodec · ffmpeg · **firefox-esr** · libc · libssl · libei · libpci · ⭐ **the md5 of the product binary** | **the desktop** — `gnome-shell 48.7` · `kwin-wayland 6.3.6` · `labwc 0.8.3` · `labwc 0.8.3` |

⛔⛔ **And one looks at what is INSIDE the running boxes, not at what is written in the recipes.** The
recipes are different **on purpose**, and a comparison that must first «remove the different parts» becomes
a comparison one argues about. ⇒ It is rule E1 applied to the environment: *written is not in force*.

⚠ **The first round was RED**, and for the right reason: the product was **only** in the GNOME
box. ⭐ With the very same binary put into all four, it turned green — ⇒ **the mesh
did exactly its job at the first shot.**

### ⛔⛔ And it too had its defect, which is the most insidious of all

`[M]` Three entries out of thirteen asked for packages with the wrong name (`libssl3` instead of `libssl3t64`).
⇒ All four boxes answered **`?`** — and ⭐⭐ **`?` equal to `?` is equal**: those three
entries **passed the comparison**, forever, without looking at anything.

> ⇒ ⭐ C11 now **counts and prints them**: *«N voci a cui nessuna scatola sa rispondere — e una voce
> muta passa il confronto senza aver guardato niente»*. `LEZIONI.md` §1.47.
>
> ⚠ It is the same form of error as §1.44 seen from another side: there the predicate always said yes,
> here the comparison always said equal. ⛔ **A check that has never given red in its life must be
> looked in the face, not celebrated.**

## 7-bis.15 ⭐⭐⭐⭐ **C14 — THE FOUR BOXES DO NOT DISTURB EACH OTHER**, and now it is measured

§3.4 **asserted** it; ⭐ now there is the measurement underneath. `[M]` **26 Aug 2026**, the same test
(C8a) run **one box at a time** and then **all four together**:

| | alone | together |
|---|---|---|
| with the fault injected | `1 sì · 1 no` × 4 | `1 sì · 1 no` × 4 |
| with the cure | `2 sì · 0 no` × 4 | `2 sì · 0 no` × 4 |

⇒ ⭐ **The very same outcome, four boxes out of four, in both modes.**

### ⭐ And the line `11-accendi.sh` carried open is closed

*«`--network=host` … quattro scatole accese insieme condividono le porte dell'ospite … **da rivedere
quando si fa C14**»*. ⇒ ⭐ **Reviewed, and it holds**: each listens on its own port, each recognises
as **its own** only its own and as **someone else's** the other three. The separation by port **is a real
separation**, and now it has a measurement underneath instead of a hope.

### ⚠ The time — which is information, not a verdict

`[M]` **6.6 s alone → 7.0 s in parallel**, that is **×1.06**. And the total drops from 26.2 s to 7.0 s:
⭐ **parallelism saves ×3.76**.

⛔ **And a measured time was THROWN AWAY, and the bench declares it by itself**: with the fault injected the
four times were `125,9 · 126,0 · 126,0 · 126,1` s. ⚠ Four numbers equal to a tenth are not
chance: with the fault the second tenant does not open the browser and C8 **waits** for it up to its cap.
⇒ That time is almost all **our own fixed waiting**, not work — and calling it «contention» would mean
measuring one's own cap and believing it a defect of the product.

### ⛔⛔ And what it does NOT measure, declared

**It does not measure the real contention on the graphics card.** Test A of C8 switches on a browser that draws
**in software**: it does not touch the card. Real contention would want four live sessions, and the
sessions today are born blind (§7-bis.13). ⇒ What is measured is **the layer underneath**: the four
boxes manage to **open the encoder at the same instant** (3 H.264 profiles each, alone and
together). ⭐ If even this did not hold, the real contention would not need testing.

### ⭐ And the certification failed the bench itself

`[M]` **15 cases out of 15**, but only after a correction: the first judge threw away the judgement when
**only one** box had managed to answer. ⛔ Wrong — *a box that runs and cannot manage to
report is still occupying the machine*, so the load is there and the judgement of the others counts.

⭐ **And the proof that it can give red on real data, not only on the fake cases**: `--smentisci` runs the
parallel asking on purpose for the **other** mode of C8, so the fingerprints *must* be different ⇒
**4 boxes out of 4 red.**

## 7-bis.16 ⭐⭐⭐ **THE HOOK, C12 AND C13** — *and the first real round*

⛔ The plan said to make the hook **last, and only after the net had caught at least one
real fault**: *«hooking up a net that catches nothing is the fastest way to turn it into
ceremony»*. ⇒ The condition is met — the net caught two.

| | |
|---|---|
| `11-gancio.sh` | decides **by path** · runs · **leaves a trace** · installs itself as a git hook |
| `11-c12-il-gancio-e-vivo.py` | it exists, it is installed, it has **really** run and recently. ⛔ It catches **the hook switched off silently** |
| `11-c13-la-certificazione-e-recente.py` | in the last rounds a fault was injected **and was seen** |

⭐ **Certifications: 11 out of 11 each.** And the case that keeps C13 standing deserves to be written down:

> ⛔ **A red coming from another mesh certifies nothing.** If in a round the net turned
> red on its own (C1 on the blind session) **and** the injected fault was **not** seen, a
> naive C13 would say «certified»: the round carries written *gave red* and *fault injected*.
> ⇒ ⭐ This one gives **red**, and gives **the name of the mesh** that missed the fault.

### ⛔⛔ The tests CUT to stay within the 3 minutes — *and the cut is declared, not suffered*

`[M]` A round of C1 costs 74 s ⇒ **two rounds** fit in the 180 s. In the fast family there remain
**C11 + C1×2**. Out:

| cut | ⛔ what it costs |
|---|---|
| ⛔⛔ **C8, both tests** | **the most expensive cut**: the most important mesh **is not looked at at every change**. It stays in the complete round |
| **C1 from the third round on** | today it does not bite (10 out of 10 are born blind, and two rounds are enough) ⚠ **but the day the defect is cured and becomes rare again, two rounds will not be enough** |
| **step 0** | it looks at the environment, which does not change when `src/` changes; and a box rebuilt behind our back is caught by **C11**, which is in the fast family |

⭐ And the hook **skips** the mesh that does not fit instead of truncating it halfway, and **writes in the log
what it skipped and why**: ⛔ truncating would give a red that does not belong to the product (`LEZIONI.md`
§1.45).

### ⚠ And the hook hooks in BEFORE SENDING, not at every save

Three minutes at every commit are exactly the thing §5.1 says gets a hook **switched off**. ⇒ The
default is `pre-push`; whoever wants `pre-commit` asks for it by name.

⚠ And something the path **cannot say**, declared instead of hidden: *«before
closing a phase»* is not a file that changes, it is a **decision** ⇒ it is asked for by name
(`--famiglia tutto`). ⭐ The arrival of a new desktop instead **can**: it shows from a
`Contenitore.<nome>` that appears.

### ⛔⛔ THE FIRST REAL ROUND — and it found three things no dry test had caught

`[M]` 26 Aug 2026. The hook was built **without the test machine** (the agent writing it
did not have it, and declared so). ⇒ At the first real round:

| ⛔ what happened | ⭐ what it teaches |
|---|---|
| ⛔ **`GIRA_C11: command not found`** — a function that does not exist. The outcome was **127**, and the round went on as if nothing had happened: the fast family ran **without its first mesh** | ⚠ `bash -n` passes, because the syntax is valid (`LEZIONI.md` §1.40). ⛔ **It can be seen only by running it** |
| ⛔ **the hook demanded a git repository in order to RUN** | ⭐ the two halves live in two different places: **deciding** wants the repository (laptop), **running** wants the boxes (test machine, where the repository **is not**). ⇒ With the family asked for by name there is nothing to decide, and the repository is not needed |
| three `git: command not found` per round | noise that looks like a fault ⇒ without a repository nothing is listed, and **it is not an error** |

### ⭐⭐⭐ AND THE COMPLETE ROUND WAS DONE — *`[M]` 26 Aug 2026, 28 minutes*

The `tutto` family on GNOME, the one done **before closing a phase**, run by the hook from
beginning to end:

| mesh | outcome | time |
|---|---|---|
| step 0 | ⭐ holds — 18/18 | 16 s |
| C1 × 10 | ⛔ **DOES NOT HOLD** — 10 blind out of 10, **zero not judged** | 760 s |
| C8 | ⭐ holds — both tenants open the browser | 6 s |
| ⭐⭐ **C8 with the fault injected** | ⭐ **the fault was SEEN**: 1 tenant out of 2 does not open the browser | 126 s |
| C11 | ⭐ holds — 13 entries out of 13 | 10 s |
| C12 | ⚠ *terrain does not hold* — ⛔ and **it is the right answer**: on that machine there is no git repository, and C12 looks at the git hooks | 0 s |
| C13 | ⛔ DOES NOT HOLD **during the round**, ⭐ **green right after** | 0 s |
| C14 | ⭐ holds | 786 s |
| | | **total 1 704 s** |

> ### ⭐⭐ And the moment that counts is C13's
>
> During the round C13 was **red**, and it told the truth: *«negli ultimi giri **nessun guasto è mai
> stato innestato** ⇒ la rete gira, e nessuno la mette alla prova. ⛔ Da fuori è indistinguibile da
> una rete che funziona benissimo.»*
>
> ⇒ Once the round was over — which **had** the injected fault inside it — C13 is **green**:
> *«negli ultimi 3 giri un guasto è stato innestato ed **è stato visto**»*.
>
> ⭐ **That is, the net can now say of itself whether it is still able to give red.** ⚠ And it says so with
> its limit attached: *«sui guasti che CONOSCE — e ogni desktop nuovo deve entrare con un
> guasto suo»* (§3.6).

⚠ **And two readings that must be done carefully**, because they look like good news and are not:

| | |
|---|---|
| **C1 × 10 costs 760 s** | ⭐ 76 s per round, consistent with the 74 measured before. ⛔ It is the reason **two** fit in the fast family, and it is not a number that can be improved by cutting: it is the time the product takes **not** to give birth to a monitor |
| **C8 lasted 6 s** | ⚠ **it is not its real speed**: the tenants were already there from the round before, with the browser profile already made. ⛔ From zero it costs much more — the other row says so, the **126 s** of the round with the fault injected |

## 7-bis.17 What exists now, on disk

| file | |
|---|---|
| `banchi/11-scatole/Contenitore.gnome` | ⭐ the box's **recipe**: system, desktop, card, tools, the tenant, and the unit that aligns the card's group |
| `banchi/11-scatole/11-accendi.sh` | build · switch on · product · server · **c1** · **c5** · **c7** · **c8** · **c9** · **c10** · step0 · fingerprint · switch off — ⭐ **with every permission justified by what breaks without it** |
| `banchi/11-scatole/11-passo0.sh` | ⭐ the **eight checks** of the environment, with the three distinct outcomes |
| `banchi/11-scatole/11-c1-nasce-e-si-vede.py` | ⭐⭐ **the first mesh of the net**, and acceptance test A. With `--certifica`: **5 cases out of 5**, including the one in which *«cieca»* must win over *«monitor 1/1»* |
| `banchi/11-scatole/Contenitore.kde` | ⭐ the **second box**, with KWin — the proof that the net is not tailor-made for GNOME |
| `banchi/11-scatole/Contenitore.xfce` · `Contenitore.lxqt` | ⭐ the **third and the fourth**, with `labwc` — ⚠ four boxes, **three** compositors (§7-bis.9) |
| `banchi/11-scatole/adattatore.{gnome,kde,xfce,lxqt}.sh` | ⭐⭐ **the «how» of every desktop**, at the same path inside every box: the list of tests stays **one** |
| `banchi/11-scatole/11-c8-il-secondo-apre-il-browser.py` | ⭐⭐⭐ **the most important mesh**, and acceptance test B. With `--certifica`: **8 cases out of 8**; with `--senza-cura`: the injected fault |
| `banchi/11-scatole/11-c8-pagina.html` | the **target in the pixels**: `#FF00FF` full screen, with the writing there on purpose so as not to be «solid colour» |
| `banchi/11-scatole/11-c11-allineamento.py` | ⭐⭐ **the mesh that looks at THE NET**: the four boxes agreeing on thirteen entries, and the product's md5 among them. With `--certifica`: **6 cases out of 6** |
| `banchi/11-scatole/11-c14-non-si-disturbano.py` | ⭐⭐ **the four boxes do not disturb each other**, measured: same outcome alone and together. With `--certifica`: **15 cases out of 15**; with `--smentisci`: it gives red on real data |
| `banchi/11-scatole/11-gancio.sh` | ⭐⭐⭐ **when the net starts, and what starts** — decided **by path**, with the 3-minute cap and the cut tests declared |
| `banchi/11-scatole/11-gancio-registro.jsonl` | the **trace** of every round: what started, what outcome, how long it lasted, whether a fault was injected. ⛔ It is what keeps C12 and C13 alive |
| `banchi/11-scatole/11-c12-il-gancio-e-vivo.py` · `11-c13-la-certificazione-e-recente.py` | ⭐ the two meshes that look at **the hook**. `--certifica`: **11 cases out of 11** each |
| `banchi/11-scatole/11-c5-il-suono-non-e-silenzio.py` | ⭐⭐ **the sound**: the **RMS** of the samples arriving at the client is measured, declared threshold **328/32767** (−40 dBFS). ⭐ It judges **bytes**, not pixels ⇒ it is the only mesh that today crosses the product from top to bottom. `--certifica`: **12 cases out of 12** |
| `banchi/11-scatole/11-c7-si-chiude-e-non-resta-niente.py` | ⭐⭐ **the leftovers**: fingerprint before, session, close, fingerprint after. ⚠ And the case that must **not** give red: «it only detaches» (I4). `--certifica`: **13 cases out of 13** |
| `banchi/11-scatole/11-c9-il-registro-dice-di-chi.py` | ⭐⭐ **the log**: two tenants alive **together**, and every compulsory line must say which. `--certifica`: **16 cases out of 16** |
| `banchi/11-scatole/11-c10-le-copie-gemelle.py` | ⭐ **the twin copies**, and ⛔ it **reads** the list **from `src/Makefile`** instead of copying it. `--certifica`: **15 cases out of 15**. ⭐ It runs **everywhere**, in 0.04 s, and switches nothing on |
| `banchi/10-f1-testimone.py` | ⛔ **it does not belong to this phase and is not touched**: it is the judge of the images, already calibrated on the real thing. C8 **imports** it — two judges that can diverge silently are worse than one |

## 7-bis.18 ⭐⭐⭐⭐⭐ **FOUR MORE MESHES — and the net now also looks at what is not a pixel**

`[M]` 26 Aug 2026, evening. Four agents in parallel, **one box each** (kde, xfce,
lxqt, and the laptop), tenants with separate prefixes, separate logs and units. ⭐ And the criterion of the
choice is one only: **none of the four judges a pixel** ⇒ they are the four that the defect of the
blind sessions (§7-bis.13) **does not block**.

| mesh | the meter | certification | cost `[M]` |
|---|---|---|---|
| **C5** the sound is not silence | **RMS** of the samples arriving at the client · threshold **328/32767** (−40 dBFS) · ≥ 200 blocks · ≥ 50 % above threshold | **12 out of 12** | 38 s |
| **C7** everything closes and nothing remains | fingerprint **before** / session / close / fingerprint **after** — processes, sockets, units, card | **13 out of 13** | 26 s |
| **C9** the log says whom it is talking about | **two** tenants alive together, and every compulsory line must say which | **16 out of 16** | 50 s |
| **C10** the twin copies | the three twin files byte for byte, ⭐ with the list **read from `src/Makefile`** | **15 out of 15** | 0.04 s |

### ⭐ And C5's calibration was done crossing the border, not declared

`[M]` Six real sessions: amplitude **0.02 ⇒ RMS 463, GREEN** · amplitude **0.01 ⇒ RMS 231, RED**. The
path is transparent (gain **1.0000**), and the synthetic values of the certification coincide
with those of the wire (463.4 against 463.1). ⛔ A threshold that has not been seen failing is an invented
number.

### ⭐⭐ And C5 proves its thesis with a number, instead of asserting it

In the same round in which the log said *«nessun monitor virtuale da catturare»* and *«0 fotogrammi
spediti»*, C5 counted **4 878 sound blocks, 4.6 MB, RMS 23 168**. ⇒ ⭐ **Zero pixels, and
something to judge all the same**: today C5 is the only mesh that crosses the product from top to
bottom.

### ⛔⛔ THE FIRST RED THE NET DRAWS OUT OF THE PRODUCT — **two lines of `src/tastiera.c`**

`[M]` C9, on **all four** boxes: 5 752 log lines, **5 490 compulsory**, and **4** that
cannot be attributed to any tenant. They are `src/tastiera.c` and `:486`, which write in the
**parent** without `registro_dice_di()`. ⛔ Two lines identical word for word, one per tenant:
**with two live sessions one cannot say which belongs to whom.**

⭐ It is not an injected fault, it is not a bench getting it wrong: **it is the product**, and nobody was
looking for it. The cure is two lines — ⛔ **not applied**, because touching `src/` forces a rebuild and
putting the binary back into four boxes, and the order of the phases is the user's decision (§11).

⚠ **And next to it, a finding that is NOT a red**: `[M]` **1 402 lines (25.5 %)** name the tenant
only in the prose and not in the bracket. They are attributable ⇒ C9 counts and prints them without judging them.
Wanting them red is a decision, not a defect.

### ⛔⛔⛔ THE SECOND RED — **and this time it belongs to ONE desktop only**

`[M]` With the meshes wired in, **all three were run on all four boxes**, with their
injected faults. Twenty-eight rounds. And this came out:

| | gnome | kde | xfce | lxqt |
|---|---|---|---|---|
| **C5** the sound | ⛔ **RED** | ✅ | ✅ | ✅ |
| C5 with the fault injected | ⭐ seen | ⭐ seen | ⭐ seen | ⭐ seen |
| **C7** the leftovers | ✅ | ✅ | ✅ | ✅ |
| C7 «only detaches» (I4) | ✅ | ✅ | ✅ | ✅ |
| C7 with the fault injected | ⭐ seen | ⭐ seen | ⭐ seen | ⭐ seen |
| **C9** the log | ⛔ red *(the product defect, the same everywhere)* | ⛔ | ⛔ | ⛔ |

⭐⭐ **C5 is green on three desktops and red on the fourth**, and the fourth is **GNOME** — that is the one on which the
product was born. The numbers:

| | gnome | kde / xfce / lxqt |
|---|---|---|
| blocks arrived at the client in 25 s | `[M]` **34 – 41** | `[M]` **~4 878** |
| blocks entered into the encoder | `[M]` **115** | `[M]` **~4 996** |
| of which digital silence, muted | `[M]` **74 out of 115** | ~2 % |
| RMS of what arrives | **22 977** (loud) | 23 168 |

⇒ ⛔ **It is not «the sound is missing»: it is that a fortieth of it arrives.** What arrives is loud and right
(RMS 22 977, peak at full scale, 100 % above threshold): ⭐ **the threshold has nothing to do with it**, and in fact C5 does not
give red for the level but for the **count** — *«41 blocchi su 200 attesi al minimo: non è un
flusso»*.

⚠ **And it is not the aged box**: the GNOME box was **knocked down and rebuilt**, product
and server put back inside, and the red came back identical. ⛔ Three rounds out of three.

> ⭐⭐⭐ **And it is the thesis of the phase, measured a second time and in the direction nobody expected.**
> §7-bis.7 said *«the second desktop asked for something the first did not ask for»*. ⇒ Here the
> desktop that behaves differently is **the first**, the home one: the three new boxes work, and
> the one on which the product grew up does not. ⛔ Without the other three, this number would have been read
> as *«il suono va così»*.
>
> `[?]` **The cause was not found**, and it is written instead of guessed: the suspicion is that in the
> GNOME session something else touches the tenant's audio graph (`wireplumber` suspending, or
> a second `pipewire` of the session), but ⛔ **it is not measured**, and until it is it stays a `[?]`.

### ⛔⛔ AND A DEFECT IN THE WIRING, which no certification could catch

`[M]` `esegui_maglia` reads an injected mesh **in reverse**: `0` means *«the fault was
seen»*, and what ends up in the log is `ha_visto_il_guasto`, which is what C13 reads. ⛔ **C9 exited with the
raw verdict** ⇒ in the round with the fault it would have written `false` **precisely when the fault had been
seen perfectly well**, and C13 would have started lying.

⭐ **And the cure was not inverting the outcome**: C9 is red **even without a fault** (the two lines of
`tastiera.c`), so a simple *«red ⇒ seen»* would have said «seen» even if the injection had
not bitten — a predicate that cannot fail, §1.44 again, and this time holding up the
certification of the whole net. ⇒ **Two** things are demanded: red verdict **and** more lines without a
name than before. `[M]` 4 without the fault ⇒ 5 490 with the fault. ⇒ `LEZIONI.md` §1.52.

⚠ And a second defect of the same kind, `LEZIONI.md` §1.51: `11-accendi.sh prodotto` failed on
all four boxes with *«Text file busy»* — ⛔ a red that came from the **order of the
commands**, not from the product.

### ⭐⭐ THE LAPTOP HALF OF THE HOOK IS NOW ALIVE — **and it takes 1 second**

§4.6-novemdecies had discovered that the hook has two halves on two machines. ⛔ The one on the laptop
injected **no** fault ⇒ C13 there could **never** have turned green. ⇒ C10 now has
a `--guasto-innestato` that copies the **real** files into a temporary folder, changes **one byte** of them and
demands the red.

`[M]` On the laptop, family `rete`: **C10 green · C12 green · C13 green**, ⭐ in **1 second**,
without switching anything on. (C11 and C14 say *«I could not look»*, and that is right: the boxes are not
there.) The hook was **installed** as `pre-push`.

### ⚠ And the cuts, declared instead of suffered

`[M]` The fast family's cap is at **173 s out of 180** — ⚠ measured again on 26 Aug with
C10 inside and with the new entry of C11: **twenty seconds more than was believed**, and it stays full.
§5.1 says an extra mesh is
**swapped**, not added. ⇒ C5 (38 s), C7 (26 s) and C9 (50 s) sit in `tutto` and in `desktop-nuovo`,
with their injected fault next to them. ⛔ **The only one that enters the fast family is C10**, which costs less than the
stopwatch's resolution. ⭐ And it enters **twice**: also in the `rete` family, because the
twin lives half in `src/` and half in `banchi/rcp/`, and a change **there** triggers `rete` — that is
exactly the change that breaks the twin.

## 7-bis.19 ⭐⭐⭐⭐⭐ **27 AUGUST — the net is complete, and the plug was not there**

`[M]` One day, up to **ten agents together**, and the result in one line: ⭐ **the fifteen
meshes exist, run, and the oldest defect of the project is closed.**

### ⭐⭐⭐ The fact of the day: **the sessions were not being born blind**

The defect of `fasi/10-…` §7.4 — *«dieci sessioni nuove su dieci nascono senza monitor»* — blocked
five tests of the net and postponed phase 12. ⛔ **It did not belong to the product, and it was not even one
single defect.** They were three things, and each one hid the next:

| | what it was | how it was seen |
|---|---|---|
| ⛔⛔ **the test** | **C1 could not say green** — it read `ZERO MONITOR`, which the product writes on the path of a **successful** birth, and its green branch was unreachable | an agent sent to **refute it** ⇒ `LEZIONI.md` §1.53 |
| ⛔ **the box** | §6 of the recipe moved the `polkitd` group off 991 to give it to the card; `groupmod` does not carry the files ⇒ `polkit` died, `gnome-shell` took **4 timeouts of 25 s** | `[M]` from **~97 s** to **1.0 s** after the cure ⇒ §1.54 |
| ⭐⭐⭐ **the real cause** | **the tenant was not in the `video` and `render` groups** | `[M]` **17 sessions out of 17** see with the groups · **0 out of 4** without · ⭐ given the groups to the same tenant ⇒ **2.04 s**. One single variable, outcome overturned |

⭐⭐ **And the table of §7.4 explains itself**: `provanic4/5/6` — those that **never** saw, over
**98 · 55 · 50** attempts — do not have those groups; `prova` and `provanic1`, which always saw,
have them. ⇒ ⛔ **It was not intermittent: they were two populations of tenants.**

⚠ **And the tail touches the past**: the benches created tenants on their own in **thirteen** places, and
⛔ without those groups. ⇒ Every bench that measured there measured **a session that could not see**.
⭐ Twelve cured in **one single file** (`banchi/attrezzi-gruppi-scheda.sh`), and one of them
(`07-b64-terreno.sh`) is used by **twenty-three benches** of phases 9 and 10.

### ⭐⭐ And the monitor: how it is really born, read and measured

`[R]` `--headless` alone **creates no monitor**, and that is intended. In the whole of Mutter **two** places
create one: the `--virtual-monitor` flag at startup, and `RecordVirtual`. ⭐ And the one from
`RecordVirtual` is born **when PipeWire fixes the format**, that is **after a consumer has
hooked on** — `[M]` 65–93 ms later, never before.

⇒ ⭐⭐ **That is why the five «blocked» tests were not blocked**: while a client is attached,
the screen **is there** — which is exactly the condition in which those five work.

⚠ And a debt, written instead of hidden: `[M]` the monitor **dies with the D-Bus connection** of
whoever called `RecordVirtual`, which in the product is the **child**, and the child dies with the client. ⛔ On
paper it contradicts I4. ⭐ But **C6 measures green**: `[M]` same child, same scene (60.5 % ⇒ 60.5 %,
deviation 0.000) — **the windows are found again**. ⇒ It stays a declared debt, not a job for today.

### ⭐ The five meshes that were missing, and the sixth nobody had asked for

| | certification |
|---|---|
| **C2** a window opens — the pixel, not the process count | 51 cases |
| **C3** the frames change — the canary against the frozen image | 56 |
| **C4** the key arrives **all the way to the screen** — and only in the **expected area** | 37 |
| **C6** it detaches and finds itself again — ⭐ it reads the **child's pid**, not the colour | 46 |
| **C8b** the page seen **from the client** — the verdict is a **difference** | 17 |
| ⭐⭐ **C15** the remote half really runs | 21 |

⭐⭐ **C15 was not in the list, and it is the most serious hole that remained**: ⛔ with the test machine switched off
for good, `[M]` **C12 and C13 stay green** and nobody notices that the real meshes no longer run.
⇒ Proved by removing from the log the only line executed on the boxes: **C12 green · C13 green ·
C15 RED** on the same file.

### ⛔⛔ And the meshes were still lying — **ten defects, and two were in all of them**

⭐ Two agents sent to **refute** found what no certification had caught:

| | |
|---|---|
| ⛔⛔ **«AMMESSO» was a predicate that could not say no** | that word is **also in the two refusal messages** ⇒ **nine meshes** believed they had got in even when they were rejected. ⭐ Cured with **one** function for nine, and the proof: with the old check, **7 new cases out of 9** answered wrongly |
| ⛔ **the injected fault read on the colour** | a mesh already red on its own said *«the fault was seen»* even if the injection had not bitten ⇒ §1.52, cured in **C5, C9, C10** |
| ⛔⛔ **C7 said green on a broken I4** | it asked *«did something change?»* instead of *«is the child still there?»* |
| ⛔ **C8 blamed the wire** | a **rejected** client came out as *«no frame arrived from the wire»* |
| ⛔ **the hook** | an outcome `3` made it write `ha_visto_il_guasto: false` — an accusation against a test that did not run |

### ⭐⭐⭐ THE WHOLE ROUND, and the numbers

`[M]` 27 Aug 2026, `--famiglia tutto` on the four boxes, binary `aa950804fed7`:

| | |
|---|---|
| duration | **7 896 s** (2 h 11) |
| outcomes `0` | **57** |
| ⭐ **injected faults seen** | **23 out of 25** |
| outcomes `3` (*«I could not look»*) | **6** |
| ⛔ reds | **3**, and they are **the same red**: C1 on kde/xfce/lxqt |
| ⭐⭐ **bench reds** | **none** |
| **C11** alignment | ⭐ green, 14 entries, same binary in all four |
| **C14** do not disturb each other | ⭐ green, **801 s**, identical fingerprint alone and in parallel |

⛔ **And the three reds are the product, and it is phase 12**: `[R]` `src/sessione.c` · `scrivi_dropin()` — the product can
start **only GNOME**. ⇒ On KDE, XFCE and LXQt the net tests the environment, the sound, the leftovers, the
log and the alignment; ⛔ **not the product**, because there the product does not run.

### ⭐ And five cures in the product, all born from a mesh

| | |
|---|---|
| `src/tastiera.c` · `webtransport.c` | ⭐ **the first red the net drew out of the product**: 4 log lines out of 5 490 did not say whom they were talking about |
| `src/figlio.c` — the audio ring | ⛔ it was not emptied without a stage ⇒ `[M]` **96 489 ms** of overflow |
| `src/figlio.c` — the uninitialised envelope | ⛔ **the «third state» of §7.4 was dirty memory** ⇒ §1.55 |
| `src/mutter.c` | a line said *«monitor virtuale montato»* when the monitor **did not exist yet** |
| `src/provisiona.sh` + `src/figlio.c` | ⭐⭐ the card's groups, read **from the node**, and a check that **says so in the log** instead of giving birth to a session that cannot be seen |

---

# §8 · The questions, and the answers received

*The six questions of the first draft. ⭐ Five were answered by the two reviewers; one remains
for the user.*

| | | outcome |
|---|---|---|
| **Q1** | what class of regression does the design not catch? | ✅ **answered**, and it became **§6** |
| **Q2** | does the container hold the piece that keeps count of who is connected? | ⭐⭐ **CLOSED WITH AN `[M]`, 26 Aug 2026: YES** — 18 greens out of 18, at the price of two declared permissions (§7-bis.1) |
| **Q3** | how does one stay blind to the desktop? | ⭐⭐ **CLOSED WITH AN `[M]`, 26 Aug 2026**: the same eight checks run on **Mutter and on KWin** without one line changed — 18/18 on both (§7-bis.7) |
| **Q4** | one user per box: what is lost? | ⚠ **correctness with several users, which is not capacity** ⇒ ❓ **§4.4, the user decides** |
| **Q5** | how long must the fast family last? | ✅ `[?]` **3 minutes**, provisional, to be measured (§5.1) |
| **Q6** | is the mark the right route? | ✅ *«yes, but not on its own»* ⇒ **§4.3** |

## 8.1 ⚠ And something neither of the two reviewers said, and it must be written

⛔ **Both accepted without discussion the most fragile premise of the design**: that the
container must host **the whole product**. ⇒ Nobody was asked whether a different
cut exists — for example the desktop inside and the server outside.
⚠ The short answer is that **it cannot be done**, because the product switches on the compositor **inside** the
session it governs. ⭐ But it is a `[?]` never put to the test, and it must be left written instead of
taken as closed.

---

# §9 · The closing criteria of the phase

*Proposed by the review, accepted: the phase **is not closed** if one of these is missing.*

*⭐ Updated on **26 Aug 2026**, morning, with what was done during the night.*

| # | | where it stands |
|---|---|---|
| 1 | **step 0** has been run and written, with outcome `[M]` | ✅ **18/18 on four desktops** |
| 2 | **one** GNOME box exists that runs | ✅ ⭐ **four of them exist** |
| 3 | ⭐⭐ **the net turns red on acceptance test A without hints** | ✅ `[M]` 5 blind sessions out of 10 judged |
| 4 | the net catches **acceptance test B**, ⚠ or it is written why it cannot and how it is compensated | ✅ ⭐ **caught**: with the fault injected the **second** tenant does not open the browser, the first does (§7-bis.10) |
| 5 | the visual tests **do not rest on the mark alone** | ✅ colour with **declared tolerance** + histogram + the «before» |
| 6 | the **hook** is defined by path, not by good will | ✅ ⭐ `11-gancio.sh`, and it has already run on the real thing (§7-bis.16) |
| 7 | the **red policy** exists | ✅ §5.2 |
| 8 | the net has **at least one test that checks itself** | ✅ ⭐⭐ **five**: C11 · C12 · C13 · C14 · **C15**, which was not in the list and was the most serious hole (§7-bis.19) |
| 9 | the **time** of the fast family is measured, not estimated | ✅ ⭐ `[M]` **173 s** on a cap of **180**, and the **whole round** `[M]` **7 896 s** (§7-bis.19). ⛔ The fast one is **full**: an extra mesh is **swapped**, not added |
| 10 | ⛔ **what the net does not catch is written** | ✅ §6, ⭐ **including what today it cannot look at and why** |
| 12 | ⭐⭐⭐ **and the list is finished**: eleven product tests and five of the net, **all written, all certified, all run** | ✅ `[M]` 27 Aug: **57 outcomes `0`**, **23 injected faults seen out of 25**, ⛔ **no bench red** (§7-bis.19) |
| 11 | ⭐⭐ and the user's criterion, which stands above all: **the net caught something the eye would not have caught**. If not, **the phase has failed and it must be said** | ✅ ⭐⭐⭐⭐ **yes, and the count is another one now**: ⭐ **the oldest defect of the project**, closed on 27 Aug — the `video` and `render` groups (§7-bis.19) · **five cures in the product**, each born from a mesh · ⛔ **ten defects in the meshes themselves**, two of which were in **nine meshes out of nine** · and before that: **yes, and five times**: the session that is born blind · the second tenant who does not open the browser · ⛔ **three BENCH reds** that would have passed for product defects (§7-bis.11) · ⭐ **the four log lines without a tenant** · ⭐⭐ **the sound that on GNOME arrives at a fortieth** — and this last one **no eye would have seen**, because the sound was there and it was loud (§7-bis.18) |

---

# §10 · What stays `[?]` at the opening

| | |
|---|---|
| ~~`[?]`~~ ⭐ **`[M]`** | ~~whether the container holds the piece of the system that keeps count of who is connected~~ ⇒ **step 0 run on 26 Aug 2026: it holds, 18 out of 18** (§7-bis.1) |
| ~~`[?]`~~ ⭐ **`[M]`** | ~~how long the fast family really lasts~~ ⇒ **153 s out of 180**. ⛔ And the cap is **full**: any extra mesh must be **swapped**, not added |
| ~~❓~~ ⭐ **closed** | ~~how C8 is run~~ ⇒ **in a box, with two tenants** (the user's answer, §4.4), and ⭐ **the acceptance test has passed** (§7-bis.10) |
| ~~`[?]`~~ ⭐ **`[M]`** | ~~whether the four boxes really do not disturb each other~~ ⇒ **measured**: same outcome alone and in parallel, four out of four (§7-bis.15). ⚠ **Left out** is the real contention on the graphics card, which needs live sessions |
| `[?]` | whether a different cut between container and product exists (§8.1) |
| ~~❓ the user decides~~ ✅ **decided** | the **hook's log** goes into git — decided by the user on 27 Aug 2026. ⭐ With `merge=union` in `.gitattributes`: the notebook is made of lines that are **added**, and two machines writing on different days are not a conflict to resolve by hand. ⚠ The price, declared: the file shows as modified at every round |
| ⛔ **OPEN, and it is phase 12** | ⭐ `[M]` **the product can start only GNOME** (`src/sessione.c` · `scrivi_dropin()`) ⇒ C1 gives red on kde/xfce/lxqt, and it is **the only red** the whole round produces. ⚠ And something phase 12 will find: ⛔ **KWin cannot be born blind** — with `--output-count 0` it makes an output all the same, so the «zero own monitors» design **does not carry over the same** |
| ⚠ **declared debt** | the **stage dies with the child's D-Bus connection** ⇒ on paper it contradicts I4. ⭐ But `[M]` C6 measures **green**: the windows are found again. ⇒ Written, not cured — the cure is architectural (`DECISIONI.md` §4.6-teretvicies) |
| ~~⛔ open~~ ⭐ **closed** | ~~why the box does not switch itself off~~ ⇒ **it was the SIGNAL, not a hung unit**: `[M]` SIGTERM (the default of `podman stop`) leaves the box standing **30 s out of 30** — `systemd` as the first process ignores it; `SIGRTMIN+3` switches it off in **3.1 s**. ⇒ The «four minutes» were an expired cap, not a wait. The cure (`STOPSIGNAL` in the recipes) is in force, and ⛔ the hypothesis *«a live session keeps it up»* is **refuted**: with a session inside the shutdown is the clean one (§7-bis.18) |
| ~~⛔⛔ OPEN~~ ⭐ **closed** | ~~C5 is red on GNOME~~ ⇒ **it was the same root as the blind session**: without a stage the product did not empty the audio ring (`[M]` **96 489 ms** of overflow). Cured in `src/figlio.c`; `[M]` C5 green on all four boxes. *(old entry: `[M]` C5 red on GNOME and green on the other three*: **34–41** sound blocks arrive at the client in 25 s instead of **~4 878**, and what arrives is loud and right. ⛔ It is not the aged box (rebuilt from zero, same red) and it is not the threshold. `[?]` The cause is not measured (§7-bis.18) |
| ~~⛔ OPEN~~ ✅ **cured** | ~~4 log lines out of 5 490 do not say whom they are talking about~~ ⇒ cured on 27 Aug in `src/tastiera.c`, `tastiera.h`, `webtransport.c` — ⚠ **eight lines, not two**: the two measured plus six twins in the same function. `[M]` C9 green on all four |
| ❓ **the user decides** | does the **hook's log** go into git or not? In git it gives C13 one single memory for all machines; outside it avoids having that file modified at every round. ⚠ And today there is **only one, on the test machine** (`DECISIONI.md` §4.6-novemdecies) |
| ~~⛔ open~~ ⭐ **closed** | ~~why half of C1's rounds do not judge~~ ⇒ **it was the clearing**: one waits for the event and not for the clock, and `[M]` the next round gives **10 judgements out of 10** (§7-bis.13) |
| ~~⛔⛔ blocks~~ ⭐⭐⭐ **CLOSED on 27 Aug** | **it was the tenant's `video` and `render` groups**: `[M]` 17 sessions out of 17 see with the groups, **0 out of 4** without, and the counter-test overturns the outcome with one single variable (§7-bis.19). ⛔ And it did not belong to the product: it belonged to the **provisioning**, plus a mesh that could not say green and a box that broke by itself. *(old entry: `[M]` ten new GNOME sessions out of ten are born blind* ⇒ C2, C3, C4, C6 and half B of C8 **cannot be measured**. It is the OPEN defect of phase 10 §7.4 — ⛔ it is plugged by curing the **product**, not by writing another mesh |
| `[?]` | how much an extra frame each costs in capacity — ⚠ **outside this phase**, it is in `MASTERPLAN.md` M1 |

---

# §11 · ✅ **THE QUESTION HAS LAPSED** — *and the reason is worth more than the answer*

This section asked: **«si va avanti con KDE avendo metà della rete che non può guardare, oppure
prima si cura la sessione che nasce cieca?»**

⇒ ⭐⭐ **The question no longer exists, because the premise was false.** `[M]` 27 Aug 2026: the sessions
**were not being born blind**. They were three overlapping things — a **mesh** that could not say green, a
**box** that broke by itself, and the real cause: ⭐ **the tenant was not in the `video` and
`render` groups** (§7-bis.19).

⇒ The five tests declared «blocked» **were not blocked**, and today they all run.

> ### ⛔⛔ And the lesson is bigger than the phase
>
> For weeks a number — *«dieci sessioni su dieci»* — governed the order of the work, the
> postponement of a phase, and a list of «impossible» things. ⛔ **That number came from one single test, and
> that test could not produce any other result.**
>
> ⭐ It took ten minutes for an agent whose mandate was **«prova a smentirla»**. ⇒ The rule
> that comes out of it, and it holds beyond this phase: **when a red has held for days and nobody manages to make it
> turn green again, the first question is not *«why is the product broken»* but *«can this test say
> green?»***. ⇒ `LEZIONI.md` §1.53.

## ⭐ What remains for the user, now

| | |
|---|---|
| ✅ **the hook's notebook in git** | **decided on 27 Aug**: yes, with `merge=union`. ⚠ The price is a file that shows as modified at every round |
| ⭐ **phase 12 is the next step, and it is no longer blocked** | ⛔ But what it will find is already measured: the product **can start only GNOME** (`src/sessione.c` · `scrivi_dropin()`), and it is **the only red** the whole round produces. ⚠ And KWin **cannot be born blind**: the «zero own monitors» design does not carry over the same |
| ⚠ **a debt, not a job** | the stage dies with the child's D-Bus connection ⇒ on paper it contradicts I4, ⭐ but C6 measures **green**: the windows are found again. Curing it is architectural, and ⇒ `DECISIONI.md` §4.6-teretvicies |

---

# §12 · The user's judgement

*(to be filled in at closing)*
