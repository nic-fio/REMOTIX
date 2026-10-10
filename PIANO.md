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

## Phase 3 — Movement ✅ **CLOSED on 14 Aug 2026**

> ### ⭐⭐⭐ CLOSED ON THE USER'S JUDGEMENT — *«abbastanza fluido, non il massimo ma pur sempre fluido»*
>
> | | |
> |---|---|
> | **the number** | the delay loop measured with encoding **in hardware** and with AV1 in software, which is the configuration **judged** — the values are in `FASI.md` §03-movimento |
> | ⭐ **the architecture** | **ACQUITTED**: removing hardware encoding the encoding segment gives way and **the other four segments do not move** |
> | ⭐ **hardware encoding** | **in the product**, not on a copy: the keyframe gets much shorter, the rhythm **doubles** |
> | ⛔ **the ceiling** | it **EXCEEDS** the 50 ms, and **would exceed it even with free encoding** |
> | ⛔⛔ **the new bottleneck** | ⚠ ~~**the DRAWING**~~ ⇒ ⛔ **CORRECTED on 14 Aug 2026** (decided by the user, on two independent measurements of phase 4): **drawing costs little `[M]`**; what was attributed to drawing was **the WAIT for the frame from the GPU** plus the drawing — an HEVC frame in hardware comes out opaque and the bench's reading of the mark causes its transfer. `fasi/rapporti/F4-A2-pagina-dipinge.md`, `F4-A10-anello-input.md` |
>
> ⛔ **And the three limits of the judgement are written in `FASI.md` §03-movimento, not kept quiet**: it is on AV1
> in software; HEVC in hardware **cannot be judged** because the user's browser does not paint it;
> and the user **did not see a desktop** but an added monitor with the benches' scene inside.
>
> ⭐⭐ **And the judgement produced two defects that no bench had found** — HEVC that does not
> paint in the real session, and the product that **adds** a monitor instead of showing the
> desktop. ⇒ *It is exactly the value the plan attributed to the judgement, and it came true in
> thirty seconds.*

> ### ⭐⭐⭐ HARDWARE ENCODING IS BROUGHT FORWARD HERE — decided by the user on 13 Aug 2026, evening
>
> *And phase 3 **does not close** until it is done.*
>
> ⛔ **The reason, and it is not an opinion: it is a measurement.** The breakdown of the delay loop
> measured on 13 Aug says that **more than half** lies in the **capture → first byte** segment, that is in
> encoding **in software**; Mutter, drawing, decoding and the wire do not change with
> acceleration. The values are in `FASI.md` §03-movimento.
>
> ⇒ **As long as encoding is in software, every delay number that phases 3-7 produce is dominated
> by a piece about to be replaced** — and it would have to be redone afterwards. It is the user's objection,
> and it is right: *«senza accelerazione hw stiamo ragionando e sviluppando su numeri non molto
> affidabili»*.
>
> ⭐⭐ **And it can be done, `[M]` verified on 13 Aug 2026 on the server:**
>
> ```
> Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 and renderD129
> VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
> VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← and even 4:4:4 at 10 bit
> ```
>
> ⚠ *An agent had reported «on this server there is no hardware encoder for either of the two
> codecs». **It is true for AV1** — and it was already in the documents — **and it is FALSE for HEVC**, which is precisely
> what phase 8 promises. Nobody had verified it: the line was repeated, not measured.*
>
> ⭐ **And it costs little to do it now**, for a precise reason: the chain that moves **exists as of
> today**, the loop bench is written, the scene and the mark are certified. ⇒ The *before* and the
> *after* are measured with **the same tool and the same scene**, so the two numbers **really
> subtract** — which would no longer be true three phases from now.
>
> ⛔ **What is brought forward, and what is NOT**: **only hardware encoding** is taken. **Zero
> copy** stays at phase 8, it is its work and it does not touch this number.
>
> ⚠ **And phase 8 does not disappear**: it stays with zero copy, and with its lesson that holds here too —
> *«one measures the frames delivered, not the milliseconds of CPU»*. In v1 the cost per frame
> dropped a lot **while the frames delivered were dropping** (`LEZIONI.md` §6.2).
>
> ⏳ **The work starts in a new session** (decided by the user). The resume point is in the
> `README.md`.
>
> ---
>
> ### ⭐⭐⭐ 13 Aug, evening — **THE TARGET IS CONFIRMED AT BOTH ENDS, and one obstacle was not there**
>
> *The plan for the new session was reread **before an agent started**, and checked
> by measuring instead of remembering. Three lines came out of it that change the work.*
>
> **1. ⛔⛔ Hardware AV1 encoding DOES NOT EXIST on this machine** — `[M]`, 3 rounds out of 3: the
> encoding test comes out with *«No usable encoding profile found»*, and `vainfo` gives AV1 as **decode
> only** on both nodes. ⚠ The encoder **appeared** in the library's list:
> *a list says that the code is there, not that the machine can do it*.
> ⇒ ⭐ **Staying on AV1 means staying in software forever.** HEVC (and then H.264) is not a
> preference: on the server side it is **the road to hardware**.
>
> **2. ⛔⛔ The obstacle «no client accepts HEVC» was a FLAG of the bench**, not a stage.
> `[M]` A/B with a single variable: without `--disable-gpu` the bench's Chrome sees the GPU and says yes
> to HEVC; with the flag it says no. ⭐ And it **really paints** an HEVC flow encoded on the card: 5 rounds out of 5,
> 1920×1080, 119 frames out of 120, `powerEfficient: true`.
> ⇒ **The lane that was supposed to open the session is cancelled**, and the critical path becomes
> *encoding → loop re-measured*, with no branches that could block it.
>
> **3. ⭐ Encoders are compared at equal bitrate and with the output frames COUNTED** —
> the measured comparison is in `FASI.md` §03-movimento. ⚠ The first round of that probe **was not a
> comparison and the bench said so by itself**: at free bitrate VP9 delivered **far fewer bytes**.
> *«Faster» at a fraction of the work is not faster.*

**It produces**: one stream per frame, abandonment with `RESET_STREAM`, the cadence.

**The user sees**: the desktop **moving**, and says whether it is fluid.

**The bench**, and it is the heart:
- ⛔ **the scene is declared and always moves** — a full-screen client that redraws at every
  compositor callback. All the rhythm measurements of phases 3-9 of v1 were thrown away for
  this (`LEZIONI.md` §1.1);
- **the frames delivered to the user**, not the ones processed. The number that in v1 nobody had
  ever counted, and which was 18 while something else was being optimised;
- ⭐ **the delay loop**: the client sends an input that changes the screen's colour and watches the
  decoded frames until it sees it. Measured **from the receiving side**
  (`DECISIONI.md` §2.6). ⛔ **And here S4 arrives too**, the measurement of the delay of *drawing* in the
  browser, which §1.2 put in the probe: without encoding, transport and decoding it cannot be executed
  *(9 Aug 2026, finding **R3.4**)*. Its seven checks and the **blind piece** — the segment between
  drawing and the lit pixel, which no API sees and which **is declared next to every number** —
  are in `STUDI.md` §web §6.3.

**The numbers to reach**: delay ≤ 50 ms, target 40 (`SPECIFICHE.md` §3.2).

> ## ⛔⛔ 13 Aug 2026 — the experiment is DONE, and the outcome was not one of the two foreseen
>
> *Here it was written: «on GNOME the 40 ms target is probably not reached, because of the wall
> of Mutter's cadence; if the measurement confirmed it it is not a defect of ours — and it is one more
> reason for the KDE phase». And next to it: «before declaring it, the decoupled cadence is tried…
> if it succeeds, GNOME enters the target; if it does not, the wall becomes `[M]`».*
>
> ⛔ **The outcome is neither «it succeeds» nor «it does not». It is: «it succeeds with a different number, and the product does not
> get there» — and meanwhile the delay was measured elsewhere, and the fault is ours.** The three halves:
>
> | | |
> |---|---|
> | ⭐ **the decoupled cadence SUCCEEDS** | `[M]` monitor **120** + brake **90** ⇒ Mutter delivers the full cadence — cell **D**, clean. ⚠ **But M3 of `STUDI.md` §gnome §13 is NOT closed: it is half closed**, because the cause is not measured |
> | ⛔ **but the written cause was wrong, and the new one is `[R]`** | not a **beat** between two clocks but a **quantisation** — `min_interval_us = 10⁶/maxFramerate` truncated to an integer (16666 for 60) against a tick of 16666.67 µs — ⛔ **read in the code, not measured**. And the discrepancy written before **does not reproduce** on the low cell |
> | ⛔⛔ **and the product does not get there** | `MOVIMENTO_FPS 60` is a compile-time constant (`src/figlio.c` · `MOVIMENTO_FPS`), `main.c` has no cadence options, **`RecordVirtual` does not take the frequency** (`src/mutter.h` · the note on `RecordVirtual`): the four virtual monitors are all **@60**. It is `[M]` **on the bench** and **zero in production** |
>
> ⛔ **And the delay, which is the number the phase existed for, EXCEEDS** the 50 ms ceiling `[M]`
> (capture → glass, blind piece **excluded**; the values in `FASI.md` §03-movimento). ⛔⛔ **But the wall
> is not Mutter's**: its part is small, **the bulk is ours**, and it lies in the capture →
> first byte segment, dominated by the **software encoder**. ⇒ The cure is **phase 8**, not 10
> (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> ⚠ **And 60 is not 40 ms**: cadence is not delay (`LEZIONI.md` §6.2). The 60 frames
> remove an obstacle; the number is made by the delay.
>
> > ⛔⛔ ⚠ *The second row of the table said: «Law on **13 points**, 8 confirm, 0
> > disprove», and the first gave **M3 as closed**. **Both false**, and corrected on the evening of
> > 13 Aug 2026 (finding of the phase 3 coordinator, verified on the outcome files): the file
> > `banchi/03-b14-esiti-griglia.jsonl` carries **only two cells**, both with
> > `scena_sul_mio_monitor: **false**` ⇒ rejected by the bench itself, which prints «⛔ la legge NON
> > regge su **0 punti su 0**». ⇒ **The renegotiated full cadence remains an `[M]` fact; the why goes back to `[R]`; M3 remains
> > half closed.** ⭐ And the reason for the rejection is trap no. 1 of `LEZIONI.md` §1.1 — the scene was not
> > on the monitor being captured — **come back to bite the result that cited it**: §1.1-bis.*

---

## Phase 4 — In command ✅ **CLOSED on 14 Aug 2026**

> ### ⭐⭐⭐ CLOSED ON THE USER'S JUDGEMENT — *«mi sembra ok»*
>
> *and, on the two optimisations he had asked for: «la situazione mi sembra migliorata, la comparsa
> del desktop è più immediata».*
>
> | | |
> |---|---|
> | ⭐⭐ **what he sees** | **he uses the desktop**: clicks, types, scrolls, moves windows. REMOTIX has stopped being a demonstration |
> | ⭐ **the phase's number** | the **input → glass** loop `[M]`, two independent rounds that agree — the values in `FASI.md` §04-si-comanda |
> | ⛔ **the ceiling** | it **EXCEEDS** the 50 ms, even before counting the two blind pieces |
> | ⛔⛔ **and no segment dominates** | six segments of similar weight ⇒ **no single cure brings the loop under the ceiling**: it is work for **phase 8** |
> | ⭐ **login → desktop** | drops a lot, and what remains is almost all **the fixed part of `RCP.md` §4.4-bis** |
> | ⭐⭐ **and the delay no longer grows** | before, it accumulated second after second (⛔ **with all counters green**); now it stays still |
>
> ⭐⭐ **And the user's judgement found SEVEN defects that none of the ten benches saw** —
> the added monitor, two servers of ours on the same session, the bar on GNOME's dock, the
> pointer capture, the failed stage kept forever, ⛔ and **a line of the coordinator's** that
> slowed the login. **Seven out of seven lay BETWEEN the pieces, none inside one.**
>
> ⛔ **And it closes with five things declared open**, put before the user **before** he
> judged: the delay that exceeds · the canvas that is not his (**36 % black band** on his 21:9)
> · the monitor always requested instead of checking whether there is one · a blind piece inside one of the segments
> · and **a single browser**. They are in [`FASI.md` §04-si-comanda](FASI.md#04-si-comanda).


> ### ⭐⭐⭐ THE FIRST WORK OF PHASE 4 IS THE **REAL DESKTOP** — decided by the user on 14 Aug 2026
>
> *And it is not a premise to the phase: **it is inside the phase**, at the top.*
>
> ⛔ **The reason, in one line**: phase 4 exists because *«the user **uses** the desktop»* — but
> **as long as the desktop is not visible, there is nothing to command**. The benches of the cursor, of the
> accented letters and of the shortcuts would have **nowhere to look**: they would be measured on an
> empty screen.
>
> **The defect, and the cure is in TWO places, not one:**
>
> > ✅ **CURED on 14 Aug 2026 (A1)** *(box added on 28 Aug, realigning to the code)*.
> > ⛔ The table below describes **how it was before the cure**, and it is in the present tense because it was
> > written as a mandate. Today the product does not ask for `--virtual-monitor` and **refuses** an
> > `ExecStart` that asks for it: `src/sessione.c`, the check on `vigore`.
>
> | | |
> |---|---|
> | `src/sessione.c` · the Shell's `ExecStart` | creates the session with `--headless --no-x11 **--virtual-monitor %ux%u**` ⇒ GNOME puts the shell **on that monitor** |
> | `src/mutter.c` · `RecordVirtual` | captures with **`RecordVirtual`**, which **mounts another one** and records that ⇒ **the user looks at the second, empty** |
> | ⛔ **and the second half of the cure** | `src/sessione.c` · the check on the `ExecStart` in force **rereads the `ExecStart` in force and DEMANDS `--virtual-monitor %ux%u`** ⇒ with the flag removed, the check **would fail**. *The check is right, the expectation is not* |
>
> ⭐ **The thesis is already PROVEN, on 14 Aug, without touching the product**: session of user
> `prova` started **without** `--virtual-monitor` (`GetCurrentState` → **0 monitors**, the session
> *«alive, complete and black»* of `STUDI.md` §gnome §3.1); with the client connected, `RecordVirtual` mounts
> **the only** monitor and ⭐ **the shell goes on it: bar, background, dock**. The proof is in
> `fasi/rapporti/F5-desktop-vero.md` and in the image
> `F3-verbali/desktop-vero-14ago.png` ⚠ *(removed from the disk like the reports; it is recovered with `git show dea834d --stat` and `git checkout dea834d -- <percorso>`)*.
>
> ⚠ **Two things to MEASURE before believing them, and they are not details:**
> 1. ⛔ **who decides the monitor's size** now that the session no longer gives it: it is given by
>    `RecordVirtual`, and **what happens if the client asks for another one?** It is `RCP.md` §4.5, the
>    granted canvas, and from here on it concerns this piece;
> 2. ⚠ **`PIANO.md` (this file, further up) and `STUDI.md` §gnome §108 say that `--virtual-monitor` is not
>    optional**. ⇒ **They must be rewritten**: they are true only for a session that must live **without
>    anybody capturing it**.
>
> ⚠ **And the user `prova` is kept** (decided on 14 Aug): it is the only place where today the real
> desktop is visible, because `nicfio` already has a session with a monitor of its own and `SPECIFICHE.md` §5.1 admits **only one
> per user**.

**It produces**: ⭐ **the real desktop** (above) · the input channel, the pointer drawn by the page, the letters and the positions —
⭐ **and the page's two layouts**, which is the work inherited from the dissolved phases A3 and A4: the
classic mode with `Pointer Lock`, and touch with the seven gestures, **with automatic switching on
context** and not a setting to go looking for (`DECISIONI.md` §5-bis.0-bis).

**The user sees**: ⭐ **he uses the desktop**. It is the moment it stops being a demonstration.

⛔ **And here one discovers what the browser keeps for itself**: `Ctrl+W`, `Ctrl+T`, `F11`. The page **MUST
declare** which shortcuts it cannot deliver on that engine, instead of letting one believe they
arrived (`SPECIFICHE.md` §7.3-bis). ⚠ The measurement is the probe's **S3**, and it must be done on at least
two engines: what is lost on Chrome is not what is lost on Safari.

**The bench**:
- ⛔ **the desktop cursor must not appear in the image**: one looks at a frame. And on
  wlroots one verifies that the transparent theme was **loaded**, not just written — a theme
  that loads zero cursors makes it fall back to a visible one (`SPECIFICHE.md` §7.1);
- an accented letter typed in a session with the right layout, and one in a
  session with the wrong layout: the second **must** end up in the log as not
  producible, not come out different;
- `Ctrl+C` that copies instead of typing a c.

⛔ **And here one discovers that the cursor does not arrive at all**, which makes `CURSORE_FORMA` (`RCP.md`
§7.2) a channel without a source: on Mutter we ask for `cursor-mode=2` — that is «give me the cursor
as metadata» — **but we do not ask for `SPA_META_Cursor`**, so shape, position and hotspot
are not delivered `[R]` (`STUDI.md` §gnome §1.1 point 6 and §5.2). To be requested here, where the channel
is born. ⭐ **The direction is the right one for us**: clean pixels in the image *and* the shape in a side
band, which is exactly what the pointer drawn by the client needs.

⚠ **Two silent replacements by libei**, which bite here and at phase 6: a **keymap** change
destroys and recreates the keyboard device, a **geometry** change all the absolute
devices — and the pointer to the old device stops working **without error** `[R]`
(`STUDI.md` §gnome §9). Keymap and regions are reread at **every** `DEVICE_ADDED`, not once at startup.

**Reused**: `input.c` (906 lines, libei), `tastiera.c` (372, xkbcommon).

---

## Phase 5 — The session ✅ **CLOSED on 16 Aug 2026**

> ### ⭐⭐⭐ CLOSED ON THE USER'S JUDGEMENT — *«funziona»* · *«il task nel terminale era ancora in esecuzione»*
>
> *And the test that counts he did himself, with REAL work inside: he logs in maximised, launches an
> infinite loop in the terminal, closes the browser, shrinks the window, comes back in — and the loop
> was still running. ⛔ All our tests had an **empty** desktop, which is the worst witness
> possible: just reborn it is identical to how it was.*
>
> | | |
> |---|---|
> | ⭐ **access** | `[M]` over twenty rounds from the browser, **no longer with the long tail** that in the morning sometimes made it last many times as long — the values in `FASI.md` §05-la-sessione |
> | ⭐ **the long tail of access** | found: the stage was born at the fallback canvas and resizing **does not complete on a still scene**. ⇒ the child waits for the client's canvas |
> | ⭐ **`RCP.md` §7.3, release on detach** | tested on the **real desktop** with a witness that counts the keystrokes: a key left down repeats, and the release stops it |
> | ⭐ **the three clocks** | silence counted **the user instead of the client** (a second device entered the desktop of whoever was reading: **I2 broken**) ⇒ fixed on packets · inactivity (`0x02`) **did not exist** ⇒ done · the 6 hours become **60 minutes**, by the user's decision on a memory measurement |
> | ⭐ **`0x0F`** | the second device is rejected, tested **from a real phone** — it had never come out before on a real connection |
> | ⭐ **the session with nobody watching** | stays alive, costs very little and the memory does not grow. In v1 `libmutter` hit a failed assertion |
> | ⛔ **and three log lines were lying** | `RILASCIO AL DISTACCO: 0` which could not say anything else · the page's `0x02` text that named the wrong clock · *«l'utente ha chiesto di uscire»* said by a clock. ⇒ `LEZIONI.md` §1.9 has its **fifth rule** |
> | ⛔ **and the login form was under the desktop** | from the beginning: the «desktop costume» was hiding nothing. Found by the user, in three reports |
>
> ⇒ ⭐ **Only two things remain**, and the list was **cut** with the user's criterion — *«se i
> punti non toccano il prodotto è solo rumore burocratico»*: `0x05` (the user with a **local** graphical
> session, which wants a person at the console) and the pointer bench after the replacement
> of the devices. Details in `FASI.md` §05-la-sessione §7.

**It produces**: PAM in full, the stage that survives detach, the three clocks, a single graphical
session per user.

> ### ⭐ And the boundary with multi-tenant was decided on 15 Aug 2026 — `DECISIONI.md` §4.6-quater
>
> **Here: one remote user at a time.** No budget, no counting, `MAX_ATTACCATE` stays the
> `#define` at 16 declared as a fallback. Multi-tenant as a **function** — several sessions together,
> `BUDGET_PIENO`, the configurable ceiling — belongs to **phase 10**, because it needs a real number
> and the number is given by the hardware encoder of **phase 8**.
>
> ⛔ **With a piece that is not postponed**: the logind guard of `0x04`/`0x05` must discriminate
> **per user**, and it is not a choice — it is the test machine that imposes it. `nicfio` has the **local**
> graphical session and `prova` comes from **remote**: a guard that asks *«is there a local
> session?»* instead of *«of this user?»* rejects `prova` **on the first day**.
>
> ⭐ **And the four decisions of the evening of 15 Aug are all in `FASI.md` §05-la-sessione**: the
> two exits (§4.1-ter), the return to the login form with the new reason `0x10` (§4.1-quater), the
> shortcut `Ctrl+Alt+Fine`, with no on-screen button (§4.1-quinquies), and ⛔ **nobody switches off the
> server** (§4.7).

**The user sees**: he closes the client, goes to lunch, reopens — **and finds everything as it was**.

**The bench**:
- detach and reattach, **twice in a row**: a bench that passes only from a clean machine is not a
  bench, it is a demonstration (`LEZIONI.md` §2.3-ter);
- ⛔ **the session with nobody watching**: in v1 the virtual monitor disappeared at detach and
  `libmutter` hit a failed assertion, with the applications losing their Wayland
  connection. It is the defect that makes the session unusable after the first detach;
- the three clocks, each with its own test;
- opening a local session while the remote one is alive → the remote one **must** drop with
  `SESSIONE_LOCALE_PREVALSA`, and the reason is verified **from the side that receives it**;
- ⭐ **and the missing twin**: a local session **already active** and a remote one arriving →
  `GIA_ATTIVA_LOCALE` `0x05` (`SPECIFICHE.md` §5.1). *Added on 9 Aug 2026, finding **R4.16**:
  it belonged to `RCP.md` §8.2 and to no phase, and it would have fallen between the phases;*
- ⛔ **releasing the keys on detach**, which `RCP.md` §11 calls *«the rule with the highest
  damage/cost ratio in the document»*: one detaches with a key pressed **and reattaches** to
  verify that it has not stayed down. *Brought here from phase 4 on 9 Aug 2026, finding **R4.7**:
  at phase 4 there is no session to reattach to — the session dies with the connection —
  so that bench either is not written there or **is written green by construction**.*

⛔ **And two defects the user would meet leaving the session idle for twenty minutes**, both
on GNOME and both never tackled in v1 (`STUDI.md` §gnome §4 and §7):

| | |
|---|---|
| **the revocation** | GNOME's screen locker does not show a lock: **it detaches us**. We are saved by `is_headless()`, which however **we never asked for** — Mutter puts itself there when the logind session has no seat. Here headless is **declared** and **verified after startup**, and if it is not there one fails declaring it (`DECISIONI.md` §4.3-bis, measurement M2) |
| **the machine falls asleep** | `sleep-inactive-ac-type` is `suspend` at 900 s, upstream **and** Debian `[R]`. Today it does not bite only by accident. The cure is a single call — `SessionManager.Inhibit(…, 12)`, that is `SUSPEND\|IDLE` **together** — and `energia_inibisci()` on Mutter today **returns NULL** (`src/energia.c:112-113`). ⛔ Never the `LOGOUT` bit |

⚠ **The bench of the three clocks crosses them**: six hours of abandonment on a machine that suspends
at fifteen minutes are not measured at all — and the bench would stay green, because the session on
waking is still there.

**Reused**: `palco.c` (1545 lines — the most precious), `sessione.c` (797), `sentinella.c` (307,
logind), `uscita.c` (384), `energia.c` (149), `compositore.c` (229).

---

> ## ⏳⛔ BEFORE PHASE 6: THE PLAN MUST BE REVIEWED — the user's remark, 16 Aug 2026
>
> At the closing of phase 5, the user: *«prima dobbiamo rivedere il piano che ha alcuni punti
> secondo me fuori sequenza»*.
>
> ⇒ ⛔ **Phase 6 does not open until that review is done.** ⚠ And the suspicion already has a
> precedent in this same document: phase 6 declares that **three quarters of its work are already
> done** — in the tail of **phase 4** — because *«the phase's number is given by why the work was done,
> not by the list of things produced»*. A plan in which a phase is born already three-quarters done
> is exactly the place to look.

## Phase 6 — The canvas and the view

**It produces**: the canvas agreed at attach, the view that rescales, reattach at a different size.

> ## ⭐⭐ THREE QUARTERS ARE ALREADY DONE AND MEASURED — in the **tail of phase 4**, on 15 Aug 2026
>
> ⛔ **And it is not a numbering error**: the phase's number is given by **why** the
> work was done, not by the list of things produced. `DECISIONI.md` §5.0-sexies had made the canvas **the cure
> for four symptoms of the mouse and the video** — black bands, interpolated text, reattach, and the 4
> seconds between login and desktop — that is the piece phase 4 was missing. All the reports of that
> night are called `F4-IN-*`. ⇒ The document is in `FASI.md` §04-si-comanda, §«the tail of phase
> 4»; the technical report is `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md`.
>
> | what this phase asks | state |
> |---|---|
> | the **canvas agreed at attach** | ✅ `[M]` the canvas takes the size of the window, scale **1.000** |
> | **reattach at a different size** | ✅ `[M]` `SESSIONE` grants the canvas the stage already has, zero frames discarded |
> | the **view that rescales** | ✅ it was there since phase 2, and now the scale is 1 when the two canvases match |
> | ⛔ *(in addition)* ~~**live resizing**~~ | **REMOVED from the product on 17 Aug 2026** — `DECISIONI.md` §5.1-bis, the user's decision: *«non voglio mettere delle eccezioni nel progetto»*. ⚠ It was possible on Mutter, and **impossible** on KWin ≤ 6.7.4 |
> | ⛔ the **fallback on KWin declared in the log** | **OPEN**: not verifiable as long as KDE is phase 11. The code path is there (`COMPOSITORE_INCAPACE`) and it is tested by case 11 of `banchi/04-b31`, **on a fake host** |
> | ⛔ the **reattach bench that PRESSES A KEY afterwards** | **OPEN**: the fact was seen in the log (`libei` recreates the devices, `input.c` reattaches them) and the user typed in a terminal after a reattach — ⛔ but there is no bench that tests it |
> | ⛔ **multi-monitor** | **OPEN**, and out of scope as a function (§6.5) |
>
> ⇒ ⭐ **When this phase really opens, its work is what remains at the bottom of this
> table** — and the first four rows are re-measured instead of redone.
>
> ⛔ **And what of this phase remains OPEN, in full:**
> - the **fallback on KWin ≤ 6.7.4 declared in the log**, which is the bench named below;
> - ⛔ **the reattach bench that presses a key and moves the pointer AFTERWARDS** — the line below
>   that talks about the recreated devices. `[M]` on 15 Aug it was seen in the log that on a geometry
>   change `libei` **really recreates** the absolute devices («regione del puntatore per chiave»,
>   four times in a row), and that `input.c` reattaches them — ⚠ but pressing a key after the
>   reattach **nobody has tried yet**;
> - **multi-monitor** and all the rest of `SPECIFICHE.md` §6.5.

**The user sees**: he resizes the window and the image adapts **without the windows inside
moving**. Then he reattaches from a machine with another screen and finds the session adapted.

> ⭐ **And since 17 Aug 2026 this sentence is always true, not «except for a switch»** — the image
> adapts and **the desktop is never touched**, on every compositor (`DECISIONI.md` §5.1-bis).
> ⚠ The declared price: if the window changes **shape**, or the tablet **rotates**, the proportions
> no longer match and the bands show. To get the right size back one **reattaches**.

**The bench**: the fallback on KWin < 6.8 **declared in the log** — one verifies that the line is
there, not that «it works anyway» (`SPECIFICHE.md` §6.3).

⛔ **And reattach also renegotiates the keyboard layout** (`SPECIFICHE.md` §7.3), which on
Mutter **destroys and recreates the keyboard device**; a geometry change recreates all the
absolute devices. The pointer to the old device stops working **without error**
`[R]` (`STUDI.md` §gnome §9). The reattach bench **must press a key and move the pointer
afterwards**, not just verify that the session is there: it is the form «a green test with the defect alive»
exactly where it shows up.

⛔ **And with the same weight, the order between the birth of the virtual pointer and the start of the
applications** — box in phase 2, `[M]` 10 Aug 2026: a Wayland client started **before**
the input devices exist **receives nothing**, and the compositor takes the injection all the
same. At reattach the devices are **destroyed and recreated**: it is exactly the case in which
this trap comes back, on applications already open that nobody will restart.

---

## Phase 7 — Audio and clipboard

> ## ⭐⭐ AUDIO IS DONE — 17 Aug 2026, on the user's judgement: **«problema audio risolto»**
>
> *Given on a **YouTube video** played in the remote session.* `[M]` no block lost,
> except at startup — the values in `fasi/07-audio-e-appunti.md`.
> ⭐ And the volume **governs**: full 0.3536 · 25 % 0.0078 · mute 0.0.
>
> ## ⭐⭐ AND THE CLIPBOARD WORKS — **«clipboard funziona in entrambi i versi»**
>
> *The user's judgement with the browser, 17 Aug 2026 evening, port 7730.* Text only, in both directions:
> new `appunti.c`, the three messages of `RCP.md` §7.4 on the wire, the seam in the two processes and the
> browser side. ⇒ 📖 `fasi/07-audio-e-appunti.md` §4.5, §6.9, §9.2-bis.
>
> ⛔ **And the bench's external referee DOES NOT EXIST**: `gnome-shell` runs with `--no-x11`, so `xclip`
> has no counterpart to talk to, and a Wayland client without focus does not own the selection.
> ⇒ That judgement is **the only proof** this half of the phase has — and the line of `fasi/07-audio-e-appunti.md` §2.4 that
> promised a free referee was rewritten.
>
> ⭐ *And the opening request said «testo formattato»: asked of the user, who confirmed
> «solo testo semplice» — `DECISIONI.md` §5-ter.4.*
>
> ⛔ **And the phase's lesson is not about audio**: five green bench rounds and the user heard
> «jitter pazzesco». `LEZIONI.md` §2.7 — *there is no better diagnostic tool than monitoring a
> real session, byte by byte*. The decisions produced are in `DECISIONI.md` **§5-quater**, which
> did not exist before today.

**It produces**: Opus and PCM out; text clipboard in both directions.

**The user hears and sees**: the music, and copy-paste that works in both directions.

**The bench**:
- ⛔ **one listens**, one does not count blocks: in v1 the bench counted samples while the audio was
  **full-scale noise**, and it stayed green;
- ⛔ **the two sides synchronise with markers, not with `sleep`**: in KDE's clipboard bench the
  two sides were **thirteen seconds** out of step and the check gave red on code that worked
  (`LEZIONI.md` §2.3-quinquies);
- ⚠ and the clipboard is **emptied at the start** of every round: what is left from the previous round is
  announced at connection and looks like a result.

⭐ **The independent side of the clipboard bench is already there, and it is free**: on GNOME Mutter's X11
counterpart is unconditional in both directions, so **`xclip` works without a session of ours**
`[R]` (`STUDI.md` §gnome §10). Copying with `xclip` and reading with the client — instead of making
two pieces of ours talk to each other — is the external referee this phase needed and that we did not think we had.

⛔ **Three Mutter traps, which the bench does not see and the product does**: `DisableClipboard` is
**one-way** (afterwards, the announcements never come back — it is never called: to let go of the clipboard
one uses `SetSelection` without types); the signature of `mime-types` is **asymmetric** between input `as` and
output `(as)`, and whoever reads with the wrong type gets `NULL` **without error**; the internal
clipboard manager holds **only one MIME type**.

**Reused**: `altoparlante.c` (892), `suono.c` (582), `appunti_mutter.c` (450), `appunti.c` (115).

⚠ Invariant I5: the volume belongs to the session, and whoever connects finds it **at maximum**.

---

## Phase 8 — Zero copy ✅ **CLOSED on 22 Aug 2026**

> ### ⭐⭐⭐ CLOSED ON THE USER'S JUDGEMENT — *«il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»*, and *«per me è ok»*
>
> *The plan's title still says «zero copy»; the phase document is called
> [`fasi/08-l-anello.md`](fasi/08-l-anello.md) because the real mandate — dictated by the user on
> 22 Aug — was **the loop**, of which zero copy is one segment.*
>
> | | |
> |---|---|
> | ⭐⭐ **what he sees** | he drags a window fast and **the window follows the arrow**. In the morning it lagged behind by **half a title bar** |
> | ⭐ **the phase's number** | `input → vetro` **shortened**, **paired**: two rounds that share everything except the binary, `macchina carica: false` written by the bench in both — the values in `fasi/08-l-anello.md` |
> | ⭐ **in the user's unit** | the arrow↔window gap **approaches local** — and ⭐ **local** is now measured |
> | ⭐⭐ **and it is not a stopwatch victory** | `[M]` the **painted** frames rise. `LEZIONI.md` §6.2 respected, after it had been grazed **twice** in this same phase |
> | ⛔ **the 50 ms ceiling** | **is not verified**, and not because it is a little short: **the phase's number sits on a different boundary** from that of the 50 (`SPECIFICHE.md` §3.2 measures up to the *frame that leaves*). ⇒ The two numbers **cannot be compared** — it is `LEZIONI.md` §1.28 applied to ourselves |
>
> **⭐ The three inheritances, all three answered**: `EncSliceLP` can **not** do temporal sub-layers
> (7 profiles out of 7, two positive controls) · the keyframe at the user's canvas stays **well inside
> the ceiling** · the encoder's card now **declares itself** instead of falling back
> silently. And `RCP.md` §5.2 and §6.2 go from `[?]` to ✅.
>
> **⭐⭐ And the defects found along the way, none of which was the target**: the **abandoned keyframe**
> (§5.2 forbids it, and it was the spiral) · the **re-encode ladder one rung short** · the
> **stride not a multiple of 64** that gave a desktop **skewed without errors** · and the **product's
> stopwatch that measured the bench**.
>
> **⛔⛔ And the two lessons that survive the phase**, `LEZIONI.md` **§1.26**, **§1.27** and **§1.28**:
> two benches on the same **machine** falsify each other silently (and give **a plausible number**, not
> a red) · the **average colour is blind** to an image wrong on every row · and **two benches that
> disagree can both be right**: they measure two different quantities.
>
> ⏳ **What was NOT done, and is carried forward:**
> - ⛔ **Mutter's wall**: `[M]` one frame at 60 Hz — it did not move all day, and
>   **nobody touched it**;
> - ⛔ **half of the gain is not explained**: it lies in a segment that zero copy **does not
>   cross**. `[?]` The hypothesis — the producer out of the real-time thread — is
>   **declared, not measured**;
> - ⚠ **the retention of the `pw_buffer` is in force without proof**: the positive control **did not
>   reproduce the damage**. Prudence, not measured necessity;
> - `[?]` **the gap model predicted badly twice, in opposite directions** — first less than the
>   truth, then more. ⛔ **It is a fact about the model, not about the user**, and it is our work;
> - 🔸 **the canvas multiple of 16** (`rcp_misura_ammessa()`): it would make zero copy valid on **every**
>   screen, ⛔ but it is a **protocol change** — `RCP.md` §4.5 today only demands that the sides be
>   even. **The user decides.**

## ~~Phase 8 — Zero copy~~

> ## ⭐ AND ON 22 AUG 2026 THE USER ADDRESSED TO IT **THE ONLY REMARK HE HAD LEFT**
>
> *After declaring audio OK on all four supported engines:* **«l'unico piccolo
> appunto è un'ottimizzazione sulle performance grafiche, che credo sia lo scopo della fase 8»**.
>
> ⭐ **He is not wrong**, and it is the second time he addresses something to this phase by reading the plan.
> ⚠ **And it counts as a mandate**: when this phase opens, its yardstick is not «zero copy is
> written», it is **what he sees move better**.
>
> ⏳ **And it gets there with two measurements already in hand**, taken on the night of 21-22 Aug:
> - `[M]` **`createImageBitmap` costs little per frame**, a small part of the 50 ms ceiling.
>   ⭐ And the current path costs **much less** than the 2D drawing that was there before;
> - `[M]` **the `?video=worker` path works and does NOT pay off**: the maximum rhythm drops. ⇒ The
>   road «move the drawing to another thread» **has already been tried and does not pay**: whoever opens
>   this phase should not redo it.

> ## ⭐⭐ THE TITLE HAS CHANGED, AND TWO THIRDS OF THE PHASE ARE ALREADY DONE — *16 Aug 2026*
>
> *The user's remark at the opening of phase 6: «gli ultimi test sono stati eseguiti con l'ausilio
> della Intel integrata, e quindi usando l'accelerazione HW, o sbaglio?». **He is not wrong**, and it is
> written here so that whoever arrives at this phase does not look for work already delivered.*
>
> *Here the title was **«The acceleration»** and the line said: «**It produces**: HEVC in hardware on
> Intel, 10 bit, and zero copy».*
>
> **Hardware encoding entered the product on 13 Aug 2026**, on purpose and with the
> reason written above at phase 3: the chain had been moving **since that day**, so the *before* and
> the *after* could be measured **with the same bench and the same scene** — which three phases later
> would no longer have been true. `src/codificatore.c` · the note «phase 8 slipped in» calls it *«phase 8 slipped in
> through the back door of phase 2»*.
>
> | the promise of this phase | where it ended up |
> |---|---|
> | ⭐ **HEVC in hardware on Intel** | ✅ **done and measured.** Encoding on the card goes through **VA-API** on **`/dev/dri/renderD128`** — the Intel iGPU, entrypoint `EncSliceLP` — and since phase 18 with **libva directly**, for H.264 and HEVC. The software fallback is **OpenH264** (H.264) or **SVT-AV1** (AV1), ⛔ **HEVC in software is not there**, and the fallback **writes that it is a fallback**. `[M]` the encoding segment halves and the frames double (`F3-E`, same stage, night of 14 Aug); the call to the encoder is by now a small part of that segment (phase 4, `hev1.2.4.L120.B0`) |
> | ⚠ **10 bits** | ⛔ **nominal, and the wall is upstream, not here.** `DECISIONI.md` §2.3-ter `[M]`: from Mutter's capture real ten bits **do not come out by any road** — MemFd gives BGRx, the DMA-BUF too, and asking for the 10-bit formats alone one gets `no more input formats` on both. `Main10` from here means **eight bits promoted to ten**. ⇒ The question is no longer *«can our code do 10 bits?»* but *«is there a source that gives them to us?»*, and it is **a question for capture**, not for encoding |
> | ⛔ **zero copy** | **intact — and not brought forward on purpose** (`README.md`: *«zero copy is NOT brought forward: it stays at phase 8»*). It is everything that follows |
>
> ⭐⭐ **And phase 4's account says that what remains weighs more than what was removed.** The
> most expensive segment of the loop is still `cattura → primo byte` `[M]`, and inside it there is:
>
> | | does zero copy remove it? |
> |---|---|
> | the colour conversion, then on the CPU | ⭐ **yes** |
> | the upload to the GPU | ⭐ **yes** |
> | encoding, **in hardware** | no — it is already cured |
> | ⛔ **and a part that none of the three explains** | ⏳ `[?]` **to be discovered, and it lies in this segment** |
>
> ⇒ ⭐ **Conversion and upload are exactly the work zero copy deletes** —
> converting and re-uploading to the GPU a frame that **was already on the GPU** — and they weigh more than
> what encoding costs today. ⛔ And the unexplained part is **in the same segment**: this is where one
> looks, and this phase is the only one that has the reason to look inside it. The values in `FASI.md`
> §04-si-comanda.

> ## ⭐⭐⭐ AND ON 22 AUG THE USER DICTATED THE SPECIFICATION — `SPECIFICHE.md` §3.2-bis
>
> *«La mia specifica è avere un'esperienza utente **il più vicina possibile a una situazione
> locale**, ma non identica: quello è impossibile.»*
>
> ⭐ **And he specified the symptom with his eye, which is a measurement**: dragging a window fast,
> the distance between the arrow and the window chasing it is **«metà della barra del titolo»**.
>
> ⛔⛔ **Hence the real mandate of this phase, and it is NOT zero copy**: that gap is
> `velocità della mano × ritardo dell'anello`, the arrow is local and the window is not ⇒ **it is a
> RUBBER BAND** that opens when the hand accelerates. Zero copy removes **a small part**
> of the loop. ⇒ **The whole loop** is needed, and it is what phase 4 had already written when closing:
> *no single cure brings the loop under the ceiling: it is phase 8's work*.
>
> ⛔ **And one road is closed before opening**: putting the loop in parallel would buy
> frames paying for them in delay ⇒ **it would widen the rubber band**. `SPECIFICHE.md` §3.2 already forbade it: *«a choice
> that raises the rhythm worsening the delay is not made»*.
>
> ⏳ **The bench's first number** is no longer a segment: it is **`input → vetro` re-measured on the real
> scene** — window 720×433, median speed **3 400 px/s**, peaks **12 400** (`[M]` from the user's
> video, 22 Aug). Phase 4's number is eight days old with two phases of cures in between.

**It produces**: ⭐ **the shortest loop**, of which zero copy is **one segment out of six** — the frame
goes from capture to the encoder **without leaving the GPU**.

**The user sees**: ⭐ **the window chasing the arrow more closely**, and judges how close we have
come to local. ⚠ *(It was: «the same image as before, and he judges that it has not got worse» — the
yardstick of when this phase was only zero copy.)*

**The bench**, and it is the lesson that cost the most:
- ⛔ **one measures the frames delivered, not the milliseconds of CPU.** Phase 9 of v1 brought
  the cost per frame down a lot while the frames delivered **were falling**.
  A gain paid for in fluidity is not a gain (`LEZIONI.md` §6.2). ⛔⛔ **And here it bites
  twice**, because phase 4 found the growing queue: the server delivered more
  frames than the page painted. A gain in milliseconds that turned
  into frames nobody paints **would worsen the delay** instead of curing it;
- ⛔ **ask for the encoder and verify that it obeyed**: an encoder that
  falls back to CPU believing itself on GPU produces two measurements under the same label. If it does not obey,
  the failure is declared (`LEZIONI.md` §1.8). ⭐ The right question is **what the encoder
  receives** — a card surface, or pixels — not what it is called;
- ⚠ and the proof «it opened a render node ⇒ it renders on GPU» **proves nothing** (§1.11);
- ⛔ **and the number is redone with the SAME bench and the SAME scene as phase 4** (`03-b17-ritardo.py`),
  or the before and the after cannot be subtracted. ⚠ The total is not enough: **the segments** are put side by side, because
  this phase's question is *«with the copy removed, do the others stay where they are?»*.

⛔ **And zero copy is reopened from the right side**: the two screens that alternated were not a
problem of *acquire* but of **release** — `can_reuse_pw_buffer` gives up if
`SPA_META_SyncTimeline` is missing and Mutter reuses the buffer **while VA-API is still reading it** `[R]`
(`LEZIONI.md` §8, the box of the wrong hunt). Two candidate cures, both small:
requesting the timeline — which Mutter offers — or **retaining** the `pw_buffer` until reading is
finished. ⚠ And **Mutter's DMA-BUF is not a diff**: whoever took up the accumulation surface again
would redo the cure that made things worse.

⭐ **And the road is open `[M]`**: Mutter **really delivers** the DMA-BUF — 388 frames, 4
buffers, modifier **LINEAR**, stride 7680 read from the chunk (`DECISIONI.md` §2.3-ter). ⚠ The
format stays **BGRx at 8 bits**: zero copy is done on that, and the ten bits do not come back through this
door.

> ### ✅ ⭐ The GPU trap is CLOSED, and it must be said so that nobody hunts for it again — *15 Aug 2026*
>
> *Here it was written: «with two cards, the compositor drawing on the wrong one gives
> software composition **without an error**. The udev rule of `fondamenta/banco/gpu-udev.sh` must be
> applied and verified».*
>
> ⛔ **And it was worse than a risk: it had already happened.** `[M]` `/etc/udev/rules.d` was **empty**, the
> `video`/`render` groups gave access to both cards, and the compositor had taken the
> **Radeon** — a measurement thrown away because it was made on the wrong card.
>
> ⭐ **The rule was applied and verified** (`DECISIONI.md` §4.6-ter): `gnome-shell` opens
> **6 descriptors on `renderD128`**, the integrated one, and only that. ⇒ **Compositor and encoder
> are on the same card** — which is precisely the condition without which zero copy would not
> make sense: a frame cannot be passed without a copy between two different cards.
>
> ⚠ **The price stays declared**: denying the node denies it to **the user's whole session**, not
> just to the compositor.

⏳ **What this phase must no longer carry around**, and where they went:
- **real 10 bits** → a question for **capture**, and it lives in the phases in which capture is touched;
- ⚠ the **quality of `EncSliceLP` against the full entrypoint** → `[?]` **never measured**: low-power
  encoding is fast and **is not equivalent** to full. It is the working point between quality and
  bandwidth, that is **phase 9** — and if one day it turned out worse, it is cured there, not here.

---

## Phase 9 — Quality and degradation ✅ **CLOSED on 24 Aug 2026**

> ### ⭐⭐⭐ CLOSED ON THE USER'S JUDGEMENT — *«il prodotto cambia in meglio; questa fase era per rendere più solido il funzionamento di remotix su reti degradate, senza pretendere di fare miracoli»*
>
> 📖 `fasi/09-la-qualita-e-la-degradazione.md` — the summary at the top, and §17-§21 the part that counts.
>
> ⭐⭐ **He corrected the target himself with the phase open** (`DECISIONI.md` §3.1-ter): not **bandwidth** —
> *«30 mbps sono una connessione da metà anni 90»* — but **the network that loses, reorders and jitters**.
> And it was the right quantity: on bandwidth the product did not give way, on a dirty wire it did.
>
> **The scale that closes the phase comes from his eyes**: up to a certain loss *«è tutto
> fluido»*, beyond it ⛔ *«bloccato»*, with the cures and without — the measured scale is in
> `fasi/09-la-qualita-e-la-degradazione.md` §19.1 and §19.6.
>
> ⛔ **Above a certain loss the degradation ladder has nothing more to offer**, and the only
> honest answer is to declare the line dead (`DECISIONI.md` §3.1-quater) — which is the decision he took
> **before** having that number.
>
> **The five cures are ON** (§3.1-septies), each with a single way to switch it off, and ⭐ **the
> test that could have made everything be withdrawn is green**: `[M]` on the healthy line the rhythm with the defaults is
> the same as with cures off — **no worsening**, which is the wound for which v1 lost this phase.
>
> **The three facts that remain**, and they hold beyond the phase:
> 1. ⭐⭐ **the defect does not begin where it shows**: the keyframe spiral starts at the **first packet
>    lost**, the drop the user **sees** comes much later;
> 2. ⭐⭐ **the trigger has a constant risk** over time, and once on it does not switch off. ⛔ The
>    benches run a few seconds, **sessions last hours**: every measurement taken near the edge
>    **underestimates**;
> 3. ⛔ **disorder is mistaken for loss**, and it came back to bite us: the first «dead line»
>    was calibrated on `pkt_lost`, and `[M]` a line that **holds** declared more of it than one that **does not
>    hold**. Redone on the **stall of the output**.
>
> ⚠ **And the count of method errors, which is the most useful part**: `[M]` **nine defects in the
> benches**, all of the form *«silence instead of red»* · **three tests that did not bite**, discovered
> by counting the packets · **two conclusions of mine withdrawn** (the applications that «did not arrive», the
> clapper test declared «null» and disproved by the third judgement) · and **two false premises**
> inherited and corrected (the user was never on PCM; the audio delay measured then does not
> reach his ear).


**It produces**: rhythm control, the degradation ladder, behaviour on a bad network.

> ### ⛔⭐⭐⭐ THE TARGET WAS CORRECTED — **23 Aug 2026, with the phase open**
>
> *«30 mbps sono una connessione da metà anni 90. La vera sfida è misurare performance con reti
> che perdono pacchetti o pacchetti fuori sequenza, o presentano fenomeni di jitter».*
> — ⇒ `DECISIONI.md` **§3.1-ter**.
>
> ⛔ **Bandwidth leaves the body of the phase.** The day had been spent narrowing the line, and
> `[M]` §16: on the **real path** the product holds the worst case **without degrading and with all
> the cures off** — every frame delivered is painted, **one** keyframe.
> A bench that cannot make what it measures give way **is not measuring the right quantity**.
>
> ⭐ **The three new quantities, and they are not the same thing:**
> **loss** (video retransmits ⇒ it is paid in delay; audio does not ⇒ it is paid in holes) ·
> **out of sequence** (⭐ it is the missing condition of the audio reordering cure, the only cure
> of 23 Aug whose useful half was never verified) ·
> **jitter** (`[?]` QUIC can mistake it for loss and narrow the window **for no reason**: if
> that happens the drop is **ours**, not the network's).
>
> ⚠ **`DECISIONI.md` §3.1-bis is not annulled**: the declared floor stays — ⛔ **and it moved to 30 Mbit/s the
> same night** (§3.1-sexies: *«ho già detto che il pavimento, per quanto riguarda la banda, è a
> 30 mbps»*). Its job changes — from the phase's **question** to the **premise** on which
> the other three are measured.
>
> ⛔⭐⭐ **And the phase produced a new decision, `DECISIONI.md` §3.1-quater**: a line that loses **in bursts**
> is declared **dead** — 10 s without packets, or a copious loss within 1-2 s — and ✅ **the user
> comes back in by hand**. It is born from the choice between two measured evils: `[M]` without cures the screen freezes
> for many seconds, with the cures it moves with seconds of delay. ⇒ Neither should be served.
> ⛔ Prerequisite: **`DECISIONI.md` §3.1-quinquies**, the *ghost* — coming back in, the user finds his own place
> occupied by himself for 30.5 s, and with a message that for him is **false**.
>
> ⛔ And `netem` on `lo` becomes a **single resource with a lock** (`banchi/09-lucchetto.py`): the
> discipline is put on the interface's root, so two benches that break things together do not
> share the work — the second **deletes the first's fault**, and the first keeps measuring
> believing it has it. ⚠ It would not give red: it would give a plausible number.

**The user sees and judges**: the image. ⛔ **And it is the only judgement that counts**: in v1 this phase
had been validated with PSNR, SSIM and the developer's eye, and the user's judgement on the
real desktop was *«siamo tornati indietro»*. The phase was reset to zero.

**The bench**: the network throttled at real values — ⭐ **20 Mbit/s, the floor declared by the user
on 23 Aug** (`DECISIONI.md` §3.1-bis), with loss and long round trip — and the check that the rhythm drops
**without ever blocking** and without ever detaching.

> ⛔ **The number was «2 Mbit/s», and it changed on 23 Aug 2026.** *«Mi ero tenuto più largo:
> ritengo che una connessione minima debba essere 20 mbps: al di sotto di questo limite l'utente
> nemmeno riesce a navigare, figuriamoci usare remotix».* ⇒ ⭐ **What is being calibrated changes**:
> the degradation ladder covers **temporary drops of a good line**, not poor lines.
> ⚠ And the direction of a risk changes: at 20 Mbit/s the bottom of the scale is almost never reached, so
> the defect that hides is no longer «it degrades badly», but **«it degrades when it should not»** — which
> is invariant I1, and it is precisely the first thing this phase verifies.
>
> ⭐ **The tool for throttling from the client side is there**: `wondershaper` in `~/.local/bin` on the
> user's tablet — ⇒ one can throttle **the real path**, not only `lo` with `netem`, which is
> the declared limit of `banchi/07-b64-rete.py`.

⛔ **The thing verified first**: that the rhythm does **not** drop when the scene is still. It is
invariant I1, and it is the wound it is born from.

⚠ And what changes what is seen stays **behind a switch that is off** until the user has
looked at it (I6).

> ### ⛔⛔ CORRECTIONS OF **23 Aug 2026, evening** — what the facts have overtaken
>
> *📖 All in `fasi/09-la-qualita-e-la-degradazione.md`, the summary at the top.*
>
> **1. ⛔ «Throttling at 20 Mbit/s» does NOT prove what this phase must prove.** `[M]` §3.10:
> with the requested bandwidth **below** the hole **absolutely nothing happens**. ⇒ ⭐ **A
> STEP is needed** — wide → 3 s narrow → wide — not a constant limit: a constant limit measures the
> **steady state**, and in steady state the prediction is that nothing happens. ⛔ And **three seconds are enough**:
> the rhythm collapses and **half of the frames become keyframes**.
>
> **2. ⭐⭐ «That the rhythm does not drop with the scene still» is MEASURED, and the answer is sharper than the
> question**: with the scene still the rhythm **does not drop, it STOPS**.
> ⛔ **And it is not our decision**: Mutter's `RecordVirtual` delivers **only on change**.
> ⭐ **And waking up costs nothing perceptible**, whatever the length of the quiet.
> ⇒ It is a **literal** violation of I1 that
> **costs nothing to whoever is watching**, and **it is not a defect of the phase**.
>
> **3. ⭐ The two «already measured» things of the box below WERE WRITTEN on 23 Aug**, with
> three more: the cure of `video_sgombra()` (`--sgombra-soglia-ms`, off), the audio reordering
> (without a switch), the quality rising back (`--qualita-risale`, off), the bandwidth ceiling
> (`--tetto-banda-mbit`, off) and ⛔ **the cure of a crash**: the server died of `SEGV` at
> 08:28:09 from a **use after free** in `webtransport.c`. ⚠ **None of the five was
> measured on the test machine.**
>
> **4. ⛔ And the defect that hides is not only «it degrades when it should not».** `[M]` `fasi/09-la-qualita-e-la-degradazione.md` §3.8: with
> QP 26 fixed and no ceiling, a **film with full-screen grain** asks for **several times the
> floor**. ⭐ **But the user's real desktop asks for a small fraction of it.** ⇒ The ceiling is for the
> **hard case**, and the phase has **two** targets, not one.
>
> **5. ⛔ And the rhythm regulator has a mandatory order**: it comes **after** the threshold on the queue.
> As long as `video_sgombra()` empties the queue at every frame, the quantity the regulator
> hooks onto is **zero by construction** — and a mute regulator and a healthy line look the same.

⭐ **And this phase now has a second client, which it did not have before**: the degradation ladder is
**the way to fit more people on the same machine**. A budget without the ladder can only say
*«no»*; with the ladder it can say *«yes, smaller»* — and it is phase 10, which comes right after.

⏳ **And here comes a question that phase 8 passed on to it**: `[?]` the quality of the
`EncSliceLP` entrypoint — **low-power** encoding, the one the product uses — against the **full** one,
at equal bandwidth. **It has never been measured**, and the working point between quality and bandwidth belongs to
this phase.

> ### ⭐⭐ AND ON THE NIGHT OF 21 AUG THIS PHASE RECEIVED TWO THINGS ALREADY MEASURED
>
> *They come from closing the holes of phases 6 and 7, ⛔ and they were **moved here by the user**:
> «i problemi di rete non rientrano in questa fase, qui stiamo chiudendo i buchi delle fasi 6 e 7».
> ⚠ The coordinator had brought the decision into the wrong room.*
>
> **1 · ⛔ The engine of the spiral: `video_sgombra()` abandons the deltas at EVERY frame.**
> `[M]` On a wide line it almost never abandons; on a narrow line a delta does not leave within the interval
> of one frame, so it is abandoned **always**, and every abandonment reignites the debt of
> `RCP.md` §5.2 — the log says so **almost at every frame**. ⇒ The video degenerates into **a flow of keyframes only**, which is the worst
> form of degradation: heavy, jerky, and it starves the audio.
> ⭐ **The cure is named and `RCP.md` §5.1 allows it without imposing it**: abandon a delta only when it is
> *truly hopeless* (a threshold on the queue) instead of at every more recent frame. That way
> under congestion the video would drop in **rhythm** while staying made of deltas.
> ⚠ **The price must be judged by the user**, and it is exactly this phase's job: for a
> fraction of a second one would see something slightly old. ⛔ In v1 a phase like this one was
> reset to zero because it was validated with PSNR instead of with the eye: **it is not decided without him**.
>
> **2 · ⛔ The audio reordering window.** `src/pagina.html` discards a datagram *«older
> than what has already ARRIVED»*, while `RCP.md` §6.3 says *«already consumed»*. ⇒ A block
> arrived **one millisecond** out of order is thrown away **while keeping 250 ms of cushion**.
> `[M]` with `netem`: with a fixed delay the tone stays pure; **with a jitter of a few milliseconds
> it gets dirty**, and a large part of the datagrams is discarded. ⭐ On real WiFi, instead, the «old» ones are **zero** — and it is the
> reason why it belongs to this phase and not to phase 7.
> ⚠ Two warnings already paid for: `netem delay X Y` **really reorders**, a home queue usually
> does not; and the measurement is in **PCM of 5 ms** — with Opus (20 ms) the threshold would be ~4 times higher.
>
> ⭐ **And the instrumentation to judge them is already written**: `banchi/07-b65-datagram.py` (the network
> throttled with the real bytes taken from the qdisc, the scene on/off check that decides),
> `banchi/07-b64-rete.py` and `banchi/07-b64-orecchio.py` (the tone judge, certified 4 out of 4).
> ⇒ This phase does not start from zero: it starts from a bench that already knows how to say when it has **not** measured
> anything.

---

## Phase 10 — Multi-tenant and the budget

> ## ⭐⭐ MOVED HERE FROM THE TAIL OF THE PLAN — *16 Aug 2026, the user's decision*
>
> *It was **phase 12**, after the three new desktops. The user: «PRIMA si chiude lo sviluppo anche con il
> multi-tenant, e solo dopo si pensa agli altri DE».*
>
> ⚠ **The desktop phases were not downgraded: they were recognised for what they are.**
> They produce **breadth** — the second, third and fourth desktop — on a shape that multi-tenant
> can still change. And the argument is not new: it is **the same** with which `DECISIONI.md` §4.6-quater
> had postponed multi-tenant until after phase 8 — *«measuring them before means measuring them twice»*
> (`LEZIONI.md` §7.2) — applied from the other end:
>
> | | |
> |---|---|
> | ⭐⭐ **depth before breadth** | if multi-tenant touches the session or the budget, the change must be re-verified **on four desktops instead of one**. It is «measuring them twice», multiplied by four |
> | ⛔ **and the budget is a GPU budget, and the GPU is ONE** | the number is measured on `renderD128` — the same iGPU that composes **every** desktop. It is a property **of the machine**, not of the desktop: measured once, phases 11 and 12 inherit it. Measured afterwards, one no longer knows which number belongs to what |
> | ⭐ **and the reverse dependency does not exist** | nothing in here needs KDE, XFCE or LXQt |
> | ⚠ **and the test machine is ALREADY multi-user** | local `nicfio` + remote `prova` that must coexist: `DECISIONI.md` §4.6-quater calls it *«the normal state of the machine, not a scenario to invent»* |
>
> ⚠ **And what this phase does NOT avoid, said in full**: the architecture is already largely there —
> `figlio.c` ⚠ *(the cited code is no longer there: to be reread)* declares *«one user per child»*, one process per session. ⇒ One is not dodging
> a structural rewrite; one is avoiding **measuring a machine number four times**.
>
> ⛔ **And the precedence that remains, and must be respected**: this phase comes **after phase 8**. Zero copy
> changes **how much a session costs** in memory and GPU bandwidth — and the budget measured before
> zero copy is a budget to redo. It is `DECISIONI.md` §4.6-quater to the letter, and nothing has changed.
>
> ⚠ **The user's words of 15 Aug said «phase 12»** (`DECISIONI.md` §4.6-quater,
> `FASI.md` §05-la-sessione), and **they stay written that way** where they are quoted: it was the number of the time.
> ⭐ **The decision has not changed — the order has**: the boundary between «one user at a time» and
> «the full machine» is still the one he drew.

**It produces**: several users together, the encoder budget, the reasoned refusal.

**The user sees**: two real sessions at the same time; and when the machine is full, a message
that **says why**.

**The bench**: the encoder is saturated on purpose and one verifies that the eleventh receives
`BUDGET_PIENO` — and that **the ten who were working do not get worse** (`DECISIONI.md` §4.6-bis).

⚠ ~~**And the debt with the written deadline belongs to this phase**: `MAX_ATTACCATE` is a `#define` at
**16** — and `MAX_FIGLI` at 16, which follows it — where `SPECIFICHE.md` §5.5 promises **ten,
configurable**.~~ ✅ **DUE AND PAID on 25 Aug 2026** *(realigned to the code on the 28th)*: the
number is a single one, `RCP_TETTO_SESSIONI` in `src/rcp.h`, and it is changed with **`--tetto-sessioni N``**.

> ## ✅ OPENED ON 24 AUG 2026, **CLOSED ON THE 25TH** on the user's judgement
>
> *«Sono soddisfatto. Riprodotto audio e video su una connessione del 1990. Non credo che si
> possa chiedere di più.»* ⚠ And **two decisions not taken**, declared: QVBR stays **off**,
> ceiling **10** and reserve **0.5**.
>
> 📖 **`fasi/10-multi-tenant-e-il-budget.md`**.
>
> ⭐ **The debt is settled**: the `#define`s at 16 were **five, not two** (`MAX_ATTACCATE`,
> `MAX_FIGLI`, `QUANTI_PRESENTI`, `WT_PALCHI` — and this last was **8**, a sixth number yet again
> different). Now they all derive from **`RCP_TETTO_SESSIONI`**, it is worth **ten**, and it moves live with
> **`--tetto-sessioni N`**.
>
> ⛔⛔ **And the phase's premise was wrong**: *«the encoder budget»*. `[M]` The bottleneck is
> **composition**, which saturates before the encoder — and what saturates it is **`gnome-shell`**, not us.
> ⇒ `DECISIONI.md` **§4.6-nonies**.
>
> ⭐ **And what the user sees has been produced**: two real sessions together, and ⭐ **`BUDGET_PIENO 0x06` really leaves**, with a sentence that says
> *why* — until this phase it was declared in `rcp.h` and in `RCP.md` **and no line of the server
> ever sent it**.

---

## Phase 11 — The safety net

> ## ⭐⭐⭐⭐⭐ DECIDED BY THE USER ON 25 AUG 2026, with phase 10 just closed
>
> *«Prima è necessario mettere in sicurezza tutto quello che abbiamo sviluppato fino a oggi. Prima di
> passare agli altri DE è necessaria una sessione dedicata per studiare una modalità che impedisca di
> introdurre regressioni man mano che verrà implementato il supporto ai nuovi DE.»*
>
> ⇒ `DECISIONI.md` **§4.6-duodecies**. ⚠ **KDE, XFCE and LXQt move down by one**: they become phases 12,
> 13 and 14. The phases **do not change by a line** — their place changes, as already on 16 Aug.

📖 **The phase document is open**:
[`fasi/11-la-rete-di-sicurezza.md`](fasi/11-la-rete-di-sicurezza.md) — ⭐ written **also for whoever does not
know the project**, because the user submits it for a second opinion: **§2** the constraints already decided,
**§4** the list of checks, **§8** the open questions.

**It produces**: a way of noticing **by ourselves** that something has broken, before the user discovers it.

> ## ✅⭐⭐⭐⭐⭐ **DONE — 27 Aug 2026**
>
> `[M]` **Sixteen meshes**, four boxes, and the whole round in **2 h 14**:
>
> | | |
> |---|---|
> | green verdicts | **58** |
> | reds | **3** — and they are **the same red**: `C1` on kde/xfce/lxqt, because ⛔ the product can start **only GNOME** (`src/sessione.c` · `scrivi_dropin()`) ⇒ **it is phase 12** |
> | ⭐⭐ **injected faults** | **49 out of 49 seen** |
> | reds of the **bench** | ⭐ **none** |
>
> ⭐⭐⭐ **And the oldest defect of the project fell along the way**: *«the session that is born
> blind»* (`fasi/10-…` `fasi/10-multi-tenant-e-il-budget.md` §7.4) **did not belong to the product** — the tenant was not in the `video` and
> `render` groups. `[M]` 17 sessions out of 17 see with the groups, **0 out of 4** without. ⇒ The five tests declared
> «impossible» were not, and today they all run.
>
> ⚠ **And what the net does NOT catch, declared**: it does not compare **yesterday with today** (a slowness that
> breaks nothing passes), and on three boxes out of four it tests **the environment**, not the product.

**The user sees**: nothing new on the screen — ⭐ **and that is the point**: he sees that the things that
worked **keep working** when the new desktops arrive.

---

### ⛔ Why this phase exists — three real defects, not a generic fear

| the defect | hidden for | ⛔ why it was invisible |
|---|---|---|
| **the session that is born blind** (phase 10 `fasi/10-multi-tenant-e-il-budget.md` §7.4) | days | ⛔ **nobody opened a NEW session**: the ones already open were reused, which had the monitor |
| **the browser that does not start for the second user** ⚠ *(not the `~/.cache` link: that is a **choice** of the user's, `DECISIONI.md` §4.6-undecies)* | **two phases** | ⛔ and the check that *«closed the question»* ran from a user **in the same condition** |
| **five benches that counted zero frames** | one round | ⛔ a cure to the log had broken their expressions, and the function returned **0 instead of «I do not know»** |

⇒ ⭐⭐ **All three invisible for the same reason**: one always looked at **the same piece of
scene**, and one looked at **the process instead of the pixel**.

---

### What it must produce, in concrete terms

| # | | ⛔ and the why lies in a real defect |
|---|---|---|
| **1** | ⭐ **A DELIVERY test that starts from zero**: clean machine → new user → new session → **an image of the desktop with a window inside** | ⛔ it is the only form that would have caught the blind session. A test that reuses a session **never catches it** |
| **2** | ⭐ **Executable invariants**, few and true: the session has a monitor · a window opens · the frames arrive · **whoever is already there does not get worse** (I1) · the R12.3 twins match · the log says **whose** it speaks of | ⚠ Few. ⛔ A net with a hundred meshes nobody reads is ceremony |
| **3** | ⛔ **That it runs BY ITSELF** after every change, without anyone having to remember | ⛔ the three times today nobody remembered — **and nobody was distracted**: there simply was no hook |
| **4** | ⭐⭐ **That it is CERTIFIED itself** — `--certifica`, with injected faults | ⛔ `LEZIONI.md` §1.36: *the layer that coordinates the benches is a bench too, and nobody certifies it*. `[M]` **six defects** found in there in a single phase |
| **5** | ⭐⭐⭐ **That it is BLIND TO THE DESKTOP** — the same invariants pointed at GNOME, KDE, XFCE, LXQt without rewriting them | ⛔ it is the whole reason the phase comes **before** the new desktops: a net written to measure for GNOME must be rewritten four times |
| **6** | ⚠ **That it looks at DELIVERY on the machine AS IT IS** | ⛔ the browser that does not start was not in our code: it was born from the meeting between **how the user configured his machine** — legitimately — and **the ten users we put there**. A net that compiles and tests only `src/` would never have caught it. ⚠ And it must not **judge** the configuration: it is none of its business |

---

### ⛔⛔ THE PHASE'S ACCEPTANCE TEST — and it is already written, today

⭐⭐ **The net is pointed at the code of 25 Aug 2026, and it MUST turn red on `fasi/10-multi-tenant-e-il-budget.md` §7.4** — the
session that is born blind — ⛔ **without anybody having told it where to look.**

⚠ **And the second acceptance test**: it must notice that **for the second user the browser does not open**.
⛔ **Not** «it must find the `~/.cache` link»: that is a **choice** of the user's on his
system, not a fault — correction of 25 Aug 2026, `DECISIONI.md` §4.6-undecies.

⇒ ⛔ **If it does not catch them, it is not a net: it is a ritual.** ⭐ And the phase's yardstick is not *«how many tests
run»*: it is **what the net CATCHES**.

---

### ⚠ What this phase is NOT

⛔ **It is not «writing more benches».** There are already more than a hundred, ⭐ and they did not help: today's three
defects passed **right through them**. ⇒ The problem is not the quantity of tests — it is ⭐ **where they
start from** (from zero, or from a state that already worked) and ⭐ **what they look at** (the pixel, or the
process).

⚠ **And it is not a ceremony phase**: if at the end the net has caught nothing the eye would not
have caught, **the phase has failed**, and it must be said.

---

## Phase 12 — KDE

⚠ *It was **phase 10** until 16 Aug 2026: multi-tenant overtook it, and the reason is
in the box of phase 10. **The phase has not changed by a line** — its place has changed.*

**It produces**: the second desktop.

**The user sees**: the same thing on Plasma.

> ## ⭐⭐ AND NOW THERE IS A NET UNDERNEATH — *and three things this phase inherits, measured*
>
> ⭐ `[M]` 27 Aug: phase 11 is closed, and the **only red** it produces is precisely the mandate of
> this phase — ⛔ **the product can start only GNOME** (`src/sessione.c` · `scrivi_dropin()`, all of `src/mutter.c`).
> ⇒ The net already measures, today, whether this phase succeeds: the day `C1(kde)` turns green, KDE is
> really served.
>
> ⛔⛔ **Three things to put in this phase's plan, or they get skipped:**
>
> | | |
> |---|---|
> | ⭐ **a fault of its own** | `fasi/11-…` `fasi/11-la-rete-di-sicurezza.md` §3.6 imposes it: *«every new desktop comes in with at least one fault of its own, invented and run»*. Today's acceptance tests are the ones GNOME taught us |
> | ⛔ **KWin cannot be born blind** | `[M]` with `--output-count 0` it makes an output anyway ⇒ the design *«zero monitors of its own»* **does not carry over unchanged**, and it must be rethought here |
> | ⚠ **the stage dies with the client** | `[M]` the virtual monitor dies with the child's D-Bus connection. ⭐ On GNOME `C6` measures green (the windows are found again), ⛔ but on a different compositor it is not a given ⇒ `DECISIONI.md` §4.6-teretvicies |

> ## ⛔⛔ The PERFORMANCE motivation of this phase has fallen — *13 Aug 2026*
>
> *Here it was written: «And here one chases the desired number: KWin delivers more frames per
> second than Mutter `[M]`. The KDE phase is not just "serving more desktops": it is the road to 60 at 4K
> and to the 40 ms target».*
>
> ⚠⚠ **The phase stays, and it stays right: it is «the second desktop», and that is the reason it had been
> put in the plan.** What is removed is **the promise about delay**, which rested on two
> facts and neither of them holds:
>
> | what the line said | what the measurement of 13 Aug says |
> |---|---|
> | «Mutter gives fewer» | ⛔ **it does not reproduce like that**. Renegotiating only the cadence (monitor 120, brake 90) Mutter delivers `[M]` **as much as KWin**. v1's number is not a property of the compositor; ⚠ that it is the remainder of a truncated division is `[R]`, read in the code and not measured (`STUDI.md` §gnome §8.2) |
> | «it is the road to the **40 ms** target» | ⛔ **no.** In the measured capture → glass delay `[M]` Mutter weighs little: **the bulk is ours**, in the capture → first byte segment, **dominated at the time by the software encoder**. ⇒ Changing compositor **would leave encoding untouched** |
>
> ⇒ ⛔ **Whoever arrives at this phase expecting it to bring the delay within the ceiling will be disappointed**,
> and it must be written here so that nobody counts on it when planning: delay **is not cured by changing
> compositor** (`SPECIFICHE.md` §3.2, `DECISIONI.md` §2.5).
>
> > #### ⛔⛔ AND THE OPEN QUESTION HAS BEEN ANSWERED — *and the half promise above has fallen too, 16 Aug 2026*
> >
> > *Here it was written: «⏳ `[?]` **It remains open and has not been measured** how much the number would drop
> > with a **hardware** encoder: it is phase 8's question, not this one's» — and, a line earlier,
> > «delay is cured **on encoding**, and it is **phase 8**».*
> >
> > ⭐ **Measured**, because hardware encoding entered the product on 13 Aug, and the
> > answer is in `fasi/rapporti/F3-E-anello-rimisurato.md`. ⛔ **And it has two faces**:
> >
> > | | `[M]`, same stage, night of 14 Aug — the values in the report |
> > |---|---|
> > | ⭐ **the encoding segment** | it halves: the piece gave way entirely, as the plan hoped |
> > | ⭐⭐ **the frames delivered** | ⭐ **double**. It is the lesson of `LEZIONI.md` §6.2 applied and **passed**: without this number the gain on encoding would have been half the news |
> > | ⭐ **and the other four segments stay where they are** | ⇒ **the architecture is acquitted**: with encoding removed, nothing hidden emerged |
> > | ⛔⛔ **but the TOTAL did not drop** | the codec that makes hardware possible **moves time to the client** — the wait for the frame from the GPU, which for one day was called «the drawing» |
> >
> > ⇒ ⛔ **The bottleneck has MOVED, it has not disappeared**, and now it is in the client, while
> > encoding by now costs little. ⭐ And it shows only because all three rounds existed: with only
> > two one would have read *«victory»* or *«hardware is useless»*, and **both are
> > wrong**.
> >
> > ⇒ ⛔⛔ **The lesson, and it holds for the whole plan**: *«delay is cured in phase N»* was true
> > **on the piece** and false **on the total**. The biggest bottleneck was removed entirely,
> > and the delay the user feels did not improve — the **rhythm** doubled, which is another
> > quantity. ⚠ Whoever writes the next line promising a ceiling from a single phase should write it
> > knowing this.

⭐ **And here one gains something worthwhile anyway**: KWin delivers the full cadence `[M]` without
anything having to be renegotiated, while on GNOME the same result requires a
cadence that **the product today cannot request** (`DECISIONI.md` §2.5-bis). ⚠ It is a gain on
**rhythm**, not on **delay**: they are two different quantities, and `LEZIONI.md` §6.2 exists because they have
already been confused.

**Reused**: `kwin.c` (822 lines), `appunti_wlr.c` (796).

⚠ The traps are already written in `STUDI.md` §kde: `XDG_MENU_PREFIX` without which the capture gate
does not open; no `InaccessiblePaths=` in the drop-in.

> ### ⛔⭐ AND ONE TRAP LEFT THE PLAN ON 17 AUG 2026 — `DECISIONI.md` §5.1-bis
>
> Here there was the third: *«resizing **in the form of the negotiation**, with the guard
> against the infinite loop that does not show on Trixie and appears on the day of the upgrade to
> 6.8»*. ⛔ **It is no longer this phase's work**, because it is no longer anyone's: live
> resizing has left the product — *«non voglio mettere delle eccezioni nel
> progetto»* — and it left **precisely so as not to have a KDE branch different from the GNOME one**.
>
> ⚠ **What this phase must still do, and it is not the same thing**: answer
> `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` to the `ADATTA_TELA` the client sends **at attach and at
> reattach**, so that the page rescales and declares it (`SPECIFICHE.md` §6.3). ⭐ And on KDE it is the **normal case**,
> not the poor branch: KWin ≤ 6.7.4 takes the size from the startup line (`--virtual --width W
> --height H`) and does not change it any more. The code path already exists and is tested on the fake
> host (case 11 of `banchi/04-b31`).
>
> ⭐ **The gain of the cut shows here**: phase 11 no longer has to carry a function, it only has to
> declare a refusal — and the guard against the infinite loop of `kwin!7932`, which would have
> been an invisible defect on Trixie and alive after the upgrade, no longer concerns us.

---

## Phase 13 — XFCE and LXQt

⚠ *It was **phase 12** until 25 Aug 2026: **the safety net** overtook it
(`DECISIONI.md` §4.6-duodecies). **The phase has not changed by a line** — its
place has changed, as already on 16 Aug.*

⚠ *It was **phase 11** until 16 Aug 2026 — same move as phase 11, same reason.*
⛔ **And here a reading trap**: `STUDI.md` §xfce and `STUDI.md` §lxqt carry at the top *«for phase 11»*, but
that is **phase 11 of v1** — they are studies of 8 Aug 2026, written before this plan
existed. ⇒ The number in those two titles **is not this number**, and it must not be chased.

**It produces**: the third and the fourth desktop, which share wlroots and therefore almost everything.

**Reused**: `appunti_wlr.c` already written for this family; the answers to the fourteen questions
are already in `STUDI.md` §xfce §12 and `STUDI.md` §lxqt.

---

## Phase 14 — The log

⭐ *Inserted on **21 Sep 2026**, by the user's decision:*

> *«Attualmente la fase 14 riguarda l'installer, ma la spostiamo in fase 15, alla fase 14 inseriamo
> un sistema di logging serio, che ci siamo dimenticati di realizzare.»*

**It produces**: a serious logging system: what whoever administers the server needs to know
what happened, to whom, and when, without having to read the code.

**Where one starts** `[R]` 21 Sep 2026: today's log was born for **the benches and for whoever
develops**, not for whoever administers.
- ⭐ There is already **a single funnel**, `src/registro.c`: every line has the instant and the area (`avvio`, `quic`,
  `rcp`, `sessione`, `video`, `budget`…), and since phase 10 it says **whose** it speaks of. It is also what
  allows B13.2 to guarantee that the password ends up in no line.
- ⛔ The lines all go to standard error, and they are collected by whoever launched the program. There is no
  **level** (error, warning, information): there is only «normal» and «chatty».
- ⛔ The lines are written **for whoever develops**: marks, references to the documents, internal jargon.

**The questions to put to the user at the opening of the phase** — ⛔ none is decided:
1. **who reads** the log: the server administrator, whoever does support, or both?
2. **where it goes**: the system journal (`journalctl -u remotix`), a file of its own with rotation, or
   both?
3. **the levels**: how many, and which is seen by default;
4. **the access log**: who came in, from where, when, and who was rejected and why.
   It is a thing distinct from the diagnostic log, and it has its own questions (how long it is kept);
5. **the language** of the lines for the administrator.

**The bench**: ⛔ the net's meshes read today's log (the «input id=…» lines, the
witnesses). ⇒ Changing the log without the net underneath would mean breaking them without knowing: the
meshes adapt **in the same change**, and the full net runs after every increment.

---

## Phase 15 — The service

⚠ *It was **phase 14** until 21 Sep 2026: the log overtook it, by the user's
decision.*

> ### ⏳ ⭐ THE TWO PENDING THINGS AFTER LXQt — *the user, 21 Sep 2026*
>
> *«Una volta completato LXQt rimangono 2 cose in sospeso: il discorso degli utenti che devono
> appartenere ai gruppi render/video e la procedura di installazione di Remotix.»*
>
> | | where it stands today |
> |---|---|
> | **the `video`/`render` groups** | ✅ decided and written on 20 Sep 2026, `DECISIONI.md` §7.21: `provisiona.sh` at installation, the product at the first connection. `[M]` only on the `kde` box. ⛔ **BROUGHT FORWARD: a dedicated session BEFORE LXQt** — *«deve funzionare per tutti i DE, non solo per KDE»* (the user, 21 Sep 2026) |
> | **the installation procedure** | it is the heart of this phase: *«packaging, installation»* below |

⚠ *It was **phase 13** until 25 Aug 2026, for the same shift.*

> ### ⛔⛔ AND ONE THING TO DO HERE IS ALREADY MEASURED — *25 Aug 2026*
>
> ⭐⭐ **DISPROVED BY THE MEASUREMENT OF 29 SEP 2026** (`fasi/17-l-installatore.md` §5.2, T2): ten
> tests with real Firefox on the four desktops — stopping the unit (`KillMode=mixed`), killing only the
> parent, killing only the child — **no desktop dies**: parent, PAM helper and child die; the
> stage (started with `setsid --fork`, outside the unit), the session and the programs survive, and at
> reattach the same compositor comes back with the windows. The fact of 25 Aug does not reproduce today.
>
> `[M]` **Stopping the server's unit takes away ALL the users' sessions**, windows
> included: the graphical session lives in its process tree (`KillMode=mixed`). ⇒ ⛔ **Today
> updating the server means throwing everybody out** — the same damage that `DECISIONI.md` §4.7
> forbids anyone to cause by switching off the machine.
>
> ⭐ `SPECIFICHE.md` §5.2 promises *«the session survives the CLIENT»*, and it is true and measured.
> ⛔ *«It survives the server»* **had never been promised, and it is not true.** ⇒ The boundary is now
> drawn there, and **this is the phase that must move it**: updating without stopping anybody.
>
> ⚠ The full finding: `fasi/10-multi-tenant-e-il-budget.md` **§7.5**.

**It produces**: systemd units, packaging, installation, the certificate generated at startup,
the limitation of attempts.

⭐ **And here the web client pays for itself a second time**: the page is **inside the same package**
as the server. No APK, no store, no client version to chase — ⛔ and no case of
«old client against new server», which is precisely what `RCP.md` §9 says it fears.
The client is updated **by reloading**.

⚠ **With one case that remains and must be tested**: the **tab already open** while the server is being
updated. There the old client against the new server really exists, for the duration of a
reload — and it is the only place where version negotiation serves any purpose.

**The bench**: ⛔ **the restore is tested by rebooting**, not by rereading the script. In v1 the first
real reboot showed that two pieces were missing, and neither was in the documents: the disk that
did not mount by itself, and the packages installed by hand months earlier that provisioning inherited
without declaring them (`LEZIONI.md` §2.5-bis).

> ### ⛔⭐ And here the clean-up is done: the bench function does not enter the package — ✅ 11 Aug 2026
>
> *The user's decision, `DECISIONI.md` §7.16: «l'utente deve vedere il desktop senza artefatti,
> come se fosse davanti al monitor del PC … si tiene quello che serve per i test, ma poi nel
> prodotto finale si fa pulizia». ⚠ **Written here, eleven phases before it is needed**, because it is the form
> of decision that gets lost: it holds at phase 13 and is decided at phase 1.*
>
> ⛔ **The binary that gets installed does not contain the bench function of `RCP.md` §7.5** — the two types
> `BANCO_MARCA` and `BANCO_ESITO`. Not switched off: **absent**, not compiled, not reachable.
>
> ⛔ **And it is measured, or it is a good intention**: *«it is not there»* and *«it is there and switched off»* look
> the same from outside. This phase's bench **searches for the marks inside the package's binary** and
> demands **not** to find them — with the positive control that says the tool can find them,
> that is the same marks searched for in the **test** binary, where they are. It is the technique already written in
> `banchi/01-p1-prodotto.sh` of phase 1, which tells a new binary from an old one with eight
> marks and two checks.

---

# ⛔ TRACK B — dissolved on 9 Aug 2026

*There were five phases — A1-A5, the Android client in Kotlin. `DECISIONI.md` §1.6 cancelled them: the
client is a web page, and there is no longer a second product to build.*

⛔ **But nothing of what those phases had to do disappeared with them.** This table
exists so that nobody loses it, and it is the only place where it is written where each piece ended up:

| Dissolved phase | Where its work ended up |
|---|---|
| **A1** — the wire on Android | **phase 1**: the page *is* the client, and the handshake is written only once. The job of second reader passes to the **test client** (§1.1 *(of this document)*) |
| **A2** — video, MediaCodec | **phase 2**, with `VideoDecoder` in place of MediaCodec — and the question *«can the phone cope?»* is settled by the probe (§1.2 *(of this document)*, measurement **S2**) |
| **A3** — mouse and keyboard, the classic mode | **phase 4**, which becomes the phase where **the page's classic interface** is written: `Pointer Lock` in place of *Pointer Capture*, and the shortcuts with their declared limit (`SPECIFICHE.md` §7.3-bis) |
| **A4** — touch and the on-screen keyboard | **phase 4** as well, as the **second layout of the same page**: the seven gestures stay the same, and switching between the two stays **automatic on context** (`DECISIONI.md` §5-bis.0-bis) |
| **A5** — the application's life | ⚠ **it scatters, and one part must be watched**: QUIC migration from WiFi to mobile network is **phase 9** (it is the best reason why QUIC was chosen); reattach is **phase 5**. ⛔ **What changes nature is the background**: a browser tab that ends up behind is slowed down or frozen by the system, and it is no longer a life cycle we govern — it is a thing to **measure and declare** |

⭐ **And DeX does not disappear as a test case** (`DECISIONI.md` §5-bis.0): it remains the place where
window resizing is exercised seriously, because the window is dragged. What changes
is that it is the browser that drags it.

---

## The order, and why

**The wire before the content** (1 before 2): a channel that cannot be opened cannot be
filled either, and protocol defects found with the video inside are three times as expensive.

**Software before hardware** (2-3 before 8): with accelerated encoding from the start, an
image defect has two suspects instead of one.

**The session after movement** (5 after 3): persistence is the hardest thing in the project,
and tackling it before having something to look at means not knowing whether the stage holds.

**A single desktop until phase 9**: the other three open when the chain is closed, otherwise one
chases compositor differences and our own defects at the same time.

⛔ ~~**Android after phase 9**~~ → **Android is no longer there** *(9 Aug 2026)*. The reason that
moved it to the end — *«tests on Android cost ten times those on Linux»* — was solved
at the root instead of being reorganised: **there is no longer a second product to test**. The
job of second reader stays with the **test client** of phase 1, which is cheaper and has the
property that counts: **it is written from the specification, not from the code**.

⭐ **And one thing comes before everything else, which was not there before**: the **browser probe**
(§1.2 *(of this document)*). Not because it is urgent in itself, but because **it decides what gets written**: the QUIC library
depends on WebTransport, the certificate default depends on a measurement, and what the page
must declare switched off depends on the engine. A phase that starts before those answers writes
code that is then thrown away.

---

## The method, in six lines

1. The phase document is opened **before** developing, and it contains the bench.
2. The bench is certified **before** being believed — and **is reviewed first**, before
   the product.
3. One tries to **break**, not to confirm. A green review is «I found nothing».
4. What did not work is written down **even** when it looks bad.
5. A finding is closed with **a measurement**, not with a discussion.
6. The phase closes when **the user has looked and given his opinion** — not when the document is
   full.

---

# ⏳ RESUME POINT — 22 Aug 2026, **evening**

*The day of 22 Aug: **nine agents in two waves**, the coordinator at the merge and at the
acceptance test. ⭐⭐ **Phase 8 opened and closed in one day**, on the user's judgement. And phases 6 and 7
remain with no real defect open.*

## ⭐⭐⭐ What changed for the user

> *«Il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»* · **«per me è ok»**
>
> *In the morning, on the same scene:* *«la distanza fra freccia e finestra è la metà della barra del titolo»*.

| | |
|---|---|
| the **`input → vetro`** loop | **shortened**, **paired** — two rounds that share everything except the binary |
| the gap, **in the user's unit** | **approaches local** |
| ⭐ and **local** is now measured | ⇒ *«non identica: quello è impossibile»* is confirmed by measurement |
| ⭐⭐ **the PAINTED frames** | **rise**. It is not a stopwatch victory |

⇒ The values are in `fasi/08-l-anello.md`.

## ⭐ What is closed, and is not reopened

| | |
|---|---|
| **phases 6 and 7** | ⭐ no real defect open |
| **phase 8** | ✅ **CLOSED on 22 Aug**, `fasi/08-l-anello.md` |
| **phase 9** | ✅ **CLOSED on 24 Aug**, `fasi/09-la-qualita-e-la-degradazione.md` — and the five cures are **on** |
| **`RCP.md` §5.2 and §6.2** | ✅ the two `[?]` closed with measurement: `EncSliceLP` can **not** do temporal sub-layers · the keyframe at the user's canvas stays **well inside** the ceiling |
| **the «double pointer»** | ✅ **does not exist** — disproved by the user's eye, and the agent stopped after a few minutes |
| **the engines** | Linux Chrome ✅ · Linux Firefox ✅ · Windows Chrome ✅ · Android Chrome ✅ · ⛔ Android Firefox out · ⚠ **Firefox on Windows: NOT TESTED** |

## ⛔ And the four real defects found in phase 8 — **none was the target**

the **abandoned keyframe** (`RCP.md` §5.2 forbids it, and it was the spiral) · the **re-encode ladder one
rung short** · the **stride not a multiple of 64** that gave a desktop **skewed without errors, with the
milliseconds already perfect** · and the **product's stopwatch that measured the bench**.

## ⛔⛔ The three new lessons — `LEZIONI.md` §1.26 · §1.27 · §1.28

1. **Two benches on the same MACHINE falsify each other silently.** §1.24 talked about what
   *kills*; this one about what does **not** kill — and it does not give a red, it gives **a plausible number**;
2. **The average colour is blind**: an image wrong on every row has **the same statistics** as
   the right one. *A check must read something that can be wrong, not something that can be averaged*;
3. ⭐⭐ **Two benches that disagree can both be right**: they measure two different
   quantities. ⇒ **And the user's eye was right**: the benches were looking at a shorter piece
   of the real loop, and the missing piece was invisible **because their hand is fake**.

## ⏳ The open points — none is a defect

1. ⛔ **Mutter's wall**: `[M]` one frame at 60 Hz — it did not move during the whole phase, and **nobody
   touched it**;
2. ⛔ **half of phase 8's gain is not explained**: it lies in a segment zero copy **does not
   cross**. `[?]` Hypothesis declared, not measured;
3. ⚠ **the retention of the `pw_buffer` is in force without proof**: the positive control did not
   reproduce the damage. Prudence, not necessity;
4. `[?]` **the gap model predicted badly twice, in opposite directions**. It is a fact about the
   model, **not about the user**, and it is our work;
5. **the datagram on a non-local network** and the **priority of the audio path** (`nice`);
6. **the `AV` measurement** to be taken again with the cured `aoff` — to notice whether the delay comes back;
7. **the 4/18 of 16 Aug** not reproduced: two causes excluded with measurement, one race remains to
   sift;
8. `[?]` **the immortal desktop** — read in the code, not measured;
9. `[?]` **on DeX does the screen respond with the external monitor or with the phone?** The user's phone is needed;
10. **Firefox on Windows**, never tested;
11. ⚠ **the 50 ms ceiling is not verified**, and not because it is a little short: **phase 8's number
    sits on a different boundary**. The two numbers **cannot be compared** — `LEZIONI.md` §1.28 applied to ourselves.

## 🔸 The decisions waiting for the user

- 🔸 **the canvas multiple of 16** (`rcp_misura_ammessa()`): it would make zero copy valid on **every**
  screen, ⛔ but it is a **protocol change** — `RCP.md` §4.5 today demands only even sides;
- 🔸 **`nice` for the whole audio path**;
- 🔸 **is a defect opened upstream in Mutter or not?** (phase 6 §7.1-bis) — an action towards the outside;
- 🔸 **DeX** with his phone;
- 🔸 **`BANCO_MARCA`/`BANCO_ESITO`**: complete the branch or remove the two types;
- 🔸 ~~**on farewell, the stage at rest size?**~~ — **provisional**, it is left as it is
  (`DECISIONI.md` §5.0-septies). *«Per il momento accetto, ma poi ci penserò su.»*

## ⚠ Clean-up to do before the next round

⛔ **Four agents' test servers were left running** on the machine (ports **7746, 7752,
7765-67, 7775**), and they run as `root`. They do no harm at rest, ⚠ **but they would falsify the next
measurement** — which is precisely the error of `LEZIONI.md` §1.26. **They must be switched off before measuring.**

⭐ Alive and wanted: **7730** (the user's) and **7790** (the product with phase 8 inside, which the user
judged).

> ✅ **CLOSED on 23 Aug 2026**: after the reboot and the re-provisioning the machine had **a single
> 7xxx port open, 7900** — verified with `ss -tuln` **before** measuring.
> ⚠ And the rule that came out of it, paid for twice in the day (`fasi/09` `fasi/09-la-qualita-e-la-degradazione.md` §3.17): between two benches
> on the same user **one verifies that the place is free** — no live client **and** no
> stage — ⛔ **one does not count time**. An orphan stage does not give a red: it gives **a plausible number**,
> and that day it was about to have three innocent cures accused.

## How to restart

```
# the product with phase 8 inside
ALBERO=/media/REMOTIX/src/08-prova-src LAV=/media/REMOTIX/tmp/08-prova \
  bash banchi/07-b41-accendi.sh --porta 7790 --hz 0

# the user's yardstick: the arrow↔window gap, in title bars
python3 banchi/08-b67-elastico.py --certifica      # 13 injected faults out of 13

# the whole loop, and ⛔ it GOES RED if the machine is not idle
python3 banchi/04-b30-anello-input.py --certifica  # 57 out of 57, 18 faults out of 18
```

⚠ **Two traps that bit today**: the session's place is **one** and the previous one stays
attached for about twenty seconds · and ⛔ **two do not measure on the same machine** (`LEZIONI.md` §1.26).
