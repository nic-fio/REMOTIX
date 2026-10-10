# PIANO — the phases, in order, and how they close

*Opened on 9 Aug 2026, after `SPECIFICHE.md` and `RCP.md` and before any line of code.*

---

## 0. How this plan is made

**A phase is a single thing that can be shown.** If at the end of a phase there is nothing the user can
look at and judge, the phase is badly divided.

Every phase has four things, and the third is the one usually forgotten:

| | |
|---|---|
| **what it produces** | in one line |
| **what the user sees** | and judges — it is the closing criterion, not the document |
| **the bench** | ⛔ **written before developing**, not after |
| **the document** | `fasi/NN-nome.md`, **opened when the phase opens** — and at closing it becomes a chapter of [`FASI.md`](FASI.md) |

### 0.1 The rule that holds up the rest

> ⛔ **The phase document is opened at the start and filled along the way. It is not written at the
> end.**

A document written afterwards is a **report**, and in a report the measurements are *remembered* instead of
being *recorded*. It is `LEZIONI.md` §9 point 8: one updates at the same moment, with the date and the
source.

> #### ⭐ And where that document lives — *changed on 16 Aug 2026, by the user's decision*
>
> ⚠ *The rule above **is not touched**. Only the place where the document lives changes.*
>
> | | |
> |---|---|
> | **the phase in progress** | has its own file, `fasi/NN-nome.md`, opened on the day the phase opens ⇒ one always works on a small file |
> | **the closed phase** | becomes a **chapter of `FASI.md`**, folded in at closing |
>
> ⇒ The project keeps **ten documents with the phase closed and eleven while working**, and one never edits
> a seven-thousand-line file in the middle of a phase.
>
> ⛔ **And what this does NOT loosen**: the chapter is not written at closing, a document that already existed is
> **moved**. A chapter that appeared in `FASI.md` without ever having existed
> as a file would have violated §0.1 — and **it would show**, because its measurements would not have the time
> next to them.

⭐ And it has a side effect that is worth something on its own: **if you cannot write the bench at the start, you have not
yet understood the phase.** A phase that cannot say how it will be measured is not ready to open.

### 0.2 The model of the phase document

```markdown
# Phase N — <title>
Opened on <date> · Closed on <date>

## What it must produce
One line. And: what the user sees and judges at the end.

## The bench                      ← written BEFORE developing
How it is measured, with which scene, which number we expect.
And the positive control: how do I know this bench can see the defect?

## What was developed
Files, lines, what they are for.

## The measurements               ← filled in along the way
| what | expected | measured | date |
The scene declared next to every number.

## ⛔ What did NOT work
The dead ends, with the reason. Even the embarrassing ones.

## The decisions produced
Links to DECISIONI.md §x.y — **not copies**.

## What remains [?]
What the phase leaves open, declared instead of forgotten.

## The user's judgement
The real sentence, with the date.
```

### 0.3 The four rules of the plan

1. ⛔ **Decisions live in `DECISIONI.md`, only once.** The phase document **refers**,
   it does not copy. Eleven decision registers are eleven places to look, and sooner or later two
   contradict each other.
2. ⛔ **«What did not work» is filled in even when it looks bad.** The most
   useful chapter of v1 — the seven dead ends of `LEZIONI.md` §8 — exists only because the failures
   had been written down. A documented dead end costs less than one rediscovered.
3. ⛔ **A phase closes on a measurement judged by the user**, not on a complete document. It is
   invariant I8.
4. ⛔ **The bench is certified before being believed.** Every phase, before declaring a number,
   proves that its bench can see the defect it is looking for (`LEZIONI.md` §1.2 and §1.9).

### 0.4 The method: agentic development and adversarial review

The work is done by two kinds of agents, with the rules in their documents — [`CODER.md`](CODER.md)
and [`REVIEWER.md`](REVIEWER.md). Here is **when** they step in within a phase, which is the part those
documents do not say.

#### The reviewer is one of the three substitutes for the referee we lost

⭐ It is the reason why review weighs more here than in a normal project. In v1 the referee was
**mstsc**: when we misunderstood the specification, someone else's client protested — for free, at once,
without anybody having to notice. By throwing away RDP that signal disappeared, and **two programs
written by the same hand that agree with each other confirm nothing**.

The three things that replace it, and none is enough on its own:

| | |
|---|---|
| **`RCP.md`** | the **written** referee: it says who is wrong, but only if someone consults it |
| **the wire validator** | the **mechanical** referee: it sees non-compliant bytes, but only those |
| **adversarial review** | the referee **that reasons**: it is the only one that can notice that server and client share the **same** misunderstanding |

#### The three moments when the reviewer steps in

⛔ **Not just one, and the first is not on the product.**

| When | On what | Why there |
|---|---|---|
| **1. as soon as the bench exists**, before writing the product | the **bench** | `REVIEWER.md` §1: *the bench is the first defendant*. A defect in the product is found by a good bench; a defect in the bench is found by nothing, and it poisons every later measurement **because it gives confidence** |
| **2. when the code is there**, before measuring it | the **product** | measuring code that already contradicts a written rule is time spent learning something already known |
| **3. before closing** | the **phase document** | that every number has its declared scene, that the failures are there, that the `[?]` have not been silently promoted to facts |

#### The adversarial posture, in concrete terms

It is not a tone: it is four practices.

1. ⛔ **The reviewer receives the code and the specification, not the reasoning of whoever wrote it.** An
   explanation of why it is right **anchors** the reader, and turns the search for contradictions
   into a check of consistency with the explanation.
2. ⛔ **One tries to break, not to confirm.** For every invariant the change touches, the
   reviewer builds **the concrete input** that would violate it. If he cannot build it, he
   declares it — that is information too.
3. ⛔ **A finding is closed with a measurement, not with a discussion.** `[R]` is corrected; `[?]` is
   **measured**, and the measurement belongs to the coder, on the iron. The reviewer does not measure and does not rewrite.
4. ⛔ **A green review is not an approval.** It is «I found nothing», and it must be declared with
   those words. The verdict always has the form *«this contradicts X»*, never *«this is right»*.

⚠ **And the separation of trades must be defended in both directions**: the coder does not ask the reviewer
to measure in his place, and does not rewrite the code on a `[?]` without first measuring it.

---

## 1. A single track

*Rewritten on 9 Aug 2026: `DECISIONI.md` §1.6 removes the dedicated clients, and with them track B.*

⛔ **The plan had two tracks because there were two clients.** Now the client is **a web page**,
served by the server, and the five Android phases — A1-A5 — **no longer exist**: what they carried
has become work inside the phases of the single track, and it is written below so that nobody
loses it.

```
  server + web page
  0 ─ 1 ─ 2 ─ 3 ─ 4 ─ 5 ─ 6 ─ 7 ─ 8 ─ 9 ─ 10 ─ 11 ─ 12 ─ 13
      │
      ├─ BROWSER probe  ⭐ before everything, and it decides the shape of the rest
      └─ test client, written from the SPECIFICATION
```

### 1.1 ⛔ The test client is now worth double

*Written on 9 Aug 2026 when Android was moved to the end, and still true when Android
disappeared altogether — for a stronger reason.*

The second client served one thing only: noticing that **server and client share the same
misunderstanding** (`DECISIONI.md` §0.4). Before there were two and the defence was weak; now **there is only one**,
and without a second reader the protocol would be validated by **a single** implementation, written
by the same hand that wrote the server.

| | |
|---|---|
| **the test client** | a few hundred lines, **in a language different from the server and the page**, written by reading `RCP.md` and **never** the code. Added at **phase 1**, it grows with the phases |
| why the validator is not enough | the validator says «this byte is not compliant»; the test client says **«you two have agreed on something the specification does not say»** |
| ⭐ **and a defence that comes for free** | the page runs on **three engines** written by three teams that do not know us. When two agree and the third does not, that defect **declares itself** — it is the piece of referee we had lost with `mstsc` (`DECISIONI.md` §1.6) |

### 1.2 ⭐ The browser probe — before everything, because it decides the shape of the rest

*It replaces the Android probe, and changes nature: that one answered a single question, this one
four, and three of them change what gets written.*

⛔ **It must be done before choosing the QUIC library and before writing the wire**, not at phase 2:
`DECISIONI.md` §6.4 depends on its outcome, because the server must carry HTTP/3 and WebTransport.

| # | The question | What it decides |
|---|---|---|
| **S1** | ⛔ does the exception the user grants on the **page**'s certificate (TCP) **also cover the WebTransport session** (UDP)? | whether the default «one click» works everywhere, or whether `serverCertificateHashes` is needed — and then **on iPhone only the real certificate remains** (`DECISIONI.md` §1.7) |
| **S2** | does the browser of the **real phone** decode **HEVC Main10 in hardware**? | `[S]` documented since Chrome 108, never measured by us. ⚠ **It is no longer a wall** but a thing to declare (`DECISIONI.md` §2.7) |
| **S3** | how many **shortcuts** are lost, engine by engine — and the clipboard in the device → session direction? | what the page must **declare switched off**, and which browsers it is advisable to recommend (`SPECIFICHE.md` §7.3-bis, §9) |
| **S4** | how much painting costs in **delay**: from the decoded frame to the pixel on the screen | it is half of the 50 ms ceiling, and it depends on the road chosen for the GPU |

> ### ⛔ Corrected on the night of 9 Aug 2026 — findings **R3.4** and **R4.3**, and the order was circular
>
> This paragraph says *«before choosing the QUIC library and before writing the wire»*, and
> `STUDI.md` §web §7 adds *«none requires a line of product»*. **Three of the measurements do not stand
> up without a WebTransport server**, that is without the library being chosen:
>
> | | |
> |---|---|
> | **S1** | the positive control is *«the connection with the published fingerprint **must succeed**»* |
> | ⛔ **S4** | it wants a server that **sends encoded frames** and a decoder that accepts them: it is not «without product», it is **phase 3** — and it even demands **a line of protocol** (`RCP.md` **§7.5** — `BANCO_MARCA` `0x000F` and `BANCO_ESITO` `0x0010`). ⚠ *This line pointed to `RCP.md` §12, where the entry is **struck through**: it was closed on the night of 9 Aug and made normative in §7.5, and whoever followed the reference found a deleted entry. Corrected on 12 Aug 2026, found by **F2.4**.* |
> | the **datagram** measurement | it wants a receiver |
>
> ⭐ **The honest order**: first the measurements that do not touch the wire — the duration of the exception, the
> decoding, the keyboard, the declared canvas, the sign of the wheel — then **the library
> bench**, which produces a minimal fifty-line server, and **on top of that** the certificate and
> the datagram. ⚠ And if the candidate changes, **those two are redone**: a positive control taken on
> an engine different from the product's is form **E10**.
>
> The complete account, with the devices each one demands, is in `FASI.md` §01-filo-nudo.

⛔ **And it is declared successful only with the proof that it really is hardware.** In the browser **the name of the
decoder is not there**: the indirect proof must be built with care — sustained rhythm, CPU
occupation, and the opposite case written first (`LEZIONI.md` §1.11: for every indirect proof one writes
what the opposite would look like, or the proof does not distinguish).

⛔ **On the real device, never on a convenient browser.** «The laptop's Chrome decodes in
hardware» says **nothing** about the phone's Chrome: it is error form **E10** in a new
disguise (`DECISIONI.md` §5-bis.0-ter).

### 1.3 📖 And before the page, a study: XPRA

*Added on 9 Aug 2026, and it is **point 0 of the recipe** of `LEZIONI.md` §9 — «who, in the world,
already does this thing?» — applied to the web client.*

Xpra has an HTML5 client that has been doing this job for years, and the user has used it. One studies **how it
behaves**, not how it is made inside: how it paints, the keyboard in the browser, the clipboard, the
cursor, resizing, delay. ⚠ **Not the transport**: Xpra is on WebSocket, we are on
WebTransport, and that piece is not inherited. Boundary and reason in `DECISIONI.md` §1.6.

> ### ✅ DONE on 14 Aug 2026 — [`STUDI.md` §xpra](STUDI.md#xpra) — ⛔ **and late, with a price paid**
>
> ⛔ *This study should have come **before the page**, and it was done **after**: the user asked for it
> a second time, in front of the product that was finally being used and with a defect in hand
> («il puntatore sembra catturato… studia la soluzione di XPRA»).*
>
> | what it found | |
> |---|---|
> | ⭐⭐ **the cursor is dressed by the browser** (`css("cursor", "url(…) x y, auto")`), and pointer capture is **a button**, not an automatism | ✅ **adopted the same day** — and it dismantled `SPECIFICHE.md` §7.1, which contradicted §7.5 (`SPECIFICHE.md`) |
> | ⭐⭐ **the first frame is ASKED FOR** (`buffer_refresh` with `refresh-now`), not waited for | ⏳ **it is the work on the time for the desktop to appear**: `[M]` most of that time was spent waiting |
> | ⭐ **the client says its size and the server resizes** (`configure_display`) | ✅ **done, but only at one end**: the size is said and taken **at attach and at reattach** (`RCP.md` §4.5, `ADATTA_TELA`). ⛔ *During* the session no — removed on 17 Aug 2026, `DECISIONI.md` §5.1-bis. ⚠ Xpra here does a thing we **decided not to do**, not one we lack |
>
> ⇒ ⚠ **The cost of having skipped point 0 was not the time of the study**: it is the code written
> in the meantime, and the defect found by the user in thirty seconds of use instead of by us.

---

# THE SERVER AND THE PAGE

## Phase 0 — The environment and the benches

**It produces**: the machine that compiles, and v1's benches put back to work.

**The user sees**: v1's numbers **reproduced** — the capture cadence of Mutter and of KWin
measured in v1. It is not a product result: it is the **positive control of the whole project**.
If the bench cannot reproduce a number we know to be true, every future measurement is suspect.

> ⛔ *13 Aug 2026, and it must be read together with the line above: **v1's number does not reproduce**:
> the cadence Mutter delivers depends on the one asked of it, and renegotiating it changes it. It is not
> the bench that is wrong: that number is not a property of the compositor — ⚠ and that it is the remainder of a
> truncated division is `[R]`, read in the code, **not measured** (`STUDI.md` §gnome §8.2; the «law on 13
> points» that could be read here on 13 Aug **fell the same evening**). ⇒ The positive control of
> this phase must be redone **against the clean cells of `banchi/03-b14-esiti.jsonl`**, not against the
> number. The measurements are in `FASI.md` §03-movimento.*

**The bench**: `fondamenta/banchi/banco-compositori/misura-cattura.c` and `banco.sh`, which regenerates the
test scenes by itself.

**Reused**: all of `fondamenta/banchi/` (262 files), `fondamenta/banco/` for provisioning.

⛔ **Step zero, and without it the phase does not start: GNOME is no longer installed on the server**
`[M]` — `dpkg-query` says *not-installed*, there is no `gnome.desktop` (`STUDI.md` §gnome §2). The
positive control of the whole project is reproducing the Mutter cadence measured in v1,
and today it cannot be executed. GNOME is put back **before** believing any number.

⚠ To be done here and not later: install `vainfo` on the test iron and **confirm** the capabilities of the
Intel encoder, which today are `[?]` derived from the chip's generation (`DECISIONI.md` §4.6).

⚠ **And the restore is tested by rebooting**, not by rereading the script: in v1 the first real reboot
showed two missing pieces that no document declared (`LEZIONI.md` §2.5-bis). It holds
now, not only at phase 13 — because it is now that the machine is being put back on its feet.

> ## ⛔ The Android environment lapses — 9 Aug 2026
>
> This phase planned SDK, emulator (AVD), `adb` and the connection to the phone, for the probe
> of phase 2. **With `DECISIONI.md` §1.6 none of this is needed any more**: there is no
> application to build, and the probe is **a web page**.
>
> ⭐ **The real phone stays**, and it is more important than before: it is the measuring instrument for **S2** and
> **S4** (§1.2 *(of this document)*). But one gets there **by opening an address in the browser**, which is the cheapest
> thing this project has ever asked of a test device.
>
> ⚠ *The box on the emulator that follows is kept for history: its conclusion — «no number
> is declared on an emulator» — survives in the form «no number is declared on a browser
> that is not the real device's».*

> ### The emulator covers more than it seems — but not decoding
>
> *Verified on 9 Aug 2026, after a first draft had dismissed it too hastily.*
>
> ⭐ **The Desktop AVD exists**, hardware profile «13.5" Freeform», from Android 11 upwards; the
> Android 13 version added **keyboard shortcuts and mouse support** besides
> drag-resizing and drag-and-drop. And **Samsung itself documents
> the emulator for DeX**: *«If you don't have the DeX Station, you can test your app resize
> behavior in Android Studio using Android Virtual Device»*, at the density and resolution
> equivalent to DeX (160 dpi, 1080×1920).
>
> So **the interaction model can be tested there**: freeform window, real mouse, real
> keyboard, draggable edges. It is a large part of phases **A1** and **A3**.
>
> ⚠ With the warning Samsung gives on the same page: the emulator **simulates, it does not replicate**
> — freeform mode is enabled from the command line and is *«not reflective of actual DeX
> hardware behavior»*.
>
> ⛔ **What the emulator does NOT give, and must be held firm:**
>
> | | |
> |---|---|
> | **hardware decoding** | its MediaCodec is not the phone's silicon. `[?]` It could not be established that it exposes a hardware HEVC decoder; the only evidence found is people who on the emulator **find no 4K HEVC profiles** |
> | the real delay, the battery, the changing network | not reliable |
> | parity with real DeX | approximation, not replica |
>
> > ⛔ **Hence the rule, which stays:** *one develops on the emulator, one measures on the phone.*
> > **No number of this project is declared on an emulator.**
>
> ⚠ It is `REVIEWER.md` **E10** — *a green test on the wrong client*. An emulator that says
> «it works» while the phone does not is a green bench with the defect alive, and it is the form that cost v1
> the most: a correction written on a bench that did not reproduce the defect, shipped
> to the user, **which made things worse**.
>
> **The real phone is the measuring instrument; the emulator is the workbench** — and the
> workbench is wider than the first draft said.

---

## Phase 1 — The bare wire

**It produces**: the RCP handshake over **WebTransport**, on both sides. No video, no
input.

**The user sees**: ⭐ **he opens an address in the browser**, types user and password, and the page says
*«admitted, new session, canvas 1920×1080, GNOME desktop»*. Or it says why not.

⛔ **And before everything else, the browser probe** (§1.2 *(of this document)*): four measurements that decide the shape
of what is written afterwards — starting with **which QUIC library**, which now must carry
HTTP/3 and WebTransport (`DECISIONI.md` §6.4).

⚠ **The server acquires its second trade here**: serving the page. Two listeners with the
same port number — **TCP** for the first load, **UDP** for HTTP/3 and WebTransport — and
the `Alt-Svc` announcement that ties them. ⛔ Forgetting it gives no error: it gives **a page that opens and a
desktop that never arrives** (`RCP.md` §2.4).

**The bench**:
- ⛔ **the handshake on TWO connections, never one**: in v1 a shared certificate killed the
  server **at the second**, and a single-connection test stays green forever
  (`LEZIONI.md` §2.1);
- the **wire validator** in its first form: it reads a recording and says which byte is not
  compliant with `RCP.md` §6;
- ⛔ **and the violation tests**: unknown type, wrong length, message in the wrong
  state. The connection **must drop every time**. A bench that does not try to violate the
  protocol does not test the protocol (`RCP.md` §11).

**Positive control of the validator**: it is given a recording **with an error inside** and one
verifies that it sees it. A tool that has never found anything is not clean: it is uncertified.

⭐ **And here the test client is born** (§1.1 *(of this document)*): the handshake written **a second time**, in
a different language, **reading only `RCP.md`**. Whoever writes it does not look at the C or the page — if
he looked at them he would inherit their misunderstandings, and it would no longer serve any purpose. It grows from phase to
phase together with the protocol.

**Reused**: `autenticazione.c` (144 lines, PAM), `registro.c` (140).

⛔ **But `autenticazione.c` must be changed in one point, and it is not a detail**: it rejects anyone who is not
the user owning the process (`autenticazione_utente_atteso()`, from the effective uid). It was
right in v1, where the server ran inside one person's session; **it contradicts the
multi-tenant** of `SPECIFICHE.md` §5.5, where the service is a system one and serves ten different users.
Whoever reuses it without removing that gets a server that works **only for itself** — and the symptom, for
everyone else, is «wrong credentials».

---

## Phase 2 — The first frame

**It produces**: capture from a real GNOME session → encoding → wire → **`VideoDecoder`** → the page's
canvas. A still image.

**The user sees**: ⭐ **his own desktop, inside a browser tab**. Still, but his — and from
any device, which is the thing that phase 2 of v1 did not have.

**The bench**: the decoded frame compared with the captured one. Not «the program did not
crash»: **the pixels**.

**Reused**: `cattura.c` (1060 lines), `mutter.c` (353), `superficie.c` (675), `immagine.c` (273),
`codificatore.c` (889, to be brought back to HEVC), `palco.c` for the mounting part.

> ### ⛔ A question that phase 1 found and that bites HERE — `[M]` 10 Aug 2026
>
> *Found by probe S7, after three rounds that came to nothing, by the check that says «the page does not see
> even the pointer move». Brought here on 11 Aug 2026 instead of being rediscovered by a
> user (`web/rapporti/S-esiti-sonda.md` §8, entry **S.4**).*
>
> ⛔ **In a GNOME session without physical input devices, if the client starts BEFORE the
> virtual pointer of `libei` exists, it receives nothing** — no wheel, no buttons, **not even the
> pointer's movement**. If it starts **after**, it receives everything. `[M]`, and it is **the order** that is
> measured.
>
> ⚠ **And it is not that the injection does not arrive**: Mutter receives it in both cases —
> `org.gnome.Mutter.IdleMonitor.GetIdletime` drops from **35 952 ms to 1 013 ms** at the first movement.
> ⛔ **The compositor takes it and does not deliver it to the window.**
>
> `[?]` **The cause is not verified**: the plausible explanation — a session without devices
> announces a `wl_seat` **without a pointer**, and the client started earlier never subscribes — has not
> been tested. What is `[M]` is the order.
>
> ⛔ **Why it concerns the product, and concerns this phase and phase 6**: in the product the graphical session
> is born **without any input device**, and the applications opened **before** a client
> connects could find themselves in the same state — the user moves the mouse and that window does not
> respond. ⇒ **The bench of this phase opens the application AFTER creating the devices**, or
> it measures a scene the product will never have.

⚠ Here encoding is **software**, on purpose: acceleration comes later, and putting it first
would mean not knowing which of the two pieces is wrong. ⭐ *And indeed it came later, but **before**
the phase that promised it: hardware encoding entered the product on **13 Aug 2026**,
with phase 3 in progress, so as to be able to measure the before and the after with the same bench. Phase 8 is no longer
called «the acceleration»: it is called **«zero copy»**, and it is what is left of it.*

⛔ **And here the GNOME session is born, which v1 started without ever having studied it** — the traps are
in `STUDI.md` §gnome §3 and they all hold at the first start, not later: `SHELL` must be set **empty**, or
`gnome-session` re-executes itself inside a login shell and pulls in `~/.profile` `[R]`;
~~`--virtual-monitor WxH` **is not optional**, because in headless mode the session otherwise starts
**alive, complete and black**~~; the drop-in for the Shell unit is written in
`src/sessione.c` · `scrivi_dropin()`.
> ⛔⛔ **REVERSED on 14 Aug 2026, phase 4 · A1** *(realigned to the code on the 28th)*. Today the
> product **does NOT ask for** `--virtual-monitor`, and indeed **refuses** an `ExecStart` that still asks
> for it: if it finds one, it writes to the log *«c'è un drop-in che vince sul mio»* and returns `FALSE`.
> ⭐ The reason is measured (`[M]` 14 Aug, bench `04-b20`): with the monitor requested, `RecordVirtual`
> mounted a **second** one and recorded that — GNOME left bar, dock and windows on the first,
> and **the user was looking at an empty screen**. Without it, `RecordVirtual` mounts **the only** monitor and the
> shell goes on it.

⭐ And a test to do **deliberately broken** (M9 of `STUDI.md` §gnome §13): without `--virtual-monitor`,
to learn what the fault looks like. A black and perfectly alive session is the thing that gets
mistaken for a capture defect, and one searches for half a day in the wrong direction.

⛔ **And here the browser probe comes back, for real instead of as a test** (§1.2 *(of this document)*): the first real
frame given to `VideoDecoder` **on the phone**, to know whether it decodes it in hardware and whether it
really returns **10 bits**.

| | |
|---|---|
| 1 | does it decode **HEVC Main10 in hardware**? `[S]` Chrome documents it since 108; in the browser **the decoder's name is not there**, so the proof is indirect and must be built with the opposite case written first (`LEZIONI.md` §1.11) |
| 2 | ⛔ **and does it really return 10 bits?** `[?]` mpv's documentation reports that on the `mediacodec` path 10-bit support is **limited and the output goes back to 8 bits** — it is the first indication against what `SPECIFICHE.md` §3.1 wants, and it comes from the side where we have no margin (`DECISIONI.md` §2.3-bis) |

⚠ **What changes if the answer were no**, and it changed on 9 Aug: **it is no longer a wall**. The
maximum is offered by the server, the height is set by the client (`DECISIONI.md` §2.7): a device that
decodes in software is a fact to **measure and declare**, not a defect of ours. ⛔ But
declared **it must be declared**: a silent fallback stays forbidden even when the fault is
someone else's.

---

> # 📅 HOW IT WAS ON **20 Aug 2026** — *«the hunt is closed, and now it is implemented»*
>
> ⚠ **One does not restart from here**: the project's entry point is the **⏸** box at the top of `README.md`.
>
> *The hunt for artefacts closed on the evening of **17 Aug** with the user's judgement —
> **«NIENTE ARTEFATTI!»** — on a bench. ⛔ **In the product the cure is not there yet**, and until it
> is there the user sees what he saw before.*
>
> ## What was learned, in three lines
>
> | | |
> |---|---|
> | ⛔ **the fault was not ours** | the pixels **enter the canvas correct** and break **on their way to the screen**: `getImageData` reads the store, not the screen ⇒ every bench that reads back the canvas was green **by construction** |
> | ⭐ **the cure is measured** | `createImageBitmap()` + `transferFromImageBitmap()` on a **`bitmaprenderer`** context — `DECISIONI.md` §5.4, proofs in `fasi/06-la-tela-e-la-vista.md` §4.9 |
> | ⛔ **and AV1 leaves the product** | Firefox for **Android** has neither HEVC nor AV1 ⇒ **H.264**, `avc1.640032` already verified — `DECISIONI.md` §1.13-ter |
>
> ⛔ **The eight dead hypotheses are not redone**: the seven of the previous box (broken AV1 stream ·
> alignment 962→968 · wrong size at the page · decoder errors · the page's drawing
> path · depth 10/8 · xrdp+RemoteFX) ⛔ **plus the `VideoDecoder`**, cleared
> by `copyTo` against the truth. Each has its measurement in `fasi/06-la-tela-e-la-vista.md` §4.9.
>
> ## ⭐ THE WORK TO COME, in this order
>
> **1. ⭐⭐ The cure inside `src/pagina.html`** — ⭐ **DONE on 20 Aug 2026**, and it is in service
> on **7730**: `dipinti == consegnati`, `tard 0`, `err 0`, sharp canvas at 1:1 with the Marionette
> witness (`fasi/06-la-tela-e-la-vista.md` §4.9). ⏳ **It waits for the user's judgement**, which is the only thing that
> can close it: no bench sees this defect. ⚠ And it remains `[?]` **how much
> `createImageBitmap` costs** — the account to beat is that of the `drawImage` it replaces.
>
> *What was done, for whoever rereads:* it is what the user **sees**, and it had to come before everything.
> The **two** 2D canvases disappear (`deposito_p.drawImage(f)` and `pennello.drawImage(deposito)`); the
> visible canvas becomes `bitmaprenderer`; the store **is no longer needed** because
> `transferFromImageBitmap` sizes the canvas by itself and the content survives
> resizing; centring is done **with CSS**. ⚠ And **the cost is measured**:
> `createImageBitmap` is asynchronous and enters the delay.
> ⛔ **The judge is the user, on his scene** — no bench can see this defect (I8).
>
> **2. H.264 in the product** — `RCP.md` §4.3/§6.2 (the third codec number **is added**),
> `codificatore.c` (H.264 on the card and the NAL reader that recognises the **IDR**), `figlio.c`, and in
> `pagina.html` the preference ladder and the probe's test stream. ⚠ With inside it the `[?]`
> of the hardware decoder's **colour range**: +8 levels on the light areas.
>
> **3. ⚠ And phase 6 remains open**: its `fasi/06-la-tela-e-la-vista.md` §8 still waits for the judgement on two scenes — the
> edge drag and the click held down.
>
> ## ⚙ The state of the machine — verified on 20 Aug 2026
>
> | | |
> |---|---|
> | **where one works** | the `git` repository is on the **CHUWI** (`192.168.0.3`), which is also the machine from which the user **looks** |
> | **where it runs** | `NIC-OS`, **192.168.0.2**: `remotix-7700.service` and `remotix-7730.service` **both alive**, and the machine **has not rebooted** |
> | ⛔ **the repository has uncommitted work** | `figlio.c` (the **on-command snapshot**, `SIGUSR1`), `pagina.html` (the `MARCA` line that says **who is speaking**), and the benches `07-b48`/`b49`/`b50` |
> | it is switched back on with | `ALBERO=/media/REMOTIX/src/07-appunti-src LAV=/media/REMOTIX/tmp/07-appunti bash banchi/07-b41-accendi.sh --porta 7730 --hz 0` |
> | ⛔ the ports in use | 7448 · 7700 · 7710 · 7720 · **7730** |
> | ⚠ the browser caches | **`Ctrl+Shift+R`** is needed after every change of the page |
>
> ## ⛔ And the two defects of ours the hunt left along the way
>
> **`?video=worker` does not paint on Firefox**, and the cause is in hand: the streams transferred to the worker
> are never read, so they are not closed, and the **1024** unidirectional streams
> of credit run out («il client ne concede ancora 0 … il delta che veniva dopo il 1023»). ⛔ And
> `postMessage` **does not throw**: the premise of the comment in `pagina.html` is false, so the
> fallback never triggers. ⇒ The cure is a **check**: if within N ms the worker has not read the
> first byte, it is declared and one falls back.
>
> ⚠ **And the verification on Chrome is still due**: after the depth cure nobody has
> looked at Chrome again.
>
> ---

## Fase 3 — Il movimento ✅ **CHIUSA il 14 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«abbastanza fluido, non il massimo ma pur sempre fluido»*
>
> | | |
> |---|---|
> | **il numero** | l'anello del ritardo misurato con la codifica **in hardware** e con AV1 in software, che è la configurazione **giudicata** — i valori stanno in `FASI.md` §03-movimento |
> | ⭐ **l'architettura** | **ASSOLTA**: togliendo la codifica in hardware cede il tratto della codifica e **gli altri quattro tratti non si muovono** |
> | ⭐ **la codifica in hardware** | **nel prodotto**, non su una copia: la chiave si accorcia di molto, il ritmo **raddoppia** |
> | ⛔ **il tetto** | **SFORA** i 50 ms, e **sforerebbe anche a codifica gratis** |
> | ⛔⛔ **il collo di bottiglia nuovo** | ⚠ ~~**il DISEGNO**~~ ⇒ ⛔ **CORRETTO il 14 agosto 2026** (deciso dall'utente, su due misure indipendenti della fase 4): **il disegno costa poco `[M]`**; quel che si attribuiva al disegno era **l'ATTESA del fotogramma dalla GPU** più il disegno — un fotogramma HEVC in hardware esce opaco e la rilettura della marca del banco ne provoca il trasferimento. `fasi/rapporti/F4-A2-pagina-dipinge.md`, `F4-A10-anello-input.md` |
>
> ⛔ **E i tre limiti del giudizio sono scritti in `FASI.md` §03-movimento, non taciuti**: è su AV1
> in software; HEVC in hardware **non è giudicabile** perché il browser dell'utente non lo dipinge;
> e l'utente **non ha visto un desktop** ma un monitor aggiunto con dentro la scena dei banchi.
>
> ⭐⭐ **E il giudizio ha prodotto due difetti che nessun banco aveva trovato** — HEVC che non
> dipinge nella sessione vera, e il prodotto che **aggiunge** un monitor invece di mostrare il
> desktop. ⇒ *È esattamente il valore che il piano attribuiva al giudizio, e si è realizzato in
> trenta secondi.*

> ### ⭐⭐⭐ LA CODIFICA IN HARDWARE È ANTICIPATA QUI — deciso dall'utente il 13 agosto 2026, sera
>
> *E la fase 3 **non si chiude** finché non è fatta.*
>
> ⛔ **La ragione, e non è un'opinione: è una misura.** La scomposizione dell'anello del ritardo
> misurato il 13 agosto dice che **più di metà** sta nel tratto **cattura → primo byte**, cioè nella
> codifica **in software**; Mutter, il disegno, la decodifica e il filo non cambiano con
> l'accelerazione. I valori stanno in `FASI.md` §03-movimento.
>
> ⇒ **Finché la codifica è in software, ogni numero di ritardo che le fasi 3-7 producono è dominato
> da un pezzo che sta per essere sostituito** — e andrebbe rifatto dopo. È l'obiezione dell'utente,
> ed è giusta: *«senza accelerazione hw stiamo ragionando e sviluppando su numeri non molto
> affidabili»*.
>
> ⭐⭐ **E si può fare, `[M]` verificato il 13 agosto 2026 sul server:**
>
> ```
> Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
> VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
> VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
> ```
>
> ⚠ *Un agente aveva riferito «su questo server non c'è un codificatore hardware per nessuno dei due
> codec». **È vero per AV1** — e stava già nei documenti — **ed è FALSO per HEVC**, che è proprio
> quel che la fase 8 promette. Nessuno l'aveva verificato: la riga è stata ripetuta, non misurata.*
>
> ⭐ **E costa poco farlo adesso**, per una ragione precisa: la catena che si muove **esiste da
> oggi**, il banco dell'anello è scritto, la scena e la marca sono certificate. ⇒ Il *prima* e il
> *dopo* si misurano con **lo stesso strumento e la stessa scena**, quindi i due numeri **si
> sottraggono davvero** — cosa che non sarebbe più vera fra tre fasi.
>
> ⛔ **Che cosa si anticipa, e che cosa NO**: si prende **la sola codifica in hardware**. La **copia
> zero** resta alla fase 8, è lavoro suo e non tocca questo numero.
>
> ⚠ **E la fase 8 non sparisce**: resta con la copia zero, e con la sua lezione che vale anche qui —
> *«si misurano i fotogrammi consegnati, non i millisecondi di CPU»*. In v1 il costo per fotogramma
> scese di molto **mentre i fotogrammi consegnati scendevano** (`LEZIONI.md` §6.2).
>
> ⏳ **Il lavoro comincia in una sessione nuova** (deciso dall'utente). Il punto di ripresa sta nel
> `README.md`.
>
> ---
>
> ### ⭐⭐⭐ 13 agosto, sera — **IL BERSAGLIO È CONFERMATO AI DUE CAPI, e uno scoglio non c'era**
>
> *Il piano della sessione nuova è stato riletto **prima che partisse un agente**, e controllato
> misurando invece che ricordando. Ne sono uscite tre righe che cambiano il lavoro.*
>
> **1. ⛔⛔ La codifica AV1 in hardware NON ESISTE su questa macchina** — `[M]`, 3 giri su 3: la
> prova di codifica esce con *«No usable encoding profile found»*, e `vainfo` dà AV1 in **sola
> decodifica** su tutt'e due i nodi. ⚠ Il codificatore **compariva** nell'elenco della libreria:
> *un elenco dice che il codice c'è, non che la macchina lo sa fare*.
> ⇒ ⭐ **Restare su AV1 vuol dire restare in software per sempre.** HEVC (e poi H.264) non è una
> preferenza: sul lato server è **la strada verso l'hardware**.
>
> **2. ⛔⛔ Lo scoglio «nessun client accetta HEVC» era una BANDIERA del banco**, non un palco.
> `[M]` A/B con una sola variabile: senza `--disable-gpu` il Chrome del banco vede la GPU e dice sì
> a HEVC; con la bandiera dice no. ⭐ E **dipinge davvero** un flusso HEVC codificato sulla scheda: 5 giri su 5,
> 1920×1080, 119 fotogrammi su 120, `powerEfficient: true`.
> ⇒ **La corsia che doveva aprire la sessione è cancellata**, e la strada critica diventa
> *codifica → anello rimisurato*, senza rami che possano bloccarla.
>
> **3. ⭐ I codificatori si confrontano a parità di bitrate e coi fotogrammi in uscita CONTATI** —
> il confronto misurato sta in `FASI.md` §03-movimento. ⚠ Il primo giro di quella sonda **non era un
> confronto e il banco l'ha detto da sé**: a bitrate libero VP9 consegnava **molti meno byte**.
> *«Più veloce» a una frazione del lavoro non è più veloce.*

**Produce**: uno stream per fotogramma, l'abbandono con `RESET_STREAM`, la cadenza.

**L'utente vede**: il desktop **che si muove**, e dice se è fluido.

**Il banco**, ed è il cuore:
- ⛔ **la scena si dichiara e si muove sempre** — un client a schermo intero che ridisegna a ogni
  richiamo del compositore. Tutte le misure di ritmo delle fasi 3-9 di v1 sono state buttate per
  questo (`LEZIONI.md` §1.1);
- **i fotogrammi consegnati all'utente**, non quelli elaborati. Il numero che in v1 nessuno aveva
  mai contato, e che era 18 mentre si ottimizzava altro;
- ⭐ **l'anello del ritardo**: il client manda un input che cambia colore allo schermo e guarda i
  fotogrammi decodificati finché non lo vede. Misurato **dal lato che riceve**
  (`DECISIONI.md` §2.6). ⛔ **E qui arriva anche S4**, la misura del ritardo del *disegno* nel
  browser, che §1.2 metteva nella sonda: senza codifica, trasporto e decodifica non è eseguibile
  *(9 agosto 2026, rilievo **R3.4**)*. I suoi sette controlli e il **pezzo cieco** — il tratto fra
  il disegno e il pixel acceso, che nessuna API vede e che **si dichiara accanto a ogni numero** —
  stanno in `STUDI.md` §web §6.3.

**I numeri da raggiungere**: ritardo ≤ 50 ms, traguardo 40 (`SPECIFICHE.md` §3.2).

> ## ⛔⛔ 13 agosto 2026 — l'esperimento è FATTO, e l'esito non era fra i due previsti
>
> *Qui stava scritto: «su GNOME il traguardo dei 40 ms probabilmente non si raggiunge, per il muro
> della cadenza di Mutter; se la misura lo confermasse non è un difetto nostro — ed è una
> ragione in più per la fase di KDE». E accanto: «prima di dichiararlo si prova la cadenza
> disaccoppiata… se riesce, GNOME entra nel traguardo; se non riesce, il muro diventa `[M]`».*
>
> ⛔ **L'esito non è «riesce» né «non riesce». È: «riesce con un numero diverso, e il prodotto non
> ci arriva» — e intanto il ritardo è stato misurato altrove, e la colpa è nostra.** Le tre metà:
>
> | | |
> |---|---|
> | ⭐ **la cadenza disaccoppiata RIESCE** | `[M]` monitor **120** + freno **90** ⇒ Mutter consegna la cadenza piena — cella **D**, pulita. ⚠ **Ma M3 di `STUDI.md` §gnome §13 NON è chiusa: è mezza**, perché la causa non è misurata |
> | ⛔ **ma la causa scritta era sbagliata, e quella nuova è `[R]`** | non un **battimento** fra due orologi ma una **quantizzazione** — `min_interval_us = 10⁶/maxFramerate` troncato a intero (16666 per 60) contro un tick da 16666,67 µs — ⛔ **letta nel codice, non misurata**. E lo scarto scritto prima **non si riproduce** sulla cella bassa |
> | ⛔⛔ **e il prodotto non ci arriva** | `MOVIMENTO_FPS 60` è una costante di compilazione (`src/figlio.c` · `MOVIMENTO_FPS`), `main.c` non ha opzioni di cadenza, **`RecordVirtual` non prende la frequenza** (`src/mutter.h` · la nota su `RecordVirtual`): i quattro monitor virtuali sono tutti **@60**. È `[M]` **sul banco** e **zero in produzione** |
>
> ⛔ **E il ritardo, che è il numero per cui la fase esisteva, SFORA** il tetto dei 50 ms `[M]`
> (cattura → vetro, pezzo cieco **escluso**; i valori in `FASI.md` §03-movimento). ⛔⛔ **Ma il muro
> non è di Mutter**: la sua parte è piccola, **il grosso è nostro**, e sta nel tratto cattura →
> primo byte, dominato dal **codificatore in software**. ⇒ La cura è la **fase 8**, non la 10
> (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> ⚠ **E il 60 non è il 40 ms**: la cadenza non è il ritardo (`LEZIONI.md` §6.2). I 60 fotogrammi
> tolgono un ostacolo; il numero lo fa il ritardo.
>
> > ⛔⛔ ⚠ *La seconda riga della tavola diceva: «Legge su **13 punti**, 8 confermano, 0
> > smentiscono», e la prima dava **M3 per chiusa**. **Tutt'e due false**, e corrette la sera del
> > 13 agosto 2026 (rilievo del coordinatore della fase 3, verificato sui file di esiti): il file
> > `banchi/03-b14-esiti-griglia.jsonl` porta **due sole celle**, tutt'e due con
> > `scena_sul_mio_monitor: **false**` ⇒ rifiutate dal banco stesso, che stampa «⛔ la legge NON
> > regge su **0 punti su 0**». ⇒ **La cadenza piena rinegoziata resta un fatto `[M]`; il perché torna `[R]`; M3 resta
> > mezza.** ⭐ E la ragione del rifiuto è la trappola n. 1 di `LEZIONI.md` §1.1 — la scena non era
> > sul monitor che si catturava — **tornata a mordere il risultato che la citava**: §1.1-bis.*

---

## Fase 4 — Si comanda ✅ **CHIUSA il 14 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«mi sembra ok»*
>
> *e, sulle due ottimizzazioni che aveva chiesto: «la situazione mi sembra migliorata, la comparsa
> del desktop è più immediata».*
>
> | | |
> |---|---|
> | ⭐⭐ **che cosa vede** | **usa il desktop**: clicca, scrive, scorre, sposta le finestre. REMOTIX ha smesso di essere una dimostrazione |
> | ⭐ **il numero della fase** | l'anello **input → vetro** `[M]`, due giri indipendenti che concordano — i valori in `FASI.md` §04-si-comanda |
> | ⛔ **il tetto** | **SFORA** i 50 ms, anche prima di contare i due pezzi ciechi |
> | ⛔⛔ **e nessun tratto domina** | sei tratti di peso simile ⇒ **nessuna cura singola porta l'anello sotto il tetto**: è lavoro della **fase 8** |
> | ⭐ **il login → desktop** | scende di molto, e quel che resta è quasi tutto **il fisso di `RCP.md` §4.4-bis** |
> | ⭐⭐ **e il ritardo non cresce più** | prima si accumulava secondo dopo secondo (⛔ **con tutti i contatori verdi**); adesso resta fermo |
>
> ⭐⭐ **E il giudizio dell'utente ha trovato SETTE difetti che nessuno dei dieci banchi vedeva** —
> il monitor aggiunto, due server nostri sulla stessa sessione, la barra sul dock di GNOME, la
> cattura del puntatore, il palco fallito tenuto per sempre, ⛔ e **una riga del coordinatore** che
> rallentava il login. **Sette su sette stavano FRA i pezzi, nessuno dentro uno.**
>
> ⛔ **E si chiude con cinque cose dichiarate aperte**, messe davanti all'utente **prima** che
> giudicasse: il ritardo che sfora · la tela che non è la sua (**36 % di banda nera** sul suo 21:9)
> · il monitor chiesto sempre invece di guardare se c'è · un pezzo cieco dentro uno dei tratti
> · e **un browser solo**. Stanno in [`FASI.md` §04-si-comanda](FASI.md#04-si-comanda).


> ### ⭐⭐⭐ IL PRIMO LAVORO DELLA FASE 4 È IL **DESKTOP VERO** — deciso dall'utente il 14 agosto 2026
>
> *E non è una premessa alla fase: **è dentro la fase**, in testa.*
>
> ⛔ **La ragione, in una riga**: la fase 4 esiste perché *«l'utente **usa** il desktop»* — ma
> **finché il desktop non si vede, non c'è niente da comandare**. I banchi del cursore, delle
> lettere accentate e delle scorciatoie non avrebbero **dove guardare**: si misurerebbero su uno
> schermo vuoto.
>
> **Il difetto, e la cura è in DUE posti non uno:**
>
> > ✅ **CURATO il 14 agosto 2026 (A1)** *(riquadro aggiunto il 28 agosto, riallineando al codice)*.
> > ⛔ La tabella qui sotto descrive **com'era prima della cura**, ed è al presente perché è stata
> > scritta come mandato. Oggi il prodotto non chiede `--virtual-monitor` e **rifiuta** un
> > `ExecStart` che lo chieda: `src/sessione.c`, il controllo su `vigore`.
>
> | | |
> |---|---|
> | `src/sessione.c` · l'`ExecStart` della Shell | crea la sessione con `--headless --no-x11 **--virtual-monitor %ux%u**` ⇒ GNOME mette la shell **su quel monitor** |
> | `src/mutter.c` · `RecordVirtual` | cattura con **`RecordVirtual`**, che **ne monta un altro** e registra quello ⇒ **l'utente guarda il secondo, vuoto** |
> | ⛔ **e la seconda metà della cura** | `src/sessione.c` · il controllo sull'`ExecStart` in vigore **rilegge l'`ExecStart` in vigore e PRETENDE `--virtual-monitor %ux%u`** ⇒ tolta la bandiera, il controllo **fallirebbe**. *Il controllo è giusto, l'atteso no* |
>
> ⭐ **La tesi è già PROVATA, il 14 agosto, senza toccare il prodotto**: sessione dell'utente
> `prova` avviata **senza** `--virtual-monitor` (`GetCurrentState` → **0 monitor**, la sessione
> *«viva, completa e nera»* di `STUDI.md` §gnome §3.1); collegato il client, `RecordVirtual` monta
> **l'unico** monitor e ⭐ **la shell ci va sopra: barra, sfondo, dock**. La prova sta in
> `fasi/rapporti/F5-desktop-vero.md` e nell'immagine
> `F3-verbali/desktop-vero-14ago.png` ⚠ *(tolta dal disco come i rapporti; si riprende con `git show dea834d --stat` e `git checkout dea834d -- <percorso>`)*.
>
> ⚠ **Due cose da MISURARE prima di crederle, e non sono dettagli:**
> 1. ⛔ **chi decide la misura del monitor** adesso che non la dà più la sessione: la dà
>    `RecordVirtual`, e **che cosa succede se il client ne chiede un'altra?** È `RCP.md` §4.5, la
>    tela concessa, e da qui in poi tocca questo pezzo;
> 2. ⚠ **`PIANO.md` (questo file, più su) e `STUDI.md` §gnome §108 dicono che `--virtual-monitor` non è
>    opzionale**. ⇒ **Vanno riscritte**: sono vere solo per una sessione che deve vivere **senza
>    nessuno che la catturi**.
>
> ⚠ **E l'utente `prova` si conserva** (deciso il 14 agosto): è l'unico posto dove oggi il desktop
> vero si vede, perché `nicfio` ha già una sessione con un monitor suo e `SPECIFICHE.md` §5.1 ne ammette **una sola
> per utente**.

**Produce**: ⭐ **il desktop vero** (qui sopra) · il canale di input, il puntatore disegnato dalla pagina, le lettere e le posizioni —
⭐ **e le due disposizioni della pagina**, che è il lavoro ereditato dalle fasi A3 e A4 sciolte: il
modo classico con `Pointer Lock`, e il tocco con i sette gesti, **con il passaggio automatico sul
contesto** e non un'impostazione da cercare (`DECISIONI.md` §5-bis.0-bis).

**L'utente vede**: ⭐ **usa il desktop**. È il momento in cui smette di essere una dimostrazione.

⛔ **E qui si scopre che cosa il browser si tiene**: `Ctrl+W`, `Ctrl+T`, `F11`. La pagina **DEVE
dichiarare** quali scorciatoie non può consegnare su quel motore, invece di lasciar credere che
siano arrivate (`SPECIFICHE.md` §7.3-bis). ⚠ La misura è **S3** della sonda, e va fatta su almeno
due motori: quel che si perde su Chrome non è quel che si perde su Safari.

**Il banco**:
- ⛔ **il cursore del desktop non deve comparire nell'immagine**: si guarda un fotogramma. E su
  wlroots si verifica che il tema trasparente sia stato **caricato**, non solo scritto — un tema
  che carica zero cursori fa ripiegare su uno visibile (`SPECIFICHE.md` §7.1);
- una lettera accentata scritta in una sessione con la disposizione giusta, e una in una
  sessione con la disposizione sbagliata: la seconda **deve** finire nel registro come non
  producibile, non uscire diversa;
- `Ctrl+C` che copia invece di scrivere una c.

⛔ **E qui si scopre che il cursore non arriva affatto**, il che rende `CURSORE_FORMA` (`RCP.md`
§7.2) un canale senza sorgente: su Mutter chiediamo `cursor-mode=2` — cioè «dammi il cursore
come metadato» — **ma non chiediamo `SPA_META_Cursor`**, quindi forma, posizione e punto attivo
non vengono consegnati `[R]` (`STUDI.md` §gnome §1.1 punto 6 e §5.2). Da chiedere qui, dove il canale
nasce. ⭐ **Il verso è quello giusto per noi**: pixel puliti nell'immagine *e* la forma in banda
laterale, che è esattamente ciò che serve al puntatore disegnato dal client.

⚠ **Due ricambi silenziosi di libei**, che mordono qui e alla fase 6: un cambio di **keymap**
distrugge e ricrea il dispositivo tastiera, un cambio di **geometria** tutti i dispositivi
assoluti — e il puntatore al dispositivo vecchio smette di funzionare **senza errore** `[R]`
(`STUDI.md` §gnome §9). Keymap e regioni si rileggono a **ogni** `DEVICE_ADDED`, non una volta all'avvio.

**Si riusa**: `input.c` (906 righe, libei), `tastiera.c` (372, xkbcommon).

---

## Fase 5 — La sessione ✅ **CHIUSA il 16 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«funziona»* · *«il task nel terminale era ancora in esecuzione»*
>
> *E la prova che vale l'ha fatta lui, con un lavoro VERO dentro: si logga massimizzato, lancia un
> ciclo infinito nel terminale, chiude il browser, rimpicciolisce la finestra, rientra — e il ciclo
> girava ancora. ⛔ Tutte le prove nostre avevano un desktop **vuoto**, che è il testimone peggiore
> possibile: appena rinato è identico a com'era.*
>
> | | |
> |---|---|
> | ⭐ **l'accesso** | `[M]` su venti giri dal browser, **senza più la coda lunga** che la mattina ogni tanto lo faceva durare molte volte tanto — i valori in `FASI.md` §05-la-sessione |
> | ⭐ **la coda lunga dell'accesso** | trovata: il palco nasceva alla tela di ripiego e il ridimensionamento **non si compie su una scena ferma**. ⇒ il figlio aspetta la tela del cliente |
> | ⭐ **`RCP.md` §7.3, il rilascio al distacco** | provato sul **desktop vero** con un testimone che conta le battute: un tasto rimasto giù si ripete, e il rilascio lo ferma |
> | ⭐ **i tre orologi** | il silenzio contava **l'utente invece del client** (un secondo dispositivo entrava sul desktop di chi stava leggendo: **I2 rotta**) ⇒ riparato sui pacchetti · l'inattività (`0x02`) **non esisteva** ⇒ fatta · le 6 ore diventano **60 minuti**, per decisione dell'utente su una misura di memoria |
> | ⭐ **`0x0F`** | il secondo dispositivo è respinto, provato **da un telefono vero** — mai uscito prima su una connessione vera |
> | ⭐ **la sessione senza nessuno che guarda** | resta viva, costa pochissimo e la memoria non cresce. In v1 `libmutter` andava in asserzione fallita |
> | ⛔ **e tre righe di registro mentivano** | `RILASCIO AL DISTACCO: 0` che non poteva dire altro · il testo `0x02` della pagina che nominava l'orologio sbagliato · *«l'utente ha chiesto di uscire»* detto da un orologio. ⇒ `LEZIONI.md` §1.9 ha la sua **quinta regola** |
> | ⛔ **e il modulo d'accesso stava sotto il desktop** | da sempre: il «vestito da desktop» non nascondeva niente. Trovato dall'utente, in tre segnalazioni |
>
> ⇒ ⭐ **Restano due cose sole**, e l'elenco è stato **tagliato** col criterio dell'utente — *«se i
> punti non toccano il prodotto è solo rumore burocratico»*: `0x05` (l'utente con una sessione
> grafica **locale**, che vuole una persona alla consolle) e il banco del puntatore dopo il ricambio
> dei dispositivi. Dettagli in `FASI.md` §05-la-sessione §7.

**Produce**: PAM per intero, il palco che sopravvive al distacco, i tre orologi, una sola sessione
grafica per utente.

> ### ⭐ E il confine col multi-tenant è stato deciso il 15 agosto 2026 — `DECISIONI.md` §4.6-quater
>
> **Qui: un utente remoto per volta.** Niente budget, niente conteggio, `MAX_ATTACCATE` resta il
> `#define` a 16 dichiarato come ripiego. Il multi-tenant come **funzione** — più sessioni insieme,
> `BUDGET_PIENO`, il tetto configurabile — è della **fase 10**, perché ha bisogno di un numero vero
> e il numero lo dà il codificatore hardware della **fase 8**.
>
> ⛔ **Con un pezzo che non si rinvia**: il guardiano di logind di `0x04`/`0x05` deve discriminare
> **per utente**, e non è una scelta — è la macchina di prova che lo impone. `nicfio` ha la sessione
> grafica **locale** e `prova` arriva da **remoto**: un guardiano che chieda *«c'è una sessione
> locale?»* invece di *«di questo utente?»* rifiuta `prova` **il primo giorno**.
>
> ⭐ **E le quattro decisioni della sera del 15 agosto stanno tutte in `FASI.md` §05-la-sessione**: le
> due uscite (§4.1-ter), il ritorno al modulo di accesso col motivo nuovo `0x10` (§4.1-quater), la
> scorciatoia `Ctrl+Alt+Fine`, senza bottone a schermo (§4.1-quinquies), e ⛔ **nessuno spegne il
> server** (§4.7).

**L'utente vede**: chiude il client, va a pranzo, riapre — **e ritrova tutto com'era**.

**Il banco**:
- distacco e riaggancio, **due volte di fila**: un banco che passa solo da macchina pulita non è un
  banco, è una dimostrazione (`LEZIONI.md` §2.3-ter);
- ⛔ **la sessione senza nessuno che guarda**: in v1 il monitor virtuale spariva al distacco e
  `libmutter` andava in asserzione fallita, con le applicazioni che perdevano la connessione
  Wayland. È il difetto che rende la sessione inutilizzabile dopo il primo stacco;
- i tre orologi, ciascuno con la sua prova;
- l'apertura di una sessione locale mentre la remota è viva → la remota **deve** cadere con
  `SESSIONE_LOCALE_PREVALSA`, e il motivo si verifica **dal lato che lo riceve**;
- ⭐ **e il gemello che mancava**: una sessione locale **già attiva** e una remota che arriva →
  `GIA_ATTIVA_LOCALE` `0x05` (`SPECIFICHE.md` §5.1). *Aggiunto il 9 agosto 2026, rilievo **R4.16**:
  era di `RCP.md` §8.2 e di nessuna fase, e sarebbe caduto fra le fasi;*
- ⛔ **il rilascio dei tasti al distacco**, che `RCP.md` §11 chiama *«la regola col rapporto
  danno/costo più alto del documento»*: si stacca con un tasto premuto **e si riattacca** a
  verificare che non sia rimasto giù. *Portato qui dalla fase 4 il 9 agosto 2026, rilievo **R4.7**:
  alla fase 4 non esiste una sessione a cui riattaccarsi — la sessione muore con la connessione —
  quindi quel banco lì o non si scrive o **si scrive verde per costruzione**.*

⛔ **E due difetti che l'utente incontrerebbe lasciando la sessione ferma venti minuti**, tutt'e
due su GNOME e tutt'e due mai affrontati in v1 (`STUDI.md` §gnome §4 e §7):

| | |
|---|---|
| **la revoca** | il blocca-schermo di GNOME non mostra un blocco: **ci stacca**. Ci salva `is_headless()`, che però **non abbiamo mai chiesto** — Mutter ci si mette da solo quando la sessione logind non ha un seat. Qui l'headless si **dichiara** e si **verifica dopo l'avvio**, e se non c'è si fallisce dichiarandolo (`DECISIONI.md` §4.3-bis, misura M2) |
| **la macchina si addormenta** | `sleep-inactive-ac-type` vale `suspend` a 900 s, upstream **e** Debian `[R]`. Oggi non morde solo per accidente. La cura è una chiamata sola — `SessionManager.Inhibit(…, 12)`, cioè `SUSPEND\|IDLE` **insieme** — e `energia_inibisci()` su Mutter oggi **ritorna NULL** (`src/energia.c:112-113`). ⛔ Mai il bit `LOGOUT` |

⚠ **Il banco dei tre orologi li incrocia**: sei ore di abbandono su una macchina che si sospende
a quindici minuti non si misurano affatto — e il banco resterebbe verde, perché la sessione al
risveglio c'è ancora.

**Si riusa**: `palco.c` (1545 righe — la più preziosa), `sessione.c` (797), `sentinella.c` (307,
logind), `uscita.c` (384), `energia.c` (149), `compositore.c` (229).

---

> ## ⏳⛔ PRIMA DELLA FASE 6: IL PIANO VA RIVISTO — rilievo dell'utente, 16 agosto 2026
>
> Alla chiusura della fase 5, l'utente: *«prima dobbiamo rivedere il piano che ha alcuni punti
> secondo me fuori sequenza»*.
>
> ⇒ ⛔ **La fase 6 non si apre finché quella revisione non è fatta.** ⚠ E il sospetto ha già un
> precedente in questo stesso documento: la fase 6 dichiara che **tre quarti del suo lavoro sono già
> fatti** — nella coda della **fase 4** — perché *«il numero della fase lo dà il perché si è fatto il
> lavoro, non l'elenco delle cose prodotte»*. Un piano in cui una fase nasce già fatta per tre quarti
> è esattamente il posto dove guardare.

## Fase 6 — La tela e la vista

**Produce**: la tela concordata all'attacco, la vista che riscala, il riattacco a misura diversa.

> ## ⭐⭐ TRE QUARTI SONO GIÀ FATTI E MISURATI — nella **coda della fase 4**, il 15 agosto 2026
>
> ⛔ **E non è un errore di numerazione**: il numero della fase lo dà il **perché** si è fatto il
> lavoro, non l'elenco delle cose prodotte. `DECISIONI.md` §5.0-sexies aveva reso la tela **la cura
> di quattro sintomi del mouse e del video** — bande nere, testo interpolato, ri-attacco, e i 4
> secondi fra login e desktop — cioè il pezzo che mancava alla **fase 4**. Tutti i rapporti di quella
> notte si chiamano `F4-IN-*`. ⇒ Il documento sta in `FASI.md` §04-si-comanda, §«la coda della fase
> 4»; il rapporto tecnico è `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.
>
> | quel che questa fase chiede | stato |
> |---|---|
> | la **tela concordata all'attacco** | ✅ `[M]` la tela prende la misura della finestra, scala **1,000** |
> | il **riattacco a misura diversa** | ✅ `[M]` `SESSIONE` concede la tela che il palco ha già, zero fotogrammi scartati |
> | la **vista che riscala** | ✅ c'era dalla fase 2, e adesso la scala vale 1 quando le due tele combaciano |
> | ⛔ *(in più)* ~~il **ridimensionamento a caldo**~~ | **USCITO dal prodotto il 17 agosto 2026** — `DECISIONI.md` §5.1-bis, decisione dell'utente: *«non voglio mettere delle eccezioni nel progetto»*. ⚠ Era possibile su Mutter, e **impossibile** su KWin ≤ 6.7.4 |
> | ⛔ il **ripiego su KWin dichiarato nel registro** | **APERTO**: non verificabile finché KDE è la fase 11. Il percorso di codice c'è (`COMPOSITORE_INCAPACE`) ed è provato dal caso 11 di `banchi/04-b31`, **su un ospite finto** |
> | ⛔ il **banco del riattacco che BATTE UN TASTO dopo** | **APERTO**: il fatto si è visto nel registro (`libei` ricrea i dispositivi, `input.c` li riaggancia) e l'utente ha scritto in un terminale dopo un riattacco — ⛔ ma un banco che lo provi non c'è |
> | ⛔ il **multi-monitor** | **APERTO**, e fuori scopo come funzione (§6.5) |
>
> ⇒ ⭐ **Quando questa fase si aprirà davvero, il suo lavoro è quel che resta in fondo a questa
> tabella** — e le prime quattro righe si rimisurano invece di rifarle.
>
> ⛔ **E quel che di questa fase resta APERTO, per intero:**
> - il **ripiego su KWin ≤ 6.7.4 dichiarato nel registro**, che è il banco nominato qui sotto;
> - ⛔ **il banco del riattacco che batte un tasto e muove il puntatore DOPO** — la riga qui sotto
>   che parla dei dispositivi ricreati. `[M]` il 15 agosto si è visto nel registro che al cambio di
>   geometria `libei` **ricrea davvero** i dispositivi assoluti («regione del puntatore per chiave»,
>   quattro volte di fila), e che `input.c` li riaggancia — ⚠ ma a battere un tasto dopo il
>   riattacco **non ci ha ancora provato nessuno**;
> - il **multi-monitor** e tutto il resto di `SPECIFICHE.md` §6.5.

**L'utente vede**: ridimensiona la finestra e l'immagine si adatta **senza che le finestre dentro
si muovano**. Poi si riattacca da una macchina con un altro schermo e ritrova la sessione adattata.

> ⭐ **E dal 17 agosto 2026 questa frase è vera sempre, non «salvo un interruttore»** — l'immagine
> si adatta e **il desktop non si tocca mai**, su ogni compositore (`DECISIONI.md` §5.1-bis).
> ⚠ Il prezzo dichiarato: se la finestra cambia **forma**, o il tablet si **ruota**, le proporzioni
> non combaciano più e si vedono le bande. Per riavere la misura giusta ci si **riattacca**.

**Il banco**: il ripiego su KWin < 6.8 **dichiarato nel registro** — si verifica che la riga ci
sia, non che «funzioni lo stesso» (`SPECIFICHE.md` §6.3).

⛔ **E il riattacco rinegozia anche la disposizione di tastiera** (`SPECIFICHE.md` §7.3), che su
Mutter **distrugge e ricrea il dispositivo tastiera**; un cambio di geometria ricrea tutti i
dispositivi assoluti. Il puntatore al dispositivo vecchio smette di funzionare **senza errore**
`[R]` (`STUDI.md` §gnome §9). Il banco del riattacco **deve battere un tasto e muovere il puntatore
dopo**, non solo verificare che la sessione ci sia: è la forma «una prova verde col difetto vivo»
esattamente dove si presenta.

⛔ **E con lo stesso peso, l'ordine fra la nascita del puntatore virtuale e l'avvio delle
applicazioni** — riquadro nella fase 2, `[M]` 10 agosto 2026: un cliente Wayland partito **prima**
che i dispositivi di input esistano **non riceve niente**, e il compositore l'iniezione la prende lo
stesso. Al riattacco i dispositivi si **distruggono e si ricreano**: è esattamente il caso in cui
questa trappola torna, su applicazioni già aperte che nessuno riavvierà.

---

## Fase 7 — Audio e appunti

> ## ⭐⭐ L'AUDIO È FATTO — 17 agosto 2026, sul giudizio dell'utente: **«problema audio risolto»**
>
> *Dato su un **video di YouTube** riprodotto nella sessione remota.* `[M]` nessun blocco perso,
> salvo l'avvio — i valori in `fasi/07-audio-e-appunti.md`.
> ⭐ E il volume **governa**: pieno 0,3536 · 25 % 0,0078 · muto 0,0.
>
> ## ⭐⭐ E GLI APPUNTI FUNZIONANO — **«clipboard funziona in entrambi i versi»**
>
> *Giudizio dell'utente col browser, 17 agosto 2026 sera, porta 7730.* Solo testo, nei due versi:
> `appunti.c` nuovo, i tre messaggi di `RCP.md` §7.4 nel filo, la cucitura nei due processi e il lato
> browser. ⇒ 📖 `fasi/07-audio-e-appunti.md` §4.5, §6.9, §9.2-bis.
>
> ⛔ **E l'arbitro esterno del banco NON ESISTE**: `gnome-shell` gira con `--no-x11`, quindi `xclip`
> non ha nessuna sponda a cui parlare, e un client Wayland senza fuoco non possiede la selezione.
> ⇒ Quel giudizio è **l'unica prova** che questa metà della fase abbia — e la riga di `fasi/07-audio-e-appunti.md` §2.4 che
> prometteva un arbitro gratis è stata riscritta.
>
> ⭐ *E la richiesta d'apertura diceva «testo formattato»: chiesto all'utente, che ha confermato
> «solo testo semplice» — `DECISIONI.md` §5-ter.4.*
>
> ⛔ **E la lezione della fase non è sull'audio**: cinque giri di banco verdi e l'utente sentiva
> «jitter pazzesco». `LEZIONI.md` §2.7 — *non c'è miglior strumento di diagnosi che monitorare una
> sessione vera, byte per byte*. Le decisioni prodotte stanno in `DECISIONI.md` **§5-quater**, che
> prima di oggi non esisteva.

**Produce**: Opus e PCM in uscita; appunti testuali nei due versi.

**L'utente sente e vede**: la musica, e il copia-incolla che funziona in tutt'e due i versi.

**Il banco**:
- ⛔ **si ascolta**, non si contano i blocchi: in v1 il banco contava i campioni mentre l'audio era
  **rumore a fondo scala**, e restava verde;
- ⛔ **i due lati si sincronizzano con marcatori, non con `sleep`**: al banco degli appunti di KDE i
  due lati erano sfasati di **tredici secondi** e il controllo dava rosso su codice che funzionava
  (`LEZIONI.md` §2.3-quinquies);
- ⚠ e la clipboard si **svuota all'inizio** di ogni giro: quel che resta dal giro prima viene
  annunciato alla connessione e sembra un risultato.

⭐ **Il lato indipendente del banco degli appunti c'è già, ed è gratis**: su GNOME la sponda X11
di Mutter è incondizionata nei due versi, quindi **`xclip` funziona senza una nostra sessione**
`[R]` (`STUDI.md` §gnome §10). Copiare con `xclip` e leggere col client — invece di far parlare fra loro
due pezzi nostri — è l'arbitro esterno che a questa fase serviva e che non credevamo di avere.

⛔ **Tre trappole di Mutter, che il banco non vede e il prodotto sì**: `DisableClipboard` è **a
senso unico** (dopo, gli annunci non tornano più — non si chiama mai: per lasciare la clipboard
si usa `SetSelection` senza tipi); la firma di `mime-types` è **asimmetrica** fra ingresso `as` e
uscita `(as)`, e chi legge col tipo sbagliato ottiene `NULL` **senza errore**; il gestore interno
degli appunti tiene **un solo tipo MIME**.

**Si riusa**: `altoparlante.c` (892), `suono.c` (582), `appunti_mutter.c` (450), `appunti.c` (115).

⚠ Invariante I5: il volume appartiene alla sessione, e chi si collega lo trova **al massimo**.

---

## Fase 8 — La copia zero ✅ **CHIUSA il 22 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»*, e *«per me è ok»*
>
> *Il titolo del piano dice ancora «la copia zero»; il documento di fase si chiama
> [`fasi/08-l-anello.md`](fasi/08-l-anello.md) perché il mandato vero — dettato dall'utente il
> 22 agosto — era **l'anello**, di cui la copia zero è un tratto.*
>
> | | |
> |---|---|
> | ⭐⭐ **che cosa vede** | trascina una finestra veloce e **la finestra segue la freccia**. Al mattino restava indietro di **mezza barra del titolo** |
> | ⭐ **il numero della fase** | `input → vetro` **accorciato**, **appaiato**: due giri che condividono tutto tranne il binario, `macchina carica: false` scritto dal banco in tutt'e due — i valori in `fasi/08-l-anello.md` |
> | ⭐ **nell'unità dell'utente** | il distacco freccia↔finestra si **avvicina al locale** — e ⭐ il **locale** adesso è misurato |
> | ⭐⭐ **e non è una vittoria di cronometro** | `[M]` i fotogrammi **dipinti** salgono. `LEZIONI.md` §6.2 rispettata, dopo che in questa stessa fase era stata sfiorata **due volte** |
> | ⛔ **il tetto dei 50 ms** | **non è verificato**, e non perché manchi poco: **il numero della fase sta su un confine diverso** da quello dei 50 (`SPECIFICHE.md` §3.2 misura fino al *fotogramma che parte*). ⇒ I due numeri **non si confrontano** — è `LEZIONI.md` §1.28 applicata a noi stessi |
>
> **⭐ Le tre eredità, tutte e tre risposte**: `EncSliceLP` **non** sa fare i sotto-livelli temporali
> (7 profili su 7, due controlli positivi) · la chiave alla tela dell'utente sta **largamente dentro
> il tetto** · la scheda del codificatore adesso si **dichiara** invece di ripiegare in
> silenzio. E `RCP.md` §5.2 e §6.2 passano da `[?]` a ✅.
>
> **⭐⭐ E i difetti trovati per strada, nessuno dei quali era il bersaglio**: la **chiave abbandonata**
> (§5.2 la vieta, ed era la spirale) · la **scala delle ricodifiche corta di uno scalino** · il
> **passo non multiplo di 64** che dava un desktop **inclinato senza errori** · e il **cronometro del
> prodotto che misurava il banco**.
>
> **⛔⛔ E le due lezioni che sopravvivono alla fase**, `LEZIONI.md` **§1.26**, **§1.27** e **§1.28**:
> due banchi sulla stessa **macchina** si falsano in silenzio (e danno **un numero plausibile**, non
> un rosso) · il **colore medio è cieco** a un'immagine sbagliata a ogni riga · e **due banchi che
> non concordano possono avere ragione tutti e due**: misurano due grandezze diverse.
>
> ⏳ **Che cosa NON è stato fatto, e si porta avanti:**
> - ⛔ **il muro di Mutter**: `[M]` un quadro a 60 Hz — non si è mosso in tutta la giornata, e
>   **non l'ha toccato nessuno**;
> - ⛔ **metà del guadagno non è spiegato**: sta in un tratto che la copia zero **non
>   attraversa**. `[?]` L'ipotesi — il produttore fuori dal thread di tempo reale — è
>   **dichiarata, non misurata**;
> - ⚠ **la ritenuta del `pw_buffer` è in vigore senza prova**: il controllo positivo **non ha
>   riprodotto il danno**. Prudenza, non necessità misurata;
> - `[?]` **il modello del distacco ha predetto male due volte, in versi opposti** — prima meno del
>   vero, poi più. ⛔ **È un fatto sul modello, non sull'utente**, ed è lavoro nostro;
> - 🔸 **la tela multipla di 16** (`rcp_misura_ammessa()`): renderebbe la copia zero valida su **ogni**
>   schermo, ⛔ ma è una **modifica al protocollo** — `RCP.md` §4.5 oggi pretende solo che i lati siano
>   pari. **Decide l'utente.**

## ~~Fase 8 — La copia zero~~

> ## ⭐ E IL 22 AGOSTO 2026 L'UTENTE LE HA INDIRIZZATO **L'UNICO APPUNTO CHE GLI RESTAVA**
>
> *Dopo aver dichiarato OK l'audio su tutti e quattro i motori supportati:* **«l'unico piccolo
> appunto è un'ottimizzazione sulle performance grafiche, che credo sia lo scopo della fase 8»**.
>
> ⭐ **Non sbaglia**, ed è la seconda volta che indirizza una cosa a questa fase leggendo il piano.
> ⚠ **E vale come mandato**: quando questa fase si apre, il suo metro non è «la copia zero è
> scritta», è **quel che lui vede muoversi meglio**.
>
> ⏳ **E ci arriva con due misure già in mano**, prese la notte del 21-22 agosto:
> - `[M]` **`createImageBitmap` costa poco per fotogramma**, una piccola parte del tetto di 50 ms.
>   ⭐ E il percorso attuale costa **molto meno** del disegno 2D che c'era prima;
> - `[M]` **il percorso `?video=worker` funziona e NON rende**: il ritmo massimo scende. ⇒ La
>   strada «spostare il disegno su un altro thread» è **già stata provata e non paga**: chi apre
>   questa fase non la rifaccia.

> ## ⭐⭐ IL TITOLO È CAMBIATO, E DUE TERZI DELLA FASE SONO GIÀ FATTI — *16 agosto 2026*
>
> *Rilievo dell'utente all'apertura della fase 6: «gli ultimi test sono stati eseguiti con l'ausilio
> della Intel integrata, e quindi usando l'accelerazione HW, o sbaglio?». **Non sbaglia**, ed è
> scritto qui perché chi arriva a questa fase non cerchi lavoro già consegnato.*
>
> *Qui il titolo era **«L'accelerazione»** e la riga diceva: «**Produce**: HEVC in hardware su
> Intel, 10 bit, e la copia zero».*
>
> **La codifica in hardware è entrata nel prodotto il 13 agosto 2026**, di proposito e con la
> ragione scritta sopra alla fase 3: la catena si muoveva **da quel giorno**, quindi il *prima* e
> il *dopo* si potevano misurare **con lo stesso banco e la stessa scena** — cosa che fra tre fasi
> non sarebbe più stata vera. `src/codificatore.c` · la nota «la fase 8 entrata di soppiatto» la chiama *«la fase 8 entrata di soppiatto
> nella fase 2»*.
>
> | la promessa di questa fase | dov'è finita |
> |---|---|
> | ⭐ **HEVC in hardware su Intel** | ✅ **fatto e misurato.** La codifica sulla scheda passa da **VA-API** su **`/dev/dri/renderD128`** — l'iGPU Intel, entrypoint `EncSliceLP` — e dalla fase 18 con **libva diretta**, per H.264 e HEVC. Il ripiego software è **OpenH264** (H.264) o **SVT-AV1** (AV1), ⛔ **HEVC in software non c'è**, e il ripiego **scrive di essere un ripiego**. `[M]` il tratto della codifica si dimezza e i fotogrammi raddoppiano (`F3-E`, stesso palco, notte del 14 agosto); la chiamata al codificatore è ormai una piccola parte di quel tratto (fase 4, `hev1.2.4.L120.B0`) |
> | ⚠ **10 bit** | ⛔ **nominali, e il muro è a monte, non qui.** `DECISIONI.md` §2.3-ter `[M]`: dalla cattura di Mutter dieci bit veri **non escono per nessuna strada** — MemFd dà BGRx, il DMA-BUF pure, e chiedendo i formati a 10 bit da soli si prende `no more input formats` su tutt'e due. `Main10` da qui vuol dire **otto bit promossi a dieci**. ⇒ La domanda non è più *«il nostro codice sa fare 10 bit?»* ma *«esiste una sorgente che ce li dia?»*, ed è **una domanda per la cattura**, non per la codifica |
> | ⛔ **la copia zero** | **intatta — e non anticipata di proposito** (`README.md`: *«la copia zero NON si anticipa: resta alla fase 8»*). È tutto quel che segue |
>
> ⭐⭐ **E il conto della fase 4 dice che quel che resta pesa più di quel che è stato tolto.** Il
> tratto più caro dell'anello è ancora `cattura → primo byte` `[M]`, e dentro ci sta:
>
> | | lo toglie la copia zero? |
> |---|---|
> | la conversione dei colori, allora in CPU | ⭐ **sì** |
> | il caricamento sulla GPU | ⭐ **sì** |
> | la codifica, **in hardware** | no — è già curata |
> | ⛔ **e una parte che nessuno dei tre spiega** | ⏳ `[?]` **da scoprire, e sta in questo tratto** |
>
> ⇒ ⭐ **La conversione e il caricamento sono esattamente il lavoro che la copia zero cancella** —
> convertire e ricaricare sulla GPU un fotogramma che **sulla GPU ci stava già** — e pesano più di
> quel che la codifica costa oggi. ⛔ E la parte non spiegata è **nello stesso tratto**: è qui che si
> cerca, e questa fase è l'unica che ha il motivo di guardarci dentro. I valori in `FASI.md`
> §04-si-comanda.

> ## ⭐⭐⭐ E IL 22 AGOSTO L'UTENTE HA DETTATO LA SPECIFICA — `SPECIFICHE.md` §3.2-bis
>
> *«La mia specifica è avere un'esperienza utente **il più vicina possibile a una situazione
> locale**, ma non identica: quello è impossibile.»*
>
> ⭐ **E ha precisato il sintomo con l'occhio, che è una misura**: trascinando veloce una finestra,
> la distanza fra la freccia e la finestra che la insegue è **«metà della barra del titolo»**.
>
> ⛔⛔ **Da cui il vero mandato di questa fase, e NON è la copia zero**: quel distacco è
> `velocità della mano × ritardo dell'anello`, la freccia è locale e la finestra no ⇒ **è un
> ELASTICO** che si apre quando la mano accelera. La copia zero toglie **una piccola parte**
> dell'anello. ⇒ Serve **l'anello intero**, ed è quel che la fase 4 aveva già scritto chiudendo:
> *nessuna cura singola porta l'anello sotto il tetto: è lavoro della fase 8*.
>
> ⛔ **E una strada è chiusa prima di aprirsi**: mettere l'anello in parallelo comprerebbe
> fotogrammi pagandoli in ritardo ⇒ **allargherebbe l'elastico**. `SPECIFICHE.md` §3.2 lo vietava già: *«una scelta
> che alza il ritmo peggiorando il ritardo non si fa»*.
>
> ⏳ **Il primo numero del banco** non è più un tratto: è **`input → vetro` rimisurato sulla scena
> vera** — finestra 720×433, velocità mediana **3 400 px/s**, picchi **12 400** (`[M]` dal video
> dell'utente, 22 agosto). Il numero della fase 4 ha otto giorni e due fasi di cure in mezzo.

**Produce**: ⭐ **l'anello più corto**, di cui la copia zero è **un tratto su sei** — il fotogramma
va dalla cattura al codificatore **senza uscire dalla GPU**.

**L'utente vede**: ⭐ **la finestra che insegue la freccia più da vicino**, e giudica quanto ci si è
avvicinati al locale. ⚠ *(Era: «la stessa immagine di prima, e giudica che non sia peggiorata» — il
metro di quando questa fase era solo la copia zero.)*

**Il banco**, ed è la lezione che è costata di più:
- ⛔ **si misurano i fotogrammi consegnati, non i millisecondi di CPU.** La fase 9 di v1 ha portato
  giù di molto il costo per fotogramma mentre i fotogrammi consegnati **scendevano**.
  Un guadagno che si paga in fluidità non è un guadagno (`LEZIONI.md` §6.2). ⛔⛔ **E qui morde
  due volte**, perché la fase 4 ha trovato la coda che cresce: il server consegnava più
  fotogrammi di quanti la pagina ne dipingesse. Un guadagno di millisecondi che si trasformasse
  in fotogrammi che nessuno dipinge **peggiorerebbe il ritardo** invece di curarlo;
- ⛔ **chiedere il codificatore e verificare che abbia obbedito**: un codificatore che
  ripiega in CPU credendosi in GPU produce due misure sotto la stessa etichetta. Se non obbedisce,
  si dichiara il fallimento (`LEZIONI.md` §1.8). ⭐ La domanda giusta è **che cosa riceve** il
  codificatore — una superficie della scheda, o dei pixel — non come si chiama;
- ⚠ e la prova «ha aperto un render node ⇒ rende in GPU» **non prova niente** (§1.11);
- ⛔ **e il numero si rifà con lo STESSO banco e la STESSA scena della fase 4** (`03-b17-ritardo.py`),
  o il prima e il dopo non si sottraggono. ⚠ Non basta il totale: si affiancano **i tratti**, perché
  la domanda di questa fase è *«tolta la copia, gli altri restano dove sono?»*.

⛔ **E la copia zero si riapre dal lato giusto**: le due schermate che si alternavano non erano un
problema di *acquire* ma di **release** — `can_reuse_pw_buffer` si arrende se manca
`SPA_META_SyncTimeline` e Mutter riusa il buffer **mentre VA-API lo sta ancora leggendo** `[R]`
(`LEZIONI.md` §8, il riquadro della caccia sbagliata). Due cure candidate, entrambe piccole:
chiedere la timeline — che Mutter offre — oppure **trattenere** il `pw_buffer` fino a lettura
finita. ⚠ E **il DMA-BUF di Mutter non è un diff**: chi riprendesse la superficie di accumulo
rifarebbe la cura che peggiorava le cose.

⭐ **E la strada è aperta `[M]`**: Mutter il DMA-BUF **lo consegna davvero** — 388 fotogrammi, 4
buffer, modificatore **LINEAR**, stride 7680 letto dal chunk (`DECISIONI.md` §2.3-ter). ⚠ Il
formato resta **BGRx a 8 bit**: la copia zero si fa su quello, e i dieci bit non tornano da questa
porta.

> ### ✅ ⭐ La trappola della GPU è CHIUSA, e va detto perché nessuno la ricerchi — *15 agosto 2026*
>
> *Qui stava scritto: «con due schede, il compositore che disegna su quella sbagliata dà
> composizione in software **senza un errore**. La regola udev di `fondamenta/banco/gpu-udev.sh` va
> applicata e verificata».*
>
> ⛔ **Ed era peggio di un rischio: era già successo.** `[M]` `/etc/udev/rules.d` era **vuota**, i
> gruppi `video`/`render` davano accesso a tutt'e due le schede, e il compositore aveva preso la
> **Radeon** — una misura buttata perché fatta sulla scheda sbagliata.
>
> ⭐ **La regola è stata applicata e verificata** (`DECISIONI.md` §4.6-ter): `gnome-shell` apre
> **6 descrittori su `renderD128`**, l'integrata, e solo quella. ⇒ **Compositore e codificatore
> stanno sulla stessa scheda** — che è precisamente la condizione senza la quale la copia zero non
> avrebbe senso: un fotogramma non si passa senza copia fra due schede diverse.
>
> ⚠ **Il prezzo resta dichiarato**: negare il nodo lo nega a **tutta la sessione dell'utente**, non
> al solo compositore.

⏳ **Che cosa questa fase NON deve più portarsi dietro**, e dove sono andati:
- i **10 bit veri** → una domanda per la **cattura**, e vive nelle fasi in cui la cattura si tocca;
- ⚠ la **qualità di `EncSliceLP` contro l'entrypoint pieno** → `[?]` **mai misurata**: la codifica a
  bassa potenza è veloce e **non è equivalente** alla piena. È il punto di lavoro fra qualità e
  banda, cioè la **fase 9** — e se un giorno si scoprisse peggiore, si cura lì, non qui.

---

## Fase 9 — La qualità e la degradazione ✅ **CHIUSA il 24 agosto 2026**

> ### ⭐⭐⭐ CHIUSA SUL GIUDIZIO DELL'UTENTE — *«il prodotto cambia in meglio; questa fase era per rendere più solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli»*
>
> 📖 `fasi/09-la-qualita-e-la-degradazione.md` — la sintesi in testa, e §17-§21 la parte che conta.
>
> ⭐⭐ **Il bersaglio l'ha corretto lui a fase aperta** (`DECISIONI.md` §3.1-ter): non la **banda** —
> *«30 mbps sono una connessione da metà anni 90»* — ma **la rete che perde, riordina e sfarfalla**.
> Ed era la grandezza giusta: sulla banda il prodotto non cedeva, su un filo sporco sì.
>
> **La scala che chiude la fase viene dai suoi occhi**: fino a una certa perdita *«è tutto
> fluido»*, oltre ⛔ *«bloccato»*, con le cure e senza — la scala misurata sta in
> `fasi/09-la-qualita-e-la-degradazione.md` §19.1 e §19.6.
>
> ⛔ **Sopra una certa perdita la scala di degradazione non ha più niente da offrire**, e l'unica
> risposta onesta è dichiarare la linea morta (`DECISIONI.md` §3.1-quater) — che è la decisione che lui ha preso
> **prima** di avere quel numero.
>
> **Le cinque cure sono ACCESE** (§3.1-septies), ognuna con una strada sola per spegnerla, e ⭐ **la
> prova che poteva far ritirare tutto è verde**: `[M]` sulla linea sana il ritmo coi predefiniti è
> lo stesso che a cure spente — **nessun peggioramento**, che è la ferita per cui v1 perse questa fase.
>
> **I tre fatti che restano**, e valgono oltre la fase:
> 1. ⭐⭐ **il difetto non comincia dove si vede**: la spirale di chiavi parte al **primo pacchetto
>    perso**, il calo che l'utente **vede** arriva molto più in là;
> 2. ⭐⭐ **l'innesco ha un rischio costante** nel tempo, e una volta acceso non si spegne. ⛔ I
>    banchi girano pochi secondi, **le sessioni durano ore**: ogni misura presa vicino al bordo
>    **sottostima**;
> 3. ⛔ **il disordine viene scambiato per perdita**, e ci è tornato addosso: la prima «linea morta»
>    era tarata su `pkt_lost`, e `[M]` una linea che **regge** ne dichiarava più di una che **non
>    regge**. Rifatta sullo **stallo dell'uscita**.
>
> ⚠ **E il conto degli errori di metodo, che è la parte più utile**: `[M]` **nove difetti nei
> banchi**, tutti della forma *«silenzio invece di rosso»* · **tre prove che non mordevano**, scoperte
> contando i pacchetti · **due conclusioni mie ritirate** (le applicazioni che «non arrivavano», la
> prova della claquette dichiarata «nulla» e smentita dal terzo giudizio) · e **due premesse false**
> ereditate e corrette (l'utente non è mai stato su PCM; il ritardo dell'audio misurato allora non
> raggiunge il suo orecchio).


**Produce**: il controllo del ritmo, la scala di degradazione, il comportamento su rete cattiva.

> ### ⛔⭐⭐⭐ IL BERSAGLIO È STATO CORRETTO — **23 agosto 2026, a fase aperta**
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti
> che perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».*
> — ⇒ `DECISIONI.md` **§3.1-ter**.
>
> ⛔ **La banda esce dal corpo della fase.** La giornata era stata passata a stringere la linea, e
> `[M]` §16: sul **percorso vero** il prodotto regge il caso peggiore **senza degradare e con tutte
> le cure spente** — ogni fotogramma consegnato è dipinto, **una** chiave.
> Un banco che non riesce a far cedere quel che misura **non sta misurando la grandezza giusta**.
>
> ⭐ **Le tre grandezze nuove, e non sono la stessa cosa:**
> **perdita** (il video ritrasmette ⇒ si paga in ritardo; l'audio no ⇒ si paga in buchi) ·
> **fuori sequenza** (⭐ è la condizione mancante della cura del riordino dell'audio, l'unica cura
> del 23 agosto la cui metà utile non è mai stata verificata) ·
> **jitter** (`[?]` QUIC può scambiarlo per perdita e stringere la finestra **senza motivo**: se
> succede il calo è **nostro**, non della rete).
>
> ⚠ **`DECISIONI.md` §3.1-bis non è annullata**: il pavimento dichiarato resta — ⛔ **ed è passato a 30 Mbit/s la
> notte stessa** (§3.1-sexies: *«ho già detto che il pavimento, per quanto riguarda la banda, è a
> 30 mbps»*). Cambia il suo mestiere — da **domanda** della fase a **premessa** su cui si misurano
> le altre tre.
>
> ⛔⭐⭐ **E la fase ha prodotto una decisione nuova, `DECISIONI.md` §3.1-quater**: una linea che perde **a raffiche**
> si dichiara **morta** — 10 s senza pacchetti, o una perdita copiosa dentro 1-2 s — e ✅ **l'utente
> rientra a mano**. Nasce dalla scelta fra due mali misurati: `[M]` senza cure lo schermo si congela
> per molti secondi, con le cure si muove con secondi di ritardo. ⇒ Nessuno dei due va servito.
> ⛔ Prerequisito: **`DECISIONI.md` §3.1-quinquies**, il *fantasma* — rientrando, l'utente trova il proprio posto
> occupato da sé stesso per 30,5 s, e con un messaggio che per lui è **falso**.
>
> ⛔ E il `netem` su `lo` diventa **risorsa unica con lucchetto** (`banchi/09-lucchetto.py`): la
> disciplina si mette sulla radice dell'interfaccia, quindi due banchi che guastano insieme non si
> dividono il lavoro — il secondo **cancella il guasto del primo**, e il primo continua a misurare
> credendo di averlo. ⚠ Non darebbe rosso: darebbe un numero plausibile.

**L'utente vede e giudica**: l'immagine. ⛔ **Ed è l'unico giudizio che conta**: in v1 questa fase
era stata validata con PSNR, SSIM e l'occhio dello sviluppatore, e il giudizio dell'utente sul
desktop vero fu *«siamo tornati indietro»*. La fase fu azzerata.

**Il banco**: la rete strozzata a valori veri — ⭐ **20 Mbit/s, il pavimento dichiarato dall'utente
il 23 agosto** (`DECISIONI.md` §3.1-bis), con perdita e giro lungo — e la verifica che il ritmo cali
**senza mai bloccarsi** e senza mai staccare.

> ⛔ **Il numero era «2 Mbit/s», ed è cambiato il 23 agosto 2026.** *«Mi ero tenuto più largo:
> ritengo che una connessione minima debba essere 20 mbps: al di sotto di questo limite l'utente
> nemmeno riesce a navigare, figuriamoci usare remotix».* ⇒ ⭐ **Cambia che cosa si sta tarando**:
> la scala di degradazione copre i **cali temporanei di una linea buona**, non le linee povere.
> ⚠ E cambia il verso di un rischio: a 20 Mbit/s il fondo scala non si raggiunge quasi mai, quindi
> il difetto che si nasconde non è più «degrada male», ma **«degrada quando non dovrebbe»** — che
> è l'invariante I1, ed è precisamente la prima cosa che questa fase verifica.
>
> ⭐ **Lo strumento per strozzare dal lato del client c'è**: `wondershaper` in `~/.local/bin` sul
> tablet dell'utente — ⇒ si può strozzare **il percorso vero**, non solo `lo` con `netem`, che è
> il limite dichiarato di `banchi/07-b64-rete.py`.

⛔ **La cosa che si verifica per prima**: che il ritmo **non** cali quando la scena è ferma. È
l'invariante I1, ed è la ferita da cui nasce.

⚠ E ciò che cambia quel che si vede sta **dietro un interruttore spento** finché l'utente non l'ha
guardato (I6).

> ### ⛔⛔ CORREZIONI DEL **23 agosto 2026, sera** — quel che i fatti hanno superato
>
> *📖 Tutto in `fasi/09-la-qualita-e-la-degradazione.md`, la sintesi in testa.*
>
> **1. ⛔ «Strozzare a 20 Mbit/s» NON prova quel che questa fase deve provare.** `[M]` §3.10:
> con la banda chiesta **sotto** il buco **non succede assolutamente niente**. ⇒ ⭐ **Serve un
> GRADINO** — larga → 3 s stretti → larga — non un limite costante: un limite costante misura il
> **regime**, e in regime la previsione è che non succeda niente. ⛔ E **tre secondi bastano**:
> il ritmo crolla e **metà dei fotogrammi diventano chiavi**.
>
> **2. ⭐⭐ «Che il ritmo non cali a scena ferma» è MISURATO, e la risposta è più netta della
> domanda**: a scena ferma il ritmo **non cala, si FERMA**.
> ⛔ **E non è una nostra decisione**: `RecordVirtual` di Mutter consegna **solo sul cambiamento**.
> ⭐ **E il risveglio non costa niente di percepibile**, qualunque sia la durata della quiete.
> ⇒ È una violazione **letterale** di I1 che
> **non costa niente a chi guarda**, e **non è un difetto della fase**.
>
> **3. ⭐ Le due cose «già misurate» del riquadro qui sotto SONO STATE SCRITTE il 23 agosto**, con
> altre tre: la cura di `video_sgombra()` (`--sgombra-soglia-ms`, spenta), il riordino dell'audio
> (senza interruttore), la risalita della qualità (`--qualita-risale`, spenta), il tetto di banda
> (`--tetto-banda-mbit`, spento) e ⛔ **la cura di un crollo**: il server è morto di `SEGV` alle
> 08:28:09 per un **uso dopo la liberazione** in `webtransport.c`. ⚠ **Nessuna delle cinque è stata
> misurata sulla macchina di prova.**
>
> **4. ⛔ E il difetto che si nasconde non è solo «degrada quando non dovrebbe».** `[M]` `fasi/09-la-qualita-e-la-degradazione.md` §3.8: con
> QP 26 fisso e nessun tetto, un **film con la grana a schermo intero** chiede **parecchie volte il
> pavimento**. ⭐ **Ma il desktop vero dell'utente ne chiede una piccola frazione.** ⇒ Il tetto è per il
> **caso duro**, e la fase ha **due** bersagli, non uno.
>
> **5. ⛔ E il regolatore del ritmo ha un ordine obbligato**: viene **dopo** la soglia sulla coda.
> Finché `video_sgombra()` svuota la coda a ogni fotogramma, la grandezza su cui il regolatore si
> aggancia è **zero per costruzione** — e un regolatore muto e una linea sana hanno la stessa faccia.

⭐ **E questa fase adesso ha un secondo cliente, che prima non aveva**: la scala di degradazione è
**il modo in cui si fa stare più gente sulla stessa macchina**. Un budget senza la scala sa dire
solo *«no»*; con la scala sa dire *«sì, più piccolo»* — ed è la fase 10, che viene subito dopo.

⏳ **E qui arriva una domanda che la fase 8 le ha passato**: `[?]` la qualità dell'entrypoint
`EncSliceLP` — la codifica a **bassa potenza**, quella che il prodotto usa — contro quello **pieno**,
a parità di banda. **Non è mai stata misurata**, e il punto di lavoro fra qualità e banda è di
questa fase.

> ### ⭐⭐ E LA NOTTE DEL 21 AGOSTO QUESTA FASE HA RICEVUTO DUE COSE GIÀ MISURATE
>
> *Arrivano dalla chiusura dei buchi delle fasi 6 e 7, ⛔ e sono state **spostate qui dall'utente**:
> «i problemi di rete non rientrano in questa fase, qui stiamo chiudendo i buchi delle fasi 6 e 7».
> ⚠ Il coordinatore aveva portato la decisione nella stanza sbagliata.*
>
> **1 · ⛔ Il motore della spirale: `video_sgombra()` abbandona i delta a OGNI fotogramma.**
> `[M]` Su linea larga non abbandona quasi mai; su linea stretta un delta non esce nell'intervallo
> di un fotogramma, quindi viene abbandonato **sempre**, e ogni abbandono riaccende il debito di
> `RCP.md` §5.2 — il registro lo dice **quasi a ogni fotogramma**. ⇒ Il video degenera in **un flusso di sole chiavi**, che è la forma
> peggiore di degradazione: pesante, a scatti, e affama l'audio.
> ⭐ **La cura è nominata e `RCP.md` §5.1 la permette senza imporla**: abbandonare un delta solo quando è
> *davvero senza speranza* (una soglia sulla coda) invece che a ogni fotogramma più recente. Così
> sotto congestione il video calerebbe di **ritmo** restando fatto di delta.
> ⚠ **Il prezzo va giudicato dall'utente**, ed è esattamente il mestiere di questa fase: per una
> frazione di secondo si vedrebbe qualcosa di leggermente vecchio. ⛔ In v1 una fase come questa fu
> azzerata perché validata con PSNR invece che con l'occhio: **non si decide senza di lui**.
>
> **2 · ⛔ La finestra di riordino dell'audio.** `src/pagina.html` scarta un datagram *«più vecchio
> di quel che è già ARRIVATO»*, mentre `RCP.md` §6.3 dice *«già consumati»*. ⇒ Si butta un blocco
> arrivato **un millisecondo** fuori ordine **mentre si tengono 250 ms di cuscino**.
> `[M]` con `netem`: con un ritardo fisso il tono resta puro; **con un jitter di pochi millisecondi
> si sporca**, e una parte grossa dei datagram viene scartata. ⭐ Su WiFi vero, invece, i «vecchi» sono **zero** — ed è la
> ragione per cui è di questa fase e non della 7.
> ⚠ Due avvertenze già pagate: `netem delay X Y` **riordina davvero**, una coda di casa di solito
> no; e la misura è in **PCM da 5 ms** — con Opus (20 ms) la soglia sarebbe ~4 volte più alta.
>
> ⭐ **E la strumentazione per giudicarle è già scritta**: `banchi/07-b65-datagram.py` (la rete
> strozzata coi byte veri presi dal qdisc, il controllo scena accesa/spenta che decide),
> `banchi/07-b64-rete.py` e `banchi/07-b64-orecchio.py` (il giudice del tono, certificato 4 su 4).
> ⇒ Questa fase non parte da zero: parte da un banco che sa già dire quando **non** ha misurato
> niente.

---

## Fase 10 — Multi-tenant e il budget

> ## ⭐⭐ SPOSTATA QUI DALLA CODA DEL PIANO — *16 agosto 2026, decisione dell'utente*
>
> *Era la **fase 12**, dopo i tre desktop nuovi. L'utente: «PRIMA si chiude lo sviluppo anche con il
> multi-tenant, e solo dopo si pensa agli altri DE».*
>
> ⚠ **Le fasi dei desktop non sono state declassate: sono state riconosciute per quel che sono.**
> Producono **larghezza** — il secondo, terzo e quarto desktop — su una forma che il multi-tenant
> può ancora cambiare. E l'argomento non è nuovo: è **lo stesso** con cui `DECISIONI.md` §4.6-quater
> aveva rimandato il multi-tenant dopo la fase 8 — *«misurarle prima vuol dire misurarle due volte»*
> (`LEZIONI.md` §7.2) — applicato dall'altro capo:
>
> | | |
> |---|---|
> | ⭐⭐ **la profondità prima della larghezza** | se il multi-tenant tocca la sessione o il budget, la modifica va riverificata **su quattro desktop invece che su uno**. È «misurarle due volte», moltiplicato per quattro |
> | ⛔ **e il budget è un budget di GPU, e la GPU è UNA** | il numero si misura su `renderD128` — la stessa iGPU che compone **ogni** desktop. È una proprietà **della macchina**, non del desktop: misurata una volta, le fasi 11 e 12 la ereditano. Misurata dopo, non si sa più quale numero appartenga a che cosa |
> | ⭐ **e la dipendenza inversa non esiste** | niente qui dentro ha bisogno di KDE, XFCE o LXQt |
> | ⚠ **e la macchina di prova è GIÀ multi-utente** | `nicfio` locale + `prova` remoto che devono convivere: `DECISIONI.md` §4.6-quater lo chiama *«lo stato normale della macchina, non uno scenario da inventare»* |
>
> ⚠ **E quel che questa fase NON evita, detto per intero**: l'architettura c'è già in buona parte —
> `figlio.c` ⚠ *(il codice citato non c'e' piu': da rileggere)* dichiara *«un utente per figlio»*, un processo per sessione. ⇒ Non si sta scansando
> una riscrittura strutturale; si sta evitando di **misurare un numero di macchina quattro volte**.
>
> ⛔ **E la precedenza che resta, e va rispettata**: questa fase sta **dopo la 8**. La copia zero
> cambia **quanto costa una sessione** in memoria e banda di GPU — e il budget misurato prima della
> copia zero è un budget da rifare. È `DECISIONI.md` §4.6-quater alla lettera, e non è cambiato niente.
>
> ⚠ **Le parole dell'utente del 15 agosto dicevano «fase 12»** (`DECISIONI.md` §4.6-quater,
> `FASI.md` §05-la-sessione), e **restano scritte così** dove sono citate: era il numero di allora.
> ⭐ **La decisione non è cambiata — è cambiato l'ordine**: il confine fra «un utente per volta» e
> «la macchina piena» è ancora quello che lui ha tracciato.

**Produce**: più utenti insieme, il budget del codificatore, il rifiuto motivato.

**L'utente vede**: due sessioni vere in contemporanea; e quando la macchina è piena, un messaggio
che **dice perché**.

**Il banco**: si satura il codificatore di proposito e si verifica che l'undicesimo riceva
`BUDGET_PIENO` — e che **i dieci che stavano lavorando non peggiorino** (`DECISIONI.md` §4.6-bis).

⚠ ~~**E il debito con la scadenza scritta è di questa fase**: `MAX_ATTACCATE` è un `#define` a
**16** — e `MAX_FIGLI` a 16, che lo segue — dove `SPECIFICHE.md` §5.5 promette **dieci
configurabile**.~~ ✅ **SCADUTO E PAGATO il 25 agosto 2026** *(riallineato al codice il 28)*: il
numero è uno solo, `RCP_TETTO_SESSIONI` in `src/rcp.h`, e si cambia con **`--tetto-sessioni N``**.

> ## ✅ APERTA IL 24 AGOSTO 2026, **CHIUSA IL 25** sul giudizio dell'utente
>
> *«Sono soddisfatto. Riprodotto audio e video su una connessione del 1990. Non credo che si
> possa chiedere di più.»* ⚠ E **due decisioni non prese**, dichiarate: QVBR resta **spenta**,
> tetto **10** e riserva **0,5**.
>
> 📖 **`fasi/10-multi-tenant-e-il-budget.md`**.
>
> ⭐ **Il debito è saldato**: i `#define` a 16 erano **cinque, non due** (`MAX_ATTACCATE`,
> `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI` — e quest'ultimo era **8**, un sesto numero ancora
> diverso). Adesso scendono tutti da **`RCP_TETTO_SESSIONI`**, vale **dieci**, e si muove a caldo con
> **`--tetto-sessioni N`**.
>
> ⛔⛔ **E la premessa della fase era sbagliata**: *«il budget del codificatore»*. `[M]` Il collo è la
> **composizione**, che satura prima del codificatore — e a saturarla è **`gnome-shell`**, non noi.
> ⇒ `DECISIONI.md` **§4.6-nonies**.
>
> ⭐ **E quel che l'utente vede è stato prodotto**: due sessioni vere insieme, e ⭐ **`BUDGET_PIENO 0x06` parte davvero**, con una frase che dice
> *perché* — fino a questa fase era dichiarato in `rcp.h` e in `RCP.md` **e nessuna riga del server
> lo mandava mai**.

---

## Fase 11 — La rete di sicurezza

> ## ⭐⭐⭐⭐⭐ DECISA DALL'UTENTE IL 25 AGOSTO 2026, a fase 10 appena chiusa
>
> *«Prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi. Prima di
> passare agli altri DE è necessaria una sessione dedicata per studiare una modalità che impedisca di
> introdurre regressioni man mano che verrà implementato il supporto ai nuovi DE.»*
>
> ⇒ `DECISIONI.md` **§4.6-duodecies**. ⚠ **KDE, XFCE e LXQt scalano di uno**: diventano le fasi 12,
> 13 e 14. Le fasi **non cambiano di una riga** — cambia il loro posto, come già il 16 agosto.

📖 **Il documento della fase è aperto**:
[`fasi/11-la-rete-di-sicurezza.md`](fasi/11-la-rete-di-sicurezza.md) — ⭐ scritto **anche per chi non
conosce il progetto**, perché l'utente lo sottopone a un secondo parere: **§2** i vincoli già decisi,
**§4** la lista dei controlli, **§8** le domande aperte.

**Produce**: un modo di accorgersi **da soli** che qualcosa si è rotto, prima che lo scopra l'utente.

> ## ✅⭐⭐⭐⭐⭐ **FATTA — 27 agosto 2026**
>
> `[M]` **Sedici maglie**, quattro scatole, e il giro intero in **2 h 14**:
>
> | | |
> |---|---|
> | verdetti verdi | **58** |
> | rossi | **3** — e sono **lo stesso rosso**: `C1` su kde/xfce/lxqt, perché ⛔ il prodotto sa avviare **solo GNOME** (`src/sessione.c` · `scrivi_dropin()`) ⇒ **è la fase 12** |
> | ⭐⭐ **guasti innestati** | **49 su 49 visti** |
> | rossi del **banco** | ⭐ **nessuno** |
>
> ⭐⭐⭐ **E il difetto più vecchio del progetto è caduto per strada**: *«la sessione che nasce
> cieca»* (`fasi/10-…` `fasi/10-multi-tenant-e-il-budget.md` §7.4) **non era del prodotto** — l'inquilino non era nei gruppi `video` e
> `render`. `[M]` 17 sessioni su 17 vedono coi gruppi, **0 su 4** senza. ⇒ Le cinque prove dichiarate
> «impossibili» non lo erano, e oggi girano tutte.
>
> ⚠ **E quel che la rete NON prende, dichiarato**: non confronta **ieri con oggi** (una lentezza che
> non rompe niente passa), e su tre scatole su quattro prova **l'ambiente**, non il prodotto.

**L'utente vede**: niente di nuovo sullo schermo — ⭐ **e questo è il punto**: vede che le cose che
funzionavano **continuano a funzionare** quando arrivano i desktop nuovi.

---

### ⛔ Perché questa fase esiste — tre difetti veri, non un timore generico

| il difetto | nascosto per | ⛔ perché era invisibile |
|---|---|---|
| **la sessione che nasce cieca** (fase 10 `fasi/10-multi-tenant-e-il-budget.md` §7.4) | giorni | ⛔ **nessuno apriva una sessione NUOVA**: si riusavano quelle già aperte, che il monitor ce l'avevano |
| **il browser che non parte al secondo utente** ⚠ *(non il collegamento `~/.cache`: quello è una **scelta** dell'utente, `DECISIONI.md` §4.6-undecies)* | **due fasi** | ⛔ e il controllo che *«chiudeva la questione»* girava da un utente **nella stessa condizione** |
| **cinque banchi che contavano zero fotogrammi** | un giro | ⛔ una cura al registro ne aveva rotto le espressioni, e la funzione tornava **0 invece di «non lo so»** |

⇒ ⭐⭐ **Tutti e tre invisibili per la stessa ragione**: si guardava sempre **lo stesso pezzo di
scena**, e si guardava **il processo invece del pixel**.

---

### Che cosa deve produrre, in concreto

| # | | ⛔ e il perché sta in un difetto vero |
|---|---|---|
| **1** | ⭐ **Una prova di CONSEGNA che parte da zero**: macchina pulita → utente nuovo → sessione nuova → **un'immagine del desktop con una finestra dentro** | ⛔ è l'unica forma che avrebbe preso la sessione cieca. Una prova che riusa una sessione **non la prende mai** |
| **2** | ⭐ **Invarianti eseguibili**, poche e vere: la sessione ha un monitor · una finestra si apre · i fotogrammi arrivano · **chi c'è già non peggiora** (I1) · le gemelle R12.3 combaciano · il registro dice **di chi** parla | ⚠ Poche. ⛔ Una rete con cento maglie che nessuno legge è cerimonia |
| **3** | ⛔ **Che giri DA SOLA** dopo ogni modifica, senza che qualcuno se ne ricordi | ⛔ le tre volte di oggi nessuno se n'è ricordato — **e nessuno era distratto**: semplicemente non c'era il gancio |
| **4** | ⭐⭐ **Che sia CERTIFICATA lei stessa** — `--certifica`, coi guasti innestati | ⛔ `LEZIONI.md` §1.36: *lo strato che coordina i banchi è un banco anche lui, e nessuno lo certifica*. `[M]` **sei difetti** trovati lì dentro in una fase sola |
| **5** | ⭐⭐⭐ **Che sia CIECA AL DESKTOP** — le stesse invarianti puntate su GNOME, KDE, XFCE, LXQt senza riscriverle | ⛔ è l'intera ragione per cui la fase sta **prima** dei desktop nuovi: una rete scritta su misura di GNOME va riscritta quattro volte |
| **6** | ⚠ **Che guardi la CONSEGNA sulla macchina COM'È** | ⛔ il browser che non parte non era nel nostro codice: nasceva dall'incontro fra **come l'utente ha configurato la sua macchina** — legittimamente — e **i dieci utenti che ci mettiamo noi**. Una rete che compila e prova solo `src/` non l'avrebbe presa mai. ⚠ E non deve **giudicare** la configurazione: non è affar suo |

---

### ⛔⛔ IL COLLAUDO DELLA FASE — ed è già scritto, oggi

⭐⭐ **La rete si punta contro il codice del 25 agosto 2026, e DEVE diventare rossa su `fasi/10-multi-tenant-e-il-budget.md` §7.4** — la
sessione che nasce cieca — ⛔ **senza che nessuno le abbia detto dove guardare.**

⚠ **E il secondo collaudo**: deve accorgersi che **al secondo utente il browser non si apre**.
⛔ **Non** «deve trovare il collegamento `~/.cache`»: quello è una **scelta** dell'utente sul suo
sistema, non un guasto — correzione del 25 agosto 2026, `DECISIONI.md` §4.6-undecies.

⇒ ⛔ **Se non li prende, non è una rete: è un rituale.** ⭐ E il metro della fase non è *«quante prove
girano»*: è **che cosa la rete PRENDE**.

---

### ⚠ Quel che questa fase NON è

⛔ **Non è «scrivere più banchi».** Ce ne sono già più di cento, ⭐ e non sono serviti: i tre difetti
di oggi sono passati **in mezzo a loro**. ⇒ Il problema non è la quantità delle prove — è ⭐ **da dove
partono** (da zero, o da uno stato che funzionava già) e ⭐ **che cosa guardano** (il pixel, o il
processo).

⚠ **E non è una fase di ceremonia**: se alla fine la rete non ha preso niente che l'occhio non
avrebbe preso, **la fase è fallita**, e va detto.

---

## Fase 12 — KDE

⚠ *Era la **fase 10** fino al 16 agosto 2026: il multi-tenant le è passato davanti, e la ragione sta
nel riquadro della fase 10. **La fase non è cambiata di una riga** — è cambiato il suo posto.*

**Produce**: il secondo desktop.

**L'utente vede**: la stessa cosa su Plasma.

> ## ⭐⭐ E ADESSO C'È UNA RETE SOTTO — *e tre cose che questa fase eredita, misurate*
>
> ⭐ `[M]` 27 agosto: la fase 11 è chiusa, e il **solo rosso** che produce è proprio il mandato di
> questa fase — ⛔ **il prodotto sa avviare solo GNOME** (`src/sessione.c` · `scrivi_dropin()`, tutto `src/mutter.c`).
> ⇒ La rete misura già, oggi, se questa fase riesce: il giorno che `C1(kde)` diventa verde, KDE è
> servito davvero.
>
> ⛔⛔ **Tre cose da mettere nel piano di questa fase, o si saltano:**
>
> | | |
> |---|---|
> | ⭐ **un guasto suo** | `fasi/11-…` `fasi/11-la-rete-di-sicurezza.md` §3.6 lo impone: *«ogni desktop nuovo entra con almeno un guasto suo, inventato e fatto girare»*. I collaudi di oggi sono quelli che GNOME ci ha insegnato |
> | ⛔ **KWin non sa nascere cieco** | `[M]` con `--output-count 0` un'uscita la fa lo stesso ⇒ il disegno *«zero monitor propri»* **non si trasporta uguale**, e va ripensato qui |
> | ⚠ **il palco muore col cliente** | `[M]` il monitor virtuale muore con la connessione D-Bus del figlio. ⭐ Su GNOME `C6` misura verde (le finestre si ritrovano), ⛔ ma su un compositore diverso non è detto ⇒ `DECISIONI.md` §4.6-teretvicies |

> ## ⛔⛔ La motivazione PRESTAZIONALE di questa fase è caduta — *13 agosto 2026*
>
> *Qui stava scritto: «E qui si insegue il numero desiderato: KWin consegna più fotogrammi al
> secondo di Mutter `[M]`. La fase di KDE non è solo "servire più desktop": è la strada per i 60 a 4K
> e per il traguardo dei 40 ms».*
>
> ⚠⚠ **La fase resta, e resta giusta: è «il secondo desktop», ed è la ragione per cui era stata
> messa nel piano.** Quel che si toglie è **la promessa sul ritardo**, che si appoggiava a due
> fatti e nessuno dei due regge:
>
> | quel che la riga diceva | che cosa dice la misura del 13 agosto |
> |---|---|
> | «Mutter ne dà meno» | ⛔ **non si riproduce così**. Rinegoziando la sola cadenza (monitor 120, freno 90) Mutter consegna `[M]` **quanto KWin**. Il numero di v1 non è una proprietà del compositore; ⚠ che sia il resto di una divisione troncata è `[R]`, letto nel codice e non misurato (`STUDI.md` §gnome §8.2) |
> | «è la strada per il traguardo dei **40 ms**» | ⛔ **no.** Nel ritardo misurato cattura → vetro `[M]` Mutter pesa poco: **il grosso è nostro**, nel tratto cattura → primo byte, **dominato allora dal codificatore in software**. ⇒ Cambiare compositore **lascerebbe intatta la codifica** |
>
> ⇒ ⛔ **Chi arriva a questa fase aspettandosi che porti il ritardo dentro il tetto resterà deluso**,
> e va scritto qui perché nessuno ci conti sopra pianificando: il ritardo **non si cura cambiando
> compositore** (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> > #### ⛔⛔ E LA DOMANDA APERTA HA AVUTO RISPOSTA — *e la mezza promessa qui sopra è caduta anche lei, 16 agosto 2026*
> >
> > *Qui stava scritto: «⏳ `[?]` **Resta aperto e non è stato misurato** quanto scenderebbe il numero
> > con un codificatore **hardware**: è la domanda della fase 8, non di questa» — e, un rigo prima,
> > «il ritardo si cura **sulla codifica**, ed è la **fase 8**».*
> >
> > ⭐ **Misurato**, perché la codifica in hardware è entrata nel prodotto il 13 agosto, e la
> > risposta sta in `fasi/rapporti/F3-E-anello-rimisurato.md`. ⛔ **Ed è a due facce**:
> >
> > | | `[M]`, stesso palco, notte del 14 agosto — i valori nel rapporto |
> > |---|---|
> > | ⭐ **il tratto della codifica** | si dimezza: il pezzo ha ceduto per intero, come il piano sperava |
> > | ⭐⭐ **i fotogrammi consegnati** | ⭐ **il doppio**. È la lezione di `LEZIONI.md` §6.2 applicata e **passata**: senza questo numero il guadagno sulla codifica sarebbe stato metà della notizia |
> > | ⭐ **e gli altri quattro tratti restano dove sono** | ⇒ **l'architettura è assolta**: tolta la codifica, non è emerso niente di nascosto |
> > | ⛔⛔ **ma il TOTALE non è sceso** | il codec che rende possibile l'hardware **sposta tempo sul client** — l'attesa del fotogramma dalla GPU, che per un giorno si è chiamata «il disegno» |
> >
> > ⇒ ⛔ **Il collo di bottiglia si è SPOSTATO, non è sparito**, e adesso sta nel client, mentre la
> > codifica costa ormai poco. ⭐ E si vede solo perché i tre giri esistevano tutti e tre: con due
> > soli si sarebbe letto *«vittoria»* oppure *«l'hardware non serve»*, e **sono tutt'e due
> > sbagliate**.
> >
> > ⇒ ⛔⛔ **La lezione, e vale per tutto il piano**: *«il ritardo si cura sulla fase N»* era vera
> > **sul pezzo** e falsa **sul totale**. Il collo di bottiglia più grosso è stato tolto per intero,
> > e il ritardo che l'utente sente non è migliorato — è raddoppiato il **ritmo**, che è un'altra
> > grandezza. ⚠ Chi scrive la prossima riga che promette un tetto da una fase sola la scriva
> > sapendo questo.

⭐ **E qui si guadagna comunque una cosa che vale**: KWin consegna la cadenza piena `[M]` senza che
gli si debba rinegoziare niente, mentre su GNOME lo stesso risultato richiede una
cadenza che **il prodotto oggi non sa chiedere** (`DECISIONI.md` §2.5-bis). ⚠ È un guadagno sul
**ritmo**, non sul **ritardo**: sono due grandezze diverse, e `LEZIONI.md` §6.2 esiste perché sono
già state confuse.

**Si riusa**: `kwin.c` (822 righe), `appunti_wlr.c` (796).

⚠ Le trappole sono già scritte in `STUDI.md` §kde: `XDG_MENU_PREFIX` senza cui il cancello della cattura
non si apre; niente `InaccessiblePaths=` nel drop-in.

> ### ⛔⭐ E UNA TRAPPOLA È USCITA DAL PIANO IL 17 AGOSTO 2026 — `DECISIONI.md` §5.1-bis
>
> Qui c'era la terza: *«il ridimensionamento **nella forma della negoziazione**, con la guardia
> contro il ciclo infinito che non si vede su Trixie e compare il giorno dell'aggiornamento a
> 6.8»*. ⛔ **Non è più lavoro di questa fase**, perché non è più lavoro di nessuna: il
> ridimensionamento a caldo è uscito dal prodotto — *«non voglio mettere delle eccezioni nel
> progetto»* — ed è uscito **proprio per non avere un ramo KDE diverso da quello GNOME**.
>
> ⚠ **Quel che questa fase deve ancora fare, e che non è la stessa cosa**: rispondere
> `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` all'`ADATTA_TELA` che il client manda **all'attacco e al
> riattacco**, così che la pagina riscali e lo dichiari (`SPECIFICHE.md` §6.3). ⭐ E su KDE è il **caso normale**,
> non il ramo povero: KWin ≤ 6.7.4 prende la misura dalla riga di avvio (`--virtual --width W
> --height H`) e non la cambia più. Il percorso di codice esiste già ed è provato sull'ospite
> finto (caso 11 di `banchi/04-b31`).
>
> ⭐ **Il guadagno del taglio si vede qui**: la fase 11 non deve più portare una funzione, deve
> solo dichiarare un rifiuto — e la guardia contro il ciclo infinito di `kwin!7932`, che sarebbe
> stata un difetto invisibile su Trixie e vivo dopo l'aggiornamento, non ci riguarda più.

---

## Fase 13 — XFCE e LXQt

⚠ *Era la **fase 12** fino al 25 agosto 2026: **la rete di sicurezza** le è passata davanti
(`DECISIONI.md` §4.6-duodecies). **La fase non è cambiata di una riga** — è cambiato il suo
posto, come già il 16 agosto.*

⚠ *Era la **fase 11** fino al 16 agosto 2026 — stesso spostamento della 11, stessa ragione.*
⛔ **E qui una trappola di lettura**: `STUDI.md` §xfce e `STUDI.md` §lxqt portano in testa *«per la fase 11»*, ma
quella è **la fase 11 di v1** — sono studi dell'8 agosto 2026, scritti prima che questo piano
esistesse. ⇒ Il numero in quei due titoli **non è questo numero**, e non va inseguito.

**Produce**: il terzo e il quarto desktop, che condividono wlroots e quindi quasi tutto.

**Si riusa**: `appunti_wlr.c` già scritto per questa famiglia; le risposte alle quattordici domande
sono già in `STUDI.md` §xfce §12 e `STUDI.md` §lxqt.

---

## Fase 14 — Il registro

⭐ *Inserita il **21 settembre 2026**, per decisione dell'utente:*

> *«Attualmente la fase 14 riguarda l'installer, ma la spostiamo in fase 15, alla fase 14 inseriamo
> un sistema di logging serio, che ci siamo dimenticati di realizzare.»*

**Produce**: un sistema di registro serio: quello che serve a chi amministra il server per sapere
che cosa è successo, a chi, e quando, senza dover leggere il codice.

**Da dove si parte** `[R]` 21 set 2026: il registro di oggi è nato per **i banchi e per chi
sviluppa**, non per chi amministra.
- ⭐ C'è già **un imbuto solo**, `src/registro.c`: ogni riga ha l'istante e l'area (`avvio`, `quic`,
  `rcp`, `sessione`, `video`, `budget`…), e dalla fase 10 dice **di chi** parla. È anche quel che
  permette a B13.2 di garantire che la parola d'ordine non finisca in nessuna riga.
- ⛔ Le righe vanno tutte sull'uscita d'errore, e le raccoglie chi ha lanciato il programma. Non c'è
  un **livello** (errore, avviso, informazione): c'è solo «normale» e «parlantina».
- ⛔ Le righe sono scritte **per chi sviluppa**: marche, rimandi ai documenti, gergo interno.

**Le domande da porre all'utente all'apertura della fase** — ⛔ nessuna è decisa:
1. **chi legge** il registro: l'amministratore del server, chi fa assistenza, o tutti e due?
2. **dove va**: il giornale di sistema (`journalctl -u remotix`), un file suo con la rotazione, o
   tutti e due?
3. **i livelli**: quanti, e quale si vede di serie;
4. **il registro degli accessi**: chi è entrato, da dove, quando, e chi è stato respinto e perché.
   È una cosa distinta dal registro di diagnosi, e ha domande sue (per quanto si conserva);
5. **la lingua** delle righe per l'amministratore.

**Il banco**: ⛔ le maglie della rete leggono il registro di oggi (le righe «input id=…», i
testimoni). ⇒ Cambiare il registro senza la rete sotto vorrebbe dire romperle senza saperlo: le
maglie si adeguano **nella stessa modifica**, e la rete completa gira dopo ogni incremento.

---

## Fase 15 — Il servizio

⚠ *Era la **fase 14** fino al 21 settembre 2026: il registro le è passato davanti, per decisione
dell'utente.*

> ### ⏳ ⭐ LE DUE COSE IN SOSPESO DOPO LXQt — *l'utente, 21 settembre 2026*
>
> *«Una volta completato LXQt rimangono 2 cose in sospeso: il discorso degli utenti che devono
> appartenere ai gruppi render/video e la procedura di installazione di Remotix.»*
>
> | | dove sta oggi |
> |---|---|
> | **i gruppi `video`/`render`** | ✅ deciso e scritto il 20 set 2026, `DECISIONI.md` §7.21: `provisiona.sh` all'installazione, il prodotto alla prima connessione. `[M]` solo sulla scatola `kde`. ⛔ **ANTICIPATO: una sessione apposita PRIMA di LXQt** — *«deve funzionare per tutti i DE, non solo per KDE»* (l'utente, 21 set 2026) |
> | **la procedura d'installazione** | è il cuore di questa fase: *«confezionamento, installazione»* qui sotto |

⚠ *Era la **fase 13** fino al 25 agosto 2026, per lo stesso scalo.*

> ### ⛔⛔ E UNA COSA DA FARE QUI È GIÀ MISURATA — *25 agosto 2026*
>
> ⭐⭐ **SMENTITO DALLA MISURA DEL 29 SETTEMBRE 2026** (`fasi/17-l-installatore.md` §5.2, T2): dieci
> prove con Firefox vero sui quattro desktop — fermare l'unità (`KillMode=mixed`), uccidere il solo
> padre, uccidere il solo figlio — **nessun desktop muore**: muoiono padre, aiutante PAM e figlio; il
> palco (partito con `setsid --fork`, fuori dall'unità), la sessione e i programmi sopravvivono, e al
> riattacco torna lo stesso compositore con le finestre. Il fatto del 25 agosto oggi non si riproduce.
>
> `[M]` **Fermare l'unità del server porta via TUTTE le sessioni degli utenti**, finestre
> comprese: la sessione grafica vive nel suo albero di processi (`KillMode=mixed`). ⇒ ⛔ **Oggi
> aggiornare il server significa buttare fuori tutti** — lo stesso danno che `DECISIONI.md` §4.7
> vieta a chiunque di provocare spegnendo la macchina.
>
> ⭐ `SPECIFICHE.md` §5.2 promette *«la sessione sopravvive al CLIENT»*, ed è vero e misurato.
> ⛔ *«Sopravvive al server»* **non era mai stato promesso, e non è vero.** ⇒ Il confine è ora
> tracciato lì, e **questa è la fase che lo deve spostare**: aggiornare senza fermare nessuno.
>
> ⚠ Il rilievo per intero: `fasi/10-multi-tenant-e-il-budget.md` **§7.5**.

**Produce**: unità systemd, confezionamento, installazione, il certificato generato all'avvio,
la limitazione dei tentativi.

⭐ **E qui il client web si ripaga la seconda volta**: la pagina sta **dentro lo stesso pacchetto**
del server. Niente APK, niente store, nessuna versione del client da inseguire — ⛔ e nessun caso
«client vecchio contro server nuovo», che è precisamente quello che `RCP.md` §9 dice di temere.
Il client si aggiorna **ricaricando**.

⚠ **Con un caso che resta e va provato**: la **scheda già aperta** mentre il server viene
aggiornato. Lì il client vecchio contro il server nuovo esiste davvero, per il tempo di un
ricaricamento — ed è il solo posto dove la negoziazione di versione serve a qualcosa.

**Il banco**: ⛔ **il ripristino si prova riavviando**, non rileggendo lo script. In v1 il primo
riavvio vero ha mostrato che mancavano due pezzi, e nessuno dei due era nei documenti: il disco che
non si montava da solo, e i pacchetti installati a mano mesi prima che il provisioning ereditava
senza dichiararli (`LEZIONI.md` §2.5-bis).

> ### ⛔⭐ E qui si fa la pulizia: la funzione di banco non entra nel pacchetto — ✅ 11 agosto 2026
>
> *Decisione dell'utente, `DECISIONI.md` §7.16: «l'utente deve vedere il desktop senza artefatti,
> come se fosse davanti al monitor del PC … si tiene quello che serve per i test, ma poi nel
> prodotto finale si fa pulizia». ⚠ **Scritta qui, undici fasi prima di servire**, perché è la forma
> di decisione che si perde: vale alla fase 13 e viene decisa alla 1.*
>
> ⛔ **Il binario che si installa non contiene la funzione di banco di `RCP.md` §7.5** — i due tipi
> `BANCO_MARCA` e `BANCO_ESITO`. Non spenta: **assente**, non compilata, non raggiungibile.
>
> ⛔ **E si misura, o è una buona intenzione**: *«non c'è»* e *«c'è ed è spenta»* hanno lo stesso
> aspetto da fuori. Il banco di questa fase **cerca le marche dentro il binario del pacchetto** e
> pretende di **non** trovarle — con il controllo positivo che dice che lo strumento sa trovarle,
> cioè le stesse marche cercate nel binario **di prova**, dove ci sono. È la tecnica già scritta in
> `banchi/01-p1-prodotto.sh` della fase 1, che distingue un binario nuovo da uno vecchio con otto
> marche e due controlli.

---

# ⛔ BINARIO B — sciolto il 9 agosto 2026

*Erano cinque fasi — A1-A5, il client Android in Kotlin. `DECISIONI.md` §1.6 le ha cancellate: il
client è una pagina web, e non c'è più un secondo prodotto da costruire.*

⛔ **Ma niente di quel che quelle fasi dovevano fare è sparito insieme a loro.** Questa tabella
esiste perché nessuno lo perda, ed è l'unico posto in cui è scritto dove è finito ciascun pezzo:

| Fase sciolta | Dove è finito il suo lavoro |
|---|---|
| **A1** — il filo su Android | **fase 1**: la pagina *è* il client, e la stretta di mano si scrive una volta sola. Il mestiere di secondo lettore passa al **cliente di prova** (§1.1 *(di questo documento)*) |
| **A2** — il video, MediaCodec | **fase 2**, con `VideoDecoder` al posto di MediaCodec — e la domanda *«il telefono ce la fa?»* la risolve la sonda (§1.2 *(di questo documento)*, misura **S2**) |
| **A3** — mouse e tastiera, il modo classico | **fase 4**, che diventa la fase dove si scrive **l'interfaccia classica della pagina**: `Pointer Lock` al posto di *Pointer Capture*, e le scorciatoie con il loro limite dichiarato (`SPECIFICHE.md` §7.3-bis) |
| **A4** — il tocco e la tastiera a schermo | **fase 4** anch'essa, come **seconda disposizione della stessa pagina**: i sette gesti restano quelli, e il passaggio fra le due resta **automatico sul contesto** (`DECISIONI.md` §5-bis.0-bis) |
| **A5** — la vita dell'applicazione | ⚠ **si sparpaglia, e una parte va sorvegliata**: la migrazione QUIC da WiFi a rete mobile è **fase 9** (è la ragione migliore per cui QUIC è stato scelto); il riattacco è **fase 5**. ⛔ **Quel che cambia natura è lo sfondo**: una scheda del browser che finisce dietro viene rallentata o congelata dal sistema, e non è più un ciclo di vita che governiamo noi — è una cosa da **misurare e dichiarare** |

⭐ **E DeX non sparisce come caso di prova** (`DECISIONI.md` §5-bis.0): resta il posto in cui il
ridimensionamento della finestra viene esercitato sul serio, perché la finestra si trascina. Cambia
che a trascinarla è il browser.

---

## L'ordine, e perché

**Il filo prima del contenuto** (1 prima di 2): un canale che non si sa aprire non si sa nemmeno
riempire, e i difetti di protocollo trovati con dentro il video sono tre volte più cari.

**Il software prima dell'hardware** (2-3 prima di 8): con la codifica accelerata dall'inizio, un
difetto d'immagine ha due sospetti invece di uno.

**La sessione dopo il movimento** (5 dopo 3): la persistenza è la cosa più difficile del progetto,
e affrontarla prima di avere qualcosa da guardare significa non sapere se il palco regge.

**Un desktop solo fino alla 9**: gli altri tre si aprono quando la catena è chiusa, altrimenti si
inseguono differenze di compositore e difetti nostri nello stesso momento.

⛔ ~~**Android dopo la 9**~~ → **Android non c'è più** *(9 agosto 2026)*. La ragione che lo
spostava in fondo — *«le prove su Android costano dieci volte quelle su Linux»* — è stata risolta
alla radice invece che riorganizzata: **non esiste più un secondo prodotto da provare**. Il
mestiere di secondo lettore resta al **cliente di prova** della fase 1, che è più economico e ha la
proprietà che conta: **è scritto dalla specifica, non dal codice**.

⭐ **E una cosa arriva prima di tutto il resto, che prima non c'era**: la **sonda del browser**
(§1.2 *(di questo documento)*). Non perché sia urgente in sé, ma perché **decide che cosa si scrive**: la libreria QUIC
dipende da WebTransport, il predefinito del certificato dipende da una misura, e quel che la pagina
deve dichiarare spento dipende dal motore. Una fase che comincia prima di quelle risposte scrive
codice che poi si butta.

---

## Il metodo, in sei righe

1. Il documento di fase si apre **prima** di sviluppare, e contiene il banco.
2. Il banco si certifica **prima** di essere creduto — e **si fa revisionare per primo**, prima
   del prodotto.
3. Si prova a **rompere**, non a confermare. Una revisione verde è «non ho trovato niente».
4. Quel che non ha funzionato si scrive **anche** quando fa una brutta figura.
5. Un rilievo si chiude con **una misura**, non con una discussione.
6. La fase si chiude quando **l'utente ha guardato e ha detto la sua** — non quando il documento è
   pieno.

---

# ⏳ PUNTO DI RIPRESA — 22 agosto 2026, **sera**

*La giornata del 22 agosto: **nove agenti in due ondate**, il coordinatore alla fusione e al
collaudo. ⭐⭐ **La fase 8 aperta e chiusa in un giorno**, sul giudizio dell'utente. E le fasi 6 e 7
restano senza nessun difetto vero aperto.*

## ⭐⭐⭐ Che cosa è cambiato per l'utente

> *«Il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»* · **«per me è ok»**
>
> *Al mattino, sulla stessa scena:* *«la distanza fra freccia e finestra è la metà della barra del titolo»*.

| | |
|---|---|
| l'anello **`input → vetro`** | **accorciato**, **appaiato** — due giri che condividono tutto tranne il binario |
| il distacco, **nell'unità dell'utente** | si **avvicina al locale** |
| ⭐ e il **locale** adesso è misurato | ⇒ *«non identica: quello è impossibile»* è confermato dalla misura |
| ⭐⭐ **i fotogrammi DIPINTI** | **salgono**. Non è una vittoria di cronometro |

⇒ I valori stanno in `fasi/08-l-anello.md`.

## ⭐ Quel che è chiuso, e non si riapre

| | |
|---|---|
| **fasi 6 e 7** | ⭐ nessun difetto vero aperto |
| **fase 8** | ✅ **CHIUSA il 22 agosto**, `fasi/08-l-anello.md` |
| **fase 9** | ✅ **CHIUSA il 24 agosto**, `fasi/09-la-qualita-e-la-degradazione.md` — e le cinque cure sono **accese** |
| **`RCP.md` §5.2 e §6.2** | ✅ le due `[?]` chiuse con la misura: `EncSliceLP` **non** sa fare i sotto-livelli temporali · la chiave alla tela dell'utente sta **largamente dentro** il tetto |
| **il «puntatore doppio»** | ✅ **non esiste** — smentito dall'occhio dell'utente, e l'agente fermato dopo pochi minuti |
| **i motori** | Linux Chrome ✅ · Linux Firefox ✅ · Windows Chrome ✅ · Android Chrome ✅ · ⛔ Android Firefox fuori · ⚠ **Firefox su Windows: NON PROVATO** |

## ⛔ E i quattro difetti veri trovati in fase 8 — **nessuno era il bersaglio**

la **chiave abbandonata** (`RCP.md` §5.2 la vieta, ed era la spirale) · la **scala delle ricodifiche corta di
uno scalino** · il **passo non multiplo di 64** che dava un desktop **inclinato senza errori, coi
millisecondi già perfetti** · e il **cronometro del prodotto che misurava il banco**.

## ⛔⛔ Le tre lezioni nuove — `LEZIONI.md` §1.26 · §1.27 · §1.28

1. **Due banchi sulla stessa MACCHINA si falsano in silenzio.** §1.24 parlava di quel che si
   *ammazza*; questa di quel che **non** si ammazza — e non dà un rosso, dà **un numero plausibile**;
2. **Il colore medio è cieco**: un'immagine sbagliata a ogni riga ha **le stesse statistiche** di
   quella giusta. *Un controllo deve leggere una cosa che si può sbagliare, non una che si può mediare*;
3. ⭐⭐ **Due banchi che non concordano possono avere ragione tutti e due**: misurano due grandezze
   diverse. ⇒ **E l'occhio dell'utente aveva ragione**: i banchi guardavano un pezzo più corto
   dell'anello vero, e il pezzo mancante era invisibile **perché la loro mano è finta**.

## ⏳ I punti aperti — nessuno è un difetto

1. ⛔ **il muro di Mutter**: `[M]` un quadro a 60 Hz — non si è mosso in tutta la fase, e **non
   l'ha toccato nessuno**;
2. ⛔ **metà del guadagno della fase 8 non è spiegato**: sta in un tratto che la copia zero **non
   attraversa**. `[?]` Ipotesi dichiarata, non misurata;
3. ⚠ **la ritenuta del `pw_buffer` è in vigore senza prova**: il controllo positivo non ha
   riprodotto il danno. Prudenza, non necessità;
4. `[?]` **il modello del distacco ha predetto male due volte, in versi opposti**. È un fatto sul
   modello, **non sull'utente**, ed è lavoro nostro;
5. **il datagram su rete non locale** e la **priorità del percorso audio** (`nice`);
6. **la misura `AV`** da riprendere con l'`aoff` curato — per accorgersi se il ritardo torna;
7. **il 4/18 del 16 agosto** non riprodotto: due cause escluse con la misura, resta una corsa da
   setacciare;
8. `[?]` **il desktop immortale** — letto nel codice, non misurato;
9. `[?]` **su DeX lo schermo risponde col monitor esterno o col telefono?** Serve il telefono dell'utente;
10. **Firefox su Windows**, mai provato;
11. ⚠ **il tetto dei 50 ms non è verificato**, e non perché manchi poco: **il numero della fase 8
    sta su un confine diverso**. I due numeri **non si confrontano** — `LEZIONI.md` §1.28 applicata a noi stessi.

## 🔸 Le decisioni che aspettano l'utente

- 🔸 **la tela multipla di 16** (`rcp_misura_ammessa()`): renderebbe la copia zero valida su **ogni**
  schermo, ⛔ ma è una **modifica al protocollo** — `RCP.md` §4.5 oggi pretende solo i lati pari;
- 🔸 **il `nice` a tutto il percorso audio**;
- 🔸 **si apre o no un difetto a monte in Mutter?** (fase 6 §7.1-bis) — azione verso l'esterno;
- 🔸 **il DeX** col suo telefono;
- 🔸 **`BANCO_MARCA`/`BANCO_ESITO`**: completare il ramo o togliere i due tipi;
- 🔸 ~~**al congedo il palco a misura di riposo?**~~ — **provvisoria**, si lascia com'è
  (`DECISIONI.md` §5.0-septies). *«Per il momento accetto, ma poi ci penserò su.»*

## ⚠ Pulizia da fare prima del prossimo giro

⛔ **Quattro server di prova degli agenti sono rimasti accesi** sulla macchina (porte **7746, 7752,
7765-67, 7775**), e girano da `root`. Non danno fastidio a riposo, ⚠ **ma falserebbero la prossima
misura** — che è precisamente l'errore di `LEZIONI.md` §1.26. **Vanno spenti prima di misurare.**

⭐ Vivi e voluti: **7730** (dell'utente) e **7790** (il prodotto con la fase 8 dentro, che l'utente
ha giudicato).

> ✅ **CHIUSA il 23 agosto 2026**: dopo il riavvio e la riprovisione la macchina aveva **una sola
> porta 7xxx aperta, la 7900** — verificato con `ss -tuln` **prima** di misurare.
> ⚠ E la regola che ne è uscita, pagata due volte nella giornata (`fasi/09` `fasi/09-la-qualita-e-la-degradazione.md` §3.17): fra due banchi
> sullo stesso utente **si verifica che il posto sia libero** — nessun cliente vivo **e** nessun
> palco — ⛔ **non si conta il tempo**. Un palco orfano non dà un rosso: dà **un numero plausibile**,
> e quel giorno stava per far accusare tre cure innocenti.

## Come si riparte

```
# il prodotto con la fase 8 dentro
ALBERO=/media/REMOTIX/src/08-prova-src LAV=/media/REMOTIX/tmp/08-prova \
  bash banchi/07-b41-accendi.sh --porta 7790 --hz 0

# il metro dell'utente: il distacco freccia↔finestra, in barre del titolo
python3 banchi/08-b67-elastico.py --certifica      # 13 guasti innestati su 13

# l'anello intero, e ⛔ VA IN ROSSO se la macchina non e' scarica
python3 banchi/04-b30-anello-input.py --certifica  # 57 su 57, 18 guasti su 18
```

⚠ **Due trappole che hanno morso oggi**: il posto della sessione è **uno** e quello di prima resta
attaccato una ventina di secondi · e ⛔ **non si misura in due sulla stessa macchina** (`LEZIONI.md` §1.26).
