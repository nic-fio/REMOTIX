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
