# Phase 8 — The shortest loop

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new flow is identical (comparison of 30 Sep 2026). User's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

> ⚠ **In the plan this phase is still called «La copia zero».** The title dates from when the phase was
> that single segment. ⛔ **The mandate of 22 Aug 2026 is broader**, and the document carries the name
> of the mandate: zero copy is **one segment out of six**. Whether the plan should be renamed is for the user to decide.

*Opened on 22 Aug 2026. Phases 6 and 7 close with no real defect open.*

---

## 1 · What it must produce

### 1.1 ⭐⭐ The specification, dictated by the user — `SPECIFICHE.md` §3.2-bis

> *«Non pretendo un comportamento allineato al nanosecondo rispetto a una situazione locale, ma che
> gli si avvicini molto. La mia specifica è avere un'esperienza utente **il più vicina possibile a
> una situazione locale, ma non identica**: quello è impossibile.»*

⭐ **And he named the symptom himself, twice, and the second time with a number**:

1. *«quando la finestra di un'app sul desktop remoto viene spostata velocemente, l'effetto visivo è
   **leggermente meno fluido** di quando la stessa azione viene svolta in locale»*;
2. and to the direct question: the distance between the mouse arrow and the window chasing it is
   **«la metà della larghezza della barra del titolo»** ⇒ on a 720 px window, **≈ 360 px**.

⚠ **And he set the register of the work himself**, which is a project fact as much as the rest:
*«è questione di micro-secondi, non di secondi, ecco perché parlavo di ottimizzazione e non di
debug»*. ⇒ ⛔ **There is no open defect in this phase.** There is a ceiling to raise.

### 1.2 ⭐⭐ And the cause has a name: **it is a rubber band**, not a delay

`[R]` In the classic mode the arrow is moved by **the browser**, at the speed of the hand — the system
cursor *and* the arrow we draw, overlaid, **both local** (`pagina.html`, the
Xpra road and its retreat of 14 Aug). The window instead chases it with **all** the
delay of the loop. ⇒

```
gap = speed of the hand × delay of the loop
```

⛔ **The gap is not constant: it opens when the hand accelerates, it closes again when it slows down.** Locally
it is **zero at any speed**. ⇒ The window *swims* relative to the hand.

⭐⭐ **That is why the user said «meno fluido» and not «lento»**, and he said it **before**
anyone knew the cause. ⇒ Whoever reads «fluidità» and goes looking for frames per second
is looking in the wrong place: **the main course is the rubber band**, the frames are the side dish.

### 1.3 ⛔ What can NOT be promised, and must be said now

A network loop **cannot have zero gap**: there is one compositor frame, one page
frame, and the wire in between. ⇒ **The gap can be halved or better, not removed.** ⭐ And this part
was put into the specification by the user himself — *«ma non identica: quello è impossibile»* — so it is not
a prepared excuse: it is the boundary declared before starting.

### 1.4 The account that opens the phase

| | |
|---|---|
| the **input → glass** loop, last measurement | phase 4, 14 Aug — ⚠ **eight days and two phases of cures ago** *(the value, on the binary from before zero copy, is removed with phase 18)* |
| the ceiling of `SPECIFICHE.md` §3.2 (only our part) | **50 ms**, target **40** |
| what the user's eye says | «metà della barra del titolo» *(the ms that derive from it, on the product of the time, are removed with phase 18)* |
| ⛔ and how that number is made | **six segments, none dominant** — written by phase 4 when closing: *no single cure brings the loop to 50: it is phase 8's work* |

⇒ ⛔⛔ **Zero copy, on its own, removed a small part of the loop** (the estimate is removed with
phase 18): **it is not the cure for what the user sees**. This phase must open **all six** segments.

---

## 2 · The bench — *written BEFORE developing*

### 2.1 ⭐ The scene is not invented: it is the user's, measured

`[M]` 22 Aug 2026, from the video shot by the user (`~/Video/Screencasts/`, 404 frames,
GNOME recorder, 17.5 s), stripped frame by frame:

| | |
|---|---|
| the window | **720 × 433** px (a terminal), title bar as wide as the window |
| drag speed | **median 3 400 px/s** · p90 **6 300** · **peaks 12 400** |
| intervals while dragging | 350 out of 403 |

⛔ **The bench reproduces THIS**, not a convenient scene. A slow drag does not show the rubber band,
because the rubber band is proportional to speed.

### 2.2 ⛔ The four rules, and three cost blood

1. ⛔ **One counts the frames the page PAINTS, not the milliseconds of CPU.** Phase 9 of v1
   brought the cost per frame from 41 ms to 6 while the delivered frames **fell** from 29 to
   22.7 (`LEZIONI.md` §6.2). ⛔⛔ And here it bites twice: phase 4 found the growing queue —
   server **39.6/s**, page **34.7/s**;
2. ⛔ **One asks for the encoder by name and verifies that it obeyed.** One that falls back to CPU
   believing itself on GPU produces two measurements under the same label (`LEZIONI.md` §1.8). ⭐ The right
   way is already in the product: `componente_e_hardware()` **asks the component** which formats it
   accepts — a surface, not pixels. ⚠ And «it opened a render node ⇒ it renders on GPU» **proves
   nothing** (§1.11);
3. ⛔ **The before and the after are done with the SAME bench and the SAME scene** (`03-b17-ritardo.py`), or
   they cannot be subtracted. ⚠ And the total is not enough: **the segments** are placed side by side, because the question is
   *«with one segment removed, do the others stay where they are?»*;
4. ⭐⭐ **And the bench measures in TWO units**: milliseconds for us, and **pixels of gap for
   the user**. The second is the only one he can judge without instruments, and it is the one in which he
   dictated the specification. `distacco = velocità × ritardo`: both are declared, never just one.

### 2.3 ⭐⭐ The first number, and it is not a segment

**`input → vetro`, re-measured on the real scene**, with the network part taken out of the way.

⛔ **Until it exists, every other measurement of this phase is born without a «before».**

### 2.4 ⭐ The network is separated, because it is not ours — and it is already measured

`[M]` 22 Aug 2026, 400 shots from the laptop (`wlo1`, **WiFi**) to the server `192.168.0.2`:

| | round trip | one way |
|---|---|---|
| minimum | 1.49 ms | 0.74 |
| **median** | **2.85 ms** | 1.43 |
| p90 | 3.94 ms | 1.97 |
| **p99** | **33.60 ms** | 16.80 |
| maximum | 37.60 ms | 18.80 |

⭐ **97 % under 4 ms**: for a WiFi that is excellent, and it is the answer to the user's remark
*«c'è pur sempre la latenza di rete in mezzo»*.

⇒ ⛔ **But the network does NOT explain the gap**: 2.85 ms are a small part of the loop, and the rest
is ours *(the loop total of the time is removed with phase 18)*. ⭐ *And this is the good news*: if it had been the network's, there would be nothing to
take.

⚠ **Where WiFi does really bite instead**: **3.2 %** of the shots jump to ~35 ms ⇒ **+128 px** of
gap that open all at once. `[?]` And in the user's video there are **six holes in 17.5 s** —
one every three seconds, **same order of magnitude**. It is not a proof, it is a candidate **and it is not
ours**. ⛔ The bench separates them, or one cures something that is not there.

### 2.5 ⭐ The external yardstick: **xrdp**, and it must be measured instead of believed

*The user: «di sicuro siamo avanti a xrdp».* ⛔ `[R]` **Nobody has ever measured it.** xrdp is studied
in depth (`STUDI.md` §12.3 and §gnome) but **only as architecture**; a delay comparison does not
exist in any document.

⭐ **And it can be done**, because xrdp is already on this machine — `LEZIONI.md` §2.7 tells it: until
17 Aug the laptop's session *was* xrdp (`Xorg :10`, `got RFX capture`), and it is the loop that
for two days nobody had counted.

⇒ The same drag, the same window, the same unit: **how many pixels of gap does xrdp make?**
⭐ It is the only number of this phase that the user can judge **by looking**, without trusting me.

#### ⭐⭐ DONE, by the user, on 22 Aug 2026 — and REMOTIX is ahead

> *«Confermo: siamo avanti, e di non poco. Non posso darti i numeri ma già si vede molto bene
> ad occhio.»*

⚠ **It is a judgement, not a measurement**, and it is written that way on purpose: the user declared himself
that he has no numbers. ⛔ Do not cite it as `[M]`.

⭐⭐ **And xrdp was running at LESS than ~2000 px of width**, against our **2560** — specified
by the user right after. ⇒ Two effects, and both must be declared because they pull in opposite directions:

| | |
|---|---|
| ⭐ **in our favour, and it weighs** | xrdp had **at most 78 % of our pixels** to capture, encode and send — less work per frame, hence a loop that *should* be shorter. **And it was behind anyway.** ⇒ The real gap between us is **wider** than what was seen |
| ⚠ **against, and it is why the unit was the right one** | the gap is `velocità × ritardo`, and on a smaller screen the same hand covers **fewer pixels per second** ⇒ xrdp's gap in *pixels* would have come out smaller anyway. ⭐ **But the judgement was in fractions of the title bar**, which scales with the screen: the chosen unit normalised the resolution difference by itself |

⇒ ⭐ **The user's unit held up against a variable nobody had foreseen.** It is the reason
§2.2 point 4 demands it: pixels are compared only at equal screen size, fractions of a bar are not.

⭐ **And on the rebound it answers the question he had been asked and that he did not need to
answer**: *«su xrdp la freccia ti risponde istantanea o un filo indietro?»* — the question was meant
to find out whether xrdp draws the pointer locally (like us) or inside the image. ⇒ **If it drew it
inside the image its gap would be ZERO by construction, and it would have won.** Being
behind, it draws it locally: **the comparison was on equal terms.**

⛔⛔ **And now the trap, because this result is the kind of thing that stops
optimisations.** «We are ahead of the competitor» **is not the specification**. The specification of §1.1 is *«il
più vicino possibile a una situazione locale»*, and the term of comparison the user named
first is **local**, not xrdp. ⇒ The mandate remains the one he gave when opening: *«se possiamo
limare ancora qualcosa allora ok»*.

### 2.6 ⛔ The tool of 22 Aug is NOT enough, and it must be said why

The GNOME recorder runs at **30 frames per second** and **does not record the pointer**
(searched by machine across all 404 frames: the only small moving objects are
the recording indicator and the terminal's text cursor).

⇒ ⛔ **Two defects of the tool, not of the product**:
- **it saturates**: the phenomenon lies between 30 and 60 frames per second, and a ceiling at 30 cannot tell them apart —
  the shape of `LEZIONI.md` §1.21, *a tool that breaks under load lies when it matters*;
- **it loses the pointer**, which is the only thing from which the gap is read. ⭐ *And the irony is
  instructive*: it loses it through the **same mechanism** we use — the cursor taken as
  metadata, outside the pixels.

⭐ **What the video gave anyway, and it is a lot**: the real scene of §2.1, and the six holes of §2.4.

---

## 3 · What was developed

*Eight agents in two waves, the coordinator at the merge. ⛔ One owner for every code
path: two agents on the same file stab each other.*

### 3.1 In the product

| where | what |
|---|---|
| `cattura.c` · `cattura.h` · `figlio.c` | ⭐ **zero copy**: the stage is mounted on the **card road** (DMA-BUF) and the frame no longer leaves the GPU. The **stride is looked at as measured, never computed**; if it is not importable the stage is remounted on memory **declaring it**; on a canvas change zero copy **retries by itself** |
| `codificatore.c` | the DMA-BUF imported **as a VA-API surface** ⇒ `sws_scale` and `av_hwframe_transfer_data` disappear. ⭐ **A keyframe is no longer abandoned** (`RCP.md` §5.2). Re-encode ladder lengthened (`CRF_PASSO` 6→9). The maximum size **is asked of the driver before opening**. The fallback line **named the wrong encoder**: cured |
| `codificatore.c` · `cattura.c` | ⭐ the **segment instrumentation**, ten entries in a row with the **remainder** declared: it is the tool that disproved two of the coordinator's hypotheses |
| `pagina.html` | ⭐⭐ **`REMOTIX.tratti()`**: the product **declares by itself** the client's four segments, **same names on all three drawing roads**, at `[M]` ~4 µs per frame. ⇒ There is no longer any need to rewrite a bench's prologue when the page changes the way it paints |
| `figlio.c` | the diagnostic pass over the pixels moves to a **cadence** instead of every frame (it cost `[M]` 5.34 ms/frame for a log line written **only once**), with the field `pixel_misurati` because `nero == FALSE` can now mean «I did not look» |

### 3.2 In the benches

`08-b67-elastico.py` (+ `-locale.py`, `-lancia.sh`) — **the user's yardstick**: the arrow↔window gap, in ms **and in title bars**, with local as the term of comparison. 13 injected faults out of 13 · `08-D1-*` and `08-D2-*` (eight benches) — the temporal sub-layers and the weight of keyframes · `08-f3-*` — how long the client waits, **without server or network** · `08-f4-*` — zero copy and the mark in the pixels.

⭐ And `04-b30-anello-input.py` **grows**: it reads the live drawing road, and ⛔ **goes red if the machine is not idle** (`carico_della_macchina()`). 57 checks out of 57, 18 faults out of 18.

## 4 · The measurements

### ⭐⭐⭐ The picture, in one table

| | ⭐ **today**, with zero copy | |
|---|---|---|
| **`input → vetro`** — the whole loop | **55.20 ms** | |
| ↳ E · encoding and return | **10.27** | |
| ↳ C · the wait for the frame in the scene | **11.78** | |
| ↳ D · **Mutter's frame** | 16.01 | ⛔ **the wall**: zero copy does not touch it |
| **the gap, in the user's unit** | **0.16 · 0.16** bars | **1.23 × local** |
| ⭐ **the frames PAINTED by the page** | **942 · 926** | |
| ⭐ **local** — the floor, measured (n=254) | **0.142 bars** · 30.05 ms | |

*(The «yesterday» column — the road from memory with `sws_scale`, before zero copy — is removed: it is no longer
valid after phase 18. The qualitative fact remains: zero copy shortened the loop and raised the
painted frames; Mutter's frame did not move.)*

⛔ **The 50 ms ceiling of `SPECIFICHE.md` §3.2 is NOT verified**, and not because it is a little short:
**55.20 sits on a different boundary** — §3.2 measures up to the *frame that leaves*, this one up to the
*glass*. ⇒ **The two numbers cannot be compared**, and it is `LEZIONI.md` §1.28 applied to ourselves.

⚠ **And the spread is declared**: on the earlier binary, from round to round, it was **~15 ms** (the values
are removed with phase 18). ⭐ **What holds up the attribution is not the total: it is the segments.**

### The answers to the questions the phase had in its charge

| | |
|---|---|
| **Can `EncSliceLP` do temporal sub-layers?** | ⛔ **NO** — 7 profiles out of 7, with **two positive controls** (VP9 on the same entrypoint has them; AMD `EncSlice` too) and 6 cells out of 6 in the bytes. ⇒ *«ogni abbandono costa una chiave»* stays, with the measurement below |
| **How much does a keyframe weigh?** | at the user's canvas **0.13 % of the ceiling**, margin **782×** (n=404 real keyframes). At 8K it breaks through *(the measurement of the software fallback, which broke through earlier, is no longer valid after phase 18)* |
| **Does the encoder go on the right card?** | yes, and now it **declares it** instead of falling back silently |
| **The unexplained ~16 ms** | ⭐ **found**: 5.34 of **diagnostics** (every pixel of every frame, for a line written once) and the rest in the producer — ⛔ which **was not Mutter's**: it was our work inside its real-time thread |
| **The 17.48 ms of segment 9** | ⛔ **did not exist** — 0.39-2.80 ms with four benches. ⚠ And the cause **is not yet closed**: contention *lowered* it |

*(The full reports of the nine agents are in sections **§4-A** … **§4-F4** below.)*

## 4-F2 · ⭐⭐⭐ AGENT F2 — **the user's eye was right**, and the two benches were not arguing · *22 Aug 2026, evening*

> ### ⭐⭐⭐ THE DISCREPANCY IS EXPLAINED **WITHOUT** USING «THE USER MUST HAVE BEEN WRONG»
>
> Three candidates knocked down by measurement: ⛔ **the pixels** (1560 · 1920 · 2560 — **twice the pixels,
> ZERO slope**), ⛔ **the hand** (3 169-3 358 px/s
> against 3 400: normalised it moves nothing), ⛔ **the bar** (`barra_px = 720` in all fifteen
> reports: it is the user's window).
>
> ⭐ The fourth remained, the one that always proves the measurer right. **It was not needed:**
>
> ```
> the bench [M]  +  11.6 [M]  +  [?] 4-12  +  [?] 16-40
>                   ↑ the browser's event queue: in the bench it is 0.165 ms
>                     because the hand is SYNTHETIC
> ```
>
> *(The bench's value and the totals, taken on the binary from memory with `sws_scale`, are removed with
> phase 18.)*
>
> ⇒ ⭐⭐ **With the three pieces put back, the account included the user's «mezza barra».** ⛔ **The bench was not wrong:
> it was looking at a shorter piece of the real loop**, and the missing piece was invisible **precisely
> because its hand is fake**. A synthetic hand does not queue up in the browser's event queue.
>
> ### ⭐⭐ And the two benches were not arguing: **they measure two different quantities**
>
> | | | |
> |---|---|---|
> | `04-b30` | ⭐ **the RESPONSE** | contains **the wait** for a frame to be produced |
> | `08-b67` | ⭐ **the AGE** of what is on screen | does not contain it |
>
> `[M]` Same machine, same day: segment 1a **11.55** against **0.165 ms**; and segment 3, the wait
> for the frame in the scene, which A pays and F2 does not *(A's value, on the binary from memory with
> `sws_scale`, and the sum of the two discrepancies are removed with phase 18)*.
>
> ⛔ **And the multiplication of §4-A came out right by COMPENSATION**: it paired the delay of one
> quantity with the speed of the other, and two errors cancelled out. 📖 `LEZIONI.md` §1.28.
>
> ### ⛔⛔ AND TWO THINGS THE DIRECTOR HAD WRITTEN ARE DISPROVED
>
> 1. ⛔ **«The 17.48 ms were contention»** — `[M]` on F2's stage, **with the machine idle**, segment 9
>    measures **17.64 ms** (n=241); **with the machine loaded 15.37**. ⇒ **Contention LOWERED it.** The
>    number was not contention: it was **a wait** that the other bench does not contain (see above). ⚠
>    Contention **exists** and is measured (§4-F1, on the same loop) — **but it was not the culprit**;
> 2. ⛔ **«The whole first wave is contaminated»** — `[M]` **false**: on the gap bench the load
>    inflated nothing (the values, taken on the binary from memory, are removed with phase 18).
>
> ### ⭐ And the state at the user's REAL resolution
>
> `[M]` 2560×1080, laptop idle, all checks green, 13 faults out of 13 recertified *(the values
> of REMOTIX, taken on the binary from memory with `sws_scale`, are removed with phase 18)*.
> **Local at the same canvas**: **30.05 ms = 0.142 bars**, n=254 (B had 29).
>
> ### ⭐⭐⭐ And a FALSIFIABLE prediction, which is up to the user
>
> `[M]` After zero copy the bench gives **0.16 bars** ⇒ on the user's screen the prediction is
> **0.31-0.46 bars**. ⛔ **If the user were still to say «metà barra», this explanation is wrong**
> — and it is written here so that it can be said.
>
> ### ⚠ And the six holes do not reappear
> Much sparser than the user's (the counts, on the binary from memory, are removed with phase 18).
> ⇒ What remains is the **network**: p99 **27.9-35.4 ms** ⇒ **+95…+120 px** that open all at once.

> ### ⭐⭐⭐ THREE THINGS, AND THE FIRST IS THAT **THE USER'S EYE WAS RIGHT**
>
> **1. `[M]` At the user's real canvas (2560×1080), with the laptop idle, resolution has NOTHING to do
> with it.** Run at three canvases with **twice** the pixels in between (1560×888, 1920×1080 and 2560×1080), the
> number does not move. *(The values, on the binary from memory with `sws_scale`, are removed with phase 18.)*
>
> **2. ⭐⭐ The discrepancy lies entirely in what the bench does NOT measure**, and now it is a calculation:
>
> | what the bench does NOT measure | ms | ⇒ bars at 3 400 px/s |
> |---|---|---|
> | `[M]` the browser's event queue (segment 1a, **real** mouse) | + 11.6 | + 0.05 |
> | `[?]` the blind piece on **input** (hand → `event.timeStamp`) | + 4 … 12 | + 0.02 … 0.06 |
> | `[?]` the blind piece on **output** (drawing finished → pixel lit) | + 16 … 40 | + 0.08 … 0.19 |
>
> *(The bench's row and the total, taken on the binary from memory with `sws_scale`, are removed with
> phase 18.)* ⇒ ⭐⭐ **The user's «mezza barra» lay inside the interval the bench itself declared.** There was
> no discrepancy: there were **two different quantities called by the same name**. ⛔ And the candidate
> «the user estimated badly» is closed **without using it**: his eye was the most
> precise instrument of the three of this phase.
>
> **3. ⛔⛔ And our two benches do not argue: they measure two different things, and the difference is
> measured, not assumed.** A measures the **RESPONSE** («I moved, when do I see it?»), B/F2 measures the
> **AGE** of what is on screen during a continuous drag. `[M]` The two segments
> that separate them were taken **today, on the same machine, in the same hour** *(their sum,
> with A's segment 3 on the binary from memory, is removed with phase 18)*.
>
> ⚠ **And a disproof that concerns a correction already under way**: `[M]` on my stage, with the laptop
> **idle**, A's segment 9 measures **17.64 ms** — that is **exactly the 17.5 ms** that F3 gives as
> inflated by contention. ⇒ ⛔ On my bench **that number is not contention**, and the correction of
> −15 ms must be called into question again before it goes into a document.

*To be inserted in `fasi/08-l-anello.md` §4 (measurements), §5 (did not work) and §7 (remains `[?]`).
⛔ Not one line of `src/` was touched, nor one of the benches.*

---

## F2.0 · The resources, the stage and ⛔ **the load, next to every number**

⭐ **Mine, all separate**: port **7765** (product) · **7766** (bridge) · **7767** (spare) ·
user **`provaf8`** (uid 1044, in the `render` group: verified) · tree
`/media/REMOTIX/src/08-f-src` · work `/media/REMOTIX/tmp/08-f` (own ban-file and socket) ·
scene `/dev/shm/remotix-08-f` · Xvfb display `:92` (and `:94` for A's bench).
⛔ **7730 and 7731 — the user's two servers — were never touched**, and 7765 was
**counted free with `ss -tulnp` before** taking it.

**Stage**: server `192.168.0.2`, headless GNOME session, virtual monitor read **from the
compositor** (`«Meta-0» 2560x1080 @ 60.000 Hz`), scene `04-b30-scena.c` full screen,
format **BGRx 8 bit**. Client: Chrome on Xvfb **on the laptop**, road **`bitmaprenderer`**
(the real one), **WiFi** network (`wlo1`) in between. ⛔ Performance **on an integrated Intel UHD 730**.

⛔⛔ **THE LAPTOP'S LOAD GOES NEXT TO THE NUMBER** — `LEZIONI.md` §2.0. ⚠ The laptop has
**4 cores** and is the **CLIENT**: that is where the agents tread on each other. The server has 20 and had
`load 0,08` all day.

| | `load` (1 min) | others' Xvfb | others' Chrome |
|---|---|---|---|
| ⛔ **first wave** (the F2.1 «load» rounds) | **2.4 – 3.2** | 1 – 5 | up to 56 |
| ⭐ **quiet window** (the «CLEAN» rounds) | **0.27 – 0.84** before the round | **0** | **0** |

⇒ ⭐⭐ **And the most useful result of the whole day about load is this**: `[M]` at 2560×1080 the
rubber-band bench gave the same number with the machine loaded and idle (the values, on the binary from
memory, are removed with phase 18). ⛔ **Contention does NOT inflate this bench.** What inflated, if anything inflated, was
another tool — and it must be said, because «all the numbers of the first wave are contaminated» is
false and would make good measurements be thrown away.

⭐⭐ **And zero copy was NOT on in any of my rounds**, verified in two ways:
`[M]` my tree predates the merge (`src/codificatore.c` has **2** occurrences of
«copia zero», the merged one has **10**), and `[M]` my server's log has **0** lines that
name zero copy / DMA-BUF / fallback. ⇒ ⭐ **My numbers are on the EXACT code the user
was looking at when he said «mezza barra».** It is the condition for the explanation to hold. ⛔ And it is also
the reason why, with phase 18, F2's loop values are removed: they belong to the road from
memory with `sws_scale`, which no longer exists.

---

## F2.1 · ⭐⭐ THE NUMBER AT THE USER'S CANVAS — `[M]` 2560×1080, idle machine

*The loop had been measured at the user's canvas, two rounds with the machine idle (delay at the two boundaries,
gap in px and in bars, our piece); the measurements, taken on the binary from memory with `sws_scale`,
are no longer valid after phase 18. What remains is the network measured in the same round: 2.8 ms (4.0 %).*

⇒ ⭐ All checks green (Q0…Q13), **13 faults out of 13** at the recertification done today on
my laptop before starting.

### ⭐⭐ The LOCAL term of comparison, redone at the same canvas — with a real denominator

| | n | the scene | the compositor | ⭐⭐ **the local loop** | ⇒ bars |
|---|---|---|---|---|---|
| `[M]` **2560×1080**, today | **254** | 10.43 ms | 20.52 | **30.05 ms** (p95 32.5) | **0.142** |
| `[M]` 1560×888, agent B, 22 Aug | 29 | 7.29 | 20.01 | 27.58 | 0.130 |

⇒ ⭐ **The floor moves little** (+9 % doubling the pixels, with n going from 29 to 254). *(The
REMOTIX/local ratio, with the REMOTIX of the road from memory, is removed with phase 18.)*

⛔ **A real defect, found and cured**: the copy of `08-b67-locale.py` **on the test machine
was OLD** (md5 `fe9ebcb…` against `78ffc5a…` of the repository), that is the one from *before* the cure
of the single sieve that agent B describes in his §6 point 4. `[M]` With that copy the first
round said **loop 13.51 ms with parts 10.92 + 20.68** — a total **smaller than its
parts**, which is impossible: the same red that B had already paid for, reappeared because the cure had never
reached the machine where the bench runs. ⇒ **A cure is valid only where the bench runs.**

---

## F2.2 · ⭐⭐ THE DISCREPANCY, CANDIDATE BY CANDIDATE — three fall with measurement, the fourth is not needed

### 1. ⛔⛔ **THE PIXELS: refuted.** With the machine idle the delay is **flat**

`[M]` Same bench, same scene, same stage, same hour, **idle machine**, at three canvases:
**1560 × 888** (1.39 Mpx, stride 6 240, **%64 = 32**), **1920 × 1080** (2.07 Mpx, stride 7 680) and
**2560 × 1080** ⭐ *(the user's;* 2.76 Mpx, stride 10 240*)*. *(Delays, gaps and bars, taken on the
binary from memory with `sws_scale`, are removed with phase 18.)*

⇒ ⛔⛔ **Doubling the pixels the number did not move.** Neither of the two boundaries scaled with the pixels,
neither the awkward one nor the convenient one.
⭐ It is the direct answer to the `[?]` that agent A had left open («how much of the 41 ms is
producer and how much is fewer pixels»): **of pixels it is almost nothing**.

⚠ **And the opposite is declared**: in the **first wave**, with the machine loaded, the same rounds
gave an apparent slope (values removed, phase 18). ⛔ **That slope
does not exist**: it was spread between sessions, and with the machine idle it disappears. ⇒ A bench that had
run only once per canvas would have delivered a pixel law **that does not exist**.

⭐ **And F4's stride trap was looked at**: the only canvas with a stride that is not a multiple of 64 is
the **1560×888** — ⛔ **and it is the one that runs the same as the others**. If the crooked stride cost
anything, it would show there. And on all canvases the mark is read `[M]` **at 100 %** (Q3) with
**contrast 1.0** and **shift [0,0]**, and the coordinates are found again **exact at 100 %** (Q5).
⚠ A note on method, because F4 rightly warns: **`08-b67` looks at no average**. The reader
is the certified one of `03-marca.py` (CRC, sync, contrast), the JS-against-numpy check is a
**maximum per cell** (`0,000 su 255` in every round) and Q5 demands **identical coordinates**, not
close ones. ⇒ A skewed image would break the CRC and the bench would say «0 echoes read», not a
green.

### 2. ⛔ **THE SPEED OF THE HAND: refuted**, and removing it the number does not move

`[M]` The synthetic hand did **3 169 … 3 358 px/s** median in the clean rounds, against the user's **3 400**:
**−7 % … −1 %**, inside the spread of his own hand (p90/median = 1.85).
⭐ And the calculation can be removed altogether: normalising every round to **exactly 3 400 px/s** gave
the same thing (values removed, phase 18).

⭐ **And there is a new fact that nobody was looking for**, and it goes in the direction awkward for us: the gap
**measured in pixels** is `[M]` **0.90 – 0.94 times** the product `velocità × ritardo`, over all
fifteen rounds. `[R]` The cause is the bench's trajectory: the serpentine **bounces** at every row,
and around a bounce the rubber band closes again because the hand reverses. ⇒ On a **real** drag,
which does not reverse, the factor is **1.0**: ⛔ **the bench measures a rubber band a bit shorter
than the user's**, not longer.

### 3. ⛔⛔ **THE TITLE BAR: the stupidest and the most lethal — checked first, and it is fine**

`[M]` Read in the report of **all fifteen rounds**: `barra_px = 720`, which is exactly the
width of the user's window measured on his video
(`SCENA_UTENTE.finestra = [720, 433]`, «barra del titolo larga quanto la finestra»).
⇒ **The bench divides by the USER'S bar**, not by one of its own, and there is no hidden factor of 1.8
in there.

⭐ **And now the unit is clean in the second sense too**: agent B ran at **1560 px** of
width dividing by a bar of **720** measured on a **2560** screen — two different screens
under the same fraction. At the user's canvas that doubt **no longer exists**: hand,
bar and screen are his three. ⛔ And the number **did not change** between the two canvases.

### 4. ⭐⭐ **THE ESTIMATE BY EYE: NOT needed, and one does not conclude by exclusion**

⛔ The mandate said: *«this is not concluded by exclusion»*. **There was no need**,
because the account closes by itself. What the bench measures is **`t0` in the page → drawing finished**;
what the user looks at has **three more pieces**:

| | how much | how it is known |
|---|---|---|
| ⭐ **the browser's event queue** (segment 1a) | `[M]` **11.55 ms** median (p75 21.4) | measured **today, on the same machine, with the laptop idle**, by A's bench. ⛔ In the rubber-band bench it is `[M]` **0.165 ms**, because the hand is **synthetic**: the event is born already inside the handler, and the browser's queue is not there |
| `[?]` **the blind piece on input** | 4 – 12 ms | hand → `event.timeStamp`: device, kernel and compositor **of the client**. No page API sees it |
| `[?]` **the blind piece on output** | 16 – 40 ms | drawing finished → pixel lit, `STUDI.md` §web §6.2. ⛔ And for the user **they are really there**: on his screen there is a compositor |

⇒ `[M]` the bench + `[M]` 11.6 + `[?]` 4-12 + `[?]` 16-40, at 3 400 px/s with the factor **1.0** of a
drag that does not reverse. *(The bench's value and the totals, on the binary from memory with
`sws_scale`, are removed with phase 18.)*

⇒ ⭐⭐ **The user's «mezza barra» lay inside the interval the bench itself declared.**
⛔ It was not an imprecise eye: it was a bench that stops **three pieces before the glass** and calls
«the loop» what is the part in the middle.

⚠ **And the piece that holds least is declared**: even setting segment 1a to **zero**, the «mezza barra»
still fitted. The conclusion does not depend on that number.

### 5. ⛔ **The fifth candidate, the LOAD: looked at, and on this bench it does not bite**

See F2.0: `[M]` the same number with the machine loaded and idle. ⇒ ⛔ **The bench
`08-b67` is insensitive to contention**, and its numbers from the first wave **should not have been thrown away** (with phase 18 they are removed anyway:
they belonged to the road from memory).
`[R]` The plausible reason is that the bulk of the loop is **on the server** (which was idle) and
that the client piece is dominated by waits, not by CPU. ⚠ It is an explanation, not a measurement.

---

## F2.3 · ⭐⭐ OUR TWO BENCHES — it is not a disagreement: they are **two quantities**

⛔ The hard fact of the mandate: A and B gave two numbers far apart. Redone **today, on the same machine,
in the same hour, on the same stage, with the laptop idle** (A with `04-b30-anello-input.py`, 1460×888,
`?tela=2d`; F2 with `08-b67-elastico.py`, 1560×888, `bitmaprenderer`). *(The medians, taken on the binary
from memory with `sws_scale`, are removed with phase 18.)*

⇒ ⛔ **The disagreement reproduced, and with the machine idle it was even wider.** And A's canvas
is **smaller**, so the pixels pull in the wrong direction. ⭐⭐ **The two pieces that explain it
are measured today, and both are in A's breakdown:**

| | A, today, clean | F2, today, clean | Δ |
|---|---|---|---|
| **segment 1a** — `event.timeStamp` → the bytes leave | `[M]` **11.55 ms** | `[M]` **0.165 ms** (`riassunto.tratto_1a_ms`) | **−11.4** |
| **segment 3** — the scene receives → the scene **DRAWS** | *(removed, phase 18)* | `[M]` **6.3 – 10.4 ms** (local bench, same field `eco_us → eco_disegnato_us`) | — |

*(A's segment 3, the sum and the residue are removed with phase 18: A ran on the binary from
memory with `sws_scale`, and zero copy then showed that that segment depended on our work
in the PipeWire thread.)*

⇒ ⭐⭐ **The two benches measure two different things, and both are true:**

- **A measures the RESPONSE**: from *that* event to the first frame that shows it. It pays the browser's
  queue **and** the whole wait for the scene's frame. It is the right number for *«I clicked,
  when do I see it?»*.
- ⭐ **F2/B measures the AGE of what is on screen** during a continuous drag:
  `04-b30-scena.c` paints **the LAST input received**, so the echo always names the **freshest**
  event and **does not pay** the wait for the frame. ⛔ **And this is the quantity that governs the
  gap**: the window the user sees is where the hand was `vecchiaia` ago, not where it was
  when a particular event left.

⇒ ⛔ **Neither of the two numbers should be called «the REMOTIX loop» without saying which of the two it is.**
`fasi/08-l-anello.md` §1.4 puts them in a column as if they were the same thing: **they are not**, and
the difference is measured (the value is removed with phase 18).

⚠ **And the multiplication of §4-A must be corrected**: `ritardo di A × 3 400 px/s` paired a
**response** number with an **age** gap. ⭐ That it gave almost the right number is a
**coincidence**: the ~30 ms too many of A's boundary compensated for the three pieces missing at the end.
⛔ Two errors in opposite directions do not make a proof, and §4-A called it *«the proof that the rubber band is
the right model»*. **The model is right all the same** — the fifteen rounds here prove it —
but not for that reason.

### ⛔⛔ And a disproof that concerns a correction already under way: **A's segment 9 is not contention**

`[M]` F3 gives A's segment 9 (17.58 ms) as inflated by contention and re-measures it at **0.39 – 2.80 ms**.
⛔ **On my stage, with the laptop idle (load 0.37 at the start, 0 Xvfb and 0 Chrome of others), the
segment 9 measures 17.64 ms** (n=241, min 10.98, p25 16.2, p75 19.x) — that is **exactly A's
number**. And with the machine loaded it measured **15.37**: ⛔ **contention lowered it, it did not raise it.**

⇒ `[?]` **The two measurements are not reconciled**, and the cheapest explanation is that they do not measure
the same thing: A's segment 9 is *«decoder callback → the frame is READY»*, that is
a **wait** (the first `drawImage` of a `VideoFrame` blocks until the GPU has delivered it) —
`04-b30` already says it on its own: *«segment 9 is not the drawing, it is the wait»*. ⛔ A bench that measures
the **drawing** will find 0.4-2.8 ms and will be right; one that measures the **wait** will find 17 and will be
right too. ⇒ **Before removing 15 ms from a number of the phase, one must write which of the two
the number contained.**

---

## F2.4 · THE SIX HOLES — `[M]` at his resolution they do **NOT reappear**

*(The counts per canvas, taken on the binary from memory with `sws_scale`, are removed with phase 18.
The user had seen 6 in 17.5 s.)*

⇒ ⛔ **Resolution did not make them reappear: they were much sparser than his.** And the detector
works — G11 proves it on an injected hole, and here it found three real ones with their description
(*«5 disegni della scena NON sono arrivati al vetro: il buco è a VALLE di lei»*).

⭐ **The network remains**, and in my rounds it is alive: `[M]` the `ping` running **in the same round** has
p99 between **27.9 and 35.4 ms** and **3.8 – 4.1 %** of the shots above 15 ms ⇒ `[M]` **+95 … +120 px of
gap that open all at once**, that is one sixth of a bar more on one shot out of twenty-five.

⇒ `[?]` **The user's six holes belong neither to the resolution nor to our scene.** Three
roads remain, none closed: **his** WiFi moment, **his real desktop** (a test scene
has no windows, no shadows, no other applications), or the **GNOME recorder** (§2.6: it runs at
30 frames per second and saturates).

---

## F2.5 · ⭐ WHAT THIS SAYS ABOUT ZERO COPY — a prediction the user can disprove

`[M]` F4 measures, **with my very bench**, **0.16/0.16** bars with zero copy (the «before» is removed,
phase 18). ⛔ Those numbers are taken **at the same boundary as mine**, so they have **the same three missing pieces**.
⇒ Applying the same calculation as F2.2 point 4:

| | bars |
|---|---|
| the bench, after zero copy | **0.16** |
| ⇒ **what the user will see**, with the three pieces put back | ⭐ **0.31 – 0.46** |

⇒ ⭐⭐ **A falsifiable prediction, and he can falsify it by looking**: where before he said «metà
della barra del titolo», he should now say **«a third, or a little less»**. ⛔ If he still said
«metà», then **the explanation of F2.2 is wrong** and must be redone. It is the right way to close
this phase: not with a number of ours, but with a prediction his eye can disprove.

---

## ⛔ WHAT DID NOT WORK

1. ⛔⛔ **Chrome's `--window-size` is NOT respected, and for three rounds I measured a wrong canvas
   believing it the right one.** `[M]` Asking for 2600×1192 the canvas came out **2544×960**; asking for
   2616×1312 it came out **the same**. `[R]` The cause, read in the profile and not deduced: Chrome saves in
   `Preferences → browser.window_placement` a placement **`maximized: true`** with
   `work_area 2560×1080`, and on Xvfb — **without a window manager** — it reopens maximised to
   that area ignoring the flag. ⛔ **The bench declared the flag** (`--window-size=2600,1192`
   is in the report) **but nobody compared it with the canvas obtained**: it is the shape of `LEZIONI.md`
   §2.0 in person — *a stage declared and not verified*.
   ⇒ **Cure**: a separate piece (`forza.py`) that from outside calls `Browser.setWindowBounds` via
   CDP as soon as Chrome opens the debugging port, **re-reads the bounds obtained** and prints them. And the
   real check is in the bench: the line `tela 2560x1080` is read **before** taking the number,
   and the rounds with the wrong canvas **are thrown away**. ⚠ I threw away three.
   ⭐ **It must be put inside `08-b67`**: today the remedy is in the head of whoever launches.

2. ⛔ **The local bench on the machine was an old copy**, and it gave a total smaller than its
   parts (see F2.1). ⚠ I did not take it at face value because the account did not add up — but a distracted
   reader would have written «the local loop is 13.5 ms» in a document.

3. ⛔ **The local loop at 1560×888 did NOT come out**: `[M]` **n = 12**, then **1**, then **1** over three
   attempts. `[R]` The cause is synchronisation: the local bench samples `/dev/shm` **from outside** and sees
   the echo change only while the hand moves; starting them by hand with a `sleep` is a
   fragile coupling, and two times out of three the window fell **before** the hand started
   (the entry and the measurement of the shift cost ~35 s). ⇒ **The local number at 1560 in this
   report (26.40 ms) has n = 12 and is read as an indication, not as a measurement.** The cure is for the
   local bench to be launched **by the rubber-band bench**, not by the agent.

4. ⛔ **Five rounds lost to an orphan `/tmp/.X11-unix/X92`.** When a round dies badly the Xvfb socket
   remains, and the next round refuses to start — rightly (`03-b17` does not share a
   display), but **the remedy (`rm -f`) is in the head of whoever launches**, not in the bench.

5. ⛔ **A's bench cannot be run at the user's canvas**, so the A↔F2 comparison is at
   **1460/1560**, not at 2560. `[R]` `04-b30-anello-input.py` builds the stage with
   `finestra=(1500, 1000)` **written in the source**, and the Xvfb is born accordingly at 1600×1200: a
   2600 window does not fit and `forza.py` cannot widen a display. ⇒ `[?]` **A's number
   at 2560×1080 does not exist**.
   ⚠ **And the same bench calls the ground WITHOUT an environment** (`_sudo("bash %s scena-avvia")`): with the
   defaults it starts `provao2`'s scene. I had to write a ground of my own around it
   (`/media/REMOTIX/src/08-f-terreno.sh`) which is just `04-b32-terreno.sh` with my variables.

6. ⛔ **Two rounds of A came out RED because of a defect of the bench, not of the product**: `[M]` *«il
   seqlock non si è fermato (seq 47482 e 47484)»* and Q4(a) without frames to show ⇒ verdict
   NOT COMPLIANT **while the time breakdown was complete and sound** (n = 241, the sum of the segments
   matched the total). ⇒ ⚠ **The A numbers I cite come from a round whose verdict is red**,
   and I say so instead of hiding it: they are good for the **comparison between segments**, not for being
   delivered as «the loop».

7. ⚠ **The cost of the bench is inside every number**: `[M]` reading the two marks costs
   **7.5 – 10.5 ms median per frame**, on the **main thread**, that is the one that decodes and
   paints. ⛔ It is a systematic error that **lengthens** my times (so it does not inflate our
   advantage) and **grows with the canvas** (7.5 at 1560, 8.5 at 1920, 9.5-10.5 at 2560): ⇒ ⭐ the real
   pixel slope is **even flatter** than the one I wrote — that is **negative** if one
   removed the cost of the bench.

8. ⛔ **I wrote on the common log of rounds**: `banchi/08-b67-esiti.jsonl` has my fifteen
   rounds next to B's. They are distinguished by name (`f2-*`), ⚠ but **the round's name is not a
   rule** — it is the same remark agent A had already made to himself.

9. ⛔ **My tree was REBUILT at 18:44 while I was working** (md5 different from the starting
   one, new `.o`), almost certainly by A's bench. ⇒ ⚠ **The rounds before and after 18:44 do not
   run on the same binary.** I verified that **the sources are the same** and that zero
   copy is in neither, and the numbers before and after coincided (values removed, phase 18) — but
   **I did the verification afterwards, and it could have gone differently.**

---

## `[?]` WHAT REMAINS OPEN

| | |
|---|---|
| ⏳⏳ **the blind piece on OUTPUT is half of my interval** | `[?]` 16-40 ms is a **24 ms bracket** taken from `STUDI.md` §web §6.2, and on its own it moves the result by ~0.11 bars. ⛔ Until it is measured, two readings a tenth of a bar apart are indistinguishable **for us** and not for the user. ⭐ It is the `[?]` worth most in the whole phase |
| ⏳ **segment 1a with a REAL mouse** | `[M]` 11.55 ms, but it is taken from A's bench with its 70 ms hand. ⭐ The `--mano cdp` road of `08-b67` (*trusted* events delivered by Chrome) is planned and **has not yet been run**: it is the right measurement, and it would close the biggest piece that remains `[?]` in my account |
| ⏳ **A's segment 9: 17.6 or 2.8 ms?** | ⛔ the two measurements are not reconciled (F2.3). Before correcting a number of the phase one must write **which of the two** it contained |
| ⏳ **the local loop at 1560×888** | n = 12: to be redone with the local bench launched **by** the rubber-band bench |
| ⏳ **the six holes** | they are not the resolution's. What remains is his WiFi, his real desktop, or his recorder |
| ⏳⏳ **the REAL desktop against the test scene** | ⛔ no bench of this phase measures a desktop with windows, shadows and compositing: they measure **a single full-screen scene**. It is the last difference between the bench and the user that has **not** been quantified, and it pulls in the awkward direction |
| `[?]` **the encoder** | `08-b67` does **not** verify that encoding is in hardware. `provaf8` is in the `render` group (verified: `groups=1044(provaf8),44(video),991(render)`), ⛔ but «it opened a render node» proves nothing (`LEZIONI.md` §1.11) |

---

## How to rerun it

```bash
# on the laptop, from the repository root
python3 banchi/08-b67-elastico.py --certifica          # 13 faults out of 13 (redone today)
bash <scratch>/fase8/f2.sh utente ; sessione ; accendi ; ponte ; parola
(python3 <scratch>/fase8/forza.py 2600 1192 9645 60 &)  # ⛔ without it, the canvas comes out 2544x960
bash <scratch>/fase8/f2.sh scena-avvia
bash <scratch>/fase8/f2.sh misura 2600 1192 25 nome     # ⛔ and the line «tela 2560x1080» is VERIFIED
bash <scratch>/fase8/carico.sh                          # ⛔ before and after every round
```

⚠ **Left running on the machine**: product on **7765**, bridge on **7766**, scene, and
`provaf8`'s GNOME session. They are switched off with `f2.sh spegni` — ⛔ which touches **only** my things.
⚠ **In the repository** `banchi/08-b67-esiti.jsonl` and `banchi/04-b30-esiti.jsonl` remain modified
(the round logs) and **nothing else**: `src/` was not touched.


---

## 4-F4 · ⭐⭐⭐ AGENT F4 — **ZERO COPY IS DONE**, and we are at 1.23 times local · *22 Aug 2026, evening*

> ### ⭐⭐⭐ THE NUMBER THAT CLOSES THE MANDATE, IN THE USER'S UNIT
>
> | | title bars | |
> |---|---|---|
> | **local** — the floor, measured by B | **0.13** | |
> | ⭐ **REMOTIX, after zero copy** | **0.16 · 0.16** | **1.23 × local** |
>
> *(The «before» row, on the road from memory with `sws_scale`, is removed: it is no longer valid after phase 18.)*
>
> ⇒ ⭐⭐ **At 1.23 times local.** The user's specification was *«il più vicino possibile a
> una situazione locale, ma non identica: quello è impossibile»* (§1.1): **zero copy has
> closed a large part of the divide.**
>
> ⛔⭐ **And the rule that could bring everything down is respected**: `LEZIONI.md` §6.2 says that a
> gain in milliseconds that does not become frames **is not a gain**, and in this very phase
> it had already happened twice (C removed milliseconds without raising the frames). ⇒ `[M]` **The frames
> PAINTED by the page rise** (942 and 926 after; the «before» is removed, phase 18). It is not a victory of milliseconds.
>
> ### The segment, and the sub-segments side by side
>
> `[M]` `cattura → byte fuori`: **6.41 ms** with zero copy (⛔ the «before», on the road from memory with
> `sws_scale`, is removed: it is no longer valid after phase 18). Three **alternating** rounds (A-B-A-B
> on the same tree), md5 verified different, canvas 1920×1080, **zero copy verified on at
> every round**. Machine: 20 cores, load 1.31-1.65, 0 Chrome, 0 Xvfb — **the load is declared**,
> as §4-F1 demands.
>
> | | after *(card)* |
> |---|---|
> | the copy | **0.00** |
> | the conversion (VPP) | **2.98** |
> | the upload to the GPU | **0.00** — the segment is no longer there |
> | ⭐ **the producer** | **0.64** |
>
> *(The «before» column, on memory with `sws_scale` and `av_hwframe_transfer_data`, is removed: phase 18
> replaced that road, and the measurement is no longer valid.)*
>
> ### ⭐⭐ And «Mutter's ms» were almost all OURS — C disproved
>
> §4-C had written that that time was Mutter's and that more than a third of the margin was not ours
> *(its value, on the binary from memory, is removed with phase 18)*. ⛔ `[M]`
> **The producer drops to 0.64 ms** by removing **our work** from PipeWire's real-time
> thread. ⇒ It was not the compositor: **it was us, inside his house.**
>
> ### ⛔⛔ And the real defect found **with the milliseconds already perfect**
>
> `[M]` The **iHD driver does not honour a stride that is not a multiple of 64 bytes**: it reads the rows at a stride
> of its own and the desktop comes out **skewed by a few pixels per row, without any error**.
>
> | canvas | stride | %64 | mark |
> |---|---|---|---|
> | 1920×1080 | 7680 | 0 | ⭐ read, contrast 1.000 |
> | 1552×888 | 6208 | 0 | ⭐ read, contrast 1.000 |
> | 1544×888 | 6176 | 32 | ⛔ **NOT read** |
> | 1560×888 | 6240 | 32 | ⛔ **NOT read** |
>
> ⛔ **1552 and 1544 are eight pixels apart and give opposite verdicts.**
>
> ### ⭐⭐⭐ And the thing to put in `LEZIONI.md`: **the colour check is BLIND to this defect**
>
> `[M]` The per-channel averages of the two flows (memory and card) match while the mark
> **is read on 0 frames out of 903** (the discrepancy in levels is removed: one side went through `sws_scale`, phase 18). Negative control (R↔B swapped): discrepancy **33**, that is
> the tool works.
>
> ⇒ ⛔⛔ **A bench that looks at averages says GREEN on a wrong image.** It is the shape of
> `LEZIONI.md` §1.20 applied to **pixels** instead of judgements: *the measurement is good and does not look at
> the thing that counts*.
>
> **The cure**: the stride is looked at **as measured**, never computed, before compressing; if it is not
> importable the stage is remounted on memory **declaring it**; on a canvas change zero copy
> retries by itself. `[M]` Same canvas 1560: **0 echoes out of 903 → 831 out of 831**.
>
> ### ⭐ And the release: the cure is implemented, **but the injected fault did NOT confirm it**
>
> The retention of the `pw_buffer` is in force (6 buffers against 4, **0 replaced out of 1 800**). ⛔ But the
> positive control **did not reproduce the damage**: 10 marks out of 10 even **without** the GPU wait.
> ⇒ ⚠ **It remains prudence, not measured necessity**, and it is written that way.
>
> ⭐ **The fault was useful all the same**: without `vaSyncSurface` the conversion drops 2.86 → 0.38 and
> encoding rises 2.43 → 4.67, total 6.19 → 6.05. ⇒ **The wait costs zero** and says where the right release
> point is.

> ### ⭐⭐ THE RESULT IN TWO LINES, and the second is worth more than the first
>
> `[M]` The `cattura → primo byte` segment drops to **6.41 ms** (the «before» on `sws_scale` is removed,
> phase 18), three **alternating** rounds, and ⭐ **this time the frames RISE at the user's yardstick too**: the gap
> measured with B's bench drops to **0.16 title bars**, with **942** frames
> painted in 25 s (the «before» is removed, phase 18). The local floor measured by B is **0.13**: we are
> at **1.23** times local.
>
> ⛔⛔ **And I found the real defect after seeing those numbers.** Zero copy worked, the
> segment had dropped, and **the desktop came out skewed by a few pixels per row** — without
> any error, on any log line. The iHD driver, importing the DMA-BUF, **does not honour a
> stride that is not a multiple of 64 bytes**.
>
> ⭐⭐⭐ **And the part that is method, not anecdote**: `[M]` the COLOUR check **does not see it**.
> The per-channel averages of the two flows matched — while the certified mark reader read
> **0 marks out of 903**. ⇒ *A bench that looks at averages says green on a wrong image.* The number that
> discriminates is the **structure**, not the intensity.

*22 Aug 2026. Test machine NIC-OS (Intel i5-13500T, **integrated Intel UHD 730 iGPU** on
`/dev/dri/renderD128`, iHD 25.2.3), user `provaf48` (uid 1046), port **7775**, tree
`/media/REMOTIX/src/08-f4-src`, work `/media/REMOTIX/tmp/08-f4`.*

> ### ⛔ AND THE FIRST THING IS THE PORT, again — «08-f» was not free
>
> `[M]` `pgrep -ax remotix` before touching anything: **another phase 8 agent** was running
> at that moment with user **`provaf8`**, tree `/media/REMOTIX/src/08-f-src`, work
> `/media/REMOTIX/tmp/08-f` and port **7765**. ⇒ Mine is called **`08-f4`** everywhere, the user is
> **`provaf48`** (uid 1046), and ports **7775 · 7776 · 7777** were **counted with `ss`** before
> taking them. ⛔ 7730 and 7731 — the user's servers — were never touched, and they are counted
> before and after every step.

---

## F4.1 · What was changed, and why

| file | what |
|---|---|
| `src/cattura.h` · `src/cattura.c` | ⭐ the **retention** of the `pw_buffer`, the DMA-BUF descriptor inside `CatturaFermo`, the **generation** of the buffers, the measurement of the first frame's pixels via `mmap` |
| `src/codificatore.h` · `src/codificatore.c` | ⭐ the import of the DMA-BUF as a VA-API surface, the **conversion on the GPU** (VPP) in place of `sws_scale` + `av_hwframe_transfer_data`, the import cache, ⛔ **the guard on the stride** |
| `src/figlio.c` | ⭐ the road is requested as **CARD**, and it falls back to **MEMORY declaring it** when the frame is not usable |

⛔ **Not one line was touched** of `src/pagina.html` nor of the `04-b30-*` and `08-b67-*` benches.

### What zero copy does, in one line

The frame **no longer leaves the GPU**. The DMA-BUF that Mutter delivers is imported as a VA-API
surface (`vaCreateSurfaces` with `VA_SURFACE_ATTRIB_MEM_TYPE_DRM_PRIME_2`) and converted to NV12 with
the **card's VPP** (`VAEntrypointVideoProc`), directly into the surface that the
encoder consumes.

⚠ **And what it does NOT remove, and it is the half nobody expects**: the colour conversion **must
be done anyway**. Mutter delivers BGRx, `hevc_vaapi` wants NV12. ⇒ It is not «no conversion»: it is
**who converts** — the GPU instead of the CPU, on the memory it already has underneath instead of on eight
megabytes passed twice across the bus. That is why its cost stays in the
`conversione` entry, under the **same label as before**: putting it in a new entry would have made
the comparison with the «before» impossible. ⛔ `caricamento` instead goes to **0**, and there zero means
**«this segment is no longer there»**, not «it is free».

---

## F4.2 · ⛔⛔ THE REAL DEFECT — the DMA-BUF stride, and eight pixels that change the verdict

`[R]` The iHD driver, importing a DMA-BUF, **does not honour a stride that is not a multiple of 64 bytes**:
it reads the rows at a stride of its own, and the image comes out **skewed by a few pixels per row**.

⭐ **Four canvases chosen on purpose on both sides of the threshold**, read with the **certified reader**
of the mark (`banchi/03-marca.py`, negative control `[M]` 0 false out of 3 000 noise probes):

| canvas | stride | stride % 64 | is the mark read? | contrast |
|---|---|---|---|---|
| 1920×1080 | 7680 | **0** | ⭐ YES (drawing 65) | **1.000** |
| 1552×888 | 6208 | **0** | ⭐ YES (drawing 70) | **1.000** |
| 1544×888 | 6176 | 32 | ⛔ **NO** | 0.617 |
| 1560×888 | 6240 | 32 | ⛔ **NO** | 0.510 |

⭐ **1552 and 1544 are EIGHT pixels apart and give opposite verdicts**: it is not a threshold chosen after
seeing the result, it is a boundary to the pixel. ⚠ And the stride is exactly `larghezza × 4` in all four,
modifier **LINEAR**, **read from the chunk** and never computed.

### ⭐⭐⭐ And the thing that goes in `LEZIONI.md`, not in a footnote

⛔ **The colour check does not see this defect.** On the same pair of flows, 40 frames
each, 2 241 760 samples:

| | mean R | mean G | mean B | min/max | at zero | at 255 |
|---|---|---|---|---|---|---|
| card (GPU, VPP) | 96.969 | 113.891 | 130.170 | 0 / 255 | 6.41 % | 1.79 % |

*(The memory row, converted with `sws_scale`, and the discrepancy between the two are removed: phase 18
replaced that conversion.)*

⭐ And the **negative control** of the same bench — the same flow with R and B **swapped by hand** —
gives discrepancies of **33.27 and 33.14**: the bench *can* say no, and that green is not by construction.

⇒ ⛔⛔ **The averages matched while the mark was read on 0
frames out of 903.** A tool that looks at intensities is blind to a **geometric** defect.
⭐ Whoever certifies a chain of images must have at least one check that looks at the **structure**.

### The cure, and why it is this one

⛔ **The stride is looked at as MEASURED, never computed** (`cattura.h` rule 1), **before compressing**. If
it is not a multiple of 64 the frame **is not sent** and the stage is **remounted on MEMORY
declaring it**; on a canvas change zero copy **retries by itself**, because a single crooked canvas
must not switch it off for the whole session.

`[M]` The cure tried live, and **the verdict is given by the bench, not by the eye**: same canvas **1560**,
same «card» binary, **before** the cure **0 echoes read out of 903** — **after** the cure **831 out of 831
(100 %)**, because it falls back to memory and the image is right. The log line says which of the
two cases it is.

⚠ **And the full cure is NOT mine to make**: the stride is decided by the producer and it makes it equal to
`larghezza × 4` `[M]`. ⇒ A canvas **that is a multiple of 16** would always have the good stride, but the canvas rule
lives in `rcp_misura_ammessa()` (today: only «even»), which is **normative** in `RCP.md` §4.5
and does not belong to this file. 🔸 **Passed to the director for the user**, not cured on the sly.

---

## F4.3 · The cure of the RELEASE, and ⛔ **the injected fault did NOT confirm it**

⭐ **Implemented the one decided by C**: the **`pw_buffer` is retained** until reading is finished, and
`SPA_META_SyncTimeline` is **not** requested. The retention is **ours** and holds on every producer; the timeline
depends on what the producer offers, and when it is not there **there is no error** — there is the
screen that alternates (`LEZIONI.md` §8, §1.25).

**How it is made**: `cattura_fermo_libera()` **is** the release; the buffer goes back to PipeWire only there.
The moment at which «the GPU has finished» is the `vaSyncSurface()` inside the conversion: when
`codificatore_comprimi_scheda()` returns, the card has **finished reading**, and only then does
`figlio.c` give the buffer back. ⛔ And two things the box imposes: the buffer that was in the slot is
given back **before** overwriting it, and a buffer that PipeWire has **removed** (`remove_buffer`) is not
given back at all — the `CatturaFermo` carries the **generation** it was born with and the comparison decides.

**The price, counted**: `[M]` on the card road **six** buffers are requested instead of
four, because we retain at most two (one in the slot, one in the hands of the reader). Mutter
grants them: `[M]` **«6 buffer distinti»** against **«4»** on memory, and **«sostituiti nel posto 0»**
over 1 800 frames ⇒ the retention does not starve the producer.

### ⛔ THE INJECTED FAULT, and the result is a NO

Removed **only the wait line** (`vaSyncSurface`) leaving everything else — the buffer goes back to
Mutter while VA-API is still reading it, which is **exactly** the mechanism of §8. Binaries
verified different by md5.

⭐ **The fault really was traversed, and the segments say so**:

| | conversion | encoding | total |
|---|---|---|---|
| healthy (with the wait) | **2.86 ms** | 2.43 | 6.19 |
| fault (without the wait) | **0.38 ms** | **4.67** | 6.05 |

⇒ ⭐⭐ **Removing the wait buys nothing**: the time moves from `conversione` to `codifica`,
because the encoder waits anyway for the VPP it depends on. **6.19 → 6.05 ms**, within the
spread. ⇒ Explicit synchronisation **costs zero** and in exchange gives the right release
point: it is a line one keeps without paying for it.

⛔ **But the corruption did NOT show up**: `[M]` **10 marks read out of 10** with the fault on,
contrast **1.000** on all ten, against **10 out of 10** for the healthy one. ⇒ **On this scene and on this
machine the retention is not shown to be necessary.** The mechanism of §8 remains `[R]` (read in
Mutter), not `[M]`. ⚠ The plausible explanation is that with six recycled buffers the window never
opens: the VPP finishes in ~3 ms and a buffer comes back around after ~100 ms. ⇒ The retention remains
**prudence with a documented mechanism and a measured price (two buffers)**, not a cure with a
measurement under it. **It must be said that way.**

⛔ And the accumulation surface was **not** redone: Mutter's DMA-BUF is not a diff.

---

## F4.4 · ⭐⭐ THE BEFORE AND THE AFTER — three **ALTERNATING** rounds, the segments side by side, the frames next to them

⛔ **The stage, next to the number** (`LEZIONI.md` §2.0), and today it counts double: `[M]` a segment given as
17.48 ms turned out to be between 0.39 and 2.80 when the machine was not hammered by other benches.

*Test machine, **20 cores**, load **1.31-1.65**, **17** `remotix` processes and **5**
`gnome-shell` of other benches alive, **0** Chrome and **0** Xvfb. Canvas **1920×1080** — ⭐ **stride 7680,
multiple of 64: zero copy was REALLY on**, and the log line «il palco si monta sulla
strada SCHEDA» was verified at every round. Codec **HEVC in hardware** — `[M]` from the log:
«hevc_vaapi (in HARDWARE · /dev/dri/renderD128 · Intel iHD 25.2.3 · ⚠ EncSliceLP, bassa potenza)»,
asked of the **component** (`componente_e_hardware()`: it accepts a surface format) and
the entrypoint **read from the driver**, not from ffmpeg.*

⛔ **Alternating and not in a row** (A-B-A-B on the same tree): the two binaries come from the **same
source**, **one constant** changes (`COPIA_ZERO`), and the bench **verifies that the md5s differ**
before measuring.

| segment | **after** *(card)* |
|---|---|
| ⛔ **producer** *(Mutter's pts → our callback)* | **0.64** |
| allocation | 0.00 |
| ⭐ **copy** | **0.00** |
| in the slot | 0.08 |
| measurement | 0.00 |
| ⭐ **conversion** (VPP) | **2.98** |
| ⭐ **upload** | **0.00** |
| encoding | 2.47 |
| sending | 0.05 |
| remainder | 0.17 |
| **TOTAL** | **6.41** |
| **frames in 45 s** | 1 519 · 1 506 · 1 454 |

*(median of the three rounds per row; the three agree — `conversione` 2,91/2,99/2,98; `totale`
6,34/6,48/6,41.)*

⚠ **The «before» column — the road from memory, with `sws_scale` and `av_hwframe_transfer_data` — is
removed, along with the differences**: phase 18 replaced that road and the measurement is no longer valid. What remains is the
decision: zero copy, because it removes the copy, the conversion on the CPU and the upload to the GPU.

### ⛔ What this table says, and what it does NOT say

1. ⭐⭐ **The «Mutter» ms were not all Mutter's.** C had written *«more than a third of the
   margin is not ours: there is nothing to trim, it is the compositor»*. `[M]` The `produttore` entry
   drops to **0.64 ms** by removing **our** work from the real-time thread and from the
   memory bandwidth (the «before» is removed, phase 18). ⇒ **They were almost all ours**, and it is the biggest disproof of today;
2. ⛔ **The frames delivered by the child did NOT rise** (within the spread):
   at **33/s** on a scene that draws 61 the bottleneck is not our CPU. It is the mild
   form of `LEZIONI.md` §6.2, and it must be said;
3. ⛔ **C's budget was exceeded, and not because the estimate was timid**: besides the three
   entries foreseen a fourth fell that nobody was counting (`produttore`) — the milliseconds of the
   «before» are removed (phase 18). ⇒ **In this segment the entries are not independent in
   either direction**: they pass each other the cache (C), and they pass each other the real-time thread (me).

---

## F4.5 · ⭐⭐⭐ THE USER'S YARDSTICK — the gap in title bars

⛔ The bench is **B's** (`banchi/08-b67-elastico.py`, **13 injected faults out of 13 accused**,
recertified today before use): no other was invented and not one line of it was
touched.

*Laptop **4 cores**, load **0.21-0.76**, **0 Xvfb** and **1** Chrome of others (quiet
window granted by the director). Test machine 20 cores. **Real WiFi** network in between.
⭐ Window **1608** ⇒ canvas **1568×888**, **stride 6272, multiple of 64: zero copy was on in
both «card» rounds**, verified on the log round by round.*

| | **after** *(card)* |
|---|---|
| ⏱ delay, AWKWARD boundary | **39.0** · **38.7** ms |
| 📏 gap | 117 · 116 px |
| ⭐⭐ **gap in title bars** | ⭐ **0.16 · 0.16** |
| 🖼 **frames painted in 25 s** | ⭐ **942 · 926** |
| echoes read (Q3) | 942/942 · 926/926 (100 %) |
| bench verdict | COMPLIANT |

*(The «before» column, on the road from memory with `sws_scale`, is removed: it is no longer valid after phase 18.)*

⇒ ⭐⭐ **AND HERE THE FRAMES RISE TOGETHER WITH THE MILLISECONDS**: by the
rule of §2.2 point 1 **this is a real victory**, and C's was not.

### ⭐⭐ The line that counts, in a single unit

| | title bars | ms |
|---|---|---|
| **local** (the same compositor, without us — measured by B) | **0.13** | 27.6 |
| ⭐ REMOTIX **after** | **0.16** | 39.0 |

*(The row of the user by eye, on his session from before zero copy, is removed with phase 18.)*

⇒ ⭐⭐ **At 1.23 times local**: on top of the compositor we add **~11 ms**. *(The row «before
zero copy», on the road with `sws_scale`, is removed: phase 18.)*

⚠ **And the comparison with the user's judgement is NOT made from here**: he looks at **2560** px and on a
real desktop, the bench at **1568** and on a scene. The discrepancy between bench and eye remains the `[?]` that B
opened.

### ⛔ And on a «crooked» canvas the after IS THE BEFORE — declared, not hidden

`[M]` Same bench, window **1600** ⇒ canvas **1560×888** (stride 6240, **not** a multiple of 64):
the log writes the refusal line and the stage is remounted on **MEMORY**. ⇒ On that canvas the
«after» **is the old path**, and whoever compared the two numbers would compare the same
thing twice. ⭐ The image however is **right** (831 echoes out of 831, 100 %), which is precisely what the cure
exists to guarantee.

---

## ⛔ What did NOT work

1. ⛔⛔ **Zero copy produced a wrong image for three bench rounds, and the milliseconds
   were perfect.** The stride not aligned to 64. Found only because B's bench reads a
   **structured** mark: my colour bench said green.
2. ⛔ **My first diagnosis of that defect was wrong.** I had blamed the VPP regions
   left at `NULL` (which scale from 1080 to 1088 rows). I fixed them — and it was a right and
   necessary cure — **but the red stayed identical**. The cause was another.
3. ⛔ **And even before that I had suspected the ORDER of the rounds** (the card always ran second).
   `[M]` Redone with the card first: same red. ⇒ A confounder excluded with a measurement
   instead of with reasoning — and it could be excluded in three minutes.
4. ⛔ **The fault injected on the release did not reproduce the defect of §8**: 10 marks out of 10 read
   even without waiting for the GPU. The retention remains prudence, not measured necessity. See F4.3.
5. ⚠ **The diagnosis of the «BLACK frame» is poorer on the card road.** On memory one
   looked at a cadence (500 ms); on the card one looks **only once**, mapping the DMA-BUF —
   `[M]` **4.76 ms** the first frame. ⛔ A desktop that went black mid-session, on
   this road, **no longer has anyone to say so**. It is declared in the code and here, not discovered afterwards.
6. ⚠ **I was not alone on the machine** in any round (17 `remotix` and 5 `gnome-shell` of other
   benches). ⇒ ⛔ **The absolute values must be read as a ceiling.** The before/after holds because it is
   **alternating**, and the load is declared next to every round.
7. ⚠ **`banchi/08-b67-esiti.jsonl` grew longer with my reports**: it is B's bench that
   writes there by itself at every round. I did not touch the file by hand; I say it so that the owner does not
   discover it from a `git status`.

---

## What remains `[?]`

| | |
|---|---|
| ⏳⏳ **the canvas multiple of 16** | ⛔ It is a **protocol change** (`RCP.md` §4.5 declares «even» normative), so it is the user's. Until it exists, zero copy **does not hold on all canvases** — and one of the uncovered canvases is precisely B's bench's **1560** |
| ⏳ **is the retention really needed?** | `[R]` the mechanism of §8 is read in Mutter; `[M]` the injected fault **does not reproduce it** on this scene. One would need a scene that keeps the GPU busy longer than the six buffers |
| `[?]` **the 0.64 ms of `produttore`** | what remains after removing our work from the real-time thread. **That** does look like Mutter's, but it is ten times less than was believed |
| `[?]` **the child's frames stuck at 33/s** | the scene draws 61. With the segment at 6.41 ms the bottleneck is no longer our CPU: `[?]` it is Mutter's cadence, or the child's loop (`MOVIMENTO_ATTESA_S`) |
| `[?]` **other drivers and other compositors** | the 64-byte constraint is `[M]` **on iHD**. On AMD (radeonsi, `renderD129`) and on KWin/wlroots it **was not looked at**. ⚠ The guard however is on the **measured stride**, so it is not a rule on iHD: it is a rule on the stride |
| `[?]` **10 bits** | ⛔ they do not come back through this door and did not belong to this phase: Mutter delivers BGRx on the card as on memory |

---

## How to redo it

All in `/media/REMOTIX/src/`, and the server was left **running on 7775** with the healthy binary
(`remotix-scheda`, md5 `c11d200f…`) so that the coordinator can rerun.

| | |
|---|---|
| `08-f4-derivami.sh` | the ground **derived** from C's, not rewritten — my ports, user and tree |
| `08-f4-due-binari.sh` | the two binaries from the **same tree**, with the check that the md5s differ |
| `08-f4-ab.sh` | ⭐ the **alternating** before/after of the segments |
| `08-f4-elastico.sh` *(on the laptop)* | ⭐ the user's yardstick, alternating, which **drives** B's bench without touching it |
| `08-f4-misure.sh` | ⭐ the four canvases on both sides of the 64-byte threshold |
| `08-f4-colore.sh` · `08-f4-colore.py` | the colour comparison, **with the R↔B negative control** |
| `08-f4-guasto-rilascio.sh` · `08-f4-prova-guasto.sh` | ⭐ the fault injected on the release |

⚠ The copies are also in `…/scratchpad/`. ⛔ None is in `banchi/`: they are benches of this
point, and the agents' reports are not kept — if the coordinator wants them, the place is
`banchi/` with a `08-…` name.


---

## 4-F1 · ⭐⭐⭐ AGENT F1 — **the whole loop: 55.20 ms** with zero copy, paired · *22 Aug 2026, night*

> ### ⭐⭐⭐ THE NUMBER THE WHOLE PHASE WAS MISSING
>
> `[M]` **`input → vetro` = 55.20 ms** with zero copy on; the paired round without it (the road from
> memory with `sws_scale`) is removed with phase 18: zero copy shortened the loop, and the value from
> before is no longer valid.
>
> ⭐⭐ **Two rounds in a row that share EVERYTHING except the binary** — same canvas 1456×888, same
> stride 5824, same window, same scene, and `macchina carica: false` **written by the bench** in
> both (load 1.10 and 0.40 on 4 cores, a single `b30` bench). Md5s read by hand from
> `/proc/PID/exe`: `f45e9f78…` against `73ce3a1f…`.
>
> ⭐ **And it was really on**: the product declares **«strada scheda»** today and **«strada memoria»**
> yesterday, **with the identical stride** ⇒ it flips because the **binary** changes, not the canvas.
>
> | | the segment | ⭐ **today** |
> |---|---|---|
> | **E** | encoding and return | **10.27** |
> | **C** | the wait for the frame in the scene | **11.78** |
> | **D** | Mutter's frame | 16.01 |
> | | **T — the whole loop** | **55.20** |
> | | p95 · n | **122.50** · 721/727 |
>
> *(phase 18: the «yesterday» column — the road from memory with `sws_scale` — and the differences are removed; they are no longer valid.)*
>
> ### ⭐⭐⭐ And the thing nobody had foreseen: **the cure pays off where it is not its own**
>
> ⛔ **About half of the gain lies in segment C**, which is **on the server** and which zero
> copy **does not cross**. ⇒ `[?]` The cheap hypothesis is F4's disproof of §4-C: **the producer
> removed from PipeWire's real-time thread**. ⚠ **Declared, not measured**, and it is written that way.
>
> ⭐⭐ **And the account matches F4's by another road**: segment 5 drops to `[M]` **9.89 ms**, with the
> same shape F4 sees without a browser (the «before» values are removed, phase 18).
>
> ⭐ **And it is the first entirely green round** this bench has ever produced: **12 out of 12, Q5 and
> Q6 included** — the two that on 14 Aug were **both red** when the number of the time
> was delivered, and no document said so.
>
> ### ⛔ The limits, written next to the number
> - ⛔ **The 55.20 is NOT compared with the numbers of F1.3**: another canvas (where zero copy **does not even
>   switch on**) and load `[R]` instead of `[M]`;
> - ⚠ **One round per side**, and on the earlier binary the spread from round to round was **~15 ms**
>   (values removed, phase 18). ⇒ ⭐ **What holds up the attribution is not the total: it is the segments.**
>
> ### ⛔⛔ And the lesson of the evening: **four false reds, and they all accused the NORMAL state**
>
> The old boundary · the stride/road disagreement · segment 1a in Q11 · `None == None` in the comparison
> script. **Every time the bench accused the control round.**
>
> ⇒ ⭐ **A false red costs as much as a false green**: both disconnect the colour from the fact. The
> twin question of `LEZIONI.md` §1.20 is *«and when is it NORMAL for that comparison not to add up?»*.
> ⚠ And one of the four was cured **after** seeing the red: the agent **declares it**, and says
> that the physical reason was already written before and that he excluded **a single, named segment**.
>
> ⛔ **And two real defects, his own**: he **broke the bench with a cure of his** (a variable that
> shadowed a module — a whole round lost), and the pid collected from the digits of the IP address.
> ⭐ **In both cases the bench DIED or said «I could not look»** instead of
> delivering false numbers.

> ### ⭐⭐⭐ THE MISSING NUMBER: `input → vetro` = `[M]` **55.20 ms** with zero copy
>
> Paired (the value without zero copy is removed, phase 18) over two rounds in a row in the same quiet half hour that share
> **everything** except the binary: same canvas (1456×888), same stride (5824), same window, same
> scene, same user, and `macchina carica: false` **written by the bench** in both.
> ⭐ And zero copy **was really on**: the product declares «strada **scheda**» today and «strada
> **memoria**» yesterday, **with the identical stride** — the road flips because the binary changes, not the
> canvas.
>
> | | the segment | ⭐ TODAY |
> |---|---|---|
> | **E** | ⭐⭐ encoding and return | **10.27** |
> | **C** | the wait for the frame in the scene | **11.78** |
> | **D** | Mutter's frame | 16.01 |
> | | **T — the whole loop** | ⭐ **55.20** |
>
> *(phase 18: the «yesterday» column — the road from memory with `sws_scale` — and the differences are removed; they are no longer valid.)*
>
> ⭐⭐ **And the account matches F4's by another road**: segment 5 drops to `[M]` **9.89 ms**;
> he, on his segment and **without a browser**, saw the same shape (the «before» values are removed, phase 18).
>
> ⭐⭐⭐ **And it pays off even where it is not its own**: about half of the gain lies in segment
> **3**, which is **on the server** and which zero copy does not even cross. `[?]` The cheapest
> explanation is F4's disproof of §4-C: the producer removed from PipeWire's real-time thread
> (`[M]` 0.64 ms with zero copy). **Hypothesis declared, not measured.**
>
> ⭐ **And today's round is the first entirely green one this bench has ever produced**: 12
> checks out of 12, **Q5 and Q6 included**.
>
> ⚠ **The rest of the report (F1.1-F1.4) stays as written** and says two other things that must not be
> confused with this one: how the bench came to read the real road, and **how much contention
> moves a loop**. ⛔ The loop values found there (removed with phase 18: binary from
> memory with `sws_scale`) **were not the «before» of zero copy** — see the warning in F1.5.

### ⭐⭐ AND THE SECOND THING I FOUND TONIGHT — getting there by a different road than F3

> ### ⛔⛔⛔ **A's «before» is not a term of comparison**, and the reason is the load
>
> My mandate was to redo `input → vetro` on the real road and put it next to A's number.
> ⛔ **Putting them side by side cannot be done**, and not because the bench cannot get there: because A's number
> **carries contention inside it**. F3 proved it with three benches; I got there without looking for it,
> and the two roads meet on the same number.
>
> `[M]` **Segment 9 — «the wait for the frame to be usable», the 17.48 ms on which §A.2 point 2
> bases its most-cited conclusion — is worth 0.71 ms.** And it is not only me saying it:
>
> | who measures it | how much | how |
> |---|---|---|
> | the **bench** (my prologue) | **0.715** and **0.835 ms** | from the decoder callback to the resolution of `createImageBitmap` |
> | ⭐⭐ the **PRODUCT**, by itself | **0.710** and **0.830 ms** | `src/pagina.html`, `bmp_ms` — a reader written by another person, in another place, who does not know the bench exists |
> | F3, three independent benches | **0.39 – 1.18 ms** | including **on A's same 2D road** |
>
> ⇒ ⭐⭐⭐ **Discrepancy between the bench and the product: `[M]` +0.005 ms. Two rounds, the same discrepancy twice.**
>
> ⛔ **And my measurement also says WHY, without my looking for it.** Four rounds, same bench,
> same stage, same evening, same scene, same product binary: the two with **another
> agent's bench** on the laptop gave a longer loop than the two in which I was alone. *(The values, on the
> binary from memory with `sws_scale`, are removed with phase 18.)*
>
> ⇒ ⛔⛔ **What changed the loop was not the product: it was who else was running on the laptop.** ⚠ It is `[R]` and not `[M]`, because the bench **did not write** that load
> anywhere — and it is exactly the defect I then cured.
>
> ⭐ **What instead holds up whole is the BENCH**: from today it reads the road the product really uses,
> and its closing boundary **is no longer a promise** (F1.2).

### ⛔⛔ And the lesson I bring is different from F3's

F3 says: *the number was contention*. ⭐ I add the thing that made it invisible, and which belongs to the
bench, not to the machine:

> **The bench declared NINE stage entries — codec, depth, GPU, canvas, monitor, WebCodecs,
> isolation, scene, `wl_surface.enter` — and NOT ONE about the load.**

⇒ `LEZIONI.md` §2.0 already asked for it: *the stage is declared next to the number*. ⛔ But a stage
described entry by entry and a load never named make a number that **looks** completely
declared. It is `LEZIONI.md` §1.20 from the reader's side: nine printed numbers make one believe that the
tenth was looked at.

⇒ ⭐ **Cured, and it is in the bench**: `carico_della_macchina()` reads at **both ends** (the laptop, where
Chrome and the bench are; the server, where the product is), **twice** — before and after the round — and
writes cores, load, Chrome processes, Xvfb, **how many other `04-b30` benches are running and on
which ports**. If it is not idle **it says so in red**, with the measurement that justifies it alongside, and the
line ends up in `esiti.jsonl`.

⛔ **And the threshold looks at the load OF OTHERS, not mine**, because `[M]` a single round of this bench
already holds **~3.7 cores out of 4 and ~29 Chrome processes**: a threshold on absolute load would be red
always, and a flag that is always red nobody looks at any more. ⇒ What is not mine is accused: a
second bench, a second Xvfb, or a number of Chrome that a single bench cannot explain — threshold
**40**, and ⚠ `[M]` when A was measuring there were **56**, with **5 Xvfb**.

---

## F1.0 ⭐ The bench recertified itself, and the certification has grown

`[M]` `--certifica` ⇒ **PASSED, 57 checks out of 57, 18 injected faults accused out of 18**
(A had 53 and 16). The checks and the two new faults all belong to **Q11**, the
boundary check.

⭐ And before that, a test the bench had never had: **the prologue tested without a
browser**. The prologue is a string that lives inside Chrome and cannot be exercised piece by piece; I
extracted it and ran it in `node` against a fake browser that imitates the real page —
asynchronous `createImageBitmap`, `ImageBitmapRenderingContext`, `VideoDecoder`, a canvas:
`[M]` **16 checks out of 16** (`f1-prova-prologo.js`). ⛔ And the fourth block demands that **the 2D
road has not broken**: 5 frames, 2 `drawImage` each, `t_dip == t_dip_vecchio`.

---

## F1.1 ⭐⭐ HOW THE BENCH READS THE REAL ROAD

⛔ The defect of §A.4 point 1 was **twofold**, and the two halves are cured together or not at all:

| | the defect | the cure, and where it is |
|---|---|---|
| **1** | the prologue reads the pixels from the **2D store**, which on `bitmaprenderer` **does not exist** ⇒ `[M]` 0 marks read out of 304 | ⭐ **they are read from the GLASS**. The `bitmaprenderer` context has no `getImageData` — it gives no access to the pixels — ⛔ **but the canvas does**: a `<canvas>` is a valid source for `drawImage` whatever context paints it. ⇒ The bench copies **only the mark region** (480×240) onto a 2D service canvas and reads it back from there (prologue §6, `leggi_marca_vetro`) |
| **2** | ⛔⛔ `createImageBitmap` is **asynchronous**: the product's callback **returns before** anything has been painted ⇒ the «awkward» boundary had become **more convenient than the convenient one**, and nobody had decided it | ⭐ the sample **is no longer closed in the decoder callback**: it is opened there and closed in **`transferFromImageBitmap`**, that is when the screen changes |

⭐ **It works, and the denominator says so**: `[M]` **555 probes closed out of 555** at the first round on the
real road (A had closed **0 out of 304**), **1424 marks read out of 1424 looked at** (Q3), and Q4(a)
`[M]` **251 frames looked at where the echo mark is not there → 0 false positives**: reading from the
glass **discriminates**, it does not always say yes.

### ⭐ The three details that make the difference between a cure and an approximation

1. ⛔ **`createImageBitmap` is wrapped WITHOUT chaining.** The bench registers its own handler on the
   promise and returns **the original one**, not `p.then(...)`: chaining it would slip a bench
   microtask between the resolution and the product's handler — that is **the bench would delay
   what it measures**.
2. ⛔ **The image is tied to the frame by the ANNOUNCED `pts`**, not by the order of resolution:
   the order is a substitute quantity (`LEZIONI.md` §1.13), and `createImageBitmap` does not promise to
   resolve in order — it is the reason why the product itself counts the `tardive`.
3. ⛔ **The pixels are read AFTER the transfer**, not from the `ImageBitmap` before: reading before
   would mean reading something that is not yet on the screen — and delaying it into the bargain.

### ⭐ And the road is not declared: it is DEDUCED

Every sample carries a `strada` field, filled by what **happened**. `coda_url` is
the intention, `strade` is the fact — and now **both are in the line deposited** in
`04-b30-esiti.jsonl` (it was minor defect no. 5 of §A.4: `[M]` all 11 lines deposited before
today, including A's five, have `coda_url: null`).

⛔ **And the first draft of that field had a defect that I found and cured**: I marked «2d» every
frame on which I had not seen a call to `createImageBitmap`. `[M]` In one round
**235 out of 2022** came out — with the 2D road never used. ⇒ They were frames the product **decoded and
never painted** (discarded because late). ⚠ **They dirty no number** — I verified it: zero
`drawImage`, zero cells, and **none of them closed a probe** — ⛔ but calling them «2d» was
mistaking *«it did not happen»* for *«the other thing happened»*, the same shape as «not arrived» ≠
«not looked at». ⇒ Now the state is **a third one and is called `non dipinto`**, and counted for what it is
it says something about the product: `[M]` **part of the decoded frames did not reach the glass**
in that round (the share, on the binary from memory, is removed with phase 18).

---

## F1.2 ⭐⭐⭐ THE POSITIVE CONTROL — and it corrected ME

⛔ **A readapted bench that gives a plausible number is not a bench that works.** The bench injects
`--ritardo-vetro N`: N ms **inside the page**, between «the frame is ready» and «the frame is at the
glass». If the boundary closed before the drawing, that delay would be **invisible**.

### ⛔⛔ The first draft of the control was WRONG, and it was the measurement that rejected it

I had written the requirement like this: *«the OLD boundary — the return of the callback — must NOT rise»*.
⛔ **It is false, and the real world rejected it at the first round**: `[M]` with 8 ms injected the old
boundary rose by **6.82 ms** and the total by **14.81** instead of by 8.

`[R]` **And the reason is physical, it is not a defect of the yardstick**: the delay is injected **by occupying the
page's thread** — which is what a costly drawing does — and that time also delays the delivery
of the **input events**, which are on the same thread. ⇒ The whole pipeline shifts, and on a
single median that shift is **indistinguishable** from the injected delay.

⇒ ⭐⭐ **The right quantity is PAIRED**: the distance between the true boundary and the wrong one taken
**on the same probe, on the same frame**. The pipeline shift hits both ends
identically and **cancels out**; only the injected delay remains.

### ⭐⭐⭐ And the number, repeated THREE times in three different rounds

| round | distance at delay 0 | with the delay of **8.000** | **rise** | ⛔ **the MINIMUM** | probes |
|---|---|---|---|---|---|
| `08f1-fase-del-quadro` | 0.085 ms | 8.090 | **+8.005** | **8.045** | 476 |
| `08f1-strada-vera-3` | 0.080 | 8.095 | **+8.015** | **8.045** | 470 |
| `08f1-strada-vera-4` | 0.100 | 8.095 | **+7.995** | **8.040** | 833 |

⇒ ⭐⭐⭐ **Maximum deviation from the injected delay: 0.015 ms.** And the **minimum** of the distribution is
above 8.04 in all three: over **1 779 probes out of 1 779** there is **not a single one** that does not see the
delay. ⛔ A bench that closed at the return of the callback would give **0.09 in every row**, and its
median would rise all the same: that is why the paired row is the proof and the median is not.

⭐ And the other two requirements hold by themselves: `[M]` the rise lies **in segment 10 (+7.995 / +8.005 /
+8.015 out of 8.0) and in no other segment** (`e_anche_altrove: []`), and the total rises **by at least N**.

### ⛔⛔ AND THE THING THAT MUST BE SAID AGAINST MYSELF: the catastrophe A feared **was not there**

`[M]` On the real road the two boundaries are **0.08 – 0.10 ms** apart. `createImageBitmap` resolves in
`[M]` **0.71 ms** and `transferFromImageBitmap` costs `[M]` **0.06**. ⇒ The old bench, if it had
been able to read the pixels, would have delivered a number **shorter by a tenth of a millisecond**, not
by twenty.

⇒ ⭐ **The second half of the defect of §A.4 was true as a MECHANISM and small as a QUANTITY**, and the
two things are said together: the mechanism is proven (the 8 ms injected lie entirely inside
that gap, and the wrong boundary loses 8 out of 8); the quantity on *this* stage is 0.09 ms.
⛔ It is not a reason to leave the boundary where it was — it is the reason why **one measures instead of
estimating**. And neither number could be deduced beforehand.

### ⭐⭐ THE CROSS-CHECK — and it carries a warning for everyone

The product measures by itself the same two quantities as segments 9 and 10 (`bmp_ms`, `vetro_ms`). The bench
now brings them out next to its own:

| | the PRODUCT | the BENCH | |
|---|---|---|---|
| **segment 9** (`createImageBitmap`) | **0.710** · **0.830** ms | **0.715** · **0.835** | ⭐⭐ discrepancy **+0.005** two times out of two |
| segment 10 (`transferFromImageBitmap`) | 8.04 · 9.86 ms | 0.05 · 0.065 | ⛔ **it is NOT a disagreement** |

⛔⛔ **And segment 10 is the most important involuntary discovery I leave behind.** The product's `vetro_ms`
times `this.bm.transferFromImageBitmap(bmp)` — but **the bench wraps precisely that method**, and
inside the wrapper it reads the pixels. ⇒ The product's stopwatch **contains the bench**.

⇒ ⛔⛔ **As long as this bench is attached, the `vetro` field of `pagina.html`'s diagnostic block
is not the product: it is the product plus the bench.** Whoever read it in another report would write
`[M]` 8-10 ms for a transfer that costs 0.06. ⭐ The bench now declares it instead of
judging it, and the difference (**7.99** and **9.80**) is a **third opinion on the cost of the bench**, taken
from the product and set beside Q9 (**7.61** and **8.79**).

---

## F1.3 ⭐⭐ THE NUMBER OF THE REAL ROAD, AND THE SIX SEGMENTS SIDE BY SIDE WITH A'S

⛔⛔ **It is read with the warning at the top, not after**: A's column **is not a reliable
«before»** (F3, and my four rounds). The two columns stand side by side because the mandate asks for it
and because the **profile** — where the time is — is what the one curing needs; ⛔ **the differences are not
attributed to the product.**

| | the segment | A · 2D (5 rounds) | ⭐ F1 · `bitmaprenderer` (4 rounds) | Δ |
|---|---|---|---|---|
| **A** | **the page** — `event.timeStamp` → the bytes leave | 7.65 ms | **5.14 ms** | −2.51 |
| **B** | **the outward leg** — bytes out → the scene receives the input | 7.25 ms | **8.58 ms** | +1.33 |
| **D** | **Mutter's frame** | 16.36 ms | **16.40 ms** | **+0.04** |
| **F** | ⛔ **the client** — `decode()` → drawing finished | **18.83 ms** | ⭐ **2.43 ms** | ⛔ **−16.40** |

*(Phase 18: removed rows **C** (the wait for the frame in the scene, which zero copy later showed
to depend on our work in the PipeWire thread), **E** (encoding and return), the sum and the total
**T**: on this canvas the product went from memory with `sws_scale`, and those values are no longer valid.)*

| segment | A · 2D [min–max] | ⭐ F1 · `bitmaprenderer` [min–max] |
|---|---|---|
| 1a event → the product sees it | 7.53 [7.04 – 15.04] | **4.95** [4.83 – 6.33] |
| 1b the product sees it → the bytes leave | 0.12 | **0.19** |
| 2 bytes out → the scene receives | 7.25 [6.84 – 7.93] | **8.58** [8.16 – 8.90] |
| 4 the scene draws → capture | 16.36 [16.23 – 16.39] | **16.40** [16.37 – 16.45] |
| 6 first byte → last byte | 0.24 | **0.34** |
| 7 stream complete → `decode()` | 0.10 | **0.15** |
| 8 `decode()` → decoder callback | 1.09 | **1.53** |
| 9 ⛔ callback → **the frame is ready** | **17.48** [14.90 – 18.72] | ⭐ **0.71** [0.69 – 0.83] |
| 10 ready → **the drawing is finished** | 0.10 | **0.06** |

*(Phase 18: segments 3 and 5 removed, for the same reason.)*

### ⛔ The four things this table says

1. ⛔⛔ **Segment 9 is not a target: `[M]` it is worth 0.71 ms**, and the conclusion of §A.2 point 2 —
   *«the 1st `drawImage` costs 17.48 ms and the 2nd 0.10: 163 times»* — **must be withdrawn**. ⇒ **Whoever was about to
   cure segment F was about to cure a segment that weighs `[M]` 2.43 ms**, a small part of the loop.
   ⭐ §A.5 feared it in its own words: *«if the number changes, he must know it before curing it»*.
2. ⭐ **Segment D did not move by four hundredths** (16.36 → 16.40), with the tightest spread
   of all [16.37 – 16.45]. ⇒ A segment that stays identical when everything else changes is
   the proof that the breakdown really separates different things — **and it remains the wall**: an exact
   compositor frame.
3. ⛔ **The other differences are NOT attributed**: they lie inside the spread that A himself
   had measured and inside the one that contention produces on my own rounds. `[?]`
4. ⭐ **The denominator is better than his**: `[M]` 463-829 probes closed per round against 224-417, and
   closure is 99-100 % in all four.

### ⛔ The number, and it must be read with the load next to it

*The loop of the real road had been delivered with the machine idle, separated from the rounds with another
agent's bench on top, and it exceeded the 50 ms and the 40 of `SPECIFICHE.md` §3.2; the measurements, taken on the binary
from memory with `sws_scale`, are no longer valid after phase 18.*

### ⚠ And the stage, next to the number

`[M]` codec **HEVC** `hev1.1.6.L120.B0`, **8 bit**, promotion 8→10 no · encoding **IN HARDWARE**
(`hevc_vaapi`, `/dev/dri/renderD128`, ⚠ **EncSliceLP**, confirmed today) · canvas **1460 × 888** ·
page GPU `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` · WebCodecs yes · page isolated yes ·
scene on **Meta-0**, confirmed by `wl_surface.enter`.
⇒ **It is the stage of §A.1 entry by entry**, and it is deliberate: same product tree
(`/media/REMOTIX/src/08-a-src`, `md5sum` of `pagina.html` verified), **same scene binary**
(identical `md5sum`), same user. ⛔ I rebuilt nothing: rebuilding would have changed one
end of the comparison without saying so.
⚠ ⭐ **And so my tree does NOT have F3's `REMOTIX.tratti()`**, which arrived later (`md5sum` of
`src/pagina.html` at HEAD: `d387c166…`, mine: `2fdf13a9…`). ⇒ Whoever redoes these rounds with today's
product has a better tool than my prologue, and must know it.

### ⛔ The two blind pieces

`[?]` **4-12 ms** on input (hand → `event.timeStamp`) · `[?]` **16-40 ms** on output (drawing
finished → pixel lit). ⛔ **And the output ones are there**: `clienti_sull_xvfb: 0` ⇒ the browser is on
the laptop's real desktop, where there is a compositor. ⇒ On a user's screen they must be added
to the loop (`[?]` 20-52 ms), **plus the network**.

### ⭐⭐ And the rubber-band calculation of §1.2 must be redone

The box of §4-A multiplied `anello × 3 400 px/s` against the gap the user sees, «within
7 %». ⛔ With the number of the real road that product was **far** from what the user saw.
⇒ ⭐ **It is not a defect: it is information.** Either the gap the user sees contains the blind pieces
and the network — and then the account adds up — or he was looking faster than his median. *(The values, on the
binary from memory with `sws_scale`, are removed with phase 18.)*
⛔⛔ **And the «within 7 %» agreement of §4-A was an agreement with a number inflated by contention: it must be
removed from the box**, or it stays there certifying the model with the wrong measurement.

---

## F1.4 ⭐⭐ THE TWO DEFECTS A LEFT WRITTEN DOWN

### 1. ⭐⭐ Q5 and Q6: **it is curable, and the cure is in the CHOICE OF THE DELAY** — not in the yardstick

§A.4 point 2 gave the hypothesis `[?]`: *«delaying the input changes its PHASE relative to the compositor's
frame»*, and closed: *«whoever wants it `[M]` tests it by injecting delays that are not multiples of 16.7»*.

⭐ I tested it **the other way round**, which is stronger: delays that are **exact multiples** of the frame. If
the hypothesis is right the phase does not change, and segment 3 **must not move**.

`[M]` **Same bench, same stage, same evening:**

| injected delay | Q5 | Q6 | ⭐ where the surplus goes | ⛔ and **segment 3**? |
|---|---|---|---|---|
| **25 / 30 ms** (not multiples of the frame) | **red** | **red** | segment 5: **+23.12** out of 25 · segment 2: **+29.62** out of 30 | ⛔ **−6.18** and **−5.66 ms** |
| ⭐ **33.4 / 33.4** (= **two exact frames**) | red by **0.22** | ⭐ **GREEN** | segment 5: **+32.94** out of 33.4 · segment 2: **+33.34** out of 33.4 | ⭐ **does not move**: `e_anche_altrove: []` |

⇒ ⭐⭐⭐ **A's hypothesis is confirmed and becomes `[M]`.** Segment 3 **compensates** when the
delay shifts the phase of the input relative to the frame: it is not contamination of the yardstick, it is the pipeline
that really behaves differently. And the surplus **lies in the right segment in all four cases,
within 0.46 ms**.

⇒ ⭐ **The cure**: the delays to inject must be set to **multiples of the frame** (16.7 ms).
⛔ **I did not change the bench's starting values**, and the reason is that **another agent had a
round in flight on this same file**: changing a calibration under him mid-experiment would have
changed his verdict without his knowing. ⇒ **It is a single line, and I pass it to the director.**

### 2. ⛔⛔ The fact about the number of 14 Aug — reread from the SOURCE, and more comes out

§A.4 point 2 declared it. I reread it from `04-b30-esiti.jsonl` (field `controlli`) and out comes
**the MANNER of the red**, which changes the reading:

| round | Q5 | Q6 | ⛔ **how** it failed |
|---|---|---|---|
| 14 Aug `b30-o2-finale` — ⛔ **the number delivered** | **red** | **red** | Q5: rise **15.79 out of 25** (−9.21) and **segment 2 goes −14.19**; Q6: right segment, total +6.29 |
| 14 Aug `b30-o2-finale2` | **red** | green | rise 20.78 out of 25, segment 2 **−7.17** |
| 22 Aug `08a-tela2d-adattano-1` | green | green | ⭐ the only one with both green |
| 22 Aug `08a-tela2d-5` — **A's number** | **red** | green | right segment, rise 30.59 out of 25 |

*(The loop totals of those rounds are removed with phase 18: they belonged to the binary from before zero
copy.)*

⇒ ⛔⛔ **The number of 14 Aug is not only «delivered with two red calibrations»: it was delivered by a round
in which segment 2 moved by −14.19 ms under a delay injected elsewhere.**
⚠ The total remains what it is — measured at both ends with the same clock — ⛔ but **its
breakdown of 14 Aug must be read with this next to it**, and no document said so.

### 3. ⚠ The three minor defects of §A.4 point 5 — **cured, all three**

| | |
|---|---|
| ⭐ **`coda_url` did not reach `esiti.jsonl`** | cured, and with **two** fields: `coda_url` (the intention) and `strade` (the **fact**). ⛔ Verified that the defect was there: `[M]` all 11 lines deposited before today have `coda_url: null` |
| ⭐ **`scena-costruisci` of `04-b30-lancia.sh` broken** | cured: the build is in a **file** (`banchi/04-b30-scena-costruisci.sh`), not in a line that goes through `ssh → enter.sh → bash -c`. ⭐ The rule was **already written** in the header of the same file — *«a file has no levels of quoting»* — only the code did not follow it. The new file also verifies that the binary is not empty before renaming it |
| ⭐ **the old scene does not let go of the focus** | cured **inside the bench**: `giro_vero()` calls `scena-ferma` **before** `scena-avvia`. ⚠ Before, the remedy was «in the head of whoever launches it», and that is how A lost his first round |

### 4. ⭐ And a contribution to `LEZIONI.md` §1.24, which F3 paid for today

I verified my resources on **every** axis, not only the port:

| | mine | others', counted |
|---|---|---|
| ports | **7760 · 7761 · 7762** | 7730/7731 (the user) · 7746 · 7752 · 7765-67 |
| user / uid | **provaa8 / 1041** | provaf8/1044 · provaf48/1046 · provaf3/1047 · provac8 · provab8 |
| shm | **remotix-08-f1** | remotix-08-f · -08-f3 · -08-f4 · -08-a/b/c |
| work dir | **/media/REMOTIX/tmp/08-f1** | 08-f · 08-f4 · 08-a/b/c |
| Xvfb / CDP | **:96 / 9660** | the only live Xvfb was mine |

⛔ **And a shape came out of it that the lesson does not yet cover**: `08-f1` and `08-f` are different names,
⛔ **but one is a PREFIX of the other**. An `rm -rf /media/REMOTIX/src/08-f*` by whoever owns `08-f`
would take mine away too, and neither of the two would have done anything wrong.
⇒ ⭐ **It is not enough for the names to be different: they must not be prefixes of each other.** It is one line
for §1.24.
⚠ **And I declare a real overlap**: I use `provaa8`, **A's** user, on purpose — it is the only
way to have his very stage. A has come back in, so nobody contends for it; ⛔ but if someone
restarted its session while I measure, my scene would die. ⭐ The bench would say so («la scena non
prende il fuoco») instead of producing a false number — I verified it by reading that branch.

---

## F1.5 ⭐⭐⭐ L'ANELLO INTERO CON LA COPIA ZERO — il prima/dopo **appaiato**

> ### ⭐⭐⭐ `input → vetro` con la copia zero: `[M]` **55,20 ms**
>
> *(Il valore di ieri, senza la copia zero — la strada dalla memoria con `sws_scale` — è tolto con la
> fase 18: la copia zero ha accorciato l'anello, e il valore di prima non vale più.)* Due giri di seguito, nella stessa mezz'ora tranquilla, che condividono **tutto** tranne il binario.

### ⛔ Prima del numero: era la copia zero, ed era accesa?

⛔⛔ La trappola peggiore sarebbe misurare il codice nuovo mentre percorre la strada vecchia, e non è
teorica: `[M]` (F4) il driver iHD **non onora un passo che non sia multiplo di 64 byte**. Il passo è
`larghezza × 4`, quindi la condizione è **larghezza multipla di 16 px**:

| tela | passo | resto su 64 | |
|---|---|---|---|
| **1460×888** — ⛔ il palco di **tutti** i giri precedenti | 5840 | **16** | ⛔ copia zero **spenta** |
| 1544×888 · 1560×888 (le tele storte di F4) | 6176 · 6240 | 32 · 32 | ⛔ spenta |
| ⭐ **1456×888** — il palco di stasera | **5824** | **0** | ⭐ **accesa** |
| 1920×1080 | 7680 | 0 | ⭐ accesa |

⇒ ⭐⭐ **1456 e non 1920, e la ragione è il confronto**: è il multiplo di 16 più vicino a 1460, cioè
**quattro pixel** dal palco di sempre invece dei **+63 % di pixel** che 1920×1080 avrebbe portato
dentro. ⭐ E il conto riproduce i casi che F4 ha misurato: 1544 e 1560 → resto 32 (storte), 1920 → 0
(buona). Due strade, stesso risultato.
⭐ La leva è **la finestra del browser** (`--finestra 1496x1000`, argomento nuovo): la pagina chiede
al server una tela grande quanto la sua vista.

### ⭐ E che i due giri siano confrontabili non si spera: **il banco lo verifica**

| | **IERI** (senza) | ⭐ **OGGI** (copia zero) |
|---|---|---|
| albero | `/media/REMOTIX/src/08-a-src/src/remotix` | `/media/REMOTIX/src/08-f1-src/src/remotix` |
| **md5 del binario CHE GIRA** (da `/proc/PID/exe`) | **`73ce3a1f19028c8e7436db9d2125ded2`** | **`f45e9f789782e316da6efc7e409e4625`** |
| sorgenti | il tronco del 22 agosto mattina | HEAD `6f5f418`, `cattura.c` `c17a7838…` verificato |
| **copia zero**, letta dal registro del PRODOTTO | ⛔ **SPENTA** — «strada **memoria**» | ⭐ **ACCESA** — «strada **scheda**» |
| tela · passo · resto su 64 | 1456×888 · 5824 · **0** | **identici** |
| finestra | 1496×1000 | **identica** |
| carico del portatile, `[M]` **nel verbale** | carico **0,40** · Chrome 13 · Xvfb 1 · **un solo banco** | carico **1,10** · Chrome 13 · Xvfb 1 · **un solo banco** |
| `macchina carica` | **false** | **false** |

⇒ ⭐⭐ **Il passo è identico e buono in tutt'e due**: la strada si ribalta da `memoria` a `scheda`
**perché cambia il binario**, non perché cambi la tela. È il controllo più pulito che potessi
costruire.
⚠ **L'impronta l'ho letta a mano** (`sudo md5sum /proc/PID/exe`): nel verbale non c'è, perché la
lettura automatica si è rotta due volte stasera (F1.6). ⇒ `[M]` ma per mano mia, non per mano del
banco — e la distinzione la scrivo invece di nasconderla.

### ⭐⭐ I SEI TRATTI AFFIANCATI — è la sola cosa che dice **quale pezzo ha reso**

| | il tratto | ⭐ OGGI (copia zero) |
|---|---|---|
| **A** | la pagina — `event.timeStamp` → i byte escono | 5,68 ms |
| **B** | l'andata — byte usciti → la scena riceve | 6,68 ms |
| **C** | l'attesa del quadro nella scena | **11,78 ms** |
| **D** | il quadro di Mutter | 16,01 ms |
| **E** | ⭐⭐ **codifica e ritorno** | **10,27 ms** |
| **F** | il cliente | 2,48 ms |
| | **T — L'ANELLO INTERO** | ⭐ **55,20 ms** |
| | **p95** | **122,50** |
| | n (sonde chiuse / tentate) | **721 / 727** |

| tratto | OGGI |
|---|---|
| 1a evento → il prodotto lo vede | 5,53 |
| 1b · 6 · 7 · 8 · 9 · 10 | 0,15 · 0,38 · 0,16 · 1,55 · 0,72 · 0,06 |
| 2 byte usciti → la scena riceve | 6,68 |
| 3 la scena riceve → la scena disegna | **11,78** |
| 4 la scena disegna → cattura | 16,01 |
| **5 cattura → PRIMO byte in pagina** | ⭐⭐ **9,89** |

*(Fase 18: le colonne «IERI», sulla strada dalla memoria con `sws_scale`, e le differenze sono tolte —
non valgono più. Le quattro conclusioni sotto restano come fatti qualitativi dell'appaiamento.)*

### ⭐⭐⭐ Le quattro cose che questa tabella dice

1. ⭐⭐ **Il tratto 5 è la firma della copia zero, e il conto torna con quello di F4.**
   `[M]` Scende a **9,89 ms** (il «prima» è tolto, fase 18). F4, sul suo tratto `cattura → byte fuori` e senza browser,
   aveva visto la stessa discesa *(il suo «prima», su `sws_scale`, è tolto: fase 18)*. ⇒ **Due banchi diversi, due palchi diversi, la stessa cura,
   la stessa forma.** È la conferma incrociata che al numero di F4 mancava.
2. ⭐⭐⭐ **E rende ANCHE nel tratto 3, che non è suo** — `[M]` scende a **11,78 ms**. Il
   tratto 3 è *«la scena riceve l'input → la scena disegna»*, cioè **l'attesa del quadro sul
   server**: la copia zero non ci passa nemmeno. ⇒ `[?]` **La spiegazione più economica è la
   smentita di F4 a §4-C**: togliendo il nostro lavoro dal thread di **tempo reale di PipeWire** il
   produttore cala a `[M]` 0,64 ms, e il compositore torna a servire la scena in tempo. ⛔ È
   un'**ipotesi**, non una misura: la prova sarebbe rifarlo con la copia zero accesa e il produttore
   riportato a mano sul thread di tempo reale. **Non l'ho fatto.**
   ⚠ E circa metà del guadagno dell'anello sta lì.
3. ⭐ **Il tratto D non si muove** (16,01 ms oggi): il quadro del compositore resta il muro, e
   un tratto che non cambia quando tutto il resto cambia è la prova che la scomposizione separa cose
   diverse davvero.
4. ⚠ **Il tratto 1a peggiora**, ed è l'unico. `[?]` Il giro di oggi aveva il carico a
   **1,10** contro **0,40** di ieri — il tratto 1a è la consegna degli eventi sul filo della pagina,
   ed è il primo a soffrire il carico. ⛔ Non lo attribuisco alla copia zero e non lo nascondo.

### ⛔⛔ COME SI LEGGE QUESTO CONFRONTO, E COME NON SI LEGGE

⚠ **Il confronto buono è questo, e solo questo.** ⛔ **NON si sottrae il 55,20 dai valori** dei miei
giri precedenti (tolti con la fase 18), e la tentazione è forte perché i numeri stanno nello stesso documento. Quei giri
erano su un'**altra tela** (1460×888, dove la copia zero **non si accende nemmeno**), col carico
`[R]` invece che `[M]`, e due dei quattro sotto la contesa di un altro banco.
⇒ ⭐ **Il «prima» buono era `08f1-copiazero-IERI-2`, non quei giri** (il suo valore è tolto, fase 18). Quelli restano scritti perché
dicono un'altra cosa — quanto la contesa sposta un anello — e quella la dicono bene.

⛔⛔ **E c'è un limite del mio stesso confronto che va detto**: `[M]` sullo **stesso** binario di ieri
la dispersione da giro a giro era di **~15 ms** (i valori sono tolti, fase 18). ⇒ Con
**un solo giro per parte**, il guadagno era più grande della dispersione ma **non di un fattore
comodo**. ⭐ **A rendere credibile l'attribuzione non è il totale: sono i tratti.** Il tratto 5 cala
e concorda con F4 misurato per un'altra strada; gli altri nove non si muovono. ⛔ Chi vuole
il totale `[M]` con la dispersione dentro deve fare **tre giri per parte, alternati**, ed è mezz'ora.

⚠ E oltre a questo: `[?]` non ho fatto una prova che la copia zero **spenta sulla stessa tela storta**
desse il numero di ieri — cioè la controprova del meccanismo dal lato del driver.

---

## F1.6 ⛔⛔⭐ QUATTRO FALSI ROSSI IN UNA SERA — e **un falso rosso costa quanto un falso verde**

⭐ Il pezzo di questa serata che vale più del numero, e non è un aneddoto: **quattro volte** ho
scritto un controllo che accusava uno **stato normale**, e ogni volta la cura è stata la stessa —
distinguere *«non è successo»* da *«è successo il contrario»*, e *«non ho guardato»* da *«ho
guardato e va male»*.

| | il controllo | perché accusava lo stato NORMALE | la cura |
|---|---|---|---|
| **1** | Q11: *«il confine vecchio non deve salire»* | il ritardo si innesta **occupando il filo della pagina**, quindi sposta **tutto** il condotto: `[M]` +6,82 ms sul confine vecchio | la grandezza giusta è **appaiata** (distanza fra i due confini sulla **stessa sonda**): lo spostamento comune si elide |
| **2** | passo/strada: *«copia zero spenta con passo buono = disaccordo»* | il passo multiplo di 64 è **necessario e non sufficiente** — serve anche il codice. ⇒ «passo buono + strada memoria» è lo stato **corretto** del binario di prima della cura, cioè **del giro di controllo** | si accusa **un verso solo**, quello impossibile (strada «scheda» con passo storto); l'altro si **dichiara** con una nota |
| **3** | Q11: *«la salita sta nel tratto 10 e in nessun altro»* | `[M]` il tratto **1a** sale di **5,60 ms**, perché 1a è la consegna degli eventi **sullo stesso filo** in cui innesto il ritardo | si esclude **un tratto solo, nominato, per la ragione detta** — e la ricaduta si **conta e si consegna**, non sparisce |
| **4** | il mio script di confronto: *«stesso md5 ⇒ nessun prima/dopo»* | `None == None` è vero: con l'impronta non letta diceva **«stesso binario»** invece di **«non ho potuto guardare»** | «non l'ho letta» diventa un `⚠` distinto dal rosso |

⇒ ⭐⭐ **Il danno non è che sbagliano: è che accusano il caso che deve andare bene.** Il giro di
controllo — quello che *deve* uscire senza copia zero, perché è il termine di paragone — sarebbe
uscito rosso ogni volta. ⛔ **E un rosso che compare quando tutto va come deve è il modo più rapido
di insegnare a chi legge che i rossi di questo banco si ignorano.**

⇒ ⛔⛔ **Un falso rosso costa esattamente quanto un falso verde, e per la stessa via**: tutt'e due
scollegano il colore dal fatto. `LEZIONI.md` §1.20 chiede *«per ogni numero che il banco stampa:
quale riga lo confronta?»* — ⭐ **e la domanda gemella, che stasera mi è costata quattro volte, è
«e quando è NORMALE che quel confronto non torni?»**.

⚠ **E il numero 3 l'ho curato DOPO aver visto il rosso**, che è il momento più pericoloso per
toccare un criterio. ⇒ Lo dichiaro: la ragione fisica era scritta in questo stesso file **prima**
che il rosso comparisse (F1.2, sul totale), e ho escluso **un tratto solo e nominato**, non «i
tratti che davano fastidio». Tutti gli altri restano accusabili: se il surplus finisse nel 2, nel 3
o nel 5, Q11 diventa rosso.

### ⛔ E due difetti veri del banco, trovati mentre lo curavo

1. ⛔⛔ **Ho rotto il banco con una mia stessa cura, e mi è costato un giro intero.** Curando la
   lettura dell'`md5` ho scritto `p = x.split()` — e in quella funzione **`p` è già il modulo del
   ponte**. Sette passi più giù `p.orologio_chiedi(...)` trovava una lista, e il giro moriva **ad
   ancora chiusa, dopo aver misurato tutto**.
   ⭐ E il difetto era **invisibile** nel giro precedente, perché lì la lettura dell'`md5` falliva e
   il ciclo non girava mai: **una riga curata ne ha rotta un'altra a distanza**.
   ⚠ L'unica cosa che ha funzionato come doveva: il banco è **morto** invece di consegnare un numero.
2. ⛔ **`"".join(c for c in stdout if c.isdigit())`** per prendere il `pid`: nello `stdout` di `sshpw`
   c'è anche *«nicfio@**192.168.0.2**'s password:»*, e il pid usciva `1921680`+quello vero.
   ⭐ Anche qui il banco ha detto **«NON HO POTUTO GUARDARE: "non lo so" non è "è quello giusto"»**
   invece di inventare un'impronta — ed è l'unica ragione per cui il difetto è costato una riga e non
   un numero falso in un documento.
   ⚠ ⛔ **È la terza volta in una sera** che un comando muore attraversando `ssh → sudo → pipe`: la
   regola di casa *«un file non ha livelli di virgolette»* vale anche per le righe brevi.

---

## F1.7 ⛔⛔ CHE COSA NON HA FUNZIONATO (il resto)

### 1. ⛔⛔ La prima stesura di Q11 era SBAGLIATA, e a bocciarla è stata la misura
⚠ **E il finto non l'avrebbe mai bocciata**: nel finto il ritardo al vetro non occupa nessun filo,
quindi il condotto non si sposta. ⇒ Un banco consegnato dopo la sola certificazione sarebbe uscito
**verde sul finto e falso sul mondo**. È la ragione per cui la certificazione non basta.

### 2. ⛔ Il banco costa **5,5 volte più di prima**
`[M]` la lettura dei pixel: **1,59 ms** dal deposito 2D (giro di A) contro **7,61 – 8,79 ms** dal
vetro. ⇒ Leggere dal vetro è una **lettura dalla GPU**, e si paga.
⭐ Q9 resta verde e non è una concessione: `[M]` il ritmo **non cala** con la lettura (i valori, sul
binario dalla memoria, sono tolti con la fase 18) ⇒ il filo non è saturo. ⛔ Ma «non satura» non è «gratis»: resta in
F1.8.
⭐ **E la cura per chi viene dopo è trovata e non applicata, apposta**: le due marche stanno **una
sopra l'altra**, quindi si leggerebbero con **una sola** `drawImage` sul riquadro che le contiene
tutt'e due. ⛔ Non l'ho fatto perché i giri erano cominciati: **cambiare il metro a metà della
misura** è il difetto che questa fase sta curando.

### 3. ⛔ La TASTIERA non chiude **niente**
`[M]` **276 messaggi sul filo, 276 sonde, 0 CHIUSE.** §A.4 punto 3 dava 0/208 · 0/212 · 8/196 ·
5/202 · 16/198. ⇒ Sulla strada vera è **0 su 276**. ⛔ **Nessun documento deve citare un ritardo di
tastiera preso da questo banco.** `[?]` Se sia la scena, l'eco o la finestra di 500 ms **non l'ho
aperto**.

### 4. ⛔ Q5 resta rosso anche coi ritardi a quadro intero, di **0,22 ms**
La diagnosi è giusta (il surplus è nel tratto 5, +32,94 su 33,4, e in nessun altro); è la mediana del
**totale** a salire di 37,62. `[?]` Non ho separato rumore e contesa.

### 5. ⛔ Il palco NON era isolato, e va detto perché è il cuore di tutto
⚠ **E c'è una conseguenza che non è solo rumore**: le mie modifiche a `04-b30-anello-input.py` sono
entrate in vigore **mentre un giro di un altro agente era in volo** — in particolare
`--ritardo-vetro`, che aggiunge una **quarta condizione** a ogni giro. ⇒ Il suo giro è durato un
quarto in più di quel che si aspettava, e il suo Q11 può comparire in un verbale che non lo
prevedeva. **La colpa è mia e la dichiaro**; il file del banco è di tutti e non c'era modo di curarlo
senza toccarlo.

### 6. ⛔ Un solo valore di ritardo al vetro, non due
Ho provato **8 ms**, tre volte in tre giri (scarto 0,005 · 0,015 · 0,005). ⛔ **Non ho fatto la
linearità** con un secondo valore. ⚠ Sopra ~16 ms il filo si satura e i fotogrammi si **buttano**
invece di ritardare — cioè si misurerebbe un'altra cosa. `[?]` Fra 4 e 12 ms lo spazio c'era.

### 7. ⛔ Il quinto giro **l'ho ammazzato io, a metà**
Su richiesta del direttore, per liberare il portatile a F4. ⇒ Ho quattro giri e non cinque, e i due a
macchina scarica sono **due**. ⭐ È la scelta giusta — un giro in più preso sotto contesa avrebbe
peggiorato la mediana invece di migliorarla — ⛔ ma il denominatore è quello che è.

---

## F1.8 ⛔ Che cosa resta `[?]` dopo di me

| | |
|---|---|
| ✅ ~~**il numero a macchina scarica, col carico SCRITTO**~~ | **FATTO** (F1.5): i due giri appaiati di stasera hanno `macchina carica: false` **scritto dal banco**, carico 0,40 e 1,10 su 4 nuclei, un solo banco b30. ⚠ **E la voce vecchia resta vera com'era scritta**: i quattro giri di prima sono anteriori alla cura (i loro valori sono tolti, fase 18), e il loro carico era `[R]` |
| ⏳ ⛔ **quanto del numero è il banco stesso** | `[M]` **7,6-8,8 ms per fotogramma** di lettura. Il ritmo non cala (Q9) ⇒ il filo non è saturo, **ma sull'anello non è trascurabile**. ⚠ E non si separa con la fetta «senza lettura» di Q9: senza pixel **nessuna sonda chiude**. ⇒ Serve un giro con la lettura **dimezzata** (una `drawImage` sola): se `T` non cambia, il costo non entra |
| ⏳ ⭐⭐ **il conto dell'elastico** | il distacco calcolato contro quello che l'utente vede (valori tolti, fase 18). Si decide **rimisurando il distacco oggi**, col video, sulla strada vera. ⛔ E intanto **l'accordo «entro il 7 %» di §4-A va tolto** |
| ⏳ **la TASTIERA** | 0 su 276 |
| ⏳ **Q5 a 0,22 ms dalla tolleranza** · **la linearità del confine** | F1.7 punti 4 e 6 |
| ⏳ `[?]` **i valori di partenza dei ritardi** | vanno messi a **multipli del quadro**: una riga, passata al direttore |
| ⏳ ⭐⭐ **il tratto 3, metà del guadagno, non è attribuito** | `[M]` il calo (valore tolto, fase 18) sta su un tratto che sta **sul server** e che la copia zero non attraversa. `[?]` L'ipotesi (il produttore fuori dal thread di tempo reale di PipeWire, F4) è plausibile e **non misurata**. ⇒ Si prova rimettendo il produttore a mano su quel thread con la copia zero accesa |
| ⏳ ⛔ **un solo giro per parte** | sullo stesso binario di ieri **~15 ms di dispersione** (valori tolti, fase 18). Il guadagno è più grande, ma **non di un fattore comodo**. ⇒ Tre giri per parte, alternati: mezz'ora |
| ⏳ **la controprova dal lato del driver** | `[?]` non ho provato che il binario NUOVO su una tela **storta** (1460×888) dia il numero di ieri — sarebbe la conferma del meccanismo del passo |
| ⏳ **l'impronta del binario nel verbale** | l'ho letta **a mano**; la lettura automatica è stata curata **dopo** i due giri, quindi nei loro verbali `md5` è `null` |
| ⏳ **`EncSliceLP`** | `[M]` il codificatore dichiara ancora **bassa potenza**: confermato oggi sul mio giro |

---

## F1.9 Che cosa ho lasciato sulla macchina

⭐ Porte **7760 · 7761 · 7762**, utente **`provaa8`** (quello di A), directory
**`/media/REMOTIX/tmp/08-f1`**, shm `/dev/shm/remotix-08-f1`, scena
`/media/REMOTIX/src/08-f1-scena-lav/08-f1-scena` (copia bit per bit di quella di A), terreno
`/media/REMOTIX/src/08-f1-terreno.sh`, ponte `/media/REMOTIX/src/08-f1-ponte.py`.
⛔ **Le porte 7730 e 7731 e le directory dell'utente non sono mai state toccate.**
⛔ **E non ho toccato nessun file di `src/`.**
⭐ **Il portatile è libero**: Xvfb e Chrome miei spenti, scena ferma.

⭐ **E l'albero del prodotto di oggi resta**: `/media/REMOTIX/src/08-f1-src` (HEAD `6f5f418`,
binario `f45e9f78…`), accanto a quello di ieri `08-a-src` (`73ce3a1f…`) che **non ho toccato**.
⇒ Chiunque può rifare il prima/dopo senza ricostruire niente, e i due terreni ci sono già:
`08-f1-terreno-OGGI.sh` e `08-f1-terreno-IERI.sh`.

I file del banco che ho cambiato, tutti in `banchi/`:
- `04-b30-anello-input.py` — il prologo §4-bis (`createImageBitmap` + `transferFromImageBitmap`) e
  §6 (`leggi_marca_vetro`), **Q11** e i suoi due guasti, `--ritardo-vetro`,
  **`carico_della_macchina()`** ai due capi e due volte, il controllo incrociato col prodotto,
  `scena-ferma` prima di `scena-avvia`, `coda_url` + `strade` + il carico nella riga depositata,
  ⭐ **`--finestra`** (la misura della finestra comanda la tela, e la tela comanda se la copia zero
  si accende), ⭐ **`strada_di_cattura()`** (la copia zero letta dal registro del PRODOTTO, col conto
  del passo accanto), ⭐ **l'impronta del binario** letta da `/proc/PID/exe`;
- `04-b30-lancia.sh` — `scena-costruisci`;
- **nuovo** `04-b30-scena-costruisci.sh`.


---

## 4-F3 · ⛔⛔⭐ AGENTE F3 — **i diciassette millisecondi non esistono**, e a mentire era la macchina · *22 agosto 2026*

> ### ⛔⛔⛔ E IL COLPEVOLE È IL DIRETTORE, NON IL PRODOTTO
>
> Il tratto 9 dell'agente A — *«richiamo del decodificatore → 1° `drawImage`»* — valeva `[M]`
> **17,48 ms**, ed era stato promosso a bersaglio della fase con un agente
> dedicato. ⭐ **Quell'agente è tornato dicendo che non c'era niente da curare.**
>
> `[M]` Lo stesso tratto, tre banchi indipendenti:
>
> | come | ms |
> |---|---|
> | strada **vera** (`bitmaprenderer`), sessione vera, HEVC in hardware, n=200 ×2 | **1,18** e **0,49** |
> | ⛔ **la stessa strada `?tela=2d` di A** | **0,39** e **0,97** |
> | senza server né rete, stream HEVC vero a 60/s | **1,00** (2D) · **2,80** (`bitmaprenderer`) |
>
> ⇒ **Da 15 a 45 volte meno, e su tutt'e due le strade** ⇒ ⛔ **la strada di disegno non era la
> spiegazione**: quella non c'entrava niente.
>
> ⭐⭐ **La causa, misurata**: `[M]` il portatile ha **4 nuclei**, e mentre A misurava ci giravano
> sopra **56 processi Chrome e 5 Xvfb** — perché **tre o quattro agenti facevano banchi da browser
> nello stesso momento**. ⇒ **Li avevo lanciati in parallelo io.**
>
> ⛔ **Che cosa cade con quel numero**: il tratto F non vale 18,83 ms ma **~3,5**; l'anello di §4-A
> **sovrastima di ~15 ms**; e la frase sui quattro tratti su sei va rifatta. ⚠ **E il sospetto si
> estende a tutta la prima ondata**, B compreso. *(I totali dell'anello, sul binario dalla memoria con
> `sws_scale`, sono tolti con la fase 18.)*
>
> ⭐ **La lezione, e non è «misurate meglio»**: `LEZIONI.md` §1.24 diceva *due banchi sulla stessa
> porta si ammazzano in silenzio*. ⛔ **È più larga di così**: due banchi sulla stessa **macchina**
> si falsano in silenzio — e il secondo caso non dà nessun rosso, dà un **numero plausibile**.
> ⇒ **Il carico va dichiarato accanto a ogni numero**, come il palco (§2.0).
>
> ### ⭐ E l'agente ha consegnato uno strumento invece di una cura
>
> **`REMOTIX.tratti()`, dentro `src/pagina.html`**: il prodotto **dichiara da sé** i quattro tratti
> del cliente, **con gli stessi nomi su tutte e tre le strade di disegno**, a `[M]` ~4 µs per
> fotogramma. ⇒ ⛔ **Non serve più riscrivere il prologo di un banco ogni volta che la pagina cambia
> modo di dipingere** — che è esattamente il difetto che aveva bloccato A (0 sonde su 304).
>
> ⚠ **E due numeri del documento vanno buttati**: `[M]` `createImageBitmap` costa **1,05 / 0,41 ms**,
> non i **3,8** di §7.1; e il tratto F vale ~3,5 ms, non 18,83.

> ### ⭐⭐⭐ IL PUNTO STA IN DUE NUMERI PRESI SULLA **STESSA** STRADA CHE HA DATO IL PRIMO
>
> L'agente A, sulla strada `?tela=2d`: `[M]` il tratto *«richiamo del decodificatore → 1°
> `drawImage` finito»* vale **17,48 ms**, contro **0,10** del disegno vero. ⇒ *«il collo di
> bottiglia è il disegno»* è falso — e su questo non c'è niente da correggere: è giusto.
>
> ⛔⛔ **Ma il tratto stesso non c'è.** Rimisurato oggi, in una sessione vera, sulla **stessa
> strada `?tela=2d`**, con lo stesso ferro e lo stesso codec:
>
> | | `richiamo → vetro` (i tratti 9+10 di A) |
> |---|---|
> | `[M]` **A, 22 agosto, `?tela=2d`** | **17,58 ms** |
> | `[M]` **F3, `?tela=2d`** — la strada di A · giro 1 · giro 2 | ⭐ **0,39** · **0,97 ms** (n=200 ×2) |
> | `[M]` **F3, la strada VERA (`bitmaprenderer`)** · giro 1 · giro 2 | ⭐⭐ **1,18** · **0,49 ms** (n=200 ×2) |
>
> *(La colonna dei fotogrammi dipinti, col prodotto sulla strada dalla memoria, è tolta con la fase 18.)*
>
> ⇒ ⭐⭐ **Da quindici a quarantacinque volte meno, sulla strada identica**, e **quattro giri su
> quattro** in **due sessioni indipendenti** stanno fra **0,39 e 1,18 ms**. E non è solo la
> sessione: un
> secondo banco, **senza server e senza rete**, che decodifica in hardware uno stream HEVC vero
> di 1460×888 a 60/s sullo stesso portatile, trova `[M]` **1,00 ms** sulla strada 2D e **2,80**
> su `bitmaprenderer`. ⛔ **I 17,48 ms non si riproducono da nessuna delle due parti.**
>
> ⇒ ⛔⛔ **Non c'è nessuna cura da fare nel disegno del cliente, perché non c'è niente da
> curare.** Il mandato diceva *«prima capire, poi curare»*: capito, e la risposta è che il
> bersaglio non esiste. ⭐ **Il risultato di questo giro è una riga cancellata, non una riga
> aggiunta** — ed è il genere di esito per cui si strumenta prima.
>
> ⚠ **E la conseguenza è più grossa del tratto**: se il tratto 9 vale 0,39 e non 17,48, allora
> il tratto **F, «il cliente»** non vale **18,83 ms** ma `[M]` **~3,5 ms** — e i **~15 ms** di
> differenza **erano nell'anello di A per davvero** (la somma dei suoi tratti chiude con il suo totale
> entro 0,002 ms). ⇒ Sono **dello strumento**, non del prodotto, e l'anello di §4-A **sovrastima
> quello vero di circa quel tanto**.

*Agente F3. Risorse tutte mie: porta **7770** · utente **`provaf3`** (uid 1047) · albero
`/media/REMOTIX/src/08-f-src` · lavoro `/media/REMOTIX/tmp/08-f` · scena
`/dev/shm/remotix-08-f3`. ⛔ Le porte **7730 e 7731** dell'utente non sono mai state toccate, e la
7770 è stata **contata** con `ss -tulnp` prima di prenderla.*

---

## F3.1 · Che cosa è stato costruito

| file | che cos'è |
|---|---|
| `src/pagina.html` | ⭐⭐ **i quattro tratti del cliente li dichiara il PRODOTTO**: `REMOTIX.tratti()` |
| `banchi/08-f3-quanto-aspetta.html` | ⭐⭐ il banco **senza server**: la stessa catena `decode() → richiamo → immagine → vetro` su uno stream vero, con i controlli che separano le tre ipotesi |
| `banchi/08-f3-lancia.py` | il lanciatore del banco: lo stream con `ffmpeg`, i quattordici giri, i confronti |
| `banchi/08-f3-tratti.py` | ⭐ legge `REMOTIX.tratti()` da una **sessione vera**, su tutt'e due le strade nella stessa seduta |
| `banchi/08-f3-sessione.sh` | il terreno mio (porta, utente, albero, scena) |
| `banchi/08-f3-esiti.json` · `08-f3-esiti.jsonl` | i verbali |

⛔ **Non è stata toccata una riga di `src/*.c`, né un banco di un altro agente.**

### ⭐⭐ E la cosa che vale più del banco: **adesso i tratti li dichiara il prodotto**

⛔ **La ragione è il difetto che ha generato questo giro.** Il numero di A è della strada `?tela=2d`
perché il prologo di `04-b30` **legge i pixel dal deposito**, e dal 20 agosto il deposito non
esiste (`DECISIONI.md` §5.4). ⇒ Il numero della strada **viva** non era misurabile da nessuno senza
riscrivere il prologo di un banco — «mezza giornata», dice §A.4.

⇒ ⭐ `src/pagina.html` misura da sé i quattro tratti che gli appartengono e li espone:

```
REMOTIX.tratti()  →  strada · tela · dipinti · saltati_coda · tardive
                     8_decode_richiamo · 9a_richiamo_chiamata · 9b_conversione
                     10_vetro · 9_10_richiamo_vetro · 11_vetro_prossimo_quadro
```

⭐ **Gli stessi nomi su tutt'e tre le strade** (`bitmaprenderer`, `?tela=2d`, il ripiego): un banco
li legge con una riga e non deve più sapere come è fatto il disegno di dentro.
⛔ **E non è un interruttore** (invariante I6): non c'è niente lì dentro che possa cambiare quel che
la pagina fa.

**Il costo, dichiarato**: due `performance.now()` in più per fotogramma (~4 µs a 60/s, `[M]` sotto
il passo dell'orologio del browser, che è 100 µs) più una voce di mappa che si cancella nel
richiamo — e la mappa ha un **tetto di 240**, perché un decodificatore che smettesse di consegnare
farebbe crescere la pagina per sempre.

---

## F3.2 · ⛔ CHE COSA SONO, QUEI MILLISECONDI — e la risposta è «non ci sono»

**Le tre ipotesi del mandato, e come apparirebbe ciascuna** (`LEZIONI.md` §1.11 regola 1: per ogni
prova indiretta si scrive prima come apparirebbe il caso opposto):

| | l'ipotesi | come apparirebbe |
|---|---|---|
| **a** | il **decodificatore hardware** macina | l'attesa sta dentro la conversione del fotogramma **e solo lì**; i gemelli (microtask, macrotask, immagine piccola) restano a ~0 |
| **b** | si aspetta un **quadro del browser** (16,7 ms a 60 Hz — un numero sospettosamente vicino) | ⛔ **è il muro**: l'attesa è incollata al quadro, e **sparisce dove non c'è scanout** |
| **c** | la **promessa si risolve tardi** perché il thread è occupato | i gemelli salgono **insieme** all'attesa, e in assoluto |

### ⭐ E il banco ha risposto a una domanda che veniva prima: **si aspetta?**

`[M]` **Banco senza server**, portatile, Chrome, GPU `ANGLE (Intel, Mesa Intel(R) Graphics
(ADL-N))`, HEVC **in hardware** (⚠ `[M]` Chrome **rifiuta** `prefer-software` su HEVC: su questo
motore HEVC è **solo** hardware), stream vero 1460×888 consegnato a 60/s, 400 fotogrammi per giro:

| giro | tratto 9 | 9+10 | contro i 17,58 di A |
|---|---|---|---|
| `2d-hw-pulito` — la strada di A, **senza strumento addosso** | **0,80 ms** | **1,00** | **−94 %** |
| `bitmap-hw-pulito` — la strada vera | **2,70** | **2,80** | **−84 %** |
| `2d-hw-letto` — **con la lettura dei pixel dentro il richiamo, come fa il banco di A** | **2,40** | 2,60 | −85 % |
| `2d-h264-hw` (hardware) | 2,80 | 3,00 | −83 % |
| `2d-h264-sw` (**software**) | 1,50 | 1,60 | −91 % |

⇒ ⭐⭐ **Sotto i 5 ms non c'è nessuna attesa da diagnosticare**, e il banco lo dice con un verdetto
invece di scegliere una delle tre ipotesi sul rumore. ⛔ **Un banco che partisse dalle tre ipotesi
ne sceglierebbe una anche su mezzo millisecondo.**

⇒ E le tre ipotesi restano **tutte e tre smentite come spiegazione dei 17 ms**:
- **(a) il decodificatore**: lo stesso stream in **software** costa **meno** (1,50 contro 2,80). Il
  decodificatore hardware non sta facendo aspettare nessuno;
- **(c) la coda**: `[M]` la **netta** — quel che il fotogramma aggiunge sopra a una continuazione
  qualunque dello stesso richiamo — vale **0,00 ms**. Tutto quel che si misura è il confine del
  compito, e il confine del compito è ~1 ms;
- **(b) il quadro**: ⛔ **non provato né escluso su quel palco**, e si dichiara: `[M]` il ritmo di
  `requestAnimationFrame` su questo Xvfb passa da **1 a 434 quadri** fra un giro e l'altro
  (`STUDI.md` §web §6.2 lo diceva già: senza scanout rAF non gira). ⇒ Il controllo positivo di (b)
  **non è eseguibile lì**, e il banco lo scrive invece di contarlo verde.
  ⭐ Ma in **sessione vera** la domanda è chiusa lo stesso: il tratto vale **1,18 ms**, cioè meno di
  un decimo di quadro. Nessun quadro ci sta dentro.

### ⭐ E la sessione vera, che è quella che conta

`[M]` 22 agosto 2026, server **7770** sul mio albero, utente `provaf3`, GNOME headless, monitor
virtuale **1520 × 868 @ 60 Hz**, scena `04-b30-scena` a 60 disegni/s, codec **HEVC**
`hev1.1.6.L153.B0` **in hardware**, `VideoFrame.format` **BGRX**, GPU della pagina `ANGLE (Intel,
Mesa Intel(R) Graphics (ADL-N))`, rete WiFi vera in mezzo, **nessun errore**:

| tratto | **strada VERA** g1 · g2 | strada `?tela=2d` g1 · g2 |
|---|---|---|
| 8 · `decode()` → richiamo | **2,20** · **0,79 ms** | 0,74 · 1,82 |
| 9a · richiamo → chiamata | **0,04** · **0,02** | — |
| 9b · la conversione (`createImageBitmap`) | **1,05** · **0,41** | — |
| 10 · il vetro (`transferFromImageBitmap`) | **0,04** · **0,02** | — |
| ⭐ **9+10 · richiamo → VETRO** | ⭐⭐ **1,18** · **0,49 ms** | ⭐ **0,39** · **0,97 ms** |
| ⭐ 11 · vetro → prossimo quadro | — · **1,67** [p95 14,53] n=55 | — |
| saltati in coda · tardive | **0 · 0** | 0 · 0 |

*(La riga dei fotogrammi dipinti, col prodotto sulla strada dalla memoria, è tolta con la fase 18.)*

⭐ **Il tratto 11 è il primo numero che quel pezzo cieco abbia mai avuto**: `[M]` **1,67 ms**
mediani fra il vetro cambiato e il quadro successivo del browser (p95 **14,53**, max **18,16**,
n=55). ⛔ **Non è «il pixel acceso»** — è il **primo istante in cui può accendersi**, cioè il
limite **inferiore** dei `[?]` 16-40 ms di `STUDI.md` §web §6.2, e il p95 dice che ogni tanto ci
sta dentro un quadro intero. ⚠ Un giro su quattro l'ha consegnato: sugli altri tre
`requestAnimationFrame` non è mai scattato (§F3.4 punto 2).

⭐ **`9a` vale 0,04 ms**, ed è un controllo, non un dato di colore: se un giorno non valesse ~zero
vorrebbe dire che fra il richiamo e la conversione qualcuno ha infilato del lavoro, e oggi nessun
conto lo vedrebbe.

⚠ **`createImageBitmap` costa 1,05 e 0,41 ms qui**, non i **3,8** di `SPECIFICHE.md`/§7.1. ⇒ Quel
numero va rimisurato prima di essere citato ancora; non è sbagliato, è di un altro palco.

### ⭐ E un controllo che ha lavorato subito

`[M]` Un giro è stato **rifiutato dal banco stesso**: *«la pagina dipinge 0,0 fotogrammi/s: il
PALCO è fermo (la scena non è sul monitor di questa sessione). ⇒ NON misuro»*. ⛔ Senza quella
riga il verbale avrebbe detto **«non misurato»** su tutti i tratti, e chi lo rilegge avrebbe letto
*«lo strumento ha guardato e non ha visto»* invece di *«lo strumento non ha potuto guardare»* —
`LEZIONI.md` §1.21. ⚠ E la riga esiste perché il **primo** giro di oggi era esattamente così:
`[M]` **2 fotogrammi dipinti in 30 secondi**, e il banco allora **non se n'era accorto**.

---

## F3.3 · ⛔ Dove sono finiti, allora, quei 17 ms

`[R]` Il prologo di `04-b30-anello-input.py` fa **due cose dentro lo stesso richiamo del
decodificatore**, e la seconda è quella che pesa:

1. avvolge `CanvasRenderingContext2D.prototype.drawImage` e ne misura la durata (`t_dip_a =
   t1 + disegni[0]` ⇒ **il tratto 9 È la durata del primo `drawImage`**);
2. ⛔ subito dopo **rilegge i pixel dal deposito con `getImageData`**, due finestrelle, **a ogni
   fotogramma**.

⇒ ⭐ **Una tela 2D da cui si rilegge viene retrocessa a tela di CPU**, e da quel momento ogni
`drawImage` di un `VideoFrame` che sta in GPU non è un disegno: è una **rilettura dalla GPU**.

⚠ **E qui la mia stessa prova mi smentisce a metà, e si scrive**: rifacendo *esattamente* quello nel
banco isolato, il disegno passa da **0,80 a 2,40 ms** — `[M]` **+1,60**, non +17. Con
`willReadFrequently` acceso: **2,70**, cioè **nessuna differenza**.

⇒ `[?]` **Il meccanismo è plausibile e la sua taglia non torna.** Quel che è `[M]` e non dipende
dall'ipotesi:

- sulla **stessa strada**, con **strumento** (A) **17,58 ms**, senza (F3) **0,39 ms**;
- il banco di A misura **4,12 – 4,86 ms** di sola lettura delle marche, e lo dichiara (Q12);
- ⛔ e il **palco era condiviso in un modo che nessuno ha scritto**: `[M]` mentre giravano queste
  misure il portatile — **4 nuclei** — aveva **56 processi di Chrome** e **5 `Xvfb`** vivi
  contemporaneamente, cioè tre o quattro agenti della fase 8 che facevano banchi da browser sulla
  stessa macchina. ⇒ ⭐ **È la spiegazione più economica**, e vale anche per A.

---

## F3.4 · ⛔⛔ CHE COSA NON HA FUNZIONATO

### 1. ⛔ `08-b67-elastico.py` sul mio terreno NON dà un numero, e non lo si cita

`[M]` giro `f3-dopo-strumentata`: **527,7 ms** di ritardo, **0 px** di distacco, **Q1 rosso**.
`[R]` La causa sta nel verbale: il banco ha generato **3 125 movimenti** e ne sono **usciti 30**.
⇒ ⛔ **Non è «l'anello è lungo», è «la mano non è partita»**: `Input.dispatchMouseEvent` via CDP ha
impiegato `[M]` **~5 secondi per evento** su questo palco, e il banco stesso lo dice — *«3 intervalli
di movimento: troppo pochi per dire che velocità aveva la mano. ⚠ Non è "la mano era lenta"»*.

⚠ **La causa è il palco condiviso di §F3.3**, non il banco di B: con 56 Chrome su 4 nuclei il canale
di diagnosi si accoda. ⭐ **Il banco di B ha rifiutato correttamente di consegnare un numero**, ed è
esattamente il comportamento che gli si chiede.

⇒ ⛔ **Il «dopo» in barre del titolo NON c'è**, e non si prende da un'altra seduta. Il mio prima/dopo
è quello di §F3.2, **coi fotogrammi accanto ai millisecondi** (i fotogrammi al secondo, sul binario
dalla memoria, sono tolti con la fase 18), con **0 saltati in coda e 0 tardive** su tutti e quattro i giri.
⇒ Il prodotto strumentato dipinge come prima, e **non è un'impressione: è il denominatore**.
⚠ E il confronto regge perché **la cura è misurazione e basta**: non c'è nessuna riga che cambi
quel che la pagina fa. ⛔ Se ci fosse stata, questo «dopo» non sarebbe bastato.

### 2. ⚠ Il tratto 11 esce **un giro su quattro**, e il denominatore va detto

Il prodotto lo campiona uno ogni 16 fotogrammi. `[M]` Su quattro giri ne ha consegnati **55
campioni in uno solo**; negli altri tre `requestAnimationFrame` **non è mai scattato**. `[R]` È la
stessa cosa di `STUDI.md` §web §6.2 — dove non c'è scanout rAF non gira — e sul banco senza server
`[M]` il ritmo dei quadri passa da **1 a 434** fra un giro e l'altro sulla stessa macchina.
⇒ ⛔ **Il numero c'è ma il denominatore è di un giro solo**: `1,67 ms` mediani va letto come un
**primo** numero, non come il numero. ⭐ Il codice per prenderlo bene c'è ed è gratis: basta un
palco con scanout vero.

### 3. ⛔⛔ Ho toccato l'utente di un altro agente, e va detto

`[M]` Il mio terreno chiedeva l'utente **`provaf8`**; `04-b32-terreno.sh` ha risposto *«c'è già —
non lo rifaccio»* e **poi gli ha riposto la parola d'ordine** e ha scritto il drop-in di systemd in
`/home/provaf8/.config`. ⛔ **`provaf8` (uid 1044) è di un altro agente della fase**, che l'aveva
creato pochi minuti prima. ⇒ Ho cambiato subito utente (**`provaf3`**, uid **1047**) e ho lasciato
`provaf8` in pace da quel momento.

⚠ **Il danno possibile e il suo limite**: la parola che ho posto è `provaf8-2026`, cioè la
convenzione del progetto; se quell'agente usa la stessa convenzione **non è cambiato niente**, se ne
usa un'altra **la sua sessione non entra più**. ⛔ **Non è verificabile da qui.**
⭐ **E la lezione è del processo, non mia**: `LEZIONI.md` §1.24 dice di contare le **porte** prima di
prenderle. `[M]` Oggi le porte le ho contate e andava bene; **quel che ha morso è l'UTENTE**, e
nessuna regola diceva di contarlo. ⇒ La regola va estesa: **utente, uid, porta, ban-file, socket e
nome dello shm si contano tutti prima**. Lo stesso è successo con lo shm: `/dev/shm/remotix-08-f`
era già di `provaf8`, e la scena moriva con `Permission denied` — quello **l'ho visto subito**
perché fallisce rumorosamente, mentre l'utente ha fallito **in silenzio**.

### 4. ⚠ Tre difetti dello strumento, trovati dallo strumento stesso

- ⛔ **il primo `bmp_ms` che ho letto era il costo del banco**: `[M]` `createImageBitmap` **0,90 ms**
  e il microtask di controllo **0,90** — identici, perché i controlli stanno dentro tutt'e due.
  ⇒ Curato con la **netta** (si sottrae il gemello) e con i giri **puliti** (i controlli spenti);
- ⛔ **il verdetto della coda era verde sempre**: il rapporto `controlli/attesa` vale ~1,0 anche su
  un thread libero. È `LEZIONI.md` §1.20 in persona — *«esiste un caso in cui vale zero e il banco
  resta verde?»*. ⇒ Curato con una soglia **assoluta** accanto al rapporto;
- ⛔ **il controllo positivo del fotogramma era cieco**: chiedere a `createImageBitmap` un
  riscalamento a 3840×2160 lascia la netta a **0,00** — ⭐ e quello è un **fatto**, non un difetto:
  quella promessa si risolve al confine del compito, non al termine del lavoro. ⇒ Il controllo si è
  spostato sulla strada 2D, dove il disegno è sincrono, e lì `[M]` otto disegni fanno salire il
  tratto 9 di **+11,50 ms** e i gemelli di **+11,60**, cioè **di quel tanto e non di più**: il banco
  attribuisce.

**La certificazione del banco senza server**: `[M]` taratura verde (20 ms bruciati escono
**+20,00 ms** nel tratto giusto), controllo positivo (c) verde, controllo positivo (a) verde,
controllo (b) **dichiarato non eseguibile**. ⇒ **rossi: 0.**

---

## F3.5 · ⛔ Che cosa resta `[?]` dopo di me

| | |
|---|---|
| ⏳ **perché A ha visto 17,48 ms** | il meccanismo (la tela retrocessa a CPU dalla rilettura) spiega `[M]` **+1,60 ms** su quattordici. Il resto è `[?]`, e il candidato migliore è il **palco condiviso** — ⛔ ma non l'ho isolato |
| ⛔ **l'anello di §4-A va rimisurato** | se il tratto 9 vale 0,39 e non 17,48, il numero di A sovrastima. ⚠ Non basta sottrarre 17: il numero va **ripreso**, con lo strumento che oggi sta nel prodotto invece che nel prologo |
| ⏳ **il tratto 11 e i `[?]` 16-40 ms** | il codice c'è, il palco no: serve un browser con scanout vero |
| ⏳ **il «dopo» in barre del titolo** | `08-b67-elastico.py` va rigirato **su un portatile scarico** |
| ⚠ **`createImageBitmap` = 3,8 ms** | `[M]` oggi ne vale **1,05**. Il numero di §7.1 è di un altro palco e non si cita più senza rifarlo |
| ⚠ **il tratto 8 cambia con la strada** | `[M]` **2,20 ms** su `bitmaprenderer` contro **0,74** su `?tela=2d`, stessa sessione. ⛔ `decode()` → richiamo **non dovrebbe** dipendere da come si dipinge: o è la contesa, o è una coda che si sposta. Non l'ho aperto |

---

## F3.6 · Che cosa ho lasciato sulla macchina

Utente **`provaf3`** (uid 1047) con sessione GNOME, albero `/media/REMOTIX/src/08-f-src`
(**compilato da me**, non copiato), scena `/media/REMOTIX/src/08-f-scena-lav/04-b30-scena`,
lavoro `/media/REMOTIX/tmp/08-f`, blocco condiviso `/dev/shm/remotix-08-f3`.
⭐ **Prodotto, ponte e scena SPENTI**, e il conteggio dei vicini lo dichiara in ogni riga di
registro. ⛔ **Le porte 7730 e 7731 non sono mai state toccate**, e la 7770 è tornata libera.
⚠ Sul portatile ho lasciato pulito: nessun `Xvfb` mio, nessun socket X mio.

---

## F3.7 · ⭐ E la riga che questa fase può portarsi via

⛔ **Il tratto F non è un bersaglio.** L'anello dell'utente è lungo perché sono lunghi **C**
(l'attesa del quadro nella scena), **D** (il quadro di Mutter, un muro a 16,36 ms) ed **E**
(codifica e ritorno). ⇒ ⭐ **Chi apre la fase 8 dopo di me non spenda un'ora sul cliente**: `[M]`
il cliente costa **1,18 ms**, una frazione minima dell'anello, e i tre quarti sono il
decodificatore che consegna (tratto 8), non noi.

⭐⭐ **E il metodo ha retto una seconda volta oggi**: l'agente C credeva di sapere dove stavano i
suoi 16 ms e lo strumento gli ha risposto **0,08**; io sono andato a curare 17 ms e lo strumento ha
risposto che **non ci sono**. ⇒ *Strumentare prima e lasciare che lo strumento smentisca* ha
prodotto, in una giornata, **due bersagli cancellati** — che è lavoro risparmiato, non lavoro perso.


---

## 4-A · ⭐⭐⭐ AGENTE A — il «prima» dell'anello · **rientrato il 22 agosto 2026**

> ### ⭐⭐⭐ E LA COSA PIÙ IMPORTANTE STA IN UNA MOLTIPLICAZIONE: **l'occhio dell'utente e lo strumento dicono la stessa cosa**
>
> L'utente, guardando lo schermo e senza strumenti: il distacco fra la freccia e la finestra è
> **«metà della barra del titolo»**. Il suo trascinamento, misurato dal video, ha velocità mediana
> **3 400 px/s**. Il banco, che non sa niente di tutto questo, misurava `input → vetro`, e
> `ritardo × velocità` tornava col distacco dell'utente entro il 7 %.
>
> *(Il ritardo e i pixel del conto, sul binario dalla memoria con `sws_scale`, sono tolti con la
> fase 18.)*
>
> ⛔⛔ **QUESTO ACCORDO È STATO RITIRATO IL 22 AGOSTO, LA SERA — 📖 §4-F1.** Il ritardo era
> gonfiato dalla contesa fra i miei stessi agenti: `[M]` a macchina scarica l'anello era più corto, e
> il conto **non era più un accordo, e sbagliava nel verso sbagliato** — l'utente vede **più**
> distacco di quanto lo strumento ne misuri.
>
> ⚠ **Quel che resta in piedi**, e non è poco: l'elastico di §1.2 — `distacco = velocità × ritardo` —
> **non è smentito**, è la sua taratura che era falsa. Ma ⛔ **l'accordo fra l'occhio e lo strumento
> era la riga più citata di questo documento, ed era un artefatto della mia orchestrazione.** Resta
> scritta com'era, sbarrata, perché la forma dell'errore vale più della conclusione.
>
> ⭐ **E dice anche a quale velocità l'utente guardava**: alla sua **mediana**, non ai picchi. ⇒ Il
> bersaglio della fase è il trascinamento **normale**, non quello estremo.
>
> ⚠ **Il conto non chiude del tutto, e si dichiara**: l'anello è il **pezzo nostro**; sullo schermo
> vero ci vanno sopra i due pezzi ciechi (`[?]` 4-12 ms in ingresso, 16-40 in uscita) e la rete
> (2,85 ms mediani), e il distacco atteso superava quello che l'utente vede.
> `[?]` O guarda un po' più veloce della sua mediana, o i pezzi ciechi stanno al minimo. **Non è
> risolto, ed è il genere di scarto che si scrive invece di limarlo a parole.**

*Agente A. Banco `banchi/04-b30-anello-input.py`, risorse tutte mie: porte **7740** (ponte) ·
**7741** (prodotto) · **7742** (ancora), utente **`provaa8`** (uid 1041), `/media/REMOTIX/tmp/08-a`,
`/dev/shm/remotix-08-a`, ban-file e socket dentro la mia directory. ⛔ Le due porte dell'utente —
**7730** e **7731** — non sono state toccate, e il conteggio dei vicini lo dichiara a ogni passo.*

---

## A.0 ⭐ Il banco si è ricertificato, e la certificazione conta i guasti

`[M]` `python3 banchi/04-b30-anello-input.py --certifica` ⇒ **PROMOSSO, 53 controlli su 53, e 16
guasti innestati accusati su 16.** Rifatto due volte: prima di toccare il file e dopo (§A.4).
⇒ Il banco sa come fallire.

---

## A.1 ⭐⭐ IL NUMERO DI OGGI

`[M]` **22 agosto 2026** — `input → vetro`, confine **scomodo** ai due capi
(`event.timeStamp` in fase di cattura → **disegno finito**), **cinque giri**, **nessuno sotto il
99 % di sonde chiuse** (n = 228 · 234 · 224 · 413 · 417). Sforava i 50 ms e i 40 di `SPECIFICHE.md`
§3.2, alla mediana e al p95.

*(Le mediane ai due confini, prese sul binario dalla memoria con `sws_scale`, sono tolte con la
fase 18.)*

### ⛔ E i DUE pezzi ciechi, che l'intestazione pretende accanto al numero

| | |
|---|---|
| **in INGRESSO** | `[?]` **4-12 ms**: mano → `event.timeStamp` — dispositivo, nucleo e compositore **del client**. Nessuna API della pagina lo vede: `event.timeStamp` è già il dopo |
| **in USCITA** | `[?]` **16-40 ms**: disegno finito → pixel acceso (`STUDI.md` §web §6.2). ⛔ **E qui ci sono davvero**: il banco ha letto `clienti_sull_xvfb: 0` ⇒ il browser misurato **non sta sull'Xvfb del banco** ma sul desktop vero del portatile, dove un compositore c'è |

⇒ ⛔ **Sullo schermo di un utente**: l'anello + `[?]` 4-12 + `[?]` 16-40 ms, **più la rete**. `SPECIFICHE.md` §3.2 misura «solo il pezzo che è nostro»: i pezzi ciechi si
**dichiarano**, non si promettono.

### ⛔ Il palco, accanto al numero (`LEZIONI.md` §2.0)

`[M]` codec negoziato **HEVC** · stringa `hev1.1.6.L120.B0`, **8 bit**, promozione 8→10 **no** ·
codifica **IN HARDWARE** (`hevc_vaapi`, `/dev/dri/renderD128`, iHD 25.2.3, ⚠ **EncSliceLP**, bassa
potenza — non è la codifica piena) · tela **1460 × 888** · GPU della pagina
`ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` · WebCodecs sì · pagina isolata sì ·
scena sul monitor **Meta-0**, confermato da `wl_surface.enter`, cioè **dal compositore**.
⚠ E sulla macchina giravano contemporaneamente i **due server dell'utente** (7730, 7731): è un
palco condiviso, e la dispersione di §A.4 lo riflette.

---

## A.2 ⭐⭐ LA SCOMPOSIZIONE — e i tratti sono SEI davvero

Il banco produce **11 tratti misurati** (più T, T-comodo, Δ e i due pezzi ciechi = i «16 tratti» che
la certificazione conta). ⭐ **Raggruppati per anello fisico sono esattamente SEI**, ed è la tabella
che la fase 4 aveva promesso senza scriverla:

| | il tratto | 14 ago | **22 ago** | Δ |
|---|---|---|---|---|
| **A** | **la pagina** — `event.timeStamp` → i byte escono (1a + 1b) | 12,75 ms | **7,65 ms** | −5,10 |
| **B** | **l'andata** — byte usciti → la scena riceve l'input (filo + server + `libei` + compositore) (2) | 25,35 ms | **7,25 ms** | **−18,09** |
| **D** | **il quadro di Mutter** — la scena disegna → cattura (`pts`) (4) | 16,23 ms | **16,36 ms** | +0,13 |
| **F** | **il cliente** — `decode()` → disegno finito (7 + 8 + 9 + 10) | 27,25 ms | **18,83 ms** | −8,42 |

*(Fase 18: tolte le righe **C** (l'attesa del quadro nella scena, che la copia zero ha poi mostrato
dipendere dal nostro lavoro nel thread di PipeWire), **E** (codifica e ritorno), la somma, il totale
**T** e le quote sull'anello: il prodotto andava dalla memoria con `sws_scale`, e quei valori non
valgono più.)*

⭐ **I tratti non perdono niente per strada**, e non è un'impressione: sulle **medie** (che sono
additive, a differenza delle mediane) la somma dei tratti 1a…10 contro la media di T faceva
`[M]` **scarto ≤ 0,002 ms su quattro giri**.

### I sotto-tratti, quando servono a chi deve curare

| tratto | 14 ago | **22 ago** (mediana di 5 giri, [min-max]) |
|---|---|---|
| 1a evento → il prodotto lo vede (fase di cattura) | 12,68 | **7,53** [7,04 – 15,04] |
| 1b il prodotto lo vede → i byte escono | 0,07 | **0,12** |
| 2 byte usciti → la scena riceve l'input | 25,35 | **7,25** [6,84 – 7,93] |
| 4 la scena disegna → cattura (`pts` di Mutter) | 16,23 | **16,36** [16,23 – 16,39] |
| 6 primo byte → ULTIMO byte (lo stream sul filo) | 0,20 | **0,24** |
| 7 stream completo → richiamo di `decode()` | 0,09 | **0,10** |
| 8 `decode()` → richiamo del decodificatore | 0,75 | **1,09** |
| 9 ⭐ richiamo → **1° `drawImage`** (l'ATTESA del fotogramma) | 26,34 | **17,48** [14,90 – 18,72] |
| 10 ⭐ 1° → 2° `drawImage` (**il disegno VERO**) | 0,08 | **0,10** |

*(Fase 18: tolti i tratti 3 e 5, per la stessa ragione.)*

### ⭐⭐ Le tre cose che questa tabella dice, e che nessun documento diceva

1. ⛔⛔ **«sei tratti da ~25 ms, nessuno dominante» NON è più vero.** ⇒ **Quattro tratti su sei**
   (C, D, E, F) facevano il grosso dell'anello, i due dell'andata (A e B) poco (le quote sono tolte,
   fase 18). La fase 8 ha **quattro** bersagli, non sei.
2. ⭐ **Q8 conferma di nuovo, e più forte di prima**: `[M]` il **1° `drawImage` costa 17,48 ms e il
   2° ne costa 0,10 — 163 volte**. ⇒ Il tratto 9 **non è il disegno**: è l'**attesa** che il
   fotogramma decodificato sia utilizzabile. La riga «il collo di bottiglia è il disegno» resta
   falsa, e adesso lo è con `[M]`.
3. ⛔ **Il tratto D è un muro, non un margine**: 16,36 ms con dispersione [16,23 – 16,39] su cinque
   giri — è **un quadro a 60 Hz**, esatto. Non si lima: si toglie solo cambiando il modo in cui
   Mutter consegna. ⇒ **Una parte fissa dell'anello è il ritmo del compositore.**

### ⭐ Quanto AGGIUNGE il canale di input (la sola cosa nuova che questo banco sa dire)

`[M]` i tratti che il metro della fase 3 non attraversava sono A + B + C (la loro somma, che
contiene C, è tolta con la fase 18). ⛔ E i due numeri **non si sommano e non si
sottraggono**: `input → vetro` **contiene** `disegno della scena → vetro`.

---

## A.3 ⛔⛔ IL CONFRONTO COL NUMERO DEL 14 AGOSTO — regge in parte, e la parte che NON regge va detta per prima

### Il file del banco: sì, è lo stesso

`[M]` `git log -- banchi/04-b30-anello-input.py`: l'ultima modifica al banco è del **16 agosto**
(`0c85e5c`), ed è la **rinomina dei documenti** (`web.md` → `STUDI.md` §web) — si vede confrontando
il verbale del 14 agosto, che cita `web.md §6.2`, con quello di oggi, che cita `STUDI.md §web §6.2`.
⇒ **Nessuna modifica al metro fra le due date.** L'unica modifica *mia* è §A.4, additiva, e il banco
è stato ricertificato dopo.

### ⛔ Ma il palco è cambiato in DUE modi, e tutt'e due tirano dalla nostra parte

| | 14 agosto | 22 agosto | che effetto ha |
|---|---|---|---|
| ⛔⛔ **la tela** | **1920 × 1080** = 2 073 600 px | **1460 × 888** = 1 296 480 px | **il 62,5 % dei pixel**: meno da convertire, codificare, spedire, decodificare e disegnare ⇒ tira giù **E** e **F**, e forse **D** |
| ⛔ **la profondità** | `hev1.**2.4**` — HEVC **10 bit**, promozione 8→10 **dichiarata** | `hev1.**1.6**` — HEVC **8 bit**, nessuna promozione *(i tempi di conversione con `sws_scale`, caricamento e codifica dalla memoria sono tolti: fase 18)* | tira giù **E** |

⚠ **Ho provato a rimettere la tela di allora e NON ci sono riuscito**: `?adatta=no` è la leva
dichiarata («la pagina di prima del 15 agosto»), il giro con quella coda ha girato, ⛔ **e la tela è
rimasta 1460 × 888**. `[R]` Il registro del server dice perché: `cattura formato negoziato:
1460x888` e `input regione 0: 0,0 1460x888` — **il monitor virtuale NASCE a quella misura**, quindi
`ADATTA_TELA` non c'entra e dall'indirizzo non si torna indietro. ⇒ **Resta `[?]`** quanto del
miglioramento sia prodotto e quanto siano pixel in meno.

### ⭐ Quel che regge lo stesso, e regge bene

1. ⭐⭐ **Il miglioramento è più grande della dispersione, e di molto.** Il **peggiore** dei cinque
   giri di oggi stava sotto il migliore dei due del 14 agosto: non c'è sovrapposizione fra i due
   gruppi (i valori sono tolti, fase 18).
2. ⭐⭐ **Il tratto B non può essere spiegato dai pixel**: `25,35 → 7,25 ms`, **−18,1 ms**, ed è il
   tratto dell'**input che va verso il desktop** — dove non passa nessun fotogramma. ⇒ Quei 18 ms
   sono **prodotto**, e sono la firma della cura del clic delle fasi 6 e 7.
   ⭐ E l'attribuzione non è un'opinione: **Q6** innesta 30 ms sul ramo d'andata e il banco li ritrova
   `[M]` **+31,57 · +31,68 · +32,36 ms proprio nel tratto 2** su tre giri su tre.
3. ⭐ **Il tratto D non si è mosso**: 16,23 → 16,36 ms. Un tratto che *non* cambia quando cambiano
   tela, codec e prodotto è la prova che la scomposizione sta separando cose diverse davvero.
4. ⛔ **E i due numeri sono presi allo stesso confine**: la strada di disegno di oggi è la stessa del
   14 agosto (§A.4), non quella nuova.

⇒ ⭐ **Conclusione onesta**: l'anello si era accorciato (i valori, sul binario dalla memoria con
`sws_scale`, sono tolti con la fase 18). Del guadagno, **almeno 18 ms sono prodotto e dimostrati**
(tratto B); il resto è **`[?]` fra prodotto e una tela più piccola del 37,5 %**.

---

## A.4 ⛔⛔ CHE COSA NON HA FUNZIONATO

### 1. ⛔⛔ Il banco NON misura la strada di disegno che il prodotto usa oggi — ed è il difetto più grosso

`[M]` **Giro `08a-strada-normale-bitmaprenderer`, 22 agosto, senza coda d'indirizzo:**
**304 input spediti**, **1249 eventi ricevuti dalla scena**, **0 sonde CHIUSE su 304** ⇒ **codice
d'uscita 3**, «non ho niente da giudicare». Q2, Q3, Q4, Q5, Q6, Q7, Q8 tutti **NON ESEGUITI**.
Il resto della catena era sano: codifica in hardware, scena su `Meta-0`, input arrivato al desktop.

`[R]` **La causa, letta nel codice e non dedotta.** Dal 20 agosto (`DECISIONI.md` §5.4,
`src/pagina.html` · `MP4_DURATA_MAX()`) la strada normale è `bitmaprenderer` + `createImageBitmap`. Su quella strada:

- **il deposito 2D non esiste** (`src/pagina.html` · `MP4_DURATA_MAX()`: `this.deposito = null; this.deposito_p =
  null;`), e il prologo del banco legge i pixel **esattamente da lì** ⇒ zero marche lette;
- **`drawImage` non viene mai chiamato** ⇒ i tratti 9 e 10 non esistono e Q8 non gira;
- ⛔⛔ **e c'è di peggio, ed è la trappola vera**: il banco prende `t_dip` — il confine **scomodo**,
  «disegno finito» — subito dopo aver chiamato il richiamo del prodotto. Ma `createImageBitmap(f)`
  è **asincrona**: quel richiamo ritorna **prima** che qualcosa sia dipinto. ⇒ Se il deposito ci
  fosse, il banco consegnerebbe un numero **più basso del vero** chiamandolo «scomodo». È la forma
  di `LEZIONI.md` §1.20 in persona.

**La cura che ho applicato (l'unica modifica al banco):** `--coda-url`, un argomento nuovo che
appende una coda all'indirizzo. Con `--coda-url "?tela=2d"` la pagina prende la strada 2D — che è
**esattamente quella del 14 agosto** — e il banco misura di nuovo. Il banco è stato **ricertificato
dopo**: `[M]` 53 su 53, 16 guasti su 16. E la coda finisce nel verbale (`coda_url`).

⛔ **Che cosa questo NON risolve, e va scritto in fase 8**: il numero di §A.1 è **la strada 2D**, non
la strada che l'utente usa. `[?]` La differenza fra le due non è deducibile dai numeri che ci sono:
`SPECIFICHE.md`/§7.1 dice `createImageBitmap` **3,8 ms** mediani, ma il tratto 9 di questo banco
(17,48 ms) **non è il disegno**, è l'attesa del fotogramma — le due grandezze non si sottraggono.
⇒ **Chi vuole il numero della strada vera deve prima rifare il prologo del banco** (chiudere su
`transferFromImageBitmap` invece che su `drawImage`, e leggere i pixel dalla tela invece che dal
deposito). **È lavoro di mezza giornata, e senza di lui la fase 8 misura una strada morta.**

### 2. ⛔ Q5 e Q6 non stanno verdi insieme, e già il 14 agosto non ci stavano

| giro | Q5 (ritardo al ritorno) | Q6 (ritardo all'andata) |
|---|---|---|
| 14 ago `b30-o2-finale` (**il numero consegnato**) | **rosso** | **rosso** |
| 14 ago `b30-o2-finale2` | **rosso** | verde |
| 22 ago `-2` | verde | **rosso** |
| 22 ago `-3` | **rosso** | verde |
| 22 ago `-adattano-1`, `-4`, `-5` | verde | verde |

⇒ ⛔ **Il numero della fase 4 è stato consegnato da un giro con TUTT'E DUE le tarature rosse.**
Non lo dice nessun documento. Oggi le tarature stanno verdi **3 giri su 5**, cioè meglio di allora,
ma non sempre.
`[R]` **Il modo in cui falliscono è sempre lo stesso e non è casuale**: il surplus finisce nel
tratto giusto (`il_surplus_sta_in` lo nomina, `nel_tratto_giusto` a parte), **ma se ne vede un pezzo
anche altrove** — quasi sempre nel tratto 3, «l'attesa del quadro». ⚠ Ha una spiegazione fisica
plausibile: ritardare l'input ne cambia la **fase** rispetto al quadro del compositore, quindi
l'attesa del quadro cambia per costruzione. `[?]` **Ipotesi, non misura** — chi la vuole `[M]` la
prova innestando ritardi non multipli di 16,7 ms.

### 3. ⛔ La TASTIERA non chiude quasi mai — e non era buona nemmeno prima

`[M]` sonde di tastiera chiuse: oggi **0 su 208** · **0 su 212** · **8 su 196** · **5 su 202** ·
**16 su 198**. Il 14 agosto: **27 su ~486** · **35 su ~744**, con mediane di **1007 ms** e **152 ms**
— cioè numeri che non vogliono dire niente.
⇒ ⛔ **Nessun documento deve citare un ritardo di tastiera preso da questo banco**, né oggi né dal
14 agosto. `[?]` Se sia la scena, l'eco o il prodotto **non l'ho aperto**: è fuori dal mio punto.

### 4. ⛔ La scena vecchia non lascia il posto, e il primo giro l'ho perso così

`[M]` primo tentativo con `?tela=2d`: **«la scena non prende il fuoco del puntatore»**, sei
tentativi, e il banco ha rifiutato di misurare — correttamente: un numero preso lì sarebbe preso su
una **miniatura dentro la Panoramica di GNOME**, scala 0,79, senza CRC e senza eco.
`[R]` La causa: `scena-avvia` dice «la scena è già viva» e riusa quella del giro precedente, che il
fuoco l'ha perso. ⇒ **Rimedio: `scena-ferma` fra un giro e l'altro.** Fatto per tutti i giri
successivi. ⚠ Va scritto nel banco: oggi il rimedio è nella testa di chi lo lancia.

### 5. ⚠ Due difetti minori, dichiarati e non curati

- ⛔ **`coda_url` non arriva nell'`esiti.jsonl`**: sta nel verbale su disco ma non nella riga
  depositata. ⇒ Chi rilegge `04-b30-esiti.jsonl` **non può sapere su quale strada di disegno** è
  stato preso un numero. Il mio l'ho messo nel nome del giro (`08a-tela2d-*`); non basta come regola.
- ⛔ **`scena-costruisci` di `04-b30-lancia.sh` non funziona**: `ssh → enter.sh → bash -c` ha tre
  livelli di virgolette e `$L`/`$P` si perdono per strada ⇒ `gcc -o /scena.nuovo`. `[M]` visto oggi.
  Rimedio: la costruzione sta in un **file** (`08-a-scena-costruisci.sh`), non in una riga.

---

## A.5 ⛔ Che cosa resta `[?]` dopo di me

| | |
|---|---|
| ⏳ **quanto dei 41 ms è prodotto** | la tela è passata da 1920×1080 a 1460×888 (**62,5 % dei pixel**) e il flusso da 10 a 8 bit, e non ho trovato il modo di rimettere la tela di allora (`?adatta=no` non basta: il monitor virtuale nasce già a quella misura). **Almeno 18 ms sono prodotto** (tratto B, dimostrato da Q6); il resto è aperto |
| ⏳ **la strada `bitmaprenderer`** | il numero che l'utente vive **non è mai stato misurato da questo banco**. Serve il prologo rifatto (§A.4 punto 1) |
| ⏳ **il tratto C, 23,25 ms e la dispersione più larga di tutte** ([13,86 – 28,28]) | è «la scena riceve l'input → la scena disegna». ⚠ È in parte **la scena del banco**, non il prodotto: prima di curarlo bisogna sapere quanto sia suo |
| ⏳ **i ~16 ms non spiegati dentro il tratto 5** | oggi il tratto 5 vale 24,19 e conversione, caricamento e codifica non lo spiegano tutto *(i loro tempi, sulla strada di `sws_scale`, sono tolti: fase 18)*. Il margine c'è ancora, ed è più piccolo di prima |
| ⏳ **i sei buchi del video dell'utente** | ⛔ **non li ho separati**: il mio giro non ha una traccia di rete abbastanza fine per attribuirli. Resta il punto §2.4 della fase |
| `[?]` **`EncSliceLP`** | `[M]` il codificatore dichiara ancora **bassa potenza, non la codifica piena** — riga letta oggi, e la fase 9 la deve sapere |
| ⚠ **il palco era condiviso** | i due server dell'utente (7730, 7731) giravano durante tutti i giri. È la spiegazione più economica della dispersione 88 – 111 ms, e non l'ho isolata |

---

## A.6 Che cosa ho lasciato sulla macchina

⭐ Utente **`provaa8`** (uid 1041) con sessione GNOME, albero `/media/REMOTIX/src/08-a-src`, scena
`/media/REMOTIX/src/08-a-scena-lav/08-a-scena`, terreno `/media/REMOTIX/src/08-a-terreno.sh`,
directory di lavoro `/media/REMOTIX/tmp/08-a`. Prodotto, ponte e scena **spenti**; si riaccendono
con `08-a-lancia.sh accendi`. ⛔ **Le porte 7730 e 7731 e le directory dell'utente non sono mai state
toccate**, e il conteggio dei vicini lo dichiara in ogni riga di registro del terreno.


---

## 4-C · ⭐⛔ AGENTE C — i ~16 ms hanno un nome, **e la copia zero NON è stata fatta** · *22 agosto 2026*

> ### ⛔⛔ QUEL CHE MANCA SI DICE PRIMA DI QUEL CHE C'È — e la colpa è del direttore, non dell'agente
>
> **La copia zero — il titolo storico di questa fase — non è entrata.** Il tempo è andato nello
> **strumentare**, che era l'ordine che gli ho dato io: *«prima si strumenta, poi si cura; una cura
> misurata con uno strumento che non c'era prima non ha un prima»*. L'ordine era giusto e lo
> rifarei; ⛔ **la stima del tempo era mia ed era sbagliata.**
>
> ⇒ Resta il budget, **da misurare col banco e non da sottrarre a tavolino**: la copia, la
> conversione con `sws_scale` e il caricamento sulla GPU (⛔ i millisecondi sono tolti: la strada
> dalla memoria con `sws_scale` non vale più dopo la fase 18).
>
> ### ⭐⭐ E i ~16 ms hanno un nome — due, e nessuno dei due era quello che cercavamo
>
> `[M]` Strumentato **dentro il prodotto**, dieci voci in fila, mediane su 512 fotogrammi, **resto
> 0,02 ms** — la scomposizione non ha buchi. 1920×1080, HEVC in hardware, 2 450 fotogrammi:
>
> | voce | ms |
> |---|---|
> | ⛔ **il produttore (Mutter)** — dal suo `pts` alla nostra richiamata | *(tolto, fase 18)* |
> | ⛔ **`misura_i_pixel()`** — la diagnostica | **5,34** |
> | la copia | 1,30 |
> | il fotogramma che aspetta nel posto | **0,08** |
>
> *(Il produttore, la conversione con `sws_scale`, il caricamento, la codifica dalla memoria e il
> totale sono tolti: quella strada non vale più dopo la fase 18 — e il produttore, F4 lo ha poi
> mostrato, conteneva il nostro lavoro sulla strada dalla memoria.)*
>
> 1. ⛔ **il produttore sembrava di Mutter**: più di un terzo del margine **non nostro** (smentito da F4);
> 2. ⛔⛔ **5,34 ms sono DIAGNOSTICA**: `misura_i_pixel()` legge **ogni pixel di ogni fotogramma**
>    per riempire **una riga di registro che si scrive una volta sola**;
> 3. ⭐⭐ **e l'ipotesi del coordinatore era sbagliata**, refutata dallo strumento costruito *prima*
>    della cura: credevo fosse il fotogramma che invecchia nel posto, ⇒ `[M]` **0,08 ms**.
>
> ### ⛔⛔ E la cura non ha reso quel che aveva tolto — **i tratti non si sommano**
>
> Il giro sui pixel è passato a cadenza (500 ms). Prima/dopo **alternato**, tre giri, stesso albero,
> md5 verificati diversi.
>
> ⛔ **Ma ha tolto la diagnostica e il totale è sceso molto meno**: `sws_scale` se ne è ripresa una parte
> (3 giri su 3, in tutt'e due i versi) perché la scansione dei pixel **gli scaldava la cache**. ⚠ I
> millisecondi del totale e della conversione sono tolti: passavano da `sws_scale` (fase 18).
> ⛔⛔ **E i fotogrammi consegnati NON sono saliti** (i conteggi, sulla strada dalla memoria, sono tolti
> con la fase 18).
>
> ⇒ ⭐ **Per la regola di §2.2 punto 1, questa non è ancora una vittoria** — «si contano i
> fotogrammi che la pagina dipinge, non i millisecondi». La cura resta (una diagnostica che legge ogni
> pixel per una riga di registro va tolta comunque), ma **il guadagno va rimisurato col banco di B**, sulla scena
> vera, contando i fotogrammi.

*22 agosto 2026. Macchina di prova NIC-OS (Intel i5-13500T, iGPU su `/dev/dri/renderD128`),
utente `provac8`, porta **7752**, albero `/media/REMOTIX/src/08-c-src`, lavoro
`/media/REMOTIX/tmp/08-c`.*

> ### ⛔ E LA PRIMA COSA E' LA PORTA, perche' era assegnata a due
>
> Il mandato mi dava la **7742**. `[M]` La 7742 e' gia' l'**ancora dell'orologio del banco A**
> (`/media/REMOTIX/src/08-a-terreno.sh`, `PORTA_ANCORA=${PORTA_ANCORA:-7742}`), e mentre A girava
> `ss` la contava **occupata**. ⇒ Ho preso **7750 · 7752 · 7753** e l'ho scritto, invece di far
> fallire il ponte di un altro banco a meta' misura (`LEZIONI.md` §1.24: *il ban di uno ferma
> tutti*). ⚠ Chi assegna le porte alla prossima fase legga `08-a-terreno.sh` prima.

---

## C.1 · ⭐⭐ I ~16 ms hanno un nome — e **cinque non erano nostri**

### Che cosa e' stato costruito

`src/cattura.h` · `src/cattura.c` · `src/figlio.c`. Il tratto `cattura → primo byte` adesso si
scompone **dentro il prodotto**, e la riga esce nel registro **una volta al secondo**:

```
⭐ TRATTO cattura → byte fuori: mediana … ms (max …) su 512 fotogrammi del campione,
   2450 in tutto — produttore … · allocazione 0.00 · copia 1.30 · nel posto 0.08 ·
   misura 5.34 · conversione … · caricamento … · codifica … · spedizione 0.01 · resto 0.02
```

*(La forma della riga è quella di allora; i valori della strada dalla memoria — produttore,
conversione con `sws_scale`, caricamento, codifica, totale — sono tolti: non valgono più dopo la
fase 18.)*

Dieci voci **disgiunte e in fila**, **mediane** (non medie) su un anello di 512 fotogrammi, col
**massimo** accanto. ⭐ L'ultima voce e' il **`resto`**: quel che il totale ha in piu' della somma
delle altre. `[M]` vale **0,02 ms** ⇒ **la scomposizione non ha buchi**, ed e' la stessa proprieta'
che rendeva credibile quella della fase 4 (scarto 0,32 ms).

⚠ **Il confine si dichiara**: qui il tratto finisce **quando i byte partono verso il padre**, non
quando arrivano in pagina. Il tratto della fase 4 (valore tolto, fase 18) e' misurato dal client; questo e' **il pezzo di
quello che sta dentro il figlio**, ed e' l'unico che questo processo puo' vedere senza dedurre.
⇒ ⛔ I due numeri **non si sottraggono fra loro**.

### Il banco, e perche' **senza browser**

`08-c-giro.sh` sulla macchina di prova: attacca `banchi/04-b31-cliente.py` (cliente RCP in Python,
dentro il contenitore), aspetta il palco, **legge dal registro** su quale monitor sta — non lo
indovina — e accende li' sopra la scena di `banchi/04-b30-scena.c`, pretendendo che il conto dei
disegni **cresca** («vivo» non e' «disegna»).
⭐ Cliente e prodotto stanno **sulla stessa macchina** ⇒ il `pts` di Mutter e il `time.monotonic()`
del cliente sono lo **stesso `CLOCK_MONOTONIC`**: niente ancora d'orologio, niente Xvfb, niente CDP.

### ⭐⭐ IL NUMERO — `[M]` 1920×1080, HEVC in hardware, 2 450 fotogrammi

| voce | mediana | max | di chi e' |
|---|---|---|---|
| **produttore** *(pts di Mutter → la nostra richiamata)* | ⛔ tolto *(fase 18)* | | ⛔ creduto **di Mutter**; F4 ha mostrato che era in gran parte nostro |
| allocazione *(la `g_malloc` del posto)* | 0,00 | 0,02 | nostro — e non costa: il buffer si riusa |
| **copia** *(la `memcpy` nella richiamata di tempo reale)* | **1,30** | 2,26 | nostro |
| **nel posto** *(il fotogramma che invecchia aspettando)* | **0,08** | 6,52 | nostro |
| **misura** *(`misura_i_pixel()`)* | **5,34** | 13,91 | ⛔ **nostro, e DIAGNOSTICA** |
| conversione *(`sws_scale`)* | ⛔ tolta *(fase 18)* | | nostro |
| caricamento *(→ GPU)* | ⛔ tolto *(fase 18)* | | nostro |
| codifica *(dalla memoria)* | ⛔ tolta *(fase 18)* | | nostro |
| spedizione | 0,01 | 0,03 | nostro |
| **resto** | **0,02** | 1,41 | ⭐ **niente buchi** |
| **TOTALE** | ⛔ tolto *(fase 18)* | | |

### ⇒ Le due risposte, e la seconda e' una **smentita mia**

1. ⛔⛔ **Il produttore sembrava di Mutter.** E' il tempo fra l'istante che Mutter stesso timbra sul
   fotogramma e l'istante in cui la nostra richiamata lo riceve, e qui si concludeva che non c'era
   niente da limare. ⛔ Smentito da F4 (§4-F4): era in gran parte il nostro lavoro sulla strada dalla
   memoria. *(Il valore è tolto con la fase 18.)*
2. ⛔ **`5,34 ms sono una diagnostica.** `misura_i_pixel()` legge **ogni pixel** di ogni fotogramma
   per dire tre cose — il range, «e' nero», «e' uniforme». ⭐ E contando riga per riga chi le
   consuma: nel prodotto finiscono in **UNA** riga di registro, scritta **UNA VOLTA**, al montaggio
   del palco. ⇒ **Trenta-sessanta scansioni al secondo da 5,34 ms per una riga sola.**

⭐ **E la mia ipotesi di partenza era un'altra, ed e' stata REFUTATA dal primo giro.** Credevo che i
~16 ms fossero il fotogramma che **invecchia nel posto** aspettando che il ciclo tornasse a
chiederlo — la fase 4 aveva scritto *«attese a vuoto 0,00/s: ce n'era sempre uno pronto»*, che letto
al contrario suonava «allora aspettava noi». `[M]` **`nel posto` vale 0,08 ms**: il fotogramma **non
invecchia**. L'ipotesi era verosimile e sbagliata, e a dirlo e' stato lo strumento che era stato
costruito **prima** della cura.

### ⚠ Il costo su CPU pura, che dice come cresce

`[M]` banco `08-c-scansione.c`, CPU sola, un processo solo, mediana di 80 giri:

| | 1920×1080 | 2560×1080 | 2560×1440 |
|---|---|---|---|
| **la scansione intera** | **5,36 ms** | 6,78 | **8,89** |
| la stessa a campione 1/8 | 0,10 | 0,12 | 0,17 |
| la `memcpy` del posto | 0,65 | 0,82 | 0,63 |
| `malloc`+tocco+`free` (se il posto non si riusasse) | 0,48 | 0,60 | 0,32 |

⇒ **Cresce coi pixel**: su una tela grande sarebbe **peggio**, non uguale.

> #### ⛔ E LO STRUMENTO HA MENTITO AL PRIMO GIRO, nella direzione comoda
> Il primo `08-c-scansione` diceva **0,000 ms** per una scansione di 14 MB. ⛔ Non era una scoperta:
> il risultato non usciva dalla funzione e **`-O2` aveva cancellato l'intero ciclo**. E' `LEZIONI.md`
> §1.21 dentro lo strumento — *uno strumento che si rompe sotto carico mente quando serve* — e
> mentiva dicendo *«la scansione non costa niente»*, cioe' esattamente quel che avrebbe chiuso la
> caccia. ⇒ Adesso c'e' una **sentinella `volatile`**, e il commento dice perche'.

---

## C.1-bis · La cura, e ⛔ **il conto NON torna come sperava**

`src/cattura.c`: il giro sui pixel si fa sul **primo** fotogramma e poi **al piu' ogni 500 ms**
(`MISURA_PIXEL_OGNI_MS`). La risposta resta **esatta** — cambia solo ogni quanto si da'.

⛔ **E `nero == FALSE` adesso puo' voler dire «non ho guardato».** Per questo `CatturaConsegna` ha un
campo nuovo, **`pixel_misurati`**, e chi legge `nero`/`uniforme` deve guardare prima quello —
esattamente come `stride_letto` sta accanto a `stride` (`LEZIONI.md` §1.9). Sui fotogrammi saltati
**non si copia il valore di prima**: sarebbe due misure sotto la stessa etichetta.

⛔ **Quel che NON ho fatto, e la ragione**: guardare **un pixel ogni otto** costerebbe `[M]` 0,10 ms
invece di 5,36 — meglio ancora. Scartata: cambierebbe il **significato**. Un fotogramma nero tranne
una regione saltata verrebbe dichiarato **NERO**, e una riga che accusa il nero quando il nero non
c'e' manda la caccia dalla parte sbagliata — che costa molto piu' di 5 ms.

### ⭐⭐ IL PRIMA E IL DOPO — tre giri **ALTERNATI**, stesso banco, stessa scena, stessa compagnia

*⛔ Alternati e non in fila: `banchi/03-solo.py` dice che un banco che misura un tempo deve essere
solo, e **non lo ero** (due sessioni GNOME, nove processi `remotix`, carico 1,25-2,09). Alternare e'
l'unico modo onesto di misurare su questa macchina oggi. I due binari nascono dallo **stesso
albero**, cambia **una costante**, e il banco **verifica che gli md5 siano diversi** prima di
misurare.*

| tratto | **prima** *(scansione su ogni fotogramma)* | **dopo** *(a cadenza)* | Δ |
|---|---|---|---|
| allocazione | 0,00 | 0,00 | — |
| copia | 1,30 | 1,65 | +0,35 |
| nel posto | 0,08 | 0,08 | — |
| ⭐ **misura** | **7,28** | **0,00** | **−7,28** |
| spedizione | 0,01 | 0,02 | — |
| resto | 0,03 | 0,04 | — |
| **fotogrammi in 40 s** | *(tolti, fase 18)* | *(tolti, fase 18)* | ⚠ **fermi** |

*(mediana dei tre giri per riga; i tre giri concordano — `misura` 6,48/7,79/7,28 prima, 0,00 sempre
dopo. ⛔ Le righe del produttore, della conversione con `sws_scale`, del caricamento, della codifica
dalla memoria, del totale e i conteggi dei fotogrammi sono tolti: quella strada non vale più dopo la
fase 18.)*

### ⛔⛔ E QUI STA LA COSA CHE VA DETTA PRIMA DEL GUADAGNO

**Ho tolto 7,28 ms e il totale ne ha guadagnati molti meno.** Il resto **l'ha ripreso `sws_scale`**,
**in tutti e tre i giri, in tutt'e due i versi**. Non e' rumore. *(I millisecondi di `sws_scale` e del
totale sono tolti, fase 18.)*

⭐ **E il meccanismo si spiega, ed e' istruttivo**: la scansione leggeva gli **8 MB del fotogramma
subito prima** che `sws_scale` leggesse gli stessi 8 MB. **Scaldava la cache per lui.** Tolta la
scansione, il traffico verso la memoria lo paga swscale. ⇒ *Una parte di quei 5,34 ms non era spreco:
era prefetch fatto per sbaglio.*

⛔ **E i fotogrammi consegnati NON sono saliti** (dentro la dispersione dei giri; i conteggi sono
tolti, fase 18). ⇒ La cura **non compra fluidita'**: compra un poco di ritardo e basta. ⚠ **E' una limatura vera
e piccola, e va chiamata cosi'.**

⭐ **Ma la lezione vale piu' del guadagno**: ⛔ **non si sommeranno mai i tratti tolti sperando che
si sottraggano dal totale.** In questo tratto le voci **non sono indipendenti**: si passano la cache.
Chi togliera' `conversione` e `caricamento` con la copia zero deve **rimisurare il totale**, non
sottrarre le voci.

---

## C.2 · ⛔ **LA COPIA ZERO NON E' STATA FATTA** — e questo e' il buco piu' grosso che lascio

Non ho toccato `CATTURA_STRADA_SCHEDA` ne' l'importazione del DMA-BUF come superficie VA-API.
`src/figlio.c` chiede ancora `CATTURA_STRADA_MEMORIA`.

⛔ **La ragione e' il tempo, non un ostacolo tecnico**, e va detta cosi'. Il mandato metteva
l'ordine — *«prima si strumenta, poi si cura»* — e strumentare e' costato: costruire il banco
server-side, l'utente, la sessione, la scena, il cliente senza browser, e poi tre giri alternati per
non consegnare un numero contaminato. ⇒ Ho consegnato **la misura** e **la cura piu' piccola**, e la
copia zero resta intera per chi viene dopo.

⭐ **E gli lascio il budget misurato**, che prima non c'era:

| che cosa la copia zero cancella | `[M]` oggi |
|---|---|
| `copia` (la `memcpy` nel posto) | **1,65 ms** |
| `conversione` (`sws_scale`) | ⛔ tolta *(fase 18)* |
| `caricamento` (memoria → GPU) | ⛔ tolto *(fase 18)* |

⚠ **E il conto da NON credere e' proprio la somma**: vedi C.1-bis. Le voci si passano la cache, e
quel che si toglie non rende quanto vale sulla tabella. ⇒ **La copia zero va misurata col banco, non stimata dalla tabella.**
⭐ Il banco per farlo c'e' ed e' quello di qui: `08-c-giro.sh` + `08-c-ab.sh` (due binari dallo
stesso albero, alternati, md5 verificati diversi).

⭐ **E resta vero che e' la strada giusta**: la copia zero non **sposta** il traffico di memoria come
ha fatto la mia cura — lo **toglie**. Il fotogramma non esce piu' dalla GPU.

### ⏳ La cura del RILASCIO — la scelta, con la ragione

⛔ Non l'ho scritta (non c'e' la copia zero da rilasciare), ma il mandato chiedeva **quale** e
**perche'**, e la risposta la lascio decisa: **trattenere il `pw_buffer` fino a lettura finita**, non
chiedere `SPA_META_SyncTimeline`.

| | |
|---|---|
| ⭐ **trattenere il buffer** | e' **nostro** e vale su **ogni** produttore. `can_reuse_pw_buffer` si arrende quando la timeline manca, e allora Mutter riusa il buffer mentre VA-API legge `[R]`: trattenendolo il caso non esiste, qualunque cosa il produttore offra. ⚠ Il prezzo e' **un buffer in meno** dei quattro che Mutter ricicla (`DECISIONI.md` §2.3-ter), ed e' un prezzo che si conta |
| ⛔ **chiedere la timeline** | dipende da **quel che il produttore offre**, ed e' la forma che questa fase ha gia' pagato: quando non c'e', non c'e' nessun errore — c'e' **la schermata che si alterna**, che e' il difetto da cui la caccia era partita dalla parte sbagliata (`LEZIONI.md` §8). ⇒ Una cura che sparisce in silenzio su un compositore che non la offre e' precisamente `LEZIONI.md` §1.8 |

⭐ E c'e' un terzo argomento che decide: `LEZIONI.md` §1.25 — *una cura si cerca dovunque valga*.
Trattenere il buffer vale su Mutter, su KWin e su wlroots senza chiedere niente a nessuno; la
timeline va richiesta a ognuno e verificata su ognuno.

⛔ **E non si rifa' la superficie di accumulo**: il DMA-BUF di Mutter **non e' un diff** — c'e'
scritto in testa a `cattura.h`, `[M]` 12 agosto, danno parziale su **410 fotogrammi su 410** e le
barre SMPTE **intere** nel buffer.

---

## C.3 · ⭐ La scheda del codificatore — **e c'era gia' quasi tutto**

⛔ **Il timore del mandato — *«se il codificatore cercasse la discreta ripiegherebbe in CPU senza un
errore»* — NON si applica**, e vale la pena scriverlo invece di curare due volte:

| | |
|---|---|
| il nodo | ⭐ **dichiarato**, non scelto: `figlio.c` `NODO_RENDERING "/dev/dri/renderD128"`, passato a `av_hwdevice_ctx_create` |
| il fornitore | ⭐ **letto** con `vaQueryVendorString` e messo **dentro il nome** del codificatore |
| l'entrypoint | ⭐ **letto dal driver** con `vaQueryConfigEntrypoints` **prima** di aprire, e ⛔ **non si ripiega sull'altro** |
| «e' in hardware?» | ⭐ **chiesto al componente** (`componente_e_hardware()`: accetta un formato di *superficie*), non letto nel nome |
| il ripiego in software | ⭐ **dichiarato** nel registro |

⇒ ⭐ `[M]` dal registro di oggi: *«HEVC 8 bit via hevc_vaapi (in HARDWARE · /dev/dri/renderD128 ·
Intel iHD driver for Intel(R) Gen Graphics - 25.2.3 · ⚠ EncSliceLP, bassa potenza — NON e' la
codifica piena)»*.

### Che cosa ho aggiunto

**1. ⛔ La riga del ripiego nominava il codificatore SBAGLIATO** — difetto vero, trovato refutando.
`figlio.c` scriveva **«hevc_vaapi»** e **«libx265»** dentro le virgolette; ⛔ ma dal 20 agosto quel
ramo serve **anche H.264**, e quando a non aprirsi era `h264_vaapi` il registro accusava un
codificatore che nessuno aveva chiesto e nominava un ripiego che non sarebbe stato usato. ⇒ *Il
numero giusto e la parola sbagliata accanto* (`LEZIONI.md` §1.20). Adesso i due nomi si **stampano**,
e il ripiego viene da **un posto solo** — `codificatore_ripiego_software()`, nuovo in
`codificatore.h`, perche' averlo in due posti sarebbe peggio di tutt'e due.

**2. ⭐⭐ La misura massima si chiede AL DRIVER, prima di aprire** — ed e' anche il punto 4 di D.
`codificatore.c`, `vaGetConfigAttributes(VAConfigAttribMaxPictureWidth/Height)`. **Tre esiti e non
due**: se il driver non risponde o non dichiara l'attributo, **non si conclude niente** e lo si
scrive — non e' «non c'e' limite», e' «non ho guardato». ⇒ `[M]` dal registro di oggi:
*«⭐ il driver dichiara al massimo 16384x12288 per «hevc_vaapi» su /dev/dri/renderD128, e 1920x1080
ci sta — CHIESTO al driver, non dedotto dal nome»*.

### ⭐ E il guasto innestato che rende quel verde credibile

`[M]` banco `08-c-scheda.c`, che chiede al driver e **prova una misura oltre il limite**:

| profilo | entrypoint | massimo dichiarato | 4096×2160 | **4112×2160** | 7680×4320 |
|---|---|---|---|---|---|
| H.264 High | EncSliceLP | **4096 × 4096** | si | ⛔ **NO** | ⛔ NO |
| H.264 High | EncSlice *(piena)* | ⚠ il driver non risponde (13) — **non e' «nessun limite»** | | | |
| HEVC Main | EncSliceLP | **16384 × 12288** | si | si | ⭐ si |
| HEVC Main | EncSlice *(piena)* | ⚠ il driver non risponde (13) | | | |
| HEVC Main10 | EncSliceLP | 16384 × 12288 | si | si | si |

⇒ ⭐ **Il numero di D e' confermato al pixel**: 4096 si', 4112 no. E il controllo **sa dire di no** —
la riga dei 4112 px cambia verdetto, quindi non e' verde per costruzione.
⭐ **Due fatti in piu' che D non aveva**: il massimo di HEVC e' **16384 × 12288** (non 4320), e
l'entrypoint **pieno non esiste affatto** su questa scheda per nessuno dei due codec — che e' la
conferma indipendente del perche' `POTENZA_RENDERING` e' BASSA.

⛔ **E la verifica NON passa da ffmpeg**, che e' il punto 5 di D: `[M]` `-low_power 0` sull'Intel
apre lo stesso `EncSliceLP` **senza fallire**. Qui si parla al driver.

---

## I quattro punti dell'agente D

| | che cosa ho fatto |
|---|---|
| **1 · ⛔ ci si arrende su una CHIAVE** | ⭐ **CURATO e PROVATO COL GUASTO.** Su una chiave non ci si arrende piu': si scende la scala finche' ha scalini, e la riga lo **dichiara** («l'immagine uscira' piu' brutta»). Il conto dei tentativi vale **solo per i delta**. L'unico caso in cui una chiave non parte e' il **fondo della scala**, e la riga dice **quale dei due** e' — «non c'e' piu' niente da abbassare» ≠ «mi sono arreso» |
| **2 · ⛔ la scala e' corta di uno scalino** | ⭐ **CURATO**: `CRF_PASSO` 6 → **9** ⇒ 26 → 35 → 44 → 51, e comprende il QP 44 che `[M]` ce la faceva (11,056 MiB). ⭐ Alzato il **passo** e non i tentativi, con la ragione di D accanto: un tentativo a 8K costa 91-108 ms. ⚠ **Il valore esatto NON e' deciso qui**: c'e' scritto nel commento che il punto di lavoro fra qualita' e banda e' della **fase 9** |
| **3 · ⭐ `max_b_frames = 0`** | ⭐ **NON TOCCATO**, e adesso il commento porta il numero: **59 figure buttabili su 120** e **−16 % di banda** (PSNR −0,065 dB) **contro +67 ms di riordino**, che da soli sfondano i 50 ms dati a *tutto* il pezzo nostro. ⇒ Comprerebbe banda vendendo risposta — lo stesso commercio per cui §6.1 ha chiuso l'anello in parallelo |
| **4 · ⚠ i 4096 px di `h264_vaapi`** | ⭐ **CURATO**, e sta qui sopra in C.3: si chiede al driver **prima di aprire**, e il numero di D e' confermato al pixel |
| **5 · ⚠ i due vicoli ciechi** | ⭐ **Rispettati**: non ho toccato `-max_frame_size` (`[M]` rifiutato in CQP), e la verifica dell'entrypoint **non passa da ffmpeg** |

### ⭐⭐ Il guasto innestato del punto 1, perche' quel ramo non si percorre mai da solo

⛔ Il tetto e' 16 MiB e `[M]` alla tela di prova la chiave piu' grossa vale ~21 KB — lo **0,13 %**.
⇒ Sul banco quel ramo **non si tocca mai**, e una cura che non si percorre e' **verde per
costruzione**. ⭐ Ho abbassato il **tetto** (`TETTO_FOTOGRAMMA` a **6000 byte**), non alzato il
contenuto, e ricostruito un binario apposta.

`[M]` 22 agosto 2026, con il guasto addosso:

```
⚠ CHIAVE sopra il tetto: scendo a QP 35 e RIPROVO (tentativo 2).  ⛔ Una chiave non si abbandona (§5.2)…
⚠ CHIAVE sopra il tetto: scendo a QP 44 e RIPROVO (tentativo 3).  …
```

⭐⭐ **E la prova vera non e' il registro, e' il fotogramma**: `fotogramma 91 · t = 4,002 s · chiave ·
4 728 byte · 1920×1080` — **sotto il tetto falso**, e **994 fotogrammi completi con 2 chiavi** nel
giro. ⛔ Prima della cura quel giro avrebbe scritto *«nemmeno dopo 3 ricodifiche… il fotogramma NON
parte»* e **nessuna chiave sarebbe uscita**.

⚠ **Quel che il guasto NON ha esercitato**: il ramo «delta abbandonato» — a 1920×1080 i delta stanno
sotto i 6 000 byte da soli. `[?]` Resta non percorso.

---

## ⛔ Che cosa NON ha funzionato

1. ⛔⛔ **La mia ipotesi sui ~16 ms era sbagliata.** Credevo fosse il fotogramma che invecchia nel
   posto: `[M]` **0,08 ms**. Refutata dal primo giro dello strumento.
2. ⛔ **La cura ha reso meno di quel che toglieva** — 7,28 ms tolti, molti meno guadagnati, perche'
   `sws_scale` si e' ripreso il tempo che la scansione gli scaldava in cache *(i millisecondi di
   `sws_scale` sono tolti, fase 18)*. ⇒ ⛔ **In questo tratto le
   voci non sono indipendenti**, e i tratti tolti **non si sommano**.
3. ⛔ **I fotogrammi consegnati non sono saliti** (1 271 → 1 242 di mediana, dentro la dispersione).
   La cura compra ritardo, non fluidita'. E' la forma mite di `LEZIONI.md` §6.2, e va detta.
4. ⛔ **Il banco della scansione mentiva**: `-O2` aveva cancellato il ciclo e il banco diceva
   **0,000 ms** — nella direzione che avrebbe chiuso la caccia.
5. ⛔ **Il primo tentativo di costruire i due binari e' uscito con lo STESSO md5**:
   `costruisci.sh` fa `rm -f remotix *.o`, quindi la `cattura.o` compilata col `-D` spariva.
   ⚠ Senza il controllo degli md5 il confronto avrebbe detto *«la cura non cambia niente»* misurando
   **due volte la stessa cosa**. ⇒ Il controllo resta nel banco.
6. ⛔ **La copia zero non e' stata fatta.** Vedi C.2.
7. ⚠ **Non ero solo sulla macchina** (`banchi/03-solo.py`): due sessioni GNOME, nove `remotix`,
   carico 1,25-2,09. ⇒ ⛔ **I valori assoluti di questo rapporto vanno letti come un tetto.** Il
   prima/dopo regge perche' e' **alternato**; i totali singoli no. Nell'ultimo giro della giornata,
   con la macchina piu' carica, la stessa `conversione` e' salita di parecchio senza che nulla
   cambiasse nel codice — ed e' la misura di quanto la compagnia sposti i numeri *(i valori, di
   `sws_scale`, sono tolti: fase 18)*.

---

## Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **la copia zero** | non fatta. Budget — ⛔ da **misurare**, non da sottrarre *(i millisecondi, sulla strada di `sws_scale`, sono tolti: fase 18)* |
| ⏳ **i ms del produttore** | creduti di Mutter (valore tolto, fase 18). `[?]` Non so **di che cosa siano fatti** (composizione? il ciclo di PipeWire? la cadenza del compositore?) — ⛔ risposto poi da F4: erano in gran parte nostri |
| ⏳ **`conversione` che si prende la cache** | `[M]` sale quando la scansione sparisce *(i millisecondi sono tolti: fase 18)*. `[?]` Se `sws_scale` acceda alla memoria in modo migliorabile (piu' thread, flag diversi) non e' stato guardato — ⚠ e la copia zero lo cancella comunque |
| `[?]` **il ramo «delta abbandonato»** | non percorso nemmeno col guasto innestato |
| `[?]` **`banchi/02-cattura-prodotto.c` legge `nero`/`uniforme` senza `pixel_misurati`** | ⛔ **non e' mio e non l'ho toccato.** Prende pochi fotogrammi e il primo si misura sempre, quindi oggi non sbaglia; ma la riga giusta e' stamparlo. **Una riga, per chi lo possiede** |
| `[?]` **il valore di `CRF_PASSO`** | 9 e' *sufficiente*, non *giusto*: il punto di lavoro e' della **fase 9** |
| `[?]` **il distacco in pixel** | ⛔ non l'ho misurato: e' l'anello intero, ed e' del punto A |

---

## Come si rifa'

Tutto sulla macchina di prova, `/media/REMOTIX/src/`:

| | |
|---|---|
| `08-c-terreno.sh` | utente `provac8`, sessione GNOME **senza** `--virtual-monitor`, prodotto sulla **7752** — derivato da quello di A con `08-c-derivami.sh`, **non ricopiato** |
| `08-c-giro.sh` | un giro: cliente senza browser + scena sul monitor **letto dal registro**, e le righe `⭐ TRATTO` |
| `08-c-ab.sh` | ⭐ il prima/dopo **alternato** |
| `08-c-due-binari.sh` | i due binari dallo stesso albero, **con la verifica che gli md5 differiscano** |
| `08-c-scansione.c` | il costo del giro sui pixel, CPU pura, con la sentinella `volatile` |
| `08-c-scheda.c` | i limiti chiesti al driver, **con la misura oltre il limite** |
| `08-c-guasto-chiave.sh` · `08-c-prova-guasto.sh` | il guasto innestato di §5.2 |

⚠ Le copie di questi file stanno anche in
`…/scratchpad/fase8/`. ⛔ Nessuno di loro sta in `banchi/`: sono banchi di questo punto, e
`documenti-si-accorpano` dice che i rapporti degli agenti non si conservano — se il coordinatore li
vuole conservare, il posto e' `banchi/` con un nome `08-…`.


---

## 4-B · ⭐⭐⭐ AGENTE B — il banco del trascinamento, e **il locale ha un numero** · *22 agosto 2026*

> ### ⭐⭐⭐ LA SPECIFICA DELL'UTENTE SMETTE DI ESSERE UN DESIDERIO: adesso il «locale» è misurato
>
> *«La mia specifica è avere un'esperienza utente il più vicina possibile a una situazione locale,
> ma non identica: quello è impossibile.»* — §1.1. ⛔ **Finché il locale non aveva un numero, quella
> frase non era collaudabile da nessuno.** Adesso ce l'ha.
>
> | | ritardo | distacco | **in barre del titolo** |
> |---|---|---|---|
> | ⭐ **il locale**, stesso banco stessa scena | **27,58 ms** | 94 px | **0,13** |
>
> *(Le righe di REMOTIX, tre giri concordi entro l'1 %, e dell'utente a occhio, sul prodotto di prima
> della copia zero — la strada dalla memoria con `sws_scale` — sono tolte con la fase 18.)*
>
> ⇒ ⭐⭐ **La differenza col locale è esattamente quel che aggiungiamo noi sopra al compositore.** Il
> mandato della fase si riscrive in una riga: **accorciare quella differenza.**
>
> ⭐ **E l'utente aveva ragione anche sul limite**: il locale **non è zero** — è 27,58 ms, perché
> anche lì c'è un compositore e uno schermo. *«Ma non identica: quello è impossibile»* è confermato
> dalla misura, non concesso per cortesia.
>
> ⚠ **E lo scarto fra il banco e l'occhio dell'utente si dichiara invece di limarlo a parole**: il banco gira a
> **1560 px** di larghezza, l'utente a **2560** — più pixel, più lavoro per fotogramma. `[?]` La
> differenza non è spiegata, ed è la prima cosa da rifare alla sua misura.

*22 agosto 2026. Da inserire in `fasi/08-l-anello.md` §3 (sviluppo), §4 (misure), §5 (non ha
funzionato) e §7 (resta `[?]`).*

---

## 1 · Che cosa è stato costruito

| file | che cos'è |
|---|---|
| `banchi/08-b67-elastico.py` | ⭐⭐ **il banco**: la mano dell'utente, la lettura dell'eco nei pixel, le tre unità, la separazione della rete, i buchi, i tredici guasti innestati |
| `banchi/08-b67-lancia.sh` | il lanciatore: porte, albero, contenitore, terreno, scena, misura |
| `banchi/08-b67-locale.py` | ⭐⭐ **il termine di paragone locale**, misurato sul ferro dal blocco condiviso della scena |
| `banchi/08-b67-esiti.jsonl` | i verbali dei giri |

⛔ **Non è stata toccata una riga di `src/`.**

⭐ **E niente è stato ricopiato che si potesse importare**: il palco, la distribuzione, il regime e
il **lettore certificato della marca** vengono da `03-b17-ritardo.py`; l'eco e il lettore del blocco
condiviso da `04-b30-anello-input.py`; **la scena è `04-b30-scena.c` senza una riga cambiata**; il
terreno è `04-b32-terreno.sh` **guidato dall'ambiente**, non una sua copia. L'unico pezzo ricopiato
è `batti()` (il `thisisunsafe`), e la ragione sta scritta accanto: il modulo che lo contiene fa
`argparse` a livello di modulo, e importarlo lancerebbe un altro banco.

---

## 2 · ⛔⛔ La porta 7741 **non era libera**, ed era di un altro agente della fase

`[M]` `ss -tulnp` prima di toccarla:

```
udp 0.0.0.0:7741  users:(("remotix",pid=3446627))
    /media/REMOTIX/src/08-a-src/src/remotix --porta 7741
      --ban-file /media/REMOTIX/tmp/08-a/ban-7741
udp 0.0.0.0:7740 / 7742  ("python3")  → il PONTE di 08-a
```

⇒ ⛔ **Il mandato mi assegnava una porta che l'agente A stava già usando.** Non l'ho presa e non
l'ho spenta: `LEZIONI.md` §1.24 — *due banchi sulla stessa porta si ammazzano in silenzio, e il
rosso compare sul terzo* — e il ban-file era il suo, quindi un mio errore avrebbe bannato lui.

⭐ **Il mio terreno, tutto separato**: porta **7746** · utente **`provab8`** (uid 1043) · albero
`/media/REMOTIX/src/08-b-src` · lavoro `/media/REMOTIX/tmp/08-b` (ban-file e socket propri) ·
scena `/dev/shm/remotix-08-b`. ⛔ **7730 e 7731 — i due server dell'utente — non sono mai state
toccate**, e si contano prima e dopo ogni passo.

⚠ **Per il coordinatore**: se il piano assegnava 7741 a due agenti, la tabella delle porte della
fase 8 va corretta prima del prossimo giro.

---

## 3 · Che cosa misura, e come si chiude l'anello

**La grandezza è il distacco fra la freccia e la finestra che la insegue**, e non è un ritardo:

```
distacco = velocità della mano × ritardo dell'anello
```

`[R]` La freccia la muove il **browser**, alla velocità della mano (`pagina.html`: il cursore di
sistema *e* la freccia disegnata, tutt'e due locali). La finestra insegue con **tutto** il ritardo.
⇒ Il distacco si apre quando la mano accelera e si richiude quando rallenta.

### L'anello si chiude **due volte**, e le due si guardano in faccia

1. ⭐⭐ **L'ECO NEI PIXEL** — `04-b30-scena.c` dipinge in una seconda marca **le coordinate stesse
   dell'evento che il compositore le ha consegnato**. Il banco legge quella marca **dalla tela
   dipinta** e sa *dove sta la finestra che l'utente vede in questo istante*. È il confine
   **SCOMODO**, ed è **l'unico dei due che sa dare i pixel**: l'eco *è* una posizione.
2. **IL CAMPO `input` DEI 28 BYTE** — `RCP.md` §6.2, che la pagina raccoglie già in `REMOTIX.giro`.
   Il banco avvolge `GIRO.torna`. È il confine **COMODO**: il fotogramma è *arrivato*, non ancora
   decodificato né dipinto.

⭐ **L'accoppiamento è per COORDINATE**, non per tempo: la traiettoria non ripassa mai sullo stesso
pixel, quindi un eco individua **un** evento. ⛔ E quando non lo individua (mano ripassata, evento
mai partito) il campione **si butta e si conta**.

### ⛔ Il prologo è nuovo, e la ragione è una misura

Quello di A10 legge i pixel dal **deposito**. `[R]` Dal 21 agosto la strada del disegno è
`bitmaprenderer` (`DECISIONI.md` §5.4) e **il deposito non esiste più** (`this.deposito = null`).
Un prologo copiato avrebbe letto `null` a ogni fotogramma. ⇒ Qui i pixel si leggono dalla **vista**,
e il confine del disegno è l'avvolgimento di **`transferFromImageBitmap`** — non di
`VideoDecoder.output`, che su questa strada ritorna **prima** che la tela sia cambiata (il
`createImageBitmap` è asincrono) e regalerebbe un fotogramma intero.

### Le TRE unità, e nessuna esce da sola (Q6)

millisecondi (per noi) · **pixel di distacco** (per l'utente) · ⭐⭐ **frazioni della barra del
titolo** (invariante di scala — è l'unità che ha già retto al confronto con xrdp a risoluzione
diversa).

---

## 4 · ⭐⭐ I PRIMI NUMERI — `[M]` 22 agosto 2026

**Palco dichiarato**: server `192.168.0.2:7746`, utente `provab8`, sessione GNOME headless, monitor
virtuale **1560 × 888 @ 60 Hz**, scena `04-b30-scena.c` a schermo intero. Client: Chrome su Xvfb
**sul portatile**, `bitmaprenderer`, formato **BGRX**. Rete **WiFi vera** (`wlo1`) in mezzo.
⛔ Prestazioni **su Intel UHD 730 integrata**, non su una scheda potente.

**Tre giri indipendenti, e concordavano entro l'1 %.** *Si erano misurati ritardo ai due confini,
distacco in px e in barre, il pezzo nostro e il ritmo dei fotogrammi visti; le misure, prese sul
binario dalla memoria con `sws_scale`, non valgono più dopo la fase 18. Restano la rete misurata
nello stesso giro — 2,7 · 2,8 · 2,7 ms (3,9-4,1 %) — e la mano: 3 185 · 3 178 · 3 226 px/s.*

### ⭐⭐ E il termine di paragone locale, misurato — non supposto

`[M]` `08-b67-locale.py`, **la stessa scena, sulla stessa macchina, senza di noi**, letto dal blocco
condiviso col seqlock verificato:

| tratto | mediana | p95 |
|---|---|---|
| 1. la **scena** (eco ricevuto → dipinto) | 7,29 ms | 16,00 |
| 2. il **compositore** (dipinto → **presentato**, `wp_presentation`) | 20,01 ms | 25,07 |
| 3. ⭐⭐ **L'ANELLO LOCALE** (eco → sullo schermo) | **27,58 ms** | 32,30 |

⇒ 📏 alla mediana dell'utente (3 400 px/s): **94 px**, cioè **0,13 barre del titolo**.
⚠ `n = 29` su 83 chiusi (54 buttati dal setaccio): **è un primo numero con un denominatore
piccolo**, e va rifatto più lungo.

### ⭐⭐ La riga che conta, e sta in una unità sola

| | barre del titolo | ms |
|---|---|---|
| **locale** (lo stesso compositore, senza di noi) | **0,13** | 27,6 |

*(Le righe di REMOTIX — il banco e il giudizio dell'utente — sul prodotto di prima della copia zero
sono tolte con la fase 18.)*

⇒ ⭐ **La differenza col locale è quel che aggiungiamo noi** sopra al compositore: è il pezzo su cui
questa fase può lavorare.

⚠ **E lo scarto fra il banco e l'utente NON si spiega da qui**, ed è una `[?]` aperta:
il banco gira a **1560 px**, l'utente a **2560** — più pixel da catturare, codificare e spedire per
ogni fotogramma — e la sua sessione ha un desktop vero addosso invece di una scena.

### ⭐ E un fatto che nessuno cercava: **il confine comodo si regala metà del numero**

`[M]` (i valori, sul binario dalla memoria, sono tolti con la fase 18). ⇒ ⛔ Chi misurasse l'anello col solo campo `input` dei 28 byte —
cioè con `REMOTIX.giro`, che è quel che la pagina mostra all'utente in diagnostica —
**direbbe la metà del vero**. Il numero della pagina è un limite inferiore, ed è dichiarato tale
nel suo commento; ma ora c'è la misura di **quanto** vale quel limite.

---

## 5 · La certificazione: **13 guasti innestati su 13 accusati**

`python3 banchi/08-b67-elastico.py --certifica` — gira sul portatile, senza rete e senza server,
e finisce **0**. Ogni verde è messo alla prova con un guasto che **deve** far diventare rosso il
banco:

| | guasto innestato | preso da |
|---|---|---|
| G1 | l'eco è **fermo** (la finestra non insegue) | Q4 |
| G2 | l'eco è **illeggibile** (rumore nei pixel) | Q0, Q3 |
| G3 | ⛔ **niente da giudicare** (zero marche) | Q0, Q3 → **uscita 3** |
| G4 | la mano è **lenta** (300 px/s invece di 3 400) | Q1 |
| G5 | le due marche sono di **due fotogrammi diversi** | Q2 |
| G6 | le celle in 0-1 invece che 0-255 (il difetto del 13 agosto) | Q13 |
| G7 | ⛔ la **rete non è misurata** in questo giro | Q9 |
| G8 | ritardo **negativo** (fotogramma prima dell'evento) | Q0 |
| G9 | ⛔ il server **trasforma** le coordinate (§7.3 violata) | Q0, Q5 |
| G10 | la traiettoria **ripassa** sugli stessi pixel (accoppiamento ambiguo) | Q0, Q5 |
| G11 | ⭐ un **buco di 300 ms** innestato nel mezzo | il rilevatore dei buchi lo trova |
| G12 | il **costo del banco** non è misurato | Q12 |
| G13 | si consegnano **solo i millisecondi** | Q6 |

### ⭐⭐ E la taratura è **doppia**, ed è il pezzo che vale di più

Si innesta un ritardo **noto** e si pretende che salgano **tutt'e due** le unità:

| innesto | il **tempo** sale di | atteso | il **distacco** sale di | atteso |
|---|---|---|---|---|
| +30 ms | 30,0 ms | 30 | 94 px | 96 |
| +60 ms | 60,0 ms | 60 | 164 px | 192 |

⛔ **Perché conta**: se il banco ricavasse il distacco dividendo il ritardo per una costante, questa
prova passerebbe **per costruzione**. Qui il distacco viene dai **pixel** (l'eco) e il ritardo dai
**tempi**: le due si muovono insieme nel rapporto della velocità **solo se tutt'e due sono vere**.

### ⭐ Il controllo positivo, e ha corretto **me**

Su una traccia in cui la finestra insegue la mano **senza nessun ritardo** il banco trova
**0 px** e **4,0 ms**. ⛔ La prima stesura di Q11 pretendeva 0,0 ms e **si accusava da sola**:
i 4 ms sono **la grana della mano** (un evento ogni 8 ms, i fotogrammi cadono in mezzo ⇒ mezzo
passo), e nemmeno un anello perfetto potrebbe scendere sotto. ⇒ La soglia è **un passo della mano**,
ed è scritta col perché.

⛔ **Il controllo negativo**: 3 000 sonde di rumore attraverso il lettore certificato → **0 falsi su
3 000**.

---

## 6 · ⛔ Che cosa NON ha funzionato — quattro rossi, tutti del banco

⭐ **Nessuno dei quattro era del prodotto**, e tutti e quattro sono stati trovati dal banco stesso.

1. ⛔⛔ **`[M]` 0 eco su 826 — e la causa era la PANORAMICA di GNOME.**
   Quando la sessione si apre senza finestre, GNOME mostra «Activities» e la scena ci compare dentro
   come **miniatura ridotta e spostata**: la marca c'è nei pixel ma non è né a (0,0) né in scala
   1:1, e ogni CRC salta. ⭐ **L'ho vista solo fotografando la tela** — un contrasto di 0,65 con
   sync 0x00 non lo dice. ⇒ Cura: il banco **batte `Escape` sul desktop remoto** e riprova, fino a
   tre volte; e il verde arriva solo quando la marca si legge con `scorrimento [0,0]` e
   `contrasto 1,0`.
   ⚠ **E prima ancora avevo saltato il passo dello SCORRIMENTO**, che `04-b30` documenta come
   costato *«0 marche su 966»*. Ho ripreso lo stesso rosso pari pari credendolo un dettaglio di
   A10: **la lezione di un altro banco vale solo se la si esegue.**

2. ⛔ **`[M]` un picco di 531 079 px/s** — cioè una mano che non è di nessuno.
   Il pilota consegnava **tutti** i punti scaduti nello stesso giro: quando il filo principale era
   occupato a decodificare restava indietro e poi sparava cinque movimenti nello stesso
   millisecondo. ⇒ Cura: **un solo movimento per giro**, i vecchi si saltano e **si contano** —
   che è quel che fa un mouse vero quando il browser fonde gli eventi.

3. ⛔ **`[M]` 450 000 px/s e poi 26 132 px/s** — due gradini nella traiettoria.
   La serpentina **ripartiva dall'alto** arrivata in fondo (un teletrasporto), e poi **scendeva a
   scalini** di una riga intera al rimbalzo (245 px in 8 ms su uno schermo largo). ⇒ Cura: si
   rimbalza sfasando di mezza riga, e **la discesa è continua** (una diagonale). `[M]` Verificato:
   0 punti ripetuti su 3 125, mediana 3 500 px/s, p90 7 250, picco 13 500.

4. ⛔ **`[M]` l'anello locale diceva 11,71 ms mentre le sue due parti facevano 7,29 + 20,01 = 27,3**
   — cioè un totale **più piccolo delle sue parti**, che è impossibile.
   Il setaccio («un disegno non può precedere l'evento che lo causa») era applicato **solo al primo
   tratto**: tre denominatori diversi sotto la stessa tabella. ⇒ Cura: un setaccio solo, applicato
   una volta, e i buttati si contano (54 su 83). Il numero vero è **27,58 ms**.

⚠ **E una cosa che non ho fatto**: il costo della lettura dei pixel è `[M]` **7,6 ms mediani per
fotogramma** (Q12), sul **filo principale**, cioè lo stesso che decodifica e dipinge. L'ho dimezzato
(una sola riconsegna dalla GPU invece di due) **ma non tolto**: è un errore sistematico dentro ogni
numero di questo banco, e sta dichiarato invece che sperato piccolo.

---

## 7 · Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **lo scarto fra il banco e l'occhio dell'utente** | il banco misura **meno** elastico di quel che l'utente riferisce. Candidati: la **risoluzione** (1560 contro 2560 — più pixel per fotogramma), il **desktop vero** contro una scena sola, e la velocità a cui lui guarda. ⛔ Non è deducibile: si rifà il giro a 2560 |
| ⏳ **i sei buchi** | `[M]` nessun buco sui tre giri (i conteggi, sul binario dalla memoria, sono tolti con la fase 18), contro i **6 in 17,5 s** dell'utente. ⛔ Il rilevatore FUNZIONA (G11 lo prova su un buco innestato), quindi *su questa scena e su questa rete i buchi non ci sono*. ⇒ Sono della sua scena, della sua risoluzione, o del suo momento di WiFi — e restano `[?]` |
| ⏳ **la mano è SINTETICA** | i `PointerEvent` nascono dentro la pagina: ⛔ il pezzo cieco in ingresso **non c'è affatto**, e per questo non si somma. ⚠ E gli eventi non vengono **fusi** dal browser come quelli veri. La strada `--mano cdp` (eventi *fidati*, consegnati da Chrome) è prevista e **non è ancora stata girata** |
| ⏳ **l'anello locale ha n = 29** | il numero c'è, il denominatore è piccolo: va rifatto su un giro lungo |
| ⏳ **il ritmo è 30/s, non 60** | `[M]` circa la metà dei fotogrammi che la scena disegna (i valori, sul binario dalla memoria, sono tolti con la fase 18). ⇒ **metà si perdono per strada**, e questo banco lo *vede* ma non lo *spiega* |
| ⏳ **la taratura sul FERRO** | Q7/Q8 girano sul sintetico. Il ponte di A10 (`04-b30-ponte.py`) sa innestare un ritardo noto sul filo vero, e il terreno lo prevede: **non è stato girato** |
| `[?]` **il codificatore e la sua scheda** | il banco **non** verifica che la codifica sia in hardware. `provab8` è nel gruppo `render` (verificato), ma «ha aperto un render node» non prova niente (`LEZIONI.md` §1.11) |
| ⏳⏳ **il mio numero contro quello dell'agente A** *(valori tolti, fase 18)* | ⛔ **I due numeri vanno riconciliati prima che uno dei due entri in un documento come «l'anello».** Non si sommano e non si sottraggono finché non è scritto, per ciascuno, *quale confine* e *quale scena*: il mio chiude al **disegno finito** su una scena di prova a **1560 px**, e la sua mano è **sintetica**. ⚠ Finché la riconciliazione non c'è, il mio numero vale come **misura dell'elastico su questa scena**, non come «l'anello di REMOTIX» |

---

## 8 · Come si rigira

```bash
bash banchi/08-b67-lancia.sh certifica          # qui, senza server: 13 guasti su 13
bash banchi/08-b67-lancia.sh porta costruisci   # albero e contenitore
bash banchi/08-b67-lancia.sh scena-costruisci
bash banchi/08-b67-lancia.sh terreno accendi
bash banchi/08-b67-lancia.sh aggancia           # il monitor virtuale nasce col figlio
bash banchi/08-b67-lancia.sh scena-avvia
bash banchi/08-b67-lancia.sh misura 25
```

⚠ **Il server sulla 7746 e la scena sono rimasti ACCESI**, così il coordinatore può rigirare senza
rimontare il terreno. Si spengono con `bash banchi/08-b67-lancia.sh spegni` — ⛔ che tocca **solo**
le mie cose.


---

## 4-D · ⭐⭐ AGENTE D — `EncSliceLP` e il peso delle chiavi · **rientrato il 22 agosto 2026**

*Due `[?]` che stavano nei documenti da settimane, chiuse tutte e due con la misura. ⛔ E due
difetti veri trovati in `codificatore.c`, girati al suo proprietario invece che curati di nascosto.*

*Misurato il 22 agosto 2026 sulla macchina di prova (`192.168.0.2`), dentro il contenitore
(`enter.sh`). Ferro: **Intel UHD 730 integrata** — `/dev/dri/renderD128`, driver **iHD 25.2.3**,
VA-API 1.22 — e, come solo controllo, la **Radeon RX 6800** su `renderD129` (Mesa 25.0.7,
radeonsi navi21). ffmpeg 7.1.5, libavcodec 61.19.101.
⛔ Nessuno dei due server dell'utente (7730, 7731) è stato toccato: questi banchi non aprono
nessuna porta, sono codifiche fuori linea.*

---

## D.1 · ⛔ `EncSliceLP` **NON** sa produrre i sotto-livelli temporali

⭐ **La risposta è NO, ed è misurata a tre porte diverse — che si chiudono tutte.**

`RCP.md` §5.2 diceva: *«se `EncSliceLP` dell'Intel li sappia produrre non lo sa nessuno, ed è una
misura della fase 8»*. Adesso lo si sa.

### D.1.1 La prima porta: il driver **non li dichiara** — e i due controlli positivi lo inchiodano

`[M]` `vaGetConfigAttributes` su `renderD128`, attributo `VAConfigAttribEncRateControlExt` (è quello
che porta `max_num_temporal_layers_minus1`), banco `banchi/08-D1-attributi-va.c`:

| profilo, entrypoint | nodo | `EncRateControlExt` | sotto-livelli |
|---|---|---|---|
| H264 ConstrainedBaseline · Main · High, **`EncSliceLP`** | Intel | ⛔ **NON SUPPORTATO** | — |
| HEVC Main · Main10 · Main444 · Main444_10, **`EncSliceLP`** | Intel | ⛔ **NON SUPPORTATO** | — |
| ⭐ **VP9** Profile0/1/2/3, **`EncSliceLP`** | Intel | `0x00000107` | **8** |
| ⭐ H264 ×3 e HEVC Main/Main10, `EncSlice` | AMD | `0x00000103` | **4** |

⛔ **7 profili su 7** dicono no sul percorso che ci riguarda. ⭐ **E i due controlli positivi sono
la parte che vale**:

- **stesso nodo, stesso driver, stesso entrypoint `EncSliceLP`**: su VP9 i sotto-livelli ci sono, e
  sono otto ⇒ il «no» **non è del percorso a bassa potenza in quanto tale**, ed è del binomio
  (codec, entrypoint);
- **stessa libva, stesso banco, altro nodo**: su AMD `EncSlice` ci sono per H.264 *e* per HEVC ⇒ il
  «no» **non è del codec in astratto**, e **non è della mia sonda**.

⚠ Questa è la porta che si legge nel driver, e da sola non basterebbe: il mandato chiedeva una
misura, non la documentazione. Le altre due sono nei byte.

### D.1.2 La seconda porta: **nei byte che escono non c'è nessun sotto-livello**

`[M]` `banchi/08-D1-struttura.py` e `08-D1-costo.py`. Sei configurazioni su `EncSliceLP`
(`-bf` 0, 1, 2/d1, 2/d2, 4/d1, 4/d3), 120 fotogrammi della **scena vera dell'utente** ciascuna,
QP 26 come il prodotto. Si legge `nuh_temporal_id_plus1` in **ogni** intestazione NAL e
`sps_max_sub_layers_minus1` nell'SPS:

⇒ ⛔ **6 celle su 6: `sps_max_sub_layers = 1`, e il 100 % dei NAL VCL porta `temporal_id = 0`.**
E la stessa cosa sul controllo AMD `EncSlice` (1 cella su 1): **ffmpeg non li produce nemmeno dove
l'hardware li dichiara**, perché nell'elenco completo delle opzioni di `hevc_vaapi` e `h264_vaapi`
**non esiste nessuna opzione per chiederli** `[R]` (c'è `b_depth`, e basta).

⇒ ⛔ **Le porte chiuse sono due e indipendenti**: il chip non li dichiara, e la nostra unica strada
verso il chip non saprebbe chiederli comunque.

### D.1.3 ⭐⭐ La terza porta: **prova a smentirti** — il lettore, e il guasto innestato

⛔ *«Non ho visto sotto-livelli»* può voler dire *«il mio lettore è rotto»*. Due testimoni,
`banchi/08-D1-testimone.py`:

| testimone | `[M]` |
|---|---|
| **`libx265` con `temporal-layers=2:bframes=8`**, 48 fotogrammi | `temporal_id` **{0: 25, 1: 23}**, `sps_max_sub_layers = **2**` ⇒ ⭐ **il lettore li vede quando ci sono** |
| **i bit alzati a mano** su un nostro flusso (59 intestazioni portate a `nuh_temporal_id_plus1 = 2`) | il lettore ne conta **59 su 59**, esatte |

⭐ **E `LEZIONI.md` §1.8 si è presentata da sola, dalla parte buona**: chiesto
`temporal-layers=**1**`, x265 **rifiuta a voce alta** — *«No support for temporal sublayers less
than 2; Disabling temporal layers»* — e produce `temporal_id` tutti a zero. ⇒ Al primo giro il mio
controllo positivo **è fallito**, e per un giro la misura è rimasta senza testimone (§«che cosa non
ha funzionato», punto 4). Un banco che avesse guardato solo il codice di uscita avrebbe scritto
«x265 non li fa» ed è **falso**.

⇒ ⛔ **Lo zero su `EncSliceLP` è del codificatore, non del banco.**

### D.1.4 ⭐ Però una **parte** di quel che i sotto-livelli servivano a fare si ottiene già oggi

I sotto-livelli servivano a *«buttare certi fotogrammi senza rompere niente»*. **Quel risultato lì
`EncSliceLP` lo dà**, per un'altra strada: le **figure non di riferimento** — in HEVC i NAL di tipo
`TRAIL_N` — che compaiono appena si chiede `-bf ≥ 1` (nel prodotto è `c->ctx->max_b_frames`,
`codificatore.c` ⚠ *(il codice citato non c'e' piu': da rileggere)*, oggi **0**).

`[M]` `banchi/08-D1-costo.py`, sorgente **grezza NV12 a cadenza fissa**, 120 fotogrammi
2560×1080 della scena dell'utente, `hevc_vaapi` `EncSliceLP` QP 26 (`entrypoint` **confessato da
libavcodec**, non dedotto):

| cella | byte (120 fot.) | buttabili | **ritardo di riordino** | PSNR | SSIM | buttandole |
|---|---|---|---|---|---|---|
| `-bf 0` — **il prodotto oggi** | 89 457 | **0**/120 | **0 ms** | 52,973 | 0,998174 | — |
| `-bf 1` | 75 119 | 59/120 | **67 ms (2 fot.)** | 52,908 | 0,998155 | PULITA, −12 % byte |
| `-bf 2 -b_depth 1` | 66 445 | 79/120 | 100 ms (3 fot.) | 52,852 | 0,998135 | PULITA, −21 % |
| `-bf 2 -b_depth 2` | 66 683 | 39/120 | 133 ms (4 fot.) | 52,853 | 0,998135 | PULITA, −10 % |
| `-bf 4 -b_depth 1` | 66 255 | 95/120 | 167 ms (5 fot.) | 52,796 | 0,998110 | PULITA, −36 % |
| `-bf 4 -b_depth 3` | 62 055 | 23/120 | 234 ms (7 fot.) | 52,797 | 0,998109 | PULITA, −7 % |

**Come si chiedono**: `-bf N` (in C: `ctx->max_b_frames = N`), niente altro. `-b_depth` sposta
**quante** figure sono buttabili, non **se** lo sono.

**Che cosa costano in qualità**: `[M]` **niente di misurabile** — da `-bf 0` a `-bf 1` il PSNR
scende di **0,065 dB** e lo SSIM di **0,00002**.
**Che cosa costano in banda**: `[M]` **la fanno risparmiare**: −16 % a `-bf 1`, fino a −31 %.
⛔ **Che cosa costano davvero**: **il riordino**. Già `-bf 1` mette **due fotogrammi** fra la
cattura e l'uscita — `[M]` **67 ms** a 30/s — cioè **da solo sfonda i 50 ms** che `DECISIONI.md`
§2.4 dà a **tutto** il pezzo nostro.

⇒ ⛔ **Su questo ferro non esiste un modo a ritardo zero di avere fotogrammi buttabili.**
⇒ ⭐ **La riga di `RCP.md` §5.2 — «ogni abbandono costa una chiave» — resta in vigore, e adesso ha
una misura sotto invece di una `[?]`.**

⚠ *E il prodotto è già protetto se qualcuno provasse a toccare quel numero*: `codificatore.c` · `comprimi_comune()`
guarda `dts ≠ pts` e **scrive nel registro** che il codificatore riordina. La riga
`max_b_frames = 0` è giusta com'è: ⛔ **non si tocca.**

### D.1.5 ⭐⭐ E il verde più importante di D.1 è stato **smentito su richiesta**

⛔ *«Il flusso tagliato decodifica senza errori»* **non prova niente**, e §5.2 lo dice testualmente:
a un delta mancante il decodificatore **non solleva nessun errore**. ⇒ La prova sono i **pixel**.
`banchi/08-D1-smentita.py`, flusso `-bf 1`, 120 fotogrammi, impronta SHA-256 di **ogni** immagine
decodificata, confrontata con le immagini del flusso **intero**:

| | figure tolte | immagini | errori del decodificatore | **identiche al flusso intero** |
|---|---|---|---|---|
| **il verde**: buttate tutte le `TRAIL_N` | 59 | 61 | nessuno | ⭐ **61/61 — 100,0 %** |
| ⭐ **guasto innestato**: buttata **1 `TRAIL_R` su 10** | 6 | 114 | *«Could not find ref with POC 20»* | ⛔ **19/114 — 16,7 %** |
| ⭐ **guasto pesante**: buttate **tutte** le `TRAIL_R` | 60 | 60 | *«Could not find ref with POC 2»* | ⛔ **1/60 — 1,7 %** |

⇒ Il verde **diventa rosso** quando si butta la cosa sbagliata, e di quanto: **100 % → 16,7 %**
togliendo **sei** figure su 120. Il banco distingue.

---

## D.2 · Quanto pesa una chiave, contro il tetto dei 16 MiB

**Il tetto è 16 777 216 byte** (`RCP.md` §6.2). Metodo: **ogni** fotogramma è una chiave (`-g 1`,
`idr_interval 0`), e si misura l'**accesso intero** — VPS+SPS+PPS+SEI+IDR — cioè quel che il
protocollo mette in un chunk `key`, non il solo slice. Regime del prodotto: `EncSliceLP`,
`rc_mode=CQP`, **QP 26** (`figlio.c` · `QP_HARDWARE`). ⛔ Le misure del ripiego in software (`libx264`/`libx265`) sono tolte: non valgono più dopo la fase 18.

⛔ **I 10 bit qui sono OTTO PROMOSSI, e si dichiara**: `DECISIONI.md` §2.3-ter ha misurato che dalla
cattura di Mutter i 10 bit veri non escono per nessuna strada. Le righe `main10` qui sotto misurano
l'**etichetta**, non il contenuto — e infatti `[M]` a 8K costano **meno** di `main` (250 355 contro
251 288 byte): la profondità dichiarata non porta informazione che non ci sia.

### D.2.1 ⭐ Alla tela dell'utente il tetto **non si può sfondare**

`[M]` `banchi/08-D2-misure.py`, il video vero girato dall'utente il 22 agosto (2560×1080, 404
fotogrammi), **ogni fotogramma una chiave**:

| | n | min | **mediana** | p90 | **massimo** | quota del tetto |
|---|---|---|---|---|---|---|
| `hevc_vaapi` `EncSliceLP` QP 26 | **404** | 20 328 | **20 817** | 21 070 | **21 433 byte** | **0,13 %** |
| `h264_vaapi` `EncSliceLP` QP 26 | **404** | 24 160 | **24 956** | 25 282 | **25 621 byte** | **0,15 %** |

⇒ ⭐ **Il margine è 782×.** E il tetto lì non si raggiunge **nemmeno di proposito**
(`banchi/08-D2-scala.py`, n=8 per riga, sorgente grezza, codificatore isolato):

| scena, 2560×1080 | massimo | quota |
|---|---|---|
| il desktop vero | 20 259 byte | 0,1 % |
| il desktop + **grana forte** (`noise=alls=30`) | 758 513 byte | 4,5 % |
| ⛔ **rumore uniforme** — il caso peggiore che esista | **2 529 464 byte (2,412 MiB)** | **15,1 %** |

⇒ ⛔⭐ **Alla tela di 2560×1080 il difetto di forma di §6.2 è irraggiungibile**: perfino il rumore
puro sta **6,6 volte** sotto.

### D.2.2 ⛔ A 7680×4320 il tetto **si sfonda davvero**

La scena 8K non si inventa e non si ingrandisce: ⛔ **ingrandire cancella il dettaglio e
sottostima**. Si prende il desktop vero e lo si **affianca 3×4** — dodici immagini diverse — così la
densità di dettaglio per pixel resta quella vera. `[M]` `banchi/08-D2-misure.py` e `08-D2-scala.py`,
`hevc_vaapi` `EncSliceLP` QP 26:

| scena, 7680×4320 | n | massimo | quota del tetto |
|---|---|---|---|
| ⚠ *il desktop **ingrandito** invece che affiancato — il caso comodo* | 6 | *76 520 byte* | *0,5 %* |
| **il desktop affiancato** (dettaglio nativo) | 33 (27 distinte) | **251 288 byte (0,240 MiB)** | **1,5 %** |
| lo stesso, etichetta `main10` (8 bit promossi) | 33 | 250 355 byte | 1,5 % |
| il desktop + grana `alls=10` | 8 | 660 939 byte | 3,9 % |
| il desktop + grana `alls=30` | 8 | 9 136 749 byte (8,713 MiB) | **54,5 %** |
| il desktop + grana `alls=60` | 8 | 15 926 065 byte (15,188 MiB) | ⚠ **94,9 %** |
| ⛔ **rumore uniforme** | 8 | **30 319 727 byte (28,915 MiB)** | ⛔ **180,7 % — sfonda 8/8** |

⚠ **E l'ingrandimento sottostima di 3,3 volte**: è la ragione per cui il mosaico esiste.

⇒ ⛔ **Risposta alla `[?]` di `RCP.md` §6.2: sì, il tetto si sfonda**, alla misura massima che §4.5
dichiara legale, con contenuto quasi incomprimibile. **Ma con un desktop vero, no** — nemmeno a 8K,
dove sta al **1,5 %**.

### D.2.3 ⛔ Oltre i 4096 px l'H.264 in hardware non c'è — e si scende in software

⛔ **`h264_vaapi` su questo chip si ferma a 4096 px per lato** — `[M]` *«Hardware does not support
encoding at size 4112x2160 (constraints: width 32-4096 height 32-4096)»*, mentre 4096×2160 passa
(41 566 byte, n=10). ⇒ **Oltre i 4096 px l'H.264 in hardware NON C'È**, e la tela legale arriva a
7680: là si scende sul ripiego in software. `[M]` `hevc_vaapi` invece regge 7680×4320, 8192×4320 e
perfino 16384×4320 (6 chiavi su 6 ciascuno).

⛔ Si era misurato che il ripiego in software (`libx264`) **sfondava il tetto prima** dell'hardware, con
un filmato granuloso a schermo intero su tela 8K; ⚠ **la misura non vale più dopo la fase 18** (il
ripiego è cambiato) ed è tolta.

### D.2.4 ⛔⛔ E qui c'è il difetto vero: **la scala delle ricodifiche è corta di UNO scalino**

`[R]` `codificatore.c` · `RICODIFICHE_MASSIME` `RICODIFICHE_MASSIME 3`, `:46` `CRF_PASSO 6`, `:2061` `abbassa_qualita()`.
La scala è dunque **QP 26 → 32 → 38** (hardware; in software lo stesso con CRF), e dopo il terzo
tentativo `:2203` **restituisce `false`: il fotogramma NON parte.**

`[M]` sul caso che sfonda, 7680×4320, n=8 per riga:

| tentativo | hardware `hevc_vaapi` LP | esito |
|---|---|---|
| 0 | QP 26 → 28,915 MiB | ⛔ sopra 8/8 |
| 1 | QP 32 → 22,442 MiB | ⛔ sopra 8/8 |
| 2 | QP 38 → **16,654 MiB** | ⛔ **sopra 8/8** |
| **3 — che non c'è** | *QP 44 → 11,056 MiB* | *0/8, ce l'avrebbe fatta* |

*(Le colonne del software, `libx264`, sono tolte: non valgono più dopo la fase 18. Allora davano lo
stesso verdetto.)*

⇒ ⛔⛔ **Manca uno scalino solo**, su tutt'e due i percorsi, e il tentativo che manca è quello che
sarebbe bastato. **QP 38 sta al 104,1 % del tetto**: si perde per il **4 %**.

⛔ **E la conseguenza è quella che `RCP.md` §5.2 esiste per non avere.** Se il fotogramma che «non
parte» è una **chiave**, §5.2 dice *«il server NON DEVE abbandonare un fotogramma chiave»*: il
client resta rotto, manda `RICHIEDI_CHIAVE`, e ogni richiesta fa rifare **tre** ricodifiche che non
producono niente. `[M]` **Ogni tentativo a 8K costa 91-108 ms in hardware** ⇒ **~300 ms** buttati per
fotogramma, a ripetizione (in software molto di più; la misura è tolta, fase 18). **È la spirale.**

⚠ **Quanto è raggiungibile**: serve una tela vicina agli 8K **e** contenuto quasi incomprimibile.
Alla tela dell'utente, mai (§D.2.1). ⇒ È un difetto **vero e dimostrato**, non **urgente**.

---

## ⛔ Che cosa NON ha funzionato — e sette cose sbagliate le ho fatte io

1. ⛔⛔ **Il denominatore era finto, e me ne sono accorto perché era troppo bello.** Le prime 33
   chiavi a 8K uscivano **tutte di 243 497 byte esatti**: impossibile su 33 immagini diverse. Causa:
   `-fps_mode cfr -r 30` sta **dopo** il filtro `tile=3x4`, che consegna 2,5 immagini al secondo ⇒
   la conversione di cadenza le **duplicava dodici volte**. Le immagini distinte erano **tre**, non
   trentatré. ⇒ Rifatto senza conversione: **27 distinte su 33**, e le misure vanno da 243 496 a
   251 288. ⭐ *La regola che ha salvato il numero: un massimo uguale alla mediana è un allarme, non
   un bel risultato.*
2. ⛔ **La prima misura di qualità era priva di senso** — PSNR **16,47 dB** in tutte le celle, e
   identico a cinque decimali. Non era una qualità: era un **disallineamento**, perché confrontavo
   una codifica a cadenza fissa con la sorgente **a cadenza variabile** del video dell'utente. Rifatto
   da una sorgente **grezza NV12 già a cadenza fissa**: **52,9 dB**.
3. ⛔ **`-max_frame_size` non è una via d'uscita**: `[M]` `hevc_vaapi` lo **rifiuta** in CQP, 3
   tentativi su 3 — *«Max frame size is invalid in CQP rate control mode»*. Era il candidato più
   comodo per il tetto e non esiste.
4. ⛔ **Il mio primo controllo positivo è fallito**: `libx265` con `temporal-layers=**1**` non
   produce sotto-livelli e **lo dichiara** (*«No support for temporal sublayers less than 2»*).
   Per un giro la misura di D.1 è rimasta senza testimone. Con `=2` funziona.
5. ⛔⛔ **`-low_power 0` sull'Intel apre lo stesso `VAEntrypointEncSliceLP`** `[M]`, e ffmpeg **non
   fallisce**: prende quel che c'è. ⇒ Chiunque misuri «LP contro entrypoint pieno» su questo chip
   passando da ffmpeg produce **due misure sotto la stessa etichetta**, che è `LEZIONI.md` §1.8 in
   piena regola. ⚠ **Riga da consegnare alla fase 9**, che quella domanda ce l'ha in carico: sul
   ferro di casa il confronto **non si può fare**, perché l'entrypoint pieno non c'è — si fa
   sull'AMD, e allora cambiano insieme chip e driver.
6. ⛔ Le opzioni di colore passate come opzioni **di uscita** su un ingresso grezzo fanno inserire a
   ffmpeg un `auto_scale` che la catena VA-API rifiuta (*«Impossible to convert between the formats
   supported by the filter Parsed_hwupload»*). Un giro perso; nei banchi definitivi il colore si
   dichiara alla sorgente o non si dichiara, e **le misure di D.2 non ne dipendono**.
7. ⚠ **La scena 8K non è un desktop 8K vero**, ed è dichiarato: è il desktop 2560×1080 dell'utente
   affiancato 3×4. Nessuno ha un desktop 8K da fotografare.

---

## `[?]` Che cosa resta aperto

1. `[?]` ⭐ **Un programma che facesse la codifica VA-API da sé — senza ffmpeg — potrebbe
   costruire i sotto-livelli su `EncSliceLP`?** Non è escluso, e l'indizio è misurato:
   `[M]` `VAConfigAttribEncPackedHeaders = 0x1f` su `EncSliceLP` vuol dire che **è l'applicazione a
   impacchettare VPS/SPS/PPS e le intestazioni di slice** ⇒ `nuh_temporal_id_plus1` **lo scrive il
   software, non il chip**; e `EncMaxRefFrames` dà **L0 = 3** riferimenti, cioè lo spazio per una
   piramide di **P** (che **non riordina**, quindi **non costa ritardo**). ⛔ Nessuno l'ha provato.
   Chiuderla vuol dire scrivere un codificatore VA-API nostro: giorni di lavoro, e la decisione è di
   chi possiede `codificatore.c`. ⚠ Finché è aperta, `RCP.md` §5.2 **non cambia**.
2. `[?]` **I 10 bit veri** restano non misurabili da qui: `DECISIONI.md` §2.3-ter, Mutter dà BGRx.
   Tutto quel che qui porta l'etichetta `main10` è **otto bit promossi**, e alle 8K costa `[M]`
   **933 byte in meno** di `main` — cioè l'etichetta non porta informazione.
3. `[?]` **Se un desktop 8K vero somigli al mosaico o alla grana.** Il mosaico è un surrogato
   dichiarato.
4. `[?]` **Il regime senza perdita** (`CODIFICATORE_QUALITA_LOSSLESS`) non è nel percorso di
   `figlio.c` e non l'ho misurato; a 8K un fotogramma senza perdita a 8 bit vale **47 MiB** di soli
   pixel grezzi, quindi sfonderebbe per costruzione. Se un giorno si accende, va misurato.

---

## ⚠ Da girare al proprietario di `src/codificatore.c` — io **non l'ho toccato**

| # | dove | che cosa, e perché |
|---|---|---|
| **1** | `codificatore.c` · `RICODIFICHE_MASSIME` `#define RICODIFICHE_MASSIME 3` **oppure** `:46` `#define CRF_PASSO 6` | ⛔ **La scala è corta di uno scalino**, misurato su tutt'e due i percorsi (§D.2.4): l'ultimo tentativo lascia **16,654 MiB** in hardware, e il quarto ce l'avrebbe fatta *(i numeri del software sono tolti: fase 18)*. ⭐ **Meglio alzare il PASSO che il numero di tentativi**: `[M]` ogni tentativo a 8K costa **91-108 ms** in hardware, quindi un passo da **9** costa un terzo di un tentativo in più. ⚠ Il numero esatto è un punto di lavoro fra qualità e banda ⇒ **è della fase 9**: io porto solo la prova che **3×6 non basta** |
| **2** | `codificatore.c:2203-2207` — la resa | ⛔⛔ Quando si arrende restituisce `false` **anche per una CHIAVE**, e `RCP.md` §5.2 vieta di abbandonare le chiavi. ⇒ Per una chiave non ci si può arrendere: si continua a scendere finché entra — `[M]` **QP 51 dà 1,771 MiB a 8K**, quindi entra **sempre** — e si scrive nel registro che l'immagine è uscita brutta. Abbandonarla lascia il client rotto **per sempre**, e ogni `RICHIEDI_CHIAVE` che segue costa tre ricodifiche **che non producono niente**: è la spirale di §5.2 |
| **3** | `codificatore.c` ⚠ *(il codice citato non c'e' piu': da rileggere)* `c->ctx->max_b_frames = 0` | ⛔ **Non si tocca, e adesso c'è il numero accanto**: metterlo a 1 darebbe `[M]` 59 figure buttabili su 120 e −16 % di banda a qualità invariata, **ma 67 ms di riordino** — da solo oltre i 50 ms di `DECISIONI.md` §2.4. ⭐ Il commento «deciso, non ereditato» merita la misura sotto |
| **4** | *nessuna riga: è una cosa che non esiste* | ⚠ `-max_frame_size` **non** è utilizzabile come tetto: `[M]` `hevc_vaapi` lo rifiuta in CQP, 3/3. Se qualcuno ci pensasse, è già misurato che non c'è |
| **5** | ⚠ **fuori da `codificatore.c`** — riguarda `figlio.c` / la trattativa della tela | `[M]` `h264_vaapi` su `EncSliceLP` accetta **32-4096 px per lato**: **4096×2160 sì, 4112×2160 no**. La tela legale di `RCP.md` §4.5 arriva a **7680×4320** ⇒ oltre i 4096 il ripiego `libx264` non è un'eventualità, è **la regola**, e a 8K costa `[M]` **309 ms** per chiave sul desktop e **1,2-3,3 s** sul granuloso. `hevc_vaapi` invece regge fino a 16384×4320 `[M]`. ⇒ Vale la pena leggerlo dal driver invece di scoprirlo al primo fotogramma |

---

## I banchi

Copiati nel worktree, ⚠ **con il prefisso `08-D` per non pestare i nomi degli altri agenti** — il
coordinatore li rinumeri come vuole:

| banco | che cosa risponde |
|---|---|
| `banchi/08-D1-attributi-va.c` | che cosa dichiara il driver su ogni (profilo, entrypoint) dei due nodi |
| `banchi/08-D1-struttura.py` | `temporal_id` e `sps_max_sub_layers` nei byte che escono |
| `banchi/08-D1-costo.py` | banda, PSNR/SSIM, riordino e figure buttabili per ogni `-bf` |
| `banchi/08-D1-smentita.py` | ⭐ la prova a pixel + i due guasti innestati |
| `banchi/08-D1-testimone.py` | ⭐ i due controlli positivi del lettore di `temporal_id` |
| `banchi/08-D2-misure.py` | le chiavi in byte, con il denominatore vero |
| `banchi/08-D2-scala.py` | dal desktop vero al rumore, codificatore isolato |
| `banchi/08-D2-ripiego.py` | lo stesso in software, e la scala delle ricodifiche |

Si girano sulla macchina di prova dentro il contenitore, da `/srv/src/08-D`, dove sta anche la
scena (`scena-utente.webm`, il video del 22 agosto).


---

## 5 · ⛔ Che cosa NON ha funzionato

*⭐ Nove agenti hanno dichiarato i propri errori invece di consegnare solo i risultati. È la parte
del documento che vale di più, e si legge prima delle misure.*

### 5.1 ⛔⛔ Gli errori del COORDINATORE, che sono i più cari

| | |
|---|---|
| ⛔⛔ **ho lanciato le misure in parallelo** | `[M]` la contesa spostava lo stesso anello di parecchi millisecondi (valori tolti, fase 18). Ha prodotto un numero falso (17,48 ms) **promosso a bersaglio della fase**, con un agente dedicato che è tornato dicendo che non c'era niente da curare. 📖 `LEZIONI.md` §1.26 |
| ⛔⛔ **ho scritto una riga che era un artefatto** | *«l'occhio dell'utente e lo strumento si accordano entro il 7 %»* — la riga più citata della giornata. Il conto tornava **per compensazione**: accostava il ritardo di una grandezza alla velocità di un'altra. 📖 §1.28 |
| ⛔ **ho attribuito alla contesa un numero che non era suo** | e l'ho scritto **dentro una lezione**, che è il posto dove un errore dura di più. Smentito da un quarto agente **mentre la lezione veniva scritta** |
| ⛔ **«tutta la prima ondata è contaminata»** | `[M]` falso: sul banco del distacco il carico non gonfia niente (70,7 contro 70,3). Crederlo avrebbe fatto **buttare misure buone** |
| ⛔ **due collisioni di terreno** | una **porta** già presa (se n'è accorto l'agente, non io) e un **utente** già preso — al secondo il terreno ha **riposto la parola d'ordine** di un agente vivo. ⇒ §1.24 va estesa oltre la porta |
| ⛔ **la stima del tempo** | ho ordinato «prima si strumenta, poi si cura» — **l'ordine era giusto** — ma ho stimato male il tempo, e alla fine della prima ondata **la copia zero non era stata fatta** |

### 5.2 ⛔ Gli errori dei banchi, e ognuno avrebbe prodotto un numero falso

- ⛔ **un denominatore finto**: 33 chiavi a 8K tutte identiche **al byte**, perché una conversione di cadenza duplicava la stessa immagine dodici volte. ⭐ Beccato perché **il massimo era uguale alla mediana** — *un risultato troppo bello è un allarme*;
- ⛔ **una qualità priva di senso** (16,47 dB in tutte le celle): non era una qualità, era un **disallineamento** fra cadenza fissa e variabile;
- ⛔ **quattro falsi rossi in una sera**, e accusavano tutti **lo stato normale**, cioè il giro di controllo. ⭐ *Un falso rosso costa quanto un falso verde: tutt'e due scollegano il colore dal fatto*;
- ⛔ **la panoramica di GNOME** mostrava la scena come **miniatura**: 0 eco su 826, scoperto solo *fotografando* quel che il banco guardava;
- ⛔ **il banco non sapeva leggere la strada di disegno viva**: 0 sonde su 304, e ⭐ **è uscito col codice «non ho niente da giudicare»** invece che con un verde;
- ⛔ **`--window-size` di Chrome ignorato** (profilo `maximized`): tre giri buttati;
- ⛔ **un agente ha rotto il proprio banco con una propria cura** — e il banco è **morto** invece di consegnare numeri falsi.

### 5.3 ⛔ E i difetti del prodotto trovati per strada — **nessuno era il bersaglio**

| | |
|---|---|
| ⛔⛔ **una chiave abbandonata** | dopo tre ricodifiche il codificatore rinunciava **anche a una chiave**, che `RCP.md` §5.2 vieta ⇒ il client resta rotto **per sempre** e ogni `RICHIEDI_CHIAVE` costa tre ricodifiche che non producono niente. **È la spirale** |
| ⛔ **la scala corta di uno scalino** | l'ultimo tentativo lasciava 16,654 MiB contro un tetto di 16,777: **si perdeva per il 4 %** |
| ⛔⛔ **il passo non multiplo di 64** | il desktop usciva **inclinato di qualche pixel per riga, senza nessun errore**, coi millisecondi già perfetti. 1552 e 1544 distano **otto pixel** e danno verdetti opposti |
| ⛔ **un cronometro che misurava il banco** | `vetro_ms` **avvolgeva** il banco: diceva 8-10 ms per un trasferimento che ne costa 0,06 |
| ⛔ **la diagnostica che costava un quarto del tratto** | ogni pixel di ogni fotogramma, per una riga di registro scritta **una volta sola** |
| ⛔ **il ripiego nominava il codificatore sbagliato** | da quando quel ramo serve anche H.264 |

### 5.4 ⛔ E una cura che non ha reso quel che aveva tolto

Tolta la diagnostica dai pixel (7,28 ms), ⛔ **il totale è sceso molto meno**, perché `sws_scale`
se n'è ripreso una parte: la scansione **gli scaldava la cache** *(i millisecondi del totale e di
`sws_scale` sono tolti: fase 18)*. ⛔⛔ **E i
fotogrammi consegnati non erano saliti** (i conteggi sono tolti: fase 18). ⇒ Per la regola di §2.2 punto 1 **non era
ancora una vittoria**, e sta scritto così. ⭐ *(La vittoria è arrivata dopo, con la copia zero.)*

## 6 · Le decisioni prodotte

### 6.1 ⛔ CHIUSA PRIMA DI APRIRSI: l'anello in parallelo — 22 agosto 2026

Mettere l'anello in pipeline — codificare l'N mentre si cattura l'N+1 — alzerebbe i fotogrammi al
secondo pagandoli con **un fotogramma di ritardo in più**.

⛔ **Su questa scena è il peggiore degli scambi**: ai picchi dell'utente (12 400 px/s) un fotogramma
in più vale **da 200 a 350 pixel** di distacco — **mezza finestra**. ⇒ Comprerebbe il contorno
vendendo il piatto.

⭐⭐ **E non serviva una misura nuova per saperlo**: `SPECIFICHE.md` §3.2 lo vietava già —
*«ogni memoria intermedia compra fluidità e vende risposta»*, *«una scelta che alza il ritmo
peggiorando il ritardo non si fa»*. ⇒ La riga era scritta **prima** che il difetto avesse un nome, e
questa fase è la prova che serviva.

### 6.3 ✅ La cura del rilascio: **trattenere il `pw_buffer`**, non chiedere la timeline

Le due schermate che si alternavano erano un problema di **release**, non di *acquire*. Due cure
possibili; scelta la ritenuta, ⭐ **e la ragione è `LEZIONI.md` §1.25**: la ritenuta è **nostra e
vale su ogni compositore**, la timeline dipende da quel che Mutter offre.

⚠ **E il prezzo dell'onestà è dichiarato**: `[M]` il controllo positivo **non ha riprodotto il
danno** (10 marche su 10 anche senza attesa GPU). ⇒ **Prudenza, non necessità misurata.** ⭐ Ma il
guasto è servito lo stesso: senza `vaSyncSurface` la conversione scende 2,86 → 0,38 e la codifica
sale 2,43 → 4,67, totale 6,19 → 6,05 ⇒ **l'attesa costa zero** e dice dov'è il punto giusto.

### 6.4 ✅ Il passo si **misura**, non si calcola — e il ripiego si **dichiara**

`[M]` iHD non onora un passo non multiplo di 64 byte ⇒ desktop **inclinato senza errori**. ⇒ Il
passo si legge **dal chunk**, mai dedotto dalla larghezza; se non è importabile il palco **si
rimonta sulla memoria dichiarandolo nel registro**; al cambio di tela la copia zero **si riprova**.

⛔ **E non si aggiusta il problema restringendo le tele**: sarebbe curare il caso comodo. La cura
vale su **ogni** tela e **ogni** driver (§1.25).

### 6.5 ✅ Una **chiave** non si abbandona mai

`RCP.md` §5.2 lo dice e il codice non lo faceva. ⇒ Per una chiave non ci si arrende: si scende
finché entra — `[M]` **QP 51 dà 1,771 MiB a 8K**, quindi entra **sempre** — e si **scrive nel
registro** che l'immagine è uscita brutta. ⭐ *Un'immagine brutta è recuperabile, un client rotto per
sempre no* (invariante **I1**: brutta e viva).

### 6.6 ✅ `max_b_frames = 0` **non si tocca** — e adesso ha il numero accanto

`[M]` Metterlo a 1 darebbe 59 figure buttabili su 120 e **−16 % di banda a qualità invariata**
(−0,065 dB) — sembra un affare. ⛔ **Costa 67 ms di riordino**, che da solo sfonda i 50 ms dati a
*tutto* il pezzo nostro.

### 6.7 ⏳ Sul tavolo, NON decisa: ritardare la freccia per chiudere l'elastico

Se la freccia venisse disegnata **in ritardo**, alla posizione che il fotogramma sta portando invece
che a quella della mano, il distacco **sparirebbe** — freccia e finestra si muoverebbero insieme.

⛔ **Il prezzo è il puntatore che risponde in ritardo**, e va contro una decisione già presa: la
freccia è locale **apposta**, perché sul DeX a 1,1 fotogrammi al secondo *«è come se si perdessero
gli input»* — non se ne perdeva nessuno, non si **vedeva** che arrivavano (`pagina.html`, 14 agosto).

⇒ 🔸 **È una decisione di prodotto, e la prende l'utente — con i numeri in mano, non adesso.**

---

## 7 · Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **a quale velocità guarda l'utente** | *(il conto px → ms, sul prodotto di allora, è tolto con la fase 18)*. ⛔ **Non è deducibile**: si misura l'anello, non si chiede a lui |
| ⏳ **i ~16 ms non spiegati** | dentro `cattura → primo byte` stanno conversione, caricamento e codifica *(i loro tempi, sulla strada di `sws_scale`, sono tolti: fase 18)* — e **~16 che nessuno dei tre spiega**. ⚠ Un margine, non un difetto |
| ⏳ **gli altri cinque tratti** | la fase 4 dice «sei da ~25 ms». ⛔ **Questo documento ne ha nominato uno solo.** Gli altri cinque vanno aperti |
| ⏳ **i sei buchi** | del WiFi (§2.4) o nostri? Il banco li separa |
| `[?]` **il codificatore e la sua scheda** | VA-API sceglie da sé; se cercasse la discreta — chiusa da udev — ripiegherebbe in CPU **in silenzio** (`DECISIONI.md` §4.6-ter) |
| `[?]` **`EncSliceLP` e i sotto-livelli temporali** | senza, ogni fotogramma abbandonato costa una chiave intera (`RCP.md` §5.2) |
| `[?]` **quanto pesa una chiave 8K** | contro il tetto dei 16 MiB di `RCP.md` |
| ✅ ~~**il puntatore doppio**~~ | **SMENTITO dall'utente il 22 agosto 2026**: *«non ci sono doppi puntatori»*. 📖 §7.3 |

### 7.1 ⭐ Le due strade già provate — non si rifanno

- `createImageBitmap`: ⚠ **non 3,8 ms — sono 1,05 / 0,41**, rifatti il 22 agosto (📖 §4-F3 e §4-F1).
  ⛔ Il 3,8 era di un altro palco e **non si cita più senza rifarlo**. Resta vero che è già **nove
  volte meglio** del disegno 2D di prima;
- ⛔ **`?video=worker` funziona e NON rende**: abbassa il tetto del **19 %**. Chi apre questa fase
  non la rifaccia.

### 7.3 · ⛔⭐ **Il «puntatore doppio» non esiste** — e a smentirlo è stato l'occhio dell'utente

*22 agosto 2026. Il punto era stato aperto e un agente ci stava già lavorando: **fermato dopo pochi
minuti**, su una frase sola.*

⛔ **Il codice lo dichiara come un difetto vivo.** `src/pagina.html`, nel commento del 14 agosto:
*«Il cursore del browser resta VISIBILE, e la freccia la disegniamo lo stesso. ⚠ Se ne vedono **due
sovrapposti** — brutto, e §7.1 lo chiama un difetto»*. Ed è la ragione per cui esiste l'interruttore
`data-puntatore` a tre condizioni, con `due` come valore per difetto **chiamato «il DIFETTO» dal
codice stesso**.

⭐⭐ **E l'utente, guardando lo schermo vero, dice che non c'è**, due volte e la seconda più netta:
*«non ci sono doppi puntatori»* e poi **«io vedo solo un puntatore»** — dopo aver già confermato,
poche ore prima, che *«sì, la freccia si vede»*. ⇒ **Uno, e si vede.**

⇒ ⛔ **Il difetto è dichiarato dal codice e non si manifesta.** È la forma di `LEZIONI.md` §1.20
rovesciata: lì il giudizio era staccato dalla misura, qui **un commento è staccato dal prodotto** —
e ha resistito otto giorni perché nessuno aveva chiesto all'unico arbitro che poteva vederlo.

⚠ **Che cosa NON si conclude da qui**, e va scritto o la prossima lettura sbaglia: *«ne vedo uno»*
non dice **quale**. Restano due mondi possibili — le due frecce **coincidono** esattamente (quindi
sono indistinguibili e il difetto è cosmetico e nullo), **oppure la seconda non viene disegnata
affatto** (e allora sul DeX potrebbe mancare proprio quella che serve). `[?]` La distinzione costa
poco e **non è stata fatta**: l'utente ha chiuso il punto, e un punto chiuso dall'arbitro non si
riapre per curiosità.

⚠ **E l'una vale l'altra per il prodotto sul desktop**, che è quel che l'utente giudica. ⛔ Non
sarebbe più vero sul **DeX**, dove la freccia disegnata esiste per una ragione misurata — a 1,1
fotogrammi al secondo il desktop sembra morto se non la disegna il client. ⇒ Chi un giorno tocca il
DeX **riapra la domanda lì**, non qui.

⇒ ⭐ **Il commento del codice va corretto**, perché oggi manda a cercare un difetto che non c'è. ⏳
Lo farà chi tocca quel file per un'altra ragione — **non si apre un giro per questo**.

### 7.2 ⛔ Che cosa NON è di questa fase

i **10 bit veri** → il muro è nella cattura, non nella codifica (Mutter dà BGRx da ogni strada) · la
**rete stretta** e il **punto di lavoro fra qualità e banda** → fase 9 · la **qualità di
`EncSliceLP` contro l'entrypoint pieno** → fase 9 · il **ridimensionamento dinamico** → fuori dal
progetto · il **multi-tenant** → fase 10, ⚠ ma aspetta il numero vero che esce da qui.

---

## 8 · Il giudizio dell'utente

### 8.1 ⭐ L'apertura — 22 agosto 2026

> *«Di sicuro siamo avanti a xrdp, ma se possiamo limare ancora qualcosa allora ok.»*

⇒ ⭐ **Il via libera, e il metro**: non «raggiungere un numero», ma **limare**.

### 8.2 ⭐⭐ E il confronto con xrdp l'ha fatto lui, subito — 22 agosto 2026

*Si è collegato dal notebook al tablet con l'altro utente e ha rifatto la stessa prova.*

> *«Confermo: siamo avanti, e di non poco. Non posso darti i numeri ma già si vede molto bene
> ad occhio.»*

⚠ Giudizio, **non misura** — e §2.5 spiega perché vale lo stesso, e perché **non chiude la fase**.

### 8.3 ⭐⭐⭐ **«È ok»** — 22 agosto 2026, sera, sul prodotto con la copia zero accesa

*Il server della porta **7790**, ramo `fase-1` con tutto il lavoro della giornata dentro, tela
2560×1080 (passo 10240, multiplo di 64 ⇒ **la copia zero è accesa**, non ripiega). L'utente si
collega, trascina una finestra veloce come nel suo video del mattino, e giudica:*

> ### ⭐⭐⭐ *«è ok»*

⇒ ⭐ **È il mandato della fase, chiuso dall'unico giudizio che lo poteva chiudere.** Il mandato era
suo — *«l'unico piccolo appunto è un'ottimizzazione sulle performance grafiche»* (§8.1) — e la
specifica pure: *«un'esperienza utente il più vicina possibile a una situazione locale»* (§1.1).

**Il cammino della giornata, nella sua unità:**

| | barre del titolo | |
|---|---|---|
| il **locale** — il pavimento, misurato (n=254, alla sua tela) | **0,142** | |
| ⭐ REMOTIX **a sera** | **0,16 · 0,16** | **1,23 × il locale** |

*(La riga «al mattino», sulla strada dalla memoria con `sws_scale`, è tolta: non vale più dopo la fase 18.)*

⚠ **Che cosa questo giudizio dice e che cosa NON dice**, e la distinzione va tenuta:
- ⭐ **dice** che la cura ha funzionato dove conta — sull'occhio dell'utente, sul suo ferro, sulla
  sua scena;
- ⛔ **non dice** se la **previsione falsificabile** di §4-F2 abbia retto. Quella prevedeva
  **0,31-0,46 barre** sul suo schermo, e *«è ok»* è un'accettazione, **non una frazione**. ⏳ Finché
  non c'è la frazione, la spiegazione dello scarto resta **plausibile e non confermata**.

⛔ **E non si scriva che la previsione è confermata**: sarebbe la forma di `LEZIONI.md` §1.20 — *il
giudizio staccato dalla misura* — con l'aggravante di farlo nel documento che quella lezione la
cita.

### 8.4 ⛔⭐ **La frazione è arrivata, ed è FUORI dalla previsione — dalla parte buona**

*Chiesta con un righello concreto (la barra del titolo e i suoi tre punti riconoscibili), per non
far stimare una frazione a mente. La risposta dell'utente, 22 agosto 2026:*

> ### *«Il puntatore resta fisso nella stessa posizione, la finestra lo segue fedelmente»*
>
> *e, alla chiusura:* **«per me è ok»**

⛔⛔ **La previsione di §4-F2 diceva 0,31-0,46 barre. L'utente ne riferisce ~0.** ⇒ **La previsione
NON ha retto**, ed è caduta **dalla parte favorevole** — che è il verso in cui è più facile
accettarla senza guardarla.

⚠ **E i nostri numeri non prevedono lo zero nemmeno adesso**: `[M]` l'anello vale **55,20 ms**, e a
`[M]` **3 400 px/s** — la velocità misurata dal video dell'utente — farebbero **188 px, cioè 0,26
barre**. ⇒ ⛔ **«Fedelmente» non è quel che l'aritmetica dice**, e la differenza non è spiegata.

#### ⭐ Una spiegazione è stata ESCLUSA, e va detto perché era la più pericolosa

`[R]` **Il cammino del puntatore non è stato toccato oggi**: `git log` su `src/pagina.html` per il
22 agosto dà un solo commit di questa fase (**F3**, `REMOTIX.tratti()`, **sola misura**), e il diff
non contiene **nessuna riga** con `puntatore`, `cursor`, `freccia` o `agganciato`.

⇒ ⭐ **Cade l'ipotesi peggiore**, che sarebbe stata invisibile a un giudizio positivo: che la freccia
avesse smesso di essere **locale** e arrivasse ormai **in ritardo insieme al fotogramma**. In quel
caso il distacco sparirebbe **senza che il ritardo sia sceso** — cioè il prodotto sembrerebbe curato
esattamente nella misura in cui è peggiorato. ⛔ **Non è andata così**: la freccia è ancora locale, e
il miglioramento è vero.

#### ⏳ Che cosa resta `[?]`, e non si chiude con un giudizio

Due spiegazioni in piedi, **nessuna misurata**:
1. `[?]` **l'utente ha trascinato più piano** di quando ha girato il video (3 400 px/s mediani): il
   distacco è `velocità × ritardo`, quindi a mano lenta lo zero è atteso;
2. `[?]` **sotto una certa soglia il distacco smette di essere percepibile** e «fedelmente» vuol dire
   «non ci faccio più caso», non «zero pixel».

⚠ ⛔ **La differenza fra le due non è accademica**: la seconda direbbe che abbiamo una soglia di
percezione da cui derivare un traguardo, la prima che la misura va rifatta. ⇒ **Nessuna delle due si
scrive come conclusione**, e il modello di §1.28 resta `[?]`: **ha predetto male due volte di
seguito, in versi opposti**, e questo è un fatto sul modello, non sull'utente.

⭐⭐ **Quel che invece è chiuso, e lo chiude lui**: *«per me è ok»*. Il mandato della fase era suo, e
il giudizio è suo. ⛔ Il modello che spiega *perché* resta un lavoro aperto — ⚠ **ed è lavoro nostro,
non altro tempo dell'utente.**
