# SPECIFICHE — what REMOTIX is, and what it promises

*Rewritten on 9 Aug 2026, incorporating the 44 decisions taken on 8 and 9 Aug.*

> **How to read this document.** Here is **what** the product does. The **why** of every
> choice, with the date and who made it, is in [`DECISIONI.md`](DECISIONI.md), and every paragraph
> refers to the corresponding entry. The **how it is measured** is in [`LEZIONI.md`](LEZIONI.md); the
> rules of whoever writes and whoever reviews in [`CODER.md`](CODER.md) and [`REVIEWER.md`](REVIEWER.md).
>
> The marks are those of `CODER.md` §5: `[M]` measured by us, `[R]` read in the code,
> `[S]` read in a specification, `[?]` hypothesised and not yet verified. **A line without a mark
> is a product decision, not a technical fact.**

---

## 1. What it is

REMOTIX is a **remote desktop system for Linux**, made of a server and **a web
page**, which speak a protocol of ours called **RCP** — *Remotix Control Protocol*.

| | |
|---|---|
| **server** | Linux only |
| **client** | ⭐ **nothing to install: a modern browser**. The server serves the page, the page speaks RCP over **WebTransport** |
| **Windows as a server** | ⛔ **out**, and it is the lever of §1.1 |
| **Windows as the place one connects from** | ✅ **in, and for free**: a browser on Windows is not our code. The same goes for macOS, iPhone, iPad, Chromebook and anything else that has a browser |

⭐ **No dedicated clients** *(decided on 9 Aug 2026, `DECISIONI.md` §1.6)*. The Android client
disappears — and with it five phases of the plan — and the Linux client disappears. What remains is **a server and a
page**.

⚠ **And the protocol has not changed by a single line.** WebTransport brings to a browser exactly the
building blocks RCP had been designed on: independent QUIC streams, dropping a frame,
datagrams for audio. Had the wire been designed on TCP, this decision would have cost
the whole protocol.

It is the evolution of REMOTIX v1, which stopped at phase 11 after serving GNOME and KDE
speaking RDP. v1's heritage — 17,481 lines of C, 4,563 lines of benches, five studies of the
desktops and the register of lessons — is under `fondamenta/` and is the base V2 rests on
(`DECISIONI.md` §6).

### 1.1 Why RDP dies, in one line

The three walls v1 stopped against — the H.264 ceiling, the Android client decoding in
software, full colour out of reach — **were all three RDP's, not the problem's**. The
line «no Windows» is the lever that removes them together. The price, accepted: the protocol must be
designed as well as written, and the clients must be written from scratch. (`DECISIONI.md` §1.1)

⭐ **And half of that price was given back on 9 Aug 2026**: the clients to write are no longer
two, it is **a single page** (§1). The first part remains whole — the protocol must be designed — and it is
the reason why `RCP.md` exists before the code.

---

## 2. The guiding principles

1. **Detect capabilities, not the distribution.** At start-up we check what is there, choose the
   best path and **declare** what is missing.
2. **Degrade, do not fail.** Every missing dependency has a fallback. The service works
   anyway, with less — but the fallback is declared in the log: a silent one produces two
   behaviours under the same label.
3. **Depend, do not rewrite.** Every component we write is a component to maintain
   forever.
4. ⭐ **We depend on the compositor, not on its surroundings.** The compositor has to be chased:
   only it delivers the frames and accepts input. Screen lockers, idle daemons,
   power managers and display managers do the same thing in four different ways, with
   four configurations that rewrite themselves: those are **not** chased.
   (`DECISIONI.md` §0.1 — it is the principle that produced several of the choices that follow)
5. **Talk directly to the compositor**, never through portals that ask for authorisation on
   screen: an unattended service has nobody to click.
6. ⭐ ⛔ **On the user's screen there is their desktop and nothing else.** *«Come se fosse davanti al
   monitor del PC»* — no artefacts, no marks, no service boxes. ⛔ And not in the
   form *«off by default»*: what we need in order to measure **does not go into the binary that
   gets installed** (`DECISIONI.md` §7.16, from the user on 11 Aug 2026; the clean-up is done and **is
   measured** in phase 13). ⚠ *Added when the first bench feature asked for permission to
   paint: the principle was not there, and the answer was wider than the question.*

---

## 3. The three numbers

They are the numbers the user sets and that technology adapts to, not the other way round. Every technical
choice is justified by showing that it brings one of these closer. (`CODER.md` §1 and §1-bis)

⚠ **Project goals, not measured promises** *(decision of the user, 30 Sep 2026)*: the performance
tests were removed (too dependent on the hardware) and the measurements with them; the thresholds of this
chapter — and the others in the document — remain as the **direction** of the technical choices, not as a guarantee.
The parameters the product really uses (minimum bandwidth, session ceiling, clocks, ban) are
configuration and apply as written.

⭐ **And all three measure the piece that is ours** *(`DECISIONI.md` §2.7, 9 Aug 2026)*: REMOTIX
promises what it **produces and delivers onto the line**. What the device on the other side
manages to decode and paint **is measured and declared, not promised** — it is not our
code. ⚠ With one boundary: a client that does not hold the minimum must be **told**, with the reason. A
silent fallback stays forbidden even when the blame is not ours.

### 3.1 Image quality

| | |
|---|---|
| **MINIMUM** | 480p · 25 fps · 24 bit |
| **DESIRED** | 4K · 60 fps · **10 bit per channel** |

⭐ **The minimum is a guarantee, not a goal.** It is not a bar to chase — v1 already
exceeded it `[M]` — but **the level below which we do not go and do not disconnect**, however bad
the line is. It comes from the mobile-network case (§8), not from giving up on quality.
(`DECISIONI.md` §2.1)

**The desired is at 10 bit, not at «32 bit».** Thirty-two bits are not an existing quantity: they are
24 of colour plus 8 of transparency, and transparency is not transmitted. Behind the intention
«massima qualità» there were two distinct levers, and one of them was chosen:

| Lever | Cure | Price |
|---|---|---|
| **10 bit per channel** ✅ | banding on gradients | almost nothing, and in hardware everywhere — Android decoder included |
| 4:4:4 `[?]` | fringed coloured text `[M]` v1 | much more bandwidth, and **no Android decoder in hardware** |

4:4:4 remains a `[?]` to measure, not a promise: it would be an option for the Linux client
only, on capable GPUs, and nobody has yet measured how much the difference shows.
(`DECISIONI.md` §2.2-2.3)

### 3.2 The delay

| | From the input arriving to the frame leaving |
|---|---|
| **CEILING** | 50 ms |
| **TARGET** | 40 ms |

⛔ **Only the piece that is ours is measured.** The network is not ours and changes from one minute to the next:
a «100 ms end-to-end» requirement would be failed while standing still, because of a tunnel — and a
requirement that can be failed without having done anything wrong **is measured by nobody**. The
total the user feels is this plus the network: it is **declared**, not promised.

⚠ **The delay weighs more than the frames**: 30 per second with 40 ms are perfectly usable, 60 with
200 ms are unbearable. A choice that raises the rate while worsening the delay is not made — and it is
a trade that comes up all the time, because **every intermediate buffer buys smoothness and sells
responsiveness**. (`DECISIONI.md` §2.4)

### 3.2-bis ⭐⭐ THE SPECIFICATION OF THE EXPERIENCE — dictated by the user on 22 Aug 2026

> *«Non pretendo un comportamento allineato al nanosecondo rispetto a una situazione locale, ma che
> gli si avvicini molto. La mia specifica è avere un'esperienza utente il più vicina possibile a una
> situazione locale, ma non identica: quello è impossibile.»*

⭐ **It is the yardstick of phase 8**, and it differs from the three numbers of §3 in one thing only but a decisive one: §3.2
promises **the piece that is ours** (input → frame leaving), this one says **what the user must
feel**. The two do not replace each other: the first can be acceptance-tested by a bench, the second is
the judgement the first serves.

> ✅ **The user's verdict, 10 Oct 2026** — manual test from **Windows with Chrome**, on the server's
> boxes (campaign binary `716e35b`, Intel UHD 770): *«Gnome, XFCE e LXQt funzionano in modo spettacolare»*;
> *«su windows l'esperienza d'uso è fantastica: sembra davvero di essere davanti al PC»*. ⇒ The specification above,
> for those three desktops, is **reached**. ⚠ KDE not: the desktop appears at half height in the browser (also for a
> second user, Zorin OS client), under examination the same day.

#### ⭐ The scene on which it was dictated, and the number the user produced by eye

22 Aug 2026, from the user's video: a terminal window dragged by hand inside the
session.

⭐ **And the user measured by eye the thing that counts**: the distance between the mouse arrow and the
window chasing it is **«la metà della larghezza della barra del titolo»**. ⇒ The speeds of the
hand and the calculations on that scene are in `fasi/08-l-anello.md`.

#### ⛔ Why it is an ELASTIC, and why the user calls it «fluidità» rather than «ritardo»

`[R]` In the classic mode the arrow is moved by **the browser**, at the speed of the hand (§7.1 and
`pagina.html`: the system cursor *and* the drawn arrow, overlapping, both local). The
window instead chases it with **all** the delay of the link. ⇒

```
gap = speed of the hand × delay of the link
```

⛔ **The gap is not constant: it grows when accelerating and closes again when slowing down.** Locally
it is **zero at any speed**. ⇒ The window *swims* relative to the hand, and this is
perceived as **lack of smoothness**, not as slowness — which is exactly the word
the user used first, before we knew its cause.

⭐⭐ **And the calculation goes both ways**: knowing the gap in pixels, the delay can be derived — but the
result changes a lot depending on the speed of the hand. ⏳ `[?]` **At what speed the user is
looking cannot be deduced**: the link must be measured, not asked of him.

#### ⛔ And the limit is declared, because the specification says «non identica»

A network link **cannot have zero gap**: there is a frame of the compositor, one of the
page, and the wire in between. ⇒ The gap **is halved or better, it is not removed**. Whoever promised
to make it disappear would promise something that does not exist — and it is precisely the part the user
put into the specification himself: *«ma non identica: quello è impossibile»*.

⏳ **The target in numbers is not written here until the link is re-measured** on the real scene. It must be
written **in the user's unit** — fractions of a title bar at a declared speed — because
that is the one he can judge without instruments.

#### ⭐ And the trade this specification forbids was ALREADY forbidden above

§3.2 says it from the start: *«every intermediate buffer buys smoothness and sells responsiveness»*, and *«a
choice that raises the rate while worsening the delay is not made»*. ⇒ ⛔ **Putting the link in parallel**
— encoding frame N while capturing N+1 — would buy frames per second paying for them in delay:
**it would make the elastic worse**, that is exactly the thing the user sees. It is **out**, and not because of a
new measurement: because of a line that was written before the defect had a name.

### ⚠ The delay measurements are historical

*13 Aug 2026, phase 3 step 5*: the capture → glass delay was measured on the hardware of the time,
with the product's encoding of the time. ⇒ The numbers, their breakdown stretch by stretch and the
discussion of the compositor are in `STUDI.md` §gnome §8.2 and §13 and in `DECISIONI.md` §2.5: they apply
to that machine and that product, **they are not guarantees** *(decision of the user of 30
Sep 2026)*.

⛔ **The method rule remains**: the delay is measured up to the **finished drawing**, not to the
decoder callback — cutting earlier means giving yourself a piece of the ceiling (`CODER.md` §1-bis). ⚠ And the
blind piece of the user's screen does not exist on Xvfb (`STUDI.md` §web §8).

---

## 4. The RCP protocol

```
librcp.so
rcp_frame_t · rcp_connect() · rcp_session_t
handshake:  RCP/1
```

The name says *Control*, not *Display*: the protocol does not carry only pixels — it carries input, clipboard,
geometry, farewell and session state, and video is **one** of its channels.

| | |
|---|---|
| **transport** | **WebTransport over HTTP/3**, that is QUIC with mandatory TLS 1.3 — **port 7447** by default, configurable |
| **video codecs** | **H.264** and **HEVC**, **only on the graphics card** — negotiated with the browser (`DECISIONI.md` §1.13); ⛔ no encoding on the processor (§11.4, `DECISIONI.md` §10.27) |
| **audio** | Opus, with PCM as an always-available base |
| **channels** | video · audio · input · cursor · clipboard · control |

⚠ **The server listens on two ports with the same number**: **TCP** to deliver the page, **UDP**
for HTTP/3 and WebTransport. ⭐ *Corrected on 9 Aug 2026 by measurement S1*: the two things are
**independent** — WebTransport does not go through `Alt-Svc`, it opens its own connection by itself — and this
removes the silent fallback onto TCP that I had declared as a danger.

⚠ **The protocol is not an implementation detail: it is the arbiter.** In v1 the oracle was `mstsc` —
if it drew, it was right. In V2 client and server are ours, and **two programs written by the
same hand that agree confirm nothing**: they repeat the same assumption. Hence
three obligations: `RCP.md` is written **before** the code and precise enough to be able to prove
someone wrong; client and server are acceptance-tested **against the specification**, not against each other; and where
possible, a validator that reads the wire is needed.

### 4.1 Trust — two levels, and no more

*Set by the user on 9 Aug 2026: «Abbiamo 2 livelli per la sicurezza: il trasporto e l'accesso».*

| Level | What it is | How it is solved |
|---|---|---|
| **the transport** | that nobody reads or rewrites what passes | **TLS**, always and with no alternatives. The certificate **is made by the server itself**, and the page passes its fingerprint to the browser |
| **the access** | who is admitted to that machine | **address, port, user and password**. Nothing else — §4.2 |

⛔ **There is no third level, and it is a decision**: no authority to install, no fingerprints
to compare by hand, no service of ours in between. The roads that added a level were
looked at and **discarded**, with the reasons in `DECISIONI.md` §1.7.

**What the user sees**: they open `https://indirizzo:7447`, **click through the warning the first time on
that device**, type user and password. ⭐ Everything else — regenerating the certificate before
it expires, publishing its fingerprint in the page — is **inside the server** and is not seen.

⚠ **The click remains, and it is the declared price of not having a domain.** Whoever has one puts in a
**real certificate** — a configuration line, not a different road — and the warning never
appears, iPhone included.

**The password does not leave** before the server has proved it is the same as yesterday —
invariant I3 applied to the order of the handshake.

⚠ The first connection **on each device** remains exposed to a man-in-the-middle. **Risk
assessed and accepted** for the intended scenario: own server, own network or VPN. ⛔ And with the
web client the **consequence** of that risk is bigger — whoever gets in the middle does not intercept
the page, **they rewrite it**. (`DECISIONI.md` §1.3 and §1.7)

⏳ **Deferred by decision of the user**: real hardening — MFA and whatever the technology
offers — is **an evolution to do once the project is complete**, not a piece of this one. It is highlighted
in `DECISIONI.md` §1.7, with the three items to reread that day.

### 4.2 Authentication

**Local PAM**, service `remotix`, with the **address ban** after three failed attempts.

⭐ ✅ **Three failed authentications from the same address within 5 minutes, and that address is out
for 12 hours** *(decided by the user on 10 Aug 2026 — `DECISIONI.md` §1.9, `RCP.md` §4.4-bis)*. The
**user name does not count**: three different names count three. A successful sign-in resets the count.

| | |
|---|---|
| **what counts** | ⛔ **only** failed authentication — non-existent user and wrong password are the same thing, as §4.1 requires. Not protocol errors, not timeouts, **and not the refusal of the second connection** (§5.1), which is what the same user's second device receives |
| **what whoever is banned sees** | the page **loads all the same** and says the attempts are used up. ⛔ Never a silence: whoever is banned by mistake is almost always the owner |
| **how one gets out** | ⭐ **the 12 hours passing, or an unblock command on the server** — which requires access to the machine, that is the only key that case admits. The ban **survives a restart** |

⚠ **The price, declared**: behind a NAT addresses are shared, so three mistakes by one
person close the door to everyone else for twelve hours — and it is the case for which the
previous form had a second counter, **removed knowingly**. And the first to trip over it is whoever types
a long password on a phone keyboard.

> ⛔ *Rewritten on 10 Aug 2026. This section said: «five failed attempts in five minutes,
> then a wait that starts at 30 seconds and doubles up to a ceiling of 15 minutes, with two counters
> — one per user name and one per address». It was 🔸, that is written by me and never spoken; now it is
> ✅ and harsher.*

⭐ **And one fixed second of delay on every answer, even when it is «admitted».** It does not serve to
slow down whoever is guessing: it serves to remove **timing** as a channel. Without it, «non-existent user»
answers in a millisecond and «wrong password» in fifty — and the distinction the
protocol forbids writing in the reason can be read with a stopwatch.

---

## 5. The session

### 5.1 A single graphical session per user

A user can have **countless** text sessions (ssh, tty) at the same time, but **only
one** graphical one — local or remote. Text and graphical sessions coexist.

| Situation | Outcome |
|---|---|
| has an active **local** graphical session and opens a remote one | ⛔ the remote one is **refused**, with an explicit message |
| has an active **remote** graphical session and opens a local one | ⛔ **the local one wins**: the remote one is closed |
| ⭐ has a remote one **active and alive** and connects from a **second device** | ⛔ **the second connection is refused** *(decided on 9 Aug 2026)* — it is invariant I2, and the reason is `GIA_ATTIVA_REMOTA` |
| has a remote one whose client **has been silent for 30 seconds** | that client is **detached** (§5.3): it does not hold the slot, and the new device **gets in** |

⚠ **The last two rows do not contradict each other, and the deciding factor is the silence clock**: a live
client occupies, a mute client does not. ⛔ The price, declared: if the laptop switches off suddenly without
saying farewell, from the phone you get in **after thirty seconds**, not at once.

### 5.2 The session survives the client

The stage — capture, control and virtual screen — **belongs to the session, not to the
connection**. The client is closed and the session stays alive; you reconnect, even from another
device, and find everything again. It is invariant I4, and it is the defect that in v1 made the session
unusable after the first detachment. (`DECISIONI.md` §4.1)

> ### ⛔⛔ BUT IT DOES NOT SURVIVE THE **SERVER** — `[M]` 25 Aug 2026
>
> ⭐ *«It survives the client»* is true and measured. ⛔ **«It survives the server» is not, and it had never
> been written anywhere.**
>
> ⭐⭐ **DISPROVED BY THE MEASUREMENT OF 29 SEP 2026** (`fasi/17-l-installatore.md` §5.2, T2): ten
> tests with real Firefox on the four desktops — stopping the unit (`KillMode=mixed`), killing only the
> parent, killing only the child — **no desktop dies**: parent, PAM helper and child die; the
> stage (started with `setsid --fork`, outside the unit), the session and the programs survive, and on
> reattaching the same compositor comes back with the windows. The fact of 25 Aug does not reproduce today.
>
> `[M]` Stopping the server's unit at **18:14:29** to update it, **the user's session
> died with it** — its windows included; at **18:14:44** a **new and empty** one was born. The
> reason is that the graphical session lives **in the server's process tree**, and the unit has
> `KillMode=mixed`.
>
> ⇒ ⛔⛔ **Today updating the server means throwing everyone out** — and it is the same damage that
> `DECISIONI.md` §4.7 forbids anyone to cause by shutting down the machine, ⚠ **done however by whoever
> administers, and without anyone having declared it.**
>
> ⭐ **It is not a broken promise: it is a boundary that had not been drawn.** It is here because the day
> the product becomes a service to update without stopping anyone — **phase 15** (it was 14 until 21 Sep 2026) — this is the
> point to start again from.
>
> ⚠ **And today it costs nothing, and that must be said**: *«nessuno sta lavorando sul server, REMOTIX è
> ancora in sviluppo»* — the user, 25 Aug 2026. ⇒ ⭐ **It is not an emergency: it is a boundary
> written now so that the day someone is inside, it is already known.**

### 5.2-bis ⭐ And it ends when the user logs out — the two exits are not the same

*Decided by the user on 15 Aug 2026 (`DECISIONI.md` §4.1-ter and §4.1-quater).*

| the user's gesture | what happens |
|---|---|
| closes the tab, closes the browser, **shuts down or restarts their own PC**, loses signal | ⭐ **a single case**: the wire drops, the **session stays alive**, and whoever comes back finds everything (§5.2). ⛔ The user's PC is not an actor of the model: there is nothing to tell apart |
| chooses **«Log Out»** from the desktop's system menu | ⛔ **the session ends**, and with it all the programs the user had running are closed. The page goes back to the **sign-in form** with the line *«the session has ended»*, and the reason on the wire is `SESSIONE_TERMINATA` (`RCP.md` §8.2 `0x10`) |

⭐ **It is the only gesture that declares «I am done»**, and that is why the «Log Out…» entry must **be there**: on
GNOME it must be switched on explicitly, because with one user and a single session the shell does not show it.

**And it can be reached in two ways** *(decided by the user on 15 Aug 2026, `DECISIONI.md`
§4.1-quinquies)*:

| | |
|---|---|
| the **«Log Out…»** entry in the desktop's system menu | the normal road, and ⭐ **it is enough on its own**: it can be reached with the pointer and with a finger, so it is there **on every device**, keyboard or not |
| ⭐ the shortcut **`Ctrl+Alt+Fine`** | it is handled by **the page**, not the desktop: once for all four desktops, and it works **even if the desktop no longer responds**. ⛔ The page keeps it for itself, so in the remote session that combination **never arrives**. ⛔ **It asks for confirmation** — *«end the session?»* — because it closes all open programs and costs a single gesture, where the menu costs three |

⛔ **And no on-screen button for logging out** *(decided by the user on 15 Aug 2026)*: the button
of §7.3-bis exists for `Ctrl+Alt+Canc`, which **has no menu entry**. Logging out has one.

### 5.3 The three clocks

| Clock | How long | What triggers |
|---|---|---|
| **client silence** | 30 seconds | the client is considered **detached**, and the encoder is freed |
| **user inactivity** | 30 minutes without input | REMOTIX **detaches** the client: user and password are needed to get back in |
| **session abandonment** | ⭐ **60 minutes without input** | the session is **closed**, **with a clean farewell** (`0x03`) |

They are in scale: seconds, minutes, minutes. The second and third are **configurable**, with those
values as defaults, and ⛔ **the value in force is written in the log at start-up** — a one-hour
ceiling is not verified by anyone waiting an hour.

> ### ⛔ The third clock has changed — decided by the user on **16 Aug 2026**
>
> It said ~~«**6 hours** without any **attach**»~~. ⇒ *«Niente timeout delle 6 ore: se dopo 60 minuti
> non c'è traccia di input la sessione viene killata.»*
>
> ⚠ **Two things change, not one**: the ceiling (6 hours → 60 minutes) and **the criterion** — no longer «nobody
> has attached», but «nobody has touched anything». Someone who attaches and stays **watching** no
> longer renews anything: the ceiling feeds on the same five gestures of §7.3 that feed the
> 30-minute clock.
>
> ⭐ **And the decision came from a measurement asked for on purpose**: an abandoned session holds
> memory and almost no processor, and **does not grow** over time. It is not a leak, it is a fixed
> cost — and the user chose to pay it for one hour instead of six. The whole reasoning, with
> the measurement, is in `DECISIONI.md` §4.8.

⭐ **A client that is silent is a client that has detached**, and no connection «holds the slot».
Whoever arrives gets in, with no timeout to wait for: the case «the phone died in a tunnel and
now I cannot get back into my session» disappears. (`DECISIONI.md` §4.4)

⚠ With QUIC the WiFi → LTE switch does **not** count as silence: the connection carries the
change of address with it. The 30 seconds cover only real interruptions.

⛔ **And one thing the web client adds, declared instead of discovered** *(9 Aug 2026,
`STUDI.md` §web §1.2 D)*: a **background tab is frozen by the browser after about five
minutes** `[S]`. A frozen tab is silent, so **it detaches**, and the session stays alive
waiting — which is the right behaviour, but it must be told to the user instead of looking like a defect.
⚠ The documented exemption requires a channel that WebTransport alone does not provide: whoever wanted to
keep the tab alive would have to add **a second network mechanism just for that**, and it is not
done without a measured reason.

⚠ «Input» is what the user sends, not what they watch: whoever spends half an hour watching a video
without touching anything is detached. The cost is small — reattaching is quick.

### 5.4 The lock belongs to REMOTIX, not to the desktop

⛔ **The desktops' screen lockers stay off**, as they were in v1. It is not an inherited oversight: it is
a dependency, and it has a measured reason. Really locking, on GNOME Mutter **revokes** capture
and input `[R]`; on KDE the chain starts that switches off the screen and mounts a dummy output **with a
filter that swallows all input** `[R]`; on XFCE and LXQt the cures would be configuration
lines, and on LXQt the daemon rewrites one of them by itself.

Security is the same: the only road to that desktop goes through RCP, and RCP goes through PAM.
(`DECISIONI.md` §4.3)

⏳ **With a declared expiry**: that reasoning holds **as long as the password is the only
key**. Whoever one day added a stronger authentication must reread this choice,
because then the desktop lock would go back to defending something.

### 5.5 Multi-tenant

Several users can each have their own remote graphical session, independent.

**Default ceiling: 10 sessions**, configurable. ⛔ But the real limit is not a count: it is a
**budget** of pixels per second, and it is set by the encoder. With the same hardware the same ten
sessions are very easy or impossible depending on the quality each one asks for.

⭐ **How many sessions hold depends on the hardware and the scene**, and it is not promised: the measurements of
phase 10 on the hardware of the time are in `fasi/10-multi-tenant-e-il-budget.md` §6.

**When the budget is full we refuse, declaring the reason.** We do not degrade whoever is already
working to let in whoever arrives: it would be a drop not born from a measurement of the line,
that is what I1 forbids. (`DECISIONI.md` §4.6)

> ### ⭐⭐⭐ THE CURRENCY OF THE BUDGET — phase 10, 24 Aug 2026
>
> ⛔ **Phase 10 disproved that the bottleneck was the encoder**: the first to saturate, on that
> hardware, was the engine that **composes** — the compositor's work, not ours — and the cliff fell on
> **how much is being composed**, not on the number of sessions. ⇒ The measurements are in
> `fasi/10-multi-tenant-e-il-budget.md` and `DECISIONI.md` §4.6-nonies; they are historical.
>
> ⇒ ⭐⭐ **That is why the budget can be computed BEFORE accepting**: the currency is the composed
> pixel, and the cost of a session is known from its canvas. ⛔ **But the pixel alone is not
> enough**: we also look at **the delay of whoever is already inside**, with a threshold
> (`BUDGET_RITARDO_AFFANNO_MS`, **22.9 ms**, in `src/budget.h`) tuned on the phase 10 machine.
>
> ### The rule, in full
>
> ```
> holds(inside, new)  ⟺  demand(inside) + cost(new)  ≤  C × tolerance
>                           AND  the delay of whoever is inside stays below the threshold
> ```
>
> **Three knobs**, `src/budget.c`:
>
> | | default | |
> |---|---|---|
> | `--budget-mpixel-s N` | ⛔ **0, that is OFF** | ⭐ because of **I6**: what changes what the user sees is born off |
> | `--tetto-sessioni N` | **10** | and from here descend `MAX_ATTACCATE`, `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI` — ⭐ **the fallback of the `#define`s at 16 is over** |
> | `--riserva F` | **0.5** | how much is kept aside for whoever is already inside |
>
> ⭐ **And `BUDGET_PIENO 0x06` now really leaves** — with the sentence that says *why*, not a mute
> refusal. Until phase 10 it was declared in `src/rcp.h` and in `RCP.md` §8.2 **and no line ever
> sent it**.
>
> ⚠ **The user's verdict on the capacity measured then is `DECISIONI.md` §4.6-septies.**

> ### ⛔ In phase 1 this line is NOT honoured, and it is a declared fallback
>
> *Written here on 11 Aug 2026, finding **R12C.17**: the fallback was declared **only** in a
> comment of `src/main.c`, that is where nobody reads it who is not reading that file — while
> this section promises ten sessions together without a line saying otherwise.*
>
> ### ⭐⭐ AND OF THE TWO FALLBACKS, THE FIRST HAS BEEN CURED — 12 Aug 2026
>
> *`DECISIONI.md` §1.10, measured by the bench `banchi/02-pam-*` and written in
> `fasi/rapporti/PAM-filo-unico.md`.* ⛔ **The PAM check no longer blocks the wire**: it is queried by a
> **helper process** (`src/aiutante.c`), and the `poll` loop goes back to its work while PAM thinks.
>
> ⭐ Whoever is **not** authenticating no longer waits for PAM, and the handshake of whoever arrives does not
> stop; whoever authenticates waits as long as PAM decides, and that was not supposed to change. The before/after measurements
> are in `fasi/rapporti/PAM-filo-unico.md`.
>
> ### ⭐⭐ AND THE SECOND FALLBACK IS OVER — 24 Aug 2026, phase 10
>
> ⛔ *It said: «`src/rcp.c` keeps **16** attached sessions in a table fixed at compile time
> (`MAX_ATTACCATE`), where here the ceiling is ten, configurable».* ⭐ **Now there is only one ceiling,
> `RCP_TETTO_SESSIONI`, it is ten, and it is changed on the fly with `--tetto-sessioni N`.**
>
> ⚠ The hand-made copies were **five**, not one: `MAX_ATTACCATE` (`rcp.c`), `MAX_FIGLI` (`figlio.c`),
> `QUANTI_PRESENTI` (`main.c`), `WT_PALCHI` (`webtransport.c`, it was **8** — that is **a sixth number
> different again**). ⭐ They all descend from the ceiling.
>
> ⛔ **And one was left separate on purpose**: `MAX_IN_VOLO` (`src/aiutante.c`) **is not** the number
> of sessions — it is how many PAM checks are in flight together. ⇒ ⭐ *unifying for symmetry what
> is not the same quantity is a new defect, not a cure.*
> The boundary in full is in `FASI.md` §01-filo-nudo, «What was developed».
>
> ### ⭐ And the two fallbacks have an expiry, decided by the user on 11 Aug 2026
>
> ⛔ *What was decided is not copied here: we refer to where decisions live.*
>
> | | |
> |---|---|
> | **the wire** | ✅ **CURED on 12 Aug 2026** — **`DECISIONI.md` §1.10**, with a **helper process** as decided. ⭐ The measurement that moved the decision was taken by **B8**: the wire stayed still for seconds at every attempt, ⛔ and **it was PAM putting it there**. ⭐ And after the cure whoever is *not* authenticating no longer waits (`banchi/02-pam-fermo.py`, `fasi/rapporti/PAM-filo-unico.md`) |
> | **the ceiling** | **`DECISIONI.md` §1.11** — ⛔ **it stays fixed at 16 until phase 3**, on purpose: above it is written that *«the real limit is not a count, it is a budget of pixels per second»*, so any number today is a placeholder and changing it now means changing it twice. ⚠ **And the price is this line**: for two phases the code says **16** and this section says **ten**, and it is the same form that produced the defect of the five-minute window (R12C.5) |

---

### 5.9 ⭐⭐ THE RUNNING ORDER OF A SESSION, STEP BY STEP

> #### ⛔ Why this running order is HERE, and where it comes from
>
> *It was a document of its own, `SESSIONE.md`, born on 16 Aug 2026 from the user's suggestion:
> «prepara una nota in cui riporti la scaletta punto per punto di cosa deve avvenire per il
> corretto set-up di una sessione». ⭐ It came in here on 16 Aug 2026, in §5, because **it describes
> the product**, not a phase: it says what must be true for a session to exist.*
>
> ⚠ **And the rest of that document did not come here**: it was the measurements of 16 Aug, and they are
> in `FASI.md` §05-la-sessione, where the measurements of that phase live.


> ⛔ **Why this document exists, and why it did not exist before.**
>
> On the morning of **16 Aug 2026** the user tried the same scene five times — connect,
> log out, reconnect — and each time found a different defect: black bands, «broken» desktop,
> no input, the desktop appearing after many seconds. ⛔ Each time we cured **the symptom that
> the log showed**, and went back to trying.
>
> ⭐ They were **almost all the same defect**, seen from different faces: a step of this running order
> that had never been written, and therefore never verified either.
>
> ⇒ *«Prepara una nota in cui riporti la scaletta punto per punto di cosa deve avvenire per il
> corretto set-up di una sessione»* — **the user's suggestion**, and it is the document that would have
> saved that morning.

⚠ **How to read it**: the «if missing» column is the one needed when something goes wrong. Start from the
symptom, find the step, and look at **who** had to do it. ⛔ Never start from the code.

---

### Part A — what must be true BEFORE, and is not done by the product

*It is in `src/provisiona.sh`, and is verified with `sudo bash src/provisiona.sh verifica`.*

| # | what | who | if missing |
|---|---|---|---|
| A1 | the **user exists** and has a password | provisioning | PAM refuses: «wrong user or password» — and the diagnosis points at the password |
| A2 | ⛔ the user is in the groups **`video`** and **`render`** | provisioning | ⚠ **the symptom is «slow», not «broken»**: without a seat the `uaccess` ACLs do not arrive, Mesa falls back to **llvmpipe** and the compositor draws in software: even a command in the terminal answers with a visible delay |
| A3 | `/etc/pam.d/remotix` exists **and calls `pam_systemd`** | provisioning | no logind session ⇒ the compositor **does not start at all** (see B3) |
| A4 | the **polkit** rule (12 actions) and `logind.conf` | provisioning | a remote user can shut down the machine and take it away from everyone (`DECISIONI.md` §4.7) |
| A5 | the **udev** rule for the graphics card | provisioning | the compositor picks the GPU **at random**; the measurements apply to that hardware and not to the product (§4.6-quinquies) |
| A6 | ⛔ **the server does NOT run inside a user session** | whoever starts the service | `pam_systemd`, if the caller is already in a session, **does not create a second one and does not say so**: the children are left without runtime, without bus and without desktop. ⚠ In production it does not happen (system unit); **it happens only in testing**, that is where we study |

> ### ⛔⛔ A6, the trap inside the trap: `setsid` **is not enough**
>
> `[M]` **16 Aug 2026.** The server had been restarted via `ssh`, and
> `riavvia-7700.sh` launched it with `setsid` — put there for another right reason (`sudo` with
> `use_pty` kills whatever remains in its pseudo-terminal).
>
> ⇒ ⚠ **`setsid` detaches from the terminal, not from the logind session.** The process stays in the cgroup
> of the `ssh` session of whoever gave the command, and from there A6 triggers fully: `[M]` `loginctl`
> showed **no** session for `prova`, `/run/user/1001` did not exist, and the log repeated
> *«NON ho il bus di sessione: Could not connect: No such file or directory»*. **Eight bench rounds
> failed out of eight**, and the face of the defect was the usual one: «the desktop does not start».
>
> ⭐ **The cure is to start it where it would be in production**: `systemd-run --unit=…`, that is a transient
> system unit in `system.slice`. ⛔ And **it is verified**, because A6 is silent by
> construction: `riavvia-7700.sh` reads `/proc/PID/cgroup` of the live process and **refuses to give
> the OK** if it finds `user@` or `session-` there.
>
> ⚠ And there was a second lesson in the same file: ⛔ **the script that starts the product was not
> in the repository** — it lived only on the test machine. Its traps were written only inside
> itself, no review ever read them, and the new one cost an hour of diagnosis on a
> defect that *this table had already written*. ⇒ Now it is in `src/riavvia-7700.sh`.

---

### Part B — what the product does, in this order

| # | what | where | if missing / if it goes wrong |
|---|---|---|---|
| B1 | **PAM authenticates** (asynchronous, the helper) | `aiutante.c` | the wire stops for seconds (§1.10) |
| B2 | the **child** is born: groups → gid → uid, and it is verified with the kernel | `figlio.c` | a process running as someone it should not |
| B3 | ⛔⭐ the child **opens the PAM session**: `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `PAM_RHOST`, **no `XDG_SEAT`** | `figlio.c`, step 2-bis | ⛔ Mutter asks `sd_pid_get_session()`, gets **ENXIO** and dies with *«Failed to find any matching session»*. ⚠ **Linger** is not enough: it gives runtime and bus, but puts the processes in a scope of class `manager` |
| B4 | the **`XDG_*`** variables are **read** from `pam_getenvlist`, not invented | `figlio.c` | a *declared* value in place of an *obtained* one: it holds as long as it holds |
| B5 | the client **ATTACHES declaring canvas = window** | `pagina.html` | ⛔ the session is born with the wrong canvas and must be **resized**, and resizing is a race: black bands, «broken» desktop, input in the wrong place |
| B6 | ⛔ the server **tells the stage the canvas** at the instant it grants it | `rcp.c`, after `SESSIONE` | the stage is born at a size nobody asked for, and every frame is thrown away |
| B7 | ⛔ **the previous session must be FINISHED** — the user manager **and** `gnome-session-restart-dbus.service` | `sessione.c` | ⛔ the new session is born inside the one that is dying and **dies with it without writing a line**: `[M]` its log stays at **zero bytes** |
| B8 | the **settings** are written: `Ctrl+Alt+F*` emptied, «Log Out…» on, automatic suspend off, screen locker off | `sessione.c` | logging out has no entry; the machine falls asleep under a live session |
| B9 | the Shell's **drop-in** is written (`--headless --no-x11`, ⛔ **without `--virtual-monitor`**) | `sessione.c` | with a monitor of its own the session is «healthy» for v1 and **black** for us |
| B10 | `gnome-session` is **started**, and ⛔ **not waited for**: the answer is the frame | `sessione.c` + the retry loop | a child that waits 40 s is a child that does not answer the parent |
| B11 | the child **says «ATTENDI»** until the stage is there, and retries at once | `figlio.c` | the parent **deduces** a failure from the silence and answers `NON_ORA`: from there the two sides never agree again |
| B12 | it mounts the **stage**: `RecordVirtual` → PipeWire → the monitor | `mutter.c`, `cattura.c` | no pixels |
| B13 | it opens the **input channel** (`libei`) on the canvas | `input.c` | the desktop is seen and cannot be controlled |
| B14 | it **inhibits** suspend and idleness (`SUSPEND\|IDLE`, ⛔ never `LOGOUT`) | `sessione.c` | the «Automatic Suspend» notification, and the machine falling asleep |
| B15 | ⭐ **verifies**: the session has no seat, and cannot shut down from here | `figlio.c` + `sentinella.c` | «written is not in force» (E1). ⛔ And it is done by **the child**: root gets the answer «yes» because logind looks at `CAP_SYS_BOOT` before polkit |

---

### Part C — the exit, which is the other half

| # | what | if it goes wrong |
|---|---|---|
| C1 | the **wire dropping** (tab closed, PC off, signal lost) ⇒ the slot is freed, **the session stays alive** (I4) | the work of whoever only wanted to change room is lost |
| C2 | **«Log Out»** — from the menu or with `Ctrl+Alt+Fine` ⇒ the session ends and the programs are closed | — |
| C3 | ⛔ the farewell **`0x10`** leaves **BEFORE** the session dies, and goes to **all** the clients of that user | whoever is watching stays on a frozen screen for thirty seconds and reads «network error» (finding B-7) |
| C4 | ⛔ the child does **not** redo the session after a logout: it waits for a new attach | the desktop the user has just closed **reappears by itself** |
| C5 | the page goes back to the **sign-in form**, and undresses again: away `data-schermo`, away the Pointer Lock, away full screen | a sign-in form inside the desktop's clothes, with the mouse still captured |

---

### Part D — from the symptom to the step

⭐ **It is the table to read first when something goes wrong.**

| the symptom | the step |
|---|---|
| «the desktop does not appear» | B3 · B7 · A6 |
| «it appears after many seconds» | B7 (the failed start is recovered, but after a few seconds) · B10 |
| «black bands on the sides» | B5 · B6 |
| «the desktop is broken» | B5 · B6 (the canvas and the stage do not match) |
| «no input» | B13 · **B6** (the pointer region follows the canvas: if the canvas wobbles, clicks end up elsewhere) |
| «it is slow» | **A2** (llvmpipe) · A5 (wrong card) |
| «the terminal stays frozen until I move the mouse» | the tail of the burst in `cattura.c` (`LEZIONI.md` §6.5) |
| «the machine can be shut down» | A4 · B15 |
| «I was reading and my **screen froze**» · «someone else took my desktop» | ✅ **the silence clock**, `FASI.md` §05-la-sessione §6-bis — fixed on 16 Aug. ⚠ If it comes back, look in the log for *«il margine si sta assottigliando»* |
| «a key stayed pressed after the line dropped» | ⭐ it does not happen: the server releases everything on detachment (`RCP.md` §7.3) — `FASI.md` §05-la-sessione §6 |

---

## 6. The geometry: the canvas and the view

They are two distinct things, and it is the separation that holds up both reattaching from different
devices and the future multi-monitor.

| | Whose it is | How much it changes |
|---|---|---|
| **the canvas** — the size of the desktop, the one the windows see | the **session**'s | it is fixed at every attach, and does not move as long as the client stays |
| **the view** — what of that canvas this client sees, and how large | the **connection**'s | freely |

### 6.1 The model

| Moment | Who decides the size |
|---|---|
| **attach** | the client: the session reads its resolution and uses it. It is 1:1 |
| **during the session** | nobody: if the user resizes the window, **the client rescales the image** |
| **reattach** from another device | the new client, with its resolution |

⭐ The mobile case comes out right by itself: the phone attaches and the canvas is born in the shape of the
phone — real pixels, no bands, no scaling.

### 6.1 ✅ ⭐⭐ IMPLEMENTED on 15 Aug 2026 — and this table now describes the product

*Until that night it was the model we wanted; from then on it is what the code does, measured on the
test machine and judged by the user on two clients («sia su Linux sia su Android è tutto
perfetto»).*

| moment | what really happens | `[M]` |
|---|---|---|
| **attach** | the page sends `ADATTA_TELA` with the size of its own window, and the canvas becomes that | canvas **1264×800** in a 1265×800 window, drawing scale **1.000** |
| **during the session** | ⛔ the client rescales, and the desktop **is never touched** — since 17 Aug 2026 there is not even the switch that did it any more (`DECISIONI.md` §5.1-bis) | ~~hot resizing~~ — measured, and removed all the same: it cost little on Mutter and **could not be done** on KWin ≤ 6.7.4 |
| **reattach from another device** | `SESSIONE` grants **the canvas the stage already has** (§4.5), so the pixels arrive at once, and then the page asks for its own | **0 frames discarded** |

⛔ **And the line «It is 1:1» became true in a narrower sense than it seemed**: not «one
desktop pixel per screen pixel», but **one desktop pixel per window
pixel** — see §6.1-bis, which was corrected that same night.

### 6.1-bis ⛔ «The client's resolution», when the client is a window

*Clarified on 9 Aug 2026. The model of §6.1 said «the session reads the client's
resolution», and with a full-screen program there was nothing else to say. **A browser is a window
inside a screen**, and the two sizes are different — sometimes very.*

| | What it is | Who uses it |
|---|---|---|
| **the canvas** | ⛔ ~~the device's screen~~ → ⭐ **the WINDOW, in physical pixels** — corrected on 15 Aug 2026, see the box below | it is fixed **at attach and at reattach**, with `ADATTA_TELA`, and ⛔ **no longer changes for the whole session** (§5.1-bis, 17 Aug 2026) |
| **the view** | **the window**, that is how much the page really has to draw, always in physical pixels | it is renegotiated at every resize |

> ## ⛔⛔ CORRECTED ON 15 AUG 2026 — the canvas is the WINDOW, not the screen
>
> *This table said: the canvas is **the device's screen**, «not the window», and «it is fixed
> at attach and does not move». ⇒ With that rule canvas and view are **almost always different**, and from
> there come the bands, scale ≠ 1 and the conversion of coordinates.*
>
> ⛔ **It was overturned by `DECISIONI.md` §5.0-sexies**, decided by the user on 14 Aug 2026 after two
> days in which the mouse on DeX stayed unusable: *«abbiamo due tele, quella del server e
> quella del client… se i compositori sanno dare la misura esatta, non servono nemmeno le
> conversioni»*. ⇒ The canvas takes the size of the **window**, and with it **four symptoms** disappear
> together: black bands, interpolated text, reattach at a different size and the four
> seconds between login and desktop.
>
> ⚠ **And the reason this paragraph gave for choosing the screen was not ignored, it was
> paid for**: *«a desktop as large as the window you happened to have open would stay so for
> the whole session — small forever»*. ⛔ It was true **as long as the canvas could not be changed**.
> Now it changes **at every attach and every reattach** — ⚠ *during* the session no, and since 17
> Aug 2026 not even behind a switch (`DECISIONI.md` §5.1-bis). The sentence «small
> forever» no longer describes anything all the same: reattaching was enough.
>
> ⭐ **And the «as soon as you go full screen it goes back to 1:1 and sharp» has become the NORMAL condition**, not
> the reward of full screen: `[M]` scale **1.000** and `image-rendering: pixelated` in any
> window.

⭐ **Why the screen and not the window**, which was the other possible choice: the canvas is **the desktop**,
and a desktop as large as the window you happened to have open at the first connection would stay
so for the whole session — small forever, and soft as soon as you enlarge it (§6.3 already declares
the price). Taking the screen, the small window shows the desktop **shrunk and whole**,
and as soon as you go full screen it goes back to **1:1 and sharp**.

⭐ **And there is a second reason, which comes from the keyboard**: the Keyboard Lock exists **only in full
screen** (§7.3-bis). That is, the way this product is really used *is* full screen — and it is
exactly the condition in which view and canvas coincide and nothing is scaled.

⚠ **What is accepted, declared:**

| | |
|---|---|
| the phone in hand, upright | the canvas is born **tall and narrow**, which is strange as a desktop. It is the emergency fallback (§7.2), and the primary case is DeX with a real screen |
| **rotating the phone** after attach | ⛔ the canvas **does not rotate**: the bands show, and the client rescales by letterboxing (§6.2). ⚠ And it is the **declared** behaviour, not a defect to cure: the switch that made it rotate was removed on 17 Aug 2026 (`DECISIONI.md` §5.1-bis). ⭐ To get the right size back you **reattach** |
| a 4K screen | the canvas is born 4K, and that is **four times the pixels** of 1080p to encode for each session: it weighs on the budget of §5.5, not on capture (`LEZIONI.md` §6.4) |
| ⭐ **the canvas at most 4096×2304** (since 1 Oct 2026, decision of the user: *«4096 max di larghezza va benissimo, non ho mai preteso di più»*) — a 5K, 8K or ultrawide screen | the canvas **is not refused**: the side that exceeds is brought to the maximum and the other stays (5120×2880 → **4096×2304**, 5120×1440 → **4096×1440**), and the page lays it out at scale 1 with bands around (§6.2), like any canvas smaller than the window. ⚠ Why: H.264 on the Intel card stops at **4096 px per side**, and Firefox on Linux receives only H.264 — a wider canvas would have had video only on Chrome. 2304 is 16:9 at 4096 (DCI 4096×2160 fits). The limit is the protocol's, `RCP.md` §4.5; the minimum stays **320×240** |

`[?]` **Three things nobody has measured, which must go into the browser probe**, because all three
change the number the client declares:

1. ⛔ **page zoom skews the count — MEASURED, and the formula above does not hold.**
   ⚠ *This line said* «*It must be measured by how much and on which engines*»: **it is measured**, and the answer is
   *«on one of the two, by 50 %»* — bench **S5**, `[M]` 10 Aug 2026, detail in
   `web/rapporti/S-esiti-sonda.md` §3 and in `DECISIONI.md` §5.0-quater. Corrected on 11 Aug 2026,
   finding **R12C.8**.

   | Engine | zoom 100 % | zoom 150 % | the canvas this formula would give |
   |---|---|---|---|
   | **Chrome 151.0.7922.108** | `screen` 1920×1080, `dpr` 1 | `screen` **1920×1080**, `dpr` 1.5 | ⛔ **2880×1620** |
   | **Firefox 140.13.0esr** | `screen` 1920×1080, `dpr` 1 | `screen` **1280×720**, `dpr` 1.5 | ✅ 1920×1080 |

   ⛔ **On Chrome `screen.width` does not change with page zoom**, so
   `screen.width × devicePixelRatio` gives `resolution × zoom`: a user who pressed `Ctrl +`
   before connecting declares a canvas **50 % larger than the one that exists**, and keeps it
   for the whole session. ⚠ **And it is not fixed with one line**: page zoom is not readable from
   JavaScript in a portable way, and neither of the two measurements alone says which one is the real one.
   ⛔ **Until the formula is revised, what this document prescribes produces a wrong
   number on one engine out of two** — and it must be written here instead of being discovered in phase 2, when
   the symptom will be *«the remote desktop is larger than the screen»*. The measurement on **DeX** is missing (the
   machine was not there): which way a phone gets it wrong nobody knows;
2. **on DeX, does `screen` answer with the external screen or with the phone's?** It is the primary use,
   and the answer decides whether the canvas is born right or as large as a phone;
3. browsers **round** these measurements so as not to let the device be recognised: by how much, and whether
   rounding can produce an **odd** number — which `RCP.md` §4.5 refuses.

**Resizing the client window never touches the desktop**, on any of the four
compositors. The reasons, in order of weight: on KDE 6.3.6 — that is Debian stable — **it cannot be done**
`[M]`; the upstream fix exists but Debian does not update Plasma; and ⛔ **even where it works it does
something worse**, because resizing an output **rearranges the user's windows** `[R]`.
The «right» version messes up the work, the «broken» one leaves it still. (`DECISIONI.md` §5.1)

### 6.2 The proportions

**We letterbox, we do not stretch.** If the window has proportions different from the canvas, the
proportions are kept and bands are added: stretching deforms the text and makes it unreadable.

The case is rare by construction — at attach the proportions **always match** — and remains only
when the window changes size after the attach (it is rescaled, `DECISIONI.md` §5.1-bis) and in the fallback of §6.3. On the phone held upright the band would be
huge: there, zoom with scrolling is needed, which is in the range of gestures (§7.2).

### 6.3 The fallback on KDE, declared

On reattach at a different size on KWin < 6.8 the canvas **cannot** change. The old one is kept
and the client rescales — and it does not cost one more line, because it is the same code as the point
«during the session». **The fallback is declared in the log.**

### 6.4 ~~«Fit the desktop to this window»~~ — ⛔ removed from the product (`DECISIONI.md` §5.1-bis)

~~Real resizing of the canvas is done in the form of **PipeWire negotiation** — a single road
for GNOME, wlroots and KDE ≥ 6.8, which on KDE switches on by itself at the update.~~
⇒ The new size is taken **only by reconnecting** (reattach, F-018). Reconfirmed by the user on
2 Oct 2026, after his manual test.

> ### ⛔ CORRECTED ON 15 AUG 2026 — «never as an automatism» is no longer true, and the reason is a decision of the user
>
> *This paragraph said: «Real resizing of the canvas remains as an **explicit choice
> of the user**, never as an automatism. Where the compositor cannot do it the entry is **off**».*
>
> ⛔ **The first half was overturned by `DECISIONI.md` §5.0-sexies** (14 Aug 2026, decided
> by the user): *«la tela del server si chiede della misura della tela del client»*, and that size
> is asked **at the attach of every session**, without anyone pressing anything. ⇒ At attach it is an
> automatism, and that is the point: without it, the black bands, the interpolated text, the conversion
> of coordinates and the four seconds of waiting between login and desktop come back.
>
> ⛔ **The second half still applies, and since 17 Aug 2026 it applies more sharply**: during the
> live session the canvas **is never touched**, and there is not even the switch to do it any more
> (`DECISIONI.md` §5.1-bis — *«non voglio mettere delle eccezioni nel progetto»*). On KWin ≤ 6.7.4
> resizing an output cannot be done at all, and where it can it rearranges the user's windows.
>
> ⚠ **And «where the compositor cannot do it the entry is off» applies in full**: the server answers
> `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` and the client **MUST** show it off (`RCP.md` §7.1).
> We do not pretend it succeeded.

### 6.5 Multi-monitor

**Out of scope as a feature**, but the implementation stays parametric on N: a canvas larger than
what a single screen shows **already is** the form of multi-monitor — two views on the same
canvas instead of one.

---

## 7. Input

### 7.1 The pointer is drawn by the client

The finger drags a pointer **drawn by the client**. It is not direct touch, where the finger is the
pointer: it is the trackpad, and you see where you are about to click **before** clicking.

Three problems closed together: ⭐ **perceived latency** — the pointer moves at the speed of the
finger, not of the network; **trails and old positions**, which come from the pointer travelling
inside the video; and **precision**, because a finger is ~10 mm wide and targets ~4.

⛔ **Hence an obligation**: the desktop's cursor **must never end up in the captured image**,
otherwise you see two. On GNOME it is already excluded; on KDE and wlroots it ends up there `[M]`, and the cure
is a theme with a 1×1 fully transparent cursor.

⚠ **And it must be verified, not hoped for**: on wlroots a theme that loads **zero** cursors makes the
library fall back to a **built-in and visible** one `[R]`. The outcome is checked after the session
starts. (`DECISIONI.md` §5-bis.1-2)

**In the page**: the pointer is drawn over the video, the browser's is hidden
(`cursor: none`), and the physical mouse comes in through **Pointer Lock** — which is the exact equivalent of
Android's *Pointer Capture* and has the same reason: without it, you would see **two**.

### 7.2 Gestures — for the phone in hand

⚠ **On Android the primary use is Samsung DeX**, with a real mouse and keyboard: there §7.4 applies, and these
gestures are not used. They serve the phone in hand, which is the emergency fallback.

| Gesture | Effect |
|---|---|
| 1 finger drag | moves the pointer |
| 1 finger tap | left click |
| 2 finger tap | right click |
| 2 finger drag | wheel / scroll |
| tap-and-a-half | drag and select |
| 3 finger tap | middle click |
| pinch | enlarges the client's **view** |
| touch on the small **⌨** button at the top right | opens the phone's keyboard; another touch (or «back») closes it |

⭐ **The on-screen keyboard opens only on request** (`DECISIONI.md` §10.28): with the phone in hand it does not
open by itself, because it would cover half the desktop. The small ⌨ button is there **only** in this layout — on the
computer and on DeX with a mouse it does not exist — and it takes nothing away from the desktop: the finger clicks where the pointer is,
not where it lands (§7.1). It is at the top because the open keyboard covers the bottom.

⭐ **It is a declared starting point, not a commitment.** Gestures are judged by using them, not by
reading them: whoever finds this table different six months from now has not found a defect.

### 7.3 The keyboard

**Letters travel as letters; keys that are not letters travel as positions.**

| What | How |
|---|---|
| letters, numbers, symbols | **as letters** |
| Enter, Tab, Esc, arrows, F1-F12, Ctrl, Alt, Shift, Super | **as positions** — they are in the same place on every keyboard |

The reason: a physical keyboard does not send letters, it sends **positions**, and it is the desktop that decides
which letter it is. If positions travelled on the wire, a client with an American keyboard attached
to an Italian session would produce **the wrong letters**. And on Android a keyboard has no
positions at all: it is an input method that produces text.

**On the phone in hand** the same rule applies: what is written with the on-screen keyboard (opened with the
small ⌨ button, §7.2) arrives as **letters**, autocorrections included — the corrected word is rewritten
by deleting what had changed; Enter and Delete arrive as **positions**.

⛔ **With one clarification**: `Ctrl+C` is not text, it is a command. A keystroke travels as a letter
when it **writes text**; when a command modifier is pressed — Ctrl, Alt, Super —
it travels as a position. Shift and AltGr do not count: they serve to *make* the letter.

**The session's layout is renegotiated at every attach and reattach**, like the resolution —
and it serves two things: making characters *reachable*, and making the positions of
shortcuts match (on a German keyboard Z is where Y is for us).

⚠ **What cannot be typed is declared, not faked.** If a character does not exist on
any key of the layout — an emoji, a different alphabet — **nothing** comes out, and the server
writes it in the log: never a different letter, never a silence. (`DECISIONI.md` §5-bis.6-7)

### 7.3-bis The shortcuts the browser keeps for itself — far fewer than it seemed

> ⛔ **Rewritten on the evening of 9 Aug 2026 by measurement S3** (`STUDI.md` §web §5). This section said
> that the Keyboard Lock exists *«only on Chrome and Edge»* and that `F11` and `Ctrl+Shift+I` are lost.
> **It was wrong on three points**, and for the better.

| | |
|---|---|
| **the lever** | ⭐ **it is no longer Chrome's alone**: `keyboardLock` entered the WHATWG standard on **8 May 2026** and Safari 26.4 and Firefox 151 shipped it `[S]`. Chrome and Edge stay on the old form — ⚠ **the page must know both** |
| **how much is lost** | ⭐ **`[M]` 14 Aug 2026 — MEASURED, and it was `[R]`.** On **Chrome 151** the thesis holds: in full screen **with the Keyboard Lock** the browser's reserved ones go from **8 to 0** — exactly `F11` and `Escape` remain. ⛔ **And on Firefox 140 ESR it is FALSE, in a way we would not have guessed: in full screen it gets WORSE** (5 → **7**), and it has **neither of the two forms** of the lock. ⚠ Safari **not tested**, and it stays `[?]`: it is not deduced from the others |
| ⭐ **and in an installed PWA it is empty** | all shortcuts reach the session. ⛔ **But a PWA wants a trusted certificate**: behind the exception of §4.1 the Service Worker does not install `[R]`. **Whoever has a domain does not buy only the absence of the warning: they buy the whole keyboard** (`STUDI.md` §web §1.2 B) |

⛔ **The states are three, not two**, and the second is the worst *(`STUDI.md` §web §8-bis, O8)*:

| | |
|---|---|
| **delivered** | it reaches the remote session, and that is all |
| ⛔ **delivered *and* reserved** | the remote session receives the keystroke **and** the browser runs its command. ⛔⭐ **And the state exists, it is MEASURED and it is WIDE**: `[M]` 14 Aug 2026, **18 combinations out of 42** on Chrome in a window ⇒ *a test that looked only at the session side would have declared them **all green**.* ⭐ **And it is switched off with `preventDefault()`**: 18 → 0 on Chrome, 15 → 0 on Firefox. ⚠ **The example that was here was wrong**: Firefox's `Ctrl+Tab` is **not** in this state — measured, it is in the **third**, and the page does not even see its `keydown` |
| **not delivered** | the browser keeps it |

⚠ **Hence the measurement is not «does it arrive?» but «does it arrive *and nothing else*?»** — a test that looks only at the
session side declares green exactly the worst case.

**What is really lost, and cannot be recovered:**

| | |
|---|---|
| `Ctrl+Alt+Canc` | ⭐ **not from the wire, but from the interface**: the user is given an **on-screen button**. Three mature references out of three do it, and it is **a requirement, not a makeshift fallback** *(O7)* |
| leaving full screen | everywhere, by construction: it is the user's escape route |
| ⛔ **on iPhone, everything** | full screen is **partial in all versions** `[S]`, and without full screen **there is no keyboard lock** *(O9)*. On iPhone the whole keyboard game is lost, not just a few shortcuts |
| ⛔ **on macOS, all system shortcuts** | there is no hook: the function that should provide it **returns `nullptr`** `[R]` |
| ⛔ **on Android and DeX, every combination with Meta** | by AOSP rule — ⚠ and DeX is the primary use (`DECISIONI.md` §5-bis.0) |

⛔ **What is done**: the page **declares** which shortcuts it cannot deliver on that browser.
We do NOT pretend they work, and we do not invent a replacement shortcut without saying so.

⚠ **Two traps of the lock, and the second bites where it hurts most** *(O10)*: it does not exist if
full screen was opened with `F11` — **and it does not say so** — and **it switches off by itself when the page
loses focus**, that is exactly at the instant a modifier stays pressed. ⭐ The cure does not
touch the protocol: **the page releases everything it has pressed when it loses focus**, and on
reattach `RCP.md` §7.3 takes care of it, obliging the server to release everything on detachment.

`[?]` **Two questions remain, and they are the two that weigh most**: whether the Keyboard Lock works on
**DeX**, and whether the PWA also holds on **Chrome for Android**.

### 7.4 Physical mouse and keyboard — on Android it is the main road

The mouse goes through *Pointer Capture*: Android's cursor disappears — otherwise you would see
two — and its movements move **the same pointer the finger moves**. One arrow,
two ways of pushing it. Acceleration is applied by the **client**: applied by both it would
add up.

> ⛔ **Superseded since 14-15 Aug 2026**: pointer capture no longer triggers by itself (it stays
> manual, `REMOTIX.input_classico.aggancia()`), the pointer is **absolute** and every event carries
> its own position (`DECISIONI.md` §5.0-sexies). ⭐ **Since 2 Oct 2026 clicks too** come from
> pointer events (`pointerdown`/`pointerup`), like movements: on Chrome for Android the compatibility `mousedown`s
> are born only after a recognised touch, and a long click or a drag did not
> arrive (the user's manual test; verified with DeX the same day: *«i clic funzionano»*).
>
> ⚠ **Declared limit, not ours:** on Samsungs (DeX included) Chrome **does not deliver movements
> with buttons up** (noVNC #1727, open since 2022, the same on moonlight-android #573, which is
> a native app). ⇒ Pointing, clicking and dragging hit right; **the preview is missing**: the shape
> of the pointer on window edges, buttons that light up, tooltips. Reconfirmed
> by the user with DeX on 2 Oct 2026.

### 7.5 What the input channel carries

| | |
|---|---|
| **absolute** pointer | yes — it is the pointer's only path |
| key **positions** | yes |
| **letters** | yes, and it is the main road |
| multi-finger touch | **reserved slot**, not implemented `[?]` |
| stylus (pressure, tilt) | out |

---

## 8. The network and degradation

### 8.1 The scenarios to serve — and the floor

⭐ **The product's minimum network is 30 Mbit/s**, and it is a **declared floor**: below it, REMOTIX
promises nothing and measures nothing as a requirement. *«Al di sotto di questo limite l'utente
nemmeno riesce a navigare, figuriamoci usare remotix»* — the user, 23 Aug 2026
(`DECISIONI.md` §3.1-bis).

Above the floor the requirement remains **adaptation**, not a second threshold:

| Connection | Bandwidth | Delay and loss | What the server does |
|---|---|---|---|
| good fixed line | **30+ Mbps** | low | aims at the desired |
| ⭐ **the floor** | **30 Mbps** | medium | **spends everything there is**, and holds the minimum |
| ⚠ below the floor | < 30 Mbps | any | **outside what is promised**: degrades and does not disconnect, but it is not a requirement |

⚠ **The ban on disconnecting (§8.3) is not weakened**: it applies below the floor too. What
is no longer there below the floor is the **promise**, not the behaviour.

> ⛔ **THE NUMBER WAS 20, AND IT BECAME 30 on the night of 23 Aug 2026** (`DECISIONI.md` §3.1-sexies):
> *«ho già detto che il pavimento, per quanto riguarda la banda, è a 30 mbps»*. ⚠ The measurements of
> phase 9 are tuned on 20 and **are not rewritten**: they are in `fasi/09-la-qualita-e-la-degradazione.md`,
> and they are historical.

> ### ⛔⭐⭐ AND BANDWIDTH IS NOT THE QUANTITY THAT DECIDES — `DECISIONI.md` §3.1-ter
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti che
> perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter»* — 23 Aug 2026.
>
> ⛔ And phase 9 showed it: with free bandwidth the worst case held, but **the keyframe spiral
> started at the first lost packet**, long before the drop the user **sees**
> (`fasi/09-la-qualita-e-la-degradazione.md`). ⇒ **The bandwidth floor is a premise, not a
> biting requirement**: the biting requirement is the behaviour on a **dirty** line.
>
> ⛔ And a line that loses **in bursts** is declared dead (§3.1-quater): 10 s without packets, or
> heavy loss within 1-2 s. ⚠ It does not contradict §8.3 — it does not disconnect *instead of degrading*: it
> declares broken a wire that **no longer carries anything**, and the user gets back in by hand.

### 8.2 The adaptation rule — invariant I1

> **The rate never drops out of caution, to save, or because the scene is still. It drops only when
> the measurement shows that the line does not carry, and every drop is declared in the log.**

The cautious heuristic is forbidden, measured adaptation is mandatory. Saving bandwidth **is not
a goal of this product**: unspent bandwidth is no use to anyone, and lost
quality shows.

### 8.3 Below the minimum

**Frames are dropped. Never blur the image, never disconnect.**

On a desktop degrading in time is better than degrading in space: at a few frames per
second each one stays sharp and the text can be read — it is slow but you can work. Blurring, the text
becomes unreadable. And at a low rate more bits can be spent on each frame.

⭐ It is the user who decides when to close the client; the session stays and resumes when the
line improves.

### 8.4 QUIC

Besides encryption, two things the transport gives for free and that must be exploited: the **continuous
measurement** of how much the line carries, which in v1 had to be derived by hand; and **connection
migration**, which keeps the session alive when the phone moves from WiFi to the mobile network.

---

## 9. The clipboard

**Text only, both ways.** You copy on the remote desktop and paste on the device in hand, and
vice versa — and it is the second direction that is used most.

No images, no files, no rich formats: text covers almost all uses, costs
a few bytes and has no negotiation, while images open the question of formats and above all
of **who pays for the bandwidth** when an 8 MB screenshot is copied over a link we are
struggling to keep at the minimum. (`DECISIONI.md` §5-ter)

**On the browser side the clipboard is not ours**, which touches exactly the most-used direction —
but less than was feared *(measurement S3, 9 Aug 2026, `STUDI.md` §web §5.3)*:

| | |
|---|---|
| ⭐ **it can be watched, on Chrome** | the `clipboardchange` event arrived with **Chrome 144**, on 13 Jan 2026 — and the motivation written in the proposal is **remote desktop clients** `[S]`. It carries only the MIME types, and wants focus |
| ⛔ **on Firefox and Safari no** | verified, not deduced. There every read costs the «Paste» menu, with a one-second wait |

⚠ And a trap that **all three** references read defuse by hand: the race between `Ctrl+V`
and reading the clipboard. Xpra solves it by delaying **every keystroke by 100 ms** `[R]` — ⛔ for us
that is **twice the delay ceiling**: that cure is not copied, it is replaced.

The rule stays the usual one: **what cannot be done is declared**, we do not pretend.

⚠ **On all three stacks the clipboard belongs to the compositor**, and it is there even without
us. On GNOME the remote session does not own it: it owns only **the door** to reach it
(`EnableClipboard`). *Corrected on 9 Aug 2026 by `STUDI.md` §gnome §10 `[R]`; this line said the
opposite, and it is the same correction as `DECISIONI.md` §5-ter.3 and `LEZIONI.md` §3 question 14.*

---

## 10. Audio

| | |
|---|---|
| **output** | **Opus**, with **PCM** as an always-available base |
| **microphone** | from the client to the session — **not urgent**, and it can slip |
| source and destination | **PipeWire** |

⚠ Invariant I5: **the volume belongs to the session.** Whoever connects finds the level at
maximum; a slider left low does not survive reconnection.

⚠ And a trap measured by v1: an audio node applies the volume **downstream of the monitor
tap**, so whoever captures the monitor receives the signal at full scale whatever the
slider says, **mute included**. The property that moves the tap exists but is off by default.

### 10.1 ⛔⭐⭐ When the window narrows, **audio goes ahead of video** — *24 Aug 2026*

⚠ **This line comes late**: the decision was taken **in the code** from the start (`wt_scrivi()`) and
**was written nowhere** — not here, not in `RCP.md` §6.3, not in `DECISIONI.md`, not in
`CODER.md`. It was found while looking for the cause of audio refused on a bad network
(`fasi/09` §20.2-quater), and it is precisely the kind of thing a measurement phase exists to
discover: **a product policy that no document declared.**

> ⛔ **In every write pass the datagrams go into the packet BEFORE the video bytes**, and on
> a window of two or three packets *«before»* means **«instead»**.

⭐ **The reason is that the two loads do not degrade in the same way:**

- a late block of **audio** **is of no use to anyone any more** — §6.3: no retransmission,
  no reordering, and whoever listens has a 250 ms cushion and then **a gap you can hear**;
- a late frame **is still a frame**: streams are reliable, and its bytes
  leave in the next pass.

⚠ **The price, declared**: it is bandwidth taken from video **exactly when there is little of it**. ⭐ And it is limited
**by construction**: the datagram queue is **eight** long, so at most eight packets go
ahead.

*(The decision is written in full, discarded alternative included, in the box of `wt_scrivi()`.)*

---

## 11. The desktops and the system

### 11.1 Wayland, and X11 applications

**Wayland sessions only.** Applications written for X11 remain supported **via XWayland**.
X11 desktops as a session type are out of scope.

### 11.2 The supported desktops, in order

| | Status |
|---|---|
| **GNOME** | served in v1 `[M]` |
| **KDE Plasma** | served in v1 `[M]` |
| **XFCE** (labwc) | studied, not yet served — ⛔ **and it is not the same case as LXQt**, see below |
| **LXQt** (labwc) | studied, not yet served |

> ### ⛔ «XFCE (labwc)» and «LXQt (labwc)» are **not** the same row — corrected on 14 Aug 2026
>
> The two entries above have the same compositor in brackets, and from that day on they were
> read as **a single case**. `[R]` **They are not**, and the difference bites exactly where
> the made-to-measure canvas is needed (`DECISIONI.md` §5.0-sexies):
>
> | | |
> |---|---|
> | **XFCE** | it has `xfsettingsd`, **first client of the session**, which rewrites all the outputs and **by default switches off every new output** (`displays-wayland.c:526-529`). ⚠ The risk **is not the size** — the made-to-measure mode survives its re-applications — it is `enabled = FALSE` |
> | **LXQt** | **has nothing similar**: `lxqt-config-monitor` goes through KScreen, dies with `exit(1)`, and the udev watcher is inside an `if (isX11)` branch |
>
> ⚠ `[R]`, **not `[M]`**: neither XFCE nor LXQt is installed on our machines. The measurement that
> closes the question is whether `xfsettingsd` really switches the output off for us, and whether an output present
> **before** it starts counts as «new» — if it does not count, the cure is the start-up order.
| **Cinnamon** | 📖 **studied on 9 Aug, last in line** — see [`STUDI.md` §cinnamon](STUDI.md#cinnamon) |

⛔ **On Cinnamon three things do not exist upstream**: `RecordVirtual`, libei, and **the clipboard** — neither
GNOME's road nor wlroots'. Feasibility depends on a single measurement, and the decision
«in or out» is taken on that, not on the study. (`DECISIONI.md` §7.13)

### 11.3 The system around

| | |
|---|---|
| **init** | systemd |
| **distributions** | capability detection and declared degradation; **Debian and Ubuntu** as reference |
| ⛔ **shutdown, restart, suspend, hibernate** | ⭐ **taken away from everyone** — *decided by the user on 15 Aug 2026, `DECISIONI.md` §4.7*. ⛔ **Not only from the remote session**: not even from whoever is physically in front of the machine, because shutting down is the only gesture that takes away **all** sessions together and whoever does it does not see who is connected. ⭐ **Inside the remote desktop the user has a single gesture that ends something: logging out** (§5.2-bis); what they do on **their own** PC is their business, and for us it is the wire dropping. ⚠ It stays possible for **root**, and it must stay so: the machine must be administered, and the attached clients learn about it with `SERVER_IN_CHIUSURA` (`RCP.md` §8.2 `0x0C`) |
| **GPU** | chosen by **PCI id** with a udev rule. ⚠ Denying the node denies it to **the user's whole session**: whoever uses the other card for something else must be put in the rule's group |

### 11.4 Hardware acceleration

**Encoding goes through the graphics card, via VA-API** — `libva` used directly, without layers
in between: REMOTIX sets the parameters, manages the buffers and writes the stream headers itself.
The ladder:

1. **on the graphics card**, with `libva`: **H.264** and **HEVC** — the only route. On zero-copy the
   **colour conversion** too is done on the card (VA-API VPP); on the «from memory» road the
   colours are converted on the processor and the planes go up to the card, where they are encoded
2. ⛔ **No encoding on the processor** — *decision of the user, 1 Oct 2026* (`DECISIONI.md`
   §10.27): *«niente cpu senza scheda»*. The software fallback (OpenH264, SVT-AV1) is **out** of the
   product, the packages and the installer. Without a card able to encode:
   - the **server** declares it at start-up in the log (*«QUESTO SERVER NON SA CODIFICARE VIDEO»*,
     with the reason for each codec) and `ECCOMI` offers no codecs: every `CIAO` ends in
     `NIENTE_IN_COMUNE`, with the reason;
   - `remotix --prova-codifica` exits with **3** (*no card can encode*), distinct from 0
     (the card encodes), 1 (it opens but the frame does not come out) and 2 (usage error);
   - the **installer** already refuses in the preliminary check, with the reason: **RX-GPU-003**
     no card · **RX-GPU-004** only NVIDIA with the proprietary driver **without its Vulkan
     driver** (the `nvidia` ICD: with that one the Vulkan Video route takes it) · **RX-GPU-005**
     no Intel, AMD or NVIDIA card (virtio, VMware, nouveau) · **RX-GPU-006** a card that on
     this distribution encodes neither in VA-API nor in Vulkan and has no driver to add
     (today AMD on Alma: RHEL's Mesa is built without H.264, in VA-API and in RADV). The Vulkan
     driver of the AMD card, where the distribution's one encodes (Debian, Ubuntu, Arch), is
     installed by the installer (on Arch it is only an optional package). A card that encodes with the driver of a third-party
     repository stays a warning with consent (D5). ⚠ The preliminary check does not open the card: it reads the
     VA drivers and the Vulkan ICDs on disk; the real test is `--prova-codifica` after installation
3. ⛔ **No GPL dependencies**: all the server's libraries are permissive (MIT, BSD, Apache),
   a condition of the licence (`DECISIONI.md` §10.22)

⭐ The **Vulkan Video** route (AMD, NVIDIA) is phase 19 (`fasi/19-nvidia.md`), ✅ grafted in on
1 Oct 2026: it is chosen by capability when each encoder opens (`h264_scheda`/`hevc_scheda`,
`src/codificatore.c`), Vulkan first and VA-API where Vulkan is not there; `--codifica vulkan|vaapi` forces it
for tests, and `--prova-codifica` says which one encoded (`strada`). `[M]` 1 Oct 2026 on the server:
Intel UHD 770 → `vaapi` (H.264 and HEVC), Radeon RX 6800 → `vulkan` (H.264 and HEVC).

⚠ On the reference hardware **neither of the two cards encodes AV1** `[M]` 9 Aug: the desired
at 10 bit goes through **HEVC Main10**, which both encode in hardware.

⚠ **AV1 in hardware is not on the ladder** *(`STUDI.md` §web §8-bis, O2)*: in decoding it brings
nothing HEVC does not already give, and whoever wanted to add it must measure both sides. ⛔ And since
phase 19 AV1 is not there even in software: it went out with the fallback.

⛔ **We encode in BT.709, and HDR is not promised** `[S]` *(O3)*: BT.2020/PQ drops the
zero-copy path in the browser, and the one-copy path converts with a washed-out result. It is a choice of the
**server**, not of the client, and it must be written here so that nobody takes it for an oversight.

⚠ **And two parameters the server must emit and that nobody guesses** *(O12)*: the
level string for the target is **5.1**, not 5.0, and above 40 Mbit/s the **High tier** is needed. A level
declared too low does not give an error: **it makes the decoder refuse the configuration**, and
the symptom is «the browser does not open the stream».

⛔ **And the parenthesis «RDNA2 and Alder Lake only decode it» was half wrong**, corrected
the same day with `vainfo` on the two nodes: the Radeon RX 6800 decodes AV1 (`AV1Profile0`,
`VLD`), **the Intel UHD 730 exposes no AV1 profile — not even in decoding**. The detail
of the two cards' capabilities is in `DECISIONI.md` §4.6.

### 11.4-bis Where the card encodes: distributions, cards, repositories

*Decisions of the user of 1 Oct 2026 (`DECISIONI.md` §10.27): encoding is **always** on the card; the
drivers with the codecs, when a distribution removes them because of patents, are asked of the administrator (D5): *«il
problema delle licenze è di chi installa remotix, non del progetto»*. REMOTIX does not distribute codecs.*

| distribution | Intel | AMD | NVIDIA (proprietary driver) | desktops |
|---|---|---|---|---|
| Debian 13 | ✅ official repositories | ✅ official repositories | ⚠ Vulkan Video, not tested | all 4 |
| Ubuntu 26.04 | ✅ official repositories (universe) | ✅ official repositories | ⚠ Vulkan Video, not tested | all 4 |
| Fedora 44 | ✅ with **RPM Fusion** (nonfree) | ✅ with **RPM Fusion** (`mesa-va-drivers-freeworld`) | ⚠ Vulkan Video, not tested | all 4 |
| Red Hat / Alma / Rocky 10 | ✅ with **RPM Fusion EL** + **EPEL** | ⛔ **not supported**: no repository puts AMD encoding back | ⚠ Vulkan Video, not tested | ⛔ **GNOME and KDE only** |
| openSUSE Leap 16, Tumbleweed | ✅ official repositories | ✅ with **Packman** | ⚠ Vulkan Video, not tested | all 4 |
| Arch | ✅ official repositories | ✅ official repositories | ⚠ Vulkan Video, not tested | all 4 |

- The Red Hat family is tested on **Alma**, which stands in for it (Red Hat is paid).
- A «no» to the drivers' repository **blocks** the installation (D5): without it, on that machine the card does not encode.
- ⚠ **NVIDIA**: the route is written (Vulkan Video) but nobody has seen it work on a real NVIDIA — the
  lab has none. It stays «not tested» until it is tested (a rented machine or a user with the card).
- Without a capable card: REMOTIX does not install (§11.4). Virtual machines work only with the card
  passed to the machine (passthrough, vGPU).
- The canvas is at most **4096×2304** (§6.1-bis): a larger window receives the reduced canvas.

### 11.5 The browsers served, and why they must be declared

| browser | where | codec | status |
|---|---|---|---|
| Chrome (and the Blink ones: Edge…) | Linux, Windows | HEVC, if the device decodes it; otherwise H.264 | ✅ supported |
| Chrome | **Android** | HEVC or H.264 | ✅ supported (`DECISIONI.md` §7.19) |
| Firefox | Linux | **H.264** (Firefox on Linux does not decode HEVC) | ✅ supported |
| Firefox | Windows | — | never tested: neither supported nor excluded |
| Firefox | **Android** | — | ⛔ **out of the project** (`DECISIONI.md` §7.18) |
| Safari | macOS, iOS | — | never tested |


⭐ **The three-client rule does not lapse with the single client: it changes form** (`LEZIONI.md` §2.1).
A page runs on **three engines written by three teams that do not know us** — Blink (Chrome,
Edge, Samsung Internet), WebKit (Safari), Gecko (Firefox) — and this gives us back a piece
of the external arbiter lost with `mstsc`: when two agree and the third does not, the defect
declares itself.

| | |
|---|---|
| **the technical minimum** | WebTransport **and** WebCodecs. `[S]` Both present on Chrome/Edge, Firefox and Safari 26+ — WebTransport has been Baseline since March 2026 |
| **it is acceptance-tested on** | ⛔ **at least two different engines**, always. A single engine is a single client, that is the case this rule forbids |
| **it is declared** | which browsers are served, and **what is lost on each** — the shortcuts (§7.3-bis), the clipboard (§9), the certificate on Safari (`DECISIONI.md` §1.7) |

⛔ **And how the page is served is a product constraint, not a detail** *(`STUDI.md` §web §8-bis,
O11)*: it must be delivered **cross-origin isolated** — the two headers the browser demands to give
the page full-resolution timers and shared memory. ⚠ It is not a bench tuning:
**it changes how the server serves every resource of the page**, and deciding it later means rewriting the
way the page is packaged.

⚠ **And versions count more than on desktops**: here the floor is not set by Debian, it is set by the
user's device. A phone stuck on an old version of Chrome has no WebCodecs, and
the symptom must be told in one sentence — not «it does not work».

> ### ⏳ At the end of phase 3: the **building blocks** stand on two engines, the **numbers** stand on one
>
> *13 Aug 2026, and it must be written here so that the line «it is acceptance-tested on at least two engines» is not
> taken as satisfied by looking in the wrong place.*
>
> | | |
> |---|---|
> | ✅ **the building blocks** | the decoder's behaviour at a canvas change is `[M]` **on Chrome and on Firefox**, in both directions — 8 cells out of 8, HEVC and AV1 (`RCP.md` §5.2) |
> | ⚠ **the numbers** | the performance measurements of the time were **on Chrome 151 only**. ⛔ Since 30 Sep 2026 they are no longer a verification of the product: *«eliminiamo i test di performance, sono troppo dipendenti dall'hardware»* — the user |

---

## 12. Out of scope

The paragraph that protects the project from creep. Each row is **excluded
deliberately**, not forgotten.

| What | Why |
|---|---|
| **Windows as a server** | it is the lever of §1.1. ⚠ *Corrected on 9 Aug 2026*: this row said «as a server **and as a client**», and the second half lapsed with §1.6 — we do not write a client for Windows, but **whoever has Windows connects from their browser**, and it costs us nothing |
| **applications to install**, on any system | §1: the client is the page. A native application would be a second product to maintain forever, to gain what the browser already gives |
| **X11 desktops** as a session type | X11 applications remain, via XWayland |
| **redirection of disks, printers, serial ports, smart cards** | it does not serve this product's job. ⚠ *10 Oct 2026*: printing becomes an entry for «afterwards», **one technology for every printer** — PDF from the server to the print dialog of the browser of whoever is connected, which prints where their device knows how to print (`MASTERPLAN.md` M6, `DECISIONI.md` §10.41) |
| **file transfer** | likewise — and the text clipboard covers the frequent case |
| **images and files in the clipboard** | §9 |
| **multi-monitor** as a feature | §6.5: groundwork yes, feature no |
| **stylus** with pressure and tilt | §7.5 |
| **native multi-finger touch** | reserved slot in the protocol, not implemented |
| **session recording** to file | never asked for |
| **compatibility with RDP, VNC or SPICE clients** | it is the opposite of §1.1 |

---

## 13. The open questions

What is **not** decided, listed so that it does not get lost. The detail and the status are in
`DECISIONI.md` §7.

| | |
|---|---|
| ✅ **the licence** | ⭐ **no licences: REMOTIX is free of charge** (`DECISIONI.md` §10.33, 10 Oct 2026, which supersedes §10.30). Visible code with the Phonestra-style licence (draft in `LICENSE.md`, to be approved). The constraint of §11.4 remains: no GPL dependencies |
| 📖 **Cinnamon** | studied, to be measured — §11.2 |
| `[?]` **4:4:4** | §3.1 |
| ✅ ~~the form of the limitation of PAM attempts~~ | **closed on 9 Aug** and ⭐ **reopened and closed again by the user on the 10th**: it is not a rate limit, it is a **ban** — three attempts, twelve hours (§4.2, `DECISIONI.md` §1.9) |
| `[?]` **native multi-finger touch** | §7.5 |
| `[?]` **the relative pointer** for applications that capture the pointer | signalled by the server, not by the client |
| `[?]` **does the certificate exception cover WebTransport?** | §4.1 — it is the measurement that decides whether the «one click» default works everywhere or only on Chrome and Firefox |
| `[?]` **how much of the shortcuts is lost**, engine by engine | §7.3-bis |
| `[?]` **the clipboard in the device → session direction** without a user gesture | §9 |
| `[?]` **HEVC Main10 in hardware in the phone's browser** | `[S]` documented since Chrome 108; to be measured on the real device — and with §3 it is no longer a wall, it is something to declare |
| ⏳ **strong security (MFA)** | deferred until the project is complete, by decision of the user — `DECISIONI.md` §1.7 |
| `[?]` **encoding smaller when the window is small** | today the server encodes the **canvas** and the client rescales. Reducing the encoded size too is `DECISIONI.md` §5.0-ter, deliberately outside the model until someone has measured how much it weighs |

---

## 14. The way of working

Development is carried out by two kinds of agents, with the rules written in their documents:

| | |
|---|---|
| [`CODER.md`](CODER.md) | what to build and how — with the three numbers, the invariants and the measurement rules |
| [`REVIEWER.md`](REVIEWER.md) | how **contradictions** are looked for. The verdict is always «this contradicts X», never «this is right» |
| [`LEZIONI.md`](LEZIONI.md) | the shared foundation: how to measure, how to test, how to learn. **It is read before anything else** |
| [`DECISIONI.md`](DECISIONI.md) | what was decided, when, by whom, and with what degree of certainty |

⛔ **And the rule that holds everything together**: when a measurement contradicts this document, it is
updated **at the same moment**, with the date and the mark of the source. A reference that
ages silently is worse than no reference.

---

## 15. The licence

> ⛔ **Abolished on 10 Oct 2026** (`DECISIONI.md` §10.33): no licences, REMOTIX is free of charge. The chapter remains
> as the history of the system that had been decided; **no rule below is in force**.

*Written on **9 Oct 2026**, at the user's request: *«meglio creare un documento dove viene messo nero su
bianco la logica di funzionamento delle licenze; se ci dimentichiamo qualche particolare quel documento diventa
oro»*. ⭐ **This chapter is the reference**: it contains only the rules **in force**. The why, the dates and the
superseded choices are in `DECISIONI.md` §10.30; how it is built, the steps and the hours in
`fasi/21-la-licenza.md` (⚠ the plan must be realigned to this rewrite before approving it); the explanation with diagrams and tables in `licenze/come-funziona.html`. ⛔ If a new
decision changes a rule, it is corrected **here and in the page**, at the same moment. The code does not exist yet: every
line is a product decision.*

*⭐ **Rewritten on the evening of 9 Oct**, after the simplification decided by the user: *«la complessità di un sistema
aumenta la probabilità di introdurre punti di vulnerabilità e di perdita di controllo del processo»*. Removed: the signature
of the installation (`INSTALL_KEY`), the hardware fingerprint (`HW_FINGERPRINT`), the licence number, recovery
with confirmation by email and upgrade with a new key. The comparison with ChatGPT (same evening) confirmed that signature
and fingerprint protected nothing the ticket did not already cover. ⭐ Shortly afterwards, simpler still (user: *«abbiamo
complicato il processo. Il cliente acquista la licenza, inserisce il codice e REMOTIX parte. Installa REMOTIX,
inserisce lo stesso codice e qui si verifica il caso del doppione»*): the confirmation of installations was removed too.
Every installation starts at once; a second one is a duplication, and is chosen as for a clone.*

### 15.0 The elements, in brief — to be read first

⭐ **A licence answers two questions** (the user's observation, 9 Oct: *«il 90% dell'attività si riduce alla
gestione dei cloni/doppioni»*):
- **where**: on which server it runs. First purchase, server change, rebuilt server, clone, backup, lent key
  are all the same question, and have the same answer: the ticket discovers the duplicate, the buyer chooses
  (§15.8);
- **until when**: expiry, renewal, tolerance (§15.6).
Everything else (site, panel, master key, payment) serves to answer these two reliably.

**The system rests on two elements**, and on nothing else on the customer's side; plus **one gesture** by the buyer:

| element | what it is | who creates it | what it is for |
|---|---|---|---|
| **`LICENSE_KEY`** | long random string (≥ 128 bit) with the class prefix (`RXT-…` trial, `RXF-…` full, `RXG-…` gold) | the service | says **which** licence. It is the **only identifier**: it serves every installation |
| **ticket** | **single-use** random token, changes at every hourly check | the service | says **which copy** is the live one: a clone presents an already-consumed ticket and is discovered |
| *the gesture:* **choice of the copy** | in the customer area, when the licence runs on two servers | the buyer | says **which server** keeps the licence. It is the only gesture for all cases: clone, backup, server change, rebuilt server (§15.8, §15.9) |

- ✅ **A single identifier** (user, 9 Oct: *«c'è un dato di troppo … lasciamo solo LICENSE_KEY»*): no separate
  licence number. Outside the customer area (invoices, support, panel, email) the key is shown
  **masked**: class and last 4 letters, `RXF-…-6YRB`. Only the buyer sees it in full, in their area.
- ✅ **A key is never reassigned** to another licence (supersedes «a `LICENSE_KEY` is used once»: the key
  serves every installation, and a second installation with the same key is a duplication).
- ⚠ **Declared**: whoever lends or loses the key gives someone else **at most 7 working days** of use, then the
  licence is blocked for both until the buyer chooses (§15.8); with 3 duplications in 90 days the
  licence goes to the seller. The risk stays with the company that let the key out.
- The key **on the server** serves only until the first ticket: after activation the product **deletes it from
  disk** and goes on with tickets. To reinstall, it is taken from the customer area.
- The seller can **regenerate** a key from the panel, on request: the old one stops being valid, the active copy
  goes on with its tickets. ⛔ No button for the customer: the custody of keys is the company's (user,
  9 Oct: *«non vorrei che REMOTIX debba entrare in aree che non sono di sua competenza»*).

**Who guarantees what**, in the exchange between REMOTIX and the service:

| what | who guarantees it |
|---|---|
| nobody reads the data on the way | **HTTPS**, the normal padlock of the web |
| the copy asking is the live one | the **ticket** |
| which server keeps the licence, if there are two | the **buyer's choice** in the customer area |
| the answer («valid until…») really comes from the service | the **VPS key** (the service signs, REMOTIX verifies) |
| the VPS key is authentic, and can be revoked if stolen | the **master key**, offline on the seller's laptop (§15.11); ⚠ the only irreplaceable one: if it is lost, a new REMOTIX is needed for everyone |
| «renew» and «suspend» really come from the payment | the **payment key** |

- ⚠ **Declared**: a corporate proxy that opens HTTPS could read a ticket in transit. The proxy belongs to
  the customer's company, inside its perimeter like root: it is not a threat REMOTIX defends against.
- ⚠ **Declared**: whoever has root and really wants to get around the check by modifying the program can do it. The system
  keeps honest people honest, handles payments and expiries, and discovers copies made by mistake.

### 15.1 The three types of licence

| type | users | duration | who gets it |
|---|---|---|---|
| **trial** | unlimited | **14 days** | whoever has an account on the site: **one per account** (§15.7) |
| **full** | unlimited | **1 year**; renewal **at the customer's choice** (§15.6) | ⭐ **the only one on sale** |
| **gold** | unlimited | no expiry | ⛔ not on sale: private use of the seller, their machines and test machines (the **4 boxes** and the test server: without it, the benches would stop at the trial) |

- Every licence is valid for **one machine**: a physical server **or** a virtual machine.
- **The program does not count users** for any licence. How many users a machine holds is said by the public
  performance table, not by the licence.
- An **expired full** behaves like an **expired trial**: REMOTIX stops working.
- **Updates** are included as long as the licence is active.
- ⛔ **A single program**: no special version without the check, not even for gold (a binary without
  the check, if it gets out, is the unlocked version for everyone). Gold goes through the **same road** as the customer and is
  **revocable**.
- ✅ **Gold is issued with a dedicated function** of the service, **not from the panel** nor from any «normal» road
  (user, 9 Oct). 🔸 A command on the VPS, only via ssh. ⇒ Whoever breaks into the panel does not create gold. (The «same road» above
  concerns the **program**: a gold, once entered, is checked like the others.)
- Until payment exists, **full licences are created by hand** from the panel.
- ⭐ **Gold is the simple case** (user, 9 Oct: *«i controlli sono ancora più ridotti … ma conserva il limite di
  una licenza per macchina»*):

  | | gold |
  |---|---|
  | expiry, warnings, renewal | **none** |
  | one per machine | **yes**: the hourly check remains, which serves only this and revocation |
  | if the network is missing | **14 days**, like the others (user, 9 Oct) |
  | two active copies | **warning to the seller**, who **disables one of the two** from the panel; the copy kept goes on with its tickets. No choice page, no automatic stop |
  | revocation | by the seller |

- ⭐ **How times are counted**: every period is counted **in exact hours from the moment of the event**, in
  universal time (14 days = 336 hours): no ambiguity of time zones or of «end of day». People are shown it
  in local time. The periods in **calendar days** (Saturdays, Sundays and holidays count): the trial's 14 days,
  the 14 of tolerance, the 30 between one exchange and the next. The periods in **working days** (Monday to Friday,
  the same all over the world, without national holidays): the warnings before expiry (§15.6) and the 7 and 15 days
  of the choice between two copies (§15.8).

### 15.2 The four parts

| part | where | what it does |
|---|---|---|
| **the product** | the customer's server | activates, checks every hour, shows warnings and states in the page, stops when the licence has expired |
| **the licence service** | the seller's VPS (OVH, Debian 13), `https://remotix.nicfio.it/licenze/v1/` | keeps the register, delivers and consumes tickets, discovers duplications, sends emails, hosts the **site** (public showcase and **customer area**, where trial and full are requested and a choice is made between two copies) |
| **the seller's panel** | ✅ a **web page** of the service (user, 9 Oct); the master key stays outside, on the laptop | creates full licences by hand (not gold: it has its own function, §15.1), chooses between two copies of a gold, revokes, regenerates a key on request, unlocks the limits, looks at duplications, **unblocks or deletes** blocked licences |
| **the payment entrance** | the service | «renew» and «suspend» a licence; ⏳ the payment processor has not been chosen |

⛔ **Activation without network does not exist.** The product also gets out through a corporate **proxy**.

### 15.3 Requesting the licence and activating it

1. ✅ **Trial and full are requested only from the site's customer area, after signing in** (user, 9 Oct: *«serve un sito web
   dove il cliente inserisce i dati e ottiene poi per email il codice»*; *«l'acquisto può essere fatto solo dalla
   sezione privata dopo essersi loggati al sito»*; *«facciamola semplice: anche la trial la si chiede dall'area
   privata»*). «Free trial» and «Buy» on the `remotix.nicfio.it` showcase lead to sign-in, then to the
   request. ⇒ A single path; the email is verified before any key; the licence is born already
   in the account, and the move from trial to full starts from there. The `LICENSE_KEY` appears in the area and also arrives by
   email.
2. ✅ **Two roads to get in, and no disposable emails** (user, 9 Oct): the customer area is entered with the
   **link sent to the email** (signing in confirms the address) or with **«Sign in with Google»**; neither of the two
   is mandatory. The service **refuses emails from temporary domains** (mailinator, 10minutemail…) with a
   public list updated every day, and answers *«use your work email»*. ⚠ Declared: it stops most of them,
   not the domains born today.
3. ✅ **The data** (user, 9 Oct): **email** (mandatory), **name** and **company** (optional). Whoever requests a
   trial becomes the **buyer** of that licence: they receive the expiry and duplication emails like the
   full.
4. ✅ **The installation**, as root (user, 9 Oct: *«il cliente acquista la licenza, inserisce il codice e REMOTIX
   parte»*): the installer asks **only for the `LICENSE_KEY`** (no personal data) and, to whoever does not have it, shows
   the site's address. The service answers with a **signed attestation** (type, commercial expiry, end of the
   tolerance, «valid until») and the **first ticket**, and REMOTIX **starts at once**. Then the product deletes the
   key from disk.
5. ✅ **The same key on a second server** starts at once too, and it is a **duplication** (§15.8): the two
   copies work, the buyer chooses which one to keep. That way the server is changed without a minute of downtime.
6. ✅ **Every licence starts from the moment its key enters the first server** (*«la full come la trial parte da
   quando si installa»*). Requesting it and installing days later costs nothing. 🔸 A trial **never activated expires
   after 30 days** (clean-up).
7. 🔸 ⇒ The sign-in page **has no key field**: it shows the state, root puts in the key.
8. ✅ **From trial to full, and to gold** (user, 9 Oct: *«ci dev'essere una funzione di upgrade per passare da trial a
   full»*; *«la scala di upgrade è trial -> full -> gold»*): the full is bought **on the same licence** from the customer
   area; the key stays the same (the class in the service changes, and the prefix shown) and the server
   notices **at the next hourly check**, without commands and without disconnecting anyone. The year of the full starts
   **from the purchase** (whoever buys on the 10th day of the trial does not lose 10 days). You only go up, even skipping a
   step (trial → gold, by the seller); never down; a full brought to gold loses its expiry.
9. The **renewal** of a full changes nothing on the server: you pay from the customer area and the expiry moves (§15.6).
10. 🔸 **The licence command**, as root, for what the installer does not do: `remotix licenza stato` ·
    `attiva <chiave>` (if the network was missing at installation, or to change server) · `controlla` (a check
    right away). It is the same `remotix` program, not the installer.

### 15.4 The check, every 60 minutes

- Every hour the product presents to the service the **ticket** from the last time. The service verifies that it is
  the last one issued for that copy, **consumes** it and delivers a new one together with the attestation.
  ⇒ Two copies of the same installation (a clone, a restored backup) start with the same ticket:
  one goes on, the other arrives with an already-consumed ticket and the **duplication is discovered** (§15.8).
- ⛔ **A fault never makes a false clone**: every request carries its own **random code**, and the product
  writes it to disk **before** sending it. If the answer does not arrive it resends it **identical**, and the service gives
  back **the same answer**. Same ticket with the same code = repetition; same ticket with a different
  code = two copies.
- ⚠ Declared: the ticket discovers copies that go on **each on its own** (clones, backups, VMs switched on
  by mistake). Copies coordinated on purpose by whoever has root stay out of reach of any local check.
- Only the REMOTIX service touches the state of the licence; «check now» goes through it.
- **The clock**: the product remembers the most recent time seen (its own and the service's); if the machine's clock
  goes back, the most recent one applies, so moving it does not lengthen a licence.
- The licence follows the **history of the installation**, not the hardware: whoever **moves the whole server** (the VM to another
  host, the disk to a new machine) and switches off the old one goes on without doing anything, because the licence
  folder travels with the system.

### 15.5 When the service does not answer

- The product keeps working for **14 days from the last successful check**.
- The administrator is warned **at the first failed check**, then **once a day** (log and sign-in
  page), with the days that remain.
- ⛔ No attestation is valid for more than **14 days**, **gold included** (user, 9 Oct): a single value for all.

### 15.6 Expiry, renewal, warnings

- ⭐ **Renewal is chosen by the customer** (user, 9 Oct: *«addebitare centinaia o migliaia di euro automaticamente
  sui conti degli acquirenti non è così simpatico … il cliente sceglie il rinnovo automatico o meno»*):
  - **manual, and it is the default**: the customer pays from the customer area; the service moves the expiry forward and
    the server notices at the next hourly check. ✅ No new key (user, 9 Oct, after the question
    «wouldn't a new code be better?»: a new key at every renewal adds no security, removes automatic
    renewal and blocks whoever forgets to enter it);
  - **automatic, only if the customer turns it on**: the charge is made by the payment processor, which calls
    «renew»; **email to the buyer 7 days before the charge** with the amount, and automatic renewal can be
    turned off at any moment;
  - ✅ **an expired and not renewed licence is blocked after 14 calendar days** (user, 9 Oct), trial included.
- ⭐ **Trial and full behave in the same way; only the duration changes** (user, 9 Oct: *«ho unificato il
  comportamento di trial e full: di fatto l'unica differenza è la validità»*). What follows applies to both.
- **The calendar** (the user's process, 9 Oct):

  | when | the buyer | the users |
  |---|---|---|
  | **3rd working day** before expiry | 1 email: the licence is about to expire, invitation to renew (or to buy the full) | a **warning on the desktop** to confirm with «I have read» |
  | **2nd working day** before | 1 email | a warning with «I have read» |
  | **working day** before | **2 emails** | a warning with «I have read» |
  | **expiry → 14 calendar days** (tolerance) | 1 email a day at 11 | the **«licence expired» warning page** with the time left before the block; **over the desktop, work goes on** |
  | **after the 14 days** | — | REMOTIX stops (below) |

  - the time of the emails: **at 11**, and the second of the last day **at 16**, the buyer's local time
    (time zone of their server or of their country);
  - everything stops **as soon as the customer renews**; whoever has automatic renewal receives only the notice of the charge;
  - ⛔ no warnings to the administrator 7 days before, nor 3 messages a day: one warning a day.
- **«The end»** is the moment REMOTIX really stops: **14 calendar days after expiry** (trial and
  full), or after the last successful check if the network is missing.
- **At the end**:
  - ⭐ **only REMOTIX** stops; ⛔ **never** access to the server (ssh, local login, the system's PAM stay intact);
  - the **connections** are closed, the **desktops stay alive** with the work inside;
  - on reconnecting the licence window appears;
  - after renewal everyone gets back in and finds their desktop as it was.

### 15.7 The trial

- **14 days, unlimited users**, requested from the customer area (§15.3).
- ✅ **One trial per account** (9 Oct: with the work email verified and disposable emails refused; supersedes
  «one per machine», which rested on the hardware fingerprint, removed). ⚠ Declared: whoever creates new accounts with
  other work emails can get more trials; but they must rebuild the server every 14 days, and that is accepted.
- ✅ **The 14 days start from installation** (user, 9 Oct), that is from when the key enters the first server, at the exact hour.
- Reinstalling during the trial lengthens nothing: the licence is the same, and so is the end date.
- **Two active copies**: like the full (§15.8).

### 15.8 Two active copies (trial and full): the customer chooses

*It applies to **all** extra copies, born by themselves (a clone, a backup put back up, a VM switched on twice) or
wanted (the same server reinstalled elsewhere, a new server, §15.9): the gesture is always the choice.*

1. **The duplication** is discovered at the hourly check (§15.4), so within an hour.
2. Each copy receives a **short name** («copy A · 4F7K»), also shown on its sign-in page.
3. The service **immediately sends an email to the buyer** (and a warning to the seller): *«the licence RXF-…-6YRB runs on
   two servers: choose which one to keep»*, with the link to the customer area. ⛔ No technical data in the email.
4. The **customer area** shows for each copy: short name, **machine name**, **public IP** (with provider and
   country), time of discovery and of last contact. The choice is **confirmed with a button**.
5. **1 email a day for the 7 working days** after the discovery (user, 9 Oct). Meanwhile the two copies
   work.
6. **Choice made**: the copy kept goes on with its tickets, the other stops (its desktops stay alive until
   shutdown).
7. **No choice within the 7 working days**: **the licence is blocked**, **both copies** stop and the
   users see the **«system blocked»** page. The choice, made at any moment, **unblocks** the chosen copy.
8. ✅ **After 15 working days** without a choice the licence **stays blocked** and goes to the seller, who decides whether to
   **unblock it** or **delete it permanently** (user, 9 Oct: *«lasciamo le licenze bloccate; poi sarò io a
   decidere se una licenza bloccata si sblocca o viene cancellata»*). ⛔ No automatic deletion.
9. **One exchange every 30 days** (choices and server changes together); the seller can unlock it by hand.
   **3 duplications in 90 days** on the same licence ⇒ the licence goes to the seller, who looks and decides whether to revoke it.
10. Changing a disk, a network card or the memory does **not** create a duplication: the ticket decides, not the hardware.

### 15.9 Changing server

| situation | what the customer does | what happens |
|---|---|---|
| **the whole server moves** (VM to another host, disk copied to a new machine) | nothing | the licence folder travels with the system; the old one is switched off and work goes on (§15.4) |
| **new server installed from scratch**, with the old one alive or dead | root gives the `LICENSE_KEY` to the installer (or `remotix licenza attiva <chiave>`) and then chooses the new one in the customer area | the new one starts at once; if the old one is alive it is a duplication (§15.8): both work until the buyer chooses the new one, then the old one stops. **No minute of downtime** during the move |
| **clone or backup put back up** by mistake | chooses which one to keep | §15.8 |

- ✅ (user, 9 Oct: *«invece di complicare le cose … dopo 1 ora il sistema rileva l'anomalia e si procede come nel
  caso del clone»*) ⛔ It supersedes the recovery with «Recover» and confirmation by email, the voluntary move with the signature
  of the release and the 72-hour rule.
- If the new server does not work, until the choice is made the old one still works; afterwards, you **choose the old one again** (reinstalling the key if it had stopped); it counts as an exchange (§15.8 point 9), and
  the seller can unlock the limit.
- The **copy left behind** (a backup put back up, the copy not chosen) is not lengthened: it works until its
  «valid until» and shows the administrator a **neutral** message (*«this installation appears to be an older
  copy, perhaps a restored backup»*).
- ⛔ Who must choose, and how the company organises itself when the buyer is not there, **is not REMOTIX's matter**
  (user, 9 Oct: *«un'azienda che si affida a un singolo è un'azienda mal gestita … non vorrei che REMOTIX debba
  entrare in aree che non sono di sua competenza»*). No delegations, roles, confirmations or provisional activations.

### 15.10 The sign-in page

| state | before the credentials | after the right user and password |
|---|---|---|
| **trial** | «Trial version — N days left» | you get in |
| **valid licence** | nothing | you get in |
| **expired** (after the 14 days of tolerance) | nothing (whoever has no account does not discover the state) | the licence window: state, «Buy», and that the administrator puts in the key (`remotix licenza`) |
| **blocked for two copies** (§15.8) | nothing | the **«system blocked»** page and the pointer to the choice email |
| **suspended** (by the payment) or **revoked** (by the seller) | nothing | the licence window, **like an expired one**, with the sentence explaining the suspension or revocation |
| **never activated** (first start without network) | nothing | *«the server has not yet been able to activate the licence: Internet access is needed»* |

In addition, when needed: the warning of the days that remain, the short name of the copy, the message of the copy
left behind.

### 15.11 The seller's keys, and the network

- An **offline master key** (never on the VPS) authorises the **VPS key**, which signs **only the attestations**.
- Service addresses, valid keys and revocations are in a **list signed by the master key**. The product
  has **two starting addresses** inside it. ⇒ A stolen VPS key is revoked without recompiling the product;
  a **new domain** does not oblige customers to update.
- HTTPS with the system's certificates, **no pinning** (corporate proxies must work); the authenticity
  of the answers is given by the service's signature, in a **fixed, signed binary format**.
- The service: transactional operations, **encrypted copies off the VPS every day**, log of every operation
  (who, when, what). If the VPS goes back to an old backup, it catches up **only** with proofs signed
  by itself, never with numbers declared by the customer.
- **Emails** leave from the VPS (Postfix outgoing only, SPF/DKIM/DMARC). ⚠ Condition: OVH must leave
  port 25 open and allow the reverse name; otherwise a relay is needed (decision of the user).
- ✅ VPS and domain have no backup provider (user, 9 Oct): OVH warns of expiries, the cost is small,
  and an OVH fault is solved well within the 14 days of §15.5.

### 15.12 Privacy

- **What reaches the service**: the ticket, the **machine name** and the **public IP** it connects from.
  Nothing else: no hardware, no internal IPs, no fingerprints. The service keeps **only the last** of each
  item, except for duplications.
- **How long they are kept** (ceilings, not minimums):

  | data | for how long |
  |---|---|
  | buyer's email, licences, register of operations | **2 years** from the end of the relationship |
  | data of a duplication (machine names, public IPs) | **6 months** from the choice, then only «duplication of day X, resolved like this» |

- The data of a copy can be seen in the customer area **even when the copy belongs to someone else**: it is done to prevent fraud
  and must be written in the **privacy notice**, to be checked by a lawyer before selling.

### 15.13 What is NOT there

- ⛔ activation without network · counting users · installation signature · hardware fingerprint · TPM ·
  cloud integrations (AWS, Google, Azure) · automatic deletion of a licence · blocking access to the
  server · delegations, roles or provisional activations for the buyer · confirmation of installations or copies
  waiting · regeneration of the key by the customer.
- ⏳ **Suspended**: the payment processor and the **sales contract** of the full (they are decided together).
  When the processor is chosen, the service will have to recognise repeated notices (a renewal sent twice
  does not add two years) and handle refunds and chargebacks.
- ⚠ **The trial contract**: §10.30 indicated the PolyForm Free Trial 1.0.0, which provides **32 days**; the trial
  now lasts **14**. To be decided together with the contract of the full.

### 15.14 The two black boxes: what goes in and what comes out

✅ (user, 9 Oct: *«immaginiamo il cliente e il server di gestione delle licenze come 2 blackbox: dalle 2 scatole
nere entrano ed escono dati, quello che succede dentro ogni scatola resta nascosto nella scatola»*). ⇒ **The contract
between REMOTIX and the service is all here.** Each of the two boxes is built, tested and changed inside without
touching the other, as long as these messages stay the same; a new message or a new field is decided **here** before
the code. Everything travels over HTTPS; the service's answers are **signed** with the VPS key.

| # | from REMOTIX to the service | from the service to REMOTIX | when |
|---|---|---|---|
| 1 | **ATTIVA**: `LICENSE_KEY`, machine name | signed **ATTESTATO** + first ticket (and, if the licence already runs elsewhere, the short name of the copy: it is a duplication) · or **RIFIUTATA** with the reason (unknown or revoked key) | at installation, or with `remotix licenza attiva` |
| 2 | **CONTROLLO**: ticket, request code, machine name | signed **ATTESTATO** (type, state, expiry, end of tolerance, «valid until», warnings to show) + new ticket · or **FERMATI** (copy replaced or not chosen) · **SDOPPIATA** (ticket already consumed) | every hour, and with `remotix licenza controlla` |
| 3 | asks for the **list** | **ELENCO** signed by the master key: service addresses, valid VPS keys, revocations | at start-up and once a day |

- **Inside REMOTIX**, hidden: where it keeps the ticket, how it shows the warnings, how it closes the connections. Only what
  is in the left column comes out.
- **Inside the service**, hidden: the register, the customer area, the panel, the payment, the emails. Only the
  answers of the right column reach REMOTIX. People (buyer, seller) and the payment processor
  enter the service through **its own** doors (site, panel, payment entrance), which REMOTIX does not see.
- ⛔ No other data leaves REMOTIX: no hardware, no internal IPs, no users or sessions.
