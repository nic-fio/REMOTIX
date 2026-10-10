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

# §7-bis · ⭐⭐⭐⭐⭐ CHE COSA È STATO FATTO — *la notte del 25-26 agosto 2026*

> ## ⭐ IN UNA RIGA, PER CHI LEGGE SOLO QUESTA
>
> | il piano di §7 | dove siamo |
> |---|---|
> | **0** il passo 0 | ✅ `[M]` **18/18**, e non su una scatola: **su tutte e quattro** |
> | **1** la lista e le decisioni aperte | ✅ la lista c'è; ⭐ l'ultima domanda aperta (C8) l'ha chiusa l'utente |
> | **2** una scatola | ✅ ⭐ **quattro** — GNOME, Plasma, XFCE, LXQt |
> | **3** ⭐⭐ il **collaudo A** | ✅ **rossa da sola**, `[M]` 10 sessioni cieche su 10 |
> | **3-bis** il rosso sbagliato | ✅ nella certificazione di C8: colore spostato ⇒ **resta verde** |
> | **4** ⭐⭐ il **collaudo B** | ✅ **preso**: col guasto innestato il **secondo** inquilino non apre il browser, il primo sì |
> | **5** le altre tre scatole | ✅ fatte, e ⭐ **senza riscrivere una riga della lista** |
> | **6** le prove della rete | ✅ ⭐ **tutte e quattro**: C11 verde · C12 e C13 girano · C14 verde e misurata |
> | **7** il gancio | ✅ ⭐ **c'è, e ha già girato davvero**: `[M]` **153 s** su un tetto di 180 |
>
> ⛔ **E la cosa che pesa di più non è nessuna di queste**: `[M]` **dieci sessioni GNOME nuove su
> dieci nascono senza monitor** ⇒ metà della rete — tutte le maglie che vogliono guardare un pixel
> **attraverso il prodotto** — non ha niente da guardare. ⚠ Non è un buco della rete: è il difetto
> **aperto** della fase 10 §7.4. ⇒ §7-bis.13, e la domanda all'utente in §11.

> ## ⭐⭐⭐⭐⭐ IL COLLAUDO A È PASSATO — **la rete è diventata rossa da sola**
>
> `[M]` **25 agosto 2026, 22:42 UTC**, il primo giro in assoluto. Puntata contro il codice del 25
> agosto, dentro una scatola, su **sei utenti nuovi**, la maglia C1 ha detto:
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
> ⚠ *Questo è il **primo** giro. Il 26 agosto, con dieci utenti e il banco curato, il numero è
> diventato **10 cieche su 10 e zero non giudicate** — ⇒ §7-bis.13.*
>
> ⛔ **Nessuno le aveva detto dove guardare.** Apre una sessione nuova, legge quel che il prodotto
> dice di sé, e giudica. ⇒ **La riga che l'ha fatta scattare**, presa dal registro del server:
>
> ```
> 22:42:15.826 sessione [c1u1] ⛔ ZERO MONITOR, e la sessione e' viva: e' la sessione
>                                «viva, completa e NERA» di STUDI.md §gnome §3.1
> 22:39:18.145 figlio  ⛔ il palco di «c1u1»: monitor «» (0 prima, 2 dopo), 0x0 stride 0 a 0 bit
> ```
>
> ⭐ E il **terzo stato** di `fasi/10…` §7.4 — *«una volta per utente ne nascono due, senza nome»* —
> ⭐ **si è riprodotto identico**: `monitor «» (0 prima, **2** dopo)`.
>
> ⇒ ⛔ **Il guasto del 25 agosto vive dentro la scatola.** Che è la seconda notizia, e non è minore:
> vuol dire che la scatola **non lo nasconde**, cioè che è il posto giusto dove tendere la rete.

## 7-bis.1 ⭐ IL PASSO 0 È PASSATO — `[M]` **18 verdi, 0 rossi, 0 «non lo so»**

*La `[?]` più pesante del documento è diventata un `[M]`.*

| # | | esito |
|---|---|---|
| 0 | il primo processo è `systemd`, il sistema parte | ⭐ **sì** (con una sola unità fallita, `polkit`, dichiarata) |
| 1 | `logind` conosce l'utente, sessione aperta | ⭐ **sì** |
| 2 | il **linger** si accende e il gestore d'utente vive senza login | ⭐ **sì** |
| 3 | un'unità d'utente si avvia da dentro la sessione | ⭐ **sì** |
| 4 | chiusa la sessione, ⛔ **i figli muoiono davvero** | ⭐ **sì** |
| 5 | la cartella privata c'è, è sua, ed è **di questa scatola** (tmpfs) | ⭐ **sì** |
| 6 | il canale di messaggi della sessione c'è e risponde | ⭐ **sì** |
| 7 | il compositore vive, **annuncia un'uscita**, e un cliente vero disegna | ⭐ **sì** |
| 8 | ⭐⭐ **la scheda grafica e il codificatore in hardware** | ⭐ **sì**: `iHD 25.2.3`, **3 profili H.264 di codifica** |

> ### ⛔⛔ E IL PREZZO, MISURATO PERMESSO PER PERMESSO — *non uno per abitudine*
>
> ⛔ **Non è stato usato `--privileged`.** Un permesso generico avrebbe fatto passare tutto e non
> avrebbe insegnato niente. ⇒ Quel che il prodotto chiede **davvero**:
>
> | permesso | ⛔ che cosa si rompe senza |
> |---|---|
> | `--device /dev/dri` | ⭐ **la scheda vera.** È la ragione di D1 |
> | ⛔ **`--cap-add=AUDIT_CONTROL`** | `[M]` `pam_loginuid.so`, che in Debian è **`required`**, fallisce con *«Cannot make/remove an entry for the specified session»* ⇒ ⛔ **il gestore d'utente non parte affatto**: niente sessione, niente canale, niente desktop |
> | `--cap-add=AUDIT_WRITE` | accompagna il precedente nella stessa catena |
> | ⚠ `--network=host` | ⛔ **non è una scelta**: `netavark` su questa macchina non applica le regole (*«nft did not return successfully»*). ⇒ **Prezzo dichiarato**: quattro scatole insieme condividono le porte dell'ospite, quindi ognuna ha la sua (8511-8514) — e resta da rivedere a **C14** |
>
> ⭐ **E la strada scartata**: togliere `pam_loginuid` dalla catena PAM avrebbe fatto passare tutto
> senza permessi in più — ⛔ **e avrebbe provato una catena PAM diversa da quella consegnata**, cioè
> esattamente il simulacro che §3.5 esiste per impedire.

## 7-bis.2 ⛔⛔ IL GUASTO CHE NESSUNO DEI DUE REVISORI AVEVA PREVISTO — **il gruppo della scheda**

`[M]` Al primo giro il nodo `/dev/dri/renderD128` è entrato nella scatola col **numero** di gruppo
dell'ospite (991), ⛔ **ma dentro Debian quel numero appartiene a un altro gruppo** (`polkitd`).
⇒ L'inquilino è rimasto fuori, e il compositore ha ripiegato:

```
libEGL warning: failed to open /dev/dri/renderD128: Permission denied
libmutter-Message: Created surfaceless renderer without GPU
```

> ⛔⛔ **Una scatola che misura la codifica in SOFTWARE credendo di misurare l'hardware** — e
> **nessun rosso da nessuna parte**: solo numeri peggiori, che qualcuno avrebbe attribuito al
> desktop. ⭐ È la forma di *«silenzio invece di rosso»* applicata a un ambiente invece che a un
> banco.

⭐ **La cura, e non è inchiodare 991**: un'unità dentro la scatola **legge il numero dal nodo**
all'avvio e vi allinea il gruppo `render`, **dichiarandolo**. ⇒ Inchiodare il numero avrebbe fatto
una scatola che funziona su questa macchina e **tace** su un'altra.

## 7-bis.3 ⛔ E DUE VOLTE IL DIFETTO ERA NEL BANCO, non nella scatola

*`REVIEWER.md` §1: il banco è il primo imputato. Confermato due volte in una notte.*

| | ⛔ che cosa faceva | la cura |
|---|---|---|
| **il punto 4 buttava giù il campo agli altri** | chiude la sessione per vedere se i figli muoiono ⇒ si porta via `/run/user/…` ⇒ **i punti 5, 6 e 7 davano TRE ROSSI FALSI** | chi prova la chiusura ha il dovere di **riaprire e verificare** prima di lasciar giudicare gli altri |
| **il punto 1 giudicava prima di aver chiesto** | leggeva mentre il gestore d'utente era ancora `activating` ⇒ *«la scatola non regge»* quando la verità era *«non avevo ancora chiesto niente»* | si **prepara** come fa il prodotto, si aspetta l'evento, **poi** si giudica |

> ⭐⭐ **E la lezione nuova è il rovescio di quella nota.** `LEZIONI.md` §1.29 dice *«silenzio invece
> di rosso»*. ⛔ Qui è stato **rosso invece di niente** — e costa uguale: *una rete che dà rossi a
> vuoto viene spenta da chi lavora*, e allora non c'è più nessuna rete.

## 7-bis.4 ⛔⛔ IL BINARIO ERA GIUSTO E LE LIBRERIE NO — **e il sintomo era dalla parte sbagliata**

`[M]` Il prodotto è stato messo nella scatola con le librerie prese da `/lib` dell'ospite:
`libngtcp2.so.16` **versione 16.2.9**. ⛔ Ma il server vero gira con quella costruita in
`src/b2/ngtcp2/build/lib`, **16.11.0**. ⇒ **Stesso nome, stesso `so.16`, cosa diversa.**

| | |
|---|---|
| il server | è **partito**, ha detto tutte le sue righe d'avvio, ha generato i certificati, si è messo in ascolto |
| ⛔ al **primo cliente** | è morto con `ngtcp2_settingslen_version: Unreachable` |
| ⛔⛔ e il cliente | ha visto soltanto **«Idle timeout»** |

> ⭐⭐ **È il guasto che l'utente aveva nominato per primo** — *«se sul container GNOME abbiamo
> remotix v1 e sul container KDE remotix v1.2 andiamo a sbattere»* (D5) — ⛔ **arrivato però da una
> porta che nessuno guardava**: non due versioni del prodotto, **due versioni di una libreria con lo
> stesso nome.** ⇒ R1 va letta così: *un solo binario **e le sue librerie**, presi dove li prende il
> server vero.*

⚠ **E la stessa famiglia, due volte ancora**: `libei1` e `python3-aioquic` funzionavano perché
qualcun altro se li tirava dietro. ⇒ Adesso le librerie che il prodotto chiede sono **dichiarate
nella ricetta**, riga per riga, invece di essere ereditate per caso.

## 7-bis.5 ⭐ IL PRODOTTO GIRA DENTRO LA SCATOLA — e la prova è un cliente vero

`[M]` 26 agosto 2026: il cliente di prova si è attaccato al server **dentro la scatola**, ed è stato
**AMMESSO in 1004 ms**, con `SESSIONE: stato=1 tela=1920x1080`, restando attaccato 30 s senza che
cadesse niente. ⇒ ⭐ Il guardiano di `logind` si è collegato al bus di sistema **dentro il
contenitore**, che era la `[?]` di Q2.

⚠ **E una sessione, quella volta, è nata col monitor**: `monitor 1/1: connettore «Meta-0» …
1920x1080@60`. ⛔ **Non è una smentita del rosso di sopra: è l'intermittenza**, la stessa che sul
ferro dava a `provanic3` **2 riusciti e 6 falliti**.

## 7-bis.6 ⛔ E DUE COSE CHE RESTANO APERTE, scritte invece che dimenticate

| | |
|---|---|
| ⛔ **la scatola non si spegne da sola** | `[M]` un `podman rm -f` normale è rimasto appeso **oltre quattro minuti** aspettando uno spegnimento ordinato che non arrivava, bloccando anche i comandi successivi. Per ora si ammazza (`-t 0`). ⚠ **Non tocca il passo 0** (la scatola è usa-e-getta) ⛔ **ma tocca C7** — *«si chiude tutto e non resta niente»* — e lì quella domanda diventa il bersaglio |
| ⚠ **tre giri su sei non hanno giudicato** | il palco impiega ~13 s a nascere e a volte non nasce affatto; l'attesa dichiarata è 45 s. ⇒ Restano **«non lo so»**, ⛔ **e non diventano verdi** |

## 7-bis.7 ⭐⭐⭐⭐ LA SECONDA SCATOLA — **e le stesse prove girano su PLASMA senza una riga cambiata**

`[M]` **26 agosto 2026, 04:05 UTC.** Costruita una seconda scatola con **KWin** al posto di Mutter,
e le **stesse identiche otto verifiche** hanno detto:

> ### ⭐ `regge: 18 · non regge: 0 · non ho potuto guardare: 0`

⛔ **Non è stata riscritta una riga della lista.** Ogni scatola porta allo stesso percorso un
**adattatore** — un file corto che risponde a tre domande: *come ti chiami · da che pacchetto vieni ·
come ti accendo*. ⇒ È la forma su cui **tutt'e due i revisori** avevano risposto la stessa cosa (Q3,
§3.7), e ⭐ **adesso è misurata invece che creduta**.

### ⛔⛔ E il secondo desktop ha chiesto subito una cosa che il primo non chiedeva — **due volte**

| | ⛔ che cosa è successo | ⭐ che cosa insegna |
|---|---|---|
| **il gruppo della scheda non esisteva** | nella scatola di GNOME `render` c'era già: lo portava un pacchetto che `gnome-shell` si tira dietro. ⛔ In quella di Plasma **non esiste**, e la ricetta è morta con `usermod: group 'render' does not exist` | il primo desktop non era «giusto»: era **generoso**, e nascondeva una dipendenza che nessuno aveva dichiarato |
| ⛔⛔ **KWin non partiva affatto** | `env: 'kwin_wayland': Operation not permitted`. ⇒ `/usr/bin/kwin_wayland` porta addosso `cap_sys_nice=ep`, e **un programma con un permesso scritto sul file non si avvia** se quel permesso non è nell'insieme della scatola | ⭐ un desktop nuovo può chiedere **permessi** che il primo non chiedeva — e il sintomo non somiglia per niente alla causa |

⭐ **La cura è per desktop e dichiarata**: `SYS_NICE` va **solo** alla scatola di Plasma. ⛔ Darlo a
tutte vorrebbe dire provare GNOME in un ambiente diverso da quello in cui gira davvero — cioè
allontanare la scatola dal prodotto per comodità nostra.

> ### ⭐⭐⭐ E QUESTA È LA TESI DELLA FASE, CAPITATA AL PRIMO TENTATIVO
>
> Due cose che il secondo desktop ha fatto emergere **in dieci minuti**, e che dentro la fase 12 —
> in mezzo al codice nuovo, con Plasma da far funzionare — sarebbero costate mezza giornata **e una
> diagnosi sbagliata**: sarebbero sembrate difetti del nostro codice KDE.
>
> ⇒ ⛔ **È esattamente la ragione per cui l'utente ha messo questa fase PRIMA dei desktop nuovi.**

⚠ **E quel che questa scatola NON fa, oggi**: il prodotto non sa ancora accendere KDE (è la fase 12),
quindi lì dentro girano **solo** le verifiche dell'ambiente. Le maglie della rete che vogliono il
prodotto — C1 e le altre — girano per ora **solo su GNOME**.

## 7-bis.9 ⭐⭐⭐⭐⭐ LA TERZA E LA QUARTA SCATOLA — **e le quattro sono in piedi**

`[M]` **26 agosto 2026, 03:5x UTC.** Costruite le scatole di **XFCE** e **LXQt**, e la stessa
identica lista di otto verifiche — ⛔ **non una riga cambiata, ancora** — ha detto:

> ### ⭐ XFCE `regge: 18 · non regge: 0 · non ho potuto guardare: 0`
> ### ⭐ LXQt `regge: 18 · non regge: 0 · non ho potuto guardare: 0`

⇒ ⭐⭐ **Quattro scatole, quattro desktop, un solo elenco di prove.** La cecità al desktop di §3.7
non è più una proposta: è `[M]` su quattro compositori, e il costo per aggiungerne uno è **un
adattatore da quaranta righe**.

### ⛔ E una cosa scomoda, detta prima che qualcuno la scopra contando male

**Le scatole sono quattro; i compositori sono TRE.** XFCE e LXQt non portano un compositore proprio
su Wayland: portano una **sessione** e si appoggiano a uno di famiglia `wlroots` — e la scelta, per
tutt'e due, è **labwc**. ⛔ Non è una comodità di questa fase: `DECISIONI.md` ha già misurato il
ridimensionamento sotto l'etichetta **«labwc (XFCE, LXQt)»** (`[M]` 5,1 ms, 0 fotogrammi persi su
25), e `PIANO.md` fase 13 lo dice in una riga — *«il terzo e il quarto desktop, che condividono
wlroots e quindi quasi tutto»*.

⇒ ⚠ **Che cosa mette alla prova davvero la quarta scatola**: una quarta **sessione**, una quarta
**ricetta**, dipendenze diverse, e un demone d'inattività che `DECISIONI.md` dà già per **diverso**
da quello di XFCE. ⛔ **Non** un quarto compositore. Chi legge i risultati conti così.

### ⭐ E il terzo desktop non ha chiesto niente di nuovo — *ed è un risultato, non un non-evento*

⛔ Il secondo desktop aveva chiesto **due** cose che il primo non chiedeva (§7-bis.7). Il terzo e il
quarto: **zero**. `labwc` non porta permessi scritti sul file, non pretende gruppi che non ci sono,
e nasce senza schermo con `WLR_BACKENDS=headless` — la terza parola diversa per la stessa cosa, dopo
`--headless` di Mutter e `--virtual` di KWin, ⭐ **e sta tutta nell'adattatore.**

⚠ E va letto per quel che è: **non** *«allora le scatole nuove sono gratis»*. È **un** desktop che
non ha chiesto niente dopo **uno** che aveva chiesto due cose — cioè la ragione per cui la domanda
si fa a ciascuno invece di generalizzare dal primo.

## 7-bis.10 ⭐⭐⭐⭐⭐ IL COLLAUDO B È PASSATO — *C8 prende il difetto, e lo prende dal SECONDO*

⛔ Era la domanda aperta della fase (§4.4), chiusa dall'utente il 26 agosto: **C8 sta in una scatola,
con due inquilini.** ⇒ È scritta, è certificata, ⭐ **e ha preso il guasto.**

> ### `[M]` 26 agosto 2026 — le due righe che valgono la fase
>
> **con la cura della provvista:**
> `c8u1 ⭐ la pagina copre il 98,7 % · c8u2 ⭐ la pagina copre il 98,7 %`
>
> **senza la cura** (il guasto innestato, cioè il codice del 25 agosto):
> `c8u1 ⭐ la pagina copre il 98,7 %` · ⛔ `c8u2 NO — profilo: è di «c8u1» · sa scrivere in ~/.cache/mozilla: NO`

⭐⭐ **E l'asimmetria è quella giusta**: il **primo** apre il browser, il **secondo** no. ⛔ Un rosso su
tutt'e due non sarebbe stato il difetto di §4.6-undecies — sarebbe stato il banco — e ⭐ **adesso è
C8 stessa a dirlo**, invece di lasciarlo dedurre a chi legge (§7-bis.12).

### ⛔⛔ E C8 SI È DOVUTA SPEZZARE IN DUE — *la ragione va letta prima dei numeri*

| | che cosa guarda | oggi |
|---|---|---|
| ⭐ **A · il browser rende la pagina** | Firefox si fotografa da sé, da utente, sulla macchina com'è configurata. ⛔ Il giudizio resta **nel pixel** | ✅ **si misura**, ed è quel che ha preso il guasto |
| **B · e la pagina si vede DAL CLIENTE** | la stessa pagina, guardata **attraverso il prodotto** | ⚠ **oggi non si misura** |

⛔⛔ **Perché B non si misura**: `[M]` 26 agosto 2026, dentro la scatola **nessuna sessione GNOME nuova
nasce con un monitor** — è il difetto **APERTO** della fase 10 §7.4, *«la sessione che nasce cieca»*,
che sta **a monte** di C8. ⇒ ⭐ **Un desktop nero non testimonia sul browser**: chiamare quello «rosso
di C8» vorrebbe dire dare la colpa al browser di una cosa successa **prima che il browser esistesse**.
⚠ Quindi B dice *«non ho potuto guardare»* e **nomina il perché**, e non diventa mai un verde.

⭐ **E la spaccatura ha un guadagno che non era previsto**: la prova A **non passa dal prodotto**, e
quindi gira in **qualunque** scatola — anche in una dove il prodotto non c'è nemmeno. ⛔ Il collaudo
qui sopra è girato dentro la scatola di **PLASMA**.

### ⭐ Le scelte del banco che contano

| | |
|---|---|
| ⭐ **il terreno se lo prepara lei** | mette `/etc/skel/.cache -> /tmp`, cioè **riproduce la configurazione della macchina vera** — che è una **scelta del proprietario**, non un guasto. ⛔ Provare su uno scheletro pulito risponderebbe a una domanda più facile di quella vera |
| ⭐ **gli inquilini nascono come li fa il prodotto** | `useradd -m`, che copia lo scheletro. ⛔ Una via più pulita qui proverebbe un prodotto diverso da quello consegnato |
| ⭐⭐ **il bersaglio nei pixel è un COLORE** | la pagina è `#FF00FF` a schermo intero, e si misura **quanta parte dell'immagine è diventata di quel colore** — tolleranza **±48 per canale**, almeno il **25 %**. ⛔ Nessun desktop mette quel colore da solo: il metro non ha bisogno di sapere che aspetto abbia GNOME |
| ⛔ **il motivo accanto al sintomo** | «non ha disegnato» da solo nasconde tre guasti: il browser morto, il profilo mai nato, la pagina non a schermo. Li distingue e li stampa — ⭐ ed è così che si legge *«profilo: è di «c8u1»»* |
| ⛔ **e non guarda il collegamento** | guardare la causa che crediamo di conoscere invece dell'effetto che ci interessa vorrebbe dire una prova che tace il giorno che la cura cambia |

### ⭐ La certificazione del giudice — `[M]` **8 casi su 8**

| il caso | perché c'è |
|---|---|
| pagina intera · desktop senza browser · schermo nero | il minimo: vede quando c'è, non vede quando non c'è |
| ⭐ **colore spostato di (−30, +30, −30) ⇒ deve restare VERDE** | i compositori applicano profili di colore e la catena passa per un H.264 **4:2:0**, che sottocampiona proprio il croma. ⛔ Una prova che pretende il colore esatto è già morta (§4.3, rilievo di Gemini) |
| colore spostato **troppo** ⇒ deve restare ROSSO | o la tolleranza non separa più niente |
| una macchia piccola non è una pagina | una finestra che si apre e non disegna |
| ⛔ **il file che non c'è e il file vuoto ⇒ «non lo so», non zero** | *«non ho guardato»* e *«ho guardato e non c'era»* sono due cose diverse |

⚠ **E la certificazione si dichiara per quel che copre**: il **lettore dei pixel**. ⛔ Non copre che il
browser sia davvero partito — quello lo dice `--senza-cura` sul vero, ed è il collaudo qui sopra.

## 7-bis.11 ⛔⛔⛔ **QUATTRO VOLTE IL DIFETTO ERA NEL BANCO** — *e le quattro lezioni*

⚠ **Va scritto, e va scritto per intero**: prima di prendere il guasto vero, il banco ha sbagliato
**quattro volte** — tre rossi falsi e ⛔ **un verde falso**. ⭐ Ognuno è una forma d'errore che questa
fase esiste per non ripetere, e tutti e quattro sono finiti in `LEZIONI.md`.

| | ⛔ che cosa succedeva | ⭐ la lezione |
|---|---|---|
| **il predicato che non poteva fallire** | *«prova a scrivere in `~/.cache`»* — ⛔ ma col collegamento `~/.cache` **è `/tmp`**, scrivibile da chiunque (`1777`). ⇒ Diceva **sì** anche all'inquilino che il browser non apriva | `LEZIONI.md` §1.44 — **applicare E1 non basta: bisogna applicarlo NEL POSTO CHE MORDE** (`~/.cache/mozilla`), o il predicato ⛔ ha lo stesso aspetto di uno che passa |
| **il tetto prestato** | il primo avvio di Firefox in una scatola fredda passa i 25 s, e il banco gli dava il tetto pensato per un'altra attesa ⇒ ⛔ **rosso a tutt'e due, con la cura e senza** | `LEZIONI.md` §1.45 — ⛔ e il danno vero non è il rosso falso: è che **il collaudo smette di valere**, perché non distingue più il guasto dal banco |
| **il banco che si dava rosso da solo** | la cartella di lavoro è di `root` a modo `0755`, e Firefox gira **da utente** ⇒ non poteva scriverci l'immagine, e il banco leggeva *«il browser non ha disegnato»* | ⭐ la cura: **scatta in casa sua**, e a portare fuori l'immagine ci pensa `root` dopo |
| ⛔⛔ **e un QUARTO, che è peggio di un rosso** | un comando annidato tre volte (`ssh` → `systemd-run` → `podman exec sh -c`) ha perso le virgolette, **non ha eseguito niente** e ha restituito **`0`** | `LEZIONI.md` §1.46 — ⛔ **un verde senza nessuna misura sotto**, identico a un giro riuscito. ⇒ Niente gusci in mezzo, e **un banco che non stampa niente non è «riuscito»** |

> ### ⭐⭐ E la cosa che le tiene insieme
>
> I primi tre davano **rosso**, ed erano **del banco**. ⛔ In una fase che costruisce una rete di
> sicurezza questo è il pericolo numero uno di §1.3: *«una rete che dà rosso a vuoto viene spenta da
> chi lavora»*. ⇒ ⭐ **Il guasto innestato li ha presi tutti e tre**, e in dieci minuti: senza
> `--senza-cura` sarebbero passati per «il difetto c'è, guarda che rosso».
>
> ⛔⛔ **Il quarto no**, e per questo sta a parte: un **verde** non lo prende nessun guasto innestato,
> perché il guasto innestato serve a controllare che si sappia dare rosso. ⇒ ⭐ Contro quello serve
> l'altra regola: **pretendere di vedere le righe**. Un banco muto non è un banco contento.

## 7-bis.12 ⛔ E UNA GUARDIA NUOVA, NATA DA QUEI ROSSI: **«ha fallito anche il PRIMO»**

Il guasto di §4.6-undecies morde **dal secondo inquilino in poi**. ⇒ ⭐ Se col guasto innestato dà
rosso **anche il primo**, quel che si sta misurando **non è quel guasto**.

⛔ C8 adesso lo dice da sé, e in quel caso **esce 1 invece di 0** — cioè *«il collaudo non vale»*, e
non *«il collaudo è riuscito»*. ⚠ È il rovescio esatto della trappola: una maglia che festeggia un
rosso senza guardare **di chi** è.

## 7-bis.13 ⛔⛔⛔ **DIECI SESSIONI NUOVE, ZERO CON UN MONITOR** — *e il banco che adesso giudica tutte e dieci*

`[M]` 26 agosto 2026, C1 dentro la scatola di GNOME, **dieci** inquilini nuovi, attesa del palco
alzata a **90 s**. Due giri, e il secondo dopo una cura al banco:

| | esito |
|---|---|
| primo giro | `nate con un monitor: 0 · ⛔ CIECHE: 5 · **non giudicate: 5**` |
| ⭐ secondo giro, col banco curato | `nate con un monitor: 0 · ⛔ **CIECHE: 10** · non giudicate: **0**` |

⭐ **Il rosso è quello atteso**, ed è il collaudo A che regge: la maglia punta il codice del 25 agosto
e diventa rossa sul difetto della fase 10 §7.4. ⛔ **E il numero è peggiore di quel che il documento
di fase lasciava sperare**: non «intermittente», ma **dieci su dieci**. ⚠ È coerente con la misura sul
ferro (`provanic4/5/6`: **mai**, su 98 · 55 · 50 tentativi) — ⇒ per un utente **nuovo** il guasto non
è raro: **è la regola**.

> ⛔⛔ **E questo è il fatto che blocca metà di C8** (§7-bis.10, prova B), e non solo: blocca **tutte**
> le maglie che vogliono guardare un pixel attraverso il prodotto — C2, C3, C4, C6.
> ⇒ ⚠ **E il fatto, senza consiglio**: cominciare la fase 12 con questo aperto vorrebbe dire far
> funzionare KDE **senza avere modo di vedere se GNOME continua a funzionare**. ⭐ La scelta è
> dell'utente, e sta in §11.

### ⭐⭐ La cura del banco: **i cinque «non lo so» si alternavano, ed era lo sgombero**

⛔ Il primo giro aveva dato `? NO ? NO ? NO ? NO ? NO` — **uno sì e uno no, dieci giri di fila**. ⚠ Una
alternanza perfetta non è un caso: è **uno stato che sopravvive al giro**.

⇒ ⭐ **Era lo sgombero**: `loginctl terminate-user` più `pkill` tornano **subito**, e il giro dopo
partiva mentre il precedente stava ancora morendo — il compositore nuovo non riusciva nemmeno a
nascere, e il registro non diceva né «monitor» né «cieca». Il giro ancora dopo trovava il campo
libero e giudicava.

⛔ **La cura è la stessa regola di sempre: si aspetta l'EVENTO, non l'orologio.** Adesso C1 aspetta
che l'inquilino del giro precedente non abbia **né sessione né processi**, e se entro il tempo
dichiarato non se n'è andato **lo dice**, invece di partire fingendo di non saperlo.

> ### ⭐ E il risultato è la differenza fra un banco e un banco che serve
>
> `non giudicate: 5` ⇒ `non giudicate: **0**`. ⚠ Nessuno dei cinque era un rosso — la maglia aveva la
> decenza di non giudicare (§4.5) — ⛔ **ma una prova che giudica la metà delle volte vale la metà.**

### ⚠ E il TEMPO, misurato invece che stimato — *criterio §9.9*

`[M]` I dieci giri sono durati **12 minuti e 20 secondi**: ⭐ **74 secondi a giro**.

⇒ ⛔ **Il tetto dei 3 minuti per la famiglia veloce ci sta dentro solo con DUE giri.** ⚠ E questo è un
numero preso **con il difetto aperto**: ogni giro spende l'attesa intera del palco (90 s di tetto) e
poi lo sgombero. ⭐ Con le sessioni sane il giro sarà molto più corto — ⛔ ma finché non lo è, il
gancio non può far girare dieci giri di C1 a ogni modifica: **si tagliano prove, non si alza il
tetto** (§5.1).

## 7-bis.14 ⭐⭐⭐ **C11 È VIVA E DICE VERDE** — *la maglia che guarda la rete, non il prodotto*

⭐ È il guasto che l'utente ha nominato **per primo**, con parole sue: *«se sul container gnome
abbiamo remotix v1 e sul container kde remotix v1.2 andiamo a sbattere»* (D5). ⇒ Adesso c'è una
maglia che lo va a cercare, e `[M]` **26 agosto 2026**:

> ### ⭐ `le 4 scatole accese sono allineate su tutte le 13 voci dichiarate`

| ⭐ dev'essere uguale | ⛔ dev'essere diverso |
|---|---|
| la base (`13.6`) · mesa · libva · pipewire · libavcodec · ffmpeg · **firefox-esr** · libc · libssl · libei · libpci · ⭐ **l'md5 del binario del prodotto** | **il desktop** — `gnome-shell 48.7` · `kwin-wayland 6.3.6` · `labwc 0.8.3` · `labwc 0.8.3` |

⛔⛔ **E si guarda quel che c'è DENTRO le scatole accese, non quel che c'è scritto nelle ricette.** Le
ricette sono diverse **apposta**, e un confronto che deve prima «togliere le parti diverse» diventa
un confronto su cui si discute. ⇒ È la regola E1 applicata all'ambiente: *scritto non è in vigore*.

⚠ **Il primo giro è stato ROSSO**, e per la ragione giusta: il prodotto stava **solo** nella scatola
di GNOME. ⭐ Messo lo stesso identico binario in tutte e quattro, è diventato verde — ⇒ **la maglia
ha fatto esattamente il suo mestiere al primo colpo.**

### ⛔⛔ E ha avuto anche lei il suo difetto, che è il più insidioso di tutti

`[M]` Tre voci su tredici chiedevano pacchetti col nome sbagliato (`libssl3` invece di `libssl3t64`).
⇒ Tutte e quattro le scatole rispondevano **`?`** — e ⭐⭐ **`?` uguale a `?` è uguale**: quelle tre
voci **passavano il confronto**, per sempre, senza guardare niente.

> ⇒ ⭐ C11 adesso le **conta e le stampa**: *«N voci a cui nessuna scatola sa rispondere — e una voce
> muta passa il confronto senza aver guardato niente»*. `LEZIONI.md` §1.47.
>
> ⚠ È la stessa forma d'errore di §1.44 vista da un'altra parte: là il predicato diceva sempre sì,
> qui il confronto diceva sempre uguale. ⛔ **Un controllo che non ha mai dato rosso in vita sua va
> guardato in faccia, non festeggiato.**

## 7-bis.15 ⭐⭐⭐⭐ **C14 — LE QUATTRO SCATOLE NON SI DISTURBANO**, e adesso è misurato

§3.4 lo **affermava**; ⭐ adesso c'è la misura sotto. `[M]` **26 agosto 2026**, la stessa prova
(C8a) fatta girare **una scatola per volta** e poi **tutte e quattro insieme**:

| | sole | insieme |
|---|---|---|
| col guasto innestato | `1 sì · 1 no` × 4 | `1 sì · 1 no` × 4 |
| con la cura | `2 sì · 0 no` × 4 | `2 sì · 0 no` × 4 |

⇒ ⭐ **Stesso identico esito, quattro scatole su quattro, in tutt'e due i modi.**

### ⭐ E si chiude la riga che `11-accendi.sh` portava aperta

*«`--network=host` … quattro scatole accese insieme condividono le porte dell'ospite … **da rivedere
quando si fa C14**»*. ⇒ ⭐ **Rivista, e regge**: ciascuna ascolta la sua porta, ciascuna riconosce
come **propria** solo la sua e come **di un altro** le altre tre. La separazione per porta **è una
separazione vera**, e adesso ha una misura sotto invece di una speranza.

### ⚠ Il tempo — che è informazione, non verdetto

`[M]` **6,6 s da sola → 7,0 s in parallelo**, cioè **×1,06**. E il totale scende da 26,2 s a 7,0 s:
⭐ **il parallelo fa risparmiare ×3,76**.

⛔ **E un tempo misurato è stato BUTTATO, e il banco lo dichiara da sé**: col guasto innestato i
quattro tempi erano `125,9 · 126,0 · 126,0 · 126,1` s. ⚠ Quattro numeri uguali a un decimo non sono
un caso: col guasto il secondo inquilino non apre il browser e C8 lo **aspetta** fino al suo tetto.
⇒ Quel tempo è quasi tutto **attesa fissa nostra**, non lavoro — e chiamarlo «contesa» vorrebbe dire
misurare il proprio tetto e crederlo un difetto del prodotto.

### ⛔⛔ E che cosa NON misura, dichiarato

**Non misura la contesa vera sulla scheda grafica.** La prova A di C8 accende un browser che disegna
**in software**: la scheda non la tocca. La contesa vera vorrebbe quattro sessioni vive, e le
sessioni oggi nascono cieche (§7-bis.13). ⇒ Quel che è misurato è **lo strato di sotto**: le quattro
scatole riescono ad **aprire il codificatore nello stesso istante** (3 profili H.264 ciascuna, sole e
insieme). ⭐ Se già questo non reggesse, la contesa vera non avrebbe bisogno di essere provata.

### ⭐ E la certificazione ha bocciato il banco stesso

`[M]` **15 casi su 15**, ma solo dopo una correzione: il primo giudice buttava via il giudizio quando
**una sola** scatola aveva saputo rispondere. ⛔ Sbagliato — *una scatola che gira e non riesce a
riferire sta comunque occupando la macchina*, quindi il carico c'è e il giudizio delle altre vale.

⭐ **E la prova che sa dare rosso su dati veri, non solo sui casi finti**: `--smentisci` fa girare il
parallelo chiedendo di proposito l'**altro** modo di C8, così le impronte *devono* essere diverse ⇒
**4 scatole su 4 rosse.**

## 7-bis.16 ⭐⭐⭐ **IL GANCIO, C12 E C13** — *e il primo giro vero*

⛔ Il piano diceva di fare il gancio **per ultimo, e solo dopo che la rete avesse preso almeno un
guasto vero**: *«agganciare una rete che non prende niente è il modo più veloce di trasformarla in
cerimonia»*. ⇒ La condizione è soddisfatta — la rete ne ha presi due.

| | |
|---|---|
| `11-gancio.sh` | decide **per percorso** · fa girare · **lascia traccia** · si installa come hook di git |
| `11-c12-il-gancio-e-vivo.py` | esiste, è installato, è girato **davvero** e di recente. ⛔ Prende **il gancio spento in silenzio** |
| `11-c13-la-certificazione-e-recente.py` | negli ultimi giri un guasto è stato innestato **ed è stato visto** |

⭐ **Certificazioni: 11 su 11 ciascuna.** E il caso che tiene in piedi C13 merita di essere scritto:

> ⛔ **Un rosso venuto da un'altra maglia non certifica niente.** Se in un giro la rete è diventata
> rossa per conto suo (C1 sulla sessione cieca) **e** il guasto innestato **non** è stato visto, una
> C13 ingenua direbbe «certificata»: il giro porta scritto *ha dato rosso* e *guasto innestato*.
> ⇒ ⭐ Questa dà **rosso**, e fa **il nome della maglia** che ha mancato il guasto.

### ⛔⛔ Le prove TAGLIATE per stare nei 3 minuti — *e il taglio è dichiarato, non subìto*

`[M]` Un giro di C1 costa 74 s ⇒ nei 180 s ci stanno **due giri**. Nella famiglia veloce restano
**C11 + C1×2**. Fuori:

| tagliato | ⛔ che cosa costa |
|---|---|
| ⛔⛔ **C8, tutt'e due le prove** | **il taglio più caro**: la maglia più importante **non viene guardata a ogni modifica**. Resta nel giro completo |
| **C1 dal terzo giro in poi** | oggi non morde (10 su 10 nascono cieche, e due giri bastano) ⚠ **ma il giorno in cui il difetto sarà curato e tornerà raro, due giri non basteranno** |
| **il passo 0** | guarda l'ambiente, che non cambia quando cambia `src/`; e una scatola ricostruita di nascosto la prende **C11**, che nella famiglia veloce c'è |

⭐ E il gancio **salta** la maglia che non ci sta invece di troncarla a metà, e **scrive nel registro
che cosa ha saltato e perché**: ⛔ troncare darebbe un rosso che non è del prodotto (`LEZIONI.md`
§1.45).

### ⚠ E il gancio si aggancia PRIMA DI MANDARE, non a ogni salvataggio

Tre minuti a ogni commit sono esattamente la cosa che §5.1 dice che fa **spegnere** un gancio. ⇒ Il
predefinito è `pre-push`; chi vuole `pre-commit` lo chiede per nome.

⚠ E una cosa che il percorso **non sa dire**, dichiarata invece di essere nascosta: *«prima di
chiudere una fase»* non è un file che cambia, è una **decisione** ⇒ si chiede per nome
(`--famiglia tutto`). ⭐ L'ingresso di un desktop nuovo invece **sì**: si vede da una
`Contenitore.<nome>` che compare.

### ⛔⛔ IL PRIMO GIRO VERO — e ha trovato tre cose che nessuna prova a secco aveva preso

`[M]` 26 agosto 2026. Il gancio è stato costruito **senza la macchina di prova** (l'agente che lo
scriveva non ce l'aveva, e lo ha dichiarato). ⇒ Al primo giro vero:

| ⛔ che cosa è successo | ⭐ che cosa insegna |
|---|---|
| ⛔ **`GIRA_C11: command not found`** — una funzione che non esiste. L'esito è stato **127**, e il giro è proseguito come se niente fosse: la famiglia veloce girava **senza la sua prima maglia** | ⚠ `bash -n` passa, perché la sintassi è valida (`LEZIONI.md` §1.40). ⛔ **Si vede solo facendola girare** |
| ⛔ **il gancio pretendeva un deposito git per GIRARE** | ⭐ le due metà vivono in due posti diversi: **decidere** vuole il deposito (portatile), **far girare** vuole le scatole (macchina di prova, dove il deposito **non c'è**). ⇒ Con la famiglia chiesta per nome non c'è niente da decidere, e il deposito non serve |
| tre `git: command not found` per giro | rumore che somiglia a un guasto ⇒ senza deposito non si elenca niente, e **non è un errore** |

### ⭐⭐⭐ E IL GIRO COMPLETO È STATO FATTO — *`[M]` 26 agosto 2026, 28 minuti*

La famiglia `tutto` su GNOME, quella che si fa **prima di chiudere una fase**, girata dal gancio dal
principio alla fine:

| maglia | esito | tempo |
|---|---|---|
| passo 0 | ⭐ regge — 18/18 | 16 s |
| C1 × 10 | ⛔ **NON REGGE** — 10 cieche su 10, **zero non giudicate** | 760 s |
| C8 | ⭐ regge — tutt'e due gli inquilini aprono il browser | 6 s |
| ⭐⭐ **C8 col guasto innestato** | ⭐ **il guasto è stato VISTO**: 1 inquilino su 2 non apre il browser | 126 s |
| C11 | ⭐ regge — 13 voci su 13 | 10 s |
| C12 | ⚠ *terreno non regge* — ⛔ e **è la risposta giusta**: su quella macchina non c'è il deposito git, e C12 guarda i ganci di git | 0 s |
| C13 | ⛔ NON REGGE **durante il giro**, ⭐ **verde subito dopo** | 0 s |
| C14 | ⭐ regge | 786 s |
| | | **totale 1 704 s** |

> ### ⭐⭐ E il momento che conta è quello di C13
>
> Durante il giro C13 era **rossa**, e diceva il vero: *«negli ultimi giri **nessun guasto è mai
> stato innestato** ⇒ la rete gira, e nessuno la mette alla prova. ⛔ Da fuori è indistinguibile da
> una rete che funziona benissimo.»*
>
> ⇒ Finito il giro — che il guasto innestato **ce l'aveva dentro** — C13 è **verde**:
> *«negli ultimi 3 giri un guasto è stato innestato ed **è stato visto**»*.
>
> ⭐ **Cioè la rete adesso sa dire di sé stessa se è ancora capace di dare rosso.** ⚠ E lo dice con
> il suo limite attaccato: *«sui guasti che CONOSCE — e ogni desktop nuovo deve entrare con un
> guasto suo»* (§3.6).

⚠ **E due letture che vanno fatte con attenzione**, perché sembrano buone notizie e non lo sono:

| | |
|---|---|
| **C1 × 10 costa 760 s** | ⭐ 76 s a giro, coerente con i 74 misurati prima. ⛔ È il motivo per cui nella famiglia veloce ce ne stanno **due**, e non è un numero che si può migliorare tagliando: è il tempo che il prodotto impiega a **non** far nascere un monitor |
| **C8 è durata 6 s** | ⚠ **non è la sua velocità vera**: gli inquilini c'erano già dal giro prima, col profilo del browser già fatto. ⛔ Da zero costa molto di più — lo dice l'altra riga, i **126 s** del giro col guasto innestato |

## 7-bis.17 Che cosa esiste adesso, su disco

| file | |
|---|---|
| `banchi/11-scatole/Contenitore.gnome` | ⭐ la **ricetta** della scatola: sistema, desktop, scheda, attrezzi, l'inquilino, e l'unità che allinea il gruppo della scheda |
| `banchi/11-scatole/11-accendi.sh` | costruisci · accendi · prodotto · server · **c1** · **c5** · **c7** · **c8** · **c9** · **c10** · passo0 · impronta · spegni — ⭐ **con ogni permesso giustificato da quel che si rompe senza** |
| `banchi/11-scatole/11-passo0.sh` | ⭐ le **otto verifiche** dell'ambiente, con i tre esiti distinti |
| `banchi/11-scatole/11-c1-nasce-e-si-vede.py` | ⭐⭐ **la prima maglia della rete**, e il collaudo A. Con `--certifica`: **5 casi su 5**, compreso quello in cui *«cieca»* deve vincere su *«monitor 1/1»* |
| `banchi/11-scatole/Contenitore.kde` | ⭐ la **seconda scatola**, con KWin — la prova che la rete non è fatta su misura di GNOME |
| `banchi/11-scatole/Contenitore.xfce` · `Contenitore.lxqt` | ⭐ la **terza e la quarta**, con `labwc` — ⚠ quattro scatole, **tre** compositori (§7-bis.9) |
| `banchi/11-scatole/adattatore.{gnome,kde,xfce,lxqt}.sh` | ⭐⭐ **il «come» di ogni desktop**, allo stesso percorso dentro ogni scatola: la lista delle prove resta **una** |
| `banchi/11-scatole/11-c8-il-secondo-apre-il-browser.py` | ⭐⭐⭐ **la maglia più importante**, e il collaudo B. Con `--certifica`: **8 casi su 8**; con `--senza-cura`: il guasto innestato |
| `banchi/11-scatole/11-c8-pagina.html` | il **bersaglio nei pixel**: `#FF00FF` a schermo intero, con le scritte apposta per non essere «tinta unita» |
| `banchi/11-scatole/11-c11-allineamento.py` | ⭐⭐ **la maglia che guarda LA RETE**: le quattro scatole d'accordo su tredici voci, e l'md5 del prodotto fra queste. Con `--certifica`: **6 casi su 6** |
| `banchi/11-scatole/11-c14-non-si-disturbano.py` | ⭐⭐ **le quattro scatole non si disturbano**, misurato: stesso esito sole e insieme. Con `--certifica`: **15 casi su 15**; con `--smentisci`: dà rosso su dati veri |
| `banchi/11-scatole/11-gancio.sh` | ⭐⭐⭐ **quando parte la rete, e che cosa parte** — deciso **per percorso**, col tetto dei 3 minuti e le prove tagliate dichiarate |
| `banchi/11-scatole/11-gancio-registro.jsonl` | la **traccia** di ogni giro: che cosa è partito, che esito, quanto è durato, se è stato innestato un guasto. ⛔ È quel che tiene in vita C12 e C13 |
| `banchi/11-scatole/11-c12-il-gancio-e-vivo.py` · `11-c13-la-certificazione-e-recente.py` | ⭐ le due maglie che guardano **il gancio**. `--certifica`: **11 casi su 11** ciascuna |
| `banchi/11-scatole/11-c5-il-suono-non-e-silenzio.py` | ⭐⭐ **il suono**: si misura l'**RMS** dei campioni che arrivano al cliente, soglia dichiarata **328/32767** (−40 dBFS). ⭐ Giudica **byte**, non pixel ⇒ è l'unica maglia che oggi attraversa il prodotto da cima a fondo. `--certifica`: **12 casi su 12** |
| `banchi/11-scatole/11-c7-si-chiude-e-non-resta-niente.py` | ⭐⭐ **i residui**: impronta prima, sessione, chiusura, impronta dopo. ⚠ E il caso che **non** deve dare rosso: «si stacca soltanto» (I4). `--certifica`: **13 casi su 13** |
| `banchi/11-scatole/11-c9-il-registro-dice-di-chi.py` | ⭐⭐ **il registro**: due inquilini vivi **insieme**, e ogni riga obbligata deve dire quale. `--certifica`: **16 casi su 16** |
| `banchi/11-scatole/11-c10-le-copie-gemelle.py` | ⭐ **le copie gemelle**, e ⛔ l'elenco lo **legge da `src/Makefile`** invece di ricopiarlo. `--certifica`: **15 casi su 15**. ⭐ Gira **ovunque**, in 0,04 s, e non accende niente |
| `banchi/10-f1-testimone.py` | ⛔ **non è di questa fase e non si tocca**: è il giudice delle immagini, già tarato sul vero. C8 lo **importa** — due giudici che possono divergere in silenzio sono peggio di uno |

## 7-bis.18 ⭐⭐⭐⭐⭐ **QUATTRO MAGLIE IN PIÙ — e la rete adesso guarda anche quel che non è un pixel**

`[M]` 26 agosto 2026, sera. Quattro agenti in parallelo, **una scatola per ciascuno** (kde, xfce,
lxqt, e il portatile), inquilini con prefissi separati, log e unità separate. ⭐ E il criterio della
scelta è uno solo: **nessuna delle quattro giudica un pixel** ⇒ sono le quattro che il difetto delle
sessioni cieche (§7-bis.13) **non blocca**.

| maglia | il metro | certificazione | costo `[M]` |
|---|---|---|---|
| **C5** il suono non è silenzio | **RMS** dei campioni che arrivano al cliente · soglia **328/32767** (−40 dBFS) · ≥ 200 blocchi · ≥ 50 % sopra soglia | **12 su 12** | 38 s |
| **C7** si chiude e non resta niente | impronta **prima** / sessione / chiusura / impronta **dopo** — processi, socket, unità, scheda | **13 su 13** | 26 s |
| **C9** il registro dice di chi parla | **due** inquilini vivi insieme, e ogni riga obbligata deve dire quale | **16 su 16** | 50 s |
| **C10** le copie gemelle | i tre file gemelli byte per byte, ⭐ con l'elenco **letto da `src/Makefile`** | **15 su 15** | 0,04 s |

### ⭐ E la taratura di C5 è stata fatta attraversando il confine, non dichiarata

`[M]` Sei sessioni vere: ampiezza **0,02 ⇒ RMS 463, VERDE** · ampiezza **0,01 ⇒ RMS 231, ROSSO**. Il
percorso è trasparente (guadagno **1,0000**), e i valori sintetici della certificazione coincidono
con quelli del filo (463,4 contro 463,1). ⛔ Una soglia che non si è vista fallire è un numero
inventato.

### ⭐⭐ E C5 dimostra la sua tesi con un numero, invece di affermarla

Nello stesso giro in cui il registro diceva *«nessun monitor virtuale da catturare»* e *«0 fotogrammi
spediti»*, C5 ha contato **4 878 blocchi di suono, 4,6 MB, RMS 23 168**. ⇒ ⭐ **Zero pixel, e
qualcosa da giudicare lo stesso**: oggi C5 è l'unica maglia che attraversa il prodotto da cima a
fondo.

### ⛔⛔ IL PRIMO ROSSO CHE LA RETE TIRA FUORI DAL PRODOTTO — **due righe di `src/tastiera.c`**

`[M]` C9, su **tutte e quattro** le scatole: 5 752 righe di registro, **5 490 obbligate**, e **4** che
non si possono attribuire a nessun inquilino. Sono `src/tastiera.c` e `:486`, che scrivono nel
**padre** senza `registro_dice_di()`. ⛔ Due righe identiche parola per parola, una per inquilino:
**con due sessioni vive non si può dire quale sia di chi.**

⭐ Non è un guasto iniettato, non è un banco che sbaglia: **è il prodotto**, e non lo cercava
nessuno. La cura è di due righe — ⛔ **non applicata**, perché toccare `src/` obbliga a ricostruire e
a rimettere il binario in quattro scatole, e l'ordine delle fasi è una decisione dell'utente (§11).

⚠ **E accanto, un rilievo che NON è un rosso**: `[M]` **1 402 righe (25,5 %)** nominano l'inquilino
solo nella prosa e non nella parentesi. Sono attribuibili ⇒ C9 le conta e le stampa senza giudicarle.
Volerle rosse è una decisione, non un difetto.

### ⛔⛔⛔ IL SECONDO ROSSO — **e questa volta è di UN desktop solo**

`[M]` Cablate le maglie, sono state fatte girare **tutte e tre su tutte e quattro le scatole**, con i
loro guasti innestati. Ventotto giri. Ed è saltato fuori questo:

| | gnome | kde | xfce | lxqt |
|---|---|---|---|---|
| **C5** il suono | ⛔ **ROSSO** | ✅ | ✅ | ✅ |
| C5 col guasto innestato | ⭐ visto | ⭐ visto | ⭐ visto | ⭐ visto |
| **C7** i residui | ✅ | ✅ | ✅ | ✅ |
| C7 «si stacca soltanto» (I4) | ✅ | ✅ | ✅ | ✅ |
| C7 col guasto innestato | ⭐ visto | ⭐ visto | ⭐ visto | ⭐ visto |
| **C9** il registro | ⛔ rosso *(il difetto del prodotto, uguale dappertutto)* | ⛔ | ⛔ | ⛔ |

⭐⭐ **C5 è verde su tre desktop e rossa sul quarto**, e il quarto è **GNOME** — cioè quello su cui il
prodotto è nato. I numeri:

| | gnome | kde / xfce / lxqt |
|---|---|---|
| blocchi arrivati al cliente in 25 s | `[M]` **34 – 41** | `[M]` **~4 878** |
| blocchi entrati nel codificatore | `[M]` **115** | `[M]` **~4 996** |
| di cui silenzio digitale, taciuti | `[M]` **74 su 115** | ~2 % |
| RMS di quel che arriva | **22 977** (forte) | 23 168 |

⇒ ⛔ **Non è «il suono manca»: è che ne arriva un quarantesimo.** Quel che arriva è forte e giusto
(RMS 22 977, picco al fondo scala, 100 % sopra soglia): ⭐ **la soglia non c'entra**, e infatti C5 non
dà rosso per il livello ma per il **conto** — *«41 blocchi su 200 attesi al minimo: non è un
flusso»*.

⚠ **E non è la scatola invecchiata**: la scatola di GNOME è stata **buttata giù e rifatta**, prodotto
e server rimessi dentro, e il rosso è tornato identico. ⛔ Tre giri su tre.

> ⭐⭐⭐ **Ed è la tesi della fase, misurata una seconda volta e nel verso che nessuno si aspettava.**
> §7-bis.7 diceva *«il secondo desktop ha chiesto una cosa che il primo non chiedeva»*. ⇒ Qui il
> desktop che si comporta diversamente è **il primo**, quello di casa: le tre scatole nuove vanno, e
> quella su cui il prodotto è cresciuto no. ⛔ Senza le altre tre, questo numero sarebbe stato letto
> come *«il suono va così»*.
>
> `[?]` **La causa non è stata trovata**, ed è scritta invece che indovinata: il sospetto è che nella
> sessione GNOME qualcosa d'altro tocchi il grafo audio dell'inquilino (`wireplumber` che sospende, o
> un secondo `pipewire` della sessione), ma ⛔ **non è misurato**, e finché non lo è resta un `[?]`.

### ⛔⛔ E UN DIFETTO NEL CABLAGGIO, che nessuna certificazione poteva prendere

`[M]` `esegui_maglia` legge una maglia innestata **al contrario**: `0` vuol dire *«il guasto è stato
visto»*, e nel registro finisce `ha_visto_il_guasto`, che è quel che C13 legge. ⛔ **C9 usciva col
verdetto grezzo** ⇒ nel giro col guasto avrebbe scritto `false` **proprio quando il guasto era stato
visto benissimo**, e C13 avrebbe cominciato a mentire.

⭐ **E la cura non era invertire l'esito**: C9 è rossa **anche senza guasto** (le due righe di
`tastiera.c`), quindi un semplice *«rosso ⇒ visto»* avrebbe detto «visto» anche se l'iniezione non
avesse morso — un predicato che non può fallire, §1.44 di nuovo, e stavolta a reggere la
certificazione di tutta la rete. ⇒ Si pretendono **due** cose: verdetto rosso **e** più righe senza
nome di prima. `[M]` 4 senza guasto ⇒ 5 490 col guasto. ⇒ `LEZIONI.md` §1.52.

⚠ E un secondo difetto dello stesso genere, `LEZIONI.md` §1.51: `11-accendi.sh prodotto` falliva su
tutte e quattro le scatole con *«Text file busy»* — ⛔ un rosso che veniva dall'**ordine dei
comandi**, non dal prodotto.

### ⭐⭐ LA METÀ-PORTATILE DEL GANCIO ADESSO È VIVA — **e ci mette 1 secondo**

§4.6-novemdecies aveva scoperto che il gancio ha due metà su due macchine. ⛔ Quella sul portatile
non innestava **nessun** guasto ⇒ C13 là non avrebbe potuto **mai** diventare verde. ⇒ C10 ha adesso
un `--guasto-innestato` che copia i file **veri** in una cartella temporanea, ne cambia **un byte** e
pretende il rosso.

`[M]` Sul portatile, famiglia `rete`: **C10 verde · C12 verde · C13 verde**, ⭐ in **1 secondo**,
senza accendere niente. (C11 e C14 dicono *«non ho potuto guardare»*, ed è giusto: le scatole non
sono lì.) Il gancio è stato **installato** come `pre-push`.

### ⚠ E i tagli, dichiarati invece che subìti

`[M]` Il tetto della famiglia veloce è a **173 s su 180** — ⚠ misurato di nuovo il 26 agosto con
C10 dentro e con la voce nuova di C11: **venti secondi in più di quanto si credeva**, e resta pieno.
§5.1 dice che una maglia in più si
**scambia**, non si somma. ⇒ C5 (38 s), C7 (26 s) e C9 (50 s) stanno in `tutto` e in `desktop-nuovo`,
col loro guasto innestato accanto. ⛔ **L'unica che entra nella veloce è C10**, che costa meno della
risoluzione del cronometro. ⭐ E ci entra **due volte**: anche nella famiglia `rete`, perché il
gemello vive metà in `src/` e metà in `banchi/rcp/`, e un cambiamento **lì** fa scattare `rete` — cioè
esattamente il cambiamento che rompe il gemello.

## 7-bis.19 ⭐⭐⭐⭐⭐ **IL 27 AGOSTO — la rete è completa, e il tappo non c'era**

`[M]` Una giornata, fino a **dieci agenti insieme**, e il risultato in una riga: ⭐ **le quindici
maglie esistono, girano, e il difetto più vecchio del progetto è chiuso.**

### ⭐⭐⭐ Il fatto della giornata: **le sessioni non nascevano cieche**

Il difetto di `fasi/10-…` §7.4 — *«dieci sessioni nuove su dieci nascono senza monitor»* — bloccava
cinque prove della rete e rinviava la fase 12. ⛔ **Non era del prodotto, e non era nemmeno un
difetto solo.** Sono state tre cose, e ciascuna nascondeva la successiva:

| | che cos'era | come si è visto |
|---|---|---|
| ⛔⛔ **la prova** | **C1 non poteva dire verde** — leggeva `ZERO MONITOR`, che il prodotto scrive nel percorso di una nascita **riuscita**, e il suo ramo verde era irraggiungibile | un agente mandato a **smentirla** ⇒ `LEZIONI.md` §1.53 |
| ⛔ **la scatola** | il §6 della ricetta spostava il gruppo `polkitd` da 991 per darlo alla scheda; `groupmod` non porta i file ⇒ `polkit` moriva, `gnome-shell` incassava **4 scadenze da 25 s** | `[M]` da **~97 s** a **1,0 s** dopo la cura ⇒ §1.54 |
| ⭐⭐⭐ **la causa vera** | **l'inquilino non era nei gruppi `video` e `render`** | `[M]` **17 sessioni su 17** vedono coi gruppi · **0 su 4** senza · ⭐ dati i gruppi allo stesso inquilino ⇒ **2,04 s**. Una variabile sola, esito ribaltato |

⭐⭐ **E la tabella di §7.4 si spiega da sola**: `provanic4/5/6` — quelli che non videro **mai**, su
**98 · 55 · 50** tentativi — non hanno quei gruppi; `prova` e `provanic1`, che videro sempre, li
hanno. ⇒ ⛔ **Non era intermittente: erano due popolazioni di inquilini.**

⚠ **E la coda tocca il passato**: i banchi creavano inquilini per conto loro in **tredici** posti, e
⛔ senza quei gruppi. ⇒ Ogni banco che ha misurato lì ha misurato **una sessione che non vedeva**.
⭐ Curati dodici in **un file solo** (`banchi/attrezzi-gruppi-scheda.sh`), e uno di essi
(`07-b64-terreno.sh`) lo usano **ventitré banchi** delle fasi 9 e 10.

### ⭐⭐ E il monitor: come nasce davvero, letto e misurato

`[R]` `--headless` da solo **non crea nessun monitor**, ed è voluto. In tutto Mutter **due** posti ne
creano uno: la bandiera `--virtual-monitor` all'avvio, e `RecordVirtual`. ⭐ E quello di
`RecordVirtual` nasce **quando PipeWire fissa il formato**, cioè **dopo che un consumatore si è
agganciato** — `[M]` 65–93 ms dopo, mai prima.

⇒ ⭐⭐ **Ecco perché le cinque prove «bloccate» non erano bloccate**: mentre un cliente è attaccato,
lo schermo **c'è** — che è esattamente la condizione in cui quelle cinque lavorano.

⚠ E un debito, scritto invece che nascosto: `[M]` il monitor **muore con la connessione D-Bus** di
chi ha chiamato `RecordVirtual`, che nel prodotto è il **figlio**, e il figlio muore col client. ⛔ Sulla
carta contraddice I4. ⭐ Ma **C6 misura verde**: `[M]` stesso figlio, stessa scena (60,5 % ⇒ 60,5 %,
scarto 0,000) — **le finestre si ritrovano**. ⇒ Resta un debito dichiarato, non un lavoro di oggi.

### ⭐ Le cinque maglie che mancavano, e la sesta che nessuno aveva chiesto

| | certificazione |
|---|---|
| **C2** una finestra si apre — il pixel, non il conto dei processi | 51 casi |
| **C3** i fotogrammi cambiano — il canarino contro l'immagine congelata | 56 |
| **C4** il tasto arriva **fino allo schermo** — e solo nella **zona attesa** | 37 |
| **C6** si stacca e si ritrova — ⭐ legge il **pid del figlio**, non il colore | 46 |
| **C8b** la pagina vista **dal cliente** — il verdetto è una **differenza** | 17 |
| ⭐⭐ **C15** la metà remota gira davvero | 21 |

⭐⭐ **C15 non era nella lista, ed è il buco più serio che restava**: ⛔ con la macchina di prova spenta
per sempre, `[M]` **C12 e C13 restano verdi** e nessuno si accorge che le maglie vere non girano più.
⇒ Dimostrato togliendo dal registro l'unica riga eseguita sulle scatole: **C12 verde · C13 verde ·
C15 ROSSA** sullo stesso file.

### ⛔⛔ E le maglie mentivano ancora — **dieci difetti, e due erano in tutte**

⭐ Due agenti mandati a **refutare** hanno trovato quel che nessuna certificazione aveva preso:

| | |
|---|---|
| ⛔⛔ **«AMMESSO» era un predicato che non poteva dire di no** | quella parola sta **anche nei due messaggi di rifiuto** ⇒ **nove maglie** credevano di essere entrate anche quando erano respinte. ⭐ Curato con **una** funzione per nove, e la prova: col controllo vecchio, **7 casi nuovi su 9** rispondevano male |
| ⛔ **il guasto innestato letto sul colore** | una maglia già rossa per conto suo diceva *«il guasto è stato visto»* anche se l'iniezione non aveva morso ⇒ §1.52, curato in **C5, C9, C10** |
| ⛔⛔ **C7 diceva verde su una I4 rotta** | chiedeva *«è cambiato qualcosa?»* invece di *«il figlio c'è ancora?»* |
| ⛔ **C8 accusava il filo** | un cliente **respinto** usciva come *«nessun fotogramma è arrivato dal filo»* |
| ⛔ **il gancio** | un esito `3` faceva scrivere `ha_visto_il_guasto: false` — un'accusa a una prova che non è girata |

### ⭐⭐⭐ IL GIRO INTERO, e i numeri

`[M]` 27 agosto 2026, `--famiglia tutto` sulle quattro scatole, binario `aa950804fed7`:

| | |
|---|---|
| durata | **7 896 s** (2 h 11) |
| esiti `0` | **57** |
| ⭐ **guasti innestati visti** | **23 su 25** |
| esiti `3` (*«non ho potuto guardare»*) | **6** |
| ⛔ rossi | **3**, e sono **lo stesso rosso**: C1 su kde/xfce/lxqt |
| ⭐⭐ **rossi del banco** | **nessuno** |
| **C11** allineamento | ⭐ verde, 14 voci, stesso binario in tutte e quattro |
| **C14** non si disturbano | ⭐ verde, **801 s**, impronta identica sola e in parallelo |

⛔ **E i tre rossi sono il prodotto, ed è la fase 12**: `[R]` `src/sessione.c` · `scrivi_dropin()` — il prodotto sa
avviare **solo GNOME**. ⇒ Su KDE, XFCE e LXQt la rete prova l'ambiente, il suono, i residui, il
registro e l'allineamento; ⛔ **non il prodotto**, perché lì il prodotto non ci gira.

### ⭐ E cinque cure nel prodotto, tutte nate da una maglia

| | |
|---|---|
| `src/tastiera.c` · `webtransport.c` | ⭐ **il primo rosso che la rete ha tirato fuori dal prodotto**: 4 righe di registro su 5 490 non dicevano di chi parlavano |
| `src/figlio.c` — l'anello dell'audio | ⛔ non si svuotava senza palco ⇒ `[M]` **96 489 ms** di trabocco |
| `src/figlio.c` — la busta non inizializzata | ⛔ **il «terzo stato» di §7.4 era memoria sporca** ⇒ §1.55 |
| `src/mutter.c` | una riga diceva *«monitor virtuale montato»* quando il monitor **non esisteva ancora** |
| `src/provisiona.sh` + `src/figlio.c` | ⭐⭐ i gruppi della scheda, letti **dal nodo**, e un controllo che **lo dice nel registro** invece di far nascere una sessione che non si vede |

---

# §8 · Le domande, e le risposte avute

*Le sei domande della prima stesura. ⭐ Cinque hanno avuto risposta dai due revisori; una resta
all'utente.*

| | | esito |
|---|---|---|
| **Q1** | che classe di regressione il disegno non prende? | ✅ **risposta**, ed è diventata **§6** |
| **Q2** | il contenitore regge il pezzo che tiene il conto di chi è collegato? | ⭐⭐ **CHIUSA CON UN `[M]`, 26 agosto 2026: SÌ** — 18 verdi su 18, al prezzo di due permessi dichiarati (§7-bis.1) |
| **Q3** | come si resta ciechi al desktop? | ⭐⭐ **CHIUSA CON UN `[M]`, 26 agosto 2026**: le stesse otto verifiche girano su **Mutter e su KWin** senza una riga cambiata — 18/18 su tutt'e due (§7-bis.7) |
| **Q4** | un utente per scatola: che cosa si perde? | ⚠ **la correttezza a più utenti, che non è capienza** ⇒ ❓ **§4.4, decide l'utente** |
| **Q5** | quanto deve durare la famiglia veloce? | ✅ `[?]` **3 minuti**, provvisorio, da misurare (§5.1) |
| **Q6** | la marca è la strada giusta? | ✅ *«sì, ma da sola no»* ⇒ **§4.3** |

## 8.1 ⚠ E una cosa che nessuno dei due revisori ha detto, e va scritta

⛔ **Tutt'e due hanno accettato senza discutere la premessa più fragile del disegno**: che il
contenitore debba ospitare **il prodotto intero**. ⇒ Non è stato chiesto a nessuno se esista un
taglio diverso — per esempio il desktop dentro e il server fuori.
⚠ La risposta breve è che **non si può**, perché il prodotto accende il compositore **dentro** la
sessione che governa lui. ⭐ Ma è una `[?]` mai messa alla prova, e va lasciata scritta invece che
data per chiusa.

---

# §9 · I criteri di chiusura della fase

*Proposti dalla revisione, accolti: la fase **non è chiusa** se manca uno di questi.*

*⭐ Aggiornati il **26 agosto 2026**, mattina, con quel che è stato fatto nella notte.*

| # | | a che punto |
|---|---|---|
| 1 | il **passo 0** è stato eseguito e scritto, con esito `[M]` | ✅ **18/18 su quattro desktop** |
| 2 | esiste **una** scatola GNOME che gira | ✅ ⭐ **ne esistono quattro** |
| 3 | ⭐⭐ **la rete diventa rossa sul collaudo A senza suggerimenti** | ✅ `[M]` 5 sessioni cieche su 10 giudicate |
| 4 | la rete prende il **collaudo B**, ⚠ oppure è scritto perché non può e come si compensa | ✅ ⭐ **preso**: col guasto innestato il **secondo** inquilino non apre il browser, il primo sì (§7-bis.10) |
| 5 | le prove visive **non si basano solo sulla marca** | ✅ colore con **tolleranza dichiarata** + istogramma + il «prima» |
| 6 | il **gancio** è definito per percorso, non per buona volontà | ✅ ⭐ `11-gancio.sh`, e ha già girato sul vero (§7-bis.16) |
| 7 | esiste la **politica del rosso** | ✅ §5.2 |
| 8 | la rete ha **almeno una prova che controlla sé stessa** | ✅ ⭐⭐ **cinque**: C11 · C12 · C13 · C14 · **C15**, che non era nella lista ed era il buco più serio (§7-bis.19) |
| 9 | il **tempo** della famiglia veloce è misurato, non stimato | ✅ ⭐ `[M]` **173 s** su un tetto di **180**, e il **giro intero** `[M]` **7 896 s** (§7-bis.19). ⛔ La veloce è **piena**: una maglia in più si **scambia**, non si somma |
| 10 | ⛔ **quel che la rete non prende è scritto** | ✅ §6, ⭐ **compreso quel che oggi non può guardare e perché** |
| 12 | ⭐⭐⭐ **e la lista è finita**: undici prove del prodotto e cinque della rete, **tutte scritte, tutte certificate, tutte fatte girare** | ✅ `[M]` 27 ago: **57 esiti `0`**, **23 guasti innestati visti su 25**, ⛔ **nessun rosso del banco** (§7-bis.19) |
| 11 | ⭐⭐ e il criterio dell'utente, che sta sopra tutti: **la rete ha preso qualcosa che l'occhio non avrebbe preso**. Se no, **la fase è fallita e va detto** | ✅ ⭐⭐⭐⭐ **sì, e il conto è un altro adesso**: ⭐ **il difetto più vecchio del progetto**, chiuso il 27 ago — i gruppi `video` e `render` (§7-bis.19) · **cinque cure nel prodotto**, ognuna nata da una maglia · ⛔ **dieci difetti nelle maglie stesse**, due dei quali erano in **nove maglie su nove** · e prima ancora: **sì, e cinque volte**: la sessione che nasce cieca · il secondo inquilino che non apre il browser · ⛔ **tre rossi del BANCO** che sarebbero passati per difetti del prodotto (§7-bis.11) · ⭐ **le quattro righe di registro senza inquilino** · ⭐⭐ **il suono che su GNOME arriva a un quarantesimo** — e quest'ultimo **nessun occhio l'avrebbe visto**, perché il suono c'era ed era forte (§7-bis.18) |

---

# §10 · Che cosa resta `[?]` all'apertura

| | |
|---|---|
| ~~`[?]`~~ ⭐ **`[M]`** | ~~se il contenitore regga il pezzo di sistema che tiene il conto di chi è collegato~~ ⇒ **passo 0 eseguito il 26 agosto 2026: regge, 18 su 18** (§7-bis.1) |
| ~~`[?]`~~ ⭐ **`[M]`** | ~~quanto dura davvero la famiglia veloce~~ ⇒ **153 s su 180**. ⛔ E il tetto è **pieno**: qualunque maglia in più va **scambiata**, non sommata |
| ~~❓~~ ⭐ **chiusa** | ~~come si esegue C8~~ ⇒ **in una scatola, con due inquilini** (risposta dell'utente, §4.4), e ⭐ **il collaudo è passato** (§7-bis.10) |
| ~~`[?]`~~ ⭐ **`[M]`** | ~~se le quattro scatole davvero non si disturbano~~ ⇒ **misurato**: stesso esito sole e in parallelo, quattro su quattro (§7-bis.15). ⚠ **Resta fuori** la contesa vera sulla scheda grafica, che vuole sessioni vive |
| `[?]` | se esista un taglio diverso fra contenitore e prodotto (§8.1) |
| ~~❓ decide l'utente~~ ✅ **deciso** | il **registro del gancio** va in git — deciso dall'utente il 27 agosto 2026. ⭐ Con `merge=union` in `.gitattributes`: il quaderno è fatto di righe che si **aggiungono**, e due macchine che scrivono in giorni diversi non sono un conflitto da risolvere a mano. ⚠ Il prezzo, dichiarato: il file risulta modificato a ogni giro |
| ⛔ **APERTO, ed è la fase 12** | ⭐ `[M]` **il prodotto sa avviare solo GNOME** (`src/sessione.c` · `scrivi_dropin()`) ⇒ C1 dà rosso su kde/xfce/lxqt, ed è **l'unico rosso** che il giro intero produce. ⚠ E una cosa che la fase 12 troverà: ⛔ **KWin non sa nascere cieco** — con `--output-count 0` un'uscita la fa lo stesso, quindi il disegno «zero monitor propri» **non si trasporta uguale** |
| ⚠ **debito dichiarato** | il **palco muore con la connessione D-Bus del figlio** ⇒ sulla carta contraddice I4. ⭐ Ma `[M]` C6 misura **verde**: le finestre si ritrovano. ⇒ Scritto, non curato — la cura è architetturale (`DECISIONI.md` §4.6-teretvicies) |
| ~~⛔ aperto~~ ⭐ **chiuso** | ~~perché la scatola non si spegne da sola~~ ⇒ **era il SEGNALE, non un'unità appesa**: `[M]` SIGTERM (il predefinito di `podman stop`) lascia la scatola in piedi **30 s su 30** — `systemd` come primo processo lo ignora; `SIGRTMIN+3` la spegne in **3,1 s**. ⇒ I «quattro minuti» erano un tetto scaduto, non un'attesa. La cura (`STOPSIGNAL` nelle ricette) è in vigore, e ⛔ l'ipotesi *«la tiene su una sessione viva»* è **smentita**: con una sessione dentro lo spegnimento è quello pulito (§7-bis.18) |
| ~~⛔⛔ APERTO~~ ⭐ **chiuso** | ~~C5 è rossa su GNOME~~ ⇒ **era la stessa radice della sessione cieca**: senza palco il prodotto non svuotava l'anello dell'audio (`[M]` **96 489 ms** di trabocco). Curato in `src/figlio.c`; `[M]` C5 verde su tutte e quattro le scatole. *(voce vecchia: `[M]` C5 rossa su GNOME e verde sugli altri tre*: al cliente arrivano **34–41** blocchi di suono in 25 s invece di **~4 878**, e quel che arriva è forte e giusto. ⛔ Non è la scatola invecchiata (rifatta da zero, stesso rosso) e non è la soglia. `[?]` La causa non è misurata (§7-bis.18) |
| ~~⛔ APERTO~~ ✅ **curato** | ~~4 righe di registro su 5 490 non dicono di chi parlano~~ ⇒ curato il 27 ago in `src/tastiera.c`, `tastiera.h`, `webtransport.c` — ⚠ **otto righe, non due**: le due misurate più sei gemelle nella stessa funzione. `[M]` C9 verde su tutte e quattro |
| ❓ **decide l'utente** | il **registro del gancio** va in git o no? In git dà a C13 una memoria sola per tutte le macchine; fuori evita di avere quel file modificato a ogni giro. ⚠ E oggi ne esiste **uno solo, sulla macchina di prova** (`DECISIONI.md` §4.6-novemdecies) |
| ~~⛔ aperto~~ ⭐ **chiuso** | ~~perché la metà dei giri di C1 non giudica~~ ⇒ **era lo sgombero**: si aspetta l'evento e non l'orologio, e `[M]` il giro dopo dà **10 giudizi su 10** (§7-bis.13) |
| ~~⛔⛔ blocca~~ ⭐⭐⭐ **CHIUSO il 27 agosto** | **erano i gruppi `video` e `render` dell'inquilino**: `[M]` 17 sessioni su 17 vedono coi gruppi, **0 su 4** senza, e la controprova ribalta l'esito con una variabile sola (§7-bis.19). ⛔ E non era del prodotto: era della **provvista**, più una maglia che non poteva dire verde e una scatola che si rompeva da sola. *(voce vecchia: `[M]` dieci sessioni GNOME nuove su dieci nascono cieche* ⇒ C2, C3, C4, C6 e la metà B di C8 **non si possono misurare**. È il difetto APERTO della fase 10 §7.4 — ⛔ si tura curando il **prodotto**, non scrivendo un'altra maglia |
| `[?]` | quanto costa in capienza un fotogramma in più a testa — ⚠ **fuori da questa fase**, sta in `MASTERPLAN.md` M1 |

---

# §11 · ✅ **LA DOMANDA È DECADUTA** — *e la ragione vale più della risposta*

Questa sezione chiedeva: **«si va avanti con KDE avendo metà della rete che non può guardare, oppure
prima si cura la sessione che nasce cieca?»**

⇒ ⭐⭐ **La domanda non esiste più, perché la premessa era falsa.** `[M]` 27 agosto 2026: le sessioni
**non nascevano cieche**. Erano tre cose sovrapposte — una **maglia** che non poteva dire verde, una
**scatola** che si rompeva da sola, e la causa vera: ⭐ **l'inquilino non era nei gruppi `video` e
`render`** (§7-bis.19).

⇒ Le cinque prove dichiarate «bloccate» **non erano bloccate**, e oggi girano tutte.

> ### ⛔⛔ E la lezione è più grossa della fase
>
> Per settimane un numero — *«dieci sessioni su dieci»* — ha governato l'ordine del lavoro, il
> rinvio di una fase, e una lista di cose «impossibili». ⛔ **Quel numero veniva da un'unica prova, e
> quella prova non poteva produrre nessun altro risultato.**
>
> ⭐ Ci sono voluti dieci minuti a un agente il cui mandato era **«prova a smentirla»**. ⇒ La regola
> che ne esce, e vale oltre questa fase: **quando un rosso regge da giorni e nessuno riesce a farlo
> tornare verde, la prima domanda non è *«perché il prodotto è rotto»* ma *«questa prova sa dire
> verde?»***. ⇒ `LEZIONI.md` §1.53.

## ⭐ Quel che resta all'utente, adesso

| | |
|---|---|
| ✅ **il quaderno del gancio in git** | **deciso il 27 agosto**: sì, con `merge=union`. ⚠ Il prezzo è un file che risulta modificato a ogni giro |
| ⭐ **la fase 12 è il prossimo passo, e non è più bloccata** | ⛔ Ma quel che troverà è già misurato: il prodotto **sa avviare solo GNOME** (`src/sessione.c` · `scrivi_dropin()`), ed è **l'unico rosso** che il giro intero produce. ⚠ E KWin **non sa nascere cieco**: il disegno «zero monitor propri» non si trasporta uguale |
| ⚠ **un debito, non un lavoro** | il palco muore con la connessione D-Bus del figlio ⇒ sulla carta contraddice I4, ⭐ ma C6 misura **verde**: le finestre si ritrovano. Curarlo è architetturale, e ⇒ `DECISIONI.md` §4.6-teretvicies |

---

# §12 · Il giudizio dell'utente

*(da riempire alla chiusura)*
